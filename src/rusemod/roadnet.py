"""The road network supply trucks and units follow along a map's roads: read and written back unchanged on every
shipped map, and a mod's new roads added to it (points along the road's curve, linked in a chain and to the nearest
road at each end)."""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

HEAD = 20
LEAF_MOST = 6          # links a leaf holds before it's split (the shipped maps' leaves hold 2 to 8)
POINT_STEP = 2300.0    # map units between a new road's points (the shipped links' median, about 9 m)
MAX_DEPTH = 24         # the deepest the index goes: the game walks it with a fixed stack of 32 entries and no test
                       # of running past it (the deepest shipped index is 12 levels)


class RoadNetError(ValueError):
    pass


def cost_word(dist: float, flag: bool = True) -> int:
    """A link's cost and flag, as the game keeps them once loaded."""
    return min(int(dist / 20), 0x7FFF) << 1 | (1 if flag else 0)


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
            # not a game rule: a damaged or unexpected file
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
    def add_road(self, line: list[tuple[float, float]], join: float = 20000.0, open_at=None) -> dict:
        """Add a road along `line` (map points, in order: a new road's curve, sampled): points about POINT_STEP
        apart, linked in a chain; each end linked to the nearest road point within `join` map units (a junction),
        else left as a dead end. A new link's flag bit (cost_word) is `open_at(x, y)` at its middle: whether the
        vehicles' graph has ground there (set when it isn't given). The index is built again. Returns what was
        added."""
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
            self.links.append((a, b, self._cost(a, b, open_at)))
        self.tree = build_tree(self.points, self.links)
        return {"points": len(pts), "links": len(new_links), "joined": sum(e is not None for e in ends)}

    def cut(self, zones: list[tuple[float, float, float]], renumbered: dict | None = None) -> int:
        """Take away the links that pass through `zones` (circles x, y, r: where a bridge that's gone stood) and the
        points only they used; the other points and links are numbered again in their order, and the index is built
        again. `renumbered`, when given, is filled with {old link number: new, or None for a link that went}: the
        movement graphs' crossings name road links by number (nav.Graph.renumber_roads). Returns how many links
        went."""
        def through(link) -> bool:
            (ax, ay), (bx, by) = self.points[link[0]], self.points[link[1]]
            dx, dy = bx - ax, by - ay
            n = dx * dx + dy * dy
            for zx, zy, zr in zones:
                t = 0.0 if n == 0 else max(0.0, min(1.0, ((zx - ax) * dx + (zy - ay) * dy) / n))
                if math.hypot(ax + t * dx - zx, ay + t * dy - zy) <= zr:
                    return True
            return False
        goes = [through(link) for link in self.links]
        if renumbered is not None:
            renumbered.clear()
            renumbered.update({old: new for new, old in enumerate(i for i, g in enumerate(goes) if not g)})
            renumbered.update({i: None for i, g in enumerate(goes) if g})
        if not any(goes):
            return 0
        kept = [link for link, g in zip(self.links, goes) if not g]
        used = {p for a, b, _cost in kept for p in (a, b)}
        orphans = {p for (a, b, _cost), g in zip(self.links, goes) if g for p in (a, b)} - used
        number, points = {}, []
        for i, p in enumerate(self.points):
            if i not in orphans:
                number[i] = len(points)
                points.append(p)
        self.points = points
        self.links = [(number[a], number[b], cost) for a, b, cost in kept]
        self.tree = build_tree(self.points, self.links)
        return sum(goes)

    def parts(self) -> list[set[int]]:
        """The network's connected pieces (sets of point numbers), the largest first. Every shipped one is one piece
        (33 of 33 maps): the game's road search runs over this network alone, so a route between two pieces fails."""
        up = list(range(len(self.points)))

        def root(a):
            while up[a] != a:
                up[a] = up[up[a]]
                a = up[a]
            return a
        for a, b, _cost in self.links:
            up[root(a)] = root(b)
        pieces: dict[int, set[int]] = {}
        for i in range(len(self.points)):
            pieces.setdefault(root(i), set()).add(i)
        return sorted(pieces.values(), key=lambda p: (-len(p), min(p)))

    def _cost(self, a: int, b: int, open_at=None) -> int:
        (ax, ay), (bx, by) = self.points[a], self.points[b]
        flag = True if open_at is None else bool(open_at((ax + bx) / 2, (ay + by) / 2))
        return cost_word(math.hypot(bx - ax, by - ay), flag)

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
    keep_trees: bool = False            # the trees and bushes on its path stay (props still go): a road under the trees


def parse_roads(items, where: str = "roads.toml") -> list[Road]:
    out = []
    for n, r in enumerate(items or [], start=1):
        at = f"{where}: road {n}"
        if not isinstance(r, dict):
            raise RoadNetError(f"{at} isn't a table")
        extra = sorted(set(r) - {"points", "join", "paint", "bridges", "keep_trees"})
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
        flags = [r.get("paint", True), r.get("bridges", True), r.get("keep_trees", False)]
        if not all(isinstance(f, bool) for f in flags):
            raise RoadNetError(f"{at}: paint, bridges and keep_trees must be true or false")
        out.append(Road(line, float(join), *flags))
    return out


TAKE_OUT = ("roads", "bridges")


@dataclass(frozen=True)
class TakeOut:
    """The map's own roads and bridges a mod takes out (roads.toml `take_out`; docs/MOD_FORMAT.md §8)."""
    roads: bool = False
    bridges: bool = False

    def names(self) -> list[str]:
        return [n for n in TAKE_OUT if getattr(self, n)]


def parse_take_out(value, where: str = "roads.toml") -> list[TakeOut]:
    """A roads.toml's `take_out` (a list naming "roads", "bridges" or both) as a row for the build ([] when absent)."""
    if value is None:
        return []
    if not isinstance(value, list) or any(v not in TAKE_OUT for v in value):
        raise RoadNetError(f"{where}: take_out lists what of the map's own goes: \"roads\", \"bridges\" or both "
                           f"(got {value!r})")
    return [TakeOut("roads" in value, "bridges" in value)]


def take_out_of(rows: list) -> TakeOut:
    """What a map's mods take out between them (every mod's take_out, in load order: each adds to the others)."""
    found = [r for r in rows if isinstance(r, TakeOut)]
    return TakeOut(any(r.roads for r in found), any(r.bridges for r in found))


def take_out_roads(win: bytes) -> tuple[bytes, list[str]]:
    """The movement file (mapinfo.win) with the map's own road network taken out: no point and no link left, and
    every crossing of the two movement graphs and their local maps gone with it (a crossing names road links). With
    no road network, supply trucks and units plan their way over the ground units walk on, as for a map with no roads
    (the game turns to that when the network is empty; not seen in the game yet). The mod's own new roads are added
    after this. Returns (the file, notes); a map whose network is empty already gives the same bytes."""
    from ruse_mod_engine import sdb
    from .nav import Graph, NavError, replace_buffers
    parts = sdb.split_mapinfo(win)
    if not parts:
        raise RoadNetError("not a movement file (mapinfo.win)")
    bufs = parts[1]
    net = RoadNet.read(bufs[0])
    if not net.points and not net.links:
        return win, []
    new = {0: RoadNet([], [], ["leaf", []]).to_bytes()}
    gone = {i: None for i in range(len(net.links))}
    dropped = 0
    for k in (1, 2):
        try:
            g = Graph.read(bufs[k])
        except (NavError, struct.error):
            continue  # (no movement graph: no crossing to take out)
        n = g.renumber_roads(gone)
        if n:
            dropped += n
            new[k] = g.to_bytes()
    return replace_buffers(win, new), [f"the map's own road network taken out: {len(net.points):,} point(s) and "
                                       f"{len(net.links):,} link(s), and the movement's {dropped:,} crossing(s) of "
                                       f"them: supply trucks go across country"]


def roads_toml(roads: list[Road], header: str = "", take_out: TakeOut | None = None) -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    if take_out is not None and take_out.names():  # (a key before the tables, as TOML has it)
        named = ", ".join('"' + n + '"' for n in take_out.names())
        lines += [f"take_out = [{named}]", ""]
    for r in roads:
        pts = ", ".join(f"[{x!r}, {y!r}]" for x, y in r.points)
        lines += (["[[road]]", f"points = [{pts}]", f"join = {r.join!r}"] + ([] if r.paint else ["paint = false"])
                  + ([] if r.bridges else ["bridges = false"]) + (["keep_trees = true"] if r.keep_trees else []) + [""])
    return "\n".join(lines)


def apply_roads(read, pack: str, roads: list[Road], blocks=()) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map: its road network with `roads` added; `read(member)` gives a
    DataMap_Win.dat file's bytes or None (the build's chain, so earlier edits to the same file stay). The network
    must come out in one piece, as every shipped one is (RoadNet.parts): a road that joins no other is refused.

    Units plan along a road only through the movement graphs' crossings (nav.Graph.add_crossings), so each graph
    (buffers 1 and 2) gets crossings for the new roads through its circles, never through one of `blocks`
    (nav.Block, the map's blocks and solid buildings) the graph's units are kept out of."""
    from ruse_mod_engine import sdb
    from .cover import PACK, member
    from .nav import UNITS, Graph, NavError, replace_buffers
    name = member(pack)
    win = read(name)
    if win is None:
        raise RoadNetError(f"{pack} has no {name} in {PACK}, so no road can be added")
    bufs = sdb.split_mapinfo(win)[1]
    net = RoadNet.read(bufs[0])
    try:
        open_at = Graph.read(bufs[2]).walkable  # the vehicles' graph, as the blocks and bridges left it
    except (NavError, struct.error):
        open_at = None
    notes, spans = [], []
    old_links = len(net.links)
    for n, r in enumerate(roads, start=1):
        first = len(net.points)
        got = net.add_road(r.points, r.join, open_at)
        spans.append((n, range(first, len(net.points)), r.join))
        notes.append(f"road {n}: {got['points']} point(s), {got['links']} link(s), joined at {got['joined']} end(s)")
    pieces = net.parts()
    if len(pieces) > 1:
        main = pieces[0]
        alone = [(n, join) for n, span, join in spans if any(p not in main for p in span)]
        what = (", ".join(f"road {n} (its ends joined no road within {join / 260:.0f} m)" for n, join in alone)
                if alone else f"the map's roads (in {len(pieces)} pieces after the old bridges' roads were cut)")
        # rule: road-network-one-piece
        raise RoadNetError(f"{pack}: {what} would be cut off from the rest of the map's roads; every road network the "
                           f"game ships is one piece, and supply routes between two pieces fail. Draw each end onto a "
                           f"road, or give the road a larger join")
    new = {0: net.to_bytes()}
    fresh = set(range(old_links, len(net.links)))
    for k, what in ((1, "infantry"), (2, "vehicles")):
        try:
            g = Graph.read(bufs[k])
        except (NavError, struct.error):
            continue  # (no movement graph to follow the roads in)
        zones = [(b.x, b.y, b.radius) for b in blocks if k in UNITS[b.units]]
        got = g.add_crossings(net, fresh, zones)
        if got["added"]:
            new[k] = g.to_bytes()
        notes.append(f"{what}: {got['added']} crossing(s) in {got['circles']} circle(s), so units follow the new "
                     f"roads")
        for n, links in _links_of(spans, net, old_links):
            if not links & got["named"]:
                notes.append(f"{what}: road {n} has no crossing (it runs through no circle of the movement from one "
                             f"gate to another on open ground): units go across country there, not along it")
        if got["full"]:
            notes.append(f"{what}: {got['full']} crossing(s) left out: the movement holds no more than 65,535")
    return {name: replace_buffers(win, new)}, notes


def _links_of(spans, net: RoadNet, old_links: int):
    """(road number, {its link numbers}) of the new roads (`spans`: (number, its points' range, join)): the links
    after `old_links` that touch its points."""
    for n, points, _join in spans:
        yield n, {i for i in range(old_links, len(net.links)) if net.links[i][0] in points or net.links[i][1] in points}


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


def _tree_write(node, top: bool = True, depth: int = 0) -> bytes:
    if node[0] == "leaf":
        return _pad(struct.pack(f"<H{len(node[1])}H", 2 * len(node[1]), *node[1]))
    if depth >= MAX_DEPTH:  # a guard: the game's walk of a deeper index runs off its fixed stack
        raise RoadNetError(f"the road index would be more than {MAX_DEPTH} levels deep")
    _, split, left, right = node
    lb = _tree_write(left, False, depth + 1)
    jump = len(lb)
    out = struct.pack("<HHf", 1 | ((jump >> 16) & 0xFFFE), ((jump & 0x1FFFF) // 2) | 1, split) + lb \
        + _tree_write(right, False, depth + 1)
    return _pad(out) if top else out


def build_tree(points: list[tuple[float, float]], links: list[tuple[int, int, int]], depth: int = 0,
               ids: list[int] | None = None):
    """A k-d tree over the links, split the game's way: x at even depths, y at odd ones, at the middle of the links'
    midpoints; a link crossing the split goes to both halves; a leaf holds at most LEAF_MOST links (or stops
    shrinking, or is MAX_DEPTH down: long links crossing every split can't go deeper)."""
    ids = list(range(len(links))) if ids is None else ids
    if len(ids) <= LEAF_MOST or depth >= MAX_DEPTH:
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
