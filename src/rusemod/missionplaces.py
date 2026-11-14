"""The places a mission needs on its map from its start, and the missions a set of mods leaves without them (the owner,
2026-11-13: on the six library mods' warning, "It should be warning on every version if there's an error"; on a check
for any mod whose map lacks places a mission needs, "use your best judgment"; RUSEMAIN's call: yes, with nothing of
the game in the apps).

Nothing of the game is kept in the apps for this: each build reads the player's own copy of the game, as the set's
mods leave it and as the game ships it. A mission (a campaign chapter, an Operation or the tutorial: each entry of the
map list that a menu pack of those menus lists, as the set leaves the menus) loads its scenario cluster
(ZZ_GladPatchableWin.dat), which names its layout (a .scenario in DataMap_Win.dat) and its script folder
(DataDir:\\Test\\map\\<map>\\Scripting<...>, in IA_Common.dat: rusemod.fairplay.script_folders); the mission's match
script there is effetmap.xyz, and a co-op Operation's folder also has effetmapmultiplayer.xyz. A BATTLES match never
runs a map folder's scripts (rusemod.fairplay, 2026-10-30), so BATTLES maps aren't looked at.

What stops a mission (F-189: a player's crash report of 2026-11-06 with the Pinnacle Map Pack on; read in the game's
scripts on 2026-11-10, round 2 on FL-101 and trace 1): its script finds a named place by its name
(leveldesignsolo.helper.TagZoneDetection('name')), and the zone gets its size only when the layout holds a design item
of that name; every units-in-zone condition (ConditionDetectUnitDansZoneDetection) on the mission's start-up list (its
launch descriptor's PostInit) is scanned once a second from the start, and the scan reads that size unchecked. So a
zone such a condition watches that the layout lacks stops the mission about a second after it starts. That is what is
checked here. Places a script uses later (positions, units, zones of later steps) are not: what a missing one does
there wasn't read.

The game as sold has no such mission (its menu missions read on 2026-11-10, and with this code on 2026-11-13: none).
A mission whose layout and scripts the set leaves as the game ships them (the same files, as its cluster names them)
isn't looked at; for one the set changes, only what the set adds is said: the zones missing with the set that the
mission as shipped doesn't miss. Which change is why: the layout (its scenario, or its cluster naming another) when the
game's own scripts miss those zones on it, the scripts when they miss them on the game's own layout, both when only the
two together do.

A layout our scenario reader can't take (two of the Balanced Realism Mod's have 20 bytes after their design items) is
read up to its design items; one that can't be read even so has the zones looked for as text in its bytes (a zone
whose name isn't anywhere in the file isn't in the layout). A changed script or cluster that can't be read is said
(`unread`)."""
from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass, field

from .ndf import Ndf, local_ref, sub_values
from .pyscript import ScriptError

GLAD = "ZZ_GladPatchableWin.dat"   # the menus and the missions' clusters
DATA = "DataMap_Win.dat"           # the layouts (scenario files)
IA = "IA_Common.dat"               # the maps' own scripts
MAPINFO = "genglad\\patchable\\mapinfo.cpp.gladndfbin"        # the map list (rusemod.players.MAPINFO)
GLOBALS = "genglad\\patchable\\misc\\globals.cpp.gladndfbin"  # the menus (rusemod.players.GLOBALS)
KINDS = {"TChapterMapInfo": "campaign", "TChallengeMapInfo": "operation"}  # (TMultiMapInfo, BATTLES: no script runs)
ORDER = ("campaign", "operation", "tutorial")
SCRIPT_ROOT = "genpython\\1000\\test\\"   # where a cluster's DataDir:\Test\... folder is in IA_Common.dat (fairplay)
MATCH_SCRIPTS = ("effetmap.xyz", "effetmapmultiplayer.xyz")   # a mission's match scripts in its folder
_FOLDER = re.compile(r"(?i)datadir:\\+test\\+(map\\+[a-z0-9_]+\\+scripting[a-z0-9_]*)\\*")
_LAYOUT = re.compile(r"(?i)^datadir:[\\/]+test[\\/]+map[\\/]+(.+\.scenario)$")
CONDITION = "ConditionDetectUnitDansZoneDetection"   # units in a zone: its scan reads the zone's size
TAG = "TagZoneDetection"                             # a zone found by its name in the layout
# what reading a set's files can raise (a value of another type where one is read is a TypeError: the review of
# 95e9b910, 2026-11-14); the build's mission_places takes anything else as one note too
_READ_ERRORS = (ValueError, KeyError, IndexError, TypeError, AttributeError, struct.error, zlib.error,
                UnicodeDecodeError, RecursionError)


@dataclass(frozen=True)
class Mission:
    kind: str        # "campaign", "operation" or "tutorial"
    name: str        # its name in the map list (M06_Ardennes_chapter1, Challenge - 1v2 Alpha (BirHakeim))
    cluster: str     # its scenario cluster: a member of ZZ_GladPatchableWin.dat, lower case
    layouts: tuple   # the layouts its cluster names: members of DataMap_Win.dat, lower case (one for every mission
    # of the game)
    scripts: tuple   # its match scripts: members of IA_Common.dat, lower case (whether the pack has them or not)
    problem: str = ""   # why its cluster can't be read (then it names no file here)
    title: int = 0      # the text key of its name in the menus (its menu entry's Description), 0 for none


@dataclass
class Missing:
    mission: Mission
    zones: list           # the zones its start-up conditions watch that its layout lacks with the set (and not as
    # shipped), sorted
    layout: bool          # its layout's change is why (its scenario, or its cluster naming another)
    script: bool          # its scripts' change is why
    repointed: bool       # its cluster names other files than the game's does (or it's a mission the game hasn't)


@dataclass
class Found:
    missing: list = field(default_factory=list)   # [Missing], in the map list's order
    unread: list = field(default_factory=list)    # [(Mission, why)]: a changed script or cluster that can't be read


def _text(nd: Ndf, v) -> str | None:
    return nd.strings[struct.unpack("<I", v.payload[:4])[0]] if v is not None and v.tc in (0x07, 0x1C) else None


def _props(nd: Ndf, o) -> dict:
    return {nd.prop_name(pi): v for pi, v in o.props}


def _member(base: str) -> str:
    """'Patchable\\Scenario\\X\\Y\\ClusterMap' -> its compiled file in ZZ_GladPatchableWin.dat (rusemod.newmap)."""
    return "genglad\\" + base.replace("/", "\\").lower() + ".cpp.gladndfbin"


def _cluster_base(m: Ndf, load: dict) -> str | None:
    """The scenario cluster a map-list entry loads (its NDF transaction's BaseName; rusemod.newmap)."""
    for v in sub_values(load["ClusterLoads"])[1::2] if "ClusterLoads" in load else []:
        c = local_ref(v)
        cp = _props(m, m.objects[c]) if c is not None else {}
        tr = local_ref(cp["NdfTransaction"]) if "NdfTransaction" in cp else None
        base = _text(m, _props(m, m.objects[tr]).get("BaseName")) if tr is not None else None
        if base:
            return base
    return None


def pairing(raw: bytes) -> tuple[tuple, tuple]:
    """(layouts, match scripts) a scenario cluster names: DataMap_Win.dat and IA_Common.dat members, lower case (Bir
    Hakeim's cluster names its layout twice, Alpha//LevelDesign_BH.scenario and Alpha\\LevelDesign_BH.scenario: one)."""
    layouts, folders = set(), set()
    for s in Ndf(raw).strings:
        m = _LAYOUT.match(s)
        if m:
            layouts.add("test\\map\\" + re.sub(r"[\\/]+", "\\\\", m.group(1)).lower())
        f = _FOLDER.fullmatch(s)
        if f:
            folders.add(SCRIPT_ROOT + re.sub(r"\\+", "\\\\", f.group(1)).lower())
    return tuple(sorted(layouts)), tuple(f"{f}\\{s}" for f in sorted(folders) for s in MATCH_SCRIPTS)


def missions(read_glad) -> list[Mission]:
    """Every mission a player can pick in the menus `read_glad` gives (member -> bytes or None, ZZ_GladPatchableWin.dat
    as the set leaves it): each map-list entry whose menu entry, listed by a menu pack, is a campaign chapter, an
    Operation or the tutorial's chapter, once for each of those menus it is in, with the files its cluster names. An
    entry whose cluster isn't there is left out (the game can't load it either); one whose cluster can't be read names
    no file and says why (Mission.problem). Menus that can't be read raise ValueError (or the reader's own error), for
    the build to say so. [] when the menus aren't there."""
    m_raw, g_raw = read_glad(MAPINFO), read_glad(GLOBALS)
    if m_raw is None or g_raw is None:
        return []
    m, g = Ndf(m_raw), Ndf(g_raw)
    listed, tuto = set(), set()
    for o in g.objects:
        p = _props(g, o)
        refs = {local_ref(x) for v in p.values() if v.tc == 0x11 for x in sub_values(v)}
        listed |= refs
        if "IsTuto" in p and p["IsTuto"].scalar():
            tuto |= refs
    by_guid: dict = {}
    titles: dict = {}   # GUID -> the text key of its name in the menus (its Description)
    for i, o in enumerate(g.objects):
        kind = KINDS.get(g.classes[o.cls])
        p = _props(g, o) if kind else {}
        if kind and "GUID" in p and i in listed:
            by_guid.setdefault(bytes(p["GUID"].payload), set()).add("tutorial" if i in tuto else kind)
            said = p.get("Description")
            if said is not None and said.tc == 0x1D and len(said.payload) >= 8:
                titles.setdefault(bytes(p["GUID"].payload), struct.unpack("<Q", bytes(said.payload[:8]))[0])
    out = []
    for o in m.objects:
        if m.classes[o.cls] != "TMapLoadInfo":
            continue
        p = _props(m, o)
        kinds = by_guid.get(bytes(p["GUID"].payload), set()) if "GUID" in p else set()
        base = _cluster_base(m, p) if kinds else None
        raw = read_glad(_member(base)) if base else None
        if raw is None:
            continue
        try:
            layouts, scripts, problem = *pairing(raw), ""
        except _READ_ERRORS as exc:
            layouts, scripts, problem = (), (), str(exc) or type(exc).__name__
        for kind in sorted(kinds, key=ORDER.index):
            out.append(Mission(kind, _text(m, p.get("Name")) or base, _member(base), layouts, scripts, problem,
                               titles.get(bytes(p["GUID"].payload), 0)))
    return out


def _str(v) -> str:
    return v.decode("latin-1") if isinstance(v, bytes) else str(v)


def _last(name) -> str:
    return (name or "").rsplit(".", 1)[-1]


def start_zones(raw: bytes) -> set[str]:
    """The zones a match script (.xyz bytes) watches from its start: the names given to TagZoneDetection for the zone
    of each units-in-zone condition on a start-up list (PostInit). Raises ScriptError when it can't be read."""
    from .missions import _follow, module_code
    calls, launch = {}, []
    try:
        _follow(module_code(raw), {}, [], calls, launch)
    except ScriptError:
        raise   # (its own words, as they are: a player's note names no class of our code)
    except (IndexError, KeyError, TypeError, ValueError, struct.error, zlib.error, RecursionError) as exc:
        raise ScriptError(f"its code can't be followed ({exc})" if str(exc) else "its code can't be followed") \
            from None

    def made(v):
        """A value as the call that made it, when it's a name a call was stored under."""
        return ("call", *calls[v[1]]) if v and v[0] == "name" and v[1] in calls else v

    started = []
    for kw in [k for _c, k, _a in calls.values()] + launch:
        post = kw.get("PostInit")
        if post and post[0] == "list":
            started += post[1]
    out = set()
    for v in started:
        what = made(v)
        if not (what and what[0] == "call" and _last(what[1]) == CONDITION):
            continue
        tag = made(what[2].get("Detecteur"))
        if tag and tag[0] == "call" and _last(tag[1]) == TAG:
            arg = tag[3][0] if tag[3] else tag[2].get("name")
            if arg and arg[0] == "const" and isinstance(arg[1], (str, bytes)):
                out.add(_str(arg[1]))
    return out


def layout_items(raw: bytes) -> list | None:
    """A layout's (.scenario bytes) design items (rusemod.scenario's), read up to them when bytes follow them; None
    when it can't be read even so."""
    from .scenario import MAGIC, Scenario, ScenarioError, _items
    try:
        return Scenario.read(raw).items
    except (ScenarioError,) + _READ_ERRORS:
        try:
            if raw[:len(MAGIC)] != MAGIC:
                return None
            at = 40 + struct.unpack_from("<I", raw, 36)[0]   # past the header, the version, 1 and the zones
            size = struct.unpack_from("<I", raw, at)[0]
            if at + 4 + size > len(raw):
                return None
            return _items(Ndf(raw[at + 4:at + 4 + size]))
        except _READ_ERRORS:
            return None


def place_names(raw: bytes) -> set[str] | None:
    """The names of a layout's named places (.scenario bytes): its listed design items' Name. Read up to the design
    items when bytes follow them; None when it can't be read even so."""
    items = layout_items(raw)
    if items is None:
        return None
    return {it.values["Name"] for it in items if it.listed and isinstance(it.values.get("Name"), str)
            and it.values["Name"]}


def _held(raw: bytes | None, zones: set[str]) -> set[str]:
    """Which of `zones` a layout holds: its named places; for one that can't be read, the ones whose name is in its
    bytes (latin-1 or UTF-16); none for no file."""
    if raw is None:
        return set()
    names = place_names(raw)
    if names is not None:
        return zones & names
    return {z for z in zones if z.encode("latin-1", "ignore") in raw or z.encode("utf-16-le") in raw}


def _lacks(zones: set[str], layouts: list) -> set[str]:
    """The zones none of the layouts (bytes or None) holds: a cluster naming two layouts is taken at its best."""
    out = set(zones)
    for raw in layouts:
        out -= _held(raw, zones)
    return out


def _zones(scripts: list) -> set[str]:
    out = set()
    for raw in scripts:
        if raw is not None:
            out |= start_zones(raw)
    return out


def check(final, shipped) -> Found:
    """The missions the set leaves without zones they watch from the start. `final` and `shipped`: (read_glad,
    read_data, read_ia), each member -> bytes or None (any case), the game's three packs as the set leaves them and as
    the game ships them."""
    fg, fd, fi = final
    sg, sd, si = shipped
    found = Found()
    for mi in missions(fg):
        if mi.problem:   # its cluster, as the set leaves it, can't be read (said, unless it's the game's own)
            if fg(mi.cluster) != sg(mi.cluster):
                found.unread.append((mi, mi.problem))
            continue
        if not mi.layouts:
            continue   # (no layout to look in: every mission of the game names one)
        was = sg(mi.cluster)
        try:
            old = pairing(was) if was is not None else None   # what the game's own cluster of it names
        except _READ_ERRORS:
            old = None
        layouts, scripts = [fd(x) for x in mi.layouts], [fi(x) for x in mi.scripts]
        layout_changed = old is None or old[0] != mi.layouts or layouts != [sd(x) for x in mi.layouts]
        script_changed = old is None or old[1] != mi.scripts or scripts != [si(x) for x in mi.scripts]
        if not (layout_changed or script_changed):
            continue   # as the game ships it
        try:
            needs = _zones(scripts)
        except ScriptError as exc:
            found.unread.append((mi, str(exc)))
            continue
        lacking = _lacks(needs, layouts)
        if not lacking:
            continue
        before, own_needs = set(), None   # what the mission as the game ships it lacks: not the set's doing
        if old is not None:
            try:
                own_needs = _zones([si(x) for x in old[1]])
                before = _lacks(own_needs, [sd(x) for x in old[0]])
            except ScriptError:
                own_needs = None
        lacking -= before
        if not lacking:
            continue
        on_layout = layout_changed and own_needs is not None and bool(_lacks(own_needs, layouts) - before)
        on_script = script_changed and old is not None and bool(_lacks(needs, [sd(x) for x in old[0]]) - before)
        if not (on_layout or on_script):   # only the two together (or a mission the game hasn't)
            on_layout, on_script = layout_changed, script_changed
        found.missing.append(Missing(mi, sorted(lacking), on_layout, on_script,
                                     old is None or old != (mi.layouts, mi.scripts)))
    return found
