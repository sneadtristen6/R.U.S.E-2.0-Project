"""Check the clearing along new roads (rusemod.scenery.road_clearing) on a shipped map (read-only: the game is read in
memory, nothing is written).

    py -3 tools/verify_clearing.py [game folder] --roads path/to/roads.toml [--map M04_Cotentin]

Clears the trees and props along each road of a mod's roads.toml the way the build does, then says per road how many
objects went and how much the map's scenery grew, and checks that the new file reads back, that the objects fewer
match the count, and that no tree or prop is left inside a road's strip.
"""
from __future__ import annotations

import argparse
import sys
import time
import tomllib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.roadnet import parse_roads  # noqa: E402
from rusemod.scenery import (CLEAR_HALF, DATA_LIMIT, MEMBER, Scenery, descriptors, erase_objects,  # noqa: E402
                             road_clearing)
from rusemod.steam import find_game  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("game", nargs="?")
    ap.add_argument("--map", default="M04_Cotentin")
    ap.add_argument("--roads", required=True)
    a = ap.parse_args(argv)
    game = Path(a.game) if a.game else Path((find_game() or {}).get("game_dir") or "")
    if not (game / "Maps" / "PC").is_dir():
        print("R.U.S.E. not found; give its folder")
        return 2
    roads = parse_roads(tomllib.loads(Path(a.roads).read_text(encoding="utf-8")).get("road", []), a.roads)
    with Edat.open(str(find_pack(game, "ZZ_GladPatchableWin.dat"))) as unit:
        descs = descriptors(unit)
    with Edat.open(str(game / "Maps" / "PC" / f"DataMap{a.map}_v09.dat")) as arc:
        raw = bytes(arc.read(arc.find(MEMBER)))
    sc = Scenery(raw)
    kinds = {i: descs[n].group for i, n in enumerate(sc.names) if n in descs}
    bridges = {i for i, n in enumerate(sc.names) if n in descs and descs[n].bridge}
    jobs = [(n, road_clearing(r.points)) for n, r in enumerate(roads, start=1) if r.clear]
    areas = [s for _n, strips in jobs for s in strips]
    t0 = time.time()
    tally: dict = {}
    new, notes, by = erase_objects(raw, areas, kinds, bridges, tally)
    took = time.time() - t0
    t = Scenery(new)
    problems = []
    gone = sum(sc.types().values()) - sum(t.types().values())
    if gone != sum(by.values()):
        problems.append(f"{gone} objects fewer, but {sum(by.values())} said erased")
    if sorted(t.roads()) != sorted(sc.roads()):
        problems.append("the road pieces changed")
    left = Counter()
    groups = ("vegetation", "prop")
    for s, m in t.walk():
        if kinds.get(s) in groups and s not in bridges and any(z.dist2(m[3], m[7]) <= z.radius ** 2 for z in areas):
            left[kinds[s]] += 1
    if left:
        problems.append(f"still inside the strips: {dict(left)}")
    k = 0
    for n, strips in jobs:
        cleared = sum(tally.get(i, 0) for i in range(k, k + len(strips)))
        k += len(strips)
        r = roads[n - 1]
        length = sum(((bx - ax) ** 2 + (by_ - ay) ** 2) ** 0.5 for (ax, ay), (bx, by_) in zip(r.points, r.points[1:]))
        print(f"road {n}: {length / 100:,.0f} m long, from ({r.points[0][0]:.0f}, {r.points[0][1]:.0f}), "
              f"{len(strips)} strip(s) {2 * CLEAR_HALF:.0f} wide: {cleared:,} trees and props cleared")
    used = t.fields[3]
    print(f"{a.map}: {'; '.join(notes)}")
    print(f"  scenery {len(raw):,} -> {len(new):,} bytes ({len(new) - len(raw):+,}); blocks' data {sc.fields[3]:,} -> "
          f"{used:,} of {DATA_LIMIT:,} ({DATA_LIMIT - used:,} left); {took:.0f} s")
    print("  ok" if not problems else "  FAIL")
    for p in problems:
        print(f"    {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
