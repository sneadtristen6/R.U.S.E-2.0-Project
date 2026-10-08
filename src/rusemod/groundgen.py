"""A new map's ground drawn as our own, from its strokes (map.toml ground = "generated"; the owner, 2026-10-07, after
the navy test's islands: "The whole map should be made but like that. From now on.").

The build's usual way moves the copied map's existing points by the strokes: the gameplay ground (coarse) first, the
drawn meshes then copying it, so an island's shore is as ragged as the old triangles under it, its top dented where a
big triangle reached into the sea, the far view blocky, and units and buildings standing up to metres off what's drawn
(measured on Blank Ocean, 2026-10-07). Here the map starts flat (its first height stroke levels the whole map, as Blank
Terrain and Blank Ocean do) and every file is made again from the strokes' own shape:

- the close-up mesh (highdef.tms) and the far mesh (lowdef.tms): one grid over the whole map, PER_CELL squares a cell
  each way, so neighbouring cells share their edge points exactly (as shipped cells do); a cell the strokes change is
  the whole grid, each square two triangles, every triangle crossing the water cut there on the shape itself (marching
  triangles): wholly wet or wholly dry, the water's edge on the true outline (a grid point the edge passes within
  SNAP_STEPS of the file's steps goes onto the water, so no triangle folds once rounded); a cell they don't change keeps
  the grid's points on its edges only and draws each of its 64 patches as a fan round the patch's middle. Patches in the
  shipped order, each its own run of points; list 1 = the triangles wholly under water; normals from the faces over the
  whole map; parents = the previous point;
- the edge's skirt (the curtain hanging from the map's edge, and the water's side) following the new edge;
- the gameplay ground (occlusioninfo_terrainonly.kdt: where units and new buildings stand, and where a click lands):
  exactly the close-up mesh's triangles, each of its subtrees holding the ones that touch its region, its trees built
  again;
- the water's pictures (the three water textures): every water cell of the map worked out from the new meshes (the
  open sea from the shape at once, the cells by an island sampled as rusemod.water samples them);
- the map's own road model, if it stays, laid on the new ground.

The camera floor (occlusioninfo_camera.kdt) and the floors units stand on over bridges are not made here.
Seen in the game (navy test copies, 2026-10-06/07, the same sums run as test tools): the big island ("perfect. Exactly
what we need"), the far view, the whole close-up mesh, the gameplay ground ("The buildings work and the tanks drive
around just fine")."""
from __future__ import annotations

import math
import struct

from . import kdt_edit
from . import water as W
from .brush import GROUND_UNCHANGED, HARD_EDGE, WATER_KINDS
from .kdt import Kdt, main_regions
from .tms import SKIRT_BOTTOM, Cell, Patch, Q_MAX, Tms, VertexBuffer, encode_indices

PER_CELL_NEAR = 128   # close-up mesh: squares a cell each way (D-Day's cells: a point every 9.85 m)
PER_CELL_FAR = 48     # far mesh (D-Day's: every 52.5 m)
SNAP_STEPS = 2.5      # a water's edge this many of the file's steps from a grid point: the point goes onto the water
REUSE_WITHIN = 8000   # the gameplay ground's index list stores steps of at most 16,383: a point is shared only among
                      # the last this many written
# the 64 patches' (column, row) in the shipped order (a space-filling curve, the same in every shipped cell, close-up
# and far: read from D-Day's)
HILBERT = [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (3, 0), (3, 1), (2, 1), (2, 2), (3, 2), (3, 3), (2, 3), (1, 3),
           (1, 2), (0, 2), (0, 3), (0, 4), (1, 4), (1, 5), (0, 5), (0, 6), (0, 7), (1, 7), (1, 6), (2, 6), (2, 7),
           (3, 7), (3, 6), (3, 5), (2, 5), (2, 4), (3, 4), (4, 4), (5, 4), (5, 5), (4, 5), (4, 6), (4, 7), (5, 7),
           (5, 6), (6, 6), (6, 7), (7, 7), (7, 6), (7, 5), (6, 5), (6, 4), (7, 4), (7, 3), (7, 2), (6, 2), (6, 3),
           (5, 3), (4, 3), (4, 2), (5, 2), (5, 1), (4, 1), (4, 0), (5, 0), (6, 0), (6, 1), (7, 1), (7, 0)]
STILL = bytes((0, 128, 128, 0))   # a flow texel of still water (rusemod.water: a dry cell given water)


class GroundGenError(ValueError):
    """A map whose ground can't be drawn as our own: the build draws it the usual way instead (and says why)."""


# --- the shape ------------------------------------------------------------------------------------------------------
class Shape:
    """The ground's height and the water's level at any point, from a map's strokes in order: the first height stroke
    levels the whole map at full strength (the start), the rest act on it as each brush acts on the build's points
    (rusemod.brush.Stroke.height_at); the water starts at the map's base level, a water stroke sets its level inside
    it, a drain puts the base level back (rusemod.water.apply_water)."""

    def __init__(self, strokes: list, bounds: tuple, base_water: float):
        heights = [s for s in strokes if s.kind.kind not in GROUND_UNCHANGED]
        if not heights or not _levels_all(heights[0], bounds):
            raise GroundGenError("its ground is drawn as our own only from a map flattened all over (a first height "
                                 "stroke levelling the whole map at full strength, as Blank Terrain and Blank Ocean "
                                 "start)")
        if any(s.kind.kind == "smooth" for s in heights):
            raise GroundGenError("a smooth stroke needs the ground around it, and drawn ground has none to ask yet")
        self.base = heights[0].level
        self.rest = [(s, s.box()) for s in heights[1:]]
        self.water = [(s, s.box()) for s in strokes if s.brush in WATER_KINDS]
        self.base_water = base_water

    def h(self, x: float, y: float) -> float:
        z = self.base
        for s, (x0, x1, y0, y1) in self.rest:
            if x0 <= x <= x1 and y0 <= y <= y1:
                z = s.height_at(x, y, z)
        return z

    def w(self, x: float, y: float) -> float:
        level = self.base_water
        for s, (x0, x1, y0, y1) in self.water:
            if x0 <= x <= x1 and y0 <= y <= y1 and s.covers(x, y):
                level = s.level if s.brush == "water" else self.base_water
        return level

    def varies_over(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        """Whether the ground's height or the water's level may change inside the box (a stroke reaching into it
        without covering all of it at one value)."""
        for s, (a0, a1, b0, b1) in self.rest + self.water:
            if a1 < x0 or a0 > x1 or b1 < y0 or b0 > y1:
                continue
            if not _uniform_over(s, x0, y0, x1, y1):
                return True
        return False


def _levels_all(s, bounds) -> bool:
    x0, y0, x1, y1 = bounds
    return (s.kind.kind == "level" and s.kind.shape == "flat" and s.edge == "hard" and s.weight >= 1.0
            and all(s.footprint().t2(x, y) <= HARD_EDGE * HARD_EDGE for x in (x0, x1) for y in (y0, y1)))


def _uniform_over(s, x0, y0, x1, y1) -> bool:
    """A stroke that gives the whole box one value: a full-strength level (hard edge, its full-strength part holding
    the box's corners), or a water/drain stroke holding the whole box (footprints are convex: corners inside = all)."""
    corners = [(x, y) for x in (x0, x1) for y in (y0, y1)]
    f = s.footprint()
    if s.brush in WATER_KINDS:
        return all(f.t2(x, y) < 1.0 for x, y in corners)
    return (s.kind.kind == "level" and s.kind.shape == "flat" and s.edge == "hard" and s.weight >= 1.0
            and all(f.t2(x, y) <= HARD_EDGE * HARD_EDGE for x, y in corners))


# --- the meshes -----------------------------------------------------------------------------------------------------
def fine_cells(t: Tms, shape: Shape) -> set:
    """The cells of mesh `t` the strokes change (drawn as the whole grid)."""
    out = set()
    for row in range(t.grid_h):
        for col in range(t.grid_w):
            if shape.varies_over(col * t.cell_w, row * t.cell_h, (col + 1) * t.cell_w, (row + 1) * t.cell_h):
                out.add(row * t.grid_w + col)
    return out


def make_mesh(t: Tms, h, w, per_cell: int, fine: set) -> tuple[list, dict]:
    """Every cell of mesh `t` (its grid, bounds and storage as they are) from the ground's height `h(x, y)` and the
    water's level `w(x, y)` (world z); `fine`: the cells drawn as the whole grid. Returns (cells, counts)."""
    q = t.to_quant
    assert per_cell % 8 == 0
    s = t.cell_w / per_cell
    nx, ny = t.grid_w * per_cell, t.grid_h * per_cell
    world = t.to_world
    pts, zq, wq, index = [], [], [], {}
    hq, lq = {}, {}   # a grid point's height and water, quantized

    def heights(i, j):
        if (i, j) not in hq:
            x, y = i * s, j * s
            hq[(i, j)], lq[(i, j)] = q(2, h(x, y)), q(2, w(x, y))
        return hq[(i, j)], lq[(i, j)]

    def node(i, j):
        key = ("n", i, j)
        if key not in index:
            z, lv = heights(i, j)
            index[key] = len(pts)
            pts.append((i * s, j * s))
            zq.append(z)
            wq.append(lv)
        return index[key]

    def wet(i, j):
        z, lv = heights(i, j)
        return z < lv

    snap_at = SNAP_STEPS * max(t.bounds[3] - t.bounds[0], t.bounds[4] - t.bounds[1]) / Q_MAX

    def snap(v):   # onto the water: its height the water's own
        z, lv = heights(*v)
        hq[v] = lv
        zq[node(*v)] = lv
        return node(*v)

    def crossing(a, b):
        za, la = heights(*a)
        zb, lb = heights(*b)
        if za == la:
            return node(*a)
        if zb == lb:
            return node(*b)
        key = ("c",) + tuple(sorted((a, b)))
        if key not in index:
            (ax, ay), (bx, by) = (a[0] * s, a[1] * s), (b[0] * s, b[1] * s)
            lo, hi = 0.0, 1.0
            wet_a = h(ax, ay) < w(ax, ay)
            for _ in range(40):
                mid = (lo + hi) / 2
                px, py = ax + mid * (bx - ax), ay + mid * (by - ay)
                if (h(px, py) < w(px, py)) == wet_a:
                    lo = mid
                else:
                    hi = mid
            f = (lo + hi) / 2
            near = snap_at / math.hypot(bx - ax, by - ay)
            if f < near:
                return snap(a)
            if f > 1 - near:
                return snap(b)
            px, py = ax + f * (bx - ax), ay + f * (by - ay)
            level = q(2, w(px, py))
            index[key] = len(pts)
            pts.append((px, py))
            zq.append(level)
            wq.append(level)
        return index[key]

    tris = []

    def cut(a, b, c):
        wets = [wet(*v) for v in (a, b, c)]
        if all(wets) or not any(wets):
            tris.append((node(*a), node(*b), node(*c)))
            return
        vs = [a, b, c]
        lone = next(k for k in range(3) if wets.count(wets[k]) == 1)
        v, p, r = vs[lone], vs[(lone + 1) % 3], vs[(lone + 2) % 3]
        cp, cr = crossing(v, p), crossing(v, r)
        for tri in ((node(*v), cp, cr), (cp, node(*p), node(*r)), (cp, node(*r), cr)):
            if len(set(tri)) == 3:   # a crossing snapped onto a corner leaves that piece empty
                tris.append(tri)

    n8 = per_cell // 8
    flat = 0
    for row in range(t.grid_h):
        for col in range(t.grid_w):
            k = row * t.grid_w + col
            i0, j0 = col * per_cell, row * per_cell
            if k in fine:
                for j in range(j0, j0 + per_cell):
                    for i in range(i0, i0 + per_cell):
                        cut((i, j), (i + 1, j), (i + 1, j + 1))
                        cut((i, j), (i + 1, j + 1), (i, j + 1))
                continue
            flat += 1
            for pr in range(8):
                for pc in range(8):
                    ia, ja = i0 + pc * n8, j0 + pr * n8
                    ib, jb = ia + n8, ja + n8
                    loop = [(i, ja) for i in range(ia, ib)] if ja == j0 else [(ia, ja)]
                    loop += [(ib, j) for j in range(ja, jb)] if ib == i0 + per_cell else [(ib, ja)]
                    loop += [(i, jb) for i in range(ib, ia, -1)] if jb == j0 + per_cell else [(ib, jb)]
                    loop += [(ia, j) for j in range(jb, ja, -1)] if ia == i0 else [(ia, jb)]
                    mx, my = (ia + n8 / 2) * s, (ja + n8 / 2) * s
                    middle = len(pts)
                    pts.append((mx, my))
                    zq.append(q(2, h(mx, my)))
                    wq.append(q(2, w(mx, my)))
                    ids = [node(*v) for v in loop]
                    for a in range(len(ids)):
                        tris.append((middle, ids[a], ids[(a + 1) % len(ids)]))
    qpts = [(q(0, x), q(1, y)) for x, y in pts]
    wpts = [(x, y, world(2, z)) for (x, y), z in zip(pts, zq)]
    fixed, folded = [], 0
    for a, b, c in tris:   # counter-clockwise from above, as shipped; none folded or flat once rounded
        (ax, ay, _), (bx, by, _), (cx, cy, _) = wpts[a], wpts[b], wpts[c]
        tri = (a, b, c) if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0 else (a, c, b)
        (ax, ay), (bx, by), (cx, cy) = qpts[tri[0]], qpts[tri[1]], qpts[tri[2]]
        folded += (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) <= 0
        fixed.append(tri)
    if folded:
        raise GroundGenError(f"{folded} of its triangles would fold once rounded to the file's steps")
    acc = [[0.0, 0.0, 0.0] for _ in pts]
    for a, b, c in fixed:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = wpts[a], wpts[b], wpts[c]
        ux, uy, uz, vx, vy, vz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
        nrm = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        for v in (a, b, c):
            acc[v][0] += nrm[0]
            acc[v][1] += nrm[1]
            acc[v][2] += nrm[2]
    normals = []
    for nv in acc:
        ln = math.sqrt(nv[0] * nv[0] + nv[1] * nv[1] + nv[2] * nv[2]) or 1.0
        normals.append(tuple(max(0, min(255, round((c / ln + 1) * 127.5))) for c in nv) + (128,))
    by_cell: dict = {}
    ps = t.cell_w / 8
    for tri in fixed:
        mx = (wpts[tri[0]][0] + wpts[tri[1]][0] + wpts[tri[2]][0]) / 3
        my = (wpts[tri[0]][1] + wpts[tri[1]][1] + wpts[tri[2]][1]) / 3
        col, row = min(t.grid_w - 1, int(mx // t.cell_w)), min(t.grid_h - 1, int(my // t.cell_h))
        pc = (min(7, int((mx - col * t.cell_w) // ps)), min(7, int((my - row * t.cell_h) // ps)))
        by_cell.setdefault(row * t.grid_w + col, {}).setdefault(pc, []).append(tri)
    cells, wet_tris, wide = [], 0, 0
    for k in range(len(t.cells)):
        patches_in = by_cell.get(k, {})
        positions, norms, list0, list1, patches = [], [], [], [], []
        for cr in HILBERT:
            local = {}
            vstart, i0start, i1start = len(positions), len(list0), len(list1)
            for tri in patches_in.get(cr, []):
                for v in tri:
                    if v not in local:
                        local[v] = len(positions)
                        positions.append(qpts[v] + (zq[v], wq[v]))
                        norms.append(normals[v])
                idx = [local[v] for v in tri]
                list0 += idx
                if all(wq[v] >= zq[v] for v in tri) and any(wq[v] > zq[v] for v in tri):
                    list1 += idx
            patches.append(Patch(vstart, len(positions) - vstart, i0start, len(list0) - i0start, i1start,
                                 len(list1) - i1start, 0.0, 0.0))
        for p in patches:   # the shipped rule (D-Day's and Blitz's dry cells, 2026-10-07): a cell with water bounds a
            run = positions[p.vstart:p.vstart + p.vcount]   # patch from its lowest ground to its highest ground or
            if run and list1:                               # water; a dry one from 0 to its highest ground
                p.zlo = t._z_f32(min(v[2] for v in run))
                p.zhi = t._z_f32(max(max(v[2], v[3]) for v in run))
            elif run:
                p.zhi = t._z_f32(max(v[2] for v in run))
        flags = 3 if list1 else 1   # bit 1: the cell has water (a list 1); dry cells are 1 (D-Day's 2, Blitz's 3)
        if any(max(p.vstart, p.vcount, p.i0start, p.i0count, p.i1start, p.i1count) > 0xFFFF for p in patches):
            flags |= 4
            wide += 1
        if len(positions) > 0xFFFF:
            raise GroundGenError(f"cell {k} would hold {len(positions)} points (a cell's 16-bit indices reach 65,535)")
        vb = VertexBuffer.build(positions, norms, [max(i - 1, 0) for i in range(len(positions))])
        lists = [encode_indices(list0)] + ([encode_indices(list1)] if list1 else [])
        counts = [len(list0)] + ([len(list1)] if list1 else [])
        cell = Cell(flags, len(positions), vb.to_bytes(), lists, counts, b"")
        cell.set_patches(patches)
        cells.append(cell)
        wet_tris += len(list1) // 3
    info = dict(triangles=len(fixed), water=wet_tris, points=sum(c.vcount for c in cells), places=len(pts),
                most=max(c.vcount for c in cells), flat=flat, wide=wide, spacing=s)
    return cells, info


def fit_skirt(t: Tms, h, w) -> int:
    """The skirt hanging from the map's edge (rusemod.tms: the curtain, and the water's side) made to follow the edge
    as drawn now: the curtain's tops at the ground's height, the water's side from the ground up to the water (flat on
    the ground where it stands above it). Tms._fit_skirt follows the edge points an edit moved; a mesh drawn new has
    none to follow, so here each skirt point asks the shape. Returns the skirt points moved."""
    if not any(t.skirt):
        return 0
    data = bytearray(t.skirt_data)
    scale = (t.bounds[5] - SKIRT_BOTTOM) / Q_MAX
    q = t.to_quant
    moved = 0
    for m, (voff, count, boff, poff, nparts) in enumerate(t._skirt_layout()):
        verts = [struct.unpack_from("<3H", data, voff + 8 * j) for j in range(count)]
        foot: dict = {}
        for x, y, z in verts:
            foot[(x, y)] = min(foot.get((x, y), z), z)
        for j, (x, y, z) in enumerate(verts):
            wx, wy = t.to_world(0, x), t.to_world(1, y)
            ground = h(wx, wy)
            if m == 0:   # the curtain: its foot stays, its top goes to the ground
                if z == 0:
                    continue
                nz = min(max(round((ground - SKIRT_BOTTOM) / scale), 1), Q_MAX)
            elif z == foot[(x, y)]:
                nz = q(2, ground)
            else:
                nz = max(q(2, w(wx, wy)), q(2, ground))
            if nz != z:
                struct.pack_into("<H", data, voff + 8 * j + 4, nz)
                moved += 1
        for part in range(nparts):
            vstart, vcount, _i0, _ni = struct.unpack_from("<4I", data, poff + 16 * part)
            if not vcount:
                continue
            zs = [struct.unpack_from("<H", data, voff + 8 * j + 4)[0] for j in range(vstart, vstart + vcount)]
            lo, hi = ((SKIRT_BOTTOM + min(zs) * scale, SKIRT_BOTTOM + max(zs) * scale) if m == 0
                      else (t.to_world(2, min(zs)), t.to_world(2, max(zs))))
            struct.pack_into("<f", data, boff + 24 * part + 8, lo)
            struct.pack_into("<f", data, boff + 24 * part + 20, hi)
    t.skirt_data = bytes(data)
    return moved


# --- the gameplay ground --------------------------------------------------------------------------------------------
def gameplay_ground(k: Kdt, mesh: Tms) -> tuple[bytes, str]:
    """The gameplay ground (a .kdt) holding exactly the close-up mesh's triangles: each subtree the ones that touch its
    region (the MainNode's x/y box; one across two regions in both, so a ray anywhere finds it), points in the tree's
    own steps, normals from the faces over the whole map (z up, as shipped), its own tree built again, the MainNode's
    height clips widened to the new heights."""
    tris = []
    for c_k, c in enumerate(mesh.cells):
        wv = mesh.world_vertices(c_k)
        t0 = c.triangles(0)
        tris += [(wv[t0[i]], wv[t0[i + 1]], wv[t0[i + 2]]) for i in range(0, len(t0), 3)]

    def qp(p):
        return k.to_quant(0, p[0]), k.to_quant(1, p[1]), k.to_quant(2, p[2])
    acc: dict = {}
    for a, b, c in tris:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        if n[2] < 0:
            n = (-n[0], -n[1], -n[2])
        for p in (a, b, c):
            s_ = acc.setdefault(qp(p), [0.0, 0.0, 0.0])
            s_[0] += n[0]
            s_[1] += n[1]
            s_[2] += n[2]
    normal = {}
    for key, (x, y, z) in acc.items():
        ln = math.sqrt(x * x + y * y + z * z) or 1.0
        normal[key] = (x / ln, y / ln, z / ln)
    regions = main_regions(k.main_entries())
    boxes = [(min(p[0] for p in t_), max(p[0] for p in t_), min(p[1] for p in t_), max(p[1] for p in t_))
             for t_ in tris]
    held = []
    for s in range(len(k.subtrees)):
        lo, hi, _path = regions[s]
        x0 = -math.inf if lo[0] is None else lo[0]
        x1 = math.inf if hi[0] is None else hi[0]
        y0 = -math.inf if lo[1] is None else lo[1]
        y1 = math.inf if hi[1] is None else hi[1]
        mine = [n for n, (bx0, bx1, by0, by1) in enumerate(boxes) if bx1 >= x0 and bx0 <= x1 and by1 >= y0 and by0 <= y1]
        index: dict = {}
        pos, nrm, flat = [], [], []
        for n in mine:
            for p in tris[n]:
                key = qp(p)
                at = index.get(key)
                if at is None or len(pos) - at > REUSE_WITHIN:
                    at = index[key] = len(pos)
                    pos.append(key)
                    nrm.append(normal[key])
                flat.append(at)
        if not mine:   # a region with nothing over it: one flat triangle at its corner keeps the subtree valid
            raise GroundGenError(f"the gameplay ground's region {s} holds no triangle")
        k.set_mesh(s, pos, flat, nrm)
        kdt_edit.rebuild(k, s, pos, [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)])
        held.append(len(mine))
    widened = kdt_edit.widen_main(k, range(len(k.subtrees)))
    k.triangle_count = len(tris)
    wrong = [p for s in range(len(k.subtrees)) for p in kdt_edit.check(k, s)] + \
        kdt_edit.check_main(k, range(len(k.subtrees)))
    if wrong:
        raise GroundGenError(f"the gameplay ground's trees came out wrong: {wrong[:3]}")
    return k.to_bytes(), (f"gameplay ground: the close-up mesh's {len(tris)} triangles in its {len(held)} parts "
                          f"({min(held)}..{max(held)} each), {widened} top limit(s) widened")


# --- the water's pictures -------------------------------------------------------------------------------------------
def water_pictures(raws: dict, near_t: Tms, far_t: Tms, shape: Shape, fine_near: set, max_depth: float) -> tuple[dict, str]:
    """The three water textures (rusemod.water.TEXTURES' keys -> bytes) for the meshes as drawn: every water cell of
    the map given its tile again. A cell the close-up mesh draws flat is worked out from the shape at once (one depth
    all over: the shared tile of about that depth, as rusemod.water shares one, or the shared dry tile); a cell the
    strokes change is sampled from the meshes' water as rusemod.water samples it, and gets a shared tile when it's of
    about one depth, else its own with every texel's depth. Every tile not kept is free again first: the shared dry
    and sea tiles stay, the rest of the atlas is ours."""
    (ti, ind), (tw, inp), (tf, flow) = (W._pixels(raws[k]) for k in ("indirection", "inputs", "flow"))
    cols = tw.width // W.TILE
    ntiles = cols * (tw.height // W.TILE)
    across = round((near_t.bounds[3] - near_t.bounds[0]) / W.CASE)
    down = round((near_t.bounds[4] - near_t.bounds[1]) / W.CASE)
    if across > ti.width or down > ti.height:
        raise GroundGenError("its water textures cover fewer cells than the map has")

    def texel(width, t, i):
        return ((t // cols) * W.TILE + i // W.TILE) * width * 4 + ((t % cols) * W.TILE + i % W.TILE) * 4

    users: dict = {}
    for cy in range(down):
        for cx in range(across):
            o = (cy * ti.width + cx) * 4
            t_ = ind[o + 1] * cols + ind[o + 2]
            users[t_] = users.get(t_, 0) + 1
    shared = [t_ for t_ in sorted(users, key=lambda t_: (-users[t_], t_))[:2] if users[t_] > 1]
    dry = next((t_ for t_ in shared if inp[texel(tw.width, t_, 8 * W.TILE + 8) + 2] == 0), None)
    sea = next((t_ for t_ in shared if inp[texel(tw.width, t_, 8 * W.TILE + 8) + 2] == 255), None)
    if dry is None:
        raise GroundGenError("its water textures have no shared dry tile to start from")
    free = [t_ for t_ in range(ntiles) if t_ not in (dry, sea)]
    free.reverse()
    near_w = W._water_triangles(near_t, (across, down))
    far_w = W._water_triangles(far_t, (across, down))
    off = near_t.to_world(2, near_t.base_water()) - far_t.to_world(2, far_t.base_water())
    base = near_t.to_world(2, near_t.base_water())
    step = (near_t.bounds[5] - near_t.bounds[2]) / 32767
    alike: dict = {}
    counts = {"shared": 0, "own": 0, "dry": 0, "sampled": 0}

    def put(cx, cy, t_, flag=0):
        o = (cy * ti.width + cx) * 4
        ind[o:o + 4] = bytes((flag, t_ // cols, t_ % cols, 0))

    def tile_for_shade(shade):
        if shade == 255 and sea is not None:
            return sea
        if shade not in alike:
            if not free:
                raise GroundGenError("its water textures have no tile left")
            t_ = alike[shade] = free.pop()
            for i in range(W.TILE * W.TILE):
                d, f_ = texel(tw.width, t_, i), texel(tf.width, t_, i)
                inp[d:d + 4] = bytes((0, 0, shade, 0))
                flow[f_:f_ + 4] = bytes(4)
        return alike[shade]

    ncw = near_t.grid_w
    for cy in range(down):
        for cx in range(across):
            mx, my = (cx + 0.5) * W.CASE, (cy + 0.5) * W.CASE
            cell = min(near_t.grid_h - 1, int(my // near_t.cell_h)) * ncw + min(ncw - 1, int(mx // near_t.cell_w))
            x0, y0 = cx * W.CASE, cy * W.CASE
            if cell not in fine_near and not shape.varies_over(x0, y0, x0 + W.CASE, y0 + W.CASE):
                depth = shape.w(mx, my) - shape.h(mx, my)
                if depth <= 0:
                    put(cx, cy, dry)
                    counts["dry"] += 1
                    continue
                v = min(max(depth / max_depth, 0.0), 1.0)
                red = int(255.0 * v + 0.5)
                put(cx, cy, tile_for_shade(W._shade([red] * (W.TILE * W.TILE))))
                counts["shared"] += 1
                continue
            counts["sampled"] += 1
            got = W._cell(near_w.get((cx, cy), []), cx, cy, max_depth)
            f = W._cell(far_w.get((cx, cy), []), cx, cy, max_depth) if not all(got[1]) else None
            red, share, mean = W._both(got, f, off)
            if not any(share):
                put(cx, cy, dry)
                counts["dry"] += 1
                continue
            # (a sliver of water, no texel half wet: judged by the texels it reaches; D-Day's own slivers are all rivers)
            wet = ([i for i in range(W.TILE * W.TILE) if share[i] >= 0.5]
                   or [i for i in range(W.TILE * W.TILE) if share[i] > 0])
            at_base = sum(1 for i in wet if abs(mean[i] - base) < 2 * step)
            other = at_base <= len(wet) / 2
            if all(share) and not other and max(red) - min(red) <= W.SHADE // 2:
                put(cx, cy, tile_for_shade(W._shade(red)))
                counts["shared"] += 1
                continue
            if not free:
                raise GroundGenError("its water textures have no tile left")
            t_ = free.pop()
            for i in range(W.TILE * W.TILE):
                d, f_ = texel(tw.width, t_, i), texel(tf.width, t_, i)
                inp[d:d + 4] = bytes((cx, 0, red[i], cy))
                flow[f_:f_ + 4] = STILL
            put(cx, cy, t_, 255 if other else 0)
            counts["own"] += 1
    out = {"indirection": W._repack(ti, ind), "inputs": W._repack(tw, inp), "flow": W._repack(tf, flow)}
    return out, (f"water pictures: {across * down} water cells given their tile again ({counts['sampled']} sampled "
                 f"by the shores, {counts['own']} with a tile of their own, {counts['shared']} sharing one by depth, "
                 f"{counts['dry']} dry)")


# --- the map's own road model ---------------------------------------------------------------------------------------
def road_model_on(raws: dict, mesh: Tms) -> tuple[dict, list[str]]:
    """The map's road model (rusemod.roadstrips, every static-mesh file it has) laid on the new close-up mesh: each
    vertex onto the ground under it. ({member: bytes}, notes)."""
    from .bridges import Ground
    from .roadstrips import STRIDE, StaticMeshes, StripError
    ground = Ground(mesh)
    out, notes = {}, []
    for member, raw in raws.items():
        try:
            sm = StaticMeshes(raw)
            if sm.model is None:
                continue
            d = sm.road_draw()
            _w, _mat, _ib, vb, _g, _p = sm.draws[d]
            base = sm.vb_data[0] + sm.vbs[vb][0]
            at = {}
            for j in range(sm.vbs[vb][1] // STRIDE):
                x, y, z = struct.unpack_from("<3f", sm.raw, base + STRIDE * j)
                g = ground.height_at(x, y)
                if g is not None:
                    at[(x, y)] = g - z
            new, n = sm.with_heights(lambda x, y: at.get((x, y)))
        except StripError as exc:
            notes.append(f"{member.rsplit(chr(92), 1)[-1]}: the road model can't follow the ground ({exc})")
            continue
        if n:
            out[member] = new
            notes.append(f"road model ({member.rsplit(chr(92), 1)[-1]}): {n} point(s) laid on the ground drawn")
    return out, notes


# --- all of it ------------------------------------------------------------------------------------------------------
def generate(read, strokes: list, name: str, max_depth: float | None) -> tuple[dict, list[str]]:
    """A map's ground drawn as our own from `strokes` (all of its mods', in order): ({member: new bytes}, notes).
    `read(member)` gives one of the map pack's files (None when it has none); `max_depth` the map's water depth scale
    (rusemod.water.max_depth). Raises GroundGenError when it can't (the build then draws the map the usual way)."""
    from .roadstrips import MEMBERS as ROAD_MEMBERS
    from .terrain_edit import FILES
    raw = {key: read(FILES[key]) for key in ("highdef", "lowdef", "ground")}
    missing = [FILES[k] for k, v in raw.items() if v is None]
    if missing:
        raise GroundGenError(f"it has no {', '.join(missing)}")
    near, far, k = Tms(raw["highdef"]), Tms(raw["lowdef"]), Kdt(raw["ground"])
    bounds = (near.bounds[0], near.bounds[1], near.bounds[3], near.bounds[4])
    base = near.to_world(2, near.base_water())
    offset = base - far.to_world(2, far.base_water())
    shape = Shape(strokes, bounds, base)
    notes = []
    fine_near = fine_cells(near, shape)
    near.cells, ni = make_mesh(near, shape.h, shape.w, PER_CELL_NEAR, fine_near)
    moved = fit_skirt(near, shape.h, shape.w)
    notes.append(f"{name}: close-up mesh drawn as our own: {ni['triangles']} triangles ({ni['water']} under water), "
                 f"{len(fine_near)} cell(s) a point every {ni['spacing']:.0f} map units, {ni['flat']} flat; most points "
                 f"in a cell {ni['most']}; {moved} skirt point(s) on the new edge")

    def far_w(x, y):
        return shape.w(x, y) - offset
    fine_far = fine_cells(far, shape)
    far.cells, fi = make_mesh(far, shape.h, far_w, PER_CELL_FAR, fine_far)
    moved = fit_skirt(far, shape.h, far_w)
    notes.append(f"{name}: far mesh drawn as our own: {fi['triangles']} triangles, {len(fine_far)} cell(s) on the "
                 f"grid, {fi['flat']} flat; its water {offset:.0f} under the close-up mesh's; {moved} skirt point(s)")
    near_bytes, far_bytes = near.to_bytes(), far.to_bytes()
    near_back, far_back = Tms(near_bytes), Tms(far_bytes)
    ground_bytes, said = gameplay_ground(k, near_back)
    notes.append(f"{name}: {said}")
    out = {FILES["highdef"]: near_bytes, FILES["lowdef"]: far_bytes, FILES["ground"]: ground_bytes}
    if max_depth:
        tex_raw = {key: read(m) for key, m in W.TEXTURES.items()}
        if all(v is not None for v in tex_raw.values()):
            tex, said = water_pictures(tex_raw, near_back, far_back, shape, fine_near, max_depth)
            out.update({W.TEXTURES[key]: data for key, data in tex.items()})
            notes.append(f"{name}: {said}")
        else:
            notes.append(f"{name}: it has no water textures: only the meshes' water was drawn")
    else:
        notes.append(f"{name}: its water depth scale couldn't be read: its water textures were left as they are")
    road_raw = {m: read(m) for m in ROAD_MEMBERS}
    roads, said = road_model_on({m: v for m, v in road_raw.items() if v is not None}, near_back)
    out.update(roads)
    notes += [f"{name}: {line}" for line in said]
    return out, notes
