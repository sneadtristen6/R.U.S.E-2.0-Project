r"""Verify the gameplay-ground reader/writer (rusemod.kdt) against every map pack (READ-ONLY on the game).

For output\occlusioninfo_terrainonly.kdt and output\occlusioninfo_camera.kdt of every Maps\PC\DataMap*_v09.dat:
  A. the file parses and rebuilds byte-identically (every table, the padding and the offset properties recomputed),
  B. every subtree's positions and normals decode, and re-encoding them reproduces the shipped inflated chunks
     (positions up to the end of the parent codes: the bytes after them are memory junk with no meaning).
One line per file with the subtree, vertex and triangle counts and OK/FAIL, then a summary. Nothing is written.

Usage:  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_kdt.py [game_dir] [--only Name]
"""
import glob
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod.kdt import MEMBERS, Kdt, encode_normals, encode_positions, inflate  # noqa: E402
from rusemod.tms import encode_parents  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def check(raw: bytes) -> tuple[list[str], int, int]:
    """Problems found in one file (empty = OK), its subtree count and its vertex count."""
    problems = []
    k = Kdt(raw)
    if k.to_bytes() != raw:
        problems.append("rebuild differs")
    verts = 0
    for s, t in enumerate(k.subtrees):
        try:
            data = inflate(t.positions)
            pos, par = k.positions(s), k.parents(s)
            verts += len(pos)
            meaningful = 8 + 6 * len(pos) + len(encode_parents(par))
            if encode_positions(pos, par)[:meaningful] != data[:meaningful]:
                problems.append(f"subtree {s}: positions re-encode differently")
            nrm = inflate(t.normals)
            if encode_normals(k.normals(s)) != nrm:
                problems.append(f"subtree {s}: normals re-encode differently")
        except (ValueError, struct.error, zlib.error) as exc:
            problems.append(f"subtree {s}: {exc}")
    return problems, len(k.subtrees), verts


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = argv[i + 1]
        del argv[i:i + 2]
    game = argv[0] if argv else DEFAULT_GAME
    paths = sorted(glob.glob(os.path.join(game, "Maps", "PC", "DataMap*_v09.dat")))
    if only:
        paths = [p for p in paths if os.path.basename(p) == f"DataMap{only}_v09.dat"]
    if not paths:
        print(f"no map packs found under {game}")
        return 2
    files = fails = 0
    for path in paths:
        name = os.path.basename(path)[7:-8]
        with Edat.open(path) as arc:
            for which, member in MEMBERS.items():
                entry = arc.find(member)
                if entry is None:
                    print(f"{name:24s} {which:7s} MISSING")
                    fails += 1
                    continue
                files += 1
                try:
                    problems, subtrees, verts = check(arc.read(entry))
                    line = f"subtrees {subtrees:4d}  vertices {verts:8,d}"
                except (ValueError, struct.error, zlib.error) as exc:
                    problems, line = [str(exc)], "parse error"
                fails += bool(problems)
                print(f"{name:24s} {which:7s} {line}  {'OK' if not problems else 'FAIL: ' + '; '.join(problems[:3])}",
                      flush=True)
    print(f"\n{len(paths)} packs, {files} files, {fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
