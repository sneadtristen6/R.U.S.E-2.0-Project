"""The mod rules engine: every row of the conflict table (MOD_FORMAT §10.4), numbers, clones, shared objects,
`patch every`, the final pass, `when mod`, lists, deletes and history. Made-up data, no game files needed."""
import struct
import unittest
from decimal import Decimal

from rusemod.patch import Engine, Game, Inline, ListV, Obj, Op, Ref, num, nums
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


if __name__ == "__main__":
    unittest.main()
