"""A new building's look of its own (the Units tab's building page; the owner, 2026-10-18: "The asset importer and
building importers"): a model file in the place of one piece of the look the building copies.

A building's look is a symbol of the base-building scenery file every map loads (DataMap_Win.dat SYMBOL_FILES; Japan's
buildings have a file of their own): a named layout of scenery pieces (the main hall, hangars, trucks, walls, ground
stickers) and the markers that make a building work (where its construction and damage effects play, what a click
selects). The building's data names its symbol twice, in its GfxDescriptor (SYMBOL_NAMES); a name the file doesn't
have stops the game with an error, so the build refuses one.

The mod's look of a new building is files/buildings/<the building's name>/building.toml beside its model:

    piece = "Prototype_building"   # the piece of the copied look the model takes the place of (its type's name)
    model = "Foundry.glb"
    size  = 1.0                    # times that piece's size (its longer side on the ground); 0.01 to 100
    # optional, as a map asset's (rusemod.sceneryasset): medium, far (its own versions), two_sided, source, author,
    # licence

The build makes the model a scenery type of its own (rusemod.sceneryasset, kind "building": a copy of the piece's
type, its close, middle and far models ours, standing where the piece's model stands and sized to it; its destroyed
state stays the piece's), copies the building's symbol under the building's own name with every placing of that piece
given our type, and points the building's two symbol names at the copy. The original building and its look stay as
they are: every building of the game has a look part of its own, which a copy copies."""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

from .sceneryasset import BUILDING, Asset, AssetError, Kind, asset_name, type_name

LOOKS = "files/buildings"   # a mod's building looks: files/buildings/<the building's name>/building.toml
SYMBOL_FILES = ("test\\typewarrior\\basebuilding\\save.boobspc",     # in DataMap_Win.dat: every nation's but Japan's
                "test\\typewarrior\\japbuildingsset\\save.boobspc")  # Japan's (loaded only when Japan plays)
SYMBOL_NAMES = (("LevelBuildGeoDatabaseModification",),             # where a building's GfxDescriptor names its look
                ("LevelBuildStateGeoDatabaseModification", "ModificationAction"))


class BuildingLookError(AssetError):
    pass


@dataclass
class Look:
    """A new building's look: its model (an asset of kind BUILDING, its piece filled in by the build) and the piece
    of the copied look it takes the place of."""
    unit: str        # the building's name (Descriptor_Building_...)
    piece: str       # the piece's scenery type: TypeWarrior/<name>
    asset: Asset


def look_name(unit: str) -> str:
    """The asset name of a building's look model (its scenery type TypeWarrior/R2_Look<...>, its models'
    r2look<...>lod0): from the building's name."""
    return "Look" + asset_name(unit.removeprefix("Descriptor_"))


def symbol_name(unit: str) -> str:
    """The name of a building's own symbol: R2_<its name without Descriptor_>."""
    return "R2_" + unit.removeprefix("Descriptor_")


def piece_type(piece: str) -> str:
    return piece if piece.startswith("TypeWarrior/") else f"TypeWarrior/{piece}"


def look_toml(piece: str, model: str, size: float = 1.0, two_sided: bool = False, credit: dict | None = None,
              versions: dict | None = None) -> str:
    """A building.toml (mod_looks reads it back)."""
    import json
    lines = [f"piece = {json.dumps(piece_type(piece).split('/', 1)[1])}", f"model = {json.dumps(model)}"]
    if size != 1.0:
        lines.append(f"size = {size:g}")
    if two_sided:
        lines.append("two_sided = true")
    for k in ("source", "author", "licence"):
        if (credit or {}).get(k):
            lines.append(f"{k} = {json.dumps(str(credit[k]))}")
    for ring, file in (versions or {}).items():
        lines.append(f"{ring} = {json.dumps(file)}")
    return "\n".join(lines) + "\n"


def mod_looks(folder) -> dict:
    """{building name: Look} from a mod folder's files/buildings/<name>/building.toml. AssetError for one that
    can't be read."""
    import tomllib
    root = Path(folder) / LOOKS
    if not root.is_dir():
        return {}
    out = {}
    for toml in sorted(root.glob("*/building.toml")):
        where = f"{LOOKS}/{toml.parent.name}/building.toml"
        try:
            data = tomllib.loads(toml.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise BuildingLookError(f"{where}: {exc}") from None
        piece = data.get("piece")
        if not isinstance(piece, str) or not piece.strip():
            raise BuildingLookError(f"{where}: piece must name the piece of the look the model takes the place of")
        files = {}
        for key in ("model", "medium", "far"):
            if key != "model" and key not in data:
                continue
            path = toml.parent / str(data.get(key, ""))
            if not data.get(key) or not path.is_file() or toml.parent.resolve() not in path.resolve().parents:
                raise BuildingLookError(f"{where}: {key} must name its model file in that folder")
            files[key] = path
        size = data.get("size", 1.0)
        if isinstance(size, bool) or not isinstance(size, (int, float)) or not 0.01 <= size <= 100:
            raise BuildingLookError(f"{where}: size is a number from 0.01 to 100 (1: as big as the piece)")
        two_sided = data.get("two_sided", False)
        if not isinstance(two_sided, bool):
            raise BuildingLookError(f"{where}: two_sided is true or false")
        unit = toml.parent.name
        model = files.pop("model")
        asset = Asset(look_name(unit), BUILDING, model, float(size),
                      {k: data[k] for k in ("source", "author", "licence") if k in data}, files, two_sided)
        out[unit] = Look(unit, piece_type(piece.strip()), asset)
    return out


def import_look(src, mod_folder, unit: str, piece: str, size: float = 1.0, two_sided: bool = False,
                credit: dict | None = None, convert=None) -> Look:
    """The model file `src` made the look of the new building `unit` in place of `piece`: saved as
    files/buildings/<unit>/<unit>.glb (one file, every picture inside), its building.toml written and its middle and
    far versions made (rusemod.sceneryasset.save_versions). Importing again replaces its model and versions."""
    from .sceneryasset import checked_credit, save_model, save_versions
    src, mod_folder = Path(src), Path(mod_folder)
    if not unit or "/" in unit or "\\" in unit:
        raise BuildingLookError(f"{unit!r} isn't a building's name")
    credit = checked_credit(src, credit)
    if not 0.01 <= float(size) <= 100:
        raise BuildingLookError("size is a number from 0.01 to 100 (1: as big as the piece)")
    folder = mod_folder / LOOKS / unit
    for old in folder.glob("*.glb") if folder.is_dir() else []:   # the model it had, and its versions
        old.unlink()
    save_model(src, folder / f"{unit}.glb", False, convert)
    (folder / "building.toml").write_text(look_toml(piece, f"{unit}.glb", float(size), bool(two_sided), credit),
                                          encoding="utf-8", newline="")
    look = mod_looks(mod_folder)[unit]
    save_versions(folder, asset=look.asset)
    return mod_looks(mod_folder)[unit]


def piece_kind(game, piece: str) -> Kind:
    """The game's piece `piece` (TypeWarrior/...) as the kind our look's type copies: its type and its close model
    (the pack name: ww2\\...\\x lod0.ase2ndfbin), from the game's data `game` (rusemod.patch's)."""
    from .patch import Inline, Text
    from .visibility import descriptors_named, entries
    found = descriptors_named(game, {piece}).get(piece)
    if not found:
        # not a game rule: the piece named in building.toml isn't one of the game's scenery types
        raise BuildingLookError(f"the game has no scenery type {piece} (the piece the look's model takes the place of)")
    got = entries(found[0][2], game.objects) or []
    desc = got[0][1].props.get("SceneryDescriptor") if got and got[0][1] is not None else None
    model = desc.obj.props.get("ModelASE") if isinstance(desc, Inline) else None
    if not isinstance(model, Text) or not model.value.lower().endswith(".ase2ndfbin"):
        raise BuildingLookError(f"{piece} has no 3D model of its own close up, so no model can take its place")
    like = model.value.replace("/", "\\")
    like = like.split(":", 1)[1].lstrip("\\") if ":" in like else like
    return Kind(piece, (like.lower(),), "building piece")


# --- the base-building scenery file: its symbols --------------------------------------------------------------------
def _layout(raw: bytes):
    """(the scenery file read, its header fields, the symbols' block offsets, the symbols' names (an empty one last))
    of a base-building file, checked to be laid out as clone_symbol rewrites it."""
    from .scenery import Scenery
    sc = Scenery(raw)
    f = list(sc.fields)
    tab_off, tab_n, data_off, data_len = f[0], f[1], f[2], f[3]
    order = [(data_off, data_len), (f[6], f[7]), (f[4], f[5]), (f[8], f[9]), (f[10], f[11]), (f[12], f[13]),
             (f[20], f[21])]
    if tab_off != 124 or data_off != tab_off + 4 * tab_n or f[22:26] != [0, 0, 0, 0] or \
            any(a + b != c for (a, b), (c, _d) in zip(order, order[1:])) or f[20] + f[21] != len(raw):
        # not a game rule: the order the shipped base-building files keep their tables in, which this writer keeps
        raise BuildingLookError("the base-building scenery file's tables aren't in the order the build knows")
    table = list(struct.unpack_from(f"<{f[9] // 4}I", raw, f[8]))
    names2, p = [], f[10]
    while p < f[10] + f[11]:
        (n,) = struct.unpack_from("<I", raw, p)
        names2.append(raw[p + 4:p + 4 + n].decode("latin-1"))
        p += 4 + n
    if not names2 or names2[-1] != "" or len(table) != len(names2) - 1:
        raise BuildingLookError("the base-building scenery file's symbol tables don't pair up")
    return sc, f, table, names2


def symbols(raw: bytes) -> dict[str, int]:
    """{symbol name: its block's offset} of a base-building scenery file."""
    _sc, _f, table, names2 = _layout(raw)
    return dict(zip(names2[:-1], table))


def symbol_pieces(raw: bytes, symbol: str) -> dict[str, int]:
    """{scenery type: how many} of what a symbol puts down (its pieces, stickers and markers, however deep)."""
    from collections import Counter
    sc, _f, table, names2 = _layout(raw)
    if symbol not in names2[:-1]:
        raise BuildingLookError(f"the base-building file has no symbol {symbol}")
    root = sc.block_at(table[names2.index(symbol)])
    return dict(Counter(sc.names[s] for s, _m in sc.walk(root.index)))


def _blocks_under(sc, offset: int) -> list[int]:
    """The offsets of a block and every block under it, in the file's order (references point forward in it)."""
    seen, todo = set(), [offset]
    while todo:
        off = todo.pop()
        if off in seen:
            continue
        seen.add(off)
        todo += [it.child_offset for it in sc.block_at(off).items if it.kind == "child"]
    return sorted(seen)


def clone_symbol(raw: bytes, source: str, new: str, swap: dict[str, str]) -> bytes:
    """The base-building file with symbol `new` added: a copy of `source` (its block and every block under it, after
    the file's own, references kept pointing forward), each object whose type is a key of `swap` given the type it
    names instead (new type names added to the file's name table). The file's own blocks, names and symbols stay
    where they are."""
    from .scenery import VERSION
    sc, f, table, names2 = _layout(raw)
    if source not in names2[:-1]:
        raise BuildingLookError(f"the base-building file has no symbol {source} to copy")
    if new in names2[:-1]:
        raise BuildingLookError(f"the base-building file already has a symbol {new}")
    names = list(sc.names[:-1])   # (without the empty name that ends the table)
    added = [t for t in dict.fromkeys(swap.values()) if t not in names]
    index = {n: i for i, n in enumerate(names + added)}
    # a type is named with TypeWarrior/ or without (the markers), the file's way: either way finds it
    by_index = {i: index[t] for old, t in swap.items() for i, n in enumerate(names)
                if n.split("/", 1)[-1] == old.split("/", 1)[-1]}
    data_off, data_len = f[2], f[3]
    root = table[names2.index(source)]
    copied = _blocks_under(sc, root)
    pad = -data_len % 16
    base = data_len + pad
    where, at = {}, base
    for off in copied:
        where[off] = at
        at += len(sc.block_at(off).raw)
    if at >= 0x1000000:
        # not a game rule: a reference keeps a block's offset in 24 bits
        raise BuildingLookError("the base-building file would grow past what its references can reach")
    new_blocks, swapped = [], 0
    for off in copied:
        b = sc.block_at(off)
        out = bytearray(b.raw)
        for it in b.items:
            p = b.items_start + it.at
            if it.kind == "child":
                struct.pack_into("<I", out, p, (it.word & ~0x00FFFFFC) | where[it.child_offset])
            elif it.kind == "object" and it.symbol in by_index:
                struct.pack_into("<I", out, p, (it.word & ~(0xFFFFF << 4)) | (by_index[it.symbol] << 4))
                swapped += 1
        new_blocks.append(bytes(out))
    if swap and not swapped:
        raise BuildingLookError(f"the look {source} has no {', '.join(sorted(swap))} to take the place of")
    body_data = raw[data_off:data_off + data_len] + b"\0" * pad + b"".join(new_blocks)
    old_table = list(struct.unpack_from(f"<{f[1]}I", raw, f[0]))
    block_table = old_table[:-1] + [where[off] for off in copied] + [len(body_data)]

    def named(values) -> bytes:
        return b"".join(struct.pack("<I", len(n.encode("latin-1"))) + n.encode("latin-1") for n in values)
    names_bytes = named(names + added + [""])
    flags = raw[f[4]:f[4] + f[5]] + bytes([1] * len(added))
    opt = struct.pack(f"<{len(table) + 1}I", *table, where[root])
    names2_bytes = named(names2[:-1] + [new, ""])
    layers = raw[f[12]:f[12] + f[13]]
    grid = raw[f[20]:f[20] + f[21]]
    g = list(f)
    g[1] = len(block_table)
    g[2] = f[0] + 4 * g[1]
    g[3] = len(body_data)
    g[6], g[7] = g[2] + g[3], len(names_bytes)
    g[4], g[5] = g[6] + g[7], len(flags)
    g[8], g[9] = g[4] + g[5], len(opt)
    g[10], g[11] = g[8] + g[9], len(names2_bytes)
    g[12], g[13] = g[10] + g[11], len(layers)
    g[20], g[21] = g[12] + g[13], len(grid)
    body = (VERSION + struct.pack("<26I", *g) + struct.pack(f"<{len(block_table)}I", *block_table) + body_data
            + names_bytes + flags + opt + names2_bytes + layers + grid)
    return hashlib.md5(body).digest() + body


def check_clone(old: bytes, new_raw: bytes, source: str, new: str, swap: dict[str, str]) -> str:
    """Read the written file back: every old block where it was and unchanged, every old symbol as it was, the new
    symbol putting down what `source` does with `swap`'s types in, references only forward. A line saying so;
    BuildingLookError when something reads back otherwise."""
    from collections import Counter
    from .scenery import Scenery
    a, b = Scenery(old), Scenery(new_raw)
    if a.names[:-1] != b.names[:len(a.names) - 1]:
        raise BuildingLookError("the file's old type names moved")
    for x in a.blocks:   # (the last old block may end in the zeros that pad the new ones to 16 bytes)
        y = b.blocks[x.index]
        if x.offset != y.offset or not y.raw.startswith(x.raw) or y.raw[len(x.raw):].strip(b"\0"):
            raise BuildingLookError(f"block {x.index} changed")
    was, now = symbols(old), symbols(new_raw)
    if any(now.get(n) != off for n, off in was.items()) or new not in now:
        raise BuildingLookError("the symbol tables don't read back")
    for blk in b.blocks[len(a.blocks):]:
        for it in blk.items:
            if it.kind == "child" and it.child_offset <= blk.offset:
                raise BuildingLookError(f"block {blk.index} refers backward")
    def swapped_to(t):
        return next((n for o, n in swap.items() if t.split("/", 1)[-1] == o.split("/", 1)[-1]), None)
    want = Counter()
    for t, n in symbol_pieces(old, source).items():
        want[swapped_to(t) or t] += n
    got = Counter(symbol_pieces(new_raw, new))
    if got != want:
        raise BuildingLookError(f"{new} doesn't put down what {source} does with the piece swapped")
    swapped = sum(n for t, n in symbol_pieces(old, source).items() if swapped_to(t))
    return (f"{new}: a copy of {source} ({sum(got.values())} objects, {swapped} of them now "
            f"{', '.join(sorted(set(swap.values())))}), every old block and symbol unchanged")


def piece_table(read_data, zz, descs: dict) -> dict:
    """{symbol: [[scenery type, how many, width, depth, height]]} of every building look's 3D pieces with a model in a
    nation's base-building pack (what a look's model can take the place of), biggest on the ground first; sizes in
    metres as the look places its biggest one. `read_data(member)`: a DataMap_Win.dat member's bytes or None; `zz`:
    ZZ_Win.dat (open); `descs`: rusemod.scenery.descriptors. Seconds: the Studio keeps it per game build."""
    from .scenery import Scenery
    from .sceneryasset import M
    from .spk import Spk, SpkError
    boxes = {}
    for e in zz.entries:
        p = e.path.lower()
        if p.startswith("gen_5\\pack\\basebuilding\\") and p.endswith(".spk"):
            try:
                for n, it in Spk(bytes(zz.read(e))).items.items():
                    boxes.setdefault(n, it.box)
            except SpkError:
                continue
    out = {}
    for member in SYMBOL_FILES:
        raw = read_data(member)
        if raw is None:
            continue
        sc, _f, table, names2 = _layout(raw)
        for symbol, off in zip(names2[:-1], table):
            found = {}
            for s, m in sc.walk(sc.block_at(off).index):
                name = sc.names[s]
                d = descs.get(name) or descs.get("TypeWarrior/" + name)
                box = boxes.get((d.model or "").lower()) if d is not None else None
                if box is None:
                    continue
                size = (m[0] ** 2 + m[4] ** 2) ** 0.5
                dims = [round((box[3] - box[0]) * size / M, 1), round((box[4] - box[1]) * size / M, 1),
                        round((box[5] - box[2]) * size / M, 1)]
                n, best = found.get(name, (0, dims))
                found[name] = (n + 1, max(best, dims, key=lambda v: v[0] * v[1]))
            out[symbol] = sorted(([t, n, *dims] for t, (n, dims) in found.items()), key=lambda r: -r[2] * r[3])
    return out


def symbol_file_of(read, symbol: str) -> tuple[str, bytes] | None:
    """(member, bytes) of the base-building file holding `symbol`: `read(member)` gives a DataMap_Win.dat member's
    bytes as the build has it so far, or None."""
    for member in SYMBOL_FILES:
        raw = read(member)
        if raw is not None and symbol in symbols(raw):
            return member, raw
    return None


__all__ = ["LOOKS", "SYMBOL_FILES", "SYMBOL_NAMES", "BuildingLookError", "Look", "check_clone", "clone_symbol",
           "import_look", "look_name", "look_toml", "mod_looks", "piece_kind", "piece_table", "piece_type",
           "symbol_file_of", "symbol_name", "symbol_pieces", "symbols", "type_name"]
