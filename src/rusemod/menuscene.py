"""A map's menu pictures made in Blender (the Studio's Make in Blender; rusemod.blender_menu runs in Blender): what the
scene needs, written into a work folder. The owner, 2026-10-05: "the option for a custom PNG or model and then also
being able to make your own".

- scene.json: the kind of scene ("map": the map's own ground; "ocean", "land": a blank map's flat sea or grass), the
  map's size, its sea level, its starting points, both cameras and where the renders go.
- ground.f32 / ground.u32 and water.f32 / water.u32 ("map" only): the map's close-up ground and the water over it as
  meshes (x, y, z and the ground picture's u, v per point; three point numbers per triangle), with the ground
  picture beside them (the Studio's own, made from the map's texture tiles: rusemod.terrain.ground_png).

Blender's axes: x east, y north, z up, a Blender metre to every 100 map units, the map's middle at 0, 0. That isn't
to scale (a map unit is about 1/260 of a metre: rusemod.nav.METRE); only the framing counts, and the scene's look (eye
heights, haze) was set by eye at this scale. The game's y grows toward the south, so y is turned round (and every
triangle with it, to keep its top side up).

The 3D map's camera is worked out from the map's size so the map's top lands where rusemod.menudraw draws a slab
(its back edge 349 pixels wide at row 10, its front 580 at row 170): the build's start dots (map.toml start_dots)
then sit on the render where the starting points are."""
from __future__ import annotations

import json
import math
from array import array
from pathlib import Path

from . import menudraw

SCALE = 0.01            # map units -> Blender metres (not to scale: see above)
BIG = (1280, 720)       # the big picture's render (the menus' 640 x 360, halved by the build)
WIDE = (1360, 400)      # the 3D map's render (680 x 200)
SEA_SHARE = 0.05        # a map with more of its ground under its sea than this gets the sea round it, else land


class SceneError(ValueError):
    pass


def wide_camera(width: float, depth: float, z: float) -> dict:
    """The 3D map's camera for a map `width` x `depth` metres whose top is at height `z`: {"location", "rotation"
    (radians), "lens" (mm, on a 36 mm wide sensor), "soil" (how deep the slab's sides go under the top, metres)}. It
    looks north at the map from the south, its middle on the map's middle line, so that the map's top is drawn as
    rusemod.menudraw's slab. A map too wide for that framing (more than about 2.6 times as wide as deep) gets the
    widest the framing allows."""
    w_px = menudraw.WIDTH
    cy = menudraw.HEIGHT / 2
    yb, yf, soil = menudraw.BACK_Y, menudraw.FRONT_Y, menudraw.SOIL
    r = menudraw.FRONT_W / menudraw.BACK_W
    sin_t = min(0.95, width * ((cy - yb) * r + (yf - cy)) / (menudraw.FRONT_W * depth))
    t = math.asin(sin_t)
    cos_t = math.cos(t)
    z_front = depth * cos_t / (r - 1)                  # the front edge's distance along the view
    f = menudraw.FRONT_W * z_front / width             # the focal length in pixels
    y_front = -(yf - cy) * width / menudraw.FRONT_W    # the front edge's height in the view
    s = z_front * cos_t + y_front * sin_t              # the camera's distance south of the front edge
    h = z_front * sin_t - y_front * cos_t              # and over the map's top
    k = (soil + yf - cy) / f                           # the soil's bottom row, as a slope in the view
    deep = s * (sin_t + k * cos_t) / (cos_t - k * sin_t) - h
    return {"location": [0.0, -(s + depth / 2), z + h], "rotation": [math.pi / 2 - t, 0.0, 0.0],
            "lens": f * 36.0 / w_px, "soil": deep}


EYES = {"map": (2000.0, -14.0), "ocean": (9.0, 5.0), "land": (24.0, 4.5)}  # eye height (m) and look up (degrees)


def big_camera(depth: float, z: float, kind: str = "map") -> dict:
    """The big picture's camera: on the map's south edge, over its top, looking north across it: a map's from high
    up, its land and coasts to the horizon (its ground picture is too coarse up close); a blank map's from just over
    the sea or the grass, a little upward (more sky), as the Studio's own blank pictures."""
    eye, up = EYES[kind]
    return {"location": [0.0, -depth / 2, z + eye], "rotation": [math.radians(90.0 + up), 0.0, 0.0], "lens": 28.0}


def _write(path: Path, typecode: str, values) -> None:
    a = array(typecode, values)
    if a.itemsize != 4:
        raise SceneError(f"this Python's {typecode!r} arrays aren't 4 bytes")
    import sys
    if sys.byteorder != "little":
        a.byteswap()
    path.write_bytes(a.tobytes())


def ground_meshes(tms, folder: Path) -> dict:
    """The map's close-up ground (rusemod.tms.Tms) as ground.f32 / .u32 and the water over it as water.f32 / .u32 in
    `folder`. Returns {"ground": points, "triangles", "water": points, "water_triangles", "sea": the sea's height
    (m), "under": the share of the ground's points under the sea}."""
    x0, y0, z0, x1, y1, z1 = tms.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy, sz, q = x1 - x0, y1 - y0, z1 - z0, 32767
    sea_q = tms.base_water()
    pts, tri, wpts, wtri = array("f"), array("I"), array("f"), array("I")
    base = wbase = under = total = 0
    for cell in tms.cells:
        verts = cell.positions()
        for x, y, z, w in verts:
            wx, wy = x0 + x * sx / q, y0 + y * sy / q
            pts.extend(((wx - cx) * SCALE, (cy - wy) * SCALE, (z0 + z * sz / q) * SCALE, x / q, 1.0 - y / q))
            wpts.extend(((wx - cx) * SCALE, (cy - wy) * SCALE, (z0 + w * sz / q) * SCALE))
            total += 1
            under += z <= sea_q
        g = cell.triangles(0)
        for i in range(0, len(g) - 2, 3):           # y turned round: each triangle the other way, top side up
            tri.extend((base + g[i], base + g[i + 2], base + g[i + 1]))
        u = cell.triangles(1)
        for i in range(0, len(u) - 2, 3):
            wtri.extend((wbase + u[i], wbase + u[i + 2], wbase + u[i + 1]))
        base += len(verts)
        wbase += len(verts)
    _write(folder / "ground.f32", "f", pts)
    _write(folder / "ground.u32", "I", tri)
    _write(folder / "water.f32", "f", wpts)
    _write(folder / "water.u32", "I", wtri)
    return {"ground": base, "triangles": len(tri) // 3, "water": wbase, "water_triangles": len(wtri) // 3,
            "sea": (z0 + sea_q * sz / q) * SCALE, "under": under / total if total else 0.0}


def write_scene(folder: Path, kind: str, bounds: tuple, starts, picture_out: Path, wide_out: Path, *, tms=None,
                ground_picture: Path | None = None, middle: float | None = None) -> Path:
    """Write what Blender needs for a map's menu-picture scene into `folder` (made if missing): `kind` "map" (with
    `tms`, the map's close-up ground, and `ground_picture`, its picture), or "ocean" / "land" (a blank map: flat at
    `middle`, a world height). `bounds`: the ground's x0, y0, x1, y1 (map units); `starts`: the starting points
    (x, y[, z], map units); the renders go to `picture_out` and `wide_out`. Returns scene.json's path."""
    if kind not in ("map", "ocean", "land"):
        raise SceneError(f"no scene kind {kind!r}")
    folder.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = bounds
    width, depth = (x1 - x0) * SCALE, (y1 - y0) * SCALE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cfg: dict = {"kind": kind, "size": [width, depth], "picture": str(picture_out), "wide_picture": str(wide_out),
                 "big_size": list(BIG), "wide_size": list(WIDE)}
    if kind == "map":
        if tms is None:
            raise SceneError("a map's scene needs its ground")
        made = ground_meshes(tms, folder)
        cfg.update(ground=made, surroundings="sea" if made["under"] > SEA_SHARE else "land",
                   ground_picture=str(ground_picture) if ground_picture else None)
        zs = sorted(tms.to_world(2, p[2]) for c in tms.cells for p in c.positions())
        top = zs[len(zs) // 2] * SCALE if zs else made["sea"]   # the slab's top: the ground's middle height
    else:
        top = (middle or 0.0) * SCALE
        cfg["surroundings"] = "sea" if kind == "ocean" else "land"
    cfg["top"] = top
    cfg["starts"] = [[(p[0] - cx) * SCALE, (cy - p[1]) * SCALE, (p[2] if len(p) > 2 else 0.0) * SCALE]
                     for p in starts]
    cfg["wide_camera"] = wide_camera(width, depth, top)
    cfg["big_camera"] = big_camera(depth, top, kind)
    path = folder / "scene.json"
    path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    return path
