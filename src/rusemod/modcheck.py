"""The mod check, for both apps: every file of a mod folder read the way the build reads it, before the game build
stops at the first mistake. The Studio runs it when a mod is picked and before Test in game; the launcher when a mod
is added. Each problem says what's wrong in plain words, and names the fix the window can offer:

- "set_aside": a broken map file can be renamed <name>.broken.toml (never lost) so the mod works without it;
- "rename_to": a map folder named after the map's title (maps/Blitz) is the pack it means (maps/SuperCrossRoads4).
"""
from __future__ import annotations

import re
from pathlib import Path

from .build import MAP_FILES, BuildError, load_mod, read_map_file
from .patch import PROP_KINDS
from .plainproblems import LIST_FILES
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
        named = list_file_in(folder, str(exc))
        if named:   # a file of the mod's lists (build-menu groups, animations): its own problem, Set aside offered
            problems.append({"file": named, "problem": str(exc), "set_aside": True})
        elif not any(p["file"] and p["file"] in str(exc) for p in problems):
            problems.append({"file": None, "problem": str(exc), "set_aside": False})
    return problems



def list_file_in(folder: Path, text: str) -> str | None:
    """The LIST_FILES file that `text` (a build error's words) is about and that is there in `folder`; None otherwise."""
    said = text.replace("\\", "/")
    for rel in LIST_FILES:
        if re.search(rf"(?:^|[\s/]){re.escape(rel)}:", said) and (Path(folder) / rel).is_file():
            return rel
    return None


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


def made_by(folder: Path) -> set:
    """The objects the mod in `folder` makes (the names its files create or clone), empty when it can't be read (the
    check of its files says what is wrong with it)."""
    try:
        _info, ops = load_mod(Path(folder))
    except (BuildError, RndfError, OSError):
        return set()
    return {op.target.partition(":")[0] for op in ops if op.kind in ("create", "clone") and op.target}


def build_problems(folder: Path, has, also_made=()) -> list[dict]:
    """The two mistakes the build stops on that the files' check above doesn't find, looked for the quick way (the
    owner's 11 A, 2026-11-26: the quick checks only, before the build starts; never a full dry build): a change to an
    object the game hasn't got and no mod makes (the build's own words: patch.Engine._missing), and a copy of a model
    left by a unit nobody makes any more (the build's words, rusemod.build unit_own_copies). `has(name)`: whether the
    game has the object `name` ("$/GFX/Everything/..."); `also_made`: what the other folders built with this one make.
    [{"file", "problem", "set_aside": False}] and, for a left-over copy, "leftover": the unit. Left out: a mod that
    depends on or optionally uses another (what it patches may be that one's: the build says), a change guarded by
    `when`, and one that names its objects by class (`@Class`, `every`); the build still stops on those, as before."""
    folder = Path(folder)
    try:
        info, ops = load_mod(folder)
    except (BuildError, RndfError, OSError):
        return []   # (the files' check says what is wrong with it)
    made = {op.target.partition(":")[0] for op in ops if op.kind in ("create", "clone") and op.target} | set(also_made)
    out = []
    if not (info.depends or info.optional):
        for op in ops:
            if op.when or op.every:
                continue
            if op.kind in PROP_KINDS:
                verb, target = "patches", op.target
            elif op.kind == "delobj":
                verb, target = "deletes", op.target
            elif op.kind == "clone":
                verb, target = "clones", op.source
            else:
                continue
            if not target or target.startswith("@"):
                continue
            name = target.partition(":")[0]
            if name in made or has(name):
                continue
            out.append({"file": op.file or None, "set_aside": False,
                        "problem": f"{op.at()} {verb} {name}, which doesn't exist in this game build (after a game "
                                   f"update, this needs a rebase)"})
    from .holding import skip_of
    from .unitmodel import COPY, MODELS
    tails = {n.rsplit("/", 1)[-1] for n in made}
    skip = skip_of(folder)
    models = folder / MODELS
    for f in sorted(models.glob("*" + COPY)) if models.is_dir() else []:
        unit = f.name[:-len(COPY)]
        if (skip and skip(f)) or unit in tails or has(f"$/GFX/Everything/{unit}"):
            continue
        out.append({"file": f"{MODELS.as_posix()}/{f.name}", "set_aside": False, "leftover": unit,
                    "problem": f"{info.id}: {MODELS.as_posix()}/{f.name}: no mod in the set makes a unit {unit}, and "
                               f"the game has none of that name. If {unit} was deleted from this mod, this file was "
                               f"left behind: in the Studio, click Take out what it left under this mistake in Test "
                               f"in game's log, or delete this file"})
    return out
