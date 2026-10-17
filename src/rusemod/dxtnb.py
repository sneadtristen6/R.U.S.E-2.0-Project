"""dxtnp's heavy sums compiled with Numba (Map Paint's speed, the owner's choice 2026-10-16: Numba, the code stays
Python): each block's two end colours (dxtnp._ends) and, for each of its nine pairs of end colours, the index word
and the squared error (dxtnp._tried), worked out block after block in compiled code instead of on numpy arrays.
The same sums in the same order (the colour axis's sums pixel after pixel, the same eight passes, the same rounding,
the first of equal palette colours), so dxtnp picks among them as before and every block comes out the same bytes
(test_dxt: random and real blocks, both ways). Without Numba (`ends_and_tries` is None), dxtnp uses numpy."""
from __future__ import annotations

import os

try:
    if os.environ.get("RUSE_NO_NUMBA"):   # a worker program of the build's pools (mend._pool: why)
        raise ImportError("RUSE_NO_NUMBA")
    import numba
    from .numpy2 import np
except ImportError:   # (numpy without numba, or neither: dxtnp's own numpy sums)
    numba = None

ends_and_tries = None

if numba is not None:
    @numba.njit(cache=True, nogil=True)
    def _ends_and_tries(px, nudges):
        n = px.shape[0]
        pairs = nudges.shape[0]
        a_out = np.empty(n, np.int64)
        b_out = np.empty(n, np.int64)
        left = np.zeros(n, np.bool_)
        c0s = np.zeros((n, pairs), np.int64)
        c1s = np.zeros((n, pairs), np.int64)
        words = np.zeros((n, pairs), np.int64)
        errs = np.zeros((n, pairs), np.int64)
        tried = np.zeros((n, pairs), np.bool_)
        for k in range(n):
            sr = 0
            sg = 0
            sb = 0
            for i in range(16):
                sr += px[k, i, 0]
                sg += px[k, i, 1]
                sb += px[k, i, 2]
            mr = sr / 16
            mg = sg / 16
            mb = sb / 16
            c00 = 0.0
            c01 = 0.0
            c02 = 0.0
            c11 = 0.0
            c12 = 0.0
            c22 = 0.0
            for i in range(16):   # (added pixel after pixel, as dxt._endpoints)
                dr = px[k, i, 0] - mr
                dg = px[k, i, 1] - mg
                db = px[k, i, 2] - mb
                c00 = c00 + dr * dr
                c01 = c01 + dr * dg
                c02 = c02 + dr * db
                c11 = c11 + dg * dg
                c12 = c12 + dg * db
                c22 = c22 + db * db
            ax = 1.0
            ay = 1.0
            az = 1.0
            for _ in range(8):
                nx = c00 * ax + c01 * ay + c02 * az
                ny = c01 * ax + c11 * ay + c12 * az
                nz = c02 * ax + c12 * ay + c22 * az
                norm = max(max(abs(nx), abs(ny)), abs(nz))
                if norm == 0.0:
                    norm = 1.0
                ax = nx / norm
                ay = ny / norm
                az = nz / norm
            left[k] = ax == 0.0 and ay == 0.0 and az == 0.0
            hi = -np.inf
            lo = np.inf
            for i in range(16):
                t = (px[k, i, 0] - mr) * ax + (px[k, i, 1] - mg) * ay + (px[k, i, 2] - mb) * az
                if t > hi:
                    hi = t
                if t < lo:
                    lo = t
            square = ax * ax + ay * ay + az * az
            if square == 0.0:
                square = 1.0
            hi = hi / square
            lo = lo / square
            ends = np.empty(2, np.int64)
            for e in range(2):
                f = hi if e == 0 else lo
                ch = np.empty(3, np.int64)
                ch[0] = int(min(max(np.rint(mr + f * ax), 0.0), 255.0))
                ch[1] = int(min(max(np.rint(mg + f * ay), 0.0), 255.0))
                ch[2] = int(min(max(np.rint(mb + f * az), 0.0), 255.0))
                ends[e] = ((ch[0] * 31 + 127) // 255) << 11 | ((ch[1] * 63 + 127) // 255) << 5 | (
                    (ch[2] * 31 + 127) // 255)
            a = ends[0]
            b = ends[1]
            a_out[k] = a
            b_out[k] = b
            for j in range(pairs):
                ca = a + nudges[j, 0]
                cb = b + nudges[j, 1]
                if ca < 0 or ca > 0xFFFF or cb < 0 or cb > 0xFFFF or ca == cb:
                    continue
                tried[k, j] = True
                c0 = max(ca, cb)
                c1 = min(ca, cb)
                c0s[k, j] = c0
                c1s[k, j] = c1
                r0 = (c0 >> 11) & 31
                g0 = (c0 >> 5) & 63
                b0 = c0 & 31
                r1 = (c1 >> 11) & 31
                g1 = (c1 >> 5) & 63
                b1 = c1 & 31
                p0r = (r0 << 3) | (r0 >> 2)
                p0g = (g0 << 2) | (g0 >> 4)
                p0b = (b0 << 3) | (b0 >> 2)
                p1r = (r1 << 3) | (r1 >> 2)
                p1g = (g1 << 2) | (g1 >> 4)
                p1b = (b1 << 3) | (b1 >> 2)
                pr = (p0r, p1r, (2 * p0r + p1r + 1) // 3, (p0r + 2 * p1r + 1) // 3)
                pg = (p0g, p1g, (2 * p0g + p1g + 1) // 3, (p0g + 2 * p1g + 1) // 3)
                pb = (p0b, p1b, (2 * p0b + p1b + 1) // 3, (p0b + 2 * p1b + 1) // 3)
                word = 0
                err = 0
                for i in range(16):
                    r = px[k, i, 0]
                    g = px[k, i, 1]
                    bl = px[k, i, 2]
                    best = 0
                    be = (r - pr[0]) ** 2 + (g - pg[0]) ** 2 + (bl - pb[0]) ** 2
                    for q in range(1, 4):
                        e = (r - pr[q]) ** 2 + (g - pg[q]) ** 2 + (bl - pb[q]) ** 2
                        if e < be:   # (the first of equals, as dxt.best_indices)
                            be = e
                            best = q
                    word |= best << (2 * i)
                    err += be
                words[k, j] = word
                errs[k, j] = err
        return a_out, b_out, left, c0s, c1s, words, errs, tried

    ends_and_tries = _ends_and_tries
