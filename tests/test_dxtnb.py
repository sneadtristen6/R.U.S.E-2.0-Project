"""dxtnb: dxtnp's heavy sums compiled with Numba give every block the same bytes as numpy's (and so as dxt's own
one-block encoder): noise, ramps, two colours, nearly flat, and a colour axis square to (1, 1, 1); the quick
encoder too."""
import unittest

from rusemod import dxt, dxtnb


class SameBytes(unittest.TestCase):
    def setUp(self):
        if dxtnb.ends_and_tries is None:
            self.skipTest("Numba isn't here: dxtnp uses numpy")
        import numpy as np
        rng = np.random.default_rng(11)
        n = 400
        kinds = [rng.integers(0, 256, (n, 16, 3)),
                 np.clip(rng.integers(0, 200, (n, 1, 3)) + np.arange(16)[None, :, None] * rng.integers(0, 4, (n, 1, 3)),
                         0, 255),
                 np.take_along_axis(rng.integers(0, 256, (n, 2, 3)),
                                    rng.integers(0, 2, (n, 16))[:, :, None].repeat(3, axis=2), axis=1),
                 np.clip(rng.integers(20, 230, (n, 1, 3)) + rng.integers(-1, 2, (n, 16, 3)), 0, 255)]
        rb = np.zeros((20, 16, 3), dtype=np.int64)
        s = rng.integers(0, 2, (20, 16))
        rb[:, :, 0], rb[:, :, 1], rb[:, :, 2] = 100 + 50 * s, 90, 150 - 50 * s
        kinds.append(rb)
        self.blocks = np.concatenate(kinds).astype(np.uint8).reshape(-1, 48)

    def both(self, encode):
        compiled = encode(self.blocks)
        keep = dxtnb.ends_and_tries
        try:
            dxtnb.ends_and_tries = None
            plain = encode(self.blocks)
        finally:
            dxtnb.ends_and_tries = keep
        return compiled, plain

    def test_the_encoder(self):
        from rusemod import dxtnp
        compiled, plain = self.both(dxtnp.encode_blocks)
        self.assertEqual(compiled, plain)
        for i in range(0, len(self.blocks), 97):
            own = dxt.encode_block([tuple(p) for p in self.blocks[i].reshape(16, 3).tolist()])
            self.assertEqual(compiled[8 * i:8 * i + 8], own, i)

    def test_the_quick_encoder(self):
        from rusemod import dxtnp
        compiled, plain = self.both(dxtnp.encode_blocks_quick)
        self.assertEqual(compiled, plain)


if __name__ == "__main__":
    unittest.main()
