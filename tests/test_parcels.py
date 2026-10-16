"""rusemod.parcels: a dab's parcel, the ground the map's own paint and borders give the field under it (made-up
pictures), and scenery.expand_field_parcel on it (test_scenery's made-up map). Skipped without numpy: the apps carry
it, and without it the field brush keeps to the fields' squares (test_scenery)."""
import math
import unittest

try:
    import numpy as np
    from rusemod import parcels
except ImportError:
    np = parcels = None

from rusemod import scenery
import test_scenery as ts
from test_scenery import FB_DESCS

M = 260.0
YELLOW, GREEN, DARK = (166, 133, 41), (80, 110, 30), (128, 100, 30)


def painter(fn):
    """picture(xs, ys) -> (colours, there) from fn(x, y) -> rgb."""
    def picture(xs, ys):
        xs, ys = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
        out = np.array([fn(x, y) for x, y in zip(xs.ravel(), ys.ravel())], dtype=float).reshape(xs.shape + (3,))
        return out, np.ones(xs.shape, dtype=bool)
    return picture


def under_disc(cx, cy, r):
    return lambda xs, ys: (np.asarray(xs) - cx) ** 2 + (np.asarray(ys) - cy) ** 2 < r * r


@unittest.skipIf(np is None, "numpy isn't here: rusemod.parcels needs it")
class Find(unittest.TestCase):
    """find_parcel on a row of squares 0..20,000 along x, 2,048 to each side across (a field of 9 x 1 pieces)."""
    SQUARES = [(float(x), 0.0, 2048.0, 0.0) for x in range(0, 20001, 2500)]

    def parcel(self, fn, walls=(), at=(10000.0, 0.0)):
        return parcels.find_parcel(under_disc(at[0], at[1], 3000.0), self.SQUARES, painter(fn), list(walls))

    def test_the_paint_s_edge_stops_it(self):
        """Yellow on the left of x = 12,000, green on the right (another field): the parcel is the yellow ground,
        all of it under the squares there, none of the green."""
        p = self.parcel(lambda x, y: YELLOW if x < 12000 else GREEN, at=(6000.0, 0.0))
        self.assertTrue(p.holds(1000.0, 0.0) and p.holds(11000.0, 1500.0) and p.holds(-1500.0, -1500.0))
        self.assertFalse(p.holds(13000.0, 0.0) or p.holds(19000.0, 0.0))

    def test_a_soft_darker_part_is_the_field_s(self):
        """A darker part painted soft-edged (Eugen's harvested ground, blended over 8 m) stays in."""
        def fn(x, y):
            t = min(1.0, max(0.0, (x - 12000.0) / (8 * M)))
            return tuple(a + (b - a) * t for a, b in zip(YELLOW, DARK))
        p = self.parcel(fn, at=(4000.0, 0.0))
        self.assertTrue(p.holds(19000.0, 0.0) and p.holds(15000.0, 1000.0))

    def test_a_wall_stops_it_and_a_hole_is_filled(self):
        """A border strip across the field at x = 14,000 stops it; a darker patch inside, sharp-edged, holding no
        wall, is a hole: the field's."""
        wall = (14000.0, 0.0, 3000.0, 0.6 * M, 0.0, 1.0)   # along y, across the field
        p = self.parcel(lambda x, y: DARK if math.hypot(x - 6000.0, y) < 800.0 else YELLOW, [wall], at=(3000.0, 0.0))
        self.assertTrue(p.holds(6000.0, 0.0))                         # the patch
        self.assertTrue(p.holds(12500.0, 0.0))
        self.assertFalse(p.holds(16000.0, 0.0) or p.holds(19000.0, 0.0))

    def test_two_fields_through_a_gap_part(self):
        """Two yellow fields side by side, a fence between them with a 3 m gap at one end: the dab's field alone."""
        fence = (10000.0, 600.0, 2100.0, 0.3 * M, 0.0, 1.0)   # x = 10,000, from y -1,500 up to 2,700 (the gap below)
        p = self.parcel(lambda x, y: YELLOW, [fence], at=(3000.0, 0.0))
        self.assertTrue(p.holds(8000.0, 0.0))
        self.assertFalse(p.holds(15000.0, 0.0) or p.holds(19000.0, 0.0))

    def test_subtract_and_clip(self):
        p = self.parcel(lambda x, y: YELLOW)
        q = self.parcel(lambda x, y: YELLOW)
        self.assertTrue(p.holds(5000.0, 0.0))
        parcels.subtract(p, q)
        self.assertFalse(p.mask.any())
        x0, y0, cell, w, h, bits = q.clip()
        self.assertEqual((len(bits), cell), (w * h, parcels.CELL))
        self.assertEqual(sum(bits), int(q.mask.sum()))


@unittest.skipIf(np is None, "numpy isn't here: rusemod.parcels needs it")
class Brush(unittest.TestCase):
    """expand_field_parcel on test_scenery's field A (ploughed rows facing 30 round (20000, 20000)) with a parcel
    covering the half of A on the +x side of x = 20,000."""

    def setUp(self):
        self.fb = ts.FieldBrush
        self.data = self.fb.map_data(self.fb(), farm=True)
        self.sc = scenery.Scenery(self.data)
        x0, y0, cell = 4000.0, 4000.0, 160.0
        w = h = int(32000 / cell)
        X = x0 + (np.arange(w) + 0.5) * cell
        mask = np.zeros((h, w), dtype=bool)
        mask[:, X >= 20000.0] = True
        self.P = parcels.Parcel(x0, y0, cell, w, h, mask, parcels._inside(mask, cell))
        self.dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)

    def look(self, **kw):
        return dict(self.fb.LOOK, masks=[{16: 3, 21: 1}], **kw)

    def test_only_the_parcel_changes(self):
        erases, objects, copies, stamps, notes = scenery.expand_field_parcel(self.dab, self.look(), self.sc, self.P)
        rows = [o for o in objects if o.type == "TypeWarrior/Paille"]
        self.assertTrue(rows)
        self.assertTrue(all(o.x >= 20000.0 - 1 for o in rows))          # its pieces alone, laid as the look's kind
        self.assertEqual(len(stamps), 1)
        self.assertEqual(stamps[0].clip, self.P.clip())                  # its paint clipped to it
        crop_erase = next(e for e in erases if e.mask is not None)
        self.assertTrue(crop_erase.mask(25000.0, 20000.0) and not crop_erase.mask(15000.0, 20000.0))
        laid, _n = scenery.copy_objects(self.data, copies, FB_DESCS)
        crops = [o for o in laid if o.type == "TypeWarrior/Champs_Bles"]
        self.assertTrue(crops and all(self.P.holds(o.x, o.y) for o in crops))
        self.assertIn("its field's ground", notes[0])

    def test_its_pieces_take_the_source_s_ring_flags_in_its_shares(self):
        _e, objects, _c, _s, _n = scenery.expand_field_parcel(self.dab, self.look(), self.sc, self.P)
        rows = [o for o in objects if o.type == "TypeWarrior/Paille"]
        share = sum(1 for o in rows if o.levels == 21) / len(rows)
        self.assertAlmostEqual(share, 0.25, delta=0.5 / len(rows) + 1e-9)
        self.assertEqual({o.levels for o in rows}, {16, 21})

    def test_a_look_without_hay_takes_the_hay_on_its_ground_off(self):
        erases, _o, _c, _s, notes = scenery.expand_field_parcel(self.dab, self.look(hay=False), self.sc, self.P)
        gone = [(e.types, round(e.x)) for e in erases if e.types in (("TypeWarrior/Foin_3",),)]
        self.assertEqual(gone, [(("TypeWarrior/Foin_3",), 24000)])   # HAY_AT lies in the parcel (x > 20,000)


if __name__ == "__main__":
    unittest.main()
