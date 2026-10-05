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
import os
import sys
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
WINDOW = 2000 * METRE  # the side of the squares the map is mended in, one after another (mend_map)
NEAR_WATER = 2 * REACH + WIDER + 2 * STEP  # how far from the old water a riverbed's hollow can reach
COARSE = 10 * METRE    # the grid the old water is first looked for on, to pick the windows

_WHOLE = []  # [rusemod.mendnp, or None without numpy], looked for once


def whole_arrays():
    """rusemod.mendnp, the mend on whole grids, when numpy is there (the apps carry it); None without it. With it,
    the hollows, the plans and the tiles' pixels are worked out for a whole grid at once: the same sums in the same
    order, so the same bytes, many times sooner. The loops in this file are what that is checked against, and what
    runs without numpy."""
    if not _WHOLE:
        try:
            from . import mendnp
            _WHOLE.append(mendnp)
        except ImportError:
            _WHOLE.append(None)
    return _WHOLE[0]


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
        r, w = max(1, round(reach / step)), round(wider / step)
        arrays = whole_arrays()
        if arrays is not None:
            bits = arrays.gorge_bits(tms, self.x0, self.y0, self.nx, self.ny, step, r, deep, w)
            if bits is not None:
                self.bits = bits
                return
        z = heights(tms, self.x0, self.y0, self.nx, self.ny, step)
        low = min((v for row in z for v in row if v is not None), default=0.0)
        z = [[low if v is None else v for v in row] for row in z]
        filled = _filter2(_filter2(z, r, max), r, min)
        hollow = [[1 if f - h > deep else 0 for f, h in zip(frow, zrow)] for frow, zrow in zip(filled, z)]
        del filled, z  # a whole map's grid is millions of numbers: only the answer is kept
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
        arrays = whole_arrays()
        if arrays is not None:
            self.bits = arrays.filled_bits(self.old.bits, new.bits)
            return
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
        """The filled squares' bounds (x0, y0, x1, y1), or None for none (without numpy, each row's first and last
        filled square found by stripping its empty ones: a whole map's windows hold 18 million squares)."""
        s = self.step
        arrays = whole_arrays()
        if arrays is not None:
            ends = arrays.bits_box(self.bits, self.nx, self.ny)
            if ends is None:
                return None
            c0, r0, c1, r1 = ends
            return self.x0 + c0 * s, self.y0 + r0 * s, self.x0 + (c1 + 1) * s, self.y0 + (r1 + 1) * s
        nx, rows, first, last = self.nx, [], None, None
        for j in range(self.ny):
            row = bytes(self.bits[j * nx:(j + 1) * nx])
            kept = row.rstrip(b"\0")
            if kept:
                rows.append(j)
                lo, hi = len(row) - len(row.lstrip(b"\0")), len(kept) - 1
                first, last = lo if first is None else min(first, lo), hi if last is None else max(last, hi)
        if not rows:
            return None
        return self.x0 + first * s, self.y0 + rows[0] * s, self.x0 + (last + 1) * s, self.y0 + (rows[-1] + 1) * s


def wet_bits(tms, x0: float, y0: float, nx: int, ny: int, step: float) -> bytearray:
    """Where the mesh `tms` (rusemod.tms.Tms) has water (its water triangles, list 1) on an nx x ny grid from
    (x0, y0), `step` apart: 1 for a square whose middle is under water."""
    arrays = whole_arrays()
    if arrays is not None:
        wet = arrays.wet_bits(tms, x0, y0, nx, ny, step)
        if wet is not None:
            return wet
    wet = bytearray(nx * ny)
    for c in tms.cells:
        tri = c.triangles(1)
        if not tri:
            continue
        pts = [((tms.to_world(0, p[0]) - x0) / step - 0.5, (tms.to_world(1, p[1]) - y0) / step - 0.5)
               for p in c.positions()]
        for t in range(0, len(tri) - 2, 3):
            a, b, d = pts[tri[t]], pts[tri[t + 1]], pts[tri[t + 2]]
            den = (b[1] - d[1]) * (a[0] - d[0]) + (d[0] - b[0]) * (a[1] - d[1])
            if not den:
                continue
            i0, i1 = max(math.ceil(min(a[0], b[0], d[0])), 0), min(math.floor(max(a[0], b[0], d[0])), nx - 1)
            j0, j1 = max(math.ceil(min(a[1], b[1], d[1])), 0), min(math.floor(max(a[1], b[1], d[1])), ny - 1)
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    l1 = ((b[1] - d[1]) * (i - d[0]) + (d[0] - b[0]) * (j - d[1])) / den
                    l2 = ((d[1] - a[1]) * (i - d[0]) + (a[0] - d[0]) * (j - d[1])) / den
                    if l1 >= -1e-9 and l2 >= -1e-9 and 1 - l1 - l2 >= -1e-9:
                        wet[j * nx + i] = 1
    return wet


def riverbeds_only(filled: Filled, wet: bytearray) -> int:
    """Keep only the stretches of `filled`'s squares (side by side, not corner to corner) that reach the old water
    (`wet`, on the same grid): a riverbed raised flat. A dry valley or dip raised flat was a field's picture before and
    is one now; mending it cost most of the time on a whole flattened map (all of Blitz: 3.16 km2 filled, 1.33 km2 of
    it reaching the water, 2026-10-04). Returns how many squares were let go."""
    nx, ny, bits = filled.nx, filled.ny, filled.bits
    arrays = whole_arrays()
    if arrays is not None:
        gone = arrays.riverbeds_only(bits, wet, nx, ny)
        if gone is not None:
            return gone
    seen = bytearray(nx * ny)
    gone = 0
    for k in range(nx * ny):
        if not bits[k] or seen[k]:
            continue
        stretch, q, wets = [k], deque([k]), bool(wet[k])
        seen[k] = 1
        while q:
            m = q.popleft()
            i, j = m % nx, m // nx
            for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if 0 <= a < nx and 0 <= b < ny:
                    n = b * nx + a
                    if bits[n] and not seen[n]:
                        seen[n] = 1
                        q.append(n)
                        stretch.append(n)
                        wets = wets or bool(wet[n])
        if not wets:
            for m in stretch:
                bits[m] = 0
            gone += len(stretch)
    return gone


_FILLED = bytes([0] + [1] * 255)  # bytes.translate: any square set to 1, an empty one 0


def _spread(rows: list[list[int]], r: int) -> bytearray:
    """_filter2(rows, r, max) for a grid of 0s and 1s, as its rows' bytes one after another: each row read as one
    number, a byte a square, so a 1 spreads r squares either way in a few shifts, then r rows up and down."""
    nx, ny = len(rows[0]), len(rows)
    whole = (1 << 8 * nx) - 1
    across = []
    for row in rows:
        v = int.from_bytes(bytes(row), "big")
        h = v
        for k in range(1, r + 1):
            h |= (v << 8 * k) | (v >> 8 * k)
        across.append(h & whole)
    out = bytearray()
    for j in range(ny):
        v = 0
        for k in range(max(0, j - r), min(ny, j + r + 1)):
            v |= across[k]
        out += v.to_bytes(nx, "big")
    return out


class Riverbeds:
    """The riverbeds a build mends, window by window (mend_map): each window's Filled, holding only its own square
    of the map (a window's grid reaches past it, for the banks). Answers as a Filled does, for the build's low cover."""

    NEAR = 30 * METRE   # touches() asked with a reach up to this answers "no" at once far from every riverbed
    CELL = 8 * METRE    # the squares of that first look

    def __init__(self, x0: float, y0: float, side: float, parts: dict):
        self.x0, self.y0, self.side, self.parts = x0, y0, side, parts  # (window column, row) -> Filled

    def holds(self, x: float, y: float) -> bool:
        part = self.parts.get((int((x - self.x0) // self.side), int((y - self.y0) // self.side)))
        return part is not None and part.holds(x, y)

    def _near_map(self):
        """(x0, y0, nx, ny, bits): the CELL squares within NEAR (and a square) of a riverbed square, made on first use:
        the build asks touches() of every low object in the riverbeds' box (millions on a big map)."""
        near = getattr(self, "_near", None)
        if near is not None:
            return near
        box = self.box()
        c = self.CELL
        pad = self.NEAR + 2 * c
        x0, y0 = box[0] - pad, box[1] - pad
        nx, ny = max(1, math.ceil((box[2] + pad - x0) / c)), max(1, math.ceil((box[3] + pad - y0) / c))
        arrays = whole_arrays()
        if arrays is not None:
            self._near = (x0, y0, nx, ny, arrays.near_bits(self.parts.values(), x0, y0, nx, ny, c,
                                                           math.ceil(self.NEAR / c) + 1))
            return self._near
        rows = [[0] * nx for _ in range(ny)]
        for part in self.parts.values():
            s, pnx = part.step, part.nx
            filled = part.bits.translate(_FILLED)  # 1 for a filled square: found one by one, the empty ones skipped
            k = filled.find(1)
            while k >= 0:
                x, y = part.x0 + (k % pnx + 0.5) * s, part.y0 + (k // pnx + 0.5) * s
                rows[int((y - y0) // c)][int((x - x0) // c)] = 1
                k = filled.find(1, k + 1)
        self._near = (x0, y0, nx, ny, _spread(rows, math.ceil(self.NEAR / c) + 1))
        return self._near

    def touches(self, x: float, y: float, reach: float) -> bool:
        if reach <= self.NEAR and self.parts:
            x0, y0, nx, ny, bits = self._near_map()
            i, j = int((x - x0) // self.CELL), int((y - y0) // self.CELL)
            if not (0 <= i < nx and 0 <= j < ny) or not bits[j * nx + i]:
                return False
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
        return sum(p.count() for p in self.parts.values())

    def box(self) -> tuple[float, float, float, float] | None:
        boxes = [b for b in (p.box() for p in self.parts.values()) if b is not None]
        if not boxes:
            return None
        return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
                max(b[3] for b in boxes))


def _windows(before, box, areas) -> list[tuple[int, int, tuple[float, float, float, float]]]:
    """The windows of the map to mend: WINDOW squares (from the box's corner) over `box`, each kept when a square of
    COARSE within NEAR_WATER of the old ground's water lies in it inside a stroke's circle. [(column, row, its square
    clipped to the box)], in order."""
    s = COARSE
    pad = NEAR_WATER + s
    x0, y0 = box[0] - pad, box[1] - pad
    nx, ny = max(1, math.ceil((box[2] + pad - x0) / s)), max(1, math.ceil((box[3] + pad - y0) / s))
    wet = wet_bits(before, x0, y0, nx, ny, s)
    if not any(wet):
        return []
    r = max(1, math.ceil(NEAR_WATER / s))
    arrays = whole_arrays()
    if arrays is not None:
        near = arrays.widened_rows(wet, nx, ny, r)
    else:
        near = _filter2([list(wet[j * nx:(j + 1) * nx]) for j in range(ny)], r, max)
    out = []
    cols, rows = math.ceil((box[2] - box[0]) / WINDOW), math.ceil((box[3] - box[1]) / WINDOW)
    for wj in range(rows):
        for wi in range(cols):
            core = (box[0] + wi * WINDOW, box[1] + wj * WINDOW, min(box[2], box[0] + (wi + 1) * WINDOW),
                    min(box[3], box[1] + (wj + 1) * WINDOW))
            i0, i1 = max(0, math.floor((core[0] - x0) / s)), min(nx, math.ceil((core[2] - x0) / s))
            j0, j1 = max(0, math.floor((core[1] - y0) / s)), min(ny, math.ceil((core[3] - y0) / s))
            mine = [(ax, ay, ar) for ax, ay, ar in areas
                    if ax + ar > core[0] and ax - ar < core[2] and ay + ar > core[1] and ay - ar < core[3]]
            if not mine:
                continue
            keep = False
            for j in range(j0, j1):
                row = near[j]
                y = y0 + (j + 0.5) * s
                for i in range(i0, i1):
                    if row[i]:
                        x = x0 + (i + 0.5) * s
                        if any((x - ax) ** 2 + (y - ay) ** 2 <= ar * ar for ax, ay, ar in mine):
                            keep = True
                            break
                if keep:
                    break
            if keep:
                out.append((wi, wj, core))
    return out


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
        arrays = whole_arrays()
        got = arrays.plan(nx, ny, fill, bad, smooth) if arrays is not None else None
        if got is not None:
            self.index, self.ux, self.uy, self.d1, self.width = got
            return
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
    return mend_tiles_parts(store, bounds, [(plan, hollow, box)], cache, source, quick=False)


def mend_tiles_parts(store, bounds, parts, cache=None, source=None, quick: bool = True) -> dict[int, bytes]:
    """mend_tiles for several Plans at once (`parts`: [(plan, hollow, box)], one per window of mend_map, their squares
    to fill apart): each tile is read and written once, each 4x4 block encoded once with all its mended pixels.
    `quick`: blocks encoded with dxt.encode_block_quick."""
    out = {}
    samplers: dict = {}
    source = store if source is None else source
    for tile in store.tiles:
        record = _mend_tile(store, tile, bounds, parts, samplers, source, cache, quick)
        if record is not None:
            out[tile.index] = record
    return out


def _touches(store, tile, bounds, parts) -> list:
    rx0, ry0, rx1, ry1 = _tile_rect(store, tile, bounds)
    return [p for p in parts if not (rx0 >= p[2][2] or rx1 <= p[2][0] or ry0 >= p[2][3] or ry1 <= p[2][1])]


def _mend_tile(store, tile, bounds, parts, samplers: dict, source, cache, quick: bool) -> bytes | None:
    """One tile of mend_tiles_parts: its new record, or None when nothing in it is mended. `samplers`: the map's own
    picture at each level (groundpaint._picture_sampler), made on first use."""
    mine = _touches(store, tile, bounds, parts)
    if not mine:
        return None
    arrays = whole_arrays()
    if arrays is not None:  # all of its pixels at once: the same record (None: something only the loops below do)
        record = arrays.mend_tile(sys.modules[__name__], store, tile, bounds, mine, samplers, source, cache, quick)
        if record is not None:
            return record or None
    rx0, ry0, rx1, ry1 = _tile_rect(store, tile, bounds)
    blocks, w, h = _blocks(store, tile, cache)
    pw, ph = (rx1 - rx0) / w, (ry1 - ry0) / h
    if tile.level not in samplers:
        samplers[tile.level] = _picture_sampler(source, bounds, tile.level, cache)
    at = samplers[tile.level]
    byblock: dict = {}
    for plan, hollow, box in mine:
        i0, i1 = max(0, math.floor((box[0] - rx0) / pw)), min(w, math.ceil((box[2] - rx0) / pw))
        j0, j1 = max(0, math.floor((box[1] - ry0) / ph)), min(h, math.ceil((box[3] - ry0) / ph))
        for i, j, x, y in _to_fill(plan, i0, i1, j0, j1, rx0, ry0, pw, ph):
            v = plan.fill_value(x, y, at, hollow)
            if v is not None:
                byblock.setdefault((j // 4) * (w // 4) + i // 4, []).append(((j % 4) * 4 + i % 4, v))
    if not byblock:
        return None
    encode = dxt.encode_block_quick if quick else dxt.encode_block
    for kb, pix in byblock.items():
        pixels = dxt.block_pixels(bytes(blocks[8 * kb:8 * kb + 8]))
        for idx, v in pix:
            pixels[idx] = tuple(max(0, min(255, c)) for c in v[:3])
        blocks[8 * kb:8 * kb + 8] = encode(pixels)
    return zipo_tile(bytes(blocks), w, h)


def _mend_window(before, after, wi: int, wj: int, core) -> tuple:
    """One window of mend_map: (wi, wj, its Filled holding only riverbeds in its own square or None, their Plan or
    None, the dry squares let go). Its grid reaches REACH past its square, so its hollows and banks are whole."""
    reach = (core[0] - REACH, core[1] - REACH, core[2] + REACH, core[3] + REACH)
    filled = Filled(before, after, reach)
    if not filled.count():
        return wi, wj, None, None, 0
    dry = riverbeds_only(filled, wet_bits(before, filled.x0, filled.y0, filled.nx, filled.ny, filled.step))
    s, nx = filled.step, filled.nx
    arrays = whole_arrays()
    if arrays is not None:  # its own square only: the next window's squares are that window's
        arrays.keep_within(filled.bits, nx, filled.x0, filled.y0, s, core)
    else:
        for k in range(nx * filled.ny):
            if filled.bits[k]:
                x, y = filled.x0 + (k % nx + 0.5) * s, filled.y0 + (k // nx + 0.5) * s
                if not (core[0] <= x < core[2] and core[1] <= y < core[3]):
                    filled.bits[k] = 0
    if not filled.count():
        return wi, wj, None, None, dry
    return wi, wj, filled, plan_filled(filled), dry


# --- the mend shared out to worker programs, one per core but one (each answer is the same as one program's) ---
WORKERS = max(1, min(8, (os.cpu_count() or 1) - 1))
_WORK: dict = {}  # in a worker: what its jobs share (set by its starter)


def _start_windows(before_raw: bytes, after_raw: bytes, corners=None) -> None:
    """`corners`: the two meshes' triangles as mendnp.corners_to_share read them (on whole grids), so no worker reads
    them again."""
    from .tms import Tms
    _WORK["before"], _WORK["after"] = Tms(before_raw), Tms(after_raw)
    arrays = whole_arrays()
    if corners is not None and arrays is not None:
        arrays.corners_shared(_WORK["before"], _WORK["after"], corners)


def _window_job(job: tuple) -> tuple:
    return _mend_window(_WORK["before"], _WORK["after"], *job)


def _start_tiles(pack_file: str, lod: str, parts: list, bounds, cache) -> None:
    from .edat import Edat
    from .tmst import Tmst
    arc = Edat.open(pack_file)
    store = Tmst(bytes(arc.read(arc.find(f"output\\{lod}.tmst_pc"))), arc.read(arc.find(f"output\\{lod}.tmst_chunk_pc")))
    _WORK.update(arc=arc, store=store, parts=parts, bounds=bounds, cache=cache, samplers={},
                 tiles={t.index: t for t in store.tiles})


def _tile_job(indices: list) -> dict:
    store, out = _WORK["store"], {}
    for i in indices:
        record = _mend_tile(store, _WORK["tiles"][i], _WORK["bounds"], _WORK["parts"], _WORK["samplers"], store,
                            _WORK["cache"], True)
        if record is not None:
            out[i] = record
    return out


def _pool(start, args, workers: int):
    from concurrent.futures import ProcessPoolExecutor
    return ProcessPoolExecutor(max_workers=workers, initializer=start, initargs=args)


def workers_start() -> str:
    """For the apps' self-test: worker programs start and answer (the mend shares its work out to them)."""
    with _pool(_start_windows_probe, (), 2) as pool:
        got = sorted(pool.map(_probe, [1, 2, 3]))
    if got != [2, 4, 6]:
        raise RuntimeError(f"the workers answered {got}")
    return f"{WORKERS} worker(s) on this PC"


def _start_windows_probe() -> None:
    _WORK["probe"] = 2


def _probe(n: int) -> int:
    return n * _WORK["probe"]


def mend_map(read, path_of, changed: dict, before, after, areas, cache=None, pack_file: str | None = None,
             workers: int | None = None) -> tuple[Riverbeds | None, list[str]]:
    """The build's step after its ground edits: the riverbeds of the old ground (`before`, a Tms) that the new ground
    (`after`) fills, within the strokes' `areas` ((x, y, radius) each), mended in both tile sets and the close-up
    map. `read(member)` gives the map pack's own member (the pictures the banks' ground is read from) or None,
    `path_of(member)` its full path; the mended members go into `changed` (the build's chain for this map). Returns
    (the Riverbeds, for the low cover the build takes off there; or None when nothing is filled), notes.

    `pack_file`: the map's pack as a file whose members are the ones `read` gives (none for a pack the build changed
    in memory): then the windows and the tiles are shared out to `workers` programs (default WORKERS) when there is
    more than one window's work, each answer the same as one program's."""
    from .groundpaint import DETAIL, LODS, grid_bounds, map_bounds
    from .tmst import Tmst
    b = before.bounds
    if not areas:
        return None, []
    box = (max(b[0], min(x - r for x, _y, r in areas)), max(b[1], min(y - r for _x, y, r in areas)),
           min(b[3], max(x + r for x, _y, r in areas)), min(b[4], max(y + r for _x, y, r in areas)))
    if box[0] >= box[2] or box[1] >= box[3]:
        return None, []
    # window by window, only where the old ground had water under the strokes: a riverbed is found within NEAR_WATER
    # of its water, and each window's grid reaches REACH past its square, so its hollows and banks are whole there
    jobs = _windows(before, box, areas)
    workers = WORKERS if workers is None else workers
    share = pack_file is not None and workers > 1 and len(jobs) > 1
    done, alone = [], []  # alone: why the workers couldn't do it (said: the same work then takes one core many times longer)
    if share:
        arrays = whole_arrays()
        corners = arrays.corners_to_share(before, after) if arrays is not None else None
        try:
            with _pool(_start_windows, (before.to_bytes(), after.to_bytes(), corners),
                       min(workers, len(jobs))) as pool:
                done = list(pool.map(_window_job, jobs))
        except Exception as exc:  # noqa: BLE001 - workers that can't start: the same work in this program
            share, done = False, []
            alone.append(f"{type(exc).__name__}: {exc}")
    if not done:
        done = [_mend_window(before, after, *job) for job in jobs]
    parts, filled_parts, dry = [], {}, 0
    for wi, wj, filled, plan, d in done:  # in the windows' order: the same answer however the work was shared
        dry += d
        if filled is not None:
            parts.append((plan, filled.hollow, filled.box()))
            filled_parts[(wi, wj)] = filled
    if not parts:
        return None, []
    beds = Riverbeds(box[0], box[1], WINDOW, filled_parts)
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
        tiles = None
        todo = [t.index for t in own.tiles if _touches(own, t, bounds, parts)]
        if share and len(todo) > 1:
            n = min(workers, len(todo))
            batches = [todo[k::n] for k in range(n)]  # every n-th tile: the expensive ones spread out
            try:
                with _pool(_start_tiles, (pack_file, lod, parts, bounds, cache), n) as pool:
                    tiles = {}
                    for got in pool.map(_tile_job, batches):
                        tiles.update(got)
                tiles = {i: tiles[i] for i in sorted(tiles)}
            except Exception as exc:  # noqa: BLE001 - workers that can't start: the same work in this program
                tiles = None
                alone.append(f"{type(exc).__name__}: {exc}")
        if tiles is None:
            tiles = mend_tiles_parts(own, bounds, parts, cache)
        if tiles:
            changed.update(own.members(tiles))
            painted += len(tiles)
    detail = read(DETAIL)
    if detail is not None:
        new, more = mend_detail_parts(detail, grid_bounds(mesh), parts)
        notes += more
        if new:
            changed[path_of(DETAIL)] = new
    ha = (METRE * METRE) * 10000.0
    step2 = STEP * STEP
    notes.insert(0, f"filled riverbeds (the old ground's, raised flat): {beds.count() * step2 / ha:.1f} ha mended from "
                    f"both banks in {painted} picture tile(s)"
                    + (f"; dry hollows raised flat left as they are ({dry * step2 / ha:.1f} ha)" if dry else ""))
    if alone:
        notes.insert(1, f"the riverbeds were mended on one core: the worker programs couldn't start ({alone[0]})")
    return beds, notes


def mend_detail(raw: bytes, bounds, plan: Plan, hollow, box, source: bytes | None = None) -> tuple[bytes, list[str]]:
    """The filled hollows mended in the close-up map too (`output\\div_map.tgv_pc`, one DXT5 picture over `bounds`,
    groundpaint.grid_bounds), all four channels, as mend_tiles; `source`: the record the banks' values are read from
    (default `raw`). Returns (the new record, notes), or (b"", notes)."""
    return mend_detail_parts(raw, bounds, [(plan, hollow, box)], source)


def mend_detail_parts(raw: bytes, bounds, parts, source: bytes | None = None) -> tuple[bytes, list[str]]:
    """mend_detail for several Plans at once (`parts`, as mend_tiles_parts)."""
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
    arrays = whole_arrays()
    if arrays is not None:  # all of its pixels at once: the same blocks (None: something only the loops below do)
        got = arrays.mend_detail(sys.modules[__name__], bytes(blocks), bytes(old), w, h, bounds, parts)
        if got is not None:
            if not got[1]:
                return b"", []
            return _tgv_with_payload(raw, zipo_pack(got[0])), [f"close-up map: {got[1]} block(s) mended"]
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
    byblock: dict = {}
    for plan, hollow, box in parts:
        i0, i1 = max(0, math.floor((box[0] - x0) / pw)), min(w, math.ceil((box[2] - x0) / pw))
        j0, j1 = max(0, math.floor((box[1] - y0) / ph)), min(h, math.ceil((box[3] - y0) / ph))
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
