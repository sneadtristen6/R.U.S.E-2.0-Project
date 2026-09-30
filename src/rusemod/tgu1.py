"""TGU1: the game's own compressed-DXT1 texture payload (terrain tiles, some .tgv mips). Read and write.

A TGU1 payload replaces the raw DXT1 bytes of a TGV mip. It is a 36-byte header and a zlib stream (flushed
with a sync flush, no final block). The inflated body describes the DXT1 surface in three parts:

* endpoint colours: every 4x4-pixel block has two RGB565 endpoints, stored as six small images (Y, Cb, Cr of
  endpoint 0, then of endpoint 1) with one sample per DXT1 block. Each image is cut into 4x4 tiles, each tile
  is a 4x4 integer DCT, and the DC is predicted from the previous tile of the same image;
* palette indices (selectors): a full-resolution image (one sample per pixel), DCT-coded per DXT1 block; the
  decoded value v maps to palette position clamp(v + 2, 0, 3), i.e. the index order 0, 2, 3, 1;
* optional raw selector words and an endpoint-order list (both empty in every shipped terrain tile).

Coefficients are stored "sub-band major": a bank holds 17 bit streams, stream 0 the per-block coefficient
counts (delta-coded), stream j the j-th coefficient (zigzag order) of every block that has at least j.
Each stream uses Rice or Exp-Golomb coding with a per-stream parameter, bits LSB-first in u32 words.

`decode` turns a payload into plain DXT1 blocks; decoded tiles match each map's own overview picture
(`output\\terrain.png`), and the Studio's map view draws the ground with them. `encode` is experimental (lossy, and
a second pass isn't guaranteed to give the same blocks); writing terrain doesn't need it, since the game accepts
plain ZIPO tiles (FORMATS.md §6). See docs/FORMATS.md for the byte layout.
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

MAGIC = b"TGU1"
HEADER = struct.Struct("<4s8I")          # magic, version, width, height, color q, selector q, blocks, flags, body size
VERSION = 5
FLAG_CODED = 0x100                       # set in every TGU1 payload the game ships
FLAG_ALPHA = 0x001                       # DXT5-style alpha banks follow (not supported here)

QUANT = (18, 14, 18, 49, 12, 16, 37, 78, 24, 57, 104, 121, 51, 69, 103, 100)   # row-major 4x4
ZIGZAG = (0, 1, 4, 8, 5, 2, 3, 6, 9, 12, 13, 10, 7, 11, 14, 15)                # j-th coefficient -> position
BASIS = ((20, 20, 20, 20), (26, 11, -11, -26), (20, -20, -20, 20), (11, -26, 26, -11))
SELECTOR_ORDER = (0, 2, 3, 1)            # palette position (c0 .. c1) -> DXT1 index
POSITION_OF_INDEX = (0, 3, 1, 2)

_F32 = struct.Struct("<f")


def _f32(x: float) -> float:
    return _F32.unpack(_F32.pack(x))[0]


def _hexf(h: str) -> float:
    return _F32.unpack(bytes.fromhex(h))[0]


# The format's YCbCr -> RGB constants, as float32.
_KY, _KCB_G, _KCB_B, _KCR_R, _KCR_G = (_hexf(h) for h in ("7f0a953f", "fe94c83e", "5e1a0140", "a0cacc3f", "b81e503f"))


def color_scale(quality: int) -> int:
    """Endpoint dequantisation factor (16.16 fixed point) for a header colour quality."""
    return int(float(quality) * 0.9712914007 * 2048.0)


def _s16(x: int) -> int:
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def _s32(x: int) -> int:
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x & 0x80000000 else x


def _sat16(x: int) -> int:
    return -32768 if x < -32768 else 32767 if x > 32767 else x


@dataclass
class Header:
    version: int = VERSION
    width: int = 128              # in 4x4 blocks
    height: int = 128
    color_quality: int = 80       # endpoint dequantisation: Q * color_scale(q), doubled for Cb/Cr
    selector_quality: int = 40    # selector dequantisation: Q * q
    block_count: int = 128 * 128
    flags: int = FLAG_CODED
    body_size: int = 0

    @classmethod
    def parse(cls, payload: bytes) -> "Header":
        if len(payload) < HEADER.size or payload[:4] != MAGIC:
            raise ValueError(f"not a TGU1 payload: {bytes(payload[:4])!r}")
        return cls(*HEADER.unpack_from(payload, 0)[1:])

    def pack(self) -> bytes:
        return HEADER.pack(MAGIC, self.version, self.width, self.height, self.color_quality,
                           self.selector_quality, self.block_count, self.flags, self.body_size)


# ---------------------------------------------------------------------------------------------------------
# Bit streams

class _Reader:
    """One sub-band: values coded with Rice (mode >= 8, k = mode - 8) or Exp-Golomb (mode < 8, k = mode)."""

    def __init__(self, mode: int, data: bytes, nbits: int):
        self.mode, self.nbits, self.pos = mode, nbits, 0
        n = len(data) * 8
        self.bits = format(int.from_bytes(data, "little"), "0%db" % n)[::-1] if n else ""

    def value(self) -> int:
        bits, pos = self.bits, self.pos
        one = bits.find("1", pos)
        if one < 0:
            raise ValueError("TGU1 sub-band ran out of data")
        q = one - pos
        pos = one + 1
        if self.mode >= 8:
            k = self.mode - 8
            u = (q << k) | (int(bits[pos:pos + k][::-1], 2) if k else 0)
        else:
            k = self.mode + q
            u = (1 << k) + (int(bits[pos:pos + k][::-1], 2) if k else 0) - (1 << self.mode)
        self.pos = pos + k
        if self.pos > self.nbits:
            raise ValueError("TGU1 sub-band ran out of data")
        return (u >> 1) ^ -(u & 1)


class _Bank:
    """17 sub-band readers plus the per-image running state (coefficient count, DC predictor)."""

    def __init__(self, body: bytes, pos: int, has_raw: bool, dc_predict: bool):
        n_raw = 0
        if has_raw:
            n_raw = struct.unpack_from("<I", body, pos)[0]
            pos += 4
        descs = struct.unpack_from("<17I", body, pos)
        pos += 68
        self.raw = list(struct.unpack_from("<%dI" % n_raw, body, pos))
        pos += 4 * n_raw
        self.readers = []
        for d in descs:
            nbits = d & 0x0FFFFFFF
            nbytes = (nbits + 31) // 32 * 4
            if pos + nbytes > len(body):
                raise ValueError("TGU1 bank runs past the end of the body")
            self.readers.append(_Reader(d >> 28, body[pos:pos + nbytes], nbits))
            pos += nbytes
        self.end = pos
        self.count = 0
        self.dc = 0
        self.dc_predict = dc_predict
        self.coded: list[tuple[int, list[int]]] = []   # per block: (count, coefficients as stored)

    def block(self) -> tuple[list[int], bool]:
        """Next block's 16 coefficients (row-major) and whether it is DC-only (fewer than 2 coded)."""
        r = self.readers
        self.count += r[0].value()
        n = self.count
        if n > 16:
            raise ValueError(f"TGU1 block claims {n} coefficients")
        coefs = [0] * 16
        for j in range(n):
            coefs[ZIGZAG[j]] = r[j + 1].value()
        self.coded.append((n, coefs[:]))
        if self.dc_predict:
            coefs[0] += self.dc
            self.dc = coefs[0]
        return coefs, n < 2

    def check_consumed(self) -> None:
        for j, r in enumerate(self.readers):
            if r.pos != r.nbits:
                raise ValueError(f"TGU1 sub-band {j}: {r.nbits - r.pos} bits left over")


# ---------------------------------------------------------------------------------------------------------
# Integer inverse transforms (exact integer arithmetic)

def _rows(d: list[int], shift_round, sat: bool) -> list[list[int]]:
    """First pass: t[k][c] = f(sum_u d[k][u] * BASIS[u][c])."""
    t = []
    for k in range(0, 16, 4):
        d0, d1, d2, d3 = d[k], d[k + 1], d[k + 2], d[k + 3]
        e0, e1 = 20 * (d0 + d2), 20 * (d0 - d2)
        o0, o1 = 26 * d1 + 11 * d3, 11 * d1 - 26 * d3
        row = (shift_round(e0 + o0), shift_round(e1 + o1), shift_round(e1 - o1), shift_round(e0 - o0))
        t.append([_sat16(v) for v in row] if sat else list(row))
    return t


def _cols(t: list[list[int]], add: int, shift: int) -> list[int]:
    """Second pass: out[r][c] = (sum_k BASIS[k][r] * t[k][c] + add) >> shift, returned row-major by r."""
    out = [0] * 16
    t0, t1, t2, t3 = t
    for c in range(4):
        a, b, cc, d = t0[c], t1[c], t2[c], t3[c]
        e0, e1 = 20 * (a + cc), 20 * (a - cc)
        o0, o1 = 26 * b + 11 * d, 11 * b - 26 * d
        out[c] = (e0 + o0 + add) >> shift
        out[4 + c] = (e1 + o1 + add) >> shift
        out[8 + c] = (e1 - o1 + add) >> shift
        out[12 + c] = (e0 - o0 + add) >> shift
    return out


def color_tables(quality: int) -> list[list[tuple[int, int]]]:
    """Per channel (Y, Cb, Cr): 16 dequantisers, each split into (high i16, low word as signed i16)."""
    s = color_scale(quality)
    tables = []
    for ch in range(3):
        tab = []
        for q in QUANT:
            t = _s32((q * s) << (1 if ch else 0))
            lo = t & 0xFFFF
            tab.append((_sat16(t >> 16), lo - 0x10000 if lo >= 0x8000 else lo))
        tables.append(tab)
    return tables


def idct_color(coefs: list[int], table: list[tuple[int, int]]) -> list[int]:
    """Endpoint-image tile: 16 coefficients -> 16 samples out[r][c] (row-major)."""
    d = [_s16(hi * c + ((lo * c) >> 16)) for c, (hi, lo) in zip((_sat16(c) for c in coefs), table)]
    return _cols(_rows(d, lambda s: (s + 16) >> 5, True), 512, 10)


def idct_selector(coefs: list[int], scale: int, dc_only: bool) -> list[int]:
    """Selector block: 16 coefficients -> 16 values out[r][c] (row-major)."""
    if dc_only:
        return [_s32(_s32(_s32(coefs[0] * scale) * QUANT[0]) * 400 + 0x80000) >> 20] * 16
    s = _s16(scale)
    d = [_s16(_s16(_sat16(c) * s) * q) for c, q in zip(coefs, QUANT)]
    return _cols(_rows(d, lambda v: v >> 9, True), 1024, 11)


def selector_word(values: list[int]) -> int:
    """16 decoded selector values (row-major) -> DXT1 index word."""
    word = 0
    for i, v in enumerate(values):
        p = _s16(_sat16(v) + 2)
        p = 0 if p < 0 else 3 if p > 3 else p
        word |= SELECTOR_ORDER[p] << (2 * i)
    return word


def ycbcr_to_565(y: int, cb: int, cr: int) -> int:
    """Endpoint colour conversion: float32 maths, round-half-even, clamp, truncate to 565."""
    yf = _f32((y - 16.0) * _KY)
    fcb, fcr = float(cb - 128), float(cr - 128)
    r = _f32(_f32(_KCR_R * fcr) + yf)
    g = _f32(_f32(yf - _f32(fcb * _KCB_G)) - _f32(fcr * _KCR_G))
    b = _f32(_f32(fcb * _KCB_B) + yf)
    r, g, b = (min(255, max(0, _sat16(round(v)))) for v in (r, g, b))
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def fix_order(ends: list[list[int]], toggles: list[int]) -> None:
    """Endpoint-order pass (in place): four-colour blocks get c0 > c1, three-colour blocks c0 <= c1.

    With no toggle list every block is made four-colour; an equal pair becomes (c|1, c) or (c, c-1).
    Otherwise the list gives run lengths after which the wanted mode flips (starting four-colour).
    """
    total = len(ends)
    four = True
    nxt = toggles[0] if toggles else total
    used = 0
    for i, e in enumerate(ends):
        if toggles and i == nxt:
            used += 1
            nxt = nxt + toggles[used] if used < len(toggles) else total
            four = not four
        c0, c1 = e
        if four:
            if c0 > c1:
                continue
            if c0 != c1:
                e[0], e[1] = c1, c0
            elif c0 & 1 == 0:
                e[0], e[1] = c0 | 1, c0
            else:
                e[0], e[1] = c0, c0 - 1
        elif c0 > c1:
            e[0], e[1] = c1, c0


# ---------------------------------------------------------------------------------------------------------
# Decoding

@dataclass
class Decoded:
    """Everything `decode_full` recovers; `dxt` is the decoded DXT1 surface."""
    header: Header
    planes: list[list[int]]          # 6 endpoint images (EP0 Y, Cb, Cr, EP1 Y, Cb, Cr), width*height each
    ends: list[list[int]]            # per block [c0, c1] after the order pass
    selectors: list[int]             # per block index word
    toggles: list[int]
    raw_selectors: list[int]
    dxt: bytes
    banks: list["_Bank"]             # the 6 endpoint banks and the selector bank, with what they held


def inflate(payload: bytes) -> tuple[Header, bytes]:
    head = Header.parse(payload)
    d = zlib.decompressobj()
    body = d.decompress(bytes(payload[HEADER.size:]))
    if len(body) != head.body_size:
        raise ValueError(f"TGU1 body is {len(body)} bytes, header says {head.body_size}")
    return head, body


def decode_full(payload: bytes) -> Decoded:
    head, body = inflate(payload)
    if head.version != VERSION:
        raise ValueError(f"unsupported TGU1 version {head.version} (only {VERSION})")
    if not head.flags & FLAG_CODED or head.flags & FLAG_ALPHA:
        raise ValueError(f"unsupported TGU1 flags {head.flags:#x} (only DXT1 terrain, {FLAG_CODED:#x})")
    w, h = head.width, head.height
    # block_count is w × h in every terrain tile, but smaller in model atlases (a France buildings atlas of 128 x 128
    # blocks says 14805), for a reason not known yet; decoding doesn't use it: the banks' own checks below (every
    # stream used up, no bytes left over) are what say a payload was read right.
    if w % 4 or h % 4 or head.block_count > w * h:
        raise ValueError(f"unsupported TGU1 size {w}x{h} blocks ({head.block_count})")

    n_tog = struct.unpack_from("<I", body, 0)[0]
    toggles = list(struct.unpack_from("<%dI" % n_tog, body, 4))
    pos = 4 + 4 * n_tog
    banks = []
    for _ in range(6):
        bank = _Bank(body, pos, has_raw=False, dc_predict=True)
        banks.append(bank)
        pos = bank.end
    sel_bank = _Bank(body, pos, has_raw=True, dc_predict=False)
    if sel_bank.end != len(body):
        raise ValueError(f"TGU1 body has {len(body) - sel_bank.end} unexpected trailing bytes")

    tables = color_tables(head.color_quality)
    planes = [[0] * (w * h) for _ in range(6)]
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            for p in range(6):
                coefs, _ = banks[p].block()
                out = idct_color(coefs, tables[p % 3])
                plane = planes[p]
                for r in range(4):          # sample (row by+c, column bx+r) = out[r][c]: tiles are transposed
                    for c in range(4):
                        plane[(by + c) * w + bx + r] = out[r * 4 + c]

    cache: dict[tuple[int, int, int], int] = {}

    def rgb(y: int, cb: int, cr: int) -> int:
        key = (y, cb, cr)
        v = cache.get(key)
        if v is None:
            v = cache[key] = ycbcr_to_565(y, cb, cr)
        return v

    y0, cb0, cr0, y1, cb1, cr1 = planes
    ends = [[rgb(y0[i], cb0[i], cr0[i]), rgb(y1[i], cb1[i], cr1[i])] for i in range(w * h)]
    fix_order(ends, toggles)

    raw = iter(sel_bank.raw)
    selectors = []
    scale = head.selector_quality
    for c0, c1 in ends:
        if c0 > c1:
            coefs, dc_only = sel_bank.block()
            selectors.append(selector_word(idct_selector(coefs, scale, dc_only)))
        elif c0 == c1:
            selectors.append(0)
        else:
            selectors.append(next(raw))
    for bank in banks + [sel_bank]:
        bank.check_consumed()
    dxt = b"".join(struct.pack("<HHI", c0, c1, s) for (c0, c1), s in zip(ends, selectors))
    return Decoded(head, planes, ends, selectors, toggles, sel_bank.raw, dxt, banks + [sel_bank])


def decode(payload: bytes) -> bytes:
    """TGU1 payload -> raw DXT1 blocks (8 bytes per 4x4 block, rows of blocks top to bottom)."""
    return decode_full(payload).dxt


# ---------------------------------------------------------------------------------------------------------
# Bit stream writing

def _unsigned(v: int) -> int:
    return v << 1 if v >= 0 else ((-v) << 1) - 1


def _code_bits(u: int, mode: int) -> str:
    """One value's code as a string of bits in stream order (LSB-first)."""
    if mode >= 8:
        k = mode - 8
        q = u >> k
        return "0" * q + "1" + (format(u & ((1 << k) - 1), "0%db" % k)[::-1] if k else "")
    v = u + (1 << mode)
    n = v.bit_length() - 1                     # m + k
    return "0" * (n - mode) + "1" + (format(v - (1 << n), "0%db" % n)[::-1] if n else "")


def _code_len(u: int, mode: int) -> int:
    if mode >= 8:
        k = mode - 8
        return (u >> k) + 1 + k
    n = (u + (1 << mode)).bit_length() - 1
    return 2 * n - mode + 1


def _best_mode(us: list[int]) -> int:
    """Cheapest mode, lowest number on ties (what the shipped encoder picked in every sub-band checked).

    Exp-Golomb codes longer than 32 bits are never used.
    """
    top = max(us, default=0)
    best, best_len = 0, None
    for mode in range(16):
        if mode < 8 and _code_len(top, mode) > 32:
            continue
        n = sum(_code_len(u, mode) for u in us)
        if best_len is None or n < best_len:
            best, best_len = mode, n
    return best


def _subband(values: list[int]) -> tuple[int, bytes]:
    us = [_unsigned(v) for v in values]
    mode = _best_mode(us)
    bits = "".join(_code_bits(u, mode) for u in us)
    nbits = len(bits)
    if nbits >= 1 << 28:
        raise ValueError("TGU1 sub-band too large")
    nbytes = (nbits + 31) // 32 * 4
    data = int(bits[::-1], 2).to_bytes(nbytes, "little") if nbits else b""
    return mode << 28 | nbits, data


def pack_bank(blocks: list[list[int]], raw: list[int] | None = None) -> bytes:
    """One bank from per-block coefficients as stored (row-major, colour DCs already delta-coded).

    `raw` (selector bank only) is the list of raw selector words; None writes a bank without that field.
    """
    streams: list[list[int]] = [[] for _ in range(17)]
    prev = 0
    for coefs in blocks:
        n = 0
        for j in range(16):
            if coefs[ZIGZAG[j]]:
                n = j + 1
        streams[0].append(n - prev)
        prev = n
        for j in range(n):
            streams[j + 1].append(coefs[ZIGZAG[j]])
    descs, datas = [], []
    for values in streams:
        d, data = _subband(values)
        descs.append(d)
        datas.append(data)
    head = b"" if raw is None else struct.pack("<I", len(raw))
    tail = b"" if raw is None else struct.pack("<%dI" % len(raw), *raw)
    return head + struct.pack("<17I", *descs) + tail + b"".join(datas)


def deflate(body: bytes, level: int = 9) -> bytes:
    """zlib stream ended with a sync flush and no final block, as the shipped payloads are."""
    c = zlib.compressobj(level)
    return c.compress(body) + c.flush(zlib.Z_SYNC_FLUSH)


def pack_payload(header: Header, body: bytes, level: int = 9) -> bytes:
    header.body_size = len(body)
    return header.pack() + deflate(body, level)


# ---------------------------------------------------------------------------------------------------------
# Encoding: DXT1 blocks -> coefficients that decode back into those blocks
#
# Both searches start from the linear model of the inverse transform (the basis rows are orthogonal, so
# the forward transform is a scaled transpose), round, then fix what rounding broke by trying +-1 steps on
# single coefficients, keeping any step that lowers the total distance to the target. Candidate results
# are always checked with the exact decoder above, so a block is only called exact when it really is.

_NORM = (1600, 1594, 1600, 1594)              # squared lengths of the basis rows
_INF = float("inf")

# Inverse of the colour matrix (R, G, B from Y-16, Cb-128, Cr-128), for starting points only.
_M = ((_KY, 0.0, _KCR_R), (_KY, -_KCB_G, -_KCR_G), (_KY, _KCB_B, 0.0))


def _inv3(m):
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return ((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det), \
           ((f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det), \
           ((d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det)


_MINV = _inv3(_M)


def _rgb_float(y: int, cb: int, cr: int) -> tuple[float, float, float]:
    yf = _KY * (y - 16)
    return yf + _KCR_R * (cr - 128), yf - _KCB_G * (cb - 128) - _KCR_G * (cr - 128), yf + _KCB_B * (cb - 128)


def _box(c: int) -> tuple[tuple[float, float], ...]:
    """Unrounded R, G, B ranges that the conversion maps onto the 565 colour c."""
    r, g, b = c >> 11, (c >> 5) & 63, c & 31
    return ((8 * r - 0.5 if r else -_INF, 8 * r + 7.5 if r < 31 else _INF),
            (4 * g - 0.5 if g else -_INF, 4 * g + 3.5 if g < 63 else _INF),
            (8 * b - 0.5 if b else -_INF, 8 * b + 7.5 if b < 31 else _INF))


def _box_target(c: int) -> tuple[float, float, float]:
    """A Y, Cb, Cr point in the middle of the 565 colour's box."""
    r, g, b = c >> 11, (c >> 5) & 63, c & 31
    rgb = (8 * r + 3.5, 4 * g + 1.5, 8 * b + 3.5)
    y, cb, cr = (sum(_MINV[i][j] * rgb[j] for j in range(3)) for i in range(3))
    return y + 16, cb + 128, cr + 128


def _forward(samples: list[float], gain: list[float]) -> list[float]:
    """Real coefficients whose (linear-model) inverse transform gives `samples` (row-major out[r][c])."""
    coefs = []
    for k in range(4):
        bk = BASIS[k]
        rowsum = [sum(bk[r] * samples[r * 4 + c] for r in range(4)) for c in range(4)]
        for u in range(4):
            bu = BASIS[u]
            s = sum(bu[c] * rowsum[c] for c in range(4))
            coefs.append(s / (_NORM[k] * _NORM[u] * gain[k * 4 + u]))
    return coefs


def _color_gain(table: list[tuple[int, int]]) -> list[float]:
    return [(hi + lo / 65536.0) / 32768.0 for hi, lo in table]


def _selector_gain(scale: int) -> list[float]:
    return [scale * q / 1048576.0 for q in QUANT]


def _viol(v: float, lo: float, hi: float) -> float:
    return lo - v + 0.05 if v < lo + 0.05 else v - hi + 0.05 if v > hi - 0.05 else 0.0


class _ColorFit:
    """Coefficients for one endpoint (Y, Cb, Cr) of one 4x4-block tile, aiming at 16 target 565 colours."""

    def __init__(self, targets: list[int], tables: list[list[tuple[int, int]]]):
        self.targets = targets                 # row-major by out[r][c]
        self.boxes = [_box(t) for t in targets]
        self.tables = tables
        self.gains = [_color_gain(t) for t in tables]

    def outs(self, z: list[list[int]]) -> list[list[int]]:
        return [idct_color(z[ch], self.tables[ch]) for ch in range(3)]

    def cost(self, o: list[list[int]]) -> float:
        total = 0.0
        for i, box in enumerate(self.boxes):
            for v, (lo, hi) in zip(_rgb_float(o[0][i], o[1][i], o[2][i]), box):
                if v < lo + 0.05 or v > hi - 0.05:
                    total += _viol(v, lo, hi)
        return total

    def exact(self, o: list[list[int]]) -> bool:
        return all(ycbcr_to_565(o[0][i], o[1][i], o[2][i]) == t for i, t in enumerate(self.targets))

    def solve(self, sweeps: int = 12) -> tuple[list[list[int]], bool]:
        pts = [_box_target(t) for t in self.targets]
        goal = [[p[ch] for p in pts] for ch in range(3)]
        z = [[round(v) for v in _forward(goal[ch], self.gains[ch])] for ch in range(3)]
        o = self.outs(z)
        # Nudge the goals by how far each sample landed outside its box, re-solve, a few times.
        for _ in range(3):
            if self.exact(o):
                return z, True
            for i, box in enumerate(self.boxes):
                rgb = _rgb_float(o[0][i], o[1][i], o[2][i])
                push = [(lo - v + 0.5 if v < lo else hi - v - 0.5 if v > hi else 0.0) for v, (lo, hi) in zip(rgb, box)]
                if any(push):
                    dy = [sum(_MINV[a][b] * push[b] for b in range(3)) for a in range(3)]
                    for ch in range(3):
                        goal[ch][i] += dy[ch]
            z = [[round(v) for v in _forward(goal[ch], self.gains[ch])] for ch in range(3)]
            o = self.outs(z)
        cost = self.cost(o)
        for _ in range(sweeps):
            if cost == 0.0 and self.exact(o):
                return z, True
            better = False
            for ch in range(3):
                for i in range(16):
                    for step in (1, -1):
                        z[ch][i] += step
                        oc = idct_color(z[ch], self.tables[ch])
                        trial = o[:ch] + [oc] + o[ch + 1:]
                        c = self.cost(trial)
                        if c < cost:
                            o, cost, better = trial, c, True
                            break
                        z[ch][i] -= step
            if not better:
                break
        return z, self.exact(o)


def _selector_targets(word: int) -> list[tuple[float, float]]:
    """Per pixel, the range of the unrounded decoded value v (out = floor(v)) that gives the wanted index."""
    ranges = ((-_INF, -1.0), (-1.0, 0.0), (0.0, 1.0), (1.0, _INF))
    return [ranges[POSITION_OF_INDEX[(word >> (2 * i)) & 3]] for i in range(16)]


def _selector_values(coefs: list[int], scale: int) -> list[float]:
    """Unrounded version of idct_selector (v such that out = floor(v)), for measuring distance to a target."""
    s = _s16(scale)
    d = [_s16(_s16(_sat16(c) * s) * q) for c, q in zip(coefs, QUANT)]
    t = _rows(d, lambda v: v >> 9, True)
    return [(v + 1024) / 2048.0 for v in _cols(t, 0, 0)]


def _is_dc_only(coefs: list[int]) -> bool:
    return not any(coefs[1:])


def fit_selectors(word: int, scale: int, sweeps: int = 16) -> tuple[list[int], bool]:
    """Coefficients for one selector block whose decode gives `word` (exact when the bool is True)."""
    ranges = _selector_targets(word)
    centre = {(-_INF, -1.0): -2.0, (-1.0, 0.0): -0.5, (0.0, 1.0): 0.5, (1.0, _INF): 2.0}
    goal = [centre[r] for r in ranges]
    gain = _selector_gain(scale)
    z = [round(v) for v in _forward(goal, gain)]

    def exact(z: list[int]) -> bool:
        return selector_word(idct_selector(z, scale, _is_dc_only(z))) == word

    def cost(z: list[int]) -> float:
        return sum(_viol(v, lo, hi) for v, (lo, hi) in zip(_selector_values(z, scale), ranges))

    if exact(z):
        return z, True
    best = cost(z)
    for _ in range(sweeps):
        better = False
        for i in range(16):
            for step in (1, -1):
                z[i] += step
                c = cost(z)
                if c < best:
                    best, better = c, True
                    if exact(z):
                        return z, True
                    break
                z[i] -= step
        if not better:
            break
    return z, exact(z)


def _blocks(dxt: bytes, n: int) -> tuple[list[list[int]], list[int]]:
    ends, words = [], []
    for i in range(n):
        c0, c1, w = struct.unpack_from("<HHI", dxt, 8 * i)
        ends.append([c0, c1])
        words.append(w)
    return ends, words


def _as_four_colour(ends: list[list[int]], words: list[int], dxt: bytes) -> None:
    """Make every block a four-colour block (in place): what decoding makes of it with no toggle list."""
    from .dxt import best_indices, block_pixels
    for i, e in enumerate(ends):
        if e[0] > e[1]:
            continue
        pixels = block_pixels(dxt[8 * i:8 * i + 8])
        fix_order([e], [])
        words[i] = best_indices(pixels, e[0], e[1])[0]


def encode(dxt: bytes, width: int, height: int, flags: int = FLAG_CODED, color_quality: int = 80,
           selector_quality: int = 40, level: int = 9, stats: dict | None = None) -> bytes:
    """DXT1 blocks -> TGU1 payload. width/height in pixels (multiples of 16).

    Blocks decode exactly as given when the search finds coefficients for them;
    `stats` (optional dict) receives how many endpoint tiles and selector blocks were exact. Three-colour
    blocks (c0 <= c1) are first turned into the four-colour blocks decoding would make of them.
    """
    if width % 16 or height % 16:
        raise ValueError("TGU1 needs width and height in multiples of 16 pixels")
    if flags != FLAG_CODED:
        raise ValueError(f"only flags {FLAG_CODED:#x} (DXT1 terrain) can be written")
    w, h = width // 4, height // 4
    n = w * h
    if len(dxt) < 8 * n:
        raise ValueError(f"need {8 * n} bytes of DXT1 data, got {len(dxt)}")
    target_ends, target_words = _blocks(dxt, n)
    _as_four_colour(target_ends, target_words, dxt)

    tables = color_tables(color_quality)
    tiles_exact = 0
    coefs = [[] for _ in range(6)]                 # per plane, per tile, 16 coefficients (DC not yet delta'd)
    planes = [[0] * n for _ in range(6)]
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            where = [(by + c) * w + bx + r for r in range(4) for c in range(4)]   # out[r][c] -> block index
            for e in range(2):
                fit = _ColorFit([target_ends[i][e] for i in where], tables)
                z, ok = fit.solve()
                tiles_exact += ok
                for ch in range(3):
                    coefs[3 * e + ch].append(z[ch])
                    out = idct_color(z[ch], tables[ch])
                    for s, i in enumerate(where):
                        planes[3 * e + ch][i] = out[s]

    # What decoding will actually make of those endpoints.
    y0, cb0, cr0, y1, cb1, cr1 = planes
    ends = [[ycbcr_to_565(y0[i], cb0[i], cr0[i]), ycbcr_to_565(y1[i], cb1[i], cr1[i])] for i in range(n)]
    fix_order(ends, [])

    from .dxt import best_indices, block_pixels
    sel_blocks, sel_exact, ends_exact = [], 0, 0
    for i in range(n):
        if ends[i] == target_ends[i]:
            ends_exact += 1
            word = target_words[i]
        else:  # endpoints drifted: pick the indices that best match the wanted pixels instead
            word = best_indices(block_pixels(dxt[8 * i:8 * i + 8]), ends[i][0], ends[i][1])[0]
        z, ok = fit_selectors(word, selector_quality)
        sel_exact += ok
        sel_blocks.append(z)

    body = [struct.pack("<I", 0)]
    for p in range(6):
        prev, stored = 0, []
        for z in coefs[p]:
            z = z[:]
            z[0], prev = z[0] - prev, z[0]
            stored.append(z)
        body.append(pack_bank(stored))
    body.append(pack_bank(sel_blocks, raw=[]))
    if stats is not None:
        stats.update(endpoint_tiles=2 * (n // 16), endpoint_tiles_exact=tiles_exact, blocks=n,
                     endpoints_exact=ends_exact, selector_blocks_exact=sel_exact)
    head = Header(VERSION, w, h, color_quality, selector_quality, n, flags)
    return pack_payload(head, b"".join(body), level)
