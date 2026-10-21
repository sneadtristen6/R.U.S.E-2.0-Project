"""A real place made a map (rusemod.realplace): the square's metres and degrees, the elevation tiles read, the
OpenStreetMap areas filled and laid by layer, the bare land cut into fields, the sea's floor and a river's bed, and the
files and strokes the Studio writes: a made-up place of 600 m, half sea, with a wood, a field with a pond-shaped hole
and a river."""
import math
import struct
import tomllib
import unittest

try:
    import numpy as np
except ImportError:
    np = None

from rusemod import realplace as rp

LAT, LON, ZOOM = 48.6, -1.5, 13
SIDE = 600.0


def tile_png(tx, ty, height_of):
    """A Terrarium tile at ZOOM: each pixel `height_of(x metres east of LON)` metres."""
    from rusemod.dxt import png_bytes
    frame = rp.Frame(LAT, LON, 0.0, 0.0, 1.0)
    lon = (tx + (np.arange(256) + 0.5) / 256.0) / 2 ** ZOOM * 360.0 - 180.0
    x, _y = frame.metres(LAT, lon)
    v = np.round((np.vectorize(height_of)(x) + 32768.0) * 256.0).astype(np.int64)   # 1/256 m steps
    row = np.stack([v // 65536, v // 256 % 256, v % 256], axis=1).astype(np.uint8)
    return png_bytes(np.tile(row, (256, 1)).tobytes(), 256, 256)


def square(frame, x0, y0, x1, y1):
    """A closed way's points round a square of metres (the Overpass answer's geometry)."""
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return [dict(zip(("lon", "lat"), frame.lonlat(x, y))) for x, y in pts]


def place():
    """The made-up place: the sea west of the reference (0 m), land at 20 m east of it."""
    frame = rp.Frame(LAT, LON, -SIDE / 2, -SIDE / 2, SIDE)
    tiles = {t: tile_png(*t, lambda x: 0.0 if x < 0 else 20.0) for t in rp.tiles_needed(frame, ZOOM)}
    river = [dict(zip(("lon", "lat"), frame.lonlat(x, 200.0))) for x in (40.0, 160.0, 280.0)]
    doc = {"elements": [
        {"type": "way", "tags": {"landuse": "forest"}, "geometry": square(frame, 50.0, -200.0, 200.0, -50.0)},
        {"type": "relation", "tags": {"type": "multipolygon", "landuse": "farmland"}, "members": [
            {"type": "way", "role": "outer", "geometry": square(frame, 40.0, 20.0, 240.0, 120.0)},
            {"type": "way", "role": "inner", "geometry": square(frame, 100.0, 50.0, 140.0, 90.0)}]},
        {"type": "way", "tags": {"waterway": "river"}, "geometry": river},
        {"type": "way", "tags": {"highway": "track"}, "geometry": square(frame, 10.0, 10.0, 20.0, 20.0)[:2]}]}
    return frame, tiles, doc


@unittest.skipIf(np is None, "numpy isn't installed")
class Frame(unittest.TestCase):
    def test_metres_and_degrees_both_ways(self):
        f = rp.Frame(LAT, LON, -100.0, -50.0, 400.0)
        x, y = f.metres(*reversed(f.lonlat(123.0, -45.0)))
        self.assertAlmostEqual(x, 123.0, places=6)
        self.assertAlmostEqual(y, -45.0, places=6)
        self.assertEqual(f.world(-100.0, -50.0), (0.0, 0.0))
        self.assertEqual(f.world(300.0, 350.0), (400.0 * rp.M, 400.0 * rp.M))
        s, w, n, e = f.bbox()
        self.assertTrue(s < LAT < n and w < LON < e)   # (south is down: y grows south)

    def test_a_terrarium_pixel(self):
        from rusemod.dxt import png_bytes
        self.assertEqual(rp.terrarium(png_bytes(bytes((128, 10, 128)), 1, 1))[0, 0], 10.5)

    def test_a_missing_tile_is_said(self):
        frame, tiles, _doc = place()
        if len(tiles) < 2:
            self.skipTest("the square lies in one tile")
        tiles.pop(next(iter(tiles)))
        with self.assertRaisesRegex(rp.PlaceError, "missing|don't cover"):
            rp.ground_heights(frame, tiles, ZOOM)


@unittest.skipIf(np is None, "numpy isn't installed")
class Shapes(unittest.TestCase):
    def test_fill_keeps_a_hole_out(self):
        outer = np.array([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)])
        inner = np.array([(4.0, 4.0), (6.0, 4.0), (6.0, 6.0), (4.0, 6.0), (4.0, 4.0)])
        mask, r0, c0 = rp.fill([outer, inner], 0.0, 0.0, 1.0, 20, 20)
        self.assertEqual((r0, c0, mask.shape), (0, 0, (10, 10)))
        self.assertEqual(int(mask.sum()), 100 - 4)
        self.assertFalse(mask[4:6, 4:6].any())
        self.assertIsNone(rp.fill([outer + 50.0], 0.0, 0.0, 1.0, 20, 20))

    def test_a_long_shape_runs_its_long_way(self):
        def box(w, h):
            return [np.array([(0.0, 0.0), (w, 0.0), (w, h), (0.0, h), (0.0, 0.0)])]
        self.assertAlmostEqual(rp.stretch_way(box(100.0, 10.0)) % 180.0, 0.0, places=6)
        self.assertAlmostEqual(rp.stretch_way(box(10.0, 100.0)), 90.0, places=6)

    def test_pick_is_the_same_every_time(self):
        got = [rp.pick(("a", "b", "c"), k) for k in range(60)]
        self.assertEqual(got, [rp.pick(("a", "b", "c"), k) for k in range(60)])
        self.assertEqual(set(got), {"a", "b", "c"})

    def test_a_relations_ways_joined_into_a_ring(self):
        a = np.array([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])
        b = np.array([(0.0, 0.0), (0.0, 1.0), (1.0, 1.0)])   # the second half, drawn the other way
        ring, = rp._joined([a, b])
        self.assertEqual(len(ring), 5)
        self.assertTrue(np.allclose(ring[0], ring[-1]))


@unittest.skipIf(np is None, "numpy isn't installed")
class MadePlace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame, tiles, doc = place()
        cls.made = rp.make_place(cls.frame, tiles, ZOOM, doc)

    def cells(self, x0, x1, y0, y1):
        """The area picture's numbers over a box of metres."""
        f = self.frame
        return self.made.areas[int((y0 - f.y0) / rp.AREA_CELL):int((y1 - f.y0) / rp.AREA_CELL),
                               int((x0 - f.x0) / rp.AREA_CELL):int((x1 - f.x0) / rp.AREA_CELL)]

    def plan_at(self, x, y):
        number = int(self.cells(x, x + rp.AREA_CELL, y, y + rp.AREA_CELL)[0, 0])
        return next(p for p in self.made.plans if p.number == number)

    def test_the_sea_west_and_its_floor(self):
        h, n = self.made.heights, self.made.heights.shape[0]
        self.assertTrue(self.made.sea[:, :140].all())
        self.assertFalse(self.made.sea[:, 160:].any())
        self.assertLess(h[:, :n // 2 - 20].max(), rp.SEA)
        self.assertAlmostEqual(float(h[:, :8].min()), rp.SEA_FLOOR)   # away from the shore
        self.assertEqual(self.plan_at(-200.0, 0.0).kind, "sea")

    def test_each_area_in_its_swatch(self):
        wood = self.plan_at(120.0, -120.0)
        self.assertEqual((wood.kind, wood.swatch, wood.turn), ("wood", "forest_floor", 0.0))
        self.assertTrue((self.cells(52.0, 198.0, -198.0, -52.0) == wood.number).all())
        self.assertEqual(wood.cells, 75 * 75)
        field = self.plan_at(60.0, 30.0)
        self.assertEqual(field.kind, "field")
        self.assertIn(field.swatch, rp.SWATCHES["field"])
        self.assertAlmostEqual(field.turn % 180.0, 0.0, places=6)   # its rows along its long way (east-west)
        self.assertFalse((self.cells(102.0, 138.0, 52.0, 88.0) == field.number).any())   # its hole is the land's

    def test_the_bare_land_cut_into_fields(self):
        land = [p for p in self.made.plans if p.kind == "land"]
        self.assertGreater(len(land), 1)
        for p in land:
            self.assertIn(p.swatch, rp.SWATCHES["land"])
            self.assertEqual(p.turn != 0.0, p.swatch in rp.ROWS)
        self.assertEqual(sorted(p.number for p in self.made.plans), sorted({p.number for p in self.made.plans}))
        seen = set(np.unique(self.made.areas).tolist())
        self.assertEqual(seen, {p.number for p in self.made.plans})   # every area laid shows, every cell has one

    def test_the_rivers_bed_cut_and_its_water(self):
        self.assertEqual([ln.kind for ln in self.made.rivers], ["river"])
        f, h = self.frame, self.made.heights
        j, i = int((200.0 - f.y0) / rp.HEIGHT_STEP), int((160.0 - f.x0) / rp.HEIGHT_STEP)
        self.assertAlmostEqual(float(h[j, i]), 20.0 - rp.RIVER_DEPTH, places=1)
        self.assertAlmostEqual(float(h[j - 10, i]), 20.0)   # 50 m off: the bank untouched
        self.assertEqual(self.plan_at(160.0, 200.0).kind, "water")

    def test_the_strokes(self):
        from rusemod.brush import parse_strokes, strokes_toml
        base = 1000.0
        st = rp.strokes(self.made, "test", base)
        lo, hi = float(self.made.heights.min()), float(self.made.heights.max())
        r = st[0]
        self.assertEqual((r.brush, r.shape, r.relief, r.x, r.y, r.radius), ("relief", "square", "test", SIDE / 2 * rp.M,
                                                                           SIDE / 2 * rp.M, SIDE / 2 * rp.M))
        self.assertEqual((r.level, r.level2), (base, base + (hi - lo) * rp.M))
        sea = st[1]
        self.assertEqual((sea.brush, sea.shape, sea.level), ("water", "square", base + (rp.SEA - lo) * rp.M))
        river = [s for s in st[2:] if s.brush == "water"]
        self.assertEqual(len(river), 8)   # 240 m of it inside the square, a stroke every WATER_STEP
        self.assertAlmostEqual(river[0].level, base + (20.0 - rp.RIVER_DROP - lo) * rp.M)
        laid = [s for s in st if s.brush == "texture"]
        self.assertEqual(len(laid), len(self.made.plans))
        by = {p.number: p for p in self.made.plans}
        for s in laid:
            p = by[int(s.within.split(":")[1])]
            self.assertEqual((s.texture, s.turn, s.clear, s.within), (f"swatch:dday:{p.swatch}", p.turn, False,
                                                                     f"test:{p.number}"))
        again = parse_strokes(tomllib.loads(strokes_toml(st))["stroke"])
        self.assertEqual([s.within for s in again], [s.within for s in st])

    def test_the_files(self):
        from rusemod.png import read_grey16
        from rusemod.relief import read_areas
        data, lo, hi = rp.heightmap(self.made)
        w, h, samples = read_grey16(data)
        q = np.frombuffer(samples, dtype=">u2").reshape(h, w)[::-1]   # (rows from the south)
        back = lo + q / 65535.0 * (hi - lo)
        self.assertLess(float(np.abs(back - self.made.heights).max()), (hi - lo) / 65535.0)
        self.assertTrue((read_areas(rp.area_picture(self.made))[::-1] == self.made.areas).all())
        colours = {"forest_floor": (1, 2, 3)}
        w, h, rgb = rp.ground_picture(self.made, lambda sw: colours.get(sw, (9, 9, 9)))
        self.assertEqual((w, h), (int(SIDE / rp.PICTURE_CELL),) * 2)
        f = self.frame
        col, row = int((120.0 - f.x0) / rp.PICTURE_CELL), h - 1 - int((-120.0 - f.y0) / rp.PICTURE_CELL)
        self.assertEqual(rgb[(row * w + col) * 3:(row * w + col) * 3 + 3], bytes((1, 2, 3)))
        credit = tomllib.loads(rp.credit_toml(self.made, "Test place"))
        self.assertEqual(credit["place"], "Test place")
        self.assertIn("OpenStreetMap", credit["osm"])
        self.assertTrue(credit["south"] < LAT < credit["north"])
        self.assertEqual(struct.unpack(">I", data[16:20])[0], int(math.ceil(SIDE / rp.HEIGHT_STEP)))   # IHDR width


if __name__ == "__main__":
    unittest.main()
