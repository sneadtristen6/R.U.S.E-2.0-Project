"""The mod check, for both apps: every file of a mod folder read the way the build reads it, before the game build
stops at the first mistake. The Studio runs it when a mod is picked and before Test in game; the launcher when a mod
is added. Each problem says what's wrong in plain words, and names the fix the window can offer:

- "set_aside": a broken map file can be renamed <name>.broken.toml (never lost) so the mod works without it;
- "rename_to": a map folder named after the map's title (maps/Blitz) is the pack it means (maps/SuperCrossRoads4).
"""
from __future__ import annotations

from pathlib import Path

from .build import MAP_FILES, BuildError, load_mod, read_map_file
from .rndf import RndfError
from .terrain import map_list, pack_for


def check_mod_folder(folder: Path, game: Path | None = None) -> list[dict]:
    """The problems of the mod in `folder`: [{"file": its path in the mod (None: the mod as a whole), "problem":
    what's wrong, "set_aside": bool, and "rename_to" for a misnamed map folder}]. `game` (the game folder) lets the
    map folders' names be checked against the game's maps; without it they aren't."""
    folder = Path(folder)
    problems = folder_problems(folder, game)
    maps = folder / "maps"
    for f in sorted(maps.glob("*/*.toml"), key=lambda p: p.as_posix().lower()) if maps.is_dir() else []:
        if f.name in MAP_FILES:
            try:
                read_map_file(folder, f)
            except BuildError as exc:
                problems.append({"file": f.relative_to(folder).as_posix(), "problem": str(exc), "set_aside": True})
    try:  # the rest: mod.toml, the unit edits, the names (the build stops at the first mistake)
        load_mod(folder)
    except (BuildError, RndfError, OSError) as exc:
        if not any(p["file"] and p["file"] in str(exc) for p in problems):
            problems.append({"file": None, "problem": str(exc), "set_aside": False})
    return problems


def folder_problems(folder: Path, game: Path | None = None) -> list[dict]:
    """Map files where the build won't look: loose in maps/ (they go in maps/<pack>/), or in a folder that isn't a
    map's pack name, often the map's title (maps/Blitz for SuperCrossRoads4): "rename_to" is the pack it most
    likely means. A new map's folder (map.toml copy_of) is its own pack name."""
    maps = Path(folder) / "maps"
    if not maps.is_dir():
        return []
    problems = [{"file": f"maps/{f.name}", "set_aside": False,
                 "problem": f"maps/{f.name} is loose in maps/: a map's files go in a folder named after the map's "
                            f"pack, like maps/SuperCrossRoads4/{f.name} for Blitz"}
                for f in sorted(maps.iterdir(), key=lambda p: p.name.lower()) if f.is_file() and f.name in MAP_FILES]
    try:
        known = map_list(game) if game is not None else None
    except (OSError, ValueError, KeyError):
        known = None  # the game's map list can't be read: the build will say it
    if not known:
        return problems
    packs = {m["pack"] for m in known}
    for d in sorted((p for p in maps.iterdir() if p.is_dir()), key=lambda p: p.name.lower()):
        if d.name in packs or not any(d.glob("*.toml")) or _new_map(d):
            continue
        guess = pack_for(d.name, known)
        if guess and guess.lower() == d.name.lower():
            why = f"the pack is written {guess}"
        elif guess:
            why = f"{d.name} is the title of a map whose pack is {guess}"
        else:
            why = "no map in the game has that pack name or title (see the wiki's Map names page)"
        problems.append({"file": f"maps/{d.name}", "set_aside": False, "rename_to": guess,
                         "problem": f"maps/{d.name}: the build only reads folders named after a map's pack, and "
                                    f"{why}."})
    return problems


def _new_map(folder: Path) -> bool:
    """Whether a mod's map folder is a new map of its own (its map.toml says copy_of): its name is the new pack's."""
    import tomllib
    f = folder / "map.toml"
    try:
        return f.is_file() and "copy_of" in tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False  # the file check says what's wrong with it
