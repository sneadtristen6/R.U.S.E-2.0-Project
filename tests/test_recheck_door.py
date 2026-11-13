"""Recheck 1 of fix/door (cdd67623): RUSE Decoy's Change its animations in Blender / Bring my changes back after the
fixer's round 1. Each test is a route to a fault of reviewer 4's (tests/test_review_decoy.py) that the fixer's tests
(tests/test_fix_door.py) don't take, and each FAILS on cdd67623, by design, until that route is fixed too:

- D-F1's class: a bone moved in Edit mode (its rest place) rewrites every animation, said only "Changed in Blender";
- D-F2's class: the mod changed while Blender is open (a model on bones of its own imported again), and the next bring
  back says every animation came back as it went out while the mod plays another run than Blender shows;
- D-F3's class: an animation that only one half of the body plays by the build's rule (rusemod.animactions.choose),
  though its name has no t_ or b_, changed on the other half's bones with no word;
- D-F5: a bone added and keyed is named now, but the answer still begins "Every animation came back as it went out.";
- D-F11: a sending set aside behind a newer one that is refused is never offered again;
- D-F8's words (real Blender, RUSE_BLENDER set): a scene at 29.97 frames a second is said to have played at 30.03.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb (no game files), Blender's part played by
test_animglb's stand-in (Blenderish) with what a real Blender sends for that edit. Real Blender 4.5 gave the same
answers for the moved bone (scratch/animmodels/fix-door/recheck1/mine/rA_real_probe.py, mine/real_probe2.out.json)."""
import json
import re
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, modelin
from test_animblender import CLIP_BYTES, COMMON, RUN, SQUAD, STAND, Closed
from test_animglb import Blenderish
from test_gltf_bones import NAME
import test_review_decoy as rd     # (RealBlender's helper and BLENDER: imported by name, its test would run here too)
from test_review_decoy import HEAD_TURN, SPINE_TURN, UNIT, Door, renamed, with_new_bone


def moved(raw: bytes, bone: str, by: tuple) -> bytes:
    """What Blender sends when the modder moved a bone in Edit mode (G there) and posed nothing: its rest place and its
    place at every frame of every animation moved by `by`, in its parent's frame, in the file's units (0.1 is 10 of the
    game's units). For a bone with no bone under it (Edit mode leaves a child bone where it was)."""
    from rusemod.gltf import FLOAT, _Glb
    doc, binary = modelin.glb_document(raw)
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    node = next(i for i, n in enumerate(doc["nodes"]) if n.get("name") == bone)
    assert not doc["nodes"][node].get("children"), bone
    t = list(doc["nodes"][node].get("translation", [0.0, 0.0, 0.0]))
    doc["nodes"][node]["translation"] = [a + b for a, b in zip(t, by)]
    for a in doc["animations"]:
        for ch in a["channels"]:
            if ch["target"]["node"] == node and ch["target"]["path"] == "translation":
                s = a["samplers"][ch["sampler"]]
                vals = modelin.glb_accessor(doc, binary, s["output"])
                s["output"] = g.accessor([tuple(x + y for x, y in zip(v, by)) for v in vals], "VEC3", FLOAT,
                                         target=None)
    return g.to_bytes()


def strings(value) -> set:
    """Every string in an answer, however deep."""
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(strings(v) for v in value.values())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(strings(v) for v in value)) if value else set()
    return set()


class Recheck(Door):
    def reopen(self) -> tuple:
        """Change its animations in Blender again (the last Blender closed): (its answer, the file Blender opened)."""
        started = []
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append(model) or Closed()):
            res = self.api.decoy_blender(SQUAD, "us")
        return res, Path(started[0]).read_bytes()

    # --- D-F1's class ---
    def test_a_bone_moved_in_edit_mode_is_not_taken_in_without_a_word(self):
        """FAILS on cdd67623. In Blender the modder moved the head (points of the model lean on it) 10 game units in
        Edit mode and posed nothing. Blender moves its rest with it, so its points stay where they were; the game's
        skeleton keeps the head's rest, so a clip putting the head 10 units off puts its points 10 units off. The door
        rewrites every animation so ("Changed in Blender, this unit's own now: Stand (made_stand), Run (made_run).") and
        never says why: D-F1's bending, by a moved bone instead of a renamed one. (Real Blender 4.5, the same answer:
        recheck1/out/real_probe2.json, case editmove_head; the same move of fx_point, which no point leans on, is the
        legitimate case: there the game plays what Blender shows.) The door must refuse it in words naming the bone, or
        write nothing, or say it naming the bone."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(moved(Blenderish(start).send(), "bip01 head", (0.0, 0.1, 0.0)))
        try:
            got = self.back()
        except StudioError as exc:
            self.assertIn("bip01 head", str(exc))
            return
        if got["written"] == 0:
            return
        self.assertIn("bip01 head", got["message"],
                      f"every animation rewritten with the head off its rest, not a word of it: {got['message']}")

    # --- D-F2's class ---
    def test_a_model_imported_again_while_blender_is_open_is_not_said_to_have_come_back_as_it_went(self):
        """FAILS on cdd67623. A model on bones of its own (the Horse Squad's kind). Round one: its run changed in Blender
        and brought back. Round two: Change its animations in Blender again (the run goes out changed, as the mod has
        it); while that Blender is open the model is imported again (Import model's store, rusemod.anim.set_animations,
        as the fixer's own test of it: the animations as the file carries them); Blender sends with the run untouched,
        still showing the change. Bring my changes back says "Every animation came back as it went out." and the mod
        plays the run as the file carries it: Blender shows one run, the game plays another (D-F2), and the door's own
        rule for a model imported again while Blender was open (the module's note: nothing taken in, "and that is
        said") is said only when an animation came back changed. The fixer's
        test_a_model_animation_put_back_elsewhere_since_is_taken_in_again takes the run in again when the change was
        brought back from the same opening: only the round differs. The run must play as Blender shows it, or the door
        must say it doesn't (a refusal in words counts)."""
        from ruse_studio.api import StudioError
        files = self.own_bones_unit({"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[RUN]})
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("run", "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], ["run"])
        changed = (self.mod / anim.OWN / UNIT / files["run"]).read_bytes()
        _res, start = self.reopen()
        went = json.loads((self.work / "animations.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(a["name"] for a in went["animations"]), ["run", "stand"])
        anim.set_animations(self.mod, UNIT, {"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[RUN]})   # (imported again)
        self.send.write_bytes(Blenderish(start).send())                 # (the run untouched in Blender)
        try:
            got = self.back()
        except StudioError:
            return      # (refused in words: said)
        if re.search(r"\brun\b", got["message"]):
            return      # (said)
        self.assertEqual((self.mod / anim.OWN / UNIT / files["run"]).read_bytes(), changed,
                         f"the run plays as the model's file carries it while Blender shows it changed: {got['message']}")

    # --- D-F3's class ---
    def test_an_animation_only_one_half_plays_is_warned_whatever_its_name(self):
        """FAILS on cdd67623. A model on bones of its own (the Horse Squad's kind) with the rider's t_stand and t_run,
        the horse's gallop, whose name has no half in it, and a ride (as the Horse Squad's hr_ride); its figure lists
        the soldier's t_stand, b_stand, t_course and b_course. By the build's rule (rusemod.animactions.choose, as
        rusemod.build._own_animations calls it for each listing, and animactions.ride for the ride on long moves)
        gallop is what the bottom half's two listings play, never a top one or the ride: its top bones are never
        played, as for hr_b_run. The modder turns the head (the top half, split at the spine) in gallop: the door
        writes it and says "Changed in Blender, this unit's own now: gallop.", no word that the head may not show (it
        warns only for a name marked t_ or b_: _halves_unplayed). The same warning as for b_run is due."""
        from rusemod import animactions
        nope = COMMON + "nothing_herelod0.baf"     # (a listing's game clip this unit can't play: no action row)
        keys = ["t_stand", "b_stand", "t_course", "b_course"]
        names = ["t_stand", "t_run", "gallop", "ride"]
        self.own_bones_unit({"t_stand": CLIP_BYTES[STAND], "t_run": CLIP_BYTES[STAND], "gallop": CLIP_BYTES[RUN],
                             "ride": CLIP_BYTES[STAND]}, split="bip01 spine")
        self.api._unit_figures = lambda address: [{"figure": f"{UNIT}:GfxDescriptorFusilier", "model": NAME,
                                                   "clips": [(k, nope) for k in keys]}]
        plays = {k: animactions.choose(k, names, {}, nope)[0] for k in keys}
        self.assertEqual(sorted(k for k, n in plays.items() if n == "gallop"), ["b_course", "b_stand"])
        self.assertEqual(animactions.ride(names)[0], "ride")
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("gallop", "bip01 head", HEAD_TURN)))
        got = self.back()
        self.assertEqual(got["changed"], ["gallop"])
        self.assertIn("bip01 head", got["message"],
                      f"gallop plays on the bottom half only (listings: {plays}), changed on the head: {got['message']}")

    # --- D-F5 ---
    def test_a_bone_added_and_keyed_is_not_said_to_have_come_back_as_it_went_out(self):
        """FAILS on cdd67623. D-F5 as the reviewer found it: a bone added under the head and keyed in the run; the door
        said "Every animation came back as it went out." The bone is named now, but the answer still begins with that
        sentence: "Every animation came back as it went out. Bones made in Blender, ...: prop. ..." The run came back
        with keys the game can't play: it didn't come back as it went out."""
        start = self.open()
        self.send.write_bytes(with_new_bone(Blenderish(start).send(), "Run (made_run)", "bip01 head"))
        got = self.back()
        self.assertIn("prop", got["message"])
        self.assertNotIn("Every animation came back as it went out.", got["message"])

    # --- D-F11 ---
    def test_a_sending_set_aside_behind_a_refused_one_can_still_be_brought_back(self):
        """FAILS on cdd67623. Round one's sending (the run changed) never brought back: the next opening sets it aside
        (A) and says Bring back the set-aside sending takes it in. Round two's sending has a bone renamed, is refused,
        and the next opening sets it aside too (B). The page offers one set-aside sending, decoy_blender_state's
        "aside": B, the newest, refused each time (its refusal says to name the bone again in Blender and Send: that
        Blender is closed), and nothing drops it; A is never offered again. A sending set aside must stay reachable."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        first, start = self.reopen()
        a = Path(first["set_aside"])
        self.send.write_bytes(renamed(Blenderish(start).send(), "bip01 spine", "Spine.R"))
        with self.assertRaises(StudioError):
            self.back()
        _second, _start = self.reopen()
        offered, said = [], []
        for _ in range(3):      # (the page's button: it brings back what "aside" names)
            st = self.api.decoy_blender_state(SQUAD)
            if a.name in strings(st) or str(a) in strings(st):
                return      # (offered)
            if st["aside"] is None:
                break
            offered.append(st["aside"])
            try:
                got = self.api.decoy_blender_back(SQUAD, "us", st["aside"])
            except StudioError as exc:
                said.append(str(exc))
                continue
            if "Run (made_run)" in got["changed"]:
                return      # (brought back)
        self.fail(f"the sending set aside first ({a.name}) is never offered: the page offers {offered}, and says "
                  f"{said[-1] if said else None}")


FPS_2997 = r'''
import bpy
bpy.context.scene.render.fps = 30
bpy.context.scene.render.fps_base = 1.001      # Blender's 29.97 preset: Frame Rate 30, Base 1.001
bpy.ops.ruse.send_model()
'''


@unittest.skipUnless(rd.BLENDER and Path(rd.BLENDER).is_file(), "set RUSE_BLENDER to Blender 4.5's blender.exe")
class RecheckRealBlender(Door):
    """The door with real Blender doing the modder's part (headless), on the made-up model."""
    blender = rd.RealBlender.blender    # (its helper, not its test)

    def test_a_scene_at_29_97_frames_a_second_is_said_at_its_own_rate(self):
        """FAILS on cdd67623 (with RUSE_BLENDER). D-F8's words: Blender's scene set to the 29.97 preset (Frame Rate
        30, Base 1.001). Blender 4.5's exporter writes the keys 1/30.03 s apart; the door reads the rate from the keys'
        spacing (rusemod.rig.sampled_rate) and says "Blender's scene played at 30.03 frames a second", while the scene
        played at 29.97 (Send's own note beside the file, send.glb.json, says 29.97: the door doesn't read it). Each
        frame is still taken in frame for frame: only the rate said is wrong. (Recheck run:
        recheck1/mine/rA_real_fps2997.json.)"""
        self.open()
        self.blender(self.start, FPS_2997, "Run (made_run)")
        about = json.loads((self.work / "send.glb.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(about["fps"], 30 / 1.001, places=3)
        got = self.back()
        self.assertNotIn("30.03", got["message"])
        self.assertIn("29.97", got["message"])


if __name__ == "__main__":
    unittest.main()
