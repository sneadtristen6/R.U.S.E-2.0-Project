"""What Export mod (rusemod.package.pack, the Studio's export_mod) lets out of the maker's PC, after the owner's answers
of 2026-11-12 (his question dialog, as the lead quoted them):
- the era units' credits and record go along ("Take both along"): CREDITS-era-units.md (every era unit maker's CC-BY
  credit, and "your name, sneadtristen6, in that mod's credits" for the Horse Squad) and era_units.json (which units
  are era units), so another player's Studio knows them as added: its Take it out works there, its Add says the unit
  is in the mod already. A mod without era units packs as before, byte for byte;
- no folder of the maker's PC goes out (FL-110, "Keep file name only": Export writes only the file's own name in each
  record, never a folder): a model's record ("from"), the data inside a .glb (an imported scenery model names the
  file it was made from, its middle and far versions the model they were made from), and any text; the mod's own
  files on his PC keep theirs. A record naming only a file's name is never looked for in the folder the Studio runs
  in (Resize and Move take a model's file only by its full path).
On the Studio tests' made-up game, the Horse Squad's builder and model import stood in for (as tests/test_horse_squad.py
does): what's checked here is what goes into the file and comes out of it."""
import json
import os
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_build import write_mod
from test_horse_squad import finished, stand_in
from test_studio import WithMod
from rusemod import package
from rusemod.gltf import _Glb
from rusemod.library import Library
from rusemod.modelin import glb_document
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError

KEY = horse_squad.KEY
LIBERTY = "WWI|USA|Mark VIII Liberty"
LIBERTY_LINE = '- Mark VIII Liberty (WWI, USA): "Liberty model" by maker, CC-BY 4.0, https://example.org/Liberty.'
HIS_LINE = "- Horse Squad (WWII, USA): by sneadtristen6."
PC = "C:\\Users\\Jane Doe\\AppData\\Local\\RUSE Mod Platform"   # a player's platform folder, his Windows name in it


def era_library(folder: Path) -> Path:
    """An era units library with one WWI unit (no model) copying the M4 Sherman, as test_horse_squad's."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": [
        {"key": LIBERTY, "era": "WWI", "nation": "USA", "name": "Mark VIII Liberty",
         "in_place_of": "", "card": "Heavy Tank", "building": "Armor base",
         "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman", "copies_name": "", "game_nation": 0,
         "factory": 10, "aircraft": False, "model": None, "fits": True, "picture": None,
         "credit": {"title": "Liberty model", "author": "maker", "licence": "CC-BY 4.0",
                    "url": "https://example.org/Liberty", "extra": ""}}]}), encoding="utf-8")
    return folder


def glb_naming(source: str) -> bytes:
    """A .glb as the Studio's scenery import writes a model's version (rusemod.meshlod.glb_bytes): its mesh and its
    asset's extras name the file it was made from."""
    g = _Glb()
    g.doc["meshes"] = [{"name": source, "primitives": [{"attributes": {"POSITION": g.packed(
        struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0), 3, "VEC3", 5126, low=[0, 0, 0], high=[1, 1, 0])}}]}]
    g.doc["nodes"] = [{"name": "model", "mesh": 0}]
    g.doc["scenes"] = [{"nodes": [0]}]
    g.doc["scene"] = 0
    g.doc["asset"]["extras"] = {"rusemod_version": source}
    return g.to_bytes()


def members(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


class FoldersOut(unittest.TestCase):
    def test_a_path_keeps_its_file_s_own_name(self):
        for text, want in (
                (PC + "\\horse_squad\\horse-squad-rifle.glb", "horse-squad-rifle.glb"),
                ("D:/RUSE-2.0/scratch/x/Boulder01.glb (far)", "Boulder01.glb (far)"),
                ("\\\\server\\share\\models\\tank.glb", "tank.glb"),
                ("/home/jane/models/tank.glb", "tank.glb"),
                ("Read C:\\models\\tank.glb and C:\\models\\turret.glb.", "Read tank.glb and turret.glb."),
                ("C:\\Users\\jane\\u1945.glb", "u1945.glb"),
                ("C:\\Users\\jane\\Desktop\\", "")):
            self.assertEqual(package.folders_out(text), want, text)
        written = 'from = "C:\\\\Users\\\\Jane Doe\\\\caf\\u00e9.glb" # D:/work/make.py'
        self.assertEqual(package.folders_out(written, written=True), 'from = "caf\\u00e9.glb" # make.py')

    def test_what_isnt_a_folder_of_the_pc_stays(self):
        for text in ("$/GFX/Everything/Descriptor_Unit_Horse_Squad",
                     "gen\\ww2\\res3d\\units\\us\\infanterie\\tscother_diffusetexture01.tgv",
                     "Horse Squad (WWII, USA): by sneadtristen6, https://github.com/sneadtristen6/R.U.S.E-2.0-Project",
                     "https://example.org/home/x", "a ratio of 3:/4", "files/models/Descriptor_Unit_X.glb"):
            self.assertEqual(package.folders_out(text), text)
            self.assertEqual(package.folders_out(text, written=True), text)


class Packing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mod = write_mod(self.root, "cavalry", {"units.rndf": "patch $/B ( ProductionPrice *= 0.5 )"},
                             extra='name = "Cavalry"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, data):
        """A file of the mod: bytes as they are, a text as the Studio writes one (its lines as the PC ends them)."""
        path = self.mod / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        (path.write_bytes if isinstance(data, bytes) else lambda t: path.write_text(t, encoding="utf-8"))(data)
        return path

    def text(self, rel) -> bytes:
        """A text as `write` wrote it, for comparing with what a package holds."""
        return self.mod.joinpath(rel).read_bytes()

    def as_before(self, out: Path) -> bytes:
        """The package a mod's files make zipped as they are, one by one (what pack wrote before it took folders out:
        z.write of each file package.files_of lists)."""
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in package.files_of(self.mod):
                z.write(f, f.relative_to(self.mod).as_posix())
        return out.read_bytes()

    def test_a_mod_without_era_units_or_folders_packs_as_before_byte_for_byte(self):
        self.write("text/units.csv", "key,us\nk1,Text\n")
        self.write("README.md", "# Cavalry\nBy sneadtristen6: https://github.com/sneadtristen6/R.U.S.E-2.0-Project\n")
        self.write("files/models/Descriptor_Unit_X.glb", glb_naming("x"))
        self.write("files/models/Descriptor_Unit_X.json", json.dumps({"from": "x.glb", "size": 1.0}, indent=1))
        self.write(era_units.INDEX, "{}")                  # (its last era unit taken out: the Studio leaves {})
        cleaned = []
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned)
        self.assertEqual(cleaned, [])
        self.assertEqual(list(members(out)), ["mod.toml", "README.md", "src/units.rndf", "text/units.csv",
                                              "files/models/Descriptor_Unit_X.glb",
                                              "files/models/Descriptor_Unit_X.json"])   # (the {} record stays behind)
        self.assertEqual(out.read_bytes(), self.as_before(self.root / "before.zip"))

    def test_the_era_units_credits_and_record_go_along(self):
        self.write(era_units.CREDITS, f"# Made for RUSE 2.0\n\n{LIBERTY_LINE}\n{HIS_LINE}\n")
        record = {KEY: "$/GFX/Everything/Descriptor_Unit_Horse_Squad",
                  LIBERTY: "$/GFX/Everything/Descriptor_Unit_Mark_VIII_Liberty"}
        self.write(era_units.INDEX, json.dumps(record, indent=1))
        self.assertEqual([f.relative_to(self.mod).as_posix() for f in package.files_of(self.mod)],
                         ["mod.toml", era_units.CREDITS, era_units.INDEX, "src/units.rndf"])
        self.assertEqual((package.ERA_CREDITS, package.ERA_RECORD), (era_units.CREDITS, era_units.INDEX))
        out = package.pack(self.mod, self.root / "out")
        got = members(out)
        self.assertEqual(json.loads(got[era_units.INDEX]), record)
        self.assertIn(HIS_LINE.encode(), got[era_units.CREDITS])
        self.assertIn(LIBERTY_LINE.encode(), got[era_units.CREDITS])
        into = self.root / "library" / "cavalry"
        package.unpack(out, into)
        self.assertEqual((into / era_units.INDEX).read_bytes(), (self.mod / era_units.INDEX).read_bytes())
        self.assertEqual((into / era_units.CREDITS).read_bytes(), (self.mod / era_units.CREDITS).read_bytes())

    def test_a_model_record_goes_out_naming_only_its_file(self):
        mine = {"from": PC + "\\horse_squad\\horse-squad-rifle.glb", "size": 1.0, "aircraft": False,
                "report": {"file": "horse-squad-rifle.glb", "notes": [f"read {PC}\\pictures\\coat.png"]},
                "for": "fusilier", "skeleton": "own"}
        record = self.write("files/models/Descriptor_Unit_Horse_Squad.json", json.dumps(mine, indent=1))
        on_disk = record.read_bytes()
        cleaned = []
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned)
        self.assertEqual(cleaned, ["files/models/Descriptor_Unit_Horse_Squad.json"])
        self.assertEqual(record.read_bytes(), on_disk)       # his own record keeps its folder: Resize uses it
        packed = members(out)["files/models/Descriptor_Unit_Horse_Squad.json"]
        self.assertEqual(json.loads(packed), dict(mine, **{"from": "horse-squad-rifle.glb", "report": {
            "file": "horse-squad-rifle.glb", "notes": ["read coat.png"]}}))
        # every other byte as it was: only the two strings naming a folder are written anew
        self.assertEqual(packed, on_disk.replace(json.dumps(mine["from"]).encode(), b'"horse-squad-rifle.glb"')
                         .replace(json.dumps(mine["report"]["notes"][0]).encode(), b'"read coat.png"'))
        with zipfile.ZipFile(self.root / "as-it-is.zip", "w", zipfile.ZIP_DEFLATED) as z:
            z.write(record, "files/models/Descriptor_Unit_Horse_Squad.json")   # (how every other member goes in)
        with zipfile.ZipFile(out) as z, zipfile.ZipFile(self.root / "as-it-is.zip") as plain:
            info, want = (zf.getinfo("files/models/Descriptor_Unit_Horse_Squad.json") for zf in (z, plain))
        self.assertEqual((info.date_time, info.external_attr, info.compress_type),
                         (want.date_time, want.external_attr, want.compress_type))   # the file's date, as z.write
        self.assertEqual(package.check(out)["files"][-1], "files/models/Descriptor_Unit_Horse_Squad.json")

    def test_a_model_s_own_data_goes_out_naming_only_its_file(self):
        model = self.write("files/assets/Boulder01/Boulder01_far.glb",
                           glb_naming(PC + "\\maps\\my-map\\files\\assets\\Boulder01\\Boulder01.glb (far)"))
        plain = self.write("files/assets/Boulder01/Boulder01.glb", glb_naming("Boulder01.glb"))
        out = package.pack(self.mod, self.root / "out")
        got = members(out)
        self.assertEqual(got["files/assets/Boulder01/Boulder01.glb"], plain.read_bytes())
        doc, binary = glb_document(got["files/assets/Boulder01/Boulder01_far.glb"])
        was, was_binary = glb_document(model.read_bytes())
        self.assertEqual((doc["meshes"][0]["name"], doc["asset"]["extras"]["rusemod_version"]),
                         ("Boulder01.glb (far)", "Boulder01.glb (far)"))
        self.assertEqual(binary, was_binary)
        self.assertEqual({k: v for k, v in doc.items() if k not in ("meshes", "asset")},
                         {k: v for k, v in was.items() if k not in ("meshes", "asset")})
        raw = got["files/assets/Boulder01/Boulder01_far.glb"]
        self.assertEqual(struct.unpack_from("<I", raw, 8)[0], len(raw))

    def test_no_member_names_a_folder_of_the_pc(self):
        self.write("files/models/Descriptor_Unit_X.json", json.dumps({"from": "D:/models/x.glb"}))
        doubled = PC.replace("\\", "\\\\")                   # (a TOML string writes each backslash twice)
        self.write("files/notes/made.toml", f'# made from {PC}\\x.blend\n[x]\nfile = "{doubled}\\\\x.glb"\n')
        self.write("README.md", f"Made on {PC}\\mods\\cavalry by sneadtristen6.\n")
        self.write("files/assets/A/A.glb", glb_naming("/home/jane/models/a.gltf"))
        cleaned = []
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned)
        self.assertEqual(sorted(cleaned), ["README.md", "files/assets/A/A.glb", "files/models/Descriptor_Unit_X.json",
                                           "files/notes/made.toml"])
        got = members(out)
        for name, data in got.items():
            for form in ("Jane Doe", "D:/models", "/home/jane", "C:\\", "C:/", "D:\\"):
                self.assertNotIn(form.encode(), data, name)
        self.assertEqual(got["README.md"], self.text("README.md").replace(f"{PC}\\mods\\".encode(), b""))
        self.assertEqual(got["files/notes/made.toml"], self.text("files/notes/made.toml")
                         .replace(f"{PC}\\".encode(), b"").replace(f"{doubled}\\\\".encode(), b""))
        self.assertIn(b"Made on cavalry by sneadtristen6.", got["README.md"])
        self.assertIn(b'# made from x.blend', got["files/notes/made.toml"])
        self.assertIn(b'file = "x.glb"', got["files/notes/made.toml"])
        self.assertEqual(package.check(out)["id"], "cavalry")


class OnTheMadeUpGame(WithMod):
    """The Horse Squad and an era unit added on one player's PC, exported, and opened in another player's Studio (his
    Launcher library's add, then Edit an installed mod)."""

    def setUp(self):
        super().setUp()
        lib = era_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        patcher.start()
        self.addCleanup(patcher.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def add(self, api) -> dict:
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            return finished(api, api.horse_squad_add(0, 10, "Cavalry", 7, group="new")["job"])

    def exported(self):
        """A mod with the Liberty, the Horse Squad and a model record naming this PC's platform folder, exported."""
        folder = Path(self.api.new_mod("Shared")["current"])
        self.liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        view = self.add(self.api)
        self.assertEqual(view["state"], "done", view.get("message"))
        self.unit = view["result"]["address"]
        record = folder / "files" / "models" / (self.unit.rsplit("/", 1)[-1] + ".json")
        record.parent.mkdir(parents=True, exist_ok=True)
        made = self.home / horse_squad.FOLDER / self.rifle.name
        record.write_text(json.dumps({"from": str(made), "size": 1.0, "report": {"file": made.name}}, indent=1),
                          encoding="utf-8")
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "With the Horse Squad.")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        return folder, record, Path(view["result"]["path"]), view

    def test_the_export_carries_the_credits_and_the_record_and_no_folder_of_his_pc(self):
        folder, record, export, view = self.exported()
        got = members(export)
        self.assertEqual(json.loads(got[era_units.INDEX]), {LIBERTY: self.liberty, KEY: self.unit})
        self.assertIn(HIS_LINE.encode(), got[era_units.CREDITS])
        self.assertIn(LIBERTY_LINE.encode(), got[era_units.CREDITS])
        home = str(self.home)
        for name, data in got.items():
            for form in (home, home.replace("\\", "/"), json.dumps(home)[1:-1]):
                self.assertNotIn(form.encode("utf-8"), data, name)
        self.assertEqual(json.loads(got[record.relative_to(folder).as_posix()])["from"], self.rifle.name)
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["from"],
                         str(self.home / horse_squad.FOLDER / self.rifle.name))   # his own record keeps its folder
        said = [ln for ln in view["lines"] if ln.startswith("Your PC's folders were left out")]
        self.assertEqual(said, ["Your PC's folders were left out of the exported file: 1 of the mod's files named "
                                f"one, and there they name only the file ({record.relative_to(folder).as_posix()})."])
        self.api.set_pref("lang", "fr")
        worded = [ln for ln in self.api.job(view["id"])["lines"] if "dossiers de votre PC" in ln]
        self.assertEqual(len(worded), 1)
        library = self.home / "library" / package.info_of(folder)["id"]   # (Export puts it in his Launcher's library)
        self.assertEqual((library / era_units.INDEX).read_bytes(), got[era_units.INDEX])
        self.assertEqual((library / era_units.CREDITS).read_bytes(), got[era_units.CREDITS])

    def test_another_player_s_studio_knows_its_era_units_are_in_the_mod(self):
        _folder, _record, export, _view = self.exported()
        other_home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        other = StudioApi(index_path=self.index, game_dir=self.game, home=other_home, instances=other_home / "copies")
        info, _replaced = Library(other_home / "library").add(export)
        copy = Path(other.edit_installed(info["id"], "Shared (my copy)")["path"])
        self.assertEqual(json.loads((copy / era_units.INDEX).read_text(encoding="utf-8")),
                         {LIBERTY: self.liberty, KEY: self.unit})
        self.assertEqual([u["added"] for u in other.era_units_list("WWII")["units"] if u["key"] == KEY], [self.unit])
        self.assertEqual([u["added"] for u in other.era_units_list("WWI")["units"] if u["key"] == LIBERTY],
                         [self.liberty])
        self.assertEqual(other.era_unit_page(KEY, "us")["added"], self.unit)
        with self.assertRaisesRegex(StudioError, "already in this mod"):
            other.horse_squad_add(0, 10, "Cavalry", 7, group="new")       # Add says it's in the mod already
        self.assertEqual(other.era_unit_remove(KEY)["removed"], self.unit)  # and Take it out works there
        self.assertNotIn(self.unit, {u["address"] for u in other.units("us")["units"] if u.get("new")})
        self.assertEqual(json.loads((copy / era_units.INDEX).read_text(encoding="utf-8")), {LIBERTY: self.liberty})
        credits = (copy / era_units.CREDITS).read_text(encoding="utf-8")
        self.assertNotIn(HIS_LINE, credits)
        self.assertIn(LIBERTY_LINE, credits)

    def test_a_record_naming_only_its_file_is_never_looked_for_where_the_studio_runs(self):
        folder, record, export, _view = self.exported()
        other_home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        other = StudioApi(index_path=self.index, game_dir=self.game, home=other_home, instances=other_home / "copies")
        info, _replaced = Library(other_home / "library").add(export)
        copy = Path(other.edit_installed(info["id"], "Shared (my copy)")["path"])
        his = copy / record.relative_to(folder)
        self.assertEqual(json.loads(his.read_text(encoding="utf-8"))["from"], self.rifle.name)
        (copy / "files" / "models" / (self.unit.rsplit("/", 1)[-1] + ".glb")).write_bytes(b"glTF")
        here = Path(tempfile.mkdtemp(dir=self.tmp.name))
        (here / self.rifle.name).write_bytes(b"another file of the same name")
        was = os.getcwd()
        os.chdir(here)                                       # (a file of that name where the Studio runs)
        self.addCleanup(os.chdir, was)
        self.assertFalse(other.model_sizes(self.unit, "us")["resizable"])
        with self.assertRaisesRegex(StudioError, "isn't there any more"):
            other.model_resize(self.unit, 1.2)
        with self.assertRaisesRegex(StudioError, "isn't there any more"):
            other.model_place(self.unit, [0, 0, 1])


if __name__ == "__main__":
    unittest.main()
