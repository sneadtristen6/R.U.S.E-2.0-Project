r"""Build a VISIBLE test mod and a safe, launchable copy of the game (C2 acceptance test).

Mod: set every building's ProductionPrice to $1 (all eras, all factions). In-game the whole build menu
reads $1 and you can spam buildings -- an unmissable confirmation the game loaded our rebuilt archive.

Safety: the Steam install is never modified. Every non-.dat file is COPIED (so the game may freely rewrite
config/logs in the instance), the big .dat archives are HARD-LINKED (free, read-only use), and the one modded
archive is written as an independent real file. steam_appid.txt lets RUSE.exe talk to Steam from the copy.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\make_test_instance.py
"""
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402

SRC = r"D:\Steam\steamapps\common\R.U.S.E"
DST = r"D:\RUSE-Instances\test-cheap-buildings"
PACK_REL = r"Data\PC\190852\ZZ_GladPatchableWin.dat"
APPID = "21970"
NEW_PRICE = 1


def build_modded_pack() -> bytes:
    arc = Edat.open(os.path.join(SRC, PACK_REL))
    ndf = Ndf(arc.read(arc.find("gfx\\everything.cpp.gladndfbin")))
    pp = ndf.prop_index("ProductionPrice")
    bcls = ndf.classes.index("TBatimentDescriptor")
    changed = 0
    for o in ndf.objects:
        if o.cls != bcls:
            continue
        v = o.get(pp)
        if v is not None and v.tc == 0x11:
            v.set_int_list([NEW_PRICE] * len(v.int_list()))
            changed += 1
    print(f"set {changed} building prices to ${NEW_PRICE}")
    return arc.to_bytes({"gfx\\everything.cpp.gladndfbin": ndf.to_member(compress=True)})


def deploy(modded: bytes) -> None:
    if os.path.exists(DST):
        print(f"removing old instance {DST}")
        shutil.rmtree(DST)
    linked = copied = 0
    for root, _dirs, files in os.walk(SRC):
        rel_dir = os.path.relpath(root, SRC)
        out_dir = os.path.join(DST, rel_dir) if rel_dir != "." else DST
        os.makedirs(out_dir, exist_ok=True)
        for fn in files:
            src_f = os.path.join(root, fn)
            dst_f = os.path.join(out_dir, fn)
            rel = os.path.relpath(src_f, SRC)
            if rel.lower() == PACK_REL.lower():
                with open(dst_f, "wb") as f:
                    f.write(modded)
            elif fn.lower().endswith(".dat"):
                os.link(src_f, dst_f)   # hard link: free, shares the original inode (read-only in play)
                linked += 1
            else:
                shutil.copy2(src_f, dst_f)  # isolated copy: safe if the game rewrites it
                copied += 1
    with open(os.path.join(DST, "steam_appid.txt"), "w") as f:
        f.write(APPID)
    print(f"instance ready: {DST}  ({linked} archives hard-linked, {copied} files copied)")


def main():
    if not os.path.exists(os.path.join(SRC, PACK_REL)):
        print(f"install not found at {SRC}")
        return 2
    modded = build_modded_pack()
    # sanity: re-read the modded pack before deploying
    check = Ndf(Edat(modded).read(Edat(modded).find("gfx\\everything.cpp.gladndfbin")))
    pp = check.prop_index("ProductionPrice")
    sample = next(o for i, o in enumerate(check.objects)
                  if check.exports.get(i, "").endswith("Descriptor_Building_BatimentAdministratif"))
    print("verify BatimentAdministratif price now:", sample.get(pp).int_list())
    deploy(modded)
    print(f"\nLAUNCH: run  {os.path.join(DST, 'RUSE.exe')}\n"
          "Then: start a Skirmish, open your base build menu -> every building costs $1.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
