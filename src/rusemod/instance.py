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
  - `steam_appid.txt` lets RUSE.exe start from the copy with Steam running;
  - RECORD (`rusemod-copy.json`, next to RUSE.exe; the game doesn't read it) says what the copy was built from
    (rusemod.play.built_from: the mods' files, the game's build and files, the app's code) and how each of its files
    got there (a link to the game's file, a copy of it, or written by the build), with each file's size and time. It
    is written last, only when everything else is in place.
A build first sets the old copy aside (set_aside_old: renamed `<dst>.old`), so it can't be started by mistake while
the new one builds; the instance is built in `<dst>.partial` and only then swapped in, so a half-built instance never
looks usable.

Reusing what's there (a player, 2026-10-04: "Waiting 30 minutes every time just to add or remove a unit"):
  - when the copy's record says it was built from exactly what Play has now, every file in it is as the record says
    and nothing else is there, the game starts from it with no build at all (needs_build); so does the old copy set
    aside by a build that then stopped on a mistake in the mods, once the mods are back as they were for it
    (take_back). A copy whose mods changed while the build read them keeps no record (forget), so the next Play
    builds;
  - otherwise the new copy is still built in `.partial`, but each file of the old copy that is still an unchanged copy
    of the game's file goes into it as it is, without copying: hard-linked from the old copy (on the copy's own drive,
    so this works when the game is on another drive), or moved out of an old copy set aside when that drive has no
    hard links. The old copy is never written to: a build that stops leaves it whole for the next one (what was moved
    out goes back). Packs linked to the game's are linked again (the same file), the files a build replaces are
    written new, and a file the last build replaced but this one doesn't goes back to the game's file (a link, or a
    copy).

A leftover (the old copy, or one left half-built) never blocks a build: what can't be removed is moved into the trash
folder next to the copies (`RUSE-Instances\\.trash`) and removed there once nothing holds it (a player's report,
2026-09-30: every second Test in game failed on an old copy Windows wouldn't delete). A file Windows won't delete can
still be moved: marked read-only, mapped into memory by a program, a running program's own file. Only an open file,
or R.U.S.E. still running from the copy, stops the move, and that is said with the program's name.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys

from . import winfiles

STEAM_APPID = "21970"
TRASH = ".trash"  # next to the copies: leftovers waiting to be removed
RECORD = "rusemod-copy.json"  # in the copy, next to RUSE.exe: what it was built from, and how each file got there
RECORD_FORMAT = 1

# The build's lines a player reads in the apps' log, in English; the apps say them in the player's language (their
# words.toml has each under the same name, the same English for "us": tests/test_play_reuse.py)
NOTES = {
    "play_unchanged": "Nothing changed since the last build: the modded copy is used as it is.",
    "play_other_drive": "The modded copy is on another drive than the game, so the game's packs are copied into it, "
                        "not shared: {gb} GB copied this time. With modded copies on the game's drive ({drive}), "
                        "starting the game with mods is much faster.",
    "doc_drive_other": "Modded copies go to {path}, on a {fs} drive: each copy is a full copy, and Windows may refuse "
                       "to delete one while R.U.S.E. runs. An NTFS drive is best.",
}


class Note(str):
    """A line for the player (NOTES), in English: `word` names it in the apps' words, `data` fills its blanks."""

    def __new__(cls, word: str, **data):
        line = super().__new__(cls, NOTES[word].format(**data))
        line.word, line.data = word, data
        return line


class Counts(dict):
    """build_instance's counts of files by how they got into the copy ("linked", "copied", "written", "kept" from the
    old copy, "full copies" of packs, "read-only packs" among them, "old copy left"), and apart from them:
    `copied_bytes`, what was copied from the game this time, and `other_drive`, whether the copy is on another drive
    than the game's files."""

    copied_bytes = 0
    other_drive = False


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
        # not a game rule: something else is busy (the game, the other app, a restore)
        raise GameRunning(f"R.U.S.E. is still running from the modded copy at {dst}: {names}. Close the game, then try "
                          f"again.", running)


def _norm(rel: str) -> str:
    return os.path.normcase(os.path.normpath(rel))


def _read_only(path: str) -> bool:
    return not os.stat(path).st_mode & stat.S_IWRITE


def _copy(src_f: str, out: str) -> None:
    """A full copy that is ours: never marked read-only, whatever the original is."""
    shutil.copy2(src_f, _fresh(out))
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
        # not a game rule: something else is busy (the game, the other app, a restore)
        raise InstanceError(f"{what} at {path} can't be removed or moved aside: Windows refused {where} "
                            f"({refused.strerror or refused}){_who(refused.filename)}. If R.U.S.E. is running from "
                            f"it, close the game and try again; otherwise restart Windows, or delete that folder by "
                            f"hand, then try again.") from exc


def set_aside_old(src: str, dst: str) -> None:
    """Take the old copy at `dst` away before a long build, so it can't be started by mistake while the new one is
    built (a test copy started early ran the old build, twice in one afternoon). It is renamed `<dst>.old`: the build
    takes its unchanged files from there (build_instance), then removes it. When Windows won't let it be renamed, it
    goes as before (removed, or moved into the trash). Refuses while R.U.S.E. runs from it."""
    refuse_if_running(dst)
    if not os.path.lexists(dst):
        return
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    old = dst + ".old"
    _set_aside(old, src, "An old modded copy")  # one left by an earlier build: the copy at dst is newer
    try:
        os.replace(dst, old)
    except OSError:
        _set_aside(dst, src, "the old modded copy")


# --- the record of a copy's build (RECORD) ---
def _entry(kind: str, path: str, rel: str | None = None, src_st=None) -> dict:
    """A file's line in the record: how it got into the copy ("link" to the game's file `rel`, "copy" of it, or
    "written"), its size and time there, and for a copy the game file's size and time when it was copied."""
    st = os.stat(path)
    entry = {"kind": kind, "size": st.st_size, "mtime_ns": st.st_mtime_ns}
    if rel is not None:
        entry["from"] = rel
    if src_st is not None:
        entry["from_size"], entry["from_mtime_ns"] = src_st.st_size, src_st.st_mtime_ns
    return entry


def _inside(rel: object) -> bool:
    return isinstance(rel, str) and bool(rel) and not os.path.isabs(rel) and not os.path.splitdrive(rel)[0] \
        and ".." not in _norm(rel).split(os.sep)


def _good_entry(rel: object, entry: object) -> bool:
    if not _inside(rel) or not isinstance(entry, dict) or entry.get("kind") not in ("link", "copy", "written"):
        return False
    numbers = ["size", "mtime_ns"] + (["from_size", "from_mtime_ns"] if entry["kind"] == "copy" else [])
    if not all(type(entry.get(n)) is int for n in numbers):
        return False
    return entry["kind"] == "written" or _inside(entry.get("from"))


def read_record(folder: str) -> dict | None:
    """The record a finished build left in the copy at `folder` (RECORD), its files also by normalised path under
    "by_path"; None when there's none, or it can't be read or doesn't make sense (any doubt means a build)."""
    try:
        with open(os.path.join(folder, RECORD), encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(record, dict) or record.get("format") != RECORD_FORMAT or not isinstance(record.get("game"), str) \
            or not isinstance(record.get("files"), dict):
        return None
    if not all(_good_entry(rel, entry) for rel, entry in record["files"].items()):
        return None
    record["by_path"] = {_norm(rel): entry for rel, entry in record["files"].items()}
    return record


def _write_record(folder: str, src: str, files: dict, built_from: dict | None) -> None:
    with open(os.path.join(folder, RECORD), "w", encoding="utf-8") as f:
        json.dump({"format": RECORD_FORMAT, "game": src, "built_from": built_from, "files": files}, f, indent=1,
                  sort_keys=True)


def _intact(src: str, folder: str, rel: str, entry: dict) -> bool:
    """Whether the copy's file `rel` is still as the record's `entry` says: the game's file itself for a link (and so
    not marked read-only), at the recorded size and time for a copy or a written file, a copy's game file unchanged."""
    path = os.path.join(folder, rel)
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode) or not st.st_mode & stat.S_IWRITE:
        return False
    if entry["kind"] == "link":
        try:
            return os.path.samefile(os.path.join(src, entry["from"]), path)
        except OSError:
            return False
    if (st.st_size, st.st_mtime_ns) != (entry["size"], entry["mtime_ns"]):
        return False
    if entry["kind"] == "copy":
        try:
            game = os.stat(os.path.join(src, entry["from"]))
        except OSError:
            return False
        return (game.st_size, game.st_mtime_ns) == (entry["from_size"], entry["from_mtime_ns"])
    return True


def needs_build(src: str, dst: str, built_from: dict | None) -> str:
    """Why the copy at `dst` can't be started as it is, for what Play would build now (`built_from`, from
    rusemod.play.built_from), or "" when it can: its record says it was built from exactly that, out of this game
    folder, every file the build put there is still as the record says, and nothing else is in it (a pack left there
    could be loaded with the rest, as a new map's pack is; the game was seen writing nothing into its folder)."""
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if not built_from or not built_from.get("key"):
        return "nothing to compare the copy with"
    if not os.path.isdir(dst):
        return "there's no modded copy yet"
    record = read_record(dst)
    if record is None:
        return "the copy has no record of its build"
    if not isinstance(record.get("built_from"), dict) or record["built_from"].get("key") != built_from["key"]:
        return "the copy was built from other mods, another game build or another version of the app"
    if _norm(record["game"]) != _norm(src):
        return "the copy was built from another game folder"
    for rel, entry in record["files"].items():
        if not _intact(src, dst, rel, entry):
            return f"{rel} in the copy isn't as its build left it"
    known = set(record["by_path"]) | {_norm(RECORD)}
    for root, _dirs, names in os.walk(dst):
        for n in names:
            rel = os.path.relpath(os.path.join(root, n), dst)
            if _norm(rel) not in known:
                return f"{rel} in the copy wasn't put there by its build"
    return ""


def forget(dst: str) -> None:
    """Take the record out of the copy at `dst`, so the next Play builds again: what it was built from isn't certain."""
    try:
        os.remove(os.path.join(dst, RECORD))
    except FileNotFoundError:
        pass


def take_back(src: str, dst: str, built_from: dict | None) -> bool:
    """With no copy at `dst`, put the old copy set aside (`<dst>.old`: the last build stopped, on a mistake in the
    mods, before a new copy was in) back in its place, when it was built from exactly `built_from` and is still
    whole (needs_build): the mods are back as they were for it. True when it is at `dst` again."""
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    old = dst + ".old"
    if os.path.lexists(dst) or not os.path.isdir(old) or needs_build(src, old, built_from):
        return False
    try:
        os.replace(old, dst)
    except OSError:
        return False
    return True


def _take(entry: dict | None, base: str, out_rel: str, rel: str, src_st, out: str, may_move: bool,
          moved: list) -> dict | None:
    """Put the old copy's file `out_rel` (in `base`) into the new copy at `out`, when the old record's `entry` says it
    is a copy of the game's file `rel` and both are unchanged since (sizes and times as recorded, not marked
    read-only): hard-linked, or moved when the drive has no hard links and the old copy is set aside (`may_move`;
    noted in `moved`, to go back if the build stops). Returns its entry for the new record, or None."""
    if entry is None or entry["kind"] != "copy" or _norm(entry["from"]) != _norm(rel):
        return None
    if (entry["from_size"], entry["from_mtime_ns"]) != (src_st.st_size, src_st.st_mtime_ns):
        return None
    have = os.path.join(base, out_rel)
    try:
        st = os.lstat(have)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode) or not st.st_mode & stat.S_IWRITE or \
            (st.st_size, st.st_mtime_ns) != (entry["size"], entry["mtime_ns"]):
        return None
    try:
        os.link(have, out)
    except OSError:  # a drive without hard links
        if not may_move:
            return None
        try:
            os.replace(have, out)
        except OSError:
            return None
        moved.append((out, have))
    return {**entry, "from": rel}


def _put_back(moved: list) -> None:
    """Files moved out of the old copy go back, so a build that stopped leaves it as it was (as far as Windows lets)."""
    for out, have in reversed(moved):
        try:
            os.replace(out, have)
        except OSError:
            pass  # that file is copied again next time


def _other_drive(src: str, dst: str) -> bool:
    try:
        return os.stat(src).st_dev != os.stat(dst).st_dev
    except OSError:
        return False


def _fresh(out: str) -> str:
    """`out`, with nothing at it: a name already there (a link into the game or the old copy) is dropped first, so a
    write can never go through a hard link into another file."""
    if os.path.lexists(out):
        os.remove(out)
    return out


def _write_file(out: str, content) -> None:
    with open(_fresh(out), "wb") as f:
        content(f) if callable(content) else f.write(content)


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
                   rename: dict[str, str] | None = None, appid: str = STEAM_APPID,
                   add: dict | None = None, built_from: dict | None = None) -> Counts:
    """Build an instance of the game folder `src` at `dst`. Returns counts of linked/copied/written files ("kept":
    unchanged copies taken from the old copy; "full copies" of packs that couldn't be linked, "read-only packs" among
    them; "old copy left" when the previous copy couldn't be removed yet: the next build removes it), and what was
    copied (Counts).

    replace: relative path -> new content: bytes, or a function that writes it to an open file (for multi-GB packs,
             e.g. `lambda f: arc.write_to(f, changed)`), written as an independent file.
    rename:  relative path -> new relative path (the file appears only under the new name; content untouched).
    add:     relative path -> content (as in `replace`) of a file the game folder hasn't got (a new map's pack).
    built_from: what the copy is built from (rusemod.play.built_from), kept in its record for needs_build.

    The old copy (at `dst`, or set aside at `<dst>.old` by set_aside_old) gives its unchanged copies of the game's
    files when its record vouches for them. One at `dst` stays whole and in place until the new copy is complete (its
    files are only hard-linked); one set aside may also have files moved out, put back if the build stops.
    """
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if _norm(dst) == _norm(src) or _norm(dst).startswith(_norm(src) + os.sep):
        # not a game rule: we never write into the game folder
        raise ValueError("refusing to build an instance inside the game folder")
    replace = {_norm(k): v for k, v in (replace or {}).items()}
    rename = {_norm(k): v for k, v in (rename or {}).items()}
    add = dict(add or {})
    for rel in add:
        if os.path.lexists(os.path.join(src, rel)) or _norm(rel) in replace:
            # not a game rule: we never write into the game folder
            raise ValueError(f"can't add {rel}: the game folder already has it")
    staging, old = dst + ".partial", dst + ".old"
    refuse_if_running(dst)  # before the long build: a running game is said at once
    _sweep(os.path.join(os.path.dirname(dst), TRASH), src)  # what earlier builds couldn't remove yet
    _set_aside(staging, src, "A modded copy left half-built")  # a build that stopped halfway
    if os.path.lexists(dst):
        _set_aside(old, src, "An old modded copy")  # one left by an earlier build: the copy at dst is newer
        base, may_move = dst, False  # stays whole and in place until the new copy is in: its files are only linked
    else:
        base, may_move = old, True  # set aside (set_aside_old): nothing starts it, its files may move out
    record = read_record(base) if os.path.isdir(base) else None
    if record is not None and _norm(record["game"]) != _norm(src):
        record = None  # copies of another game folder's files
    if record is None and base == old:
        _set_aside(old, src, "An old modded copy")  # nothing in it is known unchanged: it goes, as before
    reuse = record["by_path"] if record is not None else {}

    counts = Counts(linked=0, copied=0, written=0)
    files, moved, seen = {}, [], set()  # the new record's files; what moved out of the old copy; what was replaced
    try:
        for root, _dirs, names in os.walk(src):
            for fn in names:
                src_f = os.path.join(root, fn)
                rel = os.path.relpath(src_f, src)
                key = _norm(rel)
                out_rel = rename.get(key, rel)
                out = os.path.join(staging, out_rel)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                if key in replace:
                    _write_file(out, replace[key])
                    files[out_rel] = _entry("written", out)
                    counts["written"] += 1
                    seen.add(key)
                    continue
                src_st = os.stat(src_f)
                pack = fn.lower().endswith(".dat")
                locked = not src_st.st_mode & stat.S_IWRITE  # a link would share the mark: never linked
                if pack and not locked:
                    try:
                        os.link(src_f, out)
                        files[out_rel] = _entry("link", out, rel)
                        counts["linked"] += 1
                        continue
                    except OSError:  # another drive (or a file system without hard links)
                        pass
                kept = _take(reuse.get(_norm(out_rel)), base, out_rel, rel, src_st, out, may_move, moved)
                if kept is not None:
                    files[out_rel] = kept
                    counts["kept"] = counts.get("kept", 0) + 1
                    continue
                _copy(src_f, out)
                files[out_rel] = _entry("copy", out, rel, src_st)
                counts.copied_bytes += src_st.st_size
                if pack:
                    counts["full copies"] = counts.get("full copies", 0) + 1
                    if locked:
                        counts["read-only packs"] = counts.get("read-only packs", 0) + 1
                else:
                    counts["copied"] += 1
        missing = set(replace) - seen
        if missing:
            # not a game rule: we never write into the game folder
            raise FileNotFoundError(f"files to replace not found in the game folder: {sorted(missing)}")
        for rel, content in add.items():
            out = os.path.join(staging, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            _write_file(out, content)
            files[rel] = _entry("written", out)
            counts["written"] += 1
        appid_file = os.path.join(staging, "steam_appid.txt")
        with open(_fresh(appid_file), "w") as f:
            f.write(appid)
        files["steam_appid.txt"] = _entry("written", appid_file)
        _write_record(staging, src, files, built_from)  # last: a copy without it always gets a build
    except BaseException:
        _put_back(moved)
        try:
            _remove_tree(staging, src)
        except OSError:
            pass  # the next build says why it can't go
        raise
    counts.other_drive = _other_drive(src, staging)
    if os.path.exists(dst):
        try:
            os.replace(dst, old)
        except OSError as exc:
            _put_back(moved)
            try:
                _remove_tree(staging, src)
            except OSError:
                pass
            # not a game rule: something else is busy (the game, the other app, a restore)
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
