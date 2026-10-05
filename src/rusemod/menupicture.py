"""A map's own pictures in the game's menus (map.toml `picture` and `wide_picture`, docs/MOD_FORMAT.md §8): any PNGs,
made into the two pictures a map's entry shows, each cut to its shape from the middle of its picture and scaled to
its size: the big one (640 x 360, a view of the map's land) from `picture`, and the wide one (680 x 200, the map as a
3D slab with its starting points) from `wide_picture`, else from `picture` too; as D-Day's own are (one level of DXT5,
packed). A new map gets its own picture files; a shipped map's are replaced, wherever its entries show them.

Every step is whole-number arithmetic, so every PC makes the same bytes from the same picture."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .dxt import encode_dxt5_block
from .png import PngError, read_png
from .tmst import make_tgv, zipo_pack

# (the map-list record's property, the picture's name, width, height): D-Day's are minimap_dday.png 640 x 360 and
# Minimap2.png 680 x 200
SIZES = (("Icone", "Minimap", 640, 360), ("Icone2", "Minimap2", 680, 200))
KEYS = ("picture", "wide_picture")   # map.toml's names for them, in SIZES' order
FORMAT = "DXT5_LIN"
LARGEST = 8192          # a picture's side, at most (a screenshot is 1920 or 3840 wide)
_NAME = re.compile(r"^[^\\/:*?\"<>|]+\.png$", re.I)


class PictureError(ValueError):
    pass


def picture_names(data: dict, where: str) -> tuple[str | None, str | None]:
    """A map.toml's `picture` and `wide_picture`: each the name of a PNG in the map's folder, or None."""
    names = []
    for key in KEYS:
        name = data.get(key)
        if name is not None and (not isinstance(name, str) or not _NAME.match(name)):
            raise PictureError(f'{where}: {key} must name a PNG picture in the map\'s folder, like "menu.png"')
        names.append(name)
    return names[0], names[1]


def start_dots_of(data: dict, where: str, wide: str | None) -> bool:
    """A map.toml's `start_dots` (true: the build draws a white dot on its wide picture on each place players start,
    where the map's starting points are once the mods' edits are in, rusemod.menudraw.dotted)."""
    dots = data.get("start_dots", False)
    if not isinstance(dots, bool):
        raise PictureError(f"{where}: start_dots must be true or false")
    if dots and not wide:
        # not a game rule: our build draws the dots on a 3D map picture of the mod's own
        raise PictureError(f"{where}: start_dots puts the starting points on the map's own wide picture: name it "
                           f'(wide_picture = "menu-wide.png"); the game\'s own have their dots drawn in')
    return dots


@dataclass
class MenuPictures:
    """A shipped map's pictures in the menus, changed by a mod (map.toml picture and/or wide_picture, no copy_of):
    the picture files its BATTLES entries show (or the entry `entry` names) are replaced."""
    picture: str | None = None
    wide_picture: str | None = None
    entry: str | None = None
    start_dots: bool = False      # the starting points drawn on the wide picture by the build
    picture_data: bytes | None = field(default=None, compare=False, repr=False)
    wide_picture_data: bytes | None = field(default=None, compare=False, repr=False)


def member_of(file_name: str) -> str | None:
    """The ZZ_Win.dat member a picture record's FileName stands for, or None: DataDir:\\Test\\map\\X\\Minimap.png is
    gen\\test\\map\\x\\minimap.tgv (so every shipped map's entry pictures, 2026-10-05)."""
    low = file_name.lower()
    if not low.startswith("datadir:\\") or not low.endswith(".png"):
        return None
    return "gen\\" + low[len("datadir:\\"):-len(".png")] + ".tgv"


def fitted(rgba: bytes, w: int, h: int, tw: int, th: int) -> bytearray:
    """The middle of a w x h RGBA picture, cut to tw:th and scaled to tw x th RGBA: each new pixel the mean of the
    pixels it covers, its colour weighted by their alpha, so see-through pixels (a 3D map's background) don't darken
    the edges they meet (a smaller picture: each new pixel the one it falls in). A picture with no see-through pixels
    comes out as the plain mean of its colours."""
    if w * th > h * tw:      # wider than the shape: its sides cut
        cw, ch = max(1, h * tw // th), h
    else:                    # taller: its top and bottom cut
        cw, ch = w, max(1, w * th // tw)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    cols = [(x0 + tx * cw // tw, max(x0 + tx * cw // tw + 1, x0 + (tx + 1) * cw // tw)) for tx in range(tw)]
    out = bytearray(tw * th * 4)
    stride = w * 4
    xa, xb = cols[0][0], cols[-1][1]
    for ty in range(th):
        r0 = y0 + ty * ch // th
        r1 = max(r0 + 1, y0 + (ty + 1) * ch // th)
        # the rows this line covers, summed column by column once (alpha, and each colour times its alpha), then
        # each pixel's columns added up
        sa, sr, sg, sb = [0] * w, [0] * w, [0] * w, [0] * w
        for r in range(r0, r1):
            row = rgba[r * stride:(r + 1) * stride]
            for x in range(xa, xb):
                i = x * 4
                a = row[i + 3]
                sa[x] += a
                sr[x] += row[i] * a
                sg[x] += row[i + 1] * a
                sb[x] += row[i + 2] * a
        n_rows = r1 - r0
        o = ty * tw * 4
        for c0, c1 in cols:
            n = n_rows * (c1 - c0)
            alpha = sum(sa[c0:c1])
            if alpha:
                out[o] = (sum(sr[c0:c1]) + alpha // 2) // alpha
                out[o + 1] = (sum(sg[c0:c1]) + alpha // 2) // alpha
                out[o + 2] = (sum(sb[c0:c1]) + alpha // 2) // alpha
            out[o + 3] = (alpha + n // 2) // n
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


def wide_rgba(png: bytes) -> bytearray:
    """A PNG as the wide picture's pixels (RGBA, 680 x 200), cut and scaled as pictures() does."""
    _prop, _stem, tw, th = SIZES[1]
    try:
        w, h, rgba = read_png(png)
    except PngError as exc:
        raise PictureError(str(exc)) from None
    if not (1 <= w <= LARGEST and 1 <= h <= LARGEST):
        raise PictureError(f"the picture is {w} x {h}; it can be at most {LARGEST} on a side")
    return fitted(rgba, w, h, tw, th)


def dotted_wide(png: bytes, starts: list[tuple[float, float]]) -> bytes:
    """The wide picture's file (TGV) from a PNG, with a white dot on each place players start (`starts` as map
    fractions, rusemod.menudraw.dotted): the build's, once the map's starting points are final (start_dots)."""
    from .menudraw import dotted
    _prop, _stem, tw, th = SIZES[1]
    return make_tgv(tw, th, FORMAT, [zipo_pack(dxt5(dotted(wide_rgba(png), starts), tw, th))])


def pictures(png: bytes | None, wide: bytes | None = None) -> dict[str, bytes]:
    """The menus' picture files (TGV) made from PNGs' bytes: {"Minimap": the big one's, from `png`; "Minimap2": the
    wide one's, from `wide`, else from `png`}. A picture with no PNG for it isn't made."""
    out = {}
    for _prop, stem, tw, th in SIZES:
        src = png if stem == "Minimap" else (wide if wide is not None else png)
        if src is None:
            continue
        try:
            w, h, rgba = read_png(src)
        except PngError as exc:
            raise PictureError(str(exc)) from None
        if not (1 <= w <= LARGEST and 1 <= h <= LARGEST):
            raise PictureError(f"the picture is {w} x {h}; it can be at most {LARGEST} on a side")
        out[stem] = make_tgv(tw, th, FORMAT, [zipo_pack(dxt5(fitted(rgba, w, h, tw, th), tw, th))])
    return out
