"""Check rusemod.roadnet on the installed game: every map's road network (mapinfo.win buffer 0) reads and writes
back byte for byte, and its index rebuilt our way still reaches every link. Reads only; the game folder is never
changed.

    py -3 tools/verify_roadnet.py            (the game found through Steam)
    py -3 tools/verify_roadnet.py <game folder>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import roadnet  # noqa: E402
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.home import find_game  # noqa: E402
from ruse_mod_engine import sdb  # noqa: E402


def leaves(node) -> list[int]:
    return node[1] if node[0] == "leaf" else leaves(node[2]) + leaves(node[3])


def main(argv: list[str]) -> int:
    found = None if len(argv) > 1 else find_game()
    if len(argv) <= 1 and found is None:
        print("R.U.S.E. wasn't found; give its folder.")
        return 2
    game = Path(argv[1]) if len(argv) > 1 else Path(found["game_dir"])
    sys.setrecursionlimit(10000)
    bad = checked = 0
    with Edat.open(str(find_pack(game, "DataMap_Win.dat"))) as arc:
        for e in arc.entries:
            path = e.path.lower()
            if not path.startswith("datasmap") or not path.endswith("mapinfo.win"):
                continue  # test\map\seize\mapinfo.win is an older layout, not used by any map
            name = e.path.split("\\")[-2]
            data = sdb.split_mapinfo(bytes(arc.read(e)))[1][0]
            try:
                net = roadnet.RoadNet.read(data)
            except (roadnet.RoadNetError, ValueError) as exc:
                print(f"{name}: can't be read ({exc})")
                bad += 1
                continue
            same = net.to_bytes() == data
            ours = roadnet.build_tree(net.points, net.links)
            reach = set(leaves(ours)) == set(range(len(net.links)))
            print(f"{name}: {len(net.points)} points, {len(net.links)} links; written back "
                  f"{'identical' if same else 'DIFFERENT'}; our index reaches {'every' if reach else 'NOT every'} link")
            bad += (not same) + (not reach)
            checked += 1
    print(f"{checked} maps, {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
