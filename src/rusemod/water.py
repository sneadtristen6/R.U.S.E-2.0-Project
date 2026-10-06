"""Water that follows the terrain editor (docs/MOD_FORMAT.md §8): the water brushes on the drawn ground, and the
water pictures the game's water reads, kept in step with it by the rules every shipped map follows.

Only what changed is rewritten, so the game's own shading stays everywhere else; a dry place that gains water gets a
picture of its own, and the shared dry and sea pictures are never edited."""
from __future__ import annotations

import struct

from .tms import Q_MAX, Tms
from .tmst import Tgv, make_tgv, zipo_pack, zipo_unpack

CASE = 1310720 / 48          # world units per water cell, the same on every map
TILE = 16                    # texels per tile side
SHADE = 16                   # still water at the base level shares a tile per this many steps of depth (R, 0..255)
SAMPLES = 4                  # samples per texel side (shores fade over about a texel, as in the shipped maps)
TEXTURES = {"indirection": "output\\riverindirectionsurface.tgv_pc", "inputs": "output\\waterinputs.tgv_pc",
            "flow": "output\\wateracceleration.tgv_pc"}


def _ground(mesh: Tms, boxes: list[tuple[float, float, float, float]], bucket: float = 8192.0):
    """(x, y) -> the mesh's ground height there (world units, inside its list-0 triangles), or None; only triangles
    that touch one of `boxes` (x min, x max, y min, y max) are indexed."""
    grid: dict[tuple[int, int], list] = {}
    for c in mesh.cells:
        pos, tri = c.positions(), c.triangles(0)
        for t in range(0, len(tri), 3):
            p = [(mesh.to_world(0, pos[v][0]), mesh.to_world(1, pos[v][1]), mesh.to_world(2, pos[v][2]))
                 for v in tri[t:t + 3]]
            x0, x1 = min(q[0] for q in p), max(q[0] for q in p)
            y0, y1 = min(q[1] for q in p), max(q[1] for q in p)
            if not any(x1 >= a and x0 <= b and y1 >= c and y0 <= d for a, b, c, d in boxes):
                continue
            for gx in range(int(x0 // bucket), int(x1 // bucket) + 1):
                for gy in range(int(y0 // bucket), int(y1 // bucket) + 1):
                    grid.setdefault((gx, gy), []).append(p)

    def at(x: float, y: float):
        for a, b, c in grid.get((int(x // bucket), int(y // bucket)), ()):
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if den == 0:
                continue
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
            l3 = 1.0 - l1 - l2
            if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                return l1 * a[2] + l2 * b[2] + l3 * c[2]
        return None
    return at


def apply_water(meshes: dict[str, Tms], strokes: list) -> list[str]:
    """Set the water surface of the drawn meshes by the water brushes, in order: `water` sets the level inside its
    circle, `drain` puts the map's base level back. The far mesh gets every level 150-ish units lower, by the
    difference between the two meshes' base levels, and floods only where the close-up mesh's ground is under the
    level: its triangles are much bigger, so otherwise a lake spreads over the ground around it in the far view
    (seen in the game, 2026-09-29). Points on the map's outer edge take the level like the rest, and the water's side
    hanging from the edge follows (Tms._fit_skirt): left at an old river's level, they stood as walls of water round
    the sea of Blank Ocean (seen in the game, 2026-10-05; gone with this the same day)."""
    water = [s for s in strokes if s.brush in ("water", "drain")]
    if not water or not meshes:
        return []
    base = {key: m.base_water() for key, m in meshes.items()}
    world_base = {key: m.to_world(2, base[key]) for key, m in meshes.items()}
    ref_key = "highdef" if "highdef" in meshes else next(iter(meshes))
    ref = world_base[ref_key]
    ground = None
    if len(meshes) > 1 and any(s.brush == "water" for s in water):
        ground = _ground(meshes[ref_key], [s.box() for s in water if s.brush == "water"])
    notes = []
    for key, m in meshes.items():
        offset = ref - world_base[key]
        changed = 0
        for k, c in enumerate(m.cells):
            levels = {}
            for i, (qx, qy, _qz, _qw) in enumerate(c.positions()):
                x, y = m.to_world(0, qx), m.to_world(1, qy)
                for s in water:
                    if not s.covers(x, y):
                        continue
                    if s.brush == "drain":
                        levels[i] = base[key]
                    elif key == ref_key:
                        levels[i] = m.to_quant(2, s.level)
                    else:
                        z = ground(x, y) if ground else None
                        if z is not None and z < s.level:
                            levels[i] = m.to_quant(2, s.level - offset)
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


def _water_triangles(tms: Tms, cases: tuple[int, int]) -> dict:
    """Every water triangle of the mesh, bucketed per water cell (`cases`: the map's cells across and down):
    (corners in world x, y; depth w - z and water level w per corner in world units)."""
    across, down = cases
    step = (tms.bounds[5] - tms.bounds[2]) / 32767
    (x0, y0, z0, x1, y1, z1), q = tms.bounds, Q_MAX   # Tms.to_world's sums, the bounds looked up once
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    out: dict[tuple[int, int], list] = {}
    for c in tms.cells:
        tri = c.triangles(1)
        if not tri:
            continue
        pos = c.positions()
        used = set(tri)   # each corner's world x, y, depth and level, worked out once
        where = {v: (x0 + pos[v][0] * sx / q, y0 + pos[v][1] * sy / q) for v in used}
        dep = {v: (pos[v][3] - pos[v][2]) * step for v in used}
        lvl = {v: z0 + pos[v][3] * sz / q for v in used}
        for t in range(0, len(tri), 3):
            a, b, d = tri[t], tri[t + 1], tri[t + 2]
            xy = [where[a], where[b], where[d]]
            entry = (xy, [dep[a], dep[b], dep[d]], [lvl[a], lvl[b], lvl[d]])
            ax, ay, bx, by, dx, dy = xy[0][0], xy[0][1], xy[1][0], xy[1][1], xy[2][0], xy[2][1]
            for cx in range(max(int(min(ax, bx, dx) // CASE), 0), min(int(max(ax, bx, dx) // CASE), across - 1) + 1):
                for cy in range(max(int(min(ay, by, dy) // CASE), 0), min(int(max(ay, by, dy) // CASE), down - 1) + 1):
                    out.setdefault((cx, cy), []).append(entry)
    return out


def _samples(tris: list, col: int, row: int, first: bool = False):
    """Which of one cell's 64 x 64 samples lie in a water triangle (the first that holds a sample gives it its depth
    and level). Returns (wet, depth, level) per sample, row by row, or None when no sample is wet; `first`: True as
    soon as one sample is found (the rest isn't worked out)."""
    n = TILE * SAMPLES
    if not tris:
        return None
    h = CASE / n
    wet = [[False] * n for _ in range(n)]
    depth = level = None
    if not first:
        depth = [[0.0] * n for _ in range(n)]
        level = [[0.0] * n for _ in range(n)]
    x0, y0 = col * CASE, row * CASE
    xs = [x0 + (i + 0.5) * h for i in range(n)]   # the samples' x and y
    ys = [y0 + (j + 0.5) * h for j in range(n)]
    found = False
    for (a, b, c), d, w in tris:
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if den == 0:
            continue
        i0 = max(int((min(a[0], b[0], c[0]) - x0) / h - 0.5), 0)
        i1 = min(int((max(a[0], b[0], c[0]) - x0) / h + 0.5), n - 1)
        j0 = max(int((min(a[1], b[1], c[1]) - y0) / h - 0.5), 0)
        j1 = min(int((max(a[1], b[1], c[1]) - y0) / h + 0.5), n - 1)
        # l1 = ((b.y - c.y) * (px - c.x) + (c.x - b.x) * (py - c.y)) / den, and l2 likewise: the same steps, with
        # what doesn't change along a row worked out once for it
        e1, f1, e2, f2, cx, cy = b[1] - c[1], c[0] - b[0], c[1] - a[1], a[0] - c[0], c[0], c[1]
        d0, d1, d2, w0, w1, w2 = d[0], d[1], d[2], w[0], w[1], w[2]
        for j in range(j0, j1 + 1):
            dy = ys[j] - cy
            g1, g2 = f1 * dy, f2 * dy
            wet_row = wet[j]
            for i in range(i0, i1 + 1):
                if wet_row[i]:
                    continue
                dx = xs[i] - cx
                l1 = (e1 * dx + g1) / den
                l2 = (e2 * dx + g2) / den
                l3 = 1.0 - l1 - l2
                if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                    if first:
                        return True
                    wet_row[i] = found = True
                    depth[j][i] = l1 * d0 + l2 * d1 + l3 * d2
                    level[j][i] = l1 * w0 + l2 * w1 + l3 * w2
    return (wet, depth, level) if found else None


def _wet(tris: list, col: int, row: int) -> bool:
    """Whether any sample of the cell lies in a water triangle (as _cell finds them)."""
    return _samples(tris, col, row, first=True) is not None


def _cell(tris: list, col: int, row: int, max_depth: float):
    """One cell's 16 x 16 texels: (R per texel, wet share per texel, mean water level of the wet samples).

    The sums are taken in the same order, with the same steps, as sample by sample over the whole cell; only what
    can't change them is skipped (a dry cell, a dry texel: R 0, share 0.0, level 0.0)."""
    got = _samples(tris, col, row)
    if got is None:
        return [0] * (TILE * TILE), [0.0] * (TILE * TILE), [0.0] * (TILE * TILE)
    wet, depth, level = got
    red, share, mean = [], [], []
    for ty in range(TILE):
        rows = range(ty * SAMPLES, ty * SAMPLES + SAMPLES)
        for tx in range(TILE):
            c0 = tx * SAMPLES
            if not any(True in wet[j][c0:c0 + SAMPLES] for j in rows):
                red.append(0)
                share.append(0.0)
                mean.append(0.0)
                continue
            r = k = 0
            lv = 0.0
            for j in rows:
                wet_row, depth_row, level_row = wet[j], depth[j], level[j]
                for i in range(c0, c0 + SAMPLES):
                    if wet_row[i]:
                        k += 1
                        lv += level_row[i]
                        v = depth_row[i] / max_depth   # 255 x v held to 0..1, as min(max(v, 0.0), 1.0) holds it
                        if v < 0.0:
                            v = 0.0
                        if v > 1.0:
                            v = 1.0
                        r += 255.0 * v
            red.append(int(r / (SAMPLES * SAMPLES) + 0.5))
            share.append(k / (SAMPLES * SAMPLES))
            mean.append(lv / k if k else 0.0)
    return red, share, mean


def _both(near: tuple, far: tuple | None, far_offset: float = 0.0) -> tuple[list, list, list]:
    """One cell's texels from the close-up mesh, with the far mesh's water where the close-up mesh has none (the game
    draws the far mesh from a distance, and water drawn over a texel that says "dry" comes out dark and flat, seen in
    the game 2026-09-29; its levels are raised by `far_offset` to the close-up mesh's scale); then one texel of spill
    onto the shore, as in the shipped textures."""
    red, share, mean = (list(v) for v in near)
    if far is not None:
        for i in range(TILE * TILE):
            if not share[i] and far[1][i]:
                red[i], share[i], mean[i] = far[0][i], far[1][i], far[2][i] + far_offset
    spill = list(red)
    if not any(share):
        return spill, share, mean     # no wet texel: nothing spills
    for i in range(TILE * TILE):
        if share[i]:
            continue
        x, y = i % TILE, i // TILE
        around = [red[yy * TILE + xx] for yy in range(max(y - 1, 0), min(y + 2, TILE))
                  for xx in range(max(x - 1, 0), min(x + 2, TILE)) if share[yy * TILE + xx]]
        if around:
            spill[i] = max(around)
    return spill, share, mean


def _texels(job: tuple, max_depth: float, off: float) -> tuple:
    """One cell's texels now and before, from its water triangles now and before (`job`: col, row, close-up now, far
    now, close-up before, far before; the far ones None without a far mesh): (red, share, mean, before), `before` =
    (red, share, mean) as they were, or None when the cell is dry now and had water before (it changed then: a texel
    that had any water has a share of 1/16 or more, 0 now; the rest of before isn't needed)."""
    cx, cy, near, far, near0, far0 = job
    TT = TILE * TILE

    def merged(close, far_tris):
        """_both of the close-up and far texels; the far ones aren't worked out when every texel has close-up water
        (_both takes the far mesh's only where the close-up mesh has none)."""
        got = _cell(close, cx, cy, max_depth)
        if far_tris is None or all(got[1]):
            return _both(got, None, off)
        return _both(got, _cell(far_tris, cx, cy, max_depth), off)
    red, share, mean = merged(near, far)
    if any(share):
        old = merged(near0, far0)
    elif _wet(near0, cx, cy) or (far0 is not None and _wet(far0, cx, cy)):
        old = None
    else:             # dry before too: every texel was 0, as now
        old = [0] * TT, [0.0] * TT, [0.0] * TT
    return red, share, mean, old


# --- the cells' texels shared out to worker programs, one per core but one (each answer is the same as one program's;
# as rusemod.mend shares out the riverbeds) ---
SHARE_FROM = 256   # cells with water now, at least, before the work is shared out: each takes a few thousandths of a
                   # second, and the worker programs about a second to start
_WORK: dict = {}   # in a worker: what its jobs share (set by its starter)


def _start_texels(max_depth: float, off: float) -> None:
    _WORK["max_depth"], _WORK["off"] = max_depth, off


def _texels_job(jobs: list) -> list:
    return [_texels(job, _WORK["max_depth"], _WORK["off"]) for job in jobs]


def _pool(start, args, workers: int):
    from concurrent.futures import ProcessPoolExecutor
    return ProcessPoolExecutor(max_workers=workers, initializer=start, initargs=args)


def _all_texels(jobs: list, max_depth: float, off: float, workers: int) -> tuple[list, str | None]:
    """_texels for every job, in the jobs' order, and why the worker programs couldn't do their share (None when they
    did, or weren't needed). The cells with water now (most of the work) go to `workers` programs, every n-th to each,
    while this program does the dry ones."""
    heavy = [k for k, job in enumerate(jobs) if job[2] or job[3]]
    done: list = [None] * len(jobs)
    alone = None
    if workers > 1 and len(heavy) >= SHARE_FROM:
        n = min(workers, len(heavy))
        batches = [heavy[k::n] for k in range(n)]
        try:
            with _pool(_start_texels, (max_depth, off), n) as pool:
                got = pool.map(_texels_job, [[jobs[k] for k in batch] for batch in batches])
                shared = set(heavy)
                for k, job in enumerate(jobs):   # the dry ones here, while the workers do theirs
                    if k not in shared:
                        done[k] = _texels(job, max_depth, off)
                for batch, results in zip(batches, got):
                    for k, result in zip(batch, results):
                        done[k] = result
            return done, None
        except Exception as exc:  # noqa: BLE001 - workers that can't start: the same work in this program
            alone = f"{type(exc).__name__}: {exc}"
    return [_texels(job, max_depth, off) for job in jobs], alone


def _shade(red: list[int]) -> int:
    """The depth (R) a cell of still water all over shares a tile by: its texels' mean, to the nearest SHADE, 255 for
    the deepest; the shallowest keep their own (at least 1: 0 is a dry place's)."""
    mean = sum(red) / len(red)
    if mean > 255 - SHADE / 2:
        return 255
    shade = int(mean / SHADE + 0.5) * SHADE
    return shade if shade else max(1, int(mean + 0.5))


def update_textures(read, before: Tms, after: Tms, areas: list[tuple[float, float, float]], max_depth: float,
                    name: str = "the map", far_before: Tms | None = None,
                    far_after: Tms | None = None, workers: int | None = None) -> tuple[dict[str, bytes], list[str]]:
    """The three water textures for the edited close-up mesh `after` (`before` = the mesh as shipped; `far_before` /
    `far_after` the far mesh, whose water the textures must cover too), for every water cell within one cell of an
    edited area [(x, y, radius)]. Returns ({member: new bytes}, notes). The cells' texels are worked out by `workers`
    programs (default rusemod.mend.WORKERS) when many cells have water now, each answer the same as one program's."""
    raws = {key: read(member) for key, member in TEXTURES.items()}
    if any(v is None for v in raws.values()):
        return {}, [f"{name} has no water textures; only the meshes' water was changed"]
    (ti, ind), (tw, inp), (tf, flow) = (_pixels(raws[k]) for k in ("indirection", "inputs", "flow"))
    across = round((after.bounds[3] - after.bounds[0]) / CASE)
    down = round((after.bounds[4] - after.bounds[1]) / CASE)
    cases = (across, down)
    if across > ti.width or down > ti.height:
        return {}, [f"{name}: its water textures cover fewer cells than the map has; they were left as they are"]
    cols = tw.width // TILE  # a tile t is row t // cols, column t % cols of the atlas: (G, R) in the indirection
    ntiles = cols * (tw.height // TILE)

    def ipx(x, y):
        o = (y * ti.width + x) * 4
        return ind[o], ind[o + 1], ind[o + 2], ind[o + 3]

    def tile_of(g, r):
        return g * cols + r

    def gr(t):
        return t // cols, t % cols

    users: dict[int, int] = {}
    for cy in range(down):
        for cx in range(across):
            _b, g, r, _a = ipx(cx, cy)
            users[tile_of(g, r)] = users.get(tile_of(g, r), 0) + 1

    def texel(tex, width, t, x, y):
        return ((t // cols) * TILE + y) * width * 4 + ((t % cols) * TILE + x) * 4

    shared = [t for t in sorted(users, key=lambda t: (-users[t], t))[:2] if users[t] > 1]
    dry = next((t for t in shared if inp[texel(inp, tw.width, t, 8, 8) + 2] == 0), None)
    sea = next((t for t in shared if inp[texel(inp, tw.width, t, 8, 8) + 2] == 255), None)
    free = [t for t in range(ntiles) if t not in users       # unused, every byte 0 (a tile's row: 4 x TILE bytes)
            and not any(any(inp[o:o + 4 * TILE]) for o in (texel(inp, tw.width, t, 0, y) for y in range(TILE)))]
    base = after.to_world(2, after.base_water())
    step = (after.bounds[5] - after.bounds[2]) / 32767
    cells = set()
    for x, y, rad in areas:
        for cx in range(int((x - rad - CASE) // CASE), int((x + rad + CASE) // CASE) + 1):
            for cy in range(int((y - rad - CASE) // CASE), int((y + rad + CASE) // CASE) + 1):
                if 0 <= cx < across and 0 <= cy < down:
                    cells.add((cx, cy))
    new_tris, old_tris = _water_triangles(after, cases), _water_triangles(before, cases)
    far_new = _water_triangles(far_after, cases) if far_after is not None else None
    far_old = _water_triangles(far_before, cases) if far_before is not None else None
    off = base - far_after.to_world(2, far_after.base_water()) if far_after is not None else 0.0
    stats = {"updated": 0, "new tiles": 0, "dried": 0}
    alike: dict[int, int] = {}   # a depth (R, in SHADE steps) -> the shared tile made for it
    jobs = []
    for cx, cy in sorted(cells):
        near, near0 = new_tris.get((cx, cy), []), old_tris.get((cx, cy), [])
        far = far_new.get((cx, cy), []) if far_new is not None else None
        far0 = far_old.get((cx, cy), []) if far_old is not None else None
        if near == near0 and far == far0:
            continue                                  # the same water triangles as before: the same texels
        jobs.append((cx, cy, near, far, near0, far0))
    if workers is None:
        from .mend import WORKERS
        workers = WORKERS
    done, alone = _all_texels(jobs, max_depth, off, workers)
    for (cx, cy, *_lists), (red, share, mean, old) in zip(jobs, done):   # in the cells' order, as one program
        if old is not None:                           # (None: dry now, water before; it changed)
            red0, share0, mean0 = old
            changed = [abs(red[i] - red0[i]) > 2 or abs(share[i] - share0[i]) > 0.01
                       or abs(mean[i] - mean0[i]) > 2 * step for i in range(TILE * TILE)]
            if not any(changed):
                continue
        b, g, r, a = ipx(cx, cy)
        t = tile_of(g, r)
        o = (cy * ti.width + cx) * 4
        if not any(share):
            if dry is not None and t != dry:          # dry now: the shared dry tile, no flags
                users[t] -= 1
                users[dry] = users.get(dry, 0) + 1
                ind[o:o + 4] = bytes((0, *gr(dry), 0))
                stats["dried"] += 1
                stats["updated"] += 1
            continue
        wet_texels = [i for i in range(TILE * TILE) if share[i] >= 0.5]
        at_base = sum(1 for i in wet_texels if abs(mean[i] - base) < 2 * step)
        other = at_base <= len(wet_texels) / 2        # rivers and lakes: water not at the base level
        if len(wet_texels) == TILE * TILE and not other:
            # still water at the base level all over the cell: one tile shared by every such cell of about its
            # depth, as the shipped sea shares one (the sea's own for the deepest, one more per SHADE of depth): a
            # thin layer over a whole flattened map would otherwise want more tiles than the pictures hold
            shade = _shade(red)
            to = sea if sea is not None and shade == 255 else alike.get(shade)
            if to is None and free:
                to = alike[shade] = free.pop(0)
                for y in range(TILE):
                    for x in range(TILE):
                        do, fd = texel(inp, tw.width, to, x, y), texel(flow, tf.width, to, x, y)
                        inp[do:do + 4] = bytes((0, 0, shade, 0))
                        flow[fd:fd + 4] = bytes(4)
                users[to] = 0
                stats["new tiles"] += 1
            if to is not None:
                if t != to:
                    users[t] -= 1
                    users[to] = users.get(to, 0) + 1
                    ind[o:o + 4] = bytes((0, *gr(to), 0))
                    stats["updated"] += 1
                continue
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
        ind[o:o + 4] = bytes((255 if other else 0, *gr(t), 0))
        stats["updated"] += 1
    one_core = [f"{name}: the water textures were worked out on one core: the worker programs couldn't start "
                f"({alone})"] if alone else []
    if not stats["updated"]:
        return {}, one_core
    out = {TEXTURES["indirection"]: _repack(ti, ind), TEXTURES["inputs"]: _repack(tw, inp),
           TEXTURES["flow"]: _repack(tf, flow)}
    return out, [f"{name}: water textures: {stats['updated']} cell(s) updated, {stats['new tiles']} new tile(s), "
                 f"{stats['dried']} cell(s) dry again (depth scale {max_depth:g})"] + one_core


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
