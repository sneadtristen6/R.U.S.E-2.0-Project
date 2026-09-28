"""Name trees (EXPR/IMPR) and growing an NDF file with new classes, properties, objects and names."""
import struct
import unittest

from fixtures import make_ndf, val
from rusemod import Ndf, names
from rusemod.ndf import Value


def i32(v):
    return val(0x02, struct.pack("<i", v))


BASE = make_ndf(objects=[(0, [(0, i32(1))]), (0, [(0, i32(2))])], classes=["TUnit"], props=[("Price", 0)],
                exports={0: "A", 1: "B"}, imports=["Elsewhere"], topo=[0, 1])


def tree_of(paths):
    trans, root = [], None

    def tran_index(s):
        if s not in trans:
            trans.append(s)
        return trans.index(s)

    for leaf, p in enumerate(paths):
        root = names.add(root, p, leaf, trans, tran_index)
    return root, trans


class Trees(unittest.TestCase):
    def test_shipped_layout_round_trips(self):
        ndf = Ndf(BASE)
        self.assertEqual(names.to_bytes(ndf.expr_tree), ndf._sec("EXPR"))
        self.assertEqual(names.to_bytes(ndf.impr_tree), ndf._sec("IMPR"))

    def test_nested_paths_round_trip(self):
        paths = ["$/GFX/Everything/A", "$/GFX/Everything/B", "$/GFX/Other/C", "$/Top"]
        root, trans = tree_of(paths)
        again = names.parse(names.to_bytes(root))
        self.assertEqual(names.paths(again, trans), dict(enumerate(paths)))

    def test_new_children_keep_name_order_when_there_is_one(self):
        root, trans = tree_of(["$/Alpha", "$/Charlie"])
        root = names.add(root, "$/Bravo", 9, trans, lambda s: trans.append(s) or len(trans) - 1)
        self.assertEqual([trans[c.tran] for c in root.children], ["Alpha", "Bravo", "Charlie"])

    def test_new_children_go_last_when_there_is_no_order(self):
        trans = ["$", "Zulu", "Alpha"]
        root = names.NameNode(0, -1, [names.NameNode(1, 0), names.NameNode(2, 1)])  # out of name order
        root = names.add(root, "$/Bravo", 9, trans, lambda s: trans.append(s) or len(trans) - 1)
        self.assertEqual([trans[c.tran] for c in root.children], ["Zulu", "Alpha", "Bravo"])

    def test_remove_prunes_empty_branches(self):
        root, trans = tree_of(["$/GFX/Everything/A", "$/Top"])
        self.assertTrue(names.remove(root, 0))
        self.assertEqual(names.paths(root, trans), {1: "$/Top"})
        self.assertEqual([trans[c.tran] for c in root.children], ["Top"])

    def test_a_name_can_only_be_used_once(self):
        root, trans = tree_of(["$/A"])
        with self.assertRaises(ValueError):
            names.add(root, "$/A", 5, trans, lambda s: 0)


class GrowingAFile(unittest.TestCase):
    def test_new_class_property_object_name_import_and_topo(self):
        ndf = Ndf(BASE)
        cls = ndf.class_index("TNewThing")
        prop = ndf.add_prop("Power", cls)
        idx = ndf.add_object(cls, [(prop, Value(0x02, struct.pack("<i", 99)))])
        ndf.add_export("$/GFX/Everything/NewThing", idx)
        imp = ndf.import_index("$/Other/File/Thing")
        ndf.set_topo(ndf.topo + [idx])
        again = Ndf.from_logical(ndf.to_logical())
        self.assertEqual(len(again.objects), 3)
        self.assertEqual(struct.unpack("<II", again._sec("CHNK")), (0, 3))
        self.assertEqual(again.classes, ["TUnit", "TNewThing"])
        self.assertEqual(again.props, [("Price", 0), ("Power", 1)])
        self.assertEqual(again.exports[2], "$/GFX/Everything/NewThing")
        self.assertEqual(again.exports[0], "$/A")
        self.assertEqual(again.imports, {0: "$/Elsewhere", imp: "$/Other/File/Thing"})
        self.assertEqual(again.topo, [0, 1, 2])
        self.assertEqual(again.objects[2].get(1).scalar(), 99)
        original = Ndf(BASE)
        for i in (0, 1):  # the existing objects are untouched
            self.assertEqual([(p, v.encode()) for p, v in again.objects[i].props],
                             [(p, v.encode()) for p, v in original.objects[i].props])

    def test_removing_a_name(self):
        ndf = Ndf(BASE)
        ndf.remove_export(1)
        again = Ndf.from_logical(ndf.to_logical())
        self.assertEqual(again.exports, {0: "$/A"})
        self.assertEqual(len(again.objects), 2)  # the object stays (unnamed, unused): indices never shift

    def test_an_untouched_file_writes_back_identical(self):
        ndf = Ndf(BASE)
        self.assertEqual(ndf.to_logical(), ndf.data)


if __name__ == "__main__":
    unittest.main()
