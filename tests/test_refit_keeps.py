"""A new unit's model on bones of its own, fitted again from the file it was made from (Resize, Move, every plane or
ground unit at once), keeps what the modder made of it since it came in: an animation changed in RUSE Decoy (its Change
its animations in Blender writes the change into the unit's own animations by name, rusemod.anim.set_animations, as
decoy() does here; tests/test_review_loss.py walks the real door on the game) and the animation picked for an action on
the page. What can't be kept (the file's bones changed since; a new model brought in with Import model again or Bring
back the model, which brings its own animations as before) is named in the fit's report ("not_kept") and said on the
page. An animation the modder didn't change follows the file, as before (the silent-loss review's F9, a file made again
differently, waits on the owner). A unit on the game soldier's bones keeps RUSE Decoy's rows through all of it
(rusemod.anim.add_unit_clip's). The silent-loss review's F2, as a class. On test_animmodel's made-up game: no game
needed."""
import json
import re
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from rusemod import anim, animmodel, baf, modelin, unitmodel
from ruse_studio.animmodel_calls import FROM_FILE, NOT_KEPT
from test_horse_squad import finished
from test_ownrig import little_glb

E = "$/GFX/Everything/"
UNIT = "Descriptor_Unit_Beast"
ADDRESS = E + UNIT
BONES = ("Hips", "Spine", "Head")


def beast_glb(names=("Walk", "Run", "Idle"), extras=None, bones=BONES) -> bytes:
    """test_animmodel's little three-bone beast (test_ownrig.little_glb, `bones` its bones' names) with an animation
    for each of `names` (its first bone moved, a second long); `extras`: {animation name: its extras}."""
    anims = [(n, [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, 0.1 * (k + 1))], "LINEAR")])
             for k, n in enumerate(names)]
    data = little_glb(anims, names=bones)
    if not extras:
        return data
    doc, binary = modelin.glb_document(data)
    for a in doc["animations"]:
        if a["name"] in extras:
            a["extras"] = extras[a["name"]]
    from rusemod.gltf import _Glb
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    return g.to_bytes()


def says(*actions) -> dict:
    """An animation's extras naming the actions it plays (the Studio's own files have them)."""
    return {animmodel.ACTIONS_EXTRA: list(actions)}


class Refit(unittest.TestCase):
    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda: self.mod
        self.api._look_models = lambda address: (["the rifleman", "the bazooka man"], [])
        self.target = self.mod / "files" / "models" / f"{UNIT}.glb"
        self.api._own_model_file = lambda address: self.target
        self.api._own_copy_file = lambda address: None
        self.api._model_actions = lambda address, report: []
        self.api.look = lambda address: {"new_unit": True}
        self.api._own_models_of = lambda kind: [ADDRESS]
        self.api._new_units = lambda: {ADDRESS: SimpleNamespace(name="Beast")}
        self.src = root / "beast.glb"
        self.soldier = False   # (True: the file is rigged to the game soldier's bones)
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch("rusemod.unitmodel.import_model", self.fake_import()))
        stack.enter_context(mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)))
        stack.enter_context(mock.patch("rusemod.animmodel.own_bones_on", lambda game, path, models: models[0]))

    def fake_import(self):
        """import_model as the game's packs would answer (test_animmodel's): the unit's models take no model of other
        bones; on bones of its own, the real import on test_unitmodel's made-up packs. With self.soldier, a model on
        the game soldier's bones."""
        from rusemod.unitmodel import UnitModelError
        from test_unitmodel import TANK, zz_win
        real = unitmodel.import_model

        def fake(game, model, file, out, own_bones=False, clips=None, **kw):
            if self.soldier:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(b"glTF on the soldier's bones")
                return {"rigged": True, "like": model, "also": []}
            if not own_bones:
                raise UnitModelError(f"its bones aren't {model}'s: hips, spine")
            arc = zz_win()
            with mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), \
                    mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
                return real(Path("game"), TANK, file, out, own_bones=True, clips=clips, others=kw.get("others"))
        return fake

    # --- the mod's side ---
    def imported(self, data: bytes) -> dict:
        self.src.write_bytes(data)
        return self.api.model_import(ADDRESS, str(self.src))

    def clips(self) -> dict:
        own = anim.own_animations(self.mod, UNIT)["animations"]
        return {n: (self.mod / anim.OWN / UNIT / f).read_bytes() for n, f in own.items()}

    def plays(self) -> dict:
        return anim.own_animations(self.mod, UNIT)["plays"]

    def record(self) -> dict:
        return json.loads(self.target.with_suffix(".json").read_text(encoding="utf-8"))

    def decoy(self, name: str = "Walk") -> bytes:
        """One of its animations changed as RUSE Decoy's Bring my changes back keeps it (decoyblender.py: the mod's
        animations with the changed one in its place by name, rusemod.anim.set_animations, and the record's lengths):
        its first bone turned and the animation half as fast. Returns the changed clip."""
        now = self.clips()
        c = baf.parse(now[name])
        changed = baf.build(baf.with_speed(baf.with_bone(c, baf.skeleton(c.skeleton)["names"][0], turn=("x", 20.0)),
                                           50.0))
        self.assertNotEqual(changed, now[name])
        clips = {**now, name: changed}
        files = anim.set_animations(self.mod, UNIT, clips)
        self.api._record_lengths(ADDRESS, clips, files)
        return changed

    def every_unit(self) -> list:
        return finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)["lines"]

    # --- fitted again from the same file ---
    def test_resize_move_and_every_unit_keep_an_animation_changed_since(self):
        self.imported(beast_glb())
        file = self.clips()
        changed = self.decoy("Walk")
        for how, call in (("Resize", lambda: self.api.model_resize(ADDRESS, 1.0)),
                          ("Move", lambda: self.api.model_place(ADDRESS, [10, 0, 0])),
                          ("every ground unit", self.every_unit)):
            with self.subTest(how=how):
                got = call()
                self.assertEqual(self.clips(), {**file, "Walk": changed})
                if how == "every ground unit":
                    self.assertEqual(got, ["resized\tBeast\t1"])           # (nothing to say)
                else:
                    self.assertNotIn(NOT_KEPT, got["model"])
                # the record says its own length (the page's Its animations box reads it)
                walk = next(a for a in self.record()["animations"] if a["name"] == "Walk")
                self.assertEqual(walk["seconds"], round(baf.parse(changed).duration, 4))
        # and again on a change made after a fit again
        again = self.decoy("Idle")
        self.api.model_resize(ADDRESS, 2.0)
        self.assertEqual(self.clips(), {**file, "Walk": changed, "Idle": again})

    def test_a_pick_made_on_the_page_stays_and_the_file_s_own_word_follows_the_file(self):
        # the file says Idle plays idle1 and Run plays tir (a half's word, t_marche, makes no pick)
        self.imported(beast_glb(extras={"Idle": says("idle1"), "Run": says("tir"), "Walk": says("t_marche")}))
        self.assertEqual(self.plays(), {"idle1": "Idle", "tir": "Run"})
        anim.set_pick(self.mod, UNIT, "idle1", "Walk")      # picked on the page
        anim.set_pick(self.mod, UNIT, "course", "Run")
        self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.plays(), {"idle1": "Walk", "tir": "Run", "course": "Run"})
        self.api.model_place(ADDRESS, [0, 0, 5])
        self.assertEqual(self.plays(), {"idle1": "Walk", "tir": "Run", "course": "Run"})
        # the file's own word the page left alone follows the file (the file made again: Walk plays tir now)
        self.src.write_bytes(beast_glb(extras={"Idle": says("idle1"), "Walk": says("tir")}))
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.plays(), {"idle1": "Walk", "tir": "Walk", "course": "Run"})
        self.assertNotIn(NOT_KEPT, got["model"])

    def test_a_pick_taken_out_on_the_page_stays_out(self):
        self.imported(beast_glb(extras={"Idle": says("idle1")}))
        anim.set_pick(self.mod, UNIT, "idle1", None)         # back to the nearest, on the page
        self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.plays(), {})

    def test_on_other_bones_since_what_wasnt_kept_is_named(self):
        self.imported(beast_glb())
        self.decoy("Walk")
        anim.set_pick(self.mod, UNIT, "course", "Run")
        # the file made again on other bones (another making of it, as the silent-loss review's F9 case)
        self.src.write_bytes(beast_glb(("Walk", "Idle"), bones=("Hips", "Spine", "Neck")))
        new = self.clips_of_file()
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.clips(), new)                   # the file's, on its bones
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Walk"], "picks": ["course"]})
        self.assertEqual(self.record()["bones"], ["hips", "spine", "neck"])
        # every unit at once says it too (the page reads the JSON after the tab)
        self.decoy("Walk")
        self.src.write_bytes(beast_glb(("Walk", "Idle")))
        lines = self.every_unit()
        self.assertEqual(lines[0], "resized\tBeast\t1")
        self.assertEqual((lines[1].split("\t")[0], json.loads(lines[1].split("\t")[2])),
                         ("not_kept", {"animations": ["Walk"], "picks": []}))

    def clips_of_file(self) -> dict:
        """The clips the import makes of the file now (rusemod.unitmodel._import_own_bones' own way)."""
        from rusemod import rig
        r = rig.read_rig(self.src)
        record, _notes = unitmodel.own_skeleton(r)
        made, _notes = unitmodel.own_clips(r, record)
        return made

    def test_an_animation_the_file_hasn_t_got_any_more_stays_when_it_was_changed(self):
        self.imported(beast_glb())
        changed = self.decoy("Run")
        self.src.write_bytes(beast_glb(("Walk", "Idle")))   # Run taken out of the file
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(list(self.clips()), ["Walk", "Idle", "Run"])
        self.assertEqual(self.clips()["Run"], changed)
        self.assertNotIn(NOT_KEPT, got["model"])
        self.api.model_resize(ADDRESS, 1.0)                  # and on the next fit again too
        self.assertEqual(self.clips()["Run"], changed)

    def test_an_animation_left_alone_follows_the_file_without_a_word(self):
        """The file made again differently, nothing of the modder's touched: the fit takes the file's again, an
        animation it hasn't got any more goes, as before (whether a mod keeps its own making is the owner's call: the
        silent-loss review's F9)."""
        self.imported(beast_glb())
        self.src.write_bytes(beast_glb(("Walk", "Idle")))
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.clips(), self.clips_of_file())
        self.assertNotIn(NOT_KEPT, got["model"])

    def test_a_record_from_before_keeps_what_isn_t_the_file_s(self):
        """A record written before FROM_FILE (no fingerprints of what came in): an animation that isn't what the same
        file gives is the modder's, and stays."""
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        anim.set_pick(self.mod, UNIT, "course", "Run")
        record = self.record()
        del record[FROM_FILE]
        self.target.with_suffix(".json").write_text(json.dumps(record, indent=1), encoding="utf-8")
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.clips()["Walk"], changed)
        self.assertEqual(self.plays(), {"course": "Run"})
        self.assertNotIn(NOT_KEPT, got["model"])
        self.assertIn(FROM_FILE, self.record())             # (written now)
        self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.clips()["Walk"], changed)

    def test_ruse_decoy_s_bring_back_keeps_the_fingerprints(self):
        self.imported(beast_glb())
        before = self.record()[FROM_FILE]
        self.decoy("Walk")
        self.assertEqual(self.record()[FROM_FILE], before)

    # --- a new model brought in: its own animations, as before, and what of his it took the place of said ---
    def test_import_model_again_says_what_it_took_the_place_of(self):
        self.imported(beast_glb(extras={"Idle": says("idle1")}))
        file = self.clips()
        self.decoy("Walk")
        anim.set_pick(self.mod, UNIT, "idle1", "Run")
        got = self.imported(beast_glb(extras={"Idle": says("idle1")}))
        self.assertEqual(self.clips(), file)                  # the file's, as before
        self.assertEqual(self.plays(), {"idle1": "Idle"})     # the file's own word, as before
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Walk"], "picks": ["idle1"]})
        got = self.imported(beast_glb(extras={"Idle": says("idle1")}))
        self.assertNotIn(NOT_KEPT, got["model"])             # nothing of his left to take the place of

    def test_bring_back_the_model_says_what_it_took_the_place_of(self):
        """Change it in Blender's Bring back the model (ruse_studio.modelblender) takes what Blender sent in with
        Import model: its own animations, as before, and the RUSE Decoy change it took the place of named."""
        from ruse_studio.modelblender import WORK
        self.imported(beast_glb())
        self.decoy("Walk")
        work = self.mod / WORK / UNIT
        work.mkdir(parents=True)
        (work / f"{UNIT}.glb").write_bytes(beast_glb())         # what Blender sent (no Blender open: its last sending)
        got = self.api.model_blender_back(ADDRESS, 1.0)
        self.assertEqual(self.clips(), self.clips_of_file())
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Walk"], "picks": []})

    def test_a_model_on_the_game_soldier_s_bones_in_its_place_names_the_changes_that_went(self):
        self.imported(beast_glb())
        self.decoy("Walk")
        self.soldier = True
        got = self.imported(beast_glb())
        self.assertEqual(self.clips(), {})
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Walk"], "picks": []})

    # --- a unit on the game soldier's bones: RUSE Decoy's rows are the unit's, never the model's ---
    def test_on_the_game_soldier_s_bones_ruse_decoy_s_rows_stay(self):
        self.soldier = True
        self.imported(b"a soldier")
        clip = self.clips_of(beast_glb())["Walk"]
        anim.add_unit_clip(self.mod, UNIT, "t_stand", clip, name="blender_fusilier_stand")
        anim.add_unit_clip(self.mod, UNIT, "b_course", clip, name="blender_fusilier_course",
                           figure="GfxDescriptorBazooka")
        before = self.tree(self.mod / "files" / "anim")
        for how, call in (("Resize", lambda: self.api.model_resize(ADDRESS, 1.0)),
                          ("Move", lambda: self.api.model_place(ADDRESS, [10, 0, 0])),
                          ("every ground unit", self.every_unit),
                          ("Import model again", lambda: self.imported(b"a soldier"))):
            with self.subTest(how=how):
                got = call()
                self.assertEqual(self.tree(self.mod / "files" / "anim"), before)
                self.assertNotIn(NOT_KEPT, got["model"] if isinstance(got, dict) else {})

    def test_a_soldier_s_own_look_leaves_the_unit_s_animations_alone(self):
        """Change the squad in Blender's Bring my changes back and Import model for one soldier take a soldier's own
        look in (model_import with his number: ruse_studio.squadblender): the unit's animations are its own model's,
        so RUSE Decoy's change to one stays, whatever bones his look is on."""
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        self.api._soldier_place_model = lambda address, kind: "the rifleman" if str(kind or "").isdigit() else None
        self.src.write_bytes(beast_glb(("Walk", "Idle"), bones=("Hips", "Spine", "Neck")))
        got = self.api.model_import(ADDRESS, str(self.src), kind="2")
        self.assertTrue(self.target.with_name(f"{UNIT}@2.glb").is_file())
        self.assertEqual(self.clips()["Walk"], changed)
        self.assertNotIn(NOT_KEPT, got["model"])

    @staticmethod
    def clips_of(data: bytes) -> dict:
        from test_ownrig import rig_of_bytes
        made, _notes = unitmodel.own_clips(rig_of_bytes(data))
        return made

    @staticmethod
    def tree(folder: Path) -> dict:
        return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


class ThePage(unittest.TestCase):
    """What couldn't be kept is said in words, after the fit's own, in every language."""
    UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"

    def test_resize_move_import_bring_back_and_every_unit_say_it(self):
        app = (self.UI / "app.js").read_text(encoding="utf-8")
        for call in ("model_resize(address, s)", "model_place(address, moved())", "model_blender_back(address, Number",
                     "model_import(address, null, squad ? 1"):
            with self.subTest(call=call):
                after = app[app.index(call):][:700]
                self.assertIn("notKeptSaid(", after)
        self.assertIn('what === "not_kept"', app)
        self.assertRegex(app, r"function notKeptSaid\(lost\)")

    def test_its_words_in_every_language(self):
        from rusemod import schema
        from ruse_studio.api import _words
        words = _words()
        for key in ("model_kept_not_anims", "model_kept_not_picks"):
            with self.subTest(key=key):
                self.assertEqual([lang for lang in schema.APP_LANGS if not words[key].get(lang)], [])
                english = words[key]["us"]
                self.assertEqual([lang for lang in schema.APP_LANGS
                                  if lang not in ("us", "base") and words[key].get(lang) == english], [])
                self.assertEqual({lang: set(re.findall(r"\{(\w+)\}", t)) for lang, t in words[key].items()},
                                 {lang: set(re.findall(r"\{(\w+)\}", english)) for lang in words[key]})


if __name__ == "__main__":
    unittest.main()
