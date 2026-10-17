"""Mods kept safe across Studio updates (rusemod.modformat; the owner, 2026-10-16: "future-proofing that to where
their builds aren't destroyed between updates and there's a way to update their old build"): the mod format number in
mod.toml, an older mod brought up to date with a backup first, a newer Studio's mod not opened without a yes, and a
rewrite of a map file keeping the tables it doesn't write."""
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from fixtures import make_edat
from test_scenery import unit_pack_raw, village
from rusemod import modformat, scenery
from rusemod.build import load_mod
from ruse_studio.api import StudioApi, StudioError

MOD = '[mod]\nid = "old"\nname = "Old"\nversion = "0.1.0"\n'


def old_mod(root: Path, made_with: str = "") -> Path:
    folder = root / "old"
    (folder / "src").mkdir(parents=True)
    (folder / "mod.toml").write_text(MOD + made_with, encoding="utf-8")
    return folder


class Format(unittest.TestCase):
    def test_a_mod_with_no_number_is_format_0_and_gets_one_quietly(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = old_mod(Path(tmp))
            self.assertEqual(modformat.format_of(folder), 0)
            self.assertEqual(modformat.state(folder)["state"], "quiet")  # nothing to rewrite from 0
            done = modformat.upgrade(folder, "RUSE Studio", "0.9.9", Path(tmp) / "backups")
            self.assertEqual((done["from"], done["to"], done["backup"]), (0, modformat.FORMAT, None))
            data = tomllib.loads((folder / "mod.toml").read_text(encoding="utf-8"))
            self.assertEqual(data["made_with"], {"tool": "RUSE Studio", "version": "0.9.9", "format": modformat.FORMAT})
            self.assertEqual(data["mod"]["name"], "Old")  # the rest stays
            self.assertEqual(modformat.state(folder)["state"], "same")

    def test_an_upgrade_with_a_step_keeps_a_backup_first(self):
        """When a later Studio changes what a file means, FORMAT goes up and UPGRADES gets a step: the step runs on a
        player's Update, after a zip of the whole mod."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = old_mod(Path(tmp), '\n[made_with]\nformat = 1\n')
            (folder / "src" / "units.rndf").write_text("old words", encoding="utf-8")

            def step(f):
                (Path(f) / "src" / "units.rndf").write_text("new words", encoding="utf-8")
                return ["src/units.rndf: rewritten the new way"]
            with mock.patch.object(modformat, "FORMAT", 2), mock.patch.dict(modformat.UPGRADES, {1: step}):
                self.assertEqual(modformat.state(folder), {"format": 1, "current": 2, "state": "older", "steps": 1})
                done = modformat.upgrade(folder, "RUSE Studio", "1.0", Path(tmp) / "backups")
                self.assertEqual(done["changed"], ["src/units.rndf: rewritten the new way"])
                with zipfile.ZipFile(done["backup"]) as z:
                    self.assertEqual(z.read("src/units.rndf"), b"old words")  # the backup is the mod as it was
                self.assertEqual((folder / "src" / "units.rndf").read_text(encoding="utf-8"), "new words")
                self.assertEqual(modformat.format_of(folder), 2)

    def test_a_newer_mod_is_never_upgraded_down(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = old_mod(Path(tmp), f'\n[made_with]\nformat = {modformat.FORMAT + 1}\n')
            self.assertEqual(modformat.state(folder)["state"], "newer")
            with self.assertRaises(ValueError):
                modformat.upgrade(folder, "RUSE Studio", "0.9", Path(tmp) / "b")


class TheStudio(unittest.TestCase):
    def api(self, tmp: Path, game=None):
        return StudioApi(game_dir=game or tmp / "nowhere", home=tmp / "home", index_path=tmp / "x.sqlite")

    def test_new_mods_are_stamped_and_older_ones_on_opening(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = self.api(Path(tmp))
            made = Path(api.new_mod("Fresh")["current"])
            self.assertEqual(modformat.format_of(made), modformat.FORMAT)
            folder = old_mod(Path(tmp))
            api.choose_mod(str(folder))
            self.assertEqual(modformat.format_of(folder), modformat.FORMAT)  # nothing to rewrite: done on opening
            self.assertEqual(api.mod_format()["state"], "same")

    def test_a_newer_studio_s_mod_needs_a_yes(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = self.api(Path(tmp))
            folder = old_mod(Path(tmp), f'\n[made_with]\nformat = {modformat.FORMAT + 1}\n')
            self.assertEqual(api.mod_format(path=str(folder))["state"], "newer")
            with self.assertRaisesRegex(StudioError, "saved by a newer RUSE Studio"):
                api.choose_mod(str(folder))
            self.assertEqual(api.choose_mod(str(folder), "mod", True)["current"], str(folder))
            self.assertEqual(modformat.format_of(folder), modformat.FORMAT + 1)  # never stamped down
            with self.assertRaisesRegex(StudioError, "update the Studio, not the mod"):
                api.update_mod()

    def test_update_this_mod(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = self.api(Path(tmp))
            folder = old_mod(Path(tmp), '\n[made_with]\nformat = 1\n')
            with mock.patch.object(modformat, "FORMAT", 2), mock.patch.dict(modformat.UPGRADES, {1: lambda f: ["ok"]}):
                api.choose_mod(str(folder))
                self.assertEqual(api.mod_format()["state"], "older")  # waits for the player's Update
                done = api.update_mod()
                self.assertEqual(done["changed"], ["ok"])
                self.assertTrue(Path(done["backup"]).is_file())
                self.assertEqual(Path(done["backup"]).parent, Path(tmp) / "home" / "mod-backups")
                self.assertEqual(done["format"]["state"], "same")

    def test_a_scenery_file_keeps_the_tables_the_studio_doesn_t_write(self):
        """Studio 0.9.8.6 rewrote a scenery.toml with its objects and erase circles alone: a [[preset]] or a
        [[fieldbrush]] put there by hand or a newer Studio went. Now they stay through every rewrite, and through the
        last of the Studio's own rows going (two [[copy]] rows here: any table the Studio doesn't write is kept the
        same way)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "R.U.S.E"
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(unit_pack_raw())
            (game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(
                make_edat([("dir", "output\\", [("file", "save.boobspc", village())])]))
            api = self.api(root, game)
            folder = Path(api.new_mod("Keeps")["current"])
            path = folder / "maps" / "Test" / "scenery.toml"
            path.parent.mkdir(parents=True)
            path.write_text('[[copy]]\nx = 3000.0\ny = 4000.0\nradius = 500.0\nsx = 1000.0\nsy = 2000.0\n'
                            'layers = ["plants", "stones"]\n\n[[copy]]\nx = 6000.0\ny = 4000.0\nradius = 300.0\n'
                            'sx = 1500.0\nsy = 2500.0\nturn = 90.0\n', encoding="utf-8")
            before = tomllib.loads(path.read_text(encoding="utf-8"))
            api.scenery_add("Test", [{"type": "TypeWarrior/Chene_02", "x": 50, "y": 60}])
            after = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(after["copy"], before["copy"])
            self.assertEqual(len(after["object"]), 1)
            api.scenery_undo("Test", 1)  # the Studio's last row goes: the file stays, with the rest
            after = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("object", after)
            self.assertEqual(after["copy"], before["copy"])
            info, _ops = load_mod(folder)  # and the build still reads the file
            self.assertEqual(len(info.copy.get("Test", [])), len(scenery.parse_copies(before["copy"])))


if __name__ == "__main__":
    unittest.main()
