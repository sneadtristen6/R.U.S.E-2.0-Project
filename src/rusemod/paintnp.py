"""Map Paint on whole grids (numpy): groundpaint.paint_strokes's own tile records, byte for byte, many times sooner.
For colour strokes of any footprint and edge; a tile a stamp reaches is left to paint_strokes (paint_tile gives None).

What paint_strokes does, block for block (_in_turn does the same sums in the same order for a whole tile at once):
  - a stroke is laid on a pixel when its share there (its fall-off at the pixel's middle, or the mean of 3 x 3 points
    for a stroke under two pixels across, times its opacity) is over 0: value + (colour - value) * share, the strokes
    in their order;
  - a block a full-strength hard-edged stroke covers whole (groundpaint._solid_over) becomes that colour exactly,
    whatever was laid before, and is always written again;
  - at the end each value is rounded (halves to even) and kept in 0..255; a block is written again when one of its
    pixels differs from what the tile held (or it was covered whole), as dxt.encode_block packs it (rusemod.dxtnp,
    all the different blocks at once).

Strokes of one colour laid one after another (a whole map painted over: 135 of them on the owner's M04_Cotentin) leave
of what was there the product of what each leaves, 1 - share: colour + (value - colour) * product. _by_colour works
that out once for each run of one colour instead of laying every stroke on every channel. It is the same number as
laying them in turn to within a few million-millionths (see EDGE), so it rounds the same wherever it isn't that near
a rounding edge; the pixels that are (EDGE: far more than the two can differ by) are laid in turn,
as paint_strokes lays them. A tile the last run leaves under NEAR of anything at every pixel is that run's colour
all over, whatever it held."""
from __future__ import annotations

import math

from . import dxtnp
from .brush import HARD_EDGE
from .numpy2 import np

_I = np.int64
# How near a rounding edge (a value ending in .5) a pixel worked out by _by_colour is laid in turn instead. Each way
# strays from the true number by under 3 x 255 x 1.2e-16 for every stroke (each step's rounding, on values within
# 0..255; laying a stroke never widens what came before, a share being 0..1): under 2e-11 for 135 strokes, under
# 1e-7 for MOST; and _by_colour may take a tile a run has covered for that run's colour, COVERED off at most. So
# away from an edge by EDGE (four times all of that) both round the same way. About 6 pixels in 1,000 of a tile
# that is neither flat nor untouched are that near one: cheap to lay in turn.
EDGE = 1e-3
MOST = 1_000_000  # strokes reaching one tile, at most, for _by_colour (past it: in turn)
COVERED = 2.5e-4  # a run of one colour that leaves under this of anything (of 255) at every pixel of a tile has
                  # covered it: the tile is its colour to within this (_by_colour)
_FLAT: dict = {}  # (colour, width, height) -> the record of a tile that colour all over (packed once)


def pixels_of(blocks: bytes, nx: int, ny: int):
    """A tile's pixels (ny * 4, nx * 4, 3) from its DXT1 blocks: dxt.block_pixels for every block."""
    raw = np.frombuffer(blocks, dtype=np.uint8).reshape(ny * nx, 8)
    c0 = raw[:, 0].astype(_I) | (raw[:, 1].astype(_I) << 8)
    c1 = raw[:, 2].astype(_I) | (raw[:, 3].astype(_I) << 8)

    def rgb(c):
        r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
        return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], axis=1)
    a, b = rgb(c0), rgb(c1)
    four = (c0 > c1)[:, None]
    pal = np.stack([a, b, np.where(four, (2 * a + b + 1) // 3, (a + b) // 2), np.where(four, (a + 2 * b + 1) // 3, 0)],
                   axis=1)
    which = (raw[:, 4:8].astype(_I)[:, :, None] >> (2 * np.arange(4))[None, None, :]) & 3  # [block, row, column]
    pix = pal[np.arange(ny * nx)[:, None, None], which]
    return pix.reshape(ny, nx, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(ny * 4, nx * 4, 3).astype(np.uint8)


def _t2(f, xs, ys, grid: bool = True):
    """brush.Footprint.t2 at every (x of xs, y of ys): [row, column]; or, not `grid`, at each (xs[n], ys[n])."""
    ox, oy = ((xs - f.x)[None, :], (ys - f.y)[:, None]) if grid else (xs - f.x, ys - f.y)
    if f.shape == "square":
        n = math.sqrt(f.dx * f.dx + f.dy * f.dy) or 1.0
        u = np.abs(ox * f.dx + oy * f.dy) / n
        v = np.abs(oy * f.dx - ox * f.dy) / n
        m = np.where(u > v, u, v) / f.r
        return m * m
    if f.shape == "line":
        sx, sy = f.x2 - f.x, f.y2 - f.y
        len2 = sx * sx + sy * sy
        if len2 > 0.0:
            t = (ox * sx + oy * sy) / len2
            t = np.where(t < 0.0, 0.0, np.where(t > 1.0, 1.0, t))
        else:
            t = np.zeros(np.broadcast_shapes(ox.shape, oy.shape))
        qx, qy = ox - sx * t, oy - sy * t
        return (qx * qx + qy * qy) / (f.r * f.r)
    return (ox * ox + oy * oy) / (f.r * f.r)


def _strength(stroke, f, xs, ys, grid: bool = True):
    """brush.Stroke.strength_at for a paint stroke (the soft shape): its fall-off, 0 outside it."""
    t2 = _t2(f, xs, ys, grid)
    if stroke.edge != "hard":
        u = 1.0 - t2
        w = u * u
    else:
        t = np.sqrt(t2)
        s = (t - HARD_EDGE) / (1.0 - HARD_EDGE)
        w = np.where(t <= HARD_EDGE, 1.0, 1.0 - s * s * (3.0 - 2.0 * s))
    return np.where(t2 < 1.0, w, 0.0)


def _coverage(stroke, f, xs, ys, pw: float, ph: float, grid: bool = True):
    """groundpaint._coverage for every pixel middle (x of xs, y of ys); or, not `grid`, for each (xs[n], ys[n])."""
    if stroke.radius >= 2 * max(pw, ph):
        return _strength(stroke, f, xs, ys, grid)
    total = 0.0
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            total = total + _strength(stroke, f, xs + i * pw / 3, ys + j * ph / 3, grid)
    return total / 9


def _in_turn(gp, old, reach: list, strokes: list, boxes: list, colours: list, hard: list, px, py, cx0, cy0,
             pw: float, ph: float):
    """A tile's pixels after the strokes of `reach`, each laid in its turn on every pixel (paint_strokes's sums in
    its order), and the blocks a hard stroke covered whole (always written again). `old`: its pixels before; `px`,
    `py` the pixels' middles, `cx0`, `cy0` the blocks' corners."""
    ny, nx = len(cy0), len(cx0)
    img = old.astype(np.float64)
    force = np.zeros((ny, nx), dtype=bool)
    most = HARD_EDGE * HARD_EDGE
    # ends[p]: the one colour the strokes from reach[p] on all lay, each at most full strength and none able to cover
    # a block whole (None when they differ). Once every pixel is within NEAR of it, the rest only take each pixel
    # nearer (a share of the way, at most all of it), so it rounds to that colour as it would after all of them
    ends = [None] * (len(reach) + 1)
    for p in range(len(reach) - 1, -1, -1):
        k = reach[p]
        if not hard[k] and 0.0 <= strokes[k].weight <= 1.0 and (p == len(reach) - 1 or ends[p + 1] == colours[k]):
            ends[p] = colours[k]
    for p, k in enumerate(reach):
        if ends[p] is not None and p % 4 == 0 and p and all(
                bool((np.abs(img[:, :, ch] - ends[p][ch]) < gp.NEAR).all()) for ch in range(3)):
            break
        s, c = strokes[k], colours[k]
        f = s.footprint()
        bx0, bx1, by0, by1 = boxes[k]
        i0, i1 = int(np.searchsorted(px, bx0 - pw)), int(np.searchsorted(px, bx1 + pw, side="right"))
        j0, j1 = int(np.searchsorted(py, by0 - ph)), int(np.searchsorted(py, by1 + ph, side="right"))
        if hard[k]:  # whole blocks, for the ones it covers whole
            i0, i1, j0, j1 = i0 // 4 * 4, (i1 + 3) // 4 * 4, j0 // 4 * 4, (j1 + 3) // 4 * 4
        if i0 >= i1 or j0 >= j1:
            continue
        a = _coverage(s, f, px[i0:i1], py[j0:j1], pw, ph) * s.weight
        lay = a > 0.0
        sub = img[j0:j1, i0:i1]
        if hard[k]:
            x0, y0 = cx0[i0 // 4:i1 // 4], cy0[j0 // 4:j1 // 4]
            x1, y1 = x0 + 4 * pw, y0 + 4 * ph
            whole = ((_t2(f, x0, y0) <= most) & (_t2(f, x1, y0) <= most) & (_t2(f, x0, y1) <= most)
                     & (_t2(f, x1, y1) <= most))
            if whole.any():
                each = np.repeat(np.repeat(whole, 4, axis=0), 4, axis=1)
                sub[each] = c
                force[j0 // 4:j1 // 4, i0 // 4:i1 // 4] |= whole
                lay &= ~each
        if lay.any():
            for ch in range(3):
                v = sub[:, :, ch]
                np.copyto(v, v + (c[ch] - v) * a, where=lay)
    return np.clip(np.rint(img), 0, 255).astype(np.uint8), force


def _in_turn_at(old, xs, ys, reach: list, strokes: list, boxes: list, colours: list, pw: float, ph: float):
    """_in_turn's values, before rounding, for the pixels with middles (xs[n], ys[n]) alone (`old`: theirs before,
    [n, channel]); for strokes none of which covers a block whole. Every stroke is laid: stopping early, as _in_turn
    may, leaves a pixel within NEAR of the colour it would end nearer to, so it rounds the same."""
    v = old.astype(np.float64)
    for k in reach:
        s, c = strokes[k], colours[k]
        bx0, bx1, by0, by1 = boxes[k]
        a = _coverage(s, s.footprint(), xs, ys, pw, ph, grid=False) * s.weight
        lay = (a > 0.0) & (xs >= bx0 - pw) & (xs <= bx1 + pw) & (ys >= by0 - ph) & (ys <= by1 + ph)  # _in_turn's window
        if lay.any():
            for ch in range(3):
                np.copyto(v[:, ch], v[:, ch] + (c[ch] - v[:, ch]) * a, where=lay)
    return v


def _left(run: list, strokes: list, boxes: list, px, py, pw: float, ph: float, enough=None):
    """What the strokes of `run` (all one colour) leave of what was there, at each pixel: the product of 1 - share
    (1 where a stroke isn't laid: its share not over 0). With `enough`, None as soon as the most left anywhere is
    under it: the rest of the run can only leave less."""
    left = np.ones((len(py), len(px)))
    for k in run:
        s = strokes[k]
        bx0, bx1, by0, by1 = boxes[k]
        i0, i1 = int(np.searchsorted(px, bx0 - pw)), int(np.searchsorted(px, bx1 + pw, side="right"))
        j0, j1 = int(np.searchsorted(py, by0 - ph)), int(np.searchsorted(py, by1 + ph, side="right"))
        if i0 >= i1 or j0 >= j1:
            continue
        a = _coverage(s, s.footprint(), px[i0:i1], py[j0:j1], pw, ph) * s.weight
        left[j0:j1, i0:i1] *= np.where(a > 0.0, 1.0 - a, 1.0)
        if enough is not None and left.max() < enough:
            return None
    return left


def _by_colour(gp, old, reach: list, strokes: list, boxes: list, colours: list, px, py, pw: float, ph: float):
    """_in_turn's pixels for strokes of 0..1 opacity none of which covers a block whole, a run of one colour at a
    time (see the module's words); or the colour itself when the tile ends that colour all over.

    The runs are looked at from the last one back. One that leaves under COVERED of anything at every pixel has
    covered the tile: what the tile held and everything laid before that run no longer count (the tile is that run's
    colour to within COVERED, far under EDGE), so nothing before it is worked out. A map painted one colour all over
    and then touched up with another: only the touch-up is laid on its tiles. Within a run, the strokes reaching
    deepest over the tile are worked out first, so a run that covers the tile is known after a few of them (the
    product is the same whatever the order, to within what EDGE allows for)."""
    runs: list = []
    for k in reach:
        if runs and runs[-1][0] == colours[k]:
            runs[-1][1].append(k)
        else:
            runs.append((colours[k], [k]))
    x0, x1, y0, y1 = px[0], px[-1], py[0], py[-1]

    def deepest_first(run: list) -> list:
        if len(run) < 3:
            return run
        far = {}
        for k in run:
            t2 = strokes[k].footprint().t2
            far[k] = max(t2(x0, y0), t2(x1, y0), t2(x0, y1), t2(x1, y1))  # its farthest corner: the least it lays
        return sorted(run, key=lambda k: (far[k], k))
    # the last run first: what it leaves of a value (within 0..255 of its colour, whatever was laid before, those
    # being shares of 0..1 too) under NEAR everywhere brings every pixel within NEAR of its colour: it rounds to it
    colour, last = runs[-1]
    left = _left(deepest_first(last), strokes, boxes, px, py, pw, ph, enough=gp.NEAR / 255.0)
    if left is None:
        return colour
    after = [(colour, left)]  # the runs to lay, last first: (colour, what it leaves)
    planes = None
    for c, run in reversed(runs[:-1]):
        part = _left(deepest_first(run), strokes, boxes, px, py, pw, ph, enough=COVERED / 255.0)
        if part is None:  # it covered the tile: its colour, whatever was there
            planes = [np.full(left.shape, float(c[ch])) for ch in range(3)]
            break
        after.append((c, part))
    if planes is None:
        planes = [old[:, :, ch].astype(np.float64) for ch in range(3)]
    for c, part in reversed(after[1:]):
        for ch in range(3):
            planes[ch] = c[ch] + (planes[ch] - c[ch]) * part
    risky = np.zeros(left.shape, dtype=bool)
    for ch in range(3):
        v = planes[ch] = colour[ch] + (planes[ch] - colour[ch]) * left
        risky |= np.abs(v - np.floor(v) - 0.5) < EDGE
    new = np.empty(old.shape, dtype=np.uint8)
    for ch in range(3):
        new[:, :, ch] = np.clip(np.rint(planes[ch]), 0, 255)
    if risky.any():  # too near a rounding edge to trust: those pixels laid in turn
        jj, ii = np.nonzero(risky)
        new[jj, ii] = np.clip(np.rint(_in_turn_at(old[jj, ii], px[ii], py[jj], reach, strokes, boxes, colours, pw, ph)),
                              0, 255)
    return new


def paint_tile(gp, store, tile, rect, near: list, strokes: list, boxes: list, colours: list, hard: list, cache=None):
    """One tile painted as groundpaint.paint_strokes paints it: its new record, b"" when nothing changes, or None when
    a stroke near it isn't a colour laid with the soft shape (a stamp: paint_strokes's own pixels). `gp` is
    rusemod.groundpaint, `rect` the tile's place (_tile_rect), `near` the strokes whose boxes reach it; `boxes`,
    `colours` and `hard` as paint_strokes makes them."""
    for k in near:
        if colours[k] is None or strokes[k].kind.shape != "soft":
            return None
    rx0, ry0, rx1, ry1 = rect
    w, h = gp._dims(store, tile)
    pw, ph = (rx1 - rx0) / w, (ry1 - ry0) / h
    nx, ny = w // 4, h // 4
    # (two pixels' margin: no stroke a block's own one-pixel margin lets in is dropped)
    reach = [k for k in near if strokes[k].footprint().meets(rx0 - 2 * pw, ry0 - 2 * ph, rx1 + 2 * pw, ry1 + 2 * ph)]
    if not reach:
        return b""
    blocks = bytes(gp._blocks(store, tile, cache)[0])
    old = pixels_of(blocks, nx, ny)
    # each block's corner and each pixel's middle, by paint_strokes's own sums
    cx0, cy0 = rx0 + (np.arange(nx) * 4) * pw, ry0 + (np.arange(ny) * 4) * ph
    px = (cx0[:, None] + ((np.arange(4) + 0.5) * pw)[None, :]).ravel()
    py = (cy0[:, None] + ((np.arange(4) + 0.5) * ph)[None, :]).ravel()
    if len(reach) > MOST or any(hard[k] or not 0.0 <= strokes[k].weight <= 1.0 for k in reach):
        new, force = _in_turn(gp, old, reach, strokes, boxes, colours, hard, px, py, cx0, cy0, pw, ph)
    else:
        new, force = _by_colour(gp, old, reach, strokes, boxes, colours, px, py, pw, ph), False
        if isinstance(new, tuple):  # that colour all over
            if (old != np.array(new, dtype=np.uint8)).any(axis=2).reshape(ny, 4, nx, 4).any(axis=(1, 3)).all():
                key = (new, w, h)  # every block changes (none held exactly that colour already): one record
                if key not in _FLAT:
                    if len(_FLAT) >= 64:
                        _FLAT.clear()
                    block = dxtnp.encode_blocks(np.array([list(new) * 16], dtype=np.uint8))
                    _FLAT[key] = gp.zipo_tile(block * (nx * ny), w, h)
                return _FLAT[key]
            flat = np.empty(old.shape, dtype=np.uint8)
            flat[:] = new
            new = flat
    changed = (new != old).any(axis=2).reshape(ny, 4, nx, 4).any(axis=(1, 3)) | force
    if not changed.any():
        return b""
    which = np.flatnonzero(changed.ravel())
    rows = new.reshape(ny, 4, nx, 4, 3).transpose(0, 2, 1, 3, 4).reshape(ny * nx, 48)[which].tobytes()
    seen: dict = {}  # a block's 48 bytes -> its place among the different ones (a painted field is mostly one)
    back = [seen.setdefault(rows[at:at + 48], len(seen)) for at in range(0, len(rows), 48)]
    made = dxtnp.encode_blocks(np.frombuffer(b"".join(seen), dtype=np.uint8).reshape(len(seen), 48))
    out = np.frombuffer(blocks, dtype=np.uint8).reshape(ny * nx, 8).copy()
    out[which] = np.frombuffer(made, dtype=np.uint8).reshape(len(seen), 8)[np.array(back, dtype=_I)]
    return gp.zipo_tile(out.tobytes(), w, h)
