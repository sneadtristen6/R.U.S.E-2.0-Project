"""Map Paint on whole grids (numpy): groundpaint.paint_strokes's own sums, in its order, for all of a tile's pixels at
once instead of one pixel at a time, so a tile comes out the same bytes many times sooner. For colour strokes of any
footprint and edge; a tile a stamp reaches is left to paint_strokes (paint_tile gives None).

How it follows paint_strokes, block for block:
  - a stroke is laid on a pixel when its share there (its fall-off at the pixel's middle, or the mean of 3 x 3 points
    for a stroke under two pixels across, times its opacity) is over 0: value + (colour - value) * share, the strokes
    in their order;
  - a block a full-strength hard-edged stroke covers whole (groundpaint._solid_over) becomes that colour exactly,
    whatever was laid before, and is always written again;
  - at the end each value is rounded (halves to even) and kept in 0..255; a block is written again when one of its
    pixels differs from what the tile held (or it was covered whole), as dxt.encode_block packs it (rusemod.dxtnp,
    all the different blocks at once)."""
from __future__ import annotations

import math

import numpy as np

from . import dxtnp
from .brush import HARD_EDGE

_I = np.int64


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


def _t2(f, xs, ys):
    """brush.Footprint.t2 at every (x of xs, y of ys): [row, column]."""
    ox, oy = (xs - f.x)[None, :], (ys - f.y)[:, None]
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


def _strength(stroke, f, xs, ys):
    """brush.Stroke.strength_at for a paint stroke (the soft shape): its fall-off, 0 outside it."""
    t2 = _t2(f, xs, ys)
    if stroke.edge != "hard":
        u = 1.0 - t2
        w = u * u
    else:
        t = np.sqrt(t2)
        s = (t - HARD_EDGE) / (1.0 - HARD_EDGE)
        w = np.where(t <= HARD_EDGE, 1.0, 1.0 - s * s * (3.0 - 2.0 * s))
    return np.where(t2 < 1.0, w, 0.0)


def _coverage(stroke, f, xs, ys, pw: float, ph: float):
    """groundpaint._coverage for every pixel middle (x of xs, y of ys)."""
    if stroke.radius >= 2 * max(pw, ph):
        return _strength(stroke, f, xs, ys)
    total = 0.0
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            total = total + _strength(stroke, f, xs + i * pw / 3, ys + j * ph / 3)
    return total / 9


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
    img = old.astype(np.float64)
    # each block's corner and each pixel's middle, by paint_strokes's own sums
    cx0, cy0 = rx0 + (np.arange(nx) * 4) * pw, ry0 + (np.arange(ny) * 4) * ph
    px = (cx0[:, None] + ((np.arange(4) + 0.5) * pw)[None, :]).ravel()
    py = (cy0[:, None] + ((np.arange(4) + 0.5) * ph)[None, :]).ravel()
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
    new = np.clip(np.rint(img), 0, 255).astype(np.uint8)
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
