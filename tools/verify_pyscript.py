r"""Check rusemod.pyscript against the real game, read-only (docs/FORMATS.md §5, PLAN.md decision 23).

A. Every compiled script (.xyz, in the .ipk packs of every archive) reads: container, size, marshal data.
B. The Python unit list (ZZ_Win.dat!genpython\eugenpatchable.ipk -> parametres\classes.xyz): how many classes, how
   many follow the standard two-line template and are registered, and their base classes.
C. A dry run: a class for a made-up copy of the M3 Lee is added and passes check_added.
D. With --compare INSTANCE: the unit list in that modded copy, against A-C's reading of the game's.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_pyscript.py [GAME] [--compare D:\RUSE-Instances\x]
"""
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod import pyscript  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def scripts(arc, where):
    for e in arc.entries:
        if e.path.lower().endswith(".ipk"):
            yield from scripts(Edat(bytes(arc.read(e))), f"{where}!{e.path}")
        elif e.path.lower().endswith(".xyz"):
            yield f"{where}!{e.path}", bytes(arc.read(e))


def unit_list_of(path):
    with Edat.open(path) as arc:
        found = pyscript.find_unit_list(arc)
        if found is None:
            raise SystemExit(f"no unit list in {path}")
        return pyscript.read_xyz(found[3])


def main(argv):
    compare = argv[argv.index("--compare") + 1] if "--compare" in argv else None
    args = [a for i, a in enumerate(argv) if a != "--compare" and (i == 0 or argv[i - 1] != "--compare")]
    game = args[0] if args else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat")))
    ok, bad = 0, []
    for p in packs:
        if os.path.basename(p) == "Data_Common.dat":
            continue  # videos and fonts only
        with Edat.open(p) as arc:
            for name, raw in scripts(arc, os.path.basename(p)):
                try:
                    pyscript.load(pyscript.read_xyz(raw).payload)
                    ok += 1
                except pyscript.ScriptError as exc:
                    bad.append((name, str(exc)))
    print(f"A. compiled scripts read: {ok} of {ok + len(bad)}")
    for name, why in bad[:10]:
        print(f"   FAIL {name}: {why}")

    zz = next(p for p in packs if os.path.basename(p).lower() == "zz_win.dat")
    xyz = unit_list_of(zz)
    ul = pyscript.unit_list(xyz.payload)
    standard = [c for c in ul.classes.values() if c.standard]
    registered = [c for c in ul.classes.values() if c.registered]
    bases = collections.Counter(".".join(c.base) for c in ul.classes.values())
    print(f"B. unit list: {len(ul.classes)} classes, {len(standard)} standard, {len(registered)} registered, "
          f"{len(ul.by_path)} unit paths")
    print(f"   bases: {dict(bases.most_common())}")
    odd = [c.name for c in ul.classes.values() if not (c.standard and c.registered)]
    if odd:
        print(f"   not standard or not registered: {odd[:10]}")

    probe = pyscript.NewClass("Unit_R2_Verify_Test", "$/GFX/Everything/Descriptor_Unit_R2_Verify_Test", "Unit_M3_Lee")
    new = pyscript.add_classes(xyz.payload, [probe])
    after = pyscript.unit_list(new)
    c = after.classes[probe.name]
    print(f"C. dry run: {probe.name}(front.{'.'.join(c.base)}) for {c.path}: passes check_added; "
          f"module {len(xyz.payload):,} -> {len(new):,} bytes, classes {len(ul.classes)} -> {len(after.classes)}")

    if compare:
        other = unit_list_of(os.path.join(compare, "Data", "PC", os.path.basename(os.path.dirname(zz)), "ZZ_Win.dat"))
        theirs = pyscript.unit_list(other.payload)
        extra = sorted(set(theirs.classes) - set(ul.classes))
        print(f"D. {compare}: {len(theirs.classes)} classes; added: {extra}; source MD5 kept: "
              f"{other.source_md5 == xyz.source_md5}")
        for name in extra:
            t = theirs.classes[name]
            print(f"   {name}(front.{'.'.join(t.base)}) -> {t.path}, standard {t.standard}, registered {t.registered}")
        if extra:
            same = pyscript.add_classes(xyz.payload, [pyscript.NewClass(n, theirs.classes[n].path, "Unit_M3_Lee")
                                                      for n in extra]) == other.payload
            print(f"   byte-identical to what add_classes writes for them (like Unit_M3_Lee): {same}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
