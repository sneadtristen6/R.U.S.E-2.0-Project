"""The map check, for the Studio: what will go wrong on a map with a mod's changes, found before the game starts (the
movement probes, made for players). The map is built as Test in game builds it, into a folder that's removed
afterwards; the game's own folder is only read.

Checked on the built map's movement (rusemod.nav), for infantry and vehicles:

- pieces: every graph, and each of its local graphs, is one piece, as every shipped graph is; ground cut off from the
  rest crashes the game when a unit is ordered onto it;
- roads: each of the mod's new roads, walked every STEP map units: the stretches whose ground the index can't find
  (no order can be given there: water, woods for vehicles, land outside the play area), each with which units;
- bridges: each water crossing of a new road (where the build puts a bridge) and each bridge placed by hand: whether
  units get from one bank to the other along it, on ground orders can be given onto, in the main part of the graph;

and on the rest of the map:

- joins: the ends of new roads that aren't joined to the road network, which supply trucks use;
- objects: buildings and props, the map's and the mod's, standing on a new road (within ON_ROAD of its line).

A finding is shaped like rusemod.doctor's: {"key", "level": "ok" | "info" | "warn" | "fail", "say": a word in WORDS
(the apps' words.toml, filled with `data`), "data": {...}, "fix": None}; "x" and "y" in `data` (map units) are where
it is, for the map view. `data["units"]` is "infantry" or "vehicles": the UI says it with the word mc_units_<units>."""
from __future__ import annotations

import math
import tempfile
from dataclasses import replace
from pathlib import Path

from .nav import METRE, Graph, _Buckets

STEP = 500.0       # map units between the places a new road is tested
ON_ROAD = 600.0    # an object whose middle is this near a new road's line stands on it
MOST = 20          # objects on roads named one by one; the rest are counted
DECK_STEP = 640.0  # map units between the places a bridge is tested along its deck
UNITS = ((1, "infantry"), (2, "vehicles"))  # mapinfo.win's movement graphs

WORDS = {
    "mc_ok": "Nothing found that would go wrong on this map.",
    "mc_build_failed": "The map couldn't be built, so it wasn't checked: {why}",
    "mc_cut_off": "Ground around ({x}, {y}), {metres} m across, is cut off for {units}: they can't reach it from "
                  "the rest of the map, and an order onto it crashes the game.",
    "mc_road_closed": "Road {road}: {metres} m around ({x}, {y}) is ground {units} can't use.",
    "mc_bridge_closed": "The crossing at ({x}, {y}) is closed to {units}: they can't get from one bank to the other.",
    "mc_road_unjoined": "Road {road} ends at ({x}, {y}) without joining the road network. Supply trucks use the "
                        "road network.",
    "mc_object_on_road": "{name} stands on road {road} at ({x}, {y}).",
    "mc_objects_more": "{n} more objects stand on the new roads.",
    "mc_units_infantry": "infantry",
    "mc_units_vehicles": "vehicles",
    "mc_mission_link": "Mission {mission}: {why}",
    "mc_missions_unread": "The map's missions couldn't be checked: {why}",
}


def _finding(key: str, level: str, say: str, **data) -> dict:
    return {"key": key, "level": level, "say": say, "data": data, "fix": None}


def _metres(units: float) -> int:
    return max(1, round(units / METRE))


# --- the checks, on a built map's graphs, road network and roads ---------------------------------------------------
class _Parts:
    """A graph's connected parts: each circle's part, the main (largest) one, and who's linked to whom."""

    def __init__(self, g: Graph):
        self.label, sizes = g._labels()
        self.main = max(sizes, key=sizes.get) if sizes else None
        self.near = _Buckets([c[:3] for c in g.circles[:-1]])
        self.links: list[list[int]] = [[] for _ in range(len(g.circles) - 1)]
        for a, b, _x, _y in g.links:
            self.links[a].append(b)
            self.links[b].append(a)
        self.g = g

    def holding(self, x: float, y: float) -> set[int]:
        """The live circles that hold (x, y)."""
        out = set()
        for c in self.near.near(x, y, 0.0):
            cx, cy, r = self.g.circles[c][:3]
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                out.add(c)
        return out


def cut_off(g: Graph, units: str) -> list[dict]:
    """A "fail" finding for every piece of the graph, or of one of its local graphs, past the first (the largest):
    its circles, how far across it is and its middle (the mean of its circles' centres)."""
    out = []
    for sub, graph in enumerate([g] + g.subs):
        label, sizes = graph._labels()
        if len(sizes) < 2:
            continue
        main = max(sizes, key=sizes.get)
        pieces: dict[int, list] = {}
        for i, (x, y, r, _l, _c) in enumerate(graph.circles[:-1]):
            if r > 0 and label[i] != main:
                pieces.setdefault(label[i], []).append((x, y, r))
        for circles in sorted(pieces.values(), key=len, reverse=True):
            across = max(max(x + r for x, _y, r in circles) - min(x - r for x, _y, r in circles),
                         max(y + r for _x, y, r in circles) - min(y - r for _x, y, r in circles))
            out.append(_finding("pieces", "fail", "mc_cut_off", units=units, sub=sub, circles=len(circles),
                                metres=_metres(across), x=round(sum(c[0] for c in circles) / len(circles)),
                                y=round(sum(c[1] for c in circles) / len(circles))))
    return out


def _samples(line, step: float):
    """(how far along, x, y) every `step` map units along the polyline `line`, its last point included."""
    walked, target = 0.0, 0.0
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        seg = math.hypot(bx - ax, by - ay)
        while seg > 0 and target <= walked + seg:
            t = (target - walked) / seg
            yield target, ax + (bx - ax) * t, ay + (by - ay) * t
            target += step
        walked += seg
    if target - step < walked:  # the end, when the steps stopped short of it
        yield walked, float(line[-1][0]), float(line[-1][1])


def _point_at(line, dist: float) -> tuple[float, float]:
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        seg = math.hypot(bx - ax, by - ay)
        if dist <= seg and seg > 0:
            return ax + (bx - ax) * dist / seg, ay + (by - ay) * dist / seg
        dist -= seg
    return float(line[-1][0]), float(line[-1][1])


def _on_deck(x: float, y: float, decks, half: float) -> bool:
    for x0, y0, x1, y1 in decks:
        dx, dy = x1 - x0, y1 - y0
        n = dx * dx + dy * dy
        if n == 0:
            continue
        t = ((x - x0) * dx + (y - y0) * dy) / n
        if 0.0 <= t <= 1.0 and math.hypot(x - x0 - t * dx, y - y0 - t * dy) <= half:
            return True
    return False


def closed_roads(g: Graph, lines, units: str, decks=(), step: float = STEP) -> list[dict]:
    """A "warn" finding for every stretch of a new road (`lines`: each road's map points, in order) where the graph's
    index finds no ground (Graph.find is None: no order can be given there), walked every `step`: its length, its
    middle and the road's number (from 1). Places on `decks` (x0, y0, x1, y1: the bridges, which closed_bridges
    checks) are left out. Which units can't use it is said, not judged: vehicles keep out of woods on purpose."""
    from .bridges import DECK
    out = []
    for n, line in enumerate(lines, start=1):
        if len(line) < 2:
            continue
        total = sum(math.dist(a, b) for a, b in zip(line, line[1:]))
        run: list[float] = []

        def close():
            if run:
                mid = _point_at(line, (run[0] + run[-1]) / 2)
                out.append(_finding("road", "warn", "mc_road_closed", units=units, road=n,
                                    metres=_metres(min(total, run[-1] - run[0] + step)), x=round(mid[0]),
                                    y=round(mid[1])))
                run.clear()
        for walked, x, y in _samples(line, step):
            if _on_deck(x, y, decks, DECK / 2):
                close()
            elif g.find(x, y) is None:
                run.append(walked)
            else:
                close()
        close()
    return out


def crossable(g: Graph, deck, parts: _Parts | None = None, step: float = DECK_STEP) -> bool:
    """Whether units get along `deck` (x0, y0, x1, y1) from one end to the other: a way through the circles that hold
    places along it, from those holding its first end to those holding its last, in the graph's main part, and its
    middle on ground the index finds (an order can be given onto it)."""
    parts = parts or _Parts(g)
    x0, y0, x1, y1 = deck
    n = max(1, math.ceil(math.hypot(x1 - x0, y1 - y0) / step))
    held = [parts.holding(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n + 1)]
    start = {c for c in held[0] if parts.label[c] == parts.main}  # a way keeps to one part
    goal, allowed = held[-1], set().union(*held)
    seen, todo = set(start), list(start)
    while todo and not seen & goal:
        c = todo.pop()
        for d in parts.links[c]:
            if d in allowed and d not in seen:
                seen.add(d)
                todo.append(d)
    if not seen & goal:
        return False
    found = g.find((x0 + x1) / 2, (y0 + y1) / 2)
    return found is not None and parts.label[found] == parts.main


def closed_bridges(g: Graph, decks, units: str) -> list[dict]:
    """A "fail" finding for every bridge units can't cross (crossable): `decks` are (x0, y0, x1, y1, road number,
    or 0 for a bridge placed by hand)."""
    parts = _Parts(g) if decks else None
    out = []
    for x0, y0, x1, y1, road in decks:
        if not crossable(g, (x0, y0, x1, y1), parts):
            out.append(_finding("bridge", "fail", "mc_bridge_closed", units=units, road=road,
                                metres=_metres(math.hypot(x1 - x0, y1 - y0)), x=round((x0 + x1) / 2),
                                y=round((y0 + y1) / 2)))
    return out


def unjoined(net, lines) -> list[dict]:
    """An "info" finding for every end of a new road that isn't joined to the road network: `net` is the built road
    network (rusemod.roadnet.RoadNet), `lines` the roads' map points in the order the build added them. The build
    adds each road's points at the end of the network (RoadNet.add_road), so a road's points are found there; an end
    is joined when it's linked to a point that isn't the road's own. A network that doesn't end with the roads'
    points (not built from them) gives no findings."""
    from .roadnet import POINT_STEP, _resample
    counts = [len(_resample(line, POINT_STEP)) for line in lines if len(line) >= 2]
    first = len(net.points) - sum(counts)
    if first < 0:
        return []
    ranges, at = [], first
    for line, k in zip([ln for ln in lines if len(ln) >= 2], counts):
        mine = net.points[at:at + k]
        if math.dist(mine[0], line[0]) > 1.0 or math.dist(mine[-1], line[-1]) > 1.0:
            return []
        ranges.append((at, at + k - 1))
        at += k
    linked: dict[int, set[int]] = {}
    for a, b, _cost in net.links:
        linked.setdefault(a, set()).add(b)
        linked.setdefault(b, set()).add(a)
    out = []
    numbers = [n for n, line in enumerate(lines, start=1) if len(line) >= 2]
    for n, (lo, hi) in zip(numbers, ranges):
        for end in (lo, hi):
            if not any(p < lo or p > hi for p in linked.get(end, ())):
                x, y = net.points[end]
                out.append(_finding("join", "info", "mc_road_unjoined", road=n, x=round(x), y=round(y)))
    return out


class _Lines:
    """The new roads' straight pieces by place, for what stands near them."""

    def __init__(self, lines, reach: float = ON_ROAD, size: float = 8192.0):
        self.reach, self.size, self.cells, self.pieces = reach, size, {}, []
        for n, line in enumerate(lines, start=1):
            for (ax, ay), (bx, by) in zip(line, line[1:]):
                k = len(self.pieces)
                self.pieces.append((n, ax, ay, bx, by))
                for key in self._keys(min(ax, bx) - reach, min(ay, by) - reach, max(ax, bx) + reach,
                                      max(ay, by) + reach):
                    self.cells.setdefault(key, []).append(k)

    def _keys(self, x0, y0, x1, y1):
        s = self.size
        return [(i, j) for i in range(int(x0 // s), int(x1 // s) + 1) for j in range(int(y0 // s), int(y1 // s) + 1)]

    def touches(self, box) -> bool:
        """Whether something in `box` (x0, y0, x1, y1) may be within reach of a road."""
        x0, y0, x1, y1 = box
        s = self.size
        i0, i1, j0, j1 = int(x0 // s), int(x1 // s), int(y0 // s), int(y1 // s)
        if (i1 - i0 + 1) * (j1 - j0 + 1) > len(self.cells):
            return any(i0 <= i <= i1 and j0 <= j <= j1 for i, j in self.cells)
        return any((i, j) in self.cells for i in range(i0, i1 + 1) for j in range(j0, j1 + 1))

    def nearest(self, x: float, y: float) -> tuple[float, int] | None:
        """(how far, the road's number) of the road nearest (x, y), when one is within reach."""
        best = None
        for k in self.cells.get((int(x // self.size), int(y // self.size)), ()):
            n, ax, ay, bx, by = self.pieces[k]
            dx, dy = bx - ax, by - ay
            m = dx * dx + dy * dy
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / m)) if m else 0.0
            d = math.hypot(x - ax - t * dx, y - ay - t * dy)
            if d <= self.reach and (best is None or d < best[0]):
                best = (d, n)
        return best


def on_roads(objects, lines, reach: float = ON_ROAD, most: int = MOST) -> list[dict]:
    """"info" findings for the `objects` ((type name, x, y, group: building or prop)) whose middle is within `reach`
    of a new road's line: buildings first, then the nearest; at most `most`, and a count of the rest."""
    near = _Lines(lines, reach)
    hits = []
    for name, x, y, group in objects:
        got = near.nearest(x, y)
        if got is not None:
            hits.append((group != "building", got[0], name, x, y, got[1], group))
    hits.sort(key=lambda h: h[:2])
    out = [_finding("object", "info", "mc_object_on_road", type=name, name=name.split("/")[-1], group=group, road=n,
                    x=round(x), y=round(y))
           for _later, _d, name, x, y, n, group in hits[:most]]
    if len(hits) > most:
        out.append(_finding("object", "info", "mc_objects_more", n=len(hits) - most))
    return out


def map_objects(sc, descs: dict, lines, reach: float = ON_ROAD):
    """(type name, x, y, group) for the buildings and props of the map's scenery (rusemod.scenery.Scenery; `descs`
    its descriptors, bridges left out) that may be within `reach` of `lines`. A map places millions of objects
    (Blitz: 5 million, most of them vegetation), so the walk only goes into blocks that hold a building or a prop
    whose place comes near a road: each block's box of those, its children's included, is worked out once."""
    from .scenery import IDENTITY, compose
    wanted = {}
    for sym, name in enumerate(sc.names):
        d = descs.get(name)
        if d is not None and d.group in ("building", "prop") and not d.bridge:
            wanted[sym] = d.group
    near = _Lines(lines, reach)
    if not wanted or not near.cells:
        return

    def moved(box, m):
        xs, ys = [], []
        for px, py in ((box[0], box[1]), (box[0], box[3]), (box[2], box[1]), (box[2], box[3])):
            xs.append(m[0] * px + m[1] * py + m[3])
            ys.append(m[4] * px + m[5] * py + m[7])
        return min(xs), min(ys), max(xs), max(ys)

    def grow(box, other):
        return other if box is None else (min(box[0], other[0]), min(box[1], other[1]), max(box[2], other[2]),
                                          max(box[3], other[3]))
    boxes: list = [None] * len(sc.blocks)
    for b in reversed(sc.blocks):  # children are stored after their parents
        box = None
        for it in b.items:
            if it.kind == "object" and it.symbol in wanted:
                m = it.matrix()
                box = grow(box, (m[3], m[7], m[3], m[7]))
            elif it.kind == "child":
                inner = boxes[sc._by_offset[it.child_offset]]
                if inner is not None:
                    box = grow(box, moved(inner, it.matrix()))
        boxes[b.index] = box
    todo = [(r, IDENTITY) for r in sc.roots() if boxes[r] is not None and near.touches(boxes[r])]
    while todo:
        i, m = todo.pop()
        for it in sc.blocks[i].items:
            if it.kind == "object":
                if it.symbol in wanted:
                    t = it.matrix()
                    yield (sc.names[it.symbol], m[0] * t[3] + m[1] * t[7] + m[2] * t[11] + m[3],
                           m[4] * t[3] + m[5] * t[7] + m[6] * t[11] + m[7], wanted[it.symbol])
            elif it.kind == "child":
                j = sc._by_offset[it.child_offset]
                if boxes[j] is not None:
                    cm = compose(m, it.matrix())
                    if near.touches(moved(boxes[j], cm)):
                        todo.append((j, cm))


def check_built(win: bytes, lines, decks=(), objects=()) -> list[dict]:
    """Every check on a built map: `win` its mapinfo.win, `lines` the mod's roads (map points, in the order the build
    added them), `decks` its bridges ((x0, y0, x1, y1, road number or 0)), `objects` what stands near the roads
    ((type name, x, y, group): map_objects and the mod's own)."""
    from ruse_mod_engine import sdb
    from .roadnet import RoadNet
    parts = sdb.split_mapinfo(win)
    if parts is None:
        return [_finding("build", "fail", "mc_build_failed", why="its mapinfo.win can't be read")]
    bufs = parts[1]
    out = []
    spans = [d[:4] for d in decks]
    for k, units in UNITS:
        g = Graph.read(bufs[k])
        out += cut_off(g, units)
        out += closed_bridges(g, decks, units)
        out += closed_roads(g, lines, units, spans)
    if lines:
        out += unjoined(RoadNet.read(bufs[0]), lines)
        out += on_roads(objects, lines)
    return out


# --- the build: the map as Test in game would make it -----------------------------------------------------------------
def _one_map(info, pack: str):
    """The mod with only what it changes on the map `pack` that can touch its movement and roads: its ground, scenery,
    cover, movement and roads (no unit changes, texts, scenario or player counts)."""
    def only(d):
        return {k: v for k, v in d.items() if k.lower() == pack.lower()}
    return replace(info, texts=[], terrain=only(info.terrain), scenery=only(info.scenery), erase=only(info.erase),
                   scenario={}, cover=only(info.cover), movement=only(info.movement), roads=only(info.roads),
                   take_out=only(info.take_out), players={})


def _named(folder: Path, name: str) -> Path | None:
    for p in folder.iterdir() if folder.is_dir() else ():
        if p.name.lower() == name.lower():
            return p
    return None


def _member(path: Path, name: str, exact: bool = True) -> bytes | None:
    from .edat import Edat
    with Edat.open(str(path)) as arc:
        if exact:
            e = arc.entry(name)
        else:
            try:
                e = arc.find(name)
            except KeyError:
                e = None
        return bytes(arc.read(e)) if e is not None else None


def check_map(game: Path, mod_folder: Path, pack: str, say=None) -> list[dict]:
    """The map check for the map `pack` (its pack name, e.g. SuperCrossRoads4) with the mod in `mod_folder`: the mod
    is built as Test in game builds it (rusemod.build, its changes to this map only) into a folder removed
    afterwards, and the built map checked (check_built). `say` gets the build's report lines. Findings, or one "ok"
    finding when there's nothing to say; a build with errors gives one "fail" finding with the first."""
    from .bridges import Water, _covered, crossings, model_length, placed_spans
    from .build import DEFAULT_PACK, BuildError, build_and_write, build_cache, find_pack, load_mod
    from .cover import PACK, member
    from .edat import Edat
    from .rndf import RndfError
    from .scenery import MEMBER, Scenery, descriptors
    from .terrain import pack_file
    from .tms import Tms
    game = Path(game)
    try:
        info, ops = load_mod(Path(mod_folder))
    except (BuildError, RndfError) as exc:
        return [_finding("build", "fail", "mc_build_failed", why=str(exc))]
    mods = [(info, ops)] if info.rmod is not None else [(_one_map(info, pack), [])]
    roads = next((v for k, v in info.roads.items() if k.lower() == pack.lower()), []) if info.rmod is None else []
    placed = next((v for k, v in info.scenery.items() if k.lower() == pack.lower()), []) if info.rmod is None else []
    map_pack = find_pack(game, pack_file(pack))
    with tempfile.TemporaryDirectory(prefix="rusemod-mapcheck-") as tmp:
        try:
            result = build_and_write(game, mods, out=Path(tmp), say=say or (lambda _line: None), cache=build_cache())
        except BuildError as exc:  # a load order that can't be met, a pack that can't be read
            return [_finding("build", "fail", "mc_build_failed", why=str(exc))]
        if result.errors:
            return [_finding("build", "fail", "mc_build_failed", why=result.errors[0].message)]
        built = _named(Path(tmp), PACK)
        win = _member(built, member(pack)) if built is not None else None
        built_map = _named(Path(tmp), map_pack.name) if map_pack is not None else None
        mesh = _member(built_map, "output\\highdef.tms", exact=False) if built_map is not None else None
        missions = _mission_links(game, Path(tmp), pack)
    if win is None:
        data_pack = find_pack(game, PACK)
        win = _member(data_pack, member(pack)) if data_pack is not None else None
    if win is None:
        return [_finding("build", "fail", "mc_build_failed", why=f"{pack} has no {member(pack)} in {PACK}")]
    sc_raw = None
    if map_pack is not None:
        with Edat.open(str(map_pack)) as arc:  # the map as shipped: its own objects and ground
            try:
                sc_raw = bytes(arc.read(arc.find(MEMBER)))
                mesh = mesh or bytes(arc.read(arc.find("output\\highdef.tms")))
            except KeyError:
                pass
    descs = {}
    unit_pack = find_pack(game, DEFAULT_PACK)
    if unit_pack is not None and (roads or placed):
        with Edat.open(str(unit_pack)) as arc:
            descs = descriptors(arc)
    lines = [r.points for r in roads]
    hand = []
    by_hand = [o for o in placed if o.type in descs and descs[o.type].bridge]
    if by_hand:
        lengths: dict = {}

        def length_of(kind):
            if kind not in lengths:
                lengths[kind] = model_length(game, descs, kind)
            return lengths[kind]
        hand = placed_spans(by_hand, descs, length_of)
    decks = []
    if mesh is not None and any(r.bridges for r in roads):  # where the build puts a bridge (rusemod.bridges.plan):
        water = Water(Tms(mesh))                              # not where a bridge placed by hand already spans it
        for n, r in enumerate(roads, start=1):
            if r.bridges:
                decks += [span + (n,) for span in crossings(water, r.points) if not _covered(span, hand)]
    decks += [span + (0,) for span in hand]
    objects = []
    if lines and descs:
        objects += [(o.type, o.x, o.y, descs[o.type].group) for o in placed
                    if o.type in descs and descs[o.type].group in ("building", "prop") and not descs[o.type].bridge]
        if sc_raw is not None:
            objects += list(map_objects(Scenery(sc_raw), descs, lines))
    out = check_built(win, lines, decks, objects) + missions
    return out or [_finding("map", "ok", "mc_ok")]


def _mission_links(game: Path, built: Path, pack: str) -> list[dict]:
    """The map's missions (rusemod.missionsteps: LittleGroove's Load & Files), each one's chain from its menu entry to
    the mission walked in the built copy over the game: a finding for each link missing or not matching (`why`: the
    Studio words it, mission_why_<why>)."""
    from . import missionsteps
    out = []
    try:
        with missionsteps.PackStore(game, built) as store:
            for m in missionsteps.missions(store, pack):
                if m.kind not in missionsteps.KINDS:
                    continue  # no menu loads it (a test or an unused setup): nothing for a player to miss
                for link in missionsteps.chain(store, m.map_dir, m.file, m.kind)["links"]:
                    if link["state"] in ("missing", "mismatch"):
                        out.append(_finding("missions", "fail", "mc_mission_link", mission=m.file + ".scenario",
                                            why=link["why"]))
    except Exception as exc:  # his engine stopped on these files: said, and the rest of the check still shown
        out.append(_finding("missions", "warn", "mc_missions_unread", why=f"{type(exc).__name__}: {exc}"))
    return out
