"""Modded instances: a launchable copy of the game that never touches the Steam install (PLAN L4, proven by C2).

Layout of an instance:
  - every `.dat` archive is a HARD LINK to the original (free, same drive, read-only use by the game); on a drive
    that can't share files with the game, or when the original is marked read-only (a link shares the mark, and the
    copy could then never be removed without changing the game's file), a full copy instead (counted as "full
    copies");
  - every other file is a real COPY (the game may rewrite configs/logs without reaching the install);
  - nothing in an instance is marked read-only: a copy of a read-only file drops the mark, so the copy can always be
    rebuilt and removed (a player's report, 2026-09-30: "[WinError 5] Access is denied" on every test, from a game
    folder whose files are read-only);
  - replaced files are written fresh (never through a hard link, which would change the original);
  - `steam_appid.txt` lets RUSE.exe start from the copy with Steam running.
The instance is built in `<dst>.partial` and only then swapped in, so a half-built instance never looks usable and the
last working one stays until the new one is complete.

A leftover (the old copy, or one left half-built) never blocks a build: what can't be removed is moved into the trash
folder next to the copies (`RUSE-Instances\\.trash`) and removed there once nothing holds it (a player's report,
2026-09-30: every second Test in game failed on an old copy Windows wouldn't delete). A file Windows won't delete can
still be moved: marked read-only, mapped into memory by a program, a running program's own file. Only an open file,
or R.U.S.E. still running from the copy, stops the move, and that is said with the program's name.
"""
from __future__ import annotations

import os
import shutil
import stat
import sys

from . import winfiles

STEAM_APPID = "21970"
TRASH = ".trash"  # next to the copies: leftovers waiting to be removed


class InstanceError(OSError):
    """A modded copy that can't be built, replaced or removed, said for the player."""


class GameRunning(InstanceError):
    """R.U.S.E. (or its crash reporter) is still running from the modded copy that's about to be rebuilt."""

    def __init__(self, message: str, running: list[tuple[int, str]]):
        super().__init__(message)
        self.running = running


def game_running(dst: str) -> list[tuple[int, str]]:
    """[(process id, program file)] of what runs from the copy `dst` (its old and half-built ones only go to the
    trash, running or not)."""
    return winfiles.running_from(dst) if os.path.isdir(dst) else []


def refuse_if_running(dst: str) -> None:
    """Raise GameRunning when R.U.S.E. still runs from the copy `dst`: it can't be rebuilt under a running game."""
    running = game_running(dst)
    if running:
        names = ", ".join(f"{os.path.basename(exe)} (process {pid})" for pid, exe in running)
        raise GameRunning(f"R.U.S.E. is still running from the modded copy at {dst}: {names}. Close the game, then try "
                          f"again.", running)


def _norm(rel: str) -> str:
    return os.path.normcase(os.path.normpath(rel))


def _read_only(path: str) -> bool:
    return not os.stat(path).st_mode & stat.S_IWRITE


def _copy(src_f: str, out: str) -> None:
    """A full copy that is ours: never marked read-only, whatever the original is."""
    shutil.copy2(src_f, out)
    mode = os.stat(out).st_mode
    if not mode & stat.S_IWRITE:
        os.chmod(out, stat.S_IMODE(mode) | stat.S_IWRITE)


def _remove_tree(path: str, src: str) -> None:
    """Remove an instance folder (an old one, or one left half-built). Windows refuses to delete a file marked
    read-only, or one a program keeps mapped into memory on a volume that deletes the old way: those go by a POSIX
    delete that ignores the mark (only that name goes: a hard link's other names keep theirs, the game's file among
    them). Without it (an older Windows), the copy's own files get the mark cleared, and a hard link that shares a
    read-only game file gets it cleared just long enough to drop the link, then put back on the game's file, so the
    install ends as it was. Anything else, a file in use above all (the game running from the copy), is raised."""
    def retry(func, p, exc):
        if not isinstance(exc, PermissionError) or func not in (os.unlink, os.remove, os.rmdir):
            raise exc
        if func is not os.rmdir:
            try:
                winfiles.posix_delete(p)
                return
            except OSError:
                pass
        try:
            st = os.lstat(p)
        except OSError:
            raise exc from None
        if st.st_mode & stat.S_IWRITE:
            raise exc  # not the read-only mark: most likely in use
        mode = stat.S_IMODE(st.st_mode)
        if func is not os.rmdir and st.st_nlink > 1:
            original = os.path.join(src, os.path.relpath(p, path))
            try:
                shares = os.path.samefile(original, p)
            except OSError:
                shares = False
            if not shares:
                raise exc  # a link to something we can't name: left alone rather than changing an unknown file
            os.chmod(p, mode | stat.S_IWRITE)
            try:
                func(p)
            finally:
                os.chmod(original, mode)
            return
        os.chmod(p, mode | stat.S_IWRITE)
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=lambda func, p, info: retry(func, p, info[1]))


def _who(path: str | None) -> str:
    """' (in use by RUSE.exe, process 1234)' for the programs holding `path`, or ''."""
    held = winfiles.holders(path) if path else []
    if not held:
        return ""
    names = ", ".join(f"{os.path.basename(exe) if exe else 'a program'}, process {pid}" for pid, exe in held)
    return f" (in use by {names})"


def _free(path: str) -> str:
    """`path`, or `path-2`, `path-3`... whichever isn't taken."""
    out, n = path, 1
    while os.path.lexists(out):
        n += 1
        out = f"{path}-{n}"
    return out


def _set_aside(path: str, src: str, what: str) -> str | None:
    """Get `path` (an old copy, or one left half-built) out of the way: removed, or when Windows won't let a file in it
    go, moved into the trash folder next to it, to be removed once nothing holds it (_sweep). Returns None when it's
    gone, else where it went. Raises InstanceError, naming what holds it, when even the move is refused."""
    if not os.path.lexists(path):
        return None
    try:
        _remove_tree(path, src)
        return None
    except OSError as exc:
        refused = exc
    target = _free(os.path.join(os.path.dirname(path), TRASH, os.path.basename(path)))
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.replace(path, target)
        return target
    except OSError as exc:
        where = refused.filename or path
        raise InstanceError(f"{what} at {path} can't be removed or moved aside: Windows refused {where} "
                            f"({refused.strerror or refused}){_who(refused.filename)}. If R.U.S.E. is running from "
                            f"it, close the game and try again; otherwise restart Windows, or delete that folder by "
                            f"hand, then try again.") from exc


def _sweep(trash: str, src: str) -> None:
    """Remove what the trash folder holds, as far as Windows lets it; the rest waits for the next time."""
    if not os.path.isdir(trash):
        return
    for name in os.listdir(trash):
        try:
            _remove_tree(os.path.join(trash, name), src)
        except OSError:
            pass
    try:
        os.rmdir(trash)
    except OSError:
        pass


def build_instance(src: str, dst: str, replace: dict | None = None,
                   rename: dict[str, str] | None = None, appid: str = STEAM_APPID) -> dict[str, int]:
    """Build an instance of the game folder `src` at `dst`. Returns counts of linked/copied/written files ("full
    copies" of packs that couldn't be linked, "read-only packs" among them; "old copy left" when the previous copy
    couldn't be removed yet: the next build removes it).

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
    refuse_if_running(dst)  # before the long build: a running game is said at once
    _sweep(os.path.join(os.path.dirname(dst), TRASH), src)  # what earlier builds couldn't remove yet
    _set_aside(staging, src, "A modded copy left half-built")  # a build that stopped halfway
    _set_aside(old, src, "An old modded copy")

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
                    locked = _read_only(src_f)  # a link would share the mark: copied instead
                    linked = False
                    if not locked:
                        try:
                            os.link(src_f, out)
                            linked = True
                        except OSError:  # another drive (or a file system without hard links): a full copy
                            pass
                    if linked:
                        counts["linked"] += 1
                    else:
                        _copy(src_f, out)
                        counts["full copies"] = counts.get("full copies", 0) + 1
                        if locked:
                            counts["read-only packs"] = counts.get("read-only packs", 0) + 1
                else:
                    _copy(src_f, out)
                    counts["copied"] += 1
        missing = set(replace) - seen
        if missing:
            raise FileNotFoundError(f"files to replace not found in the game folder: {sorted(missing)}")
        with open(os.path.join(staging, "steam_appid.txt"), "w") as f:
            f.write(appid)
    except BaseException:
        try:
            _remove_tree(staging, src)
        except OSError:
            pass  # the next build says why it can't go
        raise
    if os.path.exists(dst):
        try:
            os.replace(dst, old)
        except OSError as exc:
            try:
                _remove_tree(staging, src)
            except OSError:
                pass
            raise InstanceError(f"The modded copy at {dst} is in use, so it can't be replaced ({exc.strerror or exc})"
                                f"{_who(exc.filename)}. If R.U.S.E. is running from it, close the game and try "
                                f"again.") from exc
    os.replace(staging, dst)
    try:
        if _set_aside(old, src, "An old modded copy"):
            counts["old copy left"] = 1  # moved into the trash: the next build removes it
    except InstanceError:
        counts["old copy left"] = 1  # the new copy is ready; the next build moves the old one, or says why not
    return counts
