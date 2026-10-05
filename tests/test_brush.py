"""Terrain brushes (rusemod.brush): their shapes, strokes, the terrain file and the local average. No game files."""
import tomllib
import unittest

from rusemod.brush import (
    BRUSHES, CRATER_RIM, HARD_EDGE, BrushError, Footprint, HeightGrid, Stroke, edge_weight, parse_strokes,
    shape_weight, strokes_toml,
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
        level = Stroke("level", 0, 0, 100, level=30.0)  # flat to the height where the drag started
        self.assertEqual([level.height_at(d, 0, z) for d in (0, 50)], [30.0, 30.0])
        self.assertTrue(z < level.height_at(75, 0, z) < 30.0)
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

    def test_the_ramp(self):
        z = 10.0
        ramp = Stroke("ramp", 0.0, 0.0, 100.0, level=20.0, x2=1000.0, y2=0.0, level2=120.0)
        self.assertEqual(ramp.height_at(0, 0, z), 20.0)                  # the start, at its level
        self.assertEqual(ramp.height_at(1000, 0, z), 120.0)              # the end, at its own
        self.assertEqual(ramp.height_at(250, 30, z), 45.0)               # a quarter along, inside the flat middle
        self.assertEqual(ramp.height_at(-30, 0, z), 20.0)                # beyond the start: the start's level
        self.assertEqual(ramp.height_at(1000, 100, z), z)                # the band's edge: untouched
        self.assertEqual(ramp.height_at(500, 200, z), z)                 # well beside it
        self.assertTrue(z < ramp.height_at(500, 75, z) < 70.0)           # the sides slope back to the old ground
        half = Stroke("ramp", 0.0, 0.0, 100.0, level=20.0, x2=1000.0, y2=0.0, level2=120.0, weight=0.5)
        self.assertEqual(half.height_at(0, 0, z), 15.0)
        self.assertEqual(ramp.along(500, 40), (0.5, 1600.0))
        self.assertEqual(ramp.box(), (-100.0, 1100.0, -100.0, 100.0))
        self.assertTrue(ramp.covers(500, 99))
        self.assertFalse(ramp.covers(500, 100) or ramp.covers(-100, 0))


class TerrainFile(unittest.TestCase):
    STROKES = [Stroke("hill", 983040.0, 983040.0, 60000.0, height=12000.0),
               Stroke("plateau", 1.5, 2.25, 10.0, level=-300.0, weight=0.75),
               Stroke("smooth", 3.0, 4.0, 5.0, weight=0.5),
               Stroke("crater", 0.1, 0.2, 0.3, height=7.0),
               Stroke("ramp", 5.0, 6.0, 7.0, level=8.0, weight=0.5, x2=9.0, y2=10.0, level2=11.0)]

    def test_written_and_read_back(self):
        text = strokes_toml(self.STROKES, "Made in the RUSE Studio.\nIt rewrites this file.")
        self.assertTrue(text.startswith("# Made in the RUSE Studio.\n# It rewrites this file.\n\n[[stroke]]\n"))
        self.assertEqual(parse_strokes(tomllib.loads(text)["stroke"]), self.STROKES)
        first = text.split("[[stroke]]")[1]
        self.assertIn("height = 12000.0", first)
        self.assertNotIn("level", first)                                 # only what the brush uses
        self.assertNotIn("weight", first)
        ramp = text.split("[[stroke]]")[5]
        self.assertIn("x2 = 9.0\ny2 = 10.0\nlevel = 8.0\nlevel2 = 11.0\nweight = 0.5\n", ramp)
        self.assertNotIn("height", ramp)
        self.assertEqual(strokes_toml([]), "\n")

    def test_every_brush_read_back(self):  # the Studio saved water strokes without their level once (0.7.0)
        every = [Stroke(name, 1.0, 2.0, 3.0, height=4.0, level=5.0, weight=0.5, x2=6.0, y2=7.0, level2=8.0,
                        colour="#808080", sx=9.0, sy=1.0)  # (a paint stroke's colour, a stamp's spot)
                 for name in BRUSHES]
        read = parse_strokes(tomllib.loads(strokes_toml(every))["stroke"])
        self.assertEqual([s.brush for s in read], list(BRUSHES))
        water = next(s for s in read if s.brush == "water")
        self.assertEqual(water.level, 5.0)

    def test_map_paint_clears_unless_told_not_to(self):
        paint = {"brush": "paint", "x": 1, "y": 2, "radius": 3, "colour": "#a07850"}
        stamp = {"brush": "stamp", "x": 1, "y": 2, "radius": 3, "sx": 5, "sy": 0}
        self.assertEqual([s.clear for s in parse_strokes([paint, stamp])], [True, True])   # on unless said
        kept = parse_strokes([dict(paint, clear=False), dict(stamp, clear=False)])
        self.assertEqual([s.clear for s in kept], [False, False])
        text = strokes_toml(kept + parse_strokes([paint]))
        self.assertEqual(text.count("clear = false"), 2)                                    # written only when off
        self.assertEqual(parse_strokes(tomllib.loads(text)["stroke"]), kept + parse_strokes([paint]))
        with self.assertRaisesRegex(BrushError, "stroke 1: clear must be true or false"):
            parse_strokes([dict(paint, clear="no")])
        with self.assertRaisesRegex(BrushError, "stroke 1: clear .* is for the paint and stamp brushes"):
            parse_strokes([{"brush": "hill", "x": 1, "y": 2, "radius": 3, "height": 4, "clear": True}])

    def test_a_thin_layer_of_water_units_go_under(self):
        """Water over the whole map (the owner's navy, 2026-10-05): `block = false` keeps its water out of the
        movement; written only when off, and only the water brush has it."""
        lake = {"brush": "water", "x": 1, "y": 2, "radius": 3, "level": 4}
        self.assertEqual([s.block for s in parse_strokes([lake, dict(lake, block=False)])], [True, False])
        thin = parse_strokes([dict(lake, block=False, shape="square")])
        text = strokes_toml(thin + parse_strokes([lake]))
        self.assertEqual(text.count("block = false"), 1)
        self.assertEqual(parse_strokes(tomllib.loads(text)["stroke"]), thin + parse_strokes([lake]))
        with self.assertRaisesRegex(BrushError, "stroke 1: block must be true or false"):
            parse_strokes([dict(lake, block="no")])
        with self.assertRaisesRegex(BrushError, "stroke 1: block .* is for the water brush"):
            parse_strokes([{"brush": "drain", "x": 1, "y": 2, "radius": 3, "block": False}])

    def test_brushes_and_their_values(self):
        self.assertEqual(set(BRUSHES), {"hill", "raise", "lower", "crater", "plateau", "flatten", "level", "smooth", "ramp",
                                        "water", "drain", "cover", "town", "uncover", "block", "block_infantry", "block_vehicles",
                                        "open", "open_infantry", "open_vehicles", "paint", "stamp"})
        self.assertEqual(parse_strokes([{"brush": "smooth", "x": 1, "y": 2, "radius": 3}])[0].weight, 0.5)
        self.assertEqual(parse_strokes([{"brush": "flatten", "x": 1, "y": 2, "radius": 3, "level": 4}])[0].weight, 1.0)

    def test_mistakes_name_the_file_and_the_stroke(self):
        good = {"brush": "hill", "x": 1, "y": 2, "radius": 3, "height": 4}
        for change, message in [
            ({"brush": "square"}, "stroke 2: brush 'square' isn't one of hill, raise"),
            ({"color": 1}, "stroke 2: unknown key 'color'"),
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
        with self.assertRaisesRegex(BrushError, "ramp brush needs x2, y2, level, level2"):
            parse_strokes([{"brush": "ramp", "x": 1, "y": 2, "radius": 3}])
        with self.assertRaisesRegex(BrushError, "stroke 1: the ramp's start and end are the same point"):
            parse_strokes([{"brush": "ramp", "x": 1, "y": 2, "radius": 3, "x2": 1, "y2": 2, "level": 0, "level2": 5}])
        with self.assertRaisesRegex(BrushError, "isn't a \\[\\[stroke\\]\\] table"):
            parse_strokes(["hill"])
        with self.assertRaisesRegex(BrushError, "must be a list"):
            parse_strokes({"brush": "hill"})


class BrushTypes(unittest.TestCase):
    """Every brush can be round, a square turned any way, or a line, with a soft or a hard edge (the owner,
    2026-10-03: "a couple of different Brush types. In every tool that has a brush")."""

    def test_a_turned_square(self):
        sq = Footprint("square", 0.0, 0.0, 10.0, 1.0, 1.0)     # turned 45 degrees: its corners on the axes
        self.assertTrue(sq.inside(13.0, 0.0))                   # toward a corner (14.1 out)
        self.assertFalse(sq.inside(9.0, 9.0))                    # past a side (12.7 out across it)
        self.assertAlmostEqual(sq.t2(7.0, 7.0), 0.98, 6)
        x0, x1, y0, y1 = sq.box()
        self.assertAlmostEqual(x1, 10.0 * 2 ** 0.5)
        self.assertAlmostEqual(y0, -10.0 * 2 ** 0.5)
        self.assertTrue(sq.meets(13.0, -1.0, 20.0, 1.0))         # a box at its corner
        self.assertFalse(sq.meets(9.0, 9.0, 12.0, 12.0))         # a box beyond its side, inside its bounding box
        plain = Footprint("square", 0.0, 0.0, 10.0)
        self.assertTrue(plain.inside(9.9, -9.9) and not plain.inside(10.0, 0.0))

    def test_a_line(self):
        ln = Footprint("line", 0.0, 0.0, 5.0, x2=100.0, y2=0.0)
        self.assertTrue(ln.inside(50.0, 4.9) and ln.inside(103.0, 0.0))  # beside it, past its round end
        self.assertFalse(ln.inside(50.0, 5.0) or ln.inside(106.0, 0.0))
        self.assertEqual(ln.box(), (-5.0, 105.0, -5.0, 5.0))
        self.assertTrue(ln.meets(40.0, 4.0, 60.0, 9.0))
        self.assertFalse(ln.meets(40.0, 6.0, 60.0, 9.0))
        self.assertTrue(ln.meets(-10.0, -10.0, 110.0, 10.0))       # a box round the whole line

    def test_circles_cover_the_footprint(self):
        for fp in (Footprint("square", 0.0, 0.0, 3000.0, 3.0, 1.0), Footprint("line", 0.0, 0.0, 800.0, x2=5000.0, y2=2000.0)):
            circles = fp.circles(1280.0)
            self.assertGreater(len(circles), 3)
            x0, x1, y0, y1 = fp.box()
            for k in range(40):
                for j in range(40):
                    px, py = x0 + (x1 - x0) * (k + 0.5) / 40, y0 + (y1 - y0) * (j + 0.5) / 40
                    if fp.t2(px, py) < 0.9:
                        self.assertTrue(any((px - cx) ** 2 + (py - cy) ** 2 <= r * r for cx, cy, r in circles),
                                        (fp.shape, px, py))
        self.assertEqual(Footprint("round", 1.0, 2.0, 3.0).circles(1280.0), [(1.0, 2.0, 3.0)])

    def test_a_hard_edge(self):
        self.assertEqual(edge_weight("hard", "soft", 0.5), 1.0)              # full well past the soft hump's middle
        self.assertEqual(edge_weight("hard", "soft", HARD_EDGE ** 2), 1.0)
        self.assertAlmostEqual(edge_weight("hard", "soft", 1.0 - 1e-12), 0.0, 6)
        self.assertEqual(edge_weight("hard", "crater", 0.0), shape_weight("crater", 0.0))  # a crater keeps its own
        self.assertEqual(edge_weight("soft", "flat", 0.7), shape_weight("flat", 0.7))
        hill = Stroke("hill", 0.0, 0.0, 100.0, height=50.0, edge="hard")
        self.assertEqual(hill.height_at(80.0, 0.0, 10.0), 60.0)              # full height at 80% of the way out

    def test_a_square_hill_and_a_line_ditch(self):
        sq = Stroke("plateau", 0.0, 0.0, 100.0, level=30.0, shape="square", dx=0.0, dy=1.0)
        self.assertEqual(sq.height_at(45.0, 45.0, 10.0), 30.0)                # the corner region of its flat middle
        self.assertTrue(sq.covers(99.0, 99.0) and not sq.covers(101.0, 0.0))
        ditch = Stroke("lower", 0.0, 0.0, 50.0, height=20.0, shape="line", x2=1000.0, y2=0.0)
        self.assertEqual(ditch.height_at(500.0, 0.0, 10.0), -10.0)            # all along its line
        self.assertEqual(ditch.height_at(500.0, 60.0, 10.0), 10.0)            # beside it
        self.assertEqual(ditch.box(), (-50.0, 1050.0, -50.0, 50.0))
        level = Stroke("level", 0.0, 0.0, 50.0, level=5.0, shape="line", x2=0.0, y2=500.0)
        self.assertEqual(level.kept(0.0, 250.0), 0.0)                          # flattened along it: none of the old shape

    def test_kept_made_once_gives_kept_to_the_bit(self):
        """Stroke.kept_function, for asking at many points, gives exactly what Stroke.kept gives, every brush, shape
        and edge, inside, on and past the footprint's edge."""
        import struct
        strokes = []
        for brush in ("hill", "lower", "crater", "plateau", "flatten", "level", "smooth", "ramp", "water", "cover"):
            for shape in ("round", "square", "line"):
                for edge in ("soft", "hard"):
                    if brush == "ramp" and shape == "square":
                        continue
                    extra = {"x2": 140.0, "y2": -60.0} if shape == "line" or brush == "ramp" else {}
                    if shape == "square":
                        extra.update(dx=0.6, dy=0.8)
                    strokes.append(Stroke(brush, 10.0, 20.0, 75.0, height=30.0, level=5.0, level2=9.0, weight=0.7,
                                          shape=shape, edge=edge, **extra))
        points = [(10.0 + dx, 20.0 + dy) for dx in (-90.0, -75.0, -40.3, 0.0, 12.5, 53.0, 74.999, 75.0, 75.001)
                  for dy in (-80.0, -1.0, 0.0, 33.3, 70.0, 75.0)] + [(1e7, -1e7), (85.0, 20.0)]
        for s in strokes:
            fast = s.kept_function()
            for x, y in points:
                with self.subTest(brush=s.brush, shape=s.shape, edge=s.edge, x=x, y=y):
                    self.assertEqual(struct.pack("<d", fast(x, y)), struct.pack("<d", s.kept(x, y)))

    def test_written_and_read_back(self):
        strokes = [Stroke("hill", 1.0, 2.0, 3.0, height=4.0, shape="square", dx=0.6, dy=0.8, edge="hard"),
                   Stroke("cover", 1.0, 2.0, 3.0, shape="line", x2=9.0, y2=10.0),
                   Stroke("block", 1.0, 2.0, 3.0, shape="square")]
        text = strokes_toml(strokes)
        self.assertIn('shape = "square"\ndx = 0.6\ndy = 0.8\nedge = "hard"', text)
        self.assertIn('shape = "line"\nx2 = 9.0\ny2 = 10.0', text)
        self.assertEqual(parse_strokes(tomllib.loads(text)["stroke"]), strokes)

    def test_mistakes(self):
        base = {"brush": "hill", "x": 1, "y": 2, "radius": 3, "height": 4}
        for change, message in [({"shape": "star"}, "shape must be one of round, square, line"),
                                ({"edge": "fuzzy"}, "edge must be one of soft, hard"),
                                ({"shape": "line"}, "a line needs x2 and y2"),
                                ({"shape": "line", "x2": 1, "y2": 2}, "the line's start and end are the same point"),
                                ({"dx": 1.0}, "dx and dy .* are for square strokes"),
                                ({"shape": "square", "dx": 0, "dy": 0}, "direction dx, dy can't be 0, 0")]:
            with self.subTest(change=change), self.assertRaisesRegex(BrushError, message):
                parse_strokes([dict(base, **change)])
        with self.assertRaisesRegex(BrushError, "a ramp runs along its line"):
            parse_strokes([{"brush": "ramp", "x": 1, "y": 2, "radius": 3, "x2": 5, "y2": 6, "level": 0, "level2": 5,
                            "shape": "square"}])


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
