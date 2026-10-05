"""A map's own pictures in the menus (rusemod.menupicture, map.toml picture, wide_picture, start_dots): any PNG cut to
each picture's shape from its middle, scaled, and written as the game's own menu pictures are (D-Day's: 640 x 360
and 680 x 200, one level of DXT5, packed)."""
import unittest

from rusemod import menupicture
from rusemod.dxt import decode_rgba, png_bytes
from rusemod.menupicture import PictureError, fitted, pictures
from rusemod.tmst import Tgv, zipo_unpack


def picture(w: int, h: int, colour) -> bytes:
    """A w x h RGBA picture: `colour(x, y)` -> (r, g, b, a)."""
    return bytes(v for y in range(h) for x in range(w) for v in colour(x, y))


class Fitting(unittest.TestCase):
    def test_a_wide_picture_loses_its_sides(self):
        # 8 x 2 (4:1) cut to 2:1: its middle 4 columns (green) are kept, the red and blue sides go
        colours = [(255, 0, 0, 255)] * 2 + [(0, 255, 0, 255)] * 4 + [(0, 0, 255, 255)] * 2
        out = fitted(picture(8, 2, lambda x, y: colours[x]), 8, 2, 2, 1)
        self.assertEqual(bytes(out), bytes((0, 255, 0, 255)) * 2)

    def test_each_pixel_the_mean_of_those_it_covers(self):
        src = picture(4, 4, lambda x, y: (x * 80, y * 80, 0, 255))
        out = fitted(src, 4, 4, 2, 2)
        self.assertEqual(list(out), [40, 40, 0, 255, 200, 40, 0, 255, 40, 200, 0, 255, 200, 200, 0, 255])

    def test_a_smaller_picture_is_spread(self):
        out = fitted(picture(1, 1, lambda x, y: (10, 20, 30, 255)), 1, 1, 4, 2)
        self.assertEqual(bytes(out), bytes((10, 20, 30, 255)) * 8)

    def test_see_through_pixels_dont_darken_the_edges_they_meet(self):
        """A 3D map's background is see-through: its colour (black here) stays out of the slab's edge."""
        out = fitted(picture(2, 2, lambda x, y: (0, 0, 0, 0) if x == 0 else (250, 200, 100, 255)), 2, 2, 1, 1)
        self.assertEqual(list(out), [250, 200, 100, 128])
        self.assertEqual(list(fitted(bytes(16), 2, 2, 1, 1)), [0, 0, 0, 0])

    def test_a_solid_picture_as_the_plain_mean(self):
        """Every pixel solid: each new pixel the plain mean of the colours it covers, rounded as before the alpha
        weighting (the pictures already made come out the same)."""
        import random
        rnd = random.Random(7)
        for w, h, tw, th in ((7, 5, 3, 2), (13, 11, 4, 3), (9, 9, 2, 5), (16, 9, 5, 3)):
            src = bytes(v for _ in range(w * h) for v in (rnd.randrange(256), rnd.randrange(256),
                                                           rnd.randrange(256), 255))
            out = fitted(src, w, h, tw, th)
            if w * th > h * tw:
                cw, ch = max(1, h * tw // th), h
            else:
                cw, ch = w, max(1, w * th // tw)
            x0, y0 = (w - cw) // 2, (h - ch) // 2
            for ty in range(th):
                r0 = y0 + ty * ch // th
                r1 = max(r0 + 1, y0 + (ty + 1) * ch // th)
                for tx in range(tw):
                    c0 = x0 + tx * cw // tw
                    c1 = max(c0 + 1, x0 + (tx + 1) * cw // tw)
                    n = (r1 - r0) * (c1 - c0)
                    for k in range(3):
                        total = sum(src[(r * w + c) * 4 + k] for r in range(r0, r1) for c in range(c0, c1))
                        self.assertEqual(out[(ty * tw + tx) * 4 + k], (total + n // 2) // n, (w, h, tx, ty, k))
                    self.assertEqual(out[(ty * tw + tx) * 4 + 3], 255)


class TheGamesPictures(unittest.TestCase):
    def test_both_pictures_in_the_games_form(self):
        sky = picture(64, 36, lambda x, y: (40, 90, 200, 255) if y >= 18 else (200, 220, 255, 255))
        got = pictures(png_bytes(sky, 64, 36, channels=4))
        self.assertEqual(set(got), {"Minimap", "Minimap2"})
        for stem, w, h in (("Minimap", 640, 360), ("Minimap2", 680, 200)):
            t = Tgv(got[stem])
            self.assertEqual((t.width, t.height, t.format, len(t.mips), t.codec), (w, h, "DXT5_LIN", 1, "ZIPO"))
            px = decode_rgba(zipo_unpack(t.payload(0)), w, h, "DXT5")
            top, bottom = px[(4 * w + w // 2) * 4:(4 * w + w // 2) * 4 + 4], px[((h - 4) * w + 8) * 4:((h - 4) * w + 8) * 4 + 4]
            self.assertLessEqual(max(abs(a - b) for a, b in zip(top, (200, 220, 255, 255))), 8)   # sky above
            self.assertLessEqual(max(abs(a - b) for a, b in zip(bottom, (40, 90, 200, 255))), 8)  # sea below

    def test_the_same_bytes_every_time(self):
        src = png_bytes(picture(30, 20, lambda x, y: (x * 8, y * 12, 99, 255)), 30, 20, channels=4)
        self.assertEqual(pictures(src), pictures(src))

    def test_not_a_picture(self):
        with self.assertRaises(PictureError):
            pictures(b"not a png")
        big = menupicture.LARGEST + 1
        with self.assertRaisesRegex(PictureError, "at most"):
            pictures(png_bytes(bytes(big * 4), big, 1, channels=4))

    def test_the_wide_one_from_a_picture_of_its_own(self):
        """map.toml wide_picture: the wide one (the 3D map) from its own PNG; the big one from `picture`."""
        red = png_bytes(picture(16, 9, lambda x, y: (220, 20, 20, 255)), 16, 9, channels=4)
        blue = png_bytes(picture(34, 10, lambda x, y: (20, 20, 220, 255)), 34, 10, channels=4)
        got = pictures(red, blue)
        for stem, w, h, want in (("Minimap", 640, 360, (220, 20, 20)), ("Minimap2", 680, 200, (20, 20, 220))):
            px = decode_rgba(zipo_unpack(Tgv(got[stem]).payload(0)), w, h, "DXT5")
            self.assertLessEqual(max(abs(a - b) for a, b in zip(px[:3], want)), 8, stem)
        self.assertEqual(set(pictures(None, blue)), {"Minimap2"})   # the big one stays the game's own
        self.assertEqual(pictures(None, None), {})

    def test_the_starting_points_drawn_on_the_wide_one(self):
        """start_dots: the build draws a white dot where each starting point is (rusemod.menudraw)."""
        from rusemod.menudraw import slab_png, to_picture
        got = menupicture.dotted_wide(slab_png("land"), [(0.3, 0.6)])
        t = Tgv(got)
        self.assertEqual((t.width, t.height, t.format), (680, 200, "DXT5_LIN"))
        px = decode_rgba(zipo_unpack(t.payload(0)), 680, 200, "DXT5")
        x, y = (int(v) for v in to_picture(0.3, 0.6))
        self.assertGreaterEqual(min(px[(y * 680 + x) * 4:(y * 680 + x) * 4 + 3]), 240)

    def test_map_toml_says_it(self):
        from rusemod.menupicture import member_of, picture_names, start_dots_of
        self.assertEqual(picture_names({"picture": "menu.png", "wide_picture": "Menu-Wide.PNG"}, "m"),
                         ("menu.png", "Menu-Wide.PNG"))
        self.assertEqual(picture_names({}, "m"), (None, None))
        for bad in ({"wide_picture": "x.jpg"}, {"picture": "../x.png"}, {"wide_picture": 3}):
            with self.subTest(bad=bad), self.assertRaisesRegex(PictureError, "must name a PNG"):
                picture_names(bad, "m")
        self.assertTrue(start_dots_of({"start_dots": True}, "m", "menu-wide.png"))
        self.assertFalse(start_dots_of({}, "m", None))
        with self.assertRaisesRegex(PictureError, "true or false"):
            start_dots_of({"start_dots": "yes"}, "m", "menu-wide.png")
        with self.assertRaisesRegex(PictureError, "the game's own have their dots drawn in"):
            start_dots_of({"start_dots": True}, "m", None)
        self.assertEqual(member_of("DataDir:\\Test\\map\\M04_cotentin\\minimap_dday.png"),
                         "gen\\test\\map\\m04_cotentin\\minimap_dday.tgv")
        self.assertIsNone(member_of("GameData:\\x.png"))


if __name__ == "__main__":
    unittest.main()
