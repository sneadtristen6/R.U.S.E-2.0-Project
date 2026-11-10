"""A model on bones of its own (rusemod.rig reads a .glb's skeleton and animations; rusemod.baf writes its record and
clips; rusemod.unitmodel writes its draws and record into the packs and makes its two halves).

Made-up skeletons and animations always run. With RUSE_GAME naming a game folder, the game's own scenery horse and US
rifleman go out to a .glb (their record, clips and draws, laid out as an export writes them) and back through the
importer and the writer: each record byte for byte, or every difference listed with its size; each clip's keys equal
within what the clip's numbers hold; each draw's points, bones and weights as the game's. With RUSE_HR_OUT naming the
2026-11-09 horse test's output folder (packs/, clips/, manifest.json), its combined horse-and-rider model the same."""
import base64
import math
import os
import struct
import tempfile
import unittest
from pathlib import Path

from rusemod import baf, modelin, rig, unitmodel
from rusemod.gltf import FLOAT, UINT, USHORT, _Glb, _point
from rusemod.modelin import ModelError, OWN_SKELETON
from rusemod.unitpacks import MeshPack

GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
HR_OUT = Path(os.environ["RUSE_HR_OUT"]) if os.environ.get("RUSE_HR_OUT") else None
B = "\\"
HORSE = B.join(["ww2", "res3d", "decors", "animaux", "animaux_1", "horse_standlod0.ase2ndfbin"])
SOLDIER = B.join(["ww2", "res3d", "units", "us", "infanterie", "us_soldier_modellod0.ase2ndfbin"])
BAZOOKA = B.join(["ww2", "res3d", "units", "us", "infanterie", "us_soldier_bazooka_modellod0.ase2ndfbin"])
HORSE_CLIPS = ("horse_standlod0.baf", "horse_walklod0.baf", "horse_runlod0.baf")


# --- a .glb of a skeleton, as an export lays one out ---
def make_glb(record: bytes, clips=(), parts=(), kept: bool = False, holder=None) -> bytes:
    """A .glb of the skeleton `record`: each bone a node at its rest pose from its parent (the record's from-parent set),
    the skin's inverse bind matrices its model -> bone set (each in glTF's axes, as rusemod.gltf writes them), under one
    node (`holder`: its (move, turn, size) in glTF's own, or none); `clips` [(name, baf.Clip)] each an animation with
    every key of each track as the clip has it (LINEAR); `parts` [(positions, skin [(bone, weight 0..255)] a point,
    triangles)] in the game's axes, meshes skinned to it; `kept`: the record in the skin's extras."""
    sk = baf.skeleton(record)
    g = _Glb()
    for k, (positions, skin, triangles) in enumerate(parts):
        js = [tuple(b for b, _w in v) + (0,) * (4 - len(v)) for v in skin]
        ws = [tuple(w / 255.0 for _b, w in v) + (0.0,) * (4 - len(v)) for v in skin]
        tri = [i for a, b, c in triangles for i in (a, c, b)]     # (the mirror turns each triangle round)
        prim = {"attributes": {"POSITION": g.accessor([_point(*p) for p in positions], "VEC3", FLOAT, minmax=True),
                               "JOINTS_0": g.accessor(js, "VEC4", USHORT), "WEIGHTS_0": g.accessor(ws, "VEC4", FLOAT)},
                "indices": g.accessor(tri, "SCALAR", UINT if len(positions) > 65535 else USHORT, 34963)}
        g.doc["meshes"].append({"name": f"part{k}", "primitives": [prim]})
        g.doc["nodes"].append({"name": f"part{k}", "mesh": k, "skin": 0})
    meshes = list(range(len(g.doc["nodes"])))
    first = len(g.doc["nodes"])
    for b, name in enumerate(sk["names"]):
        move, turn, size, _off = rig.decompose(sk["local"][b])
        g.doc["nodes"].append({"name": name, "translation": list(rig.move_out(move)), "rotation": list(rig.turn_out(turn)),
                               "scale": list(rig.size_out(size))})
    for b, p in enumerate(sk["parents"]):
        if p >= 0:
            g.doc["nodes"][first + p].setdefault("children", []).append(first + b)
    top = len(g.doc["nodes"])
    g.doc["nodes"].append({"name": "Armature", "children": [first + b for b, p in enumerate(sk["parents"]) if p < 0]})
    if holder:
        g.doc["nodes"][top].update(translation=list(holder[0]), rotation=list(holder[1]), scale=list(holder[2]))
    ibm = [v for b in range(sk["bones"]) for v in rig.matrix_out(sk["bind"][b])]
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                               "count": sk["bones"], "type": "MAT4"})
    skin = {"joints": list(range(first, first + sk["bones"])), "inverseBindMatrices": len(g.doc["accessors"]) - 1,
            "skeleton": top}
    if kept:
        skin["extras"] = {rig.SKELETON_EXTRA: rig.skeleton_extra(record)}
    g.doc["skins"] = [skin]
    anims = []
    for name, clip in clips:
        csk = baf.skeleton(clip.skeleton)
        samplers, channels = [], []
        for u, track in enumerate(clip.tracks):
            node = first + csk["index"][u]
            for path, keys in (("translation", track.T), ("rotation", track.R), ("scale", track.S)):
                if len(keys) == 1:      # one key holds all along: at the start and the end, as rusemod.animglb writes it
                    keys = [keys[0], (baf.LAST_TIME,) + tuple(keys[0][1:])]
                times = [k[0] / baf.LAST_TIME * clip.duration for k in keys]
                if path == "translation":
                    vals = [rig.move_out(k[1:4]) for k in keys]
                elif path == "rotation":
                    vals = [rig.turn_out(baf.unpack_quat(k[1:5])) for k in keys]
                else:
                    vals = [rig.size_out(k[1:4]) for k in keys]
                tin = g.accessor(times, "SCALAR", FLOAT, target=None)
                g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
                tout = g.accessor(vals, "VEC4" if path == "rotation" else "VEC3", FLOAT, target=None)
                samplers.append({"input": tin, "output": tout, "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
        anims.append({"name": name, "samplers": samplers, "channels": channels})
    if anims:
        g.doc["animations"] = anims
    g.doc["scenes"] = [{"nodes": meshes + [top]}]
    g.doc["scene"] = 0
    return g.to_bytes()


def rig_of_bytes(data: bytes) -> rig.Rig:
    doc, binary = modelin.glb_document(data)
    return rig.rig_of(doc, binary, "test.glb")


# --- comparing what came back ---
def record_differences(mine: bytes, theirs: bytes) -> list:
    """Every way two records differ: names, parents, track order, and each matrix set's numbers (how many differ and
    by how much at most); [] for the same bytes."""
    if mine == theirs:
        return []
    a, b = baf.skeleton(mine), baf.skeleton(theirs)
    out = []
    for key in ("names", "parents", "index"):
        if a[key] != b[key]:
            out.append(f"{key} differ")
    if a["bones"] == b["bones"]:
        for key in ("bind", "local", "world"):
            diffs = [abs(x - y) for m, n in zip(a[key], b[key]) for x, y in zip(m, n) if x != y]
            if diffs:
                out.append(f"{key}: {len(diffs)} of {12 * a['bones']} numbers differ, at most {max(diffs):.3g}")
    if not out:
        out.append("the same numbers, other bytes")
    return out


def _ulps(x: float, y: float) -> int:
    a, b = struct.unpack("<i", struct.pack("<f", x))[0], struct.unpack("<i", struct.pack("<f", y))[0]
    return abs(a - b)


def clip_differences(mine: bytes, theirs: bytes) -> dict:
    """How a clip made again compares with the one it came from, track by bone name: {"frames", "length", "tracks",
    "keys": tracks whose key counts differ, "times": the most a key's time differs (in its 1/8,388,607 steps), "moves":
    the most a move or size differs in floats (ulps), "turns": the most a turn's x, y or z differs in packing steps,
    "poses": the most a bone's move, turn or size differs over every frame (sampled as the game does)}."""
    a, b = baf.parse(mine), baf.parse(theirs)
    sa, sb = baf.skeleton(a.skeleton), baf.skeleton(b.skeleton)
    by_a = {sa["names"][bone]: a.tracks[u] for u, bone in enumerate(sa["index"])}
    by_b = {sb["names"][bone]: b.tracks[u] for u, bone in enumerate(sb["index"])}
    out = {"frames": (a.frames, b.frames), "length": (a.duration, b.duration), "tracks": (a.bones, b.bones),
           "missing": sorted(set(by_b) - set(by_a)), "keys": [], "times": 0, "moves": 0, "turns": 0.0,
           "poses": [0.0, 0.0, 0.0]}
    for name, tb in by_b.items():
        ta = by_a.get(name)
        if ta is None:
            continue
        for kind, ka, kb in (("T", ta.T, tb.T), ("S", ta.S, tb.S), ("R", ta.R, tb.R)):
            if len(ka) != len(kb):
                out["keys"].append((name, kind, len(ka), len(kb)))
                continue
            for x, y in zip(ka, kb):
                out["times"] = max(out["times"], abs(x[0] - y[0]) if len(ka) > 2 else 0)
                if kind == "R":
                    p, q = baf.unpack_quat(x[1:5]), baf.unpack_quat(y[1:5])
                    if sum(i * j for i, j in zip(p, q)) < 0:
                        q = tuple(-v for v in q)
                    out["turns"] = max(out["turns"], max(abs(i - j) for i, j in zip(p[:3], q[:3])) / baf.SCALE)
                else:
                    out["moves"] = max(out["moves"], max(_ulps(i, j) for i, j in zip(x[1:4], y[1:4])))
        for k in range(b.frames):
            f = k / (b.frames - 1) if b.frames > 1 else 0.0
            (ma, ra, za), (mb, rb, zb) = baf.sample(ta, f), baf.sample(tb, f)
            if sum(i * j for i, j in zip(ra, rb)) < 0:
                rb = tuple(-v for v in rb)
            out["poses"][0] = max(out["poses"][0], max(abs(i - j) for i, j in zip(ma, mb)))
            out["poses"][1] = max(out["poses"][1], max(abs(i - j) for i, j in zip(ra, rb)))
            out["poses"][2] = max(out["poses"][2], max(abs(i - j) for i, j in zip(za, zb)))
    return out


# --- made-up skeletons ---
def turn_about(axis: str, degrees: float) -> tuple:
    return baf.axis_angle(axis, degrees)


def little_glb(animations=None, names=("Hips", "Spine", "Head"), holder=None, kept=None, extra_mesh=False) -> bytes:
    """Three bones in glTF's own axes (y up, metres): Hips 1 up, Spine 0.5 above it turned a quarter about x, Head 0.25
    above that; one triangle skinned to them; inverse bind matrices from the rest; `animations` [(name, [(node, path,
    times, values, interpolation)])] with nodes numbered: 0 the mesh, 1 Hips, 2 Spine, 3 Head, 4 the armature."""
    g = _Glb()
    pos = [(0.0, 1.0, 0.0), (0.1, 1.5, 0.0), (0.0, 1.75, 0.1)]
    js = [(0, 0, 0, 0), (1, 0, 0, 0), (2, 1, 0, 0)]
    ws = [(1.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.75, 0.25, 0.0, 0.0)]
    prim = {"attributes": {"POSITION": g.accessor(pos, "VEC3", FLOAT, minmax=True), "JOINTS_0": g.accessor(js, "VEC4", USHORT),
                           "WEIGHTS_0": g.accessor(ws, "VEC4", FLOAT)}, "indices": g.accessor([0, 1, 2], "SCALAR", USHORT, 34963)}
    g.doc["meshes"].append({"name": "body", "primitives": [prim]})
    q = turn_about("x", 90.0)
    g.doc["nodes"] = [{"name": "body", "mesh": 0, "skin": 0},
                      {"name": names[0], "translation": [0.0, 1.0, 0.0], "children": [2]},
                      {"name": names[1], "translation": [0.0, 0.5, 0.0], "rotation": list(q), "children": [3]},
                      {"name": names[2], "translation": [0.0, 0.25, 0.0]},
                      {"name": "Armature", "children": [1], **(holder or {})}]
    # each bone's rest in the file's own axes, for its inverse bind matrix (the armature node's move counts)
    m_hips = _m4(translation=(0.0, 1.0, 0.0))
    m_spine = _mul4(m_hips, _m4(translation=(0.0, 0.5, 0.0), rotation=q))
    m_head = _mul4(m_spine, _m4(translation=(0.0, 0.25, 0.0)))
    if holder:
        h = _m4(holder.get("translation", (0, 0, 0)), holder.get("rotation", (0, 0, 0, 1)), holder.get("scale", (1, 1, 1)))
        m_hips, m_spine, m_head = _mul4(h, m_hips), _mul4(h, m_spine), _mul4(h, m_head)
    ibm = [v for m in (m_hips, m_spine, m_head) for v in _inv4(m)]
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                               "count": 3, "type": "MAT4"})
    g.doc["skins"] = [{"joints": [1, 2, 3], "inverseBindMatrices": len(g.doc["accessors"]) - 1, "skeleton": 4}]
    if kept is not None:
        g.doc["skins"][0]["extras"] = {rig.SKELETON_EXTRA: kept}
    if extra_mesh:
        g.doc["meshes"].append({"name": "loose", "primitives": [{"attributes": {"POSITION": prim["attributes"]["POSITION"]},
                                                                 "indices": prim["indices"]}]})
        g.doc["nodes"].append({"name": "loose", "mesh": 1})
    anims = []
    for name, chans in animations or []:
        samplers, channels = [], []
        for node, path, times, values, how in chans:
            tin = g.accessor(list(times), "SCALAR", FLOAT, target=None)
            g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
            tout = g.accessor([tuple(v) for v in values], "VEC4" if path == "rotation" else "VEC3", FLOAT, target=None)
            samplers.append({"input": tin, "output": tout, "interpolation": how})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
        anims.append({"name": name, "samplers": samplers, "channels": channels})
    if anims:
        g.doc["animations"] = anims
    g.doc["scenes"] = [{"nodes": [0, 4] + ([5] if extra_mesh else [])}]
    g.doc["scene"] = 0
    return g.to_bytes()


def _m4(translation=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0, 1.0), scale=(1.0, 1.0, 1.0)) -> list:
    return modelin._node_matrix({"translation": list(translation), "rotation": list(rotation), "scale": list(scale)})


def _mul4(a, b):
    return modelin._matmul(a, b)


def _inv4(m: list) -> list:
    """A column-major 4 x 4 affine's inverse (column-major)."""
    rows = tuple(v for i in range(3) for v in (m[i], m[4 + i], m[8 + i], m[12 + i]))
    inv = rig.inverse(rows)
    out = [0.0] * 16
    for i in range(3):
        for j in range(4):
            out[j * 4 + i] = inv[i * 4 + j]
    out[15] = 1.0
    return out


def close(a, b, places=5) -> bool:
    return all(abs(x - y) < 10 ** -places for x, y in zip(a, b))


class Records(unittest.TestCase):
    """A skeleton record written as the game keeps one."""

    def test_written_back_byte_for_byte(self):
        from test_anim import skeleton_part
        part = skeleton_part(["root", "a", "b", "c"], [-1, 0, 0, 1])
        sk = baf.skeleton(part)
        self.assertEqual(baf.skeleton_bytes(sk["names"], sk["parents"], sk["bind"], sk["local"], sk["world"], sk["index"]), part)

    def test_the_track_order_is_depth_by_depth(self):
        self.assertEqual(baf.depth_order([-1, 0, 0, 2, -1, 4, 1]), [0, 4, 1, 2, 5, 3, 6])
        rec = baf.skeleton_bytes(["a", "b", "c"], [-1, 0, 1], [rig.IDENTITY] * 3, [rig.IDENTITY] * 3, [rig.IDENTITY] * 3)
        self.assertEqual(baf.skeleton(rec)["index"], [0, 1, 2])
        with self.assertRaises(baf.ClipError):
            baf.depth_order([1, 0])          # a loop
        with self.assertRaises(baf.ClipError):
            baf.skeleton_bytes(["a"], [-1], [rig.IDENTITY], [rig.IDENTITY], [rig.IDENTITY], [1])


class Reading(unittest.TestCase):
    """A .glb's own skeleton and animations, in the game's axes and units."""

    def test_bones_their_parents_and_rest(self):
        r = rig_of_bytes(little_glb())
        self.assertEqual(r.names, ["hips", "spine", "head"])          # lower case, as the game's skeletons
        self.assertEqual([j.parent for j in r.joints], [-1, 0, 1])
        self.assertTrue(any("lower case" in n for n in r.notes))
        hips, spine, head = r.joints
        self.assertTrue(close(hips.world, (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 100.0)))      # 1 m up: game z 100
        self.assertTrue(close(spine.local[3::4], (0.0, 0.0, 50.0)))
        # a quarter turn about glTF's x is a quarter turn the other way about the game's x (the mirror)
        self.assertTrue(close(spine.local, rig.compose((0.0, 0.0, 50.0), turn_about("x", -90.0), (1, 1, 1))))
        self.assertTrue(close(head.world[3::4], (0.0, 25.0, 150.0)))
        for j in r.joints:     # bound at rest
            self.assertLess(rig.near(rig.mul(j.bind, j.world), rig.IDENTITY), 1.0)
        rec = r.record()
        sk = baf.skeleton(rec)
        self.assertEqual((sk["names"], sk["parents"], sk["index"]), (r.names, [-1, 0, 1], [0, 1, 2]))

    def test_a_node_above_the_bones_counts(self):
        holder = {"translation": [2.0, 0.0, 0.0], "rotation": list(turn_about("y", 90.0))}
        r = rig_of_bytes(little_glb(holder=holder))
        hips = r.joints[0]
        self.assertTrue(close(hips.local, hips.world))                 # a root's rest from its parent: in the model
        self.assertTrue(close(hips.world[3::4], (200.0, 0.0, 100.0)))
        for j in r.joints:
            self.assertLess(rig.near(rig.mul(j.bind, j.world), rig.IDENTITY), 1.0)

    def test_what_it_refuses(self):
        g = _Glb()
        g.doc["meshes"].append({"primitives": [{"attributes": {"POSITION": g.accessor([(0, 0, 0)] * 3, "VEC3", FLOAT, minmax=True)}}]})
        g.doc["nodes"] = [{"mesh": 0}]
        g.doc["scenes"] = [{"nodes": [0]}]
        with self.assertRaises(ModelError):                              # no skin
            rig_of_bytes(g.to_bytes())
        with self.assertRaises(ModelError):                              # two bones of one name, not counting capitals
            rig_of_bytes(little_glb(names=("Hips", "hips", "Head")))
        with self.assertRaises(ModelError):                              # a name a record can't hold
            rig_of_bytes(little_glb(names=("Hips", "背骨", "Head")))

    def test_the_three_ways_of_playing(self):
        q0, q1 = turn_about("x", 0.0), turn_about("x", 90.0)
        anims = [("Walk", [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, 2.0)], "LINEAR")]),
                 ("Nod", [(2, "rotation", [0.0, 0.5, 1.0], [q1, q0, q1], "STEP")]),
                 ("Bob", [(3, "translation", [0.0, 1.0], [(0, 0, 0), (0.0, 0.25, 0.0), (0.0, 2.0, 0.0),
                                                          (0, 0, 0), (0.0, 0.75, 0.0), (0, 0, 0)], "CUBICSPLINE")])]
        r = rig_of_bytes(little_glb(anims))
        self.assertEqual([a.name for a in r.animations], ["Walk", "Nod", "Bob"])
        walk, nod, bob = r.animations
        self.assertEqual(r.frames(walk), (1.0, 31))
        length, poses = r.poses(walk)
        moves = poses[0][0]
        self.assertTrue(close(moves[15], (0.0, 100.0, 100.0), 4))      # halfway: 1 m along glTF's z, the game's y
        self.assertTrue(close(moves[0], (0.0, 0.0, 100.0)))
        self.assertTrue(close(poses[1][0][7], (0.0, 0.0, 50.0)))         # Spine not moved: its rest
        _l, poses = r.poses(nod)
        self.assertTrue(close(poses[1][1][14], rig.turn_in(q1)))        # STEP holds the first key until the second
        self.assertTrue(close(poses[1][1][15], rig.turn_in(q0)))
        _l, poses = r.poses(bob)
        # halfway from 0.25 (leaving at 2 a second) to 0.75 (arriving still): 0.5 + 0.125 x (2 - 0) = 0.75, not the
        # straight line's 0.5
        self.assertTrue(close(poses[2][0][15], (0.0, 0.0, 75.0), 4))
        self.assertTrue(close(poses[2][0][30], (0.0, 0.0, 75.0), 4))    # the last key

    def test_a_record_the_file_carries_is_kept_while_its_bones_match(self):
        r = rig_of_bytes(little_glb())
        worked = r.record()
        sk = baf.skeleton(worked)
        # the same bones in another track order: kept as the file has it, not worked out again
        other = baf.skeleton_bytes(sk["names"], sk["parents"], sk["bind"], sk["local"], sk["world"], [0, 2, 1])
        self.assertNotEqual(other, worked)
        kept = rig_of_bytes(little_glb(kept=rig.skeleton_extra(other)))
        self.assertEqual(kept.record(), other)
        moved = list(sk["world"][2])
        moved[11] += 5.0                                                   # Head 5 higher in the record than in the file
        wrong = baf.skeleton_bytes(sk["names"], sk["parents"], sk["bind"], sk["local"], sk["world"][:2] + [tuple(moved)])
        changed = rig_of_bytes(little_glb(kept=rig.skeleton_extra(wrong)))
        self.assertEqual(changed.record(), worked)
        self.assertTrue(any("worked out again" in n for n in changed.notes))


class Clips(unittest.TestCase):
    """A clip from a pose at every frame, as the game's are."""

    def poses(self, frames=31):
        still = ([(0.0, 0.0, 5.0)] * frames, [(0.0, 0.0, 0.0, 1.0)] * frames, [(1.0, 1.0, 1.0)] * frames)
        straight = ([(float(k), 0.0, 0.0) for k in range(frames)], [baf.axis_angle("z", 3.0 * k) for k in range(frames)],
                    [(1.0, 1.0, 1.0)] * frames)
        curved = ([(math.sin(k / 4.0), 0.0, 0.0) for k in range(frames)],
                  [tuple(-c for c in baf.axis_angle("y", 10.0 * k)) for k in range(frames)], [(1.0, 1.0, 1.0)] * frames)
        return [still, straight, curved]

    def record(self, n=3):
        return baf.skeleton_bytes([f"b{k}" for k in range(n)], [-1] + list(range(n - 1)), [rig.IDENTITY] * n,
                                  [rig.IDENTITY] * n, [rig.IDENTITY] * n)

    def test_keys_kept_only_where_needed(self):
        c = baf.from_frames(1.0, self.poses(), self.record())
        still, straight, curved = c.tracks
        self.assertEqual((len(still.T), len(still.R), len(still.S)), (1, 1, 1))       # still: one key holds
        self.assertEqual((len(straight.T), len(straight.R)), (2, 2))                    # a straight move, a steady turn
        self.assertEqual(len(curved.T), 31)
        self.assertEqual([k[0] for k in straight.T], [0, baf.LAST_TIME])
        self.assertEqual([k[0] for k in curved.T][:3], [0, baf.time_of(1 / 30), baf.time_of(2 / 30)])
        raw = baf.build(c)
        self.assertEqual(baf.build(baf.parse(raw)), raw)
        for k in range(31):     # every frame comes back as it was
            f = k / 30
            self.assertTrue(close(baf.sample(curved, f)[0], (math.sin(k / 4.0), 0.0, 0.0), 6))

    def test_turns_on_one_side_as_the_game_keeps_them(self):
        c = baf.from_frames(1.0, self.poses(), self.record())
        turns = [baf.unpack_quat(k[1:5]) for k in c.tracks[2].R]
        self.assertGreaterEqual(turns[0][3], 0.0)                         # the first with w >= 0 (it was given < 0)
        for a, b in zip(turns, turns[1:]):
            self.assertGreaterEqual(sum(x * y for x, y in zip(a, b)), 0.0)

    def test_one_frame(self):
        r = rig_of_bytes(little_glb([("Pose", [(2, "rotation", [0.0], [turn_about("x", 45.0)], "LINEAR")])]))
        self.assertEqual(r.frames(r.animations[0]), (1.0, 1))
        clips, _notes = unitmodel.own_clips(r)
        c = baf.parse(clips["Pose"])
        self.assertEqual((c.frames, c.duration), (1, 1.0))                # as the game's one-frame clip

    def test_own_clips_are_on_the_model_s_record(self):
        anims = [("Walk", [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, 2.0)], "LINEAR")]),
                 ("Walk", [(1, "translation", [0.0, 0.5], [(0.0, 1.0, 0.0), (0.0, 1.0, 1.0)], "LINEAR")])]
        r = rig_of_bytes(little_glb(anims))
        clips, notes = unitmodel.own_clips(r)
        self.assertEqual(sorted(clips), ["Walk", "Walk 2"])               # a name given twice, numbered
        c = baf.parse(clips["Walk"])
        self.assertEqual((c.skeleton, c.frames), (r.record(), 31))
        self.assertEqual(baf.parse(clips["Walk 2"]).frames, 16)
        with self.assertRaises(unitmodel.UnitModelError):
            unitmodel.own_clips(r, self.record())                          # another skeleton's record

    def test_past_64_bones_a_warning_never_a_refusal(self):
        n = 70
        rec = self.record(n)
        poses = [self.poses()[1]] * n
        with self.assertRaises(baf.ClipError):
            baf.build(baf.from_frames(1.0, poses, rec))                   # the game's own limit, as before
        self.assertEqual(baf.parse(baf.build(baf.from_frames(1.0, poses, rec), n)).bones, n)
        fake = rig.Rig([rig.Joint(f"b{k}", k - 1, k, rig.IDENTITY, rig.IDENTITY, rig.IDENTITY) for k in range(n)], [])
        record, notes = unitmodel.own_skeleton(fake)
        self.assertEqual(baf.skeleton(record)["bones"], n)
        self.assertTrue(any("70 bones" in m and "not tried in the game" in m for m in notes))


class Halves(unittest.TestCase):
    def test_split_at_a_bone(self):
        r = rig_of_bytes(little_glb())
        got = unitmodel.halves(r.record(), "Spine")
        self.assertEqual(got["split"], "spine")
        self.assertEqual(got["top"], {"MaskUnionCode": 65280, "AnimationSlot": 1, "Weights": {"spine": 1.0, "head": 1.0}})
        self.assertEqual(got["bottom"], {"MaskUnionCode": 255, "Weights": {"hips": 1.0}})
        self.assertTrue(unitmodel.halves(r.record(), "hips")["notes"])     # every bone in the top
        with self.assertRaises(unitmodel.UnitModelError):
            unitmodel.halves(r.record(), "tail")

    def test_whether_a_soldier_s_own_masks_fit(self):
        r = rig_of_bytes(little_glb())
        fits = unitmodel.game_masks_fit(r.record(), {"top": {"Spine": 1.0, "Head": 1.0}, "bottom": {"HIPS": 1.0}})
        self.assertEqual((fits["fit"], fits["left"]), (True, []))
        no = unitmodel.game_masks_fit(r.record(), {"top": {"Bip01 Spine": 1.0}, "bottom": {"hips": 0.0}})
        self.assertEqual((no["fit"], no["missing"], no["left"]), (False, {"top": ["Bip01 Spine"]}, ["hips", "spine", "head"]))


class Writing(unittest.TestCase):
    """Its draws on its own bones, its record in the skeleton packs, through the model's file and the kept models."""

    def prep(self, n_bones=3, spread=False):
        names = ["hips", "spine", "head"] if n_bones == 3 else [f"b{k}" for k in range(n_bones)]
        rec = baf.skeleton_bytes(names, [-1] + list(range(n_bones - 1)), [rig.IDENTITY] * n_bones,
                                 [rig.IDENTITY] * n_bones, [rig.IDENTITY] * n_bones)
        pts, skin, tris = [], [], []
        count = n_bones if spread else 3
        for k in range(count):
            pts += [(float(k), 0.0, 0.0), (float(k), 1.0, 0.0), (float(k), 0.0, 1.0)]
            skin += [[(names[k % n_bones], 255)], [(names[k % n_bones], 128), (names[(k + 1) % n_bones], 127)], [(names[0], 255)]]
            tris.append((3 * k, 3 * k + 1, 3 * k + 2))
        part = modelin.Part(modelin.RIGGED, -1, pts, [(0.0, 0.0, 1.0)] * len(pts), [(0.5, 0.5)] * len(pts), tris,
                            skin=skin, tracks=None, draw=None, static=False)
        report = {"rigged": True, OWN_SKELETON: {"bones": n_bones, "record": base64.b64encode(rec).decode("ascii")}}
        return modelin.Prepared([part], [], report), rec

    def test_its_draws_and_record_in_the_packs(self):
        from rusemod.spk import Spk
        from test_unitmodel import MESHES, SKELETON, SKELETONS, TANK, zz_win
        prep, rec = self.prep()
        w = unitmodel.write_unit_model(zz_win(), TANK, "beast", prep)
        new = "ww2\\res3d\\units\\ger\\tank\\beastlod0.ase2ndfbin"
        self.assertNotIn("record", w.report[OWN_SKELETON])
        skel = MeshPack.read(w.changed[SKELETONS])
        self.assertEqual(skel.skeletons[skel.items[new][2]], rec)          # its own record under its name
        self.assertEqual(skel.skeletons[skel.items[TANK][2]], SKELETON)    # the copied model's as it was
        spk = Spk(w.changed[MESHES])
        mats = spk.materials()
        first, count = spk.meshes[spk.items[new].mesh]
        self.assertEqual(count, 1)
        part = spk.part(first)
        self.assertEqual(mats[part.material]["skinning"], [0, 1, 2])      # the bones its points lean on, its own numbers
        self.assertEqual([tuple(b[:2]) for b in part.bones[:2]], [(0, 0), (0, 1)])
        old = Spk(bytes(zz_win().read(zz_win().entry(MESHES))))
        self.assertEqual(mats[spk.part(spk.meshes[spk.items[TANK].mesh][0]).material]["skinning"],
                         old.materials()[old.part(old.meshes[old.items[TANK].mesh][0]).material]["skinning"])

    def test_more_than_64_bones_in_one_part_is_drawn_in_several(self):
        from rusemod.spk import Spk
        from test_unitmodel import MESHES, SKELETONS, TANK, zz_win
        prep, rec = self.prep(n_bones=70, spread=True)
        w = unitmodel.write_unit_model(zz_win(), TANK, "crowd", prep)
        spk = Spk(w.changed[MESHES])
        mats = spk.materials()
        first, count = spk.meshes[spk.items["ww2\\res3d\\units\\ger\\tank\\crowdlod0.ase2ndfbin"].mesh]
        lists = [mats[spk.part(first + k).material]["skinning"] for k in range(count)]
        self.assertGreater(count, 1)
        self.assertTrue(all(len(x) <= 64 for x in lists))
        self.assertEqual(set().union(*lists), set(range(70)))
        self.assertEqual(sum(len(spk.part(first + k).indices) for k in range(count)), 3 * 70)
        skel = MeshPack.read(w.changed[SKELETONS])
        self.assertEqual(baf.skeleton(skel.skeletons[skel.items["ww2\\res3d\\units\\ger\\tank\\crowdlod0.ase2ndfbin"][2]])["bones"], 70)

    def test_the_model_s_file_keeps_its_skeleton(self):
        prep, rec = self.prep()
        with tempfile.TemporaryDirectory() as d:
            glb = Path(d, "m.glb")
            modelin.write_glb(prep, glb, "the model")
            back = unitmodel.read_mod_glb(glb)
            report = unitmodel.glb_report(glb)
            r = rig.read_rig(glb)
        self.assertNotIn("record", report[OWN_SKELETON])                   # in its skin's extras, not its report
        self.assertEqual(unitmodel.own_record(back.report), rec)
        self.assertEqual((r.names, [j.parent for j in r.joints]), (["hips", "spine", "head"], [-1, 0, 1]))
        self.assertEqual(back.parts[0].skin, prep.parts[0].skin)
        kept, _textures = unitmodel._kept_read(unitmodel._kept_bytes(back, []))
        self.assertEqual(unitmodel.own_record(kept.report), rec)            # a build's kept models keep it too
        stale = modelin.Prepared(kept.parts, kept.pictures, dict(kept.report, **{OWN_SKELETON: {"bones": 3}}))
        self.assertFalse(unitmodel._kept_has_all(stale))                    # kept by a Studio that didn't know it: read again
        self.assertTrue(unitmodel._kept_has_all(modelin.Prepared([], [], {"rigged": True})))
        with self.assertRaises(unitmodel.UnitModelError):
            unitmodel.own_record(stale.report)

    def test_a_file_whose_bones_were_moved_is_built_as_it_is_now(self):
        prep, rec = self.prep()
        with tempfile.TemporaryDirectory() as d:
            glb = Path(d, "m.glb")
            modelin.write_glb(prep, glb, "the model")
            doc, binary = modelin.glb_document(glb.read_bytes())
            head = next(n for n in doc["nodes"] if n.get("name") == "head")
            head["translation"] = [0.0, 0.0, 0.5]           # moved in Blender, the old record still in its extras
            g = _Glb()
            g.doc, g.bin = doc, bytearray(binary)
            glb.write_bytes(g.to_bytes())
            back = unitmodel.read_mod_glb(glb)
        got = baf.skeleton(unitmodel.own_record(back.report))
        self.assertNotEqual(unitmodel.own_record(back.report), rec)
        self.assertTrue(close(got["local"][2][3::4], (0.0, 50.0, 0.0)))
        self.assertTrue(any("worked out again" in n for n in back.report["notes"]))

    def test_import_model_takes_a_model_on_its_own_bones(self):
        from unittest import mock
        from test_unitmodel import TANK, zz_win
        anims = [("Walk", [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, 2.0)], "LINEAR")])]
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "beast.glb")
            src.write_bytes(little_glb(anims, extra_mesh=True))
            out = Path(d, "files", "models", "Beast.glb")
            arc = zz_win()
            with mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
                report = unitmodel.import_model(Path("game"), TANK, src, out, own_bones=True, move=[1, 0, 0])
            back = unitmodel.read_mod_glb(out)
        own = report[OWN_SKELETON]
        self.assertEqual((own["bones"], own["animations"]), (3, [{"name": "Walk", "seconds": 1.0, "frames": 31}]))
        self.assertNotIn("record", own)
        self.assertTrue(report["rigged"])
        self.assertTrue(any("move wasn't used" in n for n in report["notes"]))
        self.assertTrue(any("not skinned" in n and "loose" in n for n in report["notes"]))
        self.assertEqual(baf.skeleton(unitmodel.own_record(back.report))["names"], ["hips", "spine", "head"])
        self.assertEqual({n for p in back.parts if p.skin for v in p.skin for n, _w in v}, {"hips", "spine", "head"})


# --- the game's own models, out to a .glb and back (RUSE_GAME), and the 2026-11-09 horse test's (RUSE_HR_OUT) ---
def game_data():
    """{"zz": ZZ_Win.dat, "records": {model: record}, "clips": {file: bytes}} of the game at RUSE_GAME, read once."""
    if not hasattr(game_data, "got"):
        from rusemod.build import find_pack
        from rusemod.edat import Edat
        zz = Edat.open(str(find_pack(GAME, "ZZ_Win.dat")))
        records = {}
        for model in (HORSE, SOLDIER):
            name, _meshes, skels = unitmodel.packs_holding(zz, model)
            blobs = {MeshPack.read(raw).skeletons[MeshPack.read(raw).items[name][2]] for raw in skels.values()}
            assert len(blobs) == 1, f"{model}: {len(blobs)} records"
            records[model] = blobs.pop()
        clips = {}
        for e in zz.entries:
            p = e.path.lower()
            if p.endswith(".baf"):
                clips.setdefault(p.rsplit(B, 1)[-1], bytes(zz.read(e)))
            elif p.endswith(".apk"):
                arc = Edat(bytes(zz.read(e)))
                for x in arc.entries:
                    if x.path.lower().endswith(".baf"):
                        clips.setdefault(x.path.lower().rsplit(B, 1)[-1], bytes(arc.read(x)))
        game_data.got = {"zz": zz, "records": records, "clips": clips}
    return game_data.got


def model_parts(raw: bytes, model: str, names: list) -> list:
    """A model's draws in a pack, as make_glb takes them: (positions, [(bone, weight)] a point, triangles) each."""
    from rusemod.spk import Spk
    spk = Spk(raw)
    mats = spk.materials()
    out = []
    for part in spk.model(model):
        remap = mats[part.material].get("skinning") or []
        n = len(part.positions) // 3
        skin = []
        for i in range(n):
            pairs = [(remap[b] if b < len(remap) else b, w) for b, w in zip(part.bones[i], part.weights[i]) if w]
            skin.append(pairs)
        out.append(([tuple(part.positions[3 * i:3 * i + 3]) for i in range(n)], skin,
                     [tuple(part.indices[k:k + 3]) for k in range(0, len(part.indices), 3)]))
    return out


def corners(raw: bytes, model: str, names: list) -> list:
    """Each draw's triangle corners: (position, {bone name: weight})."""
    out = []
    for positions, skin, triangles in model_parts(raw, model, names):
        out.append([(positions[i], {names[b]: w for b, w in skin[i]}) for t in triangles for i in t])
    return out


def through_the_importer(test, record: bytes, clips: list, parts: list, theirs_clips: dict, kept: bool) -> dict:
    """A skeleton (with its clips and draws) out to a .glb and back in: the record (and each clip made again) against
    the given ones. Returns {"record": record_differences, "clips": {name: clip_differences}, "rig": the Rig}."""
    r = rig_of_bytes(make_glb(record, clips, parts, kept=kept))
    mine, notes = unitmodel.own_skeleton(r)
    made, _notes = unitmodel.own_clips(r, mine)
    return {"record": record_differences(mine, record), "mine": mine, "notes": notes, "rig": r,
            "clips": {name: clip_differences(made[name], theirs_clips[name]) for name, _c in clips}}


def assert_clips_close(test, got: dict) -> None:
    for name, d in got.items():
        with test.subTest(clip=name):
            test.assertEqual(d["frames"][0], d["frames"][1])
            test.assertAlmostEqual(d["length"][0], d["length"][1], places=6)
            test.assertEqual(d["missing"], [])
            test.assertLessEqual(d["poses"][0], 0.01)        # moves: game units
            test.assertLessEqual(d["poses"][1], 4 * baf.SCALE)
            test.assertLessEqual(d["poses"][2], 1e-5)


@unittest.skipUnless(GAME is not None and GAME.is_dir(), "RUSE_GAME names no game folder")
class GameModels(unittest.TestCase):
    """The game's scenery horse (36 bones, its stand, walk and run) and its US rifleman (41 bones, his clips) out to a
    .glb and back."""

    def check(self, model: str, clip_names: list) -> dict:
        data = game_data()
        record = data["records"][model]
        names = baf.skeleton(record)["names"]
        clips = [(n, baf.parse(data["clips"][n])) for n in clip_names]
        for _n, c in clips:
            self.assertEqual(baf.skeleton(c.skeleton)["names"], names)
        with_kept = through_the_importer(self, record, clips, [], data["clips"], kept=True)
        self.assertEqual(with_kept["record"], [])                        # byte for byte, the record the file carries
        plain = through_the_importer(self, record, clips, [], data["clips"], kept=False)
        sk, back = baf.skeleton(record), baf.skeleton(plain["mine"])
        self.assertEqual((back["names"], back["parents"], back["index"]), (sk["names"], sk["parents"], sk["index"]))
        for key in ("bind", "local", "world"):
            for m, n in zip(back[key], sk[key]):
                self.assertLess(rig.near(m, n), 1.0, key)
        assert_clips_close(self, plain["clips"])
        return plain

    def test_the_horse(self):
        got = self.check(HORSE, list(HORSE_CLIPS))
        self.assertTrue(got["clips"])

    def test_the_rifleman(self):
        data = game_data()
        names = baf.skeleton(data["records"][SOLDIER])["names"]
        his = sorted(n for n, c in data["clips"].items() if n.startswith("fusilier_")
                     and baf.skeleton(baf.parse(c).skeleton)["names"] == names)
        self.assertGreater(len(his), 10)
        self.check(SOLDIER, his)

    def test_the_horse_s_draws_on_its_own_bones(self):
        """The horse's draw through import_model (its own bones, on a copy of the US rifleman) and the writer: every
        corner at the game's place with the game's bones and weights; its record in the rifleman's skeleton packs."""
        from rusemod.spk import Spk
        data = game_data()
        zz = data["zz"]
        record = data["records"][HORSE]
        names = baf.skeleton(record)["names"]
        _name, horse_meshes, _skels = unitmodel.packs_holding(zz, HORSE)
        raw = min(horse_meshes.values(), key=len)
        parts = model_parts(raw, HORSE, names)
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "horse.glb"), Path(d, "files", "models", "Horse_Check.glb")
            src.write_bytes(make_glb(record, [], parts, kept=True))
            report = unitmodel.import_model(GAME, SOLDIER, src, out, own_bones=True, others=[BAZOOKA])
            prep = unitmodel.read_mod_glb(out)
        self.assertEqual(report["also"], [BAZOOKA])
        batch = {"proxies": []}
        w = unitmodel.write_unit_model(zz, SOLDIER, "horse_check", prep, batch=batch)
        packs = unitmodel.write_batch(batch)
        new = w.model
        for path in w.report["skeleton_packs"]:
            pack = MeshPack.read(packs[path])
            self.assertEqual(pack.skeletons[pack.items[new][2]], record)
        theirs = corners(raw, HORSE, names)
        for path in w.report["mesh_packs"]:
            spk = Spk(packs[path])
            mats = spk.materials()
            mine = []
            for part in spk.model(new):
                remap = mats[part.material]["skinning"]
                self.assertLessEqual(len(remap), 64)
                mine.append([(tuple(part.positions[3 * i:3 * i + 3]),
                              {names[remap[b]]: w for b, w in zip(part.bones[i], part.weights[i]) if w})
                             for i in part.indices])
            self.assertEqual(len(mine), len(theirs))
            for a, b in zip(mine, theirs):
                self.assertEqual(len(a), len(b))
                for (pa, sa), (pb, sb) in zip(a, b):
                    self.assertLess(max(abs(x - y) for x, y in zip(pa, pb)), 0.002)
                    self.assertEqual(sa, sb)


@unittest.skipUnless(GAME is not None and GAME.is_dir() and HR_OUT is not None and HR_OUT.is_dir(),
                     "RUSE_GAME and RUSE_HR_OUT name no game folder and horse test output")
class HorseTestModel(unittest.TestCase):
    """The 2026-11-09 horse test's combined horse-and-rider model (62 bones, 24 clips, its draws), out and back."""

    def setUp(self):
        import json
        self.man = json.loads((HR_OUT / "manifest.json").read_text(encoding="utf-8"))
        rifle = self.man["models"]["rifle"]
        holder = next(p for path, p in self.man["packs"].items() if "skeleton_all" in path)
        pack = MeshPack.read((HR_OUT / "packs" / holder).read_bytes())
        self.record = pack.skeletons[pack.items[rifle][2]]
        self.clips = {c + "lod0.baf": (HR_OUT / "clips" / (c + "lod0.baf")).read_bytes() for c in self.man["clips"]}
        mesh = next(p for path, p in self.man["packs"].items() if "meshskirmish_us" in path)
        self.mesh_raw = (HR_OUT / "packs" / mesh).read_bytes()
        self.rifle = rifle

    def test_its_record_and_clips(self):
        clips = [(n, baf.parse(data)) for n, data in sorted(self.clips.items())]
        kept = through_the_importer(self, self.record, clips, [], self.clips, kept=True)
        self.assertEqual(kept["record"], [])
        plain = through_the_importer(self, self.record, clips, [], self.clips, kept=False)
        sk, back = baf.skeleton(self.record), baf.skeleton(plain["mine"])
        self.assertEqual((back["names"], back["parents"]), (sk["names"], sk["parents"]))
        self.assertEqual(sk["index"], list(range(62)))                     # the test's plain order ...
        self.assertEqual(back["index"], baf.depth_order(sk["parents"]))     # ... worked out again depth by depth
        for key in ("bind", "local", "world"):
            for m, n in zip(back[key], sk[key]):
                self.assertLess(rig.near(m, n), 1.0, key)
        assert_clips_close(self, kept["clips"])
        assert_clips_close(self, plain["clips"])

    def test_its_draws(self):
        from rusemod.spk import Spk
        names = baf.skeleton(self.record)["names"]
        parts = model_parts(self.mesh_raw, self.rifle, names)
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "rider.glb"), Path(d, "files", "models", "Rider_Check.glb")
            src.write_bytes(make_glb(self.record, [], parts, kept=True))
            unitmodel.import_model(GAME, SOLDIER, src, out, own_bones=True)
            prep = unitmodel.read_mod_glb(out)
        batch = {"proxies": []}
        w = unitmodel.write_unit_model(game_data()["zz"], SOLDIER, "rider_check", prep, batch=batch)
        packs = unitmodel.write_batch(batch)
        theirs = corners(self.mesh_raw, self.rifle, names)
        path = next(p for p in w.report["mesh_packs"] if "meshskirmish_us" in p)
        spk = Spk(packs[path])
        mats = spk.materials()
        mine = []
        for part in spk.model(w.model):
            remap = mats[part.material]["skinning"]
            mine.append([(tuple(part.positions[3 * i:3 * i + 3]),
                          {names[remap[b]]: wt for b, wt in zip(part.bones[i], part.weights[i]) if wt})
                         for i in part.indices])
        self.assertEqual([len(x) for x in mine], [len(x) for x in theirs])
        for a, b in zip(mine, theirs):
            for (pa, sa), (pb, sb) in zip(a, b):
                self.assertLess(max(abs(x - y) for x, y in zip(pa, pb)), 0.002)
                self.assertEqual(sa, sb)
        for p in w.report["skeleton_packs"]:
            pack = MeshPack.read(packs[p])
            self.assertEqual(pack.skeletons[pack.items[w.model][2]], self.record)


if __name__ == "__main__":
    unittest.main()
