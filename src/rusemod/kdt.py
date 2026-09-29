"""Gameplay ground (.kdt): the streamed kd-tree mesh of a map's ground and camera floor, read and written.

Every map pack holds two, output\\occlusioninfo_terrainonly.kdt (the ground gameplay runs on) and
output\\occlusioninfo_camera.kdt (the camera floor). Each is an NDF binary with one TStreamedMeshKdTree object: the
bounds, a triangle count, eight OffsetOf* offsets into Storage, and Storage itself, a blob that holds one mesh per
subtree (a positions chunk, a normals chunk, an index buffer, a triangle list, the subtree's own node data) plus
the MainNode bytes and the index tables that point at all of it. Layout in docs/FORMATS.md §6.

Positions and normals are decoded and re-encoded; the index buffers, triangle lists, MainNode and subtree chunks are
kept as opaque bytes. Unchanged chunks keep their original compressed bytes, so an unchanged file re-serializes
byte-for-byte; the writer rebuilds every table, the padding and the offset properties from the parts.
"""
from __future__ import annotations

import math
import struct
import zlib
from dataclasses import dataclass

from .ndf import Ndf
from .tms import encode_parents

CLASS = "TStreamedMeshKdTree"
MEMBERS = {"ground": "output\\occlusioninfo_terrainonly.kdt", "camera": "output\\occlusioninfo_camera.kdt"}
Q_MASK = 0x7FFF        # quantized positions span 0..32767 over the bounding box, like the .tms meshes
FILL = 0xAA            # the byte the writer pads a positions chunk with (the game's packer leaves memory junk there)
OFFSETS = ("OffsetOfVertexBufferIndexes", "OffsetOfIndexBuffer", "OffsetOfIndexBufferIndexes",
           "OffsetOfTriangleIndexLists", "OffsetOfTriangleIndexBufferIndexes", "OffsetOfMainNode",
           "OffsetOfCompressedSubtreeIndexBuffer", "OffsetOfCompressedSubtrees")
BLOB = 0x14            # NDF type code of Storage: u32 length + bytes

# ---------------------------------------------------------------------------------------------------------------
# Chunks: u32 L, u32 inflated size, then a zlib stream of L - 4 bytes ended by a sync flush (no final block).


def read_chunk(blob: bytes, off: int) -> tuple[bytes, int]:
    """The framed chunk starting at `off` (its bytes, unchanged) and the offset after it."""
    if off + 8 > len(blob):
        raise ValueError(f"chunk header at {off:#x} runs past the end")
    ln = struct.unpack_from("<I", blob, off)[0]
    end = off + 4 + ln
    if ln < 4 or end > len(blob):
        raise ValueError(f"chunk at {off:#x} runs past the end")
    return bytes(blob[off:end]), end


def inflate(chunk: bytes) -> bytes:
    """The content of a framed chunk."""
    size = struct.unpack_from("<I", chunk, 4)[0]
    out = zlib.decompressobj().decompress(chunk[8:])
    if len(out) != size:
        raise ValueError(f"chunk inflated to {len(out)} bytes, expected {size}")
    return out


def compress(data: bytes) -> bytes:
    """Frame `data` as a chunk: our own zlib bytes (sync flush, no final block), the same content once inflated."""
    co = zlib.compressobj(9)
    stream = co.compress(data) + co.flush(zlib.Z_SYNC_FLUSH)
    return struct.pack("<II", len(stream) + 4, len(data)) + stream


def chunk_size(chunk: bytes) -> int:
    """The inflated size a framed chunk announces."""
    return struct.unpack_from("<I", chunk, 4)[0]


# ---------------------------------------------------------------------------------------------------------------
# Positions chunk: u32 n, u32 mask 0x7FFF, 3n u16 residuals, the parent codes (as in the .tms predictor: 0 = the
# previous vertex, 0x80|hi then lo = that many vertices back; vertices 0 and 1 have parent 0), then fill bytes up
# to 8 + 12n. A coordinate is (residual + the parent's coordinate) & 0x7FFF.


def decode_positions(data: bytes) -> tuple[list[tuple[int, int, int]], list[int]]:
    """Inflated positions chunk -> (quantized (x, y, z) per vertex, parent per vertex)."""
    n, mask = struct.unpack_from("<II", data, 0)
    if mask != Q_MASK or len(data) != 8 + 12 * n:
        raise ValueError(f"unsupported positions chunk (mask {mask:#x}, {len(data)} bytes for {n} vertices)")
    res = struct.unpack_from(f"<{3 * n}H", data, 8)
    par, q = [0] * n, 8 + 6 * n
    for i in range(2, n):
        b0 = data[q]
        if b0:
            par[i] = i - ((b0 & 0x7F) << 8 | data[q + 1])
            q += 2
        else:
            par[i] = i - 1
            q += 1
        if not 0 <= par[i] < i:
            raise ValueError(f"vertex {i}: parent {par[i]} out of range")
    pos: list[tuple[int, int, int]] = []
    for i in range(n):
        p = pos[par[i]] if i else (0, 0, 0)
        pos.append(((res[3 * i] + p[0]) & mask, (res[3 * i + 1] + p[1]) & mask, (res[3 * i + 2] + p[2]) & mask))
    return pos, par


def encode_positions(positions: list, parents: list[int] | None = None) -> bytes:
    """Positions (quantized (x, y, z) per vertex) -> inflated positions chunk. Without `parents` every vertex is
    stored relative to the previous one."""
    n = len(positions)
    if parents is None:
        parents = [max(i - 1, 0) for i in range(n)]
    if len(parents) != n or any(parents[i] != 0 for i in range(min(n, 2))) or \
            any(not 0 <= parents[i] < i for i in range(2, n)):
        raise ValueError("parents must have one entry per vertex, 0 for the first two, earlier vertices after")
    res: list[int] = []
    for i, q in enumerate(positions):
        if len(q) != 3 or min(q) < 0 or max(q) > Q_MASK:
            raise ValueError(f"vertex {i}: position {q} out of range")
        p = positions[parents[i]] if i else (0, 0, 0)
        res += ((q[0] - p[0]) & Q_MASK, (q[1] - p[1]) & Q_MASK, (q[2] - p[2]) & Q_MASK)
    out = struct.pack(f"<II{3 * n}H", n, Q_MASK, *res) + encode_parents(parents)
    return out + bytes([FILL]) * (8 + 12 * n - len(out))


# ---------------------------------------------------------------------------------------------------------------
# Normals chunk: one u32 per vertex. Bits 0-3: the dominant axis k and its sign (0 -x, 1 +x, 2 -y, 3 +y, 4 -z, 5 +z).
# The two other components divided by |n[k]|: a = n[(k+1)%3] / |n[k]| in bits 16-31 as round(a * 32768) + 32768,
# b = n[(k+2)%3] / |n[k]| in bits 4-15 as round(b * 8192) as 12-bit two's complement, which wraps when |b| > 0.25.


def decode_normal(word: int) -> tuple[float, float, float]:
    """One packed normal -> unit (nx, ny, nz)."""
    tag = word & 15
    if tag > 5:
        raise ValueError(f"normal {word:#010x}: unknown axis tag {tag}")
    k = tag >> 1
    a = ((word >> 16) - 32768) / 32768
    b = (word >> 4) & 0xFFF
    b = (b - 4096 if b & 0x800 else b) / 8192
    n = [0.0, 0.0, 0.0]
    n[k] = 1.0 if tag & 1 else -1.0
    n[(k + 1) % 3] = a
    n[(k + 2) % 3] = b
    length = math.sqrt(1.0 + a * a + b * b)
    return (n[0] / length, n[1] / length, n[2] / length)


def encode_normal(n) -> int:
    """(nx, ny, nz), any length -> packed normal. On a tie the later axis is the dominant one (what the shipped
    data does); a is clamped to the 16-bit field; b wraps like the game's own packer."""
    k = 0
    for i in (1, 2):
        if abs(n[i]) >= abs(n[k]):
            k = i
    d = abs(n[k])
    if d == 0:
        raise ValueError("normal has no length")
    a = n[(k + 1) % 3] / d
    b = n[(k + 2) % 3] / d
    hi = min(max(int(round(a * 32768)) + 32768, 0), 0xFFFF)
    mid = int(round(b * 8192)) & 0xFFF
    return hi << 16 | mid << 4 | 2 * k + (1 if n[k] > 0 else 0)


def decode_normals(data: bytes) -> list[tuple[float, float, float]]:
    """Inflated normals chunk -> unit normal per vertex."""
    if len(data) % 4:
        raise ValueError("normals chunk is not whole words")
    return [decode_normal(w) for w in struct.unpack(f"<{len(data) // 4}I", data)]


def encode_normals(normals: list) -> bytes:
    """Normals -> inflated normals chunk."""
    return struct.pack(f"<{len(normals)}I", *(encode_normal(n) for n in normals))


# ---------------------------------------------------------------------------------------------------------------
# The file.

@dataclass
class Subtree:
    """One subtree's parts, each a framed chunk kept as read (or as re-encoded)."""
    positions: bytes
    normals: bytes
    index_count: int    # the u32 before the index buffer chunk
    indices: bytes      # opaque
    trilist: bytes      # opaque
    tree: bytes         # opaque: the subtree's own node data

    @property
    def count(self) -> int:
        """Vertices in this subtree (from the positions chunk header, without inflating the rest)."""
        head = zlib.decompressobj().decompress(self.positions[8:], 8)
        n, mask = struct.unpack_from("<II", head, 0)
        if mask != Q_MASK or chunk_size(self.positions) != 8 + 12 * n or chunk_size(self.normals) != 4 * n:
            raise ValueError("positions and normals chunks disagree on the vertex count")
        return n


class Kdt:
    """A parsed .kdt file: `subtrees`, `main_node`, the bounds and counts, and the NDF wrapper it came in."""

    def __init__(self, raw: bytes):
        self.ndf = Ndf(raw)
        if len(self.ndf.objects) != 1 or self.ndf.classes[self.ndf.objects[0].cls] != CLASS:
            raise ValueError(f"not a {CLASS} file")
        self._values = {self.ndf.prop_name(pi): v for pi, v in self.ndf.objects[0].props}
        missing = [p for p in OFFSETS + ("SubtreeCount", "TriangleCount", "BoundingBoxMax", "Storage")
                   if p not in self._values]
        if missing:
            raise ValueError(f"missing properties {missing}")
        for flag in ("IsStreamPacked", "IsCompressed"):
            if flag in self._values and self._values[flag].scalar() != 1:
                raise ValueError("only stream-packed, compressed trees are supported")
        # a minimum of (0, 0, 0) is left out of the file (7 of the 32 shipped ground files)
        self.bounds_min = struct.unpack("<3f", self._values["BoundingBoxMin"].payload) \
            if "BoundingBoxMin" in self._values else (0.0, 0.0, 0.0)
        self.bounds_max = struct.unpack("<3f", self._values["BoundingBoxMax"].payload)
        self.triangle_count: int = self._values["TriangleCount"].scalar()
        storage = self._values["Storage"]
        if storage.tc != BLOB:
            raise ValueError("Storage is not a blob")
        ln = struct.unpack_from("<I", storage.payload)[0]
        if len(storage.payload) != 4 + ln:
            raise ValueError("Storage length does not match")
        self.subtrees: list[Subtree] = []
        self.main_node = b""
        self._parse(storage.payload[4:])

    @classmethod
    def from_file(cls, path: str) -> "Kdt":
        with open(path, "rb") as f:
            return cls(f.read())

    @classmethod
    def from_edat(cls, arc, which: str = "ground") -> "Kdt":
        """The "ground" or "camera" tree of an open map pack."""
        return cls(arc.read(arc.find(MEMBERS[which])))

    def _parse(self, blob: bytes) -> None:
        off = {name: self._values[name].scalar() for name in OFFSETS}
        count = self._values["SubtreeCount"].scalar()
        pos = 0
        parts: list[list] = []
        for _ in range(count):
            start = pos
            positions, pos = read_chunk(blob, pos)
            normals, pos = read_chunk(blob, pos)
            parts.append([start, positions, normals])
        pos = self._table(blob, pos, off["OffsetOfVertexBufferIndexes"], [p[0] for p in parts], "vertex")
        base = pos
        self._expect(pos, off["OffsetOfIndexBuffer"], "index buffers")
        starts = []
        for p in parts:
            starts.append(pos - base)
            icount = struct.unpack_from("<I", blob, pos)[0]
            indices, pos = read_chunk(blob, pos + 4)
            p += [icount, indices]
        pos = self._table(blob, pos, off["OffsetOfIndexBufferIndexes"], starts, "index buffer")
        base = pos
        self._expect(pos, off["OffsetOfTriangleIndexLists"], "triangle lists")
        starts = []
        for p in parts:
            starts.append(pos - base)
            trilist, pos = read_chunk(blob, pos)
            p.append(trilist)
        pos = self._table(blob, pos, off["OffsetOfTriangleIndexBufferIndexes"], starts, "triangle list")
        main = off["OffsetOfMainNode"]
        if main != (pos + 7) & ~7 or blob[pos:main].strip(b"\0"):
            raise ValueError("MainNode is not at the next 8-aligned offset after zero padding")
        csib = off["OffsetOfCompressedSubtreeIndexBuffer"]
        if csib < main:
            raise ValueError("subtree index table before MainNode")
        self.main_node = bytes(blob[main:csib])
        pos = csib + 4 * count
        self._expect(pos, off["OffsetOfCompressedSubtrees"], "subtrees")
        base = pos
        starts = []
        for p in parts:
            starts.append(pos - base)
            tree, pos = read_chunk(blob, pos)
            p.append(tree)
        if list(struct.unpack_from(f"<{count}I", blob, csib)) != starts:
            raise ValueError("subtree index table does not match the chunks")
        if pos != len(blob):
            raise ValueError(f"{len(blob) - pos} bytes after the last subtree")
        self.subtrees = [Subtree(*p[1:]) for p in parts]

    @staticmethod
    def _expect(pos: int, want: int, what: str) -> None:
        if pos != want:
            raise ValueError(f"{what} expected at {want:#x}, found at {pos:#x}")

    def _table(self, blob: bytes, pos: int, want: int, starts: list[int], what: str) -> int:
        """Check that the u32 table at `pos` (which the property says is at `want`) holds `starts`."""
        self._expect(pos, want, f"{what} table")
        if list(struct.unpack_from(f"<{len(starts)}I", blob, pos)) != starts:
            raise ValueError(f"{what} table does not match the chunks")
        return pos + 4 * len(starts)

    # -- writing --------------------------------------------------------------------------------------------

    def storage(self) -> tuple[bytes, dict[str, int]]:
        """Storage rebuilt from the parts, and the offsets of its regions (the OffsetOf* properties)."""
        out = bytearray()
        off: dict[str, int] = {}

        def table(name: str, starts: list[int]) -> None:
            off[name] = len(out)
            out.extend(struct.pack(f"<{len(starts)}I", *starts))

        starts = []
        for t in self.subtrees:
            starts.append(len(out))
            out += t.positions + t.normals
        table("OffsetOfVertexBufferIndexes", starts)
        off["OffsetOfIndexBuffer"] = base = len(out)
        starts = []
        for t in self.subtrees:
            starts.append(len(out) - base)
            out += struct.pack("<I", t.index_count) + t.indices
        table("OffsetOfIndexBufferIndexes", starts)
        off["OffsetOfTriangleIndexLists"] = base = len(out)
        starts = []
        for t in self.subtrees:
            starts.append(len(out) - base)
            out += t.trilist
        table("OffsetOfTriangleIndexBufferIndexes", starts)
        out += bytes(-len(out) % 8)
        off["OffsetOfMainNode"] = len(out)
        out += self.main_node
        out += bytes(-len(out) % 8)  # every shipped file has its subtree table 8-aligned
        starts, pos = [], 0
        for t in self.subtrees:
            starts.append(pos)
            pos += len(t.tree)
        table("OffsetOfCompressedSubtreeIndexBuffer", starts)
        off["OffsetOfCompressedSubtrees"] = len(out)
        for t in self.subtrees:
            out += t.tree
        return bytes(out), off

    def to_bytes(self) -> bytes:
        """The NDF member with Storage, the offsets and the counts rebuilt from the parts."""
        blob, off = self.storage()
        for name, value in off.items():
            self._values[name].set_scalar(value)
        self._values["SubtreeCount"].set_scalar(len(self.subtrees))
        self._values["TriangleCount"].set_scalar(self.triangle_count)
        if "BoundingBoxMin" in self._values:
            self._values["BoundingBoxMin"].payload = struct.pack("<3f", *self.bounds_min)
        elif any(self.bounds_min):
            raise ValueError("this file has no BoundingBoxMin property; only a zero minimum can be written")
        self._values["BoundingBoxMax"].payload = struct.pack("<3f", *self.bounds_max)
        self._values["Storage"].payload = struct.pack("<I", len(blob)) + blob
        return self.ndf.to_member(compress=bool(self.ndf.flags & 0x80))

    # -- vertices -------------------------------------------------------------------------------------------

    def positions(self, s: int) -> list[tuple[int, int, int]]:
        """Quantized (x, y, z) of every vertex of subtree `s` (0..32767 over the bounds, like the .tms)."""
        return decode_positions(inflate(self.subtrees[s].positions))[0]

    def parents(self, s: int) -> list[int]:
        return decode_positions(inflate(self.subtrees[s].positions))[1]

    def normals(self, s: int) -> list[tuple[float, float, float]]:
        return decode_normals(inflate(self.subtrees[s].normals))

    def set_positions(self, s: int, positions: list, parents: list[int] | None = None) -> None:
        """Replace subtree `s`'s positions (same vertex count; the subtree's own parents unless given)."""
        t = self.subtrees[s]
        if len(positions) != t.count:
            raise ValueError(f"subtree {s} has {t.count} vertices, got {len(positions)}")
        t.positions = compress(encode_positions(positions, self.parents(s) if parents is None else parents))

    def set_normals(self, s: int, normals: list) -> None:
        """Replace subtree `s`'s normals (same vertex count)."""
        t = self.subtrees[s]
        if len(normals) != t.count:
            raise ValueError(f"subtree {s} has {t.count} vertices, got {len(normals)}")
        t.normals = compress(encode_normals(normals))

    def to_world(self, axis: int, q: int) -> float:
        """Quantized value -> world units on axis 0 (x), 1 (y) or 2 (z)."""
        lo, hi = self.bounds_min[axis], self.bounds_max[axis]
        return lo + q * (hi - lo) / Q_MASK

    def to_quant(self, axis: int, v: float) -> int:
        lo, hi = self.bounds_min[axis], self.bounds_max[axis]
        return min(max(int(round((v - lo) * Q_MASK / (hi - lo))), 0), Q_MASK)
