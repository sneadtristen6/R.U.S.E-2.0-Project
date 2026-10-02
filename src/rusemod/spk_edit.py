"""Write 3D model packs (.spk, and the maps' output\\staticmeshes.spkpc): rebuild one, copy models between packs,
replace a buffer. The reader is rusemod.spk; the layout is in its docstring and FORMATS.md §8.

DomesticNukes and his Claude, 2026-10-02. Checked on every pack the game ships (tools/verify_spk_write.py): the 82
packs in ZZ_Win.dat and the 33 maps' static-mesh packs (115) rebuild byte for byte, and the German skirmish pack's
74 models copied into the US one read back exactly as they were.

What the game checks when it opens a pack: `MESH` `PCPC`, version 4, and the 16 bytes at 0x10 = MD5 of the file's
first 16 bytes followed by bytes 0x20-0x2F (true of every shipped pack); and that the two (offset, size) pairs at
0x20 and 0x28 end inside the file. Those pairs are (0, start of the buffer data) and (start of the buffer data, its size);
0x30 is the model count. The header is 0xC4 bytes; at 0xB0 (offset, size, count) and 0xBC (offset, size) are the
skeleton records and their data (used by the maps' HQ-and-sky packs and the skeleton packs; empty elsewhere).

Layout rules the rebuild follows (all 104 packs): sections in the order names, formats, materials, two more
(empty except in the static-mesh packs), meshes, draw calls, skeleton records, skeleton data, the index-buffer table,
the vertex-buffer table, the index data, the vertex data, the file ending there. A section that isn't empty starts
on a 4-byte boundary, the gap filled with 0x7E; an empty one sits where the last one ended. Each buffer inside the
data starts on a 4-byte boundary (0x7E between). The name table is a trie (rusemod.spk), its entries padded to an
even length with zeros; siblings keep the pack's order, which is folder by folder (us_1\\ before us_10\\).

The maps' static meshes (the baked road and bridges): their two extra sections are decoded (see the notes above
`read_chunks`), and `add_road_pieces` adds Route pieces to the road the game draws up close.

Not done yet: skeletons (a model with a skeleton record can't be copied), the animation and proxy packs a unit
also needs, and re-encoding compressed vertex buffers (a copy keeps them as they are; new geometry goes in stored
as is, as most scenery is).
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field

from .ndf import Ndf, Value, _read_value
from .spk import FORMAT_NAME, MAGIC, SpkError

HEADER = 0xC4
FILL = b"\x7e"
NO_SKELETON = 0xCDCD
_SECTIONS = ("names", "formats", "materials", "extra1", "extra2", "meshes", "draws", "ib_table")
_REF_OBJECT = 0xBBBBBBBB


def header_hash(head: bytes) -> bytes:
    """The 16 bytes the game expects at 0x10: MD5 of bytes 0-15 and 0x20-0x2F of the header."""
    return hashlib.md5(bytes(head[0:16]) + bytes(head[0x20:0x30])).digest()


@dataclass
class Model:
    """One entry of the name table."""
    name: bytes               # the path as stored (lowercase in every shipped pack)
    box: tuple                # min x, y, z, max x, y, z
    flags: int
    mesh: int
    skeleton: int = NO_SKELETON


@dataclass
class Buffer:
    """An index or vertex buffer: its table row (count, the u16 after it, flags) and its bytes."""
    count: int
    kind: int                 # index buffers: 1; vertex buffers: the vertex format number
    flags: int                # 0xC000 compressed, 0 stored as is
    data: bytes


@dataclass
class Pack:
    version: int
    models: list[Model]
    formats: list[str]
    formats_raw: bytes        # kept so an unchanged pack writes back exactly (name padding)
    materials: Ndf | None     # None when the section is empty (skeleton packs)
    materials_raw: bytes      # written back as is unless a material was added
    material_count: int
    extra1: tuple             # (bytes, count): empty except in the static-mesh packs
    extra2: tuple
    meshes: list[tuple]       # (first draw call, draw-call count)
    draws: list[list]         # six u16: ?, material, index buffer, vertex buffer, 0xFFFF, 0xCDCD
    skel_records: tuple       # (bytes, count)
    skel_data: bytes
    ibs: list[Buffer]
    vbs: list[Buffer]
    tail_c0: bytes = b"\0\0\0\0"
    _formats_dirty: bool = field(default=False, repr=False)
    _materials_dirty: bool = field(default=False, repr=False)

    # --- reading ---
    @classmethod
    def from_bytes(cls, raw: bytes) -> "Pack":
        if raw[:8] != MAGIC:
            raise SpkError(f"not a mesh pack: {raw[:8]!r}")
        u = lambda fmt, at: struct.unpack_from(fmt, raw, at)  # noqa: E731
        sec = {nm: u("<III", 0x34 + 12 * i) for i, nm in enumerate(_SECTIONS)}
        part = lambda o, s: raw[o:o + s]  # noqa: E731
        no, ns, _nc = sec["names"]
        if ns and u("<I", no)[0] != 0x0A:
            raise SpkError("the name table doesn't start with its root")
        models = [Model(name, *_unpack_model(payload)) for name, payload in read_names(raw, no + 10, no + ns)] if ns else []
        fo, fs, fc = sec["formats"]
        formats = [raw[fo + 4 + FORMAT_NAME * i:fo + 4 + FORMAT_NAME * (i + 1)].split(b"\0", 1)[0].decode("latin-1")
                   for i in range(fc)]
        mo, ms, mc = sec["materials"]
        meshes = [u("<HH", sec["meshes"][0] + 4 * i) for i in range(sec["meshes"][2])]
        draws = [list(u("<6H", sec["draws"][0] + 12 * i)) for i in range(sec["draws"][2])]
        ib_off, _ib_size = u("<II", 0x94)
        vt_off, _vt_size, vt_count = u("<III", 0x9C)
        vb_off, _vb_size = u("<II", 0xA8)
        so, ss, sc = u("<III", 0xB0)
        bo, bs = u("<II", 0xBC)

        def buffers(table_off, count, base):
            out = []
            for i in range(count):
                off, size, n, kind, flags = u("<IIIHH", table_off + 16 * i)
                out.append(Buffer(n, kind, flags, raw[base + off:base + off + size]))
            return out

        return cls(version=u("<I", 8)[0], models=models, formats=formats, formats_raw=part(fo, fs),
                   materials=Ndf(part(mo, ms)) if ms else None, materials_raw=part(mo, ms), material_count=mc,
                   extra1=(part(*sec["extra1"][:2]), sec["extra1"][2]), extra2=(part(*sec["extra2"][:2]), sec["extra2"][2]),
                   meshes=meshes, draws=draws, skel_records=(part(so, ss), sc), skel_data=part(bo, bs),
                   ibs=buffers(sec["ib_table"][0], sec["ib_table"][2], ib_off),
                   vbs=buffers(vt_off, vt_count, vb_off), tail_c0=raw[0xC0:0xC4])

    # --- writing ---
    def to_bytes(self) -> bytes:
        out = bytearray(HEADER)
        at = {}

        def place(name, data, count=0):
            if data:
                out.extend(FILL * (-len(out) % 4))
            at[name] = (len(out), len(data), count)
            out.extend(data)

        def packed(bufs):
            data, rows = bytearray(), bytearray()
            for b in bufs:
                data.extend(FILL * (-len(data) % 4))
                rows += struct.pack("<IIIHH", len(data), len(b.data), b.count, b.kind, b.flags)
                data.extend(b.data)
            return bytes(rows), bytes(data)

        mats = self.materials.to_logical() if self._materials_dirty else self.materials_raw
        ib_rows, ib_data = packed(self.ibs)
        vb_rows, vb_data = packed(self.vbs)
        names = build_names([(m.name, _pack_model(m)) for m in self.models]) if self.models else b""  # 11 map packs: none
        place("names", names, len(self.models))
        place("formats", self._formats_bytes(), len(self.formats))
        place("materials", mats, self.material_count)
        place("extra1", *self.extra1)
        place("extra2", *self.extra2)
        place("meshes", b"".join(struct.pack("<HH", *m) for m in self.meshes), len(self.meshes))
        place("draws", b"".join(struct.pack("<6H", *d) for d in self.draws), len(self.draws))
        place("skel_records", *self.skel_records)
        place("skel_data", self.skel_data)
        place("ib_table", ib_rows, len(self.ibs))
        place("vb_table", vb_rows, len(self.vbs))
        place("ib_data", ib_data)
        place("vb_data", vb_data)
        for i, nm in enumerate(_SECTIONS):
            struct.pack_into("<III", out, 0x34 + 12 * i, *at[nm])
        struct.pack_into("<II", out, 0x94, *at["ib_data"][:2])
        struct.pack_into("<III", out, 0x9C, *at["vb_table"])
        struct.pack_into("<II", out, 0xA8, *at["vb_data"][:2])
        struct.pack_into("<III", out, 0xB0, *at["skel_records"])
        struct.pack_into("<II", out, 0xBC, *at["skel_data"][:2])
        out[0xC0:0xC4] = self.tail_c0
        data0 = at["ib_data"][0]
        out[0:8] = MAGIC
        struct.pack_into("<II", out, 8, self.version, len(out))
        struct.pack_into("<4I", out, 0x20, 0, data0, data0, len(out) - data0)
        struct.pack_into("<I", out, 0x30, len(self.models))
        out[0x10:0x20] = header_hash(out)
        return bytes(out)

    def _formats_bytes(self) -> bytes:
        if not self._formats_dirty:
            return self.formats_raw
        return struct.pack("<I", FORMAT_NAME) + b"".join(f.encode("latin-1").ljust(FORMAT_NAME, b"\0")
                                                         for f in self.formats)

    # --- editing ---
    def model(self, name: str | bytes) -> Model:
        key = name.lower().encode("latin-1") if isinstance(name, str) else name.lower()
        for m in self.models:
            if m.name.lower() == key:
                return m
        raise KeyError(name)

    def format_index(self, name: str) -> int:
        """The vertex format's number, added if the pack doesn't have it."""
        if name in self.formats:
            return self.formats.index(name)
        if len(name.encode("latin-1")) >= FORMAT_NAME:
            raise SpkError(f"vertex format name too long: {name}")
        self.formats.append(name)
        self._formats_dirty = True
        return len(self.formats) - 1

    def add_model(self, model: Model) -> None:
        """Insert a name-table entry where the game's order puts it (folder by folder)."""
        if any(m.name.lower() == model.name.lower() for m in self.models):
            raise SpkError(f"the pack already has {model.name.decode('latin-1')}")
        key = _order_key(model.name)
        at = next((i for i, m in enumerate(self.models) if _order_key(m.name) > key), len(self.models))
        self.models.insert(at, model)

    def copy_model(self, src: "Pack", name: str | bytes, new_name: bytes | None = None) -> Model:
        """Copy one model from another pack: its draw calls, buffers (bytes kept as they are, compressed or not),
        vertex formats and materials. Returns the new entry."""
        m = src.model(name)
        if m.skeleton != NO_SKELETON:
            raise SpkError(f"{m.name.decode('latin-1')} has a skeleton record; copying skeletons isn't done yet")
        first, count = src.meshes[m.mesh]
        mat_map: dict[int, int] = {}
        memo: dict[int, int] = {}
        new_first = len(self.draws)
        for d in range(first, first + count):
            unk, material, ib, vb, ffff, cdcd = src.draws[d]
            if material not in mat_map:
                if self.materials is None or src.materials is None:
                    raise SpkError("a pack without materials")
                mat_map[material] = copy_material(self.materials, src.materials, material, memo)
                self.material_count += 1
                self._materials_dirty = True
            b = src.ibs[ib]
            self.ibs.append(Buffer(b.count, b.kind, b.flags, b.data))
            v = src.vbs[vb]
            self.vbs.append(Buffer(v.count, self.format_index(src.formats[v.kind]), v.flags, v.data))
            self.draws.append([unk, mat_map[material], len(self.ibs) - 1, len(self.vbs) - 1, ffff, cdcd])
        self.meshes.append((new_first, count))
        new = Model(new_name or m.name, m.box, m.flags, len(self.meshes) - 1, NO_SKELETON)
        self.add_model(new)
        return new

    def set_buffer(self, which: str, index: int, data: bytes, count: int, compressed: bool = False) -> None:
        """Replace an index ("ib") or vertex ("vb") buffer's bytes and count (the format stays)."""
        bufs = self.ibs if which == "ib" else self.vbs
        b = bufs[index]
        bufs[index] = Buffer(count, b.kind, 0xC000 if compressed else 0, data)


# --- the name table (a trie) ---
def read_names(raw: bytes, start: int, end: int) -> list[tuple[bytes, bytes]]:
    """(name, 32-byte entry: box, flags, mesh, skeleton) for each model, in the order stored."""
    out = []

    def walk(pos, prefix):
        while pos + 8 <= end:
            head, sibling = struct.unpack_from("<II", raw, pos)
            if head == 0:
                stop = raw.index(b"\0", pos + 40)
                out.append((prefix + raw[pos + 40:stop], raw[pos + 8:pos + 40]))
            else:
                stop = raw.index(b"\0", pos + 8)
                walk(pos + head, prefix + raw[pos + 8:stop])
            if sibling == 0:
                return
            pos += sibling

    walk(start, b"")
    return out


def build_names(items: list[tuple[bytes, bytes]]) -> bytes:
    """The name table for (name, 32-byte entry) items, siblings in the items' order: a root with an empty piece,
    then the trie. Byte for byte what the game ships, given the same order."""
    def even(b):
        return b + bytes(len(b) % 2)

    def children(group):
        order, buckets = [], {}
        for suffix, payload in group:
            k = suffix[:1]
            if k not in buckets:
                buckets[k] = []
                order.append(k)
            buckets[k].append((suffix, payload))
        entries = []
        for k in order:
            b = buckets[k]
            if len(b) == 1:
                suffix, payload = b[0]
                entries.append(bytearray(even(struct.pack("<II", 0, 0) + payload + suffix + b"\0")))
                continue
            common = b[0][0]
            for suffix, _p in b[1:]:
                n = 0
                while n < min(len(common), len(suffix)) and common[n] == suffix[n]:
                    n += 1
                common = common[:n]
            if not common:
                raise SpkError("two model names where one is the start of the other")
            head = even(struct.pack("<II", 0, 0) + common + b"\0")
            entry = bytearray(head + children([(s[len(common):], p) for s, p in b]))
            struct.pack_into("<I", entry, 0, len(head))
            entries.append(entry)
        for i, e in enumerate(entries):
            struct.pack_into("<I", e, 4, 0 if i == len(entries) - 1 else len(e))
        return b"".join(entries)

    root = even(struct.pack("<II", 0, 0) + b"\0")
    body = bytearray(root + children(items))
    struct.pack_into("<I", body, 0, len(root))
    return bytes(body)


def _order_key(name: bytes):
    return name.lower().split(b"\\")


def _unpack_model(payload: bytes) -> tuple:
    vals = struct.unpack("<6fIHH", payload)
    return vals[:6], vals[6], vals[7], vals[8]


def _pack_model(m: Model) -> bytes:
    return struct.pack("<6fIHH", *m.box, m.flags, m.mesh, m.skeleton)


# --- materials: copying TMeshMaterial objects between two packs' NDF ---
def material_list(nd: Ndf) -> list[int]:
    """The material list (object 0, a TEugBListPBaseClass): the object number of material 0, 1, ..."""
    root = nd.objects[0]
    if nd.classes[root.cls] != "TEugBListPBaseClass" or len(root.props) != 1 or root.props[0][1].tc != 0x11:
        raise SpkError("the materials don't start with their list")
    v = root.props[0][1].payload
    n = struct.unpack_from("<I", v, 0)[0]
    out = []
    for i in range(n):
        tc, kind, obj = struct.unpack_from("<III", v, 4 + 16 * i)
        if tc != 0x09 or kind != _REF_OBJECT:
            raise SpkError("the material list holds something other than objects")
        out.append(obj)
    return out


def copy_material(dst: Ndf, src: Ndf, material: int, memo: dict[int, int]) -> int:
    """Copy material number `material` of `src` (and every object it points at) into `dst`; append it to dst's
    list. Returns its number in dst. `memo` (source object -> new object) shares helpers within one copy."""
    obj = material_list(src)[material]
    new = _copy_object(dst, src, obj, memo)
    root = dst.objects[0]
    pi, lst = root.props[0]
    n = struct.unpack_from("<I", lst.payload, 0)[0]
    entry = struct.pack("<IIII", 0x09, _REF_OBJECT, new, dst.class_index(src.classes[src.objects[obj].cls]))
    root.props[0] = (pi, Value(0x11, struct.pack("<I", n + 1) + lst.payload[4:] + entry))
    return n


def _copy_object(dst: Ndf, src: Ndf, index: int, memo: dict[int, int]) -> int:
    if index in memo:
        return memo[index]
    o = src.objects[index]
    cls = dst.class_index(src.classes[o.cls])
    new = dst.add_object(cls, [])
    memo[index] = new
    props = []
    for pi, v in o.props:
        name, pcls = src.props[pi]
        props.append((_prop(dst, name, dst.class_index(src.classes[pcls])), _copy_value(dst, src, v, memo)))
    dst.objects[new].props = props
    return new


def _prop(dst: Ndf, name: str, cls: int) -> int:
    for i, (n, c) in enumerate(dst.props):
        if n == name and c == cls:
            return i
    return dst.add_prop(name, cls)


def _string(dst: Ndf, text: str) -> int:
    i = dst.string_index(text)
    return i if i is not None else dst.add_string(text)


def _copy_value(dst: Ndf, src: Ndf, v: Value, memo: dict[int, int]) -> Value:
    tc, p = v.tc, v.payload
    if tc in (0x07, 0x1C):
        return Value(tc, struct.pack("<I", _string(dst, src.strings[struct.unpack("<I", p)[0]])))
    if tc == 0x09:
        kind = struct.unpack_from("<I", p, 0)[0]
        if kind == _REF_OBJECT:
            obj, cls = struct.unpack_from("<II", p, 4)
            return Value(tc, struct.pack("<III", kind, _copy_object(dst, src, obj, memo),
                                         dst.class_index(src.classes[cls])))
        if kind == 0xAAAAAAAA:
            return Value(tc, struct.pack("<II", kind, dst.import_index(src.imports[struct.unpack_from("<I", p, 4)[0]])))
        return Value(tc, p)
    if tc in (0x11, 0x12, 0x22):
        n = 2 if tc == 0x22 else struct.unpack_from("<I", p, 0)[0] * (2 if tc == 0x12 else 1)
        at = 0 if tc == 0x22 else 4
        out = bytearray() if tc == 0x22 else bytearray(p[:4])
        for _ in range(n):
            sub, at = _read_value(p, at)
            out += _copy_value(dst, src, sub, memo).encode()
        return Value(tc, bytes(out))
    return Value(tc, p)


# --- the maps' static meshes (output\staticmeshes*.spkpc): chunks, and new road pieces ---
# Only these packs fill the two extra sections (DomesticNukes and his Claude, 2026-10-02, all 33 map packs):
#  extra1 = chunks, 48 bytes each: f32 box (min x, y, z, max x, y, z), u16 cell id, 2 junk bytes, u32 first vertex,
#           vertex count, first index, index count, u8 0, 3 junk bytes (Eugen's tool left memory there: 0xDD / 0xCD);
#  extra2 = per draw call (u16 first chunk, u16 chunk count). A draw's chunks are back to back in its vertex and index
#           buffers, cover them exactly, are sorted by cell id with no id twice, and a chunk's indices are absolute
#           vertex numbers inside its own vertex range (5,022 of 5,022 chunks).
#  cell id = the rank of the chunk's 81,920-unit square along a Hilbert curve over the next power-of-two grid,
#           counting only squares inside the map (5,011 of 5,022; the rest straddle a square's edge and take a
#           neighbour's id). Bridges and roads in one square share it.
#  A road chunk's box is its vertices' box with the top raised by 10 (4,701 of 4,701).
#  The road (the `road` model, MaterialBezierLine_Road): each Route piece is 6 vertices, two cross-sections of 3 at
#  its ends (TexCoord u -0.5, 0, 0.5; v 400), and 4 triangles (a0,b1,b0)(a0,a1,b1)(a1,b2,b1)(a1,a2,b2).
CELL = 81920.0
_CHUNK = struct.Struct("<6fHHIIIIB3s")
ROAD_COLOUR = (220, 220, 220, 100)
ROAD_WIDTH = 400.0


@dataclass
class Chunk:
    box: tuple
    cell: int
    v0: int
    vn: int
    i0: int
    ni: int
    flag: int = 0
    junk: tuple = (0xDDDD, b"\xcd\xdd\xdd")


def read_chunks(pack: "Pack") -> tuple[list[Chunk], list[tuple[int, int]]]:
    raw1, n1 = pack.extra1
    raw2, n2 = pack.extra2
    if len(raw1) != _CHUNK.size * n1 or len(raw2) != 4 * n2:
        raise SpkError("not a static-mesh pack's chunk sections")
    chunks = []
    for k in range(n1):
        *box, cell, junk1, v0, vn, i0, ni, flag, junk2 = _CHUNK.unpack_from(raw1, _CHUNK.size * k)
        chunks.append(Chunk(tuple(box), cell, v0, vn, i0, ni, flag, (junk1, junk2)))
    return chunks, [struct.unpack_from("<HH", raw2, 4 * d) for d in range(n2)]


def write_chunks(pack: "Pack", chunks: list[Chunk], per_draw: list[tuple[int, int]]) -> None:
    pack.extra1 = (b"".join(_CHUNK.pack(*c.box, c.cell, c.junk[0], c.v0, c.vn, c.i0, c.ni, c.flag, c.junk[1])
                            for c in chunks), len(chunks))
    pack.extra2 = (b"".join(struct.pack("<HH", *p) for p in per_draw), len(per_draw))


def hilbert(n: int, x: int, y: int) -> int:
    d, s = 0, n // 2
    while s:
        rx, ry = (1 if x & s else 0), (1 if y & s else 0)
        d += s * s * ((3 * rx) ^ ry)
        if not ry:
            if rx:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        s //= 2
    return d


def cell_ids(map_box: tuple) -> dict[tuple[int, int], int]:
    """{(column, row): cell id} for a map's 81,920-unit squares (map_box = mapinfo.win's x0, y0, x1, y1 at 32)."""
    x0, y0, x1, y1 = map_box
    w, h = -int(-(x1 - x0) // CELL), -int(-(y1 - y0) // CELL)
    n = 1
    while n < max(w, h):
        n *= 2
    cells = sorted((hilbert(n, x, y), (x, y)) for x in range(w) for y in range(h))
    return {c: i for i, (_d, c) in enumerate(cells)}


@dataclass
class RoadPiece:
    """One Route piece: its two ends (x, y, z on the ground), the curve's direction there (x, y), and the width
    factor at each end (about 1; the game's own widen up to 1.8 at sharp joints)."""
    a: tuple
    b: tuple
    ta: tuple
    tb: tuple
    size_a: float = 1.0
    size_b: float = 1.0


def _unit(t):
    n = (t[0] * t[0] + t[1] * t[1]) ** 0.5 or 1.0
    return t[0] / n, t[1] / n


def _byte(v: float) -> int:
    return max(0, min(255, round(v * 127 + 128)))


def road_vertices(piece: RoadPiece) -> bytes:
    """The piece's 6 vertices in the road format (Position_3f NormalIn01_4ubn Normal2In01_4ubn PSize_1f
    Color0_col32 ArcLengths_2f TexCoord0_2f, 44 bytes)."""
    out = bytearray()
    for p, t, size in ((piece.a, piece.ta, piece.size_a), (piece.b, piece.tb, piece.size_b)):
        tx, ty = _unit(t)
        normal = bytes([_byte(tx), _byte(ty), 128, 128])
        normal2 = bytes([_byte(ty), _byte(-tx), 128, 128])
        for u in (-0.5, 0.0, 0.5):
            out += struct.pack("<3f", *p) + normal + normal2 + struct.pack("<f", size) + bytes(ROAD_COLOUR) \
                + struct.pack("<4f", 0.0, 0.0, u, ROAD_WIDTH)
    return bytes(out)


_PIECE_TRIANGLES = (0, 4, 3, 0, 1, 4, 1, 5, 4, 1, 2, 5)
_ROAD_STRIDE = 44


def road_draw(pack: "Pack") -> int:
    """The draw call of the `road` model."""
    m = pack.model("road")
    first, count = pack.meshes[m.mesh]
    if count != 1:
        raise SpkError("the road model should be one draw call")
    return first


def add_road_pieces(pack: "Pack", pieces: list, map_box: tuple) -> int:
    """Add Route pieces to the map's baked road mesh: each goes into the chunk of the square holding its middle
    (a new chunk if the square has none), the chunk's box grows (top + 10), and the road's buffers are rebuilt in
    chunk order. Returns the road's vertex count (it must stay under 65,536: the indices are u16)."""
    chunks, per_draw = read_chunks(pack)
    d = road_draw(pack)
    _u, _mat, ib, vb, _f, _c = pack.draws[d]
    first, count = per_draw[d]
    if pack.vbs[vb].flags or pack.ibs[ib].flags:
        raise SpkError("the road's buffers are compressed")
    vdata, idata = pack.vbs[vb].data, pack.ibs[ib].data
    ids = cell_ids(map_box)
    groups = {}   # cell id -> [vertex bytes, local indices, old chunk or None]
    for c in chunks[first:first + count]:
        local = [i - c.v0 for i in struct.unpack_from(f"<{c.ni}H", idata, 2 * c.i0)]
        groups[c.cell] = [bytearray(vdata[_ROAD_STRIDE * c.v0:_ROAD_STRIDE * (c.v0 + c.vn)]), local, c]
    x0, y0 = map_box[0], map_box[1]
    for p in pieces:
        mx, my = (p.a[0] + p.b[0]) / 2, (p.a[1] + p.b[1]) / 2
        key = (int((mx - x0) // CELL), int((my - y0) // CELL))
        if key not in ids:
            raise SpkError(f"a road piece outside the map at ({mx:.0f}, {my:.0f})")
        g = groups.setdefault(ids[key], [bytearray(), [], None])
        base = len(g[0]) // _ROAD_STRIDE
        g[0] += road_vertices(p)
        g[1] += [base + i for i in _PIECE_TRIANGLES]
    new_v, new_i, new_chunks = bytearray(), [], []
    for cell in sorted(groups):
        vb_bytes, local, old = groups[cell]
        v0, vn = len(new_v) // _ROAD_STRIDE, len(vb_bytes) // _ROAD_STRIDE
        if old is not None and vn == old.vn:
            box = old.box   # an untouched chunk keeps its box as shipped
        else:
            pos = [struct.unpack_from("<3f", vb_bytes, _ROAD_STRIDE * k) for k in range(vn)]
            box = tuple(min(q[j] for q in pos) for j in range(3)) + tuple(max(q[j] for q in pos) for j in range(3))
            box = box[:5] + (box[5] + 10.0,)
        new_chunks.append(Chunk(box, cell, v0, vn, len(new_i), len(local), 0,
                                old.junk if old is not None else (0xDDDD, b"\xcd\xdd\xdd")))
        new_i += [v0 + i for i in local]
        new_v += vb_bytes
    total = len(new_v) // _ROAD_STRIDE
    if total > 0xFFFF:
        raise SpkError(f"the road would have {total} vertices; u16 indices allow 65,535")
    chunks[first:first + count] = new_chunks
    shift = len(new_chunks) - count
    per_draw = [(f + (shift if f > first else 0), len(new_chunks) if k == d else n) for k, (f, n) in enumerate(per_draw)]
    write_chunks(pack, chunks, per_draw)
    pack.set_buffer("vb", vb, bytes(new_v), total)
    pack.set_buffer("ib", ib, struct.pack(f"<{len(new_i)}H", *new_i), len(new_i))
    m = pack.model("road")
    lo = [min(m.box[j], *(c.box[j] for c in new_chunks)) for j in range(3)]
    hi = [max(m.box[j + 3], *(c.box[j + 3] for c in new_chunks)) for j in range(3)]
    m.box = tuple(lo + hi)
    return total
