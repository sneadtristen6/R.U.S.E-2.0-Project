"""Which animation each action plays (item 5 of the owner's list, part 2, 2026-11-10): rusemod.animactions' rule (the
nearest, one rule for the page and the build), units.toml's animation, plays and ride tables (rusemod.anim), the build
giving the figures that draw a unit's own model its model's animations and the unit a ride of its own (rusemod.build),
the Studio's action table and a copied unit keeping its source's animations (ruse_studio.actions)."""
import json
import re
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, animactions as aa, baf, build
from rusemod.edat import Edat
from test_anim import clip

B = "\\"
E = "$/GFX/Everything/"
UNIT = "Descriptor_Unit_Horse_Squad"
# the rifle squad's listings as the game has them (read from the plain copy's game index, 2026-11-10): its rifleman's
# 70, its bazooka man's 16 more, the far-zoom figure's 4 replacements and the fallen figure's two
SOLDIER = [f"{h}_{a}" for a in (
    "stand", "accroupi", "marche", "marche_arriere", "course", "course2", "course3", "course_droite", "course_gauche",
    "course_arriere", "deroute", "deroute2", "deroute3", "mort_balle", "mort_balle_violente", "mort_explosion",
    "mort_balle_dos", "mort_explosion_dos", "stand_vise", "accroupi_vise", "marche_vise", "marche_arriere_vise",
    "course_vise", "course_droite_vise", "course_gauche_vise", "course_arriere_vise", "tir", "tir_secondaire",
    "tir_secondaire2", "tir_secondaire3", "recharge", "hit", "hit_dos", "hit_explosion", "look_around",
    "stand_vise_special", "course_vise_special", "course_droite_vise_special", "course_gauche_vise_special",
    "course_arriere_vise_special", "tir_special", "transition_to_special", "transition_from_special", "mort")
    for h in ("t", "b")] + ["t_transition_to_special_replacement", "t_tir_replacement", "t_tir_special_replacement"]


def horse_rule(key: str) -> str:
    """What the owner's 2026-11-09 horse copies played for each listing, by hand (scratch/modelgaps
    make_own_horse3_test.py's clip_for): walk for walking, run for running and fleeing, stand for the rest."""
    return "walk" if "marche" in key else "run" if "course" in key or "deroute" in key else "stand"


class TheRule(unittest.TestCase):
    def test_a_listing_s_half_and_action(self):
        self.assertEqual(aa.parse_key("t_course_vise"), ("top", "course_vise"))
        self.assertEqual(aa.parse_key("b_stand"), ("bottom", "stand"))
        self.assertEqual(aa.parse_key("t_tir_special_replacement"), ("top", "tir_special"))
        self.assertEqual(aa.parse_key("t_tir_secondaire_replacement_1"), ("top", "tir_secondaire"))
        self.assertEqual(aa.parse_key("idle1"), (None, "idle1"))

    def test_what_a_name_says(self):
        self.assertEqual(aa.says("Horse_Run2"), ("run", frozenset(), 2))
        self.assertEqual(aa.says("RiderFireLeft"), ("fire", frozenset({"left"}), 0))
        self.assertEqual(aa.says("aim_walk"), ("aim", frozenset({"walk"}), 0))
        self.assertEqual(aa.says("Death shot"), ("die", frozenset(), 0))          # a death, not a shot
        self.assertEqual(aa.says("hit-backwards"), ("hit", frozenset({"back"}), 0))
        self.assertEqual(aa.says("Idle1"), ("stand", frozenset(), 0))             # (1: the first way)
        self.assertEqual(aa.says("Gallop"), ("run", frozenset(), 0))
        self.assertEqual(aa.says("zzz"), (None, frozenset(), 0))

    def test_the_owner_s_horse_plays_as_it_did_by_hand(self):
        """The game's own horse's three clips on the rifle squad's every listing, as the copies he played on
        2026-11-09 had them (own-horse3 to 8): the rule gives each listing the same one."""
        names = ["horse_stand", "horse_walk", "horse_run"]
        for key in SOLDIER:
            with self.subTest(key=key):
                self.assertEqual(aa.choose(key, names)[0], f"horse_{horse_rule(key)}")
        self.assertEqual(aa.ride(names), ("horse_run", "nearest"))

    def test_the_horse_squad_s_own_animations_play_as_own_horse10_played_them(self):
        """The Horse Squad .glb (scratch/animmodels/horse-squad-rifle.glb, the owner's tenth horse copy, passed in the
        game 2026-11-09) names its animations hr_t_* (the rider: the top half) and hr_b_* (the horse: the bottom
        half). Each listing gets what that copy played (all 246 of the three figures': the agent's
        check_hr_rule.py; a sample here, with the game's clip each listing played)."""
        names = ["hr_t_stand", "hr_b_stand", "hr_b_walk", "hr_b_run", "hr_t_mort_balle", "hr_t_mort_balle_violente",
                 "hr_t_mort_explosion", "hr_t_mort_balle_dos", "hr_t_mort_explosion_dos", "hr_t_stand_vise",
                 "hr_t_tir", "hr_t_grenade", "hr_t_grenade2", "hr_t_grenade3", "hr_t_recharge", "hr_t_hit",
                 "hr_t_hit_dos", "hr_t_hit_explosion", "hr_t_look_around", "hr_ride", "hr_t_bazooka_tir",
                 "hr_t_bazooka_transition1", "hr_t_bazooka_transition2", "hr_t_bazooka_vise"]
        played = {("t_course", "courselod0"): "hr_t_stand", ("b_course", "courselod0"): "hr_b_run",
                  ("t_marche_vise", "stand_viselod0"): "hr_t_stand_vise", ("b_marche_vise", "marchelod0"): "hr_b_walk",
                  ("t_course_vise", "course_viselod0"): "hr_t_stand_vise", ("b_tir", "tirlod0"): "hr_b_stand",
                  ("t_transition_to_special", "bazooka_transition1lod0"): "hr_t_bazooka_transition1",
                  ("t_tir_special_replacement", "bazooka_tirlod0"): "hr_t_bazooka_tir",
                  ("t_course_vise_special", "bazooka_course_viselod0"): "hr_t_bazooka_vise",
                  ("t_mort_explosion_dos", "mort_explosion_doslod0"): "hr_t_mort_explosion_dos",
                  ("b_mort_explosion_dos", "mort_explosion_doslod0"): "hr_b_stand",
                  ("t_tir_secondaire2", "grenade2lod0"): "hr_t_grenade2", ("t_deroute2", "deroute2lod0"): "hr_t_stand",
                  ("b_deroute2", "deroute2lod0"): "hr_b_run", ("t_accroupi", "accroupilod0"): "hr_t_stand"}
        for (key, stem), want in played.items():
            with self.subTest(key=key):
                self.assertEqual(aa.choose(key, names, {}, f"WW2\\Res3D\\Units\\Common\\Fusilier_{stem}.Ase2NdfBin")[0],
                                 want)
        self.assertEqual(aa.ride(names), ("hr_ride", "named"))
        self.assertEqual(aa.marked(names)["hr_b_run"], ("run", "bottom"))

    def test_a_pick_wins_and_the_actions_nearest_it_follow(self):
        names = ["Idle", "Gallop", "Trot slow"]
        picks = {"course": "Gallop"}
        self.assertEqual(aa.choose("t_course", names, picks), ("Gallop", "picked"))
        self.assertEqual(aa.choose("b_course", names, picks), ("Gallop", "picked"))      # both halves
        self.assertEqual(aa.choose("t_course2", names, picks), ("Gallop", "nearest"))
        self.assertEqual(aa.choose("b_deroute", names, picks), ("Gallop", "nearest"))
        self.assertEqual(aa.choose("t_stand", names, picks), ("Idle", "named"))
        # a pick naming an animation the model hasn't got is no pick: the first one named for a run plays
        self.assertEqual(aa.choose("t_course", names, {"course": "Canter"}), ("Gallop", "named"))
        self.assertEqual(aa.choose("t_course", ["Idle", "Trot slow", "Gallop"]), ("Trot slow", "named"))

    def test_aiming_while_moving_aims_on_top_only_with_an_aim(self):
        names = ["stand", "walk", "run"]
        self.assertEqual([aa.choose(k, names)[0] for k in ("t_marche_vise", "b_marche_vise", "t_course_vise",
                                                             "b_course_vise", "t_stand_vise", "t_tir")],
                         ["walk", "walk", "run", "run", "stand", "stand"])
        names += ["aim"]
        self.assertEqual([aa.choose(k, names)[0] for k in ("t_marche_vise", "b_marche_vise", "t_course_vise",
                                                             "b_course_vise", "t_stand_vise", "t_tir")],
                         ["aim", "walk", "aim", "run", "aim", "aim"])
        names += ["aim walk"]
        self.assertEqual(aa.choose("t_marche_vise", names), ("aim walk", "named"))
        self.assertEqual(aa.choose("b_marche_vise", names), ("aim walk", "named"))

    def test_the_names_the_game_gives_its_actions_and_clips(self):
        """A model whose animations are named after the game's actions or clips (one made from the game's soldier)
        plays them where the game plays them."""
        names = ["course", "fusilier_stand_vise", "stand"]
        self.assertEqual(aa.choose("t_course", names), ("course", "named"))
        self.assertEqual(aa.choose("b_course", names), ("course", "named"))
        clip_of = "WW2\\Res3D\\Units\\Common\\Fusilier_stand_viselod0.Ase2NdfBin"
        self.assertEqual(aa.choose("t_marche_vise", names, clip=clip_of), ("fusilier_stand_vise", "named"))
        self.assertEqual(aa.choose("t_tir", names)[0], "fusilier_stand_vise")   # fire: the aim, by its name

    def test_deaths(self):
        names = ["stand", "death", "death explosion"]
        self.assertEqual(aa.choose("t_mort_balle", names), ("death", "named"))
        self.assertEqual(aa.choose("t_mort_explosion", names), ("death explosion", "named"))
        self.assertEqual(aa.choose("t_mort_explosion_dos", names), ("death explosion", "nearest"))
        self.assertEqual(aa.choose("b_mort_balle_dos", names), ("death", "nearest"))
        self.assertEqual(aa.choose("t_mort", names), ("death", "nearest"))     # the fallen figure
        self.assertEqual(aa.choose("t_mort_balle", ["stand", "walk"]), ("stand", "nearest"))

    def test_nothing_fits(self):
        self.assertEqual(aa.choose("t_course", ["zzz", "yyy"]), ("zzz", "nearest"))   # the model's first
        self.assertEqual(aa.choose("t_course", []), (None, "none"))
        self.assertEqual(aa.choose("t_unknown_thing", ["stand", "run"]), ("stand", "nearest"))

    def test_the_table_and_what_is_missing(self):
        listings = [("GfxDescriptorFusilier", k, None) for k in SOLDIER]
        rows = aa.table(listings, ["run"])
        self.assertEqual([r["action"] for r in rows[:3]], ["stand", "accroupi", "look_around"])
        self.assertEqual(len(rows), len({aa.parse_key(k)[1] for k in SOLDIER}))
        self.assertEqual(aa.missing(rows), ["stand", "marche"])
        rows = aa.table(listings, ["run", "idle"], {"marche": "run"})
        self.assertEqual(aa.missing(rows), [])
        walk = next(r for r in rows if r["action"] == "marche")
        self.assertEqual((walk["picked"], walk["plays"], walk["how"], walk["keys"]),
                         ("run", {"top": "run", "bottom": "run"}, "picked", 2))
        aim = next(r for r in rows if r["action"] == "marche_vise")
        self.assertEqual(aim["plays"], {"top": "run", "bottom": "run"})

    def test_every_action_has_a_known_line(self):
        for base, spec in aa.ACTIONS.items():
            self.assertIn(spec[0], aa.SECTIONS, base)
            for line in spec[3:]:
                for step in line.split():
                    self.assertIn(step.lstrip("!"), aa.ACTIONS, (base, step))
            for kind, ways in aa._signatures(base):
                self.assertIn(kind, {k for k, _w in aa.KINDS}, base)
                self.assertTrue(ways <= {k for k, _w in aa.WAYS} | set(aa.MOVING), base)


class UnitsToml(unittest.TestCase):
    def test_animations_picks_and_ride_written_and_read(self):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d)
            stand, gallop = baf.build(clip(lift=1.0)), baf.build(clip(lift=3.0))
            files = anim.set_animations(mod, UNIT, {"stand": stand, "Gallop fast": gallop})
            self.assertEqual(files, {"stand": "stand.baf", "Gallop fast": "Gallop_fast.baf"})
            own = mod / anim.OWN / UNIT
            self.assertEqual((own / "Gallop_fast.baf").read_bytes(), gallop)
            anim.set_pick(mod, UNIT, "course", "Gallop fast")
            anim.set_pick(mod, UNIT, "ride", "stand")
            anim.set_ride(mod, UNIT, "truck")
            got = anim.mod_unit_clips(mod)[UNIT]
            self.assertEqual(got["animations"], {"stand": own / "stand.baf", "Gallop fast": own / "Gallop_fast.baf"})
            self.assertEqual((got["plays"], got["ride"]), ({"course": "Gallop fast", "ride": "stand"}, "truck"))
            text = (mod / anim.UNITS).read_text(encoding="utf-8")
            self.assertIn('[unit.Descriptor_Unit_Horse_Squad]\nride = "truck"', text)
            self.assertIn('"Gallop fast" = "Gallop_fast.baf"', text)
            self.assertEqual(anim.units_toml(anim.read_units(mod)), text)                 # read back, written the same
            anim.set_ride(mod, UNIT, None)
            self.assertIsNone(anim.mod_unit_clips(mod)[UNIT]["ride"])
            # the model again, without the gallop: its pick goes (it plays the nearest), and its file
            anim.add_unit_clip(mod, UNIT, "t_wave", stand, name="wave")                    # (a row of Decoy's or a tool's)
            anim.set_animations(mod, UNIT, {"stand": stand, "walk": gallop})
            got = anim.mod_unit_clips(mod)[UNIT]
            self.assertEqual((sorted(got["animations"]), got["plays"]), (["stand", "walk"], {"ride": "stand"}))
            self.assertFalse((own / "Gallop_fast.baf").exists())
            anim.drop_animations(mod, UNIT)                                               # (its model taken out)
            got = anim.mod_unit_clips(mod)[UNIT]
            self.assertEqual((got["animations"], got["plays"], list(got["actions"])), ({}, {}, [("t_wave", None)]))
            self.assertEqual(sorted(p.name for p in own.iterdir()), ["wave.baf"])

    def test_refused(self):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d)
            anim.set_animations(mod, UNIT, {"stand": baf.build(clip())})
            for text in (f'[unit.{UNIT}.plays]\ncourse = "nope"\n[unit.{UNIT}.animation]\nstand = "stand.baf"\n',
                         f'[unit.{UNIT}]\nride = "boat"\n',
                         f'[unit.{UNIT}.animation]\nrun = "missing.baf"\n',
                         f'[unit.{UNIT}.plays]\n"Big Action" = "stand"\n[unit.{UNIT}.animation]\nstand = "stand.baf"\n',
                         f'[unit.{UNIT}.dance]\na = 1\n'):
                with self.subTest(text=text), self.assertRaises(anim.AnimError):
                    anim.mod_unit_clips(mod, text)
            with self.assertRaises(anim.AnimError):
                anim.set_pick(mod, UNIT, "course", "Gallop")      # no such animation
            with self.assertRaises(anim.AnimError):
                anim.set_animations(mod, UNIT, {"bad": b"not a clip"})
            with self.assertRaises(anim.AnimError):
                anim.set_ride(mod, UNIT, "boat")

    def test_a_copy_takes_its_source_s_animations_along(self):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d)
            src = "Descriptor_Unit_Soldat_US_Leger"
            stand = baf.build(clip(lift=2.0))
            anim.add_unit_clip(mod, src, "t_stand", stand, name="wave")
            (mod / anim.OWN / src / "genanim_15/ww2/res3d/units/common").mkdir(parents=True)
            (mod / anim.OWN / src / "genanim_15/ww2/res3d/units/common/fusilier_courselod0.baf").write_bytes(stand)
            table = anim.read_units(mod)
            table[src]["clip"] = {"genanim_15/ww2/res3d/units/common/fusilier_courselod0.baf": {
                "speed": 150, "file": "genanim_15/ww2/res3d/units/common/fusilier_courselod0.baf"}}
            anim.write_units(mod, table)
            self.assertTrue(anim.copy_unit(mod, src, "Descriptor_Unit_GI_Strong"))
            units = anim.read_units(mod)
            self.assertEqual(units["Descriptor_Unit_GI_Strong"], units[src])
            for rel in ("wave.baf", "genanim_15/ww2/res3d/units/common/fusilier_courselod0.baf"):
                self.assertEqual((mod / anim.OWN / "Descriptor_Unit_GI_Strong" / rel).read_bytes(), stand)
            got = anim.mod_unit_clips(mod)["Descriptor_Unit_GI_Strong"]
            self.assertEqual(list(got["actions"]), [("t_stand", None)])
            self.assertFalse(anim.copy_unit(mod, "Descriptor_Unit_Nothing", "Descriptor_Unit_Other_Copy"))


# --- a made-up game: two squads riding a troop truck, their figures on one soldier model ---
STAND_FILE, RUN_FILE, WALK_FILE = (f"WW2\\Res3D\\Units\\Common\\Fusilier_{n}lod0.Ase2NdfBin"
                                   for n in ("stand", "course", "marche"))
SOLDIER_MODEL = "WW2\\Res3D\\Units\\US\\Infanterie\\US_Soldier_modellod0.Ase2NdfBin"
TRUCK_MODEL = "WW2\\Res3D\\Units\\US\\Vehicule\\US_GMC_Cargo\\US_GMC_Cargo_infanterielod0.Ase2NDFBin"
OWN_MODEL = f"WW2\\Res3D\\Units\\US\\Infanterie\\{UNIT}lod0.Ase2ndfbin"
UNIT_DATA = "genglad\\patchable\\gfx\\everything.cpp.gladndfbin"


def unit_data() -> bytes:
    from fixtures import make_ndf, val

    def text(i):
        return val(0x07, struct.pack("<I", i))

    def path(i):
        return val(0x1C, struct.pack("<I", i))

    def ref(index, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))

    def u32(v):
        return val(0x03, struct.pack("<I", v))

    def i32(v):
        return val(0x02, struct.pack("<i", v))

    def listing(*pairs):
        return val(0x12, struct.pack("<I", len(pairs)) + b"".join(text(k) + ref(o, 2) for k, o in pairs))
    strings = ["t_stand", "b_stand", "t_course", "b_course", "t_marche_vise", "b_marche_vise", STAND_FILE, RUN_FILE,
               WALK_FILE, SOLDIER_MODEL, TRUCK_MODEL, "Roues"]
    ndf = make_ndf(objects=[
        (0, [(0, u32(2)), (8, i32(1)), (1, ref(1, 1)), (2, ref(2, 1)), (9, ref(9, 4))]),            # 0 the squad
        (1, [(4, ref(3, 3)), (3, listing((0, 4), (1, 4), (2, 5), (3, 5), (4, 6), (5, 6)))]),      # 1 its rifleman
        (1, [(4, ref(3, 3)), (3, listing((0, 4), (2, 5)))]),                                     # 2 its bazooka man
        (3, [(7, path(9)), (10, u32(524289))]),                                                  # 3 the soldier
        (2, [(5, path(6)), (6, val(0x00, b"\x01"))]),                                            # 4 stand
        (2, [(5, path(7))]),                                                                     # 5 run
        (2, [(5, path(8))]),                                                                     # 6 walk
        (0, [(0, u32(4)), (8, i32(1)), (1, ref(8, 1)), (9, ref(9, 4))]),                         # 7 another squad
        (1, [(4, ref(3, 3)), (3, listing((0, 4), (2, 5)))]),                                     # 8 its rifleman
        (4, [(11, u32(3)), (12, i32(1)), (13, ref(10, 5))]),                                     # 9 the troop truck
        (5, [(14, ref(11, 3)), (15, val(0x12, struct.pack("<I", 1) + text(11) + ref(12, 6)))]),  # 10 its look
        (3, [(7, path(10)), (10, u32(524289))]),                                                 # 11 the truck model
        (6, [])],                                                                                # 12 its wheels
        classes=["TInfanterieDescriptor", "TGfxDescriptorBiped", "TGfxDescriptorAnimation", "TResourceMultiMaterialMesh",
                 "TUniteAuSolDescriptor", "TGfxDescriptorModeleWithAnimation", "TGfxDescriptorRouePack"],
        props=[("DescriptorId", 0), ("GfxDescriptorFusilier", 0), ("GfxDescriptorBazooka", 0), ("ResourceAnimation", 1),
               ("MeshDescriptor", 1), ("FileName", 2), ("PlayInLoop", 2), ("FileName", 3), ("Nationalite", 0),
               ("TransportPourMorphe", 0), ("UsefulnessMask", 3), ("DescriptorId", 4), ("Nationalite", 4),
               ("GfxDescriptor", 4), ("MeshDescriptor", 5), ("SousElements", 5)],
        strings=strings, exports={0: "GFX/Everything/Descriptor_Unit_Squad", 7: "GFX/Everything/Descriptor_Unit_Other",
                                  9: "GFX/Everything/Descriptor_Unit_TransportSoldier"},
        compress=True)
    from fixtures import make_edat
    return make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])


def clips_pack() -> bytes:
    """The made-up game's ZZ_Win.dat: the soldiers' three clips loose, and the units' names in English (a new unit's
    name is a text of the mod's own)."""
    from fixtures import make_edat
    from rusemod.dic import name_to_key
    from test_dic import make_dic
    return make_edat([
        ("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", f"fusilier_{n}lod0.baf", baf.build(clip(lift=k))) for k, n in enumerate(("course", "marche",
                                                                                                "stand"))]),
        ("dir", "genlocalisation\\ww2\\localisation\\translations\\us\\", [
            ("file", "baseunite.dic", make_dic([(name_to_key("SQUAD"), "Rifle squad")]))])])


def own_model(run, order, result):
    """What unit_own_models does for a squad with a model of its own (rusemod.build._own_model_part on a rigged or
    own-bones model): every part naming the soldier's model names the unit's own."""
    from rusemod.unitmodel import model_key
    name = next(n for n, op in run.created.items() if op.kind == "clone" and n.endswith("/" + UNIT))
    build._point_at_copies(run, name, {model_key(SOLDIER_MODEL): OWN_MODEL})
    return {UNIT: (SOLDIER_MODEL, Path("x.glb"), "horse")}


class InTheBuild(unittest.TestCase):
    """build_pack on the made-up game: the unit's own model as unit_own_models leaves it (own_model), the rest real."""

    def mod(self, d, units: str | None = None, animations: dict | None = None, rndf: str | None = None):
        mod = Path(d, "horse")
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "horse"\nversion = "1.0.0"\n', encoding="utf-8")
        (mod / "src" / "units.rndf").write_text(rndf or f"export {UNIT} is clone {E}Descriptor_Unit_Squad ( )\n",
                                                encoding="utf-8")
        if animations:
            anim.set_animations(mod, UNIT, animations)
        if units:
            (mod / anim.UNITS).write_text((mod / anim.UNITS).read_text(encoding="utf-8") + units, encoding="utf-8")
        return mod

    def build(self, mod, with_model: bool = True):
        self.units = unit_data()
        arc, zz = Edat(self.units), Edat(clips_pack())
        mods = [build.load_mod(mod)]
        with mock.patch.object(build, "unit_own_models", own_model if with_model else build.unit_own_models):
            result = build.build_pack(arc, mods, "0", zz)
        objects = build.load_pack(Edat(arc.to_bytes(result.changed))).base.objects if result.changed else None
        return result, objects

    @staticmethod
    def listings(objects, unit, figure="GfxDescriptorFusilier"):
        from rusemod.patch import Inline
        fig = objects[E + unit].props[figure]
        fig = fig.obj if isinstance(fig, Inline) else objects[fig.target]
        out = {}
        for k, v in fig.props["ResourceAnimation"].pairs:
            a = v.obj if isinstance(v, Inline) else objects[v.target]
            out[k.value] = a.props["FileName"].value
        return out

    @staticmethod
    def part(objects, v):
        from rusemod.patch import Inline
        return v.obj if isinstance(v, Inline) else objects[v.target]

    def test_its_figures_play_its_model_s_animations_and_it_rides_as_itself(self):
        with tempfile.TemporaryDirectory() as d:
            walk, run, stand = baf.build(clip(lift=5.0)), baf.build(clip(lift=6.0)), baf.build(clip(lift=7.0))
            mod = self.mod(d, animations={"stand": stand, "walk": walk, "gallop": run})
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            own = {n: anim.own_data_name(f"own_horse_squad_{n}lod0") for n in ("stand", "walk", "gallop")}
            self.assertEqual(self.listings(objects, UNIT), {
                "t_stand": own["stand"], "b_stand": own["stand"], "t_course": own["gallop"], "b_course": own["gallop"],
                "t_marche_vise": own["walk"], "b_marche_vise": own["walk"]})
            self.assertEqual(self.listings(objects, UNIT, "GfxDescriptorBazooka"),
                             {"t_stand": own["stand"], "t_course": own["gallop"]})
            for other in ("Descriptor_Unit_Squad", "Descriptor_Unit_Other"):              # the others: the game's
                self.assertEqual(self.listings(objects, other)["t_stand"], STAND_FILE)
            # the clips: each animation once, as the mod has it
            self.assertEqual({m.rsplit(B, 1)[-1]: Path(s["file"]).name for m, s in result.own_clips.items()},
                             {"own_horse_squad_standlod0.baf": "stand.baf", "own_horse_squad_walklod0.baf": "walk.baf",
                              "own_horse_squad_galloplod0.baf": "gallop.baf"})
            # its ride: a copy of the truck, drawn as its own model playing its gallop on a loop
            ride = objects[E + UNIT].props["TransportPourMorphe"].target
            self.assertEqual(ride, E + f"{UNIT}_Ride")
            truck = objects[E + "Descriptor_Unit_TransportSoldier"]
            self.assertEqual(objects[E + "Descriptor_Unit_Other"].props["TransportPourMorphe"].target,
                             E + "Descriptor_Unit_TransportSoldier")
            look = self.part(objects, objects[ride].props["GfxDescriptor"])
            mesh = self.part(objects, look.props["MeshDescriptor"])
            self.assertEqual((mesh.props["FileName"].value, int(mesh.props["UsefulnessMask"].value)), (OWN_MODEL, 524289))
            self.assertEqual(look.props["SousElements"].pairs, [])
            self.assertEqual(look.props["DefaultAnimation"].value, "idle1")
            [(key, loop)] = look.props["ResourceAnimation"].pairs
            loop = self.part(objects, loop)
            self.assertEqual((key.value, loop.props["FileName"].value, int(loop.props["PlayInLoop"].value)),
                             ("idle1", own["gallop"], 1))
            self.assertNotEqual(objects[ride].props["DescriptorId"].value, truck.props["DescriptorId"].value)
            truck_look = self.part(objects, truck.props["GfxDescriptor"])                 # the truck: as the game's
            self.assertEqual(self.part(objects, truck_look.props["MeshDescriptor"]).props["FileName"].value, TRUCK_MODEL)
            self.assertEqual(len(truck_look.props["SousElements"].pairs), 1)
            said = " ".join(f.message for f in result.findings)
            self.assertIn(f"{UNIT} rides as itself on long moves, playing gallop on a loop", said)
            self.assertIn("play its model's animations (8 listings of 2 figures): stand 3, gallop 3, walk 2", said)

    def test_its_picks_and_a_row_of_its_own(self):
        with tempfile.TemporaryDirectory() as d:
            stand, run, wave = baf.build(clip(lift=1.0)), baf.build(clip(lift=2.0)), baf.build(clip(lift=3.0))
            mod = self.mod(d, animations={"stand": stand, "run": run})
            anim.set_pick(mod, UNIT, "stand", "run")
            anim.set_pick(mod, UNIT, "ride", "stand")
            anim.add_unit_clip(mod, UNIT, "b_stand", wave, name="wave")          # (RUSE Decoy's or a tool's: it wins)
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            got = self.listings(objects, UNIT)
            self.assertEqual((got["t_stand"], got["b_stand"], got["t_marche_vise"]),
                             (anim.own_data_name("own_horse_squad_runlod0"), anim.own_data_name("own_horse_squad_wavelod0"),
                              anim.own_data_name("own_horse_squad_runlod0")))
            self.assertEqual(result.own_rides[UNIT]["animation"], "stand")

    def test_in_its_truck(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, animations={"stand": baf.build(clip()), "run": baf.build(clip(lift=2.0))})
            anim.set_ride(mod, UNIT, "truck")
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(result.own_rides, {})
            self.assertEqual(objects[E + UNIT].props["TransportPourMorphe"].target, E + "Descriptor_Unit_TransportSoldier")
            self.assertNotIn(E + f"{UNIT}_Ride", objects)

    def test_no_model_of_its_own_plays_none_of_them(self):
        """A clip of the model's bones on a figure drawing the game's soldier is what stopped the game on 2026-11-09:
        without its own model in the build, its figures keep the game's clips, said."""
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, animations={"stand": baf.build(clip())})
            result, objects = self.build(mod, with_model=False)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(self.listings(objects, UNIT)["t_stand"], STAND_FILE)
            self.assertEqual((result.own_clips, result.own_rides), ({}, {}))
            self.assertTrue(any(f.level == "warning" and "has animations of its own but no model of its own" in f.message
                                for f in result.findings))

    def test_a_mod_without_them_is_built_as_before(self):
        """No animation table: no ride, no figure pointed, the clips and listings as one unit's own clips had them."""
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d)
            anim.add_unit_clip(mod, UNIT, "t_stand", baf.build(clip(lift=9.0)), name="wave")
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(result.own_rides, {})
            got = self.listings(objects, UNIT)
            self.assertEqual((got["t_stand"], got["b_stand"]), (anim.own_data_name("own_horse_squad_wavelod0"), STAND_FILE))
            self.assertEqual(objects[E + UNIT].props["TransportPourMorphe"].target, E + "Descriptor_Unit_TransportSoldier")


class TheStudio(unittest.TestCase):
    """The action table on a new unit's page, and a copy keeping its source's animations (ruse_studio.actions)."""

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
        self.mod = Path(self.home, "mods", "horse")
        (self.mod / "src").mkdir(parents=True)
        (self.mod / "mod.toml").write_text('[mod]\nid = "horse"\nversion = "1.0.0"\n', encoding="utf-8")
        self.api.choose_mod(str(self.mod))

    def horse(self, animations: dict) -> str:
        """A new unit made from the squad, with a model of its own (its record as Import model writes it) and
        `animations`."""
        address = self.api.new_unit(E + "Descriptor_Unit_Squad", "Horse Squad", 5)["address"]
        models = self.mod / "files" / "models"
        models.mkdir(parents=True, exist_ok=True)
        (models / f"{UNIT}.glb").write_bytes(b"glTF")
        (models / f"{UNIT}.json").write_text(json.dumps({"from": "horse.glb", "size": 1.0, "report": {
            "like": SOLDIER_MODEL.lower(), "also": [], "rigged": True}}), encoding="utf-8")
        anim.set_animations(self.mod, UNIT, animations)
        return address

    def test_the_table(self):
        address = self.horse({"stand": baf.build(clip()), "gallop": baf.build(clip(lift=2.0, frames=16, seconds=0.5))})
        got = self.api.unit_actions(address)
        self.assertTrue(got["own"])
        self.assertEqual([(a["name"], a["seconds"], a["frames"]) for a in got["animations"]],
                         [("stand", 1.0, 31), ("gallop", 0.5, 16)])
        rows = {r["action"]: r for r in got["rows"]}
        self.assertEqual(sorted(rows), ["course", "marche_vise", "stand"])
        self.assertEqual((rows["stand"]["how"], rows["stand"]["plays"]), ("named", {"top": "stand", "bottom": "stand"}))
        self.assertEqual((rows["course"]["how"], rows["course"]["plays"]["top"]), ("named", "gallop"))
        self.assertEqual(rows["marche_vise"]["plays"], {"top": "gallop", "bottom": "gallop"})
        self.assertEqual(got["missing"], [])     # (no walk listed alone in this made-up squad: only its aim)
        self.assertEqual({k: got["ride"][k] for k in ("can", "itself", "plays", "how")},
                         {"can": True, "itself": True, "plays": "gallop", "how": "nearest"})
        got = self.api.unit_action_set(address, "stand", "gallop")
        stand = next(r for r in got["rows"] if r["action"] == "stand")
        self.assertEqual((stand["picked"], stand["how"], stand["nearest"]), ("gallop", "picked", {"top": "stand", "bottom": "stand"}))
        got = self.api.unit_action_set(address, "stand", None)
        self.assertIsNone(next(r for r in got["rows"] if r["action"] == "stand")["picked"])
        got = self.api.unit_ride_set(address, "truck")
        self.assertFalse(got["ride"]["itself"])
        got = self.api.unit_ride_set(address, "stand")
        self.assertEqual((got["ride"]["itself"], got["ride"]["picked"]), (True, "stand"))
        units = anim.read_units(self.mod)[UNIT]
        self.assertEqual((units.get("ride"), units["plays"]), (None, {"ride": "stand"}))
        from ruse_studio.api import StudioError
        for args in (("stand", "trot"), ("fly_away", "stand")):
            with self.subTest(args=args), self.assertRaises(StudioError):
                self.api.unit_action_set(address, *args)
        with self.assertRaises(StudioError):
            self.api.unit_ride_set(address, "trot")

    def test_no_table_without_them(self):
        self.assertEqual(self.api.unit_actions(E + "Descriptor_Unit_Squad"), {"own": False})   # one of the game's
        address = self.api.new_unit(E + "Descriptor_Unit_Squad", "Plain Squad", 5)["address"]
        self.assertEqual(self.api.unit_actions(address), {"own": False})                       # no model, no animations

    def test_a_copy_plays_the_same_animations(self):
        """The owner, 2026-11-10: "when you copy ... They should have the same animation. The only way you should
        change animation is in Ruse Decoy": the game squad's own clip (RUSE Decoy's Only this unit) goes along with a
        copy, and the build gives both the same clip, each its own file."""
        wave = baf.build(clip(lift=4.0))
        anim.add_unit_clip(self.mod, "Descriptor_Unit_Squad", "t_stand", wave, name="wave")
        made = self.api.new_unit(E + "Descriptor_Unit_Squad", "GI Strong", 5)
        self.assertTrue(made["animations_kept"])
        copy = made["address"].rsplit("/", 1)[-1]
        units = anim.read_units(self.mod)
        self.assertEqual(units[copy], units["Descriptor_Unit_Squad"])
        self.assertEqual((self.mod / anim.OWN / copy / "wave.baf").read_bytes(), wave)
        self.assertFalse(self.api.new_unit(E + "Descriptor_Unit_Other", "Other Copy", 5)["animations_kept"])
        result = build.build_pack(Edat(unit_data()), [build.load_mod(self.mod)], "0", Edat(clips_pack()))
        self.assertEqual([f.message for f in result.errors], [])
        made_from = {s["unit"]: Path(s["file"]).read_bytes() for s in result.own_clips.values()}
        self.assertEqual(made_from, {"Descriptor_Unit_Squad": wave, copy: wave})

    def test_a_broken_units_toml_stops_a_copy_before_anything_is_made(self):
        from ruse_studio.api import StudioError
        (self.mod / anim.UNITS).parent.mkdir(parents=True, exist_ok=True)
        (self.mod / anim.UNITS).write_text("[unit.X.clip\n", encoding="utf-8")
        with self.assertRaisesRegex(StudioError, "Fix that file"):
            self.api.new_unit(E + "Descriptor_Unit_Squad", "Broken", 5)
        made = self.mod / "src" / "studio.rndf"
        self.assertNotIn("Broken", made.read_text(encoding="utf-8") if made.is_file() else "")


class ThePage(unittest.TestCase):
    """The action table's words in all eleven languages, its calls on the page and in the browser preview."""

    def test_words_and_calls(self):
        ui = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
        app, fake = (ui / "app.js").read_text(encoding="utf-8"), (ui / "fake-api.js").read_text(encoding="utf-8")
        words = tomllib.loads((ui.parent / "words.toml").read_text(encoding="utf-8"))
        langs = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
        used = set(re.findall(r"\bw\.((?:tip_)?actions_\w+|act_\w+)", app))
        used |= {f"act_{a}" for a in aa.ACTIONS} | {f"act_section_{s}" for s in aa.SECTIONS if s != "ride"}
        self.assertGreater(len(used), 80)
        blank = re.compile(r"\{(\w+)\}")
        for key in sorted(used):
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), set(langs))
                for lang in langs:
                    self.assertEqual(sorted(blank.findall(words[key][lang])), sorted(blank.findall(words[key]["us"])),
                                     lang)
        for call in ("unit_actions", "unit_action_set", "unit_ride_set"):
            self.assertIn(f"api().{call}(" if call == "unit_actions" else f'"{call}"', app)
            self.assertIn(f"{call}: async", fake)


if __name__ == "__main__":
    unittest.main()
