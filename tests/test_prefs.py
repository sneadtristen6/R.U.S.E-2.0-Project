"""What the windows keep (rusemod.home.PrefsCalls): the language and the Studio's keys, in settings.json in the platform
folder, so they outlive a restart (the window's own storage doesn't: its address changes every start), an update and
a reinstall."""
import json
import tempfile
import unittest
from pathlib import Path

from rusemod.home import PrefsCalls, save_settings, settings
from ruse_launcher.api import LauncherApi
from ruse_studio.api import StudioApi


class Kept(PrefsCalls):
    PREFS_APP = "studio"

    def __init__(self, home):
        self._home = home


class Prefs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_kept_across_a_new_start_and_next_to_the_other_settings(self):
        save_settings(self.home, {"game_dir": "D:/Games/RUSE"})
        Kept(self.home).set_pref("lang", "fr")
        Kept(self.home).set_pref("keys", {"forward": "KeyI"})
        again = Kept(self.home)  # a new start of the app reads them back
        self.assertEqual(again.prefs(), {"lang": "fr", "keys": {"forward": "KeyI"}})
        self.assertEqual(settings(self.home)["game_dir"], "D:/Games/RUSE")  # the rest is untouched
        again.set_pref("keys", None)
        self.assertEqual(again.prefs(), {"lang": "fr"})

    def test_each_app_keeps_its_own(self):
        class Other(Kept):
            PREFS_APP = "launcher"
        Kept(self.home).set_pref("lang", "fr")
        Other(self.home).set_pref("lang", "ger")
        self.assertEqual((Kept(self.home).prefs(), Other(self.home).prefs()), ({"lang": "fr"}, {"lang": "ger"}))

    def test_only_known_small_values(self):
        with self.assertRaises(ValueError):
            Kept(self.home).set_pref("game_dir", "C:/")  # not the window's to change
        with self.assertRaises(ValueError):
            Kept(self.home).set_pref("keys", {"x": "y" * 5000})
        (self.home / "settings.json").write_text(json.dumps({"prefs": {"studio": {"lang": "ru", "evil": 1}}}),
                                                 encoding="utf-8")
        self.assertEqual(Kept(self.home).prefs(), {"lang": "ru"})

    def test_both_apps_offer_them(self):
        studio = StudioApi(home=self.home, game_dir=self.home)
        launcher = LauncherApi(home=self.home, game_dir=self.home)
        studio.set_pref("lang", "jpn")
        launcher.set_pref("lang", "sc")
        self.assertEqual((studio.prefs(), launcher.prefs()), ({"lang": "jpn"}, {"lang": "sc"}))


if __name__ == "__main__":
    unittest.main()
