"""A mod as one file (docs/MOD_FORMAT.md §2): the mod folder zipped, named `<id>-<version>.rusemod`. Both apps use
this module: the Studio packs ("Export mod…"), the launcher checks and unpacks ("Add a mod file…").

A package is checked before anything is unpacked: it must hold one mod folder (`mod.toml` at the top, or inside one
folder), nothing that could run (scripts or programs, PLAN.md decision 23), nothing that would land outside the target
folder, and a size that makes sense for data files; then the mod is read the way a build reads it. Every problem is a
PackageError whose message is written for the person holding the file.

The manifest inside the package carries the game build the mod was made on and the mod's fingerprint (§12), written
by `pack()` into the folder's own `mod.toml` first, so the next export starts from them.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

from .build import NOT_IN_MODS, BuildError, load_mod
from .mapscripts import is_mod_script  # the game's mission scripts a mod changes (MOD_FORMAT §9): its only scripts
from .rndf import RndfError

EXTENSION = ".rusemod"
MANIFEST = "mod.toml"
SIZE_LIMIT = 500_000_000  # bytes unpacked: a mod of data files is a few MB; anything near this isn't one
TOP_FILES = ("mod.toml", "menus.toml", "README.md", "LICENSE", "CHANGELOG.md")  # loose files a package keeps
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
    """The files of a mod folder that go into its package: mod.toml and the other loose files of §2, the .rmod a
    community mod's mod.toml names ([rmod] file: the mod itself), and everything under src/, text/, files/, maps/
    and scripts/ (never caches, hidden files or build output)."""
    folder = Path(folder)
    out = [folder / f for f in TOP_FILES if (folder / f).is_file()]
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


def pack(folder, out, *, build_id: str | None = None, data_revision: str | None = None,
         fingerprint: str | None = None, solved: dict | None = None, made_with: dict | None = None) -> Path:
    """Zip the mod at `folder` into one file. `out` is the file to write, or a folder to put `<id>-<version>.rusemod`
    in. The mod is checked first (its manifest, and that it reads like a build would); the build it was made on and
    its fingerprint, when given, are written into the manifest (the folder's and the package's) under [game], and the
    tool that made it (`made_with`: {"tool", "version", "page"}: the credit line the list shows) under [made_with].
    `solved`: the answers the mod's build worked out for its maps (BuildResult.solved, §8 "Worked-out answers"),
    written into the folder as maps/<map>/solved.bin first, so the package carries them and players' builds take
    them instead of working them out."""
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
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files_of(folder):
            z.write(f, f.relative_to(folder).as_posix())
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
