"""Build mods into game files: from mod folders to rebuilt packs (docs/MOD_FORMAT.md §2, §3, §6, §8, §10).

  mod folders (mod.toml + src/**/*.rndf + text/*.csv + maps/<map>/terrain.toml, scenery.toml, scenario.toml, cover.toml,
  movement.toml)  ->  load order  ->  the pack's data
  files into the engine's model  ->  run the mods  ->  texts: game keys handed out, loc('...') values filled in  ->
  write changed files back  ->  rebuilt unit-data pack + fingerprint, the rebuilt ZZ_Win.dat when mods add texts or
  new units, and a rebuilt map pack for every map whose ground a mod reshapes (rusemod.terrain_edit)

Value changes, new objects (clones, new units) and deletes all go through rusemod.model; texts through rusemod.loc.
A new unit (a copy of a unit the game knows) also needs a class in the game's Python unit list, which
rusemod.pyscript adds from its one fixed template (PLAN.md decision 23). Mods never bring scripts of their own.
"""
from __future__ import annotations

import os
import re
import struct
import tomllib
import zlib
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from . import loc, pyscript, unitcheck, unitpacks
from .brush import BrushError, parse_strokes
from .edat import Edat
from .lock import fingerprint, fingerprint_text
from .model import ModelError, game_path, load, save
from .patch import Engine, Finding, Text, _walk_obj
from .visibility import SUFFIX as SEEN_SUFFIX
from .resolve import ModInfo, ResolveError, load_order
from .rndf import parse
from .spk import Spk, SpkError
from .steam import build_of, data_revisions
from .terrain_edit import edit_map

DEFAULT_PACK = "ZZ_GladPatchableWin.dat"  # the unit data

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# The game ships "_debuginfo" copies of a few data files that repeat every name of the main file. The game runs with
# them untouched (C2) or rewritten (C4); builds leave them exactly as shipped (PLAN.md §7, C4).
SHADOW = re.compile(r"_debuginfo\.cpp\.[a-z]*ndfbin$")
# PLAN.md decision 23: a mod never brings code that the game or the PC would run. The build only reads mod.toml,
# src/**/*.rndf and text/*.csv anyway; refusing these files outright keeps them from travelling with a mod at all.
NOT_IN_MODS = {".py", ".pyc", ".pyo", ".pyw", ".pyd", ".xyz", ".ipk", ".exe", ".dll", ".com", ".scr", ".msi", ".bat",
               ".cmd", ".ps1", ".vbs", ".js", ".jar"}


class BuildError(Exception):
    pass


def load_mod(path) -> tuple[ModInfo, list]:
    """A mod folder (mod.toml + src/**/*.rndf, files in path order, + text/*.csv), or a single .rndf file as a quick
    mod. Text rows end up in `ModInfo.texts`."""
    path = Path(path)
    if path.is_file() and path.suffix.lower() == ".rmod":  # a community mod as it comes (rusemod.rmod)
        from . import rmod
        mod = rmod.check(path)
        info = ModInfo(rmod.mod_id(mod, path), rmod.version_of(mod))
        info.rmod = path
        return info, []
    if path.is_file() and path.suffix.lower() == ".rndf":
        mod_id = re.sub(r"[^a-z0-9-]+", "-", path.stem.lower()).strip("-") or "mod"
        info = ModInfo(mod_id)
        ops = parse(path.read_text(encoding="utf-8"), file=path.name, mod=mod_id)
    else:
        manifest_file = path / "mod.toml"
        if not manifest_file.is_file():
            raise BuildError(f"{path} has no mod.toml (and isn't a .rndf file)")
        bad = sorted(f.relative_to(path).as_posix() for f in path.rglob("*")
                     if f.is_file() and f.suffix.lower() in NOT_IN_MODS)
        if bad:
            more = ", …" if len(bad) > 5 else ""
            raise BuildError(f"{path}: mods can't contain scripts or programs ({', '.join(bad[:5])}{more}). The "
                             f"build writes the only script changes a mod needs itself (PLAN.md decision 23).")
        try:
            manifest = tomllib.loads(manifest_file.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise BuildError(f"{manifest_file}: {exc}") from None
        m = manifest.get("mod", {})
        mod_id = m.get("id", "")
        if not _ID.match(mod_id):
            raise BuildError(f"{manifest_file}: [mod] id must be lowercase letters, digits and '-' (got {mod_id!r})")
        load_rules = manifest.get("load", {})
        info = ModInfo(mod_id, str(m.get("version", "0.0.0")), dict(manifest.get("dependencies", {})),
                       dict(manifest.get("optional", {})), list(load_rules.get("after", [])),
                       list(load_rules.get("before", [])), dict(manifest.get("conflicts", {})),
                       text_prefix=str(m.get("text_prefix", "")))
        if "rmod" in manifest:  # a .rmod mod in the library: mod.toml + the file (rusemod.rmod.make_folder)
            from . import rmod
            name = str(manifest["rmod"].get("file", ""))
            file = path / name
            if not name or Path(name).name != name or not file.is_file():
                raise BuildError(f"{manifest_file}: [rmod] file must name a .rmod file next to mod.toml (got {name!r})")
            rmod.check(file)
            info.rmod = file
            return info, []
        src = path / "src"
        files = sorted(src.rglob("*.rndf"), key=lambda p: p.relative_to(src).as_posix().lower()) if src.is_dir() else []
        ops = []
        for f in files:
            ops += parse(f.read_text(encoding="utf-8"), file=f.relative_to(path).as_posix(), mod=mod_id)
        text_dir = path / "text"
        for f in sorted(text_dir.glob("*.csv"), key=lambda p: p.name.lower()) if text_dir.is_dir() else []:
            try:  # the dictionary is the file's name, or its last part: studio.baseunite.csv is the Studio's names
                info.texts += loc.read_csv(f.read_text(encoding="utf-8"), f.stem.rsplit(".", 1)[-1].lower(), mod_id,
                                           f.relative_to(path).as_posix())
            except loc.TextError as exc:
                raise BuildError(str(exc)) from None
        info.terrain = read_terrain(path)
        info.scenery = read_scenery(path)
        _erase_areas(info)
        info.scenario = read_scenario(path)
        info.cover = read_cover(path)
        _cover_brushes(info)
        info.movement = read_movement(path)
        _block_brushes(info)
        _paint_brushes(info)
        info.roads = _read_maps(path, "roads.toml")
        info.players = _read_maps(path, "map.toml")
        _new_maps(info)
        from .unitlook import mod_cards, mod_textures
        from .unitmodel import mod_models
        info.textures = mod_textures(path)
        info.cards = mod_cards(path)
        info.models = mod_models(path)
    info.when_mods = {mid for op in ops for mid, _rng, _neg in op.when}
    return info, ops


_MAP_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def _map_readers() -> dict:
    """Each map file a mod may hold (maps/<map pack>/<file>): the tables it holds, how it says so, how its rows are
    read, and what its reader raises."""
    from .cover import CoverError, parse_paints
    from .nav import NavError, parse_blocks
    from .newmap import NewMapError
    from .players import PlayersError
    from .roadnet import RoadNetError, parse_roads
    from .scenario import ScenarioError, parse_moves, parse_spawns, parse_starts
    from .scenery import SceneryEditError, parse_erase, parse_objects
    return {
        "terrain.toml": (("stroke",), "a terrain file holds [[stroke]] tables",
                         lambda d, rel: parse_strokes(d.get("stroke", []), rel), BrushError),
        "scenery.toml": (("object", "erase"), "a scenery file holds [[object]] and [[erase]] tables",
                         lambda d, rel: parse_objects(d.get("object", []), rel) + parse_erase(d.get("erase", []), rel),
                         SceneryEditError),
        # moves first: they name the shipped items by their number, which starts and spawns (added at the end)
        # don't shift
        "scenario.toml": (("move", "start", "spawn"), "a scenario file holds [[move]], [[start]] and [[spawn]] tables",
                          lambda d, rel: (parse_moves(d.get("move", []), rel) + parse_starts(d.get("start", []), rel)
                                          + parse_spawns(d.get("spawn", []), rel)),
                          ScenarioError),
        "cover.toml": (("paint",), "a cover file holds [[paint]] tables",
                       lambda d, rel: parse_paints(d.get("paint", []), rel), CoverError),
        "movement.toml": (("block", "open"), "a movement file holds [[block]] and [[open]] tables",
                          lambda d, rel: (parse_blocks(d.get("block", []), rel)
                                          + parse_blocks(d.get("open", []), rel, "open")), NavError),
        "roads.toml": (("road",), "a roads file holds [[road]] tables",
                       lambda d, rel: parse_roads(d.get("road", []), rel), RoadNetError),
        "map.toml": (("players", "entry", "copy_of", "name"),
                     "a map file holds players = N (and entry = the map-list name), and for a new map copy_of and name",
                     _map_toml, (PlayersError, NewMapError)),
    }


def _map_toml(data: dict, rel: str) -> list:
    """A map.toml's rows: a new map (newmap.NewMap) when it says copy_of, and its players (players.Players). On a new
    map, `entry` picks the shipped map's entry to copy, and players = N applies to the copy."""
    from .newmap import parse
    from .players import parse_map
    parts = rel.replace("\\", "/").split("/")
    made = parse(data, rel, parts[-2] if len(parts) > 1 else "")
    rest = {k: v for k, v in data.items() if not (made and k == "entry")}
    return made + parse_map(rest, rel)


MAP_FILES = ("terrain.toml", "scenery.toml", "scenario.toml", "cover.toml", "movement.toml", "roads.toml", "map.toml")


def read_map_file(folder: Path, f: Path) -> list:
    """One map file of the mod in `folder` (maps/<map pack>/<one of MAP_FILES>), read as the build reads it: its
    rows, or BuildError naming the file and its mistake. The Studio's mod check reads each file this way."""
    rel = f.relative_to(folder).as_posix()
    keys, holds, parse_rows, mistake = _map_readers()[f.name]
    if not _MAP_NAME.match(f.parent.name):
        raise BuildError(f"{rel}: {f.parent.name!r} isn't a map's pack name (letters, digits and _, like "
                         f"TwoIslands)")
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise BuildError(f"{rel}: {exc}") from None
    extra = sorted(set(data) - set(keys))
    if extra:
        raise BuildError(f"{rel}: unknown key {extra[0]!r} ({holds})")
    try:
        return parse_rows(data, rel)
    except mistake as exc:
        raise BuildError(str(exc)) from None


def _read_maps(folder: Path, file: str) -> dict:
    """{map pack name: rows} of every maps/<map pack>/<file> in the mod that holds any."""
    out = {}
    maps = folder / "maps"
    for f in sorted(maps.glob(f"*/{file}"), key=lambda p: p.parent.name.lower()) if maps.is_dir() else []:
        rows = read_map_file(folder, f)
        if rows:
            out[f.parent.name] = rows
    return out


def read_scenery(folder: Path) -> dict:
    """A mod's added scenery: {map pack name: [scenery.NewObject]} from maps/<map pack>/scenery.toml (MOD_FORMAT §8),
    with its erase areas (scenery.EraseArea) among them: _erase_areas moves those to `info.erase`."""
    return _read_maps(folder, "scenery.toml")


def _erase_areas(info) -> None:
    """The erase areas of a mod's scenery.toml files go to `info.erase`; its objects stay in `info.scenery`."""
    from .scenery import EraseArea
    for pack, rows in list(info.scenery.items()):
        areas = [r for r in rows if isinstance(r, EraseArea)]
        if not areas:
            continue
        info.erase[pack] = areas
        rest = [r for r in rows if not isinstance(r, EraseArea)]
        if rest:
            info.scenery[pack] = rest
        else:
            del info.scenery[pack]


def _new_maps(info) -> None:
    """The new maps of a mod's map.toml files (copy_of) go to `info.new_maps`; their player counts stay in
    `info.players`."""
    from .newmap import NewMap
    for pack, rows in list(info.players.items()):
        made = [r for r in rows if isinstance(r, NewMap)]
        if not made:
            continue
        info.new_maps[pack] = made
        rest = [r for r in rows if not isinstance(r, NewMap)]
        if rest:
            info.players[pack] = rest
        else:
            del info.players[pack]


def _cover_brushes(info) -> None:
    """The Studio's cover and uncover brushes live in terrain.toml with the others, but paint the map's cover grid,
    not the ground: they move to `info.cover` (after the mod's own cover.toml circles), and a map whose strokes are
    all cover ones leaves the ground files alone."""
    from .cover import Paint
    for pack, strokes in list(info.terrain.items()):
        cover = [s for s in strokes if s.kind.kind == "cover"]
        if not cover:
            continue
        info.cover.setdefault(pack, []).extend(Paint(s.x, s.y, s.radius, "cover", s.kind.sign < 0, s.square, s.shape,
                                                     s.dx, s.dy, s.x2, s.y2) for s in cover)
        rest = [s for s in strokes if s.kind.kind != "cover"]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


def read_movement(folder: Path) -> dict:
    """A mod's ground units can't use: {map pack name: [nav.Block]} from maps/<map pack>/movement.toml (MOD_FORMAT
    §8)."""
    return _read_maps(folder, "movement.toml")


BLOCK_CELL = 1280.0  # map units: a square block or open stroke is laid down as circles round cells about this size


def _block_brushes(info) -> None:
    """The Studio's block and open brushes (terrain.toml) take ground away from units or give it to them: they move
    to `info.movement` in their order (after the mod's own movement.toml blocks and opens), like the cover brushes to
    the cover grid."""
    from .nav import Block
    moving = ("block", "open")
    for pack, strokes in list(info.terrain.items()):
        blocks = [s for s in strokes if s.kind.kind in moving]
        if not blocks:
            continue
        # the movement graphs are made of circles: a square or a line goes in as circles covering it
        info.movement.setdefault(pack, []).extend(Block(x, y, r, s.kind.shape, s.kind.kind == "open")
                                                  for s in blocks for x, y, r in s.footprint().circles(BLOCK_CELL))
        rest = [s for s in strokes if s.kind.kind not in moving]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


def _paint_brushes(info) -> None:
    """The Studio's Map Paint brushes (paint, stamp) live in terrain.toml with the others, but change the ground's
    picture, not its shape: they move to `info.paint` in their order, like the cover brushes to the cover grid."""
    from .brush import PAINT_KINDS
    for pack, strokes in list(info.terrain.items()):
        paint = [s for s in strokes if s.kind.kind in PAINT_KINDS]
        if not paint:
            continue
        info.paint.setdefault(pack, []).extend(paint)
        rest = [s for s in strokes if s.kind.kind not in PAINT_KINDS]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


BED_RADII = (3840.0, 2560.0, 1920.0, 1280.0)  # down to nav.MIN_RADIUS: a new movement circle fits in one of these


def cleared_woods(erasing: dict) -> tuple[dict, dict]:
    """For each map's erase areas that take trees or buildings ({map: (areas, ids)}): (opens of that ground to every
    unit, the forest cover taken away where trees went), each {map: (list, ids)}. With its trees gone the ground is no
    wood any more, but the map's movement still keeps vehicles off it and its cover still hides infantry there (a
    D-Day test, 2026-10-01: tanks couldn't drive into a cleared wood). Buildings the same: a town's movement closes
    whole blocks (houses, yards, walls: 1,108 of the 1,156 building pieces of Blitz's town by its first starting
    point), so the area opens whole; each house's own ground alone opens next to nothing (islands no unit reaches,
    checked in memory on T25's spots). Seen in the game 2026-10-04 (TESTS.md T25): tanks and infantry drive through
    where Blitz's town stood, and infantry there no longer act as in a town. Erasing only props leaves both, and so
    does a new road's own clearing (keep_ground)."""
    from .cover import Paint
    from .nav import Block
    opens, uncover = {}, {}
    for name, (areas, ids) in erasing.items():
        cleared = [a for a in areas if ("vegetation" in a.what or "building" in a.what) and not a.keep_ground]
        woods = [a for a in cleared if "vegetation" in a.what]
        if cleared:
            # a square or a line opens as circles covering it (the movement graphs are circles), and uncovers itself
            opens[name] = ([Block(x, y, r, "all", True) for a in cleared
                            for x, y, r in a.footprint().circles(BLOCK_CELL)], list(ids))
        if woods:
            uncover[name] = ([Paint(a.x, a.y, a.radius, "cover", True, False, a.shape, a.dx, a.dy, a.x2, a.y2)
                              for a in woods], list(ids))
    return opens, uncover


GROUND_GAP = 64.0  # map units (a quarter metre): a model starting higher than this above its base point is lowered


def grounded(objects: list, descs: dict, lowest_of) -> tuple[list, int]:
    """(the placed objects, each standing on the ground; how many were lowered). The game puts an object's base point
    on the ground and scales its model from there, so a model that starts above its base point floats by that much
    times its size: an upper storey meant to sit on its ground floor (TownHouseC_Haut starts 4.7 m up) placed alone,
    or any such piece made bigger (the owner's 10x houses floated about 47 m up, 2026-10-01). Such an object is sunk
    (its `lift`) so its lowest point sits on the ground. `lowest_of(type)` gives the model's lowest point in map
    units (None when unknown). Bridges keep their own sink, and road pieces aren't objects."""
    from dataclasses import replace
    from .scenery import NewObject
    out, moved = [], 0
    for o in objects:
        d = descs.get(o.type) if isinstance(o, NewObject) else None
        low = lowest_of(o.type) if d is not None and not d.bridge else None
        if low is not None and low > GROUND_GAP:
            out.append(replace(o, lift=o.lift - low * o.size))
            moved += 1
        else:
            out.append(o)
    return out, moved


class _LowestPoints:
    """lowest_of(type) for grounded(): the lowest point of the type's first model the game has (map units), kept per
    type; the game's model packs are opened when first asked, and closed by close()."""

    def __init__(self, game: Path, descs: dict):
        self.game, self.descs, self.found, self.lib = Path(game), descs, {}, None

    def __call__(self, type_name: str):
        if type_name not in self.found:
            self.found[type_name] = None
            d = self.descs.get(type_name)
            if d is not None:
                if self.lib is None:
                    from .models import Library
                    self.lib = Library(self.game)
                for model in (d.models or ([d.model] if d.model else [])):
                    name = self.lib.find(model)
                    zs = [z for part, _tex in self.lib.parts(name) for z in part.positions[2::3]] if name else []
                    if zs:
                        self.found[type_name] = min(zs)
                        break
        return self.found[type_name]

    def close(self) -> None:
        if self.lib is not None:
            self.lib.close()
            self.lib = None


def _bed_circles(drained: list[tuple[float, float]], wet=None) -> list[tuple[float, float, float]]:
    """Open zones (x, y, r) over a dried bed's samples (nav.water_blocks), for Graph.open_ground, which puts each new
    circle inside one zone and none smaller than nav.MIN_RADIUS: so each zone is one of BED_RADII, centred on a sample
    no zone holds yet, the largest whose middle and rim (8 points) aren't under water now (`wet(x, y)`; the ends of a
    bed meet the water left). A bed too narrow for the smallest stays closed."""
    zones: list[tuple[float, float, float]] = []

    def dry(x, y, r) -> bool:
        return wet is None or not any(wet(x + r * c, y + r * s) for c, s in
                                      ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (.7, .7), (.7, -.7), (-.7, .7), (-.7, -.7)))
    for x, y in sorted(drained):
        if any((x - zx) ** 2 + (y - zy) ** 2 < (zr * 0.7) ** 2 for zx, zy, zr in zones):
            continue
        r = next((r for r in BED_RADII if dry(x, y, r)), None)
        if r is not None:
            zones.append((x, y, r))
    return zones


def _wet_opens(open_pack, game: Path, name: str, blocks, map_packs, find_map=None) -> list:
    """nav.wet_opens for a map's opens, on its ground as the terrain edits left it (map_packs: (pack path, archive,
    changed members); `open_pack(path)` opens a map pack, `find_map(name)` finds it, a new map's too); none when the
    map has no opens or its ground can't be read."""
    from .bridges import Water
    from .nav import wet_opens
    from .terrain import pack_file
    from .tms import Tms
    if not any(b.open for b in blocks):
        return []
    map_path = find_map(name) if find_map is not None else find_pack(game, pack_file(name))
    if map_path is None:
        return []
    entry = next((e for e in map_packs if e[0] == map_path), None)
    try:
        map_arc = entry[1] if entry else open_pack(map_path)
        e = map_arc.find("output\\highdef.tms")
        ground = (entry[2].get(e.path) if entry else None) or bytes(map_arc.read(e))
        return wet_opens(blocks, Water(Tms(ground)).at)
    except (KeyError, ValueError, struct.error, zlib.error):
        return []


def read_cover(folder: Path) -> dict:
    """A mod's painted cover and blocked ground: {map pack name: [cover.Paint]} from maps/<map pack>/cover.toml
    (MOD_FORMAT §8)."""
    return _read_maps(folder, "cover.toml")


def read_scenario(folder: Path) -> dict:
    """A mod's scenario edits: moved design items (starting points, spawns, names) and new spawns (units and
    buildings when the scenario starts): {map pack name: [scenario.Move, then scenario.Spawn]} from
    maps/<map pack>/scenario.toml (MOD_FORMAT §8)."""
    return _read_maps(folder, "scenario.toml")


def read_terrain(folder: Path) -> dict:
    """A mod's terrain edits: {map pack name: [brush.Stroke]} from maps/<map pack>/terrain.toml (MOD_FORMAT §8).
    The folder's name is the map's pack name (TwoIslands for DataMapTwoIslands_v09.dat)."""
    return _read_maps(folder, "terrain.toml")


def _meant(game: Path, name: str) -> str:
    """For an error about a mod's maps/<name>: the fix, when the name is a map's title or its pack in another case
    (maps/Blitz for SuperCrossRoads4), else ""."""
    try:
        from .terrain import map_list, pack_for
        guess = pack_for(name, map_list(game))
    except (OSError, ValueError, KeyError):
        return ""
    if not guess or guess == name:
        return ""
    return f" (the mod's folder maps/{name} should be maps/{guess}: it takes the map's pack name, not its title)"



@dataclass
class BuildResult:
    order: list = field(default_factory=list)       # mod ids in load order
    findings: list = field(default_factory=list)    # Finding: errors, warnings, notes
    changed: dict = field(default_factory=dict)     # member path in the pack -> new bytes
    text_changed: dict = field(default_factory=dict)  # member path in the text pack (ZZ_Win.dat) -> new bytes
    script_changed: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (the script pack) -> new bytes
    model_changed: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (a skirmish unit pack) -> new bytes
    texture_changed: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (a texture, a stand-in pack) -> bytes
    close_up_maps: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (a map's close-up map copy) -> bytes
    new_classes: list = field(default_factory=list)  # class names added to the game's Python unit list
    terrain_changed: dict = field(default_factory=dict)  # map pack file name -> {member path: new bytes}
    new_maps: dict = field(default_factory=dict)    # new map's pack name -> newmap.Clone (what it adds)
    added: dict = field(default_factory=dict)       # pack file name -> {member path: bytes}: members new maps add
    own_cards: dict = field(default_factory=dict)   # new units' cards: card member to add -> (its source's, the PNG)
    own_models: dict = field(default_factory=dict)  # new units' models: unit -> (its source's model, the .glb, mod id)
    model_imports: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (packs the new models go in) -> bytes
    model_textures: dict = field(default_factory=dict)  # new members of ZZ_Win.dat (the new models' textures) -> bytes
    visibility: dict = field(default_factory=dict)  # a placed type drawn up close only -> its copy (rusemod.visibility)
    fingerprint: bytes | None = None

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]


@dataclass
class PackModel:
    base: object          # the engine's model (patch.Game) of the pack's data files
    loaded: dict          # game path -> model.NdfFile, for writing back
    members: dict         # game path -> member path in the pack
    shadows: list         # debug-info copies, left as shipped


def load_pack(arc: Edat) -> PackModel:
    """The data files of `arc` as the engine's model, the way builds see them (debug-info copies left out)."""
    members, files, shadows = {}, {}, []
    changed = getattr(arc, "changed", {})  # a pack that .rmod mods changed first (rusemod.rmod.Layered)
    for e in arc.entries:
        start = arc.data_offset + e.offset
        head = changed[e.path][:12] if e.path in changed else arc.raw[start:start + 12]
        if head[:4] == b"EUG0" and head[8:12] == b"CNDF":
            if SHADOW.search(game_path(e.path)):
                shadows.append(e.path)
                continue
            files[game_path(e.path)] = bytes(arc.read(e))
            members[game_path(e.path)] = e.path
    base, loaded = load(files)
    return PackModel(base, loaded, members, shadows)


def needs_zz_win(mods: list) -> bool:
    """Whether building `mods` [(ModInfo, ops)] needs ZZ_Win.dat: some mod adds texts or a new map (its name in the
    menus), repaints a texture (files/replace, rusemod.unitlook), or new objects (a new unit needs a class in the Python unit list, which lives there), or moves a unit to
    another nation or model (the skirmish mesh packs there say whether its models are loaded for it: unit_models)."""
    return any(m.texts or m.new_maps or getattr(m, "textures", None) for m, _ in mods) or \
        any(op.kind in ("create", "clone") or _moves(op) for _, ops in mods for op in ops)


def new_maps(order: list[str], mods: list) -> dict:
    """Every new map the mods make: {its pack name: (newmap.NewMap, the mod's id)}, in load order. Two mods making
    maps of one name is a BuildError."""
    by_id = {m.id: m for m, _ in mods}
    out: dict = {}
    for mod_id in order:
        for name, specs in getattr(by_id.get(mod_id), "new_maps", {}).items():
            same = next((n for n in out if n.lower() == name.lower()), None)
            if same is not None:
                raise BuildError(f"{out[same][1]} and {mod_id} both make a new map called {name} (maps/{name}/map.toml "
                                 f"copy_of): give one another folder name, or leave one mod out")
            out[name] = (specs[-1], mod_id)
    return out


def _spawns(mods: list) -> bool:
    """Whether a mod spawns units on a map (their models must load: spawn_models)."""
    from .scenario import Spawn
    return any(isinstance(x, Spawn) for m, _ in mods for moves in getattr(m, "scenario", {}).values() for x in moves)


def _moves_path(path: str) -> bool:
    """Whether a property path changes a unit's nation or its models."""
    root = (path or "").split(".", 1)[0].split("[", 1)[0]
    return root == unitcheck.NATION or root.startswith("Gfx")


def _moves(op) -> bool:
    return _moves_path(op.path) or any(_moves(b) for b in op.body)


def skirmish_models(zz_win: Edat) -> dict | None:
    """The models each nation's skirmish matches load (unitcheck.pack_models), from the skirmish mesh packs in
    ZZ_Win.dat; None when it has none."""
    names = {}
    for e in zz_win.entries:
        p = e.path.lower()
        if p.startswith(unitcheck.PACK_DIR) and p.endswith(".spk") and p.rsplit("\\", 1)[-1].startswith("meshskirmish"):
            try:
                names[p.rsplit("\\", 1)[-1][:-4]] = set(Spk(bytes(zz_win.read(e))).items)
            except SpkError:
                continue
    return unitcheck.pack_models(names) if names else None


FORCE_LOAD = True  # another nation's models for a unit: that nation's packs load in every skirmish (the force bit in
# the cluster maps, unitcheck.load_everywhere, and its skeleton and card picture packs in every nation's loaders,
# unitcheck.load_with_every_nation). Tested in the game 2026-10-02 (batch 9e). Off, the old way: the models are copied
# into the packs the unit's own nation loads (rusemod.unitpacks); that broke the US's own construction truck (batches
# 4 to 7), and the force bit alone crashed (T13: no skeletons). The force bit is for skirmishes only: campaign
# chapters and Operations get the nation's packs in their own lists (unitcheck.load_in_missions).


def _also_loaded(run, nations, result) -> None:
    for n, (skel, cards) in sorted(unitcheck.load_with_every_nation(run.game, nations).items()):
        if skel or cards:
            result.findings.append(Finding("note", f"{unitcheck.NATIONS[n]}'s unit skeletons and card pictures load in "
                                                   f"every nation's matches too ({skel} skeleton pack(s) and {cards} "
                                                   f"card picture pack(s) added to the other nations' loaders)"))
    for n, (count, maps) in sorted(unitcheck.load_in_missions(run.game, nations).items()):
        if count:
            result.findings.append(Finding("note", f"{unitcheck.NATIONS[n]}'s unit models load in campaign chapters and "
                                                   f"Operations too, which load only the nations they play ({count} "
                                                   f"loaders in {maps} cluster maps)"))


def _pack_names(paths) -> str:
    return ", ".join(p.rsplit("\\", 1)[-1] for p in paths)


def _given_note(given) -> str:
    if not given:
        return "copied there already for another unit of this build"
    return f"{given.summary()} copied in from {' and '.join(unitcheck.NATIONS[unitpacks.TAGS.index(t)] if t in unitpacks.TAGS else t for t in given.sources)}'s packs"


def unit_models(base, run, zz_win, result: BuildResult, into=None) -> None:
    """New units, and units moved to another nation or given other models, whose models are only in another nation's
    skirmish mesh pack: the game loads a nation's unit models only in matches where a player has that nation
    (unitcheck). So that nation's packs (meshes, proxies, animations, skeletons, card pictures) load in every skirmish
    (FORCE_LOAD), with a note; a unit whose nation's packs no loader has is refused, saying why. What the game's own
    units already have is fine. (FORCE_LOAD off, the old way: the models are copied into the skirmish packs of the
    unit's own nation, rusemod.unitpacks; `into`, a unitpacks.Packs, gathers them for the build, else they go straight
    into result.model_changed.)"""
    moved = {owner for owner, path in run.trail if owner in run.game.objects and _moves_path(path)}
    names = sorted(n for n in set(run.created) | moved if n in run.game.objects and unitcheck.is_unit(run.game.objects[n]))
    names = [n for n in names if unitcheck.model_files(run.game.objects[n], run.game)]
    if not names or zz_win is None:
        return
    packs = skirmish_models(zz_win)
    if packs is None:
        result.findings.append(Finding("note", "ZZ_Win.dat has no skirmish mesh packs, so whether the new or moved "
                                               "units' models load for their nation wasn't checked"))
        return
    allowed = unitcheck.allowed_models(base)
    wanted = []  # (unit, its op, its missing models, the nations whose packs it needs)
    chosen: set = set()
    for name in names:
        obj = run.game.objects[name]
        missing = unitcheck.missing_models(obj, run.game, packs, allowed)
        if not missing:
            continue
        op = run.created.get(name) or next((done[-1][0] for (owner, path), done in sorted(run.trail.items())
                                            if owner == name and done and _moves_path(path)), None)
        source = base.objects.get(op.source) if op is not None and op.kind == "clone" else None
        home = unitcheck.nation_of(source) if source is not None else None
        need = []
        for where in missing.values():  # one nation per model: one already loaded, else the source's, else the first
            have = [unitcheck.NATIONS.index(w) for w in where]
            pick = next((i for i in have if i in chosen or i in need), home if home in have else have[0])
            if pick not in need:
                need.append(pick)
        chosen.update(need)
        wanted.append((name, op, missing, need))
    if not wanted:
        return
    if not FORCE_LOAD:
        own = into is None
        into = into or unitpacks.Packs(zz_win)
        for name, op, missing, need in wanted:
            obj = run.game.objects[name]
            n = unitcheck.nation_of(obj)
            nation, tag = unitcheck.NATIONS[n], unitpacks.TAGS[n]
            model, where = next(iter(missing.items()))
            more = f" (and {len(missing) - 1} more)" if len(missing) > 1 else ""
            at = f"{op.at()}: " if op else ""
            try:
                given, why = into.give(sorted(unitcheck.model_files(obj, run.game)), tag,
                                       [unitpacks.TAGS[i] for i in need])
            except (unitpacks.PackError, ValueError, KeyError, IndexError, struct.error) as exc:
                given, why = None, [f"the packs can't be read ({exc})"]
            if why:
                more_why = f" (and {len(why) - 1} more)" if len(why) > 1 else ""
                # rule: nation-models
                result.findings.append(Finding("error", f"{at}{name} is in {nation}'s army (Nationalite {n}), but its "
                                                        f"model {model}{more} is in the mesh pack of "
                                                        f"{' and '.join(where)}'s units only, and it can't be copied "
                                                        f"into {nation}'s skirmish packs: {why[0]}{more_why}. The game "
                                                        f"loads a nation's unit models only in matches where a player "
                                                        f"has that nation, so in other matches this unit would have no "
                                                        f"model, or crash the game. Copy one of {nation}'s units "
                                                        f"instead, or leave it in {where[0]}'s army", op))
                continue
            result.findings.append(Finding("note", f"{at}{name} is in {nation}'s army (Nationalite {n}), but its model "
                                                   f"{model}{more} is in the mesh pack of {' and '.join(where)}'s "
                                                   f"units only: its models go into {nation}'s skirmish packs too "
                                                   f"({_given_note(given)}), so it loads with {nation}'s own units",
                                           op))
        if own:
            result.model_changed.update(into.output())
        return
    loaded = unitcheck.load_everywhere(run.game, chosen)
    _also_loaded(run, [n for n in chosen if loaded[n][0]], result)
    for nation, (count, maps) in sorted(loaded.items()):
        if count:
            result.findings.append(Finding("note", f"{unitcheck.NATIONS[nation]}'s unit models and animations now load "
                                                   f"in every skirmish, beside those of the nations playing, for the "
                                                   f"units of other nations that use them ({count} loaders in {maps} "
                                                   f"cluster maps; matches take a little more memory and loading time)"))
    for name, op, missing, need in wanted:
        obj = run.game.objects[name]
        n = unitcheck.nation_of(obj)
        nation = unitcheck.NATIONS[n]
        model, where = next(iter(missing.items()))
        more = f" (and {len(missing) - 1} more)" if len(missing) > 1 else ""
        at = f"{op.at()}: " if op else ""
        packs_of = " and ".join(unitcheck.NATIONS[i] for i in need)
        if all(loaded[i][0] for i in need):
            result.findings.append(Finding("note", f"{at}{name} is in {nation}'s army (Nationalite {n}), but its model "
                                                   f"{model}{more} is in the mesh pack of {' and '.join(where)}'s units: "
                                                   f"{packs_of}'s unit models now load in every skirmish, so it shows "
                                                   f"in matches where no player has {packs_of} too", op))
            continue
        # rule: nation-models
        result.findings.append(Finding("error", f"{at}{name} is in {nation}'s army (Nationalite {n}), but its model "
                                                f"{model}{more} is in the mesh pack of {' and '.join(where)}'s units "
                                                f"only, and the unit data has no cluster maps that could load "
                                                f"{packs_of}'s models in every match: the game loads a "
                                                f"nation's unit models only in matches where a player has that nation, "
                                                f"so in other matches this unit has no model, or crashes the game. "
                                                f"Copy one of {nation}'s units instead, or leave it in {where[0]}'s "
                                                f"army", op))


def spawn_models(run, zz_win, mods: list, order: list[str], result: BuildResult, into=None) -> None:
    """Units a mod's scenarios spawn. A skirmish loads a nation's unit models only when a player has that nation
    (unitcheck); a spawned unit whose models aren't loaded crashes the game as the match starts (a D-Day test with
    Japanese units spawned and no Japanese player, 2026-10-01). So a spawned unit's models are copied into the common
    skirmish packs, which every skirmish loads (rusemod.unitpacks; `into` as for unit_models); a spawn whose models
    can't be copied is refused, saying why. (FORCE_LOAD: the old way, the nation's packs loaded everywhere.)"""
    from .scenario import Spawn
    spawns = [(m, ids) for moves, ids in scenario_edits(order, mods).values() for m in moves if isinstance(m, Spawn)]
    in_packs = skirmish_models(zz_win) if spawns and zz_win is not None else None
    if in_packs is None:
        return
    by_class = {}
    for name, obj in run.game.objects.items():
        cls = getattr(obj.props.get("ClassNameForDebug"), "value", None) if unitcheck.is_unit(obj) else None
        if cls:
            by_class.setdefault(cls, name)
    need: dict[int, dict[str, list[str]]] = {}  # nation -> {spawned class: the mods spawning it}
    names: dict[str, str] = {}  # the spawned unit's short name -> its object
    for s, ids in spawns:
        name = by_class.get(s.class_path.rpartition(".")[2])
        if name is None:
            continue
        obj = run.game.objects[name]
        home = unitcheck.nation_of(obj)
        for model in sorted(unitcheck.model_files(obj, run.game)):
            if model in in_packs["common"]:
                continue
            where = [i for i, tag in enumerate(unitcheck.PACK_TAGS) if model in in_packs[tag]]
            if where:
                pick = next((i for i in where if i in need), home if home in where else where[0])
                need.setdefault(pick, {}).setdefault(name.rsplit("/", 1)[-1], ids)
                names[name.rsplit("/", 1)[-1]] = name
    if not need:
        return
    if not FORCE_LOAD:
        own = into is None
        into = into or unitpacks.Packs(zz_win)
        for nation, units in sorted(need.items()):
            which = ", ".join(sorted(units))
            ids = ", ".join(sorted({i for v in units.values() for i in v}))
            country = unitcheck.NATIONS[nation]
            gave, why = unitpacks.Given(), []
            for short in sorted(units):
                obj = run.game.objects[names[short]]
                home = unitcheck.nation_of(obj)
                prefer = [unitpacks.TAGS[nation]] + ([unitpacks.TAGS[home]] if 0 <= home < len(unitpacks.TAGS) else [])
                try:
                    given, w = into.give(sorted(unitcheck.model_files(obj, run.game)), unitpacks.COMMON, prefer)
                except (unitpacks.PackError, ValueError, KeyError, IndexError, struct.error) as exc:
                    given, w = unitpacks.Given(), [f"the packs can't be read ({exc})"]
                why += [f"{short}: {x}" for x in w]
                for k in ("meshes", "skeletons", "animations", "textures", "sources"):
                    getattr(gave, k).extend(x for x in getattr(given, k) if x not in getattr(gave, k))
            if why:
                more = f" (and {len(why) - 1} more)" if len(why) > 1 else ""
                # rule: spawn-models
                result.findings.append(Finding("error", f"{ids}: the spawned {which} use {country}'s unit models, "
                                                        f"which a skirmish loads only when a player has {country}, and "
                                                        f"they can't be copied into the packs every skirmish loads: "
                                                        f"{why[0]}{more}. The game would crash as the match starts (a "
                                                        f"D-Day test with Japanese units spawned and no Japanese player "
                                                        f"did). Spawn units whose models every match has, or leave "
                                                        f"these out"))
            else:
                result.findings.append(Finding("note", f"{ids}: the spawned {which} use {country}'s unit models, which "
                                                       f"a skirmish loads only when a player has {country}: they go "
                                                       f"into the skirmish packs every match loads too "
                                                       f"({_given_note(gave)})"))
        if own:
            result.model_changed.update(into.output())
        return
    loaded = unitcheck.load_everywhere(run.game, set(need))
    _also_loaded(run, [n for n in need if loaded[n][0]], result)
    for nation, units in sorted(need.items()):
        which = ", ".join(sorted(units))
        ids = ", ".join(sorted({i for v in units.values() for i in v}))
        country = unitcheck.NATIONS[nation]
        count, maps = loaded.get(nation, (0, 0))
        if count:
            result.findings.append(Finding("note", f"{ids}: the spawned {which} use {country}'s unit models, which a "
                                                   f"skirmish loads only when a player has {country}: they now load "
                                                   f"in every skirmish ({count} loaders in {maps} cluster maps)"))
        else:
            why = "the unit data has no cluster maps that could load them in every match"
            # rule: spawn-models
            result.findings.append(Finding("error", f"{ids}: the spawned {which} use {country}'s unit models, which a "
                                                    f"skirmish loads only when a player has {country}, and {why}: "
                                                    f"the game would crash as the match starts (a D-Day test with "
                                                    f"Japanese units spawned and no Japanese player did). Spawn units "
                                                    f"whose models every match has, or leave these out"))


def fill_loc(game, keys: dict) -> list[str]:
    """Turn every loc('...') value into the game key its text got. Returns the loc keys no mod defines."""
    missing = []
    for obj in game.objects.values():
        for v in _walk_obj(obj):
            if isinstance(v, Text) and v.kind == "loc":
                if v.value in keys:
                    v.kind, v.value = "key", keys[v.value]
                elif v.value not in missing:
                    missing.append(v.value)
    return missing


def _reader(arc: Edat):
    entries = {e.path.lower(): e for e in arc.entries}

    def read(path: str):
        e = entries.get(path.lower())
        return bytes(arc.read(e)) if e is not None else None
    return read, entries


def unit_cards(run, order: list, result: BuildResult) -> dict:
    """New units' own cards (a mod's files/cards/<the unit's name>.png; rusemod.unitlook): a clone starts with its
    source's card file, so the two looked the same in the build menu (T33). Its TextureForInterface gets a file of its
    own beside the source's (a later mod's picture wins). Returns {card member to add: (its source's card member, the
    PNG)} for own_cards."""
    from .patch import Inline
    from .unitlook import card_member, own_card_name
    wanted: dict = {}
    for m in order:
        for unit, png in (getattr(m, "cards", None) or {}).items():
            wanted[unit] = (png, m.id)
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    for unit, (png, mod_id) in sorted(wanted.items()):
        name = by_name.get(unit)
        if name is None:
            # not a game rule: a card picture for a unit no mod in the set makes
            result.findings.append(Finding("error", f"{mod_id}: files/cards/{unit}.png: no mod in the set makes a new "
                                                    f"unit {unit} (a game unit's card is changed with "
                                                    f"files/replace/<its card>.tgv.png)"))
            continue
        tex = run.game.objects[name].props.get("TextureForInterface")
        file = tex.obj.props.get("FileName") if isinstance(tex, Inline) else None
        if not isinstance(file, Text) or file.kind != "path":
            # not a game rule: what our build supports (a card part of its own, naming a picture file)
            result.findings.append(Finding("error", f"{mod_id}: files/cards/{unit}.png: {unit} has no card of its own "
                                                    f"(TextureForInterface) naming a picture, so it can't get one"))
            continue
        new = own_card_name(file.value, unit)
        out[card_member(new)] = (card_member(file.value), png)
        tex.obj.props["FileName"] = Text("path", new)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets its own card, {new} (files/cards/{unit}.png), "
                                               f"made from {file.value}'s"))
    return out


def unit_own_models(run, order: list, result: BuildResult) -> dict:
    """New units' own models (a mod's files/models/<the unit's name>.glb; rusemod.unitmodel): the clone's model part
    names a model of its own, beside its source's, which the build writes into the packs that hold the source's.
    Returns {unit: (its source's model, the .glb, mod id)}."""
    from .patch import Inline
    wanted: dict = {}
    for m in order:
        for unit, glb in (getattr(m, "models", None) or {}).items():
            wanted[unit] = (glb, m.id)
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    for unit, (glb, mod_id) in sorted(wanted.items()):
        name = by_name.get(unit)
        if name is None:
            # not a game rule: a model for a unit no mod in the set makes
            result.findings.append(Finding("error", f"{mod_id}: files/models/{unit}.glb: no mod in the set makes a "
                                                    f"new unit {unit}"))
            continue
        gfx = run.game.objects[name].props.get("GfxDescriptor")
        mesh = gfx.obj.props.get("MeshDescriptor") if isinstance(gfx, Inline) else None
        file = mesh.obj.props.get("FileName") if isinstance(mesh, Inline) else None
        if not isinstance(file, Text) or file.kind != "path" or not file.value.lower().endswith(".ase2ndfbin"):
            # not a game rule: what our build supports (a model part of its own, naming one model file)
            result.findings.append(Finding("error", f"{mod_id}: files/models/{unit}.glb: {unit} has no model part of "
                                                    f"its own (GfxDescriptor.MeshDescriptor) naming a model, so it "
                                                    f"can't get one"))
            continue
        source = file.value
        folder = source.replace("/", "\\").rsplit("\\", 1)[0]
        mesh.obj.props["FileName"] = Text("path", f"{folder}\\{unit}lod0.Ase2ndfbin")
        out[unit] = (source, glb, mod_id)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets its own model (files/models/{unit}.glb), "
                                               f"beside {source}"))
    return out


def unit_classes(base, run, zz_win, result: BuildResult) -> None:
    """Give every new unit a class in the game's Python unit list (ZZ_Win.dat), like the unit it copies. Units the
    list can't take (made from scratch, or copies of units it doesn't list) get a warning: the game ignores them."""
    wanted = [(name, op) for name, op in run.created.items() if name in run.game.objects]
    found = pyscript.find_unit_list(zz_win) if zz_win is not None else None
    if found is None:
        if wanted:
            where = "ZZ_Win.dat wasn't given" if zz_win is None else "ZZ_Win.dat has no Python unit list"
            result.findings.append(Finding("note", f"{where}, so new objects got no class in it (the game only uses "
                                                   f"units that have one)"))
        return
    entry, pack, member, raw = found
    try:
        xyz = pyscript.read_xyz(raw)
        ul = pyscript.unit_list(xyz.payload)
    except pyscript.ScriptError as exc:
        # not a game rule: what our writer supports, or a file it can't read or write
        result.findings.append(Finding("error", f"the game's Python unit list can't be read: {exc}"))
        return
    for path in ul.by_path:
        if path in base.objects and path not in run.game.objects:
            # rule: delete-unit-class
            result.findings.append(Finding("error", f"{path} is deleted, but it has a class in the game's Python unit "
                                                    f"list; deleting such units isn't supported yet (the game would "
                                                    f"fail to load its units)"))
    unit_kinds = {base.objects[p].cls for p in ul.by_path if p in base.objects}
    new = []
    for name, op in wanted:
        obj = run.game.objects[name]
        like = ul.by_path.get(op.source) if op.kind == "clone" else None
        if like is None:
            if obj.cls in unit_kinds:
                result.findings.append(Finding("warning", f"{op.at()}: {name} is a new {obj.cls} but isn't a copy of "
                                                          f"a unit in the game's Python unit list, so the game will "
                                                          f"ignore it; make it a clone of one", op))
            continue
        debug = obj.props.get("ClassNameForDebug")
        if not isinstance(debug, Text):
            result.findings.append(Finding("error", f"{op.at()}: {name} has no ClassNameForDebug to name its class",
                                           op))
            continue
        new.append(pyscript.NewClass(debug.value, name, like.name))
    if not new or result.errors:
        return
    try:
        added = pyscript.add_classes(xyz.payload, new)
    except pyscript.ScriptError as exc:
        result.findings.append(Finding("error", f"the new units' classes can't be added: {exc}"))
        return
    new_xyz = pyscript.write_xyz(pyscript.Xyz(xyz.source_md5, added))
    result.script_changed = {entry.path: pack.to_bytes({member.path: new_xyz})}
    result.new_classes = [n.name for n in new]
    for n in new:
        base_name = ".".join(ul.classes[n.like].base)
        result.findings.append(Finding("note", f"{n.path} gets its class {n.name}(front.{base_name}) in the game's "
                                               f"Python unit list, like {n.like}"))


def build_pack(arc: Edat, mods: list, build_id: str = "0", text_arc: Edat | None = None) -> BuildResult:
    """Run `mods` [(ModInfo, ops)] on the data files of `arc`, and their texts and new units' classes on
    `text_arc` (ZZ_Win.dat; needed when a mod has text/*.csv or new units). Nothing is written; see
    BuildResult.changed / text_changed / script_changed."""
    order = load_order([m for m, _ in mods])
    by_id = {m.id: (m, ops) for m, ops in mods}
    result = BuildResult(order=[m.id for m in order])
    pack = load_pack(arc)
    base, loaded, members, shadows = pack.base, pack.loaded, pack.members, pack.shadows
    # the types mods place that the game doesn't draw from far get copies that it does, used by the mods' objects
    # alone (rusemod.visibility; the owner, 2026-10-03)
    from . import visibility
    placed = {getattr(o, "type", None) for m in order for objects in m.scenery.values() for o in objects}
    if any(r.bridges for _m, (roads, _ids) in scenario_edits(result.order, mods, "roads").items() for r in roads):
        from .scenery import descriptors as _descriptors  # the bridges the build adds for new roads: any kind
        placed |= {t for t, d in _descriptors(arc).items() if d.bridge}
    result.visibility = visibility.plan(base, {t for t in placed if t})
    extra = []
    if result.visibility:
        extra = [(ModInfo("r2-visibility"), parse(visibility.rndf(base, result.visibility), file="visibility.rndf",
                                                  mod="r2-visibility"))]
    run = Engine(base).run([by_id[m.id] for m in order] + extra)
    result.findings = [Finding("note", n) for n in base.notes] + list(run.findings)
    if shadows:
        result.findings.insert(0, Finding("note", f"left {len(shadows)} debug-info copies as shipped "
                                                  f"({', '.join(p.rsplit(chr(92), 1)[-1] for p in shadows)})"))
    if run.errors:
        return result
    into = unitpacks.Packs(text_arc) if text_arc is not None else None
    unit_models(base, run, text_arc, result, into)
    spawn_models(run, text_arc, mods, result.order, result, into)
    if result.errors:
        return result
    if into is not None:
        try:
            result.model_changed = into.output()
        except (unitpacks.PackError, ValueError, struct.error) as exc:
            # not a game rule: what our writer supports, or a file it can't read or write
            result.findings.append(Finding("error", f"the skirmish unit packs can't be written: {exc}"))
            return result
    text_mods = [(m.id, m.text_prefix, m.texts) for m in order if m.texts]
    text_plan, read, entries = None, None, {}
    if text_mods:
        if text_arc is None:
            result.findings.append(Finding("error", "these mods add texts, which go into ZZ_Win.dat; it wasn't given"))
            return result
        read, entries = _reader(text_arc)
        try:
            text_plan = loc.plan(text_mods, loc.game_keys_of(read, sorted({r.dictionary for _, _, rows in text_mods
                                                                             for r in rows})))
        except loc.TextError as exc:
            result.findings.append(Finding("error", str(exc)))
            return result
        result.findings += [Finding("warning", message) for message, _row in text_plan.warnings]
    for key in fill_loc(run.game, text_plan.keys if text_plan else {}):
        result.findings.append(Finding("error", f"loc('{key}') has no text: no mod in the set defines {key!r} in "
                                                f"its text/*.csv"))
    result.own_cards = unit_cards(run, order, result)
    result.own_models = unit_own_models(run, order, result)
    if result.errors:
        return result
    notes: list = []
    try:
        changed = save(base, run.game, loaded, run.created, notes, new_props={(unitcheck.LOADER, unitcheck.FORCE)})
    except ModelError as exc:
        result.findings.append(Finding("error", str(exc)))
        return result
    result.findings += [Finding("note", n) for n in notes]
    result.changed = {members[p]: data for p, data in changed.items()}
    result.fingerprint = fingerprint(build_id, changed)
    if text_plan:
        try:
            text_changed, text_notes = loc.apply(text_plan, read)
        except loc.TextError as exc:
            result.findings.append(Finding("error", str(exc)))
            return result
        result.findings += [Finding("note", n) for n in text_notes]
        result.text_changed = {entries[p.lower()].path: data for p, data in text_changed.items()}
    unit_classes(base, run, text_arc, result)
    return result


def terrain_edits(order: list[str], mods: list) -> dict[str, tuple[list, list[str]]]:
    """Every map a mod reshapes: {map pack name: (the strokes of all the mods in load order, the mods' ids)}."""
    by_id = {m.id: m for m, _ in mods}
    out: dict[str, tuple[list, list[str]]] = {}
    for mod_id in order:
        if mod_id not in by_id:  # a .rmod mod: rusemod.rmod applies its map changes
            continue
        for pack, strokes in by_id[mod_id].terrain.items():
            all_strokes, ids = out.setdefault(pack, ([], []))
            all_strokes.extend(strokes)
            ids.append(mod_id)
    return out


def scenery_edits(order: list[str], mods: list) -> dict[str, tuple[list, list[str]]]:
    """Every map a mod places scenery on: {map pack name: (the objects of all the mods in load order, the mods' ids)}."""
    by_id = {m.id: m for m, _ in mods}
    out: dict[str, tuple[list, list[str]]] = {}
    for mod_id in order:
        if mod_id not in by_id:
            continue
        for pack, objects in by_id[mod_id].scenery.items():
            every, ids = out.setdefault(pack, ([], []))
            every.extend(objects)
            ids.append(mod_id)
    return out


def scenario_edits(order: list[str], mods: list, what: str = "scenario") -> dict[str, tuple[list, list[str]]]:
    """Every map a mod moves design items on: {map pack name: (the moves of all the mods in load order, their ids)}.
    `what` "cover": the circles they paint on its cover instead (a later mod's circle over an earlier one's)."""
    by_id = {m.id: m for m, _ in mods}
    out: dict[str, tuple[list, list[str]]] = {}
    for mod_id in order:
        if mod_id not in by_id:
            continue
        for pack, moves in getattr(by_id[mod_id], what, {}).items():
            every, ids = out.setdefault(pack, ([], []))
            every.extend(moves)
            ids.append(mod_id)
    return out


def draw_new_roads(read_map, path_of, lines: list, shaded=None, cache=None) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): new roads (map points, in order) written into every road file the map's own roads
    are in: painted into the ground's tiles as the map's own roads are across (rusemod.groundpaint.road_profile: what
    shows from afar), marked in the map's close-up map the way its own roads are (paint_detail), and added to the
    map's road model (rusemod.roadstrips, the far road). What shows up close is the asphalt and edge stickers the
    scenery step lays along them (scenery.road_decals; proven in the game on D-Day 2026-10-02, TESTS.md T12).
    `read_map(member)` gives the map pack's member as the build has it so far (a reshaped ground counts) or None,
    `path_of(member)` its full path. `shaded(x, y, i)`: true where lines[i] runs under trees (a road that keeps its
    trees, in one of the map's woods): painted fainter and greyer there (groundpaint.UNDER_TREES). A road that clears
    its trees is painted through a wood as the map's own roads are (the owner, 2026-10-03). `cache`: a folder where
    the map's measured road look is kept between builds (groundpaint.map_road_profile)."""
    from .groundpaint import DETAIL, DETAIL_WIDER, ROAD_WIDTH, grid_bounds, map_road_profile, paint_detail, paint_roads
    from .roadstrips import draw_roads
    from .scenery import MEMBER as SCENERY, Scenery
    raw = read_map(SCENERY)
    pieces = Scenery(raw).roads() if raw else []
    profile = map_road_profile(read_map, pieces, cache)  # new roads painted as the map's own are across (2026-10-02)
    painted, notes = paint_roads(read_map, path_of, lines, pieces, profile=profile, shaded=shaded, cache=cache)
    detail, mesh = read_map(DETAIL), read_map("output\\highdef.tms")
    if detail is not None and mesh is not None:
        marked, more = paint_detail(detail, grid_bounds(mesh), lines, pieces, ROAD_WIDTH * DETAIL_WIDER, profile)
        notes += more
        if marked:
            painted[path_of(DETAIL)] = marked
    strips, more = draw_roads(read_map, path_of, lines)
    return {**painted, **strips}, notes + more


def close_up_copy(text_arc, map_name: str, shipped: bytes, marked: bytes) -> tuple[str, bytes] | None:
    """(its path in ZZ_Win.dat, the new bytes) for the copy of a map's close-up map kept there
    (gen\\datasmap\\<map>\\mapdiversite\\div_map.tgv, the same bytes as the pack's on every shipped map), when it is
    the pack's shipped one: kept the same as the pack's new one. None when there's no such copy (a new map) or it
    differs (a mod changed one of them: left as it is)."""
    if text_arc is None:
        return None
    try:
        e = text_arc.find(f"gen\\datasmap\\{map_name.lower()}\\mapdiversite\\div_map.tgv")
    except KeyError:
        return None
    return (e.path, marked) if bytes(text_arc.read(e)) == shipped else None


def build_cache() -> Path:
    """BUILD_CACHE: the folder in the platform's own folder (rusemod.home) where builds keep what they measure once
    (a map's road look: groundpaint.map_road_profile). Safe to delete: it's measured again."""
    from .home import default_home
    return default_home() / "cache" / "build"


def find_pack(game: Path, name: str) -> Path | None:
    """A pack by path, or by name in the game folder (newest data revision first found, then Maps\\PC)."""
    p = Path(name)
    if p.is_file():
        return p
    candidates = [game / "Data" / "PC" / rev / name for rev in data_revisions(game)] + [game / "Maps" / "PC" / name]
    for c in candidates:
        if c.is_file():
            return c
    for folder in {c.parent for c in candidates if c.parent.is_dir()}:  # case-insensitive match
        for f in folder.iterdir():
            if f.name.lower() == name.lower():
                return f
    return None


_NAMES = re.compile(r"\$/\S+|\S+#\d+")


def report_lines(findings, show_all: bool = False, keep: int = 3):
    """Errors first, then warnings, then notes. Findings that differ only in object names are collapsed to the
    first `keep` plus a count, unless show_all."""
    out = []
    for level in ("error", "warning", "note"):
        groups: dict[str, list] = {}
        for f in findings:
            if f.level == level:
                groups.setdefault(_NAMES.sub("…", f.message), []).append(f)
        for items in groups.values():
            shown = items if show_all else items[:keep]
            out += [f"  {level:7}  {f.message}" for f in shown]
            if len(items) > len(shown):
                out.append(f"  {level:7}  … and {len(items) - len(shown)} more like this (--all shows them)")
    return out


def build_and_write(game: Path, mods: list, *, pack: str = DEFAULT_PACK, out: Path | None = None,
                    instance: Path | None = None, say=print, show_all: bool = False,
                    cache: Path | None = None) -> BuildResult:
    """Build `mods` [(ModInfo, ops)] against the game at `game` and write the result: rebuilt packs to `out` (a .dat
    file, or a folder for several packs) and/or a modded copy at `instance`. This is `ruse build`, and the launcher's
    Play. `say` gets every report line as it comes. Nothing is written when the build has errors. Problems the user
    can fix raise BuildError. `cache`: a folder for what can be measured once and kept between builds (BUILD_CACHE
    under the platform's folder for the apps and `ruse build`; none in the tests).

    .rmod mods (rusemod.rmod) are applied first, in their order in `mods`, and the other mods on top of them. Two
    .rmod mods that can't go together (the same file replaced with different contents, MOD_FORMAT.md §13) stop the
    build before anything is built, with every such clash named; a later mod overwriting an earlier one's values is
    a warning."""
    rmods = [m for m, _ops in mods if m.rmod is not None]
    mods = [(m, ops) for m, ops in mods if m.rmod is None]
    overwrites: list = []
    if len(rmods) > 1:
        from . import rmod
        found = rmod.clashes([m.rmod for m in rmods])
        hard = [c for c in found if c.hard]
        if hard:
            for c in hard:
                say(f"  error    {c.message}")
            raise BuildError(rmod.refusal(hard))
        overwrites = [Finding("warning", c.message) for c in found]
    pack_path = find_pack(game, pack)
    if pack_path is None:
        raise BuildError(f"No pack called {pack!r} in {game}.")
    text_path = None
    if needs_zz_win(mods):
        text_path = find_pack(game, loc.PACK)
        if text_path is None:
            raise BuildError(f"These mods add texts, new units or new maps, which need {loc.PACK}, but {game} "
                             f"doesn't have it.")
    elif _spawns(mods):  # spawned units' models are checked against its packs when it's there (spawn_models)
        text_path = find_pack(game, loc.PACK)
    if instance is not None and os.path.lexists(instance):  # the old copy goes first, so it can't be started by
        from .instance import set_aside_old                  # mistake while the new one builds (the owner did, twice)
        set_aside_old(str(game), str(instance))
        say(f"the old copy at {instance} is set aside until the new one is ready")
    build_id = build_of(game) or "0"  # the fingerprint includes the game build
    with ExitStack() as stack:
        run = None
        if rmods:
            from . import rmod
            say(".rmod mods first: " + " -> ".join(m.id for m in rmods))
            run = rmod.apply(game, [m.rmod for m in rmods], build_of(game), say)
            stack.callback(run.close)

        new_packs: dict = {}  # a new map's pack (a path the game hasn't got) -> newmap.NewPack over the shipped one

        def open_pack(path: Path) -> Edat:
            """A pack as the .rmod mods left it (or as shipped); a new map's, as the copy it is."""
            if path in new_packs:
                return new_packs[path]
            layered = run.layered(path) if run else None
            return layered if layered is not None else stack.enter_context(Edat.open(str(path)))

        arc = open_pack(pack_path)
        text_arc = open_pack(text_path) if text_path else None
        try:
            result = build_pack(arc, mods, build_id, text_arc) if mods else BuildResult()
        except ResolveError as exc:
            raise BuildError(f"load order: {exc}") from None
        if run:
            result.order = [m.id for m in rmods] + result.order
            result.findings = overwrites + run.findings + result.findings
        say("load order: " + " -> ".join(result.order))
        for line in report_lines(result.findings, show_all=show_all):
            say(line)
        counts = {lvl: sum(1 for f in result.findings if f.level == lvl) for lvl in ("error", "warning", "note")}
        say(f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['note']} note(s)")
        if result.errors:
            say("Nothing was written.")
            return result
        from .terrain import pack_file
        reported, said = len(result.findings), set()  # the findings the report above showed; the later ones said

        def warn(message: str) -> None:
            """A warning found while the maps are built (after the report above): kept and said at once."""
            result.findings.append(Finding("warning", message))
            said.add(id(result.findings[-1]))
            say(f"warning: {message}")
        # new maps first (rusemod.newmap): the mods' other map files then edit them like any map
        new_paths: dict = {}  # new map's pack name, lower case -> its pack's path, as the copy will have it
        sources: dict = {}    # new map's pack name, lower case -> the shipped map's folder (its water constants)
        data_base, data_new = None, {}  # DataMap_Win.dat as opened for the new maps, and the members they add
        try:
            making = new_maps(result.order, mods)
        except BuildError as exc:
            result.findings.append(Finding("error", str(exc)))
            making = {}
        if making:
            from .newmap import Grown, NewMapError, NewPack, make
            from .scenario import PACK as DATA_PACK
            data_path = find_pack(game, DATA_PACK)
            if data_path is None:
                # not a game rule: the game or one of its files isn't found
                result.findings.append(Finding("error", f"{DATA_PACK} isn't in this game, so no map can be added (the "
                                                        f"maps' scenarios and grids live there)"))
                making = {}
            else:
                data_base = open_pack(data_path)
            glad_new: dict = {}

            def reading(*layers):
                """read(member) over {member: bytes} layers (any case), then a pack (the last)."""
                def read(member):
                    key = member.replace("/", "\\").lower()
                    for layer in layers[:-1]:
                        found = next((d for m, d in layer.items() if m.lower() == key), None)
                        if found is not None:
                            return found
                    e = layers[-1].entry(member) if layers[-1] is not None else None
                    return bytes(layers[-1].read(e)) if e is not None else None
                return read
            for name, (spec, mod_id) in making.items():
                try:
                    clone = make(name, spec, reading(result.changed, glad_new, arc), reading(data_new, data_base),
                                 reading(result.text_changed, text_arc))
                except (NewMapError, ValueError, KeyError, struct.error) as exc:
                    result.findings.append(Finding("error", f"{mod_id}: {exc}"))
                    continue
                source = find_pack(game, clone.pack_from)
                if source is None:
                    # not a game rule: the game or one of its files isn't found
                    result.findings.append(Finding("error", f"{mod_id}: maps/{name}: {clone.pack_from}, the pack of "
                                                            f"{spec.copy_of}, isn't in this game, so it can't be copied"))
                    continue
                for member, data in clone.glad_changed.items():
                    e = arc.entry(member)
                    for old in [m for m in result.changed if m.lower() == member.lower()]:
                        del result.changed[old]
                    result.changed[e.path if e is not None else member] = data
                for member, data in clone.texts.items():
                    e = text_arc.entry(member)
                    result.text_changed[e.path if e is not None else member] = data
                glad_new.update(clone.glad)
                data_new.update(clone.data)
                path = Path(game) / "Maps" / "PC" / pack_file(name)
                new_packs[path] = NewPack(open_pack(source), clone.pack_id, source.name)
                new_paths[name.lower()] = path
                sources[name.lower()] = clone.map_folder
                result.new_maps[name] = clone
                say(f"new map: {name}, from {mod_id}")
                for note in clone.notes:
                    say(f"  {note}")
            if glad_new:
                arc = Grown(arc, glad_new)

        def find_map(name: str):
            """A map's pack: a new map's (the path its copy gets), else the game's; None when it has none."""
            return new_paths.get(name.lower()) or find_pack(game, pack_file(name))
        map_packs = []  # (path, open pack, {member: new bytes})
        flooded: dict = {}  # map pack name -> (nav.Block over each new water, the mods' ids)
        beds: dict = {}     # map pack name -> (nav.Block opens over each dried bed, the mods' ids)
        for name, (strokes, ids) in terrain_edits(result.order, mods).items():
            map_path = find_map(name)
            if map_path is None:
                # not a game rule: the game or one of its files isn't found
                result.findings.append(Finding("error", f"{', '.join(ids)}: the map {name} isn't in this game "
                                                        f"({pack_file(name)} is missing), so its ground can't be "
                                                        f"changed{_meant(game, name)}"))
                continue
            map_arc = open_pack(map_path)

            def read(member, a=map_arc):
                try:
                    return bytes(a.read(a.find(member)))
                except KeyError:
                    return None

            def depth_of(n=sources.get(name.lower(), name), a=arc):
                """The map's MaxDepthForSimulationDepthMap, from its mapwaterconstante in the unit-data pack (a new
                map's is the shipped map's)."""
                from .ndf import Ndf
                from .water import max_depth

                def nd():
                    try:
                        e = a.find(f"genglad\\patchable\\map\\{n.lower()}\\mapwaterconstante.cpp.gladndfbin")
                    except KeyError:
                        return None
                    return Ndf(bytes(a.read(e))) if e is not None else None
                return max_depth(nd)

            try:
                changed_members, notes = edit_map(read, strokes, name, max_depth_of=depth_of)
            except (ValueError, struct.error, zlib.error) as exc:
                result.findings.append(Finding("error", f"{map_path.name}: its ground files can't be read ({exc})"))
                continue
            say(f"terrain: {name}, from {', '.join(ids)}")
            for note in notes:
                say(f"  {note}")
            from .terrain_edit import FILES as GROUND, _area_of
            before = read(GROUND["highdef"]) if GROUND["highdef"] in changed_members else None
            if before is not None:  # ground under water is never walkable on a shipped map: new water is blocked
                from .bridges import Water
                from .nav import Block, water_blocks
                from .tms import Tms
                try:
                    now_at = Water(Tms(changed_members[GROUND["highdef"]])).at
                    zones, drained = water_blocks(Water(Tms(before)).at, now_at, [_area_of(s) for s in strokes])
                except (ValueError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: where the terrain edits put "
                                                            f"water can't be worked out ({exc}), so units could walk "
                                                            f"on the bed of new water"))
                    continue
                if zones:
                    flooded[name] = ([Block(x, y, r, "all") for x, y, r in zones], ids)
                    say(f"  {name}: {len(zones)} block(s) over the new water, so units keep out of it")
                if drained:  # a dried bed: the map's movement has no ground there, so it's opened to units
                    beds[name] = ([Block(x, y, r, "all", True) for x, y, r in _bed_circles(drained, now_at)], ids)
                    mx, my = (sum(p[k] for p in drained) / len(drained) for k in (0, 1))
                    say(f"  {name}: water drained around ({mx:.0f}, {my:.0f}): its bed opened to units "
                        f"({len(beds[name][0])} circle(s))")
            if changed_members:
                map_packs.append((map_path, map_arc, changed_members))
                result.terrain_changed[map_path.name] = changed_members
        # bridges where new roads cross water (rusemod.bridges): the map's own bridge kind placed along each
        # crossing (walk-through), and the crossing's deck kept for the movement graphs below
        # and bridges placed by hand (scenery.toml objects of a bridge kind, any size): coded as bridges, they open
        # their deck to units instead of blocking it, and a road crossing one gets no second bridge
        # and a road over one of the map's own bridges gets the new one in its place: the old one sunk out of sight,
        # its deck over water closed to units and to the road network (owner, 2026-09-30)
        bridge_spans: dict = {}   # map pack name -> [(x0, y0, x1, y1)]
        bridge_objects: dict = {}  # map pack name -> (the bridge objects, the mods' ids)
        bridge_hide: dict = {}    # map pack name -> [(block index, item offset)]: old bridges to sink
        bridge_obstacles: dict = {}  # map pack name -> [(x, y)]: the map's buildings and props by the decks' roads
        bridge_closed: dict = {}  # map pack name -> [(x, y, r)]: where they stood over water
        bridge_decks: dict = {}   # map pack name -> every deck a new road runs over (the painter leaves them)
        bridge_roads: dict = {}   # map pack name -> the mods' road lines: a deck's approaches follow them (nav.Graph.open)
        bridge_water: dict = {}   # map pack name -> where its water is (Water.at): no approach over it
        placed = scenery_edits(result.order, mods)
        road_edits = scenario_edits(result.order, mods, "roads")
        from .bridges import BridgeError, model_length, placed_spans, plan
        from .scenery import MEMBER as SCENERY, Scenery, SceneryError, descriptors
        descs, lengths = None, {}

        def length_of(kind):
            if kind not in lengths:
                lengths[kind] = model_length(game, descs, kind)
            return lengths[kind]
        for name in sorted(set(road_edits) | set(placed), key=str.lower):
            map_roads, road_ids = road_edits.get(name, ([], []))
            objects_here, object_ids = placed.get(name, ([], []))
            wanted = [r.points for r in map_roads if r.bridges]
            if descs is None and (wanted or objects_here):
                descs = descriptors(arc)
            by_hand = [o for o in objects_here if o.type in descs and descs[o.type].bridge] if descs else []
            map_path = find_map(name) if wanted or by_hand else None
            if map_path is None:
                continue  # (a missing map is said with the road network and the scenery below)
            ids = list(dict.fromkeys(road_ids + (object_ids if by_hand else [])))
            spans = placed_spans(by_hand, descs, length_of) if by_hand else []
            objects, notes, gone = [], [], []
            if by_hand:
                notes.append(f"{len(by_hand)} bridge(s) placed by hand: movement opened along their decks")
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            done = entry[2] if entry else {}

            def read_map(member, a=map_arc, done=done):
                try:
                    e = a.find(member)
                except KeyError:
                    return None
                return done.get(e.path) or bytes(a.read(e))
            if wanted:
                try:
                    sc_raw, mesh = read_map(SCENERY), read_map("output\\highdef.tms")
                    if sc_raw is None or mesh is None:
                        raise BridgeError("the map has no scenery or no ground mesh")
                    made = plan(mesh, wanted, Scenery(sc_raw), descs, length_of, existing=spans)
                except (BridgeError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the roads' bridges can't be made ({exc})"))
                    continue
                objects = made.objects
                spans += made.spans
                notes += made.notes
                gone = made.gone
                if made.hide:
                    bridge_hide[name] = made.hide
                    bridge_closed[name] = made.closed
                if made.kept:
                    bridge_decks[name] = list(made.kept)
            if spans:  # the map's buildings and props by the new decks' roads: the decks' approaches never cover the
                # holes the map's movement leaves for them (rusemod.bridges.near_ends; the owner's D-Day test, 2026-09-30:
                # an approach through a farm, "end of bridge hits buildings causing pathing issue")
                from .bridges import OPEN, near_ends
                from .mapcheck import map_objects
                try:
                    sc_way = read_map(SCENERY)
                    pieces = near_ends([r.points for r in map_roads], spans)
                    if sc_way is not None and pieces:
                        bridge_obstacles[name] = [(x, y) for _t, x, y, group in
                                                  map_objects(Scenery(sc_way), descs, pieces, reach=2 * OPEN)
                                                  if group == "building"]  # (props: rocks and jetties at the water)
                except (SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    notes.append(f"the map's buildings by the new bridges couldn't be read ({exc}): their approaches "
                                 f"may run through them")
            if objects or by_hand or gone:  # the floors units stand on (rusemod.floors): new bridges get their kind's
                from . import floors
                from .bridges import Ground, Water, deck as deck_of, shipped_bridges
                from .kdt import Kdt
                from .tms import Tms
                try:
                    k_raw, mesh, sc_raw = read_map(floors.MEMBER), read_map("output\\highdef.tms"), read_map(SCENERY)
                    if k_raw is None or mesh is None or sc_raw is None:
                        raise floors.FloorError("the map has no objects-only ground to hold bridge floors")
                    shipped = shipped_bridges(Scenery(sc_raw), descs, length_of)
                    new = [(floors.Deck.of(*deck_of(o, *length_of(o.type))),
                            [floors.Deck.of(*b.deck) for b in shipped if b.kind == o.type]) for o in objects + by_hand]
                    ground_mesh = Tms(mesh)  # (the water, and the ground bucketed: for the floors' aprons, which
                    data, floor_notes = floors.floors_for(  # test thousands of places beside the new decks)
                        Kdt(k_raw), Ground(ground_mesh).height_at, new, [floors.Deck.of(*d) for d in gone],
                        made.water.at if wanted else Water(ground_mesh).at)
                    if data:
                        done[map_arc.find(floors.MEMBER).path] = data
                        if entry is None:
                            map_packs.append((map_path, map_arc, done))
                        result.terrain_changed[map_path.name] = done
                    notes += floor_notes
                except floors.NoFloor as exc:  # movement opens along every deck: refused, never the riverbed
                    from .bridges import bridge_type
                    every = objects + by_hand
                    what = ", ".join(f"the {every[i].type.split('/')[-1]} at ({every[i].x:.0f}, {every[i].y:.0f})"
                                     for i in exc.missing)
                    try:
                        sc_own = Scenery(read_map(SCENERY))
                        own = bridge_type(sc_own.names, sc_own.types(), descs)
                    except (SceneryError, ValueError, KeyError, TypeError, struct.error, zlib.error):
                        own = None
                    result.findings.append(Finding("error", (
                        f"{', '.join(ids)}: {name}: {what} would have no floor (no bridge of its kind on this map has "
                        f"one to copy), so units would walk on the riverbed under it: use the map's own bridge kind"
                        + (f" ({own})" if own else "") + " or take it out")))
                    continue
                except (floors.FloorError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the new bridges' floors can't "
                                                            f"be made ({exc}), so units would walk on the riverbed "
                                                            f"under them"))
                    continue
            if objects:
                bridge_objects[name] = (objects, road_ids)
            if spans:
                bridge_spans[name] = spans
                bridge_roads[name] = [r.points for r in map_roads]
                if wanted:
                    bridge_water[name] = made.water.at
                else:  # bridges placed by hand only
                    from .bridges import Water
                    from .tms import Tms
                    ground = read_map("output\\highdef.tms")
                    bridge_water[name] = Water(Tms(ground)).at if ground is not None else None
            if notes:
                say(f"bridges: {name}, from {', '.join(ids)}")
                for note in notes:
                    say(f"  {note}")
        for name, (objects, ids) in bridge_objects.items():
            every, who = placed.setdefault(name, ([], []))
            every.extend(objects)
            who.extend(i for i in ids if i not in who)
        # new roads get the map's own road pieces (Route stickers) in the scenery, as the map's roads have them, and,
        # to show up close, its asphalt and edge stickers along them with their path cleared (road_decals: proven in
        # the game 2026-10-02); the other road files are written below (draw_new_roads: the painted ground, from afar)
        from .bridges import cut
        from .scenery import ROAD_CLEAR, ROAD_DECALS, RoadPiece, road_clearing, road_decals, road_pieces
        ROAD_CLEAR_M = round(ROAD_CLEAR / 260, 1)  # in metres for the notes (about 260 map units to the metre)
        with_pieces = {name: (list(objects), list(ids)) for name, (objects, ids) in placed.items()}
        road_lines: dict = {}  # map pack name -> the new roads' lines off the bridge decks (for the stickers)
        under_trees: dict = {}  # map pack name -> the ids of those lines whose road keeps its trees (keep_trees)
        for name, (map_roads, ids) in road_edits.items():
            decks = bridge_spans.get(name, []) + bridge_decks.get(name, [])
            lines = []
            for r in (r for r in map_roads if r.paint):
                part = cut([r.points], decks)
                if r.keep_trees:
                    under_trees.setdefault(name, set()).update(id(line) for line in part)
                lines += part
            pieces = [q for line in lines for q in road_pieces(line)]
            if pieces and find_map(name) is not None:  # (a missing map is said with the roads)
                every, who = with_pieces.setdefault(name, ([], []))
                every.extend(pieces)
                who.extend(i for i in ids if i not in who)
                road_lines[name] = lines
        erasing = scenario_edits(result.order, mods, "erase")  # the mods' erase areas (scenery.toml [[erase]])
        for name, (_areas, ids) in erasing.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        from .brush import PAINT_KINDS
        painting = scenario_edits(result.order, mods, "paint")  # Map Paint: what hides it up close goes (`clear`)
        for name, (strokes, ids) in painting.items():
            if any(s.kind.kind in PAINT_KINDS and s.clear for s in strokes):
                every, who = with_pieces.setdefault(name, ([], []))
                who.extend(i for i in ids if i not in who)
        low_sizes: dict = {}  # type name -> how far it reaches at size 1 (stickers, low plants, stones), once a build
        solid: dict = {}  # map pack name -> (nav.Block for each placed building, the mods' ids)
        for name, (objects, ids) in with_pieces.items():
            map_path = find_map(name)
            if map_path is None:
                # not a game rule: the game or one of its files isn't found
                result.findings.append(Finding("error", f"{', '.join(ids)}: the map {name} isn't in this game "
                                                        f"({pack_file(name)} is missing), so nothing can be placed "
                                                        f"on it{_meant(game, name)}"))
                continue
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            changed_members = entry[2] if entry else {}
            from .scenery import (MEMBER, SceneryEditError, SceneryError, add_objects, bury_objects,
                                  erase_objects)
            areas, erase_ids = erasing.get(name, ([], []))
            try:
                member = map_arc.find(MEMBER).path
                raw = changed_members.get(member) or bytes(map_arc.read(map_arc.find(MEMBER)))
                raw, sunk = bury_objects(raw, bridge_hide.get(name, []))  # before the new blocks move them
                dressed: list = []
                if road_lines.get(name):  # up close: the map's asphalt stickers along the new roads, path cleared
                    sc_now = Scenery(raw)
                    used = {sc_now.names[i]: n for i, n in sc_now.types().items()}
                    asphalt = max((t for t in ROAD_DECALS if used.get(t)), key=lambda t: used[t], default=None)
                    if asphalt is None:
                        sunk = sunk + ["new roads: this map has none of the asphalt stickers the game's maps lay "
                                       "along their roads, so new roads show from afar only (the painted ground)"]
                    else:
                        edge, gap = ROAD_DECALS[asphalt]
                        edge = edge if used.get(edge) else None
                        dressed = [o for line in road_lines[name] for o in road_decals(line, asphalt, edge, gap)]
                        shaded = under_trees.get(name, set())
                        areas = list(areas) + [a for line in road_lines[name]
                                               for a in road_clearing(line, keep_trees=id(line) in shaded)]
                        kept = sum(1 for line in road_lines[name] if id(line) in shaded)
                        sunk = sunk + [f"new roads up close: {sum(1 for o in dressed if o.type == asphalt)} asphalt "
                                       f"sticker(s) ({asphalt.split('/')[-1]})"
                                       + (f" with their edges ({edge.split('/')[-1]})" if edge else "")
                                       + f"; the plants and props on their path taken off ({ROAD_CLEAR_M} m either "
                                       f"side; woods' cover and movement unchanged)"
                                       + (f", but {kept} of {len(road_lines[name])} keep their trees and bushes "
                                          f"(keep_trees: only props taken off)" if kept else "")]
                objects = list(objects) + dressed
                sizes = None  # an erase by size (Map Paint's clearing): how far each type reaches
                strokes = painting.get(name, ([], []))[0]
                if any(s.kind.kind in PAINT_KINDS and s.clear for s in strokes):
                    # up close the game draws the map's stickers, low plants and stones over the ground's picture:
                    # only with them taken off does the paint show near the camera (TESTS.md T21, T26)
                    from .groundpaint import paint_clearing
                    from .scenery import low_cover, model_reach, sticker_reach
                    if descs is None:
                        descs = descriptors(arc)
                    low = low_cover(descs, set(Scenery(raw).names))
                    under = paint_clearing(strokes, low)
                    if under:
                        if not low_sizes:
                            low_sizes.update(sticker_reach(arc))
                        missing = [t for t in low if t not in low_sizes]
                        if missing:
                            from .models import Library
                            lib = Library(game)
                            try:
                                for t in missing:
                                    low_sizes[t] = model_reach(lib, descs[t])
                            finally:
                                lib.close()
                        areas = list(areas) + under
                        sizes = low_sizes
                        sunk = sunk + [f"Map Paint: what hides it up close taken off under {len(under)} stroke(s) "
                                       f"(ground stickers, low plants and stones reaching where it is at least half "
                                       f"strength; trees, buildings, cover and movement unchanged)"]
                erased_notes, erased = [], {}
                if areas:  # the map's own scenery out first: the new objects then stay whatever the areas cover
                    if descs is None:
                        descs = descriptors(arc)
                    names = Scenery(raw).names
                    kinds = {i: descs[n].group for i, n in enumerate(names) if n in descs}
                    bridges = {i for i, n in enumerate(names) if n in descs and descs[n].bridge}
                    raw, erased_notes, erased = erase_objects(raw, areas, kinds, bridges, sizes)
                if descs is None:
                    descs = descriptors(arc)
                lowest = _LowestPoints(game, descs)
                try:
                    objects, lowered = grounded(objects, descs, lowest)
                finally:
                    lowest.close()
                as_placed = objects  # by their own types: what the steps after go by (solid buildings, ...)
                seen = result.visibility  # placed types with no far mode: their copies, drawn from far too
                if seen and any(getattr(o, "type", None) in seen for o in objects):
                    from dataclasses import replace as _replace
                    from .scenery import add_names
                    swapped = sorted({o.type for o in objects if getattr(o, "type", None) in seen})
                    objects = [_replace(o, type=seen[o.type]) if getattr(o, "type", None) in seen else o for o in objects]
                    raw = add_names(raw, [seen[t] for t in swapped])
                    sunk = sunk + [f"drawn from far too (the game draws these only up close, or no further than the "
                                   f"middle distance): "
                                   f"{', '.join(t.split('/')[-1] for t in swapped)}; the mod's objects use copies of "
                                   f"them ({SEEN_SUFFIX}), the map's own stay as shipped"]
                changed_members[member], notes = add_objects(raw, objects)
                notes = sunk + erased_notes + notes + ([f"{lowered} placed object(s) lowered to stand on the ground "
                                                        f"(their models start above their base point: an upper "
                                                        f"storey, say)"] if lowered else [])
            except KeyError:
                result.findings.append(Finding("error", f"{map_path.name} has no scenery file, so nothing can be "
                                                        f"placed on {name}"))
                continue
            except (SceneryError, SceneryEditError) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: {exc}"))
                continue
            say(f"scenery: {name}, from {', '.join(ids)}")
            for note in notes:
                say(f"  {note}")
            if erased.get("building"):
                if any("building" in a.what and not a.keep_ground for a in areas):
                    say(f"  {erased['building']} of the map's buildings erased: the ground of the erase area(s) that "
                        f"take buildings is opened to every unit (cleared_woods; seen in the game, T25)")
                if any("building" not in a.what and any(t in descs and descs[t].group == "building"
                                                        and not descs[t].bridge for t in a.types) for a in areas):
                    result.findings.append(Finding("warning", (
                        f"{', '.join(erase_ids)}: {name}: buildings erased by name (an erase area's types) leave their "
                        f"ground closed to units: the map's movement still has them. Name \"building\" in that area's "
                        f"what to open its ground too")))
            if erased.get("bridge"):
                result.findings.append(Finding("warning", (
                    f"{', '.join(erase_ids)}: {name}: {erased['bridge']} of the map's bridges erased: units can still "
                    f"cross the water where they stood (the map's movement still has the decks). Leave the bridges "
                    f"out of the erase areas' types, or place a bridge there again")))
            from .nav import solid_blocks
            # by the placed types, not their far-drawn copies (rusemod.visibility), which the game's descriptors list
            # under the copies' names only: a copied building stays solid to units
            walls, wall_notes = solid_blocks(game, [o for o in as_placed if not isinstance(o, RoadPiece)])
            for note in wall_notes:
                say(f"  {note}")
            if walls:
                solid[name] = (walls, ids)
            if entry is None:
                map_packs.append((map_path, map_arc, changed_members))
            result.terrain_changed[map_path.name] = changed_members
        def woods_of(name):
            """The map's woods (its grid's "in forest" cells, as shipped), or None when its grid can't be read."""
            from .cover import CoverError, in_forest, member
            data_path = find_pack(game, "DataMap_Win.dat")
            if data_path is None:
                return None
            try:
                data_arc = open_pack(data_path)
                return in_forest(bytes(data_arc.read(data_arc.find(member(name)))))
            except (KeyError, CoverError, ValueError, struct.error):
                return None

        for name, (strokes, ids) in scenario_edits(result.order, mods, "paint").items():  # the Map Paint strokes,
            # before the new roads, so a road drawn over paint shows on top of it
            map_path = find_map(name)
            if map_path is None:
                # not a game rule: the game or one of its files isn't found
                result.findings.append(Finding("error", f"{', '.join(ids)}: the map {name} isn't in this game "
                                                        f"({pack_file(name)} is missing), so it can't be painted"
                                                        f"{_meant(game, name)}"))
                continue
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            changed_members = entry[2] if entry else {}

            def read_map(member, a=map_arc, done=changed_members):
                try:
                    e = a.find(member)
                except KeyError:
                    return None
                return done.get(e.path) or bytes(a.read(e))
            from .groundpaint import DETAIL, PaintError, paint_ground
            try:
                painted, notes = paint_ground(read_map, lambda m, a=map_arc: a.find(m).path, strokes, cache)
            except (PaintError, ValueError, KeyError, struct.error, zlib.error) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the paint can't be laid ({exc})"))
                continue
            changed_members.update(painted)
            say(f"paint: {name}, from {', '.join(ids)}: {len(strokes)} stroke(s) on the ground's picture")
            for note in notes:
                say(f"  {note}")
            marked = next((v for k, v in painted.items() if k.lower().endswith(DETAIL)), None)
            copy = close_up_copy(text_arc, name, bytes(map_arc.read(map_arc.find(DETAIL))), marked) if marked else None
            if copy:
                result.close_up_maps[copy[0]] = copy[1]
                say(f"  close-up map: its copy in {text_path.name} kept the same")
            if entry is None and painted:
                map_packs.append((map_path, map_arc, changed_members))
            if painted:
                result.terrain_changed[map_path.name] = changed_members
        for name, (map_roads, ids) in scenario_edits(result.order, mods, "roads").items():  # new roads painted
            from .bridges import cut
            decks = bridge_spans.get(name, []) + bridge_decks.get(name, [])
            lines, keep = [], set()  # the lines off the bridges' decks; those of roads that keep their trees
            for r in (r for r in map_roads if r.paint):
                part = cut([r.points], decks)
                if r.keep_trees:
                    keep.update(range(len(lines), len(lines) + len(part)))
                lines += part
            map_path = find_map(name) if lines else None
            if map_path is None:
                continue  # (a missing map is said with the road network below)
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            changed_members = entry[2] if entry else {}

            def read_map(member, a=map_arc, done=changed_members):
                try:
                    e = a.find(member)
                except KeyError:
                    return None
                return done.get(e.path) or bytes(a.read(e))
            from .groundpaint import PaintError
            from .scenery import SceneryError
            try:
                wood = woods_of(name) if keep else None
                shaded = (lambda x, y, i, wood=wood, keep=keep: i in keep and wood(x, y)) if wood else None
                painted, notes = draw_new_roads(read_map, lambda m, a=map_arc: a.find(m).path, lines, shaded, cache)
            except (PaintError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the new roads can't be drawn ({exc})"))
                continue
            changed_members.update(painted)
            # what the player reads: what was seen in the game (T12, 2026-10-02: the paint from afar, the stickers up
            # close, laid in the scenery step above)
            say(f"roads: {name}, from {', '.join(ids)}: painted into the ground as the map's own roads are (what shows "
                f"from afar); up close the map's asphalt stickers draw them (see the scenery notes)")
            for note in notes:
                say(f"  {note}")
            from .groundpaint import DETAIL
            marked = next((v for k, v in painted.items() if k.lower().endswith(DETAIL)), None)
            copy = close_up_copy(text_arc, name, bytes(map_arc.read(map_arc.find(DETAIL))), marked) if marked else None
            if copy:
                result.close_up_maps[copy[0]] = copy[1]
                say(f"  close-up map: its copy in {text_path.name} kept the same")
            if entry is None and painted:
                map_packs.append((map_path, map_arc, changed_members))
            if painted:
                result.terrain_changed[map_path.name] = changed_members
        data_packs = []  # (path, open pack, {member: new bytes}): DataMap_Win.dat, the scenarios and the cover grids
        moves, paints = scenario_edits(result.order, mods), scenario_edits(result.order, mods, "cover")
        blocks = scenario_edits(result.order, mods, "movement")
        new_roads = scenario_edits(result.order, mods, "roads")
        from .scenario import PACK as MOVEMENT_PACK  # (the movement and cover grids live in the scenarios' pack)
        cleared, uncover = cleared_woods(erasing) if find_pack(game, MOVEMENT_PACK) is not None else ({}, {})
        for name, (more, ids) in uncover.items():
            every, who = paints.setdefault(name, ([], []))
            every.extend(more)
            who.extend(i for i in ids if i not in who)
        for name, (walls, ids) in (list(cleared.items()) + list(beds.items()) + list(flooded.items())
                                   + list(solid.items())):  # after the mods' own blocks and opens: cleared woods and
            every, who = blocks.setdefault(name, ([], []))    # dried beds opened, new water closed, and placed
            every.extend(walls)                               # buildings last, so units always go around them
            who.extend(i for i in ids if i not in who)
        players = scenario_edits(result.order, mods, "players")
        if moves or paints or blocks or new_roads or bridge_spans or players or data_new:
            from .bridges import BridgeError, apply_spans
            from .cover import CoverError, apply_paints
            from .nav import NavError, apply_blocks, closing
            from .roadnet import RoadNetError, apply_roads
            from .scenario import PACK as SCENARIO_PACK, ScenarioError, apply_moves
            data_path = find_pack(game, SCENARIO_PACK)
            if data_path is None:
                # not a game rule: the game or one of its files isn't found
                result.findings.append(Finding("error", f"{SCENARIO_PACK} isn't in this game, so no starting point or "
                                                        f"spawn can be moved, and no cover painted"))
            else:
                data_arc = Grown(data_base, data_new) if data_new else open_pack(data_path)  # (a new map's files)
                changed_members: dict = {}

                def read_data(member, a=data_arc):
                    try:
                        return changed_members.get(member) or bytes(a.read(a.find(member)))
                    except KeyError:
                        return None

                def read_glad(member, a=arc):
                    """A ZZ_GladPatchableWin.dat member as the build has it so far (any case), or None."""
                    key = member.lower()
                    mine = next((d for m, d in result.changed.items() if m.lower() == key), None)
                    if mine is not None:
                        return mine
                    e = a.entry(member)
                    return bytes(a.read(e)) if e is not None else None
                classes: list = []  # [the unit list's class names, or None when it can't be read], read once
                shipped: list = []  # [every class path the shipped spawns use], read once when needed

                def registered_classes():
                    if not classes:
                        zz_path = text_path or find_pack(game, loc.PACK)  # (ZZ_Win.dat: the mods may not need it)
                        zz = text_arc if text_arc is not None else open_pack(zz_path) if zz_path else None
                        found = pyscript.find_unit_list(zz) if zz is not None else None
                        try:
                            ul = pyscript.unit_list(pyscript.read_xyz(found[3]).payload) if found else None
                        except pyscript.ScriptError:
                            ul = None
                        classes.append(None if ul is None else
                                       {n for n, c in ul.classes.items() if c.registered} | set(result.new_classes))
                    return classes[0]

                def shipped_paths():
                    if not shipped:
                        from .scenario import shipped_class_paths
                        shipped.append(shipped_class_paths(data_arc))
                    return shipped[0]
                missions_read: dict = {}  # (map, scenario file) -> its mission's camps (rusemod.missions), read once

                def mission_camps(map_name: str, file: str) -> list:
                    key = (map_name.lower(), file.lower())
                    if key not in missions_read:
                        from . import missions
                        ia_path = find_pack(game, "IA_Common.dat")
                        try:
                            with Edat.open(str(ia_path)) as ia:
                                missions_read[key] = missions.scenario_camps(ia, map_name, file)
                        except (OSError, TypeError, KeyError, ValueError, struct.error, zlib.error):
                            missions_read[key] = []  # no script to read: the warning falls back to the spawns
                    return missions_read[key]
                for name, (map_moves, ids) in moves.items():
                    from .players import skirmish_files
                    from .scenario import Move, Spawn, spawn_class_problems
                    new_spawns = [m for m in map_moves if isinstance(m, Spawn)]
                    wrong = spawn_class_problems(name, new_spawns, registered_classes(), shipped_paths) if new_spawns else []
                    # rule: spawn-class
                    if wrong:  # a class the game can't find makes loading the map fail
                        result.findings += [Finding("error", f"{', '.join(ids)}: {w}") for w in wrong]
                        continue
                    unset = [m for m in map_moves if getattr(m, "z", 0.0) is None and (
                        not isinstance(m, Move) or m.kind in ("StartingPoint", "Spawn"))]
                    map_path = find_map(name) if unset else None
                    if map_path is not None:  # a new or moved starting point or spawn sits at the ground's height,
                        # as every shipped one does (the game puts a spawned unit at the height it's given)
                        from .tms import Tms
                        entry = next((e for e in map_packs if e[0] == map_path), None)
                        map_arc = entry[1] if entry else open_pack(map_path)
                        try:
                            e = map_arc.find("output\\highdef.tms")
                            ground = Tms((entry[2].get(e.path) if entry else None) or bytes(map_arc.read(e)))
                            for m in unset:
                                m.z = ground.height_at(m.x, m.y)
                        except (KeyError, ValueError, struct.error, zlib.error):
                            pass  # without the ground, a start takes its teammate's height
                    try:
                        new, notes = apply_moves(read_data, name, map_moves, skirmish_files(read_glad, name),
                                                 warn=lambda msg, ids=ids: warn(f"{', '.join(ids)}: {msg}"),
                                                 mission=lambda file, name=name: mission_camps(name, file))
                    except (ScenarioError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"scenario: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                for name, (map_paints, ids) in paints.items():
                    from .cover import unpaired_blocked
                    for p in unpaired_blocked(map_paints, closing(blocks.get(name, ([], []))[0])):
                        result.findings.append(Finding("warning", (
                            f"{', '.join(ids)}: {name}: cover.toml paints the blocked layer at ({p.x:.0f}, {p.y:.0f}) "
                            f"with no movement.toml block there. The blocked layer only tells the AI where it can't "
                            f"see or build; units still walk on it. To keep units off, add a [[block]] with the same "
                            f"x, y and radius to movement.toml")))
                    try:
                        new, notes = apply_paints(read_data, name, map_paints)
                    except (CoverError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"cover: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                for name, (map_blocks, ids) in blocks.items():
                    idle: list = []
                    try:
                        new, notes = apply_blocks(read_data, name, map_blocks, idle)
                    except (NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"movement: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                    for b in idle:
                        result.findings.append(Finding("note", (
                            f"{', '.join(ids)}: {name}: the open at ({b.x:.0f}, {b.y:.0f}) opened nothing: units "
                            f"could already go there, or it is too small (an open needs a radius of 5 m or more) or "
                            f"out of reach of the ground they use")))
                    for b, (wx, wy) in _wet_opens(open_pack, game, name, map_blocks, map_packs, find_map):
                        result.findings.append(Finding("warning", (
                            f"{', '.join(ids)}: {name}: the open at ({b.x:.0f}, {b.y:.0f}) takes in water (at "
                            f"({wx:.0f}, {wy:.0f})): units there stand on the ground under it, on the riverbed or "
                            f"the lake's floor. Leave the open off the water unless that is what you want")))
                for name, spans in bridge_spans.items():  # the bridges' decks opened to units, after the blocks
                    try:
                        new, notes = apply_spans(read_data, name, spans, bridge_closed.get(name, []), bridge_roads.get(name, []),
                                                 closing(blocks.get(name, ([], []))[0]), bridge_water.get(name),
                                                 bridge_obstacles.get(name, []))
                    except (BridgeError, NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{name}: the bridges' movement can't be opened ({exc})"))
                        continue
                    changed_members.update(new)
                    say(f"bridges open: {name}")
                    for note in notes:
                        say(f"  {note}")
                for name, (map_roads, ids) in new_roads.items():  # the road network (buffer 0), after movement
                    try:
                        new, notes = apply_roads(read_data, name, map_roads, closing(blocks.get(name, ([], []))[0]))
                    except (RoadNetError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"roads: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                for name, (map_moves, ids) in moves.items():  # the mods' starting points on the final ground
                    from .scenario import start_ground_problems
                    # rule: start-ground
                    wrong, far = start_ground_problems(read_data, name, map_moves)
                    result.findings += [Finding("error", f"{', '.join(ids)}: {w}") for w in wrong]
                    for w in far:
                        warn(f"{', '.join(ids)}: {w}")
                for name, (settings, ids) in players.items():  # how many players: after the mods' starting points
                    from .players import PlayersError, apply_players
                    from .scenario import Scenario, folder_of

                    def places(file, n=name):
                        raw = read_data(folder_of(n) + file)
                        try:
                            return Scenario.read(raw).team_sizes() if raw else None
                        except (ScenarioError, ValueError, struct.error):
                            return None
                    try:
                        new, notes = apply_players(read_glad, name, settings[-1], places,  # the last mod's count
                                                   warn=lambda msg, ids=ids: warn(f"{', '.join(ids)}: map.toml: {msg}"))
                    except (PlayersError, ValueError, KeyError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    for member, data in new.items():
                        e = arc.entry(member)
                        for old in [m for m in result.changed if m.lower() == member.lower()]:
                            del result.changed[old]
                        result.changed[e.path if e is not None else member] = data
                    say(f"players: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                from .aigrid import AiGridError, refresh
                for member in [m for m in changed_members if m.lower().endswith("mapinfo.win")]:
                    try:  # the AI's grid follows the cover, blocks, bridges and water (rusemod.aigrid)
                        changed_members[member], notes = refresh(bytes(data_arc.read(data_arc.find(member))),
                                                                 changed_members[member])
                    except (AiGridError, KeyError, ValueError, struct.error) as exc:
                        notes = [f"the AI grid couldn't be updated ({exc}): the AI keeps the map's old woods and "
                                 f"open ground"]
                    where = member.split("\\")[-2]
                    for note in notes:
                        say(f"  {where}: {note}")
                if changed_members or data_new:
                    data_packs.append((data_path, data_arc, changed_members))
        for path, pack in new_packs.items():  # a new map's pack is written even when no mod edits its files
            if not any(e[0] == path for e in map_packs):
                map_packs.append((path, pack, {}))
        late = [f for f in result.findings[reported:] if f.level == "warning" and id(f) not in said]
        for line in report_lines(late, show_all=show_all):  # the maps' warnings (a drained river's was never shown)
            say(line)
        if result.errors:
            for line in report_lines([f for f in result.findings if f.level == "error"], show_all=show_all):
                say(line)
            say("Nothing was written.")
            return result
        rmod_packs = run.changed_packs() if run else {}
        for path, a, changed in [(pack_path, arc, result.changed)] + data_packs:  # the members new maps add
            if getattr(a, "added", None) and hasattr(a, "added_with"):
                result.added[path.name] = a.added_with(changed)
        if map_packs or rmod_packs or data_packs:
            gameplay = {}
            for p, a in rmod_packs.items():
                where = f"Maps/PC/{p.name}/" if p.parent.parent.name.lower() == "maps" else ""
                gameplay.update({where + m: d for m, d in {**a.changed, **a.added}.items()})
            gameplay.update(result.changed)
            gameplay.update(result.added.get(pack_path.name, {}))
            for map_path, a, changed_members in map_packs:
                gameplay.update({f"Maps/PC/{map_path.name}/{m}": d for m, d in changed_members.items()})
                if map_path in new_packs:  # a new map: which pack it copies, and its id
                    gameplay[f"Maps/PC/{map_path.name}"] = a.source.encode() + a.pack_id
            for data_path, _a, changed_members in data_packs:
                gameplay.update({f"{data_path.name}/{m}": d for m, d in changed_members.items()})
                gameplay.update({f"{data_path.name}/{m}": d for m, d in result.added.get(data_path.name, {}).items()})
            result.fingerprint = fingerprint(build_id, gameplay)
        for p, a in rmod_packs.items():
            say(f"changed by .rmod mods: {p.name} ({len(a.changed)} file(s) changed, {len(a.added)} added)")
        for path in result.changed:
            say(f"changed: {path}")
        if result.text_changed:
            names: dict[str, int] = {}
            for path in result.text_changed:
                name = path.rsplit("\\", 1)[-1]
                names[name] = names.get(name, 0) + 1
            say(f"texts: {len(result.text_changed)} file(s) in {text_path.name} ("
                + ", ".join(f"{n} ×{c}" for n, c in sorted(names.items())) + ")")
        if result.new_classes:
            say(f"unit list: {len(result.new_classes)} class(es) added to {pyscript.UNIT_LIST} in {text_path.name} ("
                + ", ".join(result.new_classes) + ")")
        if result.model_changed:
            say(f"unit models: {len(result.model_changed)} skirmish pack(s) in {text_path.name} ("
                + _pack_names(result.model_changed) + ")")
        for map_path, a, changed_members in map_packs:
            files = ", ".join(m.rsplit(chr(92), 1)[-1] for m in changed_members)
            if map_path in new_packs:
                say(f"new: {map_path.name}, a copy of {a.source}"
                    + (f" ({len(changed_members)} file(s) changed: {files})" if changed_members else ""))
            else:
                say(f"changed: {map_path.name} ({len(changed_members)} file(s): {files})")
        textures: dict = {}  # painted textures (MOD_FORMAT §7, rusemod.unitlook): a later mod's picture wins
        by_id = {m.id: m for m, _ops in mods}
        for mod_id in result.order:
            textures.update(getattr(by_id.get(mod_id), "textures", None) or {})
        if textures and text_arc is not None:
            from .unitlook import LookError, changes as texture_changes
            say(f"painted textures: {len(textures)}")
            try:
                result.texture_changed = texture_changes(text_arc, textures, say=say, before=result.model_changed)
            except LookError as exc:
                raise BuildError(str(exc)) from None
        if result.own_cards and text_arc is not None:  # new units' own cards, in the menu packs (rusemod.unitlook)
            from .unitlook import LookError, own_cards
            try:
                result.texture_changed.update(own_cards(text_arc, result.own_cards,
                                                        {**result.model_changed, **result.texture_changed}, say=say))
            except LookError as exc:
                raise BuildError(str(exc)) from None
        if result.own_models and text_arc is not None:  # new units' own models (rusemod.unitmodel)
            from .newmap import Grown
            from .unitmodel import UnitModelError, read_mod_glb, write_unit_model
            for unit, (source, glb, mod_id) in sorted(result.own_models.items()):
                try:
                    written = write_unit_model(text_arc, source, unit, read_mod_glb(glb), earlier={
                        **result.model_changed, **result.texture_changed, **result.model_imports})
                except (UnitModelError, ValueError, OSError, struct.error) as exc:
                    raise BuildError(f"{mod_id}: files/models/{Path(glb).name}: {exc}") from None
                result.model_imports.update(written.changed)
                result.model_textures.update(written.added)
                r = written.report
                say(f"own model of {unit}: {r.get('vertices', '?')} points, {r.get('triangles', '?')} triangles in "
                    f"{r.get('draws', '?')} draw call(s), {len(written.added)} texture(s); into "
                    f"{len(written.changed)} pack(s) beside {source}")
            text_arc = Grown(text_arc, result.model_textures)  # its textures: files of ZZ_Win.dat's own
        zz_win_changed = {**result.text_changed, **result.script_changed, **result.model_changed,
                          **result.close_up_maps, **result.texture_changed, **result.model_imports}
        for data_path, _a, changed_members in data_packs:
            new_ones = {m.lower() for m in result.added.get(data_path.name, {})}
            shipped = [m for m in changed_members if m.replace("/", "\\").lower() not in new_ones]  # (new: "added")
            if shipped:
                say(f"changed: {data_path.name} ({len(shipped)} file(s): "
                    + ", ".join(m.rsplit(chr(92), 1)[-1] for m in shipped) + ")")
        for name, members in result.added.items():
            say(f"added: {name} ({len(members)} file(s): " + ", ".join(sorted(members, key=str.lower)) + ")")
        rebuilt = [(pack_path, arc, result.changed), (text_path, text_arc, zz_win_changed)] + map_packs + data_packs
        listed = {Path(path).resolve() for path, _a, _c in rebuilt if path}
        rebuilt += [(p, a, {}) for p, a in rmod_packs.items() if p not in listed]
        # a pack the .rmod mods changed writes their changes too, even when the other mods leave it alone
        rebuilt = [(path, a, changed) for path, a, changed in rebuilt if changed or getattr(a, "is_changed", False)]
        if not rebuilt:
            say("The mods change nothing in these packs.")
            return result
        if result.fingerprint is None:
            result.fingerprint = fingerprint(build_id, result.changed)
        say(f"fingerprint: {fingerprint_text(result.fingerprint)}")
        if out is not None:
            out = Path(out)
            if out.suffix.lower() == ".dat":
                if len(rebuilt) > 1:
                    raise BuildError(f"these mods rebuild {len(rebuilt)} packs ("
                                     + ", ".join(path.name for path, _a, _c in rebuilt) + "): give --out a folder")
                targets = [(out, rebuilt[0][1], rebuilt[0][2])]
            else:
                out.mkdir(parents=True, exist_ok=True)
                targets = [(out / path.name, a, changed) for path, a, changed in rebuilt]
            for target, a, changed in targets:
                with target.open("wb") as f:
                    a.write_to(f, changed)
                say(f"wrote {target}")
        if instance is not None:
            from .instance import build_instance
            replace, add = {}, {}
            for path, a, changed in rebuilt:
                rel = str(path.resolve().relative_to(Path(game).resolve()))
                # a new map's pack isn't in the game: the copy gets it as a file of its own
                (replace if path.exists() else add)[rel] = (lambda f, a=a, changed=changed: a.write_to(f, changed))
            copied = build_instance(str(game), str(instance), replace=replace, add=add)
            say(f"modded copy ready: {instance}  {copied}")
            locked = copied.get("read-only packs", 0)
            if copied.get("full copies", 0) > locked:
                say(f"note: {instance} is on another drive than the game, so its {copied['full copies'] - locked} "
                    f"packs are full copies, which take disk space. On the game's drive they'd be free.")
            if locked:
                say(f"note: {locked} of the game's packs are marked read-only, so they were copied rather than linked "
                    f"(a link would share the mark, and the copy couldn't be removed later). Unticking Read-only in "
                    f"the game folder's Properties would save that space.")
            if copied.get("old copy left"):
                say(f"note: the previous copy at {instance}.old couldn't be removed yet; the next build removes it.")
    return result
