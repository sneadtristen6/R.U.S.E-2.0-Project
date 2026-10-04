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

    def test_a_road_under_trees_fainter_and_greyer_on_every_level(self):
        """Lines a road that keeps its trees, in a wood (shaded): painted on every level still, but only partly and
        greyer; the other line (a road that clears its trees) as before."""
        from rusemod.groundpaint import _under_trees
        s = store()
        lines = [[(100.0, 250.0), (900.0, 250.0)], [(100.0, 750.0), (900.0, 750.0)]]
        out = paint_lines(s, BOUNDS, lines, RED, width=40.0, shaded=lambda x, y, i: i == 0)
        painted = Tmst(*s.rebuild(out))
        for i in (0, 1, 3):  # the overview, cell 0's tile, its top-left quarter
            under = pixel(painted, painted.tiles[i], 300.0, 250.0)
            self.assertTrue(near(under, _under_trees(GREEN, RED)), (i, under))
            self.assertFalse(near(under, GREEN, 8), i)  # painted, not left off
        for i in (0, 1):  # (the quarter holds the first line only)
            self.assertTrue(near(pixel(painted, painted.tiles[i], 300.0, 750.0), RED), i)  # the cleared road

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

    def test_the_maps_profile_measured_once_and_kept(self):
        """With a cache folder the map's road look is measured once (half a build's time on M03_Italie) and read
        back after, the same; anything it's measured from changing (here its road pieces) means measuring again."""
        import tempfile
        from unittest import mock
        from rusemod import groundpaint
        big = (0.0, 0.0, 20000.0, 10000.0)
        s = store()
        painted = Tmst(*s.rebuild(paint_lines(s, big, [[(1000.0, 5000.0), (19000.0, 5000.0)]], RED, width=1000.0)))
        head = bytearray(0x23C)
        struct.pack_into("<2I", head, 0x10, 2, 1)  # its grid: 2 x 1 cells of 10,000
        struct.pack_into("<2f", head, 0x1C, 10000.0, 10000.0)
        mesh = bytes(head) + struct.pack("<6f", *big[:2], 0.0, *big[2:], 50.0)
        files = {"output\\highdef.tms": mesh, "output\\highdef.tmst_pc": painted.index,
                 "output\\highdef.tmst_chunk_pc": painted.chunk}
        pieces = [(x, 5000.0, x + 200.0, 5000.0, x + 400.0, 5000.0, x + 600.0, 5000.0) for x in range(2000, 17000, 600)]
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(groundpaint, "road_profile", wraps=groundpaint.road_profile) as measure:
            first = groundpaint.map_road_profile(files.get, pieces, d)
            again = groundpaint.map_road_profile(files.get, pieces, d)
            self.assertEqual(measure.call_count, 1)
            self.assertEqual(again, first)
            self.assertEqual(first, groundpaint.map_road_profile(files.get, pieces))  # as with no cache
            groundpaint.map_road_profile(files.get, pieces[:-1], d)
            self.assertEqual(measure.call_count, 3)  # (the uncached call, then the changed pieces)

    def test_a_game_tile_decoded_once_and_kept(self):
        """A shipped (TGU1) tile's blocks are kept in the cache folder by the payload's fingerprint: decoded once,
        read back the same; another payload is decoded on its own."""
        import tempfile
        from unittest import mock
        from rusemod import groundpaint
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(groundpaint.tgu1, "decode", side_effect=lambda p: bytes(reversed(p))) as decode:
            a = groundpaint._tgu1_blocks(b"TGU1 one", d)
            self.assertEqual(groundpaint._tgu1_blocks(b"TGU1 one", d), a)
            self.assertEqual(decode.call_count, 1)
            self.assertEqual(groundpaint._tgu1_blocks(b"TGU1 two", d), b"owt 1UGT")
            self.assertEqual(groundpaint._tgu1_blocks(b"TGU1 one"), a)  # no cache: decoded as before
            self.assertEqual(decode.call_count, 3)

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


SAND = (200, 170, 110)


def two_colour_store():
    """The made-up tile set with cell 0 grass and cell 1 sand, at every level (the overview: its halves)."""
    plain = store()
    tiles = []
    for t in plain.tiles:
        side = 256 if t.level == plain.depth else 512
        if t.level == plain.depth:  # the overview: left half grass, right half sand
            row = [dxt1_solid(rgb565(*(GREEN if bx < side // 8 else SAND))) for bx in range(side // 4)]
            tiles.append(zipo_tile(b"".join(row) * (side // 4), side, side))
            continue
        ax0 = plain.area(t)[0]
        tiles.append(zipo_tile(dxt1_solid(rgb565(*(GREEN if ax0 < 1 else SAND))) * (side * side // 16), side, side))
    return Tmst(*make_set(tiles))


def strokes(*items):
    from rusemod.brush import parse_strokes
    return parse_strokes(list(items))


def paint_strokes_of(s, made):
    from rusemod.groundpaint import paint_strokes
    return paint_strokes(s, BOUNDS, made)


class MapPaint(unittest.TestCase):
    """The Map Paint tab's strokes (PLAN §15): a colour, or the map's own ground copied from another spot, laid on the
    ground's picture at every level, each at its opacity times its brush's fall-off."""

    def test_what_hides_it_up_close_goes_where_it_is_at_least_half_strength(self):
        """TESTS.md T21: only with the stickers, low plants and stones taken off does paint show near the camera; the
        erase areas go by size (T26) and reach as far as the stroke paints at least half."""
        from rusemod.brush import Stroke
        from rusemod.groundpaint import paint_clearing
        hard = Stroke("paint", 0.0, 0.0, 1000.0, colour="#ff0000", edge="hard")
        soft = Stroke("paint", 0.0, 0.0, 1000.0, colour="#ff0000")
        faint = Stroke("paint", 0.0, 0.0, 1000.0, colour="#ff0000", weight=0.4)    # under half: clears nothing
        kept = Stroke("paint", 0.0, 0.0, 1000.0, colour="#ff0000", clear=False)    # the modder turned it off
        stamp = Stroke("stamp", 0.0, 0.0, 1000.0, sx=5000.0, sy=0.0, edge="hard")
        hill = Stroke("hill", 0.0, 0.0, 1000.0, height=10.0)
        areas = paint_clearing([hard, soft, faint, kept, stamp, hill], ["TypeWarrior/Champs_Bles"])
        self.assertEqual(len(areas), 3)
        self.assertAlmostEqual(areas[0].radius, 925.0, places=3)  # full out to 0.85, half way down its S-curve at 0.925
        self.assertEqual((areas[0].what, areas[0].types, areas[0].by_size),
                         (("decal",), ("TypeWarrior/Champs_Bles",), True))
        self.assertAlmostEqual(soft.strength_at(areas[1].radius, 0.0), 0.5, places=6)  # soft: where it is half
        self.assertAlmostEqual(areas[2].radius, 925.0, places=3)                       # a stamp clears too
        line = Stroke("paint", 0.0, 0.0, 100.0, colour="#ff0000", edge="hard", shape="line", x2=5000.0, y2=0.0)
        (a,) = paint_clearing([line], [])
        self.assertEqual((a.shape, a.x2, a.y2, a.types), ("line", 5000.0, 0.0, ()))

    def test_a_colour_on_every_level_it_covers(self):
        from rusemod.groundpaint import paint_strokes
        s = store()
        out = paint_strokes(s, BOUNDS, strokes({"brush": "paint", "x": 300.0, "y": 250.0, "radius": 100.0,
                                                "colour": "#e61e1e", "edge": "hard"}))
        self.assertEqual(sorted(out), [0, 1, 3])  # the overview, cell 0's tile, its top-left quarter
        painted = Tmst(*s.rebuild(out))
        for i in (0, 1, 3):
            self.assertTrue(near(pixel(painted, painted.tiles[i], 300.0, 250.0), RED), i)
        self.assertTrue(near(pixel(painted, painted.tiles[3], 300.0, 400.0), GREEN))  # 150 off: grass

    def test_opacity_and_order(self):
        from rusemod.groundpaint import paint_strokes
        s = store()
        half = paint_strokes(s, BOUNDS, strokes({"brush": "paint", "x": 300.0, "y": 250.0, "radius": 100.0,
                                                 "colour": "#e61e1e", "edge": "hard", "weight": 0.5}))
        got = pixel(Tmst(*s.rebuild(half)), Tmst(*s.rebuild(half)).tiles[3], 300.0, 250.0)
        self.assertTrue(near(got, tuple((a + b) // 2 for a, b in zip(GREEN, RED)), 16), got)
        both = paint_strokes(s, BOUNDS, strokes(  # a later stroke over an earlier one: the later shows
            {"brush": "paint", "x": 300.0, "y": 250.0, "radius": 100.0, "colour": "#e61e1e", "edge": "hard"},
            {"brush": "paint", "x": 300.0, "y": 250.0, "radius": 100.0, "colour": "#c8aa6e", "edge": "hard"}))
        painted = Tmst(*s.rebuild(both))
        self.assertTrue(near(pixel(painted, painted.tiles[3], 300.0, 250.0), SAND))

    def test_a_stamp_copies_the_maps_own_ground_from_its_spot(self):
        """Grass in cell 0 stamped with the sand 1,000 units to its right (cell 1), at every level; a stamp copies the
        map as it was, never another stroke's paint."""
        from rusemod.groundpaint import paint_strokes
        s = two_colour_store()
        out = paint_strokes(s, BOUNDS, strokes(
            {"brush": "paint", "x": 1300.0, "y": 250.0, "radius": 100.0, "colour": "#e61e1e", "edge": "hard"},
            {"brush": "stamp", "x": 300.0, "y": 250.0, "radius": 100.0, "sx": 1000.0, "sy": 0.0, "edge": "hard"}))
        painted = Tmst(*s.rebuild(out))
        self.assertTrue(near(pixel(painted, painted.tiles[3], 300.0, 250.0), SAND))  # the stamp: sand, not red
        self.assertTrue(near(pixel(painted, painted.tiles[1], 300.0, 250.0), SAND))  # cell 0's whole tile too
        self.assertTrue(near(pixel(painted, painted.tiles[3], 300.0, 450.0), GREEN))  # off the stamp: grass

    def test_a_dab_under_two_pixels_tints_a_coarse_level(self):
        """A dab 3 units across is a fraction of an overview pixel (about 7.8 units): it tints it a little instead
        of all or nothing; on the finest level (about 1 unit a pixel) its middle is fully painted."""
        from rusemod.groundpaint import paint_strokes
        s = store()
        out = paint_strokes(s, BOUNDS, strokes({"brush": "paint", "x": 303.9, "y": 253.9, "radius": 3.0,
                                                "colour": "#e61e1e", "edge": "hard"}))
        painted = Tmst(*s.rebuild(out))
        over = pixel(painted, painted.tiles[0], 303.9, 253.9)
        self.assertFalse(near(over, GREEN, 4), over)  # tinted
        self.assertFalse(near(over, RED, 40), over)    # but only a little
        self.assertTrue(near(pixel(painted, painted.tiles[3], 303.9, 253.9), RED))

    def test_a_ginormous_patch_is_quick_and_the_same(self):
        """A solid patch over most of a cell (hard edge, full) fills the blocks it covers whole at once: the same bytes
        as working out every pixel, with a softer stroke on top of part of it."""
        import time
        from unittest import mock
        from rusemod import groundpaint
        s = store()
        red = {"brush": "paint", "x": 500.0, "y": 500.0, "radius": 450.0, "colour": "#e61e1e", "edge": "hard"}
        both = strokes(red, {"brush": "paint", "x": 300.0, "y": 300.0, "radius": 60.0, "colour": "#c8aa6e", "weight": 0.5})
        quick = paint_strokes_of(s, both)
        with mock.patch.object(groundpaint, "_solid_over", return_value=False):
            self.assertEqual(paint_strokes_of(s, both), quick)  # the same bytes, every pixel worked out
        painted = Tmst(*s.rebuild(quick))
        self.assertTrue(near(pixel(painted, painted.tiles[1], 700.0, 600.0), RED))
        alone = strokes(red)
        start = time.perf_counter()
        paint_strokes_of(s, alone)
        took = time.perf_counter() - start
        with mock.patch.object(groundpaint, "_solid_over", return_value=False):
            start = time.perf_counter()
            paint_strokes_of(s, alone)
            slow_took = time.perf_counter() - start
        # only its edge is worked out pixel by pixel: a hard edge fades over its outer 15%, a quarter of the patch
        self.assertLess(took, slow_took * 0.75)

    def test_a_stamp_copies_the_close_up_map_too(self):
        from rusemod.groundpaint import stamp_detail
        raw = div_map(road_row={4, 5})  # the map's road mark along y = 140 .. 170
        new, notes = stamp_detail(raw, BOUNDS, strokes(
            {"brush": "stamp", "x": 1000.0, "y": 700.0, "radius": 60.0, "sx": 0.0, "sy": -544.0, "edge": "hard"},
            {"brush": "paint", "x": 1000.0, "y": 300.0, "radius": 60.0, "colour": "#ffffff"}))
        self.assertIn("close-up map:", notes[0])
        rgb, a = mark(new, 1000.0, 700.0)  # where the stamp painted: the road's mark, copied from 544 above
        self.assertTrue(near(rgb, ROAD_MARK[0], 8) and abs(a - ROAD_MARK[1]) <= 6, (rgb, a))
        rgb, a = mark(new, 1000.0, 300.0)  # the paint stroke leaves the close-up map alone
        self.assertTrue(near(rgb, GROUND_MARK[0], 8) and abs(a - GROUND_MARK[1]) <= 6, (rgb, a))
        self.assertEqual(stamp_detail(raw, BOUNDS, strokes(
            {"brush": "paint", "x": 1.0, "y": 1.0, "radius": 5.0, "colour": "#ffffff"}))[0], b"")

    def test_the_strokes_in_the_file(self):
        from rusemod.brush import BrushError, strokes_toml
        import tomllib
        made = strokes({"brush": "paint", "x": 1.0, "y": 2.0, "radius": 30.0, "colour": "#A07850", "weight": 0.4},
                       {"brush": "stamp", "x": 1.0, "y": 2.0, "radius": 30.0, "sx": 500.0, "sy": -20.0,
                        "shape": "square", "dx": 1.0, "dy": 1.0})
        self.assertEqual((made[0].colour, made[0].weight, made[1].sx, made[1].sy), ("#a07850", 0.4, 500.0, -20.0))
        text = strokes_toml(made)
        self.assertIn('colour = "#a07850"', text)
        self.assertEqual(strokes(*tomllib.loads(text)["stroke"]), made)
        self.assertEqual(made[0].height_at(1.0, 2.0, 50.0), 50.0)  # the ground's shape stays
        for bad in ({"brush": "paint", "x": 1.0, "y": 2.0, "radius": 3.0},                       # no colour
                    {"brush": "paint", "x": 1.0, "y": 2.0, "radius": 3.0, "colour": "red"},
                    {"brush": "raise", "x": 1.0, "y": 2.0, "radius": 3.0, "height": 1.0, "colour": "#ffffff"},
                    {"brush": "stamp", "x": 1.0, "y": 2.0, "radius": 3.0, "sx": 0.0, "sy": 0.0},  # copies itself
                    {"brush": "stamp", "x": 1.0, "y": 2.0, "radius": 3.0, "sx": 5.0},             # no sy
                    {"brush": "hill", "x": 1.0, "y": 2.0, "radius": 3.0, "height": 1.0, "sx": 5.0, "sy": 1.0}):
            with self.subTest(bad=bad), self.assertRaises(BrushError):
                strokes(bad)

    def test_the_build_takes_them_off_the_ground_edits(self):
        from types import SimpleNamespace
        from rusemod.build import _paint_brushes
        made = strokes({"brush": "paint", "x": 1.0, "y": 2.0, "radius": 30.0, "colour": "#a07850"},
                       {"brush": "raise", "x": 1.0, "y": 2.0, "radius": 30.0, "height": 5.0},
                       {"brush": "stamp", "x": 1.0, "y": 2.0, "radius": 30.0, "sx": 5.0, "sy": 0.0})
        info = SimpleNamespace(terrain={"Blitz": made, "Only": made[:1]}, paint={})
        _paint_brushes(info)
        self.assertEqual([s.brush for s in info.paint["Blitz"]], ["paint", "stamp"])
        self.assertEqual([s.brush for s in info.terrain["Blitz"]], ["raise"])
        self.assertNotIn("Only", info.terrain)  # a map with only paint leaves its ground files alone


if __name__ == "__main__":
    unittest.main()
