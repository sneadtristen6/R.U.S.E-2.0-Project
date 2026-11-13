"""What Export mod (rusemod.package.pack, the Studio's export_mod) lets out of the maker's PC, after the owner's answers
of 2026-11-12 (his question dialog, as the lead quoted them):
- the era units' credits and record go along ("Take both along"): CREDITS-era-units.md (every era unit maker's CC-BY
  credit, and "your name, sneadtristen6, in that mod's credits" for the Horse Squad) and era_units.json (which units
  are era units), so another player's Studio knows them as added: its Take it out works there, its Add says the unit
  is in the mod already. A mod without era units packs as before, byte for byte;
- no folder of the maker's PC goes out (FL-110, "Keep file name only": Export writes only the file's own name in each
  record, never a folder) in the fields the Studio itself writes a path into: a model's record ("from", the pictures
  its report names), the data inside a .glb the Studio made from a scenery model (the file it was made from), a map's
  import record (its folders); the mod's own files on his PC keep theirs. Round 2 (the export recheck's F2 and F1):
  nothing a modder wrote changes (README, description, .rndf, .csv, credits: byte for byte), the Studio's fields name
  their file on any system. A record naming only a file's name is never looked for in the folder the Studio runs in
  (Resize and Move take a model's file only by its full path).
On the Studio tests' made-up game, the Horse Squad's builder and model import stood in for (as tests/test_horse_squad.py
does): what's checked here is what goes into the file and comes out of it."""
import json
import tomllib
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
HIS_LINE = "- Generic Horse (WWII, USA): by sneadtristen6."
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


# (round 2 of the export fix, 2026-11-12: "Export never changes what a modder wrote, except a folder of this PC that
# the Studio itself put there, and then only that folder." Round 1's folders_out read paths out of any text and cut a
# modder's words, the recheck's F2; it is gone, and these tests say what replaced it.)
# Every text the export recheck's probe (fix-export/recheck1/try_paths.py) tried, with the README line of its F2 test:
MODDER_TEXTS = ("/var/home/jane/Models/tank.glb", "/Volumes/Jane Drive/models/tank.glb", "/opt/models/tank.glb",
                "/data/jane/models/tank.glb", "~/Models/tank.glb", "made from `/home/jane/x.glb`",
                "file:///home/jane/x.glb", "made from (/home/jane/x.glb)", "file:///C:/Users/jane/x.glb",
                "\\\\?\\C:\\Users\\jane\\x.glb", "Plan B:/C", "Hold sector A:\\ then B", "Phase 1: Take bridge X:/Y",
                "%USERPROFILE%\\Documents\\tank.glb", "C:\\Users\\jane\\x.glb; then see the manual\\page 3",
                "Made from C:\\models\\tank.glb, and docs\\turret.md tells how.", "https://example.org/x")
# What each becomes in his README (the owner, 2026-11-13, to "A folder path in a modder's own README, in an exported
# mod: cut it to the file name, or keep it with a warning?": "cut to file name"): only a path that names a folder is
# cut, to the name after its last slash, every word around it as written; "Plan B:/C" and the like name no folder
README_CUT = {"/var/home/jane/Models/tank.glb": "tank.glb", "/Volumes/Jane Drive/models/tank.glb": "tank.glb",
              "/opt/models/tank.glb": "tank.glb", "/data/jane/models/tank.glb": "tank.glb",
              "~/Models/tank.glb": "tank.glb", "made from `/home/jane/x.glb`": "made from `x.glb`",
              "file:///home/jane/x.glb": "x.glb", "made from (/home/jane/x.glb)": "made from (x.glb)",
              "file:///C:/Users/jane/x.glb": "x.glb", "\\\\?\\C:\\Users\\jane\\x.glb": "x.glb",
              "Plan B:/C": "Plan B:/C", "Hold sector A:\\ then B": "Hold sector A:\\ then B",
              "Phase 1: Take bridge X:/Y": "Phase 1: Take bridge X:/Y",
              "%USERPROFILE%\\Documents\\tank.glb": "tank.glb",
              "C:\\Users\\jane\\x.glb; then see the manual\\page 3": "x.glb; then see the manual\\page 3",
              "Made from C:\\models\\tank.glb, and docs\\turret.md tells how.":
                  "Made from tank.glb, and docs\\turret.md tells how.",
              "https://example.org/x": "https://example.org/x"}


class StudioPaths(unittest.TestCase):
    def test_a_path_the_studio_wrote_keeps_its_file_s_own_name_on_any_system(self):
        for text, want in (
                (PC + "\\horse_squad\\horse-squad-rifle.glb", "horse-squad-rifle.glb"),
                ("D:/RUSE-2.0/scratch/x/Boulder01.glb (far)", "Boulder01.glb (far)"),
                ("\\\\server\\share\\models\\tank.glb", "tank.glb"),
                ("/home/jane/models/tank.glb", "tank.glb"),
                ("/var/home/jane/.local/share/ruse-mod-platform/horse_squad/horse-squad-rifle.glb",
                 "horse-squad-rifle.glb"),
                ("/Volumes/Jane Drive/models/tank.glb", "tank.glb"), ("/opt/models/tank.glb", "tank.glb"),
                ("/data/jane/models/tank.glb", "tank.glb"), ("~/Models/tank.glb", "tank.glb"),
                ("file:///home/jane/x.glb", "x.glb"), ("file:///C:/Users/jane/x.glb", "x.glb"),
                ("\\\\?\\C:\\Users\\jane\\x.glb", "x.glb"), ("%USERPROFILE%\\Documents\\tank.glb", "tank.glb"),
                ("C:\\Users\\jane\\u1945.glb", "u1945.glb"), ("C:\\Users\\Jane Doe\\Desktop\\", "Desktop"),
                ("C:\\Users\\jane\\tank (2).glb (far)", "tank (2).glb (far)"), ("tank.glb", "tank.glb")):
            self.assertEqual(package.own_name(text), want, text)

    def test_which_picture_names_are_paths(self):
        for text in (PC + "\\coat.png", "/var/home/jane/coat.png", "\\\\server\\coat.png", "~/coat.png",
                     "file:///home/jane/coat.png", "%USERPROFILE%\\coat.png", "c:/coat.png"):
            self.assertTrue(package.is_absolute(text), text)
        for text in ("coat.png", "textures/coat.png", "textures\\coat.png", "$/GFX/Everything/X",
                     "https://example.org/coat.png", "Plan B:/C", None):
            self.assertFalse(package.is_absolute(text), text)


class HisReadme(unittest.TestCase):
    """package.paths_cut, what Export does to his README (the owner, 2026-11-13: "cut to file name"): each path that
    names a folder of a disk or a home loses its folders, the name after the last slash and every word around it stay.
    Each answer is written out here by hand, never worked out by the code under test."""

    def test_a_folder_path_is_cut_to_its_name_and_no_word_goes_with_it(self):
        for text, want in (
                ("Made from C:\\models\\tank.glb and docs\\turret.md", "Made from tank.glb and docs\\turret.md"),
                ("Made on C:\\Users\\Jane Doe\\AppData\\Local\\RUSE Mod Platform\\mods\\cavalry by me.",
                 "Made on cavalry by me."),
                ("I keep them in /home/jane/mods and /home/jane/maps.", "I keep them in mods and maps."),
                ("Put it in C:\\Mods\\MyMod\\ and play", "Put it in MyMod\\ and play"),
                ("C:\\Program Files (x86)\\Steam\\steamapps\\common\\R.U.S.E\\ZZ_Win.dat", "ZZ_Win.dat"),
                ("[my model](C:\\Users\\jane\\tank.glb)", "[my model](tank.glb)"),
                ("see /home/jane/x.glb and/or /tmp", "see x.glb and/or /tmp"),
                ("\\\\server\\share\\models\\tank.glb", "tank.glb"),
                ("E:\\Mods & Models\\Jane's (2026)\\horse-squad-rifle.glb", "horse-squad-rifle.glb"),
                ("C:\\Users\\jane\\My Tank.glb is mine", "My Tank.glb is mine"),
                ("C:/Users/jane/x.glb", "x.glb"), ("path=C:\\Users\\jane\\x.glb", "path=x.glb"),
                ("D:\\RUSE-2.0\\scratch\\x\\Boulder01.glb (far)", "Boulder01.glb (far)"),
                ("C:\\Mods\\Version 2.0 Final\\tank.glb", "tank.glb"),
                ("C:\\\\Users\\\\jane\\\\x.glb", "x.glb"), ("two: C:\\a\\b.glb, D:\\c\\d.glb.", "two: b.glb, d.glb."),
                ("Made from C:\\models\\tank.glb, and docs\\turret.md tells how.",
                 "Made from tank.glb, and docs\\turret.md tells how."),
                ("*~/Models/tank.glb*", "*tank.glb*"), ("%APPDATA%\\x\\y.glb", "y.glb")):
            self.assertEqual(package.paths_cut(text)[0], text if want is None else want, text)

    def test_what_names_no_folder_stays(self):
        for text in ("Join /r/ruse today", "C:\\tank.glb", "a\\b\\c and docs/x.md", "Plan B:/C",
                     "Hold sector A:\\ then B", "Phase 1: Take bridge X:/Y", "https://example.org/a/b/c.glb",
                     "By sneadtristen6: https://github.com/sneadtristen6/R.U.S.E-2.0-Project", "1/2/3", "and/or",
                     "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger", "~/x.glb", "/opt/x.glb", ""):
            self.assertEqual(package.paths_cut(text), (text, []), text)

    def test_what_export_says_of_each_cut(self):
        self.assertEqual(package.paths_cut("Made from C:\\models\\tank.glb, and more")[1],
                         [("C:\\models\\tank.glb,", "tank.glb,")])
        self.assertEqual(package.cut_shown("C:\\models\\tank.glb,", "tank.glb,"), "C:\\models\\tank.glb \u2192 tank.glb")
        self.assertEqual(package.cut_shown("C:\\a\\x.glb)", "x.glb)"), "C:\\a\\x.glb \u2192 x.glb")
        self.assertEqual(package.cut_shown("C:\\a\\tank (2).glb", "tank (2).glb"), "C:\\a\\tank (2).glb \u2192 tank (2).glb")

    def test_which_files_are_his_readmes(self):
        for name in ("README.md", "readme.txt", "files/docs/README", "src/README-fr.md", "maps/X/Readme_old.TXT",
                     "README.en.md", "readme"):
            self.assertTrue(package.is_readme(name), name)
        for name in ("CHANGELOG.md", "LICENSE", "files/notes/readme.png", "files/readmefirst.md", "src/units.rndf",
                     "README.glb", "notreadme.md", "text/units.csv"):
            self.assertFalse(package.is_readme(name), name)


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
        coat = f"{PC}\\pictures\\coat.png"                   # (a picture the model file names, not found)
        note = f"{coat}: its alpha picture is 4 x 4, the colour 8 x 8; plain alpha used"
        mine = {"from": PC + "\\horse_squad\\horse-squad-rifle.glb", "size": 1.0, "aircraft": False,
                "report": {"file": "horse-squad-rifle.glb", "missing": [coat, "textures/belt.png"],
                           "pictures": [[coat, 4, 4]], "alpha": {coat: "plain 255"},
                           "notes": [note, "Plan B:/C and docs\\turret.md stay as written"]},
                "for": "fusilier", "skeleton": "own", "copy_kept": f"# kept\nfrom = '{coat}'\n"}
        record = self.write("files/models/Descriptor_Unit_Horse_Squad.json", json.dumps(mine, indent=1))
        on_disk = record.read_bytes()
        cleaned, kinds = [], {}
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned, kinds=kinds)
        self.assertEqual(cleaned, ["files/models/Descriptor_Unit_Horse_Squad.json"])
        self.assertEqual(kinds, {"files/models/Descriptor_Unit_Horse_Squad.json": "record"})
        self.assertEqual(record.read_bytes(), on_disk)       # his own record keeps its folder: Resize uses it
        packed = members(out)["files/models/Descriptor_Unit_Horse_Squad.json"]
        self.assertEqual(json.loads(packed), dict(mine, **{"from": "horse-squad-rifle.glb", "report": {
            "file": "horse-squad-rifle.glb", "missing": ["coat.png", "textures/belt.png"],
            "pictures": [["coat.png", 4, 4]], "alpha": {"coat.png": "plain 255"},
            "notes": [note.replace(coat, "coat.png"), "Plan B:/C and docs\\turret.md stay as written"]}}))
        # every other byte as it was: only the strings naming those paths are written anew (the uniform's text kept
        # for Take it out, copy_kept, as it was)
        self.assertEqual(packed, on_disk.replace(json.dumps(mine["from"]).encode(), b'"horse-squad-rifle.glb"')
                         .replace(json.dumps(note).encode(), json.dumps(note.replace(coat, "coat.png")).encode())
                         .replace(json.dumps(coat).encode(), b'"coat.png"'))
        self.assertEqual(json.loads(packed)["copy_kept"], mine["copy_kept"])
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

    def test_only_what_the_studio_wrote_and_his_readme_s_folders_change_his_other_words_go_out_as_written(self):
        """The Studio's record and scenery model name only their files; his README goes out with the folder path in it
        cut to its own name (the owner, 2026-11-13: "cut to file name"), every other byte as he wrote it; his other
        texts (a TOML of his, a .rndf, a .csv) go out byte for byte, even naming a folder of his PC ("yes only warn"),
        and pack says which name his home folder. (Round 1 cut paths out of every text, and with them his words: the
        export recheck's F2.)"""
        self.write("files/models/Descriptor_Unit_X.json", json.dumps({"from": "D:/models/x.glb"}))
        doubled = PC.replace("\\", "\\\\")                   # (a TOML string writes each backslash twice)
        self.write("files/notes/made.toml", f'# made from {PC}\\x.blend\n[x]\nfile = "{doubled}\\\\x.glb"\n')
        self.write("README.md", f"Made on {PC}\\mods\\cavalry by sneadtristen6.\n")
        self.write("src/units.rndf", f"// made from {PC}\\x.blend; Plan B:/C\npatch $/B ( ProductionPrice *= 0.5 )\n")
        self.write("text/units.csv", f"key,us\nk1,Made from C:\\models\\tank.glb and docs\\turret.md\n")
        self.write("files/assets/A/A.glb", glb_naming("/home/jane/models/a.gltf"))
        cleaned, kinds, home_in, cuts = [], {}, [], {}
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned, kinds=kinds, home_in=home_in, home=PC,
                           cuts=cuts)
        self.assertEqual(kinds, {"files/assets/A/A.glb": "model", "files/models/Descriptor_Unit_X.json": "record",
                                 "README.md": "readme"})
        self.assertEqual(sorted(cleaned), ["README.md", "files/assets/A/A.glb", "files/models/Descriptor_Unit_X.json"])
        self.assertEqual(sorted(home_in), ["files/notes/made.toml", "src/units.rndf"])
        self.assertEqual(cuts, {"README.md": [(f"{PC}\\mods\\cavalry", "cavalry")]})
        got = members(out)
        self.assertEqual(got["README.md"], self.text("README.md").replace(f"{PC}\\mods\\".encode(), b""))
        self.assertEqual(got["README.md"].replace(b"\r\n", b"\n"), b"Made on cavalry by sneadtristen6.\n")
        self.assertIn(f"{PC}\\mods\\cavalry".encode(), self.text("README.md"))   # (his own README as he wrote it)
        for rel in ("files/notes/made.toml", "src/units.rndf", "text/units.csv", "mod.toml"):
            self.assertEqual(got[rel], self.text(rel), rel)
        self.assertEqual(json.loads(got["files/models/Descriptor_Unit_X.json"]), {"from": "x.glb"})
        doc, _binary = glb_document(got["files/assets/A/A.glb"])
        self.assertEqual((doc["meshes"][0]["name"], doc["asset"]["extras"]["rusemod_version"]), ("a.gltf", "a.gltf"))
        self.assertEqual(package.check(out)["id"], "cavalry")

    def test_every_text_the_recheck_tried_goes_out_as_written_but_his_readme_s_folder_paths(self):
        """Each text of the recheck's probe, in each kind of text a modder writes (mod.toml's description, a .rndf
        comment, a .csv text, CHANGELOG.md, the era credits): the member is the file, byte for byte (the owner,
        2026-11-13, "yes only warn"). In his README each folder path is cut to its own name and nothing else changes
        ("cut to file name"): README_CUT says what each text becomes, written out here, not worked out by the code."""
        texts = "\n".join(MODDER_TEXTS)
        self.write("README.md", texts + "\n")
        self.write("CHANGELOG.md", texts.encode("utf-8").replace(b"\n", b"\r\n"))
        self.write(era_units.CREDITS, f"# credits\n\n{texts}\n")
        self.write("src/units.rndf",
                   "".join(f"// {t}\n" for t in MODDER_TEXTS) + "patch $/B ( ProductionPrice *= 0.5 )\n")
        self.write("text/units.csv", "key,us\n" + "".join(f'k{i},"{t}"\n' for i, t in enumerate(MODDER_TEXTS)))
        manifest = self.mod / "mod.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8") + "description = "
                            + json.dumps(" / ".join(MODDER_TEXTS)) + "\n", encoding="utf-8")
        self.assertIn("Plan B:/C", tomllib.loads(manifest.read_text(encoding="utf-8"))["mod"]["description"])
        cleaned = []
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned)
        self.assertEqual(cleaned, ["README.md"])
        got = members(out)
        for rel in ("CHANGELOG.md", era_units.CREDITS, "src/units.rndf", "text/units.csv", "mod.toml"):
            self.assertEqual(got[rel], self.text(rel), rel)
        want = self.root / "want-README.md"            # (written as `write` writes a text: the PC's own line ends)
        want.write_text("\n".join(README_CUT[t] for t in MODDER_TEXTS) + "\n", encoding="utf-8")
        self.assertEqual(got["README.md"].decode("utf-8").splitlines(), want.read_text(encoding="utf-8").splitlines())
        self.assertEqual(got["README.md"], want.read_bytes())

    def test_every_readme_of_his_is_cut_and_no_other_text(self):
        """The class of his READMEs (package.is_readme): README.md at the top and any README of his in the mod's
        folders (readme.txt, README with no ending, README-fr.md), each folder path cut to its own name, his line
        ends and a UTF-8 mark at the start kept; the same path in CHANGELOG.md, LICENSE, a note of his or a picture
        called readme goes out byte for byte; a README that isn't UTF-8 goes out as written and is named when it names
        his home folder; a README with no folder path in it goes out byte for byte."""
        line = f"Made from {PC}\\models\\tank.glb, and docs\\turret.md tells how."
        cut = "Made from tank.glb, and docs\\turret.md tells how."
        readmes = {"README.md": (line + "\r\n").encode("utf-8"),
                   "files/notes/readme.txt": ("﻿" + line + "\n").encode("utf-8"),
                   "files/docs/README": (line + "\n").encode("utf-8"),
                   "src/README-fr.md": ("Fait depuis /home/jane/mods/tank.glb.\n").encode("utf-8")}
        for rel, data in readmes.items():
            self.write(rel, data)
        others = {"CHANGELOG.md": (line + "\n").encode("utf-8"), "LICENSE": (line + "\n").encode("utf-8"),
                  "files/notes/made.md": (line + "\n").encode("utf-8"), "files/notes/readme.png": b"\x89PNG " + line.encode(),
                  "files/latin/README.TXT": f"Fait sur {PC}\\x\\\xe9t\xe9.glb\n".encode("cp1252"),
                  "files/plain/README.md": b"Nothing here names a folder: docs\\turret.md, and/or /r/ruse.\n"}
        for rel, data in others.items():
            self.write(rel, data)
        cleaned, kinds, home_in, cuts = [], {}, [], {}
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned, kinds=kinds, home_in=home_in, home=PC,
                           cuts=cuts)
        got = members(out)
        self.assertEqual(got["README.md"], (cut + "\r\n").encode("utf-8"))
        self.assertEqual(got["files/notes/readme.txt"], ("﻿" + cut + "\n").encode("utf-8"))
        self.assertEqual(got["files/docs/README"], (cut + "\n").encode("utf-8"))
        self.assertEqual(got["src/README-fr.md"], "Fait depuis tank.glb.\n".encode("utf-8"))
        for rel, data in others.items():
            self.assertEqual(got[rel], data, rel)
        self.assertEqual(sorted(cleaned), sorted(readmes))
        self.assertEqual({k for k, v in kinds.items() if v == "readme"}, set(readmes))
        self.assertEqual(cuts["src/README-fr.md"], [("/home/jane/mods/tank.glb.", "tank.glb.")])
        self.assertEqual(sorted(home_in), ["CHANGELOG.md", "LICENSE", "files/latin/README.TXT", "files/notes/made.md"])
        for rel in readmes:                                  # (his own files as he wrote them)
            self.assertEqual(self.text(rel), readmes[rel], rel)

    def test_a_record_from_any_system_names_only_its_file(self):
        """F1 of the export recheck, as a class: the record's "from" is the file's own name wherever the folder was
        (no list of known folders), its other bytes as they were."""
        for i, made in enumerate(("/var/home/jane/.local/share/ruse-mod-platform/horse_squad/horse-squad-rifle.glb",
                                  "/Volumes/Jane Drive/models/horse-squad-rifle.glb",
                                  "/opt/models/horse-squad-rifle.glb", "/data/jane/horse-squad-rifle.glb",
                                  "\\\\?\\C:\\Users\\jane\\horse-squad-rifle.glb",
                                  "file:///home/jane/horse-squad-rifle.glb",
                                  "E:\\Mods & Models\\Jane's (2026)\\horse-squad-rifle.glb")):
            rel = f"files/models/Descriptor_Unit_X{i}.json"
            self.write(rel, json.dumps({"from": made, "size": 1.0, "report": {"file": "horse-squad-rifle.glb"}},
                                       indent=1))
        got = members(package.pack(self.mod, self.root / "out"))
        for i in range(7):
            rel = f"files/models/Descriptor_Unit_X{i}.json"
            packed = json.loads(got[rel])
            self.assertEqual(packed["from"], "horse-squad-rifle.glb", rel)
            self.assertEqual(got[rel], self.text(rel).replace(
                json.dumps(json.loads(self.text(rel))["from"]).encode(), b'"horse-squad-rifle.glb"'), rel)

    def test_a_model_the_modder_made_keeps_its_own_names(self):
        """A .glb of his (from Blender: no scenery source the Studio wrote) goes out byte for byte, a mesh name
        holding a path among it; a scenery model whose mesh name the modder changed keeps his name, its source the
        file's name only."""
        g = _Glb()
        g.doc["meshes"] = [{"name": "C:\\Users\\jane\\turret", "primitives": [{"attributes": {"POSITION": g.packed(
            struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0), 3, "VEC3", 5126, low=[0, 0, 0], high=[1, 1, 0])}}]}]
        g.doc["asset"]["generator"] = "Khronos glTF Blender I/O"
        his = self.write("files/models/Descriptor_Unit_Y.glb", g.to_bytes())
        made = glb_naming("D:\\maps\\a\\files\\assets\\Rock\\Rock.glb (far)")
        doc, binary = glb_document(made)
        doc["meshes"][0]["name"] = "his rock/far"
        js = json.dumps(doc, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        renamed = (struct.pack("<4sII", b"glTF", 2, 28 + len(js) + len(binary)) + struct.pack("<I4s", len(js), b"JSON")
                   + js + struct.pack("<I4s", len(binary), b"BIN\x00") + binary)
        self.write("files/assets/Rock/Rock_far.glb", renamed)
        got = members(package.pack(self.mod, self.root / "out"))
        self.assertEqual(got["files/models/Descriptor_Unit_Y.glb"], his.read_bytes())
        doc, _binary = glb_document(got["files/assets/Rock/Rock_far.glb"])
        self.assertEqual((doc["meshes"][0]["name"], doc["asset"]["extras"]["rusemod_version"]),
                         ("his rock/far", "Rock.glb (far)"))

    def test_a_map_import_record_names_only_its_folders(self):
        """maps/<Pack>/import.toml as the real-place import writes it (rusemod.placebase._import_toml, on the
        importer's branch): [base] folder, engine_run and engine_code name only their folders; every other line as it
        was. An import.toml the import didn't write goes out as it is."""
        def q(v):
            return json.dumps(v, ensure_ascii=False)
        lines = ["# The import's record (rusemod.placebase): what this map was made from, by what, with what choice.",
                 "# The build does not read it; the Studio's Import panel will.", "", "[place]", 'slug = "utah"',
                 f"note = {q('see C:/Users/jane/x for how')}", "", "[base]",
                 f"folder = {q(PC + chr(92) + 'places' + chr(92) + 'utah' + chr(92) + 'base-full')}",
                 'manifest_sha256 = "f7"', f"files = {q(json.dumps({'heights': 'ab'}))}",
                 f"engine_run = {q('/var/home/jane/terraform/builds/tf-base-land6')}",
                 f"engine_code = {q('D:/RUSE-2.0/scratch/terraform/run.py')}", "", "[made]", 'pack = "Utah"',
                 'importer = "rusemod.placebase"', "", "[said]", f"notes = [{q('heights from C:/data/dem.tif')}]", ""]
        record = self.write("maps/Utah/import.toml", "\n".join(lines))
        other = self.write("maps/Mine/import.toml", f'[base]\nfolder = {q(PC)}\n')
        kinds = {}
        got = members(package.pack(self.mod, self.root / "out", kinds=kinds))
        self.assertEqual(kinds, {"maps/Utah/import.toml": "import"})
        self.assertEqual(got["maps/Mine/import.toml"], other.read_bytes())
        want = record.read_bytes().decode("utf-8").splitlines(keepends=True)
        for k, name in ((8, 'folder = "base-full"'), (11, 'engine_run = "tf-base-land6"'),
                        (12, 'engine_code = "run.py"')):
            want[k] = name + want[k][len(want[k].rstrip("\r\n")):]
        self.assertEqual(got["maps/Utah/import.toml"].decode("utf-8"), "".join(want))
        self.assertEqual(tomllib.loads(got["maps/Utah/import.toml"].decode("utf-8"))["base"]["folder"], "base-full")


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
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "With the Generic Horse.")["job"])
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
        said = [ln for ln in view["lines"] if ln.startswith("In the exported file,")]
        self.assertEqual(said, ["In the exported file, these model records name only the file each model was made "
                                "from, not the folder on your PC it is in; nothing else in them changed: "
                                f"{record.relative_to(folder).as_posix()}."])
        self.api.set_pref("lang", "fr")
        worded = [ln for ln in self.api.job(view["id"])["lines"] if "ces fiches de modèle" in ln]
        self.assertEqual(len(worded), 1)
        library = self.home / "library" / package.info_of(folder)["id"]   # (Export puts it in his Launcher's library)
        self.assertEqual((library / era_units.INDEX).read_bytes(), got[era_units.INDEX])
        self.assertEqual((library / era_units.CREDITS).read_bytes(), got[era_units.CREDITS])

    def test_his_readme_s_folders_go_his_description_goes_out_as_written_and_the_export_says_both(self):
        """A README and a description of his naming folders of his PC (his home among them): Export cuts the README's
        folder path to its file's name (the owner, 2026-11-13: "cut to file name") and says so, his README in the mod
        as he wrote it; the description goes out as written ("yes only warn"), and Export says it names his home
        folder; both lines in his language."""
        folder = Path(self.api.new_mod("Shared")["current"])
        readme = f"Made from {PC}\\models\\tank.glb, and docs\\turret.md tells how.\nPlan B:/C\n"
        (folder / "README.md").write_bytes(readme.encode("utf-8"))
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        with mock.patch("pathlib.Path.home", return_value=Path(PC)):
            view = finished(self.api, self.api.export_mod("1.0.0", "a modder", f"Plan B:/C from {PC}\\x.glb")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        got = members(Path(view["result"]["path"]))
        self.assertEqual(got["README.md"], b"Made from tank.glb, and docs\\turret.md tells how.\nPlan B:/C\n")
        self.assertEqual((folder / "README.md").read_bytes(), readme.encode("utf-8"))   # (his own, as he wrote it)
        self.assertEqual(got["mod.toml"], (folder / "mod.toml").read_bytes())
        self.assertIn(f"Plan B:/C from {PC}\\x.glb", tomllib.loads(got["mod.toml"].decode("utf-8"))["mod"]
                      .get("description", ""))
        said = [ln for ln in view["lines"] if ln.startswith("These files of the mod name your PC's home folder")]
        self.assertEqual(said, [f"These files of the mod name your PC's home folder ({PC}) and go out as they are, "
                                "since Export never changes what you wrote: change them in the mod if that shouldn't "
                                "be shared: mod.toml."])
        cut = [ln for ln in view["lines"] if ln.startswith("In the exported file,")]
        self.assertEqual(cut, ["In the exported file, each folder path in these README files of yours is cut to its "
                               "own name, every other word as you wrote it; the files in your mod stay as they are: "
                               f"README.md ({PC}\\models\\tank.glb \u2192 tank.glb)."])
        self.api.set_pref("lang", "ger")
        lines = self.api.job(view["id"])["lines"]
        self.assertEqual(len([ln for ln in lines if "Benutzerordner" in ln]), 1)
        self.assertEqual([ln for ln in lines if ln.startswith("In der exportierten Datei ist jeder Ordnerpfad")],
                         ["In der exportierten Datei ist jeder Ordnerpfad in diesen README-Dateien von Ihnen auf seinen "
                          "eigenen Namen gekürzt, jedes andere Wort so, wie Sie es geschrieben haben; die Dateien in "
                          f"Ihrem Mod bleiben, wie sie sind: README.md ({PC}\\models\\tank.glb \u2192 tank.glb)."])

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
