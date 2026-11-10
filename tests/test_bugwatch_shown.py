"""Bug Watch counts what it was built to count beside calls and jobs (rusemod.bugwatch; the server's PAYLOADS.md):
`messages`, the problems the window shows the player, by key, and `updates`, offered, installed and failed.

Players' reports (2026-11-02 to 11-08) had 14 of 36 "New mod set" tries refused with only "LauncherError" to say why,
and `messages` empty and `updates` 0, 0, 0 in every report although players updated: nothing called the counting.
No network, no game: a made-up Launcher home and made-up releases.
"""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rusemod import bugwatch, webui  # noqa: E402
from ruse_launcher.api import LauncherApi  # noqa: E402
from test_update import App  # noqa: E402


class Shown(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._current = bugwatch.Watch(self.home, "launcher", "0.4.8.19", opener=mock.Mock())

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def day(self) -> dict:
        return bugwatch._current.days[bugwatch._today()]

    def test_a_refused_mod_set_is_counted_by_its_key(self):
        api = LauncherApi(home=self.home, game_dir=Path(self.tmp.name) / "nowhere", find=lambda: None)
        page = webui.page_api(api)
        typed = "Nick's secret set"
        with self.assertRaisesRegex(Exception, "Tick at least one mod"):
            page.new_set(typed, [])            # a name typed, no mod ticked (the editor's Create, or Enter in the name)
        with self.assertRaisesRegex(Exception, "Give the mod set a name"):
            page.new_set("  ", ["x"])
        with self.assertRaisesRegex(Exception, "can't be saved"):
            page.new_set(typed, ["not-in-the-library"])
        with self.assertRaisesRegex(Exception, "only be in a mod set once"):
            page.new_set(typed, ["a", "a"])
        with self.assertRaisesRegex(Exception, "Vanilla"):
            page.save_set("vanilla", typed, ["a"])
        with self.assertRaisesRegex(Exception, "any more"):
            page.save_set("gone", typed, ["a"])
        # each with the call it came from in front (FL-97: one key comes from several calls)
        self.assertEqual(self.day()["messages"], {"new_set:set_no_mods": 1, "new_set:set_no_name": 1,
                                                  "new_set:set_mod_missing": 1, "new_set:set_mod_twice": 1,
                                                  "save_set:set_vanilla": 1, "save_set:set_gone": 1})
        self.assertEqual(self.day()["calls"]["new_set"]["errors"], {"LauncherError": 4})
        sent = bugwatch._current.payload(bugwatch._today(), self.day())
        self.assertEqual(sent["messages"]["new_set:set_no_mods"], 1)
        self.assertNotIn("secret", str(sent))           # never what was typed
        self.assertNotIn("not-in-the-library", str(sent))

    def test_an_error_without_a_key_counts_no_message(self):
        class Api:
            def bad(self):
                raise ValueError("Nick's words")
        with self.assertRaises(ValueError):
            webui.page_api(Api()).bad()
        self.assertEqual(self.day()["messages"], {})

    def test_updates_offered_once_then_installed(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            app.update_check()
            app.update_check("fr")                       # asked again when the language changes: one offer still
            self.assertEqual(self.day()["updates"], {"offered": 1, "installed": 0, "failed": 0})
            job = app.update_install()["job"]
            for _ in range(200):
                if app._jobs[job].state != "running":
                    break
                time.sleep(0.02)
            self.assertEqual(app._jobs[job].state, "done")
            self.assertEqual(self.day()["updates"], {"offered": 1, "installed": 1, "failed": 0})
            # kept on disk before the app quits for the installer (its quit skips the save at the app's end)
            again = bugwatch.Watch(self.home, "launcher", "0.4.8.19", opener=mock.Mock())
            self.assertEqual(again.days[bugwatch._today()]["updates"]["installed"], 1)

    def test_an_update_that_fails_is_counted(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            app.update_check()
            app._update_opener = lambda url: (_ for _ in ()).throw(OSError("no internet"))
            job = app.update_install()["job"]
            for _ in range(200):
                if app._jobs[job].state != "running":
                    break
                time.sleep(0.02)
            self.assertEqual(app._jobs[job].state, "failed")
            self.assertEqual(self.day()["updates"]["failed"], 1)
            self.assertEqual(self.day()["updates"]["installed"], 0)


if __name__ == "__main__":
    unittest.main()
