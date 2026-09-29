"""Terrain edits (rusemod.terrain_edit): brush strokes on a made-up map whose four ground files change together.

The map is 3,000 units square: a close-up mesh of 3 x 3 cells with 11 x 11 points each, a far mesh with 5 x 5 points
per cell, a gameplay ground whose points are the close-up mesh's (same bounds), and a camera floor on the far mesh's
points with a taller height range. Heights step by 0.1 in the meshes (-100 to 3,176.7)."""
import math
import struct
import unittest

from fixtures import make_edat
from test_kdt import hand_storage, make_kdt
from test_tms import make_tms
from rusemod.brush import Stroke
from rusemod.edat import Edat
from rusemod.kdt import Kdt
from rusemod.terrain_edit import FILES, edit_map
from rusemod.tms import Q_MAX, Cell, Patch, Tms, VertexBuffer, encode_indices

CAMERA_Z = (-500.0, 5000.0)


def bumpy(x: int, y: int) -> int:
    """A ground height (quantized) with small bumps everywhere."""
    return 10000 + (x * 7 + y * 13) % 997


def tree(groups, bounds_min, bounds_max) -> bytes:
    """A .kdt with one subtree per group of points (quantized x, y, z), every normal straight up."""
    positions = [list(g) for g in groups]
    parents = [[0] + list(range(len(g) - 1)) for g in groups]
    normals = [[(0.0, 0.0, 1.0)] * len(g) for g in groups]
    n = len(groups)
    opaque = {"indices": [b"I" * 6] * n, "trilists": [b"T" * 4] * n, "trees": [b"S" * 10] * n, "main": b"MAINNODE" * 2}
    storage, offsets = hand_storage(positions, parents, normals, opaque)
    k = Kdt(make_kdt(storage, offsets, subtree_count=n, triangle_count=99, bounds_min=bounds_min))
    k.bounds_min, k.bounds_max = tuple(bounds_min), tuple(bounds_max)
    return k.to_bytes()


CLIFF_WEST = 5 * 11 + 3    # centre cell point at x 1300, y 1500 (row 5, column 3 of its 11 x 11 grid)
CLIFF_EAST = 5 * 11 + 6    # centre cell point at x 1600, y 1500
CLIFF_DROP = 300           # quanta (30 units) from a cliff's top down to its foot


def cliff_mesh(high: bytes) -> bytes:
    """`high` with a little cliff in its centre cell, as the shipped close-up meshes have (every one of the 32 holds
    points that share x and y at different heights): under two of the cell's grid points it also holds a second
    point, the cliff's foot, at the same x and y and CLIFF_DROP lower, joined to the top and the top's east
    neighbour by a wall triangle. The foot under CLIFF_WEST comes first in the cell, the one under CLIFF_EAST last."""
    t = Tms(high)
    c = t.cells[4]
    grid, nor, par, tri = c.positions(), c.normals(), c.parents(), c.triangles(0)

    def foot(i):
        x, y, z, w = grid[i]
        return x, y, z - CLIFF_DROP, w

    pos = [foot(CLIFF_WEST)] + list(grid) + [foot(CLIFF_EAST)]
    normals = [nor[CLIFF_WEST]] + list(nor) + [nor[CLIFF_EAST]]
    parents = [0, 0] + [p + 1 for p in par[1:]] + [CLIFF_EAST + 1]
    tri = ([0, CLIFF_WEST + 1, CLIFF_WEST + 2] + [i + 1 for i in tri]
           + [len(pos) - 1, CLIFF_EAST + 1, CLIFF_EAST + 2])
    cell = Cell(c.flags, len(pos), VertexBuffer.build(pos, normals, parents).to_bytes(), [encode_indices(tri)],
                [len(tri)], b"")
    cell.set_patches([Patch(0, len(pos), 0, len(tri), 0, 0, 0.0, 0.0)])
    t.cells[4] = cell
    return t.to_bytes()


def make_map(camera=True, cliff=False) -> dict:
    """The four ground files of a made-up map, by member path. `cliff`: the close-up mesh has the little cliff of
    `cliff_mesh`, and the gameplay ground sits on its tops."""
    high = make_tms(gw=3, gh=3, n=11, zf=bumpy)
    low = make_tms(gw=3, gh=3, n=5, zf=bumpy)
    hd, ld = Tms(high), Tms(low)
    b = hd.bounds
    cells = [[p[:3] for p in c.positions()] for c in hd.cells]
    ground = tree([cells[0] + cells[1] + cells[2], cells[3] + cells[4] + cells[5], cells[6] + cells[7] + cells[8]],
                  (b[0], b[1], b[2]), (b[3], b[4], b[5]))
    if cliff:
        high = cliff_mesh(high)
    lo_z, hi_z = CAMERA_Z
    cam_points = []
    for c in ld.cells:
        for qx, qy, qz, _w in c.positions():
            z = ld.to_world(2, qz)
            cam_points.append((qx, qy, round((z - lo_z) * 32767 / (hi_z - lo_z))))
    files = {FILES["highdef"]: high, FILES["lowdef"]: low, FILES["ground"]: ground}
    if camera:
        files[FILES["camera"]] = tree([cam_points[:40], cam_points[40:]], (b[0], b[1], lo_z), (b[3], b[4], hi_z))
    return files


def make_map_pack(camera=True, cliff=False) -> bytes:
    """The made-up map as a map pack (EDAT), its files under output\\ like the game's."""
    files = make_map(camera, cliff)
    return make_edat([("dir", "output\\", [("file", member.split("\\")[-1], data) for member, data in files.items()])])


def reader(files: dict):
    return lambda member: files.get(member)


def edge(qx, qy) -> bool:
    return qx in (0, Q_MAX) or qy in (0, Q_MAX)


class Together(unittest.TestCase):
    def setUp(self):
        self.files = make_map()
        self.hd, self.ld = Tms(self.files[FILES["highdef"]]), Tms(self.files[FILES["lowdef"]])
        self.hill = Stroke("hill", 1500.0, 1500.0, 600.0, height=400.0)

    def lift(self, x, y) -> float:
        d2 = (x - 1500.0) ** 2 + (y - 1500.0) ** 2
        return 400.0 * (1 - d2 / 360000.0) ** 2 if d2 < 360000.0 else 0.0

    def test_a_hill_raises_all_four_files_together(self):
        changed, notes = edit_map(reader(self.files), [self.hill], "Test")
        self.assertEqual(set(changed), set(FILES.values()))
        self.assertIn("Test: 1 stroke(s); points moved: close-up mesh", notes[0])
        hd, ld = Tms(changed[FILES["highdef"]]), Tms(changed[FILES["lowdef"]])
        for old_mesh, new_mesh in ((self.hd, hd), (self.ld, ld)):
            for a, b in zip(old_mesh.cells, new_mesh.cells):
                for p, q in zip(a.positions(), b.positions()):
                    self.assertEqual((p[0], p[1], p[3]), (q[0], q[1], q[3]))
                    x, y, z = (old_mesh.to_world(k, p[k]) for k in range(3))
                    want = p[2] if edge(p[0], p[1]) else old_mesh.to_quant(2, z + self.lift(x, y))
                    self.assertEqual(q[2], want)
        # the gameplay ground's points are the close-up mesh's, so they get exactly the same new heights
        heights = {(p[0], p[1]): p[2] for c in hd.cells for p in c.positions()}
        ground = Kdt(changed[FILES["ground"]])
        for s in range(len(ground.subtrees)):
            for qx, qy, qz in ground.positions(s):
                self.assertEqual(qz, heights[(qx, qy)])
        # the camera floor has its own height range: the same lift, to within its own step
        old_cam, cam = Kdt(self.files[FILES["camera"]]), Kdt(changed[FILES["camera"]])
        step = (CAMERA_Z[1] - CAMERA_Z[0]) / 32767
        for s in range(len(cam.subtrees)):
            for p, q in zip(old_cam.positions(s), cam.positions(s)):
                x, y = cam.to_world(0, p[0]), cam.to_world(1, p[1])
                lift = 0.0 if edge(p[0], p[1]) else self.lift(x, y)
                self.assertAlmostEqual(cam.to_world(2, q[2]), old_cam.to_world(2, p[2]) + lift, delta=step)
        # the corner cell is out of reach and keeps its exact bytes; the moved cell's patch bounds reach the top
        self.assertEqual(hd.cells[0].vb, self.hd.cells[0].vb)
        centre = hd.cells[4]
        top = max(hd.to_world(2, p[2]) for p in centre.positions())
        self.assertAlmostEqual(max(p.zhi for p in centre.patch_list()), top, 1)

    def test_the_same_strokes_give_the_same_bytes(self):
        strokes = [self.hill, Stroke("crater", 900.0, 2100.0, 300.0, height=150.0),
                   Stroke("smooth", 1500.0, 1500.0, 900.0, weight=0.8)]
        self.assertEqual(edit_map(reader(make_map()), strokes)[0], edit_map(reader(make_map()), strokes)[0])

    def test_a_plateau_is_level_across_its_middle_in_every_file(self):
        changed, _ = edit_map(reader(self.files), [Stroke("plateau", 1500.0, 1500.0, 800.0, level=2500.0)])
        for key in ("highdef", "lowdef"):
            mesh = Tms(changed[FILES[key]])
            inner = [p[2] for c in mesh.cells for p in c.positions()
                     if math.hypot(mesh.to_world(0, p[0]) - 1500, mesh.to_world(1, p[1]) - 1500) < 400]
            self.assertTrue(inner)
            self.assertEqual(set(inner), {mesh.to_quant(2, 2500.0)}, key)
        for key in ("ground", "camera"):
            k = Kdt(changed[FILES[key]])
            inner = [p[2] for s in range(len(k.subtrees)) for p in k.positions(s)
                     if math.hypot(k.to_world(0, p[0]) - 1500, k.to_world(1, p[1]) - 1500) < 400]
            self.assertTrue(inner)
            self.assertEqual(set(inner), {k.to_quant(2, 2500.0)}, key)

    def test_a_ramp_slopes_evenly_from_end_to_end_in_every_file(self):
        ramp = Stroke("ramp", 600.0, 1500.0, 400.0, level=1000.0, x2=2400.0, y2=1500.0, level2=2500.0)
        changed, _ = edit_map(reader(self.files), [ramp])
        self.assertEqual(set(changed), set(FILES.values()))

        def want(x):
            return 1000.0 + 1500.0 * (x - 600.0) / 1800.0

        for key in ("highdef", "lowdef"):  # inside the flat middle of the band, the ground is exactly on the ramp
            mesh = Tms(changed[FILES[key]])
            step = (mesh.bounds[5] - mesh.bounds[2]) / Q_MAX
            inner = [(mesh.to_world(0, p[0]), mesh.to_world(2, p[2])) for c in mesh.cells for p in c.positions()
                     if 600 <= mesh.to_world(0, p[0]) <= 2400 and abs(mesh.to_world(1, p[1]) - 1500) < 200]
            self.assertGreater(len(inner), 3, key)
            for x, z in inner:
                self.assertAlmostEqual(z, want(x), delta=step, msg=key)
        for key in ("ground", "camera"):
            k = Kdt(changed[FILES[key]])
            step = (k.bounds_max[2] - k.bounds_min[2]) / Q_MAX
            inner = [(k.to_world(0, p[0]), k.to_world(2, p[2])) for s in range(len(k.subtrees)) for p in k.positions(s)
                     if 600 <= k.to_world(0, p[0]) <= 2400 and abs(k.to_world(1, p[1]) - 1500) < 200]
            self.assertGreater(len(inner), 3, key)
            for x, z in inner:
                self.assertAlmostEqual(z, want(x), delta=step, msg=key)

    def test_smoothing_evens_out_the_bumps_and_keeps_the_files_in_step(self):
        def spread(mesh):
            zs = [mesh.to_world(2, p[2]) for c in mesh.cells for p in c.positions()
                  if math.hypot(mesh.to_world(0, p[0]) - 1500, mesh.to_world(1, p[1]) - 1500) < 300]
            return max(zs) - min(zs)
        changed, _ = edit_map(reader(self.files), [Stroke("smooth", 1500.0, 1500.0, 900.0, weight=1.0)])
        hd = Tms(changed[FILES["highdef"]])
        self.assertLess(spread(hd), spread(self.hd) * 0.6)
        heights = {(p[0], p[1]): p[2] for c in hd.cells for p in c.positions()}
        ground = Kdt(changed[FILES["ground"]])
        self.assertTrue(all(qz == heights[(qx, qy)] for s in range(len(ground.subtrees))
                            for qx, qy, qz in ground.positions(s)))

    def test_heights_stop_at_the_top_of_the_range(self):
        changed, notes = edit_map(reader(self.files), [Stroke("hill", 1500.0, 1500.0, 600.0, height=1e6)])
        hd = Tms(changed[FILES["highdef"]])
        self.assertEqual(max(p[2] for c in hd.cells for p in c.positions()), Q_MAX)
        self.assertTrue(any("reached the top of the map's height range" in n for n in notes), notes)

    def test_moved_ground_points_take_the_meshs_normals(self):
        changed, _ = edit_map(reader(self.files), [self.hill])
        ground = Kdt(changed[FILES["ground"]])
        east = west = 0
        for s in range(len(ground.subtrees)):
            for (qx, qy, _qz), n in zip(ground.positions(s), ground.normals(s)):
                x, y = ground.to_world(0, qx), ground.to_world(1, qy)
                if abs(y - 1500) < 1 and 1700 < x < 1950:     # the east slope leans east
                    self.assertGreater(n[0], 0.1)
                    east += 1
                if x < 700 and y < 700:                        # far from the hill: still straight up
                    self.assertEqual(n, (0.0, 0.0, 1.0))
                    west += 1
        self.assertTrue(east and west)

    def test_edge_points_never_move(self):
        changed, _ = edit_map(reader(self.files), [Stroke("hill", 1500.0, 1500.0, 5000.0, height=50.0)])
        for key in ("highdef", "lowdef"):
            old, new = Tms(self.files[FILES[key]]), Tms(changed[FILES[key]])
            for a, b in zip(old.cells, new.cells):
                for p, q in zip(a.positions(), b.positions()):
                    if edge(p[0], p[1]):
                        self.assertEqual(p, q)
                    else:
                        self.assertGreater(q[2], p[2])

    def test_a_stroke_outside_the_map_changes_nothing(self):
        changed, notes = edit_map(reader(self.files), [Stroke("hill", 9000.0, 9000.0, 100.0, height=5.0)], "Test")
        self.assertEqual(changed, {})
        self.assertIn("Test: stroke 1 (hill at 9000, 9000) is outside the map", notes)
        changed, notes = edit_map(reader(self.files), [Stroke("hill", 1515.0, 1515.0, 2.0, height=5.0)], "Test")
        self.assertEqual(changed, {})
        self.assertTrue(any("smaller than the gaps between the ground's points" in n for n in notes), notes)

    def test_a_missing_file_is_reported_and_the_others_edited(self):
        files = make_map(camera=False)
        changed, notes = edit_map(reader(files), [self.hill], "Test")
        self.assertEqual(set(changed), {FILES["highdef"], FILES["lowdef"], FILES["ground"]})
        self.assertIn("Test has no output\\occlusioninfo_camera.kdt (camera floor); the other files are edited", notes)
        with self.assertRaises(ValueError):
            edit_map(lambda member: None, [self.hill])

    def test_from_a_map_pack(self):
        arc = Edat(make_map_pack())
        changed, _ = edit_map(lambda m: bytes(arc.read(arc.find(m))), [self.hill])
        rebuilt = Edat(arc.to_bytes(changed))
        self.assertEqual(bytes(rebuilt.read(rebuilt.find(FILES["highdef"]))), changed[FILES["highdef"]])
        self.assertEqual(struct.unpack_from("<I", changed[FILES["highdef"]], 12)[0], len(changed[FILES["highdef"]]))


def unit_normal(n) -> tuple:
    """A close-up mesh normal (bytes, component = round((n + 1) * 127.5)) as a unit vector."""
    v = [c / 127.5 - 1.0 for c in n[:3]]
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v)


class Cliffs(unittest.TestCase):
    """The close-up mesh can hold several points at one x, y (a cliff's top and its foot); the gameplay ground sits on
    one of them, and must keep that one's height and take that one's normal."""

    def setUp(self):
        self.files = make_map(cliff=True)
        self.hill = Stroke("hill", 1500.0, 1500.0, 600.0, height=400.0)
        self.changed, _ = edit_map(reader(self.files), [self.hill])
        self.hd = Tms(self.changed[FILES["highdef"]])
        self.ground = Kdt(self.changed[FILES["ground"]])

    def test_the_fixture_has_two_points_at_one_x_y(self):
        cell = Tms(self.files[FILES["highdef"]]).cells[4].positions()
        self.assertEqual(cell[0][:2], cell[CLIFF_WEST + 1][:2])
        self.assertEqual(cell[0][2], cell[CLIFF_WEST + 1][2] - CLIFF_DROP)
        self.assertEqual(cell[-1][:2], cell[CLIFF_EAST + 1][:2])

    def test_ground_points_keep_the_height_of_the_mesh_point_they_sit_on(self):
        after = {}   # close-up mesh point (x, y, height before) -> its heights after
        for a, b in zip(Tms(self.files[FILES["highdef"]]).cells, self.hd.cells):
            for p, q in zip(a.positions(), b.positions()):
                after.setdefault(p[:3], set()).add(q[2])
        old = Kdt(self.files[FILES["ground"]])
        moved = 0
        for s in range(len(old.subtrees)):
            for p, q in zip(old.positions(s), self.ground.positions(s)):
                self.assertEqual(after[p], {q[2]})
                moved += p != q
        self.assertGreater(moved, 10)

    def test_a_ground_point_takes_the_normal_of_the_mesh_point_it_sits_on(self):
        top = self.hd.cells[4].positions()[CLIFF_WEST + 1]
        want = unit_normal(self.hd.cells[4].normals()[CLIFF_WEST + 1])
        self.assertLess(want[0], -0.1)     # the hill's west slope leans west
        found = 0
        for s in range(len(self.ground.subtrees)):
            for p, n in zip(self.ground.positions(s), self.ground.normals(s)):
                if p == top[:3]:
                    for got, w in zip(n, want):
                        self.assertAlmostEqual(got, w, delta=0.02)
                    found += 1
        self.assertEqual(found, 1)


if __name__ == "__main__":
    unittest.main()
