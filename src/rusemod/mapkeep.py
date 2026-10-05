"""A reshaped map kept between builds (the build cache's `maps` folder), so a build whose strokes for a map are the
same as an earlier build's takes that map's ground from there instead of making it again: on a map flattened
across kilometres, the terrain step and the riverbed mend take many minutes (the owner, 2026-10-04: "28 mins for
river way to long"), and every Play after a unit was changed made them again.

What is kept for a map: the ground files the terrain step made, with what the riverbed mend added (rusemod.mend), the
new water's blocks and the drained beds, the filled hollows (the build takes their low cover off) and the lines the
build said. It is named by a fingerprint of everything those are made from: the map's pack (its file's path, size
and time; a new map's shipped pack and its id; .rmod changes to it), the strokes in load order, the map's water
depth, and the code (rusemod.model.code_version: another version of the app makes it again). A kept file starts
with a fingerprint of the rest of it; one that doesn't match, can't be read back, or holds anything but what is
kept here is ignored and the map made again. Written to a .part file first, then renamed; a cache keeps the
KEEP_MOST most recently used."""
from __future__ import annotations

import hashlib
import io
import json
import os
import pickle
import threading
import zlib
from pathlib import Path

KEEP_FORMAT = 1
KEEP_MOST = 4     # maps kept at most, the most recently used (a kept map can be over 100 MB: its ground pictures)
DIGEST = 20       # bytes of the fingerprint at the start of a kept file, over the rest of it
FOLDER = "maps"   # in the build cache


def pack_identity(arc, path) -> list:
    """What a map's pack is, as far as its ground goes: its file (path, size, time), a new map's shipped pack and id,
    and the .rmod changes on it."""
    out: list = []
    base = getattr(arc, "base", None)
    if base is not None and hasattr(arc, "pack_id"):  # a new map (rusemod.newmap.NewPack): the shipped pack's copy
        out.append(["new map", str(getattr(arc, "source", "")), bytes(arc.pack_id).hex()])
        arc = base
    f = getattr(arc, "_file", None)
    where = getattr(arc, "path", None) or (f.name if f is not None else None) or str(path)
    try:
        st = os.stat(where)
        out.append([os.path.normcase(os.path.abspath(str(where))), st.st_size, st.st_mtime_ns])
    except OSError:
        out.append([str(where), None, None])
    changed, added = getattr(arc, "changed", None) or {}, getattr(arc, "added", None) or {}
    if changed or added:  # .rmod changes (rusemod.rmod.Layered)
        h = hashlib.sha256()
        for kind, items in (("changed", changed), ("added", added)):
            for member in sorted(items):
                h.update(f"{kind}\0{member}\0{len(items[member])}\0".encode("utf-8", "surrogatepass"))
                h.update(items[member])
        out.append(["rmod", h.hexdigest()])
    return out


def plain_file(arc) -> str | None:
    """The file a map's pack reads its members from, when they're the file's own (a new map's: its shipped pack's);
    None for a pack the build changed in memory (.rmod changes), whose members only this program has."""
    base = getattr(arc, "base", None)
    if base is not None and hasattr(arc, "pack_id"):  # a new map: the shipped pack's members
        arc = base
    if getattr(arc, "changed", None) or getattr(arc, "added", None):
        return None
    f = getattr(arc, "_file", None)
    where = getattr(arc, "path", None) or (f.name if f is not None else None)
    return str(where) if where and os.path.isfile(where) else None


def key(name: str, identity: list, strokes: list, depth) -> str | None:
    """The fingerprint a map's kept ground is named by; None when the code can't be read to tell (then nothing is
    kept)."""
    from .model import code_version
    try:
        code = code_version()
    except OSError:
        return None
    parts = {"format": KEEP_FORMAT, "map": name.lower(), "pack": identity, "strokes": [repr(s) for s in strokes],
             "depth": repr(depth)}
    h = hashlib.blake2b(json.dumps(parts, sort_keys=True).encode("utf-8", "surrogatepass") + code, digest_size=20)
    return h.hexdigest()


class _Unpickler(pickle.Unpickler):
    """Reads back only what a kept map holds: plain values, and the filled hollows (rusemod.mend)."""

    def find_class(self, module, name):
        if module == "rusemod.mend" and name in ("Filled", "Gorge", "Riverbeds"):
            from . import mend
            return getattr(mend, name)
        raise pickle.UnpicklingError(f"a kept map doesn't hold {module}.{name}")


def path_of(cache, k: str, kind: str = "map") -> Path:
    return Path(cache) / FOLDER / f"{kind}-{k}.bin"


def read(cache, k: str | None, kind: str = "map") -> dict | None:
    """The map kept under `k`, or None when there's none, or it's damaged. `kind`: what is kept ("map": a map's
    ground; "tiles": a tile set's painted tiles, groundpaint._paint_tiles), each kind with its own files."""
    if cache is None or not k:
        return None
    p = path_of(cache, k, kind)
    try:
        data = p.read_bytes()
    except OSError:
        return None
    try:
        body = data[DIGEST:]
        if len(data) <= DIGEST or hashlib.blake2b(body, digest_size=DIGEST).digest() != data[:DIGEST]:
            return None
        got = _Unpickler(io.BytesIO(zlib.decompress(body))).load()
        if not isinstance(got, dict) or got.get("format") != KEEP_FORMAT or not isinstance(got.get("members"), dict):
            return None
    except Exception:  # noqa: BLE001 - whatever is wrong with a kept file, the map is made again instead
        return None
    try:
        os.utime(p)  # recently used: kept longest
    except OSError:
        pass
    return got


def write(cache, k: str | None, value: dict, kind: str = "map", most: int = KEEP_MOST) -> None:
    """Keep a map's ground under `k`, whole or not at all; then forget the least recently used of its `kind` beyond
    `most`."""
    if cache is None or not k:
        return
    p = path_of(cache, k, kind)
    part = p.with_name(f"{p.name}.{os.getpid()}-{threading.get_ident()}.part")
    try:
        body = zlib.compress(pickle.dumps({"format": KEEP_FORMAT, **value}, protocol=5), 1)
        p.parent.mkdir(parents=True, exist_ok=True)
        part.write_bytes(hashlib.blake2b(body, digest_size=DIGEST).digest() + body)
        part.replace(p)  # two builds at once never read half a file
    except (OSError, pickle.PicklingError, TypeError, AttributeError, RecursionError, MemoryError):
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        return
    try:
        kept = sorted(((f.stat().st_mtime, f) for f in p.parent.glob(f"{kind}-*.bin")), reverse=True)
    except OSError:
        return
    for _when, old in kept[most:]:
        try:
            old.unlink(missing_ok=True)
        except OSError:
            pass  # in use by another build: forgotten next time
