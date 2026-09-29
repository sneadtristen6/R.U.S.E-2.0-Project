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


if __name__ == "__main__":
    unittest.main()
