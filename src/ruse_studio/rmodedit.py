"""An .rmod mod opened in the Studio ("Edit an installed mod…", the owner, 2026-10-10): its copy converted in place
(rusemod.rmodconvert), the value changes the Studio can show written as the Studio's own changes (src/studio.rndf,
ruse_studio.edits), the rest kept as a smaller .rmod next to it."""
from __future__ import annotations

import tomllib
from pathlib import Path

from rusemod import rmodconvert

from .edits import Edit, Literal, ModEdits, REMOVED


def rmod_file(folder) -> str:
    """The .rmod file a mod folder's mod.toml names ([rmod] file), or ""."""
    try:
        data = tomllib.loads((Path(folder) / "mod.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return ""
    table = data.get("rmod")
    return str(table.get("file", "")) if isinstance(table, dict) else ""


def convert_folder(folder, game, index_path) -> rmodconvert.Converted:
    """Convert the .rmod mod in `folder` (a copy: it's changed in place) for the game at `game`, its game index at
    `index_path`. Returns what was converted and what was kept."""
    folder = Path(folder)
    name = rmod_file(folder)
    if not name:
        raise ValueError(f"{folder} has no .rmod to convert")
    converted = rmodconvert.convert(folder / name, game, index_path)
    if converted.changes:
        edits = ModEdits(folder)
        for c in converted.changes:
            value = REMOVED if c.value is None else Literal(c.value)
            edits.edits[(c.target, c.path, c.share)] = Edit(c.target, c.path, value, c.share or None)
        edits.save()
    rmodconvert.write_kept(converted, folder, name)
    return converted
