"""Where what people make is kept (rusemod.yourfiles: Documents\\RUSE 2.0), the move there from the platform folder, and
the Studio's Show this mod's folder, Delete a mod… and Where your files are (the owner, 2026-10-30: "the file paths for
new mods ... not very clear or easy to follow", "delete the various mods in the studio, just like ... boop, I don't want
this anymore"). The Recycle Bin is a stand-in here: no test fills the PC's own bin."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import package, recycle, yourfiles
from rusemod.library import Library
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError


def make_mod(folder: Path, mod_id: str, name: str = "", files: dict | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nname = "{name or mod_id}"\nversion = "0.1.0"\n',
                                     encoding="utf-8")
    for rel, data in (files or {}).items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_bytes(data)
    return folder


class Folders(unittest.TestCase):
    def test_documents_or_the_platform_folder(self):
        home, work = Path("home"), Path("Documents", "RUSE 2.0")
        self.assertEqual(yourfiles.folders(home, None), {"mods": home / "mods", "maps": home / "maps",
                                                         "exports": home / "exports", "backups": home / "mod-backups"})
        self.assertEqual(yourfiles.folders(home, work), {"mods": work / "Mods", "maps": work / "Maps",
                                                         "exports": work / "Exports", "backups": work / "Backups"})
        self.assertEqual(yourfiles.old_folders(home, None), {})
        self.assertEqual(yourfiles.old_folders(home, work)["backups"], home / "mod-backups")

    def test_a_platform_folder_set_by_hand_keeps_everything(self):
        with mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": "D:/somewhere"}):
            self.assertIsNone(yourfiles.documents_home())

    def test_the_pcs_documents_folder(self):
        found = yourfiles.documents()  # read only: nothing is made
        self.assertTrue(found is None or found.is_dir())


class MoveIn(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home, self.work = root / "platform", root / "Documents" / "RUSE 2.0"
        self.tank = make_mod(self.home / "mods" / "tank", "tank", files={"src/studio.rndf": b"patch\n"})
        self.beach = make_mod(self.home / "maps" / "beach", "beach", files={"maps/X/terrain.toml": b"[x]\n"})
        (self.home / "exports").mkdir()
        (self.home / "exports" / "tank-0.1.0.rusemod").write_bytes(b"PK\x03\x04 zip")
        (self.home / "mod-backups").mkdir()
        (self.home / "mod-backups" / "tank-format0.zip").write_bytes(b"PK backup")
        elsewhere = make_mod(root / "elsewhere" / "theirs", "theirs")
        (self.home / "studio.json").write_text(json.dumps({
            "mod": str(self.tank), "map": str(self.beach), "recent": [str(self.tank), str(elsewhere)],
            "recent_maps": [str(self.beach)]}), encoding="utf-8")
        (self.home / "sets").mkdir()
        tank_written = json.dumps(str(self.tank))
        (self.home / "sets" / "test.toml").write_text(
            f'# by hand\nname = "Test"\nmods = ["econ-half", {tank_written}, "../maps/beach"]\n', encoding="utf-8")
        self.elsewhere = elsewhere

    def tearDown(self):
        self.tmp.cleanup()

    def test_everything_moved_and_the_records_follow(self):
        res = yourfiles.move_in(self.home, self.work)
        tank, beach = self.work / "Mods" / "tank", self.work / "Maps" / "beach"
        self.assertEqual(sorted(res["moved"]), sorted(str(p) for p in (
            tank, beach, self.work / "Exports" / "tank-0.1.0.rusemod", self.work / "Backups" / "tank-format0.zip")))
        self.assertEqual(res["left"], [])
        self.assertEqual((tank / "src" / "studio.rndf").read_bytes(), b"patch\n")
        for old in ("mods", "maps", "exports", "mod-backups"):
            self.assertFalse((self.home / old).exists(), old)  # emptied, then gone
        settings = json.loads((self.home / "studio.json").read_text(encoding="utf-8"))
        self.assertEqual(settings, {"mod": str(tank), "map": str(beach), "recent": [str(tank), str(self.elsewhere)],
                                    "recent_maps": [str(beach)]})  # a folder opened from elsewhere stays as it was
        text = (self.home / "sets" / "test.toml").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# by hand\n"))  # the rest of the file as it was
        self.assertEqual(tomllib.loads(text)["mods"], ["econ-half", str(tank), str(beach)])
        self.assertEqual(yourfiles.move_in(self.home, self.work)["moved"], [])  # nothing left: nothing to do

    def test_one_already_there_stays_where_it_was(self):
        make_mod(self.work / "Mods" / "tank", "tank-new")
        res = yourfiles.move_in(self.home, self.work)
        self.assertEqual([left["path"] for left in res["left"]], [str(self.tank)])
        self.assertTrue((self.tank / "mod.toml").is_file())
        self.assertIn('id = "tank-new"', (self.work / "Mods" / "tank" / "mod.toml").read_text(encoding="utf-8"))
        self.assertEqual(json.loads((self.home / "studio.json").read_text(encoding="utf-8"))["mod"], str(self.tank))

    def test_another_drive_copied_checked_then_taken_out(self):
        real = os.rename
        renamed = []

        def rename(a, b):
            if Path(b).parent.name in ("Mods", "Maps", "Exports", "Backups") and not Path(a).name.startswith("."):
                raise OSError(17, "The system cannot move the file to a different disk drive")  # (Windows' words)
            renamed.append((Path(a).name, Path(b).name))
            return real(a, b)

        with mock.patch("rusemod.yourfiles.os.rename", side_effect=rename):
            res = yourfiles.move_in(self.home, self.work)
        self.assertEqual(len(res["moved"]), 4)
        self.assertIn(("tank", ".moved-tank"), renamed)  # the old one renamed aside before it's removed
        self.assertEqual((self.work / "Mods" / "tank" / "src" / "studio.rndf").read_bytes(), b"patch\n")
        self.assertFalse(self.tank.exists())
        self.assertEqual([p.name for p in (self.work / "Mods").iterdir()], ["tank"])  # no copy half-made left

    def test_a_copy_that_doesnt_match_or_a_folder_in_use_leaves_it_all_as_it_was(self):
        real = os.rename

        def no_drive(a, b):
            if Path(b).parent.name in ("Mods", "Maps", "Exports", "Backups") and not Path(a).name.startswith("."):
                raise OSError(17, "another drive")
            return real(a, b)

        with mock.patch("rusemod.yourfiles.os.rename", side_effect=no_drive), \
                mock.patch("rusemod.yourfiles._identical", return_value=False):
            res = yourfiles.move_in(self.home, self.work)
        self.assertEqual(res["moved"], [])
        self.assertTrue(all("byte for byte" in left["why"] for left in res["left"]))
        self.assertTrue((self.tank / "src" / "studio.rndf").is_file())
        self.assertEqual([p.name for p in (self.work / "Mods").iterdir()], [])

        def in_use(a, b):
            if Path(b).name.startswith(".moved-") or (Path(b).parent.name in ("Mods", "Maps", "Exports", "Backups")
                                                      and not Path(a).name.startswith(".")):
                raise PermissionError(32, "The process cannot access the file because it is being used")
            return real(a, b)

        with mock.patch("rusemod.yourfiles.os.rename", side_effect=in_use):
            res = yourfiles.move_in(self.home, self.work)
        self.assertEqual(res["moved"], [])
        self.assertTrue((self.tank / "src" / "studio.rndf").is_file())
        self.assertEqual([p.name for p in (self.work / "Mods").iterdir()], [])  # its copy taken back out


class Trash(unittest.TestCase):
    def test_elsewhere_the_desktops_trash(self):
        """Linux and the Steam Deck's desktop: freedesktop.org's trash, with where it was so it can be put back."""
        with tempfile.TemporaryDirectory() as tmp:
            gone = make_mod(Path(tmp, "mods", "tank"), "tank")
            make_mod(Path(tmp, "maps", "tank"), "tank")
            with mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(Path(tmp, "data"))}), \
                    mock.patch.object(recycle.sys, "platform", "linux"):
                recycle._to_trash(gone)
                recycle._to_trash(Path(tmp, "maps", "tank"))
            trash = Path(tmp, "data", "Trash")
            self.assertEqual(sorted(p.name for p in (trash / "files").iterdir()), ["tank", "tank.2"])
            info = (trash / "info" / "tank.trashinfo").read_text(encoding="utf-8")
            self.assertTrue(info.startswith("[Trash Info]\nPath="))
            self.assertIn("DeletionDate=", info)
            self.assertFalse(gone.exists())


class StudioFolders(unittest.TestCase):
    """The Studio with its mods in a made-up Documents\\RUSE 2.0 (`work`), as in the app."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home, self.work, self.opened = root / "platform", root / "Documents" / "RUSE 2.0", []
        self.api = self.studio()
        self.binned = []

    def tearDown(self):
        self.tmp.cleanup()

    def studio(self, **kw):
        starter = Starter(open_url=self.opened.append, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        return StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None, home=self.home,
                         starter=starter, work=kw.get("work", self.work))

    def to_bin(self, path):
        self.binned.append(Path(path))
        shutil.rmtree(path)

    def test_made_in_documents_listed_and_shown(self):
        self.api.new_mod("Tank Test")
        mod = self.work / "Mods" / "tank-test"
        self.assertTrue((mod / "mod.toml").is_file())
        self.api.new_mod("Beach", kind="map")
        made = self.work / "Maps" / "beach"
        self.assertEqual(self.api.mods("map")["mods"], [{"path": str(made), "name": "beach"}])
        left = make_mod(self.home / "mods" / "left-behind", "left-behind")  # one that couldn't be moved
        make_mod(self.work / "Mods" / ".moving-half", "half")  # one being moved: never listed
        self.assertEqual([m["path"] for m in self.api.mods()["mods"]], [str(mod), str(left)])
        self.assertEqual(self.api.where_files(), {
            "mods": str(self.work / "Mods"), "maps": str(made.parent), "exports": str(self.work / "Exports"),
            "backups": str(self.work / "Backups"), "library": str(self.home / "library"), "documents": True})
        self.assertEqual(self.api.show_folder("mod"), {"opened": str(mod)})
        self.assertEqual(self.api.show_folder("map"), {"opened": str(made)})
        self.assertEqual(self.api.open_mod_in_folder(), {"opened": str(mod)})  # the mod check's button, the same
        self.api.show_folder("backups")
        self.assertTrue((self.work / "Backups").is_dir())
        self.assertEqual(self.opened, [str(mod), str(made), str(mod), str(self.work / "Backups")])
        with self.assertRaises(StudioError):
            self.api.show_folder("C:/Windows")

    def test_open_a_mod_folder_starts_where_they_are(self):
        self.api._window = object()
        with mock.patch("ruse_studio.api.pick_folder", return_value=None) as dialog:
            self.api.open_mod_folder("mod")
            self.api.open_mod_folder("map")
        self.assertEqual([c.args[1] for c in dialog.call_args_list], [self.work / "Mods", self.work / "Maps"])

    def test_delete_a_mod_to_the_recycle_bin_and_its_launcher_copy_when_ticked(self):
        self.api.new_mod("Tank Test")
        tank = Path(self.api.mods()["current"])
        self.api.new_mod("Other")
        other = Path(self.api.mods()["current"])
        Library(self.home / "library").add(make_mod(Path(self.tmp.name, "export", "tank-test"), "tank-test",
                                                    "Tank Test"))
        theirs = make_mod(Path(self.tmp.name, "elsewhere", "theirs"), "theirs", "Their mod")
        self.api.choose_mod(str(theirs))
        rows = {r["folder"]: r for r in self.api.your_mods()["mods"]}
        self.assertEqual((rows["tank-test"]["ours"], rows["tank-test"]["launcher"], rows["tank-test"]["editing"]),
                         (True, "Tank Test", ""))
        self.assertEqual((rows["theirs"]["ours"], rows["theirs"]["editing"], rows["theirs"]["name"]),
                         (False, "both", "Their mod"))  # no map changes picked: the Maps tab goes on with the mod
        with self.assertRaisesRegex(StudioError, "wasn't made in the Studio"):
            self.api.delete_mod(str(theirs))
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=self.to_bin):
            res = self.api.delete_mod(str(tank))  # the Launcher's copy not ticked: it stays
            self.assertEqual((res["deleted"], res["launcher"]), ("Tank Test", False))
            self.assertTrue((self.home / "library" / "tank-test").is_dir())
            self.api.choose_mod(str(other))
            res = self.api.delete_mod(str(other), launcher=True)  # no copy in the Launcher: just the mod
        self.assertEqual(self.binned, [tank, other])
        self.assertEqual(res["mod"]["current"], None)  # it was being edited: nothing is now
        self.assertNotIn(str(other), self.api._settings().get("recent", []))
        self.assertEqual([m["path"] for m in self.api.mods()["mods"]], [str(theirs)])
        res = self.api.forget_mod(str(theirs))
        self.assertEqual(res["mod"]["mods"], [])
        self.assertTrue((theirs / "mod.toml").is_file())  # only off the list

    def test_the_launchers_copy_too(self):
        self.api.new_mod("Tank Test")
        tank = Path(self.api.mods()["current"])
        Library(self.home / "library").add(make_mod(Path(self.tmp.name, "export", "tank-test"), "tank-test"))
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=self.to_bin):
            res = self.api.delete_mod(str(tank), launcher=True)
        self.assertTrue(res["launcher"])
        self.assertEqual(self.binned, [tank, self.home / "library" / "tank-test"])

    def test_a_folder_in_use_isnt_deleted(self):
        self.api.new_mod("Tank Test")
        tank = Path(self.api.mods()["current"])
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=OSError("close anything that has it open")), \
                self.assertRaisesRegex(StudioError, "close anything"):
            self.api.delete_mod(str(tank))
        self.assertEqual(self.api.mods()["current"], str(tank))  # still there, still being edited

    def test_the_app_moves_them_once_and_says_so(self):
        make_mod(self.home / "mods" / "old", "old")
        (self.home / "studio.json").write_text(json.dumps({"mod": str(self.home / "mods" / "old")}), encoding="utf-8")
        api = StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None, home=self.home)
        self.assertEqual(api.use_documents(), {"moved": [], "left": [], "to": ""})  # a home given: nothing moves
        self.assertTrue((self.home / "mods" / "old").is_dir())
        with mock.patch("ruse_studio.api.default_home", return_value=self.home), \
                mock.patch("rusemod.yourfiles.documents_home", return_value=self.work):
            api = StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None)
            api.use_documents()
        self.assertEqual(api.files_moved(), {"moved": 1, "to": str(self.work), "left": []})
        self.assertEqual(api.files_moved()["moved"], 0)  # said once
        self.assertEqual(api.mods()["current"], str(self.work / "Mods" / "old"))

    def test_an_edit_of_an_installed_mod_is_copied_into_documents(self):
        Library(self.home / "library").add(make_mod(Path(self.tmp.name, "dl", "econ"), "econ", "Econ",
                                                    files={"src/eco.rndf": b""}))
        with mock.patch.object(StudioApi, "_game", return_value=None):
            res = self.api.edit_installed("econ", "My Econ")
        self.assertEqual(Path(res["path"]).parent, self.work / "Mods")
        self.assertEqual(package.info_of(Path(res["path"]))["id"], "my-econ")


if __name__ == "__main__":
    unittest.main()
