"""rusemod.nav's grid of spots (nav._Spots) on whole grids, with numpy (rusemod.numpy2): each zone's spots worked out
for its whole square at once instead of point by point. The same rooms and the same `top` as the loops in nav.py,
which are what this is checked against (tests/test_nav_whole.py) and what runs without numpy.

The same sums: a spot's depth in a zone is r - sqrt(dx² + dy²). numpy's square root is the exact one; the plain
code's `** 0.5` is the C library's power, which now and then (about one sum in two thousand) ends one bit away, though
never on a whole-number distance (checked on every perfect square up to 3,000,000², 2026-10-05). A room is a whole
number of STEPs, so a bit matters only where a depth lies on a STEP or on `least`: those few spots, the whole-number
distances apart, are worked out again the plain code's way, so every room is the plain code's."""
from __future__ import annotations

from .numpy2 import np

NEAR_EDGE = 1e-6  # a depth this near a STEP or `least` is worked out again as the plain code does it


def _levels(sx: float, sy: float, sr: float, ia: int, ib: int, ja: int, jb: int, step: float, unit: float,
            least: float):
    """The rooms (whole units of `unit`, 0 for no spot) of the grid points (i, j), ia <= i <= ib, ja <= j <= jb, in
    the zone (sx, sy, sr): as the plain code works them out."""
    xs = np.arange(ia, ib + 1, dtype=np.float64) * step
    ys = np.arange(ja, jb + 1, dtype=np.float64) * step
    dx, dy = xs - sx, ys - sy
    d2 = (dx * dx)[:, None] + (dy * dy)[None, :]
    root = np.sqrt(d2)
    deep = sr - root
    lv = np.floor_divide(deep, unit)
    edge = (np.abs(deep - least) < NEAR_EDGE) | (np.abs(deep - np.round(deep / unit) * unit) < NEAR_EDGE)
    # (a whole-number distance is exact both ways, the C library's power included: every spot in line with a middle
    # on the grid is one, so these are never worked out again)
    edge &= ~((root == np.floor(root)) & (root * root == d2))
    if edge.any():
        for a, b in zip(*np.nonzero(edge)):
            d = sr - (((ia + int(a)) * step - sx) ** 2 + ((ja + int(b)) * step - sy) ** 2) ** 0.5
            deep[a, b] = d
            lv[a, b] = d // unit
    ok = (deep >= least) & (lv * unit >= least)
    return np.where(ok, lv, 0.0)


def spot_rooms(zones, least: float, i0: int, j0: int, ni: int, nj: int, step: float, unit: float,
               dtype) -> tuple[bytes, int]:
    """nav._Spots' rooms (row by row, ni rows of nj, as bytes of `dtype`) and its `top`, for `zones` (those with r >=
    least, in their order) on the grid whose first point is (i0, j0)."""
    i1, j1 = i0 + ni - 1, j0 + nj - 1
    room = np.zeros((ni, nj), dtype=np.int64)
    kinds: dict = {}  # (r, x % step, y % step) -> how many spots one such zone has, its most room (as nav._Spots)
    spare = 400000
    top = 0
    for sx, sy, sr in zones:
        kind = None
        if sr <= 64 * step and sx % 1 == 0 and sy % 1 == 0 and abs(sx) < 2.0 ** 40 and abs(sy) < 2.0 ** 40:
            ox, oy = sx % step, sy % step
            kind = kinds.get((sr, ox, oy))
            if kind is None and (2 * sr / step + 2) ** 2 <= spare:
                # nav._Spots lists such a zone's spots once, all of them, wherever the grid ends: its `top` takes
                # their most room and its spare the count, whether or not they lie on the grid
                lv = _levels(ox, oy, sr, int((ox - sr) // step), int((ox + sr) // step), int((oy - sr) // step),
                             int((oy + sr) // step), step, unit, least)
                count = int(np.count_nonzero(lv))
                kind = kinds[sr, ox, oy] = (count, int(lv.max()) if count else 0)
                top = max(top, kind[1])
                spare -= count
            if kind is not None and not kind[0]:
                continue
        ia, ib = max(i0, int((sx - sr) // step)), min(i1, int((sx + sr) // step))
        ja, jb = max(j0, int((sy - sr) // step)), min(j1, int((sy + sr) // step))
        if ia > ib or ja > jb:
            continue
        lv = _levels(sx, sy, sr, ia, ib, ja, jb, step, unit, least).astype(np.int64)
        part = room[ia - i0:ib - i0 + 1, ja - j0:jb - j0 + 1]
        np.maximum(part, lv, out=part)
        if kind is None and lv.size:
            top = max(top, int(lv.max()))
    return room.astype(dtype).tobytes(), top
