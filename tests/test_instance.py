"""Tests for modded instances, on a small made-up game folder (no real game needed)."""
import os
import shutil
import stat
import tempfile
import unittest

from rusemod.instance import InstanceError, build_instance


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

    def test_a_big_file_can_be_written_by_a_function(self):
        chunks = [b"PART1", b"PART2"]
        counts = build_instance(self.game, self.dst, replace={
            os.path.join("Data", "PC", "1", "B.dat"): lambda f: [f.write(c) for c in chunks]})
        with open(os.path.join(self.dst, "Data", "PC", "1", "B.dat"), "rb") as f:
            self.assertEqual(f.read(), b"PART1PART2")
        self.assertEqual(counts["written"], 1)

    def test_the_last_working_copy_stays_until_the_new_one_is_complete(self):
        build_instance(self.game, self.dst, replace={os.path.join("Data", "PC", "1", "B.dat"): b"FIRST"})

        def fail(_f):
            raise OSError("disk full")

        with self.assertRaises(OSError):
            build_instance(self.game, self.dst, replace={os.path.join("Data", "PC", "1", "B.dat"): fail})
        with open(os.path.join(self.dst, "Data", "PC", "1", "B.dat"), "rb") as f:
            self.assertEqual(f.read(), b"FIRST")  # the first build is still there, whole
        self.assertFalse(os.path.exists(self.dst + ".partial"))
        build_instance(self.game, self.dst, replace={os.path.join("Data", "PC", "1", "B.dat"): b"SECOND"})
        with open(os.path.join(self.dst, "Data", "PC", "1", "B.dat"), "rb") as f:
            self.assertEqual(f.read(), b"SECOND")
        self.assertFalse(os.path.exists(self.dst + ".old"))

    def test_another_drive_gets_full_copies(self):
        real_link = os.link

        def no_links(_a, _b):
            raise OSError(18, "Invalid cross-device link")

        os.link = no_links
        try:
            counts = build_instance(self.game, self.dst)
        finally:
            os.link = real_link
        self.assertEqual(counts, {"linked": 0, "copied": 2, "written": 0, "full copies": 3})
        a = os.path.join(self.dst, "Data", "PC", "1", "A.dat")
        self.assertFalse(os.path.samefile(a, os.path.join(self.game, "Data", "PC", "1", "A.dat")))
        with open(a, "rb") as f:
            self.assertEqual(f.read(), b"archive A")


def _files(folder):
    return [os.path.join(root, fn) for root, _dirs, files in os.walk(folder) for fn in files]


def _read_only(path):
    return not os.stat(path).st_mode & stat.S_IWRITE


class ReadOnlyGame(unittest.TestCase):
    """A game folder whose files are marked read-only (a disc install, a restored backup). A player's report,
    2026-09-30: every "Test in game" failed with "[WinError 5] Access is denied: ...partial\\...\\ZZ_GladPatchableWin.dat":
    copies and links kept the mark, and a copy left half-built could never be removed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.tmp.name, "game")
        _write(os.path.join(self.game, "RUSE.exe"), b"exe")
        _write(os.path.join(self.game, "Data", "PC", "1", "A.dat"), b"archive A")
        _write(os.path.join(self.game, "Data", "PC", "1", "B.dat"), b"archive B")
        _write(os.path.join(self.game, "Data", "lang.ini"), b"lang=us")
        for path in _files(self.game):
            os.chmod(path, stat.S_IREAD)
        self.dst = os.path.join(self.tmp.name, "inst")

    def tearDown(self):
        for folder in (self.game, self.dst, self.dst + ".partial", self.dst + ".old",
                       os.path.join(self.tmp.name, ".trash")):
            for path in _files(folder):
                os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
        self.tmp.cleanup()

    def test_nothing_in_the_copy_is_read_only_and_it_rebuilds(self):
        counts = build_instance(self.game, self.dst)
        self.assertEqual(counts, {"linked": 0, "copied": 2, "written": 0, "full copies": 2, "read-only packs": 2})
        self.assertEqual([p for p in _files(self.dst) if _read_only(p)], [])
        for _ in range(2):  # the old copy goes each time
            build_instance(self.game, self.dst, replace={os.path.join("Data", "PC", "1", "B.dat"): b"MODDED"})
        self.assertFalse(os.path.exists(self.dst + ".old") or os.path.exists(self.dst + ".partial"))
        self.assertTrue(all(_read_only(p) for p in _files(self.game)))  # the game's files are as they were
        with open(os.path.join(self.game, "Data", "PC", "1", "B.dat"), "rb") as f:
            self.assertEqual(f.read(), b"archive B")

    def test_a_half_built_copy_an_older_version_left(self):
        # what the older build left: a read-only hard link to a read-only pack, and a read-only copy
        partial = self.dst + ".partial"
        pack = os.path.join(self.game, "Data", "PC", "1", "A.dat")
        os.makedirs(os.path.join(partial, "Data", "PC", "1"))
        os.link(pack, os.path.join(partial, "Data", "PC", "1", "A.dat"))
        shutil.copy2(os.path.join(self.game, "Data", "lang.ini"), os.path.join(partial, "Data", "lang.ini"))
        self.assertTrue(_read_only(os.path.join(partial, "Data", "lang.ini")))
        old = self.dst + ".old"
        os.makedirs(old)
        shutil.copy2(os.path.join(self.game, "RUSE.exe"), os.path.join(old, "RUSE.exe"))
        build_instance(self.game, self.dst)
        self.assertFalse(os.path.exists(partial) or os.path.exists(old))
        self.assertTrue(_read_only(pack))  # the mark was put back on the game's pack
        self.assertEqual(os.stat(pack).st_nlink, 1)  # the old link is gone
        with open(pack, "rb") as f:
            self.assertEqual(f.read(), b"archive A")

    @unittest.skipUnless(os.name == "nt", "Windows keeps a folder whose game is running from being replaced")
    def test_a_copy_in_use_is_said_plainly(self):
        build_instance(self.game, self.dst)
        held = open(os.path.join(self.dst, "RUSE.exe"), "rb")  # as the running game holds its own .exe
        try:
            with self.assertRaisesRegex(InstanceError, "in use.*close the game"):
                build_instance(self.game, self.dst)
            self.assertFalse(os.path.exists(self.dst + ".partial"))  # nothing half-built left behind
            self.assertTrue(os.path.exists(os.path.join(self.dst, "RUSE.exe")))  # the copy it runs from stays
        finally:
            held.close()
        build_instance(self.game, self.dst)  # the game closed: it goes through

    def test_an_old_copys_link_to_a_replaced_read_only_pack(self):
        # a player's report, 2026-09-30, on 0.7.4: every second Test in game failed on the old copy's
        # ZZ_GladPatchableWin.dat ("Access is denied"). An older version had linked the read-only pack; the game's file
        # was replaced since (another mod manager), so the link's other name isn't the game's file any more
        pack = os.path.join(self.game, "Data", "PC", "1", "A.dat")
        old = self.dst + ".old"
        os.makedirs(os.path.join(old, "Data", "PC", "1"))
        os.link(pack, os.path.join(old, "Data", "PC", "1", "A.dat"))
        os.rename(pack, pack + ".orig")
        _write(pack, b"archive A, put back")
        os.chmod(pack, stat.S_IREAD)
        for _ in range(2):  # the second press is the one that failed
            build_instance(self.game, self.dst)
        self.assertFalse(os.path.exists(old) or os.path.exists(os.path.join(self.tmp.name, ".trash")))
        self.assertTrue(_read_only(pack + ".orig"))  # its other name keeps its mark and its content
        with open(pack + ".orig", "rb") as f:
            self.assertEqual(f.read(), b"archive A")
        os.chmod(pack + ".orig", stat.S_IREAD | stat.S_IWRITE)

    @unittest.skipUnless(os.name == "nt", "Windows won't delete a running program's own file")
    def test_a_leftover_windows_wont_delete_is_moved_aside(self):
        import subprocess
        old = self.dst + ".old"
        os.makedirs(old)
        ping = os.path.join(old, "PING.EXE")
        shutil.copy2(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "PING.EXE"), ping)
        running = subprocess.Popen([ping, "-n", "30", "127.0.0.1"], cwd=self.tmp.name, stdout=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            build_instance(self.game, self.dst)  # not refused: the old copy goes into the trash, running or not
            self.assertFalse(os.path.exists(old))
            self.assertTrue(os.path.exists(os.path.join(self.tmp.name, ".trash", "inst.old", "PING.EXE")))
        finally:
            running.kill()
            running.wait()
        build_instance(self.game, self.dst)  # nothing runs from it now: the trash is emptied
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, ".trash")))

    @unittest.skipUnless(os.name == "nt", "names the program through Windows")
    def test_a_game_still_running_from_the_copy_is_named(self):
        import subprocess
        from rusemod.instance import GameRunning
        build_instance(self.game, self.dst)
        ping = os.path.join(self.dst, "PING.EXE")
        shutil.copy2(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "PING.EXE"), ping)
        running = subprocess.Popen([ping, "-n", "30", "127.0.0.1"], cwd=self.tmp.name, stdout=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            with self.assertRaisesRegex(GameRunning, r"still running from the modded copy.*PING\.EXE \(process "
                                                     r"\d+\)\. Close the game") as got:
                build_instance(self.game, self.dst)
            self.assertEqual([pid for pid, _exe in got.exception.running], [running.pid])
            self.assertFalse(os.path.exists(self.dst + ".partial"))  # refused before building anything
        finally:
            running.kill()
            running.wait()
        build_instance(self.game, self.dst)

    @unittest.skipUnless(os.name == "nt", "only Windows refuses to delete a file that's open")
    def test_a_stuck_leftover_is_said_plainly(self):
        partial = self.dst + ".partial"
        _write(os.path.join(partial, "RUSE.exe"), b"exe")
        held = open(os.path.join(partial, "RUSE.exe"), "rb")
        try:
            with self.assertRaisesRegex(InstanceError, "left half-built.*can't be removed.*delete that folder by hand"):
                build_instance(self.game, self.dst)
        finally:
            held.close()


if __name__ == "__main__":
    unittest.main()
