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


class TheTilesGrid(unittest.TestCase):
    def test_tiles_keep_the_games_grid_where_the_ground_ends_short_of_it(self):
        """On 6 maps (Alpha, Beta, ...) the ground mesh ends at 1,964,160 while the tiles' grid is 6 cells of
        327,680: the paint goes by the grid (the map's own roads line up with it), not by the mesh's bounds."""
        from types import SimpleNamespace
        from rusemod.groundpaint import TILE_CELL, _cells
        close, far = SimpleNamespace(grid_w=6, grid_h=6), SimpleNamespace(grid_w=3, grid_h=3)
        self.assertEqual(_cells(close, (0.0, 0.0, 1964160.0, 1964160.0)), (TILE_CELL, TILE_CELL))
        self.assertEqual(_cells(far, (0.0, 0.0, 1964160.0, 1964160.0)), (2 * TILE_CELL, 2 * TILE_CELL))
        self.assertEqual(_cells(close, (0.0, 0.0, 6 * TILE_CELL, 6 * TILE_CELL)), (TILE_CELL, TILE_CELL))
        self.assertEqual(_cells(close, (0.0, 0.0, 6000.0, 3000.0)), (1000.0, 500.0))  # not near the grid: the bounds


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


GROUND_MARK = ((165, 138, 24), 96)   # a close-up map's ground: its channels are data (blue 24 on every map)
ROAD_MARK = ((140, 130, 24), 128)    # where the map has a road: red lower, alpha higher


def div_map(w=64, h=32, road_row=None):
    """A made-up close-up map over BOUNDS (DXT5, ZIPO like the game's): the ground's mark everywhere, the road's on
    the pixel rows `road_row` (a set) when given."""
    from rusemod.tmst import make_tgv, zipo_pack
    blocks = bytearray()
    for by in range(h // 4):
        for _bx in range(w // 4):
            rows = [ROAD_MARK if road_row and by * 4 + r in road_row else GROUND_MARK for r in range(4)]
            blocks += dxt.encode_dxt5_block([rows[i // 4][0] for i in range(16)], [rows[i // 4][1] for i in range(16)])
    return make_tgv(w, h, "DXT5_LIN", [zipo_pack(bytes(blocks))])


def mark(raw, x, y, bounds=BOUNDS):
    from rusemod.tmst import Tgv, zipo_unpack
    tex = Tgv(raw)
    blocks = zipo_unpack(tex.payload(0))
    i = int((x - bounds[0]) / (bounds[2] - bounds[0]) * tex.width)
    j = int((y - bounds[1]) / (bounds[3] - bounds[1]) * tex.height)
    k = (j // 4) * (tex.width // 4) + i // 4
    rgb, alpha = dxt.dxt5_block(blocks[16 * k:16 * k + 16])
    return rgb[(j % 4) * 4 + i % 4], alpha[(j % 4) * 4 + i % 4]


class CloseUpMap(unittest.TestCase):
    """Up close the game's ground shaders cover the tiles with detail textures except where the close-up map marks a
    road (every map marks its own: T12 failed in every batch while new roads had no mark)."""

    def test_its_place_is_the_whole_grid(self):
        from rusemod.groundpaint import grid_bounds
        mesh = bytearray(0x368)
        struct.pack_into("<2I", mesh, 0x10, 6, 6)
        struct.pack_into("<2f", mesh, 0x1C, 327680.0, 327680.0)
        struct.pack_into("<6f", mesh, 0x23C, 0.0, 0.0, 0.0, 1964160.0, 1964160.0, 50.0)  # Alpha: the mesh ends short
        self.assertEqual(grid_bounds(bytes(mesh)), (0.0, 0.0, 1966080.0, 1966080.0))
        self.assertEqual(map_bounds(bytes(mesh)), (0.0, 0.0, 1964160.0, 1964160.0))

    def test_a_new_road_gets_the_maps_own_road_mark(self):
        from rusemod.groundpaint import paint_detail
        raw = div_map(road_row={4, 5})  # the map's road along y = 140 .. 170
        road = (100.0, 156.0, 400.0, 156.0, 700.0, 156.0, 1000.0, 156.0)  # a road piece lying on it
        new, notes = paint_detail(raw, BOUNDS, [[(200.0, 700.0), (1800.0, 700.0)]], [road], 60.0)
        self.assertTrue(new)
        self.assertIn("close-up map:", notes[0])
        rgb, a = mark(new, 1000.0, 700.0)  # on the new road: the road's mark
        self.assertTrue(near(rgb, ROAD_MARK[0], 8) and abs(a - ROAD_MARK[1]) <= 6, (rgb, a))
        rgb, a = mark(new, 1000.0, 900.0)  # 200 units off it: the ground as it was
        self.assertTrue(near(rgb, GROUND_MARK[0], 8) and abs(a - GROUND_MARK[1]) <= 6, (rgb, a))
        self.assertEqual(paint_detail(raw, BOUNDS, [], [road])[0], b"")

    def test_the_copy_in_zz_win_follows_the_pack_only_when_it_was_the_same(self):
        from rusemod.build import close_up_copy
        from types import SimpleNamespace
        shipped, marked = div_map(), div_map(road_row={8})
        path = "gen\\datasmap\\m04_cotentin\\mapdiversite\\div_map.tgv"

        def arc(held):
            def find(suffix):
                if path.endswith(suffix.lower()):
                    return SimpleNamespace(path=path)
                raise KeyError(suffix)
            return SimpleNamespace(find=find, read=lambda e: held)
        self.assertEqual(close_up_copy(arc(shipped), "M04_Cotentin", shipped, marked), (path, marked))
        self.assertIsNone(close_up_copy(arc(b"a mod's own"), "M04_Cotentin", shipped, marked))
        self.assertIsNone(close_up_copy(arc(shipped), "BlitzTwin", shipped, marked))  # a new map has no copy there
        self.assertIsNone(close_up_copy(None, "M04_Cotentin", shipped, marked))


class AsTheMapsOwnRoads(unittest.TestCase):
    """New roads painted as the map's own are across (groundpaint.road_profile): the owner's shots of 2026-10-02
    showed new roads up close too wide and pale beside D-Day's own, and the files said why (twice the close-up mark,
    twice as wide, no shoulders)."""

    def test_the_profile_is_measured_on_the_maps_road_pieces(self):
        from rusemod.groundpaint import road_profile
        big = (0.0, 0.0, 20000.0, 10000.0)  # 2 cells of 10,000: the finest tiles about 10 units a pixel
        s = store()
        painted = Tmst(*s.rebuild(paint_lines(s, big, [[(1000.0, 5000.0), (19000.0, 5000.0)]], RED, width=1000.0)))
        pieces = [(x, 5000.0, x + 200.0, 5000.0, x + 400.0, 5000.0, x + 600.0, 5000.0) for x in range(2000, 17000, 600)]
        p = road_profile(painted, big, pieces)
        self.assertEqual(p.pieces, 25)
        self.assertTrue(near(p.tile[0], RED, 30) and p.weight[0] == 1.0, (p.tile[0], p.weight[0]))
        self.assertEqual(p.weight[15:], [0.0] * 16)  # 1,500 from the line: the ground beside
        self.assertTrue(near(p.tile[-1], GREEN, 30))
        self.assertIsNone(p.detail)
        self.assertIsNone(road_profile(painted, big, pieces[:10]))  # too few roads to measure

    def test_a_line_painted_as_the_profile_says(self):
        from rusemod.groundpaint import RoadProfile
        prof = RoadProfile([RED] * 5 + [GREEN] * 26, [1.0, 1.0, 1.0, 0.5, 0.25] + [0.0] * 26, None, 25)
        self.assertEqual(prof.reach(), 500.0)
        s = store()
        painted = Tmst(*s.rebuild(paint_lines(s, BOUNDS, [[(100.0, 250.0), (900.0, 250.0)]], RED, profile=prof)))
        top, below = painted.tiles[3], painted.tiles[5]  # cell 0's top-left and bottom-left quarters
        self.assertTrue(near(pixel(painted, top, 300.0, 250.0), RED))             # in the road
        self.assertTrue(near(pixel(painted, top, 300.0, 450.0), RED))             # 200 off: still the road (weight 1)
        half = tuple((a + b) // 2 for a, b in zip(RED, GREEN))
        self.assertTrue(near(pixel(painted, below, 300.0, 550.0), half, 30))      # 300 off: half way, as the map's
        self.assertTrue(near(pixel(painted, below, 300.0, 760.0), GREEN))         # past its reach: the ground

    def test_the_close_up_map_changed_as_the_maps_roads_change_it(self):
        from rusemod.groundpaint import RoadProfile, paint_detail
        prof = RoadProfile([RED] * 31, [1.0] + [0.0] * 30, [(0.0, -8.0, 0.0, 8.0)] * 3 + [(0.0,) * 4] * 28, 25)
        road = (100.0, 156.0, 400.0, 156.0, 700.0, 156.0, 1000.0, 156.0)
        new, notes = paint_detail(div_map(), BOUNDS, [[(200.0, 700.0), (1800.0, 700.0)]], [road], 60.0, prof)
        self.assertIn("as the map's own roads change it", notes[0])
        rgb, a = mark(new, 1000.0, 700.0)  # on the line: the ground's mark plus the map's roads' change
        self.assertTrue(abs(a - (GROUND_MARK[1] + 8)) <= 3 and abs(rgb[1] - (GROUND_MARK[0][1] - 8)) <= 5, (rgb, a))
        rgb, a = mark(new, 1000.0, 980.0)  # 280 off, past its reach (the change ends at 250): as it was
        self.assertTrue(near(rgb, GROUND_MARK[0], 5) and abs(a - GROUND_MARK[1]) <= 3, (rgb, a))


if __name__ == "__main__":
    unittest.main()
