"""Where what people make is kept: their mods, maps, exported files and the backups taken before a mod is updated.

In the apps it's Documents\\RUSE 2.0 (Mods, Maps, Exports, Backups), where File Explorer shows it (the owner,
2026-10-30: the file paths for new mods weren't "very clear or easy to follow"). Before, it was the platform folder
(rusemod.home: %LOCALAPPDATA%\\RUSE Mod Platform, which Windows hides); the Studio moves what's there across the first
time it starts (move_in). A platform folder set by hand ($RUSE_PLATFORM_HOME) keeps everything in it as before, and so
do tests: no Documents folder is touched then.
"""
from __future__ import annotations

import filecmp
import json
import os
import shutil
import sys
import tomllib
from pathlib import Path

FOLDER = "RUSE 2.0"  # in Documents
KINDS = ("mods", "maps", "exports", "backups")
NAMES = {"mods": "Mods", "maps": "Maps", "exports": "Exports", "backups": "Backups"}  # in Documents\RUSE 2.0
OLD_NAMES = {"mods": "mods", "maps": "maps", "exports": "exports", "backups": "mod-backups"}  # in the platform folder


def documents() -> Path | None:
    """The person's Documents folder, where Windows has it (moved to another drive, or to OneDrive, too); elsewhere the
    desktop's (XDG_DOCUMENTS_DIR), else ~/Documents. None when there's none."""
    if sys.platform == "win32":
        found = _known_documents()
        if found is not None:
            return found
    else:
        found = _xdg_documents()
        if found is not None:
            return found
    folder = Path.home() / "Documents"
    return folder if folder.is_dir() else None


def _known_documents() -> Path | None:
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_ubyte * 8)]

    # FOLDERID_Documents, {FDD39AD0-238F-46AF-ADB4-6C85480369C7}
    documents_id = GUID(0xFDD39AD0, 0x238F, 0x46AF, (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7))
    try:
        shell32, ole32 = ctypes.WinDLL("shell32"), ctypes.WinDLL("ole32")
        shell32.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                                                 ctypes.POINTER(ctypes.c_void_p)]
        shell32.SHGetKnownFolderPath.restype = ctypes.c_long
        ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        out = ctypes.c_void_p()
        if shell32.SHGetKnownFolderPath(ctypes.byref(documents_id), 0, None, ctypes.byref(out)) != 0:
            return None
        try:
            path = ctypes.wstring_at(out.value) if out.value else ""
        finally:
            ole32.CoTaskMemFree(out)
    except (OSError, AttributeError):
        return None
    return Path(path) if path and Path(path).is_dir() else None


def _xdg_documents() -> Path | None:
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "user-dirs.dirs"
    try:
        lines = config.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for line in lines:
        if line.startswith("XDG_DOCUMENTS_DIR="):
            value = line.split("=", 1)[1].strip().strip('"').replace("$HOME", str(Path.home()))
            folder = Path(value)
            return folder if folder.is_dir() and folder != Path.home() else None
    return None


def documents_home() -> Path | None:
    """Documents\\RUSE 2.0. None when the platform folder was set by hand ($RUSE_PLATFORM_HOME: everything stays in it)
    or there's no Documents folder (then everything stays in the platform folder too)."""
    if os.environ.get("RUSE_PLATFORM_HOME"):
        return None
    docs = documents()
    return docs / FOLDER if docs is not None else None


def folders(home: Path, work: Path | None) -> dict[str, Path]:
    """Where mods, maps, exports and backups go: {"mods", "maps", "exports", "backups"}. In `work` (Documents\\RUSE 2.0)
    when there is one, else in the platform folder `home` under the names they've always had there."""
    if work is None:
        return {k: Path(home) / OLD_NAMES[k] for k in KINDS}
    return {k: Path(work) / NAMES[k] for k in KINDS}


def old_folders(home: Path, work: Path | None) -> dict[str, Path]:
    """Where they were before (the platform folder's), when that's another place: anything move_in left there is still
    listed from it. {} when there's no `work`."""
    return {} if work is None else {k: Path(home) / OLD_NAMES[k] for k in KINDS}


def move_in(home: Path, work: Path) -> dict:
    """Move what the platform folder `home` holds of mods, maps, exports and backups into `work`, one at a time: renamed
    when it's on the same drive (nothing is copied), else copied, checked byte for byte and only then taken out of the
    old place. One the new place already has by that name, or one that can't be moved (a file of it open in another
    program), stays where it is. The Studio's own record of the mods it was editing and opened (studio.json) and the
    Launcher's mod sets that name a moved folder by its path follow it. Returns {"moved": [new paths], "left": [{"path",
    "why"}], "to": work}."""
    home, work = Path(home), Path(work)
    moved, left, pairs = [], [], []
    for kind in KINDS:
        old, new = home / OLD_NAMES[kind], work / NAMES[kind]
        if not old.is_dir() or _same(old, new):
            continue
        for entry in sorted(old.iterdir()):
            if entry.name.startswith("."):  # one half copied by an earlier try, or the system's own
                continue
            target = new / entry.name
            if target.exists():
                left.append({"path": str(entry), "why": f"{target} is already there"})
                continue
            try:
                _move(entry, target)
            except OSError as exc:
                left.append({"path": str(entry), "why": str(exc)})
                continue
            pairs.append((entry, target))
            moved.append(str(target))
        try:
            old.rmdir()  # only when nothing was left in it
        except OSError:
            pass
    if pairs:
        _follow(home, pairs)
    return {"moved": moved, "left": left, "to": str(work)}


def _same(a: Path, b: Path) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def _move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.rename(src, dst)  # the same drive: nothing copied, so nothing to check
        return
    except OSError:
        pass  # another drive (or something of it open): copied and checked, below
    part = dst.parent / f".moving-{dst.name}"
    _remove(part)
    try:
        if src.is_dir():
            shutil.copytree(src, part)
        else:
            shutil.copy2(src, part)
        if not _identical(src, part):
            raise OSError(f"the copy of {src} didn't match it byte for byte")
        # taken out of the old place by a rename first: it fails while a file of it is open, and then nothing is lost
        gone = src.parent / f".moved-{src.name}"
        _remove(gone)
        os.rename(src, gone)
    except BaseException:
        _remove(part)
        raise
    try:
        os.rename(part, dst)
    except OSError:
        os.rename(gone, src)  # put back as it was
        _remove(part)
        raise
    _remove(gone)


def _identical(a: Path, b: Path) -> bool:
    """Every file of `a` in `b` with the same bytes, and nothing more."""
    if a.is_file():
        return b.is_file() and filecmp.cmp(a, b, shallow=False)
    mine = sorted(p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file())
    theirs = sorted(p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file())
    return mine == theirs and all(filecmp.cmp(a / f, b / f, shallow=False) for f in mine)


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink(missing_ok=True)


def _follow(home: Path, pairs: list[tuple[Path, Path]]) -> None:
    """Paths to a moved folder, in the Studio's studio.json and the Launcher's mod sets, changed to its new place."""
    where = {_key(old): new for old, new in pairs}

    def moved(path: str, base: Path | None = None) -> str:
        p = Path(path)
        if not p.is_absolute():
            if base is None:
                return path
            p = base / p
        new = where.get(_key(p))
        return str(new) if new is not None else path

    file = home / "studio.json"
    try:
        settings = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        settings = None
    if isinstance(settings, dict):
        for k in ("mod", "map"):
            if isinstance(settings.get(k), str):
                settings[k] = moved(settings[k])
        for k in ("recent", "recent_maps"):
            if isinstance(settings.get(k), list):
                settings[k] = [moved(p) if isinstance(p, str) else p for p in settings[k]]
        file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    sets = home / "sets"
    for f in sorted(sets.glob("*.toml")) if sets.is_dir() else []:
        _follow_set(f, lambda entry, base=f.parent: moved(entry, base))


def _key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _follow_set(file: Path, moved) -> None:
    """One mod set's entries that name a moved folder (by its path, written by hand: the Launcher writes library ids)
    changed to the new path, the rest of the file as it was. Left as it was when the result doesn't read back the
    same."""
    try:
        text = file.read_text(encoding="utf-8")
        entries = [m for m in tomllib.loads(text).get("mods", []) if isinstance(m, str)]
    except (OSError, UnicodeDecodeError, ValueError, AttributeError):
        return
    want = [moved(m) for m in entries]
    if want == entries:
        return
    out = text
    for old, new in zip(entries, want):
        if old == new:
            continue
        for written in (json.dumps(old, ensure_ascii=False), json.dumps(old), f"'{old}'"):
            if written in out:
                out = out.replace(written, json.dumps(new, ensure_ascii=False))
                break
    try:
        if [m for m in tomllib.loads(out).get("mods", []) if isinstance(m, str)] != want:
            return
    except ValueError:
        return
    file.write_text(out, encoding="utf-8")
