"""Terrain brushes (PLAN.md §7 MT, steps T2-T4; docs/MOD_FORMAT.md §8): the height changes a modder paints on a map.

A stroke is one dab of a brush: which brush, where (world x, y), how wide (radius) and how much. The Studio turns a
drag into dabs along its path. A dab changes the ground inside its circle only (a ramp: inside the band along its
line), weighted by the brush's shape (full at the centre, nothing at the edge, smooth in between). Strokes apply in
order, each to the ground the ones before it left.

  brush     what it does                                              uses
  hill      raises the ground in a round hump                         height (world units)
  raise     the same, meant for painting                              height
  lower     lowers the ground in a round dip                          height
  crater    a bowl with a raised rim                                  height (the bowl's depth)
  plateau   levels the ground at a height, flat across the middle      level (world z), weight (0..1)
            half, sloping back to the old ground at the edge
  flatten   pulls the ground toward a level, most at the centre        level, weight
  level     paints the ground at a level, flat across the middle half  level, weight
            (the height where the drag starts, all along the drag)
  smooth    pulls the ground toward its own local average              weight
  ramp      an even slope from one point to another: flat across the    level (z at the start), x2, y2 and
            middle half of its width, sloping back to the old ground     level2 (the end and z there), weight;
            at its sides and beyond its ends                             radius is half its width
  water     sets the water surface inside its circle to a level: the    level (world z of the water surface)
            ground below it floods, a lake (the ground is unchanged)
  drain     puts the water surface inside its circle back to the        -
            map's base level: lakes and rivers there dry up
  cover     paints cover in its circle: units there are hidden, as in a   square (true: a square along the
            wood (the map's cover grid, rusemod.cover; proven in the game) map's axes, radius from its middle to
                                                                         each side, in map units)
  uncover   takes the cover in its circle away                           square
  block     takes the ground in its circle away from every unit: they    -
            plan around it (the map's navigation graphs, rusemod.nav)
  block_infantry, block_vehicles   the same, for infantry or vehicles only
  open      gives units the ground in its circle where the map has    -
            none (the reverse of block: rusemod.nav, Graph.open_ground)
  open_infantry, open_vehicles     the same, for infantry or vehicles only

Water brushes change the drawn meshes' water surface and the map's water textures, never the ground (and never the
.kdt trees, which hold no water); rusemod.terrain_edit and rusemod.water apply them after the height brushes. Cover
brushes change neither: the build turns them into cover.Paint circles on the map's cover grid (in DataMap_Win.dat).
Block and open brushes become nav.Block circles on the map's navigation graphs (in the same file), in order: where a
block and an open meet, the later stroke wins.

Every map's ground lives in four files that must change together (FORMATS.md §6): the two drawn meshes and the two
.kdt trees. rusemod.terrain_edit applies every stroke to all four through `Stroke.height_at`, a function of the
position and the current height only, so points the files share get the same new height.

Determinism: only + - * / and square roots, which IEEE 754 rounds the same on every PC, so every PC builds the same
bytes and multiplayer fingerprints (MOD_FORMAT §12) match.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, fields


class BrushError(ValueError):
    """A stroke that can't be used; the message names the file and the stroke."""


@dataclass(frozen=True)
class Brush:
    kind: str    # "add": z + sign * height * shape; "level": toward `level`; "smooth": toward the local average;
                 # "ramp": toward the line from `level` at (x, y) to `level2` at (x2, y2);
                 # "water" / "drain": the water surface, not the ground (height_at leaves z alone);
                 # "cover": where units hide (sign -1 takes it away), not the ground either;
                 # "block": ground units can't use (shape names the units: all, infantry, vehicles);
                 # "open": ground units can use where the map has none (the same units)
    shape: str   # "soft", "flat" or "crater" (see shape_weight)
    sign: int = 1


BRUSHES = {
    "hill": Brush("add", "soft"),
    "raise": Brush("add", "soft"),
    "lower": Brush("add", "soft", -1),
    "crater": Brush("add", "crater"),
    "plateau": Brush("level", "flat"),
    "flatten": Brush("level", "soft"),
    "level": Brush("level", "flat"),
    "smooth": Brush("smooth", "soft"),
    "ramp": Brush("ramp", "flat"),
    "water": Brush("water", "flat"),
    "drain": Brush("drain", "flat"),
    "cover": Brush("cover", "flat"),
    "town": Brush("cover", "flat"),  # the Studio's Town tool: cover around a town's buildings (its own colour there)
    "uncover": Brush("cover", "flat", -1),
    "block": Brush("block", "all"),
    "block_infantry": Brush("block", "infantry"),
    "block_vehicles": Brush("block", "vehicles"),
    "open": Brush("open", "all"),
    "open_infantry": Brush("open", "infantry"),
    "open_vehicles": Brush("open", "vehicles"),
    # the Map Paint tab (PLAN §15): the ground's picture, not its shape (rusemod.groundpaint.paint_strokes)
    "paint": Brush("paint", "soft"),  # a colour laid over the ground picture, `weight` its opacity
    "stamp": Brush("stamp", "soft"),  # the map's own ground copied from (x + sx, y + sy), `weight` its opacity
}
WATER_KINDS = ("water", "drain")
PAINT_KINDS = ("paint", "stamp")
GROUND_UNCHANGED = WATER_KINDS + ("cover", "block", "open") + PAINT_KINDS  # kinds that never move the ground
CRATER_RIM = 0.35      # the crater's rim rises by this share of the bowl's depth


def shape_weight(shape: str, t2: float) -> float:
    """How strongly a brush acts at a point, from t2 = (distance / radius)² in [0, 1): 1 at the centre (a crater's
    bowl is -1 there), 0 at the edge, with no crease anywhere.

    soft    (1 - t²)²: a round hump
    flat    1 across the middle half (t <= 0.5), then an S-curve down to 0 at the edge
    crater  a bowl of depth 1 out to t = 0.75 and a rim of CRATER_RIM around t = 0.8"""
    if shape == "soft":
        u = 1.0 - t2
        return u * u
    t = math.sqrt(t2)
    if shape == "flat":
        if t <= 0.5:
            return 1.0
        s = (t - 0.5) * 2.0
        return 1.0 - s * s * (3.0 - 2.0 * s)
    if shape == "crater":
        bowl = 0.0
        if t2 < 0.5625:        # 0.75²
            u = 1.0 - t2 / 0.5625
            bowl = u * u
        rim = 0.0
        v = (t - 0.8) / 0.2
        if -1.0 < v < 1.0:
            w = 1.0 - v * v
            rim = w * w
        return CRATER_RIM * rim - bowl
    raise ValueError(f"unknown brush shape {shape!r}")


# --- where a stroke acts: its footprint (the owner, 2026-10-03: "a couple of different Brush types. In every tool that
# has a brush"; "no square like placement tool ... a certain angle on a beach or a rock"). Every brush can be round, a
# square turned any way, or a line (a band between two points, round at its ends), with a soft edge (the brush's own
# fall-off) or a hard one (full strength out to HARD_EDGE of the way, then a short S-curve to nothing). A square's turn
# is a direction (dx, dy), never an angle: only + - * / and square roots, so every PC builds the same bytes.
SHAPES = ("round", "square", "line")
EDGES = ("soft", "hard")
HARD_EDGE = 0.85


@dataclass(frozen=True)
class Footprint:
    """A stroke's footprint in map units: `shape` round (radius r round x, y), square (sides 2r long, running along
    the direction dx, dy) or line (r either side of the segment x, y to x2, y2, round at both ends)."""
    shape: str
    x: float
    y: float
    r: float
    dx: float = 1.0
    dy: float = 0.0
    x2: float = 0.0
    y2: float = 0.0

    def t2(self, px: float, py: float) -> float:
        """(how far out / r)², 0 at the middle (on a line's segment), 1 on the edge."""
        ox, oy = px - self.x, py - self.y
        if self.shape == "square":
            n = math.sqrt(self.dx * self.dx + self.dy * self.dy) or 1.0
            u = abs(ox * self.dx + oy * self.dy) / n
            v = abs(oy * self.dx - ox * self.dy) / n
            m = u if u > v else v
            return (m / self.r) ** 2
        if self.shape == "line":
            sx, sy = self.x2 - self.x, self.y2 - self.y
            len2 = sx * sx + sy * sy
            t = 0.0
            if len2 > 0.0:
                t = (ox * sx + oy * sy) / len2
                t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
            qx, qy = ox - sx * t, oy - sy * t
            return (qx * qx + qy * qy) / (self.r * self.r)
        return (ox * ox + oy * oy) / (self.r * self.r)

    def inside(self, px: float, py: float) -> bool:
        return self.t2(px, py) < 1.0

    def corners(self) -> list[tuple[float, float]]:
        """A square's four corners, in turn round it."""
        n = math.sqrt(self.dx * self.dx + self.dy * self.dy) or 1.0
        ux, uy = self.dx / n * self.r, self.dy / n * self.r
        vx, vy = -uy, ux
        return [(self.x + a * ux + b * vx, self.y + a * uy + b * vy) for a, b in ((1, 1), (1, -1), (-1, -1), (-1, 1))]

    def box(self) -> tuple[float, float, float, float]:
        """x min, x max, y min, y max of everything the footprint covers."""
        if self.shape == "square":
            cs = self.corners()
            return min(c[0] for c in cs), max(c[0] for c in cs), min(c[1] for c in cs), max(c[1] for c in cs)
        if self.shape == "line":
            return (min(self.x, self.x2) - self.r, max(self.x, self.x2) + self.r,
                    min(self.y, self.y2) - self.r, max(self.y, self.y2) + self.r)
        return self.x - self.r, self.x + self.r, self.y - self.r, self.y + self.r

    def meets(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        """Whether the footprint reaches into the box [x0, x1] x [y0, y1] (touching its edge counts)."""
        bx0, bx1, by0, by1 = self.box()
        if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
            return False
        if self.shape == "square":   # two convex shapes: apart only if one of their four side directions parts them
            cs = self.corners()
            n = math.sqrt(self.dx * self.dx + self.dy * self.dy) or 1.0
            for ax, ay in ((self.dx / n, self.dy / n), (-self.dy / n, self.dx / n)):
                ps = [cx * ax + cy * ay for cx, cy in cs]
                qs = [px * ax + py * ay for px in (x0, x1) for py in (y0, y1)]
                if max(qs) < min(ps) or min(qs) > max(ps):
                    return False
            return True
        if self.shape == "line":     # the segment's distance to the box
            return _segment_box_distance2(self.x, self.y, self.x2, self.y2, x0, y0, x1, y1) <= self.r * self.r
        nx, ny = min(max(self.x, x0), x1), min(max(self.y, y0), y1)
        return (nx - self.x) ** 2 + (ny - self.y) ** 2 <= self.r * self.r

    def circles(self, size: float) -> list[tuple[float, float, float]]:
        """Circles (x, y, radius) whose union covers the footprint, for data made of circles (the movement graphs):
        a round one is itself; a line, circles of its radius every half radius along it (the sides dip in by about 3%
        of the radius between them); a square, a grid of cells about `size` across, each in the circle round it (it
        reaches past the square's edge by at most 0.21 of a cell)."""
        if self.shape == "round":
            return [(self.x, self.y, self.r)]
        if self.shape == "line":
            length = math.sqrt((self.x2 - self.x) ** 2 + (self.y2 - self.y) ** 2)
            n = max(1, int(length / (self.r / 2.0)) + 1)
            return [(self.x + (self.x2 - self.x) * k / n, self.y + (self.y2 - self.y) * k / n, self.r)
                    for k in range(n + 1)]
        k = max(1, int(2.0 * self.r / size + 0.999))
        cell = 2.0 * self.r / k
        n = math.sqrt(self.dx * self.dx + self.dy * self.dy) or 1.0
        ux, uy = self.dx / n, self.dy / n
        out = []
        for i in range(k):
            for j in range(k):
                a, b = -self.r + (i + 0.5) * cell, -self.r + (j + 0.5) * cell
                out.append((self.x + a * ux - b * uy, self.y + a * uy + b * ux, cell * math.sqrt(0.5)))
        return out


def _segment_box_distance2(ax: float, ay: float, bx: float, by: float, x0: float, y0: float, x1: float,
                           y1: float) -> float:
    """The squared distance between the segment a-b and the box (0 when they meet)."""
    def inside(px, py):
        return x0 <= px <= x1 and y0 <= py <= y1
    if inside(ax, ay) or inside(bx, by):
        return 0.0
    edges = (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))
    if any(_segments_cross((ax, ay), (bx, by), p, q) for p, q in edges):
        return 0.0
    best = min(_point_segment2(px, py, ax, ay, bx, by) for px in (x0, x1) for py in (y0, y1))
    for px, py in ((ax, ay), (bx, by)):
        nx, ny = min(max(px, x0), x1), min(max(py, y0), y1)
        best = min(best, (nx - px) ** 2 + (ny - py) ** 2)
    return best


def _point_segment2(px, py, ax, ay, bx, by) -> float:
    sx, sy = bx - ax, by - ay
    len2 = sx * sx + sy * sy
    t = 0.0 if len2 == 0.0 else max(0.0, min(1.0, ((px - ax) * sx + (py - ay) * sy) / len2))
    return (px - ax - sx * t) ** 2 + (py - ay - sy * t) ** 2


def _segments_cross(p, q, r, s) -> bool:
    def side(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 0) - (v < 0)
    d1, d2, d3, d4 = side(p, q, r), side(p, q, s), side(r, s, p), side(r, s, q)
    return d1 != d2 and d3 != d4 and 0 not in (d1, d2, d3, d4)


def edge_weight(edge: str, shape: str, t2: float) -> float:
    """How strongly a brush acts at t2 (the footprint's (how far out / r)², below 1): a soft edge is the brush's own
    shape_weight; a hard one is full out to HARD_EDGE of the way, then an S-curve to nothing at the edge (a crater
    keeps its own bowl and rim either way)."""
    if edge != "hard" or shape == "crater":
        return shape_weight(shape, t2)
    t = math.sqrt(t2)
    if t <= HARD_EDGE:
        return 1.0
    s = (t - HARD_EDGE) / (1.0 - HARD_EDGE)
    return 1.0 - s * s * (3.0 - 2.0 * s)


@dataclass(frozen=True)
class Stroke:
    brush: str
    x: float           # world units: x grows east, y grows south (the game's axes); a ramp: where it starts
    y: float
    radius: float      # a ramp: half its width
    height: float = 0.0   # hill, raise, lower, crater: how much, in world units
    level: float = 0.0    # plateau, flatten: the height (world z) the ground goes to; ramp: the height at its start
    weight: float = 1.0   # plateau, flatten, smooth, ramp: how far toward it, 0..1
    x2: float = 0.0       # ramp, a line: where it ends
    y2: float = 0.0
    level2: float = 0.0   # ramp: the height at its end
    square: bool = False  # the older way to say shape = "square" (along the map's axes)
    shape: str = "round"  # round, square (`radius` from its middle to each side) or line (to x2, y2; radius each side)
    edge: str = "soft"    # soft (the brush's own fall-off) or hard (full strength nearly to the edge)
    dx: float = 1.0       # a square: the direction its sides run (any length; 1, 0 = along the map's axes)
    dy: float = 0.0
    colour: str = ""      # paint: the colour laid on the ground picture, "#rrggbb"
    sx: float = 0.0       # stamp: where the ground it copies lies, from each point it paints (world units)
    sy: float = 0.0
    clear: bool = True    # paint, stamp: take off what hides it up close (stickers, low plants, stones) where it is
                          # at least half strength (groundpaint.paint_clearing; TESTS.md T21)

    @property
    def kind(self) -> Brush:
        return BRUSHES[self.brush]

    def footprint(self) -> Footprint:
        """Where the stroke acts (a ramp: the band along its line); made once per stroke."""
        made = self.__dict__.get("_footprint")
        if made is None:
            made = self._make_footprint()
            self.__dict__["_footprint"] = made  # a frozen dataclass's own cache: not a field, never compared
        return made

    def _make_footprint(self) -> Footprint:
        if self.brush == "ramp" or self.shape == "line":
            return Footprint("line", self.x, self.y, self.radius, x2=self.x2, y2=self.y2)
        if self.square or self.shape == "square":
            return Footprint("square", self.x, self.y, self.radius, self.dx, self.dy)
        return Footprint("round", self.x, self.y, self.radius)

    def strength_at(self, x: float, y: float) -> float:
        """How strongly the brush acts at (x, y): its fall-off over the footprint (0 outside it)."""
        t2 = self.footprint().t2(x, y)
        return edge_weight(self.edge, self.kind.shape, t2) if t2 < 1.0 else 0.0

    def along(self, x: float, y: float) -> tuple[float, float]:
        """A ramp: how far along its centre line the point nearest to (x, y) lies (0 at the start, 1 at the end)
        and the squared distance from (x, y) to that point."""
        dx, dy = self.x2 - self.x, self.y2 - self.y
        len2 = dx * dx + dy * dy
        t = 0.0
        if len2 > 0.0:
            t = ((x - self.x) * dx + (y - self.y) * dy) / len2
            t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
        px, py = x - (self.x + dx * t), y - (self.y + dy * t)
        return t, px * px + py * py

    def covers(self, x: float, y: float) -> bool:
        return self.footprint().inside(x, y)

    def box(self) -> tuple[float, float, float, float]:
        """The box round everything the stroke covers: x min, x max, y min, y max."""
        return self.footprint().box()

    def height_at(self, x: float, y: float, z: float, average=None) -> float:
        """The new height of a point at world (x, y) whose ground is at z now (z itself outside the footprint).
        `average(x, y)` gives the local average height, which only the smooth brush uses."""
        b = self.kind
        if b.kind in GROUND_UNCHANGED:
            return z
        t2 = self.footprint().t2(x, y)
        if t2 >= 1.0:
            return z
        p = edge_weight(self.edge, b.shape, t2)
        if b.kind == "ramp":
            target = self.level + (self.level2 - self.level) * self.along(x, y)[0]
            return z + (target - z) * (self.weight * p)
        if b.kind == "add":
            return z + b.sign * self.height * p
        if b.kind == "level":
            return z + (self.level - z) * (self.weight * p)
        if average is None:
            raise ValueError("the smooth brush needs the local average height")
        return z + (average(x, y) - z) * (self.weight * p)

    def kept(self, x: float, y: float) -> float:
        """How much of the ground's own shape at world (x, y) the stroke keeps: 1 for a stroke that adds or takes away
        (hill, raise, lower, crater) and outside its circle; 1 - weight x shape for one that goes toward a height
        (plateau, flatten, level, ramp, smooth), so 0 across a plateau's flat middle. Every ground brush is
        new = old x kept + a target, so this is how much a bump of the old ground is still there after it."""
        b = self.kind
        if b.kind in GROUND_UNCHANGED or b.kind == "add":
            return 1.0
        return 1.0 - self.weight * self.strength_at(x, y)


# --- the mod file: maps/<map pack>/terrain.toml -------------------------------------------------------------------
_NEEDS = {"add": ("height",), "level": ("level",), "smooth": (), "ramp": ("x2", "y2", "level", "level2"),
          "water": ("level",), "drain": (), "cover": (), "block": (), "open": (), "paint": ("colour",),
          "stamp": ("sx", "sy")}
_NUMBERS = ("x", "y", "radius", "height", "level", "weight", "x2", "y2", "level2", "dx", "dy", "sx", "sy")
_COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")


def colour_rgb(colour: str) -> tuple[int, int, int]:
    """'#a07850' -> (160, 120, 80)."""
    return int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)


def _number(v, what: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise BrushError(f"{what} must be a number")
    v = float(v)
    if not math.isfinite(v):
        raise BrushError(f"{what} must be a finite number")
    return v


def parse_strokes(items, where: str = "terrain.toml") -> list[Stroke]:
    """Strokes from a terrain file's `[[stroke]]` tables. Every mistake is an error that names the file and the
    stroke (numbered from 1): an unknown brush or key, a missing or non-numeric value, a radius that isn't above 0,
    a weight outside 0..1."""
    if not isinstance(items, list):
        raise BrushError(f"{where}: `stroke` must be a list of [[stroke]] tables")
    names = {f.name for f in fields(Stroke)}
    out = []
    for n, item in enumerate(items, start=1):
        at = f"{where}: stroke {n}"
        if not isinstance(item, dict):
            raise BrushError(f"{at} isn't a [[stroke]] table")
        unknown = sorted(set(item) - names)
        if unknown:
            raise BrushError(f"{at}: unknown key {unknown[0]!r} (keys: {', '.join(sorted(names))})")
        brush = item.get("brush")
        if brush not in BRUSHES:
            raise BrushError(f"{at}: brush {brush!r} isn't one of {', '.join(BRUSHES)}")
        missing = [k for k in ("x", "y", "radius") + _NEEDS[BRUSHES[brush].kind] if k not in item]
        if missing:
            raise BrushError(f"{at}: the {brush} brush needs {', '.join(missing)}")
        values = {}
        try:
            for k in _NUMBERS:
                if k in item:
                    values[k] = _number(item[k], k)
        except BrushError as exc:
            raise BrushError(f"{at}: {exc}") from None
        if values["radius"] <= 0:
            raise BrushError(f"{at}: radius must be above 0")
        if not 0.0 <= values.get("weight", 1.0) <= 1.0:
            raise BrushError(f"{at}: weight must be between 0 and 1")
        if brush == "smooth" and "weight" not in values:
            values["weight"] = 0.5
        if brush == "ramp" and (values["x"], values["y"]) == (values["x2"], values["y2"]):
            raise BrushError(f"{at}: the ramp's start and end are the same point")
        if "square" in item:
            if not isinstance(item["square"], bool):
                raise BrushError(f"{at}: square must be true or false")
            values["square"] = item["square"]
        for key, allowed in (("shape", SHAPES), ("edge", EDGES)):
            if key in item:
                if item[key] not in allowed:
                    raise BrushError(f"{at}: {key} must be one of {', '.join(allowed)}, not {item[key]!r}")
                values[key] = item[key]
        shape = "square" if values.get("square") else values.get("shape", "round")
        if brush == "ramp" and shape == "square":
            raise BrushError(f"{at}: a ramp runs along its line; it can't be square")
        if shape == "line" and brush != "ramp":
            if "x2" not in values or "y2" not in values:
                raise BrushError(f"{at}: a line needs x2 and y2 (where it ends)")
            if (values["x"], values["y"]) == (values["x2"], values["y2"]):
                raise BrushError(f"{at}: the line's start and end are the same point")
        if ("dx" in values or "dy" in values) and shape != "square":
            raise BrushError(f"{at}: dx and dy (a square's direction) are for square strokes")
        if shape == "square" and values.get("dx", 1.0) == 0.0 and values.get("dy", 0.0) == 0.0:
            raise BrushError(f"{at}: the square's direction dx, dy can't be 0, 0")
        kind = BRUSHES[brush].kind
        if "colour" in item:
            if kind != "paint":
                raise BrushError(f"{at}: colour is for the paint brush")
            if not isinstance(item["colour"], str) or not _COLOUR.match(item["colour"]):
                raise BrushError(f"{at}: colour must be like \"#a07850\" (red, green, blue in hex), not {item['colour']!r}")
            values["colour"] = item["colour"].lower()
        if ("sx" in values or "sy" in values) and kind != "stamp":
            raise BrushError(f"{at}: sx and sy (where a stamp copies from) are for the stamp brush")
        if kind == "stamp" and values["sx"] == 0.0 and values["sy"] == 0.0:
            raise BrushError(f"{at}: the stamp copies from where it paints (sx, sy are 0, 0): pick another spot")
        if "clear" in item:
            if kind not in PAINT_KINDS:
                raise BrushError(f"{at}: clear (taking off what hides the paint up close) is for the paint and stamp "
                                 f"brushes")
            if not isinstance(item["clear"], bool):
                raise BrushError(f"{at}: clear must be true or false")
            values["clear"] = item["clear"]
        out.append(Stroke(brush, **values))
    return out


def _num_text(v: float) -> str:
    """A number for the file, exactly as it is: 983040.0, 12000.5, 0.1 (repr round-trips a float)."""
    return repr(float(v))


def strokes_toml(strokes: list[Stroke], header: str = "") -> str:
    """A terrain file holding `strokes`, in order, with only the values each brush uses."""
    lines = [f"# {line}" if line else "#" for line in header.splitlines()] if header else []
    for s in strokes:
        kind = s.kind.kind
        lines += ["", "[[stroke]]", f'brush = "{s.brush}"', f"x = {_num_text(s.x)}", f"y = {_num_text(s.y)}",
                  f"radius = {_num_text(s.radius)}"]
        if kind == "add":
            lines.append(f"height = {_num_text(s.height)}")
        if kind in ("level", "water"):  # a lake's surface is its level
            lines.append(f"level = {_num_text(s.level)}")
        if kind == "ramp":
            lines += [f"x2 = {_num_text(s.x2)}", f"y2 = {_num_text(s.y2)}", f"level = {_num_text(s.level)}",
                      f"level2 = {_num_text(s.level2)}"]
        if kind == "paint":
            lines.append(f'colour = "{s.colour}"')
        if kind == "stamp":
            lines += [f"sx = {_num_text(s.sx)}", f"sy = {_num_text(s.sy)}"]
        if kind in ("level", "smooth", "ramp") + PAINT_KINDS:
            lines.append(f"weight = {_num_text(s.weight)}")
        if kind in PAINT_KINDS and not s.clear:
            lines.append("clear = false")
        if s.square:
            lines.append("square = true")
        if s.shape != "round":
            lines.append(f'shape = "{s.shape}"')
        if s.shape == "line" and kind != "ramp":
            lines += [f"x2 = {_num_text(s.x2)}", f"y2 = {_num_text(s.y2)}"]
        if (s.square or s.shape == "square") and (s.dx, s.dy) != (1.0, 0.0):
            lines += [f"dx = {_num_text(s.dx)}", f"dy = {_num_text(s.dy)}"]
        if s.edge != "soft":
            lines.append(f'edge = "{s.edge}"')
    return "\n".join(lines).lstrip("\n") + "\n"


# --- the local average, for the smooth brush ----------------------------------------------------------------------
class HeightGrid:
    """The ground as a regular grid of heights (world z), `rows` × `cols` samples at the centres of equal squares
    over the map's bounds (row 0 at y min). It changes with every stroke, like the meshes, and gives the smooth brush
    one local average that every file moves toward, so they stay in step."""

    def __init__(self, heights: list[list[float | None]], x0: float, y0: float, x1: float, y1: float):
        self.rows, self.cols = len(heights), len(heights[0])
        self.x0, self.y0 = x0, y0
        self.sx, self.sy = (x1 - x0) / self.cols, (y1 - y0) / self.rows
        self.z = [list(row) for row in heights]
        self._fill_gaps()

    def _fill_gaps(self) -> None:
        """Squares no triangle covered get the nearest covered height in their row, else in their column, else the
        lowest height of the map."""
        known = [v for row in self.z for v in row if v is not None]
        low = min(known) if known else 0.0
        for row in self.z:
            _fill_line(row)
        for c in range(self.cols):
            col = [self.z[r][c] for r in range(self.rows)]
            _fill_line(col)
            for r in range(self.rows):
                self.z[r][c] = col[r] if col[r] is not None else low

    def point(self, r: int, c: int) -> tuple[float, float]:
        """World (x, y) of the sample at row r, column c."""
        return self.x0 + (c + 0.5) * self.sx, self.y0 + (r + 0.5) * self.sy

    def span(self, x_lo: float, x_hi: float, y_lo: float, y_hi: float) -> tuple[int, int, int, int]:
        """Rows and columns (first, last, inclusive) whose samples may fall inside the box, clipped to the grid."""
        c0 = max(0, int((x_lo - self.x0) / self.sx) - 1)
        c1 = min(self.cols - 1, int((x_hi - self.x0) / self.sx) + 1)
        r0 = max(0, int((y_lo - self.y0) / self.sy) - 1)
        r1 = min(self.rows - 1, int((y_hi - self.y0) / self.sy) + 1)
        return r0, r1, c0, c1

    def apply(self, stroke: Stroke, average=None) -> None:
        r0, r1, c0, c1 = self.span(*stroke.box())
        for r in range(r0, r1 + 1):
            row = self.z[r]
            for c in range(c0, c1 + 1):
                x, y = self.point(r, c)
                row[c] = stroke.height_at(x, y, row[c], average)

    def average_for(self, stroke: Stroke):
        """The local average the smooth `stroke` pulls toward, as a function of world (x, y): the mean of the grid
        over a square about a third of the brush's radius across (1 to 8 samples each way from the centre sample),
        blended between samples. Taken from the grid as it is before the stroke."""
        k = max(1, min(8, int(stroke.radius / (3.0 * min(self.sx, self.sy)) + 0.5)))
        r0, r1, c0, c1 = self.span(*stroke.box())
        r0, r1, c0, c1 = max(0, r0 - 1), min(self.rows - 1, r1 + 1), max(0, c0 - 1), min(self.cols - 1, c1 + 1)
        # a summed-area table over the region grown by k, clipped to the grid
        R0, R1, C0, C1 = max(0, r0 - k), min(self.rows - 1, r1 + k), max(0, c0 - k), min(self.cols - 1, c1 + k)
        w = C1 - C0 + 1
        sat = [[0.0] * (w + 1) for _ in range(R1 - R0 + 2)]
        for i in range(R1 - R0 + 1):
            acc = 0.0
            src, up, out = self.z[R0 + i], sat[i], sat[i + 1]
            for j in range(w):
                acc += src[C0 + j]
                out[j + 1] = up[j + 1] + acc
        mean = {}
        for r in range(r0, r1 + 1):
            a, b = max(R0, r - k) - R0, min(R1, r + k) - R0 + 1
            for c in range(c0, c1 + 1):
                lo, hi = max(C0, c - k) - C0, min(C1, c + k) - C0 + 1
                total = sat[b][hi] - sat[a][hi] - sat[b][lo] + sat[a][lo]
                mean[(r, c)] = total / ((b - a) * (hi - lo))

        def at(x: float, y: float) -> float:
            fc = (x - self.x0) / self.sx - 0.5
            fr = (y - self.y0) / self.sy - 0.5
            c = min(max(int(math.floor(fc)), c0), c1)
            r = min(max(int(math.floor(fr)), r0), r1)
            c2, r2 = min(c + 1, c1), min(r + 1, r1)
            tx = min(max(fc - c, 0.0), 1.0)
            ty = min(max(fr - r, 0.0), 1.0)
            top = mean[(r, c)] + (mean[(r, c2)] - mean[(r, c)]) * tx
            bottom = mean[(r2, c)] + (mean[(r2, c2)] - mean[(r2, c)]) * tx
            return top + (bottom - top) * ty

        return at


def _fill_line(values: list) -> None:
    """Fill the Nones of a row or column with the nearest value along it (the earlier one on a tie)."""
    known = [i for i, v in enumerate(values) if v is not None]
    if not known or len(known) == len(values):
        return
    j = 0
    for i, v in enumerate(values):
        if v is not None:
            continue
        while j + 1 < len(known) and abs(known[j + 1] - i) < abs(known[j] - i):
            j += 1
        values[i] = values[known[j]]
