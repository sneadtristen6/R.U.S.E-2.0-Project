"""Check rusemod.nav on the installed game: every map's two navigation graphs (mapinfo.win buffers 1 and 2) read
and write back byte for byte, with their counts. Reads only; the game folder is never changed.

    py -3 tools/verify_nav.py            (the game found through Steam)
    py -3 tools/verify_nav.py <game folder>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import nav  # noqa: E402
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.home import find_game  # noqa: E402
from ruse_mod_engine import sdb  # noqa: E402


def main(argv: list[str]) -> int:
    found = None if len(argv) > 1 else find_game()
    if len(argv) <= 1 and found is None:
        print("R.U.S.E. wasn't found; give its folder.")
        return 2
    game = Path(argv[1]) if len(argv) > 1 else Path(found["game_dir"])
    pack = find_pack(game, "DataMap_Win.dat")
    bad = 0
    with Edat.open(str(pack)) as arc:
        for e in arc.entries:
            if not e.path.lower().startswith("datasmap") or not e.path.lower().endswith("mapinfo.win"):
                continue  # test\map\seize\mapinfo.win is an older layout, not used by any map
            parts = sdb.split_mapinfo(bytes(arc.read(e)))
            name = e.path.split("\\")[-2]
            line = []
            for k, what in ((1, "infantry"), (2, "vehicles")):
                try:
                    g = nav.Graph.read(parts[1][k])
                    ok = g.to_bytes() == parts[1][k]
                    line.append(f"{what}: {len(g.circles) - 1} circles, {len(g.links)} links, {len(g.subs)} local"
                                f"{'' if ok else ' DIFFERENT'}")
                    bad += not ok
                except nav.NavError as exc:
                    line.append(f"{what}: {exc}")
                    bad += 1
            print(f"{name}: " + "; ".join(line))
    print("all same" if not bad else f"{bad} graph(s) differ")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
