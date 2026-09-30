"""The mod rules engine: every row of the conflict table (MOD_FORMAT §10.4), numbers, clones, shared objects,
`patch every`, the final pass, `when mod`, lists, deletes and history. Made-up data, no game files needed."""
import struct
import unittest
from decimal import Decimal

from rusemod.patch import Engine, Game, Inline, ListV, MapV, Obj, Op, Ref, Text, num, nums
from rusemod.resolve import ModInfo


def base():
    ammo_user = lambda: ListV([Inline(Obj("TWeapon", {"Ammunition": Ref("#ammo")}))])  # noqa: E731
    return Game(objects={
        "$/B": Obj("TBatimentDescriptor", {"ProductionPrice": nums([105] * 5), "ProductionTime": num(30)}),
        "$/MG": Obj("TUniteAuSolDescriptor", {"ProductionPrice": nums([20] * 5), "Weapons": ammo_user(),
                                              "Speed": num("1.5", "float32")}),
        "$/Tank": Obj("TUniteAuSolDescriptor", {"Weapons": ammo_user()}),
        "#ammo": Obj("TAmmunition", {"Puissance": num(100)}),
        "$/Menu": Obj("TMenu", {"Units": ListV([Ref("$/MG"), Ref("$/Tank")])}),
    }, files={"gfx/icon.tgv": b"old"})


def run(*mods, game=None):
    """mods: (mod id, [Op]) in load order."""
    packed = []
    for mid, ops in mods:
        for o in ops:
            o.mod = o.mod or mid
        packed.append((ModInfo(mid), ops))
    return Engine(game or base()).run(packed)


def levels(result):
    return [f.level for f in result.findings]


def price(result, name="$/B"):
    return [int(n.value) for n in result.game.objects[name].props["ProductionPrice"].items]


class Numbers(unittest.TestCase):
    def test_worked_example_order_changes_the_result(self):
        half = lambda: ("econ-half", [Op("mul", "$/B", "ProductionPrice", Decimal("0.5"))])  # noqa: E731
        plus = lambda: ("hardcore", [Op("add", "$/B", "ProductionPrice", 5)])  # noqa: E731
        self.assertEqual(price(run(half(), plus()))[0], 58)  # 105 x 0.5 + 5 = 57.5 -> 58
        self.assertEqual(price(run(plus(), half()))[0], 55)  # (105 + 5) x 0.5 = 55

    def test_rounds_once_half_away_from_zero(self):
        r = run(("m", [Op("set", "$/B", "ProductionTime", num("52.5"))]))
        self.assertEqual(r.game.objects["$/B"].props["ProductionTime"].value, 53)
        r = run(("m", [Op("set", "$/B", "ProductionTime", num("-2.5"))]))
        self.assertEqual(r.game.objects["$/B"].props["ProductionTime"].value, -3)

    def test_rounding_happens_once_at_the_end(self):
        # 5 x 0.5 = 2.5, x 0.5 = 1.25 -> 1. Rounding after each step would give 3 x 0.5 = 1.5 -> 2.
        r = run(("a", [Op("set", "$/B", "ProductionTime", num(5))]), ("b", [Op("mul", "$/B", "ProductionTime", "0.5")]),
                ("c", [Op("mul", "$/B", "ProductionTime", "0.5")]))
        self.assertEqual(r.game.objects["$/B"].props["ProductionTime"].value, 1)

    def test_float32_ends_on_the_nearest_float32(self):
        r = run(("m", [Op("mul", "$/MG", "Speed", "1.1")]))
        got = float(r.game.objects["$/MG"].props["Speed"].value)
        self.assertEqual(got, struct.unpack("<f", struct.pack("<f", 1.5 * 1.1))[0])

    def test_value_too_big_for_its_type_is_an_error(self):
        r = run(("m", [Op("mul", "$/B", "ProductionTime", 10 ** 9)]))
        self.assertIn("doesn't fit in int32", r.errors[0].message)

    def test_literal_takes_the_property_type(self):
        r = run(("m", [Op("set", "$/MG", "Speed", num(2))]))  # an int literal on a float32 property
        self.assertEqual(r.game.objects["$/MG"].props["Speed"].kind, "float32")


class ConflictTable(unittest.TestCase):
    """Mod A loads before mod B; both touch the same thing (MOD_FORMAT §10.4)."""

    def pair(self, a_ops, b_ops):
        return run(("a", a_ops), ("b", b_ops))

    def test_set_then_set_warns_unless_equal(self):
        self.assertEqual(levels(self.pair([Op("set", "$/B", "ProductionTime", num(10))],
                                          [Op("set", "$/B", "ProductionTime", num(20))])), ["warning"])
        self.assertEqual(levels(self.pair([Op("set", "$/B", "ProductionTime", num(10))],
                                          [Op("set", "$/B", "ProductionTime", num(10))])), [])

    def test_set_then_math_is_a_note(self):
        r = self.pair([Op("set", "$/B", "ProductionTime", num(10))], [Op("mul", "$/B", "ProductionTime", 2)])
        self.assertEqual(levels(r), ["note"])
        self.assertEqual(r.game.objects["$/B"].props["ProductionTime"].value, 20)

    def test_math_then_set_warns(self):
        self.assertEqual(levels(self.pair([Op("mul", "$/B", "ProductionTime", 2)],
                                          [Op("set", "$/B", "ProductionTime", num(1))])), ["warning"])

    def test_math_then_math_is_a_note(self):
        self.assertEqual(levels(self.pair([Op("mul", "$/B", "ProductionTime", 2)],
                                          [Op("add", "$/B", "ProductionTime", 1)])), ["note"])

    def test_delete_property_then_set_warns(self):
        self.assertEqual(levels(self.pair([Op("delprop", "$/B", "ProductionTime")],
                                          [Op("set", "$/B", "ProductionTime", num(5))])), ["warning"])

    def test_delete_property_then_math_is_an_error_naming_a(self):
        r = self.pair([Op("delprop", "$/B", "ProductionTime")], [Op("mul", "$/B", "ProductionTime", 2)])
        self.assertEqual(levels(r), ["error"])
        self.assertIn("a deleted it", r.errors[0].message)

    def test_set_or_math_then_delete_property_warns(self):
        self.assertEqual(levels(self.pair([Op("set", "$/B", "ProductionTime", num(5))],
                                          [Op("delprop", "$/B", "ProductionTime")])), ["warning"])
        self.assertEqual(levels(self.pair([Op("mul", "$/B", "ProductionTime", 2)],
                                          [Op("delprop", "$/B", "ProductionTime")])), ["warning"])

    def test_append_then_append_adds_both_in_order(self):
        r = self.pair([Op("append", "$/Menu", "Units", [Ref("$/B")])], [Op("append", "$/Menu", "Units", [Ref("#ammo")])])
        self.assertEqual(levels(r), [])
        self.assertEqual([x.target for x in r.game.objects["$/Menu"].props["Units"].items],
                         ["$/MG", "$/Tank", "$/B", "#ammo"])

    def test_append_then_remove_same_item_warns(self):
        self.assertEqual(levels(self.pair([Op("append", "$/Menu", "Units", [Ref("$/B")])],
                                          [Op("remove", "$/Menu", "Units", [Ref("$/B")])])), ["warning"])

    def test_remove_then_append_same_item_warns(self):
        self.assertEqual(levels(self.pair([Op("remove", "$/Menu", "Units", [Ref("$/Tank")])],
                                          [Op("append", "$/Menu", "Units", [Ref("$/Tank")])])), ["warning"])

    def test_remove_then_insert_next_to_it_is_an_error_naming_a(self):
        r = self.pair([Op("remove", "$/Menu", "Units", [Ref("$/MG")])],
                      [Op("insert", "$/Menu", "Units", Ref("$/B"), anchor=Ref("$/MG"))])
        self.assertEqual(levels(r), ["error"])
        self.assertIn("a removed it", r.errors[0].message)

    def test_set_whole_list_then_list_edit_is_a_note(self):
        self.assertEqual(levels(self.pair([Op("set", "$/Menu", "Units", ListV([Ref("$/MG")]))],
                                          [Op("append", "$/Menu", "Units", [Ref("$/B")])])), ["note"])

    def test_list_edit_then_set_whole_list_warns(self):
        self.assertEqual(levels(self.pair([Op("append", "$/Menu", "Units", [Ref("$/B")])],
                                          [Op("set", "$/Menu", "Units", ListV([Ref("$/MG")]))])), ["warning"])

    def test_patch_object_then_delete_it_warns(self):
        r = self.pair([Op("set", "$/B", "ProductionTime", num(5))], [Op("delobj", "$/B")])
        self.assertEqual(levels(r), ["warning"])
        self.assertIn("thrown away", r.warnings[0].message)

    def test_delete_object_then_patch_clone_or_refer_is_an_error(self):
        for b_op in [Op("set", "$/B", "ProductionTime", num(5)), Op("clone", "$/B2", source="$/B"),
                     Op("append", "$/Menu", "Units", [Ref("$/B")])]:
            r = self.pair([Op("delobj", "$/B")], [b_op])
            self.assertEqual(levels(r), ["error"], b_op.kind)
            self.assertIn("which a deleted", r.errors[0].message)

    def test_same_name_twice_is_an_error(self):
        r = self.pair([Op("create", "$/New", cls="TUnit")], [Op("create", "$/New", cls="TUnit")])
        self.assertEqual(levels(r), ["error"])
        r = run(("a", [Op("clone", "$/B", source="$/MG")]))
        self.assertIn("the game already has", r.errors[0].message)

    def test_replace_file_twice_warns(self):
        self.assertEqual(levels(self.pair([Op("replacefile", "gfx\\icon.tgv", value=b"a")],
                                          [Op("replacefile", "gfx\\icon.tgv", value=b"b")])), ["warning"])

    def test_override_turns_a_warning_into_a_note(self):
        self.assertEqual(levels(self.pair([Op("set", "$/B", "ProductionTime", num(10))],
                                          [Op("set", "$/B", "ProductionTime", num(20), override=True)])), ["note"])

    def test_the_same_mod_never_conflicts_with_itself(self):
        r = run(("a", [Op("set", "$/B", "ProductionTime", num(10)), Op("set", "$/B", "ProductionTime", num(20))]))
        self.assertEqual(levels(r), [])


class ClonesAndSharing(unittest.TestCase):
    def test_clone_copies_owned_parts_and_keeps_shared_ones(self):
        r = run(("m", [Op("clone", "$/MG2", source="$/MG", body=[Op("set", path="ProductionPrice", value=nums([7] * 5))])]))
        g = r.game.objects
        self.assertEqual(price(r, "$/MG2"), [7] * 5)
        self.assertEqual(price(r, "$/MG"), [20] * 5)
        self.assertIsNot(g["$/MG2"].props["Weapons"].items[0].obj, g["$/MG"].props["Weapons"].items[0].obj)
        self.assertEqual(g["$/MG2"].props["Weapons"].items[0].obj.props["Ammunition"], Ref("#ammo"))

    def test_clone_is_a_copy_of_that_moment(self):
        r = run(("a", [Op("clone", "$/MG2", source="$/MG")]), ("b", [Op("set", "$/MG", "ProductionPrice", nums([1] * 5))]))
        self.assertEqual(price(r, "$/MG2"), [20] * 5)

    def test_editing_a_shared_part_needs_own_or_shared(self):
        r = run(("m", [Op("set", "$/MG", "Weapons[0].Ammunition.Puissance", num(120))]))
        self.assertIn("2 places use", r.errors[0].message)

    def test_shared_changes_it_for_everyone(self):
        r = run(("m", [Op("set", "$/MG", "Weapons[0].Ammunition.Puissance", num(120), share="shared")]))
        self.assertEqual(r.game.objects["#ammo"].props["Puissance"].value, 120)

    def test_own_gives_this_unit_its_own_copy(self):
        r = run(("m", [Op("set", "$/MG", "Weapons[class=TWeapon].Ammunition.Puissance", num(120), share="own")]))
        g = r.game.objects
        mine = g["$/MG"].props["Weapons"].items[0].obj.props["Ammunition"]
        self.assertIsInstance(mine, Inline)
        self.assertEqual(mine.obj.props["Puissance"].value, 120)
        self.assertEqual(g["#ammo"].props["Puissance"].value, 100)

    def test_a_selector_must_match_exactly_one_item(self):
        r = run(("m", [Op("set", "$/MG", "Weapons[class=TNope].Ammunition.Puissance", num(1), share="shared")]))
        self.assertIn("matches 0 items", r.errors[0].message)


class EveryFinalWhen(unittest.TestCase):
    def test_patch_every_skips_objects_without_the_property(self):
        r = run(("m", [Op("mul", path="ProductionPrice", value="0.5", every="TUniteAuSolDescriptor")]))
        self.assertEqual(price(r, "$/MG"), [10] * 5)
        self.assertEqual(levels(r), ["note"])  # $/Tank has no ProductionPrice
        self.assertIn("skipped", r.notes[0].message)

    def test_final_pass_reaches_units_added_by_later_mods(self):
        # "balance" sorts before "units", so it loads first; a brand-new unit from "units" comes later.
        new_unit = lambda: ("units", [Op("create", "$/New", cls="TUniteAuSolDescriptor",  # noqa: E731
                                         body=[Op("set", path="ProductionPrice", value=nums([10] * 5))])])
        plain = ("balance", [Op("mul", path="ProductionPrice", value=2, every="TUniteAuSolDescriptor")])
        final = ("balance", [Op("mul", path="ProductionPrice", value=2, every="TUniteAuSolDescriptor", final=True)])
        self.assertEqual(price(run(plain, new_unit()), "$/New"), [10] * 5)  # balance ran before the unit existed
        self.assertEqual(price(run(final, new_unit()), "$/New"), [20] * 5)  # the final pass reaches it

    def test_final_pass_runs_after_every_normal_operation(self):
        r = run(("a", [Op("mul", "$/B", "ProductionTime", 2, final=True)]), ("b", [Op("set", "$/B", "ProductionTime", num(7))]))
        self.assertEqual(r.game.objects["$/B"].props["ProductionTime"].value, 14)

    def test_when_mod(self):
        compat = lambda neg: ("compat", [Op("set", "$/B", "ProductionTime", num(1), when=[("better-ai", "*", neg)])])  # noqa: E731
        without = run(compat(False))
        self.assertEqual(without.game.objects["$/B"].props["ProductionTime"].value, 30)
        with_it = run(("better-ai", []), compat(False))
        self.assertEqual(with_it.game.objects["$/B"].props["ProductionTime"].value, 1)
        self.assertEqual(run(compat(True)).game.objects["$/B"].props["ProductionTime"].value, 1)


class ListsDeletesHistory(unittest.TestCase):
    def test_reference_already_in_the_list_is_not_added_twice(self):
        r = run(("m", [Op("append", "$/Menu", "Units", [Ref("$/MG")])]))
        self.assertEqual(len(r.game.objects["$/Menu"].props["Units"].items), 2)
        self.assertEqual(levels(r), ["note"])

    def test_remove_with_nothing_to_remove_warns(self):
        self.assertEqual(levels(run(("m", [Op("remove", "$/Menu", "Units", [Ref("$/B")])]))), ["warning"])

    def test_insert_before_after_and_at(self):
        r = run(("m", [Op("insert", "$/Menu", "Units", Ref("$/B"), anchor=Ref("$/Tank"), where="before"),
                       Op("insert", "$/Menu", "Units", Ref("#ammo"), anchor=0, where="at")]))
        self.assertEqual([x.target for x in r.game.objects["$/Menu"].props["Units"].items],
                         ["#ammo", "$/MG", "$/B", "$/Tank"])

    def test_deleting_something_still_referenced_stops_the_build(self):
        r = run(("m", [Op("delobj", "$/Tank")]))
        self.assertEqual(levels(r), ["error"])
        self.assertIn("$/Menu still refers to $/Tank, which m deleted", r.errors[0].message)

    def test_missing_target_suggests_a_rebase(self):
        self.assertIn("rebase", run(("m", [Op("set", "$/Nope", "X", num(1))])).errors[0].message)

    def test_history_shows_the_chain(self):
        r = run(("econ-half", [Op("mul", "$/B", "ProductionPrice", "0.5", file="src/eco.rndf", line=3)]),
                ("hardcore", [Op("add", "$/B", "ProductionPrice", 5, file="src/hard.rndf", line=9)]))
        self.assertEqual(r.history("$/B", "ProductionPrice"), [
            "econ-half (src/eco.rndf:3): mul -> [52.5, 52.5, 52.5, 52.5, 52.5]",
            "hardcore (src/hard.rndf:9): add -> [57.5, 57.5, 57.5, 57.5, 57.5]"])

    def test_files(self):
        self.assertIn("already exists", run(("m", [Op("addfile", "gfx/icon.tgv", value=b"x")])).errors[0].message)
        self.assertIn("isn't a game file", run(("m", [Op("replacefile", "nope.tgv", value=b"x")])).errors[0].message)


def named():
    """Two units with debug names and flag lists; the Sherman's ammo is its own part, the Lee's is shared."""
    def unit(debug, flags, ammo, origin):
        return Obj("TUniteAuSolDescriptor", {
            "ClassNameForDebug": Text("string", debug), "InitialFlagSet": nums(flags, "uint32"),
            "Nationalite": num(1 if debug.endswith("Lee") else 0),
            "Weapons": ListV([Inline(Obj("TWeapon", {"Ammunition": ammo}, origin=("f", origin)))])}, origin=("f", origin - 1))
    own_ammo = Inline(Obj("TAmmunition", {"AmmunitionId": num(1120, "uint32"), "Puissance": num(100)}, origin=("f", 3)))
    return Game(objects={
        "$/Sherman": unit("Unit_M4_Sherman", [10, 24], own_ammo, 2),
        "$/Lee": unit("Unit_M3_Lee", [10], Ref("#ammo"), 5),
        "#ammo": Obj("TAmmunition", {"AmmunitionId": num(1000, "uint32"), "Puissance": num(50)}, origin=("f", 6)),
        "$/Const": Obj("TTunableConstante", {"NbAvionsParAeroport": num(8)}, origin=("f", 7)),
    })


def puissance(result, name="$/Sherman"):
    obj = result.game.objects[name]
    ammo = obj.props["Weapons"].items[0].obj.props["Ammunition"] if "Weapons" in obj.props else None
    ammo = result.game.objects[ammo.target] if isinstance(ammo, Ref) else ammo.obj if ammo else obj
    return int(ammo.props["Puissance"].value)


class FindingObjects(unittest.TestCase):
    """MOD_FORMAT §4: objects found by a property, parts reached by `patch every`, references to parts."""

    def test_patch_every_reaches_unnamed_parts_and_takes_a_filter(self):
        r = run(("m", [Op("set", path="Puissance", value=num(2), every="TAmmunition")]), game=named())
        self.assertEqual((puissance(r), puissance(r, "$/Lee"), levels(r)), (2, 2, []))  # the Sherman's own part too
        r = run(("m", [Op("set", path="Puissance", value=num(2), every="TAmmunition", filter="AmmunitionId=1120")]),
                game=named())
        self.assertEqual((puissance(r), puissance(r, "$/Lee")), (2, 50))
        r = run(("m", [Op("add", path="Nationalite", value=5, every="TUniteAuSolDescriptor",
                          filter="ClassNameForDebug='Unit_M3_Lee'")]), game=named())
        self.assertEqual([int(r.game.objects[n].props["Nationalite"].value) for n in ("$/Sherman", "$/Lee")], [0, 6])

    def test_patch_every_that_finds_nothing_is_an_error(self):
        r = run(("m", [Op("set", path="X", value=num(1), every="TNope")]), game=named())
        self.assertIn("patches every TNope, but none exists in this game build (after a game update", r.errors[0].message)
        r = run(("m", [Op("set", path="X", value=num(1), every="TAmmunition", filter="AmmunitionId=7")]), game=named())
        self.assertIn("every TAmmunition with [AmmunitionId=7], but none exists", r.errors[0].message)

    def test_a_designator_must_find_exactly_one_object(self):
        r = run(("m", [Op("set", "@TAmmunition[AmmunitionId=1120]", "Puissance", num(3)),
                       Op("set", "@[ClassNameForDebug='Unit_M3_Lee']", "Nationalite", num(9)),
                       Op("set", "@TTunableConstante[NbAvionsParAeroport=8]", "NbAvionsParAeroport", num(128))]),
                game=named())
        self.assertEqual(levels(r), [])
        self.assertEqual(puissance(r), 3)
        self.assertEqual(int(r.game.objects["$/Lee"].props["Nationalite"].value), 9)
        self.assertEqual(int(r.game.objects["$/Const"].props["NbAvionsParAeroport"].value), 128)
        r = run(("m", [Op("set", "@[class=TUniteAuSolDescriptor]", "Nationalite", num(1))]), game=named())
        self.assertIn("matches 2 objects ($/Lee, $/Sherman); it must match exactly one", r.errors[0].message)
        r = run(("m", [Op("set", "@TAmmunition[AmmunitionId=1]", "Puissance", num(1))]), game=named())
        self.assertIn("patches TAmmunition with [AmmunitionId=1], which doesn't exist in this game build", r.errors[0].message)

    def test_a_designator_with_a_path_reaches_a_part(self):
        r = run(("m", [Op("set", "@[ClassNameForDebug='Unit_M4_Sherman']", "Weapons[0].Ammunition.Puissance", num(7))]),
                game=named())
        self.assertEqual((levels(r), puissance(r)), ([], 7))

    def test_a_reference_to_a_part_makes_it_a_shared_object(self):
        r = run(("m", [Op("set", "$/Lee", "Weapons[0].Ammunition", Ref("$/Sherman:Weapons[0].Ammunition"))]), game=named())
        self.assertEqual(levels(r), [])
        shared = r.game.objects["f#3"]  # the part keeps its place in the file, under a name of its own
        self.assertEqual(int(shared.props["AmmunitionId"].value), 1120)
        for unit in ("$/Sherman", "$/Lee"):
            self.assertEqual(r.game.objects[unit].props["Weapons"].items[0].obj.props["Ammunition"], Ref("f#3"))
        # the same, found by a property; and a part of a copy can't be referred to (it has no place in a file yet)
        r = run(("m", [Op("set", "$/Lee", "Weapons[0].Ammunition", Ref("@TAmmunition[AmmunitionId=1120]"))]), game=named())
        self.assertEqual(r.game.objects["$/Lee"].props["Weapons"].items[0].obj.props["Ammunition"], Ref("f#3"))
        r = run(("m", [Op("clone", "$/Copy", source="$/Sherman"),
                       Op("set", "$/Lee", "Weapons[0].Ammunition", Ref("$/Copy:Weapons[0].Ammunition"))]), game=named())
        self.assertIn("can't refer to a TAmmunition part that a mod made", r.errors[0].message)

    def test_a_copy_of_a_found_object_or_of_a_part(self):
        r = run(("m", [Op("clone", "$/GFX/Everything/Ammo_New", source="@TAmmunition[AmmunitionId=1120]",
                          body=[Op("set", path="Puissance", value=num(9))]),
                       Op("clone", "$/GFX/Everything/Lee_2", source="@[ClassNameForDebug='Unit_M3_Lee']")]), game=named())
        self.assertEqual(levels(r), ["note", "note"])  # each copy's fresh identity: the ammo's id, the Lee's
        self.assertIn("Ammo_New gets its own AmmunitionId 1120 -> 1121", r.notes[0].message)
        self.assertEqual(int(r.game.objects["$/GFX/Everything/Ammo_New"].props["Puissance"].value), 9)
        self.assertEqual(int(r.game.objects["$/GFX/Everything/Ammo_New"].props["AmmunitionId"].value), 1121)
        self.assertEqual(puissance(r), 100)  # the original part is untouched
        self.assertEqual(r.created["$/GFX/Everything/Ammo_New"].source, "$/Sherman")  # its file: the part's owner's
        self.assertEqual(r.created["$/GFX/Everything/Lee_2"].source, "$/Lee")
        r = run(("m", [Op("clone", "$/GFX/Everything/Ammo_Shared", source="$/Lee:Weapons[0].Ammunition")]), game=named())
        self.assertEqual(int(r.game.objects["$/GFX/Everything/Ammo_Shared"].props["Puissance"].value), 50)  # a copy of #ammo
        self.assertEqual(r.created["$/GFX/Everything/Ammo_Shared"].source, "#ammo")
        r = run(("m", [Op("clone", "$/X", source="$/Lee:Nationalite")]), game=named())
        self.assertIn("clones $/Lee:Nationalite, which isn't an object", r.errors[0].message)

    def test_list_edits_keep_the_lists_number_type_and_add_nothing_twice(self):
        r = run(("m", [Op("append", "$/Sherman", "InitialFlagSet", [num(71), num(10)]),
                       Op("remove", "$/Sherman", "InitialFlagSet", [num(24)]),
                       Op("insert", "$/Sherman", "InitialFlagSet", num(5), anchor=num(10), where="before")]), game=named())
        flags = r.game.objects["$/Sherman"].props["InitialFlagSet"].items
        self.assertEqual([(int(n.value), n.kind) for n in flags], [(5, "uint32"), (10, "uint32"), (71, "uint32")])
        self.assertEqual(levels(r), ["note"])  # 10 was there already
        self.assertIn("10 is already in $/Sherman:InitialFlagSet; not added twice", r.notes[0].message)

    def test_a_part_cannot_be_deleted(self):
        r = run(("m", [Op("delobj", "@TAmmunition[AmmunitionId=1120]")]), game=named())
        self.assertIn("a part of $/Sherman; parts can't be deleted", r.errors[0].message)


if __name__ == "__main__":
    unittest.main()


def gfx():
    """Two units' models, each with a turret whose firing effect sits in a map ("tir" -> a call of an effect), the way
    the game binds a weapon's muzzle flash and sound (FX_Tir_*). The calls are shared, like the game's."""
    def model(tag, call, origin):
        turret = Obj("TGfxDescriptorModeleSousMobile", {"BinderEffets": MapV([(Text("string", "tir"), Ref(call))])},
                     origin=("f", origin + 2))
        return Obj("TUniteAuSolDescriptor", {"GfxDescriptor": Inline(Obj("TGfxDescriptorModele", {
            "SousElements": MapV([(Text("string", "chassis"), Inline(Obj("TGfxDescriptorModeleSousMobile", {}))),
                                  (Text("string", tag), Inline(turret))])}, origin=("f", origin + 1)))},
                   origin=("f", origin))
    return Game(objects={
        "$/Sherman": model("weapon_effet_tag1", "#tir_ap", 0),
        "$/Rifleman": model("weapon_effet_tag1", "#tir_rifle", 10),
        "#tir_ap": Obj("TActionCall", {"Action": Ref("$/FX_Tir_ObusAP_Moyen")}),
        "#tir_rifle": Obj("TActionCall", {"Action": Ref("$/FX_Tir_infanterie_Moyen")}),
        "$/FX_Tir_ObusAP_Moyen": Obj("TActionDescriptor", {}),
        "$/FX_Tir_infanterie_Moyen": Obj("TActionDescriptor", {}),
    })


class MapEntries(unittest.TestCase):
    """A path goes into a map's entry by number: `Map[i].k` is its key, `Map[i].v` its value."""

    def test_a_link_into_a_map_entry_changes_only_that_unit(self):
        link = Ref("$/Sherman:GfxDescriptor.SousElements[1].v.BinderEffets[0].v")
        r = run(("m", [Op("set", "$/Rifleman:GfxDescriptor.SousElements[1].v", "BinderEffets[0].v", link)]), game=gfx())
        self.assertEqual(levels(r), [])
        effect = lambda name: r.game.objects[name].props["GfxDescriptor"].obj.props["SousElements"].pairs[1][1] \
            .obj.props["BinderEffets"].pairs[0]  # noqa: E731
        self.assertEqual(effect("$/Rifleman"), (Text("string", "tir"), Ref("#tir_ap")))
        self.assertEqual(effect("$/Sherman"), (Text("string", "tir"), Ref("#tir_ap")))
        self.assertEqual(r.game.objects["#tir_rifle"].props["Action"], Ref("$/FX_Tir_infanterie_Moyen"))  # untouched

    def test_a_key_can_be_read_and_set_and_a_missing_entry_is_an_error(self):
        r = run(("m", [Op("set", "$/Sherman", "GfxDescriptor.SousElements[0].k", Text("string", "base"))]), game=gfx())
        self.assertEqual(r.game.objects["$/Sherman"].props["GfxDescriptor"].obj.props["SousElements"].pairs[0][0],
                         Text("string", "base"))
        r = run(("m", [Op("set", "$/Sherman", "GfxDescriptor.SousElements[5].v.X", num(1))]), game=gfx())
        self.assertIn("has no entry [5]", r.errors[0].message)
