"""Check a new map in a built modded copy against the game it was built from (rusemod.newmap, MOD_FORMAT §8 "A new
map"): every registration and file the copy has for it, read back from the copy's packs, is where the others say it
is, with the checksums the game checks, and nothing else of the game changed (for a mod that edits only its new map).
Reads only.

    py -3 tools/verify_newmap.py <modded copy> <new map's pack name> <the shipped map it copies> [<game folder>]

Prints one line per check (ok / FAIL) and returns 1 when one fails.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import loc  # noqa: E402
from rusemod.build import find_pack  # noqa: E402
from rusemod.dic import GLYPH_KEY, Dic, key_to_name  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.ndf import Ndf, local_ref, sub_values  # noqa: E402
from rusemod.newmap import guid_for  # noqa: E402
from rusemod.players import GLOBALS, MAPINFO, entries  # noqa: E402
from rusemod.scenario import checksum as scenario_checksum  # noqa: E402

BS = "\\"
MENU = ("TMultiMapInfo", "TChallengeMapInfo", "TChapterMapInfo")
MAP_CLUSTER = re.compile(r"^Patchable[\\/]map[\\/]([^\\/]+)[\\/]ClusterMap$", re.I)
CONSTANTS = re.compile(r"^Patchable[\\/]map[\\/]([^\\/]+)[\\/]MapConstante$", re.I)


def _props(nd, o) -> dict:
    return {nd.prop_name(pi): v for pi, v in o.props}


def _text(nd, v) -> str | None:
    return nd.strings[struct.unpack("<I", v.payload[:4])[0]] if v is not None and v.tc in (0x07, 0x1C) else None


def _member(base: str) -> str:
    return "genglad" + BS + base.replace("/", BS).lower() + ".cpp.gladndfbin"


def _bases(nd) -> set[str]:
    """The NDF files a file loads (its transactions' BaseName)."""
    return {_text(nd, v) for o in nd.objects for pi, v in o.props if nd.prop_name(pi) == "BaseName" and _text(nd, v)}


def _read(arc):
    def read(member):
        e = arc.entry(member)
        return bytes(arc.read(e)) if e is not None else None
    return read


def _loads(m, load) -> list[str]:
    """The scenario clusters a map-list entry loads."""
    out = []
    for v in sub_values(load["ClusterLoads"])[1::2] if "ClusterLoads" in load else []:
        c = local_ref(v)
        tr = local_ref(_props(m, m.objects[c])["NdfTransaction"]) if c is not None else None
        if tr is not None:
            out.append(_text(m, _props(m, m.objects[tr])["BaseName"]))
    return out


def _mounts(nd) -> list[str]:
    return [_text(nd, _props(nd, o)["DataPack"]) for o in nd.objects if nd.classes[o.cls] == "TClusterMountMapDataPack"]


class Checks:
    def __init__(self, say=print):
        self.say, self.failed = say, 0

    def __call__(self, ok, what: str) -> bool:
        self.say(("ok    " if ok else "FAIL  ") + what)
        self.failed += not ok
        return bool(ok)


def _same_members(check, name, built, shipped, changed: set, added: set) -> None:
    """Every shipped member is in the built pack, byte for byte unless in `changed`; the new ones are `added`."""
    have = {e.path.lower(): e for e in built.entries}
    old = {e.path.lower(): e for e in shipped.entries}
    new = set(have) - set(old)
    check(new == added, f"{name}: the members added are the new map's: {sorted(new)}")
    check(set(old) <= set(have), f"{name}: every shipped member is still there ({len(old)})")
    differ = sorted(p for p, e in old.items() if p in have and p not in changed and built.read(have[p]) != shipped.read(e))
    check(not differ, f"{name}: every other member is as shipped" + (f" (these differ: {differ[:5]})" if differ else ""))


def verify(copy: Path, new: str, source: str, game: Path, say=print) -> int:
    """The checks on the new map `new` (its pack name), a copy of `source`, in the modded copy at `copy` built from
    `game`. Returns how many failed."""
    check = Checks(say)
    copy, game, low = Path(copy), Path(game), new.lower()
    names = ("ZZ_GladPatchableWin.dat", "DataMap_Win.dat", "ZZ_Win.dat")
    packs = {n: (find_pack(copy, n), find_pack(game, n)) for n in names}
    new_pack = find_pack(copy, f"DataMap{new}_v09.dat")
    if not check(all(c and g for c, g in packs.values()) and new_pack is not None,
                 f"the copy has its packs and Maps{BS}PC{BS}DataMap{new}_v09.dat"):
        return check.failed
    check(find_pack(game, f"DataMap{new}_v09.dat") is None, "the game folder has no such pack (it was only read)")
    opened = {n: (Edat.open(str(c)), Edat.open(str(g))) for n, (c, g) in packs.items()}
    try:
        (glad, glad0), (data, data0), (zz, zz0) = (opened[n] for n in names)
        rg, rg0, rd = _read(glad), _read(glad0), _read(data)
        m, g, m0, g0 = Ndf(rg(MAPINFO)), Ndf(rg(GLOBALS)), Ndf(rg0(MAPINFO)), Ndf(rg0(GLOBALS))
        # 1. the map list and BATTLES
        found = entries(m, g, new)
        if not check(len(found) == 1, f"the map list has one entry for {new}, tied to one BATTLES entry by its GUID"):
            return check.failed
        mi, gi, list_name = found[0]
        load, multi = _props(m, m.objects[mi]), _props(g, g.objects[gi])
        guid = bytes(load["GUID"].payload)
        check(guid == guid_for(new, "entry"), f"its GUID {guid.hex()} is the one its name gives")
        check(sum(bytes(v.payload) == guid for nd in (m, g) for o in nd.objects for pi, v in o.props
                  if nd.prop_name(pi) == "GUID") == 2, "no other entry has that GUID")
        check(mi in m.topo and m.topo == m0.topo + [mi], f"its map-list entry {list_name!r} is a top object after the "
                                                         f"shipped {len(m0.topo)}, which are as they were")
        lists = [(g.classes[o.cls], len(sub_values(v))) for o in g.objects for _pi, v in o.props
                 if v.tc == 0x11 and gi in [local_ref(x) for x in sub_values(v)]]
        check(len(lists) == 1 and lists[0][0] == "TMultiPack" and gi not in g.topo,
              f"its BATTLES entry is in one menu pack ({lists[0][1] if lists else 0} maps), reached through it only")
        track = _text(g, multi.get("TrackingId"))
        check([_text(g, _props(g, o).get("TrackingId")) for o in g.objects].count(track) == 1,
              f"its TrackingId {track} is its own")
        key = struct.unpack("<Q", multi["Description"].payload)[0]
        check([bytes(v.payload) for o in g.objects if g.classes[o.cls] in MENU for pi, v in o.props
               if g.prop_name(pi) == "Description"].count(bytes(multi["Description"].payload)) == 1,
              f"its name's key {key_to_name(key)} is its own")
        check(not any(p.startswith("DispoLadder") for p in multi) and any(
            p.startswith("DispoMulti") and v.scalar() for p, v in multi.items() if v.tc in (0x00, 0x02)),
            "it's offered in BATTLES and online, not in ranked games")
        # 2. its name in the menus
        for lang in loc.LANGS + ("dev",):
            member = loc.member("flash_txt", lang)
            e0 = zz0.entry(member)
            if e0 is None:
                continue
            d, d0 = Dic(bytes(zz.read(zz.entry(member)))), Dic(bytes(zz0.read(e0)))
            name = d.text(key) or ""
            glyphs = d0.glyphs is None or (d.glyphs.startswith(d0.glyphs) and all(c in d.glyphs for c in name))
            check(name and len(d.entries) == len(d0.entries) + 1 and glyphs and all(
                d.text(x.key) == x.text for x in d0.entries if x.key != GLYPH_KEY),
                f"{lang}: the menus call it {name!r}; the other {len(d0.entries)} texts are as shipped (the list of "
                f"characters the file uses grown by the name's new ones)")
        # 3. the scenario cluster: the scenario and the map cluster it names
        bases = _loads(m, load)
        base = bases[0] if bases and len(set(bases)) == 1 else ""
        if not check(base and rg(_member(base)) is not None and f"{BS}{low}{BS}" in _member(base),
                     f"its entry loads the scenario cluster {base}, which the copy has"):
            return check.failed
        sc = Ndf(rg(_member(base)))
        files = {re.sub(r"(?i)^DataDir:[\\/]", "", s).replace("/", BS).lower() for s in sc.strings if s.lower().endswith(".scenario")}
        scenario = next(iter(files)) if len(files) == 1 else ""
        raw = rd(scenario) if scenario.startswith(BS.join(["test", "map", low, ""])) else None
        check(raw is not None and raw[:10] == b"SCENARIO\r\n" and raw[10:26] == scenario_checksum(raw),
              f"it names the scenario {sorted(files)}, which DataMap_Win.dat has, with a good checksum")
        maps = [b for b in _bases(sc) if MAP_CLUSTER.match(b)]
        check(len(maps) == 1 and MAP_CLUSTER.match(maps[0]).group(1).lower() == low and rg(_member(maps[0])) is not None,
              f"it loads the map cluster {maps}, which the copy has")
        # 4. the map cluster: the pack it mounts, the constants it loads
        mc = Ndf(rg(_member(maps[0]))) if len(maps) == 1 else None
        mounted = _mounts(mc) if mc else []
        check(len(mounted) == 1 and mounted[0].split(BS)[-1].lower() == new_pack.name.lower(),
              f"the map cluster mounts {mounted}, the copy's new pack")
        consts = [b for b in _bases(mc) if CONSTANTS.match(b)] if mc else []
        check(len(consts) == 1 and CONSTANTS.match(consts[0]).group(1).lower() == low and rg(_member(consts[0])) is not None,
              f"it loads the constants {consts}, which the copy has")
        # 5. the constants: the folder of the grid
        mk = Ndf(rg(_member(consts[0]))) if len(consts) == 1 else None
        paths = [_text(mk, _props(mk, o).get("MapPath")) for o in mk.objects if mk.classes[o.cls] == "TCurrentMapInfo"] if mk else []
        grid = (re.sub(r"(?i)^DataDir:[\\/]", "", paths[0]) + BS + "mapinfo.win").lower() if len(paths) == 1 else ""
        win = rd(grid) if grid.startswith(BS.join(["datasmap", low, ""])) else None
        check(win is not None and win[:8] == b"INFOIA\r\n"
              and win[8:24] == hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + win[24:]).digest(),
              f"the constants name its grid {grid}, which DataMap_Win.dat has, with a good checksum")
        # 6. every other file the new files load is the shipped map's (some, editor-only, no map has)
        for nd, what in ((sc, "the scenario cluster"), (mc, "the map cluster"), (mk, "the constants")):
            missing = sorted(b for b in _bases(nd) if rg(_member(b)) is None) if nd else ["(unread)"]
            check(all(low not in b.lower() and rg0(_member(b)) is None for b in missing),
                  f"{what}: every file it loads is in the copy, but {len(missing)} editor-only file(s) no shipped map has")
        # 7. the new pack: the shipped one's members, with an id of its own
        src = []  # what the shipped map's cluster mounts
        for mi0, _gi0, _name0 in entries(m0, g0, source)[:1]:
            for b0 in _loads(m0, _props(m0, m0.objects[mi0])):
                src += [_mounts(Ndf(rg0(_member(b)))) for b in _bases(Ndf(rg0(_member(b0)))) if MAP_CLUSTER.match(b)]
        shipped = find_pack(game, src[0][0].split(BS)[-1]) if src and src[0] else None
        if check(shipped is not None, f"the shipped map {source} mounts {shipped and shipped.name}"):
            with Edat.open(str(new_pack)) as mp, Edat.open(str(shipped)) as mp0:
                ids = {}
                for f in sorted((copy / "Maps" / "PC").glob("*.dat")):
                    with Edat.open(str(f)) as other:
                        ids.setdefault(bytes(other.checksum), []).append(f.name)
                check(bytes(mp.checksum) == guid_for(new, "pack") and ids[bytes(mp.checksum)] == [new_pack.name],
                      f"the new pack's id {bytes(mp.checksum).hex()} is the one its name gives, and no other map pack's")
                check({e.path.lower() for e in mp.entries} == {e.path.lower() for e in mp0.entries},
                      f"it has {shipped.name}'s {len(mp0.entries)} members")
                differ = sorted(e.path for e in mp0.entries if mp.read(mp.entry(e.path)) != mp0.read(e))
                say(f"      its members the mod changed: {', '.join(differ) or 'none'}")
                boobs = bytes(mp.read(mp.find("output" + BS + "save.boobspc")))
                check(boobs[:16] == hashlib.md5(boobs[16:]).digest(), "its scenery (save.boobspc) has a good checksum")
                sdb = bytes(mp.read(mp.find("output" + BS + "output.sdb")))
                n = struct.unpack_from("<I", sdb, 25)[0]
                check(sdb[5:21] == hashlib.md5(b"SDB\r\n" + sdb[21:29 + n]).digest(),
                      "its sight layer (output.sdb) has a good checksum")
        # 8. nothing else of the game changed
        added = {_member(base).lower()} | ({_member(maps[0]).lower()} if len(maps) == 1 else set()) | (
            {_member(consts[0]).lower()} if len(consts) == 1 else set())
        _same_members(check, "ZZ_GladPatchableWin.dat", glad, glad0, {MAPINFO, GLOBALS}, added)
        _same_members(check, "DataMap_Win.dat", data, data0, set(), {scenario, grid} - {""})
        _same_members(check, "ZZ_Win.dat", zz, zz0, {loc.member("flash_txt", x).lower() for x in loc.LANGS + ("dev",)}, set())
        same = all([(m0.prop_name(pi), v.tc, bytes(v.payload)) for pi, v in o.props]
                   == [(m.prop_name(pi), v.tc, bytes(v.payload)) for pi, v in m.objects[i].props]
                   for i, o in enumerate(m0.objects))
        check(same and len(m.objects) > len(m0.objects), "every shipped map-list object is as it was")
        same = all([(g0.prop_name(pi), v.tc, bytes(v.payload)) for pi, v in o.props]
                   == [(g.prop_name(pi), v.tc, bytes(v.payload)) for pi, v in g.objects[i].props]
                   for i, o in enumerate(g0.objects) if g0.classes[o.cls] != "TMultiPack")
        check(same, "every shipped menu object but the menu pack that lists the new map is as it was")
    finally:
        for c, g_ in opened.values():
            c.close()
            g_.close()
    say(f"{check.failed} check(s) failed")
    return check.failed


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 4:
        print(__doc__)
        return 2
    game = argv[4] if len(argv) > 4 else None
    if game is None:
        from rusemod.home import find_game
        found = find_game()
        if found is None:
            print("R.U.S.E. wasn't found; give its folder.")
            return 2
        game = found["game_dir"]
    return 1 if verify(Path(argv[1]), argv[2], argv[3], Path(game)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
