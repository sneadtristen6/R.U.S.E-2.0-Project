"""Scenarios: a player making a new mod in the RUSE Studio (the owner, 2026-11-13 overnight: "Usual and unusual
situations. Player can find themselves in when making new mods in our apps"). Names plain, the page's longest, in every
script the apps' eleven languages use, with spaces, punctuation, only symbols, Windows' reserved names, a trailing dot,
a name already taken, an emoji and a rare kanji; switching between mods and maps; a mod opened again after the Studio
starts again, gone or renamed by hand meanwhile. After each: what the page says, the mod's files, and whether the mod
builds (on the made-up game, as the Studio tests build) and goes out (Export, the Launcher's library).

Each test marked expectedFailure shows a finding (its number in the comment above it; the agent's report lists them);
it passes once the finding is mended."""
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from test_scenarios_units_base import A1, M1, P1, S1, Player
from rusemod import package
from ruse_launcher.api import LauncherApi

# a mod's name as a player of each of the apps' languages might type it (the page takes at most 60 characters)
NAMES = {"us": "Tank Test", "fr": "Chars à l'été", "ger": "Panzer Ü ß Straße", "ita": "Carri armati è più",
         "spa": "Tanques ñandú", "pol": "Czołgi źdźbło", "ru": "Танковый мод", "cz": "Tanky čeřich",
         "jpn": "戦車の改造", "sc": "坦克模组", "fa": "مود تانک‌ها"}
NOT_LATIN = ("ru", "jpn", "sc", "fa")


def wait(api, job: str, seconds: float = 120) -> dict:
    end = time.time() + seconds
    while api.job(job)["state"] == "running" and time.time() < end:
        time.sleep(0.05)
    return api.job(job)


class NewMods(Player):
    """New mod…: the name typed, the folder made, the menus, the start screen, a unit made in it, its build."""

    def made(self, name: str) -> Path:
        folder = self.mod(name)
        self.assertTrue((folder / "mod.toml").is_file())
        self.assertEqual(package.info_of(folder)["name"], name.strip(), "the name typed, kept in mod.toml")
        return folder

    def a_unit_builds(self, folder: Path, unit: str = M1, name: str = "Copy"):
        made = self.call("new_unit", unit, name, 40, -1, -1, False, None)
        errors, ndf, _texts = self.build(folder)
        self.assertEqual(errors, [])
        self.assertEqual(self.value(ndf, made["address"], "ProductionPrice").int_list(), [40] * 5)
        return made

    def test_a_plain_name(self):
        folder = self.made("Tank Test")
        self.assertEqual(folder.name, "tank-test")
        mods = self.call("mods", "mod")
        self.assertEqual((mods["current"], [m["path"] for m in mods["mods"]]), (str(folder), [str(folder)]))
        self.assertEqual([m["name"] for m in self.call("start_mods")["mods"]], ["Tank Test"])
        self.a_unit_builds(folder)

    def test_a_name_in_every_script_is_kept_and_its_mod_builds(self):
        for lang, name in NAMES.items():
            with self.subTest(lang=lang):
                folder = self.made(name)
                self.a_unit_builds(folder, name=f"Copy {lang}")
                self.assertIn(name, [m["name"] for m in self.call("start_mods")["mods"]])   # the start screen
                listed = {m["path"]: m["name"] for m in self.call("your_mods")["mods"]}     # Delete a mod…
                self.assertEqual(listed[str(folder)], name)

    # U-2: the header's mod menu names a mod by its folder, so a name with no Latin letter shows as my-mod, my-mod-2...
    @unittest.expectedFailure
    def test_the_mod_menu_shows_something_of_the_name_typed(self):
        shown = {}
        for lang in NOT_LATIN:
            folder = self.made(NAMES[lang])
            shown[lang] = next(m["name"] for m in self.call("mods", "mod")["mods"] if m["path"] == str(folder))
        # (what the menu shows now: {"ru": "my-mod", "jpn": "my-mod-2", "sc": "my-mod-3", "fa": "my-mod-4"})
        for lang in NOT_LATIN:
            self.assertIn(NAMES[lang], shown[lang], shown)

    def test_the_longest_name_the_page_takes(self):
        for name in ("A" * 60, "Ж" * 60, "戦" * 60, "Panzerkampfwagen VI Ausf. B Königstiger mit Henschel-Turm 1944"[:60]):
            with self.subTest(name=name[:8]):
                folder = self.made(name)
                self.assertLessEqual(len(folder.name), 60)
                self.a_unit_builds(folder, name=name[:60])

    def test_spaces_punctuation_and_only_symbols(self):
        for name, folder_name in (("  My   Mod  ", "my-mod"), ('Tank\'s "Test" <v2>: 50% off!?', "tank-s-test-v2-50-off"),
                                  ("C:\\Mods\\new", "c-mods-new"), ("../../outside", "outside"), ("#@!$%^&*()", None),
                                  ("...", None), ("-", None), ("a/b\\c", "a-b-c")):
            with self.subTest(name=name):
                folder = self.made(name)
                if folder_name is not None:
                    self.assertEqual(folder.name, folder_name)
                self.assertEqual(folder.parent, self.home / "mods")        # never outside the mods folder
                self.a_unit_builds(folder)

    def test_windows_reserved_names(self):
        """CON, NUL, AUX, COM1, LPT1 and con.txt. On this PC's Windows (11, build 26300) a folder of each name can be
        made; NUL's goes to nul-2 (Windows answers that a "nul" is there). Windows 10 isn't tried here."""
        for name in ("CON", "NUL", "AUX", "COM1", "LPT1", "con.txt", "Con"):
            with self.subTest(name=name):
                folder = self.made(name)
                self.assertTrue(folder.is_dir())
                self.a_unit_builds(folder)

    def test_a_trailing_dot_or_space(self):
        dot = self.made("Tanks.")
        self.assertEqual(dot.name, "tanks")
        self.a_unit_builds(dot)
        space = self.made("Tanks ")          # (the page trims it: "Tanks")
        self.assertEqual(space.name, "tanks-2")
        self.a_unit_builds(space)

    def test_a_name_already_taken(self):
        first, second = self.made("Tank Test"), self.made("Tank Test")
        self.assertEqual((first.name, second.name), ("tank-test", "tank-test-2"))
        self.assertEqual(self.call("mods", "mod")["current"], str(second))
        made = self.call("new_unit", M1, "Only in the second", 40, -1, -1, False, None)
        self.call("choose_mod", str(first), "mod", False)
        self.assertNotIn(made["address"], [u["address"] for u in self.call("units")["units"] if u["new"]])
        # a map of that name: a folder of its own too (a mod and a map of one id stopped a tester's build)
        game_map = Path(self.call("new_mod", "Tank Test", "map")["current"])
        self.assertEqual(game_map.name, "tank-test-3")

    # U-1 (mended by the PROPOSED FIX commit after these tests: before it, a name with a character beyond the first
    # 65,536, an emoji or the 𠮷 of 𠮷野家, made no mod, said Python's words, and left a folder whose mod.toml couldn't
    # be read)
    def test_a_name_with_an_emoji_or_a_rare_kanji_makes_a_mod_that_opens(self):
        for name in ("Tanks 🙂", "𠮷野家の戦車"):
            with self.subTest(name=name):
                folder = self.made(name)
                self.a_unit_builds(folder)
                self.restart()                                             # opened again from its files
                self.assertEqual(self.call("mods", "mod")["current"], str(folder))
                self.assertIn(name, [m["name"] for m in self.call("start_mods")["mods"]])


class SwitchingAndReopening(Player):
    """Between mods and maps; the Studio closed and started again; the mod changed by hand meanwhile."""

    def test_switching_between_mods_and_maps(self):
        a = self.mod("Alpha")
        made = self.call("new_unit", M1, "Alpha Tank", 40, -1, -1, False, None)
        game_map = Path(self.call("new_mod", "Beta map", "map")["current"])
        self.assertEqual(self.call("mods", "mod")["current"], str(a))      # the map didn't change the mod
        c = self.mod("Gamma")
        self.assertEqual(self.call("mods", "map")["current"], str(game_map))   # nor the mod the map
        self.assertEqual([u for u in self.call("units")["units"] if u["new"]], [])
        self.call("new_unit", S1, "Gamma Squad", 20, -1, -1, False, None)
        self.call("choose_mod", str(a), "mod", False)
        self.assertEqual([u["address"] for u in self.call("units")["units"] if u["new"]], [made["address"]])
        self.assertEqual(self.build(a)[0], [])
        self.assertEqual(self.build(c)[0], [])

    def test_opened_again_after_the_studio_starts_again(self):
        folder = self.mod("Kept")
        made = self.call("new_unit", P1, "Kept Plane", 70, -1, -1, False, None)
        self.call("edit", made["address"], "SeuilMort", 30, "", "")
        self.api.set_pref("lang", "fr")
        self.restart()
        self.assertEqual(self.api.prefs().get("lang"), "fr")
        self.assertEqual(self.call("mods", "mod")["current"], str(folder))
        unit = self.call("unit", made["address"], "fr")
        self.assertEqual(unit["name"], "Kept Plane")
        rows = {r["prop"]: r for g in unit["groups"] for r in g["rows"]}
        self.assertEqual(rows["SeuilMort"]["edited"], 30)
        self.assertEqual(self.build(folder)[0], [])

    def test_the_mod_folder_deleted_by_hand_while_the_studio_was_closed(self):
        folder = self.mod("Gone")
        self.call("new_unit", M1, "Gone Tank", 40, -1, -1, False, None)
        shutil.rmtree(folder)
        self.restart()
        self.assertEqual(self.call("mods", "mod"), {"mods": [], "kind": "mod", "current": None})
        said = self.refusal("new_unit", A1, "Lost", 40, -1, -1, False, None)
        self.assertEqual(said["us"], "Pick or make a mod first: a new unit is saved in a mod.")
        self.assertEqual(self.english_left(said), [])

    def test_the_mod_folder_renamed_by_hand_while_the_studio_was_closed(self):
        folder = self.mod("Renamed")
        made = self.call("new_unit", M1, "Renamed Tank", 40, -1, -1, False, None)
        moved = folder.with_name("my renamed mod")
        folder.rename(moved)
        self.restart()
        mods = self.call("mods", "mod")
        self.assertIsNone(mods["current"])
        self.assertEqual([m["path"] for m in mods["mods"]], [str(moved)])     # found where it is now
        self.call("choose_mod", str(moved), "mod", False)
        self.assertEqual([u["address"] for u in self.call("units")["units"] if u["new"]], [made["address"]])
        self.assertEqual(self.build(moved)[0], [])

    def test_a_mod_toml_broken_by_hand(self):
        """mod.toml changed by hand into something that can't be read: the page says so in words, nothing is
        written over it."""
        folder = self.mod("Broken")
        broken = '[mod]\nid = "broken"\nname = "Broken\n'
        (folder / "mod.toml").write_text(broken, encoding="utf-8")
        self.restart()
        problems = self.call("check_mod")["problems"]
        self.assertTrue(problems, "the mod check names the broken mod.toml")
        for p in problems:
            self.assert_plain(p.get("problem", ""))
        self.assertEqual((folder / "mod.toml").read_text(encoding="utf-8"), broken)


class DeleteAMod(Player):
    """Delete a mod… (the Recycle Bin a stand-in here: no test fills the PC's bin, as test_studio_duplicate's)."""

    def binned(self, call, *args):
        gone = []

        def to_bin(path):
            gone.append(Path(path))
            shutil.rmtree(path)
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=to_bin):
            return self.call(call, *args), gone

    def test_the_mod_being_edited_deleted_then_a_new_one(self):
        folder = self.mod("Short lived")
        self.call("new_unit", M1, "Short Tank", 40, -1, -1, False, None)
        res, gone = self.binned("delete_mod", str(folder), False)
        self.assertEqual((gone, res["deleted"], res["mod"]["current"]), ([folder], "Short lived", None))
        said = self.refusal("new_unit", M1, "After", 40, -1, -1, False, None)
        self.assertEqual(self.english_left(said), [])
        again = self.mod("Short lived")                                    # its name and folder free again
        self.assertEqual(again, folder)
        self.assertEqual([u for u in self.call("units")["units"] if u["new"]], [])

    def test_a_mod_named_in_russian_deleted_with_its_launcher_copy(self):
        folder = self.mod(NAMES["ru"])
        self.call("new_unit", M1, "Tank", 40, -1, -1, False, None)
        j = wait(self.api, self.call("export_mod", "1.0.0", "", "")["job"])
        self.assertEqual(j["state"], "done", j)
        listed = {m["path"]: m for m in self.call("your_mods")["mods"]}
        self.assertEqual((listed[str(folder)]["name"], listed[str(folder)]["launcher"]), (NAMES["ru"], NAMES["ru"]))
        res, gone = self.binned("delete_mod", str(folder), True)
        self.assertEqual((res["deleted"], res["launcher"], len(gone)), (NAMES["ru"], True, 2))
        self.assertFalse((self.home / "library" / "my-mod").exists())


class TheModGoesOut(Player):
    """Export… and the Launcher's library: the mod's id comes from its name."""

    def launcher(self, home: Path) -> LauncherApi:
        return LauncherApi(game_dir=self.game, home=home, instances=home / "copies", open_url=lambda url: None,
                           start_game=lambda exe: None, steam_running=lambda: True, wait=lambda s: None)

    def exported(self, name: str, unit_name: str, home: Path | None = None) -> dict:
        """A player's PC (`home`, a platform folder of its own): a new mod `name` with one unit, exported."""
        if home is not None:
            self.api, keep = self.studio(home), self.api
            from rusemod.webui import page_api
            self.page = page_api(self.api)
        self.mod(name)
        self.call("new_unit", M1, unit_name, 40, -1, -1, False, None)
        j = wait(self.api, self.call("export_mod", "1.0.0", "A player", f"{name}'s tanks")["job"])
        self.assertEqual(j["state"], "done", j)
        return j

    def test_exported_with_an_author_and_description_in_every_script(self):
        """Export…'s boxes: an author and a description in other scripts, an emoji, quotes and a line break; the file,
        the Launcher's library and the list entry ("Share your mod") read them back."""
        from rusemod import mod_index
        self.mod("Words out")
        self.call("new_unit", M1, "Tank", 40, -1, -1, False, None)
        author, about = 'Иван "Ваня" 山田 🙂', "Танки сильнее.\nTanks 🙂 are \"tougher\" & 𠮷."
        j = wait(self.api, self.call("export_mod", "1.0.0", author, about)["job"])
        self.assertEqual(j["state"], "done", j)
        info = package.check(j["result"]["path"])
        self.assertEqual(info["authors"], [author])
        self.assertIn("Танки сильнее.", info["description"])
        listed, problems = mod_index.parse("format = 1\n" + j["result"]["entry"].replace('download = ""',
                                                                                        'download = "https://x/t"'))
        self.assertEqual((problems, listed[0]["author"]), ([], author))
        self.assertEqual(self.call("mod_info")["author"], author)            # kept for the next Export

    def test_exported_and_in_the_launchers_library(self):
        for lang in ("us", "ru", "jpn"):
            with self.subTest(lang=lang):
                j = self.exported(NAMES[lang], f"Tank {lang}")
                info = package.check(j["result"]["path"])
                self.assertEqual(info["name"], NAMES[lang])
                self.assertTrue(any("In the Launcher's mod library as" in line for line in j["lines"]), j["lines"])

    # U-3: every mod named with no Latin letter gets the id my-mod on every PC (Latin names: the same id for the same
    # name), and the Launcher's library keeps one mod per id: the second replaces the first, which is deleted
    @unittest.expectedFailure
    def test_two_players_mods_named_in_russian_and_japanese_both_go_in_one_launcher(self):
        a = Path(self.exported(NAMES["ru"], "Russian Tank", Path(tempfile.mkdtemp(dir=self.tmp.name)))["result"]["path"])
        b = Path(self.exported(NAMES["jpn"], "Japanese Tank", Path(tempfile.mkdtemp(dir=self.tmp.name)))["result"]["path"])
        launcher = self.launcher(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        launcher.add_mod(str(a))
        second = launcher.add_mod(str(b))
        self.assertFalse(second["replaced"], "the second player's mod replaced the first's")
        self.assertEqual(sorted(m["name"] for m in launcher.library()), sorted([NAMES["ru"], NAMES["jpn"]]))

    # U-3 too: Export puts the mod in this PC's Launcher library, replacing (deleting) another mod of the same id
    # installed there, and says "the older version replaced"
    @unittest.expectedFailure
    def test_export_never_replaces_another_players_mod_installed_here(self):
        other = Path(self.exported(NAMES["sc"], "Chinese Tank", Path(tempfile.mkdtemp(dir=self.tmp.name)))["result"]["path"])
        mine = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.launcher(mine).add_mod(str(other))                     # installed from the list, say
        j = self.exported(NAMES["ru"], "My Tank", mine)              # then a mod of my own, named in Russian
        names = sorted(m["name"] for m in self.launcher(mine).library())
        self.assertEqual(names, sorted([NAMES["sc"], NAMES["ru"]]), j["lines"])

    def test_what_export_does_to_a_mod_of_the_same_id_now(self):
        """U-3 as it is now, on record (passes on the code as it is; goes once U-3 is mended)."""
        other = Path(self.exported(NAMES["sc"], "Chinese Tank", Path(tempfile.mkdtemp(dir=self.tmp.name)))["result"]["path"])
        mine = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.launcher(mine).add_mod(str(other))
        j = self.exported(NAMES["ru"], "My Tank", mine)
        self.assertEqual(package.check(other)["id"], "my-mod")
        self.assertEqual([m["name"] for m in self.launcher(mine).library()], [NAMES["ru"]])   # the other one: gone
        self.assertIn(f"In the Launcher's mod library as {NAMES['ru']} 1.0.0 (the older version replaced): tick it "
                      f"in a mod set and press Play.", j["lines"])


if __name__ == "__main__":
    unittest.main()
