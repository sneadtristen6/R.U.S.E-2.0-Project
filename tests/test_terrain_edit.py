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
from rusemod.tms import Q_MAX, Tms

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


def make_map(camera=True) -> dict:
    """The four ground files of a made-up map, by member path."""
    high = make_tms(gw=3, gh=3, n=11, zf=bumpy)
    low = make_tms(gw=3, gh=3, n=5, zf=bumpy)
    hd, ld = Tms(high), Tms(low)
    b = hd.bounds
    cells = [[p[:3] for p in c.positions()] for c in hd.cells]
    ground = tree([cells[0] + cells[1] + cells[2], cells[3] + cells[4] + cells[5], cells[6] + cells[7] + cells[8]],
                  (b[0], b[1], b[2]), (b[3], b[4], b[5]))
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


def make_map_pack(camera=True) -> bytes:
    """The made-up map as a map pack (EDAT), its files under output\\ like the game's."""
    files = make_map(camera)
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


if __name__ == "__main__":
    unittest.main()
