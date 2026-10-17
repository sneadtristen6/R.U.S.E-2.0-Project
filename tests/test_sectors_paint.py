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


def plain_parts(lab):
    """The plain code for cell_parts: a flood fill from each cell not yet in a piece, row by row (sides only)."""
    ny, nx = len(lab), len(lab[0])
    comp = [[-1] * nx for _ in range(ny)]
    label, size, edge = [], [], []
    for i in range(ny):
        for j in range(nx):
            if comp[i][j] >= 0:
                continue
            k = len(label)
            label.append(lab[i][j])
            size.append(0)
            edge.append(False)
            comp[i][j] = k
            todo = [(i, j)]
            while todo:
                a, b = todo.pop()
                size[k] += 1
                edge[k] = edge[k] or a in (0, ny - 1) or b in (0, nx - 1)
                for p, q in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if 0 <= p < ny and 0 <= q < nx and comp[p][q] < 0 and lab[p][q] == lab[a][b]:
                        comp[p][q] = k
                        todo.append((p, q))
    return comp, label, size, edge


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

    def at(self, lab, x, y):
        return int(lab[int(y // self.g.step), int(x // self.g.step)])

    def written(self, setting):
        """The build's result, checked to say what tidy_cells says (view == build) and every sector one piece."""
        lab = self.cells(setting)
        tidy, done, _pinched = S.tidy_cells(lab, np)
        res = S.over_painted(self.s, self.kdt, lab, self.g, None, seed="TestMap/a")
        self.assertEqual(res.labels.astype(np.int32).tobytes(), tidy.astype(np.int32).tobytes())
        self.assertEqual(res.tidied, done)
        parts = S.cell_parts(tidy, np)
        sectors = [n for n in parts.label.tolist() if n >= 0]
        self.assertEqual(len(sectors), len(set(sectors)))   # each sector one piece
        self.assertEqual(S.sector_shapes(tidy.copy(), self.g, np)[2], [])   # no hole, nothing the build refuses
        return tidy, done, res

    def test_a_stroke_through_a_sector_gives_its_small_piece_to_the_neighbour(self):
        # sector 2 (the file's 1) drawn across sector 1 (file 0) at y 70,000: 1's top 26,000 to its bottom 46,000
        cut = S.Sectors(paints=(square(1, 20000, 70000, 110000, 70000),))
        tidy, done, _res = self.written(cut)
        self.assertEqual((self.at(tidy, 70000, 50000), self.at(tidy, 70000, 100000)), (1, 0))
        self.assertEqual([(d["kind"], d["number"], d["to"], d["bits"]) for d in done], [("pieces", 0, 1, 1)])
        # two pieces of a sector touching nothing else: the smaller (a tie: the later) goes to no sector
        two = S.Sectors(no_sectors=(FILE,), paints=(square(3, 20000, 20000, 60000, 60000),
                                                    square(3, 120000, 120000, 160000, 160000)))
        tidy, done, _res = self.written(two)
        self.assertEqual((self.at(tidy, 40000, 40000), self.at(tidy, 140000, 140000)), (3, -1))
        self.assertEqual([(d["number"], d["to"]) for d in done], [(3, -1)])
        self.assertIn("went to no sector", S.tidy_text(done[0]))

    def test_a_blob_inside_a_sector_gets_a_thin_line_out(self):
        blob = S.Sectors(no_sectors=(FILE,), paints=(square(0, 20000, 20000, 160000, 160000),
                                                     square(1, 84000, 84000, 96000, 96000)))
        tidy, done, res = self.written(blob)
        [c] = done
        self.assertEqual((c["kind"], c["number"], c["around"]), ("corridor", 1, 0))
        self.assertEqual([z.number for z in res.zones], [0, 1])
        k = Kdt(res.kdt)
        self.assertEqual((level_at(k, 90000.0, 90000.0), level_at(k, 40000.0, 40000.0)), (1, 0))
        self.assertEqual(int((tidy == 1).sum()) - int((self.cells(blob) == 1).sum()), c["cells"])  # one cell wide
        self.assertIn("thin line of sector 2 cut through sector 1", S.tidy_text(c))

    def test_an_eraser_hole_and_two_holes_in_one_sector(self):
        hole = S.Sectors(no_sectors=(FILE,), paints=(square(0, 20000, 20000, 160000, 160000),
                                                     stroke(S.NO_SECTOR, [(80000.0, 80000.0)], 12000.0)))
        _tidy, done, res = self.written(hole)
        self.assertEqual([(c["kind"], c["number"], c["around"]) for c in done], [("corridor", -1, 0)])
        self.assertEqual([z.number for z in res.zones], [0])
        self.assertIsNone(level_at(Kdt(res.kdt), 80000.0, 80000.0))
        two = S.Sectors(no_sectors=(FILE,), paints=(square(0, 20000, 20000, 160000, 160000),
                                                    square(1, 50000, 84000, 62000, 96000),
                                                    stroke(S.NO_SECTOR, [(130000.0, 90000.0)], 9000.0)))
        _tidy, done, res = self.written(two)
        self.assertEqual(sorted((c["number"], c["around"]) for c in done), [(-1, 0), (1, 0)])
        self.assertEqual([z.number for z in res.zones], [0, 1])

    def test_a_cut_that_would_split_the_sector_is_passed_over(self):
        # sector 1 round a blob of 2, with a thin neck of 1 to the right: a (made-up) shortest cut across the neck
        # would leave 1 in two pieces, so the next one is taken
        g = self.g
        lab = np.full((g.ny, g.nx), -1, np.int32)
        lab[40:120, 40:120] = 0
        lab[70:90, 70:90] = 1
        lab[80:81, 120:200] = 0     # the neck, one cell thick
        lab[60:100, 200:240] = 0    # and what it leads to
        real = S._corridors
        bad = (1, (80, 80), (np.full(1, 80), np.arange(150, 151)))   # a cut across the neck, in the blob's sector

        def with_bad(*a, **kw):
            return [bad] + real(*a, **kw)
        from unittest import mock
        with mock.patch.object(S, "_corridors", with_bad):
            tidy, done, _p = S.tidy_cells(lab, np)
        [c] = done
        self.assertEqual((c["number"], c["around"]), (1, 0))
        self.assertEqual(int(tidy[80, 150]), 0)                    # the neck left alone
        self.assertEqual(int((S.cell_parts(tidy, np).label == 0).sum()), 1)

    def test_pieces_found_on_whole_arrays_match_a_flood_fill(self):
        rng = np.random.default_rng(7)
        for trial in range(6):
            lab = rng.integers(-1, 3, size=(23 + trial, 31)).astype(np.int32)
            lab[5:15, 5:20] = 1
            parts = S.cell_parts(lab, np)
            comp, label, size, edge = plain_parts(lab.tolist())
            self.assertEqual(parts.comp.astype(np.int64).tobytes(), np.array(comp, np.int64).tobytes())
            self.assertEqual((parts.label.tolist(), parts.size.tolist(), parts.edge.tolist()), (label, size, edge))

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
        # no sector yet, outlines asked for (Shapes): {} not None, which the page took for "not worked out" and asked
        # again, forever: on a blank map no box could be drawn (the owner, 2026-10-10)
        self.assertEqual(self.api.sector_view("Blitz", f, outlines=True)["outlines"], {})
        self.assertIsNone(self.api.sector_view("Blitz", f)["outlines"])
        v = self.api.sector_paint("Blitz", f, 0, 4000.0, [[x, 60000.0] for x in range(20000, 100001, 4000)],
                                  "square")
        self.assertEqual(([s["number"] for s in v["sectors"]], v["strokes"], v["next"]), ([0], 1, 1))
        v = self.api.sector_paint("Blitz", f, 5, 10000.0, [[150000.0, 150000.0]])
        self.assertEqual([s["number"] for s in v["sectors"]], [0, 5])
        self.assertEqual(set(self.cells(v)), {0, 1, 6})
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]
        self.assertEqual((data["no_sectors"], [p["sector"] for p in data["paint"]]), ([f], [0, 5]))
        # a second, smaller piece of sector 1 touching nothing: tidied to no sector, shown and said as the build does
        v = self.api.sector_paint("Blitz", f, 0, 8000.0, [[30000.0, 150000.0]])
        self.assertEqual(v["problems"], [])
        self.assertEqual([(t["kind"], t["number"], t["to"], t["bits"]) for t in v["tidied"]], [("pieces", 0, -1, 1)])
        self.assertEqual(set(self.cells(v)), {0, 1, 6})
        from rusemod.numpy2 import np as np_
        painted, g, (s, kdt_raw, _w, _h) = self.api._sector_cells("Blitz", f, self.api._sector_setting("Blitz"))
        built = S.over_painted(s, kdt_raw, painted, g, None, seed=f"Blitz/{f}")
        k = 1
        while max(g.nx, g.ny) > self.api.PREVIEW_CELLS * k:
            k *= 2
        shown = (built.labels[k // 2::k, k // 2::k].astype(np_.int32) + 1).ravel().tolist()
        self.assertEqual(self.cells(v), shown)                  # what's shown is what the build writes
        self.assertEqual(built.tidied, v["tidied"])
        scen = next(x for x in self.api.map_scenarios("Blitz")["scenarios"] if x["file"] == f)
        self.assertEqual(([z["number"] for z in scen["zones"]], scen.get("sectors_note")), ([0, 5], None))
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

    def test_make_sectors_over_what_was_painted_and_another_layout_in_its_place(self):
        """Make sectors (the owner, 2026-10-17: "more intricate sectors rather than just four big blobs"): the whole
        map cut up, kept over the strokes before it (Undo brings them back); Another layout takes its place."""
        f = "leveldesign.scenario"
        self.api.sector_paint("Blitz", f, 0, 4000.0, [[60000.0, 60000.0]])
        v = self.api.sector_auto("Blitz", f, 500)        # the made-up map is about 1,000 x 760 m: 2 x 2 sectors
        nx, ny = S.auto_layout(W, H, 500 * 260.0)
        self.assertEqual(([s["number"] for s in v["sectors"]], v["strokes"], v["auto"], v["problems"]),
                         (list(range(nx * ny)), 2, {"metres": 500, "seed": 0}, []))
        self.assertNotIn(0, self.cells(v))               # every place in a sector
        again = self.api.sector_auto("Blitz", f, 500, 1)
        self.assertEqual((again["strokes"], again["auto"]), (2, {"metres": 500, "seed": 1}))
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]["paint"]
        self.assertEqual([("auto" in p, p.get("seed")) for p in data], [(False, None), (True, 1)])
        v = self.api.sector_undo("Blitz", f)
        self.assertEqual((v["strokes"], v["auto"]), (1, None))
        self.assertEqual([s["number"] for s in v["sectors"]], [0, 1])   # the map's own two, with the stroke on them
        for bad in (10, 50000, "a lot"):
            with self.assertRaises(Exception, msg=str(bad)):
                self.api.sector_auto("Blitz", f, bad)

    def test_shapes_saved_together_and_taken_back_together(self):
        """A shape edit (the owner, 2026-10-09: sectors as shapes you drag): the sectors it changes saved in one go,
        the outlines with them, and Undo taking them all back."""
        f = "leveldesign.scenario"
        left = [[0.0, 0.0], [140000.5, 0.0], [140000.5, H], [0.0, H]]      # the shared border moved right
        right = [[140000.5, 0.0], [W, 0.0], [W, H], [140000.5, H]]
        v = self.api.sector_area("Blitz", f, [{"sector": 0, "points": left}, {"sector": 1, "points": right}])
        self.assertEqual((sorted(v["outlines"]), v["strokes"], v["problems"]), (["0", "1"], 2, []))
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]["paint"]
        self.assertEqual([(p["sector"], p["group"], len(p["area"])) for p in data], [(0, 1, 4), (1, 1, 4)])
        v = self.api.sector_area("Blitz", f, [{"sector": 1, "points": []}])   # taken out: its ground to sector 0
        self.assertEqual([s["number"] for s in v["sectors"]], [0])
        self.assertEqual(tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]["paint"][-1]["group"], 2)
        v = self.api.sector_undo("Blitz", f)
        self.assertEqual(([s["number"] for s in v["sectors"]], v["strokes"]), ([0, 1], 2))
        v = self.api.sector_undo("Blitz", f)                                   # both rows of the first edit
        self.assertEqual(v["strokes"], 0)
        before = {s["number"]: s["cells"] for s in v["sectors"]}
        v = self.api.sector_area("Blitz", f, [{"sector": -1, "points": left}])  # a No sector box (2026-10-10)
        self.assertLess({s["number"]: s["cells"] for s in v["sectors"]}.get(0, 0), before[0])
        self.assertEqual(tomllib.loads(self.file.read_text(encoding="utf-8"))["sectors"]["paint"][-1]["sector"], -1)
        self.api.sector_undo("Blitz", f)
        for bad in ([], [{"sector": 0, "points": [[1.0, 1.0], [2.0, 2.0]]}], [{"sector": -1, "points": []}]):
            with self.assertRaises(Exception, msg=str(bad)):
                self.api.sector_area("Blitz", f, bad)


def area(sector, points, group=1, file=FILE):
    return S.SectorArea(file, sector, tuple(points), group)


def plain_inside(pts, x, y) -> bool:
    """The plain even-odd test of one point."""
    inside = False
    for i in range(len(pts)):
        (xi, yi), (xj, yj) = pts[i], pts[i - 1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
    return inside


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class Areas(unittest.TestCase):
    """A sector's shape (SectorArea, the Studio's corners to drag): the cells it holds, the ground it gives up going
    to what touches it, a sector taken out, the rows read back, and the build writing them."""

    def test_an_areas_cells_are_where_the_plain_test_says_cell_for_cell(self):
        g = S.Grid.over(W, H, 128)
        star = [(30000.3, 20000.7), (120000.1, 41000.2), (200000.9, 15000.4), (180000.2, 120000.6), (240000.5, 190000.3),
                (100000.7, 150000.1), (60000.4, 185000.9), (90000.2, 100000.8), (10000.6, 90000.5)]
        i0, i1, mask = S.polygon_mask(star, g, np)
        got = np.zeros((g.ny, g.nx), bool)
        got[i0:i1 + 1] = mask
        plain = [[plain_inside(star, (j + 0.5) * g.step, (i + 0.5) * g.step) for j in range(g.nx)] for i in range(g.ny)]
        self.assertEqual(got.tobytes(), np.array(plain, bool).tobytes())
        self.assertGreater(int(got.sum()), 1000)

    def test_the_ground_a_sector_gives_up_goes_to_what_touches_it(self):
        g = S.Grid.over(W, H, 128)
        lab = np.full((g.ny, g.nx), 0, np.int32)
        lab[:, g.nx // 2:] = 1
        lab[:8] = S.NO_SECTOR                      # a strip of ground in no sector along the top
        before0 = int((lab == 0).sum())
        small = [(W * 0.75, H * 0.5), (W * 0.9, H * 0.5), (W * 0.9, H * 0.7), (W * 0.75, H * 0.7)]
        S.area_cells(lab, area(1, small), g, np)
        i0, i1, mask = S.polygon_mask(small, g, np)
        own = np.zeros_like(lab, bool)
        own[i0:i1 + 1] = mask
        self.assertTrue((lab[own] == 1).all() and not (lab[~own] == 1).any())   # sector 1: its new shape, no more
        self.assertFalse((lab == S.LEFT_OVER).any())
        # what it gave up: to sector 0 where that's nearer, to no sector near the strip; never back to sector 1
        self.assertGreater(int((lab == 0).sum()), before0 + 1000)
        freed_none = np.argwhere(lab[8:] == S.NO_SECTOR)   # (the ground sector 1 had: the right half)
        self.assertTrue(len(freed_none) and (freed_none[:, 1] >= g.nx // 2).all())
        self.assertEqual(int((lab[8:, :g.nx // 2] != 0).sum()), 0)              # sector 0's own ground untouched
        self.assertTrue((lab[:8] == S.NO_SECTOR).all())                         # the strip stays no sector
        S.area_cells(lab, area(1, ()), g, np)       # taken out
        self.assertEqual(set(np.unique(lab).tolist()), {S.NO_SECTOR, 0})

    def test_a_sector_taken_out_gives_all_its_ground_to_the_sectors_round_it(self):
        """The owner, 2026-10-10 (T43's Sector Gap Test: a fifth of the deleted sector went to no sector where the
        map's outside touched it): none goes to no sector, however near the outside it is; a sector only no sector
        touches is the one case it becomes no sector."""
        g = S.Grid.over(W, H, 128)
        lab = np.full((g.ny, g.nx), 0, np.int32)
        lab[:, g.nx // 2:] = 1
        lab[:8] = S.NO_SECTOR                                  # the map's outside, along the top and the right
        lab[:, -8:] = S.NO_SECTOR
        lab[20:30, 10:20] = S.NO_SECTOR                        # an island of sector 2 in no sector
        lab[22:28, 12:18] = 2
        had, none = lab == 1, lab == S.NO_SECTOR
        S.area_cells(lab, area(1, ()), g, np)
        self.assertTrue((lab[had] == 0).all())                 # every cell sector 1 had: to sector 0
        self.assertTrue((lab[none] == S.NO_SECTOR).all())      # the outside stays as it was
        S.area_cells(lab, area(2, ()), g, np)
        self.assertTrue((lab[22:28, 12:18] == S.NO_SECTOR).all())   # only no sector touched it

    def test_a_no_sector_box_takes_only_its_own_ground(self):
        g = S.Grid.over(W, H, 128)
        lab = np.full((g.ny, g.nx), 0, np.int32)
        lab[:, g.nx // 2:] = 1
        lab[:8] = S.NO_SECTOR
        before = lab.copy()
        box = [(W * 0.3, H * 0.4), (W * 0.7, H * 0.4), (W * 0.7, H * 0.6), (W * 0.3, H * 0.6)]
        S.area_cells(lab, area(S.NO_SECTOR, box), g, np)
        i0, i1, mask = S.polygon_mask(box, g, np)
        inside = np.zeros_like(lab, bool)
        inside[i0:i1 + 1] = mask
        self.assertTrue((lab[inside] == S.NO_SECTOR).all())         # across both sectors
        self.assertTrue((lab[~inside] == before[~inside]).all())    # nothing else moved, the outside neither
        self.assertGreater(int((before[inside] == 0).sum()), 100)
        self.assertGreater(int((before[inside] == 1).sum()), 100)

    def test_a_moved_corner_changes_only_the_ground_round_it(self):
        """within: a corner of the border between sectors 0 and 1 moved right; only the cells in its two triangles
        (before and after) change, every other cell stays as it was, even where the new outline (a straight line
        here) and the old cells (a step here) don't agree."""
        g = S.Grid.over(W, H, 128)
        lab = np.full((g.ny, g.nx), 0, np.int32)
        lab[:, g.nx // 2:] = 1
        lab[:g.ny // 4, g.nx // 2 - 3:g.nx // 2] = 1          # a step in the border the straight outline skips
        before = lab.copy()
        top, bottom, old, new = (W / 2, 0.0), (W / 2, H), (W / 2, H / 2), (W * 0.7, H / 2)
        fans = (top + old + bottom, top + new + bottom)
        fans = tuple(tuple(zip(f[0::2], f[1::2])) for f in fans)
        right = ((W / 2, 0.0), (W, 0.0), (W, H), (W / 2, H), new)   # sector 1's new outline (its corner moved in)
        S.area_cells(lab, S.SectorArea(FILE, 1, right, 1, fans), g, np)
        region = np.zeros(lab.shape, bool)
        for f in fans:
            i0, i1, m = S.polygon_mask(f, g, np)
            region[i0:i1 + 1] |= m
        self.assertTrue((lab[~region] == before[~region]).all())          # the step stays: nothing else moved
        self.assertGreater(int(((before == 1) & (lab == 0)).sum()), 100)  # the triangle it gave up: to sector 0

    def test_shape_rows_read_back_and_mistakes_are_refused(self):
        fans = (((1.5, 2.0), (3.0, 4.0), (5.0, 1.0)), ((1.5, 2.0), (3.5, 4.5), (5.0, 1.0)))
        setting = S.Sectors(paints=(area(0, [(1.5, 2.0), (3.0, 4.0), (5.0, 1.0)], 3), stroke(2, [(5.0, 6.0)]),
                                    area(4, (), 4), S.SectorArea(FILE, 5, ((0.0, 0.0), (9.0, 0.0), (9.0, 9.0)), 5, fans),
                                    area(S.NO_SECTOR, [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0)], 6)))
        self.assertEqual(S.parse_sectors(tomllib.loads(S.sectors_toml(setting))["sectors"]), [setting])
        good = {"file": "a.scenario", "sector": 0, "group": 1, "area": [[1, 2], [3, 4], [5, 1]]}
        S.parse_sectors({"paint": [good]})
        for bad in ({"sector": -2}, {"sector": -1, "area": []}, {"sector": 255}, {"group": -1}, {"group": True}, {"area": [[1, 2], [3, 4]]},
                    {"area": [[1, "a"], [3, 4], [5, 1]]}, {"radius": 5.0}, {"file": "a.toml"},
                    {"within": [[[1, 2], [3, 4]]]}, {"within": [[1, 2], [3, 4], [5, 1]]}):
            with self.assertRaises(S.SectorError, msg=str(bad)):
                S.parse_sectors({"paint": [{**good, **bad}]})

    def test_shapes_are_written_as_zones(self):
        s, kdt = made_up()
        g = S.Grid.over(W, H, 512)
        setting = S.Sectors(no_sectors=(FILE,), paints=(
            area(0, [(20000.5, 20000.5), (130000.5, 20000.5), (130000.5, 170000.5), (20000.5, 170000.5)]),
            area(1, [(130000.5, 20000.5), (240000.5, 20000.5), (240000.5, 170000.5), (130000.5, 170000.5)]),
            area(3, [(60000.5, 60000.5), (90000.5, 60000.5), (90000.5, 100000.5), (60000.5, 100000.5)], 2)))
        start = S.start_cells(s, kdt, g, setting, FILE, np)
        lab = S.painted_cells(start, setting.paints_of(FILE), g, np)
        res = S.over_painted(s, kdt, lab, g, lambda x, y: 50.0, seed="TestMap/a")
        self.assertEqual([z.number for z in res.zones], [0, 1, 3])
        self.assertEqual([t["kind"] for t in res.tidied], ["corridor"])   # 3 inside 0: a thin line out


if __name__ == "__main__":
    unittest.main()
