"""Cliff faces made of rock scans (the owner, 2026-10-17, after the asset tests: the scans "look good ... better than a
lot of the game's textures", "it's not supposed to be like a full rock. It's just a side of a mountain"; "let's try
and do the generation test with some of these rock faces. Automatically generating maybe inside of each other all
together, mixed around, whatever looks the best on these like mountain sides or cliff faces").

A [[cliffs]] area of a map's scenery.toml (rusemod.scenery.CliffArea) names the scans and how; the build lays them on
the ground as built, after the terrain strokes:
  - over the area, a point every `spacing` times a scan's width (their mean, at their middle size: under 1, they
    overlap and grow into each other), each moved a little at random (the same every build);
  - a point on ground at least `steep` degrees takes a scan, of the area's types at random, `size` at random;
  - its front (Shape.front: the way the scan's surface faces in its own axes) turned to face downhill, give or take
    TURN_JITTER degrees, and tilted about its own across axis until its front leans as the ground does, `lean` of the
    way (a scan's front already leans: Shape.rise);
  - sunk by `sink` times its height, so no edge stands off the slope.
Scans with no back (a rock face) show their front out of the hill; seen from inside the hill nothing shows, as on a
mountain's side."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

M = 260.0              # map units to the metre
TURN_JITTER = 20.0     # degrees a scan turns off facing straight downhill, at most either way
TILT_MOST = (-20.0, 60.0)   # degrees a scan tilts (top out over the slope, top back into it), at most


@dataclass(frozen=True)
class Shape:
    """A scan as placed at size 1: metres across its front and up, and the way its front faces in its own axes
    (front: degrees from its x toward its y; rise: degrees up from level)."""
    width: float
    height: float
    front: float
    rise: float


def shape_of(pos, tri) -> Shape:
    """A model's Shape from its points (n, 3: metres, the game's axes: x, y, z up) and triangles (n, 3): its front is
    the way its surface faces, on the whole (its triangles' facing, weighted by their area); its width, its extent
    across that way."""
    from .numpy2 import np
    pos, tri = np.asarray(pos, dtype=np.float64), np.asarray(tri, dtype=np.int64)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    facing = np.cross(b - a, c - a).sum(axis=0)
    front = math.degrees(math.atan2(facing[1], facing[0]))
    rise = math.degrees(math.atan2(facing[2], math.hypot(facing[0], facing[1])))
    across = np.array([-math.sin(math.radians(front)), math.cos(math.radians(front)), 0.0])
    used = pos[np.unique(tri)]
    width = float((used @ across).max() - (used @ across).min())
    height = float(used[:, 2].max() - min(0.0, used[:, 2].min()))
    return Shape(width, height, front, rise)


def cliff_layer(areas: list, mesh, shapes: dict, inside: tuple[float, float] | None = None) -> tuple[list, dict]:
    """The scans of every cliff area (scenery.CliffArea) on the ground `mesh` (a Tms, as built): (scenery.NewObject
    list, {"types": {type: count}, "unknown": [types no shape is known of]}). `shapes`: {type: Shape}. With `inside`
    (the scenery grid's width and height) none off it."""
    from .rocks import _Heights
    from .scenery import NewObject
    ground = _Heights(mesh)
    out, said = [], {"types": {}, "unknown": []}
    for k, area in enumerate(areas):
        kinds = [t for t in area.types if t in shapes]
        said["unknown"] += [t for t in area.types if t not in shapes and t not in said["unknown"]]
        if not kinds:
            continue
        middle = (area.size[0] + area.size[1]) / 2.0
        step = max(0.5, area.spacing * middle * sum(shapes[t].width for t in kinds) / len(kinds)) * M
        r = area.radius
        for iy in range(math.floor((area.y - r) / step), math.floor((area.y + r) / step) + 1):
            for ix in range(math.floor((area.x - r) / step), math.floor((area.x + r) / step) + 1):
                rnd = random.Random(f"cliffs {area.seed} {k} {ix} {iy}")   # the same every build
                x = (ix + 0.5 + rnd.uniform(-0.4, 0.4)) * step
                y = (iy + 0.5 + rnd.uniform(-0.4, 0.4)) * step
                t = rnd.choice(kinds)
                size = rnd.uniform(*area.size)
                jitter = rnd.uniform(-TURN_JITTER, TURN_JITTER)
                if math.hypot(x - area.x, y - area.y) > r:
                    continue
                if inside is not None and not (0.0 <= x < inside[0] and 0.0 <= y < inside[1]):
                    continue
                up = ground.normal(x, y)
                if up is None:
                    continue
                slope = math.degrees(math.acos(max(-1.0, min(1.0, up[2]))))
                if slope < area.steep:
                    continue
                s = shapes[t]
                downhill = math.atan2(up[1], up[0])   # (the ground's up leans downhill)
                turn = (math.degrees(downhill) - s.front + jitter) % 360.0
                # tilt about its across axis: its front's rise to the ground's (90 - slope), `lean` of the way
                tilt = area.lean * ((90.0 - slope) - s.rise)
                tilt = math.radians(max(TILT_MOST[0], min(TILT_MOST[1], tilt)))
                d = math.radians(math.degrees(downhill) + jitter)   # (where its front faces)
                up_now = (-math.sin(tilt) * math.cos(d), -math.sin(tilt) * math.sin(d), math.cos(tilt))
                lift = -area.sink * s.height * size * M
                out.append(NewObject(t, x, y, round(turn, 2), round(size, 3), solid=False, lift=round(lift, 1),
                                     up=tuple(round(v, 6) for v in up_now)))
                said["types"][t] = said["types"].get(t, 0) + 1
    return out, said
