"""A squad's own number of soldiers and each soldier's own look (rusemod.squads; the squad work's Phases 2-3). The
owner, 2026-11-12: "I would only want to change it for this one squad. Not every squad in the game."; his picks the
same night: at least 2 soldiers, at most 8 for now, a bigger squad spreads out wider as the game does, an added soldier
is a figure only, paratroopers wear each soldier's own look while falling too.

The build (rusemod.build.squad_soldiers): a squad of 7 and one of 3 get R2Behaviour, a copy of the game's one setting
with only the number changed; soldiers with looks of their own get R2SoldierLooks; the copy gets own-squads beside
more-buildings, in the apps' order, and the fingerprint takes each; the refusals in words; a mod from before is built
as before. Nothing here is tried in the game."""
import json
import struct
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from rusemod import build, squads
from rusemod.edat import Edat
from rusemod.patch import Inline, ListV, Num, Ref
from test_animactions import clips_pack

E = "$/GFX/Everything/"
RIFLE = "WW2\\Res3D\\Units\\US\\Infanterie\\US_Soldier_modellod0.Ase2ndfbin"
HEAVY = "WW2\\Res3D\\Units\\US\\Infanterie\\US_Soldier_bazooka_modellod0.Ase2ndfbin"
STAND = "GenAnim_15\\WW2\\Res3D\\Units\\common\\fusilier_standlod0.Baf"
FOLDER = "WW2\\Res3D\\Units\\US\\Infanterie\\"


def unit_data() -> bytes:
    """The made-up game's unit data: the squad (its riflemen, its bazooka man, its fallen soldier, its far-away figure,
    a rifle and a bazooka), the game's one setting for every squad (5 soldiers, their spacing), a squad with three
    charges (NeedModelChange each) and a tank."""
    from fixtures import make_edat, make_ndf, val

    def path(i):
        return val(0x1C, struct.pack("<I", i))

    def text(i):
        return val(0x07, struct.pack("<I", i))

    def ref(index, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))

    def u32(v):
        return val(0x03, struct.pack("<I", v))

    def i32(v):
        return val(0x02, struct.pack("<i", v))

    def f32(v):
        return val(0x05, struct.pack("<f", v))

    def flag(v):
        return val(0x00, bytes([v]))

    def items(*refs):
        return val(0x11, struct.pack("<I", len(refs)) + b"".join(refs))

    def listing(*pairs):
        return val(0x12, struct.pack("<I", len(pairs)) + b"".join(text(k) + ref(o, 2) for k, o in pairs))
    strings = ["t_stand", "b_stand", STAND, RIFLE, HEAVY, "t_tir_secondaire"]
    ndf = make_ndf(objects=[
        (0, [(0, u32(2)), (12, i32(1)), (1, ref(1, 1)), (2, ref(2, 1)), (3, ref(3, 1)), (4, ref(7, 4)),
             (15, ref(11, 7))]),                                                             # 0 the squad
        (1, [(6, ref(5, 3)), (5, listing((0, 4), (1, 4)))]),                                # 1 its riflemen
        (1, [(6, ref(6, 3)), (5, listing((0, 4), (1, 4), (5, 4)))]),                        # 2 its bazooka man
        (1, [(6, ref(5, 3)), (5, listing((0, 4)))]),                                        # 3 its fallen soldier
        (2, [(7, path(2))]),                                                                # 4 stand
        (3, [(8, path(3)), (11, u32(524289))]),                                             # 5 the riflemen's model
        (3, [(8, path(4)), (11, u32(524289))]),                                             # 6 his model
        (4, [(9, ref(8, 5))]),                                                              # 7 its token
        (5, [(10, ref(9, 1))]),                                                             # 8 its pawn
        (1, [(6, ref(6, 3)), (5, listing((0, 4)))]),                                        # 9 its far-away figure
        (6, [(13, u32(5)), (14, f32(500.0))]),                                              # 10 the setting
        (7, [(16, items(ref(12, 8)))]),                                                     # 11 its weapons
        (8, [(17, items(ref(13, 9), ref(14, 9)))]),                                         # 12 its turret
        (9, [(18, ref(15, 10))]),                                                           # 13 a rifle
        (9, [(18, ref(16, 10))]),                                                           # 14 a bazooka
        (10, [(19, flag(0))]),                                                              # 15 rifle ammunition
        (10, [(19, flag(1))]),                                                              # 16 bazooka ammunition
        (0, [(0, u32(3)), (12, i32(1)), (1, ref(18, 1)), (15, ref(19, 7))]),                # 17 three charges
        (1, [(6, ref(5, 3)), (5, listing((0, 4)))]),                                        # 18 its riflemen
        (7, [(16, items(ref(20, 8)))]),                                                     # 19 its weapons
        (8, [(17, items(ref(21, 9), ref(22, 9), ref(23, 9)))]),                             # 20 its turret
        (9, [(18, ref(16, 10))]), (9, [(18, ref(16, 10))]), (9, [(18, ref(16, 10))]),      # 21-23 three charges
        (11, [(20, u32(4)), (22, i32(1))])],                                                # 24 a tank
        classes=["TInfanterieDescriptor", "TGfxDescriptorBiped", "TGfxDescriptorAnimation", "TResourceMultiMaterialMesh",
                 "TGfxDescriptorIcone", "TPawnDescriptor", "TUniteBehaviourDescriptor", "TWeaponDescriptor",
                 "TTurretInfanterieDescriptor", "TMountedWeaponDescriptor", "TAmmunition", "TTankDescriptor"],
        props=[("DescriptorId", 0), ("GfxDescriptorFusilier", 0), ("GfxDescriptorBazooka", 0),
               ("GfxDescriptorIconeCadavre", 0), ("GfxDescriptorIcone", 0), ("ResourceAnimation", 1),
               ("MeshDescriptor", 1), ("FileName", 2), ("FileName", 3), ("PawnDescriptor", 4), ("DescriptorFigurine", 5),
               ("UsefulnessMask", 3), ("Nationalite", 0), ("NbSoldatInGroupeCombat", 6), ("Dispersion", 6),
               ("WeaponDescriptor", 0), ("TurretDescriptorList", 7), ("MountedWeaponDescriptorList", 8),
               ("Ammunition", 9), ("NeedModelChange", 10), ("DescriptorId", 11), ("GfxDescriptor", 11),
               ("Nationalite", 11)],
        strings=strings, exports={0: "GFX/Everything/Descriptor_Unit_Squad", 10: "GFX/Everything/UniteBehaviourDescriptor",
                                  15: "GFX/Everything/Ammo_Rifle", 16: "GFX/Everything/Ammo_Bazooka",
                                  17: "GFX/Everything/Descriptor_Unit_Charges", 24: "GFX/Everything/Descriptor_Unit_Tank"},
        compress=True)
    return make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])


def glb(report: dict, like: str | None) -> bytes:
    """A mod's model file as the build reads it (rusemod.unitmodel.glb_report: its JSON part's asset extras)."""
    extras = {"rusemod_report": report, **({"rusemod_like": like} if like else {})}
    js = json.dumps({"asset": {"version": "2.0", "extras": extras}}).encode()
    js += b" " * (-len(js) % 4)
    return struct.pack("<4sII", b"glTF", 2, 20 + len(js)) + struct.pack("<I4s", len(js), b"JSON") + js


def model_of(node, objects) -> str:
    v = node.props["MeshDescriptor"]
    mesh = v.obj if isinstance(v, Inline) else objects[v.target]
    return mesh.props["FileName"].value


class InTheBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(lambda: self.tmp.cleanup())   # (whichever folder it is by then: a test may start another)

    def mod(self, units: dict, counts: dict | None = None, models: dict | None = None) -> Path:
        """A mod copying the game's units ({its name: the unit it copies}), with squad files {unit: count text} and
        model files {stem: (report, like)}."""
        mod = Path(self.tmp.name, "squads")
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "squads"\nversion = "1.0.0"\n', encoding="utf-8")
        (mod / "src" / "units.rndf").write_text("".join(f"export {u} is clone {E}{s} ( )\n" for u, s in units.items()),
                                                encoding="utf-8")
        files = mod / "files" / "models"
        files.mkdir(parents=True)
        for unit, count in (counts or {}).items():
            (files / f"{unit}.squad.toml").write_text(count, encoding="utf-8")
        for stem, (report, like) in (models or {}).items():
            (files / f"{stem}.glb").write_bytes(glb(report, like))
        return mod

    def build(self, mod):
        arc = Edat(unit_data())
        result = build.build_pack(arc, [build.load_mod(mod)], "0", Edat(clips_pack()))
        loaded = build.load_pack(Edat(arc.to_bytes(result.changed))) if result.changed else None
        return result, arc, loaded

    def test_a_squad_of_7_and_one_of_3(self):
        mod = self.mod({"Descriptor_Unit_Seven": "Descriptor_Unit_Squad", "Descriptor_Unit_Three": "Descriptor_Unit_Squad"},
                       {"Descriptor_Unit_Seven": "count = 7\n", "Descriptor_Unit_Three": "count = 3\n"})
        result, _arc, loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors], [])
        objects = loaded.base.objects
        shared = objects[E + "UniteBehaviourDescriptor"]
        self.assertEqual(shared.props["NbSoldatInGroupeCombat"], Num("uint32", Decimal(5)))   # every other squad: 5
        for unit, n in (("Descriptor_Unit_Seven", 7), ("Descriptor_Unit_Three", 3)):
            with self.subTest(unit=unit):
                own = objects[E + unit].props["R2Behaviour"]
                self.assertIsInstance(own, Inline)          # (its own part: one user, no name of its own)
                self.assertEqual(own.obj.cls, "TUniteBehaviourDescriptor")
                # the game's setting with only the number changed: its kind kept, every other value the same
                self.assertEqual(own.obj.props["NbSoldatInGroupeCombat"], Num("uint32", Decimal(n)))
                self.assertEqual({p: v for p, v in own.obj.props.items() if p != "NbSoldatInGroupeCombat"},
                                 {p: v for p, v in shared.props.items() if p != "NbSoldatInGroupeCombat"})
                self.assertNotIn("R2SoldierLooks", objects[E + unit].props)
        self.assertNotIn("R2Behaviour", objects[E + "Descriptor_Unit_Squad"].props)   # the game's squad: as it was
        self.assertEqual(result.game_patch, ["own-squads"])
        said = " ".join(f.message for f in result.findings)
        self.assertIn("Descriptor_Unit_Seven has 7 soldiers of its own (the game's squads have 5)", said)
        self.assertIn("gets the game patch own-squads for the squads with soldiers of their own "
                      "(Descriptor_Unit_Seven, Descriptor_Unit_Three)", said)

    def test_the_names_are_in_the_file_s_property_table_for_squads_only(self):
        from rusemod.ndf import Ndf
        mod = self.mod({"Descriptor_Unit_Seven": "Descriptor_Unit_Squad"}, {"Descriptor_Unit_Seven": "count = 7\n"},
                       {"Descriptor_Unit_Seven@2": ({"rigged": True}, RIFLE.lower())})
        result, _arc, _loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors], [])
        ndf = Ndf(next(iter(result.changed.values())))
        named = {(n, ndf.classes[c]) for n, c in ndf.props if n.startswith("R2")}
        self.assertEqual(named, {("R2Behaviour", "TInfanterieDescriptor"), ("R2SoldierLooks", "TInfanterieDescriptor")})

    def test_each_soldier_his_own_look_and_the_others_as_they_were(self):
        mod = self.mod({"Descriptor_Unit_Looks": "Descriptor_Unit_Squad"}, {},
                       {"Descriptor_Unit_Looks@1": ({"rigged": True}, RIFLE.lower()),
                        "Descriptor_Unit_Looks@5": ({"rigged": True}, HEAVY.lower())})
        result, _arc, loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors], [])
        objects = loaded.base.objects
        unit = objects[E + "Descriptor_Unit_Looks"]
        looks = unit.props["R2SoldierLooks"]
        self.assertIsInstance(looks, ListV)
        self.assertEqual(len(looks.items), 5)                 # the game's 5: soldier 1 first
        self.assertEqual([type(v).__name__ for v in looks.items], ["Inline", "Ref", "Ref", "Ref", "Inline"])
        self.assertTrue(all(v.target is None for v in looks.items[1:4]))
        first, last = looks.items[0].obj, looks.items[4].obj
        self.assertEqual(model_of(first, objects).lower(), (FOLDER + "Descriptor_Unit_Looks__1lod0.Ase2ndfbin").lower())
        self.assertEqual(model_of(last, objects).lower(), (FOLDER + "Descriptor_Unit_Looks__5lod0.Ase2ndfbin").lower())
        # each a copy of the figure the game gives his place: soldier 1 the riflemen's, the last the bazooka man's
        rifle, heavy = unit.props["GfxDescriptorFusilier"].obj, unit.props["GfxDescriptorBazooka"].obj
        self.assertEqual(first.props["ResourceAnimation"], rifle.props["ResourceAnimation"])
        self.assertEqual(last.props["ResourceAnimation"], heavy.props["ResourceAnimation"])
        # the squad's own figures draw what they drew: the other soldiers are as they were
        self.assertEqual((model_of(rifle, objects), model_of(heavy, objects)), (RIFLE, HEAVY))
        self.assertNotIn("R2Behaviour", unit.props)           # (no number of its own: the game's 5)
        self.assertEqual(result.game_patch, ["own-squads"])
        self.assertEqual(sorted(result.own_models), ["Descriptor_Unit_Looks@1", "Descriptor_Unit_Looks@5"])
        self.assertEqual(result.own_models["Descriptor_Unit_Looks@5"][0], HEAVY.lower())   # written beside his model

    def test_the_far_away_figure_wears_the_look_most_soldiers_wear(self):
        """Counted one soldier at a time, for the model he draws; a tie goes to the look of the lowest-numbered of them
        (soldier 1's when his is one of them)."""
        def far(models: dict, count: str | None = None) -> str:
            mod = self.mod({"Descriptor_Unit_Looks": "Descriptor_Unit_Squad"},
                           {"Descriptor_Unit_Looks": count} if count else {}, models)
            result, _arc, loaded = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.tmp.cleanup()
            self.tmp = tempfile.TemporaryDirectory()
            node = loaded.base.objects[E + "Descriptor_Unit_Looks"]
            for prop in build.FIGURINE:
                v = node.props[prop]
                node = v.obj if isinstance(v, Inline) else loaded.base.objects[v.target]
            return node.props["FileName"].value.rsplit("\\", 1)[-1].lower()
        own = "descriptor_unit_looks__{}lod0.ase2ndfbin".format
        # soldier 5 alone his own: the four riflemen win (the game's squad draws its bazooka man far away)
        self.assertEqual(far({"Descriptor_Unit_Looks@5": ({"rigged": True}, HEAVY.lower())}),
                         "us_soldier_modellod0.ase2ndfbin")
        # soldiers 1, 2 and 3 their own: 1, 1, 1, 1 (soldier 4, a rifleman), 1 (the bazooka man): soldier 1's
        self.assertEqual(far({f"Descriptor_Unit_Looks@{i}": ({"rigged": True}, RIFLE.lower()) for i in (1, 2, 3)}),
                         own(1))
        # soldiers 2 and 3 their own in a squad of 3: 1 (soldier 1, a rifleman), 1, 1: soldier 1's, the game rifleman
        self.assertEqual(far({f"Descriptor_Unit_Looks@{i}": ({"rigged": True}, RIFLE.lower()) for i in (2, 3)},
                             "count = 3\n"), "us_soldier_modellod0.ase2ndfbin")

    def test_the_refusals_in_words(self):
        cases = [("count = 1\n", "Descriptor_Unit_Squad", "would have 1 soldiers: a squad keeps at least 2, the game's own rule"),
                 ("count = 9\n", "Descriptor_Unit_Squad", "would have 9 soldiers: a squad has at most 8 for now"),
                 ("count = 2\n", "Descriptor_Unit_Charges",
                  "would have 2 soldiers, but its last soldiers fire 3 weapons one each (Ammo_Bazooka, Ammo_Bazooka, "
                  "Ammo_Bazooka): it needs at least 3"),
                 ("count = 5\n", "Descriptor_Unit_Tank", "isn't a squad of soldiers, so it can't have soldiers of its own")]
        for count, source, words in cases:
            with self.subTest(count=count, source=source):
                result, _arc, _loaded = self.build(self.mod({"Descriptor_Unit_Mine": source}, {"Descriptor_Unit_Mine": count}))
                self.assertEqual([f.message for f in result.errors], [f"squads: files/models/Descriptor_Unit_Mine.squad.toml: "
                                                                      f"Descriptor_Unit_Mine {words}"])
                self.assertEqual(result.game_patch, [])
                self.tmp.cleanup()
                self.tmp = tempfile.TemporaryDirectory()
        # the three charges' squad with 3: as many as its charges, taken
        result, _arc, _loaded = self.build(self.mod({"Descriptor_Unit_Mine": "Descriptor_Unit_Charges"},
                                                    {"Descriptor_Unit_Mine": "count = 3\n"}))
        self.assertEqual([f.message for f in result.errors], [])

    def test_a_look_for_a_soldier_the_squad_hasn_t_got(self):
        mod = self.mod({"Descriptor_Unit_Looks": "Descriptor_Unit_Squad"}, {"Descriptor_Unit_Looks": "count = 3\n"},
                       {"Descriptor_Unit_Looks@4": ({"rigged": True}, RIFLE.lower())})
        result, _arc, _loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors],
                         ["squads: files/models/Descriptor_Unit_Looks@4.glb: Descriptor_Unit_Looks has 3 soldiers, so "
                          "there is no soldier 4 to wear this look"])

    def test_a_squad_file_that_can_t_be_read_stops_the_build_saying_so(self):
        for text, words in (("count = 'seven'\n", "count must be a whole number of soldiers"), ("count = [\n", "can't be read")):
            with self.subTest(text=text):
                mod = self.mod({"Descriptor_Unit_Mine": "Descriptor_Unit_Squad"}, {"Descriptor_Unit_Mine": text})
                with self.assertRaisesRegex(build.BuildError, words):
                    build.load_mod(mod)
                self.tmp.cleanup()
                self.tmp = tempfile.TemporaryDirectory()

    def test_a_mod_from_before_is_built_as_before(self):
        """A mod with no squad file and no soldier's own look: the step changes nothing (the build's bytes the same with
        it as without it), and the copy gets no game patch for it."""
        mod = self.mod({"Descriptor_Unit_Kinds": "Descriptor_Unit_Squad"}, {},
                       {"Descriptor_Unit_Kinds": ({"rigged": True, "also": []}, RIFLE.lower()),
                        "Descriptor_Unit_Kinds@bazooka": ({"rigged": True, "also": []}, HEAVY.lower())})
        result, _arc, loaded = self.build(mod)
        with mock.patch.object(build, "squad_soldiers", lambda *a, **k: None):
            before, _arc2, _loaded2 = self.build(mod)
        self.assertEqual([f.message for f in result.errors], [])
        self.assertEqual(result.changed, before.changed)
        self.assertEqual(result.game_patch, [])
        self.assertFalse(any(p.startswith("R2") for o in loaded.base.objects.values() for p in o.props))

    def test_the_copy_s_patches_and_its_fingerprint(self):
        # the apps' own order, each once: a copy that had more-buildings and big-packs gets them as before
        self.assertEqual(build.copy_patches(["more-buildings"], True), ["more-buildings", "big-packs"])
        self.assertEqual(build.copy_patches(["own-squads", "more-buildings"], True),
                         ["more-buildings", "big-packs", "own-squads"])
        self.assertEqual(build.copy_patches(["own-squads"], False), ["own-squads"])
        self.assertEqual(build.copy_patches([], False), [])
        # each patch taken in by its name and its file's checksum, as before for one
        import hashlib
        fp = b"x" * 32
        one = build.patches_fingerprint(fp, [("more-buildings", "a" * 64)])
        self.assertEqual(one, hashlib.sha256(fp + b"\ngame patch more-buildings " + b"a" * 64).digest())
        both = build.patches_fingerprint(fp, [("more-buildings", "a" * 64), ("own-squads", "b" * 64)])
        self.assertNotIn(both, (fp, one))
        self.assertNotEqual(both, build.patches_fingerprint(fp, [("more-buildings", "a" * 64), ("own-squads", "c" * 64)]))

    def test_the_patch_is_known_to_the_apps(self):
        from rusemod import gamepatch
        self.assertEqual(gamepatch.PATCHES["own-squads"][0], "own-squads-24670294.json")
        self.assertIn("own-squads", gamepatch.WHY)
        self.assertEqual(squads.PATCH, "own-squads")


class TheRules(unittest.TestCase):
    def test_numbers_and_places(self):
        self.assertEqual((squads.FEWEST, squads.MOST), (2, 8))
        self.assertEqual(squads.soldier_of("Descriptor_Unit_X@3"), ("Descriptor_Unit_X", 3))
        for stem in ("Descriptor_Unit_X", "Descriptor_Unit_X@bazooka", "Descriptor_Unit_X@0", "Descriptor_Unit_X@03"):
            self.assertIsNone(squads.soldier_of(stem), stem)
        self.assertEqual([squads.place_figure(i, 5, True) for i in (1, 4, 5)],
                         ["GfxDescriptorFusilier", "GfxDescriptorFusilier", "GfxDescriptorBazooka"])
        self.assertEqual(squads.place_figure(5, 5, False), "GfxDescriptorFusilier")
        self.assertEqual(squads.fewest(1), 2)
        self.assertEqual(squads.fewest(3), 3)
        # a new soldier stands before the last soldiers who fire the squad's NeedModelChange weapons (or its last man)
        self.assertEqual(squads.join_place(5, 1, True), 5)      # the GI squad: before its bazooka man
        self.assertEqual(squads.join_place(5, 2, True), 4)
        self.assertEqual(squads.join_place(5, 0, False), 6)     # all riflemen: at the end
        self.assertEqual(squads.join_place(2, 3, True), 1)

    def test_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            squads.write_count(d, "Descriptor_Unit_X", 7)
            self.assertEqual(squads.mod_squads(d), {"Descriptor_Unit_X": 7})
            squads.write_count(d, "Descriptor_Unit_X", None)
            self.assertEqual(squads.mod_squads(d), {})


if __name__ == "__main__":
    unittest.main()
