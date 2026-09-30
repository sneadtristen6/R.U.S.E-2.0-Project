"""Check rusemod.scenery on every map the game ships (read-only).

    py -3 tools/verify_scenery.py [game folder]

Per map: the file's MD5 and layout read, every child points forward to a block's start, every object's name is in
the name table and resolves to a scenery type (a few names on four maps don't, in the game itself), and the counts
agree (per-block counts vs per-type counts). The totals over the 32 shipped maps: 321,029,228 objects and 78,417
road pieces (the figures of DomesticNukes and his Claude, whose notes this reader follows).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.scenery import MEMBER, Scenery, SceneryError, descriptors  # noqa: E402
from rusemod.steam import find_game  # noqa: E402


def main(argv: list[str]) -> int:
    game = Path(argv[0]) if argv else (find_game() or {}).get("game_dir")
    if not game:
        print("R.U.S.E. not found; give its folder")
        return 2
    with Edat.open(str(find_pack(Path(game), "ZZ_GladPatchableWin.dat"))) as unit:
        descs = descriptors(unit)
    failures, objects, roads, t0 = 0, 0, 0, time.time()
    for pack in sorted((Path(game) / "Maps" / "PC").glob("DataMap*_v09.dat")):
        name = pack.name[len("DataMap"):-len("_v09.dat")]
        problems = []
        with Edat.open(str(pack)) as arc:
            try:
                sc = Scenery(arc.read(arc.find(MEMBER)))
            except (KeyError, SceneryError) as exc:
                print(f"{name:<28} FAIL  {exc}")
                failures += 1
                continue
        weight = [0] * len(sc.blocks)
        for r in sc.roots():
            weight[r] += 1
        n_obj = n_road = 0
        unresolved = set()
        for b in sc.blocks:
            for it in b.items:
                if it.kind == "child":
                    j = sc._by_offset.get(it.child_offset)
                    if j is None or j <= b.index:
                        problems.append(f"block {b.index}: a child points back or off a block start")
                        continue
                    weight[j] += weight[b.index]
                elif it.kind == "road":
                    n_road += weight[b.index]
                else:
                    n_obj += weight[b.index]
                    if it.symbol >= len(sc.names) - 1:
                        problems.append(f"block {b.index}: a name index past the table")
                    elif sc.names[it.symbol] not in descs:
                        unresolved.add(sc.names[it.symbol])
        if sum(sc.types().values()) != n_obj or sum(sc.counts()[r] for r in sc.roots()) != n_obj:
            problems.append("the per-block and per-type counts disagree")
        objects, roads = objects + n_obj, roads + n_road
        state = "FAIL" if problems else "ok"
        failures += bool(problems)
        print(f"{name:<28} {state:<5} blocks {len(sc.blocks):>4}  objects {n_obj:>10,}  road pieces {n_road:>6,}"
              + (f"  unresolved names: {len(unresolved)}" if unresolved else "")
              + (f"  | {problems[0]}" if problems else ""), flush=True)
    print(f"total: {objects:,} objects, {roads:,} road pieces; {failures} map(s) failed; {time.time() - t0:.0f} s")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
