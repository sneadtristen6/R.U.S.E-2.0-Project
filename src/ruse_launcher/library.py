"""The launcher's mod library: the mods a player has added, one folder each in `<home>/library/<mod id>/`
(PLAN.md L5, Launcher 0.2). A mod comes in as a folder with `mod.toml` (or that file itself), or as a `.zip` of one
(MOD_FORMAT §2). It's checked before it goes in: the engine reads it the way a build would (`rusemod.build.load_mod`),
so a mod with a mistake, or one carrying scripts or programs, never reaches the library. Adding a mod whose id is
already there replaces it (a new version, usually).
"""
from __future__ import annotations

import os
import re
import shutil
import tomllib
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from rusemod.build import NOT_IN_MODS, BuildError, load_mod
from rusemod.rndf import RndfError

MANIFEST = "mod.toml"
ZIP_LIMIT = 500_000_000  # bytes unpacked: a mod of data files is a few MB; anything near this isn't one


class LibraryError(Exception):
    """A mod that can't be added, with a message that says what to do next."""


def read_info(folder: Path) -> dict:
    """What the library shows about a mod folder, from its mod.toml (already checked by the engine)."""
    manifest = tomllib.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    m, game = manifest.get("mod", {}), manifest.get("game", {})
    authors = m.get("authors", m.get("author", []))
    authors = [authors] if isinstance(authors, str) else [str(a) for a in authors]
    return {"id": str(m.get("id", folder.name)), "name": str(m.get("name") or m.get("id") or folder.name),
            "version": str(m.get("version", "")), "authors": authors, "author": ", ".join(authors),
            "description": str(m.get("description", "")), "builds": [str(b) for b in game.get("builds", [])],
            "path": str(folder)}


def check(folder: Path) -> dict:
    """Read a mod folder the way a build would; a mistake becomes a LibraryError for the player."""
    try:
        load_mod(folder)
    except BuildError as exc:
        raise LibraryError(f"This mod can't be added: {exc} Ask its author for a fixed version.") from None
    except RndfError as exc:
        raise LibraryError(f"This mod has a mistake in one of its files, so it wasn't added ({exc}). Ask its author "
                           f"for a fixed version.") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise LibraryError(f"This mod couldn't be read ({exc}).") from None
    return read_info(folder)


class Library:
    def __init__(self, folder):
        self.folder = Path(folder)

    def mods(self) -> list[dict]:
        """Every mod in the library, by name."""
        out = []
        for f in sorted(self.folder.iterdir(), key=lambda p: p.name.lower()) if self.folder.is_dir() else []:
            if f.is_dir() and not f.name.startswith(".") and (f / MANIFEST).is_file():
                try:
                    out.append(read_info(f))
                except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
                    out.append({"id": f.name, "name": f.name, "version": "", "authors": [], "author": "",
                                "description": "", "builds": [], "path": str(f),
                                "error": "its mod.toml can't be read; remove it and add the mod again"})
        return out

    def path_of(self, mod_id: str) -> Path | None:
        folder = self.folder / mod_id
        return folder if _safe_id(mod_id) and (folder / MANIFEST).is_file() else None

    def add(self, path) -> tuple[dict, bool]:
        """Add a mod from `path`: a folder with mod.toml, that file itself, or a .zip holding such a folder. Returns
        (the mod's info, whether it replaced a mod of the same id)."""
        source = Path(path)
        if source.is_file() and source.name.lower() == MANIFEST:
            source = source.parent
        if not source.exists():
            raise LibraryError(f"{source} doesn't exist any more.")
        self.folder.mkdir(parents=True, exist_ok=True)
        incoming = self.folder / f".incoming-{uuid.uuid4().hex[:8]}"
        try:
            if source.is_dir():
                if not (source / MANIFEST).is_file():
                    raise LibraryError(f"{source} isn't a mod: it has no {MANIFEST} in it. Pick the mod's own folder, "
                                       f"or a .zip of it.")
                shutil.copytree(source, incoming, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            elif zipfile.is_zipfile(source):
                _unpack(source, incoming)
            else:
                raise LibraryError(f"{source.name} isn't a mod: add a mod folder (with {MANIFEST} in it) or a .zip of "
                                   f"one.")
            info = check(incoming)
            if not _safe_id(info["id"]):
                raise LibraryError(f"This mod's id {info['id']!r} isn't allowed (lowercase letters, digits and -).")
            target = self.folder / info["id"]
            replaced = target.exists()
            if source.resolve() == target.resolve():  # added from its own place in the library: nothing to move
                return read_info(target), True
            old = self.folder / f".old-{info['id']}"
            if old.exists():
                shutil.rmtree(old)
            if replaced:
                os.replace(target, old)
            os.replace(incoming, target)
            if old.exists():
                shutil.rmtree(old, ignore_errors=True)
            info["path"] = str(target)
            return info, replaced
        finally:
            if incoming.exists():
                shutil.rmtree(incoming, ignore_errors=True)

    def remove(self, mod_id: str) -> dict:
        folder = self.path_of(mod_id)
        if folder is None:
            raise LibraryError(f"There's no mod called {mod_id!r} in the library.")
        info = read_info(folder)
        shutil.rmtree(folder)
        return info


def _safe_id(mod_id: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", mod_id))


def _unpack(zip_path: Path, into: Path) -> None:
    """Unpack the mod folder inside a .zip: mod.toml at the top, or inside one folder. Nothing outside `into` is ever
    written, and a zip carrying scripts or programs is refused before anything is unpacked."""
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        roots = sorted({n[:-len(MANIFEST)] for n in names if n == MANIFEST or n.endswith("/" + MANIFEST)}, key=len)
        roots = [r for r in roots if r.count("/") <= 1]
        if not roots:
            raise LibraryError(f"{zip_path.name} isn't a mod: there's no {MANIFEST} in it (at the top, or inside one "
                               f"folder).")
        root = roots[0]
        wanted = [n for n in names if n.startswith(root)]
        bad = sorted(PurePosixPath(n).name for n in wanted if PurePosixPath(n).suffix.lower() in NOT_IN_MODS)
        if bad:
            raise LibraryError(f"{zip_path.name} can't be added: mods can't contain scripts or programs "
                               f"({', '.join(bad[:5])}{', …' if len(bad) > 5 else ''}).")
        total = sum(z.getinfo(n).file_size for n in wanted)
        if total > ZIP_LIMIT:
            raise LibraryError(f"{zip_path.name} is too big to be a mod ({total // 1_000_000} MB unpacked).")
        into.mkdir(parents=True)
        for n in wanted:
            rel = PurePosixPath(n[len(root):])
            if rel.is_absolute() or ".." in rel.parts or any(":" in part or "\\" in part for part in rel.parts):
                raise LibraryError(f"{zip_path.name} can't be unpacked safely ({n}).")
            target = into.joinpath(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
