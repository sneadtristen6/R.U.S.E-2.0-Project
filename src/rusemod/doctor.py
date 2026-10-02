"""The troubleshooter, for both apps: what can stop Test in game or Play, checked in one go, each finding with what to do
about it (a player's report, 2026-09-30: "Access is denied" on every second test, from a leftover copy Windows wouldn't
delete). It only reads, apart from a test file it writes and removes in the copies' folder, and the two fixes a player
can ask for: closing a R.U.S.E. left running from a modded copy, and clearing leftover copies. The game's own folder is
never changed.

A finding is {"key": what's checked, "level": "ok" | "info" | "warn" | "fail", "say": the apps' word for it (each app's
words.toml, filled with `data`), "data": {...}, "fix": an action the app can run (`fix`) or None}."""
from __future__ import annotations

import os
import shutil
import stat
import time
from pathlib import Path

from . import winfiles

GAME_PROGRAMS = ("ruse.exe", "crashsender")  # the game, and its crash reporter (CrashSender.Release.x64.exe)
LINKED_ROOM = 4 << 30  # free space a copy needs on the game's NTFS drive: most packs are shared, a few written anew
BUILDING = 10 * 60  # a half-built copy changed this recently (seconds) may still be building in the other app


def _finding(key: str, level: str, say: str, fix: str | None = None, **data) -> dict:
    return {"key": key, "level": level, "say": say, "data": data, "fix": fix}


def _names(procs) -> str:
    return ", ".join(f"{os.path.basename(exe)} ({pid})" for pid, exe in procs)


def _game_program(exe: str) -> bool:
    return os.path.basename(exe).lower().startswith(GAME_PROGRAMS)


def _leftovers(instances: Path) -> list[Path]:
    """The copies a build left behind: half-built (.partial), old (.old), and what waits in the trash."""
    from .instance import TRASH
    if not instances.is_dir():
        return []
    out = sorted(p for p in instances.iterdir() if p.is_dir() and p.name.endswith((".old", ".partial")))
    trash = instances / TRASH
    return out + (sorted(trash.iterdir()) if trash.is_dir() else [])


def _held(folder: Path) -> list[tuple[int, str]]:
    """The programs holding the packs and programs of a copy (the files a build can't remove)."""
    seen = {}
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.lower().endswith((".dat", ".exe", ".dll")):
                for pid, exe in winfiles.holders(os.path.join(root, name)):
                    seen[pid] = exe or "?"
    return sorted(seen.items())


def _size(folder: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(folder):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def _existing(path: Path) -> Path:
    while not path.exists() and path.parent != path:
        path = path.parent
    return path


def _locked(game: Path) -> int:
    """How many of the game's files are marked read-only (a file that can't be read is skipped, not a crash)."""
    n = 0
    for root, _dirs, files in os.walk(game):
        for name in files:
            try:
                n += not os.stat(os.path.join(root, name)).st_mode & stat.S_IWRITE
            except OSError:
                pass
    return n


def _building(folder: Path, now: float | None = None) -> bool:
    """A half-built copy that changed in the last BUILDING seconds: the other app (the Studio's Test in game, the
    Launcher's Play) may be building it right now, and clearing it would pull files out from under that build."""
    if not folder.name.endswith(".partial"):
        return False
    now = time.time() if now is None else now
    for root, _dirs, _files in os.walk(folder):
        try:
            if now - os.stat(root).st_mtime < BUILDING:
                return True
        except OSError:
            pass
    return False


def _write_test(instances: Path) -> None:
    """Write and remove a file where modded copies go, leaving nothing behind: a folder made for the test (no copy
    built yet) is removed again. Raises OSError when Windows refuses."""
    made = []
    try:
        for folder in reversed([instances, *instances.parents]):
            if not folder.exists():
                folder.mkdir()
                made.append(folder)
        probe = instances / f".write-test-{os.getpid()}"
        probe.write_bytes(b"ok")
        probe.unlink()
    finally:
        for folder in reversed(made):
            try:
                folder.rmdir()
            except OSError:
                pass


def checks(game: Path | None, instances: Path | None, steam_running=None, processes=None) -> list[dict]:
    """Every finding, in the order a player would fix them; without `instances` (no game found yet, so no place for
    modded copies) the copies' own checks are left out. `steam_running` and `processes` stand in for the real world
    in tests."""
    from .play import steam_running as real_steam
    out = []
    found = game is not None and any(p.name.lower() == "ruse.exe" for p in game.iterdir()) if game and game.is_dir() \
        else False
    out.append(_finding("game", "ok", "doc_game_ok", path=str(game)) if found
               else _finding("game", "fail", "doc_game_missing", "choose_game"))
    out.append(_finding("steam", "ok", "doc_steam_ok") if (steam_running or real_steam)()
               else _finding("steam", "info", "doc_steam_off"))

    procs = (processes or winfiles.processes)()
    from_copies = [(pid, exe) for pid, exe in procs if instances is not None and winfiles.inside(exe, str(instances))]
    elsewhere = [(pid, exe) for pid, exe in procs if _game_program(exe) and (pid, exe) not in from_copies]
    if from_copies:
        out.append(_finding("running", "warn", "doc_running_copy", "close_game", names=_names(from_copies)))
    elif elsewhere:
        out.append(_finding("running", "info", "doc_running_game", names=_names(elsewhere)))
    else:
        out.append(_finding("running", "ok", "doc_running_none"))
    if instances is None:
        return out

    where = _existing(instances)
    vol = winfiles.volume(str(where))
    fs = vol.get("fs", "")
    same = found and Path(game).anchor.lower() == instances.anchor.lower()
    if fs and fs.upper() != "NTFS":
        out.append(_finding("drive", "warn", "doc_drive_other", path=str(instances), fs=fs))
    else:
        out.append(_finding("drive", "ok", "doc_drive_ok", path=str(instances), fs=fs or "?"))
    try:
        free = shutil.disk_usage(where).free
    except OSError:
        free = None
    if free is not None:
        need = LINKED_ROOM if same and (not fs or fs.upper() == "NTFS") else (_size(game) if found else LINKED_ROOM)
        gb = round(free / (1 << 30), 1)
        out.append(_finding("space", "ok", "doc_space_ok", gb=gb) if free >= need
                   else _finding("space", "warn", "doc_space_low", gb=gb, need=round(need / (1 << 30), 1)))

    left = _leftovers(instances)
    if not left:
        out.append(_finding("leftovers", "ok", "doc_left_none"))
    else:
        held = sorted({p for folder in left for p in _held(folder)})
        names = ", ".join(p.name if p.parent == instances else f"{p.parent.name}\\{p.name}" for p in left)
        if held:
            out.append(_finding("leftovers", "warn", "doc_left_held", "clear_leftovers", names=names,
                                held=_names(held)))
        else:
            out.append(_finding("leftovers", "info", "doc_left", "clear_leftovers", names=names))

    if found:
        locked = _locked(game)
        if locked:
            out.append(_finding("readonly", "info", "doc_readonly", n=locked))

    try:
        _write_test(instances)
        out.append(_finding("write", "ok", "doc_write_ok", path=str(instances)))
    except OSError as exc:
        out.append(_finding("write", "fail", "doc_write_fail", path=str(instances), why=exc.strerror or str(exc)))
    return out


def fix(action: str, game: Path | None, instances: Path) -> dict:
    """Run one of the findings' fixes: "close_game" ends what runs from the modded copies (never anything else);
    "clear_leftovers" removes leftover copies, or moves them into the trash when Windows won't let them go.
    Returns {"done": how many, "left": what couldn't be done}. A half-built copy that may still be building (the other
    app) is left alone and named in "left"."""
    if action not in ("close_game", "clear_leftovers"):
        raise ValueError(f"no fix called {action!r}")
    if instances is None:
        # not a game rule: the game or one of its files isn't found
        raise ValueError("no folder for modded copies yet: the game wasn't found")
    if action == "close_game":
        running = [(pid, exe) for pid, exe in winfiles.processes() if winfiles.inside(exe, str(instances))]
        closed = [pid for pid, _exe in running if winfiles.close(pid)]
        return {"done": len(closed), "left": [f"{os.path.basename(exe)} ({pid})" for pid, exe in running
                                              if pid not in closed]}
    if action == "clear_leftovers":
        from .instance import TRASH, _set_aside, _sweep
        src = str(game) if game else ""
        done, left = 0, []
        for folder in _leftovers(instances):
            if folder.parent.name == TRASH:
                continue
            if _building(folder):
                left.append(f"{folder.name}: still being built, left alone")
                continue
            try:
                # only a copy that's gone counts here: one moved into the trash counts when the sweep removes it
                if _set_aside(str(folder), src, "A leftover copy") is None:
                    done += 1
            except OSError as exc:
                left.append(str(exc))
        trash = instances / TRASH
        before = len(list(trash.iterdir())) if trash.is_dir() else 0
        _sweep(str(trash), src)
        after = len(list(trash.iterdir())) if trash.is_dir() else 0
        done += before - after
        if after:
            left.append(f"{after} in {trash}: still held, removed on a later build")
        return {"done": done, "left": left}


def report(findings: list[dict], app: str, version: str) -> str:
    """The findings as plain text for a bug report (English keys and data: the same for every language), with the
    player's own folders written as %LOCALAPPDATA% and so on: the report is meant to be pasted in public."""
    import platform

    from .community import private_paths_out
    lines = [f"{app} {version}, Windows {platform.version()}"]
    for f in findings:
        data = ", ".join(f"{k}={v}" for k, v in f["data"].items())
        lines.append(f"[{f['level']}] {f['key']}: {f['say']}" + (f" ({data})" if data else ""))
    return private_paths_out("\n".join(lines))
