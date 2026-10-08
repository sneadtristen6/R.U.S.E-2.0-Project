"""New maps: a shipped map copied under a name of its own, listed in BATTLES beside it, or, when map.toml's `entry`
names one, as a new Operation (last in OPERATIONS) or a new campaign chapter (last in the campaign) running the
shipped one's mission script.

A mod makes one with `maps/<NewName>/map.toml` (MOD_FORMAT §8):

    copy_of = "SuperCrossRoads4"   # the shipped map it starts from, by its pack name (this one is Blitz)
    name = "Blitz at Dusk"         # what the menus call it; or a table, [name] us = "...", fr = "...", ...
    entry = "(2) Blitz"            # optional: which of the shipped map's BATTLES entries, when it has several
    players = 4                    # optional: as on any map (rusemod.players), for the copy

The folder's name is the new map's pack name, and the mod's other files in that folder edit the copy like any map,
while the shipped map stays as it was. The build adds the copy's own map, its place in the map list and in BATTLES,
its scenario, cover and movement, and its name in the ten languages: each a copy of the shipped map's, pointed at the
copy. Everything else stays the shipped map's, only read.

Nothing is random: the ids come from the new map's name, so every PC builds the same files (a multiplayer game needs
both sides to have the same map list)."""
from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass, field

from . import loc
from .dic import Dic, name_to_key
from .edat import Entry
from .ndf import Ndf, Value, local_ref, sub_values
from .players import GLOBALS, MAPINFO

BS = "\\"
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
NAME_LONGEST = 60          # characters of a map's name in the menus
MENU_TEXTS = "flash_txt"   # the menus' dictionary: the shipped maps' names are M_D_01 .. M_D_30 there
KEY_STEM, KEY_FIRST = "M_D_", 31
TRACK_STEM, TRACK_FIRST = "MP", 31    # the shipped BATTLES maps are MP01 .. MP30
LADDER = ("DispoLadder1v1", "DispoLadder2v2")   # ranked matchmaking: the shipped map's place, not a copy's
DROPPED = LADDER + ("RewardId",)
# The three menus a map-list entry can be in (globals.cpp), and what each calls its entries: BATTLES' multiplayer and
# skirmish maps (TMultiMapInfo, in a TMultiPack's MultiList), the Operations (TChallengeMapInfo, a TChallengePack's
# ChallengeList) and the campaign's chapters (TChapterMapInfo, a TChapterPack's ChapterList). The game fills all three
# the same way: an entry shows when its GUID is a loaded map-list entry's.
KINDS = {"TMultiMapInfo": "battles", "TChallengeMapInfo": "operation", "TChapterMapInfo": "campaign"}
MENU_NAMES = {"battles": "BATTLES", "operation": "OPERATIONS", "campaign": "the CAMPAIGN"}
TRACKS = {"battles": (TRACK_STEM, TRACK_FIRST), "operation": ("CH", 40), "campaign": ("M", 24)}  # shipped: CH26-39, M01-23


class NewMapError(ValueError):
    """A new map that can't be made, said for the modder: what to change."""


GROUNDS = ("kept", "generated")   # a new map's ground: the copied map's moved, or drawn as our own (map.toml ground)


@dataclass
class NewMap:
    copy_of: str                  # the shipped map's pack name
    names: dict                   # language folder (loc.LANGS) -> the map's name in the menus; "us" always there
    entry: str | None = None      # which of the shipped map's BATTLES entries, by its map-list name
    picture: str | None = None    # its own big picture in the menus: a PNG in its folder (rusemod.menupicture)
    wide_picture: str | None = None  # its own wide one (the 3D map), a PNG there too; else made from `picture`
    start_dots: bool = False      # the build draws its starting points on the wide one (menupicture.start_dots_of)
    ground: str = "kept"          # "generated": its ground drawn as our own from its strokes (rusemod.groundgen),
                                  # not the copied map's moved; "kept": the copied map's, moved by the strokes
    picture_data: bytes | None = field(default=None, compare=False, repr=False)  # that PNG's bytes, read with the mod
    wide_picture_data: bytes | None = field(default=None, compare=False, repr=False)


# --- map.toml -------------------------------------------------------------------------------------------------------
def parse(data: dict, where: str = "map.toml", folder: str = "") -> list[NewMap]:
    """A map.toml's new-map settings: [NewMap] when it says copy_of, else [] (and `name` alone is a mistake)."""
    if "copy_of" not in data:
        if "name" in data:
            raise NewMapError(f"{where}: name is for a new map; add copy_of = \"<the shipped map's pack name>\" (a "
                              f"shipped map's name in the menus can't change here)")
        if "ground" in data:
            raise NewMapError(f"{where}: ground is for a new map (copy_of = \"<the shipped map's pack name>\"): a "
                              f"shipped map keeps its own ground, moved by its strokes")
        return []
    src = data["copy_of"]
    if not isinstance(src, str) or not re.match(r"^[A-Za-z0-9_]+$", src):
        raise NewMapError(f"{where}: copy_of must be a shipped map's pack name, like \"SuperCrossRoads4\" (Blitz) or "
                          f"\"M04_Cotentin\" (D-Day)")
    if folder and src.lower() == folder.lower():
        raise NewMapError(f"{where}: a map can't be a copy of itself; give the new map's folder a name of its own")
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
    from .menupicture import PictureError, picture_names, start_dots_of
    try:
        picture, wide = picture_names(data, where)
        dots = start_dots_of(data, where, wide)
    except PictureError as exc:
        raise NewMapError(str(exc)) from None
    ground = data.get("ground", "kept")
    if ground not in GROUNDS:
        raise NewMapError(f"{where}: ground must be one of {', '.join(repr(g) for g in GROUNDS)} ('generated': the "
                          f"map's ground drawn as our own from its strokes, starting from a map flattened all over)")
    return [NewMap(src, names, entry, picture, wide, dots, ground)]


def map_toml(spec: NewMap, players: int | None = None, header: str = "") -> str:
    """A new map's map.toml (the Studio writes it)."""
    lines = [f"# {ln}" for ln in header.splitlines()] + ([""] if header else [])
    lines.append(f'copy_of = "{spec.copy_of}"')
    if spec.entry:
        lines.append(f'entry = "{_toml_text(spec.entry)}"')
    if players is not None:
        lines.append(f"players = {players}")
    if spec.picture:
        lines.append(f'picture = "{_toml_text(spec.picture)}"')
    if spec.wide_picture:
        lines.append(f'wide_picture = "{_toml_text(spec.wide_picture)}"')
    if spec.start_dots:
        lines.append("start_dots = true")
    if spec.ground != "kept":
        lines.append(f'ground = "{spec.ground}"')
    if set(spec.names) == {"us"}:
        lines.append(f'name = "{_toml_text(spec.names["us"])}"')
    else:
        lines += ["", "[name]"] + [f'{lang} = "{_toml_text(spec.names[lang])}"' for lang in loc.LANGS
                                   if lang in spec.names]
    return "\n".join(lines) + "\n"


def _toml_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def check_name(new: str) -> None:
    """Refuse a new map's folder name the game's files can't carry."""
    if not NAME.match(new):
        raise NewMapError(f"maps/{new}: a new map's folder name is its pack name: a letter, then up to 39 letters, "
                          f"digits and _ (like BlitzAtDusk)")
    if new.lower().startswith("flat_"):
        # rule: newmap-names
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
    new: str                                        # the new map's pack name
    source: str                                     # the shipped map it copies (copy_of)
    map_folder: str = ""                            # the shipped map's folder in genglad\patchable\map\
    pack_from: str = ""                             # the shipped map pack copied, e.g. DataMapSuperCrossroads4_v09.dat
    pack_id: bytes = b""                            # the new pack's id (its header)
    glad: dict = field(default_factory=dict)        # ZZ_GladPatchableWin.dat: new members
    glad_changed: dict = field(default_factory=dict)  # ZZ_GladPatchableWin.dat: the map list and menus, changed
    data: dict = field(default_factory=dict)        # DataMap_Win.dat: new members
    texts: dict = field(default_factory=dict)       # ZZ_Win.dat: the menus' dictionaries, changed
    zz_new: dict = field(default_factory=dict)      # ZZ_Win.dat: new members (its own menu pictures)
    scenario: str = ""                              # the scenario file (lower case) the new entry loads
    kind: str = "battles"                           # the menu it's in: battles, operation or campaign (KINDS)
    key: str = ""                                   # the name's text key, e.g. M_D_31
    entry_name: str = ""                            # the new map-list name, e.g. "(2) Blitz at Dusk"
    guid: bytes = b""                               # ties the map-list entry to its BATTLES entry
    notes: list = field(default_factory=list)


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


def _set_text(nd: Ndf, o, name: str, text: str) -> None:
    """Property `name` of `o` (a string or path, as it is) set to `text`, a string of its own: others sharing the old
    one keep it."""
    old = _props(nd, o)[name]
    _set(nd, o, name, Value(old.tc, struct.pack("<I", _string(nd, text))))


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


def _renamer(*patterns):
    """swap(s) for _swap_strings: each pattern's group 2 (a folder name) becomes `new`, the rest kept as written."""
    def into(new: str):
        def swap(s: str) -> str | None:
            for p in patterns:
                q = p.match(s)
                if q:
                    return q.group(1) + new + q.group(3)
            return None
        return swap
    return into


def _member(nd_path: str) -> str:
    """'Patchable\\Scenario\\X\\Y\\ClusterMap' -> the compiled file in ZZ_GladPatchableWin.dat."""
    return "genglad" + BS + nd_path.replace("/", BS).lower() + ".cpp.gladndfbin"


def _listed(g: Ndf, gi: int) -> bool:
    """Whether menu entry `gi` is in a menu pack's list (what BATTLES shows)."""
    return any(v.tc == 0x11 and any(local_ref(x) == gi for x in sub_values(v)) for o in g.objects for _pi, v in o.props)


def menu_entries(m: Ndf, g: Ndf, pack: str) -> list[tuple[int, int, str, str]]:
    """Every menu entry of map `pack` a player can pick: [(its TMapLoadInfo, its menu entry, its map-list name, its
    kind: battles, operation or campaign)], in the map list's order. Entries no menu pack lists, and the tutorial's
    (a chapter pack with IsTuto), are left out."""
    tuto = set()
    for o in g.objects:
        p = _props(g, o)
        if "IsTuto" in p and p["IsTuto"].scalar():
            tuto |= {local_ref(x) for v in p.values() if v.tc == 0x11 for x in sub_values(v)}
    by_guid = {}
    for i, o in enumerate(g.objects):
        kind = KINDS.get(g.classes[o.cls])
        p = _props(g, o) if kind else {}
        if kind and "GUID" in p and i not in tuto:
            by_guid.setdefault(bytes(p["GUID"].payload), (i, kind))
    out = []
    for i, o in enumerate(m.objects):
        if m.classes[o.cls] != "TMapLoadInfo":
            continue
        p = _props(m, o)
        root = next((_text(m, p[k]) for k in ("RootDatapackName", "Path") if k in p), None)
        if not root or root.lower() != pack.lower() or "GUID" not in p:
            continue
        found = by_guid.get(bytes(p["GUID"].payload))
        if found is not None and _listed(g, found[0]):
            out.append((i, found[0], _text(m, p["Name"]) if "Name" in p else "", found[1]))
    return out


def picture_members(m: Ndf, obj: int) -> dict:
    """{picture stem ("Minimap", "Minimap2"): ZZ_Win.dat member} of map-list entry `obj`'s pictures in the menus
    (rusemod.menupicture.member_of)."""
    from .menupicture import SIZES, member_of
    p, out = _props(m, m.objects[obj]), {}
    for prop, stem, _w, _h in SIZES:
        t = local_ref(p[prop]) if prop in p else None
        name = _text(m, _props(m, m.objects[t]).get("FileName")) if t is not None else None
        member = member_of(name) if name else None
        if member is not None:
            out[stem] = member
    return out


def shipped_pictures(m: Ndf, g: Ndf, pack: str, spec, has_member) -> tuple[dict, list[str], str | None, int]:
    """A shipped map's own pictures in the menus (map.toml picture / wide_picture with no copy_of:
    rusemod.menupicture.MenuPictures `spec`): ({ZZ_Win.dat member: its new picture file}, notes, the member of its
    wide picture (or None), the first entry's TMapLoadInfo) for the pictures its BATTLES entries show, or the entry
    spec.entry names. A file another of the map's entries shows too changes there as well (a note says which). `m`,
    `g`: the map list and the menus (players.MAPINFO, GLOBALS); `has_member`: whether ZZ_Win.dat has a member."""
    from .menupicture import SIZES, PictureError, member_of, pictures
    entries = menu_entries(m, g, pack)
    chosen = [e for e in entries if (e[2] == spec.entry if spec.entry else e[3] == "battles")]
    if not chosen:
        raise NewMapError(f"maps/{pack}: {pack} has no entry {spec.entry!r}" if spec.entry else
                          f"maps/{pack}: {pack} isn't in BATTLES: say which entry's pictures change (entry = ...)")
    try:
        made = pictures(spec.picture_data, spec.wide_picture_data)
    except PictureError as exc:
        raise NewMapError(f"maps/{pack}: {spec.picture or spec.wide_picture}: {exc}") from None
    changes, notes, wide = {}, [], None
    for obj, _menu, name, _kind in chosen:
        for stem, member in picture_members(m, obj).items():
            if stem not in made:
                continue
            if not has_member(member):
                notes.append(f"{pack}: {name}'s picture {member} isn't in ZZ_Win.dat, so it stays")
                continue
            changes[member] = made[stem]
            if stem == SIZES[1][1]:
                wide = wide or member
    picked = {e[0] for e in chosen}
    for obj, _menu, name, kind in entries:
        shared = sorted({mb.rsplit("\\", 1)[-1] for mb in picture_members(m, obj).values() if mb in changes}) \
            if obj not in picked else []
        if shared:
            notes.append(f"{pack}: {name} ({kind}) shows {', '.join(shared)} too, so it changes there as well")
    return changes, notes, wide, chosen[0][0]


def _cluster_base(m: Ndf, load: dict) -> str | None:
    """The scenario cluster a map-list entry loads (its NDF transaction's BaseName)."""
    for v in sub_values(load["ClusterLoads"])[1::2] if "ClusterLoads" in load else []:
        c = local_ref(v)
        cp = _props(m, m.objects[c]) if c is not None else {}
        tr = local_ref(cp["NdfTransaction"]) if "NdfTransaction" in cp else None
        base = _text(m, _props(m, m.objects[tr]).get("BaseName")) if tr is not None else None
        if base:
            return base
    return None


def entry_scenario(m: Ndf, mi: int, read_glad) -> str | None:
    """The scenario file map-list entry `mi` plays, as its cluster names it, in lower case (D-Day's BATTLES map:
    leveldesign_3v3_v01.scenario), the one a copy of it plays; None when its cluster names none or several."""
    base = _cluster_base(m, _props(m, m.objects[mi]))
    raw = read_glad(_member(base)) if base else None
    if raw is None:
        return None
    scen_at = re.compile(r"^DataDir:[\\/]+Test[\\/]+Map[\\/]+[^\\/]+[\\/]+(.+\.scenario)$", re.I)
    # (Bir Hakeim's cluster names its file as Alpha//LevelDesign_BH.scenario and Alpha\LevelDesign_BH.scenario: one)
    found = {re.sub(r"[\\/]+", "/", scen_at.match(s).group(1)).replace("/", BS).lower()
             for s in Ndf(raw).strings if scen_at.match(s)}
    return found.pop() if len(found) == 1 else None


def make(new: str, spec: NewMap, read_glad, read_data, read_zz) -> Clone:
    """The files that add the new map `new`, a copy of `spec.copy_of`. `read_glad`, `read_data` and `read_zz` give a
    member of ZZ_GladPatchableWin.dat, DataMap_Win.dat and ZZ_Win.dat as the build has it so far (any case), or None.
    Raises NewMapError with what to change."""
    from .terrain import pack_file
    check_name(new)
    src = spec.copy_of
    g_raw, m_raw = read_glad(GLOBALS), read_glad(MAPINFO)
    if g_raw is None or m_raw is None:
        # not a game rule: the game or one of its files isn't found
        raise NewMapError("the game's map list or menus aren't in ZZ_GladPatchableWin.dat, so no map can be added")
    g, m = Ndf(g_raw), Ndf(m_raw)
    roots = {(_text(m, _props(m, o).get(k)) or "").lower() for o in m.objects if m.classes[o.cls] == "TMapLoadInfo"
             for k in ("RootDatapackName", "Path")}
    if new.lower() in roots:
        # rule: newmap-names
        raise NewMapError(f"maps/{new}: the game already has a map called {new}; give the new map another folder "
                          f"name")
    every = menu_entries(m, g, src)  # BATTLES maps, Operations, campaign chapters
    if not every:
        if src.lower() in roots:
            # not a game rule: our map copier needs the game's own map files as they are
            raise NewMapError(f"maps/{new}: no menu offers {src} (BATTLES, OPERATIONS or the CAMPAIGN), so there's no "
                              f"entry to copy; start from a map one of them lists")
        # not a game rule: the game or one of its files isn't found
        raise NewMapError(f"maps/{new}: copy_of = {src!r} isn't a map of this game (it takes the map's pack name, like "
                          f"SuperCrossRoads4 for Blitz)")
    found = [f for f in every if f[3] == "battles"]
    if spec.entry:
        chosen = [f for f in every if f[2] == spec.entry]
        if not chosen:
            names = ", ".join(repr(f[2]) for f in every)
            raise NewMapError(f"maps/{new}: {src} has no entry {spec.entry!r} (its entries: {names})")
        found = chosen
    elif len(found) > 1:
        names = ", ".join(repr(f[2]) for f in found)
        raise NewMapError(f"maps/{new}: {src} has several BATTLES entries ({names}); say which one to copy in "
                          f"map.toml (entry = \"...\")")
    elif not found:
        names = ", ".join(repr(f[2]) for f in every)
        raise NewMapError(f"maps/{new}: {src} isn't in BATTLES; to copy one of its Operations or campaign chapters, "
                          f"name it in map.toml (entry = \"...\"): {names}")
    mi, gi, list_name, kind = found[0]
    load = _props(m, m.objects[mi])
    out = Clone(new, src, pack_id=guid_for(new, "pack"), guid=guid_for(new, "entry"), kind=kind)
    used = {bytes(v.payload) for nd in (m, g) for o in nd.objects for pi, v in o.props
            if nd.prop_name(pi) == "GUID" and v.tc == 0x1A}
    if out.guid in used:
        raise NewMapError(f"maps/{new}: the new map's id is already taken; give it another folder name")
    low = new.lower()

    def must(read, member: str, what: str) -> bytes:
        raw = read(member)
        if raw is None:
            raise NewMapError(f"maps/{new}: {src}'s {what} ({member}) is missing, so it can't be copied")
        return raw

    def adding(pack: dict, read, member: str, raw: bytes) -> None:
        if read(member) is not None:
            # rule: newmap-names
            raise NewMapError(f"maps/{new}: the game already has {member}; give the new map another folder name")
        pack[member] = raw

    # 1. the scenario's cluster: it names the scenario and the map's cluster
    base = _cluster_base(m, load)
    q = re.match(r"^Patchable[\\/]Scenario[\\/]([^\\/]+)[\\/]([^\\/]+)[\\/]ClusterMap$", base or "", re.I)
    if not q:
        raise NewMapError(f"maps/{new}: {list_name!r} loads {base or 'no scenario cluster'}, which isn't laid out like "
                          f"a map's scenario; it can't be copied yet")
    folder, sub = q.group(1), q.group(2)
    cluster = Ndf(must(read_glad, _member(base), "scenario cluster"))
    scen_at = re.compile(r"^(DataDir:[\\/]Test[\\/]Map[\\/])([^\\/]+)([\\/].+\.scenario)$", re.I)
    map_at = re.compile(r"^Patchable[\\/]map[\\/]([^\\/]+)[\\/]ClusterMap$", re.I)
    scen = {(scen_at.match(s).group(2).lower(), scen_at.match(s).group(3)[1:].replace("/", BS).lower())
            for s in cluster.strings if scen_at.match(s)}
    maps = {map_at.match(s).group(1).lower(): map_at.match(s).group(1) for s in cluster.strings if map_at.match(s)}
    if len(scen) != 1 or len(maps) != 1:
        # not a game rule: our map copier needs the game's own map files as they are
        raise NewMapError(f"maps/{new}: {src}'s scenario cluster doesn't name one scenario and one map the way the "
                          f"game's maps do, so it can't be copied")
    (scen_folder, out.scenario), = scen
    out.map_folder = next(iter(maps.values()))
    mf = re.escape(out.map_folder)
    scen_dir = "test" + BS + "map" + BS
    # the scenario's MapIA names its zone map (which sector a place is in: rusemod.sectors), and the copy gets its own
    # of both, so its sectors can be made again without touching the shipped map's (Blank Ocean, 2026-10-05: the
    # copy read the shipped zone map, and its sectors over the whole map were left out)
    ia_base = "Patchable" + BS + "Scenario" + BS + folder + BS + sub + BS + "MapIA"
    ia_raw, ia_copy = read_glad(_member(ia_base)), None
    if ia_raw is not None:
        ia = Ndf(ia_raw)
        zone_at = re.compile(r"^(DataDir:[\\/]Test[\\/]Map[\\/])(" + re.escape(scen_folder)
                             + r")([\\/]ZoneBluff[\\/][^\\/]+\.kdt)$", re.I)
        zones = [zone_at.match(s).group(3)[1:].replace("/", BS).lower() for s in ia.strings if zone_at.match(s)]
        zone_raw = read_data(scen_dir + scen_folder + BS + zones[0]) if len(zones) == 1 else None
        if zone_raw is not None and _swap_strings(ia, _renamer(zone_at)(new)) >= 1:  # (D-Day's names it twice: a
            ia_copy = (ia, zones[0], zone_raw)                                        # string and a wide string)
    patterns = [
        re.compile(r"^(DataDir:[\\/]Test[\\/]Map[\\/])(" + re.escape(scen_folder) + r")([\\/].+\.scenario)$", re.I),
        re.compile(r"^(Patchable[\\/]map[\\/])(" + mf + r")([\\/]ClusterMap)$", re.I),
        re.compile(r"^(map[\\/])(" + mf + r")([\\/]ClusterMap\.ndfbin)$", re.I)]
    if ia_copy is not None:
        patterns += [
            re.compile(r"^(Patchable[\\/]Scenario[\\/])(" + re.escape(folder) + r")([\\/]" + re.escape(sub)
                       + r"[\\/]MapIA)$", re.I),
            re.compile(r"^(Scenario[\\/])(" + re.escape(folder) + r")([\\/]" + re.escape(sub) + r"[\\/]MapIA\.ndfbin)$",
                       re.I)]
    n = _swap_strings(cluster, _renamer(*patterns)(new))
    if n < 2:
        raise NewMapError(f"maps/{new}: {src}'s scenario cluster couldn't be pointed at the new map")
    new_base = "Patchable" + BS + "Scenario" + BS + new + BS + sub + BS + "ClusterMap"
    adding(out.glad, read_glad, _member(new_base), cluster.to_member(compress=bool(cluster.flags & 0x80)))
    adding(out.data, read_data, scen_dir + low + BS + out.scenario,
           must(read_data, scen_dir + scen_folder + BS + out.scenario, "scenario"))
    if ia_copy is not None:
        ia, zone_file, zone_raw = ia_copy
        adding(out.glad, read_glad, _member("Patchable" + BS + "Scenario" + BS + new + BS + sub + BS + "MapIA"),
               ia.to_member(compress=bool(ia.flags & 0x80)))
        adding(out.data, read_data, scen_dir + low + BS + zone_file, zone_raw)

    # 2. the map's cluster: it mounts the new pack, and loads the new constants
    map_member = _member("Patchable" + BS + "map" + BS + out.map_folder + BS + "ClusterMap")
    mc = Ndf(must(read_glad, map_member, "map cluster"))
    mounts = [o for o in mc.objects if mc.classes[o.cls] == "TClusterMountMapDataPack"]
    pack_txt = _text(mc, _props(mc, mounts[0]).get("DataPack")) if len(mounts) == 1 else None
    q = re.match(r"^MapDat:[\\/](DataMap[A-Za-z0-9_]+_v09\.dat)$", pack_txt or "", re.I)
    if not q:
        # not a game rule: our map copier needs the game's own map files as they are
        raise NewMapError(f"maps/{new}: {src}'s map cluster doesn't mount one map pack the way the game's maps do, "
                          f"so it can't be copied")
    out.pack_from = q.group(1)
    _set_text(mc, mounts[0], "DataPack", f"MapDat:{BS}DataMap{new}_v09.dat")
    n = _swap_strings(mc, _renamer(
        re.compile(r"^(Patchable[\\/]map[\\/])(" + mf + r")([\\/]MapConstante)$", re.I),
        re.compile(r"^(map[\\/])(" + mf + r")([\\/]MapConstante\.ndfbin)$", re.I))(new))
    if n < 1:
        # not a game rule: our map copier needs the game's own map files as they are
        raise NewMapError(f"maps/{new}: {src}'s map cluster doesn't load its constants the way the game's maps do, "
                          f"so it can't be copied")
    adding(out.glad, read_glad, _member("Patchable" + BS + "map" + BS + new + BS + "ClusterMap"),
           mc.to_member(compress=bool(mc.flags & 0x80)))

    # 3. the map's constants: the folder of its grid (mapinfo.win) is the new map's
    mk = Ndf(must(read_glad, _member("Patchable" + BS + "map" + BS + out.map_folder + BS + "MapConstante"),
                  "constants (MapConstante)"))
    infos = [o for o in mk.objects if mk.classes[o.cls] == "TCurrentMapInfo"]
    grid = _text(mk, _props(mk, infos[0]).get("MapPath")) if len(infos) == 1 else None
    q = re.match(r"^DataDir:[\\/]datasmap[\\/]([^\\/]+)$", grid or "", re.I)
    if not q:
        # not a game rule: our map copier needs the game's own map files as they are
        raise NewMapError(f"maps/{new}: {src}'s constants don't name the folder of its grid the way the game's maps "
                          f"do, so it can't be copied")
    _set_text(mk, infos[0], "MapPath", f"DataDir:{BS}datasmap{BS}{new}")
    adding(out.glad, read_glad, _member("Patchable" + BS + "map" + BS + new + BS + "MapConstante"),
           mk.to_member(compress=bool(mk.flags & 0x80)))
    adding(out.data, read_data, "datasmap" + BS + low + BS + "mapinfo.win",
           must(read_data, "datasmap" + BS + q.group(1).lower() + BS + "mapinfo.win", "grid (mapinfo.win)"))

    # 4. the map list: a new entry, a top object like every other, loading the new scenario cluster
    swap = _renamer(re.compile(r"^(Patchable[\\/]Scenario[\\/])(" + re.escape(folder) + r")([\\/]" + re.escape(sub)
                               + r"[\\/]ClusterMap)$", re.I),
                    re.compile(r"^(map[\\/])(" + re.escape(folder) + r")([\\/]" + re.escape(sub)
                               + r"[\\/]ClusterMap\.ndfbin)$", re.I))(new)
    j = _copy(m, mi, {}, lambda s: swap(s) or s)
    o = m.objects[j]
    names = {_text(m, _props(m, x).get("Name")) for x in m.objects if m.classes[x.cls] == "TMapLoadInfo"}
    out.entry_name = _list_name(list_name, spec.names["us"], new, names)
    for prop, text in (("Name", out.entry_name), ("Path", new), ("RootDatapackName", new)):
        if prop in load:
            _set_text(m, o, prop, text)
    _set(m, o, "GUID", Value(0x1A, out.guid))
    m.set_topo(list(m.topo) + [j])
    # its own pictures in the menus (map.toml picture, wide_picture): the copied record's own copies of the shipped
    # pictures' records named after files of the copy's own, made from the modder's pictures (rusemod.menupicture)
    if spec.picture_data is not None or spec.wide_picture_data is not None:
        from .menupicture import SIZES, PictureError, pictures
        try:
            made = pictures(spec.picture_data, spec.wide_picture_data)
        except PictureError as exc:
            raise NewMapError(f"maps/{new}: {spec.picture or spec.wide_picture}: {exc}") from None
        for prop, stem, _w, _h in SIZES:
            t = local_ref(_props(m, o)[prop]) if prop in _props(m, o) else None
            if stem not in made or t is None or "FileName" not in _props(m, m.objects[t]):
                continue
            _set_text(m, m.objects[t], "FileName", "DataDir:" + BS + BS.join(["Test", "map", new, stem + ".png"]))
            out.zz_new[BS.join(["gen", "test", "map", low, stem.lower() + ".tgv"])] = made[stem]
        if not out.zz_new:
            out.notes.append(f"{new}: {src}'s entry has no picture of its own to replace, so "
                             f"{spec.picture or spec.wide_picture} isn't used")

    # 5. the menu: its own entry beside the shipped one's. BATTLES: in the menu pack that lists the shipped map, after
    # the maps of its size. An Operation or a campaign chapter: at the end of its pack's list, the briefing, pictures,
    # bonus times and population caps the shipped one's (its mission script too: the scenario's cluster still names
    # the shipped one's scripting folder).
    gs = _props(g, g.objects[gi])
    out.key = _free_key(read_zz)
    tracks = {(_text(g, _props(g, x).get("TrackingId")) or "") for x in g.objects}
    stem, t = TRACKS[kind]
    while f"{stem}{t:02d}" in tracks:
        t += 1
    dropped = DROPPED if kind == "battles" else ()
    k = g.add_object(g.objects[gi].cls, [(pi, v) for pi, v in g.objects[gi].props if g.prop_name(pi) not in dropped])
    _set(g, g.objects[k], "GUID", Value(0x1A, out.guid))
    _set(g, g.objects[k], "Description", Value(0x1D, struct.pack("<Q", name_to_key(out.key))))
    if "TrackingId" in gs:
        _set_text(g, g.objects[k], "TrackingId", f"{stem}{t:02d}")
    if kind == "battles":
        left = _props(g, g.objects[k])
        if not any(p.startswith("DispoMulti") and v.tc in (0x00, 0x02) and v.scalar() for p, v in left.items()):
            raise NewMapError(f"maps/{new}: {list_name!r} is only offered in ranked games, which a copy can't join; "
                              f"pick another entry")
        if any(p in gs for p in LADDER):
            out.notes.append(f"{new} isn't offered in ranked games (the shipped map's ladder place stays its own)")
    _place(g, gi, k, at_end=kind != "battles")
    out.glad_changed = {MAPINFO: m.to_member(compress=bool(m.flags & 0x80)),
                        GLOBALS: g.to_member(compress=bool(g.flags & 0x80))}

    # 6. its name in the menus, in every language (the others fall back to English)
    for lang in loc.LANGS + ("dev",):
        member = loc.member(MENU_TEXTS, lang)
        raw = read_zz(member)
        if raw is None:
            continue
        dic = Dic(raw)
        dic.add(name_to_key(out.key), spec.names["us"] if lang == "dev" else spec.names.get(lang, spec.names["us"]))
        out.texts[member] = dic.to_bytes()
    if not out.texts:
        raise NewMapError(f"maps/{new}: the menus' texts ({MENU_TEXTS}.dic) aren't in ZZ_Win.dat, so the new map "
                          f"would have no name")
    out.notes.insert(0, f"{new}: a copy of {list_name!r} ({src}), listed in {MENU_NAMES[kind]} as "
                        f"{spec.names['us']!r} (text {out.key} in {len(out.texts)} dictionaries; map list "
                        f"{out.entry_name!r}, scenario {out.scenario}), its pack {pack_file(new)} copied from "
                        f"{out.pack_from}")
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


def _free_key(read_zz) -> str:
    """The first map-name key (M_D_31, M_D_32, ...) no language's menu dictionary uses yet."""
    used = set()
    for lang in loc.LANGS + ("dev",):
        raw = read_zz(loc.member(MENU_TEXTS, lang))
        if raw is not None:
            used |= {e.key for e in Dic(raw).entries}
    n = KEY_FIRST
    while name_to_key(f"{KEY_STEM}{n:02d}") in used:
        n += 1
    return f"{KEY_STEM}{n:02d}"


def _place(g: Ndf, source: int, new: int, at_end: bool = False) -> None:
    """Put menu entry `new` in the menu pack listing `source`, after the last entry of its size group (CategoryId):
    the menus show a pack's maps in runs of one size. `at_end`: last in the list (an Operation, a campaign chapter:
    the shipped ones keep their order and numbers)."""
    def cat(i):
        p = _props(g, g.objects[i])
        return p["CategoryId"].scalar() if "CategoryId" in p else None
    for o in g.objects:
        for k, (pi, v) in enumerate(o.props):
            if v.tc != 0x11:
                continue
            items = sub_values(v)
            refs = [local_ref(x) for x in items]
            if source not in refs:
                continue
            at = len(items) if at_end else max(n for n, r in enumerate(refs) if r is not None and cat(r) == cat(new)) + 1
            items.insert(at, Value(0x09, struct.pack("<III", 0xBBBBBBBB, new, g.objects[new].cls)))
            o.props[k] = (pi, Value(0x11, struct.pack("<I", len(items)) + b"".join(x.encode() for x in items)))
            return
    raise NewMapError("the shipped map's BATTLES entry isn't in a menu pack, so the new map can't be listed")


# --- the packs, as the build writes them -------------------------------------------------------------------------------
class Grown:
    """A pack with new members on top (a new map's files): reads see them like the pack's own members; writing adds
    them, and a change to one of them changes what is added. The pack under it (an Edat, or a pack .rmod mods
    changed) is only read."""

    def __init__(self, base, members: dict):
        self.base = base
        self.added: dict[str, bytes] = {}
        self._new: dict[str, Entry] = {}
        for path, data in members.items():
            self.add(path, data)

    def __getattr__(self, name):
        return getattr(self.base, name)

    def add(self, path: str, data: bytes) -> None:
        path = path.replace("/", BS)
        if self.entry(path) is not None:
            raise ValueError(f"can't add {path}: the pack already has it")
        self.added[path] = bytes(data)
        self._new[path.lower()] = Entry(path, 0, len(data), 0, -1 - len(self._new))

    @property
    def entries(self) -> list:
        return list(self.base.entries) + list(self._new.values())

    @property
    def is_changed(self) -> bool:
        return bool(self.added) or getattr(self.base, "is_changed", False)

    def entry(self, path: str):
        return self.base.entry(path) or self._new.get(path.replace("/", BS).lower())

    def find(self, suffix: str):
        e = self.entry(suffix)
        if e is not None:
            return e
        try:
            return self.base.find(suffix)
        except KeyError:
            low = suffix.replace("/", BS).lower()
            e = next((x for k, x in self._new.items() if k.endswith(low)), None)
            if e is None:
                raise
            return e

    def read(self, entry) -> bytes:
        return self.added[entry.path] if entry.dict_pos < 0 else self.base.read(entry)

    def added_with(self, replace=None) -> dict:
        """The members this pack adds, with the changes in `replace` (member -> new bytes) that are theirs."""
        added = dict(self.added)
        for key, blob in (replace or {}).items():
            e = self._new.get(key.replace("/", BS).lower())
            if e is not None:
                added[e.path] = blob
        return added

    def iter_chunks(self, replace=None, add=None):
        rest = {k: v for k, v in (replace or {}).items() if k.replace("/", BS).lower() not in self._new}
        return self.base.iter_chunks(rest, {**self.added_with(replace), **(add or {})})

    def to_bytes(self, replace=None, add=None) -> bytes:
        return b"".join(self.iter_chunks(replace, add))

    def write_to(self, out, replace=None, add=None) -> int:
        n = 0
        for chunk in self.iter_chunks(replace, add):
            out.write(chunk)
            n += len(chunk)
        return n


class NewPack:
    """A new map's pack: the shipped map's (as the build has it, .rmod changes included), written under the new name
    with an id of its own."""

    is_changed = True   # always written: the game has no such file

    def __init__(self, base, pack_id: bytes, source: str = ""):
        self.base, self.pack_id, self.source = base, bytes(pack_id), source   # source: the shipped pack's file name

    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def checksum(self) -> bytes:
        return self.pack_id

    def iter_chunks(self, replace=None, add=None):
        first = True
        for chunk in self.base.iter_chunks(replace, add):
            if first:
                chunk, first = bytes(chunk[:8]) + self.pack_id + bytes(chunk[24:]), False
            yield chunk

    def to_bytes(self, replace=None, add=None) -> bytes:
        return b"".join(self.iter_chunks(replace, add))

    def write_to(self, out, replace=None, add=None) -> int:
        n = 0
        for chunk in self.iter_chunks(replace, add):
            out.write(chunk)
            n += len(chunk)
        return n
