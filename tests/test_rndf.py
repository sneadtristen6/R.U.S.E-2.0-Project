"""Reading `.rndf` mod files (MOD_FORMAT §5), and mods written as text running through the rules engine."""
import struct
import unittest
import uuid
from decimal import Decimal

from rusemod.patch import Engine, Game, ListV, MapV, Num, Obj, PairV, Raw, Ref, Text, nums
from rusemod.resolve import ModInfo
from rusemod.rndf import RndfError, parse

SPEC_EXAMPLE = """
// Change an existing unit
patch $/GFX/Everything/Descriptor_Unit_M4_Sherman
(
    ProductionPrice = [30, 30, 30, 30, 30]   // set
    VitesseLineaire *= 1.10                   /* multiply */
    SeuilMort += 100                          (* add *)
    delete SeuilPinned
)

// New unit
Descriptor_Unit_R2_US_Marines is clone $/GFX/Everything/Descriptor_Unit_US_Rangers
(
    Name            = loc('r2.unit.us_marines.name')
    ProductionPrice = [15, 15, 15, 15, 15]
    ShowInMenu      = [1, 1, 1, 1, 1]
)

patch $/GFX/Everything/SomeProductionList
(
    Units += [~/Descriptor_Unit_R2_US_Marines]
    Units -= [$/GFX/Everything/Descriptor_Unit_Old]
    Units.insert(after=$/GFX/Everything/Descriptor_Unit_US_Rangers, value=~/Descriptor_Unit_R2_US_Marines)
)

Ammo_R2_Flamethrower is TAmmunition
(
    Puissance      = 120
    PorteeMaximale = 3000
)

patch every TBatimentDescriptor ( ProductionPrice *= 0.9 )
patch own $/GFX/Everything/Descriptor_Unit_M4_Sherman:Weapons[0].Ammunition ( Puissance += 10 )
patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( override ProductionPrice = [25, 25, 25, 25, 25] )
delete $/GFX/Everything/Descriptor_Unit_Unwanted
final patch every TUniteAuSolDescriptor ( SeuilMort *= 1.1 )
when mod better-ai ( patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( ProductionPrice += 5 ) )
"""


def one_value(text):
    return parse(f"patch $/X ( P = {text} )")[0].value


class SpecExample(unittest.TestCase):
    """Every construct in MOD_FORMAT §5's example reads into the right operation."""

    def setUp(self):
        self.ops = parse(SPEC_EXAMPLE, file="src/example.rndf", mod="ruse2-core")

    def test_operation_list(self):
        got = [(o.kind, o.target, o.path) for o in self.ops]
        sherman = "$/GFX/Everything/Descriptor_Unit_M4_Sherman"
        self.assertEqual(got, [
            ("set", sherman, "ProductionPrice"), ("mul", sherman, "VitesseLineaire"),
            ("add", sherman, "SeuilMort"), ("delprop", sherman, "SeuilPinned"),
            ("clone", "$/GFX/Everything/Descriptor_Unit_R2_US_Marines", ""),
            ("append", "$/GFX/Everything/SomeProductionList", "Units"),
            ("remove", "$/GFX/Everything/SomeProductionList", "Units"),
            ("insert", "$/GFX/Everything/SomeProductionList", "Units"),
            ("create", "$/GFX/Everything/Ammo_R2_Flamethrower", ""),
            ("mul", None, "ProductionPrice"),
            ("add", sherman, "Weapons[0].Ammunition.Puissance"),
            ("set", sherman, "ProductionPrice"),
            ("delobj", "$/GFX/Everything/Descriptor_Unit_Unwanted", ""),
            ("mul", None, "SeuilMort"),
            ("add", sherman, "ProductionPrice"),
        ])

    def test_details(self):
        ops = self.ops
        self.assertEqual(ops[1].value, Decimal("1.10"))  # exact decimal, not a float
        self.assertEqual((ops[0].line, ops[0].file, ops[0].mod), (5, "src/example.rndf", "ruse2-core"))
        clone = ops[4]
        self.assertEqual(clone.source, "$/GFX/Everything/Descriptor_Unit_US_Rangers")
        self.assertEqual([b.path for b in clone.body], ["Name", "ProductionPrice", "ShowInMenu"])
        self.assertEqual(clone.body[0].value, Text("loc", "r2.unit.us_marines.name"))
        marines = Ref("$/GFX/Everything/Descriptor_Unit_R2_US_Marines")  # ~/ resolved
        self.assertEqual(ops[5].value, [marines])
        self.assertEqual((ops[7].where, ops[7].anchor, ops[7].value),
                         ("after", Ref("$/GFX/Everything/Descriptor_Unit_US_Rangers"), marines))
        self.assertEqual((ops[8].cls, [b.path for b in ops[8].body]), ("TAmmunition", ["Puissance", "PorteeMaximale"]))
        self.assertEqual(ops[9].every, "TBatimentDescriptor")
        self.assertEqual(ops[10].share, "own")
        self.assertTrue(ops[11].override)
        self.assertTrue(ops[13].final and ops[13].every == "TUniteAuSolDescriptor")
        self.assertEqual(ops[14].when, [("better-ai", "*", False)])


class Values(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(one_value("30"), Num("int32", Decimal(30)))
        self.assertEqual(one_value("-2.5"), Num("float32", Decimal("-2.5")))
        self.assertEqual(one_value("0x1E"), Num("int32", Decimal(30)))
        self.assertEqual(one_value("int16(-3)"), Num("int16", Decimal(-3)))
        self.assertEqual(one_value("f64(0.1)"), Num("float64", Decimal("0.1")))
        self.assertEqual(one_value("true"), Num("bool", Decimal(1)))

    def test_texts_and_references(self):
        self.assertEqual(one_value("'MapDat:\\DataMapTwoIslands_v09.dat'"),
                         Text("string", "MapDat:\\DataMapTwoIslands_v09.dat"))
        self.assertEqual(one_value('wstr("Hello")'), Text("wstr", "Hello"))
        self.assertEqual(one_value("path('GenDatasmap/TwoIslands')"), Text("path", "GenDatasmap/TwoIslands"))
        self.assertEqual(one_value("key(M_D_01)"), Text("key", "M_D_01"))
        self.assertEqual(one_value("$/GFX/Everything/Ammo_75mm"), Ref("$/GFX/Everything/Ammo_75mm"))
        self.assertEqual(one_value("nil"), Ref(None))

    def test_collections(self):
        self.assertEqual(one_value("[1, 2, 3,]"), nums([1, 2, 3]))
        self.assertEqual(one_value("MAP [ ('a', 1), ('b', 2) ]"),
                         MapV([(Text("string", "a"), Num("int32", Decimal(1))),
                               (Text("string", "b"), Num("int32", Decimal(2)))]))
        self.assertEqual(one_value("(1, nil)"), PairV(Num("int32", Decimal(1)), Ref(None)))

    def test_warno_spellings(self):
        self.assertEqual(one_value("Float3[1, 2.5, -3]"), Raw(0x0B, struct.pack("<fff", 1, 2.5, -3)))
        self.assertEqual(one_value("RGBA[255, 128, 0, 255]"), Raw(0x0D, bytes([255, 128, 0, 255])))
        g = uuid.UUID("12345678-1234-5678-9abc-def012345678")
        self.assertEqual(one_value("GUID:{12345678-1234-5678-9abc-def012345678}"), Raw(0x1A, g.bytes_le))

    def test_minus_equals_on_a_number_subtracts(self):
        op = parse("patch $/X ( Price -= 5 )")[0]
        self.assertEqual((op.kind, op.value), ("add", Decimal(-5)))


class Errors(unittest.TestCase):
    def check(self, text, *fragments):
        with self.assertRaises(RndfError) as ctx:
            parse(text, file="m.rndf")
        for f in fragments:
            self.assertIn(f, str(ctx.exception))

    def test_messages_say_where(self):
        self.check("patch $/X\n(\n  Price = [1, 2\n", "m.rndf:4", "expected ',' or ']'")
        self.check("patch $/X ( Price = banana )", "m.rndf:1:21", "unknown value 'banana'")
        self.check("patch $/X ( Price ?= 3 )", "m.rndf:1:19", "can't read")
        self.check("patch $/X ( Units += [~/Nope] )", "~/Nope isn't declared")
        self.check("when mod x ( patch $/X ( P = 1 )", "never closed")
        self.check("A is TX ( P = 1 )\nA is TX ( P = 2 )", "m.rndf:2:1", "declared twice")
        self.check("patch $/X ( P = (1, 2, 3) )", "exactly 2 values")


class TextModsThroughTheEngine(unittest.TestCase):
    """The worked example of MOD_FORMAT §10.7, written as text and run end to end."""

    def game(self):
        return Game(objects={"$/GFX/Everything/B": Obj("TBatimentDescriptor", {"ProductionPrice": nums([105] * 5)})})

    def build(self, *mods):
        packed = [(ModInfo(mid), parse(text, file=f"{mid}.rndf", mod=mid)) for mid, text in mods]
        return Engine(self.game()).run(packed)

    def test_worked_example(self):
        half = ("econ-half", "patch $/GFX/Everything/B ( ProductionPrice *= 0.5 )")
        hard = ("hardcore", "patch $/GFX/Everything/B ( ProductionPrice += 5 )")
        r = self.build(half, hard)
        self.assertEqual(int(r.game.objects["$/GFX/Everything/B"].props["ProductionPrice"].items[0].value), 58)
        self.assertEqual(r.history("$/GFX/Everything/B", "ProductionPrice")[1],
                         "hardcore (hardcore.rndf:1): add -> [57.5, 57.5, 57.5, 57.5, 57.5]")

    def test_clone_and_menu_from_text(self):
        game = self.game()
        game.objects["$/GFX/Everything/Menu"] = Obj("TMenu", {"Units": ListV([Ref("$/GFX/Everything/B")])})
        mod = parse("""
            export B2 is clone $/GFX/Everything/B ( ProductionPrice = [1, 1, 1, 1, 1] )
            patch $/GFX/Everything/Menu ( Units += [~/B2] )
        """, file="u.rndf", mod="units")
        r = Engine(game).run([(ModInfo("units"), mod)])
        self.assertEqual(r.findings, [])
        self.assertEqual([x.target for x in r.game.objects["$/GFX/Everything/Menu"].props["Units"].items],
                         ["$/GFX/Everything/B", "$/GFX/Everything/B2"])


if __name__ == "__main__":
    unittest.main()
