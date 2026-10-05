"""Where units can go: the navigation graphs in a map's `mapinfo.win` (DataMap_Win.dat, `datasmap\\<map>\\
mapinfo.win`, buffers 1 and 2; read with `ruse_mod_engine.sdb.split_mapinfo`).

A graph is a set of overlapping circles of ground units can use, linked where two meet: units plan from circle to
circle through the meeting points. Circle centres sit on a 320-unit grid and radii are multiples of 320 (1280 to
81920 on Blitz), the largest first. Checked on Blitz (2026-09-30):

- **Two levels.** The main graph covers the play area coarsely: water (the river, lakes) and the land outside the
  play area are what no circle covers; towns are inside it (80% of building spots). Its local graphs (22 on Blitz,
  none sharing a circle with it) each cover one town-sized patch (1 km or 200 m) finely, and their circles keep
  off the buildings: 3% of the building spots in their areas are inside them, against 52% of random spots and 64%
  of trees. So buildings are obstacles only where a local graph is; a building placed in open ground is not.
  Most bridges have a local graph too (D-Day: 16 of its 21), whose circles of radius 320 to 1,280 line the deck and
  reach no more than about 1,600 off its line, so units keep to it; the main graph passes over with one big circle.
  A few bridges have a chain of main-graph circles along the deck instead (D-Day: 3), reaching onto the land.
- **Buffer 1 is for infantry, buffer 2 for vehicles:** buffer 1 covers 79% of the woods' cells, buffer 2 14%
  (open ground: 85% and 83%). Vehicles can't enter woods.

    header       84 bytes: f32 x0, y0 (0, 0) and size (the map's side), then u16 circles, links, crossings, and
                 sub-graphs; the rest zeros
    offsets      u32 per section, from the graph's start: circles, links, lists, crossings, points, then one per
                 sub-graph
    circles      (circles + 1) × 16 bytes: f32 x, y, radius; u16 where its list starts (in the list section); u16
                 where its crossings start. The last record is (0, 0, 0, the lists' total, the crossings' total)
    links        links × 12 bytes: u16 circle a < circle b, f32 x, y (a point where they meet); sorted by b
    lists        u16 link numbers: each circle's links, the circles one after another (every link twice)
    crossings    crossings × 28 bytes: the road through a circle: f32 x, y where it comes in and x, y where it leaves
                 (points on road links r0 and r1, each where the road crosses its gate's line), f32 its length along
                 the road (the shortest way), u16 the two links (gates) it goes between, the lower first, u16 r0, r1:
                 road network links (buffer 0; 7,862 of 7,862 checked on 4 maps, 2026-09-30), so a road link
                 renumbered must be renumbered here too (Graph.renumber_roads). Units plan along roads only through
                 these; new roads get theirs from Graph.add_crossings
    points       a spatial index of the circles, up to the first sub-graph: branch records (u16 1, u16 how far
                 to skip, f32 x, y: a split point) and leaf records (u16 count, then that many circle numbers);
                 see _tree_read
    sub-graphs   the same layout again, without sub-graphs of their own (22 on Blitz)

**Local maps (the sub-graphs).** Sub-graph k belongs to main circle k, for every k below the header's count: nothing
else ties them, so the owners are always the first circles (the largest first on every shipped graph, then the rest
largest first). Inside an owner, units can stand only where its local map has a circle, a route is searched again
inside the local map between the points where it comes in and goes out (a search that fails there fails the whole
route), and an order into the owner is moved to the nearest circle of its local map. So a local map is one piece and
has a circle at every point where a main link meets its owner (11,830 of 12,007 shipped ones do), and no other main
circle's middle lies inside an owner (none on any shipped map). A local map shares its main graph's box, has no local
maps of its own, and its header after the counts is zeros, like the main graph's.

Every shipped graph is one connected piece (66 of 66 main graphs on 33 maps, and all their sub-graphs): the game
never expects ground it can't reach from the rest, and an order onto such ground crashes it (seen in the game,
2026-09-30). Changes here keep a graph in one piece (Graph.parts).

`Graph.read(data).to_bytes() == data` on every shipped map (tools/verify_nav.py)."""
from __future__ import annotations

import math
import struct
from array import array
from dataclasses import dataclass, field
from heapq import heapify, heappop, heappush

HEADER = 84
STEP = 320.0         # circle centres and radii are on this grid
MIN_RADIUS = 1280.0  # the smallest circle on any shipped map
METRE = 260.0        # map units in a metre
APPROACH = 16000.0   # how far past a new deck's end its approach may run along the road to reach ground units already
                     # use (about 62 m; the shipped bridges' chains of circles reach up to 10,800 past their decks)
DECK_RADIUS = 640.0    # a new deck's circles in the main graph: narrower than
                       # the bridge floors units stand on (663), so a unit can never be off the deck
LOCAL_RADIUS = 640.0   # a new deck's circles in its local map: units keep within this of the deck's line, inside the
                       # floor they stand on (663 either side on the bridge kinds the build places; the shipped decks'
                       # local circles are mostly 640)
LOCAL_SPACING = 640.0  # between them along the deck (a link needs an overlap of STEP: at most 960 apart for 640)
LEAF = 4               # the most circles in a leaf of an index built here (the shipped ones hold 1 to 7)
MAX_DEPTH = 24         # the deepest an index may go: the game walks it with a fixed stack of 32 entries and no test of
                       # running past it (the deepest shipped index is 18 levels; one built here, balanced, about 14)


class NavError(ValueError):
    pass


@dataclass
class Graph:
    box: tuple                         # x0, y0 (words as stored), size
    circles: list                      # (x, y, radius, list start, crossings start), the closing record included
    links: list                        # (a, b, x, y)
    lists: list                        # u16 link numbers
    crossings: bytes                   # crossings × 28 bytes, as stored
    points: bytes                      # as stored
    subs: list = field(default_factory=list)
    head_rest: bytes = b""             # the header's bytes after the four counts (zeros on every shipped map)

    @classmethod
    def read(cls, data: bytes) -> "Graph":
        if len(data) < HEADER + 20:
            raise NavError("too short for a navigation graph")
        x0, y0, size = struct.unpack_from("<IIf", data, 0)
        n_circles, n_links, n_cross, n_subs = struct.unpack_from("<4H", data, 12)
        offsets = list(struct.unpack_from(f"<{5 + n_subs}I", data, HEADER))
        ends = offsets[1:] + [len(data)]
        if offsets[0] != HEADER + 4 * len(offsets) or any(e < o for o, e in zip(offsets, ends)) or ends[-1] > len(data):
            raise NavError("the graph's offsets don't fit it")
        c0, l0, s0, x0_, p0 = offsets[:5]
        if l0 - c0 != 16 * (n_circles + 1) or s0 - l0 != 12 * n_links or p0 - x0_ != 28 * n_cross:
            # not a game rule: a damaged or unexpected file
            raise NavError("the graph's sections don't match its counts")
        circles = [struct.unpack_from("<3f2H", data, c0 + 16 * i) for i in range(n_circles + 1)]
        links = [struct.unpack_from("<2H2f", data, l0 + 12 * i) for i in range(n_links)]
        lists = list(struct.unpack_from(f"<{(x0_ - s0) // 2}H", data, s0))
        if (x0_ - s0) % 2:
            raise NavError("the lists section has an odd length")
        subs = [cls.read(data[o:e]) for o, e in zip(offsets[5:], ends[5:])]
        return cls((x0, y0, size), circles, links, lists, bytes(data[x0_:p0]), bytes(data[p0:ends[4]]), subs,
                   bytes(data[20:HEADER]))

    def to_bytes(self) -> bytes:
        """The graph as stored. One with an emptied circle (radius 0) gets its index built again from the live
        circles, the numbers kept (local maps are tied to their owners by number): the game looks for the nearest
        circle to an order or a route's end through the index, with no test of the radius, so an emptied circle left
        in it is landed on, and a route to a circle with no links fails. No shipped graph has one."""
        live = [c[:3] for c in self.circles[:-1]]
        points = self.points
        if any(r <= 0 for _x, _y, r in live) and any(r > 0 for _x, _y, r in live):
            points = _tree_write(_tree_build(live))
        body = [b"".join(struct.pack("<3f2H", *c) for c in self.circles),
                b"".join(struct.pack("<2H2f", *lk) for lk in self.links),
                struct.pack(f"<{len(self.lists)}H", *self.lists),
                self.crossings, points] + [s.to_bytes() for s in self.subs]
        offsets, at = [], HEADER + 4 * len(body)
        for part in body:
            offsets.append(at)
            at += len(part)
        head = (struct.pack("<IIf4H", *self.box, len(self.circles) - 1, len(self.links), len(self.crossings) // 28,
                            len(self.subs)) + self.head_rest)
        return head + struct.pack(f"<{len(offsets)}I", *offsets) + b"".join(body)

    # --- changing it ---
    def block(self, zones: list[tuple[float, float, float]], refill: bool = True, keep_owners: bool = False) -> dict:
        """Take the ground inside `zones` (circles: x, y, radius) away, here and in the local graphs: units plan
        around it (proven in the game, 2026-09-30). With `keep_owners`, the circles that own a local map stay as they
        are: their ground is taken away in the local map only (an old bridge's deck, whose owner then takes the new
        one: Graph.open).

        A circle whose middle is in a zone, or that would be smaller than MIN_RADIUS once it keeps clear of every
        zone, is emptied (radius 0, no links); one that reaches into a zone shrinks to keep clear (its radius a
        multiple of STEP). A link whose meeting point is no longer inside both circles, or lies in a zone, moves to
        where the two still meet by STEP or more outside the zones; it goes when they don't, or one of them is
        emptied. The crossings that use a link that moved or went go too. With `refill`, the ground those circles
        gave up outside the zones gets new circles (the largest first, centres on the STEP grid), linked to every
        circle they overlap by STEP or more, and to each other; the shrunk circles are linked again where they still
        overlap. New circles are numbered after the old ones and listed in the index as one more tree (a leaf), so
        the old numbers and the old trees stay. Returns what changed."""
        counts = {"emptied": 0, "shrunk": 0, "links": 0, "crossings": 0, "added": 0, "linked": 0}
        if zones:
            self._block(zones, refill, counts, len(self.subs) if keep_owners else 0)
        for s in self.subs:
            for k, v in s.block(zones, refill).items():
                counts[k] += v
        return counts

    def _block(self, zones, refill, counts, keep: int = 0) -> None:
        n = len(self.circles) - 1
        old = [c[:3] for c in self.circles[:-1]]
        radius = []
        # the zones by place (thousands over a map's new water): a circle is looked at against those that may reach
        # within a unit of it only. Any other is over a unit clear of it, so it never decides whether the circle
        # shrinks, nor by how much; the same for a point in a zone. (All by hand when a zone has no size.)
        zoned = _Buckets(list(zones)) if all(zr > 0 for _x, _y, zr in zones) else None
        for i, (x, y, r) in enumerate(old):
            by = zones if zoned is None else [zones[k] for k in zoned.near(x, y, r + 1.0)]
            clear = min((((x - zx) ** 2 + (y - zy) ** 2) ** 0.5 - zr for zx, zy, zr in by), default=math.inf)
            if clear >= r or i < keep:
                radius.append(r)
                continue
            new = (clear // STEP) * STEP if clear > 0 else 0.0
            if new < MIN_RADIUS:
                new = 0.0
            counts["emptied" if new == 0 else "shrunk"] += 1
            radius.append(new)
        changed = [i for i in range(n) if radius[i] != old[i][2]]
        if not changed:
            return

        def in_zone(px, py):
            return any((px - zx) ** 2 + (py - zy) ** 2 <= zr * zr
                       for zx, zy, zr in (zones if zoned is None else (zones[k] for k in zoned.near(px, py, 1.0))))

        now = [(x, y, radius[i]) for i, (x, y, _r) in enumerate(old)]
        filled = _fill([old[i] for i in changed], zones, now, kept=[radius[i] for i in changed]) if refill else []
        added = [c[:3] for c in filled]
        allc = now + added
        counts["added"] += len(added)

        def holds(c, px, py):
            cx, cy, cr = allc[c]
            return cr > 0 and (px - cx) ** 2 + (py - cy) ** 2 <= cr * cr + 1.0

        kept = []
        for i, (a, b, px, py) in enumerate(self.links):
            if holds(a, px, py) and holds(b, px, py) and not in_zone(px, py):
                kept.append((i, (a, b, px, py)))
            elif allc[a][2] > 0 and allc[b][2] > 0:  # both still there: the gate moves to where they still meet,
                point = _meeting(allc[a], allc[b])  # outside the zones (else a shrunk circle could cut ground off);
                if point is not None and not in_zone(*point):  # a new link: the roads through it went with the old
                    kept.append((None, (a, b) + point))
        counts["links"] += len(self.links) - len(kept)
        new_links = []
        if refill:  # new links: new circles to everything they overlap; shrunk circles to each other again
            linked = {(a, b) for _i, (a, b, _x, _y) in kept}
            near = _Buckets([c for c in allc])
            shrunk = [i for i in changed if radius[i] > 0]
            for c in shrunk + list(range(n, n + len(added))):
                for d in near.around(c):
                    if d == c or allc[d][2] <= 0 or (c < n and d < n and d not in shrunk):
                        continue
                    a, b = min(c, d), max(c, d)
                    if (a, b) in linked:
                        continue
                    point = _meeting(allc[a], allc[b])
                    if point is None or in_zone(*point):
                        continue
                    linked.add((a, b))
                    new_links.append((None, (a, b) + point))
                    counts["linked"] += 1
        counts["crossings"] += self._finish(allc, kept, new_links, n)
        if added:  # the index: each new circle joins the leaf of the old circle it lies in (see _index_add)
            into: dict[int, list[int]] = {}
            for j, (_x, _y, _r, source) in enumerate(filled):
                into.setdefault(changed[source], []).append(n + j)
            self.points = _index_add(self.points, into)

    def _finish(self, allc, kept, new_links, n: int, old_of=None) -> int:
        """The graph's circles, links, lists and crossings written again from `allc` (every circle, the first `n`
        old), `kept` ((old number, link) pairs) and `new_links` ((None, link)); returns how many crossings went.
        `old_of` gives each circle of `allc` its old number (None for a new one) when the old ones were numbered
        again (new owners put in among them: Graph.open); without it, circle c < n is old circle c."""
        if old_of is None:
            old_of = list(range(n)) + [None] * (len(allc) - n)
        # every shipped graph lists its links by their second circle: kept ones are already in that order, new ones
        # go after the kept ones of the same second circle (a stable sort)
        ordered = sorted(kept + new_links, key=lambda pair: pair[1][1])
        number = {i: k for k, (i, _lk) in enumerate(ordered) if i is not None}  # old link number -> new
        links = [lk for _i, lk in ordered]
        mine = [[] for _ in allc]
        for i, (a, b, _x, _y) in enumerate(links):
            mine[a].append(i)
            mine[b].append(i)
        cross = [self.crossings[28 * i:28 * i + 28] for i in range(len(self.crossings) // 28)]
        circles, lists, kept_cross = [], [], []
        for c in range(len(allc)):
            start, cstart = len(lists), len(kept_cross)
            lists += mine[c]
            if old_of[c] is not None:
                c0, c1 = self.circles[old_of[c]][4], self.circles[old_of[c] + 1][4]
                for rec in cross[c0:c1]:
                    la, lb = struct.unpack_from("<2H", rec, 20)
                    if la in number and lb in number:
                        kept_cross.append(rec[:20] + struct.pack("<2H", number[la], number[lb]) + rec[24:])
            circles.append((allc[c][0], allc[c][1], allc[c][2], start, cstart))
        circles.append((0.0, 0.0, 0.0, len(lists), len(kept_cross)))
        if len(circles) > 65535 or len(links) > 65535 or len(lists) > 65535:
            raise NavError("the graph would be too big for its 16-bit numbers")
        self.circles, self.links, self.lists, self.crossings = circles, links, lists, b"".join(kept_cross)
        return len(cross) - len(kept_cross)

    def open(self, spans: list[tuple[float, float, float, float]], radius: float = 2560.0, roads=(),
             reach: float = APPROACH, avoid=None, water=None) -> dict:
        """Give units a way over `spans` (x0, y0, x1, y1: bridges' decks) where there was none (water), the way the
        game's own bridges have one: one big circle over the crossing, its owner, and in the owner's local map small
        circles along the deck (LOCAL_RADIUS, at most LOCAL_SPACING apart, end to end) with a copy of every main circle
        the owner overlaps. Inside the owner units stand only on those, so they keep to the deck and the water beside
        it stays closed (plain main circles along a deck let units cut across their whole width: off its sides and
        under it, seen in the game, 2026-09-30); the copies keep the banks inside the owner as they were, and hold
        every point where the owner's links meet the ground around.

        A deck must reach ground units already use at both ends: the shipped graphs are each one piece, and the game
        crashes when a unit is ordered onto ground its own can't reach (an empty route, seen in the game 2026-09-30).
        So where a deck's end third doesn't overlap a live main circle by STEP or more, an approach goes on from that
        end in the main graph: circles `radius` wide every 3/4 `radius` along the nearest of `roads` (lines of map
        points; the way that leads off the deck, then straight on past the road's end; straight on along the deck
        without one), until one does, at most `reach` map units out; never where `avoid(x, y, r)` says (blocked
        ground, the holes the map leaves for its buildings), with any of its disc over `water(x, y)`, with its middle
        in an owner or overlapping a new one: where a circle of `radius` would, one of 3/4 or 1/2 of it may go.

        The owner is centred at the deck's middle (on the STEP grid), as small as holds the whole deck and links to
        the ground at both ends (with no copy apart from the deck, when a size allows it), and never so big that
        another main circle's middle is inside it or it overlaps another owner (no shipped graph has either). It takes
        the circle number after the old owners (the game finds local map k as circle k's): every circle after it
        moves up one, in the links, lists, crossings and index; its local map goes after theirs, with an index of
        its own (_tree_build); it is linked to the main circles whose copies are in its local map, and listed in the
        main index under the nearest old circle (_index_add). An old deck of main circles under the new one (a bridge
        of the map's that has no owner: their middles over the water, reaching within 2 LOCAL_RADIUS of the new deck's
        line) goes when the new one opens, and so do the circles linked to it whose middles would be in any owner over
        the new deck (its ends), kept in the new local map shrunk off the water (_dry_part); unless that would leave
        ground units can't reach, when the old deck stays and the new one stays closed. A deck whose middle is in an
        old owner (a replaced bridge of the map's, a
        town by a river) goes into that owner's local map instead (_into_local). A deck that can't be joined at both
        ends, or has no room for an owner, is left closed.

        Checked before returning (NavError): the graph in no more pieces than before; every new local map one
        piece; every point where a new link meets an owner inside a circle of its local map; each new owner holding
        its whole deck and no other circle's middle, and no new circle's middle in an owner; every place along each
        opened deck ground units can stand on (walkable); the graph read back as written.

        Returns {"added": main circles added (owners and approaches), "linked": main links added, "approach": circles
        on approaches, "longest": the longest approach (map units), "owners": [(span index, circle number, radius,
        circles in its local map)], "inside": [(span index, the old owner's number)], "left_out": copies left out of
        a local map (apart from its deck), "under": an old deck's main circles taken away, "closed": [(span index, [the
        ends that couldn't be joined: 0 its start, 1 its end])], "crowded": [span index: no room for an owner, or an
        old owner it can't go into], "stopped": {(span index, end): (x, y, how far along the road, what the road
        meets there: "water", "ground closed to units", "a town's or bridge's own ground") where an approach
        had to stop}."""
        counts = {"added": 0, "linked": 0, "approach": 0, "longest": 0.0, "owners": [], "inside": [], "left_out": 0,
                  "under": 0, "closed": [], "crowded": [], "stopped": {}}
        n, nx = len(self.circles) - 1, len(self.subs)
        allc = [c[:3] for c in self.circles[:-1]]  # the main circles: the old ones, then the approaches
        ground = _Buckets(allc)  # (allc grows with it)
        parts_before = len(self._labels()[1])
        owned = []  # the new owners: {"span", "circle", "local": its local map's circles, "linked": main circles}
        decks = []  # (span index, the deck's circles), for the last check

        def in_owner(x, y, r) -> bool:
            """Whether a circle has its middle in an old owner, or overlaps a new one."""
            return any(allc[k][2] > 0 and math.hypot(x - allc[k][0], y - allc[k][1]) < allc[k][2] for k in range(nx)) \
                or any(math.hypot(x - o["circle"][0], y - o["circle"][1]) < o["circle"][2] + r for o in owned)

        def meets(c, d):
            """Where circle c meets main circle d, for a link (an old owner only where its local map has ground)."""
            if allc[d][2] <= 0:
                return None
            point = _meeting(c, allc[d])
            if point is None or (d < nx and self.subs[d].find(*point) is None):
                return None
            return point
        near_of = [set() for _ in range(n)]  # the old circles each old circle is linked to
        for a, b, _x, _y in self.links:
            near_of[a].add(b)
            near_of[b].add(a)

        def pieces_with(got) -> int:
            """How many pieces the main graph would be in with `got` (an owner and its approaches) and those before
            it: the old links between live circles, every approach circle linked to all it meets, every owner to the
            circles its local map has copies of."""
            every = allc + got["main"]
            up = list(range(len(every) + len(owned) + 1))

            def root(a):
                while up[a] != a:
                    up[a] = up[up[a]]
                    a = up[a]
                return a
            for a, b, _x, _y in self.links:
                if every[a][2] > 0 and every[b][2] > 0:
                    up[root(a)] = root(b)
            for c in range(n, len(every)):
                for d in list(ground.near(*every[c])) + list(range(len(allc), len(every))):
                    if d != c and every[d][2] > 0 and _meeting(every[c], every[d]) is not None \
                            and (d >= len(allc) or meets(every[c], d) is not None):
                        up[root(c)] = root(d)
            for j, o in enumerate(owned + [got]):
                for i in o["linked"]:
                    up[root(len(every) + j)] = root(i)
            return len({root(i) for i in range(len(up)) if i >= len(every) or every[i][2] > 0})

        for si, (x0, y0, x1, y1) in enumerate(spans):
            length = math.hypot(x1 - x0, y1 - y0)
            if length <= 0:
                continue
            steps = max(1, math.ceil(length / LOCAL_SPACING))
            deck = [(float(round(x0 + (x1 - x0) * k / steps)), float(round(y0 + (y1 - y0) * k / steps)), LOCAL_RADIUS)
                    for k in range(steps + 1)]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            host = next((k for k in range(nx) if allc[k][2] > 0
                         and math.hypot(mx - allc[k][0], my - allc[k][1]) < allc[k][2]), None)
            if host is not None:
                got = self._into_local(host, (x0, y0, x1, y1), deck, roads, reach, avoid, water)
                if got is None:
                    counts["crowded"].append(si)
                    continue
                counts["inside"].append((si, host))
                counts["approach"] += got[0]
                counts["longest"] = max(counts["longest"], got[1])
                decks.append((si, deck))
                continue
            # an old deck of main circles under the new one (a bridge of the map's without an owner) goes: those over
            # the water, and those of its ends whose middles would be in any owner over the new deck, kept (shrunk off
            # the water) in the new local map
            under = {i: allc[i] for i in _under(allc, (x0, y0, x1, y1), water) if nx <= i < n}
            cx, cy, low = _owner_middle((x0, y0, x1, y1))
            ends_of = {j: allc[j] for i in under for j in near_of[i] if j >= nx and j not in under and allc[j][2] > 0
                       and math.hypot(allc[j][0] - cx, allc[j][1] - cy) < low}
            kept_ends = [c for c in (_dry_part(water, *c) for c in ends_of.values()) if c is not None]
            gone = {**under, **ends_of}
            for i in gone:
                allc[i] = allc[i][:2] + (0.0,)
            third = max(1, len(deck) // 3)
            ends = ((deck[:third], (x0, y0), (x0 - x1, y0 - y1), (x1, y1)),
                    (deck[-third:], (x1, y1), (x1 - x0, y1 - y0), (x0, y0)))
            chains, anchors, failed, longest = [], [], [], 0.0  # anchors: each end's ground, by main circle number
            for which, (part, at, out, other) in enumerate(ends):
                here = sorted({d for c in part for d in ground.near(*c) if d >= nx and meets(c, d) is not None})
                if here:
                    chains.append([])
                    anchors.append(here)
                    continue
                chain, met = [], []
                for walked, (px, py) in _walk_out(at, out, roads, radius * 0.75, reach, away=other):
                    # the biggest circle that fits there: a smaller one squeezes past a building or the water's edge
                    # (spaced 3/4 of `radius`, circles of half of it still overlap by STEP and link)
                    r = next((float(rr) for rr in (radius, radius * 0.75, radius / 2)
                              if not ((avoid is not None and avoid(px, py, float(rr))) or _wet(water, px, py, rr)
                                      or in_owner(px, py, rr))), None)
                    if r is None:
                        small = radius / 2
                        why = "water" if _wet(water, px, py, small) else \
                            "a town's or bridge's own ground" if in_owner(px, py, small) else \
                            "ground closed to units (a building the map keeps them off, or ground a mod blocked)"
                        counts["stopped"][(si, which)] = (px, py, walked, why)
                        break
                    chain.append((px, py, r))
                    met = [d for d in ground.near(*chain[-1]) if meets(chain[-1], d) is not None]
                    if met:
                        longest = max(longest, walked)
                        break
                if met:
                    chains.append(chain)
                    anchors.append(met)
                else:
                    failed.append(which)
            got = None if failed else self._owner_for((x0, y0, x1, y1), deck, allc, nx, anchors, chains,
                                                      [o["circle"] for o in owned], kept_ends)
            if got is not None and gone and pieces_with(got) > parts_before:
                got = None  # the old deck was the only way to some ground: it stays, and the new one stays closed
            if got is None:
                counts["closed" if failed else "crowded"].append((si, failed) if failed else si)
                for i, c in gone.items():  # (the old deck stays)
                    allc[i] = c
                continue
            for c in got["main"]:  # the approaches' circles outside the owner (those in it are in its local map)
                ground.add(c)
            counts["under"] += len(gone)
            counts["approach"] += sum(len(chain) for chain in chains)
            counts["longest"] = max(counts["longest"], longest)
            counts["left_out"] += got["left_out"]
            owned.append(dict(got, span=si))
            decks.append((si, deck))
        if not decks:
            return counts
        added, m = len(allc) - n, len(owned)
        if added or m:
            owned.sort(key=lambda o: -o["circle"][2])  # owners largest first, as on every shipped graph

            def num(i):  # a main circle's number once the new owners are in, after the old ones
                return i if i < nx else i + m
            circles = allc[:nx] + [o["circle"] for o in owned] + allc[nx:]
            old_of = list(range(nx)) + [None] * m + [i if i < n else None for i in range(nx, len(allc))]
            kept = [(i, (num(a), num(b), x, y)) for i, (a, b, x, y) in enumerate(self.links)
                    if allc[a][2] > 0 and allc[b][2] > 0]  # (an old deck's under a new one go)
            linked = {lk[:2] for _i, lk in kept}
            new_links = []
            for c in range(n, len(allc)):  # the approaches: to every main circle they meet
                for d in ground.around(c):
                    point = meets(allc[c], d) if d != c else None
                    pair = (num(min(c, d)), num(max(c, d)))
                    if point is None or pair in linked:
                        continue
                    linked.add(pair)
                    new_links.append((None, pair + point))
            for j, o in enumerate(owned):  # each owner: to the main circles its local map has copies of
                new_links += [(None, (nx + j, num(i)) + _meeting(o["circle"], allc[i])) for i in o["linked"]]
            counts["added"], counts["linked"] = added + m, len(new_links)
            self._finish(circles, kept, new_links, n, old_of)
            fresh = [(nx + j, o["circle"]) for j, o in enumerate(owned)] \
                + [(num(i), allc[i]) for i in range(n, len(allc))]
            self.points = _index_more(_index_renumber(self.points, num), allc[:n], fresh, num)
            self.subs = self.subs + [_local_graph(self.box, o["local"]) for o in owned]
            counts["owners"] = [(o["span"], nx + j, o["circle"][2], len(o["local"])) for j, o in enumerate(owned)]
        self._check_opened(spans, parts_before, nx, m, n + m, decks, [(k, si) for si, k, _r, _c in counts["owners"]])
        return counts

    def open_narrow(self, spans: list[tuple[float, float, float, float]], radius: float = DECK_RADIUS, roads=(),
                    reach: float = APPROACH, avoid=None, water=None) -> dict:
        """Give units ground along `spans` (x0, y0, x1, y1: a bridge's deck) where there was none: a chain of circles
        `radius` wide every `radius` along the deck, in the main graph, with no owner circle and no local map.

        `radius` is smaller than the bridge floor's half width (DECK_RADIUS 640, the floors are 663), so every point
        a unit may stand on is over the deck it stands on. That is the whole of it: the game may straighten a route
        anywhere inside the circles it runs through, and here they are no wider than the deck. The owner's tests of
        the owner-circle design (2026-09-30 and 2026-10-01) put units in the river beside a deck, which this cannot
        do: there is no ground off the deck to be on.

        A deck must reach ground units already use at both ends, or the game crashes when a unit is ordered onto it
        (an empty route). Where a deck's end third doesn't overlap a live circle by STEP or more, an approach goes on
        from that end along the nearest of `roads`, circles every 3/4 `radius` (a smaller one where a full one won't
        fit), at most `reach` out, never where `avoid(x, y, r)` says or with any of its disc over `water(x, y)`. A
        deck that can't be joined at both ends is left closed. Returns Graph.open's counts."""
        counts = {"added": 0, "linked": 0, "approach": 0, "longest": 0.0, "owners": [], "inside": [], "left_out": 0,
                  "under": 0, "closed": [], "crowded": [], "stopped": {}}
        n = len(self.circles) - 1
        old = [c[:3] for c in self.circles[:-1]]
        ground = _Buckets(old)

        def joined(c) -> bool:
            return any(_meeting(c, old[d]) is not None for d in ground.near(*c))

        new, parts_before = [], len(self._labels()[1])
        nx = len(self.subs)
        for si, (x0, y0, x1, y1) in enumerate(spans):
            length = math.hypot(x1 - x0, y1 - y0)
            if length <= 0:
                continue
            steps = max(1, int(-(-length // radius)))
            deck = [(x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps, float(radius)) for k in range(steps + 1)]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            host = next((k for k in range(nx) if old[k][2] > 0
                         and math.hypot(mx - old[k][0], my - old[k][1]) < old[k][2]), None)
            if host is not None:  # inside an owner (a town, a bridge of the map's): its local map decides there, so
                got = self._into_local(host, (x0, y0, x1, y1), deck, roads, reach, avoid, water)  # the deck goes in it
                if got is None:
                    counts["crowded"].append(si)
                    continue
                counts["inside"].append((si, host))
                counts["approach"] += got[0]
                counts["longest"] = max(counts["longest"], got[1])
                continue
            third = max(1, len(deck) // 3)
            ends = ((deck[:third], (x0, y0), (x0 - x1, y0 - y1), (x1, y1)),
                    (deck[-third:], (x1, y1), (x1 - x0, y1 - y0), (x0, y0)))
            approaches, failed, longest = [], [], 0.0
            for which, (part, at, out, other) in enumerate(ends):
                if any(joined(c) for c in part):
                    continue
                chain, reached = [], False
                for walked, (px, py) in _walk_out(at, out, roads, radius * 0.75, reach, away=other):
                    r = next((float(rr) for rr in (radius, radius * 0.75, radius / 2)
                              if not ((avoid is not None and avoid(px, py, float(rr))) or _wet(water, px, py, rr))),
                             None)
                    if r is None:
                        why = "water" if _wet(water, px, py, radius / 2) else \
                            "ground closed to units (a building the map keeps them off, or ground a mod blocked)"
                        counts["stopped"][(si, which)] = (px, py, walked, why)
                        break
                    chain.append((px, py, r))
                    if joined(chain[-1]):
                        reached = True
                        longest = max(longest, walked)
                        break
                if reached:
                    approaches.append(chain)
                else:
                    failed.append(which)
            if failed:
                counts["closed"].append((si, failed))
                continue
            counts["longest"] = max(counts["longest"], longest)
            new += deck + [c for chain in approaches for c in chain]
            counts["approach"] += sum(len(chain) for chain in approaches)
        if not new:
            return counts
        allc = old + new
        counts["added"] = len(new)
        near = _Buckets(allc)
        linked = {(a, b) for a, b, _x, _y in self.links}
        new_links = []
        for c in range(n, n + len(new)):
            for d in near.around(c):
                if d == c or allc[d][2] <= 0:
                    continue
                a, b = min(c, d), max(c, d)
                if (a, b) in linked:
                    continue
                point = _meeting(allc[a], allc[b])
                if point is None:
                    continue
                linked.add((a, b))
                new_links.append((None, (a, b) + point))
        counts["linked"] = len(new_links)
        self._finish(allc, list(enumerate(self.links)), new_links, n)
        live = [i for i, c in enumerate(old) if c[2] > 0]  # the index: each new circle under the nearest old one
        where = _Buckets([old[i] for i in live])
        into: dict[int, list[int]] = {}
        boxes: dict[int, tuple] = {}
        for j, (x, y, r) in enumerate(new):
            ids = list(where.near(x, y, r + 20480.0)) or range(len(live))
            bank = live[min(ids, key=lambda k: math.hypot(old[live[k]][0] - x, old[live[k]][1] - y)
                            - old[live[k]][2])] if live else -1
            into.setdefault(bank, []).append(n + j)
            bx0, by0, bx1, by1 = boxes.get(bank, (x, y, x, y))
            boxes[bank] = (min(bx0, x - r), min(by0, y - r), max(bx1, x + r), max(by1, y + r))
        self.points = _index_add(self.points, into, boxes)
        if len(self._labels()[1]) > parts_before:  # a guard: never write ground units can't reach
            # rule: ground-reach
            raise NavError("opening the bridges would leave ground units can't reach, which crashes the game")
        return counts

    def open_ground(self, zones: list[tuple[float, float, float]]) -> dict:
        """Give units the ground inside `zones` (circles: x, y, radius) where the graph has none: the reverse of
        Graph.block. Ground a shipped map closes to units has no circle over it at all (no shipped graph has a circle
        without links, or an emptied one: FORMATS.md §6, movement graphs), so opening it is adding circles there.

        The main graph gets new circles over the zones where no live circle is (_grow: centres on the 2 STEP grid,
        the largest first, each inside a zone, down to MIN_RADIUS, their middles on the map and never
        in a circle that owns a local map), linked to every circle they overlap by STEP or more (to an owner only where
        its local map has ground at the meeting point). Inside an owner the game decides from its local map, so the
        zones that reach an owner get new circles in its local map too (down to STEP, the smallest a shipped local map
        has; their middles inside the owner). New circles that can't reach the old ones through their links (an
        island, ground the zone touches nowhere) are left out: the graph and each local map stay in as many pieces as
        before (one, on every shipped map). New circles are numbered after the old ones and listed in the index under
        the nearest old circle (_index_more), so the old numbers, local maps and crossings stay as they were.

        Returns {"added": main circles added, "linked": main links added, "local": local-map circles added,
        "left_out": new circles left out (couldn't be reached), "idle": [zone index: nothing was added in it]}."""
        counts = {"added": 0, "linked": 0, "local": 0, "left_out": 0, "idle": []}
        live = [z for z in zones if z[2] > 0]
        if not live:
            counts["idle"] = list(range(len(zones)))
            return counts
        size = float(self.box[2])
        nx = len(self.subs)
        middles = []
        new, linked, out = self._open_here(live, MIN_RADIUS, (0.0, 0.0, size, size), None, nx)  # (middles on the map)
        counts["added"], counts["linked"], counts["left_out"] = len(new), linked, out
        middles += new
        by_place = _Buckets(list(live)) if nx else None  # (a map drained across has a quarter of a million zones)
        for k in range(nx):
            ox, oy, orad = self.circles[k][:3]
            if orad <= 0:
                continue
            here = [live[z] for z in sorted(by_place.near(ox, oy, orad + 1.0))
                    if math.hypot(live[z][0] - ox, live[z][1] - oy) < live[z][2] + orad]
            if not here:
                continue

            def inside(x, y, ox=ox, oy=oy, orad=orad) -> bool:
                return math.hypot(x - ox, y - oy) < orad
            got, _linked, out = self.subs[k]._open_here(here, STEP, (ox - orad, oy - orad, ox + orad, oy + orad),
                                                        inside)
            counts["local"] += len(got)
            counts["left_out"] += out
            middles += got
        counts["idle"] = _without(zones, middles)
        return counts

    def _open_here(self, zones, least: float, box, where=None, nx: int = 0) -> tuple[list, int, int]:
        """Graph.open_ground on this graph alone (no local maps): (the circles added, links added, circles left
        out). The new circles' middles are inside `box` (x0, y0, x1, y1) and where `where(x, y)` allows, when given.
        The first `nx` circles own local maps: a link to one only where its local map has ground."""
        n = len(self.circles) - 1
        old = [c[:3] for c in self.circles[:-1]]

        def meets(c, d):
            """Where new circle c meets old circle d, for a link (an owner only where its local map has ground)."""
            point = _meeting(c, old[d]) if old[d][2] > 0 else None
            if point is None or (d < nx and self.subs[d].find(*point) is None):
                return None
            return point
        # every new circle comes with a link of its own or more (to the circle it was reached from), and _finish
        # refuses a graph of more than 65,535 circles, or whose links listed twice pass 65,535: from this many new
        # circles on it can only refuse, so the growing stops there (a sea drained would go on for a million)
        most = min(32768 - len(self.links), 65535 - n)
        new, left_out, full = _grow(list(zones), old, least, box, where, meets, most)
        if full:
            raise NavError("the graph would be too big for its 16-bit numbers")
        if not new:
            return [], 0, left_out
        parts_before = len(self._labels()[1])
        allc = old + new
        near = _Buckets(list(allc))
        links = []
        for c in range(n, len(allc)):
            for d in near.around(c):
                if d == c or allc[d][2] <= 0 or n <= d < c:  # (two new circles: once, from the later one)
                    continue
                point = meets(allc[c], d) if d < n else _meeting(allc[c], allc[d])
                if point is not None:
                    links.append((min(c, d), max(c, d)) + point)
        self._finish(allc, list(enumerate(self.links)), [(None, lk) for lk in links], n)
        self.points = _index_more(self.points, old, [(n + j, c) for j, c in enumerate(new)])
        if len(self._labels()[1]) > parts_before:  # a guard: never write ground units can't reach
            # rule: ground-reach
            raise NavError("opening ground would leave ground units can't reach, which crashes the game")
        return new, len(links), left_out

    def _owner_for(self, span, deck, every, nx: int, anchors, chains, owners, extra=()) -> dict | None:
        """The owner circle for a deck (its circles `deck`, along `span`): centred at the deck's middle on the STEP
        grid; its radius on the STEP grid, from the least that holds the deck up to the most that leaves the middle of
        every main circle (`every`: (x, y, r), the first `nx` old owners) outside and other owners (old, and `owners`:
        the new ones) apart. The first radius whose local map (_try_owner; `anchors` and `chains`: each end's ground
        and approach; `extra`: circles for it alone) links to the ground at both ends with no copy apart from the
        deck, else the first that links to both ends at all. {"circle", "local", "linked", "left_out", "main"}, or
        None when no radius does."""
        cx, cy, low = _owner_middle(span)
        high = math.inf
        for i, (x, y, r) in enumerate(every):
            if r <= 0:
                continue
            d = math.hypot(x - cx, y - cy)
            high = min(high, (math.ceil(d / STEP) - 1) * STEP)  # its middle outside the owner
            if i < nx:
                high = min(high, math.floor((d - r) / STEP) * STEP)  # an old owner: apart
        for x, y, r in owners:
            high = min(high, math.floor((math.hypot(x - cx, y - cy) - r) / STEP) * STEP)
        high = min(high, low + 64 * STEP)  # (a bigger one never reaches more ground units use)
        if high < low:
            return None
        near = [(i, c) for i, c in enumerate(every)
                if i >= nx and c[2] > 0 and math.hypot(c[0] - cx, c[1] - cy) < high + c[2]]
        best = None
        for size in range(int(low), int(high) + 1, int(STEP)):
            got = _try_owner((cx, cy, float(size)), deck, near, anchors, chains, len(every), extra)
            if got is not None and not got["left_out"]:
                return got
            best = best or got
        return best

    def _into_local(self, k: int, span, deck, roads, reach: float, avoid, water) -> tuple[int, float] | None:
        """Put a deck (its circles `deck`, along `span`) into the local map of old owner k, which holds the deck's
        middle (a replaced bridge of the map's, whose old deck over water the build closed; a town by a river): the
        map's circles centred over water that come within 2 LOCAL_RADIUS of the deck's line go (an old deck there),
        the deck's circles come in, each end joined to the map's ground where its end third doesn't reach it by an
        approach of LOCAL_RADIUS circles every LOCAL_SPACING along the road, inside the owner, never over water or
        where `avoid` says; circles the new deck's ground doesn't reach go too (held to the rest by the old deck
        alone: a row of small circles beside it, on some maps). New circles are linked to every circle they overlap
        by STEP or more and listed in the map's index under the nearest old one. Returns (approach circles, the
        longest approach), or None, leaving the
        map as it was, when the deck isn't all inside the owner, an end can't be joined, or the map would come out in
        more pieces or with a point where a main link meets the owner no longer on its ground."""
        ox, oy, orad = self.circles[k][:3]
        x0, y0, x1, y1 = span
        if max(math.hypot(x0 - ox, y0 - oy), math.hypot(x1 - ox, y1 - oy)) > orad:
            return None
        local = self.subs[k]
        gates = [(gx, gy) for a, b, gx, gy in self.links if k in (a, b) and local.find(gx, gy) is not None]
        pieces = len(local._labels()[1])
        lc = [c[:3] for c in local.circles[:-1]]
        m0 = len(lc)
        for i in _under(lc, span, water):  # an old deck under the new one
            lc[i] = lc[i][:2] + (0.0,)
        ground = _Buckets(list(lc))

        def joins(c) -> bool:
            return any(_meeting(c, lc[d]) is not None for d in ground.near(*c))
        third = max(1, len(deck) // 3)
        ends = ((deck[:third], (x0, y0), (x0 - x1, y0 - y1), (x1, y1)),
                (deck[-third:], (x1, y1), (x1 - x0, y1 - y0), (x0, y0)))
        new, longest = list(deck), 0.0
        for part, at, out, other in ends:
            if any(joins(c) for c in part):
                continue
            chain, reached = [], False
            for walked, (px, py) in _walk_out(at, out, roads, LOCAL_SPACING, reach, away=other):
                if math.hypot(px - ox, py - oy) >= orad or (avoid is not None and avoid(px, py, LOCAL_RADIUS)) \
                        or _wet(water, px, py, LOCAL_RADIUS):
                    break
                chain.append((px, py, LOCAL_RADIUS))
                if joins(chain[-1]):
                    reached = True
                    longest = max(longest, walked)
                    break
            if not reached:
                return None
            new += chain
        allc = lc + new
        trial = Graph(local.box, list(local.circles), list(local.links), list(local.lists), local.crossings,
                      local.points, [], local.head_rest)
        kept = [(i, lk) for i, lk in enumerate(local.links) if allc[lk[0]][2] > 0 and allc[lk[1]][2] > 0]
        near = _Buckets(allc)
        linked = {lk[:2] for _i, lk in kept}
        new_links = []
        for c in range(m0, len(allc)):
            for d in near.around(c):
                pair = (min(c, d), max(c, d))
                point = _meeting(allc[pair[0]], allc[pair[1]]) if d != c and allc[d][2] > 0 else None
                if point is None or pair in linked:
                    continue
                linked.add(pair)
                new_links.append((None, pair + point))
        piece = _reached([lk for _i, lk in kept + new_links], m0)  # the ground the new deck reaches: what the old
        for i in range(m0):  # deck alone held to it goes with it (a row of small circles beside it, on some maps)
            if allc[i][2] > 0 and i not in piece:
                allc[i] = allc[i][:2] + (0.0,)
        kept = [(i, lk) for i, lk in kept if lk[0] in piece and lk[1] in piece]
        trial._finish(allc, kept, new_links, m0)
        trial.points = _index_more(local.points, lc, [(m0 + j, c) for j, c in enumerate(new)])
        if len(trial._labels()[1]) > pieces or any(trial.find(gx, gy) is None for gx, gy in gates):
            return None
        self.subs[k] = trial
        return len(new) - len(deck), longest

    def _check_opened(self, spans, parts_before: int, nx: int, m: int, fresh: int, decks, owners) -> None:
        """Graph.open's checks on the graph it made: new owners nx..nx+m-1 (`owners`: (circle number, span index)),
        new approach circles from `fresh` on, `decks` the opened decks' circles by span index."""
        if len(self._labels()[1]) > parts_before:  # a guard: never write ground units can't reach
            # rule: ground-reach
            raise NavError("opening the bridges would leave ground units can't reach, which crashes the game")
        circles = self.circles[:-1]
        for k in range(nx, nx + m):
            ox, oy, orad = circles[k][:3]
            if len(self.subs[k].parts()) != 1:
                # rule: ground-reach
                raise NavError(f"the local movement of the bridge at ({ox:.0f}, {oy:.0f}) would be in pieces, which "
                               f"crashes the game when a route goes through it")
            if any(i != k and r > 0 and math.hypot(x - ox, y - oy) < orad for i, (x, y, r, _l, _c) in enumerate(circles)):
                raise NavError(f"the circle over the bridge at ({ox:.0f}, {oy:.0f}) would hold another's middle")
        for i, (x, y, r, _l, _c) in enumerate(circles[fresh:], start=fresh):
            if any(r > 0 and math.hypot(x - ox, y - oy) < orad for ox, oy, orad, _l, _c in circles[:nx + m]):
                raise NavError(f"a new circle at ({x:.0f}, {y:.0f}) would have its middle in a bridge's or a town's "
                               f"local movement")
        for a, b, gx, gy in self.links:  # the owner is always a (owners are the first circles)
            if a < nx + m and (a >= nx or b >= fresh) and self.subs[a].find(gx, gy) is None:
                raise NavError(f"units would come into the local movement at ({gx:.0f}, {gy:.0f}) where it has no "
                               f"ground, and a route through it fails")
        for si, deck in decks:
            x0, y0, x1, y1 = spans[si]
            if not all(self.walkable(x, y) for x, y, _r in deck):
                raise NavError(f"units couldn't stand all along the bridge at ({(x0 + x1) / 2:.0f}, "
                               f"{(y0 + y1) / 2:.0f})")
        for k, si in owners:
            ox, oy, orad = circles[k][:3]
            x0, y0, x1, y1 = spans[si]
            if max(math.hypot(x0 - ox, y0 - oy), math.hypot(x1 - ox, y1 - oy)) > orad:
                raise NavError(f"the circle over the bridge at ({ox:.0f}, {oy:.0f}) wouldn't hold its whole deck")
        data = self.to_bytes()
        if Graph.read(data).to_bytes() != data:
            raise NavError("the movement graph wouldn't read back as it was written")

    def renumber_roads(self, number: dict[int, int]) -> int:
        """Point every crossing, here and in the sub-graphs, at the road network's links as numbered again (`number`:
        old link -> new, or None for a link that went: its crossings go too; a number it doesn't name stays as it
        is). A crossing's last two u16 are road network links (buffer 0): its two points lie on them (7,862 of 7,862
        crossings on 4 maps, 2026-09-30). Returns how many crossings went."""
        gone = 0
        for g in [self] + self.subs:
            recs, starts = [], []
            for c in range(len(g.circles) - 1):
                starts.append(len(recs))
                for k in range(g.circles[c][4], g.circles[c + 1][4]):
                    rec = g.crossings[28 * k:28 * k + 28]
                    r0, r1 = (number.get(r, r) for r in struct.unpack_from("<2H", rec, 24))
                    if r0 is None or r1 is None:
                        gone += 1
                    else:
                        recs.append(rec[:24] + struct.pack("<2H", r0, r1))
            starts.append(len(recs))
            g.circles = [c[:4] + (s,) for c, s in zip(g.circles, starts)]
            g.crossings = b"".join(recs)
        return gone

    def drop_crossings_through(self, road_net, zones: list[tuple[float, float, float]]) -> int:
        """After blocks: take out every crossing, here and in the local maps, whose road (the road network's path
        between its two road links; `road_net()` gives the roadnet.RoadNet, read only if a crossing is near a zone)
        runs through one of `zones`. The game routes a unit through a circle along that road without asking whether
        the ground is walkable, and never refines that part through the circle's local map, so a block on a town's
        road (a placed building) whose circle kept its crossings had units driving through it. The road itself
        stays: supply trucks use it. Returns how many went."""
        if not zones or not any(g.crossings for g in [self] + self.subs):
            return 0
        roads, adj = None, []

        def road(r0: int, r1: int, limit: float) -> list:
            """The points of the shortest road path from link r0 to link r1 (from either end), or [] past `limit`."""
            import heapq
            nonlocal roads, adj
            if roads is None:
                roads = road_net()
                adj = [[] for _ in roads.points]
                for a, b, _cost in roads.links:
                    d = math.dist(roads.points[a], roads.points[b])
                    adj[a].append((b, d))
                    adj[b].append((a, d))
            if max(r0, r1) >= len(roads.links):
                return []
            src, goal = set(roads.links[r0][:2]), set(roads.links[r1][:2])
            dist, prev = {p: 0.0 for p in src}, {}
            todo = [(0.0, p) for p in src]
            while todo:
                d, p = heapq.heappop(todo)
                if d > dist.get(p, math.inf) or d > limit:
                    continue
                if p in goal:
                    out = [p]
                    while out[-1] in prev:
                        out.append(prev[out[-1]])
                    return [roads.points[q] for q in reversed(out)]
                for q, w in adj[p]:
                    if d + w < dist.get(q, math.inf):
                        dist[q], prev[q] = d + w, p
                        heapq.heappush(todo, (d + w, q))
            return []

        def gap(px, py, ax, ay, bx, by) -> float:
            dx, dy = bx - ax, by - ay
            n = dx * dx + dy * dy
            t = 0.0 if n == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / n))
            return math.hypot(px - ax - t * dx, py - ay - t * dy)
        gone = 0
        for g in [self] + self.subs:
            recs, starts = [], []
            for c in range(len(g.circles) - 1):
                starts.append(len(recs))
                cx, cy, cr = g.circles[c][:3]
                # (the zones near it are looked for only when it has a crossing: few circles do, and a map's new
                # water is thousands of zones)
                near = [z for z in zones if math.hypot(z[0] - cx, z[1] - cy) < cr + z[2]] \
                    if g.circles[c][4] < g.circles[c + 1][4] else []
                for k in range(g.circles[c][4], g.circles[c + 1][4]):
                    rec = g.crossings[28 * k:28 * k + 28]
                    if near:
                        x0, y0, x1, y1, length = struct.unpack_from("<5f", rec)
                        r0, r1 = struct.unpack_from("<2H", rec, 24)
                        line = [(x0, y0)] + road(r0, r1, 2 * length + 5000.0) + [(x1, y1)]
                        if any(gap(zx, zy, *a, *b) < zr for zx, zy, zr in near for a, b in zip(line, line[1:])):
                            gone += 1
                            continue
                    recs.append(rec)
            starts.append(len(recs))
            g.circles = [c[:4] + (s,) for c, s in zip(g.circles, starts)]
            g.crossings = b"".join(recs)
        return gone

    def add_crossings(self, net, fresh=None, zones=()) -> dict:
        """Crossings for the roads of `net` (a roadnet.RoadNet) through this graph's circles (the main graph's; its
        local maps are left as they are), laid out as the shipped ones are (their points, lengths and gates: 892 of
        892 of D-Day's vehicle crossings, 2026-10-01; made again from D-Day's own roads, 95% of them come out the same,
        tools/verify_crossings.py). Units plan along a road only through these: a road no crossing names is driven
        across country. A circle's crossing is a stretch of road that comes in through one of its gates and leaves
        through another:

        - its points: where the road crosses each gate's line (through the link's point, square to the line between the
          two circles' middles, inside both circles), on road links r0 and r1;
        - its length: the shortest way along the roads between them, through road points inside the circle;
        - its gates: the in point's link is the lower number (a < b, as on every shipped crossing);
        - one for each two such points on two gates, when the road from each point heads into the circle, and no
          third gate's point lies on the way between them (the shipped ones skip those: a road through three gates
          has a crossing for each two in a row, not for the first and the last).

        With `fresh` (a set of road link numbers: the new roads), only crossings whose road uses one of them are
        made, in the circles those links reach; without it, every circle's are. Never one whose road runs through
        one of `zones` (x, y, r: the blocks), or over GAP or more of ground units can't stand on (walkable: a
        town's buildings, a river): the game moves a unit along a crossing's road without asking whether the ground
        is walkable. One the circle already has (the same gates and road links) isn't made twice. New ones go in
        their circle's range, the circle's crossings in order of gates and road links.

        Returns {"added": crossings made, "circles": circles that got one, "full": crossings left out because the
        graph holds no more (65,535), "named": the road links the new crossings' roads run on}."""
        import heapq
        out = {"added": 0, "circles": 0, "full": 0, "named": set()}
        points, links = net.points, net.links
        if not links:
            return out
        n = len(self.circles) - 1
        circles = [c[:3] for c in self.circles[:-1]]
        cell = 20480.0
        by_cell: dict = {}
        for i, (a, b, _w) in enumerate(links):
            (ax, ay), (bx, by) = points[a], points[b]
            for key in _cells(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), cell):
                by_cell.setdefault(key, []).append(i)
        adj = [[] for _ in points]
        for i, (a, b, _w) in enumerate(links):
            d = math.dist(points[a], points[b])
            adj[a].append((b, d, i))
            adj[b].append((a, d, i))
        if fresh is None:
            todo = [c for c in range(n) if circles[c][2] > 0]
        else:
            fresh = set(fresh)
            near = _Buckets(circles)
            todo = set()
            for i in fresh:
                (ax, ay), (bx, by) = points[links[i][0]], points[links[i][1]]
                mx, my, half = (ax + bx) / 2, (ay + by) / 2, math.dist((ax, ay), (bx, by)) / 2
                todo.update(c for c in near.near(mx, my, half)
                            if _seg_dist(circles[c][0], circles[c][1], (ax, ay, bx, by)) < circles[c][2])
            todo = sorted(todo)
        cross = [self.crossings[28 * i:28 * i + 28] for i in range(len(self.crossings) // 28)]
        mine = [cross[self.circles[c][4]:self.circles[c + 1][4]] for c in range(n)]
        total = len(cross)
        for c in todo:
            cx, cy, r = circles[c]
            # where the roads cross each gate's line: (gate link, road link, how far along it, x, y)
            at = []
            for g in self.links_of(c):
                a, b, gx, gy = self.links[g]
                ox, oy, orad = circles[b if a == c else a]
                ends = _gate_line((cx, cy, r), (ox, oy, orad), (gx, gy))
                if ends is None:
                    continue
                (px, py), (qx, qy) = ends
                seen = set()
                for rl in sorted({i for key in _cells(min(px, qx), min(py, qy), max(px, qx), max(py, qy), cell)
                                  for i in by_cell.get(key, ())}):
                    got = _crossing_at((px, py), (qx, qy), points[links[rl][0]], points[links[rl][1]])
                    if got is None:
                        continue
                    s, u = got
                    x, y = px + (qx - px) * s, py + (qy - py) * s
                    if (round(x), round(y)) not in seen:
                        seen.add((round(x), round(y)))
                        at.append((g, rl, u, x, y))
            if len({p[0] for p in at}) < 2:
                continue
            at.sort(key=lambda p: (p[0], p[1], p[2]))
            have = {struct.unpack_from("<4H", rec, 20) for rec in mine[c]}
            made = []
            for ga, ra, ua, xa, ya in at:
                if not any(p[0] > ga for p in at):
                    continue
                a0, b0, _w = links[ra]
                sa = math.dist(points[a0], points[b0])
                dist, prev = {a0: ua * sa, b0: (1 - ua) * sa}, {}
                heap = [(d, p) for p, d in dist.items()]
                heapq.heapify(heap)
                while heap:  # every road point inside the circle, by the shortest way from this one
                    d, p = heapq.heappop(heap)
                    if d > dist[p]:
                        continue
                    for q, w, li in adj[p]:
                        if li != ra and d + w < dist.get(q, math.inf) \
                                and (points[q][0] - cx) ** 2 + (points[q][1] - cy) ** 2 <= r * r:
                            dist[q], prev[q] = d + w, (p, li)
                            heapq.heappush(heap, (d + w, q))
                for gb, rb, ub, xb, yb in at:
                    if gb <= ga:
                        continue
                    key = (ga, gb, ra, rb)
                    if key in have:
                        continue
                    if rb == ra:
                        length, nodes, used = abs(ub - ua) * sa, [], set()
                        spans = {ra: (min(ua, ub), max(ua, ub))}
                    else:
                        a1, b1, _w = links[rb]
                        sb = math.dist(points[a1], points[b1])
                        options = [(dist[e] + (ub if e == a1 else 1 - ub) * sb, e) for e in (a1, b1) if e in dist]
                        if not options:
                            continue
                        length, end = min(options)
                        nodes, used, p = [end], set(), end
                        while p in prev:
                            p, li = prev[p]
                            used.add(li)
                            nodes.append(p)
                        nodes.reverse()
                        start = nodes[0]
                        spans = {ra: (0.0, ua) if start == a0 else (ua, 1.0),
                                 rb: (0.0, ub) if end == a1 else (ub, 1.0)}
                    if fresh is not None and not (fresh & (used | {ra, rb})):
                        continue
                    if any(_on_way(p, used, spans) for p in at if p[0] not in (ga, gb)):
                        continue  # a third gate between: the road leaves the circle there
                    line = [(xa, ya)] + [points[k] for k in nodes] + [(xb, yb)]
                    if not (_heads_in(line, (cx, cy), self._other_middle(c, ga))
                            and _heads_in(line[::-1], (cx, cy), self._other_middle(c, gb))):
                        continue
                    if any(_seg_dist(zx, zy, (*p0, *p1)) < zr for zx, zy, zr in zones for p0, p1 in zip(line, line[1:])):
                        continue
                    if not _open_along(self.walkable, line):
                        continue
                    have.add(key)
                    made.append((struct.pack("<5f4H", xa, ya, xb, yb, length, ga, gb, ra, rb), used | {ra, rb}))
            if not made:
                continue
            room = 65535 - total
            if len(made) > room:
                out["full"] += len(made) - room
                made = made[:room]
            if not made:
                continue
            for _rec, way in made:
                out["named"] |= way
            made = [rec for rec, _way in made]
            mine[c] = sorted(mine[c] + made, key=lambda rec: struct.unpack_from("<4H", rec, 20))
            total += len(made)
            out["added"] += len(made)
            out["circles"] += 1
        if out["added"]:
            starts, at_ = [], 0
            for c in range(n):
                starts.append(at_)
                at_ += len(mine[c])
            starts.append(at_)
            self.circles = [rec[:4] + (s,) for rec, s in zip(self.circles, starts)]
            self.crossings = b"".join(rec for recs in mine for rec in recs)
        return out

    def _other_middle(self, c: int, link: int) -> tuple[float, float]:
        """The middle of the circle that link `link` joins circle `c` to."""
        a, b, _x, _y = self.links[link]
        return tuple(self.circles[b if a == c else a][:2])

    def _empty(self, gone: set[int]) -> None:
        """Empty the circles `gone` as a block empties one: radius 0, their links and those links' crossings out."""
        n = len(self.circles) - 1
        allc = [(c[0], c[1], 0.0 if i in gone else c[2]) for i, c in enumerate(self.circles[:-1])]
        kept = [(i, lk) for i, lk in enumerate(self.links) if lk[0] not in gone and lk[1] not in gone]
        self._finish(allc, kept, [], n)

    def drop_cut_off(self) -> int:
        """Empty every live circle outside the graph's largest part: ground a block cut off from the rest is ground no
        unit can reach, and the game crashes when a unit is ordered onto it (seen in the game, 2026-09-30); an order
        there now goes to the nearest ground units can reach. Returns how many circles went."""
        lab, sizes = self._labels()
        if len(sizes) <= 1:
            return 0
        main = max(sizes, key=lambda part: (sizes[part], -part))
        gone = {i for i, c in enumerate(self.circles[:-1]) if c[2] > 0 and lab[i] != main}
        self._empty(gone)
        return len(gone)

    def parts(self) -> list[int]:
        """How many live circles each connected part of the graph has, the largest first. Every shipped graph is one
        part (66 of 66 main graphs and all their sub-graphs, 2026-09-30): the game never expects ground it can't
        reach."""
        return sorted(self._labels()[1].values(), reverse=True)

    def _labels(self) -> tuple[list[int], dict[int, int]]:
        """Each circle's part (a circle number standing for it), and how many live circles each part has."""
        n = len(self.circles) - 1
        up = list(range(n))

        def root(a):
            while up[a] != a:
                up[a] = up[up[a]]
                a = up[a]
            return a
        for a, b, _x, _y in self.links:
            ra, rb = root(a), root(b)
            if ra != rb:
                up[ra] = rb
        lab = [root(i) for i in range(n)]
        sizes: dict[int, int] = {}
        for i in range(n):
            if self.circles[i][2] > 0:
                sizes[lab[i]] = sizes.get(lab[i], 0) + 1
        return lab, sizes

    # --- reading it ---
    def links_of(self, circle: int) -> list[int]:
        """The link numbers of one circle."""
        return self.lists[self.circles[circle][3]:self.circles[circle + 1][3]]

    def find(self, x: float, y: float) -> int | None:
        """The circle holding (x, y) as the index finds it: down the tree, x and y by turns, into each half whose edge
        takes the point in (both where the edges overlap), and the first circle of a leaf that holds it. A circle the
        index can't reach this way is ground no order can be given onto."""
        cached = getattr(self, "_tree", None)
        if cached is None or cached[0] is not self.points:
            cached = self._tree = (self.points, _tree_read(self.points))
        todo = [(cached[1], 0)]
        while todo:
            node, axis = todo.pop()
            if node[0] == "leaf":
                for c in node[1]:
                    cx, cy, r = self.circles[c][:3]
                    if r > 0 and (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                        return c
                continue
            far, near = struct.unpack("<2f", node[2])
            p = (x, y)[axis]
            if p >= near:
                todo.append((node[4], 1 - axis))
            if p <= far:
                todo.append((node[3], 1 - axis))
        return None

    def walkable(self, x: float, y: float) -> bool:
        """Whether units can stand at (x, y), as the game decides it: there is ground where the index finds a circle
        holding the point (find), and when that circle owns a local map, only where the local map's own index finds
        one of its circles there too."""
        c = self.find(x, y)
        if c is None:
            return False
        return c >= len(self.subs) or self.subs[c].find(x, y) is not None

    def at(self, x: float, y: float) -> list[int]:
        """The circles that hold the point (x, y)."""
        return [i for i, (cx, cy, r, _l, _c) in enumerate(self.circles[:-1]) if (x - cx) ** 2 + (y - cy) ** 2 <= r * r]


# --- the mod file: maps/<map pack>/movement.toml (MOD_FORMAT §8) ---------------------------------------------------
UNITS = {"all": (1, 2), "infantry": (1,), "vehicles": (2,)}  # which of mapinfo.win's graphs a block changes


@dataclass
class Block:
    """Ground units can't use: a circle (map units) taken out of the infantry graph, the vehicles' or both. With
    `open`, the reverse: ground given to them where the graph has none (Graph.open_ground). Blocks and opens apply in
    order, so where two meet the later one wins. `spare`: an open the build made itself over a dried bed, which may
    be left out when the map's movement has no room for every open of its run (apply_blocks: the smallest first),
    and isn't told of one by one when it opens nothing."""
    x: float
    y: float
    radius: float
    units: str = "all"
    open: bool = False
    spare: bool = False


def closing(blocks) -> list[Block]:
    """The blocks that take ground away (not the opens): what bridges, roads and the cover check keep clear of."""
    return [b for b in blocks if not b.open]


def parse_blocks(items, where: str = "movement.toml", table: str = "block") -> list[Block]:
    """movement.toml's [[block]] tables, or with table="open" its [[open]] ones (Block.open)."""
    out = []
    for n, b in enumerate(items or [], start=1):
        at = f"{where}: {table} {n}"
        if not isinstance(b, dict):
            raise NavError(f"{at} isn't a table")
        extra = sorted(set(b) - {"x", "y", "radius", "units"})
        if extra:
            raise NavError(f"{at}: unknown key {extra[0]!r}")
        for k in ("x", "y", "radius"):
            if k not in b:
                raise NavError(f"{at}: {k} is missing")
            if isinstance(b[k], bool) or not isinstance(b[k], (int, float)):
                raise NavError(f"{at}: {k} must be a number")
        if b["radius"] <= 0:
            raise NavError(f"{at}: radius must be more than 0")
        units = b.get("units", "all")
        if units not in UNITS:
            raise NavError(f"{at}: units must be one of {', '.join(UNITS)}")
        out.append(Block(float(b["x"]), float(b["y"]), float(b["radius"]), units, table == "open"))
    return out


def blocks_toml(blocks: list[Block], header: str = "") -> str:
    """A movement file: the blocks as [[block]] tables, then the opens as [[open]] ones (the build applies a file's
    blocks first, then its opens)."""
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for b in sorted(blocks, key=lambda b: b.open):
        lines += ["[[open]]" if b.open else "[[block]]", f"x = {b.x!r}", f"y = {b.y!r}", f"radius = {b.radius!r}",
                  f'units = "{b.units}"', ""]
    return "\n".join(lines)


def wet_opens(blocks, water, step: float = 4 * STEP) -> list[tuple[Block, tuple[float, float]]]:
    """The opens (Block.open) with water inside them, each with a wet spot (`water(x, y)`: bridges.Water.at), sampled
    every `step`: units given ground there stand on the bed under the water (an opened river puts them on the
    riverbed), which the build allows with a warning."""
    out = []
    for b in blocks:
        if not b.open:
            continue
        k = max(1, int(b.radius // step))
        wet = [(i * i + j * j, (b.x + i * step, b.y + j * step)) for j in range(-k, k + 1) for i in range(-k, k + 1)
               if (i * step) ** 2 + (j * step) ** 2 < b.radius ** 2 and water(b.x + i * step, b.y + j * step)]
        if wet:
            out.append((b, min(wet)[1]))  # the wet spot nearest its middle
    return out


def replace_buffers(win: bytes, new: dict) -> bytes:
    """mapinfo.win with buffers replaced ({number: bytes}) and its salted MD5 made again (sdb.replace_buffer4's rule)."""
    import hashlib
    from ruse_mod_engine import sdb
    parts = sdb.split_mapinfo(win)
    if not parts:
        raise NavError("not a mapinfo.win")
    header48, bufs, trailing = parts
    bufs = [new.get(i, b) for i, b in enumerate(bufs)]
    out = bytearray(header48 + b"".join(struct.pack("<I", len(b)) + b for b in bufs) + trailing)
    out[8:24] = hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + bytes(out[24:])).digest()
    return bytes(out)


def apply_blocks(read, pack: str, blocks: list[Block], idle: list | None = None) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map; `read(member)` gives a DataMap_Win.dat file's bytes or None.
    Blocks and opens (Block.open) apply in order, a run of blocks at once (Graph.block), then a run of opens
    (Graph.open_ground), and so on: where two meet, the later one wins. The opens that opened nothing in any graph
    they name (the ground was open already, or they reach no ground units use) go into `idle`."""
    from ruse_mod_engine import sdb
    from .cover import PACK, member
    name = member(pack)
    win = read(name)
    if win is None:
        raise NavError(f"{pack} has no {name} in {PACK}, so its movement can't be changed")
    bufs = sdb.split_mapinfo(win)[1]
    new, notes, roads = {}, [], []

    def road_net():  # the road network (buffer 0), read once if a crossing's road needs following
        if not roads:
            from .roadnet import RoadNet
            roads.append(RoadNet.read(bufs[0]))
        return roads[0]
    opened = set()  # the opens (their numbers in `blocks`) that opened something in a graph
    for k, what in ((1, "infantry"), (2, "vehicles")):
        mine = [(i, b) for i, b in enumerate(blocks) if k in UNITS[b.units]]
        if not mine:
            continue
        g = Graph.read(bufs[k])
        runs: list[list] = []  # [open?, [(number, Block)]]: blocks and opens in order, each run applied at once
        for i, b in mine:
            if runs and runs[-1][0] == b.open:
                runs[-1][1].append((i, b))
            else:
                runs.append([b.open, [(i, b)]])
        for is_open, run in runs:
            zones = [(b.x, b.y, b.radius) for _i, b in run]
            if is_open:
                g, c, left, under = _open_what_fits(g, run)
                idle_here = set(c["idle"])
                opened |= {run[j][0] for j in range(len(run)) if j not in idle_here}
                notes.append(f"{what}: {len(zones)} open(s); {c['added']} circle(s) and {c['linked']} link(s) added, "
                             f"{c['local']} circle(s) in towns' and bridges' own movement")
                if left:
                    notes.append(f"{what}: the map's movement has no room for all of the dried bed: the {left} "
                                 f"smallest of its zones (under {under / METRE:.0f} m, by its shores) stay closed to "
                                 f"units; the rest is opened")
                if c["left_out"]:
                    notes.append(f"{what}: {c['left_out']} circle(s) left out: ground no unit could reach from the "
                                 f"rest (an order onto it would crash the game)")
                continue
            # never shrink a circle that owns a local map (a town, a bridge of the map's): the game decides what is
            # ground inside such a circle from its local map, so shrinking it opens everything the local map kept
            # closed, water beside the map's own bridges included (seen in the game, 2026-10-01: an infantry squad
            # standing in the river beside a bridge of the map's own, on a map where the mod had only placed
            # buildings). The block goes into those local maps instead (Graph.block walks them).
            c = g.block(zones, keep_owners=True)
            notes.append(f"{what}: {len(zones)} block(s); {c['emptied']} circle(s) emptied, {c['shrunk']} shrunk, "
                         f"{c['links']} link(s) and {c['crossings']} crossing(s) taken out; {c['added']} circle(s) "
                         f"and {c['linked']} link(s) added to fill the ground back")
        zones = [(b.x, b.y, b.radius) for _i, b in mine if not b.open]
        cut = _drop_cut_off(g)
        if cut:
            notes.append(f"{what}: {cut} circle(s) the blocks cut off from the rest taken out too (no unit could "
                         f"reach them, and an order onto them crashes the game)")
        through = g.drop_crossings_through(road_net, zones) if zones else 0
        if through:
            notes.append(f"{what}: {through} crossing(s) whose road ran through a block taken out (units routed "
                         f"along that road drove through it; the road stays for supply trucks)")
        new[k] = g.to_bytes()
    if idle is not None:
        idle += [b for i, b in enumerate(blocks) if b.open and i not in opened and not b.spare]
    return {name: replace_buffers(win, new)}, notes


def _open_what_fits(g: "Graph", run: list) -> tuple["Graph", dict, int, float]:
    """Graph.open_ground for a run of opens [(number, Block)], leaving out as few of the spare ones (Block.spare) as
    it takes for the graph to hold the rest: (the graph, open_ground's counts, how many spare opens were left out,
    the radius under which they were). A graph that can't hold the opens refuses them (NavError); the run is then
    tried again on the graph as it was, without the spare opens under twice the smallest's radius, then four times,
    and so on: the narrow ends of a dried bed go before its wide middle. With no spare open in the run, or when the
    rest doesn't fit even without any of them, the refusal stands."""
    import copy
    zones = [(b.x, b.y, b.radius) for _i, b in run]
    radii = sorted(b.radius for _i, b in run if b.spare and b.radius > 0)
    if not radii:
        return g, g.open_ground(zones), 0, 0.0
    before = copy.deepcopy(g)
    under = 0.0
    while True:
        try:
            counts = g.open_ground([z if not b.spare or b.radius >= under else (z[0], z[1], 0.0)
                                    for z, (_i, b) in zip(zones, run)])
            return g, counts, sum(1 for r in radii if r < under), under
        except NavError:
            if under > radii[-1]:
                raise  # (not even without any of them)
            g = copy.deepcopy(before)
            under = max(2 * under, 2 * radii[0])


def _wide_zones(kind: bytearray, nx: int, ny: int, x0: float, y0: float, s: float, over: float, most: float) -> list:
    """Zones (x, y, r) over the wide stretches of a dried bed, the largest first, for water_blocks: `kind` says what
    each sample of its grid (nx x ny, `s` apart from x0, y0) is: 1 dried bed, 2 under water now or outside the areas
    (not known), 0 other ground. Each zone is centred on a dried sample no earlier zone holds and reaches the nearest
    sample that isn't dried bed (half a step short of a kind 2 one: the water left stays out), `most` at most; only
    zones over `over` are made. No sample inside a zone is anything but dried bed: each zone is measured against
    every sample within its reach before it is taken (the sweeps before that only say where the room is)."""
    if 1 not in kind:
        return []
    near = [k if kind[k] != 1 else -1 for k in range(nx * ny)]  # the nearest sample that isn't dried bed (its place)
    for rows, steps in ((range(ny), ((-1, -1), (0, -1), (1, -1), (-1, 0))),
                        (range(ny - 1, -1, -1), ((1, 1), (0, 1), (-1, 1), (1, 0)))):
        columns = range(nx) if steps[0][1] < 0 else range(nx - 1, -1, -1)
        for j in rows:
            for i in columns:
                at = j * nx + i
                if kind[at] != 1:
                    continue
                best, far = near[at], -1
                if best >= 0:
                    far = (i - best % nx) ** 2 + (j - best // nx) ** 2
                for di, dj in steps:
                    a, b = i + di, j + dj
                    if 0 <= a < nx and 0 <= b < ny:
                        k = near[b * nx + a]
                        if k >= 0:
                            d = (i - k % nx) ** 2 + (j - k // nx) ** 2
                            if far < 0 or d < far:
                                best, far = k, d
                near[at] = best
    order = []
    for at in range(nx * ny):
        if kind[at] == 1 and near[at] >= 0:
            i, j = at % nx, at // nx
            r = min(math.sqrt((i - near[at] % nx) ** 2 + (j - near[at] // nx) ** 2) * s, most)
            if r > over:
                order.append((-r, i, j))
    order.sort()
    held = bytearray(nx * ny)
    zones = []
    for r, i, j in order:
        if held[j * nx + i]:
            continue
        r = -r
        reach = int(r / s) + 1
        a0, a1, b0, b1 = max(i - reach, 0), min(i + reach, nx - 1), max(j - reach, 0), min(j + reach, ny - 1)
        for b in range(b0, b1 + 1):  # measured: every sample within reach that isn't dried bed holds it back
            row, dj2 = b * nx, (b - j) ** 2
            for a in range(a0, a1 + 1):
                k = kind[row + a]
                if k != 1:
                    d = math.sqrt((a - i) ** 2 + dj2) * s - (s / 2 if k == 2 else 0.0)
                    if d < r:
                        r = d
        if r <= over:
            continue
        zones.append((x0 + i * s, y0 + j * s, r))
        inside = (r / s) ** 2
        for b in range(b0, b1 + 1):
            row, dj2 = b * nx, (b - j) ** 2
            for a in range(a0, a1 + 1):
                if (a - i) ** 2 + dj2 < inside:
                    held[row + a] = 1
    return zones


def water_blocks(old_at, new_at, areas, wide: list | None = None, wide_over: float = 0.0,
                 wide_most: float = math.inf) -> tuple[list[tuple[float, float, float]], list[tuple[float, float]]]:
    """Blocks (x, y, r) over the water terrain edits made, and the places they drained. On every shipped map ground
    under water is never walkable (0.1% of wet samples at most, on both graphs), but the water and height brushes
    change only the ground files: units would walk the bed of a new lake. `old_at(x, y)` and `new_at(x, y)` say where
    the map had water and has it now (bridges.Water.at); `areas` are the strokes' circles (x, y, r: nothing changed
    outside them).

    Each group of overlapping areas is sampled on a square grid (a step of 640, or more for big areas: at most about
    250 samples across one). The new water (wet now, dry before) is covered by circles, the biggest first: each
    centred on a sample whose square (a step a side) no circle holds yet, reaching half a step short of the nearest
    sample that is neither new nor old water (the shore), at least 3/4 of a step (its own square): every new water
    sample's square is blocked, and dry ground at most about half a step past the shore. Returns (the blocks, the
    drained samples: wet before, dry now). Units can't walk a drained bed either until it's opened (the graphs have no
    ground there).

    `wide`: a list, filled with zones (x, y, r) over the wide stretches of the dried beds for the build to open
    (_wide_zones: each as big as the bed has room for, over `wide_over`, `wide_most` at most). A sea drained is a
    quarter of a million samples: small zones over all of it ask for more circles than a graph holds (65,535), while
    the shipped maps cover their open ground with a few thousand, up to 135,040 across on M04_Cotentin."""
    groups: list[list[tuple[float, float, float]]] = []
    for a in areas:  # areas that overlap go together
        into = [g for g in groups if any(math.hypot(a[0] - b[0], a[1] - b[1]) < a[2] + b[2] for b in g)]
        merged = [a] + [b for g in into for b in g]
        groups = [g for g in groups if g not in into] + [merged]
    zones, drained = [], []
    for g in groups:
        s = max(2 * STEP, math.ceil(max(r for _x, _y, r in g) / 125.0 / STEP) * STEP)
        x0 = math.floor(min(x - r for x, _y, r in g) / s) * s - s
        y0 = math.floor(min(y - r for _x, y, r in g) / s) * s - s
        nx = int(math.ceil((max(x + r for x, _y, r in g) - x0) / s)) + 2
        ny = int(math.ceil((max(y + r for _x, y, r in g) - y0) / s)) + 2
        fresh = set()       # new water samples (i, j)
        seed = {}           # the nearest sample that is neither new nor old water, for every sample: (i, j)
        kind = bytearray(nx * ny) if wide is not None else None  # for _wide_zones: what each sample is
        for j in range(ny):
            for i in range(nx):
                x, y = x0 + i * s, y0 + j * s
                if not any((x - ax) ** 2 + (y - ay) ** 2 <= ar * ar for ax, ay, ar in g):
                    seed[i, j] = (i, j)
                    if kind is not None:
                        kind[j * nx + i] = 2  # outside the areas: water or not, it wasn't asked
                    continue
                now, before = bool(new_at(x, y)), bool(old_at(x, y))
                if now and not before:
                    fresh.add((i, j))
                elif before and not now:
                    drained.append((x, y))
                if not (now or before):
                    seed[i, j] = (i, j)
                if kind is not None and (now or before):
                    kind[j * nx + i] = 2 if now else 1
        if kind is not None:
            wide += _wide_zones(kind, nx, ny, x0, y0, s, wide_over, wide_most)
        if not fresh:
            continue

        def d2(i, j, k):
            return (i - k[0]) ** 2 + (j - k[1]) ** 2
        for order, steps in ((range(ny), ((-1, -1), (0, -1), (1, -1), (-1, 0))),  # the nearest shore sample of each,
                             (range(ny - 1, -1, -1), ((1, 1), (0, 1), (-1, 1), (1, 0)))):  # in two sweeps
            for j in order:
                for i in (range(nx) if steps[0][1] < 0 else range(nx - 1, -1, -1)):
                    best = seed.get((i, j))
                    for di, dj in steps:
                        k = seed.get((i + di, j + dj))
                        if k is not None and (best is None or d2(i, j, k) < d2(i, j, best)):
                            best = k
                    if best is not None:
                        seed[i, j] = best
        left = set(fresh)
        for i, j in sorted(fresh, key=lambda p: (-d2(*p, seed[p]), p)):
            if (i, j) not in left:
                continue
            r = max(math.sqrt(d2(i, j, seed[i, j])) * s - s / 2, 0.75 * s)
            zones.append((x0 + i * s, y0 + j * s, r))
            reach = int(r // s)
            for a in range(i - reach, i + reach + 1):  # the samples whose whole square it holds are done
                for b in range(j - reach, j + reach + 1):
                    if (a, b) in left and math.hypot(a - i, b - j) * s + 0.71 * s <= r:
                        left.discard((a, b))
    return zones, drained


def _drop_cut_off(g: Graph) -> int:
    """After blocks: every local map, and then the main graph, kept in one piece (as every shipped graph is). A local
    map's cut-off pieces go first; an owner whose local map has no ground left goes too (no route could pass it);
    then the main graph's cut-off pieces. Returns how many circles went."""
    cut = sum(s.drop_cut_off() for s in g.subs)
    dead = {k for k, s in enumerate(g.subs) if g.circles[k][2] > 0 and not s.parts()}
    if dead:
        g._empty(dead)
        cut += len(dead)
    return cut + g.drop_cut_off()


# --- filling ground back after a block ------------------------------------------------------------------------------
class _Buckets:
    """Circles by place, for finding the ones that may overlap a circle."""

    def __init__(self, circles, size: float = 20480.0):
        self.circles, self.size, self.cells = circles, size, {}
        for i, (x, y, r) in enumerate(circles):
            if r > 0:
                for key in self._keys(x, y, r):
                    self.cells.setdefault(key, []).append(i)

    def _keys(self, x, y, r):
        s = self.size
        return [(i, j) for i in range(int((x - r) // s), int((x + r) // s) + 1)
                for j in range(int((y - r) // s), int((y + r) // s) + 1)]

    def add(self, circle) -> int:
        """One more circle, put at the end of the list the buckets were made with; returns its number."""
        self.circles.append(circle)
        i = len(self.circles) - 1
        if circle[2] > 0:
            for key in self._keys(*circle):
                self.cells.setdefault(key, []).append(i)
        return i

    def around(self, c):
        return self.near(*self.circles[c])

    def near(self, x, y, r):
        """The circles that may overlap a circle at (x, y) of radius r."""
        seen = set()
        for key in self._keys(x, y, r):
            for d in self.cells.get(key, ()):
                if d not in seen:
                    seen.add(d)
                    yield d


def _side(radii: list) -> float:
    """A bucket side for circles of these radii: twice the middle one, between 4 STEP and _Buckets' own 20480."""
    live = sorted(r for r in radii if r > 0)
    return max(4 * STEP, min(20480.0, 2 * live[len(live) // 2])) if live else 20480.0


def _meeting(p, q) -> tuple[float, float] | None:
    """Where two circles meet, for a link: the middle of their overlap along the line between their centres, when
    they overlap by STEP or more."""
    (ax, ay, ar), (bx, by, br) = p, q
    d = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    if d == 0 or ar + br - d < STEP:
        return None
    t = (d - br + ar) / 2 / d
    return (ax + (bx - ax) * t, ay + (by - ay) * t)


def _seg_dist(x: float, y: float, span) -> float:
    """How far (x, y) is from the segment `span` (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = span
    dx, dy = x1 - x0, y1 - y0
    n = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / n)) if n else 0.0
    return math.hypot(x - x0 - t * dx, y - y0 - t * dy)


def _cells(x0: float, y0: float, x1: float, y1: float, size: float):
    """The grid cells (i, j) of side `size` a box touches."""
    return [(i, j) for i in range(int(x0 // size), int(x1 // size) + 1) for j in range(int(y0 // size), int(y1 // size) + 1)]


def _gate_line(c, o, gate) -> tuple | None:
    """A gate's line: through the link's point `gate`, square to the line from circle c's middle to circle o's (both
    x, y, r), as far as it stays inside both circles; its two ends, or None. The shipped crossings' points lie on it
    (892 of 892 on D-Day, within 0.4 map units)."""
    (cx, cy, cr), (ox, oy, orad), (gx, gy) = c, o, gate
    d = math.hypot(ox - cx, oy - cy)
    if d == 0:
        return None
    ux, uy = (ox - cx) / d, (oy - cy) / d
    lo, hi = -math.inf, math.inf
    for x, y, r in ((cx, cy, cr), (ox, oy, orad)):
        off = (gx - x) * ux + (gy - y) * uy  # how far the line is from this middle
        if abs(off) >= r:
            return None
        half = math.sqrt(r * r - off * off)
        at = (gx - x) * -uy + (gy - y) * ux  # where the gate is along the line, from this middle's foot
        lo, hi = max(lo, -half - at), min(hi, half - at)
    if lo >= hi:
        return None
    return (gx - uy * lo, gy + ux * lo), (gx - uy * hi, gy + ux * hi)


def _crossing_at(p, q, a, b) -> tuple[float, float] | None:
    """Where segment p-q crosses segment a-b: (how far along p-q, how far along a-b), both 0..1, or None."""
    rx, ry = q[0] - p[0], q[1] - p[1]
    sx, sy = b[0] - a[0], b[1] - a[1]
    den = rx * sy - ry * sx
    if den == 0:
        return None
    t = ((a[0] - p[0]) * sy - (a[1] - p[1]) * sx) / den
    u = ((a[0] - p[0]) * ry - (a[1] - p[1]) * rx) / den
    return (t, u) if 0 <= t <= 1 and 0 <= u <= 1 else None


def _on_way(point, used: set, spans: dict) -> bool:
    """Whether a gate's point (gate, road link, how far along it, x, y) lies on a crossing's way: on a road link it
    runs all along (`used`), or inside the part of its first or last link it runs (`spans`: link -> (from, to))."""
    _g, rl, u, _x, _y = point
    if rl in used:
        return True
    lo, hi = spans.get(rl, (2.0, -1.0))
    return lo + 1e-6 < u < hi - 1e-6


def _heads_in(line, middle, other) -> bool:
    """Whether the way `line` (points), from its first point (on a gate), heads into the circle whose middle is
    `middle`: away from `other`, the middle of the circle on the gate's other side."""
    x0, y0 = line[0]
    for x, y in line[1:]:
        if math.hypot(x - x0, y - y0) > 1.0:
            return (x - x0) * (middle[0] - other[0]) + (y - y0) * (middle[1] - other[1]) > 0
    return False


def _along(line, step: float):
    """Points along the polyline `line`, at most `step` apart, its ends included."""
    yield line[0]
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        k = max(1, math.ceil(math.hypot(bx - ax, by - ay) / step))
        for i in range(1, k + 1):
            yield ax + (bx - ax) * i / k, ay + (by - ay) * i / k


GAP = 2 * STEP  # the most of a crossing's road that may run off ground units stand on: the shipped crossings in towns
                # (a local map's) cross slips of up to a few thousand between its circles, but no building is this
                # narrow (most of those slips are under 640, 2026-10-01)


def _open_along(walkable, line) -> bool:
    """Whether `walkable(x, y)` holds all along the polyline `line` (sampled every STEP / 4), but for stretches
    shorter than GAP."""
    step, run = STEP / 4, 0.0
    for x, y in _along(line, step):
        run = 0.0 if walkable(x, y) else run + step
        if run >= GAP:
            return False
    return True


def _owner_middle(span) -> tuple[float, float, float]:
    """Where a deck's owner circle goes (x, y, and its least radius): the deck's middle on the STEP grid, and the
    least radius on the grid that holds the whole deck."""
    x0, y0, x1, y1 = span
    cx, cy = round((x0 + x1) / 2 / STEP) * STEP, round((y0 + y1) / 2 / STEP) * STEP
    low = math.ceil(max(math.hypot(x0 - cx, y0 - cy), math.hypot(x1 - cx, y1 - cy)) / STEP) * STEP
    return float(cx), float(cy), float(low)


def _dry_part(water, x: float, y: float, r: float) -> tuple[float, float, float] | None:
    """The circle shrunk by STEP at a time until none of it is over water (_wet), or None when less than STEP is
    left."""
    while r >= STEP and _wet(water, x, y, r):
        r -= STEP
    return (x, y, float(r)) if r >= STEP else None


def _under(circles, span, water) -> list[int]:
    """The circles (x, y, r) of an old deck under a new one along `span`: their middles over `water(x, y)` (none
    without it), reaching within 2 LOCAL_RADIUS of the new deck's line."""
    if water is None:
        return []
    return [i for i, (x, y, r) in enumerate(circles) if r > 0 and _seg_dist(x, y, span) < r + 2 * LOCAL_RADIUS
            and water(x, y)]


def _wet(water, x: float, y: float, r: float) -> bool:
    """Whether a circle reaches over water (`water(x, y)`, or None for none): its middle, 16 points on its rim and 8
    halfway out are tested, not its middle alone."""
    if water is None:
        return False
    points = [(x, y)] + [(x + r * math.cos(math.pi * k / 8), y + r * math.sin(math.pi * k / 8)) for k in range(16)] \
        + [(x + r / 2 * math.cos(math.pi * (k + 0.5) / 4), y + r / 2 * math.sin(math.pi * (k + 0.5) / 4)) for k in range(8)]
    return any(water(px, py) for px, py in points)


def _nearest_on(line, p) -> tuple[float, int, float] | None:
    """(distance, segment, how far along it 0..1) of the point of the polyline `line` nearest `p`."""
    best = None
    for i in range(len(line) - 1):
        (ax, ay), (bx, by) = line[i], line[i + 1]
        dx, dy = bx - ax, by - ay
        n = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / n)) if n else 0.0
        d = math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)
        if best is None or d < best[0]:
            best = (d, i, t)
    return best


def _arc(line, i: int, t: float) -> float:
    """How far along the polyline `line` the point at segment i, t lies."""
    return sum(math.dist(line[j], line[j + 1]) for j in range(i)) + t * math.dist(line[i], line[i + 1])


def _walk_out(at, out, roads, step: float, reach: float, away=None):
    """(how far, (x, y)) every `step` map units from `at`, up to `reach`: along the road line nearest `at` (within
    2,560), the way that leads off the deck (away from `away`, the deck's other end, along the road; else along
    `out`), then straight on past the road's end; straight along `out` when no road is that near."""
    ox, oy = out
    norm = math.hypot(ox, oy) or 1.0
    ox, oy = ox / norm, oy / norm
    best = None
    for line in roads:
        got = _nearest_on(line, at)
        if got is not None and got[0] <= 2560.0 and (best is None or got[0] < best[0]):
            best = got + (line,)
    path = [tuple(at)]
    if best is not None:
        _d, i, t, line = best
        (ax, ay), (bx, by) = line[i], line[i + 1]
        forward = None
        other = _nearest_on(line, away) if away is not None else None
        if other is not None and other[0] <= 2560.0:  # the road runs over the deck: off it is away from its other end
            here, there = _arc(line, i, t), _arc(line, other[1], other[2])
            if here != there:
                forward = here > there
        if forward is None:
            forward = (bx - ax) * ox + (by - ay) * oy >= 0
        path.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        path += [tuple(p) for p in (line[i + 1:] if forward else reversed(line[:i + 1]))]
    dx, dy = ox, oy
    for (ax, ay), (bx, by) in zip(reversed(path[:-1]), reversed(path[1:])):  # on in the road's last direction
        seg = math.hypot(bx - ax, by - ay)
        if seg > 0:
            dx, dy = (bx - ax) / seg, (by - ay) / seg
            break
    path.append((path[-1][0] + dx * reach, path[-1][1] + dy * reach))
    walked, target = 0.0, step
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        seg = math.hypot(bx - ax, by - ay)
        while seg > 0 and target <= walked + seg:
            if target > reach:
                return
            t = (target - walked) / seg
            yield target, (ax + (bx - ax) * t, ay + (by - ay) * t)
            target += step
        walked += seg


def _fill(sources, zones, now, least: float = MIN_RADIUS, kept=None) -> list:
    """New circles over the ground `sources` (the old circles that were emptied or shrunk) covered and no circle
    in `now` covers any more, outside the zones: each inside one source circle and clear of every zone, centres on
    the STEP grid, the largest first, each on ground no circle covers yet, down to `least` (MIN_RADIUS).
    (x, y, r, the source it lies deepest in) each. `kept`: the radius each source has now, when it is still in `now`
    with it (0 for an emptied one): its spots inside that are covered, and passed over at once. (Ground opened where
    the graph had none is grown from the ground units can reach instead: _grow.)"""
    live = [c for c in now if c[2] > 0]
    # buckets about as big as the circles (a circle that holds a spot is in the spot's bucket whatever their size,
    # and fewer others are): the few nearby, not the many in a big square, looked at for each spot
    side = _side([c[2] for c in live])
    near = _Buckets(live, side)
    placed = _Buckets([], side)  # the new circles so far

    def covered(x, y, extra=None):
        key = (int(x // near.size), int(y // near.size))
        return any((x - live[i][0]) ** 2 + (y - live[i][1]) ** 2 < live[i][2] ** 2 for i in near.cells.get(key, ())) \
            or extra is not None and any((x - extra.circles[i][0]) ** 2 + (y - extra.circles[i][1]) ** 2
                                         < extra.circles[i][2] ** 2 for i in extra.cells.get(key, ()))

    # square by square of the sources' buckets: the spots in a square are those of the sources it holds, and their
    # holders are those sources, so only one square's spots are remembered at a time; a spot no source holds is never
    # deep enough to take. Their order is the sort's below.
    # A spot is taken when it lies `least` deep or more in a source, has that much room clear of every zone, and no
    # live circle covers it: the tests in the order that drops the most spots the soonest (most lie under a zone or
    # under what their own circle keeps), each spot weighed against the few circles and zones near it
    step = 2 * STEP
    spots = []
    holders, bounds = _Buckets(list(sources), _side([sr for _x, _y, sr in sources])), _Buckets(list(zones))
    size, wide = holders.size, bounds.size

    def span(lo: int, hi: int, c: int) -> range:
        """The grid indices lo..hi whose spots (index * step) lie in bucket row or column c (int(spot // size))."""
        a, b = max(lo, int(c * size // step) - 1), min(hi, int((c + 1) * size // step) + 1)
        while a <= b and int(a * step // size) < c:
            a += 1
        while b >= a and int(b * step // size) > c:
            b -= 1
        return range(a, b + 1)
    for (ci, cj), mine in holders.cells.items():
        seen = set()
        for own in mine:
            sx, sy, sr = sources[own]
            keeps = kept[own] ** 2 if kept is not None else 0.0
            for i in span(int((sx - sr) // step), int((sx + sr) // step), ci):
                x = i * step
                for j in span(int((sy - sr) // step), int((sy + sr) // step), cj):
                    y = j * step
                    if (x - sx) ** 2 + (y - sy) ** 2 < keeps or (i, j) in seen:
                        continue  # under what its own circle keeps (a live circle: covered), or weighed already
                    seen.add((i, j))
                    # the zones in its own square first: under one, or too near one, it has no room
                    room = min((((x - zones[k][0]) ** 2 + (y - zones[k][1]) ** 2) ** 0.5 - zones[k][2]
                                for k in bounds.cells.get((int(x // wide), int(y // wide)), ())), default=math.inf)
                    if room < least or covered(x, y):
                        continue
                    deep, source = max(((sources[k][2] - ((x - sources[k][0]) ** 2 + (y - sources[k][1]) ** 2) ** 0.5,
                                         k) for k in mine), default=(-1.0, 0))
                    if deep < least:
                        continue
                    # its room: how far the nearest zone's rim is, when nearer than it lies deep. A zone farther
                    # than that can't make it less: so only as far out as the least found so far leaves to look
                    room, reach = min(room, deep), 1.0
                    while reach < room + 1.0:
                        reach = min(room + 1.0, 2 * reach + wide)
                        room = min([room] + [((x - zones[k][0]) ** 2 + (y - zones[k][1]) ** 2) ** 0.5 - zones[k][2]
                                             for k in bounds.near(x, y, reach)])
                    room = (room // STEP) * STEP
                    if room >= least:
                        spots.append((room, x, y, source))
    spots.sort(key=lambda s: (-s[0], s[1], s[2]))
    out = []  # (x, y, r, the source circle it lies deepest in)
    for r, x, y, source in spots:
        if not covered(x, y, placed):
            out.append((float(x), float(y), float(r), source))
            placed.add((float(x), float(y), float(r)))
    return out


# --- opening ground (Graph.open_ground) ---------------------------------------------------------------------------
NEAR = 16  # spots with up to this many STEPs of room are looked for round each old circle (which of them meet it);
           # one with more looks round itself for the old circles, when its turn comes
RING = 24  # with no more room than this on a grid, the places round a new circle where a spot could meet it are
           # listed once for its size; with more, they are gone through square by square of TILE spots, past the
TILE = 32  # squares whose spots have too little room to reach it


class _Spots:
    """The spots new circles may go on when ground is opened (_grow), as a grid: the points of the 2 STEP grid inside
    `box` (x0, y0, x1, y1) that lie `least` or more inside a zone (x, y, r), each with its room: how deep it lies in
    the zone it lies deepest in, in whole STEPs (`room`: 0 where there is no spot, or no more: one inside a circle is
    dropped), and whether it has a turn coming (`due`). A place is a spot's number on the grid (row by row along y,
    the rows along x): the order of two spots with the same room is the order of their places.

    A number and a byte for each point, whatever the zones: a whole map drained across (a quarter of a million zones,
    thirteen million spots) takes tens of megabytes, where a list of the spots took gigabytes."""

    def __init__(self, zones, least: float, box):
        step = self.step = 2 * STEP
        zones = [z for z in zones if z[2] >= least]  # (a smaller one has no spot with that much room)
        self.ni = self.nj = self.top = 0

        def first(v):  # the first grid line at v or past it
            k = int(v // step)
            return k if k * step >= v else k + 1
        if not zones:
            return
        i0 = max(first(box[0]), min(int((x - r) // step) for x, _y, r in zones))
        j0 = max(first(box[1]), min(int((y - r) // step) for _x, y, r in zones))
        i1 = min(int(box[2] // step), max(int((x + r) // step) for x, _y, r in zones))
        j1 = min(int(box[3] // step), max(int((y + r) // step) for _x, y, r in zones))
        if i1 < i0 or j1 < j0:
            return
        self.i0, self.j0, self.ni, self.nj = i0, j0, i1 - i0 + 1, j1 - j0 + 1
        ni, nj = self.ni, self.nj
        most = int(max(r for _x, _y, r in zones) // STEP)  # no spot has more room than the largest zone's radius
        # a byte each while the rooms fit one (searched at once for the spots of one room: walk); wider numbers past it
        self.wide = None if most < 2 ** 8 else "H" if most < 2 ** 16 else "I" if most < 2 ** 32 else "Q"
        room = self.room = bytearray(ni * nj) if self.wide is None else \
            array(self.wide, bytes(ni * nj * array(self.wide).itemsize))
        self.due = bytearray(ni * nj)
        self._spans, self._rings, self._tiles, self._places, self._zero = {}, {}, None, None, None
        kinds: dict = {}  # zones of one radius whose middles sit alike in their grid squares hold the same spots
        spare = 400000    # the most spots those lists may hold between them (some tens of megabytes)
        top = 0
        for sx, sy, sr in zones:
            kind = None
            if sr <= 64 * step and sx % 1 == 0 and sy % 1 == 0 and abs(sx) < 2.0 ** 40 and abs(sy) < 2.0 ** 40:
                # a middle on whole units: every spot's distance to it is worked out from whole numbers, the same
                # whichever grid square the middle is in, so the spots are listed once for all such zones
                ox, oy = sx % step, sy % step
                kind = kinds.get((sr, ox, oy))
                if kind is None and (2 * sr / step + 2) ** 2 <= spare:
                    cells = []
                    for di in range(int((ox - sr) // step), int((ox + sr) // step) + 1):
                        for dj in range(int((oy - sr) // step), int((oy + sr) // step) + 1):
                            deep = sr - ((di * step - ox) ** 2 + (dj * step - oy) ** 2) ** 0.5
                            if deep >= least and (deep // STEP) * STEP >= least:
                                cells.append((di, dj, int(deep // STEP)))
                    kind = kinds[sr, ox, oy] = (cells, [(di * nj + dj, lv) for di, dj, lv in cells],
                                                min((c[0] for c in cells), default=0),
                                                max((c[0] for c in cells), default=0),
                                                min((c[1] for c in cells), default=0),
                                                max((c[1] for c in cells), default=0))
                    top = max([top] + [lv for _di, _dj, lv in cells])
                    spare -= len(cells)
            if kind is not None:
                cells, flat, da, db, ea, eb = kind
                if not cells:
                    continue
                ci, cj = int(sx // step) - i0, int(sy // step) - j0
                if ci + da >= 0 and ci + db < ni and cj + ea >= 0 and cj + eb < nj:
                    base = ci * nj + cj
                    for off, lv in flat:
                        if room[base + off] < lv:
                            room[base + off] = lv
                else:
                    for di, dj, lv in cells:
                        if 0 <= ci + di < ni and 0 <= cj + dj < nj and room[(ci + di) * nj + cj + dj] < lv:
                            room[(ci + di) * nj + cj + dj] = lv
                continue
            reach = sr - least + 1.0  # a spot farther from the middle hasn't the room
            for i in range(max(i0, int((sx - sr) // step)), min(i1, int((sx + sr) // step)) + 1):
                x = i * step
                dx2 = (x - sx) ** 2
                if dx2 > reach * reach:
                    continue
                h = math.sqrt(reach * reach - dx2)
                ja, jb = max(j0, int((sy - h) // step)), min(j1, int((sy + h) // step) + 1)
                k = (i - i0) * nj + ja - j0
                for j in range(ja, jb + 1):
                    deep = sr - (dx2 + (j * step - sy) ** 2) ** 0.5
                    if deep >= least and (deep // STEP) * STEP >= least:
                        lv = int(deep // STEP)
                        if room[k] < lv:
                            room[k] = lv
                            if lv > top:
                                top = lv
                    k += 1
        self.top = top  # no spot has more room than this

    def at(self, place: int) -> tuple[float, float]:
        """A spot's point on the map."""
        i, j = divmod(place, self.nj)
        return (self.i0 + i) * self.step, (self.j0 + j) * self.step

    def _none(self, count: int):
        """`count` places with no spot, to write over a run of them."""
        return bytes(count) if self.wide is None else array(self.wide, bytes(count * self.room.itemsize))

    def empty(self) -> bool:
        return self.room.count(0) == len(self.room)

    def only(self, where) -> None:
        """Spots `where(x, y)` doesn't allow are no spots."""
        room, nj, step = self.room, self.nj, self.step
        for i in range(self.ni):
            x = (self.i0 + i) * step
            for j, lv in enumerate(room[i * nj:(i + 1) * nj]):
                if lv and not where(x, (self.j0 + j) * step):
                    room[i * nj + j] = 0

    def uncover(self, circles) -> None:
        """Spots inside a circle (x, y, r), its rim apart, are no spots: ground units have already."""
        room, step, i0, j0, nj = self.room, self.step, self.i0, self.j0, self.nj
        i1, j1 = i0 + self.ni - 1, j0 + nj - 1
        none = self._none(nj)
        for cx, cy, r in circles:
            if r <= 0 or cy + r < j0 * step or cy - r > j1 * step:
                continue
            rr = r ** 2
            for i in range(max(i0, int((cx - r) // step)), min(i1, int((cx + r) // step)) + 1):
                dx2 = (i * step - cx) ** 2
                if not dx2 < rr:  # (no point of this row is nearer)
                    continue
                # the row's spots inside it are one run: about these, then to the very ones by the test itself
                h = math.sqrt(rr - dx2)
                a, b = int((cy - h) // step) + 1, int((cy + h) // step)
                while dx2 + ((a - 1) * step - cy) ** 2 < rr:
                    a -= 1
                while dx2 + ((b + 1) * step - cy) ** 2 < rr:
                    b += 1
                while a <= b and not dx2 + (a * step - cy) ** 2 < rr:
                    a += 1
                while b >= a and not dx2 + (b * step - cy) ** 2 < rr:
                    b -= 1
                a, b = max(a, j0), min(b, j1)
                if a <= b:
                    k = (i - i0) * nj - j0
                    room[k + a:k + b + 1] = none[:b - a + 1]

    def rooms(self, low: int = 1) -> list[int]:
        """The rooms the spots left have, from `low` up, the most first."""
        if self.wide is None:
            return [lv for lv in range(self.top, low - 1, -1) if self.room.find(lv) >= 0]
        return sorted((lv for lv in self._listed() if lv >= low), reverse=True)

    def walk(self, lv: int):
        """The spots with `lv` STEPs of room, in order, each as it stands when it is come to (one dropped by then is
        passed over)."""
        room = self.room
        if self.wide is None:
            place = room.find(lv)
            while place >= 0:
                yield place
                place = room.find(lv, place + 1)
            return
        for place in self._listed().get(lv, ()):
            if room[place] == lv:
                yield place

    def _listed(self) -> dict:
        """(Rooms kept in wider numbers than a byte.) The spots there were when first asked: {room: their places, in
        order}."""
        if self._places is None:
            room, nj = self.room, self.nj
            got = self._places = {}
            code = "I" if len(room) < 2 ** 32 else "Q"
            for k in range(0, len(room), nj):
                row = room[k:k + nj]
                if row.count(0) == nj:
                    continue
                for j, lv in enumerate(row):
                    if lv:
                        if lv not in got:
                            got[lv] = array(code)
                        got[lv].append(k + j)
        return self._places

    def cover(self, place: int, lv: int) -> None:
        """A new circle with `lv` STEPs of room at `place`: the spots inside it (its rim apart, itself too) are spots
        no more."""
        room, nj, ni = self.room, self.nj, self.ni
        i, j = divmod(place, nj)
        reach = lv // 2 + 1
        if lv <= 64:  # a small circle's rows are kept for the next of its size (a dried bed has a million of them)
            spans = self._spans.get(lv)
            if spans is None:
                spans = self._spans[lv] = [(di, a, b, self._none(b - a + 1))
                                           for di, a, b in self._rows(lv, -reach, reach)]
            for di, a, b, none in spans:
                if 0 <= i + di < ni:
                    k = (i + di) * nj + j
                    if j + a >= 0 and j + b < nj:
                        room[k + a:k + b + 1] = none
                    else:
                        a, b = max(a, -j), min(b, nj - 1 - j)
                        room[k + a:k + b + 1] = none[:b - a + 1]
            return
        if self._zero is None:
            self._zero = self._none(nj)
        for di, a, b in self._rows(lv, max(-reach, -i), min(reach, ni - 1 - i)):  # (only its rows on the grid)
            a, b = max(a, -j), min(b, nj - 1 - j)
            room[(i + di) * nj + j + a:(i + di) * nj + j + b + 1] = self._zero[:b - a + 1]

    def _rows(self, lv: int, lo: int, hi: int):
        """Row by row of a circle with `lv` STEPs of room (rows `lo` to `hi`, counted from its middle's), the run of
        spots inside it, counted from its middle's column: (row, first, last). About these by a square root, then to
        the very ones by the test itself (as for an old circle, in uncover)."""
        step, rr = self.step, (lv * STEP) ** 2
        for di in range(lo, hi + 1):
            dx2 = (step * di) ** 2
            if not dx2 < rr:
                continue
            b = int(math.sqrt(max(lv * lv / 4.0 - di * di, 0.0)))
            a = -b
            while dx2 + (step * (a - 1)) ** 2 < rr:
                a -= 1
            while a < 0 and not dx2 + (step * a) ** 2 < rr:
                a += 1
            while dx2 + (step * (b + 1)) ** 2 < rr:
                b += 1
            while b > 0 and not dx2 + (step * b) ** 2 < rr:
                b -= 1
            yield di, a, b

    def met(self, place: int, lv: int) -> list:
        """The spots with no turn coming yet that meet a new circle with `lv` STEPs of room at `place`, for a link
        (_meeting: an overlap of STEP or more): [(place, room)]. (After cover: the spots inside it are gone.)"""
        room, due, nj, ni, step = self.room, self.due, self.nj, self.ni, self.step
        i, j = divmod(place, nj)
        r = lv * STEP
        got = []
        if self.top <= RING:
            ring = self._rings.get(lv)
            if ring is None:
                # every place a spot could meet it from, with the least room that does, by _meeting's own sums
                reach, cells = (lv + self.top) // 2 + 1, []
                for di in range(-reach, reach + 1):
                    for dj in range(-reach, reach + 1):
                        if (step * di) ** 2 + (step * dj) ** 2 < r ** 2:
                            continue  # inside it
                        d = ((step * -di) ** 2 + (step * -dj) ** 2) ** 0.5
                        need = max(1, int((d - r) // STEP) + 1)
                        while need > 1 and not (need - 1) * STEP + r - d < STEP:
                            need -= 1
                        while need <= self.top and need * STEP + r - d < STEP:
                            need += 1
                        if need <= self.top:
                            cells.append((di, dj, di * nj + dj, need))
                ring = self._rings[lv] = (reach, cells)
            reach, cells = ring
            if reach <= i < ni - reach and reach <= j < nj - reach:
                for _di, _dj, off, need in cells:
                    if room[place + off] >= need and not due[place + off]:
                        got.append((place + off, room[place + off]))
            else:
                for di, dj, off, need in cells:
                    if 0 <= i + di < ni and 0 <= j + dj < nj and room[place + off] >= need and not due[place + off]:
                        got.append((place + off, room[place + off]))
            return got
        tiles, tw = self._tiles or self._tile()
        reach = (lv + self.most) // 2 + 1
        lowered = False
        for ti in range(max(0, i - reach) // TILE, min(ni - 1, i + reach) // TILE + 1):
            a0, a1 = ti * TILE, min(ni, (ti + 1) * TILE) - 1
            far_i = a0 - i if i < a0 else i - a1 if i > a1 else 0
            for tj in range(max(0, j - reach) // TILE, min(nj - 1, j + reach) // TILE + 1):
                most = tiles[ti * tw + tj]
                b0, b1 = tj * TILE, min(nj, (tj + 1) * TILE) - 1
                far_j = b0 - j if j < b0 else j - b1 if j > b1 else 0
                if not most or 4 * (far_i * far_i + far_j * far_j) > (lv + most) ** 2:
                    continue  # no spot left in this square, or none with the room to reach
                w = (lv + most) // 2 + 1
                ia, ib, ja, jb = max(a0, i - w), min(a1, i + w), max(b0, j - w), min(b1, j + w)
                best = 0
                for ii in range(ia, ib + 1):
                    di = ii - i
                    k = ii * nj + ja
                    for jj in range(ja, jb + 1):
                        l2 = room[k]
                        if l2 and not due[k]:
                            dj = jj - j
                            if 4 * (di * di + dj * dj) <= (lv + l2) ** 2 and (di or dj) \
                                    and not l2 * STEP + r - ((step * -di) ** 2 + (step * -dj) ** 2) ** 0.5 < STEP:
                                got.append((k, l2))
                            elif l2 > best:
                                best = l2
                        k += 1
                if best < most and (ia, ib, ja, jb) == (a0, a1, b0, b1):  # all of it seen: its most room now
                    tiles[ti * tw + tj] = best
                    lowered = lowered or most == self.most
        if lowered:
            self.most = max(tiles)
        return got

    def _tile(self):
        """The most room of a spot in each square of TILE by TILE spots (never less than a spot with no turn coming
        has there): (the squares row by row, how many a row)."""
        room, nj, ni = self.room, self.nj, self.ni
        tw = (nj + TILE - 1) // TILE
        tiles = [0] * (((ni + TILE - 1) // TILE) * tw)
        for i in range(ni):
            row = room[i * nj:(i + 1) * nj]
            if row.count(0) == nj:
                continue
            t = (i // TILE) * tw
            for tj in range(tw):
                most = max(row[tj * TILE:(tj + 1) * TILE])
                if most > tiles[t + tj]:
                    tiles[t + tj] = most
        self._tiles = (tiles, tw)
        self.most = max(tiles)
        return self._tiles


GAP_SIDE = 10240.0  # _gaps' squares


def _gaps(circles, reach: float, side: float = GAP_SIDE) -> dict:
    """For _grow: how far every point of a square of `side` is, at least, from the nearest live circle's rim (under 0
    inside one), for the squares with a circle within `reach` of them: {(square): that}. A square that isn't there has
    no circle's rim within `reach` of any of its points. (For each circle and each square near it: from the square's
    middle to the circle's middle, less its radius, less the square's half diagonal; the least of those.) A new
    circle of radius r in a square that says r or more overlaps no old circle, so it meets none."""
    half = side * 0.7072  # (a hair over half the diagonal)
    out: dict = {}
    for x, y, r in circles:
        if r <= 0:
            continue
        far = r + reach + 2 * side  # (a square past this is farther than `reach` from the rim at every point)
        for a in range(int((x - far) // side), int((x + far) // side) + 1):
            qx = (a + 0.5) * side - x
            for b in range(int((y - far) // side), int((y + far) // side) + 1):
                g = math.hypot(qx, (b + 0.5) * side - y) - r - half
                if g < out.get((a, b), math.inf):
                    out[a, b] = g
    return out


def _grow(zones, old, least: float, box, where, meets, most: int) -> tuple[list, int, bool]:
    """New circles over the zones (x, y, r) where a graph has none, grown from the ground units can reach
    (Graph.open_ground): (the circles (x, y, r) in the order they were taken, how many more the ground no circle
    reached would have had, whether it stopped at `most` circles).

    A spot (_Spots) is a point of the 2 STEP grid inside `box` that `where(x, y)` allows (when given) and no live
    circle of `old` covers, with `least` or more of room in the zones; a spot taken becomes a circle of its room. The
    spots are gone through in passes, the most room first in each (then by x, then y): a spot inside a circle taken
    before it is dropped; one that meets an old circle (`meets(circle, the old one's number)` gives where, or None) or
    one taken before it (_meeting: an overlap of STEP or more) is taken; any other waits for the next pass; until a
    pass takes none. So every circle taken is reached from the ground, and a big one in the middle of a stroke that
    wouldn't reach it leaves room for smaller ones that do. The spots left are then covered the same way, with no
    test of reach, to count the circles left out.

    The passes aren't walked spot by spot (a whole map drained has thirteen million, and a pass may take one circle):
    a spot is taken on its first turn after a circle it meets was taken, unless a circle taken by then holds it, so
    only those turns are kept, in a queue by pass and by the spots' order. The spots that meet an old circle have
    theirs in the first pass; when a circle is taken, the spots inside it are dropped and those that meet it get
    their turn: later in the same pass when they come after it, in the next when before. The same circles, in the
    same order, as walking every pass.

    `most`: with this many circles taken the caller can't use them (the graph would be too big to write), so it stops
    there and says so."""
    spots = _Spots(zones, least, box)
    if not spots.ni:
        return [], 0, False
    if where is not None:
        spots.only(where)
    # a spot's circle lies inside its zone, so only the old circles that reach into a zone can hold a spot or meet
    # one: with a few zones on a big map, the few near them (with thousands of zones, as well all of them)
    reaching = [d for d, c in enumerate(old) if c[2] > 0]
    if len(zones) <= 5000:
        by_place = _Buckets(list(zones))
        reaching = [d for d in reaching if any(
            math.hypot(old[d][0] - zones[z][0], old[d][1] - zones[z][1]) < old[d][2] + zones[z][2] + 1.0
            for z in by_place.near(old[d][0], old[d][1], old[d][2] + 1.0))]
    spots.uncover([old[d] for d in reaching])
    if spots.empty():
        return [], 0, False  # no spot: the ground is open already
    room, due, step, nj, top = spots.room, spots.due, spots.step, spots.nj, spots.top
    i0, j0, i1, j1, n = spots.i0, spots.j0, spots.i0 + spots.ni - 1, spots.j0 + nj - 1, len(spots.due)
    span = top + 1  # a turn's number: (pass * span + top - room) * n + place, so turns sort by pass, room, place
    turns = []
    near = min(top, NEAR)
    for d in reaching:  # the spots that meet an old circle: a turn in the first pass
        bx, by, br = old[d]
        reach = br + near * STEP  # (no spot with that room meets it from this far: a STEP to spare)
        ia, ib = max(i0, int((bx - reach) // step)), min(i1, int((bx + reach) // step))
        ja, jb = max(j0, int((by - reach) // step)), min(j1, int((by + reach) // step) + 1)
        if ja > jb:
            continue
        for i in range(ia, ib + 1):
            x = i * step
            dx2 = (x - bx) ** 2
            if dx2 > reach * reach:
                continue
            h = math.sqrt(reach * reach - dx2)
            runs = [(max(ja, int((by - h) // step)), min(jb, int((by + h) // step) + 1))]
            if br * br - dx2 > 4 * step * step:  # the row goes through the circle: no spot is left inside it
                g = math.sqrt(br * br - dx2) - step
                runs = [(runs[0][0], min(jb, int((by - g) // step) + 1)), (max(ja, int((by + g) // step)), runs[0][1])]
            k = (i - i0) * nj - j0
            for a, b in runs:
                for j in range(a, b + 1):
                    lv = room[k + j]
                    if lv and lv <= near and not due[k + j]:
                        y = j * step
                        if dx2 + (y - by) ** 2 <= (lv * STEP + br - STEP + 1.0) ** 2 \
                                and meets((x, y, lv * STEP), d) is not None:
                            due[k + j] = 1
                            turns.append((span + top - lv) * n + k + j)
    heapify(turns)
    out = []

    def take(place, lv, turn):
        out.append(spots.at(place) + (lv * STEP,))
        spots.cover(place, lv)
        for k, l2 in spots.met(place, lv):
            due[k] = 1
            when = turn if l2 < lv or (l2 == lv and k > place) else turn + 1
            if when > 1 or l2 <= near:  # (a spot with more room than `near` has its first turn in the walk below)
                heappush(turns, (when * span + top - l2) * n + k)
    if top > near:
        # the spots with the most room come first in every pass: in the first, each looks for the old circles round
        # itself (a few spots when the ones before them are taken: a big circle holds all the spots near it). A spot
        # whose circle no old circle's rim comes within (_gaps: most of them, in the middle of a wide dried bed)
        # meets none, and doesn't look
        ground = _Buckets(list(old))
        gaps, side = _gaps(old, top * STEP), GAP_SIDE
        for lv in spots.rooms(near + 1):
            r = lv * STEP
            for place in spots.walk(lv):
                if not due[place]:
                    c = spots.at(place) + (r,)
                    if r <= gaps.get((int(c[0] // side), int(c[1] // side)), r):
                        continue
                    if not any(meets(c, d) is not None for d in ground.near(*c)):
                        continue
                take(place, lv, 1)
                if len(out) >= most:
                    return out, 0, True
    while turns:
        turn, place = divmod(heappop(turns), n)
        if room[place]:  # (not inside a circle taken since)
            take(place, room[place], turn // span)
            if len(out) >= most:
                return out, 0, True
    left = 0
    for lv in spots.rooms():  # what is left: no turn ever came (every spot that had one is taken, or dropped)
        for place in spots.walk(lv):
            left += 1
            spots.cover(place, lv)
    return out, left, False


def _without(zones, circles, side: float = 20480.0) -> list[int]:
    """The zones (x, y, r), by their numbers, with no circle's middle inside them. The middles are looked up by
    place (squares of `side`): each zone against those in the squares it reaches, and one more all round."""
    if not circles:
        return list(range(len(zones)))
    squares: dict = {}
    for x, y, _r in circles:
        squares.setdefault((int(x // side), int(y // side)), []).append((x, y))
    out = []
    for i, (zx, zy, zr) in enumerate(zones):
        if zr > 0:
            a0, a1 = int((zx - zr) // side) - 1, int((zx + zr) // side) + 1
            b0, b1 = int((zy - zr) // side) - 1, int((zy + zr) // side) + 1
            if (a1 - a0 + 1) * (b1 - b0 + 1) > len(squares):  # a zone that big: every square there is
                near = (p for points in squares.values() for p in points)
            else:
                near = (p for a in range(a0, a1 + 1) for b in range(b0, b1 + 1) for p in squares.get((a, b), ()))
            if any(math.hypot(x - zx, y - zy) < zr for x, y in near):
                continue
        out.append(i)
    return out


# --- local maps for new bridges (Graph.open) ----------------------------------------------------------------------------
def _reached(links, start: int) -> set[int]:
    """The circles reached from circle `start` through `links` ((a, b, x, y))."""
    near: dict[int, list[int]] = {}
    for a, b, _x, _y in links:
        near.setdefault(a, []).append(b)
        near.setdefault(b, []).append(a)
    seen, todo = {start}, [start]
    while todo:
        for d in near.get(todo.pop(), ()):
            if d not in seen:
                seen.add(d)
                todo.append(d)
    return seen


def _piece(circles, start: int = 0) -> set[int]:
    """The circles (x, y, r) reached from circle `start` through ones overlapping by STEP or more (links)."""
    near = _Buckets(list(circles))
    seen, todo = {start}, [start]
    while todo:
        c = todo.pop()
        for d in near.around(c):
            if d not in seen and _meeting(circles[c], circles[d]) is not None:
                seen.add(d)
                todo.append(d)
    return seen


def _try_owner(owner, deck, near, anchors, chains, first: int, extra=()) -> dict | None:
    """The local map an owner circle (x, y, r) would have over a deck (its circles `deck`): the deck; the approaches'
    circles (`chains`: each end's, from the deck out) whose middles are in the owner, and the circles `extra`, there
    only; and a copy of every main circle the owner overlaps (`near`: (number, circle) of the old ones that may; the
    approaches' circles past the owner, which go into the main graph numbered from `first`), but for those the deck's
    piece doesn't reach.
    {"circle": owner, "local": its circles, "linked": the main circles the owner links to (those it overlaps by STEP
    or more whose copies are kept), "left_out": copies left out, "main": the approaches' circles for the main graph},
    or None when it links to no ground at one end (`anchors`: the main circles each end's deck or approach meets, or
    the approach's own circles past the owner), or an approach comes back into it."""
    cx, cy, size = owner
    inner, tails, ends = list(extra), [], []
    for e, chain in enumerate(chains):
        inside = [math.hypot(c[0] - cx, c[1] - cy) < size for c in chain]
        k = inside.index(False) if False in inside else len(chain)
        if any(inside[k:]):
            return None
        inner += chain[:k]
        tail = [(first + len(tails) + j, c) for j, c in enumerate(chain[k:])]
        tails += tail
        ends.append(set(anchors[e]) | {i for i, _c in tail})
    over = [(i, c) for i, c in near + tails if math.hypot(c[0] - cx, c[1] - cy) < size + c[2]]
    piece = _piece(list(deck) + inner + [c for _i, c in over])
    kept = [(i, c) for k, (i, c) in enumerate(over, start=len(deck) + len(inner)) if k in piece]
    linked = [i for i, c in kept if _meeting(owner, c) is not None]
    if not all(end & set(linked) for end in ends):
        return None
    return {"circle": owner, "local": list(deck) + inner + [c for _i, c in kept], "linked": linked,
            "left_out": len(over) - len(kept), "main": [c for _i, c in tails]}


def _local_graph(box, circles) -> Graph:
    """A local map of `circles` (x, y, r), the largest first: every two that overlap by STEP or more linked where
    they meet (listed by their second circle, as the game's files), no crossings, an index of its own (_tree_build),
    the main graph's `box` and a header of zeros after the counts (as every shipped local map)."""
    circles = sorted(circles, key=lambda c: -c[2])
    near = _Buckets(list(circles))
    links = []
    for b in range(len(circles)):
        for a in sorted(d for d in near.around(b) if d < b):
            point = _meeting(circles[a], circles[b])
            if point is not None:
                links.append((a, b) + point)
    mine = [[] for _ in circles]
    for k, (a, b, _x, _y) in enumerate(links):
        mine[a].append(k)
        mine[b].append(k)
    recs, lists = [], []
    for c, (x, y, r) in enumerate(circles):
        recs.append((x, y, r, len(lists), 0))
        lists += mine[c]
    recs.append((0.0, 0.0, 0.0, len(lists), 0))
    return Graph(tuple(box), recs, links, lists, b"", _tree_write(_tree_build(circles)), [], bytes(HEADER - 20))


# --- the spatial index (a graph's `points`) ---------------------------------------------------------------------------
# One bounding-interval tree, its root at the start (checked on all 1,307 shipped graphs: walked from the root it
# reaches every circle exactly once, and written back with the rules below it gives the same bytes).
#   branch  u16 tag (bit 0 set; tag & ~1, shifted 16 left, is the jump's high part), u16 word (word & ~1, times 2, is
#           the jump's low part; bit 0 is set on every shipped branch), f32 the left half's far edge, f32 the right
#           half's near edge, on the branch's axis (x and y by turns down the tree). The left half starts right after
#           the branch; the right half starts `jump` bytes after the left half's start, the left half padded to a
#           multiple of 4 bytes to get there.
#   leaf    u16 byte length (even), then that many bytes of circle numbers (u16).
# A point is looked for down both halves where the two edges overlap. The whole section is padded to 4 bytes.
def _tree_read(points: bytes, q: int = 0):
    """The index as nested lists: ["leaf", [circle numbers]] or ["branch", word bit 0, 8 bytes of edges, left, right]."""
    tag = struct.unpack_from("<H", points, q)[0]
    if tag & 1:
        word = struct.unpack_from("<H", points, q + 2)[0]
        left = q + 12
        jump = ((tag & 0xFFFE) << 16) + 2 * (word & 0xFFFE)
        return ["branch", word & 1, points[q + 4:q + 12], _tree_read(points, left), _tree_read(points, left + jump)]
    return ["leaf", list(struct.unpack_from(f"<{tag // 2}H", points, q + 2))]


def _tree_write(node, top: bool = True, depth: int = 0) -> bytes:
    if node[0] == "leaf":
        out = struct.pack(f"<H{len(node[1])}H", 2 * len(node[1]), *node[1])
    else:
        if depth >= MAX_DEPTH:  # a guard: the game's walk of a deeper index runs off its fixed stack
            raise NavError(f"the graph's index would be more than {MAX_DEPTH} levels deep")
        _kind, bit, edges, left, right = node
        lb = _tree_write(left, False, depth + 1)
        lb += bytes(-len(lb) % 4)
        jump = len(lb)
        if jump >= 1 << 32:
            raise NavError("the graph's index is too big")
        out = struct.pack("<HH", 1 | ((jump >> 16) & 0xFFFE), ((jump & 0x1FFFF) // 2) | bit) + edges + lb \
            + _tree_write(right, False, depth + 1)
    return out + bytes(-len(out) % 4) if top else out


def _index_add(points: bytes, into: dict[int, list[int]], boxes: dict | None = None) -> bytes:
    """The spatial index with new circles added: {old circle: [new circle numbers]} puts each new number in the leaf
    that lists the old circle, and the tree is written again (the jumps and padding as the game's files have them).
    A new circle inside the old one needs nothing more: every edge on the way to that leaf already takes it in, so
    a point in it is looked for where the old one would be. A new circle that reaches outside (a bridge over water)
    gives its box in `boxes` ({old circle: (x0, y0, x1, y1)}): on the way to that leaf, a left half's far edge grows
    to the box's far side and a right half's near edge to its near side, on the branch's axis (x at even depths, y
    at odd ones: on all 1,307 shipped graphs each edge is exactly its half's reach). Numbers whose old circle is in
    no leaf go into the first leaf (they'd be found only through their links)."""
    tree = _tree_read(points)
    left = {old: list(new) for old, new in into.items()}
    wide = dict(boxes or {})
    first = []

    def visit(node, depth):
        if node[0] == "leaf":
            if not first:
                first.append(node)
            got = []
            for i in list(node[1]):
                node[1] += left.pop(i, [])
                if i in wide:
                    got.append(wide.pop(i))
            return got
        axis = depth % 2
        lb = visit(node[3], depth + 1)
        rb = visit(node[4], depth + 1)
        if lb or rb:
            far, near = struct.unpack("<2f", node[2])
            for b in lb:
                far = max(far, _f32(b[2 + axis], up=True))
            for b in rb:
                near = min(near, _f32(b[axis], up=False))
            node[2] = struct.pack("<2f", far, near)
        return lb + rb

    visit(tree, 0)
    rest = [n for new in left.values() for n in new]
    if rest:
        first[0][1] += rest
    return _tree_write(tree)


def _index_more(points: bytes, old, new, number=lambda i: i) -> bytes:
    """The index with the circles `new` ((number, (x, y, r))) added, each in the leaf of the live circle of `old`
    ((x, y, r) by their numbers when the index was made; `number` gives a leaf's number for one) nearest it, the
    branches on the way widened to reach it (_index_add)."""
    live = [i for i, c in enumerate(old) if c[2] > 0]
    where = _Buckets([old[i] for i in live])
    far = None  # for a new circle with no old one near it (out on a drained sea): the nearest of them all
    into: dict[int, list[int]] = {}
    boxes: dict[int, tuple] = {}
    for j, (x, y, r) in new:
        ids = list(where.near(x, y, r + 20480.0))
        if ids:
            bank = number(live[min(ids, key=lambda k: ((old[live[k]][0] - x) ** 2 + (old[live[k]][1] - y) ** 2) ** 0.5
                                    - old[live[k]][2])])
        elif live:
            far = far or _Nearest([old[i] for i in live])
            bank = number(live[far.find(x, y)])
        else:
            bank = -1
        into.setdefault(bank, []).append(j)
        bx0, by0, bx1, by1 = boxes.get(bank, (x, y, x, y))
        boxes[bank] = (min(bx0, x - r), min(by0, y - r), max(bx1, x + r), max(by1, y + r))
    return _index_add(points, into, boxes)


class _Nearest:
    """Which of some circles (x, y, r) a point is nearest to: the one whose rim is the least far from it (or that it
    lies deepest in), the first of them among equals; what going through them all gives. The circles are halved by
    turns along x and y into a tree, each part with the box of its middles and its largest radius: a part whose every
    rim is farther than the best found is passed over."""

    def __init__(self, circles):
        self.circles = circles
        self.top = self._part(list(range(len(circles))), 0)

    def _part(self, ids, depth: int):
        xs, ys = [self.circles[i][0] for i in ids], [self.circles[i][1] for i in ids]
        box = (min(xs), min(ys), max(xs), max(ys), max(self.circles[i][2] for i in ids))
        if len(ids) <= 8:
            return box + (ids, None)
        ids = sorted(ids, key=lambda i: self.circles[i][depth % 2])
        return box + (self._part(ids[:len(ids) // 2], depth + 1), self._part(ids[len(ids) // 2:], depth + 1))

    def find(self, x: float, y: float) -> int:
        circles = self.circles

        def least(part) -> float:  # no rim in this part is nearer than this
            x0, y0, x1, y1, most = part[:5]
            return math.hypot(x0 - x if x < x0 else x - x1 if x > x1 else 0.0,
                              y0 - y if y < y0 else y - y1 if y > y1 else 0.0) - most
        best, at = math.inf, -1
        todo = [(least(self.top), self.top)]
        while todo:
            bound, (_x0, _y0, _x1, _y1, _most, a, b) = todo.pop()
            if bound - 1.0 > best:  # (a unit to spare: the sums below are rounded)
                continue
            if b is None:
                for k in a:
                    gap = ((circles[k][0] - x) ** 2 + (circles[k][1] - y) ** 2) ** 0.5 - circles[k][2]
                    if gap < best or (gap == best and k < at):
                        best, at = gap, k
            else:
                todo += sorted(((least(a), a), (least(b), b)), key=lambda part: -part[0])  # the nearer half first
        return at


def _index_renumber(points: bytes, number) -> bytes:
    """The index with every circle in its leaves numbered again (`number(old)` gives the new number)."""
    tree = _tree_read(points)
    todo = [tree]
    while todo:
        node = todo.pop()
        if node[0] == "leaf":
            node[1] = [number(i) for i in node[1]]
        else:
            todo += [node[3], node[4]]
    return _tree_write(tree)


def _tree_build(circles, ids=None, depth: int = 0):
    """An index of `circles` (x, y, r), as the game's are made: split at the median of the circles' middles, on x
    and y by turns from x, each edge exactly its half's reach (on all 1,307 shipped graphs; rounded outward to f32),
    leaves of at most LEAF circles. DomesticNukes' Open Map builds whole indexes this way and the game takes them."""
    if ids is None:
        ids = [i for i, c in enumerate(circles) if c[2] > 0]
    if len(ids) <= LEAF:
        return ["leaf", list(ids)]
    axis = depth % 2
    ids = sorted(ids, key=lambda i: (circles[i][axis], i))
    left, right = ids[:len(ids) // 2], ids[len(ids) // 2:]
    far = _f32(max(circles[i][axis] + circles[i][2] for i in left), up=True)
    near = _f32(min(circles[i][axis] - circles[i][2] for i in right), up=False)
    return ["branch", 1, struct.pack("<2f", far, near), _tree_build(circles, left, depth + 1),
            _tree_build(circles, right, depth + 1)]


def _f32(v: float, up: bool) -> float:
    """`v` as the nearest f32 on its side: no smaller when `up`, no larger otherwise (an index edge then never
    stops short of a circle's reach)."""
    f = struct.unpack("<f", struct.pack("<f", v))[0]
    if f == v or (f > v) == up:
        return f
    bits = struct.unpack("<I", struct.pack("<f", f))[0]
    if f == 0:
        bits = 1 if up else 0x80000001
    else:
        bits += 1 if (f > 0) == up else -1
    return struct.unpack("<f", struct.pack("<I", bits))[0]


# --- placed buildings units can't go through ---------------------------------------------------------------------
FOOTPRINT = 800.0  # a building's reach from its middle when its model can't be found (map units, times its size)


def solid_blocks(game, objects) -> tuple[list[Block], list[str]]:
    """Blocks for the buildings a mod places (rusemod.scenery.NewObject, unless `solid` is false): one per
    building, as far as its model reaches from its middle (across the ground), times its size. Units then go around
    them. Returns (blocks, notes)."""
    from pathlib import Path
    from .build import find_pack
    from .edat import Edat
    from .scenery import descriptors, model_reach
    wanted = [o for o in objects if o.solid]
    if not wanted:
        return [], []
    unit_path = find_pack(Path(game), "ZZ_GladPatchableWin.dat")
    if unit_path is None:
        return [], ["ZZ_GladPatchableWin.dat isn't in the game: placed buildings stay walk-through"]
    with Edat.open(str(unit_path)) as arc:
        descs = descriptors(arc)
    reach: dict[str, float] = {}
    lib = None
    out = []
    for o in wanted:
        d = descs.get(o.type)
        if d is None or d.group != "building" or d.bridge:  # a bridge opens ground instead (rusemod.bridges)
            continue
        if o.type not in reach:
            if lib is None:
                from .models import Library
                lib = Library(Path(game))
            reach[o.type] = model_reach(lib, d) or FOOTPRINT
        out.append(Block(o.x, o.y, reach[o.type] * o.size, "all"))
    if lib is not None:
        lib.close()
    return out, [f"{len(out)} placed building(s) made solid"] if out else []
