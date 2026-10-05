"""The ground units walk on and the camera floor: read and written, lossless. Every part is read and encoded again
the way the notes of DomesticNukes and his Claude found; unchanged parts keep their bytes, so an unchanged file gives
the same bytes back."""
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
BLOB = 0x14            # the type the stored data has

# ---------------------------------------------------------------------------------------------------------------
# --- the stored parts, each packed on its own


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
# --- the points


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
# --- the normals


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
# --- the rest of each part, as the notes of DomesticNukes and his Claude found (2026-09-29)

def _nibbles(data: bytes) -> list[int]:
    out = []
    for b in data:
        out += (b & 0xF, b >> 4)          # low nibble first
    return out


def decode_indices(data: bytes, count: int) -> list[int]:
    """An index buffer chunk's content: `count` vertex numbers, 3 per triangle.

    4-bit codes, low nibble first, over a move-to-front history of the last 8 values (seeded 0..7):
    0-7 = the value at that place in the history (moved to the front); 8-14 = the last value + 0..6;
    15 = an escape: one byte B < 0x81 for a step of B - 0x40, else two bytes for ((B & 0x7F) << 8 | B2) - 0x4000.
    A byte after an escape starts at the nibble after the 15: at an odd nibble it reads high nibble first."""
    nib, k, last, hist, out = _nibbles(data), 0, 0, list(range(8)), []

    def byte() -> int:
        nonlocal k
        b = (nib[k] << 4) | nib[k + 1] if k & 1 else nib[k] | (nib[k + 1] << 4)
        k += 2
        return b

    for _ in range(count):
        c = nib[k]
        k += 1
        if c < 8:
            v = hist.pop(c)
            hist.insert(0, v)
        else:
            if c < 15:
                v = last + c - 8
            else:
                b = byte()
                v = last + (b - 0x40 if b < 0x81 else (((b & 0x7F) << 8) | byte()) - 0x4000)
            hist.insert(0, v)
            hist.pop()
        out.append(v)
        last = v
    if (k + 1) // 2 != len(data):
        raise ValueError(f"index buffer: {len(data)} bytes, {count} values used {(k + 1) // 2}")
    return out


def encode_indices(values: list[int]) -> bytes:
    """The index buffer chunk content for `values` (the shipped chunks come out byte for byte)."""
    nib, last, hist = [], 0, list(range(8))

    def byte(b: int) -> None:
        nib.extend((b >> 4, b & 0xF) if len(nib) & 1 else (b & 0xF, b >> 4))

    for v in values:
        if v in hist:
            c = hist.index(v)
            nib.append(c)
            hist.insert(0, hist.pop(c))
        else:
            d = v - last
            if 0 <= d <= 6:
                nib.append(8 + d)
            elif -64 <= d <= 63:
                nib.append(15)
                byte(d + 0x40)
            else:
                if not -0x4000 <= d < 0x4000:
                    raise ValueError(f"index step {d} is out of range")
                e = (d + 0x4000) & 0x7FFF
                nib.append(15)
                byte(0x80 | (e >> 8))
                byte(e & 0xFF)
            hist.insert(0, v)
            hist.pop()
        last = v
    if len(nib) & 1:
        nib.append(0)
    return bytes(nib[i] | (nib[i + 1] << 4) for i in range(0, len(nib), 2))


@dataclass
class Leaf:
    count: int          # triangles listed (an empty leaf lists one: triangle 0)
    variant: int = 0    # bits 5-6 of the leaf byte, meaning unknown; 0 for new leaves


@dataclass
class Split:
    axis: int           # 0 x, 1 y, 2 z
    value: int          # quantized, like the positions
    above: object       # first child: lo = value on the axis
    below: object       # second child: hi = value


@dataclass
class Clip:
    axis: int
    value: int
    keep_above: bool    # False: the child is below (hi = value); True: above (lo = value)
    child: object


def decode_tree(data: bytes):
    """A subtree's tree chunk content: its k-d tree, stored pre-order. A value is stored as its difference from
    the nearest ancestor's value on the same axis (0 at the root), 9 bits in the byte and the next, or 16 bits in
    the next two bytes big-endian."""
    pos = 0

    def node(anc: tuple):
        nonlocal pos
        b = data[pos]
        pos += 1
        if b & 0x80:
            n = b & 0x1F
            if n == 0x1F:
                n = data[pos]
                pos += 1
            return Leaf(n + 1, (b >> 5) & 3)
        axis = (b >> 3) & 3
        if axis == 3:
            raise ValueError("tree node on axis 3")
        if b & 4:
            mag = (data[pos] << 8) | data[pos + 1]
            pos += 2
        else:
            mag = ((b & 1) << 8) | data[pos]
            pos += 1
        v = anc[axis] + (-mag if b & 2 else mag)
        if not -0x8000 <= v < 0x8000:
            v = (v + 0x8000) % 0x10000 - 0x8000
        inner = anc[:axis] + (v,) + anc[axis + 1:]
        if b & 0x40:
            return Split(axis, v, node(inner), node(inner))
        return Clip(axis, v, bool(b & 0x20), node(inner))

    root = node((0, 0, 0))
    if pos != len(data):
        raise ValueError(f"tree: {len(data) - pos} bytes after the root's last node")
    return root


def encode_tree(root) -> bytes:
    out = bytearray()

    def node(n, anc: tuple) -> None:
        if isinstance(n, Leaf):
            if not 1 <= n.count <= 256:
                raise ValueError(f"a leaf lists 1 to 256 triangles, not {n.count}")
            if n.count - 1 < 0x1F:
                out.append(0x80 | (n.variant << 5) | (n.count - 1))
            else:
                out.extend((0x80 | (n.variant << 5) | 0x1F, n.count - 1))
            return
        d = n.value - anc[n.axis]
        mag = abs(d)
        if mag > 0xFFFF:
            raise ValueError(f"tree value step {d} is out of range")
        b = (0x40 if isinstance(n, Split) else (0x20 if n.keep_above else 0)) | (n.axis << 3) | (2 if d < 0 else 0)
        if mag <= 0x1FF:
            out.extend((b | (mag >> 8), mag & 0xFF))
        else:
            out.extend((b | 4, mag >> 8, mag & 0xFF))
        inner = anc[:n.axis] + (n.value,) + anc[n.axis + 1:]
        if isinstance(n, Split):
            node(n.above, inner)
            node(n.below, inner)
        else:
            node(n.child, inner)

    node(root, (0, 0, 0))
    return bytes(out)


def leaves(root) -> list:
    """The leaves in stored order, each with its cell: (leaf, lo, hi) with lo/hi per axis (None = unbounded)."""
    out, stack = [], [(root, (None,) * 3, (None,) * 3)]
    while stack:
        n, lo, hi = stack.pop()
        if isinstance(n, Leaf):
            out.append((n, lo, hi))
        elif isinstance(n, Split):
            a = n.axis
            stack.append((n.below, lo, hi[:a] + (n.value,) + hi[a + 1:]))   # pushed first: visited second
            stack.append((n.above, lo[:a] + (n.value,) + lo[a + 1:], hi))
        else:
            a = n.axis
            if n.keep_above:
                stack.append((n.child, lo[:a] + (n.value,) + lo[a + 1:], hi))
            else:
                stack.append((n.child, lo, hi[:a] + (n.value,) + hi[a + 1:]))
    return out


def decode_trilists(data: bytes, counts: list[int]) -> list[list[int]]:
    """A triangle list chunk's content: one list of triangle numbers per leaf, in leaf order. Each list starts from
    0; a byte < 0x80 adds byte - 0x40, a byte >= 0x80 starts a 4-byte big-endian absolute value (top bit dropped)."""
    pos, out = 0, []
    for n in counts:
        prev, lst = 0, []
        for _ in range(n):
            b = data[pos]
            if b < 0x80:
                prev += b - 0x40
                pos += 1
            else:
                prev = ((b & 0x7F) << 24) | (data[pos + 1] << 16) | (data[pos + 2] << 8) | data[pos + 3]
                pos += 4
            lst.append(prev)
        out.append(lst)
    if pos != len(data):
        raise ValueError(f"triangle lists: {len(data) - pos} bytes after the last list")
    return out


def encode_trilists(lists: list[list[int]]) -> bytes:
    out = bytearray()
    for lst in lists:
        prev = 0
        for v in lst:
            d = v - prev
            if -64 <= d <= 63:
                out.append(d + 0x40)
            else:
                if not 0 <= v < 1 << 31:
                    raise ValueError(f"triangle number {v} is out of range")
                out += bytes((0x80 | (v >> 24), (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF))
            prev = v
    return bytes(out)


MAIN_SPLIT, MAIN_LEAF = 4, 5


def decode_main_node(data: bytes) -> list[tuple[int, int, int, float]]:
    """The MainNode's 8-byte entries as (type, axis, rest, value): type = tag >> 28, axis = tag & 3,
    rest = (tag & 0x0FFFFFFF) >> 2, value in world units. Types: 4 split (above = the next entry, below = entry
    i + rest / 2); 0 / 2 clip keeping below / above, child = the next entry; 1 / 3 the same clips, child =
    subtree `rest`; 5 leaf = subtree `rest`."""
    if len(data) % 8:
        raise ValueError("MainNode is not a whole number of 8-byte entries")
    out = []
    for o in range(0, len(data), 8):
        tag, value = struct.unpack_from("<If", data, o)
        out.append((tag >> 28, tag & 3, (tag & 0x0FFFFFFF) >> 2, value))
    return out


def encode_main_node(entries: list[tuple[int, int, int, float]]) -> bytes:
    return b"".join(struct.pack("<If", (t << 28) | (rest << 2) | axis, value) for t, axis, rest, value in entries)


def main_regions(entries: list) -> dict[int, tuple[tuple, tuple, list[int]]]:
    """Each subtree's region from the MainNode walk: subtree -> (lo, hi, the clip entries on its path) with lo/hi
    per axis in world units (None = unbounded). Raises if a subtree is reached twice."""
    out: dict[int, tuple] = {}
    stack = [(0, (None,) * 3, (None,) * 3, ())]
    while stack:
        i, lo, hi, path = stack.pop()
        t, a, rest, v = entries[i]
        cut_lo = lo[:a] + (v,) + lo[a + 1:]
        cut_hi = hi[:a] + (v,) + hi[a + 1:]
        if t == MAIN_SPLIT:
            if rest & 1:
                raise ValueError(f"MainNode entry {i}: odd split offset")
            stack.append((i + rest // 2, lo, cut_hi, path))
            stack.append((i + 1, cut_lo, hi, path))
            continue
        if t == MAIN_LEAF:
            sub, box = rest, (lo, hi)
        elif t in (0, 2):
            stack.append((i + 1, lo if t == 0 else cut_lo, cut_hi if t == 0 else hi, path + (i,)))
            continue
        elif t in (1, 3):
            sub, box = rest, ((lo, cut_hi) if t == 1 else (cut_lo, hi))
            path = path + (i,)
        else:
            raise ValueError(f"MainNode entry {i}: unknown type {t}")
        if sub in out:
            raise ValueError(f"MainNode reaches subtree {sub} twice")
        out[sub] = (box[0], box[1], list(path))
    return out


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
            # not a game rule: a damaged or unexpected file
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
            # not a game rule: a damaged or unexpected file
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
            # not a game rule: a damaged or unexpected file
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
        out += self.main_node  # copied as is; every shipped MainNode is a multiple of 8 bytes, so the table stays aligned
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

    # -- triangles and trees ---------------------------------------------------------------------------------

    def indices(self, s: int) -> list[int]:
        """Subtree `s`'s triangles as vertex numbers, 3 per triangle."""
        t = self.subtrees[s]
        return decode_indices(inflate(t.indices), t.index_count)

    def tree(self, s: int):
        """Subtree `s`'s k-d tree (Leaf, Split and Clip nodes; values quantized like the positions)."""
        return decode_tree(inflate(self.subtrees[s].tree))

    def trilists(self, s: int, root=None) -> list[list[int]]:
        """The triangle numbers each leaf of subtree `s`'s tree lists, in leaf order."""
        root = self.tree(s) if root is None else root
        return decode_trilists(inflate(self.subtrees[s].trilist), [leaf.count for leaf, _, _ in leaves(root)])

    def set_indices(self, s: int, values: list[int]) -> None:
        """Replace subtree `s`'s triangles (vertex numbers, 3 per triangle, each below its vertex count)."""
        if len(values) % 3:
            raise ValueError("triangles need 3 vertex numbers each")
        n = self.subtrees[s].count
        if any(not 0 <= v < n for v in values):
            raise ValueError(f"a vertex number is outside subtree {s}'s {n} vertices")
        t = self.subtrees[s]
        t.index_count, t.indices = len(values), compress(encode_indices(values))

    def set_tree(self, s: int, root, lists: list[list[int]]) -> None:
        """Replace subtree `s`'s k-d tree and its leaves' triangle lists (one list per leaf, in leaf order)."""
        found = leaves(root)
        if len(found) != len(lists) or any(leaf.count != len(lst) for (leaf, _, _), lst in zip(found, lists)):
            raise ValueError("one triangle list per leaf, as long as the leaf's count")
        t = self.subtrees[s]
        t.tree, t.trilist = compress(encode_tree(root)), compress(encode_trilists(lists))

    def main_entries(self) -> list[tuple[int, int, int, float]]:
        return decode_main_node(self.main_node)

    def set_main_entries(self, entries: list[tuple[int, int, int, float]]) -> None:
        self.main_node = encode_main_node(entries)

    def to_world(self, axis: int, q: int) -> float:
        """Quantized value -> world units on axis 0 (x), 1 (y) or 2 (z)."""
        lo, hi = self.bounds_min[axis], self.bounds_max[axis]
        return lo + q * (hi - lo) / Q_MASK

    def to_quant(self, axis: int, v: float) -> int:
        lo, hi = self.bounds_min[axis], self.bounds_max[axis]
        return min(max(int(round((v - lo) * Q_MASK / (hi - lo))), 0), Q_MASK)
