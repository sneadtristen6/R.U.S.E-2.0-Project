"""Painting on a map's ground picture: its highdef and lowdef texture tiles (rusemod.tmst; FORMATS.md §6), a pyramid
of 512x512 DXT1 tiles over the map's cells. A painted tile is written back as a plain ZIPO DXT1 tile, which the game
draws (proven with plain tiles, 2026-09-29); only the 4x4 blocks the paint touches are encoded again, the rest keep
their bytes. First use: the roads a mod draws, painted in the colour of the map's own roads, so a new road shows
where supply trucks already drive it (the roads a player sees are painted into these tiles, 2026-09-30).
"""
from __future__ import annotations

import math
import struct

from . import dxt, tgu1
from .tmst import Tmst, zipo_tile, zipo_unpack

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


def _tile_rect(store: Tmst, tile, bounds) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = bounds
    ax0, ay0, ax1, ay1 = store.area(tile)
    cw, ch = (x1 - x0) / store.grid_w, (y1 - y0) / store.grid_h
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
    x0, y0, x1, y1 = bounds
    side = 1 << (store.depth - 1)
    tw, th = (x1 - x0) / (store.grid_w * side), (y1 - y0) / (store.grid_h * side)
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
    return out, notes
