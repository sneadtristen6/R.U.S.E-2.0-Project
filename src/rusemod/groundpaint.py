"""Painting on a map's ground picture: its highdef and lowdef texture tiles (rusemod.tmst; FORMATS.md §6), a pyramid
of 512x512 DXT1 tiles over the map's cells. A painted tile is written back as a plain ZIPO DXT1 tile, which the game
draws (proven with plain tiles, 2026-09-29); only the 4x4 blocks the paint touches are encoded again, the rest keep
their bytes. First use: the roads a mod draws, painted in the colour of the map's own roads, so a new road shows
where supply trucks already drive it (the roads a player sees from afar are painted into these tiles, 2026-09-30).

The map's close-up map (`output\\div_map.tgv_pc`, the "texture diversity", one DXT5 picture over the whole grid of
cells) marks every map's own roads (alpha higher, red lower than the ground beside: all 31 maps with roads), and
paint_detail gives a new road the same mark. A first idea was that this mark keeps a road showing near the camera; the
game says otherwise (batch 5, 2026-10-01: with the mark, the new road still vanished up close). What the mark does in
the game, and what draws the close-up road, isn't known yet (TESTS.md T12). The checks here are on the files' bytes
only (tests/test_groundpaint.py), never proof of what the game shows.
"""
from __future__ import annotations

import math
import struct

from . import dxt, tgu1
from .tmst import Tgv, Tmst, zipo_pack, zipo_tile, zipo_unpack

LODS = ("highdef", "lowdef")
ROAD_WIDTH = 1800.0     # map units (about 7 m): a road's painted width
FEATHER = 0.6           # of the half-width: how far the edge fades into the ground


class PaintError(ValueError):
    pass


def map_bounds(mesh: bytes) -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) of the ground in map units, from a .tms mesh's header (the tiles cover exactly this)."""
    x0, y0, _z0, x1, y1, _z1 = struct.unpack_from("<6f", mesh, 0x23C)
    if not (x1 > x0 and y1 > y0):
        raise PaintError("the map's ground bounds can't be read")
    return x0, y0, x1, y1


def grid_bounds(mesh: bytes) -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) of the ground's whole grid of cells (its corner, then its cells across and down times their
    size, from a .tms header): what the close-up map covers, stretched over it (checked on all 32 maps: a round
    pixel size on every one, and on Tunisie and Ardennes, whose pictures aren't square, the map's own roads line up
    only this way). On 6 maps the mesh's bounds end 1,920 short of the grid."""
    x0, y0, _x1, _y1 = map_bounds(mesh)
    gw, gh = struct.unpack_from("<2I", mesh, 0x10)
    cw, ch = struct.unpack_from("<2f", mesh, 0x1C)
    if not (gw and gh and cw > 0 and ch > 0):
        raise PaintError("the map's ground grid can't be read")
    return x0, y0, x0 + gw * cw, y0 + gh * ch


def _blocks(store: Tmst, tile) -> tuple[bytearray, int, int]:
    """A tile's DXT1 blocks and its width and height in pixels, from the payload itself: never assumed (the whole-map
    overview tile is 256 wide on Blitz and 1024 x 512 on D-Day, the others 512) and never taken from the TGV
    header, which can say more than it holds."""
    tex = store.texture(tile)
    payload = tex.payload(0)
    if payload[:4] == b"TGU1":
        head = tgu1.Header.parse(payload)
        w, h, blocks = head.width * 4, head.height * 4, bytearray(tgu1.decode(payload))
    elif payload[:4] == b"ZIPO":
        blocks = bytearray(zipo_unpack(payload))
        w, h = tex.width, tex.height  # a plain tile (ours): its header is right, and checked below
    else:
        raise PaintError(f"tile {tile.index} has an unknown codec {payload[:4]!r}")
    if len(blocks) != w * h // 2:
        raise PaintError(f"tile {tile.index} holds {len(blocks)} bytes, not the {w}x{h} its payload says")
    return blocks, w, h


def _dims(store: Tmst, tile) -> tuple[int, int]:
    """A tile's width and height in pixels from its payload (a TGU1 header is cheap to read; ZIPO is unpacked)."""
    payload = store.texture(tile).payload(0)
    if payload[:4] == b"TGU1":
        head = tgu1.Header.parse(payload)
        return head.width * 4, head.height * 4
    return _blocks(store, tile)[1:]


TILE_CELL = 327680.0  # map units a close tile store's cell is across: on 26 maps the ground mesh ends exactly on
                      # that grid; on 6 (Alpha, Beta, DiplomatieTriangulaire, Gam_Ostfriesland, Gamma, Robert) it ends
                      # 1,920 short of it, and the tiles keep the grid (the map's own roads line up with it there)


def _cells(store: Tmst, bounds) -> tuple[float, float]:
    """The map units a cell of `store`'s grid is across, x and y: the bounds over the grid, put on the game's grid
    (TILE_CELL for the close store, twice it for the far one) when within 1% of it, as on every shipped map."""
    x0, y0, x1, y1 = bounds
    out = []
    for span, n in ((x1 - x0, store.grid_w), (y1 - y0, store.grid_h)):
        cell, k = span / n, round(span / n / TILE_CELL)
        out.append(k * TILE_CELL if k >= 1 and abs(cell - k * TILE_CELL) <= 0.01 * k * TILE_CELL else cell)
    return tuple(out)


def _tile_rect(store: Tmst, tile, bounds) -> tuple[float, float, float, float]:
    x0, y0, _x1, _y1 = bounds
    ax0, ay0, ax1, ay1 = store.area(tile)
    cw, ch = _cells(store, bounds)
    return x0 + ax0 * cw, y0 + ay0 * ch, x0 + ax1 * cw, y0 + ay1 * ch


def _segments(lines):
    return [(ax, ay, bx, by) for line in lines for (ax, ay), (bx, by) in zip(line, line[1:])]


def _dist(px, py, seg) -> float:
    ax, ay, bx, by = seg
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / n))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def road_colour(store: Tmst, bounds, pieces: list[tuple], most: int = 40) -> tuple[int, int, int]:
    """The colour of the map's own roads: its pictures' pixels at the middles of up to `most` road pieces
    (rusemod.scenery Scenery.roads), from the finest level; a grey-brown when the map has no road."""
    if not pieces:
        return (150, 140, 120)
    step = max(1, len(pieces) // most)
    picks = [pieces[i] for i in range(0, len(pieces), step)][:most]
    x0, y0, _x1, _y1 = bounds
    side = 1 << (store.depth - 1)
    cw, ch = _cells(store, bounds)
    tw, th = cw / side, ch / side
    by_tile: dict = {}
    for p in picks:
        t = 0.5  # the Bézier's middle
        x = 0.125 * p[0] + 0.375 * p[2] + 0.375 * p[4] + 0.125 * p[6]
        y = 0.125 * p[1] + 0.375 * p[3] + 0.375 * p[5] + 0.125 * p[7]
        tx, ty = int((x - x0) / tw), int((y - y0) / th)
        by_tile.setdefault((tx, ty), []).append((x, y))
    total, n = [0, 0, 0], 0
    for (tx, ty), spots in sorted(by_tile.items(), key=lambda kv: -len(kv[1]))[:6]:
        try:
            tile = store.tile(0, tx, ty)
        except KeyError:
            continue
        blocks, w, h = _blocks(store, tile)
        for x, y in spots:
            px = int((x - x0 - tx * tw) / tw * w)
            py = int((y - y0 - ty * th) / th * h)
            if not (0 <= px < w and 0 <= py < h):
                continue
            b = (py // 4) * (w // 4) + px // 4
            r, g, bl = dxt.block_pixels(bytes(blocks[8 * b:8 * b + 8]))[(py % 4) * 4 + px % 4]
            total[0] += r
            total[1] += g
            total[2] += bl
            n += 1
    return tuple(round(v / n) for v in total) if n else (150, 140, 120)


def paint_lines(store: Tmst, bounds, lines: list[list[tuple[float, float]]], colour: tuple[int, int, int],
                width: float = ROAD_WIDTH) -> dict[int, bytes]:
    """`lines` (lists of map points) painted `width` wide in `colour` on every tile of `store` they cross, at every
    level; returns {tile index: new tile record} for Tmst.members. The edge fades over FEATHER of the half-width,
    and a line thinner than a pixel (the coarse levels) is painted faint rather than not at all."""
    segs = _segments(lines)
    if not segs:
        return {}
    half = width / 2
    reach = half * (1 + FEATHER)
    boxes = [(min(a, c) - reach, min(b, d) - reach, max(a, c) + reach, max(b, d) + reach) for a, b, c, d in segs]
    out = {}
    for tile in store.tiles:
        rx0, ry0, rx1, ry1 = _tile_rect(store, tile, bounds)
        near = [s for s, (bx0, by0, bx1, by1) in zip(segs, boxes) if bx0 < rx1 and bx1 > rx0 and by0 < ry1 and by1 > ry0]
        if not near:
            continue
        w, h = _dims(store, tile)  # never assumed: the overview tile is 256 on Blitz, 1024 x 512 on D-Day
        pw, ph = (rx1 - rx0) / w, (ry1 - ry0) / h
        soft = max(half * FEATHER, pw)  # at least a pixel of fade
        faint = min(1.0, width / pw)     # a line narrower than a pixel only tints it
        blocks = None
        nx, ny = w // 4, h // 4
        for by in range(ny):
            cy0, cy1 = ry0 + by * 4 * ph, ry0 + (by + 1) * 4 * ph
            row = [s for s in near if min(s[1], s[3]) - reach < cy1 and max(s[1], s[3]) + reach > cy0]
            if not row:
                continue
            for bx in range(nx):
                cx0, cx1 = rx0 + bx * 4 * pw, rx0 + (bx + 1) * 4 * pw
                here = [s for s in row if min(s[0], s[2]) - reach < cx1 and max(s[0], s[2]) + reach > cx0]
                if not here:
                    continue
                cx, cy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
                if min(_dist(cx, cy, s) for s in here) > reach + 3 * max(pw, ph):
                    continue
                if blocks is None:
                    blocks = _blocks(store, tile)[0]
                k = by * nx + bx
                pixels = dxt.block_pixels(bytes(blocks[8 * k:8 * k + 8]))
                changed = False
                for i in range(16):
                    px = cx0 + (i % 4 + 0.5) * pw
                    py = cy0 + (i // 4 + 0.5) * ph
                    d = min(_dist(px, py, s) for s in here)
                    a = max(0.0, min(1.0, (half + soft / 2 - d) / soft)) * faint
                    if a > 0:
                        r, g, b = pixels[i]
                        pixels[i] = (round(r + (colour[0] - r) * a), round(g + (colour[1] - g) * a),
                                     round(b + (colour[2] - b) * a))
                        changed = True
                if changed:
                    blocks[8 * k:8 * k + 8] = dxt.encode_block(pixels)
        if blocks is not None:
            out[tile.index] = zipo_tile(bytes(blocks), w, h)
    return out


DETAIL = "output\\div_map.tgv_pc"
DETAIL_WIDER = 2.0      # the map's own roads there run 2 to 3 of its 5 m pixels wide: new ones are painted this much wider


def _tgv_with_payload(raw: bytes, payload: bytes) -> bytes:
    """A one-mip TGV record `raw` with its payload replaced: the header kept, the size patched, 4-aligned."""
    tex = Tgv(raw)
    if len(tex.mips) != 1:
        raise PaintError("the close-up map has more than one mip")
    offset, _size = tex.mips[0]
    name_len = struct.unpack_from("<H", raw, 26)[0]
    sizes_at = ((28 + name_len + 3) & ~3) + 4  # the header, 4-aligned, then one offset, then one size
    head = bytearray(raw[:offset])
    struct.pack_into("<I", head, sizes_at, len(payload))
    return bytes(head) + payload + bytes(-len(payload) % 4)


def paint_detail(raw: bytes, bounds, lines: list[list[tuple[float, float]]], pieces: list[tuple],
                 width: float = ROAD_WIDTH) -> tuple[bytes, list[str]]:
    """`lines` marked in the close-up map (`output\\div_map.tgv_pc`, one DXT5 picture stretched over `bounds`, the
    ground's whole grid: grid_bounds): the weights by which the ground shaders blend their detail textures over the
    tiles near the camera (its channels are data, not colours: blue is 24 on every map). The map's own roads are
    marked there (alpha higher, red lower than the ground beside), which keeps their colour from the tiles showing up
    close; new roads get the median of all four channels along the map's road pieces, `width` wide (the map's own
    run 2 to 3 pixels wide: DETAIL_WIDER). Returns (the new record, notes), or (b"", notes) when there's nothing to
    paint."""
    tex = Tgv(raw)
    payload = tex.payload(0)
    if not tex.format.upper().startswith("DXT5") or payload[:4] != b"ZIPO":
        return b"", [f"close-up map: {tex.format} {payload[:4]!r} can't be painted yet"]
    blocks = bytearray(zipo_unpack(payload))
    w, h = tex.width, tex.height
    if len(blocks) != w * h:
        raise PaintError(f"the close-up map holds {len(blocks)} bytes, not {w}x{h} DXT5")
    x0, y0, x1, y1 = bounds
    pw, ph = (x1 - x0) / w, (y1 - y0) / h
    nx = w // 4

    def at(x, y):
        px, py = min(w - 1, max(0, int((x - x0) / pw))), min(h - 1, max(0, int((y - y0) / ph)))
        k = (py // 4) * nx + px // 4
        rgb, alpha = dxt.dxt5_block(bytes(blocks[16 * k:16 * k + 16]))
        i = (py % 4) * 4 + px % 4
        return rgb[i] + (alpha[i],)
    samples = []
    for p in pieces[:: max(1, len(pieces) // 200)]:
        for t in (0.25, 0.5, 0.75):
            u = 1 - t
            samples.append(at(u ** 3 * p[0] + 3 * u * u * t * p[2] + 3 * u * t * t * p[4] + t ** 3 * p[6],
                              u ** 3 * p[1] + 3 * u * u * t * p[3] + 3 * u * t * t * p[5] + t ** 3 * p[7]))
    if not samples:
        return b"", ["close-up map: the map has no road to take the look from"]
    look = tuple(sorted(s[c] for s in samples)[len(samples) // 2] for c in range(4))
    segs = _segments(lines)
    if not segs:
        return b"", []
    half = width / 2
    soft = max(half * FEATHER, pw)
    faint = min(1.0, width / pw)
    reach = half + soft
    touched = set()
    for ax, ay, bx, by in segs:
        for bxi in range(int((min(ax, bx) - reach - x0) / pw) // 4, int((max(ax, bx) + reach - x0) / pw) // 4 + 1):
            for byi in range(int((min(ay, by) - reach - y0) / ph) // 4, int((max(ay, by) + reach - y0) / ph) // 4 + 1):
                if 0 <= bxi < nx and 0 <= byi < h // 4:
                    touched.add((bxi, byi))
    painted = 0
    for bxi, byi in sorted(touched):
        cx0, cy0 = x0 + bxi * 4 * pw, y0 + byi * 4 * ph
        near = [s for s in segs if _dist(cx0 + 2 * pw, cy0 + 2 * ph, s) <= reach + 3 * max(pw, ph)]
        if not near:
            continue
        k = byi * nx + bxi
        rgb, alpha = dxt.dxt5_block(bytes(blocks[16 * k:16 * k + 16]))
        changed = False
        for i in range(16):
            px, py = cx0 + (i % 4 + 0.5) * pw, cy0 + (i // 4 + 0.5) * ph
            a = max(0.0, min(1.0, (half + soft / 2 - min(_dist(px, py, s) for s in near)) / soft)) * faint
            if a > 0:
                r, g, b = rgb[i]
                rgb[i] = (round(r + (look[0] - r) * a), round(g + (look[1] - g) * a), round(b + (look[2] - b) * a))
                alpha[i] = round(alpha[i] + (look[3] - alpha[i]) * a)
                changed = True
        if changed:
            blocks[16 * k:16 * k + 16] = dxt.encode_dxt5_block(rgb, alpha)
            painted += 1
    if not painted:
        return b"", []
    return _tgv_with_payload(raw, zipo_pack(bytes(blocks))), [
        f"close-up map: {painted} block(s) painted, in the map's own road look {look}"]


def paint_roads(read, path_of, lines: list[list[tuple[float, float]]], pieces: list[tuple],
                width: float = ROAD_WIDTH) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): `lines` painted on both tile sets of a map pack, in its roads' colour. `read(name)`
    gives a member's bytes (the build's chain) or None, `path_of(name)` its full path in the pack; `pieces` are the
    map's road pieces (for the colour)."""
    mesh = read("output\\highdef.tms")
    if mesh is None:
        raise PaintError("the map has no ground mesh to place the paint on")
    bounds = map_bounds(mesh)
    out, notes, colour = {}, [], None
    for lod in LODS:
        index, chunk = read(f"output\\{lod}.tmst_pc"), read(f"output\\{lod}.tmst_chunk_pc")
        if index is None or chunk is None:
            continue
        store = Tmst(index, chunk)
        store.lod = lod
        store.index_path, store.chunk_path = path_of(f"output\\{lod}.tmst_pc"), path_of(f"output\\{lod}.tmst_chunk_pc")
        if colour is None:
            colour = road_colour(store, bounds, pieces)
        tiles = paint_lines(store, bounds, lines, colour, width)
        if tiles:
            out.update(store.members(tiles))
        notes.append(f"{lod}: {len(tiles)} tile(s) painted")
    if colour is not None:
        notes.insert(0, f"road colour {colour}")
    # the close-up map (paint_detail) is drawn by build.draw_new_roads, which also keeps its copy in ZZ_Win.dat
    return out, notes
