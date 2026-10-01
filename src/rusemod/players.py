"""How many players a map takes: `maps/<map pack>/map.toml` (MOD_FORMAT §8), `players = 8`.

A map played online and in BATTLES has an entry in the menus (`TMultiMapInfo` in `genglad\\patchable\\misc\\
globals.cpp`), tied by GUID to its `TMapLoadInfo` in the map list (`genglad\\patchable\\mapinfo.cpp`, whose `Name`
starts with the count: "(6) Cotentin (3v3)"). The entry holds `NbPlayers`, a size group `CategoryId` (the shipped
maps: none for 2 players, 1 for 3-4, 2 for 6, 3 for 8), the layouts it offers (`DispoMulti2Teams`, `3Teams`,
`4Teams`, `FFA`) and, for a two-team map, `GameType` (1 for 1v1, 2 for 2v2, 3 for 3v3). No shipped map is 4v4 (the
8-player ones are FFA or 2v2v2v2), so where the menus would list a GameType 4 is unknown: past 3 it's left as the
map has it until that is tried in the game.

Where each player starts is the scenario's: a starting point per player in his team (`AllianceNum`). The game takes
a team's starting points in order of `AlliancePriority` (lowest first; the values themselves don't matter, and an
absent one counts as well: '(4) Beta' has team 2 at 3 and 4), so a team of N players needs N starting points. A
two-team 8-player game needs 4 in teams 1 and 2; free-for-all needs 1 in each of teams 1-8. A mod adds the missing
ones in scenario.toml ([[start]], rusemod.scenario.Start). The build refuses a count the scenario can't seat, naming
the starting points that are missing (team t, place k: the team's k-th).

The owner's plan (PLAN A10, 2026-09-30): at least 8 players; past 8 is tried later (the game's own limit may be in
the program).
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass

from .ndf import Ndf, Value

PLAYERS_MOST = 8          # the most any shipped map takes; past it is PLAN A10's later step
GLOBALS = "genglad\\patchable\\misc\\globals.cpp.gladndfbin"
MAPINFO = "genglad\\patchable\\mapinfo.cpp.gladndfbin"
GROUP = {2: None, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3}   # CategoryId by player count, as the shipped maps have it
LAYOUTS = (("DispoMulti2Teams", 2), ("DispoMulti3Teams", 3), ("DispoMulti4Teams", 4), ("DispoMultiFFA", 0))


class PlayersError(ValueError):
    pass


@dataclass
class Players:
    count: int
    entry: str | None = None   # which of the map's entries, by its map-list name, when it has several


def parse_map(data: dict, where: str = "map.toml") -> list[Players]:
    """A map.toml's settings: [Players] when it sets `players`, else []."""
    if "players" not in data:
        if "entry" in data:
            raise PlayersError(f"{where}: entry names which of the map's entries gets players = N; players is missing")
        return []
    n = data["players"]
    if isinstance(n, bool) or not isinstance(n, int) or not 2 <= n <= PLAYERS_MOST:
        raise PlayersError(f"{where}: players must be a whole number from 2 to {PLAYERS_MOST} (past {PLAYERS_MOST} "
                           f"isn't possible yet)")
    entry = data.get("entry")
    if entry is not None and (not isinstance(entry, str) or not entry.strip()):
        raise PlayersError(f"{where}: entry must be the map-list name of one of the map's entries, like "
                           f"\"(6) Cotentin (3v3)\"")
    return [Players(n, entry)]


def map_toml(p: Players | None, header: str = "") -> str:
    lines = [f"# {ln}" for ln in header.splitlines()] + ([""] if header else [])
    if p is not None:
        lines.append(f"players = {p.count}")
        if p.entry:
            lines.append(f'entry = "{p.entry}"')
    return "\n".join(lines) + "\n"


def _props(nd: Ndf, o) -> dict:
    return {nd.prop_name(pi): v for pi, v in o.props}


def _text(nd: Ndf, v) -> str | None:
    return nd.strings[struct.unpack("<I", v.payload[:4])[0]] if v.tc in (0x07, 0x1C) else None


def entries(mapinfo: Ndf, globals_: Ndf, pack: str) -> list[tuple[int, int, str]]:
    """The map's online entries: [(its TMapLoadInfo object, its TMultiMapInfo object, its map-list name)]."""
    multi = {}
    for i, o in enumerate(globals_.objects):
        if globals_.classes[o.cls] == "TMultiMapInfo":
            p = _props(globals_, o)
            if "GUID" in p:
                multi[bytes(p["GUID"].payload)] = i
    out = []
    for i, o in enumerate(mapinfo.objects):
        if mapinfo.classes[o.cls] != "TMapLoadInfo":
            continue
        p = _props(mapinfo, o)
        root = next((_text(mapinfo, p[k]) for k in ("RootDatapackName", "Path") if k in p), None)
        if not root or root.lower() != pack.lower() or "GUID" not in p:
            continue
        g = multi.get(bytes(p["GUID"].payload))
        if g is not None:
            out.append((i, g, _text(mapinfo, p["Name"]) if "Name" in p else ""))
    return out


def scenario_of(mapinfo: Ndf, obj: int, read_glad) -> str | None:
    """The .scenario file (its name, lower case) a TMapLoadInfo loads: its cluster's NDF transaction names a
    ClusterMap file (`genglad\\<BaseName>.cpp.gladndfbin`) whose ScenarioPath names the file. `read_glad(member)`
    gives a member's bytes, any case, or None."""
    from .ndf import local_ref, sub_values
    p = _props(mapinfo, mapinfo.objects[obj])
    if "ClusterLoads" not in p:
        return None
    for v in sub_values(p["ClusterLoads"])[1::2]:
        cluster = local_ref(v)
        if cluster is None:
            continue
        cp = _props(mapinfo, mapinfo.objects[cluster])
        tr = local_ref(cp["NdfTransaction"]) if "NdfTransaction" in cp else None
        if tr is None:
            continue
        tp = _props(mapinfo, mapinfo.objects[tr])
        base = _text(mapinfo, tp["BaseName"]) if "BaseName" in tp else None
        if not base:
            continue
        raw = read_glad("genglad\\" + base.lower() + ".cpp.gladndfbin")
        if raw is None:
            return None
        for s in Ndf(raw).strings:
            if s.lower().endswith(".scenario"):
                return s.replace("/", "\\").rsplit("\\", 1)[-1].lower()
        return None
    return None


def seats(counts: dict, layouts: list[int], players: int) -> list[tuple[int, int]]:
    """What's missing for `players` in each offered layout (2, 3, 4 teams; 0 = free-for-all), given how many starting
    points the scenario has per team ({team: count}, or {team: a collection of them}): [(team, k), ...] in order, the
    team's k-th starting point missing (empty: every player has one). The game seats a team's players on its starting
    points whatever their places (AlliancePriority) say, so only the count matters."""
    def have(t):
        v = counts.get(t, 0)
        return int(v) if isinstance(v, int) else len(v)
    missing = set()
    for teams in layouts:
        if teams == 0:
            need = {t: 1 for t in range(1, players + 1)}
        elif players % teams:
            continue  # this layout can't take this many players evenly: it isn't offered (apply_players warns)
        else:
            need = {t: players // teams for t in range(1, teams + 1)}
        missing |= {(t, k) for t, n in need.items() for k in range(have(t) + 1, n + 1)}
    return sorted(missing)


def _set_int(nd: Ndf, o, name: str, value: int | None) -> None:
    """Set an int property of object `o` (adding it when the object hasn't got it); None drops it."""
    for k, (pi, v) in enumerate(o.props):
        if nd.prop_name(pi) == name:
            if value is None:
                del o.props[k]
            else:
                o.props[k] = (pi, Value(0x02, struct.pack("<i", value)))
            return
    if value is None:
        return
    pi = next((i for i, (n, c) in enumerate(nd.props) if n == name and c == o.cls), None)
    if pi is None:
        pi = nd.add_prop(name, o.cls)
    o.props.append((pi, Value(0x02, struct.pack("<i", value))))


def renamed(name: str, players: int, two_teams: bool) -> str:
    """The map-list name with the new count: "(6) Cotentin (3v3)" -> "(8) Cotentin (4v4)"."""
    out = re.sub(r"^\(\d+\)", f"({players})", name) if re.match(r"^\(\d+\)", name) else f"({players}) {name}"
    if two_teams:
        out = re.sub(r"\((\d+)v(s?)(\d+)\)$", lambda m: f"({players // 2}v{m.group(2)}{players // 2})", out)
    return out


def apply_players(read_glad, pack: str, setting: Players, starting_points, warn=None) -> tuple[dict, list[str]]:
    """({member: new bytes} for ZZ_GladPatchableWin.dat, notes): the map's entry set to `setting.count` players.
    `read_glad(member)` gives a member's bytes (as the build has it so far); `starting_points(scenario file)` gives
    how many starting points that scenario has per team, {team: count} (after the mods' own starts), or None when it
    can't be read. `warn(message)` is told what builds but may not work as meant. Raises PlayersError when the map
    has no online entry, or the scenario can't seat that many."""
    g_raw, m_raw = read_glad(GLOBALS), read_glad(MAPINFO)
    if g_raw is None or m_raw is None:
        raise PlayersError("the game's map list or menus aren't in ZZ_GladPatchableWin.dat")
    g, m = Ndf(g_raw), Ndf(m_raw)
    found = entries(m, g, pack)
    if not found:
        raise PlayersError(f"{pack} isn't played online or in BATTLES (it has no multiplayer entry), so its player "
                           f"count can't change")
    if setting.entry:
        found = [f for f in found if f[2] == setting.entry]
        if not found:
            names = ", ".join(repr(n) for _i, _g, n in entries(m, g, pack))
            raise PlayersError(f"{pack} has no entry {setting.entry!r} (its entries: {names})")
    elif len(found) > 1:
        names = ", ".join(repr(n) for _i, _g, n in found)
        raise PlayersError(f"{pack} has several entries ({names}): say which in map.toml (entry = \"...\")")
    mi, gi, name = found[0]
    multi = g.objects[gi]
    p = _props(g, multi)
    layouts = [teams for key, teams in LAYOUTS if key in p and p[key].scalar()]
    scenario_file = scenario_of(m, mi, read_glad)
    places = starting_points(scenario_file) if scenario_file else None
    if places is None:
        raise PlayersError(f"{pack}: the scenario of {name!r} can't be read, so its starting points can't be counted")
    missing = seats(places, layouts, setting.count)
    if missing:
        where = ", ".join(f"team {t}, place {q}" for t, q in missing)
        raise PlayersError(f"{pack}: {setting.count} players need a starting point for each; {scenario_file} has none "
                           f"for {where}. Add them (scenario.toml [[start]], or the Studio's Add starting point)")
    before = p["NbPlayers"].scalar() if "NbPlayers" in p else None
    if 3 in layouts and setting.count % 3 and warn is not None:
        warn(f"{pack}: {name!r} offers three teams, but {setting.count} players can't make three even teams: that "
             f"layout may not be offered, or may give teams of different sizes (untested). Use a multiple of 3, or "
             f"leave it if the other layouts are the ones meant")
    two_teams = layouts == [2] or (2 in layouts and 0 not in layouts and "GameType" in p)
    _set_int(g, multi, "NbPlayers", setting.count)
    _set_int(g, multi, "CategoryId", GROUP[setting.count])
    kept = ""
    if "GameType" in p and two_teams:
        if setting.count // 2 <= 3:
            _set_int(g, multi, "GameType", setting.count // 2)
        else:  # no shipped map is 4v4: where the menus list a GameType 4 is untested, so it stays as it was
            kept = f"; its game type stays {p['GameType'].scalar()} (a 4v4 type is untested)"
    mp = _props(m, m.objects[mi])
    new_name = renamed(name, setting.count, two_teams)
    if new_name != name and "Name" in mp:
        users = [o for o in m.objects for _pi, v in o.props if v.tc in (0x07, 0x1C) and v.payload == mp["Name"].payload]
        if len(users) == 1:
            m.set_string(struct.unpack("<I", mp["Name"].payload[:4])[0], new_name)
        else:  # the text is shared: this entry gets its own
            i = m.string_index(new_name)
            i = m.add_string(new_name) if i is None else i
            for k, (pi, v) in enumerate(m.objects[mi].props):
                if m.prop_name(pi) == "Name":
                    m.objects[mi].props[k] = (pi, Value(v.tc, struct.pack("<I", i)))
    out = {GLOBALS: g.to_member(compress=bool(g.flags & 0x80)), MAPINFO: m.to_member(compress=bool(m.flags & 0x80))}
    return out, [f"{name!r}: {before} -> {setting.count} players, named {new_name!r}; every player has a starting "
                 f"point in {scenario_file}{kept}"]
