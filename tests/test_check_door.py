"""The one check of RUSE Decoy's Blender door on the joined code (join/final1, branch check/door): routes round 3's
fixes were not tested by, each a modder's plausible order of clicks. A test that FAILS here names what it found; one
that passes is a route checked and found sound, kept so it stays so.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb (no game files), Blender's part played by
test_animglb's stand-in (Blenderish), as tests/test_review_decoy.py's Door sets it up."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import shutil
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim
from test_animblender import CLIP_BYTES, RUN, SQUAD, Closed
from test_animglb import Blenderish
from test_recheck2_door import RUN_KEYS, plays
from test_review_decoy import SPINE_TURN, UNIT, Door

CHANGED = ("Run (made_run)", "bip01 spine", SPINE_TURN)


class Check(Door):
    def every_unit_run(self, speed: float) -> None:
        """RUSE Decoy's change for every unit (files/anim/clips.toml): the run at `speed`%."""
        clips = self.mod / anim.CLIPS
        clips.parent.mkdir(parents=True, exist_ok=True)
        clips.write_text(f'[clip."{anim.clip_key(RUN)}"]\nspeed = {speed:g}\n', encoding="utf-8")

    # --- round 3's undo, by the every-unit route (clips.toml) the fixer read but did not test ---
    def test_an_undo_after_an_every_unit_change_of_the_same_clip_is_not_said_to_play_as_before(self):
        """The run changed in Blender and brought back (the unit's own rows); RUSE Decoy then changes the run for every
        unit (50%); the change is undone in the same Blender and brought back. The mod then plays the every-unit run
        at 50%, so the door must not say it plays as before: it must say the Studio's change stays."""
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.every_unit_run(50)
        self.send.write_bytes(Blenderish(start).send())        # (undone in that Blender)
        got = self.back()
        if plays(self.mod, UNIT, RUN, RUN_KEYS) == {CLIP_BYTES[RUN]}:
            return      # (plays as Blender shows it)
        self.assertNotIn("Run (made_run)", got["undone"], got["message"])
        self.assertIn("Run (made_run)", got["differs"], got["message"])

    def every_unit_head(self, degrees: float) -> None:
        """RUSE Decoy's change for every unit (files/anim/clips.toml): the run's head turned `degrees` round z."""
        clips = self.mod / anim.CLIPS
        clips.parent.mkdir(parents=True, exist_ok=True)
        clips.write_text(f'[clip."{anim.clip_key(RUN)}".bone."bip01 head"]\nturn = ["z", {degrees:g}]\n',
                         encoding="utf-8")

    def test_an_undo_with_an_every_unit_turn_made_before_opening_is_still_said_as_before(self):
        """The legitimate case beside it: an every-unit change (the head turned) was there when the run went out;
        changed, brought back, undone in Blender: the mod plays what went out again, said as before."""
        self.every_unit_head(30.0)
        self.assertTrue(anim.mod_clips(self.mod))
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["undone"], got["differs"]), (["Run (made_run)"], []), got["message"])

    def test_a_run_slowed_for_every_unit_sent_back_untouched_is_not_taken_in_as_a_change(self):
        """FAILS on join/final1 (4a38ed65), by design until fixed: RUSE Decoy's every-unit change slows the run (50%);
        Change its animations in Blender, nothing changed there, Send, Bring my changes back. The door says "Changed in
        Blender, this unit's own now: Run (made_run)" and writes the unit its own rows for the run, which from then on
        win over any later RUSE Decoy change of the run for this unit. (Round 2's fixer found it on Only this unit
        and left it, its 5a; this is the every-unit route.)"""
        self.every_unit_run(50)
        start = self.open()
        self.send.write_bytes(Blenderish(start).send())        # (nothing changed in Blender)
        got = self.back()
        self.assertEqual((got["changed"], got["written"]), ([], 0), got["message"])

    def test_an_undo_with_an_every_unit_change_made_before_opening_is_still_said_as_before(self):
        """FAILS on join/final1 (4a38ed65), by design until fixed: the every-unit change (the run at 50%) was there
        when the run went out; changed, brought back, undone in Blender: the mod should play what went out again,
        said as before. It says the run was changed in Blender (the slowed clip's own route, the test above)."""
        self.every_unit_run(50)
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["undone"], got["differs"]), (["Run (made_run)"], []), got["message"])

    # --- round 3's opening that fails after the set-aside: a real failure, not a mocked one ---
    def test_blender_that_can_t_be_started_after_the_set_aside_says_where_it_is(self):
        """Choose Blender... pointed at a file that isn't a program (Windows refuses to start it: no stand-in): the
        last sending, never brought back, is set aside and the refusal names its folder; Bring back the set-aside
        sending takes it in."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))
        not_a_program = Path(self.dir.name) / "blender.exe"
        not_a_program.write_text("not a program", encoding="utf-8")
        self.api._blender = lambda: not_a_program
        with mock.patch("rusemod.models.Library", lambda game: self.lib):
            with self.assertRaises(StudioError) as caught:
                self.api.decoy_blender(SQUAD, "us")
        said = str(caught.exception)
        asides = self.api.decoy_blender_state(SQUAD)["asides"]
        self.assertEqual(len(asides), 1, said)
        self.assertIn(asides[0]["folder"], said)
        self.assertIn("Blender couldn't be opened", said)
        got = self.api.decoy_blender_back(SQUAD, "us", aside=asides[0]["name"])
        self.assertEqual(got["changed"], ["Run (made_run)"])

    def test_bring_back_after_an_opening_that_failed_says_the_set_aside_sending_not_nothing(self):
        """After that failed opening, the page's plain Bring my changes back (not the set-aside one): it must not take
        in something else nor fail in Python's own words; a refusal in words is right (nothing new was sent)."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=CHANGED))

        def fails(b, model, send, words):
            raise OSError("no such program")
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change", fails):
            with self.assertRaises(StudioError):
                self.api.decoy_blender(SQUAD, "us")
        try:
            got = self.back()
        except StudioError as exc:
            self.assertIn("Nothing has come back from Blender yet", str(exc))
            return
        self.fail(f"brought back with nothing sent since: {got['message']}")


if __name__ == "__main__":
    unittest.main()
