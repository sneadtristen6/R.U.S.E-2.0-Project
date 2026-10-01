"""The AI's map grid: the end of a map's `mapinfo.win` (after the four buffers), kept up to date with a mod's edits.

Layout of the tail (little-endian): u32 record size (28), u32 count, count × 28-byte records (empty on every shipped
map but testia), u32 the grid's length, then the grid: u32 W, u32 H, W × H cells of 2 bytes (row by row, y growing
with the map's y; a cell is 26,000 map units square from the map's corner at (0, 0)), padded to 4 bytes; anything
after it is kept. A cell's bytes:

- byte 1, bits 0-6: clearance, 0-127: how far the cell is from ground the AI treats as blocked (127 reads as 8 cells,
  but the shipped values reach it about 4 cells out);
- byte 1, bit 7: forest;
- byte 0, bit 7: a tree-line spot (a forest cell at a wood's edge): where the AI sends its defenders and hides its
  recon. Other bits are 0.

The game reads the grid as it is, so after a mod's cover paints, blocks, bridges or water the AI kept defending the
old tree lines and ignored new woods. Eugen's grids came from a tool that isn't in the game; the rules here were fitted
to the 34 shipped grids by DomesticNukes and his Claude (2026-09-30), and a grid rebuilt by them played the same as
the shipped one in the game:

1. lay the AI grid over the cover grid's finest cells (square cells, `max(width, height) / R` from the cover grid's
   corner) and count each AI cell's share of cover cells with each layer, and how many there are;
2. forest: more than 25% of its cells have the cover layer (0x08);
3. blocked: more than 70% have the "AI: blocked" layer (0x04), or the cover grid doesn't reach it (off the map);
   and, after a change to the vehicles' movement graph, a cell whose share of ground vehicles can stand on (4 × 4
   points) fell below half counts as blocked, one whose share rose to half or more as not blocked;
4. clearance: the distance in cells to the nearest blocked cell, at most 4, as round(d / 4 × 127);
5. tree line: a forest cell with a cell that isn't forest among its 8 neighbours.

Rebuilding a whole grid adds up to 1.8 times Eugen's tree-line spots (his are a stricter subset), so `refresh` keeps
the shipped values everywhere the edits didn't reach: a cell's forest bit where the rule's answer for it changed with
its cover share, tree lines where a forest bit that changed moves the rule's answer for a cell or its neighbours,
clearance where the rule's answer changed because the blocked cells did. An unchanged map keeps its grid byte for
byte."""
from __future__ import annotations

import hashlib
import math
import struct

CELL = 26000.0        # map units an AI grid cell is across
FOREST_SHARE = 0.25   # more than this share of cover cells: a forest cell
BLOCKED_SHARE = 0.70  # more than this share of "AI: blocked" cells: a blocked cell
CAP = 4               # clearance stops growing this many cells from a blocked cell
COVER_BIT, BLOCKED_BIT = 0x08, 0x04


class AiGridError(ValueError):
    pass


class Tail:
    """The records table and the AI grid after mapinfo.win's buffers."""

    def __init__(self, tail: bytes):
        if len(tail) < 12:
            raise AiGridError("the AI grid is missing")
        self.recsize, self.count = struct.unpack_from("<II", tail, 0)
        at = 8 + self.count * 28
        if at + 4 > len(tail):
            raise AiGridError("the AI grid's records run past the file")
        self.records = tail[8:at]
        length = struct.unpack_from("<I", tail, at)[0]
        grid = tail[at + 4:at + 4 + length]
        if len(grid) != length or length < 8:
            raise AiGridError("the AI grid is shorter than it says")
        self.w, self.h = struct.unpack_from("<II", grid, 0)
        if 8 + 2 * self.w * self.h > length:
            raise AiGridError("the AI grid is smaller than its size")
        self.cells = bytearray(grid[8:8 + 2 * self.w * self.h])
        self.pad = grid[8 + 2 * self.w * self.h:]
        self.extra = tail[at + 4 + length:]

    def to_bytes(self) -> bytes:
        grid = struct.pack("<II", self.w, self.h) + bytes(self.cells) + self.pad
        return struct.pack("<II", self.recsize, self.count) + self.records + struct.pack("<I", len(grid)) + grid \
            + self.extra

    def forest(self, c: int) -> bool:
        return bool(self.cells[2 * c + 1] & 0x80)

    def clearance(self, c: int) -> int:
        return self.cells[2 * c + 1] & 0x7F


def _shares(win: bytes, w: int, h: int) -> tuple[list[float], list[float], list[int]]:
    """Each AI cell's share of cover cells with the cover layer, with the "AI: blocked" layer, and how many cover cells
    it has (rule 1)."""
    from .cover import grid
    g = grid(win)
    r, cells = g["size"], g["cells"]
    ox, oy, sx, sy = g["box"]
    cs = max(sx, sy) / r
    column = [math.floor((ox + (x + 0.5) * cs) / CELL) for x in range(r)]
    runs = []  # (AI column, first cover column, end) along a row
    x = 0
    while x < r:
        end = x
        while end < r and column[end] == column[x]:
            end += 1
        if 0 <= column[x] < w:
            runs.append((column[x], x, end))
        x = end
    forest, blocked, count = [0] * (w * h), [0] * (w * h), [0] * (w * h)
    cover_of = bytes(1 if b & COVER_BIT else 0 for b in range(256))
    blocked_of = bytes(1 if b & BLOCKED_BIT else 0 for b in range(256))
    for y in range(r):
        j = math.floor((oy + (y + 0.5) * cs) / CELL)
        if not 0 <= j < h:
            continue
        row = cells[y * r:(y + 1) * r]
        for i, x0, x1 in runs:
            c = j * w + i
            part = row[x0:x1]
            forest[c] += part.translate(cover_of).count(1)
            blocked[c] += part.translate(blocked_of).count(1)
            count[c] += x1 - x0
    return ([f / n if n else 0.0 for f, n in zip(forest, count)], [b / n if n else 0.0 for b, n in zip(blocked, count)],
            count)


def _coverage(buf: bytes, w: int, h: int, samples: int = 4) -> list[float] | None:
    """Each AI cell's share of `samples` × `samples` points vehicles can stand on (nav.Graph.walkable), or None when
    the graph can't be read."""
    from .nav import Graph, NavError
    try:
        g = Graph.read(buf)
    except (NavError, struct.error):
        return None
    out = []
    for j in range(h):
        for i in range(w):
            hit = sum(g.walkable((i + (a + 0.5) / samples) * CELL, (j + (b + 0.5) / samples) * CELL)
                      for a in range(samples) for b in range(samples))
            out.append(hit / (samples * samples))
    return out


def _clearance(blocked: list[bool], w: int, h: int) -> list[int]:
    """Rule 4 for every cell."""
    out = []
    for j in range(h):
        for i in range(w):
            d = CAP
            for b in range(max(0, j - CAP), min(h, j + CAP + 1)):
                for a in range(max(0, i - CAP), min(w, i + CAP + 1)):
                    if blocked[b * w + a]:
                        d = min(d, math.hypot(a - i, b - j))
            out.append(round(d / CAP * 127))
    return out


def _tree_line(forest: list[bool], w: int, h: int, c: int) -> bool:
    """Rule 5 for cell c (cells off the grid aren't counted as open)."""
    if not forest[c]:
        return False
    i, j = c % w, c // w
    return any(not forest[b * w + a] for b in range(max(0, j - 1), min(h, j + 2))
               for a in range(max(0, i - 1), min(w, i + 2)) if (a, b) != (i, j))


def _split(win: bytes):
    from ruse_mod_engine import sdb
    parts = sdb.split_mapinfo(win)
    if not parts:
        raise AiGridError("not a mapinfo.win")
    return parts


def refresh(before: bytes, after: bytes) -> tuple[bytes, list[str]]:
    """`after` (a mapinfo.win a mod's edits made from `before`) with its AI grid following those edits, the shipped
    values kept wherever they didn't reach (see the module's notes); and what changed. A grid that can't be read is
    left as it is, with a note."""
    head, bufs, tail = _split(after)
    _h0, old_bufs, old_tail = _split(before)
    if bufs[2:] == old_bufs[2:]:
        return after, []  # neither the cover grid nor the vehicles' movement changed: nothing the grid follows
    try:
        grid = Tail(tail)
        Tail(old_tail)
    except (AiGridError, struct.error) as exc:
        return after, [f"the AI grid couldn't be read ({exc}), so it was left as it was"]
    w, h, n = grid.w, grid.h, grid.w * grid.h
    try:
        f0, b0, n0 = _shares(before, w, h)
        f1, b1, n1 = _shares(after, w, h) if bufs[3] != old_bufs[3] else (f0, b0, n0)
    except (ValueError, KeyError, IndexError, struct.error) as exc:
        return after, [f"the cover grid couldn't be read for the AI grid ({exc}), so it was left as it was"]
    cov0 = cov1 = None
    if bufs[2] != old_bufs[2]:
        cov0, cov1 = _coverage(old_bufs[2], w, h), _coverage(bufs[2], w, h)
        if cov0 is None or cov1 is None:
            cov0 = cov1 = None
    # forest: where the rule's answer changed with the cell's cover share
    forest0 = [grid.forest(c) for c in range(n)]
    forest1 = list(forest0)
    for c in range(n):
        if (f0[c] > FOREST_SHARE) != (f1[c] > FOREST_SHARE):
            forest1[c] = f1[c] > FOREST_SHARE
    flipped = [c for c in range(n) if forest1[c] != forest0[c]]
    redone = len(flipped)
    lines = 0
    near = {b * w + a for c in flipped for b in range(max(0, c // w - 1), min(h, c // w + 2))
            for a in range(max(0, c % w - 1), min(w, c % w + 2))}
    for c in sorted(near):
        was, now = _tree_line(forest0, w, h, c), _tree_line(forest1, w, h, c)
        if c in flipped or was != now:
            bit = 0x80 if now else 0
            if grid.cells[2 * c] & 0x80 != bit:
                grid.cells[2 * c] = (grid.cells[2 * c] & 0x7F) | bit
                lines += 1
        grid.cells[2 * c + 1] = (grid.cells[2 * c + 1] & 0x7F) | (0x80 if forest1[c] else 0)

    # clearance: where the blocked cells' change moves the rule's answer
    def blocked(shares, counts, cov_old=None, cov_new=None) -> list[bool]:
        out = []
        for c in range(n):
            b = counts[c] == 0 or shares[c] > BLOCKED_SHARE
            if cov_old is not None:
                if cov_old[c] >= 0.5 > cov_new[c]:
                    b = True
                elif cov_old[c] < 0.5 <= cov_new[c]:
                    b = False
            out.append(b)
        return out
    cleared = 0
    was, now = blocked(b0, n0), blocked(b1, n1, cov0, cov1)
    if was != now:
        c0, c1 = _clearance(was, w, h), _clearance(now, w, h)
        for c in range(n):
            if c0[c] != c1[c] and grid.clearance(c) != c1[c]:
                grid.cells[2 * c + 1] = (grid.cells[2 * c + 1] & 0x80) | c1[c]
                cleared += 1
    new_tail = grid.to_bytes()
    if new_tail == tail:
        return after, []
    out = bytearray(head + b"".join(struct.pack("<I", len(b)) + b for b in bufs) + new_tail)
    out[8:24] = hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + bytes(out[24:])).digest()
    return bytes(out), [f"AI grid: forest redone on {redone} cell(s), tree-line spots on {lines}, clearance on "
                        f"{cleared}"]
