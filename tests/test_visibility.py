"""Which placed types get a copy drawn from further away, and how its modes widen (rusemod.visibility)."""
import unittest

from rusemod.visibility import needs_copy, widened


class Widening(unittest.TestCase):
    def test_which_types_get_a_copy(self):
        self.assertTrue(needs_copy([1]))          # the Italy and Normandy stones: close only
        self.assertTrue(needs_copy([3, 0x14]))    # close and middle, no far: gone past the middle range
        self.assertFalse(needs_copy([2, 4, 8]))   # a cart: every distance already
        self.assertFalse(needs_copy(None))        # no modes (a single model, a sticker)
        self.assertFalse(needs_copy([]))
        self.assertFalse(needs_copy([4096]))      # drawn by another pass alone (an effect): nothing to widen
        self.assertFalse(needs_copy([128, 256]))
        self.assertTrue(needs_copy([1, 32]))      # a close mode beside another pass's

    def test_close_only_serves_middle_and_far(self):
        self.assertEqual(widened([1]), {0: 1 | 4 | 8})
        self.assertEqual(widened([1, 2]), {0: 13, 1: 14})

    def test_a_middle_mode_serves_far_and_the_close_one_stays(self):
        self.assertEqual(widened([3, 0x14]), {1: 0x14 | 8})
        self.assertEqual(widened([2, 4]), {1: 12})


def _game():
    """Two prop types of one made-up file: Pebble (a close entry written inside it, switched off by a graphics option)
    and Cart (a close entry inside it and a middle one it refers to, shared with Barrow, the map's own)."""
    from decimal import Decimal
    from rusemod.patch import Game, Inline, ListV, Num, Obj, Ref, Text

    def entry(mask, off=False):
        props = {"ModeMask": Num("uint32", Decimal(mask))}
        if off:
            props["GraphicOptionDeactivated"] = Num("bool", Decimal(1))
        return Obj("TSceneryDescriptorMultiModeEntry", props)

    def kind(name, items, at):
        multi = Obj("TSceneryDescriptorMultiMode", {"ModeEntry": ListV(items)})
        return Obj("TSceneryDescriptorMultiState", {"RegistrationName": Text("string", f"TypeWarrior/{name}"),
                                                    "SDFalse": Inline(multi)}, origin=("props.cpp", at))
    shared = entry(4)
    shared.origin = ("props.cpp", 9)
    return Game(objects={
        "props.cpp#9": shared,
        "$/GFX/Everything/Pebble": kind("Pebble", [Inline(entry(1, off=True))], 1),
        "$/GFX/Everything/Cart": kind("Cart", [Inline(entry(2)), Ref("props.cpp#9")], 2),
        "$/GFX/Everything/Barrow": kind("Barrow", [Inline(entry(2)), Ref("props.cpp#9")], 3)})


class TheCopies(unittest.TestCase):
    def run_copies(self, placed):
        from rusemod import visibility as v
        from rusemod.patch import Engine
        from rusemod.resolve import ModInfo
        from rusemod.rndf import parse
        game = _game()
        plan = v.plan(game, placed)
        run = Engine(game).run([(ModInfo("r2-visibility"), parse(v.rndf(game, plan), file="visibility.rndf",
                                                                 mod="r2-visibility"))])
        self.assertEqual([f.message for f in run.findings if f.level == "error"], [])
        return plan, run.game

    def test_an_entry_inside_the_type_widened_in_place(self):
        from rusemod import visibility as v
        plan, after = self.run_copies({"TypeWarrior/Pebble"})
        self.assertEqual(plan, {"TypeWarrior/Pebble": "TypeWarrior/Pebble_R2Seen"})
        (_n, _f, copy), = v.descriptors_named(after, {"TypeWarrior/Pebble_R2Seen"})["TypeWarrior/Pebble_R2Seen"]
        self.assertEqual(v.modes(copy, after.objects), [1 | 4 | 8])
        self.assertNotIn("GraphicOptionDeactivated", v.entries(copy, after.objects)[0][1].props)
        (_n, _f, shipped), = v.descriptors_named(after, {"TypeWarrior/Pebble"})["TypeWarrior/Pebble"]
        self.assertEqual(v.modes(shipped, after.objects), [1])  # the map's own: as shipped

    def test_a_shared_entry_left_alone_and_copied_for_the_far_pass(self):
        """Cart's middle entry is shared with Barrow (the map's own): never changed; the copy gets its own copy of
        it, for the far pass only, at the end of its list."""
        from rusemod import visibility as v
        _plan, after = self.run_copies({"TypeWarrior/Cart"})
        (_n, _f, copy), = v.descriptors_named(after, {"TypeWarrior/Cart_R2Seen"})["TypeWarrior/Cart_R2Seen"]
        self.assertEqual(v.modes(copy, after.objects), [2, 4, 8])
        self.assertEqual(after.objects["props.cpp#9"].props["ModeMask"].value, 4)
        for name in ("Cart", "Barrow"):
            (_n, _f, o), = v.descriptors_named(after, {f"TypeWarrior/{name}"})[f"TypeWarrior/{name}"]
            self.assertEqual(v.modes(o, after.objects), [2, 4])

    def test_an_entry_that_cant_be_read_means_no_copy(self):
        from rusemod import visibility as v
        game = _game()
        del game.objects["props.cpp#9"]
        self.assertEqual(v.plan(game, {"TypeWarrior/Cart"}), {})


class TheBuildGoesByThePlacedTypes(unittest.TestCase):
    def test_solid_buildings_by_their_own_types(self):
        """The steps after the swap to the copies go by the placed types: the game's descriptors (rusemod.scenery
        descriptors) list a copy under its own name only, so a copied building found by its copy's name wasn't
        solid to units."""
        import re
        from pathlib import Path
        src = (Path(__file__).resolve().parents[1] / "src/rusemod/build.py").read_text(encoding="utf-8")
        call = re.search(r"solid_blocks\(game, \[o for o in (\w+) ", src)
        self.assertIsNotNone(call)
        self.assertEqual(call.group(1), "as_placed")
        self.assertLess(src.index("as_placed = objects"), src.index("objects = [_replace(o, type=seen[o.type])"))


if __name__ == "__main__":
    unittest.main()
