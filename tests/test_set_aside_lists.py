"""A broken animations or build-menu groups file said in plain words, with a Set aside button (51m; the owner's "7 A",
2026-11-26: "Set aside is offered; it may cost the unit its own animations in the build, and the box says so BEFORE the
player clicks Set aside").

menu_groups.toml and files/anim/units.toml, copies.toml and clips.toml were read by the build with the toml reader's
English words, and Set aside took only map files, unit changes (.rndf) and text (.csv). Now check_mod names each of them
as a problem of its own file with Set aside, the row's own line (shown before any click) says what the build goes without,
and set_aside renames the file (<name>.broken.toml, never lost).

What must keep working: a file that is fine is no problem, mod.toml and a file that isn't there still can't be set aside,
a path out of the mod is refused, a map's own file is set aside as before."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import re
import tomllib
import unittest
from pathlib import Path

from test_studio import WithMod
from ruse_studio.api import StudioError

SRC = Path(__file__).resolve().parents[1] / "src" / "ruse_studio"
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
FILES = {"menu_groups.toml": "menu_groups", "files/anim/units.toml": "units", "files/anim/copies.toml": "copies",
         "files/anim/clips.toml": "clips"}
KEYS = ["pp_list_file", "tip_check_set_aside_list"] + [f"pp_file_{n}" for n in FILES.values()] \
    + [f"pp_how_{n}" for n in FILES.values()]


class OnAMod(WithMod):
    def setUp(self):
        super().setUp()
        self.folder = Path(self.api.new_mod("Lists")["current"])

    def break_file(self, rel: str) -> Path:
        path = self.folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[[[ this is not toml\n", encoding="utf-8")
        return path

    def rows(self):
        return self.api.check_mod()["problems"]

    def test_each_file_is_its_own_problem_with_set_aside_and_set_aside_renames_it(self):
        for rel in FILES:
            with self.subTest(rel):
                path = self.break_file(rel)
                problems = [p for p in self.rows() if p["file"] == rel]
                self.assertEqual(len(problems), 1, self.rows())
                p = problems[0]
                self.assertTrue(p["set_aside"])
                self.assertEqual(p["plain"]["kind"], "list_file")
                self.assertEqual([f for f in p["fixes"] if f["fix"] == "set_aside"],
                                 [{"fix": "set_aside", "file": rel}])
                got = self.api.set_aside(rel)
                self.assertFalse(path.exists())
                self.assertTrue(Path(got["kept"]).is_file())
                self.assertEqual(Path(got["kept"]).name, path.stem + ".broken.toml")
                self.assertEqual([q for q in got["problems"] if q["file"] == rel], [])
                self.assertEqual(self.rows(), [])

    def test_a_file_that_is_fine_is_no_problem(self):
        (self.folder / "files" / "anim").mkdir(parents=True, exist_ok=True)
        (self.folder / "files" / "anim" / "units.toml").write_text("", encoding="utf-8")
        self.assertEqual(self.rows(), [])

    def test_what_still_can_t_be_set_aside(self):
        (self.folder / "files" / "anim").mkdir(parents=True, exist_ok=True)
        for rel in ("mod.toml", "files/anim/units.toml", "../mod.toml", "files/anim/other.toml"):
            with self.subTest(rel), self.assertRaises(StudioError):
                self.api.set_aside(rel)
        self.assertTrue((self.folder / "mod.toml").is_file())

    def test_the_row_says_what_the_build_goes_without_before_any_click(self):
        """The row's own line (plainHow, shown with the problem, before the button is clicked) is the page's words for
        the file; units.toml's says the unit may lose its own animations in the build."""
        app = (SRC / "ui" / "app.js").read_text(encoding="utf-8")
        how = app[app.index("function plainHow"):app.index("function needsFolder")]
        self.assertIn('pl.kind === "list_file"', how)
        self.assertIn("pp_how_", how)
        us = {k: v["us"] for k, v in tomllib.loads((SRC / "words.toml").read_text(encoding="utf-8")).items()}
        self.assertIn("animations of their own", us["pp_how_units"])

    def test_its_words_in_eleven_languages(self):
        words = tomllib.loads((SRC / "words.toml").read_text(encoding="utf-8"))
        for key in KEYS:
            with self.subTest(key):
                for lang in LANGS:
                    self.assertTrue(words[key].get(lang), lang)
                blanks = sorted(re.findall(r"\{\w+\}", words[key]["us"]))
                for lang in LANGS:
                    self.assertEqual(sorted(re.findall(r"\{\w+\}", words[key][lang])), blanks, lang)


if __name__ == "__main__":
    unittest.main()
