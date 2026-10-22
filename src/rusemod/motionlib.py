"""RUSE Decoy's motion library: the free motion capture sets' moves, listed by kind with what each is, fetched from the
internet only when a modder picks one, and kept in the platform folder (rusemod.home) for next time.

The list (motions.json.gz, beside this file) holds 3,205 moves of two sets, each with its kind, its length, where it
comes from and the exact size and SHA-256 of its file, so a fetched file is used only when it's the one listed:
  - the CMU Graphics Lab Motion Capture Database (BVH conversion by Bruce Hahne): 2,505 moves of 109 sessions
    (walks, runs, jumps, fights, climbs, everyday work, dances, sports...), each kept online as a small zip of its
    one file, fetched one at a time (most under half a megabyte). Free for any use; credit asked for.
  - 100STYLE: 100 styles of walking (marching, crouched, limping, proud...), each forwards, backwards, sideways,
    walking and running, and standing still: 700 moves, with the stretch where each way is done. The set comes as
    one 1.4 GB file: fetched once, its moves kept, the big file deleted. CC BY 4.0.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from . import net

LIST = Path(__file__).with_name("motions.json.gz")
FOLDER = Path("library") / "motions"        # in the platform folder
KINDS = ["walk", "run", "stand", "crawl", "fall", "fight", "signal", "jump", "climb", "carry", "work", "sit_lie",
         "sport", "dance", "other"]
WAYS = ["FW", "BW", "SW", "FR", "BR", "SR", "ID"]   # 100STYLE: forwards, backwards, sideways; walking, running; still
TIMEOUT = 20
_HEADERS = {"User-Agent": "RUSE-Mod-Platform"}


class MotionLibError(Exception):
    pass


def catalogue() -> dict:
    """{"sets": {set: {"name", "credit", "licence", "site", ...}}, "moves": [...]} as listed."""
    return json.loads(gzip.decompress(LIST.read_bytes()))


def folder(home: Path) -> Path:
    return Path(home) / FOLDER


def where(home: Path, move: dict) -> Path:
    return folder(home) / move["path"]


def have(home: Path, move: dict) -> bool:
    """Whether the move's file is kept, at its listed size (its SHA-256 is checked when it's fetched)."""
    p = where(home, move)
    try:
        return p.stat().st_size == move["size"]
    except OSError:
        return False


def find(cat: dict, kind: str = "", words: str = "", set_: str = "") -> list:
    """The moves of `kind` ("" any) and set ("" both) whose name, group or kind hold every one of `words`."""
    want = [w for w in re.split(r"\s+", (words or "").lower()) if w]
    out = []
    for m in cat["moves"]:
        if kind and m["kind"] != kind or set_ and m["set"] != set_:
            continue
        text = f"{m['name']} {m['group']} {m['kind']} {m.get('way', '')} {m['id']}".lower()
        if all(w in text for w in want):
            out.append(m)
    return out


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _plain(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"the server answered {exc.code}"
    if isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError)):
        return "the site couldn't be reached: is this PC on the internet?"
    return str(exc)


def fetch(home: Path, move: dict, opener=None) -> Path:
    """The move's file, kept in the platform folder: fetched from its address the first time (a set that comes whole,
    100STYLE, is fetched with fetch_set instead). Refused, and nothing kept, when what came isn't the listed file."""
    p = where(home, move)
    if have(home, move):
        return p
    if not move.get("url"):
        raise MotionLibError("set")   # the page offers the whole set's download
    opener = opener or (lambda req: net.urlopen(req, TIMEOUT))
    packed = move.get("zip_size")   # a move kept online as a small zip of its one file (the CMU set's way)
    try:
        req = urllib.request.Request(move["url"], headers=_HEADERS)
        with opener(req) as r:
            data = r.read((packed or move["size"]) + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        raise MotionLibError(f"{move['name']} couldn't be fetched ({_plain(exc)}).") from None
    if packed:
        if len(data) != packed or _sha(data) != move["zip_sha256"]:
            raise MotionLibError(f"{move['name']}: what came isn't the listed file (its size or checksum differs), "
                                 f"so it wasn't kept.")
        name = move["path"].rsplit("/", 1)[-1]
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                data = z.read(name)
        except (zipfile.BadZipFile, KeyError):
            raise MotionLibError(f"{move['name']}: the listed file doesn't hold {name}, so it wasn't kept.") from None
    if len(data) != move["size"] or _sha(data) != move["sha256"]:
        raise MotionLibError(f"{move['name']}: what came isn't the listed file (its size or checksum differs), so it "
                             f"wasn't kept.")
    p.parent.mkdir(parents=True, exist_ok=True)
    part = p.with_name(p.name + ".part")
    part.write_bytes(data)
    part.replace(p)
    return p


def set_state(home: Path, cat: dict, set_: str) -> dict:
    """How many of a set's moves are kept: {"have", "total"}."""
    moves = [m for m in cat["moves"] if m["set"] == set_]
    return {"have": sum(have(home, m) for m in moves), "total": len(moves)}


def fetch_set(home: Path, cat: dict, set_: str, progress=lambda done, total: None, opener=None) -> dict:
    """A set that comes as one file (100STYLE): fetched into the platform folder with `progress(bytes, of)`, checked
    against its listed size and MD5, its moves taken out (each checked against its own listed size and SHA-256), the
    big file deleted. Returns set_state."""
    info = cat["sets"][set_]
    if not info.get("zip"):
        raise MotionLibError(f"{info['name']} comes one move at a time")
    base = folder(home)
    base.mkdir(parents=True, exist_ok=True)
    big = base / f"{set_}.zip.part"
    md5, got = hashlib.md5(), 0
    opener = opener or (lambda req: net.urlopen(req, TIMEOUT))
    try:
        req = urllib.request.Request(info["zip"], headers=_HEADERS)
        with opener(req) as r, big.open("wb") as f:
            while chunk := r.read(1 << 20):
                got += len(chunk)
                if got > info["zip_size"]:
                    break
                md5.update(chunk)
                f.write(chunk)
                progress(got, info["zip_size"])
    except (OSError, ValueError) as exc:
        big.unlink(missing_ok=True)
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        raise MotionLibError(f"{info['name']} couldn't be fetched ({_plain(exc)}).") from None
    if got != info["zip_size"] or md5.hexdigest() != info["zip_md5"]:
        big.unlink(missing_ok=True)
        raise MotionLibError(f"{info['name']}: what came isn't the listed file (its size or checksum differs), so it "
                             f"wasn't kept. The download may have been cut off.")
    try:
        take(home, cat, set_, big)
    finally:
        big.unlink(missing_ok=True)
    return set_state(home, cat, set_)


def take(home: Path, cat: dict, set_: str, zip_path: Path) -> int:
    """The listed moves of `set_` taken out of its zip into the platform folder, each only as listed (size and
    SHA-256); a member whose name or contents aren't listed is left. Returns how many were kept."""
    moves = {m["path"].split("/", 1)[1].lower(): m for m in cat["moves"] if m["set"] == set_}
    kept = 0
    with zipfile.ZipFile(zip_path) as z:
        for zi in z.infolist():
            name = zi.filename.replace("\\", "/")
            if name.startswith("__MACOSX/") or not name.lower().endswith(".bvh"):
                continue
            key = "/".join(name.split("/")[-2:]).lower()     # <style>/<file>, wherever the zip's folders start
            m = moves.get(key)
            if m is None or zi.file_size != m["size"]:
                continue
            data = z.read(zi)
            if _sha(data) != m["sha256"]:
                continue
            p = where(home, m)
            p.parent.mkdir(parents=True, exist_ok=True)
            part = p.with_name(p.name + ".part")
            part.write_bytes(data)
            part.replace(p)
            kept += 1
    return kept
