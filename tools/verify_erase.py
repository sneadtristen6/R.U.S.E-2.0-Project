"""Check rusemod.scenery.erase_objects on a shipped map (read-only: the game is read in memory, nothing is written).

    py -3 tools/verify_erase.py [game folder] [--map M04_Cotentin] [--at X Y] [--radius 10000]

Erases the trees and props in a circle (default: D-Day, 100 m across a wood and across a town) and checks that the new
file reads back, that every tree and prop inside is gone and everything else inside stays, and that every object
outside is still drawn exactly where it was, hung on the same leaves of the top block's tree (the cells the game finds
it through); the road pieces and the grids are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.scenery import (IDENTITY, MEMBER, EraseArea, Scenery, _leaf_boxes, compose,  # noqa: E402
                             descriptors, erase_objects)
from rusemod.steam import find_game  # noqa: E402

SPOTS = {"M04_Cotentin": [("a wood", 1974337.0, 1592683.0), ("a town", 1945431.0, 1035089.0)]}


def drawn(sc: Scenery, keep) -> Counter:
    """Per item of the top block (its kind, name, transform and the leaf boxes listing it): a digest of the objects
    under it that `keep(name, x, y)` keeps, as (name, x, y)."""
    local = []  # per block: its objects (name, x, y, z) and its children (block index, transform)
    for b in sc.blocks:
        objs, kids = [], []
        for it in b.items:
            if it.kind == "object":
                m = it.matrix()
                objs.append((it.symbol, m[3], m[7], m[11]))
            elif it.kind == "child":
                kids.append((sc._by_offset[it.child_offset], it.matrix()))
        local.append((objs, kids))
    top = sc.blocks[0]
    boxes = _leaf_boxes(top)
    cells: dict = {}
    for e, at in enumerate(top.entries):
        cells.setdefault(at, set()).add(tuple(round(v, 1) for v in boxes[e]))
    out = Counter()
    for it in top.items:
        if it.kind == "road":
            continue
        found = []
        if it.kind == "object":
            m = it.matrix()
            if keep(it.symbol, m[3], m[7]):
                found.append((it.symbol, round(m[3], 1), round(m[7], 1)))
        else:
            todo = [(sc._by_offset[it.child_offset], it.matrix())]
            while todo:
                bi, m = todo.pop()
                objs, kids = local[bi]
                a, b, c, t, d, e, f, u = m[:8]
                for s, x, y, z in objs:
                    wx, wy = a * x + b * y + c * z + t, d * x + e * y + f * z + u
                    if keep(s, wx, wy):
                        found.append((s, round(wx, 1), round(wy, 1)))
                for j, cm in kids:
                    todo.append((j, compose(m, cm)))
        if found:
            found.sort()
            key = (it.kind, it.symbol if it.kind == "object" else None, it.data, tuple(sorted(cells[it.at])))
            out[(key, hashlib.sha1(repr(found).encode()).hexdigest(), len(found))] += 1
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("game", nargs="?")
    ap.add_argument("--map", default="M04_Cotentin")
    ap.add_argument("--at", nargs=2, type=float)
    ap.add_argument("--radius", type=float, default=10000.0)
    a = ap.parse_args(argv)
    game = Path(a.game) if a.game else Path((find_game() or {}).get("game_dir") or "")
    if not (game / "Maps" / "PC").is_dir():
        print("R.U.S.E. not found; give its folder")
        return 2
    with Edat.open(str(find_pack(game, "ZZ_GladPatchableWin.dat"))) as unit:
        descs = descriptors(unit)
    with Edat.open(str(game / "Maps" / "PC" / f"DataMap{a.map}_v09.dat")) as arc:
        raw = bytes(arc.read(arc.find(MEMBER)))
    sc = Scenery(raw)
    kinds = {i: descs[n].group for i, n in enumerate(sc.names) if n in descs}
    bridges = {i for i, n in enumerate(sc.names) if n in descs and descs[n].bridge}
    spots = [("the circle", *a.at)] if a.at else SPOTS.get(a.map)
    if not spots:
        print(f"give --at X Y for {a.map}")
        return 2
    failures = 0
    for what, x, y in spots:
        t0 = time.time()
        area = EraseArea(x, y, a.radius)
        new, notes, by = erase_objects(raw, [area], kinds, bridges)
        t = Scenery(new)  # reads back: the sum, the layout, every item
        r2 = a.radius ** 2

        def inside(px, py):
            return (px - x) ** 2 + (py - y) ** 2 <= r2

        def removable(s):
            return kinds.get(s) in area.what and s not in bridges
        old_kept = drawn(sc, lambda s, px, py: not (inside(px, py) and removable(s)))
        new_all = drawn(t, lambda s, px, py: True)
        left = sum(cnt * n for (_k, _h, cnt), n in drawn(t, lambda s, px, py: inside(px, py) and removable(s)).items())
        problems = []
        if old_kept != new_all:
            problems.append(f"{sum((old_kept - new_all).values())} top-block item(s) draw other objects or in other "
                            f"leaves than before")
        if left:
            problems.append(f"{left} tree(s) or prop(s) still drawn inside the circle")
        if sorted(t.roads()) != sorted(sc.roads()):
            problems.append("the road pieces changed")
        if new[t.grids[0][0]:] != raw[sc.grids[0][0]:]:
            problems.append("the grids changed")
        objects_old, objects_new = sum(sc.types().values()), sum(t.types().values())
        if objects_old - objects_new != sum(by.values()):
            problems.append(f"{objects_old - objects_new} objects fewer, but {sum(by.values())} said erased")
        status = "FAIL" if problems else "ok"
        failures += bool(problems)
        print(f"{a.map} {what} ({x:.0f}, {y:.0f}), radius {a.radius / 100:.0f} m: {status}  {'; '.join(notes)}; "
              f"{len(raw):,} -> {len(new):,} bytes, {len(sc.blocks)} -> {len(t.blocks)} blocks; "
              f"{time.time() - t0:.0f} s")
        for p in problems:
            print(f"    {p}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
