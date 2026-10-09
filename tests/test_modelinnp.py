"""rusemod.modelinnp (numpy) against rusemod.modelin's own loops, to the last bit: read_model, prepare and write_glb on
made-up models, .glb and .3ds files (tanks, trucks and planes of each kind modelin.facing's rules tell apart, every
way round) give the same meshes, the same fitted parts (a pickle of them: the same bytes), the same report and the same
.glb bytes either way; which way a model faces is modelin.facing's own either way. The loops are the reference: whole
arrays made the importer many times faster on a 2.8-million-triangle scan (2026-10-08), and the models it makes must
not change for it."""
import contextlib
import math
import pickle
import random
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import modelin, png, unitlook
from rusemod.dxt import png_bytes

try:
    import numpy as np
    from rusemod import modelinnp
except ImportError:
    np = modelinnp = None


@contextlib.contextmanager
def loops():
    """The importer's own loops from here on: whole arrays kept away (its pictures' too)."""
    with mock.patch.object(modelin, "whole_arrays", lambda: None), \
            mock.patch.object(png, "whole_arrays", lambda: None), \
            mock.patch.object(unitlook, "whole_arrays", lambda: None):
        yield


def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def model_bytes(model) -> bytes:
    return pickle.dumps(([(m.name, m.positions, m.triangles, m.uvs, m.face_materials, m.normals) for m in model.meshes],
                         [(m.name, m.picture, m.colour, m.data, m.alpha) for m in model.materials]), protocol=5)


def glb_bytes(prep) -> bytes:
    """What write_glb saves, kept in memory (2026-10-08, the PC busy: each file opened took about 10 ms, most of the
    time of a test saving hundreds of small models)."""
    kept = []
    with mock.patch.object(Path, "mkdir", lambda *_a, **_k: None), \
            mock.patch.object(Path, "write_bytes", lambda _path, data: kept.append(data)):
        modelin.write_glb(prep, Path("m.glb"), "like")
    return kept[0]


def prep_bytes(prep) -> bytes:
    """What the markings check compares (an exact pickle of every part and the pictures), and the report."""
    return pickle.dumps(([(p.bone, p.picture, p.positions, p.normals, p.uvs, p.triangles) for p in prep.parts],
                         prep.pictures, repr(prep.report)), protocol=5)


def points(rnd, n: int, lo, hi) -> list:
    return [tuple(f32(rnd.uniform(a, b)) for a, b in zip(lo, hi)) for _ in range(n)]


def triangles(rnd, n: int, count: int) -> list:
    out = [tuple(rnd.sample(range(n), 3)) for _ in range(count)]
    a, b = rnd.sample(range(n), 2)
    return out + [(a, a, b), (b, a, b)]      # two with a corner twice: no area, no normal of their own


def normals(rnd, n: int) -> list:
    out = []
    for _ in range(n):
        v = [rnd.uniform(-1, 1) for _ in range(3)]
        s = math.sqrt(sum(c * c for c in v))
        out.append(tuple(f32(c / s) for c in v))
    out[n // 2] = (0.0, 0.0, 0.0)              # one with no length: _unit's (0.0, 0.0, 1.0)
    out[n // 3] = (-0.0, 0.0, -0.0)
    return out


def picture(w: int, h: int, seed: int) -> bytes:
    rnd = random.Random(seed)
    return png_bytes(bytes(rnd.randrange(256) for _ in range(w * h * 3)), w, h)


def made_up(seed: int, turret: bool = True, own_normals: str = "some") -> modelin.Model:
    """A tank-like model of float32 numbers (as files hold them): a hull with some of its own normals and uvs, its
    triangles on four materials (one past the list: no picture); a turret with all its normals and no uvs; a barrel with
    none and fewer materials than triangles (the rest dropped, as zip drops them); a hatch resting on the turret; the
    hull a second time (the same mesh object); lowest z and x both 0.0 and -0.0 (min keeps the first)."""
    rnd = random.Random(seed)
    hull_pts = points(rnd, 90, (-30, -12, 0.5), (30, 12, 10)) + [(-30.5, 1.0, -0.0), (-30.5, 2.0, 0.0),
                                                                  (31.0, -0.0, 0.0), (31.0, 0.0, -0.0)]
    n = len(hull_pts)
    given = {"some": 60, "all": n + 2, "none": 0}[own_normals]
    hull_tris = triangles(rnd, n, 170) + [(n, n, n + 1)]   # (two points only on a triangle with no area: no normal)
    hull_pts += points(rnd, 2, (-1, -1, 1), (1, 1, 2))
    hull = modelin.Mesh("Hull_body", hull_pts, hull_tris, [(f32(rnd.random()), f32(rnd.random()))
                                                           for _ in range(n + 2)],
                        [rnd.choice((0, 1, -1, 5)) for _ in range(173)], normals(rnd, given) if given else [])
    meshes = [hull]
    if turret:
        tp = points(rnd, 40, (-8, -6, 10), (8, 6, 16))
        meshes.append(modelin.Mesh("Turret", tp, triangles(rnd, 40, 60), [], [],
                                   normals(rnd, 40) if own_normals != "none" else []))
        bp = points(rnd, 16, (8, -1, 12), (25, 1, 14))
        meshes.append(modelin.Mesh("Gun_Barrel", bp, triangles(rnd, 16, 20),
                                   [(f32(rnd.random()), f32(rnd.random())) for _ in range(16)], [1] * 15, []))
        hp = points(rnd, 10, (-3, -3, 16), (3, 3, 17))
        meshes.append(modelin.Mesh("hatch", hp, triangles(rnd, 10, 8), [], [0] * 10, []))
        meshes.append(modelin.Mesh("mg_coax", points(rnd, 6, (5, 2, 11), (9, 3, 12)), triangles(rnd, 6, 3), [], [],
                                   []))
    meshes.append(hull)
    materials = [modelin.Material("Paint", colour=(0.2, 0.4, 0.6)),
                 modelin.Material("Glass", "glass.png", data=picture(6, 5, seed), alpha=picture(6, 5, seed + 1))]
    return modelin.Model(meshes, materials)


LIKE = {"length": 600.0, "width": 250.0, "pivot": (10.0, -0.0), "ground": -0.0, "middle": 3.0}


# --- shapes for facing, z up, along x (the tanks, jets, swept wings and the parked plane facing +x, the biplanes and
# the monoplane -x); each part (name, points, triangles) ---
CUBE_FACES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (3, 7, 6), (3, 6, 2), (0, 4, 7),
              (0, 7, 3), (1, 2, 6), (1, 6, 5)]


def cube(lo, hi) -> tuple:
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
            (x0, y1, z1)], list(CUBE_FACES)


def steps(lo: float, hi: float, n: int) -> list:
    return [lo + (hi - lo) * k / (n - 1) for k in range(n)]


def sheet(xs, ys, height, sweep: float = 0.0) -> tuple:
    """A surface over xs x ys at height(x, y), each point moved back (-x) by sweep x |y| (a swept wing)."""
    pts = [(x - sweep * abs(y), y, height(x, y)) for x in xs for y in ys]
    tris = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            a, b = i * len(ys) + j, (i + 1) * len(ys) + j
            tris += [(a, b, b + 1), (a, b + 1, a + 1)]
    return pts, tris


def joined(*pieces) -> tuple:
    """Several pieces as one part (a scan's or a download's single Object_1)."""
    pts, tris = [], []
    for p, t in pieces:
        tris += [(a + len(pts), b + len(pts), c + len(pts)) for a, b, c in t]
        pts += p
    return pts, tris


def _hull_and_turret():
    return cube((-3, -1.5, 0), (3, 1.5, 1)), cube((-1, -1, 1), (1, 1, 2))


def _tank(gun_to: float, stowage: bool = False, named: bool = False) -> list:
    hull, turret = _hull_and_turret()
    gun = cube((1, -0.1, 1.4), (gun_to, 0.1, 1.55))
    if named:
        return [("Hull", *hull), ("Turret", *turret), ("Gun_Barrel", *gun)]
    pieces = [hull, turret, gun] + ([cube((-3.5, -0.5, 0.6), (-3, 0.5, 0.8))] if stowage else [])
    return [("Object_1", *joined(*pieces))]


def _truck() -> list:
    wheels = [cube((x, y, 0), (x + 0.6, y + 0.3, 0.45)) for x in (-2.8, 1.8) for y in (-1.3, 1.0)]
    return [("Object_2", *joined(cube((2, -1.2, 0.2), (3, 1.2, 2)), cube((-3, -1.2, 0.5), (2, 1.2, 1.5)))),
            ("Object_3", *joined(*wheels))]


def _jet(fins: tuple) -> list:
    body = cube((-9.5, -0.8, 0), (9.5, 0.8, 1.5))
    wings = sheet(steps(-3, 2, 6), steps(-5.8, 5.8, 13), lambda x, y: 0.7)
    tail = sheet(steps(-9.5, -7.5, 3), steps(-3, 3, 7), lambda x, y: 1.0)
    return [("fuselage", *body), ("wings", *joined(wings, tail)),
            ("fin", *joined(*(cube((-9, y - 0.1, 1.5), (-7, y + 0.1, 5)) for y in fins)))]


def _swept_wing_canopy_highest() -> list:
    """No fin above its canopy, its wings swept back (a flying wing's)."""
    return [("body", *cube((-4, -0.6, 0), (4, 0.6, 0.8))), ("canopy", *cube((0.5, -0.3, 0.8), (2.0, 0.3, 1.3))),
            ("wings", *sheet(steps(-1, 1, 5), steps(-5, 5, 41), lambda x, y: 0.4, sweep=1.0))]


def _biplane(wings: int, flat_top: bool = False) -> list:
    body = cube((-3, -0.4, 0.6), (3, 0.4, 1.2))
    out = [("body", *body)]
    for k in range(wings):
        z = 0.6 + 1.4 * k / max(1, wings - 1)
        top = k == wings - 1
        out.append((f"wing{k}", *sheet(steps(-2, -1, 5), steps(-4, 4, 17), (lambda x, y, z=z: z) if top and flat_top
                                       else (lambda x, y, z=z: z + 0.01 * abs(y)))))
    out.append(("tail", *joined(cube((2.4, -0.05, 1.2), (3, 0.05, 1.8)),
                                sheet((2.4, 3.0), (-1.2, 0.0, 1.2), lambda x, y: 1.2))))
    return out


def _parked_tail_down() -> list:
    """Parked on its tail wheel, nose up at +x, a propeller blade its highest point (as test_unitmodel's)."""
    return [("fuselage", *sheet(steps(-3, 3, 25), (-0.4, 0.4), lambda x, y: 1.0 + 0.2 * x)),
            ("cowling", *sheet((2.6, 2.8, 3.0), steps(-0.5, 0.5, 5), lambda x, y: 1.2)),
            ("wing", *sheet(steps(1, 2, 5), steps(-5, 5, 21), lambda x, y: 1.2)),
            ("tailplane", *sheet((-3.0, -2.7, -2.4), steps(-1.5, 1.5, 7), lambda x, y: 0.5)),
            ("fin", [(-2.6, 0.0, 0.4), (-3.0, 0.0, 0.4), (-2.8, 0.0, 1.3)], [(0, 1, 2)]),
            ("blade", [(3.2, -0.1, 2.8), (3.2, 0.1, 2.8), (3.2, 0.0, 0.6)], [(0, 1, 2)])]


def _monoplane_high_tips() -> list:
    return [("body", *cube((-4, -0.5, 0), (4, 0.5, 1))),
            ("wing", *sheet(steps(-1.5, 0, 4), steps(-6, 6, 25), lambda x, y: 0.5 + 0.35 * abs(y))),
            ("fin", *cube((3, -0.05, 1), (4, 0.05, 2.2)))]


SHAPES = {  # name: (aircraft, parts)
    "tank, gun and turret named": (False, lambda: _tank(4.5, named=True)),
    "tank, a long gun, nothing named": (False, lambda: _tank(5.0)),
    "tank, a short gun": (False, lambda: _tank(3.2)),
    "tank, a short gun and stowage behind": (False, lambda: _tank(3.2, stowage=True)),
    "truck": (False, _truck),
    "jet, one fin": (True, lambda: _jet((0.0,))),
    "jet, twin fins": (True, lambda: _jet((-1.5, 1.5))),
    "swept wings, its canopy highest": (True, _swept_wing_canopy_highest),
    "biplane, its top wing highest": (True, lambda: _biplane(2)),
    "triplane": (True, lambda: _biplane(3)),
    "biplane, a flat top wing": (True, lambda: _biplane(2, flat_top=True)),
    "parked tail down, a blade highest": (True, _parked_tail_down),
    "monoplane, its wingtips highest": (True, _monoplane_high_tips),
}
GROUND_LIKES = [LIKE, {"length": 600.0, "pivot": (0.0, 0.0), "ground": 0.0},
                dict(LIKE, facing=[1, -1])]     # (pinned by hand)
PLANE_LIKES = [{"length": 980.0, "width": 1130.0, "pivot": (0.0, 0.0), "ground": 50.0, "aircraft": True},   # a P-51
               {"length": 1500.0, "width": 1000.0, "pivot": (5.0, 0.0), "ground": 40.0, "aircraft": True}]  # a jet


def placed(parts: list, quarter: int, seed: int) -> list:
    """The parts turned `quarter` quarter turns round z (along x, along y, the other way round), x and y moved a little
    (not z: a flat top wing stays flat), as 32-bit floats."""
    rnd = random.Random(seed)
    out = []
    for name, pts, tris in parts:
        moved = []
        for x, y, z in pts:
            x, y = [(x, y), (-y, x), (-x, -y), (y, -x)][quarter]
            moved.append((f32(x + rnd.uniform(-2e-3, 2e-3)), f32(y + rnd.uniform(-2e-3, 2e-3)), f32(z)))
        out.append((name, moved, tris))
    return out


def shape_glb(parts: list, seed: int) -> bytes:
    """The parts as a .glb (glTF's y up: a point (x, y, z) written (x, z, -y), as read_glb reads it back): own normals
    on some, uvs on some, 16- and 32-bit indices, a picture and a plain colour."""
    from rusemod.gltf import FLOAT, UINT, USHORT, _Glb
    rnd = random.Random(seed)
    g = _Glb()
    tex = g.image(picture(8, 8, seed), "paint")
    g.doc["materials"] = [{"name": "Paint", "pbrMetallicRoughness": {"baseColorTexture": {"index": tex}}},
                          {"name": "Plain", "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.25, 1.0, 1.0]}}]
    for k, (name, pts, tris) in enumerate(parts):
        attrs = {"POSITION": g.accessor([(x, z, -y) for x, y, z in pts], "VEC3", FLOAT)}
        if k % 2 == 0:
            attrs["NORMAL"] = g.accessor(normals(rnd, len(pts)), "VEC3", FLOAT)
        if k % 3 != 1:
            attrs["TEXCOORD_0"] = g.accessor([(f32(rnd.random()), f32(rnd.random())) for _ in pts], "VEC2", FLOAT)
        index = g.accessor([i for t in tris for i in t], "SCALAR", USHORT if k % 2 else UINT, 34963)
        g.doc["meshes"].append({"name": name, "primitives": [{"attributes": attrs, "indices": index,
                                                              "material": k % 2}]})
        g.doc["nodes"].append({"name": name, "mesh": k})
    g.doc["scenes"] = [{"nodes": list(range(len(parts)))}]
    g.doc["scene"] = 0
    return g.to_bytes()


def _chunk(cid: int, body: bytes) -> bytes:
    return struct.pack("<HI", cid, 6 + len(body)) + body


def shape_3ds(parts: list, seed: int) -> bytes:
    """The parts as a .3ds (z up, as it is), uvs on some, every triangle on a material whose picture is PAINT.PNG."""
    rnd = random.Random(seed)
    material = _chunk(0xAFFF, _chunk(0xA000, b"Paint\0") + _chunk(0xA200, _chunk(0xA300, b"PAINT.PNG\0")))
    objects = b""
    for k, (name, pts, tris) in enumerate(parts):
        verts = _chunk(0x4110, struct.pack("<H", len(pts)) + b"".join(struct.pack("<3f", *p) for p in pts))
        uvs = _chunk(0x4140, struct.pack("<H", len(pts)) + b"".join(struct.pack("<2f", rnd.random(), rnd.random())
                                                                     for _ in pts)) if k % 2 else b""
        on = _chunk(0x4130, b"Paint\0" + struct.pack(f"<H{len(tris)}H", len(tris), *range(len(tris))))
        faces = _chunk(0x4120, struct.pack("<H", len(tris)) + b"".join(struct.pack("<4H", *t, 0) for t in tris) + on)
        objects += _chunk(0x4000, name.encode() + b"\0" + _chunk(0x4100, verts + uvs + faces))
    return _chunk(0x4D4D, _chunk(0x3D3D, material + objects))


class Loads(unittest.TestCase):
    def test_numpy_2_means_whole_arrays(self):
        """Where numpy 2 is (the apps carry 2.5.3), the importer and its pictures use whole arrays: a module that
        refused to load (its own check of sum(), say) would leave every test here skipped, and the importer slow."""
        try:
            from rusemod.numpy2 import np  # noqa: F401
        except ImportError:
            self.skipTest("no numpy 2 here: the loops do the work")
        self.assertIsNotNone(modelin.whole_arrays())
        self.assertIsNotNone(png.whole_arrays())
        self.assertIsNotNone(unitlook.whole_arrays())


@unittest.skipIf(modelinnp is None, "numpy isn't here: the importer's loops do all of it")
class WholeArrays(unittest.TestCase):
    """rusemod.modelinnp against the loops, piece by piece and whole, to the last bit."""

    def same(self, a: bytes, b: bytes, what=None):
        self.assertTrue(a == b, what)       # (said without laying out a large difference)

    def test_python_sum_of_floats(self):
        """sum() of a few floats (a point through a matrix, a normal's length): py_sum adds as this Python does,
        Neumaier's carry since 3.12 included, on 200,000 awkward sums."""
        rnd = random.Random(5)
        specials = [0.0, -0.0, 1.0, -1.0, 5e-324, 1e308, -1e308, math.inf, -math.inf, 1e16, 2.0 ** 53, 0.1, 3.0]
        for width in (1, 2, 3, 4):
            cases = []
            for _ in range(50000):
                case = []
                for _ in range(width):
                    k = rnd.random()
                    case.append(rnd.choice(specials) if k < 0.15 else rnd.uniform(-1, 1) * 10.0 ** rnd.randint(-25, 25)
                                if k < 0.5 else f32(rnd.uniform(-100, 100)) * rnd.choice((1.0, -0.0, 0.01, 1e-7)))
                cases.append(case)
            got = modelinnp.py_sum([np.array([c[k] for c in cases]) for k in range(width)])
            want = np.array([sum(c) for c in cases])
            same = (got.view(np.uint64) == want.view(np.uint64)) | (np.isnan(got) & np.isnan(want))
            self.assertTrue(same.all(), (width, [cases[i] for i in np.flatnonzero(~same)[:3]]))
        self.assertTrue(modelinnp._sum_is_known())

    def test_a_sum_unlike_pythons_is_refused(self):
        """The module's own check catches a sum() that adds another way (then it won't load: the loops do it all)."""
        other = modelinnp._running if modelinnp._SUM is modelinnp._compensated else modelinnp._compensated
        with mock.patch.object(modelinnp, "_SUM", other):
            self.assertFalse(modelinnp._sum_is_known())

    def test_numpy_comes_through_numpy2(self):
        text = Path(modelinnp.__file__).read_text(encoding="utf-8")
        self.assertIn("from .numpy2 import np", text)
        self.assertNotIn("import numpy", text)

    def test_the_lowest_and_highest_are_the_first_of_equals(self):
        """min() and max() keep the first of equal numbers: 0.0 and -0.0 are equal, and which comes first shows."""
        for values in ([0.0, -0.0, 1.0], [-0.0, 0.0, 1.0], [1.0, 0.0, -0.0], [2.0, -0.0, 0.0, -1.0, 3.0], [-0.0]):
            cols = [np.array(values[:2]), np.array(values[2:])] if len(values) > 2 else [np.array(values)]
            self.assertEqual(struct.pack("<d", modelinnp._lowest(cols)), struct.pack("<d", min(values)), values)
            self.assertEqual(struct.pack("<d", modelinnp._highest([-c for c in cols])),
                             struct.pack("<d", max(-v for v in values)), values)
        big = np.zeros(100000)
        big[7::2] = -0.0
        self.assertEqual(struct.pack("<d", modelinnp._lowest([big[5:]])), struct.pack("<d", min(big[5:].tolist())))

    def check_prepare(self, model, like, **kw):
        """prepare on the loops and on whole arrays: the same parts, pictures and report; and the same .glb."""
        here = modelinnp.prepare(modelin, model, [], like, kw.get("size", 1.0), kw.get("side", 1024))
        self.assertIsNotNone(here, "the whole arrays left this model to the loops")
        with loops():
            want = modelin.prepare(model, [], like, **kw)
        self.same(prep_bytes(here), prep_bytes(want), "prepare")
        self.same(prep_bytes(modelin.prepare(model, [], like, **kw)), prep_bytes(want), "prepare through modelin")
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d, "a", "m.glb"), Path(d, "b", "m.glb")
            modelin.write_glb(here, a, "like")
            with loops():
                modelin.write_glb(want, b, "like")
            self.same(a.read_bytes(), b.read_bytes(), "write_glb")
        for part in here.parts:
            self.assertIsNotNone(modelinnp.part_buffers(part, 0.01, True))
        return here

    def test_a_tank_with_a_turret_and_gun(self):
        for seed in (1, 2, 3):
            for own in ("some", "all", "none"):
                prep = self.check_prepare(made_up(seed, own_normals=own), LIKE)
                self.assertEqual(prep.report["parts"]["hatch"], modelin.TURRET)     # (it rests on the turret)
                self.assertEqual(prep.report["parts"]["Gun_Barrel"], modelin.GUN)
                if own == "some":
                    self.assertIn("the rest worked out", prep.report["normals"])
                    flat = [n for p in prep.parts for n in p.normals if n == (0.0, 0.0, 1.0)]
                    # the loops' own tuples, from _unit (a normal of no length) and smooth_normals (no area)
                    self.assertTrue(any(n is modelin._unit((0.0, 0.0, 0.0)) for n in flat))
                    self.assertTrue(any(n is modelin.smooth_normals([(0.0, 0.0, 0.0)], [])[0] for n in flat))
        self.check_prepare(made_up(4), LIKE, size=1.5, side=4)

    def test_no_turret_and_aircraft(self):
        """No turret: the middle where the unit's is; an aircraft: its highest points' side is its back (a sort of
        every point by height, ties kept in order, and Python's own sum of the highest)."""
        for seed in (5, 6):
            model = made_up(seed, turret=False)
            self.check_prepare(model, LIKE)
            self.check_prepare(model, dict(LIKE, aircraft=True))
            self.check_prepare(model, {"length": 50.0, "pivot": (0.0, 0.0), "ground": 1.0})
        flat = made_up(7, turret=False)
        level = [(x, y, 2.0) for x, y, _z in flat.meshes[0].positions]   # every point as high: the sort keeps order
        self.check_prepare(modelin.Model([modelin.Mesh("body", level, flat.meshes[0].triangles)], []),
                           dict(LIKE, aircraft=True))

    def test_facing_and_the_whole_fit_on_many_shapes(self):
        """Which way a model faces is modelin.facing's own (its rules have one home): tanks with a long gun at either
        end, a short one, stowage behind, gun and turret named or not, trucks, a facing pinned by hand; jets with one
        fin or two at either end, swept wings under a canopy higher than all else, biplanes and triplanes whose top
        wing is highest, a flat top wing, a plane parked tail down with a propeller blade highest, a monoplane whose
        wingtips are highest; each along x and along y, both ways round, from a .glb and from a .3ds, fitted to two or
        three units. Read, fitted and saved on whole arrays, each gives the loops' model, parts, report and .glb bytes,
        its facing modelin.facing's for the model the loops read."""
        seen = {False: set(), True: set()}
        count = 0
        with tempfile.TemporaryDirectory() as d:
            models, pictures = Path(d, "models"), Path(d, "pictures")
            models.mkdir()
            pictures.mkdir()
            (pictures / "PAINT.png").write_bytes(picture(4, 8, 3))
            for k, (name, (aircraft, make)) in enumerate(SHAPES.items()):
                for quarter in range(4):
                    parts = placed(make(), quarter, 100 * k + quarter)
                    for source, data in (("glb", shape_glb(parts, k)), ("3ds", shape_3ds(parts, k))):
                        path = models / f"shape{k}_{quarter}.{source}"
                        path.write_bytes(data)
                        with loops():
                            plain = modelin.read_model(path)
                        model = modelin.read_model(path)
                        self.same(model_bytes(model), model_bytes(plain), (name, quarter, source))
                        for like in PLANE_LIKES if aircraft else GROUND_LIKES:
                            what = (name, quarter, source, like["length"], like.get("width"), like.get("facing"))
                            with loops():
                                facing = modelin.facing(plain, modelin.roles(plain), like)
                                want = modelin.prepare(plain, [pictures], like)
                                want_glb = glb_bytes(want)
                            # (a second unit: the model's points read from its lists, the first took its arrays)
                            here = modelinnp.prepare(modelin, model, [pictures], like, 1.0, 1024)
                            self.assertIsNotNone(here, what)        # (the whole arrays fitted it, not the loops)
                            self.same(prep_bytes(here), prep_bytes(want), what)
                            self.same(glb_bytes(here), want_glb, what)
                            self.assertEqual(here.report["facing"], ("xy"[facing[0]], facing[1]), what)
                            seen[aircraft].add(facing)
                            count += 1
        self.assertEqual(count, sum(4 * 2 * len(PLANE_LIKES if aircraft else GROUND_LIKES)
                                    for aircraft, _make in SHAPES.values()))
        every_way = {(0, 1), (0, -1), (1, 1), (1, -1)}
        self.assertEqual((seen[False], seen[True]), (every_way, every_way))     # (the shapes face every way)

    def test_what_is_left_to_the_loops(self):
        """Numbers that aren't Python floats (ints, as a hand-made model may have), a point that isn't finite, a broken
        index: the whole arrays leave the model to the loops, which give their own answer or error."""
        model = made_up(8)
        ints = modelin.Model([modelin.Mesh("body", [(int(x), int(y), int(z)) for x, y, z in model.meshes[0].positions],
                                           model.meshes[0].triangles)], [])
        self.assertIsNone(modelinnp.prepare(modelin, ints, [], LIKE, 1.0, 1024))
        with loops():
            want = prep_bytes(modelin.prepare(ints, [], LIKE))
        self.same(prep_bytes(modelin.prepare(ints, [], LIKE)), want)
        broken = modelin.Model([modelin.Mesh("body", model.meshes[0].positions, [(0, 1, 10 ** 6)])], [])
        self.assertIsNone(modelinnp.prepare(modelin, broken, [], LIKE, 1.0, 1024))
        with self.assertRaises(IndexError):
            modelin.prepare(broken, [], LIKE)
        nan = modelin.Model([modelin.Mesh("body", [(math.nan, 0.0, 0.0)] + model.meshes[0].positions[1:],
                                          model.meshes[0].triangles)], [])
        self.assertIsNone(modelinnp.prepare(modelin, nan, [], LIKE, 1.0, 1024))
        flat = modelin.Model([modelin.Mesh("body", [(1.0, 1.0, 0.0)] * 3, [(0, 1, 2)])], [])
        with self.assertRaisesRegex(modelin.ModelError, "no length"):
            modelin.prepare(flat, [], LIKE)

    def test_a_part_changed_after_fitting_is_saved_the_same(self):
        """write_glb on parts as the markings tool may leave them: ints among the uvs (left to the loops), more points,
        a point moved, a normal swapped for an equal one, a triangle taken away: a list changed in any way is read
        again, number by number; one left as it was is taken as the array it was made from."""
        prep = modelin.prepare(made_up(9), [], LIKE)
        self.assertGreaterEqual(len(prep.parts), 4)
        for part in prep.parts:
            for field in ("positions", "normals", "uvs", "triangles"):
                self.assertIsNotNone(modelinnp._kept(part, field), field)
        prep.parts[0].uvs[0] = (0, 1)
        prep.parts[1].positions.append((1.0, 2.0, 3.0))
        x, y, z = prep.parts[2].positions[5]
        prep.parts[2].positions[5] = (x, y, z + 0.25)
        prep.parts[2].normals[0] = tuple(list(prep.parts[2].normals[0]))     # (an equal tuple, another object)
        prep.parts[3].triangles.pop()
        self.assertIsNone(modelinnp.part_buffers(prep.parts[0], 0.01, True))
        self.assertIsNone(modelinnp._kept(prep.parts[1], "positions"))
        self.assertIsNone(modelinnp._kept(prep.parts[2], "positions"))
        self.assertIsNone(modelinnp._kept(prep.parts[2], "normals"))
        self.assertIsNone(modelinnp._kept(prep.parts[3], "triangles"))
        self.assertIsNotNone(modelinnp._kept(prep.parts[3], "positions"))
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d, "a", "m.glb"), Path(d, "b", "m.glb")
            modelin.write_glb(prep, a)
            with loops():
                modelin.write_glb(prep, b)
            self.same(a.read_bytes(), b.read_bytes())

    def test_empty_primitives_read_the_same(self):
        """A primitive with no points at all, and one whose two indices make no triangle: empty lists either way."""
        from rusemod.gltf import FLOAT, USHORT, _Glb
        g = _Glb()
        empty = {"attributes": {"POSITION": g.accessor([], "VEC3", FLOAT), "NORMAL": g.accessor([], "VEC3", FLOAT),
                                "TEXCOORD_0": g.accessor([], "VEC2", FLOAT)},
                 "indices": g.accessor([], "SCALAR", USHORT, 34963)}
        pts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        short = {"attributes": {"POSITION": g.accessor(pts, "VEC3", FLOAT)},
                 "indices": g.accessor([0, 1], "SCALAR", USHORT, 34963)}
        g.doc["meshes"] = [{"name": "nothing", "primitives": [empty, short]}]
        g.doc["nodes"] = [{"mesh": 0}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "empty.glb")
            path.write_bytes(g.to_bytes())
            doc, binary = modelin.glb_document(path.read_bytes())
            for prim in (empty, short):
                self.assertIsNotNone(modelinnp.mesh(modelin, doc, binary, prim, modelin._IDENTITY, "m"))
            with loops():
                want = modelin.read_model(path)
            got = modelin.read_model(path)
            self.same(model_bytes(got), model_bytes(want))
            self.assertEqual([(len(m.positions), len(m.triangles)) for m in got.meshes], [(0, 0), (3, 0)])

    def test_a_mesh_changed_after_reading_is_fitted_the_same(self):
        """A model read on whole arrays and changed before fitting (a point moved, a triangle added): fitted from its
        lists as they are now."""
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "model.glb")
            path.write_bytes(self.glb(4))
            model = modelin.read_model(path)
            self.assertIsNotNone(modelinnp._kept(model.meshes[0], "positions"))
            x, y, z = model.meshes[0].positions[3]
            model.meshes[0].positions[3] = (x + 1.5, y, z)
            model.meshes[1].triangles.append((0, 1, 2))
            model.meshes[1].face_materials.append(0)
            self.assertIsNone(modelinnp._kept(model.meshes[0], "positions"))
            self.assertIsNotNone(modelinnp._kept(model.meshes[2], "positions"))
            like = {"length": 600.0, "width": 250.0, "pivot": (0.0, 0.0), "ground": 0.0}
            self.assertIsNotNone(modelinnp.prepare(modelin, model, [Path(d)], like, 1.0, 1024))
            self.assertIsNone(modelinnp._kept(model.meshes[2], "positions"))      # (fitting took it)
            with loops():
                want = prep_bytes(modelin.prepare(model, [Path(d)], like))
            self.same(prep_bytes(modelin.prepare(model, [Path(d)], like)), want)

    def test_pictures_sampled_to_a_power_of_two(self):
        for w, h, nw, nh in ((6, 5, 8, 4), (3, 7, 4, 8), (1, 1, 4, 4), (100, 3, 128, 4), (5, 300, 4, 256)):
            px = bytes(random.Random(w * h).randrange(256) for _ in range(w * h * 4))
            with loops():
                want = modelin._sized(w, h, px, 1024)
            self.assertEqual(want[:2], (nw, nh))
            self.assertEqual(modelinnp.nearest(px, w, h, nw, nh), want[2])
            self.assertEqual(modelin._sized(w, h, px, 1024), want)

    # --- .glb files ---
    def glb(self, seed: int) -> bytes:
        """A .glb with what files have: nodes turned, scaled and moved (TRS, a matrix, whole numbers in the JSON),
        nested; a mesh of two primitives; one primitive's data interleaved (byteStride); indices of 8, 16 and 32 bits
        and none; primitives without normals or uvs; lines (not read); positions as normalized shorts (left to the
        loops)."""
        from rusemod.gltf import FLOAT, UBYTE, UINT, USHORT, _Glb
        rnd = random.Random(seed)
        g = _Glb()
        tex = g.image(picture(8, 8, seed), "paint")
        g.doc["materials"] = [{"name": "Paint", "pbrMetallicRoughness": {"baseColorTexture": {"index": tex}}},
                              {"name": "Plain", "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.25, 1.0, 1.0]}}]

        def prim(n, index=UINT, own_normals=True, uvs=True, interleaved=False, material=0, mode=None):
            pts = points(rnd, n, (-5, -5, -5), (5, 5, 5))
            nrm = normals(rnd, n)
            uv = [(f32(rnd.random()), f32(rnd.random())) for _ in range(n)]
            if interleaved:
                view = g.view(b"".join(struct.pack("<3f3f2f", *p, *q, *u) for p, q, u in zip(pts, nrm, uv)), 34962)
                g.doc["bufferViews"][view]["byteStride"] = 32
                attrs = {}
                for name, at, kind in (("POSITION", 0, "VEC3"), ("NORMAL", 12, "VEC3"), ("TEXCOORD_0", 24, "VEC2")):
                    g.doc["accessors"].append({"bufferView": view, "byteOffset": at, "componentType": FLOAT,
                                               "count": n, "type": kind})
                    attrs[name] = len(g.doc["accessors"]) - 1
            else:
                attrs = {"POSITION": g.accessor(pts, "VEC3", FLOAT)}
                if own_normals:
                    attrs["NORMAL"] = g.accessor(nrm, "VEC3", FLOAT)
                if uvs:
                    attrs["TEXCOORD_0"] = g.accessor(uv, "VEC2", FLOAT)
            out = {"attributes": attrs, "material": material}
            if index is not None:
                idx = [i for t in triangles(rnd, n, 2 * n) for i in t] + [0]    # (a last, lone index: not a triangle)
                out["indices"] = g.accessor(idx, "SCALAR", index, 34963)
            if mode is not None:
                out["mode"] = mode
            return out

        quantized = prim(12)
        shorts = [tuple(rnd.randrange(-32767, 32767) for _ in range(3)) for _ in range(12)]
        g.doc["accessors"].append({"bufferView": g.view(b"".join(struct.pack("<3h2x", *s) for s in shorts)),
                                   "componentType": 5122, "normalized": True, "count": 12, "type": "VEC3"})
        quantized["attributes"]["POSITION"] = len(g.doc["accessors"]) - 1
        g.doc["bufferViews"][g.doc["accessors"][-1]["bufferView"]]["byteStride"] = 8
        g.doc["meshes"] = [{"name": "hull", "primitives": [prim(40), prim(30, USHORT, uvs=False, material=1)]},
                           {"name": "turret", "primitives": [prim(25, UBYTE, own_normals=False)]},
                           {"primitives": [prim(20, None, interleaved=True)]},
                           {"name": "lines", "primitives": [prim(10, mode=1)]},
                           {"name": "quantized", "primitives": [quantized]}]
        angle = rnd.uniform(0, math.pi)
        q = [math.sin(angle / 2) * c for c in (0.36, 0.48, 0.8)] + [math.cos(angle / 2)]
        matrix = [f32(rnd.uniform(-2, 2)) for _ in range(12)] + [0.5, -1.25, 3.0, 1.0]
        g.doc["nodes"] = [{"name": "Body", "mesh": 0, "translation": [1.5, -2.0, 0.25], "rotation": q,
                           "scale": [1.0, 2.0, 0.5], "children": [1, 2]},
                          {"mesh": 1, "matrix": matrix},
                          {"name": "plain", "mesh": 2, "rotation": [0, 0, 0, 1], "translation": [0, 0, 1]},
                          {"mesh": 3}, {"name": "q", "mesh": 4, "scale": [0.001, 0.001, 0.001]}]
        g.doc["scenes"] = [{"nodes": [0, 3, 4]}]
        g.doc["scene"] = 0
        return g.to_bytes()

    def test_a_glb_reads_the_same(self):
        for seed in (1, 2, 3):
            with tempfile.TemporaryDirectory() as d:
                path = Path(d, "model.glb")
                path.write_bytes(self.glb(seed))
                doc, binary = modelin.glb_document(path.read_bytes())
                taken = [modelinnp.mesh(modelin, doc, binary, p, modelin._IDENTITY, "m") is not None
                         for gm in doc["meshes"] for p in gm["primitives"]]
                self.assertEqual(taken, [True, True, True, True, True, False])  # (the shorts: the loops read them)
                with loops():
                    want = modelin.read_model(path)
                got = modelin.read_model(path)
                self.same(model_bytes(got), model_bytes(want), seed)
                self.assertEqual([m.name for m in got.meshes], ["Body.0", "Body.1", "turret", "plain", "q"])
                like = {"length": 600.0, "width": 250.0, "pivot": (0.0, 0.0), "ground": 0.0}
                with loops():
                    prep = modelin.prepare(want, [Path(d)], like)
                self.same(prep_bytes(modelin.prepare(got, [Path(d)], like)), prep_bytes(prep))
                out = Path(d, "fitted.glb")
                modelin.write_glb(prep, out)
                again_want = None
                with loops():
                    again_want = modelin.read_model(out)
                self.same(model_bytes(modelin.read_model(out)), model_bytes(again_want), "the importer's own .glb")


if __name__ == "__main__":
    unittest.main()
