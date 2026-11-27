"""The troubleshooter (rusemod.doctor) on made-up folders: what it finds, its two fixes, its report."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
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

    def test_a_kept_copy_is_never_a_leftover(self):
        # 2026-11-01: "clear leftover copies" counted every copy but the apps' own as a leftover and took a folder of
        # test copies; only copies with no keep note may go
        from rusemod import instance
        program = doctor.GAME_PROGRAMS[0]  # the game's program, by the name the troubleshooter looks for

        def copy(name, **note):
            folder = self.copies / name
            (folder / "Data").mkdir(parents=True)
            (folder / program).write_bytes(b"exe")
            (folder / "steam_appid.txt").write_text("21970")
            if note:
                instance.keep(str(folder), **note)
            return folder
        old_set = copy("my-old-set")  # one per mod set, as the apps made them before 10-02: a leftover
        test = copy("tf-museum13c", why="a test copy")
        ref = copy("m1-candidate1", why="regression evidence", reference=True)
        unreadable = copy("bad-note")
        (unreadable / instance.KEEP).write_text("{not a note")  # a note that can't be read still keeps the copy
        shared = copy("Modded game")  # the apps' own copy is never a leftover either
        got = by_key(doctor.checks(self.game, self.copies, lambda: True, lambda: []))
        self.assertEqual(got["leftovers"]["data"], {"names": "my-old-set"})
        self.assertEqual(doctor.fix("clear_leftovers", self.game, self.copies), {"done": 1, "left": []})
        self.assertFalse(old_set.exists())
        for folder in (test, ref, unreadable, shared):
            self.assertTrue((folder / program).is_file(), folder.name)
        self.assertEqual((instance.kept(str(ref))["why"], instance.kept(str(ref))["reference"]),
                         ("regression evidence", True))
        self.assertTrue(instance.kept(str(unreadable))["keep"])
        self.assertEqual(by_key(doctor.checks(self.game, self.copies, lambda: True, lambda: []))["leftovers"]["level"],
                         "ok")

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


class RedirectionGuard(unittest.TestCase):
    """FL-125 (the owner's screenshot of 2026-11-26: the Launcher opened by its installer, "D:\\Steam\\steamapps\\common
    \\R.U.S.E couldn't be read or written (error 448)"): Windows' Redirection Guard, passed on by Inno Setup, refuses
    every folder link a non-admin made. The troubleshooter says so first, as its one finding, with a fix that opens the
    app again through Explorer, without it."""

    def test_the_one_finding_and_its_fix_and_nothing_read(self):
        reads = mock.Mock(side_effect=OSError(None, "untrusted mount point", None, 448))
        got = doctor.checks(Path("D:/Steam/steamapps/common/R.U.S.E"), Path("D:/RUSE-Instances"),
                            steam_running=reads, processes=reads, guarded=lambda: True)
        self.assertEqual(got, [{"key": "redirection", "level": "fail", "say": "doc_redirection_guard", "data": {},
                                "fix": "reopen_app"}])
        reads.assert_not_called()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        game = Path(tmp.name)
        (game / "RUSE.exe").write_bytes(b"exe")
        found = by_key(doctor.checks(game, None, steam_running=lambda: True, processes=lambda: [],
                                     guarded=lambda: False))
        self.assertNotIn("redirection", found)                    # (without it: as before)
        self.assertEqual(found["game"]["level"], "ok")

    def test_the_fix_opens_the_installed_app_through_explorer_then_closes_this_one(self):
        import sys
        started, closed = [], []
        got = doctor.reopen_app(start=started.append, quit_soon=lambda: closed.append(1), installed=lambda: True)
        self.assertEqual((got, started, closed), ({"done": 1, "left": []}, [sys.executable], [1]))
        repo = doctor.reopen_app(start=started.append, quit_soon=closed.append, installed=lambda: False)
        self.assertEqual((repo["done"], len(repo["left"]), len(started), len(closed)), (0, 1, 1, 1))  # (from the repo)
        popen = mock.Mock()
        from rusemod import winfiles
        winfiles.reopen_through_explorer("C:/Apps/RUSE Launcher.exe", popen=popen)
        cmd = popen.call_args[0][0]
        self.assertEqual((os.path.basename(cmd[0]).lower(), cmd[1]), ("explorer.exe", "C:/Apps/RUSE Launcher.exe"))

    @unittest.skipUnless(os.name == "nt", "Windows' Redirection Guard")
    def test_the_real_guard_is_seen_in_a_program_that_has_it(self):
        """A Python that turns Redirection Guard on for itself (as Inno Setup does: SetProcessMitigationPolicy,
        ProcessRedirectionTrustPolicy, enforced) is seen to have it by winfiles.redirection_guarded; this one isn't."""
        import subprocess
        import sys
        from rusemod import winfiles
        self.assertFalse(winfiles.redirection_guarded())
        src = Path(doctor.__file__).resolve().parents[1]
        code = ("import ctypes, sys; sys.path.insert(0, sys.argv[1]); from ctypes import wintypes; "
                "k = ctypes.WinDLL('kernel32'); flags = wintypes.DWORD(1); "
                "k.SetProcessMitigationPolicy.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]; "
                "ok = k.SetProcessMitigationPolicy(16, ctypes.byref(flags), 4); "
                "from rusemod import winfiles; print(bool(ok), winfiles.redirection_guarded())")
        out = subprocess.run([sys.executable, "-c", code, str(src)], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.stdout.split(), ["True", "True"], out.stderr)

    def test_both_apps_say_it_without_looking_for_the_game_and_run_its_fix(self):
        from rusemod import winfiles
        from ruse_launcher.api import LauncherApi
        from ruse_studio.api import StudioApi
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        launcher = LauncherApi(home=root / "home", game_dir=root / "game", find=lambda: None)
        studio = StudioApi(game_dir=root / "game", home=root / "studio")
        blocked = OSError(None, "untrusted mount point", None, 448)
        with mock.patch.object(winfiles, "redirection_guarded", return_value=True), \
                mock.patch.object(launcher, "_doctor_places", side_effect=blocked), \
                mock.patch.object(studio, "_game", side_effect=blocked):
            for app in (launcher, studio):
                with self.subTest(app=type(app).__name__):
                    self.assertEqual([f["key"] for f in app.troubleshoot()["findings"] if f["level"] == "fail"],
                                     ["redirection"])
        with mock.patch.object(doctor, "reopen_app", return_value={"done": 1, "left": []}) as reopen:
            self.assertEqual(launcher.troubleshoot_fix("reopen_app"), {"done": 1, "left": []})
            self.assertEqual(studio.troubleshoot_fix("reopen_app"), {"done": 1, "left": []})
        self.assertEqual(reopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
