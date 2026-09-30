"""Where units hide, and where they can't go: a map's cover and blocked ground, painted by a mod.

Each map has a baked grid in DataMap_Win.dat, `datasmap\\<map>\\mapinfo.win` (its fourth buffer, an SDB quadtree:
LittleGroove's `ruse_mod_engine.sdb` reads and writes it). A cell's byte holds layers; the game asks two of them
(LittleGroove's notes): 0x08, "in forest" (units there are hidden, and ambush), and 0x04, blocked. Eugen's designers
drew these as zones in their editor (forest, obstacle), not from the trees, so a town or a wood made in a mod gives
cover only once cover is painted over it. On Blitz, the trees' cells are 0x08 twice as often as the map's, and two
thirds of the buildings stand on 0x04 cells.

A mod paints circles in maps/<map>/cover.toml (MOD_FORMAT §8), in order, each setting or clearing one layer:

    [[paint]]
    x = 500000.0      # map units, like a scenario's positions
    y = 640000.0
    radius = 20000.0
    layer = "cover"   # or "blocked"
    erase = false     # true clears it (a wood's cover taken away)

A cell is painted when its centre is in the circle. The tree is edited in place: leaves the circles don't touch keep
their bytes and place, so painting nothing gives the same file back."""
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


def member(pack: str) -> str:
    """The map's grid inside DataMap_Win.dat: datasmap\\<map in lower case>\\mapinfo.win."""
    return "\\".join(("datasmap", pack.lower(), "mapinfo.win"))


def parse_paints(items, where: str = "cover.toml") -> list[Paint]:
    out = []
    for n, p in enumerate(items or [], start=1):
        at = f"{where}: paint {n}"
        if not isinstance(p, dict):
            raise CoverError(f"{at} isn't a table")
        extra = sorted(set(p) - {"x", "y", "radius", "layer", "erase"})
        if extra:
            raise CoverError(f"{at}: unknown key {extra[0]!r}")
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
        out.append(Paint(float(p["x"]), float(p["y"]), float(p["radius"]), layer, erase))
    return out


def paints_toml(paints: list[Paint], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for p in paints:
        lines += ["[[paint]]", f"x = {p.x!r}", f"y = {p.y!r}", f"radius = {p.radius!r}", f'layer = "{p.layer}"']
        if p.erase:
            lines.append("erase = true")
        lines.append("")
    return "\n".join(lines)


def _tree(win: bytes):
    parts = sdb.split_mapinfo(win)
    if not parts:
        raise CoverError("not a mapinfo.win")
    tree = sdb.parse(parts[1][3])
    x0, y0, width, height = struct.unpack_from("<4f", tree["prefix"], 0)
    return tree, (x0, y0, width, height)


def grid(win: bytes) -> dict:
    """The map's grid, for showing it: {"size": R, "box": (x0, y0, width, height) in map units, "cells": R*R
    bytes}, row by row from the box's corner (a row is one y, going down the map: y grows south)."""
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
        # which cells: their centres in the circle, in cell units
        cx, cy, rx, ry = (p.x - x0) / cw - 0.5, (p.y - y0) / ch - 0.5, p.radius / cw, p.radius / ch

        def inside(x, y):  # a cell's centre, as an ellipse in cells (square cells make it a circle)
            return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0

        def state(x, y, s):
            """0: no cell of the square [x, x+s)² is painted; 1: all of them; 2: some."""
            nx, ny = min(max(cx, x), x + s - 1), min(max(cy, y), y + s - 1)  # the nearest cell centre
            if not inside(nx, ny):
                return 0
            far = all(inside(a, b) for a in (x, x + s - 1) for b in (y, y + s - 1))  # an ellipse is convex
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

        if 0 <= cx + rx and cx - rx < r and 0 <= cy + ry and cy - ry < r:  # a circle off the map changes nothing
            rec(ns, 0, 0, r)
    return sdb.replace_buffer4(win, sdb.serialize(tree))


def apply_paints(read, pack: str, paints: list[Paint]) -> tuple[dict, list[str]]:
    """({member: new mapinfo.win}, notes) for one map; `read(member)` gives a DataMap_Win.dat file's bytes or None."""
    name = member(pack)
    win = read(name)
    if win is None:
        raise CoverError(f"{pack} has no {name} in {PACK}, so its cover can't be painted")
    counts = {}
    for p in paints:
        key = ("cleared " if p.erase else "") + p.layer
        counts[key] = counts.get(key, 0) + 1
    return {name: paint(win, paints)}, [", ".join(f"{k}: {n} circle(s)" for k, n in counts.items())]
