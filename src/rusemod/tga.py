"""Reading Truevision .tga pictures (what most free 3D models ship their textures as): uncompressed or run-length,
24- or 32-bit colour or 8-bit grey, either row order. Gives RGBA pixels, top row first."""
from __future__ import annotations

import struct


class TgaError(ValueError):
    pass


def read_tga(raw: bytes) -> tuple[int, int, bytes]:
    """A .tga file's bytes -> (width, height, RGBA pixels, top row first)."""
    if len(raw) < 18:
        raise TgaError("too short for a .tga picture")
    idlen, cmap, kind = raw[0], raw[1], raw[2]
    w, h = struct.unpack_from("<HH", raw, 12)
    bits, desc = raw[16], raw[17]
    if cmap or kind not in (2, 3, 10, 11):
        raise TgaError(f"a .tga of kind {kind}{' with a colour map' if cmap else ''}: only true-colour and grey "
                       "pictures are read")
    grey = kind in (3, 11)
    if (grey and bits != 8) or (not grey and bits not in (24, 32)):
        raise TgaError(f"a {bits}-bit .tga: only 24- and 32-bit colour or 8-bit grey are read")
    size = bits // 8
    n = w * h
    pos = 18 + idlen
    if kind in (2, 3):
        data = raw[pos:pos + n * size]
    else:  # run-length: a head byte, then one pixel repeated (top bit set) or that many pixels
        out = bytearray()
        while len(out) < n * size:
            if pos >= len(raw):
                raise TgaError("the picture ends before its last pixel")
            head = raw[pos]
            pos += 1
            count = (head & 0x7F) + 1
            if head & 0x80:
                out += raw[pos:pos + size] * count
                pos += size
            else:
                out += raw[pos:pos + count * size]
                pos += count * size
        data = bytes(out[:n * size])
    if len(data) < n * size:
        raise TgaError("the picture ends before its last pixel")
    rgba = bytearray(n * 4)
    if grey:
        rgba[0::4] = rgba[1::4] = rgba[2::4] = data
        rgba[3::4] = b"\xff" * n
    else:  # stored blue, green, red (, alpha)
        rgba[0::4], rgba[1::4], rgba[2::4] = data[2::size], data[1::size], data[0::size]
        rgba[3::4] = data[3::size] if size == 4 else b"\xff" * n
    if desc & 0x10:
        raise TgaError("a .tga stored right to left isn't read")
    if not desc & 0x20:  # bottom row first: turn it over
        row = w * 4
        rgba = bytearray(b"".join(rgba[(h - 1 - y) * row:(h - y) * row] for y in range(h)))
    return w, h, bytes(rgba)
