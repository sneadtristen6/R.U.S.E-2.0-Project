"""Trees the build writes start with a split, as every shipped one does: the SDB quadtrees (ruse_mod_engine.sdb
build_ents: the game reads their root as a node without looking, and a one-leaf root crashed it when a building was
placed) and the k-d trees made again by rusemod.kdt_edit.rebuild (a zone map of four sectors whose tree was one leaf
picked the same sector wherever the player pointed)."""
import struct
import unittest

from test_sectors import RING_A, RING_B, W, H, level_at, template
from rusemod import kdt_edit
from rusemod import sectors as S
from rusemod.kdt import Kdt, Leaf, leaves
from ruse_mod_engine import sdb


def made_up_sdb() -> bytes:
    """An SDB of one leaf over a 1,000,000 square (the layout encode keeps: its 28-byte header and what follows)."""
    header = struct.pack("<5f2I", 0.0, 0.0, 1.0e6, 1.0e6, 1.0e6 / 8, 0, 0)   # x0, y0, width, height, cell, 2 more
    payload = header + struct.pack("<I", 0x01010101)
    return b"SDB\r\n" + bytes(16) + struct.pack("<II", 2, len(payload)) + payload + b"tail"


def root(raw: bytes) -> int:
    return struct.unpack_from("<I", raw, 57)[0]


class SdbRoot(unittest.TestCase):
    def test_a_uniform_grid_gets_a_split_root(self):
        R = 8
        out = sdb.encode_from_grid(made_up_sdb(), bytearray([0x01] * (R * R)), R)
        self.assertEqual(root(out), 0x20)                      # a node, its four quarters right after it
        g = sdb.decode_grid(out)
        self.assertEqual(set(g["grid"]), {0x01})
        self.assertEqual(g["bboxX"], 1.0e6)
        self.assertTrue(out.endswith(b"tail"))

    def test_four_uniform_quarters_keep_their_values(self):
        R = 8
        grid = bytearray(R * R)
        for y in range(R):
            for x in range(R):
                grid[y * R + x] = (0x01, 0x09, 0x05, 0x0D)[(x >= R // 2) + 2 * (y >= R // 2)]
        out = sdb.encode_from_grid(made_up_sdb(), grid, R)
        self.assertFalse(root(out) & 1)
        g = sdb.decode_grid(out)
        k = R // g["R"]                                         # the same picture, perhaps on fewer cells
        for y in range(g["R"]):
            for x in range(g["R"]):
                self.assertEqual(g["grid"][y * g["R"] + x], grid[(y * k) * R + x * k])

    def test_a_two_by_two_grid_is_doubled_up(self):
        out = sdb.encode_from_grid(made_up_sdb(), bytearray([0x01, 0x05, 0x09, 0x0D]), 2)
        self.assertFalse(root(out) & 1)
        g = sdb.decode_grid(out)
        self.assertEqual(g["R"], 4)
        self.assertEqual([g["grid"][0], g["grid"][3], g["grid"][12], g["grid"][15]], [0x01, 0x05, 0x09, 0x0D])

    def test_a_mixed_grid_is_written_as_before(self):
        R = 8
        grid = bytearray([0x01] * (R * R))
        grid[3 * R + 5] = 0x09                                  # one forest cell: the root splits anyway
        ents = sdb.build_ents(grid, R)
        self.assertEqual(ents[0], 0x20)
        back = sdb.decode_grid(sdb.encode(made_up_sdb(), ents))
        self.assertEqual(bytes(back["grid"]), bytes(grid))


class KdtRoot(unittest.TestCase):
    def test_a_handful_of_triangles_still_starts_with_a_split(self):
        kdt = S.zone_map(template(), {0: list(RING_A), 1: list(RING_B)}, W, H)
        k = Kdt(kdt)
        self.assertNotIsInstance(k.tree(0), Leaf)
        self.assertEqual(kdt_edit.check(k, 0), [])
        self.assertEqual(level_at(k, 70000.0, 80000.0), 0)
        self.assertEqual(level_at(k, 150000.0, 80000.0), 1)

    def test_a_big_map_is_cut_into_small_triangles_and_small_leaves(self):
        # four quarter-map sectors on a map 80 km across: no edge over ZONE_EDGE_MOST, a tree of many leaves, every
        # place still in its own sector
        size = 64 * 327680.0
        h = size / 2
        rings = {n: [(h * (n % 2), h * (n // 2)), (h * (n % 2) + h, h * (n // 2)), (h * (n % 2) + h, h * (n // 2) + h),
                     (h * (n % 2), h * (n // 2) + h)] for n in range(4)}
        k = Kdt(S.zone_map(template(), rings, size, size))
        pos = [(k.to_world(0, p[0]), k.to_world(1, p[1])) for p in k.positions(0)]
        idx = k.indices(0)
        longest = max(((pos[idx[t + i]][0] - pos[idx[t + (i + 1) % 3]][0]) ** 2
                       + (pos[idx[t + i]][1] - pos[idx[t + (i + 1) % 3]][1]) ** 2) ** 0.5
                      for t in range(0, len(idx), 3) for i in range(3))
        self.assertLessEqual(longest, S.ZONE_EDGE_MOST + 2 * size / 32767)
        self.assertGreater(len(idx) // 3, 8)
        self.assertGreaterEqual(len(k.trilists(0)), 5)        # the 80 km test's working zone map had 5
        self.assertEqual(kdt_edit.check(k, 0), [])
        for n in range(4):
            self.assertEqual(level_at(k, h * (n % 2) + h / 3, h * (n // 2) + h / 3), n)

    def test_every_triangle_is_listed_on_a_side_it_touches(self):
        k = Kdt(S.zone_map(template(), {0: list(RING_A), 1: list(RING_B)}, W, H))
        listed = {t for lst in k.trilists(0) for t in lst}
        self.assertEqual(listed, set(range(len(k.indices(0)) // 3)))
        self.assertGreaterEqual(len(list(leaves(k.tree(0)))), 2)


if __name__ == "__main__":
    unittest.main()
