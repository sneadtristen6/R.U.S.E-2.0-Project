"""A unit's animations out to Blender and back (item 5 of the owner's list, part 4: "fully editable in the studio"):
rusemod.gltf.model_glb's `clips` and rusemod.animglb.own_glb lay a model's bones out for Blender (turned, legs hung,
sized bones as plain turns) with its clips as the file's animations; rusemod.rig.turn_back and clips_back take them
back to the game's frames. On a made-up model, skeleton and clips (no game files, no Blender): the bones test_gltf_bones
lays out (a sized bone, a mirrored one, a Biped leg and a wheel with no parent bone, a bone no point leans on), clips
moving every one of them; Blender's part played by a stand-in that does what Blender 4.5's glTF importer and exporter
do with such a file (each key on its frame, a straight line through a turn's four numbers between keys, every frame
sampled on the way out, no extras kept, the bones in an order of its own). The real Blender's round trips are
scratch/animmodels/agent5-4/roundtrip.py's (the game's US rifleman and the 2026-11-09 Horse Squad)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import base64
import math
import re
import struct
import tempfile
import unittest
from pathlib import Path

from rusemod import animglb, baf, blender, gltf, modelin, rig, unitmodel
from rusemod.gltf import FLOAT, USHORT, _Glb
from rusemod.modelin import OWN_SKELETON
from test_gltf_bones import NAME, NAMES, PARENTS, RECORD, FakeLibrary, in_gltf, read_glb

SK = baf.skeleton(RECORD)
NB = len(NAMES)
FRAMES = 13


# --- clips on the made-up skeleton: every bone moved, turned or sized (each key on the 30-a-second frame grid) ---
def rest_trs(b: int) -> tuple:
    return rig.decompose(SK["local"][b])[:3]


def make_clip(spin: float, frames: int = FRAMES) -> baf.Clip:
    """Each bone's track from its rest pose: bip01 moves at four keys, the thigh in two (a straight line over the whole
    clip), every bone but fx_point turns at four keys (up to `spin` degrees: wide enough that Blender's straight line
    through a turn's numbers would part from the game's arc), the wing grows in two keys and the flap in three; the
    mirrored bone keeps its mirror (a size below 0)."""
    tracks = []
    last = frames - 1
    for b in range(NB):
        m0, q0, s0 = rest_trs(b)
        if b == 0:
            T = [(baf.frame_time(k, frames),) + tuple(m0[i] + d for i, d in enumerate((2.0 * k, -1.5 * k, 0.5 * k)))
                 for k in (0, 4, 9, last)]
        elif NAMES[b] == "bip01 l thigh":
            T = [(0,) + tuple(m0), (baf.LAST_TIME, m0[0] + 3.0, m0[1], m0[2] - 2.0)]
        else:
            T = [(0,) + tuple(m0)]
        if NAMES[b] == "fx_point":
            R = [(0,) + baf.pack_quat(*q0)]
        else:
            axis = "xyz"[b % 3]
            turns = [baf.qmul(q0, baf.axis_angle(axis, spin * a)) for a in (0.0, 0.6, -0.4, 1.0)]
            R = [(baf.frame_time(k, frames),) + baf.pack_quat(*q) for k, q in zip((0, 3, 7, last), baf.same_side(turns))]
        if NAMES[b] == "wing":
            S = [(0,) + tuple(s0), (baf.LAST_TIME,) + tuple(v * 1.25 for v in s0)]
        elif NAMES[b] == "flap":
            S = [(0,) + tuple(s0), (baf.frame_time(6, frames), s0[0] * 0.8, s0[1], s0[2] * 1.1), (baf.LAST_TIME,) + tuple(s0)]
        else:
            S = [(0,) + tuple(s0)]
        tracks.append(baf.Track(T, S, R))
    return baf.parse(baf.build(baf.Clip(last / baf.FPS, frames, tracks, RECORD)))   # (as the game's file holds it)


CLIPS = [("Run (made_run)", make_clip(40.0), {"rusemod_clip": "made_runlod0.baf", "rusemod_actions": ["b_course"]}),
         ("Stand (made_stand)", make_clip(8.0, frames=31), {"rusemod_clip": "made_standlod0.baf",
                                                           "rusemod_actions": ["b_stand", "t_stand"]})]
ORIGINALS = {name: baf.build(clip) for name, clip, _x in CLIPS}


# --- glTF in the test's own hands ---
def accessor(doc, binary, i):
    return modelin.glb_accessor(doc, binary, i)


def rows4(trs) -> list:
    """(translation, rotation, scale) as 4 x 4 rows."""
    t, q, s = trs
    x, y, z, w = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def mul4(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def nlerp(a, b, s):
    q = [x + (y - x) * s for x, y in zip(a, b)]
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return [c / n for c in q]


class Blenderish:
    """What Blender 4.5 does with such a file, as far as the numbers go: each animation's channels evaluated at whole
    frames of 30 a second, a straight line between keys (a turn's four numbers each on a line, then made length one);
    sent back (send()) with every frame sampled for every bone, no extras, the skin's joints in an order of its own."""

    def __init__(self, raw: bytes):
        self.doc, self.bin = read_glb(raw)
        self.parent = {c: i for i, n in enumerate(self.doc["nodes"]) for c in n.get("children", [])}

    def channels(self, anim) -> dict:
        out = {}
        for c in anim["channels"]:
            s = anim["samplers"][c["sampler"]]
            out.setdefault(c["target"]["node"], {})[c["target"]["path"]] = (
                accessor(self.doc, self.bin, s["input"]), accessor(self.doc, self.bin, s["output"]))
        return out

    @staticmethod
    def value(times, values, t, path):
        if t <= times[0] + 1e-7:
            return list(values[0])
        if t >= times[-1] - 1e-7:
            return list(values[-1])
        i = max(k for k in range(len(times)) if times[k] <= t + 1e-7)
        s = (t - times[i]) / (times[i + 1] - times[i])
        a, b = values[i], values[i + 1]
        return nlerp(a, b, s) if path == "rotation" else [x + (y - x) * s for x, y in zip(a, b)]

    def trs(self, chans, node, frame) -> tuple:
        n = self.doc["nodes"][node]
        rest = (n.get("translation", [0, 0, 0]), n.get("rotation", [0, 0, 0, 1]), n.get("scale", [1, 1, 1]))
        got = chans.get(node, {})
        return tuple(self.value(*got[p], frame / baf.FPS, p) if p in got else list(v)
                     for p, v in zip(("translation", "rotation", "scale"), rest))

    def world(self, chans, node, frame) -> list:
        m = rows4(self.trs(chans, node, frame))
        return mul4(self.world(chans, self.parent[node], frame), m) if node in self.parent else m

    def frames(self, anim) -> int:
        return round(max(max(t) for got in self.channels(anim).values() for t, _v in got.values()) * baf.FPS) + 1

    def send(self, order=None, change=None) -> bytes:
        """The file as Blender's Send writes it: every animation every bone's channels at each frame, no extras; the
        skin's joints in `order` (positions in the old list) with the points' bone numbers to match. `change`:
        (animation name, bone name, a turn (x, y, z, w) put after the bone's own at every frame)."""
        doc, binary = read_glb(gltf_bytes(self.doc, self.bin))
        g = _Glb()
        g.doc, g.bin = doc, bytearray(binary)
        skin = doc["skins"][0]
        joints = list(skin["joints"])
        anims = []
        for anim in self.doc["animations"]:
            chans = self.channels(anim)
            n = self.frames(anim)
            times = [k / baf.FPS for k in range(n)]
            samplers, channels = [], []
            tin = g.accessor(times, "SCALAR", FLOAT, target=None)
            g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [0.0], [times[-1]]
            for node in joints:
                vals = [self.trs(chans, node, k) for k in range(n)]
                if change and change[0] == anim["name"] and doc["nodes"][node]["name"] == change[1]:
                    vals = [(t, list(baf.qmul(q, change[2])), s) for t, q, s in vals]
                for i, path in enumerate(("translation", "rotation", "scale")):
                    out = g.accessor([tuple(v[i]) for v in vals], "VEC4" if path == "rotation" else "VEC3", FLOAT,
                                     target=None)
                    samplers.append({"input": tin, "output": out, "interpolation": "LINEAR"})
                    channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
            anims.append({"name": anim["name"], "samplers": samplers, "channels": channels})
        doc["animations"] = anims
        if order is not None:
            ibm = accessor(doc, binary, skin["inverseBindMatrices"])
            skin["joints"] = [joints[k] for k in order]
            flat = [v for k in order for v in ibm[k]]
            g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(flat)}f", *flat)),
                                       "componentType": FLOAT, "count": len(order), "type": "MAT4"})
            skin["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
            new_of = {k: i for i, k in enumerate(order)}
            for mesh in doc["meshes"]:
                for prim in mesh["primitives"]:
                    if "JOINTS_0" in prim["attributes"]:
                        js = [tuple(new_of[int(x)] for x in v) for v in accessor(doc, binary, prim["attributes"]["JOINTS_0"])]
                        prim["attributes"]["JOINTS_0"] = g.accessor(js, "VEC4", USHORT)
        for part in [doc.get("asset", {})] + doc.get("skins", []) + doc["animations"] + doc.get("materials", []):
            part.pop("extras", None)
        for n in doc["nodes"]:
            n.pop("extras", None)
        return g.to_bytes()


def gltf_bytes(doc, binary) -> bytes:
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    return g.to_bytes()


def game_world(clip: baf.Clip, frame: int) -> list:
    """Each bone's pose in the model (12 numbers) at a frame, as the game plays the clip."""
    csk = baf.skeleton(clip.skeleton)
    track = {csk["index"][u]: t for u, t in enumerate(clip.tracks)}
    frac = frame / (clip.frames - 1)
    w = []
    for b in range(NB):
        m = rig.compose(*baf.sample(track[b], frac))
        w.append(m if PARENTS[b] < 0 else rig.mul(w[PARENTS[b]], m))
    return w


def rows_of(m16) -> list:
    return [[m16[j * 4 + i] for j in range(4)] for i in range(4)]


def own_model_file(record: bytes = RECORD) -> bytes:
    """A model on bones of its own as the mod keeps it (rusemod.modelin.write_glb's, its record in its skin's extras):
    one draw whose points lean on every bone but fx_point."""
    names = baf.skeleton(record)["names"]
    pts, skin, tris = [], [], []
    for k, name in enumerate(n for n in names if n != "fx_point"):
        pts += [(float(k), 0.0, 100.0), (float(k), 10.0, 100.0), (float(k), 0.0, 110.0)]
        skin += [[(name, 255)], [(name, 128), (names[0], 127)], [(name, 255)]]
        tris.append((3 * k, 3 * k + 1, 3 * k + 2))
    part = modelin.Part(modelin.RIGGED, -1, pts, [(0.0, 0.0, 1.0)] * len(pts), [(0.5, 0.5)] * len(pts), tris,
                        skin=skin, tracks=None, draw=None, static=False)
    report = {"rigged": True, OWN_SKELETON: {"bones": len(names), "record": base64.b64encode(record).decode("ascii")}}
    with tempfile.TemporaryDirectory() as d:
        modelin.write_glb(modelin.Prepared([part], [], report), Path(d) / "own.glb", "the model")
        return (Path(d) / "own.glb").read_bytes()


class Out(unittest.TestCase):
    """The file Change it in Blender opens for an animated unit."""

    def setUp(self):
        self.raw, _pics, self.summary = gltf.model_glb(FakeLibrary(), NAME, clips=CLIPS)
        self.doc, self.bin = read_glb(self.raw)

    def test_every_bone_a_joint_and_each_clip_an_animation(self):
        skin = self.doc["skins"][0]
        self.assertEqual([self.doc["nodes"][j]["name"] for j in skin["joints"]], NAMES)   # fx_point too: clips move it
        self.assertEqual(self.summary["bones"], list(range(NB)))
        self.assertEqual([a["name"] for a in self.doc["animations"]], ["Run (made_run)", "Stand (made_stand)"])
        extras = self.doc["animations"][1]["extras"]
        self.assertEqual((extras["rusemod_actions"], extras["rusemod_frames"]), (["b_stand", "t_stand"], 31))
        got = {a["name"]: a for a in self.summary["animations"]}
        self.assertEqual((got["Run (made_run)"]["frames"], got["Run (made_run)"]["matched"]), (FRAMES, NB))
        self.assertEqual(got["Run (made_run)"]["missing"], [])
        self.assertLess(max(a["slant"] for a in self.summary["animations"]), 1e-6)
        for a in self.doc["animations"]:
            times = accessor(self.doc, self.bin, a["samplers"][0]["input"])
            self.assertEqual(times[0], 0.0)
            for s in a["samplers"]:
                self.assertEqual(s["interpolation"], "LINEAR")
                t = accessor(self.doc, self.bin, s["input"])
                self.assertEqual(t[-1], times[-1])                     # (every channel: the animation's whole length)
                for x in t:                                             # every key on a whole frame
                    self.assertAlmostEqual(x * baf.FPS, round(x * baf.FPS), places=4)

    def test_the_default_and_the_rest_bones_export_as_before(self):
        self.assertEqual(gltf.model_glb(FakeLibrary(), NAME)[0], gltf.model_glb(FakeLibrary(), NAME, clips=None)[0])
        self.assertNotIn("animations", read_glb(gltf.model_glb(FakeLibrary(), NAME, rest_bones=True)[0])[0])

    def test_in_blender_the_points_move_as_the_game_moves_them(self):
        """At every frame of each clip, every bone's skin matrix as Blender plays the file (its pose in the model times
        its inverse bind matrix) is the game's (its pose from the clip up its parents, times the record's inverse rest
        pose), through the mirror: the turned, hung, sized and mirrored bones alike."""
        b = Blenderish(self.raw)
        skin = self.doc["skins"][0]
        ibm = accessor(self.doc, self.bin, skin["inverseBindMatrices"])
        for (name, clip, _x), anim in zip(CLIPS, self.doc["animations"]):
            chans = b.channels(anim)
            self.assertEqual(b.frames(anim), clip.frames)
            for k in range(clip.frames):
                game = game_world(clip, k)
                for j, node in enumerate(skin["joints"]):
                    got = mul4(b.world(chans, node, k), rows_of(ibm[j]))
                    want = in_gltf(rig.mul(game[j], SK["bind"][j]))
                    for i in range(3):      # (a thousandth of a game unit: the keys' tolerances down a chain of bones)
                        for c in range(3):
                            self.assertAlmostEqual(got[i][c], want[i][c], delta=2e-5, msg=f"{name} {k} {NAMES[j]}")
                        self.assertAlmostEqual(got[i][3], want[i][3], delta=1e-5, msg=f"{name} {k} {NAMES[j]}")

    def test_keys_where_blender_needs_them(self):
        """A bone turned 40 degrees between two keys gets keys between them (Blender's straight line through the
        numbers would part from the game's arc); one barely turning keeps the clip's own."""
        run, stand = self.summary["animations"]
        self.assertGreater(run["keys"] / run["frames"], stand["keys"] / stand["frames"])
        flat = [(1.0, 2.0, 3.0)] * 9
        self.assertEqual(animglb.blender_keys(flat, "translation"), [0, 8])
        line = [(float(k), 0.0, 0.0) for k in range(9)]
        self.assertEqual(animglb.blender_keys(line, "translation"), [0, 8])
        bent = line[:4] + [(3.0 + k, 1.0 * k, 0.0) for k in range(1, 6)]
        self.assertEqual(animglb.blender_keys(bent, "translation"), [0, 3, 8])
        arc = baf.same_side([baf.axis_angle("z", 9.0 * k) for k in range(11)])   # 90 degrees at an even pace
        kept = animglb.blender_keys(arc, "rotation")
        self.assertGreater(len(kept), 2)
        for a, e in zip(kept, kept[1:]):
            for m in range(a + 1, e):
                self.assertLessEqual(animglb._apart(animglb._nlerp(arc[a], arc[e], (m - a) / (e - a)), arc[m]),
                                     animglb.TOL_TURN)
        self.assertEqual(animglb.blender_keys(arc[:2], "rotation"), [0, 1])

    def test_a_model_without_a_skeleton_or_with_points_past_it(self):
        lib = FakeLibrary(skeleton=None)
        with self.assertRaises(animglb.AnimGlbError):
            gltf.model_glb(lib, NAME, clips=CLIPS)
        short = baf.skeleton_bytes(NAMES[:3], PARENTS[:3], SK["bind"][:3], SK["local"][:3], SK["world"][:3])
        with self.assertRaises(animglb.AnimGlbError):
            gltf.model_glb(FakeLibrary(skeleton=short), NAME, clips=CLIPS)

    def test_export_passes_each_model_its_clips(self):
        with tempfile.TemporaryDirectory() as d:
            done = gltf.export(FakeLibrary(), [NAME], Path(d), side=64, rest_bones=True, clips={NAME: CLIPS[:1]})
            self.assertEqual(len(done[0]["animations"]), 1)
            plain = gltf.export(FakeLibrary(), [NAME], Path(d) / "p", side=64, rest_bones=True, clips={})
            self.assertNotIn("animations", plain[0])


class Back(unittest.TestCase):
    """Coming back: the file straight, and as Blender sends it."""

    def setUp(self):
        self.raw, _pics, _s = gltf.model_glb(FakeLibrary(), NAME, clips=CLIPS)

    def back(self, raw):
        doc, binary = modelin.glb_document(raw)
        r = rig.rig_of(doc, binary)
        return r, rig.back_of(r, RECORD)

    def test_straight_back_byte_for_byte(self):
        r, back = self.back(self.raw)
        self.assertTrue(back.turned and back.kept)
        self.assertEqual(back.names, NAMES)
        self.assertEqual(sorted(back.hung), ["bip01 l calf", "bip01 l thigh", "wheel"])
        got = rig.clips_back(r, back, RECORD, ORIGINALS)
        self.assertEqual([(g["name"], g["same"], g["changed"]) for g in got],
                         [(n, True, []) for n in ORIGINALS])
        self.assertEqual([g["clip"] for g in got], list(ORIGINALS.values()))

    def test_through_blender_byte_for_byte(self):
        sent = Blenderish(self.raw).send(order=[3, 0, 9, 1, 2, 8, 4, 7, 5, 6])
        r, back = self.back(sent)
        self.assertNotEqual(r.names, [n.lower() for n in NAMES])            # (Blender's order, not the record's)
        self.assertTrue(back.turned and back.kept)
        got = rig.clips_back(r, back, RECORD, ORIGINALS)
        self.assertEqual([g["clip"] for g in got], list(ORIGINALS.values()))
        self.assertTrue(all(g["same"] for g in got))

    def test_the_turned_back_file_reads_as_the_game_s(self):
        """Import model's reading of the turned-back file: the record kept byte for byte, the bones in its order, each
        point on the same bones, and every clip it makes within its packing of the game's at every frame."""
        sent = Blenderish(self.raw).send(order=[3, 0, 9, 1, 2, 8, 4, 7, 5, 6])
        back_raw, info = rig.turn_back(sent, RECORD)
        self.assertTrue(info["turned"] and info["kept"])
        doc, binary = modelin.glb_document(back_raw)
        r = rig.rig_of(doc, binary)
        self.assertEqual(r.kept, RECORD)
        self.assertEqual(r.names, [n.lower() for n in NAMES])
        self.assertEqual(r.notes, [])
        clips, _notes = unitmodel.own_clips(r)
        for name, clip, _x in CLIPS:
            c = baf.parse(clips[name])
            mine = {baf.skeleton(c.skeleton)["index"][u]: t for u, t in enumerate(c.tracks)}
            theirs = {SK["index"][u]: t for u, t in enumerate(clip.tracks)}
            for k in range(clip.frames):
                f = k / (clip.frames - 1)
                for b in range(NB):
                    a, e = rig.compose(*baf.sample(theirs[b], f)), rig.compose(*baf.sample(mine[b], f))
                    self.assertLess(max(abs(x - y) for x, y in zip(a, e)), 2e-4, msg=f"{name} {k} {NAMES[b]}")
        # the points: the same corners on the same bones as the file that went out (the rigged import's reading)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.glb").write_bytes(self.raw)
            (Path(d) / "b.glb").write_bytes(back_raw)
            a, b = modelin.read_model(Path(d) / "a.glb", skin=True), modelin.read_model(Path(d) / "b.glb", skin=True)
        self.assertEqual([(m.positions, m.triangles, m.skin) for m in a.meshes],
                         [(m.positions, m.triangles, m.skin) for m in b.meshes])

    def test_with_the_clips_that_went_out_the_file_holds_them_exactly(self):
        """Given the clips that went out, each bone the modder didn't change is written as its clip has it, so the
        turned-back file plays the game's poses to float precision at every frame."""
        sent = Blenderish(self.raw).send()
        back_raw, info = rig.turn_back(sent, RECORD, originals=ORIGINALS)
        self.assertEqual([a["changed"] for a in info["animations"]], [[], []])
        r = rig.rig_of(*modelin.glb_document(back_raw))
        _length, poses = r.poses(r.animations[0])
        run = CLIPS[0][1]
        for b in range(NB):
            for k in range(run.frames):
                want = rig.compose(*baf.sample(run.tracks[b], k / (run.frames - 1)))
                got = rig.compose(poses[b][0][k], poses[b][1][k], poses[b][2][k])
                self.assertLess(max(abs(x - y) for x, y in zip(got, want)), 1e-5, msg=f"{k} {NAMES[b]}")

    def test_a_changed_bone_comes_back_changed_there_only(self):
        """The spine turned 20 degrees more at every frame of the run in Blender: that clip comes back with the spine's
        track new and every other track the game's own, byte for byte; the other clip the game's, whole."""
        turn20 = baf.axis_angle("x", 20.0)
        sent = Blenderish(self.raw).send(change=("Run (made_run)", "bip01 spine", turn20))
        r, back = self.back(sent)
        got = {g["name"]: g for g in rig.clips_back(r, back, RECORD, ORIGINALS)}
        run, stand = got["Run (made_run)"], got["Stand (made_stand)"]
        self.assertEqual((run["same"], run["changed"]), (False, ["bip01 spine"]))
        self.assertTrue(stand["same"])
        mine, theirs = baf.parse(run["clip"]), CLIPS[0][1]
        self.assertEqual((mine.frames, mine.duration, mine.skeleton), (theirs.frames, theirs.duration, theirs.skeleton))
        for u in range(NB):
            if NAMES[SK["index"][u]] != "bip01 spine":
                self.assertEqual(mine.tracks[u], theirs.tracks[u])
        spine = NAMES.index("bip01 spine")
        _m, q_new, _s = baf.sample(mine.tracks[spine], 0.5)
        _m, q_old, _s = baf.sample(theirs.tracks[spine], 0.5)
        file_turn = abs(sum(a * b for a, b in zip(q_new, q_old)))   # (cos of half the angle between them)
        self.assertAlmostEqual(math.degrees(2 * math.acos(min(1.0, file_turn))), 20.0, places=2)
        back_raw, info = rig.turn_back(sent, RECORD, originals=ORIGINALS)
        self.assertEqual([a["changed"] for a in info["animations"]], [["bip01 spine"], []])

    def test_an_animation_made_in_blender_and_one_of_another_length(self):
        sent = Blenderish(self.raw).send()
        doc, binary = modelin.glb_document(sent)
        doc["animations"][1]["name"] = "Wave"          # (made in Blender: no clip went out under its name)
        r = rig.rig_of(doc, binary)
        back = rig.back_of(r, RECORD)
        got = {g["name"]: g for g in rig.clips_back(r, back, RECORD, ORIGINALS)}
        self.assertEqual(got["Wave"]["changed"], NAMES)
        self.assertFalse(got["Wave"]["same"])
        wave = baf.parse(got["Wave"]["clip"])
        self.assertEqual((wave.frames, wave.skeleton), (31, RECORD))
        short = {"Run (made_run)": baf.build(make_clip(40.0, frames=7))}
        got = {g["name"]: g for g in rig.clips_back(r, back, RECORD, short)}
        self.assertEqual(got["Run (made_run)"]["changed"], NAMES)

    def test_a_bone_moved_or_added_in_blender(self):
        sent = Blenderish(self.raw).send()
        doc, binary = modelin.glb_document(sent)
        head = next(i for i, n in enumerate(doc["nodes"]) if n.get("name") == "bip01 head")
        doc["nodes"][head]["translation"] = [v + 0.05 for v in doc["nodes"][head]["translation"]]
        doc["nodes"].append({"name": "tail", "translation": [0.0, 0.2, 0.0]})
        doc["nodes"][head].setdefault("children", []).append(len(doc["nodes"]) - 1)
        doc["skins"][0]["joints"].append(len(doc["nodes"]) - 1)
        ibm = accessor(doc, binary, doc["skins"][0]["inverseBindMatrices"]) + [(1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0,
                                                                                0, -2.0, 0, 1.0)]
        g = _Glb()
        g.doc, g.bin = doc, bytearray(binary)
        flat = [v for m in ibm for v in m]
        g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(flat)}f", *flat)), "componentType": FLOAT,
                                   "count": len(ibm), "type": "MAT4"})
        doc["skins"][0]["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
        r, back = self.back(g.to_bytes())
        self.assertEqual((back.moved, back.new, back.kept), (["bip01 head"], ["tail"], False))
        self.assertEqual(back.names[-1], "tail")
        self.assertEqual(back.parents[-1], NAMES.index("bip01 head"))
        self.assertEqual(back.fix[-1], rig._UNTURN)       # (made in Blender: turned back as every other bone is)
        sk = baf.skeleton(back.record)
        self.assertEqual(sk["names"], NAMES + ["tail"])
        head_world = sk["world"][NAMES.index("bip01 head")]
        want = SK["world"][NAMES.index("bip01 head")]
        moved = [head_world[3] - want[3], head_world[7] - want[7], head_world[11] - want[11]]
        # 0.05 along each of its parent's axes in Blender's metres: 5 x the square root of 3 of the game's units
        self.assertAlmostEqual(math.sqrt(sum(m * m for m in moved)), 5.0 * math.sqrt(3.0), places=3)

    def test_a_file_in_the_games_own_frames_is_left_alone(self):
        own = own_model_file()
        self.assertEqual(rig.turn_back(own, RECORD), (None, {"turned": False}))
        self.assertEqual(rig.turn_back(own), (None, {"turned": False}))            # (its own record, carried)
        self.assertEqual(rig.turn_back(self.raw), (None, {"turned": False}))       # (no record carried, none given)


class OwnModel(unittest.TestCase):
    """A model on bones of its own (the mod's files/models/<unit>.glb) out with its animations and back."""

    def test_laid_out_for_blender_and_back(self):
        own = own_model_file()
        raw, summary = animglb.own_glb(own, CLIPS, turned=True)
        self.assertEqual((summary["bones"], summary["turned"], len(summary["animations"])), (NB, True, 2))
        self.assertEqual(sorted(summary["hung"]), ["bip01 l calf", "bip01 l thigh", "wheel"])
        doc, binary = modelin.glb_document(raw)
        self.assertEqual(base64.b64decode(doc["skins"][0]["extras"][rig.SKELETON_EXTRA]), RECORD)
        sent = Blenderish(raw).send(order=list(reversed(range(NB))))
        back_raw, info = rig.turn_back(sent, RECORD, originals=ORIGINALS)
        self.assertTrue(info["kept"])
        self.assertEqual([a["changed"] for a in info["animations"]], [[], []])
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "back.glb").write_bytes(back_raw)
            report = unitmodel.read_mod_glb(Path(d) / "back.glb")
            (Path(d) / "own.glb").write_bytes(own)
            before = unitmodel.read_mod_glb(Path(d) / "own.glb")
        self.assertEqual(unitmodel.own_record(report.report), RECORD)       # the build gets the record as it was
        self.assertEqual([(p.positions, p.triangles, p.skin) for p in before.parts],
                         [(p.positions, p.triangles, p.skin) for p in report.parts])

    def test_a_skeleton_made_in_blender_isn_t_turned(self):
        """Bones that run along their +z (a skeleton made in Blender, through the export's mirror) go out as they are,
        and come back without a turn; the game's run along +x and are turned."""
        along_z = baf.skeleton_bytes(["root", "mid", "tip"], [-1, 0, 1], [rig.IDENTITY] * 3,
                                     [rig.IDENTITY, (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 50.0),
                                      (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 40.0)],
                                     [rig.IDENTITY, (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 50.0),
                                      (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 90.0)])
        along_x = baf.skeleton_bytes(["root", "mid", "tip"], [-1, 0, 1], [rig.IDENTITY] * 3,
                                     [rig.IDENTITY, (1, 0, 0, 50.0, 0, 1, 0, 0, 0, 0, 1, 0),
                                      (1, 0, 0, 40.0, 0, 1, 0, 0, 0, 0, 1, 0)],
                                     [rig.IDENTITY, (1, 0, 0, 50.0, 0, 1, 0, 0, 0, 0, 1, 0),
                                      (1, 0, 0, 90.0, 0, 1, 0, 0, 0, 0, 1, 0)])
        self.assertFalse(animglb.runs_along_x(along_z))
        self.assertTrue(animglb.runs_along_x(along_x))
        self.assertTrue(animglb.runs_along_x(RECORD) in (True, False))
        clip = baf.Clip(1.0, 31, [baf.Track([(0, 0.0, 0.0, float(10 * u))], [(0, 1.0, 1.0, 1.0)],
                                            [(0,) + baf.pack_quat(*baf.axis_angle("x", 15.0 * u)),
                                             (baf.LAST_TIME,) + baf.pack_quat(*baf.axis_angle("y", 25.0))])
                                  for u in range(3)], along_z)
        clip = baf.parse(baf.build(clip))
        raw, summary = animglb.own_glb(own_model_file(along_z), [("Wag", clip, {})])
        self.assertFalse(summary["turned"])
        sent = Blenderish(raw).send()
        r = rig.rig_of(*modelin.glb_document(sent))
        back = rig.back_of(r, along_z)
        self.assertIsNone(back)                         # (as it is: the game's frames, under the game's parents)
        got = unitmodel.own_clips(r)[0]["Wag"]
        mine = baf.parse(got)
        for u in range(3):
            for k in range(31):
                a = rig.compose(*baf.sample(clip.tracks[u], k / 30))
                e = rig.compose(*baf.sample(mine.tracks[u], k / 30))
                self.assertLess(max(abs(x - y) for x, y in zip(a, e)), 1e-4)

    def test_a_file_without_its_skeleton(self):
        with self.assertRaises(animglb.AnimGlbError):
            animglb.own_glb(gltf.model_glb(FakeLibrary(), NAME)[0], CLIPS)


class BlenderSide(unittest.TestCase):
    """blender_model.py (run by Blender, so read here as text): the file's animations at 30 frames a second, every
    action sent with every sample kept."""

    def test_send_names_its_animation_settings(self):
        source = blender.CHANGER.read_text(encoding="utf-8")
        for setting in ('export_animation_mode="ACTIONS"', "export_force_sampling=True", "export_frame_step=1",
                        "export_optimize_animation_size=False", "export_def_bones=False",
                        "export_reset_pose_bones=True", "export_anim_single_armature=True"):
            self.assertIn(setting, source)
        self.assertEqual(int(re.search(r"^FPS = (\d+)", source, re.M).group(1)), baf.FPS)
        self.assertIn("bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = FPS, 1.0", source)
        self.assertIn('action["actions"]', source)
        self.assertIn("bone.use_deform = False", source)


if __name__ == "__main__":
    unittest.main()
