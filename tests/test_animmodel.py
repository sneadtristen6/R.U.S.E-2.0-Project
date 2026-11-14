"""A model on bones of its own and its animations, from Import model to the build (rusemod.animmodel; the Studio's
ruse_studio.animmodel_calls): which actions each animation plays by its name, what the file says of itself, the split
of the two halves, the unit's own clips and rows kept (and kept again when the model comes back), the model's file
keeping its animations, the build pointing the figures that wear the model at its own two masks, and the Studio's
import telling such a model from one on the game soldier's bones."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import base64
import hashlib
import json
import sqlite3
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from rusemod import anim, animmodel, baf, modelin, rig, unitmodel
from rusemod.modelin import OWN_SKELETON
from test_ownrig import little_glb, rig_of_bytes, turn_about

E = "$/GFX/Everything/"
SQUAD_ACTIONS = ["t_stand", "b_stand", "t_marche", "b_marche", "t_course", "b_course", "t_tir", "b_tir",
                 "t_mort_balle", "b_mort_balle", "t_stand_vise", "b_stand_vise", "t_tir_secondaire", "t_mort", "b_mort"]


def walk_glb(names=("Walk", "Run", "Idle"), extras=None, halves=None) -> bytes:
    """The little three-bone model of test_ownrig with an animation for each of `names` (Hips moved, a second long);
    `extras`: {animation name: its extras}; `halves`: the asset's rusemod_halves."""
    anims = [(n, [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, 0.1 * (k + 1))], "LINEAR")])
             for k, n in enumerate(names)]
    data = little_glb(anims)
    if not extras and not halves:
        return data
    doc, binary = modelin.glb_document(data)
    for a in doc["animations"]:
        if a["name"] in (extras or {}):
            a["extras"] = extras[a["name"]]
    if halves:
        doc["asset"]["extras"] = {animmodel.HALVES_EXTRA: halves}
    from rusemod.gltf import _Glb
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    return g.to_bytes()


class TheNameRule(unittest.TestCase):
    def test_plain_words_both_halves(self):
        got = animmodel.actions_named(SQUAD_ACTIONS, ["Walk", "Armature|Run", "Idle", "Death", "Fire", "Gallop"])
        self.assertEqual((got["t_marche"], got["b_marche"]), ("Walk", "Walk"))
        self.assertEqual((got["t_course"], got["b_course"]), ("Armature|Run", "Armature|Run"))   # Blender's object left off
        self.assertEqual((got["t_stand"], got["b_stand"]), ("Idle", "Idle"))
        self.assertEqual((got["t_mort"], got["b_mort"]), ("Death", "Death"))       # the game's word alone: the fallen figure
        self.assertIsNone(got["t_mort_balle"])                                      # its other deaths: the nearest's (part 2)
        self.assertEqual((got["t_tir"], got["b_tir"]), ("Fire", "Fire"))
        self.assertNotIn("Gallop", got.values())                                    # named for nothing: plays nothing yet

    def test_the_game_s_names_and_halves(self):
        got = animmodel.actions_named(SQUAD_ACTIONS, ["stand", "t_stand", "b_walk", "mort_balle", "stand_vise", "grenade"])
        self.assertEqual(got["t_stand"], "t_stand")              # a name with the action's half first
        self.assertEqual(got["b_stand"], "stand")                # the other half: the name without one
        self.assertEqual(got["b_marche"], "b_walk")              # a plain word for one half
        self.assertIsNone(got["t_marche"])
        self.assertEqual((got["t_mort_balle"], got["b_mort_balle"]), ("mort_balle", "mort_balle"))
        self.assertEqual(got["t_stand_vise"], "stand_vise")
        self.assertEqual(got["t_tir_secondaire"], "grenade")

    def test_a_start_every_name_shares_is_left_off(self):
        got = animmodel.actions_named(SQUAD_ACTIONS, ["horse_stand", "horse_walk", "horse_run"])
        self.assertEqual((got["t_stand"], got["b_marche"], got["t_course"]), ("horse_stand", "horse_walk", "horse_run"))
        got = animmodel.actions_named(SQUAD_ACTIONS, ["hr_t_stand", "hr_b_stand", "hr_b_walk"])
        self.assertEqual((got["t_stand"], got["b_stand"], got["b_marche"]), ("hr_t_stand", "hr_b_stand", "hr_b_walk"))
        self.assertIsNone(got["t_marche"])
        got = animmodel.actions_named(SQUAD_ACTIONS, ["t_stand", "t_tir"])     # a half isn't a shared start
        self.assertEqual((got["t_stand"], got["t_tir"], got["b_stand"]), ("t_stand", "t_tir", None))
        self.assertIsNone(animmodel.actions_named(["t_marche"], ["horse_walk"])["t_marche"])   # one name: kept whole

    def test_what_the_file_says_comes_first(self):
        said = [["t_stand", "t_marche"], None]
        got = animmodel.actions_named(SQUAD_ACTIONS, ["hold", "walk"], said)
        self.assertEqual((got["t_stand"], got["t_marche"], got["b_marche"]), ("hold", "hold", "walk"))

    def test_clip_names_are_own_clips_names(self):
        r = rig_of_bytes(walk_glb(("Walk", "Walk", "Run")))
        clips, _notes = unitmodel.own_clips(r)
        self.assertEqual(animmodel.clip_names(r), list(clips))
        self.assertEqual(list(clips), ["Walk", "Walk 2", "Run"])


class WhatTheFileSays(unittest.TestCase):
    def test_actions_and_halves(self):
        data = walk_glb(("Walk", "Run"), extras={"Run": {animmodel.ACTIONS_EXTRA: ["t_course", "b_course"]}},
                        halves={"top": ["Spine", "Head"], "bottom": ["Hips"]})
        r = rig_of_bytes(data)
        doc, _b = modelin.glb_document(data)
        said, halves = animmodel.file_says(doc, [a.name for a in r.animations])
        self.assertEqual(said, [None, ["t_course", "b_course"]])
        self.assertEqual(halves, {"top": ["spine", "head"], "bottom": ["hips"]})
        record = r.record()
        self.assertEqual(animmodel.split_of(record, halves), "spine")
        self.assertIsNone(animmodel.split_of(record, {"top": ["hips", "head"], "bottom": ["spine"]}))   # not one bone's
        self.assertIsNone(animmodel.split_of(record, {"top": ["spine"], "bottom": ["hips"]}))           # head left out

    def test_the_halves_split_where_the_record_says(self):
        record = rig_of_bytes(walk_glb()).record()
        got, notes = animmodel.halves_for(record, "spine")
        self.assertEqual((sorted(got["top"]["Weights"]), sorted(got["bottom"]["Weights"])), (["head", "spine"], ["hips"]))
        self.assertEqual(notes, [])
        # (item 5's merge: nothing chosen splits at rusemod.bonefit's suggestion, here the spine, as the page shows)
        got, notes = animmodel.halves_for(record, None)
        self.assertEqual((sorted(got["top"]["Weights"]), sorted(got["bottom"]["Weights"])), (["head", "spine"], ["hips"]))
        self.assertEqual(notes, [])
        got, notes = animmodel.halves_for(record, "tail")                # a bone it hasn't got: said, the suggested one
        self.assertEqual(sorted(got["top"]["Weights"]), ["head", "spine"])
        self.assertTrue(any("tail" in n and "spine" in n for n in notes))


class TheUnitsOwnClips(unittest.TestCase):
    UNIT = "Descriptor_Unit_Beast"

    def clips(self, names=("Walk", "Run", "Idle")):
        r = rig_of_bytes(walk_glb(names))
        return unitmodel.own_clips(r)[0]

    def test_kept_with_rows_for_the_actions_named(self):
        with tempfile.TemporaryDirectory() as d:
            clips = self.clips()
            kept = animmodel.keep_animations(d, self.UNIT, clips, SQUAD_ACTIONS)
            own = Path(d, anim.OWN, self.UNIT)
            self.assertEqual(sorted(p.name for p in own.iterdir()), ["Idle.baf", "Run.baf", "Walk.baf"])
            self.assertEqual((own / "Walk.baf").read_bytes(), clips["Walk"])
            rows = anim.read_units(d)[self.UNIT]["action"]
            self.assertEqual((rows["t_marche"], rows["b_marche"], rows["t_stand"]), ("Walk.baf", "Walk.baf", "Idle.baf"))
            self.assertNotIn("t_tir", rows)
            self.assertEqual(kept["actions"]["t_course"], "Run")
            self.assertIsNone(kept["actions"]["t_tir"])                  # empty: shown so in the record
            self.assertEqual([a["file"] for a in kept["animations"]], ["Walk.baf", "Run.baf", "Idle.baf"])
            self.assertEqual(kept["animations"][0]["frames"], 31)
            got = anim.mod_unit_clips(d)[self.UNIT]["actions"]           # as the build reads them
            self.assertEqual(got[("t_marche", None)].name, "Walk.baf")

    def test_brought_back_keeps_the_choices_still_there(self):
        with tempfile.TemporaryDirectory() as d:
            first = animmodel.keep_animations(d, self.UNIT, self.clips(), SQUAD_ACTIONS)
            table = anim.read_units(d)
            table[self.UNIT]["action"]["t_tir"] = "Run.baf"              # a choice made after the import (part 2's)
            table[self.UNIT]["action"]["t_stand"] = "Walk.baf"
            decoy = Path(d, anim.OWN, self.UNIT, "genanim_15", "x.baf")  # one of the unit's own clips made elsewhere
            decoy.parent.mkdir(parents=True)
            decoy.write_bytes(self.clips()["Walk"])
            table[self.UNIT]["action"]["t_hit"] = "genanim_15/x.baf"
            anim.write_units(d, table)
            again = animmodel.keep_animations(d, self.UNIT, self.clips(("Walk", "Gallop")), SQUAD_ACTIONS + ["t_hit"],
                                              before=first["animations"])
            rows = anim.read_units(d)[self.UNIT]["action"]
            self.assertEqual(rows["t_stand"], "Walk.baf")                # the choice kept: Walk came back
            self.assertNotIn("t_tir", rows)                              # Run didn't: its choice went
            self.assertNotIn("t_course", rows)
            self.assertEqual(rows["t_hit"], "genanim_15/x.baf")          # another clip's row as it was
            self.assertIn(("t_tir", "Run"), again["dropped"])
            own = Path(d, anim.OWN, self.UNIT)
            self.assertEqual(sorted(p.name for p in own.iterdir() if p.is_file()), ["Gallop.baf", "Walk.baf"])
            self.assertTrue(decoy.is_file())
            self.assertEqual(again["actions"]["t_hit"], "genanim_15/x.baf")
            out = animmodel.drop_animations(d, self.UNIT, again["animations"])   # the model taken out
            self.assertIn("t_stand", out)
            self.assertEqual(anim.read_units(d)[self.UNIT]["action"], {"t_hit": "genanim_15/x.baf"})
            self.assertEqual(sorted(p.name for p in own.iterdir() if p.is_file()), [])
            self.assertTrue(decoy.is_file())

    def test_file_names_never_clash(self):
        names = animmodel.file_names(["Walk", "walk", "Run!", "???"], reserved={"run.baf"})
        self.assertEqual(names, {"Walk": "Walk.baf", "walk": "walk_2.baf", "Run!": "Run_2.baf", "???": "animation.baf"})

    def test_a_bad_clip_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(animmodel.AnimModelError):
                animmodel.keep_animations(d, self.UNIT, {"Walk": b"not a clip"}, SQUAD_ACTIONS)
            self.assertFalse(Path(d, anim.UNITS).exists())
            self.assertFalse(Path(d, anim.OWN).exists())


class TheModelsFile(unittest.TestCase):
    def test_import_keeps_every_animation_in_the_file(self):
        from test_unitmodel import TANK, zz_win
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "beast.glb")
            src.write_bytes(walk_glb(("Walk", "Pose")))
            out = Path(d, "files", "models", "Beast.glb")
            clips: dict = {}
            arc = zz_win()
            with mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
                report = unitmodel.import_model(Path("game"), TANK, src, out, own_bones=True, clips=clips)
            back = rig.read_rig(out)
            again, _notes = unitmodel.own_clips(back, unitmodel.own_record(unitmodel.read_mod_glb(out).report))
            made_from, in_its_file = hashlib.sha256(src.read_bytes()).hexdigest(), unitmodel.read_mod_glb(out).report
        self.assertEqual(list(clips), ["Walk", "Pose"])
        self.assertEqual([a["name"] for a in report[OWN_SKELETON]["animations"]], ["Walk", "Pose"])
        self.assertEqual([a.name for a in back.animations], ["Walk", "Pose"])
        for name in clips:          # the file's animations give the same clips again
            self.assertEqual(again[name], clips[name], name)
        # (the bytes it was made from, known again by the report the Studio keeps: the Generic Horse's files,
        # ruse_studio.horse_squad; never in the model file written)
        self.assertEqual(report[unitmodel.SOURCE_SHA], made_from)
        self.assertNotIn(unitmodel.SOURCE_SHA, in_its_file)

    def test_a_one_frame_pose_stays_one_frame(self):
        r = rig_of_bytes(little_glb([("Pose", [(2, "rotation", [0.0], [turn_about("x", 45.0)], "LINEAR")])]))
        record = r.record()
        clips, _n = unitmodel.own_clips(r, record)
        from rusemod.gltf import _Glb
        g = _Glb()
        sk = baf.skeleton(record)
        holder = modelin._own_bones(g, sk, base64.b64encode(record).decode("ascii"), "m")
        modelin._own_animations(g, sk, holder - sk["bones"], clips)
        g.doc["scenes"], g.doc["scene"] = [{"nodes": [holder]}], 0
        back = rig_of_bytes(g.to_bytes())
        again, _n = unitmodel.own_clips(back, record)
        self.assertEqual(baf.parse(again["Pose"]).frames, 1)
        self.assertEqual(again["Pose"], clips["Pose"])


# --- the build: a made-up squad whose figure lists its clips through the game's two masks ---
MODEL_FILE = "WW2\\Res3D\\Units\\GER\\Tank\\GER_PanzerIVlod0.Ase2NdfBin"   # (test_unitmodel's zz_win model)
STAND = "WW2\\Res3D\\Units\\Common\\Fusilier_standlod0.Ase2NdfBin"


def squad_pack() -> bytes:
    """Unit data as the game's infantry has it: Descriptor_Unit_Squad's figure (wearing MODEL_FILE) lists t_stand,
    b_stand, t_tir and b_tir, each listing an object of its own naming the game's top or bottom mask, objects every
    listing of that half shares (MaskUnionCode 65280, AnimationSlot 1 / 255, Weights naming the soldier's bones), and
    a mask that names none (the parachute's) on t_para; Descriptor_Unit_Other shares the figure."""
    def text(i):
        return val(0x07, struct.pack("<I", i))

    def ref(index, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))

    def u32(n):
        return val(0x03, struct.pack("<I", n))

    def f32(x):
        return val(0x05, struct.pack("<f", x))

    def amap(*pairs):
        return val(0x12, struct.pack("<I", len(pairs)) + b"".join(k + v for k, v in pairs))
    strings = ["t_stand", "b_stand", "t_tir", "t_para", MODEL_FILE, STAND, "Bip01", "Bip01 Spine", "b_tir"]
    objects = [
        (0, [(0, u32(2)), (10, val(0x02, struct.pack("<i", 1))), (1, ref(1, 1))]),                        # 0 the squad
        (1, [(3, ref(2, 3)), (2, amap((text(0), ref(3, 2)), (text(1), ref(4, 2)), (text(2), ref(5, 2)),
                                      (text(8), ref(11, 2)), (text(3), ref(9, 2))))]),                     # 1 its figure
        (3, [(6, val(0x1C, struct.pack("<I", 4)))]),                                                     # 2 its mesh
        (2, [(4, val(0x1C, struct.pack("<I", 5))), (5, ref(6, 4))]),                                       # 3 t_stand
        (2, [(4, val(0x1C, struct.pack("<I", 5))), (5, ref(7, 4))]),                                       # 4 b_stand
        (2, [(4, val(0x1C, struct.pack("<I", 5))), (5, ref(6, 4))]),                                       # 5 t_tir
        (4, [(7, u32(65280)), (8, val(0x02, struct.pack("<i", 1))),
             (9, amap((text(6), f32(0.0)), (text(7), f32(1.0))))]),                                        # 6 top mask
        (4, [(7, u32(255)), (9, amap((text(6), f32(1.0)), (text(7), f32(0.0))))]),                         # 7 bottom mask
        (4, [(7, u32(65535)), (11, f32(1.0))]),                                                            # 8 parachute's
        (2, [(4, val(0x1C, struct.pack("<I", 5))), (5, ref(8, 4))]),                                       # 9 t_para
        (0, [(0, u32(4)), (10, val(0x02, struct.pack("<i", 1))), (1, ref(1, 1))]),                        # 10 the other
        (2, [(4, val(0x1C, struct.pack("<I", 5))), (5, ref(7, 4))])]                                       # 11 b_tir
    ndf = make_ndf(objects=objects,
                   classes=["TInfanterieDescriptor", "TGfxDescriptorBiped", "TGfxDescriptorAnimation",
                            "TResourceMultiMaterialMesh", "THierarchicalASEModelSkeletonMask"],
                   props=[("DescriptorId", 0), ("GfxDescriptorFusilier", 0), ("ResourceAnimation", 1),
                          ("MeshDescriptor", 1), ("FileName", 2), ("Mask", 2), ("FileName", 3), ("MaskUnionCode", 4),
                          ("AnimationSlot", 4), ("Weights", 4), ("Nationalite", 0), ("DefaultWeight", 4)],
                   strings=strings, exports={0: "GFX/Everything/Descriptor_Unit_Squad",
                                             10: "GFX/Everything/Descriptor_Unit_Other"}, compress=True)
    return make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])


class TheBuild(unittest.TestCase):
    UNIT = "Descriptor_Unit_Beast"

    def mod(self, d, own_bones=True, split=None, rows=True):
        """A mod making Descriptor_Unit_Beast from the squad, with its own model: the little three-bone one on bones
        of its own (Import model's way), or the same rigged to the copied model's bones."""
        from test_unitmodel import TANK, zz_win
        mod = Path(d, "mod")
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
        (mod / "src" / "units.rndf").write_text(f"export {self.UNIT} is clone {E}Descriptor_Unit_Squad "
                                                f"( DescriptorId = 3 )\n", encoding="utf-8")
        src = Path(d, "beast.glb")
        src.write_bytes(walk_glb(("Walk", "Idle")))
        out = mod / "files" / "models" / f"{self.UNIT}.glb"
        clips: dict = {}
        arc = zz_win()
        with mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
            report = unitmodel.import_model(Path("game"), TANK, src, out, own_bones=own_bones, clips=clips)
        record = {"report": report, **({"split": split} if split else {})}
        out.with_suffix(".json").write_text(json.dumps(record), encoding="utf-8")
        if rows and clips:
            animmodel.keep_animations(mod, self.UNIT, clips, ["t_stand", "b_stand", "t_tir"])
        return mod

    def build(self, mod, pack=None):
        from rusemod.build import build_pack, load_mod
        from rusemod.edat import Edat
        from test_unitmodel import zz_win
        return build_pack(Edat(pack or squad_pack()), [load_mod(mod)], text_arc=zz_win())

    @staticmethod
    def figure(objects, unit):
        from rusemod.patch import Inline
        fig = objects[E + unit].props["GfxDescriptorFusilier"]
        return fig.obj if isinstance(fig, Inline) else objects[fig.target]

    def listings(self, objects, unit):
        """{action: (FileName, the mask's name or None for an unnamed one, its Weights {name: weight})}."""
        from rusemod.patch import Inline, Ref
        out = {}
        for k, v in self.figure(objects, unit).props["ResourceAnimation"].pairs:
            a = v.obj if isinstance(v, Inline) else objects[v.target]
            m = a.props.get("Mask")
            mask = m.obj if isinstance(m, Inline) else objects.get(m.target) if isinstance(m, Ref) else None
            w = mask.props.get("Weights") if mask is not None else None
            out[k.value] = (a.props["FileName"].value, m.target if isinstance(m, Ref) else None,
                            {x.value: float(y.value) for x, y in w.pairs} if w is not None else None)
        return out

    def test_its_figures_play_through_its_own_halves(self):
        from rusemod.model import load
        with tempfile.TemporaryDirectory() as d:
            result = self.build(self.mod(d, split="spine"))
        self.assertEqual(result.errors, [])
        game, _files = load(result.changed)
        mine, theirs = self.listings(game.objects, self.UNIT), self.listings(game.objects, "Descriptor_Unit_Squad")
        top, bottom = E + f"Mask_{self.UNIT}_Top", E + f"Mask_{self.UNIT}_Bottom"
        self.assertEqual([mine[a][1] for a in ("t_stand", "b_stand", "t_tir", "b_tir")], [top, bottom, top, bottom])
        self.assertEqual(mine["t_stand"][2], {"spine": 1.0, "head": 1.0})
        self.assertEqual(mine["b_stand"][2], {"hips": 1.0})
        self.assertEqual(mine["t_para"][2], None)                         # a mask naming no bone stays
        top_obj = game.objects[top]
        self.assertEqual((int(top_obj.props["MaskUnionCode"].value), int(top_obj.props["AnimationSlot"].value)), (65280, 1))
        self.assertEqual(int(game.objects[bottom].props["MaskUnionCode"].value), 255)
        self.assertNotIn("AnimationSlot", game.objects[bottom].props)
        for action in ("t_stand", "b_stand", "t_tir", "b_tir"):           # the game's units as they were
            low = action.startswith("b_")
            self.assertEqual(theirs[action][2], {"Bip01": 1.0 if low else 0.0, "Bip01 Spine": 0.0 if low else 1.0})
        self.assertEqual(self.listings(game.objects, "Descriptor_Unit_Other"), theirs)
        self.assertEqual(mine["t_stand"][0], anim.own_data_name(anim.own_stem(self.UNIT, "Idle.baf")))   # its own clips
        self.assertTrue(any("split at spine" in f.message for f in result.findings if f.level == "note"))

    def test_nothing_chosen_split_at_the_suggested_bone(self):
        """(item 5's merge) No split chosen: the build splits where rusemod.bonefit suggests, as the page shows it."""
        from rusemod.model import load
        with tempfile.TemporaryDirectory() as d:
            result = self.build(self.mod(d))
        self.assertEqual(result.errors, [])
        game, _files = load(result.changed)
        mine = self.listings(game.objects, self.UNIT)
        self.assertEqual(mine["t_stand"][2], {"spine": 1.0, "head": 1.0})
        self.assertEqual(mine["b_stand"][2], {"hips": 1.0})
        self.assertTrue(any("split at spine" in f.message for f in result.findings if f.level == "note"))

    def test_a_model_on_the_game_s_bones_builds_as_before(self):
        """The step changes nothing for a unit whose model is rigged to the copied model's own bones (item 4's way):
        the unit data byte for byte as the build gives it with the step left out."""
        from rusemod import build
        from test_unitmodel import TANK
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, rows=False)
            mesh = modelin.Mesh("soldier", [(0.1, 0.2, 0.3), (0.4, 0.2, 0.3), (0.1, 0.5, 0.3)], [(0, 1, 2)],
                                [(0.25, 0.5), (0.75, 0.5), (0.25, 1.0)], [-1], [(0.0, 0.0, 1.0)] * 3,
                                skin=[[("chassis", 255)]] * 3, tracks=[], draw=0, static=False)
            prep = modelin.prepare(modelin.Model([mesh], [], "m.glb"), [], {"rigged": True, "root": "chassis"})
            out = mod / "files" / "models" / f"{self.UNIT}.glb"
            modelin.write_glb(prep, out, TANK)
            out.with_suffix(".json").write_text(json.dumps({"report": prep.report, "skeleton": "soldier"}),
                                                encoding="utf-8")
            with_step = self.build(mod)
            with mock.patch.object(build, "unit_own_halves", lambda run, result: None):
                without = self.build(mod)
        self.assertEqual(with_step.errors, [])
        self.assertIn(self.UNIT, with_step.own_models)
        self.assertEqual(with_step.changed, without.changed)
        self.assertEqual(with_step.fingerprint, without.fingerprint)


# --- the Studio ---
class StudioImport(unittest.TestCase):
    ADDRESS = E + "Descriptor_Unit_Beast"

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda: self.mod
        self.api._look_models = lambda address: (["the rifleman", "the bazooka man"], [])
        self.target = self.mod / "files" / "models" / "Descriptor_Unit_Beast.glb"
        self.api._own_model_file = lambda address: self.target
        self.api._own_copy_file = lambda address: None
        self.api._model_actions = lambda address, report: list(SQUAD_ACTIONS)
        self.api.look = lambda address: {"new_unit": True}
        self.src = root / "beast.glb"

    def tearDown(self):
        self.dir.cleanup()

    def fake_import(self, own_on="the rifleman"):
        """import_model as the game's packs would answer: the unit's models take no model of other bones; on bones of
        its own, the real import on test_unitmodel's made-up packs."""
        from rusemod.unitmodel import UnitModelError
        from test_unitmodel import TANK, zz_win
        real = unitmodel.import_model
        calls = []

        def fake(game, model, file, out, own_bones=False, clips=None, **kw):
            calls.append((model, own_bones, kw.get("others")))
            if not own_bones:
                raise UnitModelError(f"its bones aren't {model}'s: hips, spine")
            arc = zz_win()
            with mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
                return real(Path("game"), TANK, file, out, own_bones=True, clips=clips, others=kw.get("others"))
        return fake, calls

    def test_a_model_on_bones_of_its_own_comes_in_with_its_animations(self):
        self.src.write_bytes(walk_glb(("Walk", "Run", "Idle"), halves={"top": ["Spine", "Head"], "bottom": ["Hips"]}))
        fake, calls = self.fake_import()
        with mock.patch("rusemod.unitmodel.import_model", fake), \
                mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)), \
                mock.patch("rusemod.animmodel.own_bones_on", lambda game, path, models: models[0]):
            res = self.api.model_import(self.ADDRESS, str(self.src))
        self.assertEqual([c[:2] for c in calls], [("the rifleman", False), ("the bazooka man", False), ("the rifleman", True)])
        model = res["model"]
        self.assertEqual(model[OWN_SKELETON]["bones"], 3)
        record = json.loads(self.target.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(record["skeleton"], "own")
        self.assertEqual(record["bones"], ["hips", "spine", "head"])
        self.assertEqual([(a["name"], a["frames"], a["file"]) for a in record["animations"]],
                         [("Walk", 31, "Walk.baf"), ("Run", 31, "Run.baf"), ("Idle", 31, "Idle.baf")])
        self.assertEqual(record["split"], "spine")                        # where the file's own halves meet
        # (item 5's merge: the animations go into Part 2's table, which the action table picks from and the build
        # plays the nearest of; no row per action)
        own = anim.own_animations(self.mod, "Descriptor_Unit_Beast")
        self.assertEqual(own["animations"], {"Walk": "Walk.baf", "Run": "Run.baf", "Idle": "Idle.baf"})
        self.assertNotIn("action", anim.read_units(self.mod)["Descriptor_Unit_Beast"])
        page = self.api.model_animations(self.ADDRESS)
        self.assertEqual((page["own"], page["bones"], page["split"]), (True, 3, "spine"))
        self.assertEqual({k: page["animations"][0][k] for k in ("name", "seconds", "frames")},
                         {"name": "Walk", "seconds": 1.0, "frames": 31})
        # taken out: its animations go with it
        self.api.model_import_remove(self.ADDRESS)
        self.assertEqual(anim.own_animations(self.mod, "Descriptor_Unit_Beast")["animations"], {})
        self.assertEqual(list(Path(self.mod, anim.OWN, "Descriptor_Unit_Beast").glob("*.baf")), [])
        self.assertEqual(self.api.model_animations(self.ADDRESS), {"own": False})

    def test_imported_again_it_keeps_what_was_chosen(self):
        """The same model brought back (Bring back the model, or Import model again): the halves chosen on the page and
        an action given another animation stay; an animation taken out of the file is taken off its actions."""
        self.src.write_bytes(walk_glb(("Walk", "Run", "Idle"), halves={"top": ["Spine", "Head"], "bottom": ["Hips"]}))
        fake, _calls = self.fake_import()
        patches = (mock.patch("rusemod.unitmodel.import_model", fake),
                   mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)),
                   mock.patch("rusemod.animmodel.own_bones_on", lambda game, path, models: models[0]))
        with patches[0], patches[1], patches[2]:
            self.api.model_import(self.ADDRESS, str(self.src))
            path = self.target.with_suffix(".json")
            record = json.loads(path.read_text(encoding="utf-8"))
            path.write_text(json.dumps(dict(record, split="head")), encoding="utf-8")       # chosen on the page
            anim.set_pick(self.mod, "Descriptor_Unit_Beast", "tir", "Run")                 # picked in the table
            anim.set_pick(self.mod, "Descriptor_Unit_Beast", "marche", "Walk")
            self.src.write_bytes(walk_glb(("Walk", "Idle"), halves={"top": ["Spine", "Head"], "bottom": ["Hips"]}))
            self.api.model_import(self.ADDRESS, str(self.src))
        record = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(record["split"], "head")
        plays = anim.own_animations(self.mod, "Descriptor_Unit_Beast")["plays"]
        self.assertNotIn("tir", plays)                                    # Run went with its file: the nearest again
        self.assertEqual(plays["marche"], "Walk")

    def test_a_model_on_the_game_soldier_s_bones_goes_on_as_before(self):
        self.src.write_bytes(walk_glb())
        written = []

        def fake(game, model, file, out, own_bones=False, clips=None, **kw):
            written.append(own_bones)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"glTF")
            return {"rigged": True, "like": model, "also": []}
        with mock.patch("rusemod.unitmodel.import_model", fake), \
                mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)):
            self.api.model_import(self.ADDRESS, str(self.src))
        self.assertEqual(written, [False])
        record = json.loads(self.target.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual((record["skeleton"], record["animations"]), ("soldier", []))
        self.assertEqual(self.api.model_animations(self.ADDRESS), {"own": False})

    def test_a_file_none_of_the_models_takes_says_why(self):
        from ruse_studio.api import StudioError
        self.src.write_bytes(walk_glb())
        fake, _calls = self.fake_import()
        with mock.patch("rusemod.unitmodel.import_model", fake), \
                mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)), \
                mock.patch("rusemod.animmodel.own_bones_on", lambda game, path, models: None):
            with self.assertRaisesRegex(StudioError, "its bones aren't the rifleman's"):
                self.api.model_import(self.ADDRESS, str(self.src))
        self.assertFalse(self.target.exists())


class OwnBonesOn(unittest.TestCase):
    def test_which_model_it_takes_the_place_of(self):
        from types import SimpleNamespace
        from rusemod.unitmodel import UnitModelError
        bones = {"rifle": ["bip01", "bip01 spine"], "bazooka": ["bip01", "bip01 spine"], "flat": None}

        def source(_zz, name, _names=None, rigged=False):
            if bones[name] is None:
                raise UnitModelError("draws nothing with bones")
            return SimpleNamespace(skeleton=SimpleNamespace(names=bones[name]))

        def model(skin):
            return SimpleNamespace(meshes=[SimpleNamespace(skin=[[(n, 255)] for n in skin])])
        arc = SimpleNamespace(close=lambda: None)
        with mock.patch("rusemod.unitmodel.find_source", source), mock.patch("rusemod.unitmodel.pack_names", lambda zz: []), \
                mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
            with mock.patch("rusemod.modelin.read_model", lambda _f, skin: model(["Horse Spine", "bip01"])):
                self.assertEqual(animmodel.own_bones_on(Path("g"), Path("f.glb"), ["flat", "rifle", "bazooka"]), "rifle")
            with mock.patch("rusemod.modelin.read_model", lambda _f, skin: model(["Bip01", "bip01 spine"])):
                self.assertIsNone(animmodel.own_bones_on(Path("g"), Path("f.glb"), ["rifle"]))   # the soldier's own
            with mock.patch("rusemod.modelin.read_model", lambda _f, skin: model([])):
                self.assertIsNone(animmodel.own_bones_on(Path("g"), Path("f.glb"), ["rifle"]))   # no bones at all


class TheIndex(unittest.TestCase):
    def test_a_unit_s_figures_and_actions(self):
        """Its figures by its links, as the build walks a unit: a figure the index files under another unit (the first
        to reach it) is found; its ride (another unit) and a named object are not walked into."""
        db = sqlite3.connect(":memory:")
        db.executescript("CREATE TABLE object (id INTEGER, address TEXT, export TEXT, class TEXT, shadow INTEGER);"
                         "CREATE TABLE ref (src INTEGER, dst INTEGER, path TEXT);"
                         "CREATE TABLE value (object INTEGER, path TEXT, text TEXT, num REAL);")
        unit, other, truck = E + "Descriptor_Unit_Squad", E + "Descriptor_Unit_Other", E + "Descriptor_Unit_Truck"
        db.executemany("INSERT INTO object VALUES (?, ?, ?, ?, 0)", [
            (1, unit, unit, "TInfanterieDescriptor"), (2, unit + ":GfxDescriptorFusilier", None, "TGfxDescriptorBiped"),
            (3, None, None, "TResourceMultiMaterialMesh"), (4, None, None, "TGfxDescriptorAnimation"),
            (5, other + ":GfxDescriptorIcone", None, "TGfxDescriptorPileJeton"),
            (6, other + ":GfxDescriptorIcone.PawnDescriptor", None, "TPawnDescriptor"),
            (7, other + ":GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine", None, "TGfxDescriptorBiped"),
            (8, truck, truck, "TUniteAuSolDescriptor"), (9, truck + ":GfxDescriptor", None, "TGfxDescriptorBiped"),
            (10, E + "Named_Figure", E + "Named_Figure", "TGfxDescriptorBiped")])
        db.executemany("INSERT INTO ref VALUES (?, ?, ?)", [
            (1, 2, "GfxDescriptorFusilier"), (1, 5, "GfxDescriptorIcone"), (1, 8, "TransportPourMorphe"),
            (1, 10, "GfxDescriptorNamed"), (2, 3, "MeshDescriptor"), (2, 4, "ResourceAnimation[1].v"),
            (2, 4, "ResourceAnimation[0].v"), (5, 6, "PawnDescriptor"), (6, 7, "DescriptorFigurine"),
            (7, 3, "MeshDescriptor"), (7, 4, "ResourceAnimation[0].v"), (8, 9, "GfxDescriptor"),
            (9, 4, "ResourceAnimation[0].v"), (10, 4, "ResourceAnimation[0].v")])
        db.executemany("INSERT INTO value VALUES (?, ?, ?, NULL)", [
            (3, "FileName", MODEL_FILE), (2, "ResourceAnimation[0].k", "t_stand"), (2, "ResourceAnimation[1].k", "b_stand"),
            (7, "ResourceAnimation[0].k", "t_tir_replacement"), (9, "ResourceAnimation[0].k", "idle1"),
            (10, "ResourceAnimation[0].k", "t_named")])
        got = animmodel.unit_figures(db, unit)
        self.assertEqual(got, [("GfxDescriptorFusilier", MODEL_FILE.lower(), ["t_stand", "b_stand"]),
                               ("GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine", MODEL_FILE.lower(),
                                ["t_tir_replacement"])])


if __name__ == "__main__":
    unittest.main()
