"""rusemod.mocap (a .bvh made into one of the game's clips on the soldiers' skeleton) and RUSE Decoy's motion capture
calls (ruse_studio.decoy: decoy_mocap_open / _preview / _use)."""
import math
import struct
import tempfile
import threading
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, mocap
from ruse_studio.decoy import DecoyCalls, DecoyError

B = "\\"
RUN = B.join(["genanim_15", "ww2", "res3d", "units", "common", "fusilier_courselod0.baf"])

# a small soldier as the game keeps one: bones along their own x, the legs hanging from nothing (in the model's
# space), x forward, y right, z up; rest turns all straight, places in the model
SOLDIER = [("bip01", -1, (0, 0, 100)), ("bip01 pelvis", 0, (0, 0, 100)), ("bip01 spine", 1, (0, 0, 110)),
           ("bip01 spine1", 2, (0, 0, 125)), ("bip01 neck", 3, (0, 0, 140)), ("bip01 head", 4, (0, 0, 150)),
           ("bip01 l clavicle", 4, (0, -5, 140)), ("bip01 l upperarm", 6, (0, -15, 140)),
           ("bip01 l forearm", 7, (0, -15, 115)), ("bip01 l hand", 8, (0, -15, 90)),
           ("bip01 r clavicle", 4, (0, 5, 140)), ("bip01 r upperarm", 10, (0, 15, 140)),
           ("bip01 r forearm", 11, (0, 15, 115)), ("bip01 r hand", 12, (0, 15, 90)),
           ("bip01 l thigh", -1, (0, -10, 100)), ("bip01 l calf", -1, (0, -10, 55)), ("bip01 l foot", -1, (0, -10, 10)),
           ("bip01 l toe0", -1, (10, -10, 0)), ("bip01 r thigh", -1, (0, 10, 100)), ("bip01 r calf", -1, (0, 10, 55)),
           ("bip01 r foot", -1, (0, 10, 10)), ("bip01 r toe0", -1, (10, 10, 0)), ("arme_1", 13, (10, 15, 90))]


def soldier_part():
    names = [n for n, _p, _w in SOLDIER]
    parents = [p for _n, p, _w in SOLDIER]
    nb = len(names)
    head = 36 + 2 * nb
    m_off = head + (-head % 4)
    p_off = m_off + 144 * nb
    i_off = p_off + 4 * nb
    n_off = i_off + 4 * nb
    out = bytearray(struct.pack("<II7I", 1, nb, m_off, p_off, i_off, n_off, 144 * nb, 4 * nb, 4 * nb))
    out += struct.pack(f"<{nb}H", *(len(n) for n in names))
    out += bytes(m_off - len(out))

    def m(t):
        return (1.0, 0.0, 0.0, t[0], 0.0, 1.0, 0.0, t[1], 0.0, 0.0, 1.0, t[2])
    world = [w for _n, _p, w in SOLDIER]
    local = [w if p < 0 else tuple(w[i] - world[p][i] for i in range(3)) for (_n, p, w) in SOLDIER]
    for w in world:
        out += struct.pack("<12f", *m(tuple(-v for v in w)))    # bind: the inverse rest pose
    for t in local:
        out += struct.pack("<12f", *m(t))
    for w in world:
        out += struct.pack("<12f", *m(w))
    out += struct.pack(f"<{nb}i", *parents) + struct.pack(f"<{nb}I", *range(nb))
    raw = "".join(names).encode("latin-1")
    return bytes(out + raw + bytes(-len(raw) % 4))


def template(loops=True):
    """A game clip on the small soldier: every bone at rest, its root ending where it starts when it `loops`."""
    ident = baf.pack_quat(0.0, 0.0, 0.0, 1.0)
    tracks = []
    for name, p, w in SOLDIER:
        t = w if p < 0 else tuple(w[i] - SOLDIER[p][2][i] for i in range(3))
        T = [(0,) + tuple(map(float, t))]
        if name == "bip01":
            end = t if loops else (t[0] + 50, t[1], 30)
            T = [(0,) + tuple(map(float, t)), (baf.time_of(0.5),) + tuple(map(float, t)),
                 (baf.LAST_TIME,) + tuple(map(float, end))]
        tracks.append(baf.Track(T, [(0, 1.0, 1.0, 1.0)], [(0,) + ident]))
    return baf.Clip(0.8, 25, tracks, soldier_part())


# a CMU-style file: Y up, facing +Z, the left on +X, T-pose; channels Z Y X like the CMU conversion's
JOINTS = [("Hips", None, (0, 0, 0)), ("LeftUpLeg", "Hips", (8, -2, 0)), ("LeftLeg", "LeftUpLeg", (0, -40, 0)),
          ("LeftFoot", "LeftLeg", (0, -40, 0)), ("LeftToeBase", "LeftFoot", (0, -8, 10)),
          ("RightUpLeg", "Hips", (-8, -2, 0)), ("RightLeg", "RightUpLeg", (0, -40, 0)),
          ("RightFoot", "RightLeg", (0, -40, 0)), ("RightToeBase", "RightFoot", (0, -8, 10)),
          ("Spine", "Hips", (0, 10, 0)), ("Spine1", "Spine", (0, 15, 0)), ("Neck", "Spine1", (0, 15, 0)),
          ("Head", "Neck", (0, 10, 0)), ("LeftShoulder", "Spine1", (5, 12, 0)), ("LeftArm", "LeftShoulder", (10, 0, 0)),
          ("LeftForeArm", "LeftArm", (25, 0, 0)), ("LeftHand", "LeftForeArm", (25, 0, 0)),
          ("RightShoulder", "Spine1", (-5, 12, 0)), ("RightArm", "RightShoulder", (-10, 0, 0)),
          ("RightForeArm", "RightArm", (-25, 0, 0)), ("RightHand", "RightForeArm", (-25, 0, 0))]


def bvh_text(frames, names=None, root_y=90.0):
    """`frames`: per frame {joint: (z, y, x) degrees} and "pos" (x, y, z) for the hips; 120 a second."""
    names = names or {}
    kids = {}
    for n, p, _o in JOINTS:
        kids.setdefault(p, []).append(n)
    off = {n: o for n, _p, o in JOINTS}
    lines, order = ["HIERARCHY"], []

    def joint(n, depth):
        order.append(n)
        pad = "  " * depth
        lines.append(f"{pad}{'ROOT' if depth == 0 else 'JOINT'} {names.get(n, n)}")
        lines.append(pad + "{")
        o = (0.0, root_y, 0.0) if depth == 0 else off[n]
        lines.append(f"{pad}  OFFSET {o[0]} {o[1]} {o[2]}")
        lines.append(f"{pad}  CHANNELS " + ("6 Xposition Yposition Zposition Zrotation Yrotation Xrotation" if depth == 0
                                            else "3 Zrotation Yrotation Xrotation"))
        for k in kids.get(n, []):
            joint(k, depth + 1)
        if n not in kids:
            lines.extend([pad + "  End Site", pad + "  {", pad + "    OFFSET 0 5 0", pad + "  }"])
        lines.append(pad + "}")
    joint("Hips", 0)
    lines += ["MOTION", f"Frames: {len(frames)}", "Frame Time: 0.0083333"]
    for f in frames:
        vals = []
        for n in order:
            if n == "Hips":
                vals += list(f.get("pos", (0.0, 0.0, 0.0)))
            vals += list(f.get(n, (0.0, 0.0, 0.0)))
        lines.append(" ".join(f"{v:g}" for v in vals))
    return "\n".join(lines) + "\n"


def world(clip, k):
    """Every bone's (turn, place) in the model at key k of the made clip (the moves the clip itself keys)."""
    s = mocap.game_rest(clip)
    out = [None] * len(s["names"])
    for b in sorted(range(len(s["names"])), key=lambda b: mocap._depth(s["parents"], b)):
        t = clip.tracks[s["index"].index(b)]
        tk = t.T[min(k, len(t.T) - 1)]
        rk = t.R[min(k, len(t.R) - 1)]
        r = mocap._q_to_m(baf.unpack_quat(rk[1:5]))
        p = s["parents"][b]
        if p < 0:
            out[b] = (r, tk[1:4])
        else:
            pr, pp = out[p]
            out[b] = (mocap._mm(pr, r), mocap._add(pp, mocap._mv(pr, tk[1:4])))
    return {n: out[i] for i, n in enumerate(s["names"])}


class Read(unittest.TestCase):
    def test_a_file_read(self):
        b = mocap.read_bvh(bvh_text([{}, {}, {}]))
        self.assertEqual(len(b.frames), 3)
        self.assertAlmostEqual(b.frame_time, 0.0083333)
        self.assertIn("Head_end", b.names)                       # end sites kept, without channels
        self.assertEqual(b.channels[0][:3], ["Xposition", "Yposition", "Zposition"])
        self.assertEqual(mocap.parts_of(b)["l_upperarm"], b.names.index("LeftArm"))
        self.assertEqual(mocap.parts_of(b)["l_clavicle"], b.names.index("LeftShoulder"))
        self.assertEqual(mocap.missing(b), [])
        short = bvh_text([{}, {}]).replace("Frames: 2", "Frames: 3")   # an exporter saying one frame too many
        self.assertEqual(len(mocap.read_bvh(short).frames), 2)
        for bad in ("", "HELLO", "HIERARCHY\nROOT Hips\n{\nOFFSET 0 0 0\n"):
            with self.subTest(bad=bad[:10]), self.assertRaises(mocap.MocapError):
                mocap.read_bvh(bad)

    def test_the_usual_names(self):
        style = {"LeftUpLeg": "LeftHip", "LeftLeg": "LeftKnee", "LeftFoot": "LeftAnkle", "LeftToeBase": "LeftToe",
                 "LeftShoulder": "LeftCollar", "LeftArm": "LeftShoulder", "LeftForeArm": "LeftElbow",
                 "LeftHand": "LeftWrist", "Spine": "Chest", "Spine1": "Chest4"}
        style.update({k.replace("Left", "Right"): v.replace("Left", "Right") for k, v in style.items()})
        b = mocap.read_bvh(bvh_text([{}], names=style))           # 100STYLE's names
        got = {p: b.names[j] for p, j in mocap.parts_of(b).items()}
        self.assertEqual((got["l_clavicle"], got["l_upperarm"], got["l_thigh"], got["chest"]),
                         ("LeftCollar", "LeftShoulder", "LeftHip", "Chest4"))
        mix = {n: "mixamorig:" + n for n, _p, _o in JOINTS}
        self.assertEqual(mocap.missing(mocap.read_bvh(bvh_text([{}], names=mix))), [])
        odd = {"LeftUpLeg": "Bein_L", "LeftLeg": "Knie_L"}
        self.assertEqual(mocap.missing(mocap.read_bvh(bvh_text([{}], names=odd))), ["l_thigh", "l_calf"])

    def test_credits_of_the_known_sets(self):
        b = mocap.read_bvh(bvh_text([{}]))
        b.names += ["LHipJoint", "LowerBack"]
        self.assertIn("mocap.cs.cmu.edu", mocap.credit_of(b))
        b.names = ["Hips", "Chest4", "LeftCollar", "LeftHip"]
        self.assertIn("100STYLE", mocap.credit_of(b))
        self.assertEqual(mocap.credit_of(mocap.read_bvh(bvh_text([{}]))), "")


class Retarget(unittest.TestCase):
    def test_rest_stands_as_the_soldier(self):
        clip, info = mocap.retarget(mocap.read_bvh(bvh_text([{}] * 121)), template(), 0.0, 1.0)
        self.assertEqual((info["frames"], clip.frames), (31, 31))
        self.assertAlmostEqual(clip.duration, 1.0, places=5)
        self.assertTrue(info["loop"])
        baf.check(clip)
        self.assertEqual(baf.build(baf.parse(baf.build(clip))), baf.build(clip))
        w = world(clip, 0)
        rest = {n: p for n, _x, p in SOLDIER}
        for leg in ("l", "r"):   # straight legs, straight down, the soldier's own lengths
            for a, b in (("thigh", "calf"), ("calf", "foot")):
                pa, pb = w[f"bip01 {leg} {a}"][1], w[f"bip01 {leg} {b}"][1]
                self.assertAlmostEqual(math.dist(pa, pb), math.dist(rest[f"bip01 {leg} {a}"], rest[f"bip01 {leg} {b}"]),
                                       delta=0.3)
                self.assertAlmostEqual(pa[0], pb[0], delta=0.3)
                self.assertAlmostEqual(pa[1], pb[1], delta=0.3)
            # the file's foot points a little flatter than the soldier's: its toe is the lowest, on the ground
            self.assertAlmostEqual(w[f"bip01 {leg} toe0"][1][2], 0.0, delta=0.3)
            self.assertGreater(w[f"bip01 {leg} toe0"][1][0], 5)
        self.assertAlmostEqual(w["bip01"][1][2], w["bip01 l thigh"][1][2], delta=0.3)
        self.assertEqual(len(clip.tracks[22].R), 1)               # the rifle keeps the game clip's own keys
        # the arms: T-pose in the file, out to the sides on the soldier (its left is -y)
        la = mocap._sub(w["bip01 l hand"][1], w["bip01 l upperarm"][1])
        self.assertLess(la[1], -40)
        self.assertAlmostEqual(la[2], 0.0, delta=1.0)

    def test_forward_and_sides_as_the_game_has_them(self):
        # knee bent: the shin back (the file's -z); the left arm raised (about the file's z)
        bent = {"LeftLeg": (0.0, 0.0, 90.0), "LeftArm": (90.0, 0.0, 0.0)}
        clip, _ = mocap.retarget(mocap.read_bvh(bvh_text([bent] * 31)), template(), 0.0, 0.25)
        w = world(clip, 0)
        shin = mocap._sub(w["bip01 l foot"][1], w["bip01 l calf"][1])
        self.assertLess(shin[0], -40)                              # backward is the game's -x
        arm = mocap._sub(w["bip01 l forearm"][1], w["bip01 l upperarm"][1])
        self.assertGreater(arm[2], 20)                             # the left arm up, the right as it was
        rarm = mocap._sub(w["bip01 r forearm"][1], w["bip01 r upperarm"][1])
        self.assertAlmostEqual(rarm[2], 0.0, delta=1.0)
        self.assertGreater(rarm[1], 20)

    def test_on_the_spot_and_looped(self):
        frames = [{"pos": (0.0, 0.0, k * 1.0), "LeftUpLeg": (0.0, 0.0, 20.0 * math.sin(k / 10))} for k in range(121)]
        b = mocap.read_bvh(bvh_text(frames))
        clip, info = mocap.retarget(b, template(), 0.0, 1.0)
        root = clip.tracks[0].T
        self.assertAlmostEqual(root[0][1], root[-1][1], places=3)  # walked 120 units forward, kept on the spot
        self.assertLess(max(abs(k[1]) for k in root), 1.0)
        thigh = clip.tracks[14].R
        self.assertEqual(thigh[0][1:], thigh[-1][1:])              # looped: the last turn is the first
        moved, _ = mocap.retarget(b, template(), 0.0, 1.0, in_place=False, loop=False)
        self.assertGreater(moved.tracks[0].T[-1][1] - moved.tracks[0].T[0][1], 100)
        once, info = mocap.retarget(b, template(loops=False), 0.0, 1.0)
        self.assertFalse(info["loop"])                              # the game's clip doesn't loop: neither does it
        self.assertFalse(mocap._loops(template(loops=False)))

    def test_refused(self):
        b = mocap.read_bvh(bvh_text([{}], names={"LeftUpLeg": "Bein_L"}))
        with self.assertRaises(mocap.MocapError):
            mocap.retarget(b, template())
        horse = template()
        horse = baf.Clip(horse.duration, horse.frames, horse.tracks, soldier_part().replace(b"bip01", b"horse"))
        with self.assertRaises(mocap.MocapError):
            mocap.retarget(mocap.read_bvh(bvh_text([{}])), horse)


class Calls(DecoyCalls):
    def __init__(self, d):
        self.mod = Path(d)
        self._saving = threading.RLock()

    def _mod_dir(self, kind="mod"):
        return self.mod

    def _decoy_clip_row(self, member):
        return {"member": RUN, "kind": "infantry", "name": "Fusilier course", "seconds": 0.8, "frames": 25,
                "bones": len(SOLDIER), "names": ["t_course"], "units": ["u"],
                "skeleton": "|".join(n for n, _p, _w in SOLDIER)} if member.lower() == RUN else None

    def _decoy_game_clips(self):
        return lambda m: baf.build(template()) if m.lower() == RUN else None

    def _decoy_preview_model(self, r):
        return "us_paratrooper_model"

    def _decoy_glb(self, model, raw):
        return {"url": "cache/x.glb", "model": model, "seconds": baf.parse(raw).duration}


class DecoyMocap(unittest.TestCase):
    def test_open_watch_use_and_take_out(self):
        with tempfile.TemporaryDirectory() as d:
            calls = Calls(d)
            got = calls.decoy_mocap_open("walk.bvh", bvh_text([{}] * 241))
            self.assertEqual((got["missing"], got["parts"], round(got["seconds"], 1)), ([], 21, 2.0))
            seen = calls.decoy_mocap_preview(RUN, got["id"], 0.5, 1.0)
            self.assertEqual((seen["url"], seen["frames"], seen["loop"]), ("cache/x.glb", 31, True))
            self.assertFalse((Path(d) / anim.REPLACE).exists())    # watching saves nothing
            with self.assertRaises(DecoyError):
                calls.decoy_mocap_preview(RUN, "nope", 0, 1)
            with self.assertRaises(DecoyError):
                calls.decoy_mocap_preview(RUN, got["id"], -1, 1)
            used = calls.decoy_mocap_use(RUN, got["id"], 0.5, 1.0, True, None, "Me, CC0")
            self.assertTrue(used["mine"])
            own = Path(d) / anim.REPLACE / anim.clip_key(RUN)
            self.assertEqual(baf.parse(own.read_bytes()).frames, 31)
            side = tomllib.loads(own.with_suffix(".toml").read_text(encoding="utf-8"))
            self.assertEqual((side["source"], side["start"], side["credit"]), ("walk.bvh", 0.5, "Me, CC0"))
            self.assertEqual(anim.mod_clips(Path(d))[RUN]["file"], own)   # the build takes it
            calls.decoy_anim_reset(RUN)
            self.assertFalse(own.exists() or own.with_suffix(".toml").exists())
            with self.assertRaises(DecoyError):
                calls.decoy_mocap_open("bad.bvh", "HELLO")


if __name__ == "__main__":
    unittest.main()
