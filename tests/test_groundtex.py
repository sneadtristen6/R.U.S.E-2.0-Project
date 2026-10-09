"""Map Paint's textures (rusemod.groundtex): what names one, how a picture is made to repeat without a seam, its
smaller copies, and the Texture brush's strokes laid on the made-up tile set of test_groundpaint (2 x 1 cells of
1,000 map units), pixel by pixel and on whole grids alike."""
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


class Library(unittest.TestCase):
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
