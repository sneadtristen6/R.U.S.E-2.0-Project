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
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import kdt as K

MEMBER = "output\\occlusioninfo_objectsonly.kdt"
LEAF_MOST = 8          # triangles in a leaf before it's split (the shipped leaves list 2 to 7)
ACROSS = 2500.0        # map units either side of a deck's line its floor reaches (the decks are ~2,400 wide)
WIDEN = 1.5            # how much wider than the shipped bridge's a new bridge's floor is made (its floors reach about
                       # 660 either side of the line, the movement on a new deck 640: a unit at the band's edge, or
                       # nudged past it by another, found no floor and dropped to the riverbed, which is what "under
                       # the bridge" looked like in the game, 2026-10-01). The floor isn't drawn: a wider one only
                       # means a unit near the deck's edge still stands at the deck's height.


class FloorError(ValueError):
    pass


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


def on_deck(tri, deck: Deck, reach: float = 1.2) -> bool:
    """A triangle lying on `deck`: every point within its length (a little past) and ACROSS of its line."""
    for x, y, _z in tri:
        t, s = deck.local(x, y)
        if abs(t) > reach or abs(s) > ACROSS:
            return False
    return True


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


def _normal(a, b, c) -> tuple[float, float, float]:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    return n if n[2] >= 0 else (-n[0], -n[1], -n[2])   # floors face up


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
    they already do, so the old points keep their exact values), vertices shared where triangles meet, per-vertex
    normals, a new k-d tree, and the MainNode's bounds."""
    if not tris:
        raise FloorError("a floor file needs at least one triangle")
    lo = [min(p[a] for t in tris for p in t) for a in range(3)]
    hi = [max(p[a] for t in tris for p in t) for a in range(3)]
    if any(lo[a] < k.bounds_min[a] or hi[a] > k.bounds_max[a] for a in range(3)):
        k.bounds_min = tuple(min(lo[a], k.bounds_min[a]) for a in range(3))
        k.bounds_max = tuple(max(hi[a], k.bounds_max[a]) for a in range(3))
    index: dict[tuple, int] = {}
    verts: list[tuple[int, int, int]] = []
    normals: list[list[float]] = []
    idx: list[int] = []
    boxes = []
    for t in tris:
        q = [tuple(k.to_quant(a, p[a]) for a in range(3)) for p in t]
        n = _normal(*t)
        for v in q:
            if v not in index:
                index[v] = len(verts)
                verts.append(v)
                normals.append([0.0, 0.0, 0.0])
            i = index[v]
            idx.append(i)
            normals[i] = [normals[i][a] + n[a] for a in range(3)]
        boxes.append((tuple(min(v[a] for v in q) for a in range(3)), tuple(max(v[a] for v in q) for a in range(3))))
    unit = []
    for n in normals:
        length = math.sqrt(sum(c * c for c in n))
        unit.append(tuple(c / length for c in n) if length > 0 else (0.0, 0.0, 1.0))
    root, lists = build_tree(boxes)
    sub = K.Subtree(K.compress(K.encode_positions(verts)), K.compress(K.encode_normals(unit)), len(idx),
                    K.compress(K.encode_indices(idx)), b"", b"")
    k.subtrees = [sub]
    k.set_tree(0, root, lists)
    k.triangle_count = len(tris)
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


def floors_for(k: K.Kdt, height_at, new: list, gone: list[Deck]) -> tuple[bytes, list[str]]:
    """The objects-only file with a floor for each new bridge and none for the sunk ones. `new`: [(the new deck,
    [the decks of the shipped bridges of its kind on this map])]; `height_at(x, y)`: the ground (None off the mesh);
    `gone`: decks whose floors go. Returns (the file, notes)."""
    shipped = triangles(k)
    tris = [t for t in shipped if not any(on_deck(t, d) for d in gone)] if gone else list(shipped)
    removed = len(shipped) - len(tris)
    notes, added = [], 0

    def ground(deck):
        (x0, y0), (x1, y1) = deck.ends()
        g0, g1 = height_at(x0, y0), height_at(x1, y1)
        return None if g0 is None or g1 is None else (g0, g1)

    def tilt(deck):
        g = ground(deck)
        return abs(g[1] - g[0]) if g else math.inf
    for deck, sources in new:
        floor, src, src_g = [], None, None
        for s in sorted(sources, key=tilt):  # the flattest shipped bridge of the kind gives the truest floor
            f, g = [t for t in shipped if on_deck(t, s)], ground(s)
            if f and g:
                floor, src, src_g = f, s, g
                break
        dst_g = ground(deck)
        if not floor or dst_g is None:
            notes.append("a new bridge has no floor to copy (no shipped bridge of its kind has one on this map): "
                         "units won't stand on it")
            continue
        tris += carry(floor, src, src_g, deck, dst_g)
        added += 1
    if not added and not removed:
        return b"", notes
    if not tris:  # the file can't be empty: the old floor stays (its ground over the water is closed to units)
        return b"", notes + ["the sunk bridge's floor stays: it's the only one on this map"]
    notes.insert(0, f"floors: {added} bridge(s) given one" + (f", {removed} triangle(s) of sunk bridges taken out"
                                                                 if removed else ""))
    return rebuild(k, tris), notes
