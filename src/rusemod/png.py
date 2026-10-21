"""PNG pictures read into plain pixels (stdlib only): what Blender, GIMP or Paint save. 8- and 16-bit grey, grey +
alpha, RGB, RGBA and 8-bit palette pictures, not interlaced (the default everywhere). The writer is rusemod.dxt.png_bytes.

With numpy there (rusemod.picturenp), the rows' filters are undone and a palette looked up for every pixel at once: the
same pixels, many times sooner. The loops here are what that is checked against (tests/test_picturenp.py), and what
runs without numpy."""
from __future__ import annotations

import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}  # colour type -> samples per pixel


class PngError(ValueError):
    pass


_WHOLE = []  # [rusemod.picturenp, or None without numpy], looked for once


def whole_arrays():
    """rusemod.picturenp, the pictures on whole arrays, when numpy is there (the apps carry it); None without it."""
    if not _WHOLE:
        try:
            from . import picturenp
            _WHOLE.append(picturenp)
        except ImportError:
            _WHOLE.append(None)
    return _WHOLE[0]


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> bytearray:
    """The scanlines without their filters (bpp: bytes per pixel, at least 1)."""
    arrays = whole_arrays()
    whole = arrays.unfilter(raw, width, height, bpp) if arrays else None
    if whole is not None:   # (numpy: the same bytes, every pixel at once)
        return whole
    stride = width * bpp
    out = bytearray(stride * height)
    prev = bytearray(stride)
    pos = 0
    for y in range(height):
        kind = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if len(line) != stride:
            raise PngError("the picture's data ends early")
        if kind == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif kind == 2:
            line = bytearray((a + b) & 0xFF for a, b in zip(line, prev))
        elif kind == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif kind == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                up_left = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], up_left)) & 0xFF
        elif kind != 0:
            raise PngError(f"unknown PNG filter {kind}")
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return out


def grey16_bytes(width: int, height: int, samples: bytes) -> bytes:
    """A 16-bit greyscale PNG of `samples` (2 bytes each, high byte first, rows top to bottom): a heightmap or an area
    picture (rusemod.relief) as read_grey16 reads it back. Each row filtered by its left neighbour (a run of one value
    packs to almost nothing)."""
    stride = 2 * width
    if len(samples) != stride * height:
        raise PngError(f"{len(samples)} bytes aren't {width} x {height} 16-bit samples")
    arrays = whole_arrays()
    raw = arrays.sub_filtered(samples, width, height, 2) if arrays else None
    if raw is None:
        rows = []
        for y in range(height):
            line = samples[y * stride:(y + 1) * stride]
            rows.append(b"\x01" + line[:2] + bytes((line[i] - line[i - 2]) & 0xFF for i in range(2, stride)))
        raw = b"".join(rows)

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    head = struct.pack(">IIBBBBB", width, height, 16, 0, 0, 0, 0)
    return SIGNATURE + chunk(b"IHDR", head) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")


def read_grey16(data: bytes) -> tuple[int, int, bytes]:
    """A greyscale PNG's bytes -> (width, height, its samples as 16-bit numbers: 2 bytes each, high byte first, rows
    top to bottom): a heightmap, every step kept (read_png keeps only the high byte). An 8-bit grey picture reads as
    its values times 257 (0..255 -> 0..65535)."""
    width, height, depth, ctype, pixels = _decoded(data)
    if ctype != 0:
        raise PngError(f"a heightmap must be a greyscale PNG (16-bit is best), not colour type {ctype}")
    if depth == 16:
        return width, height, bytes(pixels)
    out = bytearray(2 * len(pixels))
    out[0::2] = out[1::2] = pixels
    return width, height, bytes(out)


def _decoded(data: bytes):
    """(width, height, bit depth, colour type, the rows' samples with their filters undone) of a PNG that isn't a
    palette picture."""
    if data[:8] != SIGNATURE:
        raise PngError("not a PNG picture")
    pos, head, idat = 8, None, bytearray()
    while pos + 8 <= len(data):
        length, kind = struct.unpack_from(">I4s", data, pos)
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if head is None:
        raise PngError("the PNG has no header")
    width, height, depth, ctype, _compression, _filter, interlace = head
    if interlace:
        raise PngError("interlaced PNGs aren't read: save it without interlacing")
    if ctype not in CHANNELS or ctype == 3 or depth not in (8, 16):
        raise PngError(f"PNG of colour type {ctype} at {depth} bits isn't read here")
    bpp = CHANNELS[ctype] * depth // 8
    return width, height, depth, ctype, _unfilter(zlib.decompress(bytes(idat)), width, height, bpp)


def read_png(data: bytes) -> tuple[int, int, bytes]:
    """A PNG file's bytes -> (width, height, RGBA pixels: 4 bytes each, rows top to bottom)."""
    if data[:8] != SIGNATURE:
        raise PngError("not a PNG picture")
    pos, head, idat, palette, trns = 8, None, bytearray(), None, None
    while pos + 8 <= len(data):
        length, kind = struct.unpack_from(">I4s", data, pos)
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if head is None:
        raise PngError("the PNG has no header")
    width, height, depth, ctype, _compression, _filter, interlace = head
    if interlace:
        raise PngError("interlaced PNGs aren't read: save it without interlacing")
    if ctype not in CHANNELS or depth not in (8, 16) or (ctype == 3 and depth != 8):
        raise PngError(f"PNG of colour type {ctype} at {depth} bits isn't read: save it as 8-bit RGB or RGBA")
    samples = CHANNELS[ctype]
    bpp = samples * depth // 8
    pixels = _unfilter(zlib.decompress(bytes(idat)), width, height, bpp)
    if depth == 16:  # keep the high byte of each sample
        pixels = pixels[0::2]
    n = width * height
    out = bytearray(4 * n)
    if ctype == 6:
        out[:] = pixels
    elif ctype == 2:
        out[0::4], out[1::4], out[2::4] = pixels[0::3], pixels[1::3], pixels[2::3]
        out[3::4] = b"\xff" * n
    elif ctype == 0:
        out[0::4] = out[1::4] = out[2::4] = pixels
        out[3::4] = b"\xff" * n
    elif ctype == 4:
        out[0::4] = out[1::4] = out[2::4] = pixels[0::2]
        out[3::4] = pixels[1::2]
    else:  # palette
        if palette is None:
            raise PngError("a palette PNG without its palette")
        alpha = trns or b""
        arrays = whole_arrays()
        whole = arrays.palette_rgba(pixels, palette, alpha) if arrays else None
        if whole is not None:   # (numpy: the same pixels, all at once)
            return width, height, whole
        for i, k in enumerate(pixels):
            out[4 * i:4 * i + 3] = palette[3 * k:3 * k + 3]
            out[4 * i + 3] = alpha[k] if k < len(alpha) else 255
    return width, height, bytes(out)
