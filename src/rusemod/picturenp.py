"""Pictures on whole arrays (numpy): rusemod.png's filters undone and its palette looked up, and
rusemod.unitlook.halve's averages, for every pixel at once instead of one at a time, so a picture comes out the same
bytes many times sooner.
png.py and unitlook.py ask for this module through their whole_arrays() and keep their own loops: they are what every
piece here is checked against (tests/test_picturenp.py), and what runs without numpy.

How the same bytes are kept: every sum here is of whole numbers (bytes), which numpy adds as Python does.
  - a filter's sum is kept to a byte as the loops keep it (& 0xFF; Sub's running sum in bytes, which wrap the same);
    Average's halving is the same shift, Paeth's choice the same three comparisons in the same order;
  - a row filtered with Sub (or not at all) needs only itself, so those rows are done together; the other filters take
    the decoded pixel left of each, above it and above-left, so the picture is done one anti-diagonal (x + y the same)
    at a time: each pixel of a diagonal needs only the two diagonals before it, which are done;
  - a halved pixel is (s + 2) // 4 of its 2 x 2 square, the last row or column taken again where the picture is odd.
A function here gives None for what it leaves to the loops: data that ends early, a filter no PNG has, a palette index
past its palette, a picture shorter than its size says (the loops give their own answer or error)."""
from __future__ import annotations

from .numpy2 import np

_ROWS = 256  # rows of a halved picture worked out together (a 4096 x 4096 picture's sums stay small)


def unfilter(raw: bytes, width: int, height: int, bpp: int):
    """png._unfilter: the scanlines without their filters (a bytearray, as the loops give), or None."""
    stride = width * bpp
    if width <= 0 or height <= 0 or bpp <= 0 or len(raw) < height * (stride + 1):
        return None
    rows = np.frombuffer(raw, dtype=np.uint8, count=height * (stride + 1)).reshape(height, stride + 1)
    kinds = rows[:, 0]
    if int(kinds.max()) > 4:
        return None
    if int(kinds.max()) <= 1:   # None and Sub only: each row on its own
        out = rows[:, 1:].reshape(height, width, bpp).copy()
        sub = kinds == 1
        if sub.all():   # (in bytes: the running sum & 0xFF)
            np.cumsum(out, axis=1, dtype=np.uint8, out=out)
        elif sub.any():
            out[sub] = np.cumsum(out[sub], axis=1, dtype=np.uint8)
        return bytearray(out)       # (its bytes, copied once)
    return bytearray(_diagonals(rows, kinds, width, height, bpp))


def _predict(kind: int, a, b, c):
    """What a filter adds to a byte: None 0, Sub the byte left (a), Up the one above (b), Average their mean rounded
    down, Paeth whichever of a, b and c (above-left) is nearest a + b - c (a first, then b, on a tie)."""
    if kind == 0:
        return np.zeros_like(a)
    if kind == 1:
        return a
    if kind == 2:
        return b
    if kind == 3:
        return (a + b) >> 1
    bc, ac = b - c, a - c                         # p - a, p - b; p - c is their sum (p = a + b - c)
    pa, pb, pc = np.abs(bc), np.abs(ac), np.abs(ac + bc)
    return np.where((pa <= pb) & (pa <= pc), a, np.where(pb <= pc, b, c))


def _diagonals(rows, kinds, width: int, height: int, bpp: int):
    """Every row's filter undone, one anti-diagonal at a time: (height, width, bpp) bytes. A diagonal is kept by row
    ("lane"): lane y + 1 holds row y's pixel on it, lane 0 the row of 0 above the picture, and a lane whose pixel
    would lie left of the picture holds 0, so pixel (y, x) finds the one left of it at lane y + 1 of the diagonal
    before, the one above at lane y of the diagonal before, and the one above-left at lane y of the one before that."""
    line = width * bpp + 1              # a row of the data: its filter byte, then its pixels
    raw = rows.reshape(-1)
    out = np.empty((height, width, bpp), dtype=np.uint8)
    lanes = height + 1
    kind = kinds.astype(np.int64)
    counts = np.bincount(kind, minlength=5)
    base = int(np.argmax(counts))       # every pixel takes the commonest filter's prediction, then the rows of the
    others = {q: (kind == q)[:, None] for q in range(5) if counts[q] and q != base}  # others take their own
    before = np.zeros((lanes, bpp), dtype=np.int16)     # the diagonal before last
    last = np.zeros((lanes, bpp), dtype=np.int16)       # the diagonal before
    for d in range(width + height - 1):
        y0, y1 = max(0, d - width + 1), min(height - 1, d)
        n = y1 - y0 + 1
        a, b, c = last[y0 + 1:y1 + 2], last[y0:y1 + 1], before[y0:y1 + 1]     # left, above, above-left
        pred = _predict(base, a, b, c)
        for q, rows_q in others.items():
            pred = np.where(rows_q[y0:y1 + 1], _predict(q, a, b, c), pred)
        now = np.zeros((lanes, bpp), dtype=np.int16)
        got = now[y0 + 1:y1 + 2]
        np.add(pred, np.ndarray((n, bpp), dtype=np.uint8, buffer=raw, offset=y0 * line + 1 + (d - y0) * bpp,
                                strides=(line - bpp, 1)), out=got)
        got &= 0xFF
        np.ndarray((n, bpp), dtype=np.uint8, buffer=out, offset=(y0 * width + d - y0) * bpp,
                   strides=((width - 1) * bpp, 1))[...] = got
        before, last = last, now
    return out


def palette_rgba(pixels, palette: bytes, alpha: bytes):
    """png.read_png's palette look-up: every pixel's RGBA (bytes), its alpha the tRNS entry or 255. None when a pixel
    names an entry past the palette."""
    index = np.frombuffer(pixels, dtype=np.uint8)
    entries = len(palette) // 3
    if len(index) and int(index.max()) >= entries:
        return None
    colours = np.frombuffer(palette, dtype=np.uint8, count=entries * 3).reshape(entries, 3)
    alphas = np.full(256, 255, dtype=np.uint8)
    given = min(256, len(alpha))
    alphas[:given] = np.frombuffer(alpha, dtype=np.uint8, count=given)
    out = np.empty((len(index), 4), dtype=np.uint8)
    out[:, :3] = colours[index]
    out[:, 3] = alphas[index]
    return out.tobytes()


def halve(px, w: int, h: int, channels: int = 4):
    """unitlook.halve: a picture at half the size, each pixel (s + 2) // 4 of its 2 x 2 square's sum s (bytes), or
    None for a picture shorter than w x h."""
    if w <= 0 or h <= 0 or channels <= 0 or len(px) < w * h * channels:
        return None
    nw, nh = max(1, w // 2), max(1, h // 2)
    a = np.frombuffer(px, dtype=np.uint8, count=w * h * channels).reshape(h, w, channels)
    # the square's second row and column: 2y + 1 and 2x + 1, or the last where the picture is 1 across
    r1, c1 = (slice(1, 2 * nh, 2) if h > 1 else slice(0, 1)), (slice(1, 2 * nw, 2) if w > 1 else slice(0, 1))
    r0, c0 = slice(0, 2 * nh, 2), slice(0, 2 * nw, 2)
    out = np.empty((nh, nw, channels), dtype=np.uint8)
    for y in range(0, nh, _ROWS):     # (a band of rows at a time)
        top, bottom = a[r0][y:y + _ROWS], a[r1][y:y + _ROWS]
        s = top[:, c0].astype(np.uint16) + top[:, c1] + bottom[:, c0] + bottom[:, c1] + 2
        out[y:y + len(s)] = s // 4
    return out.tobytes()
