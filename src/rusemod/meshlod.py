"""Lighter versions of a map asset's model for the game's middle and far distances (the owner, 2026-10-17: the importer
makes them "as a best guess" from one model, editable in Blender, saved in the mod beside it; every model judged on its
own at each distance, never one fixed cut for all).

The game draws scenery in three rings round the camera's eye: close to 77 m, middle to 385 m, far beyond
(LevelBuild_High, LevelBuild_Mid). Each version here may be off by at most one pixel where its ring starts, at the
game's own camera (45 degrees up the screen, every screenshot's .ini: FOV 0.785398) on a 1080-pixel-high screen:
5.9 cm at 77 m, 29.5 cm at 385 m. So a model's versions follow its own size and shape: a big cliff keeps more than a
small stone, a smooth boulder less than a jagged one.

- A solid surface is merged into cells of that size (vertex clustering): every point of a cell becomes one point, put
  where the surfaces meeting there agree best (their planes' least squares, kept inside the cell), triangles that
  shrink to nothing dropped. Points on two sides of a picture seam (other UVs) or of two materials stay apart, at the
  same place, so no crack opens.
- See-through leaves (cards) would merge into nothing, so they are thinned instead: whole cards kept at random, each
  grown about its middle so the foliage covers what it did, until a card is LEAF_PIXELS across where its ring starts.

A tree's and a bush's middle and far look is a picture the game draws from models (an imposter, redrawn as the camera
turns: TImposteurManager), so it is made of their middle versions, never of the full model (the first in-game test,
2026-10-17: a 2-million-triangle tree as the source, 21-26 million primitives a frame at any distance)."""
from __future__ import annotations

import math

from .modelin import Material, Mesh, Model, smooth_normals
from .numpy2 import np

FOV = 0.785398        # the game's camera: its vertical angle (radians), as every screenshot's .ini gives it
SCREEN = 1080         # pixels up the screen
RINGS = {"medium": 77.0, "far": 385.0}   # metres: where each version starts being drawn (LevelBuild_High, _Mid)
LEAF_PIXELS = 3.0     # a thinned leaf card's least size where its ring starts, in pixels (a tree's look up there is
                      # foliage, not single leaves)


def pixel(distance: float) -> float:
    """Metres one screen pixel covers at `distance` metres from the eye."""
    return 2.0 * distance * math.tan(FOV / 2) / SCREEN


def _join(model: Model):
    """The model's meshes as one: points, normals, UVs (v up), triangles, each triangle's material."""
    pos, nrm, uvs, tri, mat = [], [], [], [], []
    base = 0
    for m in model.meshes:
        p = np.asarray(m.positions, dtype=np.float64).reshape(-1, 3)
        if not len(p):
            continue
        n = np.asarray(m.normals or smooth_normals(m.positions, m.triangles), dtype=np.float64).reshape(-1, 3)
        u = np.asarray(m.uvs, dtype=np.float64).reshape(-1, 2) if m.uvs else np.zeros((len(p), 2))
        t = np.asarray(m.triangles, dtype=np.int64).reshape(-1, 3)
        pos.append(p)
        nrm.append(n)
        uvs.append(u)
        tri.append(t + base)
        mat.append(np.asarray(m.face_materials or [-1] * len(t), dtype=np.int64))
        base += len(p)
    if not pos:
        return (np.zeros((0, 3)), np.zeros((0, 3)), np.zeros((0, 2)), np.zeros((0, 3), dtype=np.int64),
                np.zeros(0, dtype=np.int64))
    return np.concatenate(pos), np.concatenate(nrm), np.concatenate(uvs), np.concatenate(tri), np.concatenate(mat)


def _rows(*cols):
    """Each row's group number for the integer columns given (equal rows, equal number)."""
    keys = np.stack(cols, axis=1).astype(np.int64)
    _u, inv = np.unique(keys, axis=0, return_inverse=True)
    return inv.reshape(-1)


def cluster(pos, nrm, uvs, tri, mat, cell: float, uv_cell: float):
    """Solid surfaces merged into cells `cell` metres across (the module's first way). `uv_cell`: how close two UVs
    must be to merge (points across a picture seam differ by far more). Returns (points, normals, UVs, triangles,
    materials) of the lighter surface."""
    if not len(tri):
        return pos[:0], nrm[:0], uvs[:0], tri[:0], mat[:0]
    used = np.unique(tri)
    pcell = np.floor(pos / cell).astype(np.int64)
    place = np.full(len(pos), -1, dtype=np.int64)
    place[used] = _rows(*pcell[used].T)                       # each point's cell (where it goes)
    k = int(place.max()) + 1
    # each cell's point: the least squares of the planes of the triangles touching it (quadric error), kept in the cell
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    cross = np.cross(b - a, c - a)
    area = np.linalg.norm(cross, axis=1)
    n = cross / np.maximum(area, 1e-30)[:, None]
    d = -(n * a).sum(axis=1)
    w = area[:, None]
    q_aa = np.zeros((k, 3, 3))
    q_ab = np.zeros((k, 3))
    for corner in range(3):
        cells = place[tri[:, corner]]
        np.add.at(q_aa, cells, w[:, :, None] * n[:, :, None] * n[:, None, :])
        np.add.at(q_ab, cells, -(w * n * d[:, None]))
    count = np.bincount(place[used], minlength=k).astype(np.float64)
    mean = np.zeros((k, 3))
    np.add.at(mean, place[used], pos[used])
    mean /= np.maximum(count, 1.0)[:, None]
    det = np.linalg.det(q_aa)
    scale = np.einsum("kii->k", q_aa) ** 3 / 27.0
    good = np.abs(det) > 1e-6 * np.maximum(scale, 1e-30)
    best = mean.copy()
    if good.any():
        best[good] = np.linalg.solve(q_aa[good], q_ab[good][:, :, None])[:, :, 0]
    lo = np.zeros((k, 3))
    lo[place[used]] = pcell[used] * cell
    best = np.where((best >= lo) & (best <= lo + cell), best, mean)   # (a point outside its cell: the cell's mean)
    # the new points: one per cell, picture seam and material (the same place for all of a cell's)
    corner_v = tri.reshape(-1)
    corner_m = np.repeat(mat, 3)
    ucell = np.floor(uvs[corner_v] / uv_cell).astype(np.int64)
    new = _rows(place[corner_v], ucell[:, 0], ucell[:, 1], corner_m)
    m_new = int(new.max()) + 1
    out_pos = np.zeros((m_new, 3))
    out_pos[new] = best[place[corner_v]]
    out_uv = np.zeros((m_new, 2))
    out_n = np.zeros((m_new, 3))
    hits = np.bincount(new, minlength=m_new).astype(np.float64)[:, None]
    np.add.at(out_uv, new, uvs[corner_v])
    np.add.at(out_n, new, nrm[corner_v])
    out_uv /= np.maximum(hits, 1.0)
    out_n /= np.maximum(np.linalg.norm(out_n, axis=1), 1e-12)[:, None]
    t_new = new.reshape(-1, 3)
    t_cell = place[tri]
    keep = (t_cell[:, 0] != t_cell[:, 1]) & (t_cell[:, 1] != t_cell[:, 2]) & (t_cell[:, 0] != t_cell[:, 2])
    t_new, t_mat = t_new[keep], mat[keep]
    if len(t_new):   # the same triangle twice (two folded into one place): once
        _u, first = np.unique(np.concatenate([np.sort(t_new, axis=1), t_mat[:, None]], axis=1), axis=0,
                              return_index=True)
        first.sort()
        t_new, t_mat = t_new[first], t_mat[first]
    live = np.unique(t_new)
    renum = np.full(m_new, -1, dtype=np.int64)
    renum[live] = np.arange(len(live))
    return out_pos[live], out_n[live], out_uv[live], renum[t_new], t_mat


def cards(tri, points: int):
    """Each triangle's card: triangles sharing a point are one card (a leaf, a frond)."""
    label = np.arange(points, dtype=np.int64)
    while True:
        low = label[tri].min(axis=1)
        before = label.copy()
        for corner in range(3):
            np.minimum.at(label, tri[:, corner], low)
        label = label[label]                       # (follow the chains: halves the passes)
        if np.array_equal(label, before):
            return label[tri[:, 0]]


def thin(pos, nrm, uvs, tri, mat, keep: float, seed: int = 0, grow_most: float = math.inf):
    """Whole cards kept with chance `keep`, each grown about its middle by 1 / sqrt(keep) so the foliage covers what
    it did, but never by more than `grow_most` (a tiny plant thinned to a card or two: covering what it did would
    make that card bigger than the plant). Returns (points, normals, UVs, triangles, materials)."""
    if keep >= 1.0 or not len(tri):
        used = np.unique(tri) if len(tri) else np.zeros(0, dtype=np.int64)
        renum = np.full(len(pos), -1, dtype=np.int64)
        renum[used] = np.arange(len(used))
        return pos[used], nrm[used], uvs[used], renum[tri], mat
    card = cards(tri, len(pos))
    ids, per_tri = np.unique(card, return_inverse=True)
    rng = np.random.default_rng(seed)
    draw = rng.random(len(ids))   # (each card's draw the same for every ring: a farther ring's cards are a nearer's)
    kept = draw < keep
    if not kept.any():
        kept[int(np.argmin(draw))] = True   # (the one card every nearer ring kept too)
    t_keep = kept[per_tri.reshape(-1)]
    tri, mat, per_tri = tri[t_keep], mat[t_keep], per_tri.reshape(-1)[t_keep]
    used = np.unique(tri)
    point_card = np.zeros(len(pos), dtype=np.int64)
    point_card[tri.reshape(-1)] = np.repeat(per_tri, 3)
    middle = np.zeros((len(ids), 3))
    hits = np.bincount(point_card[used], minlength=len(ids)).astype(np.float64)
    np.add.at(middle, point_card[used], pos[used])
    middle /= np.maximum(hits, 1.0)[:, None]
    grow = min(1.0 / math.sqrt(keep), max(1.0, grow_most))
    p = pos.copy()
    p[used] = middle[point_card[used]] + (pos[used] - middle[point_card[used]]) * grow
    renum = np.full(len(pos), -1, dtype=np.int64)
    renum[used] = np.arange(len(used))
    return p[used], nrm[used], uvs[used], renum[tri], mat


def _typical_card(pos, tri) -> float:
    """The median card's area (square metres)."""
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    card = cards(tri, len(pos))
    per_card = np.bincount(np.unique(card, return_inverse=True)[1].reshape(-1), weights=area)
    return float(np.median(per_card)) if len(per_card) else 0.0


def card_keep(pos, tri, distance: float) -> float:
    """The chance a card is kept for a ring starting `distance` metres away: its cards grown until the typical one is
    LEAF_PIXELS across there (never shrunk)."""
    typical = _typical_card(pos, tri)
    want = (LEAF_PIXELS * pixel(distance)) ** 2
    return 1.0 if typical <= 0 else min(1.0, typical / want)


def card_growth_most(pos, tri) -> float:
    """How much a kept card may grow: until it is half as wide as all the cards together (the foliage's box)."""
    used = np.unique(tri)
    span = float((pos[used].max(axis=0) - pos[used].min(axis=0)).max()) if len(used) else 0.0
    side = math.sqrt(_typical_card(pos, tri))
    return math.inf if side <= 0 else 0.5 * span / side


def version(model: Model, ring: str, leaves: set | None = None, seed: int = 0) -> Model:
    """The model's version for `ring` ("medium" or "far": RINGS): solid materials merged to that ring's pixel,
    see-through ones (`leaves`: their material numbers; by default every cut-out material) thinned. The materials stay
    the model's own, in the same order (a version shares the model's pictures)."""
    distance = RINGS[ring]
    leaves = {i for i, m in enumerate(model.materials) if m.cutout} if leaves is None else set(leaves)
    pos, nrm, uvs, tri, mat = _join(model)
    parts = []
    is_leaf = np.isin(mat, sorted(leaves)) if leaves else np.zeros(len(mat), dtype=bool)
    if (~is_leaf).any():
        cell = pixel(distance)
        parts.append(cluster(pos, nrm, uvs, tri[~is_leaf], mat[~is_leaf], cell, uv_cell=1.0 / 512))
    if is_leaf.any():
        keep = card_keep(pos, tri[is_leaf], distance)
        parts.append(thin(pos, nrm, uvs, tri[is_leaf], mat[is_leaf], keep, seed,
                          card_growth_most(pos, tri[is_leaf])))
    meshes = []
    for p, n, u, t, m in parts:
        if len(t):
            meshes.append(Mesh(ring, [tuple(x) for x in p.tolist()], [tuple(x) for x in t.tolist()],
                               [tuple(x) for x in u.tolist()], m.tolist(), [tuple(x) for x in n.tolist()]))
    return Model(meshes, list(model.materials), f"{model.source} ({ring})")


BACK_OFFSET = 0.005   # a back face's distance behind its front, in shares of the model's longest side


def both_sides(model: Model, offset: float | None = None) -> Model:
    """The model with every triangle also facing the other way, on points of its own whose normals face that way: a
    surface with no back (a scan of a rock's face) seen from behind. (The game draws one side of a triangle; drawing
    such a scan in its leaves' bucket left its back unseen, 2026-10-17.) Twice the triangles.
    Each back point sits `offset` metres (BACK_OFFSET of the model's longest side when not given) behind its front
    point: right on it, the game drew the fronts up close with dark, smeared triangles (the third asset test,
    2026-10-17; a shadow drawn from the back face onto its own front, most likely)."""
    if offset is None:
        lo, hi = np.array(model.box()[:3]), np.array(model.box()[3:])
        offset = BACK_OFFSET * float((hi - lo).max())
    meshes = []
    for m in model.meshes:
        n = len(m.positions)
        normals = list(m.normals or smooth_normals(m.positions, m.triangles))
        back = (np.asarray(m.positions, dtype=np.float64).reshape(-1, 3)
                - offset * np.asarray(normals, dtype=np.float64).reshape(-1, 3))
        meshes.append(Mesh(m.name, list(m.positions) + [tuple(p) for p in back.tolist()],
                           list(m.triangles) + [(a + n, c + n, b + n) for a, b, c in m.triangles],
                           list(m.uvs) * 2 if m.uvs else [], list(m.face_materials) * 2 if m.face_materials else [],
                           normals + [(-x, -y, -z) for x, y, z in normals]))
    return Model(meshes, model.materials, model.source)


# --- saved in the mod beside the model (editable in Blender, read back by rusemod.modelin) ------------------------
def glb_bytes(model: Model, beside) -> bytes:
    """`model` as a .glb whose materials use the full model's own picture files when they lie in the folder
    `beside` (a .gltf's textures/...: the version adds no picture), the picture itself otherwise; glTF's axes (y up:
    a point (x, y, z) here is (x, z, -y) there, as rusemod.modelin reads it back) and UVs (v down)."""
    from pathlib import Path

    from .gltf import FLOAT, UINT, _Glb
    g = _Glb()
    for mat in model.materials:
        entry = {"name": mat.name, "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 0.9}}
        if mat.picture and (Path(beside) / mat.picture).is_file():
            g.doc["images"].append({"uri": mat.picture.replace("\\", "/"), "name": mat.picture})
            g.doc["textures"].append({"sampler": 0, "source": len(g.doc["images"]) - 1})
            entry["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(g.doc["textures"]) - 1}
        elif mat.data:
            entry["pbrMetallicRoughness"]["baseColorTexture"] = {"index": g.image(mat.data, mat.name or "picture")}
            if mat.mask:
                entry["extras"] = {"rusemod_mask_texture": g.image(mat.mask, (mat.name or "picture") + "_alpha")}
        else:
            entry["pbrMetallicRoughness"]["baseColorFactor"] = [*mat.colour, 1.0]
        if mat.cutout:
            entry["alphaMode"] = mat.cutout
            entry["doubleSided"] = True
        g.doc["materials"].append(entry)
    prims = []
    for mesh in model.meshes:
        p = np.asarray(mesh.positions, dtype=np.float64).reshape(-1, 3)
        n = np.asarray(mesh.normals or smooth_normals(mesh.positions, mesh.triangles), dtype=np.float64).reshape(-1, 3)
        u = np.asarray(mesh.uvs, dtype=np.float64).reshape(-1, 2) if mesh.uvs else np.zeros((len(p), 2))
        t = np.asarray(mesh.triangles, dtype=np.int64).reshape(-1, 3)
        fm = np.asarray(mesh.face_materials or [-1] * len(t), dtype=np.int64)
        for m in np.unique(fm):   # a primitive a material, with its own points (a reader takes a primitive's all)
            mine = t[fm == m]
            used, local = np.unique(mine, return_inverse=True)
            gp = np.stack([p[used, 0], p[used, 2], -p[used, 1]], axis=1).astype("<f4")
            gn = np.stack([n[used, 0], n[used, 2], -n[used, 1]], axis=1).astype("<f4")
            gu = np.stack([u[used, 0], 1.0 - u[used, 1]], axis=1).astype("<f4")
            idx = local.reshape(-1).astype("<u4")
            prim = {"attributes": {"POSITION": g.packed(gp.tobytes(), len(gp), "VEC3", FLOAT,
                                                        low=gp.min(axis=0).tolist(), high=gp.max(axis=0).tolist()),
                                   "NORMAL": g.packed(gn.tobytes(), len(gn), "VEC3", FLOAT),
                                   "TEXCOORD_0": g.packed(gu.tobytes(), len(gu), "VEC2", FLOAT)},
                    "indices": g.packed(idx.tobytes(), idx.size, "SCALAR", UINT, 34963)}
            if m >= 0:
                prim["material"] = int(m)
            prims.append(prim)
    g.doc["meshes"] = [{"name": model.source, "primitives": prims}]
    g.doc["nodes"] = [{"name": "model", "mesh": 0}]
    g.doc["scenes"] = [{"nodes": [0]}]
    g.doc["scene"] = 0
    g.doc["asset"]["extras"] = {"rusemod_version": model.source}
    return g.to_bytes()
