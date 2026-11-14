"""The Horse Squad made on the player's own PC from their own game (rusemod.horsesquad; the owner, 2026-11-12: "Yes,
like era units").

Made-up skeletons, clips, listings and files always run: the combined skeleton (the horse's bones renamed, the rider's
from the hips up hung on the horse's back, his rest poses moved up by the seat), the combined clips (one's bones
played, the other's held, the rider's root carried onto the horse's back), the files' animations and what each says,
the horse's fall and the rider's deaths re-based (he falls in the world as he did over a standing horse), the
listings read from a game index, and the refusals.

With RUSE_GAME naming a game folder: the two files made from it (on 62 bones, 25 animations, read by the Studio's own
reader), the same bytes twice; with RUSE_GAME_INDEX naming the Studio's game index too, the squad's listings read from
it and from the game's unit data alike; with RUSE_HORSE_FIXES3 naming the folder of the two files the game test passed
with on 2026-11-11 (horse-squad-rifle-death.glb, horse-squad-bazooka-death.glb), both byte for byte those."""
import json
import math
import os
import sqlite3
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from rusemod import baf, horsesquad as hs
from rusemod.gltf import FLOAT, _Glb

GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
INDEX = Path(os.environ["RUSE_GAME_INDEX"]) if os.environ.get("RUSE_GAME_INDEX") else None
FIXES3 = Path(os.environ["RUSE_HORSE_FIXES3"]) if os.environ.get("RUSE_HORSE_FIXES3") else None


# --- the sums: plain Python in a fixed order (numpy's matrix and dot products go to OpenBLAS, chosen by processor) ---
class PlainSums(unittest.TestCase):
    def test_a_fused_multiply_add_rounds_once(self):
        a = 1.0 + 2.0 ** -30
        self.assertEqual(a * a - (1.0 + 2.0 ** -29), 0.0)                 # rounded twice: the last bit lost
        self.assertEqual(hs._fma(a, a, -(1.0 + 2.0 ** -29)), 2.0 ** -60)   # rounded once
        self.assertEqual(math.copysign(1.0, hs._fma(-0.0, 1.0, -0.0)), -1.0)
        self.assertEqual(math.copysign(1.0, hs._fma(1.0, 1.0, -1.0)), 1.0)
        self.assertEqual(hs._fma(3.0, 0.5, 0.25), 1.75)

    def test_each_product_summed_fused_in_its_order(self):
        e = 2.0 ** -30
        v = (1.0 + e, 1.0 - e, 3.0, -1.0)
        self.assertEqual(hs._dot4(v, v), hs._fma(-1.0, -1.0, hs._fma(3.0, 3.0, hs._fma(1.0 - e, 1.0 - e, v[0] * v[0]))))
        a = [[1.0 + e, 2.0, 0.0, 5.0], [0.0, 1.0, 0.0, -7.0], [0.0, 0.0, 1.0, 0.5], [0.0, 0.0, 0.0, 1.0]]
        b = [[1.0 - e, 0.0, 0.0, 1.0], [2.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        got = hs._mm(a, b)
        self.assertEqual(got[0][0], hs._fma(5.0, 0.0, hs._fma(0.0, 0.0, hs._fma(2.0, 2.0, a[0][0] * b[0][0]))))
        self.assertEqual(got[0][3], hs._fma(5.0, 1.0, hs._fma(0.0, 0.0, hs._fma(2.0, 0.0, a[0][0] * 1.0))))
        m = [[0.5, 1.0 + e, -2.0], [1.0, 0.0, 0.0], [0.0, 3.0, 1.0 - e]]
        self.assertEqual(hs._mv3(m, (2.0, 1.0 - e, 4.0))[0],
                         hs._fma(-2.0, 4.0, hs._fma(0.5, 2.0, (1.0 + e) * (1.0 - e))))   # element 1, then 0, then 2

    def test_the_inverse_and_the_turn_of_a_matrix(self):
        m = hs._trs4((10.0, -4.0, 70.0), turn_z(30), (1.0, 1.0, 1.0))
        back = hs._mm(hs._inverse(m), m)
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(back[i][j], 1.0 if i == j else 0.0, places=12)
        sized = hs._trs4((1.0, 2.0, 3.0), turn_z(-70), (1.2336, -0.8, 2.0))
        back = hs._mm(sized, hs._inverse(sized))
        self.assertLess(max(abs(back[i][j] - (i == j)) for i in range(4) for j in range(4)), 1e-12)
        q = hs._mat_quat([row[:3] for row in m[:3]])
        np.testing.assert_allclose(q, turn_z(30), atol=1e-15)

    def test_sin_and_cos_rounded_once(self):
        self.assertEqual(hs._sin_cos(0.0), (0.0, 1.0))
        for deg in (-115.0, -70.0, -25.0, 5.0, 15.0, 45.0, 88.0, 0.1):
            h = math.radians(deg) / 2
            s, c = hs._sin_cos(h)
            self.assertLessEqual(abs(s - math.sin(h)), math.ulp(s), deg)       # (Windows' own: within one step)
            self.assertLessEqual(abs(c - math.cos(h)), math.ulp(c), deg)
        # rounded once where Windows' own sin and cos round the other way (this PC, 2026-11-12): the nearest floats
        self.assertEqual(hs._sin_cos(-math.pi / 4), (-0.7071067811865475, 0.7071067811865476))
        self.assertEqual(hs._sin_cos(math.radians(-115.0) / 2)[0], float.fromhex("-0x1.afd100eafc290p-1"))

    def test_no_sum_goes_through_numpy_s_matrix_or_dot_products(self):
        """The guard: numpy's matrix product, dot product, lengths and inverses go to OpenBLAS, whose code is chosen by
        processor (its dot product made the old PC's fall come out different), and Windows' own sin and cos aren't
        always the nearest: none of them may come back into the module."""
        import re
        text = Path(hs.__file__).read_text(encoding="utf-8")
        code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
        found = re.findall(r"np\.(?:dot|matmul|inner|vdot|einsum|tensordot|trace)\b|np\.linalg|\s@\s|\.dot\(|"
                           r"(?:math|np)\.(?:sin|cos|tan|asin|acos|atan2?|exp|log|pow)\(", code)
        self.assertEqual(found, [])


# --- made-up skeletons: every rest pose a plain move, so each number can be worked out by hand ---
def moved(x, y, z) -> tuple:
    return (1.0, 0.0, 0.0, float(x), 0.0, 1.0, 0.0, float(y), 0.0, 0.0, 1.0, float(z))


def record(bones: list) -> bytes:
    """A record of [(name, parent, (x, y, z) from the parent)], its tracks depth by depth as the game's."""
    names, parents = [b[0] for b in bones], [b[1] for b in bones]
    world = []
    for name, p, (x, y, z) in bones:
        px, py, pz = (world[p][3], world[p][7], world[p][11]) if p >= 0 else (0.0, 0.0, 0.0)
        world.append(moved(px + x, py + y, pz + z))
    return baf.skeleton_bytes(names, parents, [moved(-w[3], -w[7], -w[11]) for w in world],
                              [moved(*b[2]) for b in bones], world)


HORSE = [("bip01", -1, (0, 0, 100)), ("bip01 pelvis", 0, (5, 0, 0)), ("bip01 spine", 1, (10, 0, 2)),
         ("bip01 spine1", 2, (12, 0, 3)), ("bip01 footsteps", 0, (0, 0, -100)), ("horse", -1, (0, 0, 0)),
         ("bip01 tail", 1, (-20, 0, 0))]
RIDER = [("bip01", -1, (0, 0, 90)), ("bip01 pelvis", 0, (0, 0, 2)), ("bip01 spine", 1, (0, 0, 15)),
         ("bip01 l thigh", -1, (0, 8, 85)), ("soldat", -1, (0, 0, 0)), ("bip01 head", 2, (0, 0, 40)),
         ("arme_1", 2, (20, -10, 10))]


class TheSkeleton(unittest.TestCase):
    def setUp(self):
        self.bones = hs._combined(record(HORSE), record(RIDER))

    def test_the_horse_s_bones_renamed_then_the_rider_s_from_the_hips_up(self):
        b = self.bones
        self.assertEqual(b.names, ["horse bip01", "horse pelvis", "horse spine", "horse tail", "horse spine1",
                                   "bip01", "bip01 pelvis", "bip01 spine", "bip01 head", "arme_1"])
        # the rider's root on the horse's mid-back bone; the footsteps, the "horse" bone, his legs and soldat out
        self.assertEqual(b.parents, [-1, 0, 1, 1, 2, 4, 5, 6, 7, 7])

    def test_the_rider_moved_up_by_the_seat_and_his_root_seen_from_the_horse_s_back(self):
        b, (sx, sy, sz) = self.bones, hs.SEAT
        rider_world = {"bip01": (0, 0, 90), "bip01 pelvis": (0, 0, 92), "bip01 spine": (0, 0, 107),
                       "bip01 head": (0, 0, 147), "arme_1": (20, -10, 117)}
        for name, (x, y, z) in rider_world.items():
            k = b.names.index(name)
            self.assertEqual(b.world[k], moved(x + sx, y + sy, z + sz), name)
            self.assertEqual(b.bind[k], moved(-x - sx, -y - sy, -z - sz), name)
        spine1 = (5 + 10 + 12, 0, 100 + 2 + 3)            # the horse's mid-back bone at rest
        self.assertEqual(b.local[b.names.index("bip01")], moved(sx - spine1[0], sy - spine1[1], 90 + sz - spine1[2]))
        self.assertEqual(b.local[b.names.index("bip01 head")], moved(0, 0, 40))   # the others as they were

    def test_the_record_reads_back_and_is_one_the_game_takes(self):
        b = self.bones
        blob = baf.skeleton_bytes(b.names, b.parents, b.bind, b.local, b.world, list(range(len(b.names))))
        hs._check_record(blob)
        sk = baf.skeleton(blob)
        self.assertEqual((sk["names"], sk["parents"], sk["index"]), (b.names, b.parents, list(range(10))))

    def test_a_rider_with_a_second_root_is_refused_in_words(self):
        with self.assertRaisesRegex(hs.HorseSquadError, "second root"):
            hs._combined(record(HORSE), record(RIDER + [("bip01 prop", -1, (0, 0, 0))]))

    def test_a_horse_bone_on_a_left_out_one_is_refused_in_words(self):
        with self.assertRaisesRegex(hs.HorseSquadError, "isn't built as the Generic Horse expects"):
            hs._combined(record(HORSE + [("bip01 saddle", 5, (0, 0, 1))]), record(RIDER))

    def test_a_record_past_64_bones_is_refused(self):
        many = [("bip01", -1, (0, 0, 0))] + [(f"bone{i}", 0, (1, 0, 0)) for i in range(64)]
        with self.assertRaises(hs.HorseSquadError):
            hs._check_record(record(many))


# --- made-up clips on those skeletons ---
def turn_z(deg) -> tuple:
    h = math.radians(deg) / 2
    return (0.0, 0.0, math.sin(h), math.cos(h))


def clip(bones: list, frames: int, seconds: float, moving: str) -> baf.Clip:
    """A clip of `frames` frames: every bone at its rest place, the bone `moving` stepping along x and turning about z
    over three keys."""
    rec = record(bones)
    sk = baf.skeleton(rec)
    tracks = []
    for b in sk["index"]:
        x, y, z = bones[b][2]
        if bones[b][0] == moving:
            T = [(0, x, y, z), (baf.LAST_TIME // 2, x + 3.0, y, z), (baf.LAST_TIME, x + 7.0, y + 1.0, z)]
            R = [(0, *baf.pack_quat(*turn_z(0))), (baf.LAST_TIME // 2, *baf.pack_quat(*turn_z(20))),
                 (baf.LAST_TIME, *baf.pack_quat(*turn_z(45)))]
        else:
            T, R = [(0, float(x), float(y), float(z))], [(0, *baf.pack_quat(0.0, 0.0, 0.0, 1.0))]
        tracks.append(baf.Track(T=T, S=[(0, 1.0, 1.0, 1.0)], R=R))
    return baf.Clip(seconds, frames, tracks, rec)


class TheClips(unittest.TestCase):
    def setUp(self):
        self.bones = hs._combined(record(HORSE), record(RIDER))
        b = self.bones
        self.blob = baf.skeleton_bytes(b.names, b.parents, b.bind, b.local, b.world, list(range(len(b.names))))
        a = np.eye(4)
        a[:3, :3] = hs._quat_m(turn_z(30))
        a[:3, 3] = (4.0, -2.0, 60.0)
        self.A = a
        self.raw = {"horse.baf": baf.build(clip(HORSE, 25, 0.8, "bip01 pelvis")),
                    "rider.baf": baf.build(clip(RIDER, 41, 1.333, "bip01"))}
        self.maker = hs._Clips(self.raw, b, a, self.blob)

    def test_the_rider_s_clip_with_the_horse_held(self):
        out = baf.parse(self.maker.make("horse.baf", "rider.baf", "rider"))
        rider = baf.parse(self.raw["rider.baf"])
        self.assertEqual((out.frames, out.duration, out.skeleton), (41, rider.duration, self.blob))
        names = self.bones.names
        for u, t in enumerate(out.tracks):   # track u drives bone u
            if names[u].startswith("horse"):
                self.assertEqual((len(t.T), len(t.R), len(t.S)), (1, 1, 1), names[u])   # held
        own = {baf.skeleton(rider.skeleton)["names"][b]: rider.tracks[u]
               for u, b in enumerate(baf.skeleton(rider.skeleton)["index"])}
        for name in ("bip01 pelvis", "bip01 head", "arme_1"):
            self.assertEqual(out.tracks[names.index(name)], own[name], name)            # his own keys
        root = out.tracks[names.index("bip01")]
        for got, was in zip(root.T, own["bip01"].T):                                     # carried onto the back
            want = self.A[:3, :3] @ np.array(was[1:4]) + self.A[:3, 3]
            self.assertEqual(got[0], was[0])
            np.testing.assert_allclose(got[1:4], want, atol=2e-4)
        for got, was in zip(root.R, own["bip01"].R):
            want = baf.qmul(turn_z(30), baf.unpack_quat(was[1:5]))
            q = baf.unpack_quat(got[1:5])
            self.assertLess(min(np.abs(np.subtract(q, want)).max(), np.abs(np.add(q, want)).max()), 1e-5)

    def test_the_horse_s_clip_with_the_rider_held_at_his_first_frame(self):
        out = baf.parse(self.maker.make("horse.baf", "rider.baf", "horse"))
        horse = baf.parse(self.raw["horse.baf"])
        self.assertEqual((out.frames, out.duration), (25, horse.duration))
        names = self.bones.names
        pelvis = out.tracks[names.index("horse pelvis")]
        self.assertEqual(len(pelvis.T), 3)                                               # the horse moves
        root = out.tracks[names.index("bip01")]
        self.assertEqual((len(root.T), len(root.R)), (1, 1))                             # he holds his first pose
        np.testing.assert_allclose(root.T[0][1:4], self.A[:3, :3] @ np.array([0.0, 0.0, 90.0]) + self.A[:3, 3],
                                   atol=2e-4)

    def test_a_clip_without_one_of_the_rider_s_bones_is_refused(self):
        raw = dict(self.raw, **{"rider.baf": baf.build(clip(RIDER[:5] + [("bip01 neck", 2, (0, 0, 30)),
                                                                       RIDER[6]], 5, 0.2, "bip01"))})
        with self.assertRaisesRegex(hs.HorseSquadError, "bip01 head"):
            hs._Clips(raw, self.bones, self.A, self.blob).make("horse.baf", "rider.baf", "rider")


class TheListingsAndTheAnimations(unittest.TestCase):
    def test_the_rider_s_top_half_and_the_horse_s_clips(self):
        top = {"fusilier_standlod0": "fusilier_standlod0", "fusilier_tirlod0": "fusilier_tirlod0",
               "fusilier_accroupilod0": "fusilier_standlod0", "fusilier_deroutelod0": "fusilier_standlod0",
               "fusilier_course2lod0": "fusilier_standlod0", "fusilier_marchelod0": "fusilier_standlod0",
               "fusilier_course_viselod0": "fusilier_stand_viselod0",
               "fusilier_bazooka_course_gauche_viselod0": "fusilier_bazooka_viselod0",
               "fusilier_bazooka_tirlod0": "fusilier_bazooka_tirlod0"}
        self.assertEqual({k: hs._top_source(k) for k in top}, top)
        self.assertEqual([hs._bottom_source(k) for k in ("b_stand", "b_marche", "b_course_gauche", "b_deroute",
                                                         "b_mort_balle", "idle1")],
                         ["stand", "walk", "run", "run", "stand", "stand"])

    def test_each_file_s_animations_in_the_order_its_figures_list_them(self):
        listings = {"GfxDescriptorFusilier": [("t_stand", "fusilier_standlod0"), ("b_stand", "fusilier_standlod0"),
                                              ("t_course", "fusilier_course2lod0"),
                                              ("b_course", "fusilier_course2lod0"),
                                              ("b_marche", "fusilier_marchelod0"), ("t_tir", "fusilier_tirlod0"),
                                              ("t_stand", "fusilier_standlod0")],
                    "GfxDescriptorBazooka": [("t_stand", "fusilier_standlod0"),
                                             ("t_bazooka_tir", "fusilier_bazooka_tirlod0")],
                    hs.TOKEN: [("b_stand", "fusilier_standlod0"), ("t_tir", "fusilier_tirlod0")]}
        top_of = {"fusilier_standlod0": "hr_t_stand", "fusilier_course2lod0": "hr_t_stand",
                  "fusilier_marchelod0": "hr_t_stand", "fusilier_tirlod0": "hr_t_tir",
                  "fusilier_bazooka_tirlod0": "hr_t_bazooka_tir"}
        bottom = {"stand": "hr_b_stand", "walk": "hr_b_walk", "run": "hr_b_run"}
        clips = {n: n.upper() for n in ("hr_b_run", "hr_b_stand", "hr_b_walk", "hr_ride", "hr_t_bazooka_tir",
                                         "hr_t_stand", "hr_t_tir")}
        rows = hs._animation_rows("rifle", listings, top_of, bottom, clips)
        self.assertEqual([r[0] for r in rows], ["hr_t_stand", "hr_b_stand", "hr_b_run", "hr_b_walk", "hr_t_tir",
                                                "hr_ride", "hr_t_bazooka_tir"])
        self.assertEqual([r[1] for r in rows], [r[0].upper() for r in rows])
        stand = rows[0][2]
        self.assertEqual(stand, {"rusemod_clip": hs.CLIP_DIR + "hr_t_standlod0.baf",
                                 "rusemod_actions": ["t_course", "t_stand"],
                                 "rusemod_figures": {"GfxDescriptorFusilier": ["t_stand", "t_course"]},
                                 "rusemod_half": "top"})
        self.assertEqual(rows[5][2]["rusemod_figures"], {hs.RIDE_FIGURE: ["idle1"]})
        self.assertEqual(rows[5][2]["rusemod_half"], "whole")
        self.assertEqual((rows[6][2]["rusemod_actions"], rows[6][2]["rusemod_figures"]), ([], {}))   # not played
        self.assertEqual(rows[2][2]["rusemod_half"], "bottom")
        rows = hs._animation_rows("bazooka", listings, top_of, bottom, clips)
        self.assertEqual([r[0] for r in rows], ["hr_t_stand", "hr_t_bazooka_tir", "hr_b_stand", "hr_t_tir",
                                                "hr_b_run", "hr_b_walk", "hr_ride"])
        self.assertEqual(rows[0][2]["rusemod_figures"], {"GfxDescriptorBazooka": ["t_stand"]})
        self.assertEqual(rows[2][2]["rusemod_figures"], {hs.TOKEN: ["b_stand"]})
        self.assertEqual(rows[6][2]["rusemod_figures"], {})          # the ride drew the riflemen's model only

    def test_the_listings_from_a_game_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.sqlite"
            db = sqlite3.connect(path)
            db.executescript("CREATE TABLE object (id INTEGER, address TEXT, shadow INTEGER);"
                             "CREATE TABLE ref (src INTEGER, path TEXT, dst INTEGER);"
                             "CREATE TABLE value (object INTEGER, path TEXT, text TEXT);")
            n = 100
            for k, part in enumerate(hs.LISTED):
                db.execute("INSERT INTO object VALUES (?, ?, 0)", (k + 1, hs.UNIT + ":" + part))
                db.execute("INSERT INTO object VALUES (?, ?, 1)", (k + 50, hs.UNIT + ":" + part))   # a shadow copy
                for place, key, file in ((10, "t_tir", "Fusilier_TirLOD0"), (2, "t_stand", "Fusilier_standlod0"),
                                         (3, "b_stand", "Fusilier_standlod0")):
                    n += 1
                    db.execute("INSERT INTO ref VALUES (?, ?, ?)", (k + 1, f"ResourceAnimation[{place}].v", n))
                    db.execute("INSERT INTO value VALUES (?, ?, ?)", (k + 1, f"ResourceAnimation[{place}].k", key))
                    db.execute("INSERT INTO value VALUES (?, 'FileName', ?)",
                               (n, f"WW2\\Res3D\\Units\\Common\\{file}.Ase2NdfBin"))
            db.commit()
            db.close()
            got = hs._listings_in_index(path)
            self.assertEqual(got, {p: [("t_stand", "fusilier_standlod0"), ("b_stand", "fusilier_standlod0"),
                                       ("t_tir", "fusilier_tirlod0")] for p in hs.LISTED})   # by place: 2, 3, 10
            db = sqlite3.connect(path)
            db.execute("DELETE FROM object WHERE address = ? AND shadow = 0", (hs.UNIT + ":" + hs.TOKEN,))
            db.commit()
            db.close()
            self.assertIsNone(hs._listings_in_index(path))      # (then the game's unit data is read instead)
            self.assertIsNone(hs._listings_in_index(Path(tmp) / "nothing.sqlite"))

    def test_a_folder_that_isn_t_a_game_is_refused_in_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(hs.HorseSquadError, "isn't a R.U.S.E. game folder"):
                hs.horse_squad_glbs(Path(tmp) / "not-a-game", Path(tmp) / "out", say=lambda s: None)
            self.assertFalse((Path(tmp) / "out").exists())


# --- a made-up file with the Horse Squad's bones, for the horse's fall ---
LEG_BONES = sorted(hs._legs(0, 0, 0, 0, 0, 0, 0))


def qm(q) -> np.ndarray:
    return hs._quat_m(q)


def made_up_glb() -> bytes:
    """Nodes: a holder; the horse's hips, pelvis, spine and mid-back bone; the rider's root on it; the 13 bones the
    fall bends. Animations: the horse standing (its hips' place and a turn of the mid-back bone at its first frame), a
    rider's death (his root moving and turning over 1 s, three keys) and another animation of his."""
    g = _Glb()
    nodes = [{"name": "holder", "children": [1]},
             {"name": "horse bip01", "translation": [0.0, 1.4, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": [2]},
             {"name": "horse pelvis", "translation": [0.1, 0.0, 0.0], "children": [3]},
             {"name": "horse spine", "translation": [0.2, 0.05, 0.0], "rotation": list(turn_z(11.5)), "children": [4]},
             {"name": "horse spine1", "translation": [0.25, 0.0, 0.0], "children": [5]},
             {"name": "bip01", "translation": [-0.2, 0.7, 0.1], "rotation": [0.0, 0.0, 0.0, 1.0]}]
    for k, name in enumerate(LEG_BONES):
        nodes[1 if "thigh" in name or "tail" in name else 3].setdefault("children", []).append(len(nodes))
        nodes.append({"name": name, "translation": [0.05 * (k % 3), -0.3, 0.1 * (k % 2)],
                      "rotation": [0.0, math.sin(0.1 * k), 0.0, math.cos(0.1 * k)]})
    g.doc["nodes"] = nodes

    def channel(anim, node, path, times, values):
        tin = g.accessor([float(t) for t in times], "SCALAR", FLOAT, target=None)
        g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
        tout = g.accessor([tuple(map(float, v)) for v in values], "VEC4" if path == "rotation" else "VEC3", FLOAT,
                          target=None)
        anim["samplers"].append({"input": tin, "output": tout, "interpolation": "LINEAR"})
        anim["channels"].append({"sampler": len(anim["samplers"]) - 1, "target": {"node": node, "path": path}})
    stand = {"name": "hr_b_stand", "samplers": [], "channels": []}
    channel(stand, 1, "translation", [0.0, 1.0], [(0.0, 1.5, 0.0), (0.0, 1.55, 0.0)])
    channel(stand, 4, "rotation", [0.0, 1.0], [turn_z(5.7), (0.0, 0.0, 0.0, 1.0)])
    death = {"name": "hr_t_mort_balle", "samplers": [], "channels": []}
    channel(death, 5, "translation", [0.0, 0.5, 1.0], [(-0.2, 0.7, 0.1), (-0.5, 0.6, 0.1), (-1.0, 0.0, 0.2)])
    channel(death, 5, "rotation", [0.0, 0.5, 1.0], [turn_z(0), turn_z(45), turn_z(90)])
    other = {"name": "hr_t_stand", "samplers": [], "channels": []}
    channel(other, 5, "translation", [0.0, 1.0], [(-0.2, 0.7, 0.1), (-0.2, 0.7, 0.1)])
    g.doc["animations"] = [stand, death, other]
    g.doc["scenes"] = [{"nodes": [0]}]
    return g.to_bytes()


def glb_parts(raw: bytes) -> tuple:
    n = struct.unpack_from("<I", raw, 12)[0]
    bl = struct.unpack_from("<I", raw, 20 + n)[0]
    return json.loads(raw[20:20 + n]), raw[20 + n + 8:20 + n + 8 + bl]


def read(doc, binary, i) -> np.ndarray:
    a = doc["accessors"][i]
    v = doc["bufferViews"][a["bufferView"]]
    nc = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    at_ = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.frombuffer(binary, "<f4", a["count"] * nc, at_).reshape(-1, nc)


def at(doc, binary, anim, node, path, t):
    """The animation's value of a node's channel at time t (straight lines between keys), or None."""
    for c in anim["channels"]:
        if c["target"] == {"node": node, "path": path}:
            s = anim["samplers"][c["sampler"]]
            ts, vs = read(doc, binary, s["input"])[:, 0], read(doc, binary, s["output"]).astype(float)
            if t <= ts[0]:
                return vs[0]
            if t >= ts[-1]:
                return vs[-1]
            i = int(np.searchsorted(ts, t)) - 1
            u = (t - ts[i]) / (ts[i + 1] - ts[i])
            a, b = vs[i], vs[i + 1]
            if path == "rotation" and np.dot(a, b) < 0:
                b = -b
            v = a + (b - a) * u
            return v / np.linalg.norm(v) if path == "rotation" else v
    return None


def world_of(doc, binary, pose: dict, node: int) -> np.ndarray:
    """A node's 4 x 4 in the file at a pose ({(node, path): value}, else its stand pose... else its rest)."""
    parent = {c: i for i, n in enumerate(doc["nodes"]) for c in n.get("children", [])}
    m = np.eye(4)
    chain = []
    k = node
    while k is not None:
        chain.append(k)
        k = parent.get(k)
    for k in reversed(chain):
        n = doc["nodes"][k]
        t = pose.get((k, "translation"), n.get("translation", [0, 0, 0]))
        r = pose.get((k, "rotation"), n.get("rotation", [0, 0, 0, 1]))
        local = np.eye(4)
        local[:3, :3], local[:3, 3] = qm(r), t
        m = m @ local
    return m


class TheHorseFalls(unittest.TestCase):
    def setUp(self):
        self.raw = made_up_glb()
        self.out = hs._with_death(self.raw)
        self.doc, self.binary = glb_parts(self.out)
        self.before, self.old_binary = glb_parts(self.raw)

    def test_the_fall_added_and_every_byte_before_kept(self):
        names = [a["name"] for a in self.doc["animations"]]
        self.assertEqual(names, ["hr_b_stand", "hr_t_mort_balle", "hr_t_stand", hs.DEATH])
        self.assertTrue(self.binary.startswith(self.old_binary))
        self.assertEqual(self.doc["animations"][2], self.before["animations"][2])   # his other animations as they were
        fall = self.doc["animations"][3]
        bent = sorted(self.doc["nodes"][c["target"]["node"]]["name"] for c in fall["channels"]
                      if c["target"]["path"] == "rotation")
        self.assertEqual(bent, sorted(LEG_BONES + ["horse bip01"]))
        times = read(self.doc, self.binary, fall["samplers"][0]["input"])[:, 0]
        self.assertEqual(len(times), hs.DEATH_FRAMES)
        self.assertAlmostEqual(float(times[-1]), 2.0, places=6)
        hips = at(self.doc, self.binary, fall, 1, "translation", 2.0)
        self.assertAlmostEqual(float(hips[1]), 0.34, places=5)                   # lying: the hips down
        self.assertAlmostEqual(float(at(self.doc, self.binary, fall, 1, "translation", 0.0)[1]), 1.5, places=5)
        roll = at(self.doc, self.binary, fall, 1, "rotation", 2.0)                # rolled 88 degrees over
        self.assertAlmostEqual(math.degrees(2 * math.atan2(np.linalg.norm(roll[:3]), roll[3])), 88.0, places=3)

    def test_the_rider_falls_in_the_world_as_over_the_standing_horse(self):
        fall, death = self.doc["animations"][3], self.doc["animations"][1]
        old = self.before["animations"][1]
        stand = self.before["animations"][0]
        standing = {(c["target"]["node"], c["target"]["path"]): at(self.before, self.old_binary, stand,
                                                                   c["target"]["node"], c["target"]["path"], 0.0)
                    for c in stand["channels"]}
        self.assertEqual(len(read(self.doc, self.binary, death["samplers"][death["channels"][0]["sampler"]]["input"])),
                         31)                                                     # 1 s at 30 a second
        for f in range(0, 31, 3):
            t = f / 30
            then = dict(standing)     # (the fall starts from the horse's standing pose, as the file's own stand)
            then[(5, "translation")] = at(self.before, self.old_binary, old, 5, "translation", t)
            then[(5, "rotation")] = at(self.before, self.old_binary, old, 5, "rotation", t)
            now = dict(standing)
            now.update({(c["target"]["node"], c["target"]["path"]): at(self.doc, self.binary, fall, c["target"]["node"],
                                                                       c["target"]["path"], t)
                        for c in fall["channels"]})
            now[(5, "translation")] = at(self.doc, self.binary, death, 5, "translation", t)
            now[(5, "rotation")] = at(self.doc, self.binary, death, 5, "rotation", t)
            np.testing.assert_allclose(world_of(self.doc, self.binary, now, 5),
                                       world_of(self.before, self.old_binary, then, 5), atol=2e-5, err_msg=f"frame {f}")

    def test_a_file_with_the_fall_already_or_no_standing_horse_is_refused(self):
        with self.assertRaisesRegex(hs.HorseSquadError, "already"):
            hs._with_death(self.out)
        doc, binary = glb_parts(self.raw)
        doc["animations"][0]["name"] = "hr_b_idle"
        text = json.dumps(doc, separators=(",", ":")).encode()
        text += b" " * (-len(text) % 4)
        raw = (struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(binary))
               + struct.pack("<II", len(text), 0x4E4F534A) + text
               + struct.pack("<II", len(binary), 0x004E4942) + binary)
        with self.assertRaisesRegex(hs.HorseSquadError, "standing"):
            hs._with_death(raw)


# --- the game's own (RUSE_GAME), and the files the game test passed with (RUSE_HORSE_FIXES3) ---
@unittest.skipUnless(GAME is not None and GAME.is_dir(), "RUSE_GAME names no game folder")
class FromTheGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.files = hs.horse_squad_glbs(GAME, Path(cls.tmp.name) / "one", index=INDEX, say=lambda s: None)
        cls.raw = {k: v.read_bytes() for k, v in cls.files.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_two_files_on_62_bones_with_25_animations_the_studio_reads(self):
        from rusemod import rig
        self.assertEqual({k: v.name for k, v in self.files.items()}, hs.FILES)
        self.assertEqual(sorted(p.name for p in (Path(self.tmp.name) / "one").iterdir()), sorted(hs.FILES.values()))
        names = None
        for variant, path in self.files.items():
            r = rig.read_rig(path)
            self.assertEqual(len(r.joints), 62, variant)
            self.assertEqual(r.names[:2] + r.names[32:34], ["horse bip01", "horse pelvis", "bip01", "bip01 pelvis"])
            got = sorted(a.name for a in r.animations)
            self.assertEqual(len(got), 25, variant)
            self.assertIn(hs.DEATH, got)
            self.assertIn(hs.RIDE, got)
            names = names or got
            self.assertEqual(got, names)                       # the same animations in both
            doc, _bin = glb_parts(self.raw[variant])
            self.assertEqual(doc["asset"]["extras"]["rusemod_model"], hs.NEW[variant])
        self.assertNotEqual(self.raw["rifle"], self.raw["bazooka"])

    def test_the_same_game_gives_the_same_bytes(self):
        again = hs.horse_squad_glbs(GAME, Path(self.tmp.name) / "two", index=None, say=lambda s: None)
        for variant, path in again.items():
            self.assertEqual(path.read_bytes(), self.raw[variant], variant)

    @unittest.skipUnless(INDEX is not None and INDEX.is_file(), "RUSE_GAME_INDEX names no game index")
    def test_the_listings_from_the_index_and_from_the_game_alike(self):
        from_index = hs._listings_in_index(INDEX)
        self.assertIsNotNone(from_index)
        self.assertEqual(from_index, hs._listings_in_game(GAME))
        self.assertEqual({p: len(v) for p, v in from_index.items()}, {"GfxDescriptorFusilier": 70,
                                                                     "GfxDescriptorBazooka": 86, hs.TOKEN: 90})

    @unittest.skipUnless(FIXES3 is not None and FIXES3.is_dir(), "RUSE_HORSE_FIXES3 names no folder")
    def test_byte_for_byte_the_files_the_game_test_passed_with(self):
        for variant in hs.NEW:
            self.assertEqual(self.raw[variant], (FIXES3 / f"horse-squad-{variant}-death.glb").read_bytes(), variant)


if __name__ == "__main__":
    unittest.main()
