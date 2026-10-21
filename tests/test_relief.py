"""Ground made whole from a heightmap (rusemod.relief, brush = "relief"): the stroke read and written, the heightmap's
height under any point (bilinear, turned with the square), the ground going toward it by the stroke's fall-off, a
16-bit heightmap read with every step, and its picture laid on a made-up tile set at every level, under the edge's
fall-off."""
import math
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from test_groundpaint import BOUNDS, GREEN, near, pixel, store
from rusemod.brush import BrushError, Stroke, parse_strokes, strokes_toml
from rusemod.relief import Picture, ReliefError, height_of, lay_pictures, place, read_grid
from rusemod.tmst import Tmst

try:
    import numpy as _np  # noqa: F401
except ImportError:
    _np = None

TMP = None   # the system's temp folder (TEMP)


def grey16_png(w, h, values):
    """A 16-bit greyscale PNG of `values` (rows top to bottom)."""
    raw = b"".join(b"\x00" + b"".join(struct.pack(">H", v) for v in values[r * w:(r + 1) * w]) for r in range(h))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 16, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def relief(grid, **kw):
    base = dict(brush="relief", x=500.0, y=500.0, radius=500.0, level=0.0, level2=65535.0, shape="square",
                edge="hard", relief="test", grid=grid)
    base.update(kw)
    return Stroke(**base)


class Read(unittest.TestCase):
    def test_parsed_and_written_back(self):
        got, = parse_strokes([{"brush": "relief", "x": 10.0, "y": 20.0, "radius": 300.0, "shape": "square",
                               "relief": "valley_1", "level": 1000.0, "level2": 80000.0, "edge": "hard"}])
        self.assertEqual((got.relief, got.level, got.level2, got.grid), ("valley_1", 1000.0, 80000.0, ()))
        again, = parse_strokes([dict(__import__("tomllib").loads(strokes_toml([got]))["stroke"][0])])
        self.assertEqual(again, got)

    def test_mistakes_said(self):
        good = {"brush": "relief", "x": 0.0, "y": 0.0, "radius": 10.0, "shape": "square", "relief": "a",
                "level": 0.0, "level2": 1.0}
        for change, why in (({"shape": "round"}, "square"), ({"relief": "A b.png"}, "relief must"),
                            ({"grid": [1]}, "grid"), ({"relief": None}, "relief must")):
            row = dict(good, **change)
            with self.assertRaisesRegex(BrushError, why):
                parse_strokes([row])
        with self.assertRaisesRegex(BrushError, "needs"):
            parse_strokes([{k: v for k, v in good.items() if k != "level2"}])
        with self.assertRaisesRegex(BrushError, "relief brush"):
            parse_strokes([{"brush": "hill", "x": 0.0, "y": 0.0, "radius": 10.0, "height": 5.0, "relief": "a"}])


class Heights(unittest.TestCase):
    GRID = (2, 2, struct.pack(">4H", 0, 65535, 65535, 0))   # top row 0, 65535; bottom row 65535, 0

    def test_samples_at_their_middles_and_between(self):
        s = relief(self.GRID)
        # a 2 x 2 heightmap over 1,000 x 1,000: sample middles at 250 and 750; the top row on the high y side
        self.assertAlmostEqual(height_of(s, 250.0, 750.0), 0.0)
        self.assertAlmostEqual(height_of(s, 750.0, 750.0), 65535.0)
        self.assertAlmostEqual(height_of(s, 250.0, 250.0), 65535.0)
        self.assertAlmostEqual(height_of(s, 500.0, 500.0), 65535.0 / 2)
        self.assertAlmostEqual(height_of(s, 0.0, 1000.0), 0.0)        # held at the edge's sample past it

    def test_turned_with_its_square(self):
        """Turned a quarter (dx, dy = 0, 1): its columns run along +y, its top row on the -x side."""
        s = relief(self.GRID, dx=0.0, dy=1.0)
        self.assertEqual(place(s, 500.0, 0.0), (0.0, 0.5))
        self.assertAlmostEqual(height_of(s, 250.0, 250.0), 0.0)        # top-left: the low x, low y corner
        self.assertAlmostEqual(height_of(s, 250.0, 750.0), 65535.0)    # top-right

    def test_the_ground_goes_toward_it(self):
        s = relief(self.GRID, level=100.0, level2=200.0, weight=0.5)
        self.assertAlmostEqual(s.height_at(750.0, 750.0, 0.0), 100.0)  # half way to 200, its hard edge full there
        self.assertEqual(s.height_at(2000.0, 750.0, 7.0), 7.0)          # off the square: left alone
        self.assertEqual(s.kept(750.0, 750.0), 0.5)
        # right out to its edge, no fall-off: 0.97 of the way out it is still half way to the heightmap's height
        self.assertAlmostEqual(s.height_at(985.0, 750.0, 0.0), 100.0)
        self.assertEqual(s.kept(985.0, 750.0), 0.5)
        with self.assertRaisesRegex(ReliefError, "wasn't read"):
            relief(()).height_at(500.0, 500.0, 0.0)

    def test_a_16_bit_heightmap_keeps_every_step(self):
        from rusemod.relief import grid_range
        w, h, samples = read_grid(grey16_png(3, 2, [7, 1, 2, 65533, 300, 9]))
        self.assertEqual((w, h), (3, 2))
        self.assertEqual(struct.unpack(">6H", samples), (7, 1, 2, 65533, 300, 9))
        self.assertEqual(grid_range((w, h, samples)), (1, 65533))
        with self.assertRaises(ReliefError):
            read_grid(grey16_png(1, 1, [5]))


class Room(unittest.TestCase):
    def test_the_highest_the_ground_can_go(self):
        """groundgen.Shape.top: the blank start, the relief's highest sample, a hill added on top."""
        from rusemod.groundgen import Shape
        start = Stroke("level", 500.0, 500.0, 5000.0, level=100.0, weight=1.0, shape="square", edge="hard")
        r = relief((2, 2, struct.pack(">4H", 0, 32768, 65535, 100)), level=50.0, level2=450.0)
        hill = Stroke("hill", 500.0, 500.0, 100.0, height=30.0)
        shape = Shape([start, r, hill], (0.0, 0.0, 1000.0, 1000.0), 0.0)
        self.assertAlmostEqual(shape.top(), 450.0 + 30.0)


@unittest.skipIf(_np is None, "numpy isn't here: a relief's picture needs it (the apps carry it)")
class Picture_(unittest.TestCase):
    def test_laid_on_every_level_with_its_edge(self):
        """A red picture over the first cell (1,000 x 1,000, a hard edge): red inside on the overview, the cell's
        tile and its quarters; the second cell left green."""
        s = store()
        stroke = relief((2, 2, b"\x00" * 8))
        red = bytes((230, 30, 30)) * (64 * 64)
        out = lay_pictures(s, BOUNDS, [Picture(stroke, 64, 64, red)])
        painted = Tmst(*s.rebuild(out))
        for i, x, y in ((0, 500.0, 500.0), (1, 500.0, 500.0), (3, 250.0, 250.0), (6, 750.0, 750.0)):
            self.assertTrue(near(pixel(painted, painted.tiles[i], x, y), (230, 30, 30)), i)
        self.assertTrue(near(pixel(painted, painted.tiles[2], 1500.0, 500.0), GREEN))   # the other cell
        # past the hard edge's full part (0.85 of the way out) the green comes back by the S-curve
        edge = pixel(painted, painted.tiles[3], 500.0 - 0.99 * 500.0, 250.0)
        self.assertTrue(near(edge, GREEN, 40), edge)

    @unittest.skipIf(_np is None, "numpy isn't installed")
    def test_no_edge_lays_it_full_to_the_edge(self):
        """edge = "none" (the relief brush only): a whole map's picture, full out to its square's very edge."""
        from rusemod.relief import _strength
        xs, ys = _np.array([500.0, 980.0, 999.0, 1001.0]), _np.array([500.0, 500.0, 500.0, 500.0])
        share, _us, _vs = _strength(relief(()), xs, ys)
        self.assertLess(share[2], 0.05)                 # hard: faded by the edge
        share, _us, _vs = _strength(relief((), edge="none"), xs, ys)
        self.assertEqual(share.tolist(), [1.0, 1.0, 1.0, 0.0])
        got, = parse_strokes([{"brush": "relief", "x": 0.0, "y": 0.0, "radius": 10.0, "shape": "square",
                               "relief": "a", "level": 0.0, "level2": 1.0, "edge": "none"}])
        self.assertEqual(got.edge, "none")
        with self.assertRaisesRegex(BrushError, "for the relief brush"):
            parse_strokes([{"brush": "paint", "x": 0.0, "y": 0.0, "radius": 10.0, "colour": "#a07850",
                            "edge": "none"}])

    def test_a_pixel_reads_the_mip_its_size(self):
        p = Picture(relief(()), 64, 64, bytes(3 * 64 * 64))
        self.assertEqual(p.size, (1000.0 / 64, 1000.0 / 64))
        self.assertEqual(p.mip_for(1000.0 / 64), 0)
        self.assertEqual(p.mip_for(1000.0 / 64 * 2), 1)
        self.assertEqual(p.mip_for(1000.0 / 64 * 3), 1)
        self.assertEqual(p.mip_for(1e9), len(p.mips) - 1)

    @unittest.skipIf(_np is None, "numpy isn't installed")
    def test_the_picture_kept_as_bytes_reads_the_same(self):
        """The picture's own mip is its bytes and the next made a few rows at a time: the same values as floats."""
        w, h = 9, 11
        rgb = bytes((k * 37 + k // 3) % 256 for k in range(w * h * 3))
        old_rows = Picture.ROWS
        Picture.ROWS = 4
        try:
            p = Picture(relief(()), w, h, rgb)
        finally:
            Picture.ROWS = old_rows
        px = _np.frombuffer(rgb, dtype=_np.uint8).reshape(h, w, 3).astype(_np.float64)
        half = (px[0:10:2, 0:8:2] + px[1:10:2, 0:8:2] + px[0:10:2, 1:8:2] + px[1:10:2, 1:8:2]) * 0.25
        self.assertEqual(p.mips[0].dtype, _np.uint8)
        self.assertTrue((p.mips[1] == half).all())
        us, vs = _np.array([0.13, 0.5, 0.97]), _np.array([0.2, 0.61, 0.9])
        fx, fy = _np.clip(us * w - 0.5, 0, w - 1), _np.clip(vs * h - 0.5, 0, h - 1)
        i, j = fx.astype(int), fy.astype(int)
        i1, j1 = _np.minimum(i + 1, w - 1), _np.minimum(j + 1, h - 1)
        tx, ty = (fx - i)[:, None], (fy - j)[:, None]
        top = px[j, i] + (px[j, i1] - px[j, i]) * tx
        bottom = px[j1, i] + (px[j1, i1] - px[j1, i]) * tx
        self.assertTrue(_np.allclose(p.colours(us, vs, p.size[0]), top + (bottom - top) * ty, rtol=0, atol=1e-12))


class ModFiles(unittest.TestCase):
    def test_load_mod_reads_the_heightmap_and_lists_the_picture(self):
        from rusemod.build import BuildError, load_mod
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            mod = Path(d, "m")
            (mod / "maps" / "M04_Cotentin").mkdir(parents=True)
            (mod / "files" / "terrain").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "maps" / "M04_Cotentin" / "terrain.toml").write_text(
                '[[stroke]]\nbrush = "relief"\nx = 1.0\ny = 2.0\nradius = 500.0\nshape = "square"\n'
                'relief = "hills"\nlevel = 0.0\nlevel2 = 1000.0\n', encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "hills.png, which isn't in the mod's files/terrain"):
                load_mod(mod)
            (mod / "files" / "terrain" / "hills.png").write_bytes(grey16_png(2, 2, [0, 1, 2, 3]))
            info, _ops = load_mod(mod)
            s, = info.terrain["M04_Cotentin"]
            self.assertEqual(s.grid[:2], (2, 2))
            self.assertEqual(info.relief_pictures, {})
            (mod / "files" / "terrain" / "hills-ground.png").write_bytes(b"x")
            info, _ops = load_mod(mod)
            (s2, path), = info.relief_pictures["M04_Cotentin"]
            self.assertEqual((s2, path.name), (s, "hills-ground.png"))

    def test_paint_within_an_area_gets_its_clip(self):
        from rusemod.build import BuildError, load_mod
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            mod = Path(d, "m")
            (mod / "maps" / "M04_Cotentin").mkdir(parents=True)
            (mod / "files" / "terrain").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            terrain = mod / "maps" / "M04_Cotentin" / "terrain.toml"
            paint = ('[[stroke]]\nbrush = "paint"\nx = 400.0\ny = 400.0\nradius = 300.0\ncolour = "#a07850"\n'
                     'within = "hills:7"\n')
            terrain.write_text(paint, encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "within relief 'hills'"):
                load_mod(mod)
            terrain.write_text('[[stroke]]\nbrush = "relief"\nx = 500.0\ny = 500.0\nradius = 500.0\n'
                               'shape = "square"\nrelief = "hills"\nlevel = 0.0\nlevel2 = 1000.0\n\n' + paint,
                               encoding="utf-8")
            (mod / "files" / "terrain" / "hills.png").write_bytes(grey16_png(2, 2, [0, 1, 2, 3]))
            with self.assertRaisesRegex(BuildError, "hills-areas.png"):
                load_mod(mod)
            (mod / "files" / "terrain" / "hills-areas.png").write_bytes(grey16_png(4, 4, [0, 7] + [0] * 14))
            info, _ops = load_mod(mod)
            s, = info.paint["M04_Cotentin"]
            # the box 100..700 over cells 250 across: columns 0..2, rows 0..2; area 7 sits top left but one (row 3)
            self.assertEqual(s.clip, (0.0, 0.0, 250.0, 3, 3, bytes(9)))


@unittest.skipIf(_np is None, "numpy isn't installed")
class Areas(unittest.TestCase):
    """A relief's area picture (relief.areas_file, read_areas, area_clip): a paint stroke `within` one area."""

    def test_a_16_bit_picture_written_and_read_back(self):
        from rusemod.png import grey16_bytes, read_grey16
        samples = b"".join(struct.pack(">H", v) for v in (0, 1, 65535, 300, 300, 300))
        self.assertEqual(read_grey16(grey16_bytes(3, 2, samples)), (3, 2, samples))
        with self.assertRaisesRegex(Exception, "aren't 3 x 3"):
            grey16_bytes(3, 3, samples)

    def test_the_clip_holds_the_areas_cells(self):
        from rusemod.relief import area_clip, read_areas
        areas = read_areas(grey16_png(4, 4, [0, 7, 0, 0] + [0] * 8 + [0, 0, 7, 0]))
        s = relief((0,) * 4)   # x, y 0..1000: cells 250 across; the picture's top row the high y side
        x0, y0, cell, cols, rows, bits = area_clip(s, areas, 7, (0.0, 1000.0, 0.0, 1000.0))
        self.assertEqual((x0, y0, cell, cols, rows), (0.0, 0.0, 250.0, 4, 4))
        self.assertEqual([k for k, b in enumerate(bits) if b], [0 * 4 + 2, 3 * 4 + 1])
        self.assertEqual(area_clip(s, areas, 7, (300.0, 600.0, 800.0, 900.0)),
                         (250.0, 750.0, 250.0, 2, 1, b"\x01\x00"))
        self.assertEqual(area_clip(s, areas, 7, (2000.0, 3000.0, 0.0, 10.0)), (0.0, 0.0, 250.0, 1, 1, b"\0"))

    def test_only_along_the_axes_with_square_pixels(self):
        from rusemod.relief import area_clip, read_areas
        square = read_areas(grey16_png(2, 2, [1, 1, 1, 1]))
        with self.assertRaisesRegex(ReliefError, "along the map's axes"):
            area_clip(relief((0,) * 4, dx=0.0, dy=1.0), square, 1, (0.0, 10.0, 0.0, 10.0))
        with self.assertRaisesRegex(ReliefError, "pixels square"):
            area_clip(relief((0,) * 4), read_areas(grey16_png(4, 2, [1] * 8)), 1, (0.0, 10.0, 0.0, 10.0))

    def test_within_read_and_written_back(self):
        row = {"brush": "texture", "x": 1.0, "y": 2.0, "radius": 3.0, "texture": "swatch:dday:wheat", "within": "mont:12"}
        got, = parse_strokes([row])
        self.assertEqual(got.within, "mont:12")
        again, = parse_strokes([dict(__import__("tomllib").loads(strokes_toml([got]))["stroke"][0])])
        self.assertEqual(again, got)
        for bad in ("mont", "mont:0", "mont:65536", "Mont:1", 5):
            with self.assertRaisesRegex(BrushError, "within must be"):
                parse_strokes([dict(row, within=bad)])
        with self.assertRaisesRegex(BrushError, "for the paint, stamp, texture"):
            parse_strokes([{"brush": "hill", "x": 0.0, "y": 0.0, "radius": 10.0, "height": 5.0, "within": "a:1"}])


if __name__ == "__main__":
    unittest.main()
