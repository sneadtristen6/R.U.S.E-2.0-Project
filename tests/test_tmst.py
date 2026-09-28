"""Terrain tile sets (.tmst_pc + .tmst_chunk_pc) and ZIPO tiles, on a tiny made-up tile set (no game files)."""
import struct
import unittest
import zlib

from fixtures import make_edat
from rusemod import Edat
from rusemod.tmst import (TAGS, Tgv, Tmst, checker_tile, dxt1_checker, dxt1_solid, make_tgv, rgb565,
                          zipo_pack, zipo_tile, zipo_unpack)

KEY = 0x1234CB7A
GRID_W, GRID_H, DEPTH = 2, 1, 2          # 2x1 cells, 1 + 2x2 tiles per cell: 1 + 2 * (1 + 4) = 11 records
STORED = [3, 1, 4, 5, 6, 2, 7, 8, 9, 10, 0]  # storage order: scrambled, overview last, like the game's


def record(i: int) -> bytes:
    """A fake stored tile: 4-aligned, with a distinct body per record."""
    body = bytes([i]) * (8 + 4 * i)
    return b"REC" + bytes([i]) + body


def make_set(records=None, order=STORED):
    records = records or [record(i) for i in range(11)]
    chunk, table = bytearray(struct.pack("<I", KEY)), {}
    for i in order:
        table[i] = (len(chunk), len(records[i]))
        chunk += records[i] + struct.pack("<I", KEY)
    n = len(records)
    size = 0x4C + 8 * n + 4
    head = struct.pack("<4sI4sIIIIIIII5I", b"TMST", 3, b"PC\0\0", size, KEY, GRID_W, GRID_H, DEPTH,
                       len(chunk), 0x4C, 8 * n, 0, 0x44, 0, 0x48, 0)
    index = head + TAGS + b"".join(struct.pack("<II", *table[i]) for i in range(n)) + b"TMST"
    return index, bytes(chunk)


class Reading(unittest.TestCase):
    def setUp(self):
        self.index, self.chunk = make_set()
        self.t = Tmst(self.index, self.chunk)

    def test_header(self):
        t = self.t
        self.assertEqual((t.key, t.grid_w, t.grid_h, t.depth, len(t.tiles)), (KEY, 2, 1, 2, 11))

    def test_placement_overview_then_coarse_to_fine_grouped_by_cell(self):
        got = [(x.level, x.x, x.y) for x in self.t.tiles]
        self.assertEqual(got, [(2, 0, 0),                              # overview
                               (1, 0, 0), (1, 1, 0),                   # one per cell, cells row-major
                               (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1),   # cell 0, row-major inside
                               (0, 2, 0), (0, 3, 0), (0, 2, 1), (0, 3, 1)])  # cell 1

    def test_tile_lookup_and_area(self):
        t = self.t
        self.assertEqual(t.tile(0, 3, 1).index, 10)
        self.assertEqual(t.area(t.tile(0, 3, 1)), (1.5, 0.5, 2.0, 1.0))
        self.assertEqual(t.area(t.tile(1, 1, 0)), (1.0, 0.0, 2.0, 1.0))
        self.assertEqual(t.area(t.tiles[0]), (0.0, 0.0, 2.0, 1.0))

    def test_reads_every_record(self):
        for tile in self.t.tiles:
            self.assertEqual(self.t.read(tile), record(tile.index))

    def test_rejects_bad_files(self):
        with self.assertRaises(ValueError):
            Tmst(b"TMSG" + self.index[4:], self.chunk)
        with self.assertRaises(ValueError):
            Tmst(self.index, self.chunk + b"\0\0\0\0")  # chunk size field no longer matches


class Writing(unittest.TestCase):
    def setUp(self):
        self.index, self.chunk = make_set()
        self.t = Tmst(self.index, self.chunk)

    def test_unchanged_rebuild_is_byte_identical(self):
        self.assertEqual(self.t.rebuild(), (self.index, self.chunk))
        self.assertEqual(b"".join(self.t.iter_chunk()), self.chunk)

    def test_replacing_with_other_sizes(self):
        new = {4: b"BIGGER" * 50 + b"x", 0: b"tiny"}  # 301 bytes (gets padded to 304) and 4 bytes
        index, chunk = self.t.rebuild(new)
        n = Tmst(index, chunk)  # size fields must be consistent or this raises
        self.assertEqual(struct.unpack_from("<I", index, 0x20)[0], len(chunk))
        self.assertEqual(len(chunk), len(self.chunk) + 304 - len(record(4)) + 4 - len(record(0)))
        self.assertEqual(n.read(n.tiles[4]), new[4] + b"\0\0\0")
        self.assertEqual(n.read(n.tiles[0]), new[0])
        for a, b in zip(self.t.tiles, n.tiles):
            if a.index not in new:
                self.assertEqual(n.read(b), self.t.read(a))
        self.assertEqual([x.index for x in sorted(n.tiles, key=lambda x: x.offset)], STORED)  # order kept
        sep = struct.pack("<I", KEY)
        for x in n.tiles:
            self.assertEqual(chunk[x.offset - 4:x.offset], sep)
            self.assertEqual(chunk[x.offset + x.size:x.offset + x.size + 4], sep)
        self.assertEqual(len(index), len(self.index))
        self.assertEqual(index[:0x20], self.index[:0x20])

    def test_rejects_unknown_record(self):
        with self.assertRaises(IndexError):
            self.t.rebuild({11: b"nope"})

    def test_members_round_trip_through_a_map_pack(self):
        pack = make_edat([("dir", "output\\", [
            ("file", "highdef.tmst_chunk_pc", self.chunk),
            ("file", "highdef.tmst_pc", self.index),
            ("file", "terrain.png", b"PNG"),
        ])])
        arc = Edat(pack)
        t = Tmst.from_edat(arc, "highdef")
        tile = t.tile(0, 2, 1)
        rebuilt = Edat(arc.to_bytes(t.members({tile.index: checker_tile()})))
        again = Tmst.from_edat(rebuilt, "highdef")
        self.assertEqual(Tgv(again.read(again.tiles[tile.index])).codec, "ZIPO")
        self.assertEqual(rebuilt.read(rebuilt.find("terrain.png")), b"PNG")
        self.assertEqual(rebuilt.checksum, arc.checksum)


class Textures(unittest.TestCase):
    def test_zipo_round_trip_and_sync_flush_ending(self):
        raw = bytes(range(256)) * 40
        z = zipo_pack(raw)
        self.assertEqual(z[:4], b"ZIPO")
        self.assertEqual(struct.unpack_from("<I", z, 4)[0], len(raw))
        self.assertEqual(z[-4:], b"\0\0\xff\xff")  # sync flush, no final block: the game's own streams end so
        d = zlib.decompressobj()
        self.assertEqual(d.decompress(z[8:]), raw)
        self.assertFalse(d.eof)
        self.assertEqual(zipo_unpack(z), raw)
        with self.assertRaises(ValueError):
            zipo_unpack(b"TGU1" + z[4:])

    def test_make_tgv_aligns_payloads(self):
        raw = make_tgv(8, 8, "DXT5_LIN", [b"abc", b"defgh"])
        tex = Tgv(raw)
        self.assertEqual((tex.version, tex.flag, tex.width, tex.height, tex.format), (1, 1, 8, 8, "DXT5_LIN"))
        self.assertEqual(tex.mips, [(0x34, 3), (0x38, 5)])  # table at 0x24 (28 + 8), payloads 4-aligned
        self.assertEqual((tex.payload(0), tex.payload(1)), (b"abc", b"defgh"))
        self.assertEqual(len(raw) % 4, 0)

    def test_solid_and_checker_blocks(self):
        red, blue = rgb565(255, 0, 0), rgb565(0, 0, 255)
        self.assertEqual((red, blue), (0xF800, 0x001F))
        self.assertEqual(dxt1_solid(red), b"\x00\xf8\x00\xf8\0\0\0\0")
        blocks = dxt1_checker(16, 8, 8, red, blue)  # 4x2 blocks, squares of 2x2 blocks
        self.assertEqual(len(blocks), 4 * 2 * 8)
        row0 = [blocks[8 * i:8 * i + 8] for i in range(4)]
        row1 = [blocks[32 + 8 * i:32 + 8 * i + 8] for i in range(4)]
        self.assertEqual(row0, [dxt1_solid(red)] * 2 + [dxt1_solid(blue)] * 2)
        self.assertEqual(row1, row0)
        with self.assertRaises(ValueError):
            dxt1_checker(10, 8, 4, red, blue)

    def test_checker_tile_has_the_terrain_tile_shape(self):
        tex = Tgv(checker_tile())
        self.assertEqual((tex.width, tex.height, tex.width2, tex.height2, tex.format), (512, 512, 512, 512, "DXT1"))
        self.assertEqual((len(tex.mips), tex.mips[0][0], tex.codec), (1, 0x28, "ZIPO"))
        self.assertEqual(len(zipo_unpack(tex.payload())), 512 * 512 // 2)
        with self.assertRaises(ValueError):
            zipo_tile(b"\0" * 8)


if __name__ == "__main__":
    unittest.main()
