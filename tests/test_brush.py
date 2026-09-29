"""Terrain brushes (rusemod.brush): their shapes, strokes, the terrain file and the local average. No game files."""
import tomllib
import unittest

from rusemod.brush import (
    BRUSHES, CRATER_RIM, BrushError, HeightGrid, Stroke, parse_strokes, shape_weight, strokes_toml,
)


class Shapes(unittest.TestCase):
    def test_full_at_the_centre_and_nothing_at_the_edge(self):
        for shape in ("soft", "flat"):
            self.assertEqual(shape_weight(shape, 0.0), 1.0)
            self.assertAlmostEqual(shape_weight(shape, 1.0 - 1e-12), 0.0, 6)
        self.assertEqual(shape_weight("crater", 0.0), -1.0)            # the bowl's full depth
        self.assertAlmostEqual(shape_weight("crater", 0.64), CRATER_RIM)  # t = 0.8: the top of the rim
        self.assertAlmostEqual(shape_weight("crater", 1.0 - 1e-12), 0.0, 6)

    def test_no_step_anywhere(self):
        for shape in ("soft", "flat", "crater"):
            prev = shape_weight(shape, 0.0)
            for k in range(1, 2001):
                w = shape_weight(shape, k / 2001)
                self.assertLess(abs(w - prev), 0.01, (shape, k))
                prev = w

    def test_the_flat_shape_is_flat_across_the_middle_half(self):
        self.assertEqual([shape_weight("flat", t * t) for t in (0.0, 0.3, 0.5)], [1.0, 1.0, 1.0])
        self.assertAlmostEqual(shape_weight("flat", 0.75 * 0.75), 0.5)  # halfway down the slope

    def test_an_unknown_shape_is_refused(self):
        with self.assertRaises(ValueError):
            shape_weight("square", 0.5)


class Strokes(unittest.TestCase):
    def test_each_brush(self):
        z = 10.0
        hill = Stroke("hill", 0.0, 0.0, 100.0, height=50.0)
        self.assertEqual(hill.height_at(0, 0, z), 60.0)
        self.assertEqual(hill.height_at(50, 0, z), z + 50.0 * (1 - 0.25) ** 2)
        self.assertEqual(hill.height_at(100, 0, z), z)                  # on the edge: untouched
        self.assertEqual(Stroke("raise", 0, 0, 100, height=50).height_at(50, 0, z), hill.height_at(50, 0, z))
        self.assertEqual(Stroke("lower", 0, 0, 100, height=4).height_at(0, 0, z), 6.0)
        crater = Stroke("crater", 0, 0, 100, height=20.0)
        self.assertEqual(crater.height_at(0, 0, z), -10.0)
        self.assertAlmostEqual(crater.height_at(80, 0, z), z + CRATER_RIM * 20.0)
        plateau = Stroke("plateau", 0, 0, 100, level=30.0)
        self.assertEqual([plateau.height_at(d, 0, z) for d in (0, 30, 50)], [30.0, 30.0, 30.0])
        self.assertTrue(z < plateau.height_at(75, 0, z) < 30.0)
        flatten = Stroke("flatten", 0, 0, 100, level=30.0, weight=0.5)
        self.assertEqual(flatten.height_at(0, 0, z), 20.0)
        smooth = Stroke("smooth", 0, 0, 100, weight=0.5)
        self.assertEqual(smooth.height_at(0, 0, z, lambda x, y: 20.0), 15.0)
        with self.assertRaises(ValueError):
            smooth.height_at(0, 0, z)                                   # it needs the local average
        self.assertEqual(smooth.height_at(500, 0, z), z)                 # outside, it doesn't need it

    def test_the_circle(self):
        s = Stroke("hill", 10.0, 20.0, 5.0, height=1.0)
        self.assertEqual(s.box(), (5.0, 15.0, 15.0, 25.0))
        self.assertTrue(s.covers(13.0, 23.0))
        self.assertFalse(s.covers(15.0, 20.0))                           # the edge itself is outside


class TerrainFile(unittest.TestCase):
    STROKES = [Stroke("hill", 983040.0, 983040.0, 60000.0, height=12000.0),
               Stroke("plateau", 1.5, 2.25, 10.0, level=-300.0, weight=0.75),
               Stroke("smooth", 3.0, 4.0, 5.0, weight=0.5),
               Stroke("crater", 0.1, 0.2, 0.3, height=7.0)]

    def test_written_and_read_back(self):
        text = strokes_toml(self.STROKES, "Made in the RUSE Studio.\nIt rewrites this file.")
        self.assertTrue(text.startswith("# Made in the RUSE Studio.\n# It rewrites this file.\n\n[[stroke]]\n"))
        self.assertEqual(parse_strokes(tomllib.loads(text)["stroke"]), self.STROKES)
        first = text.split("[[stroke]]")[1]
        self.assertIn("height = 12000.0", first)
        self.assertNotIn("level", first)                                 # only what the brush uses
        self.assertNotIn("weight", first)
        self.assertEqual(strokes_toml([]), "\n")

    def test_brushes_and_their_values(self):
        self.assertEqual(set(BRUSHES), {"hill", "raise", "lower", "crater", "plateau", "flatten", "smooth"})
        self.assertEqual(parse_strokes([{"brush": "smooth", "x": 1, "y": 2, "radius": 3}])[0].weight, 0.5)
        self.assertEqual(parse_strokes([{"brush": "flatten", "x": 1, "y": 2, "radius": 3, "level": 4}])[0].weight, 1.0)

    def test_mistakes_name_the_file_and_the_stroke(self):
        good = {"brush": "hill", "x": 1, "y": 2, "radius": 3, "height": 4}
        for change, message in [
            ({"brush": "square"}, "stroke 2: brush 'square' isn't one of hill, raise"),
            ({"colour": 1}, "stroke 2: unknown key 'colour'"),
            ({"height": None}, None),
            ({"radius": 0}, "stroke 2: radius must be above 0"),
            ({"x": "left"}, "stroke 2: x must be a number"),
            ({"x": True}, "stroke 2: x must be a number"),
            ({"y": float("nan")}, "stroke 2: y must be a finite number"),
            ({"weight": 1.5}, "stroke 2: weight must be between 0 and 1"),
        ]:
            item = dict(good, **{k: v for k, v in change.items() if v is not None})
            for k, v in change.items():
                if v is None:
                    del item[k]
            message = message or "stroke 2: the hill brush needs height"
            with self.subTest(change=change), self.assertRaisesRegex(BrushError, "^maps/X/terrain.toml: " + message):
                parse_strokes([good, item], "maps/X/terrain.toml")
        with self.assertRaisesRegex(BrushError, "plateau brush needs level"):
            parse_strokes([{"brush": "plateau", "x": 1, "y": 2, "radius": 3}])
        with self.assertRaisesRegex(BrushError, "isn't a \\[\\[stroke\\]\\] table"):
            parse_strokes(["hill"])
        with self.assertRaisesRegex(BrushError, "must be a list"):
            parse_strokes({"brush": "hill"})


class LocalAverage(unittest.TestCase):
    def test_gaps_are_filled_from_the_nearest_sample(self):
        g = HeightGrid([[None, 5.0, None, None],
                        [None, None, None, None],
                        [1.0, None, None, 3.0]], 0.0, 0.0, 4.0, 3.0)
        self.assertEqual(g.z, [[5.0, 5.0, 5.0, 5.0], [5.0, 5.0, 5.0, 5.0], [1.0, 1.0, 3.0, 3.0]])
        self.assertEqual(HeightGrid([[None, None]], 0.0, 0.0, 2.0, 1.0).z, [[0.0, 0.0]])  # nothing known at all
        self.assertEqual(g.point(0, 0), (0.5, 0.5))

    def test_a_sloping_ground_is_its_own_average(self):
        n = 40
        g = HeightGrid([[2.0 * c + 3.0 * r for c in range(n)] for r in range(n)], 0.0, 0.0, 40.0, 40.0)
        smooth = Stroke("smooth", 20.0, 20.0, 9.0, weight=1.0)
        at = g.average_for(smooth)
        for x, y in ((20.0, 20.0), (17.3, 22.9), (24.0, 16.5)):
            self.assertAlmostEqual(at(x, y), 2.0 * (x - 0.5) + 3.0 * (y - 0.5), 9)

    def test_smoothing_brings_a_spike_down_and_follows_every_stroke(self):
        n = 21
        rows = [[0.0] * n for _ in range(n)]
        rows[10][10] = 90.0
        g = HeightGrid(rows, 0.0, 0.0, 21.0, 21.0)
        smooth = Stroke("smooth", 10.5, 10.5, 6.0, weight=1.0)
        g.apply(smooth, g.average_for(smooth))
        self.assertLess(g.z[10][10], 30.0)
        self.assertGreater(g.z[10][11], 0.0)                              # the neighbours come up a little
        self.assertEqual(g.z[0][0], 0.0)                                  # outside the circle nothing moves
        before = g.z[10][10]
        g.apply(Stroke("hill", 10.5, 10.5, 3.0, height=100.0))           # the grid follows every stroke
        self.assertEqual(g.z[10][10], before + 100.0)

    def test_the_same_strokes_give_the_same_numbers(self):
        def run():
            g = HeightGrid([[float((r * 7 + c * 13) % 11) for c in range(30)] for r in range(30)], 0.0, 0.0, 3.0, 3.0)
            for s in (Stroke("smooth", 1.5, 1.5, 0.9, weight=0.7), Stroke("crater", 1.2, 1.7, 0.6, height=3.0),
                      Stroke("smooth", 1.4, 1.4, 1.3, weight=0.3)):
                g.apply(s, g.average_for(s) if s.brush == "smooth" else None)
            return g.z
        self.assertEqual(run(), run())


if __name__ == "__main__":
    unittest.main()
