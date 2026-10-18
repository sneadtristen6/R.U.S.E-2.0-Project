"""Ground made whole from a heightmap (brush = "relief", MOD_FORMAT §8; the owner, 2026-10-17: "throw up a cool mountain
valley and then have it be, like, flat plains and then maybe some hills ... it has to be real to be looking in RUSE").

A relief stroke is a square (or a rectangle: `length`) turned along its dx, dy. The mod's heightmap,
files/terrain/<relief>.png (a greyscale PNG, 16-bit for every step), lies over it: its columns run along dx, dy, its
top row on the side to the left of that way (+y for a stroke along +x, as a map's picture is seen); a sample of 0 is
the height `level`, 65535 is `level2` (world z). Each ground point inside the square goes toward the heightmap's
height there by `weight`, out to the square's edge with no fall-off of the brush's own: a heightmap made by a terrain
tool (or the Studio's generator) is the ground, and its own rim meets the ground round it (a fall-off on top of a rim
that already fades squashed the mountains near it into steep walls the game threw into shadow, seen 10-17).

With files/terrain/<relief>-ground.png beside it (an RGB picture over the same square), that picture is laid on the
map's ground picture there, at every level of both tile sets, under the mods' own Map Paint (lay_pictures): the
ground's colour made with its shape, light, rock and gullies as R.U.S.E.'s own mountain maps have theirs (their
pictures carry what the ground mesh, a point every 10 m or so, can't).

Determinism: the heights come from + - * / and a square root on the stroke's own numbers, so every PC builds the same
bytes. The pictures are laid with numpy (the build already needs it for map assets): sums of the same numbers in the
same order, rounded half to even."""
from __future__ import annotations

import math
import struct
from pathlib import Path

TERRAIN = Path("files") / "terrain"  # the mod's heightmaps and their pictures


class ReliefError(ValueError):
    pass


def files_of(mod: Path, name: str) -> tuple[Path, Path]:
    """The heightmap and its picture for relief `name` in a mod's folder (the picture may not be there)."""
    return mod / TERRAIN / f"{name}.png", mod / TERRAIN / f"{name}-ground.png"


def read_grid(data: bytes) -> tuple:
    """A heightmap PNG -> the stroke's `grid`: (columns, rows, its 16-bit samples, 2 bytes each, high byte first,
    rows top to bottom)."""
    from .png import PngError, read_grey16
    try:
        w, h, samples = read_grey16(data)
    except (PngError, ValueError) as exc:
        raise ReliefError(str(exc)) from None
    if w < 2 or h < 2:
        raise ReliefError(f"a heightmap must be at least 2 x 2 samples, not {w} x {h}")
    return (w, h, samples)


def grid_range(grid: tuple) -> tuple[int, int]:
    """The lowest and highest sample of a heightmap (`grid`, read_grid's)."""
    import array
    a = array.array("H", grid[2])
    if array.array("H", b"\x01\x00")[0] == 1:   # (the samples are high byte first; this PC keeps the low first)
        a.byteswap()
    return min(a), max(a)


def _frame(s):
    """(dx, dy) as a unit way, the half-length along it and the half-width across it."""
    n = math.sqrt(s.dx * s.dx + s.dy * s.dy) or 1.0
    return s.dx / n, s.dy / n, (s.length or s.radius), s.radius


def place(s, x: float, y: float) -> tuple[float, float]:
    """Where (x, y) falls on the stroke's heightmap or picture: (u, v), 0..1 across its width (left to right) and
    down it (top to bottom); outside 0..1 off it."""
    ux, uy, along, across = _frame(s)
    ox, oy = x - s.x, y - s.y
    a = ox * ux + oy * uy        # along dx, dy
    b = oy * ux - ox * uy        # to the left of it (the picture's top side)
    return (a + along) / (2.0 * along), (across - b) / (2.0 * across)


def height_of(s, x: float, y: float) -> float:
    """The heightmap's height (world z) under (x, y): bilinear between its four nearest samples (a sample's middle at
    (column + 0.5) / columns), held at the edge's samples past it."""
    if not s.grid:
        raise ReliefError(f"the relief stroke's heightmap {s.relief!r} wasn't read")
    w, h, samples = s.grid
    u, v = place(s, x, y)
    fx, fy = u * w - 0.5, v * h - 0.5
    fx = 0.0 if fx < 0.0 else (w - 1.0 if fx > w - 1.0 else fx)
    fy = 0.0 if fy < 0.0 else (h - 1.0 if fy > h - 1.0 else fy)
    i, j = int(fx), int(fy)
    i1, j1 = (i + 1 if i + 1 < w else i), (j + 1 if j + 1 < h else j)
    tx, ty = fx - i, fy - j

    def at(c, r):
        return struct.unpack_from(">H", samples, 2 * (r * w + c))[0]
    top = at(i, j) + (at(i1, j) - at(i, j)) * tx
    bottom = at(i, j1) + (at(i1, j1) - at(i, j1)) * tx
    value = top + (bottom - top) * ty
    return s.level + (s.level2 - s.level) * (value / 65535.0)


# --- the picture ---------------------------------------------------------------------------------------------------
class Picture:
    """A relief's picture ready to lay: its mips (each half the last, averaged 2 x 2, as float RGB arrays [row,
    column, 3], rows from the top) and the map units one of the largest mip's pixels covers each way."""

    def __init__(self, stroke, width: int, height: int, rgb: bytes):
        from .numpy2 import np
        self.stroke = stroke
        _ux, _uy, along, across = _frame(stroke)
        self.size = (2.0 * along / width, 2.0 * across / height)
        px = np.frombuffer(rgb, dtype=np.uint8).reshape(height, width, -1)[:, :, :3].astype(np.float64)
        self.mips = [px]
        while min(px.shape[0], px.shape[1]) >= 2:
            h2, w2 = px.shape[0] // 2, px.shape[1] // 2
            px = (px[0:2 * h2:2, 0:2 * w2:2] + px[1:2 * h2:2, 0:2 * w2:2] + px[0:2 * h2:2, 1:2 * w2:2]
                  + px[1:2 * h2:2, 1:2 * w2:2]) * 0.25
            self.mips.append(px)

    def mip_for(self, pixel: float) -> int:
        """The mip a ground pixel `pixel` map units across reads: the smallest whose pixels are no bigger than it (the
        largest when even its pixels are bigger)."""
        m, size = 0, max(self.size)
        while m + 1 < len(self.mips) and size * 2.0 <= pixel * 1.0000001:
            m += 1
            size *= 2.0
        return m

    def colours(self, us, vs, pixel: float):
        """RGB [n, 3] at (us[n], vs[n]) (place's 0..1), bilinear in the mip for `pixel`."""
        from .numpy2 import np
        px = self.mips[self.mip_for(pixel)]
        h, w = px.shape[0], px.shape[1]
        fx = np.clip(us * w - 0.5, 0.0, w - 1.0)
        fy = np.clip(vs * h - 0.5, 0.0, h - 1.0)
        i, j = fx.astype(np.int64), fy.astype(np.int64)
        i1, j1 = np.minimum(i + 1, w - 1), np.minimum(j + 1, h - 1)
        tx, ty = (fx - i)[:, None], (fy - j)[:, None]
        top = px[j, i] + (px[j, i1] - px[j, i]) * tx
        bottom = px[j1, i] + (px[j1, i1] - px[j1, i]) * tx
        return top + (bottom - top) * ty


def _strength(s, xs, ys):
    """The stroke's fall-off at (xs[n], ys[n]) (brush.edge_weight over its square), and (u, v) there."""
    from .brush import HARD_EDGE
    from .numpy2 import np
    ux, uy, along, across = _frame(s)
    ox, oy = xs - s.x, ys - s.y
    a = ox * ux + oy * uy
    b = oy * ux - ox * uy
    m = np.maximum(np.abs(a) / along, np.abs(b) / across)
    if s.edge == "hard":
        t = np.clip((m - HARD_EDGE) / (1.0 - HARD_EDGE), 0.0, 1.0)
    else:   # the flat shape: full across the middle half
        t = np.clip((m - 0.5) * 2.0, 0.0, 1.0)
    p = np.where(m < 1.0, 1.0 - t * t * (3.0 - 2.0 * t), 0.0)
    return p * s.weight, (a + along) / (2.0 * along), (across - b) / (2.0 * across)


def lay_pictures(store, bounds, pictures: list, cache=None) -> dict[int, bytes]:
    """The `pictures` (Picture, in order) laid on every tile of `store` (over `bounds`, groundpaint.map_bounds) they
    reach, at every level: each pixel becomes its colour + (the picture's there - it) x the stroke's fall-off x weight,
    rounded half to even; only the 4 x 4 blocks that change are encoded again. {tile index: new record}."""
    from . import groundpaint as gp
    from .numpy2 import np
    from .paintnp import encoded, pixels_of
    out = {}
    boxes = [p.stroke.box() for p in pictures]   # x min, x max, y min, y max
    for tile in store.tiles:
        rx0, ry0, rx1, ry1 = gp._tile_rect(store, tile, bounds)
        near = [k for k, (bx0, bx1, by0, by1) in enumerate(boxes) if bx0 < rx1 and bx1 > rx0 and by0 < ry1 and by1 > ry0]
        if not near:
            continue
        w, h = gp._dims(store, tile)
        pw, ph = (rx1 - rx0) / w, (ry1 - ry0) / h
        nx, ny = w // 4, h // 4
        blocks = bytes(gp._blocks(store, tile, cache)[0])
        old = pixels_of(blocks, nx, ny)
        xs = rx0 + (np.arange(w) + 0.5) * pw
        ys = ry0 + (np.arange(h) + 0.5) * ph
        gx, gy = np.meshgrid(xs, ys)
        val = old.astype(np.float64).reshape(-1, 3)
        gx, gy = gx.ravel(), gy.ravel()
        for k in near:
            p = pictures[k]
            share, us, vs = _strength(p.stroke, gx, gy)
            on = share > 0.0
            if not on.any():
                continue
            col = p.colours(us[on], vs[on], max(pw, ph))
            val[on] = val[on] + (col - val[on]) * share[on][:, None]
        new = np.clip(np.rint(val), 0, 255).astype(np.uint8).reshape(h, w, 3)
        changed = (new != old).any(axis=2).reshape(ny, 4, nx, 4).any(axis=(1, 3))
        if not changed.any():
            continue
        which = np.flatnonzero(changed.ravel())
        rows = new.reshape(ny, 4, nx, 4, 3).transpose(0, 2, 1, 3, 4).reshape(ny * nx, 48)[which].tobytes()
        seen: dict = {}
        back = [seen.setdefault(rows[at:at + 48], len(seen)) for at in range(0, len(rows), 48)]
        made = encoded(list(seen))
        blk = np.frombuffer(blocks, dtype=np.uint8).reshape(ny * nx, 8).copy()
        blk[which] = np.frombuffer(made, dtype=np.uint8).reshape(len(seen), 8)[np.array(back, dtype=np.int64)]
        out[tile.index] = gp.zipo_tile(blk.tobytes(), w, h)
    return out


def paint_pictures(read, path_of, pictures: list, cache=None) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): lay_pictures on both tile sets of a map pack (`read(member)`: its files as the
    build has them; `path_of(member)`: its full path in the pack)."""
    from .groundpaint import LODS, PaintError, map_bounds
    from .tmst import Tmst
    mesh = read("output\\highdef.tms")
    if mesh is None:
        raise PaintError("the map has no ground mesh to lay the picture on")
    bounds = map_bounds(mesh)
    out, notes = {}, []
    for lod in LODS:
        index, chunk = read(f"output\\{lod}.tmst_pc"), read(f"output\\{lod}.tmst_chunk_pc")
        if index is None or chunk is None:
            continue
        store = Tmst(index, chunk)
        store.index_path, store.chunk_path = path_of(f"output\\{lod}.tmst_pc"), path_of(f"output\\{lod}.tmst_chunk_pc")
        tiles = lay_pictures(store, bounds, pictures, cache)
        if tiles:
            out.update(store.members(tiles))
        notes.append(f"{lod}: {len(tiles)} tile(s) with the relief's picture")
    return out, notes
