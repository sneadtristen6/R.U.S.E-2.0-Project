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
            from .anim import AnimError, mod_clips
            try:
                info.clips = mod_clips(path)  # files/anim/clips.toml and files/replace/**/*.baf: its animations
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
    game_patch: str | None = None  # the game patch the modded copy needs (rusemod.gamepatch), or None
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
    (the skirmish mesh packs there say whether its models are loaded for it: unit_models)."""
    return any(m.texts or m.new_maps or getattr(m, "menu_pictures", None) or getattr(m, "textures", None)
               or getattr(m, "sounds", None) or getattr(m, "new_songs", None) or getattr(m, "ambience", None)
               or getattr(m, "volumes", None) or getattr(m, "clips", None)
               or getattr(m, "assets", None) or getattr(m, "looks", None)
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
    wanted: dict = {}
    for m in order:
        for unit, glb in (getattr(m, "models", None) or {}).items():
            wanted[unit] = (glb, m.id)
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    for unit, (glb, mod_id) in sorted(wanted.items()):
        source = _own_model_part(run, by_name, unit, f"{mod_id}: files/models/{unit}.glb", result)
        if source is None:
            continue
        out[unit] = (source, glb, mod_id)
        result.findings.append(Finding("note", f"{mod_id}: {unit} gets its own model (files/models/{unit}.glb), "
                                               f"beside {source}"))
    return out


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
    its paint, mod id)}. A unit with an imported model too (files/models/<name>.glb) is an error: it would have two."""
    from .unitmodel import copy_model_name, model_key
    wanted: dict = {}
    for m in order:
        for unit, (of, paint) in (getattr(m, "model_copies", None) or {}).items():
            wanted[unit] = (of, paint, m.id)
    by_name = {n.rsplit("/", 1)[-1]: n for n, op in run.created.items() if op.kind == "clone"}
    out: dict = {}
    for unit, (of, paint, mod_id) in sorted(wanted.items()):
        where = f"{mod_id}: files/models/{unit}.copy.toml"
        if unit in result.own_models:
            # not a game rule: one model per unit (an imported one, or a copy of the one it copies)
            result.findings.append(Finding("error", f"{where}: {unit} has an imported model too "
                                                    f"(files/models/{unit}.glb); take one of the two out"))
            continue
        name = by_name.get(unit) or _game_unit(run, unit)
        if name is None:
            # not a game rule: a copy for a unit nothing makes
            result.findings.append(Finding("error", f"{where}: no mod in the set makes a unit {unit}, and the game "
                                                    f"has none of that name"))
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


def _game_unit(run, unit: str) -> str | None:
    """The name of the game's unit called `unit` ("Descriptor_Unit_Soldat_US_Lourd"), or None."""
    name = f"$/GFX/Everything/{unit}"
    return name if name in run.game.objects else None


def _point_at_copies(run, name: str, copies: dict) -> int:
    """Point every model part of the unit `name` (under its GfxDescriptor* links: a squad's soldiers, its bazooka man,
    its token's figure) that names one of `copies`' models ({the game's model, rusemod.unitmodel.model_key: the copy's
    name}) at the copy. A part the unit links to that other units link to as well (an unnamed object of its own in
    the unit data, or a model part) is copied into the unit first, so they keep the game's. A game unit is copied
    before it's changed (Game.own). Returns how many model parts name a copy now (0: none named those models)."""
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

    if not any(reaches(p, w) for p, w in objects[name].props.items() if p.startswith("GfxDescriptor")):
        return 0
    unit = run.game.own(name)
    return sum(point(p, w, lambda x, p=p: unit.props.__setitem__(p, x))
               for p, w in list(unit.props.items()) if p.startswith("GfxDescriptor"))


def _own_model_part(run, by_name: dict, unit: str, where: str, result: BuildResult) -> str | None:
    """Point the new unit `unit`'s model part at a model of its own beside its source's ({folder}\\<unit>lod0): the
    model the source draws (the part's FileName), or None, with an error said, when no mod makes `unit` or its model
    part names no model file."""
    from .patch import Inline, Ref, _fresh
    name = by_name.get(unit)
    if name is None:
        # not a game rule: a model for a unit no mod in the set makes
        result.findings.append(Finding("error", f"{where}: no mod in the set makes a new unit {unit}"))
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
    mesh.obj.props["FileName"] = Text("path", f"{folder}\\{unit}lod0.Ase2ndfbin")
    return source


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
               cache: Path | None = None) -> BuildResult:
    """Run `mods` [(ModInfo, ops)] on the data files of `arc`, and their texts and new units' classes on
    `text_arc` (ZZ_Win.dat; needed when a mod has text/*.csv or new units). Nothing is written; see
    BuildResult.changed / text_changed / script_changed. `cache`: load_pack's."""
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
    run = Engine(base).run(first + [by_id[m.id] for m in order] + extra)
    result.findings = [Finding("note", n) for n in base.notes] + list(run.findings)
    # the levels each placed type is drawn at (its far copy's too), for its objects to ask of the blocks they hang on
    result.type_levels = visibility.type_levels(run.game, {t for t in placed if t} | set(result.visibility.values()))
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
    result.own_copies = unit_own_copies(run, order, result)
    result.look_symbols = building_looks(run, result)
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
    if result.errors:
        return result
    result.script_changed = {path: pack.to_bytes(members) for path, (pack, members) in scripts.items()}
    return result


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
    if set(kinds) & ownbuildings.PATCHED:
        result.game_patch = ownbuildings.PATCH
    result.findings.append(Finding("note", f"buildings with units of their own: kinds {', '.join(map(str, kinds))}, "
                                           f"each with its tab on the build bar"
                                   + (f"; the modded copy gets the game patch {ownbuildings.PATCH}"
                                      if result.game_patch else "")))


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


def build_and_write(game: Path, mods: list, *, pack: str = DEFAULT_PACK, out: Path | None = None,
                    instance: Path | None = None, say=print, show_all: bool = False,
                    cache: Path | None = None, built_from: dict | None = None,
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
    with the other mods, on top of every .rmod."""
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
        try:
            # the collector paused for the unit data's build: on two-shermans its passes over the loaded model and the
            # engine's copy of it took 2 to 4 seconds, and 5 to 9 with the model read from the cache, which it then
            # counts as new and looks through again and again (2026-10-04)
            with collector_paused():
                result = build_pack(arc, mods, build_id, text_arc, cache) if mods else BuildResult()
        except ResolveError as exc:
            raise BuildError(f"load order: {exc}") from None
        if run:
            first = [m.id for m in rmods]
            result.order = first + [i for i in result.order if i not in first]
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
                        changed_members, notes = edit_map(read, strokes, name, max_depth_of=depth)
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
                    keep_key = mapkeep.key(name + ("|generated" if name.lower() in generated else "") + size_tag,
                                           mapkeep.pack_identity(map_arc, map_path), strokes, depth)
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
        if result.own_models and text_arc is not None:  # new units' own models (rusemod.unitmodel)
            from .unitmodel import UnitModelError, read_mod_glb, write_unit_model
            for unit, (source, glb, mod_id) in sorted(result.own_models.items()):
                try:
                    written = write_unit_model(text_arc, source, unit, read_mod_glb(glb), earlier={
                        **result.model_changed, **result.texture_changed, **result.model_imports})
                except (UnitModelError, ValueError, OSError, struct.error) as exc:
                    raise BuildError(f"{mod_id}: files/models/{Path(glb).name}: {exc}") from None
                result.model_imports.update(written.changed)
                result.new_files.update(written.added)
                r = written.report
                say(f"own model of {unit}: {r.get('vertices', '?')} points, {r.get('triangles', '?')} triangles in "
                    f"{r.get('draws', '?')} draw call(s), {len(written.added)} texture(s); into "
                    f"{len(written.changed)} pack(s) beside {source}")
        if result.own_copies and text_arc is not None:  # units' own copies of their models (rusemod.unitmodel)
            from .unitlook import LookError
            from .unitmodel import UnitModelError, write_unit_copy
            for unit, (copies, paint, mod_id) in sorted(result.own_copies.items()):
                try:
                    written = write_unit_copy(text_arc, copies, unit, paint, earlier={
                        **result.model_changed, **result.texture_changed, **result.model_imports})
                except (UnitModelError, LookError, ValueError, OSError, struct.error) as exc:
                    raise BuildError(f"{mod_id}: files/models/{unit}.copy.toml: {exc}") from None
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
        # a pack the .rmod mods changed writes their changes too, even when the other mods leave it alone
        rebuilt = [(path, a, changed) for path, a, changed in rebuilt if changed or getattr(a, "is_changed", False)]
        if not rebuilt:
            say("The mods change nothing in these packs.")
            return result
        if result.fingerprint is None:
            result.fingerprint = fingerprint(build_id, result.changed)
        patched_exe = None
        if result.game_patch:  # the modded copy's own RUSE.exe, patched (rusemod.gamepatch); the game's is only read
            from . import gamepatch
            exe = Path(game) / gamepatch.EXE
            try:
                patch = gamepatch.fetch(result.game_patch, cache, say=say)
                patched_exe = gamepatch.apply(patch, exe.read_bytes()) if instance is not None else None
            except OSError as exc:
                # not a game rule: the game's file can't be read
                raise BuildError(f"{exe} can't be read for the game patch ({exc.strerror or exc})") from None
            except gamepatch.GamePatchError as exc:
                raise BuildError(str(exc)) from None
            # players only play together with the same patch
            result.fingerprint = hashlib.sha256(result.fingerprint + b"\ngame patch " + result.game_patch.encode()
                                                + b" " + patch.sha256.encode()).digest()
            say(f"game patch {result.game_patch}: " + ("applied to the modded copy's RUSE.exe" if instance is not None
                                                        else "only a modded copy gets it (--instance)"))
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
            from .instance import Note, build_instance
            replace, add = {}, {}
            for path, a, changed in rebuilt:
                rel = str(path.resolve().relative_to(Path(game).resolve()))
                # a new map's pack isn't in the game: the copy gets it as a file of its own
                (replace if path.exists() else add)[rel] = (lambda f, a=a, changed=changed: a.write_to(f, changed))
            if patched_exe is not None:
                replace[gamepatch.EXE] = patched_exe  # written into the copy as a file of its own
            copied = build_instance(str(game), str(instance), replace=replace, add=add, built_from=built_from)
            say(f"modded copy ready: {instance}  {copied}")
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
    return result
