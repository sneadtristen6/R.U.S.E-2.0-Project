"""The refusals of the calls both apps share in the player's language (rusemod.update.words, from rusemod/buildtext.toml;
the plain-words job, 2026-11-14: they were English in both apps in every language, and the update check said why
GitHub couldn't be reached in Python's and Windows' words, "<urlopen error [WinError 10061] No connection could be
made because the target machine actively refused it>", met on every start without the internet): the update check
and a backup's refusal, in the Launcher and the Studio, each with its English control."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import tempfile
import unittest
import urllib.error
from pathlib import Path

from rusemod.webui import page_api
from ruse_launcher.api import LauncherApi, LauncherError
from ruse_studio.api import StudioApi, StudioError


def refused(url):
    raise urllib.error.URLError(ConnectionRefusedError(10061, "No connection could be made"))


class Both(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.launcher = LauncherApi(home=self.tmp / "launcher", game_dir=self.tmp / "nowhere")
        self.studio = StudioApi(game_dir=self.tmp / "nowhere", home=self.tmp / "studio", index_path=self.tmp / "x.sqlite")
        for api in (self.launcher, self.studio):
            api._update_fetch = api._update_fetch_text = refused

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_update_check_offline_in_the_player_s_language(self):
        self.assertEqual(page_api(self.launcher).update_check("ger")["error"],
                         "GitHub war nicht zu erreichen, um nach Updates zu suchen (dieser PC hat den Server nicht "
                         "erreicht: Es gibt keine Internetverbindung, oder etwas auf dem Weg (eine Firewall, ein "
                         "Virenscanner, der Server selbst) hat die Verbindung abgelehnt).")
        said = page_api(self.studio).update_check("jpn")["error"]
        self.assertTrue(said.startswith("更新を確認するために GitHub へ接続できませんでした（この PC はサーバーにつながり"), said)
        self.assertNotIn("WinError", said)

    def test_the_update_check_asked_without_a_language_uses_the_window_s(self):
        self.launcher.set_pref("lang", "pol")
        self.assertTrue(self.launcher.update_check()["error"].startswith("Nie udało się połączyć z GitHubem"))

    def test_control_the_update_check_offline_in_english(self):
        self.assertEqual(self.launcher.update_check("us")["error"],
                         "GitHub couldn't be reached to look for updates (this PC couldn't reach the server: there's no "
                         "internet connection, or something on the way (a firewall, an antivirus, the server itself) "
                         "turned the connection down).")

    def test_a_backup_s_refusal_in_the_player_s_language(self):
        self.launcher.set_pref("lang", "pol")
        with self.assertRaises(LauncherError) as caught:
            page_api(self.launcher).backup_check()
        self.assertEqual(str(caught.exception), "Nie znaleźliśmy R.U.S.E. Najpierw wybierz jego folder.")
        self.studio.set_pref("lang", "spa")
        with self.assertRaises(StudioError) as caught:
            page_api(self.studio).backup_check()
        self.assertEqual(str(caught.exception), "No encontramos R.U.S.E. Elige primero su carpeta.")

    def test_control_a_backup_s_refusal_in_english(self):
        self.launcher.set_pref("lang", "us")
        with self.assertRaises(Exception) as caught:
            page_api(self.launcher).backup_check()
        self.assertEqual(str(caught.exception), "We couldn't find R.U.S.E. Choose its folder first.")


if __name__ == "__main__":
    unittest.main()
