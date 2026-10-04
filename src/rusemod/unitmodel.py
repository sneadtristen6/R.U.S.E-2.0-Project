"""Imported unit models into the game's packs (the model importer, step two; step one is rusemod.modelin): a new unit's
own model, from its mod's files/models/<the unit's name>.glb, written beside the model of the unit it copies.

Where it goes: every mesh pack that holds the copied unit's model gets the new one too (its name record, its draw
calls, its vertex and index buffers, its materials), and every skeleton pack that holds the copied unit's skeleton
gets an entry for the new name sharing it (as T33's Tall Sherman did, proven in the game). The new model follows the
copied unit's bones: its hull the root bone (`chassis`), its turret and gun the turret's (`tourelle_01`), so the game
turns them as it turns the copied unit's.

How it's stored: one draw call per picture, each vertex in the game's skinned format with float texture coordinates
(TVertex__Position_3f__NormalIn01_4ubn__BlW_4ubn__BlIdx_4ub__TexCoord0_2f__TexPackedAtlas0_4ubn: 55 of the game's own
buffers), plain (not packed), one bone per vertex at full weight, the atlas bytes (0, 0, 255, 255) as on every unit;
indices 16-bit (a draw of more than 65,535 points has its own 32-bit indices: not tried in the game). Each draw's
material is a copy of the copied unit's body material naming the new picture. Each picture is a texture of its own
(gen\\...\\<unit>_NN.tgv, DXT5 with every level down to 4 x 4, plain TGU1 levels as in T23) added to ZZ_Win.dat, with
its stand-in (64 pixels across at most, raw DXT5) added to every stand-in pack that holds the copied body texture's.
A stand-in is found by an 8-byte key: the 64-bit CRC (polynomial 0x42F0E1EBA9EA3693, all ones in and out) of its
name, true of all 2,822 stand-ins in the game's 74 stand-in packs (checked 2026-10-04)."""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path

from . import dxt, tgu1
from .modelin import ModelError, Part, Prepared, _IDENTITY, _matmul, _node_matrix, glb_accessor, glb_document, \
    glb_image, smooth_normals
from .ndf import Ndf, Value
from .spk import Spk, SpkError
from .tmst import Tgv, make_tgv
from .unitlook import halve
from .unitpacks import NONE, PROXY_MAGIC, Buffer, MeshPack, Proxy, ProxyPack, _material_list, _subs, _texts

MODELS = Path("files") / "models"   # a mod's new units' models: <the unit's name>.glb
PACKS = "gen_5\\pack\\"
SKINNED_2F = ("$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__BlW_4ubn__BlIdx_4ub__TexCoord0_2f__"
              "TexPackedAtlas0_4ubn")
STRIDE = 12 + 4 + 4 + 4 + 8 + 4
ROOT, TURRET = "chassis", "tourelle_01"
STANDIN_SIDE = 64
INDEX_16, INDEX_32 = 1, 0   # an index buffer's kind: 1 = 16-bit (every one the game ships), else 32-bit


class UnitModelError(ModelError):
    pass


def import_model(game: Path, source_model: str, model_file: Path, out: Path, size: float = 1.0,
                 side: int = 1024, pictures: Path | None = None) -> dict:
    """Step one for a mod: `model_file` (.3ds or .glb) fitted to the game's model `source_model` (the unit the new
    one copies) and saved as `out` (the mod's files/models/<unit>.glb). A .3ds's pictures are looked for in
    `pictures`, then beside it, then one folder up (downloads often keep them in a folder of their own). Returns the
    fitting's report (parts and their roles, facing, scale, counts, pictures, "missing": pictures not found)."""
    from .build import find_pack
    from .edat import Edat
    from .modelin import prepare, read_model, write_glb
    path = find_pack(Path(game), "ZZ_Win.dat")
    if path is None:
        raise UnitModelError(f"ZZ_Win.dat isn't in {game}")
    zz = Edat.open(str(path))
    try:
        src = find_source(zz, source_model)
    finally:
        zz.close()
    here = Path(model_file).resolve().parent
    look = ([Path(pictures)] if pictures else []) + [here, here.parent]
    prep = prepare(read_model(model_file), look, src.like, size=size, side=side)
    write_glb(prep, out, src.model)
    return dict(prep.report, like=src.model)


def mod_models(folder: Path) -> dict:
    """{a new unit's name: its model file} from a mod's files/models/<the unit's name>.glb."""
    root = Path(folder) / MODELS
    return {f.stem: f for f in sorted(root.glob("*.glb"))} if root.is_dir() else {}


# --- the stand-in key ---
_POLY = 0x42F0E1EBA9EA3693
_TABLE = []
for _i in range(256):
    _c = _i << 56
    for _ in range(8):
        _c = ((_c << 1) ^ _POLY) if _c & (1 << 63) else (_c << 1)
        _c &= 0xFFFFFFFFFFFFFFFF
    _TABLE.append(_c)


def crc64(data: bytes) -> int:
    h = 0xFFFFFFFFFFFFFFFF
    for c in data:
        h = ((h << 8) & 0xFFFFFFFFFFFFFFFF) ^ _TABLE[((h >> 56) ^ c) & 0xFF]
    return h ^ 0xFFFFFFFFFFFFFFFF


def standin_key(name: str) -> bytes:
    """The key a stand-in is found by: the CRC of its name (gentexproxy\\...\\x01.tgv, as stored)."""
    return struct.pack("<Q", crc64(name.encode("latin-1")))


# --- skeletons ---
@dataclass
class Skeleton:
    names: list
    parents: list
    pivots: list          # each bone's point, model units (where it turns round)


def read_skeleton(blob: bytes) -> Skeleton:
    """A skeleton entry: u32 1, bone count, then offsets: its bind matrices (3 x 4 floats each, model -> bone), the
    parents (i32, -1: none), a second table, the names; the names' lengths (u16) from byte 0x24."""
    one, n, mats, parents, _second, names_at = struct.unpack_from("<6I", blob, 0)
    if one != 1 or not 0 < n < 1024:
        raise UnitModelError("a skeleton not laid out as known")
    lens = struct.unpack_from(f"<{n}H", blob, 0x24)
    names, at = [], names_at
    for k in lens:
        names.append(blob[at:at + k].decode("latin-1"))
        at += k
    par = list(struct.unpack_from(f"<{n}i", blob, parents))
    pivots = []
    for k in range(n):
        m = struct.unpack_from("<12f", blob, mats + 48 * k)
        rot, t = (m[0:3], m[4:7], m[8:11]), (m[3], m[7], m[11])
        pivots.append(tuple(-sum(rot[r][c] * t[r] for r in range(3)) for c in range(3)))
    return Skeleton(names, par, pivots)


# --- where the copied unit's model is ---
@dataclass
class Source:
    model: str                     # its name in the packs (lower case)
    mesh_packs: dict               # member path -> raw bytes, every mesh pack that holds it
    skeleton_packs: dict           # member path -> raw bytes, every skeleton pack that holds its skeleton entry
    skeleton: Skeleton | None
    like: dict = field(default_factory=dict)   # for modelin.prepare: length, pivot, ground
    body_texture: str = ""         # its body material's picture (ZZ:\\GenTexGroup\\...\\X01.png)


def find_source(zz, model: str) -> Source:
    """The copied unit's model `model` (its pack name, any case) across ZZ_Win.dat's packs, and what fitting to it
    needs. UnitModelError when no pack holds it, or it has no bones."""
    model = model.replace("/", "\\").lower()
    if model.startswith("datadir:\\"):
        model = model[len("datadir:\\"):]
    meshes, skeletons = {}, {}
    for e in zz.entries:
        p = e.path.lower()
        if not (p.startswith(PACKS) and p.endswith(".spk")):
            continue
        raw = bytes(zz.read(e))
        if raw[:8] != b"MESHPCPC":
            continue
        try:
            pack = MeshPack.read(raw)
        except ValueError:
            continue
        item = pack.items.get(model)
        if item is None:
            continue
        if item[1] != NONE:
            meshes[e.path] = raw
        elif item[2] != NONE:
            skeletons[e.path] = raw
    if not meshes:
        raise UnitModelError(f"no mesh pack holds the model {model}")
    first = MeshPack.read(next(iter(meshes.values())))
    skel = first.skeletons[first.items[model][2]] if first.items[model][2] != NONE else None
    if skel is None and skeletons:
        sp = MeshPack.read(next(iter(skeletons.values())))
        skel = sp.skeletons[sp.items[model][2]]
    if skel is None:
        raise UnitModelError(f"{model} has no skeleton: only units with bones (vehicles) can take a model yet")
    bones = read_skeleton(skel)
    if ROOT not in bones.names:
        raise UnitModelError(f"{model}'s skeleton has no {ROOT} bone")
    spk = Spk(next(iter(meshes.values())))
    mats = spk.materials()
    hull, low = [], math.inf
    body = None
    for part in spk.model(model):
        remap = mats[part.material].get("skinning") or []
        tex = next(iter(mats[part.material].get("textures", {}).values()), "")
        if body is None and "CombinedDSCTexture" in mats[part.material].get("textures", {}):
            body = tex
        for i in range(len(part.positions) // 3):
            p = part.positions[3 * i:3 * i + 3]
            low = min(low, p[2])
            b = part.bones[i] if i < len(part.bones) else [0]
            w = part.weights[i] if i < len(part.weights) else [255]
            heavy = max(range(len(w)), key=lambda k: w[k])
            if (remap[b[heavy]] if b[heavy] < len(remap) else b[heavy]) == bones.names.index(ROOT):
                hull.append(p[0])
    if not hull or body is None:
        raise UnitModelError(f"{model} has no hull on its {ROOT} bone, or no body texture (CombinedDSCTexture)")
    pivot = bones.pivots[bones.names.index(TURRET)] if TURRET in bones.names else ((max(hull) + min(hull)) / 2, 0.0, 0)
    like = {"length": max(hull) - min(hull), "pivot": (pivot[0], pivot[1]), "ground": low,
            "middle": (max(hull) + min(hull)) / 2}
    return Source(model, meshes, skeletons, bones, like, body)


# --- the mod's file back ---
def read_mod_glb(path: Path) -> Prepared:
    """A mod's files/models/<unit>.glb (rusemod.modelin.write_glb's, or the same saved again from Blender): parts by
    node name (the bone), a part per primitive, in the game's axes again; its pictures with their alpha (the image
    named in the material's extras, else a plain one)."""
    from .gltf import MIRROR, SCALE
    from .modelin import PLAIN_ALPHA, load_picture
    try:
        doc, binary = glb_document(Path(path).read_bytes())
    except (OSError, ValueError, struct.error) as exc:
        raise UnitModelError(f"{Path(path).name}: {exc}") from None
    pictures, pic_of = [], {}
    for k, m in enumerate(doc.get("materials", [])):
        tex = (m.get("pbrMetallicRoughness") or {}).get("baseColorTexture")
        if tex is None:
            continue
        data = glb_image(doc, binary, doc["textures"][tex["index"]]["source"])
        if not data:
            raise UnitModelError(f"{Path(path).name}: material {m.get('name', k)}'s picture isn't inside the .glb "
                               "(in Blender's export: Images > Automatic, or PNG)")
        w, h, px = load_picture(data, m.get("name", "") + ".png")
        alpha_tex = (m.get("extras") or {}).get("rusemod_alpha_texture")
        px = bytearray(px)
        if alpha_tex is not None:
            aw, ah, apx = load_picture(glb_image(doc, binary, doc["textures"][alpha_tex]["source"]), "alpha.png")
            if (aw, ah) != (w, h):
                raise UnitModelError(f"{Path(path).name}: {m.get('name', k)}'s alpha picture is {aw} x {ah}, its "
                                   f"colour {w} x {h}")
            px[3::4] = apx[0::4]
        else:
            px[3::4] = bytes([PLAIN_ALPHA]) * (w * h)
        if w % 4 or h % 4 or w & (w - 1) or h & (h - 1):
            raise UnitModelError(f"{Path(path).name}: {m.get('name', k)}'s picture is {w} x {h}; it must be a power of "
                               "two each way (256, 512, 1024...)")
        pic_of[k] = len(pictures)
        pictures.append([m.get("name", f"picture{k}"), w, h, bytes(px)])
    parts = []

    def visit(n: int, parent: list) -> None:
        node = doc["nodes"][n]
        matrix = _matmul(parent, _node_matrix(node))
        if "mesh" in node:
            bone = node.get("name") or doc["meshes"][node["mesh"]].get("name") or ROOT
            bone = bone.split(".")[0]   # Blender adds .001 to a repeated name
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                pos, nrm = [], []
                for p in glb_accessor(doc, binary, prim["attributes"]["POSITION"]):
                    g = [sum(matrix[c * 4 + r] * (p[c] if c < 3 else 1.0) for c in range(4)) for r in range(3)]
                    pos.append((g[0] / SCALE, g[2] / SCALE, g[1] / SCALE) if MIRROR else
                               (g[0] / SCALE, -g[2] / SCALE, g[1] / SCALE))
                idx = glb_accessor(doc, binary, prim["indices"]) if "indices" in prim else list(range(len(pos)))
                tris = [(idx[i], idx[i + 2], idx[i + 1]) if MIRROR else tuple(idx[i:i + 3])
                        for i in range(0, len(idx) - 2, 3)]
                if "NORMAL" in prim["attributes"]:
                    for v in glb_accessor(doc, binary, prim["attributes"]["NORMAL"]):
                        g = [sum(matrix[c * 4 + r] * v[c] for c in range(3)) for r in range(3)]
                        x, y, z = (g[0], g[2], g[1]) if MIRROR else (g[0], -g[2], g[1])
                        s = math.sqrt(x * x + y * y + z * z) or 1.0
                        nrm.append((x / s, y / s, z / s))
                else:
                    nrm = smooth_normals(pos, tris)
                uvs = glb_accessor(doc, binary, prim["attributes"]["TEXCOORD_0"]) \
                    if "TEXCOORD_0" in prim["attributes"] else [(0.0, 0.0)] * len(pos)
                parts.append(Part(bone, pic_of.get(prim.get("material", -1), -1), pos, nrm, list(uvs), tris))
        for c in node.get("children", []):
            visit(c, matrix)

    scene = (doc.get("scenes") or [{"nodes": list(range(len(doc.get("nodes", []))))}])[doc.get("scene", 0)]
    for n in scene.get("nodes", []):
        visit(n, _IDENTITY)
    if not parts:
        raise UnitModelError(f"{Path(path).name}: no meshes in it")
    return Prepared(parts, pictures, (doc.get("asset", {}).get("extras") or {}).get("rusemod_report", {}))


# --- textures ---
def _levels(px: bytes, w: int, h: int) -> list[tuple[int, int, bytes]]:
    """The picture and every level below it, halved down to 4 x 4: [(w, h, RGBA)], smallest first."""
    out = [(w, h, px)]
    while w > 4 or h > 4:
        nw, nh = max(4, w // 2), max(4, h // 2)
        if nw == w // 2 and nh == h // 2:
            px = halve(px, w, h)
        else:  # one side already 4: halve the other by averaging pairs
            px = _halve_one(px, w, h, nw, nh)
        w, h = nw, nh
        out.append((w, h, px))
    out.reverse()
    return out


def _halve_one(px: bytes, w: int, h: int, nw: int, nh: int) -> bytes:
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        for x in range(nw):
            sx, sy = x * w // nw, y * h // nh
            a = (sy * w + sx) * 4
            b = (min(h - 1, sy + (h // nh) - 1) * w + min(w - 1, sx + (w // nw) - 1)) * 4
            for c in range(4):
                out[(y * nw + x) * 4 + c] = (px[a + c] + px[b + c] + 1) // 2
    return bytes(out)


def dxt5_blocks(px: bytes, w: int, h: int) -> bytes:
    """RGBA pixels (w, h multiples of 4) as DXT5 blocks, row by row."""
    from .unitlook import alpha_block, block_pixels
    out = bytearray()
    for by in range(h // 4):
        for bx in range(w // 4):
            out += alpha_block([p[3] for p in block_pixels(px, w, bx, by, 4, 4)])
            out += dxt.encode_block(block_pixels(px, w, bx, by))
    return bytes(out)


def new_texture(px: bytes, w: int, h: int) -> bytes:
    """A unit texture of our own: DXT5, every level a plain TGU1 payload under TGV flag 1 (as the build writes a
    repainted one: T23), smallest first, down to 4 x 4."""
    levels = []
    for lw, lh, lpx in _levels(px, w, h):
        head = tgu1.Header(tgu1.VERSION, lw // 4, lh // 4, 80, 40, (lw // 4) * (lh // 4), tgu1.FLAG_ALPHA, 0)
        levels.append(head.pack()[:tgu1.PLAIN_HEADER] + dxt5_blocks(lpx, lw, lh))
    return make_tgv(w, h, "DXT5", levels, flag=1)


def new_standin(px: bytes, w: int, h: int) -> bytes:
    """Its stand-in: the level at most STANDIN_SIDE across, raw DXT5 blocks under TGV flag 0 (as the game's)."""
    for lw, lh, lpx in _levels(px, w, h)[::-1]:
        if max(lw, lh) <= STANDIN_SIDE:
            return make_tgv(lw, lh, "DXT5", [dxt5_blocks(lpx, lw, lh)], flag=0)
    raise UnitModelError("no level small enough for a stand-in")


def texture_member(image: str) -> str:
    """ZZ:\\GenTexGroup\\WW2\\...\\X.png -> gen\\ww2\\...\\x.tgv (rusemod.models.texture_member)."""
    from .models import texture_member as member
    return member(image)


def standin_member(member: str) -> str:
    return "gentexproxy\\" + member[len("gen\\"):] if member.startswith("gen\\") else "gentexproxy\\" + member


# --- the packs ---
def _vertex_buffer(part: Part, local: int) -> Buffer:
    out = bytearray()
    for (x, y, z), (nx, ny, nz), (u, v) in zip(part.positions, part.normals, part.uvs):
        out += struct.pack("<3f", x, y, z)
        out += bytes(max(0, min(255, round((c + 1.0) * 127.5))) for c in (nx, ny, nz)) + b"\0"
        out += bytes((255, 0, 0, 0)) + bytes((local, 0, 0, 0))
        out += struct.pack("<2f", u, v - 1.0)  # stored as the game's: v - 1 (its _2wn read back adds the 1)
        out += bytes((0, 0, 255, 255))
    return Buffer(bytes(out), len(out), len(part.positions), 0, 0)


def _index_buffer(part: Part) -> Buffer:
    flat = [i for t in part.triangles for i in t]
    if len(part.positions) <= 0xFFFF:
        data = struct.pack(f"<{len(flat)}H", *flat)
        return Buffer(data, len(data), len(flat), INDEX_16, 0)
    data = struct.pack(f"<{len(flat)}I", *flat)
    return Buffer(data, len(data), len(flat), INDEX_32, 0)


def _retext(nd: Ndf, v: Value, old: str, new: str) -> Value:
    """A material value with the text `old` changed to `new` (inline texts, in lists and pairs too)."""
    if v.tc in (0x07, 0x1C):
        if nd.strings[struct.unpack_from("<I", v.payload)[0]] != old:
            return v
        at = nd.string_index(new)
        return Value(v.tc, struct.pack("<I", nd.add_string(new) if at is None else at))
    if v.tc in (0x11, 0x12):
        items = _subs(v)
        return Value(v.tc, struct.pack("<I", len(items) // (2 if v.tc == 0x12 else 1))
                     + b"".join(_retext(nd, x, old, new).encode() for x in items))
    if v.tc == 0x22:
        return Value(v.tc, b"".join(_retext(nd, x, old, new).encode() for x in _subs(v)))
    return v


def _with_model(raw: bytes, source: str, new: str, prep: Prepared, images: list[str], box: tuple,
                bones: Skeleton) -> MeshPack:
    """A copy of pack `raw` holding `new`: the fitted parts as draw calls, each material a copy of `source`'s body
    material naming its own picture (for MeshPack.add to carry into each pack). `bones`: the copied model's
    skeleton (its entry is in the skeleton packs)."""
    src = MeshPack.read(raw)
    data, mesh, skel = src.items[source]
    first, _count = src.meshes[mesh]
    nd = Ndf(src.materials)
    roots = _material_list(nd)
    spk = Spk(raw)
    body_number = next(d[1] for d in (src.draws[k] for k in range(first, first + src.meshes[mesh][1]))
                       if "CombinedDSCTexture" in spk.materials()[d[1]].get("textures", {}))
    body = nd.objects[roots[body_number]]
    old = next(t for pi, v in body.props if nd.prop_name(pi) == "Textures" for t in _texts(nd, v)
               if t.lower().endswith(".png"))
    skin = next((v for pi, v in body.props if nd.prop_name(pi) == "SkinningRemapping"), None)
    remap = [struct.unpack_from("<i", x.payload)[0] for x in _subs(skin)] if skin is not None else []
    if SKINNED_2F.encode() not in [f.split(b"\0", 1)[0] for f in src.formats]:
        src.formats.append(SKINNED_2F.encode().ljust(256, b"\0"))
    fmt = [f.split(b"\0", 1)[0] for f in src.formats].index(SKINNED_2F.encode())
    material_of: dict = {}
    draws = []
    for part in prep.parts:
        if part.picture not in material_of:
            image = images[part.picture] if part.picture >= 0 else old
            props = [(pi, _retext(nd, v, old, image) if nd.prop_name(pi) == "Textures" else v) for pi, v in body.props]
            n = nd.add_object(body.cls, props)
            roots.append(n)
            material_of[part.picture] = len(roots) - 1
        if part.bone not in bones.names:
            raise UnitModelError(f"{source}'s skeleton has no bone {part.bone} (a part of the .glb is named so)")
        bone = bones.names.index(part.bone)
        if bone not in remap:
            raise UnitModelError(f"the body material of {source} doesn't reach the bone {part.bone}")
        vb = _vertex_buffer(part, remap.index(bone))
        vb.kind = fmt
        src.vbs.append(vb)
        src.ibs.append(_index_buffer(part))
        draws.append((0, material_of[part.picture], len(src.ibs) - 1, len(src.vbs) - 1, 0xFFFF, 0xCDCD))
    root = nd.objects[nd.topo[0]]
    root.props[0] = (root.props[0][0], Value(0x11, struct.pack("<I", len(roots)) + b"".join(
        Value(0x09, struct.pack("<III", 0xBBBBBBBB, n, nd.objects[n].cls)).encode() for n in roots)))
    src.materials = nd.to_logical()
    src.material_count = len(roots)
    flags = struct.unpack_from("<I", data, 24)[0]
    src.items[new] = [struct.pack("<6fI", *box, flags), None, skel]
    src._renumber({new: draws})
    return src


def model_name(source_model: str, unit: str) -> str:
    """The new model's name, beside the copied one's: ww2\\...\\us_m4_sherman\\<unit>lod0.ase2ndfbin."""
    folder = source_model.replace("/", "\\").rsplit("\\", 1)[0]
    return f"{folder}\\{unit}lod0.ase2ndfbin".lower()


@dataclass
class Written:
    changed: dict                 # member of ZZ_Win.dat -> new bytes (the packs)
    added: dict                   # new members -> bytes (the textures)
    model: str                    # the new model's name
    report: dict


def write_unit_model(zz, source_model: str, unit: str, prep: Prepared, earlier: dict | None = None) -> Written:
    """The new unit `unit`'s model `prep` into ZZ_Win.dat `zz` beside `source_model`'s: the changed packs and the
    added textures. `earlier`: members other build steps already changed (path -> bytes), changed from there."""
    earlier = {k.lower(): v for k, v in (earlier or {}).items()}
    src = find_source(zz, source_model)
    new = model_name(src.model, unit)
    if any(new in MeshPack.read(raw).items for raw in src.mesh_packs.values()):
        raise UnitModelError(f"the packs already have a model called {new}")
    folder = src.body_texture.rsplit("\\", 1)[0]
    images = [f"{folder}\\{unit}_{k + 1:02d}.png" for k in range(len(prep.pictures))]
    pts = [p for part in prep.parts for p in part.positions]
    if not pts:
        raise UnitModelError("the model has no points")
    box = tuple(min(p[i] for p in pts) for i in range(3)) + tuple(max(p[i] for p in pts) for i in range(3))
    changed: dict = {}
    first_raw = next(iter(src.mesh_packs.values()))
    carrier = _with_model(first_raw, src.model, new, prep, images, box, src.skeleton)
    for path, raw in src.mesh_packs.items():
        pack = MeshPack.read(earlier.get(path.lower(), raw))
        pack.add(carrier, new)
        changed[path] = pack.to_bytes()
    for path, raw in src.skeleton_packs.items():
        pack = MeshPack.read(earlier.get(path.lower(), raw))
        holder = MeshPack.read(raw)
        holder.items[new] = list(holder.items[src.model])
        pack.add(holder, new)
        changed[path] = pack.to_bytes()
    added: dict = {}
    standins: dict = {}
    for image, (name, w, h, px) in zip(images, prep.pictures):
        member = texture_member(image)
        added[member] = new_texture(px, w, h)
        standins[standin_member(member)] = new_standin(px, w, h)
    body_standin = standin_member(texture_member(src.body_texture))
    for e in zz.entries:
        if not e.path.lower().endswith(".ppk"):
            continue
        raw = earlier.get(e.path.lower()) or bytes(zz.read(e))
        if raw[:8] != PROXY_MAGIC:
            continue
        pack = ProxyPack.read(raw)
        names = pack.names()
        if body_standin not in names:
            continue
        extra = pack.proxies[names.index(body_standin)].extra
        for name, data in standins.items():
            one = ProxyPack([Proxy(standin_key(name), data, extra, name.encode("latin-1").ljust(256, b"\0"))], [0])
            pack.add(one, name)
        changed[e.path] = pack.to_bytes()
    report = dict(prep.report)
    report.update({"model": new, "mesh_packs": sorted(src.mesh_packs), "skeleton_packs": sorted(src.skeleton_packs),
                   "textures": sorted(added), "standin_packs": sorted(p for p in changed if p.lower().endswith(".ppk")),
                   "box": box})
    return Written(changed, added, new, report)
