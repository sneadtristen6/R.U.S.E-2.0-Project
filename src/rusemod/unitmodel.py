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
from .unitlook import halve, make_standin, paint as painted, paint_in
from .unitpacks import NONE, PROXY_MAGIC, Buffer, MeshPack, Proxy, ProxyPack, _material_list, _subs, _texts

MODELS = Path("files") / "models"   # a mod's new units' models: <the unit's name>.glb
PACKS = "gen_5\\pack\\"
SKINNED_2F = ("$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__BlW_4ubn__BlIdx_4ub__TexCoord0_2f__"
              "TexPackedAtlas0_4ubn")
STRIDE = 12 + 4 + 4 + 4 + 8 + 4
ROOT, TURRET = "chassis", "tourelle_01"
PROPELLER_TYPE = "helice"   # a material type starting so draws a spinning-propeller disc (helice_1: the game's 43 planes)
STANDIN_SIDE = 64
INDEX_16, INDEX_32 = 1, 0   # an index buffer's kind: 1 = 16-bit (every one the game ships), else 32-bit


class UnitModelError(ModelError):
    pass


def import_model(game: Path, source_model: str, model_file: Path, out: Path, size: float = 1.0,
                 side: int = 1024, pictures: Path | None = None, aircraft: bool = False,
                 facing: list | None = None) -> dict:
    """Step one for a mod: `model_file` (.3ds or .glb) fitted to the game's model `source_model` (the unit the new
    one copies) and saved as `out` (the mod's files/models/<unit>.glb). A .3ds's pictures are looked for in
    `pictures`, then beside it, then one folder up (downloads often keep them in a folder of their own). `aircraft`:
    the new unit is a plane (its tail fin, its highest point, goes at the back). `facing` ([axis, sign]) pins which way
    it faces instead of working it out (an era unit's library model is already in the game's axes, its front +x: a
    facing pinned by hand when it was fitted stays). Returns the fitting's report (parts and their roles, facing,
    scale, counts, pictures, "missing": pictures not found)."""
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
    like = dict(src.like, aircraft=aircraft, **({"facing": list(facing)} if facing else {}))
    prep = prepare(read_model(model_file), look, like, size=size, side=side)
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
        pivots.append(bone_point((m[0:3], m[4:7], m[8:11]), (m[3], m[7], m[11])))
    return Skeleton(names, par, pivots)


def bone_point(rot, t) -> tuple:
    """Where a bone sits in the model: the point its model -> bone matrix (3 x 3 `rot`, then `t`) takes to the bone's
    origin, -rot⁻¹ t. The matrix isn't always a plain turn: 185 of the 261 skeletons of the game's units scale a bone
    (the Panther's turret 100 times, the Carro Veloce's about 3.9 one way and 3.1 the others), and a turn's inverse
    (its rows read as columns) put the Panther's turret 354,000 units off and an imported model with it (a modder's
    Panther A, 2026-10-18). A matrix with no inverse (none in the game) is read as a plain turn."""
    (a, b, c), (d, e, f), (g, h, i) = rot
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        return tuple(-sum(rot[r][col] * t[r] for r in range(3)) for col in range(3))
    inv = ((e * i - f * h, c * h - b * i, b * f - c * e),
           (f * g - d * i, a * i - c * g, c * d - a * f),
           (d * h - e * g, b * g - a * h, a * e - b * d))
    return tuple(-sum(inv[row][r] * t[r] for r in range(3)) / det for row in range(3))


# --- where the copied unit's model is ---
@dataclass
class Source:
    model: str                     # its name in the packs (lower case)
    mesh_packs: dict               # member path -> raw bytes, every mesh pack that holds it
    skeleton_packs: dict           # member path -> raw bytes, every skeleton pack that holds its skeleton entry
    skeleton: Skeleton | None
    like: dict = field(default_factory=dict)   # for modelin.prepare: length, pivot, ground
    body_texture: str = ""         # its body material's picture (ZZ:\\GenTexGroup\\...\\X01.png)
    look: dict = field(default_factory=dict, repr=False)  # the first mesh pack's materials and its propellers' bones,
    # as read here, for _with_model


def pack_names(zz) -> list:
    """Every mesh pack of ZZ_Win.dat `zz` with the models it names, [(entry, {name: (mesh, skeleton)} or None where
    its name table can't be read alone)], in the archive's order: for packs_holding when it looks for many models
    (a build's own models: each one read every pack whole to find its copied model, 0.2 s a model)."""
    out = []
    for e in zz.entries:
        p = e.path.lower()
        if not (p.startswith(PACKS) and p.endswith(".spk")):
            continue
        raw = bytes(zz.read(e))
        if raw[:8] != b"MESHPCPC":
            continue
        try:
            out.append((e, MeshPack.item_names(raw)))
        except (ValueError, struct.error):
            out.append((e, None))
    return out


def packs_holding(zz, model: str, names: list | None = None) -> tuple[str, dict, dict]:
    """The model `model` (its pack name, any case) across ZZ_Win.dat's packs: (its name as the packs have it, the mesh
    packs that hold it, the skeleton packs that hold its skeleton entry: {member path: raw bytes} each).
    UnitModelError when no pack holds it. `names`: pack_names(zz), so only the packs naming it are read whole."""
    model = model.replace("/", "\\").lower()
    if model.startswith("datadir:\\"):
        model = model[len("datadir:\\"):]
    meshes, skeletons = {}, {}
    entries = zz.entries if names is None else [e for e, n in names if n is None or model in n]
    for e in entries:
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
    return model, meshes, skeletons


def find_source(zz, model: str, names: list | None = None) -> Source:
    """The copied unit's model `model` (its pack name, any case) across ZZ_Win.dat's packs, and what fitting to it
    needs. UnitModelError when no pack holds it, or it has no bones. `names`: as packs_holding takes it."""
    model, meshes, skeletons = packs_holding(zz, model, names)
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
    hull, hull_y, low = [], [], math.inf
    body = None
    propellers = []
    for part in spk.model(model):
        remap = mats[part.material].get("skinning") or []
        tex = next(iter(mats[part.material].get("textures", {}).values()), "")
        if body is None and "CombinedDSCTexture" in mats[part.material].get("textures", {}):
            body = tex
        if mats[part.material].get("type", "").startswith(PROPELLER_TYPE):
            propellers += _discs(part, remap, bones)
        for i in range(len(part.positions) // 3):
            p = part.positions[3 * i:3 * i + 3]
            low = min(low, p[2])
            b = part.bones[i] if i < len(part.bones) else [0]
            w = part.weights[i] if i < len(part.weights) else [255]
            heavy = max(range(len(w)), key=lambda k: w[k])
            if (remap[b[heavy]] if b[heavy] < len(remap) else b[heavy]) == bones.names.index(ROOT):
                hull.append(p[0])
                hull_y.append(p[1])
    if not hull or body is None:
        raise UnitModelError(f"{model} has no hull on its {ROOT} bone, or no body texture (CombinedDSCTexture)")
    pivot = bones.pivots[bones.names.index(TURRET)] if TURRET in bones.names else ((max(hull) + min(hull)) / 2, 0.0, 0)
    like = {"length": max(hull) - min(hull), "width": max(hull_y) - min(hull_y), "pivot": (pivot[0], pivot[1]),
            "ground": low, "middle": (max(hull) + min(hull)) / 2, "propellers": propellers}
    return Source(model, meshes, skeletons, bones, like, body,
                  {"mats": mats, "disc_bones": {d["bone"] for d in propellers}})


def _discs(part, remap: list, bones: Skeleton) -> list[dict]:
    """A propeller draw's discs (each a piece of 4 points: all 59 of the game's) as modelin.fit_discs takes them:
    {"bone": the bone it spins on (helice_hs_1...), "centre": its middle, "radius": half its widest side}."""
    from .modelin import pieces
    n = len(part.positions) // 3
    tris = [tuple(part.indices[k:k + 3]) for k in range(0, len(part.indices) - 2, 3)]
    out = []
    for pts in pieces(tris, n):
        xyz = [part.positions[3 * i:3 * i + 3] for i in pts]
        box = [(min(p[k] for p in xyz), max(p[k] for p in xyz)) for k in range(3)]
        local = part.bones[pts[0]][0] if pts[0] < len(part.bones) else 0
        bone = remap[local] if local < len(remap) else local
        out.append({"bone": bones.names[bone] if bone < len(bones.names) else "",
                    "centre": tuple((lo + hi) / 2 for lo, hi in box),
                    "radius": max(hi - lo for lo, hi in box) / 2})
    return out


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
    """The picture and every level below it, each half the one above, until its shorter side is 4: [(w, h, RGBA)],
    smallest first. The game makes room for level k of a w x h DXT texture as (w * h / 16) >> 2k blocks, rounded
    down, and writes as many blocks as the level holds: a level past the shorter side's 4 gets no room and its block
    is written past the end (T35 run 3: a 1024 x 512 texture down to 4 x 4 corrupted the game's memory). Every one of
    the game's own textures stops there (1024 x 512: 8 levels, the last 8 x 4)."""
    out = [(w, h, px)]
    while min(w, h) > 4:
        px, w, h = halve(px, w, h), w // 2, h // 2
        out.append((w, h, px))
    out.reverse()
    return out


def level_room(w: int, h: int, k: int) -> int:
    """The blocks the game makes room for at level k (0: the full picture) of a w x h DXT texture."""
    return (w * h // 16) >> (2 * k)


def dxt5_blocks(px: bytes, w: int, h: int) -> bytes:
    """RGBA pixels (w, h multiples of 4) as DXT5 blocks, row by row. With numpy there (rusemod.dxtnp), every block at
    once: the same bytes (a 2048 x 2048 picture's levels in seconds, not a minute); these loops are what that is checked
    against."""
    from . import unitlook
    from .unitlook import alpha_block, block_pixels
    if unitlook.whole_arrays():
        from .dxtnp import encode_dxt5_blocks, np
        rows = np.frombuffer(px, dtype=np.uint8)[:w * h * 4].reshape(h // 4, 4, w // 4, 4, 4)
        return encode_dxt5_blocks(rows.transpose(0, 2, 1, 3, 4).reshape(-1, 64))
    out = bytearray()
    for by in range(h // 4):
        for bx in range(w // 4):
            out += alpha_block([p[3] for p in block_pixels(px, w, bx, by, 4, 4)])
            out += dxt.encode_block(block_pixels(px, w, bx, by))
    return bytes(out)


def not_too_thin(px: bytes, w: int, h: int) -> tuple[bytes, int, int]:
    """A texture more than STANDIN_SIDE / 4 times longer than it is wide with its shorter side's pixels repeated until
    it isn't: (RGBA, w, h). Its levels stop at a shorter side of 4 (_levels), so such a strip has no level
    STANDIN_SIDE across for its stand-in (the HZ-5 (Il-28R)'s 256 x 8 stopped a build, 2026-10-30). Each pixel is
    repeated, so the picture on the model is the same; any other texture comes back as it is."""
    while max(w, h) > STANDIN_SIDE // 4 * min(w, h):
        if w > h:  # each row twice
            px, h = b"".join(px[y * w * 4:(y + 1) * w * 4] * 2 for y in range(h)), h * 2
        else:      # each pixel twice across
            px, w = b"".join(px[i * 4:i * 4 + 4] * 2 for i in range(w * h)), w * 2
    return px, w, h


def new_texture(px: bytes, w: int, h: int) -> bytes:
    """A unit texture of our own: DXT5, every level a plain TGU1 payload under TGV flag 1 (as the build writes a
    repainted one: T23), smallest first, until the shorter side is 4 (_levels). Each level holds exactly the blocks
    the game makes room for (level_room), or nothing is written. A strip is widened first (not_too_thin)."""
    px, w, h = not_too_thin(px, w, h)
    levels = []
    chain = _levels(px, w, h)
    for k, (lw, lh, lpx) in zip(range(len(chain) - 1, -1, -1), chain):
        blocks = (lw // 4) * (lh // 4)
        if blocks != level_room(w, h, k):
            # not a game rule we chose: the game writes a level's blocks into the room it made for them
            raise UnitModelError(f"a {w} x {h} texture's level {k} ({lw} x {lh}) holds {blocks} blocks; the game makes "
                                 f"room for {level_room(w, h, k)}")
        head = tgu1.Header(tgu1.VERSION, lw // 4, lh // 4, 80, 40, blocks, tgu1.FLAG_ALPHA, 0)
        levels.append(head.pack()[:tgu1.PLAIN_HEADER] + dxt5_blocks(lpx, lw, lh))
    return make_tgv(w, h, "DXT5", levels, flag=1)


def new_standin(px: bytes, w: int, h: int) -> bytes:
    """Its stand-in: the level at most STANDIN_SIDE across, raw DXT5 blocks under TGV flag 0 (as the game's). A strip
    is widened first, as new_texture widens it (not_too_thin), so the stand-in is one of the texture's own levels."""
    px, w, h = not_too_thin(px, w, h)
    for lw, lh, lpx in _levels(px, w, h)[::-1]:
        if max(lw, lh) <= STANDIN_SIDE:
            return make_tgv(lw, lh, "DXT5", [dxt5_blocks(lpx, lw, lh)], flag=0)
    raise UnitModelError("no level small enough for a stand-in")


def texture_member(image: str) -> str:
    """ZZ:\\GenTexGroup\\WW2\\...\\X.png -> gen\\ww2\\...\\x.tgv (rusemod.models.texture_member)."""
    from .models import texture_member as member
    return member(image)


def texture_group(picture: str) -> str:
    """The texture group a model's picture belongs to: the start of its own file name, up to the first _ (the
    Sherman's TSCCombCS_CombinedDSCTexture01.png: TSCCombCS). The game finds a model's picture through that group,
    so a new picture's name starts the same way (T35 runs 1 and 2: pictures named descriptor_unit_..._01.png named a
    group "descriptor" the game doesn't have, and it crashed when the unit was built)."""
    name = picture.replace("/", "\\").rsplit("\\", 1)[-1]
    if "_" not in name:
        raise UnitModelError(f"{name}: no texture group in its name (the part before the first _)")
    return name.split("_", 1)[0]


def standin_member(member: str) -> str:
    return "gentexproxy\\" + member[len("gen\\"):] if member.startswith("gen\\") else "gentexproxy\\" + member


# --- the packs ---
def _vertex_buffer(part: Part, local: int) -> Buffer:
    """A part's points in the game's skinned format (SKINNED_2F, STRIDE bytes each). With numpy there
    (rusemod.modelinnp.vertex_bytes), every point at once: the same bytes; these loops are what that is checked
    against."""
    from .modelin import whole_arrays
    arrays = whole_arrays()
    data = arrays.vertex_bytes(part, local) if arrays else None
    if data is None:
        out = bytearray()
        for (x, y, z), (nx, ny, nz), (u, v) in zip(part.positions, part.normals, part.uvs):
            out += struct.pack("<3f", x, y, z)
            out += bytes(max(0, min(255, round((c + 1.0) * 127.5))) for c in (nx, ny, nz)) + b"\0"
            out += bytes((255, 0, 0, 0)) + bytes((local, 0, 0, 0))
            out += struct.pack("<2f", u, v - 1.0)  # stored as the game's: v - 1 (its _2wn read back adds the 1)
            out += bytes((0, 0, 255, 255))
        data = bytes(out)
    return Buffer(data, len(data), len(part.positions), 0, 0)


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
                bones: Skeleton, memo: dict | None = None) -> MeshPack:
    """A copy of pack `raw` holding `new`: the fitted parts as draw calls, each material a copy of `source`'s body
    material naming its own picture (for MeshPack.add to carry into each pack); a part on a bone `source`'s own
    propeller discs spin on is a disc too, its material a copy of `source`'s propeller material (MaterialType
    helice_1: the game draws it as a spinning disc) naming its picture. `bones`: the copied model's skeleton (its
    entry is in the skeleton packs). `memo`: a dict kept for this `raw` and `source` (Source.look: the pack's
    materials and the propellers' bones as find_source read them, once for every model copying `source`)."""
    src = MeshPack.read(raw)
    data, mesh, skel = src.items[source]
    first, _count = src.meshes[mesh]
    nd = Ndf(src.materials)
    roots = _material_list(nd)
    if memo is None or "mats" not in memo:
        spk = Spk(raw)
        mats = spk.materials()
        disc_bones = {d["bone"] for p in spk.model(source)
                      if mats[p.material].get("type", "").startswith(PROPELLER_TYPE)
                      for d in _discs(p, mats[p.material].get("skinning") or [], bones)}
        if memo is not None:
            memo["mats"], memo["disc_bones"] = mats, disc_bones
    else:
        mats, disc_bones = memo["mats"], memo["disc_bones"]
    own = [src.draws[k][1] for k in range(first, first + src.meshes[mesh][1])]
    body_number = next(m for m in own if "CombinedDSCTexture" in mats[m].get("textures", {}))
    disc_number = next((m for m in own if mats[m].get("type", "").startswith(PROPELLER_TYPE)), None)

    def material(number: int):
        """(the material object, the picture its Textures name, its bone numbers' remapping)."""
        obj = nd.objects[roots[number]]
        pic = next(t for pi, v in obj.props if nd.prop_name(pi) == "Textures" for t in _texts(nd, v)
                   if t.lower().endswith(".png"))
        skin = next((v for pi, v in obj.props if nd.prop_name(pi) == "SkinningRemapping"), None)
        return obj, pic, [struct.unpack_from("<i", x.payload)[0] for x in _subs(skin)] if skin is not None else []

    looks = {"body": material(body_number)}
    if disc_number is not None:
        looks["disc"] = material(disc_number)
    if SKINNED_2F.encode() not in [f.split(b"\0", 1)[0] for f in src.formats]:
        src.formats.append(SKINNED_2F.encode().ljust(256, b"\0"))
    fmt = [f.split(b"\0", 1)[0] for f in src.formats].index(SKINNED_2F.encode())
    material_of: dict = {}
    draws = []
    for part in prep.parts:
        look = "disc" if part.bone in disc_bones and "disc" in looks else "body"
        base, old, remap = looks[look]
        if (look, part.picture) not in material_of:
            image = images[part.picture] if part.picture >= 0 else old
            props = [(pi, _retext(nd, v, old, image) if nd.prop_name(pi) == "Textures" else v) for pi, v in base.props]
            n = nd.add_object(base.cls, props)
            roots.append(n)
            material_of[(look, part.picture)] = len(roots) - 1
        if part.bone not in bones.names:
            raise UnitModelError(f"{source}'s skeleton has no bone {part.bone} (a part of the .glb is named so)")
        bone = bones.names.index(part.bone)
        if bone not in remap:
            raise UnitModelError(f"the {look} material of {source} doesn't reach the bone {part.bone}")
        vb = _vertex_buffer(part, remap.index(bone))
        vb.kind = fmt
        src.vbs.append(vb)
        src.ibs.append(_index_buffer(part))
        draws.append((0, material_of[(look, part.picture)], len(src.ibs) - 1, len(src.vbs) - 1, 0xFFFF, 0xCDCD))
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


def write_unit_model(zz, source_model: str, unit: str, prep: Prepared, earlier: dict | None = None,
                     batch: dict | None = None, textures: list | None = None) -> Written:
    """The new unit `unit`'s model `prep` into ZZ_Win.dat `zz` beside `source_model`'s: the changed packs and the
    added textures. `earlier`: members other build steps already changed (path -> bytes), changed from there.
    `batch`: one build's own models written together (a dict the caller keeps for them all, then write_batch): each
    pack is read once, grows as the models go in and is written once, and each source model is found once (the owner,
    2026-10-30: a copy with every era unit's own model; one by one, each model read and wrote the eight nations' model
    packs again, hours and many GB for hundreds). Its Written.changed then names the packs, with None for their bytes.
    `textures`: its pictures already made into the game's textures, [(texture, stand-in)] in prep.pictures' order
    (KeptModels: a model kept from an earlier build, its pictures then without their pixels)."""
    earlier = {k.lower(): v for k, v in (earlier or {}).items()}
    if batch is None:
        src = find_source(zz, source_model)
    else:
        sources = batch.setdefault("sources", {})
        key = source_model.replace("/", "\\").lower()
        if key not in sources:
            if "names" not in batch:
                batch["names"] = pack_names(zz)
            sources[key] = find_source(zz, source_model, batch["names"])
        src = sources[key]
    new = model_name(src.model, unit)

    def grown(path: str, raw: bytes, kind):  # the pack as this build has it so far
        if batch is None:
            return kind.read(earlier.get(path.lower(), raw))
        packs = batch.setdefault("packs", {})
        if path.lower() not in packs:
            packs[path.lower()] = [path, kind.read(earlier.get(path.lower(), raw))]
        return packs[path.lower()][1]

    if any(new in grown(path, raw, MeshPack).items for path, raw in src.mesh_packs.items()):
        raise UnitModelError(f"the packs already have a model called {new}")
    folder, body = src.body_texture.rsplit("\\", 1)
    group = texture_group(body)
    images = [f"{folder}\\{group}_{unit}_{k + 1:02d}.png" for k in range(len(prep.pictures))]
    pts = [p for part in prep.parts for p in part.positions]
    if not pts:
        raise UnitModelError("the model has no points")
    cols = [[p[i] for p in pts] for i in range(3)]
    box = tuple(min(c) for c in cols) + tuple(max(c) for c in cols)
    changed: dict = {}

    def keep(path: str, pack) -> None:  # written now, or (a batch) once, after the last model
        if batch is None:
            changed[path] = pack.to_bytes()
        else:
            batch.setdefault("touched", set()).add(path.lower())
            changed[path] = None

    first_raw = next(iter(src.mesh_packs.values()))
    carrier = _with_model(first_raw, src.model, new, prep, images, box, src.skeleton, src.look)
    for path, raw in src.mesh_packs.items():
        pack = grown(path, raw, MeshPack)
        pack.add(carrier, new)
        keep(path, pack)
    for path, raw in src.skeleton_packs.items():
        pack = grown(path, raw, MeshPack)
        holder = MeshPack.read(raw)
        holder.items[new] = list(holder.items[src.model])
        pack.add(holder, new)
        keep(path, pack)
    added: dict = {}
    standins: dict = {}
    for k, (image, (name, w, h, px)) in enumerate(zip(images, prep.pictures)):
        member = texture_member(image)
        texture, standin = textures[k] if textures is not None else (new_texture(px, w, h), new_standin(px, w, h))
        added[member] = texture
        standins[standin_member(member)] = standin
    body_standin = standin_member(texture_member(src.body_texture))
    proxies = batch.get("proxies") if batch is not None else None
    if proxies is None:  # every stand-in pack, read once (a batch keeps them for every model)
        proxies = []
        for e in zz.entries:
            if not e.path.lower().endswith(".ppk"):
                continue
            raw = earlier.get(e.path.lower()) or bytes(zz.read(e))
            if raw[:8] == PROXY_MAGIC:
                proxies.append((e.path, raw))
        if batch is not None:
            batch["proxies"] = proxies
    for path, raw in proxies:
        pack = grown(path, raw, ProxyPack)
        names = pack.names()
        if body_standin not in names:
            continue
        extra = pack.proxies[names.index(body_standin)].extra
        for name, data in standins.items():
            one = ProxyPack([Proxy(standin_key(name), data, extra, name.encode("latin-1").ljust(256, b"\0"))], [0])
            pack.add(one, name)
        keep(path, pack)
    report = dict(prep.report)
    report.update({"model": new, "mesh_packs": sorted(src.mesh_packs), "skeleton_packs": sorted(src.skeleton_packs),
                   "textures": sorted(added), "standin_packs": sorted(p for p in changed if p.lower().endswith(".ppk")),
                   "box": box})
    return Written(changed, added, new, report)


KEPT_FOLDER = "own-models"   # in the build cache: packs of kept own models (rusemod.mapkeep's tile packs)
KEPT_MOST = 4 << 30          # bytes of them kept at most, the most recently used
KEPT_PACK = 256 << 20        # a build's new kept models written as a pack once they come to this many bytes
KEPT_MAGIC = b"RUSEOWN1"
KEPT_WIDTHS = (3, 3, 2, 3)   # a point's numbers: position, normal, texture place, a triangle's corners


class KeptModels:
    """A build's own models kept between builds, so a build of a mod whose .glb files are the same as an earlier
    build's takes each model as read and its pictures as the game's textures from there instead of making them
    again: in bigpacks14's build (2026-11-01; the owner: "keep working until this bug is solved and works quickly to
    build") its 297 own models took 816 of its 1,103 s, reading the models and making their textures most of each.
    A model is kept under a fingerprint of its .glb's bytes and the kept own models' format number (rusemod.keptformat
    "ownmodel"), whichever mod or copy built it, in packs of their own in the build cache (rusemod.mapkeep's tile
    packs: one file a pack, not a file a model); a damaged one is made again. Not kept: what each build does with the
    game's packs (the copied model found, the new one added to them), which depends on the game and the other mods."""

    def __init__(self, cache):
        self.cache = cache
        self.new: dict = {}
        self.size = 0
        self.made: dict = {}    # prepare's records, until get takes each
        self.names: dict = {}   # a .glb's path -> its fingerprint, as prepare read it

    def prepare(self, glbs, workers: int | None = None) -> None:
        """The .glb files of `glbs` that aren't kept yet made side by side, biggest first, each kept as it is done, for
        get: one after another, a first build of bigpacks14's mod spent 845 of its 935 s on its 284 own models
        (2026-11-01). Worker programs read the .glb files (rusemod.mend's pool, half the workers: they run without
        Numba, mend._pool's rule) and threads of this program make their pictures into textures (Numba's encoder lets
        go of Python's lock: 256 pictures 18.0 s one after another, 5.5 s on 7 threads, the same bytes; in the workers
        without Numba they took six times as long), at most two models a worker in hand. A record made here is what
        get keeps, and get reading a kept model gives what making it gives (bigpacks14speed built both ways: every
        member the same). Fewer than two to make, or one worker: nothing done here; a model that couldn't be made
        here (or a pool that couldn't start), get makes as before, its error then the build's."""
        from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
        from .mapkeep import tile_names
        from .mend import WORKERS, _pool
        from . import unitlook
        workers = WORKERS if workers is None else workers
        todo: dict = {}
        for glb in glbs:
            try:
                name = self.names[str(glb)] = _kept_name(Path(glb).read_bytes())
            except OSError:
                continue  # get says so
            todo.setdefault(name, str(glb))
        for name in tile_names(self.cache, KEPT_FOLDER):
            todo.pop(name, None)
        if len(todo) < 2 or workers < 2:
            return
        jobs = sorted(todo.items(), key=lambda kv: -Path(kv[1]).stat().st_size)
        unitlook.whole_arrays()
        try:  # the encoder with Numba in this program before the pool keeps it out of the workers (mend._pool)
            from . import dxtnp  # noqa: F401
        except ImportError:
            pass
        reading: dict = {}   # future -> fingerprint
        making: dict = {}
        try:
            with _pool(_kept_start, (), max(1, min(workers // 2, len(jobs)))) as readers, \
                    ThreadPoolExecutor(workers) as makers:
                while jobs or reading or making:
                    while jobs and len(reading) + len(making) < 2 * workers:
                        name, glb = jobs.pop(0)
                        reading[readers.submit(_kept_read_job, glb)] = name
                    done, _ = wait(list(reading) + list(making), return_when=FIRST_COMPLETED)
                    for f in done:
                        if f in reading:
                            name = reading.pop(f)
                            prep = f.result() if f.exception() is None else None
                            if prep is not None:
                                making[makers.submit(_kept_made, prep)] = name
                            continue
                        name = making.pop(f)
                        record = f.result()
                        if record is None:
                            continue
                        self.made[name] = record
                        if self.cache is not None:
                            self.new[name] = record
                            self.size += len(record)
                            if self.size >= KEPT_PACK:
                                self.close()
        except Exception:  # noqa: BLE001 (a pool that broke: what was made is kept, get makes the rest)
            pass

    def get(self, glb) -> tuple[Prepared, list]:
        """(the .glb as read_mod_glb reads it, its pictures as the game's textures [(texture, stand-in)]) for
        write_unit_model; its pictures without their pixels (only their names and sizes are used then)."""
        from .mapkeep import read_tiles
        name = self.names.get(str(glb))
        if name is not None and name in self.made:
            got = _kept_read(self.made.pop(name))
            if got is not None:
                return got
        if name is None:
            data = Path(glb).read_bytes() if self.cache is not None else b""
            name = _kept_name(data) if self.cache is not None else b""
        if self.cache is not None:
            record = self.new.get(name) or read_tiles(self.cache, [name], folder=KEPT_FOLDER).get(name)
            got = _kept_read(record) if record else None
            if got is not None:
                return got
        prep = read_mod_glb(glb)
        textures = [(new_texture(px, w, h), new_standin(px, w, h)) for _n, w, h, px in prep.pictures]
        prep = Prepared(prep.parts, [[n, w, h, b""] for n, w, h, _px in prep.pictures], prep.report)
        if self.cache is not None:
            try:
                record = _kept_bytes(prep, textures)
            except (ValueError, TypeError, OverflowError):
                record = None      # not kept (a model laid out as this doesn't know): made again next time
            if record is not None:
                self.new[name] = record
                self.size += len(record)
                if self.size >= KEPT_PACK:
                    self.close()
        return prep, textures

    def close(self) -> None:
        """Keep the models made since the last pack, as one pack."""
        from .mapkeep import write_tiles
        if self.new:
            write_tiles(self.cache, self.new, most=KEPT_MOST, folder=KEPT_FOLDER)
        self.new, self.size = {}, 0


def _kept_start() -> None:
    """A worker of KeptModels.prepare's pool: nothing shared."""


def _kept_read_job(glb: str) -> Prepared | None:
    """In a worker: the .glb as read_mod_glb reads it, or None when it can't be (get then makes it, its error the
    build's)."""
    try:
        return read_mod_glb(Path(glb))
    except Exception:  # noqa: BLE001 (made again by get, which says what went wrong)
        return None


def _kept_made(prep: Prepared) -> bytes | None:
    """On a thread: a model read (_kept_read_job) with its pictures made into textures, as a kept record
    (KeptModels.get makes the same), or None when it can't be."""
    try:
        textures = [(new_texture(px, w, h), new_standin(px, w, h)) for _n, w, h, px in prep.pictures]
        return _kept_bytes(Prepared(prep.parts, [[n, w, h, b""] for n, w, h, _px in prep.pictures], prep.report),
                           textures)
    except Exception:  # noqa: BLE001 (made again by get, which says what went wrong)
        return None


def _kept_name(data: bytes) -> bytes:
    import hashlib
    from .keptformat import stamp
    return hashlib.blake2b(stamp("ownmodel") + data, digest_size=20).digest()


def _kept_bytes(prep: Prepared, textures: list) -> bytes:
    """A kept model: its parts' numbers exactly as read (64-bit floats, 64-bit corners), its report and pictures'
    names and sizes, and its textures and stand-ins, compressed. ValueError for a part whose points aren't all as
    wide."""
    import json
    import zlib
    from array import array
    parts, blobs = [], []
    for p in prep.parts:
        row = [p.bone, p.picture]
        for seq, width, kind in zip((p.positions, p.normals, p.uvs, p.triangles), KEPT_WIDTHS, "dddq"):
            if any(len(v) != width for v in seq):
                raise ValueError("a part's points aren't all as wide")
            row.append(len(seq))
            blobs.append(array(kind, (x for v in seq for x in v)).tobytes())
        parts.append(row)
    head = json.dumps({"report": prep.report, "pictures": [[n, w, h] for n, w, h, _px in prep.pictures],
                       "parts": parts}).encode("utf-8")
    out = [KEPT_MAGIC, struct.pack("<I", len(head)), head]
    for b in blobs:
        out += [struct.pack("<Q", len(b)), b]
    for texture, standin in textures:
        out += [struct.pack("<QQ", len(texture), len(standin)), texture, standin]
    return zlib.compress(b"".join(out), 1)


def _kept_read(record: bytes) -> tuple[Prepared, list] | None:
    """A kept model back (_kept_bytes), or None when it can't be read as one."""
    import json
    import zlib
    from array import array
    try:
        raw = zlib.decompress(record)
        if raw[:8] != KEPT_MAGIC:
            return None
        at = 8
        (n,) = struct.unpack_from("<I", raw, at)
        head = json.loads(raw[at + 4:at + 4 + n].decode("utf-8"))
        at += 4 + n

        def blob() -> bytes:
            nonlocal at
            (size,) = struct.unpack_from("<Q", raw, at)
            b = raw[at + 8:at + 8 + size]
            if len(b) != size:
                raise ValueError("cut short")
            at += 8 + size
            return b
        parts = []
        for bone, picture, *counts in head["parts"]:
            seqs = []
            for count, width, kind in zip(counts, KEPT_WIDTHS, "dddq"):
                a = array(kind)
                a.frombytes(blob())
                if len(a) != count * width:
                    return None
                seqs.append(list(zip(*[iter(a.tolist())] * width)))
            parts.append(Part(bone, picture, *seqs))
        textures = []
        for _p in head["pictures"]:
            sizes = struct.unpack_from("<QQ", raw, at)
            at += 16
            textures.append((raw[at:at + sizes[0]], raw[at + sizes[0]:at + sizes[0] + sizes[1]]))
            at += sizes[0] + sizes[1]
        if at != len(raw):
            return None
        return Prepared(parts, [[n, w, h, b""] for n, w, h in head["pictures"]], head["report"]), textures
    except (ValueError, KeyError, TypeError, struct.error, zlib.error, UnicodeDecodeError):
        return None


def write_batch(batch: dict) -> dict:
    """The packs a batch of write_unit_model calls changed, written once: {member: bytes}. Each pack is let go once
    it is bytes, so a big batch never holds every pack twice; the batch is done with after this."""
    packs, out = batch.get("packs", {}), {}
    for k in sorted(batch.get("touched", ())):
        if k in packs:
            path, pack = packs.pop(k)
            out[path] = pack.to_bytes()
    return out


# --- a new unit's own copy of the model it copies (the owner, 2026-10-11: "duplicate that part"): the same mesh,
# bones and moving parts, its textures its own, so Repaint in Blender changes that unit only and not every unit drawn
# with the game's model (a Discord player wanted new roundels on the new units of a mod) ---
COPY = ".copy.toml"  # files/models/<the unit's name>.copy.toml: the unit has its own copy; its paint in files/models/<name>/


def mod_copies(folder: Path) -> dict:
    """{a unit's name: (the models it has copies of, as its .copy.toml's `of` lists them ([] if it names none: the
    build then copies the one its GfxDescriptor draws), its paint ({the copied models' texture in ZZ_Win.dat: (colour
    PNG, alpha PNG)}, laid out as files/replace: rusemod.unitlook.paint_in))} from a mod's
    files/models/<the unit's name>.copy.toml and files/models/<the unit's name>/. UnitModelError for a .copy.toml that
    can't be read."""
    import tomllib
    root = Path(folder) / MODELS
    if not root.is_dir():
        return {}
    out: dict = {}
    for f in sorted(root.glob("*" + COPY)):
        unit = f.name[:-len(COPY)]
        try:
            of = tomllib.loads(f.read_text(encoding="utf-8")).get("of") or []
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise UnitModelError(f"{MODELS.as_posix()}/{f.name} can't be read: {exc}") from None
        of = [of] if isinstance(of, str) else of
        if not isinstance(of, list) or not all(isinstance(m, str) and m.strip() for m in of):
            raise UnitModelError(f"{MODELS.as_posix()}/{f.name}: `of` names a model or a list of models")
        out[unit] = (of, paint_in(root / unit))
    return out


def model_key(model: str) -> str:
    """A model's name as the packs have it: ww2\\res3d\\...\\x.ase2ndfbin (any case, / or \\, a DataDir: in front)."""
    model = model.replace("/", "\\").lower()
    return model[len("datadir:\\"):] if model.startswith("datadir:\\") else model


def copy_model_name(source_model: str, unit: str, several: bool = False) -> str:
    """The name of a unit's copy of the game's model `source_model`, beside it, its folder written as the source's
    is: ...\\<unit>lod0.Ase2ndfbin, or ...\\<unit>_<the source's name>lod0.Ase2ndfbin when the unit has copies of
    several models (a squad's soldiers, its bazooka man)."""
    path = source_model.replace("/", "\\")
    if path.lower().startswith("datadir:\\"):
        path = path[len("datadir:\\"):]
    folder, base = path.rsplit("\\", 1)
    stem = base[:-len(".ase2ndfbin")] if base.lower().endswith(".ase2ndfbin") else base
    stem = stem[:-len("lod0")] if stem.lower().endswith("lod0") else stem
    return f"{folder}\\{unit}_{stem}lod0.Ase2ndfbin" if several else f"{folder}\\{unit}lod0.Ase2ndfbin"


def copy_name(picture: str, unit: str) -> str:
    """A copied texture's name, beside the game's and in its texture group (texture_group: the game finds a model's
    picture through it): ...\\TSCCombCS_CombinedDSCTexture01.png -> ...\\TSCCombCS_<unit>_CombinedDSCTexture01.png."""
    folder, name = picture.replace("/", "\\").rsplit("\\", 1)
    return f"{folder}\\{texture_group(name)}_{unit}_{name.split('_', 1)[1]}"


def _copied(raw: bytes, source: str, new: str, pictures: dict) -> MeshPack:
    """A copy of pack `raw` holding `new`: `source`'s draw calls on its own buffers (MeshPack.add then shares them),
    each material a copy naming the pictures as `pictures` says ({the game's picture: the copy's})."""
    src = MeshPack.read(raw)
    data, mesh, skel = src.items[source]
    first, count = src.meshes[mesh]
    nd = Ndf(src.materials)
    roots = _material_list(nd)
    copies: dict = {}
    draws = []
    for d in range(first, first + count):
        a, m, ib, vb, e, f = src.draws[d]
        if m not in copies:
            body = nd.objects[roots[m]]
            props = []
            for pi, v in body.props:
                if nd.prop_name(pi) == "Textures":
                    for old, picture in pictures.items():
                        v = _retext(nd, v, old, picture)
                props.append((pi, v))
            roots.append(nd.add_object(body.cls, props))
            copies[m] = len(roots) - 1
        draws.append((a, copies[m], ib, vb, e, f))
    root = nd.objects[nd.topo[0]]
    root.props[0] = (root.props[0][0], Value(0x11, struct.pack("<I", len(roots)) + b"".join(
        Value(0x09, struct.pack("<III", 0xBBBBBBBB, n, nd.objects[n].cls)).encode() for n in roots)))
    src.materials = nd.to_logical()
    src.material_count = len(roots)
    src.items[new] = [data, None, skel]
    src._renumber({new: draws})
    return src


def write_unit_copy(zz, copies, unit: str, paint: dict | None = None, earlier: dict | None = None) -> Written:
    """The unit `unit`'s own copies of the game's models into ZZ_Win.dat `zz`, each beside its model: `copies`
    ({the game's model: its copy's name}, or one model's name: copied as ...\\<unit>lod0). Each copy has the same mesh,
    bones and draw calls (its vertex and index buffers shared in each pack); the models' textures are copied once for
    the unit under names of its own (copy_name: a squad's soldiers and its bazooka man share theirs, as the game's do)
    and painted as `paint` says ({the game's texture member: (colour PNG, alpha PNG)}: the Studio's Repaint in Blender
    on the copy), with their stand-ins. `earlier`: members other build steps already changed (path -> bytes), changed
    from there."""
    if isinstance(copies, str):
        copies = {copies: copy_model_name(copies, unit)}
    earlier = {k.lower(): v for k, v in (earlier or {}).items()}
    paint = {k.lower().replace("/", "\\"): v for k, v in (paint or {}).items()}
    held = []  # (the game's model, its copy, its mesh packs, its skeleton packs)
    for source, new in copies.items():
        model, meshes, skeletons = packs_holding(zz, source)
        new = model_key(new)
        if any(new in MeshPack.read(raw).items for raw in meshes.values()):
            raise UnitModelError(f"the packs already have a model called {new}")
        held.append((model, new, meshes, skeletons))
    pictures: dict = {}
    for model, _new, meshes, _skeletons in held:
        pictures.update({pic: copy_name(pic, unit) for pic in MeshPack.read(next(iter(meshes.values()))).textures(model)
                         if zz.entry(texture_member(pic)) is not None})  # (a picture of no texture here stays shared)
    if not pictures:
        raise UnitModelError(f"{', '.join(m for m, *_ in held)}: no textures of their own to copy")
    changed: dict = {}

    def current(path: str, raw: bytes) -> bytes:  # a pack as the copies before this one and earlier steps left it
        return changed.get(path) or earlier.get(path.lower(), raw)
    for model, new, meshes, skeletons in held:
        carrier = _copied(next(iter(meshes.values())), model, new, pictures)
        for path, raw in meshes.items():
            pack = MeshPack.read(current(path, raw))
            pack.add(carrier, new)
            changed[path] = pack.to_bytes()
        for path, raw in skeletons.items():
            pack = MeshPack.read(current(path, raw))
            holder = MeshPack.read(raw)
            holder.items[new] = list(holder.items[model])
            pack.add(holder, new)
            changed[path] = pack.to_bytes()
    added: dict = {}
    standins: dict = {}  # the copy's stand-in -> (the game's, what painting it needs or None)
    for old, picture in pictures.items():
        old_member, member = texture_member(old), texture_member(picture)
        original = bytes(zz.read(zz.entry(old_member)))
        colour, alpha = paint.get(old_member, (None, None))
        stand = None
        if colour is not None or alpha is not None:
            kind, original, _report, stand = painted(original, colour, alpha)
            if kind != "texture":
                raise UnitModelError(f"{old_member} isn't a model's texture")
        added[member] = original
        standins[standin_member(member)] = (standin_member(old_member), stand)
    for e in zz.entries:  # every stand-in pack holding a copied texture's stand-in gets the copy's (painted, or shared)
        if not e.path.lower().endswith(".ppk"):
            continue
        raw = changed.get(e.path) or earlier.get(e.path.lower()) or bytes(zz.read(e))
        if raw[:8] != PROXY_MAGIC:
            continue
        pack = ProxyPack.read(raw)
        names = pack.names()
        hits = [(n, old, stand) for n, (old, stand) in standins.items() if old in names and n not in names]
        for n, old, stand in hits:
            p = pack.proxies[pack.names().index(old)]  # (each one added moves the ones after it)
            data = make_standin(p.data, *stand) if stand else p.data
            pack.add(ProxyPack([Proxy(standin_key(n), data, p.extra, n.encode("latin-1").ljust(256, b"\0"))], [0]), n)
        if hits:
            changed[e.path] = pack.to_bytes()
    report = {"models": {model: new for model, new, *_ in held}, "model": held[0][1], "copy_of": held[0][0],
              "mesh_packs": sorted({p for *_, meshes, _s in held for p in meshes}),
              "skeleton_packs": sorted({p for *_, skeletons in held for p in skeletons}),
              "textures": sorted(added), "painted": sorted(texture_member(p) for o, p in pictures.items()
                                                           if texture_member(o) in paint),
              "standin_packs": sorted(p for p in changed if p.lower().endswith(".ppk"))}
    return Written(changed, added, held[0][1], report)
