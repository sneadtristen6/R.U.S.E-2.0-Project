"""Where modded copies go (rusemod.play.instances_dir): the folder chosen in either app's Settings (settings.json
`instances_dir`), else $RUSE_INSTANCES, else the recommended place, RUSE-Instances on the game's drive. The owner,
2026-10-09: "user should be able to choose where files go, game should not force it into one spot. It can have a
recommended spot maybe but everything should be customizable". On a made-up game folder; nothing starts for real."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_build import price, write_mod
from test_launcher import Base as LauncherBase, wait_for
from rusemod import doctor
from rusemod.backup import backups_dir
from rusemod.community import private_paths_out
from rusemod.home import save_settings, settings
from rusemod.play import (INSTANCES_ENV, INSTANCES_SETTING, SHARED, copies_view, instances_choice, instances_dir,
                          keep_instances_dir, other_drive, recommended_instances_dir, shared_copy)
from ruse_studio.api import StudioApi

OTHER = "Z:\\Copies\\RUSE-Instances"  # a drive this PC hasn't got: never written to


class WhereCopiesGo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "Games" / "R.U.S.E"
        self.game.mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        self.home = root / "home"
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop(INSTANCES_ENV, None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_the_recommended_place_is_on_the_games_drive(self):
        recommended = Path(self.game.anchor) / "RUSE-Instances"
        self.assertEqual(recommended_instances_dir(self.game), recommended)
        self.assertEqual(instances_choice(self.game, self.home), (recommended, "recommended"))
        self.assertEqual(instances_dir(self.game), recommended)  # without the platform folder: no setting to read
        self.assertEqual(instances_dir(self.game, self.home), recommended)
        self.assertEqual(shared_copy(self.game, home=self.home), recommended / SHARED)
        self.assertEqual(backups_dir(self.game), Path(self.game.anchor) / "RUSE-Backup")  # beside the copies
        self.assertEqual(instances_choice(None, self.home), (None, "recommended"))  # no game: no drive to go by

    def test_the_setting_wins_over_the_variable_over_the_recommended_place(self):
        chosen = Path(self.tmp.name, "Chosen")
        os.environ[INSTANCES_ENV] = OTHER
        self.assertEqual(instances_choice(self.game, self.home), (Path(OTHER), "env"))
        self.assertEqual(instances_dir(self.game), Path(OTHER))  # the variable needs no platform folder
        keep_instances_dir(self.home, chosen, self.game)
        self.assertEqual(settings(self.home)[INSTANCES_SETTING], str(chosen))
        self.assertEqual(instances_choice(self.game, self.home), (chosen, "chosen"))
        self.assertEqual(instances_dir(self.game, self.home), chosen)
        self.assertEqual(shared_copy(self.game, home=self.home), chosen / SHARED)
        self.assertEqual(shared_copy(self.game, Path(OTHER), self.home), Path(OTHER) / SHARED)  # given: as before
        self.assertEqual(backups_dir(self.game, self.home), chosen.parent / "RUSE-Backup")  # beside the copies
        self.assertEqual(instances_choice(None, self.home), (chosen, "chosen"))  # a chosen folder needs no game
        keep_instances_dir(self.home, None)  # the recommended place again: the variable is next in line
        self.assertNotIn(INSTANCES_SETTING, settings(self.home))
        self.assertEqual(instances_choice(self.game, self.home), (Path(OTHER), "env"))
        del os.environ[INSTANCES_ENV]
        self.assertEqual(instances_choice(self.game, self.home)[1], "recommended")

    def test_a_blank_or_odd_setting_counts_as_none(self):
        save_settings(self.home, {INSTANCES_SETTING: "  "})
        self.assertEqual(instances_choice(self.game, self.home)[1], "recommended")
        save_settings(self.home, {INSTANCES_SETTING: ["not", "a", "path"]})
        self.assertEqual(instances_choice(self.game, self.home)[1], "recommended")

    def test_a_folder_inside_the_game_is_refused(self):
        insides = [self.game, self.game / "Copies"]
        if os.name == "nt":  # Windows paths compare without case; elsewhere the upper-cased name is another folder
            insides.append(str(self.game).upper())
        for inside in insides:
            with self.assertRaisesRegex(ValueError, "inside the R.U.S.E. folder"):
                keep_instances_dir(self.home, inside, self.game)
        self.assertNotIn(INSTANCES_SETTING, settings(self.home))
        keep_instances_dir(self.home, self.game.parent / "R.U.S.E-copies", self.game)  # only looks alike: fine
        self.assertEqual(settings(self.home)[INSTANCES_SETTING], str(self.game.parent / "R.U.S.E-copies"))
        keep_instances_dir(self.home, self.game.parent, self.game)  # the game's own parent is outside it
        self.assertEqual(settings(self.home)[INSTANCES_SETTING], str(self.game.parent))

    def test_the_other_settings_are_kept(self):
        elsewhere = str(Path(self.tmp.name, "Elsewhere"))
        save_settings(self.home, {"game_dir": str(self.game), "prefs": {"launcher": {"lang": "fr"}}})
        keep_instances_dir(self.home, elsewhere)
        self.assertEqual(settings(self.home), {"game_dir": str(self.game), "prefs": {"launcher": {"lang": "fr"}},
                                               INSTANCES_SETTING: elsewhere})

    @unittest.skipUnless(os.name == "nt", "drive letters: Windows only")
    def test_another_drive_is_seen_by_the_drive_letter(self):
        self.assertFalse(other_drive(self.game, Path(self.game.anchor) / "RUSE-Instances"))
        self.assertTrue(other_drive(self.game, Path(OTHER)))
        same = copies_view(self.game, self.home)
        self.assertEqual(same, {"path": str(Path(self.game.anchor) / "RUSE-Instances"), "how": "recommended",
                                "recommended": str(Path(self.game.anchor) / "RUSE-Instances"),
                                "drive": os.path.splitdrive(str(self.game))[0], "other_drive": False})
        keep_instances_dir(self.home, OTHER, self.game)
        other = copies_view(self.game, self.home)
        self.assertEqual((other["path"], other["how"], other["other_drive"]), (OTHER, "chosen", True))
        fixed = copies_view(self.game, self.home, Path(self.tmp.name, "given"))
        self.assertEqual((fixed["path"], fixed["how"], fixed["other_drive"]), (str(Path(self.tmp.name, "given")),
                                                                              "fixed", False))
        none = copies_view(None, self.home)
        self.assertEqual(none, {"path": OTHER, "how": "chosen", "recommended": None, "drive": None, "other_drive": False})
        keep_instances_dir(self.home, None)
        self.assertEqual(copies_view(None, self.home)["path"], None)

    @unittest.skipUnless(os.name == "nt", "the other-drive part needs drive letters: Windows only")
    def test_the_troubleshooter_says_where_copies_go_and_why(self):
        copies = Path(self.tmp.name, "RUSE-Instances")
        got = {f["key"]: f for f in doctor.checks(self.game, copies, lambda: True, lambda: [], how="chosen")}
        self.assertEqual((got["drive"]["level"], got["drive"]["say"]), ("ok", "doc_copies_chosen"))
        self.assertEqual(got["drive"]["data"]["path"], str(copies))
        self.assertEqual(got["drive"]["data"]["how"], "chosen")
        self.assertNotIn("other_drive", got)
        for how, say in (("env", "doc_copies_env"), ("recommended", "doc_copies_recommended")):
            findings = doctor.checks(self.game, copies, lambda: True, lambda: [], how=how)
            self.assertEqual([f["say"] for f in findings if f["key"] == "drive"], [say])
        plain = doctor.checks(self.game, copies, lambda: True, lambda: [])  # without the why: as before
        self.assertEqual([f["say"] for f in plain if f["key"] == "drive"], ["doc_drive_ok"])
        text = doctor.report(doctor.checks(self.game, copies, lambda: True, lambda: [], how="chosen"), "RUSE Studio",
                             "9.9")
        # the report masks the player's own folders (%LOCALAPPDATA% and so on), the temp folder among them
        self.assertIn(f"[ok] drive: doc_copies_chosen (path={private_paths_out(str(copies))}, fs=", text)
        self.assertIn(", how=chosen)", text)
        # on another drive than the game: each copy is a full copy of the game, said as its own finding (nothing is
        # written there: the drive doesn't exist on this PC, so the write check fails instead)
        elsewhere = {f["key"]: f for f in doctor.checks(self.game, Path(OTHER), lambda: True, lambda: [], how="chosen")}
        self.assertEqual((elsewhere["other_drive"]["level"], elsewhere["other_drive"]["say"]),
                         ("info", "doc_copies_other_drive"))
        self.assertEqual(elsewhere["other_drive"]["data"],
                         {"path": OTHER, "drive": os.path.splitdrive(str(self.game))[0],
                          "recommended": str(Path(self.game.anchor) / "RUSE-Instances")})
        self.assertEqual(elsewhere["write"]["level"], "fail")
        self.assertFalse(Path(OTHER).exists())


class InTheLauncher(LauncherBase):
    """The Launcher's Settings: Where modded copies go (api.copies_folder, choose_copies_folder,
    use_recommended_copies), and a Play building in the chosen folder."""

    def setUp(self):
        super().setUp()
        os.environ.pop(INSTANCES_ENV, None)

    def test_the_settings_control(self):
        chosen = Path(self.tmp.name, "Chosen")
        picks = [str(chosen)]
        api = self.api(instances=None, pick_folder=lambda: picks.pop(0) if picks else None)
        recommended = str(Path(self.game.anchor) / "RUSE-Instances")
        drive = os.path.splitdrive(str(self.game))[0] or self.game.anchor  # a drive letter, or "/" elsewhere
        self.assertEqual(api.copies_folder(), {"path": recommended, "how": "recommended", "recommended": recommended,
                                               "drive": drive, "other_drive": False})
        got = api.choose_copies_folder()
        self.assertEqual((got["path"], got["how"], got.get("message")), (str(chosen), "chosen", None))
        self.assertEqual(settings(self.home)[INSTANCES_SETTING], str(chosen))
        self.assertEqual(api.choose_copies_folder()["path"], str(chosen))  # the dialog cancelled: as it was
        picks.append(str(self.game / "inside"))  # inside the game folder: refused, nothing kept
        refused = api.choose_copies_folder()
        self.assertIn("inside the R.U.S.E. folder", refused["message"])
        self.assertEqual((refused["path"], settings(self.home)[INSTANCES_SETTING]), (str(chosen), str(chosen)))
        self.assertEqual(api.backup_status()["folder"], str(chosen.parent / "RUSE-Backup"))  # beside the copies
        back = api.use_recommended_copies()
        self.assertEqual((back["path"], back["how"]), (recommended, "recommended"))
        self.assertNotIn(INSTANCES_SETTING, settings(self.home))
        self.assertEqual(api.backup_status()["folder"], str(Path(self.game.anchor) / "RUSE-Backup"))
        # given when the launcher started (tests): fixed, so the control can't change it
        given = self.api(pick_folder=lambda: str(chosen))
        self.assertEqual((given.copies_folder()["path"], given.copies_folder()["how"]), (str(self.instances), "fixed"))
        self.assertEqual(given.choose_copies_folder()["how"], "fixed")
        self.assertNotIn(INSTANCES_SETTING, settings(self.home))
        # no game yet: no recommended place to name, but a folder can still be chosen
        none = self.api(game_dir=None, find=lambda: None, instances=None, pick_folder=lambda: str(chosen))
        self.assertEqual(none.copies_folder()["path"], None)
        self.assertEqual(none.choose_copies_folder()["path"], str(chosen))

    def test_a_play_builds_in_the_chosen_folder_and_the_report_says_so(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod])
        chosen = Path(self.tmp.name, "Chosen")
        keep_instances_dir(self.home, chosen, self.game)
        api = self.api(instances=None)
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = chosen / SHARED
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
        self.assertEqual(self.started, [copy / "RUSE.exe"])
        self.assertFalse((self.instances / SHARED).exists())
        report = api.troubleshoot()
        drive = next(f for f in report["findings"] if f["key"] == "drive")
        self.assertEqual((drive["say"], drive["data"]["path"], drive["data"]["how"]),
                         ("doc_copies_chosen", str(chosen), "chosen"))
        self.assertIn(f"doc_copies_chosen (path={private_paths_out(str(chosen))}", report["report"])
        # the variable, with nothing chosen
        keep_instances_dir(self.home, None)
        elsewhere = Path(self.tmp.name, "FromEnv")
        with mock.patch.dict(os.environ, {INSTANCES_ENV: str(elsewhere)}):
            j = wait_for(api, api.play("half")["job"])
            self.assertEqual(j["state"], "done", j)
            self.assertEqual(self.started[-1], elsewhere / SHARED / "RUSE.exe")
            self.assertEqual(api.copies_folder()["how"], "env")
            self.assertEqual(next(f for f in api.troubleshoot()["findings"] if f["key"] == "drive")["say"],
                             "doc_copies_env")
        self.assertTrue((copy / "RUSE.exe").is_file())  # the old folder is never removed by the launcher


class InTheStudio(unittest.TestCase):
    """The Studio's Settings: the same control, through the window's folder dialog, and Test in game's place."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "Games" / "R.U.S.E"
        self.game.mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        self.home = root / "home"
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop(INSTANCES_ENV, None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_the_settings_control(self):
        chosen = Path(self.tmp.name, "Chosen")
        api = StudioApi(game_dir=self.game, home=self.home)
        recommended = str(Path(self.game.anchor) / "RUSE-Instances")
        self.assertEqual((api.copies_folder()["path"], api.copies_folder()["how"]), (recommended, "recommended"))
        self.assertEqual(api.choose_copies_folder()["how"], "recommended")  # no window: no dialog to ask with
        api._window = object()
        with mock.patch("ruse_studio.api.pick_folder", lambda window: str(chosen)):
            got = api.choose_copies_folder()
        self.assertEqual((got["path"], got["how"], got.get("message")), (str(chosen), "chosen", None))
        self.assertEqual(settings(self.home)[INSTANCES_SETTING], str(chosen))
        self.assertEqual(api._copies(self.game), (chosen, "chosen"))  # where Test in game builds
        self.assertEqual(api.backup_status()["folder"], str(chosen.parent / "RUSE-Backup"))
        with mock.patch("ruse_studio.api.pick_folder", lambda window: None):  # cancelled
            self.assertEqual(api.choose_copies_folder()["path"], str(chosen))
        with mock.patch("ruse_studio.api.pick_folder", lambda window: str(self.game / "copies")):
            refused = api.choose_copies_folder()
        self.assertIn("inside the R.U.S.E. folder", refused["message"])
        self.assertEqual(settings(self.home)[INSTANCES_SETTING], str(chosen))
        report = api.troubleshoot()
        self.assertIn(f"doc_copies_chosen (path={private_paths_out(str(chosen))}", report["report"])
        back = api.use_recommended_copies()
        self.assertEqual((back["path"], back["how"]), (recommended, "recommended"))
        self.assertEqual(api._copies(self.game), (Path(recommended), "recommended"))
        # the launcher's choice is the Studio's too (one settings.json), and the other way round
        from ruse_launcher.api import LauncherApi
        launcher = LauncherApi(game_dir=self.game, home=self.home, pick_folder=lambda: str(chosen))
        self.assertEqual(launcher.choose_copies_folder()["how"], "chosen")
        self.assertEqual(api.copies_folder()["path"], str(chosen))
        given = StudioApi(game_dir=self.game, home=self.home, instances=Path(self.tmp.name, "given"))
        self.assertEqual(given.copies_folder()["how"], "fixed")
        self.assertEqual(given._copies(self.game), (Path(self.tmp.name, "given"), "fixed"))


class TheWords(unittest.TestCase):
    """Both apps' Settings use the same words for the control, each in all ten languages (the apps' own words tests
    check every word and every language); the help names the recommended place and the other-drive cost plainly."""

    def test_the_help_tells_the_truth(self):
        from ruse_launcher.api import _words as launcher_words
        from ruse_studio.api import _words as studio_words
        for words in (launcher_words(), studio_words()):
            help_text = words["set_copies_help"]["us"]
            self.assertIn("RUSE-Instances on the game's drive", help_text)
            self.assertIn("On another drive it is a full copy of the game, slower and bigger", help_text)
            self.assertIn("deleted by hand", help_text)
            self.assertIn("RUSE-Backup", help_text)
            self.assertIn("full copy of the game", words["doc_copies_other_drive"]["us"])
            self.assertIn("Settings", words["doc_write_fail"]["us"])  # it no longer says copies must go there
            for key in ("tip_copies_change", "tip_copies_default", "tip_copies_default_off", "tip_copies_fixed"):
                self.assertTrue(words[key]["us"].endswith("."), key)  # one plain sentence on every control


if __name__ == "__main__":
    unittest.main()
