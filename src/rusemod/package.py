"""A mod as one file (docs/MOD_FORMAT.md §2): the mod folder zipped, named `<id>-<version>.rusemod`. Both apps use
this module: the Studio packs ("Export mod…"), the launcher checks and unpacks ("Add a mod file…").

A package is checked before anything is unpacked: it must hold one mod folder (`mod.toml` at the top, or inside one
folder), nothing that could run (scripts or programs, PLAN.md decision 23), nothing that would land outside the target
folder, and a size that makes sense for data files; then the mod is read the way a build reads it. Every problem is a
PackageError whose message is written for the person holding the file.

The manifest inside the package carries the game build the mod was made on and the mod's fingerprint (§12), written
by `pack()` into the folder's own `mod.toml` first, so the next export starts from them.

No folder of the maker's PC goes out in a package (FL-110): the owner, 2026-11-12, asked what Export should do with
the full path of each imported model's source file in its record (often C:\\Users\\<his Windows name>\\...), answered
"Keep file name only": Export writes only the file's own name, never a folder. `pack()` does that only in the fields
the Studio itself writes a path of the PC into (STUDIO_PATHS, packed_bytes): a model's record ("from", and the
pictures its report names), the data inside a .glb model the Studio made from a scenery or building model (its
source's path), and a map's import record (the folders it was made from). The file's own name and every other byte stay as they were.
A modder's own README (README.md, and any README of his in the mod's folders: is_readme) goes out with each folder
path in it cut to the file's own name (the owner, 2026-11-13, asked "A folder path in a modder's own README, in an
exported mod: cut it to the file name, or keep it with a warning?", answered "cut to file name"): only the path's
folders go, every word around it and every other byte stays (readme_paths_out), and Export says each cut. A path that
ends at a user's own folder (C:\\Users\\<name> and the like) is taken out whole, the user's name with it (his answer to
"... keeps the user name. Take those paths out completely?": "Probably take the username path out"). His README is
read in the text encoding it is written in (UTF-8, UTF-16 or UTF-32, or this PC's own: readme_paths_out); one Export
can't read goes out as written, and Export says so. Everything
else a modder wrote is changed nowhere (descriptions, CHANGELOG.md, LICENSE, .rndf, .csv, notes, credits: byte for
byte; his answer to "Full paths elsewhere in a modder's own text, such as their mod's description: only warn and never
change them, as now?" was "yes only warn"): a text naming this PC's home folder goes out as written, and Export says so
(home_named). The mod's own files on the maker's PC keep theirs: Resize and Move fit a model again from the file its
record names, and his README in the mod stays as he wrote it.
"""
from __future__ import annotations

import codecs
import errno
import json
import locale
import os
import re
import shutil
import struct
import tempfile
import tomllib
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

from .build import NOT_IN_MODS, BuildError, load_mod
from .mapscripts import is_mod_script  # the game's mission scripts a mod changes (MOD_FORMAT §9): its only scripts
from .menugroups import FILE as MENU_GROUPS
from .rndf import RndfError

EXTENSION = ".rusemod"
MANIFEST = "mod.toml"
SIZE_LIMIT = 500_000_000  # bytes unpacked: a mod of data files is a few MB; anything near this isn't one
# the era units a mod has (the Studio's ruse_studio.era_units CREDITS and INDEX): their makers' credits, as their
# licences ask (the Horse Squad's line too: "your name, sneadtristen6, in that mod's credits"), and which of the mod's
# units they are ({era unit key: its unit's address}), so another player's Studio knows them as added (the owner,
# 2026-11-12: "Take both along"). A record naming no unit stays behind: a mod without era units packs as before.
ERA_CREDITS, ERA_RECORD = "CREDITS-era-units.md", "era_units.json"
TOP_FILES = ("mod.toml", "menus.toml", "depots.toml", "flag-types.toml", MENU_GROUPS, "README.md", "LICENSE",
             "CHANGELOG.md", ERA_CREDITS, ERA_RECORD)  # loose files a package keeps (flag-types.toml: the Studio's
# flag types, so a copy of the mod can still change them; menu_groups.toml: the group of a build list each unit stands
# in, which the build reads)
FOLDERS = ("src", "text", "files", "maps", "scripts")             # folders a package keeps (§2; scripts/: §9)
SKIP = {"__pycache__", ".git", "cache", "build", "dist"}
_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_VERSION = re.compile(r"^\d+(\.\d+){0,2}([-+][0-9A-Za-z.-]+)?$")


class PackageError(Exception):
    """A package that can't be made, read or unpacked; the message says what to do next."""


# --- what a manifest says ---
def info_of(folder) -> dict:
    """What the apps show about a mod folder: from its mod.toml (which must exist)."""
    folder = Path(folder)
    try:
        data = tomllib.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PackageError(f"{folder} isn't a mod: it has no {MANIFEST} in it.") from None
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise PackageError(f"{folder / MANIFEST} can't be read ({exc}).") from None
    return manifest_info(data, folder)


def manifest_info(data: dict, folder=None) -> dict:
    m, game = data.get("mod", {}), data.get("game", {})
    authors = m.get("authors", m.get("author", []))
    authors = [authors] if isinstance(authors, str) else [str(a) for a in authors]
    name = Path(folder).name if folder else ""
    made = data.get("made_with", {}) if isinstance(data.get("made_with"), dict) else {}
    return {"id": str(m.get("id", name)), "name": str(m.get("name") or m.get("id") or name),
            "version": str(m.get("version", "")), "authors": authors, "author": ", ".join(authors),
            "description": str(m.get("description", "")), "builds": [str(b) for b in game.get("builds", [])],
            "data_revision": str(game.get("data_revision", "")), "fingerprint": str(game.get("fingerprint", "")),
            "rmod": str(data.get("rmod", {}).get("file", "")) if isinstance(data.get("rmod"), dict) else "",
            "made_with": f"{made.get('tool', '')} {made.get('version', '')}".strip(),
            "path": str(folder) if folder else ""}


def file_name(info: dict) -> str:
    """The package's file name: `<id>-<version>.rusemod`."""
    return f"{info['id']}-{info['version'] or '0.0.0'}{EXTENSION}"


# --- an edit of someone else's mod (the Studio's "Edit an installed mod…"): [edited_from] in its mod.toml (§3) ---
EDITED_FROM = "edited_from"


def name_key(name) -> str:
    """A mod name as names are compared: case, the forms of accented letters and spaces don't make two different."""
    return " ".join(unicodedata.normalize("NFKC", str(name or "")).casefold().split())


def edited_from(folder) -> dict:
    """The mod a mod folder is an edit of ({id, name, version, authors}), or {} for a mod that isn't one."""
    try:
        data = tomllib.loads((Path(folder) / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return {}
    table = data.get(EDITED_FROM)
    return table if isinstance(table, dict) else {}


def edit_problem(folder) -> str:
    """Why an edit can't go out as it is: its name or id is the original mod's again (the owner, 2026-10-10: an edited
    mod never takes the original's name); "" when it's fine or not an edit."""
    source = edited_from(folder)
    if not source:
        return ""
    try:
        info = info_of(folder)
    except PackageError:
        return ""
    if name_key(info["name"]) == name_key(source.get("name", "")) or info["id"] == source.get("id"):
        return (f"{info['name']} is an edit of {source.get('name') or 'another mod'}, so it can't carry that mod's "
                f"name or id. Give it its own in its mod.toml.")
    return ""


# --- editing a manifest without losing what's in it ---
def set_values(text: str, table: str, values: dict) -> str:
    """`text` (a mod.toml) with `values` set in `[table]`: existing lines keep their place, new keys go at the end
    of the table, a missing table is added at the end. A value of None removes the key. Comments and everything
    else stay as they are. Values: str, bool, int, float, or a list of str."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == f"[{table}]"), None)
    if start is None:
        if not values:
            return text
        block = [f"[{table}]"] + [f"{k} = {_toml(v)}" for k, v in values.items() if v is not None]
        tail = lines + ([""] if lines and lines[-1].strip() else []) + block
        return "\n".join(tail) + "\n"
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^\s*\[", lines[i])), len(lines))
    done = set()
    for i in range(start + 1, end):
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+)(\s*=\s*)", lines[i])
        if m and m.group(2) in values and m.group(2) not in done:
            key = m.group(2)
            done.add(key)
            lines[i] = None if values[key] is None else f"{m.group(1)}{key}{m.group(3)}{_toml(values[key])}"
    last = end
    while last > start + 1 and (lines[last - 1] is None or not lines[last - 1].strip()):
        last -= 1
    new = [f"{k} = {_toml(v)}" for k, v in values.items() if k not in done and v is not None]
    lines[last:last] = new
    return "\n".join(ln for ln in lines if ln is not None) + "\n"


# a character a TOML string can't hold as it is (a control character), or that set_values' splitlines() would read as
# the end of a line (a vertical tab, a form feed, U+001C-U+001E, U+0085, the line and paragraph separators): written as
# \uXXXX, so a character pasted into an author or a description never makes mod.toml unreadable (the export
# scenarios' FE-6: "couldn't update ...mod.toml: Illegal character")
_TOML_ESCAPE = re.compile("[\x00-\x08\x0b-\x1f\x7f\x85\u2028\u2029]")


def _toml(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_toml(x) for x in v) + "]"
    text = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")
    return '"' + _TOML_ESCAPE.sub(lambda m: f"\\u{ord(m.group(0)):04x}", text) + '"'


def update_manifest(folder, mod: dict | None = None, game: dict | None = None,
                    made_with: dict | None = None) -> dict:
    """Set values in a mod folder's mod.toml ([mod], [game] and [made_with] tables) and return the fresh info."""
    path = Path(folder) / MANIFEST
    text = path.read_text(encoding="utf-8")
    new = set_values(set_values(set_values(text, "mod", mod or {}), "game", game or {}), "made_with", made_with or {})
    try:
        tomllib.loads(new)
    except tomllib.TOMLDecodeError as exc:  # can't happen with our own values, but never write a broken manifest
        raise PackageError(f"couldn't update {path}: {exc}") from None
    if new != text:
        path.write_text(new, encoding="utf-8")
    return info_of(folder)


# --- pack ---
# the files the Studio and the build leave beside one of their own while they write it (written whole there first, then
# put in its place: <name>.part, <stem>.part, <name>.<program>.part, <name>.partial, <name>.tmp), found only when a
# program was stopped in between: half made, never read by a build, and one can name a folder of the maker's PC (a model
# record's .part: the one check of 2026-11-13, finding 13), so a package, the Launcher's copy of it and Publish's .zip
# never take one; Export names each it left out (pack's `left_out`)
WORK_ENDINGS = (".part", ".partial", ".tmp")


def is_work_file(name) -> bool:
    """Whether a file called `name` is one the Studio leaves while it writes (WORK_ENDINGS)."""
    return PurePosixPath(str(name).replace("\\", "/")).suffix.lower() in WORK_ENDINGS


def files_of(folder, left_out: list | None = None) -> list[Path]:
    """The files of a mod folder that go into its package: mod.toml and the other loose files of §2 (the era units'
    credits and record among them, a record naming no unit left out), the .rmod a community mod's mod.toml names
    ([rmod] file: the mod itself), and everything under src/, text/, files/, maps/ and scripts/ (never caches, hidden
    files, build output, or a file the Studio left half written: is_work_file; `left_out`, a list, gets each of
    those). A deleted unit's file another program had open, which the Studio takes out later (rusemod.holding), never
    goes either: the build leaves it out too."""
    from .holding import skip_of
    folder = Path(folder)
    skip = skip_of(folder)
    out = [folder / f for f in TOP_FILES if (folder / f).is_file() and (f != ERA_RECORD or _names_a_unit(folder / f))]
    try:
        named = tomllib.loads((folder / MANIFEST).read_text(encoding="utf-8")).get("rmod", {}).get("file")
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError, AttributeError):
        named = None
    if isinstance(named, str) and named == Path(named).name and named.lower().endswith(".rmod") \
            and (folder / named).is_file():
        out.append(folder / named)
    for sub in FOLDERS:
        if (folder / sub).is_dir():
            for root, dirs, names in os.walk(folder / sub):
                dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith("."))
                for n in sorted(names):
                    if n.startswith(".") or (skip is not None and skip(Path(root) / n)):
                        continue
                    if is_work_file(n):
                        if left_out is not None:
                            left_out.append(Path(root) / n)
                        continue
                    out.append(Path(root) / n)
    return out


def _names_a_unit(record: Path) -> bool:
    """Whether a mod's era_units.json names an era unit (the Studio leaves {} once the last is taken out)."""
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and bool(data)


# --- no folder of the maker's PC in a package (FL-110, the owner's "Keep file name only") ---
# Only the fields the Studio itself writes a path of the PC into are changed, each to the file's (or folder's) own
# name, whatever the folder looks like on whatever system: no list of known folders to fall out of, and no guessing at
# paths inside a modder's words (a description, a .rndf, a .csv, a credit, a note go out byte for byte: the round-1
# cleaner that read paths out of any text cut "Made from C:\models\tank.glb, and docs\turret.md tells how." down to
# "Made from turret.md tells how.", the export recheck of 2026-11-12, F2). His README alone is read for paths, by the
# owner's answer of 2026-11-13, and only a path's folders go (readme_paths_out, below).
STUDIO_PATHS = {
    # what the Studio writes where (each place's member, and the words its export line uses for it)
    "record": "files/models/<unit>.json (ruse_studio.api._fit_model): \"from\", the file the model was made from "
              "(always a path); its report's \"file\", and the pictures its report names but didn't find "
              "(\"missing\", the model file's own names for them), wherever the report repeats them (its \"pictures\", \"alpha\", "
              "\"notes\")",
    "model": "a .glb the Studio made from a scenery or building model (rusemod.meshlod): its asset's extras' "
             "\"rusemod_version\" and each mesh named the same, the source's path (and its ring, \"(far)\")",
    "import": "maps/<Pack>/import.toml (rusemod.placebase, the real-place import): [base] folder, engine_run and "
              "engine_code, the folders the map was made from",
}
TEXT_FILES = {".json", ".gltf", ".toml", ".md", ".txt", ".csv", ".rndf", ".ndf", ".xml", ".ini", ".cfg", ".yml",
              ".yaml", ".html", ".htm", ".py"}         # (and LICENSE, which has no ending)
_SEPARATOR = re.compile(r"[\\/]")
# a path that starts at the top of a disk or a home: C:\ or C:/ (any drive), \ or / (a network folder, \\?\, /home,
# /var/home, /Volumes, /opt: any), ~/, a file: address, %USERPROFILE%\ (any such name)
_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|[\\/]|~[\\/]|file:|%[A-Za-z0-9_()]+%[\\/])", re.IGNORECASE)


def own_name(value: str) -> str:
    """The file's (or a folder's) own name in a path the Studio wrote: what follows its last slash or backslash, on
    any system, a trailing slash left aside (C:\\Users\\<name>\\x.glb, /var/home/<name>/x.glb, \\\\server\\share\\
    x.glb, file:///home/<name>/x.glb: x.glb; a scenery model's "D:\\maps\\a.gltf (far)": "a.gltf (far)")."""
    parts = [p for p in _SEPARATOR.split(value) if p]
    return parts[-1] if parts else ""


def is_absolute(value) -> bool:
    """Whether a string a model file or the Studio wrote is a path from the top of a disk or a home (any system)."""
    return isinstance(value, str) and bool(_ABSOLUTE.match(value))


def _named(value, name: str):
    return own_name(value) if isinstance(value, str) and _SEPARATOR.search(value) else value


def _swapped(value, swap: dict, inside: bool = False):
    """`value` with each string in `swap` replaced: whole strings (values and keys); `inside`: also where a string
    holds one (a note naming a picture)."""
    if isinstance(value, str):
        if value in swap:
            return swap[value]
        if inside:
            for old in sorted(swap, key=len, reverse=True):
                value = value.replace(old, swap[old])
        return value
    if isinstance(value, list):
        return [_swapped(v, swap, inside) for v in value]
    if isinstance(value, dict):
        return {swap.get(k, k): _swapped(v, swap, inside) for k, v in value.items()}
    return value


def _record_swap(doc) -> dict:
    """{each path the Studio wrote into a model's record: its own name}; {} when it wrote none."""
    if not isinstance(doc, dict):
        return {}
    swap = {}
    made = doc.get("from")
    if isinstance(made, str) and _SEPARATOR.search(made):
        swap[made] = own_name(made)
    report = doc.get("report")
    if isinstance(report, dict):
        if isinstance(report.get("file"), str) and _SEPARATOR.search(report["file"]):
            swap[report["file"]] = own_name(report["file"])
        for picture in report.get("missing") or ():
            if is_absolute(picture):
                swap[picture] = own_name(picture)
    return swap


def _record_want(doc, swap: dict):
    """The record with its paths named only by their own names: "from" and the report (where the report repeats a
    picture, in its notes too); everything else, "copy_kept" among it (the uniform's text kept for Take it out), as it
    was."""
    want = dict(doc)
    for k in ("from",):
        if isinstance(want.get(k), str):
            want[k] = swap.get(want[k], want[k])
    if isinstance(want.get("report"), dict):
        want["report"] = _swapped(want["report"], swap, inside=True)
    return want


def _json_written(text: str, doc, want, indent) -> str:
    """`text` (the JSON `doc` as written) changed to `want`, which differs from `doc` only in some strings: each such
    string replaced where it's written, every other byte as it was; written anew (as `indent` says) when that can't be
    done (the same string also written where it stays, say)."""
    out = text
    pairs = dict(_pairs(doc, want))
    for old in sorted(pairs, key=len, reverse=True):
        for ascii_only in (True, False):
            out = out.replace(json.dumps(old, ensure_ascii=ascii_only), json.dumps(pairs[old], ensure_ascii=ascii_only))
    try:
        if json.loads(out) == want:
            return out
    except ValueError:
        pass
    return json.dumps(want, indent=indent) if indent is not None else json.dumps(want, separators=(",", ":"))


def _pairs(was, now):
    """Each (string as it was, as it is now) where `now` differs from `was` in a string (value or key)."""
    if isinstance(was, str) and isinstance(now, str):
        if was != now:
            yield was, now
    elif isinstance(was, list) and isinstance(now, list):
        for a, b in zip(was, now):
            yield from _pairs(a, b)
    elif isinstance(was, dict) and isinstance(now, dict):
        for (ka, va), (kb, vb) in zip(was.items(), now.items()):
            if ka != kb:
                yield ka, kb
            yield from _pairs(va, vb)


def _record_out(text: str) -> str | None:
    """A model's record with only file names where the Studio wrote paths, every other byte as it was; None when it
    names none (or isn't a record)."""
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        return None
    swap = _record_swap(doc)
    if not swap:
        return None
    want = _record_want(doc, swap)
    if want == doc:
        return None
    return _json_written(text, doc, want, 1)


def _model_out(raw: bytes) -> bytes | None:
    """A .glb with only its source's own name where the Studio's scenery import wrote the source's path (its asset's
    extras' rusemod_version and each mesh named the same), its binary part and every other field as they were; None
    when it names no such path or isn't a .glb."""
    if len(raw) < 20 or raw[:4] != b"glTF":
        return None
    version, total = struct.unpack_from("<II", raw, 4)
    length, kind = struct.unpack_from("<I4s", raw, 12)
    if kind != b"JSON":
        return None
    try:
        text = raw[20:20 + length].decode("utf-8")
        doc = json.loads(text)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return None
    extras = (doc.get("asset") or {}).get("extras") if isinstance(doc, dict) and isinstance(doc.get("asset"), dict) \
        else None
    source = extras.get("rusemod_version") if isinstance(extras, dict) else None
    if not isinstance(source, str) or not _SEPARATOR.search(source):
        return None
    name = own_name(source)
    want = json.loads(text)
    want["asset"]["extras"]["rusemod_version"] = name
    for mesh in want.get("meshes") or ():
        if isinstance(mesh, dict) and mesh.get("name") == source:
            mesh["name"] = name
    js = _json_written(text.rstrip(" "), doc, want, None).encode("utf-8")
    js += b" " * (-len(js) % 4)
    return (struct.pack("<4sII", b"glTF", version, total + len(js) - length) + struct.pack("<I4s", len(js), b"JSON")
            + js + raw[20 + length:])


_IMPORT_KEYS = ("folder", "engine_run", "engine_code")
_TABLE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
_KEY_LINE = re.compile(r'^(\s*([A-Za-z0-9_-]+)\s*=\s*)("(?:[^"\\]|\\.)*")(\s*(?:#.*)?)$')


def _import_out(text: str) -> str | None:
    """A map's import record (maps/<Pack>/import.toml, written by the real-place import) with only the folders' own
    names in [base] folder, engine_run and engine_code; every other line as it was. None when it isn't such a record
    or names no path."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    if not isinstance(doc.get("made"), dict) or doc["made"].get("importer") != "rusemod.placebase":
        return None
    lines, table, changed = text.splitlines(keepends=True), None, False
    for i, line in enumerate(lines):
        body = line.rstrip("\r\n")
        m = _TABLE.match(body)
        if m:
            table = m.group(1).strip()
            continue
        m = _KEY_LINE.match(body)
        if table != "base" or not m or m.group(2) not in _IMPORT_KEYS:
            continue
        value = tomllib.loads(f"v = {m.group(3)}")["v"]
        if not _SEPARATOR.search(value):
            continue
        lines[i] = (m.group(1) + json.dumps(own_name(value), ensure_ascii=False) + m.group(4)
                    + line[len(body):])
        changed = True
    return "".join(lines) if changed else None


def studio_paths_out(path, name: str | None = None) -> tuple[bytes, str] | None:
    """What a package holds of the mod's file at `path` (`name`: its path inside the mod, as the package names it)
    when the Studio wrote a path of the PC into it (STUDIO_PATHS): (the bytes with only the file's own name there,
    the kind of place: "record", "model" or "import"); None for a file that goes out as it is."""
    path = Path(path)
    name = (name or path.as_posix()).replace("\\", "/")
    suffix = path.suffix.lower()
    if suffix == ".glb":
        out = _model_out(path.read_bytes())
        return (out, "model") if out is not None else None
    parts = name.split("/")
    is_record = suffix == ".json" and len(parts) >= 3 and parts[-3:-1] == ["files", "models"]
    is_import = path.name == "import.toml" and len(parts) >= 3 and parts[-3] == "maps"
    if not (is_record or is_import):
        return None
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return None
    out = _record_out(text) if is_record else _import_out(text)
    return (out.encode("utf-8"), "record" if is_record else "import") if out is not None and out != text else None


def packed_bytes(path, name: str | None = None) -> bytes | None:
    """studio_paths_out's bytes: what a package holds of the file at `path` when that isn't the file as it is."""
    got = studio_paths_out(path, name)
    return got[0] if got is not None else None


# --- a folder path in a modder's own README, cut to the file's own name (the owner, 2026-11-13: "cut to file name") ---
# The 2026-11-12 recheck's F2 is what this must never do again: round 1 cut "Made from C:\models\tank.glb, and
# docs\turret.md tells how." down to "Made from turret.md tells how.", taking the modder's words with the folders. So
# only a path's root and its folders are taken out, the name after them and every word around them stay; a folder is
# read only up to the next slash or backslash, and a run that reads as words more than as a folder's name (a comma, a
# full stop, a semicolon, ! or ? before a space; a word with a file's ending, "tank.glb", before a space; a space at its
# start or end) ends the path before it. A path counts when it starts at the top of a disk or a home (C:\ or C:/ on any
# drive, \\server\ and \\?\, ~/, %NAME%\, file:) and names at least one folder before its last name, or, starting at /
# alone (a slash is common in words: "and/or", "/r/ruse"), at least two. A relative path ("docs\turret.md") is the
# mod's own and stays.
README_STEM = re.compile(r"readme(?:$|[ ._-])", re.IGNORECASE)
_NAME_LETTERS = r"[^\\/:*?\"<>|`\x00-\x1f]"        # a letter of a file's or folder's name (Windows allows none of
#                                                   \/:*?"<>| nor a control; ` is Markdown's, never a name's here)
_BEFORE = r"(?<![^\s\"'`(\[{<=,;*_])"              # at the start, or after a space, a quote, ` a bracket, =, , ; * _
# (and, for a path that ends at a user's own folder only: after a quote or bracket other languages write, or a tag's >)
_BEFORE_USER = r"(?<![^\s\"'`(\[{<>=,;*_“”‘’„‚«»‹›「」『』（）【】《》〈〉])"


def _roots(before: str, more: str = "") -> re.Pattern:
    """Where a path starts (see above), `before` what may stand just before one; `more`, other starts."""
    return re.compile(rf"(?P<file>(?<![A-Za-z0-9])file:/{{2,3}}(?:[A-Za-z]:[\\/]+)?)"
                      rf"|(?P<unc>{before}\\\\(?:\?\\(?:[A-Za-z]:[\\/]+)?)?)"
                      rf"|(?P<drive>(?<![A-Za-z0-9])[A-Za-z]:[\\/]+)"
                      rf"|(?P<home>{before}~[\\/]+)"
                      rf"|(?P<var>{before}%[A-Za-z0-9_()]+%[\\/]+)"
                      rf"|(?P<unix>{before}/(?![/\s])){more}", re.IGNORECASE)


_ROOT = _roots(_BEFORE)
# (where a path to a user's own folder is looked for, _spans: those starts, and \ alone, a path from the top of the
# drive Windows is on, \Users\jane)
_USER_ROOT = _roots(_BEFORE_USER, rf"|(?P<rooted>{_BEFORE_USER}\\(?![\\\s]))"
                                  r"|(?P<smb>(?<![A-Za-z0-9])smb://(?=[^/\s]))")   # (and a share's smb:// address)
_FOLDER_RUN = re.compile(rf"({_NAME_LETTERS}+)([\\/]+)")
_LAST_NAME = re.compile(r"[^\s\\/:*?\"<>|`\x00-\x1f]+")
_WORDS_NOT_A_NAME = re.compile(r"[,;!?.]\s|[^\s.]\.[A-Za-z][A-Za-z0-9]{0,7}\s")

# A path that ends at a user's own folder goes whole, the user's name with it (the owner, 2026-11-13, asked "A path that
# ends at the user folder, such as "C:\Users\Jane Doe", keeps the user name. Take those paths out completely?",
# answered "Probably take the username path out"): the folder right under where a system keeps its users' own folders
# (_users_places), as a path's last name or, with a slash after it, its last folder, in every way a path is written to
# it (the export fix's review, 2026-11-13, found that Git Bash's, WSL's, Cygwin's and a drive's own share's ways kept
# the name):
# - Windows' Users, and Documents and Settings before Vista (WINDOWS_USERS, any case), at the top of a Windows drive,
#   however the path writes that top: C:\ or C:/ on any drive, \ alone (the drive Windows is working on: \Users\jane),
#   \\?\C:\ and \\.\C:\ (Windows' long and device forms),
#   \\?\Volume{...}\ (a drive by its volume's name), %SystemDrive%\ and %HomeDrive%\, file:///C:/, file://localhost/C:/
#   and file:///C|/, a drive's own share (\\server\C$\, file://server/C$/), and as Git Bash (/c/), WSL (/mnt/c/), Cygwin
#   (/cygdrive/c/) and Wine (drive_c/, anywhere in a path) write a Windows drive; and the home of Cygwin and MSYS2 where
#   they install, at the top of a drive (C:\cygwin64\home\, C:\msys64\home\: UNIX_ON_WINDOWS);
# - a server's share of its users' folders (SHARE_USERS, a hidden share's $ too): \\server\Users\,
#   \\?\UNC\server\Users\, \\.\UNC\server\Users\, file://server/Users/, smb://server/Users/, a NAS's \\nas\homes\;
# - Linux's home and a Mac's Users (UNIX_USERS, written as those systems write them: so a web address's /users/me is no
#   user's folder), and /var/home, /usr/home, /export/home (USERS_UNDER), at the top of a Linux or Mac disk: /,
#   file:///, file://localhost/, \\wsl$\<its Linux>\ and \\wsl.localhost\<its Linux>\ (WSL's), a Mac's
#   /Volumes/<disk>/ and /System/Volumes/Data/.
# A folder there that is the system's own, no user's (NOT_A_USER: Windows' Public, Default, Default User and All Users,
# its desktop.ini; a Mac's Shared), or a variable in a name's place (%USERNAME%, $USER, {user}: _VARIABLE), names no
# user: its path is cut to its own name as any other, as before. A folder called home or users anywhere else
# (D:\Home\Mods, D:\Mods\users\list.txt) is any folder: its path is cut to its own name. A path that goes on past a
# user's folder (C:\Users\<name>\Desktop\x.glb) is cut to its own name as before: the user's name is one of its folders,
# so it goes. Such a path is also looked for after a quote or bracket other languages write (“/home/jane”, «...»,
# 「...」) and after a tag's > (_USER_ROOT), where a path that names no user stays as it was.
# Where the name ends, a space in it (Jane Doe): at the slash after it; else at the closing mark of the quotes,
# backticks or brackets the path is written in (any language's: _QUOTES); else after the longer of a user's name known
# exactly (this PC's own, and each one the same text writes with a slash after it or in quotes) and its first word with
# each word after it that starts with a capital letter when the first does (Jane Q Doe), and a name's small words before
# such a word (Jan de Vries, Ludwig van Beethoven: NAME_SMALL_WORDS), as long as Windows lets a user's name be. A user's
# name never holds a character Windows refuses in one, nor ends with a full stop (Microsoft Learn, USER_INFO_0: "User
# account names are limited to 20 characters ... account names cannot be terminated by a period and they cannot include
# commas or any of the following printable characters: ", /, \, [, ], :, |, <, >, +, =, ;, ?, *"), so those stay in the
# text, and so do a ! or ' after it and a bracket it closes: the sentence's own. Export lists each path it took out.
USERS_FOLDERS = frozenset({"users", "home", "documents and settings"})   # (user_of's, as casefold() gives them)
WINDOWS_USERS = frozenset({"users", "documents and settings"})          # (at the top of a Windows drive, casefold)
UNIX_USERS = frozenset({"home", "Users"})          # (at the top of a Linux or Mac disk: as Linux and a Mac write them)
USERS_UNDER = frozenset({"var", "usr", "export"})   # (a Linux or Unix disk's /var/home, /usr/home, /export/home)
UNIX_ON_WINDOWS = frozenset({"cygwin", "cygwin64", "msys32", "msys64"})   # (Cygwin's, MSYS2's own folders, casefold,
#                                                     at the top of a drive where they install: their users' home)
SHARE_USERS = frozenset({"users", "home", "homes", "documents and settings"})   # (a server's share of them, casefold)
NOT_A_USER = frozenset({"public", "default", "default user", "all users", "desktop.ini", "shared", ".localized",
                        "lost+found"})              # (a system's own folders there, casefold: no user's)
NAME_SMALL_WORDS = frozenset({"de", "da", "di", "du", "des", "del", "della", "dos", "das", "van", "von", "der", "den",
                              "ter", "ten", "zu", "la", "le", "bin", "ibn", "al"})   # (a name's own small words)
USER_NAME_MOST = 20                                 # Windows' longest user's name (USER_INFO_0, above)
_DRIVE_END = re.compile(r"(?:^|[\\/])[A-Za-z]:[\\/]+$")   # (a root that ends at a drive: C:\, \\?\C:\, file:///C:/)
# (a path's start that _ROOT reads only up to its drive's colon: \\.\C:\, file://localhost/C:/, file:///C|/)
_DRIVE_AFTER = re.compile(r"(?:\\\\\.\\|file:/{2,3}(?:localhost/+)?)[A-Za-z][:|][\\/]+", re.IGNORECASE)
_DRIVE_VARS = frozenset({"systemdrive", "homedrive"})   # (%SystemDrive%, %HomeDrive%: a drive's top)
_LETTER = re.compile(r"[a-z]")                       # (a drive's letter, as casefold() gives it)
_SHARE_OF_A_DRIVE = re.compile(r"[a-z]\$")           # (a drive's own share, C$)
_WINE_DRIVE = re.compile(r"drive_[a-z]")             # (Wine's C: drive, a folder of its own: drive_c)
_VOLUME = re.compile(r"volume\{[0-9a-f-]+\}")        # (\\?\Volume{...}\: a drive by its volume's name)
_VARIABLE = re.compile(r"%[^%\s]+%|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\{[^{}\s]*\}")   # (%USERNAME%, $USER, {user})
_USER_LETTERS = r'[^\s"/\\\[\]:|<>+=;?*,`\x00-\x1f]'   # a letter of a user's name (` is Markdown's, never a name's)
_USER_WORD = re.compile(_USER_LETTERS + "+")
_USER_NAME = re.compile(rf"{_USER_LETTERS}+(?: {_USER_LETTERS}+)*")
_QUOTES = {'"': '"', "'": "'", "`": "`", "(": ")", "[": "]", "{": "}", "<": ">", ">": "<",
           "\u201c": "\u201d\u201c", "\u2018": "\u2019\u2018", "\u201e": "\u201c\u201d", "\u201a": "\u2018\u2019",
           "\u201d": "\u201d", "\u2019": "\u2019", "\u00ab": "\u00bb", "\u00bb": "\u00ab\u00bb", "\u2039": "\u203a",
           "\u203a": "\u2039\u203a", "\u300c": "\u300d", "\u300e": "\u300f", "\uff08": "\uff09", "\u3010": "\u3011",
           "\u300a": "\u300b", "\u3008": "\u3009"}   # (each opening mark, then what closes it: “…”, „…“, «…», 「…」)


def user_of(home) -> str | None:
    """The user's name in a folder path (this PC's home folder: C:\\Users\\<name>, /home/<name>...), the folder right
    under one of USERS_FOLDERS; None when it has none."""
    parts = [p for p in _SEPARATOR.split(str(home or "")) if p]
    for up, name in zip(parts, parts[1:]):
        if up.casefold() in USERS_FOLDERS:
            return name
    return None


def _name_part(word: str) -> str:
    """A word of a user's name without what reads as the sentence's after it: a full stop (a name never ends with one),
    ! and ', and a ) that closes no ( of the word."""
    while word:
        if word[-1] in ".!'":
            word = word[:-1]
        elif word.endswith(")") and word.count(")") > word.count("("):
            word = word[:-1]
        else:
            break
    return word


def _name_goes_on(text: str, k: int) -> bool:
    """Whether text[k] goes on with the name before it (a letter, a digit, - or _, or a dot before one: .CONTOSO)."""
    if k >= len(text):
        return False
    c = text[k]
    return c.isalnum() or c in "-_" or (c == "." and k + 1 < len(text) and text[k + 1].isalnum())


def _quoted_name(text: str, j: int, before: str) -> str | None:
    """The name of a user's own folder that starts at text[j], when the path is in quotes, backticks or brackets
    (`before`, the character just before the path, opens them: _QUOTES): to the closing mark on the same line, when
    that is a name Windows lets a user have; else None."""
    closers = _QUOTES.get(before)
    if not closers:
        return None
    line = text.find("\n", j)
    ends = [k for k in (text.find(c, j) for c in closers) if k > j and (line == -1 or k < line)]
    name = text[j:min(ends)] if ends else ""
    if name and len(name) <= USER_NAME_MOST and _USER_NAME.fullmatch(name) and not name.endswith("."):
        return name
    return None


def _user_name_end(text: str, j: int, before: str, known: list) -> int | None:
    """Where the name of a user's own folder that starts at text[j], a path's last name, ends (see above): `before`,
    the character just before the path; `known`, the users' names known exactly, longest first. None when no user's
    name starts there."""
    first = _USER_WORD.match(text, j)
    if first is None:
        return None
    quoted = _quoted_name(text, j, before)              # in quotes, backticks or brackets: to the closing mark
    if quoted is not None:
        return j + len(quoted)
    word = _name_part(first.group(0))
    end = j + len(word)
    if word and word[0].isupper() and word == first.group(0):
        k = end                                         # (Jane Doe, Jane Q Doe: each next word with a capital; a
        while text.startswith(" ", k):                  # name's small words before one: Jan de Vries)
            more = _USER_WORD.match(text, k + 1)
            part = _name_part(more.group(0)) if more is not None else ""
            stop = k + 1 + len(part)
            if not part or stop - j > USER_NAME_MOST:
                break
            if part[0].isupper():
                end = k = stop
                if part != more.group(0):               # (the sentence's mark after it: the name ends there)
                    break
            elif part in NAME_SMALL_WORDS and part == more.group(0):
                k = stop                                # (the name goes on only with a word with a capital after it)
            else:
                break
    for name in known:
        k = j + len(name)
        if text[j:k].casefold() == name.casefold() and not _name_goes_on(text, k):
            end = max(end, k)
            break
    return end if end > j else None


def _names_a_user(name: str) -> bool:
    """Whether a folder's name right under where a system keeps its users' folders is a user's: not the system's own
    (NOT_A_USER), nor a variable in a name's place (_VARIABLE)."""
    return name.casefold() not in NOT_A_USER and not _VARIABLE.fullmatch(name)


def _user_at(text: str, j: int) -> bool:
    """_names_a_user for the name that starts at text[j], a path's last name."""
    for own in NOT_A_USER:
        k = j + len(own)
        if text[j:k].casefold() == own and not _name_goes_on(text, k):
            return False
    first = _USER_WORD.match(text, j)
    return first is not None and not _VARIABLE.fullmatch(_name_part(first.group(0)))


def _folders_from(text: str, j: int, forward: bool, server: bool) -> tuple[list, int]:
    """The folders of a path from text[j] on: ([(a folder's name, where it starts, where its slashes end)], where the
    last of them ends). A folder is read only up to the next slash or backslash (_folder_name_ok); `forward`, a path
    written with / only; `server`, its first folder a server's name (which has no space in it)."""
    folders = []
    while True:
        f = _FOLDER_RUN.match(text, j)
        if f is None or not _folder_name_ok(f.group(1)) or (forward and "\\" in f.group(2)) \
                or (server and not folders and any(c.isspace() for c in f.group(1))):
            break
        folders.append((f.group(1), f.start(), f.end()))
        j = f.end()
    return folders, j


def _path_at(text: str, m) -> tuple[list, int]:
    """The folders of the path whose root `m` (_ROOT) found (_folders_from)."""
    # (a path of unix, home and file kinds is written with / only: a \ after "/Iinclude share" says it is a switch and
    # words; a server's name, \\server\, has no space in it)
    return _folders_from(text, m.end(), m.lastgroup in ("unix", "home", "file", "smb"), m.group(0) == "\\\\")


def _users_places(kind: str, root: str, folders: list) -> set:
    """Each k where folders[k], of a path whose root is `root` (of `kind`, _ROOT's group, or "drive" for folders that
    start at a Windows drive's top), is where a system keeps its users' own folders (see above)."""
    names = [f[0] for f in folders]
    low = [n.casefold() for n in names]
    win, unix, server = [], [], None    # (where a Windows drive's top is, a Linux or Mac disk's, a server's name)
    if kind in ("drive", "rooted") or _DRIVE_END.search(root):      # C:\, \\?\C:\, file:///C:/; \ alone
        win.append(0)
    elif kind == "var":                                             # %SystemDrive%\, %HomeDrive%\
        if root.strip("%\\/").casefold() in _DRIVE_VARS:
            win.append(0)
    elif kind == "unix":
        unix.append(0)                                              # /home, /Users
        if len(low) > 1 and _LETTER.fullmatch(low[0]):
            win.append(1)                                           # /c/: Git Bash's (MSYS2's)
        if len(low) > 2 and low[0] in ("mnt", "cygdrive") and _LETTER.fullmatch(low[1]):
            win.append(2)                                           # /mnt/c/: WSL's; /cygdrive/c/: Cygwin's
        if len(names) > 2 and names[0] == "Volumes":
            unix.append(2)                                          # /Volumes/<disk>/: a Mac's other disk
        if names[:3] == ["System", "Volumes", "Data"]:
            unix.append(3)                                          # a Mac's own disk, as it is kept
    elif kind == "file":                                            # (file:/// or file://<a server>/, no drive)
        if root.count("/") >= 3:
            unix.append(0)
        elif low and low[0] == "localhost":
            unix.append(1)
        else:
            server = 0
    elif kind == "smb":                                             # smb://server/share/: a Mac's or Linux's way
        server = 0
    elif kind == "unc":
        if root == "\\\\":
            if low[:1] == ["."]:                                    # \\.\UNC\server\share\ (\\.\C:\: _DRIVE_AFTER)
                server = 2 if low[1:2] == ["unc"] else None
            elif low[:1] in (["wsl$"], ["wsl.localhost"]):
                unix.append(2)                                      # \\wsl$\<its Linux>\: WSL's disk
            else:
                server = 0                                          # \\server\share\
        elif low[:1] == ["unc"]:
            server = 1                                              # \\?\UNC\server\share\
        elif low and _VOLUME.fullmatch(low[0]):
            win.append(1)                                           # \\?\Volume{...}\
    places = set()
    if server is not None and server + 1 < len(low):
        share = low[server + 1]
        if _SHARE_OF_A_DRIVE.fullmatch(share):
            win.append(server + 2)                                  # \\server\C$\: a drive's own share
        elif share.rstrip("$") in SHARE_USERS:
            places.add(server + 1)                                  # \\server\Users\, \\server\users$\, \\nas\homes\
    win += [k + 1 for k, n in enumerate(low) if _WINE_DRIVE.fullmatch(n)]   # .../drive_c/: Wine's C: drive
    for t in win:
        if t < len(low) and low[t] in WINDOWS_USERS:
            places.add(t)
        elif t + 1 < len(low) and low[t] in UNIX_ON_WINDOWS and low[t + 1] == "home":
            places.add(t + 1)                                       # C:\cygwin64\home\, C:\msys64\home\
    for t in unix:
        if t < len(names) and names[t] in UNIX_USERS:
            places.add(t)
        elif t + 1 < len(names) and names[t] in USERS_UNDER and names[t + 1] == "home":
            places.add(t + 1)
    return places


def _read_path(text: str, m) -> tuple[list, int, set]:
    """The path whose root `m` (_ROOT or _USER_ROOT) found: (its folders and where they end, as _path_at gives them,
    and where among them a system keeps its users' folders: _users_places); one that _ROOT reads only up to its drive's
    colon (\\\\.\\C:\\, file://localhost/C:/, file:///C|/: _DRIVE_AFTER) read from its drive's top on."""
    d = _DRIVE_AFTER.match(text, m.start())
    if d is not None and not _DRIVE_END.search(m.group(0)):
        folders, j = _folders_from(text, d.end(), not d.group(0).startswith("\\"), False)
        return folders, j, _users_places("drive", "", folders)
    folders, j = _path_at(text, m)
    return folders, j, _users_places(m.lastgroup, m.group(0), folders)


def _user_folder_end(text: str, m, known: list) -> int | None:
    """Where the path whose root `m` found ends, when it ends at a user's own folder (see above): its last name right
    under where a system keeps its users' folders, or its last folder there with its slash after it; None for any
    other path."""
    folders, j, places = _read_path(text, m)
    if not places:
        return None
    if _LAST_NAME.match(text, j) is not None:
        if len(folders) - 1 not in places or not _user_at(text, j):
            return None
        start = m.start()
        return _user_name_end(text, j, text[start - 1] if start else "", known)
    if len(folders) >= 2 and len(folders) - 2 in places and _names_a_user(folders[-1][0]):
        return folders[-1][2]
    return None


def _users_written(text: str) -> set:
    """Each user's name `text` writes exactly, as a folder right under where a system keeps its users' own folders
    (_users_places): with a slash after it (C:\\Users\\Jane Doe\\Desktop: Jane Doe), or as a path's last name in
    quotes or brackets ("C:\\Users\\jane doe": _quoted_name)."""
    out, pos = set(), 0
    while (m := _USER_ROOT.search(text, pos)) is not None:
        folders, j, places = _read_path(text, m)
        for k in places:
            if k + 1 < len(folders):
                name = folders[k + 1][0]
                if _names_a_user(name) and _USER_NAME.fullmatch(name) and not name.endswith(".") \
                        and (" " not in name or len(name) <= USER_NAME_MOST):
                    out.add(name)
            elif k + 1 == len(folders):
                name = _quoted_name(text, j, text[m.start() - 1] if m.start() else "")
                if name is not None and _names_a_user(name):
                    out.add(name)
        pos = m.start() + 1
    return out


def is_readme(name) -> bool:
    """Whether a member called `name` (its path in the mod) is a README of the modder's: its file name, case aside,
    README, or README followed by a dot, a space, - or _ (README.md, readme.txt, README-fr.md), and a text
    (TEXT_FILES, or no ending)."""
    file = PurePosixPath(str(name).replace("\\", "/")).name
    suffix = PurePosixPath(file).suffix.lower()
    return bool(README_STEM.match(file)) and (suffix in TEXT_FILES or suffix == "" or file.lower() == "readme")


def _folder_name_ok(run: str) -> bool:
    """Whether a run of letters before a slash or backslash reads as a folder's name rather than as words."""
    if not run or run != run.strip() or len(run) > 255:
        return False
    if not any(c.isspace() for c in run):
        return True
    # (with a space in it, words read so: a sentence's stop, a file's ending before a space, a bracket left open, a
    # home's ~: "python (assuming ~guido" in a README of the tools, 2026-11-13, is words between two paths)
    return not (_WORDS_NOT_A_NAME.search(run) or run.count("(") != run.count(")") or "~" in run)


def _spans(text: str, users=()) -> list[tuple[int, int, int, str]]:
    """paths_cut's work: for each path it cuts, in the text's order, (where the path starts, where what goes of it ends,
    where the path as written ends, the name it became: "" for one taken out whole). Only what goes is ever taken
    out of the text: from where the path starts to where what goes ends."""
    spans, pos = [], 0
    known = sorted({u for u in users if u} | _users_written(text), key=len, reverse=True)
    while True:
        m = _ROOT.search(text, pos)
        u = _USER_ROOT.search(text, pos)
        # (a path after a quote or bracket of another language, or a tag's >: looked at only for a user's folder)
        only_user = u is not None and (m is None or u.start() < m.start())
        r = u if only_user else m
        if r is None:
            break
        start = r.start()
        end = _user_folder_end(text, r, known)
        if end is not None:                  # (taken out whole: its user's name goes with it)
            spans.append((start, end, end, ""))
            pos = end
            continue
        folders, j, places = _read_path(text, r)
        if not any(k + 1 < len(folders) and _names_a_user(folders[k + 1][0]) for k in places):
            if only_user:
                pos = start + 1
                continue
            folders, j = _path_at(text, m)  # (each folder: its name, where it starts, where its slashes end)
        # (else a path on past a user's own folder, however it is written: cut to its own name as any other, the
        # user's name going with its folders)
        last = _LAST_NAME.match(text, j)
        last_name = last.group(0) if last is not None else ""
        names = len(folders) + (1 if last_name else 0)
        if names < (3 if r.lastgroup == "unix" else 2):
            pos = start + 1                  # (not a path that names a folder: the words stay, look further on)
            continue
        if last_name:                        # everything before the last name goes
            spans.append((start, j, last.end(), last_name))
            pos = last.end()
        else:                                # the last folder's name stays, with its slash
            spans.append((start, folders[-1][1], folders[-1][2], folders[-1][0]))
            pos = folders[-1][2]
    return spans


def _cut(text: str, spans: list) -> tuple[str, list]:
    """`text` without what goes of each of _spans' paths, and paths_cut's list of what was cut."""
    out, cuts, i = [], [], 0
    for start, gone, end, name in spans:
        out.append(text[i:start])
        cuts.append((text[start:end], name))
        i = gone                             # (the text from there on is kept as written)
    out.append(text[i:])
    return "".join(out), cuts


def paths_cut(text: str, users=()) -> tuple[str, list]:
    """`text` with each folder path in it cut to its own name (see above): (the text, [(the path as written, the name
    it became)] in the text's order). A path whose last name is missing (it ends with a slash) keeps its last folder's
    name, the slash after it as written. A server's name (\\\\server\\share\\...) counts as a folder. A path that ends
    at a user's own folder is taken out whole, the name it became "" (_users_places): `users`, users' names known
    exactly (this PC's own, user_of), say where such a name ends."""
    return _cut(text, _spans(text, users))


_TRAILING = ".,;:!?'\""


def cut_shown(path: str, name: str) -> str:
    """One of paths_cut's cuts as Export's line says it: "C:\\models\\tank.glb → tank.glb", without the full stop,
    comma or bracket after it that the text has (they stayed where they were)."""
    def bare(s: str) -> str:
        s = s.rstrip(_TRAILING)
        while s.endswith(")") and s.count(")") > s.count("("):
            s = s[:-1].rstrip(_TRAILING)
        return s
    return f"{bare(path) or path} \u2192 {bare(name) or name}"


# A README of his is read in the text encoding it is written in (the export fix's review, 2026-11-13: one saved by
# Notepad as "ANSI" or "Unicode" went out with its user's path whole, and Export said nothing): UTF-8; UTF-16 or UTF-32
# with the mark Notepad's "Unicode" puts at its start; else this PC's own (_ansi, Notepad's "ANSI"). Only what goes of
# each path is taken out of its bytes, every other byte as it was (_bytes_without); one none of them reads goes out as
# written, and Export says so (pack's `unread`).
_MARKS = ((codecs.BOM_UTF32_LE, "utf-32-le"), (codecs.BOM_UTF32_BE, "utf-32-be"), (codecs.BOM_UTF8, "utf-8"),
          (codecs.BOM_UTF16_LE, "utf-16-le"), (codecs.BOM_UTF16_BE, "utf-16-be"))
_UNICODE = frozenset({"utf-8", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"})


def _ansi() -> str | None:
    """This PC's own text encoding for a text saved without Unicode (Windows' ANSI code page, which Notepad calls
    "ANSI": cp1252, cp1251, cp932...), as Python names it; None where that is Unicode (UTF-8) or not known."""
    try:
        name = codecs.lookup(locale.getencoding()).name
    except (LookupError, ValueError, AttributeError):
        return None
    return None if name in _UNICODE else name


def _text_of(raw: bytes) -> tuple[str, str] | None:
    """A text file's words and the encoding they are written in (see above): by the mark at its start, else UTF-8,
    else this PC's own (_ansi); a mark stays the text's first character, as UTF-8's always did. None when none of them
    reads it."""
    tries = [enc for mark, enc in _MARKS if raw.startswith(mark)] + ["utf-8", _ansi()]
    for enc in tries:
        if enc is None:
            continue
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return None


def _starts(raw: bytes, enc: str) -> list[int] | None:
    """Where each character of `raw` read as `enc` starts in it, and where the last ends (an encoding of one or more
    bytes a character: this PC's own, _ansi); None when a byte would make more than one character."""
    dec = codecs.getincrementaldecoder(enc)()
    out = [0]
    for i in range(len(raw)):
        got = dec.decode(raw[i:i + 1])
        if len(got) > 1:
            return None
        if got:
            out.append(i + 1)
    return out if not dec.decode(b"", final=True) else None


def _bytes_without(raw: bytes, text: str, enc: str, spans: list) -> bytes | None:
    """`raw` (`text` written in `enc`) without the bytes of each of _spans' parts that go, every other byte as it was;
    None when where a character starts can't be told (_starts), or the bytes left don't read as the text left."""
    if enc in _UNICODE:
        done = [0, 0]                         # (characters and bytes counted so far: each place only once)

        def at(k: int) -> int:
            done[1] += len(text[done[0]:k].encode(enc))
            done[0] = k
            return done[1]
    else:
        starts = _starts(raw, enc)
        if starts is None or len(starts) != len(text) + 1:
            return None
        at = starts.__getitem__
    out, i = [], 0
    for start, gone, _end, _name in spans:
        out.append(raw[i:at(start)])
        i = at(gone)
    out.append(raw[i:])
    data = b"".join(out)
    try:
        if data.decode(enc) != _cut(text, spans)[0]:
            return None
    except UnicodeDecodeError:
        return None
    return data


def readme_paths_out(path, name: str | None = None, users=(), unread: list | None = None) -> tuple[bytes, list] | None:
    """What a package holds of the modder's README at `path` (`name`: its path inside the mod; is_readme) when a
    folder path is in it: (its bytes with each such path cut to its own name, and each one that ends at a user's own
    folder taken out whole, paths_cut's list of what was cut; `users`: paths_cut's), in the text encoding it is written
    in, every other byte as it was (_text_of); None for a file that goes out as it is (no folder path in it, not a
    README, or a text no encoding above reads: then it goes out as written, and `unread`, a list, gets `name`)."""
    path = Path(path)
    if not is_readme(name or path.name):
        return None
    raw = path.read_bytes()
    read = _text_of(raw)
    if read is None:
        if unread is not None:
            unread.append(name or path.name)
        return None
    text, enc = read
    spans = _spans(text, users)
    new, cuts = _cut(text, spans)
    if not cuts or new == text:
        return None
    data = new.encode("utf-8") if enc == "utf-8" else _bytes_without(raw, text, enc, spans)
    if data is None:                          # (can't be cut byte for byte: as written, and said)
        if unread is not None:
            unread.append(name or path.name)
        return None
    return data, cuts


def _home_forms(home) -> list[bytes]:
    """This PC's home folder as a file could write it: as it is, with forward slashes, with each backslash twice; in
    UTF-8, UTF-16, UTF-32 and this PC's own text encoding (_ansi: a name with é or Иван in it is other bytes there;
    the export fix's review, 2026-11-13)."""
    s = str(home or "").rstrip("\\/")
    if len(_SEPARATOR.split(s)) < 2 or len(s) < 4:     # (no folder to look for: "/", "C:")
        return []
    forms = set()
    for enc in [e for e in sorted(_UNICODE) + [_ansi()] if e is not None]:
        for f in {s, s.replace("\\", "/"), s.replace("\\", "\\\\")}:
            try:
                forms.add(f.encode(enc))
            except UnicodeEncodeError:            # (a name this PC's own encoding can't write: not in it, then)
                pass
    return sorted(forms)


def home_named(data: bytes, home) -> bool:
    """Whether a member's bytes as packed name this PC's home folder (`home`, Path.home()) in any of its written forms:
    a modder's text that goes out as he wrote it, which the export says (nothing is changed in it)."""
    return any(form in data for form in _home_forms(home))


def home_shown() -> str:
    """This PC's home folder, as pack looks for it (Path.home()), for the export's line."""
    try:
        return str(Path.home())
    except RuntimeError:
        return ""


def pack(folder, out, *, build_id: str | None = None, data_revision: str | None = None,
         fingerprint: str | None = None, solved: dict | None = None, made_with: dict | None = None,
         cleaned: list | None = None, kinds: dict | None = None, home_in: list | None = None,
         home=None, left_out: list | None = None, cuts: dict | None = None, unread: list | None = None) -> Path:
    """Zip the mod at `folder` into one file. `out` is the file to write, or a folder to put `<id>-<version>.rusemod`
    in. The mod is checked first (its manifest, and that it reads like a build would); the build it was made on and
    its fingerprint, when given, are written into the manifest (the folder's and the package's) under [game], and the
    tool that made it (`made_with`: {"tool", "version", "page"}: the credit line the list shows) under [made_with].
    `solved`: the answers the mod's build worked out for its maps (BuildResult.solved, §8 "Worked-out answers"),
    written into the folder as maps/<map>/solved.bin first, so the package carries them and players' builds take
    them instead of working them out. A file the Studio wrote a path of the maker's PC into goes in with only the
    file's own name there (studio_paths_out, STUDIO_PATHS; the folder's own file stays as it is); `cleaned`, a list,
    gets each such file's path inside the package, `kinds`, a dict, {that path: the kind of place, "record", "model"
    or "import"}. A README of the modder's goes in with each folder path in it cut to its own name
    (readme_paths_out), and each path that ends at a user's own folder taken out whole (the user's name known
    exactly from this PC's home folder: `home`, Path.home() when not given), in the text encoding it is written in,
    its kind "readme", and `cuts`, a dict, gets {its path inside the package: [(the path as written, the name it
    became: "" for one taken out)]}; `unread`, a list, gets each README of his whose text no encoding readme_paths_out
    knows reads, which goes in as he wrote it. Every other file goes in byte for byte. `home_in`, a list, gets each
    member that still names this PC's home folder (`home`, Path.home() when not given) as packed: a text the modder
    wrote, left as he wrote it.
    A file the Studio left half written (is_work_file) never goes in; `left_out`, a list, gets each one's path in the
    mod folder, as a package would name it."""
    folder = Path(folder)
    if not (folder / MANIFEST).is_file():
        raise PackageError(f"{folder} isn't a mod: it has no {MANIFEST} in it.")
    if solved:
        from .solved import write_mod
        write_mod(folder, solved)
    bad = [f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in NOT_IN_MODS
           and not is_mod_script(f.relative_to(folder).as_posix())]
    if bad:
        raise PackageError(f"This mod can't be packed: mods can't contain scripts or programs "
                           f"({bad[0].relative_to(folder).as_posix()}).")
    game = {}
    if build_id:
        game["builds"] = [str(build_id)]
    if data_revision:
        game["data_revision"] = str(data_revision)
    if fingerprint:
        game["fingerprint"] = str(fingerprint)
    info = update_manifest(folder, game=game, made_with=made_with) if game or made_with else info_of(folder)
    _check_info(info)
    try:
        load_mod(folder)
    except (BuildError, RndfError) as exc:
        raise PackageError(f"Fix the mod before packing it: {exc}") from None
    except OSError as exc:      # (a file of the mod another program holds: said with its name, named_file)
        raise named_file(exc, files_of(folder))
    out = Path(out)
    target = out / file_name(info) if out.is_dir() or out.suffix.lower() != EXTENSION else out
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".part")
    if home is None and home_in is not None:
        try:
            home = Path.home()
        except RuntimeError:                              # (no home folder known: nothing to look for)
            home = None
    mine = home
    if mine is None:
        try:
            mine = Path.home()
        except RuntimeError:
            mine = None
    users = tuple(u for u in (user_of(mine),) if u)       # (this PC's user's name, known exactly: paths_cut)
    work: list = []
    files = files_of(folder, work)
    if left_out is not None:
        left_out += [f.relative_to(folder).as_posix() for f in work]
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                name = f.relative_to(folder).as_posix()
                got = studio_paths_out(f, name)
                if got is None:
                    readme = readme_paths_out(f, name, users, unread)   # (the owner's "cut to file name",
                    #                                     2026-11-13: his README only; "take the username path out")
                    if readme is not None:
                        got = (readme[0], "readme")
                        if cuts is not None:
                            cuts[name] = readme[1]
                if got is None:
                    z.write(f, name)
                    if home_in is not None and (f.suffix.lower() in TEXT_FILES or f.suffix.lower() == ".glb"
                                                or f.name == "LICENSE") and home_named(f.read_bytes(), home):
                        home_in.append(name)
                    continue
                data, kind = got
                member = zipfile.ZipInfo.from_file(f, name)   # (its date and attributes, as z.write gives them)
                member.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(member, data)
                if cleaned is not None:
                    cleaned.append(name)
                if kinds is not None:
                    kinds[name] = kind
                if home_in is not None and home_named(data, home):
                    home_in.append(name)
    except OSError as exc:      # (nothing half made is left beside the target; the file it is about named)
        tmp.unlink(missing_ok=True)
        raise named_file(exc, files)
    try:
        os.replace(tmp, target)
    except OSError:             # (the target held open: no .part left beside it either; the export scenarios' FE-15)
        tmp.unlink(missing_ok=True)
        raise
    return target


def named_file(exc: OSError, files) -> OSError:
    """`exc`, the OSError a file of a mod gave, with the file it is about named when it names none (a part of a file
    another program has locked fails in the middle of a read, nameless: Python then says only "[Errno 13] Permission
    denied"; the export scenarios' FE-13): the first of `files` that can't be read through now. A full disk names
    none: it is about the file being written."""
    full = exc.errno == errno.ENOSPC or getattr(exc, "winerror", None) in (39, 112)
    if exc.filename is None and not full:
        for f in files:
            try:
                with open(f, "rb") as h:
                    while h.read(1 << 20):
                        pass
            except OSError:
                exc.filename = str(f)
                break
    return exc


def _check_info(info: dict) -> None:
    if not _ID.match(info["id"]):
        raise PackageError(f"The mod's id {info['id']!r} isn't allowed: lowercase letters, digits and - only.")
    if not info["version"] or not _VERSION.match(info["version"]):
        raise PackageError(f"The mod's version {info['version']!r} should look like 1.0.0.")


# --- check and unpack ---
def check(path, read: bool = True) -> dict:
    """Look inside a package: its manifest's info plus `files` (the paths inside) and `root` (the folder in the zip,
    "" when mod.toml is at the top). Refuses anything that isn't one mod folder, holds a script or program, would
    write outside its folder, or is too big. With `read`, the mod is also read the way a build would (in a temporary
    folder), so a broken file is caught here."""
    path = Path(path)
    if not path.is_file():
        raise PackageError(f"{path} doesn't exist any more.")
    if not zipfile.is_zipfile(path):
        raise PackageError(f"{path.name} isn't a mod file: a mod file is a {EXTENSION} (or a .zip of a mod folder).")
    with zipfile.ZipFile(path) as z:
        entries = [e for e in z.infolist() if not e.is_dir()]
        names = [e.filename.replace("\\", "/") for e in entries]
        roots = sorted({n[:-len(MANIFEST)] for n in names if n == MANIFEST or n.endswith("/" + MANIFEST)}, key=len)
        roots = [r for r in roots if r.count("/") <= 1]
        if not roots:
            raise PackageError(f"{path.name} isn't a mod file: there's no {MANIFEST} in it (at the top, or inside one "
                               f"folder).")
        root = roots[0]
        files, members = [], {}
        for e, n in zip(entries, names):
            if not n.startswith(root):
                continue
            rel = n[len(root):]
            parts = PurePosixPath(rel).parts
            if not rel or rel.startswith("/") or ".." in parts or ":" in rel or any(p.startswith("\\") for p in parts):
                raise PackageError(f"{path.name} would write outside its folder ({rel}), so it can't be unpacked safely.")
            if PurePosixPath(rel).suffix.lower() in NOT_IN_MODS and not is_mod_script(rel):
                raise PackageError(f"{path.name} can't be used: mods can't contain scripts or programs ({rel}). Ask its "
                                   f"author for a version without it.")
            files.append(rel)
            members[rel] = e.filename
        size = sum(e.file_size for e in entries)
        if size > SIZE_LIMIT:
            raise PackageError(f"{path.name} would unpack to {size // 1_000_000} MB, far more than a mod of data "
                               f"files; it isn't unpacked.")
        try:
            data = tomllib.loads(z.read(root + MANIFEST).decode("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise PackageError(f"{path.name}: its {MANIFEST} can't be read ({exc}).") from None
    info = manifest_info(data)
    _check_info(info)
    info |= {"files": files, "members": members, "root": root, "path": str(path)}
    if read:
        with tempfile.TemporaryDirectory() as tmp:
            _extract(path, members, Path(tmp))
            try:
                load_mod(tmp)
            except (BuildError, RndfError) as exc:
                raise PackageError(f"{path.name} has a mistake in one of its files, so it can't be used ({exc}). Ask its "
                                   f"author for a fixed version.") from None
    return info


def unpack(path, into) -> dict:
    """Unpack the mod folder inside the package into `into` (made if needed; it must be empty or absent). Returns the
    package's info. Nothing is written before the package passed `check()`."""
    into = Path(into)
    if into.exists() and any(into.iterdir()):
        raise PackageError(f"{into} isn't empty, so the mod can't be unpacked there.")
    info = check(path, read=False)
    into.mkdir(parents=True, exist_ok=True)
    try:
        _extract(Path(path), info["members"], into)
    except Exception:
        shutil.rmtree(into, ignore_errors=True)
        raise
    return info


def _extract(path: Path, members: dict, into: Path) -> None:
    """Write the zip members (`{path inside the mod: member name}`) under `into`, one by one, never through the
    member names themselves."""
    with zipfile.ZipFile(path) as z:
        for rel, member in members.items():
            target = into / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
