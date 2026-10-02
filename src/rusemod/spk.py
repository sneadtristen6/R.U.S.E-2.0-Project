"""3D models (.spk mesh packs, magic MESHPCPC, version 4): read the models of buildings, trees and units, for drawing.

The layout is from the notes of DomesticNukes and his Claude (2026-09-29), checked here on every mesh pack the game
ships (tools/verify_spk.py; FORMATS.md §8). A pack (`gen_5\\pack\\*.spk` in ZZ_Win.dat) holds many models:

  header     `MESH` `PCPC`, u32 version 4, u32 file size, 16-byte hash; at 0x34 eight sections (u32 offset, size,
             count): names, vertex formats, materials, two empty ones, meshes, draw calls, the index-buffer table;
             at 0x94 the index-buffer data (offset, size), at 0x9C the vertex-buffer table (offset, size, count),
             at 0xA8 the vertex-buffer data (offset, size)
  names      a trie like an EDAT archive's (u32 header length, u32 next sibling; header length 0 = a model: its
             bounding box, flags, mesh number and skeleton record, then the last piece of its name)
  formats    u32 256, then one 256-byte name per vertex format, spelling the layout (TVertex__Position_3f__...)
  materials  an NDF holding one TMeshMaterial per material, in order: its textures (diffuseTexture: an atlas)
  mesh       u16 first draw call, u16 draw-call count
  draw call  u16, u16 material, u16 index buffer, u16 vertex buffer, u16 0xFFFF, u16 0xCDCD
  IB, VB     16-byte table rows: u32 offset (from the data start), u32 size, u32 count, u16 (1 / vertex format),
             u16 flags: 0xC000 = compressed, 0 = stored as is (most scenery)

A compressed index buffer is u32 size + zlib (sync flush): u16 differences, summed. A compressed vertex buffer is a
VBUF chunk like the terrain's (rusemod.tms): a predictor, then one SUBP stream per vertex component, each quantized
and stored relative to its parent vertex. Models are drawn as they are: scenery has no skeletons.
"""
from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass, field

from .tms import decode_parents, lz_decode

MAGIC = b"MESHPCPC"
SECTIONS = ("names", "formats", "materials", "empty1", "empty2", "meshes", "draws", "ib_table")
COMPRESSED = 0xC000
FORMAT_NAME = 256

# The vertex components a format name can spell, with their size in bytes (DomesticNukes' table).
COMPONENTS = {"Position_3f": 12, "NormalIn01_4ubn": 4, "NormalAndChenilleIndexIn01_4ubn": 4, "BlW_4ubn": 4,
              "BlIdx_4ub": 4, "TexCoord0_2wn": 4, "TexCoord0_2f": 8, "TexPackedAtlas0_4ubn": 4,
              "TexPackedAtlas1_4ubn": 4, "Color_4ub": 4, "Color0_4ub": 4, "TexCoord1_2wn": 4, "TexCoord1_2f": 8,
              "Color0_col32": 4}  # the maps' road mesh (staticmeshes): RGBA bytes
UV_WORD = 65535.0  # a stored `_2wn` UV is value / 65535 (not confirmed in-game; compressed ones use their own mask)


class SpkError(ValueError):
    pass


@dataclass
class Item:
    """A model's entry in the pack's name table."""
    name: str                 # lowercase path: ww2\res3d\decors\vegetation_eu\022lod0.ase2ndfbin
    box: tuple                # min x, y, z, max x, y, z (model units)
    flags: int
    mesh: int                 # its mesh number
    skeleton: int             # skeleton record (0xCDCD: none)


@dataclass
class Part:
    """One draw call of a model, decoded: flat lists ready to draw."""
    material: int
    positions: list           # x, y, z per vertex
    normals: list             # x, y, z per vertex (-1..1)
    uvs: list                 # u, v per vertex, already moved into the atlas when the vertex has atlas bytes
    indices: list             # triangles: 3 vertex numbers each
    atlas: list = field(default_factory=list)  # the raw atlas bytes per vertex (min u, min v, width, height) × 255


def layout(format_name: str) -> list[tuple[str, int, int]]:
    """(component, offset, size) of each part of a vertex, in order, from its format name."""
    tail = format_name.rsplit("/", 1)[-1]
    if not tail.startswith("TVertex__"):
        raise SpkError(f"not a vertex format name: {format_name!r}")
    out, at = [], 0
    for comp in tail[len("TVertex__"):].split("__"):
        size = COMPONENTS.get(comp)
        if size is None:
            m = re.search(r"_(\d)(f|ub|ubn|w|wn)$", comp)
            if not m:
                raise SpkError(f"unknown vertex component {comp!r}")
            size = int(m.group(1)) * {"f": 4, "ub": 1, "ubn": 1, "w": 2, "wn": 2}[m.group(2)]
        out.append((comp, at, size))
        at += size
    return out


class Spk:
    """One mesh pack. `items` maps each model's name to its Item; `model(name)` decodes it."""

    def __init__(self, raw: bytes):
        if raw[:8] != MAGIC:
            raise SpkError(f"not a mesh pack: {raw[:8]!r}")
        self.raw = raw
        self.version = struct.unpack_from("<I", raw, 8)[0]
        if self.version != 4:
            raise SpkError(f"mesh pack version {self.version}; only 4 is known")
        self.sections = {name: struct.unpack_from("<III", raw, 0x34 + 12 * i) for i, name in enumerate(SECTIONS)}
        self.ib_data = struct.unpack_from("<II", raw, 0x94)
        vb_off, vb_size, vb_count = struct.unpack_from("<III", raw, 0x9C)
        self.vb_data = struct.unpack_from("<II", raw, 0xA8)
        fo, _fs, fc = self.sections["formats"]
        width = struct.unpack_from("<I", raw, fo)[0]
        if width != FORMAT_NAME:
            raise SpkError(f"vertex format names of {width} bytes; 256 expected")
        self.formats = [raw[fo + 4 + FORMAT_NAME * i:fo + 4 + FORMAT_NAME * (i + 1)].split(b"\0", 1)[0].decode("latin-1")
                        for i in range(fc)]
        mo, _ms, mc = self.sections["meshes"]
        self.meshes = [struct.unpack_from("<HH", raw, mo + 4 * i) for i in range(mc)]
        do, _ds, dc = self.sections["draws"]
        self.draws = [struct.unpack_from("<HHHH", raw, do + 12 * i)[1:] for i in range(dc)]  # material, ib, vb
        io, _is, ic = self.sections["ib_table"]
        self.ibs = [struct.unpack_from("<IIIHH", raw, io + 16 * i) for i in range(ic)]
        self.vbs = [struct.unpack_from("<IIIHH", raw, vb_off + 16 * i) for i in range(vb_count)]
        self.items: dict[str, Item] = {}
        no, ns, _nc = self.sections["names"]
        if struct.unpack_from("<I", raw, no)[0] != 0x0A or not self.meshes:
            raise SpkError("no meshes: a skeleton pack (its own layout, not read here)")
        self._walk(no + 10, no + ns, "")
        self._materials = None

    def _walk(self, pos: int, end: int, prefix: str) -> None:
        raw = self.raw
        while pos + 8 <= end:
            head, sibling = struct.unpack_from("<II", raw, pos)
            if head == 0:  # a model
                box = struct.unpack_from("<6f", raw, pos + 8)
                flags, mesh, skeleton = struct.unpack_from("<IHH", raw, pos + 32)
                stop = raw.index(b"\0", pos + 40)
                name = prefix + raw[pos + 40:stop].decode("latin-1")
                self.items[name.lower()] = Item(name.lower(), box, flags, mesh, skeleton)
            else:
                stop = raw.index(b"\0", pos + 8)
                piece = raw[pos + 8:stop].decode("latin-1")
                if head >= stop + 1 - pos:
                    self._walk(pos + head, end, prefix + piece)
            if sibling == 0:
                return
            pos += sibling

    # --- materials ---
    def materials(self) -> list[dict]:
        """Each material's name and textures ({role: path}), in order (a draw call's material number)."""
        if self._materials is None:
            from .ndf import Ndf
            mo, ms, _mc = self.sections["materials"]
            nd = Ndf(self.raw[mo:mo + ms])
            out = []
            for obj in nd.objects:
                if nd.classes[obj.cls] != "TMeshMaterial":
                    continue
                out.append(_material(nd, obj))
            self._materials = out
        return self._materials

    # --- buffers ---
    def indices(self, n: int) -> list[int]:
        off, size, count, _one, flags = self.ibs[n]
        data = self.raw[self.ib_data[0] + off:self.ib_data[0] + off + size]
        if flags & COMPRESSED:
            unpacked = struct.unpack_from("<I", data, 0)[0]
            raw = zlib.decompressobj().decompress(data[4:])
            if len(raw) < unpacked:
                raise SpkError(f"index buffer {n}: {len(raw)} of {unpacked} bytes")
            diffs = struct.unpack_from(f"<{count}H", raw, 0)
            out, v = [], 0
            for d in diffs:
                v = (v + d) & 0xFFFF
                out.append(v)
            return out
        return list(struct.unpack_from(f"<{count}H", data, 0))

    def vertices(self, n: int) -> tuple[list[tuple[str, int, int]], dict[str, list]]:
        """The vertex buffer `n`: its layout and each component's values per vertex ({component: [tuple, ...]})."""
        off, size, count, fmt, flags = self.vbs[n]
        parts = layout(self.formats[fmt])
        data = self.raw[self.vb_data[0] + off:self.vb_data[0] + off + size]
        if flags & COMPRESSED:
            return parts, _vbuf(data, count, parts)
        stride = sum(s for _c, _o, s in parts)
        if stride * count != size:
            raise SpkError(f"vertex buffer {n}: {size} bytes for {count} vertices of {stride}")
        out = {}
        for comp, at, sz in parts:
            code = _code(comp, sz)
            out[comp] = [struct.unpack_from(code, data, i * stride + at) for i in range(count)]
        return parts, out

    # --- a model ---
    def model(self, name: str) -> list[Part]:
        """A model's draw calls, decoded (positions, normals, UVs in the atlas, triangles)."""
        item = self.items[name.lower()]
        if item.mesh >= len(self.meshes):
            raise SpkError(f"{name}: mesh {item.mesh} of {len(self.meshes)}")
        first, count = self.meshes[item.mesh]
        return [self.part(d) for d in range(first, first + count)]

    def part(self, d: int) -> Part:
        material, ib, vb = self.draws[d]
        _parts, comps = self.vertices(vb)
        pos = [c for p in comps["Position_3f"] for c in p]
        nrm_key = next((k for k in comps if k.startswith("Normal")), None)
        nrm = [c / 255.0 * 2 - 1 for n in comps[nrm_key] for c in n[:3]] if nrm_key else []
        uv_key = next((k for k in comps if k.startswith("TexCoord0")), None)
        uvs = list(comps[uv_key]) if uv_key else []
        if uv_key == "TexCoord0_2wn" and uvs and isinstance(uvs[0][0], int):
            uvs = [(u / UV_WORD, v / UV_WORD) for u, v in uvs]
        atlas = comps.get("TexPackedAtlas0_4ubn", [])
        if atlas and uvs:  # each vertex's UV runs inside its sub-texture of the atlas
            uvs = [(a[0] / 255 + u * a[2] / 255, a[1] / 255 + v * a[3] / 255) for (u, v), a in zip(uvs, atlas)]
        return Part(material, pos, nrm, [c for p in uvs for c in p], self.indices(ib), [list(a) for a in atlas])


def _code(comp: str, size: int) -> str:
    if comp.endswith("_3f"):
        return "<3f"
    if comp.endswith("_2f"):
        return "<2f"
    if comp.endswith("_2wn") or comp.endswith("_2w"):
        return "<2H"
    if comp.endswith("_1f"):
        return "<f"
    if size == 4:
        return "<4B"
    raise SpkError(f"no reader for {comp}")


def _material(nd, obj) -> dict:
    """A TMeshMaterial's name, type and textures ({role: path}, e.g. diffuseTexture: an atlas image, named like
    ZZ:/GenTexGroup/.../TSCVegetation_diffuseTexture01.png with backslashes) from its NDF values."""
    from .ndf import sub_values

    def text(v):
        return nd.strings[struct.unpack("<I", v.payload)[0]] if v.tc in (0x07, 0x1C) else None

    out = {"name": "", "type": "", "textures": {}}
    for pi, v in obj.props:
        prop = nd.prop_name(pi)
        if prop == "MaterialName":
            out["name"] = text(v) or ""
        elif prop == "MaterialType":
            out["type"] = text(v) or ""
        elif prop == "Textures":  # a map, stored as key, value, key, value: role -> (path, number)
            items = sub_values(v)
            for key, value in zip(items[0::2], items[1::2]):
                path = next((text(x) for x in ([value] + sub_values(value)) if text(x)), None)
                if text(key) and path:
                    out["textures"][text(key)] = path
    return out


# --- compressed vertex buffers (VBUF): the terrain's scheme, with more component kinds ---
def _stream(payload: bytes, storage: int) -> bytes:
    if storage == 0:
        return payload
    if storage == 1:
        return zlib.decompressobj().decompress(payload)
    if storage == 3:
        return lz_decode(payload)
    raise SpkError(f"unknown stream storage {storage}")


def _vbuf(data: bytes, count: int, parts) -> dict[str, list]:
    if data[:4] != b"VBUF":
        raise SpkError(f"compressed vertex buffer without VBUF: {data[:4]!r}")
    hlen = struct.unpack_from("<H", data, 4)[0]
    _b, stride, nstreams, flags = struct.unpack_from("<BHHB", data, 6)
    p = 4 + hlen
    parents = [max(i - 1, 0) for i in range(count)]
    if flags & 2:
        size = struct.unpack_from("<I", data, p)[0]
        parents = decode_parents(lz_decode(data, p + 4), count)
        p = p + 4 + ((size + 3) & ~3)
    by_offset = {at: (comp, sz) for comp, at, sz in parts}
    out: dict[str, list] = {}
    for _ in range(nstreams):
        if data[p:p + 4] != b"SUBP":
            raise SpkError(f"expected SUBP at {p:#x}")
        eh = struct.unpack_from("<H", data, p + 4)[0]
        kind, storage, mode, _fmt, offset, mirrors = struct.unpack_from("<BBBHHH", data, p + 6)
        p += 4 + eh
        size = struct.unpack_from("<I", data, p)[0]
        s = _stream(data[p + 4:p + 4 + size], storage)
        p += 4 + ((size + 3) & ~3)
        comp, _sz = by_offset.get(offset, (f"@{offset}", 0))
        if mirrors:
            raise SpkError("mirrored vertices aren't read (no shipped pack uses them)")
        out[comp] = _component(s, kind, mode, count, parents)
    return out


def _predicted(values: list, n: int, width: int, mask: int, parents, mode: int) -> list:
    rows = [values[i * width:(i + 1) * width] for i in range(n)]
    if mode != 2:
        return [tuple(r) for r in rows]
    out = [tuple(rows[0])]
    for i in range(1, n):
        par = out[parents[i]]
        out.append(tuple((a + b) & mask for a, b in zip(rows[i], par)))
    return out


def _dequant(q: int, Q: int, lo: float, hi: float) -> float:
    t = q / Q
    return lo + t * (hi - lo) if t <= 0.5 else hi - (1 - t) * (hi - lo)


def _component(s: bytes, kind: int, mode: int, n: int, parents) -> list:
    if kind == 2:  # float3 (positions): u16 Q, 3 f32 min, 3 f32 max, u16 pad, then 3 u16 per vertex
        Q = struct.unpack_from("<H", s, 0)[0]
        lo, hi = struct.unpack_from("<3f", s, 2), struct.unpack_from("<3f", s, 14)
        vals = _predicted(struct.unpack_from(f"<{3 * n}H", s, 28), n, 3, Q, parents, mode)
        return [tuple(_dequant(v[k], Q, lo[k], hi[k]) for k in range(3)) for v in vals]
    if kind == 1:  # float2 (UVs as _2f): u16 Q, 2 f32 min, 2 f32 max, u16 pad, then 2 u16 per vertex
        Q = struct.unpack_from("<H", s, 0)[0]
        lo, hi = struct.unpack_from("<2f", s, 2), struct.unpack_from("<2f", s, 10)
        vals = _predicted(struct.unpack_from(f"<{2 * n}H", s, 20), n, 2, Q, parents, mode)
        return [tuple(_dequant(v[k], Q, lo[k], hi[k]) for k in range(2)) for v in vals]
    if kind == 6:  # word2 (UVs as _2wn): u16 mask, u16 0, then 2 u16 per vertex; uv = value / mask
        mask = struct.unpack_from("<H", s, 0)[0]
        vals = _predicted(struct.unpack_from(f"<{2 * n}H", s, 4), n, 2, mask, parents, mode)
        return [(u / mask, v / mask) for u, v in vals]
    if kind == 4:  # ubyte4 (normals, atlas bytes, bone weights and indices)
        return _predicted(list(s[:4 * n]), n, 4, 0xFF, parents, mode)
    raise SpkError(f"unknown vertex stream kind {kind}")
