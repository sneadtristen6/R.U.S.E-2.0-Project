"""The start screen's calls (StudioApi's StartScreenCalls; the owner, 2026-10-18: "When you first load it up, you'll
have the option to load a mod you were previously working on, or start a new mod ... And then an option to just bypass
both"; "always want to skip, like are you an experienced modder? Select here and you can always have this menu skip").
The mods to carry on with, the one worked on last first; whether to skip the screen is a kept preference
("start_skip", rusemod.home.PREF_KEYS), changed on the screen and in Settings."""
from __future__ import annotations

import tomllib
from pathlib import Path

START_MODS_MOST = 30  # mods the screen lists (the Studio's recent list keeps 10; the rest by when they changed)


def _changed(folder: Path) -> float:
    """When a mod was last changed: its newest file's time (its folder's when it has none)."""
    newest = folder.stat().st_mtime
    for f in folder.rglob("*"):
        try:
            if f.is_file():
                newest = max(newest, f.stat().st_mtime)
        except OSError:
            continue
    return newest


def _title(folder: Path) -> str:
    """A mod's own name (its mod.toml's), else its folder's."""
    try:
        name = tomllib.loads((folder / "mod.toml").read_text(encoding="utf-8")).get("mod", {}).get("name")
    except (OSError, ValueError, UnicodeDecodeError):
        name = None
    return str(name).strip() if isinstance(name, str) and name.strip() else folder.name


class StartScreenCalls:
    """Mixed into StudioApi: uses its mods, _settings and KINDS."""

    def start_mods(self) -> dict:
        """The mods the start screen offers to carry on with: {"mods": [{path, name, folder, changed: seconds since
        1970, recent: its place in the Studio's recent list or None}], "current"}: the recent ones first (the one
        worked on last at the top), then the rest by when they last changed. An empty list on a fresh install."""
        listed = self.mods("mod")
        recent = [p for p in self._settings().get(self.KINDS["mod"][1], []) if Path(p, "mod.toml").is_file()]
        rank = {p: n for n, p in enumerate(recent)}
        out = []
        for m in listed["mods"]:
            folder = Path(m["path"])
            try:
                changed = _changed(folder)
            except OSError:
                continue
            out.append({"path": m["path"], "name": _title(folder), "folder": folder.name, "changed": changed,
                        "recent": rank.get(m["path"])})
        out.sort(key=lambda m: (m["recent"] is None, m["recent"] if m["recent"] is not None else -m["changed"]))
        return {"mods": out[:START_MODS_MOST], "current": listed["current"]}
