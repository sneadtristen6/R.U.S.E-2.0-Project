"""The platform's own folder, shared by the launcher and the Studio: settings, mods, mod sets and caches such as the game
index. Never inside the game folder.

Windows: %LOCALAPPDATA%\\RUSE Mod Platform. Elsewhere: ~/.local/share/ruse-mod-platform. $RUSE_PLATFORM_HOME overrides.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .steam import find_game


def default_home() -> Path:
    if os.environ.get("RUSE_PLATFORM_HOME"):
        return Path(os.environ["RUSE_PLATFORM_HOME"])
    if os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "RUSE Mod Platform"
    return Path.home() / ".local" / "share" / "ruse-mod-platform"


def settings(home: Path) -> dict:
    """The settings both apps share (`settings.json`): for now, the game folder picked by hand."""
    try:
        return json.loads((home / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(home: Path, values: dict) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / "settings.json").write_text(json.dumps(values, indent=2), encoding="utf-8")


def game_dir(home: Path, find=find_game) -> tuple[Path | None, dict]:
    """Where R.U.S.E. is: the folder picked by hand (when Steam couldn't tell), else $RUSE_GAME, else Steam's answer.
    Also returns what Steam said about it (build id, branch), when Steam was asked."""
    chosen = settings(home).get("game_dir")
    if chosen and Path(chosen, "RUSE.exe").is_file():
        return Path(chosen), {}
    if os.environ.get("RUSE_GAME"):
        return Path(os.environ["RUSE_GAME"]), {}
    found = find()
    return (Path(found["game_dir"]), found) if found else (None, {})
