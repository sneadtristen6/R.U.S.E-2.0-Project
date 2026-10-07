"""The game's map and mission scripts shown as Python (rusemod.mapscripts, the AI tab's script viewer) and changed in
a mod (its script editor), on a made-up game whose scripts are small ones of our own (none of the game's). Skipped
where the two libraries LittleGroove's engine uses for it aren't installed (the Python 3.11 test runs:
.github/workflows/tests.yml), and the tests that make a script where the game's Python 2.5.1 isn't with the apps."""
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from fixtures import make_edat
from rusemod import mapscripts
from rusemod.build import BuildError, build_and_write, load_mod
from rusemod.edat import Edat
from ruse_studio.api import StudioApi, StudioError

MISSING = mapscripts.missing()


def s(b: bytes) -> bytes:
    return b"s" + struct.pack("<i", len(b)) + b


def name(b: bytes) -> bytes:  # an interned name, as Python 2.5 writes a code object's names
    return b"t" + struct.pack("<i", len(b)) + b


def tup(*items: bytes) -> bytes:
    return b"(" + struct.pack("<i", len(items)) + b"".join(items)


def script(value: int) -> bytes:
    """A module of our own, `GOAL = <value>`, as the game keeps its scripts (Python 2.5, in an .xyz)."""
    from ruse_mod_engine import xyz_compile
    code = b"d\x00\x00Z\x00\x00d\x01\x00S"  # LOAD_CONST 0, STORE_NAME 0, LOAD_CONST 1 (None), RETURN_VALUE
    obj = (b"c" + struct.pack("<iiii", 0, 0, 1, 0x40) + s(code) + tup(b"i" + struct.pack("<i", value), b"N")
           + tup(name(b"GOAL")) + tup() + tup() + tup() + s(b"effetmap.py") + name(b"<module>")
           + struct.pack("<i", 1) + s(b""))
    return xyz_compile.pack(obj)


PATHS = ("genpython\\1000\\test\\map\\supercrossroads4\\scripting_challenge\\effetmap.xyz",
         "genpython\\1000\\test\\map\\m04_cotentin\\scripting_chapter1\\effetmap.xyz",
         "genpython\\1000\\test\\map\\supercrossroads4\\scripting_testia\\maptests\\__init__.xyz")


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    files = [("file", p, script(i + 1)) for i, p in enumerate(PATHS)] + [("file", "readme.txt", b"not a script")]
    (rev / "IA_Common.dat").write_bytes(make_edat(files))
    (root / "RUSE.exe").write_bytes(b"MZ")


@unittest.skipIf(MISSING, f"can't show scripts here: {MISSING}")
class Scripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_a_script_as_python(self):
        self.assertEqual(mapscripts.text(script(7)), "GOAL = 7\n")  # without the library's lines about itself
        self.assertEqual(mapscripts.text(mapscripts.sample()), "")  # the self-test's: an empty module
        self.assertIsNone(mapscripts.missing())

    def test_the_list_by_map(self):
        found = mapscripts.scripts(self.game)
        self.assertEqual([(f["map"], f["part"], f["file"]) for f in found],
                         [("m04_cotentin", "scripting_chapter1", "effetmap.xyz"),
                          ("supercrossroads4", "scripting_challenge", "effetmap.xyz"),
                          ("supercrossroads4", "scripting_testia", "maptests/__init__.xyz")])
        self.assertEqual(mapscripts.text(mapscripts.read(self.game, found[0]["path"])), "GOAL = 2\n")
        with self.assertRaises(KeyError):
            mapscripts.read(self.game, "readme.txt")  # not a script
        self.assertEqual(mapscripts.scripts(Path(self.tmp.name, "nothing")), [])

    def test_the_ai_tab_s_calls(self):
        home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        api = StudioApi(game_dir=self.game, home=home, instances=home / "copies")
        page = api.ai_scripts("us")
        self.assertIsNone(page["missing"])
        # no map list in this made-up game: each map by its folder's name
        self.assertEqual([(x["map"], x["part"], x["file"], x["detail"]) for x in page["scripts"]][:2],
                         [("m04_cotentin", "chapter1", "effetmap.xyz", "m04_cotentin/scripting_chapter1/effetmap.xyz"),
                          ("supercrossroads4", "challenge", "effetmap.xyz",
                           "supercrossroads4/scripting_challenge/effetmap.xyz")])
        shown = api.ai_script(PATHS[0])
        self.assertEqual((shown["text"], shown["lines"]), ("GOAL = 1\n", 1))
        self.assertIs(api.ai_script(PATHS[0])["text"], shown["text"])  # the second time from the session's copy
        with self.assertRaisesRegex(StudioError, "isn't one of IA_Common.dat's scripts"):
            api.ai_script("genpython\\nothing.xyz")


# --- changing a mission script in a mod (the owner, 2026-10-07: "Yes, allow a tool to edit mission scripts") ---
COMPILER = mapscripts.compiler_missing()
MEMBER = PATHS[1]  # m04_cotentin/scripting_chapter1/effetmap.xyz
KEY = ("m04_cotentin", "scripting_chapter1", "effetmap.xyz")
REL = "scripts/m04_cotentin/scripting_chapter1/effetmap.py"


def says(text: str) -> bytes:
    """A module of our own, `GOAL = u'<text>'`, a text with accented letters or quotes, as the game keeps its scripts."""
    from ruse_mod_engine import xyz_compile
    raw = text.encode("utf-8")
    code = b"d\x00\x00Z\x00\x00d\x01\x00S"
    obj = (b"c" + struct.pack("<iiii", 0, 0, 1, 0x40) + s(code) + tup(b"u" + struct.pack("<i", len(raw)) + raw, b"N")
           + tup(name(b"GOAL")) + tup() + tup() + tup() + s(b"effetmap.py") + name(b"<module>")
           + struct.pack("<i", 1) + s(b""))
    return xyz_compile.pack(obj)


def make_mod(root: Path, files: dict, mod_id: str = "story") -> Path:
    mod = root / mod_id
    (mod / "src").mkdir(parents=True)
    (mod / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nversion = "0.1.0"\n', encoding="utf-8")
    for rel, data in files.items():
        f = mod / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return mod


@unittest.skipIf(MISSING, f"can't show scripts here: {MISSING}")
class Spelling(unittest.TestCase):
    def test_accented_texts_and_quotes_shown_as_the_game_s_python_reads_them(self):
        # before 2026-10-07 his engine's library lost the first two letters of such a text and wrote the rest as hex
        # numbers (u'\u bis vus et pr0xe9sent0xe9s'), and left an apostrophe in a text unescaped
        self.assertEqual(mapscripts.text(says("présentés")), "GOAL = u'pr\\xe9sent\\xe9s'\n")
        self.assertEqual(mapscripts.text(says("L'été")), "GOAL = u\"L'\\xe9t\\xe9\"\n")
        self.assertEqual(mapscripts.text(says("a \" and a '")), "GOAL = u'a \" and a \\''\n")

    @unittest.skipIf(COMPILER, f"can't make scripts here: {COMPILER}")
    def test_made_again_with_the_game_s_python(self):
        for original in (script(1), says("L'été"), says("a \" and a '")):
            text = mapscripts.text(original)
            made = mapscripts.compile_text(text, original)
            self.assertEqual(mapscripts.text(made), text)
            self.assertEqual(mapscripts.compile_text(text, original), made)  # the same text: the same bytes
        self.assertTrue(mapscripts.same_script(made, mapscripts.compile_text(text, original)))
        self.assertFalse(mapscripts.same_script(made, script(1)))
        self.assertFalse(mapscripts.same_script(made, b"not a script"))
        self.assertEqual(mapscripts.text(mapscripts.compile_text("GOAL = 9\n", script(1))), "GOAL = 9\n")
        with self.assertRaises(mapscripts.ScriptError) as caught:
            mapscripts.compile_text("GOAL = 1\nGOAL = = 2\n", script(1))
        self.assertEqual(caught.exception.line, 2)


class ModFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_which_of_a_mod_s_files_are_mission_scripts(self):
        for rel, ok in ((REL, True), (REL[:-3] + ".xyz", True), ("scripts/m04/scripting_chapter2-ps3/effetmap.py", True),
                        ("scripts/supercrossroads4/scripting_testia/maptests/__init__.py", True),
                        ("scripts/m04/effetmap.py", False), ("src/effetmap.py", False),
                        ("scripts/m04/scripting/run.exe", False), ("scripts/m04/../../effetmap.py", False),
                        ("scripts/m 04/scripting/effetmap.py", False), ("files/m04/scripting/effetmap.xyz", False)):
            with self.subTest(rel=rel):
                self.assertEqual(mapscripts.is_mod_script(rel), ok)
        self.assertEqual(str(mapscripts.mod_file(*KEY)), REL)
        self.assertEqual(str(mapscripts.mod_file("m", "p", "maptests/__init__.xyz")), "scripts/m/p/maptests/__init__.py")

    def test_read_from_the_mod_folder(self):
        mod = make_mod(self.root, {REL: "GOAL = 9\n", REL[:-3] + ".xyz": b"XYZ0 made",
                                   "scripts/Blitz/Scripting/EffetMap.xyz": b"XYZ0 only"})
        self.assertEqual(mapscripts.read_mod(mod), {
            KEY: {"rel": REL, "text": "GOAL = 9\n", "xyz": b"XYZ0 made"},
            ("blitz", "scripting", "effetmap.xyz"): {"rel": "scripts/Blitz/Scripting/EffetMap.py", "text": None,
                                                     "xyz": b"XYZ0 only"}})
        self.assertEqual(mapscripts.read_mod(self.root / "nothing"), {})

    def test_the_build_reads_them_and_still_refuses_every_other_script(self):
        mod = make_mod(self.root, {REL: "GOAL = 9\n", REL[:-3] + ".xyz": b"XYZ0 made"})
        info, _ops = load_mod(mod)
        self.assertEqual(info.scripts, {KEY: {"rel": REL, "text": "GOAL = 9\n", "xyz": b"XYZ0 made"}})
        for rel in ("src/evil.py", "scripts/m04/run.bat", "scripts/m04/effetmap.py"):
            with self.subTest(rel=rel):
                bad = make_mod(self.root, {rel: "x = 1\n"}, mod_id="bad-" + str(len(rel)))
                with self.assertRaisesRegex(BuildError, "mods can't contain scripts or programs"):
                    load_mod(bad)

    def test_packed_installed_and_refused_like_the_build(self):
        from rusemod import package
        mod = make_mod(self.root, {REL: "GOAL = 9\n", REL[:-3] + ".xyz": b"XYZ0 made"})
        made = package.pack(mod, self.root / "out")
        info = package.check(made)
        self.assertIn(REL, info["files"])
        self.assertIn(REL[:-3] + ".xyz", info["files"])
        package.unpack(made, self.root / "installed")
        self.assertEqual((self.root / "installed" / REL).read_text(encoding="utf-8"), "GOAL = 9\n")
        evil = self.root / "evil.rusemod"
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("mod.toml", '[mod]\nid = "evil"\nversion = "0.1.0"\n')
            z.writestr("scripts/m04/run.py", "x = 1\n")
        with self.assertRaisesRegex(package.PackageError, "mods can't contain scripts or programs"):
            package.check(evil)


class Building(unittest.TestCase):
    """What a build does with a mod's mission scripts (rusemod.mapscripts.build_changes), on a made-up pack."""

    def changes(self, mods, compiler: bool, original: bytes = b"XYZ0 game's"):
        arc = Edat(make_edat([("file", p, original) for p in PATHS]))
        with mock.patch.object(mapscripts, "compiler_missing", return_value=None if compiler else "no Python 2.5.1"):
            return mapscripts.build_changes(arc, mods)

    def test_the_script_as_the_game_runs_it_goes_in_with_a_warning(self):
        entry = {"rel": REL, "text": "GOAL = 9\n", "xyz": b"XYZ0 made"}
        out, said = self.changes([("story", {KEY: entry})], compiler=False)
        self.assertEqual(out, {MEMBER: b"XYZ0 made"})
        self.assertEqual(said, [("warning", "story changes 1 of the game's mission scripts "
                                            "(m04_cotentin/scripting_chapter1/effetmap.xyz): scripts run inside the "
                                            "game, so use it only if you trust its author")])

    def test_what_stops_the_build(self):
        only_text = {"rel": REL, "text": "GOAL = 9\n", "xyz": None}
        _out, said = self.changes([("story", {KEY: only_text})], compiler=False)
        self.assertEqual([level for level, _m in said], ["error"])
        self.assertIn("story: " + REL + ": only its text is here", said[0][1])
        made = {"rel": REL, "text": None, "xyz": b"XYZ0 made"}
        _out, said = self.changes([("story", {("nowhere", "scripting", "effetmap.xyz"): made})], compiler=False)
        self.assertIn("the game has no script effetmap.xyz in nowhere/scripting", said[0][1])
        out, said = self.changes([("one", {KEY: made}), ("two", {KEY: made})], compiler=False)
        self.assertEqual(([level for level, _m in said], out), (["warning", "error"], {MEMBER: b"XYZ0 made"}))
        self.assertIn("two: " + REL + ": one changes this script too", said[1][1])

    @unittest.skipIf(MISSING or COMPILER, f"can't make scripts here: {MISSING or COMPILER}")
    def test_with_the_game_s_python_the_text_is_what_counts(self):
        original = script(1)
        made = mapscripts.compile_text("GOAL = 9\n", original)
        good = {"rel": REL, "text": "GOAL = 9\n", "xyz": made}
        out, said = self.changes([("story", {KEY: good})], compiler=True, original=original)
        self.assertEqual((out, [level for level, _m in said]), ({MEMBER: made}, ["warning"]))
        out, _said = self.changes([("story", {KEY: {**good, "xyz": None}})], compiler=True, original=original)
        self.assertEqual(out, {MEMBER: made})  # only the text: made here
        _out, said = self.changes([("story", {KEY: {**good, "xyz": script(4)}})], compiler=True, original=original)
        self.assertIn("its .xyz isn't what its text makes", said[0][1])
        _out, said = self.changes([("story", {KEY: {**good, "text": "GOAL = (\n"}})], compiler=True, original=original)
        self.assertEqual(said[0][0], "error")
        self.assertIn("the game's Python can't read this script (line ", said[0][1])

    def test_a_whole_build(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        game = root / "game"
        (game / "Data" / "PC" / "190852").mkdir(parents=True)
        (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "a.bin", b"a")]))
        ia = game / "Data" / "PC" / "190852" / "IA_Common.dat"
        ia.write_bytes(make_edat([("file", p, b"XYZ0 game's") for p in PATHS]))
        (game / "RUSE.exe").write_bytes(b"MZ")
        before = ia.read_bytes()
        mod = make_mod(root, {REL[:-3] + ".xyz": b"XYZ0 made"})
        lines = []
        with mock.patch.object(mapscripts, "compiler_missing", return_value="no Python 2.5.1"):
            result = build_and_write(game, [load_mod(mod)], out=root / "out", say=lines.append)
        self.assertEqual(result.errors, [])
        self.assertIn("mission scripts: 1 changed in IA_Common.dat", lines)
        self.assertTrue(any("only if you trust its author" in f.message for f in result.findings if
                            f.level == "warning"), result.findings)
        written = Edat((root / "out" / "IA_Common.dat").read_bytes())
        self.assertEqual({e.path: bytes(written.read(e)) for e in written.entries},
                         {PATHS[0]: b"XYZ0 game's", MEMBER: b"XYZ0 made", PATHS[2]: b"XYZ0 game's"})
        self.assertEqual(ia.read_bytes(), before)  # never the game's own


@unittest.skipIf(MISSING, f"can't show scripts here: {MISSING}")
class Editor(unittest.TestCase):
    """The AI tab's script editor (StudioApi.ai_script_check / ai_script_save / ai_script_reset / script_outline /
    script_reference)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Path(self.tmp.name, "game")
        write_game(self.game)
        home = Path(self.tmp.name, "home")
        self.api = StudioApi(game_dir=self.game, home=home, instances=home / "copies")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nothing_to_save_in_without_a_mod(self):
        shown = self.api.ai_script(MEMBER)
        self.assertEqual((shown["mine"], shown["can_change"]), (None, False))
        with self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
            self.api.ai_script_save(MEMBER, "GOAL = 9\n")
        with self.assertRaisesRegex(StudioError, "isn't one of the game's mission scripts"):
            self.api.ai_script_check("genpython\\nothing.xyz", "GOAL = 9\n")

    @unittest.skipIf(COMPILER, f"can't make scripts here: {COMPILER}")
    def test_checked_saved_and_taken_out(self):
        self.api.new_mod("Story")
        folder = Path(self.api.mods()["current"])
        self.assertEqual(self.api.ai_script_check(MEMBER, "GOAL = 9\n"), {"ok": True, "error": None, "line": None})
        bad = self.api.ai_script_check(MEMBER, "GOAL = 9\nGOAL = = 1\n")
        self.assertEqual((bad["ok"], bad["line"]), (False, 2))
        with self.assertRaisesRegex(StudioError, r"\(line 2\).*Nothing was saved"):
            self.api.ai_script_save(MEMBER, "GOAL = 9\nGOAL = = 1\n")
        self.assertFalse((folder / "scripts").exists())
        shown = self.api.ai_script_save(MEMBER, "GOAL = 9\r\n")
        self.assertEqual((shown["mine"], shown["text"], shown["can_change"]), ("GOAL = 9\n", "GOAL = 2\n", True))
        made = (folder / REL[:-3]).with_suffix(".xyz").read_bytes()
        self.assertEqual(mapscripts.text(made), "GOAL = 9\n")
        self.assertEqual([x["mine"] for x in self.api.ai_scripts("us")["scripts"]], [True, False, False])
        info, _ops = load_mod(folder)
        self.assertEqual(list(info.scripts), [KEY])
        self.api.ai_script_save(MEMBER, "GOAL = 2\n")  # the game's own text again: the mod's script is taken out
        self.assertEqual(mapscripts.read_mod(folder), {})
        self.api.ai_script_save(MEMBER, "GOAL = 9\n")
        self.assertIsNone(self.api.ai_script_reset(MEMBER)["mine"])
        self.assertEqual(mapscripts.read_mod(folder), {})

    def test_the_outline_and_the_reference(self):
        text = ("from Scripting.Library import *\n"
                "IR_0001 = Sequence(Children=[IR_0002])\n"
                "IR_0002 = Wait(Duree=5)\n")
        steps = self.api.script_outline(text)["steps"]
        self.assertIsInstance(steps, list)
        for step in steps:
            self.assertEqual(set(step), {"depth", "ir", "kind", "label", "line"})
        self.assertEqual(self.api.script_outline("this isn't python ("), {"steps": [], "more": 0})
        many = {"ir": "IR_1", "kind": "flow", "children": [{"ir": f"IR_{n}", "kind": "action"} for n in range(2, 452)]}
        with mock.patch("ruse_mod_engine.script_logic.parse_flow", return_value=many):
            got = self.api.script_outline("IR_1 = 1\nIR_2 = 2\n")
        self.assertEqual((len(got["steps"]), got["more"]), (StudioApi.OUTLINE_SHOWN, 451 - StudioApi.OUTLINE_SHOWN))
        self.assertEqual([(x["depth"], x["ir"], x["line"]) for x in got["steps"][:3]],
                         [(0, "IR_1", 1), (1, "IR_2", 2), (1, "IR_3", None)])  # in the order they run
        found = self.api.script_reference("wait")
        self.assertTrue(found["classes"], "LittleGroove's catalogue finds nothing for 'wait'")
        self.assertLessEqual(len(found["classes"]), 60)
        self.assertIn("action", found["kinds"])
        first = found["classes"][0]
        self.assertTrue(first["snippet"].startswith("IR_NEW = "), first["snippet"])
        self.assertEqual(set(first), {"name", "label", "kind", "category", "help", "params", "used", "examples",
                                      "snippet"})
        only = self.api.script_reference("", "condition")["classes"]
        self.assertTrue(only and all(c["kind"] == "condition" for c in only))


if __name__ == "__main__":
    unittest.main()
