"""A new map's own pictures in the menus (rusemod.menupicture, map.toml picture): any PNG cut to each picture's shape
from its middle, scaled, and written as the game's own menu pictures are (D-Day's: 640 x 360 and 680 x 200, one
level of DXT5, packed)."""
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


if __name__ == "__main__":
    unittest.main()
