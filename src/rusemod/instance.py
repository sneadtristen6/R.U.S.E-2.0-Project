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
"""
from __future__ import annotations

import os
import shutil
import stat
import sys

STEAM_APPID = "21970"


class InstanceError(OSError):
    """A modded copy that can't be built, replaced or removed, said for the player."""


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
    """Remove an instance folder (an old one, or one left half-built). Windows refuses to delete anything marked
    read-only: the instance's own files get the mark cleared; a hard link that shares a read-only game file (made
    before copies dropped the mark) gets it cleared just long enough to drop the link, then put back on the game's
    file, so the install ends as it was. Anything else, a file in use above all (the game running from the copy), is
    raised."""
    def retry(func, p, exc):
        if not isinstance(exc, PermissionError) or func not in (os.unlink, os.remove, os.rmdir):
            raise exc
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


def _clear(path: str, src: str, what: str) -> None:
    """Remove `path` if it's there, or say plainly why it can't be."""
    if not os.path.lexists(path):
        return
    try:
        _remove_tree(path, src)
    except OSError as exc:
        where = exc.filename or path
        raise InstanceError(f"{what} at {path} can't be removed: Windows refused {where} ({exc.strerror or exc}). "
                            f"If R.U.S.E. is running from it, close the game and try again; otherwise delete that "
                            f"folder by hand, then try again.") from exc


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
    _clear(staging, src, "A modded copy left half-built")  # a build that stopped halfway
    _clear(old, src, "An old modded copy")  # before the long build, so a stuck one is said at once

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
            raise InstanceError(f"The modded copy at {dst} is in use, so it can't be replaced ({exc.strerror or exc}). "
                                f"If R.U.S.E. is running from it, close the game and try again.") from exc
    os.replace(staging, dst)
    try:
        if os.path.lexists(old):
            _remove_tree(old, src)
    except OSError:
        counts["old copy left"] = 1  # the new copy is ready; the next build removes the old one, or says why not
    return counts
