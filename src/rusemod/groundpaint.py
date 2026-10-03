"""Painting on a map's ground picture: its highdef and lowdef texture tiles (rusemod.tmst; FORMATS.md §6), a pyramid
of 512x512 DXT1 tiles over the map's cells. A painted tile is written back as a plain ZIPO DXT1 tile, which the game
draws (proven with plain tiles, 2026-09-29); only the 4x4 blocks the paint touches are encoded again, the rest keep
their bytes. First use: the roads a mod draws, painted in the colour of the map's own roads, so a new road shows
where supply trucks already drive it (the roads a player sees from afar are painted into these tiles, 2026-09-30).

The map's close-up map (`output\\div_map.tgv_pc`, the "texture diversity", one DXT5 picture over the whole grid of
cells) marks every map's own roads (alpha higher, red lower than the ground beside: all 31 maps with roads), and
paint_detail gives a new road the same mark. The mark alone doesn't draw a road up close (batch 5, 2026-10-01): the
map's asphalt stickers do (scenery.road_decals, TESTS.md T12, proven 2026-10-02); measured as the map's own roads
make it (road_profile), it lets them blend in. The checks here are on the files' bytes only
(tests/test_groundpaint.py), never proof of what the game shows.
"""
from __future__ import annotations

import json
import math
import statistics
import struct
from dataclasses import dataclass
from pathlib import Path

from . import dxt, tgu1
from .tmst import Tgv, Tmst, zipo_pack, zipo_tile, zipo_unpack

LODS = ("highdef", "lowdef")
ROAD_WIDTH = 1800.0     # map units (about 7 m): a road's painted width
FEATHER = 0.6           # of the half-width: how far the edge fades into the ground
# A road that keeps its trees, where it runs through a wood: painted this share as strongly, its colour this much of
# the way to grey (the owner, 2026-10-03: "when it's in the trees, it should be invisible. Or less visible, more
# gray"). A road that clears its trees is painted as the map's own roads through woods are, at every level.
UNDER_TREES = 0.35
UNDER_TREES_GREY = 0.6

PROFILE_STEP = 100.0    # map units between the samples of a road's cross-section (RoadProfile)
PROFILE_SAMPLES = 31    # 0 to 3,000 from the road's line
PROFILE_FIELD = 5       # the last samples (2,600 to 3,000): the ground beside the road
PROFILE_MOST = 300      # the map's road pieces measured


class PaintError(ValueError):
    pass


@dataclass
class RoadProfile:
    """How the map's own roads look across, measured on its road pieces (road_profile): at k * PROFILE_STEP from a
    road's line, `tile[k]` the median colour of the finest ground tiles and `weight[k]` how much of it a new road
    takes (1 in the road, falling to 0 where the map's roads meet the ground beside them, their shoulders between),
    and `detail[k]` the median change (r, g, b, alpha) the map's roads make in the close-up map against the ground
    beside them (None when the map has no close-up map to measure). On D-Day (313 pieces): the road 157, 139, 110 out
    to 450, a brown shoulder to about 1,500; in the close-up map alpha +8 and green -8 in the road, gone by 2,000."""
    tile: list
    weight: list
    detail: list | None
    pieces: int

    def reach(self, what: str = "tile") -> float:
        """How far from a road's line its paint (`tile`) or its close-up mark (`detail`) goes, in map units."""
        values = self.weight if what == "tile" else [max(abs(c) for c in d) >= 1 for d in self.detail or []]
        last = max((k for k, v in enumerate(values) if v), default=-1)
        return (last + 1) * PROFILE_STEP


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


def _tgu1_blocks(payload: bytes, cache=None) -> bytes:
    """A TGU1 payload's DXT1 blocks. Decoding one of the game's 512-pixel tiles takes about a second; with `cache` (a
    folder) the blocks are kept there, named by a fingerprint of the payload itself, so each tile is decoded once."""
    if cache is None:
        return tgu1.decode(payload)
    import hashlib
    import zlib
    kept = Path(cache) / f"tgu1-{hashlib.blake2b(payload, digest_size=20).hexdigest()}.bin"
    try:
        return zlib.decompress(kept.read_bytes())
    except (OSError, zlib.error):
        pass  # not kept yet (or unreadable): decoded again
    blocks = tgu1.decode(payload)
    try:
        kept.parent.mkdir(parents=True, exist_ok=True)
        part = kept.with_suffix(".part")
        part.write_bytes(zlib.compress(blocks, 1))
        part.replace(kept)  # whole or not at all: two builds at once never read half a file
    except OSError:
        pass
    return blocks


def _blocks(store: Tmst, tile, cache=None) -> tuple[bytearray, int, int]:
    """A tile's DXT1 blocks and its width and height in pixels, from the payload itself: never assumed (the whole-map
    overview tile is 256 wide on Blitz and 1024 x 512 on D-Day, the others 512) and never taken from the TGV
    header, which can say more than it holds. `cache`: _tgu1_blocks's."""
    tex = store.texture(tile)
    payload = tex.payload(0)
    if payload[:4] == b"TGU1":
        head = tgu1.Header.parse(payload)
        w, h, blocks = head.width * 4, head.height * 4, bytearray(_tgu1_blocks(payload, cache))
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


def road_colour(store: Tmst, bounds, pieces: list[tuple], most: int = 40, cache=None) -> tuple[int, int, int]:
    """The colour of the map's own roads: its pictures' pixels at the middles of up to `most` road pieces
    (rusemod.scenery Scenery.roads), from the finest level; a grey-brown when the map has no road. `cache`:
    _tgu1_blocks's."""
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
        blocks, w, h = _blocks(store, tile, cache)
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


def _detail_reader(raw: bytes, bounds):
    """A close-up map's (r, g, b, alpha) at a map point (None off it), or None when it can't be read (not DXT5 ZIPO)."""
    tex = Tgv(raw)
    payload = tex.payload(0)
    if not tex.format.upper().startswith("DXT5") or payload[:4] != b"ZIPO":
        return None
    blocks, w, h = zipo_unpack(payload), tex.width, tex.height
    x0, y0, x1, y1 = bounds

    def at(x, y):
        px, py = int((x - x0) / (x1 - x0) * w), int((y - y0) / (y1 - y0) * h)
        if not (0 <= px < w and 0 <= py < h):
            return None
        k = (py // 4) * (w // 4) + px // 4
        rgb, alpha = dxt.dxt5_block(bytes(blocks[16 * k:16 * k + 16]))
        i = (py % 4) * 4 + px % 4
        return rgb[i] + (alpha[i],)
    return at


def road_profile(store: Tmst, bounds, pieces: list[tuple], detail: bytes | None = None, detail_bounds=None,
                 most: int = PROFILE_MOST) -> RoadProfile | None:
    """The map's own roads across (RoadProfile), from the middles of up to `most` of its road pieces (rusemod.scenery
    Scenery.roads), both sides, in the finest tiles of `store` (over `bounds`) and in the close-up map `detail` (over
    `detail_bounds`, grid_bounds). None when the map has too few roads, or its roads don't stand out in its tiles."""
    picks = pieces[::max(1, len(pieces) // most)][:most]
    if len(picks) < 20:
        return None
    x0, y0, _x1, _y1 = bounds
    side = 1 << (store.depth - 1)
    cw, ch = _cells(store, bounds)
    tw, th = cw / side, ch / side
    tiles: dict = {}

    def colour(x, y):
        tx, ty = int((x - x0) // tw), int((y - y0) // th)
        if (tx, ty) not in tiles:
            try:
                tiles[(tx, ty)] = _blocks(store, store.tile(0, tx, ty))
            except (KeyError, PaintError):
                tiles[(tx, ty)] = None
        got = tiles[(tx, ty)]
        if got is None:
            return None
        blocks, w, h = got
        px, py = int((x - x0 - tx * tw) / tw * w), int((y - y0 - ty * th) / th * h)
        k = (py // 4) * (w // 4) + px // 4
        return dxt.block_pixels(bytes(blocks[8 * k:8 * k + 8]))[(py % 4) * 4 + px % 4]
    mark = _detail_reader(detail, detail_bounds) if detail is not None and detail_bounds is not None else None
    seen_tile = [[] for _ in range(PROFILE_SAMPLES)]
    seen_mark = [[] for _ in range(PROFILE_SAMPLES)]
    for p in picks:
        x = 0.125 * p[0] + 0.375 * p[2] + 0.375 * p[4] + 0.125 * p[6]  # the Bézier's middle, and its direction
        y = 0.125 * p[1] + 0.375 * p[3] + 0.375 * p[5] + 0.125 * p[7]
        dx, dy = p[6] + p[4] - p[2] - p[0], p[7] + p[5] - p[3] - p[1]
        n = math.hypot(dx, dy)
        if n == 0:
            continue
        nx, ny = -dy / n, dx / n
        for k in range(PROFILE_SAMPLES):
            for s in ((1,) if k == 0 else (1, -1)):
                sx, sy = x + nx * s * k * PROFILE_STEP, y + ny * s * k * PROFILE_STEP
                c = colour(sx, sy)
                if c is not None:
                    seen_tile[k].append(c)
                if mark is not None and (m := mark(sx, sy)) is not None:
                    seen_mark[k].append(m)
    if any(len(v) < 20 for v in seen_tile):
        return None
    med = [tuple(statistics.median(c[i] for c in v) for i in range(3)) for v in seen_tile]
    field = tuple(statistics.median(c[i] for v in seen_tile[-PROFILE_FIELD:] for c in v) for i in range(3))
    road = math.dist(med[0], field)
    if road < 12:  # the map's roads are hardly there in its tiles: nothing to copy
        return None
    weight, ended = [], False
    for m in med:
        w = min(1.0, math.dist(m, field) / road)
        ended = ended or w < 0.1
        weight.append(0.0 if ended else round(w, 3))
    delta = None
    if mark is not None and all(len(v) >= 20 for v in seen_mark):
        mmed = [tuple(statistics.median(c[i] for c in v) for i in range(4)) for v in seen_mark]
        mfield = tuple(statistics.median(c[i] for v in seen_mark[-PROFILE_FIELD:] for c in v) for i in range(4))
        delta, ended = [], False
        for m in mmed:
            d = tuple(round(m[i] - mfield[i], 1) for i in range(4))
            ended = ended or max(abs(c) for c in d) < 1
            delta.append((0.0,) * 4 if ended else d)
    return RoadProfile([tuple(round(c) for c in m) for m in med], weight, delta, len(picks))


def _across(profile_values, d: float, pw: float):
    """The profile samples a pixel `pw` wide at `d` from a road's line covers: (index, share) pairs, so a pixel coarser
    than the profile's steps (the far levels) takes their mean."""
    n = max(1, min(16, math.ceil(pw / PROFILE_STEP)))
    out = []
    for j in range(n):
        k = int(abs(d - pw / 2 + (j + 0.5) * pw / n) / PROFILE_STEP + 0.5)
        if k < len(profile_values):
            out.append(k)
    return out, n


def _under_trees(old: tuple, new: tuple) -> tuple:
    """A road pixel under trees: `new` (the road's colour there) turned greyer and only partly laid over `old`."""
    grey = sum(new) / 3
    return tuple(max(0, min(255, round(o + (n + (grey - n) * UNDER_TREES_GREY - o) * UNDER_TREES))) for o, n in zip(old, new))


def paint_lines(store: Tmst, bounds, lines: list[list[tuple[float, float]]], colour: tuple[int, int, int],
                width: float = ROAD_WIDTH, profile: RoadProfile | None = None, shaded=None,
                cache=None) -> dict[int, bytes]:
    """`lines` (lists of map points) painted `width` wide in `colour` on every tile of `store` they cross, at every
    level; returns {tile index: new tile record} for Tmst.members. The edge fades over FEATHER of the half-width,
    and a line thinner than a pixel (the coarse levels) is painted faint rather than not at all. With `profile` (the
    map's own roads across, road_profile) a line is painted as they are instead: their colour, width and shoulders,
    blended into the ground beside as theirs are. `shaded(x, y, i)`: true where the pixel at (x, y), whose nearest line
    is lines[i], lies under trees (a road that keeps its trees, in a wood): painted fainter and greyer there.
    `cache`: _tgu1_blocks's."""
    owner = [i for i, line in enumerate(lines) for _ in zip(line, line[1:])]  # each segment's line
    segs = _segments(lines)
    if not segs:
        return {}
    index = {s: k for k, s in enumerate(segs)}
    half = width / 2
    reach = profile.reach() if profile is not None else half * (1 + FEATHER)
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
                    blocks = _blocks(store, tile, cache)[0]
                k = by * nx + bx
                pixels = dxt.block_pixels(bytes(blocks[8 * k:8 * k + 8]))
                changed = False
                for i in range(16):
                    px = cx0 + (i % 4 + 0.5) * pw
                    py = cy0 + (i // 4 + 0.5) * ph
                    d, s_at = min((_dist(px, py, s), s) for s in here)
                    under = shaded is not None and shaded(px, py, owner[index[s_at]])
                    old = pixels[i]
                    if profile is not None:  # the map's own road across, as wide as this pixel
                        ks, n = _across(profile.weight, d, pw)
                        r, g, b = pixels[i]
                        add = [0.0, 0.0, 0.0]
                        for j in ks:
                            share = profile.weight[j]
                            for c, v in enumerate((r, g, b)):
                                add[c] += share * (profile.tile[j][c] - v)
                        if any(profile.weight[j] for j in ks):
                            pixels[i] = tuple(max(0, min(255, round(v + a / n))) for v, a in zip((r, g, b), add))
                            if under:
                                pixels[i] = _under_trees(old, pixels[i])
                            changed = True
                        continue
                    a = max(0.0, min(1.0, (half + soft / 2 - d) / soft)) * faint
                    if a > 0:
                        r, g, b = pixels[i]
                        pixels[i] = (round(r + (colour[0] - r) * a), round(g + (colour[1] - g) * a),
                                     round(b + (colour[2] - b) * a))
                        if under:
                            pixels[i] = _under_trees(old, pixels[i])
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
                 width: float = ROAD_WIDTH, profile: RoadProfile | None = None) -> tuple[bytes, list[str]]:
    """`lines` marked in the close-up map (`output\\div_map.tgv_pc`, one DXT5 picture stretched over `bounds`, the
    ground's whole grid: grid_bounds): the weights by which the ground shaders blend their detail textures over the
    tiles near the camera (its channels are data, not colours: blue is 24 on every map). The map's own roads are
    marked there (alpha higher, red lower than the ground beside), which keeps their colour from the tiles showing up
    close; new roads get the median of all four channels along the map's road pieces, `width` wide (the map's own
    run 2 to 3 pixels wide: DETAIL_WIDER). With `profile` (road_profile) a new road changes it as the map's own roads
    do instead: their median change against the ground beside, at each distance from the line, added to what's there
    (on D-Day the old way marked twice as strong and twice as wide: a pale band beside new roads up close, the owner's
    shots of 2026-10-02). Returns (the new record, notes), or (b"", notes) when there's nothing to paint."""
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
    change = profile.detail if profile is not None and profile.detail and profile.reach("detail") > 0 else None
    reach = profile.reach("detail") if change else half + soft
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
            if change:  # the map's own roads' change, as wide as this pixel, added to what's there
                ks, n = _across(change, min(_dist(px, py, s) for s in near), pw)
                add = [sum(change[j][c] for j in ks) / n for c in range(4)]
                if any(round(v) for v in add):
                    r, g, b = rgb[i]
                    rgb[i] = tuple(max(0, min(255, round(v + a))) for v, a in zip((r, g, b), add[:3]))
                    alpha[i] = max(0, min(255, round(alpha[i] + add[3])))
                    changed = True
                continue
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
    how = (f"as the map's own roads change it (alpha {change[0][3]:+.0f} in the road, to {reach:,.0f} from it)"
           if change else f"in the map's own road look {look}")
    return _tgv_with_payload(raw, zipo_pack(bytes(blocks))), [f"close-up map: {painted} block(s) painted, {how}"]


PROFILE_KEPT = 1   # the kept profiles' format: a new one means they're all measured again


def map_road_profile(read, pieces: list[tuple], cache=None) -> RoadProfile | None:
    """road_profile for a map pack (`read(member)`: its files as the build has them): its finest highdef tiles and its
    close-up map. None when it can't be measured.

    Measuring unpacks a couple of hundred of the map's tiles: half of a build's time on M03_Italie (361 of 715 seconds,
    2026-10-03). With `cache` (a folder) the answer is kept there, named by a fingerprint of everything it's measured
    from (the tiles, the close-up map, the ground mesh and the road pieces, as the build has them: a reshaped ground
    or new road pieces give another name), so a map is measured once."""
    mesh = read("output\\highdef.tms")
    index, chunk = read("output\\highdef.tmst_pc"), read("output\\highdef.tmst_chunk_pc")
    if mesh is None or index is None or chunk is None or not pieces:
        return None
    detail = read(DETAIL)
    kept = None
    if cache is not None:
        import hashlib
        h = hashlib.blake2b(digest_size=20)
        for part in (f"v{PROFILE_KEPT}".encode(), mesh, index, chunk, detail or b"",
                     struct.pack(f"<{8 * len(pieces)}d", *(v for p in pieces for v in p[:8]))):
            h.update(struct.pack("<Q", len(part)))
            h.update(part)
        kept = Path(cache) / f"road-profile-{h.hexdigest()}.json"
        try:
            got = json.loads(kept.read_text(encoding="utf-8"))
            if got is None:
                return None
            return RoadProfile([tuple(c) for c in got["tile"]], got["weight"],
                               [tuple(d) for d in got["detail"]] if got["detail"] is not None else None, got["pieces"])
        except (OSError, ValueError, KeyError, TypeError):
            pass  # not kept yet (or unreadable): measured again
    try:
        profile = road_profile(Tmst(index, chunk), map_bounds(mesh), pieces, detail, grid_bounds(mesh))
    except (PaintError, ValueError, KeyError, struct.error):
        return None
    if kept is not None:
        try:
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_text(json.dumps(None if profile is None else
                                       {"tile": profile.tile, "weight": profile.weight, "detail": profile.detail,
                                        "pieces": profile.pieces}), encoding="utf-8")
        except OSError:
            pass  # not kept: measured again next time
    return profile


def paint_roads(read, path_of, lines: list[list[tuple[float, float]]], pieces: list[tuple],
                width: float = ROAD_WIDTH, profile: RoadProfile | None = None, shaded=None,
                cache=None) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): `lines` painted on both tile sets of a map pack, in its roads' colour, or as its
    roads are across with `profile` (map_road_profile). `read(name)` gives a member's bytes (the build's chain) or
    None, `path_of(name)` its full path in the pack; `pieces` are the map's road pieces (for the colour); `shaded` as
    paint_lines has it (under trees: fainter and greyer); `cache`: a folder where decoded tiles are kept
    (_tgu1_blocks)."""
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
            colour = road_colour(store, bounds, pieces, cache=cache)
        tiles = paint_lines(store, bounds, lines, colour, width, profile, shaded, cache)
        if tiles:
            out.update(store.members(tiles))
        notes.append(f"{lod}: {len(tiles)} tile(s) painted")
    if profile is not None:
        notes.insert(0, f"painted as the map's own roads are across (from {profile.pieces} of its road pieces): "
                        f"{profile.tile[0]} in the middle, shoulders to {profile.reach():,.0f} from the line")
    elif colour is not None:
        notes.insert(0, f"road colour {colour}")
    # the close-up map (paint_detail) is drawn by build.draw_new_roads, which also keeps its copy in ZZ_Win.dat
    return out, notes
