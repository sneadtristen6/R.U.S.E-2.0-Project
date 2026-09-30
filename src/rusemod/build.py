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

import re
import struct
import tomllib
import zlib
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from . import loc, pyscript
from .brush import BrushError, parse_strokes
from .edat import Edat
from .lock import fingerprint, fingerprint_text
from .model import ModelError, game_path, load, save
from .patch import Engine, Finding, Text, _walk_obj
from .resolve import ModInfo, ResolveError, load_order
from .rndf import parse
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
        info.scenario = read_scenario(path)
        info.cover = read_cover(path)
        _cover_brushes(info)
        info.movement = read_movement(path)
        _block_brushes(info)
        info.roads = _read_maps(path, "roads.toml")
    info.when_mods = {mid for op in ops for mid, _rng, _neg in op.when}
    return info, ops


_MAP_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def _map_readers() -> dict:
    """Each map file a mod may hold (maps/<map pack>/<file>): the tables it holds, how it says so, how its rows are
    read, and what its reader raises."""
    from .cover import CoverError, parse_paints
    from .nav import NavError, parse_blocks
    from .roadnet import RoadNetError, parse_roads
    from .scenario import ScenarioError, parse_moves, parse_spawns
    from .scenery import SceneryEditError, parse_objects
    return {
        "terrain.toml": (("stroke",), "a terrain file holds [[stroke]] tables",
                         lambda d, rel: parse_strokes(d.get("stroke", []), rel), BrushError),
        "scenery.toml": (("object",), "a scenery file holds [[object]] tables",
                         lambda d, rel: parse_objects(d.get("object", []), rel), SceneryEditError),
        # moves first: they name the shipped items by their number, which spawns (added at the end) don't shift
        "scenario.toml": (("move", "spawn"), "a scenario file holds [[move]] and [[spawn]] tables",
                          lambda d, rel: parse_moves(d.get("move", []), rel) + parse_spawns(d.get("spawn", []), rel),
                          ScenarioError),
        "cover.toml": (("paint",), "a cover file holds [[paint]] tables",
                       lambda d, rel: parse_paints(d.get("paint", []), rel), CoverError),
        "movement.toml": (("block",), "a movement file holds [[block]] tables",
                          lambda d, rel: parse_blocks(d.get("block", []), rel), NavError),
        "roads.toml": (("road",), "a roads file holds [[road]] tables",
                       lambda d, rel: parse_roads(d.get("road", []), rel), RoadNetError),
    }


MAP_FILES = ("terrain.toml", "scenery.toml", "scenario.toml", "cover.toml", "movement.toml", "roads.toml")


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
    """A mod's added scenery: {map pack name: [scenery.NewObject]} from maps/<map pack>/scenery.toml (MOD_FORMAT §8)."""
    return _read_maps(folder, "scenery.toml")


def _cover_brushes(info) -> None:
    """The Studio's cover and uncover brushes live in terrain.toml with the others, but paint the map's cover grid,
    not the ground: they move to `info.cover` (after the mod's own cover.toml circles), and a map whose strokes are
    all cover ones leaves the ground files alone."""
    from .cover import Paint
    for pack, strokes in list(info.terrain.items()):
        cover = [s for s in strokes if s.kind.kind == "cover"]
        if not cover:
            continue
        info.cover.setdefault(pack, []).extend(Paint(s.x, s.y, s.radius, "cover", s.kind.sign < 0) for s in cover)
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
    """The Studio's block brushes (terrain.toml) take ground away from units: they move to `info.movement` (after
    the mod's own movement.toml blocks), like the cover brushes to the cover grid."""
    from .nav import Block
    for pack, strokes in list(info.terrain.items()):
        blocks = [s for s in strokes if s.kind.kind == "block"]
        if not blocks:
            continue
        info.movement.setdefault(pack, []).extend(Block(s.x, s.y, s.radius, s.kind.shape) for s in blocks)
        rest = [s for s in strokes if s.kind.kind != "block"]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


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
    needs a class in the Python unit list, which lives there)."""
    return any(m.texts for m, _ in mods) or any(op.kind in ("create", "clone") for _, ops in mods for op in ops)


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
        changed = save(base, run.game, loaded, run.created, notes)
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
        map_packs = []  # (path, open pack, {member: new bytes})
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
            if changed_members:
                map_packs.append((map_path, map_arc, changed_members))
                result.terrain_changed[map_path.name] = changed_members
        # bridges where new roads cross water (rusemod.bridges): the map's own bridge kind placed along each
        # crossing (walk-through), and the crossing's deck kept for the movement graphs below
        # and bridges placed by hand (scenery.toml objects of a bridge kind, any size): coded as bridges, they open
        # their deck to units instead of blocking it, and a road crossing one gets no second bridge
        bridge_spans: dict = {}   # map pack name -> [(x0, y0, x1, y1)]
        bridge_objects: dict = {}  # map pack name -> (the bridge objects, the mods' ids)
        placed = scenery_edits(result.order, mods)
        road_edits = scenario_edits(result.order, mods, "roads")
        from .bridges import BridgeError, model_length, placed_spans, plan
        from .scenery import MEMBER as SCENERY, Scenery, SceneryError, descriptors, is_bridge
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
            by_hand = [o for o in objects_here if o.type in descs and is_bridge(descs[o.type].category)] if descs else []
            map_path = find_pack(game, pack_file(name)) if wanted or by_hand else None
            if map_path is None:
                continue  # (a missing map is said with the road network and the scenery below)
            ids = list(dict.fromkeys(road_ids + (object_ids if by_hand else [])))
            spans = placed_spans(by_hand, descs, length_of) if by_hand else []
            objects, notes = [], []
            if by_hand:
                notes.append(f"{len(by_hand)} bridge(s) placed by hand: movement opened along their decks")
            if wanted:
                entry = next((e for e in map_packs if e[0] == map_path), None)
                map_arc = entry[1] if entry else open_pack(map_path)
                done = entry[2] if entry else {}

                def read_map(member, a=map_arc, done=done):
                    try:
                        e = a.find(member)
                    except KeyError:
                        return None
                    return done.get(e.path) or bytes(a.read(e))
                try:
                    sc_raw, mesh = read_map(SCENERY), read_map("output\\highdef.tms")
                    if sc_raw is None or mesh is None:
                        raise BridgeError("the map has no scenery or no ground mesh")
                    objects, road_spans, road_notes = plan(mesh, wanted, Scenery(sc_raw), descs, length_of,
                                                           existing=spans)
                except (BridgeError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the roads' bridges can't be made ({exc})"))
                    continue
                spans += road_spans
                notes += road_notes
            if objects:
                bridge_objects[name] = (objects, road_ids)
            if spans:
                bridge_spans[name] = spans
            if notes:
                say(f"bridges: {name}, from {', '.join(ids)}")
                for note in notes:
                    say(f"  {note}")
        for name, (objects, ids) in bridge_objects.items():
            every, who = placed.setdefault(name, ([], []))
            every.extend(objects)
            who.extend(i for i in ids if i not in who)
        solid: dict = {}  # map pack name -> (nav.Block for each placed building, the mods' ids)
        for name, (objects, ids) in placed.items():
            map_path = find_pack(game, pack_file(name))
            if map_path is None:
                result.findings.append(Finding("error", f"{', '.join(ids)}: the map {name} isn't in this game "
                                                        f"({pack_file(name)} is missing), so nothing can be placed "
                                                        f"on it{_meant(game, name)}"))
                continue
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            changed_members = entry[2] if entry else {}
            from .scenery import MEMBER, SceneryEditError, SceneryError, add_objects
            try:
                member = map_arc.find(MEMBER).path
                raw = changed_members.get(member) or bytes(map_arc.read(map_arc.find(MEMBER)))
                changed_members[member], notes = add_objects(raw, objects)
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
            from .nav import solid_blocks
            walls, wall_notes = solid_blocks(game, objects)
            for note in wall_notes:
                say(f"  {note}")
            if walls:
                solid[name] = (walls, ids)
            if entry is None:
                map_packs.append((map_path, map_arc, changed_members))
            result.terrain_changed[map_path.name] = changed_members
        for name, (map_roads, ids) in scenario_edits(result.order, mods, "roads").items():  # new roads painted
            from .bridges import cut
            lines = cut([r.points for r in map_roads if r.paint], bridge_spans.get(name, []))  # not on a bridge's deck
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
        for name, (walls, ids) in solid.items():  # placed buildings units go around, after the mods' own blocks
            every, who = blocks.setdefault(name, ([], []))
            every.extend(walls)
            who.extend(i for i in ids if i not in who)
        if moves or paints or blocks or new_roads or bridge_spans:
            from .bridges import BridgeError, apply_spans
            from .cover import CoverError, apply_paints
            from .nav import NavError, apply_blocks
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
                for name, (map_moves, ids) in moves.items():
                    try:
                        new, notes = apply_moves(read_data, name, map_moves)
                    except (ScenarioError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"scenario: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                for name, (map_paints, ids) in paints.items():
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
                    try:
                        new, notes = apply_blocks(read_data, name, map_blocks)
                    except (NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"movement: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                for name, spans in bridge_spans.items():  # the bridges' decks opened to units, after the blocks
                    try:
                        new, notes = apply_spans(read_data, name, spans)
                    except (BridgeError, NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{name}: the bridges' movement can't be opened ({exc})"))
                        continue
                    changed_members.update(new)
                    say(f"bridges open: {name}")
                    for note in notes:
                        say(f"  {note}")
                for name, (map_roads, ids) in new_roads.items():  # the road network (buffer 0), after movement
                    try:
                        new, notes = apply_roads(read_data, name, map_roads)
                    except (RoadNetError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"roads: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
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
            if copied.get("full copies"):
                say(f"note: {instance} is on another drive than the game, so its {copied['full copies']} packs are "
                    f"full copies, which take disk space. On the game's drive they'd be free.")
    return result
