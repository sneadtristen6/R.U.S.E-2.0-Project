"""What the launcher's screens can ask for (PLAN.md L5). Every method takes and returns plain JSON-friendly data, so the
same class serves the window (JavaScript calls `window.pywebview.api.<method>()`) and the tests.

Long jobs (building a modded copy, starting the game) run in the background: `play()` returns a job id, and the
screen asks `job(id)` for progress until it's done.

Mod sets (v0.1): one TOML file each in `<home>/sets/`, e.g. `half-price.toml`:

    name = "Half-price test"
    description = "Every building costs half."
    mods = ["D:/RUSE-Mod-Platform/examples/half-price-buildings"]   # mod folders; relative paths start at this file

Installing mods from the mod index replaces the hand-written list later (L6).
"""
from __future__ import annotations

import re
import time
import tomllib
from pathlib import Path

from rusemod import play as game_start
from rusemod.build import BuildError
from rusemod.home import default_home, game_dir as find_game_dir, save_settings, settings
from rusemod.play import Starter, instances_dir
from rusemod.rndf import RndfError
from rusemod.steam import build_of, find_game
from rusemod.webui import Job, job_view

_SET_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class LauncherApi:
    """The launcher's back end. The arguments replace the real world in tests: the game folder, the launcher's own
    folder, where modded copies go, and how links, the game and Steam get started."""

    def __init__(self, game_dir=None, home=None, instances=None, open_url=game_start.open_url,
                 start_game=game_start.start_game, steam_running=game_start.steam_running, find=find_game,
                 wait=time.sleep, pick_folder=None):
        self._game_dir = Path(game_dir) if game_dir else None
        self._home = Path(home) if home else default_home()
        self._instances = Path(instances) if instances else None
        self._open_url, self._find = open_url, find
        self._starter = Starter(open_url, start_game, steam_running, wait)
        self._pick_folder = pick_folder  # set by the window: a "choose folder" dialog; returns a path or None
        self._jobs: dict[str, Job] = {}

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

    # --- mod sets ---
    def _sets_dir(self) -> Path:
        return self._home / "sets"

    def _read_sets(self) -> list[dict]:
        sets = [{"id": "vanilla", "name": "Vanilla", "description": "The game as Steam installed it.", "mods": []}]
        folder = self._sets_dir()
        for f in sorted(folder.glob("*.toml"), key=lambda p: p.stem.lower()) if folder.is_dir() else []:
            entry = {"id": f.stem.lower(), "name": f.stem, "description": "", "mods": [], "file": str(f)}
            if not _SET_ID.match(entry["id"]) or entry["id"] == "vanilla":
                entry["error"] = f"the file name {f.name} must be lowercase letters, digits and '-' (not 'vanilla')"
                sets.append(entry)
                continue
            try:
                data = tomllib.loads(f.read_text(encoding="utf-8"))
                entry["name"] = str(data.get("name", f.stem))
                entry["description"] = str(data.get("description", ""))
                entry["mods"] = [str((f.parent / m).resolve()) if not Path(m).is_absolute() else str(m)
                                 for m in data.get("mods", [])]
                if not entry["mods"]:
                    entry["error"] = "it lists no mods"
            except (OSError, ValueError) as exc:
                entry["error"] = f"{f.name}: {exc}"
            sets.append(entry)
        return sets

    def mod_sets(self) -> list[dict]:
        """Vanilla first, then every mod set in the launcher's sets folder, by file name."""
        return [{k: v for k, v in s.items() if k != "file"} | {"mod_names": [Path(m).name for m in s["mods"]]}
                for s in self._read_sets()]

    def open_sets_folder(self) -> str:
        self._sets_dir().mkdir(parents=True, exist_ok=True)
        self._open_url(str(self._sets_dir()))
        return str(self._sets_dir())

    # --- play ---
    def play(self, set_id: str) -> dict:
        """Start playing a mod set in the background. Returns {'job': id}; follow it with job(id)."""
        chosen = next((s for s in self._read_sets() if s["id"] == set_id), None)
        job = Job()
        self._jobs[job.id] = job
        if chosen is None:
            job.state, job.message = "failed", f"There's no mod set called {set_id!r}."
        elif chosen.get("error"):
            job.state, job.message = "failed", f"The mod set {chosen['name']} has a mistake: {chosen['error']}."
        else:
            job.start(lambda say: self._play(chosen, say), "R.U.S.E. is starting.",
                      plain=(BuildError, RndfError, OSError))
        return {"job": job.id}

    def job(self, job_id: str, since: int = 0) -> dict:
        return job_view(self._jobs, job_id, since)

    def _play(self, chosen: dict, say) -> None:
        if chosen["id"] == "vanilla":
            self._starter.vanilla(say)
            return
        game, _found = self._game()
        if game is None:
            raise BuildError("We couldn't find R.U.S.E. Choose its folder first.")
        instance = (self._instances or instances_dir(game)) / chosen["id"]
        self._starter.modded(game, chosen["mods"], instance, chosen["name"], say)
