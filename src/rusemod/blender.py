"""Finding Blender, and opening game models in it (the Blender bridge; rusemod.gltf, rusemod.blender_open).

Blender is a separate, free program (blender.org); the Studio and `ruse export-model --open` start it with
blender_open.py, which loads the exported models textured and links each texture to its picture file. The Studio's
Bring back asks that Blender to save the paint first (ask_to_save), so no saving is needed in Blender."""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

DOWNLOAD = "https://www.blender.org/download/"
OPENER = Path(__file__).with_name("blender_open.py")
SAVE_REQUEST, SAVE_DONE = "save.request", "save.done"  # files in the models' folder; blender_open.py's names too


def find_blender(chosen: str | None = None) -> Path | None:
    """blender.exe: the one `chosen` (the user's pick, kept in settings), else $RUSE_BLENDER, the PATH, Program
    Files (Blender Foundation), or Steam's Blender; None when none is found."""
    for c in (chosen, os.environ.get("RUSE_BLENDER"), shutil.which("blender")):
        if c and Path(c).is_file():
            return Path(c)
    roots = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramW6432", "")]
    found = []
    for root in filter(None, roots):
        found += glob.glob(os.path.join(root, "Blender Foundation", "*", "blender.exe"))
    if found:
        return Path(sorted(found)[-1])
    try:
        from .steam import libraries, steam_roots
        for root in steam_roots():
            for lib in libraries(root):
                exe = Path(lib) / "steamapps" / "common" / "Blender" / "blender.exe"
                if exe.is_file():
                    return exe
    except Exception:  # noqa: BLE001  (no Steam, or its files unreadable: just not found there)
        pass
    return None


def open_models(blender: Path, files: list) -> subprocess.Popen:
    """Start Blender with these .glb files loaded (blender_open.py); returns at once, with Blender's process."""
    return subprocess.Popen([str(blender), "--python", str(OPENER), "--"] + [str(f) for f in files])


def ask_to_save(folder: Path, timeout: float) -> list | None:
    """Ask the Blender painting the models in `folder` to save its paint, and wait for it: the names of the pictures
    it saved ([] when everything was saved already), or None when no Blender answered within `timeout` seconds
    (it was closed: what it saved before is in the folder)."""
    folder = Path(folder)
    done, request = folder / SAVE_DONE, folder / SAVE_REQUEST
    done.unlink(missing_ok=True)
    request.write_text("save", encoding="utf-8")
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if done.exists():
            try:
                saved = json.loads(done.read_text(encoding="utf-8"))
            except (OSError, ValueError):  # being written: look again
                saved = None
            if isinstance(saved, list):
                done.unlink(missing_ok=True)
                return saved
        time.sleep(0.1)
    request.unlink(missing_ok=True)
    return None
