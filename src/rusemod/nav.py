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
    crossings    crossings × 28 bytes: a trip through a circle, from one link's meeting point to another's: two
                 points (f32 x, y each), its length, the two link numbers, a word; route costs
    points       a spatial index of the circles, up to the first sub-graph: branch records (u16 1, u16 how far
                 to skip, f32 x, y: a split point) and leaf records (u16 count, then that many circle numbers);
                 not written by us yet
    sub-graphs   the same layout again, without sub-graphs of their own (22 on Blitz)

`Graph.read(data).to_bytes() == data` on every shipped map (tools/verify_nav.py)."""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

HEADER = 84
STEP = 320.0         # circle centres and radii are on this grid
MIN_RADIUS = 1280.0  # the smallest circle on any shipped map


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
    def block(self, zones: list[tuple[float, float, float]], refill: bool = True) -> dict:
        """Take the ground inside `zones` (circles: x, y, radius) away, here and in the local graphs: units plan
        around it (proven in the game, 2026-09-30).

        A circle whose middle is in a zone, or that would be smaller than MIN_RADIUS once it keeps clear of every
        zone, is emptied (radius 0, no links); one that reaches into a zone shrinks to keep clear (its radius a
        multiple of STEP). A link goes when one of its circles is emptied or its meeting point is no longer inside
        both circles, or lies in a zone; the crossings that use it go too. With `refill`, the ground those circles
        gave up outside the zones gets new circles (the largest first, centres on the STEP grid), linked to every
        circle they overlap by STEP or more, and to each other; the shrunk circles are linked again where they still
        overlap. New circles are numbered after the old ones and listed in the index as one more tree (a leaf), so
        the old numbers and the old trees stay. Returns what changed."""
        counts = {"emptied": 0, "shrunk": 0, "links": 0, "crossings": 0, "added": 0, "linked": 0}
        if zones:
            self._block(zones, refill, counts)
        for s in self.subs:
            for k, v in s.block(zones, refill).items():
                counts[k] += v
        return counts

    def _block(self, zones, refill, counts) -> None:
        n = len(self.circles) - 1
        old = [c[:3] for c in self.circles[:-1]]
        radius = []
        for x, y, r in old:
            clear = min(((x - zx) ** 2 + (y - zy) ** 2) ** 0.5 - zr for zx, zy, zr in zones)
            if clear >= r:
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

        kept = [(i, lk) for i, lk in enumerate(self.links) if holds(lk[0], lk[2], lk[3]) and holds(lk[1], lk[2], lk[3])
                and not in_zone(lk[2], lk[3])]
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
        circles, lists, kept = [], [], []
        for c in range(len(allc)):
            start, cstart = len(lists), len(kept)
            lists += mine[c]
            if c < n:
                c0, c1 = self.circles[c][4], self.circles[c + 1][4]
                for rec in cross[c0:c1]:
                    la, lb = struct.unpack_from("<2H", rec, 20)
                    if la in number and lb in number:
                        kept.append(rec[:20] + struct.pack("<2H", number[la], number[lb]) + rec[24:])
            circles.append((allc[c][0], allc[c][1], allc[c][2], start, cstart))
        circles.append((0.0, 0.0, 0.0, len(lists), len(kept)))
        counts["crossings"] += len(cross) - len(kept)
        if len(circles) > 65535 or len(links) > 65535 or len(lists) > 65535:
            raise NavError("the graph would be too big for its 16-bit numbers")
        self.circles, self.links, self.lists, self.crossings = circles, links, lists, b"".join(kept)
        if added:  # the index: each new circle joins the leaf of the old circle it lies in (see _index_add)
            into: dict[int, list[int]] = {}
            for j, (_x, _y, _r, source) in enumerate(filled):
                into.setdefault(changed[source], []).append(n + j)
            self.points = _index_add(self.points, into)

    # --- reading it ---
    def links_of(self, circle: int) -> list[int]:
        """The link numbers of one circle."""
        return self.lists[self.circles[circle][3]:self.circles[circle + 1][3]]

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
        new[k] = g.to_bytes()
        notes.append(f"{what}: {len(zones)} block(s); {c['emptied']} circle(s) emptied, {c['shrunk']} shrunk, "
                     f"{c['links']} link(s) and {c['crossings']} crossing(s) taken out; {c['added']} circle(s) and "
                     f"{c['linked']} link(s) added to fill the ground back")
    return {name: replace_buffers(win, new)}, notes


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

    def around(self, c):
        x, y, r = self.circles[c]
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


def _index_add(points: bytes, into: dict[int, list[int]]) -> bytes:
    """The spatial index (a graph's `points`) with new circles added: {old circle: [new circle numbers]} puts each
    new number in the leaf that lists the old circle. The index is a row of two-way trees: a branch is (u16 1, u16,
    f32, f32) with its left tree right after it and its right tree after that (on the split axis, the first float
    is the left tree's far edge, the second usually the right tree's near edge); a leaf is (u16 byte length, u16
    circle numbers...). A new circle lies inside the old one, so the walk that reaches the old circle's leaf for a
    point in it reaches the new circle too. Branches are left as they are. Numbers whose old circle is in no leaf
    go in one more leaf at the end."""
    out = bytearray()
    left = {old: list(new) for old, new in into.items()}

    def parse(q: int) -> int:
        tag = struct.unpack_from("<H", points, q)[0]
        if tag == 1:
            out.extend(points[q:q + 12])
            return parse(parse(q + 12))
        ids = list(struct.unpack_from(f"<{tag // 2}H", points, q + 2))
        for i in list(ids):
            ids += left.pop(i, [])
        out.extend(struct.pack(f"<H{len(ids)}H", 2 * len(ids), *ids))
        return q + 2 + tag

    pos = 0
    while pos < len(points):
        pos = parse(pos)
    rest = [n for new in left.values() for n in new]
    if rest:
        out.extend(struct.pack(f"<H{len(rest)}H", 2 * len(rest), *rest))
    return bytes(out)


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
        if d is None or d.group != "building":
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
