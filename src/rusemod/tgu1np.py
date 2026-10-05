"""TGU1 payload -> DXT1 blocks on whole arrays (numpy): rusemod.tgu1.decode's own integer and float32 sums, done for
every block of a tile at once instead of one value at a time (a 512-pixel tile: about a second there). For the tiles
a map's ground is made of: DXT1, coded, no endpoint-order list, no raw selector words. `decode` gives None for
anything else, or anything it finds wrong: the caller then uses rusemod.tgu1's own decoder (and its errors).

Only the bit streams are still walked value by value, and only to find where each value starts: a stream's values
follow one another, each as long as its own bits say."""
from __future__ import annotations

import struct
import zlib

from . import tgu1
from .numpy2 import np

_I = np.int64
_QUANT = np.array(tgu1.QUANT, dtype=_I)
_ZIGZAG = tgu1.ZIGZAG
_ORDER = np.array(tgu1.SELECTOR_ORDER, dtype=_I)
_MOST_BITS = 40  # a value's own bits: more is no ground tile's (and wouldn't fit the sums here)


def _s16(x):
    return ((x + 0x8000) & 0xFFFF) - 0x8000


def _s32(x):
    return ((x + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def _sat16(x):
    return np.clip(x, -32768, 32767)


def _stream(mode: int, data: bytes, nbits: int, want: int):
    """The `want` values of one sub-band (tgu1._Reader.value, `want` times), or None unless they use it up exactly."""
    if want == 0:
        return np.zeros(0, dtype=_I) if nbits == 0 else None
    if nbits > len(data) * 8:
        return None
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")[:nbits]
    ones = np.flatnonzero(bits)
    if not len(ones):
        return None
    at = np.arange(nbits)
    k_of = np.searchsorted(ones, at)
    term = np.where(k_of < len(ones), ones[np.minimum(k_of, len(ones) - 1)], nbits)  # the first 1 at or after each bit
    if mode >= 8:   # Rice: zeros, a 1, then k bits
        nxt = term + 1 + (mode - 8)
    else:           # Exp-Golomb: q zeros, a 1, then mode + q bits
        nxt = 2 * term - at + 1 + mode
    nxt = nxt.tolist()
    starts, pos = [], 0
    for _ in range(want):  # where each value starts: the one walk left
        if pos >= nbits:
            return None
        starts.append(pos)
        pos = nxt[pos]
    if pos != nbits:
        return None
    s = np.array(starts, dtype=_I)
    t = term[s].astype(_I)
    q = t - s

    def own_bits(first, k):  # the k bits after each 1, the first the lowest
        if not k:
            return 0
        return (bits[first[:, None] + np.arange(k)[None, :]].astype(_I) << np.arange(k, dtype=_I)).sum(axis=1)
    if mode >= 8:
        k = mode - 8  # (at most 7; q, a count of zeros, is under the stream's length)
        u = (q << k) | own_bits(t + 1, k)
    else:
        if mode + int(q.max()) > _MOST_BITS:
            return None
        u = np.empty(len(s), dtype=_I)
        for qv in np.unique(q).tolist():
            pick = q == qv
            k = mode + qv
            u[pick] = (1 << k) + own_bits(t[pick] + 1, k) - (1 << mode)
    return (u >> 1) ^ -(u & 1)


def _bank(body: bytes, pos: int, has_raw: bool, n_blocks: int, dc_predict: bool):
    """(coefficients (n_blocks, 16) row-major, how many each block had, where the bank ends), as tgu1._Bank.block gives
    them block after block; None for a bank with raw words or anything out of the ordinary."""
    if pos + 68 + 4 * has_raw > len(body):
        return None
    if has_raw:
        if struct.unpack_from("<I", body, pos)[0]:
            return None
        pos += 4
    descs = struct.unpack_from("<17I", body, pos)
    pos += 68
    streams = []
    for d in descs:
        nbits = d & 0x0FFFFFFF
        nbytes = (nbits + 31) // 32 * 4
        if pos + nbytes > len(body):
            return None
        streams.append((d >> 28, body[pos:pos + nbytes], nbits))
        pos += nbytes
    steps = _stream(*streams[0], n_blocks)
    if steps is None:
        return None
    counts = np.cumsum(steps)
    if n_blocks and int(counts.max()) > 16:
        return None
    coefs = np.zeros((n_blocks, 16), dtype=_I)
    for j in range(16):
        has = counts > j
        vals = _stream(*streams[j + 1], int(has.sum()))
        if vals is None:
            return None
        coefs[has, _ZIGZAG[j]] = vals
    if n_blocks and int(np.abs(coefs).max()) >= 1 << 31:
        return None
    if dc_predict:
        coefs[:, 0] = np.cumsum(coefs[:, 0])
        if n_blocks and int(np.abs(coefs[:, 0]).max()) >= 1 << 31:
            return None
    return coefs, counts, pos


def _rows(d, shift_round):
    """tgu1._rows (saturating): (n, 16) -> t[n, k, c]."""
    d = d.reshape(-1, 4, 4)
    d0, d1, d2, d3 = d[:, :, 0], d[:, :, 1], d[:, :, 2], d[:, :, 3]
    e0, e1 = 20 * (d0 + d2), 20 * (d0 - d2)
    o0, o1 = 26 * d1 + 11 * d3, 11 * d1 - 26 * d3
    return _sat16(np.stack([shift_round(e0 + o0), shift_round(e1 + o1), shift_round(e1 - o1), shift_round(e0 - o0)],
                           axis=2))


def _cols(t, add: int, shift: int):
    """tgu1._cols: t[n, k, c] -> out[n, r, c]."""
    a, b, c, d = t[:, 0, :], t[:, 1, :], t[:, 2, :], t[:, 3, :]
    e0, e1 = 20 * (a + c), 20 * (a - c)
    o0, o1 = 26 * b + 11 * d, 11 * b - 26 * d
    return np.stack([(e0 + o0 + add) >> shift, (e1 + o1 + add) >> shift, (e1 - o1 + add) >> shift,
                     (e0 - o0 + add) >> shift], axis=1)


def _f32(a):
    return a.astype(np.float32).astype(np.float64)


def _to_565(y, cb, cr):
    """tgu1.ycbcr_to_565 for arrays: each step rounded to float32 as there, halves to even."""
    yf = _f32((y - 16.0) * tgu1._KY)
    fcb, fcr = (cb - 128).astype(np.float64), (cr - 128).astype(np.float64)
    r = _f32(_f32(tgu1._KCR_R * fcr) + yf)
    g = _f32(_f32(yf - _f32(fcb * tgu1._KCB_G)) - _f32(fcr * tgu1._KCR_G))
    b = _f32(_f32(fcb * tgu1._KCB_B) + yf)
    r, g, b = (np.clip(np.rint(v), 0, 255).astype(_I) for v in (r, g, b))
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def decode(payload: bytes) -> bytes | None:
    """A ground tile's DXT1 blocks, the same bytes as tgu1.decode; None when this isn't such a payload."""
    try:
        head = tgu1.Header.parse(payload)
        if head.version != tgu1.VERSION or head.flags != tgu1.FLAG_CODED:
            return None
        w, h, count = head.width, head.height, head.block_count
        if w % 4 or h % 4 or not w or not h or count > w * h:
            return None
        body = zlib.decompressobj().decompress(bytes(payload[tgu1.HEADER.size:]))
        if len(body) != head.body_size or len(body) < 4 or struct.unpack_from("<I", body, 0)[0]:
            return None  # (an endpoint-order list: tgu1's own)
        pos = 4
        tables = tgu1.color_tables(head.color_quality)
        n_tiles = (w // 4) * (h // 4)
        planes = []
        for p in range(6):
            got = _bank(body, pos, False, n_tiles, True)
            if got is None:
                return None
            coefs, _counts, pos = got
            hi = np.array([t[0] for t in tables[p % 3]], dtype=_I)
            lo = np.array([t[1] for t in tables[p % 3]], dtype=_I)
            c = _sat16(coefs)
            d = _s16(hi * c + ((lo * c) >> 16))
            out = _cols(_rows(d, lambda s: (s + 16) >> 5), 512, 10)  # out[tile, r, c] is sample (row c, column r)
            planes.append(out.transpose(0, 2, 1).reshape(h // 4, w // 4, 4, 4).transpose(0, 2, 1, 3).reshape(h * w))
        got = _bank(body, pos, True, count, False)
        if got is None:
            return None
        coefs, counts, pos = got
        if pos != len(body):
            return None
        c0, c1 = _to_565(*planes[:3]), _to_565(*planes[3:])
        # tgu1.fix_order with no list: every block four-colour (c0 > c1)
        low, same, even = c0 < c1, c0 == c1, (c0 & 1) == 0
        e0 = np.where(low, c1, np.where(same & even, c0 | 1, c0))
        e1 = np.where(low, c0, np.where(same, np.where(even, c0, c0 - 1), c1))
        scale = head.selector_quality
        flat = _s32(_s32(_s32(coefs[:, 0] * scale) * tgu1.QUANT[0]) * 400 + 0x80000) >> 20
        d = _s16(_s16(_sat16(coefs) * tgu1._s16(scale)) * _QUANT)
        full = _cols(_rows(d, lambda v: v >> 9), 1024, 11).reshape(count, 16)
        values = np.where((counts < 2)[:, None], flat[:, None], full)
        place = np.clip(_s16(_sat16(values) + 2), 0, 3)
        words = (_ORDER[place] << (2 * np.arange(16, dtype=_I))).sum(axis=1)
        out = np.zeros(w * h, dtype=[("c0", "<u2"), ("c1", "<u2"), ("word", "<u4")])
        out["c0"][:count], out["c1"][:count], out["word"][:count] = e0[:count], e1[:count], words
        return out.tobytes()
    except (ValueError, struct.error, zlib.error, IndexError, OverflowError):
        return None
