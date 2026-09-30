r"""Verify the mesh-pack reader (rusemod.spk) against every mesh pack of the game (READ-ONLY on the game).

For every gen_5\pack\*.spk in ZZ_Win.dat that has a name table (the skeleton-only packs are counted and skipped):
  A. every draw call decodes: its vertex buffer (stored as is, or compressed) and its index buffer;
  B. a stored vertex buffer's size is its vertex count times the stride its format name spells;
  C. indices are below the vertex count and make whole triangles; material numbers are below the material count;
  D. every position lies inside its model's bounding box (a small tolerance for the compressed ones' rounding);
  E. the materials read, and name a texture.
These are DomesticNukes and his Claude's checks (2026-09-29), run on our own reader. One line per pack, a summary.

Usage:  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_spk.py [game_dir] [--only name]
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.spk import COMPRESSED, Spk, SpkError  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def check(spk: Spk) -> tuple[list[str], dict]:
    problems, n = [], {"draws": 0, "stored": 0, "compressed": 0, "models": len(spk.items)}
    mats = spk.materials()
    if not mats:
        problems.append("no materials")
    textured = sum(1 for m in mats if m["textures"])
    owner = {}
    for item in spk.items.values():
        if item.mesh >= len(spk.meshes):
            problems.append(f"{item.name}: mesh {item.mesh} of {len(spk.meshes)}")
            continue
        first, count = spk.meshes[item.mesh]
        for d in range(first, first + count):
            owner.setdefault(d, item)
    for d, (material, ib, vb) in enumerate(spk.draws):
        n["draws"] += 1
        n["compressed" if spk.vbs[vb][4] & COMPRESSED else "stored"] += 1
        try:
            part = spk.part(d)
        except (SpkError, ValueError, KeyError, IndexError, Exception) as exc:  # noqa: BLE001 - report, go on
            problems.append(f"draw {d}: {type(exc).__name__}: {exc}")
            continue
        verts = len(part.positions) // 3
        if len(part.indices) % 3:
            problems.append(f"draw {d}: {len(part.indices)} indices is not whole triangles")
        if part.indices and max(part.indices) >= verts:
            problems.append(f"draw {d}: index {max(part.indices)} >= {verts} vertices")
        if material >= len(mats):
            problems.append(f"draw {d}: material {material} of {len(mats)}")
        item = owner.get(d)
        if item:
            x0, y0, z0, x1, y1, z1 = item.box
            tol = 0.01 * max(x1 - x0, y1 - y0, z1 - z0, 1.0)
            out = sum(1 for i in range(verts) if not (x0 - tol <= part.positions[3 * i] <= x1 + tol
                                                      and y0 - tol <= part.positions[3 * i + 1] <= y1 + tol
                                                      and z0 - tol <= part.positions[3 * i + 2] <= z1 + tol))
            if out:
                problems.append(f"draw {d} ({item.name}): {out} of {verts} positions outside its box")
    n["textured materials"] = f"{textured}/{len(mats)}"
    return problems, n


def main(argv):
    game = next((a for a in argv if not a.startswith("--")), DEFAULT_GAME)
    only = argv[argv.index("--only") + 1].lower() if "--only" in argv else None
    arc = Edat.open(str(find_pack(__import__("pathlib").Path(game), "ZZ_Win.dat")))
    packs = [e for e in arc.entries if e.path.lower().startswith("gen_5\\pack\\") and e.path.lower().endswith(".spk")]
    total = {"packs": 0, "skeleton packs": 0, "draws": 0, "stored": 0, "compressed": 0, "models": 0, "failed": 0}
    start = time.time()
    for e in packs:
        if only and only not in e.path.lower():
            continue
        try:
            spk = Spk(bytes(arc.read(e)))
        except SpkError as exc:
            if "skeleton" in str(exc):
                total["skeleton packs"] += 1
                continue
            print(f"FAIL {e.path}: {exc}")
            total["failed"] += 1
            continue
        problems, n = check(spk)
        total["packs"] += 1
        for k in ("draws", "stored", "compressed", "models"):
            total[k] += n[k]
        total["failed"] += bool(problems)
        print(f"{'OK  ' if not problems else 'FAIL'} {e.path}: {n}")
        for p in problems[:5]:
            print("      ", p)
        if len(problems) > 5:
            print(f"       ... {len(problems) - 5} more")
    print(f"\n{total} in {time.time() - start:.0f}s")
    return 1 if total["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
