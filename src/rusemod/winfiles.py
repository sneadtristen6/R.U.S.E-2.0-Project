"""Windows file and process helpers for modded copies: who holds a file, what runs from a folder, and deleting what an
ordinary delete can't. Plain Windows calls through ctypes; elsewhere each one does nothing and says so.

Checked on Windows 11, NTFS, 2026-09-30 (a player's "Access is denied" on every second Test in game):
- a file marked read-only can't be deleted, nor can a running program's own file. A file a process keeps mapped into
  memory can't be deleted the old way either (volumes without POSIX delete). Renaming the file or its folder still
  works in all three cases; an open handle or a process's current folder inside it stops a folder rename;
- a POSIX delete that ignores the read-only mark (FileDispositionInfoEx) removes the read-only and the mapped cases,
  and leaves a hard link's other names and their mark as they were;
- the processes using a file are named by NtQueryInformationFile (FileProcessIdsUsingFileInformation), mapping-only
  holders too, which the Restart Manager misses."""
from __future__ import annotations

import os
import sys

WINDOWS = sys.platform == "win32"

if WINDOWS:
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")
    _psapi = ctypes.WinDLL("psapi", use_last_error=True)
    _INVALID = wintypes.HANDLE(-1).value
    _k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                 wintypes.DWORD, wintypes.HANDLE]
    _k32.CreateFileW.restype = wintypes.HANDLE
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.CloseHandle.restype = wintypes.BOOL
    _k32.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    _k32.SetFileInformationByHandle.restype = wintypes.BOOL
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]
    _k32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    _k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _k32.TerminateProcess.restype = wintypes.BOOL
    _k32.GetVolumeInformationW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
                                           ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
                                           ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD]
    _k32.GetVolumeInformationW.restype = wintypes.BOOL
    _psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    _psapi.EnumProcesses.restype = wintypes.BOOL

    class _IoStatus(ctypes.Structure):
        _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_size_t)]

    _ntdll.NtQueryInformationFile.argtypes = [wintypes.HANDLE, ctypes.POINTER(_IoStatus), wintypes.LPVOID,
                                              wintypes.ULONG, ctypes.c_int]
    _ntdll.NtQueryInformationFile.restype = ctypes.c_long

_DELETE, _READ_ATTRIBUTES, _SYNCHRONIZE = 0x00010000, 0x80, 0x00100000
_SHARE_ALL = 1 | 2 | 4
_OPEN_EXISTING = 3
_BACKUP_SEMANTICS, _OPEN_REPARSE_POINT = 0x02000000, 0x00200000
_DISPOSITION_EX = 21                                   # FileDispositionInfoEx
_DELETE_POSIX_IGNORE_READONLY = 0x1 | 0x2 | 0x10        # DELETE | POSIX_SEMANTICS | IGNORE_READONLY_ATTRIBUTE
_PROCESS_IDS_USING_FILE = 47                           # FileProcessIdsUsingFileInformation
_QUERY_LIMITED, _TERMINATE = 0x1000, 0x0001
_POSIX_UNLINK_RENAME = 0x400                           # a volume's FILE_SUPPORTS_POSIX_UNLINK_RENAME


def _open(path: str, access: int, flags: int = _BACKUP_SEMANTICS):
    h = _k32.CreateFileW(path, access, _SHARE_ALL, None, _OPEN_EXISTING, flags, None)
    if h == _INVALID or h is None:
        err = ctypes.get_last_error()
        raise OSError(0, ctypes.FormatError(err).strip(), path, err)
    return h


def posix_delete(path: str) -> None:
    """Delete one file (or empty folder) even if it's marked read-only or mapped into memory: its name goes at once, as
    on Linux. A hard link's other names, and their read-only mark, stay as they were. Raises OSError (with winerror)
    when Windows refuses, a running program's own file above all."""
    if not WINDOWS:
        os.remove(path)
        return
    h = _open(path, _DELETE | _READ_ATTRIBUTES | _SYNCHRONIZE, _BACKUP_SEMANTICS | _OPEN_REPARSE_POINT)
    try:
        flags = wintypes.DWORD(_DELETE_POSIX_IGNORE_READONLY)
        if not _k32.SetFileInformationByHandle(h, _DISPOSITION_EX, ctypes.byref(flags), ctypes.sizeof(flags)):
            err = ctypes.get_last_error()
            raise OSError(0, ctypes.FormatError(err).strip(), path, err)
    finally:
        _k32.CloseHandle(h)


def process_path(pid: int) -> str | None:
    """A running process's program file, or None when it can't be read."""
    if not WINDOWS:
        return None
    h = _k32.OpenProcess(_QUERY_LIMITED, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buf))
        return buf.value if _k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) else None
    finally:
        _k32.CloseHandle(h)


def holders(path: str) -> list[tuple[int, str | None]]:
    """[(process id, its program file)] of the processes using `path` (open, mapped into memory, or running it)."""
    if not WINDOWS:
        return []
    try:
        h = _open(path, _READ_ATTRIBUTES)
    except OSError:
        return []
    try:
        buf = ctypes.create_string_buffer(8 + 8 * 256)
        status = _IoStatus()
        if _ntdll.NtQueryInformationFile(h, ctypes.byref(status), buf, len(buf), _PROCESS_IDS_USING_FILE) < 0:
            return []
        n = min(ctypes.c_ulong.from_buffer(buf, 0).value, 256)
        pids = [ctypes.c_size_t.from_buffer(buf, 8 + 8 * i).value for i in range(n)]
    finally:
        _k32.CloseHandle(h)
    return [(pid, process_path(pid)) for pid in pids if pid != os.getpid()]


def processes() -> list[tuple[int, str]]:
    """[(process id, program file)] of every running process whose program file can be read."""
    if not WINDOWS:
        return []
    size = 4096
    while True:
        ids = (wintypes.DWORD * size)()
        got = wintypes.DWORD()
        if not _psapi.EnumProcesses(ids, ctypes.sizeof(ids), ctypes.byref(got)):
            return []
        n = got.value // ctypes.sizeof(wintypes.DWORD)
        if n < size:
            break
        size *= 2
    out = []
    for pid in ids[:n]:
        exe = process_path(pid) if pid else None
        if exe:
            out.append((pid, exe))
    return out


def inside(path: str, folder: str) -> bool:
    """Whether `path` is `folder` or anything in it (case and separators as Windows compares them)."""
    p, f = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(folder))
    return p == f or p.startswith(f.rstrip("\\/") + os.sep)


def running_from(folder: str) -> list[tuple[int, str]]:
    """[(process id, program file)] of the processes whose program file is in `folder` (a modded copy's game, or its
    crash reporter, still running from it)."""
    return [(pid, exe) for pid, exe in processes() if inside(exe, folder)]


def close(pid: int) -> bool:
    """End a process (a game left running from a modded copy). True when Windows did."""
    if not WINDOWS:
        return False
    h = _k32.OpenProcess(_TERMINATE, False, pid)
    if not h:
        return False
    try:
        return bool(_k32.TerminateProcess(h, 1))
    finally:
        _k32.CloseHandle(h)


def volume(path: str) -> dict:
    """{"fs": the file system's name ("NTFS", "exFAT", ...), "posix_delete": whether it deletes the POSIX way} for the
    drive `path` is on; {} when it can't be read."""
    if not WINDOWS:
        return {}
    root = os.path.splitdrive(os.path.abspath(path))[0] + "\\"
    fs = ctypes.create_unicode_buffer(64)
    flags, most, serial = wintypes.DWORD(), wintypes.DWORD(), wintypes.DWORD()
    if not _k32.GetVolumeInformationW(root, None, 0, ctypes.byref(serial), ctypes.byref(most), ctypes.byref(flags),
                                      fs, len(fs)):
        return {}
    return {"fs": fs.value, "posix_delete": bool(flags.value & _POSIX_UNLINK_RENAME)}
