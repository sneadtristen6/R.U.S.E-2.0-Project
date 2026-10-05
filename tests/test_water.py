"""Water brushes (rusemod.brush), the meshes' water rules (rusemod.tms) and the water textures' depth (rusemod.water),
on made-up meshes (tests/test_tms.py builds them)."""
import unittest

from rusemod.brush import BrushError, parse_strokes
from rusemod.tms import Q_MAX, Tms
from rusemod.tmst import make_tgv, zipo_pack
from rusemod.water import (CASE, SAMPLES, TEXTURES, TILE, _both, _cell, _pixels, _texels, apply_water,
                           update_textures)

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


class FarMesh(unittest.TestCase):
    def test_the_far_mesh_floods_only_where_the_close_up_ground_is_under_the_water(self):
        near, far = flat(500), flat(400)
        # a level under the (flat, world 0.0) ground: the close-up mesh records it, nothing floods, the far mesh
        # leaves its points alone
        strokes = parse_strokes([{"brush": "water", "x": 1500, "y": 1500, "radius": 300, "level": -5.0}])
        apply_water({"highdef": near, "lowdef": far}, strokes)
        self.assertEqual({p[3] for c in far.cells for p in c.positions()}, {400})
        self.assertTrue(all(not c.flags & 2 for c in near.cells))


class TextureDepth(unittest.TestCase):
    def test_far_only_water_is_covered_and_the_shore_gets_one_texel_of_spill(self):
        n = TILE * TILE
        near = ([0] * n, [0.0] * n, [0.0] * n)
        far = ([0] * n, [0.0] * n, [0.0] * n)
        far[0][0], far[1][0], far[2][0] = 200, 1.0, 8349.0     # water only the far mesh draws, in the corner texel
        red, share, level = _both(near, far, 152.0)
        self.assertEqual((red[0], share[0], level[0]), (200, 1.0, 8501.0))
        self.assertEqual(red[1], 200)                            # the texel beside it: spill onto the shore
        self.assertEqual(share[1], 0.0)                          # spill isn't counted as water
        self.assertEqual(red[TILE + 1], 200)                     # diagonal neighbour too
        self.assertEqual(red[2], 0)                              # two texels away: dry


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


def texture(width, height, px):
    return make_tgv(width, height, "A8R8G8B8_LIN", [zipo_pack(bytes(px))])


class TextureTiles(unittest.TestCase):
    """A map 2 water cells across and 3 down (the maps aren't all square: D-Day is 144 x 96), whose atlas is 16
    tiles across (4 maps have 16, 7 have 64, the rest 32): a lake in its last row gets a tile of its own, and the
    cell's (G, R) say that tile's row and column of the atlas."""

    def test_a_new_lake_in_a_tall_map_with_a_narrow_atlas(self):
        t = Tms(make_tms(gw=2, gh=3, n=5, zf=lambda x, y: 1000))
        t.bounds = [0.0, 0.0, -100.0, 2 * CASE, 3 * CASE, 3176.7]  # one mesh cell per water cell
        before = Tms(t.to_bytes())
        after = Tms(t.to_bytes())
        after.set_water(5, {i: 1200 for i in range(len(after.cells[5].positions()))})  # cell (1, 2): 20 deep
        after = Tms(after.to_bytes())
        ind = bytearray(4 * 4 * 4)                     # every cell on tile 0, the dry one
        cols, rows = 16, 2
        inp = bytearray(cols * TILE * rows * TILE * 4)
        for t_used in range(1, 18):                    # tiles 1-17 hold something: the first free one is 18
            row, col = divmod(t_used, cols)
            inp[(row * TILE * cols * TILE + col * TILE) * 4] = 1
        flow = bytearray(len(inp))
        raws = {TEXTURES["indirection"]: texture(4, 4, ind), TEXTURES["inputs"]: texture(cols * TILE, rows * TILE, inp),
                TEXTURES["flow"]: texture(cols * TILE, rows * TILE, flow)}
        out, notes = update_textures(raws.get, before, after, [(1.5 * CASE, 2.5 * CASE, 100.0)], 1000.0, "test")
        self.assertIn("1 cell(s) updated, 1 new tile(s)", notes[0])
        _t, new_ind = _pixels(out[TEXTURES["indirection"]])
        o = (2 * 4 + 1) * 4
        self.assertEqual(tuple(new_ind[o:o + 4]), (255, 1, 2, 0))  # tile 18: row 1, column 2 (not 0, 18)
        _t, new_inp = _pixels(out[TEXTURES["inputs"]])
        corner = (1 * TILE * cols * TILE + 2 * TILE) * 4  # that tile's first texel: the cell's column and row
        self.assertEqual((new_inp[corner], new_inp[corner + 3]), (1, 2))
        self.assertEqual(new_inp[corner + 2], 5)          # its depth: 255 * 20 / 1000

    def test_water_over_the_whole_map_shares_one_tile(self):
        """A thin layer over all of a flat map (Water over the whole map): every cell still water at the base level,
        one depth all over, so one tile serves them all, as the shipped sea's does (D-Day's atlas holds 4,096 tiles
        for 13,824 cells): no cell's place in it, no flow."""
        t = Tms(make_tms(gw=2, gh=3, n=5, zf=lambda x, y: 1000))
        t.bounds = [0.0, 0.0, -100.0, 2 * CASE, 3 * CASE, 3176.7]
        before = Tms(t.to_bytes())
        after = Tms(t.to_bytes())
        for k, c in enumerate(after.cells):  # every point under 20 of water: that level is now the map's base
            after.set_water(k, {i: 1200 for i in range(len(c.positions()))})
        after = Tms(after.to_bytes())
        cols, rows = 16, 2
        inp = bytearray(cols * TILE * rows * TILE * 4)
        inp[0] = 1                                    # tile 0 holds something (the dry tile every cell is on)
        raws = {TEXTURES["indirection"]: texture(4, 4, bytearray(4 * 4 * 4)),
                TEXTURES["inputs"]: texture(cols * TILE, rows * TILE, inp),
                TEXTURES["flow"]: texture(cols * TILE, rows * TILE, bytearray(len(inp)))}
        out, notes = update_textures(raws.get, before, after, [(CASE, 1.5 * CASE, 2 * CASE)], 1000.0, "test")
        self.assertIn("6 cell(s) updated, 1 new tile(s)", notes[0])
        _t, ind = _pixels(out[TEXTURES["indirection"]])
        self.assertEqual({tuple(ind[(y * 4 + x) * 4:(y * 4 + x) * 4 + 4]) for y in range(3) for x in range(2)},
                         {(0, 0, 1, 0)})          # all on tile 1, still water (not a river's)
        _t, new_inp = _pixels(out[TEXTURES["inputs"]])
        tile = {bytes(new_inp[(y * cols * TILE + TILE + x) * 4:(y * cols * TILE + TILE + x) * 4 + 4])
                for y in range(TILE) for x in range(TILE)}
        self.assertEqual(tile, {bytes((0, 0, 5, 0))})


# --- the texels as they were worked out sample by sample, kept here to check the quicker way against, to the bit ---
def plain_cell(tris, col, row, max_depth):
    n = TILE * SAMPLES
    h = CASE / n
    depth = [[0.0] * n for _ in range(n)]
    level = [[0.0] * n for _ in range(n)]
    wet = [[False] * n for _ in range(n)]
    x0, y0 = col * CASE, row * CASE
    for (a, b, c), d, w in tris:
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if den == 0:
            continue
        i0 = max(int((min(a[0], b[0], c[0]) - x0) / h - 0.5), 0)
        i1 = min(int((max(a[0], b[0], c[0]) - x0) / h + 0.5), n - 1)
        j0 = max(int((min(a[1], b[1], c[1]) - y0) / h - 0.5), 0)
        j1 = min(int((max(a[1], b[1], c[1]) - y0) / h + 0.5), n - 1)
        for j in range(j0, j1 + 1):
            py = y0 + (j + 0.5) * h
            for i in range(i0, i1 + 1):
                if wet[j][i]:
                    continue
                px = x0 + (i + 0.5) * h
                l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
                l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
                l3 = 1.0 - l1 - l2
                if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                    wet[j][i] = True
                    depth[j][i] = l1 * d[0] + l2 * d[1] + l3 * d[2]
                    level[j][i] = l1 * w[0] + l2 * w[1] + l3 * w[2]
    red, share, mean = [], [], []
    for ty in range(TILE):
        for tx in range(TILE):
            r = k = 0
            lv = 0.0
            for j in range(ty * SAMPLES, ty * SAMPLES + SAMPLES):
                for i in range(tx * SAMPLES, tx * SAMPLES + SAMPLES):
                    if wet[j][i]:
                        k += 1
                        lv += level[j][i]
                        r += 255.0 * min(max(depth[j][i] / max_depth, 0.0), 1.0)
            red.append(int(r / (SAMPLES * SAMPLES) + 0.5))
            share.append(k / (SAMPLES * SAMPLES))
            mean.append(lv / k if k else 0.0)
    return red, share, mean


def plain_both(near, far, far_offset=0.0):
    red, share, mean = (list(v) for v in near)
    if far is not None:
        for i in range(TILE * TILE):
            if not share[i] and far[1][i]:
                red[i], share[i], mean[i] = far[0][i], far[1][i], far[2][i] + far_offset
    spill = list(red)
    for i in range(TILE * TILE):
        if share[i]:
            continue
        x, y = i % TILE, i // TILE
        around = [red[yy * TILE + xx] for yy in range(max(y - 1, 0), min(y + 2, TILE))
                  for xx in range(max(x - 1, 0), min(x + 2, TILE)) if share[yy * TILE + xx]]
        if around:
            spill[i] = max(around)
    return spill, share, mean


def random_water(rng, col, row, count):
    """Water triangles over and around a cell: big and small, slivers, flat ones, depths below 0 and past the scale."""
    out = []
    for _ in range(count):
        cx, cy = (col + rng.uniform(-0.3, 1.3)) * CASE, (row + rng.uniform(-0.3, 1.3)) * CASE
        size = CASE * rng.choice((0.02, 0.1, 0.4, 1.5))
        corners = tuple((cx + rng.uniform(-size, size), cy + rng.uniform(-size, size)) for _ in range(3))
        if rng.random() < 0.1:   # a sliver: its third corner on (or next to) the line of the other two
            (ax, ay), (bx, by), _c = corners
            corners = ((ax, ay), (bx, by), ((ax + bx) / 2, (ay + by) / 2 + rng.choice((0.0, 1e-7))))
        out.append((corners, tuple(rng.uniform(-300.0, 7000.0) for _ in range(3)),
                    tuple(rng.uniform(8000.0, 9000.0) for _ in range(3))))
    return out


class QuickTexels(unittest.TestCase):
    """The water texels worked out the quicker way are the very same as sample by sample: every R, share and level, to
    the bit (repr tells -0.0 from 0.0), and the cells' texels shared out to worker programs are the same as one
    program's."""

    def test_a_cell_is_the_same_as_sample_by_sample(self):
        import random
        rng = random.Random(7)
        for k in range(40):
            col, row = rng.randrange(3), rng.randrange(3)
            tris = random_water(rng, col, row, rng.choice((0, 1, 3, 12, 40)))
            depth = rng.choice((1000.0, 5000.0))
            with self.subTest(k=k):
                self.assertEqual(repr(_cell(tris, col, row, depth)), repr(plain_cell(tris, col, row, depth)))

    def test_now_and_before_as_sample_by_sample(self):
        """_texels: the texels now as _both of the cells; before as well, except a cell dry now that had water (said as
        None): sample by sample, some texel of it changed then."""
        import random
        rng = random.Random(11)
        dried = full = 0
        for k in range(60):
            col, row = rng.randrange(3), rng.randrange(3)
            pick = lambda: rng.choice(([], [], random_water(rng, col, row, 4), random_water(rng, col, row, 30)))
            near, far, near0, far0 = pick(), pick(), pick(), pick()
            if k % 5 == 0:
                far = far0 = None   # no far mesh
            if k % 7 == 0:          # a cell wholly under the close-up mesh's water
                big = (((col - 1) * CASE, (row - 1) * CASE), ((col + 3) * CASE, (row - 1) * CASE),
                       ((col - 1) * CASE, (row + 3) * CASE))
                near = [(big, (40.0, 50.0, 60.0), (8500.0,) * 3)]
            red, share, mean, old = _texels((col, row, near, far, near0, far0), 1000.0, 152.0)
            want = plain_both(plain_cell(near, col, row, 1000.0),
                              plain_cell(far, col, row, 1000.0) if far is not None else None, 152.0)
            want0 = plain_both(plain_cell(near0, col, row, 1000.0),
                               plain_cell(far0, col, row, 1000.0) if far0 is not None else None, 152.0)
            with self.subTest(k=k):
                self.assertEqual(repr((red, share, mean)), repr(want))
                if old is None:
                    dried += 1
                    self.assertFalse(any(share))
                    self.assertTrue(any(abs(a - b) > 0.01 for a, b in zip(share, want0[1])))
                else:
                    full += any(share)
                    self.assertEqual(repr(old), repr(want0))
        self.assertGreater(dried, 3)
        self.assertGreater(full, 3)

    def shore_map(self):
        """A map 3 water cells square (one mesh cell each) half under the sea, then (after) partly raised dry, partly
        deepened, and a lake in the east; its three textures with the sea and dry tiles shared."""
        half = Q_MAX // 2
        t = Tms(make_tms(gw=3, gh=3, n=9, zf=lambda x, y: 800 if x < half else 1000))
        t.bounds = [0.0, 0.0, -100.0, 3 * CASE, 3 * CASE, 3176.7]
        for k, c in enumerate(t.cells):
            t.set_water(k, {i: 900 for i in range(len(c.positions()))})
        before = Tms(t.to_bytes())
        after = Tms(t.to_bytes())
        for k in (0, 3):          # the north-west and west cells raised dry
            after.set_heights(k, {i: 1000 for i in range(len(after.cells[k].positions()))})
        after.set_heights(6, {i: 500 for i, p in enumerate(after.cells[6].positions()) if p[0] < half})  # deeper
        after.set_water(5, {i: 1100 for i in range(len(after.cells[5].positions()))})                   # a lake
        after = Tms(after.to_bytes())
        far_before, far_after = Tms(before.to_bytes()), Tms(after.to_bytes())
        cols, rows = 16, 2
        ind = bytearray(4 * 4 * 4)
        inp = bytearray(cols * TILE * rows * TILE * 4)
        for cy in range(3):
            for cx in range(3):
                ind[(cy * 4 + cx) * 4 + 2] = 1 if cx < 2 else 0     # the west two columns on the sea tile (1)
        inp[((8 * cols * TILE) + TILE + 8) * 4 + 2] = 255            # the sea tile's middle texel: full depth
        flow = bytearray(len(inp))
        raws = {TEXTURES["indirection"]: texture(4, 4, ind), TEXTURES["inputs"]: texture(cols * TILE, rows * TILE, inp),
                TEXTURES["flow"]: texture(cols * TILE, rows * TILE, flow)}
        return raws, before, after, far_before, far_after

    def textures(self, workers):
        raws, before, after, far_before, far_after = self.shore_map()
        return update_textures(raws.get, before, after, [(1.5 * CASE, 1.5 * CASE, 2 * CASE)], 1000.0, "test",
                               far_before=far_before, far_after=far_after, workers=workers)

    def test_the_cells_shared_out_give_the_same_textures(self):
        from unittest import mock
        from rusemod import water
        one = self.textures(1)
        self.assertTrue(one[0], one[1])
        self.assertIn("cell(s) updated", one[1][0])
        with mock.patch.object(water, "SHARE_FROM", 1):
            self.assertEqual(self.textures(2), one)     # two worker programs: the same bytes, the same notes

    def test_workers_that_cant_start_are_said(self):
        """Worker programs that can't start: the same work done in this program, and a note saying so."""
        from unittest import mock
        from rusemod import water

        def no_pool(*_args):
            raise OSError("no programs here")
        one = self.textures(1)
        with mock.patch.object(water, "SHARE_FROM", 1), mock.patch.object(water, "_pool", no_pool):
            out, notes = self.textures(4)
        self.assertEqual(out, one[0])
        self.assertEqual(notes[:-1], one[1])
        self.assertEqual(notes[-1], "test: the water textures were worked out on one core: the worker programs "
                                    "couldn't start (OSError: no programs here)")


if __name__ == "__main__":
    unittest.main()
