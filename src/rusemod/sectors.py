"""Sectors over the whole map (maps/<map pack>/scenario.toml `[sectors] whole_map = true`; docs/MOD_FORMAT.md §8):
every place of the map in a sector, each place the map's own sectors leave out going to the sector nearest it.

How it is done, as other map editors make regions (a grid, then outlines traced from it):
  1. the map on a grid of cells (at most MOST_CELLS along its longer side): each cell in the sector the scenario's
     zone map (rusemod.kdt) puts its middle in;
  2. each cell the sectors leave out goes to the sector nearest it, measured exactly to the sectors' outlines on a
     grid COARSE times coarser (a sector's own share of the open map then reaches straight out from its edge);
  3. the borders between sectors (and the map's edge) traced along the cells' sides, as chains from one meeting place
     of three or more to the next, each chain made simpler once (Douglas-Peucker: at most 1.5 cells off on the
     sectors' own borders, 1.5 coarse cells on the new ones) and used by both its sides;
  4. each sector's outline built from its chains; each sector (rusemod.scenario.Zone) made again from its outline,
     drawn the way every shipped sector is (checked on all 1,313 of the 102 shipped scenarios, 2026-10-05), and the
     zone map made again from the same outlines, so the sectors drawn and the ones played agree, and two neighbours
     share one border, point for point.

Not seen in the game yet (2026-10-05): written for the owner's D-Day map, all of it flattened and painted blue."""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from .kdt import Kdt, Q_MASK
from .scenario import Scenario, Zone

LEVEL = 10000.0     # a sector's height in the zone map: its number times this (every shipped zone map)
BAND = 20000.0      # the border band: the inner ring this far inside the outline (the shipped zones' median)
MITER = 2.5         # an inner ring's point at most this many band widths from its outline's point (a sharp corner)
MOST_CELLS = 4096   # the grid: at most this many cells along the map's longer side (D-Day: 3,840 x 2,560, 4 m each)
COARSE = 4          # the nearest-sector fill on cells this many times bigger (16 m on D-Day), exact to the outlines
SIMPLE = 1.5        # a chain is made simpler to at most this many cells off (its own grid's cells: fine or coarse)


class SectorError(ValueError):
    pass


# --- a mod's setting: maps/<map pack>/scenario.toml [sectors] ---


@dataclass(frozen=True)
class Sectors:
    """What a mod does to a map's sectors (scenario.toml `[sectors]`): `whole_map`, every scenario's sectors reach
    over the whole map."""
    whole_map: bool = False


def parse_sectors(table, where: str = "scenario.toml") -> list:
    """A scenario.toml's [sectors] table as rows for the build ([] when it has none)."""
    if table is None:
        return []
    if not isinstance(table, dict):
        raise SectorError(f"{where}: sectors is a table: [sectors] then whole_map = true")
    extra = sorted(set(table) - {"whole_map"})
    if extra:
        raise SectorError(f"{where}: [sectors] has an unknown key {extra[0]!r} (it holds whole_map = true or false)")
    whole = table.get("whole_map", False)
    if not isinstance(whole, bool):
        raise SectorError(f"{where}: [sectors] whole_map is true or false")
    return [Sectors(whole)]


def sectors_toml(setting) -> str:
    """The [sectors] table for a scenario.toml ("" when it does nothing)."""
    if setting is None or not setting.whole_map:
        return ""
    return ("# Every scenario's sectors reach over the whole map: each place the map's sectors leave out goes to the\n"
            "# sector nearest it.\n[sectors]\nwhole_map = true\n")


def whole_map_of(rows: list) -> bool:
    """Whether a map's scenario rows (all the mods', in load order) leave its sectors over the whole map: the last
    mod's [sectors] decides."""
    found = [r for r in rows if isinstance(r, Sectors)]
    return bool(found) and found[-1].whole_map


def map_size(win: bytes) -> tuple[float, float]:
    """A map's width and height (map units) from its movement file (mapinfo.win; D-Day 3,932,160 by 2,621,440)."""
    if len(win) < 48 or win[:8] != b"INFOIA\r\n":
        raise SectorError("not a movement file (mapinfo.win)")
    return struct.unpack_from("<2f", win, 0x28)


def _numpy():
    try:
        from .numpy2 import np
    except ImportError as exc:
        raise SectorError(f"sectors over the whole map need numpy, which this copy of the program doesn't have "
                          f"({exc})") from exc
    return np


@dataclass
class Grid:
    width: float
    height: float
    step: float        # a cell's side (map units, a power of two)
    nx: int
    ny: int

    @classmethod
    def over(cls, width: float, height: float, most: int = MOST_CELLS) -> "Grid":
        if not (width > 0 and height > 0):
            raise SectorError(f"the map's size isn't known ({width} by {height})")
        step = 1.0
        while max(width, height) / step > most:
            step *= 2
        return cls(width, height, step, math.ceil(width / step), math.ceil(height / step))

    def corner(self, ci: int, cj: int) -> tuple[float, float]:
        """The point at corner row `ci`, column `cj` of the cells (x = cj steps, y = ci steps), on the map."""
        return (min(cj * self.step, self.width), min(ci * self.step, self.height))


# --- 1. the map's own sectors on the grid ---


def kdt_labels(kdt: Kdt, g: Grid, numbers, np):
    """Each cell's sector by the zone map (rusemod.kdt): the number of the highest triangle over the cell's middle
    (number = height / LEVEL, rounded), -1 where none is. Only `numbers` count (a triangle at another height is left
    out)."""
    lab = np.full((g.ny, g.nx), -1, np.int32)
    top = np.full((g.ny, g.nx), -np.inf)
    known = set(numbers)
    for s in range(len(kdt.subtrees)):
        pos = [(kdt.to_world(0, p[0]), kdt.to_world(1, p[1]), kdt.to_world(2, p[2])) for p in kdt.positions(s)]
        idx = kdt.indices(s)
        for t in range(0, len(idx) - 2, 3):
            a, b, c = pos[idx[t]], pos[idx[t + 1]], pos[idx[t + 2]]
            z = (a[2] + b[2] + c[2]) / 3
            number = int(math.floor(z / LEVEL + 0.5))
            if number not in known:
                continue
            j0 = max(0, math.ceil(min(a[0], b[0], c[0]) / g.step - 0.5))
            j1 = min(g.nx - 1, math.floor(max(a[0], b[0], c[0]) / g.step - 0.5))
            i0 = max(0, math.ceil(min(a[1], b[1], c[1]) / g.step - 0.5))
            i1 = min(g.ny - 1, math.floor(max(a[1], b[1], c[1]) / g.step - 0.5))
            if j1 < j0 or i1 < i0:
                continue
            xs = (np.arange(j0, j1 + 1) + 0.5) * g.step
            ys = (np.arange(i0, i1 + 1) + 0.5) * g.step
            px, py = np.meshgrid(xs, ys)
            d1 = (px - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (py - b[1])
            d2 = (px - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (py - c[1])
            d3 = (px - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (py - a[1])
            inside = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
            win = inside & (z > top[i0:i1 + 1, j0:j1 + 1])
            top[i0:i1 + 1, j0:j1 + 1][win] = z
            lab[i0:i1 + 1, j0:j1 + 1][win] = number
    return lab


# --- 2. the open map to the nearest sector ---


def fill_nearest(lab, outlines: dict, g: Grid, np, coarse: int = COARSE):
    """`lab` with every cell -1 given the sector nearest it: on a grid `coarse` times coarser, each cell the sectors
    leave out goes to the sector whose outline (`outlines`: number -> [(x, y), ...]) is nearest its middle (exact
    distances; on a tie the first in `outlines`), then each fine cell left out takes its coarse cell's sector."""
    cs = g.step * coarse
    cnx, cny = math.ceil(g.nx / coarse), math.ceil(g.ny / coarse)
    cx = (np.arange(cnx) + 0.5) * cs
    cy = (np.arange(cny) + 0.5) * cs
    fj = np.minimum((cx // g.step).astype(np.int64), g.nx - 1)
    fi = np.minimum((cy // g.step).astype(np.int64), g.ny - 1)
    out = lab[np.ix_(fi, fj)].copy()
    need = out < 0
    if need.any():
        px, py = np.meshgrid(cx, cy)
        px, py = px[need], py[need]
        best = np.full(px.shape, np.inf)
        who = np.full(px.shape, -1, np.int32)
        for number, ring in outlines.items():
            d2 = np.full(px.shape, np.inf)
            for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
                dx, dy = bx - ax, by - ay
                n = dx * dx + dy * dy
                if n == 0:
                    t = 0.0
                else:
                    t = np.clip(((px - ax) * dx + (py - ay) * dy) / n, 0.0, 1.0)
                ex, ey = ax + t * dx - px, ay + t * dy - py
                np.minimum(d2, ex * ex + ey * ey, out=d2)
            better = d2 < best
            best[better] = d2[better]
            who[better] = number
        out[need] = who
    big = np.repeat(np.repeat(out, coarse, axis=0), coarse, axis=1)[:g.ny, :g.nx]
    return np.where(lab >= 0, lab, big).astype(np.int32)


# --- 3. the borders ---


def _padded(lab, np):
    p = np.full((lab.shape[0] + 2, lab.shape[1] + 2), -1, np.int32)
    p[1:-1, 1:-1] = lab
    return p


def unpinch(lab, np, rounds: int = 64) -> int:
    """Take away every place where a sector touches itself only corner to corner (two diagonal cells of the four round
    a corner, the other two another sector or two: its outline would meet itself there): the lower right cell of the
    four takes its upper right neighbour's sector. Returns how many cells changed."""
    changed = 0
    for _ in range(rounds):
        p = _padded(lab, np)
        tl, tr, bl, br = p[:-1, :-1], p[:-1, 1:], p[1:, :-1], p[1:, 1:]
        pinch = ((tl == br) & (tl != tr) & (tl != bl)) | ((tr == bl) & (tr != tl) & (tr != br))
        if not pinch.any():
            return changed
        ci, cj = np.nonzero(pinch)           # corner (ci, cj): its lower right cell is the grid's cell (ci, cj)
        lab[ci, cj] = tr[ci, cj]             # (never the map's outside: round its edge no pinch can be)
        changed += len(ci)
    raise SectorError("the sectors' borders keep touching themselves corner to corner")


@dataclass
class Chain:
    corners: list          # corner ids (ci * (nx + 1) + cj), from one meeting place to the next (a loop: first = last)
    left: int              # the sector on its left going along it (-1: off the map)
    right: int
    origs: list = None     # per step between corners: the map's own sectors on both sides (a border of its own)
    scale: float = 1.0     # its tolerances times this (halved where an outline wouldn't come out simple)
    points: list | None = None   # its simpler line (map points)

    def tolerances(self, g: "Grid") -> list:
        """How far each corner may lie off the simpler line: SIMPLE cells where it is on a border of the map's own
        sectors (either step beside it), SIMPLE coarse cells elsewhere (the nearest-sector fill's own grid)."""
        fine, coarse = SIMPLE * g.step * self.scale, SIMPLE * g.step * COARSE * self.scale
        steps = self.origs or [False] * (len(self.corners) - 1)
        out = []
        for k in range(len(self.corners)):
            near = steps[max(0, k - 1):k + 1]
            out.append(fine if any(near) else coarse)
        return out


def chains_of(lab, g: Grid, np, orig=None) -> list:
    """The borders between the cells' sectors (and the map's edge), as chains from one meeting place of three or more
    sectors to the next. `orig` (the map's own sectors' cells, a bool grid) sets each chain's `origs`."""
    p = _padded(lab, np)
    nxc = g.nx + 1
    vert = p[1:-1, :-1] != p[1:-1, 1:]          # (ny, nx+1): corner (r, c) to (r + 1, c)
    horz = p[:-1, 1:-1] != p[1:, 1:-1]          # (ny+1, nx): corner (r, c) to (r, c + 1)
    vr, vc = np.nonzero(vert)
    hr, hc = np.nonzero(horz)
    a_ids = np.concatenate([vr * nxc + vc, hr * nxc + hc]).tolist()
    b_ids = np.concatenate([(vr + 1) * nxc + vc, hr * nxc + hc + 1]).tolist()
    adj: dict = {}
    for a, b in zip(a_ids, b_ids):
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    junctions = sorted(k for k, v in adj.items() if len(v) >= 3)   # (with no pinch, every other corner has two)
    used: set = set()
    paths = []

    def walk(start: int, nxt: int) -> list:
        path, prev, cur = [start, nxt], start, nxt
        used.add((min(start, nxt), max(start, nxt)))
        while cur not in jset:
            a, b = adj[cur]
            prev, cur = cur, (b if a == prev else a)
            used.add((min(prev, cur), max(prev, cur)))
            path.append(cur)
        return path
    jset = set(junctions)
    for j in junctions:
        for nb in adj[j]:
            if (min(j, nb), max(j, nb)) not in used:
                paths.append(walk(j, nb))
    for k in sorted(adj):                         # loops with no meeting place: a sector alone in another, or the
        for nb in adj[k]:                         # whole map one sector
            if (min(k, nb), max(k, nb)) not in used:
                jset.add(k)
                paths.append(walk(k, nb))
                jset.discard(k)
    out = []
    po = None if orig is None else np.pad(orig, 1).tolist()
    for path in paths:
        left, right = _sides(p, path[0], path[1], nxc)
        origs = None
        if po is not None:
            origs = []
            for a, b in zip(path, path[1:]):
                (l1, l2), (r1, r2) = _side_cells(a, b, nxc)
                origs.append(po[l1][l2] and po[r1][r2])
        out.append(Chain(path, left, right, origs))
    return out


def _side_cells(a: int, b: int, nxc: int):
    """The padded cells (row, column) on the left and right of the corner-to-corner step a -> b."""
    ai, aj = divmod(a, nxc)
    bi, bj = divmod(b, nxc)
    if bi == ai + 1:      # down (+y): left is the smaller x
        return (ai + 1, aj), (ai + 1, aj + 1)
    if bi == ai - 1:      # up (-y): left is the larger x
        return (ai, aj + 1), (ai, aj)
    if bj == aj + 1:      # +x: left is the larger y
        return (ai + 1, aj + 1), (ai, aj + 1)
    return (ai, aj), (ai + 1, aj)   # -x: left is the smaller y


def _sides(p, a: int, b: int, nxc: int) -> tuple[int, int]:
    (l1, l2), (r1, r2) = _side_cells(a, b, nxc)
    return int(p[l1, l2]), int(p[r1, r2])


def rings_of(chains: list) -> dict:
    """Each sector's outlines from the chains, the sector on their left: number -> [[chain index, forward], ...] per
    ring, in order."""
    by_zone: dict = {}
    for k, ch in enumerate(chains):
        for zone, fwd in ((ch.left, True), (ch.right, False)):
            if zone >= 0:
                start = ch.corners[0] if fwd else ch.corners[-1]
                by_zone.setdefault(zone, {}).setdefault(start, []).append((k, fwd))
    out: dict = {}
    for zone, starts in by_zone.items():
        if any(len(lst) != 1 for lst in starts.values()):
            raise SectorError(f"sector {zone}'s outline meets itself")
        left = {lst[0] for lst in starts.values()}
        rings = []
        while left:
            first = cur = min(left)
            ring = []
            while True:
                ring.append(cur)
                left.discard(cur)
                ch = chains[cur[0]]
                nxt = starts.get(ch.corners[-1] if cur[1] else ch.corners[0])
                if nxt is None:
                    raise SectorError(f"sector {zone}'s outline doesn't close")
                cur = nxt[0]
                if cur == first:
                    break
                if cur not in left:
                    raise SectorError(f"sector {zone}'s outline doesn't close")
            rings.append(ring)
        out[zone] = rings
    return out


def ring_points(ring: list, chains: list, g: Grid, simple: bool = True) -> list:
    """A ring's points on the map (each chain's simpler line, or its corners when `simple` is False), without the
    repeated ends."""
    pts: list = []
    for k, fwd in ring:
        ch = chains[k]
        line = ch.points if simple and ch.points is not None else [_corner_point(c, g) for c in ch.corners]
        line = line if fwd else line[::-1]
        pts.extend(line[:-1])
    return pts


def _corner_point(c: int, g: Grid) -> tuple[float, float]:
    ci, cj = divmod(c, g.nx + 1)
    return g.corner(ci, cj)


def area(pts: list) -> float:
    """The signed area of a ring (positive: the shipped zones' turn, the inside on the left)."""
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


def simplify(points: list, tol) -> list:
    """Douglas-Peucker: the line through `points` with its ends kept and every point dropped that lies within its
    tolerance of the line kept (`tol`: one for all, or one per point; a loop, first point = last, is split at its
    farthest point first). Of the points too far off, the one farthest past its own tolerance is kept first."""
    tols = list(tol) if isinstance(tol, (list, tuple)) else [tol] * len(points)
    if len(points) <= 2:
        return list(points)
    if points[0] == points[-1]:
        far = max(range(1, len(points) - 1), key=lambda i: math.dist(points[0], points[i]))
        return simplify(points[:far + 1], tols[:far + 1])[:-1] + simplify(points[far:], tols[far:])
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        (ax, ay), (bx, by) = points[a], points[b]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy)
        best, at = 1.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / n if n else math.hypot(px - ax, py - ay)
            if d > best * tols[i]:
                best, at = d / tols[i], i
        if at >= 0:
            keep[at] = True
            stack += [(a, at), (at, b)]
    return [pt for pt, k in zip(points, keep) if k]


def _cross(o, a, b) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _segments_cross(p1, p2, p3, p4) -> bool:
    """Whether segments p1-p2 and p3-p4 cross or touch (sharing an end doesn't count when they only meet there)."""
    d1, d2 = _cross(p3, p4, p1), _cross(p3, p4, p2)
    d3, d4 = _cross(p1, p2, p3), _cross(p1, p2, p4)
    if ((d1 > 0) != (d2 > 0)) and d1 != 0 and d2 != 0 and ((d3 > 0) != (d4 > 0)) and d3 != 0 and d4 != 0:
        return True

    def on(p, q, r):  # r on segment p-q (collinear)
        return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])
    return ((d1 == 0 and on(p3, p4, p1)) or (d2 == 0 and on(p3, p4, p2)) or (d3 == 0 and on(p1, p2, p3))
            or (d4 == 0 and on(p1, p2, p4)))


def is_simple(pts: list) -> bool:
    """Whether a ring is a simple polygon: no point twice, no two sides crossing or touching (beyond neighbours
    sharing their corner), and it encloses some area."""
    n = len(pts)
    if n < 3 or len(set(pts)) != n or area(pts) <= 0:
        return False
    sides = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    boxes = [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b in sides]
    order = sorted(range(n), key=lambda i: boxes[i][0])
    for k, i in enumerate(order):
        for j in order[k + 1:]:
            if boxes[j][0] > boxes[i][1]:
                break
            if boxes[j][2] > boxes[i][3] or boxes[j][3] < boxes[i][2]:
                continue
            if j == (i + 1) % n or i == (j + 1) % n:
                a, b = sides[i] if j == (i + 1) % n else sides[j]
                c, d = sides[j] if j == (i + 1) % n else sides[i]
                if _cross(a, b, d) == 0 and (d[0] - b[0]) * (a[0] - b[0]) + (d[1] - b[1]) * (a[1] - b[1]) > 0:
                    return False   # the next side folds back over this one
                continue
            if _segments_cross(*sides[i], *sides[j]):
                return False
    return True


# --- 4. a sector's zone and its share of the zone map ---


def triangulate(pts: list) -> list:
    """Triangles (index triples, counter-clockwise) covering the simple counter-clockwise polygon `pts` (ear
    clipping). Points on a straight stretch are left out of the triangles."""
    idx = list(range(len(pts)))
    out = []
    k = 0
    while len(idx) > 3:
        n = len(idx)
        for step in range(n):
            m = (k + step) % n
            i0, i1, i2 = idx[m - 1], idx[m], idx[(m + 1) % n]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if _cross(a, b, c) <= 0:
                continue
            if any(j not in (i0, i1, i2) and pts[j] not in (a, b, c) and _cross(a, b, pts[j]) >= 0
                   and _cross(b, c, pts[j]) >= 0 and _cross(c, a, pts[j]) >= 0 for j in idx):
                continue
            out.append((i0, i1, i2))
            del idx[m]
            k = m
            break
        else:
            for m in range(n):    # no ear: a point on a straight stretch goes (no triangle holds it)
                if _cross(pts[idx[m - 1]], pts[idx[m]], pts[idx[(m + 1) % n]]) == 0:
                    del idx[m]
                    break
            else:
                raise SectorError("a sector's outline can't be cut into triangles (it isn't a simple shape)")
    if len(idx) == 3 and _cross(pts[idx[0]], pts[idx[1]], pts[idx[2]]) > 0:
        out.append(tuple(idx))
    return out


def inner_ring(ring: list, band, rounds: int = 40) -> tuple[list, list]:
    """The ring inside a counter-clockwise ring: each point moved in along its corner's bisector, as far as keeps both
    its sides `band` away (at most MITER bands; `band`: one width, or one per point). Where that would fold the band
    (a side's two triangles turned over, a point outside the outline, the inner ring crossing itself or the outline)
    the points there come in less, halved each round, down to none (the point stays on the outline). Returns (the
    inner ring, each point's width)."""
    n = len(ring)
    d = list(band) if isinstance(band, (list, tuple)) else [float(band)] * n
    least = max(d) / 64
    q: list = []
    for _ in range(rounds):
        q = []
        for i in range(n):
            (px, py), (x, y), (qx, qy) = ring[i - 1], ring[i], ring[(i + 1) % n]
            l1, l2 = math.hypot(x - px, y - py), math.hypot(qx - x, qy - y)
            n1 = (-(y - py) / l1, (x - px) / l1)
            n2 = (-(qy - y) / l2, (qx - x) / l2)
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            m = math.hypot(mx, my)
            if m < 1e-9:
                mx, my, m = n1[0], n1[1], 1.0
            mx, my = mx / m, my / m
            reach = d[i] / max(mx * n1[0] + my * n1[1], 1 / MITER)
            q.append((x + mx * reach, y + my * reach) if d[i] > 0 else (x, y))
        bad = set()
        for i in range(n):
            j = (i + 1) % n
            if d[i] > 0 and not _inside(q[i], ring):
                bad.add(i)
            if _cross(ring[i], ring[j], q[j]) < 0 or _cross(ring[i], q[j], q[i]) < 0 \
                    or (d[i] > 0 and d[j] > 0 and (_cross(ring[i], ring[j], q[j]) == 0 or _cross(ring[i], q[j], q[i]) == 0)):
                bad |= {i, j}
        bad |= _crossing(q, ring)
        bad = {i for i in bad if d[i] > 0}
        if not bad:
            return q, d
        for i in bad:
            d[i] = d[i] / 2 if d[i] / 2 >= least else 0.0
    raise SectorError("a sector's border band can't be fitted inside it")


def _crossing(inner: list, ring: list) -> set:
    """Points of `inner` at the ends of its sides that cross another of its sides (not a neighbour) or a side of the
    outline `ring` (a side that only touches the outline at its own point on it doesn't count)."""
    n = len(inner)
    sides = [(inner[i], inner[(i + 1) % n], i) for i in range(n)]
    outer = [(ring[i], ring[(i + 1) % n], -1) for i in range(n)]
    allsides = sides + outer
    boxes = [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b, _ in allsides]
    order = sorted(range(len(allsides)), key=lambda k: boxes[k][0])
    out = set()
    for pos, k in enumerate(order):
        for m in order[pos + 1:]:
            if boxes[m][0] > boxes[k][1]:
                break
            if boxes[m][2] > boxes[k][3] or boxes[m][3] < boxes[k][2]:
                continue
            (a, b, i), (c, e, j) = allsides[k], allsides[m]
            if i < 0 and j < 0:
                continue                      # two sides of the outline: it's simple
            if i >= 0 and j >= 0 and (j == (i + 1) % n or i == (j + 1) % n or i == j):
                continue
            if len({a, b} & {c, e}) and (i < 0 or j < 0):
                continue                      # an inner point left on the outline touches its own sides there
            if _segments_cross(a, b, c, e):
                for side in (i, j):
                    if side >= 0:
                        out |= {side, (side + 1) % n}
    return out


def _inside(pt, ring: list) -> bool:
    x, y = pt
    hit = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            hit = not hit
    return hit


def _split(tris: list, pts: list, ay: float) -> tuple[list, list]:
    """The triangles (point triples: (x, y, c)) cut along y = ay: those with every point at y <= ay, those at >= ay;
    a triangle across the line is cut into pieces there (x and c taken along its sides), each keeping its turn."""
    north, south = [], []
    for t in tris:
        p = [pts[i] for i in t]
        side = [(-1 if q[1] < ay else 1 if q[1] > ay else 0) for q in p]
        if all(s <= 0 for s in side):
            north.append(tuple(p))
            continue
        if all(s >= 0 for s in side):
            south.append(tuple(p))
            continue
        # walk the triangle's sides, adding the line's crossing between points on opposite sides
        poly: list = []
        for k in range(3):
            a, b = p[k], p[(k + 1) % 3]
            sa, sb = side[k], side[(k + 1) % 3]
            poly.append((a, sa))
            if sa * sb < 0:
                t_ = (ay - a[1]) / (b[1] - a[1])
                poly.append(((a[0] + (b[0] - a[0]) * t_, ay, a[2] + (b[2] - a[2]) * t_), 0))
        for want, into in ((-1, north), (1, south)):
            piece = [q for q, s in poly if s == 0 or s == want]
            for k in range(1, len(piece) - 1):    # a fan: the piece is convex (a triangle's part)
                tri = (piece[0], piece[k], piece[k + 1])
                if _cross(tri[0], tri[1], tri[2]) > 0:
                    into.append(tri)
    return north, south


def zone_mesh(old: Zone, ring: list, height_at, band: float = BAND) -> tuple[Zone, list]:
    """Zone `old` (number, name, label, the 4th value) with the outline `ring` (counter-clockwise map points): its
    parts and border drawn the way the shipped zones are, with a border band `band` wide where it fits, each point
    at `height_at(x, y)`'s ground. Returns the zone and notes."""
    notes = []
    n = len(ring)
    widths: list = [band] * n
    inner = inside = None
    for _try in range(6):
        try:
            inner, widths = inner_ring(ring, widths)
            inside = triangulate(inner)
            break
        except SectorError:
            widths = [w / 2 for w in widths]
    if inside is None:   # no band fits anywhere: the inner ring on the outline (a border of nothing)
        inner, widths, inside = list(ring), [0.0] * n, triangulate(ring)
        notes.append(f"sector {old.number}: too narrow for its border's band, drawn without one")
    else:
        thin = sum(w < band for w in widths)
        if thin:
            notes.append(f"sector {old.number}: its border's band narrower at {thin} of its {n} corners (as little "
                         f"as {min(widths):.0f}, not {band:.0f})")
    pts = [(x, y, 0.0) for x, y in ring] + [(x, y, 1.0) for x, y in inner]
    tris = []
    for i in range(n):
        j = (i + 1) % n
        tris += [(i, j, n + j), (i, n + j, n + i)]
    tris += [(n + a, n + b_, n + c) for a, b_, c in inside]
    tris = [t for t in tris if _cross(pts[t[0]], pts[t[1]], pts[t[2]]) > 0]   # (a corner on the outline: none)
    ax, ay = old.anchor[0], old.anchor[1]
    ys = [y for _x, y in ring]
    if not min(ys) < ay < max(ys):
        ay = (min(ys) + max(ys)) / 2
        notes.append(f"sector {old.number}: its label lies outside it, so its parts split through its middle")
    north, south = _split(tris, pts, ay)
    w = old.vertices[0][3] if old.vertices else 0.0
    vertices, triangles, parts = [], [], []
    for piece in (north, south):
        first_v, first_t = len(vertices), len(triangles)
        at: dict = {}
        for tri in piece:
            ids = []
            for x, y, c in tri:
                key = (x, y, c)   # (an inner point left on the outline is its own point: its 5th value differs)
                if key not in at:
                    at[key] = len(vertices)
                    vertices.append((x, y, height_at(x, y), w, c))
                ids.append(at[key])
            triangles.append(tuple(ids))
        parts.append((first_t, len(triangles) - first_t, first_v, len(vertices) - first_v))
    first_v, first_t = len(vertices), len(triangles)
    for x, y, c in pts:
        vertices.append((x, y, height_at(x, y), w, c))
    for i in range(n):
        j = (i + 1) % n
        triangles += [(first_v + i, first_v + j, first_v + n + j), (first_v + i, first_v + n + j, first_v + n + i)]
    zone = Zone(old.number, old.name, (old.anchor[0], old.anchor[1], height_at(old.anchor[0], old.anchor[1])),
                vertices, triangles, parts, (first_t, 2 * n, first_v, 2 * n), (first_v, n), list(old.outline),
                old.stored_name)
    return zone, notes


def zone_map(template: bytes, rings: dict, width: float, height: float) -> bytes:
    """The zone map (`template`: the scenario's own) made again over `rings` (number -> counter-clockwise outline):
    each sector's outline cut into triangles at its number x LEVEL, over the whole map (rusemod.kdt_edit.rebuild)."""
    from . import kdt_edit
    k = Kdt(template)
    k.subtrees = k.subtrees[:1]
    top = max(LEVEL, max(rings) * LEVEL)
    k.bounds_min, k.bounds_max = (0.0, 0.0, 0.0), (float(width), float(height), float(top))
    positions, tris = [], []
    for number in sorted(rings):
        q = []
        for x, y in rings[number]:
            p = (k.to_quant(0, x), k.to_quant(1, y))
            if not q or q[-1] != p:
                q.append(p)
        while len(q) > 1 and q[0] == q[-1]:
            q.pop()
        if len(q) < 3 or area(q) <= 0:
            raise SectorError(f"sector {number} has no area left in the zone map")
        base = len(positions)
        zq = k.to_quant(2, number * LEVEL)
        positions += [(x, y, zq) for x, y in q]
        tris += [(base + a, base + b, base + c) for a, b, c in triangulate(q)]
    k.set_mesh(0, positions, [v for t in tris for v in t], [(0.0, 0.0, 1.0)] * len(positions))
    kdt_edit.rebuild(k, 0, positions, tris)
    k.set_main_entries([(0, 0, 0, float(width)), (2, 0, 0, 0.0), (0, 1, 0, float(height)), (2, 1, 0, 0.0),
                        (0, 2, 0, float(top)), (2, 2, 0, 0.0), (5, 0, 0, float(width) / 2)])
    problems = kdt_edit.check(k, 0)
    if problems:
        raise SectorError(f"the new zone map's tree is wrong: {problems[0]}")
    return k.to_bytes()


# --- all of it ---


@dataclass
class Whole:
    zones: list           # the scenario's zones, in their order, made again
    kdt: bytes            # the zone map made again
    labels: object        # the grid's cells' sectors (numpy), for a picture
    grid: Grid
    notes: list


def over_whole_map(s: Scenario, kdt_raw: bytes, width: float, height: float, height_at=None,
                   most: int = MOST_CELLS) -> Whole:
    """Scenario `s`'s sectors (and its zone map `kdt_raw`) made again so that they cover the whole map (`width` by
    `height` map units): every place goes to the sector it was in, or the sector nearest it. `height_at(x, y)`: the
    ground's height (None off the map: the nearest place on it), else every point at the zone's label height."""
    np = _numpy()
    if not s.zones:
        raise SectorError("the scenario has no sectors")
    numbers = [z.number for z in s.zones]
    if len(set(numbers)) != len(numbers) or min(numbers) < 0:
        raise SectorError(f"the scenario's sectors are numbered {numbers}: each must be a different number, 0 or more")
    g = Grid.over(width, height, most)
    kdt = Kdt(kdt_raw)
    lab0 = kdt_labels(kdt, g, numbers, np)
    outlines = {}
    for z in s.zones:
        ring = z.outline_points()
        if len(ring) >= 3:
            outlines[z.number] = ring
    if not outlines:
        raise SectorError("none of the scenario's sectors has an outline")
    lab = fill_nearest(lab0, outlines, g, np)
    orig = lab0 >= 0
    notes = []
    pinched = unpinch(lab, np)
    for _round in range(16):
        chains = chains_of(lab, g, np, orig)
        rings = rings_of(chains)
        strays = 0
        for zone, zr in rings.items():
            outer = [(r, area(ring_points(r, chains, g, simple=False))) for r in zr]
            outer = [(r, a) for r, a in outer if a > 0]
            if len(outer) <= 1:
                continue
            outer.sort(key=lambda ra: -ra[1])
            for r, _a in outer[1:]:   # a stray piece: its cells to the neighbour it borders most
                strays += _absorb(lab, g, chains, r, zone, np)
        if not strays:
            break
        pinched += unpinch(lab, np)
    else:
        raise SectorError("the sectors' pieces can't be joined up")
    missing = sorted(set(numbers) - set(rings))
    if missing:
        raise SectorError(f"sector(s) {missing} have no ground left on the map")
    for zone, zr in rings.items():
        if len(zr) > 1:
            inside = sorted({chains[k].right if fwd else chains[k].left for r in zr[1:] for k, fwd in r} - {-1})
            # not a game rule: a zone in the scenario's file has one outline, so a sector with a hole can't be
            # written down; the build keeps that scenario's own sectors and warns
            raise SectorError(f"sector {zone} has sector(s) {inside} inside it, and a sector's outline in the "
                              f"scenario's file can't have a hole")
    outline = {}
    for _round in range(12):
        for ch in chains:
            ch.points = simplify([_corner_point(c, g) for c in ch.corners], ch.tolerances(g))
        bad = []
        for zone, (r,) in rings.items():
            pts = ring_points(r, chains, g)
            if is_simple(pts):
                outline[zone] = pts
            else:
                bad.append(zone)
                for k, _fwd in r:
                    chains[k].scale /= 2
        if not bad:
            break
    else:
        raise SectorError(f"sector(s) {bad}: their outlines can't be made simple")
    neighbours: dict = {z: set() for z in numbers}
    for ch in chains:
        if ch.left >= 0 and ch.right >= 0:
            neighbours[ch.left].add(ch.right)
            neighbours[ch.right].add(ch.left)
    ground = _heights(height_at, width, height)
    zones = []
    for old in s.zones:
        z, more = zone_mesh(old, outline[old.number], ground)
        kept = [n for n in old.outline if n in neighbours[old.number]]
        z.outline = kept + sorted(neighbours[old.number] - set(kept))
        zones.append(z)
        notes += more
    kdt_new = zone_map(kdt_raw, outline, width, height)
    covered = float((lab0 >= 0).mean())
    notes.insert(0, f"{len(zones)} sector(s) over the whole map (they covered {covered:.0%} of it)")
    if pinched:
        notes.append(f"{pinched} cell(s) moved where a sector touched itself corner to corner")
    return Whole(zones, kdt_new, lab, g, notes)


def apply_sectors(read, map_pack: str, files: list, height_at=None, most: int = MOST_CELLS,
                  skipped: list | None = None) -> tuple[dict, list]:
    """Every scenario of a map (`files`: its scenario file names) over the whole map (over_whole_map): its zones and
    its zone map. `read(member)`: a DataMap_Win.dat member as the build has it so far (None when it isn't there).
    A scenario without sectors or without a zone map is left as it is, with a note; one whose sectors can't be made
    again (a sector inside another) too, and `skipped` (when given) is told why. Returns ({member: new bytes},
    notes)."""
    from .cover import member as movement_member
    from .scenario import ScenarioError, folder_of
    win = read(movement_member(map_pack))
    if win is None:
        # not a game rule: the game or one of its files isn't found
        raise SectorError(f"{map_pack}: its movement file isn't in the game, so the map's size isn't known")
    width, height = map_size(win)
    folder = folder_of(map_pack)
    out: dict = {}
    notes: list = []
    for f in files:
        stem = f[:-len(".scenario")] if f.lower().endswith(".scenario") else f
        raw = read(folder + f)
        if raw is None:
            continue
        try:
            s = Scenario.read(raw)
        except (ScenarioError, struct.error) as exc:
            notes.append(f"{f}: can't be read ({exc}), its sectors left as they are")
            continue
        if not s.zones:
            continue
        kdt_member = f"{folder}zonebluff\\{stem}.kdt"
        kdt_raw = read(kdt_member)
        if kdt_raw is None:
            notes.append(f"{f}: it has no zone map, its sectors left as they are")
            continue
        try:
            Kdt(kdt_raw)
        except (ValueError, struct.error) as exc:
            notes.append(f"{f}: its zone map can't be read ({exc}), its sectors left as they are")
            continue
        try:
            res = over_whole_map(s, kdt_raw, width, height, height_at, most)
        except SectorError as exc:
            why = f"{map_pack}: {f}: its sectors can't reach over the whole map ({exc}), so they stay as the map has them"
            notes.append(why)
            if skipped is not None:
                skipped.append(why)
            continue
        s.zones = res.zones
        out[folder + f] = s.to_bytes()
        out[kdt_member] = res.kdt
        notes.append(f"{f}: " + "; ".join(res.notes))
    return out, notes


def _absorb(lab, g: Grid, chains: list, ring: list, zone: int, np) -> int:
    """The cells of sector `zone` inside its stray ring `ring` go to the sector it borders most along it. Returns how
    many cells changed."""
    other: dict = {}
    for k, fwd in ring:
        ch = chains[k]
        nb = ch.right if fwd else ch.left
        if nb >= 0:
            other[nb] = other.get(nb, 0) + len(ch.corners)
    if not other:
        raise SectorError(f"a piece of sector {zone} lies alone at the map's edge")
    to = max(sorted(other), key=lambda n: other[n])
    pts = ring_points(ring, chains, g, simple=False)
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    j0, j1 = int(min(xs) // g.step), min(g.nx - 1, int(max(xs) // g.step))
    i0, i1 = int(min(ys) // g.step), min(g.ny - 1, int(max(ys) // g.step))
    cx = (np.arange(j0, j1 + 1) + 0.5) * g.step
    cy = (np.arange(i0, i1 + 1) + 0.5) * g.step
    px, py = np.meshgrid(cx, cy)
    hit = np.zeros(px.shape, bool)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if ay == by:
            continue
        cross = ((ay > py) != (by > py)) & (px < ax + (py - ay) * (bx - ax) / (by - ay))
        hit ^= cross
    box = lab[i0:i1 + 1, j0:j1 + 1]
    move = hit & (box == zone)
    box[move] = to
    return int(move.sum())


def _heights(height_at, width: float, height: float):
    """The ground's height at a point, never None: a point off the ground takes the nearest place on it inside the
    map (0 without a ground)."""
    if height_at is None:
        return lambda x, y: 0.0
    cache: dict = {}

    def at(x: float, y: float) -> float:
        key = (x, y)
        if key in cache:
            return cache[key]
        cx, cy = min(max(x, 1.0), width - 1.0), min(max(y, 1.0), height - 1.0)
        h = height_at(cx, cy)
        k = 1
        while h is None and k <= 8:
            f = 1 - k / 16
            h = height_at(width / 2 + (cx - width / 2) * f, height / 2 + (cy - height / 2) * f)
            k += 1
        cache[key] = float(h) if h is not None else 0.0
        return cache[key]
    return at
