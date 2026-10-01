"""Help and bug reports (rusemod.community): the report's link, and no Windows user name in it."""
import os
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from rusemod.community import LINKS, MESSAGE_MOST, CommunityCalls, private_paths_out, report_url

HOME = "C:/Users/snead".replace("/", "\\")
ENV = {"USERPROFILE": HOME, "LOCALAPPDATA": HOME + "\\AppData\\Local", "APPDATA": HOME + "\\AppData\\Roaming"}


@mock.patch.dict(os.environ, ENV)
class PrivatePaths(unittest.TestCase):
    def test_the_players_folders_are_named_for_anyone(self):
        mod = "C:/Users/snead/AppData/Local/RUSE Mod Platform/mods/test/maps/Blitz/terrain.toml"
        self.assertEqual(private_paths_out(mod.replace("/", "\\") + " can't be read"),
                         "%LOCALAPPDATA%\\RUSE Mod Platform\\mods\\test\\maps\\Blitz\\terrain.toml can't be read")
        self.assertEqual(private_paths_out(mod), "%LOCALAPPDATA%/RUSE Mod Platform/mods/test/maps/Blitz/terrain.toml")
        self.assertEqual(private_paths_out("c:\\users\\SNEAD\\Desktop\\x.rusemod"), "%USERPROFILE%\\Desktop\\x.rusemod")
        self.assertEqual(private_paths_out("E:/Users/someone else/x and D:\\Users\\bob\\y"),
                         "%USERPROFILE% else/x and %USERPROFILE%\\y")  # any other user folder too
        self.assertEqual(private_paths_out("D:\\RUSE-Instances\\studio-test"), "D:\\RUSE-Instances\\studio-test")
        self.assertEqual(private_paths_out(None), "")


@mock.patch.dict(os.environ, ENV)
class ReportLink(unittest.TestCase):
    def fields(self, url):
        parts = urlsplit(url)
        self.assertEqual(parts.scheme + "://" + parts.netloc + parts.path,
                         "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions/new")
        return {k: v[0] for k, v in parse_qs(parts.query).items()}

    def test_the_form_filled_in(self):
        message = HOME + "\\AppData\\Local\\RUSE Mod Platform\\mods\\t\\terrain.toml: the water brush needs level\nmore"
        got = self.fields(report_url("studio", "0.7.1", message))
        self.assertEqual((got["category"], got["app"], got["version"]), ("bug-reports", "RUSE Studio", "0.7.1"))
        self.assertTrue(got["title"].startswith("[Bug] RUSE Studio 0.7.1: %LOCALAPPDATA%"))
        self.assertLessEqual(len(got["title"]), len("[Bug] RUSE Studio 0.7.1: ") + 80)
        self.assertTrue(got["message"].endswith("needs level\nmore"))
        self.assertNotIn("snead", urlsplit(report_url("studio", "0.7.1", message)).query)  # (the repo's owner is)

    def test_no_message_and_a_long_one(self):
        got = self.fields(report_url("launcher", "0.2.7"))
        self.assertEqual((got["title"], got["app"]), ("[Bug] RUSE Launcher 0.2.7: ", "RUSE Launcher"))
        self.assertNotIn("message", got)
        self.assertEqual(len(self.fields(report_url("studio", "1", "x" * 5000))["message"]), MESSAGE_MOST)


class Calls(unittest.TestCase):
    class App(CommunityCalls):
        UPDATE_APP, UPDATE_VERSION = "studio", "0.7.1"

        def __init__(self):
            self._update_open_url = mock.Mock()

    def test_open_the_pages_and_a_report(self):
        app = self.App()
        self.assertEqual(app.help_links(), LINKS)
        self.assertEqual(app.open_help("wiki"), {"opened": LINKS["wiki"]})
        app._update_open_url.assert_called_once_with(LINKS["wiki"])
        opened = app.report_problem("it broke")["opened"]
        self.assertIn("title=%5BBug%5D+RUSE+Studio+0.7.1%3A+it+broke", opened)
        app._update_open_url.assert_called_with(opened)
        with self.assertRaisesRegex(ValueError, "no help page called 'nope'"):
            app.open_help("nope")


if __name__ == "__main__":
    unittest.main()
