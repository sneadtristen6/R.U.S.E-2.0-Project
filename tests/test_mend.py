"""Mending a filled hollow's pictures (rusemod.mend): on made-up grids and meshes, never proof of what the game shows."""
import unittest

from rusemod import mend


class FakeCell:
    def __init__(self, pos, tri):
        self._pos, self._tri = pos, tri

    def positions(self):
        return self._pos

    def triangles(self, k):
        return self._tri


class FakeMesh:
    """A mesh whose quantized values are world units already: a grid of points `step` apart with height z(x, y)."""

    def __init__(self, n, step, z):
        pos = [(i * step, j * step, z(i * step, j * step), 0) for j in range(n) for i in range(n)]
        tri = []
        for j in range(n - 1):
            for i in range(n - 1):
                a, b, c, d = j * n + i, j * n + i + 1, (j + 1) * n + i, (j + 1) * n + i + 1
                tri += [a, b, c, b, d, c]
        self.cells = [FakeCell(pos, tri)]

    def to_world(self, axis, q):
        return float(q)


class SlideTest(unittest.TestCase):
    def test_a_running_window_gives_the_highest_and_lowest_either_side(self):
        v = [3, 1, 4, 1, 5, 9, 2, 6]
        self.assertEqual(mend._slide(v, 1, max), [3, 4, 4, 5, 9, 9, 9, 6])
        self.assertEqual(mend._slide(v, 1, min), [1, 1, 1, 1, 1, 2, 2, 2])
        self.assertEqual(mend._slide(v, 0, max), v)


class GorgeTest(unittest.TestCase):
    def test_a_narrow_hollow_is_found_and_the_plain_round_it_is_not(self):
        # a plain at 10,000 with a trench 20 m wide and 10 m deep running down x = 100 m
        m = 260.0
        mesh = FakeMesh(81, 2.5 * m, lambda x, y: 10000.0 - (2600.0 if abs(x - 100 * m) < 10 * m else 0.0))
        g = mend.Gorge(mesh, (60 * m, 60 * m, 140 * m, 140 * m), wider=0.0)
        self.assertTrue(g.holds(100 * m, 100 * m))
        self.assertTrue(g.holds(95 * m, 80 * m))
        self.assertFalse(g.holds(80 * m, 100 * m))
        self.assertFalse(g.holds(125 * m, 100 * m))
        wide = mend.Gorge(mesh, (60 * m, 60 * m, 140 * m, 140 * m), wider=4 * m)
        self.assertTrue(wide.holds(112 * m, 100 * m))   # the rim, 2 m past the trench's edge
        self.assertFalse(wide.holds(120 * m, 100 * m))


class FilledTest(unittest.TestCase):
    m = 260.0

    def trench(self, depth):
        """A plain at 10,000 with a trench 20 m wide and `depth` deep down x = 100 m."""
        m = self.m
        return FakeMesh(81, 2.5 * m, lambda x, y: 10000.0 - (depth if abs(x - 100 * m) < 10 * m else 0.0))

    def test_a_riverbed_raised_flat_is_filled_and_one_still_a_dip_is_not(self):
        m = self.m
        box = (60 * m, 60 * m, 140 * m, 140 * m)
        flat = mend.Filled(self.trench(2600.0), self.trench(0.0), box)
        self.assertTrue(flat.holds(100 * m, 100 * m))
        self.assertTrue(flat.hollow(100 * m, 100 * m))
        self.assertFalse(flat.holds(80 * m, 100 * m))
        self.assertGreater(flat.count(), 0)
        x0, _y0, x1, _y1 = flat.box()
        self.assertLess(x0, 92 * m)
        self.assertGreater(x1, 108 * m)
        self.assertTrue(flat.touches(80 * m, 100 * m, 25 * m))   # a sticker 20 m off, reaching 25 m: into it
        self.assertFalse(flat.touches(70 * m, 100 * m, 10 * m))
        half = mend.Filled(self.trench(2600.0), self.trench(1300.0), box)  # raised, but still 5 m down
        self.assertEqual(half.count(), 0)
        self.assertIsNone(half.box())


class PlanTest(unittest.TestCase):
    def test_every_point_takes_its_ground_from_beyond_the_banks_and_the_weights_sum_to_one(self):
        nx, ny = 70, 8
        bits = bytearray(1 if 30 <= k % nx < 50 else 0 for k in range(nx * ny))
        plan = mend.Plan(nx, ny, bits, bits, step=1.0)
        for x in (30.2, 34.5, 40.0, 45.5, 49.8):
            src = plan.sources(x, 4.5, 2.0, 0.5)
            self.assertAlmostEqual(sum(w for w, _s, _b in src), 1.0)
            self.assertTrue(all(not 30 <= s[0] < 50 for _w, s, _b in src), (x, src))
        self.assertIsNone(plan.sources(10.5, 4.5, 2.0, 0.5))  # not in the hollow


class MendGridTest(unittest.TestCase):
    def test_each_bank_lends_its_ground_mirrored_and_the_middle_blends_both(self):
        # 20 x 6 pixels; columns 7 to 12 are the hollow (dark); the ground left of it is (100 + column), right (200 + column)
        # 70 x 6 pixels; columns 30 to 49 are the hollow (dark); the ground left of it is 100, right of it 200
        nx, ny = 70, 6
        hollow = set(range(30, 50))

        def sample(fx, fy):
            i = int(fx)
            if not 0 <= i < nx:
                return None
            return (0,) if i in hollow else ((100,) if i < 30 else (200,))
        got = mend.mend_grid(nx, ny, lambda i, j: i in hollow, lambda i, j: i in hollow, sample, ease=2.0)
        self.assertEqual({i for i, _j in got}, hollow)
        row = [got[(i, 3)][0] for i in sorted(hollow)]
        self.assertEqual(row[0], 100)                      # by each bank, its own ground
        self.assertEqual(row[-1], 200)
        self.assertEqual(row, sorted(row))                 # one side to the other, never back
        self.assertLess(abs(row[9] - 150), 20)             # the middle about half of each
        self.assertTrue(all(v[0] >= 100 for v in got.values()))  # never the hollow's own dark

    def test_away_from_the_bank_the_ground_is_moved_across_not_mirrored(self):
        # columns 30 to 49 the hollow; left of it the ground's value is 1000 + column squared, right of it 5000
        nx, ny = 70, 6
        hollow = set(range(30, 50))

        def sample(fx, fy):
            i = int(fx)
            if not 0 <= i < nx:
                return None
            return (0,) if i in hollow else ((1000 + i * i,) if i < 30 else (5000,))
        got = mend.mend_grid(nx, ny, lambda i, j: i in hollow, lambda i, j: i in hollow, sample, ease=2.0, cross=0.2)
        # column 34: its bank's edge pixel is column 29, 5 px away; the far bank 16 px on: the hollow is 21 wide there,
        # so the ground taken is 16 beyond the bank's edge (column 13), not the mirror 5 beyond (column 24)
        self.assertEqual(got[(34, 3)][0], 1000 + 13 * 13)
        # right by the bank, nearly the mirror: column 30 (a pixel in, the mirror being column 28's 1,784, the ground
        # moved across column 9's 1,081) with the mirror kept for 8 pixels
        eased = mend.mend_grid(nx, ny, lambda i, j: i in hollow, lambda i, j: i in hollow, sample, ease=8.0, cross=0.2)
        self.assertLess(abs(eased[(30, 3)][0] - (1000 + 28 * 28)), 40)

    def test_a_pixel_not_asked_for_is_left(self):
        got = mend.mend_grid(10, 3, lambda i, j: False, lambda i, j: 3 <= i <= 5, lambda fx, fy: (int(fx),))
        self.assertEqual(got, {})


class WetMesh(FakeMesh):
    """FakeMesh whose water (triangle list 1) covers only the squares with x below `wet_x`."""

    def __init__(self, n, step, z, wet_x):
        super().__init__(n, step, z)
        cell = self.cells[0]
        pos, ground = cell._pos, cell._tri
        water = [v for t in range(0, len(ground), 3) for v in ground[t:t + 3]
                 if max(pos[k][0] for k in ground[t:t + 3]) <= wet_x]

        class Cell(FakeCell):
            def triangles(self, k):
                return water if k == 1 else ground
        self.cells = [Cell(pos, ground)]


class RiverbedsOnlyTest(unittest.TestCase):
    """The build mends riverbeds only: the stretches of filled hollows that reach the old water (mend.riverbeds_only),
    window by window (mend.Riverbeds); a dry dip raised flat is left as it is."""
    m = 260.0

    def test_the_old_water_is_found_from_the_mesh(self):
        m = self.m
        mesh = WetMesh(41, 2.5 * m, lambda x, y: 10000.0, wet_x=40 * m)
        wet = mend.wet_bits(mesh, 0.0, 0.0, 40, 40, 2.5 * m)
        self.assertTrue(wet[10 * 40 + 5])          # x = 13.75 m: under the water
        self.assertFalse(wet[10 * 40 + 30])        # x = 76 m: dry

    def test_only_the_stretches_reaching_the_water_are_kept(self):
        nx, ny = 20, 4
        filled = mend.Filled.__new__(mend.Filled)
        filled.nx, filled.ny = nx, ny
        # two stretches: columns 2-4 (one of its squares wet) and columns 10-12 (dry)
        filled.bits = bytearray(1 if (2 <= k % nx <= 4 or 10 <= k % nx <= 12) else 0 for k in range(nx * ny))
        wet = bytearray(nx * ny)
        wet[1 * nx + 3] = 1
        gone = mend.riverbeds_only(filled, wet)
        self.assertEqual(gone, 3 * ny)
        self.assertTrue(all(filled.bits[j * nx + i] for i in (2, 3, 4) for j in range(ny)))
        self.assertFalse(any(filled.bits[j * nx + i] for i in (10, 11, 12) for j in range(ny)))

    def test_the_windows_answer_as_one(self):
        m = self.m
        box = (60 * m, 60 * m, 140 * m, 140 * m)
        trench = lambda depth: FakeMesh(81, 2.5 * m, lambda x, y: 10000.0 - (depth if abs(x - 100 * m) < 10 * m else 0))
        whole = mend.Filled(trench(2600.0), trench(0.0), box)
        beds = mend.Riverbeds(0.0, 0.0, 100 * m, {(0, 0): whole, (1, 0): whole})  # two windows, y below 100 m
        for x, y in ((100 * m, 70 * m), (80 * m, 70 * m), (95 * m, 90 * m), (104 * m, 80 * m)):
            self.assertEqual(beds.holds(x, y), whole.holds(x, y), (x, y))
        self.assertTrue(beds.holds(100 * m, 70 * m))
        self.assertFalse(beds.holds(100 * m, 120 * m))  # a window not given: nothing there
        self.assertEqual(beds.touches(80 * m, 70 * m, 25 * m), whole.touches(80 * m, 70 * m, 25 * m))
        self.assertEqual(beds.count(), 2 * whole.count())
        self.assertEqual(beds.box(), whole.box())
        self.assertIsNone(mend.Riverbeds(0.0, 0.0, 100 * m, {}).box())

    def test_a_dry_dip_raised_flat_isnt_mended(self):
        """mend_map with no water under the strokes: nothing to mend, nothing read."""
        m = self.m
        trench = lambda depth: WetMesh(81, 2.5 * m, lambda x, y: 10000.0 - (depth if abs(x - 100 * m) < 10 * m else 0),
                                       wet_x=-1.0)  # no water anywhere
        before, after = trench(2600.0), trench(0.0)
        before.bounds = after.bounds = (0.0, 0.0, 0.0, 200 * m, 200 * m, 0.0)

        def read(member):
            raise AssertionError(f"nothing to mend, but {member} was read")
        self.assertEqual(mend.mend_map(read, str, {}, before, after, [(100 * m, 100 * m, 40 * m)]), (None, []))


class QuickEncoderTest(unittest.TestCase):
    def test_a_block_comes_back_close_and_a_plain_one_exactly(self):
        from rusemod import dxt
        plain = [(40, 120, 60)] * 16
        self.assertEqual(dxt.block_pixels(dxt.encode_block_quick(plain)), dxt.block_pixels(dxt.encode_block(plain)))
        grain = [(40 + 9 * (k % 4), 110 + 6 * (k // 4), 55 + k) for k in range(16)]
        back = dxt.block_pixels(dxt.encode_block_quick(grain))
        self.assertLess(max(abs(a - b) for p, q in zip(grain, back) for a, b in zip(p, q)), 24)


if __name__ == "__main__":
    unittest.main()
