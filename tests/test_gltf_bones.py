"""A unit's model out to glTF with its bones at their rest poses (rusemod.gltf.model_glb's rest_bones, what Open in
Blender gives for changing a unit's model), on a made-up skinned model and skeleton record (no game files): every
bone at the record's rest pose (a bone the game sizes or mirrors as the plain turn nearest it, at its place), the
points, bone names and weights the same bytes as without it, and without it every byte as the released Studio
wrote it."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import hashlib
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

from rusemod import baf, gltf, unitlook
from rusemod.modelin import read_model
from rusemod.spk import Part
from rusemod.unitmodel import read_skeleton

NAME = "ww2\\test\\soldierlod0.ase2ndfbin"
TMP = None   # the system's temp folder (TEMP)


# --- a made-up skeleton record, laid out as the game's (rusemod.baf.skeleton reads it) ---
def turn(axis: str, degrees: float) -> list:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return {"x": [[1, 0, 0], [0, c, -s], [0, s, c]], "y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
            "z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]


def mul3(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def pose(r, at, size=1.0) -> list:
    """3 rows of [r r r t]: the turn `r` times `size`, at `at`."""
    return [[r[i][0] * size, r[i][1] * size, r[i][2] * size, at[i]] for i in range(3)]


def inverse(m) -> list:
    """Any 3 x 4 move's inverse (its turn may size or mirror)."""
    (a, b, c), (d, e, f), (g, h, i) = [row[:3] for row in m]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    inv = [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
           [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
           [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]]
    t = [m[k][3] for k in range(3)]
    return [inv[r] + [-sum(inv[r][k] * t[k] for k in range(3))] for r in range(3)]


def after(a, b) -> list:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) + (a[i][3] if j == 3 else 0.0) for j in range(4)]
            for i in range(3)]


def record(names, parents, worlds) -> bytes:
    """A skeleton record: bone count, the offsets, the names' lengths at 36, then each bone's three matrices (model ->
    bone, from its parent, bone -> model), the parents, the track index and the names."""
    nb = len(names)
    head = 36 + 2 * nb
    m_off = head + (-head % 4)
    p_off = m_off + 144 * nb
    i_off = p_off + 4 * nb
    n_off = i_off + 4 * nb
    locals_ = [w if p < 0 else after(inverse(worlds[p]), w) for w, p in zip(worlds, parents)]
    out = bytearray(struct.pack("<II7I", 1, nb, m_off, p_off, i_off, n_off, 144 * nb, 4 * nb, 4 * nb))
    out += struct.pack(f"<{nb}H", *(len(n) for n in names))
    out += bytes(m_off - len(out))
    for group in ([inverse(w) for w in worlds], locals_, worlds):
        for m in group:
            out += struct.pack("<12f", *(v for row in m for v in row))
    out += struct.pack(f"<{nb}i", *parents) + struct.pack(f"<{nb}I", *range(nb))
    raw = "".join(names).encode("latin-1")
    return bytes(out + raw + bytes(-len(raw) % 4))


# the cases the game's skeletons have: a root, a joint whose parent bone isn't one of the model's joints (it hangs
# from the joint above), a Biped leg with no parent bones (a soldier's: thigh and calf), a bone the game sizes (every
# bone of the P-47) and a child of it, a mirrored bone, and another bone with no parent (a vehicle's wheel)
NAMES = ["bip01", "bip01 spine", "fx_point", "bip01 head", "bip01 l thigh", "wing", "flap", "mirror", "bip01 l calf",
         "wheel"]
PARENTS = [-1, 0, 1, 2, -1, 0, 5, 0, -1, -1]
UP = turn("z", 90)
DOWN = turn("y", 90)     # its +x down the leg
WORLDS = [pose(UP, (0.0, 0.0, 100.0)),
          pose(mul3(UP, turn("y", 20)), (5.0, 0.0, 150.0)),
          pose(mul3(UP, turn("y", 25)), (5.0, 0.0, 170.0)),
          pose(mul3(UP, turn("x", 15)), (6.0, 1.0, 190.0)),
          pose(DOWN, (0.0, 10.0, 90.0)),
          pose(turn("x", 30), (50.0, 0.0, 100.0), size=0.9),
          pose(turn("z", 10), (80.0, 0.0, 100.0)),
          pose(mul3([[1, 0, 0], [0, -1, 0], [0, 0, 1]], turn("z", 30)), (0.0, -40.0, 120.0)),
          pose(mul3(DOWN, turn("z", 5)), (0.0, 10.0, 50.0)),
          pose(turn("z", 0), (30.0, 20.0, 10.0))]
RECORD = record(NAMES, PARENTS, WORLDS)


def parts() -> list:
    """Two draws: one on the skeleton's own numbers, one through a SkinningRemapping (its 0..3 are bones 3, 6, 7, 0);
    no bone leans on fx_point."""
    def part(material, points, bones, weights):
        n = len(points)
        return Part(material, [c for p in points for c in p], [0.0, 0.0, 1.0] * n,
                    [c for k in range(n) for c in (k / n, 1 - k / n)],
                    [k for t in range(n - 2) for k in (0, t + 1, t + 2)], bones=bones, weights=weights)
    a = part(0, [(0, 0, 100), (5, 0, 150), (0, 10, 60), (50, 0, 100), (0, 12, 80), (0, 10, 30), (30, 20, 10)],
             [[0, 0, 0, 0], [1, 0, 0, 0], [4, 0, 0, 0], [5, 0, 0, 0], [4, 0, 1, 0], [8, 4, 0, 0], [9, 0, 0, 0]],
             [[255, 0, 0, 0], [200, 55, 0, 0], [255, 0, 0, 0], [255, 0, 0, 0], [128, 0, 127, 0], [200, 55, 0, 0],
              [255, 0, 0, 0]])
    b = part(1, [(6, 1, 195), (85, 0, 100), (0, -40, 120), (3, -2, 101)],
             [[0, 0, 0, 0], [1, 2, 0, 0], [2, 0, 0, 0], [3, 0, 0, 0]],
             [[255, 0, 0, 0], [150, 105, 0, 0], [255, 0, 0, 0], [255, 0, 0, 0]])
    return [(a, None), (b, None)]


class FakeSpk:
    def materials(self):
        return [{"name": "body", "type": "Standard", "textures": {}, "skinning": []},
                {"name": "gear", "type": "Standard", "textures": {}, "skinning": [3, 6, 7, 0]}]


class FakeLibrary:
    """What gltf.model_glb uses of rusemod.models.Library, for a skinned model with no pictures."""

    def __init__(self, skeleton=RECORD):
        self.where = {NAME: FakeSpk()}
        self.record = skeleton

    def parts(self, name):
        return parts()

    def picture(self, texture, most=512):
        return None

    def bone_names(self, name):
        return read_skeleton(self.record).names if self.record else None

    def skeleton(self, name):
        return self.record


def read_glb(raw: bytes):
    n = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    blen = struct.unpack_from("<I", raw, 20 + n)[0]
    return doc, raw[28 + n:28 + n + blen]


def view(doc, binary, i) -> bytes:
    v = doc["bufferViews"][doc["accessors"][i]["bufferView"]]
    return binary[v["byteOffset"]:v["byteOffset"] + v["byteLength"]]


def node_matrix(node) -> list:
    """A node's move, turn and size as 4 x 4 rows."""
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    t, s = node.get("translation", [0, 0, 0]), node.get("scale", [1, 1, 1])
    return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def mul4(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def in_gltf(m12) -> list:
    """A record's matrix (game axes and units) as 4 x 4 rows in the export's: M R M and 0.01 M t."""
    m = [list(m12[0:4]), list(m12[4:8]), list(m12[8:12])]
    p = (0, 2, 1)
    t = gltf._point(m[0][3], m[1][3], m[2][3])
    return [[m[p[i]][p[j]] for j in range(3)] + [t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def turned(m12) -> tuple:
    """A record's rest pose with its frame turned as the file writes it (gltf.TURN): rows times TURN."""
    rows = [list(m12[0:4]), list(m12[4:8]), list(m12[8:12])]
    return tuple(sum(rows[i][k] * gltf.TURN[k][j] for k in range(3)) + (rows[i][3] if j == 3 else 0.0)
                 for i in range(3) for j in range(4))


class RestBones(unittest.TestCase):
    def setUp(self):
        self.base, _pics, self.base_summary = gltf.model_glb(FakeLibrary(), NAME)
        self.rest, _pics2, self.summary = gltf.model_glb(FakeLibrary(), NAME, rest_bones=True)
        self.d0, self.b0 = read_glb(self.base)
        self.d1, self.b1 = read_glb(self.rest)

    def test_default_as_the_released_studio_wrote_it(self):
        # the SHA-256 of this file as the released Studio's gltf.py (0.9.8.19, 67d7e1c4) writes it, and every one the
        # same with rest_bones off
        self.assertEqual(hashlib.sha256(self.base).hexdigest(), RELEASED)
        self.assertEqual(gltf.model_glb(FakeLibrary(), NAME, rest_bones=False)[0], self.base)
        self.assertNotIn("rest_bones", self.base_summary)

    def test_points_names_and_weights_the_same_bytes(self):
        for m0, m1 in zip(self.d0["meshes"], self.d1["meshes"]):
            for p0, p1 in zip(m0["primitives"], m1["primitives"]):
                self.assertEqual(p0, p1)
                for a in list(p0["attributes"].values()) + [p0["indices"]]:
                    self.assertEqual(view(self.d0, self.b0, a), view(self.d1, self.b1, a))
                    self.assertEqual(self.d0["accessors"][a], self.d1["accessors"][a])
        self.assertEqual([n["name"] for n in self.d0["nodes"]], [n["name"] for n in self.d1["nodes"]])
        self.assertEqual(self.d0["skins"], self.d1["skins"])
        self.assertEqual(self.summary["bones"], self.base_summary["bones"])
        same = ("meshes", "materials", "scenes", "scene", "skins", "asset")
        self.assertEqual({k: self.d0.get(k) for k in same}, {k: self.d1.get(k) for k in same})

    def test_each_bone_at_its_rest_pose(self):
        sk = baf.skeleton(RECORD)
        joints = self.summary["bones"]
        self.assertEqual(joints, [0, 1, 3, 4, 5, 6, 7, 8, 9])     # (fx_point: no point leans on it)
        parent = {c: i for i, n in enumerate(self.d1["nodes"]) for c in n.get("children", [])}

        def world(i):
            here = node_matrix(self.d1["nodes"][i])
            return mul4(world(parent[i]), here) if i in parent else here
        acc = self.d1["accessors"][self.d1["skins"][0]["inverseBindMatrices"]]
        raw = view(self.d1, self.b1, self.d1["skins"][0]["inverseBindMatrices"])
        self.assertEqual(acc["count"], len(joints))
        for k, (node, b) in enumerate(zip(self.d1["skins"][0]["joints"], joints)):
            w = world(node)
            want = in_gltf(turned(sk["world"][b]))
            for i in range(3):    # its place: exactly where the record has it
                self.assertAlmostEqual(w[i][3], want[i][3], places=6, msg=NAMES[b])
            cols = [[w[i][j] for i in range(3)] for j in range(3)]
            x = [sk["world"][b][4 * i] for i in range(3)]       # the record's +x for it (game axes)
            n = math.sqrt(sum(c * c for c in x))
            along = [x[0] / n, x[2] / n, x[1] / n]                # after the mirror
            if NAMES[b] in ("wing", "mirror"):       # sized or mirrored: the nearest plain turn
                for j in range(3):
                    self.assertAlmostEqual(sum(c * c for c in cols[j]), 1.0, places=6)
                rows = [row[:3] for row in w[:3]]
                det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
                       - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
                       + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
                self.assertAlmostEqual(det, 1.0, places=6)
                if NAMES[b] == "wing":   # sized only: its bone still along its +x
                    for i in range(3):
                        self.assertAlmostEqual(cols[1][i], along[i], places=5)
            else:                                    # a plain bone: its turn too, its bone (Blender: +y) along its +x
                for i in range(3):
                    for j in range(3):
                        self.assertAlmostEqual(w[i][j], want[i][j], places=5, msg=NAMES[b])
                    self.assertAlmostEqual(cols[1][i], along[i], places=5, msg=NAMES[b])
            ibm = struct.unpack_from("<16f", raw, 64 * k)
            back = mul4(w, [[ibm[c * 4 + r] for c in range(4)] for r in range(4)])
            for i in range(4):     # its pose times its inverse bind matrix: nothing moves at rest
                for j in range(4):
                    self.assertAlmostEqual(back[i][j], 1.0 if i == j else 0.0, places=5, msg=NAMES[b])

    def test_the_tree(self):
        nodes = self.d1["nodes"]
        by_name = {n["name"]: i for i, n in enumerate(nodes)}
        parent = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
        rig = self.d1["skins"][0]["skeleton"]
        self.assertEqual(nodes[rig]["name"], "soldier_bones")
        self.assertEqual([nodes[c]["name"] for c in nodes[rig]["children"]], ["bip01"])
        up = {name: nodes[parent[i]]["name"] for name, i in by_name.items() if i in parent}
        self.assertEqual(up["bip01 head"], "bip01 spine")      # past fx_point, which no point leans on
        self.assertEqual(up["flap"], "wing")
        # the bones the game gives no parent: the Biped leg chained from the first bone, the wheel from it too
        self.assertEqual((up["bip01 l thigh"], up["bip01 l calf"], up["wheel"]), ("bip01", "bip01 l thigh", "bip01"))
        self.assertEqual(self.summary["hung"], {"bip01 l thigh": "bip01", "bip01 l calf": "bip01 l thigh",
                                                "wheel": "bip01"})
        self.assertEqual(self.d1["scenes"][0]["nodes"], [0, rig])
        self.assertTrue(self.summary["rest_bones"])
        self.assertEqual(self.summary["plain_turns"], ["wing", "mirror"])
        for name in ("bip01", "bip01 spine", "bip01 head", "flap", "bip01 l calf"):     # plain ones: no size
            for s in nodes[by_name[name]]["scale"]:
                self.assertAlmostEqual(s, 1.0, places=5)

    def test_the_turn_is_exact(self):
        """A plain bone under its own parent keeps the record's numbers, only swapped and negated: its inverse bind
        matrix is the record's turned back, exactly as rusemod.animglb would write the turned matrix."""
        from rusemod.animglb import _ibm
        sk = baf.skeleton(RECORD)
        raw = view(self.d1, self.b1, self.d1["skins"][0]["inverseBindMatrices"])
        k = self.summary["bones"].index(1)                   # bip01 spine: plain, under bip01
        b = [list(sk["bind"][1][0:4]), list(sk["bind"][1][4:8]), list(sk["bind"][1][8:12])]
        back = [[-v for v in b[2]], b[1], b[0]]              # TURN's inverse times it
        want = struct.unpack("<16f", struct.pack("<16f", *_ibm(tuple(v for row in back for v in row))))
        self.assertEqual(struct.unpack_from("<16f", raw, 64 * k), want)

    def test_import_model_reads_both_the_same(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            (Path(d) / "a.glb").write_bytes(self.base)
            (Path(d) / "b.glb").write_bytes(self.rest)
            a, b = read_model(Path(d) / "a.glb", skin=True), read_model(Path(d) / "b.glb", skin=True)
        self.assertEqual([(m.positions, m.triangles, m.skin) for m in a.meshes],
                         [(m.positions, m.triangles, m.skin) for m in b.meshes])
        self.assertIn(("flap", 150), b.meshes[1].skin[1])

    def test_no_skeleton_record_writes_it_as_before_and_says_so(self):
        raw, _pics, summary = gltf.model_glb(FakeLibrary(skeleton=None), NAME, rest_bones=True)
        self.assertFalse(summary["rest_bones"])
        doc, _bin = read_glb(raw)
        self.assertEqual([n.get("name") for n in doc["nodes"]],
                         ["soldier"] + [f"bone_{b}" for b in (0, 1, 3, 4, 5, 6, 7, 8, 9)] + ["soldier_bones"])
        self.assertFalse(any("translation" in n for n in doc["nodes"]))

    def test_prepare_passes_it_on(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            rest = unitlook.prepare(FakeLibrary(), [NAME], Path(d) / "rest", rest_bones=True)
            plain = unitlook.prepare(FakeLibrary(), [NAME], Path(d) / "plain")
            file = rest["models"][0]
            self.assertEqual(rest["rest_bones"], {file: True})
            self.assertEqual(Path(file).read_bytes(), self.rest)
            self.assertEqual(sorted(plain), ["models", "pictures"])
            self.assertEqual(Path(plain["models"][0]).read_bytes(), self.base)


class LibrarySkeleton(unittest.TestCase):
    """rusemod.models.Library on a made-up ZZ_Win.dat (test_unitpacks'): the skeleton record bone_names reads, and
    model_glb's rest_bones placing the tank's bone with it."""

    def test_skeleton_record_and_bone_names(self):
        from rusemod.models import Library
        from test_unitpacks import TANK, zz_win
        rec = record(["chassis"], [-1], [pose(turn("z", 30), (12.0, -3.0, 40.0))])
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            game = Path(d)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "Maps" / "PC" / "ZZ_Win.dat").write_bytes(zz_win(skeleton_of_tank=rec).to_bytes())
            lib = Library(game)
            try:
                self.assertEqual(lib.skeleton(TANK), rec)
                self.assertEqual(lib.bone_names(TANK), ["chassis"])
                self.assertIsNone(lib.skeleton("ww2\\nothing.ase2ndfbin"))
                raw, _pics, summary = gltf.model_glb(lib, TANK, rest_bones=True)
            finally:
                lib.close()
        self.assertTrue(summary["rest_bones"])
        doc, _bin = read_glb(raw)
        bone = next(n for n in doc["nodes"] if n.get("name") == "chassis")
        self.assertEqual([round(v, 6) for v in bone["translation"]], [0.12, 0.4, -0.03])   # (x, z, y) x 0.01


# this module's made-up model as the released Studio 0.9.8.19's gltf.py (67d7e1c4) writes it: its SHA-256
RELEASED = "a470790b875fef2e0638998d90606616cf8dbe06d3bfec0cd181c3ef304ba90b"

if __name__ == "__main__":
    unittest.main()
