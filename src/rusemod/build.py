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

from . import loc, pyscript, unitcheck
from .brush import BrushError, parse_strokes
from .edat import Edat
from .lock import fingerprint, fingerprint_text
from .model import ModelError, game_path, load, save
from .patch import Engine, Finding, Text, _walk_obj
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
        info.roads = _read_maps(path, "roads.toml")
        info.players = _read_maps(path, "map.toml")
    info.when_mods = {mid for op in ops for mid, _rng, _neg in op.when}
    return info, ops


_MAP_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def _map_readers() -> dict:
    """Each map file a mod may hold (maps/<map pack>/<file>): the tables it holds, how it says so, how its rows are
    read, and what its reader raises."""
    from .cover import CoverError, parse_paints
    from .nav import NavError, parse_blocks
    from .players import PlayersError, parse_map
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
        "map.toml": (("players", "entry"), "a map file holds players = N (and entry = the map-list name)",
                     lambda d, rel: parse_map(d, rel), PlayersError),
    }


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


def _clearings(game: Path, road_edits: dict, placed: dict, spans: dict, descs=None) -> dict:
    """Where the build clears the map's trees and props for what the mods build: {map pack name: ([(where, erase
    areas)], the mods' ids)}: a strip along each new road (roads.toml, unless clear = false), a circle under each
    building placed (its model's reach and a margin) and around each end of each new bridge (MOD_FORMAT §8)."""
    from .nav import building_reach
    from .scenery import CLEAR_MARGIN, EraseArea, NewObject, bridge_end_clearing, road_clearing
    from .terrain import pack_file
    out: dict = {}
    for name in sorted(set(road_edits) | set(placed) | set(spans), key=str.lower):
        if find_pack(game, pack_file(name)) is None:
            continue  # (a missing map is said with the roads and the scenery)
        jobs, ids = [], []
        roads, road_ids = road_edits.get(name, ([], []))
        for n, r in enumerate(roads, start=1):
            if r.clear:
                x, y = r.points[0]
                jobs.append((f"along road {n} (from ({x:.0f}, {y:.0f}))", road_clearing(r.points)))
                ids += road_ids
        objects, object_ids = placed.get(name, ([], []))
        buildings, _notes = building_reach(game, [o for o in objects if isinstance(o, NewObject)], descs)
        if buildings:
            jobs.append((f"under the {len(buildings)} new building(s)",
                         [EraseArea(o.x, o.y, r + CLEAR_MARGIN) for o, r in buildings]))
            ids += object_ids
        if spans.get(name):
            jobs.append((f"at the ends of the {len(spans[name])} new bridge(s)", bridge_end_clearing(spans[name])))
            ids += road_ids + object_ids
        if jobs:
            out[name] = (jobs, list(dict.fromkeys(ids)))
    return out


def _cleared_notes(jobs: list, tally: dict, first: int) -> list[str]:
    """How many of the map's objects each clearing took (`tally`: erase_objects', its areas from index `first`)."""
    notes, k = [], first
    for where, areas in jobs:
        n = sum(tally.get(i, 0) for i in range(k, k + len(areas)))
        k += len(areas)
        notes.append(f"{n:,} of the map's trees and props cleared {where}")
    return notes


def _cover_brushes(info) -> None:
    """The Studio's cover and uncover brushes live in terrain.toml with the others, but paint the map's cover grid,
    not the ground: they move to `info.cover` (after the mod's own cover.toml circles), and a map whose strokes are
    all cover ones leaves the ground files alone."""
    from .cover import Paint
    for pack, strokes in list(info.terrain.items()):
        cover = [s for s in strokes if s.kind.kind == "cover"]
        if not cover:
            continue
        info.cover.setdefault(pack, []).extend(Paint(s.x, s.y, s.radius, "cover", s.kind.sign < 0, s.square)
                                               for s in cover)
        rest = [s for s in strokes if s.kind.kind != "cover"]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


def read_movement(folder: Path) -> dict:
    """A mod's ground units can't use: {map pack name: [nav.Block]} from maps/<map pack>/movement.toml (MOD_FORMAT
    §8)."""
    return _read_maps(folder, "movement.toml")


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
        info.movement.setdefault(pack, []).extend(Block(s.x, s.y, s.radius, s.kind.shape, s.kind.kind == "open")
                                                  for s in blocks)
        rest = [s for s in strokes if s.kind.kind not in moving]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


def _wet_opens(open_pack, game: Path, name: str, blocks, map_packs) -> list:
    """nav.wet_opens for a map's opens, on its ground as the terrain edits left it (map_packs: (pack path, archive,
    changed members); `open_pack(path)` opens a map pack); none when the map has no opens or its ground can't be
    read."""
    from .bridges import Water
    from .nav import wet_opens
    from .terrain import pack_file
    from .tms import Tms
    if not any(b.open for b in blocks):
        return []
    map_path = find_pack(game, pack_file(name))
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
    new_classes: list = field(default_factory=list)  # class names added to the game's Python unit list
    terrain_changed: dict = field(default_factory=dict)  # map pack file name -> {member path: new bytes}
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
    """Whether building `mods` [(ModInfo, ops)] needs ZZ_Win.dat: some mod adds texts, or new objects (a new unit
    needs a class in the Python unit list, which lives there), or moves a unit to another nation or model (the
    skirmish mesh packs there say whether its models are loaded for it: unit_models)."""
    return any(m.texts for m, _ in mods) or any(op.kind in ("create", "clone") or _moves(op)
                                                for _, ops in mods for op in ops)


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


def unit_models(base, run, zz_win, result: BuildResult) -> None:
    """New units, and units moved to another nation or given other models, whose models are only in another nation's
    skirmish mesh pack: the game loads a nation's unit models only in matches where a player has that nation, or that
    the cluster maps' loaders force (unitcheck). So that such a unit shows in every match, that nation's packs are set
    to load in every skirmish (unitcheck.load_everywhere, on `run.game`), with a note; a unit the cluster maps can't
    do that for (the unit data has none) is refused. What the game's own units already have is fine."""
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
    loaded = unitcheck.load_everywhere(run.game, chosen)
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
        result.findings.append(Finding("error", f"{at}{name} is in {nation}'s army (Nationalite {n}), but its model "
                                                f"{model}{more} is in the mesh pack of {' and '.join(where)}'s units "
                                                f"only, and the unit data has no cluster maps that could load "
                                                f"{packs_of}'s models in every match: the game loads a nation's unit "
                                                f"models only in matches where a player has that nation, so in other "
                                                f"matches this unit has no model, or crashes the game. Copy one of "
                                                f"{nation}'s units instead, or leave it in {where[0]}'s army", op))


def spawn_models(run, zz_win, mods: list, order: list[str], result: BuildResult) -> None:
    """Units a mod's scenarios spawn. A skirmish loads a nation's unit models only when a player has that nation, or
    when the cluster maps' loaders force it (unitcheck); a spawned unit whose models aren't loaded crashes the game as
    the match starts (a D-Day test with Japanese units spawned and no Japanese player, 2026-10-01). So the nations
    whose packs hold a spawned unit's models are set to load in every skirmish, as for units given to another nation;
    a spawn the cluster maps can't do that for is refused."""
    from .scenario import Spawn
    spawns = [(m, ids) for moves, ids in scenario_edits(order, mods).values() for m in moves if isinstance(m, Spawn)]
    packs = skirmish_models(zz_win) if spawns and zz_win is not None else None
    if packs is None:
        return
    by_class = {}
    for name, obj in run.game.objects.items():
        cls = getattr(obj.props.get("ClassNameForDebug"), "value", None) if unitcheck.is_unit(obj) else None
        if cls:
            by_class.setdefault(cls, name)
    need: dict[int, dict[str, list[str]]] = {}  # nation -> {spawned class: the mods spawning it}
    for s, ids in spawns:
        name = by_class.get(s.class_path.rpartition(".")[2])
        if name is None:
            continue
        obj = run.game.objects[name]
        home = unitcheck.nation_of(obj)
        for model in sorted(unitcheck.model_files(obj, run.game)):
            if model in packs["common"]:
                continue
            where = [i for i, tag in enumerate(unitcheck.PACK_TAGS) if model in packs[tag]]
            if where:
                pick = next((i for i in where if i in need), home if home in where else where[0])
                need.setdefault(pick, {}).setdefault(name.rsplit("/", 1)[-1], ids)
    if not need:
        return
    loaded = unitcheck.load_everywhere(run.game, set(need))
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
            result.findings.append(Finding("error", f"{ids}: the spawned {which} use {country}'s unit models, which a "
                                                    f"skirmish loads only when a player has {country}, and the unit "
                                                    f"data has no cluster maps that could load them in every match: "
                                                    f"the game would crash as the match starts. Spawn units whose "
                                                    f"models every match has, or leave these out"))


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
        result.findings.append(Finding("error", f"the game's Python unit list can't be read: {exc}"))
        return
    for path in ul.by_path:
        if path in base.objects and path not in run.game.objects:
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
    run = Engine(base).run([by_id[m.id] for m in order])
    result.findings = [Finding("note", n) for n in base.notes] + list(run.findings)
    if shadows:
        result.findings.insert(0, Finding("note", f"left {len(shadows)} debug-info copies as shipped "
                                                  f"({', '.join(p.rsplit(chr(92), 1)[-1] for p in shadows)})"))
    if run.errors:
        return result
    unit_models(base, run, text_arc, result)
    spawn_models(run, text_arc, mods, result.order, result)
    if result.errors:
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
                    instance: Path | None = None, say=print, show_all: bool = False) -> BuildResult:
    """Build `mods` [(ModInfo, ops)] against the game at `game` and write the result: rebuilt packs to `out` (a .dat
    file, or a folder for several packs) and/or a modded copy at `instance`. This is `ruse build`, and the launcher's
    Play. `say` gets every report line as it comes. Nothing is written when the build has errors. Problems the user
    can fix raise BuildError.

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
            raise BuildError(f"These mods add texts or new units, which need {loc.PACK}, but {game} doesn't have "
                             f"it.")
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

        def open_pack(path: Path) -> Edat:
            """A pack as the .rmod mods left it (or as shipped)."""
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

        def warn(message: str) -> None:
            """A warning found while the maps are built (after the report above): kept and said at once."""
            result.findings.append(Finding("warning", message))
            say(f"warning: {message}")
        map_packs = []  # (path, open pack, {member: new bytes})
        flooded: dict = {}  # map pack name -> (nav.Block over each new water, the mods' ids)
        for name, (strokes, ids) in terrain_edits(result.order, mods).items():
            map_path = find_pack(game, pack_file(name))
            if map_path is None:
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

            def depth_of(n=name, a=arc):
                """The map's MaxDepthForSimulationDepthMap, from its mapwaterconstante in the unit-data pack."""
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
                    zones, drained = water_blocks(Water(Tms(before)).at, Water(Tms(changed_members[GROUND["highdef"]])).at,
                                                  [_area_of(s) for s in strokes])
                except (ValueError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: where the terrain edits put "
                                                            f"water can't be worked out ({exc}), so units could walk "
                                                            f"on the bed of new water"))
                    continue
                if zones:
                    flooded[name] = ([Block(x, y, r, "all") for x, y, r in zones], ids)
                    say(f"  {name}: {len(zones)} block(s) over the new water, so units keep out of it")
                if len(drained) >= 3:
                    mx, my = (sum(p[k] for p in drained) / len(drained) for k in (0, 1))
                    result.findings.append(Finding("warning", (
                        f"{', '.join(ids)}: {name}: the terrain edits drain water around ({mx:.0f}, {my:.0f}), but "
                        f"the dried ground stays closed to units: the map's movement has no ground where the water "
                        f"was. Paint it with the Open brush to let units on it, leave the water there, or expect "
                        f"units to go around")))
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
            map_path = find_pack(game, pack_file(name)) if wanted or by_hand else None
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
        # new roads are drawn up close by road stickers (the game's Route pieces), from afar by the painted ground:
        # the pieces go into the scenery with the placed objects (seen in the game, 2026-09-30: without them a new
        # road vanished near the camera)
        from .bridges import cut
        from .scenery import RoadPiece, road_pieces
        with_pieces = {name: (list(objects), list(ids)) for name, (objects, ids) in placed.items()}
        for name, (map_roads, ids) in road_edits.items():
            decks = bridge_spans.get(name, []) + bridge_decks.get(name, [])
            pieces = [q for line in cut([r.points for r in map_roads if r.paint], decks) for q in road_pieces(line)]
            if pieces and find_pack(game, pack_file(name)) is not None:  # (a missing map is said with the roads)
                every, who = with_pieces.setdefault(name, ([], []))
                every.extend(pieces)
                who.extend(i for i in ids if i not in who)
        erasing = scenario_edits(result.order, mods, "erase")  # the mods' erase areas (scenery.toml [[erase]])
        for name, (_areas, ids) in erasing.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        # the map's trees and props cleared where the mods build: along each new road (unless clear = false), under
        # each building placed and at each new bridge's ends (rusemod.scenery.road_clearing): [(what, its areas)]
        clearing = _clearings(game, road_edits, with_pieces, bridge_spans, descs)
        for name, (_jobs, ids) in clearing.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        solid: dict = {}  # map pack name -> (nav.Block for each placed building, the mods' ids)
        for name, (objects, ids) in with_pieces.items():
            map_path = find_pack(game, pack_file(name))
            if map_path is None:
                result.findings.append(Finding("error", f"{', '.join(ids)}: the map {name} isn't in this game "
                                                        f"({pack_file(name)} is missing), so nothing can be placed "
                                                        f"on it{_meant(game, name)}"))
                continue
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            changed_members = entry[2] if entry else {}
            from .scenery import (MEMBER, SceneryEditError, SceneryError, SceneryFull, add_objects, bury_objects,
                                  erase_objects)
            areas, erase_ids = erasing.get(name, ([], []))
            jobs = clearing.get(name, ([], []))[0]
            cleared = [a for _what, job in jobs for a in job]
            try:
                member = map_arc.find(MEMBER).path
                raw = changed_members.get(member) or bytes(map_arc.read(map_arc.find(MEMBER)))
                raw, sunk = bury_objects(raw, bridge_hide.get(name, []))  # before the new blocks move them
                erased_notes, erased, tally = [], {}, {}
                if areas or cleared:  # the map's own scenery out first: the new objects then stay whatever it covers
                    if descs is None:
                        descs = descriptors(arc)
                    names = Scenery(raw).names
                    kinds = {i: descs[n].group for i, n in enumerate(names) if n in descs}
                    bridges = {i for i, n in enumerate(names) if n in descs and descs[n].bridge}
                    raw, erased_notes, erased = erase_objects(raw, list(areas) + cleared, kinds, bridges, tally)
                    erased_notes = ([n for n in erased_notes  # (the clearing's own counts said below)
                                     if areas or not (n.startswith("the erase area") or " erased in " in n)]
                                    + _cleared_notes(jobs, tally, len(areas)))
                changed_members[member], notes = add_objects(raw, objects)
                notes = sunk + erased_notes + notes
            except KeyError:
                result.findings.append(Finding("error", f"{map_path.name} has no scenery file, so nothing can be "
                                                        f"placed on {name}"))
                continue
            except SceneryFull as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: {exc}" + (
                    ". The clearing along the new roads, under the new buildings and at the new bridges' ends counts "
                    "too: set clear = false on roads.toml roads that run through open ground" if cleared else "")))
                continue
            except (SceneryError, SceneryEditError) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: {exc}"))
                continue
            say(f"scenery: {name}, from {', '.join(ids)}")
            for note in notes:
                say(f"  {note}")
            if erased.get("building"):
                result.findings.append(Finding("warning", (
                    f"{', '.join(erase_ids)}: {name}: {erased['building']} of the map's buildings erased: the ground "
                    f"where they stood stays closed to units (the map's movement still has them). Leave buildings "
                    f"out of the erase areas' what, or expect units to go around where they were")))
            if erased.get("bridge"):
                result.findings.append(Finding("warning", (
                    f"{', '.join(erase_ids)}: {name}: {erased['bridge']} of the map's bridges erased: units can still "
                    f"cross the water where they stood (the map's movement still has the decks). Leave the bridges "
                    f"out of the erase areas' types, or place a bridge there again")))
            from .nav import solid_blocks
            walls, wall_notes = solid_blocks(game, [o for o in objects if not isinstance(o, RoadPiece)])
            for note in wall_notes:
                say(f"  {note}")
            if walls:
                solid[name] = (walls, ids)
            if entry is None:
                map_packs.append((map_path, map_arc, changed_members))
            result.terrain_changed[map_path.name] = changed_members
        for name, (map_roads, ids) in scenario_edits(result.order, mods, "roads").items():  # new roads painted
            from .bridges import cut
            decks = bridge_spans.get(name, []) + bridge_decks.get(name, [])
            lines = cut([r.points for r in map_roads if r.paint], decks)  # not on a bridge's deck
            map_path = find_pack(game, pack_file(name)) if lines else None
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
            from .groundpaint import PaintError, paint_roads
            from .scenery import MEMBER as SCENERY, SceneryError, Scenery
            try:
                pieces = Scenery(read_map(SCENERY)).roads() if read_map(SCENERY) else []
                painted, notes = paint_roads(read_map, lambda m, a=map_arc: a.find(m).path, lines, pieces)
            except (PaintError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the new roads can't be painted ({exc})"))
                continue
            changed_members.update(painted)
            say(f"roads painted: {name}, from {', '.join(ids)}")
            for note in notes:
                say(f"  {note}")
            if entry is None and painted:
                map_packs.append((map_path, map_arc, changed_members))
            if painted:
                result.terrain_changed[map_path.name] = changed_members
        data_packs = []  # (path, open pack, {member: new bytes}): DataMap_Win.dat, the scenarios and the cover grids
        moves, paints = scenario_edits(result.order, mods), scenario_edits(result.order, mods, "cover")
        blocks = scenario_edits(result.order, mods, "movement")
        new_roads = scenario_edits(result.order, mods, "roads")
        for name, (walls, ids) in list(solid.items()) + list(flooded.items()):  # placed buildings units go around,
            every, who = blocks.setdefault(name, ([], []))                    # and new water, after the mods' blocks
            every.extend(walls)
            who.extend(i for i in ids if i not in who)
        players = scenario_edits(result.order, mods, "players")
        if moves or paints or blocks or new_roads or bridge_spans or players:
            from .bridges import BridgeError, apply_spans
            from .cover import CoverError, apply_paints
            from .nav import NavError, apply_blocks, closing
            from .roadnet import RoadNetError, apply_roads
            from .scenario import PACK as SCENARIO_PACK, ScenarioError, apply_moves
            data_path = find_pack(game, SCENARIO_PACK)
            if data_path is None:
                result.findings.append(Finding("error", f"{SCENARIO_PACK} isn't in this game, so no starting point or "
                                                        f"spawn can be moved, and no cover painted"))
            else:
                data_arc = open_pack(data_path)
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
                for name, (map_moves, ids) in moves.items():
                    from .players import skirmish_files
                    from .scenario import Move, Spawn, spawn_class_problems
                    new_spawns = [m for m in map_moves if isinstance(m, Spawn)]
                    wrong = spawn_class_problems(name, new_spawns, registered_classes(), shipped_paths) if new_spawns else []
                    if wrong:  # a class the game can't find makes loading the map fail
                        result.findings += [Finding("error", f"{', '.join(ids)}: {w}") for w in wrong]
                        continue
                    unset = [m for m in map_moves if getattr(m, "z", 0.0) is None and (
                        not isinstance(m, Move) or m.kind in ("StartingPoint", "Spawn"))]
                    map_path = find_pack(game, pack_file(name)) if unset else None
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
                                                 warn=lambda msg, ids=ids: warn(f"{', '.join(ids)}: {msg}"))
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
                    for b, (wx, wy) in _wet_opens(open_pack, game, name, map_blocks, map_packs):
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
                if changed_members:
                    data_packs.append((data_path, data_arc, changed_members))
        if result.errors:
            for line in report_lines([f for f in result.findings if f.level == "error"], show_all=show_all):
                say(line)
            say("Nothing was written.")
            return result
        rmod_packs = run.changed_packs() if run else {}
        if map_packs or rmod_packs or data_packs:
            gameplay = {}
            for p, a in rmod_packs.items():
                where = f"Maps/PC/{p.name}/" if p.parent.parent.name.lower() == "maps" else ""
                gameplay.update({where + m: d for m, d in {**a.changed, **a.added}.items()})
            gameplay.update(result.changed)
            for map_path, _a, changed_members in map_packs:
                gameplay.update({f"Maps/PC/{map_path.name}/{m}": d for m, d in changed_members.items()})
            for data_path, _a, changed_members in data_packs:
                gameplay.update({f"{data_path.name}/{m}": d for m, d in changed_members.items()})
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
        for map_path, _a, changed_members in map_packs:
            say(f"changed: {map_path.name} ({len(changed_members)} file(s): "
                + ", ".join(m.rsplit(chr(92), 1)[-1] for m in changed_members) + ")")
        zz_win_changed = {**result.text_changed, **result.script_changed}
        for data_path, _a, changed_members in data_packs:
            say(f"changed: {data_path.name} ({len(changed_members)} file(s): "
                + ", ".join(m.rsplit(chr(92), 1)[-1] for m in changed_members) + ")")
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
            replace = {}
            for path, a, changed in rebuilt:
                rel = str(path.resolve().relative_to(Path(game).resolve()))
                replace[rel] = (lambda f, a=a, changed=changed: a.write_to(f, changed))
            copied = build_instance(str(game), str(instance), replace=replace)
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
