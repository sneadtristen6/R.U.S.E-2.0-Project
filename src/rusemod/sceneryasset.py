"""A mod's own map assets (the Maps tab's asset importer, 2026-10-17): a model of a kind the game has (a rock, a prop,
a bush, a tree) made into scenery the map can place, written into the game's packs beside the game's own model of
that kind, so it loads wherever that one loads.

Each kind follows a model of the game's own (KINDS): its scenery type is copied (rusemod.sceneryasset.rndf) and its
models point at ours; our model goes into every mesh pack that holds the game's one, its material a copy of that
one's with our own picture, named in the same picture group (a picture outside the game's groups crashed the game:
rusemod.unitmodel.texture_group). A tree is two models, as the game's: its leaves (the materials that are see-through,
glTF's MASK or BLEND, with their mask in the picture's alpha) and its wood (the rest).

The model as read (rusemod.modelin.read_model: z up, metres) becomes the game's: 260 units a metre times `size`, its
y turned round (so each triangle's corners too), its points in draws of at most 65,535 (the game's 16-bit indices),
plain float UVs and no bones. No size cap: a model keeps every triangle it has (the owner's rule, 2026-10-08)."""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

from .modelin import Model, ModelError, load_picture, smooth_normals

M = 260.0              # game units a metre
MOST_POINTS = 0xFFFF   # points one draw can name (16-bit indices)
CHUNK = MOST_POINTS // 3   # triangles a draw takes at most: never more points than that, however they're shared
PICTURE_MOST = 2048    # a picture's longer side, at most (the game's own decor atlases are 2048)
FORMAT = "TVertex__Position_3f__NormalIn01_4ubn__TexCoord0_2f__TexPackedAtlas0_4ubn"   # plain, float UVs, no bones
PREFIX = "R2"          # our models' and types' names start so (none of the game's do)


class AssetError(ModelError):
    pass


@dataclass(frozen=True)
class Kind:
    template: str       # the game's scenery type a copy is made of
    models: tuple       # its model(s) ours stand beside, as the packs name them: (the one), or (leaves, wood)
    label: str

    @property
    def like(self) -> str:
        """The game model ours go beside (and are named in the folder of)."""
        return self.models[0]


_PROPS, _PLANTS = "ww2\\res3d\\decors\\props\\props_2\\", "ww2\\res3d\\decors\\vegetation_eu\\"
KINDS = {
    "rock": Kind("TypeWarrior/RocherNormandie_01", (_PROPS + "rocher_1lod0.ase2ndfbin",), "rock or cliff"),
    "prop": Kind("TypeWarrior/TasPlanchesBois", (_PROPS + "tasplanchesboislod0.ase2ndfbin",), "prop"),
    "plant": Kind("TypeWarrior/BuissonSec03_France", (_PLANTS + "buissonsec3lod0.ase2ndfbin",), "bush or plant"),
    "tree": Kind("TypeWarrior/Chene_01", (_PLANTS + "chene_01_feuilleslod0.ase2ndfbin",
                                          _PLANTS + "chene_01_tronclod0.ase2ndfbin"), "tree"),
}


def roles(kind: str) -> tuple:
    """The game models an asset of `kind` is: ("main",), or a tree's ("leaves", "wood")."""
    return ("leaves", "wood") if kind == "tree" else ("main",)


def rings(kind: str) -> tuple:
    """The versions an asset of `kind` has besides its full model (rusemod.meshlod), each drawn in a ring of its own
    as the game's buildings draw theirs: middle and far (a plant too, though the game's bushes stop at the middle: the
    owner's "nothing appears far", 2026-10-17). A plant's and a tree's are 3D models, not the game's picture of them
    (its imposter): in the game (2026-10-17) the picture of our small tree showed its trunk only, made of the full model
    or of its middle version alike."""
    return ("medium", "far")


def model_names(kind: str, name: str, ring: str = "", like: str = "") -> dict:
    """{role: our model's name in the packs} for the asset `name` of `kind` (what its scenery type names); `ring`:
    one of its versions (rings), "" for the full model; `like`: the game model ours go beside (a building piece's:
    the piece's; default its kind's)."""
    return {r: model_name(like or KINDS[kind].like, name, r, ring) for r in roles(kind)}


BUILDING = "building"   # a building's own look (rusemod.buildinglook): the kind of the model that takes a piece's place


def kind_of(asset) -> Kind:
    """The game type and model an asset follows: its kind's (KINDS), or a building piece's own (Asset.piece)."""
    return asset.piece if asset.piece is not None else KINDS[asset.kind]


@dataclass
class Draw:
    material: int        # the model's material number (its picture)
    vertices: bytes      # FORMAT, 28 bytes a point
    points: int
    indices: bytes       # 16-bit
    triangles: int


@dataclass
class Part:
    """One game model: its draws and its box (min x, y, z, max x, y, z, game units)."""
    draws: list = field(default_factory=list)
    box: tuple = ()

    @property
    def counts(self) -> tuple[int, int]:
        return sum(d.points for d in self.draws), sum(d.triangles for d in self.draws)


@dataclass
class Picture:
    width: int
    height: int
    rgba: bytes
    see_through: bool    # its alpha is a mask (leaves): drawn where it's high


def asset_name(text: str) -> str:
    """A model's or type's own name from any text: letters and digits, words joined (rock_face_01 -> RockFace01)."""
    words = [w for w in re.split(r"[^A-Za-z0-9]+", text) if w]
    if not words:
        raise AssetError("an asset needs a name with letters or digits")
    return "".join(w[:1].upper() + w[1:] for w in words)


def _arrays(model: Model):
    """Every mesh's points (game units and axes), normals, UVs (as the game stores them), triangles (turned round) and
    each triangle's material, joined: numpy arrays."""
    from .numpy2 import np
    pos, nrm, uvs, tri, mat = [], [], [], [], []
    base = 0
    for mesh in model.meshes:
        p = np.asarray(mesh.positions, dtype=np.float64).reshape(-1, 3)
        n = np.asarray(mesh.normals or smooth_normals(mesh.positions, mesh.triangles), dtype=np.float64).reshape(-1, 3)
        u = np.asarray(mesh.uvs, dtype=np.float64).reshape(-1, 2) if mesh.uvs else np.zeros((len(p), 2))
        t = np.asarray(mesh.triangles, dtype=np.int64).reshape(-1, 3)
        pos.append(p * np.array([1.0, -1.0, 1.0]))
        nrm.append(n * np.array([1.0, -1.0, 1.0]))
        uvs.append(np.stack([u[:, 0], -u[:, 1]], axis=1))     # (u, v down - 1): the game's
        tri.append(t[:, [0, 2, 1]] + base)                     # the mirror turns each round
        fm = mesh.face_materials or [-1] * len(t)
        mat.append(np.asarray(fm, dtype=np.int64))
        base += len(p)
    return (np.concatenate(pos), np.concatenate(nrm), np.concatenate(uvs), np.concatenate(tri),
            np.concatenate(mat))


def parts(model: Model, size: float = 1.0, leaves: set | None = None, offset: tuple = (0.0, 0.0, 0.0)
          ) -> dict[str, Part]:
    """The model as the game's models: {"main": Part}, or with `leaves` (the material numbers that are see-through)
    {"leaves": Part, "wood": Part} for a tree. `size`: times its own size (1: as modelled, a metre a metre);
    `offset`: game units added after (a building piece's place: fit_to)."""
    from .numpy2 import np
    pos, nrm, uvs, tri, mat = _arrays(model)
    pos = pos * (M * size) + np.asarray(offset, dtype=np.float64)
    groups = {"main": np.ones(len(tri), dtype=bool)} if leaves is None else {
        "leaves": np.isin(mat, sorted(leaves)), "wood": ~np.isin(mat, sorted(leaves))}
    out = {}
    for role, keep in groups.items():
        part = Part()
        picked = np.nonzero(keep)[0]
        if not len(picked):
            continue
        for m in np.unique(mat[picked]):
            mine = picked[mat[picked] == m]
            for at in range(0, len(mine), CHUNK):
                t = tri[mine[at:at + CHUNK]]
                used, local = np.unique(t, return_inverse=True)
                rec = np.zeros(len(used), dtype=[("p", "<f4", 3), ("n", "u1", 4), ("uv", "<f4", 2), ("a", "u1", 4)])
                rec["p"] = pos[used]
                rec["n"][:, :3] = np.clip(np.rint((nrm[used] + 1.0) * 127.5), 0, 255)
                rec["uv"] = uvs[used]
                rec["a"] = (0, 0, 255, 255)
                part.draws.append(Draw(int(m), rec.tobytes(), len(used),
                                       local.reshape(-1).astype("<u2").tobytes(), len(t)))
        lo, hi = pos[np.unique(tri[picked])].min(axis=0), pos[np.unique(tri[picked])].max(axis=0)
        part.box = tuple(float(v) for v in lo) + tuple(float(v) for v in hi)
        out[role] = part
    if not out:
        raise AssetError(f"{model.source}: no triangles to draw")
    return out


def fit_to(model: Model, box: tuple, size: float = 1.0) -> tuple[float, tuple]:
    """(size for parts(), offset) that stand `model` where a game model of box `box` (min x, y, z, max x, y, z, game
    units) stands: its longer side on the ground as long as the box's times `size`, the middle of its footprint on
    the box's, its foot on the box's floor."""
    pos = _arrays(model)[0]
    lo, hi = pos.min(axis=0), pos.max(axis=0)
    ours = max(float(hi[0] - lo[0]), float(hi[1] - lo[1]))
    theirs = max(box[3] - box[0], box[4] - box[1])
    if ours <= 0 or theirs <= 0:
        raise AssetError(f"{model.source}: the model, or the piece it takes the place of, has no size on the ground")
    s = theirs * size / (ours * M)
    k = M * s
    return s, ((box[0] + box[3]) / 2 - k * float(lo[0] + hi[0]) / 2,
               (box[1] + box[4]) / 2 - k * float(lo[1] + hi[1]) / 2, box[2] - k * float(lo[2]))


def pictures(model: Model) -> list[Picture | None]:
    """Each material's picture for the game: its colour picture (PNG or TGA: rusemod.modelin.load_picture) a power of
    two each way, at most PICTURE_MOST, its alpha the material's mask when it has one (see-through), else opaque; a
    material with no picture its plain colour. None where a material has neither."""
    from .modelin import _sized
    out: list[Picture | None] = []
    for m in model.materials:
        if m.data:
            try:
                w, h, px = load_picture(m.data, m.picture)
            except ModelError as exc:
                raise AssetError(f"{m.name}: {exc} (the Studio turns a model's JPG pictures into PNG as it imports "
                                 f"it)") from None
            w, h, px = _sized(w, h, bytes(px), PICTURE_MOST)
        else:
            r, g, b = (round(255 * c) for c in m.colour)
            w, h, px = 4, 4, bytes((r, g, b, 255)) * 16
        see = bool(m.cutout)
        if m.mask:
            mw, mh, mpx = load_picture(m.mask, "mask")
            mw, mh, mpx = _sized(mw, mh, bytes(mpx), max(w, h))
            if (mw, mh) != (w, h):
                from .modelin import whole_arrays
                arrays = whole_arrays()
                mpx = arrays.nearest(bytes(mpx), mw, mh, w, h) if arrays else mpx
            buf = bytearray(px)
            buf[3::4] = bytes(mpx)[0::4][:w * h]      # the mask's grey (its red) is the alpha
            px = bytes(buf)
        elif not see:
            buf = bytearray(px)
            buf[3::4] = b"\xff" * (w * h)
            px = bytes(buf)
        out.append(Picture(w, h, px, see))
    return out


def leaf_materials(model: Model) -> set:
    """The material numbers of a model that are see-through (its leaves)."""
    return {i for i, m in enumerate(model.materials) if m.cutout}


# --- into the packs -----------------------------------------------------------------------------------------------
def model_name(like: str, name: str, role: str = "", ring: str = "") -> str:
    """Our model's name in the packs, in the folder of the game's model it stands beside (like):
    ww2\\...\\props_2\\r2rockface01lod0.ase2ndfbin; a tree's two: ...r2<name>leaveslod0, ...r2<name>woodlod0; a
    version (`ring`) the same with it after the role: ...r2rockface01mediumlod0, ...r2<name>leavesmediumlod0."""
    folder = like.rsplit("\\", 1)[0]
    part = role.capitalize() if role not in ("", "main") else ""
    return f"{folder}\\{PREFIX}{name}{part}{ring.capitalize()}lod0.ase2ndfbin".lower()


def write_models(mesh_raw: bytes, models: dict, like: str, images: dict) -> bytes:
    """The mesh pack with our models in: `models` {our name: Part}, each draw's material a copy of the first material
    of the game's model `like` with its picture changed to `images[the draw's material number]` (the picture's path,
    ZZ:\\GenTexGroup\\...\\<group>_<ours>.png)."""
    from .ndf import Value
    from .ndf import Ndf
    from .unitmodel import _retext
    from .unitpacks import Buffer, MeshPack, _material_list, _texts
    pack = MeshPack.read(mesh_raw)
    for name in models:
        if name in pack.items:
            raise AssetError(f"the pack already has {name}")
    data, mesh, _skeleton = pack.items[like]
    first, _count = pack.meshes[mesh]
    nd = Ndf(pack.materials)
    roots = _material_list(nd)
    body = nd.objects[roots[pack.draws[first][1]]]
    old = next(t for pi, v in body.props if nd.prop_name(pi) == "Textures" for t in _texts(nd, v)
               if t.lower().endswith(".png"))
    number = {}
    for m, image in sorted(images.items()):
        props = [(pi, _retext(nd, v, old, image) if nd.prop_name(pi) == "Textures" else v) for pi, v in body.props]
        roots.append(nd.add_object(body.cls, props))
        number[m] = len(roots) - 1
    root = nd.objects[nd.topo[0]]
    root.props[0] = (root.props[0][0], Value(0x11, struct.pack("<I", len(roots)) + b"".join(
        Value(0x09, struct.pack("<III", 0xBBBBBBBB, n, nd.objects[n].cls)).encode() for n in roots)))
    pack.materials = nd.to_logical()
    pack.material_count = len(roots)
    names = [f.split(b"\0", 1)[0].decode("latin-1") for f in pack.formats]
    kind = next((k for k, f in enumerate(names) if f.endswith(FORMAT)), None)
    if kind is None:
        raise AssetError(f"the pack holding {like} has no {FORMAT.split('__', 1)[1]} format")
    flags = struct.unpack_from("<I", data, 24)[0]
    calls = {}
    for name, part in models.items():
        mine = []
        for d in part.draws:
            pack.vbs.append(Buffer(d.vertices, len(d.vertices), d.points, kind, 0))
            pack.ibs.append(Buffer(d.indices, len(d.indices), 3 * d.triangles, 1, 0))
            mine.append((0, number[d.material], len(pack.ibs) - 1, len(pack.vbs) - 1, 0xFFFF, 0xCDCD))
        pack.items[name] = [struct.pack("<6fI", *part.box, flags), None, 0xCDCD]
        calls[name] = mine
    pack._renumber(calls)
    return pack.to_bytes()


def image_path(like_picture: str, stem: str) -> str:
    """Our picture's path, in the folder and picture group of the game's: ZZ:\\GenTexGroup\\...\\TSCVegetation_R2X01.png
    for ...\\TSCVegetation_diffuseTexture01.png."""
    from .unitmodel import texture_group
    folder, name = like_picture.replace("/", "\\").rsplit("\\", 1)
    return f"{folder}\\{texture_group(name)}_{stem}.png"


@dataclass
class Asset:
    """A mod's asset: files/assets/<name>/asset.toml and the model it names."""
    name: str            # its own name (letters and digits): TypeWarrior/R2_<name>
    kind: str            # KINDS
    model: object        # the model file (Path): .glb, .gltf or .3ds
    size: float = 1.0    # times its own size
    credit: dict = field(default_factory=dict)   # source, author, licence: kept, never used by the build
    versions: dict = field(default_factory=dict)  # ring (rings: medium, far) -> its own model file; a ring without
    # one gets the version rusemod.meshlod makes
    two_sided: bool = False  # every triangle also facing the other way (rusemod.meshlod.both_sides): a scan with no
    # back (a rock face) seen from behind. (Drawing it in the game's leaves' bucket didn't: its backs stayed unseen,
    # 2026-10-17.)
    piece: Kind | None = None   # kind BUILDING: the game's building piece it takes the place of (its type and model);
    # `size` is then times that piece's size (its longer side), and the model stands where the piece's does
    solid: bool = False  # units go around it where it's placed (solid_blocks), as around a placed building; false:
    # as the game's own scenery, units drive through it and knock it over (seen in the game, 2026-10-18)


ASSETS = "files/assets"   # a mod's assets: files/assets/<name>/asset.toml beside its model


def mod_assets(folder) -> dict:
    """{name: Asset} from a mod folder's files/assets/<name>/asset.toml (kind, model, size, source, author, licence;
    medium and far: its own versions, model files in that folder too). AssetError for one that can't be read."""
    import tomllib
    root = Path(folder) / ASSETS
    if not root.is_dir():
        return {}
    out = {}
    for toml in sorted(root.glob("*/asset.toml")):
        where = f"{ASSETS}/{toml.parent.name}/asset.toml"
        try:
            data = tomllib.loads(toml.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise AssetError(f"{where}: {exc}") from None
        name = asset_name(toml.parent.name)
        kind = data.get("kind")
        if kind not in KINDS:
            raise AssetError(f"{where}: kind must be one of {', '.join(KINDS)}, not {kind!r}")
        files = {}
        for key in ("model", "medium", "far"):
            if key != "model" and key not in data:
                continue
            path = toml.parent / str(data.get(key, ""))
            if not data.get(key) or not path.is_file() or toml.parent.resolve() not in path.resolve().parents:
                raise AssetError(f"{where}: {key} must name its model file in that folder")
            files[key] = path
        size = data.get("size", 1.0)
        if isinstance(size, bool) or not isinstance(size, (int, float)) or not 0.01 <= size <= 100:
            raise AssetError(f"{where}: size is a number from 0.01 to 100 (1: as modelled)")
        two_sided, solid = data.get("two_sided", False), data.get("solid", False)
        if not isinstance(two_sided, bool):
            raise AssetError(f"{where}: two_sided is true or false")
        if not isinstance(solid, bool):
            raise AssetError(f"{where}: solid is true or false")
        model = files.pop("model")
        out[name] = Asset(name, kind, model, float(size), {k: data[k] for k in ("source", "author", "licence")
                                                           if k in data}, files, two_sided, solid=solid)
    return out


def save_versions(folder, force: bool = False, asset: Asset | None = None) -> dict:
    """An asset folder's (files/assets/<name>/) versions made (rusemod.meshlod) and saved beside its model as
    <model>_<ring>.glb (its pictures the model's own files: editable in Blender, read back by the build), and named in
    its asset.toml (medium = ..., far = ...). A version the asset.toml already names is the modder's and left as it is,
    unless `force`. Returns {ring: (file name, triangles, made: bool)}. `asset`: the folder's asset, read with its
    .toml (a building look's: rusemod.buildinglook), when it isn't a map asset's."""
    from . import meshlod
    from .modelin import read_model
    folder = Path(folder)
    asset = asset or next(iter(mod_assets_in(folder).values()))
    toml = folder / ("asset.toml" if asset.kind != BUILDING else "building.toml")
    model = read_model(asset.model)
    leaves = leaf_materials(model) if asset.kind == "tree" else None
    text = toml.read_text(encoding="utf-8")
    out = {}
    for ring in rings(asset.kind):
        own = asset.versions.get(ring)
        if own is not None and not force:
            out[ring] = (own.name, read_model(own).counts()[1], False)
            continue
        v = meshlod.version(model, ring, leaves)
        name = f"{Path(asset.model).stem}_{ring}.glb"
        (folder / name).write_bytes(meshlod.glb_bytes(v, folder))
        line = f'{ring} = "{name}"'
        text = re.sub(rf"(?m)^{ring}\s*=.*$", line, text) if re.search(rf"(?m)^{ring}\s*=", text) \
            else text.rstrip("\n") + "\n" + line + "\n"
        out[ring] = (name, v.counts()[1], True)
    toml.write_text(text, encoding="utf-8", newline="")
    return out


def mod_assets_in(folder) -> dict:
    """mod_assets for one asset's own folder (files/assets/<name>/)."""
    folder = Path(folder)
    found = mod_assets(folder.parent.parent.parent)
    name = asset_name(folder.name)
    if name not in found:
        raise AssetError(f"{folder}: not an asset folder (files/assets/<name>/asset.toml)")
    return {name: found[name]}


def write_asset(zz, asset: Asset, earlier: dict | None = None):
    """`asset` into ZZ_Win.dat `zz` beside its kind's game model: every mesh pack holding that model gets ours, its
    pictures are added as textures of their own, and their stand-ins go in every stand-in pack holding the game
    picture's. Returns rusemod.unitmodel.Written (changed packs, added textures, our model's name, a report).
    `earlier`: members other build steps already changed (path -> bytes), changed from there."""
    try:  # the models' sums are on whole arrays only; the Studio and the Launcher carry numpy
        from .numpy2 import np  # noqa: F401
    except ImportError:
        raise AssetError("map assets need numpy 2, which the Studio and the Launcher carry; this Python has none "
                         "(run the build from the Studio or the Launcher)") from None
    from .modelin import read_model
    from .spk import Spk, SpkError
    from .unitmodel import Written, new_standin, new_texture, standin_key, standin_member, texture_member
    from .unitpacks import PROXY_MAGIC, Proxy, ProxyPack
    earlier = {k.lower(): v for k, v in (earlier or {}).items()}
    kind = kind_of(asset)
    model = read_model(asset.model)
    leaves = leaf_materials(model) if asset.kind == "tree" else None
    if asset.kind == "tree" and not leaves:
        raise AssetError(f"{asset.name}: a tree needs leaves (a see-through material); one without is a prop")
    holders, box = [], None   # (member, pack bytes, the game's model in it, its picture); that model's box
    own = "\\" + kind.like.rsplit("\\", 1)[-1]
    for e in zz.entries:
        p = e.path.lower()
        if not (p.startswith("gen_5\\pack\\") and p.endswith(".spk")):
            continue
        raw = earlier.get(p) or bytes(zz.read(e))
        try:
            spk = Spk(raw)
        except SpkError:
            continue
        # the game's model by its own name, or its file in another folder of the pack (a theatre's own copy: the
        # African vegetation pack's bushes): ours go beside it, always under the name our type gives them
        like = kind.like if kind.like in spk.items else next((n for n in sorted(spk.items) if n.endswith(own)), None)
        if like is not None:
            first = spk.meshes[spk.items[like].mesh][0]
            holders.append((e.path, raw, like, next(iter(spk.materials()[spk.draws[first][0]]["textures"].values()))))
            box = box or spk.items[like].box
    if not holders:
        # not a game rule: ours go beside the kind's game model, so they load wherever it does; none, nowhere to go
        raise AssetError(f"{asset.name}: no mesh pack holds the game's {kind.like} (its kind's model)")
    from . import meshlod
    sides = meshlod.both_sides if asset.two_sided else (lambda m: m)   # (the full model and each version)
    # a building piece stands where the game's piece does, sized to it; the others as modelled, times their size
    size, offset = fit_to(model, box, asset.size) if asset.piece is not None else (asset.size, (0.0, 0.0, 0.0))
    made = parts(sides(model), size, leaves, offset)
    if asset.kind == "tree" and "wood" not in made:
        raise AssetError(f"{asset.name}: a tree needs wood (a material that isn't see-through); one all leaves is a "
                         f"plant")
    pics = pictures(model)
    names = model_names(asset.kind, asset.name, like=kind.like)   # (every one its scenery type names)
    models = {names[r]: made[r] for r in names}
    lighter, how = {}, {}
    for ring in rings(asset.kind):   # its versions: the mod's own, or made from the full model (rusemod.meshlod)
        own_file = asset.versions.get(ring)
        v = sides(read_model(own_file) if own_file else meshlod.version(model, ring, leaves))
        if len(v.materials) > len(model.materials):
            raise AssetError(f"{asset.name}: its {ring} version has {len(v.materials)} materials, the model "
                             f"{len(model.materials)} (a version shares the model's pictures, material by material)")
        try:
            v_made = parts(v, size, leaves, offset)
        except AssetError:
            v_made = {}
        ring_names = model_names(asset.kind, asset.name, ring, like=kind.like)
        for r, n in ring_names.items():   # (a part the version lost, its leaves thinned away say: the full one)
            models[n] = v_made.get(r) or made[r]
        lighter[ring] = {r: (v_made.get(r) or made[r]).counts[1] for r in ring_names}
        how[ring] = Path(own_file).name if own_file else "made"
    # our pictures beside the picture of the very model our type copies (whichever pack comes first)
    like_picture = next((pic for _p, _r, like, pic in holders if like == kind.like), holders[0][3])
    images = {m: image_path(like_picture, f"{PREFIX}{asset.name}{m + 1:02d}") for m, pic in enumerate(pics)
              if pic is not None}
    changed = {path: write_models(raw, models, like, images) for path, raw, like, _pic in holders}
    added, standins = {}, {}
    for m, pic in enumerate(pics):
        if pic is None:
            continue
        member = texture_member(image_path(like_picture, f"{PREFIX}{asset.name}{m + 1:02d}"))
        added[member] = new_texture(pic.rgba, pic.width, pic.height)
        standins[standin_member(member)] = new_standin(pic.rgba, pic.width, pic.height)
    like_standin = standin_member(texture_member(like_picture))
    for e in zz.entries:
        if not e.path.lower().endswith(".ppk"):
            continue
        raw = earlier.get(e.path.lower()) or bytes(zz.read(e))
        if raw[:8] != PROXY_MAGIC:
            continue
        pack = ProxyPack.read(raw)
        have = pack.names()
        if like_standin not in have:
            continue
        extra = pack.proxies[have.index(like_standin)].extra
        for name, data in standins.items():
            pack.add(ProxyPack([Proxy(standin_key(name), data, extra, name.encode("latin-1").ljust(256, b"\0"))],
                               [0]), name)
        changed[e.path] = pack.to_bytes()
    report = {"name": asset.name, "kind": asset.kind, "models": names,
              "triangles": {r: made[r].counts[1] for r in made}, "points": {r: made[r].counts[0] for r in made},
              "draws": {r: len(made[r].draws) for r in made}, "pictures": len(added),
              "versions": lighter, "versions_from": how,
              "see_through": sum(1 for p in pics if p is not None and p.see_through),
              "mesh_packs": sorted(p for p in changed if p.lower().endswith(".spk")),
              "standin_packs": sorted(p for p in changed if p.lower().endswith(".ppk"))}
    return Written(changed, added, names.get("main") or names.get("leaves", ""), report)


# --- its scenery type ---------------------------------------------------------------------------------------------
def data_path(model: str) -> str:
    """A pack model name as a scenery type names it: DataDir:\\ww2\\...\\x lod0.ASE2NdfBin."""
    return "DataDir:\\" + model[:-len(".ase2ndfbin")] + ".ASE2NdfBin"


def type_name(name: str) -> str:
    return f"TypeWarrior/{PREFIX}_{name}"


MIDDLE, FAR = 4, 8   # the ModeMask bits of the middle and far rings (the game's buildings: 2 / 4 / 8)


def rndf(kind: str, name: str, models: dict, files: list, switched_off=frozenset(), piece: Kind | None = None) -> str:
    """The rules making our scenery type `TypeWarrior/R2_<name>`, a copy of the kind's game type (once per game file
    that defines it: `files`), its models ours (`models`: {ring: {role: pack name}}, ring "" the full model and each
    of rings(kind); role "main", or a tree's "leaves" and "wood"), each ring its own version, as the game's buildings:
      rock, prop: the full model in the game type's close entry, its middle and far versions in copies of that entry
      for the middle and far rings;
      plant: the full model close, its middle version in the entry the game's bush draws its picture with, its far
      version in a copy of the close entry for the far ring (the game's bush has none);
      tree: its two full models (leaves, wood) close, its middle and far versions (copies of that pair) in the entries
      the game's oak draws its picture with (that picture is shared by the game's oaks: left as it is).
    `switched_off`: the files (their place in `files`) whose game type's close entry a graphics option can switch off
    (stones): ours never are.
      building (`piece`: the game's piece it takes the place of): its three entries (close, middle, far) each given a
      copy of its own model part naming ours (the full model and its middle and far versions); its destroyed state
      stays the piece's, renamed so no two types share a name."""
    k = piece or KINDS[kind]
    t = type_name(name)
    q = "'"

    def model(ring, role):
        return f"path({q}{data_path(models[ring][role])}{q})"
    out = [f"// Written by the build (rusemod.sceneryasset): the mod's asset {name} ({k.label}), a copy of {k.template}"]
    for j, file in enumerate(files):
        local = f"R2Asset_{name}_{j}"
        out += [f"{local} is clone @[RegistrationName={q}{k.template}{q}, file={q}{file}{q}]", "(",
                f"    RegistrationName = {q}{t}{q}", ")"]
        if j in switched_off:
            out.append(f"patch ~/{local}:SDFalse.ModeEntry[0] ( delete GraphicOptionDeactivated )")
        if kind == BUILDING:
            out.append(f"patch ~/{local}:SDTrue ( RegistrationName = {q}{t}_Dest{q} )")
            for e, ring in enumerate(("",) + rings(kind)):
                part = f"{local}_{ring or 'close'}"
                out += [f"{part} is clone ~/{local}:SDFalse.ModeEntry[{e}].SceneryDescriptor "
                        f"( ModelASE = {model(ring, 'main')} )",
                        f"patch ~/{local}:SDFalse.ModeEntry[{e}] ( SceneryDescriptor = ~/{part} )"]
        elif kind in ("rock", "prop"):
            out.append(f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor ( ModelASE = {model('', 'main')} )")
            added = []
            for ring, bit in (("medium", MIDDLE), ("far", FAR)):
                entry = f"{local}_{ring}"
                added.append(f"~/{entry}")
                out += [f"{entry} is clone ~/{local}:SDFalse.ModeEntry[0] ( ModeMask = {bit} )",
                        f"patch ~/{entry}:SceneryDescriptor ( ModelASE = {model(ring, 'main')} )"]
            out.append(f"patch ~/{local} ( SDFalse.ModeEntry += [{', '.join(added)}] )")
        elif kind == "plant":
            mid, far = f"{local}_medium", f"{local}_far"
            out += [f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor ( ModelASE = {model('', 'main')} )",
                    f"{mid} is clone ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor "
                    f"( ModelASE = {model('medium', 'main')} )",
                    f"patch ~/{local}:SDFalse.ModeEntry[1] ( SceneryDescriptor = ~/{mid} )",
                    f"{far} is clone ~/{local}:SDFalse.ModeEntry[0] ( ModeMask = {FAR} )",   # (the game's bush has none)
                    f"patch ~/{far}:SceneryDescriptor ( ModelASE = {model('far', 'main')} )",
                    f"patch ~/{local} ( SDFalse.ModeEntry += [~/{far}] )"]
        else:
            out += [f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor.DescriptorComposition[0] "
                    f"( ModelASE = {model('', 'leaves')} )",
                    f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor.DescriptorComposition[1] "
                    f"( ModelASE = {model('', 'wood')} )"]
            for e, ring in ((1, "medium"), (2, "far")):
                pair = f"{local}_{ring}"
                out += [f"{pair} is clone ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor", "(", ")",
                        f"patch ~/{pair}:DescriptorComposition[0] ( ModelASE = {model(ring, 'leaves')} )",
                        f"patch ~/{pair}:DescriptorComposition[1] ( ModelASE = {model(ring, 'wood')} )",
                        f"patch ~/{local}:SDFalse.ModeEntry[{e}] ( SceneryDescriptor = ~/{pair} )"]
    return "\n".join(out) + "\n"


def all_model_names(kind: str, name: str) -> dict:
    """{ring: {role: pack name}} of every model an asset's type names: "" (the full model) and each of rings(kind)."""
    return {ring: model_names(kind, name, ring) for ring in ("",) + rings(kind)}


def rules(game, assets: list) -> str:
    """The rules for every asset's scenery type (rndf), from the game's data `game` (rusemod.patch's: where each
    kind's type is defined)."""
    from .patch import Inline
    from .visibility import descriptors_named, entries
    found = descriptors_named(game, {kind_of(a).template for a in assets})
    out = []
    for a in assets:
        template = kind_of(a).template
        files = sorted({f for _n, f, _o in found.get(template, [])})
        if not files:
            # not a game rule: our type is a copy of the kind's game type; without it there's nothing to copy
            raise AssetError(f"{a.name}: the game has no {template} for its scenery type to be a copy of")
        off = set()
        for j, file in enumerate(files):
            obj = next(o for _n, f, o in found[template] if f == file)
            got = entries(obj, game.objects) or []
            if not got or not got[0][2]:
                # not a game rule: the close entry is changed in our copy; one shared with other types would change
                # them too (an entry the shipped prop sets share), so it must be the type's own
                raise AssetError(f"{a.name}: {template} in {file} has no close entry of its own to copy")
            if a.kind == BUILDING and (len(got) != 3 or not all(own for _m, _o, own in got)
                                       or not isinstance(obj.props.get("SDTrue"), Inline)):
                # not a game rule: what our copy changes (close, middle and far, and its destroyed state's name), as
                # every building piece of the game has them; one laid out otherwise isn't copied
                raise AssetError(f"{a.name}: {template} in {file} isn't laid out as building pieces are (three detail "
                                 f"entries and a destroyed state of its own)")
            if "GraphicOptionDeactivated" in got[0][1].props:
                off.add(j)
        names = {ring: model_names(a.kind, a.name, ring, like=kind_of(a).like) for ring in ("",) + rings(a.kind)}
        out.append(rndf(a.kind, a.name, names, files, off, a.piece))
    return "\n".join(out)


# --- the Studio's Import model (the Maps tab, 2026-10-18; the owner: "a custom like asset importer for the map section
# of the studio. Similarly to how the unit section has theirs for the model importer"): a model file made a mod's
# asset, and the mod's assets as the Studio's 3D view draws them ---
GROUPS = {"rock": "prop", "prop": "prop", "plant": "vegetation", "tree": "vegetation"}   # the Maps tab's place trays
LICENCES = ("CC0", "CC-BY")   # what a model taken from others may be under (CC-BY: its author credited)


def asset_toml(kind: str, model: str, size: float = 1.0, two_sided: bool = False, credit: dict | None = None,
               versions: dict | None = None, solid: bool = False) -> str:
    """An asset.toml (mod_assets reads it back)."""
    import json
    lines = [f'kind = "{kind}"', f"model = {json.dumps(model)}"]
    if size != 1.0:
        lines.append(f"size = {size:g}")
    if two_sided:
        lines.append("two_sided = true")
    if solid:
        lines.append("solid = true")
    for k in ("source", "author", "licence"):
        if (credit or {}).get(k):
            lines.append(f"{k} = {json.dumps(str(credit[k]))}")
    for ring, file in (versions or {}).items():
        lines.append(f"{ring} = {json.dumps(file)}")
    return "\n".join(lines) + "\n"


def name_of_file(src) -> str:
    """An asset's name from its model file's: the picture size sites add left off (boulder_01_2k.gltf -> Boulder01)."""
    stem = Path(src).stem
    return asset_name(re.sub(r"[_\- ]\d+k$", "", stem, flags=re.I) or stem)


def _picture_data(name: str, folder: Path) -> bytes:
    """A picture a model names (a .3ds keeps only its file name), from beside the model: by its own name (any kind,
    a JPG too), else as rusemod.modelin.find_picture finds a PNG or TGA. b"" when none is there."""
    from .modelin import find_picture
    want = Path(name.replace("\\", "/")).name
    if not want:
        return b""
    for p in [folder / want] + sorted(folder.glob("*")):
        if p.is_file() and p.name.lower() == want.lower():
            return p.read_bytes()
    found = find_picture(name, folder)
    return found.read_bytes() if found is not None else b""


def import_asset(src, mod_folder, kind: str, name: str = "", size: float = 1.0, two_sided: bool = False,
                 credit: dict | None = None, convert=None, solid: bool = False) -> Asset:
    """The model file `src` (.glb; .gltf with its files beside it; .3ds with its pictures beside it) made the mod's
    asset `name` (its file's name when none) of `kind`: saved as files/assets/<name>/<name>.glb, one file with every
    picture in it (editable in Blender; a JPG picture turned into PNG by `convert`, bytes -> PNG bytes, as the game
    reads PNG and TGA), its asset.toml written (`size`, `two_sided`, `credit`: source, author, licence; `solid`) and
    its medium and far versions made (save_versions). Importing a name again replaces its model and versions.
    AssetError for a kind not in KINDS, a licence other than LICENCES, or a model that can't be read or drawn."""
    src, mod_folder = Path(src), Path(mod_folder)
    if kind not in KINDS:
        raise AssetError(f"the kind is one of {', '.join(KINDS)}, not {kind!r}")
    name = asset_name(name) if name else name_of_file(src)
    credit = checked_credit(src, credit)
    if not 0.01 <= float(size) <= 100:
        raise AssetError("size is a number from 0.01 to 100 (1: as modelled)")
    folder = mod_folder / ASSETS / name
    save_model(src, folder / f"{name}.glb", kind == "tree", convert)
    (folder / "asset.toml").write_text(asset_toml(kind, f"{name}.glb", float(size), bool(two_sided), credit,
                                                  solid=bool(solid)), encoding="utf-8", newline="")
    save_versions(folder)
    return mod_assets(mod_folder)[name]


def extent(asset: Asset) -> tuple[float, float, float, float]:
    """(across x, across y, height, reach) of the asset's model in metres as modelled (size 1): its box, and how far it
    reaches from its middle (where it's placed) across the ground. Read from its smallest version (the far one, else
    the model: a tree's full model can be ~100 MB)."""
    import math
    from .modelin import read_model
    model = read_model(Path(asset.versions.get("far") or asset.model))
    x0, y0, z0, x1, y1, z1 = model.box()
    reach = max((math.hypot(p[0], p[1]) for m in model.meshes for p in m.positions), default=0.0)
    return x1 - x0, y1 - y0, z1 - z0, reach


def solid_blocks(assets: dict, objects) -> tuple[list, list[str]]:
    """Blocks (rusemod.nav.Block) for the placed objects of the mods' solid assets (`assets`: {name: (Asset, mod
    id)}), each as far as its model reaches from its middle times its own size and its placed size: units go around
    them, as around a placed building (rusemod.nav.solid_blocks: the shipped maps keep units off by their movement,
    never by their objects). An object placed with `solid` false stays walk-through. Returns (blocks, notes)."""
    from .nav import Block
    by_type = {type_name(n): a for n, (a, _mod) in assets.items() if a.solid}
    out, reach = [], {}
    for o in objects:
        a = by_type.get(getattr(o, "type", None))
        if a is None or not getattr(o, "solid", True):
            continue
        if o.type not in reach:
            reach[o.type] = extent(a)[3] * M * a.size
        if reach[o.type] > 0:
            out.append(Block(o.x, o.y, reach[o.type] * o.size, "all"))
    return out, [f"{len(out)} placed model(s) of the mods' own made solid"] if out else []


def checked_credit(src, credit: dict | None) -> dict:
    """A model's source, author and licence, as kept (empty ones left out). AssetError for a licence other than
    LICENCES."""
    credit = {k: str(v).strip() for k, v in (credit or {}).items() if str(v or "").strip()}
    if credit.get("licence") and credit["licence"].upper() not in LICENCES:
        # not a game rule: the project takes others' models under CC0 or CC-BY only (credited)
        raise AssetError(f"{Path(src).name}: a model taken from others must be CC0 or CC-BY (this one says "
                         f"{credit['licence']}); leave the licence empty for a model of your own")
    return credit


def save_model(src, out, tree: bool = False, convert=None) -> None:
    """The model file `src` saved as one .glb `out` with every picture inside it (a JPG turned into PNG by `convert`),
    after checking the game can be given it (triangles to draw, pictures that can be read; `tree`: its leaves apart)."""
    from . import meshlod
    from .modelin import read_model
    src, out = Path(src), Path(out)
    try:
        model = read_model(src)
    except (ModelError, OSError) as exc:
        raise AssetError(f"{src.name}: {exc}") from None
    for m in model.materials:   # every picture inside the one file, as PNG where it was a JPG
        if not m.data and m.picture:
            m.data = _picture_data(m.picture, src.parent)
        for key in ("data", "mask"):
            data = getattr(m, key)
            if data[:3] == b"\xff\xd8\xff":
                if convert is None:
                    raise AssetError(f"{src.name}: {m.picture or m.name} is a JPG: the Studio turns it into PNG as "
                                     f"it imports the model")
                setattr(m, key, convert(data))
        if m.picture:
            m.picture = Path(m.picture.replace("\\", "/")).stem + ".png"
    parts(model, 1.0, leaf_materials(model) if tree else None)   # (refused here, not at the build: nothing to draw)
    pictures(model)                                             # (and pictures that can't be read)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(meshlod.glb_bytes(model, out.parent / "(every picture inside)"))


def studio_models(assets: dict, out_dir) -> dict:
    """The mod's assets ({name: Asset}) as the Studio's 3D view draws models (the index rusemod.models.map_models
    makes: {"bin": file, "models": {type name: [part]}, "textures": {key: PNG file}}, a part {"texture", "vertices",
    "triangles", "positions", "normals", "uvs", "indices"} with byte offsets into the .bin: positions 3 f32, normals 4
    i8, uvs 2 f32 a point; indices u32), each its full model as the game gets it (parts(): its size, the game's axes).
    Written into `out_dir`, named by the assets' files and settings, so the same assets are made once."""
    import hashlib
    import json
    from array import array

    from .dxt import png_bytes
    from .modelin import read_model
    from .numpy2 import np
    out_dir = Path(out_dir)
    h = hashlib.sha1()
    for n in sorted(assets):
        a = assets[n]
        st = Path(a.model).stat()
        h.update(f"{n}|{a.kind}|{a.size}|{Path(a.model).name}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    key = h.hexdigest()[:16]
    index_file = out_dir / f"{key}.json"
    if index_file.is_file():
        return json.loads(index_file.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    blob, models, textures = bytearray(), {}, {}
    for n in sorted(assets):
        a = assets[n]
        model = read_model(a.model)
        pics = pictures(model)
        found = []
        for role, part in parts(model, a.size, leaf_materials(model) if a.kind == "tree" else None).items():
            for d in part.draws:
                rec = np.frombuffer(d.vertices, dtype=[("p", "<f4", 3), ("n", "u1", 4), ("uv", "<f4", 2),
                                                       ("a", "u1", 4)])
                nrm = np.zeros((d.points, 4), dtype=np.int8)
                nrm[:, :3] = np.clip(np.rint((rec["n"][:, :3].astype(np.float32) - 127.5) / 127.5 * 127), -127, 127)
                tex = f"{n}/{d.material}" if d.material < len(pics) and pics[d.material] is not None else None
                rec_out = {"texture": tex, "vertices": d.points, "triangles": d.triangles}
                for field_, data in (("positions", np.ascontiguousarray(rec["p"], dtype="<f4").tobytes()),
                                     ("normals", nrm.tobytes()),
                                     ("uvs", np.ascontiguousarray(rec["uv"], dtype="<f4").tobytes()),
                                     ("indices", array("I", struct.unpack(f"<{3 * d.triangles}H", d.indices)).tobytes())):
                    rec_out[field_] = len(blob)
                    blob += data
                    blob += bytes(-len(blob) % 4)
                found.append(rec_out)
                if tex is not None and tex not in textures:
                    p = pics[d.material]
                    png = f"{key}-{n}-{d.material}.png"
                    (out_dir / png).write_bytes(png_bytes(p.rgba, p.width, p.height, channels=4))
                    textures[tex] = png
        models[type_name(n)] = found
    (out_dir / f"{key}.bin").write_bytes(bytes(blob))
    index = {"bin": f"{key}.bin", "models": models, "textures": textures}
    index_file.write_text(json.dumps(index), encoding="utf-8")
    return index
