r"""Verify the reader/writer against the WHOLE game install (READ-ONLY).

For every archive in Data\PC\<rev>\ and Maps\PC\:
  1. the archive rebuilds byte-identically (compared by streamed SHA-1, so 2.4 GB packs need no RAM),
  2. every nested archive (.ipk/.ppk/.apk/.mpk/.gpk...) rebuilds byte-identically,
  3. every NDF binary re-serializes byte-identically at the logical level.
Nothing is written anywhere.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_all.py [game_dir]
"""
import glob
import hashlib
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
CHUNK = 8 << 20


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                return h.hexdigest()
            h.update(b)


def rebuilt_sha1(arc):
    h = hashlib.sha1()
    for chunk in arc.iter_chunks():
        h.update(chunk)
    return h.hexdigest()


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat"))) + \
        sorted(glob.glob(os.path.join(game, "Maps", "PC", "*.dat")))
    if not packs:
        print(f"no archives found under {game}")
        return 2
    t0 = time.time()
    n_arc = n_nested = n_ndf = 0
    failures, empty_nested = [], []
    for path in packs:
        name = os.path.basename(path)
        with Edat.open(path) as arc:
            n_arc += 1
            if rebuilt_sha1(arc) != file_sha1(path):
                failures.append(f"archive {name}")
            for e in arc.entries:
                data = arc.read(e)
                magic = data[:4]
                if magic == b"edat":
                    n_nested += 1
                    try:
                        nested = Edat(data)
                        if nested.to_bytes() != data:
                            failures.append(f"nested {name}:{e.path}")
                        elif not nested.entries:
                            empty_nested.append(f"{name}:{e.path}")
                    except Exception as exc:
                        failures.append(f"nested {name}:{e.path} ({exc})")
                elif magic == b"EUG0" and data[8:12] == b"CNDF":
                    n_ndf += 1
                    try:
                        ndf = Ndf(data)
                        if ndf.to_logical() != ndf.data:
                            failures.append(f"ndf {name}:{e.path}")
                    except Exception as exc:  # parse error = failure, keep going
                        failures.append(f"ndf {name}:{e.path} ({exc})")
        print(f"  checked {name}")
    dt = time.time() - t0
    print(f"\narchives: {n_arc}  nested archives: {n_nested}  NDF files: {n_ndf}  time: {dt:.0f}s")
    if empty_nested:
        print(f"empty nested archives (valid, no files): {len(empty_nested)}, e.g. {empty_nested[0]}")
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures[:20]:
            print("  " + f)
        return 1
    print("ALL BYTE-IDENTICAL: every archive, nested archive and NDF file round-trips exactly.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
