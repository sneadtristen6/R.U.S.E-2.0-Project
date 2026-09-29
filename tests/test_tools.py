"""The read-only check tools, run end to end on a made-up game folder (no game files needed)."""
import contextlib
import io
import json
import os
import struct
import sys
import tempfile
import unittest

from fixtures import make_edat, make_ndf, val
from test_dic import MP01_KEY, make_dic

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import dic_check  # noqa: E402
import identity_check  # noqa: E402
import names_check  # noqa: E402
import nation_scan  # noqa: E402
import rmod_to_mod  # noqa: E402
import topo_check  # noqa: E402
import verify_terrain  # noqa: E402
from rusemod import Ndf  # noqa: E402
from rusemod.build import load_mod  # noqa: E402
from rusemod.dic import name_to_key  # noqa: E402
from rusemod.patch import Engine, Game, Inline, ListV, Obj, Ref, Text, num, nums  # noqa: E402
from rusemod.resolve import ModInfo  # noqa: E402

REF = 0x09


def local(i):
    return val(REF, struct.pack("<III", 0xBBBBBBBB, i, 0))


# object 0 (class 0, named) points at 1 (class 1); object 2 (class 0) stands alone -> roots {0, 2}
OBJECTS = [(0, [(0, local(1))]), (1, []), (0, [])]
NDF_ARGS = dict(objects=OBJECTS, classes=["TUnit", "TPart"], props=[("Part", 0)], exports={0: "Unit"})


def fake_game(root):
    pack_dir = os.path.join(root, "Data", "PC", "190852")
    os.makedirs(pack_dir)
    pack = make_edat([
        ("dir", "gen\\", [
            ("file", "everything.cpp.gladndfbin", make_ndf(topo=[0, 2], **NDF_ARGS)),
            ("file", "localisation\\translations\\us\\units.dic", make_dic([(MP01_KEY, "Blitz")])),
        ]),
    ])
    with open(os.path.join(pack_dir, "ZZ_Win.dat"), "wb") as f:
        f.write(pack)


def run(module, root, *more):
    out = io.StringIO()
    old = sys.argv
    sys.argv = ["x", root, *more]
    try:
        with contextlib.redirect_stdout(out):
            code = module.main()
    finally:
        sys.argv = old
    return code, out.getvalue()


class TopoCheck(unittest.TestCase):
    def test_a_file_that_follows_the_rule(self):
        f = topo_check.check_file(Ndf(make_ndf(topo=[0, 2], **NDF_ARGS)))
        self.assertTrue(f["A_sorted_by_class"] and f["B_equals_roots"] and f["C_exports_in_topo"])

    def test_a_file_that_breaks_it(self):
        f = topo_check.check_file(Ndf(make_ndf(topo=[1, 2], **NDF_ARGS)))
        self.assertFalse(f["A_sorted_by_class"])   # #1 is class 1, #2 is class 0: out of class order
        self.assertFalse(f["B_equals_roots"])      # #1 is referenced by #0, and root #0 is missing
        self.assertFalse(f["C_exports_in_topo"])   # the named object #0 is missing

    def test_no_topo_means_nothing_to_check(self):
        self.assertIsNone(topo_check.check_file(Ndf(make_ndf(**NDF_ARGS))))


class EndToEnd(unittest.TestCase):
    def test_both_tools_run_on_a_fake_game(self):
        with tempfile.TemporaryDirectory() as root:
            fake_game(root)
            code, out = run(topo_check, root)
            self.assertEqual(code, 0)
            self.assertIn("B. exactly the objects nothing refers to: 1 of 1", out)
            code, out = run(dic_check, root)
            self.assertEqual(code, 0)
            self.assertIn("keys that decode to names: 1 of 1", out)
            self.assertIn("M_D_01 = 'Blitz'", out)
            self.assertIn("'us': 1", out)
            self.assertIn("keeps every old text: 1 of 1", out)
            code, out = run(names_check, root)
            self.assertEqual(code, 0, out)
            self.assertIn("EXPR rebuilt byte-identical: 1 of 1", out)


def i32(v):
    return val(0x02, struct.pack("<i", v))


def unit_game(root):
    """Three US armour units: Stuart 301, Sherman 302, and Easy Eight, an upgrade of the Sherman, also at 302."""
    def unit(did, debug, slot, *extra):
        return (0, [(0, i32(did)), (1, val(0x07, struct.pack("<I", debug))), (2, i32(10)), (3, i32(slot)),
                    (4, i32(0)), *extra])
    ndf = make_ndf(objects=[unit(187, 0, 302), unit(186, 1, 301), unit(188, 2, 302, (5, local(0)))],
                   classes=["TUniteAuSolDescriptor"],
                   props=[("DescriptorId", 0), ("ClassNameForDebug", 0), ("Factory", 0), ("PositionInMenu", 0),
                          ("TrackingId", 0), ("UpgradeRequire", 0)],
                   strings=["Unit_M4_Sherman", "Unit_M3A1_Stuart", "Unit_Easy_Eight"],
                   exports={0: "Descriptor_Unit_M4_Sherman", 1: "Descriptor_Unit_M3A1_Stuart",
                            2: "Descriptor_Unit_Easy_Eight"}, topo=[0, 1, 2])
    pack_dir = os.path.join(root, "Data", "PC", "190852")
    os.makedirs(pack_dir)
    pack = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])
    with open(os.path.join(pack_dir, "ZZ_GladPatchableWin.dat"), "wb") as f:
        f.write(pack)


class IdentityCheck(unittest.TestCase):
    def test_runs_on_a_fake_game(self):
        with tempfile.TemporaryDirectory() as root:
            unit_game(root)
            code, out = run(identity_check, root, "$/Descriptor_Unit_M4_Sherman")
        self.assertEqual(code, 0, out)
        self.assertIn("ClassNameForDebug        set on    3   refreshed by the build", out)
        self.assertIn("DescriptorId             set on    3   refreshed by the build", out)
        self.assertNotIn("TrackingId  ", out.split("B.")[0])  # all 0: not an id
        self.assertIn("lowest 186, highest 188", out)
        self.assertIn("Descriptor_<debug name>: 3", out)
        self.assertIn("row 3: 01 M3A1_Stuart, 02 M4_Sherman+Easy_Eight", out)
        self.assertIn("shared slot 302: M4_Sherman, Easy_Eight", out)
        self.assertIn("units with UpgradeRequire: 1", out)
        self.assertIn("parents with more than one upgrade: 0", out)
        self.assertIn("gets its own DescriptorId 187 -> 189, ClassNameForDebug 'Unit_M4_Sherman' -> 'Unit_C5_Check', "
                      "PositionInMenu 302 -> 303", out)

    def test_a_missing_source_unit_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            unit_game(root)
            code, out = run(identity_check, root, "$/Descriptor_Unit_Nope")
        self.assertEqual(code, 1)
        self.assertIn("not found", out)


def seven(values=range(7)):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(i32(v) for v in values))


class NationScan(unittest.TestCase):
    def test_runs_on_a_fake_game(self):
        ndf = make_ndf(
            objects=[(0, [(0, i32(1))]), (0, []), (0, [(0, i32(6))]),        # GER, US (not written), JAP units
                     (1, [(1, seven()), (3, i32(0x3F))]),                     # a per-nation list and bit field
                     (2, [(2, seven())])],                                    # 7 weapons: 7 by coincidence
            classes=["TUniteAuSolDescriptor", "TMapNations", "TWeaponSet"],
            props=[("Nationalite", 0), ("SubClusterNationaliteList", 1), ("Weapons", 2),
                   ("BitFieldNationaliteIfNotSkirmish", 1)])
        with tempfile.TemporaryDirectory() as root:
            pack_dir = os.path.join(root, "Data", "PC", "190852")
            os.makedirs(pack_dir)
            with open(os.path.join(pack_dir, "ZZ_GladPatchableWin.dat"), "wb") as f:
                f.write(make_edat([("dir", "gfx\\", [("file", "everything.cpp.gladndfbin", ndf),
                                                     ("file", "everything_debuginfo.cpp.gladndfbin", ndf)])]))
            code, out = run(nation_scan, root)
        self.assertEqual(code, 0, out)
        self.assertIn("NDF files: 1 (skipped 1 debug-info copies)", out)
        self.assertIn("TUniteAuSolDescriptor (3): US 1, GER 1, JAP 1", out)
        self.assertIn("* TMapNations.SubClusterNationaliteList: 1 object(s) in 1 file(s)", out)
        self.assertIn("  TWeaponSet.Weapons: 1 object(s) in 1 file(s)", out)
        self.assertIn("TMapNations.BitFieldNationaliteIfNotSkirmish: 0x3F ×1", out)
        self.assertIn("an 8th entry in 1 named per-nation structure(s) (1 objects, 1 files)", out)
        self.assertIn("Chinese versions of 1 kind(s) of nation-tagged objects; 1 bit field(s)", out)


def loc_hash(name: str) -> str:
    """How a .rmod writes a text key: the 64-bit key's eight bytes in file order, as hex."""
    return name_to_key(name).to_bytes(8, "little").hex()


NDF = "genglad/patchable/gfx/everything.cpp.gladndfbin"
SYNTHETIC_RMOD = {
    "$schema": "ruse-mod/v1", "id": "synthetic", "name": "Synthetic", "version": "1.2.0", "author": "tests",
    "description": "A made-up mod with one of everything.", "game_version": "24087620",
    "patches": [{"dat": "Data/PC/190852/ZZ_GladPatchableWin.dat", "ndf": NDF, "changes": [
        {"action": "patch", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"},
         "set": {"SeuilMort": {"type": "Float32", "value": 250.0},
                 "InitialFlagSet": {"type": "List<UInt32>", "value": [10, 71]}}},
        {"action": "patch", "table": "TAmmunition", "match": {"AmmunitionId": "1120"},
         "set": {"NbTirParSalves": {"type": "Int32", "value": 40}}},
        {"action": "patch", "table": "TIAProfil", "match": {}, "set": {"NbProdIdleInfanterie": {"type": "Int32", "value": 3}}},
        {"action": "patch", "table": "TTunableConstante", "match": {"_index": "0"},
         "set": {"NbAvionsParAeroport": {"type": "Int32", "value": 24}}},
        {"action": "create", "table": "TAmmunition", "local_id": "inst_new", "top_object": True,
         "set": {"AmmunitionId": {"type": "UInt32", "value": 9000}, "Name": {"type": "LocHash", "value": loc_hash("NEWGUN1")},
                 "Icon": {"type": "ObjRef", "value": {"anchor": {"root": ["ClassNameForDebug", "Unit_X"],
                                                                 "steps": [["Weapons", "[0]"], ["Ammunition"]]}}}}},
        {"action": "patch", "table": "TWeapon", "match": {"anchor": {"root": ["ClassNameForDebug", "Unit_X"],
                                                                     "steps": [["Weapons", "[0]"]]}},
         "set": {"Ammunition": {"$ref": "inst_new"}}},
        {"action": "patch", "table": "TIAProfil", "match": {"_index": "77"}, "set": {"NbProdIdleTank": {"type": "Int32", "value": 9}}},
        {"action": "delete_props", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"}, "props": ["SeuilPinned"]},
    ]}],
    "loc_patches": [{"dat": "Data/PC/190852/ZZ_Win.dat", "dic": f"genlocalisation/ww2/localisation/translations/{lang}/baseunite.dic",
                     "entries": [{"key": loc_hash("N_UNI_15"), "value": "Speed bump"},
                                 {"key": loc_hash("NEWGUN1"), "value": "New gun", "add": True}]} for lang in ("us", "fr")],
    "file_patches": [{"dat": "Data/PC/190852/Data_Common.dat", "files": [{"path": "ww2\\videos\\logo\\eugen.webm", "data": "AAAA"}]}],
}


def synthetic_game() -> Game:
    ammo = Inline(Obj("TAmmunition", {"AmmunitionId": num(1120, "uint32"), "NbTirParSalves": num(8)}, origin=("f", 3)))
    return Game(objects={
        "$/GFX/Everything/Descriptor_Unit_X": Obj("TUniteAuSolDescriptor", {
            "ClassNameForDebug": Text("string", "Unit_X"), "SeuilMort": num("100", "float32"),
            "SeuilPinned": num("50", "float32"), "InitialFlagSet": nums([10], "uint32"),
            "Weapons": ListV([Inline(Obj("TWeapon", {"Ammunition": ammo}, origin=("f", 2)))])}, origin=("f", 1)),
        "$/Const": Obj("TTunableConstante", {"NbAvionsParAeroport": num(8)}, origin=("f", 4)),
        "$/IA/A": Obj("TIAProfil", {"NbProdIdleInfanterie": num(0)}, origin=("f", 5)),
        "$/IA/B": Obj("TIAProfil", {"NbProdIdleInfanterie": num(1)}, origin=("f", 6)),
    })


class RmodToMod(unittest.TestCase):
    """A made-up RUSE-Mod-Manager mod becomes a mod of ours that the engine runs (MOD_FORMAT §13)."""

    def convert(self, data, name="Synthetic_V1.rmod"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = os.path.join(tmp.name, name)
        with open(src, "w", encoding="utf-8") as f:
            json.dump(data, f)
        out = os.path.join(tmp.name, "mods")
        with contextlib.redirect_stdout(io.StringIO()) as said:
            rmod_to_mod.main([src, "--out", out])
        self.assertIn(data["id"], said.getvalue())
        return os.path.join(out, data["id"])

    def test_everything_carries_over_and_runs(self):
        folder = self.convert(SYNTHETIC_RMOD)
        info, ops = load_mod(folder)
        self.assertEqual((info.id, info.version), ("synthetic", "1.2.0"))
        rows = {r.key: r for r in info.texts}
        self.assertEqual(rows["game:N_UNI_15"].texts, {"us": "Speed bump"})  # the same text in both languages: one column
        self.assertEqual((rows["synthetic.NEWGUN1"].game_key, rows["synthetic.NEWGUN1"].texts["us"]), ("NEWGUN1", "New gun"))
        r = Engine(synthetic_game()).run([(ModInfo("synthetic"), ops)])
        self.assertEqual([f.message for f in r.errors], [])
        unit = r.game.objects["$/GFX/Everything/Descriptor_Unit_X"]
        self.assertEqual(unit.props["SeuilMort"].value, 250)
        self.assertEqual([(int(n.value), n.kind) for n in unit.props["InitialFlagSet"].items], [(10, "uint32"), (71, "uint32")])
        self.assertNotIn("SeuilPinned", unit.props)
        new = r.game.objects["$/GFX/Everything/New"]  # the created ammunition, named after its local id
        self.assertEqual(unit.props["Weapons"].items[0].obj.props["Ammunition"], Ref("$/GFX/Everything/New"))
        self.assertEqual(new.props["Name"], Text("loc", "synthetic.NEWGUN1"))
        self.assertEqual(new.props["Icon"], Ref("f#3"))  # the old ammunition, now shared under a name of its own
        self.assertEqual(r.game.objects["f#3"].props["NbTirParSalves"].value, 40)  # found by AmmunitionId
        self.assertEqual([r.game.objects[n].props["NbProdIdleInfanterie"].value for n in ("$/IA/A", "$/IA/B")], [3, 3])
        self.assertEqual(r.game.objects["$/Const"].props["NbAvionsParAeroport"].value, 24)
        with open(os.path.join(folder, "mod.toml"), encoding="utf-8") as f:
            manifest = f.read()
        self.assertIn('builds = ["24087620"]', manifest)
        self.assertIn('file         = "Synthetic_V1.rmod"', manifest)
        with open(os.path.join(folder, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        self.assertIn("TIAProfil object #77", readme)  # matched by position: not rebuilt, said so
        self.assertIn("eugen.webm", readme)
        with open(os.path.join(folder, "src", "synthetic.rndf"), encoding="utf-8") as f:
            rndf = f.read()
        self.assertIn("// Not rebuilt (TIAProfil object #77", rndf)
        self.assertIn("//     NbProdIdleTank = 9", rndf)  # the values stay, as comments

    def test_a_flag_recipe_turns_a_whole_list_into_a_list_edit(self):
        data = dict(SYNTHETIC_RMOD, id="all-around-awareness", loc_patches=[], file_patches=[])
        data["patches"] = [{"dat": "x", "ndf": NDF, "changes": [SYNTHETIC_RMOD["patches"][0]["changes"][0]]}]
        folder = self.convert(data, "All_Around_Awareness_V1.rmod")
        info, ops = load_mod(folder)
        r = Engine(synthetic_game()).run([(ModInfo(info.id), ops)])
        flags = r.game.objects["$/GFX/Everything/Descriptor_Unit_X"].props["InitialFlagSet"].items
        self.assertEqual([(int(n.value), n.kind) for n in flags], [(10, "uint32"), (71, "uint32")])
        self.assertEqual([o.kind for o in ops], ["set", "append"])


class VerifyTerrain(unittest.TestCase):
    """The terrain check and the in-game hill test, on a made-up game with one made-up map."""

    def setUp(self):
        from test_build import PACK
        from test_terrain_edit import make_map_pack
        self.tmp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.tmp.name, "R.U.S.E")
        os.makedirs(os.path.join(self.game, "Maps", "PC"))
        os.makedirs(os.path.join(self.game, "Data", "PC", "190852"))
        with open(os.path.join(self.game, "Maps", "PC", "DataMapTest_v09.dat"), "wb") as f:
            f.write(make_map_pack())
        with open(os.path.join(self.game, "Data", "PC", "190852", "ZZ_GladPatchableWin.dat"), "wb") as f:
            f.write(PACK)
        with open(os.path.join(self.game, "RUSE.exe"), "wb") as f:
            f.write(b"MZ")

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_map_is_checked(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify_terrain.main([self.game])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("Test                     OK  hill at (", out.getvalue())
        self.assertIn("1 maps, 0 failures", out.getvalue())

    def add_cliff_map(self):
        from test_terrain_edit import make_map_pack
        with open(os.path.join(self.game, "Maps", "PC", "DataMapCliff_v09.dat"), "wb") as f:
            f.write(make_map_pack(cliff=True))

    def test_a_cliff_in_the_close_up_mesh_is_no_mismatch(self):
        # the close-up mesh holds two points at one x, y (a cliff's top and foot, the foot last); the gameplay ground
        # sits on the top, so it matches that point, not the last one at that x, y
        self.add_cliff_map()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify_terrain.main([self.game, "--only", "Cliff"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("Cliff                    OK  hill at (", out.getvalue())

    def test_a_ground_point_off_the_close_up_mesh_is_still_caught(self):
        from rusemod.kdt import Kdt
        from rusemod.terrain_edit import FILES
        self.add_cliff_map()
        real = verify_terrain.edit_map

        def skewed(read, strokes, name):   # the hill, then one gameplay-ground point one step higher
            changed, notes = real(read, strokes, name)
            ground = Kdt(changed[FILES["ground"]])
            pos = ground.positions(1)
            x, y, z = pos[121 + 60]         # the centre point of the centre cell, under the hill
            pos[121 + 60] = (x, y, z + 1)
            ground.set_positions(1, pos)
            changed[FILES["ground"]] = ground.to_bytes()
            return changed, notes

        out = io.StringIO()
        verify_terrain.edit_map = skewed
        try:
            with contextlib.redirect_stdout(out):
                code = verify_terrain.main([self.game, "--only", "Cliff"])
        finally:
            verify_terrain.edit_map = real
        self.assertEqual(code, 1, out.getvalue())
        self.assertIn("Cliff                    FAIL: 1 gameplay-ground point(s) differ from the close-up mesh",
                      out.getvalue())

    def test_the_hill_test_makes_a_modded_copy(self):
        copy = os.path.join(self.tmp.name, "hill")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify_terrain.main([self.game, "--make-test", "Test", copy, "--radius", "500"])
        self.assertEqual(code, 0, out.getvalue())
        text = out.getvalue()
        self.assertIn("terrain: Test, from hill-test", text)
        self.assertIn("with a radius of 500 units", text)
        with open(os.path.join(copy, "Maps", "PC", "DataMapTest_v09.dat"), "rb") as f, \
                open(os.path.join(self.game, "Maps", "PC", "DataMapTest_v09.dat"), "rb") as g:
            self.assertNotEqual(f.read(), g.read())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_terrain.main([self.game, "--make-test", "Nope", copy]), 2)


if __name__ == "__main__":
    unittest.main()
