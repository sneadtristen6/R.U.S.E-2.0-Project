"""A field brush dab's PARCEL: the ground the dab changes, as the map's own paint and borders draw the fields there,
and nothing past it.

Why (2026-10-15): the brush's fields are row pieces of one facing joined square to square (scenery.brush_fields),
and their squares are not the fields the player sees. Where two plots' squares overlap (most of D-Day's plots along
their edges), Eugen's paint follows the plot holding the point deepest only 57% of the time, the plot with the nearest
row piece 57% (13,173 points of 1,812 plots where the two plots' colours differ: scratch/looks/ownership_measure.py):
he painted the picture by hand per place. A dab's paint changed over its fields' squares spilled into the next field
(R's green over E's corner by the hut, seen from afar in the owner's 14:24 shots); ground inside a field no square
covers (W's tree line) and corner pieces' ground (Q's tiny spot) were left in their old paint.

How (find_parcel): on cells of the finest picture's pixel (61.5 cm) round the dab's fields, each cell's colour averaged
over 3 m (a ploughed field's stripes); from the ground under the dab (its fields' cells there), the parcel grows to
each neighbour cell whose colour steps little from the last (LOCAL: a painted field's edge is a step) and stays near
the colours under the dab (FAR), within the fields' squares grown by MARGIN, never through a wall: the map's own
field borders (the hedge-foot and field-edge strips Eugen placed along them: border_blocks), its fence pieces, its
roads and buildings; then its speckle smoothed, and the holes in it filled that hold no wall.

    walls = border_walls(sc, blocks, box) + fence_walls(...) + ...
    p = find_parcel(seed_test, squares, picture, walls)
    p.holds(x, y); p.depth(x, y); p.clip()
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

from .numpy2 import np

M = 260.0
CELL = 160.0             # map units a cell: the finest picture's pixel (61.5 cm)
MARGIN = 4.0 * M         # how far past its fields' squares a parcel may reach when its field's paint runs on
SEARCH = 30.0 * M        # how far past them the fields under a dab are looked for, whole
PASSAGE = 6              # cells: a passage narrower than about twice this (7.4 m) parts two fields
OTHER_FIELD = 150.0 * M * M   # map units^2: a body this big beyond a passage is another field (smaller: a nook)
RUN_OFF = 20.0 * M       # a parcel touching the edge of the search over this long runs on: its squares bound it
SMOOTH = 2               # cells each way a colour is averaged over (5 x 5 = 3 m: a ploughed field's stripes)
LOCAL = 9.0              # RGB distance a cell's colour may step from its neighbour's inside one field
FAR = 90.0               # ... and from the nearest of the colours under the dab (loose: Eugen paints a field's
                         # harvested part darker, soft-edged: 42 split E's field there, 2026-10-15; its edges are the
                         # steps, the walls and the passages)
CENTRES = 3              # the colours under the dab: up to this many (a field's stripes and patches)
OPEN = 3                 # cells: runs of the parcel narrower than about twice this (3.7 m) are cut off
EDGE = 34.0              # RGB distance across 2 x EDGE_SPAN cells that marks a field's painted edge (20 and 26 cut
                         # E's field at its harvested part and R's in two; 34 kept them, stopped Q at the grey plot)
EDGE_SPAN = 2
BORDER_MIN = 50          # a border strip: a thin block of low cover placed at least this often
FENCES = ("BarriereChamps", "Barriere")


@dataclass
class Parcel:
    x0: float
    y0: float
    cell: float
    w: int
    h: int
    mask: object         # bool [h, w]: the parcel's ground
    inside: object       # float32 [h, w]: metres in from the parcel's edge (0 off it)
    walls: object = None  # bool [h, w]: the walls drawn (for pictures)
    seeds: object = None  # bool [h, w]: the ground under the dab it grew from

    def _ij(self, x: float, y: float):
        return int((x - self.x0) // self.cell), int((y - self.y0) // self.cell)

    def holds(self, x: float, y: float, _reach: float = 0.0) -> bool:
        i, j = self._ij(x, y)
        return 0 <= i < self.w and 0 <= j < self.h and bool(self.mask[j, i])

    def depth(self, x: float, y: float) -> float:
        """Metres in from the parcel's edge (0 off it)."""
        i, j = self._ij(x, y)
        return float(self.inside[j, i]) if 0 <= i < self.w and 0 <= j < self.h else 0.0

    def clip(self, mask=None) -> tuple:
        """(x0, y0, cell, w, h, bytes): brush.Stroke.clip (of `mask`, a part of the parcel, else all of it)."""
        m = self.mask if mask is None else mask
        return (self.x0, self.y0, self.cell, self.w, self.h, bytes(m.astype(np.uint8).ravel()))

    def area_m2(self) -> float:
        return float(self.mask.sum()) * (self.cell / M) ** 2

    def box(self) -> tuple:
        return self.x0, self.y0, self.x0 + self.w * self.cell, self.y0 + self.h * self.cell


# --- the map's borders ------------------------------------------------------------------------------------------------
def border_blocks(sc, low_syms: set, most: int = BORDER_MIN) -> dict:
    """{block index: (half long, half wide, middle x, middle y, long axis x, long axis y)} in the block's own frame: the
    map's border strips (on D-Day #983, the hedge-foot strip, 27 x 1.5 m, placed 30,363 times; #986, the field-edge
    strip, 16 x 0.8 m, 12,735 times: scratch/looks/border_sources.py): leaf blocks of low cover only (`low_syms`),
    10-40 m long and under 3.5 m wide, placed `most` times or more."""
    weight = [0] * len(sc.blocks)
    for r in sc.roots():
        weight[r] += 1
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "child":
                weight[sc._by_offset[it.child_offset]] += weight[b.index]
    out = {}
    for b in sc.blocks:
        if weight[b.index] < most or not b.items:
            continue
        if any(it.kind != "object" or it.symbol not in low_syms for it in b.items):
            continue
        pts = [(it.matrix()[3], it.matrix()[7]) for it in b.items]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        # its long axis: the points' main direction
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        sxy = sum((x - mx) * (y - my) for x, y in pts)
        t = 0.5 * math.atan2(2 * sxy, sxx - syy)
        ux, uy = math.cos(t), math.sin(t)
        us = [(x - mx) * ux + (y - my) * uy for x, y in pts]
        vs = [-(x - mx) * uy + (y - my) * ux for x, y in pts]
        long, wide = max(us) - min(us), max(vs) - min(vs)
        if 10.0 * M <= long <= 40.0 * M and wide <= 3.5 * M:
            out[b.index] = (long / 2.0, max(wide / 2.0, 0.4 * M), mx, my, ux, uy)
    return out


def walk_blocks(sc, box: tuple, targets: set):
    """(block index, 3x4 transform in map coordinates) for every placement of a block in `targets` meeting `box`
    (x0, y0, x1, y1); blocks whose box misses it aren't walked (as scenery.walk_levels)."""
    from .scenery import IDENTITY, compose
    x0, y0, x1, y1 = box
    holds = {}

    def holding(i) -> bool:   # whether a target lies under block i
        if i not in holds:
            holds[i] = False
            b = sc.blocks[i]
            got = i in targets or any(holding(sc._by_offset[it.child_offset]) for it in b.items if it.kind == "child")
            holds[i] = got
        return holds[i]

    def meets(b, m) -> bool:
        bx0, by0, bx1, by1 = b.bbox
        xs = [m[0] * x + m[1] * y + m[3] for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1))]
        ys = [m[4] * x + m[5] * y + m[7] for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1))]
        return max(xs) >= x0 and min(xs) <= x1 and max(ys) >= y0 and min(ys) <= y1

    import sys
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 20000))
    try:
        todo = [(r, IDENTITY) for r in sc.roots()]
        while todo:
            i, m = todo.pop()
            if not holding(i):
                continue
            if i in targets:
                if meets(sc.blocks[i], m):
                    yield i, m
                continue
            for it in sc.blocks[i].items:
                if it.kind == "child":
                    j = sc._by_offset[it.child_offset]
                    if holding(j):
                        w = compose(m, it.matrix())
                        if meets(sc.blocks[j], w):
                            todo.append((j, w))
    finally:
        sys.setrecursionlimit(old)


def border_walls(sc, blocks: dict, box: tuple) -> list:
    """The border strips placed in `box` as walls: [(x, y, half long, half wide, ux, uy)] in map coordinates."""
    out = []
    for i, m in walk_blocks(sc, box, set(blocks)):
        hl, hw, mx, my, ux, uy = blocks[i]
        x = m[0] * mx + m[1] * my + m[3]
        y = m[4] * mx + m[5] * my + m[7]
        ax, ay = m[0] * ux + m[1] * uy, m[4] * ux + m[5] * uy
        s = math.hypot(ax, ay) or 1.0
        out.append((x, y, hl * s, hw * s, ax / s, ay / s))
    return out


def piece_walls(pieces, half_long: float, half_wide: float) -> list:
    """Walls for objects placed along a line (fence pieces): [(x, y, half long, half wide, ux, uy)] from their 3x4
    transforms, each a short bar along its own facing, long enough to close the gaps between pieces."""
    out = []
    for m in pieces:
        s = math.hypot(m[0], m[4]) or 1.0
        out.append((m[3], m[7], half_long * s, half_wide, m[0] / s, m[4] / s))
    return out


# --- the grid -------------------------------------------------------------------------------------------------------
def _depth(squares: list, x0: float, y0: float, cell: float, w: int, h: int, reach: float = MARGIN):
    """[h, w] how far each cell's middle lies inside the squares (x, y, half, facing radians), map units (below 0
    outside them, worked out to `reach` past them); -inf farther."""
    out = np.full((h, w), -np.inf, dtype=np.float64)
    for x, y, half, t in squares:
        r = half * 1.4143 + reach + 2 * cell
        i0, i1 = max(0, int((x - r - x0) // cell)), min(w, int((x + r - x0) // cell) + 1)
        j0, j1 = max(0, int((y - r - y0) // cell)), min(h, int((y + r - y0) // cell) + 1)
        if i0 >= i1 or j0 >= j1:
            continue
        xs = x0 + (np.arange(i0, i1) + 0.5) * cell
        ys = y0 + (np.arange(j0, j1) + 0.5) * cell
        X, Y = np.meshgrid(xs - x, ys - y)
        c, s = math.cos(t), math.sin(t)
        d = half - np.maximum(np.abs(X * c + Y * s), np.abs(-X * s + Y * c))
        np.maximum(out[j0:j1, i0:i1], d, out=out[j0:j1, i0:i1])
    return out


def _rects(rects: list, x0: float, y0: float, cell: float, w: int, h: int):
    """[h, w] True on the cells whose middles lie in one of the rectangles (x, y, half long, half wide, ux, uy)."""
    out = np.zeros((h, w), dtype=bool)
    for x, y, hl, hw, ux, uy in rects:
        r = math.hypot(hl, hw) + cell
        i0, i1 = max(0, int((x - r - x0) // cell)), min(w, int((x + r - x0) // cell) + 1)
        j0, j1 = max(0, int((y - r - y0) // cell)), min(h, int((y + r - y0) // cell) + 1)
        if i0 >= i1 or j0 >= j1:
            continue
        X, Y = np.meshgrid(x0 + (np.arange(i0, i1) + 0.5) * cell - x, y0 + (np.arange(j0, j1) + 0.5) * cell - y)
        hit = (np.abs(X * ux + Y * uy) <= hl) & (np.abs(-X * uy + Y * ux) <= hw + cell * 0.5)
        out[j0:j1, i0:i1] |= hit
    return out


def _blur(a, k: int, valid):
    """Mean over (2k+1)^2 cells of the valid ones (a: [h, w, 3])."""
    if k <= 0:
        return a
    v = valid.astype(np.float64)
    pad = ((k, k), (k, k))
    s = np.pad(a * v[..., None], pad + ((0, 0),))
    n = np.pad(v, pad)
    cs = np.pad(s.cumsum(0).cumsum(1), ((1, 0), (1, 0), (0, 0)))
    cn = np.pad(n.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    hh, ww = a.shape[:2]
    q = 2 * k + 1
    tot = cs[q:q + hh, q:q + ww] - cs[:hh, q:q + ww] - cs[q:q + hh, :ww] + cs[:hh, :ww]
    cnt = cn[q:q + hh, q:q + ww] - cn[:hh, q:q + ww] - cn[q:q + hh, :ww] + cn[:hh, :ww]
    return np.where(cnt[..., None] > 0, tot / np.maximum(cnt, 1)[..., None], a)


def _centres(colours, k: int = CENTRES, iters: int = 10):
    """Up to k colour centres of `colours` [n, 3] (k-means from the darkest to the lightest; a centre holding under
    4% of them dropped), or None for none."""
    if len(colours) == 0:
        return None
    if len(colours) > 8000:
        colours = colours[np.linspace(0, len(colours) - 1, 8000).astype(np.int64)]
    k = min(k, len(colours))
    order = np.argsort(colours.sum(1))
    centres = colours[order[[int((i + 0.5) * len(colours) / k) for i in range(k)]]].astype(np.float64)
    lab = np.zeros(len(colours), dtype=np.int64)
    for _ in range(iters):
        lab = ((colours[:, None, :] - centres[None]) ** 2).sum(2).argmin(1)
        for i in range(k):
            sel = colours[lab == i]
            if len(sel):
                centres[i] = sel.mean(0)
    keep = [i for i in range(k) if (lab == i).sum() >= 0.04 * len(colours)]
    return centres[keep] if keep else centres


def _grow(mask, n: int):
    """mask grown n cells each way (eight neighbours, n times)."""
    out = mask.copy()
    for _ in range(n):
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        g[1:, 1:] |= out[:-1, :-1]
        g[:-1, :-1] |= out[1:, 1:]
        g[1:, :-1] |= out[:-1, 1:]
        g[:-1, 1:] |= out[1:, :-1]
        out = g
    return out


def _shrink(mask, n: int):
    return ~_grow(~mask, n)


def _components(mask):
    """[h, w] labels of the 4-connected pieces of mask (0 off it), and their count."""
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    flat = mask.ravel()
    lf = lab.ravel()
    n = 0
    for start in np.flatnonzero(flat):
        if lf[start]:
            continue
        n += 1
        lf[start] = n
        todo = deque([start])
        while todo:
            p = todo.popleft()
            r, c = divmod(p, w)
            for q in ((p - w) if r else -1, (p + w) if r < h - 1 else -1, (p - 1) if c else -1,
                      (p + 1) if c < w - 1 else -1):
                if q >= 0 and flat[q] and not lf[q]:
                    lf[q] = n
                    todo.append(q)
    return lab, n


def _majority(mask, times: int = 2):
    """Each cell takes what most of its 3 x 3 cells are (`times` over): speckle out."""
    for _ in range(times):
        v = mask.astype(np.int16)
        p = np.pad(v, 1)
        s = sum(p[1 + a:1 + a + v.shape[0], 1 + b:1 + b + v.shape[1]] for a in (-1, 0, 1) for b in (-1, 0, 1))
        mask = s >= 5
    return mask


def _inside(mask, cell: float, most: float = 30.0 * M):
    """[h, w] metres from each of the mask's cells to the nearest cell off it (whole cells, eight neighbours a step,
    up to `most`)."""
    out = np.zeros(mask.shape, dtype=np.float32)
    cur = mask.copy()
    k = 0
    while cur.any() and k * cell < most:
        k += 1
        out[cur] = k * cell / M
        cur = _shrink(cur, 1) & cur
    out[cur] = (k + 1) * cell / M
    return out


def find_parcel(under, squares: list, picture, walls: list = (), cell: float = CELL, margin: float = SEARCH,
                local: float = LOCAL, far: float = FAR, edge: float = None) -> Parcel | None:
    """The parcel a dab changes. `under(xs, ys)` -> bool array: the dab's footprint (brush.Footprint.t2 < 1);
    `squares` [(x, y, half, facing radians)]: the row squares of the fields it changes (brush_fields); `picture(xs,
    ys)` -> (colours [n, 3], there [n]): the map's own paint, finest level (paintnp._Picture.at_points); `walls`
    [(x, y, half long, half wide, ux, uy)]: the map's borders (border_walls, piece_walls). None when the picture has
    nothing under the dab."""
    if not squares:
        return None
    edge = EDGE if edge is None else edge
    x0 = min(x - h * 1.4143 for x, _y, h, _t in squares) - margin
    x1 = max(x + h * 1.4143 for x, _y, h, _t in squares) + margin
    y0 = min(y - h * 1.4143 for _x, y, h, _t in squares) - margin
    y1 = max(y + h * 1.4143 for _x, y, h, _t in squares) + margin
    x0, y0 = math.floor(x0 / cell) * cell, math.floor(y0 / cell) * cell
    w, h = int(math.ceil((x1 - x0) / cell)), int(math.ceil((y1 - y0) / cell))
    X, Y = np.meshgrid(x0 + (np.arange(w) + 0.5) * cell, y0 + (np.arange(h) + 0.5) * cell)
    rgb, there = picture(X.ravel(), Y.ravel())
    there = np.asarray(there).reshape(h, w)
    if not there.any():
        return None
    img = _blur(np.asarray(rgb, dtype=np.float64).reshape(h, w, 3), SMOOTH, there)
    dF = _depth(squares, x0, y0, cell, w, h, margin)
    bound = (dF > -margin) & there
    wall = _rects(list(walls), x0, y0, cell, w, h)
    # the paint's own field edges: where the colour (averaged over 3 m) changes by EDGE or more across 2.5 m (a step
    # between two fields; inside one the averaged colour drifts slowly). The averaging spreads a step over 5 cells, so
    # cell to cell it is small: R's and Q's flood went through 30-50 steps that way, 10-15
    k = EDGE_SPAN
    gx = np.zeros((h, w))
    gy = np.zeros((h, w))
    gx[:, k:-k] = np.sqrt(((img[:, 2 * k:] - img[:, :-2 * k]) ** 2).sum(2))
    gy[k:-k, :] = np.sqrt(((img[2 * k:, :] - img[:-2 * k, :]) ** 2).sum(2))
    wall = wall | (np.maximum(gx, gy) >= edge)
    seeds = np.asarray(under(X.ravel(), Y.ravel())).reshape(h, w) & (dF >= 0.5 * M) & there & ~wall
    if seeds.sum() < 8:
        seeds = np.asarray(under(X.ravel(), Y.ravel())).reshape(h, w) & (dF >= 0.0) & there
    if not seeds.any():
        return None
    centres = _centres(img[seeds])
    near = np.sqrt(((img[:, :, None, :] - centres[None, None]) ** 2).sum(3)).min(2)
    ok = bound & ~wall & (near <= far)
    mask = seeds & ok
    flat_ok, flat_mask = ok.ravel(), mask.ravel()
    col = img.reshape(-1, 3)
    todo = deque(np.flatnonzero(flat_mask).tolist())
    while todo:
        p = todo.popleft()
        r, c = divmod(p, w)
        cp = col[p]
        for q in ((p - w) if r else -1, (p + w) if r < h - 1 else -1, (p - 1) if c else -1, (p + 1) if c < w - 1 else -1):
            if q < 0 or flat_mask[q] or not flat_ok[q]:
                continue
            d = col[q] - cp
            if d[0] * d[0] + d[1] * d[1] + d[2] * d[2] <= local * local:
                flat_mask[q] = True
                todo.append(q)
    mask = _majority(mask) & bound & ~wall
    # the fields under the dab, whole: the region cut at its narrow passages (a gap at a fence's end let R's paint
    # into the next yellow field, 10-15; a verge of the field's colour led Q's 60 m along a neighbour), the pieces
    # holding ground under the dab kept, each given back its own edges (grown again within the region, as far as it
    # was cut: not back through a passage)
    mask0 = mask
    blocked = np.zeros_like(mask)
    # thin runs (a verge, a hedge foot's band of the field's colour: under 3.7 m across) cut first
    mask = _grow(_shrink(mask, OPEN), OPEN) & mask
    core = _shrink(mask, PASSAGE)
    lab, n = _components(core)
    keep = np.unique(lab[seeds & core])
    keep = keep[keep > 0]
    if len(keep):
        # given back all of the region reached from the kept fields but the other fields' bodies (a field's narrow
        # end has no other field beyond it: Q's tip, cut off when only the passage's width was given back)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        others = (lab > 0) & ~np.isin(lab, keep) & (sizes[lab] * cell * cell >= OTHER_FIELD)
        blocked = _grow(others, PASSAGE + 1)
        start = np.isin(lab, keep)
        free = mask & ~blocked
        flat_free, got = free.ravel(), start.ravel().copy()
        todo = deque(np.flatnonzero(got).tolist())
        while todo:
            p = todo.popleft()
            r, c = divmod(p, w)
            for q in ((p - w) if r else -1, (p + w) if r < h - 1 else -1, (p - 1) if c else -1,
                      (p + 1) if c < w - 1 else -1):
                if q >= 0 and flat_free[q] and not got[q]:
                    got[q] = True
                    todo.append(q)
        mask = got.reshape(h, w) | (_grow(start, PASSAGE + 1) & mask)
    else:   # (a field narrower than a passage under the dab: the thin runs alone cut)
        opened = _grow(_shrink(mask, OPEN), OPEN) & mask
        lab, n = _components(opened)
        keep = np.unique(lab[seeds & opened])
        keep = keep[keep > 0]
        mask = np.isin(lab, keep) if len(keep) else (mask & seeds)
    # what the thin-run cut took off its edges and tips given back (a field's sharp tip narrows under 3.7 m: E's
    # triangle's and Q's ends kept their old paint, 10-15), within its fields' squares, never into another field
    mask = mask | (_grow(mask, OPEN + 2) & mask0 & (dF >= 0.0) & ~blocked)
    # one that runs on past where it was looked for is no field (a meadow's paint all round): its fields' squares alone
    rim = bound & ~_shrink(bound, 1)
    if (mask & rim).sum() * cell > RUN_OFF and margin > MARGIN:
        return find_parcel(under, squares, picture, walls, cell, MARGIN, local, far, edge)
    # its holes are its own ground (a darker patch, a tree's painted shadow, a short hedge strip or a fence inside it:
    # W's plot, 10-15, with the trees standing among them in its middle); a hole reaching off the bound isn't one
    holes, nh = _components(~mask)
    edge_ids = set(np.unique(np.concatenate([holes[0], holes[-1], holes[:, 0], holes[:, -1]])).tolist())
    for k in range(1, nh + 1):
        if k in edge_ids:
            continue
        hole = holes == k
        if (hole & ~bound).any():
            continue
        mask |= hole
    return Parcel(x0, y0, cell, w, h, mask, _inside(mask, cell), wall, seeds)


class FieldGround:
    """What the field brush needs of a map's ground to find a dab's parcel, read once per map: its paint (the finest
    tile level, read as paint_strokes reads it: paintnp._Picture), its border strips (border_blocks) and its fence
    pieces. `store`: the map's highdef Tmst; `bounds`: groundpaint.map_bounds; `descs`: the game's scenery
    descriptors."""

    def __init__(self, sc, store, bounds, descs):
        from . import groundpaint, paintnp
        from .scenery import copy_layers
        self.sc = sc
        self._pic = paintnp._Picture(groundpaint, store, bounds, 0)
        layers = copy_layers(sc.names, descs)
        self.low = layers["plants"] | layers["stones"]
        self.tree_syms = set(layers["trees"])
        self.blocks = border_blocks(sc, self.low)
        short = [n.rsplit("/", 1)[-1] for n in sc.names]
        self.fence_syms = {i for i, n in enumerate(short) if n.startswith(FENCES)}

    def picture(self, xs, ys):
        return self._pic.at_points(np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64))

    def walls(self, box: tuple) -> list:
        """The border strips and the fence pieces in `box` as walls."""
        from .scenery import walk_levels
        out = border_walls(self.sc, self.blocks, box)
        out += piece_walls([m for _s, m, _k in walk_levels(self.sc, box, self.fence_syms)], 1.1 * M, 0.3 * M)
        return out

    def strips(self, box: tuple) -> list:
        """The border strips in `box`: [(block index, its placement's 3x4 transform)]."""
        return list(walk_blocks(self.sc, box, set(self.blocks)))

    def strip_kinds(self) -> dict:
        """{block: (half long, half wide, middle x, middle y, ux, uy, its objects' type names)} of the border strips."""
        out = {}
        for b, (hl, hw, mx, my, ux, uy) in self.blocks.items():
            names = tuple(sorted({self.sc.names[it.symbol] for it in self.sc.blocks[b].items if it.kind == "object"}))
            out[b] = (hl, hw, mx, my, ux, uy, names)
        return out

    def parcel(self, footprint, squares: list) -> Parcel | None:
        """The parcel a dab with `footprint` (brush.Footprint) changes, its fields' row squares `squares`."""
        if not squares:
            return None
        r = SEARCH + 2 * CELL
        box = (min(x - h * 1.4143 for x, _y, h, _t in squares) - r, min(y - h * 1.4143 for _x, y, h, _t in squares) - r,
               max(x + h * 1.4143 for x, _y, h, _t in squares) + r, max(y + h * 1.4143 for _x, y, h, _t in squares) + r)

        def under(xs, ys):
            return np.fromiter((footprint.t2(x, y) < 1.0 for x, y in zip(xs, ys)), dtype=bool, count=len(xs))
        return find_parcel(under, squares, self.picture, self.walls(box))


def subtract(p: Parcel, q: Parcel) -> None:
    """Takes off parcel `p` the cells whose middles parcel `q` holds (a later dab's ground is the later dab's)."""
    jj, ii = np.nonzero(p.mask)
    if not len(jj):
        return
    xs = p.x0 + (ii + 0.5) * p.cell
    ys = p.y0 + (jj + 0.5) * p.cell
    qi = np.floor((xs - q.x0) / q.cell).astype(np.int64)
    qj = np.floor((ys - q.y0) / q.cell).astype(np.int64)
    ok = (qi >= 0) & (qi < q.w) & (qj >= 0) & (qj < q.h)
    hit = np.zeros(len(jj), dtype=bool)
    hit[ok] = q.mask[qj[ok], qi[ok]]
    if hit.any():
        p.mask[jj[hit], ii[hit]] = False
        p.inside = _inside(p.mask, p.cell)
