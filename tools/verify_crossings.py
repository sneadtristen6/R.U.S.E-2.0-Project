"""Check rusemod.nav's crossings on the installed game: for a map's own roads, the crossings Graph.add_crossings makes
in each movement graph (mapinfo.win buffers 1 and 2, the main graph) against the map's own. Reads only; the game folder
is never changed.

    py -3 tools/verify_crossings.py                       (D-Day, the game found through Steam)
    py -3 tools/verify_crossings.py <map> [<game folder>]  (e.g. m04_cotentin, supercrossroads4)

Each graph's own crossings are taken out, made again from the map's road network, and matched by circle, gates and
road links: how many of the map's are made again, how many more are made, and how far the matched ones' points and
lengths are from the map's. Fails when fewer than 85% are made again or more than 15% of those made are extra.
On D-Day (2026-10-01): 92% (infantry) and 95% (vehicles) made again, 4% and 5% extra, points within 0.71 map units
and lengths within 0.1. About 40% of the misses are in towns, where the map's own roads cross gaps in the town's
ground longer than new ones may (nav.GAP); the rest are roads that turn back at a gate, pass a third one or leave the
circle on the way.
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import nav  # noqa: E402
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.home import find_game  # noqa: E402
from rusemod.roadnet import RoadNet  # noqa: E402
from ruse_mod_engine import sdb  # noqa: E402


def records(g: nav.Graph) -> dict:
    """{(circle, gate a, gate b, road link 0, road link 1): (x0, y0, x1, y1, length)} of a graph's own crossings."""
    out = {}
    for c in range(len(g.circles) - 1):
        for k in range(g.circles[c][4], g.circles[c + 1][4]):
            x0, y0, x1, y1, length, ga, gb, r0, r1 = struct.unpack_from("<5f4H", g.crossings, 28 * k)
            out[(c, ga, gb, r0, r1)] = (x0, y0, x1, y1, length)
    return out


def compare(g: nav.Graph, net: RoadNet) -> dict:
    own = records(g)
    g.crossings = b""
    g.circles = [c[:4] + (0,) for c in g.circles]
    g.add_crossings(net)
    made = records(g)
    both = set(own) & set(made)
    point = max((max(math.hypot(own[k][0] - made[k][0], own[k][1] - made[k][1]),
                     math.hypot(own[k][2] - made[k][2], own[k][3] - made[k][3])) for k in both), default=0.0)
    lengths = sorted(abs(own[k][4] - made[k][4]) for k in both)
    return {"own": len(own), "made": len(made), "matched": len(both), "point": point,
            "length": lengths[len(lengths) // 2] if lengths else 0.0}


def main(argv: list[str]) -> int:
    name = argv[1] if len(argv) > 1 else "m04_cotentin"
    found = None if len(argv) > 2 else find_game()
    if len(argv) <= 2 and found is None:
        print("R.U.S.E. wasn't found; give its folder.")
        return 2
    game = Path(argv[2]) if len(argv) > 2 else Path(found["game_dir"])
    with Edat.open(str(find_pack(game, "DataMap_Win.dat"))) as arc:
        win = bytes(arc.read(arc.find(f"datasmap\\{name}\\mapinfo.win")))
    bufs = sdb.split_mapinfo(win)[1]
    net = RoadNet.read(bufs[0])
    bad = 0
    for k, what in ((1, "infantry"), (2, "vehicles")):
        got = compare(nav.Graph.read(bufs[k]), net)
        share = got["matched"] / got["own"] if got["own"] else 1.0
        extra = (got["made"] - got["matched"]) / got["made"] if got["made"] else 0.0
        ok = share >= 0.85 and extra <= 0.15
        bad += not ok
        print(f"{name} {what}: {got['own']} crossings of its own, {got['made']} made, {got['matched']} the same "
              f"({share:.1%}; {extra:.1%} of those made are extra); matched ones' points within {got['point']:.2f}, "
              f"lengths within {got['length']:.2f} (median){'' if ok else '  TOO DIFFERENT'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
