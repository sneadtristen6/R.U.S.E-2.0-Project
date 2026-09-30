"""Bridges where a mod's new road crosses water (maps/<map>/roads.toml, `bridges = true`, the default).

A road's line is walked over the map's ground mesh; where it runs over the water triangles (the mesh's list 1), that
run, plus a stretch of bank at each end, is a crossing. On it the build places the map's own bridge kind, end to end
at its real size (the game only takes a scenery type the map already uses; 24 of the 32 maps ship one, the rest
get a note and no bridge), walk-through so units can drive on it, and opens the movement graphs along the deck
(rusemod.nav Graph.open). The road network already runs across (rusemod.roadnet), and the ground painter leaves the
deck unpainted. Not tried in the game yet.
"""
from __future__ import annotations

import math

from .scenery import NewObject, is_bridge
from .tms import Tms

BANK = 2500.0        # map units of bank each end of a bridge stands on (about 10 m)
SAMPLE = 800.0       # map units between the places a road is tested for water
LEAST = 1500.0       # a run of water shorter than this is a puddle: no bridge
DECK = 2560.0        # the movement circles' radius on a bridge (the shipped bridges' circles are 2,240-3,520)
FALLBACK_LENGTH = 8000.0  # a bridge model's length when its model can't be measured (about 30 m)


class BridgeError(ValueError):
    pass


class Water:
    """Where a map's ground mesh has water: its cells' water triangles (list 1), bucketed by place."""

    def __init__(self, mesh: Tms, bucket: float = 16384.0):
        self.bucket = bucket
        self.grid: dict[tuple[int, int], list] = {}
        for c in mesh.cells:
            tri = c.triangles(1)
            if not tri:
                continue
            pos = c.positions()
            pts = [(mesh.to_world(0, p[0]), mesh.to_world(1, p[1])) for p in pos]
            for t in range(0, len(tri), 3):
                p = [pts[v] for v in tri[t:t + 3]]
                x0, x1 = min(q[0] for q in p), max(q[0] for q in p)
                y0, y1 = min(q[1] for q in p), max(q[1] for q in p)
                for gx in range(int(x0 // bucket), int(x1 // bucket) + 1):
                    for gy in range(int(y0 // bucket), int(y1 // bucket) + 1):
                        self.grid.setdefault((gx, gy), []).append(p)

    def at(self, x: float, y: float) -> bool:
        for a, b, c in self.grid.get((int(x // self.bucket), int(y // self.bucket)), ()):
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if den == 0:
                continue
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
            if l1 >= -1e-9 and l2 >= -1e-9 and 1.0 - l1 - l2 >= -1e-9:
                return True
        return False


def _along(line, dist: float) -> tuple[float, float]:
    """The point `dist` map units along the polyline `line` (its end past its length)."""
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        seg = math.hypot(bx - ax, by - ay)
        if dist <= seg or seg == 0:
            t = 0.0 if seg == 0 else max(0.0, dist / seg)
            return (ax + (bx - ax) * t, ay + (by - ay) * t)
        dist -= seg
    return tuple(map(float, line[-1]))


def crossings(water: Water, line, sample: float = SAMPLE, bank: float = BANK, least: float = LEAST) -> list[tuple]:
    """Where the road `line` (map points, in order) crosses water: [(x0, y0, x1, y1)], each run of water along the
    line longer than `least`, stretched by `bank` onto the ground at both ends (never past the road's ends)."""
    if len(line) < 2:
        return []
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(line, line[1:]))
    if total <= 0:
        return []
    n = max(1, int(total // sample))
    wet = [water.at(*_along(line, total * k / n)) for k in range(n + 1)]
    out, k = [], 0
    while k <= n:
        if not wet[k]:
            k += 1
            continue
        start = k
        while k <= n and wet[k]:
            k += 1
        d0, d1 = total * start / n, total * (k - 1) / n
        if d1 - d0 + sample < least:
            continue
        out.append(_along(line, max(0.0, d0 - sample / 2 - bank)) + _along(line, min(total, d1 + sample / 2 + bank)))
    return out


def bridge_type(names: list[str], counts: dict[int, int], descs: dict) -> str | None:
    """The map's own bridge kind: a scenery type it uses whose editor category is a bridge one (…/Ponts), the ones
    with a floor (…_TangeantFloor, what the shipped maps place) first, then the most used."""
    found = []
    for i, name in enumerate(names):
        d = descs.get(name)
        if d is None or not is_bridge(d.category):
            continue
        found.append((0 if name.lower().endswith("_tangeantfloor") else 1, -counts.get(i, 0), name))
    return min(found)[2] if found else None


def model_length(game, descs: dict, type_name: str) -> tuple[float, float]:
    """(the bridge model's length along its longer side, the turn in degrees that puts that side along x)."""
    from pathlib import Path
    from .models import Library
    d = descs.get(type_name)
    if d is None:
        return FALLBACK_LENGTH, 0.0
    lib = Library(Path(game))
    try:
        best = (0.0, 0.0)
        for model in (d.models or ([d.model] if d.model else [])):
            name = lib.find(model)
            if name is None:
                continue
            xs, ys = [], []
            for part, _tex in lib.parts(name):
                pos = part.positions
                xs += pos[0::3]
                ys += pos[1::3]
            if xs:
                best = max(best, (max(xs) - min(xs), 0.0), (max(ys) - min(ys), 90.0))
    finally:
        lib.close()
    return best if best[0] > 0 else (FALLBACK_LENGTH, 0.0)


def bridge_objects(type_name: str, span: tuple, length: float, extra_turn: float = 0.0) -> list[NewObject]:
    """Bridges of `type_name` end to end along `span`, each at its real size, turned along it (NewObject's turn:
    degrees from east toward south, as the road's direction is in map coordinates), walk-through."""
    x0, y0, x1, y1 = span
    total = math.hypot(x1 - x0, y1 - y0)
    if total <= 0 or length <= 0:
        return []
    count = max(1, math.ceil(total / length - 0.15))  # a short overhang onto the bank rather than a gap
    turn = (math.degrees(math.atan2(y1 - y0, x1 - x0)) + extra_turn) % 360
    ux, uy = (x1 - x0) / total, (y1 - y0) / total
    out = []
    for k in range(count):
        d = (k + 0.5) * total / count
        out.append(NewObject(type_name, x0 + ux * d, y0 + uy * d, round(turn, 2), 1.0, False))
    return out


def cut(lines, spans) -> list:
    """`lines` with the parts inside `spans` (bridges) left out, for the ground painter: a line is split where it
    enters and leaves a span's box along it."""
    out = []
    for line in lines:
        cur = []
        for (ax, ay), (bx, by) in zip(line, line[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) // (SAMPLE / 2)))
            for k in range(n + 1):
                t = k / n
                p = (ax + (bx - ax) * t, ay + (by - ay) * t)
                if _on_span(p, spans):
                    if len(cur) >= 2:
                        out.append(cur)
                    cur = []
                elif not cur or cur[-1] != p:
                    cur.append(p)
        if len(cur) >= 2:
            out.append(cur)
    return out


def _on_span(p, spans) -> bool:
    for x0, y0, x1, y1 in spans:
        dx, dy = x1 - x0, y1 - y0
        n = dx * dx + dy * dy
        if n == 0:
            continue
        t = ((p[0] - x0) * dx + (p[1] - y0) * dy) / n
        if 0.0 <= t <= 1.0 and math.hypot(p[0] - x0 - t * dx, p[1] - y0 - t * dy) <= DECK / 2:
            return True
    return False


def placed_spans(objects, descs: dict, length_of) -> list[tuple]:
    """The decks of the bridges a mod places by hand (scenery.toml objects of a bridge kind, any size): each one's
    model length times its size, along its turn (less the model's own axis turn from `length_of`), as (x0, y0, x1,
    y1). Placed like buildings, they're coded as bridges: they open the ground along them instead of blocking it."""
    out = []
    for o in objects:
        d = descs.get(o.type)
        if d is None or not is_bridge(d.category):
            continue
        length, extra = length_of(o.type)
        a = math.radians(o.turn - extra)
        half = length * o.size / 2
        out.append((o.x - math.cos(a) * half, o.y - math.sin(a) * half, o.x + math.cos(a) * half, o.y + math.sin(a) * half))
    return out


def _covered(span, existing) -> bool:
    """A crossing a bridge placed by hand already spans (its middle on that bridge's deck)."""
    mx, my = (span[0] + span[2]) / 2, (span[1] + span[3]) / 2
    for x0, y0, x1, y1 in existing:
        dx, dy = x1 - x0, y1 - y0
        n = dx * dx + dy * dy
        if n == 0:
            continue
        t = ((mx - x0) * dx + (my - y0) * dy) / n
        if -0.25 <= t <= 1.25 and math.hypot(mx - x0 - t * dx, my - y0 - t * dy) <= DECK * 2:
            return True
    return False


def plan(mesh: bytes, lines, sc, descs: dict, length_of=None, game=None, sample: float = SAMPLE, bank: float = BANK,
         least: float = LEAST, existing=()) -> tuple[list, list, list[str]]:
    """The bridges for `lines` (the roads' lines) on a map: (the bridge objects to place, the spans to open for
    movement (x0, y0, x1, y1), notes). `sc` is the map's rusemod.scenery.Scenery, `descs` the scenery descriptors;
    the bridge model's length comes from `length_of(type name)` or, without it, the game's model files. A crossing
    one of the `existing` spans (bridges placed by hand) already covers gets nothing more."""
    water = Water(Tms(mesh))
    found = [span for line in lines for span in crossings(water, line, sample, bank, least)]
    spans = [s for s in found if not _covered(s, existing)]
    if not spans:
        return [], [], [f"{len(found)} water crossing(s), already bridged by hand"] if found else []
    kind = bridge_type(sc.names, sc.types(), descs)
    if kind is None:
        return [], [], [f"{len(spans)} water crossing(s), but this map has no bridge kind of its own: no bridge can go "
                        f"there, and units can't cross"]
    length, extra = length_of(kind) if length_of else model_length(game, descs, kind)
    objects = [o for span in spans for o in bridge_objects(kind, span, length, extra)]
    notes = [f"{len(spans)} water crossing(s): {len(objects)} x {kind.split('/')[-1]} placed, "
             f"{round(length / 260)} m each; movement opened along the deck"]
    return objects, spans, notes


def apply_spans(read, pack: str, spans: list[tuple]) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map: both movement graphs opened along `spans` (the bridges'
    decks); `read(member)` gives a DataMap_Win.dat file's bytes or None (the build's chain)."""
    from ruse_mod_engine import sdb
    from .cover import PACK, member
    from .nav import Graph, replace_buffers
    name = member(pack)
    win = read(name)
    if win is None:
        raise BridgeError(f"{pack} has no {name} in {PACK}, so no bridge can open its movement")
    bufs = sdb.split_mapinfo(win)[1]
    new, notes = {}, []
    for k, what in ((1, "infantry"), (2, "vehicles")):
        g = Graph.read(bufs[k])
        c = g.open(spans, DECK)
        new[k] = g.to_bytes()
        notes.append(f"{what}: {c['added']} circle(s) and {c['linked']} link(s) added along {len(spans)} bridge(s)")
    return {name: replace_buffers(win, new)}, notes
