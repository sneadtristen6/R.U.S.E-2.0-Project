"""The mod check in plain words with a fix for each problem (rusemod.plainproblems, StudioApi.check_mod / fix_problem;
the owner, 2026-10-10: "all of the error messages should be able to have a fix or like a fix button or like a how-to
fix in like plain people language"): problems read back into their parts, the fixes edit only what they say, and the
Studio's mod check offers them."""
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import plainproblems as pp
from ruse_studio.api import StudioApi, StudioError

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}
T = "maps/SuperCrossRoads4/terrain.toml"
TERRAIN = """# made by the Studio
[[stroke]]
brush = "water"
x = 100.0
y = 200.0
radius = 50.0

[[stroke]]
brush = "raise"
x = 5.0
y = 6.0
radius = 100.0
height = 300.0
weight = 0.5
"""


def kinds(raw, set_aside=False):
    e = pp.explain({"file": None, "problem": raw, "set_aside": set_aside})
    return e["plain"], [(f["fix"], f.get("key")) for f in e["fixes"]]


class Explain(unittest.TestCase):
    def test_map_items(self):
        plain, fixes = kinds(f"{T}: stroke 1: the water brush needs level", True)
        self.assertEqual((plain["kind"], plain["map"], plain["table"], plain["n"], plain["key"]),
                         ("missing", "SuperCrossRoads4", "stroke", 1, "level"))
        self.assertEqual(fixes, [("fill", "level"), ("remove_item", None), ("set_aside", None)])
        plain, fixes = kinds(f"{T}: stroke 2: unknown key 'colr' (keys: brush, colour)", True)
        self.assertEqual((plain["kind"], plain["key"]), ("unknown_key", "colr"))
        self.assertEqual(fixes, [("remove_key", "colr"), ("remove_item", None), ("set_aside", None)])
        plain, fixes = kinds(f"{T}: stroke 3: radius must be above 0")
        self.assertEqual((plain["kind"], plain["key"], fixes), ("bad_value", "radius", [("remove_item", None)]))
        plain, _ = kinds("maps/X/scenery.toml: erase area 4 has no radius")
        self.assertEqual((plain["table"], plain["n"], plain["kind"], plain["key"]), ("erase", 4, "missing", "radius"))
        plain, _ = kinds("maps/X/scenario.toml: spawn 1: a line needs x2 and y2 (where it ends)")
        self.assertEqual((plain["table"], plain["keys"]), ("spawn", ["x2", "y2"]))
        plain, _ = kinds("maps/X/scenery.toml: object 2: a number is out of range (size: 0.05 to 50)")
        self.assertEqual((plain["kind"], plain["key"]), ("bad_value", None))

    def test_files(self):
        plain, fixes = kinds(f"{T}: Expected '=' after a key in a key/value pair (at line 3, column 5)", True)
        self.assertEqual((plain["kind"], fixes), ("unreadable", [("set_aside", None)]))
        plain, fixes = kinds("src/studio.rndf:425:14: can't read '/patchable/s'")
        self.assertEqual((plain["kind"], plain["file"], plain["line"], fixes),
                         ("unit_file", "src/studio.rndf", 425, [("set_aside", None)]))
        plain, _ = kinds("text/names.csv:3: a row without a key")
        self.assertEqual((plain["kind"], plain["line"]), ("text_file", 3))
        plain, fixes = kinds("D:/mods/x/mod.toml: [mod] id must be lowercase letters, digits and '-'")
        self.assertEqual((plain["kind"], fixes), ("manifest", []))
        plain, _ = kinds("Unit X is researched from a unit the mod took out")
        self.assertEqual(plain["kind"], "other")


class Edit(unittest.TestCase):
    def test_each_fix_changes_only_what_it_says(self):
        filled = pp.edit(TERRAIN, "fill", "stroke", 1, "level", 1234.56789)
        self.assertEqual(tomllib.loads(filled)["stroke"][0]["level"], 1234.568)
        self.assertEqual(filled.replace("level = 1234.568\n", ""), TERRAIN)
        gone = pp.edit(TERRAIN, "remove_key", "stroke", 2, "weight")
        self.assertNotIn("weight", gone)
        self.assertEqual(len(tomllib.loads(gone)["stroke"]), 2)
        one = tomllib.loads(pp.edit(TERRAIN, "remove_item", "stroke", 1))["stroke"]
        self.assertEqual([s["brush"] for s in one], ["raise"])
        self.assertTrue(pp.edit(TERRAIN, "remove_item", "stroke", 2).startswith("# made by the Studio\n"))

    def test_what_it_refuses(self):
        for args in (("remove_item", "stroke", 3), ("remove_key", "stroke", 1, "weight"), ("fill", "stroke", 2, "x", 1.0),
                     ("remove_key", "stroke", 1, "bad key"), ("explode", "stroke", 1)):
            with self.subTest(args=args), self.assertRaises(pp.FixError):
                pp.edit(TERRAIN, *args)
        long = TERRAIN.replace("weight = 0.5", "weight = [\n  1,\n  2,\n]")
        with self.assertRaises(pp.FixError):
            pp.edit(long, "remove_key", "stroke", 2, "weight")


class Studio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        home = Path(self.tmp.name, "home")
        self.api = StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None, home=home)
        self.mod = Path(self.api.new_mod("Broken")["current"])
        (self.mod / T).parent.mkdir(parents=True)
        (self.mod / T).write_text(TERRAIN, encoding="utf-8", newline="\n")
        self.api._map_water = lambda pack, folder: 812.25  # the game's own map isn't here: its water height, made up

    def problems(self):
        return self.api.check_mod()["problems"]

    def test_the_check_says_it_plainly_and_the_fill_fixes_it(self):
        (p,) = self.problems()
        self.assertEqual(p["problem"], f"{T}: stroke 1: the water brush needs level")
        self.assertEqual((p["plain"]["kind"], p["plain"]["key"]), ("missing", "level"))
        fill = next(f for f in p["fixes"] if f["fix"] == "fill")
        res = self.api.fix_problem(fill)
        self.assertEqual(res["problems"], [])
        self.assertIn("terrain.before-fix.toml", res["message"])
        self.assertEqual(tomllib.loads((self.mod / T).read_text(encoding="utf-8"))["stroke"][0]["level"], 812.25)
        self.assertEqual((self.mod / T).with_name("terrain.before-fix.toml").read_text(encoding="utf-8"), TERRAIN)

    def test_remove_the_item_and_set_aside(self):
        (p,) = self.problems()
        res = self.api.fix_problem(next(f for f in p["fixes"] if f["fix"] == "remove_item"))
        self.assertEqual(res["problems"], [])
        self.assertEqual(len(tomllib.loads((self.mod / T).read_text(encoding="utf-8"))["stroke"]), 1)
        bad = self.mod / "src" / "hand.rndf"
        bad.write_text("patch $/GFX/Everything/X\n(\n    Speed = \n", encoding="utf-8")
        (p,) = self.problems()
        self.assertEqual((p["plain"]["kind"], p["plain"]["file"]), ("unit_file", "src/hand.rndf"))
        res = self.api.fix_problem(p["fixes"][0])
        self.assertEqual(res["problems"], [])
        self.assertTrue((self.mod / "src" / "hand.rndf.broken").is_file())

    def test_a_fix_only_for_this_mod_s_map_files(self):
        with self.assertRaises(StudioError):
            self.api.fix_problem({"fix": "remove_item", "file": "../elsewhere/terrain.toml", "table": "stroke", "n": 1})
        with self.assertRaises(StudioError):
            self.api.fix_problem({"fix": "fill", "file": T, "table": "stroke", "n": 2, "key": "x"})


class Page(unittest.TestCase):
    def test_the_words_are_in_every_language(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        keys = [k for k in words if k.startswith(("pp_", "tip_pp_"))]
        self.assertGreater(len(keys), 60)
        for key in keys:
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), LANGS)
        for table in set(pp.ITEMS.values()):
            self.assertIn(f"pp_item_{table}", words)

    def test_the_bar_uses_them(self):
        ui = ROOT / "src" / "ruse_studio" / "ui"
        app, fake = (ui / "app.js").read_text(encoding="utf-8"), (ui / "fake-api.js").read_text(encoding="utf-8")
        for needle in ("function plainProblem", "function fixButton", "api().fix_problem(", "api().open_mod_in_folder("):
            self.assertIn(needle, app)
        for needle in ("fix_problem: async", "open_mod_in_folder: async"):
            self.assertIn(needle, fake)


if __name__ == "__main__":
    unittest.main()
