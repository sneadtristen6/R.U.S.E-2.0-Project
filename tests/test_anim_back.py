"""A model on bones of its own through the model's own Blender (Change it in Blender, the one Blender button's model
door) and back: every animation that comes back as it went out is the mod's own clip again, byte for byte, and a
changed one differs only where it was changed (the owner, 2026-11-13, item 45: "Yes, an animation that comes back from
Bundler should come back the exact same"). Before, a trip with nothing changed rewrote all 25 of the Generic Horse's
animation files, every track of each and its skeleton part (real Blender 4.5.14 on e9a092c3,
scratch/release-0920/agents/anims/out-before).

On the made-up skeleton and clips of test_gltf_bones and test_animglb (always run), Blender's part played by
test_animglb's stand-in (each key on its frame, a straight line through a turn's four numbers between keys, every
frame sampled on the way back, no extras kept, the bones in an order of its own): what goes out (rusemod.modelin.
own_animations_glb), what the Bring back puts back in the file (rusemod.rig.with_record, with_went_out) and what the
import keeps (rusemod.rig.kept_clips). On the game (RUSE_GAME, the Studio's index and the passed copy's two horse
files, as tests/test_horse_squad.py; skipped without them): the Generic Horse added through the Studio's own Add and
taken through the one Blender button's Open in Blender and Bring my changes back, the mod's files judged byte for
byte. The real Blender's walks are scratch/release-0920/agents/anims/animwalk.py's."""
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)
from test_animglb import CLIPS, Blenderish, gltf_bytes, make_clip, own_model_file
from test_gltf_bones import NAMES, RECORD
from rusemod import anim, baf, gltf, modelin, rig, unitmodel
from ruse_studio import animblender

ORIGINALS = {name: baf.build(clip) for name, clip, _x in CLIPS}   # the mod's own clips, as it keeps them
SPINE = "bip01 spine"


def read_back(raw: bytes) -> tuple:
    """A file as Import model reads a model on bones of its own (rusemod.unitmodel._import_own_bones): (its rig, its
    record, its clips {name: bytes})."""
    doc, binary = modelin.glb_document(raw)
    r = rig.rig_of(doc, binary, "test.glb")
    record, _notes = unitmodel.own_skeleton(r)
    clips, _notes = unitmodel.own_clips(r, record)
    return r, record, clips


def brought_back(sending: bytes, start: bytes, went: dict, given: dict | None = None) -> bytes:
    """What Bring back the model makes of what Blender sent (ruse_studio.modelblender.model_blender_back): the bones in
    the order they went out, then the record and each clip that went out back in it."""
    raw = gltf.joints_like(sending, start)
    raw = rig.with_record(raw, RECORD)
    return rig.with_went_out(raw, went, given)


def taken_in(raw: bytes) -> tuple:
    """(the clips the import keeps of a file brought back: ruse_studio.animmodel_calls._went_out_kept's, the record,
    {name: the bones that came back changed})."""
    doc, _binary = modelin.glb_document(raw)
    r, record, made = read_back(raw)
    kept, changed = rig.kept_clips(made, rig.clips_out(doc), r)
    return kept, record, changed


def tracks_of(data: bytes) -> dict:
    c = baf.parse(data)
    sk = baf.skeleton(c.skeleton)
    return {sk["names"][sk["index"][u]]: t for u, t in enumerate(c.tracks)}


class Trip(unittest.TestCase):
    """The mod's clips out to Blender with the model, Blender's stand-in sending it back, and what comes in."""

    def setUp(self):
        self.model = own_model_file()            # (the mod's model file: write_glb's, its record in its skin's extras)
        self.start = modelin.own_animations_glb(self.model, ORIGINALS, blender=True)

    def test_untouched_every_animation_comes_back_byte_for_byte(self):
        """Blender changing nothing, its bones sent in another order and its animations in another (as Blender 4.5
        does): every clip is the mod's own again, byte for byte, on the mod's own skeleton record, in the order they
        went out (units.toml lists them so)."""
        sending = Blenderish(self.start).send(order=list(reversed(range(len(NAMES)))))
        doc, binary = modelin.glb_document(sending)
        doc["animations"].reverse()
        sending = gltf_bytes(doc, binary)
        _r, _rec, made = read_back(sending)
        self.assertTrue(all(made[n] != ORIGINALS[n] for n in ORIGINALS))   # (the import alone rewrote every one)
        kept, record, changed = taken_in(brought_back(sending, self.start, ORIGINALS))
        self.assertEqual(record, RECORD)
        self.assertEqual(list(kept), list(ORIGINALS))
        for name in ORIGINALS:
            self.assertEqual(kept[name], ORIGINALS[name], name)
            self.assertEqual(changed[name], [])

    def test_one_bone_turned_in_one_animation_only_it_differs(self):
        """The spine turned 20 degrees more at every frame of the run: the run comes back with its spine's track
        Blender's and every other track the one that went out, byte for byte, its length and skeleton part too; the
        stand comes back the mod's own."""
        name = CLIPS[0][0]
        sending = Blenderish(self.start).send(change=(name, SPINE, baf.axis_angle("x", 20.0)))
        kept, _record, changed = taken_in(brought_back(sending, self.start, ORIGINALS))
        self.assertEqual(kept[CLIPS[1][0]], ORIGINALS[CLIPS[1][0]])
        self.assertEqual(changed, {name: [SPINE], CLIPS[1][0]: []})
        mine, theirs = baf.parse(kept[name]), baf.parse(ORIGINALS[name])
        self.assertEqual((mine.duration, mine.frames, mine.skeleton), (theirs.duration, theirs.frames, theirs.skeleton))
        got, was = tracks_of(kept[name]), tracks_of(ORIGINALS[name])
        for bone in NAMES:
            (self.assertNotEqual if bone == SPINE else self.assertEqual)(got[bone], was[bone], bone)

    def test_with_the_clip_s_own_keys_alone_a_wide_turn_would_come_back_changed(self):
        """Why the model goes out with its turns keyed where Blender needs (rusemod.modelin._blender_animations):
        given only the clip's own keys, Blender's straight line between two keys 40 degrees apart misses the game's
        arc by more than a change's measure, so the untouched run came back changed (as 18 of the Generic Horse's 25
        did with the real Blender, 2026-11-13)."""
        sparse = modelin.own_animations_glb(self.model, ORIGINALS)
        sending = Blenderish(sparse).send()
        _kept, _record, changed = taken_in(brought_back(sending, sparse, ORIGINALS))
        self.assertTrue(changed[CLIPS[0][0]])
        sending = Blenderish(self.start).send()
        _kept, _record, changed = taken_in(brought_back(sending, self.start, ORIGINALS))
        self.assertEqual(changed[CLIPS[0][0]], [])

    def test_a_clip_off_the_game_s_frames_comes_back_as_the_mod_had_it(self):
        """A clip RUSE Decoy's speed left off the game's 30 frames a second goes out on them (animblender.
        on_game_frames, what Blender is given): back untouched, it is the mod's own clip, its own timing and all."""
        slow = baf.build(baf.with_speed(CLIPS[1][1], 70.0))
        mod = {CLIPS[0][0]: ORIGINALS[CLIPS[0][0]], CLIPS[1][0]: slow}
        given = {n: animblender.on_game_frames(c) for n, c in mod.items()}
        self.assertNotEqual(given[CLIPS[1][0]], slow)
        start = modelin.own_animations_glb(self.model, given, blender=True)
        sending = Blenderish(start).send()
        kept, _record, changed = taken_in(brought_back(sending, start, mod, given))
        self.assertEqual(kept, mod)
        self.assertEqual(changed, {CLIPS[0][0]: [], CLIPS[1][0]: []})

    def test_a_bone_moved_where_it_rests_is_taken_in_as_blender_sent_it(self):
        """A bone moved where it rests in Blender (its Edit Mode): the record isn't the one that went out any more, so
        it is worked out from the bones again and every clip carries it (as before), never the old one kept."""
        doc, binary = modelin.glb_document(Blenderish(self.start).send())
        joints = doc["skins"][0]["joints"]
        node = next(j for j in joints if doc["nodes"][j]["name"] == SPINE)
        doc["nodes"][node]["translation"] = [v + 0.3 for v in doc["nodes"][node]["translation"]]
        sending = gltf_bytes(doc, binary)
        self.assertEqual(rig.with_record(sending, RECORD), sending)    # (its bones aren't the record's: left as sent)
        kept, record, _changed = taken_in(brought_back(sending, self.start, ORIGINALS))
        self.assertNotEqual(record, RECORD)
        self.assertTrue(all(baf.parse(c).skeleton == record for c in kept.values()))


class TheFileCarries(unittest.TestCase):
    """What the Bring back puts back in the file Blender sent (rusemod.rig.with_went_out, with_record, clips_out)."""

    def test_the_animations_in_the_order_they_went_out_each_with_its_clip(self):
        start = modelin.own_animations_glb(own_model_file(), ORIGINALS, blender=True)
        doc, binary = modelin.glb_document(Blenderish(start).send())
        new = dict(doc["animations"][0], name="Wave")         # (one made in Blender)
        doc["animations"] = [new] + list(reversed(doc["animations"]))
        out = rig.with_went_out(gltf_bytes(doc, binary), ORIGINALS)
        got, _b = modelin.glb_document(out)
        self.assertEqual([a["name"] for a in got["animations"]], list(ORIGINALS) + ["Wave"])
        self.assertEqual(rig.clips_out(got), {n: (c, None) for n, c in ORIGINALS.items()})
        self.assertNotIn("extras", got["animations"][-1])
        # (none went out: the file as it is)
        self.assertEqual(rig.with_went_out(gltf_bytes(doc, binary), {"Other": ORIGINALS[CLIPS[0][0]]}),
                         gltf_bytes(doc, binary))

    def test_the_record_back_only_while_its_bones_still_match(self):
        start = modelin.own_animations_glb(own_model_file(), ORIGINALS, blender=True)
        sending = Blenderish(start).send()
        self.assertIsNone(rig._carried(modelin.glb_document(sending)[0]))        # (Blender keeps no extras)
        doc, _b = modelin.glb_document(rig.with_record(sending, RECORD))
        self.assertEqual(rig._carried(doc), RECORD)
        self.assertEqual(rig.with_record(b"not a glb", RECORD), b"not a glb")


class KeptClip(unittest.TestCase):
    def test_a_turn_near_half_a_turn_is_measured_on_the_file_s_pose_not_on_it_packed_again(self):
        """A bone turned near half a turn (w about 0.001, as the Generic Horse's clavicles are): its turn's w is
        packed from x, y and z, so a millionth more on each, as Blender's floats give it back, packs to a turn more
        than a change's measure away (rusemod.baf). Measured on the pose the file gives (Rig.poses'), it is the same
        turn: the clip that went out, byte for byte; measured on the clip packed again, it would have been a change."""
        went = make_clip(8.0)
        sk = baf.skeleton(went.skeleton)
        head = sk["names"].index("bip01 head")
        u = sk["index"].index(head)
        axis = (0.3, -0.5, 0.81)
        size = sum(a * a for a in axis) ** 0.5
        half = math.radians(179.9) / 2
        near = tuple(a / size * math.sin(half) for a in axis) + (math.cos(half),)
        tracks = list(went.tracks)
        tracks[u] = baf.Track(list(tracks[u].T), list(tracks[u].S), [(0,) + baf.pack_quat(*near)])
        went = baf.parse(baf.build(baf.Clip(went.duration, went.frames, tracks, went.skeleton)))
        packed = baf.unpack_quat(went.tracks[u].R[0][1:5])
        noisy = tuple(packed[i] + 1e-6 for i in range(3)) + (packed[3],)
        again = list(went.tracks)
        again[u] = baf.Track(list(went.tracks[u].T), list(went.tracks[u].S), [(0,) + baf.pack_quat(*noisy)])
        made = baf.build(baf.Clip(went.duration, went.frames, again, went.skeleton))
        a, b = rig.turn_matrix(packed), rig.turn_matrix(baf.unpack_quat(again[u].R[0][1:5]))
        self.assertGreater(max(abs(a[i][j] - b[i][j]) for i in range(3) for j in range(3)), 2 * rig.TOL_BACK_FRAME)
        n = went.frames
        poses = [None] * sk["bones"]
        for v, t in enumerate(went.tracks):
            got = [baf.sample(t, k / (n - 1)) for k in range(n)]
            turns = [noisy if v == u else g[1] for g in got]
            poses[sk["index"][v]] = ([g[0] for g in got], turns, [g[2] for g in got])
        went_bytes = baf.build(went)
        self.assertEqual(rig.kept_clip(made, went_bytes, poses=poses), (went_bytes, []))
        self.assertEqual(rig.kept_clip(made, went_bytes)[1], ["bip01 head"])

    def test_other_bones_or_timing_are_taken_in_as_made(self):
        made = ORIGINALS[CLIPS[0][0]]
        longer = baf.build(make_clip(40.0, frames=17))
        self.assertEqual(rig.kept_clip(longer, made), (longer, None))
        other = baf.skeleton_bytes(["root"], [-1], [rig.IDENTITY], [rig.IDENTITY], [rig.IDENTITY])
        lone = baf.build(baf.Clip(1.0, 31, [baf.Track([(0, 0.0, 0.0, 0.0)], [(0, 1.0, 1.0, 1.0)],
                                                      [(0,) + baf.pack_quat(0.0, 0.0, 0.0, 1.0)])], other))
        self.assertEqual(rig.kept_clip(lone, made), (lone, None))
        self.assertEqual(rig.kept_clip(made, made), (made, []))
        self.assertEqual(rig.kept_clip(b"junk", made), (b"junk", None))


class OwnAnimationsInto(unittest.TestCase):
    """rusemod.modelin.own_animations_glb: a model's animations put into its file anew."""

    def test_in_place_of_its_own_and_nothing_of_them_left(self):
        model = own_model_file()
        bare, _views = gltf.glb_views(model)
        one = modelin.own_animations_glb(model, {CLIPS[0][0]: ORIGINALS[CLIPS[0][0]]})
        two = modelin.own_animations_glb(one, ORIGINALS)
        doc, views = gltf.glb_views(two)
        self.assertEqual([a["name"] for a in doc["animations"]], list(ORIGINALS))
        again, _v = gltf.glb_views(modelin.own_animations_glb(model, ORIGINALS))
        self.assertEqual(len(doc["accessors"]), len(again["accessors"]))   # (the first one's data taken out)
        self.assertEqual(len(doc["bufferViews"]), len(again["bufferViews"]))
        self.assertEqual(two, modelin.own_animations_glb(model, ORIGINALS))
        _r, record, clips = read_back(two)
        self.assertEqual(record, RECORD)
        self.assertEqual(rig.kept_clips(clips, {n: (c, None) for n, c in ORIGINALS.items()})[0], ORIGINALS)
        none, _v = gltf.glb_views(modelin.own_animations_glb(two, {}))
        self.assertNotIn("animations", none)
        self.assertEqual((len(none["accessors"]), len(none["bufferViews"])),
                         (len(bare["accessors"]), len(bare["bufferViews"])))

    def test_a_clip_of_other_bones_is_refused_and_the_file_left_as_it_was(self):
        other = baf.skeleton_bytes(["root"], [-1], [rig.IDENTITY], [rig.IDENTITY], [rig.IDENTITY])
        lone = baf.build(baf.Clip(1.0, 31, [baf.Track([(0, 0.0, 0.0, 0.0)], [(0, 1.0, 1.0, 1.0)],
                                                      [(0,) + baf.pack_quat(0.0, 0.0, 0.0, 1.0)])], other))
        doc, views = gltf.glb_views(modelin.own_animations_glb(own_model_file(), ORIGINALS))
        before = gltf.pack_glb(doc, views)
        with self.assertRaises(modelin.ModelError):
            modelin.own_animations_into(doc, views, {**ORIGINALS, "lone": lone})
        self.assertEqual(gltf.pack_glb(doc, views), before)


# --- on the game: the Generic Horse through the one Blender button ---
from test_horse_squad import GAME, HEAVY, INDEX, RIFLE, finished, stand_in  # noqa: E402
from ruse_studio import horse_squad  # noqa: E402

ON_THE_GAME = GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file()
WHY_SKIPPED = ("RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of the copy "
               "that passed in the game aren't there")
TMP = os.environ.get("RUSE_TEST_TMP") or None
RUN, HORSE_SPINE = "hr_b_run", "horse spine1"


class Closed:
    """A stand-in for the Blender the Studio started, closed again."""

    def poll(self):
        return 0


@unittest.skipUnless(ON_THE_GAME, WHY_SKIPPED)
class OnTheGame(unittest.TestCase):
    """The Generic Horse added through the Studio's own Add (its builder standing in with the passed copy's two files),
    its riflemen's model taken through the one Blender button (everything ticked) and Blender's stand-in, then Bring my
    changes back: the mod's animation files (files/anim/own/<unit>/, units.toml) judged byte for byte. The untouched
    trip, the control, the Resize and the RUSE Decoy change going out failed on e9a092c3's code (every one of its 25
    files rewritten, units.toml in another order, the change undone); the second trip and the change never named lost
    failed on a87ddb70's (this piece's first commit)."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(prefix="anim-back-", dir=TMP))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.mod = Path(self.api.new_mod("Mine")["current"])
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            view = finished(self.api, self.api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.address = view["result"]["address"]
        self.tail = self.address.rsplit("/", 1)[-1]
        self.api._blender = lambda: Path("C:/b/blender.exe")

    def animation_files(self) -> dict:
        base = self.mod / "files" / "anim"
        return {p.relative_to(base).as_posix(): p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()}

    def trip(self, change=None, noise: bool = False) -> dict:
        """Open in Blender (the riflemen with their horse, everything ticked), Blender's stand-in sending it back with
        its bones and its animations in other orders, as Blender 4.5 does (`change`: test_animglb's Blenderish.send's;
        `noise`: one bone's rest moved by 0.6 of what rusemod.rig counts as float noise, as Blender's floats move it),
        Bring my changes back."""
        handed = {}
        with mock.patch("rusemod.blender.open_model_to_change",
                        lambda b, model, send, words: handed.update(model=Path(model), send=Path(send)) or Closed()):
            self.api.blender_open(self.address, {"model": True, "kind": "", "bones": True, "paint": True}, "us")
        blender = Blenderish(handed["model"].read_bytes())
        joints = len(blender.doc["skins"][0]["joints"])     # (Blender 4.5 writes the bones in an order of its own)
        doc, binary = modelin.glb_document(blender.send(change=change, order=list(reversed(range(joints)))))
        doc["animations"].sort(key=lambda a: a["name"])        # (and the animations so)
        if noise:   # (a bone with no bone under it, the same one each trip: only its own rest moves)
            bones = doc["skins"][0]["joints"]
            leaf = min((j for j in bones if not set(doc["nodes"][j].get("children", [])) & set(bones)),
                       key=lambda j: doc["nodes"][j]["name"])
            doc["nodes"][leaf]["translation"][0] += 0.6 * rig.NEAR_MOVE * gltf.SCALE
        handed["send"].write_bytes(gltf_bytes(doc, binary))
        return self.api.blender_back(self.address, "us")

    def test_untouched_every_animation_file_comes_back_byte_for_byte(self):
        before = self.animation_files()
        self.assertEqual(sum(1 for k in before if k.endswith(".baf")), 25)
        back = self.trip()
        self.assertEqual(back["door"], "model")
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        after = self.animation_files()
        self.assertEqual(sorted(after), sorted(before))
        self.assertEqual([k for k in before if after[k] != before[k]], [])

    def test_one_bone_moved_in_one_animation_only_it_differs(self):
        """The control: a change made in Blender comes in, only where it was made: the run's horse spine1 turned 10
        degrees more at every frame, its other 61 tracks, its length and its skeleton part as they were, the other 24
        files and units.toml byte for byte."""
        before = self.animation_files()
        self.trip(change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        after = self.animation_files()
        run = f"own/{self.tail}/{RUN}.baf"
        self.assertEqual([k for k in before if after[k] != before[k]], [run])
        mine, theirs = baf.parse(after[run]), baf.parse(before[run])
        self.assertEqual((mine.duration, mine.frames, mine.skeleton), (theirs.duration, theirs.frames, theirs.skeleton))
        got, was = tracks_of(after[run]), tracks_of(before[run])
        self.assertEqual([b for b in was if got[b] != was[b]], [HORSE_SPINE])

    def test_a_ruse_decoy_change_then_one_made_in_blender_is_never_named_lost(self):
        """The run changed in RUSE Decoy (its spine2 turned), then in Blender (its spine1 turned on top of that, as
        Blender showed it): the run comes back with both, every track but spine1's as it was (spine2's turn too), and
        the Bring back never says the RUSE Decoy change wasn't kept (a87ddb70 said so: not_kept named the run, real
        Blender 4.5.14)."""
        own = anim.own_animations(self.mod, self.tail)["animations"]
        folder = self.mod / anim.OWN / self.tail
        mine = {n: (folder / f).read_bytes() for n, f in own.items()}
        mine[RUN] = baf.build(baf.with_bone(baf.parse(mine[RUN]), "horse spine2", turn=("x", 25.0)))
        anim.set_animations(self.mod, self.tail, mine)
        before = self.animation_files()
        back = self.trip(change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        after = self.animation_files()
        run = f"own/{self.tail}/{RUN}.baf"
        self.assertEqual([k for k in before if after[k] != before[k]], [run])
        got, was = tracks_of(after[run]), tracks_of(before[run])
        self.assertEqual([b for b in was if got[b] != was[b]], [HORSE_SPINE])

    def test_opened_again_blender_s_float_noise_on_its_bones_doesnt_add_up(self):
        """Opened again, Blender starts from its last sending: a bone's rest moved each trip by a little float noise
        (here 0.6 of what rusemod.rig counts as noise) went out again so moved, and the second trip's came back past
        it (1.2), its clips on a skeleton worked out anew: all 25 files rewritten (real Blender 4.5.14 so, the Generic
        Horse's upper arms, 2026-11-13). The sending goes out again on the mod's own bones while they're its within
        that noise (ModelBlenderCalls._again), so the second trip keeps them too."""
        before = self.animation_files()
        self.trip(noise=True)
        self.assertEqual([k for k in before if self.animation_files()[k] != before[k]], [])
        self.trip(noise=True)
        after = self.animation_files()
        self.assertEqual([k for k in before if after[k] != before[k]], [])

    def test_a_resize_after_the_trip_keeps_them(self):
        """Resize fits the model again from the file the Bring back made it from: the animations stay as they came
        back (the same file gives the same clips)."""
        before = self.animation_files()
        self.trip()
        self.api.model_resize(self.address, 1.0)
        after = self.animation_files()
        self.assertEqual([k for k in before if after.get(k) != before[k]], [])

    def test_an_animation_changed_in_ruse_decoy_goes_out_and_comes_back_as_it_is(self):
        """The run changed in the mod since the model came in (RUSE Decoy's way: its file in the mod, never the
        model's): it goes out to Blender as the mod plays it, and back untouched it is still the mod's change, byte for
        byte (on e9a092c3 the model's file's old run went out, and the change was undone: not_kept)."""
        own = anim.own_animations(self.mod, self.tail)["animations"]
        folder = self.mod / anim.OWN / self.tail
        mine = {n: (folder / f).read_bytes() for n, f in own.items()}
        mine[RUN] = baf.build(baf.with_bone(baf.parse(mine[RUN]), HORSE_SPINE, turn=("x", 25.0)))
        anim.set_animations(self.mod, self.tail, mine)
        before = self.animation_files()
        back = self.trip()
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        after = self.animation_files()
        self.assertEqual([k for k in before if after[k] != before[k]], [])


class Open:
    """A stand-in for the Blender the Studio started: open until it is closed."""

    def __init__(self):
        self.running = True

    def poll(self):
        return None if self.running else 0


STAND, SPINE2 = "hr_b_stand", "horse spine2"
TICKS = {"model": True, "kind": "", "bones": True, "paint": True}


@unittest.skipUnless(ON_THE_GAME, WHY_SKIPPED)
class OpenedAgain(unittest.TestCase):
    """The review of 278fe767 (scratch/release-0920/agents/reports-v2/review-anims.json) and what it found of the same
    kind: nothing of the modder's lost on the way through the model's own Blender, by how Blender is opened again, by
    a Studio change made while it is open, by a sending set against animations it wasn't made from, by Its bones
    unticked, or by one clip file that can't be read. The Generic Horse through the one Blender button with Blender's
    stand-in, as OnTheGame; each failed on 278fe767's code (the controls pass there too)."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(prefix="anim-again-", dir=TMP))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.mod = Path(self.api.new_mod("Mine")["current"])
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            view = finished(self.api, self.api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.address = view["result"]["address"]
        self.tail = self.address.rsplit("/", 1)[-1]
        self.api._blender = lambda: Path("C:/b/blender.exe")
        self.run_file, self.stand_file = f"own/{self.tail}/{RUN}.baf", f"own/{self.tail}/{STAND}.baf"

    def files(self) -> dict:
        base = self.mod / "files" / "anim"
        return {p.relative_to(base).as_posix(): p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()}

    def open(self, proc=None, ticks=None, direct: bool = False) -> dict:
        """The one Blender button's Open in Blender (`ticks`, everything ticked unless given), or (`direct`) the
        Model row's own Change it in Blender (model_blender): what Blender was handed, and the session its words carry."""
        handed = {}

        def started(b, model, send, words):
            handed.update(model=Path(model), send=Path(send),
                          session=json.loads(Path(words).read_text(encoding="utf-8")).get("session"))
            return proc or Closed()
        with mock.patch("rusemod.blender.open_model_to_change", started):
            if direct:
                self.api.model_blender(self.address, "us")
            else:
                self.api.blender_open(self.address, ticks or TICKS, "us")
        return handed

    @staticmethod
    def send(scene: bytes, to: Path, change=None, session: str | None = None, bone_moved: float = 0.0) -> bytes:
        """Blender's stand-in sending the scene `scene` (a file as Blender has it) to `to`, its bones and animations in
        orders of its own, as Blender 4.5 does; `change`: Blenderish.send's; `session`: what Send writes beside it
        (rusemod.blender_model.say_about), the opening's session; `bone_moved`: the horse's spine1 moved where it rests
        by this much (its Edit Mode)."""
        blender = Blenderish(scene)
        joints = len(blender.doc["skins"][0]["joints"])
        doc, binary = modelin.glb_document(blender.send(change=change, order=list(reversed(range(joints)))))
        doc["animations"].sort(key=lambda a: a["name"])
        if bone_moved:
            node = next(j for j in doc["skins"][0]["joints"] if doc["nodes"][j]["name"] == HORSE_SPINE)
            doc["nodes"][node]["translation"][1] += bone_moved
        data = gltf_bytes(doc, binary)
        to.write_bytes(data)
        if session is not None:
            import hashlib
            to.with_name(to.name + ".json").write_text(json.dumps(
                {"glb": hashlib.sha256(data).hexdigest(), "fps": 30.0, "nla": [], "stretch": None,
                 "session": session}), encoding="utf-8")
        return data

    def back(self, direct: bool = False) -> dict:
        """Bring my changes back (`direct`: the Model row's own Bring back the model), an open Blender's stand-in having
        sent already."""
        with mock.patch("rusemod.blender.ask_to_send", lambda send, wait: send):
            if direct:
                return self.api.model_blender_back(self.address, 1.0)
            return self.api.blender_back(self.address, "us")

    def decoy(self, name: str, bone: str, degrees: float) -> bytes:
        """`name` changed in RUSE Decoy's store (files/anim/own/<unit>/, its Only this unit): `bone` turned."""
        own = anim.own_animations(self.mod, self.tail)["animations"]
        folder = self.mod / anim.OWN / self.tail
        mine = {n: (folder / f).read_bytes() for n, f in own.items()}
        mine[name] = baf.build(baf.with_bone(baf.parse(mine[name]), bone, turn=("x", degrees)))
        anim.set_animations(self.mod, self.tail, mine)
        return mine[name]

    def turned(self, a: bytes, b: bytes, bone: str) -> float:
        """The most, in degrees, `bone`'s turn in clip `a` is off its turn in clip `b`, over their frames."""
        ta, tb = tracks_of(a)[bone], tracks_of(b)[bone]
        n = max(baf.parse(a).frames, 2)
        worst = 0.0
        for k in range(n):
            qa, qb = baf.sample(ta, k / (n - 1))[1], baf.sample(tb, k / (n - 1))[1]
            worst = max(worst, math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(qa, qb)))))))
        return worst

    def opened_clip(self, file: Path, name: str) -> bytes:
        """An animation as the file Blender opened has it, the way an import takes it in."""
        _r, _record, clips = read_back(file.read_bytes())
        return clips[name]

    # --- the review's first finding: Blender opened again on a sending never brought back ---
    def test_a_sending_never_brought_back_is_where_blender_opens_again(self):
        """The modder brings the run's change back while Blender is open, goes on there (the stand's spine1 turned
        too), clicks Send and closes Blender: that sending was never brought back. Opened again, Blender opens it with
        the stand's change (278fe767 put the mod's animations in its place, the stand as before the trip, without a
        word), and sent back untouched the stand's change comes in, the run as its first Bring back left it, every other
        file byte for byte."""
        before = self.files()
        proc = Open()
        handed = self.open(proc)
        first = self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        mid = self.files()
        self.assertEqual([k for k in before if mid[k] != before[k]], [self.run_file])
        self.send(first, handed["send"], change=(STAND, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        proc.running = False
        again = self.open()
        self.assertGreater(self.turned(self.opened_clip(again["model"], STAND), before[self.stand_file], HORSE_SPINE),
                           9.0)
        self.send(again["model"].read_bytes(), again["send"])
        back = self.back()
        after = self.files()
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        self.assertGreater(self.turned(after[self.stand_file], before[self.stand_file], HORSE_SPINE), 9.0)
        self.assertEqual(after[self.run_file], mid[self.run_file])
        self.assertEqual([k for k in before if after[k] != before[k]], [self.run_file, self.stand_file])
        got, was = tracks_of(after[self.stand_file]), tracks_of(before[self.stand_file])
        self.assertEqual([b for b in was if got[b] != was[b]], [HORSE_SPINE])

    def test_opened_twice_without_a_bring_back_keeps_the_first_sending_s_change(self):
        """The Model row's own Change it in Blender (drawn when a squad's card can't be read) clicked again before any
        Bring back: Blender opens what it sent, the run's change in it, and that change comes in with the next Bring
        back (278fe767 opened the mod's run in its place: the change was gone)."""
        before = self.files()
        handed = self.open(direct=True)
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        again = self.open(direct=True)
        self.send(again["model"].read_bytes(), again["send"])
        self.back(direct=True)
        after = self.files()
        self.assertEqual([k for k in before if after[k] != before[k]], [self.run_file])
        self.assertGreater(self.turned(after[self.run_file], before[self.run_file], HORSE_SPINE), 9.0)

    def test_a_change_undone_in_blender_after_its_bring_back_stays_undone_when_opened_again(self):
        """The run's change brought back, then undone in Blender and sent (never brought back), Blender closed: opened
        again, Blender opens the run as it was undone there, and sent back untouched the run is as before the trip, byte
        for byte (278fe767 opened the mod's run, with the change, in its place: the undo was gone)."""
        before = self.files()
        proc = Open()
        handed = self.open(proc)
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        self.send(handed["model"].read_bytes(), handed["send"])     # (undone there: the scene as it opened)
        proc.running = False
        again = self.open()
        self.assertLess(self.turned(self.opened_clip(again["model"], RUN), before[self.run_file], HORSE_SPINE), 0.1)
        self.send(again["model"].read_bytes(), again["send"])
        self.back()
        after = self.files()
        self.assertEqual([k for k in before if after[k] != before[k]], [])

    def test_control_a_sending_brought_back_opens_again_with_the_mod_s_animations_as_they_are_now(self):
        """The control: a sending brought back is in the mod, so Blender opened again starts from it with the mod's
        animations as they are now, a RUSE Decoy change made since too (the walk's spine2 turned); sent back
        untouched, every file stays as it was after the first trip and that change."""
        handed = self.open()
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        walk = self.decoy("hr_b_walk", SPINE2, 25.0)
        mid = self.files()
        again = self.open()
        self.assertLess(self.turned(self.opened_clip(again["model"], "hr_b_walk"), walk, SPINE2), 0.1)
        self.send(again["model"].read_bytes(), again["send"])
        back = self.back()
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        after = self.files()
        self.assertEqual([k for k in mid if after[k] != mid[k]], [])

    # --- its second finding: a RUSE Decoy change made while the model's Blender is open ---
    def test_a_ruse_decoy_change_made_while_blender_is_open_stays_when_it_comes_back_untouched(self):
        """Open in Blender; the run changed in RUSE Decoy while that Blender is open (its spine2 turned 25 degrees);
        sent back with nothing changed there: the run stays as RUSE Decoy made it, byte for byte, nothing named lost,
        and the answer names it as kept the Studio's ("differs", as RUSE Decoy's own Bring back says it); a Resize after
        keeps it too (278fe767 put the run that went out back over it and named it lost)."""
        handed = self.open(Open())
        self.decoy(RUN, SPINE2, 25.0)
        before = self.files()
        self.send(handed["model"].read_bytes(), handed["send"])
        back = self.back()
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        self.assertEqual(back.get("differs"), [RUN])
        self.assertEqual([k for k in before if self.files()[k] != before[k]], [])
        self.api.model_resize(self.address, 1.0)
        after = self.files()
        self.assertEqual([k for k in before if after.get(k) != before[k]], [])

    def test_a_ruse_decoy_change_made_after_a_bring_back_stays_when_blender_sends_that_animation_again(self):
        """The run's change brought back while Blender is open; then the run changed in RUSE Decoy (its spine2 turned on
        top of it); then Blender sends again, the stand changed there and the run as it brought it back: the run stays
        as RUSE Decoy made it, named as kept the Studio's, and the stand's change comes in; a Resize after keeps them
        (278fe767 put the run as Blender had it over the RUSE Decoy change)."""
        before = self.files()
        handed = self.open(Open())
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        decoyed = self.decoy(RUN, SPINE2, 25.0)
        blender = Blenderish(handed["model"].read_bytes())      # (the same scene: the run as it was sent, the stand too)
        joints = len(blender.doc["skins"][0]["joints"])
        doc, binary = modelin.glb_document(blender.send(change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)),
                                                        order=list(reversed(range(joints)))))
        stand = Blenderish(gltf_bytes(doc, binary)).send(change=(STAND, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        handed["send"].write_bytes(stand)
        back = self.back()
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        self.assertEqual(back.get("differs"), [RUN])
        after = self.files()
        self.assertEqual(after[self.run_file], decoyed)
        self.assertGreater(self.turned(after[self.stand_file], before[self.stand_file], HORSE_SPINE), 9.0)
        self.assertEqual([k for k in before if after[k] != before[k]], [self.run_file, self.stand_file])
        self.api.model_resize(self.address, 1.0)      # (fitted again from the same file: the same clips)
        self.assertEqual([k for k in after if self.files()[k] != after[k]], [])

    def test_a_ruse_decoy_change_back_to_what_went_out_stays_when_blender_sends_the_run_again(self):
        """The run's change brought back while Blender is open; then the run put back in RUSE Decoy as it was, the clip
        that went out, byte for byte; then Blender sends the run again as it brought it back: the run stays as RUSE Decoy
        put it back, said as kept the Studio's (being the clip that went out, it was taken for Blender's own and
        Blender's change put over it without a word)."""
        before = self.files()
        handed = self.open(Open())
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        own = anim.own_animations(self.mod, self.tail)["animations"]
        folder = self.mod / anim.OWN / self.tail
        mine = {n: (folder / f).read_bytes() for n, f in own.items()}
        mine[RUN] = before[self.run_file]               # (RUSE Decoy: the run as it was)
        anim.set_animations(self.mod, self.tail, mine)
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        back = self.back()
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        self.assertEqual(back.get("differs"), [RUN])
        self.assertEqual(self.files()[self.run_file], before[self.run_file])

    def test_a_ruse_decoy_change_kept_then_changed_in_blender_is_named(self):
        """The run changed in RUSE Decoy while Blender is open and kept by a Bring back that left it untouched; then the
        run changed in that Blender (its scene has the run as it went out) and brought back: Blender's run comes in and
        the RUSE Decoy change is named, as when both change it before one Bring back (kept once, it was put back the
        next time without a word: its fingerprint said the mod's run was the file's)."""
        handed = self.open(Open())
        decoyed = self.decoy(RUN, SPINE2, 25.0)
        self.send(handed["model"].read_bytes(), handed["send"])
        self.assertEqual(self.back().get("differs"), [RUN])
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        back = self.back()
        self.assertEqual(((back.get("model") or {}).get("not_kept") or {}).get("animations"), [RUN])
        self.assertGreater(self.turned(self.files()[self.run_file], decoyed, SPINE2), 20.0)

    def test_control_a_change_made_in_both_is_blender_s_and_the_ruse_decoy_change_named(self):
        """The control: the run changed in RUSE Decoy while Blender is open and changed in Blender too (its spine1):
        Blender's comes in and the RUSE Decoy change is named, as before (Changes to these animations weren't kept)."""
        handed = self.open(Open())
        decoyed = self.decoy(RUN, SPINE2, 25.0)
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        back = self.back()
        self.assertEqual(((back.get("model") or {}).get("not_kept") or {}).get("animations"), [RUN])
        self.assertFalse(back.get("differs"))
        after = self.files()
        self.assertGreater(self.turned(after[self.run_file], decoyed, SPINE2), 20.0)

    def test_control_a_change_brought_back_then_undone_in_the_same_blender_is_undone(self):
        """The control: the run's change brought back while Blender is open, then undone there and sent: the Bring back
        puts the run back as it went out (Blender's undo), never kept as the Studio's."""
        before = self.files()
        handed = self.open(Open())
        self.send(handed["model"].read_bytes(), handed["send"], change=(RUN, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        self.send(handed["model"].read_bytes(), handed["send"])
        back = self.back()
        self.assertFalse(back.get("differs"))
        self.assertIsNone((back.get("model") or {}).get("not_kept"))
        after = self.files()
        self.assertEqual([k for k in before if after[k] != before[k]], [])

    # --- its third suspicion: a sending set against animations it wasn't made from ---
    def test_a_brought_back_sending_is_never_set_against_what_went_out_after_it(self):
        """Brought back, Blender closed, the run changed in RUSE Decoy, Blender opened again and never sending (it
        didn't start, or didn't answer): Bring back says nothing came back and the run stays as RUSE Decoy made it
        (278fe767 set the old sending against the new run: RUSE Decoy's spine2 put back without a word)."""
        from ruse_studio.api import StudioError
        handed = self.open()
        self.send(handed["model"].read_bytes(), handed["send"], change=(STAND, HORSE_SPINE, baf.axis_angle("x", 10.0)))
        self.back()
        self.decoy(RUN, SPINE2, 25.0)
        before = self.files()
        again = self.open()
        try:
            self.back()
            refused = None
        except StudioError as exc:
            refused = str(exc)
        self.assertEqual([k for k in before if self.files()[k] != before[k]], [])
        self.assertIn("Nothing has come back from Blender yet", refused or "")
        self.assertFalse(again["send"].is_file())     # (brought back: in the mod, taken out of the Blender folder)

    def test_what_a_blender_opened_before_the_last_one_sends_is_refused(self):
        """A Blender left open when the Studio started again (the one button then offers Open in Blender): opened again,
        then the old Blender sends. Its sending is refused, nothing written (278fe767 set it against what the new
        opening sent: the run's RUSE Decoy change made between them put back without a word); the Blender opened last
        sends and is taken in."""
        from ruse_studio.api import StudioError
        handed = self.open(Open())
        old = self.send(handed["model"].read_bytes(), handed["send"], change=(STAND, HORSE_SPINE, baf.axis_angle("x", 10.0)),
                        session=handed["session"])
        self.back()
        self.decoy(RUN, SPINE2, 25.0)
        self.api._blenders.clear()        # (the Studio started again: it knows of no Blender)
        again = self.open()
        before = self.files()
        self.send(old, handed["send"], session=handed["session"])
        try:
            self.back()
            refused = None
        except StudioError as exc:
            refused = str(exc)
        self.assertEqual([k for k in before if self.files()[k] != before[k]], [])
        self.assertIn("opened before the one opened last", refused or "")
        self.assertNotEqual(again["session"], handed["session"])
        self.send(again["model"].read_bytes(), again["send"], session=again["session"])
        self.back()
        self.assertEqual([k for k in before if self.files()[k] != before[k]], [])

    # --- its second suspicion: Its bones unticked set against the first opening's file ---
    def test_bones_unticked_after_a_bone_moved_and_brought_back_keeps_it_and_every_animation(self):
        """The horse's spine1 moved where it rests in Blender and brought back (Its bones ticked); opened again with Its
        bones unticked and sent back untouched: the bones stay as the mod has them, the moved one too, and every
        animation file byte for byte (278fe767 put back the first opening's bones: the spine moved back and all 25
        files made again on them)."""
        handed = self.open()
        self.send(handed["model"].read_bytes(), handed["send"], bone_moved=0.05)
        self.back()
        mid = self.files()
        record = baf.parse(mid[self.run_file]).skeleton
        again = self.open(ticks={**TICKS, "bones": False})
        self.send(again["model"].read_bytes(), again["send"])
        back = self.back()
        self.assertIn((back.get("kept") or {}).get("bones"), ("kept", "same"))
        after = self.files()
        self.assertEqual([k for k in mid if after[k] != mid[k]], [])
        self.assertEqual(baf.parse(after[self.run_file]).skeleton, record)

    def test_control_bones_unticked_on_the_first_trip_keeps_everything(self):
        """The control: Its bones unticked on the first trip, nothing changed: every file byte for byte."""
        before = self.files()
        handed = self.open(ticks={**TICKS, "bones": False})
        self.send(handed["model"].read_bytes(), handed["send"])
        self.back()
        after = self.files()
        self.assertEqual([k for k in before if after[k] != before[k]], [])

    # --- its fifth suspicion: one clip file that can't be read ---
    def test_one_clip_file_that_cant_be_read_leaves_the_others_byte_for_byte(self):
        """One of the unit's clip files damaged (not a clip any more): an untouched trip takes the model's own file's
        animation in its place and names it, as before, and every other file comes back byte for byte (278fe767 sent
        every animation as the model's file carries it then, and all 25 came back rewritten)."""
        damaged = f"own/{self.tail}/hr_t_stand.baf"
        (self.mod / "files" / "anim" / damaged).write_bytes(b"not a clip")
        before = self.files()
        back = self.trip_untouched()
        after = self.files()
        self.assertEqual([k for k in before if after[k] != before[k]], [damaged])
        self.assertIn("hr_t_stand", ((back.get("model") or {}).get("not_kept") or {}).get("animations") or [])
        baf.check(baf.parse(after[damaged]))

    def trip_untouched(self) -> dict:
        handed = self.open()
        self.send(handed["model"].read_bytes(), handed["send"])
        return self.back()
