"""Mending the ground's pictures where a hollow of the old ground was filled (a flattened riverbed): its picture and
close-up map still show the old banks, painted with their light and shadow (T18, T26, T27).

A hollow is found from the old mesh: its height filled in (the highest ground within `reach`, then the lowest of that,
a closing) minus its height, more than `deep`; widened by `wider`, so the banks' painted rims go too (Gorge). A filled
hollow is one the new ground no longer has (Filled): a riverbed raised flat, not one that is still a dip (the owner,
T28: "make it look like grass when it's super, super flat"). Each side of a hollow takes the ground beyond its own
bank, moved across by the hollow's width (a copy, not a mirror: a mirror doubles what lies by the bank into twin
shapes), mirrored only right by the bank so its edge meets its own ground; the two sides cross-fade through the
middle. The fill keeps the fields' grain instead of a flat smear or a copied field that reads as a road (T26's yellow
stretch, the owner: "a road pops through"; T27: "maybe if that was like a combination of the two and blended in").

How each point is filled is worked out once on the hollows' grid (Plan: the way across, the near bank, the width,
smoothed so neighbouring squares agree), then every pixel of every picture level takes its ground through it, at its
own resolution: the finest picture keeps its grain, and a whole flattened map costs minutes, not hours.

Seen in the game (T28, "purple wins": all the low cover off and the riverbed mended this way, laid on a test copy by
hand); the build's own step is not seen yet. The checks here are on the files' bytes only (tests/test_mend.py)."""
from __future__ import annotations

import math
from array import array
from collections import deque

from . import dxt
from .groundpaint import PaintError, _blocks, _picture_sampler, _tgv_with_payload, _tile_rect
from .tmst import Tgv, zipo_pack, zipo_tile, zipo_unpack

METRE = 260.0
REACH = 60 * METRE     # a hollow up to twice this across is filled in (Blitz's river gorges: 30 to 80 m)
DEEP = 1.5 * METRE     # filled in by more than this
WIDER = 4 * METRE      # and this much round it: the rims painted light or dark
STEP = 2.5 * METRE     # the hollows' grid
EASE = 6 * METRE       # mirrored by the bank, moved across from this far in
SMOOTH = 8 * METRE     # the way across and the width taken over this far round
CROSS = 0.5            # the share of a hollow's width, about its middle, where its two sides cross-fade


def _slide(values: list, r: int, pick) -> list:
    """The highest (pick=max) or lowest (min) of `values` within r either side of each, in one pass (a running window
    whose candidates are kept in order)."""
    n = len(values)
    out = [0.0] * n
    q: deque = deque()
    better = (lambda a, b: a >= b) if pick is max else (lambda a, b: a <= b)
    j = 0
    for i in range(n):
        while j < n and j <= i + r:
            while q and better(values[j], values[q[-1]]):
                q.pop()
            q.append(j)
            j += 1
        while q[0] < i - r:
            q.popleft()
        out[i] = values[q[0]]
    return out


def _filter2(grid: list[list[float]], r: int, pick) -> list[list[float]]:
    """A square window's highest or lowest over a grid (rows, then columns)."""
    rows = [_slide(row, r, pick) for row in grid]
    cols = [_slide([rows[j][i] for j in range(len(rows))], r, pick) for i in range(len(rows[0]))]
    return [[cols[i][j] for i in range(len(cols))] for j in range(len(rows))]


def _blur(vals, nx: int, ny: int, r: int) -> array:
    """The mean of a grid's values (row by row, nx across) over a square 2r+1 across round each (rows, then columns;
    by an edge, over what there is)."""
    n = nx * ny
    if r <= 0:
        return array("d", vals)
    tmp = array("d", bytes(8 * n))
    for j in range(ny):
        acc, o = [0.0], j * nx
        for i in range(nx):
            acc.append(acc[-1] + vals[o + i])
        for i in range(nx):
            a, b = max(0, i - r), min(nx, i + r + 1)
            tmp[o + i] = (acc[b] - acc[a]) / (b - a)
    out = array("d", bytes(8 * n))
    for i in range(nx):
        acc = [0.0]
        for j in range(ny):
            acc.append(acc[-1] + tmp[j * nx + i])
        for j in range(ny):
            a, b = max(0, j - r), min(ny, j + r + 1)
            out[j * nx + i] = (acc[b] - acc[a]) / (b - a)
    return out


def heights(tms, x0: float, y0: float, nx: int, ny: int, step: float) -> list[list[float | None]]:
    """The ground's height (world z) of a .tms mesh (rusemod.tms.Tms) at the middle of each square of an nx x ny grid
    from (x0, y0), `step` apart: its ground triangles (list 0) laid on the grid. None off the mesh."""
    grid: list[list[float | None]] = [[None] * nx for _ in range(ny)]
    x1, y1 = x0 + nx * step, y0 + ny * step
    for c in tms.cells:
        pos = c.positions()
        if not pos:
            continue
        pts = [(tms.to_world(0, p[0]), tms.to_world(1, p[1]), tms.to_world(2, p[2])) for p in pos]
        if (max(p[0] for p in pts) < x0 or min(p[0] for p in pts) > x1 or max(p[1] for p in pts) < y0
                or min(p[1] for p in pts) > y1):
            continue
        tri = c.triangles(0)
        for t in range(0, len(tri) - 2, 3):
            a, b, d = pts[tri[t]], pts[tri[t + 1]], pts[tri[t + 2]]
            ax, ay = (a[0] - x0) / step - 0.5, (a[1] - y0) / step - 0.5
            bx, by = (b[0] - x0) / step - 0.5, (b[1] - y0) / step - 0.5
            cx, cy = (d[0] - x0) / step - 0.5, (d[1] - y0) / step - 0.5
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if not den:
                continue
            i0, i1 = max(math.ceil(min(ax, bx, cx)), 0), min(math.floor(max(ax, bx, cx)), nx - 1)
            j0, j1 = max(math.ceil(min(ay, by, cy)), 0), min(math.floor(max(ay, by, cy)), ny - 1)
            for j in range(j0, j1 + 1):
                row = grid[j]
                for i in range(i0, i1 + 1):
                    l1 = ((by - cy) * (i - cx) + (cx - bx) * (j - cy)) / den
                    l2 = ((cy - ay) * (i - cx) + (ax - cx) * (j - cy)) / den
                    l3 = 1 - l1 - l2
                    if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                        row[i] = l1 * a[2] + l2 * b[2] + l3 * d[2]
    return grid


class Gorge:
    """The old ground's hollows over a box (x0, y0, x1, y1) of the map: where its height filled in (closing: the
    highest within `reach`, then the lowest of that within `reach`) stands more than `deep` above it, widened by
    `wider`. `tms`: the ground mesh (rusemod.tms.Tms). The grid starts `reach + wider + step` before the box."""

    def __init__(self, tms, box, reach: float = REACH, deep: float = DEEP, wider: float = WIDER, step: float = STEP):
        pad = reach + wider + step
        self.x0, self.y0 = box[0] - pad, box[1] - pad
        self.step = step
        self.nx = max(1, math.ceil((box[2] + pad - self.x0) / step))
        self.ny = max(1, math.ceil((box[3] + pad - self.y0) / step))
        z = heights(tms, self.x0, self.y0, self.nx, self.ny, step)
        low = min((v for row in z for v in row if v is not None), default=0.0)
        z = [[low if v is None else v for v in row] for row in z]
        r = max(1, round(reach / step))
        filled = _filter2(_filter2(z, r, max), r, min)
        hollow = [[1 if f - h > deep else 0 for f, h in zip(frow, zrow)] for frow, zrow in zip(filled, z)]
        del filled, z  # a whole map's grid is millions of numbers: only the answer is kept
        w = round(wider / step)
        if w:
            hollow = _filter2(hollow, w, max)
        self.bits = bytearray(1 if v else 0 for row in hollow for v in row)

    def holds(self, x: float, y: float) -> bool:
        i, j = int((x - self.x0) // self.step), int((y - self.y0) // self.step)
        return 0 <= i < self.nx and 0 <= j < self.ny and bool(self.bits[j * self.nx + i])

    def share(self) -> float:
        return sum(self.bits) / len(self.bits)


class Filled:
    """The hollows of the old ground (`before`, a Tms) that the new ground (`after`) no longer has, over a box: where
    a riverbed was raised flat. `holds` says filled; `hollow` says a hollow of the old ground (filled or not: no ground
    is read from there); `touches` whether a circle reaches into a filled one (the build takes the low cover that
    does)."""

    def __init__(self, before, after, box, **kw):
        self.old = Gorge(before, box, **kw)
        new = Gorge(after, box, **kw)
        self.x0, self.y0, self.step, self.nx, self.ny = self.old.x0, self.old.y0, self.old.step, self.old.nx, self.old.ny
        self.bits = bytearray(a & (1 - b) for a, b in zip(self.old.bits, new.bits))

    def holds(self, x: float, y: float) -> bool:
        i, j = int((x - self.x0) // self.step), int((y - self.y0) // self.step)
        return 0 <= i < self.nx and 0 <= j < self.ny and bool(self.bits[j * self.nx + i])

    def hollow(self, x: float, y: float) -> bool:
        return self.old.holds(x, y)

    def touches(self, x: float, y: float, reach: float) -> bool:
        if self.holds(x, y):
            return True
        for f in (0.5, 1.0):
            r = reach * f
            for k in range(8):
                a = k * math.pi / 4
                if self.holds(x + r * math.cos(a), y + r * math.sin(a)):
                    return True
        return False

    def count(self) -> int:
        return sum(self.bits)

    def box(self) -> tuple[float, float, float, float] | None:
        """The filled squares' bounds (x0, y0, x1, y1), or None for none."""
        rows = [j for j in range(self.ny) if any(self.bits[j * self.nx:(j + 1) * self.nx])]
        if not rows:
            return None
        cols = [i for i in range(self.nx) if any(self.bits[j * self.nx + i] for j in rows)]
        s = self.step
        return self.x0 + cols[0] * s, self.y0 + rows[0] * s, self.x0 + (cols[-1] + 1) * s, self.y0 + (rows[-1] + 1) * s


def _smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Plan:
    """How each square of a grid (nx x ny, `step` map units from (x0, y0)) is filled: `fill` (a bytearray, 1 per
    square) the squares to fill, `bad` the squares no ground is read from (the hollows). For each square to fill: the
    way across the hollow (away from its nearest bank, smoothed over `smooth` squares round: an uneven bank would
    otherwise turn it square by square and the ground taken into streaks), how far it lies from that bank, and the
    hollow's width there (on along the way to the far bank; smoothed too, so the ground moved across doesn't jump
    from square to square). A square with no far bank on the grid fills from its near bank alone."""

    def __init__(self, nx: int, ny: int, fill, bad, x0: float = 0.0, y0: float = 0.0, step: float = 1.0,
                 smooth: float = 0.0):
        self.nx, self.ny, self.x0, self.y0, self.step = nx, ny, x0, y0, step
        n = nx * ny
        self.bad = bad
        big = float("inf")
        sx, sy = array("i", [-1]) * n, array("i", [-1]) * n
        d2 = array("d", [big]) * n
        for k in range(n):
            if not bad[k]:
                sx[k], sy[k], d2[k] = k % nx, k // nx, 0.0
        # the nearest good square: two passes, each carrying its neighbours' nearest along (8 neighbours over both)
        for order, near in ((range(n), ((-1, -1), (0, -1), (1, -1), (-1, 0))),
                            (range(n - 1, -1, -1), ((1, 1), (0, 1), (-1, 1), (1, 0)))):
            for k in order:
                if not bad[k]:
                    continue
                i, j = k % nx, k // nx
                for di, dj in near:
                    a, b = i + di, j + dj
                    if 0 <= a < nx and 0 <= b < ny:
                        m = b * nx + a
                        if sx[m] >= 0:
                            e = (sx[m] - i) ** 2 + (sy[m] - j) ** 2
                            if e < d2[k]:
                                sx[k], sy[k], d2[k] = sx[m], sy[m], e
        sm = round(smooth)
        dist = _blur([math.sqrt(d2[k]) if bad[k] and d2[k] < big else 0.0 for k in range(n)], nx, ny, sm) \
            if sm > 0 else None
        self.index = array("i", [-1]) * n
        ux, uy, d1s, widths = array("d"), array("d"), array("d"), array("d")
        cells = []
        most = 2 * max(nx, ny)
        for k in range(n):
            if not fill[k] or not bad[k] or sx[k] < 0:
                continue
            i, j = k % nx, k // nx
            px, py = i + 0.5, j + 0.5
            qx, qy = sx[k] + 0.5, sy[k] + 0.5
            d1 = math.hypot(px - qx, py - qy)
            if d1 == 0:
                continue
            u, v = (px - qx) / d1, (py - qy) / d1
            if dist is not None and 0 < i < nx - 1 and 0 < j < ny - 1:
                gx, gy = dist[k + 1] - dist[k - 1], dist[k + nx] - dist[k - nx]
                g = math.hypot(gx, gy)
                if g > 1e-9 and gx * u + gy * v > 0:  # the smoothed way, unless it turns back (the middle's ridge)
                    u, v = gx / g, gy / g
            width = -1.0
            for t in range(1, most):  # on across to the far bank
                fx, fy = px + u * t, py + v * t
                a, b = math.floor(fx), math.floor(fy)
                if not (0 <= a < nx and 0 <= b < ny):
                    break
                if not bad[b * nx + a]:
                    width = d1 + t
                    break
            self.index[k] = len(cells)
            cells.append(k)
            ux.append(u)
            uy.append(v)
            d1s.append(d1)
            widths.append(width)
        if sm > 0 and cells:  # the width, smoothed over the squares round that have one
            w_grid, c_grid = array("d", bytes(8 * n)), array("d", bytes(8 * n))
            for idx, k in enumerate(cells):
                if widths[idx] > 0:
                    w_grid[k], c_grid[k] = widths[idx], 1.0
            ws, cs = _blur(w_grid, nx, ny, sm), _blur(c_grid, nx, ny, sm)
            for idx, k in enumerate(cells):
                if widths[idx] > 0 and cs[k] > 0:
                    widths[idx] = max(ws[k] / cs[k], d1s[idx] + 0.5)
        self.ux, self.uy, self.d1, self.width = ux, uy, d1s, widths

    def count(self) -> int:
        return len(self.ux)

    def sources(self, x: float, y: float, ease: float, cross: float):
        """Where a point (map units) takes its ground: [(weight, (x, y) beyond a bank, its bank (x, y)), ...], the
        weights summing to 1; None when the point isn't one to fill. Each source can step back toward its bank when it
        lands in a hollow (fill_value does)."""
        s = self.step
        gx, gy = (x - self.x0) / s, (y - self.y0) / s
        i, j = math.floor(gx), math.floor(gy)
        if not (0 <= i < self.nx and 0 <= j < self.ny):
            return None
        idx = self.index[j * self.nx + i]
        if idx < 0:
            return None
        u, v, d1c, w = self.ux[idx], self.uy[idx], self.d1[idx], self.width[idx]
        d1 = max(0.0, d1c + (gx - i - 0.5) * u + (gy - j - 0.5) * v)  # this point's own distance from the bank
        bx, by = gx - u * d1, gy - v * d1                              # the near bank, straight back along the way
        e = ease / s

        def side(kx, ky, ox, oy, din, wide):
            """One side's sources for a point `din` in from its bank (kx, ky), (ox, oy) pointing out of the hollow."""
            mirror = (kx + ox * din, ky + oy * din)
            if wide <= 0:
                return [(1.0, mirror)]
            k = _smooth(din / e) if e > 0 else 1.0
            moved = (kx + ox * (wide - din), ky + oy * (wide - din))
            return [(1.0 - k, mirror), (k, moved)] if k < 1.0 else [(1.0, moved)]
        out = [(wt, src, (bx, by)) for wt, src in side(bx, by, -u, -v, d1, w)]
        if w > 0:
            d2 = max(0.0, w - d1)
            fx, fy = gx + u * d2, gy + v * d2
            w1 = _smooth(0.5 + (d2 - d1) / (2 * cross * w)) if cross > 0 else float(d1 <= d2)
            out = [(wt * w1, src, b) for wt, src, b in out] + \
                  [(wt * (1 - w1), src, (fx, fy)) for wt, src in side(fx, fy, u, v, d2, w)]
        return [(wt, (self.x0 + sx_ * s, self.y0 + sy_ * s), (self.x0 + kx * s, self.y0 + ky * s))
                for wt, (sx_, sy_), (kx, ky) in out if wt > 1e-6]

    def fill_value(self, x: float, y: float, sample, hollow, ease: float = EASE, cross: float = CROSS):
        """The mended value (a tuple) at a point: its sources' values (`sample(x, y)`, None off the picture) by their
        weights; a source landing in a hollow (`hollow(x, y)`) steps back toward its bank. None: not a point to fill,
        or nothing to take."""
        src = self.sources(x, y, ease, cross)
        if not src:
            return None
        total, acc = 0.0, None
        for wt, (sx_, sy_), (kx, ky) in src:
            got = None
            for t in (1.0, 0.75, 0.5, 0.25, 0.0):
                px, py = kx + (sx_ - kx) * t, ky + (sy_ - ky) * t
                if t == 0.0 or not hollow(px, py):
                    got = sample(px, py)
                    break
            if got is None:
                continue
            acc = [wt * c for c in got] if acc is None else [a + wt * c for a, c in zip(acc, got)]
            total += wt
        if acc is None or total <= 0:
            return None
        return tuple(round(a / total) for a in acc)


def plan_filled(filled: Filled, smooth: float = SMOOTH) -> Plan:
    """The Plan for a Filled's grid: its filled squares filled, its old hollows (filled or not) read from nowhere."""
    return Plan(filled.nx, filled.ny, filled.bits, filled.old.bits, filled.x0, filled.y0, filled.step,
                smooth / filled.step)


def mend_grid(nx: int, ny: int, fill, bad, sample, ease: float = 1.0, cross: float = CROSS,
              smooth: float = 0.0) -> dict[tuple[int, int], tuple]:
    """The mended values of a grid's pixels (a Plan on the pixels themselves): `fill(i, j)` which to mend, `bad(i, j)`
    which can't lend their ground (may be asked off the grid), `sample(fx, fy)` the value at a pixel spot as it was,
    None off the picture; `ease`, `smooth` in pixels. Returns {(i, j): value}."""
    fill_bits = bytearray(1 if fill(k % nx, k // nx) else 0 for k in range(nx * ny))
    bad_bits = bytearray(1 if bad(k % nx, k // nx) else 0 for k in range(nx * ny))
    plan = Plan(nx, ny, fill_bits, bad_bits, smooth=smooth)

    def hollow(fx, fy):
        a, b = math.floor(fx), math.floor(fy)
        return bool(bad_bits[b * nx + a]) if 0 <= a < nx and 0 <= b < ny else bool(bad(a, b))
    out = {}
    for k in range(nx * ny):
        if fill_bits[k]:
            i, j = k % nx, k // nx
            v = plan.fill_value(i + 0.5, j + 0.5, sample, hollow, ease, cross)
            if v is not None:
                out[(i, j)] = v
    return out


def _to_fill(plan: Plan, i0: int, i1: int, j0: int, j1: int, ox: float, oy: float, pw: float, ph: float):
    """The pixels of a picture (pixel (0, 0) starting at ox, oy; pw x ph map units each) in columns i0..i1 and rows
    j0..j1 whose middle lies in a square of `plan` to fill: (i, j, x, y). Each column's grid square is worked out once,
    so the pixels with nothing to fill cost one look-up each."""
    s, nx, ny, index = plan.step, plan.nx, plan.ny, plan.index
    cols = [(i, ox + (i + 0.5) * pw) for i in range(i0, i1)]
    cols = [(i, x, math.floor((x - plan.x0) / s)) for i, x in cols]
    cols = [(i, x, g) for i, x, g in cols if 0 <= g < nx]
    for j in range(j0, j1):
        y = oy + (j + 0.5) * ph
        gj = math.floor((y - plan.y0) / s)
        if not 0 <= gj < ny:
            continue
        base = gj * nx
        for i, x, g in cols:
            if index[base + g] >= 0:
                yield i, j, x, y


def mend_tiles(store, bounds, plan: Plan, hollow, box, cache=None, source=None) -> dict[int, bytes]:
    """The filled hollows mended in every tile of a tile set (rusemod.tmst.Tmst over `bounds`, groundpaint.map_bounds)
    that `box` (x0, y0, x1, y1: the filled squares' bounds) touches, at every level, each pixel through `plan` at its
    own resolution; `hollow(x, y)`: where no ground is read from. `source`: the tile set the banks' ground is read from
    (default `store`; the map's own, if paint is on `store` already, so none is copied in). Only the 4x4 blocks with a
    mended pixel are encoded again. Returns {tile index: new tile record} for Tmst.members."""
    out = {}
    samplers: dict = {}
    source = store if source is None else source
    for tile in store.tiles:
        rx0, ry0, rx1, ry1 = _tile_rect(store, tile, bounds)
        if rx0 >= box[2] or rx1 <= box[0] or ry0 >= box[3] or ry1 <= box[1]:
            continue
        blocks, w, h = _blocks(store, tile, cache)
        pw, ph = (rx1 - rx0) / w, (ry1 - ry0) / h
        if tile.level not in samplers:
            samplers[tile.level] = _picture_sampler(source, bounds, tile.level, cache)
        at = samplers[tile.level]
        i0, i1 = max(0, math.floor((box[0] - rx0) / pw)), min(w, math.ceil((box[2] - rx0) / pw))
        j0, j1 = max(0, math.floor((box[1] - ry0) / ph)), min(h, math.ceil((box[3] - ry0) / ph))
        byblock: dict = {}
        for i, j, x, y in _to_fill(plan, i0, i1, j0, j1, rx0, ry0, pw, ph):
            v = plan.fill_value(x, y, at, hollow)
            if v is not None:
                byblock.setdefault((j // 4) * (w // 4) + i // 4, []).append(((j % 4) * 4 + i % 4, v))
        if not byblock:
            continue
        for kb, pix in byblock.items():
            pixels = dxt.block_pixels(bytes(blocks[8 * kb:8 * kb + 8]))
            for idx, v in pix:
                pixels[idx] = tuple(max(0, min(255, c)) for c in v[:3])
            blocks[8 * kb:8 * kb + 8] = dxt.encode_block(pixels)
        out[tile.index] = zipo_tile(bytes(blocks), w, h)
    return out


def mend_map(read, path_of, changed: dict, before, after, areas, cache=None) -> tuple[Filled | None, list[str]]:
    """The build's step after its ground edits: the hollows of the old ground (`before`, a Tms) that the new ground
    (`after`) fills, within the strokes' `areas` ((x, y, radius) each), mended in both tile sets and the close-up
    map. `read(member)` gives the map pack's own member (the pictures the banks' ground is read from) or None,
    `path_of(member)` its full path; the mended members go into `changed` (the build's chain for this map). Returns
    (the Filled, for the low cover the build takes off there; or None when nothing is filled), notes."""
    from .groundpaint import DETAIL, LODS, grid_bounds, map_bounds
    from .tmst import Tmst
    b = before.bounds
    if not areas:
        return None, []
    box = (max(b[0], min(x - r for x, _y, r in areas)), max(b[1], min(y - r for _x, y, r in areas)),
           min(b[3], max(x + r for x, _y, r in areas)), min(b[4], max(y + r for _x, y, r in areas)))
    if box[0] >= box[2] or box[1] >= box[3]:
        return None, []
    filled = Filled(before, after, box)
    if not filled.count():
        return None, []
    plan = plan_filled(filled)
    fbox = filled.box()
    mesh = read("output\\highdef.tms")
    bounds = map_bounds(mesh)
    notes, painted = [], 0
    for lod in LODS:
        index, chunk = read(f"output\\{lod}.tmst_pc"), read(f"output\\{lod}.tmst_chunk_pc")
        if index is None or chunk is None:
            continue
        own = Tmst(index, chunk)
        own.lod = lod
        own.index_path, own.chunk_path = path_of(f"output\\{lod}.tmst_pc"), path_of(f"output\\{lod}.tmst_chunk_pc")
        tiles = mend_tiles(own, bounds, plan, filled.hollow, fbox, cache)
        if tiles:
            changed.update(own.members(tiles))
            painted += len(tiles)
    detail = read(DETAIL)
    if detail is not None:
        new, more = mend_detail(detail, grid_bounds(mesh), plan, filled.hollow, fbox)
        notes += more
        if new:
            changed[path_of(DETAIL)] = new
    area = filled.count() * filled.step * filled.step / (METRE * METRE) / 10000.0
    notes.insert(0, f"filled riverbeds and hollows (the old ground's, raised flat): {area:.1f} ha mended from both "
                    f"banks in {painted} picture tile(s)")
    return filled, notes


def mend_detail(raw: bytes, bounds, plan: Plan, hollow, box, source: bytes | None = None) -> tuple[bytes, list[str]]:
    """The filled hollows mended in the close-up map too (`output\\div_map.tgv_pc`, one DXT5 picture over `bounds`,
    groundpaint.grid_bounds), all four channels, as mend_tiles; `source`: the record the banks' values are read from
    (default `raw`). Returns (the new record, notes), or (b"", notes)."""
    tex = Tgv(raw)
    payload = tex.payload(0)
    if not tex.format.upper().startswith("DXT5") or payload[:4] != b"ZIPO":
        return b"", [f"close-up map: {tex.format} {payload[:4]!r} can't be mended yet"]
    blocks = bytearray(zipo_unpack(payload))
    old = zipo_unpack(Tgv(source).payload(0)) if source is not None else bytes(blocks)
    w, h = tex.width, tex.height
    if len(blocks) != w * h or len(old) != len(blocks):
        raise PaintError(f"the close-up map holds {len(blocks)} bytes, not {w}x{h} DXT5")
    x0, y0, x1, y1 = bounds
    pw, ph = (x1 - x0) / w, (y1 - y0) / h
    nbx = w // 4
    decoded: dict = {}

    def value(x, y):
        a, b = math.floor((x - x0) / pw), math.floor((y - y0) / ph)
        if not (0 <= a < w and 0 <= b < h):
            return None
        k = (b // 4) * nbx + a // 4
        if k not in decoded:
            decoded[k] = dxt.dxt5_block(bytes(old[16 * k:16 * k + 16]))
        rgb, alpha = decoded[k]
        i = (b % 4) * 4 + a % 4
        return rgb[i] + (alpha[i],)
    i0, i1 = max(0, math.floor((box[0] - x0) / pw)), min(w, math.ceil((box[2] - x0) / pw))
    j0, j1 = max(0, math.floor((box[1] - y0) / ph)), min(h, math.ceil((box[3] - y0) / ph))
    byblock: dict = {}
    for i, j, x, y in _to_fill(plan, i0, i1, j0, j1, x0, y0, pw, ph):
        v = plan.fill_value(x, y, value, hollow)
        if v is not None:
            byblock.setdefault((j // 4) * nbx + i // 4, []).append(((j % 4) * 4 + i % 4, v))
    if not byblock:
        return b"", []
    for kb, pix in byblock.items():
        rgb, alpha = dxt.dxt5_block(bytes(blocks[16 * kb:16 * kb + 16]))
        for idx, v in pix:
            rgb[idx] = tuple(max(0, min(255, c)) for c in v[:3])
            alpha[idx] = max(0, min(255, v[3]))
        blocks[16 * kb:16 * kb + 16] = dxt.encode_dxt5_block(rgb, alpha)
    return _tgv_with_payload(raw, zipo_pack(bytes(blocks))), [f"close-up map: {len(byblock)} block(s) mended"]
