"""Building mods into a pack, and `ruse build`, on a made-up game (no game files needed)."""
import contextlib
import io
import os
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat, Ndf, loc
from rusemod.dic import Dic, name_to_key
from rusemod.build import BuildError, build_and_write, build_pack, load_mod
from rusemod.brush import Stroke
from rusemod.cli import main
from rusemod.lock import fingerprint_text

UNITS = "genglad\\patchable\\gfx\\everything.cpp.gladndfbin"


def ints(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(val(0x02, struct.pack("<i", v)) for v in values))


NDF = make_ndf(objects=[(0, [(0, ints([105] * 5))])], classes=["TBatimentDescriptor"], props=[("ProductionPrice", 0)],
               exports={0: "B"}, compress=True)
PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", NDF)]),
                  ("file", "readme.txt", b"untouched")])


def write_mod(root, mod_id, files, extra=""):
    folder = Path(root, mod_id)
    folder.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (folder / "src" / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / "src" / rel).write_text(text, encoding="utf-8")
    (folder / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nversion = "1.0.0"\n{extra}', encoding="utf-8")
    return folder


def price(pack_bytes):
    arc = Edat(pack_bytes)
    return Ndf(arc.read(arc.find("everything.cpp.gladndfbin"))).objects[0].get(0).int_list()


class LoadingMods(unittest.TestCase):
    def test_a_mod_folder(self):
        with tempfile.TemporaryDirectory() as d:
            folder = write_mod(d, "econ", {"b.rndf": "patch $/B ( ProductionPrice += 1 )",
                                           "a/x.rndf": "when mod better-ai ( patch $/B ( ProductionPrice *= 2 ) )"},
                               extra='[dependencies]\ncore = "^1.0"\n[load]\nafter = ["z"]\n')
            info, ops = load_mod(folder)
            self.assertEqual((info.id, info.version, info.depends, info.after), ("econ", "1.0.0", {"core": "^1.0"}, ["z"]))
            self.assertEqual([o.file for o in ops], ["src/a/x.rndf", "src/b.rndf"])  # files in path order
            self.assertEqual(info.when_mods, {"better-ai"})

    def test_a_single_rndf_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d, "My Tweak.rndf")
            f.write_text("patch $/B ( ProductionPrice += 1 )", encoding="utf-8")
            info, ops = load_mod(f)
            self.assertEqual((info.id, len(ops)), ("my-tweak", 1))

    def test_bad_mods_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BuildError, "no mod.toml"):
                load_mod(d)
            folder = write_mod(d, "Bad_ID", {})
            with self.assertRaisesRegex(BuildError, "lowercase"):
                load_mod(folder)


class BuildingAPack(unittest.TestCase):
    def mods(self, d):
        return [load_mod(write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})),
                load_mod(write_mod(d, "hardcore", {"hard.rndf": "patch $/B ( ProductionPrice += 5 )"}))]

    def test_worked_example_in_a_real_pack(self):
        with tempfile.TemporaryDirectory() as d:
            arc = Edat(PACK)
            result = build_pack(arc, self.mods(d), build_id="24687178")
            self.assertEqual((result.order, result.errors), (["econ-half", "hardcore"], []))
            new = arc.to_bytes(result.changed)
            self.assertEqual(price(new), [58] * 5)
            self.assertEqual(Edat(new).read(Edat(new).find("readme.txt")), b"untouched")
            self.assertEqual(len(result.fingerprint), 32)

    def test_errors_mean_nothing_to_write(self):
        with tempfile.TemporaryDirectory() as d:
            bad = load_mod(write_mod(d, "bad", {"x.rndf": "patch $/Nope ( P = 1 )"}))
            result = build_pack(Edat(PACK), [bad])
            self.assertTrue(result.errors)
            self.assertEqual(result.changed, {})


class DebugInfoShadows(unittest.TestCase):
    def test_debuginfo_copies_are_left_as_shipped(self):
        pack = make_edat([("dir", "genglad\\patchable\\gfx\\", [
            ("file", "everything.cpp.gladndfbin", NDF),
            ("file", "everything_debuginfo.cpp.gladndfbin", NDF)])])  # repeats every name of the main file
        with tempfile.TemporaryDirectory() as d:
            mod = load_mod(write_mod(d, "half", {"p.rndf": "patch every TBatimentDescriptor ( ProductionPrice *= 0.5 )"}))
            result = build_pack(Edat(pack), [mod])
        self.assertEqual(result.errors, [])
        self.assertEqual(list(result.changed), ["genglad\\patchable\\gfx\\everything.cpp.gladndfbin"])
        self.assertEqual([f.message for f in result.findings],
                         ["left 1 debug-info copies as shipped (everything_debuginfo.cpp.gladndfbin)"])


class Report(unittest.TestCase):
    def test_similar_notes_collapse(self):
        from rusemod.cli import report_lines
        from rusemod.patch import Finding
        notes = [Finding("note", f"m (p.rndf:4): $/GFX/Everything/B{i} has no ProductionPrice; skipped") for i in range(10)]
        lines = report_lines([Finding("error", "boom")] + notes)
        self.assertEqual(lines[0], "  error    boom")
        self.assertEqual(len(lines), 5)
        self.assertIn("… and 7 more like this", lines[-1])
        self.assertEqual(len(report_lines(notes, show_all=True)), 10)


class BuildCommand(unittest.TestCase):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(argv))
        return code, out.getvalue()

    def test_build_to_a_file_and_to_a_modded_copy(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d, "steamapps", "common", "R.U.S.E")
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "RUSE.exe").write_bytes(b"MZ")
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            Path(d, "steamapps", "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            mod = write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})

            code, out = self.run_cli("--game", str(game), "build", str(mod), "--out", str(Path(d, "out.dat")))
            self.assertEqual(code, 0, out)
            self.assertIn("load order: econ-half", out)
            self.assertIn("fingerprint: ", out)
            self.assertEqual(price(Path(d, "out.dat").read_bytes()), [53] * 5)  # 105 x 0.5 = 52.5 -> 53

            copy = Path(d, "RUSE-Instances", "econ")
            code, out = self.run_cli("--game", str(game), "build", str(mod), "--instance", str(copy))
            self.assertEqual(code, 0, out)
            self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
            self.assertEqual((copy / "steam_appid.txt").read_text(), "21970")
            self.assertEqual(price(PACK), [105] * 5)  # the made-up "Steam install" pack is untouched
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes(), PACK)

    def test_build_refuses_when_mods_have_errors(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d, "R.U.S.E")
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            mod = write_mod(d, "bad", {"x.rndf": "patch $/Nope ( P = 1 )"})
            code, out = self.run_cli("--game", str(game), "build", str(mod), "--out", str(Path(d, "out.dat")))
            self.assertEqual(code, 2)
            self.assertIn("Nothing was written.", out)
            self.assertFalse(Path(d, "out.dat").exists())


SHERMAN_KEY = name_to_key("SHERMAN")
UNIT_NDF = make_ndf(objects=[(0, [(0, val(0x02, struct.pack("<i", 187))), (1, val(0x1D, struct.pack("<Q", SHERMAN_KEY)))])],
                    classes=["TUniteAuSolDescriptor"], props=[("DescriptorId", 0), ("NameInMenuToken", 0)],
                    exports={0: "Sherman"}, topo=[0])
UNIT_PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", UNIT_NDF)])])
TEXT_PACK = make_edat([("dir", "genlocalisation\\ww2\\localisation\\", [
    ("dir", "translations\\", [("dir", f"{lang}\\", [("file", "baseunite.dic", make_dic([(SHERMAN_KEY, f"Sherman {lang}")]))])
                               for lang in ("us", "fr")]),
    ("dir", "dev\\", [("file", "baseunite.dic", make_dic([(SHERMAN_KEY, "Sherman dev")]))])]),
    ("file", "other.bin", b"untouched")])
NAMED = {"units.rndf": "export Test is clone $/Sherman ( NameInMenuToken = loc('c6.test.name') )"}
NAMES = "key,us,fr\nc6.test.name,Test Sherman,Sherman d'essai\n"


def text_of(pack, lang, key):
    arc = Edat(pack)
    return Dic(arc.read(arc.find(loc.member("baseunite", lang)))).text(key)


class Texts(unittest.TestCase):
    def mod(self, d, names=NAMES, prefix='text_prefix = "C6"\n'):
        folder = write_mod(d, "named", NAMED, extra=prefix)
        (folder / "text").mkdir()
        (folder / "text" / "baseunite.csv").write_text(names, encoding="utf-8")
        return load_mod(folder)

    def test_a_new_unit_gets_its_own_name(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d)
            self.assertEqual((mod[0].text_prefix, [r.key for r in mod[0].texts]), ("C6", ["c6.test.name"]))
            result = build_pack(Edat(UNIT_PACK), [mod], text_arc=Edat(TEXT_PACK))
        self.assertEqual(result.errors, [])
        new_key = name_to_key("C6000001")
        ndf = Ndf(result.changed[UNITS])
        self.assertEqual(struct.unpack("<Q", ndf.objects[1].get(1).payload)[0], new_key)  # the clone points at it
        self.assertEqual(struct.unpack("<Q", ndf.objects[0].get(1).payload)[0], SHERMAN_KEY)  # the Sherman doesn't
        rebuilt = Edat(TEXT_PACK).to_bytes(result.text_changed)
        self.assertEqual(text_of(rebuilt, "us", new_key), "Test Sherman")
        self.assertEqual(text_of(rebuilt, "fr", new_key), "Sherman d'essai")
        self.assertEqual(text_of(rebuilt, "dev", new_key), "Test Sherman")
        self.assertEqual(text_of(rebuilt, "us", SHERMAN_KEY), "Sherman us")
        self.assertTrue(any("isn't in the ger" in f.message for f in result.findings))  # the made-up game has 2 languages

    def test_a_text_file_can_carry_a_prefix_before_its_dictionary(self):  # text/studio.baseunite.csv: the Studio's names
        with tempfile.TemporaryDirectory() as d:
            folder = write_mod(d, "named", NAMED, extra='text_prefix = "C6"\n')
            (folder / "text").mkdir()
            (folder / "text" / "mine.baseunite.csv").write_text(NAMES, encoding="utf-8")
            info, _ops = load_mod(folder)
            self.assertEqual([(r.dictionary, r.file) for r in info.texts], [("baseunite", "text/mine.baseunite.csv")])

    def test_mistakes(self):
        with tempfile.TemporaryDirectory() as d:
            result = build_pack(Edat(UNIT_PACK), [self.mod(d)])
            self.assertIn("it wasn't given", result.errors[0].message)
        with tempfile.TemporaryDirectory() as d:
            result = build_pack(Edat(UNIT_PACK), [self.mod(d, names="key,us\nother.key,x\n")], text_arc=Edat(TEXT_PACK))
            self.assertIn("loc('c6.test.name') has no text", result.errors[0].message)
        with tempfile.TemporaryDirectory() as d:
            result = build_pack(Edat(UNIT_PACK), [self.mod(d, prefix="")], text_arc=Edat(TEXT_PACK))
            self.assertIn("set text_prefix", result.errors[0].message)

    def test_ruse_build_rebuilds_both_packs(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d, "R.U.S.E")
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(UNIT_PACK)
            (game / "Data" / "PC" / "190852" / "ZZ_Win.dat").write_bytes(TEXT_PACK)
            folder = write_mod(d, "named", NAMED, extra='text_prefix = "C6"\n')
            (folder / "text").mkdir()
            (folder / "text" / "baseunite.csv").write_text(NAMES, encoding="utf-8")
            code, out = BuildCommand.run_cli(self, "--game", str(game), "build", str(folder),
                                             "--instance", str(Path(d, "copy")))
            self.assertEqual(code, 0, out)
            self.assertIn("texts: 3 file(s) in ZZ_Win.dat (baseunite.dic ×3)", out)
            copy = Path(d, "copy", "Data", "PC", "190852")
            self.assertEqual(text_of((copy / "ZZ_Win.dat").read_bytes(), "us", name_to_key("C6000001")), "Test Sherman")
            rebuilt = Edat((copy / "ZZ_Win.dat").read_bytes())
            self.assertEqual(bytes(rebuilt.read(rebuilt.find("other.bin"))), b"untouched")
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_Win.dat").read_bytes(), TEXT_PACK)  # install untouched

            code, out = BuildCommand.run_cli(self, "--game", str(game), "build", str(folder), "--out", str(Path(d, "o.dat")))
            self.assertEqual(code, 2)  # two packs don't fit in one file
            code, out = BuildCommand.run_cli(self, "--game", str(game), "build", str(folder), "--out", str(Path(d, "packs")))
            self.assertEqual(code, 0, out)
            self.assertTrue(Path(d, "packs", "ZZ_Win.dat").is_file() and Path(d, "packs", "ZZ_GladPatchableWin.dat").is_file())


class Examples(unittest.TestCase):
    def test_every_example_mod_loads(self):
        root = Path(__file__).resolve().parent.parent / "examples"
        folders = sorted(p for p in root.iterdir() if (p / "mod.toml").is_file())
        self.assertTrue(folders)
        for folder in folders:
            info, ops = load_mod(folder)
            self.assertEqual(info.id, folder.name)
            self.assertTrue(ops or info.texts or info.terrain or info.scenery, folder.name)


HILL = ('[[stroke]]\nbrush = "hill"\nx = 1500.0\ny = 1500.0\nradius = 600.0\nheight = 400.0\n')


class Terrain(unittest.TestCase):
    """A mod that reshapes a map's ground: maps/<map>/terrain.toml, built into the map's pack (MOD_FORMAT §8)."""

    def setUp(self):
        from test_terrain_edit import make_map_pack
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        (self.game / "Data" / "PC" / "190852").mkdir(parents=True)
        (self.game / "Maps" / "PC").mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        (self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        self.map_pack = make_map_pack()
        (self.game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(self.map_pack)
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, mod_id, terrain=HILL, rndf=None, map_name="Test"):
        folder = write_mod(self.root / "mods", mod_id, rndf or {})
        (folder / "maps" / map_name).mkdir(parents=True)
        (folder / "maps" / map_name / "terrain.toml").write_text(terrain, encoding="utf-8")
        return folder

    def build(self, *folders, copy="copy"):
        lines = []
        result = build_and_write(self.game, [load_mod(f) for f in folders], instance=self.root / copy,
                                 say=lines.append)
        return result, lines

    def test_the_mod_file_is_read(self):
        info, ops = load_mod(self.mod("hill"))
        self.assertEqual((info.terrain, ops), ({"Test": [Stroke("hill", 1500.0, 1500.0, 600.0, height=400.0)]}, []))

    def test_a_reshaped_map_goes_into_the_modded_copy(self):
        result, lines = self.build(self.mod("hill"))
        self.assertEqual(result.errors, [], lines)
        pack = self.root / "copy" / "Maps" / "PC" / "DataMapTest_v09.dat"
        arc = Edat(pack.read_bytes())
        for member, data in result.terrain_changed["DataMapTest_v09.dat"].items():
            self.assertEqual(bytes(arc.read(arc.find(member))), data)
        self.assertEqual(len(result.terrain_changed["DataMapTest_v09.dat"]), 4)
        self.assertIn("terrain: Test, from hill", lines)
        self.assertTrue(any(line.startswith("changed: DataMapTest_v09.dat (4 file(s): highdef.tms") for line in lines))
        self.assertEqual((self.game / "Maps" / "PC" / "DataMapTest_v09.dat").read_bytes(), self.map_pack)  # untouched
        self.assertEqual((self.root / "copy" / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes(), PACK)
        # the ground counts for multiplayer: another hill, another fingerprint
        other, _ = self.build(self.mod("other", HILL.replace("400.0", "300.0")), copy="copy2")
        self.assertNotEqual(fingerprint_text(result.fingerprint), fingerprint_text(other.fingerprint))
        self.assertIn(f"fingerprint: {fingerprint_text(result.fingerprint)}", lines)

    def test_terrain_and_unit_changes_together_and_two_mods_on_one_map(self):
        a = self.mod("aaa", rndf={"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        b = self.mod("bbb", HILL.replace('"hill"', '"lower"').replace("400.0", "100.0"))
        result, lines = self.build(a, b)
        self.assertEqual(result.errors, [], lines)
        self.assertIn("terrain: Test, from aaa, bbb", lines)            # the strokes of both, in load order
        self.assertEqual(price((self.root / "copy" / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()),
                         [53] * 5)
        from rusemod.terrain_edit import FILES
        from rusemod.tms import Tms
        hd = Tms(result.terrain_changed["DataMapTest_v09.dat"][FILES["highdef"]])
        orig = Tms(bytes(Edat(self.map_pack).read(Edat(self.map_pack).find(FILES["highdef"]))))
        centre = [p for p in hd.cells[4].positions() if (p[0], p[1]) == (16383, 16383)]
        before = [p for p in orig.cells[4].positions() if (p[0], p[1]) == (16383, 16383)]
        self.assertTrue(centre and before)
        self.assertEqual(centre[0][2] - before[0][2], 3000)   # +400 then -100 at the very centre: +300, in 0.1 steps

    def test_mistakes(self):
        result, lines = self.build(self.mod("elsewhere", map_name="Nope"))
        self.assertIn("elsewhere: the map Nope isn't in this game (DataMapNope_v09.dat is missing)",
                      result.errors[0].message)
        self.assertIn("Nothing was written.", lines)
        self.assertFalse((self.root / "copy").exists())
        for n, (terrain, message) in enumerate([
                ("[[stroke]]\nbrush = 'hill'\n", "maps/Test/terrain.toml: stroke 1: the hill brush needs"),
                ("stroke = 5\n", "maps/Test/terrain.toml: `stroke` must be a list"),
                ("colour = 1\n", "maps/Test/terrain.toml: unknown key 'colour'"),
                ("[[stroke\n", "maps/Test/terrain.toml: ")]):
            with self.subTest(terrain=terrain), self.assertRaisesRegex(BuildError, message):
                load_mod(self.mod(f"bad-{n}", terrain))
        with self.assertRaisesRegex(BuildError, "isn't a map's pack name"):
            load_mod(self.mod("bad-name", map_name="Two Islands"))

    def test_every_rebuilt_community_mod_loads(self):
        """mods/: RUSE-Mod-Manager mods rebuilt in our format (MOD_FORMAT §13); each reads, has a README and a build.
        The rebuilt mods live in the private repo until their authors agree to publish them; none here, nothing to check."""
        root = Path(__file__).resolve().parent.parent / "mods"
        folders = sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
        if not folders:
            self.skipTest("no rebuilt community mods in this checkout")
        for folder in folders:
            info, ops = load_mod(folder)
            self.assertEqual(info.id, folder.name)
            self.assertTrue(ops or info.texts, folder.name)
            self.assertTrue((folder / "README.md").is_file(), folder.name)
            self.assertIn("[origin]", (folder / "mod.toml").read_text(encoding="utf-8"), folder.name)


if __name__ == "__main__":
    unittest.main()


class ScenarioMoves(unittest.TestCase):
    """A mod that moves a starting point: maps/<map>/scenario.toml, built into DataMap_Win.dat (MOD_FORMAT §8)."""

    def setUp(self):
        from test_scenario import scenario
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        rev = self.game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        self.data = make_edat([("dir", "test/map/blitz/".replace("/", "\\"), [("file", "leveldesign.scenario", scenario())])])
        (rev / "DataMap_Win.dat").write_bytes(self.data)
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, mod_id, moves):
        folder = write_mod(self.root / "mods", mod_id, {})
        (folder / "maps" / "Blitz").mkdir(parents=True)
        (folder / "maps" / "Blitz" / "scenario.toml").write_text(moves, encoding="utf-8")
        return folder

    def test_a_moved_starting_point_goes_into_the_modded_copy(self):
        from rusemod.scenario import Scenario
        folder = self.mod("start", '[[move]]\nfile = "leveldesign.scenario"\nitem = 0\nkind = "StartingPoint"\n'
                                   'x = 1500.0\ny = 2500.0\n')
        info, _ops = load_mod(folder)
        self.assertEqual(len(info.scenario["Blitz"]), 1)
        lines = []
        result = build_and_write(self.game, [load_mod(folder)], instance=self.root / "copy", say=lines.append)
        self.assertEqual(result.errors, [], lines)
        self.assertIn("scenario: Blitz, from start", lines)
        arc = Edat((self.root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
        s = Scenario.read(bytes(arc.read(arc.find("test/map/blitz/leveldesign.scenario".replace("/", "\\")))))
        self.assertEqual(s.items[0].position, (1500.0, 2500.0, 50.0))
        self.assertEqual((self.game / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes(), self.data)  # untouched

    def test_a_spawned_unit_goes_into_the_modded_copy(self):
        from rusemod.scenario import Scenario
        folder = self.mod("sherman", '[[move]]\nfile = "leveldesign.scenario"\nitem = 0\nkind = "StartingPoint"\n'
                                     'x = 1500.0\ny = 2500.0\n\n[[spawn]]\nfile = "leveldesign.scenario"\n'
                                     'what = "Unit_M4_Sherman"\nx = 1600.0\ny = 2600.0\ncamp = 1\nrotation = 0.5\n')
        lines = []
        result = build_and_write(self.game, [load_mod(folder)], instance=self.root / "copy", say=lines.append)
        self.assertEqual(result.errors, [], lines)
        self.assertIn("  Blitz: leveldesign.scenario: 1 item(s) moved, 1 spawn(s) added", lines)
        arc = Edat((self.root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
        s = Scenario.read(bytes(arc.read(arc.find("test/map/blitz/leveldesign.scenario".replace("/", "\\")))))
        new = s.items[-1]
        self.assertEqual((new.kind, new.position[:2], new.rotation), ("Spawn", (1600.0, 2600.0), 0.5))
        self.assertEqual(new.values, {"Camp": 1, "PythonClassName": "front.parametres.Classes.Unit_M4_Sherman"})
        self.assertEqual(s.items[0].position[:2], (1500.0, 2500.0))

    def test_a_move_for_another_version_of_the_map_is_refused(self):
        folder = self.mod("wrong", '[[move]]\nfile = "leveldesign.scenario"\nitem = 1\nkind = "StartingPoint"\n'
                                   'x = 1.0\ny = 2.0\n')
        lines = []
        result = build_and_write(self.game, [load_mod(folder)], instance=self.root / "copy", say=lines.append)
        self.assertTrue(any("item 1 is a Spawn, not a StartingPoint" in f.message for f in result.errors), lines)
        self.assertFalse((self.root / "copy").exists())
        bad = self.mod("bad", '[[move]]\nfile = "../x.scenario"\nitem = 0\nkind = "StartingPoint"\nx = 1\ny = 2\n')
        with self.assertRaises(BuildError):
            load_mod(bad)


class ScenarioOnTheGround(unittest.TestCase):
    """Spawned units and moved starting points stand at the ground's height there, as every shipped one does
    (6,380 spawns, none at z 0): read from the map's highdef.tms, on a made-up map with hills."""

    def test_spawns_and_moved_starts_take_the_grounds_height(self):
        from test_scenario import scenario
        from test_terrain_edit import make_map_pack
        from rusemod.scenario import DEPOT, Scenario
        from rusemod.terrain_edit import FILES
        from rusemod.tms import Tms
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "steamapps" / "common" / "R.U.S.E"
            rev = game / "Data" / "PC" / "190852"
            rev.mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "RUSE.exe").write_bytes(b"MZ")
            (rev / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            (rev / "DataMap_Win.dat").write_bytes(
                make_edat([("dir", "test/map/test/".replace("/", "\\"), [("file", "leveldesign.scenario", scenario())])]))
            map_pack = make_map_pack()
            (game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(map_pack)
            (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            folder = write_mod(root / "mods", "ground", {})
            (folder / "maps" / "Test").mkdir(parents=True)
            (folder / "maps" / "Test" / "scenario.toml").write_text(
                '[[move]]\nfile = "leveldesign.scenario"\nitem = 0\nkind = "StartingPoint"\nx = 1400.0\ny = 1600.0\n\n'
                '[[spawn]]\nfile = "leveldesign.scenario"\nwhat = "Unit_M4_Sherman"\nx = 1500.0\ny = 1500.0\n\n'
                '[[spawn]]\nfile = "leveldesign.scenario"\nwhat = "DalleBatimentDepot"\nx = 1700.0\ny = 1300.0\n',
                encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            arc = Edat((root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
            s = Scenario.read(bytes(arc.read(arc.find("test/map/test/leveldesign.scenario".replace("/", "\\")))))
            ground = Tms(bytes(Edat(map_pack).read(Edat(map_pack).find(FILES["highdef"]))))
            start, tank, depot = s.items[0], s.items[-2], s.items[-1]
            for it in (start, tank, depot):
                self.assertAlmostEqual(it.position[2], ground.height_at(*it.position[:2]), places=3)
            self.assertNotEqual(tank.position[2], 0.0)
            self.assertEqual(tank.values["Camp"], -1)  # no camp given: neutral
            self.assertEqual(depot.values, {"PythonClassName": DEPOT, "ChampInteger": 25, "Camp": -1})
