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


def model_names(kind: str, name: str) -> dict:
    """{role: our model's name in the packs} for the asset `name` of `kind` (what its scenery type names)."""
    return {r: model_name(KINDS[kind].like, name, r) for r in roles(kind)}


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


def parts(model: Model, size: float = 1.0, leaves: set | None = None) -> dict[str, Part]:
    """The model as the game's models: {"main": Part}, or with `leaves` (the material numbers that are see-through)
    {"leaves": Part, "wood": Part} for a tree. `size`: times its own size (1: as modelled, a metre a metre)."""
    from .numpy2 import np
    pos, nrm, uvs, tri, mat = _arrays(model)
    pos = pos * (M * size)
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
def model_name(like: str, name: str, role: str = "") -> str:
    """Our model's name in the packs, in the folder of the game's model it stands beside (like):
    ww2\\...\\props_2\\r2rockface01lod0.ase2ndfbin; a tree's two: ...r2<name>leaveslod0, ...r2<name>woodlod0."""
    folder = like.rsplit("\\", 1)[0]
    return f"{folder}\\{PREFIX}{name}{role.capitalize() if role not in ('', 'main') else ''}lod0.ase2ndfbin".lower()


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


ASSETS = "files/assets"   # a mod's assets: files/assets/<name>/asset.toml beside its model


def mod_assets(folder) -> dict:
    """{name: Asset} from a mod folder's files/assets/<name>/asset.toml (kind, model, size, source, author, licence).
    AssetError for one that can't be read."""
    import tomllib
    from pathlib import Path
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
        model = toml.parent / str(data.get("model", ""))
        if not data.get("model") or not model.is_file() or toml.parent.resolve() not in model.resolve().parents:
            raise AssetError(f"{where}: model must name its model file in that folder")
        size = data.get("size", 1.0)
        if isinstance(size, bool) or not isinstance(size, (int, float)) or not 0.01 <= size <= 100:
            raise AssetError(f"{where}: size is a number from 0.01 to 100 (1: as modelled)")
        out[name] = Asset(name, kind, model, float(size), {k: data[k] for k in ("source", "author", "licence")
                                                           if k in data})
    return out


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
    kind = KINDS[asset.kind]
    model = read_model(asset.model)
    leaves = leaf_materials(model) if asset.kind == "tree" else None
    if asset.kind == "tree" and not leaves:
        raise AssetError(f"{asset.name}: a tree needs leaves (a see-through material); one without is a prop")
    made = parts(model, asset.size, leaves)
    if asset.kind == "tree" and "wood" not in made:
        raise AssetError(f"{asset.name}: a tree needs wood (a material that isn't see-through); one all leaves is a "
                         f"plant")
    pics = pictures(model)
    names = model_names(asset.kind, asset.name)   # (every one its scenery type names)
    holders = []   # (member, pack bytes, the game's model in it, its picture)
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
    if not holders:
        # not a game rule: ours go beside the kind's game model, so they load wherever it does; none, nowhere to go
        raise AssetError(f"{asset.name}: no mesh pack holds the game's {kind.like} (its kind's model)")
    # our pictures beside the picture of the very model our type copies (whichever pack comes first)
    like_picture = next((pic for _p, _r, like, pic in holders if like == kind.like), holders[0][3])
    images = {m: image_path(like_picture, f"{PREFIX}{asset.name}{m + 1:02d}") for m, pic in enumerate(pics)
              if pic is not None}
    changed = {path: write_models(raw, {names[r]: made[r] for r in names}, like, images)
               for path, raw, like, _pic in holders}
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


def rndf(kind: str, name: str, models: dict, files: list) -> str:
    """The rules making our scenery type `TypeWarrior/R2_<name>`, a copy of the kind's game type (once per game file
    that defines it: `files`), its models ours ({role: pack name}: "main", or "leaves" and "wood"):
      rock, prop: its one 3D model ours, drawn close, middle and far (the game's draw it close only);
      plant: its 3D model (close) and the model its middle-distance picture is made of, ours;
      tree: its two models (leaves, wood) ours close, and its middle and far picture a copy of the game's of its own
      (the game's is shared by its oaks), made of our two."""
    k = KINDS[kind]
    t = type_name(name)
    q = "'"
    out = [f"// Written by the build (rusemod.sceneryasset): the mod's asset {name} ({k.label}), a copy of {k.template}"]
    for j, file in enumerate(files):
        local = f"R2Asset_{name}_{j}"
        out += [f"{local} is clone @[RegistrationName={q}{k.template}{q}, file={q}{file}{q}]", "(",
                f"    RegistrationName = {q}{t}{q}", ")"]
        if kind in ("rock", "prop"):
            out += [f"patch ~/{local}:SDFalse.ModeEntry[0] ( ModeMask = 31 )",
                    f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor "
                    f"( ModelASE = path({q}{data_path(models['main'])}{q}) )"]
        elif kind == "plant":
            out += [f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor "
                    f"( ModelASE = path({q}{data_path(models['main'])}{q}) )",
                    f"patch ~/{local}:SDFalse.ModeEntry[1].SceneryDescriptor.SceneryDescriptor[0] "
                    f"( ModelASE = path({q}{data_path(models['main'])}{q}) )"]
        else:
            far = f"R2Asset_{name}_{j}_far"
            out += [f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor.DescriptorComposition[0] "
                    f"( ModelASE = path({q}{data_path(models['leaves'])}{q}) )",
                    f"patch ~/{local}:SDFalse.ModeEntry[0].SceneryDescriptor.DescriptorComposition[1] "
                    f"( ModelASE = path({q}{data_path(models['wood'])}{q}) )",
                    f"{far} is clone ~/{local}:SDFalse.ModeEntry[1].SceneryDescriptor", "(", ")",
                    f"patch ~/{far}:SceneryDescriptor[0] ( ModelASE = path({q}{data_path(models['leaves'])}{q}) )",
                    f"patch ~/{far}:SceneryDescriptor[1] ( ModelASE = path({q}{data_path(models['wood'])}{q}) )",
                    f"patch ~/{local}:SDFalse.ModeEntry[1] ( SceneryDescriptor = ~/{far} )",
                    f"patch ~/{local}:SDFalse.ModeEntry[2] ( SceneryDescriptor = ~/{far} )"]
    return "\n".join(out) + "\n"


def rules(game, assets: list) -> str:
    """The rules for every asset's scenery type (rndf), from the game's data `game` (rusemod.patch's: where each
    kind's type is defined)."""
    from .visibility import descriptors_named
    found = descriptors_named(game, {KINDS[a.kind].template for a in assets})
    out = []
    for a in assets:
        template = KINDS[a.kind].template
        files = sorted({f for _n, f, _o in found.get(template, [])})
        if not files:
            # not a game rule: our type is a copy of the kind's game type; without it there's nothing to copy
            raise AssetError(f"{a.name}: the game has no {template} for its scenery type to be a copy of")
        out.append(rndf(a.kind, a.name, model_names(a.kind, a.name), files))
    return "\n".join(out)
