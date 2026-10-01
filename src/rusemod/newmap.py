"""New maps: a shipped map copied under a new name, listed in BATTLES as a map of its own (PLAN §13, level 2).

A mod makes one with `maps/<NewName>/map.toml` (MOD_FORMAT §8):

    clone_of = "M04_Cotentin"                    # the shipped map it starts from (its pack name)
    name = "Omaha Ridge"                         # what the menus call it, or a table: [name] us = ... fr = ...
    entry = "(6) Cotentin (3v3)"                 # which of the shipped map's BATTLES entries, when it has several

The build then adds the new map to the modded copy (FORMATS.md §6 "A map's files, and a new one"):
- its own pack, `Maps\\PC\\DataMap<NewName>_v09.dat`: the shipped map's, with a pack id of its own;
- in ZZ_GladPatchableWin.dat: the map's ClusterMap (which mounts that pack and names the map's data folder), the
  scenario's ClusterMap and MapIA (which name its scenario, camera paths and bluff zones), each copied under the
  new name and pointed at the new files; a map-list entry (TMapLoadInfo, a top object, as every entry is) and a
  BATTLES entry (TMultiMapInfo, in the same menu pack as the shipped map, after the maps of its size) tied to it by
  a GUID of their own;
- in DataMap_Win.dat: the scenario, its camera paths and bluff zones, and the map's grid (`mapinfo.win`);
- in ZZ_Win.dat: the map's environment and diversity textures and its menu pictures, and its name in the menus'
  dictionary (`flash_txt.dic`) in all ten languages.
Everything else (the scenery's models, sounds, lighting, the in-mission dialogue) stays the shipped map's: those
files are only read, and two maps never load at once.

Nothing here is random: the ids come from the new map's name, so every PC builds the same files (a multiplayer
game needs both sides to have the same map list). Edits a mod makes to `maps/<NewName>/` then apply to the copy as
to any map, and the shipped map stays as it was.
"""
from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass, field

from . import loc
from .dic import Dic, name_to_key
from .ndf import Ndf, Value, local_ref, sub_values
from .players import GLOBALS, MAPINFO, entries

BS = "\\"
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
NAME_LONGEST = 60          # characters of a map's name in the menus
MENU_TEXTS = "flash_txt"   # the menus' dictionary: the shipped maps' names are M_D_01 .. M_D_30 there
KEY_STEM, KEY_FIRST = "M_D_", 31
TRACK_STEM, TRACK_FIRST = "MP", 31    # the shipped BATTLES maps are MP01 .. MP30
LADDER = ("DispoLadder1v1", "DispoLadder2v2")   # ranked matchmaking: the shipped map's, not a copy's
DROPPED = LADDER + ("RewardId",)


class NewMapError(ValueError):
    """A new map that can't be made, said for the modder: what to change."""


@dataclass
class NewMap:
    clone_of: str                 # the shipped map's pack name
    names: dict                   # language folder (loc.LANGS) -> the map's name in the menus; "us" always there
    entry: str | None = None      # which of the shipped map's BATTLES entries, by its map-list name


# --- map.toml -------------------------------------------------------------------------------------------------------
def parse(data: dict, where: str = "map.toml", folder: str = "") -> list[NewMap]:
    """A map.toml's new-map settings: [NewMap] when it says clone_of, else [] (and `name` alone is a mistake)."""
    if "clone_of" not in data:
        if "name" in data:
            raise NewMapError(f"{where}: name is for a new map; add clone_of = \"<the shipped map's pack name>\" "
                              f"(a shipped map's name in the menus can't change here)")
        return []
    src = data["clone_of"]
    if not isinstance(src, str) or not re.match(r"^[A-Za-z0-9_]+$", src):
        raise NewMapError(f"{where}: clone_of must be a shipped map's pack name, like \"M04_Cotentin\" (D-Day) or "
                          f"\"TwoIslands\"")
    if folder and src.lower() == folder.lower():
        raise NewMapError(f"{where}: a map can't be a copy of itself; give the new map's folder another name")
    raw = data.get("name", folder)
    if isinstance(raw, str):
        names = {"us": raw.strip()}
    elif isinstance(raw, dict):
        names = {}
        for lang, text in raw.items():
            code = loc.ALIASES.get(str(lang).lower(), str(lang).lower())
            if code not in loc.LANGS:
                raise NewMapError(f"{where}: [name] {lang!r} isn't a language; they are {' '.join(loc.LANGS)}")
            if not isinstance(text, str):
                raise NewMapError(f"{where}: [name] {lang} must be text")
            if text.strip():
                names[code] = text.strip()
        if "us" not in names:
            raise NewMapError(f"{where}: [name] needs us = \"...\" (English), which the other languages fall back to")
    else:
        raise NewMapError(f"{where}: name must be text, or a table of languages ([name] us = \"...\")")
    for lang, text in names.items():
        if not text:
            raise NewMapError(f"{where}: the new map needs a name for the menus (name = \"...\")")
        if len(text) > NAME_LONGEST:
            raise NewMapError(f"{where}: the {lang} name is {len(text)} characters; the menus take {NAME_LONGEST}")
        if any(ord(c) < 32 for c in text):
            raise NewMapError(f"{where}: the {lang} name has a control character")
    entry = data.get("entry")
    if entry is not None and (not isinstance(entry, str) or not entry.strip()):
        raise NewMapError(f"{where}: entry must be the map-list name of one of {src}'s BATTLES entries, like "
                          f"\"(6) Cotentin (3v3)\"")
    return [NewMap(src, names, entry)]


def check_name(new: str) -> None:
    """Refuse a new map's folder name the game's files can't carry."""
    if not NAME.match(new):
        raise NewMapError(f"maps/{new}: a new map's folder name is its pack name: a letter, then up to 39 letters, "
                          f"digits and _ (like OmahaRidge)")
    if new.lower().startswith("flat_"):
        raise NewMapError(f"maps/{new}: names starting flat_ belong to the game's test maps; pick another")


# --- ids, the same on every PC -----------------------------------------------------------------------------------------
def guid_for(new: str, what: str) -> bytes:
    """16 bytes shaped like a random (version 4) GUID, from the new map's name: the same on every PC."""
    b = bytearray(hashlib.md5(f"rusemod new map {what} {new.lower()}".encode()).digest())
    b[7] = (b[7] & 0x0F) | 0x40   # (bytes_le: the version nibble is the high one of byte 7)
    b[8] = (b[8] & 0x3F) | 0x80
    return bytes(b)


# --- the files a copy gets ---------------------------------------------------------------------------------------------
@dataclass
class Clone:
    new: str
    source: str                                     # the shipped map's folder name, as its entry spells it
    glad: dict = field(default_factory=dict)        # ZZ_GladPatchableWin.dat: member -> bytes (added, and the map
    data: dict = field(default_factory=dict)        #   list and menus changed); DataMap_Win.dat: added members
    zz: dict = field(default_factory=dict)          # ZZ_Win.dat: added members
    texts: dict = field(default_factory=dict)       # ZZ_Win.dat: changed dictionaries
    pack_id: bytes = b""                            # the new pack's id (its header)
    scenario: str = ""                              # the scenario file (lower case) the new entry loads
    key: str = ""                                   # the name's text key, e.g. M_D_31
    entry_name: str = ""                            # the new map-list name, e.g. "(6) Omaha Ridge (3v3)"
    notes: list = field(default_factory=list)


class Files:
    """One pack as the build has it so far: read(member) -> bytes or None (any case), names(prefix) -> [members]."""

    def __init__(self, members: dict, read_base=None, base_names=()):
        self._mine = {k.lower(): v for k, v in members.items()}
        self._read_base, self._base = read_base, [n for n in base_names]

    def read(self, member: str):
        key = member.lower()
        if key in self._mine:
            return self._mine[key]
        return self._read_base(member) if self._read_base else None

    def names(self, prefix: str) -> list:
        p = prefix.lower()
        return sorted({n for n in list(self._base) + list(self._mine) if n.lower().startswith(p)}, key=str.lower)


def _props(nd: Ndf, o) -> dict:
    return {nd.prop_name(pi): v for pi, v in o.props}


def _text(nd: Ndf, v) -> str | None:
    return nd.strings[struct.unpack("<I", v.payload[:4])[0]] if v is not None and v.tc in (0x07, 0x1C) else None


def _string(nd: Ndf, text: str) -> int:
    i = nd.string_index(text)
    return nd.add_string(text) if i is None else i


def _rewrite(nd: Ndf, v: Value, ref, text) -> Value:
    """`v` with its strings passed through text(s) and its local references through ref(index) (lists, maps and
    pairs rebuilt around them); `v` itself when nothing changes."""
    if v.tc in (0x07, 0x1C):
        s = _text(nd, v)
        t = text(s)
        return v if t == s else Value(v.tc, struct.pack("<I", _string(nd, t)))
    if v.tc == 0x08:
        s = bytes(v.payload[4:]).decode("utf-16-le")
        t = text(s)
        if t == s:
            return v
        enc = t.encode("utf-16-le")
        return Value(0x08, struct.pack("<I", len(enc)) + enc)
    if v.tc == 0x09:
        i = local_ref(v)
        if i is None:
            return v
        j = ref(i)
        return v if j == i else Value(0x09, v.payload[:4] + struct.pack("<I", j) + v.payload[8:])
    if v.tc in (0x11, 0x12, 0x22):
        subs = sub_values(v)
        new = [_rewrite(nd, x, ref, text) for x in subs]
        if all(a is b for a, b in zip(subs, new)):
            return v
        body = b"".join(x.encode() for x in new)
        if v.tc == 0x22:
            return Value(0x22, body)
        return Value(v.tc, struct.pack("<I", len(new) // (2 if v.tc == 0x12 else 1)) + body)
    return v


def _copy(nd: Ndf, i: int, remap: dict, text) -> int:
    """A copy of object `i` and of every object it reaches (each once), with text(s) applied to their strings."""
    if i in remap:
        return remap[i]
    o = nd.objects[i]
    j = nd.add_object(o.cls, [])
    remap[i] = j
    nd.objects[j].props = [(pi, _rewrite(nd, v, lambda k: _copy(nd, k, remap, text), text)) for pi, v in o.props]
    return j


def _set(nd: Ndf, o, name: str, value: Value | None) -> None:
    """Set (or with None drop) property `name` of object `o`, keeping its place."""
    for k, (pi, _v) in enumerate(o.props):
        if nd.prop_name(pi) == name:
            if value is None:
                del o.props[k]
            else:
                o.props[k] = (pi, value)
            return
    if value is not None:
        pi = next((i for i, (n, c) in enumerate(nd.props) if n == name and c == o.cls), None)
        o.props.append((nd.add_prop(name, o.cls) if pi is None else pi, value))


def _swap_strings(nd: Ndf, swap) -> int:
    """Rename strings across a whole file (one we copy, so all its users follow): swap(s) -> new text or None. Wide
    strings in the objects too. Returns how many changed."""
    n = 0
    for i, s in enumerate(nd.strings):
        t = swap(s)
        if t is not None and t != s:
            nd.set_string(i, t)
            n += 1
    for o in nd.objects:
        for k, (pi, v) in enumerate(o.props):
            if v.tc == 0x08:
                s = bytes(v.payload[4:]).decode("utf-16-le")
                t = swap(s)
                if t is not None and t != s:
                    enc = t.encode("utf-16-le")
                    o.props[k] = (pi, Value(0x08, struct.pack("<I", len(enc)) + enc))
                    n += 1
    return n


def _member(nd_path: str) -> str:
    """'Patchable\\Scenario\\X\\Y\\ClusterMap' -> the compiled file in ZZ_GladPatchableWin.dat."""
    return "genglad" + BS + nd_path.replace("/", BS).lower() + ".cpp.gladndfbin"


def _datadir(path: str) -> str | None:
    """'DataDir:\\Test\\Map\\X/LevelDesign.scenario' -> 'test\\map\\x\\leveldesign.scenario' (a member of a data pack)."""
    m = re.match(r"^DataDir:[\\/](.+)$", path, re.I)
    return m.group(1).replace("/", BS).lower() if m else None


def _under(folder: str):
    """A pattern for a path under the map folder `folder`: 'Test\\Map\\<folder>' then a separator."""
    return re.compile(r"^(DataDir:[\\/]Test[\\/]Map[\\/])" + re.escape(folder) + r"([\\/].+)$", re.I)


def make(new: str, spec: NewMap, glad: Files, data: Files, zz: Files) -> Clone:
    """The files that add the new map `new`, a copy of `spec.clone_of`, given the three packs as the build has them
    (ZZ_GladPatchableWin.dat, DataMap_Win.dat, ZZ_Win.dat). Raises NewMapError with what to change."""
    check_name(new)
    src = spec.clone_of
    g_raw, m_raw = glad.read(GLOBALS), glad.read(MAPINFO)
    if g_raw is None or m_raw is None:
        raise NewMapError("the game's map list or menus aren't in ZZ_GladPatchableWin.dat, so no map can be added")
    g, m = Ndf(g_raw), Ndf(m_raw)
    low = new.lower()
    for o in m.objects:
        if m.classes[o.cls] == "TMapLoadInfo":
            p = _props(m, o)
            if any((_text(m, p.get(k)) or "").lower() == low for k in ("RootDatapackName", "Path")):
                raise NewMapError(f"maps/{new}: the game already has a map called {new}; give the new map another "
                                  f"folder name")
    found = entries(m, g, src)
    if not found:
        known = any(m.classes[o.cls] == "TMapLoadInfo" and any(
            (_text(m, _props(m, o).get(k)) or "").lower() == src.lower() for k in ("RootDatapackName", "Path"))
            for o in m.objects)
        if known:
            raise NewMapError(f"maps/{new}: {src} isn't played in BATTLES (it has no skirmish entry), so it can't "
                              f"be copied as a skirmish map yet; start from a map BATTLES lists")
        raise NewMapError(f"maps/{new}: clone_of = {src!r} isn't a map of this game (it takes the map's pack name, "
                          f"like M04_Cotentin for D-Day)")
    if spec.entry:
        chosen = [f for f in found if f[2] == spec.entry]
        if not chosen:
            names = ", ".join(repr(n) for _i, _g, n in found)
            raise NewMapError(f"maps/{new}: {src} has no BATTLES entry {spec.entry!r} (its entries: {names})")
        found = chosen
    elif len(found) > 1:
        names = ", ".join(repr(n) for _i, _g, n in found)
        raise NewMapError(f"maps/{new}: {src} has several BATTLES entries ({names}); say which one to copy in "
                          f"map.toml (entry = \"...\")")
    mi, gi, list_name = found[0]
    load = _props(m, m.objects[mi])
    folder = _text(m, load.get("Path")) or _text(m, load.get("RootDatapackName"))
    out = Clone(new, folder)
    out.pack_id = guid_for(new, "pack")
    guid = guid_for(new, "entry")
    used = {bytes(v.payload) for nd in (m, g) for o in nd.objects for pi, v in o.props
            if nd.prop_name(pi) in ("GUID", "PackGUID") and v.tc == 0x1A}
    if guid in used:
        raise NewMapError(f"maps/{new}: the new map's id is already taken; give it another folder name")

    def must(member: str, what: str, pack: Files) -> bytes:
        raw = pack.read(member)
        if raw is None:
            raise NewMapError(f"maps/{new}: {src}'s {what} ({member}) is missing, so it can't be copied")
        return raw

    def adding(pack: dict, files: Files, member: str, raw: bytes) -> None:
        if files.read(member) is not None:
            raise NewMapError(f"maps/{new}: the game already has {member}; give the new map another folder name")
        pack[member] = raw

    # 1. the scenario's cluster: what the entry loads
    base = None
    for v in sub_values(load["ClusterLoads"])[1::2] if "ClusterLoads" in load else []:
        c = local_ref(v)
        tr = local_ref(_props(m, m.objects[c])["NdfTransaction"]) if c is not None else None
        base = _text(m, _props(m, m.objects[tr]).get("BaseName")) if tr is not None else None
        if base:
            break
    if not base:
        raise NewMapError(f"maps/{new}: {list_name!r} names no scenario cluster, so it can't be copied")
    fold = re.compile(r"^(Patchable[\\/]Scenario[\\/])" + re.escape(folder) + r"([\\/][^\\/]+[\\/]ClusterMap)$", re.I)
    if not fold.match(base):
        raise NewMapError(f"maps/{new}: {list_name!r} loads {base}, which isn't laid out like a map's scenario; it "
                          f"can't be copied yet")
    new_base = fold.sub(lambda q: q.group(1) + new + q.group(2), base)
    cluster = Ndf(must(_member(base), "scenario cluster", glad))
    scen_pat = _under(folder)
    map_cluster = mapia = None
    scenario = None
    for s in cluster.strings:
        if scen_pat.match(s) and s.lower().endswith(".scenario"):
            scenario = s.replace("/", BS).rsplit(BS, 1)[-1].lower()
        q = re.match(r"^Patchable[\\/]map[\\/]" + re.escape(folder) + r"[\\/]ClusterMap$", s, re.I)
        if q:
            map_cluster = s
        q = re.match(r"^Patchable[\\/]Scenario[\\/]" + re.escape(folder) + r"[\\/][^\\/]+[\\/]MapIA$", s, re.I)
        if q:
            mapia = s
    if scenario is None or map_cluster is None:
        raise NewMapError(f"maps/{new}: {src}'s scenario cluster doesn't name its scenario and map the way the "
                          f"game's maps do, so it can't be copied")
    out.scenario = scenario
    src_dir, new_dir = "test" + BS + "map" + BS + folder.lower() + BS, "test" + BS + "map" + BS + low + BS
    adding(out.data, data, new_dir + scenario, must(src_dir + scenario, "scenario", data))

    def into_new(s: str, pattern) -> str | None:
        q = pattern.match(s)
        return q.group(1) + new + q.group(2) if q else None
    map_pat = re.compile(r"^(Patchable[\\/]map[\\/]|map[\\/])" + re.escape(folder) + r"([\\/]ClusterMap(\.ndfbin)?)$",
                         re.I)
    ia_pat = re.compile(r"^(Patchable[\\/]Scenario[\\/]|Scenario[\\/])" + re.escape(folder)
                        + r"([\\/][^\\/]+[\\/]MapIA(\.ndfbin)?)$", re.I)
    clu_pat = re.compile(r"^(Patchable[\\/]Scenario[\\/]|map[\\/])" + re.escape(folder)
                         + r"([\\/][^\\/]+[\\/]ClusterMap(\.ndfbin)?)$", re.I)

    # 2. the scenario's MapIA: its camera paths and bluff zones, copied with it
    if mapia is not None:
        ia = Ndf(must(_member(mapia), "scenario's MapIA", glad))
        copied = {}

        def ia_swap(s: str) -> str | None:
            q = scen_pat.match(s)
            if not q:
                return None
            rel = q.group(2).replace("/", BS).lstrip(BS).lower()
            raw = data.read(src_dir + rel)
            if raw is None:
                return None  # not shipped: left pointing at the shipped map's
            copied[new_dir + rel] = raw
            return q.group(1) + new + q.group(2)
        _swap_strings(ia, ia_swap)
        for member, raw in sorted(copied.items()):
            adding(out.data, data, member, raw)
        adding(out.glad, glad, _member(into_new(mapia, ia_pat)), ia.to_member(compress=bool(ia.flags & 0x80)))
    n = _swap_strings(cluster, lambda s: (into_new(s, scen_pat) if s.lower().endswith(".scenario") else None)
                      or into_new(s, map_pat) or (into_new(s, ia_pat) if mapia else None))
    if n < 2:
        raise NewMapError(f"maps/{new}: {src}'s scenario cluster couldn't be pointed at the new map")
    adding(out.glad, glad, _member(new_base), cluster.to_member(compress=bool(cluster.flags & 0x80)))

    # 3. the map's cluster: it mounts the new pack and names the new data folder
    mc = Ndf(must(_member(map_cluster), "map cluster", glad))
    mounts = [(_props(mc, o), o) for o in mc.objects if mc.classes[o.cls] == "TClusterMountMapDataPack"]
    if len(mounts) != 1:
        raise NewMapError(f"maps/{new}: {src}'s map cluster doesn't mount one pack, so it can't be copied")
    mp, mo = mounts[0]
    pack_txt, datas_txt = _text(mc, mp.get("DataPack")), _text(mc, mp.get("DatasMapDirectory"))
    if not pack_txt or not datas_txt or not re.match(r"^MapDat:[\\/]DataMap.+_v09\.dat$", pack_txt, re.I):
        raise NewMapError(f"maps/{new}: {src}'s map cluster doesn't name its pack the way the game's maps do")
    datas_dir = re.split(r"[\\/]", datas_txt)[-1]
    _set(mc, mo, "DataPack", Value(mp["DataPack"].tc, struct.pack("<I", _string(mc, f"MapDat:{BS}DataMap{new}_v09.dat"))))
    _set(mc, mo, "DatasMapDirectory", Value(mp["DatasMapDirectory"].tc,
                                            struct.pack("<I", _string(mc, datas_txt[:-len(datas_dir)] + new))))
    adding(out.glad, glad, _member(into_new(map_cluster, map_pat)), mc.to_member(compress=bool(mc.flags & 0x80)))
    win = "datasmap" + BS + datas_dir.lower() + BS + "mapinfo.win"
    adding(out.data, data, "datasmap" + BS + low + BS + "mapinfo.win", must(win, "grid (mapinfo.win)", data))
    gen = "gen" + BS + "datasmap" + BS + datas_dir.lower() + BS
    for member in zz.names(gen):
        adding(out.zz, zz, "gen" + BS + "datasmap" + BS + low + BS + member[len(gen):].lower(), zz.read(member))

    # 4. the map list: a new entry, a top object like every other
    pictures = {}

    def entry_text(s: str) -> str:
        q = scen_pat.match(s)
        if q and s.lower().endswith(".png"):
            picture = "gen" + BS + (_datadir(s) or "")[:-len(".png")] + ".tgv"
            raw = zz.read(picture)
            if raw is None:
                return s  # no picture shipped there: the copy shows the shipped map's
            pictures["gen" + BS + new_dir + picture[len("gen" + BS + src_dir):]] = raw
            return q.group(1) + new + q.group(2)
        return into_new(s, clu_pat) or into_new(s, scen_pat) or s
    j = _copy(m, mi, {}, entry_text)
    for member, raw in sorted(pictures.items()):
        adding(out.zz, zz, member, raw)
    o = m.objects[j]
    names = {_text(m, _props(m, x).get("Name")) for x in m.objects if m.classes[x.cls] == "TMapLoadInfo"}
    out.entry_name = _list_name(list_name, spec.names["us"], new, names)
    for prop, text in (("Name", out.entry_name), ("Path", new), ("RootDatapackName", new)):
        if prop in load:
            _set(m, o, prop, Value(load[prop].tc, struct.pack("<I", _string(m, text))))
    _set(m, o, "GUID", Value(0x1A, guid))
    m.set_topo(list(m.topo) + [j])

    # 5. BATTLES: its own entry, in the menu pack that lists the shipped map, after the maps of its size
    gs = _props(g, g.objects[gi])
    out.key = _free_key(zz)
    tracks = {(_text(g, _props(g, x).get("TrackingId")) or "") for x in g.objects}
    n = TRACK_FIRST
    while f"{TRACK_STEM}{n:02d}" in tracks:
        n += 1
    k = g.add_object(g.objects[gi].cls, [(pi, v) for pi, v in g.objects[gi].props if g.prop_name(pi) not in DROPPED])
    _set(g, g.objects[k], "GUID", Value(0x1A, guid))
    _set(g, g.objects[k], "Description", Value(0x1D, struct.pack("<Q", name_to_key(out.key))))
    if "TrackingId" in gs:
        _set(g, g.objects[k], "TrackingId", Value(gs["TrackingId"].tc,
                                                  struct.pack("<I", _string(g, f"{TRACK_STEM}{n:02d}"))))
    left = _props(g, g.objects[k])
    if not any(p.startswith("DispoMulti") and v.tc in (0x00, 0x02) and v.scalar() for p, v in left.items()):
        raise NewMapError(f"maps/{new}: {list_name!r} is only offered in ranked games, which a copy can't join; "
                          f"pick another entry")
    if any(p in gs for p in LADDER):
        out.notes.append(f"{new} isn't offered in ranked games (the shipped map's ladder place stays its own)")
    _place(g, gi, k)

    # 6. its name in the menus, in every language
    for lang in loc.LANGS + ("dev",):
        member = loc.member(MENU_TEXTS, lang)
        raw = zz.read(member)
        if raw is None:
            continue
        dic = Dic(raw)
        dic.add(name_to_key(out.key), spec.names["us"] if lang == "dev" else spec.names.get(lang, spec.names["us"]))
        out.texts[member] = dic.to_bytes()
    if not out.texts:
        raise NewMapError(f"maps/{new}: the menus' texts ({MENU_TEXTS}.dic) aren't in ZZ_Win.dat, so the new map "
                          f"would have no name")
    out.glad[MAPINFO] = m.to_member(compress=bool(m.flags & 0x80))
    out.glad[GLOBALS] = g.to_member(compress=bool(g.flags & 0x80))
    out.notes.insert(0, f"{new}: a copy of {list_name!r} ({src}), listed in BATTLES as {out.entry_name!r}, its "
                        f"name {out.key} in {len(out.texts)} dictionaries; {len(out.glad) - 2 + len(out.data) + len(out.zz)} "
                        f"file(s) copied under its name, and its own pack")
    return out


def _list_name(source_name: str, display: str, new: str, taken: set) -> str:
    """The new map-list name: the shipped entry's player count and teams around the new map's name
    ("(6) Cotentin (3v3)" -> "(6) Omaha Ridge (3v3)"), with the folder name if the menus' name can't be written
    there (the map list is Latin-1) or another entry has it."""
    head = re.match(r"^\(\d+\)\s*", source_name)
    tail = re.search(r"\s*\((?:FFA|\d+(?:vs?\d+)+)\)$", source_name)
    for middle in (display, new):
        try:
            middle.encode("latin-1")
        except UnicodeEncodeError:
            continue
        name = (head.group(0) if head else "") + middle + (tail.group(0) if tail else "")
        if name not in taken:
            return name
    raise NewMapError(f"maps/{new}: the map list already has an entry called like the new map; give it another name")


def _free_key(zz: Files) -> str:
    """The first map-name key (M_D_31, M_D_32, ...) no language's menu dictionary uses yet."""
    used = set()
    for lang in loc.LANGS + ("dev",):
        raw = zz.read(loc.member(MENU_TEXTS, lang))
        if raw is not None:
            used |= {e.key for e in Dic(raw).entries}
    n = KEY_FIRST
    while name_to_key(f"{KEY_STEM}{n:02d}") in used:
        n += 1
    return f"{KEY_STEM}{n:02d}"


def _place(g: Ndf, source: int, new: int) -> None:
    """Put menu entry `new` in the menu pack listing `source`, after the last entry of its size group (CategoryId):
    the menus show a pack's maps in runs of one size."""
    cat = lambda i: (_props(g, g.objects[i]).get("CategoryId").scalar()  # noqa: E731
                     if "CategoryId" in _props(g, g.objects[i]) else None)
    for o in g.objects:
        for k, (pi, v) in enumerate(o.props):
            if v.tc != 0x11:
                continue
            items = sub_values(v)
            refs = [local_ref(x) for x in items]
            if source not in refs:
                continue
            at = max(n for n, r in enumerate(refs) if r is not None and cat(r) == cat(new)) + 1
            ref = Value(0x09, struct.pack("<III", 0xBBBBBBBB, new, g.objects[new].cls))
            items.insert(at, ref)
            o.props[k] = (pi, Value(0x11, struct.pack("<I", len(items)) + b"".join(x.encode() for x in items)))
            return
    raise NewMapError("the shipped map's BATTLES entry isn't in a menu pack, so the new map can't be listed")
