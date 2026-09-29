"""Terrain edits on a map's ground (PLAN.md §7 MT, step T2; docs/MOD_FORMAT.md §8): brush strokes applied to all
four files that hold a map's ground, together (FORMATS.md §6):

  output\\highdef.tms                    the close-up mesh the game draws
  output\\lowdef.tms                     the far mesh (coarser, its own points)
  output\\occlusioninfo_terrainonly.kdt  the gameplay ground (its points sit on highdef's)
  output\\occlusioninfo_camera.kdt       the camera floor

Every stroke (rusemod.brush) moves every point of every file inside its circle, as a function of the point's position
and height only, so points the files share end up at the same height. The map's outer edge stays where it is (the
drawn mesh's curtain hangs from it). Heights stay inside each file's own height range: a point pushed past the top or
the bottom stops there, and the report says how many did. In the meshes, the normals around moved points and the
height bounds of their patches are recomputed (rusemod.tms); in the .kdt trees, a moved point takes the normal of the
nearest close-up mesh point. Parts nothing touched keep their exact bytes.

Not yet (MOD_FORMAT §8): raising the ground above a map's highest point, water that follows the ground (lakes keep
their outline), and cutting the mesh finer.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .brush import HeightGrid, Stroke
from .kdt import MEMBERS as KDT_MEMBERS, Q_MASK, Kdt
from .tms import Q_MAX, Tms

FILES = {"highdef": "output\\highdef.tms", "lowdef": "output\\lowdef.tms",
         "ground": KDT_MEMBERS["ground"], "camera": KDT_MEMBERS["camera"]}
LABELS = {"highdef": "close-up mesh", "lowdef": "far mesh", "ground": "gameplay ground", "camera": "camera floor"}
GRID_SAMPLES = 64      # height samples per close-up cell for the smooth brush's local average (at most 1,024 across)


@dataclass
class _Points:
    """One file's points, flattened: world x, y and the current z, which file part each belongs to (a mesh cell or a
    tree's subtree) and its number there. Points on the map's outer edge are left out: they never move."""
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
            if qx in (0, Q_MAX) or qy in (0, Q_MAX):
                continue
            pts.add(tms.to_world(0, qx), tms.to_world(1, qy), tms.to_world(2, qz), k, i)
    b = tms.bounds
    pts.build_index(b[0], b[1], b[3], b[4])
    return pts


def _tree_points(name: str, kdt: Kdt) -> _Points:
    pts = _Points(name)
    for s in range(len(kdt.subtrees)):
        for i, (qx, qy, qz) in enumerate(kdt.positions(s)):
            if qx in (0, Q_MASK) or qy in (0, Q_MASK):
                continue
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


def _commit_tree(kdt: Kdt, pts: _Points, normal_at) -> tuple[int, int, int]:
    """Write the new heights into the tree; moved points take `normal_at(x, y)` (or keep theirs when it's None)."""
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
            nrm = normal_at(pts.x[n], pts.y[n]) if normal_at else None
            if nrm is not None:
                normals[i] = nrm
        kdt.set_positions(s, [tuple(p) for p in pos])
        kdt.set_normals(s, normals)
        moved += len(points)
    return (moved,) + _held(pts, kdt.bounds_min[2], kdt.bounds_max[2])


def _normal_lookup(tms: Tms, pts: _Points):
    """The normal of the close-up mesh point nearest to (x, y), as a unit vector, or None when no point is within
    two index squares (the tree point then keeps its own normal)."""
    def at(x: float, y: float):
        best, best_d = None, None
        s = pts.step
        for n in pts.near(x - 2 * s, x + 2 * s, y - 2 * s, y + 2 * s):
            dx, dy = pts.x[n] - x, pts.y[n] - y
            d = dx * dx + dy * dy
            if best_d is None or d < best_d or (d == best_d and n < best):
                best, best_d = n, d
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
    dx = max(x0 - stroke.x, 0.0, stroke.x - x1)
    dy = max(y0 - stroke.y, 0.0, stroke.y - y1)
    return dx * dx + dy * dy < stroke.radius * stroke.radius


def edit_map(read, strokes: list[Stroke], name: str = "the map") -> tuple[dict[str, bytes], list[str]]:
    """Apply `strokes`, in order, to a map pack's ground. `read(member path)` gives a member's bytes, or None when
    the pack hasn't got it. Returns ({member path: new bytes} for the files that changed, report lines)."""
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
    for n, stroke in enumerate(strokes, start=1):
        if stroke.brush == "smooth" and grid is None:
            continue
        average = grid.average_for(stroke) if stroke.brush == "smooth" else None
        covered = sum(pts.apply(stroke, average) for pts in points.values())
        if grid is not None:
            grid.apply(stroke, average)
        if not covered:
            where = f"stroke {n} ({stroke.brush} at {stroke.x:g}, {stroke.y:g})"
            if _touches(stroke, area):
                notes.append(f"{name}: {where} is smaller than the gaps between the ground's points, so it changes "
                             f"nothing")
            else:
                notes.append(f"{name}: {where} is outside the map")

    changed: dict[str, bytes] = {}
    counts = []
    held_top = held_bottom = 0
    for key in ("highdef", "lowdef"):
        if key in meshes:
            moved, top, bottom = _commit_mesh(meshes[key], points[key])
            held_top, held_bottom = held_top + top, held_bottom + bottom
            counts.append(f"{LABELS[key]} {moved}")
            if moved:
                changed[FILES[key]] = meshes[key].to_bytes()
    normal_at = _normal_lookup(meshes["highdef"], points["highdef"]) if "highdef" in meshes else None
    for key in ("ground", "camera"):
        if key in trees:
            moved, top, bottom = _commit_tree(trees[key], points[key], normal_at)
            held_top, held_bottom = held_top + top, held_bottom + bottom
            counts.append(f"{LABELS[key]} {moved}")
            if moved:
                changed[FILES[key]] = trees[key].to_bytes()
    notes.insert(0, f"{name}: {len(strokes)} stroke(s); points moved: " + ", ".join(counts))
    if held_top:
        notes.append(f"{name}: {held_top} point(s) reached the top of the map's height range and stop there "
                     f"(raising the ground above the map's highest point comes later)")
    if held_bottom:
        notes.append(f"{name}: {held_bottom} point(s) reached the bottom of the map's height range and stop there")
    return changed, notes
