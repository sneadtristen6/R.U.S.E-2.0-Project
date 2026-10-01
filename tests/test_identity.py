"""Fresh identity for copied units (MOD_FORMAT §10.5): their own id, debug name and build-menu slot."""
import struct
import unittest
from pathlib import Path

from fixtures import make_ndf, val
from rusemod import Ndf
from rusemod.build import load_mod
from rusemod.identity import debug_name
from rusemod.model import load, save
from rusemod.patch import Engine, Game, Inline, ListV, Obj, Op, Text, num, nums
from rusemod.resolve import ModInfo
from rusemod.rndf import parse

E = "$/GFX/Everything/"
SHERMAN = E + "Descriptor_Unit_M4_Sherman"
LEE = E + "Descriptor_Unit_M3_Lee"


def unit(did, debug, slot, factory=10, nation=None, **extra):
    props = {"DescriptorId": num(did), "ClassNameForDebug": Text("string", debug), "Factory": num(factory),
             "PositionInMenu": num(slot), "ProductionPrice": nums([30] * 5), **extra}
    if nation is not None:
        props["Nationalite"] = num(nation)
    return Obj("TUniteAuSolDescriptor", props)


def game():
    weapon = Inline(Obj("TWeaponDescriptor", {"DescriptorId": num(999)}))  # ids inside parts count for "highest"
    return Game(objects={
        SHERMAN: unit(187, "Unit_M4_Sherman", 302, Weapons=ListV([weapon])),
        E + "Descriptor_Unit_M3A1_Stuart": unit(186, "Unit_M3A1_Stuart", 301),
        E + "Descriptor_Unit_M24_Chaffee": unit(190, "Unit_M24_Chaffee", 303),
        E + "Descriptor_Unit_PanzerIV": unit(300, "Unit_PanzerIV", 302, nation=1),  # German armor menu
        E + "Descriptor_Unit_M7_Priest": unit(400, "Unit_M7_Priest", 304, factory=13),  # US artillery menu
        E + "Descriptor_Unit_Test": unit(12, "Unit_Test", 101, factory=8),
    })


def run(text, g=None):
    return Engine(g or game()).run([(ModInfo("units"), parse(text, file="u.rndf", mod="units"))])


def props(r, name, *which):
    obj = r.game.objects[name]
    return [getattr(obj.props.get(p), "value", None) for p in which]


FRESH = ("DescriptorId", "ClassNameForDebug", "PositionInMenu")


class FreshIdentity(unittest.TestCase):
    def test_a_clone_gets_its_own_id_debug_name_and_slot(self):
        r = run(f"export Descriptor_Unit_R2_Sherman_Test is clone {SHERMAN} ( ProductionPrice = [1, 1, 1, 1, 1] )")
        new = E + "Descriptor_Unit_R2_Sherman_Test"
        # highest id anywhere (999, in a weapon part) + 1; the source's debug-name pattern; after the last unit of
        # row 3 in the US armor menu (the German 302 and the artillery 304 are other menus)
        self.assertEqual(props(r, new, *FRESH), [1000, "Unit_R2_Sherman_Test", 304])
        self.assertEqual(props(r, SHERMAN, *FRESH), [187, "Unit_M4_Sherman", 302])  # the source is untouched
        self.assertEqual([f.level for f in r.findings], ["note"])
        self.assertIn(f"{new} gets its own DescriptorId 187 -> 1000, ClassNameForDebug 'Unit_M4_Sherman' -> "
                      f"'Unit_R2_Sherman_Test', PositionInMenu 302 -> 304", r.findings[0].message)
        self.assertEqual(r.history(new, "PositionInMenu"), ["units (u.rndf:1): fresh identity -> 304"])

    def test_values_the_clone_sets_itself_are_kept(self):
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( DescriptorId = 5000  PositionInMenu = 309 )")
        self.assertEqual(props(r, E + "Descriptor_Unit_X", *FRESH), [5000, "Unit_X", 309])
        self.assertEqual(r.warnings, [])

    def test_a_copied_slot_that_is_free_in_the_new_menu_is_kept(self):
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( Factory = 11 )")  # the empty anti-tank menu
        self.assertEqual(props(r, E + "Descriptor_Unit_X", "PositionInMenu"), [302])
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( Nationalite = 1 )")  # German armor: 302 is taken
        self.assertEqual(props(r, E + "Descriptor_Unit_X", "PositionInMenu"), [303])

    def test_each_clone_gets_the_next_values(self):
        r = run(f"export Descriptor_Unit_A is clone {SHERMAN} ( )\n"
                f"export Descriptor_Unit_B is clone {SHERMAN} ( )\n"
                f"export Descriptor_Unit_C is clone ~/Descriptor_Unit_A ( )")
        got = [props(r, E + n, *FRESH) for n in ("Descriptor_Unit_A", "Descriptor_Unit_B", "Descriptor_Unit_C")]
        self.assertEqual(got, [[1000, "Unit_A", 304], [1001, "Unit_B", 305], [1002, "Unit_C", 306]])
        self.assertEqual(r.warnings, [])

    def test_a_taken_debug_name_gets_a_number(self):
        g = game()
        g.objects[E + "Other"] = unit(1, "Unit_Tank", 900, factory=99)
        r = run(f"export Descriptor_Unit_Tank is clone {SHERMAN} ( )", g)
        self.assertEqual(props(r, E + "Descriptor_Unit_Tank", "ClassNameForDebug"), ["Unit_Tank_2"])

    def test_a_taken_debug_name_set_by_hand_is_kept_with_a_warning(self):
        r = run(f"Clone_Of_Test is clone {E}Descriptor_Unit_Test ( ClassNameForDebug = 'Unit_Test' )")
        self.assertEqual(props(r, E + "Clone_Of_Test", *FRESH), [1000, "Unit_Test", 102])
        self.assertEqual([f.message for f in r.warnings],
                         [f"{E}Clone_Of_Test has ClassNameForDebug 'Unit_Test', the same as {E}Descriptor_Unit_Test"])

    def test_values_the_game_shares_are_not_ids(self):
        g = game()
        for obj in g.objects.values():
            obj.props["TrackingId"] = num(0)  # every unit has the same one: not an id, so copied as is
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( )", g)
        self.assertEqual(props(r, E + "Descriptor_Unit_X", "TrackingId", "DescriptorId"), [0, 1000])
        self.assertEqual(r.warnings, [])

    def test_objects_outside_build_menus_keep_their_slot(self):
        g = game()
        del g.objects[SHERMAN].props["Factory"]
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( )", g)
        self.assertEqual(props(r, E + "Descriptor_Unit_X", "PositionInMenu"), [302])

    def test_a_full_row_falls_back_to_its_first_free_column(self):
        g = game()
        g.objects[E + "Last"] = unit(5, "Unit_Last", 399)
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( )", g)
        self.assertEqual(props(r, E + "Descriptor_Unit_X", "PositionInMenu"), [300])

    def test_clashes_made_later_are_warnings(self):
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( )\n"
                f"patch {E}Descriptor_Unit_M3A1_Stuart ( PositionInMenu = 304 )")
        self.assertEqual(sorted(f.message for f in r.warnings), [
            f"{E}Descriptor_Unit_X has build-menu slot 304, the same as {E}Descriptor_Unit_M3A1_Stuart "
            f"(they overlap in the menu)"])

    def test_a_unit_s_id_taken_later_is_an_error(self):
        # the game keeps one unit per DescriptorId (rusemod.unitcheck): no longer a warning, and only once
        r = run(f"export Descriptor_Unit_X is clone {SHERMAN} ( )\n"
                f"patch ~/Descriptor_Unit_X ( DescriptorId = 187 )")
        self.assertEqual(r.warnings, [])
        self.assertEqual(len(r.errors), 1)
        self.assertIn(f"{E}Descriptor_Unit_X: DescriptorId 187 is also {SHERMAN}'s", r.errors[0].message)

    def test_new_objects_from_scratch_are_left_as_written(self):
        r = Engine(game()).run([(ModInfo("m"), [Op("create", E + "New", cls="TUniteAuSolDescriptor",
                                                   body=[Op("set", path="DescriptorId", value=num(7))], mod="m")])])
        self.assertEqual(props(r, E + "New", "DescriptorId"), [7])
        self.assertEqual(r.findings, [])

    def test_debug_name_pattern(self):
        self.assertEqual(debug_name("$/A/Descriptor_Unit_X", "Unit_X", "$/A/Descriptor_Unit_Y"), "Unit_Y")
        self.assertEqual(debug_name("$/A/Descriptor_Unit_X", "Sherman", "$/A/Descriptor_Unit_Y"), "Descriptor_Unit_Y")
        self.assertEqual(debug_name("$/A/Descriptor_Unit_X", "Unit_X", "$/A/MyTank"), "MyTank")
        self.assertEqual(debug_name("$/A/Descriptor_Unit_X", "Descriptor_Unit_X", "$/A/MyTank"), "MyTank")


class ExampleMod(unittest.TestCase):
    def test_the_c5_example_does_what_it_says(self):
        info, ops = load_mod(Path(__file__).resolve().parent.parent / "examples" / "cloned-unit")
        g = game()
        g.objects[LEE] = unit(188, "Unit_M3_Lee", 304)  # C5 copies the Lee (the Sherman is an upgrade of it)
        r = Engine(g).run([(info, ops)])
        self.assertEqual(r.errors + r.warnings, [])
        new = E + "Descriptor_Unit_R2_Lee_Test"
        self.assertEqual(props(r, new, *FRESH), [1000, "Unit_R2_Lee_Test", 305])
        self.assertEqual([int(n.value) for n in r.game.objects[new].props["ProductionPrice"].items], [1] * 5)
        self.assertEqual([int(n.value) for n in r.game.objects[LEE].props["ProductionPrice"].items], [30] * 5)


class InTheDataFile(unittest.TestCase):
    """The fresh values reach the rebuilt NDF file."""

    def test_clone_written_with_fresh_values(self):
        i32 = lambda v: val(0x02, struct.pack("<i", v))  # noqa: E731
        raw = make_ndf(objects=[(0, [(0, i32(187)), (1, val(0x07, struct.pack("<I", 0))), (2, i32(10)),
                                     (3, i32(302))])],
                       classes=["TUniteAuSolDescriptor"],
                       props=[("DescriptorId", 0), ("ClassNameForDebug", 0), ("Factory", 0), ("PositionInMenu", 0)],
                       strings=["Unit_M4_Sherman"], exports={0: "Descriptor_Unit_M4_Sherman"}, topo=[0])
        path = "genglad/patchable/gfx/everything.cpp.gladndfbin"
        base, loaded = load({path: raw})
        r = Engine(base).run([(ModInfo("m"), parse("export Descriptor_Unit_R2 is clone $/Descriptor_Unit_M4_Sherman ( )",
                                                    file="m.rndf", mod="m"))])
        out = save(base, r.game, loaded, r.created)
        ndf = Ndf(out[path])
        new = ndf.objects[1]
        self.assertEqual(ndf.exports[1], "$/Descriptor_Unit_R2")
        self.assertEqual([new.get(0).scalar(), ndf.strings[struct.unpack("<I", new.get(1).payload)[0]],
                          new.get(2).scalar(), new.get(3).scalar()], [188, "Unit_R2", 10, 303])
        self.assertEqual(ndf.topo, [0, 1])


if __name__ == "__main__":
    unittest.main()
