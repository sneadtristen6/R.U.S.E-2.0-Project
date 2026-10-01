"""A clean backup of the game's own folder, a check of the game against it, and a restore from it, for both apps (the
owner, 2026-09-30: "backup restore clean version of game in studio or launcher ... that way files stay clean").

Our apps never change the game's folder: they build modded copies in RUSE-Instances. Other mod managers and hand edits
do change it, and every copy built from a changed game carries those changes. So:
  - make: an independent copy of every file of the game folder (full copies, never hard links: a link shares its
    content with the game's file, so it would change with it) in `<the game's drive>\\RUSE-Backup\\<Steam build>`,
    with `manifest.json`: {"build", "made" (ISO time), "game" (the folder it was made from), "folders" (every folder,
    empty ones too), "files": {relative path, with "/": [size, mtime, sha256]}}. One backup per build. It is built in
    `<backup>.partial` and renamed when complete, so a half-made backup is never listed or used; the free space is
    checked first. No file in it is marked read-only, so it can always be removed. A file written while it's copied
    (Steam repairing it, say) is copied again, so the manifest describes exactly the bytes in the backup; one that
    keeps changing stops the backup, naming it. A make stopped between moving the old backup aside (`<backup>.old`)
    and moving the new one in leaves the old one complete: it is put back the next time the backups are listed or
    one is made.
  - check: the game folder against a backup: the files changed, missing and added. Fast by default (size and date; a
    file whose date differs is hashed, so a file that was only touched isn't "changed"); `deep` hashes every file.
  - restore: the added files moved into `RUSE-Backup\\set-aside-<date>` first, then the changed and missing files
    copied back from the backup (each written next to its target under a name no other file has, checked against the
    manifest's checksum, the version it replaces moved into the same set-aside folder, and only then swapped in; a
    target marked read-only keeps its mark; the temporary file never stays behind): nothing is ever deleted. The
    set-aside folder sits beside the backups, not inside one, so making a backup again never takes a player's files
    with the old one. Refused while R.U.S.E. runs (from the game folder, or from a modded copy, whose packs are the
    game's own files), when Steam has updated the game since the backup (another build: Steam's own repair,
    steam_verify_url, needs no backup), when the drive hasn't room for the files copied back, when the backup is
    inside the game folder (or the game inside it), and when the backup is damaged: a manifest whose paths aren't
    plain relative paths could name a place outside the game folder.
  - links: a link inside the game folder (a symbolic link, a junction: any reparse point that names another place,
    _link) is never followed, by any of the three. It isn't backed up; a check lists it as added (as changed where the
    backup has a file); a restore moves the link itself aside, and never writes through one.
  - one at a time, across both apps: making and restoring hold `RUSE-Backup\\.busy` (_busy: an app that stops lets
    it go), so the other app is told the backup is busy. A restore also waits for a modded copy being built from the
    game in either app (a Play, a Test in game: each marks it with a `.reading-*` file there while it builds, reading).

This module is the only place either app writes into the game's own folder: only when the player asks for a restore,
and only the files that differ from their clean backup.
"""
from __future__ import annotations

import contextlib
import datetime
import errno
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import time
from pathlib import Path

from . import winfiles
from .doctor import GAME_PROGRAMS
from .instance import STEAM_APPID, _free, _remove_tree, _who
from .steam import build_of

BACKUPS = "RUSE-Backup"         # next to RUSE-Instances, on the game's drive
MANIFEST = "manifest.json"
SET_ASIDE = "set-aside-"        # + the date: the files a restore moved out of the game folder
NO_BUILD = "no-build"           # the folder of a game whose Steam build can't be read (a folder picked by hand)
ROOM = 64 << 20                 # free space kept on top of what's copied (the manifest, the drive's own needs)
CHUNK = 8 << 20
TRIES = 3                       # reads of a file that changes while make copies it, before the backup stops
LOCK = ".busy"                  # in the backups folder: held by the app making or restoring a backup (_busy)
READING = ".reading-"           # + a random part: held by an app building a modded copy from the game (reading)
REPARSE_POINT = 0x400           # a file's FILE_ATTRIBUTE_REPARSE_POINT (Windows)
NAME_SURROGATE = 0x20000000     # a reparse tag's bit for a point that names another place (a link, a junction)
NOT_SAME_DEVICE = 17            # Windows' error for a move to another drive
DEVICE = re.compile(r"(con|prn|aux|nul|com\d|lpt\d)(\..*)?", re.IGNORECASE)  # names Windows keeps for devices
SHA256 = re.compile(r"[0-9a-f]{64}")
REQUESTED = "make-backup"       # in the platform folder (rusemod.home): the installer's "Keep a clean copy" task


class BackupError(OSError):
    """A backup that can't be made, checked or restored, said for the player."""


def steam_verify_url() -> str:
    """Steam's own repair: it checks every file of the game and downloads the ones that changed (no backup needed)."""
    return f"steam://validate/{STEAM_APPID}"


def backups_dir(game: Path) -> Path:
    """Where backups go: RUSE-Backup on the game's drive, beside RUSE-Instances."""
    return Path(Path(game).anchor) / BACKUPS


def backup_path(folder: Path, build: str | None) -> Path:
    """The backup of game build `build` in `folder` (one per build)."""
    return Path(folder) / (build or NO_BUILD)


def gb(size: int) -> float:
    return round(size / (1 << 30), 1)


def _key(rel: str) -> str:
    """A relative path as Windows compares them (case and separators)."""
    return os.path.normcase(rel)


def _link(st: os.stat_result) -> bool:
    """Whether an os.lstat is of a link to another place: a symbolic link, or on Windows a reparse point that names
    another place (a junction, a mount point; one whose kind can't be read counts too). A walk never goes through one,
    and nothing is read or written through one. Other reparse points (a cloud drive's files, say) hold their own
    content, so they are files and folders like any other."""
    if stat.S_ISLNK(st.st_mode):
        return True
    if not getattr(st, "st_file_attributes", 0) & REPARSE_POINT:
        return False
    tag = getattr(st, "st_reparse_tag", 0)
    return not tag or bool(tag & NAME_SURROGATE)


def _regular(st: os.stat_result) -> bool:
    """Whether an os.lstat is of a file a backup holds: an ordinary file, not a link (nor, elsewhere than Windows, a
    pipe or a device)."""
    return stat.S_ISREG(st.st_mode) and not _link(st)


def _walk(game: Path):
    """Everything inside `game`, as (relative path with "/", full path, its os.lstat), never through a link (_link):
    the link is listed, what it points to isn't (os.walk follows a Windows junction, even out of the folder or round
    in a loop)."""
    todo = [str(game)]
    while todo:
        folder = todo.pop()
        with os.scandir(folder) as entries:
            found = [entry.path for entry in entries]
        for full in found:
            try:
                st = os.lstat(full)
            except FileNotFoundError:
                continue  # gone since its folder was listed
            yield os.path.relpath(full, game).replace(os.sep, "/"), full, st
            if stat.S_ISDIR(st.st_mode) and not _link(st):
                todo.append(full)


def _scan(game: Path) -> tuple[dict[str, tuple[str, str, os.stat_result]], list[str]]:
    """The game folder's files and links (_link) by key -> (relative path with "/", full path, os.lstat), and its
    folders (empty ones too, links left out) as relative paths with "/"."""
    files, folders = {}, []
    for rel, full, st in _walk(game):
        if stat.S_ISDIR(st.st_mode) and not _link(st):
            folders.append(rel)
        else:
            files[_key(rel)] = (rel, full, st)
    return files, sorted(folders)


def _files(game: Path) -> dict[str, tuple[str, str, os.stat_result]]:
    """Every file (and link) of the game folder: key -> (its relative path with "/", its full path, its os.lstat)."""
    return _scan(game)[0]


def _kept(manifest: dict) -> set[str]:
    """The keys of the folders a backup has: its own list, and every folder its files are in."""
    out = {_key(d) for d in manifest.get("folders", [])}
    for rel in manifest["files"]:
        parts = rel.split("/")[:-1]
        out |= {_key("/".join(parts[:n])) for n in range(1, len(parts) + 1)}
    return out


def size_of(game: Path) -> int:
    """The bytes a backup of the game folder takes (links aren't backed up)."""
    return sum(st.st_size for _rel, _full, st in _files(Path(game)).values() if _regular(st))


def free_space(path: Path) -> int:
    """Free bytes on the drive of `path` (or of its nearest folder that exists)."""
    path = Path(os.path.abspath(path))
    while not path.exists() and path.parent != path:
        path = path.parent
    return shutil.disk_usage(path).free


def _plain(rel) -> bool:
    """Whether a manifest's path is a plain relative path with "/", so it can only name a place inside the folder it's
    taken in: no drive, no root, no "..", "." or empty part, no backslash or colon, no name Windows keeps for a device
    (NUL, COM1...) and no part ending in a dot or a space (Windows drops those, so two names would be one file)."""
    if not isinstance(rel, str) or not rel or "\\" in rel or ":" in rel or "\0" in rel or rel.startswith("/"):
        return False
    return all(part and not part.endswith((".", " ")) and not DEVICE.fullmatch(part) for part in rel.split("/"))


def _damage(data: dict) -> str:
    """What is wrong in a manifest's lists, said for the player, or ""."""
    for rel, (size, mtime, sha) in data["files"].items():
        if not _plain(rel):
            return f"the file {rel!r} isn't a place inside the game folder"
        if (isinstance(size, bool) or not isinstance(size, int) or size < 0 or isinstance(mtime, bool)
                or not isinstance(mtime, (int, float)) or not isinstance(sha, str) or not SHA256.fullmatch(sha)):
            return f"the file {rel!r} has no size, date or checksum"
    folders = data.get("folders", [])
    if not isinstance(folders, list):
        return "its folder list is damaged"
    for rel in folders:
        if not _plain(rel):
            return f"the folder {rel!r} isn't a place inside the game folder"
    if not isinstance(data.get("build"), (str, type(None))):
        return "its build is damaged"
    return ""


def read_manifest(backup: Path) -> dict:
    """A backup's manifest. Raises BackupError when the folder isn't a complete backup, or its manifest is damaged
    (_damage: a path that isn't a plain relative one could name a place outside the game folder)."""
    try:
        data = json.loads((Path(backup) / MANIFEST).read_text(encoding="utf-8"))
        files = data["files"]
        if not isinstance(files, dict) or not all(isinstance(v, list) and len(v) == 3 for v in files.values()):
            raise ValueError("its file list is damaged")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BackupError(f"{backup} isn't a complete backup ({MANIFEST}: {exc}).") from None
    damage = _damage(data)
    if damage:
        raise BackupError(f"The backup at {backup} is damaged ({MANIFEST}: {damage}), so it can't be used. Make a new "
                          f"backup while the game is clean (Verify with Steam first).")
    return data


def _orphans(folder: Path) -> list[Path]:
    """The old backups (.old) in `folder` whose backup isn't there: a make that stopped (a power cut, say) between
    moving the old one aside and moving the new one in."""
    return [p for p in sorted(folder.iterdir()) if p.name.endswith(".old") and len(p.name) > 4 and p.is_dir()
            and not os.path.lexists(p.with_name(p.name[:-4]))]


def _put_back_olds(folder: Path) -> None:
    """Put each orphan old backup (_orphans) back in place when it's complete: it is the last backup made. Only while
    holding the folder (_busy)."""
    for old in _orphans(folder):
        try:
            read_manifest(old)
            os.replace(old, old.with_name(old.name[:-4]))
        except OSError:
            pass  # damaged, or held by a program: a make says what's in the way


def list_backups(folder: Path) -> list[dict]:
    """The complete backups in `folder`, newest first: {"path", "build", "made", "files", "size"}. A half-made one
    (.partial), an old one being replaced (.old) and set-aside files are left out; an old one a make left without its
    replacement (_orphans) is put back first."""
    out = []
    folder = Path(folder)
    if not folder.is_dir():
        return out
    if _orphans(folder):
        try:
            with _busy(folder, "tidy"):
                _put_back_olds(folder)
        except OSError:
            pass  # the other app is at work there: its make puts it back itself
    for sub in sorted(folder.iterdir()):
        if not sub.is_dir() or sub.name.endswith((".partial", ".old")) or sub.name.startswith(SET_ASIDE):
            continue
        try:
            data = read_manifest(sub)
        except BackupError:
            continue
        out.append({"path": str(sub), "build": data.get("build"), "made": str(data.get("made", "")),
                    "files": len(data["files"]), "size": sum(int(v[0]) for v in data["files"].values())})
    return sorted(out, key=lambda b: b["made"], reverse=True)


# --- one app at a time: the lock files in the backups folder ---
def _claim(path: Path) -> int | None:
    """Open the lock file `path` as this app's own, or None when another app (or job) holds it. On Windows it is made
    new and kept open, and Windows won't remove an open file: one that can be removed is a leftover of an app that
    stopped (Windows closes a stopped program's files), so it goes and is made again. Elsewhere it holds an exclusive
    flock, which a stopped program lets go of too."""
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0)
    for _ in range(5):
        try:
            if winfiles.WINDOWS:
                try:
                    return os.open(path, flags | os.O_EXCL, 0o666)
                except FileExistsError:
                    if _in_use(path):
                        return None
                    continue  # a leftover, removed: made again
            import fcntl
            fd = os.open(path, flags, 0o666)
        except FileNotFoundError:
            path.parent.mkdir(parents=True, exist_ok=True)  # its folder went as another app let go: made again
            continue
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return None
        try:
            same = os.path.samestat(os.fstat(fd), os.stat(path))
        except FileNotFoundError:
            same = False
        if same:
            return fd
        os.close(fd)  # its holder removed it as it let go: a new one
    return None


def _in_use(path: Path) -> bool:
    """Whether an app holds the lock file `path` (_claim). A leftover of an app that stopped is removed."""
    if winfiles.WINDOWS:
        for attempt in range(3):
            try:
                os.remove(path)
                return False
            except FileNotFoundError:
                return False
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.05)  # an antivirus can have it open for a moment
        return True
    import fcntl
    try:
        fd = os.open(path, os.O_RDWR)
    except FileNotFoundError:
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return True
    try:
        if os.path.samestat(os.fstat(fd), os.stat(path)):
            os.remove(path)
    except FileNotFoundError:
        pass
    os.close(fd)
    return False


def _release(path: Path, fd: int) -> None:
    """Let go of a lock file taken with _claim, and remove it when it still can be (Windows: another app may hold it
    anew by then; it stays theirs)."""
    if winfiles.WINDOWS:
        os.close(fd)
    try:
        os.remove(path)
    except OSError:
        pass
    if not winfiles.WINDOWS:
        os.close(fd)


def _taken(path: Path) -> str:
    """The message for a backups folder the other app holds (_busy), saying what it is doing."""
    try:
        what = json.loads(path.read_text(encoding="utf-8")).get("what")
    except (OSError, ValueError, AttributeError):
        what = None
    doing = {"make": "making a backup", "restore": "restoring the game's files"}.get(what, "working on the backups")
    return (f"The game backup is busy: the other app (the Launcher or the Studio) is {doing}. Wait for it to finish, "
            f"then try again.")


def _readers(folder: Path) -> int:
    """How many modded copies are being built from the game right now, in either app (their marks in `folder`:
    reading). The marks of an app that stopped are removed."""
    return sum(1 for p in sorted(folder.iterdir()) if p.name.startswith(READING) and _in_use(p))


@contextlib.contextmanager
def _busy(folder: Path, what: str):
    """Hold the backups folder `folder` for `what` ("make", "restore", "tidy"): one app at a time, across both apps.
    Raises BackupError, saying what the other app is doing, when it holds it. A restore also waits for a modded copy
    being built from the game (reading): the lock says "restore" before the marks are looked at, and a build looks at
    the lock after making its mark, so one of the two always sees the other. A folder made only for this goes again
    after, when nothing else was put in it."""
    folder = Path(folder)
    made = not folder.is_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / LOCK
    fd = _claim(path)
    if fd is None:
        raise BackupError(_taken(path))
    try:
        os.ftruncate(fd, 0)  # a leftover's words (elsewhere than Windows, the file can be an old one)
        os.write(fd, json.dumps({"what": what, "pid": os.getpid()}).encode("utf-8"))
        if what == "restore" and _readers(folder):
            raise BackupError("A modded copy of the game is being built from its files (a Play, or a Test in game): "
                              "wait for it to finish, then try again.")
        yield
    finally:
        _release(path, fd)
        if made:
            try:
                folder.rmdir()
            except OSError:
                pass  # something was made in it (the backup): it stays


def _restore_running(folder: Path) -> bool:
    """Whether an app is restoring the game's files from a backup in `folder` right now (it holds the folder: _busy)."""
    path = folder / LOCK
    try:
        what = json.loads(path.read_text(encoding="utf-8")).get("what")
    except (OSError, ValueError, AttributeError):
        return False  # none, or one just taken that doesn't say yet: a restore looks for the marks after it says
    return what == "restore" and _in_use(path)


@contextlib.contextmanager
def reading(folder: Path | None):
    """While a modded copy is built from the game's files (a Play, a Test in game, in either app): a mark in the
    backups folder `folder` that a restore waits for (_busy). Raises BackupError while a restore runs. No mark when the
    folder isn't there (no backup to restore from yet; making one copies the whole game, which takes longer than
    building a copy, whose packs are links), or when one can't be made there (that never stops a Play)."""
    folder = Path(folder) if folder is not None else None
    path, fd = None, None
    if folder is not None and folder.is_dir():
        path = folder / f"{READING}{secrets.token_hex(8)}"
        try:
            fd = _claim(path)
        except OSError:
            fd = None
    try:
        if folder is not None and folder.is_dir() and _restore_running(folder):
            raise BackupError("The game's files are being restored: wait for it to finish.")
        yield
    finally:
        if fd is not None:
            _release(path, fd)


# --- copying and hashing ---
class _Count:
    """Bytes done out of a total, told to `progress(done, total)` as they go."""

    def __init__(self, total: int, progress=None):
        self.done, self.total, self.progress = 0, total, progress

    def add(self, n: int) -> None:
        self.done += n
        if self.progress is not None:
            self.progress(self.done, self.total)


def _hash(path: str, count: _Count) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
            count.add(len(chunk))
    return h.hexdigest()


def _pipe(f, g, count: _Count) -> tuple[str, int]:
    """Copy the open file `f` into the open file `g`: (the sha256 of the bytes copied, how many)."""
    h, n = hashlib.sha256(), 0
    while chunk := f.read(CHUNK):
        g.write(chunk)
        h.update(chunk)
        n += len(chunk)
        count.add(len(chunk))
    return h.hexdigest(), n


def _same(a: os.stat_result, b: os.stat_result, which: bool = True) -> bool:
    """Whether two looks at a file saw the same version of it: its size, its date and (`which`, for two looks of the
    same kind: by name, or through the open file) which file it is, where the drive says."""
    return ((a.st_size, a.st_mtime_ns) == (b.st_size, b.st_mtime_ns)
            and (not which or not a.st_ino or not b.st_ino or a.st_ino == b.st_ino))


def _copy_steady(rel: str, full: str, out: Path, count: _Count) -> tuple[os.stat_result, str]:
    """Copy the game's file `rel` (at `full`) to `out`, with its dates, never marked read-only: (its stat, the sha256
    of what was copied). A file written while it's read would be saved half old, half new, and later put back as
    clean: the copy is kept only when every byte was read and the file is the same after as before, by its name and
    through the open file (_same); else it's read again, TRIES times, then the backup stops, naming it."""
    for _ in range(TRIES):
        start = count.done
        try:
            first = os.lstat(full)
            with open(full, "rb") as f, open(out, "wb") as g:
                before = os.fstat(f.fileno())
                sha, n = _pipe(f, g, count)
                after = os.fstat(f.fileno())
            last = os.lstat(full)
        except FileNotFoundError:
            raise BackupError(f"{rel} went away while the backup was being made (a program is changing the game's "
                              f"files: Steam?). Make the backup again once it has finished.") from None
        if n == before.st_size and _same(before, after) and _same(first, last) and _same(first, before, False):
            os.utime(out, ns=(first.st_atime_ns, first.st_mtime_ns))
            return first, sha  # by name, as a check sees the game's files
        count.add(start - count.done)  # read again: back to where this file began
    raise BackupError(f"{rel} kept changing while it was being copied (a program is writing it: Steam, or a mod "
                      f"manager?). Wait for it to finish or close it, then make the backup again.")


def _is_game(game: Path) -> bool:
    return game.is_dir() and any(p.name.lower() == "ruse.exe" for p in game.iterdir())


def _existing(dest: Path, replace: bool) -> None:
    """Refuse a make over what is at `dest`: a folder that isn't a backup, or a backup that isn't to be replaced."""
    if not dest.exists():
        return
    try:
        made = read_manifest(dest).get("made", "?")
    except BackupError:
        raise BackupError(f"There's a folder at {dest} that isn't a backup: move or rename it, then try "
                          f"again.") from None
    if not replace:
        raise BackupError(f"There's already a backup of this build at {dest} (made {made}). Make it again only if "
                          f"the game is clean now: Verify with Steam first.")


def make(game: Path, dest: Path | None = None, progress=None, replace: bool = False) -> dict:
    """Back up every file of the game folder `game` into `dest` (by default RUSE-Backup\\<build> on its drive); links
    in it (_link) are left out. `progress(done, total)` follows the bytes copied. A backup already there is only
    replaced with `replace` (the game may not be clean any more). Refused (BackupError) while the other app makes or
    restores a backup there (_busy). Returns {"path", "build", "files", "size"}."""
    game = Path(os.path.abspath(game))
    if not _is_game(game):
        raise BackupError(f"{game} isn't the R.U.S.E folder (there's no RUSE.exe in it).")
    build = build_of(game)
    dest = Path(os.path.abspath(dest)) if dest else backup_path(backups_dir(game), build)
    staging, old = Path(f"{dest}.partial"), Path(f"{dest}.old")
    if winfiles.inside(str(dest), str(game)) or any(winfiles.inside(str(game), str(p)) for p in (dest, staging, old)):
        raise BackupError("A backup can't go inside the game folder, nor the game folder inside a backup.")
    _existing(dest, replace)
    found, folders = _scan(game)
    files = sorted((f for f in found.values() if _regular(f[2])), key=lambda f: f[0])
    need = sum(st.st_size for _rel, _full, st in files)
    free = free_space(dest.parent)
    if free < need + ROOM:
        raise BackupError(f"There isn't enough free space on {dest.anchor or dest.parent} for the backup: it needs "
                          f"{gb(need + ROOM)} GB, and {gb(free)} GB is free. Free some space, then try again.")
    with _busy(dest.parent, "make"):
        _put_back_olds(dest.parent)
        _existing(dest, replace)  # again, now that the other app can't be at work there
        for leftover in (staging, old):  # a backup that stopped halfway, or an old one a replace couldn't remove
            if leftover.exists():
                _remove_tree(str(leftover), str(game))
        count = _Count(need, progress)
        manifest = {"build": build, "made": datetime.datetime.now().isoformat(timespec="seconds"), "game": str(game),
                    "folders": folders, "files": {}}
        try:
            for folder in folders:
                (staging / folder).mkdir(parents=True, exist_ok=True)
            for rel, full, _st in files:
                out = staging / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                st, sha = _copy_steady(rel, full, out, count)
                manifest["files"][rel] = [st.st_size, st.st_mtime, sha]
            (staging / MANIFEST).write_text(json.dumps(manifest, indent=1), encoding="utf-8")
            if dest.exists():
                try:
                    os.replace(dest, old)
                except OSError as exc:
                    raise BackupError(f"The backup at {dest} is in use, so it can't be replaced "
                                      f"({exc.strerror or exc}){_who(exc.filename)}. Close what has it open, then try "
                                      f"again.") from exc
            os.replace(staging, dest)
        except BaseException:
            if old.exists() and not dest.exists():
                try:
                    os.replace(old, dest)  # the old backup goes back where it was
                except OSError:
                    pass  # the next listing puts it back (_put_back_olds)
            try:
                _remove_tree(str(staging), str(game))
            except OSError:
                pass  # the next backup removes it
            raise
        try:
            if old.exists():
                _remove_tree(str(old), str(game))
        except OSError:
            pass  # the new backup is complete; the next one removes the old
    return {"path": str(dest), "build": build, "files": len(files),
            "size": sum(v[0] for v in manifest["files"].values())}


def _compare(game: Path, manifest: dict, deep: bool, progress) -> dict:
    """The game folder against a backup's manifest: {"changed", "missing", "added", "hashed"} (check's)."""
    have = _files(game)
    changed, missing, to_hash = [], [], []
    for rel, (size, mtime, sha) in manifest["files"].items():
        got = have.pop(_key(rel), None)
        if got is None:
            missing.append(rel)
        elif not _regular(got[2]) or got[2].st_size != size:
            changed.append(rel)  # a link where the backup has a file isn't that file (and isn't read through)
        elif deep or got[2].st_mtime != mtime:
            to_hash.append((rel, got[1], sha))
    count = _Count(sum(manifest["files"][rel][0] for rel, _full, _sha in to_hash), progress)
    for rel, full, sha in to_hash:
        try:
            if _hash(full, count) != sha:
                changed.append(rel)
        except FileNotFoundError:
            missing.append(rel)  # gone since the folder was listed
    return {"changed": sorted(changed), "missing": sorted(missing),
            "added": sorted(rel for rel, _full, _st in have.values()), "hashed": len(to_hash)}


def check(game: Path, backup: Path, deep: bool = False, progress=None) -> dict:
    """The game folder against a backup: {"build_matches", "changed", "missing", "added"} (relative paths with "/";
    "added" are files the backup doesn't have, links among them), plus "build" (the game's), "backup_build", "files"
    (in the backup) and "hashed". Fast by default: a file of the same size and date is taken as unchanged, and only a
    file whose date differs is hashed; `deep` hashes every file. A link is never read through: where the backup has a
    file, it's "changed". `progress(done, total)` follows the bytes hashed."""
    game = Path(os.path.abspath(game))
    manifest = read_manifest(backup)
    found = _compare(game, manifest, deep, progress)
    build = build_of(game)
    return {"build_matches": manifest.get("build") == build, "build": build, "backup_build": manifest.get("build"),
            **found, "files": len(manifest["files"])}


def running(game: Path, processes=None) -> list[tuple[int, str]]:
    """[(process id, program file)] of what stops a restore: anything running from the game folder, and R.U.S.E. (or
    its crash reporter) running from anywhere, since a modded copy's packs are the game's own files. `processes`
    stands in for the real list in tests."""
    out = []
    for pid, exe in (processes or winfiles.processes)():
        if winfiles.inside(exe, str(game)) or os.path.basename(exe).lower().startswith(GAME_PROGRAMS):
            out.append((pid, exe))
    return out


def _other_drive(exc: OSError) -> bool:
    return exc.errno == errno.EXDEV or getattr(exc, "winerror", None) == NOT_SAME_DEVICE


def _move(src: Path, out: Path) -> None:
    """Move the game's `src` (a file, or a link: the link itself, never what it points to) to `out`, making its folder.
    Raises OSError when it can't (in use, say): it stays where it was, and no copy of it is left at `out`. A file on
    another drive than `out` (a game folder that is a link to another drive) is copied, then removed; when it can't be
    removed, the copy goes again."""
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(src, out)
        return
    except OSError as exc:
        refused = exc
    st = os.lstat(src)
    if not _other_drive(refused) or not _regular(st):
        raise refused  # a link moves as itself or not at all
    mode = stat.S_IMODE(st.st_mode)
    try:
        shutil.copy2(src, out)
        if not mode & stat.S_IWRITE:
            os.chmod(src, mode | stat.S_IWRITE)  # Windows won't remove a file marked read-only
        os.remove(src)
    except BaseException:
        if os.path.lexists(src):  # it stays where it was, so its copy goes again
            with contextlib.suppress(OSError):
                os.chmod(src, mode)
            with contextlib.suppress(OSError):
                os.chmod(out, mode | stat.S_IWRITE)
                os.remove(out)
        raise


def _set_aside(game: Path, rel: str, aside: Path, keep: set[str]) -> bool:
    """Move the game's file (or link) `rel` into `aside` (same relative path: _move), then remove the folders that
    move left empty, unless the backup has them (`keep`, their keys): they come with the set-aside file, so nothing is
    lost. False when it had already gone (a restore's temporary file, say)."""
    src = game / rel
    try:
        _move(src, aside / rel)
    except FileNotFoundError:
        if os.path.lexists(src):
            raise
        return False
    folder = src.parent
    while folder != game and _key(folder.relative_to(game).as_posix()) not in keep:
        try:
            folder.rmdir()  # only an empty folder goes: it held nothing but what was moved
        except OSError:
            break
        folder = folder.parent
    return True


def _prune(folder: Path) -> None:
    """Remove the empty folders in `folder`, and `folder` itself when it ends empty, never going through a link: the
    ones a restore made for files it then couldn't move."""
    if not folder.is_dir():
        return
    inner = [full for _rel, full, st in _walk(folder) if stat.S_ISDIR(st.st_mode) and not _link(st)]
    for path in sorted(inner, key=len, reverse=True) + [str(folder)]:  # the deepest first
        with contextlib.suppress(OSError):
            os.rmdir(path)  # only an empty folder goes


def _in_the_way(game: Path, parts: list[str], safe: set[str]) -> str | None:
    """The first of the folders on the path `parts` (inside the game folder) that isn't a real folder there: a link to
    another place, or a file. None when each one that's there is a folder (the rest are made as real folders). `safe`
    remembers the folders seen."""
    for n in range(1, len(parts) + 1):
        sub = "/".join(parts[:n])
        if sub in safe:
            continue
        try:
            st = os.lstat(game / sub)
        except FileNotFoundError:
            return None
        if _link(st) or not stat.S_ISDIR(st.st_mode):
            return sub
        safe.add(sub)
    return None


def _new_temp(target: Path) -> tuple[int, Path]:
    """A new file next to `target` whose name no other file has (made here and now, so a player's own file is never
    overwritten): (its open descriptor, its path)."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    while True:
        temp = target.with_name(f"{target.name}.{secrets.token_hex(2)}.restoring")
        try:
            return os.open(temp, flags, 0o666), temp
        except FileExistsError:
            continue


def _put_back(src: Path, target: Path, sha: str, count: _Count, aside: Path) -> bool:
    """Copy the backup's `src` over the game's `target`: written next to it (_new_temp), checked against the manifest's
    checksum, then swapped in, the version it replaces (a file, or a link) moved to `aside` first, so nothing is
    deleted. A target marked read-only: the clean file gets the mark too. The temporary file never stays behind.
    Returns whether a replaced version went to `aside`."""
    if not src.is_file():
        raise BackupError("the backup's copy is missing")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = _new_temp(target)
    try:
        with os.fdopen(fd, "wb") as g, open(src, "rb") as f:
            got, _n = _pipe(f, g, count)
        if got != sha:
            raise BackupError("the backup's copy is damaged (it doesn't match its checksum)")
        when = os.stat(src)
        os.utime(temp, ns=(when.st_atime_ns, when.st_mtime_ns))
        try:
            now = os.lstat(target)
        except FileNotFoundError:
            now = None
        mode = None
        if now is not None:
            if stat.S_ISDIR(now.st_mode) and not _link(now):
                raise BackupError("a folder is in its place")
            if not _link(now):
                mode = stat.S_IMODE(now.st_mode)
            _move(target, aside)
        try:
            os.replace(temp, target)
        except OSError:
            if now is not None:
                with contextlib.suppress(OSError):
                    os.replace(aside, target)  # the version that was there goes back
            raise
        if mode is not None and not mode & stat.S_IWRITE:
            os.chmod(target, mode)
        return now is not None
    finally:
        with contextlib.suppress(OSError):
            os.remove(temp)  # still there only when something failed


def restore(game: Path, backup: Path, deep: bool = False, progress=None, checking=None, processes=None) -> dict:
    """Put the game folder back as the backup has it: the added files (and links) moved into
    RUSE-Backup\\set-aside-<date>, then the changed and missing ones copied back, each changed one's own version moved
    into that folder too, so nothing is deleted. Checks first (check(), `deep` as there, its progress told to
    `checking`); then `progress(done, total)` follows the bytes copied. Returns {"restored": how many, "set_aside": how
    many added files were moved, "kept": how many replaced versions were, "set_aside_to": that folder, or None when
    nothing went there, "left": what couldn't be done, "build"}. Nothing is written through a link (_in_the_way).
    Refused (BackupError) while R.U.S.E. runs (`processes` stands in for the real list in tests), while the other app
    makes or restores a backup or either app builds a modded copy from the game (_busy), when the game isn't the
    backup's build, when the backup is damaged (read_manifest) or inside the game folder (or the game inside it), and
    when the game's drive hasn't room for the files copied back (the versions they replace are kept)."""
    game, backup = Path(os.path.abspath(game)), Path(os.path.abspath(backup))
    if not _is_game(game):
        raise BackupError(f"{game} isn't the R.U.S.E folder (there's no RUSE.exe in it).")
    if winfiles.inside(str(backup), str(game)) or winfiles.inside(str(game), str(backup)):
        raise BackupError("A backup inside the game folder (or a game folder inside a backup) can't be restored from: "
                          "move the backup out of the game folder, then try again.")
    read_manifest(backup)
    with _busy(backup.parent, "restore"):
        manifest = read_manifest(backup)  # again: the other app may have made it again in between
        held = running(game, processes)
        if held:
            names = ", ".join(f"{os.path.basename(exe)} (process {pid})" for pid, exe in held)
            raise BackupError(f"R.U.S.E. is running: {names}. Close the game, then restore.")
        build = build_of(game)
        if manifest.get("build") != build:
            raise BackupError(f"Steam has updated R.U.S.E. since this backup was made (the backup is build "
                              f"{manifest.get('build') or '?'}, the game is build {build or '?'}), so its files would "
                              f"put back the old version. Use Verify with Steam to repair the game, then make a new "
                              f"backup.")
        found = _compare(game, manifest, deep, checking)
        files = manifest["files"]
        todo = found["changed"] + found["missing"]
        need = sum(int(files[rel][0]) for rel in todo)
        free = free_space(game)
        if need and free < need + ROOM:
            raise BackupError(f"There isn't enough free space on {game.anchor} to restore the game's files: it needs "
                              f"{gb(need + ROOM)} GB, and {gb(free)} GB is free. Free some space, then try again.")
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        aside = Path(_free(str(backup.parent / f"{SET_ASIDE}{stamp}")))
        keep = _kept(manifest)
        restored, moved, kept, left = 0, 0, 0, []
        for rel in found["added"]:  # first: an added link may stand where the backup has a folder
            try:
                moved += _set_aside(game, rel, aside, keep)
            except OSError as exc:
                left.append(f"{rel}: {exc.strerror or exc}{_who(str(game / rel))}")
        count = _Count(need, progress)
        safe, blocked = set(), set()  # the folders seen to be real ones, and the ones that aren't
        for rel in todo:
            target = game / rel
            way = _in_the_way(game, rel.split("/")[:-1], safe)
            if way is not None:
                blocked.add(way)
                left.append(f"{rel}: {way} isn't a folder of the game's (a link to another place, or a file), so "
                            f"nothing was written through it")
                count.add(int(files[rel][0]))
                continue
            try:
                kept += _put_back(backup / rel, target, files[rel][2], count, aside / rel)
                restored += 1
            except OSError as exc:
                left.append(f"{rel}: {exc.strerror or exc}{_who(str(target))}")
        for folder in manifest.get("folders", []):  # an empty folder of the game's that went (EmptySteamDepot, say)
            way = _in_the_way(game, folder.split("/"), safe)
            if way is not None:
                if way not in blocked:  # once is enough
                    blocked.add(way)
                    left.append(f"{folder}: {way} isn't a folder of the game's (a link to another place, or a file)")
                continue
            try:
                (game / folder).mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                left.append(f"{folder}: {exc.strerror or exc}")
        _prune(aside)  # the folders made for files that then couldn't move
    return {"restored": restored, "set_aside": moved, "kept": kept,
            "set_aside_to": str(aside) if moved or kept else None, "left": left, "build": build}


def _percent(say, prefix: str = ""):
    """A progress(done, total) that says "37%" (after `prefix`) each time the whole percent changes."""
    last = [-1]

    def progress(done, total):
        pct = int(done * 100 / total) if total else 100
        if pct != last[0]:
            last[0] = pct
            say(f"{prefix}{pct}%")
    return progress


class BackupCalls:
    """The window API's clean-backup calls, for both apps (a mixin beside rusemod.update.UpdateCalls: the API has
    `_jobs`, `_home` (the platform folder) and `_backups`, where backups go (None: RUSE-Backup on the game's drive),
    and gives `_backup_game()` (the game folder, or None), `_backup_open_url(url)` and `_building_copy()`: what is
    building a modded copy from the game right now (a Play, a Test in game), said as a sentence, or "").

    Making, checking and restoring run as jobs (one at a time; across the two apps, rusemod.backup._busy); a job's
    lines are its progress ("37%"; a restore's check comes first, as "check 37%"), and what it found or did is the
    job's "result" once it's done (the APIs' job() add it, with _with_result). A Play or a Test in game wraps its work
    in _reading_game, so a restore in the other app waits for it."""

    _backups: Path | None = None
    _backup_job: str | None = None

    def _backup_busy(self) -> str:
        """The kind of backup job running ("make", "check", "restore"), or ""."""
        job = self._jobs.get(self._backup_job) if self._backup_job else None
        return getattr(job, "kind", "") if job is not None and job.state == "running" else ""

    def _restoring(self) -> bool:
        """Whether the game's files are being restored (a Play or a Test in game waits for it)."""
        return self._backup_busy() == "restore"

    def _reading_game(self, game: Path | None, work):
        """`work(say)` for a job that builds a modded copy from `game`'s files (a Play, a Test in game): marked while
        it runs, so a restore in either app waits for it, and refused while one runs (reading)."""
        folder = self._backup_folder(game) if game is not None else None

        def run(say):
            with reading(folder):
                return work(say)
        return run

    def _backup_folder(self, game: Path) -> Path:
        return Path(self._backups) if self._backups else backups_dir(game)

    def _the_game(self) -> Path:
        game = self._backup_game()
        if game is None:
            raise BackupError("We couldn't find R.U.S.E. Choose its folder first.")
        return game

    def _backup_for(self, game: Path) -> Path:
        """The backup of the game's build, else the newest one (restore then says Steam has updated the game)."""
        folder = self._backup_folder(game)
        mine = backup_path(folder, build_of(game))
        if (mine / MANIFEST).is_file():
            return mine
        found = list_backups(folder)
        if not found:
            raise BackupError("There's no backup of the game yet: make one first, while the game is clean.")
        return Path(found[0]["path"])

    def backup_status(self) -> dict:
        """The clean game backup as Settings shows it: {"found": the game is, "build", "folder": where backups go,
        "drive", "backups": [{"path", "build", "made", "date", "files", "size_gb", "matches": of the game's build}]
        newest first, "current": the one of the game's build or None, "need_gb": what a backup takes, "free_gb": free
        on that drive (None when it can't be read), "enough", "busy": the backup job running or ""}."""
        game = self._backup_game()
        if game is None:
            return {"found": False, "backups": [], "current": None, "busy": self._backup_busy()}
        folder, build = self._backup_folder(game), build_of(game)
        backups = [b | {"date": b["made"][:16].replace("T", " "), "size_gb": gb(b["size"]),
                        "matches": b["build"] == build} for b in list_backups(folder)]
        need = size_of(game) + ROOM
        try:
            free = free_space(folder)
        except OSError:
            free = None
        return {"found": True, "build": build, "folder": str(folder), "drive": game.drive or game.anchor,
                "backups": backups, "current": next((b for b in backups if b["matches"]), None), "need_gb": gb(need),
                "free_gb": None if free is None else gb(free), "enough": free is None or free >= need,
                "busy": self._backup_busy()}

    def _backup_start(self, kind: str, work, done: str) -> dict:
        from .webui import Job
        if self._backup_busy():
            raise BackupError("The game backup is busy: wait for it to finish, then try again.")
        job = Job()
        job.kind, job.result = kind, None
        self._jobs[job.id] = job
        self._backup_job = job.id

        def run(say):
            job.result = work(say)
        return job.start(run, done, plain=(OSError,))

    def backup_make(self, replace: bool = False) -> dict:
        """Make the clean backup of the game's build, in the background (`replace`: make it again over the one there,
        when the game is clean now). Returns {'job': id}; the result is {"path", "build", "files", "size",
        "size_gb"}."""
        game = self._the_game()
        dest = backup_path(self._backup_folder(game), build_of(game))

        def work(say):
            made = make(game, dest, _percent(say), replace=bool(replace))
            self._backup_asked().unlink(missing_ok=True)  # the installer's ask, done
            return made | {"size_gb": gb(made["size"])}
        return self._backup_start("make", work, "The backup is made.")

    def _backup_asked(self) -> Path:
        return Path(self._home) / REQUESTED

    def backup_requested(self) -> dict:
        """{"make": True} when the installer's task "Keep a clean copy of my game's files" was ticked (it leaves
        `make-backup` in the platform folder), the game is found and its build has no backup yet: the window then
        makes it on this start. The mark stays until a backup of the build exists (made now, or already there), so
        a start without the game asks again once it's found."""
        mark = self._backup_asked()
        if not mark.is_file():
            return {"make": False}
        game = self._backup_game()
        if game is None:
            return {"make": False}
        if (backup_path(self._backup_folder(game), build_of(game)) / MANIFEST).is_file():
            mark.unlink(missing_ok=True)
            return {"make": False}
        return {"make": not self._backup_busy()}

    def backup_check(self, deep: bool = False) -> dict:
        """Check the game's files against its backup, in the background (`deep`: every byte). Returns {'job': id}; the
        result is rusemod.backup.check's."""
        game = self._the_game()
        found = self._backup_for(game)
        return self._backup_start("check", lambda say: check(game, found, bool(deep), _percent(say)),
                                  "The game's files are checked.")

    def backup_restore(self, deep: bool = False) -> dict:
        """Put the game's files back as the backup has them, in the background: the added ones moved into
        RUSE-Backup\\set-aside-<date>, the changed and missing ones copied back (the versions they replace moved there
        too). Refused while a modded copy is being built from the game. Returns {'job': id}; the result is
        rusemod.backup.restore's."""
        building = self._building_copy()
        if building:
            raise BackupError(building)
        game = self._the_game()
        found = self._backup_for(game)
        return self._backup_start("restore", lambda say: restore(game, found, bool(deep), _percent(say),
                                                                 _percent(say, "check ")),
                                  "The game's files are restored.")

    def steam_verify(self) -> dict:
        """Steam's own repair of the game (it downloads the files that changed; no backup needed)."""
        url = steam_verify_url()
        self._backup_open_url(url)
        return {"opened": url}

    def _with_result(self, view: dict) -> dict:
        """A job's view, with a backup job's "result" once it's done."""
        job = self._jobs.get(view.get("id"))
        result = getattr(job, "result", None)
        return view | {"result": result} if result is not None and view.get("state") == "done" else view
