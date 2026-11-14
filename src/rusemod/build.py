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

import hashlib
import math
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
from .lock import fingerprint, fingerprint_text, looks_only_change
from .model import ModelError, collector_paused, game_path, load, save
from .patch import Engine, Finding, MapV, Num, Text, _walk_obj
from .visibility import SUFFIX as SEEN_SUFFIX
from .resolve import ModInfo, ResolveError, load_order
from .rndf import parse
from .spk import Spk, SpkError
from .steam import build_of, data_revisions
from .terrain_edit import edit_map, without_floor_notes

DEFAULT_PACK = "ZZ_GladPatchableWin.dat"  # the unit data

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# The game ships "_debuginfo" copies of a few data files that repeat every name of the main file. The game runs with
# them untouched (C2) or rewritten (C4); builds leave them exactly as shipped (PLAN.md §7, C4).
SHADOW = re.compile(r"_debuginfo\.cpp\.[a-z]*ndfbin$")
# PLAN.md decision 23: a mod never brings code that the game or the PC would run. The build only reads mod.toml,
# src/**/*.rndf and text/*.csv anyway; refusing these files outright keeps them from travelling with a mod at all.
# One exception, the owner's (2026-10-07, "allow a tool to edit mission scripts"): the game's own mission scripts as
# the Studio saves them, scripts/<map>/<part>/*.py and *.xyz (rusemod.mapscripts, MOD_FORMAT §9).
NOT_IN_MODS = {".py", ".pyc", ".pyo", ".pyw", ".pyd", ".xyz", ".ipk", ".exe", ".dll", ".com", ".scr", ".msi", ".bat",
               ".cmd", ".ps1", ".vbs", ".js", ".jar"}


class BuildError(Exception):
    pass


def load_mod(path, as_id: str | None = None) -> tuple[ModInfo, list]:
    """A mod folder (mod.toml + src/**/*.rndf, files in path order, + text/*.csv), or a single .rndf file as a quick
    mod. Text rows end up in `ModInfo.texts`. `as_id`: the id it is read under in place of its own, for a build that
    has another folder with the same id (rusemod.play.read_mods); its files are left as they are."""
    path = Path(path)
    if as_id is not None and not _ID.match(as_id):
        raise BuildError(f"{path}: {as_id!r} can't be a mod's id (lowercase letters, digits and '-')")
    if path.is_file() and path.suffix.lower() == ".rmod":  # a community mod as it comes (rusemod.rmod)
        from . import rmod
        mod = rmod.check(path)
        info = ModInfo(as_id or rmod.mod_id(mod, path), rmod.version_of(mod))
        info.rmod = path
        return info, []
    if path.is_file() and path.suffix.lower() == ".rndf":
        mod_id = as_id or re.sub(r"[^a-z0-9-]+", "-", path.stem.lower()).strip("-") or "mod"
        info = ModInfo(mod_id)
        ops = parse(path.read_text(encoding="utf-8"), file=path.name, mod=mod_id)
    else:
        manifest_file = path / "mod.toml"
        if not manifest_file.is_file():
            raise BuildError(f"{path} has no mod.toml (and isn't a .rndf file)")
        from .mapscripts import is_mod_script
        bad = sorted(rel for rel in (f.relative_to(path).as_posix() for f in path.rglob("*")
                                     if f.is_file() and f.suffix.lower() in NOT_IN_MODS)
                     if not is_mod_script(rel))  # the game's mission scripts a mod changes (§9): its only scripts
        if bad:
            more = ", …" if len(bad) > 5 else ""
            # not a game rule: what our format lets a mod bring (PLAN decision 23; mission scripts, the owner 2026-10-07)
            raise BuildError(f"{path}: mods can't contain scripts or programs ({', '.join(bad[:5])}{more}), apart "
                             f"from the game's mission scripts as the Studio saves them (scripts/<map>/<part>/, "
                             f".py and .xyz). The build writes the only other script changes a mod needs itself "
                             f"(decision 23).")
        try:
            manifest = tomllib.loads(manifest_file.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise BuildError(f"{manifest_file}: {exc}") from None
        m = manifest.get("mod", {})
        mod_id = m.get("id", "")
        if not _ID.match(mod_id):
            raise BuildError(f"{manifest_file}: [mod] id must be lowercase letters, digits and '-' (got {mod_id!r})")
        mod_id = as_id or mod_id
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
            if not (path / "src").is_dir() and not (path / "text").is_dir():
                return info, []
            # an .rmod mod converted for the Studio (rusemod.rmodconvert) has changes of its own too: read below,
            # built on top of every .rmod (build_and_write)
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
        _reliefs(info, path)
        info.scenery = read_scenery(path)
        _erase_areas(info)
        info.scenario = read_scenario(path)
        for name in ("places.toml", "items.toml"):  # new labels, points and zones (after the spawns), then the map's
            for pack, rows in _read_maps(path, name).items():  # own items changed: after its moves
                info.scenario.setdefault(pack, []).extend(rows)
        info.cover = read_cover(path)
        _cover_brushes(info)
        info.movement = read_movement(path)
        _block_brushes(info)
        _paint_brushes(info)
        _ground_pictures(info, path)
        _area_clips(info, path)
        info.roads = _read_maps(path, "roads.toml")
        _take_outs(info)
        info.players = _read_maps(path, "map.toml")
        _new_maps(info)
        from .menuorder import MenuOrderError, read_mod as menu_order_of
        try:
            info.menu_order = menu_order_of(path)  # menus.toml: missions' places in the menus
        except MenuOrderError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        from .menugroups import MenuGroupsError, read as menu_groups_of
        try:
            info.menu_groups = menu_groups_of(path)  # menu_groups.toml: each unit's group in its build list
        except MenuGroupsError as exc:
            raise BuildError(str(exc)) from None  # (its words name the file)
        from .scenario import ScenarioError, read_depots
        try:
            info.depots = read_depots(path)  # depots.toml: every depot's trucks, on every map or the ones named
        except ScenarioError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        from .unitlook import mod_cards, mod_textures
        from .unitmodel import UnitModelError, mod_copies, mod_models
        info.textures = mod_textures(path)
        info.cards = mod_cards(path)
        info.models = mod_models(path)
        try:
            info.model_copies = mod_copies(path)
        except UnitModelError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        from .squads import SquadError, mod_game_looks, mod_squads
        try:
            info.squads = mod_squads(path)  # files/models/<unit>.squad.toml: a squad's own number of soldiers
        except SquadError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        info.squad_game = mod_game_looks(path)  # files/models/<unit>@<i>.json alone: soldier i wears the game's look
        from .sceneryasset import AssetError, mod_assets
        try:
            info.assets = mod_assets(path)  # files/assets/<name>/asset.toml: its own rocks, props, plants, trees
            from .buildinglook import mod_looks
            info.looks = mod_looks(path)    # files/buildings/<name>/building.toml: its new buildings' own looks
        except AssetError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        from .sound import SoundError, mod_ambience, mod_new_songs, mod_sounds, mod_volumes, new_songs_rndf
        info.sounds = mod_sounds(path)
        try:
            info.volumes = mod_volumes(path)  # files/sound/volume.toml: how loud it plays each of the game's sounds
            from .anim import AnimError, mod_clips, mod_copies, mod_unit_clips
            try:
                info.clips = mod_clips(path)  # files/anim/clips.toml and files/replace/**/*.baf: its animations
                info.unit_clips = mod_unit_clips(path)  # files/anim/units.toml, files/anim/own: one unit's own
                info.anim_copies = mod_copies(path)  # files/anim/copies.toml: copies for the units ticked for each
            except AnimError as exc:
                raise SoundError(str(exc)) from None
            info.ambience = mod_ambience(path, mod_id)  # maps/<map>/background_<n>.wav and sound.toml
        except SoundError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        info.new_songs = mod_new_songs(path, mod_id)  # files/music/list<N>/<name>.wav: and the data they need
        if info.new_songs:
            ops += parse(new_songs_rndf(info.new_songs), file="files/music", mod=mod_id)
        from .solved import read_mod
        info.solved = read_mod(path)
        from . import mapscripts
        info.scripts = mapscripts.read_mod(path)
        from .mission import MissionError, read_mod as missions_of
        try:
            info.missions = missions_of(path)  # maps/<map>/mission.toml: a new Operation's or chapter's own mission
        except MissionError as exc:
            raise BuildError(f"{mod_id}: {exc}") from None
        from .gamefiles import GameFileError, read_mod as game_files_of
        try:
            info.game_files = game_files_of(path, info.id)
        except GameFileError as exc:
            raise BuildError(f"{path.name}: {exc}") from None
    info.when_mods = {mid for op in ops for mid, _rng, _neg in op.when}
    return info, ops


_MAP_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def _map_readers() -> dict:
    """Each map file a mod may hold (maps/<map pack>/<file>): the tables it holds, how it says so, how its rows are
    read, and what its reader raises."""
    from .cover import CoverError, parse_paints
    from .menupicture import PictureError
    from .nav import NavError, parse_blocks
    from .newmap import NewMapError
    from .players import PlayersError
    from .roadnet import RoadNetError, parse_roads, parse_take_out
    from .scenario import (ScenarioError, parse_changes, parse_moves, parse_places, parse_removes, parse_spawns,
                           parse_starts)
    from .scenery import (SceneryEditError, parse_cliffs, parse_copies, parse_erase, parse_field_brushes,
                          parse_field_copies, parse_objects, parse_own, parse_presets, parse_sections)
    from .sectors import SectorError, parse_sectors
    return {
        "terrain.toml": (("stroke",), "a terrain file holds [[stroke]] tables",
                         lambda d, rel: parse_strokes(d.get("stroke", []), rel), BrushError),
        "scenery.toml": (("object", "erase", "copy", "preset", "fieldbrush", "fieldcopy", "own", "cliffs", "section"),
                         "a scenery file holds [[object]], [[erase]], [[copy]], [[preset]], [[fieldbrush]], "
                         "[[fieldcopy]], [[own]], [[cliffs]] and [[section]] tables",
                         # an [[own]] row (the map's own object moved or taken away) is an erase of that one object
                         # and, when it's moved, the object placed again (scenery.OwnEdit.expand)
                         lambda d, rel: (parse_objects(d.get("object", []), rel) + parse_erase(d.get("erase", []), rel)
                                         + [x for e in parse_own(d.get("own", []), rel) for x in e.expand()]
                                         + parse_copies(d.get("copy", []), rel)
                                         + parse_presets(d.get("preset", []), rel)
                                         + parse_field_brushes(d.get("fieldbrush", []), rel)
                                         + parse_field_copies(d.get("fieldcopy", []), rel)
                                         + parse_cliffs(d.get("cliffs", []), rel)
                                         + parse_sections(d.get("section", []), rel)),
                         SceneryEditError),
        # moves and removes first: they name the shipped items by their number, which starts and spawns (added at
        # the end) don't shift, and a removed item keeps its place; the sectors' setting last (rusemod.sectors)
        "scenario.toml": (("move", "remove", "start", "spawn", "sectors"),
                          "a scenario file holds [[move]], [[remove]], [[start]] and [[spawn]] tables and [sectors]",
                          lambda d, rel: (parse_moves(d.get("move", []), rel) + parse_removes(d.get("remove", []), rel)
                                          + parse_starts(d.get("start", []), rel)
                                          + parse_spawns(d.get("spawn", []), rel)
                                          + parse_sectors(d.get("sectors"), rel)),
                          (ScenarioError, SectorError)),
        # new town and hill names, named points and zones: added after the scenario.toml edits (load_mod)
        "places.toml": (("place",), "a places file holds [[place]] tables",
                        lambda d, rel: parse_places(d.get("place", []), rel), ScenarioError),
        # the map's own items with some of their values changed (a depot's trucks, a spawn's side, a zone's size, a
        # name): applied after the scenario.toml and places.toml edits (load_mod puts them last)
        "items.toml": (("set",), "an items file holds [[set]] tables",
                       lambda d, rel: parse_changes(d.get("set", []), rel), ScenarioError),
        "cover.toml": (("paint",), "a cover file holds [[paint]] tables",
                       lambda d, rel: parse_paints(d.get("paint", []), rel), CoverError),
        "movement.toml": (("block", "open"), "a movement file holds [[block]] and [[open]] tables",
                          lambda d, rel: (parse_blocks(d.get("block", []), rel)
                                          + parse_blocks(d.get("open", []), rel, "open")), NavError),
        "roads.toml": (("road", "take_out"), "a roads file holds [[road]] tables and take_out = [\"roads\", \"bridges\"]",
                       lambda d, rel: parse_roads(d.get("road", []), rel) + parse_take_out(d.get("take_out"), rel),
                       RoadNetError),
        "map.toml": (("players", "entry", "copy_of", "name", "picture", "wide_picture", "start_dots", "ground",
                      "blank", "size", "clouds", "room"),
                     "a map file holds players = N (and entry = the map-list name), picture, wide_picture and "
                     "start_dots, and for a new map copy_of, name, ground and blank (and for a blank one size, "
                     "clouds and room)",
                     _map_toml, (PlayersError, NewMapError, PictureError)),
    }


def _map_toml(data: dict, rel: str) -> list:
    """A map.toml's rows: a new map (newmap.NewMap) when it says copy_of, else a shipped map's own menu pictures
    (menupicture.MenuPictures) when it names any, and its players (players.Players). On a new map, `entry` picks the
    shipped map's entry to copy, and players = N applies to the copy; on a shipped map it picks the entry that gets
    the players or the pictures."""
    from .menupicture import MenuPictures, picture_names, start_dots_of
    from .newmap import parse
    from .players import parse_map
    parts = rel.replace("\\", "/").split("/")
    made = parse(data, rel, parts[-2] if len(parts) > 1 else "")
    if not made:
        picture, wide = picture_names(data, rel)
        dots = start_dots_of(data, rel, wide)
        if picture or wide:
            made = [MenuPictures(picture, wide, data.get("entry"), dots)]
            if "players" not in data:  # the entry is the pictures'
                data = {k: v for k, v in data.items() if k != "entry"}
    rest = {k: v for k, v in data.items() if not (made and k == "entry" and not isinstance(made[0], MenuPictures))}
    return made + parse_map(rest, rel)


MAP_FILES = ("terrain.toml", "scenery.toml", "scenario.toml", "places.toml", "items.toml", "cover.toml", "movement.toml",
             "roads.toml", "map.toml")


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
        rows = parse_rows(data, rel)
    except mistake as exc:
        raise BuildError(str(exc)) from None
    for r in rows:  # a map's own menu pictures: the PNGs beside its map.toml, read with the mod
        for key in ("picture", "wide_picture"):
            name = getattr(r, key, None)
            if name and getattr(r, key + "_data", 1) is None:
                pic = f.parent / name
                if not pic.is_file():
                    raise BuildError(f"{rel}: {key} = {name!r}, but maps/{f.parent.name}/ has no such picture")
                setattr(r, key + "_data", pic.read_bytes())
    return rows


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
    """The erase areas of a mod's scenery.toml files go to `info.erase` and its copies to `info.copy`; its objects stay
    in `info.scenery`. A preset area ([[preset]]) becomes its tiles' copies, its erase (replace mode) and its ground
    picture stamps (into `info.paint`, laid OVER the terrain file's own paint strokes: _paint_brushes puts those
    under them, as the field brush's picture goes over the mods' paint; scenery.expand_preset). The
    field brush's dabs ([[fieldbrush]]) go to `info.fields`: they read the map's own fields, so the build expands
    them where it reads the map's scenery (scenery.expand_field_brush). The cliff areas ([[cliffs]]) go to
    `info.cliffs`: laid on the ground as built (rusemod.cliffs); the sections ([[section]]) to `info.sections`: read
    from the map's scenery as it comes in, placed by references (scenery.add_sections)."""
    from .scenery import (CliffArea, CopyArea, EraseArea, FieldBrush, FieldCopy, PresetArea, SectionArea,
                          border_library, expand_preset, hedgerow_library, preset_library)
    lib = borders = hedgerows = None
    for pack, rows in list(info.scenery.items()):
        moved = False
        for kind, into in ((CliffArea, info.cliffs), (SectionArea, info.sections)):
            mine = [r for r in rows if isinstance(r, kind)]
            if mine:
                into[pack] = mine
                rows = [r for r in rows if not isinstance(r, kind)]
                moved = True
        if moved:
            if not rows:
                del info.scenery[pack]
                continue
            info.scenery[pack] = rows
        dabs = [r for r in rows if isinstance(r, (FieldBrush, FieldCopy))]   # (and the field copies: they read the
        if dabs:                                                             # map's own fields too)
            info.fields[pack] = dabs
            rows = [r for r in rows if not isinstance(r, (FieldBrush, FieldCopy))]
            if not rows:
                del info.scenery[pack]
                continue
            info.scenery[pack] = rows
        presets = [r for r in rows if isinstance(r, PresetArea)]
        if presets:
            if lib is None:
                lib, borders, hedgerows = preset_library(), border_library(), hedgerow_library()
            rows = [r for r in rows if not isinstance(r, PresetArea)]
            for k, p in enumerate(presets, 1):
                # its own group: its tiles (and border strips) don't thin each other
                copies, erases, stamps, objects = expand_preset(p, lib, group=k, borders=borders, hedgerows=hedgerows)
                # the area's erase before its tiles, as the build applies them; a field's hedgerow trees and fence
                # are placed objects like a [[object]] row's
                rows = rows + erases + copies + objects
                if stamps:
                    info.paint.setdefault(pack, []).extend(stamps)
        areas = [r for r in rows if isinstance(r, EraseArea)]
        copies = [r for r in rows if isinstance(r, CopyArea)]
        if not areas and not copies:
            if presets:
                info.scenery[pack] = rows
            continue
        if areas:
            info.erase[pack] = areas
        if copies:
            info.copy[pack] = copies
        rest = [r for r in rows if not isinstance(r, (EraseArea, CopyArea))]
        if rest:
            info.scenery[pack] = rest
        else:
            del info.scenery[pack]


def _take_outs(info) -> None:
    """A roads.toml's take_out (roadnet.TakeOut: the map's own roads and bridges taken out) goes to `info.take_out`;
    its roads stay in `info.roads`."""
    from .roadnet import TakeOut
    for pack, rows in list(info.roads.items()):
        taken = [r for r in rows if isinstance(r, TakeOut)]
        if not taken:
            continue
        info.take_out[pack] = taken
        rest = [r for r in rows if not isinstance(r, TakeOut)]
        if rest:
            info.roads[pack] = rest
        else:
            del info.roads[pack]


def _new_maps(info) -> None:
    """The new maps of a mod's map.toml files (copy_of) go to `info.new_maps`, and a shipped map's own menu pictures
    to `info.menu_pictures`; their player counts stay in `info.players`."""
    from .menupicture import MenuPictures
    from .newmap import NewMap
    for kind, into in ((NewMap, info.new_maps), (MenuPictures, info.menu_pictures)):
        for pack, rows in list(info.players.items()):
            made = [r for r in rows if isinstance(r, kind)]
            if not made:
                continue
            into[pack] = made
            rest = [r for r in rows if not isinstance(r, kind)]
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
                                                  for s in blocks for x, y, r in s.footprint().circles(
                                                      _block_cell(s.footprint())))
        rest = [s for s in strokes if s.kind.kind not in moving]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


def _paint_brushes(info) -> None:
    """The Studio's Map Paint brushes (paint, stamp, texture) live in terrain.toml with the others, but change the
    ground's picture, not its shape: they move to `info.paint` in their order, like the cover brushes to the cover
    grid, under the preset areas' picture stamps (a Blank Terrain coat over the whole map hid a preset field's ground
    from afar, where its crops aren't drawn: the palette test 10-16). A repaint stroke goes to `info.repaint`:
    the build paints what the ground brushes moved by its new shape (rusemod.repaint), under the mod's own paint."""
    from .brush import PAINT_KINDS
    for pack, strokes in list(info.terrain.items()):
        paint = [s for s in strokes if s.kind.kind in PAINT_KINDS]
        repaint = [s for s in strokes if s.kind.kind == "repaint"]
        if not paint and not repaint:
            continue
        if paint:   # under the preset areas' picture stamps (_erase_areas put them in first): a whole-map coat
            info.paint[pack] = paint + info.paint.get(pack, [])   # mustn't hide a preset field's ground
        if repaint:
            info.repaint.setdefault(pack, []).extend(repaint)
        rest = [s for s in strokes if s.kind.kind not in PAINT_KINDS and s.kind.kind != "repaint"]
        if rest:
            info.terrain[pack] = rest
        else:
            del info.terrain[pack]


def _reliefs(info, path: Path) -> None:
    """A relief stroke's heightmap read into it (rusemod.relief: files/terrain/<relief>.png), and its picture
    (<relief>-ground.png, when there) listed in `info.relief_pictures` to lay on the ground; a heightmap that isn't
    there, or doesn't read, is an error that says where it should be."""
    from dataclasses import replace
    from .relief import TERRAIN, ReliefError, files_of, read_grid
    for pack, strokes in info.terrain.items():
        out = []
        for s in strokes:
            if s.kind.kind == "relief":
                heights, picture = files_of(path, s.relief)
                if not heights.is_file():
                    raise BuildError(f"{info.id}: maps/{pack}/terrain.toml lays the heightmap {s.relief}.png, which "
                                     f"isn't in the mod's {TERRAIN.as_posix()} folder")
                try:
                    s = replace(s, grid=read_grid(heights.read_bytes()))
                except ReliefError as exc:
                    raise BuildError(f"{info.id}: {TERRAIN.as_posix()}/{s.relief}.png: {exc}") from None
                if picture.is_file():
                    info.relief_pictures.setdefault(pack, []).append((s, picture))
            out.append(s)
        info.terrain[pack] = out


def _area_clips(info, path: Path) -> None:
    """A paint stroke `within` a relief's area (`<relief>:<area>`: a real place's field, wood or marsh,
    rusemod.realplace) given its clip: the cells of that relief's area picture (files/terrain/<relief>-areas.png) holding
    that number, over the box the stroke reaches (rusemod.relief.area_clip). The relief must be one of the same map's
    strokes in this mod; a picture that isn't there, or doesn't read, is an error that says where it should be."""
    from dataclasses import replace
    from .relief import TERRAIN, ReliefError, area_clip, areas_file, read_areas
    read: dict = {}   # (pack, relief) -> (its stroke, its area picture)
    for pack, strokes in info.paint.items():
        if not any(s.within for s in strokes):
            continue
        reliefs = {s.relief: s for s in info.terrain.get(pack, []) if s.kind.kind == "relief"}
        out = []
        for s in strokes:
            if s.within:
                name, area = s.within.rsplit(":", 1)
                if (pack, name) not in read:
                    if name not in reliefs:
                        raise BuildError(f"{info.id}: maps/{pack}/terrain.toml paints within relief {name!r}, which "
                                         f"isn't one of that map's relief strokes in the mod")
                    file = areas_file(path, name)
                    if not file.is_file():
                        raise BuildError(f"{info.id}: maps/{pack}/terrain.toml paints within relief {name!r}'s areas, "
                                         f"but {file.name} isn't in the mod's {TERRAIN.as_posix()} folder")
                    try:
                        read[pack, name] = (reliefs[name], read_areas(file.read_bytes()))
                    except ReliefError as exc:
                        raise BuildError(f"{info.id}: {TERRAIN.as_posix()}/{file.name}: {exc}") from None
                relief, areas = read[pack, name]
                try:
                    s = replace(s, clip=area_clip(relief, areas, int(area), s.box()))
                except ReliefError as exc:
                    raise BuildError(f"{info.id}: maps/{pack}/terrain.toml: {exc}") from None
            out.append(s)
        info.paint[pack] = out


def _ground_pictures(info, path: Path) -> None:
    """The mod's own pictures its texture strokes lay (texture = "file:<name>.png": files/ground/<name>.png), named
    with the mod (file:<mod id>/<name>.png) so two mods' pictures of one name stay apart; one that isn't there is an
    error that says where it should be."""
    from dataclasses import replace
    from .groundtex import GROUND
    for pack, strokes in info.paint.items():
        out = []
        for s in strokes:
            if s.kind.kind == "texture" and s.texture.startswith("file:"):
                name = s.texture[5:]
                file = path / GROUND / name
                if not file.is_file():
                    raise BuildError(f"{info.id}: maps/{pack}/terrain.toml paints with the picture {name}, which "
                                     f"isn't in the mod's {GROUND.as_posix()} folder")
                key = f"file:{info.id}/{name}"
                info.ground_pictures[key] = file
                s = replace(s, texture=key)
            out.append(s)
        info.paint[pack] = out


BED_RADII = (3840.0, 2560.0, 1920.0, 1280.0)  # down to nav.MIN_RADIUS: a new movement circle fits in one of these
BED_MOST = 81600.0  # the widest zone over a wide dried bed (nav.water_blocks's `wide`): 255 nav.STEPs. The shipped
                    # maps' own circles go up to 135,040 (M04_Cotentin), and 81,600 is on that map twice
BLOCK_SIDE = 64     # a square block or open goes in as at most this many cells along its side: a bigger square gets
                    # bigger cells (a whole-map erase on M04_Cotentin made 13 million circles and ran out of memory,
                    # 2026-10-05), never a circle wider than BED_MOST


def _block_cell(f) -> float:
    """The cell size a footprint's circles are laid on (brush.Footprint.circles): BLOCK_CELL, bigger for a square
    with more than BLOCK_SIDE of those along its side, never so big that a circle is wider than BED_MOST."""
    return min(max(BLOCK_CELL, 2.0 * f.r / BLOCK_SIDE), BED_MOST * math.sqrt(2.0))


def cleared_woods(erasing: dict) -> tuple[dict, dict]:
    """For each map's erase areas that take trees or buildings ({map: (areas, ids)}): (opens of that ground to every
    unit, the forest cover taken away where trees went), each {map: (list, ids)}. With its trees gone the ground is no
    wood any more, but the map's movement still keeps vehicles off it and its cover still hides infantry there (a
    D-Day test, 2026-10-01: tanks couldn't drive into a cleared wood). Buildings the same: a town's movement closes
    whole blocks (houses, yards, walls: 1,108 of the 1,156 building pieces of Blitz's town by its first starting
    point), so the area opens whole; each house's own ground alone opens next to nothing (islands no unit reaches,
    checked in memory on T25's spots). Seen in the game 2026-10-04 (TESTS.md T25): tanks and infantry drive through
    where Blitz's town stood, and infantry there no longer act as in a town. Erasing only props leaves both, and so
    does a new road's own clearing (keep_ground).

    The blocked layer goes too, under trees and buildings alike: the maps mark their towns' buildings blocked, and
    where an erased town stood (everywhere on Blank Terrain, which erases the whole map) tanks saw the enemy and
    didn't fire (seen in T41 run 1, 2026-10-09); with the blocked layer taken out with them, they fired (T41 run 2)."""
    from .cover import Paint
    from .nav import Block
    opens, uncover = {}, {}
    for name, (areas, ids) in erasing.items():
        cleared = [a for a in areas if ("vegetation" in a.what or "building" in a.what) and not a.keep_ground]
        woods = [a for a in cleared if "vegetation" in a.what]
        # one of the map's own buildings moved or taken away ([[own]]): its own ground, as far as it reaches
        single = [a for a in areas if a.opens and a not in cleared]
        if cleared or single:
            # a square or a line opens as circles covering it (the movement graphs are circles), and uncovers itself
            opens[name] = ([Block(x, y, r, "all", True) for a in cleared
                            for x, y, r in a.footprint().circles(_block_cell(a.footprint()))]
                           + [Block(a.x, a.y, a.opens, "all", True) for a in single], list(ids))
            uncover[name] = ([Paint(a.x, a.y, a.radius, "cover", True, False, a.shape, a.dx, a.dy, a.x2, a.y2)
                              for a in woods]
                             + [Paint(a.x, a.y, a.radius, "blocked", True, False, a.shape, a.dx, a.dy, a.x2, a.y2)
                                for a in cleared]
                             + [Paint(a.x, a.y, a.opens, "blocked", True, False) for a in single], list(ids))
    return opens, uncover


def _asset_shapes(own_assets: dict, types: set, kept: dict) -> dict:
    """{type: rusemod.cliffs.Shape} of the mods' own map assets among `types` (their models read once: `kept`), at the
    asset's own size: what a [[cliffs]] area lays them by."""
    from .cliffs import shape_of
    from .modelin import read_model
    from .sceneryasset import _arrays, type_name
    for name, (asset, _mod) in own_assets.items():
        t = type_name(name)
        if t in types and t not in kept:
            pos, _n, _uv, tri, _mat = _arrays(read_model(asset.model))
            kept[t] = shape_of(pos * asset.size, tri)
    return {t: kept[t] for t in types if t in kept}


GROUND_GAP = 64.0  # map units (a quarter metre): a model starting higher than this above its base point is lowered


def grounded(objects: list, descs: dict, lowest_of) -> tuple[list, int]:
    """(the placed objects, each standing on the ground; how many were lowered). The game puts an object's base point
    on the ground and scales its model from there, so a model that starts above its base point floats by that much
    times its size: an upper storey meant to sit on its ground floor (TownHouseC_Haut starts 4.7 m up) placed alone,
    or any such piece made bigger (the owner's 10x houses floated about 47 m up, 2026-10-01). Such an object is sunk
    (its `lift`) so its lowest point sits on the ground. `lowest_of(type)` gives the model's lowest point in map
    units (None when unknown). Bridges keep their own sink, road pieces aren't objects, and an object laid as the map
    lays it (a [[copy]]'s: NewObject.levels) keeps the height its shipped copy has."""
    from dataclasses import replace
    from .scenery import NewObject
    out, moved = [], 0
    for o in objects:
        d = descs.get(o.type) if isinstance(o, NewObject) and not o.levels else None
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


def _bed_circles(drained: list[tuple[float, float]], wet=None, wide=None) -> list[tuple[float, float, float]]:
    """Open zones (x, y, r) over a dried bed's samples (nav.water_blocks), for Graph.open_ground, which puts each new
    circle inside one zone and none smaller than nav.MIN_RADIUS: so each zone is one of BED_RADII, centred on a sample
    no zone holds yet, the largest whose middle and rim (8 points) aren't under water now (`wet(x, y)`; the ends of a
    bed meet the water left). A bed too narrow for the smallest stays closed.

    A zone holds no sample as far away as the largest radius, so each sample is looked at against the zones in its
    square of that side and the 8 round it only: the same zones as looking at all of them (a map drained across
    kilometres has a hundred thousand).

    `wide`: water_blocks's zones over the wide stretches (up to BED_MOST), which come first: a sample inside one needs
    no zone of its own. A sea drained (the owner's M04_Cotentin, 2026-10-04: 255,466 samples) is then 2,790 zones,
    which the map's movement holds; as zones of BED_RADII alone it was 255,117, a hundred times what it holds."""
    zones: list[tuple[float, float, float]] = []
    side = max(BED_RADII)
    near: dict[tuple[int, int], list[tuple[float, float, float]]] = {}
    wide = list(wide or [])
    over: dict[tuple[int, int], list[tuple[float, float, float]]] = {}  # the wide zones, by where their middles are
    for zone in wide:
        over.setdefault((int(zone[0] // BED_MOST), int(zone[1] // BED_MOST)), []).append(zone)

    def dry(x, y, r) -> bool:
        return wet is None or not any(wet(x + r * c, y + r * s) for c, s in
                                      ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (.7, .7), (.7, -.7), (-.7, .7), (-.7, -.7)))
    for x, y in sorted(drained):
        if over:
            a, b = int(x // BED_MOST), int(y // BED_MOST)
            if any((x - zx) ** 2 + (y - zy) ** 2 < zr * zr
                   for da in (-1, 0, 1) for db in (-1, 0, 1) for zx, zy, zr in over.get((a + da, b + db), ())):
                continue
        i, j = int(x // side), int(y // side)
        if any((x - zx) ** 2 + (y - zy) ** 2 < (zr * 0.7) ** 2
               for di in (-1, 0, 1) for dj in (-1, 0, 1) for zx, zy, zr in near.get((i + di, j + dj), ())):
            continue
        r = next((r for r in BED_RADII if dry(x, y, r)), None)
        if r is not None:
            zones.append((x, y, r))
            near.setdefault((i, j), []).append((x, y, r))
    return wide + zones


def _kept_movement(read_data, name: str, blocks: list, idle: list, cache, given: dict | None = None,
                   answers: dict | None = None, ahead=None) -> tuple[dict, list[str]]:
    """nav.apply_blocks for a map, its answer kept between builds (rusemod.mapkeep, kind "movement"): named by
    _movement_key (what the step reads of the movement file, its blocks and opens in their order, the answers given,
    the kept movement's format number: rusemod.keptformat), the new graphs kept and put back into the movement file as
    the build has it then. A map whose blocks and opens are the same as an earlier build's takes its movement from
    there: opening a drained sea takes minutes (the owner's M04_Cotentin, 2026-10-04), and every build made it again.
    A refusal isn't kept.
    `given`: the answers the mods brought for this map (rusemod.solved), taken where they hold; `answers` is filled
    with the ones this map's movement asked for (taken and worked out): what an export carries. `ahead`: the step
    started earlier (nav.Ahead, _movement_ahead), taken when it was asked the same."""
    from . import mapkeep, solved
    from .cover import member
    from .nav import apply_blocks, replace_buffers
    from ruse_mod_engine import sdb
    win = read_data(member(name))
    k = _movement_key(cache, name, win, blocks, given)
    kept = mapkeep.read(cache, k, "movement")
    if kept is not None and isinstance(kept.get("notes"), list) and isinstance(kept.get("idle"), list) \
            and all(type(i) is int and 0 <= i < len(blocks) for i in kept["idle"]) \
            and isinstance(kept.get("solved"), dict) \
            and all(i in (1, 2) and isinstance(b, bytes) for i, b in kept["members"].items()):
        if ahead is not None:
            ahead.close()
        idle += [blocks[i] for i in kept["idle"]]
        if answers is not None:
            answers.update(kept["solved"])
        return {member(name): replace_buffers(win, kept["members"])}, list(kept["notes"])
    mine: list = []
    store = solved.Solved(given)
    with solved.using(store):
        new, notes = apply_blocks(read_data, name, blocks, mine, ahead=ahead)
    idle += mine
    if answers is not None:
        answers.update(store.needed())
    places = {id(b): i for i, b in enumerate(blocks)}
    made = sdb.split_mapinfo(new[member(name)])[1]
    mapkeep.write(cache, k, {"members": {1: made[1], 2: made[2]}, "notes": list(notes),  # (its two new graphs)
                             "idle": [places[id(b)] for b in mine], "solved": store.needed()}, "movement")
    return new, notes


def _movement_key(cache, name: str, win: bytes | None, blocks: list, given: dict | None) -> str | None:
    """The build cache's name for a map's movement (rusemod.mapkeep, kind "movement"): a fingerprint of what the
    movement step reads of the movement file (its road network and its two graphs, not the cover grid the cover step
    may have changed before), its blocks and opens in their order, the answers given, and its format number
    (rusemod.keptformat). None without a cache or a movement file."""
    import hashlib
    from . import mapkeep, solved
    from ruse_mod_engine import sdb
    if cache is None or win is None:
        return None
    parts = sdb.split_mapinfo(win)
    if not parts:
        return None
    h = hashlib.blake2b(digest_size=20)
    for b in parts[1][:3]:
        h.update(len(b).to_bytes(8, "little") + b)
    about = ["movement graphs", h.hexdigest()]
    return mapkeep.key(name, about + ([solved.digest(given)] if given else []), blocks, None, "movement")


def _movement_ahead(game: Path, open_pack, order: list, mods: list, cache, erasing: dict, beds: dict, flooded: dict,
                    solid: dict, data_base, data_new: dict) -> dict:
    """{map pack name: nav.Ahead}: the movement step of each big map, started in worker programs now, before the
    ground is painted, with the blocks and opens the build will give it then (the mods' own, cleared woods, dried
    beds, new water, placed buildings: as build_and_write puts them together) and the answers the mods brought. The
    movement step takes the answer only when it is asked exactly that (nav.Ahead.fits); a map whose movement is in
    the build cache isn't started. On a PC with one or two cores, nothing is started."""
    from .nav import PARALLEL_FROM, Ahead, NavError
    from .cover import member
    from .scenario import PACK as MOVEMENT_PACK
    if (os.cpu_count() or 1) <= 2:
        return {}
    data_path = find_pack(game, MOVEMENT_PACK)
    if data_path is None:
        return {}
    blocks = scenario_edits(order, mods, "movement")
    cleared, _uncover = cleared_woods(erasing)
    for name, (walls, ids) in (list(cleared.items()) + list(beds.items()) + list(flooded.items())
                               + list(solid.items())):
        every, who = blocks.setdefault(name, ([], []))
        every.extend(walls)
        who.extend(i for i in ids if i not in who)
    out = {}
    if not any(len(b) >= PARALLEL_FROM for b, _ids in blocks.values()):
        return out
    from .newmap import Grown
    arc = Grown(data_base, data_new) if data_new else open_pack(data_path)
    for name, (map_blocks, _ids) in blocks.items():
        if len(map_blocks) < PARALLEL_FROM:
            continue
        try:
            win = bytes(arc.read(arc.find(member(name))))
        except KeyError:
            continue
        given, _unused = _given_answers(order, mods, name, win)
        from . import mapkeep
        if mapkeep.read(cache, _movement_key(cache, name, win, map_blocks, given), "movement") is not None:
            continue
        try:
            out[name] = Ahead(win, map_blocks, given)
        except (NavError, ValueError, struct.error):
            continue
    return out


def _given_answers(order: list, mods: list, name: str, shipped: bytes | None) -> tuple[dict, list[str]]:
    """(the answers the mods brought for a map, notes): each mod's maps/<map>/solved.bin (rusemod.solved) opened with
    the game's own movement file for the map, as shipped. A file that doesn't open (made on another version of the
    game, or changed) is left out with a note: the build works its answers out instead."""
    from . import solved
    by_id = {m.id: m for m, _ in mods}
    given: dict = {}
    notes = []
    for mod_id in order:
        data = getattr(by_id.get(mod_id), "solved", {}).get(name)
        if data is None:
            continue
        try:
            if shipped is None:
                # not a game rule: our own lock (rusemod.solved) needs the map's movement file as its key
                raise solved.SolvedError("the game has no movement file for this map")
            given.update(solved.unpack(data, shipped))
        except solved.SolvedError as exc:
            notes.append(f"{mod_id}: the worked-out answers that came with the mod for {name} weren't used ({exc}): "
                         f"the build works them out here instead, which takes longer")
    return given, notes


def _wet_opens(open_pack, game: Path, name: str, blocks, map_packs, find_map=None, thin=()) -> list:
    """nav.wet_opens for a map's opens, on its ground as the terrain edits left it (map_packs: (pack path, archive,
    changed members); `open_pack(path)` opens a map pack, `find_map(name)` finds it, a new map's too); none when the
    map has no opens or its ground can't be read. `blocks`: the map's blocks and opens in the order they apply
    (_open_runs). `thin`: water strokes units go under (block = false): their place counts as dry, and so does a
    place a later block closes to every unit (new water's own blocks come after every open: a Blank Terrain map's
    opens over a real place's sea, 2026-10-18, 116 warnings of nothing)."""
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
        water = Water(Tms(ground))
        out = []
        for opens, later in _open_runs(blocks):
            if not thin and not later:
                out += wet_opens(opens, water.at, many=water.at_many)
                continue
            closed = _closing(later)

            def dry(x, y, closed=closed):
                return closed(x, y) or any(s.covers(x, y) for s in thin)
            out += wet_opens(opens, lambda x, y, dry=dry: water.at(x, y) and not dry(x, y),
                             many=lambda xs, ys, dry=dry: [w and not dry(x, y)
                                                           for w, x, y in zip(water.at_many(xs, ys), xs, ys)])
        return out
    except (KeyError, ValueError, struct.error, zlib.error):
        return []


def _open_runs(blocks) -> list:
    """`blocks` (in the order they apply: the later one wins) as runs of the opens drawn (not spare: the build's own
    over a dried bed keep off the water), each with the blocks after it that close the ground to every unit."""
    runs, run = [], []
    for k, b in enumerate(blocks):
        if b.open:
            if not b.spare:
                run.append(b)
        elif run:
            runs.append((run, k))
            run = []
    if run:
        runs.append((run, len(blocks)))
    return [(run, [c for c in blocks[k:] if not c.open and c.units == "all"]) for run, k in runs]


def _closing(closes):
    """`at(x, y)`: whether one of `closes` (blocks) covers (x, y); looked up by squares as wide as the widest."""
    if not closes:
        return lambda x, y: False
    cell = max(c.radius for c in closes) or 1.0
    grid: dict = {}
    for c in closes:
        for i in range(int((c.x - c.radius) // cell), int((c.x + c.radius) // cell) + 1):
            for j in range(int((c.y - c.radius) // cell), int((c.y + c.radius) // cell) + 1):
                grid.setdefault((i, j), []).append(c)

    def at(x, y):
        return any((x - c.x) ** 2 + (y - c.y) ** 2 < c.radius ** 2
                   for c in grid.get((int(x // cell), int(y // cell)), ()))
    return at


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
    sound_changed: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (a sound, a sound bank) -> bytes
    close_up_maps: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (a map's close-up map copy) -> bytes
    new_classes: list = field(default_factory=list)  # class names added to the game's Python unit list
    terrain_changed: dict = field(default_factory=dict)  # map pack file name -> {member path: new bytes}
    new_maps: dict = field(default_factory=dict)    # new map's pack name -> newmap.Clone (what it adds)
    mission_scripts: dict = field(default_factory=dict)  # new members of IA_Common.dat: the new maps' own missions
    mission_packs: list = field(default_factory=list)    # [(entry GUID, kind, own pack GUID)]: missions' own packs
    mission_sources: dict = field(default_factory=dict)  # new map's pack name -> its mission script as Python
    added: dict = field(default_factory=dict)       # pack file name -> {member path: bytes}: members new maps add
    own_cards: dict = field(default_factory=dict)   # new units' cards: card member to add -> (its source's, the PNG)
    own_models: dict = field(default_factory=dict)  # new units' models: unit -> (its source's model, the .glb, mod id)
    own_copies: dict = field(default_factory=dict)  # units' own model copies: unit -> ({model: copy}, paint, mod id)
    own_clips: dict = field(default_factory=dict)   # units' own clips: new member of ZZ_Win.dat -> how it's made
    # (unit_own_clips; rusemod.anim.own_clip_files makes them)
    own_rides: dict = field(default_factory=dict)   # units riding as themselves on long moves: unit -> its ride
    # (unit_own_clips plans it, unit_own_rides makes it)
    own_assets: dict = field(default_factory=dict)  # mods' map assets: name -> (sceneryasset.Asset, mod id)
    own_looks: dict = field(default_factory=dict)   # new buildings' looks: building -> (buildinglook.Look, mod id)
    look_symbols: dict = field(default_factory=dict)  # new buildings' looks: building -> (the symbol it copies, its own)
    model_imports: dict = field(default_factory=dict)  # member path in ZZ_Win.dat (packs the new models go in) -> bytes
    new_files: dict = field(default_factory=dict)  # new members of ZZ_Win.dat (new cards, new models' textures) -> bytes
    visibility: dict = field(default_factory=dict)  # a placed type drawn up close only -> its copy (rusemod.visibility)
    type_levels: dict = field(default_factory=dict)  # a placed type -> the draw tree's levels it's drawn at (its objects
    # ask them of the blocks they hang on: rusemod.visibility.type_levels)
    solved: dict = field(default_factory=dict)  # map pack name -> its answers, a locked file (rusemod.solved)
    own_kinds: list = field(default_factory=list)  # the kinds of the buildings with units of their own (ownbuildings)
    # the game patches the modded copy needs (rusemod.gamepatch's names: a copy can need more-buildings AND own-squads),
    # each once; big-packs is added when the packs are written wide (build_and_write)
    game_patch: list = field(default_factory=list)
    wide_packs: list = field(default_factory=list)  # the packs written wide, past 4 GiB (the big-packs game patch)
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


def load_pack(arc: Edat, cache=None) -> PackModel:
    """The data files of `arc` as the engine's model, the way builds see them (debug-info copies left out). `cache`:
    a folder where the model is kept for the next build of the same files (model.load)."""
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
    base, loaded = load(files, cache)
    return PackModel(base, loaded, members, shadows)


def needs_zz_win(mods: list) -> bool:
    """Whether building `mods` [(ModInfo, ops)] needs ZZ_Win.dat: some mod adds texts or a new map (its name in the
    menus), changes a map's menu pictures, repaints a texture or replaces a sound (files/replace, rusemod.unitlook,
    rusemod.sound), adds map assets or building looks (their models go there: rusemod.sceneryasset), or new objects
    (a new unit needs a class in the Python unit list, which lives there), or moves a unit to another nation or model
    (the skirmish mesh packs there say whether its models are loaded for it: unit_models), or puts a unit in a group
    of a build list (menu_groups.toml: the menu script there gets the lines template, menu_lines), or gives a unit
    animations of its own (files/anim/units.toml, or a copy of a clip ticked for it in files/anim/copies.toml: their
    clips go there, rusemod.anim)."""
    return any(m.texts or m.new_maps or getattr(m, "menu_pictures", None) or getattr(m, "textures", None)
               or getattr(m, "sounds", None) or getattr(m, "new_songs", None) or getattr(m, "ambience", None)
               or getattr(m, "volumes", None) or getattr(m, "clips", None) or getattr(m, "unit_clips", None)
               or getattr(m, "anim_copies", None)
               or getattr(m, "assets", None) or getattr(m, "looks", None) or getattr(m, "menu_groups", None)
               for m, _ in mods) or \
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


UNIT_CARDS = "baseunite"   # the game's dictionary of its units' names on their cards (rusemod.bugwatch.CARD_NAMES)


def _unit_cards(zz_win):
    """card(obj) -> a unit's name on its card, in English, from ZZ_Win.dat as the mods leave it (`zz_win`), or None;
    the dictionary read once, when first asked."""
    from .dic import Dic, name_to_key
    from .patch import Text
    got: dict = {}

    def card(obj):
        if "dic" not in got:
            got["dic"] = None
            try:
                e = zz_win.entry(loc.member(UNIT_CARDS, "us")) if zz_win is not None else None
                got["dic"] = Dic(bytes(zz_win.read(e))) if e is not None else None
            except (OSError, ValueError, KeyError, IndexError, struct.error):
                got["dic"] = None
        v = obj.props.get("NameInMenuToken")
        if got["dic"] is None or not isinstance(v, Text) or v.kind != "key":
            return None
        try:
            key = int(v.value, 16) if v.value.lower().startswith("0x") else name_to_key(v.value)
        except ValueError:
            return None
        said = " ".join((got["dic"].text(key) or "").split())
        return said or None
    return card


def _readable(name: str) -> str:
    """A unit's name in the data as a name to read: $/GFX/Everything/Descriptor_Unit_Battleship_FR -> Battleship FR."""
    short = re.sub(r"^(?:Descriptor_)?(?:Unit_)?", "", str(name).replace("\\", "/").rsplit("/", 1)[-1])
    return " ".join(short.replace("_", " ").split()) or str(name)


def unit_models(base, run, zz_win, result: BuildResult, into=None, names=None, allowed=None, who=None) -> bool:
    """New units, and units moved to another nation or given other models, whose models are only in another nation's
    skirmish mesh pack: the game loads a nation's unit models only in matches where a player has that nation
    (unitcheck). So that nation's packs (meshes, proxies, animations, skeletons, card pictures) load in every skirmish
    (FORCE_LOAD), with a note; a unit whose nation's packs no loader has is refused, saying why. What the game's own
    units already have is fine. (FORCE_LOAD off, the old way: the models are copied into the skirmish packs of the
    unit's own nation, rusemod.unitpacks; `into`, a unitpacks.Packs, gathers them for the build, else they go straight
    into result.model_changed.) Returns whether a unit needed another nation's models (the game was changed for it, or
    it was refused).

    `names`, `allowed`, `who`: for the units .rmod mods make or move (rmod_unit_models), which are already in the data
    the build reads: the units to look at (in place of the run's own new and moved ones), the (model, nation) pairs
    the game's own units have as shipped (in place of `base`'s), and {unit: the mods that change it, said first}."""
    if names is None:
        moved = {owner for owner, path in run.trail if owner in run.game.objects and _moves_path(path)}
        names = sorted(n for n in set(run.created) | moved
                       if n in run.game.objects and unitcheck.is_unit(run.game.objects[n]))
        names = [n for n in names if unitcheck.model_files(run.game.objects[n], run.game)]
    if not names or zz_win is None:
        return False
    packs = skirmish_models(zz_win)
    if packs is None:
        result.findings.append(Finding("note", "ZZ_Win.dat has no skirmish mesh packs, so whether the new or moved "
                                               "units' models load for their nation wasn't checked"))
        return False
    allowed = unitcheck.allowed_models(base) if allowed is None else allowed
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
        return False

    def said_at(unit, op) -> str:
        """Where a unit's finding starts: its mod's file and line, or the .rmod mods changing it."""
        if op:
            return f"{op.at()}: "
        return f"{', '.join(who[unit])}: " if who and who.get(unit) else ""

    cards = _unit_cards(zz_win) if who is not None else None

    def said_name(unit) -> str:
        """A unit as its finding names it: its name, or for one a .rmod mod made with no name of its own (file#n), its
        class's name; a unit an .rmod mod makes or moves (no mod file of ours to point at: a player reads it) by its
        name on its card, else its name made readable (the review of 95e9b910, 2026-11-14)."""
        obj = run.game.objects[unit]
        cls = getattr(obj.props.get("ClassNameForDebug"), "value", None)
        if who is None:
            return unit
        if cards is not None and wanted_op.get(unit) is None:
            card = cards(obj)
            if card:
                return card
            return _readable(cls if "#" in unit and isinstance(cls, str) and cls else unit)
        return cls if "#" in unit and isinstance(cls, str) and cls else unit
    wanted_op = {unit: op for unit, op, _missing, _need in wanted}
    if not FORCE_LOAD:
        own = into is None
        into = into or unitpacks.Packs(zz_win)
        for unit, op, missing, need in wanted:
            obj, name = run.game.objects[unit], said_name(unit)
            n = unitcheck.nation_of(obj)
            nation, tag = unitcheck.NATIONS[n], unitpacks.TAGS[n]
            model, where = next(iter(missing.items()))
            more = f" (and {len(missing) - 1} more)" if len(missing) > 1 else ""
            at = said_at(unit, op)
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
        return True
    loaded = unitcheck.load_everywhere(run.game, chosen)
    _also_loaded(run, [n for n in chosen if loaded[n][0]], result)
    for nation, (count, maps) in sorted(loaded.items()):
        if count:
            result.findings.append(Finding("note", f"{unitcheck.NATIONS[nation]}'s unit models and animations now load "
                                                   f"in every skirmish, beside those of the nations playing, for the "
                                                   f"units of other nations that use them ({count} loaders in {maps} "
                                                   f"cluster maps; matches take a little more memory and loading time)"))
    for unit, op, missing, need in wanted:
        obj, name = run.game.objects[unit], said_name(unit)
        n = unitcheck.nation_of(obj)
        nation = unitcheck.NATIONS[n]
        model, where = next(iter(missing.items()))
        more = f" (and {len(missing) - 1} more)" if len(missing) > 1 else ""
        at = said_at(unit, op)
        packs_of = " and ".join(unitcheck.NATIONS[i] for i in need)
        plain = who is not None and op is None   # (an .rmod mod's unit: said to a player, with no code names)
        if all(loaded[i][0] for i in need):
            if plain:
                result.findings.append(Finding("note", f"{at}{name}, in {nation}'s army, has a model of "
                                                       f"{' and '.join(where)}'s units: {packs_of}'s unit models now "
                                                       f"load in every skirmish, so it shows in matches where no player "
                                                       f"has {packs_of} too"))
                continue
            result.findings.append(Finding("note", f"{at}{name} is in {nation}'s army (Nationalite {n}), but its model "
                                                   f"{model}{more} is in the mesh pack of {' and '.join(where)}'s units: "
                                                   f"{packs_of}'s unit models now load in every skirmish, so it shows "
                                                   f"in matches where no player has {packs_of} too", op))
            continue
        if plain:
            # rule: nation-models
            result.findings.append(Finding("error", f"{at}{name}, in {nation}'s army, has a model only "
                                                    f"{' and '.join(where)}'s units have, and the unit data has no cluster "
                                                    f"maps that could load {packs_of}'s models in every match: in matches "
                                                    f"where no player has {packs_of}, this unit would have no model, or "
                                                    f"crash the game"))
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
    return True


def rmod_unit_models(run, shipped, zz_win, result: BuildResult, rmods=(), base=None, into=None) -> bool:
    """unit_models for the units a set of .rmod mods makes, moves to another nation or gives other models (the owner,
    2026-11-13, item 29: "Sets made only of .rmod mods skip the unit-model check: (A) run it" -> "A"). Those mods
    change the game's files themselves, so their units are already in the data the build reads (`run`, an engine run
    over it): each unit is set against the game's own unit data as shipped (`shipped`, its engine model), and a unit
    the game hasn't, or has with another nation or other models, is looked at as a mod's new or moved unit is; what the
    game's own units have as shipped is fine. `zz_win()` gives ZZ_Win.dat as the mods leave it, opened only when a unit
    is looked at; `rmods`: the .rmod files of the set, to say which changes a unit. Returns whether the game was
    changed for one (or one was refused).

    In a set with mods of ours too (build_pack: `base`, the unit data as the .rmod mods left it, and `run`, our mods
    run over it; `into` as unit_models'), the .rmod mods' units are looked at the same way, and our mods' new and moved
    units with them, each said with its mod's file and line: the game's own units as shipped are what's fine for all
    of them, so a unit an .rmod mod made is never taken for the game's own (the review of 95e9b910, 2026-11-14: in a
    set with any folder mod the .rmod mods' units were never looked at)."""
    own = {n: (unitcheck.nation_of(o), frozenset(unitcheck.model_files(o, shipped)))
           for n, o in shipped.objects.items() if unitcheck.is_unit(o)}
    names = []
    for n, o in run.game.objects.items():
        if not unitcheck.is_unit(o):
            continue
        files = frozenset(unitcheck.model_files(o, run.game))
        if files and own.get(n) != (unitcheck.nation_of(o), files):
            names.append(n)
    if not names:
        return False
    from .rmod import edits_of
    who: dict = {}   # unit -> the .rmod mods whose changes name its class (his engine's name for a unit it changes)
    edits = [e for e in (edits_of(path) for path in rmods) if e is not None]
    for n in names:
        cls = getattr(run.game.objects[n].props.get("ClassNameForDebug"), "value", None)
        if not isinstance(cls, str) or not cls:
            continue
        mine = f"ClassNameForDebug={cls}"
        # the mods that make it, or set its nation or its models, are the ones the finding is about; a mod that only
        # changes its other values (every test copy's cheat mod re-prices most units) isn't named for it (the review
        # of 95e9b910, its fault 3's kind); when none of them does (a model changed through another object, which
        # these edits can't tell), every mod changing the unit is named, as before
        moved = [e.name for e in edits
                 if any(k[3] == cls for k in e.creates) or any(mine in k[3].split(";") and _moves_path(str(k[4]))
                                                               for k in e.values)]
        said = moved or [e.name for e in edits if any(mine in k[3].split(";") for k in e.values)]
        if said:
            who[n] = list(dict.fromkeys(said))
    return unit_models(shipped if base is None else base, run, zz_win(), result, into, names=sorted(names),
                       allowed=unitcheck.allowed_models(shipped), who=who)


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


def mission_models(run, zz_win, mods: list, order: list[str], result: BuildResult) -> None:
    """The units a new map's own mission makes (maps/<map>/mission.toml: an event's spawn), and the nations its sides
    are given. A mission is played as an Operation or a campaign chapter, never as a skirmish, and loads only the
    nations of the mission it copies (most Operations: the six of the game as first sold; a chapter: the two to five
    it plays; Japan in almost none). A unit of another nation made there has no model and no skeleton, and the game
    stops when it is made: the build said nothing (a mission spawning Japanese units built with 0 errors, 2026-11-10;
    players' games stopped in the game's model code with mods of their own on, which is this family; the same stop a
    scenario's spawns gave on 2026-10-01). So a nation the copied map doesn't load in all its missions gets its packs
    loaded in campaign chapters and Operations, and its skeletons and card pictures with every nation's, as for a unit
    given another nation's models (_also_loaded), with the same notes."""
    try:
        made = new_maps(order, mods)
    except BuildError:
        return  # two mods make one map: build_and_write says so as a mistake, and nothing is written
    by_class: dict | None = None
    in_packs = None
    wanted: set[int] = set()
    for m, _ops in mods:
        for map_name, found in (getattr(m, "missions", None) or {}).items():
            mission = found[0] if isinstance(found, tuple) else found
            nations: set[int] = set()
            for side in getattr(mission, "sides", None) or []:
                if side.nation in unitcheck.NATIONS:
                    nations.add(unitcheck.NATIONS.index(side.nation))
            for event in getattr(mission, "events", None) or []:
                for action in event.actions:
                    if action.do != "spawn" or not action.unit:
                        continue
                    if by_class is None:
                        by_class = {}
                        for name, obj in run.game.objects.items():
                            cls = getattr(obj.props.get("ClassNameForDebug"), "value", None) \
                                if unitcheck.is_unit(obj) else None
                            if cls:
                                by_class.setdefault(cls, name)
                        in_packs = skirmish_models(zz_win) if zz_win is not None else None
                    name = by_class.get(action.unit)
                    if name is None:
                        continue  # (not a unit of this build: the mission's own check says so)
                    obj = run.game.objects[name]
                    nations.add(unitcheck.nation_of(obj))
                    for model in unitcheck.model_files(obj, run.game) if in_packs else ():
                        if model not in in_packs["common"]:  # a unit wearing another nation's model needs that one
                            nations |= {i for i, tag in enumerate(unitcheck.PACK_TAGS) if model in in_packs[tag]}
            spec = next((s for n, (s, _id) in made.items() if n.lower() == map_name.lower()), None)
            loads = unitcheck.mission_nation_bits(run.game, spec.copy_of) if spec is not None else []
            # a nation every mission of the copied map loads needs nothing; no word on the map: every nation is asked
            wanted |= {n for n in nations if 0 <= n < len(unitcheck.NATIONS)
                       and not (loads and all(bits >> n & 1 for bits in loads))}
    if wanted:
        _also_loaded(run, sorted(wanted), result)


def far_upgrades(run, result: BuildResult) -> None:
    """An upgrade (IsUpgrade 1) of a unit made in ANOTHER building becomes a research of its own, and the build says so
    (the owner, 2026-11-10, after playing two library mods together: "it shouldn't be taken away before the new
    one's researched ... I feel like that kind of is a new fault", then "Yes, do that" to this rule). One mod had
    moved a light tank to the Barracks and given it an upgrade there; another had made a tank of the Armor Base its
    upgrade. The game takes a unit out of its list the moment ANY upgrade of it is researched, so researching the
    Armor Base's tank took the light tank out of the Barracks, its own upgrade there not researched yet; and the
    build list of the Armor Base stops the game when an upgrade's card finds no card of its unit in it (two
    players' reports; rusemod.scriptguards keeps the game going there). Neither mod is wrong alone. EVERY unit of
    the build is looked at, whichever mod set its values, .rmod mods included (unitcheck.cut_far_upgrades). Research
    from another building's unit WITHOUT the upgrade flag, as the Studio's board writes it, is left as it is: that
    unit stayed buildable after the research in the game (2026-10-18). Runs before the menu lines and groups, so they
    see the research where the game will show it: on its own, as the game as sold has the T-34."""
    game = run.game

    def called(name: str) -> str:
        obj = game.objects.get(name)
        cls = getattr(obj.props.get("ClassNameForDebug"), "value", None) if obj is not None else None
        return cls if isinstance(cls, str) and cls else name

    def made_in(name: str) -> str:
        kind = unitcheck._int(game.objects[name].props.get(unitcheck.FACTORY))
        return BUILDING_NAMES.get(kind, f"building {kind}")

    for name, parent in unitcheck.cut_far_upgrades(game):
        # rule: unit-far-upgrade
        result.findings.append(Finding("warning", f"{called(name)} ({made_in(name)}) was an upgrade of "
                                                  f"{called(parent)} ({made_in(parent)}): the game takes a unit out "
                                                  f"of its list as soon as any upgrade of it is researched, in "
                                                  f"whatever building, so it is now a research of its own"))


def rmod_far_upgrades(arc: Edat, build_id: str, cache, result: BuildResult, models=None) -> None:
    """far_upgrades for a set of .rmod mods ONLY, the set most players have: those mods change the game's files
    themselves and build_pack never runs, so nothing of ours would look at the unit data they leave (the two mods
    of the owner's test were both .rmod mods). The unit data as they left it (`arc`) is read, and written again
    only when a far upgrade was cut. With none, `result` is not touched: the copy's files, its fingerprint and its
    join code are what they were before this step existed, so players on the release before still match.

    `models` (the owner, 2026-11-13, item 29, answer A): (the unit data pack as the game ships it, zz_win() giving
    ZZ_Win.dat as the mods leave it, the set's .rmod files): when the mods changed the unit data pack, the units they
    make or move get the unit-model check too (rmod_unit_models). A unit that needs another nation's models has that
    nation's packs load everywhere, as a folder mod's unit has, written with any far upgrade's cut, or it is refused;
    with neither a cut nor such a unit, `result` is still not touched (notes aside)."""
    pack = load_pack(arc, cache)
    run = Engine(pack.base).run([])
    found = BuildResult()
    far_upgrades(run, found)
    looked = False
    if models is not None and (getattr(arc, "changed", None) or getattr(arc, "added", None)):
        shipped, zz_win, rmod_files = models
        looked = rmod_unit_models(run, load_pack(shipped, cache).base, zz_win, found, rmod_files)
    if found.errors or not (looked or any(f.level == "warning" for f in found.findings)):
        result.findings += found.findings   # (refused, or notes only: nothing to write)
        return
    notes: list = []
    try:
        changed = save(pack.base, run.game, pack.loaded, run.created, notes,
                       **({"new_props": {(unitcheck.LOADER, unitcheck.FORCE)}} if looked else {}))
    except ModelError as exc:
        # not a game rule: the unit data these mods left can't be written again by our writer
        result.findings.append(Finding("error", str(exc)))
        return
    result.findings += found.findings + [Finding("note", n) for n in notes]
    result.changed = {pack.members[p]: data for p, data in changed.items()}
    result.fingerprint = fingerprint(build_id, changed)
    result.model_changed.update(found.model_changed)   # (FORCE_LOAD off, the old way: the models' copies)


def fill_loc(game, keys: dict) -> list[str]:
    """Turn every loc('...') value into the game key its text got. Returns the loc keys no mod defines."""
    missing = []
    for name, obj in list(game.objects.items()):
        if not any(isinstance(v, Text) and v.kind == "loc" for v in _walk_obj(obj)):
            continue
        for v in _walk_obj(game.own(name)):  # (changed in the game's own copy of the object: patch.Game.own)
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
        tex.obj.props["FileName"] = Text("path", new)  # (a copy the engine made: not the shipped game's object)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets its own card, {new} (files/cards/{unit}.png), "
                                               f"made from {file.value}'s"))
    return out


def unit_own_models(run, order: list, result: BuildResult) -> dict:
    """New units' own models (a mod's files/models/<the unit's name>.glb; rusemod.unitmodel): the clone's model part
    names a model of its own, beside its source's, which the build writes into the packs that hold the source's.
    Returns {unit: (its source's model, the .glb, mod id)}."""
    from .squads import soldier_of
    from .unitmodel import glb_report, model_key
    wanted: dict = {}
    for m in order:
        for stem, glb in (getattr(m, "models", None) or {}).items():
            wanted[stem] = (glb, m.id)
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    # a model file for one kind of a squad's soldiers (<unit>@<kind>.glb: its bazooka man) takes the place of the game
    # model those soldiers drew; the unit's main file never takes that model too (an older Studio's main file named
    # every soldier model of the squad: it still does when no kind has a file of its own, so its mod builds as before).
    # One soldier's own look (<unit>@<i>.glb, rusemod.squads) claims nothing: he alone wears it (squad_soldiers)
    claimed: dict = {}
    for stem, (glb, _mod) in wanted.items():
        unit, _, kind = stem.partition("@")
        like = glb_report(glb).get("like") if kind and soldier_of(stem) is None else None
        if like:
            claimed.setdefault(unit, set()).add(model_key(like))
    out: dict = {}
    for stem, (glb, mod_id) in sorted(wanted.items()):
        unit, _, kind = stem.partition("@")
        where = f"{mod_id}: files/models/{stem}.glb"
        report = glb_report(glb)
        rigged_on = report.get("like") if report.get("rigged") else None
        also = list(report.get("also") or [])
        soldier = soldier_of(stem)
        if soldier is not None:
            # one soldier's own look: his model is written beside the one he was fitted to (the figure the game gives
            # his place draws it), and no figure of the unit is pointed at it here: squad_soldiers gives him a figure
            # of his own, so the squad's other soldiers keep theirs
            if not rigged_on:
                # not a game rule: a soldier's own look is a model on his bones (what the Studio's import writes)
                result.findings.append(Finding("error", f"{where}: the model of {unit}'s soldier {soldier[1]} must be "
                                                        f"fitted to his bones (import it again in the Studio)"))
                continue
            if unit not in by_name:
                # not a game rule: a model for a unit no mod in the set makes
                result.findings.append(Finding("error", f"{where}: no mod in the set makes a new unit {unit}"))
                continue
            out[stem] = (rigged_on, glb, mod_id)
            continue
        if kind and not rigged_on:
            # not a game rule: a kind's own file is a soldier's model, on bones (what the Studio's import writes)
            result.findings.append(Finding("error", f"{where}: a model for {unit}'s {kind} must be fitted to his bones "
                                                    f"(import it again in the Studio)"))
            continue
        if kind:
            also = []
        elif rigged_on:
            taken = claimed.get(unit, set())
            mine = [m for m in [rigged_on, *also] if model_key(m) not in taken]
            if not mine:
                result.findings.append(Finding("warning", f"{where}: every soldier of {unit} has a model of his own "
                                                          f"file, so this one draws none of them"))
                continue
            rigged_on, also = mine[0], mine[1:]
        source = _own_model_part(run, by_name, unit, where, result, rigged_on, also, own_stem=_own_stem(stem))
        if source is None:
            continue
        if not kind:
            _own_propeller_list(run, by_name[unit], unit, glb, where, result)
        out[stem] = (source, glb, mod_id)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets its own model (files/models/{stem}.glb), "
                                               f"beside {source}"))
    # a squad whose soldiers have looks of their own: its far-away figure wears the riflemen's (_far_figure_riflemen);
    # one whose soldiers have looks one by one, the look most of them wear (squad_soldiers decides it)
    by_soldier = {_unit_of(stem) for stem in out if soldier_of(stem) is not None}
    for unit in sorted({stem.partition("@")[0] for stem in out}):
        if unit in by_name and unit not in by_soldier:
            _far_figure_riflemen(run, by_name[unit], unit, out, result)
    return out


# a squad's riflemen's figure (the game's GfxDescriptorFusilier: every man but the last), its model part
RIFLEMEN = ("GfxDescriptorFusilier", "MeshDescriptor")


def _far_figure_riflemen(run, name: str, unit: str, out: dict, result: BuildResult) -> None:
    """A new squad whose soldiers have looks of their own (unit_own_models' `out`: files/models/<unit>.glb for its
    riflemen, <unit>@<kind>.glb for its bazooka man): its far-away figure (FIGURINE) wears its riflemen's look, the most
    soldiers of the squad. The owner, 2026-11-11, on squad-page1 (only the bazooka man painted red): far away "they're
    red ... It should take that like the more predominant unit ... up close, it should be just the red bazooka guy".
    The game draws the G.I. squad's far-away figure with its bazooka man, so before this a bazooka man of his own lent
    the squad his look far away, and riflemen of their own left the game's bazooka man there. The riflemen's look: their
    own model when they have one (written beside the game model it was fitted to, as _own_model_part names it), else
    the game model their figure draws. A unit with no riflemen's figure (not a squad) is left as it is."""
    from .unitmodel import model_key
    obj = run.game.objects[name]
    far = _figurine_model(run, obj)
    if far is None:
        return
    if unit in out:
        fitted = out[unit][0].replace("/", "\\")
        riflemen = f"{fitted.rsplit(chr(92), 1)[0]}\\{_own_stem(unit)}lod0.Ase2ndfbin"
    else:
        riflemen = _part_model(run, obj, RIFLEMEN)
    if riflemen is None or model_key(riflemen) == model_key(far):
        return
    if _point_at_copies(run, name, {model_key(far): riflemen}, parts=lambda p: p == FIGURINE[0]):
        result.findings.append(Finding("note", f"{unit}'s far-away figure wears its riflemen's look "
                                               f"({riflemen.replace(chr(92), '/').rsplit('/', 1)[-1]})"))


def squad_soldiers(base, run, order: list, result: BuildResult) -> None:
    """New squads with soldiers of their own (rusemod.squads): files/models/<unit>.squad.toml, the squad's own number of
    soldiers, and files/models/<unit>@<i>.glb, soldier i's own look (in result.own_models, written beside the model it
    was fitted to as any own model), or <unit>@<i>.json alone, soldier i wearing the game's look (rusemod.squads.
    write_game_look). Such a squad gets R2Behaviour, its own copy of the game's one setting for every squad as the mods
    leave it, only its number of soldiers its own; and R2SoldierLooks, one entry per soldier, soldier 1 first: none (he
    wears what the game gives his place), a copy of the figure the game gives his place drawing his own model, or one
    drawing the game's model (_game_figure; none when his place's figure draws it already). Its far-away figure wears
    the look most of its soldiers wear (_far_figure_most), and the modded copy gets the own-squads game patch. Refused,
    said: a number below FEWEST or above MOST (the owner's picks 1 and 2, 2026-11-12), or below the squad's weapons its
    last soldiers fire one each (NeedModelChange: the game gives the first to the last soldier, the next to the one
    before him); a look for a soldier the squad hasn't got; a unit no mod makes, or that isn't a squad. A squad with none
    of these files, or whose only one says a soldier wears the game's look his place's figure draws already, and every
    game squad, is left exactly as it was. Runs after the units' own models, clips, halves and rides (each soldier's
    figure is a copy of the squad's as it then stands)."""
    from decimal import Decimal

    from . import squads as sq
    from .patch import Inline, ListV, Ref, _fresh
    from .unitmodel import model_key
    wanted: dict = {}
    for m in order:
        for unit, count in (getattr(m, "squads", None) or {}).items():
            wanted[unit] = (count, m.id)
    looks: dict = {}   # unit -> {soldier: (the model his look was fitted to, mod id, his file's stem)}
    for stem, (source, _glb, mod_id) in result.own_models.items():
        soldier = sq.soldier_of(stem)
        if soldier is not None:
            looks.setdefault(soldier[0], {})[soldier[1]] = (source, mod_id, stem)
    plain: dict = {}   # unit -> {soldier: mod id}: soldiers who wear the game's look (rusemod.squads.write_game_look)
    for m in order:
        for unit, numbers in (getattr(m, "squad_game", None) or {}).items():
            for i in numbers:
                plain.setdefault(unit, {})[i] = m.id
    if not wanted and not looks and not plain:
        return
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    shared = run.game.objects.get(sq.BEHAVIOUR)
    shared_count = shared.props.get(sq.COUNT) if shared is not None else None
    shared_n = int(shared_count.value) if isinstance(shared_count, Num) else None
    done = []
    for unit in sorted(set(wanted) | set(looks) | set(plain)):
        count, mod_id = wanted.get(unit, (None, None))
        soldiers = looks.get(unit, {})
        games = plain.get(unit, {})
        mod_id = mod_id or (next(iter(soldiers.values()))[1] if soldiers else next(iter(games.values())))
        where = f"{mod_id}: files/models/{unit}{sq.SUFFIX}" if unit in wanted else f"{mod_id}: files/models/{unit}"
        name = by_name.get(unit)
        if name is None:
            # not a game rule: a squad's file for a unit no mod in the set makes
            result.findings.append(Finding("error", f"{where}: no mod in the set makes a new unit {unit}"))
            continue
        if run.game.objects[name].cls != sq.SQUAD_CLASS:
            # not a game rule: the own-squads game patch gives soldiers of their own to squads alone (their class)
            result.findings.append(Finding("error", f"{where}: {unit} isn't a squad of soldiers, so it can't have "
                                                    f"soldiers of its own"))
            continue
        need, fired = _squad_need(run, run.game.objects[name])
        if count is not None:
            if count < sq.FEWEST:
                # the game's rule (its setting makes any number below 2 a 2 as it loads) and the owner's pick 1
                # rule: squad-fewest-two
                result.findings.append(Finding("error", f"{where}: {unit} would have {count} soldiers: a squad keeps at "
                                                        f"least {sq.FEWEST}, the game's own rule"))
                continue
            if count > sq.MOST:
                # not a game rule: the owner's pick 2 (2026-11-12), "Most soldiers for now: 8, with the first test at 7"
                result.findings.append(Finding("error", f"{where}: {unit} would have {count} soldiers: a squad has at "
                                                        f"most {sq.MOST} for now"))
                continue
            if count < need:
                # the game's rule: each of these weapons goes to one soldier, from the last one back
                result.findings.append(Finding("error", f"{where}: {unit} would have {count} soldiers, but its last "
                                                        f"soldiers fire {need} weapons one each ({', '.join(fired)}): "
                                                        f"it needs at least {need}"))
                continue
        n = count if count is not None else shared_n
        if n is None or (count is not None and shared_n is None):
            # not a game rule: the game's own setting, as our build reads the unit data
            result.findings.append(Finding("error", f"{where}: the game's number of soldiers in a squad "
                                                    f"({sq.BEHAVIOUR}) can't be read, so {unit}'s soldiers can't be "
                                                    f"counted"))
            continue
        past = [i for i in sorted(soldiers) if i > n]
        for i in past:
            # not a game rule: a look for a soldier the squad hasn't got (a file left after the squad got fewer)
            result.findings.append(Finding("error", f"{soldiers[i][1]}: files/models/{soldiers[i][2]}.glb: {unit} has "
                                                    f"{n} soldiers, so there is no soldier {i} to wear this look"))
        past_game = [i for i in sorted(games) if i > n]
        for i in past_game:
            # not a game rule: the same, for a soldier who'd wear the game's look
            result.findings.append(Finding("error", f"{games[i]}: files/models/{sq.soldier_stem(unit, i)}.json: {unit} "
                                                    f"has {n} soldiers, so there is no soldier {i} to wear the game's "
                                                    f"look"))
        if past or past_game:
            continue
        # each soldier's look fitted to a model the copied unit's soldiers wear (the Studio fits it to his place's: a
        # file made otherwise, fitted to another unit's model, is refused, as a kind's is)
        op = run.created.get(name)
        copied = base.objects.get(op.source) if op is not None and op.kind == "clone" else None
        worn = {model_key(m) for m in (_mesh_file(run, _figure_of(run, copied, p)) if copied is not None else None
                                       for p in (sq.RIFLEMEN, sq.LAST)) if m}
        strays = [i for i in sorted(soldiers) if worn and model_key(soldiers[i][0]) not in worn]
        for i in strays:
            # not a game rule: what our build gives a soldier's own figure (a model on the bones his figure plays on)
            result.findings.append(Finding("error", f"{soldiers[i][1]}: files/models/{soldiers[i][2]}.glb: the model "
                                                    f"of {unit}'s soldier {i} was fitted to {soldiers[i][0]}, which "
                                                    f"none of its soldiers wears (import it again in the Studio)"))
        if strays:
            continue
        unit_obj = run.game.own(name)
        wrote = False
        if count is not None:
            copy = _fresh(shared)
            copy.props[sq.COUNT] = Num(shared_count.kind, Decimal(count))
            unit_obj.props[sq.OWN_COUNT] = Inline(copy)
            result.findings.append(Finding("note", f"{where}: {unit} has {count} soldiers of its own (the game's "
                                                   f"squads have {shared_n})"))
            wrote = True
        if soldiers or games:
            has_last = _figure_of(run, unit_obj, sq.LAST) is not None
            entries = []
            worn_game: dict = {}   # soldier -> the game's model he draws, wearing the game's look
            for i in range(1, n + 1):
                fig = None
                if i in soldiers:
                    fig = _soldier_figure(base, run, name, unit, unit_obj, sq.place_figure(i, n, has_last),
                                          soldiers[i], result)
                    if fig is not None:
                        result.findings.append(Finding("note", f"{soldiers[i][1]}: {unit}'s soldier {i} wears a look "
                                                               f"of his own"))
                elif i in games:
                    fig = _game_figure(base, run, name, unit, unit_obj, sq.place_figure(i, n, has_last), i, games[i],
                                       result)
                    if fig is not None:
                        worn_game[i] = _mesh_file(run, fig)
                        result.findings.append(Finding("note", f"{games[i]}: {unit}'s soldier {i} wears the game's "
                                                               f"look"))
                entries.append(Inline(fig) if fig is not None else Ref(None))
            if soldiers or worn_game:
                unit_obj.props[sq.OWN_LOOKS] = ListV(entries)
                _far_figure_most(run, name, unit, unit_obj, n, has_last, soldiers, result, worn_game)
                wrote = True
        if wrote:
            done.append(unit)
    if done:
        if sq.PATCH not in result.game_patch:
            result.game_patch.append(sq.PATCH)
        result.findings.append(Finding("note", f"the modded copy gets the game patch {sq.PATCH} for the squads with "
                                               f"soldiers of their own ({', '.join(done)})"))


def _figure_of(run, obj, prop: str):
    """The figure (or any part) the unit object `obj` names in `prop`: its own part, or the object a link names; None
    when it names none."""
    from .patch import Inline, Ref
    v = obj.props.get(prop)
    if isinstance(v, Inline):
        return v.obj
    if isinstance(v, Ref) and v.target:
        return run.game.objects.get(v.target)
    return None


def _mesh_file(run, figure) -> str | None:
    """The model a figure draws (its MeshDescriptor's FileName), or None."""
    mesh = _figure_of(run, figure, "MeshDescriptor") if figure is not None else None
    f = mesh.props.get("FileName") if mesh is not None else None
    return f.value if isinstance(f, Text) and f.kind == "path" else None


def _soldier_figure(base, run, name: str, unit: str, unit_obj, place: str, look: tuple, result: BuildResult):
    """Soldier's own figure for R2SoldierLooks: a copy of the figure the game gives his place (`place`, the squad's
    riflemen's or its last man's, as the build leaves it: its clips and halves the squad's), its model part his own
    model (<the model he was fitted to's folder>\\<unit>__<i>lod0, as unit_own_models writes it). When the squad's own
    model is on bones of its own and his isn't on those bones, the figure is the copied unit's as the game has it, so he
    plays what it plays (made on the game soldier's bones: an animation made on other bones can stop the game)."""
    from . import squads as sq
    from .modelin import OWN_SKELETON
    from .patch import Inline, _fresh
    from .unitmodel import glb_report
    like, mod_id, stem = look
    src = _figure_of(run, unit_obj, place) or _figure_of(run, unit_obj, sq.RIFLEMEN)
    main = result.own_models.get(unit)
    if src is not None and main is not None and glb_report(main[1]).get(OWN_SKELETON) \
            and _own_stem(stem) not in _on_main_bones(result, unit):
        op = run.created.get(name)
        source = base.objects.get(op.source) if op is not None and op.kind == "clone" else None
        game = _figure_of(run, source, place) if source is not None else None
        if game is not None:
            src = game
    if src is None or _mesh_file(run, src) is None:
        # not a game rule: what our build copies a soldier's figure from (the squad's figure for his place, with a model)
        result.findings.append(Finding("error", f"{mod_id}: files/models/{stem}.glb: {unit} has no figure with a model "
                                                f"for its soldiers to copy, so its soldier can't wear a look of his own"))
        return None
    fig = _fresh(src)
    mesh = _fresh(_figure_of(run, fig, "MeshDescriptor"))   # (a model part the game's units share: his own copy)
    mesh.props["FileName"] = Text("path", _own_model_path(like, stem))
    fig.props["MeshDescriptor"] = Inline(mesh)
    return fig


def _own_model_path(like: str, stem: str) -> str:
    """The model a mod's model file is written as (unit_own_models, squad_soldiers): <the folder of the model it was
    fitted to>\\<unit>lod0, <unit>__<kind>lod0 or <unit>__<i>lod0 (_own_stem)."""
    return f"{like.replace('/', chr(92)).rsplit(chr(92), 1)[0]}{chr(92)}{_own_stem(stem)}lod0.Ase2ndfbin"


def _game_figure(base, run, name: str, unit: str, unit_obj, place: str, i: int, mod_id: str, result: BuildResult):
    """Soldier `i`'s figure for R2SoldierLooks when he wears the game's look (rusemod.squads.write_game_look: Back to the
    game's look on him alone while the soldiers of his place wear a model of the mod; the owner's pick 3, 2026-11-12): a
    copy of the figure the game gives his place, as _soldier_figure copies it (its clips and halves the squad's), its
    model part the copied unit's for that place; the copied unit's figure as the game has it when the squad's own model
    is on bones of its own (the game's model is on the game soldier's bones). None when his place's figure draws that
    model already: he wears the game's look without an entry."""
    from . import squads as sq
    from .modelin import OWN_SKELETON
    from .patch import Inline, _fresh
    from .unitmodel import glb_report, model_key
    op = run.created.get(name)
    source = base.objects.get(op.source) if op is not None and op.kind == "clone" else None
    game = _figure_of(run, source, place) if source is not None else None
    model = _mesh_file(run, game) if game is not None else None
    if model is None:
        # not a game rule: what our build copies the game's look from (the copied unit's figure for his place)
        result.findings.append(Finding("error", f"{mod_id}: files/models/{sq.soldier_stem(unit, i)}.json: the unit "
                                                f"{unit} copies has no figure with a model for soldier {i}'s place, so "
                                                f"he can't wear the game's look"))
        return None
    src = _figure_of(run, unit_obj, place) or _figure_of(run, unit_obj, sq.RIFLEMEN)
    if src is not None and _mesh_file(run, src) is not None and model_key(_mesh_file(run, src)) == model_key(model):
        return None
    main = result.own_models.get(unit)
    if src is None or (main is not None and glb_report(main[1]).get(OWN_SKELETON)):
        return _fresh(game)
    fig = _fresh(src)
    fig.props["MeshDescriptor"] = Inline(_fresh(_figure_of(run, game, "MeshDescriptor")))
    return fig


def _squad_need(run, obj) -> tuple[int, list]:
    """How many of a squad's weapons fire an ammunition with NeedModelChange (each goes to one soldier, from the last
    one back: the game's rule), and those ammunitions' names; its weapons as the unit holds them (WeaponDescriptor's
    turrets, their mounted weapons, each one's Ammunition), only its own parts walked."""
    from . import squads as sq
    from .patch import Inline, ListV, MapV, Ref
    found: list = []

    def part(v, named: bool = False):
        if isinstance(v, Inline):
            return v.obj
        if isinstance(v, Ref) and v.target and (named or not v.target.startswith("$/")):
            return run.game.objects.get(v.target)
        return None

    def walk(v, depth: int) -> None:
        if depth > 16:
            return
        if isinstance(v, ListV):
            for x in v.items:
                walk(x, depth + 1)
            return
        if isinstance(v, MapV):
            for _k, x in v.pairs:
                walk(x, depth + 1)
            return
        o = part(v)
        if o is None:
            return
        for p, w in o.props.items():
            if p != "Ammunition":
                walk(w, depth + 1)
                continue
            ammo = w.obj if isinstance(w, Inline) else run.game.objects.get(w.target) \
                if isinstance(w, Ref) and w.target else None
            flag = ammo.props.get(sq.NEED) if ammo is not None else None
            if isinstance(flag, Num) and flag.value != 0:
                found.append(w.target.rsplit("/", 1)[-1] if isinstance(w, Ref) else ammo.cls)

    weapons = part(obj.props.get("WeaponDescriptor"), named=True)   # (its own, or a named one: either is its weapons)
    for w in (weapons.props.values() if weapons is not None else ()):
        walk(w, 1)
    return len(found), found


def _far_figure_most(run, name: str, unit: str, unit_obj, n: int, has_last: bool, soldiers: dict,
                     result: BuildResult, worn_game: dict | None = None) -> None:
    """A squad whose soldiers have looks one by one: its far-away figure (FIGURINE) wears the look most of its `n`
    soldiers wear (the owner, 2026-11-11, on squad-page1: "It should take that like the more predominant unit"). Each
    soldier counts once, for the look he wears: his own look's model, the game's model when he wears the game's look
    (`worn_game`: {soldier: that model}), else the model of the figure the game gives his place as the build leaves it
    (the riflemen's own model, the last man's, or the game's). Copies of one look are one look (the owner's pick 5,
    2026-11-12): two models of the mod whose files show the same (rusemod.squads.look_key) count together, as do two
    soldiers drawing one game model. The most soldiers win; between looks with as many, the one the lowest-numbered of
    them wears (so a tie with soldier 1's look goes to soldier 1's)."""
    from collections import Counter

    from . import squads as sq
    from .unitmodel import model_key
    # this unit's models of the mod (its riflemen's, a kind's, each soldier's own), by the model each is written as
    files = {model_key(_own_model_path(like, stem)): glb for stem, (like, glb, _mod) in result.own_models.items()
             if _unit_of(stem) == unit}
    seen: dict = {}

    def look(model: str):
        glb = files.get(model_key(model))
        if glb is None:
            return ("game", model_key(model))
        if glb not in seen:
            seen[glb] = sq.look_key_file(glb) or f"file:{glb}"
        return ("mod", seen[glb])
    worn = []
    for i in range(1, n + 1):
        if i in soldiers:
            like, _mod, stem = soldiers[i]
            model = _own_model_path(like, stem)
        elif worn_game and i in worn_game:
            model = worn_game[i]
        else:
            model = _mesh_file(run, _figure_of(run, unit_obj, sq.place_figure(i, n, has_last)))
        if model:
            worn.append((look(model), model))
    if not worn:
        return
    counts = Counter(k for k, _m in worn)
    top = max(counts.values())
    _key, model = next((k, m) for k, m in worn if counts[k] == top)
    far = _figurine_model(run, unit_obj)
    if far is None or model_key(far) == model_key(model):
        return
    if _point_at_copies(run, name, {model_key(far): model}, parts=lambda p: p == FIGURINE[0]):
        result.findings.append(Finding("note", f"{unit}'s far-away figure wears the look most of its soldiers wear "
                                               f"({model.replace(chr(92), '/').rsplit('/', 1)[-1]}, {top} of {n})"))


def building_looks(run, result: BuildResult) -> dict:
    """New buildings' own looks (a mod's files/buildings/<name>/; rusemod.buildinglook): each building's two symbol
    names (its GfxDescriptor's) point at a symbol of its own, the copy the build makes of the one they named. Returns
    {building: (the symbol it copies, its own)}; an error said for a building no mod makes or whose look part names no
    symbol."""
    from .buildinglook import SYMBOL_NAMES, symbol_name
    from .patch import Inline, Ref, _fresh
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    for unit, (_look, mod_id) in sorted(result.own_looks.items()):
        where = f"{mod_id}: files/buildings/{unit}"
        name = by_name.get(unit)
        if name is None:
            # not a game rule: a look for a building no mod in the set makes
            result.findings.append(Finding("error", f"{where}: no mod in the set makes a new building {unit}"))
            continue
        gfx = run.game.objects[name].props.get("GfxDescriptor")
        found = []
        for path in SYMBOL_NAMES:
            obj = gfx.obj if isinstance(gfx, Inline) else None
            for step in path:
                v = obj.props.get(step) if obj is not None else None
                if isinstance(v, Ref) and v.target in run.game.objects:  # a part shared with another: a copy of it
                    v = obj.props[step] = Inline(_fresh(run.game.objects[v.target]))  # (every game building's is
                obj = v.obj if isinstance(v, Inline) else None                        # its own, 2026-10-18)
            found.append((obj, obj.props.get("SymbolName") if obj is not None else None))
        if any(not isinstance(s, Text) for _o, s in found):
            # not a game rule: what a building's look is made of (a symbol named twice in its GfxDescriptor)
            result.findings.append(Finding("error", f"{where}: {unit} names no look (GfxDescriptor "
                                                    f"{'.'.join(SYMBOL_NAMES[0])}.SymbolName), so it can't get one"))
            continue
        source, own = found[0][1].value, symbol_name(unit)
        for obj, s in found:
            obj.props["SymbolName"] = Text(s.kind, own)
        out[unit] = (source, own)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets a look of its own, {own}: a copy of {source} "
                                               f"with its {_look.piece.split('/', 1)[-1]} our model"))
    return out


def unit_own_copies(run, order: list, result: BuildResult) -> dict:
    """Units' own copies of the models they draw (a mod's files/models/<the unit's name>.copy.toml, its paint in
    files/models/<the unit's name>/; rusemod.unitmodel.write_unit_copy): every model part of the unit that names one
    of the models its file lists names the unit's copy instead, beside the game's model. A new unit's, or one of the
    game's units' (a squad's own uniform: its soldiers, its bazooka man and its token's figure; the owner,
    2026-10-11: "you don't want the whole game to be colored the same"). Returns {unit: ({the game's model: its copy},
    its paint, mod id)}. A unit with an imported model too (files/models/<name>.glb) is an error: it would have two
    (the Studio's Import model takes the copy out, so only a mod made by an older Studio or by hand has both)."""
    from .unitmodel import copy_model_name, model_key
    wanted: dict = {}
    for m in order:
        for unit, (of, paint) in (getattr(m, "model_copies", None) or {}).items():
            wanted[unit] = (of, paint, m.id)
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    for unit, (of, paint, mod_id) in sorted(wanted.items()):
        where = f"{mod_id}: files/models/{unit}.copy.toml"
        if any(_unit_of(s) == unit for s in result.own_models):   # (its main model, or one kind's: _unit_of)
            # One model per unit (an imported one, or a copy of the one it copies): each of its model parts names one
            # file. The Studio's Import model takes the copy out since 2026-11-10, so only a mod made by an older Studio
            # or by hand gets here; the words name the Studio's buttons that fix it (words.toml uniform_default_again,
            # model_copy_remove, model_remove).
            # not a game rule: one model per unit, our build's own way of writing a unit's model parts
            result.findings.append(Finding("error", f"{where}: {unit} has two models: one you imported "
                                                    f"(files/models/{unit}.glb) and its own copy of the game's model "
                                                    f"(this file, a squad's Custom uniform). Each of its figures is "
                                                    f"drawn with one model, so it can't use both. In the Studio, on "
                                                    f"this unit's page, click Back to the default uniform (or Use the "
                                                    f"shared model again, for a unit that isn't a squad) to keep your "
                                                    f"model, or Use the copied unit's model to keep the copy"))
            continue
        name = by_name.get(unit) or _game_unit(run, unit)
        if name is None:
            # Said with what to do (the owner, 2026-11-12: "this is not going to work because of this. You need to
            # change this."): a unit deleted from the mod by a Studio that stopped half way left it (ruse_studio.edits.
            # remove_leftovers takes such leftovers out).
            # not a game rule: a copy for a unit nothing makes
            result.findings.append(Finding("error", f"{where}: no mod in the set makes a unit {unit}, and the game "
                                                    f"has none of that name. If {unit} was deleted from this mod, "
                                                    f"this file was left behind: in the Studio, click Take out what "
                                                    f"it left under this mistake in Test in game's log, or delete "
                                                    f"this file"))
            continue
        if not of:  # (a file naming no model: the one its GfxDescriptor draws, as the first copies were made)
            source = _own_model_part(run, by_name, unit, where, result) if name in by_name.values() else None
            if source is None:
                if name not in by_name.values():
                    result.findings.append(Finding("error", f"{where}: `of` names no model to copy"))
                continue
            out[unit] = ({model_key(source): copy_model_name(source, unit)}, paint, mod_id)
        else:
            several = len({model_key(m) for m in of}) > 1
            copies = {model_key(m): copy_model_name(m, unit, several) for m in of}
            missing = [m for m in copies if not _point_at_copies(run, name, {m: copies[m]})]
            if missing:
                # not a game rule: the build copies only models the unit's own model parts name
                result.findings.append(Finding("error", f"{where}: {unit} draws no {', '.join(missing)} (none of "
                                                        f"its model parts names it)"))
                continue
            out[unit] = (copies, paint, mod_id)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets its own copy of "
                                               f"{', '.join(out[unit][0])}"
                                               f"{f', {len(paint)} texture(s) painted' if paint else ''}"))
    return out


def unit_own_clips(run, order: list, result: BuildResult, zz=None) -> dict:
    """Units' own animations (a mod's files/anim/units.toml and files/anim/own/<the unit's name>/; rusemod.anim): each
    clip a unit has of its own gets a name of its own in ZZ_Win.dat (`zz`, which those names mustn't be in already),
    and only that unit's listings name it (anim.own_listings: a part another unit shares is copied into the unit
    first, so they keep the game's). A new unit's or one of the game's. A later mod's row for the same clip or action
    of a unit wins. Returns {the clip's path in ZZ_Win.dat: {"unit", "mod", "clip": the game's clip it's made from or
    None, "edit": its changes, "file": the unit's own file or None}} for build_and_write, which makes them
    (anim.own_clip_files); a clip no listing names in the end is left out.

    A unit with a model of its own and its model's animations ([unit.<name>.animation]): every listing of the figures
    that draw its own model plays one of them, the one rusemod.animactions' rule picks (the modder's pick, else the
    nearest); a row of the action tables still wins. Its ride on long moves (unless it rides in its truck) is planned
    in result.own_rides for unit_own_rides.

    A mod's copies of a clip (files/anim/copies.toml; RUSE Decoy's Copy this animation…; the owner, 2026-11-13): each
    copy is made once, as a clip of its own ({"copy": its id, "mod", "clip", "edit"} in the answer), and the listings of
    that clip on the units ticked for it (or on the figures ticked of a unit) name it, every other unit's as before. A
    unit's own rows win over a copy for the listings they name (an action row, its own copy of the clip): said
    (_copy_coverage), as is a tick that nothing plays. Two copies ticked for the same figure: the later mod's plays."""
    from . import anim
    wanted: dict = {}   # unit -> {"clips": {clip: (edit, mod id)}, "actions": {(action, figure): (file, mod id)},
    #                              "animations": {name: (file, mod id)}, "plays": {action: (name, mod id)}, "ride"}
    for m in order:
        for unit, u in (getattr(m, "unit_clips", None) or {}).items():
            w = wanted.setdefault(unit, {"clips": {}, "actions": {}, "animations": {}, "plays": {}, "ride": None})
            for member, edit in u["clips"].items():
                w["clips"][member] = (edit, m.id)
            for key, file in u["actions"].items():
                w["actions"][key] = (file, m.id)
            if u.get("animations"):   # (a later mod's model brings its own animations: they take the place, whole)
                w["animations"] = {n: (f, m.id) for n, f in u["animations"].items()}
            for action, n in (u.get("plays") or {}).items():
                w["plays"][action] = (n, m.id)
            if u.get("ride"):
                w["ride"] = (u["ride"], m.id)
    copies: dict = {}   # (mod id, copy id) -> the copy (anim.mod_copies'), in load order
    for m in order:
        for cid, c in (getattr(m, "anim_copies", None) or {}).items():
            copies[(m.id, cid)] = c
    if not wanted and not copies:
        return {}
    if zz is None:
        result.findings.append(Finding("error", "these mods give units animations of their own, which go into "
                                                "ZZ_Win.dat; it wasn't given"))
        return {}
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    taken: set = set()

    def fresh(stem: str) -> str:
        """`stem`, or with _2, _3... when another clip has it already (or the game has a file of that name)."""
        base, k = stem[:-len("lod0")], 1
        while stem in taken or zz.entry(anim.own_member(stem)) is not None:
            k += 1
            stem = f"{base}_{k}lod0"
        taken.add(stem)
        return stem

    def copy_where(key) -> str:
        return f"{key[0]}: {anim.COPIES}: the copy {copies[key]['name']} ({key[1]})"

    # each copy, its clip's name planned once; and unit by unit, {(the clip, a figure's path or None for every figure of
    # it): the copy ticked for it}, a later mod's tick winning
    copy_files: dict = {}   # (mod id, copy id) -> (its path in ZZ_Win.dat, the FileName its listings give it)
    ticks: dict = {}
    for key, c in copies.items():
        stem = fresh(anim.own_stem(f"copy_{key[1]}", c["clip"]))
        copy_files[key] = (anim.own_member(stem), anim.own_data_name(stem))
        if not c["units"]:
            result.findings.append(Finding("note", f"{copy_where(key)} is ticked for no unit, so nothing plays it and "
                                                   f"it isn't made"))
        for unit, figs in sorted(c["units"].items()):
            t = ticks.setdefault(unit, {})
            for fig in figs or (None,):
                was = t.get((c["clip"], fig))
                if was is not None and was != key:
                    result.findings.append(Finding("warning", f"{copy_where(key)}: {unit}"
                                                              f"{f' ({fig})' if fig else ''} is ticked for "
                                                              f"{copy_where(was)} too: it plays {c['name']}, the later"))
                t[(c["clip"], fig)] = key
            wanted.setdefault(unit, {"clips": {}, "actions": {}, "animations": {}, "plays": {}, "ride": None})
    copy_counts: dict = {}   # (mod id, copy id) -> {unit: how many of its listings play the copy}

    for unit in sorted(wanted):
        w = wanted[unit]
        t = ticks.get(unit, {})
        mods = sorted({mid for _e, mid in w["clips"].values()} | {mid for _f, mid in w["actions"].values()}
                      | {mid for _f, mid in w["animations"].values()} | {mid for _n, mid in w["plays"].values()}
                      | ({w["ride"][1]} if w["ride"] else set()))
        where = f"{', '.join(mods)}: {anim.UNITS}"
        name = by_name.get(unit) or _game_unit(run, unit)
        if name is None:
            # not a game rule: animations for a unit nothing makes. Said with what to do, as unit_own_copies' line
            if mods:
                result.findings.append(Finding("error", f"{where}: no mod in the set makes a unit {unit}, and the "
                                                        f"game has none of that name. If {unit} was deleted from this "
                                                        f"mod, its animations were left behind: in the Studio, click "
                                                        f"Take out what it left under this mistake in Test in game's "
                                                        f"log, or take [unit.{unit}] out of {anim.UNITS} and delete "
                                                        f"the folder {anim.OWN}/{unit}/"))
            for key in sorted(set(t.values())):
                result.findings.append(Finding("error", f"{copy_where(key)}: it is ticked for a unit {unit}, which no "
                                                        f"mod in the set makes and the game hasn't got. If {unit} was "
                                                        f"deleted from this mod, untick it under Who plays it in RUSE "
                                                        f"Decoy (Your copies), or take {unit} out of "
                                                        f"[copy.{key[1]}.units] in {anim.COPIES}"))
            continue
        planned, by_clip, by_action, files = {}, {}, {}, {}
        for member in sorted(w["clips"]):
            edit, mod_id = w["clips"][member]
            stem = fresh(anim.own_stem(unit, member))
            by_clip[member] = anim.own_data_name(stem)
            planned[anim.own_member(stem)] = {"unit": unit, "mod": mod_id, "clip": member, "edit": edit, "file": None}
        for key in sorted(w["actions"], key=lambda k: (k[0], k[1] or "")):
            file, mod_id = w["actions"][key]
            if file not in files:   # (a file several actions play: one clip)
                files[file] = fresh(anim.own_stem(unit, Path(file).name))
                planned[anim.own_member(files[file])] = {"unit": unit, "mod": mod_id, "clip": None, "edit": None,
                                                         "file": file}
            by_action[key] = anim.own_data_name(files[file])
        ride_stem = None
        if w["animations"]:   # its model's own animations, on the figures that draw its model (and its ride)
            def plan(file, mod_id):
                if file not in files:
                    files[file] = fresh(anim.own_stem(unit, Path(file).name))
                    planned[anim.own_member(files[file])] = {"unit": unit, "mod": mod_id, "clip": None, "edit": None,
                                                             "file": file}
                return files[file]
            ride_stem = _own_animations(run, unit, name, w, result, where, plan, by_action)
        by_figure = {k: copy_files[key][1] for k, key in t.items()}
        if t:   # (before own_listings points the listings: what each tick finds there)
            _copy_coverage(run, unit, name, t, by_clip, by_action, copy_where, result)
        got = anim.own_listings(run.game, name, by_clip, by_action, by_figure)
        for key in sorted(set(t.values())):
            n = got["pointed"].get(copy_files[key][1], 0)
            if n:
                copy_counts.setdefault(key, {})[unit] = n
        for member in sorted(by_clip):
            if member not in got["plays"]:
                result.findings.append(Finding("warning", f"{where}: {unit} plays no {anim.clip_key(member)}, so "
                                                          f"nothing plays the copy of it it was given"))
        figures = {fig for fig, _a in got["actions"]}
        listed = {a for _f, a in got["actions"]}
        for action, fig in sorted(by_action, key=lambda k: (k[0], k[1] or "")):
            found = (fig, action) in got["actions"] if fig else action in listed
            if not found:
                on = "" if not fig else f" on its figure {fig}" if fig in figures else f" (it has no figure {fig})"
                result.findings.append(Finding("warning", f"{where}: {unit} lists no action {action}{on}, so "
                                                          f"nothing plays the clip it was given for it"))
        names = []
        for member, spec in sorted(planned.items()):
            stem = member.rsplit("\\", 1)[-1][:-len(".baf")]
            n = got["pointed"].get(anim.own_data_name(stem), 0) + (stem == ride_stem)   # (its ride plays one too)
            if n:
                out[member] = spec
                names.append(f"{stem} ({n})")
            elif spec["clip"] and spec["clip"] in got["plays"]:
                result.findings.append(Finding("note", f"{where}: {unit}'s own {anim.clip_key(spec['clip'])} isn't "
                                                       f"needed: every action playing it has a clip of its own"))
        if names:
            result.findings.append(Finding("note", f"{where}: {unit} plays {len(names)} clip(s) of its own, every "
                                                   f"other unit as before (listings naming each): {', '.join(names)}"))
    for key, c in copies.items():
        member, _file = copy_files[key]
        played = copy_counts.get(key, {})
        if played:
            out[member] = {"unit": None, "copy": key[1], "mod": key[0], "clip": c["clip"], "edit": c["edit"],
                           "file": None}
            result.findings.append(Finding("note", f"{copy_where(key)} of {anim.clip_key(c['clip'])} plays on "
                                                   f"{sum(played.values())} listing(s), every other unit's as before: "
                                                   f"{', '.join(f'{u} ({n})' for u, n in sorted(played.items()))}"))
        elif c["units"]:
            result.findings.append(Finding("warning", f"{copy_where(key)}: nothing plays it, so it isn't made: no unit "
                                                      f"ticked for it plays {anim.clip_key(c['clip'])} where it is "
                                                      f"ticked"))
    return out


def _copy_coverage(run, unit: str, name: str, ticks: dict, by_clip: dict, by_action: dict, copy_where,
                   result: BuildResult) -> None:
    """Said for the copies of clips ticked for the unit `unit` (`ticks`: {(the clip, a figure's path or None for every
    figure): (mod id, copy id)}), walked as anim.own_listings walks the unit and before it points anything: a figure
    ticked that the unit hasn't got, a tick none of whose listings plays the clip, and the listings where the unit's own
    rows win over the copy (an action row of units.toml, its own copy of the clip: RUSE Decoy's Only this unit)."""
    from . import anim
    from .animlist import member_of
    figures = anim.unit_figures(run.game, name)
    paths = {f["path"] for f in figures}
    for (clip, fig), key in sorted(ticks.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        who = f"{unit}'s figure {fig}" if fig else unit
        played = own_rows = own_copy = 0
        for f in figures:
            if fig is not None and f["path"] != fig or fig is None and (clip, f["path"]) in ticks:
                continue   # (another figure; or one ticked for a copy of its own, which wins there)
            for action, file in f["listings"]:
                if file is None or member_of(file) != clip:
                    continue
                if (action, f["path"]) in by_action or (action, None) in by_action:
                    own_rows += 1
                elif clip in by_clip:
                    own_copy += 1
                else:
                    played += 1
        if fig is not None and fig not in paths:
            result.findings.append(Finding("warning", f"{copy_where(key)}: {unit} has no figure {fig}, so nothing of "
                                                      f"it plays the copy"))
        elif not (played or own_rows or own_copy):
            result.findings.append(Finding("warning", f"{copy_where(key)}: {who} plays no {anim.clip_key(clip)}, so "
                                                      f"nothing of it plays the copy"))
        if own_copy:
            result.findings.append(Finding("note", f"{copy_where(key)}: {who} has its own copy of "
                                                   f"{anim.clip_key(clip)} ({anim.UNITS}), which it plays instead"))
        if own_rows:
            result.findings.append(Finding("note", f"{copy_where(key)}: {own_rows} of {who}'s listings of "
                                                   f"{anim.clip_key(clip)} play the unit's own animation for their "
                                                   f"action ({anim.UNITS}), which wins over the copy there"))


def _draws_own_model(model: str | None, unit: str, stems=None) -> bool:
    """Whether a figure's model is the unit's own: the name _own_model_part (and unitmodel.model_name) give it,
    <the copied model's folder>\\<unit>lod0.Ase2ndfbin; `stems`: every own model of the unit (_own_stems: its
    soldiers' and its bazooka man's), else its one."""
    if not model:
        return False
    name = model.replace("/", "\\").lower()
    return any(name.endswith(f"\\{s.lower()}lod0.ase2ndfbin") for s in (stems or [unit]))


def _unit_of(stem: str) -> str:
    """The unit a mod's model file is for: files/models/<unit>.glb, or <unit>@<kind>.glb for one kind of its
    soldiers (the owner, 2026-11-11: "when you copy a fucking unit, it should copy the unit": Import model gives the
    riflemen a model, the bazooka man keeps what the copied unit gave him until he gets <unit>@bazooka.glb)."""
    return stem.partition("@")[0]


def _own_stem(stem: str) -> str:
    """The name a model file's own model is written under, beside the copied model: <unit>lod0, or <unit>__<kind>lod0
    for one kind of its soldiers."""
    unit, _, kind = stem.partition("@")
    return f"{unit}__{kind}" if kind else unit


def _on_main_bones(result, unit: str) -> list:
    """The unit's own models that play its model's own animations, by the stem each is written under (_own_stem): its
    main one (files/models/<unit>.glb), and each kind's (<unit>@<kind>.glb, its bazooka man's) on the same bones as
    it, names and parents. A kind's model on other bones (the game soldier's, or another skeleton) is left to play
    what its figure played: an animation made on other bones can stop the game (2026-11-09)."""
    from .bonefit import skeleton_key
    main = result.own_models.get(unit)
    if main is None:
        return []
    key = skeleton_key(main[1])
    out = [unit]
    for stem, (_source, glb, _mod) in sorted(result.own_models.items()):
        if stem != unit and _unit_of(stem) == unit and key is not None and skeleton_key(glb) == key:
            out.append(stem)
    return [_own_stem(s) for s in out]


def _own_animations(run, unit: str, name: str, w: dict, result: BuildResult, where: str, plan, by_action: dict):
    """unit_own_clips' part for a unit with its model's own animations (`w`: its "animations", "plays", "ride" and
    the action rows that win): each listing of the figures that draw the unit's own model, by_action[(action,
    figure)] = the FileName of the animation rusemod.animactions.choose gives it (`plan(file, mod id)` gives a file
    its clip's stem). A unit with no model of its own in the build, or none of whose figures draws it, plays none of
    them, said (a clip of the model's bones on a figure drawing another model is what stopped the game on
    2026-11-09). Its ride on long moves goes in result.own_rides (unit_own_rides makes it). Returns the stem of the
    clip its ride plays, or None."""
    from . import anim, animactions
    from .patch import Inline, Num, Ref, Text
    anims = {n: f for n, (f, _m) in w["animations"].items()}
    names = list(anims)
    picks = {}
    for action, (n, mod_id) in sorted(w["plays"].items()):
        if n in anims:
            picks[action] = n
        else:
            result.findings.append(Finding("warning", f"{mod_id}: {anim.UNITS}: {unit}'s {action} plays {n}, which "
                                                      f"isn't one of its model's animations now, so it plays the "
                                                      f"nearest"))
    if unit not in result.own_models:
        result.findings.append(Finding("warning", f"{where}: {unit} has animations of its own but no model of its own "
                                                  f"(files/models/{unit}.glb), so none of them plays: its figures play "
                                                  f"what the unit it copies plays"))
        return None
    # (its figures drawing its own model: its riflemen, and its bazooka man when his own is on the same bones; on other
    # bones he plays what he played, unit_own_halves says so)
    stems = _on_main_bones(result, unit)
    drawn = [f for f in anim.unit_figures(run.game, name) if _draws_own_model(f["model"], unit, stems)]
    if not drawn:
        result.findings.append(Finding("warning", f"{where}: none of {unit}'s figures draws its own model, so its own "
                                                  f"animations play nowhere"))
        return None
    mod_of = {n: m for n, (_f, m) in w["animations"].items()}
    plays: dict = {}
    for fig in drawn:
        for key, clip in fig["listings"]:
            if (key, fig["path"]) in w["actions"] or (key, None) in w["actions"]:
                continue   # (a row RUSE Decoy or a tool wrote for the action wins)
            pick, _how = animactions.choose(key, names, picks, clip)
            by_action[(key, fig["path"])] = anim.own_data_name(plan(anims[pick], mod_of[pick]))
            plays[pick] = plays.get(pick, 0) + 1
    if plays:
        result.findings.append(Finding("note", f"{where}: {unit}'s figures that draw its own model play its model's "
                                               f"animations ({sum(plays.values())} listings of {len(drawn)} figures): "
                                               f"{', '.join(f'{n} {k}' for n, k in plays.items())}"))
    if w["ride"] and w["ride"][0] == "truck":
        return None
    truck = run.game.objects[name].props.get("TransportPourMorphe")
    if not isinstance(truck, Ref) or truck.target not in run.game.objects:
        result.findings.append(Finding("note", f"{where}: {unit} rides in no truck on long moves, so it gets no ride "
                                               f"of its own"))
        return None
    first = next((f for f in drawn if f["path"] == "GfxDescriptorFusilier"), drawn[0])   # (a squad's rifleman)
    mesh = first["object"].props.get("MeshDescriptor")
    mesh = mesh.obj if isinstance(mesh, Inline) else run.game.objects.get(mesh.target) if isinstance(mesh, Ref) \
        and mesh.target else None
    model = mesh.props.get("FileName") if mesh is not None else None
    mask = mesh.props.get("UsefulnessMask") if mesh is not None else None
    pack = first["object"].props.get("MultiRenderTypeMaterialPack")
    # how the riders grow as the camera goes out (their ScaleWithVisibilityRange_Coef and _Ref, a model look's own
    # pair: the game's US riflemen 20 against Zoom3_Infanterie, its trucks 12 against Zoom3): the ride takes its
    # riders', so the one model it rides as is drawn as big as each of them (the owner's FL-104, 2026-11-11: "The
    # horse that it switches to while it's moving needs to be a bit bigger")
    coef = first["object"].props.get("ScaleWithVisibilityRange_Coef")
    ref = first["object"].props.get("ScaleWithVisibilityRange_Ref")
    pick, _how = animactions.ride(names, picks)
    stem = plan(anims[pick], mod_of[pick])
    result.own_rides[unit] = {
        "unit": name, "truck": truck.target, "clip": anim.own_data_name(stem), "animation": pick,
        "model": model.value if isinstance(model, Text) else None,
        "mask": int(mask.value) if isinstance(mask, Num) else None,
        "pack": pack.target if isinstance(pack, Ref) and pack.target else None, "where": where,
        "mod": mod_of[pick],
        "coef": float(coef.value) if isinstance(coef, Num) else None,
        "ref": ref.target if isinstance(ref, Ref) and ref.target else None}
    return stem


def unit_own_rides(engine, run, result: BuildResult):
    """Each unit riding as itself on long moves (result.own_rides, planned by unit_own_clips): a copy of the truck it
    rides in, drawn as the unit's own model playing one of its animations on a loop, and the unit riding in that copy
    (the owner's 2026-11-09 words, "Just make it look like the horse is running for that truck animation"; the way his
    sixth and tenth Horse Squad copies did it by hand, played in the game: its own ride unit, the truck's look part with
    no wheels, chassis or dust (bones the model hasn't got), one listing 'idle1' looping, the default clip, its own
    size, the squad's own shader pack). The truck's values (its speed on the roads), its wreck and its far-zoom pile
    stay the truck's; the truck itself and every other unit's ride stay as they are. Made by the patch engine as a
    mod's lines are (`engine`, the build's: a clone gets its own id and name), after the mods. Returns `run` with the
    new objects among its created ones."""
    from . import anim
    from .patch import PatchError
    from .rndf import RndfError, parse
    objects = run.game.objects

    def free(stem: str) -> str:
        n, got = 2, f"$/GFX/Everything/{stem}"
        while got in objects:
            got, n = f"$/GFX/Everything/{stem}_{n}", n + 1
        return got

    for unit, r in sorted(result.own_rides.items()):
        if not r["model"] or r["mask"] is None:
            # not a game rule: what our build reads off the unit's figure to draw its ride
            result.findings.append(Finding("error", f"{r['where']}: {unit}'s figure names no model to draw its ride "
                                                    f"with"))
            continue
        ride, clip_obj = free(f"{unit}_Ride"), free(f"Anim_{unit}_Ride")
        look = (f"SousElements = MAP[]  ResourceAnimation = MAP[ ( 'idle1', {clip_obj} ) ]  DefaultAnimation = 'idle1'"
                f"  InnerScale = 1.0" + (f"  MultiRenderTypeMaterialPack = {r['pack']}" if r["pack"] else "")
                + (f"  ScaleWithVisibilityRange_Coef = {r['coef']!r}" if r.get("coef") is not None else "")
                + (f"  ScaleWithVisibilityRange_Ref = {r['ref']}" if r.get("ref") else ""))
        text = "\n".join([
            f"export {ride.rsplit('/', 1)[-1]} is clone {r['truck']} ( )",
            f"patch own {ride}:GfxDescriptor.MeshDescriptor ( FileName = path('{r['model']}')  "
            f"UsefulnessMask = {r['mask']} )",
            f"export {clip_obj.rsplit('/', 1)[-1]} is TGfxDescriptorAnimation ( FileName = path('{r['clip']}')  "
            f"UsefulnessMask = {RIDE_CLIP_MASK}  PlayInLoop = true )",
            f"patch own {ride}:GfxDescriptor ( {look} )",
            f"patch {r['unit']} ( TransportPourMorphe = {ride} )"])
        before = len(engine.findings)
        try:
            ops = parse(text, file=f"{anim.UNITS} ({unit}'s ride)", mod=r["mod"])
        except RndfError as exc:
            result.findings.append(Finding("error", f"{r['where']}: {unit}'s ride can't be made: {exc}"))
            continue
        for op in ops:
            try:
                engine.apply(op)
            except PatchError as exc:
                engine.findings.append(Finding("error", str(exc), op))
        result.findings += engine.findings[before:]
        if ride in engine.game.objects:
            result.findings.append(Finding("note", f"{r['where']}: {unit} rides as itself on long moves, playing "
                                                   f"{r['animation']} on a loop ({ride.rsplit('/', 1)[-1]}, a copy of "
                                                   f"{r['truck'].rsplit('/', 1)[-1]})"))
    for name, op in engine.created.items():
        run.created.setdefault(name, op)
    return run


RIDE_CLIP_MASK = 81920   # the UsefulnessMask every clip listing of the game carries (2026-11-09: all 593 of them)
def unit_own_halves(run, result: BuildResult) -> None:
    """New units whose own model is on bones of its own (its file's report says so: rusemod.unitmodel's own_bones):
    every figure that wears the model plays its clips through two masks of its own, the model's top and bottom halves,
    which the build adds to the unit data (rusemod.animmodel: copies of the game's top and bottom masks naming the
    model's own bones, split at the bone its record names, files/models/<the unit's name>.json "split", while the
    model has it, else at rusemod.bonefit's suggestion). The game's own masks name the game soldier's bones, and a mask naming a bone the model lacks
    would stop the game with its error box. A model on the game's own bones, and every other unit, are left as they
    were. Said: each such unit's halves; a listing of one of its figures that doesn't wear the model playing one of the
    unit's own clips (made on the model's bones)."""
    from . import anim, animmodel, bonefit
    from .modelin import OWN_SKELETON
    from .unitmodel import glb_report
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    for unit, (source, glb, mod_id) in sorted(result.own_models.items()):
        if "@" in unit or not glb_report(glb).get(OWN_SKELETON) or unit not in by_name:
            continue    # (a kind's own model, <unit>@<kind>: through its unit's main model, below)
        where = f"{mod_id}: files/models/{unit}.glb"
        name = by_name[unit]
        try:
            record = animmodel.record_of(glb)
        except animmodel.AnimModelError as exc:
            result.findings.append(Finding("error", f"{where}: {exc}"))
            continue
        # the unit's other own models (its bazooka man's) play through the same halves when they're on the same bones
        same = _on_main_bones(result, unit)
        wearing = []
        for stem, (k_source, k_glb, k_mod) in sorted(result.own_models.items()):
            if _unit_of(stem) != unit:
                continue
            if _own_stem(stem) in same:
                wearing.append(f"{k_source.replace('/', chr(92)).rsplit(chr(92), 1)[0]}{chr(92)}{_own_stem(stem)}lod0"
                               f".Ase2ndfbin")
            elif glb_report(k_glb).get(OWN_SKELETON):
                # not a game rule: the unit's own animations and halves are made on its main model's bones; a kind's
                # model on bones of its own but other ones plays the game's, made on the game soldier's bones
                result.findings.append(Finding("warning", f"{k_mod}: files/models/{stem}.glb: its bones aren't those "
                                                          f"of {unit}'s main model (files/models/{unit}.glb), so its "
                                                          f"figures play what the unit it copies plays, made on the "
                                                          f"game soldier's bones (an animation made on other bones can "
                                                          f"stop the game: make his model on the same bones as the "
                                                          f"main one)"))
        try:   # (one rule for the page and the build, item 5's merge: the bone the modder chose on the unit's page
            # while the model still has it, else rusemod.bonefit's suggestion: the 11-09 split for the Horse Squad)
            split = bonefit.split_for(Path(glb))
        except (bonefit.FitError, OSError, ValueError):
            split = None
        halves, notes = animmodel.halves_for(record, split)
        own = f"{source.replace('/', chr(92)).rsplit(chr(92), 1)[0]}{chr(92)}{unit}lod0.Ase2ndfbin"
        like = animmodel.game_masks(run.game, name, own)
        masks = {}
        for half in ("top", "bottom"):
            mask, k = f"$/GFX/Everything/Mask_{unit}_{half.capitalize()}", 1
            while mask in run.game.objects:
                k += 1
                mask = f"$/GFX/Everything/Mask_{unit}_{half.capitalize()}_{k}"
            run.game.objects[mask] = animmodel.mask_object(run.game, like[half], halves[half])
            masks[half] = mask
        got = animmodel.point_masks(run.game, name, tuple(wearing), masks)
        if not got["pointed"]:      # (no listing of a figure that wears it weighs bones by name: nothing to point)
            for mask in masks.values():
                del run.game.objects[mask]
        else:
            result.findings.append(Finding("note", f"{where}: {unit}'s {len(got['figures'])} figure(s) wearing its "
                                                   f"model play through its own two halves, split at "
                                                   f"{halves['split']} ({len(halves['top']['Weights'])} bone(s) on "
                                                   f"top, {len(halves['bottom']['Weights'])} below; "
                                                   f"{got['pointed']} listing(s))"))
        for n in notes:
            result.findings.append(Finding("warning", f"{where}: {unit}: {n}"))
        own_files = {anim.own_data_name(m.rsplit("\\", 1)[-1][:-len(".baf")]).lower()
                     for m, spec in result.own_clips.items() if spec.get("unit") == unit}
        wrong = sorted({fig for fig, _action, f in got["others"] if f.lower() in own_files})
        if wrong:
            # not a game rule: a clip goes with the model it was made on (a clip of other bones can stop the game)
            result.findings.append(Finding("warning", f"{where}: {unit}'s figure(s) {', '.join(wrong)} don't wear its "
                                                      f"model but play clips made on its bones"))


def _game_unit(run, unit: str) -> str | None:
    """The name of the game's unit called `unit` ("Descriptor_Unit_Soldat_US_Lourd"), or None."""
    name = f"$/GFX/Everything/{unit}"
    return name if name in run.game.objects else None


def unit_fit_checks(run, result: BuildResult, zz=None) -> int:
    """The owner's 7 (2026-11-10: "seven should warn them. If it's gonna break, and then tell them how to fix it. And
    what's the issue is."): a warning, never an error, for what doesn't fit on a unit with a model on bones of its own
    (every figure drawing it: each animation it plays, each bone its parts and shots need, its two halves, more than 64
    bones) and on a unit with animations of its own (each on the figure that plays it, against that figure's model: a
    model rigged to the game's bones it copies, a squad's soldier, has those bones). rusemod.bonefit says what each check
    rests on. Runs once the units' models, animations and halves are pointed (after unit_own_models and
    unit_own_clips); `zz`: ZZ_Win.dat, for the game's own clips and skeletons, read only when a check needs them.
    Returns how many warnings it said."""
    from . import anim, bonefit
    from .animlist import member_of, words
    from .modelin import OWN_SKELETON
    from .unitmodel import glb_report
    if not result.own_models and not result.own_clips:
        return 0
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    game = bonefit.GameBones(zz)

    def bones_of(file: str) -> list | None:     # (the clip a listing names: the unit's own, or the game's)
        m = member_of(file)
        spec = result.own_clips.get(m)
        if spec is None:
            return game.clip_bones(m)
        if spec.get("file"):
            try:
                return bonefit.clip_bones(Path(spec["file"]).read_bytes())
            except OSError:
                return None
        return game.clip_bones(spec["clip"]) if spec.get("clip") else None

    def own(file: str) -> bool:
        return member_of(file) in result.own_clips

    def clip_name(file: str) -> str:
        spec = result.own_clips.get(member_of(file))
        if spec is not None and spec.get("file"):
            return Path(spec["file"]).stem
        return words(member_of(file) if spec is None or not spec.get("clip") else spec["clip"])

    said = 0
    checked = set()     # (unit, figure) whose every animation is checked already
    like_of = {}        # a model rigged to the game's bones it copies (a squad's soldier) -> that model: its bones
    broken = (ValueError, KeyError, IndexError, OSError, struct.error)   # a file a check can't read: said, below
    for stem, (source, glb, mod_id) in sorted(result.own_models.items()):
        unit = _unit_of(stem)   # (its main model, or one kind's of its soldiers: <unit>@<kind>, its bazooka man's)
        name, where = by_name.get(unit), f"{mod_id}: {stem}"
        try:
            report = glb_report(glb)
            if name is None or name not in run.game.objects or not report.get("rigged"):
                continue    # (a model on a hull's bones plays no animations of its own)
            like = str(report.get("like") or source).replace("/", "\\")
            own_model = f"{like.rsplit(chr(92), 1)[0]}\\{_own_stem(stem)}lod0.Ase2ndfbin"
            if not report.get(OWN_SKELETON):
                like_of[bonefit.model_key(own_model)] = like    # (the game's own clips fit it: only its own can't)
                continue
            record = bonefit.glb_record(glb)
            if record is None:
                continue    # (its writing says why)
            names, parents = bonefit.skeleton_of(record)
            problems = bonefit.model_problems(names, parents, bonefit.model_record(glb).get(bonefit.SPLIT))
            for fig in bonefit.own_figures(bonefit.data_figures(run.game, name), [own_model]):
                problems += bonefit.check_figure(names, fig, bones_of, own)
                checked.add((unit, fig.path))
        except broken as exc:
            # not a game rule: a check that can't run is said, never dropped; it's only warnings, so the build goes on
            result.findings.append(Finding("warning", f"{where}: its animations and bones couldn't be checked "
                                                      f"({exc}), so the build goes on without that check."))
            said += 1
            continue
        said += _say_fit(result, where, problems, clip_name)
    for unit in sorted({spec["unit"] for spec in result.own_clips.values()}):
        name = by_name.get(unit) or _game_unit(run, unit)
        if name is None:
            continue
        mods = sorted({spec["mod"] for spec in result.own_clips.values() if spec["unit"] == unit})
        where = f"{', '.join(mods)}: {anim.UNITS}: {unit}"
        problems = []
        try:
            for fig in bonefit.data_figures(run.game, name):
                mine = [x for x in fig.listings if own(x[1])]
                if not mine or (unit, fig.path) in checked:
                    continue
                names = game.model_bones(like_of.get(bonefit.model_key(fig.model), fig.model))
                if names is None:   # a model no skeleton pack holds: the bones of the game's clips the figure plays
                    kinds = {tuple(b) for _a, f, _m in fig.listings if not own(f) and (b := bones_of(f)) is not None}
                    names = list(next(iter(kinds))) if len(kinds) == 1 else None
                if names is not None:
                    problems += bonefit.check_figure(names, bonefit.Figure(fig.path, fig.model, mine), bones_of, own,
                                                     masks=False)
        except broken as exc:
            result.findings.append(Finding("warning", f"{where}: its animations and bones couldn't be checked "
                                                      f"({exc}), so the build goes on without that check."))
            said += 1
            continue
        said += _say_fit(result, where, problems, clip_name)
    return said


def _say_fit(result: BuildResult, where: str, problems: list, clip_name) -> int:
    """unit_fit_checks' problems (rusemod.bonefit's) as the build's warnings, in plain words: what doesn't fit, what the
    game does with it, how to fix it."""
    from .bonefit import SHOT
    for p in problems:
        k, fig = p["kind"], p.get("figure", "")
        if k == "clip":   # (the animations that don't fit the same way, said together: a few by name)
            names = ", ".join(clip_name(c) for c in p["clips"][:4]) + (f" (+{len(p['clips']) - 4})"
                                                                         if len(p["clips"]) > 4 else "")
            n, acts = len(p["clips"]), len(p["actions"])
        if k == "clip" and p["how"] == "fewer":
            result.findings.append(Finding("warning", f"{where}: its figure {fig} plays {n} animation(s) for {acts} "
                                                      f"action(s) ({names}), and they have {p['clip_bones']} bones "
                                                      f"where the model has {p['model_bones']}. The game can stop on an "
                                                      f"animation with fewer bones than its model (it did in a test). "
                                                      f"Give those actions animations made on this model's own bones "
                                                      f"(in Blender, then Import model; the unit's page shows which "
                                                      f"animation each action plays)."))
        elif k == "clip" and p["how"] == "more":
            result.findings.append(Finding("warning", f"{where}: its figure {fig} plays {n} animation(s) for {acts} "
                                                      f"action(s) ({names}), and they have {p['clip_bones']} bones "
                                                      f"where the model has {p['model_bones']}. An animation with more "
                                                      f"bones than its model can stop the game (not tried in the game "
                                                      f"yet). Give those actions animations made on this model's own "
                                                      f"bones (in Blender, then Import model; the unit's page shows "
                                                      f"which animation each action plays)."))
        elif k == "clip" and p["how"] == "names":
            result.findings.append(Finding("warning", f"{where}: its figure {fig} plays {n} animation(s) for {acts} "
                                                      f"action(s) ({names}), and their bones have other names than the "
                                                      f"model's (the first: {p['examples'][0][0]}, where the model has "
                                                      f"{p['examples'][0][1]}). The game plays an animation bone by bone "
                                                      f"in order, so the wrong bones will move. Give those actions "
                                                      f"animations made on this model's own bones (in Blender, then "
                                                      f"Import model)."))
        elif k == "clip":
            result.findings.append(Finding("warning", f"{where}: its figure {fig} plays {n} animation(s) for {acts} "
                                                      f"action(s) ({names}), and they have the model's bones in another "
                                                      f"order. The game plays an animation bone by bone in order, so "
                                                      f"the wrong bones will move. Give those actions animations made on "
                                                      f"this model's own bones (in Blender, then Import model)."))
        elif k == "bone" and p["need"] == SHOT:
            result.findings.append(Finding("warning", f"{where}: its figure {fig} fires from a bone called "
                                                      f"{p['bone']}, which the model hasn't got, so the unit will fire "
                                                      f"with no shot to be seen (seen in a test). In Blender, add a bone "
                                                      f"called {p['bone']} at the weapon's muzzle, under the bone the "
                                                      f"weapon moves with, then bring the model back."))
        elif k == "bone":
            result.findings.append(Finding("warning", f"{where}: its figure {fig} hangs {p['count']} part(s) on a "
                                                      f"bone called {p['bone']}, which the model hasn't got: the game "
                                                      f"can stop on it (not tried in the game yet). In Blender, add a "
                                                      f"bone called {p['bone']} where that part belongs, then bring the "
                                                      f"model back."))
        elif k == "mask_bones":
            gone = ", ".join(p["names"][:6]) + (f" (+{len(p['names']) - 6})" if len(p["names"]) > 6 else "")
            result.findings.append(Finding("warning", f"{where}: its figure {fig} plays {p['count']} animation(s) "
                                                      f"on halves of the body that name bones the model hasn't got "
                                                      f"({gone}): the game can stop on it (not tried in the game yet). "
                                                      f"Choose where the model splits in two on the unit's page (Its two "
                                                      f"halves), then build again."))
        elif k == "mask_sum":
            result.findings.append(Finding("warning", f"{where}: its figure {fig}'s upper and lower halves together "
                                                      f"move {len(p['bones'])} bone(s) more than once over ("
                                                      f"{', '.join(p['bones'][:6])}), so the model will grow out of "
                                                      f"shape, as the horses of a test did. Choose where the model "
                                                      f"splits in two on the unit's page (Its two halves), then build "
                                                      f"again."))
        elif k == "too_many":
            result.findings.append(Finding("warning", f"{where}: the model has {p['bones']} bones. The game isn't "
                                                      f"seen to animate a model with more than {p['most']} (not tried in "
                                                      f"the game yet): it may stand still. In Blender, join or delete "
                                                      f"bones until it has {p['most']} or fewer, then bring the model "
                                                      f"back."))
        elif k == "split_gone":
            result.findings.append(Finding("warning", f"{where}: the bone {p['split']} chosen to split the model in "
                                                      f"two isn't in it any more, so it splits at {p['used']}. Choose "
                                                      f"again on the unit's page (Its two halves)."))
        elif k == "split_all_top":
            result.findings.append(Finding("warning", f"{where}: the model splits at {p['split']}, its first bone, "
                                                      f"so every bone is in its upper half and the lower half's "
                                                      f"animations (walking, running) move nothing. Choose another bone "
                                                      f"on the unit's page (Its two halves)."))
    return len(problems)


def _point_at_copies(run, name: str, copies: dict, parts=None) -> int:
    """Point every model part of the unit `name` (under its GfxDescriptor* links: a squad's soldiers, its bazooka man,
    its token's figure) that names one of `copies`' models ({the game's model, rusemod.unitmodel.model_key: the copy's
    name}) at the copy. A part the unit links to that other units link to as well (an unnamed object of its own in
    the unit data, or a model part) is copied into the unit first, so they keep the game's. A game unit is copied
    before it's changed (Game.own). `parts`: which of the unit's GfxDescriptor* links to look under (a test of the
    link's name; None: all of them). Returns how many model parts name a copy now (0: none named those models)."""
    from .patch import Inline, ListV, MapV, PairV, Ref, _fresh
    from .unitmodel import model_key
    objects = run.game.objects
    reached: dict = {}

    def names_one(obj) -> bool:
        f = obj.props.get("FileName")
        return isinstance(f, Text) and f.kind == "path" and model_key(f.value) in copies

    def followed(prop: str, v) -> bool:  # (never into another unit, a shared drawer or the like: only unnamed parts)
        return isinstance(v, Ref) and v.target in objects and (prop == "MeshDescriptor" or not v.target.startswith("$/"))

    def reaches(prop: str, v, depth: int = 0) -> bool:
        if depth > 24:
            return False
        if isinstance(v, Ref):
            if not followed(prop, v):
                return False
            if v.target not in reached:
                reached[v.target] = False  # (a loop counts as no)
                obj = objects[v.target]
                reached[v.target] = names_one(obj) or any(reaches(p, w, depth + 1) for p, w in obj.props.items())
            return reached[v.target]
        if isinstance(v, Inline):
            return names_one(v.obj) or any(reaches(p, w, depth + 1) for p, w in v.obj.props.items())
        if isinstance(v, ListV):
            return any(reaches(prop, x, depth + 1) for x in v.items)
        if isinstance(v, MapV):
            return any(reaches(prop, x, depth + 1) for _k, x in v.pairs)
        if isinstance(v, PairV):
            return reaches(prop, v.a, depth + 1) or reaches(prop, v.b, depth + 1)
        return False

    def point(prop: str, v, put) -> int:
        if not reaches(prop, v):
            return 0
        if isinstance(v, Ref):
            v = Inline(_fresh(objects[v.target]))  # the unit's own copy of a part others link to as well
            put(v)
        if isinstance(v, Inline):
            n = 0
            if names_one(v.obj):
                v.obj.props["FileName"] = Text("path", copies[model_key(v.obj.props["FileName"].value)])
                n += 1
            for p, w in list(v.obj.props.items()):
                n += point(p, w, lambda x, p=p, o=v.obj: o.props.__setitem__(p, x))
            return n
        if isinstance(v, ListV):
            return sum(point(prop, x, lambda y, i=i: v.items.__setitem__(i, y)) for i, x in enumerate(v.items))
        if isinstance(v, MapV):
            return sum(point(prop, x, lambda y, i=i, k=k: v.pairs.__setitem__(i, (k, y)))
                       for i, (k, x) in enumerate(v.pairs))
        if isinstance(v, PairV):
            return point(prop, v.a, lambda y: setattr(v, "a", y)) + point(prop, v.b, lambda y: setattr(v, "b", y))
        return 0

    def looked(p: str) -> bool:
        return p.startswith("GfxDescriptor") and (parts is None or parts(p))

    if not any(reaches(p, w) for p, w in objects[name].props.items() if looked(p)):
        return 0
    unit = run.game.own(name)
    return sum(point(p, w, lambda x, p=p: unit.props.__setitem__(p, x))
               for p, w in list(unit.props.items()) if looked(p))


def _own_model_part(run, by_name: dict, unit: str, where: str, result: BuildResult, rigged_on: str | None = None, also: list | None = None,
                    own_stem: str | None = None) -> str | None:
    """Point the new unit `unit`'s model part at a model of its own beside its source's ({folder}\\<unit>lod0): the
    model the source draws (the part's FileName), or None, with an error said, when no mod makes `unit` or its model
    part names no model file. `rigged_on`: the game's model a rigged model was fitted to (any kind of unit: a soldier's model is in parts of other names): every
    part of the unit naming it, or one of `also` (the unit's other models with the same bones: a squad's bazooka man), names the unit's own."""
    from .patch import Inline, Ref, _fresh
    from .unitmodel import model_key
    name = by_name.get(unit)
    if name is None:
        # not a game rule: a model for a unit no mod in the set makes
        result.findings.append(Finding("error", f"{where}: no mod in the set makes a new unit {unit}"))
        return None
    own_stem = own_stem or unit    # (a kind's own model, <unit>__<kind>: _own_stem)
    if rigged_on:
        own = f"{rigged_on.replace('/', chr(92)).rsplit(chr(92), 1)[0]}{chr(92)}{own_stem}lod0.Ase2ndfbin"
        if _point_at_copies(run, name, {model_key(m): own for m in [rigged_on, *(also or [])]}):
            return rigged_on
        # not a game rule: what our build supports (a part of the unit naming the model it was fitted to)
        result.findings.append(Finding("error", f"{where}: no part of {unit} names {rigged_on}, the model it was fitted to"))
        return None
    gfx = run.game.objects[name].props.get("GfxDescriptor")
    mesh = gfx.obj.props.get("MeshDescriptor") if isinstance(gfx, Inline) else None
    if isinstance(mesh, Ref) and mesh.target in run.game.objects:
        # a plane's model part is an object of its own that the copy shares with the unit it copies (the Bf 109's
        # MeshDescriptor names one; a tank's is written in the unit): the copy gets a copy of that part, written
        # in it, to name its own model, and the copied unit keeps its own (era planes, 2026-10-08)
        mesh = Inline(_fresh(run.game.objects[mesh.target]))
        gfx.obj.props["MeshDescriptor"] = mesh
    file = mesh.obj.props.get("FileName") if isinstance(mesh, Inline) else None
    if not isinstance(file, Text) or file.kind != "path" or not file.value.lower().endswith(".ase2ndfbin"):
        # not a game rule: what our build supports (a model part of its own, naming one model file)
        result.findings.append(Finding("error", f"{where}: {unit} has no model part of its own "
                                                f"(GfxDescriptor.MeshDescriptor) naming a model, so it can't get one"))
        return None
    source = file.value
    folder = source.replace("/", "\\").rsplit("\\", 1)[0]
    own = f"{folder}\\{own_stem}lod0.Ase2ndfbin"
    mesh.obj.props["FileName"] = Text("path", own)
    # its figurine, drawn zoomed out: a towed gun's names a model of its own (<gun>Midlod0) that the close-up's
    # change doesn't reach, so the unit showed the copied gun there (the owner, 2026-10-31, bigpacks4: "at certain
    # angles, it takes the default shape of what that unit was"). It names the unit's own model too: the two have the
    # same bones (15 of the 122 game units the era library copies have one, every one so)
    from .unitmodel import model_key
    figurine = _figurine_model(run, run.game.objects[name])
    if figurine is not None and model_key(figurine) != model_key(source):
        _point_at_copies(run, name, {model_key(figurine): own})
    return source


def _own_propeller_list(run, name: str, unit: str, glb, where: str, result: BuildResult) -> None:
    """A plane's own model with propellers its unit doesn't list (the model file's report, "own_propellers": modelin.fit_discs): each gets an entry in the unit's
    list of propellers (the game spins only what is listed, finding each one's bones by its number), a copy of the list's first entry with its
    own number, as T64 and T65 had it by hand in the game. Worked out here from the file, so it follows the model: another import, a removed model or unit leave nothing behind."""
    from .patch import Inline, ListV, MapV, Ref, Text, _fresh
    from .unitmodel import glb_report
    places = glb_report(glb).get("own_propellers")
    if not places:
        return
    objects = run.game.objects

    def of(value):
        return value.obj if isinstance(value, Inline) else objects.get(value.target) if isinstance(value, Ref) else None

    gfx = objects[name].props.get("GfxDescriptor")
    parts = gfx.obj.props.get("SousElements") if isinstance(gfx, Inline) else None
    pairs = parts.pairs if isinstance(parts, MapV) else []
    at = next((k for k, pair in enumerate(pairs) if of(pair[1]) is not None and "ListeHelice" in of(pair[1]).props), None)
    if at is None:
        # not a game rule: what our build supports (the list where every plane of the game has it)
        result.findings.append(Finding("warning", f"{where}: {unit}'s model has its own propellers, but the unit has no list of propellers to put them on: they won't spin"))
        return
    if isinstance(pairs[at][1], Ref):       # (a part shared with another: the copy gets its own, and the other keeps its list)
        pairs[at] = (pairs[at][0], Inline(_fresh(of(pairs[at][1]))))
    holder = of(pairs[at][1])
    old = holder.props["ListeHelice"]
    entries = [of(v) for v in old.items] if isinstance(old, ListV) else []
    listed = {e.props["HeliceNumber"].value for e in entries if e is not None and isinstance(e.props.get("HeliceNumber"), Text)}
    first = next((e for e in entries if e is not None and isinstance(e.props.get("HeliceNumber"), Text)), None)
    missing = [str(p[0]) for p in places if str(p[0]) not in listed]
    if not missing:
        return
    if first is None:
        result.findings.append(Finding("warning", f"{where}: {unit}'s list of propellers has no entry to copy: propellers {missing} won't spin"))
        return
    added = []
    for number in missing:
        entry = _fresh(first)
        entry.props["HeliceNumber"] = Text(first.props["HeliceNumber"].kind, number)
        added.append(Inline(entry))
    holder.props["ListeHelice"] = ListV(list(old.items) + added)
    result.findings.append(Finding("note", f"{where}: {unit} lists {len(added)} more propeller(s), numbers {', '.join(missing)}"))


FIGURINE = ("GfxDescriptorIcone", "PawnDescriptor", "DescriptorFigurine", "MeshDescriptor")


def _figurine_model(run, obj) -> str | None:
    """The model a unit's zoomed-out figurine names (its FIGURINE part's FileName), or None."""
    return _part_model(run, obj, FIGURINE)


def _part_model(run, obj, path) -> str | None:
    """The model a unit's model part at `path` (its links' names from the unit, the last one the part) names (its
    FileName), or None."""
    from .patch import Inline, Ref
    node = obj
    for prop in path:
        v = node.props.get(prop)
        node = v.obj if isinstance(v, Inline) else run.game.objects.get(v.target) if isinstance(v, Ref) else None
        if node is None:
            return None
    f = node.props.get("FileName")
    return f.value if isinstance(f, Text) and f.kind == "path" else None


def unit_classes(base, run, zz_win, result: BuildResult, scripts: dict | None = None) -> None:
    """Give every new unit a class in the game's Python unit list (ZZ_Win.dat), like the unit it copies. Units the
    list can't take (made from scratch, or copies of units it doesn't list) get a warning: the game ignores them.
    The new list goes into `scripts` ({script pack: (the pack, {module: new bytes})}, written once per pack by the
    caller); without it, straight into result.script_changed."""
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
        # a copy of a unit's part (its bomb bay, say) is placed with the unit as its source: only a unit takes a class
        like = ul.by_path.get(op.source) if op.kind == "clone" and obj.cls in unit_kinds else None
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
    if scripts is None:
        result.script_changed = {entry.path: pack.to_bytes({member.path: new_xyz})}
    else:
        scripts.setdefault(entry.path, (pack, {}))[1][member.path] = new_xyz
    result.new_classes = [n.name for n in new]
    for n in new:
        base_name = ".".join(ul.classes[n.like].base)
        result.findings.append(Finding("note", f"{n.path} gets its class {n.name}(front.{base_name}) in the game's "
                                               f"Python unit list, like {n.like}"))


def _own_kinds_planned(ops_lists) -> dict:
    """The kinds of buildings with units of their own (ownbuildings.KINDS) the mods' files give a building: {kind: the
    loc key of the first such building's name (its tab's title), or None}. Read from the files before the build runs,
    so the tabs go in with the mods; checked against what the build made (_own_kinds_made)."""
    from . import ownbuildings
    found: dict = {}
    for ops in ops_lists:
        for op in ops:
            if op.kind in ("clone", "create"):
                body = op.body
            elif op.kind == "set" and op.target:
                body = [op]
            else:
                continue
            kind = next((b.value for b in body if b.kind == "set" and b.path == "TypeBatiment"), None)
            if not isinstance(kind, Num) or int(kind.value) not in ownbuildings.KINDS:
                continue
            name = next((b.value for b in body if b.kind == "set" and b.path == "NameInMenuToken"), None)
            if found.get(int(kind.value)) is None:
                found[int(kind.value)] = name.value if isinstance(name, Text) and name.kind == "loc" else None
    return found


def _own_kinds_made(game, result: BuildResult) -> list[int]:
    """The kinds of buildings with units of their own the built unit data has, each building checked: in its kind's
    own build menu."""
    from . import ownbuildings
    kinds = set()
    for name, obj in game.objects.items():
        kind = obj.props.get("TypeBatiment")
        if not isinstance(kind, Num) or int(kind.value) not in ownbuildings.KINDS:
            continue
        k = int(kind.value)
        kinds.add(k)
        menu = obj.props.get("Menu")
        if not isinstance(menu, Num) or int(menu.value) != ownbuildings.MENU_OF[k]:
            # rule: own-units-menu
            result.findings.append(Finding("error", f"{name}: a building with units of its own of kind {k} needs build "
                                                    f"menu {ownbuildings.MENU_OF[k]} (Menu), its kind's own: a click "
                                                    f"on it opens the first tab of its menu"))
    return [k for k in ownbuildings.KINDS if k in kinds]


def _game_tab_keys(base) -> list[str]:
    """The build bar's list keys in the game's order (ownbuildings.tabs_rndf), or [] when the data has no such list."""
    from . import ownbuildings
    obj = base.objects.get(ownbuildings.TABS_OBJECT)
    value = obj.props.get(ownbuildings.TABS_PROP) if obj is not None else None
    if not isinstance(value, MapV):
        return []
    return [k.value if isinstance(k, Text) else str(k) for k, _v in value.pairs]


def build_pack(arc: Edat, mods: list, build_id: str = "0", text_arc: Edat | None = None,
               cache: Path | None = None, rmod_units=None) -> BuildResult:
    """Run `mods` [(ModInfo, ops)] on the data files of `arc`, and their texts and new units' classes on
    `text_arc` (ZZ_Win.dat; needed when a mod has text/*.csv or new units). Nothing is written; see
    BuildResult.changed / text_changed / script_changed. `cache`: load_pack's. `rmod_units`, for a set holding .rmod
    mods too, whose changes `arc` already has: (the unit data pack as the game ships it, zz_win() giving ZZ_Win.dat as
    the mods leave it, the .rmod files), so their own units get the unit-model check with ours (rmod_unit_models)."""
    order = load_order([m for m, _ in mods])
    by_id = {m.id: (m, ops) for m, ops in mods}
    result = BuildResult(order=[m.id for m in order])
    pack = load_pack(arc, cache)
    base, loaded, members, shadows = pack.base, pack.loaded, pack.members, pack.shadows
    # the types mods place that the game doesn't draw from far get copies that it does, used by the mods' objects
    # alone (rusemod.visibility; the owner, 2026-10-03)
    from . import visibility
    placed = {getattr(o, "type", None) for m in order for objects in m.scenery.values() for o in objects}
    placed |= {t for m in order for areas in m.cliffs.values() for a in areas for t in a.types}   # ([[cliffs]])
    if any(r.bridges for _m, (roads, _ids) in scenario_edits(result.order, mods, "roads").items() for r in roads):
        from .scenery import descriptors as _descriptors  # the bridges the build adds for new roads: any kind
        placed |= {t for t, d in _descriptors(arc).items() if d.bridge}
    result.visibility = visibility.plan(base, {t for t in placed if t})
    extra = []
    if result.visibility:
        extra = [(ModInfo("r2-visibility"), parse(visibility.rndf(base, result.visibility), file="visibility.rndf",
                                                  mod="r2-visibility"))]
    first = []  # the mods' own map assets' scenery types (rusemod.sceneryasset), before any mod's rules
    for m in order:
        for name, asset in sorted(m.assets.items()):
            if name in result.own_assets:
                result.findings.append(Finding("error", f"{m.id}: files/assets/{name}: {result.own_assets[name][1]} "
                                                        f"has an asset of that name too"))
            result.own_assets[name] = (asset, m.id)
        for unit, look in sorted(getattr(m, "looks", {}).items()):   # new buildings' own looks (rusemod.buildinglook)
            if unit in result.own_looks:
                result.findings.append(Finding("error", f"{m.id}: files/buildings/{unit}: {result.own_looks[unit][1]} "
                                                        f"gives that building a look too"))
            result.own_looks[unit] = (look, m.id)
    if result.errors:
        return result
    if (result.own_assets or result.own_looks) and text_arc is None:
        result.findings.append(Finding("error", "these mods add map assets or building looks, whose models go into "
                                                "ZZ_Win.dat; it wasn't given"))
        return result
    if result.own_looks:
        from .buildinglook import BuildingLookError, piece_kind
        for unit, (look, mod_id) in sorted(result.own_looks.items()):
            try:   # the piece of the copied look the model takes the place of: its type and its model
                look.asset.piece = piece_kind(base, look.piece)
            except BuildingLookError as exc:
                result.findings.append(Finding("error", f"{mod_id}: files/buildings/{unit}: {exc}"))
        if result.errors:
            return result
    if result.own_assets or result.own_looks:
        from .sceneryasset import AssetError, rules as asset_rules
        try:
            text = asset_rules(base, [a for a, _mod in result.own_assets.values()]
                               + [look.asset for look, _mod in result.own_looks.values()])
        except AssetError as exc:
            result.findings.append(Finding("error", str(exc)))
            return result
        first = [(ModInfo("r2-assets"), parse(text, file="files/assets", mod="r2-assets"))]
    # the build bar's tabs of the buildings with units of their own (rusemod.ownbuildings), after the mods
    own_planned = _own_kinds_planned(by_id[m.id][1] for m in order)
    if own_planned:
        from . import ownbuildings
        game_keys = _game_tab_keys(base)
        if ownbuildings.COPIED_TAB not in game_keys:
            # not a game rule: what the build copies each new tab from
            result.findings.append(Finding("error", "these mods have buildings with units of their own, but the unit "
                                                    "data has no build bar list with the Prototypes tab to copy"))
            return result
        tabs = [(k, own_planned[k]) for k in ownbuildings.KINDS if k in own_planned]
        extra = extra + [(ModInfo("r2-own-buildings"), parse(ownbuildings.tabs_rndf(tabs, game_keys),
                                                             file="own buildings", mod="r2-own-buildings"))]
    engine = Engine(base)
    run = engine.run(first + [by_id[m.id] for m in order] + extra)
    result.findings = [Finding("note", n) for n in base.notes] + list(run.findings)
    # the levels each placed type is drawn at (its far copy's too), for its objects to ask of the blocks they hang on
    result.type_levels = visibility.type_levels(run.game, {t for t in placed if t} | set(result.visibility.values()))
    if shadows:
        result.findings.insert(0, Finding("note", f"left {len(shadows)} debug-info copies as shipped "
                                                  f"({', '.join(p.rsplit(chr(92), 1)[-1] for p in shadows)})"))
    if run.errors:
        return result
    far_upgrades(run, result)
    into = unitpacks.Packs(text_arc) if text_arc is not None else None
    if rmod_units is not None and (getattr(arc, "changed", None) or getattr(arc, "added", None)):
        # .rmod mods changed the unit data under ours: their own units are in `base`, so every unit is set against the
        # game's as shipped (item 29, answer A, in every set that holds .rmod mods)
        shipped, zz_win, rmod_files = rmod_units
        rmod_unit_models(run, load_pack(shipped, cache).base, zz_win if text_arc is None else (lambda: text_arc),
                         result, rmod_files, base=base, into=into)
    else:
        unit_models(base, run, text_arc, result, into)
    spawn_models(run, text_arc, mods, result.order, result, into)
    mission_models(run, text_arc, mods, result.order, result)
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
    result.own_copies = unit_own_copies(run, order, result)
    result.own_clips = unit_own_clips(run, order, result, text_arc)
    unit_own_halves(run, result)   # (the unit's own figures only: before its ride, a unit of its own, is made)
    if result.own_rides:   # (units riding as themselves on long moves: their rides, made after the mods)
        run = unit_own_rides(engine, run, result)
    squad_soldiers(base, run, order, result)   # (each soldier's own figure a copy of the squad's as it now stands)
    result.look_symbols = building_looks(run, result)
    unit_fit_checks(run, result, text_arc)  # (after every step that points a unit's models, clips and halves)
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
    scripts: dict = {}  # script pack in ZZ_Win.dat -> (the pack, {module: new bytes})
    unit_classes(base, run, text_arc, result, scripts)
    own_buildings(run, text_arc, own_planned, result, scripts)
    groups = merged_groups(order)
    menu_lines(run, text_arc, result, scripts, groups)
    menu_group_limits(run, text_arc, groups, result)
    if result.errors:
        return result
    result.script_changed = {path: pack.to_bytes(members) for path, (pack, members) in scripts.items()}
    return result


def merged_groups(order) -> dict:
    """The build lists' groups of the mods `order` (ModInfo, in load order: each one's menu_groups.toml,
    rusemod.menugroups), together: a later mod's entry wins for the same unit."""
    out: dict = {}
    for m in order:
        out.update(getattr(m, "menu_groups", None) or {})
    return out


def menu_lines(run, zz_win, result: BuildResult, scripts: dict, groups: dict | None = None) -> None:
    """A build list's lines as rows (rusemod.menulines): when the mods make new objects (units among them, so a tab's
    list can grow past the screen) or put units in groups (`groups`: their menu groups, merged_groups), the game's
    menu script with the lines template run after it (into `scripts`), each unit's line filled in."""
    from . import menulines
    groups = groups or {}
    if not (run.created or groups) or result.errors or zz_win is None:
        return
    missing = menulines.missing(zz_win)
    if missing:
        result.findings.append(Finding("note", f"the build lists keep the game's rows: {missing}"))
        return
    found = pyscript.find_unit_list(zz_win)
    by_path: dict = {}
    if found is not None:
        try:
            ul = pyscript.unit_list(pyscript.read_xyz(found[3]).payload)
            by_path = {path: uc.name for path, uc in ul.by_path.items()}
        except pyscript.ScriptError as exc:
            # not a game rule: what our reader supports
            result.findings.append(Finding("error", f"the build lists' lines can't be set: {exc}"))
            return
    lines = menulines.lines_of(run.game.objects, by_path, run.created, groups)
    if not run.created and not lines:  # the groups put no unit anywhere but where the game has it
        return
    try:
        changes = menulines.script_changes(zz_win, lines, scripts)
    except (menulines.MenuLinesError, pyscript.ScriptError) as exc:
        # not a game rule: what our writer supports, or a script it can't read or join
        result.findings.append(Finding("error", f"the build lists' lines can't be set: {exc}"))
        return
    scripts.update(changes)
    new = {menulines.class_name(run.game.objects, by_path, p) for p in run.created}
    placed = sum(1 for name, _line in lines if name in new)
    result.findings.append(Finding("note", f"each line of a build list stands in its own rows, at most "
                                           f"{menulines.ACROSS} units across ({placed} new units placed in a "
                                           f"line)"))
    if len(lines) > placed:
        result.findings.append(Finding("note", f"{len(lines) - placed} of the game's units stand in the group of a "
                                               f"build list the mods put them in (menu_groups.toml)"))


BUILDING = "TBatimentDescriptor"  # a building's class: its kind is TypeBatiment, the units it makes have it as Factory
# a building's name when the game's texts aren't at hand (ruse_studio.board ROWS), else the kind's number
BUILDING_NAMES = {8: "Barracks", 13: "Artillery & AA Base", 10: "Armor Base", 11: "Anti-Tank Base", 9: "Airfield",
                  12: "Prototype Base"}


def _english_names(zz_win, result: BuildResult):
    """A function giving an object's name in English as the built game shows it (its NameInMenuToken's text in the
    unit names, baseunite, the mods' texts as this build wrote them), or None: always None without ZZ_Win.dat or that
    dictionary."""
    import html
    from .dic import Dic, name_to_key
    dic = None
    if zz_win is not None:
        read, entries = _reader(zz_win)
        member = loc.member("baseunite", "us")
        e = entries.get(member.lower())
        raw = (result.text_changed.get(e.path) if e is not None else None) or read(member)
        try:
            dic = Dic(raw) if raw else None
        except (ValueError, struct.error):
            dic = None

    def name(obj) -> str | None:
        v = obj.props.get("NameInMenuToken") if obj is not None and dic is not None else None
        if not isinstance(v, Text) or v.kind != "key":
            return None
        try:
            text = dic.text(int(v.value, 16) if v.value.lower().startswith("0x") else name_to_key(v.value))
        except ValueError:
            return None
        return (html.unescape(text).strip() or None) if text else None
    return name


def menu_group_limits(run, zz_win, groups: dict, result: BuildResult) -> None:
    """A warning for each group of a built build list holding more than menugroups.MOST units, and for each building
    whose build list has more than menugroups.MOST_GROUPS groups (the owner, 2026-10-31: "We just need to limit how many
    can be in a certain group. Because it's buggy."; his picks: a mod already over it when it's built is built, with a
    warning; 11-01: "10 groups"), never an error: counted over the built units as the Studio counts them
    (rusemod.menulines over_limits, `groups` the mods' menu groups), the game's own units included. Named by the
    game's English names when ZZ_Win.dat is at hand, else by class names and the buildings' plain names."""
    from . import menugroups, menulines
    big, full = menulines.over_limits(run.game.objects, run.created, groups)
    if not big and not full:
        return
    name_of = _english_names(zz_win, result)
    buildings: dict = {}  # (nation, kind) -> its buildings, the game's first, by address
    for path, obj in run.game.objects.items():
        kind = obj.props.get("TypeBatiment")
        if obj.cls == BUILDING and isinstance(kind, Num):
            buildings.setdefault((unitcheck.nation_of(obj), int(kind.value)), []).append((path in run.created, path))

    def nation(n: int) -> str:
        return unitcheck.NATIONS[n] if 0 <= n < len(unitcheck.NATIONS) else f"nation {n}"

    def building(n: int, kind: int) -> str:
        for _new, path in sorted(buildings.get((n, kind), [])):
            said = name_of(run.game.objects[path])
            if said:
                return said
        return BUILDING_NAMES.get(kind) or f"building of kind {kind}"

    def unit(path: str) -> str:
        return name_of(run.game.objects.get(path)) or menulines.class_name(run.game.objects, {}, path) \
            or path.rsplit("/", 1)[-1]
    for (n, kind, _first), count, shown in big:
        # not a game rule: the owner's limit (2026-10-31, after bigpacks13); whether the game's menu limits a row or
        # the rows is not known
        result.findings.append(Finding("warning", f"the {unit(shown)} group in {nation(n)}'s {building(n, kind)} "
                                                  f"holds {count}: its build list may act up past {menugroups.MOST}"))
    for (n, kind), count in full:
        # not a game rule: the owner's pick (2026-11-01, "10 groups"), after his frames at 1920 x 1080 showed 11 rows
        # on the screen, 10 while the row under the mouse is drawn twice as big
        result.findings.append(Finding("warning", f"{nation(n)}'s {building(n, kind)} has {count} groups: its build "
                                                  f"list may run off the screen past {menugroups.MOST_GROUPS}"))


def own_buildings(run, zz_win, planned: dict, result: BuildResult, scripts: dict) -> None:
    """The buildings with units of their own (rusemod.ownbuildings): each checked in its kind's own build menu, the
    game's tab, bar-place and production-queue scripts with the templates run after them (into `scripts`), and the
    game patch the copy needs for kinds 4 and 7."""
    from . import ownbuildings
    kinds = _own_kinds_made(run.game, result)
    if sorted(kinds) != sorted(planned):
        # not a game rule: the tabs are planned from the mods' files before the build runs
        result.findings.append(Finding("error", f"the mods' files give buildings with units of their own of kinds "
                                                f"{sorted(planned)}, but the built data has kinds {sorted(kinds)} "
                                                f"(a later change to TypeBatiment?): keep each such building's kind "
                                                f"in the block that makes it"))
        return
    if not kinds or result.errors:
        return
    if zz_win is None:
        result.findings.append(Finding("error", "these mods have buildings with units of their own, whose tabs go "
                                                "into ZZ_Win.dat's scripts; it wasn't given"))
        return
    try:
        changes = ownbuildings.script_changes(zz_win, kinds)
    except (ownbuildings.OwnBuildingsError, pyscript.ScriptError) as exc:
        # not a game rule: what our writer supports, or a script it can't read or join
        result.findings.append(Finding("error", f"the tabs of the buildings with units of their own can't be added "
                                                f"to the game's scripts: {exc}"))
        return
    for path, (pack, members) in changes.items():
        scripts.setdefault(path, (pack, {}))[1].update(members)
    result.own_kinds = kinds
    patched = bool(set(kinds) & ownbuildings.PATCHED)
    if patched and ownbuildings.PATCH not in result.game_patch:
        result.game_patch.append(ownbuildings.PATCH)
    result.findings.append(Finding("note", f"buildings with units of their own: kinds {', '.join(map(str, kinds))}, "
                                           f"each with its tab on the build bar"
                                   + (f"; the modded copy gets the game patch {ownbuildings.PATCH}"
                                      if patched else "")))


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


def _shipped_menu_pictures(result, mods: list, arc, text_arc, new_maps: set, say) -> dict:
    """A shipped map's own pictures in the menus (map.toml picture / wide_picture with no copy_of, MOD_FORMAT §8): the
    picture files its entries show, replaced in ZZ_Win.dat (result.text_changed). Each picture is the last mod's that
    gives one. A new map's own come with it (rusemod.newmap.make). Returns, for the start dots (_start_dots), {map:
    (its pictures as merged, the text_changed key of its wide picture or None, the scenario its entry plays or None,
    the mods' ids)}."""
    from dataclasses import replace
    from .ndf import Ndf
    from .newmap import NewMapError, entry_scenario, shipped_pictures
    from .players import GLOBALS, MAPINFO
    out: dict = {}
    pictured = {name: rows for name, rows in scenario_edits(result.order, mods, "menu_pictures").items()
                if name.lower() not in new_maps}
    if not pictured:
        return out
    if text_arc is None:
        # not a game rule: the game or one of its files isn't found
        result.findings.append(Finding("error", "ZZ_Win.dat isn't in this game, so no map's menu pictures can change"))
        return out

    def glad_now(member):
        """A ZZ_GladPatchableWin.dat member as the build has it so far (any case), or None."""
        key = member.lower()
        mine = next((d for m, d in result.changed.items() if m.lower() == key), None)
        if mine is not None:
            return mine
        e = arc.entry(member)
        return bytes(arc.read(e)) if e is not None else None
    for name, (specs, ids) in pictured.items():
        spec = specs[-1]
        for key in ("picture", "wide_picture"):  # a picture an earlier mod gives stays when a later one gives none
            if getattr(spec, key) is None:
                earlier = next((s for s in reversed(specs) if getattr(s, key) is not None), None)
                if earlier is not None:
                    spec = replace(spec, **{key: getattr(earlier, key),
                                            key + "_data": getattr(earlier, key + "_data"),
                                            **({"start_dots": earlier.start_dots} if key == "wide_picture" else {})})
        try:
            m = Ndf(glad_now(MAPINFO))
            changes, notes, wide, obj = shipped_pictures(m, Ndf(glad_now(GLOBALS)), name, spec,
                                                         lambda member: text_arc.entry(member) is not None)
            scen = entry_scenario(m, obj, glad_now) if spec.start_dots else None
        except (NewMapError, ValueError, KeyError, struct.error) as exc:
            result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}"))
            continue
        keys = {}
        for member, data in changes.items():
            e = text_arc.entry(member)
            keys[member] = e.path if e is not None else member
            result.text_changed[keys[member]] = data
        out[name] = (spec, keys.get(wide), scen, ids)
        say(f"menu pictures: {name}, from {', '.join(ids)} ({len(changes)} picture file(s))")
        for note in notes:
            say(f"  {note}")
    return out


def _start_dots(result, making: dict, shipped: dict, read_data, ground_bounds, say) -> None:
    """The places players start, drawn as white dots on the wide pictures that ask for them (map.toml start_dots,
    rusemod.menudraw.dotted): where each map's starting points are once the mods' edits are in, so a moved starting
    point moves its dot. `making`: the new maps (new_maps()); `shipped`: _shipped_menu_pictures' answer;
    `read_data(member)`: DataMap_Win.dat as the build leaves it; `ground_bounds(map)`: (x0, y0, x1, y1) or None."""
    from .menudraw import dots, places
    from .menupicture import PictureError, dotted_wide
    from .scenario import Scenario, ScenarioError, folder_of
    jobs = []  # (map, scenario file, wide picture PNG, where its file goes, its key there, the mods' ids)
    for name, (spec, mod_id) in making.items():
        clone = result.new_maps.get(name)
        member = next((m for m in clone.zz_new if m.lower().endswith("\\minimap2.tgv")), None) if clone else None
        if spec.start_dots and member and spec.wide_picture_data is not None:
            jobs.append((name, clone.scenario, spec.wide_picture_data, result.new_files, member, [mod_id]))
    for name, (spec, key, scen, ids) in shipped.items():
        if spec.start_dots and key and scen and spec.wide_picture_data is not None:
            jobs.append((name, scen, spec.wide_picture_data, result.text_changed, key, ids))
    for name, scen, png, into, key, ids in jobs:
        raw, bounds = read_data(folder_of(name) + scen), ground_bounds(name)
        try:
            if raw is None or bounds is None:
                raise ValueError("its scenario or its ground isn't there")
            starts = places(bounds, [it.position for it in Scenario.read(raw).items
                                     if it.kind == "StartingPoint" and it.listed])
            into[key] = dotted_wide(png, starts)
        except (ScenarioError, PictureError, ValueError, KeyError, struct.error, zlib.error) as exc:
            # not a game rule: what our build can draw
            result.findings.append(Finding("warning", f"{', '.join(ids)}: maps/{name}: start_dots: its starting "
                                                      f"points couldn't be drawn ({exc}), so its 3D map picture has "
                                                      f"no dots"))
            continue
        say(f"menu pictures: {name}: {len(dots(starts))} start dot(s) on its 3D map picture, where its starting "
            f"points are")


def _make_mission(result, clone, found: tuple, mod_id: str, rows: list, game, text_arc, read_data, say) -> bool:
    """A new map's own mission (maps/<map>/mission.toml, rusemod.mission and missionbuild): its script into
    result.mission_scripts, its texts into the copy's new ZZ_Win.dat files, its camera moves into the copy's own camera
    file, its scenario cluster and MapIA pointed at them, its own menu pack into result.mission_packs. False (with the
    findings said) when it can't be made."""
    from . import mission as M
    from . import missionbuild as MB
    from .scenario import Place, Scenario
    mission, rel = found
    new, src, bs = clone.new, clone.source, chr(92)
    where = f"{mod_id}: {rel}"
    if clone.kind not in ("operation", "campaign"):
        # not a game rule: our missions are made for Operations and campaign chapters (BATTLES events come later)
        result.findings.append(Finding("error", f"{where}: maps/{new} copies a BATTLES map; a mission of its own is "
                                                f"for a copy of an Operation or a campaign chapter (map.toml entry)"))
        return False
    try:
        if text_arc is None:
            # not a game rule: the game or one of its files isn't found
            raise MB.MissionBuildError("ZZ_Win.dat isn't in this game, so the mission's texts can't be added")
        clusters = [k for k in clone.glad if f"scenario{bs}{new.lower()}{bs}" in k.lower() and "clustermap" in k.lower()]
        if len(clusters) != 1:
            raise MB.MissionBuildError(f"the copy's scenario cluster wasn't found once ({len(clusters)})")
        cluster, folder = MB.cluster_pointed(clone.glad[clusters[0]], src, new)
        ia_path = find_pack(game, "IA_Common.dat")
        if ia_path is None:
            # not a game rule: the game or one of its files isn't found
            raise MB.MissionBuildError("IA_Common.dat isn't in this game, so no mission can be added")
        with Edat.open(str(ia_path)) as ia:
            src_member, new_member = MB.script_members(ia, src, folder, new)
            base = M.base_of(bytes(ia.read(ia.find(src_member))))
        # what the mission can name: the copy's scenario's named points and zones, and those the mods add
        scen = next((d for k, d in clone.data.items() if k.lower().endswith(bs + clone.scenario.lower())), None)
        points, zones, rects = set(), set(), set()
        for it in (Scenario.read(scen).items if scen is not None else []):
            name = it.values.get("Name")
            if isinstance(name, str) and name:
                (zones if it.kind in ("CircularZone", "RectangleZone") else points).add(name)
                if it.kind == "RectangleZone":
                    rects.add(name)
        for r in rows:
            if isinstance(r, Place) and r.file.lower() == clone.scenario.lower() and r.name:
                if r.kind in ("CircularZone", "RectangleZone"):
                    zones.add(r.name)
                    if r.kind == "RectangleZone":
                        rects.add(r.name)
                else:
                    points.add(r.name)
        mapia = [k for k in clone.glad if f"scenario{bs}{new.lower()}{bs}" in k.lower() and "mapia" in k.lower()]
        cam_member = MB.camera_file_of(clone.glad[mapia[0]], src) if len(mapia) == 1 else None
        cam_raw = read_data(cam_member) if cam_member else None
        classes = None
        found_list = pyscript.find_unit_list(text_arc) if text_arc is not None else None
        if found_list:
            try:
                ul = pyscript.unit_list(pyscript.read_xyz(found_list[3]).payload)
                classes = {n for n, c in ul.classes.items() if c.registered} | set(result.new_classes)
            except pyscript.ScriptError:
                classes = None
        from .scenario import placed_groups
        ctx = M.Context(new, clone.kind, points, zones, rects,
                        set(MB.camera_paths(cam_raw)) if cam_raw is not None else set(),
                        placed_groups(rows, clone.scenario), classes)
        bad = M.problems(mission, base, ctx)
        for level, message in bad:
            result.findings.append(Finding(level, f"{where}: {message}"))
            say(f"{level}: {where}: {message}")
        if any(level == "error" for level, _m in bad):
            return False
        xyz, text = MB.compiled(mission, base, ctx, new)
        dics = MB.text_files([e.path for e in text_arc.entries], lambda p: bytes(text_arc.read(text_arc.entry(p))),
                             src, folder, new, M.texts(mission, new))
        if mission.cameras:
            if cam_raw is None or len(mapia) != 1:
                raise MB.MissionBuildError("the copied map has no camera file to add the camera moves to")
            own = cam_member.replace(bs + src.lower() + bs, bs + new.lower() + bs)
            clone.data[own] = MB.with_cameras(cam_raw, mission.cameras)
            clone.glad[mapia[0]] = MB.mapia_pointed(clone.glad[mapia[0]], src, new)
    except (MB.MissionBuildError, M.MissionError, pyscript.ScriptError, ValueError, KeyError, struct.error,
            zlib.error) as exc:
        result.findings.append(Finding("error", f"{where}: the mission couldn't be made: {exc}"))
        return False
    clone.glad[clusters[0]] = cluster
    clone.zz_new.update(dics)
    result.mission_scripts[new_member] = xyz
    result.mission_sources[new] = text
    from .newmap import guid_for
    result.mission_packs.append((clone.guid, clone.kind, guid_for(new, "own menu pack")))
    clone.notes.append(f"its own mission: {len(mission.goals)} goal(s), {len(mission.events)} event(s), "
                       f"{len(mission.cameras)} camera move(s), in a menu pack of its own")
    return True


def _menu_orders(result, mods: list, arc, say) -> None:
    """Missions put in the mods' order in their menus (menus.toml, rusemod.menuorder): on globals.cpp as the build
    has it once everything else is in (the new maps' entries, the player counts), in load order."""
    from .menuorder import apply
    by_id = {m.id: m for m, _ in mods}
    orders = [(o, mod_id) for mod_id in result.order if mod_id in by_id
              for o in getattr(by_id[mod_id], "menu_order", [])]
    if not orders:
        return

    def read_glad(member):
        key = member.lower()
        mine = next((d for m, d in result.changed.items() if m.lower() == key), None)
        if mine is not None:
            return mine
        e = arc.entry(member)
        return bytes(arc.read(e)) if e is not None else None
    try:
        new, notes, problems = apply(read_glad, orders)
    except (ValueError, KeyError, struct.error) as exc:
        result.findings.append(Finding("error", f"menus.toml: the menus couldn't be read ({exc})"))
        return
    result.findings += [Finding("error", p) for p in problems]
    for member, data in new.items():
        e = arc.entry(member)
        for old in [m for m in result.changed if m.lower() == member.lower()]:
            del result.changed[old]
        result.changed[e.path if e is not None else member] = data
    for note in notes:
        say(f"menus: {note}")


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


def depot_rules(order: list[str], mods: list) -> tuple[dict, list[str]]:
    """Every mod's depots.toml together ({"all" or a map pack: scenario.DepotRule}), a later mod's rule for a map or
    for all maps replacing an earlier one's, and the mods that have one, in load order."""
    by_id = {m.id: m for m, _ in mods}
    rules: dict = {}
    ids: list[str] = []
    for mod_id in order:
        m = by_id.get(mod_id)
        if m is None or not getattr(m, "depots", None):
            continue
        for k, r in m.depots.items():
            rules.pop(next((x for x in rules if x.lower() == k.lower()), k), None)
            rules[k] = r
        ids.append(mod_id)
    return rules, ids


def draw_new_roads(read_map, path_of, lines: list, shaded=None, cache=None, shipped=None) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): new roads (map points, in order) written into every road file the map's own roads
    are in: painted into the ground's tiles as the map's own roads are across (rusemod.groundpaint.road_profile: what
    shows from afar), marked in the map's close-up map the way its own roads are (paint_detail), and added to the
    map's road model (rusemod.roadstrips, the far road). What shows up close is the asphalt and edge stickers the
    scenery step lays along them (scenery.road_decals; proven in the game on D-Day 2026-10-02, TESTS.md T12).
    `read_map(member)` gives the map pack's member as the build has it so far (a reshaped ground counts) or None,
    `path_of(member)` its full path. `shaded(x, y, i)`: true where lines[i] runs under trees (a road that keeps its
    trees, in one of the map's woods): painted fainter and greyer there (groundpaint.UNDER_TREES). A road that clears
    its trees is painted through a wood as the map's own roads are (the owner, 2026-10-03). `cache`: a folder where
    the map's measured road look is kept between builds (groundpaint.map_road_profile). `shipped(member)`: the map
    pack's member as the game ships it, where the map's own roads are looked at when it takes them out (roads.toml
    take_out): its road pieces, and its road model's look."""
    from .groundpaint import DETAIL, DETAIL_WIDER, ROAD_WIDTH, grid_bounds, map_road_profile, paint_detail, paint_roads
    from .roadstrips import draw_roads
    from .scenery import MEMBER as SCENERY, Scenery
    raw = (shipped or read_map)(SCENERY)
    pieces = Scenery(raw).roads() if raw else []
    profile = map_road_profile(read_map, pieces, cache)  # new roads painted as the map's own are across (2026-10-02)
    painted, notes = paint_roads(read_map, path_of, lines, pieces, profile=profile, shaded=shaded, cache=cache)
    detail, mesh = read_map(DETAIL), read_map("output\\highdef.tms")
    if detail is not None and mesh is not None:
        marked, more = paint_detail(detail, grid_bounds(mesh), lines, pieces, ROAD_WIDTH * DETAIL_WIDER, profile)
        notes += more
        if marked:
            painted[path_of(DETAIL)] = marked
    strips, more = draw_roads(read_map, path_of, lines, shipped)
    return {**painted, **strips}, notes + more


def sticker_mean(text_arc, colour: str, alpha: str = "") -> tuple | None:
    """A sticker's colour (r, g, b, 0-1) as the game shows it: its colour picture's mean over its shape (the picture's
    own alpha, or its material's separate alpha texture `alpha` when it has one: D-Day's grass and earth stickers'
    pictures are opaque, their shapes apart), read from the game's texture pack; None when the picture isn't there."""
    from .groundtex import tgv_grey, tgv_rgba
    from .tmst import Tgv
    e = text_arc.entry(colour)
    if e is None:
        return None
    w, h, px = tgv_rgba(bytes(text_arc.read(e)), 64)
    weight = [px[k + 3] for k in range(0, len(px), 4)]
    ea = text_arc.entry(alpha) if alpha else None
    if ea is not None:
        raw = bytes(text_arc.read(ea))
        if Tgv(raw).format.upper().startswith(("L8", "A8")):   # (France's: one channel, the shape itself)
            aw, ah, a_ch = tgv_grey(raw, 64)
        else:
            aw, ah, apx = tgv_rgba(raw, 64)
            a_ch = [apx[k + 3] for k in range(0, len(apx), 4)]
            if min(a_ch) == max(a_ch):   # (a grey picture: its shape in its brightness)
                a_ch = [apx[k] for k in range(0, len(apx), 4)]
        weight = [a_ch[(j * ah // h) * aw + i * aw // w] for j in range(h) for i in range(w)]
    tot = [0.0, 0.0, 0.0, 0.0]
    for n, a in enumerate(weight):
        tot[0] += px[4 * n] * a
        tot[1] += px[4 * n + 1] * a
        tot[2] += px[4 * n + 2] * a
        tot[3] += a
    if not tot[3]:
        return None
    return tot[0] / tot[3] / 255, tot[1] / tot[3] / 255, tot[2] / tot[3] / 255


def section_tint(map_arc, done: dict, stuck: list, text_arc) -> tuple[dict, list[str]]:
    """({member: new bytes}, notes): the map's close-up map with the tint under the stickers its sections lay
    (`stuck`: (x, y, half, turn, (their colour picture's member, their alpha texture's or ""))) fitted to the ground as
    painted and shaped by this build (`done`: its members so far), so they draw its colour
    (groundpaint.fit_sticker_tint). Each sticker's colour is its picture's mean over its shape (sticker_mean)."""
    from .groundpaint import DETAIL, _picture_sampler, fit_sticker_tint, grid_bounds
    from .groundtex import FINEST
    from .tms import Tms
    from .tmst import Tgv, Tmst

    def read(member):
        e = map_arc.find(member)
        return done.get(e.path) or bytes(map_arc.read(e))
    means: dict = {}
    for pics in sorted({s[4] for s in stuck}):
        mean = sticker_mean(text_arc, *pics)
        if mean is not None:
            means[pics] = mean
    stickers = [(x, y, half, turn, means[m]) for x, y, half, turn, m in stuck if m in means]
    mesh = read("output\\highdef.tms")
    bounds = grid_bounds(mesh)
    detail = read(DETAIL)
    store = Tmst(read("output\\highdef.tmst_pc"), read("output\\highdef.tmst_chunk_pc"))
    pixel = (bounds[2] - bounds[0]) / max(1, Tgv(detail).width)
    level = max(0, min(store.depth - 1, round(math.log2(max(1.0, pixel / FINEST)))))   # about the tint's own pixel
    at = _picture_sampler(store, bounds, level)
    normal_at = None
    xs, ys = [s[0] for s in stickers], [s[1] for s in stickers]
    if stickers:
        try:
            import numpy as np
        except ImportError:   # (level ground taken everywhere)
            np = None
        if np is not None:
            gx0, gy0 = min(xs) - 2 * pixel, min(ys) - 2 * pixel
            grid = Tms(mesh).height_box(gx0, gy0, max(xs) + 2 * pixel, max(ys) + 2 * pixel, pixel)
            z = np.array([[np.nan if v is None else v for v in row] for row in grid], dtype=float)
            if z.size and not np.isnan(z).all():
                z = np.where(np.isnan(z), np.nanmean(z), z)
                dzy, dzx = np.gradient(z, pixel)
                norm = np.sqrt(dzx * dzx + dzy * dzy + 1.0)

                def normal_at(x, y):
                    i = min(max(int(round((x - gx0) / pixel)), 0), z.shape[1] - 1)
                    j = min(max(int(round((y - gy0) / pixel)), 0), z.shape[0] - 1)
                    n = norm[j, i]
                    return -dzx[j, i] / n, -dzy[j, i] / n, 1.0 / n
    new, notes = fit_sticker_tint(detail, bounds, stickers, at, normal_at)
    missing = len(stuck) - len(stickers)
    if missing:
        notes.append(f"{missing:,} sticker(s) whose picture isn't in the game's texture pack keep their tint")
    return ({map_arc.find(DETAIL).path: new} if new else {}), notes


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
    (a map's road look: groundpaint.map_road_profile; the unit data as loaded: model.load). Safe to delete: it's
    measured again."""
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


def _shipped(arc, member: str) -> bytes | None:
    """A member of a layered pack (rmod.Layered) as the game ships it, under the changes on top."""
    e = arc.entry(member)
    return bytes(Edat.read(arc, e)) if e is not None else None


def copy_patches(wanted: list, wide: bool) -> list:
    """The game patches a modded copy gets: the build's (`wanted`, BuildResult.game_patch), and big-packs when a pack is
    written wide; each once, in the apps' own order (rusemod.gamepatch.PATCHES: more-buildings, big-packs, own-squads),
    so a copy that needed the first two before gets them as before. A name the apps don't know comes last, refused when
    it's fetched."""
    from . import gamepatch
    names = set(wanted) | ({"big-packs"} if wide else set())
    return [p for p in gamepatch.PATCHES if p in names] + sorted(names - set(gamepatch.PATCHES))


def patches_fingerprint(fp: bytes, patches: list) -> bytes:
    """A copy's fingerprint `fp` with each of its game patches taken in, in order ([(name, its file's SHA-256)]): players
    only play together with the same ones."""
    for name, sha in patches:
        fp = hashlib.sha256(fp + b"\ngame patch " + name.encode() + b" " + sha.encode()).digest()
    return fp


def _pack_reader(arc, *layers):
    """read(member) -> bytes or None, any case: the first of `layers` ({member: bytes}) that has it, else the pack
    `arc` (its own members, a new map's added ones, and those .rmod mods added: rmod.Layered.added)."""
    lows = [{k.replace("/", "\\").lower(): v for k, v in layer.items()} for layer in layers]

    def read(member: str):
        key = member.replace("/", "\\").lower()
        for low in lows:
            if key in low:
                return low[key]
        e = arc.entry(member)
        if e is not None:
            return bytes(arc.read(e))
        for a in (arc, getattr(arc, "base", None)):
            added = getattr(a, "added", None)
            if isinstance(added, dict):
                hit = next((d for m, d in added.items() if m.replace("/", "\\").lower() == key), None)
                if hit is not None:
                    return bytes(hit)
        return None
    return read


def _layout_names(raw) -> tuple[list, dict]:
    """A layout's (.scenario bytes) named places, to know which an edit takes out or renames: ([design item k's name,
    or None], {object of its NDF, a design item or its AddOn: the item's name}); ([], {}) when it can't be read."""
    from .ndf import local_ref
    from .scenario import Scenario, ScenarioError
    try:
        s = Scenario.read(raw)
        names, at = [], {}
        for it in s.items:
            name = it.values.get("Name") if isinstance(it.values.get("Name"), str) and it.values.get("Name") else None
            names.append(name)
            if name is not None:
                at[it.obj] = name
                props = {s.ndf.prop_name(pi): v for pi, v in s.ndf.objects[it.obj].props}
                addon = local_ref(props["AddOn"]) if "AddOn" in props else None
                if addon is not None:
                    at[addon] = name
        return names, at
    except (ScenarioError, ValueError, KeyError, IndexError, TypeError, AttributeError, struct.error, zlib.error):
        return [], {}


def _touched(table: dict, at, name) -> None:
    """Note in `table` ({(pack, member): the names its edits take out or rename, or None when one isn't known}) that
    an edit takes out or renames `name` (None: a name that can't be told) of the layout `at`."""
    if at in table and table[at] is None:
        return
    table[at] = None if name is None else (table.get(at) or set()) | {name}


def _mission_changers(rmods: list, mods: list, order: list, result, before=None, shipped=None) -> list:
    """The set's mods, in the order the build applies them (.rmod mods first), each with what it changes of the
    missions' files (rusemod.missionplaces), to name the mods a mission's warning is about: [(its name, whole
    {(pack, member): its bytes, or None when the file only becomes them in the build}, names {(pack, member): the
    names of the layout's places its edits take out or rename, or None when one can't be told}, other {(pack,
    member)}: its other changes there)], packs and members in lower case. A .rmod mod is named as it names itself (the
    mod list's name), any other by its id. `before` and `shipped`: DataMap_Win.dat as the build was given it (the .rmod
    mods' changes in) and as the game ships it, member -> bytes or None: where a Studio edit's item and an .rmod edit's
    object number are looked up for their names."""
    from . import missionplaces as mp
    from .scenario import NAMED_KINDS, Change, Remove, folder_of

    def key(pack, path) -> tuple:
        return str(pack).replace("\\", "/").rsplit("/", 1)[-1].lower(), str(path).replace("/", "\\").lower()
    layouts: dict = {}

    def names_of(read, member) -> tuple:
        if (id(read), member) not in layouts:
            raw = read(member) if read is not None else None
            layouts[(id(read), member)] = _layout_names(raw) if raw is not None else ([], {})
        return layouts[(id(read), member)]
    entries: dict = {}
    for m in rmods:
        name, whole, names, other = m.id, {}, {}, set()
        try:
            from ruse_mod_engine import mod_format
            mod = mod_format.load(str(m.rmod))
            name = str(mod.name or mod.id or m.id)
            for g in mod.file_patches:
                for fp in g.files:
                    if not fp.container:
                        whole[key(g.dat, fp.path)] = bytes(fp.data)
            for g in mod.scenario_patches:
                at = key(g.dat, g.scenario)
                for c in g.changes:
                    if not (c.action == "delete" or "Name" in (c.set_props or {}) or "Name" in (c.del_props or ())):
                        continue
                    match = c.match or {}
                    said = str(match["Name"]).strip("\"'") if "Name" in match else None
                    if said is None and str(match.get("_index", "")).isdigit():
                        said = names_of(shipped, at[1])[1].get(int(match["_index"]))
                    _touched(names, at, said)
                if at not in names:
                    other.add(at)
            for g in mod.patches:
                other.add(key(g.dat, g.ndf))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass   # (read by the build before: its changes are in; only what they are is missed here)
        entries[m.id] = (name, whole, names, other)
    by_id = {m.id: m for m, _ops in mods}
    for mod_id in order:
        m = by_id.get(mod_id)
        if m is None:
            continue
        name, whole, names, other = entries.get(mod_id, (mod_id, {}, {}, set()))
        for g in getattr(m, "game_files", None) or []:
            whole[key(g.pack, g.path)] = bytes(g.data) if g.added else None
        for (map_, part, file) in getattr(m, "scripts", None) or {}:
            whole[key(mp.IA, f"{mp.SCRIPT_ROOT}map\\{map_}\\{part}\\{file}")] = None
        for pack, rows in (getattr(m, "scenario", None) or {}).items():
            for row in rows:
                file = getattr(row, "file", None)
                if not file:
                    continue
                at = key(mp.DATA, folder_of(pack) + file)
                if (isinstance(row, Remove) and row.kind in NAMED_KINDS) or \
                        (isinstance(row, Change) and "name" in row.values):
                    items = names_of(before, at[1])[0]   # (the item's name before our edits: the one it loses)
                    _touched(names, at, items[row.item] if 0 <= row.item < len(items) else None)
                else:
                    other.add(at)
        for new in getattr(m, "new_maps", None) or {}:   # a new map's own files, its own mission's script too
            clone = next((c for n, c in result.new_maps.items() if n.lower() == new.lower()), None)
            if clone is not None:
                whole.update({key(mp.GLAD, k): bytes(v) for k, v in {**clone.glad, **clone.glad_changed}.items()})
                whole.update({key(mp.DATA, k): bytes(v) for k, v in clone.data.items()})
            whole.update({key(mp.IA, k): bytes(v) for k, v in result.mission_scripts.items()
                          if f"\\map\\{new.lower()}\\" in k.replace("/", "\\").lower()})
        entries[mod_id] = (name, whole, names, other)
    return list(entries.values())


def _mission_blame(x, changers: list, read: dict) -> tuple[list, list]:
    """The mods a rusemod.missionplaces.Missing's warning names: (for its layout, for its scripts), as its why says.
    For a file: the mods whose version of it is the one the build leaves (a whole file's last writer: the one whose
    bytes it is, or whose file only becomes them in the build), and the mods whose edits take out or rename a place of
    its layout that the mission lacks (or one that can't be told: the review of 95e9b910, 2026-11-14, found a mod
    named that took out only a place nothing watches); when its cluster names other files than the game's does, the
    mods changing the cluster too. When that names none (a change made some other way), every mod changing any of its
    files, else every mod of the set. `read`: {pack lower case: read(member)}, the packs as the build leaves them."""
    from . import missionplaces as mp
    cluster = (mp.GLAD.lower(), x.mission.cluster)
    lacked = set(x.zones)

    def in_effect(k) -> list:
        writers = [c for c in changers if k in c[1]]
        later = [c for c in writers if c[1][k] is None]   # (a folder mod's: written after every .rmod mod's)
        if later:
            return [later[-1][0]]
        now = read[k[0]](k[1])
        return [c[0] for c in writers if c[1][k] == now] or [c[0] for c in writers]

    def named(keys) -> list:
        out = []
        for k in keys:
            out += in_effect(k) + [c[0] for c in changers if k in c[2] and (c[2][k] is None or c[2][k] & lacked)]
        if x.repointed:
            out += [c[0] for c in changers if cluster in c[1] or cluster in c[3]]
        if not out:
            every = list(keys) + [cluster]
            out = [c[0] for c in changers if any(k in c[1] or k in c[2] or k in c[3] for k in every)]
        return list(dict.fromkeys(out)) or [c[0] for c in changers]
    layout = named([(mp.DATA.lower(), m) for m in x.mission.layouts]) if x.layout else []
    script = named([(mp.IA.lower(), m) for m in x.mission.scripts]) if x.script else []
    return layout, [n for n in script if n not in layout]


def mission_place_findings(found, changers: list, read: dict, titles=None) -> list:
    """The build's words on rusemod.missionplaces.check's answer `found`: for each mod it is about (in the set's order),
    a warning for the missions it leaves without zones they watch from the start, by the menu they're in (the owner,
    2026-11-13: "It should be warning on every version if there's an error"); and a note for each changed mission
    script that can't be read, the mission named as the menus name it (`titles`: _menu_titles). Only warns: the set
    builds and plays as before, battles and multiplayer included."""
    from . import missionplaces as mp
    counts: dict = {}   # mod name -> {(why, kind): {mission names}}
    for x in found.missing:
        on_layout, on_script = _mission_blame(x, changers, read)
        for why, names in (("layout", on_layout), ("script", on_script)):
            for name in names:
                counts.setdefault(name, {}).setdefault((why, x.mission.kind), set()).add(x.mission.name)
    out = []
    order = [c[0] for c in changers]
    for name in sorted(counts, key=lambda n: order.index(n) if n in order else len(order)):
        for (why, kind), missions in sorted(counts[name].items(),
                                            key=lambda kv: (kv[0][0] != "layout", mp.ORDER.index(kv[0][1]))):
            n = len(missions)
            if why == "layout" and kind == "tutorial":
                # rule: mission-zones
                out.append(Finding("warning", f"{name} replaces the tutorial's map with one that lacks places its "
                                              f"mission uses: with it on, the tutorial stops about a second after it "
                                              f"starts"))
            elif why == "layout" and kind == "campaign":
                # rule: mission-zones
                out.append(Finding("warning", f"{name} replaces the maps of {n} campaign chapter(s) with ones that "
                                              f"lack places their missions use: with it on, those chapters stop about "
                                              f"a second after they start"))
            elif why == "layout":
                # rule: mission-zones
                out.append(Finding("warning", f"{name} replaces the maps of {n} Operation(s) with ones that lack "
                                              f"places their missions use: with it on, those Operations stop about a "
                                              f"second after they start"))
            elif kind == "tutorial":
                # rule: mission-zones
                out.append(Finding("warning", f"{name} replaces the tutorial's mission with one that uses places its "
                                              f"map lacks: with it on, the tutorial stops about a second after it "
                                              f"starts"))
            elif kind == "campaign":
                # rule: mission-zones
                out.append(Finding("warning", f"{name} replaces the missions of {n} campaign chapter(s) with ones that "
                                              f"use places their maps lack: with it on, those chapters stop about a "
                                              f"second after they start"))
            else:
                # rule: mission-zones
                out.append(Finding("warning", f"{name} replaces the missions of {n} Operation(s) with ones that use "
                                              f"places their maps lack: with it on, those Operations stop about a "
                                              f"second after they start"))
    for name, why in dict.fromkeys((_mission_title(m, titles), why) for m, why in found.unread):   # (a mission in
        out.append(Finding("note", f"{name}: a file of its mission can't be read ({why}), so whether its map holds "
                                   f"every place the mission watches from its start wasn't checked"))   # two menus: once)
    return out


def _mission_title(mission, titles) -> str:
    """A mission as a player knows it: its name in the menus (`titles`: its text key -> the game's English text, or
    None), else its name in the map list."""
    said = titles(mission.title) if titles is not None and mission.title else None
    return " ".join(said.split()) if isinstance(said, str) and said.strip() else mission.name


def _menu_titles(open_texts):
    """titles(key) -> the menus' English text of a chapter's or an Operation's name, from the game's texts as the set
    leaves them (`open_texts()`: ZZ_Win.dat, or None), read once when first asked; None when it can't be read."""
    from . import loc
    from .dic import Dic
    got: dict = {}

    def titles(key: int):
        if "dic" not in got:
            got["dic"] = None
            try:
                arc = open_texts()
                e = arc.entry(loc.member(MENU_TEXTS, "us")) if arc is not None else None
                got["dic"] = Dic(bytes(arc.read(e))) if e is not None else None
            except (OSError, ValueError, KeyError, IndexError, struct.error):
                got["dic"] = None
        return got["dic"].text(key) if got["dic"] is not None else None
    return titles


MENU_TEXTS = "flash_txt"   # the game's dictionary of its menus' texts: chapters' and Operations' names among them


def mission_places(game: Path, stack, open_pack, glad, glad_changed: dict, data_packs: list, rmods: list, mods: list,
                   result) -> list:
    """The missions a player can pick (campaign chapters, Operations, the tutorial) that this set leaves without zones
    they watch from their start, read in the player's own game as the set leaves it and as the game ships it
    (rusemod.missionplaces), as the build's findings (mission_place_findings). `glad`: ZZ_GladPatchableWin.dat as the
    build has it, with `glad_changed` ({member: bytes}) on top; `data_packs`: the build's (path, pack, {member: bytes})
    for DataMap_Win.dat and IA_Common.dat; `open_pack`: a pack as the .rmod mods left it. None for a game without the
    three packs (no mission to look at).

    The check only warns, so nothing of it ever stops a build: whatever a set's files hold that can't be read, or
    anything else going wrong in it, is one note and the build goes on (the review of 95e9b910, 2026-11-14: menus with
    a list where a flag is stopped a build that had built before)."""
    from . import missionplaces as mp
    try:
        paths = {name: find_pack(game, name) for name in (mp.GLAD, mp.DATA, mp.IA)}
        if any(p is None for p in paths.values()):
            return []
        final, given = {}, {}
        for name, path in paths.items():
            if name == mp.GLAD and glad is not None:
                final[name] = _pack_reader(glad, glad_changed)
                continue
            arc = next((a for p, a, _c in data_packs if p == path), None)
            given[name] = _pack_reader(arc if arc is not None else open_pack(path))   # (as the build was given it)
            final[name] = _pack_reader(arc if arc is not None else open_pack(path),
                                       *[c for p, _a, c in data_packs if p == path])
        shipped = {name: _pack_reader(stack.enter_context(Edat.open(str(path)))) for name, path in paths.items()}
        found = mp.check(tuple(final[n] for n in (mp.GLAD, mp.DATA, mp.IA)),
                         tuple(shipped[n] for n in (mp.GLAD, mp.DATA, mp.IA)))
        if not (found.missing or found.unread):
            return []
        texts = find_pack(game, loc.PACK)
        return mission_place_findings(found, _mission_changers(rmods, mods, result.order, result, given.get(mp.DATA),
                                                               shipped[mp.DATA]),
                                      {n.lower(): r for n, r in final.items()},
                                      _menu_titles(lambda: open_pack(texts) if texts is not None else None))
    except (OSError, *mp._READ_ERRORS) as exc:   # (the menus or a cluster as the set leaves them, unreadable)
        return [Finding("note", f"the places the missions watch from their start couldn't be checked: the menus "
                                f"or a mission's files can't be read ({exc})")]
    except Exception as exc:  # noqa: BLE001 - a check that only warns never stops a build (above); a fault of
        # this check itself, not said to be a file's
        return [Finding("note", f"the places the missions watch from their start couldn't be checked ({exc})")]


def build_and_write(game: Path, mods: list, *, pack: str = DEFAULT_PACK, out: Path | None = None,
                    instance: Path | None = None, say=print, show_all: bool = False,
                    cache: Path | None = None, built_from: dict | None = None, fairplay=None,
                    cut_off_errors: bool = False, signature: bool = False) -> BuildResult:
    """Build `mods` [(ModInfo, ops)] against the game at `game` and write the result: rebuilt packs to `out` (a .dat
    file, or a folder for several packs) and/or a modded copy at `instance`. This is `ruse build`, and the launcher's
    Play. `say` gets every report line as it comes. Nothing is written when the build has errors. Problems the user
    can fix raise BuildError. `cache`: a folder for what can be measured once and kept between builds (BUILD_CACHE
    under the platform's folder for the apps and `ruse build`; none in the tests). `signature`: the copy gets R.U.S.E.
    2.0's gold title (rusemod.signature; the apps' Play and Test in game, unless Settings says the game's own title,
    signature.title_on). `built_from`: what the mods were read from (rusemod.play.built_from), kept in the copy's
    record so the next Play can start it without a build.

    .rmod mods (rusemod.rmod) are applied first, in their order in `mods`, and the other mods on top of them. Two
    .rmod mods that can't go together (the same file replaced with different contents, MOD_FORMAT.md §13) stop the
    build before anything is built, with every such clash named; a later mod overwriting an earlier one's values is
    a warning. An .rmod mod converted for the Studio (rusemod.rmodconvert) also has changes of its own: they're built
    with the other mods, on top of every .rmod.

    `fairplay` (rusemod.fairplay.FairPlay, from the mods' folders): whether the copy is a cheat copy (a cheat or a
    test tool in it: it gets the lock, with the copy's build code in it, so it plays multiplayer only with players
    who have the same build); without it, the .rmod mods' scripts decide. Every build gets the watcher, both in
    the maps' own script folders (IA_Common.dat, 1.5 MB). A modded copy gets the build's record (fairplay.RECORD):
    its join code and what the build wrote."""
    from . import fairplay as fair_play
    fair_mods = [(m.id, m.version) for m, _ops in mods]  # the mods in the set's order, for the join code
    lock_code = None  # the build code in a cheat copy's lock (fair_play.build_code), once the lock is made
    fair = fairplay if fairplay is not None else \
        fair_play.check_infos([m for m, _ops in mods]) if fair_play.ON else fair_play.FairPlay()
    rmods = [m for m, _ops in mods if m.rmod is not None]
    mods = [(m, ops) for m, ops in mods if m.rmod is None or ops or m.texts]
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
        game_files = [(m.id, m.game_files) for m, _ops in mods if getattr(m, "game_files", None)]
        if game_files or signature:  # whole game files the mods change or add (rusemod.gamefiles, MOD_FORMAT §7)
            from . import gamefiles, rmod as layers  # into the packs before anything else, so later changes go on
            if run is None:                          # top of them
                run = layers.RmodRun()
                stack.callback(run.close)

            def layered(path: Path):
                p = Path(path).resolve()
                if p not in run.packs:
                    base = Edat.open(str(p))
                    run.opened.append(base)
                    run.packs[p] = layers.Layered(base, p)
                return run.packs[p]

            if signature:  # R.U.S.E. 2.0's title (rusemod.signature), read as the .rmod mods left the game, and
                from . import signature as sig  # under every mod's game files: a mod changing one has its own
                theirs = {(g.pack.lower(), g.path.lower()): mod_id for mod_id, files in game_files for g in files}
                mine = []
                for g in sig.game_files(layered, lambda name: find_pack(game, name), cache, say):
                    mod_id = theirs.get((g.pack.lower(), g.path.lower()))
                    if mod_id is None:
                        mine.append(g)
                    else:
                        say(f"{sig.TITLE}: {mod_id} changes {g.pack}: {g.path}, so {mod_id}'s is used")
                game_files = ([(sig.TITLE, mine)] if mine else []) + game_files
            _touched, said = gamefiles.changes(layered, lambda name: find_pack(game, name), game_files, say)
            run.findings += [Finding(level, message) for level, message in said]

        new_packs: dict = {}  # a new map's pack (a path the game hasn't got) -> newmap.NewPack over the shipped one

        def open_pack(path: Path) -> Edat:
            """A pack as the .rmod mods left it (or as shipped); a new map's, as the copy it is."""
            if path in new_packs:
                return new_packs[path]
            layered = run.layered(path) if run else None
            return layered if layered is not None else stack.enter_context(Edat.open(str(path)))

        arc = open_pack(pack_path)
        text_arc = open_pack(text_path) if text_path else None
        zz_path, rmod_units = find_pack(game, loc.PACK), None
        if rmods:  # the .rmod mods' own units get the unit-model check, whatever else the set holds (item 29): the
            # unit data as the game ships it, ZZ_Win.dat as the mods leave it (opened only when a unit is looked at),
            # and the .rmod files, to say which changes a unit
            rmod_units = (stack.enter_context(Edat.open(str(pack_path))),
                          lambda: open_pack(zz_path) if zz_path is not None else None, [m.rmod for m in rmods])
        try:
            # the collector paused for the unit data's build: on two-shermans its passes over the loaded model and the
            # engine's copy of it took 2 to 4 seconds, and 5 to 9 with the model read from the cache, which it then
            # counts as new and looks through again and again (2026-10-04)
            with collector_paused():
                result = build_pack(arc, mods, build_id, text_arc, cache, rmod_units) if mods else BuildResult()
                if not mods and rmods:  # .rmod mods only: our build's looks at the unit data they leave (far
                    rmod_far_upgrades(arc, build_id, cache, result, rmod_units)  # upgrades; the unit models)
                if result.model_changed and text_arc is None:  # (FORCE_LOAD off, the old way: copies go there, also
                    text_path, text_arc = zz_path, open_pack(zz_path)  # an .rmod mod's units' beside mods of ours)
        except ResolveError as exc:
            raise BuildError(f"load order: {exc}") from None
        if run:
            first = [m.id for m in rmods]
            result.order = first + [i for i in result.order if i not in first]
            result.findings = overwrites + run.findings + result.findings
        say("load order: " + " -> ".join(result.order))
        for line in report_lines(result.findings, show_all=show_all):
            say(line)

        counts_said: list = []

        def counted() -> None:
            """The report's count of the build's findings, every one: said when the build stops on errors, else once
            the maps' and the missions' findings are in too (the review of 95e9b910, 2026-11-14: the count, said here
            before them, missed the missions' warnings, which the six's warning used to be counted with); a build
            that stops later on an error raised in its work (a map's BuildError) says it as it stops, as it did."""
            counts_said.append(True)
            counts = {lvl: sum(1 for f in result.findings if f.level == lvl) for lvl in ("error", "warning", "note")}
            say(f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['note']} note(s)")
        stack.callback(lambda: counts_said or counted())   # (said once, whichever way the build ends from here)
        if result.errors:
            counted()
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
        generated: set = set()  # new maps (lower case) whose ground is drawn as our own (map.toml ground; groundgen)
        sized: dict = {}        # new maps (lower case) given a size of their own -> (cells across, down) (bigmap)
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
                base_pack = open_pack(source)
                if spec.size:  # a blank map of its own size (map.toml size): its copied files grown to it (bigmap)
                    from .bigmap import BigMapError, Resized, grow_clone, grow_pack
                    from .newmap import CLOUDS_OFF
                    cx, cy = spec.size
                    try:
                        members, facts, pack_notes = grow_pack(base_pack, cx, cy)
                        bigger = cx * cy > facts["cells"]
                        room = spec.room or ("out" if bigger else "kept")
                        clouds = spec.clouds if spec.clouds is not None else (CLOUDS_OFF if bigger else None)
                        clone.notes += [f"size {cx} x {cy} cells: {note}" for note in pack_notes + grow_clone(
                            clone, reading(result.changed, glad_new, arc), cx, cy, clouds, room)]
                    except ImportError:
                        # not a game rule: the apps carry numpy, a plain Python build hasn't it
                        result.findings.append(Finding("error", f"{mod_id}: maps/{name}: its size ({cx} x {cy} "
                                                                f"cells) needs numpy, which this Python hasn't got"))
                        continue
                    except (BigMapError, ValueError, KeyError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{mod_id}: maps/{name}: it can't be made {cx} x {cy} "
                                                                f"cells ({exc})"))
                        continue
                    base_pack = Resized(base_pack, members)
                    sized[name.lower()] = spec.size
                owner = next((m for m, _ops in mods if m.id == mod_id), None)
                found = next((v for k, v in getattr(owner, "missions", {}).items() if k.lower() == name.lower()), None)
                if found is not None:  # its own mission (maps/<map>/mission.toml)
                    rows = [r for mod_id_ in result.order for m, _ops in mods if m.id == mod_id_  # (load order, as
                            for k, rs in m.scenario.items() if k.lower() == name.lower() for r in rs]  # applied)
                    if not _make_mission(result, clone, found, mod_id, rows, game, text_arc,
                                         reading(data_new, data_base), say):
                        continue
                for member, data in clone.glad_changed.items():
                    e = arc.entry(member)
                    for old in [m for m in result.changed if m.lower() == member.lower()]:
                        del result.changed[old]
                    result.changed[e.path if e is not None else member] = data
                for member, data in clone.texts.items():
                    e = text_arc.entry(member)
                    result.text_changed[e.path if e is not None else member] = data
                result.new_files.update(clone.zz_new)  # its own menu pictures (map.toml picture)
                glad_new.update(clone.glad)
                data_new.update(clone.data)
                path = Path(game) / "Maps" / "PC" / pack_file(name)
                new_packs[path] = NewPack(base_pack, clone.pack_id, source.name)
                new_paths[name.lower()] = path
                sources[name.lower()] = clone.map_folder
                if spec.ground == "generated":
                    generated.add(name.lower())
                result.new_maps[name] = clone
                say(f"new map: {name}, from {mod_id}")
                for note in clone.notes:
                    say(f"  {note}")
            if glad_new:
                arc = Grown(arc, glad_new)
        shipped_pictures = _shipped_menu_pictures(result, mods, arc, text_arc, {n.lower() for n in making}, say)

        def find_map(name: str):
            """A map's pack: a new map's (the path its copy gets), else the game's; None when it has none."""
            return new_paths.get(name.lower()) or find_pack(game, pack_file(name))
        map_packs = []  # (path, open pack, {member: new bytes})
        flooded: dict = {}  # map pack name -> (nav.Block over each new water, the mods' ids)
        beds: dict = {}     # map pack name -> (nav.Block opens over each dried bed, the mods' ids)
        filled_hollows: dict = {}  # map pack name -> (mend.Filled: riverbeds the edits raised flat, the mods' ids)
        from .roadnet import take_out_of
        bridges_out = {name.lower() for name, (rows, _ids) in scenario_edits(result.order, mods, "take_out").items()
                       if take_out_of(rows).bridges}  # maps whose own bridges go (roads.toml take_out)
        ends_kept: dict = {}  # (the scenery descriptors, read once for the bridges' ends)

        def bridge_ends(read, name) -> list:
            """The two ends of each of the map's own bridges, (x, y), where the strokes leave the ground at its height
            (terrain_edit.edit_map's keep: the game rests a bridge on the ground under its ends); none when the mods
            take them out or the map starts blank (its scenery erased), or when its scenery can't be read (the strokes
            then move the ground there as before)."""
            from .newmap import is_blank
            if name.lower() in bridges_out or any(n.lower() == name.lower() and is_blank(spec)
                                                  for n, (spec, _m) in making.items()):
                return []
            from .bridges import model_length, shipped_bridges
            from .scenery import MEMBER as SCENERY, Scenery, SceneryError, descriptors
            raw = read(SCENERY)
            if raw is None:
                return []
            try:
                if "descs" not in ends_kept:
                    ends_kept["descs"] = descriptors(arc)
                descs, lengths = ends_kept["descs"], ends_kept.setdefault("lengths", {})

                def length_of(kind):
                    if kind not in lengths:
                        lengths[kind] = model_length(game, descs, kind)
                    return lengths[kind]
                decks = [b.deck for b in shipped_bridges(Scenery(raw), descs, length_of)]
            except (SceneryError, ValueError, KeyError, struct.error, zlib.error):
                return []
            return [p for x0, y0, x1, y1 in decks for p in ((x0, y0), (x1, y1))]
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

            def make_ground(read=read, depth=depth_of, map_arc=map_arc, map_path=map_path, name=name, strokes=strokes,
                            ids=ids) -> dict | None:
                """The map's new ground: its files, the lines said about it, the new water's blocks and the drained
                beds' circles, the filled hollows, warnings. None after an error (said in the findings)."""
                drawn, why = name.lower() in generated, None
                if drawn:  # a new map whose ground is drawn as our own (map.toml ground = "generated")
                    from .groundgen import GroundGenError, generate
                    try:
                        changed_members, notes = generate(read, strokes, name, depth())
                    except (GroundGenError, struct.error, zlib.error) as exc:
                        drawn, why = False, str(exc)
                if not drawn:
                    try:
                        changed_members, notes = edit_map(read, strokes, name, max_depth_of=depth,
                                                          keep=bridge_ends(read, name))
                    except (ValueError, struct.error, zlib.error) as exc:
                        result.findings.append(Finding("error", f"{map_path.name}: its ground files can't be read ({exc})"))
                        return None
                made = {"members": changed_members, "lines": [f"  {note}" for note in notes], "zones": [],
                        "beds": [], "filled": None, "warnings": [], "drawn": drawn}
                if why:
                    made["warnings"].append(f"{', '.join(ids)}: {name}: ground = \"generated\" asks for its ground drawn "
                                            f"as our own, but {why}: it was made the usual way, the map's own ground "
                                            f"moved by the strokes")
                from .terrain_edit import FILES as GROUND, _area_of
                before = read(GROUND["highdef"]) if GROUND["highdef"] in changed_members else None
                if before is None:
                    return made
                # the level-build state database marks water, and the game draws no scenery on it: drained ground
                # made land, new water made water (rusemod.statedb; the blank farm's fields on D-Day's drained sea
                # drew nothing, 2026-10-16)
                from .statedb import MEMBER as STATE, with_water
                from .tms import Tms
                state = read(STATE)
                if state is not None:
                    try:
                        # a ground drawn as our own is all new: the water marks follow it everywhere (the copied
                        # map's shore cells mean nothing there); an edited one keeps Eugen's where it didn't change
                        new_state, dried, flooded = with_water(state, Tms(changed_members[GROUND["highdef"]]),
                                                               None if drawn else Tms(before))
                    except ImportError:  # the apps carry numpy; plain Python builds on without this step
                        made["warnings"].append(f"{', '.join(ids)}: {name}: its level-build state (output.sdb) "
                                                f"needs numpy to be redrawn: scenery on drained ground may not show")
                    except (ValueError, struct.error, IndexError) as exc:
                        made["warnings"].append(f"{', '.join(ids)}: {name}: its level-build state (output.sdb) "
                                                f"couldn't be read ({exc}): scenery on drained ground may not show")
                    else:
                        if dried or flooded:
                            changed_members[STATE] = new_state
                            made["lines"].append(f"  {name}: level-build state (output.sdb): {dried:,} cell(s) of "
                                                 f"drained ground made land, {flooded:,} of new water made water, so "
                                                 f"scenery shows on the new land")
                # ground under water is never walkable on a shipped map: new water is blocked
                from .bridges import Water
                from .nav import water_blocks
                from .tms import Tms
                try:
                    now_at = Water(Tms(changed_members[GROUND["highdef"]])).at
                    thin = [s for s in strokes if s.brush == "water" and not s.block]
                    if thin:  # a thin layer (block = false): its place is dry ground to units, under the water drawn
                        now_at = (lambda x, y, wet=now_at, thin=thin:
                                  wet(x, y) and not any(s.covers(x, y) for s in thin))
                        made["lines"].append(f"  {name}: {len(thin)} water stroke(s) units go under (block = false): "
                                             f"the movement takes their place for dry ground")
                    wide: list = []  # zones over the wide stretches of a dried bed (a lake, a sea)
                    zones, drained = water_blocks(Water(Tms(before)).at, now_at, [_area_of(s) for s in strokes],
                                                  wide, max(BED_RADII), BED_MOST)
                except (ValueError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: where the terrain edits put "
                                                            f"water can't be worked out ({exc}), so units could walk "
                                                            f"on the bed of new water"))
                    return {**made, "failed": True}  # its lines are said, as before; the map isn't changed
                if zones:
                    made["zones"] = list(zones)
                    made["lines"].append(f"  {name}: {len(zones)} block(s) over the new water, so units keep out of it")
                if drained:  # a dried bed: the map's movement has no ground there, so it's opened to units
                    made["beds"] = list(_bed_circles(drained, now_at, wide))
                    mx, my = (sum(p[k] for p in drained) / len(drained) for k in (0, 1))
                    made["lines"].append(f"  {name}: water drained around ({mx:.0f}, {my:.0f}): its bed opened to "
                                         f"units ({len(made['beds'])} circle(s))")
                if drawn:  # drawn as our own from a map flattened all over: no old riverbed left to mend
                    return made
                # a riverbed raised flat still shows its old banks: up close the river's rock stickers and the low
                # cover laid for it, from high up the banks painted in the picture (TESTS.md T27). Its pictures are
                # mended from both banks here, its low cover taken off with the scenery below (T28: "purple wins")
                from .mapkeep import plain_file
                from .mend import mend_map
                try:
                    filled, more = mend_map(read, lambda m, a=map_arc: a.find(m).path, changed_members, Tms(before),
                                            Tms(changed_members[GROUND["highdef"]]), [_area_of(s) for s in strokes],
                                            cache, pack_file=plain_file(map_arc))
                except (ValueError, KeyError, struct.error, zlib.error) as exc:
                    made["warnings"].append(f"{', '.join(ids)}: {name}: the riverbeds the terrain edits fill can't "
                                            f"be mended ({exc}): they keep their old banks' look")
                    filled, more = None, []
                made["lines"] += [f"  {name}: {note}" for note in more]
                made["filled"] = filled
                return made

            # a map reshaped the same way as in an earlier build: its ground as that build made it (rusemod.mapkeep;
            # a map flattened across kilometres takes many minutes to make)
            from . import mapkeep
            keep_key = None
            if cache is not None:
                try:
                    depth = depth_of()
                    size_tag = "|{}x{}".format(*sized[name.lower()]) if name.lower() in sized else ""
                    keep_key = mapkeep.key(name + ("|generated" if name.lower() in generated else "") + size_tag
                                           + ("|bridges-out" if name.lower() in bridges_out else ""),  # (their ends
                                           mapkeep.pack_identity(map_arc, map_path), strokes, depth)  # kept or not)
                except Exception:  # noqa: BLE001 - nothing to tell it by: the map is made as before, and not kept
                    keep_key = None
            made = mapkeep.read(cache, keep_key)
            if made is None:
                made = make_ground()
                if made is None:
                    continue
                if not made["warnings"] and not made.get("failed"):
                    mapkeep.write(cache, keep_key, made)
            say(f"terrain: {name}, from {', '.join(ids)}")
            # (a map whose own bridges go: their floors are sunk with them, so a stroke at one leaves nothing in the air)
            for line in without_floor_notes(made["lines"]) if name.lower() in bridges_out else made["lines"]:
                say(line)
            if made.get("failed"):
                continue
            result.findings += [Finding("warning", w) for w in made["warnings"]]
            from .nav import Block
            if made["zones"]:
                flooded[name] = ([Block(x, y, r, "all") for x, y, r in made["zones"]], ids)
            if made["beds"]:
                beds[name] = ([Block(x, y, r, "all", True, True) for x, y, r in made["beds"]], ids)
            if made["filled"] is not None:
                filled_hollows[name] = (made["filled"], ids)
            changed_members = made["members"]
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
        cliff_areas = scenario_edits(result.order, mods, "cliffs")  # ([[cliffs]]: laid with the map's scenery)
        cliff_shapes: dict = {}   # their scans' shapes, read once
        for name, (_areas, ids) in cliff_areas.items():
            _every, who = placed.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        road_edits = scenario_edits(result.order, mods, "roads")
        from .bridges import BridgeError, model_length, placed_spans, plan
        crossings_out = {name: ids for name, (rows, ids) in scenario_edits(result.order, mods, "take_out").items()
                         if take_out_of(rows).crossings}  # maps whose old bridges' crossings close too (take_out)
        from .scenery import MEMBER as SCENERY, Scenery, SceneryError, descriptors
        descs, lengths = None, {}

        def length_of(kind):
            if kind not in lengths:
                lengths[kind] = model_length(game, descs, kind)
            return lengths[kind]
        for name in sorted(set(road_edits) | set(placed) | set(crossings_out), key=str.lower):
            map_roads, road_ids = road_edits.get(name, ([], []))
            objects_here, object_ids = placed.get(name, ([], []))
            wanted = [r.points for r in map_roads if r.bridges]
            if descs is None and (wanted or objects_here or name in crossings_out):
                descs = descriptors(arc)
            by_hand = [o for o in objects_here if o.type in descs and descs[o.type].bridge] if descs else []
            map_path = find_map(name) if wanted or by_hand or name in crossings_out else None
            if map_path is None:
                continue  # (a missing map is said with the road network and the scenery below)
            ids = list(dict.fromkeys(road_ids + (object_ids if by_hand else []) + crossings_out.get(name, [])))
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
            closed_here = []
            if name in crossings_out:  # take_out "crossings": every old bridge's deck closed too (bridges.old_crossings)
                from .bridges import Water, old_crossings, shipped_bridges
                from .tms import Tms
                try:
                    sc_raw, mesh = read_map(SCENERY), read_map("output\\highdef.tms")
                    if sc_raw is None or mesh is None:
                        raise BridgeError("the map has no scenery or no ground mesh")
                    water_here = made.water if wanted else Water(Tms(mesh))
                    closed_here, shut = old_crossings(shipped_bridges(Scenery(sc_raw), descs, length_of), water_here,
                                                      spans, made.hide if wanted else [])
                except (BridgeError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the old bridges' crossings can't "
                                                            f"be closed ({exc})"))
                    continue
                if closed_here:
                    bridge_closed[name] = bridge_closed.get(name, []) + closed_here
                    notes.append(f"{shut} old bridge deck(s) over water closed to units and cut from the road network "
                                 f"(take_out crossings): nothing crosses where they stood")
                else:
                    notes.append("take_out crossings: no old bridge deck over water to close")
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
            if closed_here and name not in bridge_spans:  # nothing new to open, old decks to close
                bridge_spans[name] = []
                bridge_roads[name] = [r.points for r in map_roads]
                bridge_water[name] = water_here.at
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
        copying = scenario_edits(result.order, mods, "copy")  # the map's own ground detail laid again ([[copy]])
        for name, (_areas, ids) in copying.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        brushing = scenario_edits(result.order, mods, "fields")  # the field brush's dabs ([[fieldbrush]])
        for name, (_dabs, ids) in brushing.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        sectioning = scenario_edits(result.order, mods, "sections")  # copied once, placed many times ([[section]])
        for name, (_rows, ids) in sectioning.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        brush_paint: dict = {}  # map pack name -> the field brush's picture stamps, for the paint step
        take_outs = {name: (take_out_of(rows), ids)  # the map's own roads and bridges taken out (roads.toml take_out)
                     for name, (rows, ids) in scenario_edits(result.order, mods, "take_out").items()}
        for name, (_what, ids) in take_outs.items():
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        from .brush import PAINT_KINDS
        painting = scenario_edits(result.order, mods, "paint")  # Map Paint: what hides it up close goes (`clear`)
        for name, (strokes, ids) in painting.items():  # (and the game's own decals laid over game textures)
            if any(s.kind.kind in PAINT_KINDS and (s.clear or (s.kind.kind == "texture" and s.decals))
                   for s in strokes):
                every, who = with_pieces.setdefault(name, ([], []))
                who.extend(i for i in ids if i not in who)
        repaints = scenario_edits(result.order, mods, "repaint")   # (rusemod.repaint: under the rest of the paint,
        # over a blank map's one-colour coat; its rock with the map's own 3D rocks, rusemod.rocks)
        ground_strokes = terrain_edits(result.order, mods) if repaints else {}
        ruled_kept: dict = {}  # map pack name -> repaint's strokes and words (repaint.expand), made once: the rocks
        for name, (rows, ids) in repaints.items():  # over its rock (the scenery) and the paint both use them
            if any(r.rocks for r in rows):
                every, who = with_pieces.setdefault(name, ([], []))
                who.extend(i for i in ids if i not in who)

        def ruled_for(name: str, map_arc, done: dict) -> tuple[list, str]:
            """Repaint's strokes on map `name` and what it did in words, from its pack and its members built so far
            (`done`: the ground as shaped)."""
            e = map_arc.find("output\\highdef.tms")
            old = bytes(map_arc.read(e))
            new = done.get(e.path) or old
            if name not in ruled_kept or ruled_kept[name][0] != new:   # (made again if the ground changed since)
                from .repaint import expand, start_level
                shaped = ground_strokes.get(name, ([], []))[0]
                ruled_kept[name] = (new, expand(repaints[name][0], old, new,
                                                [s for s in shaped if s.kind.kind == "water"],
                                                start_level(shaped, old)))
            return ruled_kept[name][1]
        for name, (_filled, ids) in filled_hollows.items():  # riverbeds raised flat: their low cover goes (T28)
            every, who = with_pieces.setdefault(name, ([], []))
            who.extend(i for i in ids if i not in who)
        low_sizes: dict = {}  # type name -> how far it reaches at size 1 (stickers, low plants, stones), once a build
        decal_kept: dict = {}  # "types": the game's decal types by the texture they lay (groundtex.decal_types), once
        section_stickers: dict = {}  # map pack name -> the stickers its sections lay: (x, y, half, turn, texture)
        solid: dict = {}  # map pack name -> (nav.Block for each placed building, the mods' ids)
        lights_out: dict = {}  # map pack name -> (where its erased lighthouses stood, the mods' ids)
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
            from .scenery import (LOW_COVER, MEMBER, SceneryEditError, SceneryError, add_objects, bury_objects,
                                  erase_objects)
            areas, erase_ids = erasing.get(name, ([], []))
            try:
                member = map_arc.find(MEMBER).path
                raw = changed_members.get(member) or bytes(map_arc.read(map_arc.find(MEMBER)))
                copied, copy_notes = [], []
                copy_areas = list(copying.get(name, ([], []))[0])
                if name in brushing:  # the field brush, from the map's own fields as it comes in
                    from .scenery import Scenery as _Scenery
                    from .scenery import FieldCopy, expand_field_brush, expand_field_copy, look_library, own_fields
                    from .groundtex import decal_types
                    looks, here = look_library(), _Scenery(raw)
                    # each sticker type's own square (the decor sets' MaxExtent): a field's shape is its stickers'
                    halves = {d.name: d.half for ds in decal_types(arc).values() for d in ds}
                    areas = list(areas)
                    dabs = [d for d in brushing[name][0] if not isinstance(d, FieldCopy)]
                    field_copies = [d for d in brushing[name][0] if isinstance(d, FieldCopy)]
                    field_buildings = None   # each building type's model box and the gap crops keep from it
                    if dabs or field_copies:   # (and what stood on one a field copy leaves behind)
                        from .scenery import building_table
                        if descs is None:
                            descs = descriptors(arc)
                        try:
                            from .models import Library
                            model_lib = Library(game)
                        except OSError:   # (no mesh packs to read: no building kept clear)
                            model_lib = None
                        if model_lib is not None:
                            try:
                                field_buildings = building_table(here.names, descs, model_lib.box)
                            finally:
                                model_lib.close()
                    for k, fc in enumerate(field_copies, 1):
                        c_erases, c_copies, c_stamps, c_notes = expand_field_copy(fc, here, group=2000 + k,
                                                                                  halves=halves,
                                                                                  buildings=field_buildings)
                        areas += c_erases
                        copy_areas += c_copies
                        brush_paint.setdefault(name, ([], brushing[name][1]))[0].extend(c_stamps)
                        copy_notes += c_notes
                    for k, dab in enumerate(dabs, 1):
                        if dab.look not in looks:  # not a game rule: the look is the Studio's own library's
                            raise SceneryEditError(f"{', '.join(brushing[name][1])}: field brush {k}: there's no "
                                                   f"look called {dab.look!r} (the looks: {', '.join(sorted(looks))})")
                    # a field two dabs touch is the later one's; nothing one dab changes is laid back by another
                    own, changed = own_fields(dabs, looks, here, halves)
                    relaid: set = set()   # a neighbour sticker two dabs' erases take is laid back once
                    # (no picture given: a stamp per row sticker. The painted outline from the picture's colour,
                    # scenery.field_outline, held only 64% of an uneven field's squares on D-Day, 2026-10-15: whole
                    # parts kept their old paint; off until it follows the painted boundary lines)
                    field_picture = None
                    # each dab's PARCEL: the ground the map's own paint and borders give the field under it (the owner,
                    # 2026-10-15: R's paint over E's corner, W's trees, Q's corner spot; rusemod.parcels); a later dab's
                    # ground is the later dab's. Without numpy or the map's picture: the fields' squares, as before.
                    ground, dab_parcels = None, [None] * len(dabs)
                    if dabs:
                        try:
                            from .groundpaint import map_bounds
                            from .parcels import FieldGround, subtract
                            from .scenery import _facing, brush_fields
                            from .tmst import Tmst
                            hd_store = Tmst(bytes(map_arc.read(map_arc.find("output\\highdef.tmst_pc"))),
                                            bytes(map_arc.read(map_arc.find("output\\highdef.tmst_chunk_pc"))))
                            ground = FieldGround(here, hd_store,
                                                 map_bounds(bytes(map_arc.read(map_arc.find("output\\highdef.tms")))),
                                                 descs)
                        except (ImportError, KeyError, ValueError):
                            ground = None
                    if ground is not None:
                        for k, dab in enumerate(dabs):
                            squares = [(m[3], m[7], h, math.radians(_facing(m)))
                                       for f in brush_fields(dab, looks[dab.look], here, halves) for _s, m, _mk, h in f]
                            dab_parcels[k] = ground.parcel(dab.footprint(), squares)
                        for k in range(len(dabs)):
                            for j in range(k + 1, len(dabs)):
                                if dab_parcels[k] is not None and dab_parcels[j] is not None:
                                    subtract(dab_parcels[k], dab_parcels[j])
                    for k, dab in enumerate(dabs, 1):
                        b_erases, b_objects, b_copies, b_stamps, b_notes = expand_field_brush(
                            dab, looks[dab.look], here, group=1000 + k, halves=halves, fields=own[k - 1],
                            changed=changed, relaid=relaid, picture=field_picture, buildings=field_buildings,
                            descs=descs, parcel=dab_parcels[k - 1], ground=ground,
                            others=[p for j, p in enumerate(dab_parcels) if j != k - 1 and p is not None])
                        areas += b_erases
                        copied += b_objects
                        copy_areas += b_copies
                        brush_paint.setdefault(name, ([], brushing[name][1]))[0].extend(b_stamps)
                        copy_notes += b_notes
                if copy_areas:  # read from the scenery as it comes in: before this build erases anything
                    from .scenery import copy_objects
                    if descs is None:
                        descs = descriptors(arc)
                    sources: dict = {}   # another map's shipped scenery a preset's tiles come from
                    for area in copy_areas:
                        if area.source and area.source not in sources:
                            src_path = find_map(area.source)
                            if src_path is None:  # not a game rule: a file the preset reads isn't there
                                raise BuildError(f"{', '.join(copying[name][1])}: the ground preset's map "
                                                 f"{area.source} isn't in this game ({pack_file(area.source)} is "
                                                 f"missing), so its tiles can't be read")
                            src_arc = next((e[1] for e in map_packs if e[0] == src_path), None) or open_pack(src_path)
                            sources[area.source] = bytes(src_arc.read(src_arc.find(MEMBER)))
                    more, more_notes = copy_objects(raw, copy_areas, descs, sources)
                    copied, copy_notes = copied + more, copy_notes + more_notes
                section_objs: list = []   # [[section]]: (name, its objects about its middle, its places), copied
                if name in sectioning:    # from the scenery as it comes in, placed after the objects (add_sections)
                    from .scenery import copy_objects
                    if descs is None:
                        descs = descriptors(arc)
                    s_sources: dict = {}
                    for s in sectioning[name][0]:
                        if s.source and s.source not in s_sources:
                            src_path = find_map(s.source)
                            if src_path is None:  # not a game rule: a file the section reads isn't there
                                raise BuildError(f"{', '.join(sectioning[name][1])}: section {s.name}'s map "
                                                 f"{s.source} isn't in this game ({pack_file(s.source)} is "
                                                 f"missing), so it can't be copied")
                            src_arc = next((e[1] for e in map_packs if e[0] == src_path), None) or open_pack(src_path)
                            s_sources[s.source] = bytes(src_arc.read(src_arc.find(MEMBER)))
                    listed = 0
                    for k, s in enumerate(sectioning[name][0], 1):
                        if s.objects:   # made elsewhere (a mod's generated dressing): its objects as listed
                            section_objs.append((s.name, s.new_objects(), s.places))
                            listed += 1
                            continue
                        # its own group: the whole square comes (the fill rule thins nothing of it)
                        got, _said = copy_objects(raw, [s.copy_area(group=5000 + k)], descs, s_sources)
                        section_objs.append((s.name, got, s.places))
                        copy_notes = copy_notes + [f"section {s.name}: {len(got):,} object(s) copied from "
                                                   f"({s.sx / 260:.0f} m, {s.sy / 260:.0f} m)"
                                                   + (f" on {s.source}" if s.source else "")
                                                   + f", to go at {len(s.places):,} place(s)"]
                    if listed:
                        copy_notes = copy_notes + [f"{listed} section(s) with their objects listed in the mod"]
                if any(LOW_COVER in a.types for a in areas):  # a preset's replace: the map's low plants and stones
                    from dataclasses import replace as _with
                    from .scenery import low_cover
                    if descs is None:
                        descs = descriptors(arc)
                    low = tuple(low_cover(descs, set(Scenery(raw).names)))
                    areas = [_with(a, types=tuple(t for t in a.types if t != LOW_COVER) + low)
                             if LOW_COVER in a.types else a for a in areas]
                raw, sunk = bury_objects(raw, bridge_hide.get(name, []))  # before the new blocks move them
                sunk = copy_notes + sunk
                gone_what = take_outs.get(name, (None, []))[0]
                if gone_what is not None and (gone_what.roads or gone_what.bridges):
                    # the map's own roads (their pieces, drawn from far; their stickers, up close) and bridges out,
                    # before the new objects go in: a new road's stickers and a new bridge stay
                    from .scenery import ERASE_MAX, EraseArea, road_stickers, take_out_road_pieces
                    from .tms import Tms
                    if gone_what.roads:
                        raw, more = take_out_road_pieces(raw)
                        sunk = sunk + more
                    if descs is None:
                        descs = descriptors(arc)
                    here = Scenery(raw).names
                    types = (road_stickers(here, descs) if gone_what.roads else []) + (
                        [n for n in here if n in descs and descs[n].bridge] if gone_what.bridges else [])
                    ground_raw = changed_members.get(map_arc.find("output\\highdef.tms").path) \
                        or bytes(map_arc.read(map_arc.find("output\\highdef.tms")))
                    gx0, gy0, _gz0, gx1, gy1, _gz1 = Tms(ground_raw).bounds
                    if types:   # one square over all of the map, as the Studio's Erase the whole map makes it
                        areas = list(areas) + [EraseArea((gx0 + gx1) / 2, (gy0 + gy1) / 2,
                                                         min(ERASE_MAX, max(gx1 - gx0, gy1 - gy0) / 2 + 1000), (),
                                                         tuple(types), shape="square")]
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
                objects = list(objects) + dressed + copied
                sizes = None  # an erase by size (Map Paint's clearing, filled riverbeds): how far each type reaches
                strokes = painting.get(name, ([], []))[0]
                from .scenery import low_cover, model_reach, sticker_reach
                names_read: list = []

                def map_names() -> list:
                    """The map's type names, its scenery read once (whole, for them) for the paint, the riverbeds and
                    the erase: `raw` stays as it is until the erase."""
                    if not names_read:
                        names_read.append(Scenery(raw).names)
                    return names_read[0]

                def reach_of(low):
                    """How far each of the map's low types reaches (measured once a build)."""
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
                    return low_sizes
                if any(s.kind.kind in PAINT_KINDS and s.clear for s in strokes):
                    # up close the game draws the map's stickers, low plants and stones over the ground's picture:
                    # only with them taken off does the paint show near the camera (TESTS.md T21, T26)
                    from .groundpaint import paint_clearing
                    if descs is None:
                        descs = descriptors(arc)
                    low = low_cover(descs, set(map_names()))
                    under = paint_clearing(strokes, low)
                    if under:
                        areas = list(areas) + under
                        sizes = reach_of(low)
                        sunk = sunk + [f"Map Paint: what hides it up close taken off under {len(under)} stroke(s) "
                                       f"(ground stickers, low plants and stones reaching where it is at least half "
                                       f"strength; trees, buildings, cover and movement unchanged)"]
                beds_area = []  # the filled riverbeds' clearing: the build's own, so it gives way when the map is full
                if name in filled_hollows:
                    # a riverbed raised flat: the river's rock stickers make jagged rock on it up close (T27), and
                    # the field it becomes shows only with all its low cover gone (T28: "purple wins")
                    from .scenery import EraseArea
                    if descs is None:
                        descs = descriptors(arc)
                    low = low_cover(descs, set(map_names()))
                    filled = filled_hollows[name][0]
                    fx0, fy0, fx1, fy1 = filled.box()
                    beds_area = [EraseArea((fx0 + fx1) / 2, (fy0 + fy1) / 2, max(fx1 - fx0, fy1 - fy0) / 2,
                                           ("decal",), tuple(low), shape="square", by_size=True, mask=filled.touches)]
                    sizes = reach_of(low)
                erased_notes, erased = [], {}
                from .lighthouses import LIGHTHOUSE, gone, lighthouses
                towers = lighthouses(raw) if areas and any(LIGHTHOUSE.search(n) for n in map_names()) else []
                if areas or beds_area:  # the map's own scenery out first: the new objects then stay whatever the
                    if descs is None:  # areas cover
                        descs = descriptors(arc)
                    names = map_names()
                    kinds = {i: descs[n].group for i, n in enumerate(names) if n in descs}
                    bridges = {i for i, n in enumerate(names) if n in descs and descs[n].bridge}
                    try:
                        raw_after, erased_notes, erased = erase_objects(raw, list(areas) + beds_area, kinds, bridges,
                                                                        sizes)
                        if beds_area:
                            sunk = sunk + ["filled riverbeds: the ground stickers, low plants and stones reaching "
                                           "into them taken off (trees, buildings, cover and movement unchanged)"]
                    except SceneryEditError:
                        if not beds_area:
                            raise
                        # the clearing would make the map's scenery too big (all of Blitz Twin flattened: 20.8 MB of
                        # a 16.7 MB most, 2026-10-04): the riverbeds keep their low cover, the rest is erased as asked
                        result.findings.append(Finding("warning", f"{', '.join(ids)}: {name}: the filled riverbeds' "
                                                                  f"ground stickers, low plants and stones stay: taking "
                                                                  f"them off would make the map's scenery bigger than a "
                                                                  f"map can hold. Their pictures are mended all the "
                                                                  f"same"))
                        raw_after, erased_notes, erased = (erase_objects(raw, areas, kinds, bridges, sizes)
                                                           if areas else (raw, [], {}))
                    raw = raw_after
                    erased_towers = gone(towers, lighthouses(raw)) if towers else []
                    if erased_towers:  # their lights go with them (rusemod.lighthouses), once every map's scenery
                        lights_out[name] = (erased_towers, ids)  # is done
                laid_decals = 0
                if any(s.kind.kind == "texture" and s.decals and s.texture.startswith("game:") for s in strokes):
                    # up close: the game's own decals of the game textures painted, laid over the ground they paint
                    # (groundtex.decal_grid), as many as the map's scenery has room for; not tried in the game yet
                    from .groundtex import decal_grid, decal_room, decal_types, map_sets
                    from .scenery import GRID_CELL, add_names
                    if "types" not in decal_kept:
                        decal_kept["types"] = decal_types(arc)
                    held = Scenery(raw)
                    room = decal_room(held.fields[3])
                    grid = (min(held.grid_dims[2 * k] * GRID_CELL[k] for k in range(3)),  # the scenery grid's
                            min(held.grid_dims[2 * k + 1] * GRID_CELL[k] for k in range(3)))  # width and height
                    sets = map_sets(arc, name)
                    decals, laid_how = decal_grid(strokes, decal_kept["types"], sets, seed=name, most=room, inside=grid)
                    if decals:
                        raw = add_names(raw, sorted({o.type for o in decals}))
                        objects = list(objects) + decals
                        sunk = sunk + [f"Map Paint up close: {len(decals):,} of the game's own decal(s) over the game "
                                       f"textures painted, {laid_how['step'] / 260:.0f} m apart"
                                       + (" (spread out to fit the map's scenery room)" if laid_how["thinned"] else "")
                                       + " (" + ", ".join(f"{t.split('/')[-1]} {n:,}"
                                                          for t, n in sorted(laid_how["types"].items())) + ")"]
                    elif laid_how.get("types") is not None and room == 0:
                        sunk = sunk + ["Map Paint up close: no room left in the map's scenery for the game's decals"]
                    if laid_how.get("missing"):
                        sunk = sunk + [f"Map Paint up close: no decal of "
                                       f"{', '.join(r[5:] for r in laid_how['missing'])} is loaded on this map (its "
                                       f"decor sets: {', '.join(sorted(sets)) or 'none'}), so it shows from its "
                                       f"painted ground only"]
                    laid_decals = len(decals)
                rock_strokes = strokes
                if name in repaints and any(r.rocks for r in repaints[name][0]):
                    from .repaint import RepaintError, coats
                    try:
                        ruled = ruled_for(name, map_arc, changed_members)[0]
                    except (RepaintError, KeyError, ValueError, struct.error):
                        ruled = []   # (the paint step says why)
                    shipped_ground = bytes(map_arc.read(map_arc.find("output\\highdef.tms")))
                    coat = coats(strokes, shipped_ground)
                    rock_strokes = list(strokes[:coat]) + ruled + list(strokes[coat:])
                from .rocks import is_rock
                if any(is_rock(s) for s in rock_strokes):
                    # up close: the map's own 3D rocks over the palette's rock painted (rusemod.rocks), laid to the
                    # slope, as many as the map's scenery has room for; not tried in the game yet
                    from .groundtex import DECAL_BYTES
                    from .models import Library as _Models
                    from .rocks import map_mix, rock_layer, rock_room
                    from .scenery import GRID_CELL
                    from .tms import Tms
                    if descs is None:
                        descs = descriptors(arc)
                    held = Scenery(raw)
                    placed_n = held.types()   # every name the map lists (loaded on it), how many it places
                    used = {n: placed_n.get(i, 0) for i, n in enumerate(held.names) if n}
                    grid = (min(held.grid_dims[2 * k] * GRID_CELL[k] for k in range(3)),
                            min(held.grid_dims[2 * k + 1] * GRID_CELL[k] for k in range(3)))
                    ground_now = changed_members.get(map_arc.find("output\\highdef.tms").path) \
                        or bytes(map_arc.read(map_arc.find("output\\highdef.tms")))
                    shapes = _Models(game)
                    try:
                        def box_of(t, shapes=shapes):
                            d = descs.get(t)
                            first = (d.models or ((d.model,) if d.model else ())) if d is not None else ()
                            return shapes.box(first[0]) if first else None
                        rocks, rocks_how = rock_layer(rock_strokes, Tms(ground_now), used, box_of, seed=name,
                                                      most=rock_room(held.fields[3], laid_decals * DECAL_BYTES),
                                                      inside=grid)
                    finally:
                        shapes.close()
                    if rocks:
                        objects = list(objects) + rocks
                        sunk = sunk + [f"Map Paint up close: {len(rocks):,} of the map's own 3D rocks over the rock "
                                       f"painted, laid to its slope"
                                       + (" (thinned to fit the map's scenery room)" if rocks_how["thinned"] else "")
                                       + " (" + ", ".join(f"{t.split('/')[-1]} {n:,}"
                                                          for t, n in sorted(rocks_how["types"].items())) + ")"]
                    elif not any(map_mix(used).values()):
                        sunk = sunk + ["Map Paint up close: this map places none of the game's rocks, so its painted "
                                       "rock gets no 3D rocks (a type from another theatre isn't loaded on it)"]
                if name in cliff_areas:
                    # cliff faces of rock scans ([[cliffs]], rusemod.cliffs) on the ground as built; not tried in the
                    # game yet
                    from .cliffs import cliff_layer
                    from .scenery import GRID_CELL
                    from .tms import Tms
                    held = Scenery(raw)
                    grid = (min(held.grid_dims[2 * k] * GRID_CELL[k] for k in range(3)),
                            min(held.grid_dims[2 * k + 1] * GRID_CELL[k] for k in range(3)))
                    ground_now = changed_members.get(map_arc.find("output\\highdef.tms").path) \
                        or bytes(map_arc.read(map_arc.find("output\\highdef.tms")))
                    areas_here = cliff_areas[name][0]
                    shapes = _asset_shapes(result.own_assets, {t for a in areas_here for t in a.types}, cliff_shapes)
                    laid, laid_said = cliff_layer(areas_here, Tms(ground_now), shapes, inside=grid)
                    if laid:
                        objects = list(objects) + laid
                        sunk = sunk + [f"cliffs: {len(laid):,} rock scan(s) on the steep ground of {len(areas_here)} "
                                       f"area(s) (" + ", ".join(f"{t.split('/')[-1]} {n:,}"
                                                                for t, n in sorted(laid_said["types"].items())) + ")"]
                    else:
                        sunk = sunk + [f"cliffs: no ground in its {len(areas_here)} area(s) steep enough for a scan"]
                    if laid_said["unknown"]:
                        result.findings.append(Finding("warning", (
                            f"{', '.join(ids)}: {name}: [[cliffs]] names {', '.join(laid_said['unknown'])}: only the "
                            f"mods' own map assets (files/assets) can make cliffs, their shape known")))
                if descs is None:
                    descs = descriptors(arc)
                lowest = _LowestPoints(game, descs)
                try:
                    objects, lowered = grounded(objects, descs, lowest)
                finally:
                    lowest.close()
                as_placed = objects  # by their own types: what the steps after go by (solid buildings, ...)
                seen = result.visibility  # placed types with no far mode: their copies, drawn from far too
                # (not an object laid at its shipped copy's levels, a [[copy]]'s: drawn exactly as the map draws it)

                def far_too(o) -> bool:
                    return getattr(o, "type", None) in seen and not getattr(o, "levels", 0)
                if seen and any(far_too(o) for o in objects):
                    from dataclasses import replace as _replace
                    from .scenery import add_names
                    swapped = sorted({o.type for o in objects if far_too(o)})
                    objects = [_replace(o, type=seen[o.type]) if far_too(o) else o for o in objects]
                    raw = add_names(raw, [seen[t] for t in swapped])
                    sunk = sunk + [f"drawn from far too (the game draws these only up close, or no further than the "
                                   f"middle distance): "
                                   f"{', '.join(t.split('/')[-1] for t in swapped)}; the mod's objects use copies of "
                                   f"them ({SEEN_SUFFIX}), the map's own stay as shipped"]
                if result.type_levels:
                    # each placed object asking for nothing asks for the levels its type is drawn at, far included, so
                    # it hangs on a block listed at them (else never drawn far: rusemod.visibility.type_levels). After
                    # grounded(), which leaves objects with levels as they are (a [[copy]]'s, laid as the map lays it)
                    from dataclasses import replace as _replace
                    asks = result.type_levels
                    objects = [_replace(o, levels=asks[o.type])
                               if getattr(o, "type", None) in asks and getattr(o, "levels", None) == 0 else o
                               for o in objects]
                if result.own_assets:  # the mods' own map assets' types (rusemod.sceneryasset): new to every map
                    from .scenery import add_names
                    from .sceneryasset import type_name
                    mine = {type_name(n) for n in result.own_assets}
                    raw = add_names(raw, sorted({o.type for o in objects if getattr(o, "type", None) in mine}))
                changed_members[member], notes = add_objects(raw, objects)
                if section_objs:   # each copied once, placed by references ([[section]])
                    from .groundtex import decal_kinds, decal_types, map_sets
                    from .scenery import add_sections
                    changed_members[member], more = add_sections(changed_members[member], section_objs)
                    notes = notes + more
                    if "types" not in decal_kept:
                        decal_kept["types"] = decal_types(arc)
                    # each sticker as the map draws it: its own theatre's definition (a new map: the copied map's)
                    sets = map_sets(arc, name) or (map_sets(arc, making[name][0].copy_of) if name in making else set())
                    kinds = decal_kinds(decal_kept["types"], sets)
                    stuck = []   # every sticker they lay, where it lies: the tint under it is fitted after the paint
                    for _n, objs, places in section_objs:
                        mine = [(o, kinds[o.type]) for o in objs if o.type in kinds]
                        for px, py, pt in places:
                            c, s = math.cos(math.radians(pt)), math.sin(math.radians(pt))
                            stuck += [(px + c * o.x - s * o.y, py + s * o.x + c * o.y,
                                       d.half * o.size * max(1.0, o.stretch), o.turn + pt, (d.colour, d.alpha))
                                      for o, d in mine]
                    if stuck:
                        section_stickers[name] = stuck
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
                        f"take buildings is opened to every unit (cleared_woods; seen in the game)")
                if any("building" not in a.what and not a.opens  # (an [[own]] row opens its building's own ground)
                       and any(t in descs and descs[t].group == "building" and not descs[t].bridge for t in a.types)
                       for a in areas):
                    result.findings.append(Finding("warning", (
                        f"{', '.join(erase_ids)}: {name}: buildings erased by name (an erase area's types) leave their "
                        f"ground closed to units: the map's movement still has them. Name \"building\" in that area's "
                        f"what to open its ground too")))
            taken_bridges = take_outs.get(name, (None, []))[0] is not None and take_outs[name][0].bridges
            if erased.get("bridge") and taken_bridges and take_outs[name][0].crossings:
                say(f"  the map's own bridges taken out: {erased['bridge']} erased, their floors sunk under the "
                    f"ground; their decks over water are closed to units and cut from the road network "
                    f"(take_out crossings)")
            elif erased.get("bridge") and taken_bridges:
                say(f"  the map's own bridges taken out: {erased['bridge']} erased, their floors sunk under the "
                    f"ground; the movement over their decks stays (units cross there, on the ground under them)")
            elif erased.get("bridge"):
                result.findings.append(Finding("warning", (
                    f"{', '.join(erase_ids)}: {name}: {erased['bridge']} of the map's bridges erased: units can still "
                    f"cross the water where they stood (the map's movement still has the decks). Leave the bridges "
                    f"out of the erase areas' types, or place a bridge there again")))
            from .nav import solid_blocks
            # by the placed types, not their far-drawn copies (rusemod.visibility), which the game's descriptors list
            # under the copies' names only: a copied building stays solid to units
            walls, wall_notes = solid_blocks(game, [o for o in as_placed if not isinstance(o, RoadPiece)])
            if result.own_assets:  # the mods' own models marked solid: units go around them too
                from .sceneryasset import solid_blocks as own_solid_blocks
                mine, mine_notes = own_solid_blocks(result.own_assets,
                                                    [o for o in as_placed if not isinstance(o, RoadPiece)])
                walls, wall_notes = walls + mine, wall_notes + mine_notes
            for note in wall_notes:
                say(f"  {note}")
            if walls:
                solid[name] = (walls, ids)
            if entry is None:
                map_packs.append((map_path, map_arc, changed_members))
            result.terrain_changed[map_path.name] = changed_members
        from .lighthouses import take_out as lights_taken_out

        def glad_member(member):
            """A ZZ_GladPatchableWin.dat member as the build has it so far (any case), or None."""
            key = member.lower()
            mine = next((d for m, d in result.changed.items() if m.lower() == key), None)
            if mine is not None:
                return mine
            e = arc.entry(member)
            return bytes(arc.read(e)) if e is not None else None
        for name, (places, ids) in lights_out.items():  # an erased lighthouse's light goes too (rusemod.lighthouses)
            try:
                changes, notes = lights_taken_out(glad_member, name, places)
            except (ValueError, KeyError, IndexError, struct.error) as exc:
                result.findings.append(Finding("warning", f"{', '.join(ids)}: {name}: the light of its erased "
                                                          f"lighthouse(s) stays: the map's effects couldn't be "
                                                          f"read ({exc})"))
                continue
            for member, data in changes.items():
                e = arc.entry(member)
                for old in [m for m in result.changed if m.lower() == member.lower()]:
                    del result.changed[old]
                result.changed[e.path if e is not None else member] = data
            if notes:
                say(f"lighthouses: {name}, from {', '.join(ids)}")
                for note in notes:
                    say(f"  {note}")
        for name, (gone_what, ids) in take_outs.items():  # the map's own roads drawn as nothing (its road model) and
            if not (gone_what.roads or gone_what.bridges):  # its bridges' floors sunk: after the scenery, before the new
                continue                                    # roads are drawn into the same files
            map_path = find_map(name)
            if map_path is None:
                continue  # (said with the scenery: the map isn't in the game)
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            done = entry[2] if entry else {}

            def read_done(member, a=map_arc, done=done):
                try:
                    e = a.find(member)
                except KeyError:
                    return None
                return done.get(e.path) or bytes(a.read(e))

            def read_shipped(member, a=map_arc):
                try:
                    return bytes(a.read(a.find(member)))
                except KeyError:
                    return None
            from . import floors
            from .roadstrips import StripError, take_out_bridges as bridges_out, take_out_roads as model_out
            notes = []
            try:
                if gone_what.roads:
                    new, more = model_out(read_done, lambda m, a=map_arc: a.find(m).path)
                    done.update(new)
                    notes += more
                if gone_what.bridges:  # the bridges model drawn as nothing (it floated over the flattened blank
                    # D-Day, 2026-10-05), their floors sunk under the ground, found on the ground they were made on
                    new, more = bridges_out(read_done, lambda m, a=map_arc: a.find(m).path)
                    done.update(new)
                    notes += more
                    from .bridges import Ground, model_length, shipped_bridges
                    from .kdt import Kdt
                    from .tms import Tms
                    if descs is None:
                        descs = descriptors(arc)
                    k_raw, shipped_ground = read_done(floors.MEMBER), read_shipped("output\\highdef.tms")
                    sc_shipped = read_shipped(SCENERY)
                    if k_raw is not None and shipped_ground is not None and sc_shipped is not None:
                        decks = [floors.Deck.of(*b.deck) for b in shipped_bridges(
                            Scenery(sc_shipped), descs, lambda kind: model_length(game, descs, kind))]
                        own_raw = read_shipped(floors.MEMBER)  # the map's own floors: every one along a gone deck
                        own = ({floors.tri_key(t) for t in floors.triangles(Kdt(own_raw))}  # goes (a mod's new
                               if own_raw is not None else None)                           # bridges keep theirs)
                        now_ground = read_done("output\\highdef.tms")  # the ground as built (a reshaped or blank
                        lay = Ground(Tms(now_ground)).height_at if now_ground is not None else None   # map's own)
                        data, more = floors.sink_floors(Kdt(k_raw), Ground(Tms(shipped_ground)).height_at, decks,
                                                        own, lay)
                        if data:
                            done[map_arc.find(floors.MEMBER).path] = data
                        notes += more
            except (StripError, floors.FloorError, SceneryError, ValueError, KeyError, struct.error, zlib.error) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the map's own "
                                                        f"{' and '.join(gone_what.names())} can't be taken out ({exc})"))
                continue
            if done:
                if entry is None:
                    map_packs.append((map_path, map_arc, done))
                result.terrain_changed[map_path.name] = done
            say(f"take out: {name}, the map's own {' and '.join(gone_what.names())}, from {', '.join(ids)}")
            for note in notes:
                say(f"  {note}")
        # a big map's movement step started now, in worker programs of its own, while its ground is painted: every
        # block and open it takes is known by now (the movement step below takes the answer only when it's the same)
        aheads = {} if result.errors else _movement_ahead(game, open_pack, result.order, mods, cache, erasing, beds,
                                                          flooded, solid, data_base, data_new)
        stack.callback(lambda: [a.close() for a in aheads.values()])

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

        library: list = []  # [the texture strokes' groundtex.Library], made once when a mod paints with a texture

        def textures():
            """The textures the mods' texture strokes lay: the game's (from ZZ_Win.dat, their repeats from the unit
            data), a square of any map's ground, or a mod's own picture (rusemod.groundtex)."""
            if not library:
                from .groundtex import Library
                zz_path = text_path or find_pack(game, loc.PACK)
                zz = text_arc if text_arc is not None else open_pack(zz_path) if zz_path else None

                def map_reader(pack):
                    where = find_map(pack)
                    if where is None:
                        return None
                    a = open_pack(where)

                    def read(member, a=a):
                        try:
                            return bytes(a.read(a.find(member)))
                        except KeyError:
                            return None
                    return read
                files = {}
                for m, _ops in mods:
                    files.update(getattr(m, "ground_pictures", None) or {})
                library.append(Library(zz, arc, map_reader, files, cache))
            return library[0]

        all_paint = scenario_edits(result.order, mods, "paint")
        for name, (stamps, ids) in brush_paint.items():  # the field brush's picture after the mods' own paint
            strokes, who = all_paint.setdefault(name, ([], []))
            all_paint[name] = (strokes + stamps, who + [i for i in ids if i not in who])
        for name, (_rows, ids) in repaints.items():   # (repaints: read with the scenery's rocks, above)
            strokes, who = all_paint.setdefault(name, ([], []))
            all_paint[name] = (strokes, who + [i for i in ids if i not in who])
        relief_pictures = scenario_edits(result.order, mods, "relief_pictures")   # (rusemod.relief: under the paint)
        for name, (_laid, ids) in relief_pictures.items():
            strokes, who = all_paint.setdefault(name, ([], []))
            all_paint[name] = (strokes, who + [i for i in ids if i not in who])
        for name, (strokes, ids) in all_paint.items():  # the Map Paint strokes,
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
            from . import mapkeep
            from .groundpaint import DETAIL, PaintError, paint_ground, paint_inputs
            from .groundtex import TextureError
            if name in relief_pictures:   # a relief's own picture, first: the rest of the paint goes over it
                from .relief import Picture, paint_pictures
                laid = relief_pictures[name][0]
                try:
                    from .repaint import coats
                    coat = coats(strokes, bytes(map_arc.read(map_arc.find("output\\highdef.tms"))))
                    if coat:   # a blank map's one-colour coat first: the relief's picture goes over it
                        coated, more = paint_ground(read_map, lambda m, a=map_arc: a.find(m).path, strokes[:coat],
                                                    cache)
                        changed_members.update(coated)
                        say(f"paint: {name}: the coat under the relief's picture: {', '.join(more)}")
                        strokes = strokes[coat:]
                    from .png import read_png
                    pictures = [Picture(s, *read_png(p.read_bytes())) for s, p in laid]
                    made_from_r = ["relief", paint_inputs(read_map)] + [
                        f"{s.relief} {hashlib.blake2b(p.read_bytes(), digest_size=16).hexdigest()} {s.x} {s.y} "
                        f"{s.radius} {s.length} {s.dx} {s.dy} {s.weight} {s.edge}" for s, p in laid]
                    relief_k = mapkeep.key(name, made_from_r, [], None) if cache is not None else None
                    kept_r = mapkeep.read(cache, relief_k, "paint")
                    if kept_r is not None and isinstance(kept_r.get("notes"), list):
                        laid_members, notes_r = kept_r["members"], ["kept from an earlier build"] + kept_r["notes"]
                    else:
                        laid_members, notes_r = paint_pictures(read_map, lambda m, a=map_arc: a.find(m).path,
                                                               pictures, cache)
                        mapkeep.write(cache, relief_k, {"members": laid_members, "notes": notes_r}, "paint")
                except (ImportError, PaintError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(relief_pictures[name][1])}: {name}: the "
                                                            f"relief's picture can't be laid ({exc})"))
                    continue
                changed_members.update(laid_members)
                say(f"relief picture: {name}, from {', '.join(relief_pictures[name][1])}: {len(laid)} picture(s)")
                for note in notes_r:
                    say(f"  {note}")
                if laid_members:
                    if entry is None:
                        map_packs.append((map_path, map_arc, changed_members))
                        entry = map_packs[-1]
                    result.terrain_changed[map_path.name] = changed_members
                if not strokes and name not in repaints:
                    continue
            if name in repaints:   # the ground the brushes moved, by its new shape, under the mods' own paint
                from .repaint import RepaintError, coats
                try:
                    old = bytes(map_arc.read(map_arc.find("output\\highdef.tms")))
                    ruled, words = ruled_for(name, map_arc, changed_members)
                except (RepaintError, KeyError, ValueError, struct.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(repaints[name][1])}: {name}: what moved "
                                                            f"can't be repainted ({exc})"))
                    continue
                coat = coats(strokes, old)   # over a blank map's one-colour coat, under the rest
                strokes = strokes[:coat] + ruled + strokes[coat:]
                say(f"repaint: {name}, from {', '.join(repaints[name][1])}: {words}")
                if not strokes:
                    continue
            swatches = None
            if any(s.kind.kind == "texture" for s in strokes):
                try:
                    swatches = textures().for_strokes(strokes)
                except (TextureError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: a texture to paint with "
                                                            f"can't be read ({exc})"))
                    continue
            # the same paint on the same ground as an earlier build: its pictures from the build cache (a map painted
            # all over takes many minutes), kept like a reshaped map (rusemod.mapkeep) but apart from the reshaped maps
            # (kind "paint": a build of three painted maps used to throw out the terrain it was about to use); a
            # texture's own pixels count
            made_from = ["paint", paint_inputs(read_map)] + sorted(f"{r} {s.digest}" for r, s in (swatches or {}).items())
            paint_k = mapkeep.key(name, made_from, strokes, None, "paint") if cache is not None else None
            kept = mapkeep.read(cache, paint_k, "paint")
            if kept is not None and isinstance(kept.get("notes"), list):   # (its notes are that build's: said so)
                painted = kept["members"]
                notes = ["kept from an earlier build of the same paint; what it said then:"] + kept["notes"]
            else:
                try:
                    painted, notes = paint_ground(read_map, lambda m, a=map_arc: a.find(m).path, strokes, cache,
                                                  swatches=swatches)
                except (PaintError, ValueError, KeyError, struct.error, zlib.error) as exc:
                    result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the paint can't be laid "
                                                            f"({exc})"))
                    continue
                mapkeep.write(cache, paint_k, {"members": painted, "notes": notes}, "paint")
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

                def shipped(member, a=map_arc):
                    try:
                        return bytes(a.read(a.find(member)))
                    except KeyError:
                        return None
                taken = name in take_outs and take_outs[name][0].roads   # (the map's own roads out: their look
                painted, notes = draw_new_roads(read_map, lambda m, a=map_arc: a.find(m).path, lines, shaded, cache,
                                                shipped if taken else None)   # is read where the map ships them)
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
        for name, stuck in section_stickers.items():   # [[section]]: the tint under their stickers, after all paint
            map_path = find_map(name)
            if map_path is None:
                continue
            entry = next((e for e in map_packs if e[0] == map_path), None)
            map_arc = entry[1] if entry else open_pack(map_path)
            changed_members = entry[2] if entry else {}
            ids = sectioning[name][1]
            if text_arc is None:   # (the stickers' own pictures are in it)
                say(f"tint: {name}: the game's texture pack wasn't given, so its sections' stickers keep the tint "
                    f"the map has under them")
                continue
            from .groundpaint import PaintError
            try:
                painted, notes = section_tint(map_arc, changed_members, stuck, text_arc)
            except (PaintError, ValueError, KeyError, struct.error, zlib.error) as exc:
                result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the tint under its sections' "
                                                        f"stickers can't be fitted ({exc})"))
                continue
            changed_members.update(painted)
            say(f"tint: {name}, from {', '.join(ids)}")
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
        from .newmap import is_blank
        for name, (spec, mod_id) in making.items():  # a blank map: its old towns' and bridges' own movement opened
            if not is_blank(spec) or name not in result.new_maps:  # whole (T41 run 4: units stuck where the bridges
                continue                                           # stood; their decks' local maps kept them in)
            from .cover import member as movement_member
            from .nav import Block, NavError, owner_circles
            raw = reading(data_new, data_base)(movement_member(name)) if data_base is not None else None
            try:
                owners = owner_circles(raw) if raw is not None else []
            except (NavError, ValueError, KeyError, IndexError, struct.error):
                owners = []
            if owners:
                every, who = blocks.setdefault(name, ([], []))
                every.extend(Block(x, y, r, "all", True, True) for x, y, r in owners)
                who.extend([mod_id] if mod_id not in who else [])
                say(f"  {name}: blank: {len(owners)} town or bridge circle(s) opened whole (not tried in the game yet)")
        players = scenario_edits(result.order, mods, "players")
        roads_out = {name: ids for name, (what, ids) in take_outs.items() if what.roads}
        depots, depot_ids = depot_rules(result.order, mods)
        if (moves or paints or blocks or new_roads or bridge_spans or players or data_new or roads_out or depots
                or result.look_symbols):
            from .bridges import BridgeError, apply_spans
            from .cover import CoverError, apply_paints
            from .nav import NavError, closing
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
                if depots:  # depots.toml: every depot's trucks on the maps named or on every map, written as each
                    # depot's own trucks changed (before the mods' own changes, which win: scenario.with_depots)
                    from .scenario import ALL_MAPS, depot_rule, map_packs_of, of_map, with_depots
                    packs = map_packs_of(data_arc) if ALL_MAPS in depots else []
                    for pack in {p.lower(): p for p in [*packs, *(k for k in depots if k != ALL_MAPS)]}.values():
                        key = next((k for k in moves if k.lower() == pack.lower()), pack)
                        rows, ids = moves.get(key, ([], []))
                        scenarios = of_map(data_arc, key)  # (not `shipped`: shipped_paths() above reads that name)
                        new_rows = with_depots(rows, depot_rule(depots, key), scenarios) if scenarios else rows
                        if new_rows != rows:
                            moves[key] = (new_rows, ids + [i for i in depot_ids if i not in ids])
                from .newmap import is_blank
                for name, (spec, mod_id) in making.items():  # a blank map's HQs: every seat's put by the modder
                    if not is_blank(spec):
                        continue
                    from .players import blank_seats, entry_seating
                    from .scenario import folder_of
                    rows = moves.get(name, ([], []))[0]
                    settings = players.get(name, ([], []))[0]
                    for entry, count, layouts, file in entry_seating(read_glad, name):
                        raw = read_data(folder_of(name) + file) if file else None
                        n = settings[-1].count if settings else count
                        if raw is None or not n:
                            continue
                        try:
                            seats_ = blank_seats(raw, file, rows, n, layouts)
                        except (ScenarioError, ValueError, struct.error):
                            continue  # (its scenario can't be read: the moves below say so)
                        missing = sorted((t, k) for t, k, placed in seats_.values() if not placed)
                        if missing:
                            # The owner's call (2026-10-09): a blank map's HQs are each put by the modder ("the HQ
                            # shouldn't be there ... This isn't D-Day"), and Test in game stops until they are. The game
                            # itself would start those players where the copied map had them; a blank map with HQs
                            # left there has never been tried in the game.
                            where = ", ".join(f"team {t}, HQ {k}" for t, k in missing)
                            # not a game rule: the owner's call for blank maps (above), not something the game asks
                            result.findings.append(Finding("error", f"{mod_id}: maps/{name}: {entry!r} seats {n} "
                                                                    f"players, and these HQs aren't placed yet: {where}. "
                                                                    f"Place each in the Studio (Scenario, Each "
                                                                    f"player's HQ), or set fewer players"))
                for name, (map_moves, ids) in moves.items():
                    from .players import skirmish_files
                    from .scenario import Move, Spawn, spawn_class_problems
                    from .sectors import Sectors
                    map_moves = [m for m in map_moves if not isinstance(m, Sectors)]  # (the sectors: after these)
                    if not map_moves:
                        continue
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
                for name, (rows, ids) in moves.items():  # sectors over the whole map (rusemod.sectors), after the
                    from .scenario import folder_of       # design items: every scenario's zones and zone map, their
                    from .sectors import SectorError, apply_sectors, sectors_of  # points on the final ground; or
                    setting = sectors_of(rows)                                   # painted (the Sectors brush)
                    if setting is None or not setting.active:
                        continue
                    height_at = None
                    map_path = find_map(name)
                    if map_path is not None:
                        from .bridges import Ground
                        from .tms import Tms
                        entry = next((e for e in map_packs if e[0] == map_path), None)
                        map_arc = entry[1] if entry else open_pack(map_path)
                        try:
                            e = map_arc.find("output\\highdef.tms")
                            height_at = Ground(Tms((entry[2].get(e.path) if entry else None)
                                                   or bytes(map_arc.read(e)))).height_at
                        except (KeyError, ValueError, struct.error, zlib.error):
                            pass  # without the ground, the sectors' points sit at height 0 (the shapes are the same)
                    folder = folder_of(name)
                    files = sorted(e.path[len(folder):] for e in data_arc.entries
                                   if e.path.lower().startswith(folder) and e.path.lower().endswith(".scenario")
                                   and "\\" not in e.path[len(folder):])
                    skipped: list = []
                    try:
                        # a painted scenario with no sector at all, or a painted sector in pieces or with a hole,
                        # raises PaintError (a SectorError): the build stops with it, so the map check and Test in
                        # game say why
                        new, notes = apply_sectors(read_data, name, files, height_at, skipped=skipped,
                                                   setting=setting)
                    except (SectorError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    for why in skipped:
                        warn(f"{', '.join(ids)}: {why}")
                    changed_members.update(new)
                    say(f"sectors: {name}, {'painted' if setting.paints or setting.no_sectors else 'over the whole map'}"
                        f", from {', '.join(ids)}")
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
                    from . import solved
                    from .cover import member as movement_member
                    try:  # the game's own movement file for the map, as shipped: the key of the answers' lock
                        shipped = bytes(data_arc.read(data_arc.find(movement_member(name))))
                    except KeyError:
                        shipped = None
                    given, unused = _given_answers(result.order, mods, name, shipped)
                    for note in unused:
                        result.findings.append(Finding("note", note))
                    answers: dict = {}
                    try:
                        new, notes = _kept_movement(read_data, name, map_blocks, idle, cache, given, answers,
                                                    aheads.get(name))
                    except (NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {exc}{_meant(game, name)}"))
                        continue
                    changed_members.update(new)
                    say(f"movement: {name}, from {', '.join(ids)}")
                    for note in notes:
                        say(f"  {note}")
                    took = sum(1 for k in answers if k in given)
                    if took:
                        say(f"  {took} of its {len(answers)} worked-out answers came with the mod")
                    if answers and shipped is not None:
                        result.solved[name] = solved.pack(answers, shipped, name)
                    for b in idle:
                        result.findings.append(Finding("note", (
                            f"{', '.join(ids)}: {name}: the open at ({b.x:.0f}, {b.y:.0f}) opened nothing: units "
                            f"could already go there, or it is too small (an open needs a radius of 5 m or more) or "
                            f"out of reach of the ground they use")))
                    thin = [s for s in terrain_edits(result.order, mods).get(name, ([], []))[0]
                            if s.brush == "water" and not s.block]
                    for b, (wx, wy) in _wet_opens(open_pack, game, name, map_blocks, map_packs, find_map, thin):
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
                for name, ids in roads_out.items():  # the map's own road network out, before the new roads go in
                    from .cover import member as movement_member
                    from .roadnet import take_out_roads
                    win = read_data(movement_member(name))
                    if win is None:
                        continue  # (a map with no movement file has no road network)
                    try:
                        new_win, notes = take_out_roads(win)
                    except (RoadNetError, NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{', '.join(ids)}: {name}: the map's own road "
                                                                f"network can't be taken out ({exc})"))
                        continue
                    if notes:
                        changed_members[movement_member(name)] = new_win
                        say(f"roads out: {name}, from {', '.join(ids)}")
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
                for name in sorted(set(blocks) | set(bridge_spans) | set(new_roads)):  # last: no circle with more
                    from .cover import member as movement_member                      # links than a route through
                    from .nav import cap_movement                                     # it can take (nav.MAX_LINKS)
                    win = changed_members.get(movement_member(name))
                    if win is None:
                        continue
                    try:
                        capped, notes = cap_movement(win)
                    except (NavError, ValueError, struct.error) as exc:
                        result.findings.append(Finding("error", f"{name}: {exc}{_meant(game, name)}"))
                        continue
                    if notes:
                        changed_members[movement_member(name)] = capped
                        say(f"movement: {name}, every circle's links checked")
                        for note in notes:
                            say(f"  {note}")
                # last of all: ground the mods' changes cut off from the rest of the map, which the map as shipped
                # didn't have (rusemod.mapcheck.new_cut_off): an order onto it crashes the game. An error when
                # `cut_off_errors` (the Studio's Test in game: the owner, 2026-10-16, a map that would crash is refused
                # first), else a warning (a player's Play goes on, told where)
                from .cover import member as movement_member
                from .mapcheck import new_cut_off
                from .nav import NavError
                for name in sorted(set(blocks) | set(bridge_spans) | set(new_roads) | set(roads_out)):
                    win = changed_members.get(movement_member(name))
                    if win is None:
                        continue
                    try:
                        shipped = bytes(data_arc.read(data_arc.find(movement_member(name))))
                    except KeyError:
                        shipped = None
                    try:
                        found = new_cut_off(shipped, win)
                    except (NavError, ValueError, struct.error):
                        continue  # (a file the check can't read: the build's own checks have said what they could)
                    for f in found:
                        d = f["data"]
                        text = (f"{name}: ground around ({d['x']}, {d['y']}), {d['metres']} m across, is cut off for "
                                f"{d['units']}: they can't reach it from the rest of the map, and an order onto it "
                                f"crashes the game. Open a way to it (the Movement brush's Open, or Erase), or take "
                                f"back what closed it{_meant(game, name)}")
                        if cut_off_errors:
                            result.findings.append(Finding("error", text))
                        else:
                            warn(text)
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
                for unit, (source, own) in sorted(result.look_symbols.items()):  # new buildings' own looks
                    from .buildinglook import BuildingLookError, check_clone, clone_symbol, symbol_file_of
                    from .sceneryasset import type_name
                    look, mod_id = result.own_looks[unit]
                    try:
                        found = symbol_file_of(read_data, source)
                        if found is None:
                            # rule: building-symbol (a look the base-building file doesn't have stops the game)
                            raise BuildingLookError(f"the game's base-building file has no look {source} for "
                                                    f"{unit}'s to be a copy of")
                        member, raw = found
                        swap = {look.piece: type_name(look.asset.name)}
                        changed_members[member] = clone_symbol(raw, source, own, swap)
                        say(f"look: {check_clone(raw, changed_members[member], source, own, swap)}")
                    except BuildingLookError as exc:
                        result.findings.append(Finding("error", f"{mod_id}: files/buildings/{unit}: {exc}"))
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
        _menu_orders(result, mods, arc, say)  # last on the menus: after the new maps' entries and the player counts
        if result.mission_packs:  # a new map with its own mission: alone in a menu pack of its own (missionbuild)
            from . import missionbuild
            from .players import GLOBALS
            key = next((k for k in result.changed if k.lower() == GLOBALS.lower()), None)
            if key is None:
                result.findings.append(Finding("error", "the missions' own menu packs: the menus weren't changed"))
            else:
                try:
                    result.changed[key] = missionbuild.own_packs(result.changed[key], result.mission_packs)
                    say(f"menus: {len(result.mission_packs)} mission(s) of the mods' own, each in a pack of its own")
                except (missionbuild.MissionBuildError, ValueError, KeyError, struct.error, StopIteration) as exc:
                    result.findings.append(Finding("error", f"the missions' own menu packs couldn't be made: {exc}"))
        by_id = {m.id: m for m, _ops in mods}
        mod_scripts = [(i, by_id[i].scripts) for i in result.order if i in by_id and getattr(by_id[i], "scripts", None)]
        if mod_scripts:  # the game's mission scripts the mods change (rusemod.mapscripts, MOD_FORMAT §9)
            from . import mapscripts
            ia_path = find_pack(game, mapscripts.PACK)
            if ia_path is None:
                # not a game rule: the game or one of its files isn't found
                result.findings.append(Finding("error", f"{mapscripts.PACK} isn't in this game, so no mission "
                                                        f"script can be changed"))
            else:
                ia_arc = open_pack(ia_path)
                scripts_changed, said_scripts = mapscripts.build_changes(ia_arc, mod_scripts)
                result.findings += [Finding(level, message) for level, message in said_scripts]  # (said below)
                if scripts_changed:
                    data_packs.append((ia_path, ia_arc, scripts_changed))
                    say(f"mission scripts: {len(scripts_changed)} changed in {ia_path.name}")
        if result.mission_scripts:  # the new maps' own missions (rusemod.mission): new files of IA_Common.dat
            from .newmap import Grown
            ia_path = find_pack(game, "IA_Common.dat")
            at = next((k for k, (p, _a, _c) in enumerate(data_packs) if ia_path is not None and p == ia_path), None)
            if at is None:
                data_packs.append((ia_path, Grown(open_pack(ia_path), result.mission_scripts), {}))
            else:
                p, a, c = data_packs[at]
                data_packs[at] = (p, Grown(a, result.mission_scripts), c)
            say(f"mission scripts: {len(result.mission_scripts)} new in {ia_path.name}")
        for path, pack in new_packs.items():  # a new map's pack is written even when no mod edits its files
            if not any(e[0] == path for e in map_packs):
                map_packs.append((path, pack, {}))
        if any(spec.start_dots for spec, _id in making.values()) or \
                any(v[0].start_dots for v in shipped_pictures.values()):
            from .scenario import PACK as DOTS_PACK

            def final_data(member):
                """A DataMap_Win.dat member as the build leaves it (any case), or None."""
                key = member.replace("/", "\\").lower()
                for layer in [c for _p, _a, c in data_packs] + [data_new]:
                    found = next((d for m, d in layer.items() if m.lower() == key), None)
                    if found is not None:
                        return found
                base = data_base if data_base is not None else (
                    open_pack(find_pack(game, DOTS_PACK)) if find_pack(game, DOTS_PACK) else None)
                e = base.entry(member) if base is not None else None
                return bytes(base.read(e)) if e is not None else None

            def ground_bounds(name):
                """A map's ground bounds (x0, y0, x1, y1), from its pack as the build has it, or None."""
                from .tms import Tms
                path = find_map(name)
                if path is None:
                    return None
                entry = next((e for e in map_packs if e[0] == path), None)
                a = entry[1] if entry else open_pack(path)
                try:
                    e = a.find("output\\highdef.tms")
                    x0, y0, _z0, x1, y1, _z1 = Tms((entry[2].get(e.path) if entry else None) or bytes(a.read(e))).bounds
                except (KeyError, ValueError, struct.error, zlib.error):
                    return None
                return x0, y0, x1, y1
            _start_dots(result, making, shipped_pictures, final_data, ground_bounds, say)
        if not result.errors:  # the missions a player can pick, as the set leaves them: none without a zone it
            # watches from its start (rusemod.missionplaces; the owner, 2026-11-13, items 31 and 32)
            from .missionplaces import GLAD
            placed = mission_places(game, stack, open_pack, arc if pack_path.name.lower() == GLAD.lower() else None,
                                    result.changed, data_packs, rmods, mods, result)
            result.findings += placed
            for line in report_lines([f for f in placed if f.level == "note"], show_all=show_all):
                say(line)
        late = [f for f in result.findings[reported:] if f.level == "warning" and id(f) not in said]
        for line in report_lines(late, show_all=show_all):  # the maps' warnings (a drained river's was never shown)
            say(line)
        if result.errors:
            for line in report_lines([f for f in result.findings if f.level == "error"], show_all=show_all):
                say(line)
            counted()
            say("Nothing was written.")
            return result
        counted()   # (every finding is in now: the maps' and the missions' too)
        rmod_packs = run.changed_packs() if run else {}
        for path, a, changed in [(pack_path, arc, result.changed)] + data_packs:  # the members new maps add
            if getattr(a, "added", None) and hasattr(a, "added_with"):
                result.added[path.name] = a.added_with(changed)
        if map_packs or rmod_packs or data_packs:
            gameplay = {}
            for p, a in rmod_packs.items():
                where = f"Maps/PC/{p.name}/" if p.parent.parent.name.lower() == "maps" else ""
                gameplay.update({where + m: d for m, d in {**a.changed, **a.added}.items()
                                 if not (m in a.changed and looks_only_change(m, d, lambda a=a, m=m: _shipped(a, m)))})
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
                                                        {**result.model_changed, **result.texture_changed}, say=say,
                                                        loose=result.new_files))
            except LookError as exc:
                raise BuildError(str(exc)) from None
        fair_pack = None
        # a cheat copy's lock carries the copy's build code: what the mods make of the game, as the join code names
        # it (the game patches a copy gets below follow from the same mods, so they need no place in it)
        lock_code = fair_play.build_code(
            build_id, result.fingerprint if result.fingerprint is not None else fingerprint(build_id, result.changed),
            fair_mods) if fair.offline and not fair.dev else None
        patches = fair.patches(lock_code or fair_play.NO_BUILD_CODE)
        if not patches:
            lock_code = None  # (our game scripts are off in this build: no lock)
        if patches:  # our fair play scripts, in every map's own script folder in IA_Common.dat (rusemod.fairplay)
            ia_path, zz_path = find_pack(game, fair_play.MAP_SCRIPTS), text_path or find_pack(game, loc.PACK)
            if (ia_path is None or zz_path is None) and fair.offline:
                # not a game rule: the game or one of its files isn't found
                raise BuildError(f"The game has no {fair_play.MAP_SCRIPTS} or {loc.PACK}, so this copy can't get its "
                                 f"offline lock: build it without the cheats and test tools.")
            if ia_path is None or zz_path is None:
                say(f"note: no {fair_play.MAP_SCRIPTS} or {loc.PACK} in this game, so no RUSE Guard watcher")
                patches = []
        if patches:
            from .rmod import Layered
            zz = text_arc if text_arc is not None else open_pack(zz_path)  # only read: the game's own match script
            ia = open_pack(ia_path)
            ia = ia if isinstance(ia, Layered) else Layered(ia, ia_path)
            changed_low = {m.lower(): d for m, d in result.changed.items()}
            new_low = {m.lower(): d for m, d in result.added.get(pack_path.name, {}).items()}
            clusters = [changed_low.get(e.path.lower()) or bytes(arc.read(e)) for e in arc.entries
                        if e.path.lower().startswith(fair_play.SCENARIOS) and "cluster" in e.path.lower()]
            clusters += [d for m, d in new_low.items() if m.startswith(fair_play.SCENARIOS) and "cluster" in m]
            try:
                folders = fair_play.script_folders(clusters)
                done = fair_play.add_to_maps(ia, folders, fair_play.multiplayer_script(zz, result.script_changed),
                                             patches)
                # and after the game's own Battles launcher, the one place the game loads them for Battles (the map
                # folders' copies above never ran in a Battles match: 2026-10-30); after add_to_maps, whose
                # fallback for a folder without its own script is the launcher as it was
                launcher_pack, launcher_bytes = fair_play.add_to_launcher(zz, patches, result.script_changed)
            except (fair_play.FairPlayError, pyscript.ScriptError, KeyError, ValueError) as exc:
                raise BuildError(f"RUSE Guard's scripts can't be added: {exc}") from None
            result.script_changed[launcher_pack] = launcher_bytes
            if text_arc is None:  # the launcher is in ZZ_Win.dat, so the copy gets its own ZZ_Win.dat
                text_path, text_arc = zz_path, zz
            fair_pack = (ia_path, ia)
            say(f"RUSE Guard: the watcher{' and the lock of a copy with cheats' if lock_code else ''} in the Battles "
                f"launcher ({Path(zz_path).name}) and {done} map script folders ({ia_path.name})")
            for reason in fair.offline:
                say(f"built with cheats or test tools: {reason}; multiplayer and co-op only with players who have "
                    f"the same build, any other match is left at once")
        # guards on three places where the game's own scripts stop the game with mods on (rusemod.scriptguards): in
        # every copy, on top of what the steps above did to the same script packs. One that can't be joined is left
        # out and said; it never stops the build.
        from . import scriptguards
        guard_path = text_path or find_pack(game, loc.PACK)
        if guard_path is not None:
            guard_zz = text_arc if text_arc is not None else open_pack(guard_path)
            guarded, guards_added, guards_left = scriptguards.script_changes(guard_zz, result.script_changed)
            if guarded:
                result.script_changed.update(guarded)
                if text_arc is None:  # the script packs are in ZZ_Win.dat, so the copy gets its own ZZ_Win.dat
                    text_path, text_arc = guard_path, guard_zz
                guards_said = "; ".join(scriptguards.WHAT[name] for name in guards_added)
                say(f"guards in the game's own scripts, each only where the game would otherwise stop: {guards_said}")
            for left in guards_left:
                say(f"note: a guard in the game's scripts was left out. {left}")
        if result.own_models and text_arc is not None:  # new units' own models (rusemod.unitmodel)
            from .unitmodel import KeptModels, UnitModelError, write_batch, write_unit_model
            batch: dict = {}  # every own model into each pack at once: each pack read and written once
            before = {**result.model_changed, **result.texture_changed, **result.model_imports}
            kept = KeptModels(cache)  # each model as read and its textures, kept between builds
            kept.prepare([glb for _unit, (_source, glb, _mod) in sorted(result.own_models.items())])  # side by side
            for unit, (source, glb, mod_id) in sorted(result.own_models.items()):
                try:
                    prep, textures = kept.get(glb)
                    # (written under its own stem: <unit>, or <unit>__<kind> for one kind of its soldiers)
                    written = write_unit_model(text_arc, source, _own_stem(unit), prep, earlier=before, batch=batch,
                                               textures=textures)
                except (UnitModelError, ValueError, OSError, struct.error) as exc:
                    kept.close()
                    raise BuildError(f"{mod_id}: files/models/{Path(glb).name}: {_pack_full(exc)}") from None
                result.new_files.update(written.added)
                r = written.report
                say(f"own model of {unit}: {r.get('vertices', '?')} points, {r.get('triangles', '?')} triangles in "
                    f"{r.get('draws', '?')} draw call(s), {len(written.added)} texture(s); into "
                    f"{len(written.changed)} pack(s) beside {source}")
            kept.close()
            try:
                result.model_imports.update(write_batch(batch))
            except (ValueError, struct.error) as exc:
                raise BuildError(f"the mods' own models: {_pack_full(exc)}") from None
            batch.clear()
        if result.own_copies and text_arc is not None:  # units' own copies of their models (rusemod.unitmodel)
            from .unitlook import LookError
            from .unitmodel import UnitModelError, write_unit_copy
            for unit, (copies, paint, mod_id) in sorted(result.own_copies.items()):
                try:
                    written = write_unit_copy(text_arc, copies, unit, paint, earlier={
                        **result.model_changed, **result.texture_changed, **result.model_imports})
                except (UnitModelError, LookError, ValueError, OSError, struct.error) as exc:
                    raise BuildError(f"{mod_id}: files/models/{unit}.copy.toml: {_pack_full(exc)}") from None
                result.model_imports.update(written.changed)
                result.new_files.update(written.added)
                r = written.report
                say(f"own copy of {', '.join(copies)} for {unit}: {len(written.added)} texture(s), "
                    f"{len(r['painted'])} painted; into {len(written.changed)} pack(s)")
        if result.own_assets and text_arc is not None:  # mods' own map assets (rusemod.sceneryasset)
            from .sceneryasset import AssetError, type_name, write_asset
            for name, (asset, mod_id) in sorted(result.own_assets.items()):
                try:
                    written = write_asset(text_arc, asset, earlier={
                        **result.model_changed, **result.texture_changed, **result.model_imports})
                except (AssetError, ValueError, OSError, struct.error) as exc:
                    raise BuildError(f"{mod_id}: files/assets/{name}: {exc}") from None
                result.model_imports.update(written.changed)
                result.new_files.update(written.added)
                r = written.report
                say(f"map asset {type_name(name)} ({asset.kind}): "
                    + ", ".join(f"{role} {r['triangles'][role]:,} triangles in {r['draws'][role]} draw(s)"
                                for role in r["triangles"])
                    + "".join(f"; {ring} " + ", ".join(f"{n:,}" for n in tris.values())
                              + f" ({r['versions_from'][ring]})" for ring, tris in r["versions"].items())
                    + f", {r['pictures']} texture(s); into {len(r['mesh_packs'])} mesh pack(s)")
        if result.look_symbols and text_arc is not None:  # new buildings' own looks' models (rusemod.buildinglook)
            from .sceneryasset import AssetError, type_name, write_asset
            for unit in sorted(result.look_symbols):
                look, mod_id = result.own_looks[unit]
                try:
                    written = write_asset(text_arc, look.asset, earlier={
                        **result.model_changed, **result.texture_changed, **result.model_imports})
                except (AssetError, ValueError, OSError, struct.error) as exc:
                    raise BuildError(f"{mod_id}: files/buildings/{unit}: {exc}") from None
                result.model_imports.update(written.changed)
                result.new_files.update(written.added)
                r = written.report
                say(f"look of {unit}: {type_name(look.asset.name)} in place of {look.piece}, "
                    f"{r['triangles']['main']:,} triangles in {r['draws']['main']} draw(s)"
                    + "".join(f"; {ring} {tris['main']:,}" for ring, tris in r["versions"].items())
                    + f", {r['pictures']} texture(s); into {', '.join(p.rsplit(chr(92), 1)[-1] for p in r['mesh_packs'])}")
        sounds: dict = {}  # mods' own sounds (MOD_FORMAT §7, rusemod.sound): a later mod's WAV wins
        for mod_id in result.order:
            sounds.update(getattr(by_id.get(mod_id), "sounds", None) or {})
        if sounds and text_arc is not None:
            from .sound import SoundError, changes as sound_changes
            say(f"sounds: {len(sounds)}")
            try:
                result.sound_changed = sound_changes(text_arc, sounds, cache, say=say, before={
                    **result.model_changed, **result.texture_changed, **result.model_imports})
            except SoundError as exc:
                raise BuildError(str(exc)) from None
        volumes: dict = {}  # how loud mods play the game's sounds (files/sound/volume.toml): a later mod's wins
        for mod_id in result.order:
            volumes.update(getattr(by_id.get(mod_id), "volumes", None) or {})
        if volumes and text_arc is not None:
            from .sound import SoundError, volume_changes
            say(f"sound volumes: {len(volumes)}")
            try:
                result.sound_changed.update(volume_changes(text_arc, volumes, cache, say=say, before={
                    **result.model_changed, **result.texture_changed, **result.model_imports,
                    **result.sound_changed}))
            except SoundError as exc:
                raise BuildError(str(exc)) from None
        clips: dict = {}  # mods' animations (files/anim/clips.toml, files/replace/*.baf; rusemod.anim): a later mod's wins
        for mod_id in result.order:
            clips.update(getattr(by_id.get(mod_id), "clips", None) or {})
        if clips and text_arc is not None:
            from .anim import AnimError, changes as anim_changes
            say(f"animations: {len(clips)}")
            try:
                # (kept with the sounds: members of ZZ_Win.dat the build replaces, its genanim_15 packs here)
                result.sound_changed.update(anim_changes(text_arc, clips, cache, say=say, before={
                    **result.model_changed, **result.texture_changed, **result.model_imports,
                    **result.sound_changed}))
            except AnimError as exc:
                raise BuildError(str(exc)) from None
        if result.own_clips and text_arc is not None:  # units' own clips (files/anim/units.toml; rusemod.anim): new
            from .anim import AnimError, own_clip_files  # files of ZZ_Win.dat's own beside the game's, which stay
            say(f"units' own animations: {len(result.own_clips)}")
            try:
                result.new_files.update(own_clip_files(text_arc, result.own_clips, cache, say=say))
            except AnimError as exc:
                raise BuildError(str(exc)) from None
        new_songs: dict = {}  # mods' new songs (files/music/list<N>, rusemod.sound): new files and descriptions
        for mod_id in result.order:
            new_songs.update(getattr(by_id.get(mod_id), "new_songs", None) or {})
        if new_songs and text_arc is not None:
            from .sound import SoundError, new_song_changes
            try:
                banks, added = new_song_changes(text_arc, new_songs, cache, say=say, before={
                    **result.model_changed, **result.texture_changed, **result.model_imports,
                    **result.sound_changed})
            except SoundError as exc:
                raise BuildError(str(exc)) from None
            result.sound_changed.update(banks)
            result.new_files.update(added)
        ambience: dict = {}  # mods' map backgrounds (maps/<map>/background_<n>.wav, sound.toml; rusemod.sound)
        for mod_id in result.order:
            ambience.update(getattr(by_id.get(mod_id), "ambience", None) or {})
        if ambience and text_arc is not None:
            from .sound import SoundError, ambience_changes

            def read_config(member: str):
                """A map's settings file as the build has it so far: changed by a mod, a new map's, or the game's."""
                low = member.lower()
                got = next((v for k, v in result.changed.items() if k.replace("/", "\\").lower() == low), None)
                if got is not None:
                    return got
                e = arc.entry(member)
                return bytes(arc.read(e)) if e is not None else None
            try:
                configs, banks, added = ambience_changes(read_config, text_arc, ambience, cache, say=say, before={
                    **result.model_changed, **result.texture_changed, **result.model_imports,
                    **result.sound_changed})
            except SoundError as exc:
                raise BuildError(str(exc)) from None
            for member, raw in configs.items():
                key = arc.entry(member).path
                result.changed[key] = raw
                if key in result.added.get(pack_path.name, {}):  # a new map's own settings file
                    result.added[pack_path.name][key] = raw
            result.sound_changed.update(banks)
            result.new_files.update(added)
        if result.new_files and text_arc is not None:  # new cards and model textures: files of ZZ_Win.dat's own
            from .newmap import Grown
            text_arc = Grown(text_arc, result.new_files)
        zz_win_changed = {**result.text_changed, **result.script_changed, **result.model_changed,
                          **result.close_up_maps, **result.texture_changed, **result.model_imports,
                          **result.sound_changed}
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
        if fair_pack and Path(fair_pack[0]).resolve() not in {Path(p).resolve() for p, _a, _c in rebuilt if p}:
            rebuilt.append((fair_pack[0], fair_pack[1], {}))  # (a pack the .rmod mods changed already has them)
        # a pack the .rmod mods changed writes their changes too, even when the other mods leave it alone
        rebuilt = [(path, a, changed) for path, a, changed in rebuilt if changed or getattr(a, "is_changed", False)]
        if not rebuilt:
            say("The mods change nothing in these packs.")
            return result
        # packs past 4 GiB (the owner, 2026-10-30): written wide, with the big-packs game patch in the copy
        wide, opened = _wide_packs(game, rebuilt, say)
        rebuilt += opened
        result.wide_packs = sorted(Path(p).name for p in wide)
        if result.fingerprint is None:
            result.fingerprint = fingerprint(build_id, result.changed)
        patched_exe = None
        from . import gamepatch
        patches = copy_patches(result.game_patch, bool(wide))
        if patches:  # the modded copy's own RUSE.exe, patched (rusemod.gamepatch); the game's is only read
            exe = Path(game) / gamepatch.EXE
            try:
                got = [gamepatch.fetch(name, cache, say=say) for name in patches]
                patched_exe = gamepatch.apply_all(got, exe.read_bytes()) if instance is not None else None
            except OSError as exc:
                # not a game rule: the game's file can't be read
                raise BuildError(f"{exe} can't be read for the game patch ({exc.strerror or exc})") from None
            except gamepatch.GamePatchError as exc:
                raise BuildError(str(exc)) from None
            # players only play together with the same patches
            result.fingerprint = patches_fingerprint(result.fingerprint,
                                                     [(name, patch.sha256) for name, patch in zip(patches, got)])
            for name in patches:
                say(f"game patch {name}: " + ("applied to the modded copy's RUSE.exe" if instance is not None
                                              else "only a modded copy gets it (--instance)"))
        say(f"fingerprint: {fingerprint_text(result.fingerprint)}")
        if out is not None:
            out = Path(out)
            if out.suffix.lower() == ".dat":
                if len(rebuilt) > 1:
                    raise BuildError(f"these mods rebuild {len(rebuilt)} packs ("
                                     + ", ".join(path.name for path, _a, _c in rebuilt) + "): give --out a folder")
                targets = [(out, rebuilt[0][1], rebuilt[0][2], rebuilt[0][0] in wide)]
            else:
                out.mkdir(parents=True, exist_ok=True)
                targets = [(out / path.name, a, changed, path in wide) for path, a, changed in rebuilt]
            for target, a, changed, is_wide in targets:
                with target.open("wb") as f:
                    a.write_to(f, changed, None, is_wide)
                say(f"wrote {target}")
        if instance is not None:
            from .instance import Note, build_instance
            replace, add = {}, {}
            for path, a, changed in rebuilt:
                rel = str(path.resolve().relative_to(Path(game).resolve()))
                # a new map's pack isn't in the game: the copy gets it as a file of its own
                (replace if path.exists() else add)[rel] = (lambda f, a=a, changed=changed, w=path in wide:
                                                            a.write_to(f, changed, None, w))
            if patched_exe is not None:
                replace[gamepatch.EXE] = patched_exe  # written into the copy as a file of its own
            copied = build_instance(str(game), str(instance), replace=replace, add=add, built_from=built_from)
            say(f"modded copy ready: {instance}  {copied}")
            if fair_play.ON:  # (switched off until the owner says: fairplay.ON)
                record = fair_play.write_record(instance, build_id, result.fingerprint, fair_mods, fair,
                                                 [*replace, *add], lock_code)
                say(f"join code: {record['code']}" if record["code"] else f"no join code ({record['why']})")
            locked = copied.get("read-only packs", 0)
            if getattr(copied, "other_drive", False):  # said once, every build: how much it cost this time
                drive = os.path.splitdrive(os.path.realpath(game))[0] or str(Path(game).anchor)
                say(Note("play_other_drive", gb=f"{copied.copied_bytes / (1 << 30):.1f}", drive=drive))
            elif copied.get("full copies", 0) > locked:  # the game's drive, but maybe one that can't share files
                from .winfiles import volume
                fs = volume(str(instance)).get("fs", "")
                if fs and fs.upper() != "NTFS":  # FAT32, exFAT: no hard links at all
                    say(Note("doc_drive_other", path=str(Path(instance).parent), fs=fs))
            if locked:
                say(f"note: {locked} of the game's packs are marked read-only, so they were copied rather than linked "
                    f"(a link would share the mark, and the copy couldn't be removed later). Unticking Read-only in "
                    f"the game folder's Properties would save that space.")
            if copied.get("old copy left"):
                say(f"note: the previous copy at {instance}.old couldn't be removed yet; the next build removes it.")
        for _p, a, _c in opened:  # the game's own big packs opened to be rewritten wide
            a.close()
    return result


TWO_GIB = 1 << 31
# not a game rule: one file inside a game pack is at most 4 GB, its size said in 4 bytes (a model pack holding the
# mods' own models is such a file); the wide layout can't change that
MODEL_PACK_FULL = ("the game's model pack it goes into would pass 4 GB, the most one file inside a game pack can be: "
                   "take some of the mods' own models out (the era units' own models are the biggest) and build again")
# not a game rule: a model pack counts its draw calls, buffers and meshes in 2 bytes each
MODEL_PACK_COUNTS = ("the game's model pack it goes into would hold more than 65,535 draw calls, buffers or meshes, the "
                     "most it can count: take some of the mods' own models out (the era units' own models are the "
                     "biggest) and build again")


def _past_4_gb(exc) -> bool:
    """A number written in 4 bytes that didn't fit (Python says it so for every such write)."""
    return isinstance(exc, struct.error) and "4294967295" in str(exc)


def _pack_full(exc) -> str:
    """A model pack's write that didn't fit, in plain words; anything else as it is."""
    if _past_4_gb(exc):
        return MODEL_PACK_FULL
    if isinstance(exc, struct.error) and "65535" in str(exc):
        return MODEL_PACK_COUNTS
    return str(exc)


def _laid_out(a, changed, wide: bool = False) -> int:
    """A pack's size once written (rusemod.edat's layout, nothing read or written): PackTooBig when it can't be."""
    head = next(iter(a.iter_chunks(changed, None, wide)))
    return len(head) + struct.unpack_from("<Q", head, 0x25)[0]


def _wide_packs(game, rebuilt: list, say) -> tuple[set, list]:
    """The packs to write wide (rusemod.edat), for a copy with the big-packs game patch: none while every pack fits
    the game's own layout (its members start within 4 GiB of its file). Once one doesn't, every pack of 2 GiB or more
    in the copy is written wide, the game's own big ones too, rewritten as they are: with the patch, a plain place
    with bit 31 (a member past 2 GiB) would be read as a wide one. Returns (their paths, the game's packs opened for
    it, to add to `rebuilt`). A pack too big even wide (past 32 GiB, or one file in it past 4 GiB) stops the build."""
    from .edat import PackTooBig
    sizes, over = {}, []
    for path, a, changed in rebuilt:
        try:
            sizes[path] = _laid_out(a, changed)
        except PackTooBig:
            over.append(path)
    if not over:
        return set(), []
    wide = set(over) | {path for path, size in sizes.items() if size >= TWO_GIB}
    have = {Path(p).resolve() for p, _a, _c in rebuilt}
    opened = []
    for f in sorted(Path(game).rglob("*.dat")):
        if f.stat().st_size < TWO_GIB or f.resolve() in have:
            continue
        try:
            opened.append((f, Edat.open(str(f)), {}))
        except ValueError:
            continue  # not one of the game's packs
        wide.add(f)
    for path, a, changed in rebuilt + opened:
        if path not in wide:
            continue
        try:
            size = _laid_out(a, changed, True)
        except PackTooBig as exc:
            for _f, arc, _c in opened:
                arc.close()
            # not a game rule: a wide pack's own reach (32 GiB, each file in it 4 GiB)
            raise BuildError(f"{Path(path).name}: {exc}. Take some of the mods' own models or files out (the era "
                             f"units' own models are the biggest) and build again.") from None
        if path in over:
            say(f"{Path(path).name}: {size / (1 << 30):.2f} GB, past the 4 GB a game pack holds: written in the wider "
                f"layout, and the modded copy's RUSE.exe gets the big-packs game patch to read it")
        else:
            say(f"{Path(path).name}: written in the wider layout too (2 GB or more)")
    return wide, opened
