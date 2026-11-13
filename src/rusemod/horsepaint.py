"""The Generic Horse's horse in a picture of our own (the owner, 2026-11-13, his answer 13 to "The Generic Horse's
picture: a new picture on the same horse, a free horse model, or a repaint?": "new picture of horse"; and 2026-11-12,
in Export's question: "horse squad shoul d have a diff picture of a horse").

The made files (rusemod.horsesquad) carry the game's own picture of its scenery horse, pixel for pixel (Export packs
them: his exception "for now"). This paints another one for the same horse model, from the model alone: every pixel
is worked out here from the horse's own mesh (where each spot of the picture lies on the horse: along it, how high, how
far to the side, which way it faces) and a few colours and rules of our own; nothing of the game's picture is copied
or traced. The game's picture was read once (2026-11-13, agent-horse's horse_eye.py) only to find where the eye is
painted on it; that place, as fractions of the horse, is EYE below.

The look (ours, a different horse from the game's chestnut with white stockings): a dark bay, a rich brown coat with
black points (mane, forelock, tail, lower legs, ear tips), a dark muzzle, dark grey hooves; lit from above as the
game's own pictures are (darker under the belly and between the legs, lighter along the back), and a fine hair grain.
Its picture is the size of the game's (1024 x 512) with the horse's parts where the model's UVs put them, so nothing of
the model changes; the rest of the picture, which the horse doesn't use, is the coat's colour.

Only + - * / and square roots, in a fixed order, so the same model gives the same bytes on every PC (the builder's own
rule, rusemod.horsesquad); its noise is integer hashing. Switched on only by the owner's look (horsesquad.OWN_PICTURE);
with it off, the made files are the passed copy's bytes, as before.

    paint(points, uvs, triangles, width, height) -> the PNG
    with_own_picture(glb) -> the .glb with its horse's picture ours (the material named HORSE_MATERIAL)
"""
from __future__ import annotations

import numpy as np

from .dxt import png_bytes

HORSE_TEXTURE = "tscforcedxt1_diffusetexture01"   # the game's picture of its scenery horse (animaux_1), by its name
HORSE_MATERIAL = "generic_horse_coat"            # the material (and picture) our picture goes in under
SIZE = (1024, 512)
# colours of our own (sRGB): a dark bay
COAT = (72.0, 36.0, 19.0)
COAT_LIGHT = (122.0, 66.0, 34.0)
COAT_DARK = (30.0, 17.0, 10.0)
POINTS = (29.0, 23.0, 20.0)           # black points: mane, forelock, tail, lower legs, ear tips
POINTS_SHINE = (68.0, 58.0, 52.0)     # the hair's lighter strands
HOOF = (58.0, 54.0, 50.0)
MUZZLE = (44.0, 31.0, 24.0)
EYE_COLOUR = (14.0, 10.0, 9.0)
# where the eye is, as fractions of the horse (along it from the tail, up from the ground, out to the side): found from
# the game's picture by agent-horse's horse_eye.py on 2026-11-13 (the darkest small spot of the head), never its pixels
EYE = (0.900, 0.894, 0.170)
EYE_RADIUS = 0.010                    # (of the horse's length; the dark around it twice that)
MANE = (0.62, 0.86, 0.075)            # the mane along the neck's crest: from (along), to (along), how far down (of height)
PAD = 8                               # pixels each part's colour runs on past its edge (no seam where it's sampled)
REACH = 0.32                          # how far (of the horse's length) another part of it shades a spot (occlusion)


class PaintError(ValueError):
    """The model isn't the horse this paints (its parts aren't where they are expected)."""


# --- noise of our own: integer hashing, smooth steps (no sine, no exponent: the same bytes on every PC) ---
def _hash(ix, iy, seed: int):
    h = (ix.astype(np.uint64) * np.uint64(374761393) + iy.astype(np.uint64) * np.uint64(668265263)
         + np.uint64(seed) * np.uint64(2246822519)) & np.uint64(0xFFFFFFFF)
    h = ((h ^ (h >> np.uint64(13))) * np.uint64(1274126177)) & np.uint64(0xFFFFFFFF)
    h = h ^ (h >> np.uint64(16))
    return h.astype(np.float64) / 4294967295.0


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def noise(x, y, seed: int):
    """Value noise in [-1, 1] at (x, y) (float arrays, one cell a unit)."""
    x0, y0 = np.floor(x), np.floor(y)
    tx, ty = _smooth(x - x0), _smooth(y - y0)
    ix, iy = x0.astype(np.int64), y0.astype(np.int64)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    top = a + (b - a) * tx
    bottom = c + (d - c) * tx
    return (top + (bottom - top) * ty) * 2.0 - 1.0


# --- the horse's parts, from its mesh ---
def _islands(uv, tris) -> list:
    """The triangles in groups joined by a shared UV corner: the model's parts on the picture."""
    parent = list(range(len(tris)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first = {}
    for t, tri in enumerate(tris):
        for v in tri:
            k = (int(np.floor(uv[v, 0] * 65536.0 + 0.5)), int(np.floor(uv[v, 1] * 65536.0 + 0.5)))
            if k in first:
                a, b = find(t), find(first[k])
                if a != b:
                    parent[a] = b
            else:
                first[k] = t
    groups = {}
    for t in range(len(tris)):
        groups.setdefault(find(t), []).append(t)
    return [np.array(g) for g in sorted(groups.values(), key=lambda g: g[0])]


def parts_of(f, h, uv, tris) -> list:
    """[(an island's triangles, "legs", "tail", "ears", "head" or "body")] from where each lies on the horse (`f` along
    it, tail 0 to muzzle 1; `h` up, ground 0 to the ears' tips 1): legs touch the ground; the tail is the part furthest
    back above the ground; the ears the highest; the head and neck the part furthest forward; the body the rest."""
    stats = []
    for g in _islands(uv, tris):
        vs = np.unique(tris[g].ravel())
        stats.append((g, float(h[vs].min()), float(f[vs].mean()), float(h[vs].max())))
    legs = [k for k, s in enumerate(stats) if s[1] < 0.02]
    rest = [k for k, s in enumerate(stats) if s[1] >= 0.02]
    if not legs or len(rest) < 4:
        # not a game rule: the horse model this paints (the game's scenery horse, as the builder joins it)
        raise PaintError("the model's parts aren't the horse's: no legs, or too few other parts")
    tail = min(rest, key=lambda k: stats[k][2])
    ears = max((k for k in rest if k != tail), key=lambda k: stats[k][3])
    head = max((k for k in rest if k not in (tail, ears)), key=lambda k: stats[k][2])
    names = {tail: "tail", ears: "ears", head: "head"}
    return [(stats[k][0], "legs" if k in legs else names.get(k, "body")) for k in range(len(stats))]


def _normals(points, tris):
    """Each corner's normal: the faces' normals around it summed (their areas weigh them), made one long."""
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    e1, e2 = b - a, c - a
    face = np.stack([e1[:, 1] * e2[:, 2] - e1[:, 2] * e2[:, 1], e1[:, 2] * e2[:, 0] - e1[:, 0] * e2[:, 2],
                     e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]], 1)
    n = np.zeros_like(points)
    for k in range(3):
        np.add.at(n, tris[:, k], face)
    length = np.sqrt(n[:, 0] * n[:, 0] + n[:, 1] * n[:, 1] + n[:, 2] * n[:, 2])
    length[length == 0] = 1.0
    return n / length[:, None]


def _mix(a, b, t):
    t = np.clip(t, 0.0, 1.0)[..., None]
    return np.asarray(a, np.float64) * (1.0 - t) + np.asarray(b, np.float64) * t


# directions a spot looks out along for the shade the horse casts on itself: every (i, j, k) of -2..2 but nought, made
# one long (124 of them; integer steps and square roots only, the same on every PC)
_DIRS = np.array([(i, j, k) for i in range(-2, 3) for j in range(-2, 3) for k in range(-2, 3) if (i, j, k) != (0, 0, 0)],
                 np.float64)
_DIRS = _DIRS / np.sqrt(_DIRS[:, 0] * _DIRS[:, 0] + _DIRS[:, 1] * _DIRS[:, 1] + _DIRS[:, 2] * _DIRS[:, 2])[:, None]


def occlusion(points, normals, tris, reach: float):
    """Each corner's open sky, 0 to 1: of the directions around its normal (cosine-weighted), how many leave without
    meeting another of the horse's triangles within `reach` (Moller-Trumbore, each direction in turn: the sums in a
    fixed order). The belly, the inner legs and under the neck come out darker, as a painter shades them."""
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    e1, e2 = b - a, c - a
    out = np.zeros(len(points))
    total = np.zeros(len(points))
    lift = points + normals * (reach * 0.01)              # (off its own surface, so it never meets its own triangles)
    for d in _DIRS:
        cos = normals[:, 0] * d[0] + normals[:, 1] * d[1] + normals[:, 2] * d[2]
        use = cos > 0.1
        if not use.any():
            continue
        o = lift[use]
        pv = np.array([d[1] * e2[:, 2] - d[2] * e2[:, 1], d[2] * e2[:, 0] - d[0] * e2[:, 2],
                       d[0] * e2[:, 1] - d[1] * e2[:, 0]]).T                       # d x e2, each triangle
        det = e1[:, 0] * pv[:, 0] + e1[:, 1] * pv[:, 1] + e1[:, 2] * pv[:, 2]
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o[:, None, :] - a[None, :, :]                                          # [corners, triangles, 3]
        u = (tv[..., 0] * pv[:, 0] + tv[..., 1] * pv[:, 1] + tv[..., 2] * pv[:, 2]) * inv
        qv = np.stack([tv[..., 1] * e1[:, 2] - tv[..., 2] * e1[:, 1], tv[..., 2] * e1[:, 0] - tv[..., 0] * e1[:, 2],
                       tv[..., 0] * e1[:, 1] - tv[..., 1] * e1[:, 0]], -1)
        v = (d[0] * qv[..., 0] + d[1] * qv[..., 1] + d[2] * qv[..., 2]) * inv
        t = (e2[:, 0] * qv[..., 0] + e2[:, 1] * qv[..., 1] + e2[:, 2] * qv[..., 2]) * inv
        hit = ok & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0) & (t > 0.0) & (t < reach)
        free = ~hit.any(1)
        out[use] = out[use] + cos[use] * free
        total[use] = total[use] + cos[use]
    total[total == 0] = 1.0
    return out / total


def _crest(p, f, nrm, tris_head, half: float):
    """The neck's crest, where the mane grows from: the head and neck part's corners on the horse's middle (its two
    halves meet there) that face up, within MANE's stretch along it, in order along it: [k, 3] points."""
    vs = np.unique(tris_head.ravel())
    on = vs[(np.abs(p[vs, 2]) <= half * 0.02) & (nrm[vs, 1] > 0.0) & (f[vs] >= MANE[0] - 0.03) & (f[vs] <= MANE[1] + 0.02)]
    return p[on[np.argsort(f[on], kind="stable")]]


def paint(points, uvs, triangles, width: int = SIZE[0], height: int = SIZE[1]) -> bytes:
    """Our picture of the horse whose mesh is `points` ([n, 3]: forward, up, side, the glTF axes the made files have),
    `uvs` ([n, 2], as the model has them: they wrap) and `triangles` ([m, 3]): a PNG of `width` x `height`, RGB."""
    p = np.asarray(points, np.float64)
    uv = np.mod(np.asarray(uvs, np.float64), 1.0)
    tris = np.asarray(triangles, np.int64)
    lo, hi = p.min(0), p.max(0)
    f = (p[:, 0] - lo[0]) / (hi[0] - lo[0])
    h = (p[:, 1] - lo[1]) / (hi[1] - lo[1])
    half = max(abs(lo[2]), abs(hi[2])) or 1.0
    s = np.abs(p[:, 2]) / half
    nrm = _normals(p, tris)
    length = hi[0] - lo[0]
    sky = occlusion(p, nrm, tris, REACH * length)
    eye = np.array([lo[0] + EYE[0] * length, lo[1] + EYE[1] * (hi[1] - lo[1]), EYE[2] * half])
    canvas = np.zeros((height, width, 3), np.float64)
    painted = np.zeros((height, width), bool)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    grain = 0.04 * noise(xx / 2.5, yy / 2.5, 11) + 0.03 * noise(xx / 6.0, yy / 6.0, 23) + \
        0.08 * noise(xx / 16.0, yy / 16.0, 29) + 0.06 * noise(xx / 40.0, yy / 40.0, 31)
    strands = noise(xx / 1.6, yy / 14.0, 37) * 0.5 + noise(xx / 14.0, yy / 1.6, 41) * 0.5
    parts = parts_of(f, h, uv, tris)
    crest = _crest(p, f, nrm, tris[next(g for g, part in parts if part == "head")], half)
    for group, part in parts:
        for t in tris[group]:
            q = uv[t] * [width, height]
            x0, y0 = (int(np.floor(v)) for v in q.min(0))
            x1, y1 = (int(np.ceil(v)) for v in q.max(0))
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, width - 1), min(y1, height - 1)
            if x1 < x0 or y1 < y0:
                continue
            (ax, ay), (bx, by), (cx, cy) = q
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if den == 0:
                continue
            px, py = xx[y0:y1 + 1, x0:x1 + 1] + 0.5, yy[y0:y1 + 1, x0:x1 + 1] + 0.5
            w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
            w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            w = np.stack([w0, w1, w2], -1)[inside]
            pf = w[:, 0] * f[t[0]] + w[:, 1] * f[t[1]] + w[:, 2] * f[t[2]]     # (where on the horse: along, up, side)
            ph = w[:, 0] * h[t[0]] + w[:, 1] * h[t[1]] + w[:, 2] * h[t[2]]
            ps = w[:, 0] * s[t[0]] + w[:, 1] * s[t[1]] + w[:, 2] * s[t[2]]
            pk = w[:, 0] * sky[t[0]] + w[:, 1] * sky[t[1]] + w[:, 2] * sky[t[2]]
            n = w[:, 0:1] * nrm[t[0]] + w[:, 1:2] * nrm[t[1]] + w[:, 2:3] * nrm[t[2]]
            nl = np.sqrt(n[:, 0] * n[:, 0] + n[:, 1] * n[:, 1] + n[:, 2] * n[:, 2])
            nl[nl == 0] = 1.0
            n_up, n_fwd = n[:, 1] / nl, n[:, 0] / nl
            g = grain[y0:y1 + 1, x0:x1 + 1][inside]
            st = strands[y0:y1 + 1, x0:x1 + 1][inside]
            col = _coat(n_up, n_fwd, pk, g)
            if part == "legs":
                col = _mix(col, col * 0.62, (0.42 - ph) / 0.12)          # darker down the leg, then black points
                col = _mix(col, POINTS, (0.29 - ph) / 0.07)
                col = _mix(col, HOOF, (0.034 - ph) / 0.008)              # dark grey hooves
            elif part == "tail":
                col = _hair(st, n_up) * (0.75 + 0.25 * pk)[:, None]
            elif part == "ears":
                col = _mix(col, POINTS, (ph - 0.95) / 0.03)              # black ear tips
            elif part == "head":
                below = np.interp(pf, (crest[:, 0] - lo[0]) / length, (crest[:, 1] - lo[1]) / (hi[1] - lo[1])) - ph
                fall = MANE[2] * (0.6 + 0.4 * np.clip((pf - MANE[0]) / (MANE[1] - MANE[0]), 0.0, 1.0)) \
                    * (1.0 + 0.35 * st)                                  # (longer toward the head, its ends ragged)
                mane = (fall - below) / (MANE[2] * 0.45) * np.clip((MANE[1] - pf) / 0.015, 0.0, 1.0) \
                    * np.clip((pf - MANE[0]) / 0.02, 0.0, 1.0)            # (it falls about MANE[2] below the crest)
                forelock = (ph - 0.915) / 0.025 * np.clip((0.33 - ps) / 0.08, 0.0, 1.0)
                col = _mix(col, _hair(st, n_up), np.maximum(mane, forelock))
                col = _mix(col, MUZZLE, (pf - 0.925) / 0.045)            # a dark muzzle
                ex = (eye[0] - (lo[0] + pf * length)) / length
                ey = (eye[1] - (lo[1] + ph * (hi[1] - lo[1]))) / length
                ez = (eye[2] - ps * half) / length
                d = np.sqrt(ex * ex + ey * ey + ez * ez)
                col = _mix(col, col * 0.7, (2.0 * EYE_RADIUS - d) / EYE_RADIUS)   # the hollow round the eye
                col = _mix(col, EYE_COLOUR, (EYE_RADIUS - d) / (EYE_RADIUS * 0.4))
            region = canvas[y0:y1 + 1, x0:x1 + 1]
            region[inside] = col
            painted[y0:y1 + 1, x0:x1 + 1] |= inside
    canvas = _padded(canvas, painted, PAD)
    rgb = np.clip(np.floor(canvas + 0.5), 0, 255).astype(np.uint8)
    return png_bytes(rgb.tobytes(), width, height)


def _coat(n_up, n_fwd, sky, grain):
    """The coat at a spot facing up by `n_up` and forward by `n_fwd`, `sky` of it open (occlusion): lit from above,
    shaded where the horse hides it, a sheen along the back, its hair's grain on it."""
    lit = np.clip(0.72 + 0.26 * n_up + 0.10 * n_fwd, 0.45, 1.0) * (0.38 + 0.68 * sky)
    col = _mix(COAT_DARK, COAT, (lit - 0.30) / 0.45)
    col = _mix(col, COAT_LIGHT, (lit - 0.84) / 0.20)
    return col * (1.0 + grain)[:, None]


def _hair(strands, n_up):
    """The mane's, the forelock's and the tail's black hair, its strands a little lighter in places."""
    shine = np.clip(strands * 0.9 + 0.1 * n_up, 0.0, 1.0) * 0.35
    return _mix(POINTS, POINTS_SHINE, shine)


def _padded(canvas, painted, steps: int):
    """Each part's colour run on `steps` pixels past its edge (the nearest painted neighbour's), the rest the coat."""
    out, done = canvas.copy(), painted.copy()
    for _ in range(steps):
        acc = np.zeros_like(out)
        cnt = np.zeros(done.shape, np.float64)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            moved = np.roll(np.roll(done, dy, 0), dx, 1)
            col = np.roll(np.roll(out, dy, 0), dx, 1)
            acc += col * moved[..., None]
            cnt += moved
        grow = (~done) & (cnt > 0)
        out[grow] = acc[grow] / cnt[grow][:, None]
        done |= grow
    out[~done] = COAT
    return out


def with_own_picture(raw: bytes) -> bytes:
    """A made .glb (rusemod.horsesquad's) with its horse's picture ours: the material showing the game's horse picture
    (its extras' rusemod_texture names HORSE_TEXTURE) shows paint()'s picture of the horse's own mesh instead, under
    HORSE_MATERIAL (no game picture named in it any more); every other byte's meaning as it was. PaintError when the
    file has no such material."""
    from .gltf import glb_views, pack_glb
    doc, views = glb_views(raw)
    mats = [k for k, m in enumerate(doc.get("materials", []))
            if HORSE_TEXTURE in str((m.get("extras") or {}).get("rusemod_texture", "")).lower()]
    if len(mats) != 1:
        # not a game rule: the made file this paints (the builder's, with the game's horse in it)
        raise PaintError("the file hasn't the horse's one material")
    k = mats[0]
    pts, uvs, tris = [], [], []
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("material") != k:
                continue
            base = sum(len(x) for x in pts)
            pts.append(_read(doc, views, prim["attributes"]["POSITION"]))
            uvs.append(_read(doc, views, prim["attributes"]["TEXCOORD_0"]))
            tris.append(_read(doc, views, prim["indices"]).reshape(-1, 3).astype(np.int64) + base)
    if not pts:
        # not a game rule: the made file this paints
        raise PaintError("the file's horse has no draw")
    png = paint(np.concatenate(pts), np.concatenate(uvs), np.concatenate(tris))
    mat = doc["materials"][k]
    image = doc["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
    views[doc["images"][image]["bufferView"]] = png
    doc["images"][image]["name"] = HORSE_MATERIAL
    mat["name"] = HORSE_MATERIAL
    mat["extras"] = {"rusemod_picture": HORSE_MATERIAL}
    return pack_glb(doc, views)


def _read(doc, views, index):
    a = doc["accessors"][index]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    kind = {5126: "<f4", 5123: "<u2", 5125: "<u4", 5121: "u1"}[a["componentType"]]
    data = views[a["bufferView"]]
    return np.frombuffer(data, dtype=kind, count=a["count"] * n, offset=a.get("byteOffset", 0)).reshape(a["count"], n)
