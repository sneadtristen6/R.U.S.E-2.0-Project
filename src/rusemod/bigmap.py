"""Bigger (or smaller) maps: a blank new map grown to the size its map.toml asks (size = [cells across, cells down]).

A map's ground is a grid of cells, 327,680 map units (1.26 km) a side; the far view draws them two by two, so every
shipped map is an even number of cells each way (2 x 2 Commander's maps up to D-Day's 12 x 8). A new map that starts
blank (map.toml blank) can be any even size from 2 x 2 to MOST x MOST: the build grows the copied map's size-bound
files to it before any other step reads them, flat and empty, and the steps after (the ground drawn from its strokes,
the paint, the scenery, the movement, the sectors) work on the bigger map as on any other.

What is made at the new size (each the copied map's own file, made again):
  the map pack
    - highdef.tms / lowdef.tms: flat meshes on the new grid (groundgen.make_mesh), the edge's skirt following it;
    - occlusioninfo_terrainonly.kdt / occlusioninfo_camera.kdt: the units' ground and the camera's floor over the
      new box, cut into parts of about PART_TARGET triangles each (the shipped maps' parts hold up to 1,488);
    - highdef / lowdef .tmst: a tile for every place of the bigger grid (the copied map's plain tile);
    - terrain.png / terrainwithunit.png: the far views' whole-map pictures, at most GLOBAL_MOST pixels a side;
    - riverindirectionsurface.tgv: the water's lookup over the new size, all dry;
    - output.sdb: the level-build state, all land, square over the longer side as the shipped ones are;
  mapinfo.win (DataMap_Win.dat)
    - the size in its header; both movement graphs a lattice of overlapping circles over the whole map (open
      everywhere, at most LATTICE_MOST a side: a circle's list start is 16-bit); the cover grid over the map, no
      cover; the AI grid, open;
  the map's settings (ZZ_GladPatchableWin.dat)
    - MapConstante: the size fields, the camera's flat floor, the cloud layer's height;
    - its own mapTerrain: the meshes' cell grids, the water's, and the static level build's squares at most
      STATIC_MOST a side (the game orders them on a Hilbert curve of order ceil(sqrt(squares a side)): 256 a side
      asked for 4.3 billion entries and crashed the game on loading);
    - its own HQLoader: the HQ room out of sight on a map bigger than the copied one (its table is D-Day's; the
      owner's pick on the 80 km test, "get rid of the whole room"), the sky kept; its ClusterMap loads both.

Its two SDB trees always start with a node and reach the shipped trees' depth (a one-leaf root crashed the game when a
building was placed; a shallow tree would have the cover and water painters work on 20 km squares).
Proven in the game on an 80.7 km map (64 x 64 cells, 2026-10-17): it loads and plays, units, buildings and ruses
work in every sector, with the room out and the clouds over the camera."""
from __future__ import annotations

import hashlib
import math
import struct
import zlib
from collections import Counter

CASE = 327680.0            # map units a cell is across, on every map
MOST = 128                 # cells a side at most (an 80.7 km map, 64 x 64, played; past it not tried)
PART_TARGET = 1100.0       # triangles a kd-tree part aims at (the shipped maps' parts: 1,488 at most)
GLOBAL_MOST = 2048         # the far views' whole-map pictures at most this many pixels a side (mapTerrain)
LATTICE_MOST = 128         # movement circles a side at most (16-bit list starts: the links listed twice < 65,536)
LATTICE_PITCH = 140 * 320.0   # the movement circles' spacing aimed at (172 m), wider on maps past LATTICE_MOST
GRID_CELL_MOST = 1600.0    # map units an SDB cell is across at most (the shipped trees: 500-1,600)
GRID_R_MOST = 16384        # an SDB tree's cells a side at most (sdb.tree_grid_R's cap)
AI_CELL = 26000.0          # map units an AI grid cell is across (rusemod.aigrid)
STATIC_MOST = 64           # the static level build's squares a side at most (Hilbert order 8: played)
FLOOR_REACH = 1.5          # the camera's flat floor reaches this many map sizes (at least D-Day's 5,000,000)
ROOM_AWAY = 1.0e8          # how far under the map the HQ room's meshes go (twice the far clipping)
HQ_ROOM = ("HQLoader",)    # the copied map's settings file that places the room (Patchable\map\<map>\HQLoader)


class BigMapError(ValueError):
    """A size that can't be made, said for the modder."""


def check_size(size, where: str = "map.toml") -> tuple[int, int]:
    """map.toml's size = [cells across, cells down]: two even whole numbers from 2 to MOST."""
    if (not isinstance(size, (list, tuple)) or len(size) != 2
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in size)):
        raise BigMapError(f"{where}: size must be two whole numbers, the map's cells across and down, like "
                          f"size = [24, 16] (a cell is 1.26 km)")
    w, h = size
    for v in (w, h):
        if v < 2 or v > MOST:
            raise BigMapError(f"{where}: size {w} x {h}: each side is 2 to {MOST} cells (2.5 to {MOST * 1.26:.0f} km)")
        if v % 2:
            raise BigMapError(f"{where}: size {w} x {h}: each side must be an even number of cells (the far view "
                              f"draws them two by two, as on every shipped map)")
    return w, h


def per_cell(cells: int) -> tuple[int, int]:
    """The close-up and far meshes' squares a cell each way for a map of `cells` cells: groundgen's own (a point every
    10 m close up) up to 256 cells (16 x 16), then 32 and 16 (the 80 km map's: 1.4 million triangles close up)."""
    from . import groundgen as G
    return (G.PER_CELL_NEAR, G.PER_CELL_FAR) if cells <= 256 else (32, 16)


# --- the map pack -----------------------------------------------------------------------------------------------
def grow_mesh(raw: bytes, cx: int, cy: int, near: bool, ground: float, water: float) -> tuple[bytes, dict]:
    """A mesh (close-up or far) grown to `cx` x `cy` of its cells, flat at `ground` with the water at `water`."""
    from . import groundgen as G
    from .tms import Tms
    t = Tms(raw)
    sx, sy = cx / t.grid_w, cy / t.grid_h
    data = bytearray(t.skirt_data)
    for _voff, _count, boff, _poff, nparts in t._skirt_layout():
        for p in range(nparts):   # each skirt part's box stretched to the new edge (its points are in the file's
            x0, y0, z0, x1, y1, z1 = struct.unpack_from("<6f", data, boff + 24 * p)   # steps, so they follow it)
            struct.pack_into("<6f", data, boff + 24 * p, x0 * sx, y0 * sy, z0, x1 * sx, y1 * sy, z1)
    t.skirt_data = bytes(data)
    t.grid_w, t.grid_h = cx, cy
    t.bounds[3], t.bounds[4] = cx * t.cell_w, cy * t.cell_h
    t.cells = [None] * (cx * cy)
    close, far = per_cell(cx * cy if near else 4 * cx * cy)
    t.cells, info = G.make_mesh(t, lambda x, y: ground, lambda x, y: water, close if near else far, set(), 8)
    info["skirt"] = G.fit_skirt(t, lambda x, y: ground, lambda x, y: water)
    out = t.to_bytes()
    Tms(out)   # reads back
    return out, info


def mesh_triangles(mesh, camera: bool):
    """A mesh's world triangles (numpy, n x 3 points x 3) as a kd-tree holds them: the camera's floor at the ground
    or the water, whichever is higher, plus groundgen.CAMERA_OVER."""
    import numpy as np
    from . import groundgen as G
    (x0, y0, z0, x1, y1, z1), q = mesh.bounds, 32767.0
    out = []
    for c in mesh.cells:
        p = np.asarray(c.positions(), dtype=np.float64)
        w = np.empty((len(p), 3))
        w[:, 0] = x0 + p[:, 0] * (x1 - x0) / q
        w[:, 1] = y0 + p[:, 1] * (y1 - y0) / q
        h = np.maximum(p[:, 2], p[:, 3]) if camera else p[:, 2]
        w[:, 2] = z0 + h * (z1 - z0) / q + (G.CAMERA_OVER if camera else 0.0)
        out.append(w[np.asarray(c.triangles(0), dtype=np.int64)].reshape(-1, 3, 3))
    return np.concatenate(out)


def parts_tree(tris, box: tuple, target: float = PART_TARGET):
    """A kd-tree's MainNode over `tris` in `box` (x0, y0, x1, y1): split at the triangles' middles across the longer
    side, each side as many parts as it holds, until a part has about `target` triangles (a triangle a split's line
    crosses goes to both). Returns (the tree, each leaf's triangle numbers in leaf order)."""
    import numpy as np
    bx0, bx1 = tris[:, :, 0].min(1), tris[:, :, 0].max(1)
    by0, by1 = tris[:, :, 1].min(1), tris[:, :, 1].max(1)
    mid = ((bx0 + bx1) / 2, (by0 + by1) / 2)
    lo_of, hi_of = (bx0, by0), (bx1, by1)
    leaves = []

    def node(ids, x0, y0, x1, y1):
        parts = math.ceil(len(ids) / target)
        if parts <= 1:
            leaves.append(ids)
            return ("leaf",)
        axis = 0 if x1 - x0 >= y1 - y0 else 1
        k = len(ids) * (parts // 2) // parts
        v = float(np.partition(mid[axis][ids], k)[k])
        hi = ids[hi_of[axis][ids] >= v]
        lo = ids[lo_of[axis][ids] < v]
        if axis == 0:
            return ("split", 0, v, node(hi, v, y0, x1, y1), node(lo, x0, y0, v, y1))
        return ("split", 1, v, node(hi, x0, v, x1, y1), node(lo, x0, y0, x1, v))
    return node(np.arange(len(tris)), *box), leaves


def fill_parts(k, tris, leaves: list) -> list:
    """Part s of `k` filled with the triangles leaves[s]: points in the tree's own steps, shared within a part, normals
    from the faces, the part's own tree built again (groundgen._fill_tree's way). Returns each part's count."""
    import numpy as np
    from . import kdt_edit
    lo, hi = np.asarray(k.bounds_min), np.asarray(k.bounds_max)
    held = []
    for s, ids in enumerate(leaves):
        t = tris[ids]
        q = np.clip(np.rint((t - lo) * 32767.0 / (hi - lo)), 0, 32767).astype(np.int64)
        pts, inv = np.unique(q.reshape(-1, 3), axis=0, return_inverse=True)
        inv = inv.reshape(-1)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n[n[:, 2] < 0] *= -1
        acc = np.zeros((len(pts), 3))
        for j in range(3):
            np.add.at(acc, inv.reshape(-1, 3)[:, j], n)
        acc /= np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
        pos = [tuple(int(c) for c in p) for p in pts]
        flat = [int(i) for i in inv]
        k.set_mesh(s, pos, flat, [tuple(float(c) for c in a) for a in acc])
        kdt_edit.rebuild(k, s, pos, [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)])
        held.append(len(ids))
    kdt_edit.widen_main(k, range(len(k.subtrees)))
    k.triangle_count = int(sum(held))
    return held


def balanced_tree(raw: bytes, mesh, camera: bool, size: tuple) -> tuple[bytes, str]:
    """A kd-tree (the units' ground, or the camera's floor with `camera`) made over `mesh` and the map's `size` (x, y
    map units): its box the map's (the copied tree's margin past the edge kept), a new MainNode of balanced parts
    (parts_tree; each part a clip on its height, as most of D-Day's are), each part filled (fill_parts)."""
    from dataclasses import replace as copy
    from .kdt import Kdt
    k = Kdt(raw)
    tris = mesh_triangles(mesh, camera)
    margin = -k.bounds_min[0]   # (D-Day's camera floor reaches 175,000 past the map; its units' ground 0)
    k.bounds_min = (-margin, -margin, min(k.bounds_min[2], float(tris[:, :, 2].min())))
    k.bounds_max = (size[0] + margin, size[1] + margin, max(k.bounds_max[2], float(tris[:, :, 2].max())))
    root, leaves = parts_tree(tris, (-margin, -margin, size[0] + margin, size[1] + margin))
    entries = [(0, 0, 0, k.bounds_max[0]), (2, 0, 0, k.bounds_min[0]), (0, 1, 0, k.bounds_max[1]),
               (2, 1, 0, k.bounds_min[1]), (0, 2, 0, k.bounds_max[2]), (2, 2, 0, k.bounds_min[2])]
    count = [0]

    def emit(n):
        if n[0] == "leaf":
            entries.append((1, 2, count[0], k.bounds_max[2]))
            count[0] += 1
            return
        at = len(entries)
        entries.append(None)
        emit(n[3])   # above the split: the next entry
        entries[at] = (4, n[1], 2 * (len(entries) - at), n[2])
        emit(n[4])   # below it
    emit(root)
    k.subtrees = [copy(k.subtrees[0]) for _ in range(count[0])]
    k.set_main_entries(entries)
    held = fill_parts(k, tris, leaves)
    data = k.to_bytes()
    Kdt(data)
    return data, (f"{'camera floor' if camera else 'units ground'}: {len(tris):,} triangles in {count[0]} part(s) "
                  f"({min(held)}..{max(held)} each)")


def grow_tiles(arc, lod: str, cx: int, cy: int) -> tuple[dict, str]:
    """A tile set (close-up or far) for `cx` x `cy` of its cells: each level's tiles the copied map's own tile of that
    level from the middle of the map (one plain colour all over), the overview its own."""
    from .tmst import Tmst
    tm = Tmst.from_edat(arc, lod)
    d = tm.depth
    pick = {}
    for level in range(d):
        side = 1 << (d - 1 - level)
        pick[level] = tm.read(tm.tile(level, (tm.grid_w // 2) * side, (tm.grid_h // 2) * side))
    records = [tm.read(tm.tiles[0])]
    for level in range(d - 1, -1, -1):
        side = 1 << (d - 1 - level)
        records += [pick[level]] * (cx * cy * side * side)
    key = struct.pack("<I", tm.key)
    chunk, table, pos = [key], [], 4
    for rec in records:
        table.append(struct.pack("<II", pos, len(rec)))
        chunk += [rec, key]
        pos += len(rec) + 4
    head = bytearray(tm.index[:tm.table_offset])
    table_b = b"".join(table)
    struct.pack_into("<I", head, 0x0C, len(head) + len(table_b) + 4)
    struct.pack_into("<II", head, 0x14, cx, cy)
    struct.pack_into("<I", head, 0x20, pos)
    struct.pack_into("<I", head, 0x28, len(table_b))
    index, store = bytes(head) + table_b + b"TMST", b"".join(chunk)
    back = Tmst(index, store)
    if back.grid_w != cx or back.grid_h != cy or len(back.tiles) != len(records):
        raise BigMapError(f"{lod}: the grown tile set doesn't read back")
    return {tm.index_path: index, tm.chunk_path: store}, f"{lod} tiles: {len(records):,} on {cx} x {cy} cells"


def png_bytes(width: int, height: int, pixel: bytes) -> bytes:
    """A PNG of one pixel value all over: 8-bit RGBA (colour type 6, as the maps' own) or RGB."""
    raw = (b"\0" + pixel * width) * height

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    kind = 6 if len(pixel) == 4 else 2
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, kind, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def colour_of(png: bytes) -> bytes:
    """A picture's commonest pixel (all its channels)."""
    from .png import read_png
    w, h, px = read_png(png)
    bpp = len(px) // (w * h)
    return Counter(bytes(px[i:i + bpp]) for i in range(0, len(px), bpp)).most_common(1)[0][0]


def picture_size(cx: int, cy: int, per: int) -> tuple[int, int]:
    """A whole-map picture's size for `cx` x `cy` cells at `per` pixels a cell, at most GLOBAL_MOST a side (both sides
    scaled alike)."""
    w, h = cx * per, cy * per
    k = min(1.0, GLOBAL_MOST / max(w, h))
    return max(1, round(w * k)), max(1, round(h * k))


def dry_tile(lookup: bytes, inputs: bytes) -> bytes:
    """The water lookup's pixel for a dry cell: of the atlas tiles its cells use, the most used whose middle texel
    has no depth (the test groundgen.water_pictures and rusemod.water make), with no flags. Not just the most used
    tile: on a map with a lot of sea (D-Day) that's the sea's, and a map grown all sea has no dry tile for the
    build's own ground to start from (it fell back to its slow way, 2026-10-17)."""
    from . import water as W
    _t, ind = W._pixels(lookup)
    tw, inp = W._pixels(inputs)
    cols = tw.width // W.TILE
    uses = Counter((ind[i + 1], ind[i + 2]) for i in range(0, len(ind), 4))
    for (row, col), _n in uses.most_common():
        o = (row * W.TILE + 8) * tw.width * 4 + (col * W.TILE + 8) * 4
        if col < cols and o + 2 < len(inp) and inp[o + 2] == 0:
            return bytes((0, row, col, 0))
    raise BigMapError("the copied map's water has no dry tile")


def grow_water_lookup(raw: bytes, size: tuple, inputs: bytes) -> tuple[bytes, str]:
    """The water's lookup (riverindirectionsurface) over `size`, all dry (dry_tile, from the copied map's water
    `inputs`): a power of two each way covering the map's water cells (D-Day's 256 x 128, Hollande's 64 x 128)."""
    from . import water as W
    from .tmst import make_tgv, zipo_pack
    t, _px = W._pixels(raw)
    dry = dry_tile(raw, inputs)
    ax, ay = (math.ceil(s / W.CASE) for s in size)
    sx, sy = (1 << (a - 1).bit_length() for a in (ax, ay))
    out = make_tgv(sx, sy, t.format, [zipo_pack(dry * (sx * sy))])
    W._pixels(out)
    return out, f"water lookup: {sx} x {sy} ({ax} x {ay} water cells), dry"


def grid_r(side: float) -> int:
    """An SDB tree's cells a side over `side` map units: the smallest power of two keeping a cell within
    GRID_CELL_MOST, at most GRID_R_MOST."""
    r = 2
    while side / r > GRID_CELL_MOST and r < GRID_R_MOST:
        r *= 2
    return r


def uniform_sdb(raw: bytes, box: tuple, value: int, r: int, cell: float | None = None) -> bytes:
    """An SDB quadtree over `box` (x0, y0, width, height) holding `value` everywhere, `r` cells a side: a root node and
    one line of nodes down to the finest level (the rest leaves), so the tree reads as r x r cells (sdb.tree_grid_R)
    and its painters (cover, water marks) work at that size. Never one leaf: the game reads the root as a node without
    looking (a one-leaf root crashed it when a building was placed; every shipped tree starts with a node)."""
    from ruse_mod_engine import sdb
    levels = max(2, r.bit_length() - 1)
    leaf = (value | value << 8 | value << 16 | value << 24) | 1
    ents = [(1 << 2) + 0x1C]
    for level in range(1, levels):
        nxt = 0x20 + 16 * level if level < levels - 1 else leaf   # the next block, or a leaf at the finest level
        ents += [nxt, leaf, leaf, leaf]
    head28 = bytearray(raw[29:57])
    struct.pack_into("<4f", head28, 0, *box)
    if cell is not None:
        struct.pack_into("<f", head28, 16, cell)
    payload = bytes(head28) + struct.pack(f"<{len(ents)}I", *ents)
    ver = raw[21:25]
    md5 = hashlib.md5(b"SDB\r\n" + ver + struct.pack("<I", len(payload)) + payload).digest()
    trailing = raw[29 + struct.unpack_from("<I", raw, 25)[0]:]
    out = b"SDB\r\n" + md5 + ver + struct.pack("<I", len(payload)) + payload + trailing
    p = sdb.parse(out)
    if sdb.tree_grid_R(p) != 1 << levels or struct.unpack_from("<I", out, 57)[0] & 1:
        raise BigMapError("a grown SDB tree doesn't read back")
    return out


def grow_pack(arc, cx: int, cy: int) -> tuple[dict, dict, list[str]]:
    """The map pack's size-bound members made at `cx` x `cy` cells, from the copied map's own (`arc`): ({member path:
    bytes}, facts {"ground": height}, notes). Needs numpy (the kd-trees)."""
    from . import water as W
    from .tms import Tms

    def rd(m):
        return bytes(arc.read(arc.find(m)))
    size = (cx * CASE, cy * CASE)
    near0, far0 = Tms(rd("output\\highdef.tms")), Tms(rd("output\\lowdef.tms"))
    ground = near0.height_at(near0.bounds[3] / 2, near0.bounds[4] / 2)
    if ground is None:
        raise BigMapError("the copied map's ground can't be read at its middle")
    water_near, water_far = near0.to_world(2, near0.base_water()), far0.to_world(2, far0.base_water())
    new, notes = {}, []
    near_raw, info = grow_mesh(rd("output\\highdef.tms"), cx, cy, True, ground, water_near)
    new["output\\highdef.tms"] = near_raw
    notes.append(f"close-up mesh: {cx} x {cy} cells, {info['triangles']:,} triangles, flat at {ground:.0f}")
    far_raw, info = grow_mesh(rd("output\\lowdef.tms"), cx // 2, cy // 2, False, ground, water_far)
    new["output\\lowdef.tms"] = far_raw
    notes.append(f"far mesh: {cx // 2} x {cy // 2} cells, {info['triangles']:,} triangles")
    near, far = Tms(near_raw), Tms(far_raw)
    for m, mesh, camera in (("output\\occlusioninfo_terrainonly.kdt", near, False),
                            ("output\\occlusioninfo_camera.kdt", far, True)):
        new[m], said = balanced_tree(rd(m), mesh, camera, size)
        notes.append(said)
    for lod, (gx, gy) in (("highdef", (cx, cy)), ("lowdef", (cx // 2, cy // 2))):
        members, said = grow_tiles(arc, lod, gx, gy)
        new.update(members)
        notes.append(said)
    for m, per, (gx, gy) in (("output\\terrain.png", 64, (cx, cy)), ("output\\terrainwithunit.png", 128, (cx // 2, cy // 2))):
        try:
            rgb = colour_of(rd(m))
        except KeyError:
            continue
        w, h = picture_size(gx, gy, per)
        new[m] = png_bytes(w, h, rgb)
        notes.append(f"{m.split(chr(92))[-1]}: {w} x {h}")
    new[W.TEXTURES["indirection"]], said = grow_water_lookup(rd(W.TEXTURES["indirection"]), size,
                                                              rd(W.TEXTURES["inputs"]))
    notes.append(said)
    side = max(size)
    new["output\\output.sdb"] = uniform_sdb(rd("output\\output.sdb"), (0.0, 0.0, side, side), 0x01, grid_r(side))
    notes.append(f"level-build state: {grid_r(side)} cells a side over {side:,.0f}, all land")
    return ({arc.find(m).path: b for m, b in new.items()}, {"ground": ground, "cells": near0.grid_w * near0.grid_h},
            notes)


class Resized:
    """A map pack with some members made again (grow_pack's): every read and the written pack see the new ones; the
    pack under it is only read."""

    def __init__(self, base, members: dict):
        self.base = base
        self.over = {k.lower(): (k, bytes(v)) for k, v in members.items()}

    def __getattr__(self, name):
        return getattr(self.base, name)

    def read(self, entry):
        got = self.over.get(entry.path.lower())
        return got[1] if got is not None else self.base.read(entry)

    def iter_chunks(self, replace=None, add=None):
        merged = {path: data for path, data in self.over.values()}
        for key, data in (replace or {}).items():
            e = self.base.entry(key) or self.base.find(key)
            merged = {p: d for p, d in merged.items() if p.lower() != e.path.lower()}
            merged[e.path] = data
        return self.base.iter_chunks(merged, add)

    def to_bytes(self, replace=None, add=None) -> bytes:
        return b"".join(self.iter_chunks(replace, add))

    def write_to(self, out, replace=None, add=None) -> int:
        n = 0
        for chunk in self.iter_chunks(replace, add):
            out.write(chunk)
            n += len(chunk)
        return n


# --- tiles added on the map's first sides: everything placed moves with the map -------------------------------------
SHIFT_FILES = ("terrain.toml", "scenery.toml", "scenario.toml", "places.toml", "items.toml", "cover.toml",
               "movement.toml", "roads.toml", "mission.toml")   # a map's files that hold places on it (MOD_FORMAT §8)
_NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"


FIXED_TABLES = ("erase", "own")   # tables that name the copied map's own objects where they stand (scenery.toml's
                                  # [[erase]] areas and [[own]] rows): those never move, so they aren't shifted


def shift_text(text: str, dx: float, dy: float) -> tuple[str, int]:
    """A map file's text with every place the mod put on it moved by (dx, dy) map units: each `x = ` and `y = ` line,
    and each point (the first two numbers of every innermost [..]) in `points`, `area` and `within` (one line or
    several), except in FIXED_TABLES (they point at the copied map's own objects, which stay where they are).
    Everything else (comments, layout, other numbers) is kept as it was. Returns (text, how many numbers moved)."""
    import re
    parts = re.split(r"(?m)^(?=\s*\[\[?\s*[A-Za-z_])", text)   # each table with what follows it (the first part:
    # before any table); a header is [name] or [[name]], never an array's next line ([5.0, ...)
    out, total = [], 0
    for part in parts:
        head = re.match(r"\s*\[\[?\s*([A-Za-z_]+)", part)
        if head and head.group(1) in FIXED_TABLES:
            out.append(part)
            continue
        moved_part, n = _shift_part(part, dx, dy)
        out.append(moved_part)
        total += n
    return "".join(out), total


def _shift_part(text: str, dx: float, dy: float) -> tuple[str, int]:
    import re
    moved = [0]

    def num(v: float) -> str:
        return repr(float(v))

    def one(m):
        moved[0] += 1
        return f"{m.group(1)}{m.group(2)} = {num(float(m.group(3)) + (dx if m.group(2) == 'x' else dy))}"
    text = re.sub(r"(?m)^(\s*)(x|y)\s*=\s*(" + _NUM + r")(?=\s*(?:#|$))", one, text)
    point = re.compile(r"\[\s*(" + _NUM + r")\s*,\s*(" + _NUM + r")((?:\s*,\s*" + _NUM + r")*)\s*\]")

    def pair(m):
        moved[0] += 2
        return f"[{num(float(m.group(1)) + dx)}, {num(float(m.group(2)) + dy)}{m.group(3)}]"
    out, pos = [], 0
    for m in re.finditer(r"(?m)^\s*(?:points|area|within)\s*=\s*\[", text):
        start = m.end() - 1
        depth, i = 0, start
        while i < len(text):   # the array's end: its brackets counted (an array may run over several lines)
            depth += {"[": 1, "]": -1}.get(text[i], 0)
            if depth == 0:
                break
            i += 1
        out += [text[pos:start], point.sub(pair, text[start:i + 1])]
        pos = i + 1
    out.append(text[pos:])
    return "".join(out), moved[0]


def refit_whole_map(text: str, old: tuple, new: tuple) -> tuple[str, int]:
    """terrain.toml's text with the strokes a blank start lays over the whole map (rusemod.presets.strokes: the level,
    the drain or the sea, the paint, each a square at the map's middle reaching past its corners) made to reach over
    the new map: each stroke at `old` (x, y, radius) gets `new` (x, y, radius). A blank map's ground is drawn as our
    own only when its first height stroke levels the whole map (groundgen.Shape). Returns (text, strokes refitted)."""
    import re
    ox, oy, orad = old
    nx, ny, nrad = new
    done = [0]

    def block(m):
        part = m.group(0)
        vals = {k: float(v) for k, v in re.findall(r"(?m)^\s*(x|y|radius)\s*=\s*(" + _NUM + r")", part)}
        if len(vals) == 3 and abs(vals["x"] - ox) < 1 and abs(vals["y"] - oy) < 1 and abs(vals["radius"] - orad) < 1:
            done[0] += 1
            for k, v in (("x", nx), ("y", ny), ("radius", nrad)):
                part = re.sub(r"(?m)^(\s*)" + k + r"\s*=\s*" + _NUM, lambda mm, v=v, k=k: f"{mm.group(1)}{k} = {float(v)!r}",
                              part, count=1)
        return part
    out = re.sub(r"(?ms)^\[\[stroke\]\].*?(?=^\[|\Z)", block, text)
    return out, done[0]


def whole_map_reach(width: float, height: float) -> tuple[float, float, float]:
    """The middle of a `width` x `height` map and the half-side of the square a blank start's strokes use there
    (presets.whole_map: past the corners at full strength)."""
    from .brush import HARD_EDGE
    from .presets import REACH
    return width / 2, height / 2, max(width, height) / 2 / HARD_EDGE * REACH


def shift_map_folder(folder, dx: float, dy: float) -> list[tuple[str, int]]:
    """Every place in a map's files (maps/<map>/, SHIFT_FILES) moved by (dx, dy): each file rewritten (written next to
    it, then put in place). Returns (file name, numbers moved) for each file changed."""
    import os
    from pathlib import Path
    done = []
    for name in SHIFT_FILES:
        f = Path(folder) / name
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        new, n = shift_text(text, dx, dy)
        if n:
            tmp = f.with_suffix(f.suffix + ".moving")
            tmp.write_text(new, encoding="utf-8")
            os.replace(tmp, f)
            done.append((name, n))
    return done


# --- mapinfo.win --------------------------------------------------------------------------------------------------
def lattice(size: tuple) -> tuple[bytes, int, int]:
    """A movement graph open everywhere over `size`: circles every pitch (LATTICE_PITCH, wider past LATTICE_MOST a
    side), each 0.75 of a pitch across so they overlap, linked to the next along and down; no local maps, no road
    crossings; its index made the game's way (nav._tree_build). Returns (bytes, circles, links)."""
    from .nav import Graph, _tree_build, _tree_write
    longest = max(size)
    n_most = min(LATTICE_MOST, math.ceil(longest / LATTICE_PITCH))
    pitch = math.ceil(longest / n_most / 640.0) * 640.0
    radius = math.ceil(0.75 * pitch / 320.0) * 320.0
    nx, ny = math.ceil(size[0] / pitch), math.ceil(size[1] / pitch)
    ax = [pitch / 2 + i * pitch for i in range(nx)]
    ay = [pitch / 2 + j * pitch for j in range(ny)]
    number, circles = {}, []
    for j in range(ny):
        for i in range(nx):
            number[(i, j)] = len(circles)
            circles.append((ax[i], ay[j], radius))
    links, mine = [], {c: [] for c in range(len(circles))}
    for j in range(ny):
        for i in range(nx):
            a = number[(i, j)]
            for di, dj in ((1, 0), (0, 1)):
                if (i + di, j + dj) in number:
                    b = number[(i + di, j + dj)]
                    links.append((a, b, (circles[a][0] + circles[b][0]) / 2, (circles[a][1] + circles[b][1]) / 2))
                    mine[a].append(len(links) - 1)
                    mine[b].append(len(links) - 1)
    lists, recs = [], []
    for c, (x, y, r) in enumerate(circles):
        recs.append((x, y, r, len(lists), 0))
        lists += mine[c]
    recs.append((0.0, 0.0, 0.0, len(lists), 0))   # the closing record: where the last list ends
    if len(lists) >= 65536:
        raise BigMapError(f"the movement lattice lists {len(lists):,} links (at most 65,535)")
    g = Graph((0, 0, longest), recs, links, lists, b"", _tree_write(_tree_build(circles)), [], bytes(64))
    raw = g.to_bytes()
    back = Graph.read(raw)
    if len(back.parts()) != 1 or not back.walkable(size[0] - 1000.0, size[1] - 1000.0):
        raise BigMapError("the movement lattice doesn't read back as one piece")
    return raw, len(circles), len(links)


def join_mapinfo(head: bytes, bufs: list, tail: bytes) -> bytes:
    """mapinfo.win from its parts, with its (salted) checksum."""
    out = bytearray(head + b"".join(struct.pack("<I", len(b)) + b for b in bufs) + tail)
    out[8:24] = hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + bytes(out[24:])).digest()
    return bytes(out)


def grow_mapinfo(win: bytes, cx: int, cy: int) -> tuple[bytes, list[str]]:
    """mapinfo.win at `cx` x `cy` cells: its header's size, both movement graphs a lattice open everywhere, the cover
    grid over the map with no cover (as deep as the shipped grids), the AI grid open."""
    from ruse_mod_engine import sdb
    from .aigrid import Tail
    size = (cx * CASE, cy * CASE)
    head, bufs, tail = sdb.split_mapinfo(win)
    head = bytearray(head)
    struct.pack_into("<2f", head, 0x28, *size)
    graph, nc, nl = lattice(size)
    bufs = list(bufs)
    bufs[1] = bufs[2] = graph
    notes = [f"movement (both graphs): {nc:,} circles, {nl:,} links, open everywhere"]
    r = grid_r(max(size))
    bufs[3] = uniform_sdb(bufs[3], (0.0, 0.0, *size), 0x01, r, max(size) / r)
    notes.append(f"cover grid: {r} cells a side, no cover")
    t = Tail(tail)
    t.w, t.h = math.ceil(size[0] / AI_CELL), math.ceil(size[1] / AI_CELL)
    t.cells = bytearray(b"\x00\x7f" * (t.w * t.h))
    t.pad = b""
    notes.append(f"AI grid: {t.w} x {t.h}, open")
    return join_mapinfo(bytes(head), bufs, t.to_bytes()), notes


# --- the map's settings -------------------------------------------------------------------------------------------
def _f32(x):
    return lambda v: struct.pack("<f", x)


def _f3(x, y, z):
    return lambda v: struct.pack("<3f", x, y, z)


def _i32(x):
    return lambda v: struct.pack("<i", x)


def _set(nd, o, values: dict) -> int:
    from .ndf import Value
    n = 0
    for k, (pi, v) in enumerate(o.props):
        name = nd.prop_name(pi)
        if name in values:
            o.props[k] = (pi, Value(v.tc, values[name](v)))
            n += 1
    return n


def _set_class(nd, cls: str, values: dict) -> int:
    return sum(_set(nd, o, values) for o in nd.objects if nd.classes[o.cls] == cls)


def grow_constants(raw: bytes, cx: int, cy: int, clouds: float | None) -> tuple[bytes, list[str]]:
    """A map's MapConstante at `cx` x `cy` cells: the camera's map size, the level build's areas (the copied map's
    margin past the edge kept), the cell grid, the camera's flat floor (over the new edge), Map_Size, and the cloud
    layer's height when `clouds` is given."""
    from .ndf import Ndf, Value
    nd = Ndf(raw)
    sx, sy = cx * CASE, cy * CASE
    n = _set_class(nd, "TCameraMoverHelperUsingCameraAndWorldFloor", {"MapSizeX": _f32(sx), "MapSizeY": _f32(sy)})
    n += _set_class(nd, "TLevelBuildStateGeoDatabase", {"AreaMaxX": _f32(sx), "AreaMaxY": _f32(sy)})
    margin = 0.0
    for o in nd.objects:
        if nd.classes[o.cls] == "TLevelBuildGeoDatabase":
            props = {nd.prop_name(pi): v for pi, v in o.props}
            lo = struct.unpack("<3f", bytes(props["AreaMin"].payload))
            hi = struct.unpack("<3f", bytes(props["AreaMax"].payload))
            margin = -lo[0]
            n += _set(nd, o, {"AreaMax": _f3(sx + margin, sy + margin, hi[2]), "VisibleAreaMax": _f3(sx, sy, 0.0)})
    n += _set_class(nd, "TCurrentMapInfo", {"NbCaseX": _i32(2 * cx), "NbCaseY": _i32(2 * cy)})
    reach = max(5.0e6, FLOOR_REACH * max(sx, sy))
    floor = {"Min": _f3(-reach, -reach, 0.0), "Max": _f3(reach, reach, 0.0)}
    n += _set_class(nd, "TWorldFloorFlat", floor) + _set_class(nd, "TWorldFloorStreamedMeshKdTree", floor)
    notes = []
    for i, o in enumerate(nd.objects):
        name = nd.exports.get(i) or ""
        if nd.classes[o.cls] == "TEugBFloat3" and name.endswith("/Map_Size"):
            o.props = [(pi, Value(v.tc, struct.pack("<3f", sx, sy, 1.0))) for pi, v in o.props]
            n += 1
        if clouds is not None and nd.classes[o.cls] == "TEugBFloat" and name.endswith("/CloudHeight"):
            n += _set(nd, o, {"Value": _f32(clouds)})
            notes.append(f"clouds: at {clouds:,.0f}")
    notes.insert(0, f"MapConstante: {n} value(s) for {cx} x {cy} cells ({sx / 260 / 1000:.1f} x {sy / 260 / 1000:.1f} km)")
    return nd.to_member(compress=bool(nd.flags & 0x80)), notes


def grow_terrain_settings(raw: bytes, cx: int, cy: int) -> tuple[bytes, list[str]]:
    """A map's mapTerrain at `cx` x `cy` cells: each mesh loader's cell grid (close-up cx x cy, far half that), the
    water's (twice the close-up's), and the static level build's squares doubled until a side holds STATIC_MOST or
    fewer (the game's Hilbert curve over them: order ceil(sqrt(squares a side)), 4^order entries)."""
    from .ndf import Ndf
    nd = Ndf(raw)
    n = 0
    for o in nd.objects:
        if nd.classes[o.cls] == "TTerrainGeometryLoader":
            props = {nd.prop_name(pi): v for pi, v in o.props}
            close = props["CaseSize"].scalar() == CASE
            n += _set(nd, o, {"NbCaseX": _i32(cx if close else cx // 2), "NbCaseY": _i32(cy if close else cy // 2)})
    n += _set_class(nd, "TWaterOnGPU", {"NbHighDefCaseX": _i32(2 * cx), "NbHighDefCaseY": _i32(2 * cy)})
    static, side = 81920.0, max(cx, cy) * CASE + 2 * 34050.0
    for o in nd.objects:
        if nd.classes[o.cls] == "TStaticLevelBuildManager":
            props = {nd.prop_name(pi): v for pi, v in o.props}
            static = props["CaseSize"].scalar()
    while int(side / static) > STATIC_MOST:
        static *= 2
    n += _set_class(nd, "TStaticLevelBuildManager", {"CaseSize": _f32(static)})
    return nd.to_member(compress=bool(nd.flags & 0x80)), [
        f"mapTerrain: {n} value(s); static level build squares of {static:,.0f} ({int(side / static)} a side)"]


def grow_clone(clone, read_glad, cx: int, cy: int, clouds: float | None, room: str) -> list[str]:
    """A new map's copied files (newmap.Clone) made for `cx` x `cy` cells, in place: its MapConstante (grow_constants),
    its mapinfo.win (grow_mapinfo), and its own mapTerrain (grow_terrain_settings) and HQLoader (the room out when
    `room` is "out", else as the copied map's), which its map cluster is pointed at. `read_glad(member)`: a member of
    ZZ_GladPatchableWin.dat as the build has it. Returns the notes."""
    import re
    from .ndf import Ndf
    from .newmap import BS, _member, _renamer, _swap_strings
    new, src = clone.new, clone.map_folder
    notes = []

    def key_of(d: dict, member: str):
        return next((k for k in d if k.lower() == member.lower()), None)
    mk = key_of(clone.glad, _member("Patchable" + BS + "map" + BS + new + BS + "MapConstante"))
    win = key_of(clone.data, "datasmap" + BS + new.lower() + BS + "mapinfo.win")
    cm = key_of(clone.glad, _member("Patchable" + BS + "map" + BS + new + BS + "ClusterMap"))
    if mk is None or win is None or cm is None:
        raise BigMapError(f"maps/{new}: the copy of {clone.source} has no MapConstante, mapinfo.win or map cluster to "
                          f"make at the new size")
    clone.glad[mk], said = grow_constants(clone.glad[mk], cx, cy, clouds)
    notes += said
    clone.data[win], said = grow_mapinfo(clone.data[win], cx, cy)
    notes += said
    cluster = Ndf(clone.glad[cm])
    mf = re.escape(src)
    for name, make in (("mapTerrain", lambda raw: grow_terrain_settings(raw, cx, cy)),
                       ("HQLoader", (lambda raw: room_out(raw)) if room == "out" else (lambda raw: (raw, [])))):
        raw = read_glad(_member("Patchable" + BS + "map" + BS + src + BS + name))
        if raw is None:
            raise BigMapError(f"maps/{new}: {clone.source} has no {name} to copy for the new size")
        data, said = make(raw)
        notes += said
        clone.glad[_member("Patchable" + BS + "map" + BS + new + BS + name)] = data
        n = _swap_strings(cluster, _renamer(
            re.compile(r"^(Patchable[\\/]map[\\/])(" + mf + r")([\\/]" + name + r")$", re.I),
            re.compile(r"^(map[\\/])(" + mf + r")([\\/]" + name + r"\.ndfbin)$", re.I))(new))
        if n < 1:
            raise BigMapError(f"maps/{new}: {clone.source}'s map cluster doesn't load its {name} the way the game's "
                              f"maps do, so the new size can't be given to it")
    clone.glad[cm] = cluster.to_member(compress=bool(cluster.flags & 0x80))
    return notes


def room_out(raw: bytes) -> tuple[bytes, list[str]]:
    """A map's HQLoader with every room mesh placed (table, people, glass, lights, walls, floor) put ROOM_AWAY under
    the map, past the far clipping; the outdoor sky (the mesh without a place) stays."""
    from .ndf import Ndf
    nd = Ndf(raw)
    n = 0
    for o in nd.objects:
        props = {nd.prop_name(pi) for pi, _v in o.props}
        if nd.classes[o.cls] == "TMultiMobileMesh" and "Position" in props:
            n += _set(nd, o, {"Position": _f3(0.0, 0.0, -ROOM_AWAY)})
    return nd.to_member(compress=bool(nd.flags & 0x80)), [f"HQ room: {n} mesh(es) out of sight, the sky kept"]
