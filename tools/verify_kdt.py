r"""Verify the gameplay-ground reader/writer (rusemod.kdt) against every map pack (READ-ONLY on the game).

For output\occlusioninfo_terrainonly.kdt and output\occlusioninfo_camera.kdt of every Maps\PC\DataMap*_v09.dat:
  A. the file parses and rebuilds byte-identically (every table, the padding and the offset properties recomputed),
  B. every subtree's positions and normals decode, and re-encoding them reproduces the shipped inflated chunks
     (positions up to the end of the parent codes: the bytes after them are memory junk with no meaning),
  C. every index buffer, k-d tree and triangle list decodes and re-encodes to the shipped inflated bytes; every
     vertex number fits its subtree, every listed triangle exists and touches its leaf's cell; the MainNode
     re-encodes and reaches every subtree exactly once; TriangleCount = the distinct triangles by vertex positions.
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
from rusemod.kdt import (MEMBERS, Kdt, decode_indices, decode_main_node, decode_tree, decode_trilists,  # noqa: E402
                         encode_indices, encode_main_node, encode_normals, encode_positions, encode_tree,
                         encode_trilists, inflate, leaves, main_regions)
from rusemod.tms import encode_parents  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def check(raw: bytes) -> tuple[list[str], int, int]:
    """Problems found in one file (empty = OK), its subtree count and its vertex count."""
    problems = []
    k = Kdt(raw)
    if k.to_bytes() != raw:
        problems.append("rebuild differs")
    verts = 0
    distinct: set = set()
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
            problems += parts(k, s, pos, distinct)
        except (ValueError, struct.error, zlib.error, IndexError) as exc:
            problems.append(f"subtree {s}: {exc}")
    try:
        entries = decode_main_node(k.main_node)
        if encode_main_node(entries) != k.main_node:
            problems.append("MainNode re-encodes differently")
        if sorted(main_regions(entries)) != list(range(len(k.subtrees))):
            problems.append("MainNode doesn't reach every subtree exactly once")
    except (ValueError, struct.error, IndexError) as exc:
        problems.append(f"MainNode: {exc}")
    if len(distinct) != k.triangle_count:
        problems.append(f"TriangleCount {k.triangle_count}, distinct triangles {len(distinct)}")
    return problems, len(k.subtrees), verts


def parts(k: Kdt, s: int, pos: list, distinct: set) -> list[str]:
    """Part C for subtree `s`: index buffer, tree and triangle lists."""
    t, problems = k.subtrees[s], []
    raw = inflate(t.indices)
    idx = decode_indices(raw, t.index_count)
    if encode_indices(idx) != raw:
        problems.append(f"subtree {s}: index buffer re-encodes differently")
    if t.index_count % 3 or any(not 0 <= v < len(pos) for v in idx):
        problems.append(f"subtree {s}: a vertex number outside the subtree")
        return problems
    tris = [idx[i:i + 3] for i in range(0, len(idx), 3)]
    for tri in tris:
        distinct.add(tuple(sorted(pos[v] for v in tri)))
    raw = inflate(t.tree)
    root = decode_tree(raw)
    if encode_tree(root) != raw:
        problems.append(f"subtree {s}: tree re-encodes differently")
    found = leaves(root)
    raw = inflate(t.trilist)
    lists = decode_trilists(raw, [leaf.count for leaf, _, _ in found])
    if encode_trilists(lists) != raw:
        problems.append(f"subtree {s}: triangle lists re-encode differently")
    away = 0
    for (_, lo, hi), lst in zip(found, lists):
        for n in lst:
            if not 0 <= n < len(tris):
                problems.append(f"subtree {s}: a listed triangle doesn't exist")
                return problems
            ps = [pos[v] for v in tris[n]]
            away += any((lo[a] is not None and max(p[a] for p in ps) < lo[a]) or
                        (hi[a] is not None and min(p[a] for p in ps) > hi[a]) for a in range(3))
    if away:
        problems.append(f"subtree {s}: {away} listed triangle(s) don't touch their leaf's cell")
    return problems


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
