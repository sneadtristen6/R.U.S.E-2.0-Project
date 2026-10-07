"""The game's map and mission scripts: shown as Python to read (the script viewer of LittleGroove's AI editor), and
changed in a mod (his Mission Script editor), both brought over through his engine (src/ruse_mod_engine). They are the
scripts the game runs on its maps: the campaign's chapters, challenges, Operations and its own tests (IA_Common.dat).
The Studio lists them by map and turns one into text when it is picked (a big one takes a few seconds).

A mod changes a script by bringing its whole text, as the Studio saves it: `scripts/<map>/<part>/<file>.py`, with the
script as the game runs it beside it (`<file>.xyz`), turned back into the game's form with the game's own Python 2.5.1
(the owner, 2026-10-07: "Yes, allow a tool to edit mission scripts"; PLAN decision 23 kept for everything else). A
build with Python 2.5.1 at hand checks that the two still agree; one without it (the Launcher) uses the .xyz. Either
way the build says a mod changes scripts: they run inside the game, so a player should trust the mod's author.

His engine shows scripts with two libraries the apps carry (installers/requirements.txt, THIRD_PARTY_NOTICES.md); a
copy of the apps without them shows why (`missing`), and one without Python 2.5.1 why scripts can't be changed
(`compiler_missing`).
"""
from __future__ import annotations

import re
import struct
from pathlib import Path, PurePosixPath

PACK = "IA_Common.dat"
MOD_DIR = "scripts"  # a mod's mission scripts: scripts/<map>/<part>/<file>.py, and the .xyz the Studio made from it
_NAME = re.compile(r"[A-Za-z0-9_.-]+")


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
    top about itself (its version, the Python it ran on): a compiled script keeps no comments of its own. Texts with
    accented letters come out as escapes the game's Python reads back as the same text (his engine, as corrected
    here on 2026-10-07: 16 of the game's missions didn't compile back as shown before)."""
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


# --- changing a script in a mod ---
class ScriptError(ValueError):
    """A script's text the game's Python can't read: the message says why, `line` where (None: not known)."""

    def __init__(self, message: str, line: int | None = None):
        super().__init__(message)
        self.line = line


def compiler_missing() -> str | None:
    """Why this copy of the apps can't turn a script's text back into the game's form (Python 2.5.1 isn't with it),
    or None when it can."""
    try:
        from ruse_mod_engine import script_logic
        if script_logic.have_compiler():
            return None
    except Exception as exc:  # his engine itself doesn't load
        return f"{type(exc).__name__}: {exc}"
    return "the game's Python (2.5.1) isn't with this copy of the apps"


def compile_text(source: str, original: bytes) -> bytes:
    """A script's text as the game runs it (an .xyz file's bytes), made with the game's own Python 2.5.1 and keeping
    the game's script's own name and header (`original`), so the same text always gives the same bytes. ScriptError
    with the line of the first mistake when the game's Python can't read it."""
    from ruse_mod_engine import script_logic
    try:
        return script_logic.recompile_source_to_xyz(source, xyz_for_meta=original)
    except FileNotFoundError as exc:
        raise ScriptError(compiler_missing() or str(exc)) from None
    except RuntimeError as exc:
        said = str(exc).strip()
        lines = re.findall(r'line (\d+)', said)
        last = said.splitlines()[-1] if said else "the game's Python can't read it"
        # not a game rule: Python 2.5.1's own message about the text
        raise ScriptError(last, int(lines[-1]) if lines else None) from None


def same_script(a: bytes, b: bytes) -> bool:
    """Whether two .xyz files hold the same script (their code; the header's checksum aside)."""
    from ruse_mod_engine import xyz_compile
    try:
        return xyz_compile.unpack(a)["marshal"] == xyz_compile.unpack(b)["marshal"]
    except Exception:  # (ValueError, zlib.error: not a script at all)
        return False


def mod_file(map_: str, part: str, file: str) -> PurePosixPath:
    """Where a mod keeps its text of the game's script `file` (effetmap.xyz) of `map_`'s `part`, as `scripts` names
    them: scripts/<map>/<part>/<file without .xyz>.py (the .xyz the Studio makes from it beside it)."""
    stem = file[:-len(".xyz")] if file.lower().endswith(".xyz") else file
    return PurePosixPath(MOD_DIR, map_, part, stem + ".py")


def is_mod_script(rel: str) -> bool:
    """Whether a file of a mod (its path in the mod, with /) is one of its mission scripts: scripts/<map>/<part>/...,
    a .py text or the .xyz made from it, each name letters, digits, _, - and dots. Nothing else a mod brings may be a
    script or a program (rusemod.build.NOT_IN_MODS)."""
    parts = rel.replace("\\", "/").split("/")
    return (len(parts) >= 4 and parts[0] == MOD_DIR and PurePosixPath(rel).suffix.lower() in (".py", ".xyz")
            and all(_NAME.fullmatch(p) and p not in (".", "..") for p in parts[1:]))


def read_mod(folder: Path) -> dict:
    """A mod folder's mission scripts: {(map, part, file) in lower case: {"rel", "text", "xyz"}}, `file` the game
    script's name (effetmap.xyz), `text` the .py's text (None when only the .xyz is there), `xyz` the .xyz's bytes
    (None when only the text is)."""
    root = Path(folder) / MOD_DIR
    out: dict = {}
    for f in sorted(root.rglob("*")) if root.is_dir() else []:
        rel = f.relative_to(folder).as_posix()
        if not f.is_file() or not is_mod_script(rel):
            continue
        parts = rel.split("/")
        stem = "/".join(parts[3:])[:-len(f.suffix)]
        key = (parts[1].lower(), parts[2].lower(), (stem + ".xyz").lower())
        entry = out.setdefault(key, {"rel": str(PurePosixPath(*parts[:3], stem + ".py")), "text": None, "xyz": None})
        if f.suffix.lower() == ".py":
            entry["text"] = f.read_text(encoding="utf-8")
        else:
            entry["xyz"] = f.read_bytes()
    return out


def build_changes(arc, mods: list) -> tuple[dict, list]:
    """The mods' mission scripts for the game's scripts pack `arc` (IA_Common.dat, as the build has it): `mods` is
    [(mod id, read_mod's dict)] in load order. Returns ({member: the script as the game runs it}, [(level,
    message)]): a script the game hasn't got, two mods changing one script, a text without its .xyz where Python 2.5.1
    isn't at hand, or a text and .xyz that disagree are errors; each mod that changes scripts gets a warning."""
    index = {}
    for e in arc.entries:
        if not e.path.lower().endswith(".xyz"):
            continue
        parts = e.path.replace("\\", "/").split("/")
        at = next((i for i, p in enumerate(parts) if p.lower() == "map"), None)
        if at is not None and len(parts) >= at + 4:
            index[(parts[at + 1].lower(), parts[at + 2].lower(), "/".join(parts[at + 3:]).lower())] = e
    can_compile = compiler_missing() is None
    out: dict = {}
    by: dict = {}
    said: list = []
    for mod_id, scripts in mods:
        mine = []
        for key, s in sorted(scripts.items()):
            where = f"{mod_id}: {s['rel']}"
            e = index.get(key)
            if e is None:
                # not a game rule: the script a mod's file names isn't one of the game's
                said.append(("error", f"{where}: the game has no script {key[2]} in {key[0]}/{key[1]} (the Studio's "
                                      f"script list names them as the game does)"))
                continue
            if e.path in by:
                said.append(("error", f"{where}: {by[e.path]} changes this script too, and only one can run: keep one "
                                      f"of the two mods"))
                continue
            by[e.path] = mod_id
            xyz = s["xyz"]
            if s["text"] is not None and can_compile:
                try:
                    made = compile_text(s["text"], bytes(arc.read(e)))
                except ScriptError as exc:
                    at = f" (line {exc.line})" if exc.line else ""
                    # not a game rule: Python 2.5.1 can't read the mod's text
                    said.append(("error", f"{where}: the game's Python can't read this script{at}: {exc}"))
                    continue
                if xyz is not None and not same_script(xyz, made):
                    said.append(("error", f"{where}: its .xyz isn't what its text makes (changed by another tool?): "
                                          f"open the script in the Studio and save it again"))
                    continue
                xyz = made
            if xyz is None:
                # not a game rule: what this copy of the apps carries
                said.append(("error", f"{where}: only its text is here, and this copy of the apps can't make the "
                                      f"game's form of it ({compiler_missing()}): save it in the Studio, which makes "
                                      f"the .xyz beside it"))
                continue
            out[e.path] = xyz
            mine.append(key)
        if mine:
            names = ", ".join(f"{m}/{p}/{f}" for m, p, f in mine[:3]) + (", …" if len(mine) > 3 else "")
            said.append(("warning", f"{mod_id} changes {len(mine)} of the game's mission scripts ({names}): scripts "
                                    f"run inside the game, so use it only if you trust its author"))
    return out, said
