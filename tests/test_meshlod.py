"""A map asset's lighter versions (rusemod.meshlod) on made-up shapes: off by at most a cell where solid, no crack
along a picture seam, leaf cards thinned and grown to cover what they did, the materials kept, and a version saved as
.glb and read back as it was."""
import math
import tempfile
import unittest
from pathlib import Path

from rusemod.dxt import png_bytes
from rusemod.modelin import Material, Mesh, Model, read_model

try:  # a model's medium and far versions are made on whole arrays
    from rusemod import meshlod
    from rusemod.numpy2 import np
except ImportError:
    meshlod = np = None

TMP = None   # the system's temp folder (TEMP)


def grid(n: int, size: float, bump: float = 0.0, u0: float = 0.0):
    """A square `size` across of n x n cells, z a gentle bump of height `bump`: points, normals, UVs, triangles."""
    xs = np.linspace(0.0, size, n + 1)
    x, y = np.meshgrid(xs, xs, indexing="ij")
    z = bump * np.sin(x / size * math.pi) * np.sin(y / size * math.pi)
    pos = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1)
    uv = np.stack([u0 + x.ravel() / size * 0.5, y.ravel() / size], axis=1)
    k = np.arange((n + 1) * (n + 1)).reshape(n + 1, n + 1)
    a, b, c, d = k[:-1, :-1].ravel(), k[1:, :-1].ravel(), k[1:, 1:].ravel(), k[:-1, 1:].ravel()
    tri = np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, d], 1)])
    nrm = np.tile([0.0, 0.0, 1.0], (len(pos), 1))
    return pos, nrm, uv, tri


def cards(count: int, side: float, seed: int = 1):
    """`count` separate square leaf cards `side` across, scattered in a 2 m box: two triangles each."""
    rng = np.random.default_rng(seed)
    pos, tri = [], []
    for k in range(count):
        o = rng.random(3) * 2.0
        pos += [o, o + [side, 0, 0], o + [side, 0, side], o + [0, 0, side]]
        tri += [[4 * k, 4 * k + 1, 4 * k + 2], [4 * k, 4 * k + 2, 4 * k + 3]]
    pos = np.array(pos)
    return pos, np.tile([0.0, -1.0, 0.0], (len(pos), 1)), np.tile([[0, 0], [1, 0], [1, 1], [0, 1]], (count, 1)) \
        .astype(float), np.array(tri)


def area(pos, tri):
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


@unittest.skipIf(meshlod is None, "numpy isn't here: rusemod.meshlod needs it (the apps carry it)")
class Pixels(unittest.TestCase):
    def test_one_pixel_where_each_ring_starts(self):
        self.assertAlmostEqual(meshlod.pixel(77.0), 0.0591, delta=1e-4)   # 5.9 cm
        self.assertAlmostEqual(meshlod.pixel(385.0), 0.2953, delta=1e-4)  # 29.5 cm
        self.assertEqual(meshlod.RINGS, {"medium": 77.0, "far": 385.0})


@unittest.skipIf(meshlod is None, "numpy isn't here: rusemod.meshlod needs it (the apps carry it)")
class Merged(unittest.TestCase):
    def test_fewer_triangles_within_a_cell(self):
        pos, nrm, uv, tri = grid(60, 3.0, bump=0.4)
        mat = np.zeros(len(tri), dtype=np.int64)
        cell = 0.25
        p, n, u, t, m = meshlod.cluster(pos, nrm, uv, tri, mat, cell, 1.0)
        self.assertLess(len(t), len(tri) / 20)
        self.assertGreater(len(t), 50)
        # every new point lies within a cell of the surface it stands for (the bump, sampled finely)
        surface = 0.4 * np.sin(p[:, 0] / 3.0 * math.pi) * np.sin(p[:, 1] / 3.0 * math.pi)
        self.assertLess(float(np.abs(p[:, 2] - surface).max()), cell)
        self.assertLess(float(np.abs(p[:, :2].min(axis=0)).max()), cell)
        self.assertLess(float(np.abs(p[:, :2].max(axis=0) - 3.0).max()), cell)
        self.assertTrue(np.allclose(np.linalg.norm(n, axis=1), 1.0))
        self.assertEqual(set(m.tolist()), {0})
        # (its edges come in by at most a cell: the area within what that takes off a 3 m square)
        self.assertAlmostEqual(area(p, t), area(pos, tri), delta=4 * 3.0 * cell / 2)

    def test_no_crack_along_a_picture_seam(self):
        """Two halves of one surface (each its own picture island: their points at the seam the same places, other
        UVs): merged, the halves still meet: no edge along the seam is open (used by one triangle only)."""
        left, nl, ul, tl = grid(20, 1.0, bump=0.2)
        right, nr, ur, tr = grid(20, 1.0, bump=0.2, u0=0.5)
        right[:, 0] += 1.0
        right[:, 2] = 0.2 * np.sin((right[:, 0] - 1.0) * math.pi) * np.sin(right[:, 1] * math.pi)
        pos = np.concatenate([left, right])
        uv = np.concatenate([ul, ur])
        tri = np.concatenate([tl, tr + len(left)])
        nrm = np.concatenate([nl, nr])
        p, _n, _u, t, _m = meshlod.cluster(pos, nrm, uv, tri, np.zeros(len(tri), dtype=np.int64), 0.15, 1.0 / 64)
        key = {q: k for k, q in enumerate(map(tuple, np.round(p, 9).tolist()))}
        place = np.array([key[q] for q in map(tuple, np.round(p, 9).tolist())])
        edges = np.sort(np.concatenate([place[t[:, [0, 1]]], place[t[:, [1, 2]]], place[t[:, [2, 0]]]]), axis=1)
        e, n = np.unique(edges, axis=0, return_counts=True)
        open_mid = [(p[a], p[b]) for (a, b), c in zip(e, n) if c == 1
                    and 0.3 < p[a][0] < 1.7 and 0.3 < p[b][0] < 1.7 and 0.2 < p[a][1] < 0.8 and 0.2 < p[b][1] < 0.8]
        self.assertTrue(any(abs(q[0] - 1.0) < 0.1 for q in p))
        self.assertEqual(open_mid, [])

    def test_materials_kept_apart(self):
        pos, nrm, uv, tri = grid(10, 1.0)
        mat = (np.arange(len(tri)) % 2).astype(np.int64)
        _p, _n, _u, t, m = meshlod.cluster(pos, nrm, uv, tri, mat, 0.3, 1.0)
        self.assertEqual(set(m.tolist()), {0, 1})


@unittest.skipIf(meshlod is None, "numpy isn't here: rusemod.meshlod needs it (the apps carry it)")
class Thinned(unittest.TestCase):
    def test_cards_kept_whole_and_grown(self):
        pos, nrm, uv, tri = cards(400, 0.05)
        mat = np.ones(len(tri), dtype=np.int64)
        p, _n, _u, t, m = meshlod.thin(pos, nrm, uv, tri, mat, 0.25, seed=3)
        kept = len(t) // 2
        self.assertTrue(60 <= kept <= 140, kept)              # about a quarter of 400
        self.assertEqual(len(t) % 2, 0)                       # (whole cards: both triangles)
        self.assertAlmostEqual(area(p, t), area(pos, tri), delta=0.35 * area(pos, tri))
        sides = np.linalg.norm(p[t[0::2, 1]] - p[t[0::2, 0]], axis=1)   # (each card's first triangle: a side)
        self.assertTrue(np.allclose(sides, 0.05 * 2.0))       # each grown by 1 / sqrt(0.25)
        self.assertEqual(set(m.tolist()), {1})

    def test_a_kept_card_never_bigger_than_half_the_foliage(self):
        """A tiny plant thinned to a card or two: each grows no wider than half of all its cards' box (else covering
        what it did would make one card bigger than the plant: shrub_04, 58 cm, its far card, 2026-10-17)."""
        pos, nrm, uv, tri = cards(40, 0.01)                   # (40 cards of 1 cm in a 2 m box)
        most = meshlod.card_growth_most(pos, tri)
        span = float((pos.max(axis=0) - pos.min(axis=0)).max())
        self.assertAlmostEqual(most, 0.5 * span / 0.01, places=6)
        p, _n, _u, t, _m = meshlod.thin(pos, nrm, uv, tri, np.zeros(len(tri), dtype=np.int64), 1e-6, seed=1,
                                        grow_most=most)
        side = float(np.linalg.norm(p[t[0, 1]] - p[t[0, 0]]))
        self.assertAlmostEqual(side, 0.01 * most, places=6)   # (not 0.01 * 1000)
        self.assertLessEqual(side, 0.5 * span + 1e-9)

    def test_a_farther_rings_cards_are_a_nearer_rings(self):
        """The same draw for every ring: what a farther ring keeps is among what a nearer one kept, even when it keeps
        only the one card it can't do without."""
        pos, nrm, uv, tri = cards(200, 0.02)
        mat = np.zeros(len(tri), dtype=np.int64)
        middles = []
        for keep in (0.5, 0.05, 1e-9):
            p, _n, _u, t, _m = meshlod.thin(pos, nrm, uv, tri, mat, keep, seed=7, grow_most=1.0)
            middles.append({tuple(np.round(p[t[k]].mean(axis=0), 9)) for k in range(0, len(t), 2)})
        self.assertTrue(middles[2] <= middles[1] <= middles[0])
        self.assertEqual(len(middles[2]), 1)

    def test_how_many_kept(self):
        pos, _n, _u, tri = cards(10, 0.05)
        want = (meshlod.LEAF_PIXELS * meshlod.pixel(77.0)) ** 2
        self.assertAlmostEqual(meshlod.card_keep(pos, tri, 77.0), 0.05 ** 2 / want)
        big, _n, _u, tri2 = cards(10, 1.0)
        self.assertEqual(meshlod.card_keep(big, tri2, 77.0), 1.0)   # (never shrunk)


@unittest.skipIf(meshlod is None, "numpy isn't here: rusemod.meshlod needs it (the apps carry it)")
class BothSides(unittest.TestCase):
    def test_every_triangle_also_the_other_way(self):
        """A surface with no back gets one: each triangle again, turned round, on points of its own facing back."""
        mesh = Mesh("m", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [(0, 1, 2)],
                    [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [0], [(0.0, 0.0, 1.0)] * 3)
        two = meshlod.both_sides(Model([mesh], [Material("a")], "scan"), offset=0.0).meshes[0]
        self.assertEqual(two.triangles, [(0, 1, 2), (3, 5, 4)])
        self.assertEqual(two.positions[3:], two.positions[:3])
        self.assertEqual(two.normals[3:], [(-0.0, -0.0, -1.0)] * 3)
        self.assertEqual((two.uvs[3:], two.face_materials), (two.uvs[:3], [0, 0]))
        p = np.array(two.positions)
        front = np.cross(p[1] - p[0], p[2] - p[0])
        back = np.cross(p[5] - p[3], p[4] - p[3])
        self.assertTrue(np.allclose(front, -back))   # (the copy faces the other way)
        # by default the back sits behind the front by BACK_OFFSET of the longest side (never right on it: the game
        # drew such fronts with dark, smeared triangles up close)
        moved = meshlod.both_sides(Model([mesh], [Material("a")], "scan")).meshes[0]
        self.assertEqual(moved.positions[:3], mesh.positions)
        self.assertTrue(np.allclose(np.array(moved.positions[3:]),
                                    np.array(mesh.positions) - [0.0, 0.0, meshlod.BACK_OFFSET * 1.0]))


@unittest.skipIf(meshlod is None, "numpy isn't here: rusemod.meshlod needs it (the apps carry it)")
class Versions(unittest.TestCase):
    def model(self):
        pos, nrm, uv, tri = grid(40, 2.0, bump=0.3)
        lp, ln, lu, lt = cards(300, 0.03)
        lp = lp + [0.0, 0.0, 1.0]
        mesh = Mesh("tree", [tuple(x) for x in np.concatenate([pos, lp]).tolist()],
                    [tuple(x) for x in np.concatenate([tri, lt + len(pos)]).tolist()],
                    [tuple(x) for x in np.concatenate([uv, lu]).tolist()],
                    [0] * len(tri) + [1] * len(lt), [tuple(x) for x in np.concatenate([nrm, ln]).tolist()])
        return Model([mesh], [Material("bark", "bark_diff_2k.png"), Material("leaf", "leaf_diff_2k.png",
                                                                             cutout="MASK")], "test")

    def test_each_ring_lighter_the_materials_kept(self):
        model = self.model()
        full = model.counts()[1]
        mid = meshlod.version(model, "medium")
        far = meshlod.version(model, "far")
        self.assertLess(mid.counts()[1], full)
        self.assertLess(far.counts()[1], mid.counts()[1])
        self.assertIs(mid.materials, mid.materials)
        self.assertEqual([m.name for m in mid.materials], ["bark", "leaf"])
        self.assertEqual(mid.source, "test (medium)")
        leaf_tris = [sum(1 for f in m.face_materials if f == 1) for m in mid.meshes]
        self.assertGreater(sum(leaf_tris), 0)
        self.assertEqual(sum(leaf_tris) % 2, 0)   # (whole cards)

    def test_saved_and_read_back(self):
        """A version saved as .glb: its points, UVs and triangles read back as made (glTF's y up and v down undone);
        its pictures the model's own files beside it, a cut-out material MASK."""
        model = meshlod.version(self.model(), "medium")
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            for name in ("bark_diff_2k.png", "leaf_diff_2k.png"):
                (Path(d) / name).write_bytes(png_bytes(bytes([60, 90, 30] * 16), 4, 4))
            path = Path(d) / "tree_medium.glb"
            path.write_bytes(meshlod.glb_bytes(model, d))
            back = read_model(path)
        self.assertEqual(back.counts(), model.counts())
        self.assertEqual([m.picture for m in back.materials], ["bark_diff_2k.png", "leaf_diff_2k.png"])
        self.assertEqual([m.cutout for m in back.materials], ["", "MASK"])
        for made, got in zip(model.meshes, back.meshes):   # (a material a mesh, in order: the same points, in order)
            self.assertTrue(np.allclose(np.array(made.positions), np.array(got.positions), atol=1e-5))
            self.assertTrue(np.allclose(np.array(made.uvs), np.array(got.uvs), atol=1e-6))
            self.assertEqual(made.triangles, got.triangles)


if __name__ == "__main__":
    unittest.main()
