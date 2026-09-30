"""The mod index (docs/MOD_FORMAT.md §15): a small public git repository holds `index.toml`, one entry per published
mod. The launcher's "Browse mods" reads it, keeps a copy for offline use, and installs a mod by downloading its
package (a `.rusemod`, §2) and checking its size and SHA-256 against the entry before the library takes it. No
server of ours: GitHub serves the file, and GitHub Releases the packages.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from .resolve import parse_version

DEFAULT_URL = "https://raw.githubusercontent.com/sneadtristen6/Ruse-Mods/main/index.toml"
TIMEOUT = 10          # seconds for the index and for a download to start answering
FORMAT = 1
INDEX_LIMIT = 5_000_000  # bytes: an index is a few KB per mod
FIELDS = ("id", "version", "download", "size", "sha256")  # an entry needs these; name and the rest are optional
_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_HEADERS = {"User-Agent": "RUSE-Mod-Platform"}


class ModIndexError(Exception):
    """A problem with the mod list or a download, said for the player."""


@dataclass
class IndexResult:
    mods: list
    source: str                     # "online" (fresh) or "cache" (the copy from before)
    as_of: str                      # when the copy shown was fetched
    problems: list = field(default_factory=list)  # entries skipped and why; why a fresh copy couldn't be had
    message: str = ""               # for the screen when the list is the copy from before


# --- reading an index ---
def parse(text: str) -> tuple[list[dict], list[str]]:
    """The entries of an index.toml, each checked, and the problems found: an entry that's missing something is
    skipped and listed, so one mistake never hides the whole list."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ModIndexError(f"the mod list can't be read ({exc})") from None
    if data.get("format", FORMAT) != FORMAT:
        raise ModIndexError(f"the mod list is format {data.get('format')}, made for a newer launcher; update the launcher")
    out, problems, seen = [], [], set()
    for i, e in enumerate(data.get("mod", []), start=1):
        why = _check(e, seen)
        if why:
            problems.append(f"entry {i} ({e.get('id', '?') if isinstance(e, dict) else '?'}) skipped: {why}")
            continue
        seen.add(str(e["id"]))
        out.append(_entry(e))
    return out, problems


def _check(e, seen: set) -> str | None:
    if not isinstance(e, dict):
        return "not a [[mod]] table"
    missing = [f for f in FIELDS if f not in e]
    if missing:
        return f"missing {', '.join(missing)}"
    if not _ID.match(str(e["id"])):
        return "the id isn't lowercase letters, digits and -"
    if str(e["id"]) in seen:
        return "listed twice"
    try:
        parse_version(str(e["version"]))
    except ValueError:
        return "the version isn't like 1.0.0"
    if not str(e["download"]).lower().startswith(("https://", "http://127.0.0.1", "http://localhost")):
        return "the download isn't an https:// link"
    if isinstance(e["size"], bool) or not isinstance(e["size"], int) or e["size"] < 0:
        return "the size isn't a number of bytes"
    if not _SHA.match(str(e["sha256"]).lower()):
        return "the sha256 isn't 64 hex characters"
    return None


def _entry(e: dict) -> dict:
    return {"id": str(e["id"]), "name": str(e.get("name") or e["id"]), "version": str(e["version"]),
            "author": str(e.get("author", "")), "description": str(e.get("description", "")),
            "homepage": str(e.get("homepage", "")), "download": str(e["download"]), "size": int(e["size"]),
            "sha256": str(e["sha256"]).lower(), "game_build": str(e.get("game_build", "")),
            "fingerprint": str(e.get("fingerprint", "")), "tags": [str(t) for t in e.get("tags", [])]}


# --- getting it, and keeping a copy ---
def fetch(url: str, cache_dir, timeout: float = TIMEOUT, now=time.localtime) -> IndexResult:
    """The index from `url`, with a copy kept in `cache_dir`. When the network fails, the copy from before, with its
    date and why a fresh one couldn't be had; with no copy at all, ModIndexError."""
    cache_dir = Path(cache_dir)
    cached, stamp = cache_dir / "index.toml", cache_dir / "index.json"
    try:
        text = _get(url, timeout, INDEX_LIMIT).decode("utf-8")
        mods, problems = parse(text)
    except (ModIndexError, OSError, UnicodeDecodeError) as exc:
        why = plain(exc, timeout)
        if cached.is_file():
            try:
                mods, problems = parse(cached.read_text(encoding="utf-8"))
                as_of = _fetched(stamp)
                return IndexResult(mods, "cache", as_of, problems + [f"no fresh list: {why}"],
                                   f"No connection to the mod list ({why}). This is the copy from {as_of}.")
            except (ModIndexError, OSError, UnicodeDecodeError):
                pass
        if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:  # the address answers, the list isn't there
            exc.close()
            raise ModIndexError("No mod list has been published yet, so there's nothing to browse. A mod you have as "
                                "a file goes in with “Add a mod file…”.") from None
        raise ModIndexError(f"The mod list couldn't be loaded ({why}), and there's no copy from before.") from None
    cache_dir.mkdir(parents=True, exist_ok=True)
    when = time.strftime("%Y-%m-%d %H:%M", now())
    cached.write_text(text, encoding="utf-8")
    stamp.write_text(json.dumps({"url": url, "fetched": when}), encoding="utf-8")
    return IndexResult(mods, "online", when, problems)


def _fetched(stamp: Path) -> str:
    try:
        return str(json.loads(stamp.read_text(encoding="utf-8")).get("fetched", "before"))
    except (OSError, ValueError):
        return "before"


def _get(url: str, timeout: float, limit: int) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=_HEADERS), timeout=timeout) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ModIndexError(f"the file is bigger than {limit // 1_000_000} MB, which a mod list never is")
    return data


def plain(exc: BaseException, timeout: float = TIMEOUT) -> str:
    """Why a request failed, in plain words."""
    if isinstance(exc, urllib.error.HTTPError):
        return f"the server answered {exc.code}"
    if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
        return f"no answer in {timeout:g} seconds"
    if isinstance(exc, urllib.error.URLError):
        return str(exc.reason)
    return str(exc)


# --- installing from it ---
def download(entry: dict, into, timeout: float = TIMEOUT) -> Path:
    """Download the entry's package into the folder `into`, as `<id>-<version>.rusemod`, and check the size and the
    SHA-256 the index promises. Anything else is deleted and refused, so a changed or cut-off file never installs."""
    into = Path(into)
    into.mkdir(parents=True, exist_ok=True)
    target = into / f"{entry['id']}-{entry['version']}.rusemod"
    part = target.with_name(target.name + ".part")
    digest, got = hashlib.sha256(), 0
    try:
        req = urllib.request.Request(entry["download"], headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r, part.open("wb") as f:
            while chunk := r.read(65536):
                got += len(chunk)
                if got > entry["size"]:
                    break  # bigger than promised: no point reading on
                digest.update(chunk)
                f.write(chunk)
    except (OSError, ValueError) as exc:
        part.unlink(missing_ok=True)
        raise ModIndexError(f"{entry['name']} couldn't be downloaded ({plain(exc, timeout)}).") from None
    if got != entry["size"] or digest.hexdigest() != entry["sha256"]:
        part.unlink(missing_ok=True)
        raise ModIndexError(f"The file for {entry['name']} isn't the one the mod list promises (its size or checksum "
                            f"differs), so it wasn't installed. The download may have been cut off, or the file "
                            f"changed since it was listed.")
    part.replace(target)
    return target


def states(entries: list[dict], installed: dict[str, str]) -> list[dict]:
    """Mark each entry against the library (`installed`: id -> version): "installed" (that version, or a newer one,
    is in the library), "update" (the library's is older) or "new" (not in the library)."""
    for e in entries:
        have = installed.get(e["id"])
        if have is None:
            e["state"] = "new"
        else:
            try:
                older = parse_version(have) < parse_version(e["version"])
            except ValueError:
                older = have != e["version"]
            e["state"] = "update" if older else "installed"
        e["installed_version"] = have or ""
    return entries


def size_text(size: int) -> str:
    """A size the way people read it: 12 KB, 3.4 MB."""
    if size < 1_000_000:
        return f"{max(1, round(size / 1000))} KB"
    return f"{size / 1_000_000:.1f} MB"
