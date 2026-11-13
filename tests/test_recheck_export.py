"""Recheck of fix/export (55e6db0c, round 1): what Export mod lets out, judged on the real artifacts: the exported file's
members, the Launcher library's copy Export makes, and the .zip Publish puts beside the file.

The owner's answers of 2026-11-12 (his question dialog, as the lead quoted them): to "Should Export take both along?"
(the mod's CREDITS-era-units.md and era_units.json) "Take both along (Recommended)"; to "What should Export do?" (each
imported model's record keeps the full path of its source file) "Keep file name only (Recommended)" (its description:
Export writes only the file's own name in each record, never a folder).

- SOUND, kept (OnTheGame, the real builder): with the platform folder under C:\\Users\\<a Windows name>\\... (here a
  temporary folder whose names stand for it), the exported file, the Launcher library's copy and Publish's .zip name
  no part of that folder, and each model record names its file only; the mod's own records on the maker's PC keep the
  full path (that is what test_review_loss's test_its_records_in_an_exported_mod_name_no_folder_of_the_players reads:
  the mod folder, not an exported file).
- FINDINGS, failing on 55e6db0c by design until fixed:
  - a home folder elsewhere than the few the fix lists goes out whole: on Linux the Studio's platform folder is
    ~/.local/share/ruse-mod-platform (rusemod/home.py), and where home is /var/home/<name> (Fedora Atomic, Bazzite) the
    Horse Squad's records go out naming /var/home/<name>/...;
  - in a text, the file's own name and the modder's words after a path are cut up to the line's last slash or
    backslash ("Made from C:\\models\\tank.glb, and docs\\turret.md tells how." goes out as "Made from turret.md tells
    how.");
  - a mod whose last era unit went with the unit page's Delete (not Take it out) still exports a credits file and an era
    record naming the unit it no longer has;
  - another player who hasn't the era downloaded opens the exported file and takes the Horse Squad out: the credits
    file is written again without the Liberty's CC-BY line, though the Liberty stays in his copy."""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_build import write_mod
from test_studio import WithMod
from test_export_out import LIBERTY, era_library
from rusemod import package
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi

GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
INDEX = Path(os.environ.get("RUSE_GAME_INDEX") or os.environ.get("RUSE_STUDIO_INDEX")
             or "D:/RUSE-2.0/scratch/modelgaps/game-index.sqlite")
FIXES3 = Path(os.environ.get("RUSE_HORSE_FIXES3") or os.environ.get("RUSE_HORSE_SQUAD_GLBS")
              or "D:/RUSE-2.0/scratch/animmodels/fixes3")
READY = (GAME is not None and GAME.is_dir() and INDEX.is_file()
         and (FIXES3 / "horse-squad-rifle-death.glb").is_file() and (FIXES3 / "horse-squad-bazooka-death.glb").is_file())
NAME = "Jane Q Doe"     # a Windows user name, in the folder the platform folder stands under
DRIVE_FOLDER = re.compile(rb"(?<![A-Za-z0-9])[A-Za-z]:(?:\\\\|\\|/)[^\\/\"\r\n]{1,80}(?:\\\\|\\|/)")


def members(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def forms(folder: Path) -> list:
    """A folder as a file could write it: as it is, with forward slashes, as JSON or TOML write it (each backslash
    twice), and the Windows name alone."""
    s = str(folder)
    return [f.encode("utf-8") for f in {s, s.replace("\\", "/"), s.replace("\\", "\\\\"), NAME}]


@unittest.skipUnless(READY, "needs RUSE_GAME, the Studio's game index and the passed copy's two Horse Squad files")
class OnTheGame(unittest.TestCase):
    """The Horse Squad added with the real builder, the mod exported as the Studio's Export does (built on the game),
    added to the Launcher library by Export, and Publish's .zip made."""

    @classmethod
    def setUpClass(cls):
        from test_review_path import added, finished
        cls.tmp = Path(tempfile.mkdtemp(prefix="recheck-export-"))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, True)
        cls.home = cls.tmp / "C" / "Users" / NAME / "AppData" / "Local" / "RUSE Mod Platform"
        cls.home.mkdir(parents=True)
        env = mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(cls.home)})
        env.start()
        cls.addClassCleanup(env.stop)
        cls.api = StudioApi(index_path=INDEX, game_dir=GAME, home=cls.home)
        cls.mod, cls.unit = added(cls.api, "Cavalry")
        cls.job = finished(cls.api, cls.api.export_mod("1.0.0", "a modder", "With the Horse Squad.")["job"])
        cls.export = Path(cls.job["result"]["path"]) if cls.job["state"] == "done" else None
        cls.opened = []
        cls.api._starter.open_url = cls.opened.append
        cls.published = cls.api.publish_mod() if cls.export is not None else None

    def setUp(self):
        self.assertEqual(self.job["state"], "done", self.job.get("message"))

    def no_folder(self, files: dict):
        """No form of the platform folder in any file's bytes; and no drive-letter folder in a text, or in a .glb's
        JSON part (its binary part holds any bytes, a drive letter's look-alikes among them)."""
        from rusemod.modelin import glb_document
        for name, data in files.items():
            for form in forms(self.home):
                self.assertNotIn(form, data, name)
            if name.endswith(".glb"):
                doc, _binary = glb_document(data)
                text = json.dumps(doc, ensure_ascii=False).encode("utf-8")
            elif Path(name).suffix.lower() in package.TEXT_FILES:
                text = data
            else:
                continue
            self.assertIsNone(DRIVE_FOLDER.search(text), name)

    def test_the_exported_file_names_no_folder_of_his_pc(self):
        got = members(self.export)
        self.no_folder(got)
        tail = self.unit.rsplit("/", 1)[-1]
        for stem, made in ((tail, "horse-squad-rifle.glb"), (f"{tail}@bazooka", "horse-squad-bazooka.glb")):
            record = json.loads(got[f"files/models/{stem}.json"])
            self.assertEqual((record["from"], record["report"]["file"]), (made, made))
        self.assertIn(era_units.INDEX, got)
        self.assertIn(b"Horse Squad (WWII, USA): by sneadtristen6", got[era_units.CREDITS])

    def test_the_launcher_library_copy_names_no_folder_of_his_pc(self):
        library = self.home / "library" / package.info_of(self.mod)["id"]
        files = {p.relative_to(library).as_posix(): p.read_bytes() for p in library.rglob("*") if p.is_file()}
        self.assertEqual(sorted(files), sorted(members(self.export)))
        self.no_folder(files)

    def test_publish_s_zip_is_the_exported_file_and_names_no_folder_of_his_pc(self):
        zipped = Path(self.published["zip"])
        self.assertEqual(zipped.read_bytes(), self.export.read_bytes())
        self.no_folder(members(zipped))

    def test_his_own_records_keep_their_folder_and_only_the_export_drops_it(self):
        """What test_review_loss's test_its_records_in_an_exported_mod_name_no_folder_of_the_players reads is the mod
        folder on his PC (package.files_of, then each file as it is), where Resize and Move need the full path."""
        tail = self.unit.rsplit("/", 1)[-1]
        mine = json.loads((self.mod / "files" / "models" / f"{tail}.json").read_text(encoding="utf-8"))
        self.assertEqual(mine["from"], str(self.home / horse_squad.FOLDER / "horse-squad-rifle.glb"))
        self.assertEqual(json.loads(members(self.export)[f"files/models/{tail}.json"])["from"], "horse-squad-rifle.glb")


class Packing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mod = write_mod(self.root, "cavalry", {"units.rndf": "patch $/B ( ProductionPrice *= 0.5 )"},
                             extra='name = "Cavalry"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_home_folder_under_var_home_goes_out_naming_only_its_file(self):
        """Linux: the platform folder is ~/.local/share/ruse-mod-platform (rusemod/home.py); on Fedora Atomic and
        Bazzite home is /var/home/<name>."""
        made = "/var/home/jane/.local/share/ruse-mod-platform/horse_squad/horse-squad-rifle.glb"
        record = self.mod / "files" / "models" / "Descriptor_Unit_Horse_Squad.json"
        record.parent.mkdir(parents=True)
        record.write_text(json.dumps({"from": made, "size": 1.0}, indent=1), encoding="utf-8")
        got = members(package.pack(self.mod, self.root / "out"))
        self.assertEqual(json.loads(got["files/models/Descriptor_Unit_Horse_Squad.json"])["from"],
                         "horse-squad-rifle.glb")

    def test_a_text_keeps_the_file_s_own_name_and_the_words_after_it(self):
        (self.mod / "README.md").write_bytes(b"Made from C:\\models\\tank.glb, and docs\\turret.md tells how.\n")
        got = members(package.pack(self.mod, self.root / "out"))["README.md"].decode("utf-8")
        self.assertEqual(got, "Made from tank.glb, and docs\\turret.md tells how.\n")


class EraUnitDeleted(WithMod):
    """An era unit added, then taken away with the unit page's Delete (delete_unit), not the era page's Take it out."""

    def setUp(self):
        super().setUp()
        lib = era_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_export_credits_and_records_no_unit_the_mod_hasnt(self):
        from test_review_path import finished
        self.api.new_mod("Shared")
        address = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        self.assertEqual(self.api.delete_unit(address)["deleted"], address)
        self.assertNotIn(address, {u["address"] for u in self.api.units("us")["units"] if u.get("new")})
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "No era units left.")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        got = members(Path(view["result"]["path"]))
        self.assertEqual([n for n in (era_units.INDEX, era_units.CREDITS) if n in got], [],
                         {n: got[n].decode("utf-8") for n in (era_units.INDEX, era_units.CREDITS) if n in got})


class AnotherPlayerWithoutTheEra(WithMod):
    """The Liberty (an era unit from the WWI download) and the Horse Squad exported by one player; another player who
    hasn't the WWI era downloaded opens the file (his Launcher library's add, then Edit an installed mod) and takes the
    Horse Squad out. The Liberty stays in his copy, its model in the file, so its maker's CC-BY credit line must stay."""

    def setUp(self):
        super().setUp()
        lib = era_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        self.env = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        self.env.start()
        self.addCleanup(self.env.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def test_taking_the_horse_squad_out_keeps_the_liberty_s_credit(self):
        from test_horse_squad import finished, stand_in
        from test_export_out import LIBERTY_LINE
        from rusemod.library import Library
        Path(self.api.new_mod("Shared")["current"])
        liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Cavalry", 7, group="new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "With the Horse Squad.")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertIn(LIBERTY_LINE.encode(), members(Path(view["result"]["path"]))[era_units.CREDITS])
        self.env.stop()                                      # (another PC: no WWI era downloaded there)
        none = Path(tempfile.mkdtemp(dir=self.tmp.name))
        with mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(none)}):
            other_home = Path(tempfile.mkdtemp(dir=self.tmp.name))
            other = StudioApi(index_path=self.index, game_dir=self.game, home=other_home,
                              instances=other_home / "copies")
            info, _replaced = Library(other_home / "library").add(Path(view["result"]["path"]))
            copy = Path(other.edit_installed(info["id"], "Shared (my copy)")["path"])
            other.era_unit_remove(horse_squad.KEY)
            self.assertIn(liberty, {u["address"] for u in other.units("us")["units"] if u.get("new")})
            credits = copy / era_units.CREDITS
            self.assertIn(LIBERTY_LINE, credits.read_text(encoding="utf-8") if credits.is_file() else "(no credits file)")
        self.env.start()


if __name__ == "__main__":
    unittest.main()
