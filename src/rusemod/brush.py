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
  smooth    pulls the ground toward its own local average              weight
  ramp      an even slope from one point to another: flat across the    level (z at the start), x2, y2 and
            middle half of its width, sloping back to the old ground     level2 (the end and z there), weight;
            at its sides and beyond its ends                             radius is half its width
  water     sets the water surface inside its circle to a level: the    level (world z of the water surface)
            ground below it floods, a lake (the ground is unchanged)
  drain     puts the water surface inside its circle back to the        -
            map's base level: lakes and rivers there dry up

Water brushes change the drawn meshes' water surface and the map's water textures, never the ground (and never the
.kdt trees, which hold no water); rusemod.terrain_edit and rusemod.water apply them after the height brushes.

Every map's ground lives in four files that must change together (FORMATS.md §6): the two drawn meshes and the two
.kdt trees. rusemod.terrain_edit applies every stroke to all four through `Stroke.height_at`, a function of the
position and the current height only, so points the files share get the same new height.

Determinism: only + - * / and square roots, which IEEE 754 rounds the same on every PC, so every PC builds the same
bytes and multiplayer fingerprints (MOD_FORMAT §12) match.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields


class BrushError(ValueError):
    """A stroke that can't be used; the message names the file and the stroke."""


@dataclass(frozen=True)
class Brush:
    kind: str    # "add": z + sign * height * shape; "level": toward `level`; "smooth": toward the local average;
                 # "ramp": toward the line from `level` at (x, y) to `level2` at (x2, y2);
                 # "water" / "drain": the water surface, not the ground (height_at leaves z alone)
    shape: str   # "soft", "flat" or "crater" (see shape_weight)
    sign: int = 1


BRUSHES = {
    "hill": Brush("add", "soft"),
    "raise": Brush("add", "soft"),
    "lower": Brush("add", "soft", -1),
    "crater": Brush("add", "crater"),
    "plateau": Brush("level", "flat"),
    "flatten": Brush("level", "soft"),
    "smooth": Brush("smooth", "soft"),
    "ramp": Brush("ramp", "flat"),
    "water": Brush("water", "flat"),
    "drain": Brush("drain", "flat"),
}
WATER_KINDS = ("water", "drain")
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


@dataclass(frozen=True)
class Stroke:
    brush: str
    x: float           # world units: x grows east, y grows south (the game's axes); a ramp: where it starts
    y: float
    radius: float      # a ramp: half its width
    height: float = 0.0   # hill, raise, lower, crater: how much, in world units
    level: float = 0.0    # plateau, flatten: the height (world z) the ground goes to; ramp: the height at its start
    weight: float = 1.0   # plateau, flatten, smooth, ramp: how far toward it, 0..1
    x2: float = 0.0       # ramp: where it ends
    y2: float = 0.0
    level2: float = 0.0   # ramp: the height at its end

    @property
    def kind(self) -> Brush:
        return BRUSHES[self.brush]

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
        if self.brush == "ramp":
            return self.along(x, y)[1] < self.radius * self.radius
        dx, dy = x - self.x, y - self.y
        return dx * dx + dy * dy < self.radius * self.radius

    def box(self) -> tuple[float, float, float, float]:
        """The square around the circle (a ramp: around its whole band): x min, x max, y min, y max."""
        if self.brush == "ramp":
            return (min(self.x, self.x2) - self.radius, max(self.x, self.x2) + self.radius,
                    min(self.y, self.y2) - self.radius, max(self.y, self.y2) + self.radius)
        return self.x - self.radius, self.x + self.radius, self.y - self.radius, self.y + self.radius

    def height_at(self, x: float, y: float, z: float, average=None) -> float:
        """The new height of a point at world (x, y) whose ground is at z now (z itself outside the circle, or
        outside a ramp's band). `average(x, y)` gives the local average height, which only the smooth brush uses."""
        b = self.kind
        if b.kind in WATER_KINDS:
            return z
        r2 = self.radius * self.radius
        if b.kind == "ramp":
            t, d2 = self.along(x, y)
            if d2 >= r2:
                return z
            target = self.level + (self.level2 - self.level) * t
            return z + (target - z) * (self.weight * shape_weight(b.shape, d2 / r2))
        dx, dy = x - self.x, y - self.y
        d2 = dx * dx + dy * dy
        if d2 >= r2:
            return z
        p = shape_weight(b.shape, d2 / r2)
        if b.kind == "add":
            return z + b.sign * self.height * p
        if b.kind == "level":
            return z + (self.level - z) * (self.weight * p)
        if average is None:
            raise ValueError("the smooth brush needs the local average height")
        return z + (average(x, y) - z) * (self.weight * p)


# --- the mod file: maps/<map pack>/terrain.toml -------------------------------------------------------------------
_NEEDS = {"add": ("height",), "level": ("level",), "smooth": (), "ramp": ("x2", "y2", "level", "level2"),
          "water": ("level",), "drain": ()}
_NUMBERS = ("x", "y", "radius", "height", "level", "weight", "x2", "y2", "level2")


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
        if kind == "level":
            lines.append(f"level = {_num_text(s.level)}")
        if kind == "ramp":
            lines += [f"x2 = {_num_text(s.x2)}", f"y2 = {_num_text(s.y2)}", f"level = {_num_text(s.level)}",
                      f"level2 = {_num_text(s.level2)}"]
        if kind in ("level", "smooth", "ramp"):
            lines.append(f"weight = {_num_text(s.weight)}")
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
