"""The riverbed mend on whole grids (numpy): rusemod.mend's own sums, in its order, for a whole grid of squares or all
of a tile's pixels at once instead of one at a time, so a window of the map and a picture tile come out the same
bytes many times sooner. rusemod.mend asks for this module through its whole_arrays() and keeps its own loops: they
are what every piece here is checked against (tests/test_mend.py), and what runs without numpy.

How the same bytes are kept:
  - the sums are the loops' own, in their order: each +, -, *, / and square root of numpy's float64 gives the same
    bits as Python's; a sum the loops add item after item is added in that order here (a running sum, or a short
    loop over whole arrays);
  - round() is numpy's rint (halves to even); `//` on floats is floor_div below (numpy's floor_divide, sooner);
    math.hypot stays Python's own, asked for each value (numpy's differs in the last bit);
  - the highest, the lowest and "any" of a set don't depend on the order they are taken in.
What is still walked square by square: the nearest bank of each hollow square (Plan's two passes: a square takes its
neighbours' answers as they come, so the order is part of the answer), over the hollows' own squares only.

A function here gives None for what it leaves to the loops."""
from __future__ import annotations

import math
import struct
import weakref
from array import array
from collections import OrderedDict

from . import dxtnp
from .numpy2 import np

_I = np.int64
CHUNK = 1 << 18  # squares looked at together when a mesh is laid on a grid (a triangle's: the ones its box holds)


def floor_div(a, b: float):
    """`a // b` for an array of floats, as Python gives it (which square or tile a point lies in). numpy's
    floor_divide goes by the remainder as Python does, and is slow; the division floored is the same answer except
    where the division comes out a whole number (the true quotient may lie a hair under it, and its floor one less),
    so only those are asked of floor_divide."""
    d = a / b
    q = np.floor(d)
    whole = np.flatnonzero(d == q)
    if len(whole):
        q[whole] = np.floor_divide(a[whole], b)
    return q


# --- a mesh laid on a grid (mend.heights, mend.wet_bits) -------------------------------------------------------------
_MESHES = weakref.WeakKeyDictionary()  # a mesh -> {triangle list: (what it was read from, its corners)}


def _read_from(tms):
    """What a mesh's corners are read from: its bounds, and each cell's coded points and triangle lists, the same
    objects for as long as it isn't edited (an edit writes new ones). None for a mesh whose cells don't say (it is
    read again each time)."""
    out = [tuple(getattr(tms, "bounds", ()))]
    for c in tms.cells:
        vb, ib = getattr(c, "vb", None), getattr(c, "ib", None)
        if vb is None or ib is None:
            return None
        out.append((vb, tuple(ib)))
    return out


def _unchanged(a: list, b: list) -> bool:
    return (len(a) == len(b) and a[0] == b[0]
            and all(p is q and len(s) == len(t) and all(x is y for x, y in zip(s, t))
                    for (p, s), (q, t) in zip(a[1:], b[1:])))


def _world(tms, axis: int, values) -> np.ndarray:
    """tms.to_world for a cell's values on one axis: asked once for each different value, as the loops ask it."""
    different, where = np.unique(np.array(values), return_inverse=True)
    return np.array([tms.to_world(axis, q) for q in different.tolist()], dtype=np.float64)[where]


def _corners(tms, which: int):
    """Every triangle of list `which` (0 the ground, 1 the part under water) as its three corners' world x, y and z,
    (n, 3) each: the cells in order and each cell's triangles in order, as the loops go through them. Kept with the
    mesh until it is edited: a window of the map asks for the same mesh's again and again."""
    stamp = _read_from(tms)
    kept = None
    if stamp is not None:
        try:
            kept = _MESHES.setdefault(tms, {})
        except TypeError:  # (a mesh that can't be held this way: read again each time)
            kept = None
        got = kept.get(which) if kept is not None else None
        if got is not None and _unchanged(got[0], stamp):
            return got[1]
    xs, ys, zs = [], [], []
    for c in tms.cells:
        pos = c.positions()
        tri = c.triangles(which) if pos else []
        n = len(tri) // 3
        if not n:
            continue
        t = np.array(tri[:3 * n], dtype=_I).reshape(n, 3)
        axes = list(zip(*pos))
        wx, wy, wz = (_world(tms, axis, axes[axis]) for axis in range(3))
        xs.append(wx[t])
        ys.append(wy[t])
        zs.append(wz[t])
    none = np.zeros((0, 3))
    out = tuple(np.concatenate(v) if v else none for v in (xs, ys, zs))
    if kept is not None:
        kept[which] = (stamp, out)
    return out


def corners_to_share(before, after):
    """The corners mend._mend_window asks for (the old ground's and its water's, the new ground's), read here once
    to hand to the worker programs with the two meshes (corners_shared): a worker then decodes neither mesh. None
    for a mesh whose bounds a worker's copy wouldn't have exactly (they are written as 32-bit numbers, as a mesh read
    from a file has them): each worker reads its own then."""
    try:
        for tms in (before, after):
            if list(struct.unpack("<6f", struct.pack("<6f", *tms.bounds))) != list(tms.bounds):
                return None
    except (AttributeError, TypeError, struct.error, OverflowError):
        return None
    return _corners(before, 0), _corners(before, 1), _corners(after, 0)


def corners_shared(before, after, corners: tuple) -> None:
    """In a worker: corners_to_share's answer, for its own copies of the same two meshes."""
    for tms, which, got in ((before, 0, corners[0]), (before, 1, corners[1]), (after, 0, corners[2])):
        stamp = _read_from(tms)
        if stamp is not None:
            _MESHES.setdefault(tms, {})[which] = (stamp, got)


def _held(corners, x0: float, y0: float, nx: int, ny: int, step: float):
    """The squares of an nx x ny grid from (x0, y0), `step` apart, whose middle each triangle holds, as mend.heights
    and mend.wet_bits find them (the same sums), in their order: triangle after triangle, each one's squares row by
    row. Gives them part by part: (which triangle, the square's place j * nx + i, its three weights). None instead of
    the first part for a mesh with a corner that isn't a number (the loops', and their error)."""
    X, Y = corners[0], corners[1]
    ax, ay = (X[:, 0] - x0) / step - 0.5, (Y[:, 0] - y0) / step - 0.5
    bx, by = (X[:, 1] - x0) / step - 0.5, (Y[:, 1] - y0) / step - 0.5
    cx, cy = (X[:, 2] - x0) / step - 0.5, (Y[:, 2] - y0) / step - 0.5
    if not all(bool(np.isfinite(v).all()) for v in (ax, ay, bx, by, cx, cy)):
        yield None
        return
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    byc, cxb, cya, axc = by - cy, cx - bx, cy - ay, ax - cx
    lo_i = np.maximum(np.ceil(np.minimum(np.minimum(ax, bx), cx)), 0.0)
    hi_i = np.minimum(np.floor(np.maximum(np.maximum(ax, bx), cx)), nx - 1.0)
    lo_j = np.maximum(np.ceil(np.minimum(np.minimum(ay, by), cy)), 0.0)
    hi_j = np.minimum(np.floor(np.maximum(np.maximum(ay, by), cy)), ny - 1.0)
    some = np.flatnonzero((den != 0.0) & (hi_i >= lo_i) & (hi_j >= lo_j))
    i0, j0 = lo_i[some].astype(_I), lo_j[some].astype(_I)
    wide, high = hi_i[some].astype(_I) - i0 + 1, hi_j[some].astype(_I) - j0 + 1
    count = wide * high
    ends = np.cumsum(count)
    start = 0
    while start < len(some):
        base = int(ends[start - 1]) if start else 0
        stop = max(start + 1, int(np.searchsorted(ends, base + CHUNK, side="right")))
        # each triangle's rows, then each row's squares; what is the same along a row is worked out once for the row
        tall = high[start:stop]
        of = np.repeat(np.arange(start, stop), tall)                 # each row's triangle, among `some`
        j = np.arange(len(of)) - np.repeat(np.cumsum(tall) - tall, tall) + j0[of]
        tri = some[of]
        dj = j - cy[tri]
        r1, r2 = cxb[tri] * dj, axc[tri] * dj
        across = wide[of]
        row = np.repeat(np.arange(len(of)), across)                  # each square's row
        at = np.arange(len(row))
        shift = i0[of] - (np.cumsum(across) - across)                # a square's place in the part, to its column
        i = at + shift[row]
        di, d = i - cx[tri][row], den[tri][row]
        l1 = (byc[tri][row] * di + r1[row]) / d
        l2 = (cya[tri][row] * di + r2[row]) / d
        l3 = 1 - l1 - l2
        ok = np.flatnonzero((l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9))
        inside = row[ok]
        yield tri[inside], (j * nx)[inside] + i[ok], l1[ok], l2[ok], l3[ok]
        start = stop


_LAID = []        # [(the grid, the triangles' x and y, the squares they hold)]: the last ground laid on a grid
KEEP_LAID = 2_000_000  # squares: a larger grid's aren't kept


def _held_again(corners, x0: float, y0: float, nx: int, ny: int, step: float):
    """_held, kept for the next mesh with the same triangles on the same grid: the new ground's after the old
    ground's (an edit moves heights, not where the triangles lie), so its squares are found once for both."""
    grid = (x0, y0, nx, ny, step)
    if _LAID and _LAID[0][0] == grid and all(a is b or np.array_equal(a, b) for a, b in zip(_LAID[0][1], corners)):
        yield from _LAID[0][2]
        return
    parts, n = [], 0
    for part in _held(corners, x0, y0, nx, ny, step):
        if parts is not None:
            n += 0 if part is None else len(part[1])
            if part is None or n > KEEP_LAID:
                parts = None
            else:
                parts.append(part)
        yield part
    _LAID[:] = [(grid, corners[:2], parts)] if parts is not None else []


def heights(tms, x0: float, y0: float, nx: int, ny: int, step: float):
    """mend.heights on a whole grid: (the heights (ny, nx), which squares the mesh covers); None left to the loops.
    A square two triangles hold takes the later one's height, as there."""
    corners = _corners(tms, 0)
    za, zb, zc = (np.ascontiguousarray(corners[2][:, n]) for n in range(3))
    z, covered = np.zeros(nx * ny), np.zeros(nx * ny, dtype=bool)
    mark, twice = np.zeros(nx * ny, dtype=_I), np.zeros(nx * ny, dtype=bool)
    for part in _held_again(corners, x0, y0, nx, ny, step):
        if part is None:
            return None
        tri, k, l1, l2, l3 = part
        v = l1 * za[tri] + l2 * zb[tri] + l3 * zc[tri]
        seq = np.arange(len(k))
        mark[k] = seq                 # one of each square's (whichever was written last)
        shared = mark[k] != seq       # a square held more than once: one of its others is here
        if shared.any():
            twice[k[shared]] = True
            more = np.flatnonzero(twice[k])  # every one on such a square, in order
            twice[k[shared]] = False
            once = np.ones(len(k), dtype=bool)
            once[more] = False
            z[k[once]] = v[once]
            order = more[np.argsort(k[more], kind="stable")]
            ks = k[order]
            last = np.ones(len(ks), dtype=bool)
            last[:-1] = ks[1:] != ks[:-1]
            z[ks[last]] = v[order[last]]
        else:
            z[k] = v
        covered[k] = True
    return z.reshape(ny, nx), covered.reshape(ny, nx)


def wet_bits(tms, x0: float, y0: float, nx: int, ny: int, step: float):
    """mend.wet_bits on a whole grid: its bytearray; None left to the loops."""
    wet = np.zeros(nx * ny, dtype=np.uint8)
    for part in _held(_corners(tms, 1), x0, y0, nx, ny, step):
        if part is None:
            return None
        wet[part[1]] = 1
    return bytearray(wet.tobytes())


# --- the highest, the lowest and the mean round each square (mend._slide, _filter2, _blur) ---------------------------
def _cut(a, axis: int, lo: int, hi: int):
    at = [slice(None)] * a.ndim
    at[axis] = slice(lo, hi)
    return a[tuple(at)]


def slide(a, r: int, highest: bool, axis: int):
    """The highest (or lowest) of `a` within r either side of each along an axis, by an edge over what there is:
    mend._slide for every row (axis 1) or column (axis 0) at once. The run is doubled up from one square (1, 2, 4,
    ...), then two of the longest are laid over its two ends."""
    if r <= 0:
        return a
    op = np.maximum if highest else np.minimum
    if a.dtype.kind == "f":
        edge = -np.inf if highest else np.inf
    else:
        edge = np.iinfo(a.dtype).min if highest else np.iinfo(a.dtype).max
    n, full = a.shape[axis], 2 * r + 1
    shape = list(a.shape)
    shape[axis] = n + 2 * r
    cur = np.full(shape, edge, dtype=a.dtype)
    _cut(cur, axis, r, r + n)[...] = a
    size = 1
    while 2 * size <= full:
        m = cur.shape[axis]
        cur = op(_cut(cur, axis, 0, m - size), _cut(cur, axis, size, m))
        size *= 2
    return op(_cut(cur, axis, 0, n), _cut(cur, axis, full - size, full - size + n))


def square(a, r: int, highest: bool):
    """mend._filter2 on a whole grid: a square window's highest or lowest (rows, then columns)."""
    return slide(slide(a, r, highest, 1), r, highest, 0)


def blur(vals, r: int):
    """mend._blur on a whole grid (ny, nx): running sums along each row, then each column, added in the loops' order
    (a running sum adds one value after another)."""
    if r <= 0:
        return vals.copy()
    out = vals
    for axis in (1, 0):
        n = out.shape[axis]
        zero = np.zeros([1 if k == axis else s for k, s in enumerate(out.shape)])
        acc = np.cumsum(np.concatenate([zero, out], axis=axis), axis=axis)  # (from 0.0, as the loops' running sum)
        new = np.empty_like(out)
        at = np.arange(n)
        a, b = np.maximum(0, at - r), np.minimum(n, at + r + 1)
        whole = np.flatnonzero((a == at - r) & (b == at + r + 1))  # the squares a whole window fits round: one stretch
        if len(whole):
            lo, hi = int(whole[0]), int(whole[-1]) + 1
            _cut(new, axis, lo, hi)[...] = (_cut(acc, axis, lo + r + 1, hi + r + 1)
                                            - _cut(acc, axis, lo - r, hi - r)) / (2 * r + 1)
            at = np.concatenate([at[:lo], at[hi:]])  # by the edges: over what there is
            a, b = np.maximum(0, at - r), np.minimum(n, at + r + 1)
        if len(at):
            span = (b - a) if axis == 1 else (b - a)[:, None]
            edge = (np.take(acc, b, axis=axis) - np.take(acc, a, axis=axis)) / span
            if axis == 1:
                new[:, at] = edge
            else:
                new[at, :] = edge
        out = new
    return out


# --- the hollows (mend.Gorge, Filled, riverbeds_only, Riverbeds) -----------------------------------------------------
def gorge_bits(tms, x0: float, y0: float, nx: int, ny: int, step: float, r: int, deep: float, w: int):
    """mend.Gorge's squares: the ground filled in (the highest within r, then the lowest of that) more than `deep`
    above it, widened by w. None left to the loops."""
    got = heights(tms, x0, y0, nx, ny, step)
    if got is None:
        return None
    z, covered = got
    if not np.isfinite(z).all():
        return None
    z[~covered] = z[covered].min() if covered.any() else 0.0
    hollow = ((square(square(z, r, True), r, False) - z) > deep).astype(np.uint8)
    if w:
        hollow = square(hollow, w, True)
    return bytearray(hollow.tobytes())


def filled_bits(old, new) -> bytearray:
    """mend.Filled's squares: a hollow of the old ground that the new ground no longer has."""
    a, b = np.frombuffer(old, dtype=np.uint8), np.frombuffer(new, dtype=np.uint8)
    return bytearray((a & (1 - b)).tobytes())


def bits_box(bits, nx: int, ny: int):
    """The first and last column and row with a square set: (column, row, column, row), or None for none."""
    b = np.frombuffer(bits, dtype=np.uint8).reshape(ny, nx) != 0
    rows = np.flatnonzero(b.any(axis=1))
    if not len(rows):
        return None
    cols = np.flatnonzero(b.any(axis=0))
    return int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])


def keep_within(bits, nx: int, x0: float, y0: float, step: float, core) -> None:
    """mend._mend_window's last step: the squares of `bits` whose middle lies outside `core` taken off, in place."""
    k = np.flatnonzero(np.frombuffer(bits, dtype=np.uint8))
    x, y = x0 + (k % nx + 0.5) * step, y0 + (k // nx + 0.5) * step
    out = k[~((core[0] <= x) & (x < core[2]) & (core[1] <= y) & (y < core[3]))]
    if len(out):
        left = np.frombuffer(bits, dtype=np.uint8).copy()
        left[out] = 0
        bits[:] = left.tobytes()


def riverbeds_only(bits, wet, nx: int, ny: int) -> int:
    """mend.riverbeds_only on a whole grid: the stretches of `bits` (side by side) that don't reach `wet` taken off, in
    place; how many squares went (None: left to the loops). A stretch is put together from its runs along the rows:
    runs one row apart that share a column belong together."""
    if not (isinstance(bits, bytearray) and isinstance(wet, (bytes, bytearray)) and len(bits) == len(wet) == nx * ny):
        return None
    b = np.frombuffer(bits, dtype=np.uint8).reshape(ny, nx) != 0
    edge = np.zeros((ny, nx + 2), dtype=np.int8)
    edge[:, 1:-1] = b
    turn = edge[:, 1:] - edge[:, :-1]            # +1 where a run starts, -1 one past its end
    row, c0 = np.nonzero(turn == 1)
    c1 = np.nonzero(turn == -1)[1]               # (the k-th end is the k-th start's: both row by row, left to right)
    n = len(row)
    if not n:
        return 0
    w = np.frombuffer(wet, dtype=np.uint8).reshape(ny, nx) != 0
    wets = np.concatenate([[0], np.cumsum((w & b).ravel(), dtype=_I)])
    run_wet = wets[row * nx + c1] > wets[row * nx + c0]
    # the runs of the next row that share a column with each run: from the first ending after its start to the last
    # starting before its end
    start, end = row * (nx + 1) + c0, row * (nx + 1) + c1
    first = np.searchsorted(end, (row + 1) * (nx + 1) + c0, side="right")
    after = np.searchsorted(start, (row + 1) * (nx + 1) + c1, side="left")
    many = np.maximum(after - first, 0)
    a = np.repeat(np.arange(n), many)
    other = np.arange(int(many.sum())) - np.repeat(np.cumsum(many) - many, many) + np.repeat(first, many)
    head = list(range(n))  # each run's stretch, named by one of its runs

    def find(k):
        while head[k] != k:
            head[k] = head[head[k]]
            k = head[k]
        return k
    for p, q in zip(a.tolist(), other.tolist()):
        p, q = find(p), find(q)
        if p != q:
            head[q] = p
    heads = np.array([find(k) for k in range(n)], dtype=_I)
    reaches = np.zeros(n, dtype=bool)
    reaches[heads[run_wet]] = True
    go = ~reaches[heads]
    if not go.any():
        return 0
    off = np.zeros((ny, nx + 1), dtype=np.int8)
    off[row[go], c0[go]] += 1                    # (a run's start and end are no other run's)
    off[row[go], c1[go]] -= 1
    gone = np.cumsum(off, axis=1, dtype=np.int8)[:, :nx] != 0
    left = np.frombuffer(bits, dtype=np.uint8).copy()
    left[gone.ravel()] = 0
    bits[:] = left.tobytes()
    return int((c1 - c0)[go].sum())


def near_bits(parts, x0: float, y0: float, nx: int, ny: int, cell: float, r: int) -> bytearray:
    """mend.Riverbeds._near_map's squares: each `cell` square holding the middle of a riverbed square of `parts`,
    widened by r."""
    rows = np.zeros((ny, nx), dtype=np.uint8)
    for part in parts:
        k = np.flatnonzero(np.frombuffer(part.bits, dtype=np.uint8))
        x, y = part.x0 + (k % part.nx + 0.5) * part.step, part.y0 + (k // part.nx + 0.5) * part.step
        rows[floor_div(y - y0, cell).astype(_I), floor_div(x - x0, cell).astype(_I)] = 1
    return bytearray(square(rows, r, True).tobytes())


def widened_rows(bits, nx: int, ny: int, r: int) -> list:
    """A grid of bits widened by r (mend._filter2, highest), as its rows."""
    out = square(np.frombuffer(bits, dtype=np.uint8).reshape(ny, nx), r, True)
    return [row.tobytes() for row in out]


# --- how each square is filled (mend.Plan) ---------------------------------------------------------------------------
def _nearest_bank(nx: int, ny: int, bad):
    """Plan's two passes: for each square, its nearest good square's column and row ((ny, nx) each, -1 for none) and
    the squared distance (inf for none). Walked square by square as there, in its order, over the bad squares only: a
    square takes its neighbours' answers as they come. (A rim of squares with no answer round the grid stands in for
    the loops' "is it on the grid".)"""
    wide = nx + 2
    none = 1 << 62
    good = np.zeros((ny + 2, wide), dtype=bool)
    good[1:-1, 1:-1] = ~bad
    sx, sy = np.full((ny + 2, wide), -1, dtype=_I), np.full((ny + 2, wide), -1, dtype=_I)
    jj, ii = np.nonzero(good)
    sx[jj, ii], sy[jj, ii] = ii - 1, jj - 1
    rim = np.zeros((ny + 2, wide), dtype=bool)
    rim[1:-1, 1:-1] = bad
    at = np.flatnonzero(rim.ravel())
    places = at.tolist()
    cells = list(zip(places, (at % wide - 1).tolist(), (at // wide - 1).tolist()))
    sx_all, sy_all, d2_all = sx.ravel(), sy.ravel(), np.where(good.ravel(), 0, none)
    sx, sy, d2 = sx_all.tolist(), sy_all.tolist(), d2_all.tolist()
    for order, (a, b, c, d) in ((cells, (-wide - 1, -wide, -wide + 1, -1)),
                                (reversed(cells), (wide + 1, wide, wide - 1, 1))):
        for k, i, j in order:
            best = least = d2[k]
            s = sx[k + a]
            if s >= 0:
                t = sy[k + a]
                e = (s - i) * (s - i) + (t - j) * (t - j)
                if e < best:
                    best, px, py = e, s, t
            s = sx[k + b]
            if s >= 0:
                t = sy[k + b]
                e = (s - i) * (s - i) + (t - j) * (t - j)
                if e < best:
                    best, px, py = e, s, t
            s = sx[k + c]
            if s >= 0:
                t = sy[k + c]
                e = (s - i) * (s - i) + (t - j) * (t - j)
                if e < best:
                    best, px, py = e, s, t
            s = sx[k + d]
            if s >= 0:
                t = sy[k + d]
                e = (s - i) * (s - i) + (t - j) * (t - j)
                if e < best:
                    best, px, py = e, s, t
            if best < least:
                d2[k], sx[k], sy[k] = best, px, py
    inner = (slice(1, -1), slice(1, -1))
    for whole, walked in ((sx_all, sx), (sy_all, sy), (d2_all, d2)):  # (only the bad squares' answers changed)
        whole[at] = np.fromiter(map(walked.__getitem__, places), dtype=_I, count=len(places))
    sx, sy, d2 = (v.reshape(ny + 2, wide)[inner] for v in (sx_all, sy_all, d2_all))
    return sx, sy, np.where(d2 == none, np.inf, d2.astype(np.float64))


def _hypot(a, b):
    """math.hypot for each pair: Python's own (numpy's differs in the last bit)."""
    return np.array(list(map(math.hypot, a.tolist(), b.tolist())), dtype=np.float64)


def _as_array(code: str, a) -> array:
    out = array(code)
    out.frombytes(np.ascontiguousarray(a).tobytes())
    return out


def plan(nx: int, ny: int, fill, bad, smooth: float):
    """mend.Plan's own sums on whole grids: (index, the way's x and y, the distance from the near bank, the width), as
    Plan keeps them. `fill` and `bad`: a byte for each square, row by row; None left to the loops."""
    if not all(isinstance(v, (bytes, bytearray)) and len(v) == nx * ny for v in (fill, bad)):
        return None
    bad2 = np.frombuffer(bad, dtype=np.uint8).reshape(ny, nx) != 0
    fill2 = np.frombuffer(fill, dtype=np.uint8).reshape(ny, nx) != 0
    sx, sy, d2 = _nearest_bank(nx, ny, bad2)
    sm = round(smooth)
    dist = blur(np.where(bad2 & (d2 < np.inf), np.sqrt(np.where(d2 < np.inf, d2, 0.0)), 0.0), sm) if sm > 0 else None
    j, i = np.nonzero(fill2 & bad2 & (sx >= 0))  # row by row: the loops' order
    px, py = i + 0.5, j + 0.5
    qx, qy = sx[j, i] + 0.5, sy[j, i] + 0.5
    d1 = _hypot(px - qx, py - qy)
    some = d1 != 0
    i, j, px, py, qx, qy, d1 = (v[some] for v in (i, j, px, py, qx, qy, d1))
    u, v = (px - qx) / d1, (py - qy) / d1
    if dist is not None:
        inner = np.flatnonzero((0 < i) & (i < nx - 1) & (0 < j) & (j < ny - 1))
        ji, ii = j[inner], i[inner]
        gx, gy = dist[ji, ii + 1] - dist[ji, ii - 1], dist[ji + 1, ii] - dist[ji - 1, ii]
        g = _hypot(gx, gy)
        turn = (g > 1e-9) & (gx * u[inner] + gy * v[inner] > 0)  # the smoothed way, unless it turns back
        g = np.where(turn, g, 1.0)
        u[inner] = np.where(turn, gx / g, u[inner])
        v[inner] = np.where(turn, gy / g, v[inner])
    width = np.full(len(d1), -1.0)
    left = np.arange(len(d1))
    for t in range(1, 2 * max(nx, ny)):  # on across to the far bank, every square still on its way a step at a time
        if not len(left):
            break
        a, b = np.floor(px[left] + u[left] * t), np.floor(py[left] + v[left] * t)
        on = (0 <= a) & (a < nx) & (0 <= b) & (b < ny)
        left, a, b = left[on], a[on].astype(_I), b[on].astype(_I)
        over = ~bad2[b, a]
        width[left[over]] = d1[left[over]] + t
        left = left[~over]
    index = np.full((ny, nx), -1, dtype=np.intc)
    index[j, i] = np.arange(len(d1))
    if sm > 0 and len(d1):  # the width, smoothed over the squares round that have one
        has = width > 0
        w_grid, c_grid = np.zeros((ny, nx)), np.zeros((ny, nx))
        w_grid[j[has], i[has]], c_grid[j[has], i[has]] = width[has], 1.0
        ws, cs = blur(w_grid, sm)[j, i], blur(c_grid, sm)[j, i]
        change = has & (cs > 0)
        mean, least = ws / np.where(change, cs, 1.0), d1 + 0.5
        width = np.where(change, np.where(least > mean, least, mean), width)
    return _as_array("i", index), _as_array("d", u), _as_array("d", v), _as_array("d", d1), _as_array("d", width)


# --- a picture's pixels through a Plan (mend.Plan.sources, fill_value; mend._mend_tile, mend_detail_parts) -----------
class _Leave(Exception):
    """Something here isn't worked out on whole grids: the loops' own."""


def _smooth(t):
    t = np.where(t < 1.0, t, 1.0)
    t = np.where(t > 0.0, t, 0.0)
    return t * t * (3 - 2 * t)


def _plan_arrays(p):
    return (np.frombuffer(p.index, dtype=np.intc).reshape(p.ny, p.nx), np.frombuffer(p.ux, dtype=np.float64),
            np.frombuffer(p.uy, dtype=np.float64), np.frombuffer(p.d1, dtype=np.float64),
            np.frombuffer(p.width, dtype=np.float64))


def _to_fill(p, index, i0: int, i1: int, j0: int, j1: int, ox: float, oy: float, pw: float, ph: float):
    """mend._to_fill on a whole grid: the pixels to fill as (column, row, x, y, the plan's square's number), row by
    row."""
    s = p.step
    i, j = np.arange(i0, max(i0, i1)), np.arange(j0, max(j0, j1))
    x, y = ox + (i + 0.5) * pw, oy + (j + 0.5) * ph
    g, gj = np.floor((x - p.x0) / s), np.floor((y - p.y0) / s)
    on, onj = (0 <= g) & (g < p.nx), (0 <= gj) & (gj < p.ny)
    i, x, g = i[on], x[on], g[on].astype(_I)
    j, y, gj = j[onj], y[onj], gj[onj].astype(_I)
    number = index[gj[:, None], g[None, :]]
    rows, cols = np.nonzero(number >= 0)
    return i[cols], j[rows], x[cols], y[rows], number[rows, cols]


def _sources(p, arrays, x, y, idx, ease: float, cross: float) -> list:
    """Plan.sources for many points to fill at once (`idx`: each one's square's number): its sources in the same
    order, each (weight, where it takes its ground x and y, its bank x and y, which points have it)."""
    _index, ux, uy, d1s, widths = arrays
    s = p.step
    gx, gy = (x - p.x0) / s, (y - p.y0) / s
    i, j = np.floor(gx), np.floor(gy)
    u, v, w = ux[idx], uy[idx], widths[idx]
    t = d1s[idx] + (gx - i - 0.5) * u + (gy - j - 0.5) * v
    d1 = np.where(t > 0.0, t, 0.0)       # this point's own distance from the bank
    bx, by = gx - u * d1, gy - v * d1    # the near bank, straight back along the way
    e = ease / s
    wide = w > 0

    def side(kx, ky, ox, oy, din):
        """One side's two sources for points `din` in from their bank: the mirror, then the ground moved across."""
        k = _smooth(din / e) if e > 0 else np.ones(len(din))
        part = k < 1.0
        return ((np.where(wide, 1.0 - k, 1.0), kx + ox * din, ky + oy * din, part),
                (np.where(part, k, 1.0), kx + ox * (w - din), ky + oy * (w - din), wide))
    (m_wt, m_x, m_y, part), (v_wt, v_x, v_y, _) = side(bx, by, -u, -v, d1)
    d2 = np.where(w - d1 > 0.0, w - d1, 0.0)
    fx, fy = gx + u * d2, gy + v * d2
    if cross > 0:
        w1 = _smooth(0.5 + (d2 - d1) / np.where(wide, 2 * cross * w, 1.0))
    else:
        w1 = (d1 <= d2).astype(np.float64)
    (n_wt, n_x, n_y, far_part), (o_wt, o_x, o_y, _) = side(fx, fy, u, v, d2)
    out = [(np.where(wide, m_wt * w1, m_wt), m_x, m_y, bx, by, ~wide | part),
           (v_wt * w1, v_x, v_y, bx, by, wide),
           (n_wt * (1 - w1), n_x, n_y, fx, fy, wide & far_part),
           (o_wt * (1 - w1), o_x, o_y, fx, fy, wide)]
    return [(wt, p.x0 + sx * s, p.y0 + sy * s, p.x0 + kx * s, p.y0 + ky * s, there & (wt > 1e-6))
            for wt, sx, sy, kx, ky, there in out]


def _hollow(old, bits, x, y):
    """mend.Gorge.holds for many points."""
    fi, fj = floor_div(x - old.x0, old.step), floor_div(y - old.y0, old.step)
    on = (0 <= fi) & (fi < old.nx) & (0 <= fj) & (fj < old.ny)
    out = np.zeros(len(x), dtype=bool)
    out[on] = bits[fj[on].astype(_I) * old.nx + fi[on].astype(_I)] != 0
    return out


def _fill_values(p, arrays, old, x, y, idx, sample, channels: int, ease: float, cross: float):
    """Plan.fill_value for many points to fill at once: (their values (n, channels), which have one). `old`: the
    hollows no ground is read from (a Gorge); `sample(x, y)` gives (the values there, one array for each channel;
    which of the points are on the picture)."""
    n = len(x)
    bits = np.frombuffer(old.bits, dtype=np.uint8)
    acc, total, have = [np.zeros(n) for _ in range(channels)], np.zeros(n), np.zeros(n, dtype=bool)
    for wt, sx, sy, kx, ky, there in _sources(p, arrays, x, y, idx, ease, cross):
        left = np.flatnonzero(there)
        sx, sy, kx, ky = sx[left], sy[left], kx[left], ky[left]
        for t in (1.0, 0.75, 0.5, 0.25, 0.0):  # a source landing in a hollow steps back toward its bank
            if not len(left):
                break
            px, py = kx + (sx - kx) * t, ky + (sy - ky) * t
            take = None if t == 0.0 else ~_hollow(old, bits, px, py)
            if take is not None and not take.any():
                continue
            if take is None or take.all():  # every one still looking takes its ground here
                rows, take = left, None
                values, on = sample(px, py)
            else:
                rows = left[take]
                values, on = sample(px[take], py[take])
            if not on.all():
                rows, values = rows[on], [v[on] for v in values]
            w = wt[rows]
            for c in range(channels):  # (a point is in `rows` once: its sum takes this source after the ones before)
                acc[c][rows] += w * values[c]
            total[rows] += w
            have[rows] = True
            if take is None:
                break
            keep = ~take
            left, sx, sy, kx, ky = left[keep], sx[keep], sy[keep], kx[keep], ky[keep]
    have &= total > 0
    out = np.zeros((n, channels), dtype=_I)
    for c in range(channels):
        out[have, c] = np.rint(acc[c][have] / total[have]).astype(_I)
    return out, have


_BLOCK = np.dtype([("c0", "<u2"), ("c1", "<u2"), ("word", "<u4")])
_U = np.uint32


def tile_pixels(blocks, nx: int, ny: int):
    """A tile's pixels (ny * 4, nx * 4, 3) from its DXT1 blocks: dxt.block_pixels for every block."""
    return tile_packed(blocks, nx, ny).view(np.uint8).reshape(ny * 4, nx * 4, 4)[..., :3]


def tile_packed(blocks, nx: int, ny: int):
    """A tile's pixels (ny * 4, nx * 4) from its DXT1 blocks, each one number: red, green << 8, blue << 16
    (dxt.block_pixels for every block). Each block's four colours are packed first, then every pixel looks its own
    up."""
    n = nx * ny
    raw = np.frombuffer(blocks, dtype=_BLOCK, count=n)
    c0, c1 = raw["c0"].astype(_U), raw["c1"].astype(_U)

    def rgb(c):
        r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
        return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)

    def packed(r, g, b):
        return r | (g << 8) | (b << 16)
    a, b = rgb(c0), rgb(c1)
    four = c0 > c1
    pal = np.empty((n, 4), dtype="<u4")
    pal[:, 0], pal[:, 1] = packed(*a), packed(*b)
    pal[:, 2] = packed(*(np.where(four, (2 * x + y + 1) // 3, (x + y) // 2) for x, y in zip(a, b)))
    pal[:, 3] = packed(*(np.where(four, (x + 2 * y + 1) // 3, 0) for x, y in zip(a, b)))
    which = (raw["word"][:, None] >> (2 * np.arange(16, dtype=_U))[None, :]) & 3  # [block, pixel]: which of the four
    which += (4 * np.arange(n, dtype=_U))[:, None]
    pix = pal.ravel()[which].reshape(ny, nx, 4, 4)  # [block row, block, row, column]
    return np.ascontiguousarray(pix.transpose(0, 2, 1, 3)).reshape(ny * 4, nx * 4)


def _unpacked(v, channels: int) -> list:
    """A packed picture's values as one array for each channel."""
    return [(v >> (8 * c)) & 255 for c in range(channels)]


class Pictures:
    """The map's own picture at each level of a tile set, for many points at once: groundpaint._picture_sampler's own
    sums. Decoded tiles are kept, up to KEEP bytes of them: the ones unused the longest go first."""
    KEEP = 80 << 20

    def __init__(self, store, bounds, cache=None):
        self.store, self.bounds, self.cache = store, bounds, cache
        self.kept: OrderedDict = OrderedDict()
        self.size = 0
        self.over = next((t for t in store.tiles if t.level == store.depth), None)

    def tile(self, level: int, key: tuple, read=None):
        """A tile's pixels (h, w), each one number (tile_packed), or None for none there. `read`: its (blocks, width,
        height), when the caller has read them already."""
        from .groundpaint import PaintError, _blocks
        name = (level,) + key
        if name in self.kept:
            self.kept.move_to_end(name)
            return self.kept[name]
        try:
            blocks, w, h = read or _blocks(self.store, self.over if level >= self.store.depth
                                           else self.store.tile(level, *key), self.cache)
        except (KeyError, PaintError):
            pic = None
        else:
            if w % 4 or h % 4:
                raise _Leave
            pic = tile_packed(bytes(blocks), w // 4, h // 4)
        self.kept[name] = pic
        self.size += 0 if pic is None else pic.nbytes
        while self.size > self.KEEP and len(self.kept) > 1:
            _name, gone = self.kept.popitem(last=False)
            self.size -= 0 if gone is None else gone.nbytes
        return pic

    def at(self, level: int, x, y):
        """(the colours at the map points: red, green and blue, an array each; which points are on the picture)."""
        from .groundpaint import _cells, _tile_rect
        store = self.store
        x0, y0 = self.bounds[0], self.bounds[1]
        values, on = np.zeros(len(x), dtype=_U), np.zeros(len(x), dtype=bool)
        if level >= store.depth:  # the whole-map overview tile
            if self.over is None:
                return _unpacked(values, 3), on
            groups = [((0, 0), np.arange(len(x)), _tile_rect(store, self.over, self.bounds))]
        else:
            cw, ch = _cells(store, self.bounds)
            side = 1 << (store.depth - 1 - level)
            tw, th = cw / side, ch / side
            kx, ky = floor_div(x - x0, tw), floor_div(y - y0, th)
            across, down = store.grid_w * side, store.grid_h * side
            there = np.flatnonzero((0 <= kx) & (kx < across) & (0 <= ky) & (ky < down))  # (no tile anywhere else)
            which = ky[there].astype(_I) * across + kx[there].astype(_I)
            groups = []
            tiles = np.flatnonzero(np.bincount(which, minlength=across * down)).tolist()
            for k in tiles:
                key = (k % across, k // across)
                rx0, ry0 = x0 + key[0] * tw, y0 + key[1] * th
                groups.append((key, there if len(tiles) == 1 else there[which == k], (rx0, ry0, rx0 + tw, ry0 + th)))
        for key, mine, (rx0, ry0, rx1, ry1) in groups:
            pic = self.tile(level, key)
            if pic is None:
                continue
            h, w = pic.shape
            px = np.trunc((x[mine] - rx0) / (rx1 - rx0) * w).astype(_I)
            py = np.trunc((y[mine] - ry0) / (ry1 - ry0) * h).astype(_I)
            inside = (0 <= px) & (px < w) & (0 <= py) & (py < h)
            if not inside.all():
                mine, px, py = mine[inside], px[inside], py[inside]
            values[mine] = pic.ravel()[py * w + px]
            on[mine] = True
        return _unpacked(values, 3), on


def _old_of(mend, hollow):
    """The Gorge a part's `hollow` reads (a Filled's own hollow); otherwise it is left to the loops."""
    filled = getattr(hollow, "__self__", None)
    if not isinstance(filled, mend.Filled) or getattr(hollow, "__func__", None) is not mend.Filled.hollow:
        raise _Leave
    return filled.old


def _pixel_range(box, rx0: float, ry0: float, pw: float, ph: float, w: int, h: int):
    return (max(0, math.floor((box[0] - rx0) / pw)), min(w, math.ceil((box[2] - rx0) / pw)),
            max(0, math.floor((box[1] - ry0) / ph)), min(h, math.ceil((box[3] - ry0) / ph)))


def mend_tile(mend, store, tile, bounds, mine: list, samplers: dict, source, cache, quick: bool):
    """One tile mended as mend._mend_tile mends it: its new record, b"" when nothing in it is mended, None when it is
    left to the loops. `mine`: the parts that touch it; `samplers`: the map's own pictures are kept there between
    tiles."""
    from .groundpaint import _blocks, _tile_rect
    from .tmst import zipo_tile
    try:
        olds = [_old_of(mend, hollow) for _plan, hollow, _box in mine]
        rx0, ry0, rx1, ry1 = _tile_rect(store, tile, bounds)
        blocks, w, h = _blocks(store, tile, cache)
        if w % 4 or h % 4:
            return None
        pw, ph = (rx1 - rx0) / w, (ry1 - ry0) / h
        pictures = samplers.get("whole grids")
        if pictures is None or pictures.store is not source:
            pictures = samplers["whole grids"] = Pictures(source, bounds, cache)
        level = tile.level
        img, touched = None, np.zeros((h // 4, w // 4), dtype=bool)
        for (p, _hollow_of, box), old in zip(mine, olds):
            arrays = _plan_arrays(p)
            i0, i1, j0, j1 = _pixel_range(box, rx0, ry0, pw, ph, w, h)
            i, j, x, y, idx = _to_fill(p, arrays[0], i0, i1, j0, j1, rx0, ry0, pw, ph)
            if not len(i):
                continue
            values, have = _fill_values(p, arrays, old, x, y, idx, lambda a, b: pictures.at(level, a, b), 3,
                                        mend.EASE, mend.CROSS)
            if not have.any():
                continue
            if img is None:  # the tile's own pixels, to change (the kept ones stay as the map has them)
                img = (pictures.tile(level, (tile.x, tile.y), (blocks, w, h)).copy() if source is store
                       else tile_packed(bytes(blocks), w // 4, h // 4))
            i, j = i[have], j[have]
            new = np.clip(values[have], 0, 255).astype(_U)
            img[j, i] = new[:, 0] | (new[:, 1] << 8) | (new[:, 2] << 16)
            touched[j // 4, i // 4] = True
    except _Leave:
        return None
    if img is None:
        return b""
    which = np.flatnonzero(touched.ravel())
    rows = img.reshape(h // 4, 4, w // 4, 4).transpose(0, 2, 1, 3).reshape(-1, 16)[which]  # a block's 16 pixels
    rows = np.ascontiguousarray(rows.view(np.uint8).reshape(-1, 16, 4)[:, :, :3]).reshape(-1, 48)
    made = dxtnp.encode_blocks_quick(rows) if quick else dxtnp.encode_blocks(rows)
    out = np.frombuffer(bytes(blocks), dtype=np.uint8).reshape(-1, 8).copy()
    out[which] = np.frombuffer(made, dtype=np.uint8).reshape(-1, 8)
    return zipo_tile(out.tobytes(), w, h)


# --- the close-up map (mend.mend_detail_parts): one DXT5 picture, all four channels ----------------------------------
def _alpha_tables(a0, a1):
    """dxt._alpha_table for many blocks: (n, 8)."""
    eight = [a0, a1] + [((7 - k) * a0 + k * a1 + 3) // 7 for k in range(1, 7)]
    six = [a0, a1] + [((5 - k) * a0 + k * a1 + 2) // 5 for k in range(1, 5)]
    six += [np.zeros_like(a0), np.full_like(a0, 255)]
    return np.where((a0 > a1)[:, None], np.stack(eight, axis=1), np.stack(six, axis=1))


def _dxt5_pixels(blocks: bytes, nx: int, ny: int):
    """A DXT5 picture's pixels (ny * 4, nx * 4, 4: red, green, blue, alpha): dxt.dxt5_block for every block."""
    raw = np.frombuffer(blocks, dtype=np.uint8).reshape(ny * nx, 16)
    table = _alpha_tables(raw[:, 0].astype(_I), raw[:, 1].astype(_I))
    bits = (raw[:, 2:8].astype(_I) << (8 * np.arange(6, dtype=_I))[None, :]).sum(axis=1)
    alpha = table[np.arange(ny * nx)[:, None], (bits[:, None] >> (3 * np.arange(16, dtype=_I))[None, :]) & 7]
    c0 = raw[:, 8].astype(_I) | (raw[:, 9].astype(_I) << 8)
    c1 = raw[:, 10].astype(_I) | (raw[:, 11].astype(_I) << 8)

    def rgb(c):
        r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
        return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], axis=1)
    a, b = rgb(c0), rgb(c1)
    pal = np.stack([a, b, (2 * a + b + 1) // 3, (a + 2 * b + 1) // 3], axis=1)  # (its colours always four)
    idx = (raw[:, 12].astype(_I) | (raw[:, 13].astype(_I) << 8) | (raw[:, 14].astype(_I) << 16)
           | (raw[:, 15].astype(_I) << 24))
    colour = pal[np.arange(ny * nx)[:, None], (idx[:, None] >> (2 * np.arange(16, dtype=_I))[None, :]) & 3]
    pix = np.concatenate([colour, alpha[:, :, None]], axis=2)  # (block, pixel, 4)
    return pix.reshape(ny, nx, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(ny * 4, nx * 4, 4).astype(np.uint8)


def _dxt5_blocks(rows) -> bytes:
    """dxt.encode_dxt5_block for each row ((n, 64): 16 pixels of red, green, blue, alpha): n x 16 bytes."""
    px = np.asarray(rows, dtype=np.uint8).reshape(-1, 16, 4)
    n = len(px)
    alpha = px[:, :, 3].astype(_I)
    a0, a1 = alpha.max(axis=1), alpha.min(axis=1)
    step = np.abs(_alpha_tables(a0, a1)[:, None, :] - alpha[:, :, None]).argmin(axis=2)  # (the first of equals)
    bits = (step.astype(_I) << (3 * np.arange(16, dtype=_I))[None, :]).sum(axis=1)
    out = np.zeros((n, 16), dtype=np.uint8)
    out[:, 0], out[:, 1] = a0, a1
    out[:, 2:8] = (bits[:, None] >> (8 * np.arange(6, dtype=_I))[None, :]) & 0xFF
    colours = dxtnp.encode_blocks(np.ascontiguousarray(px[:, :, :3]).reshape(n, 48))
    out[:, 8:] = np.frombuffer(colours, dtype=np.uint8).reshape(n, 8)
    return out.tobytes()


def mend_detail(mend, blocks: bytes, old: bytes, w: int, h: int, bounds, parts):
    """mend.mend_detail_parts's pixels on whole grids: (the picture's new blocks, how many were mended), or None left
    to the loops. `blocks`: the picture's DXT5 blocks, `old`: the ones the banks' values are read from."""
    if w % 4 or h % 4 or len(blocks) != w * h or len(old) != len(blocks):
        return None
    try:
        olds = [_old_of(mend, hollow) for _plan, hollow, _box in parts]
    except _Leave:
        return None
    x0, y0, x1, y1 = bounds
    pw, ph = (x1 - x0) / w, (y1 - y0) / h
    lends = _dxt5_pixels(old, w // 4, h // 4)
    packed = np.ascontiguousarray(lends).view("<u4").ravel()  # a pixel's four channels as one number

    def value(x, y):
        a, b = np.floor((x - x0) / pw), np.floor((y - y0) / ph)
        on = (0 <= a) & (a < w) & (0 <= b) & (b < h)
        out = np.zeros(len(x), dtype=_U)
        out[on] = packed[b[on].astype(_I) * w + a[on].astype(_I)]
        return _unpacked(out, 4), on
    img, touched = None, np.zeros((h // 4, w // 4), dtype=bool)
    for (p, _hollow_of, box), gorge in zip(parts, olds):
        arrays = _plan_arrays(p)
        i0, i1, j0, j1 = _pixel_range(box, x0, y0, pw, ph, w, h)
        i, j, x, y, idx = _to_fill(p, arrays[0], i0, i1, j0, j1, x0, y0, pw, ph)
        if not len(i):
            continue
        values, have = _fill_values(p, arrays, gorge, x, y, idx, value, 4, mend.EASE, mend.CROSS)
        if not have.any():
            continue
        if img is None:
            img = lends.copy() if old == blocks else _dxt5_pixels(blocks, w // 4, h // 4).copy()
        i, j = i[have], j[have]
        img[j, i] = np.clip(values[have], 0, 255)
        touched[j // 4, i // 4] = True
    if img is None:
        return blocks, 0
    which = np.flatnonzero(touched.ravel())
    rows = img.reshape(h // 4, 4, w // 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 64)[which]
    out = np.frombuffer(blocks, dtype=np.uint8).reshape(-1, 16).copy()
    out[which] = np.frombuffer(_dxt5_blocks(rows), dtype=np.uint8).reshape(-1, 16)
    return out.tobytes(), len(which)
