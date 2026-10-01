"""Bridges where a mod's new road crosses water (maps/<map>/roads.toml, `bridges = true`, the default).

A road's line is walked over the map's ground mesh; where it runs over the water triangles (the mesh's list 1), that
run, plus a stretch of bank at each end, is a crossing. On it the build places the map's own bridge kind (the game
only takes a scenery type the map already uses; 24 of the 32 maps ship one, the rest get a note and no bridge): ONE
bridge, centred on the water and stretched along its length so both ends rest on the banks, as every shipped bridge
does (the game sets a "TangeantFloor" bridge on the ground under its ends: one with an end over the river tips into
it), sunk to its kind's usual height, walk-through so units can drive on it. The movement graphs are opened along the
deck the way the shipped bridges' are, with local movement of its own that keeps units on it (rusemod.nav Graph.open),
it gets a floor units stand on (a shipped bridge's, rusemod.floors: without one they walk the riverbed under it), the
road network already runs across (rusemod.roadnet), and the ground painter leaves the deck unpainted.

A crossing where the map already has a bridge gets the new one in its place (owner, 2026-09-30: "if a road goes over
an existing bridge, delete the old and replace it with the new one"): the old one is sunk out of sight
(scenery.bury_objects), and its deck, where it's over water and off the new deck, is closed to units and to the road
network.
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field

from .scenery import NewObject, is_bridge
from .tms import Tms

BANK = 2000.0        # map units of bank past the water each end of a bridge reaches, beyond half a SAMPLE (the
                     # shipped bridges reach 200 to 4,600 past the water, about 2,200 in the middle)
SAMPLE = 800.0       # map units between the places a road is tested for water
LEAST = 1500.0       # a run of water shorter than this is a puddle: no bridge
DECK = 2560.0        # a deck's width, give or take (the shipped bridges' circles are 2,240-3,520)
OPEN = 1280.0        # the movement circles on a new deck's approaches, in the main graph: the smallest the shipped
                     # main graphs use (nav.MIN_RADIUS). The deck itself gets local movement of its own, circles of
                     # nav.LOCAL_RADIUS that keep units on it (main circles along it let them step off its sides: 2,560
                     # and 1,280 both did, seen in the game 2026-09-30)
FALLBACK_LENGTH = 8000.0  # a bridge model's length when its model can't be measured (about 30 m)
STRETCH = (0.9, 2.0)  # how far a bridge is stretched along its length to fit (the shipped ones: 0.91 to 1.91)
CLOSE = 1600.0       # the radius of the ground closed along an old bridge's deck, every CLOSE / 2 over water
HOLE = 480.0         # how far from a building's or prop's middle (in a hole of the map's movement) new ground stays


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


class Ground:
    """A map's ground mesh (triangle list 0) bucketed by place: its height at a point, fast. Tms.height_at scans every
    cell (fine for a few points, 55 ms each on D-Day); a bridge floor's apron asks for thousands (rusemod.floors)."""

    def __init__(self, mesh: Tms, bucket: float = 8192.0):
        self.bucket = bucket
        self.grid: dict[tuple[int, int], list] = {}
        for k, c in enumerate(mesh.cells):
            tri = c.triangles(0)
            if not tri:
                continue
            pts = mesh.world_vertices(k)
            for t in range(0, len(tri) - 2, 3):
                p = [pts[v] for v in tri[t:t + 3]]
                x0, x1 = min(q[0] for q in p), max(q[0] for q in p)
                y0, y1 = min(q[1] for q in p), max(q[1] for q in p)
                for gx in range(int(x0 // bucket), int(x1 // bucket) + 1):
                    for gy in range(int(y0 // bucket), int(y1 // bucket) + 1):
                        self.grid.setdefault((gx, gy), []).append(p)

    def height_at(self, x: float, y: float) -> float | None:
        """The ground's height at (x, y), as Tms.height_at gives it (None off the mesh)."""
        for a, b, c in self.grid.get((int(x // self.bucket), int(y // self.bucket)), ()):
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if den == 0:
                continue
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
            l3 = 1.0 - l1 - l2
            if min(l1, l2, l3) >= -1e-9:
                return l1 * a[2] + l2 * b[2] + l3 * c[2]
        return None


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
    """The map's own bridge kind: a scenery type it uses that is a bridge (scenery.is_bridge), the ones with a floor
    (…_TangeantFloor, what the shipped maps place) first, then the most used."""
    found = []
    for i, name in enumerate(names):
        d = descs.get(name)
        if d is None or not is_bridge(d.category, name):
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


def bridge_objects(type_name: str, span: tuple, length: float, extra_turn: float = 0.0,
                   lift: float = 0.0) -> list[NewObject]:
    """One bridge of `type_name` along `span` (x0, y0, x1, y1: bank to bank), centred on it and stretched along its
    length to reach both ends (within STRETCH; none when the water is too wide for it), turned along it (NewObject's
    turn: degrees from east toward south, as the road's direction is in map coordinates), sunk by `lift`,
    walk-through. `extra_turn` is 90 for a model whose length runs along its own y (every shipped bridge), whose
    stretch is then along its length; one long on its x is sized instead."""
    x0, y0, x1, y1 = span
    total = math.hypot(x1 - x0, y1 - y0)
    if total <= 0 or length <= 0:
        return []
    need = total / length
    if need > STRETCH[1]:
        return []
    k = max(STRETCH[0], need)
    turn = round((math.degrees(math.atan2(y1 - y0, x1 - x0)) + extra_turn) % 360, 2)
    mid = ((x0 + x1) / 2, (y0 + y1) / 2)
    if extra_turn % 180 == 90:
        return [NewObject(type_name, *mid, turn, 1.0, False, round(k, 4), lift)]
    return [NewObject(type_name, *mid, turn, round(k, 4), False, 1.0, lift)]


def deck(o: NewObject, length: float, extra_turn: float) -> tuple:
    """A placed bridge's deck (x0, y0, x1, y1): its model's length through its size and stretch, along its turn less
    the model's own axis turn."""
    a = math.radians(o.turn - extra_turn)
    half = length * o.size * (o.stretch if extra_turn % 180 == 90 else 1.0) / 2
    return (o.x - math.cos(a) * half, o.y - math.sin(a) * half, o.x + math.cos(a) * half, o.y + math.sin(a) * half)


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
    """The decks of the bridges a mod places by hand (scenery.toml objects of a bridge kind, any size and stretch),
    as (x0, y0, x1, y1). Placed like buildings, they're coded as bridges: they open the ground along them instead of
    blocking it."""
    out = []
    for o in objects:
        d = descs.get(o.type)
        if d is None or not is_bridge(d.category, o.type):
            continue
        out.append(deck(o, *length_of(o.type)))
    return out


def _segment_gap(x: float, y: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / n))
    return math.hypot(x - ax - t * dx, y - ay - t * dy)


class _Points:
    """Points by place, each standing for a disc of `margin` (a building or prop the map's movement leaves a hole
    for): whether a circle reaches one."""

    def __init__(self, points, margin: float, size: float = 4096.0):
        self.margin, self.size, self.cells = margin, size, {}
        for x, y in points:
            self.cells.setdefault((int(x // size), int(y // size)), []).append((x, y))

    def within(self, x: float, y: float, r: float) -> bool:
        reach = r + self.margin
        s = self.size
        for i in range(int((x - reach) // s), int((x + reach) // s) + 1):
            for j in range(int((y - reach) // s), int((y + reach) // s) + 1):
                if any(math.hypot(px - x, py - y) < reach for px, py in self.cells.get((i, j), ())):
                    return True
        return False


def near_ends(lines, decks, along: float = 16000.0) -> list[list[tuple]]:
    """The straight pieces of the roads' `lines` that come within `along` of a deck's end (`decks`: (x0, y0, x1, y1)),
    each as a two-point line: where a deck's approach may run (nav.APPROACH), to look for what stands there."""
    ends = [p for x0, y0, x1, y1 in decks for p in ((x0, y0), (x1, y1))]
    return [[a, b] for line in lines for a, b in zip(line, line[1:])
            if ends and min(_segment_gap(ex, ey, *a, *b) for ex, ey in ends) <= along]


@dataclass
class Shipped:
    """A bridge the map ships: its kind, its deck, how far it's sunk, and where it's stored (block index, item
    offset) when it can be sunk out of sight (a block the map places once, an object stored with a transform)."""
    kind: str
    deck: tuple
    lift: float
    place: tuple | None


def shipped_bridges(sc, descs: dict, length_of) -> list[Shipped]:
    """Every bridge the map places (objects of a bridge kind), with its deck."""
    from .scenery import T_IDENTITY
    once = {}
    for bi, it, m in sc.objects_once():
        if it.tform != T_IDENTITY:
            once[(it.symbol, round(m[3]), round(m[7]))] = (bi, it.at)
    out = []
    for sym, m in sc.walk():
        name = sc.names[sym]
        d = descs.get(name)
        if d is None or not is_bridge(d.category, name):
            continue
        length, extra = length_of(name)
        col = (m[1], m[5]) if extra % 180 == 90 else (m[0], m[4])
        k = math.hypot(*col)
        if k == 0:
            continue
        half = length * k / 2
        ux, uy = col[0] / k, col[1] / k
        out.append(Shipped(name, (m[3] - ux * half, m[7] - uy * half, m[3] + ux * half, m[7] + uy * half), m[11],
                           once.get((sym, round(m[3]), round(m[7])))))
    return out


def _covered(span, existing, reach: float = DECK * 2) -> bool:
    """A crossing one of the `existing` decks already spans: its middle within `reach` of the deck's line, and no
    further along it than a quarter of the deck past either end."""
    mx, my = (span[0] + span[2]) / 2, (span[1] + span[3]) / 2
    for x0, y0, x1, y1 in existing:
        dx, dy = x1 - x0, y1 - y0
        n = dx * dx + dy * dy
        if n == 0:
            continue
        t = ((mx - x0) * dx + (my - y0) * dy) / n
        if -0.25 <= t <= 1.25 and math.hypot(mx - x0 - t * dx, my - y0 - t * dy) <= reach:
            return True
    return False


@dataclass
class Plan:
    objects: list = field(default_factory=list)   # the new bridges (NewObject)
    spans: list = field(default_factory=list)     # their decks, to open to units (x0, y0, x1, y1)
    notes: list = field(default_factory=list)
    hide: list = field(default_factory=list)      # old bridges to sink: (block index, item offset) in the scenery
    closed: list = field(default_factory=list)    # ground to close where old bridges stood over water: (x, y, r)
    kept: list = field(default_factory=list)      # decks of old bridges that stay and serve a road (not painted)
    gone: list = field(default_factory=list)      # decks of the old bridges sunk: their floors go too (floors.py)
    kind: str | None = None                       # the map's bridge kind the new ones are
    water: object = None                          # the map's water (Water), for the decks' approaches


def plan(mesh: bytes, lines, sc, descs: dict, length_of=None, game=None, sample: float = SAMPLE, bank: float = BANK,
         least: float = LEAST, existing=()) -> Plan:
    """The bridges for `lines` (the roads' lines) on a map. `sc` is the map's rusemod.scenery.Scenery, `descs` the
    scenery descriptors; a bridge model's (length, axis turn) comes from `length_of(type name)` or, without it, the
    game's model files. A crossing one of the `existing` spans (bridges placed by hand) already covers gets nothing
    more; one where the map has a bridge of its own gets the new one in its place (the old one sunk, its deck over
    water closed)."""
    if length_of is None:
        seen_lengths: dict = {}

        def length_of(kind):
            if kind not in seen_lengths:
                seen_lengths[kind] = model_length(game, descs, kind)
            return seen_lengths[kind]
    out = Plan()
    water = out.water = Water(Tms(mesh))
    found = [span for line in lines for span in crossings(water, line, sample, bank, least)]
    spans = [s for s in found if not _covered(s, existing)]
    if len(spans) < len(found):
        out.notes.append(f"{len(found) - len(spans)} water crossing(s) already bridged by hand")
    if not spans:
        return out
    kind = bridge_type(sc.names, sc.types(), descs)
    if kind is None:
        out.notes.append(f"{len(spans)} water crossing(s), but this map has no bridge kind of its own: no bridge can "
                         f"go there, and units can't cross")
        return out
    out.kind = kind
    length, extra = length_of(kind)
    shipped = shipped_bridges(sc, descs, length_of)
    lifts = sorted(b.lift for b in shipped if b.kind == kind)
    lift = lifts[len(lifts) // 2] if lifts else 0.0
    wide, kept_old, old = [], 0, []
    for span in spans:
        under = [b for b in shipped if _covered(span, [b.deck], DECK)]  # the road runs over it, within a deck
        if any(b.place is None for b in under):
            kept_old += 1  # an old bridge that can't be sunk: it stays, and serves the road
            out.kept += [b.deck for b in under]
            continue
        made = bridge_objects(kind, span, length, extra, lift)
        if not made:
            wide.append(math.hypot(span[2] - span[0], span[3] - span[1]))
            continue
        out.objects += made
        out.spans.append(deck(made[0], length, extra))
        old += under
    if out.objects:
        out.notes.append(f"{len(out.objects)} water crossing(s): {len(out.objects)} x {kind.split('/')[-1]} placed, "
                         f"stretched to reach both banks; movement opened along the deck")
    if old:
        places = []
        for b in old:
            if b.place in places:
                continue
            places.append(b.place)
            out.gone.append(b.deck)
            out.closed += _closing(water, b.deck, out.spans)
        out.hide = places
        out.notes.append(f"{len(places)} old bridge(s) replaced: sunk out of sight, their decks over water closed to "
                         f"units and roads")
    if kept_old:
        out.notes.append(f"{kept_old} crossing(s) on an old bridge the map places in several places at once: it "
                         f"can't be taken away, so it stays and serves the road")
    if wide:
        out.notes.append(f"{len(wide)} crossing(s) too wide for {kind.split('/')[-1]} (at most "
                         f"{round(length * STRETCH[1] / 260)} m bank to bank, these are "
                         f"{', '.join(str(round(w / 260)) for w in wide)} m): no bridge, and units can't cross there")
    return out


def _closing(water: Water, old: tuple, new_decks: list) -> list[tuple]:
    """Circles (x, y, CLOSE) along an old bridge's deck, where it's over water and off the new decks."""
    x0, y0, x1, y1 = old
    total = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(total // (CLOSE / 2)))
    out = []
    for k in range(n + 1):
        p = (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)
        if water.at(*p) and not _on_span(p, new_decks):
            out.append((p[0], p[1], CLOSE))
    return out


def _end_name(dx: float, dy: float) -> str:
    """The compass end of a deck its outward direction (dx, dy) points to (map x grows east, y south)."""
    return ("east" if dx > 0 else "west") if abs(dx) >= abs(dy) else ("south" if dy > 0 else "north")


def _opened_notes(what: str, spans: list[tuple], c: dict) -> list[str]:
    """The build's notes on one movement graph opened along `spans` (`c`: what nav.Graph.open returned)."""
    from .nav import APPROACH, DECK_RADIUS, METRE
    out = []
    owners, inside = c["owners"], c["inside"]
    opened = len(spans) - len(c["closed"]) - len(c["crowded"])
    if not owners and not inside and c["added"] and opened > 0:  # the deck as narrow main circles (open_narrow)
        line = (f"{what}: {opened} bridge(s) opened, units kept to the deck ({c['added']} circle(s) "
                f"{round(2 * DECK_RADIUS / METRE)} m wide along it, narrower than the floor they stand on)")
        if c["approach"]:
            line += (f"; {c['approach']} circle(s) on the approaches to them (the longest "
                     f"{round(c['longest'] / METRE)} m along the road)")
        out.append(line)
    if owners or inside:
        how = []
        if owners:
            how.append(f"{len(owners)} with local movement of its own (a circle "
                       f"{', '.join(str(round(2 * r / METRE)) for _si, _k, r, _n in owners)} m across over the "
                       f"crossing, {sum(n for _si, _k, _r, n in owners)} circle(s) in its local movement)")
        if inside:
            how.append(f"{len(inside)} in the local movement already there (an old bridge's or a town's)")
        line = f"{what}: {len(owners) + len(inside)} bridge(s) opened, units kept to the deck: " + "; ".join(how)
        if c["approach"]:
            line += (f"; {c['approach']} circle(s) on the approaches to them (the longest "
                     f"{round(c['longest'] / METRE)} m along the road)")
        if c["under"]:
            line += f"; {c['under']} circle(s) of old decks under them taken away"
        if c["left_out"]:
            line += f"; {c['left_out']} patch(es) of ground beside them out of reach, left out of it"
        out.append(line)
    for si, ends in c["closed"]:
        x0, y0, x1, y1 = spans[si]
        where = " and ".join(_end_name(*((x0 - x1, y0 - y1) if e == 0 else (x1 - x0, y1 - y0))) for e in ends)
        met = []
        for e in ends:
            stop = c.get("stopped", {}).get((si, e))
            if stop is not None:
                px, py, walked, why = stop
                name = _end_name(*((x0 - x1, y0 - y1) if e == 0 else (x1 - x0, y1 - y0)))
                met.append(f"{round(walked / METRE)} m past its {name} end the road meets {why}, at ({px:.0f}, {py:.0f})")
        out.append(f"{what} can't use the bridge at ({(x0 + x1) / 2:.0f}, {(y0 + y1) / 2:.0f}): past its {where} "
                   f"end, no ground they already use lies within {round(APPROACH / METRE)} m along the road"
                   + (f" ({'; '.join(met)}: move the road clear of it)" if met else "")
                   + ", so it's left closed to them (ground they can't reach from the rest crashes the game)")
    for si in c["crowded"]:
        x0, y0, x1, y1 = spans[si]
        out.append(f"{what} can't use the bridge at ({(x0 + x1) / 2:.0f}, {(y0 + y1) / 2:.0f}): other ground lies too "
                   f"close to it for the local movement that keeps units on a deck, so it's left closed to them "
                   f"(without it they step off its sides)")
    return out


def apply_spans(read, pack: str, spans: list[tuple], closed: list[tuple] = (), roads=(), blocks=(),
                water=None, obstacles=()) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map: both movement graphs closed in `closed` (circles x, y, r: where
    old bridges stood over water; an old bridge's owner circle stays, its local movement loses the old deck and
    takes the new one) and then opened along `spans` (the new bridges' decks: each in local movement of its own that
    keeps units on it, joined to the ground units already use along `roads`, the mod's road lines; nav.Graph.open),
    never through the mod's `blocks` (nav.Block), `closed`, water (`water(x, y)`: Water.at) or the holes the map's
    movement leaves for its buildings and props (`obstacles`: their (x, y); one counts for a graph where that graph
    keeps units off its middle: the owner's D-Day test, 2026-09-30, had an approach through a farm), and the road
    network's links through `closed` taken away; `read(member)` gives a DataMap_Win.dat file's bytes or None (the
    build's chain). Raises BridgeError rather than write a graph, or one of its local graphs, in more pieces than it
    was."""
    from ruse_mod_engine import sdb
    from .cover import PACK, member
    from .nav import DECK_RADIUS as DECK, UNITS, Graph, replace_buffers
    from .roadnet import RoadNet
    name = member(pack)
    win = read(name)
    if win is None:
        raise BridgeError(f"{pack} has no {name} in {PACK}, so no bridge can open its movement")
    bufs = sdb.split_mapinfo(win)[1]
    new, notes, number, road_note = {}, [], {}, None
    if closed:  # first, so the graphs' crossings can follow the road links' new numbers
        net = RoadNet.read(bufs[0])
        gone = net.cut(list(closed), number)
        new[0] = net.to_bytes()
        road_note = f"road network: {gone} link(s) taken off the old bridges"
        if not gone:
            number = {}
    for k, what in ((1, "infantry"), (2, "vehicles")):
        g = Graph.read(bufs[k])
        pieces = [len(s.parts()) for s in [g] + g.subs]
        if closed:  # (an old bridge's owner stays: its local movement takes the new deck)
            c = g.block(list(closed), refill=False, keep_owners=True)
            notes.append(f"{what}: {c['emptied']} circle(s) taken and {c['shrunk']} shrunk where old bridges stood")
        if number:
            g.renumber_roads(number)  # a crossing names road links by number (the road through its circle)
        zones = [(b.x, b.y, b.radius) for b in blocks if k in UNITS[b.units]] + list(closed)
        holes = _Points([(x, y) for x, y in obstacles if not g.walkable(x, y)], HOLE)

        def avoid(x, y, r, zones=zones, holes=holes):
            return any(math.hypot(x - zx, y - zy) < zr + r for zx, zy, zr in zones) or holes.within(x, y, r)
        c = g.open_narrow(spans, DECK, roads, avoid=avoid, water=water) if spans else None
        if any(len(s.parts()) > n for s, n in zip([g] + g.subs, pieces)):  # e.g. an old bridge, the only way across
            raise BridgeError(f"{what}: taking the old bridges away would cut ground off from the rest of the map "
                              f"(or of a bridge's own local movement), and the game crashes when a unit is ordered "
                              f"onto ground it can't reach")
        new[k] = g.to_bytes()
        if c is not None:
            notes += _opened_notes(what, spans, c)
    if road_note:
        notes.append(road_note)
    return {name: replace_buffers(win, new)}, notes
