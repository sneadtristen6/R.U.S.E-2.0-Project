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

import json
import os
import re
import subprocess
import sys
import threading
import time
import tomllib
import webbrowser
from pathlib import Path

from ..build import BuildError, build_and_write, load_mod
from ..home import default_home
from ..webui import Job
from ..rndf import RndfError
from ..steam import build_of, find_game

STEAM_PLAY = "steam://rungameid/21970"
STEAM_OPEN = "steam://open/main"
_SET_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _open_url(url: str) -> None:
    if sys.platform == "win32":
        os.startfile(url)  # steam:// links and folders open with their Windows handler
    else:
        webbrowser.open(url)


def _start_game(exe: Path) -> None:
    subprocess.Popen([str(exe)], cwd=str(exe.parent))


def _steam_running() -> bool:
    if sys.platform != "win32":
        return True
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"], capture_output=True, text=True)
    return "steam.exe" in out.stdout.lower()


class LauncherApi:
    """The launcher's back end. The arguments replace the real world in tests: the game folder, the launcher's own
    folder, where modded copies go, and how links, the game and Steam get started."""

    def __init__(self, game_dir=None, home=None, instances=None, open_url=_open_url, start_game=_start_game,
                 steam_running=_steam_running, find=find_game, wait=time.sleep, pick_folder=None):
        self._game_dir = Path(game_dir) if game_dir else None
        self._home = Path(home) if home else default_home()
        self._instances = Path(instances) if instances else None
        self._open_url, self._start_game = open_url, start_game
        self._steam_running, self._find, self._wait = steam_running, find, wait
        self._pick_folder = pick_folder  # set by the window: a "choose folder" dialog; returns a path or None
        self._jobs: dict[str, Job] = {}

    # --- the game ---
    def _settings(self) -> dict:
        try:
            return json.loads((self._home / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self, settings: dict) -> None:
        self._home.mkdir(parents=True, exist_ok=True)
        (self._home / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

    def _game(self) -> tuple[Path | None, dict]:
        if self._game_dir:
            return self._game_dir, {}
        chosen = self._settings().get("game_dir")
        if chosen and Path(chosen, "RUSE.exe").is_file():
            return Path(chosen), {}
        if os.environ.get("RUSE_GAME"):
            return Path(os.environ["RUSE_GAME"]), {}
        found = self._find()
        return (Path(found["game_dir"]), found) if found else (None, {})

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
        settings = self._settings()
        settings["game_dir"] = str(folder)
        self._save_settings(settings)
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
    def _instances_dir(self, game: Path) -> Path:
        return self._instances or Path(game.anchor) / "RUSE-Instances"

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
            threading.Thread(target=self._play, args=(job, chosen), daemon=True).start()
        return {"job": job.id}

    def play_folders(self, name: str, folders: list[str], copy_id: str) -> dict:
        """Build these mod folders into the modded copy `copy_id` and start the game from it (the Studio's Play)."""
        job = Job()
        self._jobs[job.id] = job
        chosen = {"id": copy_id, "name": name, "mods": [str(f) for f in folders]}
        threading.Thread(target=self._play, args=(job, chosen), daemon=True).start()
        return {"job": job.id}

    def job(self, job_id: str, since: int = 0) -> dict:
        job = self._jobs.get(job_id)
        return job.view(since) if job else {"id": job_id, "state": "failed", "message": "unknown job", "lines": [],
                                            "count": 0}

    def _ensure_steam(self, job: Job) -> bool:
        if self._steam_running():
            return True
        job.say("Starting Steam…")
        self._open_url(STEAM_OPEN)
        for _ in range(60):
            self._wait(1)
            if self._steam_running():
                return True
        return False

    def _play(self, job: Job, chosen: dict) -> None:
        try:
            if chosen["id"] == "vanilla":
                job.say("Starting R.U.S.E. through Steam…")
                self._open_url(STEAM_PLAY)
            else:
                game, _found = self._game()
                if game is None:
                    raise BuildError("We couldn't find R.U.S.E. Choose its folder first.")
                mods = [load_mod(Path(m)) for m in chosen["mods"]]
                instance = self._instances_dir(game) / chosen["id"]
                job.say(f"Building the modded copy of R.U.S.E. for {chosen['name']} in {instance}…")
                result = build_and_write(game, mods, instance=instance, say=job.say)
                if result.errors:
                    raise BuildError("These mods have errors (listed above). Nothing was changed.")
                exe = next((p for p in instance.iterdir() if p.name.lower() == "ruse.exe"), None) \
                    if instance.is_dir() else None
                if exe is None:
                    raise BuildError(f"The modded copy at {instance} has no RUSE.exe.")
                if not self._ensure_steam(job):
                    raise BuildError("Steam didn't start. Start Steam, then press Play again.")
                job.say("Starting R.U.S.E. from the modded copy…")
                self._start_game(exe)
            job.state, job.message = "done", "R.U.S.E. is starting."
        except (BuildError, RndfError, OSError) as exc:
            job.state, job.message = "failed", str(exc)
        except Exception as exc:  # anything unexpected still ends the job, with the error for a bug report
            job.state, job.message = "failed", f"Something went wrong: {type(exc).__name__}: {exc}"
