"""What the game needs of a unit beyond its data's types (rusemod.unitcheck, rusemod.unitflags.problems): the build's
errors and warnings for ids, nations, price and menu lists, flags and salvos. Made-up units, no game files needed."""
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat
from rusemod.build import build_pack, load_mod
from rusemod.patch import Engine, Game, Inline, ListV, Obj, Op, Ref, Text, num, nums
from rusemod.resolve import ModInfo
from rusemod import unitcheck

TANK, PLANE, C47, PARA, TRUCK, ROCKETS = "$/Tank", "$/Plane", "$/C47", "$/Para", "$/Truck", "$/Rockets"
LAUNCHER = "$/Turret_Rockets"  # a named turret: a mod can put it on another weapon
NEW = "$/New"


def unit(cls, did, flags, nation=1, **extra):
    return Obj(cls, {"DescriptorId": num(did, "uint32"), "Nationalite": num(nation), "Factory": num(8),
                     "InitialFlagSet": nums(flags, "uint32"), "ProductionPrice": nums([10] * 5),
                     "ShowInMenu": nums([1] * 5, "bool"), "ClassNameForDebug": Text("string", f"Unit_{did}"), **extra})


def mounted(salvo):
    return Inline(Obj("TMountedWeaponDescriptor", {"SalveNumber": num(salvo)}))


def weapon(turrets, salves=None):
    props = {"TurretDescriptorList": ListV(turrets)}
    if salves is not None:
        props["Salves"] = nums(salves)
    return Inline(Obj("TWeaponDescriptor", props))


def game():
    """As the game has them: a tank whose gun fires no salvos (no Salves), an aircraft (flag 2), a C-47 dropping
    paratroopers (2 and 59, with the unit it drops), a truck (62), and a rocket launcher whose weapon has salvos and
    whose turret, a named object, fires salvo 1."""
    turret = Inline(Obj("TTurretDescriptor", {"MountedWeaponDescriptorList": ListV([mounted(-1)])}))
    return Game(objects={
        TANK: unit("TUniteAuSolDescriptor", 1000, [10, 24, 43, 55], WeaponDescriptor=weapon([turret])),
        PLANE: unit("TAvionDescriptor", 1200, [2, 10, 24]),
        C47: unit("TAvionDescriptor", 1201, [2, 10, 24, 59], UniteTransportee=Ref(PARA)),
        PARA: unit("TInfanterieDescriptor", 1300, [10, 24, 42, 48]),
        TRUCK: Obj("TTruckDescriptor", {"DescriptorId": num(10, "uint32"), "Nationalite": num(1),
                                        "InitialFlagSet": nums([10, 24, 44, 62], "uint32")}),
        ROCKETS: unit("TUniteAuSolDescriptor", 1400, [10, 24, 43],
                      WeaponDescriptor=weapon([Ref(LAUNCHER)], salves=[2, 6, -1, -1, -1])),
        LAUNCHER: Obj("TTurretDescriptor", {"MountedWeaponDescriptorList": ListV([mounted(1)])}),
    })


def run(*ops, base=None):
    for op in ops:
        op.mod, op.file, op.line = "m", "m.rndf", op.line or 1
    return Engine(base or game()).run([(ModInfo("m"), list(ops))])


def clone(*body, source=TANK):
    return Op("clone", NEW, source=source, body=[Op("set", path=p, value=v) for p, v in body])


def said(result, level="error"):
    return [f.message for f in result.findings if f.level == level]


class TheGameAsShipped(unittest.TestCase):
    def test_nothing_to_say(self):
        r = run()
        self.assertEqual([f for f in r.findings if f.level != "note"], [])
        for name in (TANK, PLANE, C47, PARA, TRUCK, ROCKETS):  # a copy of each is fine too
            with self.subTest(copy_of=name):
                self.assertEqual([f.level for f in run(clone(source=name)).findings if f.level != "note"], [])

    def test_what_it_already_had_isn_t_the_mods_doing(self):
        base = game()
        base.objects[TANK].props["Nationalite"] = num(9)
        base.objects[TANK].props["ProductionPrice"] = nums([10])
        base.objects[PLANE].props["DescriptorId"] = num(1000, "uint32")
        r = run(Op("set", TANK, "SeuilMort", num(5)), Op("set", PLANE, "SeuilMort", num(5)), base=base)
        self.assertEqual(said(r) + said(r, "warning"), [])


class Ids(unittest.TestCase):
    """The game keeps one unit per DescriptorId, across every kind of unit."""

    def test_another_unit_s_id_even_of_another_kind(self):
        r = run(clone(("DescriptorId", num(1200, "uint32"))))
        self.assertEqual(said(r), [f"m (m.rndf:1): {NEW}: DescriptorId 1200 is also {PLANE}'s: the game keeps one "
                                   f"unit per id, so this one is left out of its nation's list and orders for it build "
                                   f"{PLANE}; give it a number no other unit has (a copy gets one by itself when it "
                                   f"doesn't set DescriptorId)"])

    def test_zero(self):
        r = run(clone(("DescriptorId", num(0, "uint32"))))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: DescriptorId 0 isn't an id", said(r)[0])

    def test_a_game_unit_patched_to_another_s_id_is_named_not_the_other(self):
        r = run(Op("set", TANK, "DescriptorId", num(1200, "uint32"), line=4))
        self.assertEqual([m.split(" is also ")[0] for m in said(r)], [f"m (m.rndf:4): {TANK}: DescriptorId 1200"])

    def test_a_unit_made_from_scratch_needs_one(self):
        r = run(Op("create", NEW, cls="TUniteAuSolDescriptor"))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: it has no DescriptorId", said(r)[0])
        r = run(Op("create", NEW, cls="TUniteAuSolDescriptor", body=[Op("set", path="DescriptorId", value=num(7))]))
        self.assertEqual(said(r), [])
        r = run(Op("create", "$/Thing", cls="TSomethingElse"))  # not a unit
        self.assertEqual(said(r), [])

    def test_taking_it_away(self):
        r = run(Op("delprop", TANK, "DescriptorId"))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{TANK}: it has no DescriptorId", said(r)[0])

    def test_copies_get_their_own(self):
        r = run(clone(), Op("clone", "$/New2", source=PLANE))
        self.assertEqual(said(r) + said(r, "warning"), [])
        self.assertEqual(int(r.game.objects["$/New2"].props["DescriptorId"].value), 1402)


class Nations(unittest.TestCase):
    def test_0_to_6(self):
        for n in (7, -1, 100):
            with self.subTest(nation=n):
                r = run(clone(("Nationalite", num(n))))
                self.assertEqual(len(said(r)), 1)
                self.assertTrue(said(r)[0].startswith(f"m (m.rndf:1): {NEW}: Nationalite {n} isn't a nation: it must "
                                                      f"be 0 to 6 (0 US, 1 Germany, 2 UK, 3 France, 4 Italy, 5 USSR, "
                                                      f"6 Japan)"), said(r)[0])
        for n in (0, 6):
            self.assertEqual(said(run(clone(("Nationalite", num(n)))), "error"), [])
        r = run(Op("add", TANK, "Nationalite", 7))
        self.assertIn(f"{TANK}: Nationalite 8 isn't a nation", said(r)[0])


class Lists(unittest.TestCase):
    """ProductionPrice and ShowInMenu have one item per battle date: 5."""

    def test_fewer_or_more_than_5(self):
        cases = {"ProductionPrice": nums([10]), "ShowInMenu": nums([1], "bool")}
        for prop, value in cases.items():
            with self.subTest(prop=prop):
                r = run(clone((prop, value)))
                self.assertEqual(len(said(r)), 1)
                self.assertTrue(said(r)[0].startswith(f"m (m.rndf:1): {NEW}: {prop} has 1 item(s); it needs 5, one "
                                                      f"per battle date ("), said(r)[0])
        r = run(Op("append", TANK, "ProductionPrice", [num(99)]))
        self.assertIn(f"{TANK}: ProductionPrice has 6 item(s)", said(r)[0])
        r = run(Op("set", TANK, "ProductionPrice", num(30)))  # a number where the list was
        self.assertIn(f"{TANK}: ProductionPrice isn't a list", said(r)[0])

    def test_5_items_pass(self):
        r = run(Op("set", TANK, "ProductionPrice", nums([30] * 5)), Op("mul", TANK, "ProductionPrice", "0.5"),
                Op("set", TANK, "ShowInMenu", nums([0, 0, 1, 1, 1])), Op("set", TANK, "ProductionPrice[2]", num(1)))
        self.assertEqual(said(r), [])

    def test_names_the_operation_that_changed_the_list(self):
        r = run(Op("set", TANK, "SeuilMort", num(1), line=2), Op("set", TANK, "ShowInMenu", nums([1, 1]), line=3),
                Op("set", TANK, "SeuilMort", num(2), line=4))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:3): {TANK}: ShowInMenu has 2 item(s)"), said(r))


class Flags(unittest.TestCase):
    def test_59_on_anything_but_an_aircraft_crashes(self):
        r = run(Op("append", TANK, "InitialFlagSet", [num(59)]))
        self.assertEqual(len(said(r)), 1)
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:1): {TANK}: flag 59 (transport_parachutiste) on a unit that "
                                              f"isn't an aircraft crashes R.U.S.E."), said(r))

    def test_59_on_an_aircraft_that_drops_nobody_crashes(self):
        r = run(clone(("UniteTransportee", Ref(None)), source=C47))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: flag 59 (transport_parachutiste) on an aircraft with no UniteTransportee", said(r)[0])
        r = run(Op("append", PLANE, "InitialFlagSet", [num(59)], line=2))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:2): {PLANE}: flag 59"), said(r))
        r = run(Op("set", C47, "UniteTransportee", Ref(None), line=5))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:5): {C47}: flag 59"), said(r))
        r = run(Op("set", C47, "InitialFlagSet", nums([2, 10, 24]), line=6), Op("delprop", C47, "UniteTransportee"))
        self.assertEqual(said(r), [])  # no 59, nothing dropped: fine

    def test_2_belongs_to_aircraft(self):
        r = run(clone(("InitialFlagSet", nums([2, 10, 24, 43], "uint32"))))
        self.assertEqual(said(r), [])
        self.assertEqual(said(r, "warning"), [f"m (m.rndf:1): {NEW}: flag 2 (avion) on a unit that isn't an aircraft "
                                              f"makes the game move and order it like an aircraft; take it off"])
        r = run(Op("remove", PLANE, "InitialFlagSet", [num(2)]))
        self.assertEqual(said(r), [])
        self.assertIn(f"{PLANE}: an aircraft without flag 2 (avion)", said(r, "warning")[0])

    def test_a_truck_without_62(self):
        r = run(Op("remove", TRUCK, "InitialFlagSet", [num(62)]))
        self.assertEqual(said(r), [])
        self.assertIn(f"{TRUCK}: a truck without flag 62 (truck)", said(r, "warning")[0])

    def test_only_0_to_104(self):
        r = run(Op("append", TANK, "InitialFlagSet", [num(105)]))
        self.assertEqual(said(r), [])
        self.assertEqual(said(r, "warning"), [f"m (m.rndf:1): {TANK}: flag 105 is outside 0 to 104, so the game "
                                              f"ignores it; take it off"])
        r = run(Op("append", TANK, "InitialFlagSet", [num(104)]))
        self.assertEqual(said(r) + said(r, "warning"), [])

    def test_override_makes_a_warning_a_note(self):
        op = Op("append", TANK, "InitialFlagSet", [num(105)])
        op.override = True
        self.assertEqual(said(run(op), "warning"), [])


class Salvos(unittest.TestCase):
    """A mounted weapon's SalveNumber (other than -1) is 0 to 4, and its weapon has that salvo (Salves[n] above 0)."""

    def test_a_salvo_turret_on_a_weapon_without_salvos(self):
        r = run(Op("append", TANK, "WeaponDescriptor.TurretDescriptorList", [Ref(LAUNCHER)], line=3))
        self.assertEqual(said(r), [f"m (m.rndf:3): {TANK}:WeaponDescriptor: TurretDescriptorList[1]."
                                   f"MountedWeaponDescriptorList[0] has SalveNumber 1, but the weapon has no Salves: "
                                   f"salvo 1 isn't defined; the game stops at load with a \"Quit game ?\" box. Give the "
                                   f"weapon a Salves list with salvo 1 above 0, or set SalveNumber to -1"])

    def test_the_salvo_taken_away(self):
        r = run(Op("set", ROCKETS, "WeaponDescriptor.Salves[1]", num(0), line=2))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:2): {ROCKETS}:WeaponDescriptor: TurretDescriptorList[0]."
                                              f"MountedWeaponDescriptorList[0] has SalveNumber 1, but Salves[1] is 0"),
                        said(r))
        r = run(Op("set", ROCKETS, "WeaponDescriptor.Salves", nums([2])))
        self.assertIn("but Salves has no item 1", said(r)[0])
        r = run(Op("delprop", ROCKETS, "WeaponDescriptor.Salves"))
        self.assertIn("but the weapon has no Salves", said(r)[0])

    def test_a_salvo_number_out_of_range(self):
        r = run(Op("set", ROCKETS, "WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0]."
                                   "SalveNumber", num(5), line=7))
        self.assertEqual(len(said(r)), 1)
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:7): {ROCKETS}:WeaponDescriptor: TurretDescriptorList[0]."
                                              f"MountedWeaponDescriptorList[0] has SalveNumber 5, which isn't -1 or 0 "
                                              f"to 4"), said(r))

    def test_what_works(self):
        r = run(Op("set", ROCKETS, "WeaponDescriptor.Salves[1]", num(3)),
                Op("set", ROCKETS, "WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0]."
                                   "SalveNumber", num(0)),
                Op("append", TANK, "WeaponDescriptor.TurretDescriptorList",
                   [Inline(Obj("TTurretDescriptor", {"MountedWeaponDescriptorList": ListV([mounted(-1)])}))]),
                clone(source=ROCKETS))
        self.assertEqual(said(r), [])


# --- the build stops ---
def flag_list(values):
    import struct
    return val(0x11, struct.pack("<I", len(values)) + b"".join(val(0x03, struct.pack("<I", v)) for v in values))


UNITS = make_ndf(objects=[(0, [(0, flag_list([10, 55]))])], classes=["TUniteAuSolDescriptor"],
                 props=[("InitialFlagSet", 0)], exports={0: "Stuart"}, compress=True)
PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", UNITS)])])


class TheBuild(unittest.TestCase):
    def build(self, text):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "flags.rndf")
            mod.write_text(text, encoding="utf-8")
            return build_pack(Edat(PACK), [load_mod(mod)])

    def test_an_error_writes_nothing_a_warning_builds(self):
        result = self.build("patch $/Stuart ( InitialFlagSet += [uint32(59)] )\n")
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.changed, {})
        result = self.build("patch $/Stuart ( InitialFlagSet += [uint32(2)] )\n")
        self.assertEqual(result.errors, [])
        self.assertTrue(result.changed)


class Rules(unittest.TestCase):
    def test_the_kinds_of_unit(self):
        self.assertTrue(unitcheck.is_unit(Obj("TBatimentDescriptor")))
        self.assertFalse(unitcheck.is_unit(Obj("TAcknowUnitDescriptor")))  # has a Nationalite, isn't a unit
        base = game()
        base.objects["$/Ack"] = Obj("TAcknowUnitDescriptor", {"Nationalite": num(1)})
        self.assertEqual(said(run(Op("set", "$/Ack", "Nationalite", num(9)), base=base)), [])  # not a unit: not asked


if __name__ == "__main__":
    unittest.main()
