"""Sending files and folders to the Windows Recycle Bin (not deleting them), so a delete in the apps can be undone
from the bin. Windows' own shell does it (SHFileOperationW with "allow undo"), silently: no dialog of its own.
Elsewhere (Linux, the Steam Deck's desktop) they go to the desktop's trash, which its file manager puts back from."""
from __future__ import annotations

import ctypes
import os
import shutil
import sys
import time
import urllib.parse
from ctypes import wintypes
from pathlib import Path

FO_DELETE = 3
FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 0x4, 0x10, 0x40, 0x400
FOF_WANTNUKEWARNING = 0x4000  # something too big for the bin: Windows asks before deleting it for good, never silently
# (A file another program has open isn't moved: Windows says "the system call level is not correct", code 0x7c.)


class _FileOp(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL),
                ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]


def to_recycle_bin(path: Path) -> None:
    """Move `path` (a file or a folder, with everything in it) to the Recycle Bin. OSError when it can't be."""
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"{path} isn't there")
    if sys.platform != "win32":
        _to_trash(path)
        return
    op = _FileOp(None, FO_DELETE, str(path) + "\0\0", None,
                 FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_WANTNUKEWARNING | FOF_SILENT | FOF_NOERRORUI, False, None,
                 None)
    code = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if code or op.fAnyOperationsAborted or path.exists():
        raise OSError(f"Windows couldn't move {path} to the Recycle Bin (code {code:#x}): close anything that has it "
                      "open, then try again")


def _to_trash(path: Path) -> None:
    """The desktop's trash: on Linux freedesktop.org's (files/ and info/ in $XDG_DATA_HOME/Trash, the info file saying
    where it was, so the file manager can put it back), on a Mac ~/.Trash."""
    if sys.platform == "darwin":
        bin_ = Path.home() / ".Trash"
        bin_.mkdir(exist_ok=True)
        shutil.move(str(path), str(_free(bin_, path.name)))
        return
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "Trash"
    files, info = base / "files", base / "info"
    files.mkdir(parents=True, exist_ok=True)
    info.mkdir(parents=True, exist_ok=True)
    name, n = path.name, 1
    while True:  # the info file is made first, so two trashed things of one name never take the same place
        try:
            fd = os.open(info / f"{name}.trashinfo", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            break
        except FileExistsError:
            n += 1
            name = f"{path.stem}.{n}{path.suffix}"
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(f"[Trash Info]\nPath={urllib.parse.quote(str(path))}\n"
                f"DeletionDate={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    try:
        shutil.move(str(path), str(files / name))
    except OSError:
        (info / f"{name}.trashinfo").unlink(missing_ok=True)
        raise


def _free(folder: Path, name: str) -> Path:
    """`name` in `folder`, or name 2, name 3... when it's taken."""
    stem, suffix = Path(name).stem, Path(name).suffix
    out, n = folder / name, 1
    while out.exists():
        n += 1
        out = folder / f"{stem} {n}{suffix}"
    return out
