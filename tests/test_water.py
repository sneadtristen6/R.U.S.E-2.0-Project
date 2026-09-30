"""Water brushes (rusemod.brush), the meshes' water rules (rusemod.tms) and the water textures' depth (rusemod.water),
on made-up meshes (tests/test_tms.py builds them)."""
import unittest

from rusemod.brush import BrushError, parse_strokes
from rusemod.tms import Tms
from rusemod.water import CASE, TILE, _cell, apply_water

from test_tms import make_tms


def flat(level_q):
    """A 3 x 3 cell map, flat ground at z quantum 1000 (world 0.0), every vertex's water at `level_q`."""
    t = Tms(make_tms(gw=3, gh=3, n=11, zf=lambda x, y: 1000))
    for k, c in enumerate(t.cells):
        t.set_water(k, {i: level_q for i in range(len(c.positions()))})
    return Tms(t.to_bytes())


class Brushes(unittest.TestCase):
    def test_water_needs_a_level_and_drain_nothing(self):
        w, d = parse_strokes([{"brush": "water", "x": 1, "y": 2, "radius": 3, "level": 9000},
                              {"brush": "drain", "x": 1, "y": 2, "radius": 3}])
        self.assertEqual((w.brush, w.level, d.brush), ("water", 9000.0, "drain"))
        with self.assertRaises(BrushError):
            parse_strokes([{"brush": "water", "x": 1, "y": 2, "radius": 3}])

    def test_water_brushes_never_move_the_ground(self):
        w, d = parse_strokes([{"brush": "water", "x": 0, "y": 0, "radius": 10, "level": 9000},
                              {"brush": "drain", "x": 0, "y": 0, "radius": 10}])
        self.assertEqual(w.height_at(0, 0, 123.0), 123.0)
        self.assertEqual(d.height_at(0, 0, 123.0), 123.0)


class MeshWater(unittest.TestCase):
    def test_dry_map_has_no_water_lists_and_zero_low_bounds(self):
        t = flat(500)                                   # water under the ground everywhere
        for c in t.cells:
            self.assertEqual(c.flags & 2, 0)
            self.assertEqual(c.triangles(1), [])
            for p in c.patch_list():
                self.assertEqual(p.zlo, 0.0)            # the shipped rule for a cell without water
                self.assertEqual((p.i1start, p.i1count), (0, 0))
        self.assertEqual(t.base_water(), 500)

    def test_a_lake_is_copied_ground_triangles_with_bounds_by_the_cell_rule(self):
        t = flat(500)
        c = t.cells[4]
        pos = c.positions()
        # flood the vertices of the cell's left half: water at quantum 1200 (20 world units above the ground)
        left = {i: 1200 for i, p in enumerate(pos) if p[0] <= (pos[0][0] + pos[-1][0]) // 2}
        self.assertEqual(t.set_water(4, left), len(left))
        back = Tms(t.to_bytes())
        c = back.cells[4]
        pos, tri0, tri1 = c.positions(), c.triangles(0), c.triangles(1)
        self.assertEqual(c.flags & 2, 2)
        ground = {tuple(tri0[i:i + 3]) for i in range(0, len(tri0), 3)}
        water = [tuple(tri1[i:i + 3]) for i in range(0, len(tri1), 3)]
        self.assertTrue(water)
        for tri in water:
            self.assertIn(tri, ground)                  # copies of ground triangles, same corner order
            self.assertTrue(all(pos[v][3] >= pos[v][2] for v in tri))
        wanted = [tuple(tri0[i:i + 3]) for i in range(0, len(tri0), 3)
                  if all(pos[v][3] >= pos[v][2] for v in tri0[i:i + 3])]
        self.assertEqual(sorted(water), sorted(wanted))
        for p in c.patch_list():
            run = pos[p.vstart:p.vstart + p.vcount]
            self.assertAlmostEqual(p.zlo, back.to_world(2, min(v[2] for v in run)), 3)
            self.assertAlmostEqual(p.zhi, back.to_world(2, max(max(v[2], v[3]) for v in run)), 3)
        for k in (0, 1, 2, 3, 5, 6, 7, 8):             # the other cells stay dry
            self.assertEqual(back.cells[k].flags & 2, 0)

    def test_draining_removes_the_list_and_the_flag(self):
        t = flat(500)
        n = len(t.cells[4].positions())
        t.set_water(4, {i: 1200 for i in range(n)})
        self.assertEqual(t.cells[4].flags & 2, 2)
        t.set_water(4, {i: 500 for i in range(n)})
        back = Tms(t.to_bytes())
        self.assertEqual(back.cells[4].flags & 2, 0)
        self.assertEqual(back.cells[4].triangles(1), [])
        self.assertTrue(all(p.zlo == 0.0 for p in back.cells[4].patch_list()))

    def test_the_far_mesh_gets_its_own_base_and_offset(self):
        near, far = flat(500), flat(400)                 # far mesh base 10 world units lower (0.1 per quantum)
        strokes = parse_strokes([{"brush": "water", "x": 1500, "y": 1500, "radius": 300, "level": 20.0}])
        notes = apply_water({"highdef": near, "lowdef": far}, strokes)
        self.assertEqual(len(notes), 2)
        lvl_near = {p[3] for c in near.cells for p in c.positions()} - {500}
        lvl_far = {p[3] for c in far.cells for p in c.positions()} - {400}
        self.assertEqual(lvl_near, {near.to_quant(2, 20.0)})
        self.assertEqual(lvl_far, {far.to_quant(2, 10.0)})
        drained = parse_strokes([{"brush": "drain", "x": 1500, "y": 1500, "radius": 300}])
        apply_water({"highdef": near, "lowdef": far}, drained)
        self.assertEqual({p[3] for c in near.cells for p in c.positions()}, {500})   # back to each mesh's base
        self.assertEqual({p[3] for c in far.cells for p in c.positions()}, {400})


class TextureDepth(unittest.TestCase):
    def test_red_is_depth_over_the_maps_scale(self):
        big = ((-10.0, -10.0), (3 * CASE, -10.0), (-10.0, 3 * CASE))   # covers cell (0, 0) completely
        red, share, level = _cell([(big, (500.0, 500.0, 500.0), (9000.0, 9000.0, 9000.0))], 0, 0, 1000.0)
        self.assertEqual(len(red), TILE * TILE)
        self.assertTrue(all(r == 128 for r in red))     # 255 * 500 / 1000, rounded
        self.assertTrue(all(s == 1.0 for s in share))
        self.assertAlmostEqual(level[0], 9000.0)
        red, *_ = _cell([(big, (5000.0, 5000.0, 5000.0), (9000.0,) * 3)], 0, 0, 1000.0)
        self.assertTrue(all(r == 255 for r in red))     # capped
        red, share, _ = _cell([], 0, 0, 1000.0)
        self.assertEqual((max(red), max(share)), (0, 0.0))


if __name__ == "__main__":
    unittest.main()
