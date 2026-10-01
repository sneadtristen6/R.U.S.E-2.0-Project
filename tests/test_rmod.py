""".rmod mods through LittleGroove's engine (rusemod.rmod), on made-up packs: nothing is written to the game, the
changes reach the modded copy, mods with scripts are refused, and mods that don't go together are found before
anything is built (no game files needed)."""
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


def rmod_json(files, mod_id="Test.Map_Mod-1", version="1.2", container="", name="Test mod", patches=(), texts=()):
    """A .rmod replacing (or adding) whole files in the unit pack, plus value changes (`patches`: his change objects
    on the unit data file) and texts (`texts`: {key: value} in baseunite.dic)."""
    return json.dumps({
        "$schema": "ruse-mod/v1", "id": mod_id, "name": name, "version": version, "author": "Tester",
        "description": "made up", "game_version": "",
        "patches": [{"dat": PACK, "ndf": "genglad/patchable/everything.cpp.gladndfbin", "changes": list(patches)}]
        if patches else [],
        "file_patches": [{"dat": PACK, "files": [
            {"path": p, "data": base64.b64encode(d).decode(), **({"container": container} if container else {})}
            for p, d in files.items()]}] if files else [],
        "loc_patches": [{"dat": "Data/PC/190852/ZZ_Win.dat", "dic": "genlocalisation/ww2/localisation/translations/us/"
                        "baseunite.dic", "entries": [{"key": k, "value": v} for k, v in dict(texts).items()]}]
        if texts else []})


def set_values(unit, **values):
    """A change setting `values` on the unit called `unit` (as his mods do: match by ClassNameForDebug)."""
    return {"action": "patch", "table": "TUnitDescriptor", "match": {"ClassNameForDebug": unit},
            "set": {k: {"type": "Float32", "value": v} for k, v in values.items()}}


def new_unit(name):
    return {"action": "create", "table": "TUnitDescriptor", "match": {}, "local_id": "u1",
            "set": {"ClassNameForDebug": {"type": "StringRef", "value": name}}}


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

    def test_a_community_mod_packs_with_its_rmod(self):
        """Packed for the mod list or a friend, a library mod made from a .rmod carries the .rmod: without it the
        package held only its manifest, and installed nothing."""
        from rusemod.package import check, files_of, pack
        path = self.write("Test_Mod_V1.rmod", rmod_json({"genglad/readme.txt": b"new"}))
        Library(self.dir / "library").add(path)
        folder = self.dir / "library" / "test-map-mod-1"
        self.assertIn(folder / "Test_Mod_V1.rmod", files_of(folder))
        packed = pack(folder, self.dir)
        info = check(packed)  # read the way a build would, from the package alone
        self.assertIn("Test_Mod_V1.rmod", info["files"])
        self.assertEqual(info["id"], "test-map-mod-1")


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
        # the same readme.txt as A brings (identical bytes: no clash; two different ones would stop the build)
        b = self.mod("B.rmod", {"genglad/readme.txt": b"from A", "top.bin": b"from B"}, mod_id="b", name="Mod B")
        lines = []
        result = build_and_write(self.game, [a, b], instance=self.instance, say=lines.append)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.order, ["a", "b"])
        got = self.packed(self.instance)
        self.assertEqual((got["genglad\\readme.txt"], got["genglad\\brand\\new.bin"], got["top.bin"]),
                         (b"from A", b"NEW", b"from B"))
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

    def test_hard_clashes_stop_the_build_soft_ones_are_warnings(self):
        a = self.mod("A.rmod", {"genpython/map/effetmap.xyz": b"XYZ0 A"}, mod_id="a", name="Mod A",
                     patches=[set_values("Unit_Battleship", VitesseLineaire=9.5)])
        b = self.mod("B.rmod", {"genpython/map/effetmap.xyz": b"XYZ0 B"}, mod_id="b", name="Mod B",
                     patches=[set_values("Unit_Battleship", VitesseLineaire=0)])
        lines = []
        with self.assertRaises(BuildError) as cm:
            build_and_write(self.game, [a, b], instance=self.instance, say=lines.append)
        message = str(cm.exception)
        self.assertIn("These mods can't be played together (1 clash):", message)
        self.assertIn("Mod A and Mod B each replace the same script, effetmap.xyz", message)
        self.assertIn("Nothing was built.", message)
        self.assertTrue(any(line.startswith("  error") and "Mod A and Mod B" in line for line in lines), lines)
        self.assertFalse(self.instance.exists())
        c = self.mod("C.rmod", {"genpython/map/other.xyz": b"XYZ0 C"}, mod_id="c", name="Mod C",
                     patches=[set_values("Unit_Battleship", VitesseLineaire=0)])
        result = build_and_write(self.game, [a, c], instance=self.instance, say=lines.append)
        warnings = [f.message for f in result.findings if f.level == "warning"]
        self.assertIn("Mod C changes 1 value Mod A changed too, e.g. Unit_Battleship.VitesseLineaire; it comes later, so "
                      "it wins. Put Mod A after Mod C if you want Mod A's values.", warnings)


class Clashes(unittest.TestCase):
    """Mods that don't go together (rusemod.rmod.clashes), found from the .rmod files alone: the same file replaced
    with different bytes, an archive replaced whole and edited inside, two new objects with one name (hard: the
    build refuses the set); a later mod overwriting an earlier one's values or texts (soft: a warning)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, name, files=None, **kw):
        path = self.root / f"{name}.rmod"
        path.write_text(rmod_json(files or {}, mod_id=name.lower(), name=name, **kw), encoding="utf-8")
        return path

    def kinds(self, *paths):
        return [(c.kind, c.hard, c.mods) for c in rmod.clashes(paths)]

    def test_the_same_file_with_different_bytes_is_hard_identical_bytes_are_fine(self):
        a = self.mod("Alpha", {"genpython/map/effetmap.xyz": b"XYZ0 script A"})
        b = self.mod("Beta", {"genpython/map/effetmap.xyz": b"XYZ0 script B"})
        same = self.mod("Same", {"genpython/MAP/effetmap.xyz": b"XYZ0 script A"})  # as A, another spelling
        other = self.mod("Other", {"genpython/map/other.xyz": b"XYZ0 script C"})
        found = rmod.clashes([a, b, other])
        self.assertEqual([(c.kind, c.hard, c.mods, c.what, c.file_kind) for c in found],
                         [("file", True, ["Alpha", "Beta"], "genpython/map/effetmap.xyz", "script")])
        self.assertIn("Alpha and Beta each replace the same script, effetmap.xyz", found[0].message)
        self.assertIn("Only one of them can be in a set.", found[0].message)
        self.assertEqual(found[0].sides(), ("Alpha", "Beta"))
        self.assertEqual(found[0].view()["a"], "Alpha")
        self.assertEqual(self.kinds(a, same), [])          # identical bytes: harmless
        self.assertEqual(self.kinds(a, same, b), [("file", True, ["Alpha", "Same", "Beta"])])
        self.assertEqual(self.kinds(a), [])
        self.assertEqual(rmod.file_kind("x/y.scenario"), "map file")
        self.assertEqual(rmod.file_kind("x/y.ndfbin"), "game data")

    def test_a_file_inside_an_archive_and_the_archive_replaced_whole(self):
        ipk = "genpython/eugenpatchable.ipk"
        a = self.mod("Alpha", {"genpython/eugen/classes.xyz": b"XYZ0 A"}, container=ipk)
        b = self.mod("Beta", {"genpython/eugen/classes.xyz": b"XYZ0 B"}, container=ipk)
        c = self.mod("Gamma", {"genpython/eugen/other.xyz": b"XYZ0 C"}, container=ipk)
        whole = self.mod("Whole", {ipk: b"EDAT whole archive"})
        found = rmod.clashes([a, b, c])
        self.assertEqual([(x.kind, x.mods) for x in found], [("script", ["Alpha", "Beta"])])
        self.assertIn("inside eugenpatchable.ipk", found[0].message)
        found = rmod.clashes([c, whole])
        self.assertEqual([(x.kind, x.hard, x.mods, x.what) for x in found],
                         [("archive", True, ["Whole", "Gamma"], "eugenpatchable.ipk")])
        self.assertEqual(found[0].sides(), ("Whole", "Gamma"))
        self.assertEqual(self.kinds(whole, a, c), [("archive", True, ["Whole", "Alpha", "Gamma"])])  # either order

    def test_two_new_objects_with_one_name(self):
        a = self.mod("Alpha", patches=[new_unit("Unit_Zeppelin")])
        b = self.mod("Beta", patches=[new_unit("Unit_Zeppelin")])
        c = self.mod("Gamma", patches=[new_unit("Unit_Blimp")])
        found = rmod.clashes([a, c, b])
        self.assertEqual([(x.kind, x.hard, x.mods, x.what) for x in found], [("create", True, ["Alpha", "Beta"], "Unit_Zeppelin")])
        self.assertIn("each add a new TUnitDescriptor 'Unit_Zeppelin'", found[0].message)

    def test_a_later_mod_overwriting_values_and_texts_is_soft(self):
        navy = self.mod("Navy", patches=[set_values("Unit_Battleship", VitesseLineaire=9.5, Blindage=3),
                                         set_values("Unit_Destroyer", VitesseLineaire=12)], texts={"86504ed857620000": "Ship"})
        static = self.mod("Static", patches=[set_values("Unit_Battleship", VitesseLineaire=0, Blindage=3, Portee=1)],
                          texts={"86504ed857620000": "Boat", "86504ed857620001": "New"})
        other = self.mod("Other", patches=[set_values("Unit_Tank", Blindage=1)])
        found = rmod.clashes([navy, other, static])
        self.assertEqual([(c.kind, c.hard, c.mods, c.what, c.count) for c in found],
                         [("value", False, ["Navy", "Static"], "Unit_Battleship.VitesseLineaire", 2),
                          ("text", False, ["Navy", "Static"], "baseunite.dic 86504ed857620000", 1)])
        self.assertEqual(found[0].message, "Static changes 2 values Navy changed too, e.g. Unit_Battleship.VitesseLineaire; "
                                           "it comes later, so it wins. Put Navy after Static if you want Navy's values.")
        self.assertEqual(found[0].sides(), ("Static", "Navy"))  # the later mod first: it wins
        self.assertEqual([c.mods for c in rmod.clashes([static, navy])], [["Static", "Navy"], ["Static", "Navy"]])

    def test_the_best_order_lets_the_smaller_mod_keep_its_values(self):
        navy = self.mod("Navy", patches=[set_values("Unit_Battleship", VitesseLineaire=9.5, Blindage=3),
                                         set_values("Unit_Destroyer", VitesseLineaire=12, Blindage=2)])
        static = self.mod("Static", patches=[set_values("Unit_Battleship", VitesseLineaire=0)])
        other = self.mod("Other", patches=[set_values("Unit_Tank", Blindage=1)])
        # Navy changes 4 values, Static 1 (the battleship's speed, the reason it exists): Static goes after Navy, in
        # Navy's place; Other shares nothing and stays where it is
        self.assertEqual(rmod.best_order([static, other, navy]), [2, 1, 0])
        self.assertEqual(rmod.overwritten([static, other, navy]), [1, 0, 0])   # now Static loses all it changes
        self.assertEqual(rmod.overwritten([navy, other, static]), [1, 0, 0])   # after: Navy loses 1 of its 4
        self.assertEqual(rmod.sizes([navy, static, other]), [4, 1, 1])
        self.assertEqual(rmod.best_order([navy, other, static]), [0, 1, 2])   # already the best order
        # two groups that share nothing are each ordered in their own places; a tie keeps the set's order
        tanks = self.mod("Tanks", patches=[set_values("Unit_Tank", Blindage=2, Vitesse=3)])
        self.assertEqual(rmod.best_order([static, other, navy, tanks]), [2, 3, 0, 1])
        again = self.mod("Again", patches=[set_values("Unit_Battleship", VitesseLineaire=5)])
        self.assertEqual(rmod.best_order([again, static]), [0, 1])
        self.assertEqual(rmod.best_order([static, self.root / "ours", navy]), [2, 1, 0])  # not a .rmod: stays

    def test_library_folders_other_mods_and_changed_files(self):
        a = self.mod("Alpha", {"genpython/map/effetmap.xyz": b"XYZ0 A"})
        b = self.mod("Beta", {"genpython/map/effetmap.xyz": b"XYZ0 B"})
        folder = self.root / "lib" / "beta"
        rmod.make_folder(b, folder)
        self.assertEqual(rmod.rmod_of(folder), folder / "Beta.rmod")
        self.assertIsNone(rmod.rmod_of(self.root))
        ours = self.root / "ours"
        ours.mkdir()
        (ours / "mod.toml").write_text('[mod]\nid = "ours"\n', encoding="utf-8")
        self.assertEqual(self.kinds(a, folder, ours, self.root / "missing.rmod"), [("file", True, ["Alpha", "Beta"])])
        b.write_text(rmod_json({"genpython/map/effetmap.xyz": b"XYZ0 A"}, mod_id="beta", name="Beta"), encoding="utf-8")
        self.assertEqual(self.kinds(a, b), [])  # the file changed: read again, and now the bytes are the same


if __name__ == "__main__":
    unittest.main()
