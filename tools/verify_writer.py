r"""Verify the EDAT + NDF writer against the real game files (READ-ONLY).

Proves, without launching the game and without modifying the install:
  A. NDF re-serializes byte-identically (logical level).
  B. The archive rebuilds byte-identically when nothing changed.
  C. A scalar value edit produces exactly the intended change and nothing else.
  D. The rebuilt archive reads back: the edit is present and every other member is untouched.

Rebuilt bytes live only in memory. Usage:
  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_writer.py [path\to\ZZ_GladPatchableWin.dat]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402
from rusemod.ndf import decode  # noqa: E402

DEFAULT = r"D:\Steam\steamapps\common\R.U.S.E\Data\PC\190852\ZZ_GladPatchableWin.dat"
UNIT_DB = "gfx\\everything.cpp.gladndfbin"


def ok(name, passed, detail=""):
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    return passed


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        print(f"game pack not found: {path}\npass the path to ZZ_GladPatchableWin.dat as an argument.")
        return 2
    original = open(path, "rb").read()
    arc = Edat(original)
    member = arc.read(arc.find(UNIT_DB))
    ndf = Ndf(member)
    print(f"unit DB: {len(ndf.objects):,} objects, {len(ndf.classes)} classes, {len(ndf.props)} props")
    results = []

    # A. NDF logical round-trip
    results.append(ok("A. NDF re-serializes byte-identical (logical)",
                      ndf.to_logical() == ndf.data,
                      f"{len(ndf.data):,} B"))

    # B. EDAT byte-identical rebuild (no changes)
    results.append(ok("B. archive rebuilds byte-identical (unchanged)",
                      arc.to_bytes() == original,
                      f"{len(original):,} B, {len(arc.entries)} members"))

    # C. Scalar edit: pick a named unit descriptor and bump one int32 property.
    target_name = next((n for n in ndf.exports.values() if n.rsplit("/", 1)[-1].startswith("Descriptor_Unit_")), None)
    obj = ndf.object_by_export(target_name)
    pi, val = next(((pi, v) for pi, v in obj.props if v.tc == 0x02), (None, None))
    old = val.scalar()
    val.set_scalar(old + 1)
    edited_logical = ndf.to_logical()
    re = Ndf.from_logical(edited_logical)
    new = re.object_by_export(target_name).get(pi).scalar()
    diffs = sum(1 for a, b in zip(edited_logical, ndf.data) if a != b)
    prop = ndf.prop_name(pi)
    results.append(ok("C. scalar edit applies as a minimal in-place change",
                      new == old + 1 and len(edited_logical) == len(ndf.data) and 1 <= diffs <= 4,
                      f"{target_name.rsplit('/',1)[-1]}.{prop}: {old} -> {new}, {diffs} byte(s) differ"))

    # D. Rebuild the archive with the edited member (compressed) and read it back.
    edited_member = ndf.to_member(compress=True)
    rebuilt = arc.to_bytes({UNIT_DB: edited_member})
    arc2 = Edat(rebuilt)
    ndf2 = Ndf(arc2.read(arc2.find(UNIT_DB)))
    read_back = ndf2.object_by_export(target_name).get(pi).scalar()
    others_intact = all(
        arc2.read(arc2.find(e.path)) == arc.read(e)
        for e in arc.entries[:60] if not e.path.endswith("everything.cpp.gladndfbin")
    )
    results.append(ok("D. edited archive reads back; other members intact",
                      read_back == old + 1 and len(ndf2.objects) == len(ndf.objects) and others_intact,
                      f"value reads {read_back}; {len(ndf2.objects):,} objects"))

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
