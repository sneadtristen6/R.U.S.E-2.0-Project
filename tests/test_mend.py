"""Mending a filled hollow's pictures (rusemod.mend): on made-up grids and meshes, never proof of what the game shows."""
import random
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

    def test_the_first_look_far_from_riverbeds_changes_no_answer(self):
        """Riverbeds.touches answers "no" at once far from every riverbed (its near map): every answer is the same as
        the Filled's own, close by or far, for reaches up to NEAR and past it."""
        m = self.m
        box = (60 * m, 60 * m, 140 * m, 140 * m)
        trench = lambda depth: FakeMesh(81, 2.5 * m, lambda x, y: 10000.0 - (depth if abs(x - 100 * m) < 10 * m else 0))
        whole = mend.Filled(trench(2600.0), trench(0.0), box)
        beds = mend.Riverbeds(-1000 * m, -1000 * m, 4000 * m, {(0, 0): whole})  # one window round all of it
        for x in range(30, 171, 3):
            for reach in (0.5, 4.0, 12.0, 29.0, 45.0):
                self.assertEqual(beds.touches(x * m, 100 * m, reach * m), whole.touches(x * m, 100 * m, reach * m),
                                 (x, reach))

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

    def test_workers_that_cant_start_are_said(self):
        """Worker programs that can't start: the same work done in this program, and a note saying so (on one core a
        big map's riverbeds take many times longer)."""
        from unittest import mock
        from rusemod import groundpaint
        m = self.m
        box = (60 * m, 60 * m, 140 * m, 140 * m)
        trench = lambda depth: FakeMesh(81, 2.5 * m, lambda x, y: 10000.0 - (depth if abs(x - 100 * m) < 10 * m else 0))
        whole = mend.Filled(trench(2600.0), trench(0.0), box)
        before, after = trench(2600.0), trench(0.0)
        before.bounds = after.bounds = (0.0, 0.0, 0.0, 200 * m, 200 * m, 0.0)
        before.to_bytes = after.to_bytes = lambda: b""

        def no_pool(*_args):
            raise OSError("no programs here")
        with mock.patch.object(mend, "_windows", lambda b, x, a: [(0, 0, box), (1, 0, box)]), \
                mock.patch.object(mend, "_mend_window", lambda b, a, wi, wj, core: (wi, wj, whole, None, 0)), \
                mock.patch.object(mend, "_pool", no_pool), \
                mock.patch.object(groundpaint, "map_bounds", lambda mesh: (0.0, 0.0, 1.0, 1.0)):
            beds, notes = mend.mend_map(lambda member: None, str, {}, before, after, [(100 * m, 100 * m, 40 * m)],
                                        pack_file="pack.dat", workers=4)
        self.assertEqual(beds.count(), 2 * whole.count())  # both windows mended all the same
        self.assertIn("one core: the worker programs couldn't start (OSError: no programs here)", notes[1])


class WholeMapTest(unittest.TestCase):
    """A whole map's riverbeds (18 million squares over the owner's M04_Cotentin, 2026-10-04): their bounds and the
    squares near them found without looking at each square in Python, the same answers."""

    def test_the_bounds_are_those_of_the_filled_squares(self):
        rng = random.Random(11)
        for k in range(200):
            f = mend.Filled.__new__(mend.Filled)
            f.nx, f.ny, f.step, f.x0, f.y0 = rng.randint(1, 30), rng.randint(1, 20), 650.0, -1300.0, 2600.0
            p = rng.choice((0.0, 0.02, 0.3, 1.0))
            f.bits = bytearray((rng.choice((1, 1, 2)) if rng.random() < p else 0) for _ in range(f.nx * f.ny))
            at = [(i, j) for j in range(f.ny) for i in range(f.nx) if f.bits[j * f.nx + i]]  # square by square
            if not at:
                self.assertIsNone(f.box(), k)
                continue
            cols, rows = [i for i, _j in at], [j for _i, j in at]
            self.assertEqual(f.box(), (f.x0 + min(cols) * f.step, f.y0 + min(rows) * f.step,
                                       f.x0 + (max(cols) + 1) * f.step, f.y0 + (max(rows) + 1) * f.step), k)

    def test_filled_squares_spread_as_the_running_window_spreads_them(self):
        """Riverbeds' near map: mend._spread (a row read as one number, a byte a square) against _filter2(rows, r,
        max), for seeded grids of 0s and 1s, empty and full ones, any reach (past the grid's size too)."""
        rng = random.Random(7)
        for _ in range(150):
            nx, ny = rng.randint(1, 60), rng.randint(1, 40)
            p = rng.choice((0.0, 0.01, 0.1, 0.5, 1.0))
            rows = [[1 if rng.random() < p else 0 for _ in range(nx)] for _ in range(ny)]
            r = rng.randint(0, 70)
            want = bytearray(v for row in mend._filter2(rows, r, max) for v in row)
            self.assertEqual(mend._spread(rows, r), want, (nx, ny, r))


class QuickEncoderTest(unittest.TestCase):
    def test_a_block_comes_back_close_and_a_plain_one_exactly(self):
        from rusemod import dxt
        plain = [(40, 120, 60)] * 16
        self.assertEqual(dxt.block_pixels(dxt.encode_block_quick(plain)), dxt.block_pixels(dxt.encode_block(plain)))
        grain = [(40 + 9 * (k % 4), 110 + 6 * (k // 4), 55 + k) for k in range(16)]
        back = dxt.block_pixels(dxt.encode_block_quick(grain))
        self.assertLess(max(abs(a - b) for p, q in zip(grain, back) for a, b in zip(p, q)), 24)


try:
    import numpy as np
    from rusemod import mendnp
except ImportError:
    np = mendnp = None


def loops():
    """The mend's own loops from here on: whole grids kept away."""
    from unittest import mock
    return mock.patch.object(mend, "whole_arrays", lambda: None)


def same_bits(values, arr) -> bool:
    """A list of floats and a numpy array hold the same numbers, to the last bit."""
    from array import array
    return array("d", values).tobytes() == np.ascontiguousarray(arr, dtype=np.float64).tobytes()


def hills(x, y):
    """A made-up ground: slopes and bumps, no two triangles alike."""
    import math
    return 9000.0 + 1300.0 * math.sin(x / 2100.0) + 900.0 * math.cos(y / 1700.0) + 0.031 * x - 0.017 * y


def lapping_mesh(wet_x=None):
    """Two cells whose triangles lie over one another (the second a third of a square across and higher): a square's
    height is the later triangle's. With `wet_x`: water under the squares left of it."""
    step = 10.0
    mesh = (WetMesh(12, step, hills, wet_x) if wet_x is not None else FakeMesh(12, step, hills))
    pos = [(33.3 + i * step, 21.7 + j * step, hills(i * step, j * step) + 500.0, 0) for j in range(6) for i in range(6)]
    tri = []
    for j in range(5):
        for i in range(5):
            a, b, c, d = j * 6 + i, j * 6 + i + 1, (j + 1) * 6 + i, (j + 1) * 6 + i + 1
            tri += [a, b, c, b, d, c]
    tri += [0, 1, 2, 0, 7, 14, 3, 3, 9]  # triangles with no area (three points in a line, one point twice): skipped
    mesh.cells.append(FakeCell(pos, tri))
    mesh.cells.append(FakeCell([], []))  # an empty cell
    return mesh


@unittest.skipIf(mendnp is None, "numpy isn't here: the mend's own loops do all of it")
class WholeGrids(unittest.TestCase):
    """rusemod.mendnp (numpy) against the mend's own loops, piece by piece, to the last bit: on made-up meshes, grids
    and tiles. The loops are the reference: whole grids made the mend many times faster on a whole flattened map, and
    its pictures must not change for it."""
    m = 260.0

    def same(self, a, b, what=None):
        """Two large values are equal: said without showing them (unittest takes minutes to lay out the difference
        between two tiles' 100,000 bytes)."""
        self.assertTrue(a == b, what)

    def test_floor_division_is_pythons(self):
        """`//` on floats (which square, which tile a point lies in): numpy's floor_divide gives Python's answer, and
        so does mendnp.floor_div (the division floored, and only the whole answers asked of floor_divide)."""
        import math
        import random
        rnd = random.Random(1)
        for step in (650.0, 2080.0, 327680.0 / 4, 0.1, 81920.0, 1.0 / 3):
            xs = [rnd.uniform(-5e6, 5e6) for _ in range(4000)] + [k * step for k in range(-300, 300)]
            # a hair under a whole number of steps the division rounds to it, and the floor is one less
            xs += [float(np.nextafter(x, -np.inf)) for x in xs[4000:]]
            xs += [float(np.nextafter(x, np.inf)) for x in xs[4000:4600]]
            want = [x // step for x in xs]
            self.assertTrue(same_bits(want, np.floor_divide(np.array(xs), step)), step)
            self.assertTrue(same_bits(want, mendnp.floor_div(np.array(xs), step)), step)
            self.assertNotEqual(want, [float(math.floor(x / step)) for x in xs], step)  # (not the division floored)

    def test_a_mesh_laid_on_a_grid(self):
        """mend.heights and mend.wet_bits: the same squares, the same heights, where triangles lie over one another
        too, and whether the squares are gone through in one part or many."""
        from unittest import mock
        mesh = lapping_mesh(wet_x=60.0)
        seen = []
        # (the first grid's middles lie on the mesh's points and edges: squares two triangles hold)
        for x0, y0, nx, ny, step in ((-2.5, -2.5, 50, 50, 5.0), (-13.1, 4.2, 37, 29, 4.7), (40.0, 40.0, 3, 2, 30.0),
                                     (500.0, 500.0, 4, 4, 5.0)):
            want = mend.heights(mesh, x0, y0, nx, ny, step)
            flat = [v for row in want for v in row]
            with loops():
                wet = mend.wet_bits(mesh, x0, y0, nx, ny, step)
            seen.append((sum(wet), sum(v is not None for v in flat)))
            for part in (1 << 18, 37):
                with mock.patch.object(mendnp, "CHUNK", part), mock.patch.object(mendnp, "_LAID", []):
                    z, covered = mendnp.heights(mesh, x0, y0, nx, ny, step)
                    again = mendnp.heights(mesh, x0, y0, nx, ny, step)  # (its squares kept from the first time)
                    self.same(mendnp.wet_bits(mesh, x0, y0, nx, ny, step), wet, (x0, part))
                self.same([v is not None for v in flat], covered.ravel().tolist(), (x0, part))
                self.assertTrue(same_bits([v for v in flat if v is not None], z[covered]), (x0, part))
                self.assertTrue(same_bits(z.ravel().tolist(), again[0]), (x0, part))
        self.assertTrue(all(wet and covered for wet, covered in seen[:3]), seen)  # water and ground on the first three
        self.assertEqual(seen[3], (0, 0))                                         # the last lies off the mesh
        self.same(mend.wet_bits(mesh, -2.5, -2.5, 50, 50, 5.0),
                         mendnp.wet_bits(mesh, -2.5, -2.5, 50, 50, 5.0))  # (asked through mend: on whole grids)

    def test_a_mesh_is_read_once_until_it_is_edited(self):
        """A real mesh's triangles are read once and kept (window after window asks for the same mesh's): an edit of
        its heights or its water shows at once. And a worker handed them with its own copy of the mesh (mend_map
        shares them out) answers as one that read its own."""
        from test_tms import make_tms
        from rusemod.tms import Tms, plateau
        tms = Tms(make_tms(gw=3, gh=3, n=11, zf=lambda x, y: 1000 + (x * 7 + y * 3) % 900, water_cell=(1, 1)))
        grid = (-100.0, -50.0, 80, 78, 40.0)

        def both(mesh):
            flat = [v for row in mend.heights(mesh, *grid) for v in row]
            with loops():
                wet = mend.wet_bits(mesh, *grid)
            z, covered = mendnp.heights(mesh, *grid)
            self.same([v is not None for v in flat], covered.ravel().tolist())
            self.assertTrue(same_bits([v for v in flat if v is not None], z[covered]))
            self.same(mendnp.wet_bits(mesh, *grid), wet)
            return flat, wet
        first = both(tms)
        self.assertIs(mendnp._corners(tms, 0), mendnp._corners(tms, 0))  # kept: the same arrays
        self.assertGreater(tms.edit_heights(plateau(1500.0, 1500.0, 200.0, 400.0, 2000.0)), 0)
        second = both(tms)
        self.assertNotEqual(first[0], second[0])
        self.assertGreater(tms.set_water(0, {i: 20000 for i in range(40)}), 0)
        third = both(tms)
        self.assertGreater(sum(third[1]), sum(second[1]))
        twin = Tms(tms.to_bytes())
        corners = mendnp.corners_to_share(tms, tms)
        mendnp.corners_shared(twin, twin, corners)
        self.assertIs(mendnp._corners(twin, 0), corners[2])
        self.assertIs(mendnp._corners(twin, 1), corners[1])
        self.same(both(twin), third)
        self.assertGreater(twin.edit_heights(plateau(500.0, 2500.0, 200.0, 400.0, 2500.0)), 0)  # handed, then edited
        self.assertNotEqual(both(twin)[0], third[0])
        tms.bounds[5] = 3176.7  # (not a 32-bit number: a worker's copy of the mesh would have another)
        self.assertIsNone(mendnp.corners_to_share(tms, tms))

    def test_the_highest_the_lowest_and_the_mean_round_each_square(self):
        import random
        from array import array
        rnd = random.Random(2)
        for _ in range(60):
            nx, ny = rnd.randint(1, 40), rnd.randint(1, 40)
            grid = [[rnd.choice([rnd.randint(0, 5), rnd.uniform(-9e3, 9e3)]) for _ in range(nx)] for _ in range(ny)]
            a = np.array(grid, dtype=np.float64)
            for r in (0, 1, 2, 7, 24, 60):
                for pick, highest in ((max, True), (min, False)):
                    self.same(mendnp.square(a, r, highest).tolist(), mend._filter2(grid, r, pick),
                                     (nx, ny, r, highest))
            bits = [[1 if rnd.random() < 0.1 else 0 for _ in range(nx)] for _ in range(ny)]
            r = rnd.randint(1, 4)
            self.same(mendnp.square(np.array(bits, dtype=np.uint8), r, True).tolist(),
                             mend._filter2(bits, r, max))
            vals = [rnd.choice([0.0, -0.0, rnd.uniform(0, 50), rnd.uniform(-50, 50)]) for _ in range(nx * ny)]
            for r in (0, 1, 3, 9, 45):
                want = mend._blur(array("d", vals), nx, ny, r)
                got = mendnp.blur(np.array(vals).reshape(ny, nx), r)
                self.same(want.tobytes(), got.tobytes(), (nx, ny, r))

    def trenches(self, depth, wet_x=-1.0):
        """A plain with a trench 20 m wide down x = 100 m and one 12 m wide along y = 90 m, `depth` deep, the ground
        a little uneven; water under the squares left of `wet_x`."""
        m = self.m

        def z(x, y):
            low = depth if abs(x - 100 * m) < 10 * m or abs(y - 90 * m) < 6 * m else 0.0
            return 10000.0 - low + 0.002 * x + 0.003 * y
        return WetMesh(81, 2.5 * m, z, wet_x)

    def test_the_hollows(self):
        """Gorge and Filled: the same squares, the same bounds and count; the rims' widening and none of it too."""
        m = self.m
        before, after, half = self.trenches(2600.0), self.trenches(0.0), self.trenches(1300.0)
        for box, kw in (((60 * m, 60 * m, 140 * m, 140 * m), {}),
                        ((75 * m, 70 * m, 131 * m, 118 * m), {"wider": 0.0, "reach": 30 * m}),
                        ((60 * m, 60 * m, 140 * m, 140 * m), {"step": 3.7 * m, "deep": 4 * m})):
            for new in (after, half):
                grids = mend.Filled(before, new, box, **kw)
                with loops():
                    pixels = mend.Filled(before, new, box, **kw)
                    want_box = pixels.box()
                self.same(grids.old.bits, pixels.old.bits, kw)
                self.same(grids.bits, pixels.bits, kw)
                self.assertEqual((grids.x0, grids.y0, grids.nx, grids.ny), (pixels.x0, pixels.y0, pixels.nx, pixels.ny))
                self.assertEqual(grids.box(), want_box, kw)
                self.assertIsInstance(grids.bits, bytearray)  # (a kept map holds plain values only)
                self.assertIsInstance(grids.old.bits, bytearray)
            self.assertGreater(mend.Filled(before, after, box, **kw).count(), 0)

    def test_riverbeds_only(self):
        """The stretches that don't reach the water taken off: the same squares, the same count, on made-up stretches
        of every shape (side by side only: corner to corner is two stretches)."""
        import random
        rnd = random.Random(5)
        for k in range(120):
            nx, ny = rnd.randint(1, 30), rnd.randint(1, 30)
            share = rnd.choice([0.05, 0.3, 0.55, 0.8])
            bits = bytearray(1 if rnd.random() < share else 0 for _ in range(nx * ny))
            wet = bytearray(1 if rnd.random() < rnd.choice([0.0, 0.01, 0.1]) else 0 for _ in range(nx * ny))
            grids, pixels = mend.Filled.__new__(mend.Filled), mend.Filled.__new__(mend.Filled)
            grids.nx, grids.ny, grids.bits = nx, ny, bytearray(bits)
            pixels.nx, pixels.ny, pixels.bits = nx, ny, bytearray(bits)
            gone = mend.riverbeds_only(grids, wet)
            with loops():
                want = mend.riverbeds_only(pixels, wet)
            self.same((gone, grids.bits), (want, pixels.bits), (k, nx, ny))

    def test_the_plan(self):
        """Plan: each square's number, its way across, its distance from the bank and the hollow's width there, on
        made-up hollows of every shape, smoothed and not."""
        import random
        rnd = random.Random(6)
        filled = 0
        for k in range(40):
            nx, ny = rnd.randint(3, 46), rnd.randint(3, 40)
            bad = bytearray(nx * ny)
            for _ in range(rnd.randint(1, 6)):  # hollows: bands, blobs and a square by the edge
                cx, cy, r = rnd.uniform(0, nx), rnd.uniform(0, ny), rnd.uniform(1, 9)
                band = rnd.random() < 0.4
                for j in range(ny):
                    for i in range(nx):
                        if (abs(i - cx) < r / 2) if band else ((i - cx) ** 2 + (j - cy) ** 2 < r * r):
                            bad[j * nx + i] = 1
            if k % 7 == 0:
                bad = bytearray(b"\1") * (nx * ny)  # no bank anywhere: nothing to fill from
            fill = bytearray(b if rnd.random() < 0.8 else 1 - b if rnd.random() < 0.1 else 0 for b in bad)
            for smooth in (0.0, 3.2, 1.0):
                grids = mend.Plan(nx, ny, fill, bad, 30.0, -70.0, 2.5, smooth)
                with loops():
                    pixels = mend.Plan(nx, ny, fill, bad, 30.0, -70.0, 2.5, smooth)
                for name in ("index", "ux", "uy", "d1", "width"):
                    self.same(getattr(grids, name).tobytes(), getattr(pixels, name).tobytes(),
                                     (k, nx, ny, smooth, name))
                    self.assertEqual(getattr(grids, name).typecode, getattr(pixels, name).typecode)
                self.assertEqual(grids.count(), pixels.count())
                filled += pixels.count()
        self.assertGreater(filled, 2000)

    def windows(self):
        """Two windows of a mended map side by side (mend._mend_window), the trenches reaching water."""
        m = self.m
        before, after = self.trenches(2600.0, wet_x=96 * m), self.trenches(0.0)
        return [mend._mend_window(before, after, wi, 0, core)
                for wi, core in ((0, (60 * m, 60 * m, 101 * m, 140 * m)), (1, (101 * m, 60 * m, 140 * m, 140 * m)))]

    def test_a_window(self):
        """A whole window of mend_map: its riverbeds, their plan, the dry squares let go; and what the Riverbeds
        answer from them."""
        m = self.m
        grids = self.windows()
        with loops():
            pixels = self.windows()
            beds_p = mend.Riverbeds(60 * m, 60 * m, 41 * m, {(w[0], w[1]): w[2] for w in pixels})
            near_p, box_p = beds_p._near_map(), beds_p.box()
        beds = mend.Riverbeds(60 * m, 60 * m, 41 * m, {(w[0], w[1]): w[2] for w in grids})
        self.same(beds._near_map(), near_p)
        self.assertEqual(beds.box(), box_p)
        for a, b in zip(grids, pixels):
            self.assertEqual((a[0], a[1], a[4]), (b[0], b[1], b[4]))
            self.same((a[2].bits, a[2].old.bits), (b[2].bits, b[2].old.bits))
            self.assertGreater(a[2].count(), 0)
            for name in ("index", "ux", "uy", "d1", "width"):
                self.same(getattr(a[3], name).tobytes(), getattr(b[3], name).tobytes(), name)

    def test_each_points_sources_and_its_value(self):
        """Plan.sources and Plan.fill_value for many points at once: the same sources in the same order, their
        weights and places the same to the last bit; the same values, with values of every size (where the order a
        point's sources are added in shows), sources landing in hollows or off the picture, and exact halves."""
        import math
        import random
        m = self.m
        rnd = random.Random(12)

        def big(x, y):
            return None if x < 80 * m else (int(x) % 251, int(y) * 10 ** 13 + int(x) * 977, int(x * y) % 3, int(x + y))

        def big_many(xs, ys):  # (the values, an array for each of the four; which points have one)
            got = [big(x, y) for x, y in zip(xs.tolist(), ys.tolist())]
            values = np.array([g or (0, 0, 0, 0) for g in got], dtype=np.int64).reshape(-1, 4)
            return [values[:, c] for c in range(4)], np.array([g is not None for g in got], dtype=bool)
        valued = 0
        for _wi, _wj, filled, plan, _d in self.windows():
            arrays = mendnp._plan_arrays(plan)
            s, nx = plan.step, plan.nx
            x0, y0, x1, y1 = filled.box()
            pts = [(rnd.uniform(x0, x1), rnd.uniform(y0, y1)) for _ in range(5000)]
            squares = [k for k in range(len(plan.index)) if plan.index[k] >= 0][::7]
            pts += [(plan.x0 + (k % nx) * s, plan.y0 + (k // nx) * s) for k in squares]              # their corners
            pts += [(plan.x0 + (k % nx + 0.5) * s, plan.y0 + (k // nx + 0.5) * s) for k in squares]  # their middles
            pts = [(x, y, plan.index[math.floor((y - plan.y0) / s) * nx + math.floor((x - plan.x0) / s)])
                   for x, y in pts]
            pts = [p for p in pts if p[2] >= 0]  # the points in a square to fill, each with its square's number
            xs, ys, idx = (np.array([p[k] for p in pts]) for k in range(3))
            bits = np.frombuffer(filled.old.bits, dtype=np.uint8)
            self.same(mendnp._hollow(filled.old, bits, xs, ys).tolist(),
                             [filled.hollow(x, y) for x, y, _k in pts])
            for ease, cross in ((mend.EASE, mend.CROSS), (0.0, 0.0), (2 * m, 1.5), (40 * m, 0.05)):
                got = mendnp._sources(plan, arrays, xs, ys, idx, ease, cross)
                for n, (x, y, _k) in enumerate(pts):
                    mine = [(float(wt[n]).hex(), (float(sx[n]).hex(), float(sy[n]).hex()),
                             (float(kx[n]).hex(), float(ky[n]).hex())) for wt, sx, sy, kx, ky, there in got if there[n]]
                    want = [(wt.hex(), (a.hex(), b.hex()), (c.hex(), d.hex()))
                            for wt, (a, b), (c, d) in plan.sources(x, y, ease, cross)]
                    self.assertEqual(mine, want, (x, y, ease, cross))
                values, have = mendnp._fill_values(plan, arrays, filled.old, xs, ys, idx, big_many, 4, ease, cross)
                for n, (x, y, _k) in enumerate(pts):
                    want = plan.fill_value(x, y, big, filled.hollow, ease, cross)
                    self.assertEqual(tuple(values[n].tolist()) if have[n] else None, want, (x, y, ease, cross))
                    valued += want is not None
        self.assertGreater(valued, 5000)
        # a straight hollow 20 squares wide: a point at its very middle takes half of each side, an exact half
        nx, ny = 70, 8
        bits = bytearray(1 if 30 <= k % nx < 50 else 0 for k in range(nx * ny))
        plan = mend.Plan(nx, ny, bits, bits, step=1.0)
        old = mend.Gorge.__new__(mend.Gorge)
        old.x0, old.y0, old.step, old.nx, old.ny, old.bits = 0.0, 0.0, 1.0, nx, ny, bits
        pts = [(30.0 + 0.5 * k, 0.5 + j) for k in range(40) for j in range(ny)]
        xs, ys = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
        idx = np.frombuffer(plan.index, dtype=np.intc)[ys.astype(int) * nx + xs.astype(int)]

        def side(x, y):
            return 7 if x < 30 else 10, int(x) % 2, 3  # (one side's first value odd, the other's even)

        def many(a, b):
            values = np.array([side(x, y) for x, y in zip(a.tolist(), b.tolist())]).reshape(-1, 3)
            return [values[:, c] for c in range(3)], np.ones(len(a), dtype=bool)
        values, have = mendnp._fill_values(plan, mendnp._plan_arrays(plan), old, xs, ys, idx, many, 3, 2.0, 0.5)
        want = [plan.fill_value(x, y, side, old.holds, 2.0, 0.5) for x, y in pts]
        self.same([tuple(v) if h else None for v, h in zip(values.tolist(), have.tolist())], want)
        self.assertEqual(want[20 * ny], (8, 1, 3))  # x = 40.0: 8.5 to the even 8; 0.5 * (1 + 1) from the odd columns

    def test_the_hollows_asked_for_many_points(self):
        """Gorge.holds for many points: on its squares' edges, a hair either side of them, and off its grid."""
        import random
        rnd = random.Random(13)
        old = mend.Gorge.__new__(mend.Gorge)
        old.x0, old.y0, old.step, old.nx, old.ny = -1300.0, 2600.5, 650.0, 23, 17
        old.bits = bytearray(1 if rnd.random() < 0.5 else 0 for _ in range(old.nx * old.ny))
        xs = [old.x0 + k * old.step for k in range(-2, old.nx + 3)]
        ys = [old.y0 + k * old.step for k in range(-2, old.ny + 3)]
        xs += [float(np.nextafter(x, -np.inf)) for x in xs] + [float(np.nextafter(x, np.inf)) for x in xs]
        ys += [float(np.nextafter(y, -np.inf)) for y in ys] + [float(np.nextafter(y, np.inf)) for y in ys]
        pts = [(x, y) for x in xs for y in ys]
        pts += [(rnd.uniform(-3000, 15000), rnd.uniform(0, 15000)) for _ in range(3000)]
        got = mendnp._hollow(old, np.frombuffer(old.bits, dtype=np.uint8), np.array([p[0] for p in pts]),
                             np.array([p[1] for p in pts]))
        self.same(got.tolist(), [old.holds(x, y) for x, y in pts])

    def noise_store(self, sides=(32, 64, 128)):
        """The made-up tile set with every block of every tile made up (so both kinds of DXT1 block): the overview,
        the two cells' tiles and their four quarters, `sides` pixels across."""
        import random
        from test_tmst import make_set
        from rusemod.tmst import Tmst, zipo_tile
        rnd = random.Random(8)
        plain = Tmst(*make_set())
        tiles = []
        for t in plain.tiles:
            side = sides[plain.depth - t.level]
            tiles.append(zipo_tile(bytes(rnd.randrange(256) for _ in range(side * side // 2)), side, side))
        return Tmst(*make_set(tiles))

    def test_a_tiles_pixels_and_the_maps_own_picture(self):
        """A tile's blocks to pixels as dxt.block_pixels gives them; the map's own picture at every level, on it and
        off it, as groundpaint._picture_sampler reads it."""
        import random
        from rusemod import dxt
        from rusemod.groundpaint import _blocks, _picture_sampler
        store = self.noise_store()
        bounds = (0.0, 0.0, 400 * self.m, 200 * self.m)
        for tile in store.tiles[:4]:
            blocks, w, h = _blocks(store, tile)
            pic = mendnp.tile_pixels(bytes(blocks), w // 4, h // 4)
            for kb in range(len(blocks) // 8):
                want = dxt.block_pixels(bytes(blocks[8 * kb:8 * kb + 8]))
                by, bx = divmod(kb, w // 4)
                got = [tuple(int(v) for v in pic[by * 4 + r, bx * 4 + c]) for r in range(4) for c in range(4)]
                self.assertEqual(got, want, (tile.index, kb))
        rnd = random.Random(9)
        pictures = mendnp.Pictures(store, bounds)
        for level in range(store.depth + 1):
            want_at = _picture_sampler(store, bounds, level)
            pts = [(rnd.uniform(-40 * self.m, 440 * self.m), rnd.uniform(-40 * self.m, 240 * self.m))
                   for _ in range(3000)]
            pts += [(k * 25 * self.m, j * 25 * self.m) for k in range(17) for j in range(9)]  # the tiles' own edges
            values, on = pictures.at(level, np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
            for k, (x, y) in enumerate(pts):
                want = want_at(x, y)
                self.assertEqual(want is not None, bool(on[k]), (level, x, y))
                if want is not None:
                    self.assertEqual(tuple(int(v[k]) for v in values), want, (level, x, y))

    def test_the_tiles(self):
        """Both windows' riverbeds mended in every tile of a tile set at every level: the same records, with the
        quick packer (the build's) and the full one; a part whose hollows are asked another way goes to the loops."""
        m = self.m
        bounds = (0.0, 0.0, 400 * m, 200 * m)
        done = self.windows()
        parts = [(plan, filled.hollow, filled.box()) for _wi, _wj, filled, plan, _d in done]
        store = self.noise_store()
        want = {}
        for quick in (True, False):
            grids = mend.mend_tiles_parts(store, bounds, parts, quick=quick)
            with loops():
                want[quick] = pixels = mend.mend_tiles_parts(store, bounds, parts, quick=quick)
            self.assertEqual(sorted(grids), sorted(pixels), quick)
            self.assertGreater(len(pixels), 4)
            for i in pixels:
                self.same(grids[i], pixels[i], (quick, i))
        self.assertNotEqual(want[True], want[False])
        asked = [(plan, lambda x, y, f=hollow: f(x, y), box) for plan, hollow, box in parts]
        self.same(mend.mend_tiles_parts(store, bounds, asked), want[True])
        self.assertIsNone(mendnp.mend_tile(mend, store, store.tiles[0], bounds, asked, {}, store, None, True))
        # the banks' ground read from another tile set than the one mended
        other = self.noise_store(sides=(64, 64, 64))
        grids = mend.mend_tiles_parts(store, bounds, parts, source=other)
        with loops():
            pixels = mend.mend_tiles_parts(store, bounds, parts, source=other)
        self.same(grids, pixels)

    def test_the_close_up_map(self):
        """The close-up map (one DXT5 picture, all four channels): the same record and note; its blocks to pixels and
        back as dxt reads and packs them."""
        import random
        from rusemod import dxt
        from rusemod.tmst import make_tgv, zipo_pack
        m = self.m
        rnd = random.Random(10)
        w, h = 96, 64
        blocks = bytes(rnd.randrange(256) for _ in range(w * h))
        for kb in range(0, w * h // 16, 5):  # (some blocks' alphas all one value, some the other way up)
            flat = bytes([rnd.randrange(256)]) * 2 if kb % 2 else bytes(sorted(blocks[16 * kb:16 * kb + 2]))
            blocks = blocks[:16 * kb] + flat + blocks[16 * kb + 2:]
        pic = mendnp._dxt5_pixels(blocks, w // 4, h // 4)
        rows = []
        for kb in range(w * h // 16):
            rgb, alpha = dxt.dxt5_block(blocks[16 * kb:16 * kb + 16])
            by, bx = divmod(kb, w // 4)
            got = [tuple(int(v) for v in pic[by * 4 + r, bx * 4 + c]) for r in range(4) for c in range(4)]
            self.assertEqual(got, [p + (a,) for p, a in zip(rgb, alpha)], kb)
            rows.append([v for p in got for v in p])
            self.assertEqual(mendnp._dxt5_blocks(np.array([rows[-1]], dtype=np.uint8)),
                             dxt.encode_dxt5_block(rgb, alpha), kb)
        raw = make_tgv(w, h, "DXT5", [zipo_pack(blocks)])
        done = self.windows()
        parts = [(plan, filled.hollow, filled.box()) for _wi, _wj, filled, plan, _d in done]
        bounds = (20 * m, 30 * m, 190 * m, 170 * m)
        grids = mend.mend_detail_parts(raw, bounds, parts)
        with loops():
            pixels = mend.mend_detail_parts(raw, bounds, parts)
            nothing = mend.mend_detail_parts(raw, (500 * m, 500 * m, 600 * m, 600 * m), parts)
        self.same(grids, pixels)
        self.assertIn("block(s) mended", pixels[1][0])
        self.same(mend.mend_detail_parts(raw, (500 * m, 500 * m, 600 * m, 600 * m), parts), nothing)
        self.assertEqual(nothing, (b"", []))
        other = make_tgv(w, h, "DXT5", [zipo_pack(bytes(rnd.randrange(256) for _ in range(w * h)))])
        grids = mend.mend_detail_parts(raw, bounds, parts, source=other)
        with loops():
            pixels = mend.mend_detail_parts(raw, bounds, parts, source=other)
        self.same(grids, pixels)

    def test_picking_the_windows(self):
        """mend._windows: the same windows, the old water looked for on whole grids."""
        m = self.m
        before = self.trenches(2600.0, wet_x=96 * m)
        before.bounds = (0.0, 0.0, 0.0, 200 * m, 200 * m, 0.0)
        box = (0.0, 0.0, 200 * m, 200 * m)
        from unittest import mock
        picked = 0
        with mock.patch.object(mend, "WINDOW", 50 * m):
            for areas in ([(100 * m, 100 * m, 40 * m)], [(20 * m, 180 * m, 15 * m), (150 * m, 30 * m, 30 * m)],
                          [(190 * m, 190 * m, 5 * m)]):
                grids = mend._windows(before, box, areas)
                with loops():
                    pixels = mend._windows(before, box, areas)
                self.assertEqual(grids, pixels, areas)
                picked += len(pixels)
        self.assertGreater(picked, 3)


if __name__ == "__main__":
    unittest.main()
