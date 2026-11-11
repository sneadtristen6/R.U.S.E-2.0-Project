"""rusemod.bonefit (whether a model's bones fit the animations it plays and the parts and shots that hang on it; where
a model on bones of its own splits into its two halves), the build's warnings from it (rusemod.build.unit_fit_checks:
never an error) and the unit page's (ruse_studio.modelfit: model_fit, model_split). Item 5, part 3; the owner's 7
(2026-11-10): "Yes, seven should warn them. If it's gonna break, and then tell them how to fix it. And what's the issue
is. Should be intuitive."

Made-up skeletons, clips and unit data always run. With RUSE_HORSE_GLB naming the owner's Horse Squad of 2026-11-09
(scratch/animmodels/horse-squad-rifle.glb), its suggested split and its own animations are checked as well."""
import base64
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from rusemod import anim, baf, bonefit, modelin, rig
from rusemod.modelin import OWN_SKELETON

B = "\\"
E = "$/GFX/Everything/"
UNIT = "Descriptor_Unit_Horse_Squad"
LIKE = B.join(["ww2", "res3d", "units", "us", "infanterie", "us_soldier_modellod0.ase2ndfbin"])
OWN_MODEL = B.join(["ww2", "res3d", "units", "us", "infanterie", f"{UNIT}lod0.Ase2ndfbin"])
STAND = "WW2\\Res3D\\Units\\Common\\Fusilier_standlod0.Ase2NdfBin"
HORSE_GLB = Path(os.environ["RUSE_HORSE_GLB"]) if os.environ.get("RUSE_HORSE_GLB") else None

# a soldier's 41 bones, as the game's riflemen have them (in name; the made-up ones fill the count)
SOLDIER = (["bip01", "bip01 footsteps", "bip01 pelvis", "bip01 spine", "bip01 spine1", "bip01 neck", "bip01 head",
            "bip01 l clavicle", "bip01 r clavicle", "bip01 l upperarm", "bip01 r upperarm", "bip01 l forearm",
            "bip01 r forearm", "bip01 l hand", "bip01 r hand", "arme_1", "arme_2", "fx_tir_01", "fx_tir_02",
            "bip01 l thigh", "bip01 r thigh", "bip01 l calf", "bip01 r calf", "bip01 l foot", "bip01 r foot"]
           + [f"bip01 finger{k}" for k in range(16)])
SOLDIER_PARENTS = [-1, 0, 0, 2, 3, 4, 5, 5, 5, 7, 8, 9, 10, 11, 12, 14, 14, 15, 16, -1, -1, 19, 20, 21, 22] + [13] * 16


def horse_and_rider():
    """A small horse with a rider on its back, named as the owner's Horse Squad of 2026-11-09 is: the horse's bones
    "horse ...", the rider's from his bip01 on the horse's spine (and his weapon's bones)."""
    names = ["horse bip01", "horse pelvis", "horse spine", "horse l thigh", "horse spine1", "horse neck", "horse head",
             "bip01", "bip01 pelvis", "bip01 spine", "bip01 head", "bip01 r hand", "arme_1", "fx_tir_01"]
    parents = [-1, 0, 1, 2, 2, 4, 5, 4, 7, 8, 9, 9, 11, 12]
    return names, parents


def record(names, parents) -> bytes:
    n = len(names)
    return baf.skeleton_bytes(list(names), list(parents), [rig.IDENTITY] * n, [rig.IDENTITY] * n, [rig.IDENTITY] * n)


def clip_on(names, parents=None) -> bytes:
    """A one-second clip on a skeleton of these bones (every bone held still)."""
    parents = parents if parents is not None else [-1] + [0] * (len(names) - 1)
    still = baf.pack_quat(0.0, 0.0, 0.0, 1.0)
    tracks = [baf.Track([(0, 0.0, 0.0, float(k))], [(0, 1.0, 1.0, 1.0)], [(0,) + still]) for k in range(len(names))]
    return baf.build(baf.Clip(1.0, 2, tracks, record(names, parents)), max(64, len(names)))


def mod_glb(path: Path, names, parents) -> bytes:
    """A mod's files/models/<unit>.glb of a model on bones of its own (modelin.write_glb's, fitted to LIKE)."""
    rec = record(names, parents)
    part = modelin.Part(modelin.RIGGED, -1, [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [(0.0, 0.0, 1.0)] * 3,
                        [(0.5, 0.5)] * 3, [(0, 1, 2)], skin=[[(names[0], 255)]] * 3, tracks=None, draw=None, static=False)
    report = {"rigged": True, OWN_SKELETON: {"bones": len(names), "record": base64.b64encode(rec).decode("ascii")},
              "also": [LIKE.replace("modellod0", "bazooka_modellod0")]}     # (a squad's bazooka man wears it too)
    path.parent.mkdir(parents=True, exist_ok=True)
    modelin.write_glb(modelin.Prepared([part], [], report), path, LIKE)
    return rec


class ClipFit(unittest.TestCase):
    def test_the_11_09_crash_s_numbers(self):
        # the game read the horse's standing clip (36 bones) on a figure of 41: the game stopped
        fit = bonefit.clip_fit(SOLDIER, SOLDIER[:36])
        self.assertEqual((fit["how"], fit["clip_bones"], fit["model_bones"]), ("fewer", 36, 41))
        self.assertEqual(bonefit.clip_level(fit["how"]), ("stops", True))

    def test_more_other_names_another_order_and_the_same(self):
        self.assertIsNone(bonefit.clip_fit(SOLDIER, [n.upper() for n in SOLDIER]))      # names in any case
        more = bonefit.clip_fit(SOLDIER[:36], SOLDIER)
        self.assertEqual((more["how"], bonefit.clip_level("more")), ("more", ("stops", False)))
        named = bonefit.clip_fit(["a", "b", "c"], ["a", "x", "c"])
        self.assertEqual((named["how"], named["examples"]), ("names", [["x", "b"]]))
        self.assertEqual(bonefit.clip_fit(["a", "b", "c"], ["a", "c", "b"])["how"], "order")
        self.assertEqual(bonefit.clip_level("names"), ("wrong", False))

    def test_a_clip_s_own_bones(self):
        self.assertEqual(bonefit.clip_bones(clip_on(["Hips", "Spine"])), ["hips", "spine"])
        self.assertIsNone(bonefit.clip_bones(b"not a clip"))


class Split(unittest.TestCase):
    def test_a_rider_on_a_horse_splits_at_the_rider(self):
        names, parents = horse_and_rider()
        self.assertEqual(bonefit.suggest_split(names, parents), "bip01")
        h = bonefit.halves_of(names, parents, "bip01")
        self.assertEqual(h["top"], ["bip01", "bip01 pelvis", "bip01 spine", "bip01 head", "bip01 r hand", "arme_1",
                                    "fx_tir_01"])
        self.assertEqual(h["bottom"], names[:7])

    def test_a_soldier_splits_at_the_spine(self):
        self.assertEqual(bonefit.suggest_split(SOLDIER, SOLDIER_PARENTS), "bip01 spine")

    def test_no_spine_splits_where_it_first_branches(self):
        names = ["root", "hips", "thigh.l", "thigh.r", "chest", "head", "arm.l", "arm.r"]
        parents = [-1, 0, 1, 1, 1, 4, 4, 4]
        self.assertEqual(bonefit.suggest_split(names, parents), "chest")        # the branch with the most bones
        self.assertEqual(bonefit.suggest_split(["only"], [-1]), "only")

    def test_the_chosen_split_kept_or_said_when_gone(self):
        names, parents = horse_and_rider()
        self.assertEqual(bonefit.chosen_split(names, parents, "HORSE NECK"), ("horse neck", []))
        split, said = bonefit.chosen_split(names, parents, "tail")
        self.assertEqual((split, [p["kind"] for p in said]), ("bip01", ["split_gone"]))
        self.assertEqual((said[0]["split"], said[0]["used"]), ("tail", "bip01"))
        split, said = bonefit.chosen_split(names, parents, "horse bip01")
        self.assertEqual([p["kind"] for p in said], ["split_all_top"])          # the lower half's clips move nothing
        with self.assertRaises(bonefit.FitError):
            bonefit.halves_of(names, parents, "tail")

    def test_the_masks_the_build_writes_from_it(self):
        from rusemod import unitmodel
        names, parents = horse_and_rider()
        masks = unitmodel.halves(record(names, parents), bonefit.suggest_split(names, parents))
        top, bottom = masks["top"]["Weights"], masks["bottom"]["Weights"]
        self.assertEqual((masks["top"]["MaskUnionCode"], masks["bottom"]["MaskUnionCode"]), (65280, 255))
        self.assertEqual(sorted(top), sorted(bonefit.halves_of(names, parents, "bip01")["top"]))
        self.assertFalse(set(top) & set(bottom))                                # each bone weighed once: never doubled
        self.assertEqual(sorted(set(top) | set(bottom)), sorted(names))

    def test_the_split_saved_beside_the_model_and_used(self):
        names, parents = horse_and_rider()
        with tempfile.TemporaryDirectory() as d:
            glb = Path(d, "files", "models", f"{UNIT}.glb")
            mod_glb(glb, names, parents)
            glb.with_suffix(".json").write_text(json.dumps({"from": "x.glb", "size": 1.0}), encoding="utf-8")
            self.assertEqual(bonefit.split_for(glb), "bip01")                   # nothing chosen: the suggested one
            bonefit.save_split(glb, "Horse Neck")
            kept = json.loads(glb.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual((kept["split"], kept["from"]), ("horse neck", "x.glb"))   # the rest of the record kept
            self.assertEqual(bonefit.split_for(glb), "horse neck")
            masks = bonefit.halves_for(glb)                                      # what the build writes for it
            self.assertEqual((masks["split"], sorted(masks["top"]["Weights"])), ("horse neck", ["horse head", "horse neck"]))
            bonefit.save_split(glb, None)
            self.assertNotIn("split", json.loads(glb.with_suffix(".json").read_text(encoding="utf-8")))
            self.assertEqual(bonefit.glb_record(glb), record(names, parents))
            plain = Path(d, "plain.glb")                                         # a model on another unit's bones
            modelin.write_glb(modelin.Prepared([modelin.Part("chassis", -1, [(0.0, 0.0, 0.0)] * 3, [(0.0, 0.0, 1.0)] * 3,
                                                             [(0.0, 0.0)] * 3, [(0, 1, 2)])], [], {}), plain, LIKE)
            self.assertIsNone(bonefit.split_for(plain))
            self.assertIsNone(bonefit.halves_for(plain))

    def test_too_many_bones_said_never_refused(self):
        names = [f"b{k}" for k in range(65)]
        self.assertEqual([p["kind"] for p in bonefit.model_problems(names)], ["too_many"])
        self.assertEqual(bonefit.model_problems(names[:64]), [])


def game_with_squad(own_model=OWN_MODEL, listings=None, extra=None):
    """The build's data (rusemod.patch.Game) with the unit UNIT: a rifleman figure drawing `own_model` whose upper body
    turns at Bip01 Spine and whose firing listing shoots from Fx_Tir_01, with a person held on a Saddle bone (a figure
    of its own), a far-away figure under its token showing a weapon on Arme_2 (the made-up horse and rider has neither
    Saddle nor Arme_2), and `listings` [(action, FileName, mask weights or None, code)] on the rifleman."""
    from rusemod.patch import Game, Inline, ListV, MapV, Num, Obj, Ref, Text

    def mesh(f):
        return Inline(Obj("TResourceMultiMaterialMesh", {"FileName": Text("path", f)}))

    def mask(weights, code):
        if weights is None:
            return {}
        return {"Mask": Inline(Obj("THierarchicalASEModelSkeletonMask", {
            "MaskUnionCode": Num("int32", Decimal(code)),
            "Weights": MapV([(Text("string", n), Num("float32", Decimal(str(w)))) for n, w in weights.items()])}))}

    def shot(bone):
        return Inline(Obj("TGfxDescriptorAnimationEventSequence", {"Events": ListV([Inline(Obj(
            "TGfxDescriptorAnimationEvent", {"Action": Inline(Obj("TActionDescriptorLaunchEffetOnSousMobile",
                                                                  {"SousMobile": Text("string", bone)}))}))])}))

    rows = []
    for action, file, weights, code in (listings or [("t_tir", STAND, None, 65280)]):
        props = {"FileName": Text("path", file), **mask(weights, code)}
        if action == "t_tir":
            props["EventSequence"] = shot("Fx_Tir_01")
        rows.append((Text("string", action), Inline(Obj("TGfxDescriptorAnimation", props))))
    named = Obj("TGfxDescriptorAnimation", {"FileName": Text("path", STAND)})     # a listing that is a named object
    rider = Obj("TGfxDescriptorBiped", {"MeshDescriptor": mesh("WW2\\Res3D\\Units\\US\\Servant_modellod0.Ase2NdfBin"),
                                        "SousElements": MapV([(Text("string", "x"), Inline(Obj(
                                            "TGfxDescriptorCompensationBoneOperator",
                                            {"SousMobileName": Text("string", "Bip01 Spine")})))])})
    rifle = Obj("TGfxDescriptorBiped", {
        "MeshDescriptor": mesh(own_model),
        "SousElements": MapV([
            (Text("string", "torso"), Inline(Obj("TGfxDescriptorCompensationBoneOperator",
                                                 {"SousMobileName": Text("string", "Bip01 Spine")}))),
            (Text("string", "seat"), Inline(Obj("TGfxDescriptorModeleSousMobile", {
                "SousMobileName": Text("string", "Saddle"),
                "SousElements": MapV([(Text("string", "sous_modele"), Inline(rider))])})))]),
        "ResourceAnimation": MapV(rows + [(Text("string", "t_named"), Ref(E + "Anim_Named"))])})
    token = Obj("TGfxDescriptorPileJeton", {"PawnDescriptor": Inline(Obj("TPawnDescriptor", {
        "DescriptorFigurine": Inline(Obj("TGfxDescriptorBiped", {
            "MeshDescriptor": mesh(own_model),
            "SousElements": MapV([(Text("string", "w"), Inline(Obj("TGfxDescriptorVisibilityBoneOperator",
                                                                    {"SousMobileName": Text("string", "Arme_2")})))]),
            "ResourceAnimation": MapV([])}))}))})
    unit = Obj("TInfanterieDescriptor", {"GfxDescriptorFusilier": Inline(rifle), "GfxDescriptorIcone": Inline(token),
                                         "VisibilityRange": Ref(E + "Zoom3")})
    objects = {E + UNIT: unit, E + "Anim_Named": named, **(extra or {})}
    return Game(objects=objects)


class Figures(unittest.TestCase):
    def test_what_each_figure_draws_plays_and_needs(self):
        figs = {f.path: f for f in bonefit.data_figures(game_with_squad(), E + UNIT)}
        self.assertEqual(sorted(figs), ["GfxDescriptorFusilier", "GfxDescriptorFusilier.SousElements[1].v.SousElements[0].v",
                                        "GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"])
        rifle = figs["GfxDescriptorFusilier"]
        self.assertEqual(rifle.model, OWN_MODEL)
        self.assertEqual([(a, f) for a, f, _m in rifle.listings], [("t_tir", STAND), ("t_named", STAND)])
        self.assertEqual(sorted(rifle.needs), [("Bip01 Spine", "turn"), ("Fx_Tir_01", "shot"), ("Saddle", "hold")])
        # the person held on the saddle is a figure of its own: his parts need his model's bones, not the horse's
        rider = figs["GfxDescriptorFusilier.SousElements[1].v.SousElements[0].v"]
        self.assertEqual((rider.needs, rider.model.endswith("Servant_modellod0.Ase2NdfBin")), ([("Bip01 Spine", "turn")], True))
        self.assertEqual(figs["GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"].needs, [("Arme_2", "show")])
        self.assertEqual(len(bonefit.own_figures(list(figs.values()), [OWN_MODEL.upper().replace(B, "/")])), 2)

    def test_from_the_game_index_the_same(self):
        db = index_of_squad()
        figs = {f.path: f for f in bonefit.index_figures(db, E + "Descriptor_Unit_Soldat")}
        self.assertEqual(sorted(figs), ["GfxDescriptorFusilier", "GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"])
        rifle = figs["GfxDescriptorFusilier"]
        self.assertEqual(rifle.model, LIKE)
        self.assertEqual([(a, f, m.code) for a, f, m in rifle.listings], [("t_tir", STAND, 65280)])
        self.assertIsNone(rifle.listings[0][2].weights)                         # (the index keeps no weights)
        self.assertEqual(sorted(rifle.needs), [("Bip01 Spine", "turn"), ("Fx_Tir_01", "shot")])
        self.assertEqual(figs["GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"].needs, [("Arme_2", "show")])
        self.assertEqual(bonefit.index_figures(db, E + "Descriptor_Unit_Nobody"), [])


def index_of_squad():
    """A game index (rusemod.index's tables, the columns read) with a rifle squad: its rifleman (the torso turn on Bip01
    Spine, a firing listing shooting from Fx_Tir_01 on the upper half) and its token's far-away figure (Arme_2 shown and
    hidden); its VisibilityRange a named object of the game's (not walked)."""
    db = sqlite3.connect(":memory:")
    db.executescript("""CREATE TABLE object(id INTEGER PRIMARY KEY, class TEXT, address TEXT, export TEXT, shadow INTEGER);
                        CREATE TABLE ref(src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
                        CREATE TABLE value(object INTEGER, path TEXT, num REAL, text TEXT);""")
    objs = [(1, "TInfanterieDescriptor", E + "Descriptor_Unit_Soldat", E + "Descriptor_Unit_Soldat"),
            (2, "TGfxDescriptorBiped", None, None), (3, "TResourceMultiMaterialMesh", None, None),
            (4, "TGfxDescriptorCompensationBoneOperator", None, None), (5, "TGfxDescriptorAnimation", None, None),
            (6, "THierarchicalASEModelSkeletonMask", None, None), (7, "TGfxDescriptorAnimationEventSequence", None, None),
            (8, "TGfxDescriptorAnimationEvent", None, None), (9, "TActionDescriptorLaunchEffetOnSousMobile", None, None),
            (10, "TVisibilityRange", E + "Zoom3", E + "Zoom3"), (11, "TGfxDescriptorPileJeton", None, None),
            (12, "TPawnDescriptor", None, None), (13, "TGfxDescriptorBiped", None, None),
            (14, "TGfxDescriptorVisibilityBoneOperator", None, None), (15, "TResourceMultiMaterialMesh", None, None)]
    db.executemany("INSERT INTO object VALUES (?, ?, ?, ?, 0)", objs)
    db.executemany("INSERT INTO ref(src, path, kind, dst) VALUES (?, ?, 'object', ?)", [
        (1, "GfxDescriptorFusilier", 2), (1, "GfxDescriptorIcone", 11), (2, "MeshDescriptor", 3),
        (2, "SousElements[0].v", 4), (2, "ResourceAnimation[0].v", 5), (5, "Mask", 6), (5, "EventSequence", 7),
        (7, "Events[1]", 8), (8, "Action", 9), (2, "VisibilityRange", 10), (11, "PawnDescriptor", 12),
        (12, "DescriptorFigurine", 13), (13, "MeshDescriptor", 15), (13, "SousElements[0].v", 14)])
    db.executemany("INSERT INTO value VALUES (?, ?, ?, ?)", [
        (3, "FileName", None, LIKE), (4, "SousMobileName", None, "Bip01 Spine"), (2, "ResourceAnimation[0].k", None, "t_tir"),
        (5, "FileName", None, STAND), (6, "MaskUnionCode", 65280.0, None), (6, "Weights[0].k", None, "Bip01 Spine"),
        (9, "SousMobile", None, "Fx_Tir_01"), (15, "FileName", None, LIKE.replace("modellod0", "bazooka_modellod0")),
        (14, "SousMobileName", None, "Arme_2")])
    return db


class Checks(unittest.TestCase):
    def setUp(self):
        self.names, self.parents = horse_and_rider()

    def test_a_game_soldier_s_clip_on_a_model_of_its_own_bones(self):
        fig = bonefit.Figure("GfxDescriptorFusilier", OWN_MODEL, [("t_stand", STAND, None), ("t_marche", STAND, None),
                                                                 ("b_stand", "mine", None)], [])
        bones = {STAND: SOLDIER, "mine": self.names}
        got = bonefit.check_figure(self.names, fig, bones.get, lambda f: f == "mine")
        self.assertEqual(len(got), 1)                                           # one warning, its actions listed
        p = got[0]
        self.assertEqual((p["kind"], p["how"], p["clip_bones"], p["model_bones"], p["level"], p["seen"]),
                         ("clip", "more", 41, 14, "stops", False))
        self.assertEqual((p["actions"], p["own"], p["clips"]), (["t_marche", "t_stand"], False, [STAND]))

    def test_the_game_s_clips_that_don_t_fit_the_same_way_said_together(self):
        # a figure still playing the game soldier's clips: one problem with them all, not one a clip; its own clip
        # of other bones apart
        run, walk, mine = STAND.replace("stand", "course"), STAND.replace("stand", "marche"), "own"
        fig = bonefit.Figure("f", OWN_MODEL, [("t_stand", STAND, None), ("t_course", run, None), ("b_marche", walk, None),
                                             ("t_own", mine, None)], [])
        bones = {STAND: SOLDIER, run: SOLDIER, walk: SOLDIER, mine: ["a", "b"]}
        got = bonefit.check_figure(self.names, fig, bones.get, lambda f: f == mine)
        self.assertEqual([(p["how"], p["own"], len(p["clips"]), len(p["actions"])) for p in got],
                         [("more", False, 3, 3), ("fewer", True, 1, 1)])

    def test_bones_its_shots_and_parts_need(self):
        fig = bonefit.Figure("f", OWN_MODEL, [], [("Fx_Tir_01", "shot"), ("Fx_Tir_02", "shot"), ("Bip01 Spine", "turn"),
                                                 ("Arme_9", "show"), ("Arme_9", "show")])
        got = bonefit.check_figure(self.names, fig, lambda f: None)
        said = {(p["bone"], p["need"], p["level"], p["seen"], p["count"]) for p in got}
        self.assertEqual(said, {("Fx_Tir_02", "shot", "unseen", True, 1), ("Arme_9", "show", "stops", False, 2)})

    def test_halves_naming_bones_it_hasn_t_got_or_weighing_one_twice(self):
        from rusemod import unitmodel
        game_top = bonefit.Mask(65280, 0.0, {"Bip01 Spine": 1.0, "Bip01 L Thigh": 0.0})   # the game soldier's way
        fig = bonefit.Figure("f", OWN_MODEL, [("t_stand", "x", game_top)], [])
        got = bonefit.check_figure(self.names, fig, lambda f: None)
        self.assertEqual([(p["kind"], p["halves"], p["names"]) for p in got], [("mask_bones", ["top"], ["Bip01 L Thigh"])])
        # two halves weighing every bone at full: the 2026-11-09 horses as big as the map
        full = [("t_stand", "x", bonefit.Mask(65280, 1.0, {})), ("b_stand", "x", bonefit.Mask(255, 1.0, {}))]
        got = bonefit.check_figure(self.names, bonefit.Figure("f", OWN_MODEL, full, []), lambda f: None)
        self.assertEqual([(p["kind"], len(p["bones"]), p["most"], p["seen"]) for p in got], [("mask_sum", 14, 2.0, True)])
        # the halves the build writes from the split: nothing to say
        masks = unitmodel.halves(record(self.names, self.parents), "bip01")
        ours = [("t_stand", "x", bonefit.Mask(65280, 0.0, masks["top"]["Weights"])),
                ("b_stand", "x", bonefit.Mask(255, 0.0, masks["bottom"]["Weights"]))]
        self.assertEqual(bonefit.check_figure(self.names, bonefit.Figure("f", OWN_MODEL, ours, []), lambda f: None), [])
        self.assertEqual(bonefit.check_figure(self.names, fig, lambda f: None, masks=False), [])


class TheBuild(unittest.TestCase):
    """unit_fit_checks: the build's warnings, never an error; nothing for a mod without units of their own bones."""

    def run_checks(self, d, listings, own_clips=None, names=None, parents=None, zz=None, models=True):
        from rusemod.build import BuildResult, unit_fit_checks
        names, parents = (names, parents) if names else horse_and_rider()
        glb = Path(d, "mod", "files", "models", f"{UNIT}.glb")
        mod_glb(glb, names, parents)
        result = BuildResult()
        result.own_models = {UNIT: (LIKE, glb, "my-mod")} if models else {}
        result.own_clips = own_clips or {}
        run = SimpleNamespace(game=game_with_squad(listings=listings), created={E + UNIT: SimpleNamespace(kind="clone")})
        said = unit_fit_checks(run, result, zz)
        return said, [f for f in result.findings]

    def own_clip(self, d, stem, data):
        f = Path(d, "mod", anim.OWN, UNIT, f"{stem}.baf")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return {anim.own_member(stem): {"unit": UNIT, "mod": "my-mod", "clip": None, "edit": None, "file": f}}

    def test_its_own_animations_and_bones_fit_nothing_said(self):
        names, parents = horse_and_rider()
        names = names + ["saddle", "arme_2"]
        parents = parents + [4, 11]
        with tempfile.TemporaryDirectory() as d:
            own = self.own_clip(d, "own_horse_squad_tirlod0", clip_on(names, parents))
            from rusemod import unitmodel
            masks = unitmodel.halves(record(names, parents), "bip01")
            said, found = self.run_checks(d, [("t_tir", anim.own_data_name("own_horse_squad_tirlod0"),
                                               masks["top"]["Weights"], 65280)], own, names, parents)
        self.assertEqual(said, 0)
        self.assertEqual(found, [])

    def test_what_doesn_t_fit_is_said_in_plain_words(self):
        from fixtures import make_edat
        from rusemod.edat import Edat
        zz = Edat(make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", "fusilier_standlod0.baf", clip_on(SOLDIER, SOLDIER_PARENTS))])]))
        with tempfile.TemporaryDirectory() as d:
            own = self.own_clip(d, "own_horse_squad_otherlod0", clip_on(["a", "b"]))   # made for another model
            listings = [("t_stand", STAND, {"Bip01 Spine": 1.0, "Bip01 L Thigh": 1.0}, 65280),
                        ("t_tir", anim.own_data_name("own_horse_squad_otherlod0"), None, 65280)]
            said, found = self.run_checks(d, listings, own, zz=zz)
        text = "\n".join(f.message for f in found)
        self.assertEqual({f.level for f in found}, {"warning"})                # never an error: the build goes on
        self.assertEqual(said, len(found))
        self.assertIn(f"my-mod: {UNIT}: its figure GfxDescriptorFusilier plays 1 animation(s) for 2 action(s) "
                      "(Fusilier stand), and they have 41 bones where the model has 14. An animation with more bones "
                      "than its model can stop the game (not tried in the game yet).", text)
        self.assertIn("plays 1 animation(s) for 1 action(s) (own_horse_squad_otherlod0), and they have 2 bones where "
                      "the model has 14. The game can stop on an animation with fewer bones than its model (it did in "
                      "a test).", text)
        self.assertIn("hangs 1 part(s) on a bone called Saddle, which the model hasn't got: the game can stop on it",
                      text)
        self.assertIn("on halves of the body that name bones the model hasn't got (Bip01 L Thigh)", text)
        self.assertIn("its figure GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine hangs 1 part(s) on a bone "
                      "called Arme_2", text)
        self.assertNotIn("Fx_Tir_01", text)                                     # the rider has it: no shot warning
        self.assertNotIn("Servant", text)                                       # the held person is another model

    def test_a_missing_firing_bone_and_the_split_said(self):
        names, parents = horse_and_rider()
        names = [n for n in names if n != "fx_tir_01"]
        parents = parents[:len(names)]
        with tempfile.TemporaryDirectory() as d:
            Path(d, "mod", "files", "models").mkdir(parents=True)
            Path(d, "mod", "files", "models", f"{UNIT}.json").write_text(json.dumps({"split": "tail"}), encoding="utf-8")
            said, found = self.run_checks(d, None, names=names, parents=parents)
        text = "\n".join(f.message for f in found)
        self.assertIn("its figure GfxDescriptorFusilier fires from a bone called Fx_Tir_01, which the model hasn't "
                      "got, so the unit will fire with no shot to be seen (seen in a test). In Blender, add a bone "
                      "called Fx_Tir_01 at the weapon's muzzle", text)
        self.assertIn("the bone tail chosen to split the model in two isn't in it any more, so it splits at bip01", text)

    def test_a_unit_s_own_clip_on_the_game_s_model(self):
        # Descriptor_Unit_Soldat's own clip (units.toml) of other bones, on a figure drawing the game's soldier: the
        # model's bones from the game's own clips it still plays (no skeleton pack here)
        from fixtures import make_edat
        from rusemod.build import BuildResult, unit_fit_checks
        from rusemod.edat import Edat
        zz = Edat(make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", "fusilier_standlod0.baf", clip_on(SOLDIER, SOLDIER_PARENTS))])]))
        with tempfile.TemporaryDirectory() as d:
            own = self.own_clip(d, "own_horse_squad_wavelod0", clip_on(SOLDIER[:30]))
            result = BuildResult()
            result.own_clips = own
            run = SimpleNamespace(game=game_with_squad(own_model=LIKE, listings=[
                ("t_stand", STAND, None, 65280), ("t_wave", anim.own_data_name("own_horse_squad_wavelod0"), None, 65280)]),
                created={E + UNIT: SimpleNamespace(kind="clone")})
            said = unit_fit_checks(run, result, zz)
        self.assertEqual(said, 1)
        self.assertIn(f"my-mod: {anim.UNITS}: {UNIT}: its figure GfxDescriptorFusilier plays 1 animation(s) for 1 "
                      "action(s) (own_horse_squad_wavelod0), and they have 30 bones where the model has 41",
                      result.findings[0].message)

    def test_a_squad_on_the_game_soldier_s_bones_only_its_own_clips(self):
        # a model rigged to the game soldier's bones (item 4's way): the game's clips and parts fit it; an own clip
        # of other bones on it is said
        from fixtures import make_edat
        from rusemod.build import BuildResult, unit_fit_checks
        from rusemod.edat import Edat
        zz = Edat(make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", "fusilier_standlod0.baf", clip_on(SOLDIER, SOLDIER_PARENTS))])]))
        with tempfile.TemporaryDirectory() as d:
            glb = Path(d, "mod", "files", "models", f"{UNIT}.glb")
            glb.parent.mkdir(parents=True)
            part = modelin.Part(modelin.RIGGED, -1, [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
                                [(0.0, 0.0, 1.0)] * 3, [(0.5, 0.5)] * 3, [(0, 1, 2)], skin=[[("bip01 spine", 255)]] * 3)
            modelin.write_glb(modelin.Prepared([part], [], {"rigged": True}), glb, LIKE)
            result = BuildResult()
            result.own_models = {UNIT: (LIKE, glb, "my-mod")}
            result.own_clips = self.own_clip(d, "own_horse_squad_wavelod0", clip_on(SOLDIER[:30]))
            run = SimpleNamespace(game=game_with_squad(listings=[
                ("t_stand", STAND, None, 65280), ("t_wave", anim.own_data_name("own_horse_squad_wavelod0"), None, 65280)]),
                created={E + UNIT: SimpleNamespace(kind="clone")})
            said = unit_fit_checks(run, result, zz)
        self.assertEqual(said, 1)
        self.assertIn("plays 1 animation(s) for 1 action(s) (own_horse_squad_wavelod0), and they have 30 bones where "
                      "the model has 41", result.findings[0].message)

    def test_a_check_that_can_t_run_is_said(self):
        # a model file that can't be read: a warning that says so (never dropped quietly), and the build goes on
        from unittest import mock
        with tempfile.TemporaryDirectory() as d, \
                mock.patch("rusemod.bonefit.glb_record", side_effect=OSError("the file is gone")):
            said, found = self.run_checks(d, None)
        self.assertEqual((said, [f.level for f in found]), (1, ["warning"]))
        self.assertEqual(found[0].message, f"my-mod: {UNIT}: its animations and bones couldn't be checked (the file "
                                           "is gone), so the build goes on without that check.")

    def test_a_mod_without_units_of_their_own_says_nothing(self):
        from rusemod.build import BuildResult, unit_fit_checks
        result = BuildResult()
        run = SimpleNamespace(game=game_with_squad(own_model=LIKE), created={})
        self.assertEqual(unit_fit_checks(run, result, None), 0)
        self.assertEqual(result.findings, [])

    def test_every_warning_in_eleven_languages(self):
        from rusemod import buildtext, wordedtext
        mine = [t for t in buildtext.templates() if ": its figure {1}" in t or "the model splits at" in t
                or "chosen to split the model" in t or "The game isn't seen to animate" in t
                or "couldn't be checked" in t]
        self.assertEqual(len(mine), 12)
        self.assertEqual(wordedtext.missing(buildtext.FILE, mine), [])
        fr = buildtext.worded(f"warning: my-mod: {UNIT}: the model splits at horse bip01, its first bone, so every "
                              "bone is in its upper half and the lower half's animations (walking, running) move "
                              "nothing. Choose another bone on the unit's page (Its two halves).", "fr")
        self.assertTrue(fr.startswith(f"avertissement: my-mod: {UNIT} : le modèle se partage à horse bip01"), fr)


class ThePage(unittest.TestCase):
    """model_fit and model_split on a new unit whose own model is on bones of its own (ruse_studio.modelfit)."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        from ruse_studio.edits import NewUnit
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        (root / "R.U.S.E" / "Data" / "PC" / "190852").mkdir(parents=True)
        (root / "R.U.S.E" / "Data" / "PC" / "190852" / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.glb = self.mod / "files" / "models" / f"{UNIT}.glb"
        self.names, self.parents = horse_and_rider()
        mod_glb(self.glb, self.names, self.parents)
        from rusemod.unitmodel import glb_report
        self.glb.with_suffix(".json").write_text(json.dumps({"from": "horse.glb", "report": glb_report(self.glb)}),
                                                 encoding="utf-8")
        api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        api._mod_dir = lambda: self.mod
        api._own_model_file = lambda address: self.glb
        unit = NewUnit(E + UNIT, E + "Descriptor_Unit_Soldat", "Horse Squad")
        api._edits = lambda: SimpleNamespace(new_unit_of=lambda address: unit)
        db = index_of_squad()
        api._open = lambda: SimpleNamespace(db=db, close=lambda: None)
        api._decoy_clip_row = lambda member: {"skeleton": "|".join(SOLDIER)} if "fusilier" in member else None
        self.api = api

    def tearDown(self):
        self.dir.cleanup()

    def test_its_halves_and_what_won_t_fit(self):
        got = self.api.model_fit(E + UNIT)
        self.assertEqual((got["skeleton"], got["bones"]), ("own", 14))
        h = got["halves"]
        self.assertEqual((h["split"], h["suggested"], h["chosen"]), ("bip01", "bip01", False))
        self.assertEqual((len(h["top"]), len(h["bottom"])), (7, 7))
        self.assertEqual([b["name"] for b in h["tree"]][:4], ["horse bip01", "horse pelvis", "horse spine", "horse l thigh"])
        self.assertEqual({b["name"]: b["depth"] for b in h["tree"]}["bip01"], 4)
        kinds = sorted((p["kind"], p.get("bone") or p.get("clip_names")[0], p["figure_kind"]) for p in got["problems"])
        # the rifleman still plays the game's clip (41 bones on 14); the far-away figure shows a weapon on Arme_2,
        # a bone this model hasn't got
        self.assertEqual(kinds, [("bone", "Arme_2", "far"), ("clip", "Fusilier stand", "rifle")])

    def test_its_own_animation_for_the_action_is_what_s_checked(self):
        (self.mod / anim.OWN / UNIT).mkdir(parents=True)
        anim.add_unit_clip(self.mod, UNIT, "t_tir", clip_on(self.names, self.parents), name="hr_t_tir")
        got = self.api.model_fit(E + UNIT)
        self.assertEqual([p["kind"] for p in got["problems"]], ["bone"])         # the animation fits now

    def test_the_split_chosen_saved_and_back(self):
        got = self.api.model_split(E + UNIT, "horse neck")
        self.assertEqual((got["halves"]["split"], got["halves"]["chosen"], len(got["halves"]["top"])), ("horse neck", True, 2))
        self.assertEqual(json.loads(self.glb.with_suffix(".json").read_text(encoding="utf-8"))["split"], "horse neck")
        from ruse_studio.api import StudioError
        with self.assertRaises(StudioError):
            self.api.model_split(E + UNIT, "tail")
        got = self.api.model_split(E + UNIT, "")
        self.assertEqual((got["halves"]["split"], got["halves"]["chosen"]), ("bip01", False))

    def test_a_model_on_the_game_soldier_s_bones_keeps_the_game_s_halves(self):
        report = {"rigged": True, "like": LIKE}
        self.glb.with_suffix(".json").write_text(json.dumps({"report": report}), encoding="utf-8")
        self.api._fitcheck_game_bones = lambda model: list(SOLDIER)
        got = self.api.model_fit(E + UNIT)
        self.assertEqual((got["skeleton"], got["halves"], got["problems"]), ("soldier", None, []))
        from ruse_studio.api import StudioError
        with self.assertRaises(StudioError):
            self.api.model_split(E + UNIT, "bip01 spine")                      # no choice for it

    def test_a_unit_with_no_model_of_its_own_shows_nothing(self):
        self.glb.unlink()
        self.assertEqual(self.api.model_fit(E + UNIT)["skeleton"], None)


@unittest.skipUnless(HORSE_GLB, "RUSE_HORSE_GLB names the 2026-11-09 Horse Squad's .glb")
class TheHorseSquad(unittest.TestCase):
    def test_its_split_and_its_own_animations(self):
        from rusemod import unitmodel
        r = rig.read_rig(HORSE_GLB)
        names, parents = bonefit.skeleton_of(r.record())
        self.assertEqual(len(names), 62)
        self.assertEqual(bonefit.suggest_split(names, parents), "bip01")        # where the 11-09 test split
        h = bonefit.halves_of(names, parents, "bip01")
        self.assertEqual((len(h["top"]), len(h["bottom"])), (30, 32))
        self.assertTrue(all(n.startswith("horse ") for n in h["bottom"]))
        clips, _notes = unitmodel.own_clips(r)
        self.assertEqual(len(clips), 24)
        self.assertEqual([n for n, c in clips.items() if bonefit.clip_fit(names, bonefit.clip_bones(c))], [])
        soldier = bonefit.clip_fit(names, SOLDIER)                              # a game soldier's clip put on it
        self.assertEqual((soldier["how"], soldier["clip_bones"], soldier["model_bones"]), ("fewer", 41, 62))
        self.assertEqual(bonefit.model_problems(names, parents), [])


if __name__ == "__main__":
    unittest.main()
