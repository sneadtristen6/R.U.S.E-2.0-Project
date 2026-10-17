"""The game's own 3D rocks over the ground painted rock (the owner, 2026-10-16: "can't we just make our own 3D rock
layer generate?", "if giving it dimensions is what needs to be done, we work on that"). A painted rock reads flat
up close whatever its picture: the shipped maps put their close-up detail in 3D, stones and rocks over the picture.
So wherever a palette rock (texture strokes of swatch:<theme>:rock, Paint by shape's steep ground included) shows on
top, the build scatters the map's own rocks over it, as KINDS says:

  flat stone patches (ChampsPierres: 3-6.5 m across, 0.16 m high), stone clusters (Pierres), boulders
  (RocherNormandie_03/04, 1.4-1.8 m), big boulders (RocherNormandie_01/02, 2.4-2.9 m), pebbles (Caillou, close up
  only); on a snow map its frosted rocks, on an African one its own low rocks, by the map's own mix.

Only types the map's scenery lists (loaded on it: a type from another theatre isn't), each kind's in the proportions
the map places them, or alike where it places none (a blank map keeps its names). Eugen sets his upright at their base (their models start there), so on a slope their downhill
side floats; these are laid to the ground instead (tilted square to it, a full transform the game draws: its
leaning ladders), turned at random, a little leaned off it and sunk by part of their height, so none floats and they
read as rock coming out of the slope. Each kind its own grid over the rock strokes' boxes, a point every
sqrt(100 m^2 / its density), shifted at random (the same every build: `seed`); a point takes a rock where the stroke
on top paints it at least ROCK_AT strongly, more of them the steeper the ground (Italy's slope layer is twice as
dense on slopes as on the flat). Drawn close and middle (pebbles close only), as the shipped ones."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

M = 260.0              # map units to the metre
ROCK_AT = 0.5          # a point takes a rock where the stroke on top paints it at least this strongly (as decals)
CELL = 2.0 * M         # the ground's heights read on a grid this fine round the rocks (their slope and tilt)
TILE = 128             # heights read in tiles of this many CELLs a side, only where rocks go
ROCK_BYTES = 72        # what one rock adds to a map's scenery, about: a full 48-byte transform, its word, its list
                       # entries and a little for its block (groundtex.DECAL_BYTES is a compact decal's 40)
FLAT = 0.5             # the share of points kept on flat ground; all of them from STEEP_ALL degrees
STEEP_ALL = 30.0


@dataclass(frozen=True)
class RockKind:
    name: str
    types: tuple          # the game's types it may lay (short names): those the map places, by the map's own mix
    per100: float         # how many per 100 m^2 of rock ground (at STEEP_ALL and steeper)
    size: tuple           # (least, most) scale
    sink: tuple           # (least, most) share of its height sunk into the ground
    lean: float           # degrees it may lean off square to the ground, at random
    levels: int           # the draw levels (scenery.NewObject.levels): 5 close and middle, 1 close only


KINDS = (
    RockKind("patch", ("ChampsPierres_02", "ChampsPierres_03", "ChampsPierres_04", "ChampsPierres_05",
                       "ChampsPierres"), 0.8, (0.5, 1.4), (0.0, 0.3), 3.0, 5),
    RockKind("stones", ("Pierres", "rochelow_bright", "rochelow"), 1.5, (0.8, 1.8), (0.1, 0.3), 8.0, 5),
    RockKind("boulder", ("RocherNormandie_03", "RocherNormandie_04", "Rocher_3_G", "Rocher_4_G", "rochemax_bright",
                         "rochemax"), 1.0, (0.5, 1.2), (0.15, 0.4), 12.0, 5),
    RockKind("big", ("RocherNormandie_01", "RocherNormandie_02", "Rocher_1_G", "Rocher_2_G"), 0.25, (0.6, 1.3),
             (0.2, 0.45), 10.0, 5),
    RockKind("pebble", ("Caillou_01", "Caillou_02", "Caillou_03", "Caillou_04", "Caillou_06", "Caillou_08",
                        "Caillou_09", "Caillou_10", "Caillou_14"), 3.0, (0.8, 1.2), (0.0, 0.2), 20.0, 1),
)


def is_rock(stroke) -> bool:
    """Whether a stroke lays a palette's rock with its 3D rocks on."""
    return (stroke.kind.kind == "texture" and stroke.rocks and stroke.texture.startswith("swatch:")
            and stroke.texture.rsplit(":", 1)[-1] == "rock")


def rock_room(scenery_len: int, taken: int = 0) -> int:
    """How many rocks a map's scenery of `scenery_len` bytes has room for, `taken` bytes already promised (decals)."""
    from .groundtex import ROOM_KEPT, SCENERY_MOST
    return max(0, (SCENERY_MOST - ROOM_KEPT - scenery_len - taken) // ROCK_BYTES)


def map_mix(used: dict[str, int]) -> dict[str, list]:
    """{kind: [(full type name, its weight)]}: each kind's types in the map's name table (`used`: full name -> how
    many the map places; a name the map's scenery lists is loaded on it), by short name, weighed by how many the map
    places, or alike when it places none of them (a blank map: its scenery erased, its names kept)."""
    by_short = {n.split("/")[-1]: (n, c) for n, c in used.items()}
    out = {}
    for k in KINDS:
        have = [by_short[t] for t in k.types if t in by_short]
        out[k.name] = have if any(c for _n, c in have) else [(n, 1) for n, _c in have]
    return {k: [(n, c) for n, c in v if c] for k, v in out.items()}


class _Heights:
    """The built ground's heights on a CELL grid, read in tiles where asked (Tms.height_box), for the height's slope
    and the ground's up direction at a point."""

    def __init__(self, mesh):
        self.mesh, self.tiles = mesh, {}

    def _tile(self, tx: int, ty: int):
        got = self.tiles.get((tx, ty))
        if got is None:
            side = TILE * CELL
            x0, y0 = tx * side - CELL, ty * side - CELL   # a square more round it, for the slope at its edge
            got = (x0, y0, self.mesh.height_box(x0, y0, x0 + side + 2 * CELL, y0 + side + 2 * CELL, CELL))
            self.tiles[(tx, ty)] = got
        return got

    def normal(self, x: float, y: float) -> tuple | None:
        """The ground's up direction at (x, y) (a unit vector), from the heights round it; None off the mesh."""
        side = TILE * CELL
        x0, y0, grid = self._tile(int(math.floor(x / side)), int(math.floor(y / side)))
        i, j = int((x - x0) / CELL - 0.5), int((y - y0) / CELL - 0.5)
        rows, cols = len(grid), len(grid[0])
        i, j = max(1, min(cols - 3, i)), max(1, min(rows - 3, j))
        z = [[grid[j + b][i + a] for a in (-1, 0, 1, 2)] for b in (-1, 0, 1, 2)]
        if any(v is None for row in z for v in row):
            return None
        # the slope over the 2 x 2 squares round the point (central differences, averaged)
        gx = sum(z[b][a + 1] - z[b][a - 1] for b in (1, 2) for a in (1, 2)) / (4 * 2 * CELL)
        gy = sum(z[b + 1][a] - z[b - 1][a] for b in (1, 2) for a in (1, 2)) / (4 * 2 * CELL)
        n = math.sqrt(gx * gx + gy * gy + 1.0)
        return (-gx / n, -gy / n, 1.0 / n)


def rock_layer(strokes: list, mesh, used: dict[str, int], box_of, seed: str = "", most: int | None = None,
               inside: tuple[float, float] | None = None) -> tuple[list, dict]:
    """The rocks over the palette rock painted on a map: (scenery.NewObject list, {"types": {type: count}, "kinds":
    {kind: count}, "thinned": whether they were thinned to fit}). `strokes`: the map's paint strokes in the order
    they are laid; `mesh` (a Tms): the ground as built; `used`: the map's types and how many it places (Scenery.types,
    by name); `box_of(type)`: its model's box (min x, y, z, max x, y, z, map units) or None. With `inside` (the scenery
    grid's width and height) no rock off it; with `most` (rock_room), the rocks thinned evenly to fit."""
    from .brush import PAINT_KINDS
    from .scenery import NewObject
    said = {"types": {}, "kinds": {}, "thinned": False}
    lay = [s for s in strokes if is_rock(s)]
    mix = map_mix(used)
    if not lay or not any(mix.values()):
        return [], said
    paint = [s for s in strokes if s.kind.kind in PAINT_KINDS]
    boxes = [s.box() for s in paint]
    bucket = 64.0 * M   # strokes filed by the cells their boxes reach, to find the ones over a point
    cells: dict = {}
    for k, (bx0, bx1, by0, by1) in enumerate(boxes):
        for cx in range(int(bx0 // bucket), int(bx1 // bucket) + 1):
            for cy in range(int(by0 // bucket), int(by1 // bucket) + 1):
                cells.setdefault((cx, cy), []).append(k)

    def rock_on_top(x, y) -> bool:
        for k in reversed(cells.get((int(x // bucket), int(y // bucket)), [])):
            bx0, bx1, by0, by1 = boxes[k]
            if bx0 <= x <= bx1 and by0 <= y <= by1 and paint[k].strength_at(x, y) * paint[k].weight >= ROCK_AT:
                return is_rock(paint[k])
        return False
    ground = _Heights(mesh)
    heights = {}
    found = []   # (rank, NewObject, kind name)
    for kind in KINDS:
        types = mix[kind.name]
        if not types:
            continue
        total = sum(c for _t, c in types)
        step = 10.0 * M / math.sqrt(kind.per100)
        done = set()
        for s in lay:
            bx0, bx1, by0, by1 = s.box()
            for iy in range(math.floor(by0 / step), math.floor(by1 / step) + 1):
                for ix in range(math.floor(bx0 / step), math.floor(bx1 / step) + 1):
                    if (ix, iy) in done:
                        continue
                    done.add((ix, iy))
                    rnd = random.Random(f"rocks {seed} {kind.name} {ix} {iy}")   # the same every build
                    x = (ix + 0.5 + rnd.uniform(-0.45, 0.45)) * step
                    y = (iy + 0.5 + rnd.uniform(-0.45, 0.45)) * step
                    keep, rank = rnd.random(), rnd.random()
                    if inside is not None and not (0.0 <= x < inside[0] and 0.0 <= y < inside[1]):
                        continue
                    if not rock_on_top(x, y):
                        continue
                    up = ground.normal(x, y)
                    if up is None:
                        continue
                    slope = math.degrees(math.acos(max(-1.0, min(1.0, up[2]))))
                    if keep > FLAT + (1.0 - FLAT) * min(1.0, slope / STEEP_ALL):
                        continue
                    pick = rnd.uniform(0.0, total)
                    for t, c in types:
                        pick -= c
                        if pick <= 0.0:
                            break
                    size = round(rnd.uniform(*kind.size), 3)
                    if t not in heights:
                        b = box_of(t)
                        heights[t] = (b[5] - min(0.0, b[2])) if b else 0.0
                    lean = math.radians(rnd.uniform(0.0, kind.lean))
                    way = rnd.uniform(0.0, 2.0 * math.pi)
                    ux, uy, uz = (up[0] + math.sin(lean) * math.cos(way), up[1] + math.sin(lean) * math.sin(way),
                                  up[2])
                    n = math.sqrt(ux * ux + uy * uy + uz * uz)
                    lift = -rnd.uniform(*kind.sink) * heights[t] * size
                    found.append((rank, NewObject(t, x, y, rnd.uniform(0.0, 360.0), size, solid=False,
                                                  lift=round(lift, 1), levels=kind.levels,
                                                  up=(ux / n, uy / n, uz / n)), kind.name))
    if most is not None and len(found) > most:   # thinned evenly: the same look, fewer of them
        found = sorted(found, key=lambda r: r[0])[:most]
        said["thinned"] = True
    out = []
    for _rank, o, kind_name in found:
        out.append(o)
        said["types"][o.type] = said["types"].get(o.type, 0) + 1
        said["kinds"][kind_name] = said["kinds"].get(kind_name, 0) + 1
    return out, said
