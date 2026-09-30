"""Painting on the ground's picture (rusemod.groundpaint), on a tiny made-up tile set: 2x1 cells of 1,000 map units,
a 256-pixel overview tile like the game's (its size comes from the payload, never assumed) and 512-pixel tiles."""
import struct
import unittest

from test_tmst import make_set
from rusemod import dxt
from rusemod.groundpaint import PaintError, _blocks, map_bounds, paint_lines, paint_roads
from rusemod.tmst import Tmst, dxt1_solid, rgb565, zipo_tile

GREEN = (40, 120, 40)
RED = (230, 30, 30)
BOUNDS = (0.0, 0.0, 2000.0, 1000.0)


def grass(side):
    return zipo_tile(dxt1_solid(rgb565(*GREEN)) * (side * side // 16), side, side)


def store():
    index, chunk = make_set([grass(256)] + [grass(512) for _ in range(10)])  # record 0 is the overview
    return Tmst(index, chunk)


def pixel(s, tile, x, y):
    """The colour at map (x, y) in `tile`."""
    blocks, w, h = _blocks(s, tile)
    ax0, ay0, ax1, ay1 = s.area(tile)
    px, py = int((x / 1000 - ax0) / (ax1 - ax0) * w), int((y / 1000 - ay0) / (ay1 - ay0) * h)
    k = (py // 4) * (w // 4) + px // 4
    return dxt.block_pixels(bytes(blocks[8 * k:8 * k + 8]))[(py % 4) * 4 + px % 4]


def near(a, b, tol=24):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


class Painting(unittest.TestCase):
    def test_a_line_on_every_level_it_crosses(self):
        s = store()
        out = paint_lines(s, BOUNDS, [[(100.0, 250.0), (900.0, 250.0)]], RED, width=40.0)
        # the line lies in cell 0's top half: the overview, cell 0's whole tile, and its two top quarters
        self.assertEqual(sorted(out), [0, 1, 3, 4])
        painted = Tmst(*s.rebuild(out))
        for i, x in ((0, 500.0), (1, 500.0), (3, 300.0), (4, 700.0)):  # a point inside each tile, on the line
            self.assertTrue(near(pixel(painted, painted.tiles[i], x, 250.0), RED), i)
        fine = painted.tiles[3]  # cell 0, top-left quarter
        self.assertTrue(near(pixel(painted, fine, 300.0, 350.0), GREEN))  # 100 units off the line: grass
        self.assertEqual(_blocks(painted, painted.tiles[0])[1:], (256, 256))  # the overview kept its own size

    def test_nothing_crossed_nothing_written(self):
        self.assertEqual(paint_lines(store(), BOUNDS, [[(100.0, 250.0), (900.0, 250.0)]][:0], RED), {})
        self.assertEqual(paint_lines(store(), BOUNDS, [[(5000.0, 5000.0), (6000.0, 5000.0)]], RED), {})

    def test_a_map_pack_both_sets_in_its_roads_colour(self):
        s = store()
        mesh = bytes(0x23C) + struct.pack("<6f", *BOUNDS[:2], 0.0, *BOUNDS[2:], 50.0)
        files = {"output\\highdef.tms": mesh, "output\\highdef.tmst_pc": s.index, "output\\highdef.tmst_chunk_pc": s.chunk}
        members, notes = paint_roads(files.get, lambda m: "map\\" + m, [[(1100.0, 500.0), (1900.0, 500.0)]], [], 40.0)
        self.assertEqual(sorted(members), ["map\\output\\highdef.tmst_chunk_pc", "map\\output\\highdef.tmst_pc"])
        self.assertEqual(notes[0], "road colour (150, 140, 120)")  # no road on the map: a grey-brown
        self.assertIn("highdef: ", notes[1])
        self.assertEqual(map_bounds(mesh), BOUNDS)
        with self.assertRaisesRegex(PaintError, "no ground mesh"):
            paint_roads({}.get, str, [[(0.0, 0.0), (1.0, 1.0)]], [])


if __name__ == "__main__":
    unittest.main()
