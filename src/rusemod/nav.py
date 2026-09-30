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
    def block(self, zones: list[tuple[float, float, float]]) -> dict:
        """Take the ground inside `zones` (circles: x, y, radius) away, here and in the local graphs: units plan
        around it. A circle whose middle is in a zone, or that would be smaller than MIN_RADIUS once it keeps clear
        of every zone, is emptied (radius 0, no links); one that reaches into a zone shrinks to keep clear (its
        radius a multiple of STEP). A link goes when one of its circles is emptied or its meeting point is no longer
        inside both circles, or lies in a zone; the crossings that use it go too, and the links left are numbered
        again. Circle numbers stay, so the index (points) needs no change. Returns what changed."""
        counts = {"emptied": 0, "shrunk": 0, "links": 0, "crossings": 0}
        if zones:
            n = len(self.circles) - 1
            radius = []
            for x, y, r, _l, _c in self.circles[:-1]:
                clear = min(((x - zx) ** 2 + (y - zy) ** 2) ** 0.5 - zr for zx, zy, zr in zones)
                if clear >= r:
                    radius.append(r)
                    continue
                new = (clear // STEP) * STEP if clear > 0 else 0.0
                if new < MIN_RADIUS:
                    new = 0.0
                counts["emptied" if new == 0 else "shrunk"] += 1
                radius.append(new)

            def inside(c, px, py):
                cx, cy = self.circles[c][:2]
                return radius[c] > 0 and (px - cx) ** 2 + (py - cy) ** 2 <= radius[c] ** 2 + 1.0

            keep = [inside(a, x, y) and inside(b, x, y)
                    and all((x - zx) ** 2 + (y - zy) ** 2 > zr * zr for zx, zy, zr in zones)
                    for a, b, x, y in self.links]
            number, links = {}, []
            for i, (lk, k) in enumerate(zip(self.links, keep)):
                if k:
                    number[i] = len(links)
                    links.append(lk)
            counts["links"] = len(self.links) - len(links)
            cross = [self.crossings[28 * i:28 * i + 28] for i in range(len(self.crossings) // 28)]
            circles, lists, kept = [], [], []
            for c in range(n):
                x, y, _r, l0, c0 = self.circles[c]
                l1, c1 = self.circles[c + 1][3], self.circles[c + 1][4]
                start, cstart = len(lists), len(kept)
                lists += [number[k] for k in self.lists[l0:l1] if k in number]
                for rec in cross[c0:c1]:
                    la, lb = struct.unpack_from("<2H", rec, 20)
                    if la in number and lb in number:
                        kept.append(rec[:20] + struct.pack("<2H", number[la], number[lb]) + rec[24:])
                circles.append((x, y, radius[c], start, cstart))
            circles.append((0.0, 0.0, 0.0, len(lists), len(kept)))
            counts["crossings"] = len(cross) - len(kept)
            self.circles, self.links, self.lists, self.crossings = circles, links, lists, b"".join(kept)
        for s in self.subs:
            for k, v in s.block(zones).items():
                counts[k] += v
        return counts

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
                     f"{c['links']} link(s) and {c['crossings']} crossing(s) taken out")
    return {name: replace_buffers(win, new)}, notes
