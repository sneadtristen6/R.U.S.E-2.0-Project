"""dxt.encode_block for many blocks at once (numpy): the same 8 bytes for every block, its sums done in its order
(the colour axis's sums pixel after pixel, the same eight passes, the same rounding).

Where two different pairs of end colours come out equally good, dxt.encode_block keeps the first it tried, in the
order its set of pairs gives them: that order is asked of the same set here, block by block (a few steps each). A
block whose colour axis shrank to nothing on the first try (it starts again from its farthest pixel there) is handed
to dxt.encode_block whole."""
from __future__ import annotations

from . import dxt
from .numpy2 import np

_I = np.int64
_S = np.int32
_NUDGES = [(da, db) for da in (-0x0821, 0, 0x0821) for db in (-0x0821, 0, 0x0821)]
_NUDGE_AT = {n: j for j, n in enumerate(_NUDGES)}
_SHIFTS = 2 * np.arange(16, dtype=_I)
CHUNK = 2048  # blocks worked on together (their tries: 9 pairs x 16 pixels x 4 colours each)


def _unpack565(c):
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)


def _pack565(r, g, b):
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)


def _to565(x, y, z):
    r, g, b = (np.clip(np.rint(v), 0, 255).astype(_I) for v in (x, y, z))
    return _pack565(r, g, b)


def _first_tried(a: int, b: int, good: list) -> int:
    """Of the pairs marked in `good` (by their place in _NUDGES), the one dxt.encode_block comes to first: its own set
    of pairs, made the same way, gone through in the set's order."""
    cands = {(a, b)}
    for da, db in _NUDGES:
        if 0 <= a + da <= 0xFFFF and 0 <= b + db <= 0xFFFF:
            cands.add((a + da, b + db))
    for x, y in cands:
        j = _NUDGE_AT[(x - a, y - b)]
        if good[j]:
            return j
    raise AssertionError("no pair of the set is marked")


def _some(px):
    """(c0, c1, word, left) for blocks that aren't one flat colour: px (n, 16, 3) int64. `left` marks the blocks to
    give to dxt.encode_block whole."""
    n = len(px)
    r, g, b = px[:, :, 0], px[:, :, 1], px[:, :, 2]
    mr, mg, mb = r.sum(axis=1) / 16, g.sum(axis=1) / 16, b.sum(axis=1) / 16
    c00 = c01 = c02 = c11 = c12 = c22 = 0
    for i in range(16):  # (added pixel after pixel, as there)
        dr, dg, db = r[:, i] - mr, g[:, i] - mg, b[:, i] - mb
        c00 = c00 + dr * dr
        c01 = c01 + dr * dg
        c02 = c02 + dr * db
        c11 = c11 + dg * dg
        c12 = c12 + dg * db
        c22 = c22 + db * db
    ax = ay = az = np.ones(n)
    for _ in range(8):
        ax, ay, az = (c00 * ax + c01 * ay + c02 * az, c01 * ax + c11 * ay + c12 * az, c02 * ax + c12 * ay + c22 * az)
        norm = np.maximum(np.maximum(np.abs(ax), np.abs(ay)), np.abs(az))
        norm = np.where(norm == 0.0, 1.0, norm)
        ax, ay, az = ax / norm, ay / norm, az / norm
    left = (ax == 0.0) & (ay == 0.0) & (az == 0.0)  # (it starts again from its farthest pixel: dxt's own)
    t = (r - mr[:, None]) * ax[:, None] + (g - mg[:, None]) * ay[:, None] + (b - mb[:, None]) * az[:, None]
    square = ax * ax + ay * ay + az * az
    square = np.where(square == 0.0, 1.0, square)
    hi, lo = t.max(axis=1) / square, t.min(axis=1) / square
    a = _to565(mr + hi * ax, mg + hi * ay, mb + hi * az)
    b0 = _to565(mr + lo * ax, mg + lo * ay, mb + lo * az)
    # the pairs tried: the two ends as they are, and each nudged a step either way
    ca = np.stack([a + da for da, _db in _NUDGES], axis=1)
    cb = np.stack([b0 + db for _da, db in _NUDGES], axis=1)
    tried = (ca >= 0) & (ca <= 0xFFFF) & (cb >= 0) & (cb <= 0xFFFF) & (ca != cb)
    c0, c1 = np.maximum(ca, cb), np.minimum(ca, cb)  # (n, 9)
    e = 0
    for ch, (p0, p1) in enumerate(zip(_unpack565(c0), _unpack565(c1))):  # a channel at a time: (n, 9, 16, 4)
        pal = np.stack([p0, p1, (2 * p0 + p1 + 1) // 3, (p0 + 2 * p1 + 1) // 3], axis=2).astype(_S)
        d = px[:, None, :, None, ch].astype(_S) - pal[:, :, None, :]
        e = e + d * d
    best = e.argmin(axis=3)  # (the first of equals, as there)
    err = e.min(axis=3).sum(axis=2, dtype=_I)  # (n, 9)
    word = (best.astype(_I) << _SHIFTS[None, None, :]).sum(axis=2)
    err = np.where(tried, err, np.iinfo(_I).max)
    least = err.min(axis=1)
    pick = err.argmin(axis=1)
    rows = np.arange(n)
    oc0, oc1, ow = c0[rows, pick], c1[rows, pick], word[rows, pick]
    # as good as the one picked but a different answer: the first tried wins, in the set's own order
    good = tried & (err == least[:, None])
    ties = (good & ((c0 != oc0[:, None]) | (c1 != oc1[:, None]) | (word != ow[:, None]))).any(axis=1) & ~left
    for i in np.flatnonzero(ties).tolist():
        j = _first_tried(int(a[i]), int(b0[i]), good[i].tolist())
        oc0[i], oc1[i], ow[i] = c0[i, j], c1[i, j], word[i, j]
    none = ~tried.any(axis=1)  # every pair fell to one colour: that colour, flat
    oc0, oc1, ow = np.where(none, a, oc0), np.where(none, a, oc1), np.where(none, 0, ow)
    return oc0, oc1, ow, left


def encode_blocks(rows) -> bytes:
    """dxt.encode_block for each row of `rows` ((n, 48) uint8: 16 RGB pixels, row-major): n x 8 bytes."""
    n = len(rows)
    px = np.asarray(rows, dtype=np.uint8).reshape(n, 16, 3).astype(_I)
    out = np.zeros(n, dtype=[("c0", "<u2"), ("c1", "<u2"), ("word", "<u4")])
    flat = (px == px[:, :1, :]).all(axis=(1, 2))
    c = _pack565(px[:, 0, 0], px[:, 0, 1], px[:, 0, 2])
    out["c0"], out["c1"] = np.where(flat, c, 0), np.where(flat, c, 0)
    todo = np.flatnonzero(~flat)
    own = []
    for at in range(0, len(todo), CHUNK):
        part = todo[at:at + CHUNK]
        c0, c1, word, left = _some(px[part])
        out["c0"][part], out["c1"][part], out["word"][part] = c0, c1, word
        own += part[left].tolist()
    raw = bytearray(out.tobytes())
    for i in own:
        raw[8 * i:8 * i + 8] = dxt.encode_block([tuple(p) for p in px[i].tolist()])
    return bytes(raw)
