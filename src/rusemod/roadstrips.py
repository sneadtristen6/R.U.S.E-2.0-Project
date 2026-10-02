"""The roads the game draws from high up: the road model of a map pack's static meshes (`output\\staticmeshes.spkpc`,
a mesh pack like FORMATS.md §8, model `road`). The map's terrain settings (`mapterrain` in ZZ_GladPatchableWin.dat)
name it on every map: a static mesh `Road`, mode 128 (the strip of the `Route` road pieces: width 400, colour
dcdcdc64, stored B, G, R, A), from `DatasMap:\\Output\\StaticMeshes`. Proven in the game (2026-10-02, batch 12: every
vertex coloured and lifted): it is the road line seen from high up, the map's own and the new roads added here both;
up close the map's own textured road (grey, a dashed centre line) didn't change, so the close-up road is drawn by
something else, not found yet (T12, on hold). The scenery's `Route` pieces (rusemod.scenery.RoadPiece) are what the
map's tools built the model from.

The model is one draw call over the whole map, cut into parts by cases of CASE map units, one part per case:

    vertex    44 bytes: position (x, y, the ground's height), the road's direction (4 bytes, b / 255 x 2 - 1), the
              side it widens to (the same, flat), a width factor (f32: 1 where the road runs on, wider at a bend),
              colour (4 bytes), two f32 0, and (u, v): u -0.5, 0 or 0.5 across the road, v its width
    piece     each road piece is its own strip: two points, three vertices at each (u -0.5, 0, 0.5), 12 indices
              (SEGMENT) over the 6; a curved piece has more points (4,678 strips for D-Day's 4,693 pieces)
    part      48 bytes in the pack's fourth section: its box (6 f32: the vertices' bounds), u16 case, u16 pad,
              u32 first vertex, vertex count, first index, index count, u32 pad; a draw call's parts are listed by
              case, one each, its vertices and indices in that order with no gap; indices count from the buffer's
              start (u16, so the model holds at most 65,536 vertices)
    groups    the fifth section: u16 first part, u16 count, per draw call (the draw call's fifth word picks one)
    case      the cases are numbered along a curve (case_numbers) over the map's grid of CASE squares, skipping
              those off the map (checked on every part of the 28 maps that have the file)

The pack's header hash is MD5 of its first 16 bytes and bytes 0x20-0x2F. Rebuilt with nothing added, every shipped
file comes back byte for byte."""
from __future__ import annotations

import hashlib
import math
import struct

MEMBER = "output\\staticmeshes.spkpc"
MODEL = "road"
CASE = 81920.0          # map units a case of the static meshes is across (every map's `CaseSize`)
VERTEX = "TVertex__Position_3f__NormalIn01_4ubn__Normal2In01_4ubn__PSize_1f__Color0_col32__ArcLengths_2f__TexCoord0_2f"
STRIDE = 44
SEGMENT = (0, 4, 3, 0, 1, 4, 1, 5, 4, 1, 2, 5)  # a strip between two points' three vertices, as every shipped one
MOST = 65536            # vertices a model's u16 indices reach
WIDEST = 2.0            # a bend's width factor at most (the shipped ones reach 1.8)
HEADER = 0xC4
SECTIONS = ("names", "formats", "materials", "parts", "groups", "meshes", "draws", "ib_table")
_PART = struct.Struct("<6fHHIIIII")
_VTX = struct.Struct("<3f4B4Bf4B2f2f")


class StripError(ValueError):
    pass


def curve(order: int) -> list[tuple[int, int]]:
    """The squares of a 2**order grid in the order the static meshes number their cases."""
    pts = [(0, 0)]
    for n in range(1, order + 1):
        s = 1 << (n - 1)
        pts = ([(b, a) for a, b in pts] + [(a, b + s) for a, b in pts] + [(a + s, b + s) for a, b in pts]
               + [(2 * s - 1 - b, s - 1 - a) for a, b in pts])
    return pts


def case_numbers(nx: int, ny: int) -> dict[tuple[int, int], int]:
    """{(case x, case y): its number} for a map nx by ny cases across: along the curve, the squares off the map
    skipped."""
    order = max(0, math.ceil(math.log2(max(nx, ny, 1))))
    out: dict[tuple[int, int], int] = {}
    for x, y in curve(order):
        if x < nx and y < ny:
            out[(x, y)] = len(out)
    return out


def grid(bounds) -> tuple[int, int]:
    """The map's cases across and down, from its ground's bounds (x0, y0, x1, y1): on 6 maps the ground ends a little
    short of the grid, which still counts the whole last case."""
    x0, y0, x1, y1 = bounds[:4]
    return max(1, math.ceil((x1 - x0) / CASE - 0.01)), max(1, math.ceil((y1 - y0) / CASE - 0.01))


def _byte(v: float) -> int:
    return min(255, max(0, math.floor((v + 1.0) * 127.5 + 0.5)))


def _unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v) if n > 0 else None


def _flat_side(t) -> tuple[float, float, float]:
    s = _unit((t[1], -t[0]))
    return (s[0], s[1], 0.0) if s else (1.0, 0.0, 0.0)


def strips(lines: list, height_at) -> tuple[list[list[tuple]], int]:
    """Each road's points ((x, y, z), direction, side, width factor) as the road model holds them: a point at every
    piece's end (rusemod.scenery.road_pieces: the stickers' pieces), on the ground (`height_at(x, y)`, None off it),
    its direction along the road (at a joint, the two pieces' between), its side flat and square to that, its width
    factor 1 / cos(half the bend) so the strips on both sides of a joint keep the road's width. Returns (runs: lists
    of points, every two in a row a piece, the pieces left out because an end is off the ground)."""
    from .scenery import road_pieces
    runs, lost = [], 0
    for line in lines:
        pieces = road_pieces(line)
        if not pieces:
            continue
        flat = [(pieces[0].x0, pieces[0].y0)] + [(p.x1, p.y1) for p in pieces]
        zs = [height_at(x, y) for x, y in flat]
        lost += sum(1 for a, b in zip(zs, zs[1:]) if a is None or b is None)
        run: list = []
        for (x, y), z in zip(flat, zs):  # cut where the ground isn't: each stretch on it a run of its own
            if z is None:
                if len(run) > 1:
                    runs.append(run)
                run = []
            else:
                run.append((x, y, z))
        if len(run) > 1:
            runs.append(run)
    out = []
    for run in runs:
        ds = [_unit((b[0] - a[0], b[1] - a[1], b[2] - a[2])) or (1.0, 0.0, 0.0) for a, b in zip(run, run[1:])]
        pts = []
        for k, p in enumerate(run):
            if k == 0 or k == len(run) - 1:
                t, wide = ds[0] if k == 0 else ds[-1], 1.0
            else:
                t = _unit(tuple(a + b for a, b in zip(ds[k - 1], ds[k]))) or ds[k]
                side, piece_side = _flat_side(t), _flat_side(ds[k])
                cos = side[0] * piece_side[0] + side[1] * piece_side[1]
                wide = min(WIDEST, 1.0 / cos) if cos > 1.0 / WIDEST else WIDEST
            pts.append((p, t, _flat_side(t), wide))
        out.append(pts)
    return out, lost


class StaticMeshes:
    """A map pack's static meshes, read for adding road strips: the layout every shipped one has (the sections in
    order, no gaps, the road model's draw call stored as is with VERTEX, its parts listed by case, one each)."""

    def __init__(self, raw: bytes):
        raw = bytes(raw)
        if raw[:8] != b"MESHPCPC" or struct.unpack_from("<I", raw, 8)[0] != 4:
            raise StripError("not a version-4 mesh pack")
        if struct.unpack_from("<I", raw, 0x0C)[0] != len(raw):
            raise StripError("the mesh pack's size isn't its length")
        self.raw = raw
        self.sections = [list(struct.unpack_from("<III", raw, 0x34 + 12 * i)) for i in range(len(SECTIONS))]
        self.ib_data = list(struct.unpack_from("<II", raw, 0x94))
        self.vb_table = list(struct.unpack_from("<III", raw, 0x9C))
        self.vb_data = list(struct.unpack_from("<II", raw, 0xA8))
        at = HEADER
        self.gaps = []  # before each part of the file: nothing, or filler (`~`) up to a multiple of 4
        regions = [(off, size) for off, size, _n in self.sections] + [
            (self.vb_table[0], self.vb_table[1]), tuple(self.ib_data), tuple(self.vb_data)]
        for name, (off, size) in zip(SECTIONS + ("vertex-buffer table", "index data", "vertex data"), regions):
            if not (off == at or (at < off < at + 4 and off % 4 == 0)):
                raise StripError(f"the mesh pack's {name} aren't where this writer expects them")
            self.gaps.append(raw[at:off])
            at = off + size
        ib_table = self.sections[7][0]
        if at != len(raw) or struct.unpack_from("<5I", raw, 0xB0) != (ib_table, 0, 0, ib_table, 0):
            raise StripError("the mesh pack's layout isn't one this writer knows")
        if struct.unpack_from("<4I", raw, 0x20) != (0, self.ib_data[0], self.ib_data[0], len(raw) - self.ib_data[0]):
            raise StripError("the mesh pack's two halves aren't where this writer expects them")
        fo, _fs, fc = self.sections[1]
        self.formats = [raw[fo + 4 + 256 * i:fo + 260 + 256 * i].split(b"\0", 1)[0].decode("latin-1") for i in range(fc)]
        mo, _ms, mc = self.sections[5]
        self.meshes = [struct.unpack_from("<HH", raw, mo + 4 * i) for i in range(mc)]
        do, _ds, dc = self.sections[6]
        self.draws = [list(struct.unpack_from("<6H", raw, do + 12 * i)) for i in range(dc)]
        io, _is, ic = self.sections[7]
        self.ibs = [list(struct.unpack_from("<IIIHH", raw, io + 16 * i)) for i in range(ic)]
        self.vbs = [list(struct.unpack_from("<IIIHH", raw, self.vb_table[0] + 16 * i)) for i in range(self.vb_table[2])]
        for table, data in ((self.ibs, self.ib_data), (self.vbs, self.vb_data)):
            end = 0
            for off, size, *_rest in table:
                if off != end:
                    raise StripError("the mesh pack's buffers aren't one after another")
                end = off + size
            if end != data[1]:
                raise StripError("the mesh pack's buffers don't fill their data")
        go, _gs, gc = self.sections[4]
        self.groups = [list(struct.unpack_from("<HH", raw, go + 4 * i)) for i in range(gc)]
        po, _ps, pc = self.sections[3]
        self.parts = [list(_PART.unpack_from(raw, po + 48 * i)) for i in range(pc)]
        self.model = self._find_model(MODEL)  # (its record's place in the file, its mesh number) or None

    def _find_model(self, name: str):
        no, ns, _nc = self.sections[0]
        found = []

        def walk(pos, end, prefix, depth=0):
            while pos + 8 <= end and depth < 64:
                head, sibling = struct.unpack_from("<II", self.raw, pos)
                if head == 0:
                    stop = self.raw.index(b"\0", pos + 40)
                    if (prefix + self.raw[pos + 40:stop].decode("latin-1")).lower() == name:
                        found.append((pos, struct.unpack_from("<H", self.raw, pos + 36)[0]))
                else:
                    stop = self.raw.index(b"\0", pos + 8)
                    if head >= stop + 1 - pos:
                        walk(pos + head, end, prefix + self.raw[pos + 8:stop].decode("latin-1"), depth + 1)
                if sibling == 0:
                    return
                pos += sibling
        if struct.unpack_from("<I", self.raw, no)[0] == 0x0A:
            walk(no + 10, no + ns, "")
        return found[0] if found else None

    def road_draw(self) -> int:
        """The road model's draw call, checked to be one this writer can add to."""
        if self.model is None:
            raise StripError("the map's static meshes have no road model")
        first, count = self.meshes[self.model[1]]
        if count != 1:
            raise StripError("the map's road model has more than one draw call")
        d = first
        _w, _mat, ib, vb, group, _pad = self.draws[d]
        if self.formats[self.vbs[vb][3]].rsplit("/", 1)[-1] != VERTEX or self.vbs[vb][4] or self.ibs[ib][4]:
            raise StripError("the map's road model is stored in a way this writer doesn't know")
        if group >= len(self.groups):
            raise StripError("the map's road model has no list of parts")
        g0, gn = self.groups[group]
        cases = [p[6] for p in self.parts[g0:g0 + gn]]
        if cases != sorted(set(cases)):
            raise StripError("the map's road parts aren't one per case in order")
        return d

    def buffers(self, d: int) -> tuple[bytes, list[int]]:
        """The draw call's vertices (as stored) and indices."""
        _w, _mat, ib, vb, _g, _p = self.draws[d]
        voff, vsize = self.vbs[vb][:2]
        ioff, isize, icount = self.ibs[ib][:3]
        vbytes = self.raw[self.vb_data[0] + voff:self.vb_data[0] + voff + vsize]
        idx = list(struct.unpack_from(f"<{icount}H", self.raw, self.ib_data[0] + ioff))
        return vbytes, idx

    def with_strips(self, by_case: dict[int, list[bytes]]) -> bytes:
        """The pack with each case's new strips (6 vertices each, as bytes) added to the road model: its parts rebuilt
        in case order (the old vertices first, then the new), every index counted again, the tables, the header and
        the model's box made to match. Nothing to add: the same bytes."""
        if not by_case:
            return self.raw
        d = self.road_draw()
        _w, _mat, ib, vb, group, _pad = self.draws[d]
        g0, gn = self.groups[group]
        old = {p[6]: p for p in self.parts[g0:g0 + gn]}
        vbytes, idx = self.buffers(d)
        pad = (old[min(old)][7], old[min(old)][12]) if old else (0xDDDD, 0xDDDDCD00)
        verts, ids, parts = [], [], []
        for case in sorted(set(old) | set(by_case)):
            v0, i0 = len(verts), len(ids)
            box = None
            if case in old:
                p = old[case]
                fv, nv, fi, ni = p[8:12]
                mine = idx[fi:fi + ni]
                if any(not fv <= k < fv + nv for k in mine):
                    raise StripError("a road part's indices reach past its vertices")
                verts += [vbytes[STRIDE * k:STRIDE * (k + 1)] for k in range(fv, fv + nv)]
                ids += [k - fv + v0 for k in mine]
                box = list(p[:6])
            for k in range(0, len(by_case.get(case, [])), 6):
                base = len(verts)
                verts += by_case[case][k:k + 6]
                ids += [base + j for j in SEGMENT]
            for v in verts[v0 + (old[case][9] if case in old else 0):]:
                x, y, z = struct.unpack_from("<3f", v)
                box = [x, y, z, x, y, z] if box is None else [min(box[0], x), min(box[1], y), min(box[2], z),
                                                              max(box[3], x), max(box[4], y), max(box[5], z)]
            p = old.get(case)
            parts.append([*box, case, p[7] if p else pad[0], v0, len(verts) - v0, i0, len(ids) - i0,
                          p[12] if p else pad[1]])
        if len(verts) > MOST:
            raise StripError(f"the road model would hold {len(verts):,} vertices, past the {MOST:,} its indices reach")
        new_vb, new_ib = b"".join(verts), struct.pack(f"<{len(ids)}H", *ids)
        # the parts table, every group's own place in it again
        all_parts, groups = [], []
        for gi, (f0, fn) in enumerate(self.groups):
            groups.append([len(all_parts), len(parts) if gi == group else fn])
            all_parts += parts if gi == group else self.parts[f0:f0 + fn]
        # the buffers, one after another, the road's replaced
        ibs, ib_blobs = [], []
        for i, (off, size, count, one, flags) in enumerate(self.ibs):
            blob = new_ib if i == ib else self.raw[self.ib_data[0] + off:self.ib_data[0] + off + size]
            ibs.append([sum(len(b) for b in ib_blobs), len(blob), len(ids) if i == ib else count, one, flags])
            ib_blobs.append(blob)
        vbs, vb_blobs = [], []
        for i, (off, size, count, fmt, flags) in enumerate(self.vbs):
            blob = new_vb if i == vb else self.raw[self.vb_data[0] + off:self.vb_data[0] + off + size]
            vbs.append([sum(len(b) for b in vb_blobs), len(blob), len(verts) if i == vb else count, fmt, flags])
            vb_blobs.append(blob)
        names = bytearray(self._section(0))
        if self.model is not None:  # the model's box, grown to hold the new strips
            at = self.model[0] - self.sections[0][0] + 8
            box = list(struct.unpack_from("<6f", names, at))
            for p in parts:
                box = [min(box[0], p[0]), min(box[1], p[1]), min(box[2], p[2]),
                       max(box[3], p[3]), max(box[4], p[4]), max(box[5], p[5])]
            struct.pack_into("<6f", names, at, *box)
        blobs = [bytes(names), self._section(1), self._section(2), b"".join(_PART.pack(*p) for p in all_parts),
                 b"".join(struct.pack("<HH", *g) for g in groups), self._section(5), self._section(6),
                 b"".join(struct.pack("<IIIHH", *t) for t in ibs), b"".join(struct.pack("<IIIHH", *t) for t in vbs),
                 b"".join(ib_blobs), b"".join(vb_blobs)]
        body, starts = bytearray(self.raw[:HEADER]), []
        for gap, blob in zip(self.gaps, blobs):
            if gap:  # filler as the shipped files have it: `~` up to a multiple of 4
                body += gap if (len(body) + len(gap)) % 4 == 0 else b"~" * (-len(body) % 4)
            starts.append(len(body))
            body += blob
        for i in range(len(SECTIONS)):
            count = len(all_parts) if i == 3 else self.sections[i][2]
            struct.pack_into("<III", body, 0x34 + 12 * i, starts[i], len(blobs[i]), count)
        struct.pack_into("<III", body, 0x9C, starts[8], len(blobs[8]), len(vbs))
        struct.pack_into("<II", body, 0x94, starts[9], len(blobs[9]))
        struct.pack_into("<II", body, 0xA8, starts[10], len(blobs[10]))
        struct.pack_into("<5I", body, 0xB0, starts[7], 0, 0, starts[7], 0)
        struct.pack_into("<I", body, 0x0C, len(body))
        struct.pack_into("<4I", body, 0x20, 0, starts[9], starts[9], len(body) - starts[9])
        body[0x10:0x20] = hashlib.md5(bytes(body[:0x10]) + bytes(body[0x20:0x30])).digest()
        return bytes(body)

    def _section(self, i: int) -> bytes:
        off, size, _n = self.sections[i]
        return self.raw[off:off + size]


def add_roads(raw: bytes, lines: list, height_at, bounds) -> tuple[bytes, list[str]]:
    """The map's static meshes (`raw`) with `lines` (each a new road's map points, in order) added to its road model
    as strips on the ground (`height_at(x, y)`: the ground's height, None off it), in the look of the map's own (its
    colour and width copied), each piece in the part of the case its middle lies in (`bounds`: the ground's x0, y0,
    x1, y1). Returns (new bytes, notes)."""
    pack = StaticMeshes(raw)
    d = pack.road_draw()
    vbytes, _idx = pack.buffers(d)
    if len(vbytes) < STRIDE:
        raise StripError("the map's road model has no vertex to copy its look from")
    look = _VTX.unpack_from(vbytes, 0)
    colour, width = look[12:16], look[19]
    runs, lost = strips(lines, height_at)
    nx, ny = grid(bounds)
    number = case_numbers(nx, ny)
    by_case: dict[int, list[bytes]] = {}
    pieces = 0
    for run in runs:
        for a, b in zip(run, run[1:]):
            mx, my = (a[0][0] + b[0][0]) / 2, (a[0][1] + b[0][1]) / 2
            cx = min(nx - 1, max(0, int((mx - bounds[0]) // CASE)))
            cy = min(ny - 1, max(0, int((my - bounds[1]) // CASE)))
            out = by_case.setdefault(number[(cx, cy)], [])
            for (x, y, z), t, side, wide in (a, b):
                for u in (-0.5, 0.0, 0.5):
                    out.append(_VTX.pack(x, y, z, _byte(t[0]), _byte(t[1]), _byte(t[2]), 128,
                                         _byte(side[0]), _byte(side[1]), _byte(side[2]), 128, wide, *colour,
                                         0.0, 0.0, u, width))
            pieces += 1
    notes = []
    if lost:
        notes.append(f"{lost} road piece(s) off the ground left out of the close-up strips")
    if not pieces:
        return bytes(raw), notes
    new = pack.with_strips(by_case)
    notes.insert(0, f"close-up strips: {pieces} road piece(s) added to the map's road model, in {len(by_case)} case(s)")
    return new, notes


def draw_roads(read, path_of, lines: list) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): `lines` added to the map pack's road model, on its ground (`output\\highdef.tms`).
    `read(name)` gives a member's bytes (the build's chain: a reshaped ground counts) or None, `path_of(name)` its full
    path in the pack. A map with no static meshes (Alpha, Gam_Ostfriesland, Gamma, Robert) draws no road up close,
    its own neither: nothing to add there."""
    if not lines:
        return {}, []
    raw = read(MEMBER)
    if raw is None:
        return {}, ["this map has no road model: its roads, the new ones too, show from afar only"]
    mesh = read("output\\highdef.tms")
    if mesh is None:
        raise StripError("the map has no ground mesh to lay the road strips on")
    from .bridges import Ground
    from .tms import Tms
    tms = Tms(mesh)
    new, notes = add_roads(raw, lines, Ground(tms).height_at, (tms.bounds[0], tms.bounds[1], tms.bounds[3], tms.bounds[4]))
    return ({path_of(MEMBER): new} if new != raw else {}), notes
