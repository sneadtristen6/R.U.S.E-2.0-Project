"""Blank maps to start from (the Studio's Duplicate map: Blank Terrain or Blank Ocean; docs/MOD_FORMAT.md §8): a new
map's own files that take the copied map back to its ground and its starting points, ready to be built up again.

- Blank Terrain: the whole map flat land at the map's middle height, every water drained, painted one plain colour.
- Blank Ocean: the whole map flat a thin sea's depth under the map's own sea level, the sea over all of it, units
  going under it as under a navy map's painted sea (a water stroke with block = false), painted the owner's blue
  under the water.
- Both: every object of the map's scenery erased (the types the game gives no kind are named one by one), the map's
  own roads and bridges taken out, every design item but the starting points taken out (depots, town names), and the
  sectors over the whole map.

Every number comes from the map's own files, so every PC writes the same files. Not seen in the game yet
(2026-10-05): the owner's blank D-Day ("a blank blue map on the lowest terrain, with nothing on it") is the model."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .brush import HARD_EDGE, Stroke, strokes_toml

KINDS = ("blank_terrain", "blank_ocean")
NAMES = {"blank_terrain": "Blank Terrain", "blank_ocean": "Blank Ocean"}   # the owner's names for them
OCEAN_DEPTH = 1353.0         # the sea's depth over the flat ground: the owner's D-Day corner, flattened to 11,270 under
                             # the map's sea at 12,623 (his "thin layer of water", 2026-10-05)
OCEAN_COLOUR = "#0010d2"     # the owner's blue (his D-Day's 135 paint strokes)
TERRAIN_COLOUR = "#5f6f3a"   # a plain grass green
LAND_OVER_SEA = 2 * OCEAN_DEPTH   # Blank Terrain's ground stands at least this far over the sea level
REACH = 1.01                 # the whole-map strokes reach this much past the map's corners at full strength


class PresetError(ValueError):
    pass


@dataclass
class Facts:
    """What a preset needs to know about the map it starts from."""
    bounds: tuple       # the ground's x0, y0, x1, y1 (map units)
    sea: float          # the map's sea level: its close-up ground's base water level (world z)
    middle: float       # the ground's middle height: the median of the close-up ground's points (world z)
    scenario: str       # the scenario file the new map plays
    items: list         # [(item number, kind)] of that scenario's design items, in order
    untyped: list       # the scenery types on the map the game gives no kind (an erase names them one by one)


def facts_of(highdef: bytes, scenery: bytes, scenario_name: str, scenario: bytes, descs: dict) -> Facts:
    """The Facts of a map from its own files: its close-up ground (output\\highdef.tms), its scenery, the scenario
    the new map plays (its name and bytes) and the game's scenery descriptors (rusemod.scenery.descriptors)."""
    from .scenario import Scenario
    from .scenery import Scenery
    from .tms import Tms
    hd = Tms(highdef)
    x0, y0, _z0, x1, y1, _z1 = hd.bounds
    zs = sorted(hd.to_world(2, p[2]) for c in hd.cells for p in c.positions())
    if not zs:
        raise PresetError("the map's ground has no points")
    sc = Scenery(scenery)
    used = sorted(sc.names[i] for i in sc.types())
    s = Scenario.read(scenario)
    return Facts((x0, y0, x1, y1), hd.to_world(2, hd.base_water()), zs[len(zs) // 2], scenario_name,
                 [(i, it.kind) for i, it in enumerate(s.items)], [n for n in used if n not in descs])


def read_facts(game: Path, pack: str, scenario_name: str) -> Facts:
    """The Facts of shipped map `pack` (its pack name), read from the game's own files (nothing is written)."""
    from .build import find_pack
    from .edat import Edat
    from .scenario import folder_of
    from .scenery import MEMBER, descriptors
    from .terrain import pack_file
    paths = {k: find_pack(game, n) for k, n in (("map", pack_file(pack)), ("data", "DataMap_Win.dat"),
                                                 ("glad", "ZZ_GladPatchableWin.dat"))}
    missing = [k for k, p in paths.items() if p is None]
    if missing:
        # not a game rule: the game or one of its files isn't found
        raise PresetError(f"{pack}: the game's files aren't all there ({', '.join(missing)})")
    with Edat.open(str(paths["map"])) as m, Edat.open(str(paths["data"])) as d, Edat.open(str(paths["glad"])) as g:
        def read(arc, member):
            e = arc.entry(member)
            if e is None:
                raise PresetError(f"{pack}: {member} isn't in the game's files")
            return bytes(arc.read(e))
        return facts_of(read(m, "output\\highdef.tms"), read(m, MEMBER), scenario_name,
                        read(d, folder_of(pack) + scenario_name), descriptors(g))


def copy_scenario(game: Path, pack: str, entry: str | None = None) -> str:
    """The scenario a copy of shipped map `pack` plays: its one BATTLES entry's, or the entry named (rusemod.newmap),
    from the game's files."""
    from .build import find_pack
    from .edat import Edat
    from .ndf import Ndf
    from .newmap import entry_scenario, menu_entries
    from .players import GLOBALS, MAPINFO
    path = find_pack(game, "ZZ_GladPatchableWin.dat")
    if path is None:
        # not a game rule: the game or one of its files isn't found
        raise PresetError("ZZ_GladPatchableWin.dat isn't in the game folder")
    with Edat.open(str(path)) as g:
        def read(member):
            e = g.entry(member)
            return bytes(g.read(e)) if e is not None else None
        m, menus = Ndf(read(MAPINFO)), Ndf(read(GLOBALS))
        found = [e for e in menu_entries(m, menus, pack) if (e[2] == entry if entry else e[3] == "battles")]
        if len(found) != 1:
            raise PresetError(f"{pack}: say which of its entries the new map copies" if found else
                              f"{pack}: no menu entry {entry!r}" if entry else f"{pack} isn't in BATTLES")
        name = entry_scenario(m, found[0][0], read)
    if name is None:
        # not a game rule: our map copier needs the game's own map files as they are
        raise PresetError(f"{pack}: its scenario can't be found, so it can't start blank")
    return name


PICTURES = {"blank_ocean": "blank_ocean.png", "blank_terrain": "blank_terrain.png"}  # the big ones, in pictures/
PICTURE, WIDE_PICTURE = "menu.png", "menu-wide.png"  # their names in the new map's folder (map.toml names them)


def preset_pictures(kind: str) -> dict[str, bytes]:
    """The new map's own pictures in the menus for preset `kind` ({file name: PNG}, map.toml picture and
    wide_picture, with start_dots): the big one ours (pictures/, made in Blender by rusemod.blender_menu: the open
    sea, or plain grass to the horizon, framed like the game's own), the wide one the map as a slab
    (rusemod.menudraw), its starting points drawn on it by the build wherever they are then."""
    from .menudraw import slab_png
    if kind not in KINDS:
        raise PresetError(f"no preset {kind!r} (presets: {', '.join(KINDS)})")
    big = (Path(__file__).with_name("pictures") / PICTURES[kind]).read_bytes()
    return {PICTURE: big, WIDE_PICTURE: slab_png("ocean" if kind == "blank_ocean" else "land")}


def whole_map(f: Facts) -> tuple[float, float, float]:
    """The middle of the map and the half-side of a square reaching past its corners at full strength (a hard
    edge's full strength reaches HARD_EDGE of the way out)."""
    x0, y0, x1, y1 = f.bounds
    return (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2 / HARD_EDGE * REACH


def strokes(kind: str, f: Facts) -> list[Stroke]:
    """The preset's terrain strokes, in order: the whole map flat, its water (drained or the sea), its paint."""
    if kind not in KINDS:
        raise PresetError(f"no preset {kind!r} (presets: {', '.join(KINDS)})")
    cx, cy, r = whole_map(f)
    square = {"shape": "square", "edge": "hard"}
    if kind == "blank_ocean":
        return [Stroke("level", cx, cy, r, level=f.sea - OCEAN_DEPTH, **square),
                Stroke("water", cx, cy, r, level=f.sea, block=False, **square),
                Stroke("paint", cx, cy, r, colour=OCEAN_COLOUR, **square)]
    return [Stroke("level", cx, cy, r, level=max(f.middle, f.sea + LAND_OVER_SEA), **square),
            Stroke("drain", cx, cy, r, **square),
            Stroke("paint", cx, cy, r, colour=TERRAIN_COLOUR, **square)]


def preset_files(kind: str, f: Facts) -> dict[str, str]:
    """The new map's files for preset `kind` ({file name: text}): terrain.toml, scenario.toml, roads.toml and
    scenery.toml, each in the form the Studio writes and reads back."""
    from .roadnet import TakeOut, roads_toml
    from .scenario import Remove, scenario_toml
    from .scenery import ERASE_GROUPS, ERASE_MAX, EraseArea, objects_toml
    from .sectors import Sectors
    name = NAMES[kind] if kind in NAMES else kind
    said = f"{name} (the Studio's Duplicate map preset; MOD_FORMAT §8): "
    cx, cy, r = whole_map(f)
    removes = [Remove(f.scenario, i, k) for i, k in f.items if k != "StartingPoint"]
    erase = EraseArea(cx, cy, min(ERASE_MAX, r), tuple(ERASE_GROUPS), tuple(f.untyped), shape="square")
    return {
        "terrain.toml": strokes_toml(strokes(kind, f), said + "the whole map flat, "
                                     + ("the sea over it (units go under it), painted blue under the water."
                                        if kind == "blank_ocean" else "every water drained, painted one colour.")),
        "scenario.toml": scenario_toml([], [], [], removes, said + "every design item but the starting points taken "
                                       "out; the sectors over the whole map.", Sectors(True)),
        "roads.toml": roads_toml([], said + "the map's own roads and bridges taken out.", TakeOut(True, True)),
        "scenery.toml": objects_toml([], said + "everything on the map erased.", [erase]),
    }
