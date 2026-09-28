r"""Check C3, step 1 (READ-ONLY): how does the game mount packs? See docs/PLAN.md §7.

Lists every NDF class whose name contains Mount, DataPack, Pack or Cluster, across every NDF file in every pack
(nested packs included): where its objects are, their export names, their text values (strings, paths, wide
strings, with how many values in that file share each string), and which objects refer to them.
Then lists RUSE.exe's own strings that contain the same words. Nothing is written.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\c3_survey.py [game_dir] > c3_survey.txt
"""
import collections
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402
from rusemod.ndf import _read_value  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
CLASS_WORDS = re.compile(r"mount|datapack|pack|cluster", re.I)
EXE_WORDS = re.compile(rb"[\x20-\x7e]{5,}")
MAX_OBJECTS_SHOWN = 40  # per class; classes with more show the first ones and a count


def walk_ndf(arc, where):
    """Yield (location, raw bytes) for every NDF member, descending into nested packs."""
    for e in arc.entries:
        data = bytes(arc.read(e))
        if data[:4] == b"edat":
            yield from walk_ndf(Edat(data), f"{where}!{e.path}")
        elif data[:4] == b"EUG0" and data[8:12] == b"CNDF":
            yield f"{where}!{e.path}", data


def sub_values(v):
    """The values nested inside a list (0x11), map (0x12) or pair (0x22)."""
    b, out = v.payload, []
    if v.tc in (0x11, 0x12):
        cnt, p = struct.unpack_from("<I", b, 0)[0], 4
        for _ in range(cnt * (2 if v.tc == 0x12 else 1)):
            x, p = _read_value(b, p)
            out.append(x)
    elif v.tc == 0x22:
        x, p = _read_value(b, 0)
        y, _ = _read_value(b, p)
        out = [x, y]
    return out


def all_values(v):
    yield v
    for x in sub_values(v):
        yield from all_values(x)


def text_of(ndf, v):
    if v.tc in (0x07, 0x1C):  # string / path: index into STRG
        i = struct.unpack("<I", v.payload)[0]
        return i, ndf.strings[i] if i < len(ndf.strings) else f"<bad STRG index {i}>"
    if v.tc == 0x08:  # wide string, stored inline
        n = struct.unpack_from("<I", v.payload)[0]
        return None, v.payload[4:4 + n].decode("utf-16-le", "replace")
    return None


def local_ref(v):
    if v.tc == 0x09 and struct.unpack_from("<I", v.payload)[0] == 0xBBBBBBBB:
        inst = struct.unpack_from("<I", v.payload, 4)[0]
        return None if inst == 0xFFFFFFFF else inst
    return None


def survey_file(where, ndf, out):
    wanted = {ci for ci, name in enumerate(ndf.classes) if CLASS_WORDS.search(name)}
    if not wanted:
        return
    strg_uses = collections.Counter()
    referrers = collections.defaultdict(list)  # object index -> [(referrer index, property)]
    for oi, o in enumerate(ndf.objects):
        for pi, v in o.props:
            for x in all_values(v):
                t = text_of(ndf, x)
                if t and t[0] is not None:
                    strg_uses[t[0]] += 1
                r = local_ref(x)
                if r is not None:
                    referrers[r].append((oi, ndf.prop_name(pi)))
    for oi, o in enumerate(ndf.objects):
        if o.cls not in wanted:
            continue
        lines = [f"  {where}  #{oi}" + (f"  = {ndf.exports[oi]}" if oi in ndf.exports else "")]
        for pi, v in o.props:
            texts = [text_of(ndf, x) for x in all_values(v)]
            texts = [t for t in texts if t]
            if texts:
                shown = ", ".join(f"'{s}'" + (f" [STRG #{i}, used {strg_uses[i]}x in file]" if i is not None else "")
                                  for i, s in texts)
                lines.append(f"      {ndf.prop_name(pi)} (type 0x{v.tc:02x}) = {shown}")
            else:
                lines.append(f"      {ndf.prop_name(pi)} (type 0x{v.tc:02x})")
        for ri, prop in referrers.get(oi, [])[:5]:
            rname = ndf.exports.get(ri, "")
            lines.append(f"      used by #{ri} {ndf.classes[ndf.objects[ri].cls]} {rname} .{prop}")
        out[ndf.classes[o.cls]].append(lines)


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat"))) + \
        sorted(glob.glob(os.path.join(game, "Maps", "PC", "*.dat")))
    if not packs:
        print(f"no archives found under {game}")
        return 2
    out = collections.defaultdict(list)  # class name -> [object lines]
    n_ndf = 0
    for path in packs:
        with Edat.open(path) as arc:
            for where, raw in walk_ndf(arc, os.path.basename(path)):
                n_ndf += 1
                try:
                    survey_file(where, Ndf(raw), out)
                except Exception as exc:  # report and keep going
                    print(f"  ! could not survey {where}: {exc}")
    print(f"surveyed {n_ndf} NDF files in {len(packs)} packs\n")
    for cls in sorted(out, key=lambda c: (-len(out[c]), c)):
        objs = out[cls]
        print(f"== {cls}: {len(objs)} object(s)")
        for lines in objs[:MAX_OBJECTS_SHOWN]:
            print("\n".join(lines))
        if len(objs) > MAX_OBJECTS_SHOWN:
            print(f"  ... {len(objs) - MAX_OBJECTS_SHOWN} more")
        print()
    exe = os.path.join(game, "RUSE.exe")
    if os.path.exists(exe):
        found = sorted({m.group().decode() for m in EXE_WORDS.finditer(open(exe, "rb").read())
                        if re.search(rb"mount|datapack|pack|cluster", m.group(), re.I)})
        print(f"== RUSE.exe strings with Mount / DataPack / Pack / Cluster: {len(found)}")
        for s in found:
            print("  " + s)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
