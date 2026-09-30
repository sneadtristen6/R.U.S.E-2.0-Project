""".rmod mods through LittleGroove's engine (rusemod.rmod), on made-up packs: nothing is written to the game, the
changes reach the modded copy, and mods with scripts are refused (no game files needed)."""
import base64
import json
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat
from rusemod import rmod
from rusemod.build import BuildError, build_and_write, load_mod
from rusemod.edat import Edat
from ruse_launcher.library import Library, LibraryError

TREE = [
    ("dir", "genglad\\", [
        ("file", "readme.txt", b"hello"),
        ("dir", "patchable\\", [("file", "everything.cpp.gladndfbin", b"UNIT DATA " * 10)]),
    ]),
    ("file", "top.bin", b"\x00\x01\x02"),
]
PACK = "Data/PC/190852/ZZ_GladPatchableWin.dat"


def rmod_json(files, mod_id="Test.Map_Mod-1", version="1.2", container="", name="Test mod"):
    """A .rmod replacing (or adding) whole files in the unit pack."""
    return json.dumps({
        "$schema": "ruse-mod/v1", "id": mod_id, "name": name, "version": version, "author": "Tester",
        "description": "made up", "game_version": "", "patches": [],
        "file_patches": [{"dat": PACK, "files": [
            {"path": p, "data": base64.b64encode(d).decode(), **({"container": container} if container else {})}
            for p, d in files.items()]}]})


class Layers(unittest.TestCase):
    def setUp(self):
        self.raw = make_edat(TREE)
        self.pack = rmod.Layered(Edat(self.raw), "made-up.dat")

    def test_reads_see_the_changes_and_nothing_else_moves(self):
        p = self.pack
        self.assertEqual(p.get("GENGLAD/readme.txt"), b"hello")
        p.replace("genglad\\readme.txt", b"changed")
        p.add("genglad/new.bin", b"NEW")
        p.batch_update({"top.bin": b"top!"}, {"more\\x.bin": b"x"})
        self.assertEqual((p.get("genglad/readme.txt"), p.get("GENGLAD\\NEW.BIN"), p.get("top.bin")),
                         (b"changed", b"NEW", b"top!"))
        self.assertEqual(p.read(p.find("readme.txt")), b"changed")
        self.assertIn("more\\x.bin", [e.path for e in p._entries])
        self.assertIsNone(p.get("nothing.bin"))
        with self.assertRaises(KeyError):
            p.add("top.bin", b"again")
        with self.assertRaises(KeyError):
            p.replace("nothing.bin", b"x")
        self.assertEqual(self.raw, make_edat(TREE))  # the pack itself is only read
        out = Edat(p.to_bytes({"patchable\\everything.cpp.gladndfbin": b"ours"}))
        got = {e.path: out.read(e) for e in out.entries}
        self.assertEqual(got, {"genglad\\readme.txt": b"changed", "genglad\\patchable\\everything.cpp.gladndfbin": b"ours",
                               "top.bin": b"top!", "genglad\\new.bin": b"NEW", "more\\x.bin": b"x"})


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_game_scripts_are_allowed_programs_are_not(self):
        path = self.write("Scripted.rmod", rmod_json({"genpython/eugen/x.xyz": b"code"},
                                                     container="genpython/eugenpatchable.ipk"))
        info, _ = load_mod(path)
        self.assertEqual(rmod.scripts_of(rmod.check(info.rmod)), ["genpython/eugenpatchable.ipk/genpython/eugen/x.xyz"])
        with self.assertRaises(BuildError) as cm:
            load_mod(self.write("Program.rmod", rmod_json({"tools/setup.exe": b"MZ"})))
        self.assertIn("run on the PC", str(cm.exception))
        with self.assertRaises(BuildError):
            load_mod(self.write("Bad.rmod", "{not json"))

    def test_the_library_keeps_a_rmod_next_to_a_manifest_made_from_it(self):
        path = self.write("Test_Mod_V1.rmod", rmod_json({"genglad/readme.txt": b"new"}))
        info, replaced = Library(self.dir / "library").add(path)
        self.assertEqual((info["id"], info["name"], info["version"], info["authors"], replaced),
                         ("test-map-mod-1", "Test mod", "1.2", ["Tester"], False))
        folder = self.dir / "library" / "test-map-mod-1"
        self.assertEqual((folder / "Test_Mod_V1.rmod").read_bytes(), path.read_bytes())
        mod, ops = load_mod(folder)
        self.assertEqual((mod.id, mod.rmod, ops), ("test-map-mod-1", folder / "Test_Mod_V1.rmod", []))
        program = self.write("Program.rmod", rmod_json({"a/b.dll": b"MZ"}, mod_id="program"))
        with self.assertRaises(LibraryError):
            Library(self.dir / "library").add(program)


class Builds(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "R.U.S.E"
        (self.game / "Data" / "PC" / "190852").mkdir(parents=True)
        self.pack = self.game / PACK
        self.pack.write_bytes(make_edat(TREE))
        (self.game / "RUSE.exe").write_bytes(b"made up")
        self.instance = root / "instances" / "test"
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, file_name, files, **kw):
        path = self.root / file_name
        path.write_text(rmod_json(files, **kw), encoding="utf-8")
        return load_mod(path)

    def packed(self, folder):
        arc = Edat((folder / PACK).read_bytes())
        return {e.path: bytes(arc.read(e)) for e in arc.entries}

    def test_changes_reach_the_modded_copy_and_never_the_game(self):
        a = self.mod("A.rmod", {"genglad/readme.txt": b"from A", "genglad/brand/new.bin": b"NEW"}, mod_id="a",
                     name="Mod A")
        b = self.mod("B.rmod", {"genglad/readme.txt": b"from B"}, mod_id="b", name="Mod B")
        lines = []
        result = build_and_write(self.game, [a, b], instance=self.instance, say=lines.append)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.order, ["a", "b"])
        got = self.packed(self.instance)
        self.assertEqual((got["genglad\\readme.txt"], got["genglad\\brand\\new.bin"], got["top.bin"]),
                         (b"from B", b"NEW", b"\x00\x01\x02"))  # the later mod wins
        self.assertTrue(any("1 change(s) overwrite 'Mod A'" in f.message for f in result.findings), result.findings)
        self.assertEqual(self.pack.read_bytes(), make_edat(TREE))
        self.assertIsNotNone(result.fingerprint)
        out = self.root / "out"
        build_and_write(self.game, [a], out=out, say=lines.append)
        written = Edat((out / "ZZ_GladPatchableWin.dat").read_bytes())
        self.assertEqual(written.read(written.find("readme.txt")), b"from A")

    def test_a_mod_with_game_scripts_builds_with_a_warning(self):
        mod = self.mod("S.rmod", {"genpython/map/effetmap.xyz": b"XYZ0 code"}, mod_id="s", name="Scripted")
        result = build_and_write(self.game, [mod], instance=self.instance, say=lambda s: None)
        self.assertEqual(result.errors, [])
        self.assertTrue(any("game's scripts (effetmap.xyz)" in f.message for f in result.findings if
                            f.level == "warning"), result.findings)
        self.assertEqual(self.packed(self.instance)["genpython\\map\\effetmap.xyz"], b"XYZ0 code")

    def test_a_mod_for_a_pack_the_game_lacks_writes_nothing(self):
        text = rmod_json({"x.bin": b"x"}).replace("ZZ_GladPatchableWin.dat", "NoSuchPack.dat")
        (self.root / "C.rmod").write_text(text, encoding="utf-8")
        lines = []
        result = build_and_write(self.game, [load_mod(self.root / "C.rmod")], instance=self.instance,
                                 say=lines.append)
        self.assertTrue(result.errors)
        self.assertIn("Nothing was written.", lines)
        self.assertFalse(self.instance.exists())


if __name__ == "__main__":
    unittest.main()
