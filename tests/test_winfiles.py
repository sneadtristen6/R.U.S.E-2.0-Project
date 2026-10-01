"""Windows file and process helpers (rusemod.winfiles): what holds a file, what runs from a folder, a delete that
ignores the read-only mark. The Windows-only parts start small helper programs of their own and end them."""
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest

from rusemod import winfiles


class Paths(unittest.TestCase):
    def test_inside(self):
        base = os.path.join(tempfile.gettempdir(), "RUSE-Instances", "studio-x")
        self.assertTrue(winfiles.inside(base, base))
        self.assertTrue(winfiles.inside(os.path.join(base, "RUSE.exe"), base))
        self.assertFalse(winfiles.inside(base + ".old", base))  # a sibling that starts the same isn't in it
        self.assertFalse(winfiles.inside(os.path.dirname(base), base))


class Deleting(unittest.TestCase):
    def test_a_read_only_file_goes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pack.dat")
            with open(path, "wb") as f:
                f.write(b"pack")
            os.chmod(path, stat.S_IREAD)
            winfiles.posix_delete(path)
            self.assertFalse(os.path.exists(path))

    @unittest.skipUnless(os.name == "nt", "hard links sharing a read-only mark are Windows' problem")
    def test_a_links_other_name_keeps_its_mark(self):
        with tempfile.TemporaryDirectory() as tmp:
            game, link = os.path.join(tmp, "game.dat"), os.path.join(tmp, "link.dat")
            with open(game, "wb") as f:
                f.write(b"pack")
            os.chmod(game, stat.S_IREAD)
            os.link(game, link)
            with self.assertRaises(PermissionError):
                os.unlink(link)  # what the old copies ran into
            winfiles.posix_delete(link)
            self.assertFalse(os.path.exists(link))
            self.assertFalse(os.stat(game).st_mode & stat.S_IWRITE)
            os.chmod(game, stat.S_IREAD | stat.S_IWRITE)


@unittest.skipUnless(os.name == "nt", "processes and volumes through Windows")
class Processes(unittest.TestCase):
    def test_who_holds_a_file_and_what_runs_from_a_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "held.dat")
            with open(path, "wb") as f:
                f.write(b"x")
            ready = os.path.join(tmp, "ready")
            code = f"f = open({path!r}, 'rb'); open({ready!r}, 'w').close(); import time; time.sleep(30)"
            helper = subprocess.Popen([sys.executable, "-c", code], creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                for _ in range(100):
                    if os.path.exists(ready):
                        break
                    time.sleep(0.1)
                self.assertIn(helper.pid, [pid for pid, _exe in winfiles.holders(path)])
            finally:
                helper.kill()
                helper.wait()
            self.assertEqual(winfiles.holders(path), [])
            ping = os.path.join(tmp, "PING.EXE")
            with open(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "PING.EXE"), "rb") as src, \
                    open(ping, "wb") as dst:
                dst.write(src.read())
            running = subprocess.Popen([ping, "-n", "30", "127.0.0.1"], stdout=subprocess.DEVNULL,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                found = winfiles.running_from(tmp)
                self.assertEqual([pid for pid, _exe in found], [running.pid])
                self.assertTrue(winfiles.close(running.pid))
                running.wait(10)
            finally:
                if running.poll() is None:
                    running.kill()
                    running.wait()
            self.assertEqual(winfiles.running_from(tmp), [])

    def test_the_drive(self):
        got = winfiles.volume(tempfile.gettempdir())
        self.assertTrue(got["fs"])
        self.assertIsInstance(got["posix_delete"], bool)


if __name__ == "__main__":
    unittest.main()
