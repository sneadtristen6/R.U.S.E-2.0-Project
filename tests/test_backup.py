"""The clean game backup (rusemod.backup) on small made-up game folders: made, checked, restored, and what's refused.
No real game is needed, and nothing here touches one."""
import contextlib
import errno
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from rusemod import backup, winfiles
from rusemod.backup import BackupError, check, list_backups, make, restore, steam_verify_url

BUILD = "24670294"
SRC = Path(backup.__file__).resolve().parents[1]
NONE_RUNNING = lambda: []  # noqa: E731  (the process list, in place of the real one)
OTHER_APP = ("import sys\n"
             "from pathlib import Path\n"
             "from rusemod import backup\n"
             "folder, what = Path(sys.argv[1]), sys.argv[2]\n"
             "with (backup.reading(folder) if what == 'reading' else backup._busy(folder, what)):\n"
             "    print('held', flush=True)\n"
             "    sys.stdin.read()\n")  # the other app: holds the backups folder until its input closes


def _write(path: Path, data: bytes, mtime: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def _read_only(path: Path) -> bool:
    return not os.stat(path).st_mode & stat.S_IWRITE


def _link_folder(target: Path, link: Path) -> None:
    """A link to another folder, as a mod manager makes one: a junction on Windows (no admin needed, and os.walk goes
    through it), a symbolic link elsewhere."""
    if sys.platform == "win32":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def _tree(folder: Path) -> list[str]:
    """The files in `folder`, never through a link."""
    return sorted(rel for rel, _full, st in backup._walk(folder) if stat.S_ISREG(st.st_mode))


def _temps(folder: Path) -> list[str]:
    return [rel for rel, _full, _st in backup._walk(folder) if rel.endswith(".restoring")]


def make_game(root: Path, build: str = BUILD) -> Path:
    """A made-up Steam install: steamapps/common/R.U.S.E (with an empty folder, as the real one has) and the app
    manifest that gives its build."""
    game = root / "steamapps" / "common" / "R.U.S.E"
    old = time.time() - 86400
    for rel, data in [("RUSE.exe", b"MZ game"), ("Data/PC/190852/ZZ_Win.dat", b"pack " * 1000),
                      ("Data/PC/190852/ZZ_GladPatchableWin.dat", b"patchable pack"), ("Data/lang.ini", b"en-US"),
                      ("Maps/PC/DataMapAlpha_v09.dat", b"map pack"), ("Manual/RUSE_Manual_English.pdf", b"%PDF")]:
        _write(game / rel, data, old)
    (game / "EmptySteamDepot").mkdir()
    set_build(root, build)
    return game


def set_build(root: Path, build: str) -> None:
    (root / "steamapps" / "appmanifest_21970.acf").write_text(f'"AppState" {{ "buildid" "{build}" }}')


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tidy)  # the first cleanup runs last: after another app a test started has stopped
        self.root = Path(self.tmp.name)
        self.game = make_game(self.root)
        self.folder = self.root / "RUSE-Backup"
        self.dest = self.folder / BUILD

    def tidy(self):
        for _rel, full, st in list(backup._walk(self.root)):  # never through a link a test made
            if backup._link(st):
                try:
                    os.rmdir(full)  # a junction (Windows)
                except OSError:
                    os.unlink(full)
            elif stat.S_ISREG(st.st_mode):  # a read-only file left by a test doesn't stop the clean-up
                os.chmod(full, stat.S_IREAD | stat.S_IWRITE)
        self.tmp.cleanup()

    def manifest(self) -> dict:
        return json.loads((self.dest / "manifest.json").read_text(encoding="utf-8"))

    def assert_complete(self, dest: Path) -> None:
        """Every file of the backup at `dest` is there, and is exactly what its manifest says."""
        manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        for rel, (size, _mtime, sha) in manifest["files"].items():
            data = (dest / rel).read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (size, sha), rel)
        self.assertEqual(len(_tree(dest)), len(manifest["files"]) + 1)


class Backups(Base):
    def test_make_copies_every_file_with_a_manifest(self):
        os.chmod(self.game / "Data" / "lang.ini", stat.S_IREAD)  # a read-only game file: its copy isn't
        seen = []
        made = make(self.game, self.dest, progress=lambda done, total: seen.append((done, total)))
        self.assertEqual((made["path"], made["build"], made["files"]), (str(self.dest), BUILD, 6))
        manifest = self.manifest()
        self.assertEqual(manifest["build"], BUILD)
        self.assertEqual(manifest["game"], str(self.game))
        self.assertIn("EmptySteamDepot", manifest["folders"])
        self.assertTrue((self.dest / "EmptySteamDepot").is_dir())
        self.assertTrue(manifest["made"][:4].isdigit() and "T" in manifest["made"])
        self.assertEqual(sorted(manifest["files"]), [
            "Data/PC/190852/ZZ_GladPatchableWin.dat", "Data/PC/190852/ZZ_Win.dat", "Data/lang.ini",
            "Manual/RUSE_Manual_English.pdf", "Maps/PC/DataMapAlpha_v09.dat", "RUSE.exe"])
        for rel, (size, mtime, sha) in manifest["files"].items():
            original, copy = self.game / rel, self.dest / rel
            data = original.read_bytes()
            self.assertEqual((size, mtime, sha),
                             (len(data), os.stat(original).st_mtime, hashlib.sha256(data).hexdigest()))
            self.assertEqual(copy.read_bytes(), data)
            self.assertFalse(os.path.samefile(original, copy))  # an independent copy, never a hard link
            self.assertEqual(os.stat(copy).st_nlink, 1)
            self.assertEqual(os.stat(copy).st_mtime, os.stat(original).st_mtime)
            self.assertFalse(_read_only(copy), rel)
        self.assertEqual(seen[-1], (made["size"], made["size"]))
        self.assertFalse(Path(f"{self.dest}.partial").exists())
        self.assertEqual([(b["path"], b["build"], b["files"]) for b in list_backups(self.folder)],
                         [(str(self.dest), BUILD, 6)])
        self.assertEqual([p.name for p in self.folder.iterdir()], [BUILD])  # its lock went with it

    def test_the_default_place_is_on_the_games_drive(self):
        self.assertEqual(backup.backups_dir(self.game), Path(self.game.anchor) / "RUSE-Backup")
        self.assertEqual(backup.backup_path(self.folder, BUILD), self.dest)
        self.assertEqual(backup.backup_path(self.folder, None), self.folder / "no-build")
        self.assertEqual(steam_verify_url(), "steam://validate/21970")

    def test_a_backup_already_there_is_only_replaced_when_asked(self):
        make(self.game, self.dest)
        with self.assertRaisesRegex(BackupError, "already a backup of this build"):
            make(self.game, self.dest)
        (self.game / "Data" / "lang.ini").write_bytes(b"fr-FR")
        make(self.game, self.dest, replace=True)
        self.assertEqual((self.dest / "Data" / "lang.ini").read_bytes(), b"fr-FR")
        self.assertEqual([p.name for p in self.folder.iterdir()], [BUILD])  # the old one is gone, no .old left
        other = self.folder / "mine"
        (other / "notes").mkdir(parents=True)
        with self.assertRaisesRegex(BackupError, "isn't a backup: move or rename it"):
            make(self.game, other, replace=True)
        self.assertTrue((other / "notes").is_dir())  # a folder of the player's is never removed
        with self.assertRaisesRegex(BackupError, "inside the game folder"):
            make(self.game, self.game / "backup")
        with self.assertRaisesRegex(BackupError, "nor the game folder inside a backup"):
            make(self.game, self.game.parent, replace=True)  # it would move the game itself aside
        self.assertTrue((self.game / "RUSE.exe").is_file())
        with self.assertRaisesRegex(BackupError, "isn't the R.U.S.E folder"):
            make(self.root, self.dest)

    def test_not_enough_space_is_refused_before_copying(self):
        with mock.patch("rusemod.backup.free_space", return_value=1 << 20):
            with self.assertRaisesRegex(BackupError, r"needs 0\.\d GB, and 0\.0 GB is free"):
                make(self.game, self.dest)
        self.assertFalse(self.dest.exists() or Path(f"{self.dest}.partial").exists() or self.folder.exists())

    def test_a_half_made_backup_is_never_listed_or_used(self):
        partial = Path(f"{self.dest}.partial")
        _write(partial / "RUSE.exe", b"MZ game")
        (partial / "manifest.json").write_text(json.dumps({"build": BUILD, "made": "2026-09-30T20:00:00", "files": {}}))
        self.assertEqual(list_backups(self.folder), [])
        with self.assertRaisesRegex(BackupError, "isn't a complete backup"):
            check(self.game, partial.with_name(BUILD))
        made = make(self.game, self.dest)  # the leftover goes
        self.assertFalse(partial.exists())
        self.assertEqual([b["path"] for b in list_backups(self.folder)], [made["path"]])
        (self.folder / "set-aside-2026-09-30-200000" / "x").mkdir(parents=True)  # set-aside files aren't a backup
        self.assertEqual(len(list_backups(self.folder)), 1)

    def test_check_finds_what_changed_fast_and_deep(self):
        make(self.game, self.dest)
        clean = check(self.game, self.dest)
        self.assertEqual((clean["build_matches"], clean["changed"], clean["missing"], clean["added"], clean["hashed"]),
                         (True, [], [], [], 0))  # fast: nothing hashed when sizes and dates match
        pack = self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat"
        when = os.stat(pack)
        _write(pack, b"PATCHABLE PACK")  # same size, same date: only a deep check sees it
        os.utime(pack, ns=(when.st_atime_ns, when.st_mtime_ns))
        _write(self.game / "Maps" / "PC" / "DataMapAlpha_v09.dat", b"a bigger modded map pack")
        os.utime(self.game / "RUSE.exe")  # touched only: hashed, and not changed
        (self.game / "Data" / "lang.ini").unlink()
        _write(self.game / "Mods" / "mod.dat", b"another manager's file")
        fast = check(self.game, self.dest)
        self.assertEqual((fast["changed"], fast["missing"], fast["added"], fast["hashed"]),
                         (["Maps/PC/DataMapAlpha_v09.dat"], ["Data/lang.ini"], ["Mods/mod.dat"], 1))
        deep = check(self.game, self.dest, deep=True)
        self.assertEqual((deep["changed"], deep["missing"], deep["added"], deep["hashed"]),
                         (["Data/PC/190852/ZZ_GladPatchableWin.dat", "Maps/PC/DataMapAlpha_v09.dat"], ["Data/lang.ini"],
                          ["Mods/mod.dat"], 4))
        set_build(self.root, "99999999")
        self.assertFalse(check(self.game, self.dest)["build_matches"])

    def test_restore_brings_the_files_back_and_sets_the_added_ones_aside(self):
        make(self.game, self.dest)
        pack = self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        _write(pack, b"modded pack")
        (self.game / "Data" / "lang.ini").unlink()
        (self.game / "EmptySteamDepot").rmdir()
        _write(self.game / "Mods" / "deep" / "mod.dat", b"another manager's file")
        _write(self.game / "Data" / "PC" / "190852" / "extra.dat", b"a loose file")
        seen = []
        done = restore(self.game, self.dest, progress=lambda d, t: seen.append((d, t)), processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["set_aside"], done["kept"], done["left"], done["build"]),
                         (2, 2, 1, [], BUILD))
        self.assertEqual(pack.read_bytes(), b"pack " * 1000)
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"en-US")
        self.assertTrue((self.game / "EmptySteamDepot").is_dir())
        self.assertFalse((self.game / "Mods").exists())  # emptied by the move: its files are in the set-aside folder
        aside = Path(done["set_aside_to"])
        self.assertEqual(aside.parent, self.folder)  # beside the backups: making one again never takes it along
        self.assertTrue(aside.name.startswith("set-aside-"))
        self.assertEqual((aside / "Mods" / "deep" / "mod.dat").read_bytes(), b"another manager's file")
        self.assertEqual((aside / "Data" / "PC" / "190852" / "extra.dat").read_bytes(), b"a loose file")
        self.assertEqual((aside / "Data" / "PC" / "190852" / "ZZ_Win.dat").read_bytes(), b"modded pack")  # kept
        self.assertEqual(seen[-1][0], seen[-1][1])
        after = check(self.game, self.dest)
        self.assertEqual((after["changed"], after["missing"], after["added"], after["hashed"]), ([], [], [], 0))
        self.assertEqual(restore(self.game, self.dest, processes=NONE_RUNNING),
                         {"restored": 0, "set_aside": 0, "kept": 0, "set_aside_to": None, "left": [], "build": BUILD})
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), [BUILD, aside.name])  # no lock, no new folder

    def test_a_read_only_file_is_restored_and_stays_read_only(self):
        make(self.game, self.dest)
        pack = self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat"
        _write(pack, b"modded")
        os.chmod(pack, stat.S_IREAD)
        done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["kept"], done["left"]), (1, 1, []))
        self.assertEqual(pack.read_bytes(), b"patchable pack")
        self.assertTrue(_read_only(pack))
        self.assertEqual(_temps(self.game), [])

    def test_a_damaged_backup_copy_is_not_restored(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        (self.dest / "Data" / "lang.ini").write_bytes(b"xx-XX")  # the backup's own copy changed since
        done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["kept"], done["set_aside_to"]), (0, 0, None))
        self.assertEqual(done["left"], ["Data/lang.ini: the backup's copy is damaged (it doesn't match its checksum)"])
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")  # left as it was
        self.assertEqual(_temps(self.game), [])
        self.assertEqual([p.name for p in self.folder.iterdir()], [BUILD])  # no empty set-aside folder

    def test_another_build_is_refused(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        set_build(self.root, "99999999")  # Steam updated the game since
        with self.assertRaisesRegex(BackupError, "the backup is build 24670294, the game is build 99999999"):
            restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")

    def test_a_running_game_is_refused(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        copy = str(self.root / "RUSE-Instances" / "my-set" / "RUSE.exe")  # a modded copy's packs are the game's
        for running in ([(4312, str(self.game / "RUSE.exe"))], [(77, copy)],
                        [(5, str(self.game / "CrashSender" / "CrashSender.Release.x64.exe"))]):
            with self.subTest(running=running):
                with self.assertRaisesRegex(BackupError, r"R\.U\.S\.E\. is running: .*process"):
                    restore(self.game, self.dest, processes=lambda: running)
        with self.assertRaisesRegex(BackupError, r"RUSE\.exe \(process 4312\)\. Close the game"):
            restore(self.game, self.dest, processes=lambda: [(4312, str(self.game / "RUSE.exe"))])
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")
        other = [(9, "C:/Windows/notepad.exe")]  # anything else running doesn't matter
        self.assertEqual(restore(self.game, self.dest, processes=lambda: other)["restored"], 1)

    def test_only_a_game_folder_is_restored(self):
        make(self.game, self.dest)
        with self.assertRaisesRegex(BackupError, "isn't the R.U.S.E folder"):
            restore(self.root, self.dest, processes=NONE_RUNNING)

    def test_a_restore_needs_room_for_what_it_copies_back(self):
        make(self.game, self.dest)
        pack = self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        _write(pack, b"modded pack")
        with mock.patch("rusemod.backup.free_space", return_value=1 << 20):
            with self.assertRaisesRegex(BackupError, r"enough free space .* to restore the game's files: it needs"):
                restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual(pack.read_bytes(), b"modded pack")


class Links(Base):
    """A link inside the game folder (a mod manager's junction, say) is never followed: not backed up, not read, never
    written through; a restore moves the link itself aside."""

    def test_a_link_out_of_the_game_folder_is_never_followed(self):
        store = self.root / "ModManagerStore"
        _write(store / "store.dat", b"the mod manager's own file, outside the game")
        _link_folder(store, self.game / "Mods")
        made = make(self.game, self.dest)
        self.assertEqual(made["files"], 6)
        self.assertFalse((self.dest / "Mods").exists())  # what it points to isn't the game's
        self.assertEqual(backup.size_of(self.game), made["size"])
        _write(store / "new.dat", b"another of the manager's files")
        _write(store / "store.dat", b"CHANGED store file")
        found = check(self.game, self.dest)
        self.assertEqual((found["changed"], found["missing"], found["added"]), ([], [], ["Mods"]))
        done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["set_aside"], done["left"]), (0, 1, []))
        self.assertEqual(_tree(store), ["new.dat", "store.dat"])  # nothing outside was moved or written
        self.assertEqual((store / "store.dat").read_bytes(), b"CHANGED store file")
        self.assertFalse(os.path.lexists(self.game / "Mods"))
        self.assertTrue(backup._link(os.lstat(Path(done["set_aside_to"]) / "Mods")))  # the link itself, moved

    def test_a_link_back_into_the_game_folder_is_no_loop(self):
        _link_folder(self.game, self.game / "Loop")
        files = backup._files(self.game)
        self.assertEqual(sorted(rel for rel, _full, _st in files.values() if rel.startswith("Loop")), ["Loop"])
        made = make(self.game, self.dest)
        self.assertEqual((made["files"], backup.size_of(self.game)), (6, made["size"]))
        self.assertEqual(check(self.game, self.dest)["added"], ["Loop"])
        self.assertEqual(restore(self.game, self.dest, processes=NONE_RUNNING)["set_aside"], 1)
        self.assertEqual(check(self.game, self.dest)["added"], [])

    def test_a_link_in_place_of_a_game_folder_is_set_aside_and_never_written_through(self):
        make(self.game, self.dest)
        store = self.root / "ModManagerStore"
        _write(store / "190852" / "ZZ_Win.dat", b"the manager's own pack")
        os.replace(self.game / "Data" / "PC", self.root / "MovedAway")
        _link_folder(store, self.game / "Data" / "PC")
        found = check(self.game, self.dest)
        self.assertEqual((found["changed"], found["missing"], found["added"]),
                         ([], ["Data/PC/190852/ZZ_GladPatchableWin.dat", "Data/PC/190852/ZZ_Win.dat"], ["Data/PC"]))
        with mock.patch("rusemod.backup._move", side_effect=PermissionError(13, "in use")):  # the link won't move
            done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual(done["restored"], 0)
        self.assertEqual(len(done["left"]), 3)
        self.assertIn("Data/PC isn't a folder of the game's (a link to another place, or a file), so nothing was "
                      "written through it", done["left"][1])
        self.assertEqual(_tree(store), ["190852/ZZ_Win.dat"])
        self.assertEqual((store / "190852" / "ZZ_Win.dat").read_bytes(), b"the manager's own pack")
        done = restore(self.game, self.dest, processes=NONE_RUNNING)  # it moves: the game's own folder comes back
        self.assertEqual((done["restored"], done["set_aside"], done["left"]), (2, 1, []))
        self.assertFalse(backup._link(os.lstat(self.game / "Data" / "PC")))
        self.assertEqual(_tree(store), ["190852/ZZ_Win.dat"])
        self.assertEqual((store / "190852" / "ZZ_Win.dat").read_bytes(), b"the manager's own pack")
        self.assertEqual(check(self.game, self.dest, deep=True)["changed"], [])

    def test_a_link_in_place_of_a_game_file_is_changed_and_never_read(self):
        make(self.game, self.dest)
        store = self.root / "ModManagerStore"
        _write(store / "inside.dat", b"x")
        (self.game / "Data" / "lang.ini").unlink()
        _link_folder(store, self.game / "Data" / "lang.ini")
        found = check(self.game, self.dest, deep=True)
        self.assertEqual((found["changed"], found["added"], found["hashed"]), (["Data/lang.ini"], [], 5))
        done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["kept"], done["left"]), (1, 1, []))
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"en-US")
        self.assertEqual(_tree(store), ["inside.dat"])


class OneAtATime(Base):
    """Making and restoring, one app at a time across both apps; a restore waits for a modded copy being built."""

    def other_app(self, what: str) -> subprocess.Popen:
        """Another app (another process) holding the backups folder for `what`, until its input closes."""
        app = subprocess.Popen([sys.executable, "-c", OTHER_APP, str(self.folder), what], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, text=True, env=dict(os.environ, PYTHONPATH=str(SRC)))

        def stop():
            if app.returncode is None:
                app.kill()
            app.wait()
            for pipe in (app.stdin, app.stdout):
                with contextlib.suppress(OSError):
                    pipe.close()
        self.addCleanup(stop)
        self.assertEqual(app.stdout.readline().strip(), "held")
        return app

    def test_two_makes_at_once_the_second_is_refused_and_the_first_completes(self):
        refused = []

        def progress(done, total):
            if not refused:  # the other app starts the same backup while this one copies
                with self.assertRaises(BackupError) as said:
                    make(self.game, self.dest)
                refused.append(str(said.exception))
        with mock.patch.object(backup, "CHUNK", 1024):
            make(self.game, self.dest, progress)
        self.assertEqual(refused, ["The game backup is busy: the other app (the Launcher or the Studio) is making a "
                                   "backup. Wait for it to finish, then try again."])
        self.assert_complete(self.dest)
        self.assertEqual([p.name for p in self.folder.iterdir()], [BUILD])

    def test_the_other_app_at_work_refuses_and_one_that_stopped_does_not(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        other = self.other_app("make")
        with self.assertRaisesRegex(BackupError, r"the other app \(the Launcher or the Studio\) is making a backup"):
            make(self.game, self.dest, replace=True)
        with self.assertRaisesRegex(BackupError, "is making a backup"):
            restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")
        other.kill()  # it stopped (a crash, a power cut): what it held is a leftover
        other.wait()
        self.assertEqual(restore(self.game, self.dest, processes=NONE_RUNNING)["restored"], 1)
        other = self.other_app("restore")
        with self.assertRaisesRegex(BackupError, "is restoring the game's files"):
            make(self.game, self.dest, replace=True)
        other.communicate()  # it finished
        make(self.game, self.dest, replace=True)
        self.assertEqual(sorted(p.name for p in self.folder.iterdir() if p.is_file()), [])  # no lock left

    def test_a_restore_and_a_copy_being_built_wait_for_each_other(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        with backup.reading(self.folder):  # a Play building its copy, in this app or the other
            with self.assertRaisesRegex(BackupError, r"A modded copy of the game is being built .*wait for it"):
                restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")
        other = self.other_app("reading")  # a Test in game building in the other app
        with self.assertRaisesRegex(BackupError, "being built"):
            restore(self.game, self.dest, processes=NONE_RUNNING)
        other.kill()  # it stopped: its mark doesn't stop a restore
        other.wait()
        with backup._busy(self.folder, "restore"):  # a restore running: a build waits
            with self.assertRaisesRegex(BackupError, "The game's files are being restored: wait for it to finish."):
                with backup.reading(self.folder):
                    self.fail("built during a restore")
        with backup._busy(self.folder, "make"):  # a backup being made only reads the game: a build goes ahead
            with backup.reading(self.folder):
                pass
        self.assertEqual(restore(self.game, self.dest, processes=NONE_RUNNING)["restored"], 1)
        self.assertEqual(sorted(p.name for p in self.folder.iterdir() if p.is_file()), [])  # no marks left
        with backup.reading(self.root / "nowhere"):  # no backups folder: no backup to wait for, nothing made
            pass
        self.assertFalse((self.root / "nowhere").exists())

    def test_a_job_that_builds_a_copy_is_marked_while_it_runs(self):
        calls = backup.BackupCalls()
        calls._backups = self.folder
        self.folder.mkdir()
        seen = []
        work = calls._reading_game(self.game, lambda say: seen.append(backup._readers(self.folder)) or "built")
        self.assertEqual(work(print), "built")
        self.assertEqual((seen, list(self.folder.iterdir())), ([1], []))
        self.assertEqual(calls._reading_game(None, lambda say: "no game")(print), "no game")


class ChangingFiles(Base):
    """A game file written while make copies it is never saved half old, half new."""

    def setUp(self):
        super().setUp()
        self.big = self.game / "Data" / "PC" / "190852" / "Big.dat"
        _write(self.big, b"a" * 20000, time.time() - 86400)
        self.copying = Path(f"{self.dest}.partial") / "Data" / "PC" / "190852" / "Big.dat"  # while Big.dat is copied

    def test_a_file_written_while_it_is_copied_is_copied_again(self):
        new = b"b" * 20000
        written = []

        def progress(done, total):
            if self.copying.exists() and not written:  # Steam repairs it in place, halfway through the copy
                with open(self.big, "r+b") as f:
                    f.write(new)
                os.utime(self.big, (time.time(), time.time()))
                written.append(done)
        with mock.patch.object(backup, "CHUNK", 4096):
            make(self.game, self.dest, progress)
        self.assertTrue(written)
        size, mtime, sha = self.manifest()["files"]["Data/PC/190852/Big.dat"]
        self.assertEqual((self.dest / "Data" / "PC" / "190852" / "Big.dat").read_bytes(), new)
        self.assertEqual((size, mtime, sha), (len(new), os.stat(self.big).st_mtime, hashlib.sha256(new).hexdigest()))
        self.assert_complete(self.dest)
        self.assertEqual(check(self.game, self.dest, deep=True)["changed"], [])

    def test_a_file_that_keeps_changing_stops_the_backup(self):
        when = [1.0e9]

        def progress(done, total):
            if self.copying.exists():
                when[0] += 10
                os.utime(self.big, (when[0], when[0]))  # written again and again
        with mock.patch.object(backup, "CHUNK", 4096):
            with self.assertRaisesRegex(BackupError, r"Data/PC/190852/Big\.dat kept changing while it was being "
                                                     r"copied"):
                make(self.game, self.dest, progress)
        self.assertFalse(self.folder.exists())  # no backup, nothing half made, no lock


class DamagedManifests(Base):
    """A manifest whose paths could name a place outside the game folder: the backup is damaged, and never used."""

    def test_paths_outside_the_game_folder_are_refused(self):
        make(self.game, self.dest)
        clean = self.manifest()
        sha = hashlib.sha256(b"outside").hexdigest()
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        bad = ["../../../outside.txt", "Data/../../../../outside.txt", (self.root / "abs.txt").as_posix(),
               "/outside.txt", "C:/outside.txt", "D:outside.txt", "Data\\..\\..\\outside.txt", "Data//x.dat",
               "./RUSE.exe", "", "NUL", "Data/com1.ini", "Data/x. ", "Data/x."]
        for rel in bad:
            with self.subTest(rel=rel):
                files = dict(clean["files"], **{rel: [7, 0.0, sha]})
                (self.dest / "manifest.json").write_text(json.dumps(clean | {"files": files}), encoding="utf-8")
                with self.assertRaisesRegex(BackupError, "is damaged .*isn't a place inside the game folder"):
                    restore(self.game, self.dest, processes=NONE_RUNNING)
                with self.assertRaisesRegex(BackupError, "is damaged"):
                    check(self.game, self.dest)
                self.assertEqual(list_backups(self.folder), [])
        for folders in (["../../made-by-restore"], ["EmptySteamDepot", (self.root / "made").as_posix()], "Data"):
            with self.subTest(folders=folders):
                (self.dest / "manifest.json").write_text(json.dumps(clean | {"folders": folders}), encoding="utf-8")
                with self.assertRaisesRegex(BackupError, "is damaged"):
                    restore(self.game, self.dest, processes=NONE_RUNNING)
        for value in (["7", 0.0, sha], [-1, 0.0, sha], [7, "today", sha], [7, 0.0, "not a checksum"], [True, 0.0, sha]):
            with self.subTest(value=value):
                files = dict(clean["files"], **{"RUSE.exe": value})
                (self.dest / "manifest.json").write_text(json.dumps(clean | {"files": files}), encoding="utf-8")
                with self.assertRaisesRegex(BackupError, "has no size, date or checksum"):
                    restore(self.game, self.dest, processes=NONE_RUNNING)
                self.assertEqual(list_backups(self.folder), [])
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")  # nothing was restored
        self.assertFalse((self.root / "outside.txt").exists() or (self.root / "made-by-restore").exists())
        with self.assertRaisesRegex(BackupError, "isn't a backup: move or rename it"):  # make won't remove it
            make(self.game, self.dest, replace=True)
        (self.dest / "manifest.json").write_text(json.dumps(clean), encoding="utf-8")
        self.assertEqual(restore(self.game, self.dest, processes=NONE_RUNNING)["restored"], 1)


class SafeRestores(Base):
    """A restore that stops, fails or meets a player's own files leaves nothing half done behind, and deletes
    nothing."""

    def test_a_copy_that_fails_leaves_no_temporary_file(self):
        make(self.game, self.dest)
        pack = self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        _write(pack, b"modded pack")
        real = backup._Count.add

        def full(count, n):
            real(count, n)
            if count.done > 2048:
                raise OSError(errno.ENOSPC, "There is not enough space on the disk")
        with mock.patch.object(backup, "CHUNK", 1024), mock.patch.object(backup._Count, "add", full):
            done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual(done["left"], ["Data/PC/190852/ZZ_Win.dat: There is not enough space on the disk"])
        self.assertEqual((done["restored"], done["kept"], done["set_aside_to"]), (0, 0, None))
        self.assertEqual(pack.read_bytes(), b"modded pack")  # as it was
        self.assertEqual(_temps(self.game), [])

        def stop(count, n):  # the player closes the app mid-copy
            real(count, n)
            raise KeyboardInterrupt
        with mock.patch.object(backup._Count, "add", stop), self.assertRaises(KeyboardInterrupt):
            restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual(pack.read_bytes(), b"modded pack")
        self.assertEqual(_temps(self.game), [])
        self.assertEqual([p.name for p in self.folder.iterdir()], [BUILD])  # no lock, no set-aside folder

    def test_after_a_restore_that_stopped_the_next_one_finishes_it(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        _write(self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat.1a2b.restoring", b"pack pack")  # killed mid-copy
        (self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat").unlink()  # after moving the old version aside
        done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["set_aside"], done["kept"], done["left"]), (2, 1, 1, []))
        after = check(self.game, self.dest, deep=True)
        self.assertEqual((after["changed"], after["missing"], after["added"]), ([], [], []))
        self.assertEqual(_tree(Path(done["set_aside_to"])),
                         ["Data/PC/190852/ZZ_Win.dat.1a2b.restoring", "Data/lang.ini"])

    def test_a_players_own_restoring_file_is_kept(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        _write(self.game / "Data" / "lang.ini.restoring", b"the player's own notes")
        done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["set_aside"], done["kept"], done["left"]), (1, 1, 1, []))
        aside = Path(done["set_aside_to"])
        self.assertEqual((aside / "Data" / "lang.ini.restoring").read_bytes(), b"the player's own notes")
        self.assertEqual((aside / "Data" / "lang.ini").read_bytes(), b"de-DE")
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"en-US")

    def test_an_old_backup_a_make_left_behind_is_put_back(self):
        make(self.game, self.dest)
        old = Path(f"{self.dest}.old")
        os.replace(self.dest, old)  # a make cut between its two renames (a power cut)
        _write(Path(f"{self.dest}.partial") / "RUSE.exe", b"MZ")  # and its new one, half made
        self.assertEqual([b["path"] for b in list_backups(self.folder)], [str(self.dest)])
        self.assertFalse(old.exists())
        os.replace(self.dest, old)
        with self.assertRaisesRegex(BackupError, "already a backup of this build"):  # it's back, so it's kept
            make(self.game, self.dest)
        self.assert_complete(self.dest)
        os.replace(self.dest, old)
        (old / "manifest.json").write_text("{", encoding="utf-8")  # a damaged one isn't put back
        self.assertEqual(list_backups(self.folder), [])
        self.assertTrue(old.is_dir())
        make(self.game, self.dest)  # a new one replaces it
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), [BUILD])

    def test_a_backup_inside_the_game_folder_or_around_it_is_refused(self):
        make(self.game, self.dest)
        inside = self.game / "MyBackups" / BUILD
        inside.parent.mkdir()
        os.replace(self.dest, inside)  # the player moved the backup into the game folder
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        with self.assertRaisesRegex(BackupError, "A backup inside the game folder .* can't be restored from"):
            restore(self.game, inside, processes=NONE_RUNNING)
        self.assertTrue((inside / "manifest.json").is_file())
        with self.assertRaisesRegex(BackupError, "can't be restored from"):  # the game folder is the backup
            restore(inside, inside, processes=NONE_RUNNING)
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"de-DE")

    @unittest.skipUnless(winfiles.WINDOWS, "only Windows stops a move of a file a program has open")
    def test_a_file_in_use_is_left_in_place_and_never_copied(self):
        make(self.game, self.dest)
        held = self.game / "Mods" / "held.dat"
        _write(held, b"open in another program")
        _write(self.game / "Mods" / "free.dat", b"not open")
        with open(held, "rb"):
            done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["set_aside"], len(done["left"])), (1, 1))
        self.assertTrue(done["left"][0].startswith("Mods/held.dat: "), done["left"])
        self.assertEqual(held.read_bytes(), b"open in another program")
        self.assertEqual(_tree(Path(done["set_aside_to"])), ["Mods/free.dat"])  # no copy of the held file

    def test_a_game_on_another_drive_than_its_backups(self):
        make(self.game, self.dest)
        _write(self.game / "Data" / "lang.ini", b"de-DE")
        _write(self.game / "Mods" / "a.dat", b"a mod")
        _write(self.game / "Mods" / "b.dat", b"a mod in use")
        os.chmod(self.game / "Mods" / "a.dat", stat.S_IREAD)
        real_replace, real_remove = os.replace, os.remove

        def replace(src, dst):  # a game folder that is a link to another drive: a move out of it is refused
            if winfiles.inside(str(src), str(self.game)) and not winfiles.inside(str(dst), str(self.game)):
                raise OSError(errno.EXDEV, "The system cannot move the file to a different disk drive")
            return real_replace(src, dst)

        def remove(path):
            if Path(path).name == "b.dat" and winfiles.inside(str(path), str(self.game)):
                raise PermissionError(errno.EACCES, "The process cannot access the file")
            return real_remove(path)
        with mock.patch("os.replace", replace), mock.patch("os.remove", remove):
            done = restore(self.game, self.dest, processes=NONE_RUNNING)
        self.assertEqual((done["restored"], done["set_aside"], done["kept"]), (1, 1, 1))
        self.assertEqual(done["left"], ["Mods/b.dat: The process cannot access the file"])
        aside = Path(done["set_aside_to"])
        self.assertEqual(_tree(aside), ["Data/lang.ini", "Mods/a.dat"])  # copied, then removed from the game
        self.assertTrue(_read_only(aside / "Mods" / "a.dat"))
        self.assertEqual(_tree(self.game / "Mods"), ["b.dat"])  # left where it was, and not copied
        self.assertEqual((self.game / "Data" / "lang.ini").read_bytes(), b"en-US")


if __name__ == "__main__":
    unittest.main()
