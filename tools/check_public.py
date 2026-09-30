"""Keep the public repo public-safe (PLAN.md §10 "Two repos"; the owner's rule: sensitive files stay in the private
shared repo). Fails when a tracked file is something that belongs only there:

- the private folder, the research handover, the community mods (`private/`, `*handover*`, `mods/`);
- game files or data taken out of the game (packs, NDF, texts, textures, meshes, scenery, scripts; `.rmod` mods);
- details of the game's program: code addresses (`FUN_14xxxxxx`, `0x14xxxxxxx`) or disassembly-tool notes.

    py -3 tools/check_public.py            # the files git tracks here
    py -3 tools/check_public.py FILE ...   # just these (a pre-commit check)

GitHub runs it on every push and pull request (.github/workflows/tests.yml). The sync to the private repo only ever
goes one way (public -> private, .github/workflows/sync-private.yml), so nothing private comes back through it.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = ("private/", "mods/", "extracted/")
PRIVATE_NAMES = re.compile(r"handover", re.I)
GAME_FILES = {".dat", ".ndfbin", ".gladndfbin", ".dic", ".tgv", ".tgv_pc", ".spk", ".spkpc", ".ppk", ".ipk", ".xyz",
              ".boobspc", ".kdt", ".tms", ".tmst", ".tmst_pc", ".tmst_chunk_pc", ".scenario", ".ess", ".win", ".sdb",
              ".rmod", ".ase2ndfbin", ".exe", ".dll", ".pdb", ".idb", ".i64", ".gzf"}
PROGRAM = re.compile(r"\bFUN_[0-9A-Fa-f]{6,}\b|\b0x14[0-9A-Fa-f]{7}\b|\bsub_14[0-9A-Fa-f]{7}\b")
# where the words may appear on purpose: this check itself, and code that must refuse such files
ALLOWED = {"tools/check_public.py", "tests/test_check_public.py"}
TEXT_LIMIT = 4_000_000


def problems(paths: list[str], read=lambda p: (ROOT / p).read_bytes()) -> list[str]:
    out = []
    for path in paths:
        p = path.replace("\\", "/")
        low = p.lower()
        if p in ALLOWED:
            continue
        if low.startswith(PRIVATE_DIRS) or any(f"/{d}" in f"/{low}" for d in PRIVATE_DIRS[:1]):
            out.append(f"{p}: private material belongs in the private shared repo")
            continue
        if PRIVATE_NAMES.search(PurePosixPath(low).name):
            out.append(f"{p}: the research handover stays in the private repo")
            continue
        suffix = PurePosixPath(low).suffix
        if suffix in GAME_FILES and not low.startswith("tests/"):
            out.append(f"{p}: a game file (or one made from the game's), never stored here")
            continue
        try:
            data = read(p)
        except OSError:
            continue
        if len(data) > TEXT_LIMIT or b"\0" in data[:8192]:
            continue
        m = PROGRAM.search(data.decode("utf-8", "replace"))
        if m:
            out.append(f"{p}: names a place in the game's program ({m.group(0)}); program details stay private")
    return out


def main(argv: list[str]) -> int:
    paths = argv or subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                                   check=True).stdout.splitlines()
    found = problems(paths)
    for line in found:
        print(line)
    print(f"{len(paths)} file(s) checked, {len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
