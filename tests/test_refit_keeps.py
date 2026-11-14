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
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import re
import struct
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


def beast_glb(names=("Walk", "Run", "Idle"), extras=None, bones=BONES, holder=None, step=0.1) -> bytes:
    """test_animmodel's little three-bone beast (test_ownrig.little_glb, `bones` its bones' names) with an animation
    for each of `names` (its first bone moved `step` times its place, a second long); `extras`: {animation name: its
    extras}; `holder`: its armature node's move, turn or size (the same bones on another rest)."""
    anims = [(n, [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, step * (k + 1))], "LINEAR")])
             for k, n in enumerate(names)]
    data = little_glb(anims, names=bones, holder=holder)
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
        decoyed = self.tree(self.mod / "files" / "anim")       # (what the build reads: units.toml and the clips)
        for how, call in (("Resize", lambda: self.api.model_resize(ADDRESS, 1.0)),
                          ("Move", lambda: self.api.model_place(ADDRESS, [10, 0, 0])),
                          ("every ground unit", self.every_unit)):
            with self.subTest(how=how):
                got = call()
                self.assertEqual(self.clips(), {**file, "Walk": changed})
                self.assertEqual(self.tree(self.mod / "files" / "anim"), decoyed)   # byte for byte as RUSE Decoy left it
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

    def test_the_same_bone_names_on_another_rest_are_other_bones(self):
        """A change is kept only on the bones it was made on, which its clip carries: the file made again with the same
        bone names on another rest (its armature twice the size) takes its own animation in its place, named (the
        resize recheck, round 1: the bones check had no test that failed without it)."""
        self.imported(beast_glb())
        self.decoy("Walk")
        self.src.write_bytes(beast_glb(holder={"scale": [2.0, 2.0, 2.0]}))
        new = self.clips_of_file()
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.record()["bones"], [b.lower() for b in BONES])     # (the same names)
        self.assertEqual(self.clips(), new)
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Walk"], "picks": []})

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

    def from_before(self) -> None:
        """The model's record as a Studio before FROM_FILE wrote it (this branch before 2026-11-12)."""
        record = self.record()
        del record[FROM_FILE]
        self.target.with_suffix(".json").write_text(json.dumps(record, indent=1), encoding="utf-8")

    def test_a_record_from_before_follows_a_file_made_again_where_the_modder_changed_nothing(self):
        """A record from before the fingerprints, its file made again since: what the model's own file carries tells
        what the last fit took in, so the animations the modder left alone follow the file (as with a record's
        fingerprints) and his RUSE Decoy change stays."""
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        self.from_before()
        self.src.write_bytes(beast_glb(step=0.2))             # (every animation of the file made again)
        new = self.clips_of_file()
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual(self.clips(), {**new, "Walk": changed})
        self.assertNotIn(NOT_KEPT, got["model"])

    def test_a_record_from_before_import_model_again_names_the_change(self):
        """Import model again over a record from before the fingerprints names the RUSE Decoy change it puts back (the
        resize recheck, round 1, tests/test_recheck_resize.py ARecordFromBefore), and nothing the modder left alone:
        from the same file; from another file, the one it was made from still there (what it gives tells) or gone
        (what the model's own file carries tells); with neither readable, every animation it had that the new model
        doesn't bring back as it was is named (never dropped without a word)."""
        other = self.src.with_name("other.glb")
        other.write_bytes(beast_glb(step=0.2))                # (another model: each of its animations another)
        for how in ("the same file", "another file", "another file, the first one gone",
                    "another file, the first one gone and the model's own file cut short"):
            with self.subTest(how=how):
                self.src.write_bytes(beast_glb())
                self.api.model_import(ADDRESS, str(self.src))
                self.decoy("Walk")
                self.from_before()
                if how == "the same file":
                    got = self.api.model_import(ADDRESS, str(self.src))
                else:
                    if "gone" in how:
                        self.src.unlink()
                    if "cut short" in how:
                        self.target.write_bytes(self.target.read_bytes()[:16])
                    got = self.api.model_import(ADDRESS, str(other))
                came = self.clips_of(self.src.read_bytes() if how == "the same file" else other.read_bytes())
                self.assertEqual(self.clips(), came)          # (the new model's own, as before)
                said = got["model"][NOT_KEPT]["animations"]
                self.assertEqual(said, ["Walk", "Run", "Idle"] if "cut short" in how else ["Walk"])
        # left alone, nothing to name
        self.src.write_bytes(beast_glb())
        self.api.model_import(ADDRESS, str(self.src))
        self.from_before()
        self.assertNotIn(NOT_KEPT, self.api.model_import(ADDRESS, str(other))["model"])

    def test_animations_that_came_along_with_a_copy_go_as_before_when_a_model_comes_in(self):
        """A copy of a unit takes its animations along with no model of its own (ruse_studio.actions; the owner,
        2026-11-10): the first model brought in brings its own in their place without a word, as before (no record of a
        fit of its own to tell a change of the modder's by; the unit it copies keeps them)."""
        anim.set_animations(self.mod, UNIT, self.clips_of(beast_glb(step=0.3)))   # (as anim.copy_unit leaves them)
        got = self.imported(beast_glb())
        self.assertEqual(self.clips(), self.clips_of(beast_glb()))
        self.assertNotIn(NOT_KEPT, got["model"])

    def test_a_record_from_before_with_a_model_on_the_game_soldier_s_bones_in_its_place(self):
        self.imported(beast_glb())
        self.decoy("Run")
        self.from_before()
        self.soldier = True
        got = self.imported(beast_glb())
        self.assertEqual(self.clips(), {})
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Run"], "picks": []})

    def test_a_record_from_before_bring_back_the_model_names_the_change(self):
        from ruse_studio.modelblender import WORK
        self.imported(beast_glb())
        self.decoy("Walk")
        self.from_before()
        work = self.mod / WORK / UNIT
        work.mkdir(parents=True)
        (work / f"{UNIT}.glb").write_bytes(beast_glb())
        got = self.api.model_blender_back(ADDRESS, 1.0)
        self.assertEqual(self.clips(), self.clips_of_file())
        self.assertEqual(got["model"][NOT_KEPT], {"animations": ["Walk"], "picks": []})

    def test_files_of_the_mod_that_can_t_be_read_never_stop_a_fit(self):
        """A clip file or the model's own file damaged on disk: Resize and Move write them anew from the file as before
        the fingerprints and name what they took the place of; nothing stops them (the resize recheck, round 1: a clip
        file whose bones' table runs past its end, and a model file cut short, stopped Resize, Move and every unit at
        once)."""
        self.imported(beast_glb())
        file = self.clips()
        bad = struct.pack("<IfHHIIII", 15, 1.0, 1, 1000, 28, 36, 8, 0) + bytes(8)
        walk = self.mod / anim.OWN / UNIT / anim.own_animations(self.mod, UNIT)["animations"]["Walk"]
        walk.write_bytes(bad)
        got = self.api.model_place(ADDRESS, [10, 0, 0])
        self.assertEqual((self.clips(), got["model"][NOT_KEPT]), (file, {"animations": ["Walk"], "picks": []}))
        # the model's own file cut short, a change of his made: kept (its clip carries its bones), the file whole again
        changed = self.decoy("Run")
        self.api.model_resize(ADDRESS, 1.0)
        whole = self.target.read_bytes()
        self.target.write_bytes(whole[:16])
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual((self.clips()["Run"], self.target.read_bytes()), (changed, whole))
        self.assertNotIn(NOT_KEPT, got["model"])
        # and with a record from before the fingerprints too (only the file it was made from tells then)
        self.from_before()
        self.target.write_bytes(whole[:16])
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual((self.clips(), self.target.read_bytes()), ({**file, "Run": changed}, whole))
        self.assertNotIn(NOT_KEPT, got["model"])

    def test_every_unit_at_once_goes_on_past_one_that_fails_another_way(self):
        """One that can't be fitted leaves the rest, whatever stopped it; the job then ends failed with it (for a bug
        report), never as done (the resize recheck, round 1)."""
        units = ["$/GFX/Everything/Descriptor_Unit_One", ADDRESS]
        self.api._own_models_of = lambda kind: units
        self.api._new_units = lambda: {units[0]: SimpleNamespace(name="One"), ADDRESS: SimpleNamespace(name="Beast")}
        self.imported(beast_glb())
        real = self.api.model_resize

        def resize(address, size):
            if address == units[0]:
                raise KeyError("a fault of the Studio")
            return real(address, size)
        self.api.model_resize = resize
        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)
        self.assertEqual(view["lines"], ["skipped\tOne\tKeyError: 'a fault of the Studio'", "resized\tBeast\t1"])
        self.assertEqual((view["state"], view["message"]),
                         ("failed", "Something went wrong: KeyError: 'a fault of the Studio'"))

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


class Near(unittest.TestCase):
    """What the model's own file carries is read back near the clips a fit wrote into it (24 of the Horse Squad's 25
    byte for byte, one with moves off by 7.7e-6): near is a float's last places, never a change RUSE Decoy keeps."""

    def setUp(self):
        self.clip = Refit.clips_of(beast_glb())["Walk"]
        self.c = baf.parse(self.clip)

    def moved(self, by: float) -> bytes:
        t = self.c.tracks[0]
        first = t.T[0]
        tracks = [baf.Track([(first[0], first[1] + by, *first[2:])] + list(t.T[1:]), t.S, t.R)] + self.c.tracks[1:]
        return baf.build(baf.Clip(self.c.duration, self.c.frames, tracks, self.c.skeleton))

    def test_near(self):
        from ruse_studio.animmodel_calls import _near
        bone = baf.skeleton(self.c.skeleton)["names"][0]
        self.assertTrue(_near(self.clip, self.clip))
        self.assertTrue(_near(self.clip, self.moved(7.7e-6)))
        self.assertFalse(_near(self.clip, self.moved(1e-3)))
        self.assertFalse(_near(self.clip, baf.build(baf.with_bone(self.c, bone, turn=("x", 0.03)))))
        self.assertFalse(_near(self.clip, baf.build(baf.with_speed(self.c, 101.0))))
        self.assertFalse(_near(self.clip, struct.pack("<IfHHIIII", 15, 1.0, 1, 1000, 28, 36, 8, 0) + bytes(8)))
        self.assertFalse(_near(self.clip, Refit.clips_of(beast_glb(holder={"scale": [2.0, 2.0, 2.0]}))["Walk"]))


class ThePage(unittest.TestCase):
    """What couldn't be kept is said in words, after the fit's own, in every language."""
    UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"

    def test_every_unit_at_once_says_a_job_that_failed_as_an_error(self):
        """The row read a job that stopped as done, with the ok mark (the resize recheck, round 1, from reading)."""
        app = (self.UI / "app.js").read_text(encoding="utf-8")
        row = app[app.index("function resizeAllRow("):]
        row = row[:row.index("\n}\n")]
        self.assertIn('if (st.state === "failed") failed = st.message', row)
        self.assertIn('say(note.textContent, failed || skipped.length || notKept.length ? "" : "ok");', row)
        self.assertIn('if (failed) say(failed, "error");', row)
        self.assertNotIn("problem(err); break;", row)     # (a job that can't be followed is the same: failed)

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
