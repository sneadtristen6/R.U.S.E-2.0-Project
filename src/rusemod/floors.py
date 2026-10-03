"""Bridge floors: what units stand on at a bridge, in each map pack's `output\\occlusioninfo_objectsonly.kdt`.

The gameplay ground (`occlusioninfo_terrainonly.kdt`) dips into the river under a bridge just like the visible
ground; units cross on the bridge because the map pack holds a third tree, "objects only", with each bridge's floor:
on D-Day 556 triangles in clusters exactly at its 21 bridges (Pont_Metallique_02: 8 triangles in four sections along
the deck; _03: 24; the stone Pont_TangeantFloor: 12, arched). A floor runs from end to end 5 to 60 units above the
ground at the deck's ends (the game sets a "TangeantFloor" bridge on the ground under its ends). A new bridge
without one is drawn, but units ordered across walk the riverbed under it (seen in the game, 2026-09-30).

So a new bridge gets the floor of a shipped bridge of its kind: each point taken as (how far along the deck, how
far across it, its height above the line between the ground at the deck's ends), then put back along the new deck,
at the new ends' ground. A bridge sunk out of sight loses its floor. The file is then built again as one subtree,
as the shipped ones are: the vertices (shared by the triangles that meet there), their normals, the triangles, and a
k-d tree whose leaves list every triangle that reaches into their box (rusemod.kdt has the codecs).

A floor is wider than the deck (2026-10-01). Where a unit is comes from the movement graph, how high it stands from
the floor under it, and nothing ties the two: an infantry squad is five men on an arc 2,828 wide around the squad's
own place (the game data's Dispersion 500 for 5 men), each man standing on the floor under his own feet. So beside a
deck whose movement is 640 either side of its line two of the five are 2,054 out, and a man who has drifted to the
squad's limit (DispersionMax 620 for 5 men: 2,480) is 3,120 out. The game's metal bridges have, beside the deck's
band, two flat aprons as long as the band reaching 12,000 to 17,000 either side, so its infantry stand at the deck's
height over the river ("vanilla ruse they float"); its stone bridges have none, and infantry stand in the river
beside them. A new bridge with the band alone put every man beside the deck on the riverbed ("ours are in water").
So a new bridge gets an apron too (`apron`): in its band's plane, out to APRON either side, over water only.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from . import kdt as K

MEMBER = "output\\occlusioninfo_objectsonly.kdt"
LEAF_MOST = 8          # triangles in a leaf before it's split (the shipped leaves list 2 to 7)
ACROSS = 2500.0        # map units either side of a deck's line its floor reaches (the decks are ~2,400 wide)
ACROSS_WIDE = 30000.0  # ...and the stone bridges' (measured on every shipped map 2026-10-03: one strip end to end along
                       # the deck at the deck's height, about 6,940 either side of its line on Italy's, 10,620 on
                       # Germany's, 15,290 to 21,160 on Holland's small ones); looked for only when a bridge has nothing
                       # in the narrow band, so the metal bridges' floors (D-Day's, tested in the game) are found as before
HIGH = 1500.0          # ...every point of a wide floor within this of the deck's height (the line between its ends'
                       # ground): so nothing else at that width (the riverbed, another object's floor) is taken
WIDEN = 1.5            # how much wider than the shipped bridge's a new bridge's floor is made (its floors reach about
                       # 660 either side of the line, the movement on a new deck 640: a unit at the band's edge, or
                       # nudged past it by another, found no floor and dropped to the riverbed, which is what "under
                       # the bridge" looked like in the game, 2026-10-01). The floor isn't drawn: a wider one only
                       # means a unit near the deck's edge still stands at the deck's height.
APRON = 3200.0         # map units either side of a new deck's line its floor reaches over the water: the movement on
                       # the deck (640) and a squad's limit (2,480), see the top of this file
CELL = 160.0           # an apron is tested for water in cells this size (so at a bank at most this much water is
                       # left without floor: a man there wades at the water's edge)
LAP = 150.0            # how far an apron's pieces lap over the band and each other: the file's points sit on a grid
                       # (61 by 40 map units on D-Day), so pieces that only met could leave a crack to fall through
GAP = 150.0            # an apron piece is kept only where the riverbed is at least this far below it
RISE = 200.0           # ...and, at the water's edge, over dry ground no more than this far below it: a steep bank
                       # whose top is about the deck's height (else the last CELL of water under such a bank is left
                       # without floor, and it's deep there: a man 4 m under at D-Day's fourth new bridge). A unit on
                       # that edge of the bank stands this much higher at most; a low bank is never under the floor.
FAR = 20000.0          # the farthest a shipped bridge's apron reaches from its line (D-Day's: 17,230)
EDGE = (300.0, 800.0)  # where a shipped apron's near edge lies from its bridge's line (D-Day's: 438 to 630)
UP = 0x7FFDFFF5        # the normal every point of every shipped floor file has (all 45,188 points on the 29 maps that
                       # have one): straight up, whatever the floor's slope. The game turns a man to the normal of
                       # what he stands on, so a floor file never gets normals worked out from its triangles.


class FloorError(ValueError):
    pass


class NoFloor(FloorError):
    """New bridges with no floor to copy: units would walk on the riverbed under them, so the build refuses them.
    `missing`: their places in floors_for's `new`."""

    def __init__(self, missing: list[int]):
        self.missing = missing
        super().__init__(f"{len(missing)} new bridge(s) have no floor to copy (no shipped bridge of their kind on "
                         f"this map has one)")


@dataclass
class Deck:
    """A bridge's deck on the map: its middle, the unit vector along it, half its length."""
    x: float
    y: float
    ux: float
    uy: float
    half: float

    @classmethod
    def of(cls, x0: float, y0: float, x1: float, y1: float) -> "Deck":
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy)
        if n == 0:
            raise FloorError("a deck has no length")
        return cls((x0 + x1) / 2, (y0 + y1) / 2, dx / n, dy / n, n / 2)

    def local(self, x: float, y: float) -> tuple[float, float]:
        """(t: -1 at the start, 1 at the end; s: map units across, to the left)."""
        ax, ay = x - self.x, y - self.y
        return (ax * self.ux + ay * self.uy) / self.half, -ax * self.uy + ay * self.ux

    def world(self, t: float, s: float) -> tuple[float, float]:
        return (self.x + self.ux * t * self.half - self.uy * s, self.y + self.uy * t * self.half + self.ux * s)

    def ends(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return self.world(-1.0, 0.0), self.world(1.0, 0.0)


def triangles(k: K.Kdt) -> list[tuple]:
    """Every triangle of every subtree, in world units: ((x, y, z), (x, y, z), (x, y, z))."""
    out = []
    for s in range(len(k.subtrees)):
        pos = [(k.to_world(0, x), k.to_world(1, y), k.to_world(2, z)) for x, y, z in k.positions(s)]
        idx = k.indices(s)
        out += [(pos[idx[i]], pos[idx[i + 1]], pos[idx[i + 2]]) for i in range(0, len(idx), 3)]
    return out


def on_deck(tri, deck: Deck, reach: float = 1.2, across: float = ACROSS) -> bool:
    """A triangle lying on `deck`: every point within its length (a little past) and `across` of its line."""
    for x, y, _z in tri:
        t, s = deck.local(x, y)
        if abs(t) > reach or abs(s) > across:
            return False
    return True


def deck_floor(tris: list, deck: Deck, ground: tuple[float, float] | None) -> tuple[list, bool]:
    """The triangles of `deck`'s floor, and whether it's a wide one: the narrow band first (the metal bridges', ACROSS);
    for a bridge with nothing there, the wide strip the stone bridges have (ACROSS_WIDE), every point at the deck's
    height (within HIGH of the line between `ground`, its ends' ground; none without it)."""
    narrow = [t for t in tris if on_deck(t, deck)]
    if narrow or ground is None:
        return narrow, False

    def level(tri):
        for x, y, z in tri:
            t = deck.local(x, y)[0]
            if abs(z - (ground[0] + (ground[1] - ground[0]) * (t + 1) / 2)) > HIGH:
                return False
        return True
    return [t for t in tris if on_deck(t, deck, across=ACROSS_WIDE) and level(t)], True


def beside_deck(tri, deck: Deck, reach: float = 1.2) -> bool:
    """A triangle of an apron beside `deck` (the shipped metal bridges': one flat piece either side, as long as the
    deck's band): every point within the deck's length, all on one side of its line, the nearest at the band's edge
    (EDGE) and none farther than FAR."""
    across = []
    for x, y, _z in tri:
        t, s = deck.local(x, y)
        if abs(t) > reach or abs(s) > FAR:
            return False
        across.append(s)
    near = min(abs(s) for s in across)
    return EDGE[0] <= near <= EDGE[1] and (all(s > 0 for s in across) or all(s < 0 for s in across))


def apron(band: list, deck: Deck, ground: tuple[float, float], water, height_at, half: float = APRON) -> list[tuple]:
    """The floor beside a new deck's `band` (its carried floor: triangles on `deck`, whose ends' ground is `ground`),
    out to `half` either side of the deck's line wherever that's over water: flat pieces in the band's own plane (at
    each place along the deck, the band's height there), so a man beside the deck stands at the deck's height, not on
    the riverbed. `water(x, y)` says where the map's water is, `height_at(x, y)` gives the ground (None off the
    mesh). Tested in cells of CELL: a cell is floor when its corners and middle are over water with the riverbed
    GAP or more below (at the water's edge a corner may be on dry ground no more than RISE below the floor: a steep
    bank's top), so the floor never lifts a unit standing on dry ground by more than RISE, and a bank that runs at an
    angle to the deck (dry beside the deck, water farther out) still gets floor over its water. Cells that are clear
    alike join into one piece; the pieces lap over the band and over each other by LAP, always inside what was
    tested."""
    def base(t):
        return ground[0] + (ground[1] - ground[0]) * (t + 1) / 2
    points = sorted({(deck.local(x, y), z) for tri in band for x, y, z in tri})
    lines: list[list] = []  # the band's cross lines, in order along the deck: the points 200 or less apart along it
    for (t, s), z in points:  # (a line's points sit on the file's grid, so they aren't at exactly one place along)
        if lines and (t - lines[-1][0][0]) * deck.half <= 200.0:
            lines[-1].append((t, s, z))
        else:
            lines.append([(t, s, z)])
    if len(lines) < 2:
        return []
    ts = [sum(p[0] for p in line) / len(line) for line in lines]
    lift = {t: sum(p[2] - base(p[0]) for p in line) / len(line) for t, line in zip(ts, lines)}
    width = {side: {t: max(side * p[1] for p in line) for t, line in zip(ts, lines)} for side in (1, -1)}

    def height(t):
        for a, b in zip(ts, ts[1:]):
            if t <= b:
                f = min(max((t - a) / (b - a), 0.0), 1.0)
                return base(t) + lift[a] + (lift[b] - lift[a]) * f
        return base(t) + lift[ts[-1]]

    def clear(t, s):
        """May (t, s) be under the floor: 2 over water (the riverbed GAP or more below), 1 on dry ground RISE or
        less below the floor (a steep bank's top), 0 not."""
        x, y = deck.world(t, s)
        g = height_at(x, y)
        if g is None:
            return 0
        if water(x, y):
            return 2 if height(t) - g >= GAP else 0
        return 1 if height(t) - g <= RISE else 0

    def cell(u0, u1, s0, s1):  # a cell is floor when every corner and its middle may be, and one of them is water
        marks = [clear(u, s) for u, s in ((u0, s0), (u0, s1), (u1, s0), (u1, s1), ((u0 + u1) / 2, (s0 + s1) / 2))]
        return min(marks) > 0 and max(marks) == 2
    def quad(u0, u1, s0, s1, side):
        p = [(*deck.world(u0, side * s0), height(u0)), (*deck.world(u0, side * s1), height(u0)),
             (*deck.world(u1, side * s0), height(u1)), (*deck.world(u1, side * s1), height(u1))]
        return [(p[0], p[1], p[2]), (p[1], p[3], p[2])]
    out = []
    lap = LAP / deck.half
    for side in (1, -1):
        inner = max(min(width[side].values()) - LAP, 0.0)  # (0: the band has no edge on this side at some line)
        if inner >= half:
            continue
        edges = []  # the cells' edges across, from just inside the band's edge out to `half`
        s = inner
        while s < half:
            edges.append(s)
            s += CELL
        edges.append(half)
        runs = []  # [from t, to t, the stretches across that are clear ((s0, s1), ...), the band's section], in order
        for section, (a, b) in enumerate(zip(ts, ts[1:])):
            n = max(1, math.ceil((b - a) * deck.half / CELL))
            cuts = [a + (b - a) * i / n for i in range(n)] + [b]
            for u0, u1 in zip(cuts, cuts[1:]):
                spans: list[tuple[float, float]] = []
                for s0, s1 in zip(edges, edges[1:]):
                    if cell(u0, u1, side * s0, side * s1):
                        if spans and spans[-1][1] == s0:
                            spans[-1] = (spans[-1][0], s1)
                        else:
                            spans.append((s0, s1))
                if runs and runs[-1][3] == section and runs[-1][2] == tuple(spans):
                    runs[-1][1] = u1  # clear across as the cells before it are: one piece (within a section of the
                else:                 # band, where its height runs straight)
                    runs.append([u0, u1, tuple(spans), section])
        for i, (u0, u1, spans, _section) in enumerate(runs):
            before = runs[i - 1] if i else None
            after = runs[i + 1] if i + 1 < len(runs) else None
            for s0, s1 in spans:
                v0, v1 = u0, u1
                # lap over a neighbour's stretch that holds this one whole (what's lapped was tested for it)
                if before and any(n0 <= s0 and s1 <= n1 for n0, n1 in before[2]):
                    v0 = max(u0 - lap, before[0])
                if after and any(n0 <= s0 and s1 <= n1 for n0, n1 in after[2]):
                    v1 = min(u1 + lap, after[1])
                out += quad(v0, v1, s0, s1, side)
                for n0, n1 in after[2] if after else ():  # one that only partly meets it: a piece over their joint
                    lo, hi = max(s0, n0), min(s1, n1)
                    if lo < hi and not (n0 <= s0 and s1 <= n1) and not (s0 <= n0 and n1 <= s1):
                        out += quad(max(u1 - lap, u0), min(u1 + lap, after[1]), lo, hi, side)
    return out


def carry(floor: list, src: Deck, src_ground: tuple[float, float], dst: Deck,
          dst_ground: tuple[float, float], widen: float = WIDEN) -> list[tuple]:
    """`floor` (triangles on deck `src`, whose ends' ground is `src_ground`) put on deck `dst` (ends' ground
    `dst_ground`): each point keeps how far along and across it is (`widen` times as far across: WIDEN), and its
    height above the line between the ends' ground."""
    def base(g, t):
        return g[0] + (g[1] - g[0]) * (t + 1) / 2
    out = []
    for tri in floor:
        pts = []
        for x, y, z in tri:
            t, s = src.local(x, y)
            wx, wy = dst.world(t, s * widen)
            pts.append((wx, wy, base(dst_ground, t) + z - base(src_ground, t)))
        out.append(tuple(pts))
    return out


def build_tree(boxes: list[tuple[tuple, tuple]]):
    """A k-d tree over triangles' quantized boxes ((lo x, y, z), (hi x, y, z)): (root, one triangle list per leaf in
    leaf order). Each node is first clipped to its triangles' box (as the shipped trees are); it's split at the middle
    of its triangles along its longest side while that separates them, else it's a leaf. A leaf lists every triangle
    whose box reaches into it, so a point on a triangle always finds it."""
    lists: list[list[int]] = []

    def node(ids: list[int], lo: tuple, hi: tuple):
        blo = tuple(min(boxes[i][0][a] for i in ids) for a in range(3))
        bhi = tuple(max(boxes[i][1][a] for i in ids) for a in range(3))
        clips = []
        for a in range(3):  # tighten the cell to the triangles, like the shipped trees' clips
            if lo[a] is None or blo[a] > lo[a]:
                clips.append((a, blo[a], True))
                lo = lo[:a] + (blo[a],) + lo[a + 1:]
            if hi[a] is None or bhi[a] < hi[a]:
                clips.append((a, bhi[a], False))
                hi = hi[:a] + (bhi[a],) + hi[a + 1:]
        inner = None
        if len(ids) > LEAF_MOST:
            for a in sorted(range(3), key=lambda a: -(hi[a] - lo[a])):
                centres = sorted((boxes[i][0][a] + boxes[i][1][a]) // 2 for i in ids)
                v = centres[len(centres) // 2]
                if not lo[a] < v < hi[a]:
                    continue
                above = [i for i in ids if boxes[i][1][a] >= v]
                below = [i for i in ids if boxes[i][0][a] <= v]
                if len(above) < len(ids) and len(below) < len(ids):
                    first = node(above, lo[:a] + (v,) + lo[a + 1:], hi)
                    second = node(below, lo, hi[:a] + (v,) + hi[a + 1:])
                    inner = K.Split(a, v, first, second)
                    break
        if inner is None:
            if len(ids) > 256:
                raise FloorError(f"{len(ids)} triangles can't be told apart (a leaf lists at most 256)")
            lists.append(sorted(ids))
            inner = K.Leaf(len(ids))
        for a, v, up in reversed(clips):
            inner = K.Clip(a, v, up, inner)
        return inner

    if not boxes:
        raise FloorError("no triangles to build a tree over")
    root = node(list(range(len(boxes))), (None,) * 3, (None,) * 3)
    return root, lists


def rebuild(k: K.Kdt, tris: list[tuple]) -> bytes:
    """The file `k` holding exactly `tris` (world units) as one subtree: the bounds grown to hold them (kept when
    they already do, so the old points keep their exact values), vertices shared where triangles meet, every
    triangle facing up, every point's normal straight up (UP), a new k-d tree, and the MainNode's bounds."""
    if not tris:
        raise FloorError("a floor file needs at least one triangle")
    lo = [min(p[a] for t in tris for p in t) for a in range(3)]
    hi = [max(p[a] for t in tris for p in t) for a in range(3)]
    if any(lo[a] < k.bounds_min[a] or hi[a] > k.bounds_max[a] for a in range(3)):
        k.bounds_min = tuple(min(lo[a], k.bounds_min[a]) for a in range(3))
        k.bounds_max = tuple(max(hi[a], k.bounds_max[a]) for a in range(3))
    index: dict[tuple, int] = {}
    verts: list[tuple[int, int, int]] = []
    idx: list[int] = []
    boxes = []
    for t in tris:
        q = [tuple(k.to_quant(a, p[a]) for a in range(3)) for p in t]
        # every shipped floor triangle faces up by the order of its points (all 556 of D-Day's), so ours do too;
        # one that's no triangle any more on the file's grid (a sliver) is left out: nothing can stand on it
        ux, uy, uz = (q[1][a] - q[0][a] for a in range(3))
        vx, vy, vz = (q[2][a] - q[0][a] for a in range(3))
        nz = ux * vy - uy * vx
        if nz == 0 and uy * vz - uz * vy == 0 and uz * vx - ux * vz == 0:
            continue
        if nz < 0:
            q[1], q[2] = q[2], q[1]
        for v in q:
            if v not in index:
                index[v] = len(verts)
                verts.append(v)
            idx.append(index[v])
        boxes.append((tuple(min(v[a] for v in q) for a in range(3)), tuple(max(v[a] for v in q) for a in range(3))))
    if not boxes:
        raise FloorError("a floor file needs at least one triangle")
    root, lists = build_tree(boxes)
    sub = K.Subtree(K.compress(K.encode_positions(verts)), K.compress(struct.pack(f"<{len(verts)}I", *[UP] * len(verts))),
                    len(idx), K.compress(K.encode_indices(idx)), b"", b"")
    k.subtrees = [sub]
    k.set_tree(0, root, lists)
    k.triangle_count = len(boxes)
    entries = k.main_entries()
    leaf = next((e for e in entries if e[0] == K.MAIN_LEAF), (K.MAIN_LEAF, 0, 0, 0.0))
    k.set_main_entries([(0, 0, 0, k.bounds_max[0]), (2, 0, 0, k.bounds_min[0]),
                        (0, 1, 0, k.bounds_max[1]), (2, 1, 0, k.bounds_min[1]),
                        (0, 2, 0, k.bounds_max[2]), (2, 2, 0, k.bounds_min[2]),
                        (K.MAIN_LEAF, leaf[1], 0, leaf[3])])
    return k.to_bytes()


def found_at(k: K.Kdt, x: float, y: float) -> list[int]:
    """The triangles of subtree 0 whose leaves hold the point (x, y) at any height (a vertical look-up)."""
    qx, qy = k.to_quant(0, x), k.to_quant(1, y)
    root = k.tree(0)
    lists = k.trilists(0, root)
    out = []
    for (leaf, lo, hi), lst in zip(K.leaves(root), lists):
        if all((lo[a] is None or lo[a] <= q) and (hi[a] is None or q <= hi[a]) for a, q in ((0, qx), (1, qy))):
            out += lst
    return sorted(set(out))


def floors_for(k: K.Kdt, height_at, new: list, gone: list[Deck], water=None) -> tuple[bytes, list[str]]:
    """The objects-only file with a floor for each new bridge and none for the sunk ones. `new`: [(the new deck,
    [the decks of the shipped bridges of its kind on this map])]; `height_at(x, y)`: the ground (None off the mesh);
    `gone`: decks whose floors go, their aprons with them; `water(x, y)`: where the map's water is, for the new
    floors' aprons (without it they get the band alone). Returns (the file, notes). Raises NoFloor when a new deck
    gets no floor: the build opens movement along every new deck, and units there would stand on the riverbed."""
    shipped = triangles(k)

    def ground(deck):
        (x0, y0), (x1, y1) = deck.ends()
        g0, g1 = height_at(x0, y0), height_at(x1, y1)
        return None if g0 is None or g1 is None else (g0, g1)
    if gone:  # each sunk deck's floor (narrow or wide, deck_floor) and its aprons go
        out = {id(t) for d in gone for t in deck_floor(shipped, d, ground(d))[0]}
        tris = [t for t in shipped if id(t) not in out and not any(beside_deck(t, d) for d in gone)]
    else:
        tris = list(shipped)
    removed = len(shipped) - len(tris)
    notes, added, reaches, missing = [], 0, [], []

    def tilt(deck):
        g = ground(deck)
        return abs(g[1] - g[0]) if g else math.inf
    for i, (deck, sources) in enumerate(new):
        floor, src, src_g, wide = [], None, None, False
        for s in sorted(sources, key=tilt):  # the flattest shipped bridge of the kind gives the truest floor
            g = ground(s)
            f, w = deck_floor(shipped, s, g)
            if f and g:
                floor, src, src_g, wide = f, s, g, w
                break
        dst_g = ground(deck)
        if not floor or dst_g is None:
            missing.append(i)
            continue
        band = carry(floor, src, src_g, deck, dst_g, widen=1.0 if wide else WIDEN)  # a wide floor is wide enough
        tris += band
        added += 1
        if water is not None:
            beside = apron(band, deck, dst_g, water, height_at)
            tris += beside
            reaches.append(max((abs(deck.local(p[0], p[1])[1]) for t in beside for p in t), default=0.0))
    if missing:
        raise NoFloor(missing)
    if not added and not removed:
        return b"", notes
    if not tris:  # the file can't be empty: the old floor stays (its ground over the water is closed to units)
        return b"", notes + ["the sunk bridge's floor stays: it's the only one on this map"]
    notes.insert(0, f"floors: {added} bridge(s) given one" + (f", {removed} triangle(s) of sunk bridges taken out"
                                                                 if removed else ""))
    dry = sum(1 for r in reaches if r < APRON / 2)
    if dry:  # (no water beside the deck, or a bank within a few metres of its line all the way)
        notes.append(f"{dry} new bridge(s) have little or no water beside the deck for their floor to reach over: "
                     f"infantry beside the deck stand on the ground there")
    return rebuild(k, tris), notes
