"""NDF reading, value editing and writing, on small made-up files (no game files needed)."""
import struct
import unittest

from fixtures import make_ndf, val
from rusemod import Ndf
from rusemod.ndf import iter_values, local_ref, sub_values


def i32(v):
    return val(0x02, struct.pack("<i", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def boolean(raw_byte):
    return val(0x00, bytes([raw_byte]))


def int_list(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(i32(v) for v in values))


def ref(i):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, 0))


CLASSES = ["TBatimentDescriptor", "TWeapon"]
PROPS = [("ProductionPrice", 0), ("ProductionTime", 0), ("Speed", 0), ("ShowInMenu", 0), ("Weapons", 0)]
OBJECTS = [
    (0, [(0, int_list([100, 100, 100, 100, 100])), (1, i32(30)), (2, f32(1.5)), (3, boolean(0x4E)),
         (4, val(0x11, struct.pack("<I", 2) + ref(1) + ref(2)))]),
    (1, []),
    (1, []),
]
ARGS = dict(objects=OBJECTS, classes=CLASSES, props=PROPS, exports={0: "Descriptor_Building_Test"})


class Reading(unittest.TestCase):
    def setUp(self):
        self.ndf = Ndf(make_ndf(**ARGS))

    def test_tables(self):
        self.assertEqual(self.ndf.classes, CLASSES)
        self.assertEqual([name for name, _cls in self.ndf.props], [n for n, _ in PROPS])
        self.assertEqual(len(self.ndf.objects), 3)
        self.assertEqual(self.ndf.exports, {0: "$/Descriptor_Building_Test"})

    def test_lookups(self):
        obj = self.ndf.object_by_export("$/Descriptor_Building_Test")
        pi = self.ndf.prop_index("ProductionTime")
        self.assertEqual(obj.get(pi).scalar(), 30)
        self.assertEqual(self.ndf.prop_name(pi), "ProductionTime")
        self.assertIsNone(obj.get(99))

    def test_odd_booleans_are_kept_raw(self):
        obj = self.ndf.objects[0]
        self.assertEqual(obj.get(self.ndf.prop_index("ShowInMenu")).payload, b"\x4e")
        self.assertEqual(self.ndf.to_logical(), self.ndf.data)

    def test_unknown_type_code_is_an_error(self):
        with self.assertRaises(ValueError):
            Ndf(make_ndf(objects=[(0, [(0, val(0x7F, b""))])], classes=["T"], props=[("P", 0)]))

    def test_walking_nested_values_finds_references(self):
        weapons = self.ndf.objects[0].get(self.ndf.prop_index("Weapons"))
        self.assertEqual(len(sub_values(weapons)), 2)
        self.assertEqual([local_ref(v) for v in iter_values(weapons) if local_ref(v) is not None], [1, 2])


class Editing(unittest.TestCase):
    def setUp(self):
        self.ndf = Ndf(make_ndf(**ARGS))
        self.obj = self.ndf.objects[0]

    def reparse(self):
        out = self.ndf.to_logical()
        self.assertEqual(len(out), len(self.ndf.data))  # value edits never change the size
        return Ndf.from_logical(out).objects[0]

    def test_int_and_float_edits(self):
        self.obj.get(self.ndf.prop_index("ProductionTime")).set_scalar(45)
        self.obj.get(self.ndf.prop_index("Speed")).set_scalar(2.25)
        again = self.reparse()
        self.assertEqual(again.get(self.ndf.prop_index("ProductionTime")).scalar(), 45)
        self.assertEqual(again.get(self.ndf.prop_index("Speed")).scalar(), 2.25)

    def test_int_list_edit(self):
        price = self.obj.get(self.ndf.prop_index("ProductionPrice"))
        self.assertEqual(price.int_list(), [100] * 5)
        price.set_int_list([1] * 5)
        self.assertEqual(self.reparse().get(self.ndf.prop_index("ProductionPrice")).int_list(), [1] * 5)

    def test_int_list_edit_must_keep_the_count(self):
        with self.assertRaises(ValueError):
            self.obj.get(self.ndf.prop_index("ProductionPrice")).set_int_list([1, 2])

    def test_scalar_edit_on_a_list_is_refused(self):
        with self.assertRaises(TypeError):
            self.obj.get(self.ndf.prop_index("ProductionPrice")).set_scalar(5)


class Compression(unittest.TestCase):
    def test_compressed_file_reads_to_the_same_content(self):
        plain = Ndf(make_ndf(**ARGS))
        packed = Ndf(make_ndf(compress=True, **ARGS))
        self.assertEqual(packed.data[0x28:], plain.data[0x28:])
        self.assertTrue(struct.unpack_from("<I", packed.data, 12)[0] & 0x80)

    def test_member_output_both_ways(self):
        ndf = Ndf(make_ndf(compress=True, **ARGS))
        self.assertEqual(Ndf(ndf.to_member(compress=True)).data, ndf.data)
        self.assertEqual(ndf.to_member(compress=False), make_ndf(**ARGS))


if __name__ == "__main__":
    unittest.main()
