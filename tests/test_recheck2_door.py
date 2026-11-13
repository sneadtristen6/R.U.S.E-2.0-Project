"""Recheck 2 of fix/door (659fc768): RUSE Decoy's Change its animations in Blender / Bring my changes back after the
fixer's round 2. Each test is a route to a fault of reviewer 4's (tests/test_review_decoy.py) that the fixer's tests
(test_fix_door.py, test_fix_door2.py) and recheck 1's (test_recheck_door.py) don't take, and each FAILS on 659fc768, by
design, until that route is fixed too:

- D-F2's class: a change brought back, then RUSE Decoy's Only this unit changing the same clip for the unit (or taking
  out the change it went out with) beneath the door's own rows, then the change undone in that Blender: the door says
  "Your change undone in Blender, so they play as before again" while the mod plays the Studio's change, not the clip
  Blender shows (the undo puts the rows back without comparing what the mod then plays with what went out);
- D-F1's class: the unit's own model on the game soldier's bones (Import model's files/models/<unit>.glb, no record of
  its own) leaning on a bone the game models it copies don't, that bone moved in Blender's Edit Mode: taken in, every
  animation rewritten, no word (the points the door checks are the copied game models' only);
- D-F11's class: Change its animations in Blender failing after it set the last sending aside says nothing of it, and
  Bring my changes back then answers "Nothing has come back from Blender yet";
- D-F4's and D-F8's class (real Blender, RUSE_BLENDER set): the scene's Time Stretching makes Blender play every
  animation at half speed; each comes back cut to its first half and is written so, said only "Changed in Blender";
- D-F3's class (on the game, RUSE_GAME and the game index and the Horse Squad's files): a horse unit made from the US
  paratroopers, which ride in no truck, so the build gives it no ride of its own; its hr_ride, which no listing plays
  by the build's rule, changed in Blender is said "Changed in Blender" and nothing else, though nothing plays it (the
  door counts the ride as played unless the unit's ride is "truck").

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb, Blender's part played by test_animglb's
stand-in (Blenderish); the paratroopers' test on the game's own unit, the index and the Horse Squad's two files (as
test_horse_squad.OnTheGame), Blenderish standing in for Blender. Real Blender 4.5 and a dry-run build gave the same for
the paratroopers (scratch/animmodels/fix-door/recheck2/walks/p-ride.json)."""
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, animactions, animlist, baf, modelin
from test_animblender import CLIP_BYTES, RUN, SQUAD, Closed
from test_animglb import Blenderish
import test_fix_door2 as fd2       # (its helpers by name: its tests would run here too)
import test_review_decoy as rd     # (RealBlender's helper and BLENDER, by name likewise)
from test_gltf_bones import RECORD
from test_recheck_door import moved
from test_review_decoy import SPINE_TURN, UNIT, Door

RUN_KEYS = {"GfxDescriptorBazooka": ["t_tir"], "GfxDescriptorFusilier": ["b_course"]}   # (the run's, test_animblender)


def plays(mod: Path, unit: str, member: str, keys: dict) -> set:
    """The clips the mod plays for the figures' actions `keys` ({figure: [action]}) of the game's clip `member`, by
    ruse_studio.animblender.unit_plays' rule (a row of the unit's own, else its own change to the clip, else every
    unit's change, else the game's), on test_animblender's clips."""
    rows = anim.mod_unit_clips(mod).get(unit) or {"clips": {}, "actions": {}}
    edits = anim.mod_clips(mod)
    out = set()
    for fig, ks in keys.items():
        for k in ks:
            own = rows["actions"].get((k, fig)) or rows["actions"].get((k, None))
            if own is not None:
                out.add(Path(own).read_bytes())
            else:
                e = rows["clips"].get(member) or edits.get(member)
                out.add(anim.made(CLIP_BYTES[member], e) if e else CLIP_BYTES[member])
    return out


def game_bones_model_file(record: bytes = RECORD) -> bytes:
    """A unit's own model rigged to the game soldier's bones as Import model keeps it (rusemod.modelin.write_glb, no
    record of its own in it): one draw whose points lean on every bone of `record` but fx_point."""
    names = baf.skeleton(record)["names"]
    pts, skin, tris = [], [], []
    for k, name in enumerate(n for n in names if n != "fx_point"):
        pts += [(float(k), 0.0, 100.0), (float(k), 10.0, 100.0), (float(k), 0.0, 110.0)]
        skin += [[(name, 255)], [(name, 128), (names[0], 127)], [(name, 255)]]
        tris.append((3 * k, 3 * k + 1, 3 * k + 2))
    part = modelin.Part(modelin.RIGGED, -1, pts, [(0.0, 0.0, 1.0)] * len(pts), [(0.5, 0.5)] * len(pts), tris,
                        skin=skin, tracks=None, draw=None, static=False)
    with tempfile.TemporaryDirectory() as d:
        modelin.write_glb(modelin.Prepared([part], [], {"rigged": True}), Path(d) / "own.glb", "the model")
        return (Path(d) / "own.glb").read_bytes()


class Recheck2(Door):
    unit_clip_edit = fd2.Round2.unit_clip_edit      # (RUSE Decoy's Only this unit, test_fix_door2's helper)

    # --- D-F2's class: an undo in Blender after the Studio changed the same clip beneath the door's rows ---
    def test_an_undo_after_ruse_decoy_changed_the_same_clip_is_not_said_to_play_as_before(self):
        """FAILS on 659fc768. The run changed in Blender and brought back (the unit's own rows); RUSE Decoy's Only this
        unit then sets the unit's run to 50% (its [clip] table, beneath those rows: unit_plays reads the rows first);
        in the same Blender the change is undone and sent, and Bring my changes back pressed. The door takes the rows
        out and says "Your change undone in Blender, so they play as before again: Run (made_run).", while the mod now
        plays the run at 50%: neither as before nor what Blender shows. The run must play as Blender shows it, or the
        door must say the Studio's change plays instead (not that it plays as before)."""
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        self.unit_clip_edit(RUN, 50.0)
        self.send.write_bytes(Blenderish(start).send())        # (the change undone in that Blender, sent)
        got = self.back()
        if plays(self.mod, UNIT, RUN, RUN_KEYS) == {CLIP_BYTES[RUN]}:
            return      # (plays as Blender shows it)
        self.assertNotIn("Run (made_run)", got["undone"],
                         f"said to play as before again, while the mod plays the Studio's run at 50%, not the run "
                         f"Blender shows: {got['message']}")
        self.assertIn("Run (made_run)", got["message"])

    def test_an_undo_after_ruse_decoy_took_out_the_change_it_went_out_with_is_not_said_to_play_as_before(self):
        """FAILS on 659fc768. The same with RUSE Decoy's other way: the run went out with the unit's own copy of it (the
        head turned, Only this unit), changed in Blender and brought back; RUSE Decoy then takes that copy out (beneath
        the door's rows), and the change is undone in Blender. The door says the run plays as before again, while the
        mod plays the game's run, not the one Blender shows (the head turned)."""
        self.unit_clip_edit(RUN, turn=("z", 30.0))
        start = self.open()
        went = json.loads((self.work / "animations.json").read_text(encoding="utf-8"))
        run = next(a for a in went["animations"] if a.get("member") == RUN)
        went_clip = (self.work / run["file"]).read_bytes()
        self.send.write_bytes(Blenderish(start).send(change=(run["name"], "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], [run["name"]])
        table = anim.read_units(self.mod)
        table[UNIT] = {k: v for k, v in table[UNIT].items() if k != "clip"}     # (Only this unit: its copy reset)
        anim.write_units(self.mod, table)
        self.send.write_bytes(Blenderish(start).send())        # (undone in Blender)
        got = self.back()
        if plays(self.mod, UNIT, RUN, RUN_KEYS) == {went_clip}:
            return
        self.assertNotIn(run["name"], got["undone"],
                         f"said to play as before again, while the mod plays the game's run, not the one Blender shows "
                         f"(its head turned): {got['message']}")
        self.assertIn(run["name"], got["message"])

    # --- D-F11's class: an opening that fails after it set the last sending aside ---
    def test_an_opening_that_fails_after_setting_the_sending_aside_says_where_it_is(self):
        """FAILS on 659fc768. The run changed in Blender and sent, never brought back; Change its animations in Blender
        again fails (here: the unit plays no animation the Studio can open any more), but only after it has set that
        sending aside (decoy_blender sets it aside first). It says only "This unit plays no animation the Studio can
        open in Blender.", never that the sending was set aside or where; the page keeps what it showed before (decoy.js
        blenderOpen redraws its old state after an error), so its Bring my changes back answers "Nothing has come back
        from Blender yet", though it came back and is kept aside. The sending must still be waiting (Bring my changes
        back takes it in), or the words must say where it was set aside."""
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.assertTrue(self.api.decoy_blender_state(SQUAD)["waiting"])
        figures = self.api._unit_figures
        self.api._unit_figures = lambda address: []          # (nothing it can open now)
        said = ""
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change", lambda b, model, send, words: Closed()):
            try:
                said = self.api.decoy_blender(SQUAD, "us")["message"]
            except StudioError as exc:
                said = str(exc)
        self.api._unit_figures = figures
        if self.send.is_file():                               # (still waiting: Bring my changes back takes it in)
            self.assertEqual(self.back()["changed"], ["Run (made_run)"])
            return
        asides = self.api.decoy_blender_state(SQUAD)["asides"]
        self.assertEqual(len(asides), 1)
        self.assertIn(asides[0]["folder"], said,
                      f"the sending, set aside by an opening that failed, isn't said: {said!r}; Bring my changes back "
                      f"now answers that nothing has come back")

    # --- D-F1's class: the unit's own model on the game soldier's bones ---
    def test_a_bone_only_the_unit_s_own_model_leans_on_moved_in_edit_mode_is_not_taken_in_unsaid(self):
        """FAILS on 659fc768. The unit has a model of its own on the game soldier's bones (Import model's, with no
        record of its own: the build draws its figures with it, and it plays the unit's own clips), which leans on the
        head; the game model the unit copies doesn't (no_points_on(3)). In Blender (which shows the game model) the
        head is moved in Edit Mode, nothing posed. The door checks only the copied game models' points, so it takes the
        move in, every animation rewritten with the head off its rest ("Changed in Blender, this unit's own now: Stand
        (made_stand), Run (made_run).") and no word, while in the game the unit's own model's points on the head move
        off with it. The fixer's legitimate case (test_fix_door2: a bone no point of the unit's models leans on) is the
        same move with no model of the unit leaning on it. The door must refuse it naming the bone, or say it."""
        from ruse_studio.api import StudioError
        own = self.mod / "files" / "models" / f"{UNIT}.glb"
        own.parent.mkdir(parents=True, exist_ok=True)
        own.write_bytes(game_bones_model_file())
        self.assertEqual(self.api._own_bones_model(SQUAD), (None, None))     # (a model on the game's bones)
        self.lib.parts = lambda name: fd2.no_points_on(3)     # (the game model it copies: no point on the head)
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
                      f"the head moved in Edit Mode, which the unit's own model leans on, taken in with no word: "
                      f"{got['message']}")


TIME_STRETCH = r'''
import bpy
sc = bpy.context.scene
sc.render.frame_map_old, sc.render.frame_map_new = 100, 200    # Time Stretching: Blender plays everything at half speed
bpy.ops.ruse.send_model()
'''


@unittest.skipUnless(rd.BLENDER and Path(rd.BLENDER).is_file(), "set RUSE_BLENDER to Blender 4.5's blender.exe")
class Recheck2RealBlender(Door):
    """The door with real Blender doing the modder's part (headless), on the made-up model."""
    blender = rd.RealBlender.blender    # (its helper, not its test)

    def test_time_stretching_is_taken_in_as_blender_plays_it_or_said(self):
        """FAILS on 659fc768 (with RUSE_BLENDER). D-F4's and D-F8's class, timing done in Blender: the scene's Time
        Stretching (Output Properties > Frame Range: Old 100, New 200) makes Blender play every animation at half speed,
        each over twice its frames. Send samples each action over its own frame range with the scene's time so
        stretched, so what comes back of each is its first half at half speed; the door writes every animation so as
        the unit's own and says only "Changed in Blender, this unit's own now: Stand (made_stand), Run (made_run).":
        the second half of each is gone in the game, and nothing says why (Send's note beside the file has the scene's
        frames a second and the NLA's timing, not this). (Real Blender on the game's US rifleman: all 41 rewritten so,
        scratch/animmodels/fix-door/recheck2/walks/x-time-stretch.json.) The run must be taken in whole, as Blender
        plays it, or the stretching must be said (by Blender's name for it, or as the frames a second it comes to)."""
        self.open()
        self.blender(self.start, TIME_STRETCH)
        got = self.back()
        if "Run (made_run)" in got["changed"]:
            file = (anim.read_units(self.mod).get(UNIT) or {}).get("figure", {}).get("GfxDescriptorFusilier", {}) \
                .get("action", {}).get("b_course")
            run = baf.parse((self.mod / anim.OWN / UNIT / file).read_bytes())
            if abs(run.duration - 2 * baf.parse(CLIP_BYTES[RUN]).duration) < 1e-3:
                return      # (taken in whole, at half speed: as Blender plays it)
        self.assertTrue("Time Stretching" in got["message"] or "15 frames a second" in got["message"],
                        f"every animation cut to its first half at half speed, the stretching not said: "
                        f"{got['message']}")


GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
INDEX = Path(os.environ.get("RUSE_GAME_INDEX") or "D:/RUSE-2.0/scratch/modelgaps/game-index.sqlite")
FIXES = Path(os.environ.get("RUSE_HORSE_FIXES3") or "D:/RUSE-2.0/scratch/animmodels/fixes3")
RIFLE = FIXES / "horse-squad-rifle-death.glb"
PARA = "$/GFX/Everything/Descriptor_Para_Soldat_US_Para"
NECK_TURN = baf.axis_angle("x", 30.0)


@unittest.skipUnless(GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file(),
                     "RUSE_GAME names no game folder, or the game index or the Horse Squad's riflemen's file isn't there")
class OnTheGame(unittest.TestCase):
    """The game's own US paratroopers, the index, and the Horse Squad's riflemen's file (scratch/animmodels/fixes3)."""

    def test_the_ride_s_animation_of_a_unit_with_no_truck_is_said_to_play_nowhere(self):
        """FAILS on 659fc768. A new unit made from the US paratroopers, the Horse Squad's horse and rider imported for
        its riflemen (its animations, hr_ride among them, and Import model's pick idle1 -> hr_ride). The paratroopers
        ride in no truck on long moves (no TransportPourMorphe), so the build gives the unit no ride of its own
        (rusemod.build._own_animations: "rides in no truck on long moves, so it gets no ride of its own"), and by the
        build's rule (rusemod.animactions.choose for each of its figures' listings) no listing plays hr_ride: nothing
        plays it. In Blender the horse's neck is turned in hr_ride: the door writes it and says only "Changed in Blender,
        this unit's own now: hr_ride.", never that no action plays it (its words for that, decoy_blender_unplayed, are
        said for an animation no listing plays: the ride is counted as played unless the unit's ride is "truck")."""
        from ruse_studio.api import StudioApi
        db = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
        try:
            unit_id = db.execute("SELECT id FROM object WHERE address = ? ORDER BY shadow LIMIT 1", (PARA,)).fetchone()[0]
            self.assertIsNone(db.execute("SELECT dst FROM ref WHERE src = ? AND path = 'TransportPourMorphe'",
                                         (unit_id,)).fetchone())      # (no truck to ride in)
            figures = animlist.unit_figures(db, PARA)
        finally:
            db.close()
        home = Path(tempfile.mkdtemp(prefix="recheck2-door-"))
        self.addCleanup(shutil.rmtree, home, True)
        api = StudioApi(index_path=INDEX, game_dir=GAME, home=home)
        mod = Path(api.new_mod("Para horses")["current"])
        unit = api.new_unit(PARA, "Para Horses", 5, group="new")["address"]
        api.model_import(unit, str(RIFLE))
        tail = unit.rsplit("/", 1)[-1]
        mine = anim.own_animations(mod, tail)
        names = list(mine["animations"])
        self.assertIn("hr_ride", names)
        played = {animactions.choose(k, names, mine["plays"], clip)[0] for f in figures for k, clip in f["clips"]}
        self.assertNotIn("hr_ride", played)                   # (no listing of its figures plays it)
        api._blender = lambda: Path("C:/b/blender.exe")
        started = []
        with mock.patch("rusemod.blender.open_model_to_change",
                        lambda b, model, send, words: started.append(model) or Closed()):
            opened = api.decoy_blender(unit, "us")
        work = Path(opened["work"])
        (work / "send.glb").write_bytes(Blenderish(Path(started[0]).read_bytes())
                                        .send(change=("hr_ride", "horse neck", NECK_TURN)))
        got = api.decoy_blender_back(unit, "us")
        self.assertEqual(got["changed"], ["hr_ride"])
        self.assertIn("hr_ride", got["unplayed"],
                      f"hr_ride, which nothing plays on a unit with no truck, changed with no word of it: "
                      f"{got['message']}")


if __name__ == "__main__":
    unittest.main()
