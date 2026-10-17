"""Bigger maps (rusemod.bigmap, newmap's size / clouds / room, sectors' Make sectors): the pieces that need no game
files. The grown map itself was proven in the game (an 80.7 km map, 2026-10-17); its build runs on a real copy."""
import math
import struct
import unittest

from rusemod import bigmap, newmap, sectors

try:
    from rusemod.numpy2 import np
except ImportError:  # the apps carry numpy
    np = None


class Sizes(unittest.TestCase):
    def test_even_sizes_within_the_limits(self):
        self.assertEqual(bigmap.check_size([24, 16]), (24, 16))
        self.assertEqual(bigmap.check_size((2, bigmap.MOST)), (2, bigmap.MOST))
        for bad in ([23, 16], [0, 16], [bigmap.MOST + 2, 2], [24], "24x16", [24.0, 16], [True, 2]):
            with self.assertRaises(bigmap.BigMapError):
                bigmap.check_size(bad)

    def test_mesh_density_drops_past_16_by_16(self):
        from rusemod import groundgen as G
        self.assertEqual(bigmap.per_cell(256), (G.PER_CELL_NEAR, G.PER_CELL_FAR))
        self.assertEqual(bigmap.per_cell(258), (32, 16))

    def test_whole_map_pictures_keep_their_shape(self):
        self.assertEqual(bigmap.picture_size(12, 8, 64), (768, 512))
        w, h = bigmap.picture_size(64, 32, 64)
        self.assertEqual((w, h), (2048, 1024))

    def test_sdb_cells_a_side(self):
        self.assertEqual(bigmap.grid_r(3932160.0), 4096)          # D-Day's: 960 units a cell
        self.assertEqual(bigmap.grid_r(64 * bigmap.CASE), 16384)   # at most the readers' cap
        self.assertLessEqual(64 * bigmap.CASE / bigmap.grid_r(64 * bigmap.CASE), 1280.0)


def made_up_sdb() -> bytes:
    header = struct.pack("<5f2I", 0.0, 0.0, 1.0e6, 1.0e6, 1000.0, 0, 0)
    payload = header + struct.pack("<I", 0x01010101)
    return b"SDB\r\n" + bytes(16) + struct.pack("<II", 2, len(payload)) + payload


class Trees(unittest.TestCase):
    def test_a_uniform_tree_is_as_deep_as_asked_and_never_one_leaf(self):
        from ruse_mod_engine import sdb
        for r in (4, 1024, 16384):
            out = bigmap.uniform_sdb(made_up_sdb(), (0.0, 0.0, 2.0e7, 1.0e7), 0x01, r)
            p = sdb.parse(out)
            self.assertEqual(sdb.tree_grid_R(p), r)
            self.assertFalse(struct.unpack_from("<I", out, 57)[0] & 1)
            g = sdb.decode_grid(out) if r <= 4096 else None
            if g is not None:
                self.assertEqual(set(g["grid"]), {0x01})
                self.assertEqual((g["bboxX"], g["bboxY"]), (2.0e7, 1.0e7))


class Movement(unittest.TestCase):
    def test_a_lattice_over_a_map_wider_than_it_is_deep(self):
        from rusemod.nav import Graph
        size = (24 * bigmap.CASE, 16 * bigmap.CASE)
        raw, circles, links = bigmap.lattice(size)
        g = Graph.read(raw)
        self.assertEqual(g.box[2], size[0])                        # the longer side, as D-Day's graphs
        self.assertEqual(len(g.parts()), 1)
        self.assertTrue(g.walkable(size[0] - 5000.0, size[1] - 5000.0) and g.walkable(5000.0, 5000.0))
        self.assertEqual(len(g.circles) - 1, circles)


class Shift(unittest.TestCase):
    TEXT = ("# a comment with x = 5\n[[object]]\nname = \"House\"\nx = 100.0\ny = 200.0\nturn = 1.5\n\n"
            "[[erase]]\nx = 50.0\ny = 60.0\nradius = 10.0\n\n"
            "[[stroke]]\nbrush = \"level\"\nx = 1.0\ny = 2.0\nradius = 3.0\npoints = [[10.0, 20.0], [30.0, 40.0]]\n"
            "dx = 1.0\ndy = 0.0\n\n[[sectors.paint]]\nfile = \"a.scenario\"\nsector = 1\n"
            "area = [[0.0, 0.0],\n  [5.0, 0.0], [5.0, 5.0]]\nwithin = [[[1.0, 1.0], [2.0, 2.0], [3.0, 1.0]]]\n")

    def test_the_mods_places_move_and_the_copied_maps_stay(self):
        out, n = bigmap.shift_text(self.TEXT, 1000.0, -500.0)
        self.assertIn("x = 1100.0\ny = -300.0", out)                # an object of the mod's
        self.assertIn("[[erase]]\nx = 50.0\ny = 60.0", out)         # erases name the copied map's own objects
        self.assertIn("points = [[1010.0, -480.0], [1030.0, -460.0]]", out)
        self.assertIn("dx = 1.0\ndy = 0.0", out)                    # a direction isn't a place
        self.assertIn("area = [[1000.0, -500.0],\n  [1005.0, -500.0], [1005.0, -495.0]]", out)
        self.assertIn("within = [[[1001.0, -499.0], [1002.0, -498.0], [1003.0, -499.0]]]", out)
        self.assertIn("# a comment with x = 5", out)
        self.assertEqual(n, 2 + 2 + 4 + 6 + 6)

    def test_a_points_triple_keeps_its_height(self):
        out, _n = bigmap.shift_text("points = [[1.0, 2.0, 3.0]]\n", 10.0, 10.0)
        self.assertEqual(out, "points = [[11.0, 12.0, 3.0]]\n")

    def test_the_blank_starts_strokes_reach_over_the_new_size(self):
        old = bigmap.whole_map_reach(3932160.0, 2621440.0)
        self.assertAlmostEqual(old[2], 2336165.647, places=2)       # Blank Terrain's on D-Day (presets.whole_map)
        text = ("[[stroke]]\nbrush = \"level\"\nx = 1966080.0\ny = 1310720.0\nradius = 2336165.6470588236\n"
                "level = 19233.0\n\n[[stroke]]\nbrush = \"raise\"\nx = 5.0\ny = 5.0\nradius = 9.0\n")
        new = bigmap.whole_map_reach(24 * bigmap.CASE, 16 * bigmap.CASE)
        out, n = bigmap.refit_whole_map(text, old, new)
        self.assertEqual(n, 1)
        self.assertIn(f"x = {new[0]!r}\ny = {new[1]!r}\nradius = {new[2]!r}", out)
        self.assertIn("brush = \"raise\"\nx = 5.0\ny = 5.0\nradius = 9.0", out)


class MapToml(unittest.TestCase):
    BASE = {"copy_of": "M04_Cotentin", "name": "Big", "ground": "generated", "blank": "terrain"}

    def test_size_clouds_and_room(self):
        spec, = newmap.parse({**self.BASE, "size": [24, 16], "clouds": 900, "room": "out"}, "map.toml", "Big")
        self.assertEqual((spec.size, spec.clouds, spec.room), ((24, 16), 900 * newmap.M, "out"))
        off, = newmap.parse({**self.BASE, "size": [24, 16], "clouds": "off"}, "map.toml", "Big")
        self.assertEqual(off.clouds, newmap.CLOUDS_OFF)
        back, = newmap.parse(__import__("tomllib").loads(newmap.map_toml(spec)), "map.toml", "Big")
        self.assertEqual((back.size, back.clouds, back.room), (spec.size, spec.clouds, spec.room))

    def test_size_only_for_a_blank_map(self):
        with self.assertRaises(newmap.NewMapError):
            newmap.parse({"copy_of": "M04_Cotentin", "name": "Big", "size": [24, 16]}, "map.toml", "Big")
        with self.assertRaises(newmap.NewMapError):
            newmap.parse({**self.BASE, "size": [25, 16]}, "map.toml", "Big")
        with self.assertRaises(newmap.NewMapError):
            newmap.parse({**self.BASE, "room": "out"}, "map.toml", "Big")
        with self.assertRaises(newmap.NewMapError):
            newmap.parse({**self.BASE, "clouds": 10}, "map.toml", "Big")


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class MakeSectors(unittest.TestCase):
    def grid(self, w=24 * bigmap.CASE, h=16 * bigmap.CASE):
        return sectors.Grid.over(w, h, most=512)

    def test_the_row_reads_back_and_is_written(self):
        row = sectors.parse_paint({"file": "a.scenario", "auto": 5000, "seed": 3}, "here")
        self.assertEqual(row, sectors.SectorAuto("a.scenario", 5000 * 260.0, 3))
        toml = sectors.sectors_toml(sectors.Sectors(paints=(row,)))
        back = sectors.parse_sectors(__import__("tomllib").loads(toml)["sectors"])[0]
        self.assertEqual(back.paints, (row,))
        for bad in ({"file": "a.scenario", "auto": 10}, {"file": "a.scenario", "auto": 5000, "seed": -1},
                    {"file": "a", "auto": 5000}, {"file": "a.scenario", "auto": 5000, "sector": 2}):
            with self.assertRaises(sectors.SectorError):
                sectors.parse_paint(bad, "here")

    def test_every_place_in_a_sector_each_one_piece_the_same_every_time(self):
        g = self.grid()
        auto = sectors.SectorAuto("a.scenario", 5000 * 260.0)
        nx, ny = sectors.auto_layout(g.width, g.height, auto.size)
        lab = np.full((g.ny, g.nx), -1, np.int32)
        sectors.auto_cells(lab, auto, g, np)
        self.assertEqual(set(np.unique(lab).tolist()), set(range(nx * ny)))
        again = np.full((g.ny, g.nx), -1, np.int32)
        sectors.auto_cells(again, auto, g, np)
        self.assertTrue((lab == again).all())
        for k in range(nx * ny):   # each sector one piece (4-neighbour flood fill)
            cells = set(zip(*np.nonzero(lab == k)))
            first = next(iter(cells))
            seen, todo = {first}, [first]
            while todo:
                i, j = todo.pop()
                for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if n in cells and n not in seen:
                        seen.add(n)
                        todo.append(n)
            self.assertEqual(len(seen), len(cells), f"sector {k} is in pieces")

    def test_borders_wander(self):
        g = self.grid()
        lab = np.zeros((g.ny, g.nx), np.int32)
        sectors.auto_cells(lab, sectors.SectorAuto("a.scenario", 5000 * 260.0), g, np)
        changes = (np.diff(lab, axis=1) != 0).sum(axis=0)
        self.assertGreater(int((changes > 0).sum()), int(g.nx * 0.5))   # not a few straight lines

    def test_too_many_sectors_are_refused(self):
        g = sectors.Grid.over(128 * bigmap.CASE, 128 * bigmap.CASE, most=256)
        lab = np.zeros((g.ny, g.nx), np.int32)
        with self.assertRaises(sectors.SectorError):
            sectors.auto_cells(lab, sectors.SectorAuto("a.scenario", 1000 * 260.0), g, np)


if __name__ == "__main__":
    unittest.main()
