"""DXT1 blocks and TGU1 texture payloads, on made-up pictures (no game files)."""
import struct
import unittest

from rusemod import dxt, tgu1


def gradient(w, h):
    return bytes(v for y in range(h) for x in range(w) for v in ((x * 8) % 256, (y * 8) % 256, 128))


class Dxt1(unittest.TestCase):
    def test_solid_block_and_palette(self):
        red = dxt.pack565(255, 0, 0)
        self.assertEqual(red, 0xF800)
        self.assertEqual(dxt.unpack565(red), (255, 0, 0))
        block = struct.pack("<HHI", red, red, 0)
        self.assertEqual(set(dxt.block_pixels(block)), {(255, 0, 0)})
        self.assertEqual(bytes(dxt.decode(block, 4, 4)[:6]), bytes([255, 0, 0, 255, 0, 0]))

    def test_encode_then_decode_stays_close(self):
        w = h = 16
        rgb = gradient(w, h)
        blocks = dxt.encode(rgb, w, h)
        self.assertEqual(len(blocks), (w // 4) * (h // 4) * 8)
        back = dxt.decode(blocks, w, h)
        self.assertLess(sum(abs(a - b) for a, b in zip(rgb, back)) / len(rgb), 6)

    def test_two_colours_square_to_grey(self):
        # red against blue: their axis (1, 0, -1) is square to the search's first guess (1, 1, 1); both ends came
        # out as the mean, a purple-blue, before (found 2026-10-04 by the model importer's test)
        for one, two in (((200, 10, 10), (10, 10, 200)), ((0, 200, 0), (100, 0, 100))):
            pixels = [one] * 4 + [two] * 12
            back = dxt.block_pixels(dxt.encode_block(pixels))
            for want, got in zip(pixels, back):
                self.assertLessEqual(max(abs(a - b) for a, b in zip(want, got)), 8, (want, got))

    def test_png_writer(self):
        png = dxt.png_bytes(bytes([10, 20, 30]) * 4, 2, 2)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", png[16:24]), (2, 2))


class Tgu1(unittest.TestCase):
    def test_header_and_round_trip(self):
        w = h = 32
        blocks = dxt.encode(gradient(w, h), w, h)
        payload = tgu1.encode(blocks, w, h)
        self.assertEqual(payload[:4], b"TGU1")
        head, body = tgu1.inflate(payload)
        self.assertEqual((head.version, head.width, head.height, head.flags), (5, w // 4, h // 4, tgu1.FLAG_CODED))
        self.assertEqual(head.block_count, (w // 4) * (h // 4))
        self.assertEqual(len(body), head.body_size)
        decoded = tgu1.decode(payload)
        self.assertEqual(len(decoded), len(blocks))
        self.assertEqual(tgu1.decode(payload), decoded)  # the same every time
        before, after = dxt.decode(blocks, w, h), dxt.decode(decoded, w, h)
        self.assertLess(sum(abs(a - b) for a, b in zip(before, after)) / len(before), 4)  # lossy, but close

    def test_not_a_payload(self):
        with self.assertRaises(ValueError):
            tgu1.decode(b"ZIPO" + bytes(40))


def coded(w, h, count, alpha):
    """A coded payload of w x h blocks whose banks hold only zero coefficients, `count` blocks with selectors."""
    tiles, zero = (w // 4) * (h // 4), [0] * 16
    body = struct.pack("<I", 0) + b"".join(tgu1.pack_bank([zero] * tiles) for _ in range(6))
    body += tgu1.pack_bank([zero] * count, raw=[])
    if alpha:
        body += tgu1.pack_bank([zero] * tiles) * 2 + tgu1.pack_bank([zero] * count, raw=[])
    flags = tgu1.FLAG_CODED | (tgu1.FLAG_ALPHA if alpha else 0)
    return tgu1.pack_payload(tgu1.Header(5, w, h, 80, 40, count, flags), body)


class Tgu1Alpha(unittest.TestCase):
    """DXT5 payloads (unit textures): the plain ones, the alpha banks, and the header's block count."""

    def test_plain_payload_is_its_blocks(self):
        for flags, size in ((tgu1.FLAG_ALPHA, 16), (0, 8)):
            blocks = bytes(range(256))[:2 * 2 * size]
            payload = tgu1.Header(5, 2, 2, 80, 40, 4, flags, 0).pack()[:tgu1.PLAIN_HEADER] + blocks
            self.assertEqual(tgu1.decode(payload), blocks)
            with self.assertRaises(ValueError):
                tgu1.decode(payload[:-1])

    def test_alpha_pair(self):
        self.assertEqual(tgu1.alpha_pair(200, 50), (200, 150))     # the second image: how far below alpha 0
        self.assertEqual(tgu1.alpha_pair(300, -2), (255, 254))     # clamped, then never equal
        self.assertEqual(tgu1.alpha_pair(100, 0), (100, 99))
        self.assertEqual(tgu1.alpha_pair(0, 0), (1, 0))
        self.assertEqual(tgu1.alpha_pair(-5, 3), (1, 0))
        self.assertEqual(tgu1.alpha_pair(40, 90), (40, 0))         # alpha 1 stops at 0
        self.assertEqual(tgu1.alpha_pair(0, 90), (1, 0))
        self.assertEqual(tgu1.alpha_pair(100, 0, version=2), (100, 100))

    def test_alpha_word(self):
        self.assertEqual(tgu1.alpha_word([-4] * 16), 0)            # position 0: alpha 0 itself, index 0
        self.assertEqual(tgu1.alpha_word([3] * 16), sum(1 << 3 * i for i in range(16)))  # position 7: alpha 1
        self.assertEqual(tgu1.alpha_word([40000] * 16), 0)         # 16-bit: saturated to 32767, + 4 wraps below 0
        word = tgu1.alpha_word([-9, -3, -2, -1, 0, 1, 2, 3] * 2)
        self.assertEqual([(word >> 3 * i) & 7 for i in range(8)], [0, 2, 3, 4, 5, 6, 7, 1])

    def test_coded_dxt5_blocks_and_block_count(self):
        w = h = 8
        for count in (w * h, 40):
            d = tgu1.decode_full(coded(w, h, count, alpha=True))
            self.assertEqual(len(d.dxt), w * h * 16)
            five = sum(5 << 3 * i for i in range(16))              # value 0 -> position 4 -> index 5
            for i in range(w * h):
                block = d.dxt[16 * i:16 * i + 16]
                if i < count:
                    a0, a1, lo, hi = struct.unpack_from("<BBHI", block)
                    self.assertEqual((a0, a1, lo | hi << 16), (1, 0, five))
                    self.assertEqual(block[8:], struct.pack("<HHI", d.ends[i][0], d.ends[i][1], d.selectors[i]))
                else:
                    self.assertEqual(block, bytes(16))             # past the block count: zero

    def test_coded_dxt1_block_count(self):
        d = tgu1.decode_full(coded(8, 8, 24, alpha=False))
        self.assertEqual(len(d.selectors), 24)
        self.assertEqual(d.dxt[24 * 8:], bytes(40 * 8))

    def test_alpha_flag_without_alpha_banks(self):
        payload = bytearray(coded(4, 4, 16, alpha=False))
        struct.pack_into("<I", payload, 0x1C, tgu1.FLAG_CODED | tgu1.FLAG_ALPHA)
        with self.assertRaises(ValueError):
            tgu1.decode(bytes(payload))


def speckled(w, h, seed):
    """A made-up picture with fields, a slope and grain, so its payload uses many coefficients and long codes."""
    out = bytearray()
    v = seed
    for y in range(h):
        for x in range(w):
            v = (v * 1103515245 + 12345) & 0x7FFFFFFF
            grain = (v >> 16) % 23
            out += bytes(((x * 5 + grain) % 256, (40 + (y // 8) * 37 + grain * 2) % 256, (x * y // 7 + seed) % 256))
    return bytes(out)


@unittest.skipIf(tgu1.whole_arrays() is None, "numpy isn't here: tgu1.decode uses decode_full alone")
class Tgu1WholeArrays(unittest.TestCase):
    """rusemod.tgu1np: the same blocks as decode_full, byte for byte, or None for what it leaves to it."""

    def test_the_same_blocks_as_value_by_value(self):
        fast = tgu1.whole_arrays()
        for w, h, seed in ((32, 32, 1), (64, 32, 7), (128, 128, 3), (16, 48, 11)):
            for picture in (gradient(w, h), speckled(w, h, seed)):
                payload = tgu1.encode(dxt.encode(picture, w, h), w, h)
                got = fast.decode(payload)
                self.assertIsNotNone(got, (w, h, seed))
                self.assertEqual(got, tgu1.decode_full(payload).dxt, (w, h, seed))
                self.assertEqual(tgu1.decode(payload), got)

    def test_blocks_past_the_block_count_are_zero_as_there(self):
        fast = tgu1.whole_arrays()
        for count in (64, 24, 0):
            payload = coded(8, 8, count, alpha=False)
            self.assertEqual(fast.decode(payload), tgu1.decode_full(payload).dxt, count)

    def test_what_it_doesnt_read_is_left_to_decode_full(self):
        fast = tgu1.whole_arrays()
        self.assertIsNone(fast.decode(coded(8, 8, 64, alpha=True)))          # DXT5
        raw = struct.pack("<I", 0) + b"".join(tgu1.pack_bank([[0] * 16] * 4) for _ in range(6))
        raw += tgu1.pack_bank([[0] * 16] * 60, raw=[5, 6, 7, 8])               # raw selector words
        self.assertIsNone(fast.decode(tgu1.pack_payload(tgu1.Header(5, 8, 8, 80, 40, 64, tgu1.FLAG_CODED), raw)))
        cut = bytearray(coded(8, 8, 64, alpha=False))
        struct.pack_into("<I", cut, 0x18, 65)                                 # more blocks than the picture has
        self.assertIsNone(fast.decode(bytes(cut)))
        self.assertIsNone(fast.decode(b"ZIPO" + bytes(40)))                   # (decode_full says what's wrong)
        with self.assertRaises(ValueError):
            tgu1.decode(b"ZIPO" + bytes(40))


if __name__ == "__main__":
    unittest.main()
