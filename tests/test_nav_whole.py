"""rusemod.navnp (numpy) against nav._Spots' own loops: the same rooms, byte for byte, and the same `top`, on made-up
zones of every kind the loops tell apart (whole-unit middles listed once for their kind, any middles, big zones, a
grid that cuts them off, more kinds than the loops keep lists for, rooms past a byte, depths right on a STEP)."""
import random
import unittest
from unittest import mock

from rusemod import nav

try:
    from rusemod import navnp
except ImportError:  # (numpy isn't here: the loops do all of it)
    navnp = None

STEP = nav.STEP


def spots(zones, least, box, whole: bool):
    with mock.patch.object(nav, "_WHOLE", [navnp if whole else None]):
        s = nav._Spots(zones, least, box)
    return (s.ni, s.nj, getattr(s, "i0", None), getattr(s, "j0", None), s.wide, s.top,
            bytes(s.room) if s.ni else b"")


@unittest.skipIf(navnp is None, "numpy isn't here: nav._Spots' own loops do all of it")
class SpotsOnWholeGrids(unittest.TestCase):
    def same(self, zones, least, box):
        self.assertEqual(spots(zones, least, box, True), spots(zones, least, box, False))

    def test_whole_unit_middles_listed_by_kind(self):
        rng = random.Random(1)
        zones = [(float(rng.randint(0, 200) * 160 + rng.choice((0, 37, 320))), float(rng.randint(0, 200) * 160),
                  float(rng.choice((1280, 1600, 2560, 4000, 9600)))) for _ in range(300)]
        self.same(zones, nav.MIN_RADIUS, (0.0, 0.0, 40000.0, 40000.0))

    def test_any_middles_and_big_zones(self):
        rng = random.Random(2)
        zones = [(rng.uniform(-5000, 60000), rng.uniform(-5000, 60000), rng.uniform(1000, 30000)) for _ in range(80)]
        zones += [(30000.0, 30000.0, 64 * 2 * STEP + 1.0), (12345.5, 777.25, 50000.0)]
        self.same(zones, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0))

    def test_a_grid_that_cuts_the_zones_off(self):
        rng = random.Random(3)
        zones = [(float(rng.randint(-50, 250) * 320), float(rng.randint(-50, 250) * 320),
                  float(rng.randint(4, 40) * 320)) for _ in range(150)]
        self.same(zones, nav.MIN_RADIUS, (6400.0, 3200.0, 41000.0, 52000.0))

    def test_more_kinds_than_are_kept(self):
        """Past 400,000 listed spots the loops work each new kind spot by spot; its `top` comes only from the grid."""
        rng = random.Random(4)
        zones = [(float(rng.randint(0, 639)), float(rng.randint(0, 639)), float(rng.randint(60, 128) * 320))
                 for _ in range(40)]
        zones = [(x + 20000.0 * (k % 5), y + 20000.0 * (k // 5), r) for k, (x, y, r) in enumerate(zones)]
        self.same(zones, nav.MIN_RADIUS, (10000.0, 10000.0, 90000.0, 150000.0))

    def test_rooms_past_a_byte(self):
        self.same([(200000.0, 200000.0, 300 * STEP), (150000.5, 260000.0, 90000.0)], nav.MIN_RADIUS,
                  (0.0, 0.0, 400000.0, 400000.0))

    def test_depths_right_on_a_step_or_on_least(self):
        """3-4-5 distances: spots whose depth is a whole number of STEPs, and spots exactly `least` deep."""
        zones = [(0.0, 0.0, 5 * 640.0 + 1280.0), (6400.0, 0.0, 3200.0 + 1280.0), (0.0, 9600.0, 4000.0),
                 (12800.0, 12800.0, 3 * 1280.0 + 1280.0), (640.0 * 7, 640.0 * 9, 640.0 * 5)]
        for least in (nav.MIN_RADIUS, 1920.0, 640.0):
            self.same(zones, least, (-20000.0, -20000.0, 30000.0, 30000.0))


if __name__ == "__main__":
    unittest.main()
