"""A squad's soldiers by kind (the owner, 2026-11-11: "when you copy a fucking unit, it should copy the unit"): Import
model gives the riflemen a model, and the heavy-weapon soldier keeps the copied unit's until he gets his own
(files/models/<unit>@bazooka.glb). The 19 game squads whose riflemen and heavy-weapon soldier draw different models
all have the same four figures (read 2026-11-11 from the game index, scratch/animmodels/kinds/figures_of.py): the
riflemen, the heavy-weapon soldier, the fallen soldier and the figure drawn from far away (GfxDescriptorIcone's), the
last two each drawing one of the first two's models. The made-up squad here has the four: its fallen soldier draws
the riflemen's model, its far-away figure the heavy-weapon soldier's, as the GI squad has them.

Checked: the build (rusemod.build.unit_own_models, _own_model_part, _on_main_bones) points each figure at the model of
its kind, a mod made by an older Studio (its file naming every soldier model) builds as before, a kind's own
animations follow its bones; the Studio (ruse_studio.api: _soldier_kinds, model_import and model_import_remove with a
kind, look's "kinds", Resize keeping a kept Custom uniform) and the page's words and calls."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import re
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, build
from rusemod.edat import Edat
from test_anim import clip
from test_animactions import clips_pack

E = "$/GFX/Everything/"
UNIT = "Descriptor_Unit_Kinds_Squad"
RIFLE = "WW2\\Res3D\\Units\\US\\Infanterie\\US_Soldier_modellod0.Ase2ndfbin"
HEAVY = "WW2\\Res3D\\Units\\US\\Infanterie\\US_Soldier_bazooka_modellod0.Ase2ndfbin"
STAND = "GenAnim_15\\WW2\\Res3D\\Units\\common\\fusilier_standlod0.Baf"
OWN = f"WW2\\Res3D\\Units\\US\\Infanterie\\{UNIT}lod0.Ase2ndfbin"
OWN_HEAVY = f"WW2\\Res3D\\Units\\US\\Infanterie\\{UNIT}__bazookalod0.Ase2ndfbin"
# (model_of reads them in lower case)
R, H, O, OH = RIFLE.lower(), HEAVY.lower(), OWN.lower(), OWN_HEAVY.lower()
FIGURES = {"rifle": ["GfxDescriptorFusilier"], "heavy": ["GfxDescriptorBazooka"], "fallen": ["GfxDescriptorIconeCadavre"],
           "far": ["GfxDescriptorIcone", "PawnDescriptor", "DescriptorFigurine"]}


def unit_data() -> bytes:
    """The made-up game's unit data: the squad (its riflemen, its heavy-weapon soldier, its fallen soldier and its
    far-away figure), and a squad whose soldiers all draw one model."""
    from fixtures import make_edat, make_ndf, val

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
    strings = ["t_stand", "b_stand", STAND, RIFLE, HEAVY, "t_tir_secondaire"]
    ndf = make_ndf(objects=[
        (0, [(0, u32(2)), (12, i32(1)), (1, ref(1, 1)), (2, ref(2, 1)), (3, ref(3, 1)), (4, ref(7, 4))]),   # 0 the squad
        (1, [(6, ref(5, 3)), (5, listing((0, 4), (1, 4)))]),                                # 1 its riflemen
        (1, [(6, ref(6, 3)), (5, listing((0, 4), (1, 4), (5, 4)))]),                        # 2 its heavy-weapon soldier
        (1, [(6, ref(5, 3)), (5, listing((0, 4)))]),                                        # 3 its fallen soldier
        (2, [(7, path(2))]),                                                                # 4 stand
        (3, [(8, path(3)), (11, u32(524289))]),                                             # 5 the riflemen's model
        (3, [(8, path(4)), (11, u32(524289))]),                                             # 6 his model
        (4, [(9, ref(8, 5))]),                                                              # 7 its token
        (5, [(10, ref(9, 1))]),                                                             # 8 its pawn
        (1, [(6, ref(6, 3)), (5, listing((0, 4)))]),                                        # 9 its far-away figure
        (0, [(0, u32(4)), (12, i32(1)), (1, ref(11, 1))]),                                  # 10 another squad
        (1, [(6, ref(5, 3)), (5, listing((0, 4)))])],                                       # 11 its riflemen
        classes=["TInfanterieDescriptor", "TGfxDescriptorBiped", "TGfxDescriptorAnimation", "TResourceMultiMaterialMesh",
                 "TGfxDescriptorIcone", "TPawnDescriptor"],
        props=[("DescriptorId", 0), ("GfxDescriptorFusilier", 0), ("GfxDescriptorBazooka", 0),
               ("GfxDescriptorIconeCadavre", 0), ("GfxDescriptorIcone", 0), ("ResourceAnimation", 1),
               ("MeshDescriptor", 1), ("FileName", 2), ("FileName", 3), ("PawnDescriptor", 4), ("DescriptorFigurine", 5),
               ("UsefulnessMask", 3), ("Nationalite", 0)],
        strings=strings, exports={0: "GFX/Everything/Descriptor_Unit_Squad", 10: "GFX/Everything/Descriptor_Unit_One"},
        compress=True)
    return make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])


def glb(report: dict, like: str | None) -> bytes:
    """A mod's model file as the build reads it (rusemod.unitmodel.glb_report: its JSON part's asset extras)."""
    extras = {"rusemod_report": report, **({"rusemod_like": like} if like else {})}
    js = json.dumps({"asset": {"version": "2.0", "extras": extras}}).encode()
    js += b" " * (-len(js) % 4)
    return struct.pack("<4sII", b"glTF", 2, 20 + len(js)) + struct.pack("<I4s", len(js), b"JSON") + js


def model_of(objects, unit: str, figure: str) -> str:
    """The model a figure of `unit` draws (its MeshDescriptor's FileName, in lower case: the game reads the names in
    any case, and a model the Studio fitted names its folder as the record has it), the figure by its path from the
    unit."""
    from rusemod.patch import Inline
    node = objects[E + unit]
    for prop in FIGURES[figure] + ["MeshDescriptor"]:
        v = node.props[prop]
        node = v.obj if isinstance(v, Inline) else objects[v.target]
    return node.props["FileName"].value.lower()


def listings(objects, unit: str, figure: str) -> dict:
    from rusemod.patch import Inline
    node = objects[E + unit]
    for prop in FIGURES[figure]:
        v = node.props[prop]
        node = v.obj if isinstance(v, Inline) else objects[v.target]
    out = {}
    for k, v in node.props["ResourceAnimation"].pairs:
        a = v.obj if isinstance(v, Inline) else objects[v.target]
        out[k.value] = a.props["FileName"].value
    return out


class InTheBuild(unittest.TestCase):
    def mod(self, d, files: dict) -> Path:
        """A mod copying the squad, with model files {stem: (report, like)}."""
        mod = Path(d, "kinds")
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "kinds"\nversion = "1.0.0"\n', encoding="utf-8")
        (mod / "src" / "units.rndf").write_text(f"export {UNIT} is clone {E}Descriptor_Unit_Squad ( )\n", encoding="utf-8")
        models = mod / "files" / "models"
        models.mkdir(parents=True)
        for stem, (report, like) in files.items():
            (models / f"{stem}.glb").write_bytes(glb(report, like))
        return mod

    def build(self, mod):
        arc = Edat(unit_data())
        result = build.build_pack(arc, [build.load_mod(mod)], "0", Edat(clips_pack()))
        objects = build.load_pack(Edat(arc.to_bytes(result.changed))).base.objects if result.changed else None
        return result, objects

    def drawn(self, objects, unit=UNIT) -> dict:
        return {f: model_of(objects, unit, f) for f in FIGURES}

    def test_the_riflemen_s_model_leaves_the_heavy_weapon_soldier_as_the_copied_unit_had_him(self):
        """Import model's file for a squad since 2026-11-11: fitted to the riflemen's model alone ("also" empty). Its
        far-away figure wears the riflemen's look (the owner, 2026-11-11 on squad-page1: "It should take that like the
        more predominant unit"), no more the game's bazooka man."""
        with tempfile.TemporaryDirectory() as d:
            result, objects = self.build(self.mod(d, {UNIT: ({"rigged": True, "also": []}, RIFLE.lower())}))
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(self.drawn(objects), {"rifle": O, "fallen": O, "heavy": H, "far": O})
            self.assertEqual(self.drawn(objects, "Descriptor_Unit_Squad"),
                             {"rifle": R, "fallen": R, "heavy": H, "far": H})   # the game's: as it was

    def test_each_kind_its_own_model(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, {UNIT: ({"rigged": True, "also": []}, RIFLE.lower()),
                               f"{UNIT}@bazooka": ({"rigged": True, "also": []}, HEAVY.lower())})
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(self.drawn(objects), {"rifle": O, "fallen": O, "heavy": OH, "far": O})
            self.assertEqual(sorted(result.own_models), [UNIT, f"{UNIT}@bazooka"])
            said = " ".join(f.message for f in result.findings)
            self.assertIn(f"files/models/{UNIT}@bazooka.glb", said)
            self.assertEqual(self.drawn(objects, "Descriptor_Unit_Squad"),
                             {"rifle": R, "fallen": R, "heavy": H, "far": H})

    def test_a_mod_made_by_an_older_studio_builds_as_before(self):
        """Its file names every soldier model of the squad ("also"): every figure draws it, as in 0.9.8.19."""
        with tempfile.TemporaryDirectory() as d:
            result, objects = self.build(self.mod(d, {UNIT: ({"rigged": True, "also": [HEAVY.lower()]}, RIFLE.lower())}))
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(self.drawn(objects), {"rifle": O, "fallen": O, "heavy": O, "far": O})

    def test_his_own_file_takes_his_model_from_an_older_file(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, {UNIT: ({"rigged": True, "also": [HEAVY.lower()]}, RIFLE.lower()),
                               f"{UNIT}@bazooka": ({"rigged": True, "also": []}, HEAVY.lower())})
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(self.drawn(objects), {"rifle": O, "fallen": O, "heavy": OH, "far": O})

    def test_a_kind_s_file_not_on_bones_is_refused_said(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, {UNIT: ({"rigged": True, "also": []}, RIFLE.lower()),
                               f"{UNIT}@bazooka": ({"rigged": False}, None)})
            result, objects = self.build(mod)
            self.assertTrue(any(f"{UNIT}@bazooka.glb" in f.message and "fitted to his bones" in f.message
                                for f in result.errors))

    def test_a_main_file_whose_soldiers_all_have_their_own_draws_none_said(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d, {UNIT: ({"rigged": True, "also": []}, HEAVY.lower()),
                               f"{UNIT}@bazooka": ({"rigged": True, "also": []}, HEAVY.lower())})
            result, objects = self.build(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertTrue(any(f.level == "warning" and "draws none of them" in f.message for f in result.findings))
            self.assertEqual(self.drawn(objects), {"rifle": R, "fallen": R, "heavy": OH, "far": R})

    def test_only_his_own_model_far_away_the_squad_wears_the_riflemen_s(self):
        """His squad-page1 case (2026-11-11): the bazooka man alone has a model of his own (painted red in Blender).
        Up close he draws it; far away the squad's figure is the riflemen's, the game's rifleman ("They're definitely
        red from up high. But up close, it should be just the red bazooka guy"); the game's own squad as it was."""
        with tempfile.TemporaryDirectory() as d:
            result, objects = self.build(self.mod(d, {f"{UNIT}@bazooka": ({"rigged": True, "also": []}, HEAVY.lower())}))
            self.assertEqual([f.message for f in result.errors], [])
            self.assertEqual(self.drawn(objects), {"rifle": R, "fallen": R, "heavy": OH, "far": R})
            self.assertTrue(any("far-away figure wears its riflemen's look" in f.message for f in result.findings))
            self.assertEqual(self.drawn(objects, "Descriptor_Unit_Squad"),
                             {"rifle": R, "fallen": R, "heavy": H, "far": H})

    def test_names(self):
        self.assertEqual((build._unit_of(f"{UNIT}@bazooka"), build._own_stem(f"{UNIT}@bazooka"), build._own_stem(UNIT)),
                         (UNIT, f"{UNIT}__bazooka", UNIT))
        self.assertTrue(build._draws_own_model(OWN_HEAVY, UNIT, [UNIT, f"{UNIT}__bazooka"]))
        self.assertFalse(build._draws_own_model(OWN_HEAVY, UNIT))
        self.assertFalse(build._draws_own_model(HEAVY, UNIT, [UNIT, f"{UNIT}__bazooka"]))


class TheirAnimations(unittest.TestCase):
    """The unit's own animations are made on its main model's bones: the heavy-weapon soldier plays them when his own
    model is on the same bones (a horse and rider like the riflemen's), else what he played (rusemod.build.
    _on_main_bones). An animation made on other bones can stop the game (2026-11-09)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def build(self, keys: dict):
        mod = Path(self.tmp.name, "kinds")
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "kinds"\nversion = "1.0.0"\n', encoding="utf-8")
        (mod / "src" / "units.rndf").write_text(f"export {UNIT} is clone {E}Descriptor_Unit_Squad ( )\n", encoding="utf-8")
        anim.set_animations(mod, UNIT, {"stand": baf.build(clip(lift=3.0))})

        def own_models(run, order, result):   # (unit_own_models, as it leaves the two: each figure drawing its own)
            from rusemod.unitmodel import model_key
            name = next(n for n, op in run.created.items() if op.kind == "clone" and n.endswith("/" + UNIT))
            build._point_at_copies(run, name, {model_key(RIFLE): OWN, model_key(HEAVY): OWN_HEAVY})
            return {UNIT: (RIFLE, Path("main.glb"), "kinds"), f"{UNIT}@bazooka": (HEAVY, Path("heavy.glb"), "kinds")}
        arc = Edat(unit_data())
        with mock.patch.object(build, "unit_own_models", own_models), \
                mock.patch("rusemod.bonefit.skeleton_key", lambda glb: keys.get(Path(glb).name)):
            result = build.build_pack(arc, [build.load_mod(mod)], "0", Edat(clips_pack()))
        return result, build.load_pack(Edat(arc.to_bytes(result.changed))).base.objects

    def test_on_the_same_bones_he_plays_them(self):
        horse = (("horse bip01", "bip01"), (-1, 0))
        result, objects = self.build({"main.glb": horse, "heavy.glb": horse})
        self.assertEqual([f.message for f in result.errors], [])
        mine = anim.own_data_name("own_kinds_squad_standlod0")
        self.assertEqual(set(listings(objects, UNIT, "heavy").values()), {mine})
        self.assertEqual(set(listings(objects, UNIT, "rifle").values()), {mine})

    def test_on_other_bones_he_plays_what_he_played(self):
        for keys in ({"main.glb": (("horse bip01", "bip01"), (-1, 0)), "heavy.glb": (("bip01",), (-1,))},
                     {"main.glb": (("horse bip01", "bip01"), (-1, 0))}):     # (his on the game soldier's bones)
            with self.subTest(keys=sorted(keys)):
                result, objects = self.build(keys)
                self.assertEqual([f.message for f in result.errors], [])
                self.assertEqual(set(listings(objects, UNIT, "heavy").values()), {STAND})
                self.assertEqual(set(listings(objects, UNIT, "rifle").values()),
                                 {anim.own_data_name("own_kinds_squad_standlod0")})
                self.tmp.cleanup()
                self.tmp = tempfile.TemporaryDirectory()

    def test_which_models_play_them(self):
        class Result:
            own_models = {UNIT: ("x", Path("main.glb"), "m"), f"{UNIT}@bazooka": ("x", Path("heavy.glb"), "m")}
        same = (("a", "b"), (-1, 0))
        with mock.patch("rusemod.bonefit.skeleton_key", lambda g: same):
            self.assertEqual(build._on_main_bones(Result, UNIT), [UNIT, f"{UNIT}__bazooka"])
        with mock.patch("rusemod.bonefit.skeleton_key", lambda g: same if g.name == "main.glb" else None):
            self.assertEqual(build._on_main_bones(Result, UNIT), [UNIT])
        with mock.patch("rusemod.bonefit.skeleton_key", lambda g: None):    # (main on the game's bones)
            self.assertEqual(build._on_main_bones(Result, UNIT), [UNIT])
        self.assertEqual(build._on_main_bones(Result, "Descriptor_Unit_Other"), [])


class TheStudio(unittest.TestCase):
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
        # (the models the game's packs hold, as Library.find names them: the made-up game has no model packs)
        self.api._look_models = lambda address: ([RIFLE.lower(), HEAVY.lower()]
                                                 if "One" not in address else [RIFLE.lower()], [])
        self.mod = Path(self.home, "mods", "kinds")
        (self.mod / "src").mkdir(parents=True)
        (self.mod / "mod.toml").write_text('[mod]\nid = "kinds"\nversion = "1.0.0"\n', encoding="utf-8")
        self.api.choose_mod(str(self.mod))
        self.unit = self.api.new_unit(E + "Descriptor_Unit_Squad", "Kinds Squad", 5)["address"]
        self.models = self.mod / "files" / "models"
        self.source = Path(self.home, "rider.glb")
        self.source.write_bytes(b"glTF")
        self.calls = []

    def fitted(self, game, source_model, model_file, out, **kw):
        """rusemod.unitmodel.import_model stood in for (test_unitmodel has the fitting): the file written, its report."""
        self.calls.append((source_model, list(kw.get("others") or [])))
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"glTF fitted")
        return {"file": Path(model_file).name, "vertices": 3, "triangles": 1, "rigged": True, "like": source_model}

    def imported(self, kind=None, address=None):
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            return self.api.model_import(address or self.unit, str(self.source), kind=kind)

    def record(self, stem):
        return json.loads((self.models / f"{stem}.json").read_text(encoding="utf-8"))

    def test_its_kinds(self):
        self.assertEqual(self.api._soldier_kinds(self.unit), {"fusilier": RIFLE.lower(), "bazooka": HEAVY.lower()})
        rows = self.api.look(self.unit)["kinds"]
        self.assertEqual([(r["kind"], r["own"], r["also"]) for r in rows],
                         [("fusilier", False, ["fallen"]), ("bazooka", False, ["far"])])
        one = self.api.new_unit(E + "Descriptor_Unit_One", "One Squad", 5)["address"]
        self.assertEqual((self.api._soldier_kinds(one), self.api.look(one)["kinds"]), ({}, []))
        self.assertEqual(self.api.look(E + "Descriptor_Unit_Squad")["kinds"], [])     # (a game unit: no own models)

    def test_import_model_is_the_riflemen_s(self):
        res = self.imported()
        self.assertEqual(self.calls, [(RIFLE.lower(), [RIFLE.lower()])])   # fitted to theirs, his left out
        self.assertEqual(self.record(UNIT)["for"], "fusilier")
        self.assertFalse((self.models / f"{UNIT}@bazooka.glb").exists())
        self.assertEqual([(r["kind"], r["own"]) for r in res["kinds"]], [("fusilier", True), ("bazooka", False)])

    def test_his_own_model(self):
        self.imported()
        res = self.imported("bazooka")
        self.assertEqual(self.calls[-1], (HEAVY.lower(), [HEAVY.lower()]))
        self.assertTrue((self.models / f"{UNIT}@bazooka.glb").is_file())
        self.assertEqual({k: v for k, v in self.record(f"{UNIT}@bazooka").items() if k in ("for", "skeleton")},
                         {"for": "bazooka", "skeleton": "soldier"})
        self.assertNotIn("animations", self.record(f"{UNIT}@bazooka"))     # (the unit's are the main model's)
        self.assertEqual([(r["kind"], r["own"], r["file"]) for r in res["kinds"]],
                         [("fusilier", True, "rider.glb"), ("bazooka", True, "rider.glb")])
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "kind called medic"):
            self.imported("medic")
        # his taken out: the riflemen's stays
        res = self.api.model_import_remove(self.unit, "bazooka")
        self.assertTrue(res["model_out"])
        self.assertFalse((self.models / f"{UNIT}@bazooka.glb").exists() or (self.models / f"{UNIT}@bazooka.json").exists())
        self.assertTrue((self.models / f"{UNIT}.glb").is_file())
        self.assertEqual([(r["kind"], r["own"]) for r in res["kinds"]], [("fusilier", True), ("bazooka", False)])

    def test_his_model_on_its_bones_goes_with_the_riflemen_s(self):
        self.imported()
        self.imported("bazooka")
        his = self.models / f"{UNIT}@bazooka.json"
        his.write_text(json.dumps({**json.loads(his.read_text(encoding="utf-8")), "skeleton": "own"}), encoding="utf-8")
        res = self.api.model_import_remove(self.unit)
        self.assertEqual((res["model_out"], res["kinds_out"]), (True, ["bazooka"]))
        self.assertEqual(list(self.models.glob("*.glb")), [])
        # on the game soldier's bones, his stays
        self.imported()
        self.imported("bazooka")
        res = self.api.model_import_remove(self.unit)
        self.assertEqual((res["model_out"], res["kinds_out"]), (True, []))
        self.assertEqual([p.name for p in self.models.glob("*.glb")], [f"{UNIT}@bazooka.glb"])

    def test_a_custom_uniform_comes_back_when_the_last_model_goes_even_after_a_resize(self):
        self.api.model_copy(self.unit)
        copy = self.models / f"{UNIT}.copy.toml"
        before = copy.read_text(encoding="utf-8")
        self.assertTrue(self.imported()["copy_out"])
        self.imported("bazooka")
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            self.api.model_resize(self.unit, 1.0)    # (written anew: it kept no Custom uniform before 2026-11-11)
        self.assertEqual(self.record(UNIT)["copy_kept"], before)
        res = self.api.model_import_remove(self.unit)
        self.assertEqual((res["copy_back"], res["kinds_out"]), (False, []))   # his model is still there
        self.assertFalse(copy.exists())
        res = self.api.model_import_remove(self.unit, "bazooka")
        self.assertTrue(res["copy_back"])
        self.assertEqual(copy.read_text(encoding="utf-8"), before)

    def test_a_kept_custom_uniform_survives_every_rewrite_of_the_record(self):
        """Every Studio call that writes a model's record (files/models/<unit>.json, or a kind's) keeps the Custom
        uniform an import took the place of: Import model again, Resize, Move, Bring back the model (Blender), the
        split chosen on the page, his model's refit with the squad's. Each one in turn, the record read after each;
        then taking the models out gives the uniform back as it was. (Before 2026-11-11 _fit_model wrote the record
        anew and dropped it on the first Resize.)"""
        from rusemod import bonefit
        self.api.model_copy(self.unit)
        copy = self.models / f"{UNIT}.copy.toml"
        before = copy.read_text(encoding="utf-8")
        self.assertTrue(self.imported()["copy_out"])
        kept = lambda: self.record(UNIT).get("copy_kept")   # noqa: E731
        self.assertEqual(kept(), before)
        steps = []
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            self.api.model_import(self.unit, str(self.source))                     # Import model again
            steps.append(("import again", kept()))
            self.api.model_resize(self.unit, 1.3)                                  # Resize
            steps.append(("resize", kept()))
            self.api.model_place(self.unit, [10, 0, 0])                            # Move
            steps.append(("move", kept()))
            work, send = self.api._model_work(self.unit)                           # Bring back the model
            work.mkdir(parents=True, exist_ok=True)
            send.write_bytes(b"glTF")
            self.api.model_blender_back(self.unit)
            steps.append(("bring back", kept()))
            self.api.model_import(self.unit, str(self.source), kind="bazooka")     # his own, then the squad's refits
            self.api.model_resize(self.unit, 1.1)
            steps.append(("resize with his", kept()))
            self.api.model_place(self.unit, [0, 0, 0])
            steps.append(("move with his", kept()))
        bonefit.save_split(self.models / f"{UNIT}.glb", "bip01")                    # the split chosen on the page
        steps.append(("split", kept()))
        bonefit.save_split(self.models / f"{UNIT}.glb", None)
        steps.append(("split back", kept()))
        self.assertEqual([s for s, k in steps if k != before], [])
        self.assertNotIn("copy_kept", self.record(f"{UNIT}@bazooka"))   # (one record keeps it)
        res = self.api.model_import_remove(self.unit)       # his is on the soldier's bones: it stays, the uniform waits
        self.assertEqual((res["copy_back"], res["kinds_out"]), (False, []))
        self.assertEqual(self.record(f"{UNIT}@bazooka")["copy_kept"], before)
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            self.api.model_import(self.unit, str(self.source), kind="bazooka")     # his imported again: still kept
        self.assertEqual(self.record(f"{UNIT}@bazooka")["copy_kept"], before)
        res = self.api.model_import_remove(self.unit, "bazooka")
        self.assertTrue(res["copy_back"])
        self.assertEqual(copy.read_text(encoding="utf-8"), before)

    def test_resize_fits_his_model_again_too(self):
        self.imported()
        self.imported("bazooka")
        self.calls.clear()
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            self.api.model_resize(self.unit, 1.5)
        self.assertEqual([c[0] for c in self.calls], [RIFLE.lower(), HEAVY.lower()])
        self.assertEqual((self.record(UNIT)["size"], self.record(f"{UNIT}@bazooka")["size"]), (1.5, 1.5))
        # his file gone from where it was: nothing fitted, said
        from ruse_studio.api import StudioError
        his = self.models / f"{UNIT}@bazooka.json"
        his.write_text(json.dumps({**json.loads(his.read_text(encoding="utf-8")), "from": "D:/gone/rider.glb"}),
                       encoding="utf-8")
        self.calls.clear()
        with mock.patch("rusemod.unitmodel.import_model", self.fitted), \
                self.assertRaisesRegex(StudioError, "one of its soldiers .* again under Its soldiers"):
            self.api.model_resize(self.unit, 2.0)
        self.assertEqual(self.calls, [])

    def test_a_squad_whose_soldiers_draw_one_model_as_before(self):
        one = self.api.new_unit(E + "Descriptor_Unit_One", "One Squad", 5)["address"]
        self.imported(address=one)
        record = json.loads((self.models / "Descriptor_Unit_One_Squad.json").read_text(encoding="utf-8"))
        self.assertNotIn("for", record)


class ThePage(unittest.TestCase):
    KEYS = ("model_kinds_title", "model_kinds_how", "model_kind_game", "model_kind_own", "model_kind_also",
            "tip_model_kind_import", "tip_model_kind_remove", "model_kind_done", "model_kind_removed", "model_kinds_out",
            "model_kind_bones_other", "tip_model_import_kinds", "model_how_kinds", "tip_model_remove_kinds",
            "model_blender_how_kinds", "tip_model_blender_back_kinds", "model_blender_done_kinds")
    NAMES = {  # each text that names a button or a box, and the words of those labels
        "model_kinds_how": ("model_import",), "tip_model_import_kinds": ("uniform_custom", "test_in_game",
                                                                         "model_kinds_title"),
        "model_how_kinds": ("model_blender", "model_import", "model_kinds_title"),
        "tip_model_remove_kinds": ("uniform_custom",), "tip_model_kind_import": ("test_in_game",),
        "model_kind_done": ("test_in_game",), "tip_model_blender_back_kinds": ("test_in_game",),
        "model_blender_done_kinds": ("test_in_game",),
        "model_blender_how_kinds": ("model_blender", "model_blender_back", "model_kinds_title")}

    def test_words(self):
        ui = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
        words = tomllib.loads((ui.parent / "words.toml").read_text(encoding="utf-8"))
        langs = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
        blank = re.compile(r"\{(\w+)\}")
        for key in self.KEYS:
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), set(langs))
                for lang in langs:
                    self.assertEqual(sorted(blank.findall(words[key][lang])), sorted(blank.findall(words[key]["us"])))
        for key, labels in self.NAMES.items():
            for lang in langs:
                for label in labels:
                    self.assertIn(words[label][lang], words[key][lang], (key, lang, label))

    def test_calls(self):
        ui = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
        app, fake = (ui / "app.js").read_text(encoding="utf-8"), (ui / "fake-api.js").read_text(encoding="utf-8")
        for key in ThePage.KEYS:
            self.assertIn(f"w.{key}", app, key)
            self.assertIn(f'"{key}"', fake, key)
        for needle in ("api().model_import(address, null, 1, false, null, true, true, null, row.kind)",
                       "api().model_import_remove(address, row.kind)", "kindsBox(address, kinds, draw, changed)",
                       "r.kinds_out", "info.kinds"):
            self.assertIn(needle, app)
        for needle in ("kinds: fakeKinds(address)", "model_import_remove: async (address, kind)", "kinds_out"):
            self.assertIn(needle, fake)


if __name__ == "__main__":
    unittest.main()
