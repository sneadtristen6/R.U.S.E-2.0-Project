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
                 (points on road links r0 and r1), f32 its length along the road, u16 the two links (gates) it goes
                 between, u16 r0, r1: road network links (buffer 0; 7,862 of 7,862 checked on 4 maps, 2026-09-30),
                 so a road link renumbered must be renumbered here too (Graph.renumber_roads)
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
from dataclasses import dataclass, field

HEADER = 84
STEP = 320.0         # circle centres and radii are on this grid
MIN_RADIUS = 1280.0  # the smallest circle on any shipped map
METRE = 260.0        # map units in a metre
APPROACH = 16000.0   # how far past a new deck's end its approach may run along the road to reach ground units already
                     # use (about 62 m; the shipped bridges' chains of circles reach up to 10,800 past their decks)
LOCAL_RADIUS = 640.0   # a new deck's circles in its local map: units keep within this of the deck's line, inside the
                       # floor they stand on (663 either side on the bridge kinds the build places; the shipped decks'
                       # local circles are mostly 640)
LOCAL_SPACING = 640.0  # between them along the deck (a link needs an overlap of STEP: at most 960 apart for 640)
LEAF = 4               # the most circles in a leaf of an index built here (the shipped ones hold 1 to 7)


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
        body = [b"".join(struct.pack("<3f2H", *c) for c in self.circles),
                b"".join(struct.pack("<2H2f", *lk) for lk in self.links),
                struct.pack(f"<{len(self.lists)}H", *self.lists),
                self.crossings, self.points] + [s.to_bytes() for s in self.subs]
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
        for i, (x, y, r) in enumerate(old):
            clear = min(((x - zx) ** 2 + (y - zy) ** 2) ** 0.5 - zr for zx, zy, zr in zones)
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
            return any((px - zx) ** 2 + (py - zy) ** 2 <= zr * zr for zx, zy, zr in zones)

        now = [(x, y, radius[i]) for i, (x, y, _r) in enumerate(old)]
        filled = _fill([old[i] for i in changed], zones, now) if refill else []
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
            raise NavError("opening the bridges would leave ground units can't reach, which crashes the game")
        circles = self.circles[:-1]
        for k in range(nx, nx + m):
            ox, oy, orad = circles[k][:3]
            if len(self.subs[k].parts()) != 1:
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
    """Ground units can't use: a circle (map units) taken out of the infantry graph, the vehicles' or both."""
    x: float
    y: float
    radius: float
    units: str = "all"


def parse_blocks(items, where: str = "movement.toml") -> list[Block]:
    out = []
    for n, b in enumerate(items or [], start=1):
        at = f"{where}: block {n}"
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
        out.append(Block(float(b["x"]), float(b["y"]), float(b["radius"]), units))
    return out


def blocks_toml(blocks: list[Block], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for b in blocks:
        lines += ["[[block]]", f"x = {b.x!r}", f"y = {b.y!r}", f"radius = {b.radius!r}", f'units = "{b.units}"', ""]
    return "\n".join(lines)


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


def apply_blocks(read, pack: str, blocks: list[Block]) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map; `read(member)` gives a DataMap_Win.dat file's bytes or None."""
    from ruse_mod_engine import sdb
    from .cover import PACK, member
    name = member(pack)
    win = read(name)
    if win is None:
        raise NavError(f"{pack} has no {name} in {PACK}, so its movement can't be changed")
    bufs = sdb.split_mapinfo(win)[1]
    new, notes = {}, []
    for k, what in ((1, "infantry"), (2, "vehicles")):
        zones = [(b.x, b.y, b.radius) for b in blocks if k in UNITS[b.units]]
        if not zones:
            continue
        g = Graph.read(bufs[k])
        c = g.block(zones)
        notes.append(f"{what}: {len(zones)} block(s); {c['emptied']} circle(s) emptied, {c['shrunk']} shrunk, "
                     f"{c['links']} link(s) and {c['crossings']} crossing(s) taken out; {c['added']} circle(s) and "
                     f"{c['linked']} link(s) added to fill the ground back")
        cut = _drop_cut_off(g)
        if cut:
            notes.append(f"{what}: {cut} circle(s) the blocks cut off from the rest taken out too (no unit could "
                         f"reach them, and an order onto them crashes the game)")
        new[k] = g.to_bytes()
    return {name: replace_buffers(win, new)}, notes


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


def _fill(sources, zones, now) -> list[tuple[float, float, float]]:
    """New circles over the ground `sources` (the old circles that were emptied or shrunk) covered and no circle
    in `now` covers any more, outside the zones: each inside one source circle and clear of every zone, centres on
    the STEP grid, the largest first, each on ground no circle covers yet, down to MIN_RADIUS."""
    live = [c for c in now if c[2] > 0]
    near = _Buckets(live)

    def covered(x, y, extra):
        key = (int(x // near.size), int(y // near.size))
        return any((x - live[i][0]) ** 2 + (y - live[i][1]) ** 2 < live[i][2] ** 2 for i in near.cells.get(key, ())) \
            or any((x - c[0]) ** 2 + (y - c[1]) ** 2 < c[2] * c[2] for c in extra)

    step = 2 * STEP
    spots = []
    for sx, sy, sr in sources:
        for i in range(int((sx - sr) // step), int((sx + sr) // step) + 1):
            for j in range(int((sy - sr) // step), int((sy + sr) // step) + 1):
                x, y = i * step, j * step
                deep, source = max(((cr - ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5, k) for k, (cx, cy, cr) in enumerate(sources)),
                                   default=(0.0, 0))
                room = min([deep] + [((x - zx) ** 2 + (y - zy) ** 2) ** 0.5 - zr for zx, zy, zr in zones])
                room = (room // STEP) * STEP
                if room >= MIN_RADIUS and not covered(x, y, ()):
                    spots.append((room, x, y, source))
    spots.sort(key=lambda s: (-s[0], s[1], s[2]))
    out = []  # (x, y, r, the source circle it lies deepest in)
    for r, x, y, source in spots:
        if not covered(x, y, out):
            out.append((float(x), float(y), float(r), source))
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


def _tree_write(node, top: bool = True) -> bytes:
    if node[0] == "leaf":
        out = struct.pack(f"<H{len(node[1])}H", 2 * len(node[1]), *node[1])
    else:
        _kind, bit, edges, left, right = node
        lb = _tree_write(left, False)
        lb += bytes(-len(lb) % 4)
        jump = len(lb)
        if jump >= 1 << 32:
            raise NavError("the graph's index is too big")
        out = struct.pack("<HH", 1 | ((jump >> 16) & 0xFFFE), ((jump & 0x1FFFF) // 2) | bit) + edges + lb \
            + _tree_write(right, False)
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
    into: dict[int, list[int]] = {}
    boxes: dict[int, tuple] = {}
    for j, (x, y, r) in new:
        ids = list(where.near(x, y, r + 20480.0)) or range(len(live))
        bank = number(live[min(ids, key=lambda k: ((old[live[k]][0] - x) ** 2 + (old[live[k]][1] - y) ** 2) ** 0.5
                                - old[live[k]][2])]) if live else -1
        into.setdefault(bank, []).append(j)
        bx0, by0, bx1, by1 = boxes.get(bank, (x, y, x, y))
        boxes[bank] = (min(bx0, x - r), min(by0, y - r), max(bx1, x + r), max(by1, y + r))
    return _index_add(points, into, boxes)


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
    from .scenery import descriptors
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
            far = 0.0
            for model in (d.models or ([d.model] if d.model else [])):
                name = lib.find(model)
                if name is None:
                    continue
                for part, _tex in lib.parts(name):
                    pos = part.positions
                    for k in range(0, len(pos) - 2, 3):
                        far = max(far, (pos[k] * pos[k] + pos[k + 1] * pos[k + 1]) ** 0.5)
            reach[o.type] = far or FOOTPRINT
        out.append(Block(o.x, o.y, reach[o.type] * o.size, "all"))
    if lib is not None:
        lib.close()
    return out, [f"{len(out)} placed building(s) made solid"] if out else []
