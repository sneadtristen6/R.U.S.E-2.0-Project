"""Brushes that are pictures (Map Paint plan step 5): a Colour, Texture, Tint or Stamp stroke with a `mask` lays as
much as the mask shows at each point, times its fall-off. A mask is a small picture of how much (SIZE x SIZE values
0-255, repeating), one of MASKS:

  noise     mottled: soft clouds of more and less
  splatter  scattered drops of different sizes
  ragged    whole, with a torn outline: here the mask doesn't let less through, it sets how far the stroke reaches
            (reach_scale: from RAG_IN of its radius where the mask is 0 to all of it where 255), so the middle stays
            whole and the edge tears (a mask laid over the whole dab only makes holes in it)
  tufts     many small dabs close together
  ridge     a net of thin lines

Each stroke reads its mask in its own frame (frame): centred on its middle, one repeat across its width (twice its
radius), turned along its direction (a square's dx, dy; a line's run; a round dab one of TURNS, picked by its middle,
so a drag of dabs doesn't show the same mask over and over). Between the mask's values, the four nearest weigh by
nearness (mask_at). The masks are made once from fixed seeds (make); every sum is + - x / or a square root, so every
PC lays the same bytes, and the Studio page is sent the masks themselves (StudioApi.brush_masks) to preview with the
same sums."""
from __future__ import annotations

import math
import random

SIZE = 64     # a mask's values across (and down): one repeat
MASKS = ("noise", "splatter", "ragged", "tufts", "ridge")
# a round dab's turnings: points on the circle with whole-number sides (3-4-5, 5-12-13, 8-15-17), so a turn is only
# x and +: every PC and the page turn alike
TURNS = ((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0),
         (3 / 5, 4 / 5), (4 / 5, -3 / 5), (-3 / 5, -4 / 5), (-4 / 5, 3 / 5),
         (5 / 13, 12 / 13), (12 / 13, -5 / 13), (-5 / 13, -12 / 13), (-12 / 13, 5 / 13),
         (8 / 17, 15 / 17), (15 / 17, -8 / 17), (-8 / 17, -15 / 17), (-15 / 17, 8 / 17))
MIX = 65521   # (groundtex.MIX: the dab's turning picked by the same kind of sums)
RAG_IN = 0.6  # ragged: the stroke reaches this share of its radius where the mask is 0
EDGE_MASKS = ("ragged",)  # the masks that set the reach (reach_scale) instead of letting less through (mask_at)

_made: dict[str, bytes] = {}


def _value_noise(rnd: random.Random, cells: int) -> list[float]:
    """SIZE x SIZE values 0..1, smooth: a `cells` x `cells` grid of random values (repeating) between which each
    point eases (3t^2 - 2t^3) from its four corners."""
    grid = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
    step = SIZE / cells
    out = []
    for j in range(SIZE):
        fy = (j + 0.5) / step - 0.5
        gy = math.floor(fy)
        ty = fy - gy
        ty = ty * ty * (3.0 - 2.0 * ty)
        for i in range(SIZE):
            fx = (i + 0.5) / step - 0.5
            gx = math.floor(fx)
            tx = fx - gx
            tx = tx * tx * (3.0 - 2.0 * tx)
            a, b = grid[gy % cells][gx % cells], grid[gy % cells][(gx + 1) % cells]
            c, d = grid[(gy + 1) % cells][gx % cells], grid[(gy + 1) % cells][(gx + 1) % cells]
            out.append((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
    return out


def _clouds(seed: int, sizes=((4, 0.55), (8, 0.3), (16, 0.15))) -> list[float]:
    """Value noise at three sizes (cells across, weight: 4, 8 and 16, the largest strongest), stretched to 0..1."""
    rnd = random.Random(seed)
    layers = [(_value_noise(rnd, cells), w) for cells, w in sizes]
    sums = [sum(v[k] * w for v, w in layers) for k in range(SIZE * SIZE)]
    lo, hi = min(sums), max(sums)
    return [(s - lo) / (hi - lo) for s in sums]


def _drops(seed: int, count: int, small: float, big: float) -> list[float]:
    """`count` round drops (radius small..big values, soft over one value), as much as the strongest drop over each
    point (repeating: a drop near an edge goes on across it)."""
    rnd = random.Random(seed)
    drops = [(rnd.random() * SIZE, rnd.random() * SIZE, small + (big - small) * rnd.random() ** 2) for _ in range(count)]
    out = [0.0] * (SIZE * SIZE)
    for x, y, r in drops:
        for j in range(math.floor(y - r - 1), math.ceil(y + r + 1) + 1):
            for i in range(math.floor(x - r - 1), math.ceil(x + r + 1) + 1):
                d = math.sqrt((i + 0.5 - x) ** 2 + (j + 0.5 - y) ** 2)
                v = min(1.0, max(0.0, r + 0.5 - d))
                k = (j % SIZE) * SIZE + i % SIZE
                if v > out[k]:
                    out[k] = v
    return out


def make(name: str) -> bytes:
    """Mask `name`'s SIZE x SIZE values 0..255, rows from the top (made once, from fixed seeds)."""
    if name in _made:
        return _made[name]
    if name not in MASKS:
        raise ValueError(f"no brush mask {name!r}: {', '.join(MASKS)}")
    if name == "noise":
        v = _clouds(11)
    elif name == "splatter":
        v = _drops(23, 46, 1.2, 7.0)
    elif name == "ragged":   # a reach (reach_scale): finer clouds, so the outline tears often
        v = _clouds(37, ((8, 0.5), (16, 0.3), (32, 0.2)))
    elif name == "tufts":
        clouds = _clouds(41)
        v = [max(d, 0.25 * c) for d, c in zip(_drops(43, 260, 0.8, 2.2), clouds)]
    else:  # ridge
        v = [(1.0 - abs(2.0 * c - 1.0)) ** 3 for c in _clouds(53)]
    _made[name] = bytes(int(x * 255.0 + 0.5) for x in v)
    return _made[name]


def frame(stroke) -> tuple[float, float, float, float, float]:
    """(x, y, ax, ay, span): where a stroke's mask is centred, the way its columns run (a unit length), and how far
    one repeat reaches across (twice the radius)."""
    shape = "square" if stroke.square else stroke.shape
    x, y = stroke.x, stroke.y
    if shape == "square":
        n = math.sqrt(stroke.dx * stroke.dx + stroke.dy * stroke.dy) or 1.0
        ax, ay = stroke.dx / n, stroke.dy / n
    elif shape == "line" and (stroke.x2 != stroke.x or stroke.y2 != stroke.y):
        sx, sy = stroke.x2 - stroke.x, stroke.y2 - stroke.y
        n = math.sqrt(sx * sx + sy * sy)
        ax, ay = sx / n, sy / n
        x, y = stroke.x + sx / 2, stroke.y + sy / 2
    else:   # a round dab: a turning picked by where it is
        h = (math.floor(stroke.x) * 92821 + math.floor(stroke.y) * 68917 + 29) % MIX
        h = (h * h + 12345) % MIX
        ax, ay = TURNS[h * len(TURNS) // MIX]
    return x, y, ax, ay, 2.0 * stroke.radius


def mask_at(stroke, px: float, py: float) -> float:
    """How much of the stroke its mask lets through at (px, py), 0..1: the mask in the stroke's frame, its four
    nearest values weighed by nearness."""
    data = make(stroke.mask)
    x, y, ax, ay, span = frame(stroke)
    ox, oy = px - x, py - y
    fu = ((ox * ax + oy * ay) / span + 0.5) * SIZE - 0.5
    fv = ((oy * ax - ox * ay) / span + 0.5) * SIZE - 0.5
    gu, gv = math.floor(fu), math.floor(fv)
    tu, tv = fu - gu, fv - gv
    i0, i1, j0, j1 = gu % SIZE, (gu + 1) % SIZE, (gv % SIZE) * SIZE, ((gv + 1) % SIZE) * SIZE
    return ((data[j0 + i0] * (1.0 - tu) + data[j0 + i1] * tu) * (1.0 - tv)
            + (data[j1 + i0] * (1.0 - tu) + data[j1 + i1] * tu) * tv) / 255.0


DITHER_MOST = 1.5 * 160.0   # a dithered edge speckles only on pixels this small at most (the finest level's: 160
                            # map units, 0.6 m); a coarser level mixes as before, as a speckle there would shimmer
                            # from afar (Map Paint plan step 6)


def dither_at(stroke, px: float, py: float, pw: float, ph: float) -> float:
    """A dithered stroke's threshold at the pixel centred at (px, py), pw x ph map units: a number in 0..1 from the
    pixel's place (its column and row on its level) and the stroke's own (where its middle is), so every build and
    the page pick alike; the pixel takes the stroke whole where its fall-off is above it, else not at all."""
    i, j = math.floor(px / pw), math.floor(py / ph)
    seed = (math.floor(stroke.x) * 31 + math.floor(stroke.y) * 17) % MIX
    h = (i * 92821 + j * 68917 + seed) % MIX
    h = (h * h + 12345) % MIX
    h = (h * h + 54321) % MIX
    return (h + 0.5) / MIX


def reach_scale(m: float) -> float:
    """An edge mask (EDGE_MASKS): what the footprint's t2 (its distance out, squared, as a share of the radius) is
    multiplied by where the mask is `m` (0..1): the stroke reaches RAG_IN + (1 - RAG_IN) m of its radius there."""
    s = RAG_IN + (1.0 - RAG_IN) * m
    return 1.0 / (s * s)
