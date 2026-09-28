"""Modded instances: a launchable copy of the game that never touches the Steam install (PLAN L4, proven by C2).

Layout of an instance:
  - every `.dat` archive is a HARD LINK to the original (free, same drive, read-only use by the game);
  - every other file is a real COPY (the game may rewrite configs/logs without reaching the install);
  - replaced files are written fresh (never through a hard link, which would change the original);
  - `steam_appid.txt` lets RUSE.exe start from the copy with Steam running.
The instance is built in `<dst>.partial` and renamed at the end, so a half-built instance never looks usable.
"""
from __future__ import annotations

import os
import shutil

STEAM_APPID = "21970"


def _norm(rel: str) -> str:
    return os.path.normcase(os.path.normpath(rel))


def build_instance(src: str, dst: str, replace: dict[str, bytes] | None = None,
                   rename: dict[str, str] | None = None, appid: str = STEAM_APPID) -> dict[str, int]:
    """Build an instance of the game folder `src` at `dst`. Returns counts of linked/copied/written files.

    replace: relative path -> new file content (written as an independent file).
    rename:  relative path -> new relative path (the file appears only under the new name; content untouched).
    """
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if _norm(dst) == _norm(src) or _norm(dst).startswith(_norm(src) + os.sep):
        raise ValueError("refusing to build an instance inside the game folder")
    replace = {_norm(k): v for k, v in (replace or {}).items()}
    rename = {_norm(k): v for k, v in (rename or {}).items()}
    staging = dst + ".partial"
    for d in (staging, dst):
        if os.path.exists(d):
            shutil.rmtree(d)  # removing hard links never affects the originals

    counts = {"linked": 0, "copied": 0, "written": 0}
    seen = set()
    for root, _dirs, files in os.walk(src):
        for fn in files:
            src_f = os.path.join(root, fn)
            rel = os.path.relpath(src_f, src)
            key = _norm(rel)
            out_rel = rename.get(key, rel)
            out = os.path.join(staging, out_rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            if key in replace:
                with open(out, "wb") as f:
                    f.write(replace[key])
                counts["written"] += 1
                seen.add(key)
            elif fn.lower().endswith(".dat"):
                os.link(src_f, out)
                counts["linked"] += 1
            else:
                shutil.copy2(src_f, out)
                counts["copied"] += 1
    missing = set(replace) - seen
    if missing:
        shutil.rmtree(staging)
        raise FileNotFoundError(f"files to replace not found in the game folder: {sorted(missing)}")
    with open(os.path.join(staging, "steam_appid.txt"), "w") as f:
        f.write(appid)
    os.replace(staging, dst)
    return counts
