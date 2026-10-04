r"""Check terrain edits (rusemod.terrain_edit) on every map, and make the in-game hill test (PLAN.md §7 MT, T2).

Without --make-test (READ-ONLY on the game): on every Maps\PC\DataMap*_v09.dat a test hill goes, in memory, on the
dry land nearest the middle of the map, and the four ground files are checked:
  A. all four change and read back,
  B. in the gameplay ground and the close-up mesh, the point nearest the hill's centre rose by what the brush says,
     to within the file's height step (the far mesh and the camera floor follow the gameplay ground's triangles),
  C. every gameplay-ground point still has the height of the close-up mesh point it sat on (same x, y and height;
     the mesh can hold several points at one x, y, a cliff's top and foot, so x and y alone don't say which),
  D. the gameplay ground's parts the hill doesn't reach keep their exact bytes,
  E. both .kdt files' trees hold the moved ground: every triangle a leaf lists touches the leaf's cell, and every
     moved part fits its MainNode region (stale limits made the game refuse move orders; rusemod.kdt_edit).
One line per map with the time it took, then a summary. Nothing is written.

With --edges (READ-ONLY too): on every map, (1) the whole ground flattened and (2) a hill on the middle of one edge;
after each, the map's edge in all four files and the close-up mesh's skirt are checked (see check_edges).

With --make-test MAP COPY: builds a modded copy of the game at COPY (never the Steam install) with that hill on MAP,
and next to it a pit (Lower) and a flattened patch (Level), through the same build as `ruse build` and the Studio's
"Test in game", and says where they are and what to look for in the game.

Usage:  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_terrain.py [game_dir] [--only Name] [--edges]
        py -3 tools\verify_terrain.py [game_dir] --make-test TwoIslands D:\RUSE-Instances\hill [--radius R] [--height H]
"""
import glob
import math
import os
import struct
import sys
import tempfile
import time
import zlib
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, kdt_edit  # noqa: E402
from rusemod.brush import Stroke, strokes_toml  # noqa: E402
from rusemod.kdt import Kdt  # noqa: E402
from rusemod.terrain_edit import FILES, LABELS, edit_map  # noqa: E402
from rusemod.tms import Q_MAX, SKIRT_BOTTOM, Tms  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
RADIUS_SHARE = 0.05    # the test hill's radius, as a share of the map's width
HEIGHT_SHARE = 0.8     # its height, as a share of the room between the ground there and the map's highest point


def reader(arc):
    def read(member):
        try:
            return bytes(arc.read(arc.find(member)))
        except KeyError:
            return None
    return read


def test_hill(hd: Tms, radius: float | None = None, height: float | None = None) -> Stroke:
    """The test hill: on the dry land (ground above its water) nearest the middle of the map."""
    b = hd.bounds
    cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
    best = None
    for cell in hd.cells:
        for qx, qy, qz, qw in cell.positions():
            if qz <= qw or qx in (0, Q_MAX) or qy in (0, Q_MAX):
                continue
            x, y = hd.to_world(0, qx), hd.to_world(1, qy)
            d = (x - cx) ** 2 + (y - cy) ** 2
            if best is None or d < best[0]:
                best = (d, x, y, hd.to_world(2, qz))
    if best is None:  # no dry land at all: the middle of the map
        best = (0.0, cx, cy, hd.to_world(2, 0))
    _d, x, y, z = best
    if radius is None:
        radius = RADIUS_SHARE * (b[3] - b[0])
    if height is None:
        height = HEIGHT_SHARE * (b[5] - z)
    return Stroke("hill", x, y, radius, height=height)


def _ground_at(hd: Tms, x: float, y: float) -> float:
    """The close-up mesh's height at the point nearest (x, y)."""
    best = None
    for cell in hd.cells:
        for qx, qy, qz, _qw in cell.positions():
            d = (hd.to_world(0, qx) - x) ** 2 + (hd.to_world(1, qy) - y) ** 2
            if best is None or d < best[0]:
                best = (d, hd.to_world(2, qz))
    return best[1]


def nearest(points, x, y):
    return min(points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)


def world_points_mesh(t: Tms):
    return [(t.to_world(0, p[0]), t.to_world(1, p[1]), t.to_world(2, p[2]), k, i)
            for k, c in enumerate(t.cells) for i, p in enumerate(c.positions())]


def world_points_tree(t: Kdt):
    return [(t.to_world(0, p[0]), t.to_world(1, p[1]), t.to_world(2, p[2]), s, i)
            for s in range(len(t.subtrees)) for i, p in enumerate(t.positions(s))]


def check(read, name: str) -> tuple[list[str], str]:
    """Problems (empty = OK) and a summary for one map."""
    problems = []
    raw = {key: read(member) for key, member in FILES.items()}
    if raw["highdef"] is None:
        return ["no close-up mesh"], ""
    hd = Tms(raw["highdef"])
    hill = test_hill(hd)
    t0 = time.time()
    changed, notes = edit_map(read, [hill], name)
    took = time.time() - t0
    # A
    for key, member in FILES.items():
        if raw[key] is not None and member not in changed:
            problems.append(f"the {LABELS[key]} didn't change")
    new = {}
    try:
        for member, data in changed.items():
            k = next(k for k, m in FILES.items() if m == member)
            new[k] = Tms(data) if k in ("highdef", "lowdef") else Kdt(data)
    except (ValueError, struct.error, zlib.error) as exc:
        return problems + [f"an edited file doesn't read back: {exc}"], ""
    # B
    for key, obj in new.items():
        if key not in ("highdef", "ground"):
            continue
        old = Tms(raw[key]) if key in ("highdef", "lowdef") else Kdt(raw[key])
        pts = world_points_mesh(old) if key in ("highdef", "lowdef") else world_points_tree(old)
        x, y, z, part, i = nearest([p for p in pts if hill.covers(p[0], p[1])] or pts, hill.x, hill.y)
        if key in ("highdef", "lowdef"):
            q = obj.cells[part].positions()[i][2]
            lo, hi = obj.bounds[2], obj.bounds[5]
        else:
            q = obj.positions(part)[i][2]
            lo, hi = obj.bounds_min[2], obj.bounds_max[2]
        want = min(max(hill.height_at(x, y, z), lo), hi)
        got = obj.to_world(2, q)
        step = (hi - lo) / Q_MAX
        if abs(got - want) > step:
            problems.append(f"the {LABELS[key]} rose to {got:.1f} at the hill's centre, not {want:.1f}")
    # C: the close-up mesh can hold several points at one x, y at different heights (a cliff's top and foot: every
    # shipped mesh has hundreds), so each gameplay-ground point is matched, before the edit, to the mesh point it
    # sits on (same quantized x, y and height; all 32 shipped maps: every ground point has one) and must have that
    # point's height after it, exactly
    if "ground" in new and "highdef" in new:
        g, h = new["ground"], new["highdef"]
        if tuple(g.bounds_min) == tuple(h.bounds[:3]) and tuple(g.bounds_max) == tuple(h.bounds[3:]):
            after: dict[tuple, set] = {}   # close-up mesh point (x, y, height before) -> its heights after
            for a, b in zip(Tms(raw["highdef"]).cells, h.cells):
                for p, q in zip(a.positions(), b.positions()):
                    after.setdefault(p[:3], set()).add(q[2])
            old_g = Kdt(raw["ground"])
            off = lost = 0
            for s in range(len(g.subtrees)):
                for p, q in zip(old_g.positions(s), g.positions(s)):
                    heights = after.get(p)
                    if heights is None:
                        lost += 1
                    elif heights != {q[2]}:
                        off += 1
            if off:
                problems.append(f"{off} gameplay-ground point(s) differ from the close-up mesh")
            if lost:
                problems.append(f"{lost} gameplay-ground point(s) sit on no close-up mesh point (before the edit)")
    # D: the gameplay ground (the other files follow its triangles, which can reach past the hill's circle)
    for key in ("ground",):
        if key in new:
            old = Kdt(raw[key])
            for s, (a, b) in enumerate(zip(old.subtrees, new[key].subtrees)):
                reach = any(hill.covers(old.to_world(0, p[0]), old.to_world(1, p[1])) for p in old.positions(s))
                if not reach and a.positions != b.positions:
                    problems.append(f"{LABELS[key]} part {s} changed though the hill doesn't reach it")
    # E
    for key in ("ground", "camera"):
        if key in new:
            old = Kdt(raw[key])
            moved = [s for s in range(len(old.subtrees)) if old.subtrees[s].positions != new[key].subtrees[s].positions]
            bad = [m for s in moved for m in kdt_edit.check(new[key], s)] + kdt_edit.check_main(new[key], moved)
            if bad:
                problems.append(f"{LABELS[key]}: {len(bad)} tree problem(s), e.g. {bad[0]}")
    fitted = "; ".join(n.split(": ", 1)[1] for n in notes if "part(s) widened" in n)
    summary = (f"hill at ({hill.x:.0f}, {hill.y:.0f}), radius {hill.radius:.0f}, height {hill.height:.0f}; "
               f"{notes[0].split(': ', 1)[1]}; {fitted}; {took:.1f} s")
    return problems, summary


class _Heights:
    """A .kdt's surface height at any x, y: barycentric in its triangles; beyond its box, the nearest edge point's."""

    def __init__(self, k: Kdt):
        self.x0, self.y0, self.x1, self.y1 = k.bounds_min[0], k.bounds_min[1], k.bounds_max[0], k.bounds_max[1]
        self.step = max(self.x1 - self.x0, self.y1 - self.y0, 1.0) / 256.0
        self.tris, self.buckets = [], {}
        for s in range(len(k.subtrees)):
            idx = k.indices(s)
            w = [(k.to_world(0, p[0]), k.to_world(1, p[1]), k.to_world(2, p[2])) for p in k.positions(s)]
            for t in range(0, len(idx), 3):
                tri = (w[idx[t]], w[idx[t + 1]], w[idx[t + 2]])
                xs, ys = [c[0] for c in tri], [c[1] for c in tri]
                for bx in range(self._b(min(xs), self.x0), self._b(max(xs), self.x0) + 1):
                    for by in range(self._b(min(ys), self.y0), self._b(max(ys), self.y0) + 1):
                        self.buckets.setdefault((bx, by), []).append(len(self.tris))
                self.tris.append(tri)

    def _b(self, v: float, origin: float) -> int:
        return int((v - origin) // self.step)

    def at(self, x: float, y: float) -> tuple[float, int] | tuple[None, None]:
        """(height, the triangle's number), or (None, None) off every triangle."""
        x, y = min(max(x, self.x0), self.x1), min(max(y, self.y0), self.y1)
        for n in self.buckets.get((self._b(x, self.x0), self._b(y, self.y0)), ()):
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = self.tris[n]
            det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if not det:
                continue
            l0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / det
            l1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / det
            if min(l0, l1, 1.0 - l0 - l1) >= -1e-9:
                return l0 * z0 + l1 * z1 + (1.0 - l0 - l1) * z2, n
        return None, None


def _skirt(t: Tms) -> dict:
    """The skirt read back from its bytes (layout in rusemod.tms): {submesh: (index bytes, vertices, bounds, parts)}
    for the submeshes present."""
    out, pos = {}, 0
    for m in range(2):
        ib, vb, bb, pb = struct.unpack_from("<4I", t.skirt, 4 + 16 * m)
        if vb:
            data = t.skirt_data
            out[m] = (data[pos:pos + ib], [struct.unpack_from("<4H", data, pos + ib + 8 * j) for j in range(vb // 8)],
                      [data[pos + ib + vb + 24 * k:pos + ib + vb + 24 * k + 24] for k in range(bb // 24)],
                      [struct.unpack_from("<4I", data, pos + ib + vb + bb + 16 * k) for k in range(pb // 16)])
        pos += ib + vb + bb + pb
    return out


def _edge_heights(t: Tms) -> dict:
    """The top height (quantized) at every x, y of the close-up mesh's outer edge."""
    out = {}
    for c in t.cells:
        for x, y, z, _w in c.positions():
            if x in (0, Q_MAX) or y in (0, Q_MAX):
                out[(x, y)] = max(out.get((x, y), z), z)
    return out


def _f32(v: float) -> float:
    return struct.unpack("<f", struct.pack("<f", v))[0]


def _skirt_problems(old: Tms, new: Tms) -> tuple[list[str], dict]:
    """The skirt against the edge's new heights: the curtain's tops at the edge's new height (its scale SKIRT_BOTTOM
    to the file's top), the feet at q 0; the water's side with its foot on the ground and its top at the water or flat
    on the ground; parts with a moved vertex have height bounds that fit them; anything under an unmoved edge point
    keeps its value; the indices, parts and x, y never change."""
    problems, counts = [], {"columns moved": 0, "curtain tops moved": 0, "water side vertices moved": 0}
    if old.skirt != new.skirt:
        return ["the skirt's descriptor changed"], counts
    before, after = _edge_heights(old), _edge_heights(new)
    cols = {xy for xy in after if after[xy] != before[xy]}
    counts["columns moved"] = len(cols)
    # the water side's points between the edge's own (where its surface meets the bank) follow the edge there, from
    # the edge points either side along the same edge
    edges = {}
    for (x, y), z in after.items():
        for side, along in (((0, x),) if y == 0 else ()) + (((1, y),) if x == 0 else ()) + \
                (((2, y),) if x == Q_MAX else ()) + (((3, x),) if y == Q_MAX else ()):
            edges.setdefault(side, []).append((along, before[(x, y)], z))
    for profile in edges.values():
        profile.sort()

    def between(x, y):
        side, along = (0, x) if y == 0 else (3, x) if y == Q_MAX else (1, y) if x == 0 else (2, y)
        profile = edges.get(side, [])
        for (a0, b0, z0), (a1, b1, z1) in zip(profile, profile[1:]):
            if a0 < along < a1:
                t = (along - a0) / (a1 - a0)
                return round(b0 + (b1 - b0) * t), round(z0 + (z1 - z0) * t)
        return None
    scale = (new.bounds[5] - SKIRT_BOTTOM) / Q_MAX
    sk_old, sk_new = _skirt(old), _skirt(new)
    for m, (idx, verts, bounds, parts) in sk_new.items():
        o_idx, o_verts, o_bounds, o_parts = sk_old[m]
        if (idx, parts, [v[:2] for v in verts]) != (o_idx, o_parts, [v[:2] for v in o_verts]):
            problems.append(f"submesh {m + 1}: its indices, parts or x, y changed")
            continue
        foot = {}
        for x, y, z, _w in o_verts:
            foot[(x, y)] = min(foot.get((x, y), z), z)
        bad = 0
        for (x, y, z, _w), (_x, _y, oz, _ow) in zip(verts, o_verts):
            if (x, y) in after:
                height = after[(x, y)] if (x, y) in cols else None
            else:
                pair = between(x, y)
                height = pair[1] if pair and pair[0] != pair[1] else None
            if height is None:
                want = oz
            elif m == 0:
                want = 0 if oz == 0 else min(max(round((new.to_world(2, height) - SKIRT_BOTTOM) / scale), 1), Q_MAX)
            else:
                want = height if oz == foot[(x, y)] else max(oz, height)
            bad += z != want
            if z != oz:
                counts["curtain tops moved" if m == 0 else "water side vertices moved"] += 1
        if bad:
            problems.append(f"submesh {m + 1}: {bad} vertex height(s) not where the edge says")
        for k, (vstart, vcount, _i, _n) in enumerate(parts):
            run, o_run = verts[vstart:vstart + vcount], o_verts[vstart:vstart + vcount]
            b, ob = struct.unpack("<6f", bounds[k]), struct.unpack("<6f", o_bounds[k])
            if run == o_run:
                if bounds[k] != o_bounds[k]:
                    problems.append(f"submesh {m + 1} part {k}: bounds changed though nothing in it moved")
                continue
            to_w = (lambda q: SKIRT_BOTTOM + q * scale) if m == 0 else (lambda q: new.to_world(2, q))
            want = (_f32(to_w(min(v[2] for v in run))), _f32(to_w(max(v[2] for v in run))))
            if b[:2] + b[3:5] != ob[:2] + ob[3:5] or (b[2], b[5]) != want:
                problems.append(f"submesh {m + 1} part {k}: bounds {[round(v, 1) for v in b]}, z should be {want}")
    return problems, counts


def check_edges(read, name: str) -> tuple[list[str], str]:
    """The map's edge after (1) the whole ground flattened (a plateau over the whole map at 40% of the close-up mesh's
    height range) and (2) a hill on the middle of the edge y = min: in the close-up mesh and the gameplay ground every
    edge point is where the brush says (to the file's height step); the far mesh's and the camera floor's points (the
    camera floor's ring beyond the edge too) moved by the gameplay ground's change under them, or beside them past the
    edge; the skirt follows the edge (_skirt_problems); both .kdt files' trees hold the moved ground; everything reads
    back. Problems (empty = OK) and a summary."""
    raw = {key: read(member) for key, member in FILES.items()}
    if raw["highdef"] is None or raw["ground"] is None:
        return ["no close-up mesh or gameplay ground"], ""
    hd = Tms(raw["highdef"])
    b = hd.bounds
    level = b[2] + 0.4 * (b[5] - b[2])
    diag = math.hypot(b[3] - b[0], b[4] - b[1])
    mid_x = (b[0] + b[3]) / 2
    radius = 0.1 * (b[3] - b[0])
    top = _ground_at(hd, mid_x, b[1])
    tests = [("flat", Stroke("plateau", mid_x, (b[1] + b[4]) / 2, 2 * diag, level=level)),
             ("edge hill", Stroke("hill", mid_x, b[1], radius, height=0.3 * (b[5] - top)))]
    problems, summary = [], []
    for label, stroke in tests:
        t0 = time.time()
        changed, notes = edit_map(read, [stroke], name)
        took = time.time() - t0
        new = {}
        try:
            for member, data in changed.items():
                k = next(k for k, m in FILES.items() if m == member)
                new[k] = Tms(data) if k in ("highdef", "lowdef") else Kdt(data)
        except (ValueError, struct.error, zlib.error) as exc:
            problems.append(f"{label}: an edited file doesn't read back: {exc}")
            continue
        old = {k: (Tms(raw[k]) if k in ("highdef", "lowdef") else Kdt(raw[k])) for k in new}
        g_old, g_new = _Heights(old["ground"]), _Heights(new["ground"])
        # the gameplay ground's points (quantized; its box is the close-up mesh's): a close-up point on one of them
        # gets the brush itself, any other follows the ground's change under it
        on_ground = {p for s in range(len(old["ground"].subtrees)) for p in old["ground"].positions(s)}
        moved_edge = {}
        for key, obj in new.items():
            o = old[key]
            if key in ("highdef", "lowdef"):
                pts = [(p, q) for a, c in zip(o.cells, obj.cells) for p, q in zip(a.positions(), c.positions())]
                lo, hi = obj.bounds[2], obj.bounds[5]
                on_edge = lambda p: p[0] in (0, Q_MAX) or p[1] in (0, Q_MAX)
            else:
                pts = [(p, q) for s in range(len(o.subtrees)) for p, q in zip(o.positions(s), obj.positions(s))]
                lo, hi = obj.bounds_min[2], obj.bounds_max[2]
                on_edge = lambda p: p[0] in (0, Q_MAX) or p[1] in (0, Q_MAX)
            step = (hi - lo) / Q_MAX
            bad = moved = 0
            for p, q in pts:
                if not on_edge(p):
                    continue
                x, y, z = (o.to_world(a, p[a]) for a in range(3))
                if key == "ground" or (key == "highdef" and tuple(p[:3]) in on_ground):
                    want = min(max(stroke.height_at(x, y, z), lo), hi) if stroke.covers(x, y) else z
                else:
                    (gz0, t0), (gz1, _t1) = g_old.at(x, y), g_new.at(x, y)
                    if gz0 is None or gz1 is None:
                        want = None
                    else:
                        want = z + (gz1 - gz0)
                        # a drawn mesh's own offset off the ground goes as far as the brush flattens: every brush is
                        # new = old x kept + a target, so kept is the slope of its height in the old height
                        kept = (stroke.height_at(x, y, 1000.0) - stroke.height_at(x, y, 0.0)) / 1000.0
                        if key in ("highdef", "lowdef") and kept < 1.0 and g_old.tris[t0] != g_new.tris[t0]:
                            want -= (z - gz0) * (1.0 - kept)
                        want = min(max(want, lo), hi)
                if want is None:
                    bad += 1
                    continue
                got = obj.to_world(2, q[2])
                bad += abs(got - want) > step * 1.01 + 1e-6
                moved += q[2] != p[2]
            moved_edge[key] = moved
            if bad:
                problems.append(f"{label}: {LABELS[key]}: {bad} edge point(s) not where they should be")
        for key in ("ground", "camera"):
            if key in new:
                parts = [s for s in range(len(old[key].subtrees))
                         if old[key].subtrees[s].positions != new[key].subtrees[s].positions]
                tree_bad = [m for s in parts for m in kdt_edit.check(new[key], s)] + kdt_edit.check_main(new[key], parts)
                if tree_bad:
                    problems.append(f"{label}: {LABELS[key]}: {len(tree_bad)} tree problem(s), e.g. {tree_bad[0]}")
        if "highdef" in new:
            sk_problems, counts = _skirt_problems(old["highdef"], new["highdef"])
            problems += [f"{label}: {p}" for p in sk_problems]
        else:
            counts = {}
        summary.append(f"{label}: edge points moved " + ", ".join(f"{LABELS[k]} {n}" for k, n in moved_edge.items())
                       + "; skirt " + ", ".join(f"{k} {n}" for k, n in counts.items()) + f"; {took:.1f} s")
    return problems, " | ".join(summary)


def make_test(game: str, name: str, copy: str, radius=None, height=None) -> int:
    from rusemod.build import build_and_write, load_mod
    pack = os.path.join(game, "Maps", "PC", f"DataMap{name}_v09.dat")
    if not os.path.isfile(pack):
        print(f"{pack} doesn't exist")
        return 2
    with Edat.open(pack) as arc:
        hd = Tms(bytes(arc.read(arc.find(FILES["highdef"]))))
    hill = test_hill(hd, radius, height)
    b = hd.bounds
    # a pit three hill-widths east and a flattened patch three hill-widths west, if the map has room there
    gap = 3 * hill.radius
    pit_x = min(hill.x + gap, b[3] - hill.radius * 1.5)
    flat_x = max(hill.x - gap, b[0] + hill.radius * 1.5)
    strokes = [hill, Stroke("lower", pit_x, hill.y, hill.radius, height=hill.height * 0.5),
               Stroke("level", flat_x, hill.y, hill.radius, level=_ground_at(hd, flat_x, hill.y), weight=1.0)]
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp, "terrain-test")
        (mod / "maps" / name).mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "terrain-test"\nname = "Terrain test"\nversion = "0.2.0"\n',
                                      encoding="utf-8")
        (mod / "maps" / name / "terrain.toml").write_text(
            strokes_toml(strokes, "The in-game terrain test (tools/verify_terrain.py --make-test)."), encoding="utf-8")
        result = build_and_write(Path(game), [load_mod(mod)], instance=Path(copy), say=print)
    if result.errors:
        return 1
    east = (hill.x - b[0]) / (b[3] - b[0]) * 100
    south = (hill.y - b[1]) / (b[4] - b[1]) * 100
    print(f"""
The hill: {east:.0f}% of the way from the map's west edge and {south:.0f}% from its north edge (the dry land nearest
the middle), with a radius of {hill.radius:.0f} units and {hill.height:.0f} units high at its top. East of it a pit
half as deep, west of it a patch flattened to the ground's height there.
Start RUSE.exe in {copy} (Steam running), play a skirmish on this map and check, on all three:
  1. drawn close up and zoomed out, with no holes, steps or seams;
  2. move orders onto the hill, into the pit and onto the flat patch are taken, and units drive there;
  3. the camera stays above the ground when you fly over them (it doesn't speed up or drop through);
  4. trees and buildings on them stand on the new ground (not floating, not buried).
Screenshot each from the side, close and far.""")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def option(flag, cast=float):
        if flag in argv:
            i = argv.index(flag)
            value = cast(argv[i + 1])
            del argv[i:i + 2]
            return value
        return None

    only = option("--only", str)
    radius, height = option("--radius"), option("--height")
    edges = "--edges" in argv
    if edges:
        argv.remove("--edges")
    if "--make-test" in argv:
        i = argv.index("--make-test")
        name, copy = argv[i + 1], argv[i + 2]
        del argv[i:i + 3]
        return make_test(argv[0] if argv else DEFAULT_GAME, name, copy, radius, height)
    game = argv[0] if argv else DEFAULT_GAME
    paths = sorted(glob.glob(os.path.join(game, "Maps", "PC", "DataMap*_v09.dat")))
    if only:
        paths = [p for p in paths if os.path.basename(p) == f"DataMap{only}_v09.dat"]
    if not paths:
        print(f"no map packs found under {game}")
        return 2
    fails = 0
    for path in paths:
        name = os.path.basename(path)[7:-8]
        with Edat.open(path) as arc:
            try:
                problems, summary = (check_edges if edges else check)(reader(arc), name)
            except (ValueError, struct.error, zlib.error) as exc:
                problems, summary = [str(exc)], ""
        fails += bool(problems)
        print(f"{name:24s} {'OK' if not problems else 'FAIL: ' + '; '.join(problems[:3])}  {summary}", flush=True)
    print(f"\n{len(paths)} maps, {fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
