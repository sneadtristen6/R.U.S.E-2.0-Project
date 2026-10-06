"""A lighthouse's light goes with it (docs/MOD_FORMAT.md §8, erase areas).

The game's lighthouses (the scenery's TypeWarrior/Phare and Phare2) don't shine by themselves: the map's effect set,
the one the effect launcher (TFXLauncher) in each of its scenarios' MapIA names ($/gfx/everything/FX_Atmospheric_<map>),
starts a lighthouse light (the game's GEN_Fx_Phare) at a fixed place for each, beside the map's rain, seagulls and
sounds. Erased, the lighthouses left their lights turning over the empty sea (Blank Ocean, the owner, 2026-10-05: "there
is light coming from the lighthouses that we just gotta get rid of"). So when the erase areas take a map's lighthouse
out, the map gets a copy of its effect set without that light, and its scenarios name the copy; the shipped set keeps
its lights for every other map and scenario naming it. On the shipped maps: D-Day's two lights, Swamps' one and Blitz's
one, each 85 to 301 map units from its lighthouse (2026-10-05). Seen in the game the same day: Blank Ocean's lights
gone ("Lighthouse is gone. Blank maps work.").

The copy is the set's own object with its other actions shared, as the game's sets already share their templates."""
from __future__ import annotations

import re
import struct

from .ndf import Ndf, Value, local_ref, sub_values

GFX = "genglad\\patchable\\gfx\\everything.cpp.gladndfbin"   # the game's effects, in ZZ_GladPatchableWin.dat
LIGHT = "GEN_Fx_Phare"           # the lighthouse light the effect sets start (the game's own)
LIGHTHOUSE = re.compile(r"(^|/)phare[^/]*$", re.I)   # TypeWarrior/Phare, Phare2 (not fx_prod_gyrophare)
NEAR = 2000.0                    # a light this close to a lighthouse (map units, across the ground) is its lamp
SAME = 1.0                       # a lighthouse this close to where it stood still stands


def lighthouses(scenery_raw: bytes) -> list[tuple[float, float]]:
    """Where the map's lighthouses stand (x, y), from its scenery file."""
    from .scenery import Scenery
    sc = Scenery(scenery_raw)
    kinds = {i for i, n in enumerate(sc.names) if LIGHTHOUSE.search(n)}
    return [(mt[3], mt[7]) for _s, mt in sc.walk(only=kinds)] if kinds else []


def gone(before: list, after: list) -> list[tuple[float, float]]:
    """The lighthouses of `before` that `after` no longer has."""
    return [p for p in before if not any(abs(p[0] - q[0]) <= SAME and abs(p[1] - q[1]) <= SAME for q in after)]


def _prop(nd: Ndf, o, name: str) -> Value | None:
    return next((v for pi, v in o.props if nd.prop_name(pi) == name), None)


def _refs(v: Value | None) -> list[int]:
    """The objects of this file a value points at, in order (in lists too)."""
    if v is None:
        return []
    if v.tc == 0x09:
        r = local_ref(v)
        return [] if r is None else [r]
    return [r for x in sub_values(v) for r in _refs(x)] if v.tc in (0x11, 0x12, 0x22) else []


def lights(gfx: Ndf, set_index: int) -> list[tuple[int, tuple[float, float, float]]]:
    """The lighthouse lights an effect set starts: (the set's action that starts it, where it shines)."""
    template = next((i for i, p in gfx.exports.items() if p.rsplit("/", 1)[-1] == LIGHT), None)
    if template is None:
        return []
    out = []
    for a in _refs(_prop(gfx, gfx.objects[set_index], "Actions")):
        act = gfx.objects[a]
        if not any(template in _refs(_prop(gfx, gfx.objects[c], "Action")) for c in _refs(_prop(gfx, act, "Actions"))):
            continue
        at = None
        for var in _refs(_prop(gfx, act, "LocalVariables")):   # pinned_Absolute_Offset: its place
            for k in _refs(_prop(gfx, gfx.objects[var], "InitialValue")):
                o = gfx.objects[k]
                if gfx.classes[o.cls] != "TConstantFloat3":   # D-Day's: the place less the mouse's
                    o = next((gfx.objects[j] for j in _refs(_prop(gfx, o, "Param0"))), None)
                if o is not None and gfx.classes[o.cls] == "TConstantFloat3":
                    at = struct.unpack("<3f", _prop(gfx, o, "Value").payload)
        if at is not None:
            out.append((a, at))
    return out


def scenario_effects(read_glad, pack: str) -> list[tuple[str, Ndf, int]]:
    """The map's scenarios that start an effect set: (their MapIA member, the file, its launcher object), from every
    map-list entry (BATTLES, Operations, the campaign) on the map. `read_glad(member)` gives a ZZ_GladPatchableWin.dat
    member's bytes, any case, or None."""
    from .newmap import _cluster_base, _member, _props, _text
    from .players import MAPINFO
    raw = read_glad(MAPINFO)
    if raw is None:
        return []
    m = Ndf(raw)
    out, seen = [], set()
    for o in m.objects:
        if m.classes[o.cls] != "TMapLoadInfo":
            continue
        p = _props(m, o)
        root = next((_text(m, p[k]) for k in ("RootDatapackName", "Path") if k in p), None)
        base = _cluster_base(m, p) if root and root.lower() == pack.lower() else None
        if not base or not base.lower().endswith("clustermap"):
            continue
        member = _member(base[:-len("ClusterMap")] + "MapIA")
        ia_raw = read_glad(member) if member.lower() not in seen else None
        seen.add(member.lower())
        if ia_raw is None:
            continue
        ia = Ndf(ia_raw)
        out += [(member, ia, k) for k, x in enumerate(ia.objects)
                if ia.classes[x.cls] == "TFXLauncher" and _text(ia, _props(ia, x).get("FXName"))]
    return out


def _copy_without(gfx: Ndf, set_index: int, drop: set[int], path: str) -> None:
    """Add the set's copy, its actions but `drop`, named `path` (the set's own children stay shared)."""
    from .newmap import _string
    o = gfx.objects[set_index]
    props = []
    for pi, v in o.props:
        name = gfx.prop_name(pi)
        if name == "Actions":
            kept = [x for x in sub_values(v) if local_ref(x) not in drop]
            v = Value(v.tc, struct.pack("<I", len(kept)) + b"".join(x.encode() for x in kept))
        elif name == "_ShortDatabaseName" and v.tc == 0x07:
            v = Value(v.tc, struct.pack("<I", _string(gfx, path.rsplit("/", 1)[-1])))
        props.append((pi, v))
    j = gfx.add_object(o.cls, props)
    gfx.add_export(path, j)
    if set_index in gfx.topo:   # a top object like the set it copies
        gfx.set_topo(list(gfx.topo) + [j])


def take_out(read_glad, pack: str, places: list) -> tuple[dict, list[str]]:
    """({ZZ_GladPatchableWin.dat member: new bytes}, notes): the lights of the map's lighthouses that stood at
    `places` (x, y) taken out: a copy of each effect set its scenarios start, without them, which they start instead."""
    if not places:
        return {}, []
    raw = read_glad(GFX)
    if raw is None:
        return {}, []
    from .newmap import _props, _set_text, _text
    gfx = Ndf(raw)
    by_path = {p.lower(): i for i, p in gfx.exports.items()}
    made: dict[str, tuple[str, int] | None] = {}   # the set a scenario names (lower case) -> (its copy's name, lights)
    changes: dict[str, bytes] = {}
    for member, ia, k in scenario_effects(read_glad, pack):
        launcher = ia.objects[k]
        named = _text(ia, _props(ia, launcher)["FXName"])
        key = named.replace("\\", "/").lower()
        if key not in made:
            made[key] = None
            si = by_path.get(key)
            drop = set() if si is None else {a for a, (x, y, _z) in lights(gfx, si)
                                               if any((x - px) ** 2 + (y - py) ** 2 <= NEAR * NEAR for px, py in places)}
            if drop:
                own = gfx.exports[si]
                path, n = f"{own}_{pack}", 2
                while path.lower() in by_path:   # (another build step's copy for this map)
                    path, n = f"{own}_{pack}{n}", n + 1
                _copy_without(gfx, si, drop, path)
                by_path[path.lower()] = gfx._by_export[path]
                made[key] = (path.rsplit("/", 1)[-1], len(drop))
        if made[key] is None:
            continue
        _set_text(ia, launcher, "FXName", named[:named.replace("\\", "/").rfind("/") + 1] + made[key][0])
        changes[member] = ia.to_member(compress=bool(ia.flags & 0x80))
    copies = [v for v in made.values() if v]
    if not copies:
        return {}, []
    changes[GFX] = gfx.to_member(compress=bool(gfx.flags & 0x80))
    notes = [f"lighthouse lights: the light of {n} erased lighthouse(s) taken out; the map's scenarios start "
             f"{name}, a copy of its effects without them" for name, n in copies]
    return changes, notes
