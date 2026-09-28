"""Tests for modded instances, on a small made-up game folder (no real game needed)."""
import os
import tempfile
import unittest

from rusemod.instance import build_instance


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


class InstanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.tmp.name, "game")
        _write(os.path.join(self.game, "RUSE.exe"), b"exe")
        _write(os.path.join(self.game, "Data", "PC", "1", "A.dat"), b"archive A")
        _write(os.path.join(self.game, "Data", "PC", "1", "B.dat"), b"archive B")
        _write(os.path.join(self.game, "Maps", "PC", "Map1.dat"), b"map pack")
        _write(os.path.join(self.game, "Data", "lang.ini"), b"lang=us")
        self.dst = os.path.join(self.tmp.name, "inst")

    def tearDown(self):
        self.tmp.cleanup()

    def test_links_copies_and_appid(self):
        counts = build_instance(self.game, self.dst)
        self.assertEqual(counts, {"linked": 3, "copied": 2, "written": 0})
        a = os.path.join(self.dst, "Data", "PC", "1", "A.dat")
        self.assertTrue(os.path.samefile(a, os.path.join(self.game, "Data", "PC", "1", "A.dat")))
        ini = os.path.join(self.dst, "Data", "lang.ini")
        self.assertFalse(os.path.samefile(ini, os.path.join(self.game, "Data", "lang.ini")))
        with open(os.path.join(self.dst, "steam_appid.txt")) as f:
            self.assertEqual(f.read(), "21970")
        self.assertFalse(os.path.exists(self.dst + ".partial"))

    def test_replace_never_touches_original(self):
        build_instance(self.game, self.dst, replace={os.path.join("Data", "PC", "1", "B.dat"): b"MODDED"})
        with open(os.path.join(self.dst, "Data", "PC", "1", "B.dat"), "rb") as f:
            self.assertEqual(f.read(), b"MODDED")
        with open(os.path.join(self.game, "Data", "PC", "1", "B.dat"), "rb") as f:
            self.assertEqual(f.read(), b"archive B")

    def test_rename_hides_old_name(self):
        build_instance(self.game, self.dst, rename={os.path.join("Maps", "PC", "Map1.dat"): os.path.join("Maps", "PC", "Map2.dat")})
        self.assertFalse(os.path.exists(os.path.join(self.dst, "Maps", "PC", "Map1.dat")))
        self.assertTrue(os.path.samefile(os.path.join(self.dst, "Maps", "PC", "Map2.dat"),
                                         os.path.join(self.game, "Maps", "PC", "Map1.dat")))

    def test_refuses_inside_game_folder(self):
        with self.assertRaises(ValueError):
            build_instance(self.game, os.path.join(self.game, "inst"))

    def test_missing_replace_target_fails_cleanly(self):
        with self.assertRaises(FileNotFoundError):
            build_instance(self.game, self.dst, replace={"nope.dat": b"x"})
        self.assertFalse(os.path.exists(self.dst))
        self.assertFalse(os.path.exists(self.dst + ".partial"))


if __name__ == "__main__":
    unittest.main()
