"""DXT1 (BC1) blocks <-> RGB pixels, plus a tiny PNG writer for previews.

A DXT1 block is 8 bytes covering 4x4 pixels: two RGB565 endpoint colours (u16 little-endian, c0 then c1)
and 16 two-bit palette indices (u32 little-endian; row r is byte r, pixel c of the row is bits 2c..2c+1).
When c0 > c1 the palette is c0, c1, 2/3*c0+1/3*c1, 1/3*c0+2/3*c1; otherwise it is c0, c1, the midpoint and
black (transparent). Blocks are stored row by row, left to right.

The encoder here is deliberately simple (principal-axis endpoints, a few refinement passes, exhaustive
index choice). It always emits four-colour blocks (c0 > c1), except for a flat block, which gets c0 == c1
and all-zero indices. Pure stdlib, so it is slow-ish (a 512x512 image takes a few seconds).
"""
from __future__ import annotations

import struct
import zlib
from typing import BinaryIO


def unpack565(c: int) -> tuple[int, int, int]:
    """RGB565 -> 8-bit RGB with the usual bit replication."""
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)


def pack565(r: int, g: int, b: int) -> int:
    """8-bit RGB -> RGB565, rounding each channel to the nearest level."""
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)


def palette(c0: int, c1: int) -> list[tuple[int, int, int]]:
    """The four colours a block can use (the common integer approximation of the GPU interpolation)."""
    a, b = unpack565(c0), unpack565(c1)
    if c0 > c1:
        return [a, b,
                tuple((2 * x + y + 1) // 3 for x, y in zip(a, b)),
                tuple((x + 2 * y + 1) // 3 for x, y in zip(a, b))]
    return [a, b, tuple((x + y) // 2 for x, y in zip(a, b)), (0, 0, 0)]


def decode(data: bytes, width: int, height: int) -> bytearray:
    """DXT1 blocks -> RGB pixels (3 bytes per pixel, rows top to bottom). width/height in pixels (multiples of 4)."""
    bw, bh = width // 4, height // 4
    if len(data) < bw * bh * 8:
        raise ValueError(f"need {bw * bh * 8} bytes of DXT1 data for {width}x{height}, got {len(data)}")
    out = bytearray(width * height * 3)
    stride = width * 3
    for by in range(bh):
        for bx in range(bw):
            c0, c1, idx = struct.unpack_from("<HHI", data, (by * bw + bx) * 8)
            pal = [bytes(p) for p in palette(c0, c1)]
            base = by * 4 * stride + bx * 12
            for r in range(4):
                row = base + r * stride
                for c in range(4):
                    out[row + c * 3:row + c * 3 + 3] = pal[(idx >> (2 * (r * 4 + c))) & 3]
    return out


def _dist(p: tuple[int, int, int], q: tuple[int, int, int]) -> int:
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2


def best_indices(pixels: list[tuple[int, int, int]], c0: int, c1: int) -> tuple[int, int]:
    """Pick the nearest palette entry for each of the 16 pixels (the first of equals). Returns (index word, total
    squared error). Unrolled over the palette's four colours: the encoder's inner loop, run many times a block."""
    (r0, g0, b0), (r1, g1, b1), (r2, g2, b2), (r3, g3, b3) = palette(c0, c1)
    word = err = shift = 0
    for r, g, b in pixels:
        d0, d1, d2 = r - r0, g - g0, b - b0
        be, best = d0 * d0 + d1 * d1 + d2 * d2, 0
        d0, d1, d2 = r - r1, g - g1, b - b1
        e = d0 * d0 + d1 * d1 + d2 * d2
        if e < be:
            be, best = e, 1
        d0, d1, d2 = r - r2, g - g2, b - b2
        e = d0 * d0 + d1 * d1 + d2 * d2
        if e < be:
            be, best = e, 2
        d0, d1, d2 = r - r3, g - g3, b - b3
        e = d0 * d0 + d1 * d1 + d2 * d2
        if e < be:
            be, best = e, 3
        word |= best << shift
        err += be
        shift += 2
    return word, err


def _endpoints(pixels: list[tuple[int, int, int]]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Extremes of the block along its principal colour axis (power iteration on the covariance)."""
    # written out as plain loops for speed, adding in the same order as before, so every value is the same to the bit
    n = len(pixels)
    sr = sg = sb = 0
    for r, g, b in pixels:
        sr += r
        sg += g
        sb += b
    mr, mg, mb = sr / n, sg / n, sb / n
    c00 = c01 = c02 = c11 = c12 = c22 = 0
    for r, g, b in pixels:
        dr, dg, db = r - mr, g - mg, b - mb
        c00 += dr * dr
        c01 += dr * dg
        c02 += dr * db
        c11 += dg * dg
        c12 += dg * db
        c22 += db * db
    ax, ay, az = 1.0, 1.0, 1.0
    for _ in range(8):
        ax, ay, az = c00 * ax + c01 * ay + c02 * az, c01 * ax + c11 * ay + c12 * az, c02 * ax + c12 * ay + c22 * az
        norm = max(abs(ax), abs(ay), abs(az)) or 1.0
        ax, ay, az = ax / norm, ay / norm, az / norm
    lo = hi = None
    for r, g, b in pixels:
        t = (r - mr) * ax + (g - mg) * ay + (b - mb) * az
        if lo is None or t < lo:
            lo = t
        if hi is None or t > hi:
            hi = t
    return (mr + hi * ax, mg + hi * ay, mb + hi * az), (mr + lo * ax, mg + lo * ay, mb + lo * az)


def _to565(c: tuple[float, ...]) -> int:
    return pack565(*(min(255, max(0, int(round(x)))) for x in c))


def encode_block(pixels: list[tuple[int, int, int]]) -> bytes:
    """16 RGB pixels (row-major) -> one 8-byte four-colour DXT1 block."""
    if all(p == pixels[0] for p in pixels):
        c = pack565(*pixels[0])
        return struct.pack("<HHI", c, c, 0)
    hi, lo = _endpoints(pixels)
    best = None
    cands = {(_to565(hi), _to565(lo))}
    # Nudge the quantised endpoints a little: cheap and often worth a few units of error.
    a, b = _to565(hi), _to565(lo)
    for da in (-0x0821, 0, 0x0821):
        for db in (-0x0821, 0, 0x0821):
            if 0 <= a + da <= 0xFFFF and 0 <= b + db <= 0xFFFF:
                cands.add((a + da, b + db))
    for c0, c1 in cands:
        if c0 == c1:
            continue
        if c0 < c1:
            c0, c1 = c1, c0
        word, err = best_indices(pixels, c0, c1)
        if best is None or err < best[0]:
            best = (err, c0, c1, word)
    if best is None:  # every candidate collapsed to one colour
        c = _to565(hi)
        return struct.pack("<HHI", c, c, 0)
    _, c0, c1, word = best
    return struct.pack("<HHI", c0, c1, word)


def encode(rgb: bytes, width: int, height: int) -> bytes:
    """RGB pixels (3 bytes per pixel, rows top to bottom) -> DXT1 blocks. width/height multiples of 4."""
    if width % 4 or height % 4:
        raise ValueError("width and height must be multiples of 4")
    stride = width * 3
    out = bytearray()
    for by in range(height // 4):
        for bx in range(width // 4):
            px = []
            for r in range(4):
                o = (by * 4 + r) * stride + bx * 12
                px.extend(tuple(rgb[o + 3 * c:o + 3 * c + 3]) for c in range(4))
            out += encode_block(px)
    return bytes(out)


def block_pixels(block: bytes) -> list[tuple[int, int, int]]:
    """The 16 RGB pixels (row-major) an 8-byte DXT1 block stands for."""
    c0, c1, idx = struct.unpack("<HHI", block[:8])
    pal = palette(c0, c1)
    return [pal[(idx >> (2 * i)) & 3] for i in range(16)]


def decode_rgba(data: bytes, width: int, height: int, fmt: str = "DXT1") -> bytearray:
    """DXT1 or DXT5 blocks -> RGBA pixels (4 bytes per pixel, rows top to bottom), for model textures: a DXT1
    block with c0 <= c1 makes its 4th colour transparent (tree leaves are cut out that way); a DXT5 block is 8 bytes
    of alpha (two 8-bit endpoints, 16 three-bit indices) before its colour block, whose colours are always four."""
    bw, bh, dxt5 = width // 4, height // 4, fmt.upper() == "DXT5"
    size = 16 if dxt5 else 8
    if len(data) < bw * bh * size:
        raise ValueError(f"need {bw * bh * size} bytes of {fmt} data for {width}x{height}, got {len(data)}")
    out = bytearray(width * height * 4)
    stride = width * 4
    for by in range(bh):
        for bx in range(bw):
            at = (by * bw + bx) * size
            alphas = None
            if dxt5:
                a0, a1 = data[at], data[at + 1]
                bits = int.from_bytes(data[at + 2:at + 8], "little")
                if a0 > a1:
                    table = [a0, a1] + [((7 - k) * a0 + k * a1 + 3) // 7 for k in range(1, 7)]
                else:
                    table = [a0, a1] + [((5 - k) * a0 + k * a1 + 2) // 5 for k in range(1, 5)] + [0, 255]
                alphas = [table[(bits >> (3 * i)) & 7] for i in range(16)]
                at += 8
            c0, c1, idx = struct.unpack_from("<HHI", data, at)
            a, b = unpack565(c0), unpack565(c1)
            if c0 > c1 or dxt5:
                pal = [a + (255,), b + (255,), tuple((2 * x + y + 1) // 3 for x, y in zip(a, b)) + (255,),
                       tuple((x + 2 * y + 1) // 3 for x, y in zip(a, b)) + (255,)]
            else:
                pal = [a + (255,), b + (255,), tuple((x + y) // 2 for x, y in zip(a, b)) + (255,), (0, 0, 0, 0)]
            base = by * 4 * stride + bx * 16
            for i in range(16):
                r, c = divmod(i, 4)
                px = pal[(idx >> (2 * i)) & 3]
                if alphas is not None:
                    px = px[:3] + (alphas[i],)
                o = base + r * stride + c * 4
                out[o:o + 4] = bytes(px)
    return out


def _alpha_table(a0: int, a1: int) -> list[int]:
    if a0 > a1:
        return [a0, a1] + [((7 - k) * a0 + k * a1 + 3) // 7 for k in range(1, 7)]
    return [a0, a1] + [((5 - k) * a0 + k * a1 + 2) // 5 for k in range(1, 5)] + [0, 255]


def dxt5_block(block: bytes) -> tuple[list[tuple[int, int, int]], list[int]]:
    """The 16 RGB pixels and 16 alphas (row-major) a 16-byte DXT5 block stands for (its colours always four)."""
    table = _alpha_table(block[0], block[1])
    bits = int.from_bytes(block[2:8], "little")
    c0, c1, idx = struct.unpack_from("<HHI", block, 8)
    a, b = unpack565(c0), unpack565(c1)
    pal = [a, b, tuple((2 * x + y + 1) // 3 for x, y in zip(a, b)), tuple((x + 2 * y + 1) // 3 for x, y in zip(a, b))]
    return [pal[(idx >> (2 * i)) & 3] for i in range(16)], [table[(bits >> (3 * i)) & 7] for i in range(16)]


def encode_dxt5_block(pixels: list[tuple[int, int, int]], alphas: list[int]) -> bytes:
    """16 RGB pixels and 16 alphas (row-major) -> one 16-byte DXT5 block: the alpha endpoints the block's highest and
    lowest (eight steps between), each alpha its nearest step; the colours as encode_block's four-colour block."""
    a0, a1 = max(alphas), min(alphas)
    table = _alpha_table(a0, a1)
    bits = 0
    for i, v in enumerate(alphas):
        k = min(range(8), key=lambda j: abs(table[j] - v))
        bits |= k << (3 * i)
    return bytes((a0, a1)) + bits.to_bytes(6, "little") + encode_block(pixels)


def png_bytes(rgb: bytes, width: int, height: int, channels: int = 3) -> bytes:
    """Minimal 8-bit RGB (or, with channels=4, RGBA) PNG (no filtering)."""
    stride = width * channels
    raw = b"".join(b"\0" + bytes(rgb[y * stride:(y + 1) * stride]) for y in range(height))

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6 if channels == 4 else 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")


def write_png(out: str | BinaryIO, rgb: bytes, width: int, height: int) -> None:
    data = png_bytes(rgb, width, height)
    if isinstance(out, str):
        with open(out, "wb") as f:
            f.write(data)
    else:
        out.write(data)
