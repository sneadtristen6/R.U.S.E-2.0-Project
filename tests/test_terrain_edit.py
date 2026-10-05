"""Terrain edits (rusemod.terrain_edit): brush strokes on a made-up map whose four ground files change together.

The map is 3,000 units square: a close-up mesh of 3 x 3 cells with 11 x 11 points each, a far mesh with 5 x 5 points
per cell, a gameplay ground whose points and triangles are the close-up mesh's (same bounds; one part per row of
cells), and a camera floor on the far mesh's points and triangles with a taller height range (one part for the first
row, one for the rest). Both .kdt files have real trees (rusemod.kdt_edit.rebuild) with a tight height limit around
each part, and a MainNode whose limits are tight too, so any rise has to widen them. Heights step by 0.1 in the
meshes (-100 to 3,176.7)."""
import math
import struct
import unittest

from fixtures import make_edat
from test_kdt import hand_storage, make_kdt
from test_tms import make_tms, skirt_meshes, skirt_q
from rusemod.brush import Stroke
from rusemod.edat import Edat
from rusemod import kdt_edit
from rusemod.kdt import Clip, Kdt, leaves
from rusemod.terrain_edit import FILES, edit_map, without_floor_notes
from rusemod.tms import Q_MAX, Cell, Patch, Tms, VertexBuffer, encode_indices

CAMERA_Z = (-500.0, 5000.0)


def bumpy(x: int, y: int) -> int:
    """A ground height (quantized) with small bumps everywhere."""
    return 10000 + (x * 7 + y * 13) % 997


def tree(groups, triangles, bounds_min, bounds_max, rows) -> bytes:
    """A .kdt with one subtree per group of points (quantized x, y, z) and its triangles (vertex triples), every normal
    straight up. Each subtree's tree is built by rusemod.kdt_edit.rebuild and wrapped in a keep-below and a
    keep-above height limit that fit it exactly. The MainNode: the file's box (six limits), then a split on y at
    each row boundary in `rows` (world y where the next subtree starts), each subtree behind a tight keep-below limit."""
    positions = [list(g) for g in groups]
    parents = [[0] + list(range(len(g) - 1)) for g in groups]
    normals = [[(0.0, 0.0, 1.0)] * len(g) for g in groups]
    n = len(groups)
    opaque = {"indices": [b"I" * 6] * n, "trilists": [b"T" * 4] * n, "trees": [b"S" * 10] * n, "main": b"MAINNODE" * 2}
    storage, offsets = hand_storage(positions, parents, normals, opaque)
    k = Kdt(make_kdt(storage, offsets, subtree_count=n, triangle_count=99, bounds_min=bounds_min))
    k.bounds_min, k.bounds_max = tuple(bounds_min), tuple(bounds_max)
    for s, tris in enumerate(triangles):
        k.set_indices(s, [v for tri in tris for v in tri])
        kdt_edit.rebuild(k, s)
        zs = [p[2] for p in groups[s]]
        root = Clip(2, min(zs), True, Clip(2, max(zs), False, k.tree(s)))
        k.set_tree(s, root, k.trilists(s))
    entries = [(0, 0, 0, bounds_max[0]), (2, 0, 0, bounds_min[0]), (0, 1, 0, bounds_max[1]), (2, 1, 0, bounds_min[1]),
               (0, 2, 0, bounds_max[2]), (2, 2, 0, bounds_min[2])]

    def top(s):
        return k.to_world(2, max(p[2] for p in groups[s]))

    def part(s):
        if s == n - 1:
            entries.append((1, 2, s, top(s)))
            return
        i = len(entries)
        entries.append(None)
        part(s + 1)                      # above the split: the next rows
        below = len(entries)
        entries.append((1, 2, s, top(s)))
        entries[i] = (4, 1, 2 * (below - i), rows[s])
    part(0)
    k.set_main_entries(entries)
    return k.to_bytes()


def cell_triangles(mesh: Tms, cells: list[int]) -> list[tuple]:
    """The ground triangles of these cells, numbered over their points laid end to end."""
    out, base = [], 0
    for c in cells:
        tri = mesh.cells[c].triangles(0)
        out += [(base + tri[k], base + tri[k + 1], base + tri[k + 2]) for k in range(0, len(tri), 3)]
        base += len(mesh.cells[c].positions())
    return out


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
    """The four ground files of a made-up map, by member path; the close-up mesh has a skirt like the shipped ones.
    `cliff`: the close-up mesh has the little cliff of `cliff_mesh`, and the gameplay ground sits on its tops."""
    high = make_tms(gw=3, gh=3, n=11, zf=bumpy, skirt=True)
    low = make_tms(gw=3, gh=3, n=5, zf=bumpy)
    hd, ld = Tms(high), Tms(low)
    b = hd.bounds
    cells = [[p[:3] for p in c.positions()] for c in hd.cells]
    ground = tree([cells[0] + cells[1] + cells[2], cells[3] + cells[4] + cells[5], cells[6] + cells[7] + cells[8]],
                  [cell_triangles(hd, [0, 1, 2]), cell_triangles(hd, [3, 4, 5]), cell_triangles(hd, [6, 7, 8])],
                  (b[0], b[1], b[2]), (b[3], b[4], b[5]), rows=[1000.0, 2000.0])
    if cliff:
        high = cliff_mesh(high)
    lo_z, hi_z = CAMERA_Z
    cam_points = []
    for c in ld.cells:
        for qx, qy, qz, _w in c.positions():
            z = ld.to_world(2, qz)
            cam_points.append((qx, qy, round((z - lo_z) * 32767 / (hi_z - lo_z))))
    first_row = sum(len(ld.cells[c].positions()) for c in range(3))
    files = {FILES["highdef"]: high, FILES["lowdef"]: low, FILES["ground"]: ground}
    if camera:
        files[FILES["camera"]] = tree([cam_points[:first_row], cam_points[first_row:]],
                                      [cell_triangles(ld, [0, 1, 2]), cell_triangles(ld, range(3, 9))],
                                      (b[0], b[1], lo_z), (b[3], b[4], hi_z), rows=[1000.0])
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

    def points(self, files, key):
        """(x, y, z) in world units of every point of one of the four files."""
        if key in ("highdef", "lowdef"):
            m = Tms(files[FILES[key]])
            return [tuple(m.to_world(k, p[k]) for k in range(3)) for c in m.cells for p in c.positions()]
        k = Kdt(files[FILES[key]])
        return [tuple(k.to_world(a, p[a]) for a in range(3)) for s in range(len(k.subtrees)) for p in k.positions(s)]

    def assertFollows(self, changed):
        """The far mesh and the camera floor move by the gameplay ground's change: exactly, where one of their points
        sits on a gameplay-ground point (they keep their own bumps; the fixture's are up to 100 units)."""
        before, after = self.points(self.files, "ground"), self.points(changed, "ground")
        dz = {(round(x), round(y)): b[2] - a[2] for (x, y, _z), a, b in zip(before, before, after)}
        for key in ("lowdef", "camera"):
            step = 0.11 if key == "lowdef" else (CAMERA_Z[1] - CAMERA_Z[0]) / Q_MAX + 0.11
            shared = 0
            for (x, y, z0), (_x, _y, z1) in zip(self.points(self.files, key), self.points(changed, key)):
                if (round(x), round(y)) in dz:
                    self.assertAlmostEqual(z1 - z0, dz[(round(x), round(y))], delta=step, msg=key)
                    shared += dz[(round(x), round(y))] != 0.0
            self.assertGreater(shared, 3, key)

    def lift(self, x, y) -> float:
        d2 = (x - 1500.0) ** 2 + (y - 1500.0) ** 2
        return 400.0 * (1 - d2 / 360000.0) ** 2 if d2 < 360000.0 else 0.0

    def test_the_road_model_moves_with_the_ground(self):
        """The road model (the white roads seen from high up) holds the ground's height at every vertex: it moves by
        the close-up mesh's change under each (left, it stood off the painted roads on flattened Blitz Twin)."""
        from test_roadstrips import road_vertices, static_pack
        from rusemod.roadstrips import MEMBER
        files = dict(self.files)
        files[MEMBER] = static_pack(road_cases=((0, (1000.0, 1500.0, 2000.0, 1700.0)),))
        changed, notes = edit_map(reader(files), [self.hill], "Test")
        self.assertIn(MEMBER, changed)
        self.assertTrue(any("road model" in n and "6 point(s) moved" in n for n in notes), notes)
        before, after = Tms(files[FILES["highdef"]]), Tms(changed[FILES["highdef"]])
        for (x, y, z0, *_r), (_x, _y, z1, *_s) in zip(road_vertices(files[MEMBER]), road_vertices(changed[MEMBER])):
            rise = after.height_at(x, y) - before.height_at(x, y)
            self.assertGreater(rise, 10.0)  # the hill's flank: 15 at the far end, more nearer its top
            self.assertAlmostEqual(z1 - z0, rise, delta=0.01)
        flat = edit_map(reader(files), [Stroke("hill", 9000.0, 9000.0, 100.0, height=5.0)], "Test")[0]
        self.assertNotIn(MEMBER, flat)  # ground that didn't move leaves it

    def test_a_stroke_at_a_bridges_floor_is_said(self):
        """A unit stands on the higher of the ground and a bridge's floor, and the floor keeps its height: a stroke
        that reaches a bridge's floor gets a note (lower ground leaves the floor's end in the air)."""
        from rusemod import floors
        from rusemod.floors import Deck, rebuild
        from test_floors import strip
        from test_kdt import make_valid_kdt
        files = dict(self.files)
        files[floors.MEMBER] = rebuild(Kdt(make_valid_kdt()), strip(Deck.of(1300.0, 1500.0, 1700.0, 1500.0), 0.0, 0.0))
        _changed, notes = edit_map(reader(files), [self.hill], "Test")
        self.assertTrue(any("stroke 1 (hill at 1500, 1500) reaches a bridge's floor" in n for n in notes), notes)
        # the map's own bridges taken out: their floors sunk, the notes left out, every other note kept
        self.assertEqual(without_floor_notes(notes), [n for n in notes if "bridge's floor" not in n])
        self.assertLess(len(without_floor_notes(notes)), len(notes))
        _changed, notes = edit_map(reader(files), [Stroke("hill", 2600.0, 2600.0, 200.0, height=400.0)], "Test")
        self.assertFalse(any("bridge's floor" in n for n in notes), notes)
        self.assertEqual(without_floor_notes(notes), notes)

    def test_a_hill_raises_all_four_files_together(self):
        changed, notes = edit_map(reader(self.files), [self.hill], "Test")
        self.assertEqual(set(changed), set(FILES.values()))
        self.assertIn("Test: 1 stroke(s); points moved: close-up mesh", notes[0])
        hd, ld = Tms(changed[FILES["highdef"]]), Tms(changed[FILES["lowdef"]])
        # the close-up mesh's points are the gameplay ground's, so they get the brush exactly; the far mesh follows the
        # gameplay ground's triangles, so it's off by at most the bend of the hill across one triangle
        for old_mesh, new_mesh, exact in ((self.hd, hd, True), (self.ld, ld, False)):
            for a, b in zip(old_mesh.cells, new_mesh.cells):
                for p, q in zip(a.positions(), b.positions()):
                    self.assertEqual((p[0], p[1], p[3]), (q[0], q[1], q[3]))
                    x, y, z = (old_mesh.to_world(k, p[k]) for k in range(3))
                    if exact:
                        self.assertEqual(q[2], old_mesh.to_quant(2, z + self.lift(x, y)))
                    else:
                        self.assertAlmostEqual(new_mesh.to_world(2, q[2]), z + self.lift(x, y), delta=15.0)
        # the gameplay ground's points are the close-up mesh's, so they get exactly the same new heights
        heights = {(p[0], p[1]): p[2] for c in hd.cells for p in c.positions()}
        ground = Kdt(changed[FILES["ground"]])
        for s in range(len(ground.subtrees)):
            for qx, qy, qz in ground.positions(s):
                self.assertEqual(qz, heights[(qx, qy)])
        # the camera floor has its own height range and follows the gameplay ground's triangles too
        old_cam, cam = Kdt(self.files[FILES["camera"]]), Kdt(changed[FILES["camera"]])
        step = (CAMERA_Z[1] - CAMERA_Z[0]) / 32767
        for s in range(len(cam.subtrees)):
            for p, q in zip(old_cam.positions(s), cam.positions(s)):
                x, y = cam.to_world(0, p[0]), cam.to_world(1, p[1])
                self.assertAlmostEqual(cam.to_world(2, q[2]), old_cam.to_world(2, p[2]) + self.lift(x, y),
                                       delta=15.0 + step)
        # the corner cell is out of reach and keeps its exact bytes; the moved cell's patch bounds reach the top
        self.assertEqual(hd.cells[0].vb, self.hd.cells[0].vb)
        centre = hd.cells[4]
        top = max(hd.to_world(2, p[2]) for p in centre.positions())
        self.assertAlmostEqual(max(p.zhi for p in centre.patch_list()), top, 1)

    def test_the_trees_and_the_top_limits_hold_the_moved_ground(self):
        """The fixture's height limits fit its ground exactly, so a hill pokes out of them: after the edit, every
        triangle a leaf lists touches the leaf's cell and every part fits its MainNode region, in both .kdt files."""
        changed, notes = edit_map(reader(self.files), [self.hill], "Test")
        for key in ("ground", "camera"):
            old, new = Kdt(self.files[FILES[key]]), Kdt(changed[FILES[key]])
            moved = [s for s in range(len(new.subtrees)) if new.positions(s) != old.positions(s)]
            self.assertTrue(moved, key)
            for s in range(len(new.subtrees)):
                self.assertEqual(kdt_edit.check(new, s), [], key)
            self.assertEqual(kdt_edit.check_main(new, range(len(new.subtrees))), [], key)
            self.assertNotEqual(new.main_node, old.main_node, key)
            # the old trees don't hold the new ground: that's what refused move orders in the game
            stale = Kdt(changed[FILES[key]])
            for s in moved:
                stale.subtrees[s].tree, stale.subtrees[s].trilist = old.subtrees[s].tree, old.subtrees[s].trilist
            self.assertTrue(any(kdt_edit.check(stale, s) for s in moved), key)
        self.assertTrue(any("gameplay ground:" in n and "widened" in n for n in notes), notes)

    def test_a_hole_below_a_height_split_rebuilds_that_part(self):
        """A part whose tree splits on height: a pit that pulls triangles from above the split to below it can't be
        fixed by widening, so that part's tree is built again (on x and y only) and still holds every triangle."""
        k = Kdt(self.files[FILES["ground"]])
        pos, tris = kdt_edit.triangles(k, 1)
        zs = sorted(p[2] for p in pos)
        mid = zs[len(zs) // 2]
        above = [t for t, tri in enumerate(tris) if max(pos[v][2] for v in tri) >= mid]
        below = [t for t, tri in enumerate(tris) if min(pos[v][2] for v in tri) <= mid]
        root_a, lists_a = _xy_build(k, 1, above)
        root_b, lists_b = _xy_build(k, 1, below)
        k.set_tree(1, kdt_edit.Split(2, mid, root_a, root_b), lists_a + lists_b)
        self.assertEqual(kdt_edit.check(k, 1), [])
        files = dict(self.files)
        files[FILES["ground"]] = k.to_bytes()
        changed, notes = edit_map(reader(files), [Stroke("crater", 1500.0, 1500.0, 500.0, height=1500.0)], "Test")
        new = Kdt(changed[FILES["ground"]])
        self.assertEqual(kdt_edit.check(new, 1), [])
        self.assertFalse(any(isinstance(n, kdt_edit.Split) and n.axis == 2 for n in _nodes(new.tree(1))))
        self.assertTrue(any("1 rebuilt" in n for n in notes if "gameplay ground:" in n), notes)

    def test_the_same_strokes_give_the_same_bytes(self):
        strokes = [self.hill, Stroke("crater", 900.0, 2100.0, 300.0, height=150.0),
                   Stroke("smooth", 1500.0, 1500.0, 900.0, weight=0.8)]
        self.assertEqual(edit_map(reader(make_map()), strokes)[0], edit_map(reader(make_map()), strokes)[0])

    def test_a_plateau_is_level_across_its_middle_in_every_file(self):
        changed, _ = edit_map(reader(self.files), [Stroke("plateau", 1500.0, 1500.0, 800.0, level=2500.0)])
        # flat across its middle half (400) in the files that hold the gameplay ground's points
        for key in ("highdef", "ground"):
            for x, y, z in self.points(changed, key):
                if math.hypot(x - 1500, y - 1500) < 400:
                    self.assertAlmostEqual(z, 2500.0, delta=0.11, msg=key)
        self.assertFollows(changed)

    def test_a_ramp_slopes_evenly_from_end_to_end_in_every_file(self):
        ramp = Stroke("ramp", 600.0, 1500.0, 400.0, level=1000.0, x2=2400.0, y2=1500.0, level2=2500.0)
        changed, _ = edit_map(reader(self.files), [ramp])
        self.assertEqual(set(changed), set(FILES.values()))

        def want(x):
            return 1000.0 + 1500.0 * (x - 600.0) / 1800.0

        # inside the flat middle of the band the ground is exactly on the ramp
        for key in ("highdef", "ground"):
            inner = [(x, z) for x, y, z in self.points(changed, key) if 600 <= x <= 2400 and abs(y - 1500) < 200]
            self.assertGreater(len(inner), 3, key)
            for x, z in inner:
                self.assertAlmostEqual(z, want(x), delta=0.11, msg=key)
        self.assertFollows(changed)

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
        held = [n for n in notes if "reached the top of a file's height range" in n]
        self.assertEqual(len(held), 1, notes)
        self.assertIn("close-up mesh", held[0])  # which files held, by name

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

    def test_edge_points_move_and_the_curtain_follows(self):
        """A stroke over the whole map moves its edge too, in every file (the edge kept still was a wall of old
        mountain round the owner's flattened Blitz Twin, 2026-10-03), and the close-up mesh's curtain follows it."""
        changed, _ = edit_map(reader(self.files), [Stroke("plateau", 1500.0, 1500.0, 5000.0, level=2500.0)])
        # level in the files on the gameplay ground's points; the far mesh and the camera floor follow its change and
        # keep their own bumps (up to 100 units; the ground was 900 to 1,000 before)
        for key, delta in (("highdef", 0.11), ("ground", 0.11), ("lowdef", 110.0), ("camera", 110.0)):
            for x, y, z in self.points(changed, key):
                self.assertAlmostEqual(z, 2500.0, delta=delta, msg=(key, x, y))
        hd = Tms(changed[FILES["highdef"]])
        edge_q = {(p[0], p[1]): p[2] for c in hd.cells for p in c.positions() if edge(p[0], p[1])}
        curtain = skirt_meshes(hd)[0][1]
        self.assertTrue(curtain)
        for x, y, z, _w in curtain:
            self.assertIn(z, (0, skirt_q(hd, edge_q[(x, y)])))
        self.assertEqual(sum(v[2] == 0 for v in curtain), len(curtain) // 2)

    def test_beyond_the_edge_a_point_follows_the_edge_beside_it(self):
        """The camera floor reaches past the map's edge (every shipped one 175,000 out, 20,999 under the floor at
        the edge): where there's no gameplay ground under a point, it takes the change at the nearest edge point."""
        from rusemod.terrain_edit import _Surface, _tree_points
        ground = Kdt(self.files[FILES["ground"]])
        pts = _tree_points("ground", ground)
        pts.apply(Stroke("hill", 0.0, 1500.0, 800.0, height=300.0))
        surface = _Surface(ground, pts)
        self.assertGreater(surface.change(0.0, 1500.0), 250.0)
        self.assertEqual(surface.change(-175000.0, 1500.0), surface.change(0.0, 1500.0))
        self.assertEqual(surface.change(-50.0, -50.0), surface.change(0.0, 0.0))
        self.assertEqual(surface.change(4000.0, 1500.0), surface.change(3000.0, 1500.0))

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


def _xy_build(k, s, ts):
    pos, tris = kdt_edit.triangles(k, s)
    scratch = Kdt(k.to_bytes())
    scratch.set_indices(s, [v for t in ts for v in tris[t]])
    kdt_edit.rebuild(scratch, s)
    root, lists = scratch.tree(s), scratch.trilists(s)
    return root, [[ts[i] for i in lst] for lst in lists]


def _nodes(n):
    yield n
    if isinstance(n, kdt_edit.Split):
        yield from _nodes(n.above)
        yield from _nodes(n.below)
    elif isinstance(n, Clip):
        yield from _nodes(n.child)


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


def bits(v):
    """A float's exact bits (or None), so -0.0 and 0.0 count as different."""
    return None if v is None else struct.pack("<d", v)


class QuickLookups(unittest.TestCase):
    """The terrain step's lookups made for many points give exactly what the plain ones give, to the bit: each stroke's
    share of the old shape (looked up by place), the gameplay ground's change and old height (one search), and the
    nearest close-up mesh point's normal (the nearest squares first)."""

    def setUp(self):
        from rusemod import terrain_edit
        self.te = terrain_edit
        self.files = make_map(cliff=True)
        self.hd = Tms(self.files[FILES["highdef"]])
        self.area = (0.0, 0.0, 3000.0, 3000.0)

    def probe_points(self, step):
        """Points all over the map and past it, on the squares' edges and on every close-up mesh point."""
        out = [(x * 37.3 - 200.0, y * 41.9 - 300.0) for x in range(95) for y in range(90)]
        out += [(k * step, j * step) for k in range(0, 260, 7) for j in range(0, 260, 11)]
        out += [(self.hd.to_world(0, p[0]), self.hd.to_world(1, p[1])) for c in self.hd.cells for p in c.positions()]
        return out

    def test_the_strokes_share_of_the_old_shape_by_place(self):
        strokes = [Stroke("plateau", 1500.0, 1500.0, 600.0, level=200.0, weight=0.8),
                   Stroke("flatten", 400.0, 2600.0, 900.0, level=0.0, weight=0.5, edge="hard"),
                   Stroke("hill", 1500.0, 1500.0, 600.0, height=400.0),
                   Stroke("level", 2900.0, 100.0, 300.0, level=50.0, shape="square", dx=1.0, dy=2.0),
                   Stroke("ramp", 100.0, 100.0, 250.0, x2=2800.0, y2=2900.0, level=0.0, level2=900.0),
                   Stroke("smooth", -50.0, 1500.0, 400.0, weight=0.3),
                   Stroke("flatten", 3200.0, 3300.0, 700.0, level=10.0, weight=1.0, shape="line", x2=2000.0,
                          y2=3100.0),
                   Stroke("plateau", 50000.0, 50000.0, 100.0, level=1.0)]   # far off the map
        quick = self.te._Kept(strokes, self.area)
        for x, y in self.probe_points(quick.step) + [(1e6, 1e6), (-1e6, 20.0)]:
            self.assertEqual(bits(quick.at(x, y)), bits(self.te._kept(strokes, x, y)), (x, y))

    def test_the_grounds_change_and_old_height_from_one_search(self):
        files = make_map(cliff=True)
        kdt = Kdt(files[FILES["ground"]])
        pts = self.te._tree_points("ground", kdt)
        pts.apply(Stroke("hill", 1500.0, 1500.0, 900.0, height=400.0))
        pts.apply(Stroke("plateau", 600.0, 2500.0, 500.0, level=900.0))
        surface = self.te._Surface(kdt, pts)
        self.assertTrue(surface)
        for x, y in self.probe_points(surface.step):
            change, old = surface.change_and_old(x, y)
            self.assertEqual((bits(change), bits(old)), (bits(surface.change(x, y)), bits(surface.old(x, y))), (x, y))

    def test_the_nearest_mesh_points_normal(self):
        pts = self.te._mesh_points("highdef", self.hd)
        quick = self.te._normal_lookup(self.hd, pts)

        def plain(x, y, z):   # the lookup as it was: every point of the squares within two of it
            best, best_d = None, None
            s = pts.step
            for n in pts.near(x - 2 * s, x + 2 * s, y - 2 * s, y + 2 * s):
                dx, dy = pts.x[n] - x, pts.y[n] - y
                d = (dx * dx + dy * dy, abs(pts.z[n] - z))
                if best_d is None or d < best_d or (d == best_d and n < best):
                    best, best_d = n, d
            if best is None:
                return None
            bx, by, bz, _ = self.hd.cells[pts.part[best]].normals()[pts.index[best]]
            v = (bx / 127.5 - 1.0, by / 127.5 - 1.0, bz / 127.5 - 1.0)
            length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
            if length == 0.0 or v[2] <= 0.0:
                return None
            return (v[0] / length, v[1] / length, v[2] / length)
        zs = (-100.0, 900.0, 1013.0, 1040.0, 3000.0)
        probes = self.probe_points(pts.step) + [(x, y) for x in (-700.0, 3700.0) for y in (-700.0, 1500.0)]
        for k, (x, y) in enumerate(probes):
            z = zs[k % len(zs)]
            self.assertEqual(quick(x, y, z), plain(x, y, z), (x, y, z))
        for c in self.hd.cells:   # the cliff's top and foot share an x, y: the height picks the one sat on
            for p in c.positions():
                x, y, z = (self.hd.to_world(a, p[a]) for a in range(3))
                self.assertEqual(quick(x, y, z), plain(x, y, z), (x, y, z))


if __name__ == "__main__":
    unittest.main()
