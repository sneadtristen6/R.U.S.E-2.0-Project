"""The read-only check tools, run end to end on a made-up game folder (no game files needed)."""
import contextlib
import io
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
import topo_check  # noqa: E402
import verify_terrain  # noqa: E402
from rusemod import Ndf  # noqa: E402

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
