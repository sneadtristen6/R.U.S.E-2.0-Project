"""The two apps' icons as Windows .ico files.

Since 2026-10-01 they are the owner's artwork, in installers/art: RUSE Launcher a bare-metal WWII fighter climbing
through blue clouds, RUSE Studio the war-room table (the map, its units and plans, a hand drawing a zone). Each
<app>.ico holds 16 to 256 px pictures (PNG; the 16, 24 and 32 px ones zoomed in on the subject so it reads that small)
and <app>.png is the 256 px one. Without them (an older checkout), the icons are drawn here with nothing but the
standard library: a gold Play triangle and a gold pencil on a dark tile.

  py -3 installers/icons.py OUT_DIR        writes OUT_DIR/launcher.ico, OUT_DIR/studio.ico (and .png previews)
"""
from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 256)
TILE, EDGE, GOLD, GOLD_DARK = (29, 34, 38), (200, 166, 75), (214, 180, 88), (143, 117, 48)


def _rounded(x: float, y: float, r: float) -> bool:
    """Inside the rounded square that fills the unit square (corner radius r)."""
    cx, cy = min(max(x, r), 1 - r), min(max(y, r), 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _in_poly(x: float, y: float, pts) -> bool:
    inside, j = False, len(pts) - 1
    for i in range(len(pts)):
        (xi, yi), (xj, yj) = pts[i], pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _along(u: float, v: float):
    """A point on the tile's rising diagonal: u along it (towards the top right), v across it."""
    s = math.sqrt(0.5)
    return 0.5 + (u + v) * s, 0.5 + (-u + v) * s


PLAY = [(0.38, 0.27), (0.38, 0.73), (0.77, 0.50)]
PENCIL_BODY = [_along(-0.12, -0.085), _along(0.26, -0.085), _along(0.26, 0.085), _along(-0.12, 0.085)]
PENCIL_TIP = [_along(-0.12, -0.085), _along(-0.12, 0.085), _along(-0.30, 0.0)]
PENCIL_END = [_along(0.28, -0.085), _along(0.36, -0.085), _along(0.36, 0.085), _along(0.28, 0.085)]


def _shape(app: str, x: float, y: float):
    """The colour at a point of the unit square, or None outside the tile."""
    if not _rounded(x, y, 0.2):
        return None
    if not _rounded((x - 0.045) / 0.91, (y - 0.045) / 0.91, 0.17):
        return EDGE
    if app == "launcher":
        return GOLD if _in_poly(x, y, PLAY) else TILE
    if _in_poly(x, y, PENCIL_BODY) or _in_poly(x, y, PENCIL_TIP):
        return GOLD
    if _in_poly(x, y, PENCIL_END):
        return GOLD_DARK
    return TILE


def draw(app: str, size: int, samples: int = 4) -> list[list[tuple]]:
    """RGBA rows, smoothed by sampling each pixel samples x samples times."""
    rows = []
    for py in range(size):
        row = []
        for px in range(size):
            r = g = b = a = 0
            for sy in range(samples):
                for sx in range(samples):
                    c = _shape(app, (px + (sx + 0.5) / samples) / size, (py + (sy + 0.5) / samples) / size)
                    if c:
                        r, g, b, a = r + c[0], g + c[1], b + c[2], a + 1
            n = samples * samples
            row.append((r // a, g // a, b // a, 255 * a // n) if a else (0, 0, 0, 0))
        rows.append(row)
    return rows


def png(rows) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = b"".join(b"\0" + bytes(v for px in row for v in px) for row in rows)
    head = struct.pack(">IIBBBBB", len(rows[0]), len(rows), 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def bitmap(rows) -> bytes:
    """A classic icon picture: a 32-bit bitmap (rows bottom-up, blue-green-red-alpha) plus a 1-bit mask."""
    size = len(rows)
    head = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    pixels = b"".join(bytes((b, g, r, a)) for row in reversed(rows) for r, g, b, a in row)
    stride = (size + 31) // 32 * 4
    mask = bytearray()
    for row in reversed(rows):
        line = bytearray(stride)
        for x, (_r, _g, _b, a) in enumerate(row):
            if a == 0:
                line[x // 8] |= 0x80 >> (x % 8)
        mask += line
    return head + pixels + bytes(mask)


def ico(pictures: list[tuple[int, bytes]]) -> bytes:
    out = struct.pack("<HHH", 0, 1, len(pictures))
    offset = 6 + 16 * len(pictures)
    for size, data in pictures:
        side = 0 if size >= 256 else size
        out += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return out + b"".join(data for _size, data in pictures)


ART = Path(__file__).resolve().parent / "art"  # the owner's artwork (2026-10-01): <app>.ico (16-256 px) and <app>.png


def make(app: str) -> tuple[bytes, bytes]:
    """(the .ico file, a 256 px PNG preview): the app's artwork when installers/art has it, else drawn here."""
    if (ART / f"{app}.ico").is_file() and (ART / f"{app}.png").is_file():
        return (ART / f"{app}.ico").read_bytes(), (ART / f"{app}.png").read_bytes()
    pictures, preview = [], b""
    for size in SIZES:
        rows = draw(app, size, samples=4 if size >= 64 else 8)
        data = png(rows) if size >= 256 else bitmap(rows)
        if size >= 256:
            preview = data
        pictures.append((size, data))
    return ico(pictures), preview


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0] if argv else "build/icons")
    out.mkdir(parents=True, exist_ok=True)
    for app in ("launcher", "studio"):
        icon, preview = make(app)
        (out / f"{app}.ico").write_bytes(icon)
        (out / f"{app}.png").write_bytes(preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())
