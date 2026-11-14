"""The Studio's folders copied to a short path in one click (ruse_studio.homemove; the owner, 2026-11-13, his answer 8 to
"A Studio folder too deep for Windows: the message tells the modder to change a Windows setting, the only way now, or
should the Studio get its own setting for it?": "tell the modder, provide a quick fix that auto does it if they dont
want to do it manually").

On scratch folders only: a made-up platform folder and a made-up Documents\\RUSE 2.0 in each test's own temporary folder,
the short folder there too (homemove.short_target stood in for: never C:\\RUSE2), the Windows setting and the restart
stood in for (StudioApi._home_set_env, _home_restart: never the real user variable, never a real restart).
- the move copies everything (the platform folder but the window's own folder, and the modder's mods, maps, exports
  and backups), every file byte for byte, makes the copy name its own places (studio.json, the mod sets, the model
  records that name a copied file), sets RUSE_PLATFORM_HOME to the new folder, starts the Studio again, and deletes
  nothing;
- a file that doesn't arrive as it is: nothing switched, the copy taken away, the old folders as they were;
- two files landing on one place, another job running, long paths on or not Windows: refused at once in words;
- every refusal of a folder too deep (the Generic Horse's Add: the platform folder, the mod's folder, a path longer
  than Windows takes) is what the page offers the move beside (home_move_offer's "needed");
- the short folder the Studio picks, or one the modder chooses with Choose another folder… (the owner, 2026-11-13: "It
  can be selected automatically, but the modder should be able to choose"), each checked the same way before anything
  is copied: on a drive of this PC, empty or new, outside what gets copied and the game's folder, short enough; an
  empty folder he chose is left there when a copy fails;
- the words the page shows, in the 11 languages."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)

from test_horse_squad import stand_in
from test_studio import WithMod
from ruse_studio import homemove, horse_squad
from ruse_studio.api import StudioApi, StudioError


def finished(api, job: str, most: float = 120) -> dict:
    end = time.monotonic() + most
    while time.monotonic() < end:
        view = api.job(job)
        if view["state"] != "running":
            return view
        time.sleep(0.05)
    raise AssertionError(f"job {job} still running after {most} s")


def tree(folder: Path) -> dict:
    """{each file's path in `folder`: its bytes}."""
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}


class TheMove(unittest.TestCase):
    """A modder's platform folder and his Documents\\RUSE 2.0, moved to a short folder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="homemove-")
        root = Path(self.tmp.name)
        self.home = root / "Users" / "Jane Q Doe" / "AppData" / "Local" / "RUSE Mod Platform"
        self.work = root / "Users" / "Jane Q Doe" / "Documents" / "RUSE 2.0"
        self.to = root / "RUSE2"
        mod = self.work / "Mods" / "cavalry"
        self.files = {
            self.home / "settings.json": json.dumps({"game_dir": "D:/Games/RUSE", "prefs": {"studio": {"lang": "us"}}}),
            self.home / "studio.json": json.dumps({"mod": str(mod), "recent": [str(mod), "D:/elsewhere/other"]}),
            self.home / "sets" / "mine.toml": f'name = "Mine"\nmods = [{json.dumps(str(mod))}, "steam-mod-id"]\n',
            self.home / "library" / "air-nerf" / "mod.toml": '[mod]\nid = "air-nerf"\n',
            self.home / "horse_squad" / "horse-squad-rifle.glb": b"glTF rifle",
            self.home / "index" / "game-index.sqlite": b"SQLite format 3\0" + bytes(range(256)) * 40,
            self.home / "logs" / "studio.log": "a line\n",
            self.home / "webview" / "EBWebView" / "held.bin": b"the window's own",
            mod / "mod.toml": '[mod]\nid = "cavalry"\nname = "Cavalry"\nversion = "1.0.0"\n',
            mod / "files" / "models" / "Descriptor_Unit_Horse_Squad.json":
                json.dumps({"from": str(self.home / "horse_squad" / "horse-squad-rifle.glb"), "size": 1.0}, indent=1),
            mod / "files" / "models" / "Descriptor_Unit_Tank.json":
                json.dumps({"from": str(mod / "blender" / "Descriptor_Unit_Tank" / "kept" / "Descriptor_Unit_Tank.glb"),
                            "size": 1.2}, indent=1),
            mod / "files" / "models" / "Descriptor_Unit_Jeep.json":
                json.dumps({"from": "D:\\models\\jeep.glb", "size": 1.0}, indent=1),
            mod / "blender" / "Descriptor_Unit_Tank" / "kept" / "Descriptor_Unit_Tank.glb": b"glTF tank",
            self.work / "Maps" / "m1" / "mod.toml": '[mod]\nid = "m1"\n',
            self.work / "Exports" / "cavalry-1.0.0.rusemod": b"PK\x03\x04 a package",
            self.work / "Backups" / "cavalry-0.9" / "mod.toml": '[mod]\nid = "cavalry"\n',
        }
        for path, data in self.files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            (path.write_bytes if isinstance(data, bytes) else lambda t, p=path: p.write_text(t, encoding="utf-8"))(data)
        self.before = {"home": tree(self.home), "work": tree(self.work)}
        self.api = StudioApi(home=self.home, work=self.work, instances=root / "copies")
        self.set, self.restarted = [], []
        self.api._home_set_env = lambda name, value: self.set.append((name, value))
        self.api._home_restart = self.restarted.append
        for patch in (mock.patch.object(homemove, "short_target", lambda home: self.to),
                      mock.patch.object(horse_squad, "long_paths_on", lambda: False),
                      mock.patch.object(homemove.sys, "platform", "win32")):
            patch.start()
            self.addCleanup(patch.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_everything_is_copied_checked_switched_and_nothing_deleted(self):
        view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        got = tree(self.to)
        for rel, data in self.before["home"].items():          # the platform folder: all of it but the window's own
            if rel.startswith("webview/"):
                self.assertNotIn(rel, got)
            elif rel not in ("studio.json", "sets/mine.toml"):
                self.assertEqual(got[rel], data, rel)
        for kind, name in (("Mods", "mods"), ("Maps", "maps"), ("Exports", "exports"), ("Backups", "mod-backups")):
            for rel, data in self.before["work"].items():      # his mods, maps, exports and backups, under the names a
                if rel.startswith(kind + "/") and not rel.endswith(".json"):   # platform folder set by hand has
                    self.assertEqual(got[name + rel[len(kind):]], data, rel)
        self.assertEqual(tree(self.home), self.before["home"])  # nothing deleted, nothing changed
        self.assertEqual(tree(self.work), self.before["work"])
        self.assertEqual(self.set, [("RUSE_PLATFORM_HOME", str(self.to))])
        self.assertEqual(self.restarted, [self.to])
        result = view["result"]
        self.assertEqual((result["to"], result["old"], result["restarting"]),
                         (str(self.to), [str(self.home), str(self.work)], True))
        self.assertEqual(result["files"], len(self.before["home"]) - 1 + len(self.before["work"]))

    def test_the_copy_names_its_own_places(self):
        """The Studio's record, the mod set and the model records that name a copied file name the copy's; one naming
        a file elsewhere stays byte for byte."""
        view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        new_mod = self.to / "mods" / "cavalry"
        studio = json.loads((self.to / "studio.json").read_text(encoding="utf-8"))
        self.assertEqual(studio["mod"], str(new_mod))
        self.assertEqual(studio["recent"], [str(new_mod), "D:/elsewhere/other"])
        self.assertIn(json.dumps(str(new_mod)), (self.to / "sets" / "mine.toml").read_text(encoding="utf-8"))
        models = new_mod / "files" / "models"
        self.assertEqual(json.loads((models / "Descriptor_Unit_Horse_Squad.json").read_text(encoding="utf-8"))["from"],
                         str(self.to / "horse_squad" / "horse-squad-rifle.glb"))
        self.assertEqual(json.loads((models / "Descriptor_Unit_Tank.json").read_text(encoding="utf-8"))["from"],
                         str(new_mod / "blender" / "Descriptor_Unit_Tank" / "kept" / "Descriptor_Unit_Tank.glb"))
        self.assertEqual((models / "Descriptor_Unit_Jeep.json").read_bytes(),
                         self.before["work"]["Mods/cavalry/files/models/Descriptor_Unit_Jeep.json"])
        # (a record's other bytes as they were: only its "from" string is another)
        was = self.before["work"]["Mods/cavalry/files/models/Descriptor_Unit_Tank.json"]
        self.assertEqual((models / "Descriptor_Unit_Tank.json").read_bytes(),
                         was.replace(json.dumps(str(self.work / "Mods" / "cavalry"))[1:-1].encode(),
                                     json.dumps(str(new_mod))[1:-1].encode()))
        self.assertTrue(any("1 model record(s)" in ln or "2 model record(s)" in ln for ln in view["lines"]))

    def test_a_file_that_doesnt_arrive_as_it_is_switches_nothing_and_the_copy_goes(self):
        real = homemove._same

        def differs(src, dst):
            return False if src.endswith("game-index.sqlite") else real(src, dst)
        with mock.patch.object(homemove, "_same", differs):
            view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn("game-index.sqlite didn't arrive in", view["message"])
        self.assertIn("nothing was switched and the copy was taken away again", view["message"])
        self.assertFalse(self.to.exists())
        self.assertEqual((self.set, self.restarted), ([], []))
        self.assertEqual(tree(self.home), self.before["home"])
        self.assertEqual(tree(self.work), self.before["work"])

    def test_a_file_written_while_it_was_copied_is_copied_again(self):
        """A log that gets a line while the move copies it is copied again and checked again, not a failed move."""
        real, seen = homemove._same, []

        def once(src, dst):
            if src.endswith("studio.log") and not seen:
                seen.append(src)
                return False
            return real(src, dst)
        with mock.patch.object(homemove, "_same", once):
            view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(len(seen), 1)

    def test_a_file_that_cant_be_read_is_said_in_words(self):
        def held(src, dst, *a, **k):
            raise PermissionError(13, "Permission denied", src)
        with mock.patch.object(homemove.shutil, "copy2", held):
            view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn("another program has it open or Windows didn't allow it", view["message"])
        self.assertNotIn("Permission denied", view["message"])
        self.assertFalse(self.to.exists())
        self.assertEqual(self.set, [])

    def test_two_files_landing_on_one_place_are_refused(self):
        clash = self.home / "mods" / "cavalry" / "mod.toml"     # (one left in the platform folder from before)
        clash.parent.mkdir(parents=True)
        clash.write_text('[mod]\nid = "cavalry"\n', encoding="utf-8")
        view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn("Two files would be copied to the same place", view["message"])
        self.assertFalse(self.to.exists())
        self.assertEqual(self.set, [])

    def test_the_windows_setting_refused_is_said_with_what_to_do(self):
        def refused(name, value):
            raise PermissionError(5, "Access is denied")
        self.api._home_set_env = refused
        view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "failed")
        self.assertEqual(view["message"], (
            f"Everything is copied to {self.to} and checked, but the Windows setting RUSE_PLATFORM_HOME couldn't be set. "
            f"Set it to {self.to} yourself (Windows: Edit environment variables for your account), then start the "
            f"Studio again."))
        self.assertEqual(self.restarted, [])
        self.assertTrue((self.to / "settings.json").is_file())   # (the checked copy stays for him to use)

    def test_a_restart_that_cant_start_says_to_start_it_again(self):
        def cant(to):
            raise OSError(2, "No such file")
        self.api._home_restart = cant
        view = finished(self.api, self.api.home_move()["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertFalse(view["result"]["restarting"])
        self.assertIn(f"Close the Studio and start it again: it then uses {self.to}.", view["lines"])

    def test_refused_at_once_when_there_is_nothing_to_fix_or_a_job_runs(self):
        with mock.patch.object(horse_squad, "long_paths_on", lambda: True), \
                self.assertRaisesRegex(StudioError, "Windows takes long paths for the Studio on this PC"):
            self.api.home_move()
        with mock.patch.object(homemove.sys, "platform", "linux"), \
                self.assertRaisesRegex(StudioError, "so its folders don't need to move"):
            self.api.home_move()

        class Running:
            state = "running"
        self.api._jobs["x"] = Running()
        with self.assertRaisesRegex(StudioError, "The Studio is busy with another job"):
            self.api.home_move()
        self.assertFalse(self.to.exists())

    def test_the_offer_says_where_from_where_to_and_how_much(self):
        offer = self.api.home_move_offer(count_all=True)
        self.assertEqual((offer["needed"], offer["can"], offer["from"], offer["files"], offer["to"]),
                         (None, True, str(self.home), str(self.work), str(self.to)))
        self.assertEqual(offer["count"], len(self.before["home"]) - 1 + len(self.before["work"]))
        self.assertEqual(offer["size"], sum(len(d) for r, d in self.before["home"].items() if not r.startswith("webview/"))
                         + sum(len(d) for d in self.before["work"].values()))
        self.assertEqual(offer["leave"], ["webview"])
        with mock.patch.object(horse_squad, "long_paths_on", lambda: True):
            self.assertFalse(self.api.home_move_offer()["can"])


class TheChosenFolder(unittest.TestCase):
    """The short folder picked automatically, or one the modder chooses instead (the owner, 2026-11-13, to "The short
    folder, such as C:\\RUSE2, is picked automatically. OK, or should the modder choose?": "It can be selected
    automatically, but the modder should be able to choose"): Choose another folder… (home_move_choose, the folder
    window stood in for: _home_pick), both checked the same way before anything is copied. On e9a092c3 home_move took
    no folder and there was no Choose. TheMove's folders and stand-ins (never the real Windows setting)."""
    setUp = TheMove.setUp
    tearDown = TheMove.tearDown

    def chooses(self, folder):
        """home_move_choose with the folder window answering `folder` (None: cancelled); the start it was opened at."""
        asked = []
        self.api._home_pick = lambda window, start: asked.append(start) or (str(folder) if folder else None)
        return self.api.home_move_choose(), asked

    def test_a_chosen_folder_gets_everything_and_the_studio_switches_to_it(self):
        chosen = Path(self.tmp.name) / "Games" / "R2"            # (a new folder: made by the move)
        got, asked = self.chooses(chosen)
        self.assertEqual(got, {"to": str(chosen)})
        self.assertEqual(asked, [self.to.parent])                 # (opened at the top of the drive the Studio picked on)
        view = finished(self.api, self.api.home_move(got["to"])["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        moved = tree(chosen)
        self.assertEqual(moved["library/air-nerf/mod.toml"], self.before["home"]["library/air-nerf/mod.toml"])
        self.assertEqual(moved["mods/cavalry/mod.toml"], self.before["work"]["Mods/cavalry/mod.toml"])
        self.assertEqual(json.loads(moved["mods/cavalry/files/models/Descriptor_Unit_Horse_Squad.json"])["from"],
                         str(chosen / "horse_squad" / "horse-squad-rifle.glb"))
        self.assertFalse(self.to.exists())                        # (not the folder the Studio picked)
        self.assertEqual(self.set, [("RUSE_PLATFORM_HOME", str(chosen))])
        self.assertEqual(self.restarted, [chosen])
        self.assertEqual(view["result"]["to"], str(chosen))
        self.assertEqual(tree(self.home), self.before["home"])   # nothing deleted, nothing changed
        self.assertEqual(tree(self.work), self.before["work"])

    def test_an_empty_folder_he_made_is_used_and_left_there_empty_when_the_copy_fails(self):
        chosen = Path(self.tmp.name) / "Mine"
        chosen.mkdir()
        self.assertEqual(self.chooses(chosen)[0], {"to": str(chosen)})
        real = homemove._same

        def differs(src, dst):
            return False if src.endswith("studio.log") else real(src, dst)
        with mock.patch.object(homemove, "_same", differs):
            view = finished(self.api, self.api.home_move(str(chosen))["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn("nothing was switched and the copy was taken away again", view["message"])
        self.assertTrue(chosen.is_dir())                          # (his folder stays, as it was: empty)
        self.assertEqual(list(chosen.iterdir()), [])
        self.assertEqual((self.set, self.restarted), ([], []))

    def test_a_cancelled_window_chooses_nothing(self):
        self.assertEqual(self.chooses(None)[0], {"to": None})
        self.api._home_pick = None
        self.assertIsNone(self.api._window)
        self.assertEqual(self.api.home_move_choose(), {"to": None})   # (no window: no folder window opened)

    def test_a_folder_that_cant_be_the_short_folder_is_refused_in_words(self):
        root = Path(self.tmp.name)
        full = root / "Full"
        full.mkdir()
        (full / "his.txt").write_text("his", encoding="utf-8")
        a_file = root / "a-file.txt"
        a_file.write_text("x", encoding="utf-8")
        game = root / "Steam" / "R.U.S.E"
        game.mkdir(parents=True)
        self.api._game_dir = game
        free = next((f"{c}:\\" for c in "ZYXWVUTSRQPONMLKJIHGFEB" if not os.path.isdir(f"{c}:\\")), None)
        cases = [(full, f"{full} isn't an empty folder: choose an empty folder, or make a new one in the folder window."),
                 (a_file, f"{a_file} isn't an empty folder"),
                 (self.home / "R2", f"{self.home / 'R2'} is inside {self.home}, which is what gets copied: choose a "
                                    f"folder outside it."),
                 (self.work / "Mods" / "R2", f"{self.work / 'Mods' / 'R2'} is inside {self.work}, which is what gets "
                                             f"copied"),
                 (game / "RUSE2", f"{game / 'RUSE2'} is inside the R.U.S.E. folder ({game}): the Studio's files can't go "
                                  f"there. Choose a folder outside the game."),
                 ("RUSE2", "RUSE2 isn't on a drive of this PC: choose a folder on one of its drives.")]
        if free is not None and sys.platform == "win32":
            cases.append((free + "RUSE2", f"{free}RUSE2 isn't on a drive of this PC"))
        for folder, said in cases:
            with self.subTest(folder=str(folder)):
                with self.assertRaises(StudioError) as caught:
                    self.chooses(folder)
                self.assertTrue(str(caught.exception).startswith(said), str(caught.exception))
                with self.assertRaises(StudioError) as again:   # (the move itself checks it again, at once)
                    self.api.home_move(str(folder))
                self.assertEqual(str(again.exception), str(caught.exception))
        self.assertEqual(list(full.iterdir()), [full / "his.txt"])
        self.assertFalse((game / "RUSE2").exists())
        self.assertEqual((self.set, self.restarted, self.api._jobs), ([], [], {}))
        from ruse_studio import errortext
        message = str(caught.exception)
        self.assertNotEqual(errortext.worded(message, "fr"), message)  # (in the modder's language)

    def test_short_enough_for_what_was_refused_the_studio_s_pick_too(self):
        """Short enough: the path the refusal measured, once in the folder, fits what Windows takes; the folder the
        Studio picks is checked the same way, so a move that wouldn't help is refused before anything is copied."""
        mod = self.work / "Mods" / "cavalry"
        fits = len(str(mod)) - len(str(self.to / "mods" / "cavalry"))   # (the most the move to self.to shortens it)
        deeper = Path(self.tmp.name) / "abc" / "RUSE2"                  # (4 characters longer than self.to)
        self.api.__dict__["_too_deep"] = {"what": "mod", "folder": str(mod), "over": fits}
        self.assertEqual(homemove.still_over(self.to, self.home, self.work, self.api.__dict__["_too_deep"]), 0)
        with self.assertRaises(StudioError) as caught:
            self.chooses(deeper)
        self.assertEqual(str(caught.exception), (
            f"{deeper} is too deep: there, the path that was too long would still be 4 character(s) longer than Windows "
            f"takes. Choose a folder nearer the top of a drive, or give the mod or the unit a shorter name."))
        self.api.__dict__["_too_deep"] = {"what": "mod", "folder": str(mod), "over": fits + 2}
        with self.assertRaisesRegex(StudioError, "would still be 2 character"):
            self.api.home_move()                                   # (the Studio's own pick: refused at once too)
        self.assertFalse(self.to.exists())
        self.api.__dict__["_too_deep"] = {"what": "platform", "folder": str(self.home),
                                          "over": len(str(self.home)) - len(str(self.to))}
        self.assertEqual(homemove.still_over(self.to, self.home, self.work, self.api.__dict__["_too_deep"]), 0)
        self.assertEqual(homemove.still_over(deeper, self.home, self.work, self.api.__dict__["_too_deep"]), 4)
        long = str(self.home / horse_squad.FOLDER / ("x" * 300))         # (a path inside the platform folder: it
        shorter = len(str(self.home)) - len(str(self.to))               # moves with it, that much shorter)
        needed = {"what": "path", "folder": long, "over": shorter + 7}
        self.assertEqual(homemove.still_over(self.to, self.home, self.work, needed), 7)
        needed["over"] = shorter
        self.assertEqual(homemove.still_over(self.to, self.home, self.work, needed), 0)
        elsewhere = {"what": "mod", "folder": "D:\\elsewhere\\mod", "over": 50}   # (not a folder the move copies)
        self.assertEqual(homemove.still_over(self.to, self.home, self.work, elsewhere), 0)
        self.api.__dict__["_too_deep"] = {"what": "mod", "folder": str(mod), "over": fits}
        view = finished(self.api, self.api.home_move()["job"])     # (and one that fits is moved)
        self.assertEqual(view["state"], "done", view.get("message"))

    def test_the_studio_s_pick_is_checked_the_same_way(self):
        self.to.mkdir()
        (self.to / "someone else's.txt").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(StudioError, "isn't an empty folder"):
            self.api.home_move()
        self.assertEqual(sorted(p.name for p in self.to.iterdir()), ["someone else's.txt"])


class TheShortFolder(unittest.TestCase):
    def test_the_first_free_name_on_the_platform_folder_s_drive(self):
        taken = set()
        with mock.patch.object(homemove.os.path, "lexists", lambda p: str(p) in taken):
            self.assertEqual(homemove.short_target(Path("D:/Users/x/AppData/Local/RUSE Mod Platform")), Path("D:/RUSE2"))
            taken.add(str(Path("D:/RUSE2")))
            taken.add(str(Path("D:/RUSE2-2")))
            self.assertEqual(homemove.short_target(Path("D:/deep/home")), Path("D:/RUSE2-3"))

    def test_the_studio_starts_again_as_it_was_started(self):
        with mock.patch.object(homemove.sys, "argv", ["x", "--debug"]), \
                mock.patch.object(homemove.sys, "executable", "C:/py/python.exe"):
            self.assertEqual(homemove.restart_command(), ["C:/py/python.exe", "-m", "ruse_studio", "--debug"])
            with mock.patch.object(homemove.sys, "frozen", True, create=True):
                self.assertEqual(homemove.restart_command(), ["C:/py/python.exe", "--debug"])
        started = []
        with mock.patch("rusemod.update._quit_soon", lambda s: started.append(("quit", s))):
            homemove.restart(Path("C:/RUSE2"), popen=lambda cmd, **kw: started.append((cmd, kw["env"]["RUSE_PLATFORM_HOME"])))
        self.assertEqual(started[0][1], str(Path("C:/RUSE2")))
        self.assertEqual(started[-1], ("quit", homemove.QUIT_AFTER))

    def test_a_folder_too_deep_for_windows_paths_is_still_read(self):
        if sys.platform != "win32":
            self.skipTest("Windows' own paths")
        self.assertEqual(homemove._long("C:/a/b"), "\\\\?\\C:\\a\\b")
        self.assertEqual(homemove._long("\\\\server\\share\\x"), "\\\\?\\UNC\\server\\share\\x")
        self.assertEqual(homemove._shown("\\\\?\\C:\\a\\b"), "C:\\a\\b")
        with tempfile.TemporaryDirectory() as d:
            deep = Path(d) / ("d" * 120) / ("e" * 120) / "f.bin"        # (past 259 characters)
            os.makedirs(homemove._long(deep.parent))
            Path(homemove._long(deep)).write_bytes(b"deep")
            files, _folders = homemove.files_of([(Path(d) / ("d" * 120), Path(d) / "out")])
            homemove.copy_checked(files, _folders)
            self.assertEqual(Path(homemove._long(Path(d) / "out" / ("e" * 120) / "f.bin")).read_bytes(), b"deep")
            import shutil
            shutil.rmtree(homemove._long(Path(d) / ("d" * 120)))


class EveryTooDeepRefusalOffersIt(WithMod):
    """The Studio's refusals of a folder too deep (the Generic Horse's Add, ruse_studio.horse_squad): each leaves
    home_move_offer's "needed" saying so, which the page shows the quick fix for; an Add that works clears it."""

    def setUp(self):
        super().setUp()
        off = mock.patch.object(horse_squad, "long_paths_on", lambda: False)
        off.start()
        self.addCleanup(off.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")
        self.folder = Path(self.api.new_mod("Room")["current"])

    def add(self, longest, name="Generic Horse"):
        from test_horse_squad import finished as done
        module = stand_in(self.rifle, self.heavy)
        module.longest_written = longest
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: module}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            try:
                return done(self.api, self.api.horse_squad_add(0, 10, name, 7, group="new")["job"])
            except StudioError as exc:
                return exc

    def test_the_platform_folder_too_deep(self):
        said = self.add(lambda out: horse_squad.PATH_MOST + 3)
        self.assertIsInstance(said, StudioError)
        self.assertIn("RUSE_PLATFORM_HOME", str(said))           # (his own words to do it by hand, kept)
        self.assertEqual(self.api.home_move_offer()["needed"],
                         {"what": "platform", "folder": str(self.home), "over": 3})

    def test_the_mod_s_folder_too_deep(self):
        room = horse_squad.PATH_MOST - len(str(Path(self.folder, *horse_squad.OWN_CLIPS, "Descriptor_Unit_",
                                                    "x" * horse_squad.CLIP_LONGEST + ".part")))
        said = self.add(lambda out: 10, name="H" * (room + 1))
        self.assertIsInstance(said, StudioError)
        self.assertEqual(self.api.home_move_offer()["needed"], {"what": "mod", "folder": str(self.folder), "over": 1})
        view = self.add(lambda out: 10, name="H" * room)          # (and an Add that goes through clears it)
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertIsNone(self.api.home_move_offer()["needed"])

    def test_a_later_refusal_of_another_kind_offers_nothing(self):
        """The note is the last Add's own: refused for another reason after a folder too deep, nothing is offered."""
        self.assertIsInstance(self.add(lambda out: horse_squad.PATH_MOST + 3), StudioError)
        self.assertIsNotNone(self.api.home_move_offer()["needed"])
        taken = self.api.new_unit(horse_squad.SQUAD, "Taken", 5, group="new")["address"]
        said = self.add(lambda out: 10, name="Taken")                 # (the name's address is taken: refused)
        self.assertIsInstance(said, StudioError, taken)
        self.assertIn("There's already a unit called", str(said))
        self.assertIsNone(self.api.home_move_offer()["needed"])

    def test_a_path_longer_than_windows_takes_after_all(self):
        import errno
        long = str(self.home / horse_squad.FOLDER / ("x" * 300))

        def builder_stops(game, out, **kw):
            raise FileNotFoundError(errno.ENOENT, "No such file", long)
        module = stand_in(self.rifle, self.heavy)
        module.horse_squad_glbs = builder_stops
        from test_horse_squad import finished as done
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: module}):
            view = done(self.api, self.api.horse_squad_add(0, 10, "Generic Horse", 7, group="new")["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn("longer than Windows takes in a path", view["message"])
        self.assertEqual(self.api.home_move_offer()["needed"],
                         {"what": "path", "folder": long, "over": len(long) - horse_squad.PATH_MOST})


class TheWords(unittest.TestCase):
    def test_the_page_s_words_and_the_lines_in_every_language(self):
        from ruse_studio.api import _words
        from rusemod import buildtext, schema, wordedtext
        words = _words()
        keys = ("home_move_title", "home_move_why", "home_move_what", "home_move_files", "home_move_close_launcher",
                "home_move_button", "tip_home_move", "home_move_done", "home_move_done_start_again",
                "home_move_choose", "tip_home_move_choose")
        for key in keys:
            self.assertEqual([lang for lang in schema.APP_LANGS if not words[key].get(lang)], [], key)
        js = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "eraunits.js").read_text(encoding="utf-8")
        for key in keys:
            self.assertIn(f"w.{key}", js, key)
        self.assertIn("api().home_move_offer()", js)
        self.assertIn("api().home_move(moveChosen)", js)      # (the folder chosen, or null: the Studio's pick)
        self.assertIn("api().home_move_choose()", js)
        # Choose another folder… sits beside the copy button, its tooltip on it
        self.assertIn('el("div", { className: "actions" }, go, pick)', js)
        self.assertIn("title: fill(w.tip_home_move_choose, { to: o.to })", js)
        self.assertNotIn("Copied", buildtext.worded("Copied 3 of 9 files.", "ger"))
        self.assertEqual(wordedtext.missing(buildtext.FILE, buildtext.templates()), [])


if __name__ == "__main__":
    unittest.main()
