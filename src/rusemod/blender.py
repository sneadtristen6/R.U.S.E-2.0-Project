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
    Files (Blender Foundation), Steam's Blender, or a portable one (the zip from blender.org unpacked anywhere
    usual: portable_blenders); None when none is found."""
    for c in (chosen, os.environ.get("RUSE_BLENDER"), shutil.which("blender")):
        if c and Path(c).is_file():
            return Path(c)
    roots = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramW6432", "")]
    found = []
    for root in filter(None, roots):
        found += glob.glob(os.path.join(root, "Blender Foundation", "*", "blender.exe"))
    if found:
        return newest(found)
    try:
        from .steam import libraries, steam_roots
        for root in steam_roots():
            for lib in libraries(root):
                exe = Path(lib) / "steamapps" / "common" / "Blender" / "blender.exe"
                if exe.is_file():
                    return exe
    except Exception:  # noqa: BLE001  (no Steam, or its files unreadable: just not found there)
        pass
    portable = portable_blenders()
    return newest(portable) if portable else None


def _drives() -> list[str]:
    """The PC's local hard drives ("C:\\", "D:\\"...): no network, CD or removable drive (they can be slow)."""
    if os.name != "nt":
        return []
    import ctypes
    import string
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    drives = [f"{d}:\\" for i, d in enumerate(string.ascii_uppercase) if mask >> i & 1]
    return [d for d in drives if ctypes.windll.kernel32.GetDriveTypeW(d) == 3]  # DRIVE_FIXED


def portable_blenders() -> list[Path]:
    """Blenders unpacked from blender.org's zip (no installer, so in no list): a blender* folder holding blender.exe
    at the top of a local drive or one folder down (D:\\Tools\\blender-4.5.14-windows-x64, the owner's), or in the
    user's Downloads, Desktop or Documents (or one folder down there)."""
    places = list(_drives())
    home = Path.home()
    places += [str(home / sub) for sub in ("Downloads", "Desktop", "Documents")]
    found: list[Path] = []
    for top in places:
        for pattern in (os.path.join(top, "blender*", "blender.exe"), os.path.join(top, "*", "blender*", "blender.exe")):
            found += [Path(p) for p in glob.glob(pattern)]
    return sorted(set(found))


def newest(paths) -> Path:
    """The Blender with the highest version in its folder's name (blender-4.5.14-windows-x64 over 4.2.3)."""
    import re

    def version(p) -> tuple:
        m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", Path(p).parent.name)
        return tuple(int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return Path(max(paths, key=lambda p: (version(p), str(p))))


def open_models(blender: Path, files: list) -> subprocess.Popen:
    """Start Blender with these .glb files loaded (blender_open.py); returns at once, with Blender's process."""
    return subprocess.Popen([str(blender), "--python", str(OPENER), "--"] + [str(f) for f in files])


MENU_SCENE = Path(__file__).with_name("blender_menu.py")


def open_menu_scene(blender: Path, folder: Path) -> subprocess.Popen:
    """Start Blender on a map's menu-picture scene in `folder` (blender_menu.py, rusemod.menuscene): its scene.blend
    as it was left, else a new scene made from its scene.json; returns at once, with Blender's process."""
    folder = Path(folder)
    blend = folder / "scene.blend"
    return subprocess.Popen([str(blender)] + ([str(blend)] if blend.is_file() else [])
                            + ["--python", str(MENU_SCENE), "--", str(folder / "scene.json")])


def ask_to_save(folder: Path, timeout: float) -> list | None:
    """Ask the Blender painting the models in `folder` to save its paint, and wait for it: the names of the pictures
    it saved ([] when everything was saved already), or None when no Blender answered within `timeout` seconds
    (it was closed: what it saved before is in the folder)."""
    folder = Path(folder)
    done, request = folder / SAVE_DONE, folder / SAVE_REQUEST
    done.unlink(missing_ok=True)
    part = folder / (SAVE_REQUEST + ".part")  # written beside it, then put in place: Blender never sees it half made
    part.write_text("save", encoding="utf-8")  # (on Windows a file still open can't be deleted, so its answer failed)
    os.replace(part, request)
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
