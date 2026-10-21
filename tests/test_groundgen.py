"""A new map's ground drawn as our own (rusemod.groundgen), on made-up meshes (tests/test_tms.py), trees
(tests/test_kdt.py) and water textures (tests/test_water.py): no game files needed."""
import math
import unittest

from rusemod import kdt_edit
from rusemod.brush import Stroke
from rusemod.groundgen import (CAMERA_OVER, GroundGenError, Shape, camera_floor, fine_cells, fit_skirt,
                               gameplay_ground, hilbert, make_mesh, water_pictures)
from rusemod.kdt import Kdt
from rusemod.tms import SKIRT_BOTTOM, Q_MAX, Tms
from rusemod.water import CASE, TEXTURES, TILE, _cell, _pixels, _water_triangles

from test_kdt import make_valid_kdt
from test_tms import make_tms, skirt_meshes
from test_water import texture

BOUNDS = (0.0, 0.0, 2000.0, 2000.0)


def whole(level, size=2000.0):
    """A hard level stroke over the whole map (as Blank Terrain and Blank Ocean start)."""
    return Stroke(brush="level", x=size / 2, y=size / 2, radius=size, level=level, weight=1.0, shape="square",
                  edge="hard")


def sea(level, size=2000.0):
    return Stroke(brush="water", x=size / 2, y=size / 2, radius=size, level=level, shape="square", edge="hard")


def island(x=1500.0, y=1500.0, r=300.0, level=50.0):
    return Stroke(brush="plateau", x=x, y=y, radius=r, level=level, weight=1.0, edge="hard")


def triangles_of(t: Tms):
    for c in t.cells:
        pos = c.positions()
        tri = c.triangles(0)
        for i in range(0, len(tri), 3):
            yield [pos[v] for v in tri[i:i + 3]]


class Shapes(unittest.TestCase):
    def test_a_map_not_flattened_first_is_drawn_the_usual_way(self):
        with self.assertRaises(GroundGenError):
            Shape([island()], BOUNDS, 0.0)
        with self.assertRaises(GroundGenError):   # a soft flatten doesn't level the whole map at one height
            Shape([Stroke(brush="flatten", x=1000.0, y=1000.0, radius=2000.0, level=0.0, weight=1.0)], BOUNDS, 0.0)

    def test_a_smooth_stroke_is_drawn_the_usual_way(self):
        with self.assertRaises(GroundGenError):
            Shape([whole(0.0), Stroke(brush="smooth", x=500.0, y=500.0, radius=100.0, weight=1.0)], BOUNDS, 0.0)

    def test_heights_and_water_follow_the_strokes_in_order(self):
        s = Shape([whole(0.0), island(), sea(20.0)], BOUNDS, -50.0)
        self.assertEqual(s.h(1500.0, 1500.0), 50.0)     # the island's flat top
        self.assertEqual(s.h(500.0, 500.0), 0.0)        # the flat start
        self.assertEqual(s.w(500.0, 500.0), 20.0)       # under the sea
        self.assertEqual(Shape([whole(0.0)], BOUNDS, -50.0).w(500.0, 500.0), -50.0)   # no water: the base level
        drained = Shape([whole(0.0), sea(20.0), Stroke(brush="drain", x=500.0, y=500.0, radius=100.0)], BOUNDS, -50.0)
        self.assertEqual(drained.w(500.0, 500.0), -50.0)
        self.assertEqual(drained.w(1500.0, 500.0), 20.0)

    def test_only_cells_a_stroke_changes_are_on_the_grid(self):
        s = Shape([whole(0.0), sea(20.0), island()], BOUNDS, -50.0)
        t = Tms(make_tms(gw=2, gh=2))
        self.assertEqual(fine_cells(t, s), {3})          # the island's cell (1, 1) alone


class Meshes(unittest.TestCase):
    def setUp(self):
        self.shape = Shape([whole(0.0), sea(20.0), island()], BOUNDS, -50.0)
        t = Tms(make_tms(gw=2, gh=2))
        t.cells, self.info = make_mesh(t, self.shape.h, self.shape.w, 16, fine_cells(t, self.shape))
        self.t = Tms(t.to_bytes())

    def test_every_triangle_is_wholly_wet_or_wholly_dry(self):
        for corners in triangles_of(self.t):
            self.assertFalse(any(p[2] > p[3] for p in corners) and any(p[2] < p[3] for p in corners), corners)

    def test_the_shore_is_the_island_s_own_outline(self):
        """Along rays out from the island's middle, the first wet triangle starts where the shape meets the water."""
        lv = 20.0
        # the plateau's hard edge: full to 0.85 of 300, then an S-curve to the seabed; where it crosses the water
        target = None
        r = 255.0
        while r < 300.0:
            if self.shape.h(1500.0 + r, 1500.0) < lv:
                target = r
                break
            r += 0.01
        wet_pts = [p for c in self.t.cells for p in c.positions() if p[2] == p[3]]
        dists = [math.hypot(self.t.to_world(0, p[0]) - 1500.0, self.t.to_world(1, p[1]) - 1500.0) for p in wet_pts]
        near_shore = [d for d in dists if abs(d - target) < 10.0]
        self.assertTrue(near_shore)
        # every point at the water's level lies on the outline, to the file's steps
        step = 2000.0 / Q_MAX * 2
        self.assertTrue(all(abs(d - target) < 4 * step for d in near_shore), (target, min(near_shore), max(near_shore)))

    def test_no_crack_where_the_shore_cuts_the_triangles(self):
        """Every edge inside a cell is shared by two of its triangles: a shoreline point put on one triangle's edge is
        on its neighbour's too. (A corner the cutting snapped onto the shore once turned from wet to dry for the
        triangles after it: an edge got a shoreline point on one side only, and the crack showed the sky, the pale
        spikes over the real-place rivers, 2026-10-19.)"""
        from collections import Counter
        for c in self.t.cells:
            pos = c.positions()
            tri = c.triangles(0)
            key = [(p[0], p[1]) for p in pos]
            edges = Counter()
            for k in range(0, len(tri), 3):
                a, b, d = (key[v] for v in tri[k:k + 3])
                for e in ((a, b), (b, d), (d, a)):
                    edges[tuple(sorted(e))] += 1
            lo_x, hi_x = min(p[0] for p in key), max(p[0] for p in key)
            lo_y, hi_y = min(p[1] for p in key), max(p[1] for p in key)
            inner = [e for e, n in edges.items() if n == 1
                     and not all(p[0] in (lo_x, hi_x) for p in e) and not all(p[1] in (lo_y, hi_y) for p in e)]
            self.assertEqual(inner, [])

    def test_a_shore_dip_puts_the_shoreline_under_the_water(self):
        """With shore_dip, the points on the shoreline lie under the water, so a triangle of only such points counts as
        under water (the game draws water where a corner lies under it); the outlines stay as without it."""
        t = Tms(make_tms(gw=2, gh=2))
        t.cells, _info = make_mesh(t, self.shape.h, self.shape.w, 16, fine_cells(t, self.shape), shore_dip=5.0)
        t = Tms(t.to_bytes())
        self.assertFalse(any(p[2] == p[3] for c in t.cells for p in c.positions() if p[3] > p[2] - 1 and p[3] < p[2] + 1))
        flat = [p for c in self.t.cells for p in c.positions()]
        dipped = [p for c in t.cells for p in c.positions()]
        self.assertEqual(sorted((p[0], p[1]) for p in flat), sorted((p[0], p[1]) for p in dipped))

    def test_neighbouring_cells_share_their_edge_points(self):
        t = self.t
        for k, nk, axis in ((0, 1, 0), (2, 3, 0), (0, 2, 1), (1, 3, 1)):
            a = t.cells[k].positions()
            val = max(p[axis] for p in a)
            self.assertEqual({p for p in a if p[axis] == val}, {p for p in t.cells[nk].positions() if p[axis] == val})

    def test_a_flat_cell_is_a_fan_per_patch(self):
        """Cell (0, 0): 64 patches, each its middle and its corners, and the grid's points on the cell's own edges."""
        c = self.t.cells[0]
        tris = len(c.triangles(0)) // 3
        # interior patches: 4 triangles; along an edge, one more per extra point (16 squares, 2 a patch side)
        self.assertEqual(tris, 64 * 4 + 4 * 8 * 1)
        self.assertEqual(c.flags, 3)                       # all under the sea: a water list

    def test_heights_at_the_grid_points_are_the_shape_s(self):
        t, s = self.t, 1000.0 / 16
        gx = {t.to_quant(0, i * s): i for i in range(33)}
        for c in t.cells:
            for p in c.positions():
                i, j = gx.get(p[0]), gx.get(p[1])
                if i is not None and j is not None:
                    z = t.to_quant(2, self.shape.h(i * s, j * s))
                    self.assertTrue(p[2] in (z, p[3]), (i, j, p))   # or snapped onto the water at the edge

    def test_a_finer_patch_split_keeps_the_ground_and_stores_each_patch_on_the_curve(self):
        """16 x 16 patches a cell: the same ground (the fine cell's triangles as with 8), the file's patch_div 16, 256
        patches a cell, and each patch's triangles inside its own square, the squares in hilbert(16)'s order."""
        fine = fine_cells(Tms(make_tms(gw=2, gh=2)), self.shape)
        t = Tms(make_tms(gw=2, gh=2))
        t.cells, info = make_mesh(t, self.shape.h, self.shape.w, 16, fine, 16)
        t = Tms(t.to_bytes())
        self.assertEqual(t.patch_div, 16)
        self.assertEqual(len(t.cells[3].triangles(0)), len(self.t.cells[3].triangles(0)))   # the island's cell
        self.assertEqual(len(t.cells[0].triangles(0)) // 3, 256 * 4)   # a flat cell: a 4-triangle fan a patch
        order = hilbert(16)
        side = Q_MAX / 2 / 16
        for k, c in enumerate(t.cells):
            pats = c.patch_list()
            self.assertEqual(len(pats), 256)
            pos, tri = c.positions(), c.triangles(0)
            x0, y0 = (k % 2) * Q_MAX / 2, (k // 2) * Q_MAX / 2
            for (col, row), p in zip(order, pats):
                for i in range(p.i0start, p.i0start + p.i0count, 3):
                    mx = sum(pos[v][0] for v in tri[i:i + 3]) / 3 - x0
                    my = sum(pos[v][1] for v in tri[i:i + 3]) / 3 - y0
                    self.assertEqual((int(mx // side), int(my // side)), (col, row))

    def test_the_patch_order_is_d_day_s(self):
        dday = [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (3, 0), (3, 1), (2, 1), (2, 2), (3, 2), (3, 3), (2, 3), (1, 3),
                (1, 2), (0, 2), (0, 3), (0, 4), (1, 4), (1, 5), (0, 5), (0, 6), (0, 7), (1, 7), (1, 6), (2, 6), (2, 7),
                (3, 7), (3, 6), (3, 5), (2, 5), (2, 4), (3, 4), (4, 4), (5, 4), (5, 5), (4, 5), (4, 6), (4, 7), (5, 7),
                (5, 6), (6, 6), (6, 7), (7, 7), (7, 6), (7, 5), (6, 5), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2), (6, 3),
                (5, 3), (4, 3), (4, 2), (5, 2), (5, 1), (4, 1), (4, 0), (5, 0), (6, 0), (6, 1), (7, 1), (7, 0)]
        self.assertEqual(hilbert(8), dday)
        # a finer split: each run of 4 is one of the coarser patches, in the coarser order
        self.assertEqual([(x // 2, y // 2) for x, y in hilbert(16)[::4]], dday)

    def test_a_dry_map_s_cells_follow_the_shipped_dry_rule(self):
        """No water: every cell flag 1, one list, its patches bounded from 0 to its highest ground (D-Day's and
        Blitz's dry cells)."""
        s = Shape([whole(0.0), island()], BOUNDS, -50.0)
        t = Tms(make_tms(gw=2, gh=2))
        t.cells, _info = make_mesh(t, s.h, s.w, 16, fine_cells(t, s))
        t = Tms(t.to_bytes())
        for c in t.cells:
            self.assertEqual(c.flags, 1)
            self.assertEqual(len(c.icount), 1)
            pos = c.positions()
            for p in c.patch_list():
                if p.vcount:
                    self.assertEqual(p.zlo, 0.0)
                    self.assertAlmostEqual(p.zhi, t.to_world(2, max(v[2] for v in pos[p.vstart:p.vstart + p.vcount])),
                                           places=1)


class Skirt(unittest.TestCase):
    def test_the_skirt_follows_the_edge_as_drawn(self):
        shape = Shape([whole(10.0), sea(20.0)], BOUNDS, -50.0)
        t = Tms(make_tms(gw=2, gh=2, skirt=True, zf=lambda x, y: 1000 + x // 64))
        t.cells, _info = make_mesh(t, shape.h, shape.w, 16, fine_cells(t, shape))
        moved = fit_skirt(t, shape.h, shape.w)
        self.assertGreater(moved, 0)
        t = Tms(t.to_bytes())
        scale = (t.bounds[5] - SKIRT_BOTTOM) / Q_MAX
        curtain = skirt_meshes(t)[0]
        for x, y, z, _w in curtain[1]:
            if z:
                self.assertAlmostEqual(SKIRT_BOTTOM + z * scale, 10.0, delta=scale)
        if len(skirt_meshes(t)) > 1:                       # the water's side: from the ground (10) up to the sea (20)
            zs = {t.to_world(2, z) for _x, _y, z, _w in skirt_meshes(t)[1][1]}
            self.assertTrue(all(abs(z - 10.0) < 0.2 or abs(z - 20.0) < 0.2 for z in zs), zs)


class GameplayGround(unittest.TestCase):
    def test_the_tree_holds_the_drawn_triangles_and_finds_them(self):
        k = Kdt(make_valid_kdt())
        size = k.bounds_max[0]
        t = Tms(make_tms(gw=2, gh=2))
        t.bounds = [0.0, 0.0, -100.0, size, size, 3176.7]
        t.cell_w = t.cell_h = size / 2
        shape = Shape([whole(10.0, size), Stroke(brush="plateau", x=0.75 * size, y=0.75 * size, radius=size / 8,
                                                  level=60.0, weight=1.0, edge="hard")], (0.0, 0.0, size, size), -50.0)
        t.cells, info = make_mesh(t, shape.h, shape.w, 16, fine_cells(t, shape))
        t = Tms(t.to_bytes())
        data, said = gameplay_ground(k, t)
        k2 = Kdt(data)
        self.assertEqual(k2.triangle_count, info["triangles"])
        for s in range(len(k2.subtrees)):
            self.assertEqual(kdt_edit.check(k2, s), [])
        self.assertEqual(kdt_edit.check_main(k2, range(len(k2.subtrees))), [])
        self.assertIn("triangles in its 2 parts", said)

    def test_the_camera_floor_lies_a_few_metres_over_the_new_ground(self):
        """The camera's floor made from the mesh: every point CAMERA_OVER over the ground (the island's top too),
        its trees valid (a blank map kept the copied map's: 53-61 m under the blank farm's flat 74 m, 2026-10-15)."""
        k = Kdt(make_valid_kdt())
        size = k.bounds_max[0]
        t = Tms(make_tms(gw=2, gh=2))
        t.bounds = [0.0, 0.0, -100.0, size, size, 3176.7]
        t.cell_w = t.cell_h = size / 2
        shape = Shape([whole(10.0, size), Stroke(brush="plateau", x=0.75 * size, y=0.75 * size, radius=size / 8,
                                                  level=60.0, weight=1.0, edge="hard")], (0.0, 0.0, size, size), -50.0)
        t.cells, _info = make_mesh(t, shape.h, shape.w, 16, fine_cells(t, shape))
        t = Tms(t.to_bytes())
        data, said = camera_floor(k, t)
        k2 = Kdt(data)
        for s in range(len(k2.subtrees)):
            self.assertEqual(kdt_edit.check(k2, s), [])
        self.assertEqual(kdt_edit.check_main(k2, range(len(k2.subtrees))), [])
        step = (k2.bounds_max[2] - k2.bounds_min[2]) / 0x7FFF
        ground = {z for c_k in range(len(t.cells)) for _x, _y, z in t.world_vertices(c_k)}
        zs = {k2.to_world(2, p[2]) for s in range(len(k2.subtrees)) for p in k2.positions(s)}
        for z in zs:   # a point of the mesh as stored, CAMERA_OVER up, to the tree's own step
            self.assertTrue(min(abs(z - (g + CAMERA_OVER)) for g in ground) <= step, (z, sorted(ground)[:5]))
        self.assertAlmostEqual(min(zs), min(ground) + CAMERA_OVER, delta=step)   # the flat ground
        self.assertAlmostEqual(max(zs), max(ground) + CAMERA_OVER, delta=step)   # the island's top
        self.assertGreater(max(ground) - min(ground), 40.0)
        self.assertIn("camera floor", said)


class WaterPictures(unittest.TestCase):
    def test_open_sea_shares_one_tile_and_an_island_s_cells_are_sampled(self):
        size_x, size_y = 2 * CASE, 3 * CASE
        t = Tms(make_tms(gw=2, gh=3, n=5))
        t.bounds = [0.0, 0.0, -100.0, size_x, size_y, 3176.7]
        t.cell_w = t.cell_h = CASE
        shape = Shape([Stroke(brush="level", x=size_x / 2, y=size_y / 2, radius=size_y, level=0.0, weight=1.0,
                              shape="square", edge="hard"),
                       Stroke(brush="water", x=size_x / 2, y=size_y / 2, radius=size_y, level=20.0, shape="square",
                              edge="hard"),
                       Stroke(brush="plateau", x=1.5 * CASE, y=2.5 * CASE, radius=0.3 * CASE, level=50.0, weight=1.0,
                              edge="hard")], (0.0, 0.0, size_x, size_y), -50.0)
        fine = fine_cells(t, shape)
        t.cells, _ = make_mesh(t, shape.h, shape.w, 16, fine)
        near = Tms(t.to_bytes())
        far = Tms(t.to_bytes())
        cols, rows = 16, 2
        inp = bytearray(cols * TILE * rows * TILE * 4)
        raws = {"indirection": texture(4, 4, bytearray(4 * 4 * 4)),
                "inputs": texture(cols * TILE, rows * TILE, inp),
                "flow": texture(cols * TILE, rows * TILE, bytearray(len(inp)))}
        out, said = water_pictures(raws, near, far, shape, fine, 1000.0)
        _t, ind = _pixels(out["indirection"])
        tiles = {(x, y): tuple(ind[(y * 4 + x) * 4:(y * 4 + x) * 4 + 4]) for y in range(3) for x in range(2)}
        open_sea = {tiles[(0, 0)], tiles[(1, 0)], tiles[(0, 1)], tiles[(1, 1)], tiles[(0, 2)]}
        self.assertEqual(len(open_sea), 1)                 # the open sea: one shared tile
        self.assertNotEqual(tiles[(1, 2)], tiles[(0, 0)])  # the island's cell: its own
        self.assertIn("1 sampled by the shores", said)
        _t, new_inp = _pixels(out["inputs"])
        t0 = tiles[(0, 0)]
        tile = t0[1] * cols + t0[2]
        texel = ((tile // cols) * TILE * cols * TILE + (tile % cols) * TILE) * 4
        self.assertEqual(new_inp[texel + 2], 5)            # 20 deep over a scale of 1000: 255 * 0.02 = 5

    def test_a_sliver_of_sea_round_an_island_is_sea_not_other_water(self):
        # an island all but filling the middle cell: a band of sea along its sides narrower than half a texel
        size = 3 * CASE
        t = Tms(make_tms(gw=3, gh=3, n=5))
        t.bounds = [0.0, 0.0, -100.0, size, size, 3176.7]
        t.cell_w = t.cell_h = CASE
        shape = Shape([Stroke(brush="level", x=size / 2, y=size / 2, radius=size, level=0.0, weight=1.0,
                              shape="square", edge="hard"),
                       Stroke(brush="water", x=size / 2, y=size / 2, radius=size, level=20.0, shape="square",
                              edge="hard"),
                       Stroke(brush="plateau", x=1.5 * CASE, y=1.5 * CASE, radius=0.52 * CASE, level=50.0,
                              weight=1.0, shape="square", edge="hard")], (0.0, 0.0, size, size), 20.0)
        fine = fine_cells(t, shape)
        t.cells, _ = make_mesh(t, shape.h, shape.w, 64, fine)   # (a point every quarter texel: a band that thin)
        near = Tms(t.to_bytes())
        _red, share, _mean = _cell(_water_triangles(near, (3, 3)).get((1, 1), []), 1, 1, 1000.0)
        self.assertTrue(any(share) and max(share) < 0.5, max(share))   # (it is a sliver: some water, no texel half)
        cols, rows = 16, 2
        inp = bytearray(cols * TILE * rows * TILE * 4)
        raws = {"indirection": texture(4, 4, bytearray(4 * 4 * 4)),
                "inputs": texture(cols * TILE, rows * TILE, inp),
                "flow": texture(cols * TILE, rows * TILE, bytearray(len(inp)))}
        out, _said = water_pictures(raws, near, Tms(t.to_bytes()), shape, fine, 1000.0)
        _t, ind = _pixels(out["indirection"])
        self.assertEqual([ind[(y * 4 + x) * 4] for y in range(3) for x in range(3)], [0] * 9)   # all of it the sea


if __name__ == "__main__":
    unittest.main()
