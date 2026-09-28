"""Modded instances: a launchable copy of the game that never touches the Steam install (PLAN L4, proven by C2).

Layout of an instance:
  - every `.dat` archive is a HARD LINK to the original (free, same drive, read-only use by the game); on a drive
    that can't share files with the game, a full copy instead (counted as "full copies");
  - every other file is a real COPY (the game may rewrite configs/logs without reaching the install);
  - replaced files are written fresh (never through a hard link, which would change the original);
  - `steam_appid.txt` lets RUSE.exe start from the copy with Steam running.
The instance is built in `<dst>.partial` and only then swapped in, so a half-built instance never looks usable and the
last working one stays until the new one is complete.
"""
from __future__ import annotations

import os
import shutil

STEAM_APPID = "21970"


def _norm(rel: str) -> str:
    return os.path.normcase(os.path.normpath(rel))


def build_instance(src: str, dst: str, replace: dict | None = None,
                   rename: dict[str, str] | None = None, appid: str = STEAM_APPID) -> dict[str, int]:
    """Build an instance of the game folder `src` at `dst`. Returns counts of linked/copied/written files.

    replace: relative path -> new content: bytes, or a function that writes it to an open file (for multi-GB packs,
             e.g. `lambda f: arc.write_to(f, changed)`), written as an independent file.
    rename:  relative path -> new relative path (the file appears only under the new name; content untouched).
    """
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if _norm(dst) == _norm(src) or _norm(dst).startswith(_norm(src) + os.sep):
        raise ValueError("refusing to build an instance inside the game folder")
    replace = {_norm(k): v for k, v in (replace or {}).items()}
    rename = {_norm(k): v for k, v in (rename or {}).items()}
    staging, old = dst + ".partial", dst + ".old"
    if os.path.exists(staging):
        shutil.rmtree(staging)  # a build that stopped halfway; removing hard links never affects the originals

    counts = {"linked": 0, "copied": 0, "written": 0}
    seen = set()
    try:
        for root, _dirs, files in os.walk(src):
            for fn in files:
                src_f = os.path.join(root, fn)
                rel = os.path.relpath(src_f, src)
                key = _norm(rel)
                out = os.path.join(staging, rename.get(key, rel))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                if key in replace:
                    with open(out, "wb") as f:
                        content = replace[key]
                        content(f) if callable(content) else f.write(content)
                    counts["written"] += 1
                    seen.add(key)
                elif fn.lower().endswith(".dat"):
                    try:
                        os.link(src_f, out)
                        counts["linked"] += 1
                    except OSError:  # another drive (or a file system without hard links): a full copy
                        shutil.copy2(src_f, out)
                        counts["full copies"] = counts.get("full copies", 0) + 1
                else:
                    shutil.copy2(src_f, out)
                    counts["copied"] += 1
        missing = set(replace) - seen
        if missing:
            raise FileNotFoundError(f"files to replace not found in the game folder: {sorted(missing)}")
        with open(os.path.join(staging, "steam_appid.txt"), "w") as f:
            f.write(appid)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if os.path.exists(old):
        shutil.rmtree(old)
    if os.path.exists(dst):
        os.replace(dst, old)
    os.replace(staging, dst)
    shutil.rmtree(old, ignore_errors=True)
    return counts
