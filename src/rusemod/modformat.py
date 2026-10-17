"""Which version of the mod format a mod's files are in, and bringing an older mod up to date (the owner, 2026-10-16:
"future-proofing that to where their builds aren't destroyed between updates and there's a way to update their old
build").

A mod's edits are kept as text (its maps/*.toml, src/*.rndf...), so a new Studio never loses them by itself. What
can go wrong between versions:
- a newer Studio changes what something in a file means, or how it's written: an older mod would build differently
  without a word. Then FORMAT goes up by one and UPGRADES gets a step from the old number that rewrites an older
  mod's files the new way (keeping what it meant), run by the player's "Update this mod", a backup taken first;
- an older Studio opens a mod a newer one saved, and its rewrite of a file drops what it doesn't know (Studio
  0.9.8.6 rewrote a scenery.toml with its objects and erase circles alone). The Studio refuses to open a mod of a
  newer format unless the player says so (StudioApi.choose_mod), and every rewrite keeps the tables it doesn't
  write (StudioApi._save_checked `keeps`).

The number is kept in mod.toml as [made_with] format, beside the tool and version that last saved the mod. A mod
with none is format 0 (made before the number was kept). Format 1 (Studio after 0.9.8.6): the mod files as
MOD_FORMAT.md describes them today; from 0 there's nothing to rewrite, only the number to write."""
from __future__ import annotations

import tomllib
import zipfile
from datetime import datetime
from pathlib import Path

from . import package

FORMAT = 1  # the mod format this code reads and writes; one more each time UPGRADES gets a step

# from format n: the step that rewrites a mod's files from n to n + 1, (folder) -> [what it changed, said plainly].
# None: nothing to rewrite (the number alone goes up), so the Studio does it quietly when the mod is opened.
UPGRADES: dict = {0: None}


def format_of(folder) -> int:
    """The mod format a mod folder's files are in: its mod.toml's [made_with] format, 0 when it has none."""
    try:
        data = tomllib.loads((Path(folder) / package.MANIFEST).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return 0
    value = (data.get("made_with") or {}).get("format", 0) if isinstance(data.get("made_with"), dict) else 0
    return value if isinstance(value, int) and value >= 0 else 0


def state(folder) -> dict:
    """{"format": the mod's, "current": FORMAT, "state": "same" | "older" (an upgrade with steps waits) | "quiet" (older,
    with nothing to rewrite) | "newer" (a newer Studio saved it), "steps": how many steps an upgrade would run}."""
    have = format_of(folder)
    if have > FORMAT:
        return {"format": have, "current": FORMAT, "state": "newer", "steps": 0}
    if have == FORMAT:
        return {"format": have, "current": FORMAT, "state": "same", "steps": 0}
    steps = sum(1 for n in range(have, FORMAT) if UPGRADES.get(n) is not None)
    return {"format": have, "current": FORMAT, "state": "older" if steps else "quiet", "steps": steps}


def stamp(folder, tool: str, version: str) -> None:
    """Write the current format, and the tool and version saving the mod, into its mod.toml ([made_with])."""
    package.update_manifest(folder, made_with={"tool": tool, "version": version, "format": FORMAT})


def backup(folder, into) -> Path:
    """A zip of the whole mod folder in the folder `into` (named after the mod, the time and its format), made before
    an upgrade rewrites anything."""
    folder, into = Path(folder), Path(into)
    into.mkdir(parents=True, exist_ok=True)
    when = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    out = into / f"{folder.name}-{when}-format{format_of(folder)}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(folder).as_posix())
    return out


def upgrade(folder, tool: str, version: str, backups) -> dict:
    """Bring a mod of an older format up to FORMAT: a backup first (when any step rewrites a file), then each step in
    turn, then the number. {"from", "to", "backup": the zip or None, "changed": what the steps said}. A mod of a newer
    format is refused (ValueError): this code doesn't know its files."""
    folder = Path(folder)
    have = format_of(folder)
    if have > FORMAT:
        raise ValueError(f"{folder.name} is in mod format {have}, newer than this one ({FORMAT})")
    steps = [UPGRADES.get(n) for n in range(have, FORMAT)]
    saved = backup(folder, backups) if any(s is not None for s in steps) else None
    changed: list[str] = []
    for step in steps:
        if step is not None:
            changed += list(step(folder))
    stamp(folder, tool, version)
    return {"from": have, "to": FORMAT, "backup": str(saved) if saved else None, "changed": changed}
