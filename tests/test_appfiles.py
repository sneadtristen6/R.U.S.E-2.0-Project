"""FL-57: the troubleshooter says when the app's own data files (rusemod.appfiles: what a build reads from the install)
are missing, on made-up app folders; and the list is kept equal to what the installer ships and what the code opens."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import importlib.util
import re
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import appfiles, doctor, fairplay

ROOT = Path(__file__).parents[1]
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")


def installer():
    spec = importlib.util.spec_from_file_location("installers_build_app", ROOT / "installers" / "build_app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finds(app_dir):
    return [f for f in doctor.checks(None, None, steam_running=lambda: True, processes=lambda: [], app_dir=app_dir)
            if f["key"] == "app_files"]


class AppFilesFinding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Path(self.tmp.name)
        for rel in appfiles.APP_FILES:
            (self.app / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.app / rel).write_bytes(b"x")

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_complete_install_gives_none(self):
        self.assertEqual(finds(self.app), [])
        self.assertEqual(appfiles.missing(self.app), [])

    def test_a_missing_data_file_is_a_fail_naming_it(self):
        (self.app / "rusemod" / "gamescripts" / "fairplay_watch.bin").unlink()  # the FL-56 file
        (self.app / "ruse_mod_engine" / "data" / "game_versions.json").unlink()
        got = finds(self.app)
        self.assertEqual(len(got), 1)
        f = got[0]
        self.assertEqual((f["level"], f["say"], f["fix"]), ("fail", "doc_app_files_missing", None))
        self.assertEqual(f["data"]["n"], 2)
        self.assertIn("rusemod\\gamescripts\\fairplay_watch.bin", f["data"]["files"])
        self.assertIn("ruse_mod_engine\\data\\game_versions.json", f["data"]["files"])
        self.assertNotIn(str(self.app), f["data"]["files"])  # relative to the app, never the player's folders

    def test_a_file_that_cannot_be_read_counts_as_missing(self):
        path = self.app / "rusemod" / "motions.json.gz"
        path.unlink()
        path.mkdir()  # a folder where the file should be: opening it fails
        self.assertEqual(appfiles.missing(self.app), ["rusemod/motions.json.gz"])

    def test_many_missing_are_counted_and_the_first_named(self):
        for rel in appfiles.APP_FILES[:20]:
            (self.app / rel).unlink()
        f = finds(self.app)[0]
        self.assertEqual(f["data"]["n"], 20)
        self.assertTrue(f["data"]["files"].endswith(f"(+{20 - doctor.SAID_FILES})"))

    def test_the_real_install_is_complete(self):
        self.assertEqual(appfiles.missing(), [])  # (from source here: src/ holds every file)

    def test_the_finding_has_words_in_both_apps(self):
        for app in ("ruse_launcher", "ruse_studio"):
            words = tomllib.loads((ROOT / "src" / app / "words.toml").read_text(encoding="utf-8"))
            word = words["doc_app_files_missing"]
            self.assertEqual(sorted(word), sorted(LANGS), app)
            for lang in LANGS:
                self.assertIn("{files}", word[lang], (app, lang))
                self.assertIn("{n}", word[lang], (app, lang))
            self.assertIn("einstall", word["us"].replace("Re", "re"))  # says what to do: reinstall


class AppFilesList(unittest.TestCase):
    def test_the_list_is_what_the_installer_ships(self):
        shipped = {dest for _src, dest in installer().data_files("launcher")
                   if dest.startswith(("rusemod/", "ruse_mod_engine/data/"))}
        listed = set(appfiles.APP_FILES) | set(appfiles.NOT_READ)
        self.assertEqual(len(appfiles.APP_FILES), len(set(appfiles.APP_FILES)))
        self.assertFalse(set(appfiles.APP_FILES) & set(appfiles.NOT_READ))
        self.assertEqual(sorted(shipped - listed), [], "a data file the app ships isn't in rusemod/appfiles.py")
        self.assertEqual(sorted(listed - shipped), [], "rusemod/appfiles.py lists a file that isn't there")

    def test_the_files_the_code_names_are_listed(self):
        """What the code opens beside itself: Path(__file__).with_name("<file>"), and the game scripts fairplay names."""
        listed = set(appfiles.APP_FILES)
        seen = {}
        for py in sorted((ROOT / "src" / "rusemod").glob("*.py")):
            text = py.read_text(encoding="utf-8")
            for name in re.findall(r"__file__\)\.with_name\(\s*[\"']([^\"']+)[\"']", text):
                if not name.endswith(".py"):  # (the scripts Blender runs are code, not data)
                    seen[name] = f"rusemod/{name}"
        for name in (fairplay.LOCK, fairplay.WATCH, fairplay.GUARD):  # game_script(name) opens SCRIPTS/<name>.bin
            seen[name] = f"rusemod/gamescripts/{name}.bin"
        self.assertEqual(fairplay.SCRIPTS.name, "gamescripts")
        self.assertGreater(len(seen), 8)
        unlisted = [p for p in seen.values() if p not in listed and not any(f.startswith(p + "/") for f in listed)]
        self.assertEqual(sorted(unlisted), [])  # (a folder named, like pictures, holds listed files)
        self.assertIn("rusemod/gamescripts/fairplay_watch.bin", seen.values())


if __name__ == "__main__":
    unittest.main()
