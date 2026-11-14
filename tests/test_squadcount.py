"""A squad's own number of soldiers and each soldier's own look (rusemod.squads; the squad work's Phases 2-3). The
owner, 2026-11-12: "I would only want to change it for this one squad. Not every squad in the game."; his picks the
same night: at least 2 soldiers, at most 8 for now, a bigger squad spreads out wider as the game does, an added soldier
is a figure only, paratroopers wear each soldier's own look while falling too.

The build (rusemod.build.squad_soldiers): a squad of 7 and one of 3 get R2Behaviour, a copy of the game's one setting
with only the number changed; soldiers with looks of their own get R2SoldierLooks; the copy gets own-squads beside
more-buildings, in the apps' order, and the fingerprint takes each; the refusals in words; a mod from before is built
as before. Nothing here is tried in the game."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
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


def glb(report: dict, like: str | None, scale: float | None = None) -> bytes:
    """A mod's model file as the build reads it (rusemod.unitmodel.glb_report: its JSON part's asset extras); `scale`
    (rusemod_scale) makes it another look (rusemod.squads.look_key): two files made with the same are copies of one."""
    extras = {"rusemod_report": report, **({"rusemod_like": like} if like else {}),
              **({"rusemod_scale": scale} if scale is not None else {})}
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
        for stem, made in (models or {}).items():
            (files / f"{stem}.glb").write_bytes(glb(*made))
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
        """Counted one soldier at a time, for the look he wears, copies of one look as one look (the owner's pick 5,
        2026-11-12); a tie goes to the look of the lowest-numbered of them (soldier 1's when his is one of them)."""
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
        # soldiers 1, 2 and 3 three looks of their own: 1, 1, 1, 1 (soldier 4, a rifleman), 1 (the bazooka man):
        # soldier 1's
        self.assertEqual(far({f"Descriptor_Unit_Looks@{i}": ({"rigged": True}, RIFLE.lower(), i) for i in (1, 2, 3)}),
                         own(1))
        # soldiers 2 and 3 two looks of their own in a squad of 3: 1 (soldier 1, a rifleman), 1, 1: soldier 1's, the
        # game rifleman
        self.assertEqual(far({f"Descriptor_Unit_Looks@{i}": ({"rigged": True}, RIFLE.lower(), i) for i in (2, 3)},
                             "count = 3\n"), "us_soldier_modellod0.ase2ndfbin")
        # the same two wearing copies of one look: one look, 2 of 3 (before pick 5: two looks, soldier 1's)
        self.assertEqual(far({f"Descriptor_Unit_Looks@{i}": ({"rigged": True}, RIFLE.lower()) for i in (2, 3)},
                             "count = 3\n"), own(2))
        # soldiers 2, 3 and 4 copies of one look, the report naming each after himself: 3 of 5 (before: soldier 1's)
        self.assertEqual(far({f"Descriptor_Unit_Looks@{i}": ({"rigged": True, "pictures": [[f"Rifleman {i} 1", 4, 4]]},
                                                            RIFLE.lower()) for i in (2, 3, 4)}), own(2))

    def test_one_soldier_wears_the_game_s_look_among_riflemen_wearing_the_mod_s(self):
        """Back to the game's look on soldier 2 alone (the owner's pick 3, 2026-11-12): the squad's riflemen wear its
        own model (from before each soldier had his own), soldier 2's entry is a copy of their figure drawing the game's
        rifleman, with their clips; the far-away figure keeps the riflemen's look (3 of 5)."""
        mod = self.mod({"Descriptor_Unit_Kinds": "Descriptor_Unit_Squad"}, {},
                       {"Descriptor_Unit_Kinds": ({"rigged": True, "also": []}, RIFLE.lower())})
        squads.write_game_look(mod, "Descriptor_Unit_Kinds", 2)
        result, _arc, loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors], [])
        objects = loaded.base.objects
        unit = objects[E + "Descriptor_Unit_Kinds"]
        looks = unit.props["R2SoldierLooks"].items
        self.assertEqual([type(v).__name__ for v in looks], ["Ref", "Inline", "Ref", "Ref", "Ref"])
        rifle = unit.props["GfxDescriptorFusilier"].obj
        self.assertEqual(model_of(rifle, objects).lower(), (FOLDER + "Descriptor_Unit_Kindslod0.Ase2ndfbin").lower())
        self.assertEqual(model_of(looks[1].obj, objects), RIFLE)                  # the game's rifleman
        self.assertEqual(looks[1].obj.props["ResourceAnimation"], rifle.props["ResourceAnimation"])
        self.assertEqual(result.game_patch, ["own-squads"])
        said = " ".join(f.message for f in result.findings)
        self.assertIn("Descriptor_Unit_Kinds's soldier 2 wears the game's look", said)
        node = unit
        for prop in build.FIGURINE:
            v = node.props[prop]
            node = v.obj if isinstance(v, Inline) else objects[v.target]
        self.assertEqual(node.props["FileName"].value.lower(), (FOLDER + "Descriptor_Unit_Kindslod0.Ase2ndfbin").lower())

    def test_a_game_s_look_record_where_the_game_s_look_is_worn_already(self):
        """A record for a soldier whose place's figure draws the game's model already (no model of the mod for his
        place) changes nothing: no entry, no game patch; one past the squad's soldiers is refused in words."""
        mod = self.mod({"Descriptor_Unit_Plain": "Descriptor_Unit_Squad"})
        squads.write_game_look(mod, "Descriptor_Unit_Plain", 5)
        result, _arc, loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors], [])
        self.assertEqual(result.game_patch, [])
        self.assertFalse(any(p.startswith("R2") for o in loaded.base.objects.values() for p in o.props))
        self.tmp.cleanup()
        self.tmp = tempfile.TemporaryDirectory()
        mod = self.mod({"Descriptor_Unit_Plain": "Descriptor_Unit_Squad"}, {"Descriptor_Unit_Plain": "count = 3\n"})
        squads.write_game_look(mod, "Descriptor_Unit_Plain", 4)
        result, _arc, _loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors],
                         ["squads: files/models/Descriptor_Unit_Plain@4.json: Descriptor_Unit_Plain has 3 soldiers, so "
                          "there is no soldier 4 to wear the game's look"])

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

    def test_a_look_fitted_to_a_model_none_of_its_soldiers_wears(self):
        tank = "WW2\\Res3D\\Units\\US\\Char\\US_Sherman_modellod0.Ase2ndfbin".lower()
        mod = self.mod({"Descriptor_Unit_Looks": "Descriptor_Unit_Squad"}, {},
                       {"Descriptor_Unit_Looks@2": ({"rigged": True}, tank)})
        result, _arc, _loaded = self.build(mod)
        self.assertEqual([f.message for f in result.errors],
                         [f"squads: files/models/Descriptor_Unit_Looks@2.glb: the model of Descriptor_Unit_Looks's soldier 2 "
                          f"was fitted to {tank}, which none of its soldiers wears (import it again in the Studio)"])
        self.assertEqual(result.game_patch, [])

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

    def test_own_squads_beside_more_buildings(self):
        """A copy needing both: the squads' step and the buildings' step each add theirs to the one list (before,
        the buildings' step set the copy's one patch), and the copy gets both in the apps' order."""
        from types import SimpleNamespace

        from rusemod.model import Obj
        from rusemod.patch import num
        from test_ownbuildings import made_up_zz_win
        result, _arc, _loaded = self.build(self.mod({"Descriptor_Unit_Seven": "Descriptor_Unit_Squad"},
                                                    {"Descriptor_Unit_Seven": "count = 7\n"}))
        self.assertEqual(result.game_patch, ["own-squads"])
        buildings = {"$/W": Obj("TBatimentDescriptor", {"TypeBatiment": num(7), "Menu": num(10)})}
        build.own_buildings(SimpleNamespace(game=SimpleNamespace(objects=buildings)), Edat(made_up_zz_win()), {7: None},
                            result, {})
        self.assertEqual([f.message for f in result.errors], [])
        self.assertEqual(result.game_patch, ["own-squads", "more-buildings"])
        self.assertEqual(build.copy_patches(result.game_patch, False), ["more-buildings", "own-squads"])
        build.own_buildings(SimpleNamespace(game=SimpleNamespace(objects=buildings)), Edat(made_up_zz_win()), {7: None},
                            result, {})
        self.assertEqual(result.game_patch, ["own-squads", "more-buildings"])   # (each once)

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


from rusemod.modelin import glb_document  # noqa: E402
from test_squadblender import (BAZOOKA, GAME_SQUAD, RIFLE_FIRES, RIFLEMAN, SQUAD, STEM, WEAPONS, Running,  # noqa: E402
                               Squad, game_glb, glb_from, own_glb, sha)


class TheStudioCalls(Squad):
    """A soldier more or less in the Studio (ruse_studio.squadblender): squad_info's count, can and limits; soldier_add,
    its join on Bring my changes back, soldier_remove; with test_squadblender's stand-ins for Blender, the index and the
    game's models."""

    def set_count(self, n):
        squads.write_count(self.mod, STEM, n)

    def add(self, source, of=None, unit=None, file=None):
        with self.patched():
            return self.api.soldier_add(SQUAD, source, of, unit, file)

    def remove(self, soldier):
        with self.patched():
            return self.api.soldier_remove(SQUAD, soldier)

    def back(self):
        with self.patched():
            return self.api.squad_blender_back(SQUAD)

    def look(self, i: int, data: bytes, **record):
        f = self.models / f"{STEM}@{i}.glb"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        f.with_suffix(".json").write_text(json.dumps({"from": f"C:/x/{i}.glb", "for": str(i), **record}),
                                          encoding="utf-8")
        return f

    def test_the_count_is_the_squad_s_own(self):
        self.set_count(7)
        info = self.info()
        self.assertEqual((info["count"], len(info["soldiers"])), (7, 7))
        self.assertEqual([r["label"] for r in info["soldiers"]], ["Rifleman"] * 6 + ["Bazooka man"])
        self.assertTrue(info["line"].startswith("7 soldiers: 6 riflemen"))
        self.assertEqual([r["fires"] for r in info["soldiers"]][-2:], [RIFLE_FIRES, ["Bazooka"]])

    def test_the_limits_in_words(self):
        from ruse_studio.api import StudioError
        self.set_count(8)
        info = self.info()
        self.assertEqual((info["can"]["add"], info["can"]["remove"]), (False, True))
        self.assertEqual(info["limits"], {"add": "A squad has at most 8 soldiers for now.", "remove": None})
        with self.assertRaisesRegex(StudioError, "^A squad has at most 8 soldiers for now.$"):
            self.add("copy", "1")
        self.set_count(2)
        info = self.info()
        self.assertEqual((info["can"]["add"], info["can"]["remove"]), (True, False))
        self.assertEqual(info["limits"], {"add": None, "remove": "A squad keeps at least 2 soldiers: the game's own rule."})
        with self.assertRaisesRegex(StudioError, "^A squad keeps at least 2 soldiers: the game's own rule.$"):
            self.remove("1")
        # three weapons its last soldiers fire one each (NeedModelChange): at least 3
        self.weapons = [WEAPONS[0]] + [("Ammo_Bazooka", "Bazooka")] * 3
        self.set_count(3)
        info = self.info()
        self.assertEqual((info["fewest"], info["can"]["remove"]), (3, False))
        said = "This squad keeps at least 3 soldiers: its last 3 fire Bazooka, one each."
        self.assertEqual(info["limits"]["remove"], said)
        with self.assertRaisesRegex(StudioError, f"^{said}$"):
            self.remove("2")
        self.assertEqual(squads.mod_squads(self.mod), {STEM: 3})   # (nothing changed)
        # its Blender open: neither, until its changes are brought back or it's closed
        self.set_count(5)
        self.weapons = list(WEAPONS)
        self.api._blenders[str(self.work)] = Running()
        self.assertEqual({k: self.info()["can"][k] for k in ("add", "remove")}, {"add": False, "remove": False})
        with self.assertRaisesRegex(StudioError, "This squad is open in Blender already"):
            self.remove("1")
        with self.assertRaisesRegex(StudioError, "This squad is open in Blender already"):
            self.add("copy", "1")

    def test_a_copy_joins_before_the_bazooka_man_when_brought_back(self):
        """His picture's soldier 2 copied: Blender opens with him alone; brought back, he's soldier 5, the bazooka man
        soldier 6 with his own look as it was, the squad 6 (its own number, in the mod)."""
        old = self.look(5, own_glb(b"PNG-old-5", b"PNG-a"), report={"like": BAZOOKA})
        before = sha(old)
        res = self.add("copy", "2")
        self.assertEqual((res["opened"], res["adding"], res["count"]), (["new"], {"at": 5, "started": "game"}, 5))
        m = self.manifest()
        self.assertEqual([(s["id"], s["name"]) for s in m["soldiers"]], [("new", "New soldier")])
        self.assertEqual(m["adding"], {"id": "new", "at": 5, "source": "copy"})
        self.assertEqual(squads.mod_squads(self.mod), {})        # (not in the squad until he's brought back)
        self.blender_opened()
        calls = self.taking_in()
        self.blender_sends({"new": glb_from(b"PNG-new", "New soldier 1")})
        res = self.back()
        self.assertEqual((res["joined"], res["count"], res["changed"]), ("5", 6, ["5"]))
        self.assertEqual(res["message"], "Soldier 5 joins the squad: it has 6 soldiers now.")
        self.assertEqual(calls, [(SQUAD, f"{STEM}@5.glb", 1.0, "5")])
        self.assertEqual(sha(self.models / f"{STEM}@6.glb"), before)          # the bazooka man: still last, as he was
        self.assertEqual(json.loads((self.models / f"{STEM}@6.json").read_text(encoding="utf-8"))["for"], "6")
        self.assertEqual(squads.mod_squads(self.mod), {STEM: 6})
        info = self.info()
        self.assertEqual([r["label"] for r in info["soldiers"]], ["Rifleman"] * 5 + ["Bazooka man"])
        self.assertEqual([r["wears"] for r in info["soldiers"]], ["game"] * 4 + ["own", "own"])
        state = json.loads((self.work / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(state["taken"]), ["5"])

    def test_a_join_that_fails_leaves_the_squad_as_it_was(self):
        from ruse_studio.api import StudioError
        old = self.look(5, b"glTF-old-5")
        self.add("copy", "1")
        self.blender_opened()

        def fails(*_a, **_k):
            raise StudioError("This model can't be fitted.")
        self.api.model_import = fails
        self.blender_sends({"new": glb_from(b"PNG-new", "New soldier 1")})
        with self.assertRaisesRegex(StudioError, "can't be fitted"):
            self.back()
        self.assertEqual((old.read_bytes(), squads.mod_squads(self.mod)), (b"glTF-old-5", {}))
        self.assertFalse((self.models / f"{STEM}@6.glb").exists())

    def test_a_soldier_from_another_squad_and_from_a_file(self):
        from ruse_studio.api import StudioError
        res = self.add("unit", "1", GAME_SQUAD)
        self.assertEqual(res["adding"], {"at": 5, "started": "game"})
        doc, _binary = glb_document(Path(self.manifest()["soldiers"][0]["file"]).read_bytes())
        self.assertEqual([x["name"] for x in doc["materials"]], ["New soldier 1"])
        self.api._soldiers = lambda address: address != E + "Descriptor_Unit_Tank"
        with self.assertRaisesRegex(StudioError, "^The unit to take a soldier from isn't a squad of soldiers.$"):
            self.add("unit", "1", E + "Descriptor_Unit_Tank")
        with self.assertRaisesRegex(StudioError, "^That squad has no soldier called 9.$"):
            self.add("unit", "9", GAME_SQUAD)
        # a model file: fitted to a rifleman's bones into the squad's Blender folder, the mod's files untouched
        fitted = []

        def fit(address, file, size, aircraft, facing, own_turret, own_propellers, move, kind=None, out=None):
            fitted.append((Path(file).name, kind, Path(out)))
            Path(out).write_bytes(own_glb(b"PNG-file", b"PNG-file-alpha"))
            Path(out).with_suffix(".json").write_text(json.dumps({"report": {"like": RIFLEMAN}}), encoding="utf-8")
            return {"rigged": True}
        self.api._fit_model = fit
        res = self.add("file", file="C:/Users/x/marine.glb")
        self.assertEqual(fitted, [("marine.glb", "1", self.work / "new" / "marine.glb")])
        self.assertEqual(res["adding"], {"at": 5, "started": "model"})
        self.assertEqual(list(self.models.glob("*")) if self.models.is_dir() else [], [])
        self.assertIsNone(self.add("file"))     # (no file given and no window to pick one in: nothing opened)

    def test_remove_moves_the_soldiers_after_him_up_and_keeps_his_look_aside(self):
        for i in (2, 3, 5):
            self.look(i, f"glTF-{i}".encode())
        kept = self.work / "kept"
        kept.mkdir(parents=True)
        (kept / f"{STEM}@3.glb").write_bytes(b"kept-3")
        (self.work / "state.json").write_text(json.dumps({"taken": {"3": {"kept": "a", "model": "b"},
                                                                     "fusilier": {"x": 1}}}), encoding="utf-8")
        res = self.remove("2")
        self.assertEqual((res["removed"], res["count"]), ("2", 4))
        aside = Path(res["kept_aside"])
        self.assertTrue(aside.is_relative_to(self.work))
        self.assertEqual(sorted(p.name for p in aside.iterdir()), [f"{STEM}@2.glb", f"{STEM}@2.json"])
        self.assertEqual(((self.models / f"{STEM}@2.glb").read_bytes(), (self.models / f"{STEM}@4.glb").read_bytes()),
                         (b"glTF-3", b"glTF-5"))                         # soldiers 3 and 5 are 2 and 4 now
        self.assertFalse((self.models / f"{STEM}@5.glb").exists() or (self.models / f"{STEM}@3.glb").exists())
        self.assertEqual(json.loads((self.models / f"{STEM}@4.json").read_text(encoding="utf-8"))["for"], "4")
        self.assertEqual((kept / f"{STEM}@2.glb").read_bytes(), b"kept-3")
        state = json.loads((self.work / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["taken"], {"2": {"kept": "a", "model": "b"}, "fusilier": {"x": 1}})
        self.assertEqual(squads.mod_squads(self.mod), {STEM: 4})
        # one more joins: the game's 5 again, so no number of its own is kept
        self.add("copy", "1")
        self.blender_opened()
        self.taking_in()
        self.blender_sends({"new": glb_from(b"PNG-new", "New soldier 1")})
        self.assertEqual((self.back()["count"], squads.mod_squads(self.mod)), (5, {}))

    def test_the_refusals(self):
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "^pigeon isn't a way to add a soldier"):
            self.add("pigeon")
        with self.assertRaisesRegex(StudioError, "^This squad has no soldier called 7.$"):
            self.add("copy", "7")
        with self.assertRaisesRegex(StudioError, "^This squad has no soldier called 9.$"):
            self.remove("9")
        with self.patched(), self.assertRaisesRegex(StudioError, "one of the game's own squads: copy it first"):
            self.api.soldier_add(GAME_SQUAD, "copy", "1")
        self.api._blender = lambda: None
        with self.assertRaisesRegex(StudioError, "Blender isn't found on this PC"):
            self.add("copy", "1")
        self.assertFalse((self.work / "squad.json").exists())

    # --- +1 and −1, no Blender (the owner, 2026-11-12: "I would like to add the +1 button because that seems a lot
    # easier than 4 steps to add 1 unit"; "You should be able to subtract from the base unit. And add.") ---
    def plus(self):
        with self.patched():
            return self.api.soldier_plus(SQUAD)

    def minus(self):
        with self.patched():
            return self.api.soldier_minus(SQUAD)

    def files(self) -> dict:
        return {p.name: p.read_bytes() for p in sorted(self.models.iterdir())} if self.models.is_dir() else {}

    def test_plus_one_joins_before_the_bazooka_man_looking_like_most_riflemen(self):
        """No Blender: he's soldier 5 of 6, the bazooka man soldier 6 with his own look as it was; he wears the look
        most of the riflemen wear: the game's (no file of his own), then, with three riflemen painted alike (copies of
        one look, each named after himself), a copy of the first one's."""
        from ruse_studio.api import StudioError
        bazooka = self.look(5, own_glb(b"PNG-bazooka", b"PNG-a"), report={"like": BAZOOKA})
        before = sha(bazooka)
        res = self.plus()
        self.assertEqual((res["joined"], res["count"], self.started), ("5", 6, []))
        self.assertEqual(sha(self.models / f"{STEM}@6.glb"), before)
        self.assertFalse((self.models / f"{STEM}@5.glb").exists() or (self.models / f"{STEM}@5.json").exists())
        self.assertEqual([r["wears"] for r in res["soldiers"]], ["game"] * 5 + ["own"])
        self.assertEqual(squads.mod_squads(self.mod), {STEM: 6})
        from rusemod import gltf
        for i in (1, 2, 3):
            doc, views = gltf.glb_views(own_glb(b"PNG-red", b"PNG-a"))
            for x in doc["materials"] + doc["images"]:
                x["name"] = f"Rifleman {i} 1"
            self.look(i, gltf.pack_glb(doc, views), copy_kept='of = ["x"]\n')
        res = self.plus()
        self.assertEqual((res["joined"], res["like"], res["count"]), ("6", "1", 7))
        self.assertEqual((self.models / f"{STEM}@6.glb").read_bytes(), (self.models / f"{STEM}@1.glb").read_bytes())
        record = json.loads((self.models / f"{STEM}@6.json").read_text(encoding="utf-8"))
        self.assertEqual((record["for"], "copy_kept" in record), ("6", False))   # (a uniform waits in one record)
        self.assertEqual(sha(self.models / f"{STEM}@7.glb"), before)          # the bazooka man: still last
        self.assertEqual([r["wears"] for r in res["soldiers"]], ["own"] * 3 + ["game"] * 2 + ["own", "own"])
        self.plus()
        with self.assertRaisesRegex(StudioError, "^A squad has at most 8 soldiers for now.$"):
            self.plus()
        self.assertEqual(squads.mod_squads(self.mod), {STEM: 8})

    def test_plus_one_among_riflemen_wearing_the_squad_s_one_model(self):
        """Riflemen wearing the squad's one model from before (files/models/<unit>.glb): +1's soldier wears it too (no
        file of his own); with most of them back to the game's look (pick 3's records), he wears the game's look too."""
        riflemen = self.models / f"{STEM}.glb"
        riflemen.parent.mkdir(parents=True)
        riflemen.write_bytes(own_glb(b"PNG-riflemen", b"PNG-a"))
        res = self.plus()
        self.assertEqual(res["joined"], "5")
        self.assertFalse((self.models / f"{STEM}@5.json").exists() or (self.models / f"{STEM}@5.glb").exists())
        self.assertEqual([r["wears"] for r in res["soldiers"]], ["kind"] * 5 + ["game"])
        for i in (1, 2, 3):
            squads.write_game_look(self.mod, STEM, i)
        res = self.plus()
        self.assertEqual((res["joined"], res["like"]), ("6", "1"))
        self.assertEqual(json.loads((self.models / f"{STEM}@6.json").read_text(encoding="utf-8")),
                         {"for": "6", "look": "game"})
        self.assertEqual([r["wears"] for r in res["soldiers"]], ["game"] * 3 + ["kind"] * 2 + ["game", "game"])

    def test_minus_one_takes_the_last_rifleman_and_plus_then_minus_is_as_before(self):
        from ruse_studio.api import StudioError
        self.look(4, own_glb(b"PNG-4", b"PNG-a"))
        self.look(5, own_glb(b"PNG-bazooka", b"PNG-a"), report={"like": BAZOOKA})
        bazooka = sha(self.models / f"{STEM}@5.glb")
        res = self.minus()
        self.assertEqual((res["removed"], res["count"], res["look_kept"]), ("4", 4, True))
        self.assertEqual(sorted(p.name for p in Path(res["kept_aside"]).iterdir()), [f"{STEM}@4.glb", f"{STEM}@4.json"])
        self.assertEqual(sha(self.models / f"{STEM}@4.glb"), bazooka)        # the bazooka man is soldier 4 now
        before = self.files()
        self.plus()
        self.assertEqual(squads.mod_squads(self.mod), {})                    # (the game's 5 again: no number kept)
        self.minus()
        self.assertEqual(self.files(), before)
        self.api._blenders[str(self.work)] = Running()
        for call in (self.plus, self.minus):
            with self.assertRaisesRegex(StudioError, "This squad is open in Blender already"):
                call()
        self.assertEqual(self.files(), before)
        self.api._blenders.clear()
        self.minus()
        self.minus()
        self.assertEqual((self.info()["count"], squads.mod_squads(self.mod)), (2, {STEM: 2}))
        with self.assertRaisesRegex(StudioError, "^A squad keeps at least 2 soldiers: the game's own rule.$"):
            self.minus()

    def test_a_soldier_taken_out_keeps_the_uniform_waiting_in_his_record(self):
        """A Custom uniform his look took the place of waits in his record (Import model): taken out by −1 or Remove,
        it waits in the record of a model still in the mod; with none left, it is the squad's uniform again."""
        self.look(4, own_glb(b"PNG-4", b"PNG-a"), copy_kept='of = ["x"]\n')
        self.look(5, own_glb(b"PNG-bazooka", b"PNG-a"), report={"like": BAZOOKA})
        res = self.minus()
        self.assertEqual(res["copy_back"], False)
        self.assertEqual(json.loads((self.models / f"{STEM}@4.json").read_text(encoding="utf-8"))["copy_kept"],
                         'of = ["x"]\n')
        self.assertFalse((self.models / f"{STEM}.copy.toml").exists())
        res = self.remove("4")
        self.assertEqual(res["copy_back"], True)
        self.assertEqual((self.models / f"{STEM}.copy.toml").read_text(encoding="utf-8"), 'of = ["x"]\n')

    def test_a_soldier_who_wears_the_game_s_look_moves_with_his_number(self):
        squads.write_game_look(self.mod, STEM, 3)
        self.remove("2")
        self.assertEqual(json.loads((self.models / f"{STEM}@2.json").read_text(encoding="utf-8")),
                         {"for": "2", "look": "game"})
        self.assertFalse((self.models / f"{STEM}@3.json").exists())


class InTheStudio(unittest.TestCase):
    """Import a model for one soldier alone, Back to the game's look, Resize and a deleted unit, on a made-up game's
    index (the squad above): each soldier's own look fitted to the figure the game gives his place."""

    @classmethod
    def setUpClass(cls):
        from rusemod.index import build_index
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        data = cls.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(unit_data())
        (data / "ZZ_Win.dat").write_bytes(clips_pack())
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home)
        self.api._look_models = lambda address: ([RIFLE.lower(), HEAVY.lower()], [])
        self.mod = Path(self.home, "mods", "squads")
        (self.mod / "src").mkdir(parents=True)
        (self.mod / "mod.toml").write_text('[mod]\nid = "squads"\nversion = "1.0.0"\n', encoding="utf-8")
        self.api.choose_mod(str(self.mod))
        self.unit = self.api.new_unit(E + "Descriptor_Unit_Squad", "Squad Seven", 5)["address"]
        self.stem = self.unit.rsplit("/", 1)[-1]
        self.models = self.mod / "files" / "models"
        self.source = Path(self.home, "marine.glb")
        self.source.write_bytes(b"glTF")
        self.calls = []

    def fitted(self, game, source_model, model_file, out, **kw):
        """rusemod.unitmodel.import_model stood in for (test_unitmodel has the fitting): the file written, its report."""
        self.calls.append(source_model)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"glTF fitted")
        return {"file": Path(model_file).name, "vertices": 3, "triangles": 1, "rigged": True, "like": source_model}

    def imported(self, kind=None):
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            return self.api.model_import(self.unit, str(self.source), kind=kind)

    def test_one_soldier_s_own_look_fitted_to_his_place(self):
        from ruse_studio.api import StudioError
        self.imported("5")
        self.assertEqual(self.calls[-1], HEAVY.lower())      # the last place: the bazooka man's figure's model
        self.imported("2")
        self.assertEqual(self.calls[-1], RIFLE.lower())      # a rifleman's place
        own = lambda i: self.models / f"{self.stem}@{i}"   # noqa: E731
        self.assertTrue(own(5).with_suffix(".glb").is_file() and own(2).with_suffix(".glb").is_file())
        self.assertEqual(json.loads(own(5).with_suffix(".json").read_text(encoding="utf-8"))["for"], "5")
        self.assertFalse((self.models / f"{self.stem}.glb").exists())     # the riflemen's model: none made
        with mock.patch("rusemod.gltf.model_glb", lambda lib, name, side=2048, rest_bones=False: game_glb(name)):
            info = self.api.squad_info(self.unit)       # (its previews: the made-up game has no model packs)
        self.assertEqual([r["wears"] for r in info["soldiers"]], ["game", "own", "game", "game", "own"])
        with self.assertRaisesRegex(StudioError, "kind called 6"):     # (a squad of 5 has no soldier 6)
            self.imported("6")
        squads.write_count(self.mod, self.stem, 7)
        self.imported("6")                                    # (with 7, soldier 6 stands among the riflemen)
        self.assertEqual(self.calls[-1], RIFLE.lower())
        squads.write_count(self.mod, self.stem, None)
        own(6).with_suffix(".glb").unlink()
        own(6).with_suffix(".json").unlink()
        # his own look out; the others' stay
        res = self.api.model_import_remove(self.unit, "5")
        self.assertTrue(res["model_out"])
        self.assertFalse(own(5).with_suffix(".glb").exists())
        self.assertTrue(own(2).with_suffix(".glb").is_file())
        # Resize fits each soldier's own look again too: one size for the squad
        self.imported()
        self.calls.clear()
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            self.api.model_resize(self.unit, 1.5)
        self.assertEqual(self.calls, [RIFLE.lower(), RIFLE.lower()])     # the riflemen's model, then soldier 2's
        self.assertEqual(json.loads(own(2).with_suffix(".json").read_text(encoding="utf-8"))["size"], 1.5)

    def test_a_deleted_unit_takes_its_soldiers_files_with_it(self):
        from ruse_studio.edits import ModEdits
        self.imported("3")
        squads.write_count(self.mod, self.stem, 7)
        self.assertEqual(sorted(p.name for p in self.models.iterdir()),
                         [f"{self.stem}.squad.toml", f"{self.stem}@3.glb", f"{self.stem}@3.json"])
        ModEdits(self.mod).remove_unit(self.unit)
        self.assertEqual(list(self.models.iterdir()), [])


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

    def test_who_leaves_on_minus_one(self):
        # the soldier +1 puts a new one before: +1 then −1 leaves the squad as it was
        self.assertEqual(squads.leave_place(5, 1, True), 4)     # the GI squad: the rifleman before the bazooka man
        self.assertEqual(squads.leave_place(6, 2, True), 4)
        self.assertEqual(squads.leave_place(5, 0, False), 5)    # all riflemen: the last
        self.assertIsNone(squads.leave_place(3, 3, True))       # every soldier fires a weapon of his own
        for n, need, last in ((5, 1, True), (6, 2, True), (5, 0, False), (3, 1, True)):
            self.assertEqual(squads.leave_place(n + 1, need, last), squads.join_place(n, need, last))

    def test_a_soldier_who_wears_the_game_s_look(self):
        with tempfile.TemporaryDirectory() as d:
            path = squads.write_game_look(d, "Descriptor_Unit_X", 3)
            self.assertEqual(path.name, "Descriptor_Unit_X@3.json")
            self.assertEqual(squads.mod_game_looks(d), {"Descriptor_Unit_X": [3]})
            path.with_suffix(".glb").write_bytes(b"glTF")        # (a look of his own beside it: his own, not the game's)
            self.assertEqual(squads.mod_game_looks(d), {})
            path.with_suffix(".glb").unlink()
            path.write_text('{"for": "3", "from": "C:/m.glb"}', encoding="utf-8")   # (another record: not the game's)
            self.assertEqual(squads.mod_game_looks(d), {})

    def test_copies_of_one_look_are_one_look(self):
        """What never shows in the game doesn't count (the pictures', materials' and scene's names, the report naming
        them: the Studio names each soldier's after him); his pictures, shape and bones do."""
        from rusemod import gltf
        a = own_glb(b"PNG-red", b"PNG-alpha")

        def changed(raw: bytes, change) -> bytes:
            doc, views = gltf.glb_views(raw)
            change(doc, views)
            return gltf.pack_glb(doc, views)

        def renamed(doc, _views):
            for part in ("materials", "images", "scenes"):
                for x in doc.get(part) or []:
                    x["name"] = "Rifleman 6 1"
            doc["asset"].setdefault("extras", {})["rusemod_report"] = {"pictures": [["Rifleman 6 1", 4, 4]]}
        copy = changed(a, renamed)
        self.assertNotEqual(copy, a)
        self.assertEqual(squads.look_key(copy), squads.look_key(a))
        self.assertNotEqual(squads.look_key(own_glb(b"PNG-blue", b"PNG-alpha")), squads.look_key(a))
        self.assertNotEqual(squads.look_key(own_glb(b"PNG-red", b"PNG-other-alpha")), squads.look_key(a))

        def on_another_bone(doc, _views):
            joint = doc["skins"][0]["joints"][-1]
            doc["nodes"][joint]["name"] = "bip01 l hand"
        self.assertNotEqual(squads.look_key(changed(a, on_another_bone)), squads.look_key(a))
        self.assertTrue(squads.look_key(b"not a model").startswith("bytes:"))


if __name__ == "__main__":
    unittest.main()
