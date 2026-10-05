"""Where units hide, and the ground the AI treats as blocked: a map's cover grid, painted by a mod (LittleGroove's
engine, ruse_mod_engine.sdb, reads and writes the grid).

A mod paints circles (or squares) in maps/<map>/cover.toml (MOD_FORMAT §8), in order, each setting or clearing one
layer:

    [[paint]]
    x = 500000.0      # map units, like a scenario's positions
    y = 640000.0
    radius = 20000.0
    layer = "cover"   # or "blocked" (for the AI only: units still walk there without a movement.toml block)
    erase = false     # true clears it (a wood's cover taken away)
    square = false    # true: a square along the map's axes, `radius` (map units) from its middle to each side (the
                      # owner asked for a square brush, 2026-09-30; its edges follow the grid's rows and columns)

A cell is painted when its centre is in the circle (or square), and only those cells change: painting nothing gives
the same file back. The designers drew cover as zones, not from the trees, so a town or a wood made in a mod gives
cover only once cover is painted over it. "Blocked" is for the AI only: units move by the map's movement
(rusemod.nav), so ground units must keep off needs a movement.toml block too (unpaired_blocked). On a map that isn't
square the grid reaches past its short side, the map in its middle (taken as the map's own size, a paint landed up to
a kilometre off: a wood cleared on D-Day kept hiding infantry in the game, 2026-10-01)."""
from __future__ import annotations

import struct
from dataclasses import dataclass

from ruse_mod_engine import sdb

PACK = "DataMap_Win.dat"
LAYERS = {"cover": sdb.FOREST_BIT, "blocked": sdb.BLOCKED_BIT}
_NODE = 16


class CoverError(ValueError):
    pass


@dataclass
class Paint:
    x: float
    y: float
    radius: float
    layer: str = "cover"
    erase: bool = False
    square: bool = False   # a square along the map's axes (the older way)
    shape: str = "round"   # round, square (sides along dx, dy) or line (to x2, y2): rusemod.brush Footprint
    dx: float = 1.0
    dy: float = 0.0
    x2: float = 0.0
    y2: float = 0.0

    def footprint(self):
        from .brush import Footprint
        if self.shape == "line":
            return Footprint("line", self.x, self.y, self.radius, x2=self.x2, y2=self.y2)
        if self.square or self.shape == "square":
            return Footprint("square", self.x, self.y, self.radius, self.dx, self.dy)
        return Footprint("round", self.x, self.y, self.radius)

    @property
    def squared(self) -> bool:
        return self.square or self.shape == "square"

    @property
    def plain(self) -> bool:
        """A circle, or a square whose sides run along the map's axes: painted by the first rule, as before shapes
        came (so those keep their exact bytes); a turned square or a line by the footprint's."""
        if self.shape == "line":
            return False
        return not self.squared or self.dx == 0.0 or self.dy == 0.0


def member(pack: str) -> str:
    """The map's grid inside DataMap_Win.dat: datasmap\\<map in lower case>\\mapinfo.win."""
    return "\\".join(("datasmap", pack.lower(), "mapinfo.win"))


def parse_paints(items, where: str = "cover.toml") -> list[Paint]:
    out = []
    for n, p in enumerate(items or [], start=1):
        at = f"{where}: paint {n}"
        if not isinstance(p, dict):
            raise CoverError(f"{at} isn't a table")
        extra = sorted(set(p) - {"x", "y", "radius", "layer", "erase", "square", "shape", "dx", "dy", "x2", "y2"})
        if extra:
            raise CoverError(f"{at}: unknown key {extra[0]!r}")
        shape = p.get("shape", "round")
        if shape not in ("round", "square", "line"):
            raise CoverError(f"{at}: shape must be round, square or line")
        for k in ("dx", "dy", "x2", "y2"):
            if k in p and (isinstance(p[k], bool) or not isinstance(p[k], (int, float))):
                raise CoverError(f"{at}: {k} must be a number")
        if shape == "line" and ("x2" not in p or "y2" not in p):
            raise CoverError(f"{at}: a line needs x2 and y2 (where it ends)")
        for k in ("x", "y", "radius"):
            if k not in p:
                raise CoverError(f"{at}: {k} is missing")
            if isinstance(p[k], bool) or not isinstance(p[k], (int, float)):
                raise CoverError(f"{at}: {k} must be a number")
        if p["radius"] <= 0:
            raise CoverError(f"{at}: radius must be more than 0")
        layer = p.get("layer", "cover")
        if layer not in LAYERS:
            raise CoverError(f"{at}: layer must be one of {', '.join(LAYERS)}")
        erase = p.get("erase", False)
        if not isinstance(erase, bool):
            raise CoverError(f"{at}: erase must be true or false")
        square = p.get("square", False)
        if not isinstance(square, bool):
            raise CoverError(f"{at}: square must be true or false")
        out.append(Paint(float(p["x"]), float(p["y"]), float(p["radius"]), layer, erase, square, shape,
                         float(p.get("dx", 1.0)), float(p.get("dy", 0.0)), float(p.get("x2", 0.0)),
                         float(p.get("y2", 0.0))))
    return out


def paints_toml(paints: list[Paint], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for p in paints:
        lines += ["[[paint]]", f"x = {p.x!r}", f"y = {p.y!r}", f"radius = {p.radius!r}", f'layer = "{p.layer}"']
        if p.erase:
            lines.append("erase = true")
        if p.square:
            lines.append("square = true")
        if p.shape != "round":
            lines.append(f'shape = "{p.shape}"')
        if p.squared and (p.dx, p.dy) != (1.0, 0.0):
            lines += [f"dx = {p.dx!r}", f"dy = {p.dy!r}"]
        if p.shape == "line":
            lines += [f"x2 = {p.x2!r}", f"y2 = {p.y2!r}"]
        lines.append("")
    return "\n".join(lines)


def _tree(win: bytes):
    parts = sdb.split_mapinfo(win)
    if not parts:
        raise CoverError("not a mapinfo.win")
    tree = sdb.parse(parts[1][3])
    x0, y0, x1, y1 = struct.unpack_from("<4f", tree["prefix"], 0)  # the grid's two corners
    if not (x1 > x0 and y1 > y0):
        raise CoverError(f"the cover grid's corners are ({x0:g}, {y0:g}) and ({x1:g}, {y1:g}): not a box")
    return tree, (x0, y0, x1 - x0, y1 - y0)


def grid(win: bytes) -> dict:
    """The map's grid, for showing it: {"size": R, "box": (x0, y0, width, height) in map units, "cells": R*R
    bytes}, row by row from the box's corner (a row is one y, going down the map: y grows south). The box can reach
    past the map (a map that isn't square: see above)."""
    tree, box = _tree(win)
    r = sdb.tree_grid_R(tree)
    return {"size": r, "box": box, "cells": _cells(tree, r)}


def _cells(tree, r: int) -> bytes:
    """The tree's cells, R*R bytes (sdb.to_grid's layout), filled a row slice at a time: a second or two on the
    biggest maps, where filling cell by cell takes half a minute."""
    nodes, ns = tree["nodes"], tree["node_start"]
    out = bytearray(r * r)
    stack = [(ns, 0, 0, r)]
    visits = len(nodes) * 4 + 16  # a malformed tree that loops stops here
    while stack and visits:
        visits -= 1
        off, x0, y0, size = stack.pop()
        idx = (off - ns) // _NODE
        if size < 2 or not 0 <= idx < len(nodes):
            continue
        h = size >> 1
        for q, (qx, qy) in enumerate(((x0, y0), (x0 + h, y0), (x0, y0 + h), (x0 + h, y0 + h))):
            v = nodes[idx][q]
            if not v & 1:
                stack.append((v, qx, qy, h))
                continue
            hh = max(h >> 1, 1)
            for s, (sx, sy) in enumerate(((qx, qy), (qx + hh, qy), (qx, qy + hh), (qx + hh, qy + hh))):
                run = bytes([(v >> (8 * s)) & 0xFF]) * min(hh, r - sx)
                for yy in range(sy, min(sy + hh, r)):
                    out[yy * r + sx:yy * r + sx + len(run)] = run
    return bytes(out)


def in_forest(win: bytes):
    """A test (x, y) -> True where the map's grid says "in forest" (its woods, as Eugen's designers drew them)."""
    g = grid(win)
    r, cells = g["size"], g["cells"]
    x0, y0, w, h = g["box"]
    bit = LAYERS["cover"]

    def test(x: float, y: float) -> bool:
        cx, cy = int((x - x0) / w * r), int((y - y0) / h * r)
        return 0 <= cx < r and 0 <= cy < r and bool(cells[cy * r + cx] & bit)
    return test


def cover_bits(win: bytes, most: int = 1024) -> dict:
    """Where units hide, small enough to send to the map view: {"size": n (at most `most`; bigger grids are
    sampled), "box": (x0, y0, width, height), "bits": n*n bits, cell i at byte i // 8, bit i % 8, 1 = cover}."""
    g = grid(win)
    r, cells = g["size"], g["cells"]
    step = max(1, r // most)
    n = r // step
    bits = bytearray((n * n + 7) // 8)
    i = 0
    for row in range(0, n * step, step):
        line = cells[row * r:(row + 1) * r:step]
        for b in line[:n]:
            if b & LAYERS["cover"]:
                bits[i >> 3] |= 1 << (i & 7)
            i += 1
    return {"size": n, "box": g["box"], "bits": bytes(bits)}


def paint(win: bytes, paints: list[Paint]) -> bytes:
    """mapinfo.win with `paints` applied in order (checksums made again). No paints: the same bytes."""
    if not paints:
        return win
    tree, (x0, y0, width, height) = _tree(win)
    r = sdb.tree_grid_R(tree)
    cw, ch = width / r, height / r
    nodes, ns = tree["nodes"], tree["node_start"]
    for p in paints:
        bit = LAYERS[p.layer]
        # which cells: their centres in the circle (or square), in cell units
        cx, cy, rx, ry = (p.x - x0) / cw - 0.5, (p.y - y0) / ch - 0.5, p.radius / cw, p.radius / ch
        fp = None if p.plain else p.footprint()

        def inside(x, y, square=p.squared):  # a cell's centre, as an ellipse in cells (square cells make it a
            if fp is not None:               # circle), or the box along the axes, or the footprint (a turned square,
                return fp.t2(x0 + (x + 0.5) * cw, y0 + (y + 0.5) * ch) <= 1.0   # a line): all convex, as state needs
            if square:
                return abs(x - cx) <= rx and abs(y - cy) <= ry
            return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0

        def state(x, y, s):
            """0: no cell of the square [x, x+s)² is painted; 1: all of them; 2: some."""
            far = all(inside(a, b) for a in (x, x + s - 1) for b in (y, y + s - 1))  # the shapes are convex
            if fp is not None:
                if far:
                    return 1
                return 2 if fp.meets(x0 + (x + 0.5) * cw, y0 + (y + 0.5) * ch, x0 + (x + s - 0.5) * cw,
                                     y0 + (y + s - 0.5) * ch) else 0
            nx, ny = min(max(cx, x), x + s - 1), min(max(cy, y), y + s - 1)  # the nearest cell centre
            if not inside(nx, ny):
                return 0
            return 1 if far else 2

        def change(b):
            return (b & ~bit if p.erase else b | bit) & 0xFF

        def leaf(bs):
            return (bs[0] | bs[1] << 8 | bs[2] << 16 | bs[3] << 24) | 1  # bit 0: the leaf mark

        def rec(off, x, y, size):
            node = nodes[(off - ns) // _NODE]
            h = size >> 1
            for q, (qx, qy) in enumerate(((x, y), (x + h, y), (x, y + h), (x + h, y + h))):
                st = state(qx, qy, h)
                if st == 0:
                    continue
                v = node[q]
                if not v & 1:
                    rec(v, qx, qy, h)
                    continue
                hh = h >> 1
                bs = [(v >> (8 * s)) & 0xFF for s in range(4)]
                if hh < 1:  # a leaf of one cell per byte, at the finest level
                    node[q] = leaf([change(b) for b in bs])
                    continue
                subs = ((qx, qy), (qx + hh, qy), (qx, qy + hh), (qx + hh, qy + hh))
                states = [state(sx, sy, hh) for sx, sy in subs]
                if 2 in states:  # the circle's edge crosses a byte's square: the leaf becomes a node of four
                    nodes.append([leaf([b] * 4) for b in bs])
                    node[q] = ns + (len(nodes) - 1) * _NODE
                    rec(node[q], qx, qy, h)
                else:
                    node[q] = leaf([change(b) if s == 1 else b for b, s in zip(bs, states)])

        if fp is not None:
            bx0, bx1, by0, by1 = fp.box()
            if bx1 >= x0 and bx0 < x0 + width and by1 >= y0 and by0 < y0 + height:
                rec(ns, 0, 0, r)
        elif 0 <= cx + rx and cx - rx < r and 0 <= cy + ry and cy - ry < r:  # a circle off the map changes nothing
            rec(ns, 0, 0, r)
    return sdb.replace_buffer4(win, sdb.serialize(tree))


def unpaired_blocked(paints: list[Paint], blocks) -> list[Paint]:
    """The paints that set the blocked layer where no block (nav.Block: x, y, radius) holds their middle. The blocked
    layer is what the AI asks about ground (where it looks and places things), not where units go: units move by the
    movement graphs alone, and walk on shipped "blocked" cells too (3% of them on SuperCrossroads4, half on Ardennes).
    A modder painting it as no-go ground needs a movement.toml block there as well."""
    return [p for p in paints if p.layer == "blocked" and not p.erase
            and not any((p.x - b.x) ** 2 + (p.y - b.y) ** 2 <= b.radius ** 2 for b in blocks)]


def apply_paints(read, pack: str, paints: list[Paint]) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map; `read(member)` gives a DataMap_Win.dat file's bytes or None."""
    name = member(pack)
    win = read(name)
    if win is None:
        raise CoverError(f"{pack} has no {name} in {PACK}, so its cover can't be painted")
    counts = {}  # (what, shape): how many
    for p in paints:
        key = (("cleared " if p.erase else "") + p.layer,
               "line(s)" if p.shape == "line" else "square(s)" if p.squared else "circle(s)")
        counts[key] = counts.get(key, 0) + 1
    return {name: paint(win, paints)}, [", ".join(f"{what}: {n} {shape}" for (what, shape), n in counts.items())]
