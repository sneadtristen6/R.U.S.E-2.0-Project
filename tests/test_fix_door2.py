"""RUSE Decoy's Change its animations in Blender / Bring my changes back, round 2 of the fixes (after recheck 1,
tests/test_recheck_door.py): the routes the recheck found to the same faults, closed as a class, each with the
legitimate case beside it that must still work.

- D-F1's class: a bone that points of the model lean on moved in Blender's Edit mode is refused naming it, nothing
  written (there its points stay put; the model keeps its rest and would move them); a bone no point leans on moved so
  is taken in where Blender has it; the whole armature moved in Object mode, its mesh with it, is taken in.
- D-F2's class: each animation is compared with what the mod plays now, not with what went out: one changed in the
  Studio while Blender was open (RUSE Decoy, a set-aside sending brought back) that came back untouched keeps the
  Studio's, said; one changed in both takes Blender's, said.
- D-F3's class: a changed animation no action plays at all is said (the build's own rule picks which plays where); a
  row of the unit's own naming one of the model's animations' files plays it on that listing's half.
- D-F8's words: the rate said is the scene's as Send read it (Blender writes 29.97's keys 1/30.03 s apart).
- D-F11's class: every sending set aside is on the page, newest first, each with its own Bring back and Put it in the
  Recycle Bin, so a refused one never hides an older one, and one can go.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb (no game files), Blender's part played by
test_animglb's stand-in (Blenderish) doing what real Blender 4.5 sends for that edit (measured for the moves in Edit and
Object mode: scratch/animmodels/fix-door/round2/real_probe_rest.py, out/real_probe_rest.json). RealBlender's tests run
Blender itself: set RUSE_BLENDER to Blender 4.5's blender.exe, else they are skipped."""
import copy
import hashlib
import json
import math
import shutil
import struct
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, modelin
from test_animblender import CLIP_BYTES, COMMON, RUN, SQUAD, STAND, Closed
from test_animglb import Blenderish
from test_fix_door import at_rate
from test_gltf_bones import NAME, parts
import test_review_decoy as rd
from test_review_decoy import HEAD_TURN, SPINE_TURN, UNIT, Door, renamed
from test_recheck_door import moved


def armature_moved(raw: bytes, by: tuple) -> bytes:
    """What Blender sends when the modder moved the whole armature in Object mode (G, no key): the node the bones hang
    from and the mesh on them moved by `by` (the file's metres), each bone's inverse bind matrix with it (Blender binds
    the points where the bones rest), the animations' keys as they were (each bone's from its parent)."""
    from rusemod.gltf import FLOAT, _Glb
    doc, binary = modelin.glb_document(raw)
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    nodes = doc["nodes"]
    skin = doc["skins"][0]
    up = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
    holder = up[skin["joints"][0]]
    meshes = [i for i, n in enumerate(nodes) if "mesh" in n and "skin" in n]
    for i in [holder, *meshes]:
        t = list(nodes[i].get("translation", [0.0, 0.0, 0.0]))
        nodes[i]["translation"] = [a + b for a, b in zip(t, by)]
    out = []
    for m in modelin.glb_accessor(doc, binary, skin["inverseBindMatrices"]):     # (each times the move's inverse)
        m = list(m)
        for i in range(3):
            m[12 + i] -= m[i] * by[0] + m[4 + i] * by[1] + m[8 + i] * by[2]
        out += m
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(out)}f", *out)), "componentType": FLOAT,
                               "count": len(skin["joints"]), "type": "MAT4"})
    skin["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
    return g.to_bytes()


def no_points_on(bone: int) -> list:
    """test_gltf_bones' model with no point leaning on the skeleton's bone `bone` (its points on the root instead)."""
    out = copy.deepcopy(parts())
    remaps = {0: None, 1: [3, 6, 7, 0]}       # (FakeSpk's materials: the second draws through a SkinningRemapping)
    for part, _tex in out:
        remap = remaps[part.material]
        for k, (b, w) in enumerate(zip(part.bones, part.weights)):
            part.bones[k] = [(remap.index(0) if remap else 0) if w[i] and (remap[x] if remap else x) == bone else x
                             for i, x in enumerate(b)]
    return out


class Round2(Door):
    def reopen(self) -> tuple:
        """Change its animations in Blender again (the last Blender closed): (its answer, the file Blender opened)."""
        started = []
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append(model) or Closed()):
            res = self.api.decoy_blender(SQUAD, "us")
        return res, Path(started[0]).read_bytes()

    def own_files(self) -> dict:
        folder = self.mod / anim.OWN / UNIT
        return {p.name: p.read_bytes() for p in folder.glob("*.baf")} if folder.is_dir() else {}

    # --- D-F1's class: where a bone rests ---
    def test_a_bone_points_lean_on_moved_in_edit_mode_is_refused_naming_it(self):
        from ruse_studio.api import StudioError
        start = self.open()
        state = json.loads((self.work / "state.json").read_text(encoding="utf-8"))
        self.assertIn("bip01 head", state["points"])          # (kept when it went out: the model's points)
        self.assertNotIn("fx_point", state["points"])
        self.send.write_bytes(moved(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)),
                                    "bip01 head", (0.0, 0.1, 0.0)))
        with self.assertRaisesRegex(StudioError, "^These bones of this unit's skeleton were moved in Blender's Edit "
                                                 "Mode, where they rest: bip01 head\\. "):
            self.back()
        self.assertEqual((self.rows(), self.own_files()), ({}, {}))     # (nothing written, not even the spine's turn)
        self.assertTrue(self.api.decoy_blender_state(SQUAD)["waiting"])

    def test_a_bone_no_point_leans_on_moved_in_edit_mode_is_taken_in_where_blender_has_it(self):
        """The same move of a bone no point of the unit's models leans on (an effect's point): the game moves nothing
        with it, so it is taken in, the bone where Blender shows it at every frame."""
        self.lib.parts = lambda name: no_points_on(3)          # (no point on the head)
        start = self.open()
        state = json.loads((self.work / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("bip01 head", state["points"])
        self.send.write_bytes(moved(Blenderish(start).send(), "bip01 head", (0.0, 0.1, 0.0)))
        got = self.back()
        self.assertEqual(sorted(got["changed"]), ["Run (made_run)", "Stand (made_stand)"])
        clip = baf.parse(self.own_files()["blender_made_run.baf"])
        sk = baf.skeleton(clip.skeleton)
        head = sk["index"].index(sk["names"].index("bip01 head"))
        theirs = baf.parse(CLIP_BYTES[RUN])
        # (from its parent, fx_point, as it went out: 0.1 of the file's metres off at every frame, 10 game units)
        off = [math.dist(baf.sample(clip.tracks[head], k / (clip.frames - 1))[0],
                         baf.sample(theirs.tracks[head], k / (clip.frames - 1))[0]) for k in range(clip.frames)]
        self.assertTrue(all(abs(d - 10.0) < 0.05 for d in off), off)

    def test_the_whole_armature_moved_in_object_mode_is_taken_in(self):
        """Real Blender moves the bones, their binds and the mesh together when the armature is moved in Object mode
        (real_probe_rest.json, case objmove): no bone moved off its points, so nothing is refused; every animation is
        taken in, as Blender shows it (the whole unit moved)."""
        start = self.open()
        self.send.write_bytes(armature_moved(Blenderish(start).send(), (0.0, 0.0, 0.1)))
        got = self.back()
        self.assertEqual(sorted(got["changed"]), ["Run (made_run)", "Stand (made_stand)"])
        self.assertEqual(got["written"], 2)

    def test_a_moved_bone_of_a_model_on_bones_of_its_own_is_refused(self):
        from ruse_studio.api import StudioError
        files = self.own_bones_unit({"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[RUN]})
        before = {f: (self.mod / anim.OWN / UNIT / f).read_bytes() for f in files.values()}
        start = self.open()
        self.send.write_bytes(moved(Blenderish(start).send(change=("run", "bip01 spine", SPINE_TURN)),
                                    "bip01 head", (0.0, 0.1, 0.0)))
        with self.assertRaisesRegex(StudioError, "Edit Mode, where they rest: bip01 head\\. "):
            self.back()
        self.assertEqual({f: (self.mod / anim.OWN / UNIT / f).read_bytes() for f in files.values()}, before)

    # --- D-F2's class: compared with what the mod plays now ---
    def unit_clip_edit(self, member: str, speed: float | None = None, turn: tuple | None = None) -> None:
        """RUSE Decoy's Only this unit: the unit's own copy of a game clip at another speed, or with the head turned
        (units.toml's clip table)."""
        table = anim.read_units(self.mod)
        u = dict(table.get(UNIT) or {})
        edit = {"speed": speed} if speed else {"bone": {"bip01 head": {"turn": list(turn)}}}
        u["clip"] = {**(u.get("clip") or {}), anim.clip_key(member): edit}
        table[UNIT] = u
        anim.write_units(self.mod, table)

    def test_a_ruse_decoy_change_made_while_blender_was_open_stays_and_is_said(self):
        start = self.open()
        self.unit_clip_edit(RUN, 50.0)
        before = (self.mod / anim.UNITS).read_bytes()
        self.send.write_bytes(Blenderish(start).send())             # (the run untouched in Blender)
        got = self.back()
        self.assertEqual((got["differs"], got["changed"], got["written"]), (["Run (made_run)"], [], 0))
        self.assertIn("Changed in the Studio since they went out to Blender, and sent back from Blender unchanged, so "
                      "the Studio's change stays, not what Blender sent: Run (made_run).", got["message"])
        self.assertNotIn("came back as it went out", got["message"])
        self.assertEqual((self.mod / anim.UNITS).read_bytes(), before)      # (RUSE Decoy's change as it was)

    def test_a_ruse_decoy_reset_or_every_unit_change_while_blender_was_open_is_said_too(self):
        """The same for RUSE Decoy's other ways: the unit's own copy taken out (Only this unit, reset) after the run
        went out with it, and a change for every unit (files/anim/clips.toml): each keeps the Studio's, said. (The
        copy turns the head: a copy at another speed has its frames at another rate, which comes back from Blender
        as a change of its own, a separate finding.)"""
        self.unit_clip_edit(RUN, turn=("z", 30.0))
        start = self.open()                                   # (the run goes out with the head turned, its own copy)
        table = anim.read_units(self.mod)
        table.pop(UNIT)
        anim.write_units(self.mod, table)                     # (reset: every unit's run again)
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["differs"], got["written"]), (["Run (made_run)"], 0))
        self.assertFalse((self.mod / anim.UNITS).exists())
        self.tearDown()
        self.setUp()
        start = self.open()
        clips = self.mod / anim.CLIPS
        clips.parent.mkdir(parents=True, exist_ok=True)
        clips.write_text(f'[clip."{anim.clip_key(RUN)}"]\nspeed = 50\n', encoding="utf-8")
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["differs"], got["written"]), (["Run (made_run)"], 0))

    def test_a_change_made_in_both_takes_blender_s_and_says_so(self):
        start = self.open()
        self.unit_clip_edit(RUN, 50.0)
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        got = self.back()
        self.assertEqual((got["changed"], got["replaced"], got["written"]), (["Run (made_run)"], ["Run (made_run)"], 1))
        self.assertIn("Changed in the Studio too since they went out to Blender: Blender's change takes the place of "
                      "the Studio's: Run (made_run).", got["message"])
        # the legitimate case: nothing changed in the Studio meanwhile, so nothing of the kind is said
        self.tearDown()
        self.setUp()
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        got = self.back()
        self.assertEqual((got["changed"], got["replaced"], got["differs"]), (["Run (made_run)"], [], []))

    def test_a_set_aside_sending_brought_back_while_blender_is_open_is_said_by_the_next(self):
        """Round one: the run changed and brought back, then undone in that Blender and sent, never brought back. Round
        two opens (that sending set aside; the run goes out changed, as the mod has it). The set-aside sending is
        brought back: the run undone in the mod. Round two's Blender sends the run untouched, still changed: the mod
        keeps the set-aside one's, and that is said, never that every animation came back as it went out."""
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send())                 # (undone in Blender, sent, not brought back)
        res, start = self.reopen()
        aside = Path(res["set_aside"]).name
        got = self.api.decoy_blender_back(SQUAD, "us", aside)
        self.assertEqual(got["undone"], ["Run (made_run)"])
        self.assertEqual(self.own_files(), {})
        self.send.write_bytes(Blenderish(start).send())                 # (round two's Blender: the run as it went out)
        got = self.back()
        self.assertEqual((got["differs"], got["written"]), (["Run (blender_made_run)"], 0))
        self.assertNotIn("came back as it went out", got["message"])

    def test_what_the_studio_changed_to_what_came_back_is_nothing_to_say(self):
        """The legitimate case: the mod changed meanwhile to what Blender sends (here: the change brought back once,
        then the same sending again after RUSE Decoy took the unit's rows out and put the same clip back) plays as
        Blender shows it: nothing is said to differ."""
        start = self.open()
        sending = Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN))
        self.send.write_bytes(sending)
        self.back()
        clip = self.own_files()["blender_made_run.baf"]
        for fig, key in (("GfxDescriptorBazooka", "t_tir"), ("GfxDescriptorFusilier", "b_course")):
            anim.remove_unit_clip(self.mod, UNIT, key, figure=fig)
            anim.add_unit_clip(self.mod, UNIT, key, clip, name="by_hand", figure=fig)
        got = self.back()
        self.assertEqual((got["changed"], got["differs"], got["written"]), ([], [], 0))

    # --- D-F3's class: which listings play a model's own animation ---
    def halves_unit(self, names: list) -> None:
        """A model on bones of its own split at the spine, its animations `names` (the stand's or the run's clip), its
        figure listing the soldier's t_stand, b_stand, t_course and b_course (a game clip it can't play)."""
        nope = COMMON + "nothing_herelod0.baf"
        self.own_bones_unit({n: CLIP_BYTES[RUN if "run" in n else STAND] for n in names}, split="bip01 spine")
        self.api._unit_figures = lambda address: [{"figure": f"{UNIT}:GfxDescriptorFusilier", "model": NAME,
                                                   "clips": [(k, nope) for k in ("t_stand", "b_stand", "t_course",
                                                                                 "b_course")]}]

    def test_a_changed_animation_no_action_plays_is_said(self):
        """t_stand, b_run and extra: by the build's rule t_stand plays on top, b_run below and as the ride; extra on no
        listing. Its change is said, as nothing plays it; once picked for an action, nothing of the kind is said."""
        from rusemod import animactions
        self.halves_unit(["t_stand", "b_run", "extra"])
        names = ["t_stand", "b_run", "extra"]
        self.assertNotIn("extra", {animactions.choose(k, names, {}, None)[0]
                                   for k in ("t_stand", "b_stand", "t_course", "b_course")}
                         | {animactions.ride(names)[0]})
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("extra", "bip01 spine", SPINE_TURN)))
        got = self.back()
        self.assertEqual((got["changed"], got["unplayed"], got["halves"]), (["extra"], ["extra"], []))
        self.assertIn("No action of this unit plays these, so their changes won't show in the game until one does: "
                      "extra.", got["message"])
        anim.set_pick(self.mod, UNIT, "stand", "extra")
        self.send.write_bytes(Blenderish(start).send(change=("extra", "bip01 spine", HEAD_TURN)))
        got = self.back()
        self.assertEqual((got["changed"], got["unplayed"], got["halves"]), (["extra"], [], []))

    def test_a_row_of_its_own_naming_a_model_animation_plays_it_on_that_half(self):
        """A row of the unit's own for b_stand naming extra's file: the build plays extra there, on the bottom half,
        so a change to the head (the top half) is said as one the half doesn't play, not as one nothing plays."""
        self.halves_unit(["t_stand", "b_run", "extra"])
        files = anim.own_animations(self.mod, UNIT)["animations"]
        table = anim.read_units(self.mod)
        table[UNIT] = {**table[UNIT], "figure": {"GfxDescriptorFusilier": {"action": {"b_stand": files["extra"]}}}}
        anim.write_units(self.mod, table)
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("extra", "bip01 head", HEAD_TURN)))
        got = self.back()
        self.assertEqual((got["unplayed"], got["halves"]), ([], ["extra (bip01 head)"]))

    # --- D-F8's words ---
    def test_the_rate_said_is_the_scene_s_as_send_read_it(self):
        """Blender's 29.97 preset: its keys come 1/30.03 s apart, and Send's note beside the file says 29.97. Each
        frame is taken as one of the game's (the clip has the frames sent), and the rate said is the note's."""
        start = self.open()
        self.send.write_bytes(at_rate(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)),
                                      30.0 * 1.001))
        (self.work / "send.glb.json").write_text(json.dumps(
            {"glb": hashlib.sha256(self.send.read_bytes()).hexdigest(), "fps": 30 / 1.001, "nla": []}),
            encoding="utf-8")
        got = self.back()
        self.assertIn("Blender's scene played at 29.97 frames a second", got["message"])
        self.assertNotIn("30.03", got["message"])
        self.assertAlmostEqual(got["fps"], 30 / 1.001, places=4)
        mine = baf.parse(self.own_files()["blender_made_run.baf"])
        self.assertEqual(mine.frames, baf.parse(CLIP_BYTES[RUN]).frames)
        # without a note (or one of another sending), the keys' own rate is said
        (self.work / "send.glb.json").unlink()
        self.send.write_bytes(at_rate(Blenderish(start).send(change=("Run (made_run)", "bip01 head", HEAD_TURN)), 24.0))
        got = self.back()
        self.assertIn("Blender's scene played at 24 frames a second", got["message"])

    # --- D-F11's class: every sending set aside on the page ---
    def test_every_sending_set_aside_is_listed_and_one_can_go_to_the_recycle_bin(self):
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        first, start = self.reopen()
        a = Path(first["set_aside"])
        self.send.write_bytes(renamed(Blenderish(start).send(), "bip01 spine", "Spine.R"))
        with self.assertRaises(StudioError):
            self.back()
        second, _start = self.reopen()
        b = Path(second["set_aside"])
        st = self.api.decoy_blender_state(SQUAD)
        self.assertEqual([x["name"] for x in st["asides"]], [b.name, a.name])             # (newest first)
        self.assertEqual([x["folder"] for x in st["asides"]], [str(b), str(a)])
        self.assertRegex(st["asides"][1]["when"], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$")
        with self.assertRaisesRegex(StudioError, "If the Blender that sent it is still open"):
            self.api.decoy_blender_back(SQUAD, "us", b.name)           # (refused: its Blender is closed now)
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=OSError("close anything that has it open")):
            with self.assertRaisesRegex(StudioError, "can't be moved to the Recycle Bin \\(close anything"):
                self.api.decoy_blender_recycle(SQUAD, b.name)
        self.assertTrue(b.is_dir())
        binned = []
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=lambda p: binned.append(p) or shutil.rmtree(p)):
            got = self.api.decoy_blender_recycle(SQUAD, b.name)
        self.assertEqual((binned, got["message"]),
                         ([b], "The set-aside sending is in the Recycle Bin now, nothing in it taken in."))
        self.assertEqual([x["name"] for x in got["asides"]], [a.name])
        self.assertEqual((self.rows(), self.own_files()), ({}, {}))     # (nothing of either taken in by that)
        got = self.api.decoy_blender_back(SQUAD, "us", a.name)
        self.assertEqual((got["changed"], got["asides"]), (["Run (made_run)"], []))
        for name in (b.name, "../../mod", "clips", "state.json"):
            with self.assertRaisesRegex(StudioError, "^There's no sending set aside called"):
                self.api.decoy_blender_recycle(SQUAD, name)


EDIT_MOVE = r'''
import bpy, sys
from mathutils import Vector
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
how, bone = sys.argv[sys.argv.index("--") + 4], sys.argv[sys.argv.index("--") + 5]
if how == "edit":
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones[bone]
    eb.head = eb.head + Vector((0.0, 0.0, 0.1))
    eb.tail = eb.tail + Vector((0.0, 0.0, 0.1))
    bpy.ops.object.mode_set(mode="OBJECT")
else:
    rig.location = rig.location + Vector((0.0, 0.0, 0.1))
bpy.ops.ruse.send_model()
'''


@unittest.skipUnless(rd.BLENDER and Path(rd.BLENDER).is_file(), "set RUSE_BLENDER to Blender 4.5's blender.exe")
class Round2RealBlender(Door):
    """D-F1's class with real Blender doing the modder's part (headless), on the made-up model."""
    blender = rd.RealBlender.blender    # (its helper, not its test)

    def test_edit_mode_moves_refused_or_taken_in_by_their_points_and_the_whole_armature_taken_in(self):
        from ruse_studio.api import StudioError
        for how, bone, refused in (("edit", "bip01 head", True), ("edit", "fx_point", False),
                                   ("edit", "bip01", True), ("object", "-", False)):
            with self.subTest(how=how, bone=bone):
                self.tearDown()
                self.setUp()
                self.open()
                self.blender(self.start, EDIT_MOVE, how, bone)
                if refused:
                    with self.assertRaisesRegex(StudioError, f"Edit Mode, where they rest: {bone}\\. "):
                        self.back()
                    self.assertEqual(self.rows(), {})
                else:
                    got = self.back()
                    self.assertEqual(sorted(got["changed"]), ["Run (made_run)", "Stand (made_stand)"])


if __name__ == "__main__":
    unittest.main()
