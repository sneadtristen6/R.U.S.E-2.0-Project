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


# what a window may keep: its language (and whether the player picked it on "Choose your language", rusemod.uilang),
# its map-view keys, small view choices
PREF_KEYS = {"lang", "lang_chosen", "keys", "view"}
PREF_SIZE = 4096                      # characters a kept value may take, as JSON


class PrefsCalls:
    """The window API's own preferences, for both apps (a mixin: the API sets PREFS_APP and has `_home`). Kept in
    settings.json under "prefs" -> app, in the platform folder, so they outlive a restart, an update and a reinstall
    (the window's own storage doesn't: its address changes every time the app starts)."""

    PREFS_APP = ""

    def prefs(self) -> dict:
        """This app's kept preferences: {key: value}."""
        kept = settings(self._home).get("prefs", {}).get(self.PREFS_APP, {})
        return {k: v for k, v in kept.items() if k in PREF_KEYS} if isinstance(kept, dict) else {}

    def set_pref(self, key: str, value) -> dict:
        """Keep one preference (None forgets it). Returns them all."""
        if key not in PREF_KEYS:
            raise ValueError(f"{key!r} isn't a preference the window keeps")
        if len(json.dumps(value)) > PREF_SIZE:
            raise ValueError(f"the value for {key!r} is too big to keep")
        values = settings(self._home)
        mine = values.setdefault("prefs", {}).setdefault(self.PREFS_APP, {})
        if value is None:
            mine.pop(key, None)
        else:
            mine[key] = value
        save_settings(self._home, values)
        return self.prefs()


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
