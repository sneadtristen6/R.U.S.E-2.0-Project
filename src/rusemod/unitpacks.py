"""Unit model packs, written: a unit's models copied into another nation's skirmish packs, or the common ones.

A skirmish loads a nation's unit models only when a player has that nation (rusemod.unitcheck). They are in four
packs of ZZ_Win.dat per nation (<tag>: us, ger, uk, fr, ita, urss, japan; `common` ones load in every skirmish):

  gen_5\\pack\\gfxdescriptor\\meshskirmish_<tag>.spk        the meshes (the US has a second set: ...witboat_us)
  gen_5\\pack\\gfxdescriptor\\skeleton_<tag>.spk            their skeletons, under the same names
  gentexproxy\\pack\\gfxdescriptor\\proxyskirmish_<tag>.ppk  small stand-ins of their textures (the US: two again)
  genanim_15\\pack\\gfxdescriptor_<tag>.apk                 their animations (.baf), an EDAT archive

The game's own packs already carry other nations' models where its units need them (Germany's carry the US Long
Tom's mesh, skeleton and texture stand-in), so a unit given to another nation gets its models copied into that
nation's packs the same way, and a spawned unit's go into the common ones. The full textures are loose files of
ZZ_Win.dat, the same for every nation.

Mesh packs (MESHPCPC, version 4), little-endian:
  0x00  magic, u32 4, u32 file size, 16 bytes (an id; the game doesn't check it against the content)
  0x20  (u32 0, u32 size) of the part read first (everything but the buffers); 0x28 (offset, size) of the buffers
  0x30  u32 model count
  0x34  8 x (offset, size, count): names, vertex formats, materials, two empty, meshes, draw calls, index-buffer table
  0x94  index buffers (offset, size); 0x9C vertex-buffer table (offset, size, count); 0xA8 vertex buffers
  0xB0  skeleton table (offset, size, count): u32 offset (in the skeleton data), u32 size per skeleton
  0xBC  skeleton data (offset, size)
  0xC4  the sections in the order names, formats, materials, the two empty ones, meshes, draw calls, skeleton table,
        skeleton data, index-buffer table, vertex-buffer table, index buffers, vertex buffers. A section that isn't
        empty starts on a multiple of 4, and so does every index buffer; the bytes between are 0x7E.
  names a trie: u32 10, 6 bytes, then nodes of u32 header length (0: a model), u32 offset to the next sibling (0: the
        last); a folder's piece of the name follows (its children at the header length), a model's box (6 f32),
        u32 flags, u16 mesh, u16 skeleton (0xCDCD: none) and the last piece. Pieces end with a 0 and a node takes an
        even number of bytes. Names are sorted with the folder separator first (us_1\\x before us_10\\x), siblings
        split on their first character, a folder holds what its names share.
  The materials are an NDF: its root object lists one TMeshMaterial per material number. A skeleton pack is the same
  container without meshes or buffers: its names are its mesh pack's, each with its skeleton's number (shared: a gun
  and its idle pose have one). Meshes are numbered in name order and their draw calls follow each other in mesh
  order; buffers, materials and skeletons are shared by number.

Texture stand-in packs (PRXYPCPC, version 4):
  0x00  magic, u32 4, u32 file size, 16-byte id
  0x20  table (offset, size), data (offset, size), u32 count, names (offset, size), u32 count
        table: 24 bytes per texture: 8-byte key (the game registers stand-ins by it; the first pack to bring one wins),
        u32 offset in the data, u32 size, 8 bytes; names: 256 bytes (the texture under gentexproxy\\, as .tgv) and the
        key again. Sorted by name; each stand-in is a small .tgv, and textures with the same picture share one.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field

from .edat import Edat
from .ndf import Ndf, Value, _read_value

MESH_MAGIC = b"MESHPCPC"
PROXY_MAGIC = b"PRXYPCPC"
PAD = 0x7E
NAMES_HEAD = struct.pack("<I", 10) + bytes(6)
ITEM = struct.Struct("<6fIHH")  # a model's box, flags, mesh, skeleton
NONE = 0xCDCD
MODEL = ".ase2ndfbin"

MESH_DIR = "gen_5\\pack\\gfxdescriptor\\"
PROXY_DIR = "gentexproxy\\pack\\gfxdescriptor\\"
ANIM_DIR = "genanim_15\\pack\\"


class PackError(ValueError):
    pass


def _align(buf: bytearray) -> None:
    buf += bytes([PAD]) * (-len(buf) % 4)


def sort_key(name: str) -> bytes:
    """The order of names in a pack: the folder separator before any other character."""
    return name.replace("\\", "\0").encode("latin-1")


# --- the name trie (mesh packs; an EDAT archive's dictionary is the same with a 9-byte payload) ---
def read_names(raw: bytes, start: int, end: int, payload: int) -> list[tuple[str, bytes]]:
    """Every (name, payload bytes) of the trie whose first node is at `start`, in their order."""
    out: list[tuple[str, bytes]] = []

    def walk(pos: int, stop: int, prefix: str) -> None:
        while pos + 8 <= stop:
            head, sib = struct.unpack_from("<II", raw, pos)
            if head == 0:
                end_name = raw.index(b"\0", pos + 8 + payload)
                out.append((prefix + raw[pos + 8 + payload:end_name].decode("latin-1"),
                            bytes(raw[pos + 8:pos + 8 + payload])))
            else:
                end_name = raw.index(b"\0", pos + 8)
                piece = raw[pos + 8:end_name].decode("latin-1")
                if head >= end_name + 1 - pos:
                    walk(pos + head, pos + sib if sib else stop, prefix + piece)
            if sib == 0:
                return
            pos += sib
    walk(start, end, "")
    return out


def _even(b: bytes) -> bytes:
    return b + bytes(len(b) % 2)


def write_names(entries: list[tuple[str, bytes]]) -> bytes:
    """The trie of `entries` [(name, payload)], laid out as the game's packs are (sorted by sort_key)."""
    entries = sorted(entries, key=lambda e: sort_key(e[0]))
    for a, b in zip(entries, entries[1:]):
        if a[0] == b[0]:
            raise PackError(f"the name {a[0]!r} twice")

    def nodes(group: list[tuple[str, bytes]]) -> list[bytes]:
        out, i = [], 0
        while i < len(group):
            j = i
            while j < len(group) and group[j][0][:1] == group[i][0][:1]:
                j += 1
            same = group[i:j]
            if len(same) == 1:
                name, data = same[0]
                out.append(_even(struct.pack("<II", 0, 0) + data + name.encode("latin-1") + b"\0"))
            else:
                share = _shared([n for n, _ in same])
                if any(len(n) == len(share) for n, _ in same):
                    raise PackError(f"the name {share!r} is the start of another name")
                head = _even(struct.pack("<II", 0, 0) + share.encode("latin-1") + b"\0")
                head = struct.pack("<I", len(head)) + head[4:]
                out.append(head + b"".join(_link(nodes([(n[len(share):], d) for n, d in same]))))
            i = j
        return out
    return b"".join(_link(nodes(entries)))


def _shared(names: list[str]) -> str:
    first, last = min(names), max(names)
    n = 0
    while n < min(len(first), len(last)) and first[n] == last[n]:
        n += 1
    return first[:n]


def _link(siblings: list[bytes]) -> list[bytes]:
    """Each node but the last points at the next one (its own size)."""
    return [struct.pack("<I", len(s)).join([s[:4], s[8:]]) if k < len(siblings) - 1 else s
            for k, s in enumerate(siblings)]


# --- mesh packs ---
SECTIONS = ("names", "formats", "materials", "empty1", "empty2", "meshes", "draws", "ib_table")
LAYOUT = ("names", "formats", "materials", "empty1", "empty2", "meshes", "draws", "skel_table", "skel_data",
          "ib_table", "vb_table", "ib_data", "vb_data")


@dataclass
class Buffer:
    """An index or vertex buffer: its bytes (with the 0x7E after it, for index buffers), size, count, its u16
    (1 / the vertex format) and flags (0xC000: compressed)."""
    data: bytes
    size: int
    count: int
    kind: int
    flags: int


@dataclass
class MeshPack:
    """One MESHPCPC pack (meshes, or skeletons only), every part kept so it writes back as it was."""
    ident: bytes
    items: dict = field(default_factory=dict)     # name -> [box and flags (28 bytes), mesh, skeleton]
    formats: list = field(default_factory=list)   # vertex format names (256 bytes each, zero-padded)
    materials: bytes = b""                         # the materials' NDF
    material_count: int = 0
    empty: tuple = ((0, 0), (0, 0))                # (size, count) of the two empty sections, as read
    meshes: list = field(default_factory=list)    # (first draw call, count)
    draws: list = field(default_factory=list)     # (u16, material, index buffer, vertex buffer, u16, u16)
    ibs: list = field(default_factory=list)       # Buffer
    vbs: list = field(default_factory=list)       # Buffer
    skeletons: list = field(default_factory=list)  # bytes
    has_formats: bool = True                       # (a pack with nothing in it has no format section at all)

    @classmethod
    def read(cls, raw: bytes) -> "MeshPack":
        if raw[:8] != MESH_MAGIC or struct.unpack_from("<I", raw, 8)[0] != 4:
            raise PackError(f"not a version 4 mesh pack: {raw[:8]!r}")
        sec = {n: struct.unpack_from("<III", raw, 0x34 + 12 * i) for i, n in enumerate(SECTIONS)}
        ib_off, ib_size = struct.unpack_from("<II", raw, 0x94)
        vt_off, _vt_size, vt_count = struct.unpack_from("<III", raw, 0x9C)
        vb_off, vb_size = struct.unpack_from("<II", raw, 0xA8)
        st_off, _st_size, st_count = struct.unpack_from("<III", raw, 0xB0)
        sd_off, _sd_size = struct.unpack_from("<II", raw, 0xBC)
        pack = cls(bytes(raw[0x10:0x20]))
        no, ns, nc = sec["names"]
        if ns:
            if raw[no:no + 10] != NAMES_HEAD:
                raise PackError("its name table doesn't start as known")
            for name, data in read_names(raw, no + 10, no + ns, ITEM.size):
                *_box, mesh, skel = ITEM.unpack(data)
                pack.items[name] = [data[:28], mesh, skel]
            if len(pack.items) != nc:
                raise PackError(f"{len(pack.items)} names for {nc}")
        fo, fs, fc = sec["formats"]
        if fs and struct.unpack_from("<I", raw, fo)[0] != 256:
            raise PackError("vertex format names that aren't 256 bytes")
        pack.formats = [bytes(raw[fo + 4 + 256 * i:fo + 4 + 256 * (i + 1)]) for i in range(fc)]
        pack.has_formats = bool(fs)
        mo, ms, pack.material_count = sec["materials"]
        pack.materials = bytes(raw[mo:mo + ms])
        pack.empty = tuple(sec[n][1:] for n in ("empty1", "empty2"))
        if any(pack.empty[k][0] for k in (0, 1)):
            raise PackError("a section known to be empty isn't")
        o, _s, c = sec["meshes"]
        pack.meshes = [struct.unpack_from("<HH", raw, o + 4 * i) for i in range(c)]
        o, _s, c = sec["draws"]
        pack.draws = [struct.unpack_from("<6H", raw, o + 12 * i) for i in range(c)]
        o, _s, c = sec["ib_table"]
        pack.ibs = _buffers(raw, [struct.unpack_from("<IIIHH", raw, o + 16 * i) for i in range(c)], ib_off, ib_size)
        pack.vbs = _buffers(raw, [struct.unpack_from("<IIIHH", raw, vt_off + 16 * i) for i in range(vt_count)],
                            vb_off, vb_size)
        rows = [struct.unpack_from("<II", raw, st_off + 8 * i) for i in range(st_count)]
        pos = 0
        for off, size in rows:
            if off != pos:
                raise PackError("skeletons that don't follow each other")
            pack.skeletons.append(bytes(raw[sd_off + off:sd_off + off + size]))
            pos = off + size
        return pack

    # --- writing ---
    def to_bytes(self) -> bytes:
        """The pack, laid out as the game's are."""
        names = NAMES_HEAD + write_names([(n, data + struct.pack("<HH", mesh, skel))
                                          for n, (data, mesh, skel) in self.items.items()]) if self.items else b""
        formats = (struct.pack("<I", 256) + b"".join(self.formats)) if self.formats or self.has_formats else b""
        parts = {
            "names": names, "formats": formats, "materials": self.materials, "empty1": b"", "empty2": b"",
            "meshes": b"".join(struct.pack("<HH", *m) for m in self.meshes),
            "draws": b"".join(struct.pack("<6H", *d) for d in self.draws),
        }
        st, sd, pos = bytearray(), bytearray(), 0
        for s in self.skeletons:
            st += struct.pack("<II", pos, len(s))
            sd += s
            pos += len(s)
        parts["skel_table"], parts["skel_data"] = bytes(st), bytes(sd)
        ib_table, ib_data = _table(self.ibs, pad=True)
        vb_table, vb_data = _table(self.vbs, pad=False)
        parts.update(ib_table=ib_table, vb_table=vb_table, ib_data=ib_data, vb_data=vb_data)
        out = bytearray(0xC4)
        at = {}
        for name in LAYOUT:
            if parts[name]:
                _align(out)
            at[name] = (len(out), len(parts[name]))
            out += parts[name]
        out[0:8] = MESH_MAGIC
        cpu = at["ib_data"][0]
        counts = {"names": len(self.items), "formats": len(self.formats), "materials": self.material_count,
                  "empty1": self.empty[0][1], "empty2": self.empty[1][1], "meshes": len(self.meshes),
                  "draws": len(self.draws), "ib_table": len(self.ibs)}
        struct.pack_into("<III", out, 0x08, 4, len(out), 0)
        struct.pack_into("<IIIII", out, 0x20, 0, cpu, cpu, len(out) - cpu, len(self.items))
        for i, name in enumerate(SECTIONS):
            struct.pack_into("<III", out, 0x34 + 12 * i, *at[name], counts[name])
        struct.pack_into("<II", out, 0x94, *at["ib_data"])
        struct.pack_into("<III", out, 0x9C, *at["vb_table"], len(self.vbs))
        struct.pack_into("<II", out, 0xA8, *at["vb_data"])
        struct.pack_into("<III", out, 0xB0, *at["skel_table"], len(self.skeletons))
        struct.pack_into("<II", out, 0xBC, *at["skel_data"])
        out[0x10:0x20] = self.ident
        return bytes(out)

    def renew(self) -> None:
        """A new id for a changed pack (the content's MD5, so the same pack always gets the same one)."""
        self.ident = hashlib.md5(self.to_bytes()).digest()

    # --- reading models ---
    def bones(self, name: str) -> bool:
        """Whether a model's vertices follow bones (its vertex formats have bone indices): it needs its skeleton."""
        _data, mesh, _skel = self.items[name]
        if mesh == NONE:
            return False
        first, count = self.meshes[mesh]
        return any(b"BlIdx" in self.formats[self.vbs[self.draws[d][3]].kind] for d in range(first, first + count))

    def textures(self, name: str) -> list[str]:
        """The texture images a model's materials name (ZZ:\\GenTexGroup\\...\\X01.png), in order."""
        _data, mesh, _skel = self.items[name]
        if mesh == NONE or not self.meshes[mesh][1]:
            return []
        first, count = self.meshes[mesh]
        nd = Ndf(self.materials)
        roots = _material_list(nd)
        out = []
        for d in range(first, first + count):
            obj = nd.objects[roots[self.draws[d][1]]]
            for pi, v in obj.props:
                if nd.prop_name(pi) == "Textures":
                    out += [p for p in _texts(nd, v) if p.lower().endswith((".png", ".tga", ".dds"))
                            and p not in out]
        return out

    # --- copying a model from another pack ---
    def add(self, src: "MeshPack", name: str) -> None:
        """Copy the model `name` of `src` in: its mesh, draw calls, materials, buffers and vertex formats, or (in a
        skeleton pack) its skeleton. Buffers, formats and materials this pack already has are shared. Meshes keep
        their name order, so the ones after it move up one."""
        if name in self.items:
            raise PackError(f"{name} is already in the pack")
        data, mesh, skel = src.items[name]
        new_skel = NONE
        if skel != NONE:
            blob = src.skeletons[skel]
            new_skel = self.skeletons.index(blob) if blob in self.skeletons else len(self.skeletons)
            if new_skel == len(self.skeletons):
                self.skeletons.append(blob)
        if mesh == NONE:
            self.items[name] = [data, NONE, new_skel]
            return
        first, count = src.meshes[mesh]
        mats = _copy_materials(self, src, [src.draws[d][1] for d in range(first, first + count)]) if count else []
        draws = []
        for k, d in enumerate(range(first, first + count)):
            a, _m, ib, vb, e, f = src.draws[d]
            vbuf = src.vbs[vb]
            fmt = src.formats[vbuf.kind]
            if fmt not in self.formats:
                self.formats.append(fmt)
            draws.append((a, mats[k], _share(self.ibs, src.ibs[ib]),
                          _share(self.vbs, Buffer(vbuf.data, vbuf.size, vbuf.count, self.formats.index(fmt),
                                                  vbuf.flags)), e, f))
        self.items[name] = [data, None, new_skel]
        self._renumber({name: draws})

    def _renumber(self, new: dict) -> None:
        """Number the meshes in name order again (their draw calls in mesh order), with `new` {name: draw calls}."""
        old_draws, old_meshes = self.draws, self.meshes
        self.meshes, self.draws = [], []
        for name in sorted(self.items, key=sort_key):
            item = self.items[name]
            if name in new:
                calls = new[name]
            elif item[1] == NONE:
                continue
            else:
                first, count = old_meshes[item[1]]
                calls = old_draws[first:first + count]
            # A draw call's first field is its own mesh's number, in every shipped pack (1,529 of 1,529 draws).
            calls = [(len(self.meshes), *c[1:]) for c in calls]
            item[1] = len(self.meshes)
            self.meshes.append((len(self.draws), len(calls)))
            self.draws += calls


def _buffers(raw: bytes, rows, start: int, total: int) -> list[Buffer]:
    """Each buffer's bytes up to the next one's (so the bytes between stay with it)."""
    out = []
    for i, (off, size, count, kind, flags) in enumerate(rows):
        stop = rows[i + 1][0] if i + 1 < len(rows) else total
        if stop < off + size:
            raise PackError("buffers out of order")
        out.append(Buffer(bytes(raw[start + off:start + stop]), size, count, kind, flags))
    return out


def _table(buffers: list[Buffer], pad: bool) -> tuple[bytes, bytes]:
    table, data = bytearray(), bytearray()
    for i, b in enumerate(buffers):
        table += struct.pack("<IIIHH", len(data), b.size, b.count, b.kind, b.flags)
        body = b.data[:b.size]
        tail = b.data[b.size:]
        data += body
        if i + 1 < len(buffers):  # the bytes up to the next buffer, which starts on a multiple of 4
            want = -len(data) % 4 if pad else 0
            data += tail[:want] if len(tail) >= want else tail + bytes([PAD]) * (want - len(tail))
    return bytes(table), bytes(data)


def _share(buffers: list[Buffer], b: Buffer) -> int:
    for i, have in enumerate(buffers):
        if (have.data[:have.size], have.count, have.kind, have.flags) == (b.data[:b.size], b.count, b.kind, b.flags):
            return i
    buffers.append(Buffer(b.data[:b.size], b.size, b.count, b.kind, b.flags))
    return len(buffers) - 1


# --- materials: copying TMeshMaterial objects between two packs' NDFs ---
def _material_list(nd: Ndf) -> list[int]:
    """The object number of each material number: the root object's list."""
    root = nd.objects[nd.topo[0]] if nd.topo else None
    if root is None or nd.classes[root.cls] != "TEugBListPBaseClass" or len(root.props) != 1:
        raise PackError("the materials have no root list")
    out = []
    for v in _subs(root.props[0][1]):
        if v.tc != 0x09 or v.payload[:4] != b"\xbb" * 4:
            raise PackError("the materials' root list holds something other than objects")
        out.append(struct.unpack_from("<I", v.payload, 4)[0])
    return out


def _subs(v: Value) -> list[Value]:
    b, out = v.payload, []
    count = struct.unpack_from("<I", b, 0)[0] if v.tc in (0x11, 0x12) else 2
    p = 4 if v.tc in (0x11, 0x12) else 0
    for _ in range(count * (2 if v.tc == 0x12 else 1)):
        x, p = _read_value(b, p)
        out.append(x)
    return out


def _texts(nd: Ndf, v: Value) -> list[str]:
    if v.tc in (0x07, 0x1C):
        return [nd.strings[struct.unpack_from("<I", v.payload)[0]]]
    if v.tc in (0x11, 0x12, 0x22):
        return [t for x in _subs(v) for t in _texts(nd, x)]
    return []


def _copy_materials(dst: MeshPack, src: MeshPack, numbers: list[int]) -> list[int]:
    """Copy materials `numbers` of `src` into `dst` (with the objects they refer to); their numbers in `dst`. A
    material `dst` already has, the same in every value, is shared."""
    s, d = Ndf(src.materials), Ndf(dst.materials)
    s_list, d_list = _material_list(s), _material_list(d)
    done: dict[int, int] = {}
    known: dict[bytes, int] = {}  # what an object of `dst` is (class and values) -> its number

    def ident(nd: Ndf, i: int) -> bytes:
        o = nd.objects[i]
        return nd.classes[o.cls].encode() + b"".join(nd.props[pi][0].encode() + v.encode() for pi, v in o.props)

    for i in range(len(d.objects)):
        known.setdefault(ident(d, i), i)

    def value(v: Value) -> Value:
        if v.tc in (0x07, 0x1C):
            text = s.strings[struct.unpack_from("<I", v.payload)[0]]
            at = d.string_index(text)
            return Value(v.tc, struct.pack("<I", d.add_string(text) if at is None else at))
        if v.tc == 0x09:
            tag, *rest = struct.unpack_from(f"<{len(v.payload) // 4}I", v.payload)
            if tag != 0xBBBBBBBB:
                raise PackError("a material refers to another file")
            inst, _cls = rest
            if inst == 0xFFFFFFFF:
                return v
            n = obj(inst)
            return Value(0x09, struct.pack("<III", tag, n, d.objects[n].cls))
        if v.tc in (0x11, 0x12):
            items = _subs(v)
            return Value(v.tc, struct.pack("<I", len(items) // (2 if v.tc == 0x12 else 1))
                         + b"".join(value(x).encode() for x in items))
        if v.tc == 0x22:
            return Value(v.tc, b"".join(value(x).encode() for x in _subs(v)))
        return Value(v.tc, v.payload)

    def obj(i: int) -> int:
        if i in done:
            return done[i]
        o = s.objects[i]
        cls = d.class_index(s.classes[o.cls])
        props = []
        for pi, v in o.props:
            pname, pcls = s.props[pi]
            want = (pname, d.class_index(s.classes[pcls]))
            at = next((k for k, p in enumerate(d.props) if p == want), None)
            props.append((d.add_prop(*want) if at is None else at, value(v)))
        key = d.classes[cls].encode() + b"".join(d.props[pi][0].encode() + v.encode() for pi, v in props)
        if key in known:
            done[i] = known[key]
        else:
            done[i] = known[key] = d.add_object(cls, props)
        return done[i]

    out = []
    for m in numbers:
        n = obj(s_list[m])
        if n not in d_list:
            d_list.append(n)
        out.append(d_list.index(n))
    root = d.objects[d.topo[0]]
    root.props[0] = (root.props[0][0], Value(0x11, struct.pack("<I", len(d_list)) + b"".join(
        Value(0x09, struct.pack("<III", 0xBBBBBBBB, n, d.objects[n].cls)).encode() for n in d_list)))
    dst.materials = d.to_logical()
    dst.material_count = len(d_list)
    return out


# --- texture stand-in packs ---
@dataclass
class Proxy:
    key: bytes      # 8 bytes
    data: bytes     # the stand-in .tgv
    extra: bytes    # the table row's last 8 bytes, as read
    name: bytes     # 256 bytes, zero-padded


@dataclass
class ProxyPack:
    """One PRXYPCPC pack. Stand-ins that share their picture are written once, as the game's are."""
    ident: bytes
    proxies: list = field(default_factory=list)  # Proxy, in the pack's order
    shared: list = field(default_factory=list)   # for each proxy, the number of the one whose bytes it uses (or its own)

    @classmethod
    def read(cls, raw: bytes) -> "ProxyPack":
        if raw[:8] != PROXY_MAGIC or struct.unpack_from("<I", raw, 8)[0] != 4:
            raise PackError(f"not a version 4 texture stand-in pack: {raw[:8]!r}")
        to, ts, do, ds, count, no, ns, count2 = struct.unpack_from("<8I", raw, 0x20)
        if count != count2 or ts != 24 * count or ns != 264 * count:
            raise PackError("its tables don't agree")
        pack = cls(bytes(raw[0x10:0x20]))
        first: dict[int, int] = {}
        for i in range(count):
            key, off, size, extra = struct.unpack_from("<8sII8s", raw, to + 24 * i)
            name = raw[no + 264 * i:no + 264 * i + 256]
            if raw[no + 264 * i + 256:no + 264 * (i + 1)] != key:
                raise PackError("a name whose key isn't its table row's")
            pack.proxies.append(Proxy(key, bytes(raw[do + off:do + off + size]), extra, bytes(name)))
            pack.shared.append(first.setdefault(off, i))
        return pack

    def names(self) -> list[str]:
        return [p.name.split(b"\0", 1)[0].decode("latin-1") for p in self.proxies]

    def to_bytes(self) -> bytes:
        table, data, names, at = bytearray(), bytearray(), bytearray(), {}
        for i, p in enumerate(self.proxies):
            j = self.shared[i]
            if j not in at:
                at[j] = len(data)
                data += p.data
            table += struct.pack("<8sII8s", p.key, at[j], len(p.data), p.extra)
            names += p.name + p.key
        n = len(self.proxies)
        out = bytearray(0x40)
        out[0:8] = PROXY_MAGIC
        to, do = 0x40, 0x40 + len(table)
        no = do + len(data)
        struct.pack_into("<II", out, 0x08, 4, no + len(names))
        out[0x10:0x20] = self.ident
        struct.pack_into("<8I", out, 0x20, to, len(table), do, len(data), n, no, len(names), n)
        return bytes(out + table + data + names)

    def renew(self) -> None:
        self.ident = hashlib.md5(self.to_bytes()).digest()

    def add(self, src: "ProxyPack", name: str) -> None:
        """Copy the stand-in `name` (gentexproxy\\...\\x01.tgv) of `src` in, in name order; a picture this pack
        already has is shared."""
        names = self.names()
        if name in names:
            raise PackError(f"{name} is already in the pack")
        p = src.proxies[src.names().index(name)]
        same = next((self.shared[i] for i, q in enumerate(self.proxies) if q.data == p.data), None)
        at = next((i for i, n in enumerate(names) if sort_key(n) > sort_key(name)), len(names))
        self.proxies.insert(at, p)
        self.shared = [j + (j >= at) for j in self.shared]
        self.shared.insert(at, at if same is None else same + (same >= at))


def proxy_name(texture: str) -> str:
    """The stand-in of a material's image: ZZ:\\GenTexGroup\\WW2\\...\\X01.png -> gentexproxy\\ww2\\...\\x01.tgv."""
    p = texture.replace("/", "\\")
    for head in ("zz:\\gentexgroup\\", "zz:\\"):
        if p.lower().startswith(head):
            p = p[len(head):]
            break
    if p.lower().endswith((".png", ".tga", ".dds")):
        p = p[:-4] + ".tgv"
    return ("gentexproxy\\" + p).lower()


def animation_name(model: str) -> str:
    """The animation a descriptor's model name stands for: ww2\\...\\canon_idlelod0.ase2ndfbin ->
    genanim_15\\ww2\\...\\canon_idlelod0.baf."""
    return "genanim_15\\" + model[:-len(MODEL)] + ".baf" if model.endswith(MODEL) else model


# --- animation packs: EDAT archives, written whole ---
def archive_with(raw: bytes, add: dict[str, bytes]) -> bytes:
    """The EDAT archive `raw` with the files `add` {path: bytes} put in, laid out as the game's animation packs are:
    the dictionary in name order (the same trie as a mesh pack's, a file's 9 bytes being its offset, size and a flag)
    and the files' data in the same order, one after the other. With nothing to add it is `raw` again."""
    arc = Edat(raw)
    files = {e.path: (bytes(arc.read(e)), e.flag) for e in arc.entries}
    have = {p.lower() for p in files}
    for path, data in add.items():
        if path.lower() in have:
            raise PackError(f"{path} is already in the archive")
        files[path] = (bytes(data), 0)
    order = sorted(files, key=sort_key)
    entries, pos = [], 0
    for path in order:
        data, flag = files[path]
        entries.append((path, struct.pack("<IIB", pos, len(data), flag)))
        pos += len(data)
    names = (NAMES_HEAD + write_names(entries)) if entries else b"\x01" + bytes(9)
    head = bytearray(raw[:arc.dict_offset])
    struct.pack_into("<IIII", head, 0x19, arc.dict_offset, len(names), arc.dict_offset + len(names), pos)
    return bytes(head) + names + b"".join(files[p][0] for p in order)


# --- giving a nation (or every skirmish) a unit's models ---
TAGS = ("us", "ger", "uk", "fr", "ita", "urss", "japan")  # by Nationalite, as the packs are named
COMMON = "common"


def pack_paths(tag: str) -> dict[str, list[str]]:
    """The packs of ZZ_Win.dat a skirmish loads for `tag` (a nation's, or COMMON: every skirmish), by kind."""
    boat = tag == "us"
    return {"mesh": [f"{MESH_DIR}meshskirmish_{tag}.spk"] + ([f"{MESH_DIR}meshskirmishwitboat_us.spk"] if boat else []),
            "skeleton": [f"{MESH_DIR}skeleton_{tag}.spk"],
            "proxy": [f"{PROXY_DIR}proxyskirmish_{tag}.ppk"] + ([f"{PROXY_DIR}proxyskirmishwitboat_us.ppk"] if boat
                                                                 else []),
            "anim": [f"{ANIM_DIR}gfxdescriptor_{tag}.apk"]}


@dataclass
class Given:
    """What `Packs.give` copied for one nation: the models' meshes, skeletons, animations and texture stand-ins."""
    meshes: list = field(default_factory=list)
    skeletons: list = field(default_factory=list)
    animations: list = field(default_factory=list)
    textures: list = field(default_factory=list)
    sources: list = field(default_factory=list)  # the nations (tags) they came from

    def __bool__(self) -> bool:
        return bool(self.meshes or self.skeletons or self.animations or self.textures)

    def summary(self) -> str:
        parts = [(len(self.meshes), "mesh", "meshes"), (len(self.skeletons), "skeleton", "skeletons"),
                 (len(self.animations), "animation", "animations"),
                 (len(self.textures), "texture stand-in", "texture stand-ins")]
        return ", ".join(f"{n} {one if n == 1 else more}" for n, one, more in parts if n)


class Packs:
    """The skirmish unit packs of ZZ_Win.dat (`arc`), read when first needed, and the models copied into them."""

    def __init__(self, arc: Edat):
        self.arc = arc
        self._packs: dict[str, object] = {}
        self._apk_added: dict[str, dict[str, bytes]] = {}
        self.changed: set[str] = set()

    def pack(self, path: str):
        """A pack by its path in ZZ_Win.dat (MeshPack, ProxyPack, or an animation pack's Edat); None if missing."""
        if path not in self._packs:
            e = self.arc.entry(path)
            raw = bytes(self.arc.read(e)) if e is not None else None
            if raw is None:
                self._packs[path] = None
            elif path.endswith(".spk"):
                self._packs[path] = MeshPack.read(raw)
            elif path.endswith(".ppk"):
                self._packs[path] = ProxyPack.read(raw)
            else:
                self._packs[path] = Edat(raw)
        return self._packs[path]

    def _has(self, kind: str, tag: str, name: str) -> bool:
        """Whether every pack of this kind `tag` loads has `name` (a model, or an animation or stand-in path)."""
        found = [self._find(path, kind, name) for path in pack_paths(tag)[kind] if self.pack(path) is not None]
        return bool(found) and all(found)

    def _find(self, path: str, kind: str, name: str) -> bool:
        p = self.pack(path)
        if p is None:
            return False
        if kind in ("mesh", "skeleton"):
            return name in p.items
        if kind == "proxy":
            return name in p.names()
        return p.entry(name) is not None or name in self._apk_added.get(path, {})

    def _source(self, kind: str, name: str, prefer: list[str]) -> str | None:
        """The first pack of this kind that has `name`, from the nations `prefer` first, then the others."""
        for tag in list(dict.fromkeys(list(prefer) + list(TAGS))):
            for path in pack_paths(tag)[kind]:
                if self._find(path, kind, name):
                    return path
        return None

    def give(self, models, tag: str, prefer=()) -> tuple[Given, list[str]]:
        """Copy what the models `models` (lower-case names, as rusemod.unitcheck.model_files gives them) need into
        the packs `tag` loads, from the packs of the nations that have them (`prefer` first): their meshes,
        skeletons, animations and their textures' stand-ins. What `tag`'s packs, or the common ones, already have is
        left as it is. Returns what was copied and, when something can't be, why (then nothing is copied)."""
        plan: list[tuple[str, str, str]] = []  # (kind, source pack, name)
        why: list[str] = []
        targets = pack_paths(tag)

        def loaded(kind: str, name: str) -> bool:
            return self._has(kind, tag, name) or (tag != COMMON and self._has(kind, COMMON, name)) \
                or any(k == kind and n == name for k, _s, n in plan)

        def want(kind: str, name: str, prefer) -> str | None:
            """Plan copying `name` in; the pack it comes from (None: no pack has it, or it can't go in)."""
            src = self._source(kind, name, prefer)
            if src is None:
                return None
            missing = [p for p in targets[kind] if self.pack(p) is None]
            if missing:
                why.append(f"ZZ_Win.dat has no {missing[0].rsplit(chr(92), 1)[-1]} to copy {name} into")
                return None
            plan.append((kind, src, name))
            return src
        for model in models:
            src = None if loaded("mesh", model) else want("mesh", model, prefer)
            home = [t for t in TAGS if src in pack_paths(t)["mesh"]] + list(prefer)
            if not loaded("skeleton", model) and want("skeleton", model, home) is None and src is not None \
                    and self._source("skeleton", model, home) is None and self.pack(src).bones(model):
                why.append(f"no skeleton pack has the skeleton of {model}, which its mesh needs")
            anim = animation_name(model)
            if not loaded("anim", anim):
                want("anim", anim, home)
            for texture in self.pack(src).textures(model) if src is not None else []:
                stand_in = proxy_name(texture)
                if not loaded("proxy", stand_in) and want("proxy", stand_in, home) is None:
                    why.append(f"no texture stand-in pack has {stand_in}, a texture of {model}")
        if why:
            return Given(), why
        given = Given()
        for kind, src, name in plan:
            for path in targets[kind]:
                if self._find(path, kind, name):
                    continue
                if kind == "anim":
                    self._apk_added.setdefault(path, {})[name] = self._animation(src, name)
                else:
                    self.pack(path).add(self.pack(src), name)
                self.changed.add(path)
            {"mesh": given.meshes, "skeleton": given.skeletons, "anim": given.animations,
             "proxy": given.textures}[kind].append(name)
            source = next(t for t in TAGS + (COMMON,) if src in pack_paths(t)[kind])
            if source not in given.sources:
                given.sources.append(source)
        return given, []

    def _animation(self, path: str, name: str) -> bytes:
        added = self._apk_added.get(path, {})
        if name in added:
            return added[name]
        arc = self.pack(path)
        return bytes(arc.read(arc.entry(name)))

    def output(self) -> dict[str, bytes]:
        """{path in ZZ_Win.dat: new bytes} of every pack models were copied into."""
        out = {}
        for path in sorted(self.changed):
            e = self.arc.entry(path)
            p = self.pack(path)
            if path.endswith(".apk"):
                out[e.path] = archive_with(bytes(self.arc.read(e)), self._apk_added[path])
            else:
                p.renew()
                out[e.path] = p.to_bytes()
        return out
