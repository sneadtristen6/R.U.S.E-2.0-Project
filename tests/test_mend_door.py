"""The door's mend of the one check's findings 14 and 15 (branch mend/door, off join/final1 8de30e95).

14: what goes out to Blender and what comes back are compared as the same thing: a clip RUSE Decoy made slower or
faster (for every unit, or Only this unit; a model's own animation of another timing too) goes out on the game's frames
(ruse_studio.animblender.on_game_frames), so sent back untouched it is the mod's clip again, never "Changed in
Blender"; a real change made in Blender on top of it is still taken in and said, at the speed it played.
15: the opening's failures said in words, in the modder's language, never Python's: Blender that can't be started
names Choose Blender… (on RUSE Decoy's page too); the file Blender opens, the set-aside and the opening's own files that
can't be written (a full disk, a file another program holds) as api.file_error says them; a set-aside stopped part way
leaves the sending where it was, still waiting, never in a folder the page doesn't list.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb (no game files), Blender's part played by
test_animglb's stand-in (Blenderish), as tests/test_review_decoy.py's Door sets it up."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import errno
import json
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf
from test_animblender import CLIP_BYTES, RUN, SQUAD, STAND
from test_animglb import Blenderish
from test_review_decoy import SPINE_TURN, UNIT, Door

CHANGED = ("Run (made_run)", "bip01 spine", SPINE_TURN)


class Timing(Door):
    """Finding 14 and its class."""

    def every_unit(self, speed: float) -> None:
        clips = self.mod / anim.CLIPS
        clips.parent.mkdir(parents=True, exist_ok=True)
        clips.write_text(f'[clip."{anim.clip_key(RUN)}"]\nspeed = {speed:g}\n', encoding="utf-8")

    def only_this_unit(self, speed: float) -> None:
        table = anim.read_units(self.mod)
        u = dict(table.get(UNIT) or {})
        u["clip"] = {**(u.get("clip") or {}), anim.clip_key(RUN): {"speed": speed}}
        table[UNIT] = u
        anim.write_units(self.mod, table)

    def untouched(self) -> dict:
        start = self.open()
        before = (self.mod / anim.UNITS).read_bytes() if (self.mod / anim.UNITS).is_file() else None
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["changed"], got["undone"], got["differs"], got["written"]), ([], [], [], 0),
                         got["message"])
        after = (self.mod / anim.UNITS).read_bytes() if (self.mod / anim.UNITS).is_file() else None
        self.assertEqual(after, before, "the unit got rows of its own for an untouched clip")
        self.assertFalse((self.mod / anim.OWN / UNIT).is_dir() and any((self.mod / anim.OWN / UNIT).iterdir()))
        return got

    def test_only_this_unit_slowed_sent_back_untouched_is_not_a_change(self):
        """Round 2's 5a route: RUSE Decoy's Only this unit at 50%."""
        self.only_this_unit(50)
        got = self.untouched()
        self.assertIn("came back as it went out", got["message"])

    def test_every_unit_made_faster_sent_back_untouched_is_not_a_change(self):
        """Faster (200%): fewer of the game's frames than the clip's keys; the mod keeps its clip, every key."""
        self.every_unit(200)
        self.untouched()

    def test_a_speed_that_is_no_whole_number_of_frames_sent_back_untouched_is_not_a_change(self):
        self.only_this_unit(70)
        self.untouched()

    def test_slowed_and_changed_in_blender_is_taken_in_at_the_speed_it_played(self):
        """The legitimate case: a real change in Blender on top of the slowed run is taken in and said, and the clip
        written plays as long as the slowed run did (the same speed), the change in it."""
        self.every_unit(50)
        slowed = baf.parse(anim.made(CLIP_BYTES[RUN], {"speed": 50.0}))
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        got = self.back()
        self.assertEqual((got["changed"], got["written"]), (["Run (made_run)"], 1), got["message"])
        self.assertIn("Changed in Blender, this unit's own now: Run (made_run)", got["message"])
        own = sorted((self.mod / anim.OWN / UNIT).glob("*.baf"))
        self.assertEqual(len(own), 1)
        written = baf.parse(own[0].read_bytes())
        self.assertAlmostEqual(written.duration, slowed.duration, delta=1.0 / baf.FPS)
        self.assertEqual(written.frames, round(slowed.duration * baf.FPS) + 1)

    def test_slowed_changed_then_undone_in_blender_plays_the_slowed_run_again(self):
        """Only this unit's 50%: changed, brought back, undone in Blender: the unit's rows go, the slowed run plays
        again, said as before."""
        self.only_this_unit(50)
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["undone"], got["differs"], got["changed"]), (["Run (made_run)"], [], []), got["message"])
        self.assertNotIn("figure", anim.read_units(self.mod).get(UNIT) or {})

    def test_a_clip_on_the_game_s_frames_goes_out_as_it_is(self):
        """Every clip already on the game's 30 a second goes out byte for byte as before: no second file is kept."""
        self.open()
        sent = json.loads((self.work / "animations.json").read_text(encoding="utf-8"))
        self.assertFalse(any("blender_file" in a for a in sent["animations"]))
        self.assertFalse(list((self.work / "clips").glob("*.blender.baf")))

    def test_an_opening_written_before_the_mend_is_still_read(self):
        """A work folder whose animations.json has no "blender_file" (opened by the joined code): its clips are what
        Blender was given, as before (a change made in Blender is taken in)."""
        self.every_unit(50)
        start = self.open()
        sent = json.loads((self.work / "animations.json").read_text(encoding="utf-8"))
        self.assertTrue(any("blender_file" in a for a in sent["animations"]))
        for a in sent["animations"]:
            a.pop("blender_file", None)
        (self.work / "animations.json").write_text(json.dumps(sent), encoding="utf-8")
        for f in (self.work / "clips").glob("*.blender.baf"):
            f.unlink()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        got = self.back()
        self.assertEqual(got["changed"], ["Run (made_run)"])

    def test_a_model_s_own_animation_of_another_timing_sent_back_untouched_is_not_a_change(self):
        """The class on a model on bones of its own: one of its own animations slower than the game's frames (a file
        of another timing) goes out on the game's frames and comes back as the mod's."""
        slow = baf.build(baf.with_speed(baf.parse(CLIP_BYTES[RUN]), 50.0))
        files = self.own_bones_unit({"stand": CLIP_BYTES[STAND], "run": slow})
        before = {f: (self.mod / anim.OWN / UNIT / f).read_bytes() for f in files.values()}
        start = self.open()
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["changed"], got["written"]), ([], 0), got["message"])
        self.assertEqual({f: (self.mod / anim.OWN / UNIT / f).read_bytes() for f in files.values()}, before)

    def test_a_model_s_own_slow_animation_changed_in_blender_is_taken_in(self):
        slow = baf.build(baf.with_speed(baf.parse(CLIP_BYTES[RUN]), 50.0))
        self.own_bones_unit({"stand": CLIP_BYTES[STAND], "run": slow})
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("run", "bip01 spine", SPINE_TURN)))
        got = self.back()
        self.assertEqual(got["changed"], ["run"], got["message"])


class Failures(Door):
    """Finding 15 and its class."""

    def sending_waiting(self) -> bytes:
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        return self.send.read_bytes()

    def opening(self, *patches, lang: str = "us") -> str:
        from ruse_studio.api import StudioError
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change", lambda b, model, send, words: None):
            for p in patches:
                p.start()
            try:
                with self.assertRaises(StudioError) as caught:
                    self.api.decoy_blender(SQUAD, lang)
            finally:
                for p in patches:
                    p.stop()
        said = str(caught.exception)
        for python in ("Errno", "WinError", "Traceback"):
            self.assertNotIn(python, said)
        return said

    def still_waiting(self, sent: bytes) -> None:
        state = self.api.decoy_blender_state(SQUAD)
        self.assertEqual((state["waiting"], state["asides"]), (True, []))
        self.assertEqual(self.send.read_bytes(), sent)
        self.assertEqual([p.name for p in self.work.iterdir() if p.name.startswith("sent-not-brought-")], [])
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])     # (and it can still be brought back)

    def test_a_set_aside_stopped_copying_leaves_the_sending_where_it_was(self):
        sent = self.sending_waiting()

        def held(src, dst, *a, **k):
            raise PermissionError(errno.EACCES, "Access is denied", str(src))
        said = self.opening(mock.patch("shutil.copytree", held))
        self.assertIn("another program has it open", said)
        self.assertIn("clips", said)
        self.still_waiting(sent)

    def test_a_set_aside_stopped_moving_the_sending_leaves_it_where_it_was(self):
        sent = self.sending_waiting()
        real = __import__("os").replace

        def held(src, dst):
            if Path(src).name == "send.glb":
                raise PermissionError(errno.EACCES, "Access is denied", str(src))
            return real(src, dst)
        said = self.opening(mock.patch("ruse_studio.decoyblender.os.replace", held))
        self.assertIn("send.glb couldn't be read or written, because another program has it open", said)
        self.still_waiting(sent)

    def test_a_full_disk_at_the_set_aside_is_said_in_french(self):
        sent = self.sending_waiting()

        def full(src, dst, *a, **k):
            raise OSError(errno.ENOSPC, "No space left on device", str(dst))
        said = self.opening(mock.patch("shutil.copy2", full), lang="fr")
        self.assertIn("est plein", said)
        self.still_waiting(sent)

    def test_the_file_blender_opens_that_can_t_be_written_is_said(self):
        self.sending_waiting()

        def full(*a, **k):
            raise OSError(errno.ENOSPC, "No space left on device")
        said = self.opening(mock.patch("rusemod.gltf.export", full))
        self.assertIn("is full. Make room on it, then try again.", said)
        self.assertEqual(self.api.decoy_blender_state(SQUAD)["asides"], [])     # (refused before the set-aside)

    def test_the_opening_s_state_that_can_t_be_written_is_said_with_the_set_aside(self):
        """After the set-aside: the state file held: said as a file another program holds (not "Blender couldn't be
        opened"), with the folder the sending was set aside in, which can be brought back."""
        self.sending_waiting()
        from ruse_studio import decoyblender
        real = decoyblender._write

        def held(path, data):
            if Path(path).name == "state.json" and "sent-not-brought-" not in str(path):
                raise PermissionError(errno.EACCES, "Access is denied", str(path))
            return real(path, data)
        said = self.opening(mock.patch("ruse_studio.decoyblender._write", held))
        self.assertIn("state.json couldn't be read or written, because another program has it open", said)
        self.assertNotIn("Blender couldn't be opened", said)
        asides = self.api.decoy_blender_state(SQUAD)["asides"]
        self.assertEqual(len(asides), 1)
        self.assertIn(asides[0]["folder"], said)
        self.assertEqual(self.api.decoy_blender_back(SQUAD, "us", aside=asides[0]["name"])["changed"],
                         ["Run (made_run)"])

    def test_blender_that_can_t_be_started_says_choose_blender_in_each_language(self):
        from ruse_studio.api import StudioError, words
        for lang in ("us", "fr", "jpn"):
            not_a_program = Path(self.dir.name) / "blender.exe"
            not_a_program.write_text("not a program", encoding="utf-8")
            self.api._blender = lambda: not_a_program
            with mock.patch("rusemod.models.Library", lambda game: self.lib):
                with self.assertRaises(StudioError) as caught:
                    self.api.decoy_blender(SQUAD, lang)
            said = str(caught.exception)
            self.assertIn(words(lang)["decoy_blender_open_choose"], said)
            self.assertIn(words(lang)["look_choose_blender"], said)

    def test_a_bring_back_whose_units_file_is_held_is_said_and_can_be_done_again(self):
        """The same class at Bring my changes back: the mod's animation rows held by another program as the change is
        written: said in words (not Python's), and once that program lets go, the same sending is taken in."""
        from ruse_studio.api import StudioError
        self.sending_waiting()

        def held(*a, **k):
            raise PermissionError(errno.EACCES, "Access is denied", str(self.mod / anim.UNITS))
        with mock.patch("rusemod.anim.add_unit_clip", held):
            with self.assertRaises(StudioError) as caught:
                self.back()
        said = str(caught.exception)
        self.assertIn("units.toml couldn't be read or written, because another program has it open", said)
        self.assertNotIn("Errno", said)
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])

    def test_a_sending_held_as_it_is_read_is_said(self):
        from ruse_studio.api import StudioError
        self.sending_waiting()
        real = Path.read_bytes

        def held(path):
            if path.name == "send.glb":
                raise PermissionError(errno.EACCES, "Access is denied", str(path))
            return real(path)
        with mock.patch.object(Path, "read_bytes", held):
            with self.assertRaises(StudioError) as caught:
                self.back()
        self.assertIn("send.glb couldn't be read or written, because another program has it open",
                      str(caught.exception))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])

    def test_a_set_aside_that_works_is_still_listed_and_brought_back(self):
        """The legitimate case: nothing held, the sending is set aside whole, listed, and brought back."""
        self.sending_waiting()
        self.open()
        got = self.api.decoy_blender_state(SQUAD)
        self.assertEqual(len(got["asides"]), 1)
        folder = Path(got["asides"][0]["folder"])
        self.assertTrue((folder / "send.glb").is_file() and (folder / "animations.json").is_file()
                        and (folder / "clips").is_dir() and (folder / "state.json").is_file())
        self.assertFalse(self.send.exists())
        self.assertEqual(self.api.decoy_blender_back(SQUAD, "us", aside=got["asides"][0]["name"])["changed"],
                         ["Run (made_run)"])


SEND_ONLY = '''
import bpy
bpy.ops.ruse.send_model()
'''
TURN_SPINE = r'''
import bpy, math, sys
act = bpy.data.actions[sys.argv[sys.argv.index("--") + 4]]
cs = sorted((fc for fc in act.fcurves if fc.data_path == 'pose.bones["bip01 spine"].rotation_quaternion'),
            key=lambda fc: fc.array_index)
assert len(cs) == 4, len(cs)
h = math.radians(20.0) / 2
r = (math.cos(h), math.sin(h), 0.0, 0.0)
for k in range(len(cs[0].keyframe_points)):
    a = [cs[i].keyframe_points[k].co[1] for i in range(4)]
    q = (a[0]*r[0] - a[1]*r[1] - a[2]*r[2] - a[3]*r[3], a[0]*r[1] + a[1]*r[0] + a[2]*r[3] - a[3]*r[2],
         a[0]*r[2] - a[1]*r[3] + a[2]*r[0] + a[3]*r[1], a[0]*r[3] + a[1]*r[2] - a[2]*r[1] + a[3]*r[0])
    for i in range(4):
        p = cs[i].keyframe_points[k]
        p.co[1] = p.handle_left[1] = p.handle_right[1] = q[i]
for fc in cs:
    fc.update()
bpy.ops.ruse.send_model()
'''


import test_review_decoy as rd     # noqa: E402  (its real Blender helper; the module, so its tests aren't found here)


@unittest.skipUnless(rd.BLENDER and Path(rd.BLENDER).is_file(), "set RUSE_BLENDER to Blender 4.5's blender.exe")
class TimingRealBlender(Door):
    """Finding 14 with real Blender doing the modder's part (headless): untouched, and a bone turned at every key."""
    blender = rd.RealBlender.blender    # (its helper, not its test)

    def real(self, how, speed: float, script: str = SEND_ONLY) -> dict:
        self.tearDown()
        self.setUp()
        how(self, speed)
        self.open()
        self.blender(self.start, script, "Run (made_run)")
        return self.back()

    def test_slowed_or_faster_sent_back_untouched_by_real_blender_is_not_a_change(self):
        for how, speed in ((Timing.every_unit, 50), (Timing.only_this_unit, 50), (Timing.every_unit, 200),
                           (Timing.only_this_unit, 70)):
            with self.subTest(how=how.__name__, speed=speed):
                got = self.real(how, speed)
                self.assertEqual((got["changed"], got["written"]), ([], 0), got["message"])

    def test_slowed_and_turned_in_real_blender_is_taken_in(self):
        slowed = baf.parse(anim.made(CLIP_BYTES[RUN], {"speed": 50.0}))
        got = self.real(Timing.every_unit, 50, TURN_SPINE)
        self.assertEqual(got["changed"], ["Run (made_run)"], got["message"])
        own = sorted((self.mod / anim.OWN / UNIT).glob("*.baf"))
        self.assertEqual(len(own), 1)
        self.assertAlmostEqual(baf.parse(own[0].read_bytes()).duration, slowed.duration, delta=1.0 / baf.FPS)


class Page(unittest.TestCase):
    def test_ruse_decoy_s_blender_box_has_choose_blender(self):
        js = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "decoy.js").read_text(encoding="utf-8")
        box = js[js.index("function drawBlender"):js.index("async function blenderRecycle")]
        self.assertIn("w.look_choose_blender", box)
        self.assertIn("w.tip_look_choose_blender", box)
        self.assertIn("api().choose_blender()", box)


if __name__ == "__main__":
    unittest.main()
