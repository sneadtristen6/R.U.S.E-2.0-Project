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
import names_check  # noqa: E402
import topo_check  # noqa: E402
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


def run(module, root):
    out = io.StringIO()
    old = sys.argv
    sys.argv = ["x", root]
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


if __name__ == "__main__":
    unittest.main()
