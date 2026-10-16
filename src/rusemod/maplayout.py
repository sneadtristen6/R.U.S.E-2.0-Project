"""A map's layout as its builder laid it, read once and kept, for the field brush's preview: every PLOT (a field's row
stickers joined square to square by the field brush's own rule, scenery.brush_fields), what stands on and round it
(crops by kind, hay and farm machines, fences, trees, other props, the buildings near it), the colour its ground
picture is painted under it and the look that makes (wheat, stubble, ploughed, green ...), the plots it touches, and
the farm piece it sits in: the scenery blocks a map places many times over, turned (a plot of the same piece is the
same field at every place the piece stands). Measured from the map itself, never assumed.

    lay = read_layout(sc, descs, halves, picture)     # once per map (a few minutes for D-Day), then save()/load()
    lay.plots_under(footprint)                         # the plots a dab's footprint holds a sticker middle of
    lay.plot_at(x, y)                                  # the plot whose square holds (x, y) deepest
    facts(lay)                                         # what the map does with hay, machines and buildings
"""
from __future__ import annotations

import collections
import colorsys
import json
import math
from dataclasses import asdict, dataclass, field

from .scenery import (FARM_HAY, FARM_MACHINES, FIELD_ACROSS, FIELD_ALONG, FIELD_KINDS, IDENTITY, Scenery, _alike,
                      _cut, _facing, compose, sticker_half, walk_levels)

M = 260.0                       # map units a metre
CELL = 40.0 * M                 # the grid squares are filed in
TILE_MIN, TILE_MAX = 150.0 * M, 600.0 * M   # a farm piece: a block this big each way (its own box), placed 2+ times
NEAR = 40.0 * M                 # how far round a plot's squares a building counts as near it
HAY, MACHINES = FARM_HAY, FARM_MACHINES   # (the field brush's own: what it keeps on a field)
CROPS = ("Champs_",)
FENCES = ("BarriereChamps", "Barriere")
LAYOUT_VERSION = 1


@dataclass
class Plot:
    id: int
    stickers: list                      # indexes into Layout.stickers
    facing: float                       # its rows' facing, degrees 0-180
    middle: tuple                       # (x, y) of its stickers' box
    rows: dict                          # row sticker kind (short name) -> count
    area_m2: float = 0.0                # its squares' union, 4 m cells
    crops: dict = field(default_factory=dict)       # crop kind -> count on its squares
    hay: list = field(default_factory=list)         # [name, x, y, depth m, crops within 6 m] hay and machines on it
    fences: int = 0
    trees: int = 0
    props: int = 0                      # other props on it
    picture: list | None = None         # its ground picture's median colour (finest level), [r, g, b]
    look: str = ""                      # what it reads as (look_of)
    tile: list | None = None            # [farm piece block, placement number, local x, local y] of its middle
    neighbours: list = field(default_factory=list)  # plots whose squares meet its own
    buildings: list = field(default_factory=list)   # indexes into Layout.buildings within NEAR of its squares


@dataclass
class Layout:
    map: str
    names: list                         # the scenery's type names
    stickers: list                      # [sym, [12 floats], mask, half] every row sticker once
    plots: list
    buildings: list                     # [name, x, y, nearest crop m, nearest row sticker m]
    tiles: list                         # [block, placements, width m, height m] the farm pieces
    placements: list                    # [block, [12 floats]] each farm piece's place on the map
    version: int = LAYOUT_VERSION
    _grid: dict = field(default_factory=dict, repr=False)

    # --- queries -------------------------------------------------------------------------------------------------
    def _cells(self):
        if not self._grid:
            for k, (_sym, m, _mask, h) in enumerate(self.stickers):
                r = h * 1.4143
                for i in range(int((m[3] - r) // CELL), int((m[3] + r) // CELL) + 1):
                    for j in range(int((m[7] - r) // CELL), int((m[7] + r) // CELL) + 1):
                        self._grid.setdefault((i, j), []).append(k)
            self._owner = {}
            for p in self.plots:
                for k in p.stickers:
                    self._owner[k] = p.id
        return self._grid

    def depth_at(self, k: int, x: float, y: float) -> float:
        """How far (x, y) lies inside sticker k's square (map units; below 0 outside)."""
        _sym, m, _mask, h = self.stickers[k]
        t = math.atan2(m[4], m[0])
        u = (x - m[3]) * math.cos(t) + (y - m[7]) * math.sin(t)
        v = -(x - m[3]) * math.sin(t) + (y - m[7]) * math.cos(t)
        return h - max(abs(u), abs(v))

    def plot_at(self, x: float, y: float) -> tuple:
        """(plot id or None, depth in map units) of the plot whose square holds (x, y) deepest."""
        grid = self._cells()
        best, depth = None, 0.0
        for k in grid.get((int(x // CELL), int(y // CELL)), ()):
            d = self.depth_at(k, x, y)
            if d >= 0.0 and (best is None or d > depth):
                best, depth = self._owner.get(k), d
        return best, depth

    def plots_under(self, footprint) -> list:
        """The plots holding a sticker whose middle the footprint (rusemod.brush.Footprint) holds, as brush_fields
        seeds them."""
        x0, x1, y0, y1 = footprint.box()
        grid = self._cells()
        out = set()
        for i in range(int(x0 // CELL), int(x1 // CELL) + 1):
            for j in range(int(y0 // CELL), int(y1 // CELL) + 1):
                for k in grid.get((i, j), ()):
                    _s, m, _mask, _h = self.stickers[k]
                    if footprint.t2(m[3], m[7]) < 1.0:
                        out.add(self._owner.get(k))
        return sorted(p for p in out if p is not None)

    # --- keeping -------------------------------------------------------------------------------------------------
    def save(self, path) -> None:
        from pathlib import Path
        d = asdict(self)
        d.pop("_grid", None)
        Path(path).write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "Layout":
        from pathlib import Path
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        if d.get("version") != LAYOUT_VERSION:
            raise ValueError(f"{path}: a layout of version {d.get('version')}, this reader's is {LAYOUT_VERSION}")
        d["plots"] = [Plot(**p) for p in d["plots"]]
        d.pop("_grid", None)
        return cls(**d)


# --- reading -------------------------------------------------------------------------------------------------------
def _join(stickers: list) -> list[list[int]]:
    """The stickers grouped into plots: two join when brush_fields would join them, either way round (same facing
    within BRUSH_ANGLE; middles within FIELD_ALONG of the two halves along the rows and FIELD_ACROSS across)."""
    if not stickers:
        return []
    cell = 2.0 * max(h for _s, _m, _k, h in stickers)
    grid = collections.defaultdict(list)
    for k, (_s, m, _k, _h) in enumerate(stickers):
        grid[(int(m[3] // cell), int(m[7] // cell))].append(k)
    parent = list(range(len(stickers)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    facing = [_facing(m) for _s, m, _k, _h in stickers]

    def joined(a, b):
        ma, mb = stickers[a][1], stickers[b][1]
        t = math.radians(facing[a])
        dx, dy = mb[3] - ma[3], mb[7] - ma[7]
        s = stickers[a][3] + stickers[b][3]
        return (abs(dx * math.cos(t) + dy * math.sin(t)) < FIELD_ALONG * s
                and abs(-dx * math.sin(t) + dy * math.cos(t)) < FIELD_ACROSS * s)
    for (gx, gy), ks in grid.items():
        near = [q for i in (gx - 1, gx, gx + 1) for j in (gy - 1, gy, gy + 1) for q in grid.get((i, j), ())]
        for a in ks:
            for b in near:
                if b > a and _alike(facing[a], facing[b]) and (joined(a, b) or joined(b, a)):
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        parent[ra] = rb
    groups = collections.defaultdict(list)
    for k in range(len(stickers)):
        groups[find(k)].append(k)
    return sorted(groups.values(), key=lambda g: min(g))


def _farm_pieces(sc: Scenery, field_syms: set) -> tuple[list, list]:
    """([block, placements, width m, height m] for each farm piece: a block holding row stickers, TILE_MIN to TILE_MAX
    across each way, placed twice or more; [block, matrix] for each of their places, the walk stopping at a piece)."""
    weight, _where = sc.placings()
    holds = sc.holding(field_syms)
    pieces = {}
    for b in sc.blocks:
        x0, y0, x1, y1 = b.bbox
        if (weight[b.index] >= 2 and holds[b.index] and TILE_MIN <= x1 - x0 <= TILE_MAX
                and TILE_MIN <= y1 - y0 <= TILE_MAX):
            pieces[b.index] = (round((x1 - x0) / M), round((y1 - y0) / M))
    places = []
    todo = [(r, IDENTITY) for r in sc.roots()]
    while todo:
        i, m = todo.pop()
        if i in pieces:
            places.append([i, list(m)])
            continue
        for it in sc.blocks[i].items:
            if it.kind == "child":
                j = sc._by_offset[it.child_offset]
                if holds[j]:
                    todo.append((j, compose(m, it.matrix())))
    counts = collections.Counter(p[0] for p in places)
    tiles = [[b, counts[b], w, h] for b, (w, h) in sorted(pieces.items()) if counts[b]]
    return tiles, places


def _local(m: list, x: float, y: float) -> tuple:
    """(x, y) in a placement's own frame (its matrix m: rotation and scale in 0, 1, 4, 5, the place in 3, 7)."""
    a, b, c, d = m[0], m[1], m[4], m[5]
    det = a * d - b * c or 1.0
    dx, dy = x - m[3], y - m[7]
    return (d * dx - b * dy) / det, (-c * dx + a * dy) / det


def hue_of(rgb) -> float:
    return colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))[0] * 360.0


def look_of(picture, rows: dict, crops: dict, area_m2: float) -> str:
    """What a plot reads as, by what the map shows: its picture's hue (from far), its main row sticker kind and its
    crops (the field brush's look library uses the same bands): wheat (yellow, straw rows,
    35+ crop clumps a 100 m2, more wheat than green), stubble (yellow, straw rows, under 10), ploughed (brown, earth
    rows, under 10), green (green, light grass rows, under 10), green crop (green, 35+ green clumps), else meadow-ish
    "other"."""
    if not picture or not rows:
        return "other"
    whole = {k: n for k, n in rows.items() if not _cut(k)} or rows
    top = max(whole, key=whole.get)
    hue = hue_of(picture)
    per = 100.0 * sum(crops.values()) / area_m2 if area_m2 else 0.0
    wheat = sum(n for k, n in crops.items() if k.startswith("Champs_Bles"))
    green = sum(n for k, n in crops.items() if k.startswith("Champs_Verts"))
    if 38.0 <= hue < 52.0 and top.startswith("Paille"):
        if per >= 35.0 and wheat >= green:
            return "wheat"
        if per < 10.0:
            return "stubble"
    if hue < 38.0 and top.startswith(("Labourage_terre", "Labourage")) and not top.startswith("Labourage_herbe") \
            and per < 10.0:
        return "ploughed"
    if 64.0 <= hue < 90.0 and top.startswith("Labourage_herbe"):
        if per < 10.0:
            return "green"
        if green > wheat:
            return "green crop"
    return "other"


def read_layout(sc: Scenery, descs: dict, halves: dict | None, picture=None, map_name: str = "",
                say=lambda s: None) -> Layout:
    """The map's layout (see the module). `descs`: scenery.descriptors (the type groups); `halves`: each row sticker
    type's square (decor sets' MaxExtent; scenery.sticker_half); `picture`: (x, y) -> rgb or None, the finest level of
    the map's ground picture (groundpaint._picture_sampler), or None to leave colours and looks out."""
    short = [n.rsplit("/", 1)[-1] for n in sc.names]
    field_syms = {i for i, n in enumerate(short) if n.startswith(FIELD_KINDS)}
    everything = (-1e12, -1e12, 1e12, 1e12)
    found: dict = {}
    for sym, m, mask in walk_levels(sc, everything, field_syms):
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in found:
            found[key][2] |= mask
        else:
            found[key] = [sym, list(m), mask, sticker_half(sc, sym, m, halves)]
    stickers = sorted(found.values(), key=lambda s: (s[1][3], s[1][7], s[0]))
    say(f"{len(stickers):,} row stickers")
    groups = _join(stickers)
    plots = []
    for g, ks in enumerate(groups):
        xs = [stickers[k][1][3] for k in ks]
        ys = [stickers[k][1][7] for k in ks]
        c = sum(math.cos(math.radians(2 * _facing(stickers[k][1]))) for k in ks)
        s = sum(math.sin(math.radians(2 * _facing(stickers[k][1]))) for k in ks)
        plots.append(Plot(g, ks, round((math.degrees(math.atan2(s, c)) / 2) % 180.0, 2),
                          ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2),
                          dict(collections.Counter(short[stickers[k][0]] for k in ks).most_common())))
    lay = Layout(map_name, list(sc.names), stickers, plots, [], [], [])
    say(f"{len(plots):,} plots")

    # each plot's area: its squares' union in 4 m cells
    for p in plots:
        cells = set()
        for k in p.stickers:
            _sym, m, _mask, h = stickers[k]
            t = math.atan2(m[4], m[0])
            n = max(1, math.ceil(2 * h / (2.0 * M)))   # a point every 2 m at most: every 4 m cell it covers
            for i in range(n):
                for j in range(n):
                    a, b = (-1 + (2 * i + 1) / n) * h, (-1 + (2 * j + 1) / n) * h
                    x = m[3] + a * math.cos(t) - b * math.sin(t)
                    y = m[7] + a * math.sin(t) + b * math.cos(t)
                    cells.add((int(x // (4.0 * M)), int(y // (4.0 * M))))
        p.area_m2 = float(len(cells) * 16)

    # neighbours: plots whose squares meet (middles within the two halves' reach, across their corners)
    grid = lay._cells()
    for p in plots:
        near = set()
        for k in p.stickers:
            _sym, m, _mask, h = stickers[k]
            for q in grid.get((int(m[3] // CELL), int(m[7] // CELL)), ()):
                other = lay._owner.get(q)
                if other is None or other == p.id or other in near:
                    continue
                _s2, m2, _k2, h2 = stickers[q]
                if math.hypot(m2[3] - m[3], m2[7] - m[7]) < (h + h2) * 1.4143:
                    near.add(other)
        p.neighbours = sorted(near)

    # the farm pieces and where each plot's middle stands in one
    tiles, places = _farm_pieces(sc, field_syms)
    lay.tiles, lay.placements = tiles, places
    boxes = {b.index: b.bbox for b in sc.blocks}
    by_cell = collections.defaultdict(list)
    for n, (b, m) in enumerate(places):
        x0, y0, x1, y1 = boxes[b]
        corners = [(m[0] * x + m[1] * y + m[3], m[4] * x + m[5] * y + m[7]) for x in (x0, x1) for y in (y0, y1)]
        for i in range(int(min(c[0] for c in corners) // (300 * M)), int(max(c[0] for c in corners) // (300 * M)) + 1):
            for j in range(int(min(c[1] for c in corners) // (300 * M)),
                           int(max(c[1] for c in corners) // (300 * M)) + 1):
                by_cell[(i, j)].append(n)
    for p in plots:
        x, y = p.middle
        for n in by_cell.get((int(x // (300 * M)), int(y // (300 * M))), ()):
            b, m = places[n]
            lx, ly = _local(m, x, y)
            x0, y0, x1, y1 = boxes[b]
            if x0 <= lx <= x1 and y0 <= ly <= y1:
                p.tile = [b, n, round(lx), round(ly)]
                break
    say(f"{len(tiles)} farm pieces, {len(places):,} places; "
        f"{sum(1 for p in plots if p.tile):,} plots in one")

    # what stands on and round the plots: one walk over the crops, props, trees and buildings
    group = [descs[n].group if n in descs else "" for n in sc.names]
    crop_syms = {i for i, n in enumerate(short) if n.startswith(CROPS)}
    from .scenery import low_cover
    low = set(low_cover(descs, sc.names))
    # the crops, the trees, the props (not the stones) and the buildings: the low plants and stones (millions of
    # tufts and pebbles) aren't asked about
    wanted = crop_syms | {i for i, g in enumerate(group) if (g in ("prop", "vegetation") and sc.names[i] not in low)
                          or g == "building"}
    wanted -= field_syms
    buildings_at = collections.defaultdict(list)   # cell -> building indexes (filled as they come)
    hay_at = collections.defaultdict(list)
    seen: set = set()
    pending_crops = []
    for sym, m, _mask in walk_levels(sc, everything, wanted):
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in seen:
            continue
        seen.add(key)
        name = short[sym]
        x, y = m[3], m[7]
        if sym in crop_syms:
            pid, _d = lay.plot_at(x, y)
            if pid is not None:
                c = plots[pid].crops
                c[name] = c.get(name, 0) + 1
            pending_crops.append((x, y))
            continue
        g = group[sym]
        if g == "building":
            pid, _d = lay.plot_at(x, y)
            near_plot = pid is not None or any(
                lay.depth_at(k, x, y) > -NEAR for i in range(int((x - NEAR) // CELL), int((x + NEAR) // CELL) + 1)
                for j in range(int((y - NEAR) // CELL), int((y + NEAR) // CELL) + 1) for k in grid.get((i, j), ()))
            if near_plot:
                lay.buildings.append([sc.names[sym], x, y, None, None])
                buildings_at[(int(x // NEAR), int(y // NEAR))].append(len(lay.buildings) - 1)
            continue
        pid, depth = lay.plot_at(x, y)
        if pid is None:
            continue
        p = plots[pid]
        if name.startswith(HAY) or name.startswith(MACHINES):
            p.hay.append([name, x, y, round(depth / M, 1), 0])
            hay_at[(int(x // (6 * M)), int(y // (6 * M)))].append((pid, len(p.hay) - 1))
        elif name.startswith(FENCES):
            p.fences += 1
        elif g == "vegetation" and sc.names[sym] not in low:
            p.trees += 1
        elif g == "prop" and sc.names[sym] not in low:
            p.props += 1
    seen.clear()
    say(f"{len(pending_crops):,} crops; {len(lay.buildings):,} buildings near plots")
    # the crops round each hay piece and each building's nearest crop
    for x, y in pending_crops:
        gx, gy = int(x // (6 * M)), int(y // (6 * M))
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for pid, n in hay_at.get((i, j), ()):
                    h = plots[pid].hay[n]
                    if (h[1] - x) ** 2 + (h[2] - y) ** 2 <= (6 * M) ** 2:
                        h[4] += 1
        bx, by = int(x // NEAR), int(y // NEAR)
        for i in (bx - 1, bx, bx + 1):
            for j in (by - 1, by, by + 1):
                for b in buildings_at.get((i, j), ()):
                    rec = lay.buildings[b]
                    d = math.hypot(rec[1] - x, rec[2] - y) / M
                    if rec[3] is None or d < rec[3]:
                        rec[3] = round(d, 1)
    pending_crops.clear()
    for rec in lay.buildings:   # and its nearest row sticker
        x, y = rec[1], rec[2]
        best = None
        for i in range(int((x - NEAR) // CELL), int((x + NEAR) // CELL) + 1):
            for j in range(int((y - NEAR) // CELL), int((y + NEAR) // CELL) + 1):
                for k in grid.get((i, j), ()):
                    m = stickers[k][1]
                    d = math.hypot(m[3] - x, m[7] - y) / M
                    if best is None or d < best:
                        best = d
        rec[4] = round(best, 1) if best is not None else None
    for p in plots:
        x0 = min(stickers[k][1][3] for k in p.stickers) - NEAR
        x1 = max(stickers[k][1][3] for k in p.stickers) + NEAR
        y0 = min(stickers[k][1][7] for k in p.stickers) - NEAR
        y1 = max(stickers[k][1][7] for k in p.stickers) + NEAR
        for i in range(int(x0 // NEAR), int(x1 // NEAR) + 1):
            for j in range(int(y0 // NEAR), int(y1 // NEAR) + 1):
                for b in buildings_at.get((i, j), ()):
                    rec = lay.buildings[b]
                    if any(lay.depth_at(k, rec[1], rec[2]) > -NEAR for k in p.stickers):
                        p.buildings.append(b)
        p.buildings = sorted(set(p.buildings))

    # the picture's colour and the look
    if picture is not None:
        for p in plots:
            got = []
            for k in p.stickers:
                _sym, m, _mask, h = stickers[k]
                t = math.atan2(m[4], m[0])
                for a, b in ((0, 0), (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                    x = m[3] + (a * math.cos(t) - b * math.sin(t)) * h
                    y = m[7] + (a * math.sin(t) + b * math.cos(t)) * h
                    c = picture(x, y)
                    if c is not None:
                        got.append(c)
            if got:
                p.picture = [sorted(c[q] for c in got)[len(got) // 2] for q in range(3)]
        say("colours read")
    for p in plots:
        p.look = look_of(p.picture, p.rows, p.crops, p.area_m2)
    return lay


def facts(lay: Layout) -> dict:
    """What the map does with hay and farm machines (on which looks, how deep inside a plot, among how many crops)
    and how near its crops and row stickers come to its buildings: measured, for the field brush to follow."""
    by_look = collections.defaultdict(list)
    for p in lay.plots:
        for h in p.hay:
            by_look[p.look].append(h)

    def spread(vals):
        vals = sorted(v for v in vals if v is not None)
        if not vals:
            return None
        return {"n": len(vals), "min": vals[0], "q1": vals[len(vals) // 4], "median": vals[len(vals) // 2],
                "q3": vals[3 * len(vals) // 4], "max": vals[-1]}
    plots_by_look = collections.Counter(p.look for p in lay.plots)
    with_hay = collections.Counter(p.look for p in lay.plots if any(h[0].startswith(HAY) for h in p.hay))
    return {
        "plots by look": dict(plots_by_look),
        "plots with hay by look": dict(with_hay),
        "hay and machines by look": {look: {"pieces": len(hs),
                                            "names": dict(collections.Counter(h[0] for h in hs).most_common(6)),
                                            "depth m": spread([h[3] for h in hs]),
                                            "crops within 6 m": spread([h[4] for h in hs])}
                                     for look, hs in by_look.items()},
        "buildings near plots": len(lay.buildings),
        "nearest crop to a building m": spread([b[3] for b in lay.buildings]),
        "nearest row sticker to a building m": spread([b[4] for b in lay.buildings]),
    }
