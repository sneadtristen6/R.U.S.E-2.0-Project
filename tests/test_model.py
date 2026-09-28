"""The bridge between game data files and the rules engine: load, run mods, write back (made-up data)."""
import struct
import unittest
from decimal import Decimal

from fixtures import make_ndf, val
from rusemod import Ndf
from rusemod.dic import name_to_key
from rusemod.model import ModelError, load, save
from rusemod.patch import Engine, Inline, Ref
from rusemod.resolve import ModInfo
from rusemod.rndf import parse

UNITS = "genglad/patchable/gfx/everything.cpp.gladndfbin"
OTHER = "genglad/patchable/other.cpp.gladndfbin"


def i32(v):
    return val(0x02, struct.pack("<i", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def ints(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(i32(v) for v in values))


def local(i):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, 0))


def imported(k):
    return val(0x09, struct.pack("<II", 0xAAAAAAAA, k))


CLASSES = ["TUniteAuSolDescriptor", "TWeapon", "TAmmunition"]
PROPS = [("ProductionPrice", 0), ("Speed", 0), ("Weapon", 0), ("Ammo", 1), ("Puissance", 2), ("Flag", 0),
         ("Name", 0), ("Show", 0), ("Title", 0)]
# #0 Unit A: price, speed, own weapon #1 (inline), odd bool, key, an import; #1 weapon -> shared ammo #2
# #2 ammo (used by #1 and #4: shared); #3 Unit B; #4 weapon of B (inline) -> #2
OBJECTS = [
    (0, [(0, ints([100] * 5)), (1, f32(1.5)), (2, local(1)), (5, val(0x00, b"\x4e")),
         (6, val(0x1D, struct.pack("<Q", name_to_key("M_D_01")))), (7, imported(0))]),
    (1, [(3, local(2))]),
    (2, [(4, i32(40))]),
    (0, [(0, ints([50] * 5)), (2, local(4)), (8, val(0x07, struct.pack("<I", 0)))]),
    (1, [(3, local(2))]),
]
FILES = {
    UNITS: make_ndf(objects=OBJECTS, classes=CLASSES, props=PROPS, strings=["Old title"],
                    exports={0: "A", 3: "B"}, imports=["VersionOption/ShowOfficialMap"], compress=True),
}


def build(text, files=FILES):
    base, loaded = load(files)
    result = Engine(base).run([(ModInfo("m"), parse(text, file="m.rndf", mod="m"))])
    return base, loaded, result


def reread(out, path=UNITS):
    return Ndf(out[path])


class Loading(unittest.TestCase):
    def test_model_shape(self):
        game, _ = load(FILES)
        a = game.objects["$/A"]
        self.assertEqual(a.cls, "TUniteAuSolDescriptor")
        self.assertIsInstance(a.props["Weapon"], Inline)                     # used only by A: part of A
        self.assertEqual(a.props["Weapon"].obj.props["Ammo"], Ref(f"{UNITS}#2"))  # used twice: shared
        self.assertEqual(a.props["Show"], Ref("$/VersionOption/ShowOfficialMap"))
        self.assertEqual(game.objects["$/VersionOption/ShowOfficialMap"].cls, "<external>")  # stand-in, not broken
        self.assertEqual(a.props["Name"].value, "M_D_01")

    def test_nothing_changes_without_mods(self):
        base, loaded, result = build("patch $/A ( Speed *= 1 )")
        self.assertEqual(save(base, result.game, loaded), {})

    def test_the_same_name_in_two_files_is_reported_and_kept_apart(self):
        other = make_ndf(objects=[(0, [])], classes=["T"], props=[], exports={0: "A"})
        game, _ = load({**FILES, OTHER: other})
        self.assertEqual(game.objects["$/A"].cls, "TUniteAuSolDescriptor")  # the first file's
        self.assertEqual(game.objects[f"{OTHER}#0"].cls, "T")
        self.assertIn("$/A is named in both", game.notes[0])


class WritingBack(unittest.TestCase):
    def test_value_changes_land_and_everything_else_keeps_its_bytes(self):
        base, loaded, result = build("patch $/A ( ProductionPrice *= 0.5  Speed *= 1.1 )")
        self.assertEqual(result.errors, [])
        out = save(base, result.game, loaded)
        ndf, orig = reread(out), Ndf(FILES[UNITS])
        a = ndf.objects[0]
        self.assertEqual(a.get(0).int_list(), [50] * 5)
        self.assertEqual(a.get(1).payload, struct.pack("<f", 1.5 * 1.1))
        self.assertEqual(a.get(5).payload, b"\x4e")                       # the odd bool kept its raw byte
        for i in (1, 2, 3, 4):
            self.assertEqual([(p, v.encode()) for p, v in ndf.objects[i].props],
                             [(p, v.encode()) for p, v in orig.objects[i].props])
        self.assertTrue(struct.unpack_from("<I", out[UNITS], 12)[0] & 0x80)  # still compressed

    def test_inline_part_and_shared_object(self):
        base, loaded, result = build("patch shared $/A:Weapon.Ammo ( Puissance = 55 )")
        self.assertEqual(result.errors, [])
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual(ndf.objects[2].get(4).scalar(), 55)              # the shared ammo object changed
        self.assertEqual([(p, v.encode()) for p, v in ndf.objects[1].props],
                         [(p, v.encode()) for p, v in Ndf(FILES[UNITS]).objects[1].props])

    def test_texts_and_keys(self):
        base, loaded, result = build("patch $/B ( Title = 'New title' )\npatch $/A ( Name = key(R2MARINE) )")
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual(ndf.strings, ["Old title", "New title"])           # new string appended
        self.assertEqual(ndf.objects[3].get(8).payload, struct.pack("<I", 1))
        self.assertEqual(struct.unpack("<Q", ndf.objects[0].get(6).payload)[0], name_to_key("R2MARINE"))

    def test_references_to_existing_objects(self):
        base, loaded, result = build("patch $/A ( Show = $/B )\npatch $/B ( Title = nil )")
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual(struct.unpack("<III", ndf.objects[0].get(7).payload), (0xBBBBBBBB, 3, 0))
        self.assertEqual(struct.unpack("<III", ndf.objects[3].get(8).payload), (0xBBBBBBBB, 0xFFFFFFFF, 0xFFFFFFFF))

    def test_replacing_an_owned_part_is_reported(self):
        base, loaded, result = build("patch $/B ( Weapon = $/A )")  # B's own weapon part would be left unused
        with self.assertRaisesRegex(ModelError, r"#4 \(TWeapon\) is gone after the mods ran"):
            save(base, result.game, loaded)

    def test_new_objects_are_reported_as_the_next_step(self):
        base, loaded, result = build("export C is clone $/A ( ProductionPrice = [1, 1, 1, 1, 1] )")
        with self.assertRaisesRegex(ModelError, "next step"):
            save(base, result.game, loaded)

    def test_same_property_name_in_two_classes_keeps_each_objects_own_entry(self):
        # PROP has "Cost" twice: entry 0 for class TA, entry 1 for class TB. Changing B's other value must not move
        # its Cost to TA's entry, and setting Cost on an A that lacked it must use TA's entry.
        files = {UNITS: make_ndf(
            objects=[(0, [(0, i32(1))]), (1, [(1, i32(2)), (2, i32(3))]), (0, [])],
            classes=["TA", "TB"], props=[("Cost", 0), ("Cost", 1), ("Other", 1)], exports={0: "A", 1: "B", 2: "A2"})}
        base, loaded, result = build("patch $/B ( Other = 30 )\npatch $/A2 ( Cost = 7 )", files)
        self.assertEqual(result.errors, [])
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual([(pi, v.scalar()) for pi, v in ndf.objects[1].props], [(1, 2), (2, 30)])
        self.assertEqual([(pi, v.scalar()) for pi, v in ndf.objects[2].props], [(0, 7)])

    def test_refs_to_unimported_objects_are_reported(self):
        base, loaded, result = build("patch $/A ( Show = $/Somewhere/Else )")
        self.assertTrue(result.errors)  # the engine already says it's dangling
        self.assertIn("still refers to $/Somewhere/Else", result.errors[0].message)


if __name__ == "__main__":
    unittest.main()
