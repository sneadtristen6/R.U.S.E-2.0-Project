r"""Check the moddingSuite lead on the TOPO table (READ-ONLY). See docs/FORMATS.md, open question 1.

moddingSuite (MIT; Wargame, and it lists R.U.S.E. too) reads TOPO as the list of "top objects", writes it as their
indices sorted by class, and adds every new top-level object to it. If R.U.S.E. works the same way, adding objects
(new units) only needs TOPO updated by that rule. For every NDF file that has a TOPO table, this reports whether:
  A. TOPO is sorted by (class, object index)
  B. TOPO holds exactly the objects that nothing else in the file refers to (the "roots")
  C. every exported (named) object is in TOPO
Nothing is written.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\topo_check.py [game_dir]
"""
import collections
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402
from rusemod.ndf import iter_values, local_ref  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def topo_of(ndf):
    b = ndf._sec("TOPO")
    return [struct.unpack_from("<I", b, 4 * i)[0] for i in range(len(b) // 4)]


def check_file(ndf):
    """Return the facts for one file, or None if it has no TOPO entries."""
    topo = topo_of(ndf)
    if not topo:
        return None
    n = len(ndf.objects)
    referenced = set()
    for o in ndf.objects:
        for _pi, v in o.props:
            for x in iter_values(v):
                r = local_ref(x)
                if r is not None:
                    referenced.add(r)
    roots = set(range(n)) - referenced
    top = set(topo)
    return {
        "objects": n,
        "topo": len(topo),
        "duplicates": len(topo) - len(top),
        "out_of_range": sum(1 for i in topo if i >= n),
        "A_sorted_by_class": topo == sorted(topo, key=lambda i: (ndf.objects[i].cls if i < n else -1, i)),
        "B_equals_roots": top == roots,
        "in_topo_not_root": sorted(top - roots)[:5],
        "root_not_in_topo": sorted(roots - top)[:5],
        "C_exports_in_topo": set(ndf.exports) <= top,
    }


def walk_ndf(arc, where):
    for e in arc.entries:
        data = bytes(arc.read(e))
        if data[:4] == b"edat":
            yield from walk_ndf(Edat(data), f"{where}!{e.path}")
        elif data[:4] == b"EUG0" and data[8:12] == b"CNDF":
            yield f"{where}!{e.path}", data


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat"))) + \
        sorted(glob.glob(os.path.join(game, "Maps", "PC", "*.dat")))
    if not packs:
        print(f"no archives found under {game}")
        return 2
    totals = collections.Counter()
    misses = collections.defaultdict(list)
    for path in packs:
        with Edat.open(path) as arc:
            for where, raw in walk_ndf(arc, os.path.basename(path)):
                facts = check_file(Ndf(raw))
                if facts is None:
                    continue
                totals["files with TOPO"] += 1
                for k in ("A_sorted_by_class", "B_equals_roots", "C_exports_in_topo"):
                    if facts[k]:
                        totals[k] += 1
                    elif len(misses[k]) < 5:
                        misses[k].append((where, facts))
                if facts["duplicates"] or facts["out_of_range"]:
                    totals["files with duplicate or out-of-range entries"] += 1
    n = totals["files with TOPO"]
    print(f"files with a TOPO table: {n}")
    for k, label in [("A_sorted_by_class", "A. sorted by (class, index)"),
                     ("B_equals_roots", "B. exactly the objects nothing refers to"),
                     ("C_exports_in_topo", "C. every named object is in TOPO")]:
        print(f"  {label}: {totals[k]} of {n}")
        for where, f in misses[k]:
            print(f"    miss: {where}  ({f['topo']} TOPO / {f['objects']} objects; "
                  f"in TOPO but referenced: {f['in_topo_not_root']}; unreferenced but not in TOPO: {f['root_not_in_topo']})")
    bad = totals["files with duplicate or out-of-range entries"]
    print(f"  files with duplicate or out-of-range TOPO entries: {bad}")
    print("\nIf A, B and C hold everywhere, adding a top-level object = append its index and keep TOPO sorted by class.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
