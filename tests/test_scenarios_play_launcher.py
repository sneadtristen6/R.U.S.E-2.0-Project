"""Scenarios: Play in the RUSE Launcher, as a player meets it on the PC where he makes mods with the Studio (the base,
its made-up game and its stand-ins: tests/test_scenarios_play_base.py): a mod made in the Studio played in a set, in
the player's language; two mods in one set; no mod ticked; a mod gone from the library; the mod check when a mod is
added; join codes shown and compared, before any Play, after it, and after the Studio's Test in game built the same
modded copy. Each ends with what the page says, the copy built and what was started.

FOR: the Test in game and Play scenarios (release 0.9.8.20, overnight 2026-11-14). USED-BY: the scenarios' run and
report."""
import unittest
from pathlib import Path

from test_scenarios_play_base import LANGS, M4, PlayScenario
from test_scenarios_play_studio import value_in

LAUNCHER_UI = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher" / "ui" / "app.js"


class Sets(PlayScenario):
    def library_mod(self, la, name: str, value: int) -> str:
        """A mod made in the Studio (New mod, one value) added to the Launcher's library as Add a mod… adds a folder:
        its library id."""
        folder = self.a_mod(name, value)
        return la.add_mod(str(folder))["mod"]["id"]


class PlayASet(Sets):
    def test_a_studio_mod_played_in_a_set_in_french(self):
        """Usual: a mod made in the Studio, added to the library, put in a new set and played with the Launcher in
        French: its lines in French, the copy built with the mod's value, the game started from it."""
        la = self.launcher()
        mod = self.library_mod(la, "Tank Test", 15)
        la.new_set("Mine", [mod])
        j = self.played(la, "mine", "fr")
        self.assertEqual(j["state"], "done", j)
        self.assertTrue(any(line.startswith("Construction de la copie moddée") for line in j["lines"]), j["lines"])
        self.assertEqual((value_in(self.copy()), self.started), (15, [self.exe_of(self.copy())]))

    def test_two_mods_the_later_wins(self):
        """Usual: two mods changing the same value in one set: the one lower in the set is the one in the game."""
        la = self.launcher()
        first, second = self.library_mod(la, "Tank Test", 15), self.library_mod(la, "Tank Test Two", 20)
        la.new_set("Both", [first, second])
        self.assertEqual(self.played(la, "both")["state"], "done")
        self.assertEqual(value_in(self.copy()), 20)

    def test_no_mod_ticked_is_said_by_the_page_in_every_language(self):
        """Usual: Save on the set editor with no mod ticked: the page says it itself (set_none_yet, or
        library_empty_for_set with an empty library), in every language, and saves nothing."""
        page = LAUNCHER_UI.read_text(encoding="utf-8")
        self.assertIn("ed.problem = state.library.length ? w.set_none_yet : w.library_empty_for_set;", page)
        for key in ("set_none_yet", "library_empty_for_set"):
            with self.subTest(key=key):
                self.assert_worded({lang: self.launcher_words(lang)[key] for lang in LANGS})
        la = self.launcher()
        with self.assertRaises(Exception):
            la.new_set("Nothing", [])
        self.assertEqual([s["id"] for s in la.mod_sets()], ["vanilla"])

    def test_a_mod_gone_from_the_library(self):
        """Unusual: a mod of a set removed from the library: the set says it's missing and how to add it, its Play
        button is off (app.js: Play disabled while the set has a mistake), and a Play asked all the same is refused
        before anything is built; the copy as it was."""
        la = self.launcher()
        mod = self.library_mod(la, "Tank Test", 15)
        la.new_set("Mine", [mod])
        self.assertEqual(self.played(la, "mine")["state"], "done")
        la.remove_mod(mod)
        (mine,) = [s for s in la.mod_sets() if s["id"] == "mine"]
        self.assertIn(mod, mine["error"])
        self.assertIn("play.disabled = state.playing || Boolean(set.error)", LAUNCHER_UI.read_text(encoding="utf-8"))
        j = self.played(la, "mine", "fr")
        print("\na mod gone, French:", j["message"])
        self.assertEqual((j["state"], len(self.started), value_in(self.copy())), ("failed", 1, 15))

    def test_the_mod_check_when_a_mod_is_added(self):
        """Usual: a mod with a map file loose in its maps folder (the build won't look there) added to the library: the
        Launcher says it at once (add_mod's problems), the mod is in the library all the same, and its set plays."""
        la = self.launcher()
        folder = self.a_mod("Tank Test", 15)
        (folder / "maps").mkdir(exist_ok=True)
        (folder / "maps" / "scenario.toml").write_text("", encoding="utf-8")
        added = la.add_mod(str(folder))
        self.assertEqual([p["file"] for p in added["problems"]], ["maps/scenario.toml"])
        la.new_set("Mine", [added["mod"]["id"]])
        self.assertEqual(self.played(la, "mine")["state"], "done")


class AModsTextSavedByExcel(Sets):
    def test_added_to_the_library(self):
        """Unusual (finding P-1, the Launcher's side, its PROPOSED FIX): a mod whose text file was saved by Excel as "CSV
        (Comma delimited)" (the PC's ANSI code page, an accented letter in it) added to the library: refused, its words
        naming the file, never Python's. Before: "This mod couldn't be read ('utf-8' codec can't decode byte 0xe9 in
        position 56: invalid continuation byte).\""""
        from test_scenarios_play_base import PYTHON_WORDS
        from test_scenarios_play_studio import CSV
        folder = self.a_mod()
        (folder / "text").mkdir(exist_ok=True)
        (folder / "text" / "names.csv").write_bytes(CSV.encode("cp1252"))
        la = self.launcher()
        with self.assertRaises(Exception) as said:
            la.add_mod(str(folder))
        print("\nP-1 Launcher's add:", said.exception)
        self.assertIn("names.csv", str(said.exception))
        for bad in PYTHON_WORDS + ("codec", "UnicodeDecodeError"):
            self.assertNotIn(bad, str(said.exception))


class JoinCodes(Sets):
    def test_before_any_play_after_it_and_compared(self):
        """Usual: before any Play the copy has no join code (the page: press Play once); after Play it has one;
        compared with itself: the same; compared with the code of a set with another mod: not the same, with the
        mods that differ named."""
        la = self.launcher()
        self.assertEqual((la.fair_play()["built"], la.fair_play()["code"]), (False, None))
        self.assert_worded({lang: self.launcher_words(lang)["fair_not_built"] for lang in LANGS})
        first = self.library_mod(la, "Tank Test", 15)
        la.new_set("Mine", [first])
        self.played(la, "mine")
        mine = la.fair_play()["code"]
        self.assertTrue(mine.startswith("RUSE1:"), mine)
        self.assertEqual(la.compare_code(mine), {"same": True, "differences": []})
        other = self.library_mod(la, "Other Tanks", 20)
        la.new_set("Other", [other])
        self.played(la, "other")
        theirs = la.fair_play()["code"]
        self.played(la, "mine")
        compared = la.compare_code(theirs)
        self.assertFalse(compared["same"])
        self.assertTrue(any("other-tanks" in d for d in compared["differences"]), compared)

    @unittest.expectedFailure    # finding P-3: the set's join code box shows another build's code
    def test_the_code_shown_on_a_sets_page_is_that_sets(self):
        """Unusual: a set played (its code sent to a friend), then Test in game in the Studio after one more change to
        the same mod: the one modded copy is the Studio's test now. On the set's page, Join code (app.js: the box is on
        the set's page) shows that build's code, with nothing saying it isn't the set's; compared with the friend's
        code: "Same mods and versions, but the games still differ...". A Play builds the set again, and its code is
        the first one."""
        la = self.launcher()
        mod = self.library_mod(la, "Tank Test", 15)
        la.new_set("Mine", [mod])
        self.played(la, "mine")
        sent = la.fair_play()["code"]
        self.page.edit(M4, "SeuilMort", 22)
        self.assertEqual(self.in_game()["state"], "done")
        shown = la.fair_play()
        compared = la.compare_code(sent)
        print("\nP-3 shown after the Studio's test:", shown["code"], shown["why"], shown["problems"], "|",
              compared["differences"])
        self.played(la, "mine")
        self.assertEqual(la.fair_play()["code"], sent)
        self.assertTrue(shown["code"] in (None, sent) or shown["why"], shown)


if __name__ == "__main__":
    unittest.main()
