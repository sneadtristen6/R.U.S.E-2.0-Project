"""The model importer on whole arrays (numpy): rusemod.modelin's own sums, in its order, for every point of a model at
once instead of one at a time, so a model is read, fitted and saved to the same bytes many times sooner.
rusemod.modelin asks for this module through its whole_arrays() and keeps its own loops: they are what every piece
here is checked against (tests/test_modelinnp.py), and what runs without numpy.

How the same bytes are kept:
  - each +, -, *, / and square root of numpy's float64 gives the same bits as Python's float, and every sum is
    taken in the loops' order: a running sum where they add item after item (a vertex's normal, triangle after
    triangle), the same terms in the same order everywhere else;
  - Python's sum() of a few floats (a point through its node's matrix, a normal's length) has been no plain running
    sum since Python 3.12: it keeps what each addition loses apart and adds that back at the end (Neumaier's way).
    py_sum adds as this Python's sum() adds, and this module refuses to load (the ImportError a missing numpy gives,
    so the loops do the work) when sum() gives anything else on a set of awkward cases;
  - the lowest and the highest of a list are the first of the equal ones, as min() and max() keep them (0.0 and -0.0
    are equal, and which of them comes first is what min() gives);
  - a 32-bit float is the 64-bit one rounded to the nearest, as struct's "<f" rounds it;
  - what comes out is what the loops give: lists of tuples of Python floats and ints, a normal with no length being
    the loops' own (0.0, 0.0, 1.0) (so a pickle of a fitted model is the same bytes too);
  - which way a model faces isn't worked out here at all: prepare asks modelin.facing itself, on the model's own lists
    (its rules have one home).
A function here gives None for what it leaves to the loops: a file or a model it isn't made for (numbers that aren't
Python floats or ints where the loops have them, a point that isn't finite, a broken index, an odd accessor...); the
loops then give their own answer, or their own error.

A list made here (a Mesh's or a Part's) remembers the array it was made from, with a copy of the list itself: while the
list still holds the very tuples it was made with (a tuple can't change), the next step takes the array instead of
reading the list again (a read mesh lets its arrays go as fitting takes them: they are needed once). A list changed in
any way (an item replaced, added or taken away) is read again, number by number."""
from __future__ import annotations

import math
import operator
import random
import struct
from itertools import chain

from .numpy2 import np

_FLOAT = {5126: "<f4"}                                  # glTF component types read here: 32-bit floats,
_INDEX = {5121: "<u1", 5123: "<u2", 5125: "<u4"}        # and the unsigned whole numbers indices are kept in
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# --- Python's sum() of a few floats, for whole arrays ---------------------------------------------------------------
def _compensated(terms: list):
    """sum() of floats as Python 3.12 adds them (Neumaier): the sum starts as 0 + the first term (so a -0.0 alone
    comes out 0.0); then each term's addition, with what it loses kept apart; that is added back at the end when it
    isn't 0 and is finite."""
    s = 0.0 + terms[0]
    lost = np.zeros(np.shape(s))
    for x in terms[1:]:
        t = s + x
        lost = lost + np.where(np.abs(s) >= np.abs(x), (s - t) + x, (x - t) + s)
        s = t
    return np.where((lost != 0.0) & np.isfinite(lost), s + lost, s)


def _running(terms: list):
    """sum() of floats as Python 3.11 adds them: a running sum from 0."""
    s = 0.0 + terms[0]
    for x in terms[1:]:
        s = s + x
    return s


_SUM = _compensated if sum([1.0, 1e100, 1.0, -1e100]) == 2.0 else _running


def py_sum(terms: list):
    """sum(terms) of Python floats for whole arrays at once: terms[k] is the k-th term of every sum (float64 arrays of
    one shape, or a float that every sum has), added as this Python's sum() adds them."""
    with np.errstate(all="ignore"):
        return _SUM([np.asarray(t, dtype=np.float64) for t in terms])


def _sum_is_known() -> bool:
    """py_sum gives what sum() gives, bit for bit, on awkward sums: signed zeros, terms that cancel, a small term
    beside big ones, infinities, a sum past the largest float, and random ones."""
    big, tiny, inf = 1e308, 5e-324, math.inf
    cases = [[0.0], [-0.0], [-0.0, -0.0], [-0.0, 0.0, -0.0], [0.0, -0.0, -0.0, -0.0], [1.0, 1e100, 1.0, -1e100],
             [1e16, 1.0, -1e16], [0.1, 0.2, 0.3], [3.0, -1e-16, 1e-16, 2.0], [big, big, -big], [-big, -big, big, 1.0],
             [inf, 1.0], [inf, -inf], [-inf, 2.0, 3.0], [tiny, -tiny, tiny], [1e-300, 1e300, -1e300, 1e-300],
             [2.0 ** 53, 1.0, 1.0], [-2.0 ** 53, -1.0, 0.5, 0.25], [1.0, -1.0, 1e-30], [0.5, 2.0 ** 52, -2.0 ** 52]]
    rnd = random.Random(2026)
    specials = [0.0, -0.0, 1.0, -1.0, tiny, -tiny, big, -big, 1e16, -1e16, 2.0 ** 53, 0.1, 1e-16, inf, -inf]
    for _ in range(600):
        case = []
        for _ in range(rnd.choice((2, 3, 4))):
            k = rnd.random()
            case.append(rnd.choice(specials) if k < 0.2 else rnd.uniform(-1, 1) * 10.0 ** rnd.randint(-30, 30)
                        if k < 0.6 else rnd.uniform(-1e3, 1e3))
        cases.append(case)
    for width in sorted({len(c) for c in cases}):
        group = [c for c in cases if len(c) == width]
        got = py_sum([np.array([c[k] for c in group]) for k in range(width)])
        want = np.array([sum(c) for c in group])
        same = (got.view(np.uint64) == want.view(np.uint64)) | (np.isnan(got) & np.isnan(want))
        if not same.all():
            return False
    return True


if not _sum_is_known():
    raise ImportError("this Python's sum() of floats isn't the one checked here: the importer's loops do the work")


# --- the lowest and the highest, as min() and max() keep them -------------------------------------------------------
def _lowest(columns: list) -> float:
    """min() of the numbers of several columns in turn (none empty, none NaN): the first of the lowest."""
    best = None
    for c in columns:
        j = int(np.flatnonzero(c == c.min())[0])      # (0.0 and -0.0 are equal: the first of them)
        x = float(c[j])
        if best is None or x < best:
            best = x
    return best


def _highest(columns: list) -> float:
    """max() of the numbers of several columns in turn (none empty, none NaN): the first of the highest."""
    best = None
    for c in columns:
        j = int(np.flatnonzero(c == c.max())[0])
        x = float(c[j])
        if best is None or x > best:
            best = x
    return best


def _box(chunks: list) -> tuple:
    """modelin._box over the points of several (n, 3) arrays in turn."""
    return tuple(_lowest([p[:, i] for p in chunks]) for i in range(3)) + \
        tuple(_highest([p[:, i] for p in chunks]) for i in range(3))


# --- lists of tuples to arrays and back ---------------------------------------------------------------------------
def _floats(seq, width: int):
    """A list of `width`-long tuples of Python floats as an (n, width) float64 array; None when it isn't one (a tuple of
    another length, a number that isn't a Python float) or a number isn't finite."""
    try:
        n = len(seq)
        if not n:
            return np.zeros((0, width))
        if set(map(len, seq)) != {width} or set(map(type, chain.from_iterable(seq))) != {float}:
            return None
        a = np.fromiter(chain.from_iterable(seq), dtype=np.float64, count=n * width).reshape(n, width)
    except (TypeError, ValueError):
        return None
    return a if np.isfinite(a).all() else None


def _ints(seq, width: int):
    """A list of `width`-long tuples of Python ints as an (n, width) int64 array; None when it isn't one."""
    try:
        n = len(seq)
        if not n:
            return np.zeros((0, width), dtype=np.int64)
        if set(map(len, seq)) != {width} or set(map(type, chain.from_iterable(seq))) != {int}:
            return None
        return np.fromiter(chain.from_iterable(seq), dtype=np.int64, count=n * width).reshape(n, width)
    except (TypeError, ValueError, OverflowError):
        return None


def _rows(a) -> list:
    """An (n, width) array of float64 (or int64) as a list of tuples of Python floats (ints), a row each: struct's own
    unpacking of the array's bytes, which makes each row's tuple at once (the same numbers, sooner than zipping
    columns)."""
    if not len(a):
        return []       # (a view of no bytes can't be cast)
    whole = a.dtype.kind == "i"
    a = np.ascontiguousarray(a, dtype="<i8" if whole else "<f8")
    return list(struct.iter_unpack(f"<{a.shape[1]}{'q' if whole else 'd'}", memoryview(a).cast("B")))


_KEPT = "_whole_arrays"     # a Mesh's or a Part's {field: (a copy of the list made here, the array it was made from)}


def _keep(owner, field: str, array) -> None:
    """Remember the array owner.<field> (a list just made from it) was made from."""
    owner.__dict__.setdefault(_KEPT, {})[field] = (list(getattr(owner, field)), array)


def _kept(owner, field: str, take: bool = False):
    """The array owner.<field> was made from, while the list holds the very tuples it was made with; else None.
    `take`: forgotten by the owner as it is given (the next step needs it once: it isn't held for the owner's life)."""
    try:
        kept = owner.__dict__[_KEPT]
        made, array = kept.pop(field) if take else kept[field]
        now = getattr(owner, field)
        return array if len(now) == len(made) and all(map(operator.is_, now, made)) else None
    except (AttributeError, KeyError, TypeError):
        return None


def _numbers(owner, field: str, width: int, whole: bool = False, take: bool = False):
    """owner.<field> as an array: the one it was made from (_kept), else read again (_floats, or _ints: whole)."""
    array = _kept(owner, field, take)
    if array is not None:
        return array
    seq = getattr(owner, field)
    return _ints(seq, width) if whole else _floats(seq, width)


def _finite(*columns) -> bool:
    return all(np.isfinite(c).all() for c in columns)


# --- reading a .glb (modelin.read_glb) ----------------------------------------------------------------------------
def accessor(doc: dict, binary: bytes, i, kinds: dict, width: int):
    """Accessor `i`'s values as modelin.glb_accessor reads them, as a (count, width) array: 32-bit floats (kinds
    _FLOAT) as float64, unsigned whole numbers (_INDEX) as int64. None for one of another kind or width, laid out
    otherwise (sparse, in another buffer, normalized whole numbers...) or reaching past the data: glb_accessor
    reads it, or says what is wrong with it."""
    try:
        a = doc["accessors"][i]
        view = doc["bufferViews"][a["bufferView"]]
        code, kind, count = a["componentType"], a["type"], a["count"]
    except (KeyError, IndexError, TypeError):
        return None
    if not isinstance(a, dict) or not isinstance(view, dict) or "sparse" in a or type(code) is not int:
        return None
    dt = kinds.get(code)
    if dt is None or _WIDTH.get(kind) != width or (dt != "<f4" and a.get("normalized")) or view.get("buffer", 0) != 0:
        return None
    size = np.dtype(dt).itemsize
    stride = view.get("byteStride") or size * width
    start, more = view.get("byteOffset", 0), a.get("byteOffset", 0)
    if not all(type(v) is int for v in (count, stride, start, more)) or count < 0 or stride <= 0 \
            or min(start, more) < 0:
        return None
    base = start + more
    out = np.float64 if dt == "<f4" else np.int64
    if count == 0:
        return np.zeros((0, width), dtype=out)
    if base + (count - 1) * stride + size * width > len(binary):
        return None
    return np.ndarray((count, width), dtype=dt, buffer=binary, offset=base, strides=(stride, size)).astype(out)


def _units(plain, v: tuple):
    """modelin._unit for every row of the columns v = (x, y, z): (x, y, z) / its length, or modelin's own (0.0, 0.0,
    1.0) where the length is 1e-12 or less. (A list of tuples, its (n, 3) array), or None where a number isn't
    finite."""
    with np.errstate(all="ignore"):
        n = np.sqrt(py_sum([v[0] * v[0], v[1] * v[1], v[2] * v[2]]))
        long = n > 1e-12
        q = np.stack([c / n for c in v], axis=1)
    if not (_finite(*v) and np.isfinite(q[long]).all()):
        return None
    q[~long] = (0.0, 0.0, 1.0)
    out = _rows(q)
    if not long.all():
        flat = plain._unit((0.0, 0.0, 0.0))       # (the very tuple _unit gives)
        for i in np.flatnonzero(~long).tolist():
            out[i] = flat
    return out, q


def mesh(plain, doc: dict, binary: bytes, prim: dict, matrix: list, name: str):
    """One triangle primitive of a .glb as modelin.read_glb's loops read it: a Mesh named `name` (its points through
    `matrix`, z up; its triangles; its uvs, v up the picture; its own normals, unit length), lists of tuples as theirs.
    None for one it leaves to them."""
    try:
        attrs = prim["attributes"]
        position = attrs["POSITION"]
        uv, normal, indexed = "TEXCOORD_0" in attrs, "NORMAL" in attrs, "indices" in prim
        m = list(matrix)
    except (KeyError, TypeError):
        return None
    if len(m) != 16 or not all(type(v) in (int, float) and math.isfinite(v) and abs(v) <= 2.0 ** 53 for v in m):
        return None
    p = accessor(doc, binary, position, _FLOAT, 3)
    idx = accessor(doc, binary, prim["indices"], _INDEX, 1) if indexed else None
    uvs = accessor(doc, binary, attrs["TEXCOORD_0"], _FLOAT, 2) if uv else None
    nrm = accessor(doc, binary, attrs["NORMAL"], _FLOAT, 3) if normal else None
    if p is None or (indexed and idx is None) or (uv and uvs is None) or (normal and nrm is None) or \
            not _finite(p, *([uvs] if uv else []), *([nrm] if normal else [])):
        return None
    with np.errstate(all="ignore"):     # sum(matrix[c * 4 + r] * (p[c] if c < 3 else 1.0) for c in range(4))
        x, y, z = (py_sum([m[r] * p[:, 0], m[4 + r] * p[:, 1], m[8 + r] * p[:, 2], m[12 + r] * 1.0])
                   for r in range(3))
        z = -z
    if not _finite(x, y, z):
        return None
    own = None
    if normal:
        nm = plain._normal_matrix(matrix)
        if not all(type(v) is float and math.isfinite(v) for row in nm for v in row):
            return None
        with np.errstate(all="ignore"):     # sum(nm[r][c] * n[c] for c in range(3))
            a, b, c = (py_sum([nm[r][0] * nrm[:, 0], nm[r][1] * nrm[:, 1], nm[r][2] * nrm[:, 2]]) for r in range(3))
            c = -c
        own = _units(plain, (a, c, b))
        if own is None:
            return None
    index = idx[:, 0] if indexed else np.arange(len(p), dtype=np.int64)
    tri = index[:len(index) // 3 * 3].reshape(-1, 3)
    points = np.stack([x, z, y], axis=1)
    flipped = np.stack([uvs[:, 0], 1.0 - uvs[:, 1]], axis=1) if uv else None
    tris = _rows(tri)
    out = plain.Mesh(name, _rows(points), tris, _rows(flipped) if uv else [], [prim.get("material", -1)] * len(tris),
                     own[0] if normal else [])
    _keep(out, "positions", points)
    _keep(out, "triangles", tri)
    if uv:
        _keep(out, "uvs", flipped)
    if normal:
        _keep(out, "normals", own[1])
    return out


# --- fitting to a unit (modelin.prepare) --------------------------------------------------------------------------
def _mesh(m) -> dict | None:
    """A mesh's points, own normals, uvs and triangles as arrays, the triangles as many as its materials pair with
    (zip), and those materials; None for a mesh the loops are left with. The arrays a read mesh kept are taken (fitting
    needs them once; the mesh's lists stay as they are)."""
    try:
        points = _numbers(m, "positions", 3, take=True)
        normals = _numbers(m, "normals", 3, take=True) if m.normals else np.zeros((0, 3))
        uvs = _numbers(m, "uvs", 2, take=True) if m.uvs else None
        tris = _numbers(m, "triangles", 3, whole=True, take=True)
        mats = m.face_materials or [-1] * len(m.triangles)
        if points is None or not len(points) or normals is None or (m.uvs and uvs is None) or tris is None:
            return None
        used = min(len(tris), len(mats))
        mats = list(mats[:used])
        kinds = set(mats)
    except (TypeError, ValueError, AttributeError):
        return None
    tris = tris[:used]
    if used and (int(tris.min()) < 0 or int(tris.max()) >= len(points)
                 or (uvs is not None and int(tris.max()) >= len(uvs))):
        return None
    return {"points": points, "normals": normals, "uvs": uvs, "tris": tris, "mats": mats, "kinds": kinds}


def _roles(plain, model, data: list) -> list:
    """modelin.roles."""
    out = [plain.named_role(m.name) for m in model.meshes]
    turret = [d["points"] for d, r in zip(data, out) if r == plain.TURRET]
    if turret:
        tb = _box(turret)
        for i, d in enumerate(data):
            if out[i] is None:
                b = _box([d["points"]])
                cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
                if tb[0] <= cx <= tb[3] and tb[1] <= cy <= tb[4] and b[2] >= tb[2] - 0.02 * (tb[5] - tb[2]):
                    out[i] = plain.TURRET
    return [r or plain.HULL for r in out]


def _turn_ring(points) -> tuple[float, float]:
    """modelin.turn_ring."""
    b = _box([points])
    low = points[points[:, 2] <= b[2] + (b[5] - b[2]) / 6]
    lb = _box([low])
    return (lb[0] + lb[3]) / 2, (lb[1] + lb[4]) / 2


def _smooth(x, y, z, a, b, c, need):
    """modelin.smooth_normals for the points `need` marks of a part whose triangles are (a, b, c): each the sum, in
    triangle order, of the (b - a) x (c - a) of the triangles it is a corner of (a running sum from 0.0), then made
    unit length. (x, y, z columns for every point (0 where not needed), and where the sum has no length)."""
    ux, uy, uz = x[b] - x[a], y[b] - y[a], z[b] - z[a]
    vx, vy, vz = x[c] - x[a], y[c] - y[a], z[c] - z[a]
    n = np.stack([uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx], axis=1)
    count, corners = len(x), len(a) * 3
    # each corner (triangle t's a, b, c in turn: entry 3t, 3t + 1, 3t + 2) of a point that needs it
    every = np.stack([a, b, c], axis=1).reshape(-1)
    entry = np.flatnonzero(need[every])
    point = every[entry]
    acc = np.zeros((count, 3))
    if not len(entry):      # (a point with no triangle: its sum stays 0)
        return acc[:, 0], acc[:, 1], acc[:, 2], np.ones(count, dtype=bool)
    # in order point by point, each point's corners in triangle order (the keys are all different: no sort's order
    # among equals is relied on)
    key = np.sort(point * corners + entry)
    point, entry = key // corners, key % corners
    first = np.flatnonzero(np.r_[True, point[1:] != point[:-1]])
    nth = np.arange(len(point)) - np.repeat(first, np.diff(np.r_[first, len(point)]))
    start = np.zeros(count, dtype=np.int64)
    start[point[first]] = first
    # the n-th corner of every point is added at once, n = 0, 1, 2...: each point's sum in its triangles' order
    order = np.sort(nth * count + point)
    by_nth = np.bincount(order // count)
    at = 0
    for k, many in enumerate(by_nth.tolist()):
        p = order[at:at + many] % count
        at += many
        acc[p] = acc[p] + n[entry[start[p] + k] // 3]
    sx, sy, sz = acc[:, 0], acc[:, 1], acc[:, 2]
    with np.errstate(all="ignore"):
        length = np.sqrt(sx * sx + sy * sy + sz * sz)
        flat = length == 0.0
        return sx / length, sy / length, sz / length, flat


def _points(distinct: list, starts, total: int, f: list, r: tuple, scale: float, shift: tuple, lift: float):
    """Every point of the meshes (each mesh once, starting at its number in `starts`) as prepare's loops make it:
    placed (place), its uv (u, 1 - v; (0, 1) without uvs), whether it has its own normal, that normal turned (turn), and
    where turn gives _unit's own (0.0, 0.0, 1.0). None where a number isn't finite. (Its working arrays end here.)"""
    with np.errstate(all="ignore"):
        pts = np.concatenate([d["points"] for d in distinct])
        placed = ((pts[:, 0] * f[0] + pts[:, 1] * f[1]) * scale + shift[0],
                  (pts[:, 0] * r[0] + pts[:, 1] * r[1]) * scale + shift[1], pts[:, 2] * scale + lift)
        del pts
        uv = np.zeros((total, 2))
        has = np.zeros(total, dtype=bool)
        nrm = np.zeros((total, 3))
        for d, at in zip(distinct, starts):
            k = len(d["points"])
            if d["uvs"] is not None:
                u = d["uvs"][:k]
                uv[at:at + len(u)] = u
            g = d["normals"][:k]
            has[at:at + len(g)] = True
            nrm[at:at + len(g)] = g
        flipped = (uv[:, 0].copy(), 1.0 - uv[:, 1])
        del uv
        a = nrm[:, 0] * f[0] + nrm[:, 1] * f[1]
        b = nrm[:, 0] * r[0] + nrm[:, 1] * r[1]
        c = nrm[:, 2].copy()
        del nrm
        n = np.sqrt(py_sum([a * a, b * b, c * c]))
        long = n > 1e-12
        turned = (a / n, b / n, c / n)
    if not (_finite(*placed) and all(np.isfinite(q[has & long]).all() for q in turned)):
        return None
    return placed, flipped, has, turned, has & ~long


def _numbered(entries: list, total: int):
    """A part's points, as prepare's loops number them (in the order its triangles first name them: the triangles of
    `entries` [(the mesh's first point's number, its triangles, the ones in this part)] in turn, each one's corners
    a, b, c), and its triangles in those numbers. (Its working arrays end here.)"""
    corners = np.concatenate([tris[sel] + at for at, tris, sel in entries]).reshape(-1)
    place = np.arange(len(corners))
    first = np.full(total, len(corners), dtype=np.int64)
    np.minimum.at(first, corners, place)
    points = corners[first[corners] == place]
    number = np.empty(total, dtype=np.int64)
    number[points] = np.arange(len(points))
    return points, number[corners].reshape(-1, 3)


def prepare(plain, model, folders: list, like: dict, size: float, side: int):
    """modelin.prepare: `model` fitted to a unit, its pictures and its report, the same as the loops make them; None
    for a model left to them."""
    meshes = model.meshes
    if not meshes:
        return None
    seen, data, offset, total = {}, [], {}, 0
    for m in meshes:
        if id(m) not in seen:
            seen[id(m)] = _mesh(m)
            if seen[id(m)] is None:
                return None
            offset[id(m)] = total
            total += len(seen[id(m)]["points"])
        data.append(seen[id(m)])
    parts = _roles(plain, model, data)
    # which way it faces: modelin.facing itself, its rules kept in one place (2026-10-08: they were still changing),
    # on the model's own lists (a .glb read here hands its points as lists too: nothing is built for it)
    axis, sign = plain.facing(model, parts, like)
    f = [0.0, 0.0, 0.0]
    f[axis] = float(sign)
    r = (f[1], -f[0], 0.0)
    hull = [d["points"] for d, k in zip(data, parts) if k == plain.HULL] or [d["points"] for d in data]
    with np.errstate(all="ignore"):
        along = [p[:, 0] * f[0] + p[:, 1] * f[1] for p in hull]
    if not _finite(*along):
        return None
    length = _highest(along) - _lowest(along)
    if length <= 0:
        return None     # (the loops say: the model has no length)
    scale = like["length"] * size / length
    turret = [i for i, k in enumerate(parts) if k == plain.TURRET]
    if turret:
        main = max(turret, key=lambda i: len(meshes[i].positions))
        cx, cy = _turn_ring(data[main]["points"])
        ring = ((cx * f[0] + cy * f[1]) * scale, (cx * r[0] + cy * r[1]) * scale)
        shift = (like["pivot"][0] - ring[0], like["pivot"][1] - ring[1])
    else:  # no turret: its middle where the unit's is
        mid = (_highest(along) + _lowest(along)) / 2 * scale
        with np.errstate(all="ignore"):
            side_mid = [p[:, 0] * r[0] + p[:, 1] * r[1] for p in hull]
        if not _finite(*side_mid):
            return None
        shift = (like.get("middle", like["pivot"][0]) - mid, -(_highest(side_mid) + _lowest(side_mid)) / 2 * scale)
    low = _lowest([d["points"][:, 2] for d in data])
    lift = like["ground"] - low * scale
    every = _points([seen[k] for k in offset], offset.values(), total, f, r, scale, shift, lift)
    if every is None:
        return None
    (px, py, pz), (uu, vv), has, (tx, ty, tz), given_flat = every

    # each mesh's triangles by picture (pic_of.get(material, -1)): the pictures first, as the loops make them
    pictures, pic_of, missing, own_alpha, notes = plain.fit_pictures(model, folders, side)
    groups: dict = {}
    for m, d, k in zip(meshes, data, parts):
        if not len(d["tris"]):
            continue
        look = {mk: pic_of.get(mk, -1) for mk in d["kinds"]}
        if len(look) == 1:
            pics = np.full(len(d["tris"]), next(iter(look.values())), dtype=np.int64)
        else:
            pics = np.fromiter(map(look.__getitem__, d["mats"]), dtype=np.int64, count=len(d["mats"]))
        for pic in sorted(set(look.values())):
            groups.setdefault((plain.BONES[k], pic), []).append((offset[id(m)], d["tris"],
                                                                 np.flatnonzero(pics == pic)))
    unit_flat = plain._unit((0.0, 0.0, 0.0))                  # (the loops' own tuples)
    smooth_flat = plain.smooth_normals([(0.0, 0.0, 0.0)], [])[0]
    out, own_normals = [], 0
    for (bone, pic), entries in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        points, tri = _numbered(entries, total)
        ta, tb, tc = tri[:, 0], tri[:, 2], tri[:, 1]        # wound the game's way: (a, c, b)
        x, y, z = px[points], py[points], pz[points]
        own = has[points]
        nrm_out = np.stack([tx[points], ty[points], tz[points]], axis=1)
        flat_given = given_flat[points]
        flat_smooth = np.zeros(len(points), dtype=bool)
        if not own.all():
            sx, sy, sz, flat = _smooth(x, y, z, ta, tb, tc, ~own)
            work = ~own & ~flat
            if not all(np.isfinite(q[work]).all() for q in (sx, sy, sz)):
                return None
            nrm_out[~own] = np.stack([sx, sy, sz], axis=1)[~own]
            flat_smooth = ~own & flat
        nrm_out[flat_given | flat_smooth] = (0.0, 0.0, 1.0)
        normals = _rows(nrm_out)
        for i in np.flatnonzero(flat_given).tolist():
            normals[i] = unit_flat
        for i in np.flatnonzero(flat_smooth).tolist():
            normals[i] = smooth_flat
        pos_out = np.stack([x, y, z], axis=1)
        uv_out = np.stack([uu[points], vv[points]], axis=1)
        tri_out = np.stack([ta, tb, tc], axis=1)
        part = plain.Part(bone, pic, _rows(pos_out), normals, _rows(uv_out), _rows(tri_out))
        _keep(part, "positions", pos_out)
        _keep(part, "normals", nrm_out)
        _keep(part, "uvs", uv_out)
        _keep(part, "triangles", tri_out)
        out.append(part)
        own_normals += int(own.sum())
    return plain.Prepared(out, pictures, plain.fit_report(model, parts, axis, sign, scale, out, pictures, missing,
                                                          own_normals, own_alpha, notes))


def nearest(px, w: int, h: int, nw: int, nh: int):
    """modelin._sized's sampling: an RGBA picture w x h at nw x nh, each pixel the one at (x * w // nw, y * h // nh)
    (bytes). None for a picture shorter than w x h."""
    if min(w, h, nw, nh) <= 0 or len(px) < w * h * 4:
        return None
    a = np.frombuffer(px, dtype=np.uint8, count=w * h * 4).reshape(h, w, 4)
    sy = np.minimum(h - 1, np.arange(nh) * h // nh)
    sx = np.minimum(w - 1, np.arange(nw) * w // nw)
    return a[sy][:, sx].tobytes()


# --- saving (modelin.write_glb) -------------------------------------------------------------------------------------
def part_buffers(part, scale: float, mirror: bool):
    """A fitted part's POSITION, NORMAL, TEXCOORD_0 and indices packed as write_glb's loops pack them (rusemod.gltf's
    axes, positions times `scale`): ((bytes, count, lowest, highest), (bytes, count), (bytes, count), (bytes, count)).
    None for a part left to them."""
    p = _numbers(part, "positions", 3)
    n = _numbers(part, "normals", 3)
    uv = _numbers(part, "uvs", 2)
    tri = _numbers(part, "triangles", 3, whole=True)
    if p is None or not len(p) or n is None or uv is None or tri is None:
        return None
    with np.errstate(all="ignore"):     # gltf._point: (x * scale, z * scale, y * scale), or -y with no mirror
        pos = np.stack([p[:, 0] * scale, p[:, 2] * scale, (p[:, 1] if mirror else -p[:, 1]) * scale], axis=1)
        nrm = np.stack([n[:, 0] * 1.0, n[:, 2] * 1.0, (n[:, 1] if mirror else -n[:, 1]) * 1.0], axis=1)
    if not _finite(pos, nrm):
        return None
    low = [_lowest([pos[:, i]]) for i in range(3)]
    high = [_highest([pos[:, i]]) for i in range(3)]
    pos32, nrm32, uv32 = pos.astype("<f4"), nrm.astype("<f4"), uv.astype("<f4")
    if not _finite(pos32, nrm32, uv32):
        return None     # (past a 32-bit float: struct says so)
    wide = len(p) > 65535
    if len(tri) and (int(tri.min()) < 0 or int(tri.max()) > (0xFFFFFFFF if wide else 0xFFFF)):
        return None
    order = tri[:, [0, 2, 1]] if mirror else tri
    return ((pos32.tobytes(), len(p), low, high), (nrm32.tobytes(), len(n)), (uv32.tobytes(), len(uv)),
            (order.astype("<u4" if wide else "<u2").tobytes(), 3 * len(tri)))
