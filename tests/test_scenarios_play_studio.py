"""Scenarios: the RUSE Studio's check of a mod and its Test in game, as a player meets them (the base, its made-up game
and its stand-ins: tests/test_scenarios_play_base.py): a mod that builds, in the player's language, and clicked again
with nothing changed; clicked twice while it builds, with the Launcher's Play meanwhile; a value changed while it
builds; the Maps tab's map and the Units tab's mod together; the Launcher's Play between two tests on the one modded
copy; the game still running from that copy; the check's problems and their fixes (Set aside, Take out what it left)
and fixes that can't be done; a mod's own files saved by another program in another encoding. Each ends with what the
page says (every language where it is the Studio's own words), the files, and what was built and started.

FOR: the Test in game and Play scenarios (release 0.9.8.20, overnight 2026-11-14). USED-BY: the scenarios' run and
report."""
import threading
import unittest
from pathlib import Path
from unittest import mock

from test_scenarios_play_base import LANGS, M4, PYTHON_WORDS, PlayScenario, fill


def value_in(copy: Path) -> int:
    """The M4's SeuilMort in the modded copy's unit data (what the game would read)."""
    from rusemod import Edat, Ndf
    pack = Edat((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
    return Ndf(pack.read(pack.find("everything.cpp.gladndfbin"))).objects[0].get(1).scalar()


class SlowBuild:
    """The build held at its start until `go` is set (a real build, only later): the time a player has to click again
    or edit meanwhile."""

    def __init__(self):
        from rusemod import build
        self.real, self.inside, self.go = build.build_and_write, threading.Event(), threading.Event()

    def __call__(self, *a, **kw):
        self.inside.set()
        self.go.wait(20)
        return self.real(*a, **kw)

    def patched(self):
        return mock.patch("rusemod.play.build_and_write", self)


class AModThatBuilds(PlayScenario):
    def test_test_in_game_in_the_players_language_and_again_unchanged(self):
        """Usual: a mod with one value changed, the check finds nothing; Test in game in French builds the one modded
        copy (its lines in French) and starts the game from it, the value in the copy; clicked again with nothing
        changed, nothing is built (said in French) and the game starts again."""
        self.a_mod()
        self.assertEqual(self.problems(), [])
        j = self.in_game("fr")
        self.assertEqual(j["state"], "done", j)
        w = self.words("fr")
        self.assertTrue(any(line.startswith("Construction de la copie moddée") for line in j["lines"]), j["lines"])
        self.assertEqual((self.started, value_in(self.copy())), ([self.exe_of(self.copy())], 15))
        again = self.in_game("fr")
        self.assertEqual((again["state"], again["lines"][0]), ("done", w["play_unchanged"]))
        self.assertEqual(len(self.started), 2)


class ClickedTwice(PlayScenario):
    def test_a_second_click_and_the_launchers_play_while_it_builds(self):
        """Usual: Test in game clicked, and while its build runs, clicked again: refused in words in every language,
        nothing more built; the Launcher's Play meanwhile is refused too (the one copy is being built), nothing started
        by it. The first test then ends as usual: the game started once."""
        folder = self.a_mod()
        la = self.launcher()
        la.add_mod(str(folder))
        la.new_set("Mine", [folder.name])
        slow = SlowBuild()
        with slow.patched():
            first = self.page.test_in_game()["job"]
            self.assertTrue(slow.inside.wait(20))
            self.assert_worded(self.refused("test_in_game"), "A test is already being built: wait for it to finish.")
            played = self.played(la, "mine")
            slow.go.set()
            j = self.wait(first)
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(played["state"], "failed", played)
        print("\nLauncher's Play while the Studio builds:", played["message"])
        self.assertEqual(self.started, [self.exe_of(self.copy())])


class ChangedWhileItBuilds(PlayScenario):
    def test_a_value_changed_during_the_build_builds_again_next_time(self):
        """Usual: Test in game clicked, and while it builds the player changes the value again on the unit's page (the
        page lets him). The copy may hold the old value; the next Test in game builds again (never "nothing changed")
        and the copy has the new one."""
        self.a_mod(value=15)
        slow = SlowBuild()
        with slow.patched():
            first = self.page.test_in_game()["job"]
            self.assertTrue(slow.inside.wait(20))
            self.page.edit(M4, "SeuilMort", 30)
            slow.go.set()
            self.assertEqual(self.wait(first)["state"], "done")
        j = self.in_game()
        self.assertEqual(j["state"], "done", j)
        self.assertNotEqual(j["lines"][0], self.words("us")["play_unchanged"])
        self.assertEqual(value_in(self.copy()), 30)


class TheMapAndTheMod(PlayScenario):
    def test_a_map_folder_and_a_mod_of_one_name_together(self):
        """Usual: the Units tab's mod and the Maps tab's map, both called "Normandy", the map's folder changing the same
        value as the mod: Test in game builds both into the copy (the map after the mod, as the Studio builds them), and
        the map's value is the one in the game."""
        mod = self.a_mod("Normandy", 15)
        made = Path(self.page.new_mod("Normandy", "map")["current"])
        (made / "src").mkdir(parents=True, exist_ok=True)
        (made / "src" / "ground.rndf").write_text(f"patch {M4} ( SeuilMort = 40 )", encoding="utf-8")
        self.assertEqual((self.api._mod_dir(), self.api._map_dir()), (mod, made))
        j = self.in_game()
        self.assertEqual(j["state"], "done", j)
        print("\nmap and mod lines:", [ln for ln in j["lines"] if "order" in ln or "warning" in ln.lower()])
        self.assertEqual(value_in(self.copy()), 40)


class TheLaunchersPlayBetweenTwoTests(PlayScenario):
    def test_the_one_copy_built_by_each_app_in_turn(self):
        """Usual: Test in game (15); the Launcher plays a set of another mod (20) into the same copy; Test in game
        again: built again (the copy holds the Launcher's set now), 15 in the game again."""
        self.a_mod("Tank Test", 15)
        self.assertEqual(self.in_game()["state"], "done")
        other = Path(self.page.new_mod("Other Tanks")["current"])
        self.page.edit(M4, "SeuilMort", 20)
        la = self.launcher()
        la.add_mod(str(other))
        la.new_set("Others", [other.name])
        self.assertEqual(self.played(la, "others")["state"], "done")
        self.assertEqual(value_in(self.copy()), 20)
        self.page.choose_mod(str(self.home / "mods" / "tank-test"))
        j = self.in_game()
        self.assertEqual(j["state"], "done", j)
        self.assertNotEqual(j["lines"][0], self.words("us")["play_unchanged"])
        self.assertEqual(value_in(self.copy()), 15)


class TheGameStillRunning(PlayScenario):
    def test_the_game_running_from_the_copy(self):
        """Unusual: the game is still running from the modded copy (started by an earlier test) and the player clicks
        Test in game after changing a value: refused before anything is built, the copy as it was, nothing started."""
        self.a_mod("Tank Test", 15)
        self.assertEqual(self.in_game()["state"], "done")
        exe = self.exe_of(self.copy())
        self.page.edit(M4, "SeuilMort", 16)
        with mock.patch("rusemod.instance.game_running", lambda dst: [(4242, str(exe))]):
            j = self.in_game("fr")
        print("\ngame still running, French:", j["message"])
        self.assertEqual((j["state"], value_in(self.copy()), len(self.started)), ("failed", 15, 1))


class TheChecksFixes(PlayScenario):
    def test_set_aside_a_broken_changes_file(self):
        """Usual: a changes file of the mod broken by hand (a line cut short): the check names it with Set aside; Set
        aside renames it beside it (never deleted), the check finds nothing, and Test in game builds the mod's other
        changes."""
        folder = self.a_mod()
        (folder / "src" / "extra.rndf").write_text(f"patch {M4} ( SeuilMort = ", encoding="utf-8")
        found = self.page.check_mod()["problems"]
        self.assertEqual([f["fix"] for p in found for f in p["fixes"]], ["set_aside"], found)
        out = self.page.fix_problem({"fix": "set_aside", "file": "src/extra.rndf"})
        self.assertFalse((folder / "src" / "extra.rndf").exists())
        self.assertTrue(Path(out["kept"]).is_file())
        self.assertEqual(out["problems"], [])
        self.assertEqual(self.in_game()["state"], "done")
        self.assertEqual(value_in(self.copy()), 15)

    def test_a_problem_in_the_maps_own_folder(self):
        """Usual: the Maps tab's map is a folder of its own, and a changes file in it is broken: the check names it
        as the map's, with Set aside there; Set aside on it leaves the mod's files alone, and Test in game builds both."""
        mod = self.a_mod()
        made = Path(self.page.new_mod("My Map", "map")["current"])
        (made / "src").mkdir(parents=True, exist_ok=True)
        (made / "src" / "ground.rndf").write_text(f"patch {M4} ( SeuilMort = ", encoding="utf-8")
        found = self.page.check_mod()["problems"]
        self.assertEqual([(p["where"], [f["fix"] for f in p["fixes"]]) for p in found], [("map", ["set_aside"])])
        mine = sorted(p.name for p in (mod / "src").iterdir())
        out = self.page.fix_problem({"fix": "set_aside", "file": "src/ground.rndf", "where": "map"})
        self.assertTrue(Path(out["kept"]).is_relative_to(made))
        self.assertEqual((out["problems"], sorted(p.name for p in (mod / "src").iterdir())), ([], mine))
        self.assertEqual(self.in_game()["state"], "done")

    def test_take_out_what_it_left(self):
        """Usual (a unit deleted half way by an older Studio left its Custom uniform file): Test in game stops on it,
        its mistake said in the player's language with Take out what it left; that takes the file out, the test then
        builds, and the same fix again is refused in words in every language."""
        folder = self.a_mod()
        models = folder / "files" / "models"
        models.mkdir(parents=True, exist_ok=True)
        (models / "Descriptor_Unit_Gone.copy.toml").write_text('of = ["x"]\n', encoding="utf-8")
        j = self.in_game("fr")
        self.assertEqual(j["state"], "failed", j)
        self.api.set_pref("lang", "fr")
        found = self.page.test_problems()["problems"]
        self.api.set_pref("lang", "us")
        self.assertEqual(len(found), 1)
        self.assertIn("aucun mod de l'ensemble ne crée d'unité Descriptor_Unit_Gone", found[0]["text"])
        (fix,) = found[0]["fixes"]
        self.assert_worded({lang: self.words(lang)["test_fix_unit_leftovers"] for lang in LANGS})
        done = self.page.test_fix(fix)
        self.assertEqual(done["done"], "Descriptor_Unit_Gone: taken out (files/models/Descriptor_Unit_Gone.copy.toml)")
        self.assertFalse((models / "Descriptor_Unit_Gone.copy.toml").exists())
        self.assertEqual(self.in_game()["state"], "done")
        self.assert_worded(self.refused("test_fix", fix),
                           "Nothing that Descriptor_Unit_Gone left behind is in the mod any more, or it is a unit the "
                           "mod or the game has.")

    def held_and_set_aside(self) -> tuple:
        folder = self.a_mod()
        bad = folder / "src" / "extra.rndf"
        bad.write_text(f"patch {M4} ( SeuilMort = ", encoding="utf-8")
        held = open(bad, "rb")
        try:
            said = self.refused("fix_problem", {"fix": "set_aside", "file": "src/extra.rndf"})
        finally:
            held.close()
        return bad, said

    def test_a_fix_that_cant_be_done_the_file_is_held(self):
        """Unusual: Set aside on a broken changes file another program has open (Windows won't let it be renamed):
        refused in words in every language, the file as it was; once let go, Set aside works."""
        bad, said = self.held_and_set_aside()
        print("\nset aside a held file:", said["us"], "|", said["fr"])
        self.assertTrue(bad.is_file())
        self.assert_worded(said)
        self.assertTrue(Path(self.page.fix_problem({"fix": "set_aside", "file": "src/extra.rndf"})["kept"]).is_file())

    def test_the_held_file_is_the_one_named(self):
        """Finding P-5, its PROPOSED FIX: the refusal named the file Set aside would have made (extra.rndf.broken:
        api.file_named takes the second file of a rename, as for a file put in another's place), not the one another
        program holds (extra.rndf). Now the held one."""
        bad, said = self.held_and_set_aside()
        self.assertNotIn(".broken", said["us"])
        self.assertIn(str(bad), said["us"])

    def test_the_held_folder_is_the_one_named(self):
        """Finding P-5's class, its PROPOSED FIX: the check's Rename fix (a map folder named after the map's title,
        rename_map_folder) on a folder with a file another program has open named the folder it would have made
        (maps/SuperCrossRoads4), not the one held (maps/Blitz). Now the held one."""
        folder = self.a_mod()
        source = folder / "maps" / "Blitz"
        source.mkdir(parents=True)
        (source / "scenario.toml").write_text("", encoding="utf-8")
        held = open(source / "scenario.toml", "rb")
        try:
            said = self.refused("rename_map_folder", "Blitz", "SuperCrossRoads4")
        finally:
            held.close()
        print("\nP-5 rename of a held folder:", said["us"])
        self.assertTrue(source.is_dir())
        self.assertNotIn("SuperCrossRoads4", said["us"])
        self.assertIn(str(source), said["us"])

    @unittest.expectedFailure    # finding P-4: the check passes mods the build stops on (SQ-7's class)
    def test_the_check_says_what_test_in_game_will_stop_on(self):
        """The check before Test in game (check_mod: "Every file of the current mod read as the build reads it") finds
        nothing in a mod the build then stops on: a patch of an object the game hasn't got, and what a unit deleted
        half way left (rusemod.modcheck loads the mod; the build's own checks run only in the build)."""
        folder = self.a_mod()
        (folder / "src" / "extra.rndf").write_text("patch $/GFX/Everything/Nope ( SeuilMort = 1 )", encoding="utf-8")
        models = folder / "files" / "models"
        models.mkdir(parents=True, exist_ok=True)
        (models / "Descriptor_Unit_Gone.copy.toml").write_text('of = ["x"]\n', encoding="utf-8")
        checked = self.problems()
        j = self.in_game()
        print("\nP-4 check:", checked, "| Test in game:", j["state"], j.get("errors"))
        self.assertEqual(j["state"], "failed")
        self.assertEqual(len(checked), len(j["errors"] or []))


CSV = "key,us,fr\nDescriptor_Unit_M4_Sherman,Sherman,Char moyen é\n"


class ModFilesSavedElsewhere(PlayScenario):
    """A mod's own text files edited outside the Studio and saved by another program its own way: Excel's "CSV (Comma
    delimited)" (the PC's ANSI code page), Notepad's "Unicode" (UTF-16), Notepad's "UTF-8 with BOM"."""

    def said(self, rel: str, data: bytes) -> tuple:
        folder = self.a_mod()
        f = folder / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data(f.read_text(encoding="utf-8")) if callable(data) else data)
        from ruse_studio.api import StudioError
        try:
            checked = self.page.check_mod()["problems"]
        except StudioError as exc:
            checked = f"refused: {exc}"
        except Exception as exc:   # noqa: BLE001 - what reaches the page: an error that isn't the Studio's own
            checked = f"{type(exc).__name__}: {exc}"
        j = self.in_game("fr")
        return checked, j

    def assert_named(self, rel: str, checked, j) -> None:
        print(f"\n{rel}: check: {checked} | Test in game: {j['message']}")
        self.assertIsInstance(checked, list, checked)
        self.assertTrue(any(Path(rel).name in (p.get("problem") or "") for p in checked), checked)
        self.assertIn(Path(rel).name, j["message"])
        for bad in PYTHON_WORDS + ("UnicodeDecodeError", "codec"):
            self.assertNotIn(bad, j["message"])

    def test_a_text_file_saved_by_excel(self):
        """Finding P-1, its PROPOSED FIX: Excel's "CSV (Comma delimited)" with an accented letter. Before, the check
        stopped on Python's UnicodeDecodeError (no problem listed, no Set aside) and Test in game said "Something went
        wrong: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 56", no file named. Now both name
        the file and its line and say how to save it as UTF-8; the check offers Set aside."""
        checked, j = self.said("text/names.csv", CSV.encode("cp1252"))
        self.assert_named("text/names.csv", checked, j)
        self.assertIn("text/names.csv:2:", j["message"])
        self.assertEqual([f["fix"] for p in checked for f in p["fixes"]], ["set_aside"])

    def test_a_changes_file_saved_as_unicode(self):
        """Finding P-1, its PROPOSED FIX: Notepad's "Unicode" (UTF-16): named, never Python's words."""
        checked, j = self.said("src/studio.rndf", lambda text: text.encode("utf-16"))
        self.assert_named("src/studio.rndf", checked, j)

    def test_a_changes_file_saved_as_utf8_with_a_bom(self):
        """Finding P-2, its PROPOSED FIX: Notepad's "UTF-8 with BOM" is UTF-8 all the same (the mod's .csv files were
        read past a BOM already). Before, the changes file was refused ("src/studio.rndf:1:1: can't read '\\ufeff// Made
        by '"), and the check's only fix, Set aside, took the Studio's changes file, every change of the mod, out of
        it. Now it builds, and the Studio reads its own changes as before."""
        checked, j = self.said("src/studio.rndf", lambda text: b"\xef\xbb\xbf" + text.encode("utf-8"))
        print("\nP-2 check:", checked, "| Test in game:", j["message"])
        self.assertEqual((checked, j["state"]), ([], "done"))
        self.assertEqual(value_in(self.copy()), 15)
        self.assertEqual(self.page.edited(), [M4])    # (the Studio's own reading of its changes: the M4's)


if __name__ == "__main__":
    unittest.main()
