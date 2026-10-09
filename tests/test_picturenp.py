"""rusemod.picturenp (numpy) against rusemod.png's and rusemod.unitlook's own loops, byte for byte: a PNG's rows with
every filter undone (every pixel size, odd sizes, a lone row or column), whole PNG files of every kind read, a palette
looked up, and pictures halved. The loops are the reference: whole arrays read a downloaded model's 2048 x 2048 photos
many times sooner (2026-10-08), and their pixels must not change for it."""
import contextlib
import random
import struct
import unittest
import zlib
from pathlib import Path
from unittest import mock

from rusemod import png, unitlook

try:
    import numpy  # noqa: F401
    from rusemod import picturenp
except ImportError:
    picturenp = None


@contextlib.contextmanager
def loops():
    """png's and unitlook's own loops from here on: whole arrays kept away."""
    with mock.patch.object(png, "whole_arrays", lambda: None), \
            mock.patch.object(unitlook, "whole_arrays", lambda: None):
        yield


def filtered(rnd, width: int, height: int, bpp: int, kinds: tuple) -> bytes:
    """A PNG's data before it is zipped: rows of random bytes, each behind a filter byte from `kinds` (any bytes undo
    to some picture, so every carry and every Paeth choice comes up)."""
    out = bytearray()
    for _ in range(height):
        out.append(rnd.choice(kinds))
        out += bytes(rnd.randrange(256) for _ in range(width * bpp))
    return bytes(out)


def chunk(tag: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)


def png_file(width: int, height: int, depth: int, ctype: int, data: bytes, palette=None, trns=None) -> bytes:
    out = png.SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, ctype, 0, 0, 0))
    if palette is not None:
        out += chunk(b"PLTE", palette)
    if trns is not None:
        out += chunk(b"tRNS", trns)
    return out + chunk(b"IDAT", zlib.compress(data)) + chunk(b"IEND", b"")


@unittest.skipIf(picturenp is None, "numpy isn't here: png's and unitlook's loops do all of it")
class WholeArrays(unittest.TestCase):

    def test_numpy_comes_through_numpy2(self):
        text = Path(picturenp.__file__).read_text(encoding="utf-8")
        self.assertIn("from .numpy2 import np", text)
        self.assertNotIn("import numpy", text)

    def test_every_filter_on_every_pixel_size(self):
        rnd = random.Random(1)
        for width, height in ((1, 1), (1, 7), (7, 1), (5, 3), (16, 16), (33, 20), (3, 40)):
            for bpp in (1, 2, 3, 4, 6, 8):
                for kinds in ((0,), (1,), (0, 1), (2,), (3,), (4,), (0, 1, 2, 3, 4), (4, 4, 4, 1, 2), (3, 0)):
                    raw = filtered(rnd, width, height, bpp, kinds)
                    with loops():
                        want = png._unfilter(raw, width, height, bpp)
                    got = picturenp.unfilter(raw, width, height, bpp)
                    self.assertIsInstance(got, bytearray)
                    self.assertEqual(got, want, (width, height, bpp, kinds))
                    self.assertEqual(png._unfilter(raw + b"left over", width, height, bpp), want)
        for width, height, bpp in ((257, 130, 4), (130, 257, 3)):     # long diagonals, both ways round
            raw = filtered(rnd, width, height, bpp, (4, 4, 4, 4, 3, 2, 1, 0))
            with loops():
                want = png._unfilter(raw, width, height, bpp)
            self.assertEqual(picturenp.unfilter(raw, width, height, bpp), want)

    def test_what_is_left_to_the_loops(self):
        """Data that ends early and a filter no PNG has: the loops say what is wrong."""
        rnd = random.Random(2)
        raw = filtered(rnd, 8, 4, 3, (0, 1, 2, 3, 4))
        self.assertIsNone(picturenp.unfilter(raw[:-1], 8, 4, 3))
        with self.assertRaisesRegex(png.PngError, "ends early"):
            png._unfilter(raw[:-1], 8, 4, 3)
        bad = bytearray(raw)
        bad[2 * (8 * 3 + 1)] = 5
        self.assertIsNone(picturenp.unfilter(bytes(bad), 8, 4, 3))
        with self.assertRaisesRegex(png.PngError, "unknown PNG filter 5"):
            png._unfilter(bytes(bad), 8, 4, 3)
        self.assertIsNone(picturenp.palette_rgba(bytearray([0, 3, 4]), bytes(12), b""))  # (entry 4 of 4)

    def test_pictures_of_every_kind_read_the_same(self):
        rnd = random.Random(3)
        for ctype, depth in ((0, 8), (0, 16), (2, 8), (2, 16), (3, 8), (4, 8), (4, 16), (6, 8), (6, 16)):
            for w, h in ((13, 9), (1, 5), (64, 3)):
                bpp = png.CHANNELS[ctype] * depth // 8
                raw = filtered(rnd, w, h, bpp, (0, 1, 2, 3, 4))
                palette = trns = None
                if ctype == 3:
                    palette = bytes(rnd.randrange(256) for _ in range(256 * 3))
                    trns = bytes(rnd.randrange(256) for _ in range(100))      # (the rest: 255)
                data = png_file(w, h, depth, ctype, raw, palette, trns)
                with loops():
                    want = png.read_png(data)
                self.assertEqual(png.read_png(data), want, (ctype, depth, w, h))
        small = bytes(rnd.randrange(16) for _ in range(40))                # a 16-colour palette, no tRNS
        data = png_file(8, 5, 8, 3, b"".join(b"\0" + small[8 * y:8 * y + 8] for y in range(5)),
                        bytes(rnd.randrange(256) for _ in range(48)))
        with loops():
            want = png.read_png(data)
        self.assertEqual(png.read_png(data), want)

    def test_halved(self):
        rnd = random.Random(4)
        for w, h in ((1, 1), (1, 6), (6, 1), (2, 2), (3, 3), (7, 4), (8, 8), (33, 17), (600, 2), (2, 520),
                     (514, 600)):
            for channels in (1, 3, 4):
                px = bytes(rnd.randrange(256) for _ in range(w * h * channels))
                with loops():
                    want = unitlook.halve(px, w, h, channels)
                self.assertEqual(picturenp.halve(px, w, h, channels), want, (w, h, channels))
                self.assertEqual(unitlook.halve(px, w, h, channels), want)
        self.assertIsNone(picturenp.halve(b"\0" * 11, 2, 2, 3))


if __name__ == "__main__":
    unittest.main()
