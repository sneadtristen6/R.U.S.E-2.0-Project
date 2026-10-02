"""Terrain texture tiles: the .tmst_pc index and its .tmst_chunk_pc tile store (read and write, lossless).

Every map pack carries two tile sets, output\\highdef.* and output\\lowdef.*. Each set is an index (.tmst_pc) plus
a store (.tmst_chunk_pc) of 512x512 DXT1 tiles, each tile being a complete one-mip TGV texture. The tiles form a
pyramid over a grid of cells: one whole-map overview tile, then per cell 1, 2x2 and 4x4 tiles (for the shipped
depth of 3). See docs/FORMATS.md.

The writer keeps the index header and the tiles' storage order and only re-lays the store and patches the
(offset, size) table and the two size fields, so an unchanged rebuild is byte-identical to the original.

Also here: a minimal TGV header reader/builder and the plain 'ZIPO' mip payload (zlib-packed raw texel data)
that ordinary .tgv textures use, to build replacement tiles without the terrain's own TGU1 codec.
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import Iterator

MAGIC = b"TMST"
TAGS = b"ATEXKEYSTEXF"  # section tags at 0x40, right before the table; ATEX and KEYS are empty in every map
TILE = 512              # pixel size of every regular tile


@dataclass
class Tile:
    index: int    # position in the index table (0 = the overview tile)
    level: int    # 0 = finest (2**(depth-1) tiles per cell side) ... depth-1 = one tile per cell; depth = overview
    x: int        # column at this level, 0 = map's left edge (terrain.png orientation)
    y: int        # row at this level, 0 = map's top edge (terrain.png orientation)
    offset: int   # byte offset of the tile's TGV record in the store
    size: int     # record length, including the 0-3 zero bytes that keep records 4-aligned


class Tmst:
    """One tile set: `index` is the .tmst_pc member, `chunk` the .tmst_chunk_pc member (bytes or any buffer)."""

    def __init__(self, index: bytes, chunk):
        if index[:4] != MAGIC or index[-4:] != MAGIC:
            raise ValueError(f"not a TMST index: {bytes(index[:4])!r}")
        (self.version, self.platform, file_size, self.key, self.grid_w, self.grid_h, self.depth,
         chunk_size, self.table_offset, table_size) = struct.unpack_from("<I4sIIIIIIII", index, 4)
        if self.version != 3:
            raise ValueError(f"unsupported TMST version {self.version}")
        if file_size != len(index) or chunk_size != len(chunk):
            # not a game rule: a damaged or unexpected file
            raise ValueError(f"size fields {file_size}/{chunk_size} do not match {len(index)}/{len(chunk)}")
        count = table_size // 8
        if count != 1 + self.grid_w * self.grid_h * sum(4 ** k for k in range(self.depth)):
            raise ValueError(f"{count} records do not fit a {self.grid_w}x{self.grid_h} grid of depth {self.depth}")
        self.index = bytes(index)
        self.chunk = chunk
        self.lod = self.index_path = self.chunk_path = None  # set by from_edat
        self.tiles: list[Tile] = []
        for i in range(count):
            offset, size = struct.unpack_from("<II", index, self.table_offset + 8 * i)
            level, x, y = self._place(i)
            self.tiles.append(Tile(i, level, x, y, offset, size))
        self._by_pos = {(t.level, t.x, t.y): t for t in self.tiles}

    @classmethod
    def from_edat(cls, arc, lod: str = "highdef") -> "Tmst":
        """Read output\\<lod>.tmst_pc and .tmst_chunk_pc from an open map pack (an `Edat`)."""
        ie, ce = arc.find(f"\\{lod}.tmst_pc"), arc.find(f"\\{lod}.tmst_chunk_pc")
        t = cls(arc.read(ie), arc.read(ce))
        t.lod, t.index_path, t.chunk_path = lod, ie.path, ce.path
        return t

    def _place(self, i: int) -> tuple[int, int, int]:
        """Record i -> (level, x, y). After the overview come the levels coarse to fine; within a level the
        records are grouped by cell (cells row-major), and a cell's tiles are row-major inside it."""
        if i == 0:
            return self.depth, 0, 0
        i -= 1
        for level in range(self.depth - 1, -1, -1):
            side = 1 << (self.depth - 1 - level)
            n = self.grid_w * self.grid_h * side * side
            if i < n:
                cell, inner = divmod(i, side * side)
                cy, cx = divmod(cell, self.grid_w)
                ty, tx = divmod(inner, side)
                return level, cx * side + tx, cy * side + ty
            i -= n
        raise IndexError(i)

    def tile(self, level: int, x: int, y: int) -> Tile:
        return self._by_pos[(level, x, y)]

    def area(self, tile: Tile) -> tuple[float, float, float, float]:
        """(x0, y0, x1, y1) covered by `tile`, in grid cells from the map's top-left corner."""
        if tile.level == self.depth:
            return 0.0, 0.0, float(self.grid_w), float(self.grid_h)
        side = 1 << (self.depth - 1 - tile.level)
        return tile.x / side, tile.y / side, (tile.x + 1) / side, (tile.y + 1) / side

    def read(self, tile: Tile) -> bytes:
        """The tile's stored TGV record (with its alignment padding)."""
        return bytes(self.chunk[tile.offset:tile.offset + tile.size])

    def texture(self, tile: Tile) -> "Tgv":
        return Tgv(self.read(tile))

    def _layout(self, replace: dict[int, bytes]) -> tuple[list[Tile], dict[int, tuple[int, int]], int]:
        """Storage order (kept from the original), new (offset, size) per record, new store size.
        The store is: key, then each record followed by the key again."""
        for i in replace:
            if not 0 <= i < len(self.tiles):
                raise IndexError(f"no record {i}")
        order = sorted(self.tiles, key=lambda t: t.offset)
        placed, pos = {}, 4
        for t in order:
            size = _aligned(len(replace[t.index])) if t.index in replace else t.size
            placed[t.index] = (pos, size)
            pos += size + 4
        return order, placed, pos

    def iter_chunk(self, replace: dict[int, bytes] | None = None) -> Iterator[bytes]:
        """Stream the rebuilt store. `replace` maps a record index -> new TGV record bytes (any length)."""
        replace = replace or {}
        order, _, _ = self._layout(replace)
        sep = struct.pack("<I", self.key)
        yield sep
        for t in order:
            if t.index in replace:
                blob = replace[t.index]
                yield blob + b"\0" * (_aligned(len(blob)) - len(blob))
            else:
                yield self.read(t)
            yield sep

    def build_index(self, replace: dict[int, bytes] | None = None) -> bytes:
        replace = replace or {}
        _, placed, total = self._layout(replace)
        out = bytearray(self.index)
        struct.pack_into("<I", out, 0x20, total)  # the index's size field (0x0C) cannot change: same record count
        for i, (offset, size) in placed.items():
            struct.pack_into("<II", out, self.table_offset + 8 * i, offset, size)
        return bytes(out)

    def rebuild(self, replace: dict[int, bytes] | None = None) -> tuple[bytes, bytes]:
        """Return (new .tmst_pc, new .tmst_chunk_pc)."""
        return self.build_index(replace), b"".join(self.iter_chunk(replace))

    def members(self, replace: dict[int, bytes] | None = None) -> dict[str, bytes]:
        """The rebuilt pair keyed by member path, ready for `Edat.write_to(out, replace=...)`."""
        if self.index_path is None:
            raise ValueError("member paths are only known for a tile set read with from_edat")
        index, chunk = self.rebuild(replace)
        return {self.index_path: index, self.chunk_path: chunk}


def _aligned(n: int) -> int:
    return (n + 3) & ~3


# --- TGV textures ------------------------------------------------------------------------------------------

class Tgv:
    """Header of a TGV texture: version, flag, width, height, a second width/height pair (equal to the first in
    every file seen), the format name (e.g. 'DXT1') and (offset, size) of each mip payload."""

    def __init__(self, raw: bytes):
        (self.version, self.flag, self.width, self.height, self.width2, self.height2,
         count, name_len) = struct.unpack_from("<6IHH", raw, 0)
        if self.version != 1:
            raise ValueError(f"unsupported TGV version {self.version}")
        self.format = raw[28:28 + name_len].decode("ascii")
        table = _aligned(28 + name_len)
        offsets = struct.unpack_from(f"<{count}I", raw, table)
        sizes = struct.unpack_from(f"<{count}I", raw, table + 4 * count)
        self.mips = list(zip(offsets, sizes))
        self.raw = raw

    def payload(self, mip: int = 0) -> bytes:
        offset, size = self.mips[mip]
        return self.raw[offset:offset + size]

    @property
    def codec(self) -> str:
        """'ZIPO', 'TGU1' (the terrain/texture DCT codec) or whatever tag the first mip starts with."""
        return self.payload(0)[:4].decode("latin-1")


def make_tgv(width: int, height: int, fmt: str, mips: list[bytes]) -> bytes:
    """Build a TGV record (version 1, flag 1, as the game's own) with the given mip payloads, 4-aligned."""
    name = fmt.encode("ascii")
    table = _aligned(28 + len(name))
    head = bytearray(struct.pack("<6IHH", 1, 1, width, height, width, height, len(mips), len(name)) + name)
    head += b"\0" * (table - len(head))
    pos, offsets = table + 8 * len(mips), []
    for m in mips:
        offsets.append(pos)
        pos = _aligned(pos + len(m))
    head += struct.pack(f"<{len(mips)}I", *offsets) + struct.pack(f"<{len(mips)}I", *(len(m) for m in mips))
    body = b"".join(m + b"\0" * (_aligned(len(m)) - len(m)) for m in mips)
    return bytes(head) + body


def zipo_pack(raw: bytes) -> bytes:
    """'ZIPO' + u32 unpacked size + zlib stream ending in a sync flush (no final block), as the game writes it."""
    c = zlib.compressobj(9)
    return b"ZIPO" + struct.pack("<I", len(raw)) + c.compress(raw) + c.flush(zlib.Z_SYNC_FLUSH)


def zipo_unpack(payload: bytes) -> bytes:
    if payload[:4] != b"ZIPO":
        raise ValueError(f"not a ZIPO payload: {payload[:4]!r}")
    size = struct.unpack_from("<I", payload, 4)[0]
    raw = zlib.decompressobj().decompress(payload[8:])
    if len(raw) != size:
        raise ValueError(f"ZIPO unpacked to {len(raw)} bytes, header says {size}")
    return raw


# --- hand-made DXT1 -----------------------------------------------------------------------------------------

def rgb565(r: int, g: int, b: int) -> int:
    return (r >> 3) << 11 | (g >> 2) << 5 | b >> 3


def dxt1_solid(color: int) -> bytes:
    """One 4x4 DXT1 block of a single RGB565 colour (both endpoints equal, every selector 0)."""
    return struct.pack("<HHI", color, color, 0)


def dxt1_checker(width: int, height: int, square: int, a: int, b: int) -> bytes:
    """DXT1 blocks (row-major, 8 bytes per 4x4) for a checkerboard of `square`-pixel squares, colours a/b (RGB565)."""
    if width % 4 or height % 4 or square % 4:
        raise ValueError("width, height and square must be multiples of 4")
    ba, bb = dxt1_solid(a), dxt1_solid(b)
    rows = []
    for by in range(height // 4):
        row = b"".join(ba if ((bx * 4 // square) + (by * 4 // square)) % 2 == 0 else bb for bx in range(width // 4))
        rows.append(row)
    return b"".join(rows)


def zipo_tile(blocks: bytes, width: int = TILE, height: int = TILE) -> bytes:
    """A terrain-shaped tile record (one DXT1 mip) whose payload is ZIPO instead of the terrain's TGU1."""
    if len(blocks) != width * height // 2:
        raise ValueError(f"{len(blocks)} bytes of DXT1 do not fill {width}x{height}")
    return make_tgv(width, height, "DXT1", [zipo_pack(blocks)])


MAGENTA, YELLOW = rgb565(255, 0, 255), rgb565(255, 255, 0)


def checker_tile(a: int = MAGENTA, b: int = YELLOW, square: int = 64) -> bytes:
    """The standard in-game test tile: a 512x512 checkerboard of 64-pixel squares, ZIPO-packed."""
    return zipo_tile(dxt1_checker(TILE, TILE, square, a, b))
