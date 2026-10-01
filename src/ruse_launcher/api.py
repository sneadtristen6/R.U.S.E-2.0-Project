"""What the launcher's screens can ask for (PLAN.md L5). Every method takes and returns plain JSON-friendly data, so the
same class serves the window (JavaScript calls `window.pywebview.api.<method>()`) and the tests.

Long jobs (building a modded copy, starting the game) run in the background: `play()` returns a job id, and the
screen asks `job(id)` for progress until it's done.

Players never touch a file (Launcher 0.2):
- The **mod library** (`library.py`) holds the mods a player added, from a folder or a `.zip`, checked first.
- **Mod sets** are made on screen (new, edit, rename, duplicate, delete) and stored by the launcher itself, one TOML
  file each in `<home>/sets/`, e.g. `ruse2.toml`:

      name = "RUSE 2.0"
      description = ""
      mods = ["ruse2-core", "ruse2-china"]   # mods of the library by id, in the order they load; a mod folder's path
                                             # (relative paths start at this file) still works for hand-written sets

  Every call that changes something returns the fresh lists, so the screen never waits for a restart.
- Before Play, `set_check` says which of a set's mods don't go together (rusemod.rmod.clashes): hard clashes disable
  Play (the build would refuse them anyway), soft ones are shown as the later mod winning.
"""
from __future__ import annotations

import functools
import json
import locale
import os
import re
import sys
import time
import tomllib
from pathlib import Path

from rusemod import mod_index
from rusemod import play as game_start, schema
from rusemod.community import CommunityCalls
from rusemod.update import UpdateCalls
from rusemod.build import BuildError
from rusemod.loadorder import match as match_order, parse as parse_order, share_text
from rusemod.mod_index import DEFAULT_URL, ModIndexError, size_text, states
from rusemod.package import PackageError
from rusemod.rmod import best_order as rmod_best_order, clashes as rmod_clashes, data_layout, overwritten as rmod_overwritten, sizes as rmod_sizes
from rusemod.home import PrefsCalls, default_home, game_dir as find_game_dir, save_settings, settings
from rusemod.play import Starter, instances_dir
from rusemod.rndf import RndfError
from rusemod.steam import build_of, find_game
from rusemod.webui import Job, job_view

from .library import MANIFEST, Library, LibraryError, read_info
from . import __version__

_SET_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VANILLA = "vanilla"
MOD_FILES = ("Mods (*.rusemod;*.rmod;*.zip;*.toml)", "All files (*.*)")  # the file dialog's filter: a mod file
# (.rusemod, the Studio's export), a community .rmod, a .zip of a mod folder, or a mod's own mod.toml


class LauncherError(Exception):
    """A problem the player can act on; the message says what to do next."""


# --- the screen's words ---
@functools.cache
def _words() -> dict:
    return tomllib.loads(Path(__file__).with_name("words.toml").read_text(encoding="utf-8"))


def words(lang: str = "us") -> dict:
    """The launcher's own words in `lang` (English for anything missing)."""
    return {key: texts.get(lang) or texts["us"] for key, texts in _words().items()}


_CODES = {"en": "us", "fr": "fr", "de": "ger", "it": "ita", "es": "spa", "pl": "pol", "ru": "ru", "cs": "cz",
          "ja": "jpn", "zh": "sc"}


def language_code(tag: str) -> str:
    """A language tag as Windows or Python gives it ("fr-FR", "de_DE", "zh_CN") -> the game's code, or "us"."""
    head = re.split(r"[-_.@]", (tag or "").strip().lower())[0]
    return _CODES.get(head, "us")


def pc_language() -> str:
    """The language this PC shows its own screens in, as a tag."""
    if sys.platform == "win32":
        import ctypes
        return locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "en")
    return locale.getlocale()[0] or os.environ.get("LANG", "") or "en"


class LauncherApi(UpdateCalls, PrefsCalls, CommunityCalls):
    """The launcher's back end. The arguments replace the real world in tests: the game folder, the launcher's own
    folder, where modded copies go, how links, the game and Steam get started, and the window's dialogs."""

    UPDATE_APP, UPDATE_VERSION = "launcher", __version__  # rusemod.update: the app looks for its newer releases
    PREFS_APP = "launcher"  # rusemod.home: the language, kept in settings.json

    def __init__(self, game_dir=None, home=None, instances=None, open_url=game_start.open_url,
                 start_game=game_start.start_game, steam_running=game_start.steam_running, find=find_game,
                 wait=time.sleep, pick_folder=None, pick_file=None, ui_language=pc_language, index_url=None):
        self._game_dir = Path(game_dir) if game_dir else None
        self._home = Path(home) if home else default_home()
        self._instances = Path(instances) if instances else None
        self._open_url, self._find = open_url, find
        self._starter = Starter(open_url, start_game, steam_running, wait)
        self._pick_folder = pick_folder  # set by the window: a "choose folder" dialog; returns a path or None
        self._pick_file = pick_file      # set by the window: a "choose file" dialog; returns a path or None
        self._ui_language = ui_language
        self._library = Library(self._home / "library")
        self._jobs: dict[str, Job] = {}
        self._index_url_given = index_url   # tests: a local web server instead of the mod index on GitHub
        self._index: mod_index.IndexResult | None = None  # the mod list as last fetched, for search and installs

    # --- words ---
    def languages(self) -> list[dict]:
        return [lang for lang in schema.languages() if lang["code"] != schema.BASE]

    def default_language(self) -> str:
        """The language to start in: this PC's, when the game has it; English otherwise."""
        try:
            return language_code(self._ui_language())
        except Exception:  # noqa: BLE001  (a PC whose language can't be read still gets a launcher)
            return "us"

    def strings(self, lang: str = "us") -> dict:
        return words(lang)

    # --- the game ---
    def _game(self) -> tuple[Path | None, dict]:
        if self._game_dir:
            return self._game_dir, {}
        return find_game_dir(self._home, self._find)

    def status(self) -> dict:
        """Where the game is, which build, and a sentence for the screen."""
        game, found = self._game()
        if game is None or not game.is_dir():
            return {"found": False, "message": "We couldn't find R.U.S.E. Is it installed through Steam?"}
        build = found.get("build_id") or build_of(game) or "?"
        drive = game.drive or game.anchor
        return {"found": True, "game_dir": str(game), "build": build, "branch": found.get("branch", ""),
                "drive": drive, "message": f"Found R.U.S.E. on {drive} (build {build})"}

    def choose_game_folder(self) -> dict:
        """Ask for the game folder (when Steam can't tell us). It must hold RUSE.exe."""
        if self._pick_folder is None:
            return self.status()
        folder = self._pick_folder()
        if not folder:
            return self.status()
        if not Path(folder, "RUSE.exe").is_file():
            status = self.status()
            status["message"] = f"{folder} doesn't have RUSE.exe in it. Pick the R.U.S.E folder itself."
            return status
        values = settings(self._home)
        values["game_dir"] = str(folder)  # the Studio uses it too
        save_settings(self._home, values)
        return self.status()

    # --- the mod library ---
    def library(self) -> list[dict]:
        """The mods the player added, by name: id, name, version, author, description, the game builds they were
        made for, and how many mod sets use each."""
        used: dict[str, int] = {}
        for s in self._read_sets():
            for entry in s["mods"]:
                used[entry] = used.get(entry, 0) + 1
        return [m | {"used_in": used.get(m["id"], 0)} for m in self._library.mods()]

    def _lists(self, **extra) -> dict:
        return {"library": self.library(), "sets": self.mod_sets(), **extra}

    def add_mod(self, path: str) -> dict:
        """Add a mod (a folder with mod.toml, that file, or a .zip of the folder) to the library, after checking it.
        Returns the fresh lists, the mod, and whether it replaced an older copy of the same mod."""
        try:
            info, replaced = self._library.add(path)
        except LibraryError as exc:
            raise LauncherError(str(exc)) from None
        return self._lists(mod=info, replaced=replaced, problems=self._mod_problems(info))

    def _mod_problems(self, info: dict) -> list:
        """The mod check (rusemod.modcheck) on a mod just added: what Play would stop at, or map files the build
        would skip, said now (the mod stays in the library; its author has the fix)."""
        folder = Path(info.get("path") or "")
        if not info.get("path") or not folder.is_dir():
            return []  # an .rmod is one file, checked by its own engine
        from rusemod.modcheck import check_mod_folder
        return check_mod_folder(folder, self._game()[0])

    def add_mod_file(self) -> dict:
        """Ask for a mod file (the window's dialog), then add it. Nothing picked: the lists as they are."""
        if self._pick_file is None:
            return self._lists(mod=None, replaced=False)
        chosen = self._pick_file()
        if not chosen:
            return self._lists(mod=None, replaced=False)
        return self.add_mod(chosen)

    def remove_mod(self, mod_id: str) -> dict:
        try:
            info = self._library.remove(mod_id)
        except LibraryError as exc:
            raise LauncherError(str(exc)) from None
        return self._lists(mod=info)

    # --- browse mods: the mod index (MOD_FORMAT §15) ---
    def _index_url(self) -> str:
        return self._index_url_given or settings(self._home).get("index_url") or DEFAULT_URL

    def browse(self, search: str = "", fresh: bool = False) -> dict:
        """The mods in the mod index, each with its state next to the library ("new", "update" available, or
        "installed"), filtered by `search` (id, name, author, description, tags). The list is fetched once per
        launcher run, or again with `fresh`; offline it is the copy from before, and `message` says so."""
        if fresh or self._index is None:
            try:
                self._index = mod_index.fetch(self._index_url(), self._home / "index")
            except ModIndexError as exc:
                return {"mods": [], "source": "none", "as_of": "", "message": str(exc), "problems": []}
        result = self._index
        mods = states([dict(m) for m in result.mods], {m["id"]: m["version"] for m in self._library.mods()})
        q = (search or "").strip().lower()
        if q:
            mods = [m for m in mods if q in " ".join([m["id"], m["name"], m["author"], m["description"]] + m["tags"]).lower()]
        for m in mods:
            m["size_text"] = size_text(m["size"])
        return {"mods": mods, "source": result.source, "as_of": result.as_of, "message": result.message,
                "problems": list(result.problems)}

    def install_from_index(self, mod_id: str) -> dict:
        """Download a mod from the mod index, check it against the list (size and checksum) and add it to the
        library, in the background. Returns {'job': id}; follow it with job(id)."""
        if self._index is None:
            self.browse()
        entry = next((m for m in (self._index.mods if self._index else []) if m["id"] == mod_id), None)
        if entry is None:
            raise LauncherError(f"There's no mod called {mod_id!r} in the mod list.")

        def work(say):
            say(f"Downloading {entry['name']} {entry['version']} ({size_text(entry['size'])})…")
            file = mod_index.download(entry, self._home / "downloads")
            say("The file matches the mod list (size and checksum).")
            try:
                info, replaced = self._library.add(file)
            except LibraryError as exc:
                raise ModIndexError(str(exc)) from None
            finally:
                file.unlink(missing_ok=True)
            say(f"{info['name']} {info['version']} is in the library" + (" (it replaced the older copy)." if replaced else "."))

        job = Job()
        self._jobs[job.id] = job
        return job.start(work, f"{entry['name']} is in the library.", plain=(ModIndexError, OSError))

    def open_link(self, url: str) -> dict:
        """Open a mod's page in the browser (https links only)."""
        if not str(url).lower().startswith("https://"):
            raise LauncherError("Only https:// links open from here.")
        self._open_url(str(url))
        return {"opened": str(url)}

    # --- mod sets ---
    def _sets_dir(self) -> Path:
        return self._home / "sets"

    def _resolve(self, entry: str, sets_file: Path) -> tuple[Path | None, str | None]:
        """A mod set's entry -> (its folder, or None with why not): a mod of the library by id first, else a folder."""
        in_library = self._library.path_of(entry)
        if in_library is not None:
            return in_library, None
        folder = Path(entry) if Path(entry).is_absolute() else sets_file.parent / entry
        if (folder / MANIFEST).is_file():
            return folder.resolve(), None
        if re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry):
            return None, f"it needs {entry}, which isn't in the library (add it with “Add a mod file…”)"
        return None, f"it needs the mod folder {entry}, which isn't there any more"

    def _read_sets(self) -> list[dict]:
        sets = [{"id": VANILLA, "name": "Vanilla", "description": "The game as Steam installed it.", "mods": [],
                 "folders": [], "mod_names": [], "error": None}]
        folder = self._sets_dir()
        for f in sorted(folder.glob("*.toml"), key=lambda p: p.stem.lower()) if folder.is_dir() else []:
            entry = {"id": f.stem.lower(), "name": f.stem, "description": "", "mods": [], "folders": [],
                     "mod_names": [], "error": None, "file": str(f)}
            if not _SET_ID.match(entry["id"]) or entry["id"] == VANILLA:
                entry["error"] = f"the file name {f.name} must be lowercase letters, digits and '-' (not 'vanilla')"
                sets.append(entry)
                continue
            try:
                data = tomllib.loads(f.read_text(encoding="utf-8"))
                entry["name"] = str(data.get("name", f.stem))
                entry["description"] = str(data.get("description", ""))
                entry["mods"] = [str(m) for m in data.get("mods", [])]
                if not entry["mods"]:
                    entry["error"] = "it lists no mods"
                for m in entry["mods"]:
                    path, why = self._resolve(m, f)
                    entry["folders"].append(str(path) if path else None)
                    entry["mod_names"].append(self._mod_name(m, path))
                    if why and not entry["error"]:
                        entry["error"] = why
            except (OSError, ValueError) as exc:
                entry["error"] = f"{f.name}: {exc}"
            sets.append(entry)
        return sets

    def _mod_name(self, entry: str, path: Path | None) -> str:
        if path is not None and path.parent == self._library.folder:
            try:
                return self._library_names()[entry]
            except KeyError:
                pass
        return Path(entry).name

    def _library_names(self) -> dict[str, str]:
        return {m["id"]: m["name"] for m in self._library.mods()}

    def mod_sets(self) -> list[dict]:
        """Vanilla first, then every mod set, by file name: its mods (library ids, or folders for hand-written
        sets) in load order, their names, and what's wrong with it, if anything."""
        return [{k: v for k, v in s.items() if k not in ("file", "folders")} | {"editable": s["id"] != VANILLA}
                for s in self._read_sets()]

    def _set(self, set_id: str) -> dict:
        chosen = next((s for s in self._read_sets() if s["id"] == set_id), None)
        if chosen is None:
            raise LauncherError(f"There's no mod set called {set_id!r} any more. Pick another one.")
        return chosen

    def _check_mods(self, mods) -> list[str]:
        if not isinstance(mods, list) or not all(isinstance(m, str) and m.strip() for m in mods):
            raise LauncherError("Tick at least one mod for this mod set.")
        mods = [m.strip() for m in mods]
        if not mods:
            raise LauncherError("Tick at least one mod for this mod set.")
        if len(set(mods)) != len(mods):
            raise LauncherError("A mod can only be in a mod set once.")
        for m in mods:
            path, why = self._resolve(m, self._sets_dir() / "x.toml")
            if path is None:
                raise LauncherError(f"This mod set can't be saved: {why}.")
        return mods

    def _write_set(self, set_id: str, name: str, description: str, mods: list[str]) -> None:
        self._sets_dir().mkdir(parents=True, exist_ok=True)
        text = (f"name = {json.dumps(name, ensure_ascii=False)}\n"
                f"description = {json.dumps(description, ensure_ascii=False)}\n"
                f"mods = [{', '.join(json.dumps(m, ensure_ascii=False) for m in mods)}]\n")
        (self._sets_dir() / f"{set_id}.toml").write_text(text, encoding="utf-8")

    def _new_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "mod-set"
        if slug == VANILLA:
            slug = "vanilla-2"
        taken = {s["id"] for s in self._read_sets()}
        set_id, n = slug, 2
        while set_id in taken:
            set_id, n = f"{slug}-{n}", n + 1
        return set_id

    def new_set(self, name: str, mods: list[str], description: str = "") -> dict:
        """A mod set made on screen: its name and the library mods ticked for it, in order. Returns the fresh lists
        and the new set's id, so the screen can select it."""
        name = (name or "").strip()
        if not name:
            raise LauncherError("Give the mod set a name.")
        mods = self._check_mods(mods)
        set_id = self._new_id(name)
        self._write_set(set_id, name, (description or "").strip(), mods)
        return self._lists(set=set_id)

    def save_set(self, set_id: str, name: str, mods: list[str] | None = None, description: str | None = None) -> dict:
        """Change a mod set: its name (a rename), its mods and their order, or both. The id (and so its modded
        copy's folder) stays."""
        chosen = self._set(set_id)
        if set_id == VANILLA:
            raise LauncherError("Vanilla is the game as Steam installed it; it can't be changed. Make a new mod set.")
        name = (name or "").strip() or chosen["name"]
        mods = self._check_mods(mods) if mods is not None else chosen["mods"]
        self._write_set(set_id, name, chosen["description"] if description is None else description.strip(), mods)
        return self._lists(set=set_id)

    def duplicate_set(self, set_id: str, name: str) -> dict:
        """A copy of a mod set under a new name (the screen suggests "<name> (copy)"), selected."""
        chosen = self._set(set_id)
        name = (name or "").strip() or f"{chosen['name']} 2"
        if set_id == VANILLA:
            raise LauncherError("Vanilla has no mods to copy. Make a new mod set instead.")
        new_id = self._new_id(name)
        self._write_set(new_id, name, chosen["description"], chosen["mods"])
        return self._lists(set=new_id)

    def delete_set(self, set_id: str) -> dict:
        chosen = self._set(set_id)
        if set_id == VANILLA:
            raise LauncherError("Vanilla can't be deleted: it's the game itself.")
        Path(chosen["file"]).unlink()
        return self._lists(set=VANILLA)

    # --- do the set's mods work together? (rusemod.rmod.clashes; shown before Play, and while a set is edited) ---
    def check_mods(self, mods: list[str]) -> dict:
        """The clashes between these mods (library ids or folders, in load order): {"hard": [...], "soft": [...]},
        each with the mods' names, what clashes and a sentence. Hard ones mean the set can't be played (the build
        refuses it); soft ones mean a later mod overwrites an earlier one's values. Mods that aren't in the library
        are skipped: the set's own error says so."""
        entries, folders = [], []
        for entry in mods if isinstance(mods, list) else []:
            path, _why = self._resolve(str(entry), self._sets_dir() / "x.toml")
            if path is not None:
                entries.append(entry)
                folders.append(path)
        found = rmod_clashes(folders) if len(folders) > 1 else []
        out = {"hard": [c.view() for c in found if c.hard], "soft": [c.view() for c in found if not c.hard],
               "best": None}
        if any(not c.hard for c in found):
            # the order in which each mod keeps the most of its changes (rusemod.rmod.best_order), when it's another
            order = rmod_best_order(folders)
            if order != sorted(order):
                best = iter([entries[i] for i in order])
                listed = set(entries)
                out["best"] = [next(best) if entry in listed else entry for entry in mods]
                # the mods that lose most of their changes now and wouldn't in the best order
                sizes = rmod_sizes(folders)
                now, after = rmod_overwritten(folders), rmod_overwritten([folders[i] for i in order])
                after = {i: after[k] for k, i in enumerate(order)}
                out["helped"] = [self._mod_name(entries[i], folders[i]) for i in range(len(entries))
                                 if now[i] and now[i] * 2 >= sizes[i] and after[i] * 2 < sizes[i]]
        return out

    def best_order(self, set_id: str) -> dict:
        """Put a mod set's mods in the best order (check_mods' "best") and save it. Returns the fresh lists."""
        chosen = self._set(set_id)
        best = self.check_mods(chosen["mods"])["best"]
        if best is None:
            return self._lists(set=set_id)
        return self.save_set(set_id, chosen["name"], best)

    def set_check(self, set_id: str) -> dict:
        """check_mods for a mod set (Vanilla: nothing clashes)."""
        chosen = self._set(set_id)
        return self.check_mods(chosen["mods"])

    # --- sharing a mod set's load order (rusemod.loadorder: the same text RUSE Mod Manager copies and reads) ---
    def share_set(self, set_id: str) -> dict:
        """A mod set's load order as text to send to a friend: {"text": ...}. RUSE Launcher and RUSE Mod Manager
        both import it."""
        chosen = self._set(set_id)
        if set_id == VANILLA or not chosen["mods"]:
            raise LauncherError("Vanilla has no mods, so there's no load order to share.")
        mods = []
        for entry, folder in zip(chosen["mods"], chosen["folders"]):
            try:
                info = read_info(Path(folder)) if folder else {"name": entry, "version": ""}
            except (OSError, PackageError):
                info = {"name": entry, "version": ""}
            mods.append({"name": info.get("name") or entry, "version": info.get("version", ""),
                         "compat": str(info.get("rmod", "")).lower().endswith(".compat.rmod")})
        game, _found = self._game()
        layout = data_layout(game) if game else "public"
        return {"text": share_text(mods, layout, chosen["name"], (build_of(game) if game else "") or "")}

    def import_check(self, text: str) -> dict:
        """What a pasted load order would give: the mods found in the library (in its order), the missing ones, the
        ones found in another version, and whether it was made for the other game layout."""
        shared = parse_order(text)
        if not shared.entries:
            raise LauncherError("There's no load order in that text. A shared load order starts with a line like "
                                "“=== R.U.S.E. Load Order ===”: copy the whole block.")
        m = match_order(shared, self._library.mods())
        game, _found = self._game()
        layout = data_layout(game) if game else None
        return {"set_name": shared.set_name, "mode": shared.mode, "build": shared.build,
                "wrong_game": bool(layout and shared.mode and layout != shared.mode),
                "found": [{"id": mod["id"], "name": mod["name"], "version": mod["version"]} for _e, mod in m.found],
                "missing": [{"name": e.name, "version": e.version} for e in m.missing],
                "other_version": [{"name": mod["name"], "have": mod["version"], "wanted": e.version}
                                  for e, mod in m.other_version],
                "repeated": [e.name for e in m.repeated]}

    def import_set(self, text: str, name: str = "") -> dict:
        """Make a mod set from a pasted load order: the mods found in the library, in its order. Returns the fresh
        lists (the new set selected) and what the check found."""
        check = self.import_check(text)
        if not check["found"]:
            raise LauncherError("None of these mods are in your library yet. Add them first (Add a mod file… or Browse "
                                "mods), then import the load order again.")
        name = (name or check["set_name"] or "Shared load order").strip()[:60]
        return self.new_set(name, [f["id"] for f in check["found"]]) | {"import": check}

    # --- play ---
    def play(self, set_id: str) -> dict:
        """Start playing a mod set in the background. Returns {'job': id}; follow it with job(id)."""
        chosen = next((s for s in self._read_sets() if s["id"] == set_id), None)
        busy = self._jobs.get(getattr(self, "_play_job", None))
        job = Job()
        self._jobs[job.id] = job
        if busy is not None and busy.state == "running":  # one at a time: two would race for the same copy
            job.state, job.message = "failed", "R.U.S.E. is already being started: wait for it to finish."
        elif chosen is None:
            job.state, job.message = "failed", f"There's no mod set called {set_id!r}."
        elif chosen.get("error"):
            job.state, job.message = "failed", f"The mod set {chosen['name']} has a mistake: {chosen['error']}."
        else:
            self._play_job = job.id
            job.start(lambda say: self._play(chosen, say), "R.U.S.E. is starting.",
                      plain=(BuildError, RndfError, OSError))
        return {"job": job.id}

    def job(self, job_id: str, since: int = 0) -> dict:
        return job_view(self._jobs, job_id, since)

    def _play(self, chosen: dict, say) -> None:
        if chosen["id"] == VANILLA:
            self._starter.vanilla(say)
            return
        game, _found = self._game()
        if game is None:
            raise BuildError("We couldn't find R.U.S.E. Choose its folder first.")
        instance = (self._instances or instances_dir(game)) / chosen["id"]
        self._starter.modded(game, chosen["folders"], instance, chosen["name"], say)
