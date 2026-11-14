"""Review 4 of feat/anim-decoy-blender (07a688b5): RUSE Decoy's Change its animations in Blender and Bring my changes
back, the Blender round trip. Each test is an edit a modder plausibly makes in Blender (or an order of clicks), and
what the door must do with it: take it in as Blender shows it, or refuse it in words. Every one of these FAILS on
07a688b5, by design, until the fault it names is fixed: the edit comes back wrong, or is dropped, without a word.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb (no game files), Blender's part played by
test_animglb's stand-in (Blenderish) with the change a real Blender makes for that edit; the reviewer's runs through the
real door with real Blender 4.5 on the game's US rifleman and the Horse Squad (scratch/animmodels/review-decoy/door.py,
scenarios.py, out/) found each fault first. RealBlender's test runs Blender itself: set RUSE_BLENDER to blender.exe
(Blender 4.5), else it is skipped."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import re
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, modelin
from ruse_studio import animblender
from test_animblender import CLIP_BYTES, FIGURES, RUN, STAND, SQUAD, Closed, FakeArc
from test_animglb import Blenderish, gltf_bytes, own_model_file
from test_gltf_bones import NAME, FakeLibrary

UNIT = "Descriptor_Unit_My_Riflemen"
SPINE_TURN = baf.axis_angle("x", 20.0)
HEAD_TURN = baf.axis_angle("z", 35.0)


class Door(unittest.TestCase):
    """The Studio's own calls, as test_animblender.Studio sets them up (a new unit of a mod, the made-up model)."""

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
        self.api._mod_dir = lambda kind="mod": self.mod
        self.api._look_models = lambda address: ([NAME], [])
        self.api._own_model_file = lambda address: self.mod / "files" / "models" / f"{UNIT}.glb"
        self.api._blender = lambda: Path("C:/b/blender.exe")
        self.api._unit_figures = lambda address: FIGURES
        self.work = self.mod / "blender" / UNIT / "animations"
        self.send = self.work / "send.glb"
        lib = FakeLibrary()
        lib.arc = FakeArc()
        lib.close = lambda: None
        self.lib = lib

    def tearDown(self):
        self.dir.cleanup()

    def open(self) -> bytes:
        """Change its animations in Blender; the file Blender opened, as bytes."""
        started = []
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append(model) or Closed()):
            self.api.decoy_blender(SQUAD, "us")
        self.start = Path(started[0])
        return self.start.read_bytes()

    def own_bones_unit(self, animations: dict, split: str | None = None) -> dict:
        """The unit's own model on bones of its own (the Horse Squad's kind), its model's animations `animations`
        ({name: clip bytes}) in the mod as Import model keeps them, its record naming them (and `split`, the bone
        its two halves meet at, as the unit's page keeps it). Returns the animations' files."""
        own = self.mod / "files" / "models" / f"{UNIT}.glb"
        own.parent.mkdir(parents=True, exist_ok=True)
        own.write_bytes(own_model_file())
        self.api._unit_figures = lambda address: []
        files = anim.set_animations(self.mod, UNIT, animations)
        record = {"skeleton": "own", "animations": [
            {"name": n, "frames": baf.parse(c).frames, "seconds": round(baf.parse(c).duration, 4), "file": files[n]}
            for n, c in animations.items()]}
        if split:
            record["split"] = split
        own.with_suffix(".json").write_text(json.dumps(record, indent=1), encoding="utf-8")
        return files

    def back(self) -> dict:
        return self.api.decoy_blender_back(SQUAD, "us")

    def rows(self) -> dict:
        f = self.mod / anim.UNITS
        return tomllib.loads(f.read_text(encoding="utf-8")).get("unit", {}).get(UNIT, {}) if f.is_file() else {}


def renamed(raw: bytes, bone: str, name: str) -> bytes:
    """What Blender sends when the modder renamed a bone (Bone Properties, or F2 on it): the same node and keys under
    the new name (Blender renames the bone's keys in every action with it)."""
    doc, binary = modelin.glb_document(raw)
    node = next(n for n in doc["nodes"] if n.get("name") == bone)
    node["name"] = name
    return gltf_bytes(doc, binary)


def with_new_bone(raw: bytes, animation: str, under: str, name: str = "prop") -> bytes:
    """What Blender sends when the modder added a bone under `under` in Edit Mode and keyed it in `animation`: one
    more joint of the skin (Send writes every bone, deforming or not), its keys in that animation, a turn of 45
    degrees half way."""
    from rusemod.gltf import FLOAT, _Glb
    import struct
    doc, binary = modelin.glb_document(raw)
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    parent = next(i for i, n in enumerate(doc["nodes"]) if n.get("name") == under)
    doc["nodes"].append({"name": name, "translation": [0.0, 0.1, 0.0]})
    new = len(doc["nodes"]) - 1
    doc["nodes"][parent].setdefault("children", []).append(new)
    skin = doc["skins"][0]
    ibm = modelin.glb_accessor(doc, binary, skin["inverseBindMatrices"])
    flat = [v for m in ibm for v in m] + list(ibm[skin["joints"].index(parent)])
    skin["joints"].append(new)
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(flat)}f", *flat)), "componentType": FLOAT,
                               "count": len(skin["joints"]), "type": "MAT4"})
    skin["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
    a = next(x for x in doc["animations"] if x["name"] == animation)
    times = modelin.glb_accessor(doc, binary, a["samplers"][0]["input"])
    half = baf.axis_angle("x", 45.0)
    turns = [half if 0 < k < len(times) - 1 else (0.0, 0.0, 0.0, 1.0) for k in range(len(times))]
    tin = a["samplers"][0]["input"]
    tout = g.accessor([tuple(q) for q in turns], "VEC4", FLOAT, target=None)
    a["samplers"].append({"input": tin, "output": tout, "interpolation": "LINEAR"})
    a["channels"].append({"sampler": len(a["samplers"]) - 1, "target": {"node": new, "path": "rotation"}})
    return g.to_bytes()


class GameSoldierBones(Door):
    """A new unit on the game soldier's bones (the made-up soldier's): its changed clips the unit's own, by action."""

    def test_a_renamed_bone_does_not_rewrite_every_animation(self):
        """FAILS on 07a688b5. In Blender the modder renamed the spine (to use Blender's mirror tools, say) and changed
        no pose. What came back has no bone of that name, so the door hangs its child under the spine's parent and
        writes the child's pose from there into a clip whose skeleton hangs it from the spine: the spine's own turn
        counted twice in every frame of every animation. Every animation is said to be "Changed in Blender" and
        written as the unit's own, bent. (Real Blender, the US rifleman's right upper arm renamed: every one of the
        41 animations rewritten, its forearm and hand off what Blender showed: out/s-bone-rename.json.) The door must
        refuse it in words (the game's skeleton can't take a renamed bone), or write nothing the modder didn't
        change."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(renamed(Blenderish(start).send(), "bip01 spine", "spine.R"))
        try:
            got = self.back()
        except StudioError as exc:
            self.assertIn("bip01 spine", str(exc))
            return
        self.assertEqual((got["changed"], got["written"]), ([], 0), got["message"])
        self.assertEqual(self.rows(), {})

    def test_a_bone_added_and_keyed_is_said(self):
        """FAILS on 07a688b5. In Blender the modder added a bone under the head and keyed it in the run (a prop to
        swing). The game's skeleton has no such bone, so it can't play it: the door drops its keys and says "Every
        animation came back as it went out.", no word of the bone. (Real Blender: out/s-bone-add.json.)"""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(with_new_bone(Blenderish(start).send(), "Run (made_run)", "bip01 head"))
        try:
            got = self.back()
        except StudioError as exc:
            self.assertIn("prop", str(exc))
            return
        self.assertIn("prop", got["message"])

    def test_an_undone_change_brought_back_again_is_not_kept_silently(self):
        """FAILS on 07a688b5. The run changed in Blender and brought back (the unit's own now); then, in the same
        Blender, the change undone (Ctrl+Z) and sent, and Bring my changes back pressed again. What came back is the
        run as it first went out, so the door says "Every animation came back as it went out." and leaves the mod
        playing the changed run: Blender shows one run, the game plays another. (Real Blender, both kinds of unit:
        out/s-revert.json, out/h-revert.json.) The run must play as Blender shows it, or the door must say it still
        plays the change."""
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        first = self.back()
        self.assertEqual(first["changed"], ["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send())     # (the change undone in Blender, sent again)
        got = self.back()
        if "Run (made_run)" in got["message"]:
            return
        figures = self.rows().get("figure") or {}
        playing = {(fig, key): f for fig, v in figures.items() for key, f in (v.get("action") or {}).items()}
        for (fig, key), f in playing.items():
            if key in ("b_course", "t_tir"):
                self.assertEqual((self.mod / anim.OWN / UNIT / f).read_bytes(), CLIP_BYTES[RUN],
                                 f"{fig} {key} still plays the change undone in Blender: {got['message']}")

    def test_brought_back_with_nothing_sent_since_opening_says_so(self):
        """FAILS on 07a688b5. The run changed, sent and brought back; Change its animations in Blender again (the page
        shows Bring my changes back while that Blender is open); the modder closes Blender without clicking Send and
        clicks Bring my changes back. Nothing came from this Blender, but the last sending (already brought back) is
        still in the work folder: the door reads it against what went out this time and says "Made in Blender, played
        by no action yet: Run (made_run). ... Not sent back (deleted or renamed in Blender), so they play as before:
        Run (blender_made_run)." None of it happened. (Real Blender: out/s-closed.json.) The door must say nothing
        came back since it opened."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.back()
        self.open()                                  # (Blender closed again without a Send)
        try:
            got = self.back()
        except StudioError:
            return
        self.assertEqual((got["new"], got["gone"]), ([], []), got["message"])

    def test_another_scene_frame_rate_plays_as_blender_plays_it(self):
        """FAILS on 07a688b5. The modder set Blender's scene to 24 frames a second (the door opened it at 30): Blender
        plays every animation slower, and Send writes each frame at its time at that rate. The door takes every
        animation in as changed (said), but makes each clip again at 30 frames a second from those frames, so each
        pose Blender showed is now a mix of its neighbours: the game's clip is off what Blender plays at those very
        moments. (Real Blender, the rifleman: all 41 animations rewritten, the run's legs up to 6 game units and
        about 6 degrees off: out/s-fps.json.) Each frame Blender sent must play as sent (within a clip's packing),
        or the door must say the frame rate isn't the game's."""
        from rusemod import rig
        start = self.open()
        doc, binary = modelin.glb_document(Blenderish(start).send())
        from rusemod.gltf import FLOAT, _Glb
        g = _Glb()
        g.doc, g.bin = doc, bytearray(binary)
        for a in doc["animations"]:      # (each frame at its time at 24 a second)
            times = [t * 30.0 / 24.0 for t in modelin.glb_accessor(doc, binary, a["samplers"][0]["input"])]
            tin = g.accessor(times, "SCALAR", FLOAT, target=None)
            g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
            for s in a["samplers"]:
                s["input"] = tin
        self.send.write_bytes(g.to_bytes())
        got = self.back()
        if "frame" in got["message"].lower():
            return
        self.assertIn("Run (made_run)", got["changed"])
        figures = self.rows()["figure"]
        mine = baf.parse((self.mod / anim.OWN / UNIT / figures["GfxDescriptorFusilier"]["action"]["b_course"])
                         .read_bytes())
        theirs = baf.parse(CLIP_BYTES[RUN])
        sk = baf.skeleton(mine.skeleton)
        worst = 0.0
        for k in range(theirs.frames):    # (frame k of what went out: Blender sent it at k / 24 s, its k / (n - 1))
            f = k / (theirs.frames - 1)
            for u in range(theirs.bones):
                b = sk["index"][u]
                a = rig.compose(*baf.sample(theirs.tracks[baf.skeleton(theirs.skeleton)["index"].index(b)], f))
                e = rig.compose(*baf.sample(mine.tracks[u], f))
                worst = max(worst, max(abs(a[4 * i + j] - e[4 * i + j]) for i in range(3) for j in range(3)))
        self.assertLess(worst, 2 * rig.TOL_BACK_FRAME, "the poses Blender sent, off at their own times")

    def test_animations_not_sent_back_are_not_said_to_have_come_back(self):
        """FAILS on 07a688b5. The stand deleted or renamed in Blender: the door rightly leaves it as it was and says
        so, but its message begins "Every animation came back as it went out." (Real Blender: out/s-actions.json,
        two actions gone, three new: "Every animation came back as it went out. Made in Blender, ...")."""
        start = self.open()
        doc, binary = modelin.glb_document(Blenderish(start).send())
        doc["animations"][0]["name"] = "Wave"
        self.send.write_bytes(gltf_bytes(doc, binary))
        got = self.back()
        self.assertEqual(got["gone"], ["Stand (made_stand)"])
        self.assertNotIn("Every animation came back as it went out.", got["message"])


class OwnBones(Door):
    """A model on bones of its own (the Horse Squad's kind): its model's animations come back by name."""

    def test_an_undone_change_brought_back_again_is_not_kept_silently(self):
        """FAILS on 07a688b5: as GameSoldierBones', for the model's own animations (real Blender, the Horse Squad's
        run: out/h-revert.json)."""
        files = self.own_bones_unit({"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[RUN]})
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("run", "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], ["run"])
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        if re.search(r"\brun\b", got["message"]):
            return
        self.assertEqual((self.mod / anim.OWN / UNIT / files["run"]).read_bytes(), CLIP_BYTES[RUN],
                         f"the run still plays the change undone in Blender: {got['message']}")

    def test_bring_back_twice_is_not_refused_as_changed_after_going_out(self):
        """FAILS on 07a688b5. The run changed and brought back; Bring my changes back pressed again with nothing new
        from Blender (a second click). The door refuses: "This unit's model or its animations changed after they
        went out to Blender, so what came back can't be taken in: open its animations in Blender again." Nothing
        changed them but its own first bring back; for a unit on the game soldier's bones the same second click
        writes the same clips again. (Real Blender: out/h-twice.json.)"""
        from ruse_studio.api import StudioError
        self.own_bones_unit({"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[RUN]})
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("run", "bip01 spine", SPINE_TURN)))
        self.back()
        try:
            self.back()
        except StudioError as exc:
            self.assertNotIn("changed after they went out", str(exc))

    def test_a_change_to_bones_the_animation_s_half_does_not_play_is_said(self):
        """FAILS on 07a688b5. A model on bones of its own plays its animations by halves (rusemod.animactions: a
        b_... animation through the bottom half's listings, a t_... one through the top's; the build points each
        listing at the model's own two masks, rusemod.unitmodel.halves, split at the record's bone): the Horse
        Squad's horse is the bottom half, its rider the top. In Blender each animation plays on every bone, so the
        modder changes the head (the top half here, split at the spine) in the bottom half's run: the door writes it
        and says "Changed in Blender, this unit's own now: b_run.", but no listing plays the run's head. (Real
        Blender, the Horse Squad: the rider's arm in hr_b_mort_balle and hr_b_run, the horse's neck in hr_ride:
        out/h-halves.json, its build's listings and masks.) The door must say which changed bones won't show."""
        from ruse_studio.api import StudioError
        self.own_bones_unit({"t_stand": CLIP_BYTES[STAND], "b_run": CLIP_BYTES[RUN]}, split="bip01 spine")
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("b_run", "bip01 head", HEAD_TURN)))
        try:
            got = self.back()
        except StudioError as exc:
            self.assertIn("bip01 head", str(exc))
            return
        self.assertEqual(got["changed"], ["b_run"])
        self.assertIn("bip01 head", got["message"])


BLENDER = os.environ.get("RUSE_BLENDER")
NLA_SCRIPT = r'''
import bpy, sys, json
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
act = bpy.data.actions[sys.argv[sys.argv.index("--") + 4]]
track = next(t for t in rig.animation_data.nla_tracks if any(s.action == act for s in t.strips))
strip = next(s for s in track.strips if s.action == act)
track.mute = False
track.lock = False
strip.scale = 2.0                      # the run played at half speed, its strip's Scale in the NLA editor
rig.animation_data.action = None       # no action showing: Blender plays the NLA
bpy.ops.ruse.send_model()
'''


@unittest.skipUnless(BLENDER and Path(BLENDER).is_file(), "set RUSE_BLENDER to Blender 4.5's blender.exe")
class RealBlender(Door):
    """The door with real Blender doing the modder's part (headless), on the made-up model."""

    def blender(self, start_glb: Path, script: str, *args) -> str:
        src = Path(__file__).resolve().parents[1] / "src" / "rusemod" / "blender_model.py"
        ops = Path(self.dir.name) / "ops.py"
        ops.write_text(script, encoding="utf-8")
        r = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", str(src), "--python", str(ops),
                            "--", str(start_glb), str(self.send), str(self.work / "words.json"), *args],
                           capture_output=True, text=True, timeout=600)
        self.assertTrue(self.send.is_file(), r.stdout[-2000:] + r.stderr[-2000:])
        return r.stdout + r.stderr

    def test_an_nla_strip_played_slower_is_taken_in_or_said(self):
        """FAILS on 07a688b5. Every animation opens as an action, each also on a track of the NLA editor (Blender's
        glTF importer stashes them there, muted). The modder plays the run at half speed the NLA's way: its track
        unmuted, its strip's Scale 2, no action showing; Blender now plays the run at half speed. Send writes every
        action as it is (Blender's exporter in its ACTIONS mode never reads a strip's timing), and the door says
        "Every animation came back as it went out.": the run plays at full speed in the game, no word. (Real
        Blender, the rifleman's Run 2: out/s-nla.json, the game's clip off what Blender showed by up to 124 game
        units.)"""
        self.open()
        said = self.blender(self.start, NLA_SCRIPT, "Run (made_run)")
        got = self.back()
        run = baf.parse((self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes()) \
            if "Run (made_run)" in got["changed"] else None
        if run is not None:      # taken in: at half speed, as Blender plays it
            self.assertAlmostEqual(run.duration, 2 * baf.parse(CLIP_BYTES[RUN]).duration, places=3)
            return
        self.assertTrue("Run (made_run)" in got["message"] or "NLA" in got["message"] or "NLA" in said,
                        f"the run's strip at half speed, dropped with no word: {got['message']}")


if __name__ == "__main__":
    unittest.main()
