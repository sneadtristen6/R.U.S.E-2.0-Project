"""Cliff faces of rock scans (rusemod.cliffs, [[cliffs]] in scenery.toml) on made-up ground: only on steep ground, each
scan's front turned downhill and leaned as the slope, sunk, mixed, overlapping, the same every build; a scan's shape
read from its model; the area read from scenery.toml and kept apart from the placed objects."""
import math
import tempfile
import unittest
from pathlib import Path

from rusemod import cliffs
from rusemod.scenery import CliffArea, SceneryEditError, parse_cliffs

M = 260.0
TMP = "D:/RUSE-2.0/scratch/tmp"
WALL = cliffs.Shape(width=5.0, height=4.0, front=90.0, rise=0.0)     # a scan facing its own +y, upright
LEANING = cliffs.Shape(width=8.0, height=10.0, front=90.0, rise=30.0)


class Slope:
    """Ground rising toward +x at `degrees` (Tms.height_box's grid of square middles)."""

    def __init__(self, degrees):
        self.g = math.tan(math.radians(degrees))

    def height_box(self, x0, y0, x1, y1, step):
        cols, rows = max(1, math.ceil((x1 - x0) / step)), max(1, math.ceil((y1 - y0) / step))
        return [[self.g * (x0 + (c + 0.5) * step) for c in range(cols)] for _r in range(rows)]


def area(**kw):
    base = dict(types=("TypeWarrior/R2_Wall", "TypeWarrior/R2_Leaning"), x=100.0 * M, y=100.0 * M, radius=40.0 * M)
    base.update(kw)
    return CliffArea(**base)


SHAPES = {"TypeWarrior/R2_Wall": WALL, "TypeWarrior/R2_Leaning": LEANING}


class Laid(unittest.TestCase):
    def test_only_on_steep_ground(self):
        self.assertEqual(cliffs.cliff_layer([area()], Slope(0.0), SHAPES)[0], [])
        self.assertEqual(cliffs.cliff_layer([area(steep=30.0)], Slope(20.0), SHAPES)[0], [])
        self.assertTrue(cliffs.cliff_layer([area(steep=10.0)], Slope(20.0), SHAPES)[0])

    def test_front_downhill_and_leaned_as_the_slope(self):
        """Ground rising toward +x: downhill is 180 degrees. Each scan's front (its own 90 degrees) turned to it, give
        or take TURN_JITTER; tilted `lean` of the way from its own rise to the ground's (90 - slope), its top back into
        the hill (+x)."""
        laid, said = cliffs.cliff_layer([area(lean=0.5)], Slope(50.0), SHAPES)
        self.assertGreater(len(laid), 20)
        self.assertEqual(sum(said["types"].values()), len(laid))
        for o in laid:
            s = SHAPES[o.type]
            facing = (o.turn + s.front) % 360.0
            self.assertLessEqual(abs((facing - 180.0 + 180.0) % 360.0 - 180.0), cliffs.TURN_JITTER + 1e-6, o)
            tilt = math.radians(0.5 * ((90.0 - 50.0) - s.rise))
            self.assertAlmostEqual(o.up[2], math.cos(tilt), places=5)
            self.assertGreater(o.up[0], 0.0)    # (its top leans back into the hill, uphill)
            self.assertAlmostEqual(o.lift, -0.2 * s.height * o.size * M, delta=0.5)   # (its size rounded after)
            self.assertTrue(1.0 <= o.size <= 2.0)
            self.assertFalse(o.solid)
            self.assertLessEqual(math.hypot(o.x - 100.0 * M, o.y - 100.0 * M), 40.0 * M)

    def test_mixed_overlapping_and_the_same_every_build(self):
        a = area(spacing=0.6)
        laid, said = cliffs.cliff_layer([a], Slope(45.0), SHAPES)
        self.assertEqual(set(said["types"]), set(SHAPES))   # (both scans)
        again, _ = cliffs.cliff_layer([a], Slope(45.0), SHAPES)
        self.assertEqual(laid, again)
        # a point every 0.6 times the scans' mean width at their middle size: 0.6 * 1.5 * 6.5 m = 5.85 m
        step = 0.6 * 1.5 * (5.0 + 8.0) / 2
        expected = math.pi * 40.0 ** 2 / step ** 2
        self.assertTrue(0.8 * expected <= len(laid) <= 1.2 * expected, (len(laid), expected))
        other, _ = cliffs.cliff_layer([area(seed=3)], Slope(45.0), SHAPES)
        self.assertNotEqual([(o.x, o.y) for o in other], [(o.x, o.y) for o in laid])

    def test_a_type_with_no_shape_said(self):
        laid, said = cliffs.cliff_layer([area(types=("TypeWarrior/Rock_01", "TypeWarrior/R2_Wall"))], Slope(45.0),
                                        SHAPES)
        self.assertEqual(said["unknown"], ["TypeWarrior/Rock_01"])
        self.assertEqual({o.type for o in laid}, {"TypeWarrior/R2_Wall"})

    def test_shape_of_a_model(self):
        """A wall 4 m across (x) and 3 m up, its triangles facing +y: front 90 degrees, rise 0."""
        pos = [(0, 0, 0), (4, 0, 0), (4, 0, 3), (0, 0, 3)]
        s = cliffs.shape_of(pos, [(0, 2, 1), (0, 3, 2)])
        self.assertAlmostEqual(s.front, 90.0)
        self.assertAlmostEqual(s.rise, 0.0)
        self.assertAlmostEqual(s.width, 4.0)
        self.assertAlmostEqual(s.height, 3.0)


class Read(unittest.TestCase):
    def test_parsed(self):
        got, = parse_cliffs([{"types": ["TypeWarrior/R2_A"], "x": 1.0, "y": 2.0, "radius": 300.0, "size": [2, 3],
                              "steep": 40, "spacing": 0.5, "lean": 0.3, "sink": 0.1, "seed": 7}])
        self.assertEqual(got, CliffArea(("TypeWarrior/R2_A",), 1.0, 2.0, 300.0, (2.0, 3.0), 40.0, 0.5, 0.3, 0.1, 7))
        self.assertEqual(parse_cliffs([{"types": ["T"], "x": 0, "y": 0, "radius": 10}])[0].size, (1.0, 2.0))
        for row, why in (({"x": 0, "y": 0, "radius": 10}, "types"), ({"types": [], "x": 0, "y": 0, "radius": 10}, "types"),
                         ({"types": ["T"], "y": 0, "radius": 10}, "has no x"),
                         ({"types": ["T"], "x": 0, "y": 0, "radius": 0}, "radius"),
                         ({"types": ["T"], "x": 0, "y": 0, "radius": 10, "size": [3, 2]}, "size"),
                         ({"types": ["T"], "x": 0, "y": 0, "radius": 10, "lean": 2}, "lean"),
                         ({"types": ["T"], "x": 0, "y": 0, "radius": 10, "colour": 1}, "unknown key")):
            with self.assertRaisesRegex(SceneryEditError, why):
                parse_cliffs([row])

    def test_kept_apart_from_the_placed_objects(self):
        """load_mod: a scenery.toml's [[cliffs]] go to ModInfo.cliffs, its objects stay in .scenery."""
        from rusemod.build import load_mod
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            mod = Path(d, "m")
            (mod / "maps" / "M04_Cotentin").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "maps" / "M04_Cotentin" / "scenery.toml").write_text(
                '[[object]]\ntype = "TypeWarrior/Chene_01"\nx = 1.0\ny = 2.0\nturn = 0.0\nsize = 1.0\n\n'
                '[[cliffs]]\ntypes = ["TypeWarrior/R2_A"]\nx = 10.0\ny = 20.0\nradius = 500.0\n', encoding="utf-8")
            info, _ops = load_mod(mod)
        self.assertEqual([a.types for a in info.cliffs["M04_Cotentin"]], [("TypeWarrior/R2_A",)])
        self.assertEqual([o.type for o in info.scenery["M04_Cotentin"]], ["TypeWarrior/Chene_01"])


if __name__ == "__main__":
    unittest.main()
