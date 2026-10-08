"""Models from other 3D tools into the game's form (the model importer), step one: read a model file into named
parts and fit them to a unit, ready for the build (rusemod.unitmodel) to write as the game stores its own.

Readers: Autodesk .3ds (the free-model sites' commonest format, with its pictures beside it: .tga or .png) and glTF
binary .glb (Blender's, pictures inside). A model read is a list of Mesh, z up, right-handed, in the file's own units.

Fitting (`prepare`): each part gets a role, from its name (turret, barrel...) or, failing that, from where it sits (a
part resting on the turret turns with it); everything else is the hull. The model is turned to face the game's way (its
gun points forward; else its longest side), scaled to the length of the unit it copies (times `size`), and moved so its
turret turns round the spot the copied unit's turret turns round. Pictures keep their colours, made a power of two each
way and at most `side` across (the game's own unit textures are 1024 at most); their alpha (the game's side colour
where low, shine where high) is the model's own alpha picture when a .glb material names one (`rusemod_alpha_texture`
in its extras), else a plain 144, as most of the Sherman's body. Normals: the model's own when the file has them (a
.glb's NORMAL: its weighted normals and hard edges are its shading, as other engines' importers keep them by default),
worked out from the triangles only where it has none. The report says which (no data is dropped silently).

`write_glb` saves the result as the mod's files/models/<unit>.glb: one node per bone ("chassis", "tourelle_01"), its
pictures inside, in the axes `ruse export-model` writes (rusemod.gltf), so it opens in Blender like an exported unit."""
from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path


class ModelError(ValueError):
    pass


@dataclass
class Mesh:
    """One named part of a model: its triangles' corners (indices into `positions`), and per triangle the material
    it shows (an index into Model.materials)."""
    name: str
    positions: list               # (x, y, z) per vertex
    triangles: list               # (a, b, c) per triangle
    uvs: list = field(default_factory=list)        # (u, v) per vertex, v up the picture; or empty
    face_materials: list = field(default_factory=list)  # material number per triangle (-1: none)
    normals: list = field(default_factory=list)    # the model's own (x, y, z) per vertex, unit length; or empty


@dataclass
class Material:
    name: str
    picture: str = ""             # the picture file it names (as the file says it), or ""
    colour: tuple = (0.7, 0.7, 0.7)
    data: bytes = b""             # the picture itself, when the model file holds it (.glb)
    alpha: bytes = b""            # its own alpha picture (side colour / shine), when the .glb names one


@dataclass
class Model:
    meshes: list
    materials: list
    source: str = ""

    def box(self) -> tuple:
        return _box([p for m in self.meshes for p in m.positions])

    def counts(self) -> tuple[int, int]:
        """(vertices, triangles) over every mesh."""
        return sum(len(m.positions) for m in self.meshes), sum(len(m.triangles) for m in self.meshes)


def _box(points) -> tuple:
    if not points:
        raise ModelError("the model has no points")
    return tuple(min(p[i] for p in points) for i in range(3)) + tuple(max(p[i] for p in points) for i in range(3))


# --- .3ds: chunks of (u16 id, u32 length counting its 6-byte head), nested ---
MAIN, EDITOR, OBJECT, TRIMESH = 0x4D4D, 0x3D3D, 0x4000, 0x4100
VERTICES, FACES, FACE_MATERIAL, UVS = 0x4110, 0x4120, 0x4130, 0x4140
MATERIAL, MAT_NAME, MAT_DIFFUSE, TEXTURE_MAP, MAP_FILE = 0xAFFF, 0xA000, 0xA020, 0xA200, 0xA300
COLOUR_F, COLOUR_24 = 0x0010, 0x0011


def _chunks(raw: bytes, start: int, end: int):
    pos = start
    while pos + 6 <= end:
        cid, length = struct.unpack_from("<HI", raw, pos)
        if length < 6 or pos + length > end:
            raise ModelError(f"a broken chunk {cid:#06x} at byte {pos}")
        yield cid, pos + 6, pos + length
        pos += length


def _cstring(raw: bytes, pos: int) -> tuple[str, int]:
    stop = raw.index(b"\0", pos)
    return raw[pos:stop].decode("latin-1"), stop + 1


def read_3ds(path: Path) -> Model:
    raw = Path(path).read_bytes()
    if len(raw) < 6 or struct.unpack_from("<H", raw, 0)[0] != MAIN:
        raise ModelError(f"{Path(path).name}: not a .3ds file")
    meshes, materials = [], []
    by_name: dict[str, int] = {}
    pending: list = []  # (mesh, [(material name, faces)]) resolved once every material is read
    for cid, a, b in _chunks(raw, 6, min(len(raw), struct.unpack_from("<I", raw, 2)[0])):
        if cid != EDITOR:
            continue
        for cid2, a2, b2 in _chunks(raw, a, b):
            if cid2 == MATERIAL:
                mat = Material("")
                for cid3, a3, b3 in _chunks(raw, a2, b2):
                    if cid3 == MAT_NAME:
                        mat.name = _cstring(raw, a3)[0]
                    elif cid3 == MAT_DIFFUSE:
                        for cid4, a4, _b4 in _chunks(raw, a3, b3):
                            if cid4 == COLOUR_24:
                                mat.colour = tuple(c / 255 for c in raw[a4:a4 + 3])
                            elif cid4 == COLOUR_F:
                                mat.colour = struct.unpack_from("<3f", raw, a4)
                    elif cid3 == TEXTURE_MAP:
                        for cid4, a4, _b4 in _chunks(raw, a3, b3):
                            if cid4 == MAP_FILE:
                                mat.picture = _cstring(raw, a4)[0]
                by_name[mat.name] = len(materials)
                materials.append(mat)
            elif cid2 == OBJECT:
                name, pos = _cstring(raw, a2)
                for cid3, a3, b3 in _chunks(raw, pos, b2):
                    if cid3 != TRIMESH:
                        continue
                    mesh, groups = Mesh(name, [], []), []
                    for cid4, a4, b4 in _chunks(raw, a3, b3):
                        if cid4 == VERTICES:
                            n = struct.unpack_from("<H", raw, a4)[0]
                            v = struct.unpack_from(f"<{3 * n}f", raw, a4 + 2)
                            mesh.positions = [tuple(v[3 * i:3 * i + 3]) for i in range(n)]
                        elif cid4 == UVS:
                            n = struct.unpack_from("<H", raw, a4)[0]
                            v = struct.unpack_from(f"<{2 * n}f", raw, a4 + 2)
                            mesh.uvs = [tuple(v[2 * i:2 * i + 2]) for i in range(n)]
                        elif cid4 == FACES:
                            n = struct.unpack_from("<H", raw, a4)[0]
                            f = struct.unpack_from(f"<{4 * n}H", raw, a4 + 2)
                            mesh.triangles = [tuple(f[4 * i:4 * i + 3]) for i in range(n)]
                            for cid5, a5, _b5 in _chunks(raw, a4 + 2 + 8 * n, b4):
                                if cid5 == FACE_MATERIAL:
                                    mname, p = _cstring(raw, a5)
                                    k = struct.unpack_from("<H", raw, p)[0]
                                    groups.append((mname, struct.unpack_from(f"<{k}H", raw, p + 2)))
                    if mesh.positions and mesh.triangles:
                        if mesh.uvs and len(mesh.uvs) != len(mesh.positions):
                            mesh.uvs = []  # (not one per point: not usable)
                        meshes.append(mesh)
                        pending.append((mesh, groups))
    for mesh, groups in pending:
        mesh.face_materials = [-1] * len(mesh.triangles)
        for mname, faces in groups:
            for f in faces:
                if f < len(mesh.triangles):
                    mesh.face_materials[f] = by_name.get(mname, -1)
    if not meshes:
        raise ModelError(f"{Path(path).name}: no meshes in it")
    return Model(meshes, materials, str(path))


# --- .glb (glTF 2.0 binary): every mesh primitive of the default scene, placed by its node's transform; glTF is y up,
# so points come out as (x, -z, y): z up, still right-handed ---
_COMPONENT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
_IDENTITY = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]


def _matmul(a: list, b: list) -> list:
    """Two 4 x 4 column-major matrices multiplied (glTF's order)."""
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def _node_matrix(node: dict) -> list:
    if "matrix" in node:
        return list(node["matrix"])
    tx, ty, tz = node.get("translation", (0, 0, 0))
    x, y, z, w = node.get("rotation", (0, 0, 0, 1))
    sx, sy, sz = node.get("scale", (1, 1, 1))
    r = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 0,
         2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 0,
         2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y), 0, 0, 0, 0, 1]
    for c, s in enumerate((sx, sy, sz)):
        for k in range(3):
            r[c * 4 + k] *= s
    r[12:15] = [tx, ty, tz]
    return r


def glb_document(raw: bytes) -> tuple[dict, bytes]:
    """A .glb's JSON document and its binary chunk."""
    if raw[:4] != b"glTF":
        raise ModelError("not a .glb file")
    length, kind = struct.unpack_from("<I4s", raw, 12)
    if kind != b"JSON":
        raise ModelError("a .glb without its JSON chunk first")
    doc = json.loads(raw[20:20 + length])
    at, binary = 20 + length, b""
    if at + 8 <= len(raw):
        blen, bkind = struct.unpack_from("<I4s", raw, at)
        if bkind == b"BIN\0":
            binary = raw[at + 8:at + 8 + blen]
    return doc, binary


def glb_accessor(doc: dict, binary: bytes, i: int) -> list:
    """Accessor `i`'s values (tuples, or numbers for scalars)."""
    a = doc["accessors"][i]
    view = doc["bufferViews"][a["bufferView"]]
    if view.get("buffer", 0) != 0:
        raise ModelError("a .glb whose data is outside its own buffer")
    code, width = _COMPONENT[a["componentType"]], _WIDTH[a["type"]]
    size = struct.calcsize(code)
    stride = view.get("byteStride") or size * width
    base = view.get("byteOffset", 0) + a.get("byteOffset", 0)
    out = []
    for k in range(a["count"]):
        v = struct.unpack_from(f"<{width}{code}", binary, base + k * stride)
        if a.get("normalized") and code != "f":
            top = float((1 << (8 * size - (0 if code.isupper() else 1))) - 1)
            v = tuple(max(-1.0, c / top) for c in v)
        out.append(v if width > 1 else v[0])
    return out


def glb_image(doc: dict, binary: bytes, image: int) -> bytes:
    """An image the .glb holds (its bytes), or b"" when it's a file beside it."""
    img = doc["images"][image]
    if "bufferView" not in img:
        return b""
    v = doc["bufferViews"][img["bufferView"]]
    return binary[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]


def _normal_matrix(m: list) -> list:
    """The 3x3 that turns normals the way the column-major 4x4 `m` turns points: the inverse's transpose (cofactors
    over the determinant), so normals stay square to their faces even under an uneven scale."""
    a = [[m[c * 4 + r] for c in range(3)] for r in range(3)]
    cof = [[a[(r + 1) % 3][(c + 1) % 3] * a[(r + 2) % 3][(c + 2) % 3]
            - a[(r + 1) % 3][(c + 2) % 3] * a[(r + 2) % 3][(c + 1) % 3] for c in range(3)] for r in range(3)]
    det = sum(a[0][c] * cof[0][c] for c in range(3))
    if abs(det) < 1e-12:
        return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    return [[cof[r][c] / det for c in range(3)] for r in range(3)]


def _unit(v) -> tuple:
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v) if n > 1e-12 else (0.0, 0.0, 1.0)


def read_glb(path: Path) -> Model:
    """A .glb's meshes (z up) with their own normals when it has them, and each material's picture and, when the
    material's extras name one (`rusemod_alpha_texture`, as write_glb writes it), its alpha picture."""
    try:
        doc, binary = glb_document(Path(path).read_bytes())
    except (ValueError, struct.error) as exc:
        raise ModelError(f"{Path(path).name}: {exc}") from None
    materials = []
    for m in doc.get("materials", []):
        pic, data, alpha = "", b"", b""
        tex = (m.get("pbrMetallicRoughness") or {}).get("baseColorTexture")
        if tex is not None:
            source = doc["textures"][tex["index"]]["source"]
            img = doc["images"][source]
            pic = img.get("uri") or img.get("name") or f"image{source}"
            data = glb_image(doc, binary, source)
        alpha_tex = (m.get("extras") or {}).get("rusemod_alpha_texture")
        if alpha_tex is not None:
            alpha = glb_image(doc, binary, doc["textures"][alpha_tex]["source"])
        colour = tuple((m.get("pbrMetallicRoughness") or {}).get("baseColorFactor", (0.7, 0.7, 0.7, 1))[:3])
        materials.append(Material(m.get("name", ""), pic, colour, data, alpha))
    meshes = []

    def visit(n: int, parent: list) -> None:
        node = doc["nodes"][n]
        matrix = _matmul(parent, _node_matrix(node))
        if "mesh" in node:
            gm = doc["meshes"][node["mesh"]]
            for k, prim in enumerate(gm["primitives"]):
                if prim.get("mode", 4) != 4:
                    continue  # only triangles
                pos = []
                for p in glb_accessor(doc, binary, prim["attributes"]["POSITION"]):
                    x, y, z = (sum(matrix[c * 4 + r] * (p[c] if c < 3 else 1.0) for c in range(4)) for r in range(3))
                    pos.append((x, -z, y))
                idx = glb_accessor(doc, binary, prim["indices"]) if "indices" in prim else list(range(len(pos)))
                uvs = glb_accessor(doc, binary, prim["attributes"]["TEXCOORD_0"]) \
                    if "TEXCOORD_0" in prim["attributes"] else []
                nrm = []
                if "NORMAL" in prim["attributes"]:      # the model's own shading (weighted normals, hard edges)
                    nm = _normal_matrix(matrix)
                    for n in glb_accessor(doc, binary, prim["attributes"]["NORMAL"]):
                        x, y, z = (sum(nm[r][c] * n[c] for c in range(3)) for r in range(3))
                        nrm.append(_unit((x, -z, y)))
                name = node.get("name") or gm.get("name") or f"mesh{node['mesh']}"
                tris = [tuple(idx[i:i + 3]) for i in range(0, len(idx) - 2, 3)]
                meshes.append(Mesh(name if len(gm["primitives"]) == 1 else f"{name}.{k}", pos, tris,
                                   [(u, 1.0 - v) for u, v in uvs],  # glTF's v runs down the picture
                                   [prim.get("material", -1)] * len(tris), nrm))
        for c in node.get("children", []):
            visit(c, matrix)

    scene = (doc.get("scenes") or [{"nodes": list(range(len(doc.get("nodes", []))))}])[doc.get("scene", 0)]
    for n in scene.get("nodes", []):
        visit(n, _IDENTITY)
    if not meshes:
        raise ModelError(f"{Path(path).name}: no meshes in it")
    return Model(meshes, materials, str(path))


def read_model(path: Path) -> Model:
    """A model file by its kind: .3ds or .glb."""
    suffix = Path(path).suffix.lower()
    if suffix == ".3ds":
        return read_3ds(path)
    if suffix == ".glb":
        return read_glb(path)
    raise ModelError(f"{Path(path).name}: a {suffix or 'nameless'} file; the importer reads .3ds and .glb (Blender "
                     "saves .glb: File > Export > glTF 2.0)")


# --- pictures ---
PICTURES = (".png", ".tga")


def _pictures_in(folder: Path, depth: int = 3) -> list[Path]:
    """The .png and .tga files in `folder` and up to `depth` folders below it."""
    out, level = [], [Path(folder)]
    for _ in range(depth + 1):
        below = []
        for d in level:
            try:
                for p in d.iterdir():
                    if p.is_dir():
                        below.append(p)
                    elif p.suffix.lower() in PICTURES:
                        out.append(p)
            except OSError:  # (a folder we may not read)
                continue
        level = below
    return out


def find_picture(name: str, folder: Path) -> Path | None:
    """The picture file a material names, in `folder` or up to three folders below (the shallowest wins): by its file
    name, else (a .3ds keeps 8.3 names: MAIN_DEF.TGA for Main_Defuse.tga) the file whose name starts with the same
    eight letters."""
    want = Path(name.replace("\\", "/")).name.lower()
    if not want:
        return None
    stem8 = Path(want).stem[:8]
    found = sorted(_pictures_in(Path(folder)), key=lambda p: (len(p.relative_to(folder).parts), str(p).lower()))
    exact = [p for p in found if p.name.lower() == want or p.stem.lower() == Path(want).stem]
    if exact:
        return exact[0]
    short = [p for p in found if len(Path(want).stem) == 8 and p.stem.lower()[:8] == stem8]
    return short[0] if short else None


def load_picture(data: bytes, name: str = "") -> tuple[int, int, bytes]:
    """A .png or .tga picture's bytes -> (width, height, RGBA)."""
    from .png import read_png
    from .tga import read_tga
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return read_png(data)
    if name.lower().endswith(".tga") or data[2:3] in (b"\x02", b"\x03", b"\x0a", b"\x0b"):
        return read_tga(data)
    raise ModelError(f"{name or 'a picture'}: only .png and .tga pictures are read")


def _sized(w: int, h: int, px: bytes, side: int) -> tuple[int, int, bytes]:
    """A picture made a power of two each way (4 at least), its longer side at most `side`: halved by averaging
    while too big, then sampled to the nearest power of two."""
    from .unitlook import halve
    while max(w, h) > side and w % 2 == 0 and h % 2 == 0 and min(w, h) > 4:
        px, w, h = halve(px, w, h), w // 2, h // 2

    def pow2(n: int) -> int:
        return max(4, min(side, 1 << max(0, round(math.log2(max(1, n))))))
    nw, nh = pow2(w), pow2(h)
    if (nw, nh) == (w, h):
        return w, h, px
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        sy = min(h - 1, y * h // nh)
        for x in range(nw):
            sx = min(w - 1, x * w // nw)
            out[(y * nw + x) * 4:(y * nw + x) * 4 + 4] = px[(sy * w + sx) * 4:(sy * w + sx) * 4 + 4]
    return nw, nh, bytes(out)


# --- fitting to a unit ---
HULL, TURRET, GUN = "hull", "turret", "gun"
BONES = {HULL: "chassis", TURRET: "tourelle_01", GUN: "tourelle_01"}  # the gun turns with the turret (no recoil yet)
TURRET_WORDS = ("turret", "turre", "tourelle", "tower")
GUN_WORDS = ("barrel", "barre", "cannon", "canon", "gun")
NOT_THE_GUN = ("minigun", "machine", "mg_", "_mg", "coax")
PLAIN_ALPHA = 144       # alpha: the Sherman's body is mostly 128-159 (no side colour; shine is high, side colour low)


def roles(model: Model) -> list[str]:
    """Each mesh's role (HULL, TURRET or GUN): from its name, else a part resting on the turret (its middle inside
    the turret's outline, its bottom no lower than the turret's) turns with it; everything else is the hull."""
    out: list = []
    for m in model.meshes:
        n = m.name.lower()
        if any(w in n for w in TURRET_WORDS):
            out.append(TURRET)
        elif any(w in n for w in GUN_WORDS) and not any(w in n for w in NOT_THE_GUN):
            out.append(GUN)
        else:
            out.append(None)
    turret = [p for m, r in zip(model.meshes, out) if r == TURRET for p in m.positions]
    if turret:
        tb = _box(turret)
        for i, m in enumerate(model.meshes):
            if out[i] is None:
                b = _box(m.positions)
                cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
                if tb[0] <= cx <= tb[3] and tb[1] <= cy <= tb[4] and b[2] >= tb[2] - 0.02 * (tb[5] - tb[2]):
                    out[i] = TURRET
    return [r or HULL for r in out]


def facing(model: Model, parts: list[str], like: dict | None = None) -> tuple[int, int]:
    """Which way the model faces, as (axis: 0 = x, 1 = y; sign): the way its gun points from its turret's middle;
    without a gun or turret, the way round whose length over width is nearest the copied unit's (`like`'s "length"
    and "width": a plane is wider than it is long, so its longer side is its wings, 2026-10-08), else along its
    longer side; +, but an aircraft's (`like` "aircraft") tail fin, its highest point, is at the back."""
    gun = [p for m, r in zip(model.meshes, parts) if r == GUN for p in m.positions]
    turret = [p for m, r in zip(model.meshes, parts) if r == TURRET for p in m.positions]
    if gun and turret:
        g, t = _box(gun), _box(turret)
        d = ((g[0] + g[3] - t[0] - t[3]) / 2, (g[1] + g[4] - t[1] - t[4]) / 2)
        axis = 0 if abs(d[0]) >= abs(d[1]) else 1
        return axis, 1 if d[axis] > 0 else -1
    b = model.box()
    dx, dy = b[3] - b[0], b[4] - b[1]
    axis = 0 if dx >= dy else 1
    if like and like.get("width") and like.get("length") and dx > 0 and dy > 0:
        want = math.log(like["length"] / like["width"])
        axis = 0 if abs(math.log(dx / dy) - want) <= abs(math.log(dy / dx) - want) else 1
    sign = 1
    if like and like.get("aircraft"):
        pts = [p for m in model.meshes for p in m.positions]
        top = sorted(pts, key=lambda p: p[2])[-max(1, len(pts) // 50):]
        middle = (b[axis] + b[axis + 3]) / 2
        if sum(p[axis] for p in top) / len(top) > middle:
            sign = -1
    return axis, sign


def turn_ring(points: list) -> tuple[float, float]:
    """Where a turret turns: the middle of its lowest sixth (the ring it sits on), across x and y."""
    b = _box(points)
    low = [p for p in points if p[2] <= b[2] + (b[5] - b[2]) / 6]
    lb = _box(low)
    return (lb[0] + lb[3]) / 2, (lb[1] + lb[4]) / 2


@dataclass
class Part:
    """One draw of the fitted model: the bone it follows, its picture (index into Prepared.pictures, or -1) and its
    vertices in the game's axes and units (x forward, y right, z up)."""
    bone: str
    picture: int
    positions: list
    normals: list
    uvs: list                     # (u, v), v down the picture, as the game's
    triangles: list               # wound the game's way: (b - a) x (c - a) points out


@dataclass
class Prepared:
    parts: list
    pictures: list                # (name, width, height, RGBA: colour, and alpha = side colour / shine)
    report: dict


def prepare(model: Model, folder, like: dict, size: float = 1.0, side: int = 1024) -> Prepared:
    """`model` fitted to a unit: `like` is the copied unit's model as {"length": its hull's length along x (game
    units), "pivot": (x, y) its turret turns round, "ground": its lowest z}; `size` scales on top (1: as long as it);
    pictures at most `side` pixels, inside the model (.glb) or found in `folder` (a .3ds's: a folder, or several
    looked in in turn). A picture named but not found is a flat colour, listed in the report's "missing"."""
    folders = [Path(f) for f in ([folder] if isinstance(folder, (str, Path)) else (folder or []))]
    parts = roles(model)
    axis, sign = facing(model, parts, like)
    f = [0.0, 0.0, 0.0]
    f[axis] = float(sign)
    r = (f[1], -f[0], 0.0)        # forward x up: the right-hand side
    hull = [p for m, k in zip(model.meshes, parts) if k == HULL for p in m.positions] or \
        [p for m in model.meshes for p in m.positions]
    along = [p[0] * f[0] + p[1] * f[1] for p in hull]
    length = max(along) - min(along)
    if length <= 0:
        raise ModelError("the model has no length")
    scale = like["length"] * size / length
    turret = [m for m, k in zip(model.meshes, parts) if k == TURRET]
    if turret:
        main = max(turret, key=lambda m: len(m.positions))
        cx, cy = turn_ring(main.positions)
        ring = ((cx * f[0] + cy * f[1]) * scale, (cx * r[0] + cy * r[1]) * scale)
        shift = (like["pivot"][0] - ring[0], like["pivot"][1] - ring[1])
    else:  # no turret: its middle where the unit's is
        mid = (max(along) + min(along)) / 2 * scale
        side_mid = [p[0] * r[0] + p[1] * r[1] for p in hull]
        shift = (like.get("middle", like["pivot"][0]) - mid, -(max(side_mid) + min(side_mid)) / 2 * scale)
    low = min(p[2] for m in model.meshes for p in m.positions)
    lift = like["ground"] - low * scale

    def place(p):
        x, y, z = p
        return ((x * f[0] + y * f[1]) * scale + shift[0], (x * r[0] + y * r[1]) * scale + shift[1], z * scale + lift)

    def turn(n):      # a normal through place's turn (and its mirror into the game's axes); scale and shift don't apply
        x, y, z = n
        return _unit((x * f[0] + y * f[1], x * r[0] + y * r[1], z))

    # pictures: one per material that has one (a flat colour for those that don't)
    pictures, pic_of, missing, alphas = [], {}, [], []
    for k, mat in enumerate(model.materials):
        data, label = mat.data, mat.picture
        if not data and mat.picture:
            path = next((p for p in (find_picture(mat.picture, f) for f in folders if f.is_dir()) if p), None)
            if path is not None:
                data, label = path.read_bytes(), path.name
            else:
                missing.append(mat.picture)
        if data:
            w, h, px = _sized(*load_picture(data, label), side)
        else:
            w = h = 4
            px = bytes(round(c * 255) for c in mat.colour) + b"\xff"
            px = px * 16
        pic_of[k] = len(pictures)
        pictures.append([label or mat.name or f"material{k}", w, h, px])
        alphas.append(mat.alpha if data else b"")
    # colours as the model has them; alpha (side colour where low, shine where high) the model's own alpha picture
    # when it names one (sized the same way as the colour), else the game's plain value. Said in the report, never
    # dropped silently (2026-10-05: a model's shine map was lost here before).
    own_alpha, notes = [], []
    for pic, alpha in zip(pictures, alphas):
        px = bytearray(pic[3])
        values = None
        if alpha:
            aw, ah, apx = _sized(*load_picture(alpha, pic[0] + " (alpha)"), side)
            if (aw, ah) == (pic[1], pic[2]):
                values = apx[0::4]
            else:
                notes.append(f"{pic[0]}: its alpha picture is {aw} x {ah}, the colour {pic[1]} x {pic[2]}; "
                             f"plain alpha used")
        px[3::4] = values if values is not None else bytes([PLAIN_ALPHA]) * (pic[1] * pic[2])
        if values is not None:
            own_alpha.append(pic[0])
        pic[3] = bytes(px)

    out: list[Part] = []
    groups: dict = {}
    for m, k in zip(model.meshes, parts):
        mats = m.face_materials or [-1] * len(m.triangles)
        for t, mk in zip(m.triangles, mats):
            groups.setdefault((BONES[k], pic_of.get(mk, -1)), []).append((m, t))
    own_normals = 0
    for (bone, pic), tris in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        index: dict = {}
        part = Part(bone, pic, [], [], [], [])
        given: list = []      # per vertex: the model's own normal (game axes), or None
        for m, (a, b, c) in tris:
            corners = []
            for v in (a, b, c):
                key = (id(m), v)
                if key not in index:
                    index[key] = len(part.positions)
                    part.positions.append(place(m.positions[v]))
                    u, vv = m.uvs[v] if m.uvs else (0.0, 0.0)
                    part.uvs.append((u, 1.0 - vv))
                    given.append(turn(m.normals[v]) if v < len(m.normals) else None)
                corners.append(index[key])
            part.triangles.append((corners[0], corners[2], corners[1]))  # the turn to the game's axes mirrors
        # the model's own normals where it has them (as other engines' importers do by default: its weighted normals
        # and hard edges are its shading); worked out from the triangles only where it has none
        computed = smooth_normals(part.positions, part.triangles)
        part.normals = [g if g is not None else n for g, n in zip(given, computed)]
        own_normals += sum(g is not None for g in given)
        out.append(part)
    vertices = sum(len(p.positions) for p in out)
    report = {"parts": {m.name: k for m, k in zip(model.meshes, parts)}, "facing": ("x" if axis == 0 else "y",
              sign), "scale": scale, "vertices": vertices, "triangles": sum(len(p.triangles) for p in out),
              "draws": len(out), "pictures": [(p[0], p[1], p[2]) for p in pictures], "missing": missing,
              "normals": ("the model's own" if own_normals == vertices else "worked out" if own_normals == 0
                          else f"the model's own for {own_normals} of {vertices} points, the rest worked out"),
              "alpha": {p[0]: ("the model's own" if p[0] in own_alpha else f"plain {PLAIN_ALPHA}") for p in pictures},
              "notes": notes}
    return Prepared(out, pictures, report)


def smooth_normals(positions: list, triangles: list) -> list:
    """Each vertex's normal: the sum of its triangles' (b - a) x (c - a) (larger triangles count more), unit length."""
    acc = [[0.0, 0.0, 0.0] for _ in positions]
    for a, b, c in triangles:
        pa, pb, pc = positions[a], positions[b], positions[c]
        u = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
        v = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        for i in (a, b, c):
            acc[i][0] += n[0]
            acc[i][1] += n[1]
            acc[i][2] += n[2]
    out = []
    for x, y, z in acc:
        length = math.sqrt(x * x + y * y + z * z)
        out.append((x / length, y / length, z / length) if length else (0.0, 0.0, 1.0))
    return out


# --- the mod's own file: files/models/<unit>.glb ---
def write_glb(prep: Prepared, path: Path, like_model: str = "") -> None:
    """Save a fitted model as a .glb in the axes `ruse export-model` writes (rusemod.gltf): one node per bone, a
    primitive per picture, the colour pictures as its materials' and each alpha (side colour / shine) as an image of
    its own (named in the material's extras)."""
    from .dxt import png_bytes
    from .gltf import FLOAT, MIRROR, SCALE, UINT, USHORT, _Glb, _point, _split
    g = _Glb()
    for name, w, h, px in prep.pictures:
        colour, grey = _split(px)
        tex = g.image(png_bytes(colour, w, h), Path(name).stem)
        alpha = g.image(png_bytes(grey, w, h), Path(name).stem + "_alpha")
        g.doc["materials"].append({"name": Path(name).stem, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": tex}, "metallicFactor": 0.0, "roughnessFactor": 0.8}, "doubleSided": True,
            "extras": {"rusemod_alpha_texture": alpha}})
    nodes: dict = {}
    for part in prep.parts:
        pos = [_point(*p) for p in part.positions]
        nrm = [_point(*n, scale=1.0) for n in part.normals]
        tri = [i for a, b, c in part.triangles for i in ((a, c, b) if MIRROR else (a, b, c))]
        prim = {"attributes": {"POSITION": g.accessor(pos, "VEC3", FLOAT, minmax=True),
                               "NORMAL": g.accessor(nrm, "VEC3", FLOAT),
                               "TEXCOORD_0": g.accessor(part.uvs, "VEC2", FLOAT)},
                "indices": g.accessor(tri, "SCALAR", UINT if len(pos) > 65535 else USHORT, 34963)}
        if part.picture >= 0:
            prim["material"] = part.picture
        nodes.setdefault(part.bone, []).append(prim)
    for bone, prims in nodes.items():
        g.doc["meshes"].append({"name": bone, "primitives": prims})
        g.doc["nodes"].append({"name": bone, "mesh": len(g.doc["meshes"]) - 1})
    g.doc["scenes"] = [{"name": Path(path).stem, "nodes": list(range(len(g.doc["nodes"])))}]
    g.doc["scene"] = 0
    g.doc["asset"]["extras"] = {"rusemod_import": 1, "rusemod_scale": SCALE, "rusemod_mirror": MIRROR,
                                "rusemod_like": like_model, "rusemod_report": prep.report}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(g.to_bytes())
