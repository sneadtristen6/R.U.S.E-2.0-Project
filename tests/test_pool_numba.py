"""The build's worker programs start without Numba (rusemod.mend._pool: with it a paint worker lost its call queue's
semaphore before its first job, 2026-10-16), the program that starts them keeping what it has: dxtnb and tgu1nb
give the same bytes either way (test_dxt, test_tgu1nb)."""
import os
import unittest

from rusemod import dxtnb, mend, tgu1nb


def _start() -> None:
    pass


def _numba_there(_n):
    from rusemod import dxtnb as d
    from rusemod import tgu1nb as t
    return os.environ.get(mend.NO_NUMBA), d.ends_and_tries is not None, t.values is not None


class Pool(unittest.TestCase):
    def test_workers_without_numba_this_program_as_it_was(self):
        had = (dxtnb.ends_and_tries is not None, tgu1nb.values is not None)
        before = os.environ.get(mend.NO_NUMBA)
        with mend._pool(_start, (), 1) as pool:
            got = list(pool.map(_numba_there, [0]))
        self.assertEqual(got, [("1", False, False)])
        self.assertEqual(os.environ.get(mend.NO_NUMBA), before)   # put back as it was
        self.assertEqual((dxtnb.ends_and_tries is not None, tgu1nb.values is not None), had)


if __name__ == "__main__":
    unittest.main()
