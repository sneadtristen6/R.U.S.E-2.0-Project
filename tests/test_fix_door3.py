"""Round 3 of fix/door: the legitimate cases beside the round-2 recheck's routes (tests/test_recheck2_door.py), which the
fixes of round 3 must not take away:

- an undo in Blender with nothing changed in the Studio meanwhile is still undone in the mod and said "as before";
- the unit's own model on the game soldier's bones leaning on no point of a bone: that bone moved in Edit Mode is
  still taken in where Blender has it (only a bone some point of the unit's models leans on is refused);
- Change its animations in Blender refused (nothing it can open) leaves the last sending waiting where it was, and
  Bring my changes back still takes it in;
- Change its animations in Blender failing after it set the last sending aside (Blender can't be started) says where
  it was set aside, and Bring back the set-aside sending takes it in;
- (on the game, RUSE_GAME and the game index and the Horse Squad's files) a horse unit made from the US rifle squad,
  which rides in the troop truck: its ride's animation changed is not said to be played by no action.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb, Blender's part played by test_animglb's
stand-in (Blenderish)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, modelin
from test_animblender import CLIP_BYTES, RUN, SQUAD, Closed
from test_animglb import Blenderish
import test_fix_door2 as fd2       # (its helpers by name: its tests would run here too)
from test_gltf_bones import RECORD
from test_recheck_door import moved
from test_review_decoy import SPINE_TURN, UNIT, Door
import test_recheck2_door as rd2   # (its paths by name: its tests would run here too)
from test_recheck2_door import RUN_KEYS, plays


def model_leaning_on_all_but(left: set, record: bytes = RECORD) -> bytes:
    """A unit's own model on the game soldier's bones as Import model keeps it (no record of its own): one draw whose
    points lean on every bone of `record` but fx_point and those in `left`."""
    names = baf.skeleton(record)["names"]
    on = [n for n in names if n != "fx_point" and n not in left]
    pts, skin, tris = [], [], []
    for k, name in enumerate(on):
        pts += [(float(k), 0.0, 100.0), (float(k), 10.0, 100.0), (float(k), 0.0, 110.0)]
        skin += [[(name, 255)], [(name, 128), (on[0], 127)], [(name, 255)]]
        tris.append((3 * k, 3 * k + 1, 3 * k + 2))
    part = modelin.Part(modelin.RIGGED, -1, pts, [(0.0, 0.0, 1.0)] * len(pts), [(0.5, 0.5)] * len(pts), tris,
                        skin=skin, tracks=None, draw=None, static=False)
    with tempfile.TemporaryDirectory() as d:
        modelin.write_glb(modelin.Prepared([part], [], {"rigged": True}), Path(d) / "own.glb", "the model")
        return (Path(d) / "own.glb").read_bytes()


class Round3(Door):
    def test_an_undo_with_nothing_changed_in_the_studio_is_still_said_as_before(self):
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send())        # (undone in Blender)
        got = self.back()
        self.assertEqual((got["undone"], got["differs"]), (["Run (made_run)"], []))
        self.assertEqual(plays(self.mod, UNIT, RUN, RUN_KEYS), {CLIP_BYTES[RUN]})

    def test_a_bone_the_unit_s_own_model_leans_on_nowhere_moved_in_edit_mode_is_taken_in(self):
        own = self.mod / "files" / "models" / f"{UNIT}.glb"
        own.parent.mkdir(parents=True, exist_ok=True)
        own.write_bytes(model_leaning_on_all_but({"bip01 head"}))
        self.lib.parts = lambda name: fd2.no_points_on(3)     # (the game model it copies: no point on the head)
        start = self.open()
        self.send.write_bytes(moved(Blenderish(start).send(), "bip01 head", (0.0, 0.1, 0.0)))
        got = self.back()
        self.assertGreater(got["written"], 0)

    def test_an_opening_refused_leaves_the_sending_waiting(self):
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        figures = self.api._unit_figures
        self.api._unit_figures = lambda address: []
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change", lambda b, model, send, words: Closed()):
            with self.assertRaises(StudioError):
                self.api.decoy_blender(SQUAD, "us")
        self.api._unit_figures = figures
        state = self.api.decoy_blender_state(SQUAD)
        self.assertTrue(state["waiting"])
        self.assertEqual(state["asides"], [])
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])

    def test_an_opening_failing_after_setting_the_sending_aside_says_where_and_it_can_be_brought_back(self):
        from ruse_studio.api import StudioError

        def fails(b, model, send, words):
            raise OSError("no such program")
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change", fails):
            with self.assertRaises(StudioError) as caught:
                self.api.decoy_blender(SQUAD, "fr")
        asides = self.api.decoy_blender_state(SQUAD)["asides"]
        self.assertEqual(len(asides), 1)
        self.assertIn(asides[0]["folder"], str(caught.exception))
        self.assertIn("Blender n'a pas pu être ouvert (no such program).", str(caught.exception))
        got = self.api.decoy_blender_back(SQUAD, "us", aside=asides[0]["name"])
        self.assertEqual(got["changed"], ["Run (made_run)"])


LEGER = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"     # the US rifle squad: rides in the troop truck


@unittest.skipUnless(rd2.GAME is not None and rd2.GAME.is_dir() and rd2.INDEX.is_file() and rd2.RIFLE.is_file(),
                     "RUSE_GAME names no game folder, or the game index or the Generic Horse's riflemen's file isn't there")
class OnTheGame(unittest.TestCase):
    def test_the_ride_of_a_unit_riding_a_truck_is_not_said_to_play_nowhere(self):
        """The legitimate case beside test_recheck2_door.OnTheGame: a unit made from the US rifle squad, which rides in
        the troop truck, gets a ride of its own from the build, so its hr_ride changed in Blender is not said to be
        played by no action."""
        from ruse_studio.api import StudioApi
        home = Path(tempfile.mkdtemp(prefix="fix-door3-"))
        self.addCleanup(shutil.rmtree, home, True)
        api = StudioApi(index_path=rd2.INDEX, game_dir=rd2.GAME, home=home)
        api.new_mod("Rifle horses")
        unit = api.new_unit(LEGER, "Rifle Horses", 5, group="new")["address"]
        api.model_import(unit, str(rd2.RIFLE))
        self.assertTrue(api.rides_in(unit))
        api._blender = lambda: Path("C:/b/blender.exe")
        started = []
        with mock.patch("rusemod.blender.open_model_to_change",
                        lambda b, model, send, words: started.append(model) or Closed()):
            opened = api.decoy_blender(unit, "us")
        work = Path(opened["work"])
        (work / "send.glb").write_bytes(Blenderish(Path(started[0]).read_bytes())
                                        .send(change=("hr_ride", "horse neck", rd2.NECK_TURN)))
        got = api.decoy_blender_back(unit, "us")
        self.assertEqual((got["changed"], got["unplayed"]), (["hr_ride"], []))


if __name__ == "__main__":
    unittest.main()
