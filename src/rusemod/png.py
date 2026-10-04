"""PNG pictures read into plain pixels (stdlib only): what Blender, GIMP or Paint save. 8- and 16-bit grey, grey +
alpha, RGB, RGBA and 8-bit palette pictures, not interlaced (the default everywhere). The writer is rusemod.dxt.png_bytes."""
from __future__ import annotations

import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}  # colour type -> samples per pixel


class PngError(ValueError):
    pass


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> bytearray:
    """The scanlines without their filters (bpp: bytes per pixel, at least 1)."""
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
        for i, k in enumerate(pixels):
            out[4 * i:4 * i + 3] = palette[3 * k:3 * k + 3]
            out[4 * i + 3] = alpha[k] if k < len(alpha) else 255
    return width, height, bytes(out)
