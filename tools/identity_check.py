r"""Check the fresh-identity rules for copied units against the real game (READ-ONLY). See src/rusemod/identity.py.

Loads the unit data pack the way `ruse build` does, then reports:
  A. ids: for units, infantry, aircraft and buildings, the properties where no two objects share a value. The build
     gives a clone fresh DescriptorId, TrackingId and ClassNameForDebug; any other id listed here may need adding.
  B. DescriptorId: which classes have it (also inside parts), lowest and highest, and any value two objects share.
  C. ClassNameForDebug: how many follow the pattern Descriptor_<debug name> (the build follows the source's).
  D. build menus: for each nation and factory, the slots in use, row by row (slot = row * 100 + column), and any slot
     two units share.
  E. upgrades: how many units have UpgradeRequire, and parents with more than one upgrade.
  F. the C5 source unit (default Descriptor_Unit_M4_Sherman): its menu values, and what a clone of it gets.
Nothing is written.

Numbers, from RUSE-Mod-Manager's tables (unconfirmed): nations 0 US, 1 Germany, 2 UK, 3 France, 4 Italy, 5 USSR,
6 Japan; factories 3 turrets/defences, 8 barracks, 9 airfield, 10 armour, 11 anti-tank, 12 prototypes, 13 artillery/AA.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\identity_check.py [game_dir] [unit name]
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod.build import load_pack  # noqa: E402
from rusemod.cli import _find_pack  # noqa: E402
from rusemod.identity import DEBUG_NAME, RULES, SLOT, menu_of  # noqa: E402
from rusemod.patch import INT_RANGES, Engine, Inline, Num, Ref, Text, _walk_value, show  # noqa: E402
from rusemod.resolve import ModInfo  # noqa: E402
from rusemod.rndf import parse  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
BUILDABLE = ("TUniteAuSolDescriptor", "TInfanterieDescriptor", "TAvionDescriptor", "TBatimentDescriptor")
KEPT = {"NameInMenuToken": "the name shown in game: kept until text mods can give new names"}


def short(name):
    return name.rsplit("/", 1)[-1].replace("Descriptor_Unit_", "").replace("Descriptor_", "")


def value_key(v):
    """Values that can be ids: whole numbers, strings and text keys (not decimals, file paths or references)."""
    if isinstance(v, Num) and v.kind in INT_RANGES:
        return ("num", v.value)
    if isinstance(v, Text) and v.kind in ("string", "key"):
        return (v.kind, v.value)
    return None


def all_objects(game):
    """(name, Obj, inside a part?) for every object, parts included."""
    for name, obj in game.objects.items():
        yield name, obj, False
        for v in obj.props.values():
            for x in _walk_value(v):
                if isinstance(x, Inline):
                    yield name, x.obj, True


def ids(game):
    print("A. Ids (no two objects of the class share a value):")
    for cls in BUILDABLE:
        objs = [(n, o) for n, o in game.objects.items() if o.cls == cls]
        if not objs:
            continue
        values = collections.defaultdict(list)
        for n, o in objs:
            for p, v in o.props.items():
                k = value_key(v)
                if k is not None:
                    values[p].append(k)
        found = [p for p, ks in sorted(values.items()) if len(ks) >= 2 and len(set(ks)) == len(ks)]
        print(f"  {cls} ({len(objs)} objects):")
        for p in found:
            what = "refreshed by the build" if p in RULES else KEPT.get(p, "NOT refreshed: check it (PLAN.md C5)")
            print(f"    {p:24} set on {len(values[p]):4}   {what}")


def descriptor_ids(game):
    print("B. DescriptorId:")
    where, seen = collections.Counter(), collections.defaultdict(list)
    for name, obj, part in all_objects(game):
        v = obj.props.get("DescriptorId")
        if isinstance(v, Num):
            where[(obj.cls, part)] += 1
            seen[v.value].append(name if not part else f"{name} (part)")
    for (cls, part), n in sorted(where.items()):
        print(f"  {cls}{' (inside parts)' if part else ''}: {n}")
    if seen:
        print(f"  lowest {min(seen)}, highest {max(seen)}")
    shared = {v: ns for v, ns in seen.items() if len(ns) > 1}
    print(f"  values two or more objects share: {len(shared)}")
    for v, ns in sorted(shared.items())[:5]:
        print(f"    {v}: {', '.join(short(n) for n in ns[:4])}")


def debug_names(game):
    print("C. ClassNameForDebug:")
    kinds, odd = collections.Counter(), []
    for name, obj in game.objects.items():
        d = obj.props.get(DEBUG_NAME)
        if not isinstance(d, Text) or not name.startswith("$/"):
            continue
        last = name.rsplit("/", 1)[-1]
        if last == "Descriptor_" + d.value:
            kinds["Descriptor_<debug name>"] += 1
        elif last == d.value:
            kinds["the same as the name"] += 1
        elif last.endswith(d.value):
            kinds["the name ends with it (other prefix)"] += 1
        else:
            kinds["unrelated"] += 1
            odd.append(f"{last} / {d.value}")
    for k, n in kinds.most_common():
        print(f"  {k}: {n}")
    for x in odd[:5]:
        print(f"    unrelated, e.g. {x}")


def menus(game):
    print("D. Build menus (nation, factory): row: column name ...")
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    odd = collections.Counter()
    for name, obj in game.objects.items():
        menu, slot = menu_of(obj), obj.props.get(SLOT)
        if menu is None or not isinstance(slot, Num):
            continue
        s = int(slot.value)
        if s <= 0:
            odd[s] += 1
        groups[menu][s].append(name)
    for (nation, factory), slots in sorted(groups.items()):
        print(f"  nation {nation}, factory {factory}:")
        rows = collections.defaultdict(list)
        for s, names in sorted(slots.items()):
            rows[s // 100].append(f"{s % 100:02} " + "+".join(short(n) for n in names))
        for row, cells in sorted(rows.items()):
            print(f"    row {row}: " + ", ".join(cells))
        for s, names in sorted(slots.items()):
            if len(names) > 1:
                print(f"    shared slot {s}: {', '.join(short(n) for n in names)}")
    if odd:
        print(f"  slots 0 or below: {dict(odd)}")


def upgrades(game):
    print("E. Upgrades:")
    parents = collections.defaultdict(list)
    for name, obj in game.objects.items():
        v = obj.props.get("UpgradeRequire")
        if isinstance(v, Ref) and v.target:
            parents[v.target].append(name)
    is_up = collections.Counter(show(o.props.get("IsUpgrade")) for o in game.objects.values() if "IsUpgrade" in o.props)
    print(f"  units with UpgradeRequire: {sum(len(c) for c in parents.values())}; IsUpgrade values: {dict(is_up)}")
    many = {p: c for p, c in parents.items() if len(c) > 1}
    print(f"  parents with more than one upgrade: {len(many)}")
    for p, c in sorted(many.items())[:5]:
        print(f"    {short(p)}: {', '.join(short(n) for n in c)}")


def source(game, unit):
    print(f"F. C5 source: {unit}")
    obj = game.objects.get(unit)
    if obj is None:
        print("  not found; pick another unit from D (a full name, $/GFX/Everything/Descriptor_Unit_...)")
        return 1
    for p in ("Nationalite", "Factory", SLOT, "ShowInMenu", "ProductionPrice", "UpgradeRequire", "IsUpgrade",
              "DescriptorId", "TrackingId", DEBUG_NAME, "NameInMenuToken"):
        print(f"  {p:18} {show(obj.props.get(p))}")
    ops = parse(f"export Descriptor_Unit_C5_Check is clone {unit} ( )", file="check.rndf", mod="check")
    r = Engine(game).run([(ModInfo("check"), ops)])
    for f in r.findings:
        print(f"  {f.level}: {f.message}")
    return 0 if not r.errors else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game", nargs="?", default=DEFAULT_GAME)
    ap.add_argument("unit", nargs="?", default="$/GFX/Everything/Descriptor_Unit_M4_Sherman")
    args = ap.parse_args()
    pack_path = _find_pack("ZZ_GladPatchableWin.dat", argparse.Namespace(game=args.game))
    with Edat.open(str(pack_path)) as arc:
        game = load_pack(arc).base
    print(f"{pack_path}: {len(game.objects)} objects")
    ids(game)
    descriptor_ids(game)
    debug_names(game)
    menus(game)
    upgrades(game)
    return source(game, args.unit)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
