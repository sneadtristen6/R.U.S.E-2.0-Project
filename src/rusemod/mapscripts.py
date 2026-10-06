"""The game's map and mission scripts, shown as Python to read: the script viewer of LittleGroove's AI editor
(RUSE-Mod-Manager), brought over through his engine (src/ruse_mod_engine). They are the scripts the game runs on its
maps: the campaign's chapters, challenges, Operations and its own tests (IA_Common.dat). The Studio lists them by map
and turns one into text when it is picked (a big one takes a few seconds). Read only: changing a mission's script is
another of his tools, not here yet.

His engine does it with two libraries the apps carry (installers/requirements.txt, THIRD_PARTY_NOTICES.md); a copy of
the apps without them shows why (`missing`).
"""
from __future__ import annotations

import struct
from pathlib import Path

PACK = "IA_Common.dat"


def _str(b: bytes) -> bytes:
    return b"s" + struct.pack("<i", len(b)) + b


def _tuple(*items: bytes) -> bytes:
    return b"(" + struct.pack("<i", len(items)) + b"".join(items)


def sample() -> bytes:
    """A script of our own, the smallest there is (an empty module, made here, not taken from the game), for checking
    that scripts can be shown at all (the apps' self-test)."""
    from ruse_mod_engine import xyz_compile
    code = (b"c" + struct.pack("<iiii", 0, 0, 1, 0x40) + _str(b"d\x00\x00S") + _tuple(b"N") + _tuple() + _tuple()
            + _tuple() + _tuple() + _str(b"sample.py") + _str(b"<module>") + struct.pack("<i", 1) + _str(b""))
    return xyz_compile.pack(code)  # Python 2.5's layout of a module's code: return None


def text(xyz: bytes) -> str:
    """One script (an .xyz file's bytes) as Python source text, without the lines his engine's library writes at the
    top about itself (its version, the Python it ran on): a compiled script keeps no comments of its own."""
    from ruse_mod_engine import xyz_compile
    lines = xyz_compile.decompile_xyz(xyz).splitlines()
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    return "\n".join(lines).strip("\n") + "\n" if lines else ""


def missing() -> str | None:
    """Why this copy of the apps can't show scripts (a library isn't there), or None when it can."""
    try:
        text(sample())
    except Exception as exc:  # any failure: the library, or one it needs, isn't there or doesn't load
        return f"{type(exc).__name__}: {exc}"
    return None


def scripts(game: Path) -> list[dict]:
    """[{path, map, part, file}] of every script in the game's IA_Common.dat (its newest data revision), by map:
    `map` the map's folder there (a pack name, M04_cotentin's is m04_cotentin), `part` the folder of scripts in it
    (scripting_chapter1, scripting_challenge...), `file` the rest (effetmap.xyz). Empty when the pack isn't found."""
    from .build import find_pack
    from .edat import Edat
    pack = find_pack(game, PACK)
    if pack is None:
        return []
    with Edat.open(str(pack)) as arc:
        paths = [e.path for e in arc.entries if e.path.lower().endswith(".xyz")]
    out = []
    for path in paths:
        parts = path.replace("\\", "/").split("/")
        at = next((i for i, p in enumerate(parts) if p.lower() == "map"), None)
        if at is None or len(parts) < at + 4:
            out.append({"path": path, "map": "", "part": "", "file": "/".join(parts[-2:])})
        else:
            out.append({"path": path, "map": parts[at + 1], "part": parts[at + 2], "file": "/".join(parts[at + 3:])})
    return sorted(out, key=lambda s: (s["map"].lower(), s["part"].lower(), s["file"].lower()))


def read(game: Path, path: str) -> bytes:
    """One script's bytes from the game's IA_Common.dat, by its path there (as `scripts` gives it)."""
    from .build import find_pack
    from .edat import Edat
    pack = find_pack(game, PACK)
    if pack is None:
        raise FileNotFoundError(f"{PACK} isn't in {game}")
    with Edat.open(str(pack)) as arc:
        entry = arc.entry(path)
        if entry is None or not path.lower().endswith(".xyz"):
            raise KeyError(f"{path} isn't one of {PACK}'s scripts")
        return bytes(arc.read(entry))
