"""The 3D map picture a blank map's menus show (map.toml wide_picture, docs/MOD_FORMAT.md §8): the map as a slab seen
from its front edge, the way the game's own are drawn (680 x 200, the map's top a trapezoid narrowing to its back
edge, its soil along the front, everything round it see-through): the sea all over for Blank Ocean, plain grass for
Blank Terrain (rusemod.presets), so it fits any map a blank start is made from.

The white dot on each place players start isn't part of the picture: the build draws them (dotted, map.toml
start_dots) where the map's starting points are once the mods' edits are in, and the Studio's preview the same way,
so moving a starting point moves its dot (the owner, 2026-10-05: the dots "should be ... coded to where that's
actually the spawn point of those players").

North is the slab's back edge, as in the game's own: a map's world y grows toward the south, so a point's depth
into the picture is y / the map's depth, and x / its width goes left to right."""
from __future__ import annotations

import math

WIDTH, HEIGHT = 680, 200
BACK_Y, FRONT_Y, SOIL = 10.0, 170.0, 20.0    # the slab's back edge, its front edge, its soil below that (pixels)
BACK_W, FRONT_W, MIDDLE = 349.0, 580.0, 340.0  # its back and front widths, about the picture's middle; D-Day's own
SAME_PLACE = 0.01            # starting points nearer than this (of the map's width and depth) are one dot
DOT_RX, DOT_RY = 5.0, 2.6    # a dot's half width and half height (pixels), as the game's own
KINDS = ("ocean", "land")
_RATIO = FRONT_W / BACK_W    # how much nearer the front edge is than the back: the perspective


def _hash(i: int, j: int, seed: int) -> float:
    h = (i * 374761393 + j * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


class _Noise:
    """Smooth value noise over a 64 x 64 lattice that repeats, several octaves summed (0..1)."""
    SIDE = 64

    def __init__(self, seed: int, octaves: int = 4):
        n = self.SIDE
        self.octaves = octaves
        self.grid = [[_hash(i, j, seed) for i in range(n)] for j in range(n)]

    def at(self, x: float, y: float) -> float:
        n, grid = self.SIDE, self.grid
        total, amp, norm = 0.0, 1.0, 0.0
        for k in range(self.octaves):
            xi, yi = math.floor(x), math.floor(y)
            fx, fy = x - xi, y - yi
            sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
            i0, j0 = int(xi) % n, int(yi) % n
            i1, j1 = (i0 + 1) % n, (j0 + 1) % n
            top = grid[j0][i0] + (grid[j0][i1] - grid[j0][i0]) * sx
            bottom = grid[j1][i0] + (grid[j1][i1] - grid[j1][i0]) * sx
            total += amp * (top + (bottom - top) * sy)
            norm += amp
            amp *= 0.5
            x, y = x * 2.0 + 17.3, y * 2.0 + 31.7
        return total / norm


def _lerp(a, b, t: float) -> tuple:
    return tuple(p + (q - p) * t for p, q in zip(a, b))


def to_picture(u: float, v: float) -> tuple[float, float]:
    """Where a point of the map's top (u: 0 west .. 1 east, v: 0 north .. 1 south) is in the picture (x, y)."""
    t = v / (_RATIO * (1.0 - v) + v) if v > 0 else 0.0
    width = BACK_W + t * (FRONT_W - BACK_W)
    return MIDDLE + (u - 0.5) * width, BACK_Y + t * (FRONT_Y - BACK_Y)


def _top_at(x: float, y: float) -> tuple[float, float] | None:
    """The map point (u, v) a picture point on the slab's top shows, or None when it's off the top."""
    if not BACK_Y <= y <= FRONT_Y:
        return None
    t = (y - BACK_Y) / (FRONT_Y - BACK_Y)
    u = 0.5 + (x - MIDDLE) / (BACK_W + t * (FRONT_W - BACK_W))
    if not 0.0 <= u <= 1.0:
        return None
    return u, t / (t + (1.0 - t) / _RATIO)


class _Painter:
    def __init__(self, kind: str):
        self.kind = kind
        self.big, self.fine, self.soil = _Noise(11, 4), _Noise(23, 3), _Noise(37, 3)

    def top(self, u: float, v: float, edge: float) -> tuple:
        """The colour of the map's top at (u, v); `edge`: how near the back edge (1 on it, 0 a few pixels in)."""
        big, fine = self.big.at(u * 9.0, v * 6.0), self.fine.at(u * 70.0, v * 45.0)
        if self.kind == "ocean":
            c = _lerp((22, 62, 84), (9, 41, 58), v)            # lighter far off, as the game's own sea
            k = 0.9 + 0.16 * big + 0.08 * (fine - 0.5)
            c = tuple(min(255.0, p * k) for p in c)
            c = _lerp(c, (70, 104, 122), 0.18 * (1.0 - v) ** 4)  # the sky's sheen toward the back
        else:
            c = _lerp((88, 106, 50), (104, 113, 56), big)      # plain grass, a little patchy
            c = _lerp(c, (70, 84, 38), max(0.0, self.fine.at(u * 18.0 + 5.0, v * 12.0) - 0.62) * 1.6)
            k = 0.94 + 0.12 * (fine - 0.5)
            c = tuple(min(255.0, p * k) for p in c)
        return _lerp(c, (150, 170, 175) if self.kind == "ocean" else (140, 150, 105), 0.45 * edge)

    def front(self, x: float, y: float) -> tuple:
        """The colour of the slab's front: soil in thin layers (under a band of sea for the ocean)."""
        depth = y - FRONT_Y
        if self.kind == "ocean" and depth < 3.0:
            return (12, 44, 60) if depth > 0.8 else (40, 82, 100)
        layer = self.soil.at(x * 0.012, depth * 0.55)
        grain = self.fine.at(x * 0.6, depth * 0.9)
        k = 0.72 + 0.5 * layer + 0.14 * (grain - 0.5)
        k *= 1.0 - 0.25 * depth / SOIL                       # darker toward the bottom
        return tuple(min(255.0, p * k) for p in (56, 43, 28))

    def at(self, x: float, y: float) -> tuple | None:
        """RGBA at a picture point, or None when the slab isn't there."""
        top = _top_at(x, y)
        if top is not None:
            return self.top(top[0], top[1], max(0.0, 1.0 - (y - BACK_Y) / 1.5)) + (255,)
        if FRONT_Y < y <= FRONT_Y + SOIL and abs(x - MIDDLE) <= FRONT_W / 2:
            return self.front(x, y) + (255,)
        return None


def _region(x: float, y: float) -> int:
    if _top_at(x, y) is not None:
        return 1
    if FRONT_Y < y <= FRONT_Y + SOIL and abs(x - MIDDLE) <= FRONT_W / 2:
        return 2
    return 0


def slab(kind: str, starts: list[tuple[float, float]] = ()) -> bytes:
    """The 3D map picture as RGBA (WIDTH x HEIGHT, rows top to bottom): `kind` "ocean" or "land"; with `starts`
    (starting points as map fractions: u 0 west .. 1 east, v 0 north .. 1 south) their dots on it too (dotted)."""
    if kind not in KINDS:
        raise ValueError(f"no slab kind {kind!r} ({', '.join(KINDS)})")
    paint = _Painter(kind)
    out = bytearray(WIDTH * HEIGHT * 4)
    for py in range(HEIGHT):
        for px in range(WIDTH):
            corners = {_region(px + dx, py + dy) for dx in (0.0, 1.0) for dy in (0.0, 1.0)}
            if corners == {0}:
                continue
            if len(corners) == 1:              # wholly on one face: its middle
                rgba = paint.at(px + 0.5, py + 0.5)
                if rgba is None:
                    continue
                o = (py * WIDTH + px) * 4
                out[o:o + 4] = bytes(int(c + 0.5) for c in rgba)
                continue
            acc, n = [0.0, 0.0, 0.0, 0.0], 0   # an edge: 4 x 4 samples
            for sy in range(4):
                for sx in range(4):
                    n += 1
                    rgba = paint.at(px + (sx + 0.5) / 4, py + (sy + 0.5) / 4)
                    if rgba is not None:
                        for k in range(3):
                            acc[k] += rgba[k]
                        acc[3] += 1.0
            if acc[3]:
                o = (py * WIDTH + px) * 4
                out[o:o + 4] = bytes((int(acc[0] / acc[3] + 0.5), int(acc[1] / acc[3] + 0.5),
                                      int(acc[2] / acc[3] + 0.5), int(255 * acc[3] / n + 0.5)))
    return bytes(dotted(out, starts))


def places(bounds: tuple, points) -> list[tuple[float, float]]:
    """Map points (x, y, ...) as map fractions (u, v) of the ground's bounds (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = bounds
    return [((p[0] - x0) / (x1 - x0), (p[1] - y0) / (y1 - y0)) for p in points]


def dotted(rgba: bytes | bytearray, starts: list[tuple[float, float]]) -> bytearray:
    """A 3D map picture (RGBA, WIDTH x HEIGHT) with a white dot on each place players start (`starts` as map
    fractions; points nearer than SAME_PLACE are one dot)."""
    if len(rgba) != WIDTH * HEIGHT * 4:
        raise ValueError(f"a 3D map picture is {WIDTH} x {HEIGHT}")
    out = bytearray(rgba)
    for cx, cy in dots(starts):
        _dot(out, cx, cy)
    return out


def dots(starts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Where the white dots go (picture x, y): one per place players start (points nearer than SAME_PLACE are one),
    off-map points left out."""
    places: list[tuple[float, float]] = []
    for u, v in starts:
        if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
            continue
        if any(abs(u - a) < SAME_PLACE and abs(v - b) < SAME_PLACE for a, b in places):
            continue
        places.append((u, v))
    return [to_picture(u, v) for u, v in places]


def _dot(out: bytearray, cx: float, cy: float) -> None:
    for py in range(int(cy - DOT_RY) - 1, int(cy + DOT_RY) + 2):
        for px in range(int(cx - DOT_RX) - 1, int(cx + DOT_RX) + 2):
            if not (0 <= px < WIDTH and 0 <= py < HEIGHT):
                continue
            inside = sum(1 for sy in range(4) for sx in range(4)
                         if ((px + (sx + 0.5) / 4 - cx) / DOT_RX) ** 2 + ((py + (sy + 0.5) / 4 - cy) / DOT_RY) ** 2 <= 1)
            if not inside:
                continue
            a = inside / 16
            o = (py * WIDTH + px) * 4
            for k in range(3):
                out[o + k] = int(out[o + k] * (1 - a) + 255 * a + 0.5)
            out[o + 3] = max(out[o + 3], int(255 * a + 0.5))


def slab_png(kind: str, starts: list[tuple[float, float]] = ()) -> bytes:
    """slab() as a PNG's bytes."""
    from .dxt import png_bytes
    return png_bytes(slab(kind, starts), WIDTH, HEIGHT, 4)


FRAME = (132, 134, 132)       # the big pictures' grey edge, 3 pixels wide, as the game's own
FRAME_SIDE = 3
FRAME_SHADE = (0.3, 0.45, 0.6, 0.75, 0.88, 0.96)  # the picture darkened just inside it, pixel by pixel inward


def framed(rgba: bytes | bytearray, w: int, h: int) -> bytearray:
    """A big picture (RGBA, w x h) with the game's own frame: a grey edge, and the picture shaded just inside it."""
    out = bytearray(rgba)
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            if d >= FRAME_SIDE + len(FRAME_SHADE):
                continue
            o = (y * w + x) * 4
            if d < FRAME_SIDE:
                out[o:o + 4] = bytes(FRAME + (255,))
            else:
                k = FRAME_SHADE[d - FRAME_SIDE]
                for c in range(3):
                    out[o + c] = int(out[o + c] * k + 0.5)
                out[o + 3] = 255
    return out
