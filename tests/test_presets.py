"""Blank maps to start from (rusemod.presets, the Studio's Duplicate map: Blank Terrain and Blank Ocean): the files a
preset writes read back as the build reads them, act at full strength over the whole map, and keep only the
starting points."""
import tempfile
import unittest
from pathlib import Path

from rusemod import presets
from rusemod.presets import Facts, PresetError, preset_files, strokes

FACTS = Facts((0.0, 0.0, 400000.0, 200000.0), 12623.0, 19233.0, "leveldesign_3v3_v01.scenario",
              [(0, "LabelVille"), (1, "Spawn"), (2, "StartingPoint"), (3, "Spawn"), (4, "StartingPoint")],
              ["Batiment3F_1ET_Colombages_Cordonnerie"])
CORNERS = [(0.0, 0.0), (400000.0, 0.0), (0.0, 200000.0), (400000.0, 200000.0), (200000.0, 100000.0)]


class Files(unittest.TestCase):
    def mod(self, kind: str):
        """A mod holding the preset's files for new map BlankMap, read as the build reads it."""
        from rusemod.build import load_mod
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "m"
        (root / "maps" / "BlankMap").mkdir(parents=True)
        (root / "mod.toml").write_text('[mod]\nid = "m"\nname = "m"\nversion = "1.0.0"\n', encoding="utf-8")
        for name, text in preset_files(kind, FACTS).items():
            (root / "maps" / "BlankMap" / name).write_text(text, encoding="utf-8")
        return load_mod(root)[0]

    def test_the_files_read_back_as_the_build_reads_them(self):
        from rusemod.roadnet import TakeOut, take_out_of
        from rusemod.scenario import Remove
        from rusemod.scenery import ERASE_GROUPS
        from rusemod.sectors import whole_map_of
        for kind in presets.KINDS:
            info = self.mod(kind)
            got = info.terrain["BlankMap"] + info.paint["BlankMap"]
            self.assertEqual(got, strokes(kind, FACTS), kind)
            rows = info.scenario["BlankMap"]
            self.assertEqual([(r.file, r.item, r.kind) for r in rows if isinstance(r, Remove)],
                             [(FACTS.scenario, 0, "LabelVille"), (FACTS.scenario, 1, "Spawn"),
                              (FACTS.scenario, 3, "Spawn")])   # the starting points stay
            self.assertTrue(whole_map_of(rows))
            self.assertEqual(take_out_of(info.take_out["BlankMap"]), TakeOut(True, True))
            [area] = info.erase["BlankMap"]
            self.assertEqual((set(area.what), area.types), (set(ERASE_GROUPS), tuple(FACTS.untyped)))
            self.assertTrue(all(area.footprint().inside(x, y) for x, y in CORNERS))

    def test_every_stroke_at_full_strength_over_the_whole_map(self):
        for kind in presets.KINDS:
            for s in strokes(kind, FACTS):
                self.assertEqual([s.strength_at(x, y) for x, y in CORNERS], [1.0] * len(CORNERS), (kind, s.brush))
                self.assertTrue(all(s.covers(x, y) for x, y in CORNERS))

    def test_its_own_menu_pictures(self):
        """The big one ours (the open sea, or grass to the horizon, framed like the game's own), the wide one the map
        as a slab with no dots: the build draws the starting points on it wherever they are (start_dots)."""
        from rusemod.menudraw import slab_png
        from rusemod.png import read_png
        for kind in presets.KINDS:
            pics = presets.preset_pictures(kind)
            self.assertEqual(set(pics), {presets.PICTURE, presets.WIDE_PICTURE})
            w, h, big = read_png(pics[presets.PICTURE])
            self.assertEqual((w, h), (640, 360))
            self.assertEqual(tuple(big[:3]), (132, 134, 132))      # the game's own grey frame
            self.assertEqual(pics[presets.WIDE_PICTURE], slab_png("ocean" if kind == "blank_ocean" else "land"))
        with self.assertRaises(PresetError):
            presets.preset_pictures("blank_moon")

    def test_the_ocean_is_the_maps_own_sea_over_flat_ground(self):
        level, water, paint = strokes("blank_ocean", FACTS)
        self.assertEqual((level.brush, level.level, level.weight), ("level", 12623.0 - presets.OCEAN_DEPTH, 1.0))
        self.assertEqual((water.brush, water.level, water.block), ("water", 12623.0, False))  # units go under it
        self.assertEqual((paint.brush, paint.colour, paint.weight), ("paint", presets.OCEAN_COLOUR, 1.0))

    def test_the_terrain_is_dry_land(self):
        level, drain, paint = strokes("blank_terrain", FACTS)
        self.assertEqual((level.level, drain.brush, paint.colour), (19233.0, "drain", presets.TERRAIN_COLOUR))
        under = Facts(FACTS.bounds, 12623.0, 9000.0, FACTS.scenario, [], [])   # a map mostly under its sea
        self.assertEqual(strokes("blank_terrain", under)[0].level, 12623.0 + presets.LAND_OVER_SEA)

    def test_an_unknown_preset_is_refused(self):
        with self.assertRaises(PresetError):
            preset_files("blank_moon", FACTS)


class FromTheMapsOwnFiles(unittest.TestCase):
    def test_the_facts(self):
        from test_scenario import scenario
        from test_scenery import NAMES, village
        from test_terrain_edit import make_map
        from rusemod.scenario import Scenario
        from rusemod.terrain_edit import FILES
        from rusemod.tms import Tms
        files = make_map()
        f = presets.facts_of(files[FILES["highdef"]], village(), "x.scenario", scenario(), {NAMES[0]: object()})
        hd = Tms(files[FILES["highdef"]])
        zs = sorted(hd.to_world(2, p[2]) for c in hd.cells for p in c.positions())
        self.assertEqual(f.bounds, (hd.bounds[0], hd.bounds[1], hd.bounds[3], hd.bounds[4]))
        self.assertEqual((f.sea, f.middle), (hd.to_world(2, hd.base_water()), zs[len(zs) // 2]))
        self.assertEqual(f.items, [(i, it.kind) for i, it in enumerate(Scenario.read(scenario()).items)])
        self.assertEqual((f.scenario, f.untyped), ("x.scenario", [NAMES[1]]))  # the type the game gives no kind


if __name__ == "__main__":
    unittest.main()
