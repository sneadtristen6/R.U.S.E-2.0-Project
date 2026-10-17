"""tgu1np's bit-stream walk compiled with Numba (Map Paint's speed, 2026-10-16): one sub-band's values (tgu1._Reader
.value, `want` times: Rice or Exp-Golomb codes, then the zigzag back to signed), read bit after bit in compiled code.
Reading D-Day's own ground tiles was over half of the heaviest map mod's paint time (paint_profile.py: 15.4 of 28 s,
most in tgu1np._stream). The same values and the same refusals as tgu1np._stream's numpy walk (a value starting
past the stream, no 1 to end its zeros, bits past the stream, an Exp-Golomb value over its most bits, a stream not
used up exactly); test_tgu1nb checks both on real tiles. Without Numba (`values` is None), tgu1np walks with numpy."""
from __future__ import annotations

import os

try:
    if os.environ.get("RUSE_NO_NUMBA"):   # a worker program of the build's pools (mend._pool: why)
        raise ImportError("RUSE_NO_NUMBA")
    import numba
    from .numpy2 import np
except ImportError:   # (numpy without numba, or neither: tgu1np's own walk)
    numba = None

values = None

if numba is not None:
    @numba.njit(cache=True, nogil=True)
    def _values(data, nbits, mode, want, most_bits):
        out = np.empty(want, np.int64)
        pos = 0
        for v in range(want):
            if pos >= nbits:
                return False, out
            q = 0
            while pos < nbits and ((data[pos >> 3] >> (pos & 7)) & 1) == 0:
                q += 1
                pos += 1
            if pos >= nbits:   # (no 1 to end the zeros)
                return False, out
            pos += 1
            if mode >= 8:      # Rice: q, then k bits
                k = mode - 8
            else:              # Exp-Golomb: mode + q bits
                k = mode + q
                if k > most_bits:
                    return False, out
            if pos + k > nbits:
                return False, out
            x = 0
            for i in range(k):   # (the first bit the lowest)
                x |= ((data[(pos + i) >> 3] >> ((pos + i) & 7)) & 1) << i
            pos += k
            if mode >= 8:
                u = (q << k) | x
            else:
                u = (1 << k) + x - (1 << mode)
            out[v] = (u >> 1) ^ -(u & 1)
        return pos == nbits, out

    values = _values
