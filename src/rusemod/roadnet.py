"""The road network: `mapinfo.win`'s buffer 0 (docs/FORMATS.md, the mapinfo row), the graph units follow along a
map's roads. Read and written byte-identical on all 32 maps (tools/verify_roadnet.py); a new road is added as points
along its curve, linked in a chain and to the nearest road at each end, with the index built again.

Layout (little-endian):
- header: u16 point count, u16 link count, then u32 offsets of the points (20), the links, the lists and the index;
- points: u32 (start of its links in the lists << 8 | how many), f32 x, f32 y; on the road curves, about 9 m apart;
- links: u16 a, u16 b, u16 cost (the distance between them / 10, the game's own rounding within 2); padded to 4;
- lists: every point's links in turn, ascending (u16 link numbers); padded to 4;
- index: a k-d tree over the links. A branch is u16 tag (bit 0 set; the jump's high bits), u16 word ((word & ~1) *
  2 = the jump's low part, bit 0 set), f32 split: x at even depths, y at odd ones; its left half follows it, the right
  half starts `jump` bytes after the left. A leaf is u16 byte length, then its links (u16; a link crossing a split is
  in both halves), padded to 4. The same jump rule as the navigation graphs' index (rusemod.nav).
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

HEAD = 20
LEAF_MOST = 6          # links a leaf holds before it's split (the shipped maps' leaves hold 2 to 8)
POINT_STEP = 2300.0    # map units between a new road's points (the shipped links' median, about 9 m)


class RoadNetError(ValueError):
    pass


def _pad(data: bytes) -> bytes:
    return data + bytes(-len(data) % 4)


@dataclass
class RoadNet:
    points: list[tuple[float, float]] = field(default_factory=list)
    links: list[tuple[int, int, int]] = field(default_factory=list)   # (a, b, cost)
    tree: list = field(default_factory=list)                          # ["branch", split, left, right] / ["leaf", ids]

    @classmethod
    def read(cls, data: bytes) -> "RoadNet":
        if len(data) < HEAD:
            raise RoadNetError("the road network is shorter than its header")
        n, m = struct.unpack_from("<HH", data, 0)
        o1, o2, o3, o4 = struct.unpack_from("<4I", data, 4)
        if o1 != HEAD or o2 != o1 + 12 * n or not o2 <= o3 <= o4 <= len(data):
            raise RoadNetError(f"the road network's sections don't add up ({n} points at {o1}..{o2}, then {o3}, {o4})")
        raw = [struct.unpack_from("<Iff", data, o1 + 12 * i) for i in range(n)]
        links = [struct.unpack_from("<3H", data, o2 + 6 * i) for i in range(m)]
        net = cls([(x, y) for _, x, y in raw], [tuple(link) for link in links],
                  _tree_read(data[o4:], 0) if o4 < len(data) else ["leaf", []])
        if [w for w, _, _ in raw] != net._words() or data[o3:o4] != net._lists_bytes():
            raise RoadNetError("the road network's point lists don't match its links")
        return net

    def _lists(self) -> list[list[int]]:
        out: list[list[int]] = [[] for _ in self.points]
        for i, (a, b, _cost) in enumerate(self.links):
            out[a].append(i)
            out[b].append(i)
        return out

    def _words(self) -> list[int]:
        words, at = [], 0
        for mine in self._lists():
            words.append(at << 8 | len(mine))
            at += len(mine)
        return words

    def _lists_bytes(self) -> bytes:
        ids = [i for mine in self._lists() for i in mine]
        return _pad(struct.pack(f"<{len(ids)}H", *ids))

    def to_bytes(self) -> bytes:
        if len(self.points) > 0xFFFF or len(self.links) > 0xFFFF:
            raise RoadNetError("the road network holds at most 65,535 points and links")
        points = b"".join(struct.pack("<Iff", w, x, y) for w, (x, y) in zip(self._words(), self.points))
        links = _pad(b"".join(struct.pack("<3H", *link) for link in self.links))
        lists = self._lists_bytes()
        o2 = HEAD + len(points)
        o3 = o2 + len(links)
        o4 = o3 + len(lists)
        return (struct.pack("<HH4I", len(self.points), len(self.links), HEAD, o2, o3, o4) + points + links + lists
                + _tree_write(self.tree))

    # --- adding a road ---
    def add_road(self, line: list[tuple[float, float]], join: float = 20000.0) -> dict:
        """Add a road along `line` (map points, in order: a new road's curve, sampled): points about POINT_STEP
        apart, linked in a chain; each end linked to the nearest road point within `join` map units (a junction),
        else left as a dead end. The index is built again. Returns what was added."""
        if len(line) < 2:
            raise RoadNetError("a road needs at least two points")
        pts = _resample(line, POINT_STEP)
        ends = [self._nearest(pts[0], join), self._nearest(pts[-1], join)]
        first = len(self.points)
        self.points.extend(pts)
        new_links = [(first + i, first + i + 1) for i in range(len(pts) - 1)]
        if ends[0] is not None:
            new_links.insert(0, (ends[0], first))
        if ends[1] is not None and ends[1] != ends[0]:
            new_links.append((first + len(pts) - 1, ends[1]))
        for a, b in new_links:
            self.links.append((a, b, self._cost(a, b)))
        self.tree = build_tree(self.points, self.links)
        return {"points": len(pts), "links": len(new_links), "joined": sum(e is not None for e in ends)}

    def _cost(self, a: int, b: int) -> int:
        return min(0xFFFF, round(math.dist(self.points[a], self.points[b]) / 10))

    def _nearest(self, at: tuple[float, float], within: float) -> int | None:
        best, where = within, None
        for i, p in enumerate(self.points):
            d = math.dist(p, at)
            if d <= best:
                best, where = d, i
        return where


def _resample(line: list[tuple[float, float]], step: float) -> list[tuple[float, float]]:
    """Points along the polyline `line`, `step` apart (its ends kept)."""
    out = [tuple(map(float, line[0]))]
    carried = 0.0
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        at = step - carried
        while at < seg:
            t = at / seg
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
            at += step
        carried = (carried + seg) % step if seg else carried
    last = tuple(map(float, line[-1]))
    if math.dist(out[-1], last) > step * 0.25:
        out.append(last)
    else:
        out[-1] = last
    return out


# --- a mod's roads: maps/<map>/roads.toml (docs/MOD_FORMAT.md §8) ---
@dataclass
class Road:
    points: list[tuple[float, float]]   # the road's line, in map units, in order
    join: float = 20000.0               # how near an end must be to a road to join it (map units; about 77 m)
    paint: bool = True                  # painted on the ground's picture (rusemod.groundpaint), so it shows
    bridges: bool = True                # a bridge where it crosses water (rusemod.bridges), so units can cross


def parse_roads(items, where: str = "roads.toml") -> list[Road]:
    out = []
    for n, r in enumerate(items or [], start=1):
        at = f"{where}: road {n}"
        if not isinstance(r, dict):
            raise RoadNetError(f"{at} isn't a table")
        extra = sorted(set(r) - {"points", "join", "paint", "bridges"})
        if extra:
            raise RoadNetError(f"{at}: unknown key {extra[0]!r}")
        pts = r.get("points")
        if not isinstance(pts, list) or len(pts) < 2:
            raise RoadNetError(f"{at}: points must list at least two [x, y] places")
        line = []
        for p in pts:
            if (not isinstance(p, list) or len(p) != 2
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in p)):
                raise RoadNetError(f"{at}: every point is [x, y], two numbers")
            line.append((float(p[0]), float(p[1])))
        join = r.get("join", 20000.0)
        if isinstance(join, bool) or not isinstance(join, (int, float)) or not 0 <= join <= 200000:
            raise RoadNetError(f"{at}: join must be a number from 0 to 200000")
        flags = [r.get("paint", True), r.get("bridges", True)]
        if not all(isinstance(f, bool) for f in flags):
            raise RoadNetError(f"{at}: paint and bridges must be true or false")
        out.append(Road(line, float(join), *flags))
    return out


def roads_toml(roads: list[Road], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for r in roads:
        pts = ", ".join(f"[{x!r}, {y!r}]" for x, y in r.points)
        lines += (["[[road]]", f"points = [{pts}]", f"join = {r.join!r}"] + ([] if r.paint else ["paint = false"])
                  + ([] if r.bridges else ["bridges = false"]) + [""])
    return "\n".join(lines)


def apply_roads(read, pack: str, roads: list[Road]) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map: its road network with `roads` added; `read(member)` gives a
    DataMap_Win.dat file's bytes or None (the build's chain, so earlier edits to the same file stay)."""
    from ruse_mod_engine import sdb
    from .cover import PACK, member
    from .nav import replace_buffers
    name = member(pack)
    win = read(name)
    if win is None:
        raise RoadNetError(f"{pack} has no {name} in {PACK}, so no road can be added")
    net = RoadNet.read(sdb.split_mapinfo(win)[1][0])
    notes = []
    for n, r in enumerate(roads, start=1):
        got = net.add_road(r.points, r.join)
        notes.append(f"road {n}: {got['points']} point(s), {got['links']} link(s), joined at {got['joined']} end(s)")
    return {name: replace_buffers(win, {0: net.to_bytes()})}, notes


# --- the index ---
def _tree_read(data: bytes, q: int):
    tag = struct.unpack_from("<H", data, q)[0]
    if tag & 1:
        word, split = struct.unpack_from("<Hf", data, q + 2)
        if not word & 1:
            raise RoadNetError(f"a branch of the road index at {q} has an even word")
        jump = ((tag & 0xFFFE) << 16) + 2 * (word & 0xFFFE)
        left = q + 8
        return ["branch", split, _tree_read(data, left), _tree_read(data, left + jump)]
    return ["leaf", list(struct.unpack_from(f"<{tag // 2}H", data, q + 2))]


def _tree_write(node, top: bool = True) -> bytes:
    if node[0] == "leaf":
        return _pad(struct.pack(f"<H{len(node[1])}H", 2 * len(node[1]), *node[1]))
    _, split, left, right = node
    lb = _tree_write(left, False)
    jump = len(lb)
    out = struct.pack("<HHf", 1 | ((jump >> 16) & 0xFFFE), ((jump & 0x1FFFF) // 2) | 1, split) + lb + _tree_write(right, False)
    return _pad(out) if top else out


def build_tree(points: list[tuple[float, float]], links: list[tuple[int, int, int]], depth: int = 0,
               ids: list[int] | None = None):
    """A k-d tree over the links, split the game's way: x at even depths, y at odd ones, at the middle of the links'
    midpoints; a link crossing the split goes to both halves; a leaf holds at most LEAF_MOST links (or stops
    shrinking)."""
    ids = list(range(len(links))) if ids is None else ids
    if len(ids) <= LEAF_MOST or depth > 40:
        return ["leaf", sorted(ids)]
    axis = depth % 2
    ends = {i: (points[links[i][0]][axis], points[links[i][1]][axis]) for i in ids}
    mids = sorted((a + b) / 2 for a, b in ends.values())
    split = mids[len(mids) // 2]
    left = [i for i in ids if min(ends[i]) <= split]
    right = [i for i in ids if max(ends[i]) >= split]
    if len(left) == len(ids) and len(right) == len(ids):  # every link crosses: splitting can't help
        return ["leaf", sorted(ids)]
    split = struct.unpack("<f", struct.pack("<f", split))[0]  # as the file keeps it
    return ["branch", split, build_tree(points, links, depth + 1, left), build_tree(points, links, depth + 1, right)]
