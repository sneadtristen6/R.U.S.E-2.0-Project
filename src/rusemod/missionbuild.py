"""What a new Operation's or chapter's own mission (rusemod.mission) adds to the build: its script, its texts, its
camera moves and its own menu pack. The steps are T41's (2026-10-09, played in the game: a mission of our own in its
own folder, its texts, the Operation and the chapter each in a menu pack of their own), moved into the build:

- the copy's scenario cluster names its own script folder and text file (the copied mission's are left alone);
- the script (rusemod.missionscript) goes into IA_Common.dat beside the copied mission's;
- the texts: the copied mission's text files (its sides' names are there) under the new folder, with the mission's
  goals and messages added, each language in its own words or the English;
- the camera moves: the copy's own camera file, the copied map's with the new paths added, each listed in the file's
  TOPO table (the game makes only the objects that table lists: T41's own path, left out of it, never played), and
  the copy's MapIA naming that file;
- the menus: the entry alone in a pack of its own (the game keeps saved results and opens chapters by pack and
  place in the pack; a mission of ours in a pack of its own lands on no shipped mission's saves, and a chapter first
  in its pack is open).
"""
from __future__ import annotations

import hashlib
import re
import struct

from . import mission as M
from .dic import Dic, name_to_key
from .missionscript import assemble, source
from .ndf import Ndf, Value, sub_values
from .pyscript import Xyz, write_xyz

BS = "\\"
FOLDER = "Scripting_Mission"   # the new mission's folder, beside the copied mission's under the new map's name


class MissionBuildError(ValueError):
    pass


def _props(nd: Ndf, o) -> dict:
    return {nd.prop_name(pi): v for pi, v in o.props}


def cluster_folders(raw: bytes, src: str) -> tuple[str, str]:
    """(the copied mission's script folder, its text file) as the copy's scenario cluster names them."""
    nd = Ndf(raw)
    s = re.escape(src)
    py = [x for x in nd.strings if re.fullmatch(r"DataDir:\\Test\\map\\" + s + r"\\(scripting[^\\]*)", x, re.I)]
    loc = [x for x in nd.strings if re.fullmatch(s + r"\\(scripting[^\\]*)\\Localization\.csv", x, re.I)]
    if len(py) != 1 or len(loc) != 1:
        raise MissionBuildError(f"the copy's scenario cluster doesn't name one mission folder and one text file "
                                f"({len(py)} and {len(loc)})")
    return py[0], loc[0]


def entry_folder(read_glad, src: str, entry: str | None) -> str:
    """The script folder of shipped map `src`'s menu entry `entry` (its BATTLES entry when None), as its scenario
    cluster names it (Anzio: scripting_challenge; its scenario file's name doesn't say)."""
    from .newmap import _cluster_base, _member, _props, menu_entries
    from .players import GLOBALS, MAPINFO
    g_raw, m_raw = read_glad(GLOBALS), read_glad(MAPINFO)
    if g_raw is None or m_raw is None:
        # not a game rule: the game or one of its files isn't found
        raise MissionBuildError("the game's menus aren't in ZZ_GladPatchableWin.dat")
    m, g = Ndf(m_raw), Ndf(g_raw)
    found = [f for f in menu_entries(m, g, src) if (f[2] == entry if entry else f[3] == "battles")]
    if len(found) != 1:
        raise MissionBuildError(f"{src} has no one entry {entry!r} to read the mission of")
    base = _cluster_base(m, _props(m, m.objects[found[0][0]]))
    raw = read_glad(_member(base)) if base else None
    if raw is None:
        # not a game rule: the game or one of its files isn't found
        raise MissionBuildError(f"{entry or src}'s scenario cluster isn't in the game")
    return cluster_folders(raw, src)[0].rsplit(BS, 1)[1]


def cluster_pointed(raw: bytes, src: str, new: str) -> tuple[bytes, str]:
    """The copy's scenario cluster with its script folder and text file at the new mission's; and the copied
    mission's folder name (scripting_challenge...)."""
    from .newmap import _swap_strings
    py, loc = cluster_folders(raw, src)
    nd = Ndf(raw)
    swaps = {py.lower(): BS.join(["DataDir:", "Test", "map", new, FOLDER]),
             loc.lower(): BS.join([new, FOLDER, "Localization.csv"])}
    n = _swap_strings(nd, lambda x: swaps.get(x.lower()))
    if n != 2 or any(x.lower() in swaps for x in nd.strings):
        raise MissionBuildError("the copy's scenario cluster still names the copied mission's folder")
    return nd.to_member(compress=bool(nd.flags & 0x80)), py.rsplit(BS, 1)[1]


def script_members(ia, src: str, folder: str, new: str) -> tuple[str, str]:
    """(the copied mission's script in IA_Common.dat, where the new one goes)."""
    want = BS.join(["test", "map", src, folder, "effetmap.xyz"]).lower()
    found = [e.path for e in ia.entries if e.path.lower().endswith(BS + want) and e.path.lower().startswith("genpython")]
    if len(found) != 1:
        raise MissionBuildError(f"the copied mission's script ({want}) wasn't found once in IA_Common.dat")
    head = found[0][:len(found[0]) - len(want)]
    return found[0], head + BS.join(["test", "map", new.lower(), FOLDER.lower(), "effetmap.xyz"])


def text_files(zz_entries, read, src: str, folder: str, new: str, words: dict) -> dict:
    """{new member: bytes}: the copied mission's text files under the new folder, with `words` {key name: Words}
    added (each file's language: translations\\<lang>\\..., else English)."""
    suffix = BS.join([src, folder, "localization.dic"]).lower()
    out = {}
    for path in [p for p in zz_entries if p.lower().endswith(BS + suffix)]:
        q = re.search(r"\\translations\\([^\\]+)\\", path.lower())
        lang = q.group(1) if q and q.group(1) in M.LANGS else "us"
        d = Dic(read(path))
        for name, w in words.items():
            d.add(name_to_key(name), w.get(lang))
        out[path[:len(path) - len(suffix)] + BS.join([new.lower(), FOLDER.lower(), "localization.dic"])] = d.to_bytes()
    if not out:
        raise MissionBuildError(f"the copied mission's text files (…\\{suffix}) weren't found")
    for path, raw in out.items():
        d = Dic(raw)
        q = re.search(r"\\translations\\([^\\]+)\\", path.lower())
        lang = q.group(1) if q and q.group(1) in M.LANGS else "us"
        if any(d.text(name_to_key(n)) != w.get(lang) for n, w in words.items()):
            raise MissionBuildError(f"{path}: the mission's texts didn't read back")
    return out


def camera_file_of(mapia_raw: bytes, src: str) -> str | None:
    """The copied map's camera file (a DataMap_Win.dat member) as its MapIA names it, or None."""
    nd = Ndf(mapia_raw)
    at = re.compile(r"^DataDir:\\Test\\Map\\" + re.escape(src) + r"(\\CamPath\\[^\\]+\.ndfbin)$", re.I)
    found = [x for x in nd.strings if at.match(x)]
    if not found:
        return None
    return ("test" + BS + "map" + BS + src + at.match(found[0]).group(1)).lower()


def camera_paths(raw: bytes) -> list[str]:
    nd = Ndf(raw)
    out = []
    for o in nd.objects:
        if nd.classes[o.cls] == "TCameraPath":
            v = _props(nd, o).get("Name")
            if v is not None:
                out.append(nd.strings[struct.unpack_from("<I", v.payload)[0]])
    return out


def with_cameras(raw: bytes, cams: list) -> bytes:
    """The copied map's camera file with each of `cams` (mission.Camera) added as a path, laid out as Eugen's files
    (a path, then its points, then its directions) and listed in the TOPO table."""
    nd = Ndf(raw)
    path_cls, key_cls = nd.class_index("TCameraPath"), nd.class_index("TCameraPathKey")
    taken = set(camera_paths(raw))

    def prop(name, cls):
        for i, (n, c) in enumerate(nd.props):
            if n == name and c == cls:
                return i
        return nd.add_prop(name, cls)
    first = next((o for o in nd.objects if o.cls == path_cls), None)
    if first is None:
        raise MissionBuildError("the camera file has no path to copy the layout of")
    ref0 = sub_values(_props(nd, first)["PositionKeyVector"])[0]

    def ref(obj: int) -> bytes:
        p = bytearray(ref0.payload)
        struct.pack_into("<I", p, 4, obj)
        return Value(ref0.tc, bytes(p)).encode()
    topo = list(nd.topo)
    for c in cams:
        if c.name in taken:
            raise MissionBuildError(f"camera move {c.name!r}: the map's camera file already has a path of that name")
        keys = M.camera_keys(c)
        at = len(nd.objects)
        pos = list(range(at + 1, at + 1 + len(keys)))
        dirs = list(range(at + 1 + len(keys), at + 1 + 2 * len(keys)))
        i = nd.string_index(c.name)
        nd.add_object(path_cls, [
            (prop("PositionKeyVector", path_cls), Value(0x11, struct.pack("<I", len(pos)) + b"".join(map(ref, pos)))),
            (prop("DirectionKeyVector", path_cls), Value(0x11, struct.pack("<I", len(dirs)) + b"".join(map(ref, dirs)))),
            (prop("Name", path_cls), Value(0x07, struct.pack("<I", nd.add_string(c.name) if i is None else i)))])
        for p, _d in keys:
            nd.add_object(key_cls, [(prop("Coord", key_cls), Value(0x0B, struct.pack("<3f", *p)))])
        for _p, d in keys:
            nd.add_object(key_cls, [(prop("Coord", key_cls), Value(0x0B, struct.pack("<3f", *d)))])
        topo.append(at)
    nd.set_topo(topo)
    out = nd.to_member(compress=bool(nd.flags & 0x80))
    back = Ndf(out)
    names = camera_paths(out)
    listed = [back.strings[struct.unpack_from("<I", _props(back, back.objects[t])["Name"].payload)[0]]
              for t in back.topo if back.classes[back.objects[t].cls] == "TCameraPath"]
    for c in cams:
        if c.name not in names or c.name not in listed:
            raise MissionBuildError(f"camera move {c.name!r} didn't read back listed in the camera file")
    return out


def mapia_pointed(raw: bytes, src: str, new: str) -> bytes:
    """The copy's MapIA naming the copy's own camera file."""
    from .newmap import _swap_strings
    nd = Ndf(raw)
    at = re.compile(r"^(DataDir:\\Test\\Map\\)(" + re.escape(src) + r")(\\CamPath\\[^\\]+\.ndfbin)$", re.I)
    n = _swap_strings(nd, lambda x: at.sub(lambda q: q.group(1) + new + q.group(3), x) if at.match(x) else None)
    if n < 1 or any(at.match(x) for x in nd.strings):
        raise MissionBuildError("the copy's MapIA wasn't pointed at its own camera file")
    return nd.to_member(compress=bool(nd.flags & 0x80))


def own_packs(raw: bytes, moves: list) -> bytes:
    """globals.cpp with each (entry GUID, "campaign" or "operation", new pack GUID) taken out of the pack it was
    listed in and put in a new pack of its own, listed last by its pack manager (T41's own_packs)."""
    nd = Ndf(raw)
    for guid, kind, pack_guid in moves:
        pack_c, mgr_c, list_p, mgr_p = (("TChapterPack", "TChapterPackManager", "ChapterList", "ChapterPackList")
                                        if kind == "campaign" else
                                        ("TChallengePack", "TChallengePackManager", "ChallengeList", "ChallengePackList"))
        info = [i for i, o in enumerate(nd.objects) if "GUID" in _props(nd, o)
                and bytes(_props(nd, o)["GUID"].payload) == guid]
        if len(info) != 1:
            raise MissionBuildError(f"menus: {len(info)} entries carry the copy's id")
        info = info[0]
        holders, ref_proto = [], None
        for i, o in enumerate(nd.objects):
            if nd.classes[o.cls] != pack_c:
                continue
            for k, (pi, v) in enumerate(o.props):
                if nd.prop_name(pi) == list_p:
                    items = sub_values(v)
                    keep = [x for x in items if struct.unpack_from("<I", x.payload, 4)[0] != info]
                    if len(keep) != len(items):
                        holders.append(i)
                        o.props[k] = (pi, Value(0x11, struct.pack("<I", len(keep)) + b"".join(x.encode() for x in keep)))
                        ref_proto = items[0]
        if len(holders) != 1 or ref_proto is None:
            raise MissionBuildError(f"menus: the copy's entry was in {len(holders)} packs")
        shipped = nd.objects[holders[0]]
        guid_p = next(pi for pi, _v in shipped.props if nd.prop_name(pi) == "PackGUID")
        guid_v = next(v for pi, v in shipped.props if pi == guid_p)
        lst_p = next(pi for pi, _v in shipped.props if nd.prop_name(pi) == list_p)
        p = bytearray(ref_proto.payload)
        struct.pack_into("<I", p, 4, info)
        new_pack = nd.add_object(shipped.cls, [(guid_p, Value(guid_v.tc, pack_guid)),
                                               (lst_p, Value(0x11, struct.pack("<I", 1)
                                                             + Value(ref_proto.tc, bytes(p)).encode()))])
        mgr = [o for o in nd.objects if nd.classes[o.cls] == mgr_c]
        if len(mgr) != 1:
            raise MissionBuildError(f"menus: {len(mgr)} {mgr_c}")
        for k, (pi, v) in enumerate(mgr[0].props):
            if nd.prop_name(pi) == mgr_p:
                packs = sub_values(v)
                q = bytearray(packs[0].payload)
                struct.pack_into("<I", q, 4, new_pack)
                if len(q) >= 12 and struct.unpack_from("<I", q, 8)[0] != shipped.cls:
                    struct.pack_into("<I", q, 8, shipped.cls)
                mgr[0].props[k] = (pi, Value(0x11, struct.pack("<I", len(packs) + 1) + b"".join(
                    x.encode() for x in packs) + Value(packs[0].tc, bytes(q)).encode()))
    out = nd.to_member(compress=bool(nd.flags & 0x80))
    back = Ndf(out)
    for _guid, kind, pack_guid in moves:
        pack_c, list_p = ("TChapterPack", "ChapterList") if kind == "campaign" else ("TChallengePack", "ChallengeList")
        mine = [o for o in back.objects if back.classes[o.cls] == pack_c
                and bytes(_props(back, o)["PackGUID"].payload) == pack_guid]
        if len(mine) != 1 or len(sub_values(_props(back, mine[0])[list_p])) != 1:
            raise MissionBuildError(f"menus: the mission's own {kind} pack didn't read back")
    return out


def compiled(m: M.Mission, base: M.Base, ctx: M.Context, new: str) -> tuple[bytes, str]:
    """(the .xyz script, its source as Python, for the record)."""
    imports, defs, launch = M.script(m, base, ctx, name_to_key)
    filename = BS.join(["datadir:", "test", "map", new.lower(), FOLDER.lower(), "effetmap.py"])
    text = source(imports, defs, launch)
    return write_xyz(Xyz(hashlib.md5(text.encode("latin-1")).digest(), assemble(imports, defs, launch, filename))), text
