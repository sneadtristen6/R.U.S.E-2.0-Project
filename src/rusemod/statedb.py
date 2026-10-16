"""The map's level-build state database (output\\output.sdb in the map pack): a quadtree of one byte per small cell
(D-Day: 4,096 x 4,096 cells of 3.7 m over a square from its corners), the same SDB format as mapinfo.win's cover grid
(ruse_mod_engine.sdb). What its bits mean, measured on D-Day against its own meshes and scenery (2026-10-16,
a 64 x 64 sample of the map):

- 0x08 water: the cells reading 0x09 lie under the close-up mesh's water 100.0% of the time and hold scenery 0.9%;
  the ones reading 0x01 2.9% (shore cells);
- 0x01 every cell of the map (the leaf mark); 0x10 with scenery on it (0x11: 97% hold objects); 0x04 blocked (0x05).

The game draws no scenery decor on a cell it reads as water: on the blank farm (2026-10-16) the fields copied onto
D-Day's drained sea (0x09) drew no crops, stones, plants or trees at any distance, field 7, half on D-Day's land
(0x01), drew its trees and fences there, and the kept area round the HQ (0x01) drew everything (F-46). The build
left this file as the copied map had it. with_water() writes the water bit again from a new close-up mesh."""
from __future__ import annotations

import struct

from .tms import Tms

MEMBER = "output\\output.sdb"
WATER = 0x08
SCENERY = 0x10


def corners(p: dict) -> tuple[float, float, float, float]:
    """The grid's square (x0, y0, x1, y1, map units): the first four floats of the SDB's header."""
    return struct.unpack_from("<4f", p["prefix"], 0)


def water_mask(mesh: Tms, box: tuple, R: int):
    """R x R booleans (row = y, as the SDB's grid): whether each cell's middle lies under one of the close-up mesh's
    water triangles (its list 1)."""
    import numpy as np
    x0, y0, x1, y1 = box
    sx, sy = (x1 - x0) / R, (y1 - y0) / R
    out = np.zeros((R, R), bool)
    for k, c in enumerate(mesh.cells):
        tri = c.triangles(1)
        if not tri:
            continue
        pts = mesh.world_vertices(k)
        for t in range(0, len(tri) - 2, 3):
            a, b, d = pts[tri[t]], pts[tri[t + 1]], pts[tri[t + 2]]
            i0 = max(0, int((min(a[0], b[0], d[0]) - x0) / sx - 0.5))
            i1 = min(R - 1, int((max(a[0], b[0], d[0]) - x0) / sx - 0.5) + 1)
            j0 = max(0, int((min(a[1], b[1], d[1]) - y0) / sy - 0.5))
            j1 = min(R - 1, int((max(a[1], b[1], d[1]) - y0) / sy - 0.5) + 1)
            if i1 < i0 or j1 < j0:
                continue
            den = (b[1] - d[1]) * (a[0] - d[0]) + (d[0] - b[0]) * (a[1] - d[1])
            if den == 0:
                continue
            xs = x0 + (np.arange(i0, i1 + 1) + 0.5) * sx
            ys = y0 + (np.arange(j0, j1 + 1) + 0.5) * sy
            X, Y = np.meshgrid(xs, ys)
            l1 = ((b[1] - d[1]) * (X - d[0]) + (d[0] - b[0]) * (Y - d[1])) / den
            l2 = ((d[1] - a[1]) * (X - d[0]) + (a[0] - d[0]) * (Y - d[1])) / den
            inside = (l1 >= -1e-9) & (l2 >= -1e-9) & (1.0 - l1 - l2 >= -1e-9)
            out[j0:j1 + 1, i0:i1 + 1] |= inside
    return out


def with_water(raw: bytes, mesh: Tms, before: Tms | None = None) -> tuple[bytes, int, int]:
    """(the state database with its water bit as the close-up mesh `mesh` draws its water, cells made dry, cells made
    wet). With `before` (the mesh the file was made for), only cells whose water the new mesh changes are touched:
    Eugen's own marks stay where the ground is as he made it (on D-Day this cell-middle test and his file differ on
    1.5% of the cells, along the shores). A cell made wet loses the scenery bit too (no shipped cell carries both);
    every other bit and every untouched node stays as it was."""
    import numpy as np
    from ruse_mod_engine import sdb
    p = sdb.parse(raw)
    grid, R = sdb.to_grid(p)
    cur = np.frombuffer(bytes(grid), np.uint8).reshape(R, R)
    box = corners(p)
    wet = water_mask(mesh, box, R)
    was = (cur & WATER) > 0
    dried, flooded = was & ~wet, wet & ~was
    if before is not None:
        changed = wet ^ water_mask(before, box, R)
        dried, flooded = dried & changed, flooded & changed
    if dried.any():
        sdb.paint_tree(p, dried, R, WATER, False)
    if flooded.any():
        sdb.paint_tree(p, flooded, R, WATER, True)
        stale = flooded & ((cur & SCENERY) > 0)
        if stale.any():
            sdb.paint_tree(p, stale, R, SCENERY, False)
    if not dried.any() and not flooded.any():
        return bytes(raw), 0, 0
    return sdb.serialize(p), int(dried.sum()), int(flooded.sum())
