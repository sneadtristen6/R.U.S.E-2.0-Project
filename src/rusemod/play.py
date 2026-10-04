"""Starting R.U.S.E. (PLAN.md L4), for both apps: the launcher's Play and the Studio's Test in game. Vanilla starts
through Steam; modded play builds the mods into a modded copy of the game (rusemod.instance) and starts the game from
there, after Steam. The Steam install is never touched.

A Play whose mods, game and app are the same as the modded copy's last build, with the copy as that build left it,
starts the copy with no build (built_from, rusemod.instance.needs_build); a build reuses what it can of the old copy.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import webbrowser
import zlib
from pathlib import Path

from .build import DEFAULT_PACK, BuildError, build_and_write, build_cache, load_mod
from .instance import Note
from .steam import build_of

STEAM_PLAY = "steam://rungameid/21970"
STEAM_OPEN = "steam://open/main"


def _files_hash(folder: Path, skip=("__pycache__",)) -> str:
    """SHA-256 over every file under `folder` (its path inside, its size, its bytes), in path order."""
    h = hashlib.sha256()
    found = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in skip]
        found += [os.path.join(root, n) for n in names]
    for path in sorted(found, key=lambda p: os.path.relpath(p, folder).replace(os.sep, "/").lower()):
        with open(path, "rb") as f:
            data = f.read()
        h.update(f"{os.path.relpath(path, folder).replace(os.sep, '/')}\0{len(data)}\0".encode() + data)
    return h.hexdigest()


def _code_id() -> dict:
    """The app's own code as this program started with it: the files of the packages a build runs (rusemod, and
    ruse_mod_engine for .rmod mods), the Python running them, and the app's own .exe when it's built into one."""
    out = {"python": sys.version, "zlib": zlib.ZLIB_RUNTIME_VERSION}
    exe = Path(sys.executable)
    if "__compiled__" in globals() or getattr(sys, "frozen", False):  # built into an .exe: the code is in it
        try:
            st = exe.stat()
            out["exe"] = [str(exe), st.st_size, st.st_mtime_ns]
        except OSError:
            out["exe"] = [str(exe)]
    from importlib.util import find_spec
    for name in ("rusemod", "ruse_mod_engine"):
        try:
            spec = find_spec(name)
            folder = list(spec.submodule_search_locations or [])[0] if spec else None
            out[name] = _files_hash(Path(folder)) if folder else None
        except (ImportError, OSError, ValueError, IndexError):
            out[name] = None
    return out


CODE = _code_id()  # taken once, as the program starts: an edit made to the code later shows after a restart


def built_from(game: Path, mod_paths, pack: str = DEFAULT_PACK) -> dict:
    """What a modded copy is built from, for rusemod.instance.needs_build: the mods in their order (every file of
    each), the game (its Steam build, and every file's size and time), the pack the units come from and the app's code
    (CODE). Taken before the mods are read and again after the build (Starter.modded): a copy whose mods changed in
    between keeps no record, so the next Play builds. `key` is the SHA-256 of all of it."""
    game = Path(game)
    files = []
    for root, _dirs, names in os.walk(game):
        for n in names:
            path = os.path.join(root, n)
            try:
                st = os.stat(path)
                files.append([os.path.normcase(os.path.relpath(path, game)), st.st_size, st.st_mtime_ns])
            except OSError:
                files.append([os.path.normcase(os.path.relpath(path, game)), None, None])
    mods = []
    for m in mod_paths:
        p = Path(m)
        try:
            if p.is_dir():
                mods.append([str(p.resolve()), _files_hash(p)])
            else:
                mods.append([str(p.resolve()), hashlib.sha256(p.read_bytes()).hexdigest()])
        except OSError:
            mods.append([str(p), None])  # not there (or unreadable): never the same as a build's
    try:
        build = build_of(game)
    except (OSError, ValueError):
        build = None
    parts = {"game": os.path.normcase(str(game.resolve())), "build": build,
             "game_files": hashlib.sha256(json.dumps(sorted(files, key=lambda f: f[0])).encode()).hexdigest(),
             "mods": mods, "pack": pack, "code": CODE}
    return {"key": hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest(), **parts}


def mod_stamps(mod_paths) -> list:
    """Every file of the mods, with its size and time: taken with built_from before the build and again after, a file
    written in between shows even when its bytes are back as they were (built_from compares bytes only)."""
    out = []
    for m in mod_paths:
        found = []
        for root, dirs, names in os.walk(m) if os.path.isdir(m) else [(os.path.dirname(m), [], [os.path.basename(m)])]:
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            found += [os.path.join(root, n) for n in names]
        for path in sorted(found):
            try:
                st = os.stat(path)
                out.append([path, st.st_size, st.st_mtime_ns])
            except OSError:
                out.append([path, None, None])
    return out


def in_words(say, words: dict | None):
    """`say`, with the lines rusemod gives in English for a player (rusemod.instance.Note) said in the player's
    language: `words` is the app's words (its words.toml) in that language. Any other line goes as it is."""
    if not words:
        return say

    def said(line):
        if isinstance(line, Note) and words.get(line.word):
            try:
                line = words[line.word].format(**line.data)
            except (KeyError, IndexError, ValueError):
                pass  # a translation that lost a blank: the English
        say(line)
    return said


def open_url(url: str) -> None:
    if sys.platform == "win32":
        os.startfile(url)  # steam:// links and folders open with their Windows handler
    else:
        webbrowser.open(url)


def start_game(exe: Path) -> None:
    subprocess.Popen([str(exe)], cwd=str(exe.parent))


def steam_running() -> bool:
    if sys.platform != "win32":
        return True
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"], capture_output=True, text=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)  # no console flashing up from the apps
    return "steam.exe" in out.stdout.lower()


def instances_dir(game: Path) -> Path:
    """Where modded copies go: RUSE-Instances on the game's drive (sharing files with the game only works on one
    drive)."""
    return Path(game.anchor) / "RUSE-Instances"


SHARED = "Modded game"  # the one modded copy on the PC: both apps build every Play and Test in game into it (the owner,
# 2026-10-02: "only one stored ... version of game on whole pc needed"); one game runs at a time anyway
BUILDING = ".building"  # held while either app builds the copy (rusemod.backup._claim): the other one waits its turn


def shared_copy(game: Path, instances: Path | None = None) -> Path:
    """The modded copy both apps use: `RUSE-Instances\\Modded game` on the game's drive (or in `instances`)."""
    return (Path(instances) if instances else instances_dir(game)) / SHARED


def keep_order(mods) -> None:
    """Make the given order of `mods` [(ModInfo, ops)] count for the load order: each mod loads after the one before
    it, unless either of the two already says how they relate (a dependency, `after` or `before`)."""
    for (prev, _ops), (info, _o) in zip(mods, mods[1:]):
        related = prev.id in info.after or prev.id in info.before or prev.id in info.depends or \
            info.id in prev.after or info.id in prev.before or info.id in prev.depends
        if not related and prev.id != info.id:
            info.after.append(prev.id)


class Starter:
    """Starts the game. The arguments replace the real world in tests: opening links, starting the game, checking for
    Steam, and waiting for it."""

    def __init__(self, open_url=open_url, start_game=start_game, steam_running=steam_running, wait=time.sleep):
        self.open_url, self.start_game, self.steam_running, self.wait = open_url, start_game, steam_running, wait

    def vanilla(self, say) -> None:
        say("Starting R.U.S.E. through Steam…")
        self.open_url(STEAM_PLAY)

    def modded(self, game: Path, mod_folders, instance: Path, name: str, say, words: dict | None = None) -> None:
        """Build these mod folders into the modded copy `instance` and start the game from it. The folders' order
        counts: a later mod comes after an earlier one, so it wins when both change the same value, unless the mods
        themselves say otherwise (MOD_FORMAT §10.6). A problem raises BuildError (or RndfError, OSError) with a
        message for the player, and nothing starts; so do .rmod mods that can't go together (the build refuses them
        before building anything, naming every clash: rusemod.rmod.clashes).

        When the copy was last built from these same mods (every file as it was), this game build and this app, and
        is still as that build left it, nothing is built: the game starts from it (rusemod.instance.needs_build). A
        mod changed while the build read it leaves the copy with no record, so the next Play builds again.
        `words`: the app's words in the player's language, for the lines meant for the player (in_words)."""
        from .backup import _claim, _release
        from .instance import forget, needs_build, refuse_if_running, take_back
        say = in_words(say, words)
        refuse_if_running(str(instance))  # before anything is built: a game still running from the copy is said at once
        lock = instance.parent / BUILDING
        lock.parent.mkdir(parents=True, exist_ok=True)
        fd = _claim(lock)
        if fd is None:
            # not a game rule: something else is busy (the game, the other app, a restore)
            raise BuildError("The other app (the Launcher or the Studio) is building the modded game right now: wait "
                             "for it to finish, then try again.")
        result = None
        try:
            made_from = built_from(game, mod_folders)  # before the mods are read, and again after the build
            stamps = mod_stamps(mod_folders)
            if needs_build(str(game), str(instance), made_from) and \
                    not take_back(str(game), str(instance), made_from):
                mods = [load_mod(Path(m)) for m in mod_folders]
                keep_order(mods)
                say(f"Building the modded copy of R.U.S.E. for {name} in {instance}…")
                result = build_and_write(game, mods, instance=instance, say=say, cache=build_cache(),
                                         built_from=made_from)
                if built_from(game, mod_folders)["key"] != made_from["key"] or mod_stamps(mod_folders) != stamps:
                    forget(str(instance))  # changed while the build read it: the copy may hold some of each
            else:
                say(Note("play_unchanged"))
        finally:
            _release(lock, fd)
        if result is not None and result.errors:
            exc = BuildError("These mods have errors (listed above). Nothing was changed.")
            # what the apps show one by one, each with its fix when there is one (ruse_studio test_problems)
            exc.errors, exc.order = [f.message for f in result.errors], list(result.order)
            raise exc
        exe = next((p for p in instance.iterdir() if p.name.lower() == "ruse.exe"), None) if instance.is_dir() else None
        if exe is None:
            raise BuildError(f"The modded copy at {instance} has no RUSE.exe.")
        if not self._steam(say):
            raise BuildError("Steam didn't start. Start Steam, then try again.")
        say("Starting R.U.S.E. from the modded copy…")
        self.start_game(exe)

    def _steam(self, say) -> bool:
        if self.steam_running():
            return True
        say("Starting Steam…")
        self.open_url(STEAM_OPEN)
        for _ in range(60):
            self.wait(1)
            if self.steam_running():
                return True
        return False
