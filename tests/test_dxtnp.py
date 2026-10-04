"""rusemod.dxtnp: many DXT1 blocks packed at once come out as dxt.encode_block packs each, byte for byte (made-up
blocks, no game files). Skipped without numpy: the apps carry it, the plain code doesn't need it."""
import random
import unittest

from rusemod import dxt

try:
    import numpy as np
    from rusemod import dxtnp
except ImportError:
    np = dxtnp = None


def made_up(rng, n):
    """Blocks of every kind the packer treats differently, 16 RGB pixels each, as rows of 48 values."""
    rows = []
    for k in range(n):
        kind = k % 9
        if kind == 0:    # one flat colour
            px = [[rng.randrange(256) for _ in range(3)]] * 16
        elif kind == 1:  # two colours
            a, b = [[rng.randrange(256) for _ in range(3)] for _ in range(2)]
            px = [a if rng.random() < 0.5 else b for _ in range(16)]
        elif kind == 2:  # a slope from one colour to another
            a, b = [[rng.randrange(256) for _ in range(3)] for _ in range(2)]
            px = [[(a[c] * (15 - i) + b[c] * i) // 15 for c in range(3)] for i in range(16)]
        elif kind == 3:  # noise
            px = [[rng.randrange(256) for _ in range(3)] for _ in range(16)]
        elif kind == 4:  # greys
            px = [[v] * 3 for v in (rng.randrange(256) for _ in range(16))]
        elif kind == 5:  # red against blue: the colour axis shrinks to nothing on the first try
            px = [[200, 30, 30] if i % 2 else [30, 30, 200] for i in range(16)]
            if rng.random() < 0.3:
                px[rng.randrange(16)] = [rng.randrange(256) for _ in range(3)]
        elif kind == 6:  # near black or white: the nudged end colours run off the scale
            base = rng.choice((0, 255))
            px = [[min(255, max(0, base + rng.randrange(-6, 7))) for _ in range(3)] for _ in range(16)]
        elif kind == 7:  # a field's grain: close colours, many equally good pairs
            base = [rng.randrange(256) for _ in range(3)]
            px = [[min(255, max(0, base[c] + rng.randrange(-9, 10))) for c in range(3)] for _ in range(16)]
        else:            # flat but for one pixel
            p = [rng.randrange(256) for _ in range(3)]
            px = [p] * 16
            px[rng.randrange(16)] = [min(255, p[0] + rng.randrange(1, 4)), p[1], p[2]]
        rows.append([v for p in px for v in p])
    return rows


@unittest.skipIf(dxtnp is None, "numpy isn't here")
class ManyBlocks(unittest.TestCase):
    def test_each_block_as_encode_block_packs_it(self):
        rows = made_up(random.Random(7), 5400)
        together = dxtnp.encode_blocks(np.array(rows, dtype=np.uint8))
        self.assertEqual(len(together), 8 * len(rows))
        for i, row in enumerate(rows):
            one = dxt.encode_block([tuple(row[3 * k:3 * k + 3]) for k in range(16)])
            self.assertEqual(together[8 * i:8 * i + 8], one, (i, i % 9, row))

    def test_none_and_one(self):
        self.assertEqual(dxtnp.encode_blocks(np.zeros((0, 48), dtype=np.uint8)), b"")
        row = [9, 200, 77] * 16
        self.assertEqual(dxtnp.encode_blocks(np.array([row], dtype=np.uint8)),
                         dxt.encode_block([(9, 200, 77)] * 16))


if __name__ == "__main__":
    unittest.main()
