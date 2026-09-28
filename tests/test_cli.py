"""The `ruse` tool, Steam detection and the text view, on a made-up Steam install and game (no game files needed)."""
import contextlib
import io
import os
import struct
import tempfile
import unittest
import uuid
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Ndf
from rusemod.cli import main
from rusemod.dic import name_to_key
from rusemod.steam import find_game, parse_vdf
from rusemod.text import NdfText


def ref(i):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, 0))


def i32(v):
    return val(0x02, struct.pack("<i", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


# #0 Unit (named) -> #1 weapon (only #0 uses it: printed inside) and #2 part (shared with #3: printed on its own)
CLASSES = ["TUnit", "TWeapon", "TPart"]
PROPS = [("Price", 0), ("Name", 0), ("Weapon", 0), ("Parts", 0), ("Damage", 1), ("Id", 0), ("Title", 0), ("Big", 0)]
GUID = uuid.UUID("12345678-1234-5678-9abc-def012345678")
OBJECTS = [
    (0, [(0, val(0x11, struct.pack("<I", 2) + i32(30) + i32(40))),
         (1, val(0x1D, struct.pack("<Q", name_to_key("M_D_01")))),
         (2, ref(1)),
         (3, val(0x11, struct.pack("<I", 1) + ref(2))),
         (5, val(0x1A, GUID.bytes_le)),
         (6, val(0x08, struct.pack("<I", 10) + "Hello".encode("utf-16-le"))),
         (7, val(0x00, b"\x4e"))]),
    (1, [(4, f32(1.5))]),
    (2, []),
    (0, [(3, val(0x11, struct.pack("<I", 1) + ref(2)))]),
]
NDF = make_ndf(objects=OBJECTS, classes=CLASSES, props=PROPS, exports={0: "Unit", 3: "Other"})


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Vdf(unittest.TestCase):
    def test_new_library_format_with_escapes_and_comments(self):
        text = '''// comment
"libraryfolders"
{
    "0" { "path" "C:\\\\Program Files (x86)\\\\Steam" "apps" { "21970" "123" } }
    "1" { "path" "D:\\\\SteamLibrary" }
}'''
        data = parse_vdf(text)["libraryfolders"]
        self.assertEqual(data["0"]["path"], "C:\\Program Files (x86)\\Steam")
        self.assertEqual(data["1"]["path"], "D:\\SteamLibrary")
        self.assertEqual(data["0"]["apps"]["21970"], "123")

    def test_keys_are_case_insensitive_and_empty_values_kept(self):
        data = parse_vdf('"AppState" { "InstallDir" "R.U.S.E" "LastOwner" "" }')
        self.assertEqual(data["appstate"], {"installdir": "R.U.S.E", "lastowner": ""})


class FindGame(unittest.TestCase):
    def test_finds_the_game_in_a_second_library_with_its_branch(self):
        with tempfile.TemporaryDirectory() as d:
            steam, lib = Path(d, "Steam"), Path(d, "Lib2")
            (steam / "steamapps").mkdir(parents=True)
            lib_escaped = str(lib).replace("\\", "\\\\")
            (steam / "steamapps" / "libraryfolders.vdf").write_text(
                f'"libraryfolders" {{ "0" {{ "path" "{str(steam)}" }} "1" {{ "path" "{lib_escaped}" }} }}')
            (lib / "steamapps" / "common" / "R.U.S.E" / "Data" / "PC" / "190852").mkdir(parents=True)
            (lib / "steamapps" / "appmanifest_21970.acf").write_text(
                '"AppState" { "appid" "21970" "installdir" "R.U.S.E" "buildid" "24687178" '
                '"UserConfig" { "language" "english" "BetaKey" "compat" } }')
            found = find_game([steam])
            self.assertEqual(found["game_dir"], lib / "steamapps" / "common" / "R.U.S.E")
            self.assertEqual((found["build_id"], found["branch"], found["data_revisions"]),
                             ("24687178", "compat", ["190852"]))

    def test_nothing_found(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(find_game([Path(d)]))


class TextView(unittest.TestCase):
    def setUp(self):
        self.text = "\n".join(NdfText(Ndf(NDF)).lines())

    def test_named_objects_and_values(self):
        for expected in ["export Unit is TUnit   // $/Unit, #0",
                         "    Price = [30, 40]",
                         "    Name = key(M_D_01)",
                         "    Id = GUID:{12345678-1234-5678-9abc-def012345678}",
                         '    Title = wstr("Hello")',
                         "    Big = bool(0x4E)"]:
            self.assertIn(expected, self.text)

    def test_single_use_objects_are_printed_inside_their_owner(self):
        self.assertIn("    Weapon = TWeapon\n    (\n        Damage = 1.5\n    )", self.text)
        self.assertNotIn("#1 is", self.text)

    def test_shared_objects_are_printed_on_their_own(self):
        self.assertIn("    Parts = [#2]", self.text)
        self.assertIn("#2 is TPart   // unnamed, shared: used by #0, #3", self.text)

    def test_filter_keeps_matching_objects(self):
        only = "\n".join(NdfText(Ndf(NDF)).lines("other"))
        self.assertIn("export Other is TUnit", only)
        self.assertNotIn("export Unit is", only)


class Commands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Path(self.tmp.name, "R.U.S.E")
        packs = self.game / "Data" / "PC" / "190852"
        packs.mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        inner = make_edat([("file", "eugen\\base\\camp.xyz", b"XYZ0")])
        (packs / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([
            ("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", NDF)]),
            ("file", "genpython\\eugen.ipk", inner),
        ]))

    def tearDown(self):
        self.tmp.cleanup()

    def test_ls_finds_the_pack_by_name(self):
        code, out, _ = run("--game", str(self.game), "ls", "ZZ_GladPatchableWin.dat")
        self.assertEqual(code, 0)
        self.assertIn("genglad\\patchable\\gfx\\everything.cpp.gladndfbin", out)
        self.assertIn("2 file(s)", out)

    def test_ls_inside_a_nested_pack(self):
        code, out, _ = run("--game", str(self.game), "ls", "zz_gladpatchablewin.dat!eugen.ipk")
        self.assertEqual(code, 0)
        self.assertIn("eugen\\base\\camp.xyz", out)

    def test_names_and_dump(self):
        code, out, _ = run("--game", str(self.game), "names", "ZZ_GladPatchableWin.dat", "unit")
        self.assertEqual(code, 0)
        self.assertIn("$/Unit    TUnit", out)
        code, out, _ = run("--game", str(self.game), "dump", "ZZ_GladPatchableWin.dat", "everything.cpp.gladndfbin")
        self.assertEqual(code, 0)
        self.assertIn("// 4 objects, 3 classes, 2 named", out)
        self.assertIn("export Unit is TUnit", out)

    def test_extract_writes_elsewhere_but_never_into_the_game(self):
        out_dir = Path(self.tmp.name, "extracted")
        code, out, _ = run("--game", str(self.game), "extract", "ZZ_GladPatchableWin.dat", "everything",
                           "--out", str(out_dir))
        self.assertEqual(code, 0)
        self.assertEqual((out_dir / "genglad" / "patchable" / "gfx" / "everything.cpp.gladndfbin").read_bytes(), NDF)
        code, _, err = run("--game", str(self.game), "extract", "ZZ_GladPatchableWin.dat", "everything",
                           "--out", str(self.game / "Data"))
        self.assertEqual(code, 2)
        self.assertIn("Refusing to write into the game folder", err)

    def test_friendly_errors(self):
        code, _, err = run("--game", str(self.game), "ls", "Nope.dat")
        self.assertEqual(code, 2)
        self.assertIn("No pack called 'Nope.dat'", err)
        code, _, err = run("--game", str(self.game), "dump", "ZZ_GladPatchableWin.dat", "missing.bin")
        self.assertEqual(code, 2)
        self.assertIn("No file ending in 'missing.bin'", err)


if __name__ == "__main__":
    unittest.main()
