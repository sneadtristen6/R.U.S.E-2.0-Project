"""Where missions show in their menus: a mod's `menus.toml` (MOD_FORMAT §8), LittleGroove's Menu Entry step's Move up
and Move down (ruse_mod_engine.scenario_registry.move_within_group).

The menus list their entries from menu packs (globals.cpp: a TChallengePack's ChallengeList for OPERATIONS, a
TChapterPack's ChapterList for the CAMPAIGN, a TMultiPack's MultiList for BATTLES), each pack's list in its order, and
group them by CategoryId in runs of one value (his edits.place_at_end_of_group: an entry put outside its run splits
its group in two). A mod gives the order of one run's missions:

    [[order]]
    menu = "operation"                      # operation, campaign or battles
    missions = ["Alpha/LevelDesign_BH.scenario", "TwoIslands/leveldesign_challenge.scenario"]

each mission by its map's pack name and its scenario file. The build puts those missions in that order in the places
they had in their list, so an entry the order doesn't name (another mod's new map) keeps its place. A later mod's
order of the same missions comes after an earlier one's. Not tried in the game yet.
"""
from __future__ import annotations

import re
import struct
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .ndf import Ndf, Value, local_ref, sub_values
from .newmap import KINDS, MENU_NAMES, entry_scenario
from .players import GLOBALS, MAPINFO

FILE = "menus.toml"                       # beside the mod's mod.toml
MENUS = ("operation", "campaign", "battles")
MISSION = re.compile(r"^([A-Za-z0-9_]+)/([^/\\]+\.scenario)$", re.I)


class MenuOrderError(ValueError):
    """A menus.toml the build can't read, said for the modder."""


@dataclass
class Order:
    menu: str             # one of MENUS
    missions: list[str]   # "<map pack>/<scenario file>", in the order wanted


def mission(pack: str, file: str) -> str:
    """How menus.toml names a mission: its map's pack name and its scenario file's name."""
    return f"{pack}/{file.replace(chr(92), '/').rsplit('/', 1)[-1]}"


def key(menu: str, name: str) -> tuple[str, str, str]:
    """A mission of a menu as the build compares them: (menu, map pack, scenario file), in lower case."""
    pack, _, file = name.partition("/")
    return menu, pack.lower(), file.lower()


def parse(data: dict, where: str = FILE) -> list[Order]:
    extra = sorted(set(data) - {"order"})
    if extra:
        # not a game rule: what our format reads
        raise MenuOrderError(f"{where}: unknown key {extra[0]!r} (a menus file holds [[order]] tables)")
    rows = data.get("order", [])
    if not isinstance(rows, list):
        raise MenuOrderError(f"{where}: order must be [[order]] tables")
    out = []
    for n, row in enumerate(rows, 1):
        at = f"{where}: [[order]] {n}"
        if not isinstance(row, dict) or set(row) - {"menu", "missions"}:
            # not a game rule: what our format reads
            raise MenuOrderError(f"{at}: an order holds menu and missions, nothing else")
        menu, missions = row.get("menu"), row.get("missions")
        if menu not in MENUS:
            raise MenuOrderError(f"{at}: menu must be one of {', '.join(MENUS)} (got {menu!r})")
        if not isinstance(missions, list) or len(missions) < 2 or not all(isinstance(x, str) for x in missions):
            # not a game rule: an order is of two missions or more
            raise MenuOrderError(f"{at}: missions must list two missions or more, like "
                                 f"[\"Alpha/LevelDesign_BH.scenario\", \"TwoIslands/leveldesign_challenge.scenario\"]")
        bad = next((x for x in missions if not MISSION.match(x)), None)
        if bad is not None:
            raise MenuOrderError(f"{at}: {bad!r} isn't a mission: its map's pack name, a /, and its scenario file")
        keys = [key(menu, x) for x in missions]
        if len(set(keys)) != len(keys):
            raise MenuOrderError(f"{at}: a mission is listed twice")
        out.append(Order(menu, list(missions)))
    return out


def read_mod(folder) -> list[Order]:
    """The mod's menus.toml, or [] when it has none."""
    f = Path(folder) / FILE
    if not f.is_file():
        return []
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise MenuOrderError(f"{FILE}: {exc}") from None
    return parse(data)


def text(orders: list[Order]) -> str:
    """A menus.toml holding `orders` (the Studio writes it)."""
    def quoted(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    out = ["# Where missions show in their menus (MOD_FORMAT §8): each order puts these missions in this order, in "
           "the places they have"]
    for o in orders:
        out += ["", "[[order]]", f"menu = {quoted(o.menu)}", "missions = ["]
        out += [f"    {quoted(x)}," for x in o.missions]
        out.append("]")
    return "\n".join(out) + "\n"


def arrange(ids: list, wanted: list) -> list:
    """`ids` with those of `wanted` it has put in wanted's order, in the places they had there; the rest stay put."""
    present = [w for w in dict.fromkeys(wanted) if w in ids]
    slots = [i for i, x in enumerate(ids) if x in present]
    out = list(ids)
    for slot, w in zip(slots, present):
        out[slot] = w
    return out


def records(m: Ndf, g: Ndf, read_glad) -> dict[tuple[str, str, str], int]:
    """{(menu, map pack, scenario file), both lower case: its menu entry (an object of `g`, the menus)} for every menu
    entry whose map-list entry (`m`) plays a scenario file. `read_glad(member)`: a ZZ_GladPatchableWin.dat member."""
    by_guid = {}
    for i, o in enumerate(g.objects):
        kind = KINDS.get(g.classes[o.cls])
        if kind:
            p = {g.prop_name(pi): v for pi, v in o.props}
            if "GUID" in p:
                by_guid.setdefault(bytes(p["GUID"].payload), (i, kind))
    out = {}
    for mi, o in enumerate(m.objects):
        if m.classes[o.cls] != "TMapLoadInfo":
            continue
        p = {m.prop_name(pi): v for pi, v in o.props}
        found = by_guid.get(bytes(p["GUID"].payload)) if "GUID" in p else None
        root = next((p[k] for k in ("RootDatapackName", "Path") if k in p and p[k].tc in (0x07, 0x1C)), None)
        if found is None or root is None:
            continue
        pack = m.strings[struct.unpack("<I", root.payload[:4])[0]]
        file = entry_scenario(m, mi, read_glad)
        if file:
            out.setdefault(key(found[1], mission(pack, file)), found[0])
    return out


def _list_of(g: Ndf, wanted: list[int]):
    """(object, its property's place) of the menu pack list holding every one of `wanted`, or None."""
    for o in g.objects:
        for k, (_pi, v) in enumerate(o.props):
            if v.tc == 0x11 and set(wanted) <= {local_ref(x) for x in sub_values(v)}:
                return o, k
    return None


def apply(read_glad, orders: list[tuple[Order, str]]) -> tuple[dict, list[str], list[str]]:
    """({member: new bytes} for ZZ_GladPatchableWin.dat, notes, problems): the mods' orders [(Order, its mod's id)],
    in load order, put in the menus. `read_glad(member)` gives a member as the build has it so far, or None."""
    g_raw, m_raw = read_glad(GLOBALS), read_glad(MAPINFO)
    if g_raw is None or m_raw is None:
        # not a game rule: the game or one of its files isn't found
        return {}, [], ["the game's map list or menus aren't in ZZ_GladPatchableWin.dat, so no mission can move there"]
    g, m = Ndf(g_raw), Ndf(m_raw)
    found = records(m, g, read_glad)
    notes, problems, moved = [], [], False
    for order, mod_id in orders:
        at = f"{mod_id}: {FILE}"
        wanted = [found[key(order.menu, x)] for x in order.missions if key(order.menu, x) in found]
        gone = [x for x in order.missions if key(order.menu, x) not in found]
        if gone:
            notes.append(f"{at}: {', '.join(gone)} isn't in {MENU_NAMES[order.menu]}, so it has no place to keep")
        if len(wanted) < 2:
            continue
        spot = _list_of(g, wanted)
        if spot is None:
            # not a game rule: an order moves missions within one list
            problems.append(f"{at}: {', '.join(order.missions)} aren't in one list of {MENU_NAMES[order.menu]}, so "
                            f"they can't be put in one order")
            continue
        o, k = spot
        pi, v = o.props[k]
        items = sub_values(v)
        refs = [local_ref(x) for x in items]
        new = arrange(refs, wanted)
        if new == refs:
            continue
        put = [items[refs.index(r)] if r in wanted else x for r, x in zip(new, items)]
        o.props[k] = (pi, Value(0x11, struct.pack("<I", len(put)) + b"".join(x.encode() for x in put)))
        moved = True
        notes.append(f"{at}: {', '.join(order.missions)} in that order in {MENU_NAMES[order.menu]}")
    return ({GLOBALS: g.to_member(compress=bool(g.flags & 0x80))} if moved else {}), notes, problems
