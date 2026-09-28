r"""Check the name-tree writer against every NDF file in the game (READ-ONLY). See src/rusemod/names.py.

Before the bridge adds names for new objects (M2 clones), this confirms on the real files that:
  A. every EXPR and IMPR tree rebuilds byte-identically from its parsed form (same node layout);
  B. how siblings are ordered: by name (case-insensitive / case-sensitive) or not, so new names can go in the
     same way the game's own do (the writer keeps name order where a node already has it).
Nothing is written.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\names_check.py [game_dir]
"""
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf, names  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def walk_ndf(arc, where):
    for e in arc.entries:
        data = bytes(arc.read(e))
        if data[:4] == b"edat":
            yield from walk_ndf(Edat(data), f"{where}!{e.path}")
        elif data[:4] == b"EUG0" and data[8:12] == b"CNDF":
            yield f"{where}!{e.path}", data


def order_stats(root, trans, stats):
    if root is None:
        return
    kids = [trans[c.tran] for c in root.children]
    if len(kids) >= 2:
        stats["nodes with 2+ children"] += 1
        stats["in case-insensitive name order"] += [k.lower() for k in kids] == sorted(k.lower() for k in kids)
        stats["in case-sensitive name order"] += kids == sorted(kids)
    for c in root.children:
        order_stats(c, trans, stats)


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat"))) + \
        sorted(glob.glob(os.path.join(game, "Maps", "PC", "*.dat")))
    if not packs:
        print(f"no archives found under {game}")
        return 2
    t = collections.Counter()
    misses = []
    for path in packs:
        with Edat.open(path) as arc:
            for where, raw in walk_ndf(arc, os.path.basename(path)):
                ndf = Ndf(raw)
                t["files"] += 1
                for sec, tree in (("EXPR", ndf.expr_tree), ("IMPR", ndf.impr_tree)):
                    t[f"{sec} trees"] += tree is not None
                    if names.to_bytes(tree) == ndf._sec(sec):
                        t[f"{sec} rebuilt byte-identical"] += 1
                    elif len(misses) < 10:
                        misses.append(f"{where} {sec}")
                    order_stats(tree, ndf.trans, t)
    print(f"NDF files: {t['files']}")
    for sec in ("EXPR", "IMPR"):
        print(f"  A. {sec} rebuilt byte-identical: {t[f'{sec} rebuilt byte-identical']} of {t['files']} "
              f"({t[f'{sec} trees']} non-empty)")
    for m in misses:
        print(f"     miss: {m}")
    n = t["nodes with 2+ children"]
    print(f"  B. nodes with 2+ children: {n}; in case-insensitive name order: {t['in case-insensitive name order']}; "
          f"in case-sensitive name order: {t['in case-sensitive name order']}")
    return 0 if not misses else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
