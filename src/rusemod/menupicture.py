"""A new map's own pictures in the game's menus (map.toml `picture`, docs/MOD_FORMAT.md §8): any PNG, made into the two
pictures a map's entry shows, each cut to its shape from the middle of the picture and scaled to its size: the card
(640 x 360) and the wide one (680 x 200), as D-Day's own are (one level of DXT5, packed).

Every step is whole-number arithmetic, so every PC makes the same bytes from the same picture."""
from __future__ import annotations

from .dxt import encode_dxt5_block
from .png import PngError, read_png
from .tmst import make_tgv, zipo_pack

# (the map-list record's property, the picture's name, width, height): D-Day's are minimap_dday.png 640 x 360 and
# Minimap2.png 680 x 200
SIZES = (("Icone", "Minimap", 640, 360), ("Icone2", "Minimap2", 680, 200))
FORMAT = "DXT5_LIN"
LARGEST = 8192          # a picture's side, at most (a screenshot is 1920 or 3840 wide)


class PictureError(ValueError):
    pass


def fitted(rgba: bytes, w: int, h: int, tw: int, th: int) -> bytearray:
    """The middle of a w x h RGBA picture, cut to tw:th and scaled to tw x th RGBA: each new pixel the mean of the
    pixels it covers (a smaller picture: each new pixel the one it falls in)."""
    if w * th > h * tw:      # wider than the shape: its sides cut
        cw, ch = max(1, h * tw // th), h
    else:                    # taller: its top and bottom cut
        cw, ch = w, max(1, w * th // tw)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    cols = [(x0 + tx * cw // tw, max(x0 + tx * cw // tw + 1, x0 + (tx + 1) * cw // tw)) for tx in range(tw)]
    out = bytearray(tw * th * 4)
    stride = w * 4
    for ty in range(th):
        r0 = y0 + ty * ch // th
        r1 = max(r0 + 1, y0 + (ty + 1) * ch // th)
        # the rows this line covers, summed column by column once, then each pixel's columns added up
        sums = [0] * (w * 4)
        for r in range(r0, r1):
            row = rgba[r * stride:(r + 1) * stride]
            for i in range(cols[0][0] * 4, cols[-1][1] * 4):
                sums[i] += row[i]
        n_rows = r1 - r0
        o = ty * tw * 4
        for c0, c1 in cols:
            n = n_rows * (c1 - c0)
            for k in range(4):
                total = sum(sums[i * 4 + k] for i in range(c0, c1))
                out[o + k] = (total + n // 2) // n
            o += 4
    return out


def dxt5(rgba: bytes | bytearray, w: int, h: int) -> bytes:
    """A w x h RGBA picture (sides multiples of 4) as DXT5 blocks, row by row."""
    out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            pixels, alphas = [], []
            for y in range(by, by + 4):
                for x in range(bx, bx + 4):
                    i = (y * w + x) * 4
                    pixels.append((rgba[i], rgba[i + 1], rgba[i + 2]))
                    alphas.append(rgba[i + 3])
            out += encode_dxt5_block(pixels, alphas)
    return bytes(out)


def check(png: bytes) -> tuple[int, int]:
    """A PNG's width and height, checked the way pictures() takes it (rusemod.png's kinds, not interlaced, at most
    LARGEST a side), without reading its pixels: for the Studio, when a picture is picked."""
    import struct
    from .png import CHANNELS, SIGNATURE
    if png[:8] != SIGNATURE or png[12:16] != b"IHDR" or len(png) < 29:
        raise PictureError("not a PNG picture")
    w, h, depth, ctype, _comp, _filt, interlace = struct.unpack(">IIBBBBB", png[16:29])
    if interlace:
        raise PictureError("interlaced PNGs aren't read: save it without interlacing")
    if ctype not in CHANNELS or depth not in (8, 16) or (ctype == 3 and depth != 8):
        raise PictureError(f"PNG of colour type {ctype} at {depth} bits isn't read: save it as 8-bit RGB or RGBA")
    if not (1 <= w <= LARGEST and 1 <= h <= LARGEST):
        raise PictureError(f"the picture is {w} x {h}; it can be at most {LARGEST} on a side")
    return w, h


def pictures(png: bytes) -> dict[str, bytes]:
    """{"Minimap": the card's picture file (TGV), "Minimap2": the wide one's} from a PNG's bytes."""
    try:
        w, h, rgba = read_png(png)
    except PngError as exc:
        raise PictureError(str(exc)) from None
    if not (1 <= w <= LARGEST and 1 <= h <= LARGEST):
        raise PictureError(f"the picture is {w} x {h}; it can be at most {LARGEST} on a side")
    return {stem: make_tgv(tw, th, FORMAT, [zipo_pack(dxt5(fitted(rgba, w, h, tw, th), tw, th))])
            for _prop, stem, tw, th in SIZES}
