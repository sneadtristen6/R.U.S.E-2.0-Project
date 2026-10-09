"""Painted sectors (rusemod.sectors: the Studio's Sectors brush, scenario.toml [[sectors.paint]] and no_sectors) on the
made-up map of test_sectors (no game files). Checked: the strokes land on the cells Footprint.inside says (whole
arrays against the plain code, cell for cell), the setting reads back, painted sectors are written as the scenario's
zones and zone map, and the two checks: a scenario with no sector at all, a sector in pieces or with a hole."""
import struct
import tomllib
import unittest

from test_sectors import H, W, level_at, made_up
from rusemod import sectors as S
from rusemod.kdt import Kdt
from rusemod.scenario import Scenario

try:
    from rusemod.numpy2 import np
except ImportError:  # the module needs numpy, as the apps have it
    np = None

FILE = "a.scenario"


def stroke(sector, points, radius=20000.0, shape="round", dx=1.0, dy=0.0, file=FILE):
    return S.SectorPaint(file, sector, radius, tuple(points), shape, dx, dy)


def square(sector, x0, y0, x1, y1, file=FILE):
    """A filled box painted with square dabs (sides along the map) of 4,000 half-side, every 4,000."""
    pts = [(x, y) for x in range(int(x0), int(x1) + 1, 4000) for y in range(int(y0), int(y1) + 1, 4000)]
    return stroke(sector, pts, 4000.0, "square", file=file)


def plain_paint(lab, p, g):
    """The plain code: every cell's middle tested with Footprint.inside."""
    for fp in p.footprints():
        for i in range(g.ny):
            for j in range(g.nx):
                if fp.inside((j + 0.5) * g.step, (i + 0.5) * g.step):
                    lab[i][j] = p.sector


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class Cells(unittest.TestCase):
    def test_strokes_land_where_the_plain_code_says_cell_for_cell(self):
        g = S.Grid.over(W, H, 128)
        strokes = [stroke(2, [(30000.5, 40000.25), (61000.0, 52000.0)], 17333.0),
                   stroke(5, [(130000.0, 90000.0)], 25000.0, "square", 0.6, 0.8),
                   stroke(S.NO_SECTOR, [(40000.0, 45000.0)], 9000.0),
                   stroke(7, [(0.0, 0.0), (W, H)], 12000.0, "square")]
        start = np.full((g.ny, g.nx), S.NO_SECTOR, np.int32)
        start[10:20, 10:40] = 1
        got = S.painted_cells(start, strokes, g, np)
        plain = start.tolist()
        for p in strokes:
            plain_paint(plain, p, g)
        self.assertEqual(got.tobytes(), np.array(plain, np.int32).tobytes())
        self.assertEqual(start[0, 0], S.NO_SECTOR)  # the start is left as it was
        self.assertEqual(set(np.unique(got).tolist()), {-1, 1, 2, 5, 7})


class Setting(unittest.TestCase):
    def test_paints_and_no_sectors_read_back(self):
        setting = S.Sectors(True, ("A.scenario",), (stroke(0, [(1.5, 2.0), (3.0, 4.0)]),
                                                     stroke(-1, [(5.0, 6.0)], 7.0, "square", 0.0, 1.0, "b.scenario")))
        text = S.sectors_toml(setting)
        self.assertEqual(S.parse_sectors(tomllib.loads(text)["sectors"]), [setting])
        self.assertTrue(setting.painted("a.scenario") and setting.painted("B.scenario"))
        self.assertFalse(setting.painted("c.scenario"))
        self.assertEqual(len(setting.paints_of("A.SCENARIO")), 1)
        only = S.Sectors(no_sectors=("x.scenario",))
        self.assertEqual(S.parse_sectors(tomllib.loads(S.sectors_toml(only))["sectors"]), [only])
        self.assertFalse(S.Sectors().active)
        self.assertEqual(S.sectors_toml(S.Sectors()), "")

    def test_mistakes_are_refused(self):
        good = {"file": "a.scenario", "sector": 0, "radius": 5.0, "points": [[1, 2]]}
        S.parse_sectors({"paint": [good]})
        for bad in ({"sector": 255}, {"sector": -2}, {"sector": True}, {"sector": 1.5}, {"radius": 0},
                    {"points": []}, {"points": [[1]]}, {"points": [["a", 2]]}, {"shape": "line"},
                    {"file": "a.toml"}, {"file": "x/a.scenario"}, {"extra": 1}, {"dx": "1"}):
            with self.assertRaises(S.SectorError, msg=str(bad)):
                S.parse_sectors({"paint": [{**good, **bad}]})
        with self.assertRaises(S.SectorError):
            S.parse_sectors({"no_sectors": "a.scenario"})


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class Painted(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s, cls.kdt = made_up()   # sectors 0 (left square) and 1 (right square)
        cls.g = S.Grid.over(W, H, 512)

    def cells(self, setting, file=FILE):
        start = S.start_cells(self.s, self.kdt, self.g, setting, file, np)
        return S.painted_cells(start, setting.paints_of(file), self.g, np)

    def test_painted_from_none_are_written_as_zones_and_zone_map(self):
        setting = S.Sectors(no_sectors=(FILE,), paints=(square(0, 20000, 20000, 100000, 100000),
                                                        square(4, 100000, 20000, 180000, 100000)))
        res = S.over_painted(self.s, self.kdt, self.cells(setting), self.g, lambda x, y: 50.0, seed="TestMap/a")
        self.assertEqual([z.number for z in res.zones], [0, 4])
        z0, z4 = res.zones
        self.assertEqual(z0.name, self.s.zones[0].name)               # a number the scenario has keeps its name
        self.assertEqual(z4.name, S.new_zone_name("testmap/A", 4))     # a new one: the same on every PC
        self.assertRegex(z4.name, r"^zone_[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$")
        self.assertEqual((z0.outline, z4.outline), ([4], [0]))
        self.assertEqual(z4.vertices[0][3], self.s.zones[0].vertices[0][3])   # the scenario's 4th value
        for z in res.zones:
            self.assertEqual(level_at(Kdt(res.kdt), z.anchor[0], z.anchor[1]), z.number)  # its label inside it
        k = Kdt(res.kdt)
        self.assertEqual(level_at(k, 60000.0, 60000.0), 0)
        self.assertEqual(level_at(k, 140000.0, 60000.0), 4)
        self.assertIsNone(level_at(k, 60000.0, 160000.0))              # ground left in no sector stays in none
        self.assertTrue(any("new sector(s) 5" in n and "not tried" in n for n in res.notes))
        self.assertTrue(any("gaps" in n for n in res.notes))
        back = Scenario.read(Scenario(9, res.zones, []).to_bytes())
        self.assertEqual([z.name for z in back.zones], [z0.name, z4.name])

    def test_paint_over_the_maps_own_sectors(self):
        # sector 2 (the file's 1) erased, and sector 1 grown down into the ground below both
        setting = S.Sectors(paints=(stroke(S.NO_SECTOR, [(150000.0, 80000.0)], 60000.0, "square"),
                                    square(0, 40000, 124000, 100000, 160000)))
        res = S.over_painted(self.s, self.kdt, self.cells(setting), self.g, None, seed="TestMap/a")
        [z] = res.zones
        self.assertEqual((z.number, z.name, z.outline), (0, self.s.zones[0].name, []))
        self.assertEqual(z.anchor[:2], self.s.zones[0].anchor[:2])     # its label still inside: kept
        self.assertEqual(level_at(Kdt(res.kdt), 70000.0, 150000.0), 0)

    def test_no_sector_at_all_stops(self):
        with self.assertRaises(S.PaintError) as caught:
            S.over_painted(self.s, self.kdt, self.cells(S.Sectors(no_sectors=(FILE,))), self.g)
        self.assertIn("paint at least one sector", str(caught.exception))
        self.assertIn("never been tried in the game", str(caught.exception))

    def test_a_sector_in_two_pieces_or_with_a_hole_is_named(self):
        two = S.Sectors(no_sectors=(FILE,), paints=(square(3, 20000, 20000, 60000, 60000),
                                                    square(3, 120000, 120000, 160000, 160000)))
        with self.assertRaises(S.PaintError) as caught:
            S.over_painted(self.s, self.kdt, self.cells(two), self.g)
        self.assertEqual(caught.exception.problems, [{"number": 3, "pieces": 2, "holes": 0, "inside": []}])
        self.assertIn("sector 4 is in 2 pieces", str(caught.exception))
        ring = S.Sectors(no_sectors=(FILE,), paints=(square(0, 20000, 20000, 140000, 140000),
                                                     stroke(S.NO_SECTOR, [(80000.0, 80000.0)], 20000.0)))
        with self.assertRaises(S.PaintError) as caught:
            S.over_painted(self.s, self.kdt, self.cells(ring), self.g)
        self.assertEqual(caught.exception.problems, [{"number": 0, "pieces": 1, "holes": 1, "inside": [-1]}])
        self.assertIn("ground in no sector inside it", str(caught.exception))

    def test_a_label_lands_inside_a_c_shape(self):
        g = S.Grid.over(W, H, 256)
        lab = np.full((g.ny, g.nx), -1, np.int32)
        lab[20:120, 20:60] = 2
        lab[20:40, 60:200] = 2
        lab[100:120, 60:200] = 2
        x, y = S.label_point(lab, 2, g, np)
        self.assertEqual(lab[int(y // g.step), int(x // g.step)], 2)


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class Apply(unittest.TestCase):
    def pack(self):
        from rusemod.cover import member as movement_member
        from rusemod.scenario import folder_of
        s, kdt = made_up()
        folder = folder_of("TestMap")
        win = b"INFOIA\r\n" + bytes(32) + struct.pack("<2f", W, H) + bytes(16)
        return folder, {movement_member("TestMap"): win, folder + "a.scenario": s.to_bytes(),
                        folder + "zonebluff\\a.kdt": kdt, folder + "b.scenario": s.to_bytes(),
                        folder + "zonebluff\\b.kdt": kdt}

    def test_only_the_painted_scenario_changes(self):
        folder, pack = self.pack()
        setting = S.Sectors(no_sectors=("A.scenario",), paints=(square(1, 20000, 20000, 100000, 100000),))
        out, notes = S.apply_sectors(pack.get, "TestMap", ["a.scenario", "b.scenario"], None, most=512,
                                     setting=setting)
        self.assertEqual(sorted(out), sorted([folder + "a.scenario", folder + "zonebluff\\a.kdt"]))
        self.assertEqual([z.number for z in Scenario.read(out[folder + "a.scenario"]).zones], [1])
        self.assertTrue(any("painted" in n for n in notes))

    def test_an_empty_scenario_stops_the_build(self):
        _folder, pack = self.pack()
        setting = S.Sectors(no_sectors=("b.scenario",), paints=(square(0, 20000, 20000, 100000, 100000),))
        with self.assertRaises(S.PaintError) as caught:
            S.apply_sectors(pack.get, "TestMap", ["a.scenario", "b.scenario"], None, most=512, setting=setting)
        self.assertIn("TestMap: b.scenario: it has no sector at all", str(caught.exception))


def _with_mod():
    from test_studio import WithMod
    return WithMod


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class StudioBrush(_with_mod()):
    """The Studio's Sectors brush calls: strokes kept in the mod's scenario.toml, taken back, cleared, a start from
    no sectors, and the view the map shows (cells run by run, the checks, the outlines when asked)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_scenario import scenario
        from test_studio import make_edat
        zoned, kdt = made_up()
        s = Scenario.read(scenario())
        s.zones = zoned.zones
        win = b"INFOIA\r\n" + bytes(32) + struct.pack("<2f", W, H) + bytes(16)
        (cls.game / "Data" / "PC" / "190852" / "DataMap_Win.dat").write_bytes(make_edat([
            ("dir", "test\\map\\blitz\\", [("file", "leveldesign.scenario", s.to_bytes()),
                                           ("dir", "zonebluff\\", [("file", "leveldesign.kdt", kdt)])]),
            ("dir", "datasmap\\blitz\\", [("file", "mapinfo.win", win)])]))

    def setUp(self):
        from pathlib import Path
        from unittest import mock
        super().setUp()
        menus = mock.patch("rusemod.scenario.kinds_of", return_value={})
        menus.start()
        self.addCleanup(menus.stop)
        self.mod = Path(self.api.new_mod("Sectors")["current"])
        self.file = self.mod / "maps" / "Blitz" / "scenario.toml"

    def cells(self, view):
        out = []
        for v, n in zip(view["runs"][0::2], view["runs"][1::2]):
            out += [v] * n
        self.assertEqual(len(out), view["nx"] * view["ny"])
        return out

    def test_paint_take_back_clear_and_start_from_none(self):
        f = "leveldesign.scenario"
        v = self.api.sector_view("Blitz", f)
        self.assertEqual([s["number"] for s in v["sectors"]], [0, 1])
        self.assertEqual((v["empty"], v["problems"], v["next"], v["strokes"]), (False, [], 2, 0))
        v = self.api.sector_start("Blitz", f, True)
        self.assertEqual((v["empty"], v["starts_empty"], v["next"]), (True, True, 0))
        self.assertEqual(set(self.cells(v)), {0})
        v = self.api.sector_paint("Blitz", f, 0, 4000.0, [[x, 60000.0] for x in range(20000, 100001, 4000)],
                                  "square")
        self.assertEqual(([s["number"] for s in v["sectors"]], v["strokes"], v["next"]), ([0], 1, 1))
        v = self.api.sector_paint("Blitz", f, 5, 10000.0, [[150000.0, 150000.0]])
        self.assertEqual([s["number"] for s in v["sectors"]], [0, 5])
        self.assertEqual(set(self.cells(v)), {0, 1, 6})
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]
        self.assertEqual((data["no_sectors"], [p["sector"] for p in data["paint"]]), ([f], [0, 5]))
        # a second piece of sector 1: named, with what the build says
        v = self.api.sector_paint("Blitz", f, 0, 8000.0, [[30000.0, 150000.0]])
        self.assertEqual(v["problems"], [{"number": 0, "pieces": 2, "holes": 0, "inside": []}])
        scen = next(x for x in self.api.map_scenarios("Blitz")["scenarios"] if x["file"] == f)
        self.assertIn("sector 1 is in 2 pieces", scen["sectors_note"])
        v = self.api.sector_undo("Blitz", f)
        self.assertEqual((v["problems"], v["strokes"]), ([], 2))
        v = self.api.sector_view("Blitz", f, outlines=True)
        self.assertEqual(sorted(v["outlines"]), ["0", "5"])
        scen = next(x for x in self.api.map_scenarios("Blitz")["scenarios"] if x["file"] == f)
        self.assertEqual(([z["number"] for z in scen["zones"]], scen.get("sectors_note")), ([0, 5], None))
        v = self.api.sector_clear("Blitz", f)
        self.assertEqual((v["strokes"], v["empty"]), (0, True))
        v = self.api.sector_start("Blitz", f, False)
        self.assertEqual([s["number"] for s in v["sectors"]], [0, 1])
        self.assertFalse(self.file.exists())   # nothing left: no file
        self.api.scenario_sectors("Blitz", True)    # the whole-map switch keeps the strokes
        self.api.sector_paint("Blitz", f, 1, 5000.0, [[60000.0, 60000.0]])
        self.api.scenario_sectors("Blitz", False)
        self.assertEqual(len(tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]["paint"]), 1)
        with self.assertRaises(Exception):
            self.api.sector_paint("Blitz", f, 300, 5000.0, [[1.0, 1.0]])


if __name__ == "__main__":
    unittest.main()
