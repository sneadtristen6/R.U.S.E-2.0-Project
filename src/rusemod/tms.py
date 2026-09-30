"""Terrain mesh (.tms, magic TMSG): read, edit heights, write.

Every map pack holds two of these, output\\highdef.tms and output\\lowdef.tms (a coarser mesh with half the
cells per side). The map is cut into a grid of cells. Each cell is one irregular triangle mesh with its own
compressed vertex buffer, a triangle list for the whole ground (list 0), an optional second list that repeats
the triangles covered by water (list 1), and a table of 8 x 8 culling patches with height bounds. A "skirt" mesh
(a curtain hanging from the map edge) follows the cells. Layout in docs/FORMATS.md.

Every vertex holds a quantized position (x, y, z, water) as four u16 and a normal as four u8. All three axes use
the file's bounding box: world = min + q * (max - min) / 32767. `water` is the water-surface height on the same
scale as z; most vertices carry the map's base water level, and list 1 holds the triangles whose ground lies
below it. Normal bytes are round((n + 1) * 127.5) with the 4th byte always 128; the shipped normals follow the
mesh closely but not exactly (they were baked from finer data), so edits recompute them as area-weighted face
normals only around the vertices that moved.

Cells that were not edited keep their original bytes, so an unchanged file re-serializes byte-for-byte. An
edited cell gets its position and normal streams re-encoded with our own LZ encoder (same stream format the game
ships; the predictor and triangle lists stay as they were) and the bounds of the patches it touched recomputed.
"""
from __future__ import annotations

import math
import struct
import zlib
from dataclasses import dataclass, field
from typing import Callable

MAGIC = b"TMSG"
HEADER_SIZE = 0x368
CELL_SIZE = 48
Q_MAX = 32767         # quantized span of every axis
VERTEX_TYPE = "$/M3D/System/VERTEXTYPE/TVertex__PositionIn4w_4w__NormalIn01_4ubn"
POSITION, NORMAL = 8, 4   # vertex element kinds: 4 x u16 and 4 x u8

# ---------------------------------------------------------------------------------------------------------------
# LZ stream codec (the payload of every vertex-buffer stream).
#
# 20-byte header: u8 version=1, u8 header_len=0x14, u8 method (8 = byte units, 16 = u16 units), u8 shift-2,
# u32 unit_count, u32 literal_count, u32 token_count, u16 literal_base, u16 token_base (both << shift).
# Then u32 control words (read LSB first; 0 = copy one literal unit, 1 = one back-reference token, then a single
# 1 bit that ends the stream), the literal units, and the tokens. Lengths and distances count units.

_LZ_HDR = struct.Struct("<BBBBIIIHH")
_MAX_DIST = 8192
_MAX_LEN = 259


def lz_decode(src: bytes, pos: int = 0) -> bytes:
    """Decode the LZ stream starting at `pos`. The method byte is the literal width in bits: 8 and 16 in the
    terrain; mesh packs (rusemod.spk) also pack 5- and 11-bit literals, and store small blocks unpacked (bit 7 set:
    the units follow the first 8 bytes). Output units are 1 byte up to 8 bits, else 2."""
    ver, _hlen, method, _sb, count = struct.unpack_from("<BBBBI", src, pos)
    width = method & 0x7F
    unit = 2 if width > 8 else 1
    if ver == 1 and method & 0x80:  # a stored block can be shorter than a packed one's header
        return bytes(src[pos + 8:pos + 8 + count * unit])
    ver, hlen, method, sb, count, nlit, ntok, lbase, tbase = _LZ_HDR.unpack_from(src, pos)
    if ver != 1 or hlen != 0x14 or not 1 <= width <= 16:
        raise ValueError(f"unsupported LZ stream header {ver}/{hlen:#x}/{method:#x}")
    need = count * unit
    shift = sb + 2
    cp = pos + hlen
    lp = pos + (lbase << shift)
    tp = pos + (tbase << shift)
    lits = src
    if width not in (8, 16):  # literals packed `width` bits each, least significant bit first
        bits = int.from_bytes(src[lp:lp + (nlit * width + 7) // 8], "little")
        mask = (1 << width) - 1
        vals = [(bits >> (i * width)) & mask for i in range(nlit)]
        lits = bytes(vals) if unit == 1 else struct.pack(f"<{nlit}H", *vals)
        lp = 0
    out = bytearray()
    while len(out) < need:
        word = struct.unpack_from("<I", src, cp)[0]
        cp += 4
        left = 32
        while left and len(out) < need:
            if not word & 1:  # a run of literal units
                run = ((word & -word).bit_length() - 1) if word else left
                run = min(run, left, (need - len(out)) // unit)
                out += lits[lp:lp + run * unit]
                lp += run * unit
                word >>= run
                left -= run
                continue
            word >>= 1
            left -= 1
            t = src[tp]
            if t & 3 == 3:
                if t & 4:
                    v = t | src[tp + 1] << 8 | src[tp + 2] << 16
                    tp += 3
                    ln, dist = ((v >> 3) & 0xFF) + 4, ((v >> 11) & 0x1FFF) + 1
                else:
                    v = t | src[tp + 1] << 8
                    tp += 2
                    ln, dist = ((v >> 3) & 0xF) + 4, ((v >> 7) & 0x1FF) + 1
            elif t & 4:
                tp += 1
                ln, dist = (t & 3) + 1, ((t >> 3) & 0x1F) + 1
            else:
                v = t | src[tp + 1] << 8
                tp += 2
                ln, dist = (t & 3) + 1, ((v >> 3) & 0x1FFF) + 1
            n, back = ln * unit, dist * unit
            if back > len(out):
                raise ValueError("LZ back-reference before the start of the output")
            start = len(out) - back
            if back >= n:
                out += out[start:start + n]
            else:  # overlapping copy: repeats the last `back` bytes
                out += (out[start:] * (n // back + 1))[:n]
    del out[need:]
    return bytes(out)


def _token(ln: int, dist: int) -> bytes:
    d = dist - 1
    if ln <= 3:
        if dist <= 32:
            return bytes([(ln - 1) | 4 | d << 3])
        return struct.pack("<H", (ln - 1) | d << 3)
    if ln <= 19 and dist <= 512:
        return struct.pack("<H", 3 | (ln - 4) << 3 | d << 7)
    v = 7 | (ln - 4) << 3 | d << 11
    return bytes((v & 0xFF, v >> 8 & 0xFF, v >> 16))


def _token_len(ln: int, dist: int) -> int:
    if ln <= 3:
        return 1 if dist <= 32 else 2
    return 2 if (ln <= 19 and dist <= 512) else 3


def lz_encode(data: bytes, unit: int = 1, chain: int = 16) -> bytes:
    """Encode `data` (bytes, or u16 units when unit=2) as one LZ stream, greedy hash-chain matching.

    The result decodes with `lz_decode` (and with the game's decoder: same header, control-word, literal and
    token layout, end bit and padding as the shipped streams), but it is not the byte sequence the game's own
    encoder produced: that one makes different match choices.
    """
    if unit not in (1, 2) or len(data) % unit:
        raise ValueError("unit must be 1 or 2 and divide the data length")
    n = len(data) // unit
    syms = memoryview(data).cast("H").tolist() if unit == 2 else data
    key_len = 2 if unit == 2 else 3
    heads: dict[bytes, list[int]] = {}
    bits: list[int] = []
    lits = bytearray()
    toks = bytearray()
    i = 0
    while i < n:
        best_len = best_dist = 0
        if i + key_len <= n:
            cands = heads.get(data[i * unit:(i + key_len) * unit])
            if cands:
                limit = min(n - i, _MAX_LEN)
                for j in reversed(cands):
                    dist = i - j
                    if dist > _MAX_DIST:
                        break
                    ln = key_len
                    while ln < limit and syms[j + ln] == syms[i + ln]:
                        ln += 1
                    if ln > best_len:
                        best_len, best_dist = ln, dist
                        if ln == limit:
                            break
        if best_len and _token_len(best_len, best_dist) < best_len * unit:
            bits.append(1)
            toks += _token(best_len, best_dist)
            step = best_len
        else:
            bits.append(0)
            lits += data[i * unit:(i + 1) * unit]
            step = 1
        for k in range(i, min(i + step, n - key_len + 1)):
            lst = heads.setdefault(data[k * unit:(k + key_len) * unit], [])
            lst.append(k)
            if len(lst) > chain:
                del lst[0]
        i += step
    ntok = bits.count(1)
    bits.append(1)  # end bit, as in the shipped streams
    words = bytearray()
    for w in range(0, len(bits), 32):
        v = 0
        for b, bit in enumerate(bits[w:w + 32]):
            v |= bit << b
        words += struct.pack("<I", v)
    shift = 2
    while True:
        al = 1 << shift
        lbase = (0x14 + len(words) + al - 1) & -al
        tbase = (lbase + len(lits) + al - 1) & -al
        if tbase >> shift <= 0xFFFF:
            break
        shift += 1
    body = bytearray(_LZ_HDR.pack(1, 0x14, 16 if unit == 2 else 8, shift - 2, n, len(lits) // unit, ntok,
                                  lbase >> shift, tbase >> shift))
    body += words
    body += bytes(lbase - len(body))
    body += lits
    body += bytes(tbase - len(body))
    body += toks
    body += bytes(((len(body) + 3) & ~3) + 4 - len(body))  # 4 to 7 zero bytes, as shipped
    return bytes(body)


# ---------------------------------------------------------------------------------------------------------------
# Predictor: the parent of each vertex, whose value an element with mode 2 is stored relative to.
# Vertices 0 and 1 have parent 0. From vertex 2 on: one 0 byte means "the previous vertex", otherwise two bytes
# 0x80|hi, lo give how many vertices back the parent is.

def decode_parents(raw: bytes, count: int) -> list[int]:
    par = [0] * count
    q = 0
    for i in range(2, count):
        b0 = raw[q]
        if b0:
            par[i] = i - ((b0 & 0x7F) << 8 | raw[q + 1])
            q += 2
        else:
            par[i] = i - 1
            q += 1
    if q != len(raw):
        raise ValueError("predictor stream length does not match the vertex count")
    return par


def encode_parents(parents: list[int]) -> bytes:
    out = bytearray()
    for i in range(2, len(parents)):
        back = i - parents[i]
        if back == 1:
            out.append(0)
        elif 1 < back <= 0x7FFF:
            out += bytes((0x80 | back >> 8, back & 0xFF))
        else:
            raise ValueError(f"vertex {i}: parent {parents[i]} out of range")
    return bytes(out)


# ---------------------------------------------------------------------------------------------------------------
# Vertex buffer ("VBUF"): 12-byte header, the predictor stream, then one "SUBP" stream per vertex element.
# VBUF header: magic, u16 8 (bytes that follow), u8 0xA1 (unknown), u16 stride 12, u16 element count 2, u8 flags
# (2 = a predictor stream follows as u32 length + LZ stream). SUBP header: magic, u16 12 (bytes that follow),
# u8 kind, u8 3 (unknown), u8 mode 2, u16 bytes per vertex, u16 offset in the vertex, 3 zero bytes; then u32
# length + LZ stream.

_VBUF_HEAD = b"VBUF" + struct.pack("<HBHHB", 8, 0xA1, 12, 2, 2)   # identical in all 1390 shipped cells
_SUBP_HEAD = {POSITION: b"SUBP" + struct.pack("<HBBBHH3x", 12, POSITION, 3, 2, 8, 0),
              NORMAL: b"SUBP" + struct.pack("<HBBBHH3x", 12, NORMAL, 3, 2, 4, 8)}


@dataclass
class Element:
    head: bytes          # the SUBP header, kept verbatim
    kind: int            # POSITION (4 x u16) or NORMAL (4 x u8)
    mode: int            # 2 = stored relative to the predictor parent
    size: int            # bytes per vertex
    offset: int          # byte offset inside the vertex
    stream: bytes        # the encoded LZ stream, with its trailing padding


@dataclass
class VertexBuffer:
    head: bytes                  # 12-byte VBUF header
    stride: int
    count: int
    pred_stream: bytes | None    # encoded predictor stream (None: every parent is the previous vertex)
    elements: list[Element]

    @classmethod
    def parse(cls, raw: bytes, count: int) -> "VertexBuffer":
        if raw[:4] != b"VBUF":
            raise ValueError(f"not a vertex buffer: {raw[:4]!r}")
        hlen = struct.unpack_from("<H", raw, 4)[0]
        stride, nelem, flags = struct.unpack_from("<HHB", raw, 7)
        p = 4 + hlen
        pred = None
        if flags & 2:
            ln = struct.unpack_from("<I", raw, p)[0]
            pred = raw[p + 4:p + 4 + ln]
            p += 4 + ln
        elements = []
        for _ in range(nelem):
            if raw[p:p + 4] != b"SUBP":
                raise ValueError(f"expected SUBP at {p:#x}")
            eh = struct.unpack_from("<H", raw, p + 4)[0]
            kind, _codec, mode, size, offset = struct.unpack_from("<BBBHH", raw, p + 6)
            head = raw[p:p + 4 + eh]
            p += 4 + eh
            ln = struct.unpack_from("<I", raw, p)[0]
            elements.append(Element(head, kind, mode, size, offset, raw[p + 4:p + 4 + ln]))
            p += 4 + ln
        if p != len(raw):
            raise ValueError(f"vertex buffer has {len(raw) - p} trailing bytes")
        return cls(raw[:4 + hlen], stride, count, pred, elements)

    @classmethod
    def build(cls, positions: list, normals: list, parents: list[int]) -> "VertexBuffer":
        """A new buffer in the shipped layout (header bytes, element order, delta mode) from decoded values."""
        vb = cls(_VBUF_HEAD, 12, len(positions), lz_encode(encode_parents(parents)),
                 [Element(_SUBP_HEAD[POSITION], POSITION, 2, 8, 0, b""), Element(_SUBP_HEAD[NORMAL], NORMAL, 2, 4, 8, b"")])
        vb.encode(POSITION, positions, parents)
        vb.encode(NORMAL, normals, parents)
        return vb

    def to_bytes(self) -> bytes:
        out = bytearray(self.head)
        if self.pred_stream is not None:
            out += struct.pack("<I", len(self.pred_stream)) + self.pred_stream
        for e in self.elements:
            out += e.head + struct.pack("<I", len(e.stream)) + e.stream
        return bytes(out)

    def parents(self) -> list[int]:
        if self.pred_stream is None:
            return [max(i - 1, 0) for i in range(self.count)]
        return decode_parents(lz_decode(self.pred_stream), self.count)

    def element(self, kind: int) -> Element:
        for e in self.elements:
            if e.kind == kind:
                return e
        raise KeyError(kind)

    def decode(self, kind: int, parents: list[int] | None = None) -> list[tuple[int, int, int, int]]:
        """Per-vertex 4-tuples of one element. A POSITION stream starts with u16 mask = 0xFFFF and u16 0 (the
        only values shipped; other masks are refused), then 4 x u16 per vertex; a NORMAL stream is 4 x u8."""
        e = self.element(kind)
        s = lz_decode(e.stream)
        n = self.count
        if kind == POSITION:
            mask, extra = struct.unpack_from("<HH", s, 0)
            if (mask, extra) != (0xFFFF, 0):
                raise ValueError(f"unsupported position stream prefix {mask:#x}/{extra:#x}")
            vals = struct.unpack_from(f"<{4 * n}H", s, 4)
        elif kind == NORMAL:
            mask, vals = 0xFF, s
        else:
            raise ValueError(f"unsupported vertex element kind {kind}")
        if len(vals) != 4 * n:
            raise ValueError("element stream length does not match the vertex count")
        if e.mode != 2:
            acc = list(vals)
        else:
            par = self.parents() if parents is None else parents
            acc = [0] * (4 * n)
            for i in range(n):
                b, pb = 4 * i, 4 * par[i]
                acc[b] = (vals[b] + acc[pb]) & mask
                acc[b + 1] = (vals[b + 1] + acc[pb + 1]) & mask
                acc[b + 2] = (vals[b + 2] + acc[pb + 2]) & mask
                acc[b + 3] = (vals[b + 3] + acc[pb + 3]) & mask
        return [tuple(acc[4 * i:4 * i + 4]) for i in range(n)]

    def encode(self, kind: int, values: list, parents: list[int] | None = None) -> None:
        """Replace one element's stream with `values` (per-vertex 4-tuples)."""
        e = self.element(kind)
        n = self.count
        if len(values) != n:
            raise ValueError(f"expected {n} vertices, got {len(values)}")
        mask = 0xFFFF if kind == POSITION else 0xFF
        flat = [c for v in values for c in v]
        if len(flat) != 4 * n or min(flat, default=0) < 0 or max(flat, default=0) > mask:
            raise ValueError("vertex values out of range")
        if e.mode == 2:
            par = self.parents() if parents is None else parents
            enc = list(flat)
            for i in range(1, n):
                b, pb = 4 * i, 4 * par[i]
                for c in range(4):
                    enc[b + c] = (flat[b + c] - flat[pb + c]) & mask
        else:
            enc = flat
        if kind == POSITION:
            e.stream = lz_encode(struct.pack(f"<HH{4 * n}H", mask, 0, *enc), 2)
        else:
            e.stream = lz_encode(bytes(enc), 1)


# ---------------------------------------------------------------------------------------------------------------
# Triangle lists: u32 byte count, then a zlib stream ended by a sync flush (no final block, no checksum). The
# u16 values are running differences: index k = (value 0 + ... + value k) mod 65536.

def decode_indices(raw: bytes) -> list[int]:
    size = struct.unpack_from("<I", raw, 0)[0]
    data = zlib.decompressobj().decompress(raw[4:])
    if len(data) != size:
        raise ValueError(f"triangle list inflated to {len(data)} bytes, expected {size}")
    out = []
    acc = 0
    for d in memoryview(data).cast("H"):
        acc = (acc + d) & 0xFFFF
        out.append(acc)
    return out


def encode_indices(indices: list[int]) -> bytes:
    diffs = [(v - (indices[k - 1] if k else 0)) & 0xFFFF for k, v in enumerate(indices)]
    data = struct.pack(f"<{len(diffs)}H", *diffs)
    co = zlib.compressobj(9)
    return struct.pack("<I", len(data)) + co.compress(data) + co.flush(zlib.Z_SYNC_FLUSH)


# ---------------------------------------------------------------------------------------------------------------
# Cells and their patch tables.

@dataclass
class Patch:
    """One of a cell's 8 x 8 culling patches: a run of vertices, runs of both triangle lists, height bounds."""
    vstart: int
    vcount: int
    i0start: int
    i0count: int
    i1start: int
    i1count: int
    zlo: float     # min z of its vertices; exactly 0.0 when the cell has no list 1
    zhi: float     # max over its vertices of max(z, water)


@dataclass
class Cell:
    flags: int           # bit 0: list 0 present, bit 1: list 1 (water) present, bit 2: 32-bit patch table
    vcount: int
    vb: bytes            # encoded vertex buffer
    ib: list[bytes]      # encoded triangle lists present, in order
    icount: list[int]    # index count of each present list
    patches: bytes       # raw patch table (64 records of 20 bytes, or of 32 bytes when flags bit 2 is set)
    _cache: dict = field(default_factory=dict, repr=False)

    def vbuf(self) -> VertexBuffer:
        if "vb" not in self._cache:
            self._cache["vb"] = VertexBuffer.parse(self.vb, self.vcount)
        return self._cache["vb"]

    def parents(self) -> list[int]:
        if "par" not in self._cache:
            self._cache["par"] = self.vbuf().parents()
        return self._cache["par"]

    def positions(self) -> list[tuple[int, int, int, int]]:
        """Quantized (x, y, z, water) per vertex."""
        if "pos" not in self._cache:
            self._cache["pos"] = self.vbuf().decode(POSITION, self.parents())
        return self._cache["pos"]

    def normals(self) -> list[tuple[int, int, int, int]]:
        """(nx, ny, nz, 128) per vertex; component = round((n + 1) * 127.5)."""
        if "nor" not in self._cache:
            self._cache["nor"] = self.vbuf().decode(NORMAL, self.parents())
        return self._cache["nor"]

    def triangles(self, which: int = 0) -> list[int]:
        """Vertex indices (3 per triangle) of list 0 (all ground) or list 1 (the part under water)."""
        if not self.flags & (1 << which):
            return []
        return decode_indices(self.ib[bin(self.flags & ((1 << which) - 1)).count("1")])

    def patch_list(self) -> list[Patch]:
        fmt = "<6I2f" if self.flags & 4 else "<6H2f"
        size = struct.calcsize(fmt)
        return [Patch(*struct.unpack_from(fmt, self.patches, o)) for o in range(0, len(self.patches), size)]

    def set_patches(self, patches: list[Patch]) -> None:
        fmt = "<6I2f" if self.flags & 4 else "<6H2f"
        self.patches = b"".join(struct.pack(fmt, p.vstart, p.vcount, p.i0start, p.i0count, p.i1start,
                                            p.i1count, p.zlo, p.zhi) for p in patches)

    def set_vertices(self, positions: list, normals: list) -> None:
        """Re-encode the position and normal streams (same predictor and triangle lists)."""
        vb = self.vbuf()
        par = self.parents()
        vb.encode(POSITION, positions, par)
        vb.encode(NORMAL, normals, par)
        self.vb = vb.to_bytes()
        self._cache.update(pos=[tuple(p) for p in positions], nor=[tuple(n) for n in normals])


def _align4(n: int) -> int:
    return (n + 3) & ~3


def _f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


# ---------------------------------------------------------------------------------------------------------------
# The file.

class Tms:
    """A parsed .tms file. `cells` is row-major (index = y * grid_w + x)."""

    def __init__(self, raw: bytes):
        if raw[:4] != MAGIC or raw[-4:] != MAGIC:
            raise ValueError(f"not a TMSG terrain mesh: {raw[:4]!r}")
        version, platform, size = struct.unpack_from("<I4sI", raw, 4)
        if version != 3 or platform != b"PC\0\0" or size != len(raw):
            raise ValueError(f"unsupported TMSG header (version {version}, platform {platform!r}, size {size})")
        self.head = bytes(raw[:HEADER_SIZE])
        self.grid_w, self.grid_h, self.patch_div = struct.unpack_from("<III", raw, 0x10)
        self.cell_w, self.cell_h = struct.unpack_from("<ff", raw, 0x1C)
        cell_off, cell_len, patch_off, patch_len, geo_off, geo_len = struct.unpack_from("<6I", raw, 0x24)
        self.vertex_type = raw[0x3C:0x23C].split(b"\0")[0].decode("latin-1")
        self.bounds = list(struct.unpack_from("<6f", raw, 0x23C))   # min x, y, z, max x, y, z (world units)
        skirt_off, skirt_len, sdata_off, sdata_len = struct.unpack_from("<4I", raw, 0x254)
        if cell_off != HEADER_SIZE or cell_len != CELL_SIZE * self.grid_w * self.grid_h:
            raise ValueError("unexpected cell table placement")
        if (patch_off, geo_off, skirt_off, sdata_off) != (cell_off + cell_len, patch_off + patch_len,
                                                          geo_off + geo_len, skirt_off + skirt_len):
            raise ValueError("sections are not contiguous")
        if sdata_off + sdata_len + 4 != len(raw):
            raise ValueError("unexpected data after the skirt")
        self.skirt = bytes(raw[skirt_off:skirt_off + skirt_len])         # skirt descriptor, kept verbatim
        self.skirt_data = bytes(raw[sdata_off:sdata_off + sdata_len])    # skirt meshes, kept verbatim
        geo = raw[geo_off:geo_off + geo_len]
        self.cells: list[Cell] = []
        pos = ppos = 0
        for k in range(self.grid_w * self.grid_h):
            f = struct.unpack_from("<12I", raw, cell_off + CELL_SIZE * k)
            flags, vb_off, vb_len, vcount = f[:4]
            if vb_off != pos or f[10] != ppos:
                raise ValueError(f"cell {k}: unexpected placement")
            vb = bytes(geo[vb_off:vb_off + vb_len])
            pos = _align4(vb_off + vb_len)
            ib, icount = [], []
            for bit, (o, ln, cnt) in enumerate((f[4:7], f[7:10])):
                if not flags & (1 << bit):
                    if (o, ln, cnt) != (0, 0, 0):
                        raise ValueError(f"cell {k}: absent triangle list has data")
                    continue
                if o != pos:
                    raise ValueError(f"cell {k}: unexpected triangle list placement")
                ib.append(bytes(geo[o:o + ln]))
                icount.append(cnt)
                pos = _align4(o + ln)
            self.cells.append(Cell(flags, vcount, vb, ib, icount, bytes(raw[patch_off + ppos:patch_off + ppos + f[11]])))
            ppos += f[11]
        if pos != geo_len or ppos != patch_len:
            raise ValueError("cell data does not fill its sections")

    @classmethod
    def from_file(cls, path: str) -> "Tms":
        with open(path, "rb") as f:
            return cls(f.read())

    def to_bytes(self) -> bytes:
        """Serialize: header, cell table, patch tables, geometry (per cell: vertex buffer then its triangle
        lists, each 4-byte aligned with zero padding), skirt descriptor, skirt meshes, closing magic."""
        table = bytearray()
        geo = bytearray()
        patches = bytearray()
        for c in self.cells:
            vb_off = len(geo)
            geo += c.vb + bytes(_align4(len(c.vb)) - len(c.vb))
            parts = []
            lists = iter(zip(c.ib, c.icount))
            for bit in range(2):
                if c.flags & (1 << bit):
                    blob, cnt = next(lists)
                    parts += (len(geo), len(blob), cnt)
                    geo += blob + bytes(_align4(len(blob)) - len(blob))
                else:
                    parts += (0, 0, 0)
            table += struct.pack("<12I", c.flags, vb_off, len(c.vb), c.vcount, *parts, len(patches), len(c.patches))
            patches += c.patches
        head = bytearray(self.head)
        patch_off = HEADER_SIZE + len(table)
        geo_off = patch_off + len(patches)
        skirt_off = geo_off + len(geo)
        sdata_off = skirt_off + len(self.skirt)
        struct.pack_into("<I", head, 0x0C, sdata_off + len(self.skirt_data) + 4)
        struct.pack_into("<III", head, 0x10, self.grid_w, self.grid_h, self.patch_div)
        struct.pack_into("<ff", head, 0x1C, self.cell_w, self.cell_h)
        struct.pack_into("<6I", head, 0x24, HEADER_SIZE, len(table), patch_off, len(patches), geo_off, len(geo))
        struct.pack_into("<6f", head, 0x23C, *self.bounds)
        struct.pack_into("<4I", head, 0x254, skirt_off, len(self.skirt), sdata_off, len(self.skirt_data))
        return bytes(head + table + patches + geo + self.skirt + self.skirt_data + MAGIC)

    # -- coordinates ------------------------------------------------------------------------------------------

    def to_world(self, axis: int, q: int) -> float:
        """Quantized value -> world units on axis 0 (x), 1 (y) or 2 (z; also the water height)."""
        lo, hi = self.bounds[axis], self.bounds[axis + 3]
        return lo + q * (hi - lo) / Q_MAX

    def to_quant(self, axis: int, v: float) -> int:
        lo, hi = self.bounds[axis], self.bounds[axis + 3]
        return min(max(round((v - lo) * Q_MAX / (hi - lo)), 0), Q_MAX) if hi > lo else 0

    def _z_f32(self, q: int) -> float:
        """World height as the game stores it in patch bounds (float32 steps; matches 80% exactly, else 1 ulp)."""
        z0, z1 = self.bounds[2], self.bounds[5]
        return _f32(z0 + _f32(_f32(q * _f32(1 / Q_MAX)) * _f32(z1 - z0)))

    def world_vertices(self, k: int) -> list[tuple[float, float, float]]:
        """World (x, y, z) of every vertex of cell `k`."""
        return [(self.to_world(0, p[0]), self.to_world(1, p[1]), self.to_world(2, p[2]))
                for p in self.cells[k].positions()]

    def height_grid(self, width: int = 256) -> list[list[float | None]]:
        """Ground heights (world z) sampled on a width x height grid over the map by rasterizing triangle list 0.
        Row 0 is y = min (the top row of the map's terrain.png); height follows the map's aspect ratio."""
        span_x = self.bounds[3] - self.bounds[0]
        span_y = self.bounds[4] - self.bounds[1]
        height = max(1, round(width * span_y / span_x))
        grid: list[list[float | None]] = [[None] * width for _ in range(height)]
        sx, sy = width / Q_MAX, height / Q_MAX
        for c in self.cells:
            pos = c.positions()
            tri = c.triangles(0)
            zs = [self.to_world(2, p[2]) for p in pos]
            for t in range(0, len(tri), 3):
                a, b, d = tri[t], tri[t + 1], tri[t + 2]
                ax, ay = pos[a][0] * sx, pos[a][1] * sy
                bx, by = pos[b][0] * sx, pos[b][1] * sy
                cx, cy = pos[d][0] * sx, pos[d][1] * sy
                den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
                if not den:
                    continue
                x0, x1 = max(int(min(ax, bx, cx) - 0.5), 0), min(int(max(ax, bx, cx) - 0.5) + 1, width - 1)
                y0, y1 = max(int(min(ay, by, cy) - 0.5), 0), min(int(max(ay, by, cy) - 0.5) + 1, height - 1)
                za, zb, zc = zs[a], zs[b], zs[d]
                for py in range(y0, y1 + 1):
                    qy = py + 0.5
                    row = grid[py]
                    for px in range(x0, x1 + 1):
                        qx = px + 0.5
                        l1 = ((by - cy) * (qx - cx) + (cx - bx) * (qy - cy)) / den
                        l2 = ((cy - ay) * (qx - cx) + (ax - cx) * (qy - cy)) / den
                        l3 = 1 - l1 - l2
                        if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                            row[px] = l1 * za + l2 * zb + l3 * zc
        return grid

    # -- editing ----------------------------------------------------------------------------------------------

    def edit_heights(self, fn: Callable[[float, float, float], float | None], keep_border: bool = True) -> int:
        """Set new ground heights. `fn(x, y, z)` gets a vertex's world position and returns its new world z (or
        None to leave it). Heights are clamped to the file's z bounds (the whole-file quantization range).
        Vertices on the outer map edge are left alone by default: the skirt mesh hangs from them.

        For every changed cell: normals are recomputed for the changed vertices and their neighbours (area-weighted
        face normals of list 0), the streams are re-encoded, and the bounds of the touched patches recomputed.
        Returns the number of vertices whose height changed."""
        total = 0
        for c in self.cells:
            pos = [list(p) for p in c.positions()]
            changed = []
            for i, p in enumerate(pos):
                if keep_border and (p[0] in (0, Q_MAX) or p[1] in (0, Q_MAX)):
                    continue
                nz = fn(self.to_world(0, p[0]), self.to_world(1, p[1]), self.to_world(2, p[2]))
                if nz is None:
                    continue
                q = self.to_quant(2, nz)
                if q != p[2]:
                    p[2] = q
                    changed.append(i)
            if changed:
                self._commit(c, pos, changed)
                total += len(changed)
        return total

    def set_heights(self, k: int, heights: dict[int, int]) -> int:
        """Give vertices of cell `k` new quantized heights ({vertex index: z, 0..32767}), then recompute what
        depends on them, as edit_heights does (the normals around them, the bounds of their patches). Returns how
        many changed."""
        c = self.cells[k]
        pos = [list(p) for p in c.positions()]
        changed = []
        for i, q in sorted(heights.items()):
            q = min(max(int(q), 0), Q_MAX)
            if pos[i][2] != q:
                pos[i][2] = q
                changed.append(i)
        if changed:
            self._commit(c, pos, changed)
        return len(changed)

    def _commit(self, c: Cell, pos: list[list[int]], changed: list[int]) -> None:
        tri = c.triangles(0)
        moved = set(changed)
        faces = [t for t in range(0, len(tri), 3) if tri[t] in moved or tri[t + 1] in moved or tri[t + 2] in moved]
        affected = {tri[t + j] for t in faces for j in range(3)}
        nor = [list(n) for n in c.normals()]
        for i, n in self._normals(pos, tri, affected).items():
            nor[i][:3] = n
        c.set_vertices(pos, nor)
        has_water = bool(c.flags & 2)
        patches = c.patch_list()
        for p in patches:
            if p.vcount and any(p.vstart <= i < p.vstart + p.vcount for i in changed):
                run = pos[p.vstart:p.vstart + p.vcount]
                p.zhi = self._z_f32(max(max(v[2], v[3]) for v in run))
                if has_water:
                    p.zlo = self._z_f32(min(v[2] for v in run))
        c.set_patches(patches)

    def _normals(self, pos: list, tri: list[int], which: set[int]) -> dict[int, list[int]]:
        """Byte normals for the vertices in `which`: sum of the (upward) area-weighted normals of their faces."""
        P = [(self.to_world(0, p[0]), self.to_world(1, p[1]), self.to_world(2, p[2])) for p in pos]
        acc = {i: [0.0, 0.0, 0.0] for i in which}
        for t in range(0, len(tri), 3):
            a, b, d = tri[t], tri[t + 1], tri[t + 2]
            if a not in acc and b not in acc and d not in acc:
                continue
            ux, uy, uz = (P[b][k] - P[a][k] for k in range(3))
            vx, vy, vz = (P[d][k] - P[a][k] for k in range(3))
            n = [uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx]
            if n[2] < 0:
                n = [-n[0], -n[1], -n[2]]
            for v in (a, b, d):
                if v in acc:
                    s = acc[v]
                    s[0] += n[0]
                    s[1] += n[1]
                    s[2] += n[2]
        out = {}
        for i, s in acc.items():
            ln = math.sqrt(s[0] * s[0] + s[1] * s[1] + s[2] * s[2])
            s = [x / ln for x in s] if ln else [0.0, 0.0, 1.0]
            out[i] = [min(max(round((x + 1) * 127.5), 0), 255) for x in s]
        return out


def plateau(cx: float, cy: float, top_radius: float, base_radius: float, top_z: float) -> Callable:
    """Height function for `Tms.edit_heights`: a flat-topped mound centred on world (cx, cy). Inside top_radius
    the ground is raised to top_z; between top_radius and base_radius it slopes linearly back down to the
    original ground; outside it (and wherever the ground is already higher) nothing changes."""
    def fn(x: float, y: float, z: float) -> float | None:
        d = math.hypot(x - cx, y - cy)
        if d >= base_radius:
            return None
        t = 1.0 if d <= top_radius else (base_radius - d) / (base_radius - top_radius)
        new = z + (top_z - z) * t
        return new if new > z else None
    return fn
