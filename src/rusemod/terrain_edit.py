"""Terrain edits on a map's ground (docs/MOD_FORMAT.md §8): brush strokes applied to the four forms a map's ground
takes, together: the close-up mesh the game draws, the far mesh, the ground units walk on, and the camera floor.

The gameplay ground leads (the recipe of DomesticNukes and his Claude, checked in the game on Blitz, 2026-09-28):
1. The strokes (rusemod.brush) move the gameplay ground's points only.
2. The other three files follow its surface: each of their points moves by the change of the gameplay ground's
   triangle under it (its corners' changes, weighted by where the point lies in it). The files don't share one
   set of triangles, so moving each by the brush itself left the drawn slope up to 1,700 units off the ground units
   stand on (units sank into it). A drawn mesh's point that isn't on the ground's surface (the far mesh is fitted
   on its own, up to 3,000 off it on Blitz; a cliff's foot) also loses that offset as far as the strokes flatten
   (rusemod.brush Stroke.kept: all of it across a plateau's middle, none under a hill), or a flattened map kept
   bumps where its mountains were. The camera floor keeps its offset: that's how high the camera stays.
3. Both .kdt files keep their trees true (rusemod.kdt_edit): the height limits over every moved triangle, and the
   MainNode's over every moved part, are widened (a part is rebuilt when a moved triangle crosses a height split).
   Stale limits made the game refuse move orders there and let the camera fall through.
4. Scenery is never lifted: the game stands it on the ground at load, through the drawn meshes' patch bounds, which
   rusemod.tms recomputes around moved points (stale bounds left trees at the old height).
Without a gameplay ground file, every stroke moves every file's points by itself, as before.

The map's outer edge moves like any other point: the curtain that hangs from the close-up mesh's edge follows it
(rusemod.tms; keeping the edge still left a wall of old mountain one point thick round a flattened map, the owner's
flat Blitz Twin, 2026-10-03), and the camera floor's ring beyond the edge (175,000 out, 20,999 under the floor at the
edge on every map) moves as the edge beside it. Heights stay inside each file's own
height range: a point pushed past the top or the bottom stops there, and the report says how many did. In the
meshes, the normals around moved points are recomputed (rusemod.tms); in the .kdt trees, a moved point takes the
normal of the nearest close-up mesh point (nearest in x, y, then in height: the close-up mesh can hold several points
at one x, y, a cliff's top and foot, and a gameplay-ground point sits on one of them). Parts nothing touched keep
their exact bytes.

Not yet (MOD_FORMAT §8): raising the ground above a map's highest point, water that follows the ground (lakes keep
their outline), and cutting the mesh finer.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

from . import kdt_edit
from .brush import GROUND_UNCHANGED, HeightGrid, Stroke
from .kdt import MEMBERS as KDT_MEMBERS, Kdt
from .tms import Q_MAX, Tms

FILES = {"highdef": "output\\highdef.tms", "lowdef": "output\\lowdef.tms",
         "ground": KDT_MEMBERS["ground"], "camera": KDT_MEMBERS["camera"]}
LABELS = {"highdef": "close-up mesh", "lowdef": "far mesh", "ground": "gameplay ground", "camera": "camera floor"}
GRID_SAMPLES = 64      # height samples per close-up cell for the smooth brush's local average (at most 1,024 across)
FLOOR_NOTE = "reaches a bridge's floor"   # in each note on a stroke at a bridge's floor (_near_bridge_floors)


@dataclass
class _Points:
    """One file's points, flattened: world x, y and the current z, which file part each belongs to (a mesh cell or a
    tree's subtree) and its number there."""
    name: str
    x: list = field(default_factory=list)
    y: list = field(default_factory=list)
    z: list = field(default_factory=list)
    part: list = field(default_factory=list)
    index: list = field(default_factory=list)
    buckets: dict = field(default_factory=dict)
    step: float = 1.0
    x0: float = 0.0
    y0: float = 0.0
    inside: int = 0      # points some stroke's circle covered

    def add(self, x: float, y: float, z: float, part: int, i: int) -> None:
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        self.part.append(part)
        self.index.append(i)

    def build_index(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0, self.y0 = x0, y0
        self.step = max(x1 - x0, y1 - y0, 1.0) / 256.0
        for n, (x, y) in enumerate(zip(self.x, self.y)):
            self.buckets.setdefault((int((x - x0) // self.step), int((y - y0) // self.step)), []).append(n)

    def near(self, x_lo: float, x_hi: float, y_lo: float, y_hi: float):
        """Numbers of the points that may lie in the box."""
        b0, b1 = int((x_lo - self.x0) // self.step), int((x_hi - self.x0) // self.step)
        c0, c1 = int((y_lo - self.y0) // self.step), int((y_hi - self.y0) // self.step)
        for bx in range(b0, b1 + 1):
            for by in range(c0, c1 + 1):
                yield from self.buckets.get((bx, by), ())

    def apply(self, stroke: Stroke, average=None) -> int:
        """Move the points inside the stroke's circle. Returns how many it covered."""
        n = 0
        z = self.z
        for k in self.near(*stroke.box()):
            x, y = self.x[k], self.y[k]
            if stroke.covers(x, y):
                z[k] = stroke.height_at(x, y, z[k], average)
                n += 1
        self.inside += n
        return n


def _mesh_points(name: str, tms: Tms) -> _Points:
    pts = _Points(name)
    for k, cell in enumerate(tms.cells):
        for i, (qx, qy, qz, _w) in enumerate(cell.positions()):
            pts.add(tms.to_world(0, qx), tms.to_world(1, qy), tms.to_world(2, qz), k, i)
    b = tms.bounds
    pts.build_index(b[0], b[1], b[3], b[4])
    return pts


def _tree_points(name: str, kdt: Kdt) -> _Points:
    pts = _Points(name)
    for s in range(len(kdt.subtrees)):
        for i, (qx, qy, qz) in enumerate(kdt.positions(s)):
            pts.add(kdt.to_world(0, qx), kdt.to_world(1, qy), kdt.to_world(2, qz), s, i)
    pts.build_index(kdt.bounds_min[0], kdt.bounds_min[1], kdt.bounds_max[0], kdt.bounds_max[1])
    return pts


def _held(pts: _Points, z0: float, z1: float) -> tuple[int, int]:
    """Points a stroke pushed past the top or the bottom of the file's height range (by more than half a step)."""
    tol = (z1 - z0) / (2 * Q_MAX)
    return sum(1 for v in pts.z if v > z1 + tol), sum(1 for v in pts.z if v < z0 - tol)


def _commit_mesh(tms: Tms, pts: _Points) -> tuple[int, int, int]:
    """Write the new heights into the mesh. Returns (points moved, held at the top, held at the bottom)."""
    by_cell: dict[int, dict[int, int]] = {}
    for n in range(len(pts.z)):
        k, i = pts.part[n], pts.index[n]
        q = tms.to_quant(2, pts.z[n])
        if q != tms.cells[k].positions()[i][2]:
            by_cell.setdefault(k, {})[i] = q
    moved = sum(tms.set_heights(k, heights) for k, heights in sorted(by_cell.items()))
    return (moved,) + _held(pts, tms.bounds[2], tms.bounds[5])


def _commit_tree(kdt: Kdt, pts: _Points, normal_at) -> tuple[int, int, int, dict]:
    """Write the new heights into the tree; moved points take `normal_at(x, y, z)` (or keep theirs when it's
    None). Returns (points moved, held at the top, held at the bottom, {subtree: its moved vertices})."""
    by_sub: dict[int, dict[int, int]] = {}
    positions: dict[int, list] = {}
    for n in range(len(pts.z)):
        s, i = pts.part[n], pts.index[n]
        if s not in positions:
            positions[s] = kdt.positions(s)
        q = kdt.to_quant(2, pts.z[n])
        if q != positions[s][i][2]:
            by_sub.setdefault(s, {})[i] = n
    moved = 0
    for s, points in sorted(by_sub.items()):
        pos = [list(p) for p in positions[s]]
        normals = list(kdt.normals(s))
        for i, n in points.items():
            pos[i][2] = kdt.to_quant(2, pts.z[n])
            nrm = normal_at(pts.x[n], pts.y[n], pts.z[n]) if normal_at else None
            if nrm is not None:
                normals[i] = nrm
        kdt.set_positions(s, [tuple(p) for p in pos])
        kdt.set_normals(s, normals)
        moved += len(points)
    return (moved,) + _held(pts, kdt.bounds_min[2], kdt.bounds_max[2]) + ({s: set(v) for s, v in by_sub.items()},)


class _Surface:
    """How much the gameplay ground's surface moved, at any x, y: inside a triangle of it that moved, its corners'
    changes weighted by where the point lies (barycentric); 0 elsewhere. Beyond the map's edge (the camera floor's
    ring), the change at the nearest point of the edge. `old(x, y)` is the ground's height there before, in a moved
    triangle (else None). Built from the ground before its new heights are written."""

    def __init__(self, kdt: Kdt, pts: _Points):
        new_q: dict[int, dict[int, int]] = {}
        for n in range(len(pts.z)):
            new_q.setdefault(pts.part[n], {})[pts.index[n]] = kdt.to_quant(2, pts.z[n])
        self.tris: list[tuple] = []
        for s, heights in sorted(new_q.items()):
            pos = kdt.positions(s)
            dz = {i: kdt.to_world(2, q) - kdt.to_world(2, pos[i][2]) for i, q in heights.items() if q != pos[i][2]}
            if not dz:
                continue
            idx = kdt.indices(s)
            for k in range(0, len(idx), 3):
                a, b, c = idx[k], idx[k + 1], idx[k + 2]
                if a in dz or b in dz or c in dz:
                    corners = [(kdt.to_world(0, pos[v][0]), kdt.to_world(1, pos[v][1]), dz.get(v, 0.0),
                                kdt.to_world(2, pos[v][2])) for v in (a, b, c)]
                    (x0, y0, _, _), (x1, y1, _, _), (x2, y2, _, _) = corners
                    det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
                    if det:  # a wall (no area seen from above) has no surface to follow
                        self.tris.append((corners, det))
        self.step = max(kdt.bounds_max[0] - kdt.bounds_min[0], kdt.bounds_max[1] - kdt.bounds_min[1], 1.0) / 256.0
        self.x0, self.y0 = kdt.bounds_min[0], kdt.bounds_min[1]
        self.x1, self.y1 = kdt.bounds_max[0], kdt.bounds_max[1]
        self.buckets: dict[tuple, list[int]] = {}
        for n, (corners, _det) in enumerate(self.tris):
            xs, ys = [c[0] for c in corners], [c[1] for c in corners]
            for bx in range(self._b(min(xs), self.x0), self._b(max(xs), self.x0) + 1):
                for by in range(self._b(min(ys), self.y0), self._b(max(ys), self.y0) + 1):
                    self.buckets.setdefault((bx, by), []).append(n)

    def _b(self, v: float, origin: float) -> int:
        return int((v - origin) // self.step)

    def __bool__(self) -> bool:
        return bool(self.tris)

    def _at(self, x: float, y: float, value: int) -> float | None:
        x, y = min(max(x, self.x0), self.x1), min(max(y, self.y0), self.y1)
        for n in self.buckets.get((self._b(x, self.x0), self._b(y, self.y0)), ()):
            (c0, c1, c2), det = self.tris[n]
            (x0, y0), (x1, y1), (x2, y2) = c0[:2], c1[:2], c2[:2]
            l0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / det
            l1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / det
            l2 = 1.0 - l0 - l1
            if l0 >= -1e-9 and l1 >= -1e-9 and l2 >= -1e-9:
                return l0 * c0[value] + l1 * c1[value] + l2 * c2[value]
        return None

    def change(self, x: float, y: float) -> float:
        return self._at(x, y, 2) or 0.0

    def old(self, x: float, y: float) -> float | None:
        return self._at(x, y, 3)

    def change_and_old(self, x: float, y: float) -> tuple[float, float | None]:
        """(change(x, y), old(x, y)) from one search: both come from the same triangle."""
        x, y = min(max(x, self.x0), self.x1), min(max(y, self.y0), self.y1)
        for n in self.buckets.get((self._b(x, self.x0), self._b(y, self.y0)), ()):
            (c0, c1, c2), det = self.tris[n]
            (x0, y0), (x1, y1), (x2, y2) = c0[:2], c1[:2], c2[:2]
            l0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / det
            l1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / det
            l2 = 1.0 - l0 - l1
            if l0 >= -1e-9 and l1 >= -1e-9 and l2 >= -1e-9:
                return l0 * c0[2] + l1 * c1[2] + l2 * c2[2] or 0.0, l0 * c0[3] + l1 * c1[3] + l2 * c2[3]
        return 0.0, None


def _kept(strokes: list[Stroke], x: float, y: float) -> float:
    """How much of the ground's old shape at (x, y) is left after all the strokes (Stroke.kept, one after another)."""
    kept = 1.0
    for s in strokes:
        kept *= s.kept(x, y)
    return kept


class _Kept:
    """_kept for many points: each point looks only at the strokes whose box reaches its square of the map (strokes
    indexed by place). Every other stroke keeps all of the old shape there (1.0), and so do the strokes that add or
    take away; a product is the same without its ones, so the answer is exactly _kept's. A point off the map's
    squares (none of the meshes' points) asks every stroke."""

    def __init__(self, strokes: list[Stroke], area):
        x0, y0, x1, y1 = area
        self.strokes = strokes
        self.x0, self.y0 = x0, y0
        self.step = max(x1 - x0, y1 - y0, 1.0) / 128.0
        self.cols = (self._b(x0, x0) - 1, self._b(x1, x0) + 1)   # the squares indexed, a ring beyond the map's
        self.rows = (self._b(y0, y0) - 1, self._b(y1, y0) + 1)
        self.buckets: dict[tuple[int, int], list] = {}
        for s in strokes:
            if s.kind.kind in GROUND_UNCHANGED or s.kind.kind == "add":
                continue
            kept = s.kept_function()
            bx0, bx1, by0, by1 = s.box()
            pad = self.step  # a whole square more on every side: rounding at the box's edge can't leave a point out
            for bx in range(max(self._b(bx0 - pad, x0), self.cols[0]), min(self._b(bx1 + pad, x0), self.cols[1]) + 1):
                for by in range(max(self._b(by0 - pad, y0), self.rows[0]),
                                min(self._b(by1 + pad, y0), self.rows[1]) + 1):
                    self.buckets.setdefault((bx, by), []).append(kept)

    def _b(self, v: float, origin: float) -> int:
        return int((v - origin) // self.step)

    def at(self, x: float, y: float) -> float:
        bx, by = self._b(x, self.x0), self._b(y, self.y0)
        if not (self.cols[0] <= bx <= self.cols[1] and self.rows[0] <= by <= self.rows[1]):
            return _kept(self.strokes, x, y)
        kept = 1.0
        for k in self.buckets.get((bx, by), ()):
            kept *= k(x, y)
        return kept


def _refit(kdt: Kdt, moved: dict) -> str:
    """Widen the trees of a .kdt over its moved vertices (rusemod.kdt_edit); the report's words for it."""
    done = {"widened": 0, "rebuilt": 0}
    for s, vertices in sorted(moved.items()):
        result = kdt_edit.refit(kdt, s, vertices)
        if result in done:
            done[result] += 1
    main = kdt_edit.widen_main(kdt, moved)
    return f"{done['widened']} part(s) widened, {done['rebuilt']} rebuilt, {main} top limit(s) widened"


def _normal_lookup(tms: Tms, pts: _Points):
    """The normal of the close-up mesh point nearest to (x, y), as a unit vector, or None when no point is within
    two index squares (the tree point then keeps its own normal). The mesh can hold several points at one x, y (a
    cliff's top and its foot; every shipped close-up mesh has hundreds): among those, the one whose height is
    nearest to z, so a tree point takes the normal of the mesh point it sits on.

    The answer is the least (distance, height difference, point number) among the points of the index squares
    within two squares. The point's own square is looked through first: when one of its points is nearer than the
    square's nearest side, no point of another square can come before it (a tree point on a mesh point: distance
    0). Then the squares next to it: when one of their points lies within half a square, no point of a farther
    square (at least a square away) can come before it. Only then all of them. Each side is taken a millionth of a
    square nearer (`slack`), so rounding at the squares' edges can't matter."""
    xs, ys, zs, buckets, s = pts.x, pts.y, pts.z, pts.buckets, pts.step
    near = (0.5 * s) ** 2
    slack = max(s * 1e-6, 1e-12 * (abs(pts.x0) + abs(pts.y0) + 256 * s))   # far above the rounding of x, y there

    def best_in(x, y, z, cols, rows):
        best, best_d = None, None
        for bx in cols:
            for by in rows:
                for n in buckets.get((bx, by), ()):
                    dx, dy = xs[n] - x, ys[n] - y
                    d = (dx * dx + dy * dy, abs(zs[n] - z))
                    if best_d is None or d < best_d or (d == best_d and n < best):
                        best, best_d = n, d
        return best, best_d

    def at(x: float, y: float, z: float):
        b0, b1 = int((x - 2 * s - pts.x0) // s), int((x + 2 * s - pts.x0) // s)   # the squares pts.near looks in
        c0, c1 = int((y - 2 * s - pts.y0) // s), int((y + 2 * s - pts.y0) // s)
        bx, by = int((x - pts.x0) // s), int((y - pts.y0) // s)                   # the point's own square
        best = None
        if b0 <= bx <= b1 and c0 <= by <= c1:
            side = min(x - (pts.x0 + bx * s), pts.x0 + (bx + 1) * s - x,
                       y - (pts.y0 + by * s), pts.y0 + (by + 1) * s - y) - slack
            if side > 0.0:
                best, best_d = best_in(x, y, z, (bx,), (by,))
                if best is not None and not best_d[0] < side * side:
                    best = None
        if best is None:
            best, best_d = best_in(x, y, z, range(max(b0, bx - 1), min(b1, bx + 1) + 1),
                                   range(max(c0, by - 1), min(c1, by + 1) + 1))
            if best is None or best_d[0] > near:
                best, best_d = best_in(x, y, z, range(b0, b1 + 1), range(c0, c1 + 1))
        if best is None:
            return None
        bx, by, bz, _ = tms.cells[pts.part[best]].normals()[pts.index[best]]
        v = (bx / 127.5 - 1.0, by / 127.5 - 1.0, bz / 127.5 - 1.0)
        length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        if length == 0.0 or v[2] <= 0.0:
            return None
        return (v[0] / length, v[1] / length, v[2] / length)
    return at


def _area(meshes: dict, trees: dict) -> tuple[float, float, float, float]:
    """The map's square (x min, y min, x max, y max), from the first file there is."""
    for m in meshes.values():
        return m.bounds[0], m.bounds[1], m.bounds[3], m.bounds[4]
    t = next(iter(trees.values()))
    return t.bounds_min[0], t.bounds_min[1], t.bounds_max[0], t.bounds_max[1]


def _touches(stroke: Stroke, area) -> bool:
    x0, y0, x1, y1 = area
    return stroke.footprint().meets(x0, y0, x1, y1)


def _area_of(stroke: Stroke) -> tuple[float, float, float]:
    """A circle (x, y, radius) around everything a stroke can change."""
    fp = stroke.footprint()
    if fp.shape == "line":
        half = math.hypot(fp.x2 - fp.x, fp.y2 - fp.y) / 2
        return (fp.x + fp.x2) / 2, (fp.y + fp.y2) / 2, half + fp.r
    if fp.shape == "square":
        return fp.x, fp.y, fp.r * math.sqrt(2.0)
    return fp.x, fp.y, fp.r


def _near_bridge_floors(read, strokes: list[Stroke], name: str) -> list[str]:
    """A note for each height stroke that reaches the floor of one of the map's bridges (the objects-only ground,
    rusemod.floors): a unit stands on the higher of the ground and that floor, and the floor keeps its height, so
    lowering the ground there leaves the floor's end in the air (men step down at its edge), and raising it over the
    deck buries it (units walk over the bank through the bridge)."""
    from . import floors
    try:
        raw = read(floors.MEMBER)
    except KeyError:  # (a pack without it)
        raw = None
    if raw is None or not strokes:
        return []
    try:
        tris = floors.triangles(Kdt(raw))
    except (ValueError, IndexError, struct.error):
        return []
    points = [(sum(p[0] for p in t) / 3, sum(p[1] for p in t) / 3) for t in tris]
    out = []
    for n, s in enumerate(strokes, start=1):
        x, y, r = _area_of(s)
        hit = next(((px, py) for px, py in points if (px - x) ** 2 + (py - y) ** 2 <= r * r), None)
        if hit:
            out.append(f"{name}: stroke {n} ({s.brush} at {s.x:g}, {s.y:g}) {FLOOR_NOTE} at "
                       f"({hit[0]:.0f}, {hit[1]:.0f}), which keeps its height: units there stand on the floor's old "
                       f"level (lower ground leaves its end in the air, higher ground buries it); shape the banks "
                       f"clear of the bridge's ends")
    return out


def without_floor_notes(lines: list[str]) -> list[str]:
    """`lines` without the notes on strokes at a bridge's floor (FLOOR_NOTE): for a map whose own bridges are taken
    out (roads.toml take_out), their floors sunk with them, so the notes don't hold."""
    return [line for line in lines if FLOOR_NOTE not in line]


def _reseat_roads(read, before: Tms, after: Tms, name: str) -> tuple[dict[str, bytes], list[str]]:
    """The map's road model (rusemod.roadstrips: the white roads seen from high up) moved with its close-up mesh: each
    vertex by the ground's change of height under it, in every static-mesh file the map has. Left, the model kept the
    old heights and stood off the roads painted on the ground (flattened Blitz Twin, 2026-10-04)."""
    from .bridges import GroundChange
    from .roadstrips import MEMBERS, StaticMeshes, StripError
    moved = GroundChange(before, after).at   # the ground's height there after, less before (None off either)
    out, notes = {}, []
    for member in MEMBERS:
        try:
            raw = read(member)
        except KeyError:  # a pack's own find, asked for a file the map hasn't got
            raw = None
        if raw is None:
            continue
        try:
            new_raw, n = StaticMeshes(raw).with_heights(moved)
        except StripError as exc:
            notes.append(f"{name}: {member.rsplit(chr(92), 1)[-1]}: the road model can't follow the ground ({exc}): "
                         f"the white roads seen from high up keep the old heights")
            continue
        if n:
            out[member] = new_raw
            notes.append(f"{name}: road model ({member.rsplit(chr(92), 1)[-1]}): {n} point(s) moved with the ground")
    return out, notes


def edit_map(read, strokes: list[Stroke], name: str = "the map", max_depth_of=None) -> tuple[dict[str, bytes], list[str]]:
    """Apply `strokes`, in order, to a map pack's ground. `read(member path)` gives a member's bytes, or None when
    the pack hasn't got it. Height brushes come first, then the water brushes (rusemod.water); then the map's water
    textures follow the drawn water near every stroke. `max_depth_of()` gives the map's MaxDepthForSimulationDepthMap
    (the textures' depth scale), or None. Returns ({member path: new bytes} for the files that changed, report
    lines)."""
    from .water import apply_water, update_textures
    water_strokes = [s for s in strokes if s.brush in ("water", "drain")]
    strokes = [s for s in strokes if s.brush not in ("water", "drain")]
    notes: list[str] = []
    meshes: dict[str, Tms] = {}
    trees: dict[str, Kdt] = {}
    for key, member in FILES.items():
        raw = read(member)
        if raw is None:
            notes.append(f"{name} has no {member} ({LABELS[key]}); the other files are edited")
        elif key in ("highdef", "lowdef"):
            meshes[key] = Tms(raw)
        else:
            trees[key] = Kdt(raw)
    if not meshes and not trees:
        raise ValueError(f"{name} has none of the files that hold its ground")
    points = {key: _mesh_points(key, m) for key, m in meshes.items()}
    points.update({key: _tree_points(key, t) for key, t in trees.items()})

    grid = None
    if any(s.brush == "smooth" for s in strokes):
        ref = meshes.get("highdef") or meshes.get("lowdef")
        if ref is None:
            notes.append(f"{name}: the smooth brush needs a drawn mesh for the local average; smooth strokes skipped")
        else:
            cols = min(1024, max(8, ref.grid_w * GRID_SAMPLES))
            b = ref.bounds
            grid = HeightGrid(ref.height_grid(cols), b[0], b[1], b[3], b[4])

    area = _area(meshes, trees)
    notes += _near_bridge_floors(read, strokes, name)
    # the gameplay ground leads; without it, every file is moved by the strokes themselves
    painted = [points["ground"]] if "ground" in points else list(points.values())
    applied = []
    for n, stroke in enumerate(strokes, start=1):
        if stroke.brush == "smooth" and grid is None:
            continue
        applied.append(stroke)
        average = grid.average_for(stroke) if stroke.brush == "smooth" else None
        covered = sum(pts.apply(stroke, average) for pts in painted)
        if grid is not None:
            grid.apply(stroke, average)
        if not covered:
            where = f"stroke {n} ({stroke.brush} at {stroke.x:g}, {stroke.y:g})"
            if _touches(stroke, area):
                notes.append(f"{name}: {where} is smaller than the gaps between the ground's points, so it changes "
                             f"nothing")
            else:
                notes.append(f"{name}: {where} is outside the map")

    if "ground" in points:  # the others follow the gameplay ground's surface, sampled inside its triangles
        surface = _Surface(trees["ground"], points["ground"])
        if surface:
            kept_at = _Kept(applied, area).at
            for key, pts in points.items():
                if key == "ground":
                    continue
                xs, ys, zs = pts.x, pts.y, pts.z
                mesh = key in meshes
                for k in range(len(zs)):
                    x, y = xs[k], ys[k]
                    dz, g = surface.change_and_old(x, y)
                    kept = kept_at(x, y) if mesh else 1.0
                    if kept < 1.0:   # a drawn mesh's own bumps off the ground go as far as the strokes flatten
                        if g is not None:
                            dz -= (zs[k] - g) * (1.0 - kept)
                    zs[k] += dz

    changed: dict[str, bytes] = {}
    counts = []
    held: dict[str, tuple[int, int]] = {}  # file -> points held at the top, at the bottom of its own height range
    moved_mesh = {}
    for key in ("highdef", "lowdef"):
        if key in meshes:
            moved, top, bottom = _commit_mesh(meshes[key], points[key])
            held[LABELS[key]] = (top, bottom)
            counts.append(f"{LABELS[key]} {moved}")
            moved_mesh[key] = moved
    water_notes = apply_water(meshes, water_strokes)
    for key in ("highdef", "lowdef"):
        if key in meshes and (moved_mesh[key] or water_strokes):
            changed[FILES[key]] = meshes[key].to_bytes()
    if "highdef" in meshes and FILES["highdef"] in changed:
        before = Tms(read(FILES["highdef"]))   # the close-up mesh as it was (only read from, below)
        depth = max_depth_of() if max_depth_of else None
        if depth:
            far = "lowdef" in meshes
            new_tex, tex_notes = update_textures(read, before, meshes["highdef"],
                                                 [_area_of(s) for s in strokes + water_strokes], depth, name,
                                                 far_before=Tms(read(FILES["lowdef"])) if far else None,
                                                 far_after=meshes["lowdef"] if far else None)
            changed.update(new_tex)
            water_notes += tex_notes
        elif water_strokes:
            water_notes.append(f"{name}: the map's water depth scale couldn't be read, so its water textures were "
                               f"left as they are")
        roads, road_notes = _reseat_roads(read, before, meshes["highdef"], name)
        changed.update(roads)
        water_notes += road_notes
    normal_at = _normal_lookup(meshes["highdef"], points["highdef"]) if "highdef" in meshes else None
    fitted = []
    for key in ("ground", "camera"):
        if key in trees:
            moved, top, bottom, by_sub = _commit_tree(trees[key], points[key], normal_at)
            held[LABELS[key]] = (top, bottom)
            counts.append(f"{LABELS[key]} {moved}")
            if moved:
                fitted.append(f"{name}: {LABELS[key]}: {_refit(trees[key], by_sub)}")
                changed[FILES[key]] = trees[key].to_bytes()
    notes.insert(0, f"{name}: {len(strokes) + len(water_strokes)} stroke(s); points moved: " + ", ".join(counts))
    notes[1:1] = water_notes + fitted
    # each file stops heights at its own range, and the ranges differ (Alpha's far mesh tops out 218 under its
    # close-up mesh; Beta's camera floor goes down to -303, its ground to -2,452): say which files held, since the
    # others went on (a far mesh flat-topped under a peak, a camera floor over a pit)
    for side, k in (("top", 0), ("bottom", 1)):
        which = {label: v[k] for label, v in held.items() if v[k]}
        if which:
            what = ", ".join(f"{label} {n}" for label, n in which.items())
            others = [label for label in held if label not in which]
            notes.append(f"{name}: point(s) reached the {side} of a file's height range and stop there ({what})"
                         + (f", while the {' and the '.join(others)} went on: keep the stroke within the map's "
                            f"heights" if others else " (going past the map's heights comes later)"))
    return changed, notes
