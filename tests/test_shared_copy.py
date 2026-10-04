"""The engine works on a copy of the caller's game that has the game's objects in common with it until one is changed
(patch.shared_copy, Game.own): the caller's game must come out of a build exactly as it went in, because the build
compares the two to write only what changed (model.save) and reads the game as shipped after (build.unit_classes,
build.unit_models). Made-up data, no game files needed."""
import unittest
from decimal import Decimal

from test_unitcheck import HOLLAND, cluster_map, forced, listed, mission
from rusemod import unitcheck
from rusemod.build import fill_loc
from rusemod.model import EXTERNAL
from rusemod.patch import (Engine, Game, Inline, ListV, MapV, Num, Obj, Op, PairV, Ref, Text, _walk_obj, num, nums,
                           shared_copy)
from rusemod.resolve import ModInfo


def snapshot(game, ids=True):
    """Everything in `game` as plain values: each object's class, where it came from and its properties, numbers as
    written (5.0 isn't 5); with `ids`, which object and which value each one is, too."""
    def value(v):
        if isinstance(v, Num):
            return ("num", v.kind, str(v.value))
        if isinstance(v, Inline):
            return ("part", obj(v.obj))
        if isinstance(v, ListV):
            return ("list", [value(x) for x in v.items])
        if isinstance(v, MapV):
            return ("map", [(value(k), value(x)) for k, x in v.pairs])
        if isinstance(v, PairV):
            return ("pair", value(v.a), value(v.b))
        return (type(v).__name__, repr(v))  # Text, Ref, Raw: every field

    def obj(o):
        return (id(o) if ids else None, o.cls, o.origin, o.copied_from,
                [(k, id(x) if ids else None, value(x)) for k, x in o.props.items()])
    return {n: obj(o) for n, o in game.objects.items()}, dict(game.files), list(game.notes)


def weapon(ammo, origin):
    return ListV([Inline(Obj("TWeapon", {"Ammunition": ammo}, origin=("f", origin)))])


def callers_game():
    """Units with flag lists and weapons, one with an ammunition of its own (a part), three sharing one; a model whose
    parts sit in a map; a unit no mod touches holding numbers not yet rounded; one to delete; and what the build
    changes after the engine for units of other nations: cluster maps' loaders, a campaign chapter's, and the
    $/IA/Cluster loaders of skeletons and card pictures (rusemod.unitcheck)."""
    own_ammo = Inline(Obj("TAmmunition", {"AmmunitionId": num(1120, "uint32"), "Puissance": num(100)}, origin=("f", 3)))
    objects = {
        "$/Sherman": Obj("TUniteAuSolDescriptor", {
            "ClassNameForDebug": Text("string", "Unit_M4_Sherman"), "InitialFlagSet": nums([10, 24], "uint32"),
            "Nationalite": num(0), "Weapons": weapon(own_ammo, 2)}, origin=("f", 1)),
        "$/Lee": Obj("TUniteAuSolDescriptor", {
            "ClassNameForDebug": Text("string", "Unit_M3_Lee"), "InitialFlagSet": nums([10], "uint32"),
            "Nationalite": num(0), "Weapons": weapon(Ref("#ammo"), 5)}, origin=("f", 4)),
        "$/Jumbo": Obj("TUniteAuSolDescriptor", {"Weapons": weapon(Ref("#ammo"), 9)}, origin=("f", 8)),
        "$/Grant": Obj("TUniteAuSolDescriptor", {"Weapons": weapon(Ref("#ammo"), 11)}, origin=("f", 10)),
        "#ammo": Obj("TAmmunition", {"AmmunitionId": num(1000, "uint32"), "Puissance": num(50)}, origin=("f", 6)),
        "$/Const": Obj("TTunableConstante", {"NbAvionsParAeroport": num(8), "Title": Text("key", "OLD")},
                       origin=("f", 7)),
        "$/Rifleman": Obj("TUniteAuSolDescriptor", {"GfxDescriptor": Inline(Obj("TGfxDescriptorModele", {
            "SousElements": MapV([(Text("string", "chassis"), Inline(Obj("TGfxDescriptorModeleSousMobile", {},
                                                                         origin=("f", 14)))),
                                  (Text("string", "tag1"), Ref("#tir"))])}, origin=("f", 13)))}, origin=("f", 12)),
        "#tir": Obj("TActionCall", {"Action": Ref("$/FX_Tir")}, origin=("f", 15)),
        "$/FX_Tir": Obj("TActionDescriptor", {}, origin=("f", 16)),
        "$/Old": Obj("TUniteAuSolDescriptor", {"ProductionTime": num("2.5"), "Weight": num("5.0"),
                                               "Speed": num("1.5", "float32"), "Pair": PairV(num(1), Text("string", "a"))},
                     origin=("f", 17)),
        "$/Gone": Obj("TUniteAuSolDescriptor", {"ProductionPrice": nums([5] * 5)}, origin=("f", 18)),
        "$/Cluster": cluster_map(),
        "$/Holland": mission(*HOLLAND),
    }
    for n, tag in enumerate(unitcheck.LOADER_TAGS):
        objects[unitcheck.SKELETONS.format(tag)] = Obj("TClusterLoadResource", {"Packs": ListV([Inline(Obj(
            "TResourceDescriptorMeshPack", {"PackName": Text("path", f"Skeleton_{tag}.spk")}, origin=("c", n)))])},
            origin=("c", 100 + n))
        for c in unitcheck.CARDS:
            objects[c.format(tag)] = Obj("TClusterLoadResource", {"Packs": ListV([Ref(f"$/Menu{tag}Pack")])})
    for obj in list(objects.values()):  # the packs the loaders name: stand-ins, as for objects in files not loaded
        for v in _walk_obj(obj):
            if isinstance(v, Ref) and v.target not in objects:
                objects[v.target] = Obj(EXTERNAL)
    return Game(objects=objects, files={"gfx/icon.tgv": b"old"}, notes=["noticed while loading"])


def ops():
    """Edits units (a value, a list, a list item), changes the ammunition three units share for all of them and gives
    one its own, makes the Sherman's own ammunition a shared object by referring to it, edits a map entry, deletes a
    unit, makes one from scratch and copies another, finds an object by a value an earlier operation set, sets a text
    the build fills in later, and replaces a file."""
    return [
        Op("set", "@TTunableConstante[NbAvionsParAeroport=8]", "NbAvionsParAeroport", num(9)),
        Op("set", "$/Lee", "Weapons[0].Ammunition.Puissance", num(120), share="shared"),
        Op("set", "@TAmmunition[Puissance=120]", "Puissance", num(121)),
        Op("set", path="Puissance", value=num(122), every="TAmmunition", filter="Puissance=121"),
        Op("set", "$/Jumbo", "Weapons[0].Ammunition.Puissance", num(7), share="own"),
        Op("set", "$/Sherman", "Nationalite", num(1)),
        Op("append", "$/Lee", "InitialFlagSet", [num(71)]),
        Op("set", "$/Sherman", "InitialFlagSet[0]", num(11)),
        Op("mul", "$/Sherman", "Weapons[0].Ammunition.Puissance", "1.5"),
        Op("set", "$/Grant", "Weapons[0].Ammunition", Ref("$/Sherman:Weapons[0].Ammunition")),
        Op("set", "$/Jumbo", "Chassis", Ref("$/Rifleman:GfxDescriptor.SousElements[0].v")),  # (a part in a map entry)
        Op("set", "$/Rifleman", "GfxDescriptor.SousElements[0].k", Text("string", "base")),
        Op("set", "$/Rifleman", "GfxDescriptor.SousElements[1].v", Ref("$/FX_Tir")),
        Op("delobj", "$/Gone"),
        Op("create", "$/New", cls="TThing", body=[Op("set", path="Title", value=Text("loc", "r2.new"))]),
        Op("clone", "$/Sherman2", source="$/Sherman", body=[Op("set", path="Nationalite", value=num(3))]),
        Op("set", "$/Const", "Title", Text("loc", "r2.const")),
        Op("replacefile", "gfx/icon.tgv", value=b"new"),
    ]


def build(game):
    """The engine, then what the build changes in its result after (build.build_pack): the loaders for units of other
    nations (unit_models, spawn_models) and the texts (fill_loc)."""
    r = Engine(game).run([(ModInfo("m"), [_mod(op) for op in ops()])])
    assert r.errors == [], [f.message for f in r.errors]
    unitcheck.load_everywhere(r.game, {1})
    unitcheck.load_in_missions(r.game, {3})
    unitcheck.load_with_every_nation(r.game, {1})
    missing = fill_loc(r.game, {"r2.new": "R2NEW", "r2.const": "R2CONST"})
    assert missing == [], missing
    return r


def _mod(op):
    op.mod = "m"
    return op


def puissance(game, name):
    ammo = game.objects[name].props["Weapons"].items[0].obj.props["Ammunition"]
    return (game.objects[ammo.target] if isinstance(ammo, Ref) else ammo.obj).props["Puissance"].value


class TheCallersGame(unittest.TestCase):
    def test_a_build_leaves_it_exactly_as_it_was(self):
        base = callers_game()
        before = snapshot(base)
        r = build(base)
        self.assertEqual(snapshot(base), before)
        # while the build's own copy has every change
        g = r.game.objects
        self.assertEqual(int(g["$/Const"].props["NbAvionsParAeroport"].value), 9)
        self.assertEqual([puissance(r.game, n) for n in ("$/Lee", "$/Jumbo", "$/Sherman", "$/Grant")],
                         [122, 7, 150, 150])
        self.assertIn("f#3", g)  # the Sherman's own ammunition, now a shared object
        self.assertEqual(g["$/Sherman"].props["Weapons"].items[0].obj.props["Ammunition"], Ref("f#3"))
        self.assertIsInstance(base.objects["$/Sherman"].props["Weapons"].items[0].obj.props["Ammunition"], Inline)
        self.assertEqual([int(x.value) for x in g["$/Lee"].props["InitialFlagSet"].items], [10, 71])
        self.assertEqual([int(x.value) for x in g["$/Sherman"].props["InitialFlagSet"].items], [11, 24])
        self.assertEqual(g["$/Rifleman"].props["GfxDescriptor"].obj.props["SousElements"].pairs[0],
                         (Text("string", "base"), Ref("f#14")))
        self.assertEqual((g["$/Jumbo"].props["Chassis"], g["f#14"].cls), (Ref("f#14"), "TGfxDescriptorModeleSousMobile"))
        self.assertIsInstance(base.objects["$/Rifleman"].props["GfxDescriptor"].obj.props["SousElements"].pairs[0][1],
                              Inline)
        self.assertEqual(g["$/Rifleman"].props["GfxDescriptor"].obj.props["SousElements"].pairs[1][1], Ref("$/FX_Tir"))
        self.assertNotIn("$/Gone", g)
        self.assertIn("$/Gone", base.objects)
        self.assertEqual(int(g["$/Sherman2"].props["Nationalite"].value), 3)
        self.assertEqual((g["$/New"].props["Title"], g["$/Const"].props["Title"]),
                         (Text("key", "R2NEW"), Text("key", "R2CONST")))
        self.assertEqual(r.game.files["gfx/icon.tgv"], b"new")
        self.assertEqual(forced(r.game), [num(2, "uint32")] * 3)
        self.assertEqual(forced(base), [None] * 3)
        self.assertEqual(listed(r.game, "$/Holland")[1][-1], "PackMeshSkirmish_FR")
        self.assertEqual(len(r.game.objects[unitcheck.SKELETONS.format("US")].props["Packs"].items), 2)
        self.assertEqual(len(base.objects[unitcheck.SKELETONS.format("US")].props["Packs"].items), 1)
        # numbers are rounded once at the end in every object, the ones no mod touched too: in the copy
        old = g["$/Old"].props
        self.assertEqual([str(old[p].value) for p in ("ProductionTime", "Weight")], ["3", "5"])
        self.assertEqual([str(base.objects["$/Old"].props[p].value) for p in ("ProductionTime", "Weight")],
                         ["2.5", "5.0"])
        # what nothing changed is the caller's own object, not a copy
        self.assertIs(g["$/FX_Tir"], base.objects["$/FX_Tir"])
        self.assertIs(g["#tir"], base.objects["#tir"])

    def test_the_same_build_twice_on_one_game_gives_the_same(self):
        base = callers_game()
        first, second = build(base), build(base)
        self.assertEqual(snapshot(first.game, ids=False), snapshot(second.game, ids=False))
        self.assertEqual(snapshot(first.game, ids=False), snapshot(build(callers_game()).game, ids=False))
        self.assertEqual([f.message for f in first.findings], [f.message for f in second.findings])

    def test_a_find_sees_what_an_earlier_operation_changed(self):
        # the find index is made before the ammunition is copied to be changed: it follows the copy
        r = Engine(callers_game()).run([(ModInfo("m"), [_mod(op) for op in ops()[:4]])])
        self.assertEqual(r.errors, [])
        self.assertEqual(int(r.game.objects["#ammo"].props["Puissance"].value), 122)

    def test_numbers_of_untouched_objects(self):
        # rounded in a copy when rounding changes one, even only in how it's written; an error for one that doesn't fit
        # said once
        g = Game(objects={"$/Big": Obj("T", {"A": num(2 ** 40), "B": num("2.5"), "C": num(2 ** 41)}),
                          "$/Too": Obj("T", {"A": num(2 ** 40)}), "$/Ok": Obj("T", {"A": num(1)}),
                          "$/Float": Obj("T", {"A": num("1.0", "float32")}), "$/NaN": Obj("T", {"A": Num("float32",
                                                                                                  Decimal("NaN"))})})
        before = snapshot(g)
        r = Engine(g).run([])
        self.assertEqual(snapshot(g), before)
        self.assertEqual([f.message for f in r.errors], [f"$/Big: {2 ** 40} doesn't fit in int32",
                                                         f"$/Big: {2 ** 41} doesn't fit in int32",
                                                         f"$/Too: {2 ** 40} doesn't fit in int32"])
        self.assertEqual(r.game.objects["$/Big"].props["B"].value, 3)
        self.assertEqual(str(r.game.objects["$/Float"].props["A"].value), "1")
        self.assertIs(r.game.objects["$/Ok"], g.objects["$/Ok"])
        self.assertIs(r.game.objects["$/Too"], g.objects["$/Too"])
        # a NaN is never equal to itself, so rounding it makes the object count as changed, as before
        self.assertIsNot(r.game.objects["$/NaN"], g.objects["$/NaN"])


class SharedCopy(unittest.TestCase):
    def test_own_copies_once_and_only_what_is_shared(self):
        g = callers_game()
        c = shared_copy(g)
        self.assertIs(c.objects["$/Lee"], g.objects["$/Lee"])
        lee = c.own("$/Lee")
        self.assertIsNot(lee, g.objects["$/Lee"])
        self.assertEqual(lee, g.objects["$/Lee"])
        self.assertIs(c.own("$/Lee"), lee)
        self.assertFalse(c.shares("$/Lee"))
        self.assertTrue(c.shares("$/Sherman"))
        part = c.own_part("$/Cluster", "SubClusterList[1]")
        self.assertIs(part, c.objects["$/Cluster"].props["SubClusterList"].items[1].obj)
        self.assertIsNot(part, g.objects["$/Cluster"].props["SubClusterList"].items[1].obj)
        self.assertEqual(c, g)  # (the same content; which objects are in common isn't compared)
        self.assertIsNot(c.files, g.files)
        self.assertIsNot(c.notes, g.notes)
        c.objects["$/Made"] = Obj("T")  # an object of its own: changed in place
        self.assertIs(c.own("$/Made"), c.objects["$/Made"])
        del c.objects["$/Gone"]  # one deleted, then made again: the new one is its own
        c.objects["$/Gone"] = Obj("T")
        self.assertIs(c.own("$/Gone"), c.objects["$/Gone"])
        self.assertEqual(g.objects["$/Gone"].cls, "TUniteAuSolDescriptor")

    def test_a_game_of_its_own_changes_in_place(self):
        g = callers_game()
        self.assertIs(g.own("$/Lee"), g.objects["$/Lee"])


if __name__ == "__main__":
    unittest.main()
