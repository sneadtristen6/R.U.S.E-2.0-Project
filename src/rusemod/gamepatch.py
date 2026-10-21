"""Game patches: small, checked changes to the RUSE.exe of a modded copy, for what a mod's data can't reach alone (the
owner, 2026-10-18: they ship with the Studio, and "only change the copy of it").

- Only the modded copy's own RUSE.exe is changed: the build hands the patched file to rusemod.instance, which writes it
  into the copy as a file of its own. The game in the Steam folder is never touched.
- A patch is a file of the platform's game-patches release: the game build it's for (the SHA-256 of that RUSE.exe),
  the bytes it expects at each place and the bytes it writes there, and the SHA-256 of the result. The apps know each
  patch by name and the SHA-256 of its file (PATCHES): a file that isn't exactly that one is refused, and so is a
  RUSE.exe of any other build. A mod never brings a patch: the build applies one only when the mods use what needs it.
- The file is downloaded once into the build cache and checked every time it's used.
- The copy's fingerprint covers the patch (build.build_and_write), so players only play together with the same one.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

RELEASE_URL = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/download/game-patches/"
URL_ENV = "RUSE_GAME_PATCHES_URL"  # another place for the files, ending in "/" (a test's, a local folder)
FOLDER = "game-patches"            # in the build cache
FORMAT = 1
TIMEOUT = 15                       # seconds for a file to start coming
FILE_MOST = 1_000_000              # bytes: a patch file is a few KB
EXE = "RUSE.exe"
_HEADERS = {"User-Agent": "RUSE-Mod-Platform"}

# The patches the apps may apply: name -> (its file in the release, that file's SHA-256)
PATCHES: dict[str, tuple[str, str]] = {
    # more buildings with units of their own: building kinds 4 and 7 and build menus 9 and 10 for the game's scripts
    # (rusemod.ownbuildings), Steam build 24670294
    "more-buildings": ("more-buildings-24670294.json",
                       "37ce1ed82562a0976535e5703ba000477ee3dc6df7763ee5785e6bfcdabb5fbc"),
}


class GamePatchError(Exception):
    """A patch that can't be had or can't be applied, said for the player."""


@dataclass
class Patch:
    name: str
    from_sha256: str        # the game's RUSE.exe it's made for
    to_sha256: str          # the copy's RUSE.exe once patched
    edits: list             # [(offset in the file, bytes expected there, bytes written there)]
    sha256: str             # the patch file's own


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha(text) -> bool:
    return isinstance(text, str) and len(text) == 64 and all(c in "0123456789abcdef" for c in text)


def parse(name: str, data: bytes) -> Patch:
    """A patch file, checked: it must be exactly the file PATCHES names, and say what it changes plainly."""
    if name not in PATCHES:
        # not a game rule: the patches these apps know
        raise GamePatchError(f"{name}: not a game patch these apps know")
    file, sha = PATCHES[name]
    if _sha(data) != sha:
        # not a game rule: the exact file these apps know
        raise GamePatchError(f"{file} isn't the game patch these apps were made with (its checksum differs), so it "
                             f"wasn't used. Update the apps, or delete the file to have it downloaded again.")
    try:
        doc = json.loads(data.decode("utf-8"))
        assert isinstance(doc, dict) and doc.get("format") == FORMAT and doc.get("name") == name
        assert _is_sha(doc["from_sha256"]) and _is_sha(doc["to_sha256"])
        edits = []
        for offset, old, new in doc["edits"]:
            old_b, new_b = bytes.fromhex(old), bytes.fromhex(new)
            assert isinstance(offset, int) and offset >= 0 and len(old_b) == len(new_b) > 0
            edits.append((offset, old_b, new_b))
        assert edits
    except (UnicodeDecodeError, ValueError, KeyError, TypeError, AssertionError):
        # not a game rule: the patch file's own form
        raise GamePatchError(f"{file} can't be read as a game patch") from None
    return Patch(name, doc["from_sha256"], doc["to_sha256"], edits, sha)


def apply(patch: Patch, exe: bytes) -> bytes:
    """The patched copy of the game's RUSE.exe `exe` (never written back: the caller writes it into the modded copy).
    Refused unless `exe` is the build the patch is for, every place holds the bytes it expects, and the result is
    exactly the one the patch promises."""
    if _sha(exe) != patch.from_sha256:
        # not a game rule: the patch is made for one game build
        raise GamePatchError(f"the game patch {patch.name} is made for another version of R.U.S.E. than the one "
                             f"installed (its RUSE.exe differs), so it can't be applied. Mods that need it can't be "
                             f"played with this version.")
    out = bytearray(exe)
    for offset, old, new in patch.edits:
        if bytes(out[offset:offset + len(old)]) != old:
            # not a game rule: what the patch expects to find
            raise GamePatchError(f"the game patch {patch.name} doesn't match this RUSE.exe at {offset}, so it wasn't "
                                 f"applied")
        out[offset:offset + len(new)] = new
    if _sha(bytes(out)) != patch.to_sha256:
        # not a game rule: the patch's own promise
        raise GamePatchError(f"the game patch {patch.name} didn't give the RUSE.exe it promises, so it wasn't used")
    return bytes(out)


def base_url() -> str:
    return os.environ.get(URL_ENV) or RELEASE_URL


def _open(url: str):
    """A file of the patches' place: over HTTPS (the apps' certificate handling), or from a folder."""
    if url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        from .net import urlopen
        return urlopen(urllib.request.Request(url, headers=_HEADERS), timeout=TIMEOUT)
    return open(url, "rb")


def fetch(name: str, cache: Path | None, opener=_open, say=lambda line: None) -> Patch:
    """Patch `name`: from the build cache when it's there and right, else downloaded into it (`cache` None: into
    nothing, read each time)."""
    if name not in PATCHES:
        # not a game rule: the patches these apps know
        raise GamePatchError(f"{name}: not a game patch these apps know")
    file, sha = PATCHES[name]
    kept = Path(cache) / FOLDER / file if cache is not None else None
    if kept is not None and kept.is_file():
        data = kept.read_bytes()
        if _sha(data) == sha:
            return parse(name, data)
        kept.unlink()  # changed or cut off: fetched again
    url = base_url() + file
    say(f"game patch {name}: downloading {file}")
    try:
        with opener(url) as r:
            data = r.read(FILE_MOST + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        from .mod_index import plain
        # not a game rule: the file couldn't be had
        raise GamePatchError(f"the game patch {name} couldn't be downloaded ({plain(exc, TIMEOUT)}). It's needed once, "
                             f"for the mods' new buildings; connect to the internet and build again.") from None
    if len(data) > FILE_MOST:
        # not a game rule: the patch file's own size
        raise GamePatchError(f"{file} is far bigger than a game patch ever is, so it wasn't used")
    patch = parse(name, data)
    if kept is not None:
        kept.parent.mkdir(parents=True, exist_ok=True)
        part = kept.with_name(kept.name + ".part")
        part.write_bytes(data)
        os.replace(part, kept)
    return patch


def write(name: str, from_sha256: str, to_sha256: str, edits) -> bytes:
    """A patch file's bytes (the maker's side: how a file in the release is made)."""
    doc = {"format": FORMAT, "name": name, "from_sha256": from_sha256, "to_sha256": to_sha256,
           "edits": [[offset, old.hex(), new.hex()] for offset, old, new in edits]}
    return (json.dumps(doc, indent=1) + "\n").encode("utf-8")
