"""Water that follows the terrain editor (PLAN.md §7 MT; docs/MOD_FORMAT.md §8): the water brushes on the drawn meshes,
and the three water textures the game's water shader reads, kept in step with the water triangles.

The rules are the ones every shipped map follows (private notes water-and-trees-2026-09-29; private/tools/check_water.py
checks them rule by rule):

  meshes    a vertex's 4th value w is the water surface over it; list 1 = the water triangles (Tms._water_lists);
            the far mesh's water sits about 150 world units below the close-up mesh's (each mesh's base level, the w
            most vertices carry, says by how much)
  textures  one water cell = 27,306.67 world units, one 16 x 16 tile per cell; rows run north to south
    riverindirectionsurface  per cell (B, G, R, A): (G, R) = the cell's tile (G * 32 + R); B = 255 when the cell's
                             water is NOT at the map's base level (rivers, lakes); A = 255 only on all-water cells at
                             the base level that use the shared all-sea tile; a dry cell uses the shared dry tile
    waterinputs              R = the water DEPTH: 255 * (w - z) / MaxDepthForSimulationDepthMap, capped at 255 (the
                             map's own value in map\\<name>\\mapwaterconstante: 1,000 on Blitz); G = foam; in a cell's
                             own tile B / A = the cell's column / row
    wateracceleration        G / R = the flow (128 = still water)

Only texels whose water changed are rewritten, so Eugen's own shading stays everywhere else. A dry cell that gains
water gets a free tile (all zero, used by no cell); the shared dry and sea tiles are never edited.
"""
from __future__ import annotations

import struct

from .tms import Tms
from .tmst import Tgv, make_tgv, zipo_pack, zipo_unpack

CASE = 1310720 / 48          # world units per water cell, the same on every map
TILE = 16                    # texels per tile side
SAMPLES = 4                  # samples per texel side (shores fade over about a texel, as in the shipped maps)
TEXTURES = {"indirection": "output\\riverindirectionsurface.tgv_pc", "inputs": "output\\waterinputs.tgv_pc",
            "flow": "output\\wateracceleration.tgv_pc"}


def apply_water(meshes: dict[str, Tms], strokes: list) -> list[str]:
    """Set the water surface of the drawn meshes by the water brushes, in order: `water` sets the level inside its
    circle, `drain` puts the map's base level back. The far mesh gets every level 150-ish units lower, by the
    difference between the two meshes' base levels. Points on the map's outer edge are left alone."""
    water = [s for s in strokes if s.brush in ("water", "drain")]
    if not water or not meshes:
        return []
    base = {key: m.base_water() for key, m in meshes.items()}
    world_base = {key: m.to_world(2, base[key]) for key, m in meshes.items()}
    ref = world_base.get("highdef", next(iter(world_base.values())))
    notes = []
    for key, m in meshes.items():
        offset = ref - world_base[key]
        changed = 0
        top = 32767
        for k, c in enumerate(m.cells):
            levels = {}
            for i, (qx, qy, _qz, _qw) in enumerate(c.positions()):
                if qx in (0, top) or qy in (0, top):
                    continue
                x, y = m.to_world(0, qx), m.to_world(1, qy)
                for s in water:
                    if s.covers(x, y):
                        levels[i] = base[key] if s.brush == "drain" else m.to_quant(2, s.level - offset)
            if levels:
                changed += m.set_water(k, levels)
        notes.append(f"{key}: water level changed at {changed} point(s)" + (f" (far mesh {offset:.0f} lower)" if offset else ""))
    return notes


def _pixels(raw: bytes) -> tuple[Tgv, bytearray]:
    t = Tgv(raw)
    if not t.format.startswith("A8R8G8B8") or len(t.mips) != 1 or t.codec != "ZIPO":
        raise ValueError(f"unexpected water texture ({t.format}, {len(t.mips)} mips, {t.codec})")
    return t, bytearray(zipo_unpack(t.payload(0)))


def _repack(t: Tgv, px: bytearray) -> bytes:
    return make_tgv(t.width, t.height, t.format, [zipo_pack(bytes(px))])


def _water_triangles(tms: Tms, cases: int) -> dict:
    """Every water triangle of the mesh, bucketed per water cell: (corners in world x, y; depth w - z and water
    level w per corner in world units)."""
    step = (tms.bounds[5] - tms.bounds[2]) / 32767
    out: dict[tuple[int, int], list] = {}
    for c in tms.cells:
        tri = c.triangles(1)
        if not tri:
            continue
        pos = c.positions()
        for t in range(0, len(tri), 3):
            v = [pos[tri[t + j]] for j in range(3)]
            xy = [(tms.to_world(0, p[0]), tms.to_world(1, p[1])) for p in v]
            dep = [(p[3] - p[2]) * step for p in v]
            lvl = [tms.to_world(2, p[3]) for p in v]
            xs, ys = [q[0] for q in xy], [q[1] for q in xy]
            for cx in range(max(int(min(xs) // CASE), 0), min(int(max(xs) // CASE), cases - 1) + 1):
                for cy in range(max(int(min(ys) // CASE), 0), min(int(max(ys) // CASE), cases - 1) + 1):
                    out.setdefault((cx, cy), []).append((xy, dep, lvl))
    return out


def _cell(tris: list, col: int, row: int, max_depth: float):
    """One cell's 16 x 16 texels: (R per texel, wet share per texel, mean water level of the wet samples)."""
    n = TILE * SAMPLES
    h = CASE / n
    depth = [[0.0] * n for _ in range(n)]
    level = [[0.0] * n for _ in range(n)]
    wet = [[False] * n for _ in range(n)]
    x0, y0 = col * CASE, row * CASE
    for (a, b, c), d, w in tris:
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if den == 0:
            continue
        i0 = max(int((min(a[0], b[0], c[0]) - x0) / h - 0.5), 0)
        i1 = min(int((max(a[0], b[0], c[0]) - x0) / h + 0.5), n - 1)
        j0 = max(int((min(a[1], b[1], c[1]) - y0) / h - 0.5), 0)
        j1 = min(int((max(a[1], b[1], c[1]) - y0) / h + 0.5), n - 1)
        for j in range(j0, j1 + 1):
            py = y0 + (j + 0.5) * h
            for i in range(i0, i1 + 1):
                if wet[j][i]:
                    continue
                px = x0 + (i + 0.5) * h
                l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
                l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
                l3 = 1.0 - l1 - l2
                if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                    wet[j][i] = True
                    depth[j][i] = l1 * d[0] + l2 * d[1] + l3 * d[2]
                    level[j][i] = l1 * w[0] + l2 * w[1] + l3 * w[2]
    red, share, mean = [], [], []
    for ty in range(TILE):
        for tx in range(TILE):
            r = k = 0
            lv = 0.0
            for j in range(ty * SAMPLES, ty * SAMPLES + SAMPLES):
                for i in range(tx * SAMPLES, tx * SAMPLES + SAMPLES):
                    if wet[j][i]:
                        k += 1
                        lv += level[j][i]
                        r += 255.0 * min(max(depth[j][i] / max_depth, 0.0), 1.0)
            red.append(int(r / (SAMPLES * SAMPLES) + 0.5))
            share.append(k / (SAMPLES * SAMPLES))
            mean.append(lv / k if k else 0.0)
    return red, share, mean


def update_textures(read, before: Tms, after: Tms, areas: list[tuple[float, float, float]], max_depth: float,
                    name: str = "the map") -> tuple[dict[str, bytes], list[str]]:
    """The three water textures for the edited close-up mesh `after` (`before` = the mesh as shipped), for every
    water cell within one cell of an edited area [(x, y, radius)]. Returns ({member: new bytes}, notes)."""
    raws = {key: read(member) for key, member in TEXTURES.items()}
    if any(v is None for v in raws.values()):
        return {}, [f"{name} has no water textures; only the meshes' water was changed"]
    (ti, ind), (tw, inp), (tf, flow) = (_pixels(raws[k]) for k in ("indirection", "inputs", "flow"))
    cases = round((after.bounds[3] - after.bounds[0]) / CASE)
    if cases > ti.width or cases > ti.height:
        return {}, [f"{name}: its water textures cover fewer cells than the map has; they were left as they are"]
    cols = tw.width // TILE
    ntiles = cols * (tw.height // TILE)

    def ipx(x, y):
        o = (y * ti.width + x) * 4
        return ind[o], ind[o + 1], ind[o + 2], ind[o + 3]

    users: dict[int, int] = {}
    for cy in range(cases):
        for cx in range(cases):
            _b, g, r, _a = ipx(cx, cy)
            users[g * 32 + r] = users.get(g * 32 + r, 0) + 1

    def texel(tex, width, t, x, y):
        return ((t // cols) * TILE + y) * width * 4 + ((t % cols) * TILE + x) * 4

    shared = [t for t in sorted(users, key=lambda t: (-users[t], t))[:2] if users[t] > 1]
    dry = next((t for t in shared if inp[texel(inp, tw.width, t, 8, 8) + 2] == 0), None)
    sea = next((t for t in shared if inp[texel(inp, tw.width, t, 8, 8) + 2] == 255), None)
    free = [t for t in range(ntiles) if t not in users
            and not any(inp[texel(inp, tw.width, t, x, y) + ch] for y in range(TILE) for x in range(TILE) for ch in range(4))]
    base = after.to_world(2, after.base_water())
    step = (after.bounds[5] - after.bounds[2]) / 32767
    cells = set()
    for x, y, rad in areas:
        for cx in range(int((x - rad - CASE) // CASE), int((x + rad + CASE) // CASE) + 1):
            for cy in range(int((y - rad - CASE) // CASE), int((y + rad + CASE) // CASE) + 1):
                if 0 <= cx < cases and 0 <= cy < cases:
                    cells.add((cx, cy))
    new_tris, old_tris = _water_triangles(after, cases), _water_triangles(before, cases)
    stats = {"updated": 0, "new tiles": 0, "dried": 0}
    for cx, cy in sorted(cells):
        red, share, mean = _cell(new_tris.get((cx, cy), []), cx, cy, max_depth)
        red0, share0, mean0 = _cell(old_tris.get((cx, cy), []), cx, cy, max_depth)
        changed = [abs(red[i] - red0[i]) > 2 or abs(share[i] - share0[i]) > 0.01 or abs(mean[i] - mean0[i]) > 2 * step
                   for i in range(TILE * TILE)]
        if not any(changed):
            continue
        b, g, r, a = ipx(cx, cy)
        t = g * 32 + r
        o = (cy * ti.width + cx) * 4
        if not any(share):
            if dry is not None and t != dry:          # dry now: the shared dry tile, no flags
                users[t] -= 1
                users[dry] = users.get(dry, 0) + 1
                ind[o:o + 4] = bytes((0, dry // 32, dry % 32, 0))
                stats["dried"] += 1
                stats["updated"] += 1
            continue
        wet_texels = [i for i in range(TILE * TILE) if share[i] >= 0.5]
        at_base = sum(1 for i in wet_texels if abs(mean[i] - base) < 2 * step)
        other = at_base <= len(wet_texels) / 2        # rivers and lakes: water not at the base level
        if t == sea and len(wet_texels) == TILE * TILE and not other:
            continue                                  # still open sea at the base level: the shared sea tile stays
        if users.get(t, 0) > 1 or t in (dry, sea):
            if not free:
                raise ValueError(f"{name}: no free water tile is left for the cell at ({cx}, {cy})")
            nt = free.pop(0)
            for y in range(TILE):
                for x in range(TILE):
                    so, do = texel(inp, tw.width, t, x, y), texel(inp, tw.width, nt, x, y)
                    fo, fd = texel(flow, tf.width, t, x, y), texel(flow, tf.width, nt, x, y)
                    if t == dry:                      # a dry cell gains water: no foam, still water
                        inp[do:do + 4] = bytes((cx, 0, 0, cy))
                        flow[fd:fd + 4] = bytes((0, 128, 128, 0))
                    else:
                        inp[do:do + 4] = bytes((cx, inp[so + 1], inp[so + 2], cy))
                        flow[fd:fd + 4] = flow[fo:fo + 4]
            users[t] -= 1
            users[nt] = 1
            t = nt
            changed = [True] * (TILE * TILE)
            stats["new tiles"] += 1
        for i in range(TILE * TILE):
            if changed[i]:
                inp[texel(inp, tw.width, t, i % TILE, i // TILE) + 2] = red[i]
        ind[o:o + 4] = bytes((255 if other else 0, t // 32, t % 32, 0))
        stats["updated"] += 1
    if not stats["updated"]:
        return {}, []
    out = {TEXTURES["indirection"]: _repack(ti, ind), TEXTURES["inputs"]: _repack(tw, inp),
           TEXTURES["flow"]: _repack(tf, flow)}
    return out, [f"{name}: water textures: {stats['updated']} cell(s) updated, {stats['new tiles']} new tile(s), "
                 f"{stats['dried']} cell(s) dry again (depth scale {max_depth:g})"]


def max_depth(read_ndf) -> float | None:
    """MaxDepthForSimulationDepthMap from a map's mapwaterconstante NDF (`read_ndf()` gives an rusemod.ndf.Ndf or
    None)."""
    nd = read_ndf()
    if nd is None:
        return None
    names = [n for n, _ in nd.props]
    for o in nd.objects:
        for pi, v in o.props:
            if names[pi] == "MaxDepthForSimulationDepthMap":
                return struct.unpack("<f", v.payload)[0]
    return None
