r"""Check C3 step 2: is a map pack found by the name written in the game data? (docs/PLAN.md §7)

Builds D:\RUSE-Instances\c3-renamed-map where Two Islands' pack is renamed
  Maps\PC\DataMapTwoIslands_v09.dat  ->  Maps\PC\DataMapTwoIslandz_v09.dat   (same size name, content untouched)
and the one place the data names it (genglad\patchable\map\twoislands\clustermap.cpp) is changed to match.
The old name no longer exists in the instance, so the map can only load if the game follows the name in the data.
In the skirmish list the map is "(6) Centre de gravite". The Steam install is never modified.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\make_c3_instance.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402
from rusemod.instance import build_instance  # noqa: E402

GAME = r"D:\Steam\steamapps\common\R.U.S.E"
DST = r"D:\RUSE-Instances\c3-renamed-map"
PACK_REL = r"Data\PC\190852\ZZ_GladPatchableWin.dat"
CLUSTER = r"genglad\patchable\map\twoislands\clustermap.cpp.gladndfbin"
OLD = r"MapDat:\DataMapTwoIslands_v09.dat"
NEW = r"MapDat:\DataMapTwoIslandz_v09.dat"
MAP_OLD = r"Maps\PC\DataMapTwoIslands_v09.dat"
MAP_NEW = r"Maps\PC\DataMapTwoIslandz_v09.dat"


def main():
    with Edat.open(os.path.join(GAME, PACK_REL)) as arc:
        ndf = Ndf(arc.read(arc.find(CLUSTER)))
        idx = ndf.strings.index(OLD)
        ndf.set_string(idx, NEW)
        member = ndf.to_member(compress=True)
        pack = arc.to_bytes({CLUSTER: member})
    # verify before deploying: the rebuilt pack carries the new name
    check = Ndf(Edat(pack).read(Edat(pack).find(CLUSTER)))
    assert NEW in check.strings and OLD not in check.strings, "string edit did not stick"
    print(f"clustermap now points at: {NEW}")
    counts = build_instance(GAME, DST, replace={PACK_REL: pack}, rename={MAP_OLD: MAP_NEW})
    print(f"instance ready: {DST}  {counts}")
    print(f"old map file present in instance: {os.path.exists(os.path.join(DST, MAP_OLD))}")
    print(f"new map file present in instance: {os.path.exists(os.path.join(DST, MAP_NEW))}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
