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
Nothing a modder wrote is changed (README, descriptions, .rndf, .csv, notes, credits: byte for byte), so no sentence
can be cut; a text naming this PC's home folder goes out as written, and Export says so (home_named). The mod's own
files on the maker's PC keep theirs: Resize and Move fit a model again from the file its record names.
"""
from __future__ import annotations

import json
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


def _toml(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_toml(x) for x in v) + "]"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "") + '"'


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
def files_of(folder) -> list[Path]:
    """The files of a mod folder that go into its package: mod.toml and the other loose files of §2 (the era units'
    credits and record among them, a record naming no unit left out), the .rmod a community mod's mod.toml names
    ([rmod] file: the mod itself), and everything under src/, text/, files/, maps/ and scripts/ (never caches, hidden
    files or build output)."""
    folder = Path(folder)
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
                out += [Path(root) / n for n in sorted(names) if not n.startswith(".")]
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
# paths inside a modder's words (a README, a description, a .rndf, a .csv, a credit, a note go out byte for byte: the
# round-1 cleaner that read paths out of any text cut "Made from C:\models\tank.glb, and docs\turret.md tells how."
# down to "Made from turret.md tells how.", the export recheck of 2026-11-12, F2).
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


def _home_forms(home) -> list[bytes]:
    """This PC's home folder as a file could write it: as it is, with forward slashes, with each backslash twice."""
    s = str(home or "").rstrip("\\/")
    if len(_SEPARATOR.split(s)) < 2 or len(s) < 4:     # (no folder to look for: "/", "C:")
        return []
    return [f.encode("utf-8") for f in {s, s.replace("\\", "/"), s.replace("\\", "\\\\")}]


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
         home=None) -> Path:
    """Zip the mod at `folder` into one file. `out` is the file to write, or a folder to put `<id>-<version>.rusemod`
    in. The mod is checked first (its manifest, and that it reads like a build would); the build it was made on and
    its fingerprint, when given, are written into the manifest (the folder's and the package's) under [game], and the
    tool that made it (`made_with`: {"tool", "version", "page"}: the credit line the list shows) under [made_with].
    `solved`: the answers the mod's build worked out for its maps (BuildResult.solved, §8 "Worked-out answers"),
    written into the folder as maps/<map>/solved.bin first, so the package carries them and players' builds take
    them instead of working them out. A file the Studio wrote a path of the maker's PC into goes in with only the
    file's own name there (studio_paths_out, STUDIO_PATHS; the folder's own file stays as it is); `cleaned`, a list,
    gets each such file's path inside the package, `kinds`, a dict, {that path: the kind of place, "record", "model"
    or "import"}. Every other file goes in byte for byte. `home_in`, a list, gets each member that still names this
    PC's home folder (`home`, Path.home() when not given) as packed: a text the modder wrote, left as he wrote it."""
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
    out = Path(out)
    target = out / file_name(info) if out.is_dir() or out.suffix.lower() != EXTENSION else out
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".part")
    if home is None and home_in is not None:
        try:
            home = Path.home()
        except RuntimeError:                              # (no home folder known: nothing to look for)
            home = None
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files_of(folder):
            name = f.relative_to(folder).as_posix()
            got = studio_paths_out(f, name)
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
    os.replace(tmp, target)
    return target


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
