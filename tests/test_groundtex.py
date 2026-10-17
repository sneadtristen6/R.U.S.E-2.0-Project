"""Map Paint's textures (rusemod.groundtex): what names one, how a picture is made to repeat without a seam, its
smaller copies, and the Texture brush's strokes laid on the made-up tile set of test_groundpaint (2 x 1 cells of
1,000 map units), pixel by pixel and on whole grids alike."""
import math
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_groundpaint import BOUNDS, GREEN, near, pixel, strokes, two_colour_store
from rusemod import groundtex as gt
from rusemod.brush import BrushError, parse_strokes, strokes_toml
from rusemod.tmst import Tmst


def checker(n: int, cell: int, a=(200, 40, 40, 255), b=(40, 40, 200, 255)) -> bytes:
    """n x n RGBA squares of `cell` pixels, a and b in turn (seamless when cell divides n / 2... and n)."""
    out = bytearray()
    for j in range(n):
        for i in range(n):
            out += bytes(a if (i // cell + j // cell) % 2 == 0 else b)
    return bytes(out)


def ramp(n: int) -> bytes:
    """Dark at the left edge to light at the right: its left and right edges meet in a seam."""
    out = bytearray()
    for _j in range(n):
        for i in range(n):
            v = 20 + 220 * i // (n - 1)
            out += bytes((v, v, v, 255))
    return bytes(out)


class Names(unittest.TestCase):
    def test_what_names_a_texture(self):
        for ok in ("game:france/stickers01/herbe_verte", "map:M04_Cotentin:806088.0:881645", "file:my sand.png",
                   "map:Valley:-10:20.5"):
            self.assertEqual(gt.check_ref(ok), ok)
        for bad in ("", "game:herbe", "game:../x/y", "map:M04_Cotentin:1", "file:../x.png", "file:x.jpg",
                    "http://x/y.png", None, 3):
            with self.assertRaises(gt.TextureError, msg=repr(bad)):
                gt.check_ref(bad)

    def test_a_game_texture_and_its_member(self):
        member = "gen\\ww2\\res2d\\decors\\france\\stickers01\\herbe_verte.tgv"
        self.assertEqual(gt.game_member("game:france/stickers01/herbe_verte"), member)
        self.assertEqual(gt.game_ref(member.upper().replace("HERBE", "Herbe")), "game:france/stickers01/herbe_verte")
        self.assertIsNone(gt.game_ref("gen\\ww2\\res2d\\decors\\france\\alpha\\herbe_a.tgv"))  # a shape's mask

    def test_what_its_name_says(self):
        self.assertEqual(gt.describe("herbe_verteclaire_02"), ("grass", ["light_green", "grass"]))
        self.assertEqual(gt.describe("labourage_terrefonce"), ("fields", ["dark", "ploughed", "earth"]))
        self.assertEqual(gt.describe("coc_stickers_tunisie_sablehumide01")[0], "water")
        self.assertEqual(gt.describe("sousbois_brule_02", "stickers_destructions")[0], "damage")
        self.assertEqual(gt.describe("givre_degrade_03"), ("snow", ["frost", "worn"]))
        self.assertEqual(gt.describe("us_logo")[0], "marks")


class Pictures(unittest.TestCase):
    def test_a_seam_is_mended_and_the_middle_kept(self):
        n = 32
        self.assertEqual(gt.seamless(n, checker(n, 4)), checker(n, 4))  # a pattern lining up with its moved self
        seam = ramp(n)  # dark at the left edge, light at the right: they meet in a seam
        mended = gt.seamless(n, seam)
        self.assertEqual(len(mended), len(seam))

        def at(px, i, j):
            return px[4 * (j * n + i)]
        self.assertGreater(abs(at(seam, n - 1, 5) - at(seam, 0, 5)), 200)
        self.assertLess(abs(at(mended, n - 1, 5) - at(mended, 0, 5)), 20)  # across the edge as it repeats
        for i in range(n // 8, n - n // 8):  # the middle as it was
            self.assertEqual(at(mended, i, n // 2), at(seam, i, n // 2), i)
        self.assertEqual(gt.edge_weights(16)[:3], [0.15625, 0.84375, 1.0])

    def test_its_smaller_copies(self):
        px = bytes([0, 0, 0, 255, 255, 255, 255, 255, 10, 20, 30, 0, 1, 2, 3, 4])
        self.assertEqual(gt.halve(2, px), bytes([(0 + 255 + 10 + 1 + 2) // 4, (0 + 255 + 20 + 2 + 2) // 4,
                                                  (0 + 255 + 30 + 3 + 2) // 4, (255 + 255 + 0 + 4 + 2) // 4]))
        s = gt.Swatch.make("file:x.png", 8, checker(8, 1), 800.0)
        self.assertEqual([n for n, _ in s.mips], [8, 4, 2, 1])
        self.assertEqual(s.mips[-1][1], bytes((120, 40, 120, 255)))  # all of it mixed

    def test_the_middle_square_of_a_picture(self):
        w, h = 6, 4
        px = bytes(v for k in range(w * h) for v in (k, 0, 0, 255))
        n, sq = gt.square(w, h, px)
        self.assertEqual(n, 4)
        self.assertEqual([sq[4 * k] for k in range(4)], [1, 2, 3, 4])  # row 0, columns 1..4 of the picture

    def test_the_mip_a_pixel_takes(self):
        s = gt.Swatch.make("file:x.png", 64, checker(64, 8), 6400.0)  # 100 units a pixel at its own size
        self.assertEqual(s.mip_for(6400.0, 100.0), 0)
        self.assertEqual(s.mip_for(6400.0, 141.0), 0)
        self.assertEqual(s.mip_for(6400.0, 142.0), 1)  # its 200-unit pixels are nearer 142 than its 100-unit ones
        self.assertEqual(s.mip_for(3200.0, 142.0), 2)  # laid at half its size: 50, 100, 200 a pixel
        self.assertEqual(s.mip_for(6400.0, 50.0), 0)  # finer than its pixels: its finest
        self.assertEqual(s.mip_for(6400.0, 1e9), len(s.mips) - 1)
        self.assertEqual(gt.need(8192.0), 64)
        self.assertEqual(gt.need(160.0), 1)
        self.assertEqual(gt.need(1e9), gt.MOST)

    def test_a_game_picture_read_at_the_mip_wanted(self):
        """A DXT1 picture with mips (smallest first, as the game's): the smallest at least the size asked for."""
        from rusemod import dxt
        from rusemod.tmst import dxt1_solid, make_tgv, rgb565, zipo_pack
        mips = []
        for side, c in ((4, (250, 0, 0)), (8, (0, 250, 0)), (16, (0, 0, 250))):
            mips.append(zipo_pack(dxt1_solid(rgb565(*c)) * (side * side // 16)))
        raw = make_tgv(16, 16, "DXT1", mips)
        w, h, px = gt.tgv_rgba(raw, 8)
        self.assertEqual((w, h), (8, 8))
        self.assertTrue(near(px[:3], (0, 250, 0), 8))
        self.assertEqual(gt.tgv_rgba(raw, 1000)[:2], (16, 16))  # more than it has: its full size
        self.assertTrue(dxt)


class TheBrush(unittest.TestCase):
    def test_the_strokes_in_the_file(self):
        item = {"brush": "texture", "x": 10.0, "y": 20.0, "radius": 30.0, "texture": "game:france/stickers01/paille",
                "size": 4096.0, "weight": 0.5, "clear": False}
        made = parse_strokes([item])
        self.assertEqual((made[0].texture, made[0].size, made[0].kind.kind), ("game:france/stickers01/paille", 4096.0,
                                                                             "texture"))
        import tomllib
        again = parse_strokes(tomllib.loads(strokes_toml(made))["stroke"])
        self.assertEqual(again, made)
        own = parse_strokes([{**item, "size": 0.0}])
        self.assertNotIn("size", strokes_toml(own))  # its own size: said by leaving it out
        for bad, says in (({**item, "texture": "x"}, "isn't one"), ({**item, "size": -1.0}, "below 0"),
                          ({"brush": "texture", "x": 1.0, "y": 1.0, "radius": 1.0}, "needs texture"),
                          ({"brush": "paint", "x": 1.0, "y": 1.0, "radius": 1.0, "colour": "#000000",
                            "texture": "file:a.png"}, "for the texture brush"),
                          ({"brush": "paint", "x": 1.0, "y": 1.0, "radius": 1.0, "colour": "#000000", "size": 3.0},
                           "for the texture brush")):
            with self.assertRaises(BrushError) as caught:
                parse_strokes([bad])
            self.assertIn(says, str(caught.exception))


RED_BLUE = gt.Swatch.make("file:rb.png", 64, checker(64, 8), 64.0)  # 1 unit a pixel; red and blue squares of 8
SEE = gt.Swatch.make("file:see.png", 16, checker(16, 4, (250, 250, 0, 255), (0, 0, 0, 0)), 64.0)  # yellow, holes
SWATCHES = {"file:rb.png": RED_BLUE, "file:see.png": SEE}


def textured(*items):
    return strokes(*({"brush": "texture", **it} for it in items))


class Laid(unittest.TestCase):
    """Texture strokes laid by groundpaint.paint_strokes on the made-up tile set (about a unit a pixel, finest)."""

    def test_the_texture_repeats_from_the_maps_corner_at_every_level(self):
        from rusemod.groundpaint import paint_strokes
        s = two_colour_store()
        out = paint_strokes(s, BOUNDS, textured({"x": 300.0, "y": 250.0, "radius": 120.0, "texture": "file:rb.png",
                                                 "edge": "hard"}), swatches=SWATCHES)
        painted = Tmst(*s.rebuild(out))
        fine = painted.tiles[3]
        for x, y in ((260.5, 230.5), (300.5, 250.5), (324.5, 260.5)):  # (x // 8 + y // 8) even: red, else blue
            want = (200, 40, 40) if (int(x) % 64 // 8 + int(y) % 64 // 8) % 2 == 0 else (40, 40, 200)
            self.assertTrue(near(pixel(painted, fine, x, y), want, 12), (x, y))
        self.assertTrue(near(pixel(painted, fine, 300.0, 450.0), GREEN))  # off the stroke: as it was
        out = paint_strokes(s, BOUNDS, textured({"x": 300.0, "y": 250.0, "radius": 120.0, "texture": "file:rb.png",
                                                 "edge": "hard", "size": 16.0}), swatches=SWATCHES)
        painted = Tmst(*s.rebuild(out))  # laid 16 units a repeat, its squares 2 across: the overview (7.8 units a
        over = pixel(painted, painted.tiles[0], 300.0, 250.0)  # pixel) takes its mixed copy
        self.assertTrue(near(over, (120, 40, 120), 20), over)

    def test_a_see_through_texture_lays_as_much_as_it_shows(self):
        from rusemod.groundpaint import paint_strokes
        s = two_colour_store()
        out = paint_strokes(s, BOUNDS, textured({"x": 300.0, "y": 250.0, "radius": 120.0, "texture": "file:see.png",
                                                 "edge": "hard", "size": 64.0}), swatches=SWATCHES)
        painted = Tmst(*s.rebuild(out))
        self.assertTrue(near(pixel(painted, painted.tiles[3], 258.0, 194.0), (250, 250, 0), 12))  # yellow square
        self.assertTrue(near(pixel(painted, painted.tiles[3], 274.0, 194.0), GREEN))  # a hole: the grass shows

    def test_a_texture_not_made_ready_is_an_error(self):
        from rusemod.groundpaint import PaintError, paint_strokes
        with self.assertRaises(PaintError):
            paint_strokes(two_colour_store(), BOUNDS, textured({"x": 300.0, "y": 250.0, "radius": 50.0,
                                                                "texture": "file:none.png"}), swatches=SWATCHES)

    def test_whole_grids_lay_the_same_tiles_as_pixel_by_pixel(self):
        import rusemod.groundpaint as gp
        if gp.whole_arrays() is None:
            self.skipTest("numpy isn't here: paint_strokes paints pixel by pixel alone")
        sets = {
            "one texture, soft": [{"brush": "texture", "x": 500.0, "y": 500.0, "radius": 300.0,
                                   "texture": "file:rb.png"}],
            "sizes, see-through, opacity, over a colour": [
                {"brush": "paint", "x": 600.0, "y": 400.0, "radius": 350.0, "colour": "#c8aa6e", "edge": "hard"},
                {"brush": "texture", "x": 500.0, "y": 450.0, "radius": 250.0, "texture": "file:rb.png",
                 "size": 37.5, "weight": 0.7},
                {"brush": "texture", "x": 1300.0, "y": 600.0, "radius": 400.0, "texture": "file:see.png",
                 "size": 300.0, "edge": "hard"},
                {"brush": "paint", "x": 1250.0, "y": 600.0, "radius": 100.0, "colour": "#0010d2", "weight": 0.5},
                {"brush": "texture", "x": 900.0, "y": 300.0, "radius": 200.0, "texture": "file:rb.png",
                 "shape": "square", "dx": 1.0, "dy": 0.4, "size": 900.0}],
            "under two pixels across": [
                {"brush": "texture", "x": 303.9 + 37.0 * k, "y": 253.9 + 11.0 * k, "radius": 1.5 + 0.9 * k,
                 "texture": "file:see.png" if k % 2 else "file:rb.png"} for k in range(10)],
        }
        for what, items in sets.items():
            made = strokes(*items)
            grids = gp.paint_strokes(two_colour_store(), BOUNDS, made, swatches=SWATCHES)
            with mock.patch.object(gp, "whole_arrays", lambda: None):
                pixels = gp.paint_strokes(two_colour_store(), BOUNDS, made, swatches=SWATCHES)
            self.assertTrue(pixels, what)
            self.assertEqual(sorted(grids), sorted(pixels), what)
            for i in pixels:
                self.assertEqual(grids[i], pixels[i], (what, i))

    def test_a_changed_texture_paints_its_tiles_again(self):
        """The kept tiles' fingerprints hold each texture's own: the same strokes with another picture are new."""
        import rusemod.groundpaint as gp
        made = textured({"x": 300.0, "y": 250.0, "radius": 120.0, "texture": "file:rb.png"})
        s = two_colour_store()
        _todo, one = gp._tile_names(s, BOUNDS, made, SWATCHES)
        _todo, same = gp._tile_names(s, BOUNDS, made, SWATCHES)
        other = gt.Swatch.make("file:rb.png", 64, checker(64, 4), 64.0)
        _todo, two = gp._tile_names(s, BOUNDS, made, {"file:rb.png": other})
        self.assertTrue(one)
        self.assertEqual(one, same)
        self.assertTrue(all(one[i] != two[i] for i in one))


class Decals(unittest.TestCase):
    """The game's own decals over a game texture's ground (groundtex.decal_grid): each texture its own grid, a point
    only where that texture shows on top at least half strength, only decal types the map loads, the same every
    build, spread out to fit the room the map's scenery has."""

    TYPES = {gt.game_member("game:france/stickers01/herbe_verte").lower(): [
        gt.DecalType("TypeWarrior/Herbe_verte", "france", 2048.0, ""),
        gt.DecalType("TypeWarrior/Herbe_verte_triangle", "france", 2048.0, "")],
        gt.game_member("game:italie/stickers/sable").lower(): [gt.DecalType("TypeWarrior/Sable", "italie", 4096.0, "")]}

    def strokes(self, *extra):
        return parse_strokes([{"brush": "texture", "x": 100000.0, "y": 100000.0, "radius": 60000.0,
                               "texture": "game:france/stickers01/herbe_verte", "shape": "square", "edge": "hard"},
                              *extra])

    def test_a_grid_over_the_ground_it_paints(self):
        out, said = gt.decal_grid(self.strokes(), self.TYPES, {"france", "communs"}, seed="m")
        step = gt.DECAL_STEP * 2 * gt.DECAL_SIZE * 2048.0
        self.assertAlmostEqual(said["step"], step)
        self.assertGreater(len(out), (100000.0 / step) ** 2 * 0.8)  # about the square's area over a point's
        self.assertTrue(all(abs(o.x - 100000.0) <= 60000.0 and abs(o.y - 100000.0) <= 60000.0 for o in out))
        self.assertEqual({o.type for o in out}, {"TypeWarrior/Herbe_verte", "TypeWarrior/Herbe_verte_triangle"})
        self.assertTrue(all(not o.solid and 0.8 * gt.DECAL_SIZE <= o.size <= 1.2 * gt.DECAL_SIZE for o in out))
        again, _ = gt.decal_grid(self.strokes(), self.TYPES, {"france", "communs"}, seed="m")
        self.assertEqual(out, again)  # the same every build

    def test_only_where_it_shows_on_top(self):
        cover = {"brush": "paint", "x": 100000.0, "y": 100000.0, "radius": 30000.0, "colour": "#000000",
                 "shape": "square", "edge": "hard"}
        out, _ = gt.decal_grid(self.strokes(cover), self.TYPES, {"france"}, seed="m")
        self.assertTrue(out)
        self.assertFalse([o for o in out if abs(o.x - 100000.0) < 25000.0 and abs(o.y - 100000.0) < 25000.0])
        off, _ = gt.decal_grid(parse_strokes([{"brush": "texture", "x": 0.0, "y": 0.0, "radius": 50000.0,
                                               "texture": "game:france/stickers01/herbe_verte", "decals": False}]),
                               self.TYPES, {"france"})
        self.assertEqual(off, [])  # decals = false: none

    def test_only_the_decals_the_map_loads(self):
        sand = {"brush": "texture", "x": 300000.0, "y": 100000.0, "radius": 60000.0, "texture": "game:italie/stickers/sable"}
        out, said = gt.decal_grid(self.strokes(sand), self.TYPES, {"france", "communs"})
        self.assertNotIn("TypeWarrior/Sable", said["types"])
        self.assertEqual(said["missing"], ["game:italie/stickers/sable"])
        out, said = gt.decal_grid(self.strokes(sand), self.TYPES, {"france", "italie"})
        self.assertIn("TypeWarrior/Sable", said["types"])

    def test_none_off_the_scenery_grid(self):
        # a stroke reaching past the grid's edge (T44's whole-map paint): its decals stop at the edge, none past it
        out, _ = gt.decal_grid(self.strokes(), self.TYPES, {"france"}, seed="m", inside=(120000.0, 90000.0))
        self.assertTrue(out)
        self.assertTrue(all(0.0 <= o.x < 120000.0 and 0.0 <= o.y < 90000.0 for o in out))
        full, _ = gt.decal_grid(self.strokes(), self.TYPES, {"france"}, seed="m")
        self.assertTrue([o for o in full if o.x >= 120000.0 or o.y >= 90000.0])

    def test_spread_out_to_fit_the_room(self):
        full, _ = gt.decal_grid(self.strokes(), self.TYPES, {"france"}, seed="m")
        fitted, said = gt.decal_grid(self.strokes(), self.TYPES, {"france"}, seed="m", most=len(full) // 4)
        self.assertTrue(said["thinned"])
        self.assertLessEqual(len(fitted), len(full) // 4)
        self.assertGreater(len(fitted), len(full) // 10)
        self.assertEqual(gt.decal_room(gt.SCENERY_MOST), 0)
        self.assertEqual(gt.decal_room(0), (gt.SCENERY_MOST - gt.ROOM_KEPT) // gt.DECAL_BYTES)

    def test_the_switch_in_the_file(self):
        made = parse_strokes([{"brush": "texture", "x": 1.0, "y": 2.0, "radius": 3.0,
                               "texture": "game:france/stickers01/paille", "decals": False}])
        self.assertFalse(made[0].decals)
        self.assertIn("decals = false", strokes_toml(made))
        self.assertTrue(parse_strokes([{"brush": "texture", "x": 1.0, "y": 2.0, "radius": 3.0,
                                        "texture": "file:a.png"}])[0].decals)
        with self.assertRaises(BrushError):
            parse_strokes([{"brush": "paint", "x": 1.0, "y": 2.0, "radius": 3.0, "colour": "#000000", "decals": True}])


class TheStudio(unittest.TestCase):
    """The Studio's calls (ruse_studio.groundtex_calls): the mod's own pictures kept in files/ground and listed, and
    the words the Texture panel says a game texture with in all ten languages."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.tmp = tempfile.TemporaryDirectory()
        self.api = StudioApi(home=Path(self.tmp.name, "home"), game_dir=Path(self.tmp.name, "game"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_your_own_pictures(self):
        import base64
        from rusemod.dxt import png_bytes
        with self.assertRaises(gt.TextureError):  # no mod picked yet: nowhere to keep it
            self.api.add_ground_picture("sand.jpg", "data:image/png;base64,")
        self.api.new_mod("My maps", "map")
        self.assertEqual(self.api.ground_pictures()["pictures"], [])
        pic = "data:image/png;base64," + base64.b64encode(png_bytes(bytes([200, 170, 110] * 48 * 32), 48, 32)).decode()
        res = self.api.add_ground_picture("Desert sand?.JPG", pic)
        self.assertEqual(res["ref"], "file:Desert sand_.png")
        again = self.api.add_ground_picture("Desert sand?.JPG", pic)
        self.assertEqual(again["ref"], "file:Desert sand__2.png")  # a name already there gets _2
        self.assertEqual([p["name"] for p in again["pictures"]], ["Desert sand_", "Desert sand__2"])
        self.assertTrue(again["pictures"][0]["thumb"].startswith("data:image/png;base64,"))
        self.assertTrue(Path(again["folder"], "Desert sand_.png").is_file())
        made = self.api.ground_texture("file:Desert sand_.png")
        self.assertEqual((made["period"], made["n"]), (gt.FILE_PERIOD, 32))  # its middle square
        with self.assertRaises(gt.TextureError):
            self.api.add_ground_picture("bad.png", "data:image/png;base64,bm90IGEgcGljdHVyZQ==")

    def test_the_palette(self):
        """ground_palette: the palette's pictures made once in a job from the map each is measured on, then listed
        with small pictures; ground_texture gives one mirrored, its repeat its side."""
        import time
        import ruse_studio.groundtex_calls as calls
        got = self.api.ground_palette()  # no game: nothing to read the materials from
        self.assertEqual(got["swatches"], [])
        self.assertIn("M04_Cotentin", got["error"])
        pack = Path(self.tmp.name, "M04_Cotentin.dat")
        pack.write_bytes(b"made-up")
        flat = lambda read, x, y, side, facing, n, cache=None: (n, bytes((120, 100, 40, 255)) * n * n)  # noqa: E731
        made = []
        with mock.patch.object(calls, "find_pack", lambda game, name: None if name == "ZZ_Win.dat" else pack), \
                mock.patch.object(self.api, "_game", lambda: Path(self.tmp.name)), \
                mock.patch.object(calls.Edat, "open", lambda path: mock.MagicMock()), \
                mock.patch.object(gt, "map_patch", lambda *a, **k: made.append(a[1:5]) or flat(*a, **k)):
            job = self.api.ground_palette()["job"]   # (no ZZ_Win.dat: the swatches without their grain)
            end = time.time() + 30
            while self.api.job(job)["state"] == "running" and time.time() < end:
                time.sleep(0.05)
            self.assertEqual(self.api.job(job)["state"], "done", self.api.job(job))
            pal = gt.palette()
            self.assertEqual(len(made), len(pal))  # each read from its map once
            listed = self.api.ground_palette()["swatches"]
            self.assertEqual([s["ref"] for s in listed], list(pal))
            self.assertEqual(len(made), len(pal))  # then kept: not read again
            wheat = next(s for s in listed if s["name"] == "wheat")
            self.assertEqual((wheat["kind"], wheat["map"], wheat["period"]), ("rows", "M04_Cotentin",
                                                                              pal["swatch:dday:wheat"].side))
            self.assertTrue(wheat["thumb"].startswith("data:image/png;base64,"))
            one = self.api.ground_texture("swatch:dday:wheat")
            self.assertEqual((one["period"], one["mirrored"]), (pal["swatch:dday:wheat"].side, True))
        with self.assertRaises(gt.TextureError):
            self.api.ground_texture("swatch:dday:none")

    def test_the_build_reads_the_mods_own_picture_in_its_strokes(self):
        from rusemod.build import BuildError, load_mod
        from rusemod.dxt import png_bytes
        import base64
        self.api.new_mod("My maps", "map")
        pic = "data:image/png;base64," + base64.b64encode(png_bytes(bytes([90, 120, 60] * 64), 8, 8)).decode()
        ref = self.api.add_ground_picture("grass.png", pic)["ref"]
        self.api.terrain_add("SuperCrossRoads4", [{"brush": "texture", "x": 1.0, "y": 2.0, "radius": 3.0,
                                                   "texture": ref, "size": 4096.0}])
        folder = Path(self.api.ground_pictures()["folder"]).parents[1]
        info, _ops = load_mod(folder)
        stroke = info.paint["SuperCrossRoads4"][0]
        self.assertEqual(stroke.texture, f"file:{info.id}/grass.png")  # named with its mod
        self.assertEqual(info.ground_pictures[stroke.texture], folder / "files" / "ground" / "grass.png")
        (folder / "files" / "ground" / "grass.png").unlink()
        with self.assertRaisesRegex(BuildError, "grass.png, which isn't in the mod's files/ground folder"):
            load_mod(folder)

    def test_every_word_a_game_texture_is_said_with(self):
        from ruse_studio.api import _words
        from rusemod import schema
        words = _words()
        keys = ({f"gtex_group_{g}" for g in gt.GROUP_ORDER} | {f"gtex_{k}" for _, k in gt.WORDS}
                | {f"gtex_theatre_{t}" for t in gt.THEATRES})
        self.assertEqual(sorted(keys - set(words)), [])
        for k in keys:
            self.assertEqual([lang for lang in schema.LANGS if not words[k].get(lang)], [], k)

    def test_a_pictures_name_for_files_ground(self):
        from ruse_studio.groundtex_calls import _file_name
        self.assertEqual(_file_name("My Sand.jpeg"), "My Sand.png")
        self.assertEqual(_file_name("../../x.png"), "_.._x.png")  # no folders: one file in files/ground
        self.assertEqual(_file_name(""), "picture.png")
        self.assertTrue(gt.file_name_ok(_file_name("été 1944!.webp")))


JPG = b"\xff\xd8\xff\xe0 a stand-in JPG"


class FakeWeb:
    """Stand-in answers for urllib.request.urlopen, nothing over the network: {address start: bytes, or an exception
    to raise}, the first that matches; every address asked is kept in `asked`."""

    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def __call__(self, req, timeout=None):
        import io
        import urllib.error
        url = getattr(req, "full_url", req)
        self.asked.append(url)
        for start, answer in self.answers.items():
            if url.startswith(start):
                if isinstance(answer, BaseException):
                    raise answer
                return io.BytesIO(answer)
        raise urllib.error.URLError("no stand-in for that address")


class Online(unittest.TestCase):
    """Online (free) textures (ruse_studio.groundtex_online) with stand-in answers: the lists read and kept a day,
    one picture taken per click from the right place, the US photos' address, words in plain English when something
    goes wrong, and the picture kept in the mod with its real size and credit (files/ground/<name>.toml)."""

    PH_AERIAL = {"aerial_beach_01": {"name": "Aerial Beach 01", "categories": ["terrain", "aerial"], "tags": ["beach"],
                                     "dimensions": [30000, 30000], "authors": {"Rob Tuytel": "All"},
                                     "thumbnail_url": "https://cdn.polyhaven.com/asset_img/thumbs/aerial_beach_01.png"}}
    PH_TERRAIN = {**PH_AERIAL, "brown_mud": {"name": "Brown Mud", "categories": ["terrain"], "tags": ["mud"],
                                             "dimensions": [2000, 1000], "authors": {"A": "All", "B": "Photo"},
                                             "thumbnail_url": "http://not-secure.example/x.png"}}
    PH_FILES = {"Diffuse": {"1k": {"jpg": {"url": "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/"
                                                  "aerial_beach_01/aerial_beach_01_diff_1k.jpg", "size": 20}}},
                "nor_gl": {"1k": {"jpg": {"url": "https://dl.polyhaven.org/nor.jpg", "size": 20}}}}

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.tmp = tempfile.TemporaryDirectory()
        self.api = StudioApi(home=Path(self.tmp.name, "home"), game_dir=Path(self.tmp.name, "game"))
        self.cache = self.api.cache_dir / "groundtex" / "online"

    def tearDown(self):
        self.tmp.cleanup()

    def web(self, answers):
        web = FakeWeb(answers)
        patch = mock.patch("urllib.request.urlopen", web)
        patch.start()
        self.addCleanup(patch.stop)
        return web

    @staticmethod
    def json(doc) -> bytes:
        import json
        return json.dumps(doc).encode()

    def test_nothing_goes_over_the_network_on_import(self):
        import importlib
        from ruse_studio import groundtex_online
        web = self.web({})
        importlib.reload(groundtex_online)
        self.assertEqual(web.asked, [])

    def test_poly_havens_list_aerial_first_and_kept_a_day(self):
        import os
        web = self.web({"https://api.polyhaven.com/assets?t=textures&c=aerial": self.json(self.PH_AERIAL),
                        "https://api.polyhaven.com/assets?t=textures&c=terrain": self.json(self.PH_TERRAIN)})
        got = self.api.online_textures("polyhaven")
        self.assertEqual(got["licence"], "CC0")
        self.assertEqual([t["id"] for t in got["items"]], ["aerial_beach_01", "brown_mud"])  # the aerial ones first
        beach, mud = got["items"]
        self.assertEqual((beach["metres"], beach["author"], beach["group"]), (30.0, "Rob Tuytel", "aerial"))
        self.assertEqual((mud["metres"], mud["author"], mud["thumb"]), (1.0, "A, B", ""))  # mm; its smaller side
        self.assertEqual(len(web.asked), 2)
        self.api.online_textures("polyhaven")
        self.assertEqual(len(web.asked), 2)  # kept: not asked again
        kept = self.cache / "polyhaven.json"
        os.utime(kept, (kept.stat().st_atime, kept.stat().st_mtime - 2 * 24 * 3600))
        self.api.online_textures("polyhaven")
        self.assertEqual(len(web.asked), 4)  # two days old: asked again

    def test_one_poly_haven_picture(self):
        import base64
        web = self.web({"https://api.polyhaven.com/assets?t=textures&c=": self.json(self.PH_AERIAL),
                        "https://api.polyhaven.com/files/aerial_beach_01": self.json(self.PH_FILES),
                        "https://dl.polyhaven.org/file/": JPG})
        self.api.online_textures("polyhaven")
        got = self.api.online_texture("polyhaven", "aerial_beach_01")
        self.assertEqual(base64.b64decode(got["picture"].split(",", 1)[1]), JPG)
        self.assertTrue(got["picture"].startswith("data:image/jpeg;base64,"))
        self.assertEqual((got["name"], got["metres"]), ("Aerial Beach 01", 30.0))
        self.assertEqual(got["credit"], {"source": "Poly Haven", "author": "Rob Tuytel", "licence": "CC0",
                                         "url": "https://polyhaven.com/a/aerial_beach_01"})
        pictures = [u for u in web.asked if "api.polyhaven.com" not in u]
        self.assertEqual(pictures, [self.PH_FILES["Diffuse"]["1k"]["jpg"]["url"]])  # only its colour picture
        elsewhere = {"Diffuse": {"1k": {"jpg": {"url": "https://elsewhere.example/beach.jpg"}}}}
        web.answers["https://api.polyhaven.com/files/aerial_beach_01"] = self.json(elsewhere)
        with self.assertRaisesRegex(gt.TextureError, "no colour picture"):
            self.api.online_texture("polyhaven", "aerial_beach_01")
        self.assertNotIn("https://elsewhere.example/beach.jpg", web.asked)
        with self.assertRaises(gt.TextureError):
            self.api.online_texture("polyhaven", "not_listed")

    def test_ambientcg_found_by_words_and_its_colour_picture_out_of_the_zip(self):
        import base64
        import io
        import zipfile

        def asset(key, dx, dy, attribute="1K-JPG"):
            return {"assetId": key, "displayName": key[:-3] + " " + key[-3:], "dimensionX": dx, "dimensionY": dy,
                    "tags": ["ground"], "shortLink": f"https://ambientcg.com/a/{key}",
                    "previewImage": {"64-PNG": f"https://acg-media.example/64/{key}.png",
                                     "128-JPG-242424": f"https://acg-media.example/128/{key}.jpg"},
                    "downloadFolders": {"default": {"downloadFiletypeCategories": {"zip": {"downloads": [
                        {"attribute": attribute, "size": 3000, "downloadLink":
                            f"https://ambientcg.com/get?file={key}_{attribute}.zip"}]}}}}}
        found = {"foundAssets": [asset("Ground054", 200, 300), asset("Grass005", 0, 0),
                                 asset("Fabric001", 100, 100, "2K-PNG")]}
        pack = io.BytesIO()
        with zipfile.ZipFile(pack, "w") as z:
            z.writestr("Ground054_1K-JPG_NormalGL.jpg", b"\xff\xd8\xff not the colour")
            z.writestr("Ground054_1K-JPG_Color.jpg", JPG)
            z.writestr("Ground054_1K-JPG.usda", b"text")
        web = self.web({"https://ambientcg.com/api/v2/full_json": self.json(found),
                        "https://ambientcg.com/get?file=Ground054_1K-JPG.zip": pack.getvalue()})
        got = self.api.online_textures("ambientcg", "")
        self.assertIn("q=ground&", web.asked[0])  # nothing typed: its ground materials
        self.assertEqual([(t["id"], t["metres"]) for t in got["items"]], [("Ground054", 2.0), ("Grass005", None)])
        self.assertEqual(got["items"][0]["thumb"], "https://acg-media.example/128/Ground054.jpg")
        self.api.online_textures("ambientcg", "wet   mud")
        self.assertIn("q=wet%20mud&", web.asked[1])
        taken = self.api.online_texture("ambientcg", "Ground054")
        self.assertEqual(base64.b64decode(taken["picture"].split(",", 1)[1]), JPG)
        self.assertEqual((taken["metres"], taken["credit"]["licence"], taken["credit"]["url"]),
                         (2.0, "CC0", "https://ambientcg.com/a/Ground054"))
        empty = io.BytesIO()
        with zipfile.ZipFile(empty, "w") as z:
            z.writestr("Grass005_1K-JPG_Roughness.jpg", b"\xff\xd8\xff")
        web.answers["https://ambientcg.com/get?file=Grass005_1K-JPG.zip"] = empty.getvalue()
        with self.assertRaisesRegex(gt.TextureError, "no colour picture"):
            self.api.online_texture("ambientcg", "Grass005")
        with self.assertRaisesRegex(gt.TextureError, "find it again"):
            self.api.online_texture("ambientcg", "Fabric001")  # (not listed: it has no 1K-JPG)

    def test_a_us_aerial_photo(self):
        import base64
        import math
        import urllib.parse
        from ruse_studio import groundtex_online as online
        web = self.web({online.NAIP + "/exportImage?": JPG})
        places = self.api.online_textures("usgs")
        self.assertEqual((places["licence"], places["metres"], places["default"]),
                         ("Public domain", [160, 320, 640, 1280], 320))
        self.assertEqual(len(places["items"]), len(online.PLACES))
        self.assertEqual(web.asked, [])  # the places are the Studio's own: nothing asked
        got = self.api.online_texture("usgs", "wheat_kansas", 320)
        self.assertEqual(len(web.asked), 1)
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(web.asked[0]).query))
        self.assertEqual((q["f"], q["format"], q["size"], q["bboxSR"], q["imageSR"]),
                         ("image", "jpg", "512,512", "3857", "3857"))
        x0, y0, x1, y1 = (float(v) for v in q["bbox"].split(","))
        self.assertAlmostEqual(x1 - x0, 320 / math.cos(math.radians(38.35)), delta=0.05)  # 320 m on the ground
        self.assertAlmostEqual(y1 - y0, x1 - x0, delta=0.05)
        self.assertAlmostEqual((x0 + x1) / 2, 6378137.0 * math.radians(-98.60), delta=0.05)
        self.assertEqual(base64.b64decode(got["picture"].split(",", 1)[1]), JPG)
        self.assertEqual((got["name"], got["metres"], got["credit"]["licence"]),
                         ("Wheat fields Kansas 320m", 320.0, "Public domain"))
        typed = self.api.online_texture("usgs", "", 1280, "38.2000, -98.4")
        self.assertEqual((typed["name"], typed["metres"]), ("US photo 38.2000 -98.4000 1280m", 1280.0))
        self.assertIn("size=1024%2C1024", web.asked[-1])
        self.assertEqual([online.naip_pixels(m) for m in online.NAIP_METRES], [256, 512, 1024, 1024])
        for where, said in (("51.5, -0.12", "48 US states"), ("somewhere", "latitude and a longitude")):
            with self.assertRaisesRegex(gt.TextureError, said):
                self.api.online_texture("usgs", "", 320, where)
        with self.assertRaisesRegex(gt.TextureError, "m across"):
            self.api.online_texture("usgs", "wheat_kansas", 300)
        self.assertEqual(len(web.asked), 2)  # none of those was asked for
        web.answers[online.NAIP + "/exportImage?"] = self.json({"error": {"code": 400, "message": "Bad extent"}})
        with self.assertRaisesRegex(gt.TextureError, r"didn't send a photo \(Bad extent\)"):
            self.api.online_texture("usgs", "wheat_kansas", 320)

    def test_the_places_are_in_the_48_states_and_said_in_every_language(self):
        from ruse_studio import groundtex_online as online
        from ruse_studio.api import _words
        from rusemod import schema
        words = _words()
        self.assertGreaterEqual(len(online.PLACES), 30)  # "the more, the merrier"
        self.assertEqual(len({p[0] for p in online.PLACES}), len(online.PLACES))
        for key, name, lat, lon, _kind in online.PLACES:
            self.assertTrue(online.US_LAT[0] <= lat <= online.US_LAT[1] and online.US_LON[0] <= lon <= online.US_LON[1])
            self.assertEqual(words[f"tex_place_{key}"]["us"], name)
            self.assertEqual([lang for lang in schema.LANGS if not words[f"tex_place_{key}"].get(lang)], [], key)

    def test_plain_words_when_a_site_cant_be_reached(self):
        import urllib.error
        self.web({"https://api.polyhaven.com/": urllib.error.URLError("timed out"),
                  "https://ambientcg.com/": TimeoutError("timed out")})
        with self.assertRaisesRegex(gt.TextureError, r"Poly Haven's list couldn't be loaded \(no answer in 20 seconds\)"):
            self.api.online_textures("polyhaven")
        with self.assertRaisesRegex(gt.TextureError, r"no answer in 20 seconds"):
            self.api.online_textures("ambientcg", "rock")
        with self.assertRaisesRegex(gt.TextureError, "isn't one of the online sources"):
            self.api.online_textures("elsewhere")
        self.assertFalse((self.cache / "polyhaven.json").exists())  # nothing kept from a failed list

    def test_the_picture_kept_with_its_real_size_and_credit(self):
        import base64
        from rusemod.dxt import png_bytes
        self.api.new_mod("My maps", "map")
        pic = "data:image/png;base64," + base64.b64encode(png_bytes(bytes([200, 170, 110] * 64), 8, 8)).decode()
        credit = {"source": "Poly Haven", "author": "Rob \"R\" Tuytel\n", "licence": "CC0",
                  "url": "https://polyhaven.com/a/aerial_beach_01", "other": "not kept"}
        res = self.api.add_ground_picture("Aerial Beach 01", pic, 30.0, credit)
        self.assertEqual(res["ref"], "file:Aerial Beach 01.png")
        folder = Path(res["folder"])
        said = gt.read_credit(folder / "Aerial Beach 01.png")
        self.assertEqual(said, {"metres": 30.0, "source": "Poly Haven", "author": "Rob \"R\" Tuytel", "licence": "CC0",
                                "url": "https://polyhaven.com/a/aerial_beach_01"})
        row = res["pictures"][0]
        self.assertEqual((row["metres"], row["period"], row["credit"]["author"]), (30.0, 30.0 * 260, "Rob \"R\" Tuytel"))
        self.assertEqual(self.api.ground_texture(res["ref"])["period"], 30.0 * 260)  # laid at its real size
        plain = self.api.add_ground_picture("mine", pic)
        self.assertFalse((folder / "mine.toml").exists())  # a picture of your own: no sidecar
        self.assertEqual(self.api.ground_texture(plain["ref"])["period"], gt.FILE_PERIOD)
        self.assertNotIn("credit", plain["pictures"][1])
        (folder / "left.toml").write_text("metres = 5.0\n", encoding="utf-8")
        self.assertEqual(self.api.add_ground_picture("left", pic)["ref"], "file:left_2.png")  # not another's sidecar
        for bad in (-1.0, float("nan"), "30", 1e9):
            with self.assertRaises(gt.TextureError):
                self.api.add_ground_picture("bad", pic, bad)


def stripes(n: int) -> bytes:
    """Rows along i (a field's rows): each row j its own shade, a dark furrow every 4th; dark top to light bottom, so
    its top and bottom meet in a seam."""
    out = bytearray()
    for j in range(n):
        v = 30 if j % 4 == 0 else 40 + 200 * j // n
        out += bytes((v, v // 2, 10, 255)) * n
    return bytes(out)


def turned(n: int, px: bytes) -> bytes:
    """The picture with its columns and rows swapped."""
    return b"".join(px[4 * (i * n + j):4 * (i * n + j) + 4] for j in range(n) for i in range(n))


ROWS = gt.Swatch.make("swatch:t:rows", 32, stripes(32), 64.0, mirrored=True)
PLAIN = gt.Swatch.make("swatch:t:plain", 32, ramp(32), 64.0, mirrored=True)
DOWN = gt.Swatch.make("swatch:t:down", 32, turned(32, ramp(32)), 64.0, mirrored=True)
COINS = [1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1]  # coin(k, 7) for k from -3 to 8


class Palette(unittest.TestCase):
    """The named palette's swatches: each repeat mirrored its own way, no seam whichever way two neighbours are."""

    def test_which_way_each_repeat_is_mirrored(self):
        self.assertEqual([gt.coin(k, 7) for k in range(-3, 9)], COINS)  # (the Studio's the same)
        for salt in (7, 68917):
            flips = [gt.coin(k, salt) for k in range(-64, 64)]
            self.assertLess(abs(sum(flips) / len(flips) - 0.5), 0.15)  # each about as often
            alike = sum(a == b for a, b in zip(flips, flips[1:])) / (len(flips) - 1)
            self.assertLess(abs(alike - 0.5), 0.15)  # the next alike about as often as chance
        for ci in range(-4, 4):
            for cj in range(-4, 4):  # along i the same down a column of repeats, across it the same along a row
                self.assertEqual(gt.mirror_of(ci, cj) & 1, gt.mirror_of(ci, 99) & 1)
                self.assertEqual(gt.mirror_of(ci, cj) & 2, gt.mirror_of(-99, cj) & 2)

    def test_no_seam_whichever_way_two_repeats_are_mirrored(self):
        for sw in (PLAIN, DOWN):  # a ramp along each way: its two ends 200 apart before it's mended
            at = sw.sampler(64.0, 2.0)  # 2 units a pixel: its finest
            worst = 0
            for k in range(-6, 6):
                for t in range(1, 64, 3):
                    edge = 64.0 * k
                    worst = max(worst, abs(at(edge - 1.0, t + 0.5)[0] - at(edge + 1.0, t + 0.5)[0]),
                                abs(at(t + 0.5, edge - 1.0)[0] - at(t + 0.5, edge + 1.0)[0]))
            self.assertLess(worst, 20, sw.ref)
        self.assertGreater(abs(ramp(32)[0] - ramp(32)[4 * 31]), 200)
        self.assertEqual(PLAIN.mips[0][1], gt.seamless(32, ramp(32)))  # its pixels: made seamless as any texture
        self.assertNotEqual(PLAIN.digest, gt.Swatch.make("swatch:t:plain", 32, ramp(32), 64.0).digest)

    def test_the_games_own_grain_under_a_swatchs_colour(self):
        """F-56: a palette swatch with a detail is its picture averaged over DETAIL_SPLIT (low_pass) and the detail's
        grain laid by itself over it (grain_of, Swatch.grain_sampler): unmirrored, so no fold line shows; about 1 on
        average, so the colour from afar is the swatch's own; light and dark up close; the scalar sampler and the
        painter's numpy sums the same bytes."""
        from rusemod import paintnp
        from rusemod.numpy2 import np
        from rusemod.brush import Stroke
        dn, rep = 32, 32 * 40.0   # 40 units a pixel: x4 ground's finest
        detail = bytes(v for j in range(dn) for i in range(dn)
                       for v in ((40, 200, 40, 255) if (i // 2 + j // 2) % 2 else (10, 60, 10, 255)))
        g = gt.grain_of(dn, detail, rep, gt.DETAIL_SPLIT)
        self.assertEqual(len(g), dn * dn)
        self.assertLess(abs(sum(g) / len(g) / gt.GRAIN_UNIT - 1.0), 0.08)   # about 1 on average
        self.assertGreater(max(g) - min(g), 60)                             # the grain, light and dark
        self.assertEqual(set(gt.grain_of(dn, bytes(4 * dn * dn), rep, gt.DETAIL_SPLIT)), {int(gt.GRAIN_UNIT)})
        n, side = 64, 64 * 40.0
        base = bytes(v for q in range(n * n) for v in (120, 90, 50, 255))
        sw = gt.Swatch.make("swatch:t:g", n, base, side, mirrored=True, grain=(dn, g, rep))
        self.assertEqual((sw.grain_period, sw.grain[0][0], len(sw.grain)), (rep, dn, 6))
        self.assertNotEqual(sw.digest, gt.Swatch.make("swatch:t:g", n, base, side, mirrored=True).digest)
        at = sw.sampler(side, 40.0)
        got = [at(x * 40.0 + 20.0, y * 40.0 + 20.0) for y in range(-40, 40, 3) for x in range(-40, 40, 3)]
        self.assertGreater(max(c[1] for c in got) - min(c[1] for c in got), 40)   # the grain shows up close
        self.assertTrue(all(abs(c[0] / max(1, c[2]) - 120 / 50) < 0.2 for c in got if c[2] > 10))   # its hue
        far = sw.sampler(side, 40.0 * 64)(10.0, 10.0)   # from afar: the grain's last mip, about 1
        self.assertLess(max(abs(far[c] - (120, 90, 50)[c]) for c in range(3)), 8)
        xs = np.arange(-40, 40) * 40.0 + 20.0
        stroke = Stroke("texture", 0.0, 0.0, 1000.0, texture="swatch:t:g")
        rgb, _a = paintnp._texture(stroke, sw, xs, xs, 40.0)
        want = [[at(x, y)[:3] for x in xs] for y in xs]
        self.assertEqual(rgb.astype(int).tolist(), [[list(c) for c in row] for row in want])   # the same bytes
        self.assertTrue(all(p.detail.lower().endswith(".tgv") and p.detail_side > 0.0 for p in gt.palette().values()))
        self.assertEqual((gt.detail_repeats(7800.0, 12000.0), gt.detail_repeats(10400.0, 4096.0)), (1, 3))
        rows = bytes(v for j in range(n) for i in range(n) for v in ((200, 150, 90, 255) if i % 4 < 2 else
                                                                      (90, 60, 30, 255)))   # rows 2 pixels wide
        kept = gt.low_pass(n, rows, side, side / n)   # (a field: averaged over the map's pixel)
        self.assertGreater(kept[0] - kept[4 * 2], 60)   # its rows still there
        lost = gt.low_pass(n, rows, side, gt.DETAIL_SPLIT)
        self.assertLess(abs(lost[0] - lost[4 * 2]), 40)   # (averaged over DETAIL_SPLIT they'd be gone)

    def test_a_fields_rows_keep_running_one_way(self):
        at = ROWS.sampler(64.0, 2.0)
        for ci in range(-4, 4):
            for cj in range(-4, 4):  # along a row inside a repeat, away from its mended edges: one shade
                for row in (12.5, 21.5, 36.5):
                    shades = {at(64.0 * ci + x, 64.0 * cj + row)[0] for x in (10.5, 20.5, 30.5, 40.5, 50.5)}
                    self.assertEqual(len(shades), 1, (ci, cj, row))

    def test_some_repeats_mirrored_some_not(self):
        at = PLAIN.sampler(64.0, 2.0)
        ways = set()
        for ci in range(8):  # the ramp rises along x in some repeats, falls in others
            x0 = 64.0 * ci
            ways.add(at(x0 + 52.5, 32.5)[0] > at(x0 + 12.5, 32.5)[0])
            self.assertEqual(ways and at(x0 + 52.5, 32.5)[0] > at(x0 + 12.5, 32.5)[0],
                             gt.mirror_of(ci, 0) & 1 == 0, ci)
        self.assertEqual(ways, {True, False})

    def test_a_turned_texture(self):
        at, turned = RED_BLUE.sampler(64.0, 1.0), RED_BLUE.sampler(64.0, 1.0, 90.0)
        for x, y in ((3.5, 5.5), (100.25, -7.75), (-40.5, 33.5)):
            self.assertEqual(turned(x, y), at(y, -x))  # a point reads the texture at itself turned back

    def test_the_same_with_and_without_numpy(self):
        import rusemod.groundpaint as gp
        if gp.whole_arrays() is None:
            self.skipTest("numpy isn't here: paint_strokes paints pixel by pixel alone")
        made = strokes({"brush": "texture", "x": 500.0, "y": 450.0, "radius": 300.0, "texture": "swatch:t:rows",
                        "turn": 33.0, "size": 90.0},
                       {"brush": "texture", "x": 1300.0, "y": 500.0, "radius": 350.0, "texture": "swatch:t:plain",
                        "size": 70.0, "edge": "hard"},
                       {"brush": "texture", "x": 900.0, "y": 300.0, "radius": 200.0, "texture": "file:rb.png",
                        "turn": -120.0, "size": 50.0})
        swatches = {**SWATCHES, "swatch:t:rows": ROWS, "swatch:t:plain": PLAIN}  # (mirrored, turned, both)
        grids = gp.paint_strokes(two_colour_store(), BOUNDS, made, swatches=swatches)
        with mock.patch.object(gp, "whole_arrays", lambda: None):
            pixels = gp.paint_strokes(two_colour_store(), BOUNDS, made, swatches=swatches)
        self.assertEqual(sorted(grids), sorted(pixels))
        for i in pixels:
            self.assertEqual(grids[i], pixels[i], i)

    def test_turn_in_the_file(self):
        item = {"brush": "texture", "x": 1.0, "y": 2.0, "radius": 3.0, "texture": "swatch:dday:wheat", "turn": 154.08}
        made = parse_strokes([item])
        self.assertEqual(made[0].turn, 154.08)
        import tomllib
        self.assertEqual(parse_strokes(tomllib.loads(strokes_toml(made))["stroke"]), made)
        with self.assertRaises(BrushError):
            parse_strokes([{"brush": "paint", "x": 1.0, "y": 1.0, "radius": 1.0, "colour": "#000000", "turn": 5.0}])

    def test_the_palette_in_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.toml"
            path.write_text('[themes]\ndday = "D-Day"\n\n[[swatch]]\ntheme = "dday"\nname = "wheat"\nlabel = "Wheat"\n'
                            'map = "M04_Cotentin"\nx = 100.0\ny = 200.0\nside = 8192.0\nfacing = 154.08\n'
                            'kind = "rows"\nwhy = "a field"\n', encoding="utf-8")
            got = gt.palette(path)
            self.assertEqual(list(got), ["swatch:dday:wheat"])
            w = got["swatch:dday:wheat"]
            self.assertEqual((w.label, w.theme_label, w.map, w.side, w.facing, w.kind),
                             ("Wheat", "D-Day", "M04_Cotentin", 8192.0, 154.08, "rows"))
            lib = gt.Library(swatches=got)
            self.assertEqual(lib.period_of("swatch:dday:wheat"), 8192.0)
            with self.assertRaises(gt.TextureError):
                lib.swatch("swatch:dday:wheat", 64)  # its map isn't there
            with self.assertRaises(gt.TextureError):
                lib.period_of("swatch:dday:sand")
            for bad in ('theme = "other"', 'kind = "dots"', "side = 0.0", 'name = "Wheat!"'):
                key = bad.split(" ")[0]
                text = path.read_text(encoding="utf-8")
                lines = [ln for ln in text.splitlines() if not ln.startswith(key + " ")]
                (Path(tmp) / "bad.toml").write_text("\n".join(lines + [bad]) + "\n", encoding="utf-8")
                with self.assertRaises(gt.TextureError, msg=bad):
                    gt.palette(Path(tmp) / "bad.toml")

    def test_a_patch_turned_to_its_rows(self):
        """map_patch: the map's picture read turned, so the way `facing` points runs along the patch's columns."""
        import rusemod.groundpaint as gp
        import rusemod.tmst as tm

        def picture(_store, _bounds, _level, _cache):
            return lambda x, y: (int(x / 40.0) % 256, int(y / 40.0) % 256, 0)  # red grows along x, green along y
        with mock.patch.object(gp, "_picture_sampler", picture), \
                mock.patch.object(gp, "map_bounds", lambda _m: (0.0, 0.0, 20000.0, 20000.0)), \
                mock.patch.object(tm, "Tmst", lambda *_a: None):
            n, px = gt.map_patch(lambda _m: b"x", 5000.0, 5000.0, 1600.0, 90.0, 16)
        self.assertEqual(n, 16)
        red = [[px[4 * (j * n + i)] for i in range(n)] for j in range(n)]
        green = [[px[4 * (j * n + i) + 1] for i in range(n)] for j in range(n)]
        self.assertTrue(all(len(set(row)) <= 2 for row in red))   # along its columns' way: map +y, red the same
        self.assertGreater(green[0][-1] - green[0][0], 30)          # ...and green growing
        self.assertGreater(red[0][0] - red[-1][0], 30)               # across: map -x
        self.assertEqual({px[4 * k + 3] for k in range(n * n)}, {255})


class Masks(unittest.TestCase):
    """Brushes that are pictures (rusemod.brushmask): five masks, read in each stroke's own frame, the same sums pixel
    by pixel and on whole grids."""

    def test_the_masks(self):
        from rusemod import brushmask as bm
        self.assertEqual(bm.MASKS, ("noise", "splatter", "ragged", "tufts", "ridge"))
        for name in bm.MASKS:
            m = bm.make(name)
            self.assertEqual(len(m), bm.SIZE * bm.SIZE, name)
            self.assertLess(min(m), 40, name)      # each lets nothing through somewhere...
            self.assertGreater(max(m), 215, name)  # ...and (nearly) all somewhere else
            bm._made.pop(name)
            self.assertEqual(bm.make(name), m, name)  # made the same again (fixed seeds)
        share = {n: sum(bm.make(n)) / (255 * bm.SIZE * bm.SIZE) for n in bm.MASKS}
        self.assertLess(share["splatter"], 0.5)   # drops on bare ground
        self.assertEqual((bm.reach_scale(1.0), bm.reach_scale(0.0)), (1.0, 1.0 / (bm.RAG_IN * bm.RAG_IN)))
        for ax, ay in bm.TURNS:   # each turning a whole length
            self.assertAlmostEqual(ax * ax + ay * ay, 1.0, places=15)
        with self.assertRaises(ValueError):
            bm.make("dots")

    def test_read_in_the_stroke_s_own_frame(self):
        from rusemod import brushmask as bm
        from rusemod.brush import Stroke
        data = bm.make("splatter")
        s = Stroke("paint", 1000.0, 2000.0, 320.0, colour="#000000", shape="square", dx=0.0, dy=2.0, mask="splatter")
        self.assertEqual(bm.frame(s), (1000.0, 2000.0, 0.0, 1.0, 640.0))
        # a value's middle (10 + 0.5 columns along dx, dy from the frame's corner; 5 + 0.5 rows across) reads it alone
        for i, j in ((10, 5), (0, 0), (63, 63), (31, 40)):
            u, v = (i + 0.5) / 64 * 640.0 - 320.0, (j + 0.5) / 64 * 640.0 - 320.0
            x, y = 1000.0 + u * 0.0 - v * 1.0, 2000.0 + u * 1.0 + v * 0.0
            self.assertAlmostEqual(bm.mask_at(s, x, y), data[j * 64 + i] / 255.0, places=9, msg=(i, j))
        # repeating: a whole width further on reads the same
        self.assertAlmostEqual(bm.mask_at(s, 1000.0, 2000.0 + 640.0), bm.mask_at(s, 1000.0, 2000.0), places=9)
        dab = Stroke("paint", 12345.6, -789.0, 50.0, colour="#000000", mask="noise")
        self.assertIn(bm.frame(dab)[2:4], bm.TURNS)   # a round dab: one of the turnings, by where it is
        turned = {bm.frame(Stroke("paint", 997.0 * k, 0.0, 50.0, colour="#000000", mask="noise"))[2:4]
                  for k in range(40)}
        self.assertGreater(len(turned), 6)   # dabs along a drag turned many ways

    def test_the_same_with_and_without_numpy(self):
        import rusemod.groundpaint as gp
        if gp.whole_arrays() is None:
            self.skipTest("numpy isn't here: paint_strokes paints pixel by pixel alone")
        made = strokes({"brush": "paint", "x": 500.0, "y": 450.0, "radius": 300.0, "colour": "#c8aa6e", "mask": "noise"},
                       {"brush": "paint", "x": 1300.0, "y": 500.0, "radius": 350.0, "colour": "#202080", "edge": "hard",
                        "shape": "square", "dx": 0.3, "dy": 1.0, "mask": "splatter"},
                       {"brush": "texture", "x": 900.0, "y": 300.0, "radius": 200.0, "texture": "file:rb.png",
                        "mask": "ragged", "weight": 0.8},
                       {"brush": "paint", "x": 200.0, "y": 700.0, "radius": 90.0, "colour": "#ffffff", "shape": "line",
                        "x2": 900.0, "y2": 800.0, "mask": "ridge"},
                       {"brush": "paint", "x": 1700.0, "y": 300.0, "radius": 1.2, "colour": "#00ff00", "mask": "tufts"})
        grids = gp.paint_strokes(two_colour_store(), BOUNDS, made, swatches=SWATCHES)
        with mock.patch.object(gp, "whole_arrays", lambda: None):
            pixels = gp.paint_strokes(two_colour_store(), BOUNDS, made, swatches=SWATCHES)
        self.assertEqual(sorted(grids), sorted(pixels))
        for i in pixels:
            self.assertEqual(grids[i], pixels[i], i)

    def test_a_splattered_patch_leaves_ground_between_its_drops(self):
        from rusemod.groundpaint import paint_strokes
        s = two_colour_store()
        plain = Tmst(*s.rebuild(paint_strokes(s, BOUNDS, strokes(
            {"brush": "paint", "x": 300.0, "y": 250.0, "radius": 120.0, "colour": "#ff0000", "edge": "hard"}))))
        s = two_colour_store()
        drops = Tmst(*s.rebuild(paint_strokes(s, BOUNDS, strokes(
            {"brush": "paint", "x": 300.0, "y": 250.0, "radius": 120.0, "colour": "#ff0000", "edge": "hard",
             "mask": "splatter"}))))
        spots = [(300.0 + dx, 250.0 + dy) for dx in range(-60, 61, 6) for dy in range(-60, 61, 6)]
        red = [near(pixel(drops, drops.tiles[3], x, y), (255, 0, 0), 30) for x, y in spots]
        self.assertTrue(all(near(pixel(plain, plain.tiles[3], x, y), (255, 0, 0), 12) for x, y in spots))
        self.assertTrue(any(red) and not all(red), sum(red))

    def test_a_ragged_patch_is_whole_inside_and_torn_round_its_edge(self):
        """ragged sets how far the stroke reaches (RAG_IN to all of its radius): its middle is all paint, its outline
        goes in and out between RAG_IN and the radius."""
        from rusemod import brushmask as bm
        from rusemod.groundpaint import paint_strokes
        s = two_colour_store()
        dab = {"brush": "paint", "x": 500.0, "y": 500.0, "radius": 300.0, "colour": "#ff0000", "edge": "hard",
               "mask": "ragged"}
        got = Tmst(*s.rebuild(paint_strokes(s, BOUNDS, strokes(dab))))

        def red(x, y):   # in the finest tile over the point
            tile = next(t for t in got.tiles if t.level == 0 and got.area(t)[0] <= x / 1000 < got.area(t)[2]
                        and got.area(t)[1] <= y / 1000 < got.area(t)[3])
            return near(pixel(got, tile, x, y), (255, 0, 0), 40)
        import math as m
        inside = [red(500.0 + r * m.cos(a / 10), 500.0 + r * m.sin(a / 10)) for a in range(63)
                  for r in (20.0, 80.0, 0.45 * bm.RAG_IN * 300.0)]
        self.assertTrue(all(inside))
        ring = [red(500.0 + 0.8 * 300.0 * m.cos(a / 10), 500.0 + 0.8 * 300.0 * m.sin(a / 10)) for a in range(63)]
        self.assertTrue(any(ring) and not all(ring), sum(ring))   # torn: in and out round it

    def test_in_the_file(self):
        import tomllib
        item = {"brush": "texture", "x": 1.0, "y": 2.0, "radius": 3.0, "texture": "swatch:dday:grass", "mask": "tufts"}
        made = parse_strokes([item])
        self.assertEqual(made[0].mask, "tufts")
        self.assertEqual(parse_strokes(tomllib.loads(strokes_toml(made))["stroke"]), made)
        self.assertNotIn("mask", strokes_toml(parse_strokes([{**item, "mask": ""}])))
        for bad, says in (({**item, "mask": "dots"}, "must be one of"),
                          ({"brush": "raise", "x": 1.0, "y": 1.0, "radius": 1.0, "height": 5.0, "mask": "noise"},
                           "is for the paint")):
            with self.assertRaises(BrushError) as caught:
                parse_strokes([bad])
            self.assertIn(says, str(caught.exception))

    def test_a_speckled_edge(self):
        """dither: on the finest level each pixel takes the stroke whole or not at all, more of them nearer its middle
        (a chance that follows the fall-off); a coarser level blends as before; the same with and without numpy."""
        import rusemod.groundpaint as gp
        from rusemod import brushmask as bm
        dab = {"brush": "paint", "x": 500.0, "y": 500.0, "radius": 300.0, "colour": "#ff0000", "dither": True}
        made = strokes(dab)[0]
        fine, coarse = 2.0, bm.DITHER_MOST * 1.01
        ring = [gp._coverage(made, 500.0 + 200.0 * math.cos(a / 50), 500.0 + 200.0 * math.sin(a / 50), fine, fine)
                for a in range(314)]
        self.assertEqual(set(ring), {0.0, 1.0})   # all or nothing
        share = sum(ring) / len(ring)
        plain = strokes({**dab, "dither": False})[0]
        want = plain.strength_at(700.0, 500.0)
        self.assertLess(abs(share - want), 0.1, (share, want))   # as many as the fall-off's share
        x, y = 690.0, 505.0   # coarser: blended, as before
        self.assertEqual(gp._coverage(made, x, y, coarse, coarse), gp._coverage(plain, x, y, coarse, coarse))
        if gp.whole_arrays() is None:
            self.skipTest("numpy isn't here: paint_strokes paints pixel by pixel alone")
        many = strokes({**dab, "edge": "hard"}, {"brush": "texture", "x": 1300.0, "y": 500.0, "radius": 350.0,
                                                 "texture": "file:rb.png", "dither": True, "mask": "ragged"},
                       {"brush": "paint", "x": 900.0, "y": 300.0, "radius": 1.3, "colour": "#00ff00", "dither": True})
        grids = gp.paint_strokes(two_colour_store(), BOUNDS, many, swatches=SWATCHES)
        with mock.patch.object(gp, "whole_arrays", lambda: None):
            pixels = gp.paint_strokes(two_colour_store(), BOUNDS, many, swatches=SWATCHES)
        self.assertEqual(sorted(grids), sorted(pixels))
        for i in pixels:
            self.assertEqual(grids[i], pixels[i], i)
        import tomllib
        self.assertEqual(parse_strokes(tomllib.loads(strokes_toml([made]))["stroke"]), [made])
        with self.assertRaises(BrushError):
            parse_strokes([{"brush": "raise", "x": 1.0, "y": 1.0, "radius": 1.0, "height": 5.0, "dither": True}])

    def test_the_page_gets_the_masks(self):
        import base64
        from rusemod import brushmask as bm
        from ruse_studio.api import StudioApi
        with tempfile.TemporaryDirectory() as tmp:
            got = StudioApi(home=Path(tmp, "home"), game_dir=Path(tmp, "game")).brush_masks()
        self.assertEqual((got["size"], list(got["masks"])), (bm.SIZE, list(bm.MASKS)))
        self.assertEqual(base64.b64decode(got["masks"]["ridge"]), bm.make("ridge"))
        self.assertEqual([tuple(t) for t in got["turns"]], list(bm.TURNS))


class EncodedOnce(unittest.TestCase):
    """paintnp.encoded: a block's pixels encoded once for all the tiles a worker paints, the same 8 bytes as encoding
    it again."""

    def test_a_block_is_encoded_once(self):
        import rusemod.groundpaint as gp
        if gp.whole_arrays() is None:
            self.skipTest("numpy isn't here: paint_strokes paints pixel by pixel alone")
        from rusemod import dxtnp, paintnp
        import numpy as np
        a, b, c = bytes(range(48)), bytes(range(100, 148)), bytes([7] * 48)
        paintnp._DONE.clear()
        calls = []
        real = dxtnp.encode_blocks
        with mock.patch.object(dxtnp, "encode_blocks", lambda rows: calls.append(len(rows)) or real(rows)):
            one = paintnp.encoded([a, b, a])
            two = paintnp.encoded([b, c, a])
        self.assertEqual(calls, [2, 1])   # a and b the first time; then only c is new
        self.assertEqual(one, b"".join(real(np.frombuffer(p, dtype=np.uint8).reshape(1, 48)) for p in (a, b, a)))
        self.assertEqual(two, b"".join(real(np.frombuffer(p, dtype=np.uint8).reshape(1, 48)) for p in (b, c, a)))
        with mock.patch.object(paintnp, "DONE_MOST", 2):   # full: forgotten, but the tile's own still come out
            three = paintnp.encoded([c, bytes([9] * 48)])
        self.assertEqual(three[:8], two[8:16])
        self.assertLessEqual(len(paintnp._DONE), 3)


class Library(unittest.TestCase):
    def test_a_pictures_real_size_from_its_sidecar(self):
        from rusemod.dxt import png_bytes
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "beach.png"
            path.write_bytes(png_bytes(bytes([200, 180, 120] * 64), 8, 8))
            lib = gt.Library(files={"file:mod/beach.png": path})  # (the build's name: file:<mod>/...)
            self.assertEqual(lib.period_of("file:mod/beach.png"), gt.FILE_PERIOD)
            (Path(tmp) / "beach.toml").write_text(gt.credit_toml(4.0, {"licence": "CC0"}), encoding="utf-8")
            self.assertEqual(lib.period_of("file:mod/beach.png"), 4.0 * gt.METRE)
            self.assertEqual(lib.swatch("file:mod/beach.png", 8).period, 4.0 * gt.METRE)
            (Path(tmp) / "beach.toml").write_text("metres = -3\nlicence = 'CC0'\n", encoding="utf-8")
            self.assertEqual(gt.read_credit(path), {"licence": "CC0"})  # a size that isn't one is left out
            (Path(tmp) / "beach.toml").write_text("not = [toml", encoding="utf-8")
            self.assertEqual(lib.period_of("file:mod/beach.png"), gt.FILE_PERIOD)

    def test_the_mods_own_picture(self):
        from rusemod.dxt import png_bytes
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sand.png"
            rgb = bytes(v for k in range(20 * 12) for v in (200, 180, 120 + k % 3))
            path.write_bytes(png_bytes(rgb, 20, 12))
            lib = gt.Library(files={"file:mod/sand.png": path})  # (the build names it with its mod: file:<mod>/...)
            s = lib.swatch("file:mod/sand.png", 64)
            self.assertEqual((s.period, s.mips[0][0]), (gt.FILE_PERIOD, 8))  # its middle square, 8 a side
            self.assertTrue(near(s.mips[-1][1][:3], (200, 180, 121), 2))
            with self.assertRaises(gt.TextureError):
                lib.swatch("file:mod/none.png", 64)

    def test_the_game_isnt_there(self):
        with self.assertRaises(gt.TextureError):
            gt.Library().swatch("game:france/stickers01/paille", 64)
        with self.assertRaises(gt.TextureError):
            gt.Library().swatch("map:Valley:1:2", 64)


if __name__ == "__main__":
    unittest.main()
