"""The Studio's folders copied to a short path in one click (StudioApi's HomeMoveCalls).

The owner, 2026-11-13, his answer 8 to "A Studio folder too deep for Windows: the message tells the modder to change a
Windows setting, the only way now, or should the Studio get its own setting for it?": "tell the modder, provide a quick
fix that auto does it if they dont want to do it manually". So each refusal of a folder too deep keeps its words (what
to do by hand) and the page offers this beside them.

Windows takes a path of 259 characters at most while its long paths are off for a program (horse_squad.PATH_MOST,
long_paths_on). The Studio's refusals of a folder too deep for it are the Generic Horse's Add's (ruse_studio.horse_squad:
the platform folder too deep for the files its builder makes there, the mod's folder too deep for its animations, and
a path longer than Windows takes that its sums didn't see coming); the page offers the move under each.

What the move does (home_move, a job):
1. Copies everything the Studio keeps to a short folder, short_target: <the platform folder's drive>\\RUSE2 (or RUSE2-2,
   RUSE2-3...: the first that doesn't exist yet), or the folder the modder chose instead (home_move_choose: the owner,
   2026-11-13, to "The short folder, such as C:\\RUSE2, is picked automatically. OK, or should the modder choose?": "It
   can be selected automatically, but the modder should be able to choose"). Either is checked before anything is
   copied, the same way (target_checked): on a drive of this PC, an empty folder or a new one, outside the folders it
   copies and the game's, and short enough for what was refused. Everything: the platform folder (rusemod.home:
   settings, the Launcher's library and mod sets, caches, the Generic Horse's files...) but the window's own folder
   (LEAVE: webview, which the window holds open while the Studio runs and makes again at its next start), and the
   mods, maps, exported files and backups the modder keeps in Documents\\RUSE 2.0 (rusemod.yourfiles), under the names
   a platform folder set by hand keeps them under (mods, maps, exports, mod-backups): with RUSE_PLATFORM_HOME set, the
   apps keep them there (yourfiles.documents_home), so none of them is left behind where the Studio wouldn't look.
2. Checks every file arrived, byte for byte (each copied file read again against the one it came from).
3. Makes the copy name its own places: the Studio's record of the mods it edits and opened (studio.json) and the
   Launcher's mod sets (yourfiles._follow), and each model record's "from" (files/models/<unit>.json) that names a file
   inside a copied folder (the Generic Horse's files in the platform folder, a model brought back from Blender in the
   mod's own blender folder): Resize and Move fit a model again from that file, so they keep working once the old
   folders are deleted.
4. Switches: the Windows user setting RUSE_PLATFORM_HOME to the new folder (set_user_env), then the Studio starts again
   from it (restart), so nothing changed after the copy is left in the old place.
Nothing is deleted: the old folders stay as they were, for the modder to delete himself once he has checked his mods in
the new place (the words say where they are). A copy that fails or doesn't check out is taken away again (the new
folder only, which the move made; a folder the modder chose that was there, empty, is left there empty), nothing is
switched, and the words say why. Windows only: elsewhere a path has no such limit (long_paths_on), so nothing is
offered."""
from __future__ import annotations

import filecmp
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ENV = "RUSE_PLATFORM_HOME"   # rusemod.home's: the platform folder set by hand
SHORT = "RUSE2"              # the short folder's name, at the top of the platform folder's drive
LEAVE = {"webview"}          # the window's own folder (rusemod.webui's storage_path): held open, made again at a start
QUIT_AFTER = 3.0             # seconds the page has to show the move's last line before the Studio starts again


def short_target(home: Path) -> Path:
    """The short folder the move copies to: <the drive of `home`>\\RUSE2, or RUSE2-2, RUSE2-3... (the first that isn't
    there yet)."""
    anchor = Path(os.path.abspath(str(home))).anchor or "C:\\"
    first = Path(anchor) / SHORT
    if not os.path.lexists(first):
        return first
    n = 2
    while os.path.lexists(Path(anchor) / f"{SHORT}-{n}"):
        n += 1
    return Path(anchor) / f"{SHORT}-{n}"


def _long(path) -> str:
    """A path Windows reads and writes whatever its length (\\\\?\\ in front), so a folder too deep can still be copied
    from; as it is elsewhere."""
    p = os.path.abspath(str(path))
    if sys.platform != "win32" or p.startswith("\\\\?\\"):
        return p
    return "\\\\?\\UNC\\" + p[2:] if p.startswith("\\\\") else "\\\\?\\" + p


def plan(home: Path, work: Path | None, to: Path) -> list[tuple[Path, Path]]:
    """[(what is copied, where to)]: each thing in the platform folder `home` but LEAVE, to the same name in `to`;
    each of the modder's folders in `work` (Documents\\RUSE 2.0: Mods, Maps, Exports, Backups) to the name a platform
    folder set by hand keeps it under (rusemod.yourfiles.OLD_NAMES), beside what the platform folder had of it."""
    from rusemod import yourfiles
    pairs = []
    if Path(home).is_dir():
        for entry in sorted(Path(home).iterdir(), key=lambda p: p.name.lower()):
            if entry.name.lower() in LEAVE:
                continue
            pairs.append((entry, Path(to) / entry.name))
    if work is not None:
        for kind in yourfiles.KINDS:
            src = Path(work) / yourfiles.NAMES[kind]
            if src.is_dir():
                pairs.append((src, Path(to) / yourfiles.OLD_NAMES[kind]))
    return pairs


def files_of(pairs: list) -> tuple[list[tuple[str, str]], list[str]]:
    """([(a file copied, where to)] as _long paths, [every folder to make]) of `pairs`, folders merged where two copy
    into one (the platform folder's mods left from before, and Documents\\RUSE 2.0\\Mods)."""
    files, folders = [], []
    for src, dst in pairs:
        if Path(_long(src)).is_file():
            files.append((_long(src), _long(dst)))
            continue
        for root, dirs, names in os.walk(_long(src)):
            dirs.sort()
            rel = os.path.relpath(root, _long(src))
            target = os.path.normpath(os.path.join(_long(dst), rel)) if rel != "." else _long(dst)
            folders.append(target)
            for n in sorted(names):
                files.append((os.path.join(root, n), os.path.join(target, n)))
    return files, folders


def clashes(files: list) -> list[str]:
    """Each place two of the copied files would land on (a mod of the same name in the platform folder's mods and in
    Documents\\RUSE 2.0\\Mods): the move is refused then, never one copied over the other."""
    seen, out = {}, []
    for src, dst in files:
        key = os.path.normcase(dst)
        if key in seen and seen[key] != src:
            out.append(dst)
        seen[key] = src
    return out


def _shown(path: str) -> str:
    """A _long path as the modder knows it."""
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    return path[4:] if path.startswith("\\\\?\\") else path


AGAIN = 2   # times a file that didn't check out is copied again (one written while it was copied: a log's new line)


def _same(src: str, dst: str) -> bool:
    return os.path.isfile(dst) and filecmp.cmp(src, dst, shallow=False)


def copy_checked(files: list, folders: list, say=None) -> int:
    """Copy each (file, where to) and make each folder, then check every file arrived byte for byte; one that doesn't
    is copied again (AGAIN times: it may have been written while it was copied). Returns the bytes copied; an OSError
    for a file that couldn't be read or written, a CopyMismatch for one that still isn't as it is."""
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    total = len(files)
    copied = 0
    for k, (src, dst) in enumerate(files, 1):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += os.path.getsize(dst)
        if say is not None and (k % 200 == 0 or k == total):
            say(f"Copied {k} of {total} files.")
    bad = []
    for k, (src, dst) in enumerate(files, 1):
        if not _same(src, dst):
            bad.append((src, dst))
        if say is not None and (k % 200 == 0 or k == total):
            say(f"Checked {k} of {total} files.")
    for _again in range(AGAIN):
        if not bad:
            break
        for src, dst in bad:
            shutil.copy2(src, dst)
        bad = [(src, dst) for src, dst in bad if not _same(src, dst)]
    if bad:
        raise CopyMismatch(_shown(bad[0][0]), _shown(bad[0][1]))
    return copied


class CopyMismatch(Exception):
    """A copied file that isn't byte for byte the one it came from (or isn't there)."""

    def __init__(self, src: str, dst: str):
        super().__init__(src)
        self.src, self.dst = src, dst


def _under(path: str, root: Path) -> str | None:
    """`path` written from inside `root` (any slashes, any case on Windows): the part after it, else None."""
    p = os.path.normcase(os.path.abspath(path))
    r = os.path.normcase(os.path.abspath(str(root))).rstrip("\\/")
    if p == r:
        return ""
    if p.startswith(r + os.sep):
        return os.path.abspath(path)[len(r) + 1:]
    return None


def moved_path(path: str, roots: list) -> str | None:
    """`path` in its new place when it's inside one of `roots` [(old folder, new folder)], else None."""
    if not isinstance(path, str) or not path or not os.path.isabs(path):
        return None
    for old, new in roots:
        rest = _under(path, old)
        if rest is not None:
            return str(Path(new) / rest) if rest else str(new)
    return None


def still_over(to: Path, home: Path, work: Path | None, needed) -> int:
    """How many characters the path a refusal measured (`needed`, home_move_offer's: {"what", "folder", "over"}) would
    still be longer than Windows takes once everything is in `to`: the platform folder is `to` itself, a mod's folder
    or a file moves with the folder it is in (plan). 0 when it fits there, and when nothing says how long it is (no
    refusal, or one of a folder the move doesn't copy: a mod opened from elsewhere)."""
    if not isinstance(needed, dict) or not isinstance(needed.get("over"), int) or needed["over"] <= 0 \
            or not isinstance(needed.get("folder"), str) or not needed["folder"]:
        return 0
    if needed.get("what") == "platform":
        new = str(to)
    else:
        new = moved_path(needed["folder"], list(plan(home, work, to)) + [(home, to)])
        if new is None:
            return 0
    return max(0, needed["over"] - (len(needed["folder"]) - len(new)))


def target_checked(to, home: Path, work: Path | None, game: Path | None, needed=None) -> Path:
    """`to`, the folder the move copies everything to (short_target, or the one the modder chose), once it's checked,
    as a full path; else a StudioError in words: it must be on a drive of this PC, an empty folder or a new one (the
    move never mixes his files with others, nor copies over them), outside the platform folder and the modder's own
    folder (`home`, `work`: what gets copied, and what the words then tell him to delete), outside the game's folder
    (`game`), and short enough for what was refused (`needed`: still_over)."""
    from .api import StudioError
    raw = str(to or "").strip()
    path = Path(os.path.abspath(raw)) if raw and Path(raw).is_absolute() else None
    if path is None or not os.path.isdir(path.anchor):
        # not a game rule: a folder the Studio can write to on this PC
        raise StudioError(f"{raw or to} isn't on a drive of this PC: choose a folder on one of its drives.")
    try:
        full = os.path.lexists(_long(path)) and not os.path.isdir(_long(path))
        if not full and os.path.isdir(_long(path)):
            with os.scandir(_long(path)) as inside:
                full = any(True for _entry in inside)
    except OSError:
        full = True
    if full:
        # not a game rule: the move never mixes the Studio's files with others, nor copies over them
        raise StudioError(f"{path} isn't an empty folder: choose an empty folder, or make a new one in the folder "
                          f"window.")
    for mine in [home] + ([work] if work is not None else []):
        if _under(str(path), Path(mine)) is not None:
            # not a game rule: what gets copied, which the modder deletes himself once he has checked the copy
            raise StudioError(f"{path} is inside {mine}, which is what gets copied: choose a folder outside it.")
    if game is not None and _under(str(path), Path(game)) is not None:
        # not a game rule: we never write into the game folder
        raise StudioError(f"{path} is inside the R.U.S.E. folder ({game}): the Studio's files can't go there. Choose a "
                          f"folder outside the game.")
    over = still_over(path, Path(home), work, needed)
    if over:
        # not a game rule: Windows' longest path, the one reason to move the Studio's folders
        raise StudioError(f"{path} is too deep: there, the path that was too long would still be {over} "
                          f"character(s) longer than Windows takes. Choose a folder nearer the top of a drive, or give "
                          f"the mod or the unit a shorter name.")
    return path


def _take_away(to: Path, existed: bool) -> None:
    """A copy that failed taken away again: the folder the move made, or, when it was a folder the modder chose that
    was there already (empty: target_checked), only what the move put in it."""
    if not existed:
        shutil.rmtree(_long(to), ignore_errors=True)
        return
    try:
        entries = list(os.scandir(_long(to)))
    except OSError:
        return
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            shutil.rmtree(entry.path, ignore_errors=True)
        else:
            try:
                os.remove(entry.path)
            except OSError:
                pass


def follow_records(to: Path, roots: list) -> list[str]:
    """In the copy at `to`: each model record (files/models/*.json of each mod and map) whose "from" is inside one of
    `roots` names the same file in its new place, every other byte as it was. Returns the records changed."""
    changed = []
    for kind in ("mods", "maps"):
        base = Path(to) / kind
        for record in sorted(base.glob("*/files/models/*.json")) if base.is_dir() else []:
            try:
                text = record.read_bytes().decode("utf-8")      # (its own line ends kept)
                doc = json.loads(text)
            except (OSError, UnicodeDecodeError, ValueError):
                continue                         # (one that can't be read stays as it is)
            if not isinstance(doc, dict) or not isinstance(doc.get("from"), str):
                continue
            new = moved_path(doc["from"], roots)
            if new is None or new == doc["from"]:
                continue
            out = text
            for ascii_only in (True, False):
                out = out.replace(json.dumps(doc["from"], ensure_ascii=ascii_only),
                                  json.dumps(new, ensure_ascii=ascii_only))
            want = dict(doc, **{"from": new})
            try:
                if json.loads(out) != want:
                    out = json.dumps(want, indent=1)
            except ValueError:
                out = json.dumps(want, indent=1)
            part = record.with_name(record.name + ".part")
            part.write_bytes(out.encode("utf-8"))
            os.replace(part, record)
            changed.append(str(record))
    return changed


def set_user_env(name: str, value: str) -> None:
    """The Windows user setting `name` (an environment variable of the user's, HKEY_CURRENT_USER\\Environment) set to
    `value`, and the programs started from now on told (WM_SETTINGCHANGE). An OSError when it can't be."""
    import ctypes
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    result = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(result))


def restart_command() -> list[str]:
    """How this Studio was started, to start it again: the program itself when built into one, else Python with
    ruse_studio."""
    if "__compiled__" in globals() or getattr(sys, "frozen", False):
        return [sys.executable] + sys.argv[1:]
    return [sys.executable, "-m", "ruse_studio"] + sys.argv[1:]


def restart(home: Path, popen=subprocess.Popen) -> None:
    """Start the Studio again on the platform folder `home` (RUSE_PLATFORM_HOME in its settings), apart from this one,
    which quits a moment later (QUIT_AFTER: the page shows the move's last line first)."""
    from rusemod.update import _quit_soon
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    popen(restart_command(), env=dict(os.environ, **{ENV: str(home)}), close_fds=True, creationflags=flags)
    try:
        from rusemod import bugwatch
        watch = bugwatch.current()
        if watch is not None:
            watch.save()      # (os._exit skips the save Bug Watch leaves for the app's end, as an update's quit does)
    except Exception:  # noqa: BLE001 - its counts never stop the restart
        pass
    _quit_soon(QUIT_AFTER)


class HomeMoveCalls:
    """Mixed into StudioApi: uses its _home, _work, _jobs, _mod_dir, _game, _window (and horse_squad's
    long_paths_on)."""

    _home_restart = staticmethod(restart)            # (tests stand in for these two: never the real Windows setting)
    _home_set_env = staticmethod(set_user_env)
    _home_pick = None                                # (tests stand in for the folder window: (window, start) -> a
    #                                                  folder or None; None: rusemod.webui.pick_folder)

    def home_move_offer(self, count_all: bool = False) -> dict:
        """What the page shows beside a refusal of a folder too deep: {"needed": the last such refusal of this Studio
        ({"what": "platform", "mod" or "path", "folder", "over": characters too many}: horse_squad's) or None, "can":
        whether the move can be done here (Windows, its long paths off for this program), "from": the platform folder,
        "files": the modder's own folder (Documents\\RUSE 2.0) or None, "to": the short folder it would copy to,
        "count": how many files, "size": their bytes ("size_text" as people read it), counted only while a refusal is
        "needed" or with `count_all` (a page asking after any other failure walks no folder), "leave": the folders of
        the platform folder it doesn't copy}."""
        from .horse_squad import long_paths_on
        home, work = Path(self._home), getattr(self, "_work", None)
        to = short_target(home)
        can = sys.platform == "win32" and not long_paths_on()
        count = size = 0
        if can and (self.__dict__.get("_too_deep") or count_all):
            files, _folders = files_of(plan(home, work, to))
            count = len(files)
            for src, _dst in files:
                try:
                    size += os.path.getsize(src)
                except OSError:
                    pass
        from rusemod.mod_index import size_text
        needed = self.__dict__.get("_too_deep")
        return {"needed": dict(needed) if isinstance(needed, dict) else None, "can": can, "from": str(home),
                "files": str(work) if work is not None else None, "to": str(to), "count": count, "size": size,
                "size_text": size_text(size), "leave": sorted(LEAVE)}

    def home_move_choose(self) -> dict:
        """Choose another folder… beside the move's button (the owner, 2026-11-13: "It can be selected automatically,
        but the modder should be able to choose"): the window's folder dialog, opened at the top of the platform
        folder's drive; the folder picked is checked as the move checks it (target_checked) and returned as {"to"}, the
        folder the page then shows and hands to home_move; {"to": None} when the modder cancels. One that can't be is
        refused in words."""
        home, work = Path(self._home), getattr(self, "_work", None)
        pick = self._home_pick
        if pick is None:
            if self._window is None:
                return {"to": None}
            from rusemod.webui import pick_folder
            pick = pick_folder
        chosen = pick(self._window, Path(short_target(home)).parent)
        if not chosen:
            return {"to": None}
        to = target_checked(chosen, home, work, self._game(), self.__dict__.get("_too_deep"))
        return {"to": str(to)}

    def home_move(self, to: str | None = None) -> dict:
        """Copy everything the Studio keeps to a short folder (`to`, the one the modder chose: home_move_choose; else
        short_target), check it, switch to it and start the Studio again from there (see the module's note): a job the
        page follows; done, its "result" is {"to", "files", "bytes", "records", "old": [the folders left where they
        were]}. Refused at once, in words: not Windows or long paths on (nothing to fix), another job of the Studio
        running, a folder that can't be the short folder (target_checked). Returns {"job": id}."""
        from rusemod.webui import Job
        from .api import StudioError
        from .horse_squad import long_paths_on
        if sys.platform != "win32" or long_paths_on():
            # not a game rule: Windows' longest path, the one reason to move the Studio's folders
            raise StudioError("Windows takes long paths for the Studio on this PC, so its folders don't need to move.")
        running = [j for j in self._jobs.values() if getattr(j, "state", None) == "running"]
        if running:
            # not a game rule: the copy must be of everything as it is, with nothing being written meanwhile
            raise StudioError("The Studio is busy with another job: wait for it to finish, then click again.")
        home, work = Path(self._home), getattr(self, "_work", None)
        to = target_checked(to if to else short_target(home), home, work, self._game(),
                            self.__dict__.get("_too_deep"))
        existed = os.path.isdir(_long(to))   # (a chosen folder that was there, empty: left there if the copy fails)
        job = Job()
        job.result = None
        self._jobs[job.id] = job

        def work_(say):
            pairs = plan(home, work, to)
            files, folders = files_of(pairs)
            same = clashes(files)
            if same:
                # not a game rule: two of the modder's files would land on one another
                raise StudioError(f"Two files would be copied to the same place ({_shown(same[0])}): a mod or map of "
                                  f"the same name is in {home} and in {work}. Rename or move one of them, then click "
                                  f"again.")
            say(f"Copying {len(files)} files to {to}…")
            try:
                copied = copy_checked(files, folders, say)
            except CopyMismatch as exc:
                _take_away(to, existed)
                # not a game rule: every file checked against the one it came from before anything is switched
                raise StudioError(f"{exc.src} didn't arrive in {to} as it is, so nothing was switched and the copy was "
                                  f"taken away again. Close the Launcher if it's open, then click again; if it happens "
                                  f"again, please report this.") from None
            except OSError as exc:
                _take_away(to, existed)
                from .api import file_error
                raise file_error(exc, to) from exc
            from rusemod import yourfiles
            try:
                records = follow_records(to, list(pairs))
                moved = [(Path(e), Path(dst) / Path(e).name) for src, dst in pairs if Path(src).is_dir()
                         and Path(dst).name in yourfiles.OLD_NAMES.values() for e in sorted(Path(src).iterdir())]
                yourfiles._follow(to, moved)
            except OSError as exc:      # (said in words, never in Python's own; nothing switched, the copy taken away)
                _take_away(to, existed)
                from .api import file_error
                raise file_error(exc, to) from exc
            say(f"Every file arrived as it is ({len(files)} files). The records in the copy name its own places "
                f"({len(records)} model record(s)).")
            try:
                self._home_set_env(ENV, str(to))
            except OSError:
                # not a game rule: the Windows setting the Studio's folder is read from (said in words, never Python's)
                raise StudioError(f"Everything is copied to {to} and checked, but the Windows setting {ENV} couldn't "
                                  f"be set. Set it to {to} yourself (Windows: Edit environment variables for your "
                                  f"account), then start the Studio again.") from None
            old = [str(home)] + ([str(work)] if work is not None else [])
            job.result = {"to": str(to), "files": len(files), "bytes": copied, "records": len(records), "old": old,
                          "restarting": True}
            say(f"The Studio now uses {to}. Your old folders are still where they were, nothing deleted: "
                f"{', '.join(old)}. Delete them yourself once you have checked your mods in {to}.")
            try:
                self._home_restart(to)
                say(f"Everything is in {to}: the Studio starts again from there.")
            except OSError:
                job.result["restarting"] = False
                say(f"Close the Studio and start it again: it then uses {to}.")

        return job.start(work_, f"Everything is in {to}.", plain=(StudioError, OSError))
