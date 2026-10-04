"""Sending files and folders to the Windows Recycle Bin (not deleting them), so a delete in the apps can be undone
from the bin. Windows' own shell does it (SHFileOperationW with "allow undo"), silently: no dialog of its own."""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

FO_DELETE = 3
FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 0x4, 0x10, 0x40, 0x400


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
        raise OSError("the Recycle Bin is Windows' own: nothing was moved")
    op = _FileOp(None, FO_DELETE, str(path) + "\0\0", None,
                 FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI, False, None, None)
    code = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if code or op.fAnyOperationsAborted or path.exists():
        raise OSError(f"Windows couldn't move {path} to the Recycle Bin (code {code:#x}): close anything that has it "
                      "open, then try again")
