"""The troubleshooter (rusemod.doctor) on made-up folders: what it finds, its two fixes, its report."""
import os
import stat
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from rusemod import doctor


def by_key(findings):
    return {f["key"]: f for f in findings}


class Troubleshooter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "game"
        (self.game / "Data").mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"exe")
        (self.game / "Data" / "lang.ini").write_bytes(b"lang=us")
        os.chmod(self.game / "Data" / "lang.ini", stat.S_IREAD)
        self.copies = root / "RUSE-Instances"

    def tearDown(self):
        os.chmod(self.game / "Data" / "lang.ini", stat.S_IREAD | stat.S_IWRITE)
        self.tmp.cleanup()

    def test_all_clear(self):
        got = by_key(doctor.checks(self.game, self.copies, steam_running=lambda: True, processes=lambda: []))
        self.assertEqual({k: f["level"] for k, f in got.items() if k != "space"},
                         {"game": "ok", "steam": "ok", "running": "ok", "drive": "ok", "leftovers": "ok",
                          "readonly": "info", "write": "ok"})
        self.assertEqual(got["readonly"]["data"], {"n": 1})
        self.assertEqual(got["game"]["data"], {"path": str(self.game)})
        self.assertFalse(any(f["fix"] for f in got.values()))
        self.assertFalse(self.copies.exists())  # the write test leaves nothing, not even the folder it made for itself
        self.copies.mkdir()
        doctor.checks(self.game, self.copies, steam_running=lambda: True, processes=lambda: [])
        self.assertEqual(list(self.copies.iterdir()), [])  # nor a file in a folder that was there

    def test_what_stops_a_test_and_its_fixes(self):
        (self.copies / "studio-x.old" / "Data").mkdir(parents=True)
        (self.copies / "studio-x.old" / "Data" / "A.dat").write_bytes(b"pack")
        game_in_copy = str(self.copies / "studio-x" / "RUSE.exe")
        steam_game = str(self.game / "RUSE.exe")
        got = by_key(doctor.checks(None, self.copies, steam_running=lambda: False,
                                   processes=lambda: [(7, game_in_copy), (9, steam_game), (11, "C:\\x\\notepad.exe")]))
        self.assertEqual((got["game"]["level"], got["game"]["fix"]), ("fail", "choose_game"))
        self.assertEqual(got["steam"]["level"], "info")
        self.assertEqual((got["running"]["say"], got["running"]["fix"]), ("doc_running_copy", "close_game"))
        self.assertEqual(got["running"]["data"], {"names": "RUSE.exe (7)"})
        self.assertEqual((got["leftovers"]["say"], got["leftovers"]["fix"]), ("doc_left", "clear_leftovers"))
        self.assertEqual(got["leftovers"]["data"], {"names": "studio-x.old"})
        self.assertNotIn("readonly", got)  # no game to look at
        only_steam = by_key(doctor.checks(self.game, self.copies, steam_running=lambda: True,
                                          processes=lambda: [(9, steam_game)]))
        self.assertEqual((only_steam["running"]["level"], only_steam["running"]["fix"]), ("info", None))
        done = doctor.fix("clear_leftovers", self.game, self.copies)
        self.assertEqual(done, {"done": 1, "left": []})
        self.assertFalse((self.copies / "studio-x.old").exists())
        self.assertEqual(by_key(doctor.checks(self.game, self.copies, lambda: True, lambda: []))["leftovers"]["level"],
                         "ok")
        with self.assertRaises(ValueError):
            doctor.fix("format the drive", self.game, self.copies)
        none = by_key(doctor.checks(None, None, lambda: True, lambda: []))  # no game, so no place for copies yet
        self.assertEqual(list(none), ["game", "steam", "running"])

    def test_a_copy_moved_into_the_trash_counts_once(self):
        # a copy Windows won't delete goes into the trash; it's done when the sweep removes it, not twice
        from rusemod import instance
        (self.copies / "studio-x.old").mkdir(parents=True)

        def moved(path, src, what):
            target = os.path.join(os.path.dirname(path), instance.TRASH, os.path.basename(path))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            os.replace(path, target)
            return target
        with mock.patch.object(instance, "_set_aside", moved):
            self.assertEqual(doctor.fix("clear_leftovers", self.game, self.copies), {"done": 1, "left": []})
        self.assertEqual(list(self.copies.iterdir()), [])

    def test_a_copy_still_being_built_is_left_alone(self):
        building = self.copies / "launcher-set.partial"
        (building / "Data").mkdir(parents=True)  # just written to: the other app may be building it
        got = doctor.fix("clear_leftovers", self.game, self.copies)
        self.assertEqual((got["done"], got["left"]), (0, ["launcher-set.partial: still being built, left alone"]))
        self.assertTrue(building.is_dir())
        self.assertFalse(doctor._building(building, now=time.time() + 2 * doctor.BUILDING))  # an old one is cleared
        self.assertFalse(doctor._building(self.copies / "studio-x.old"))  # only half-built copies build
        with self.assertRaises(ValueError):
            doctor.fix("clear_leftovers", self.game, None)  # no game found yet: no folder for copies

    def test_the_report(self):
        text = doctor.report(doctor.checks(self.game, self.copies, lambda: True, lambda: []), "RUSE Studio", "9.9")
        self.assertTrue(text.startswith("RUSE Studio 9.9, Windows "))
        self.assertIn("[ok] game: doc_game_ok (path=", text)
        self.assertIn("[info] readonly: doc_readonly (n=1)", text)
        mine = str(Path.home() / "Games" / "R.U.S.E")  # it's pasted in public: no Windows user name in it
        text = doctor.report([{"key": "game", "level": "ok", "say": "doc_game_ok", "data": {"path": mine},
                               "fix": None}], "RUSE Launcher", "9.9")
        self.assertNotIn(str(Path.home()), text)
        self.assertIn("%USERPROFILE%", text)


if __name__ == "__main__":
    unittest.main()
