"""What a unit's Delete couldn't take out of the mod yet: a file of the unit another program has open, which Windows
won't let anything move or remove until that program lets go of it. The owner, 2026-11-13, asked why deleting a unit
should ever stop: "if someone clicks it should through". So the Studio's Delete (ruse_studio.edits.TakeOut) takes the
unit out all the same and names each such file here, in the mod's holding record <mod>/.taking-out/waiting.json; the
build (build.load_mod's readers) and Export (package.files_of) leave every file named here out, so neither stops on
it, and the Studio takes them out by itself (clear) when the mod is opened and before Test in game and Export build it.

Each file is named with its unit and with its size and time as Delete left it. A unit made again under that name
(ModEdits.add_unit) takes its lines out first (forget): what it writes is its own, even the very bytes and time Delete
left (a copy of the same source's clips keeps their times), and is never left out or taken out. A file the program that
held it wrote since (an editor saving the card it had open) is never taken out, and stays out of the build while its
unit is gone: the build never stops on a deleted unit's file (the owner: "it should through"). A folder Delete couldn't
move is named too, to go once nothing is left in it, and so is a finished take-out's own holding folder it couldn't
empty ("holds"). The record and the holding folders are the Studio's own: .taking-out is a dot folder, which a build
never reads and a package never takes."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

FOLDER = ".taking-out"      # <mod>/.taking-out/: the holding folders of the Studio's take-outs, and this record
RECORD = "waiting.json"
NOTE = "wrote.json"         # <mod>/.taking-out/wrote.json: the Studio's note of its own saves (see note)


def record_path(mod) -> Path:
    return Path(mod) / FOLDER / RECORD


def _safe(rel) -> bool:
    """Whether `rel` is a path of the mod's own files ("files/cards/X.png"): a record changed by hand never names
    anything outside them."""
    if not isinstance(rel, str) or "\\" in rel or ":" in rel:
        return False
    parts = rel.split("/")
    return len(parts) >= 2 and parts[0] == "files" and not any(p in ("", ".", "..") for p in parts)


def read(mod) -> dict:
    """The record: {"files": [{"unit", "path", "size", "time"}], "folders": [{"unit", "path"}], "holds": [names]}, each
    path in the mod ("files/cards/X.png"); every list empty without a record, or with one that can't be read (what it
    named is then read by the build like any file, and the build says what to do about it)."""
    out: dict = {"files": [], "folders": [], "holds": []}
    try:
        data = json.loads(record_path(mod).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    if not isinstance(data, dict):
        return out
    for e in data.get("files") or []:
        if isinstance(e, dict) and _safe(e.get("path")) and type(e.get("size")) is int and type(e.get("time")) is int:
            line = {"unit": str(e.get("unit") or ""), "path": e["path"], "size": e["size"], "time": e["time"]}
            if e.get("reborn") is True:
                line["reborn"] = True
            out["files"].append(line)
    for e in data.get("folders") or []:
        if isinstance(e, dict) and _safe(e.get("path")):
            out["folders"].append({"unit": str(e.get("unit") or ""), "path": e["path"]})
    for name in data.get("holds") or []:   # (a folder's own name in .taking-out, on any system)
        if isinstance(name, str) and name and not set(name) & set("/\\:") and name not in (".", "..", RECORD):
            out["holds"].append(name)
    return out


def _write(mod, rec: dict) -> None:
    """The record as `rec`, whole (through a .partial file); none (and no .taking-out, once empty) when it names
    nothing. OSError when it can't be written."""
    f = record_path(mod)
    if not (rec["files"] or rec["folders"] or rec["holds"]):
        f.unlink(missing_ok=True)
        (f.parent / NOTE).unlink(missing_ok=True)
        try:
            f.parent.rmdir()   # (when empty)
        except OSError:
            pass
        return
    if not any(e.get("reborn") for e in rec["files"]):
        (f.parent / NOTE).unlink(missing_ok=True)   # (nothing is waiting to be told from a new write)
    f.parent.mkdir(parents=True, exist_ok=True)
    part = f.with_name(f.name + ".partial")
    try:
        part.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(part, f)
    except OSError:
        part.unlink(missing_ok=True)
        raise


def _key(path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _rel(mod: Path, path) -> str | None:
    try:
        rel = Path(path).relative_to(mod).as_posix()
    except ValueError:
        return None
    return rel if _safe(rel) else None


def add(mod, files=(), folders=(), holds=()) -> list[str]:
    """Name these in the record, beside what it names already: `files` and `folders` as (path, the unit's name) pairs,
    each file with its size and time now (one that's gone, or isn't a file of the mod's own files, is left out), and
    `holds`, names of holding folders in .taking-out. Returns the files and folders named, as paths in the mod. OSError
    when the record can't be written (then nothing is named)."""
    mod = Path(mod)
    rec = read(mod)
    named = []
    for path, unit in files:
        rel = _rel(mod, path)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if rel is None or not stat.S_ISREG(st.st_mode):
            continue
        rec["files"] = [e for e in rec["files"] if _key(mod / e["path"]) != _key(mod / rel)]
        rec["files"].append({"unit": unit or "", "path": rel, "size": st.st_size, "time": st.st_mtime_ns})
        named.append(rel)
    for path, unit in folders:
        rel = _rel(mod, path)
        if rel is None or not Path(path).is_dir():
            continue
        if all(_key(mod / e["path"]) != _key(mod / rel) for e in rec["folders"]):
            rec["folders"].append({"unit": unit or "", "path": rel})
        named.append(rel)
    for name in holds:
        if name not in rec["holds"]:
            rec["holds"].append(name)
    _write(mod, rec)
    return named


def _as_left(mod: Path, e: dict) -> bool:
    """Whether the record's file `e` is still as Delete left it: there, the same size and time."""
    try:
        st = os.stat(mod / e["path"])
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode) and (st.st_size, st.st_mtime_ns) == (e["size"], e["time"])


def _there(mod: Path, e: dict) -> bool:
    """Whether the record's file `e` is still there: as Delete left it, or written since by the program that held it."""
    try:
        return stat.S_ISREG(os.stat(mod / e["path"]).st_mode)
    except OSError:
        return False


def waiting_files(mod) -> set[str]:
    """The files the record names that are still there (each os.path.normcase'd, absolute), as Delete left them or
    written since by the program that held them: their unit is gone all the same."""
    mod = Path(mod)
    if not record_path(mod).is_file():
        return set()
    wrote = _wrote(mod)
    return {_key(mod / e["path"]) for e in read(mod)["files"] if _there(mod, e) and not _new_units(mod, e, wrote)}


def _wrote(mod: Path) -> dict:
    """The Studio's note of its saves: {path in the mod: SHA-256 of the bytes it wrote}; empty without a note."""
    try:
        data = json.loads((mod / FOLDER / NOTE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    files = data.get("files") if isinstance(data, dict) else None
    return {k: v for k, v in files.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(files, dict) else {}


def _sha(path) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
    except OSError:
        return None
    return h.hexdigest()


def _new_units(mod: Path, e: dict, wrote: dict) -> bool:
    """Whether the record's file `e`, of a unit made again since (reborn), is the new unit's own: written since (not as
    Delete left it), or, when its size and time are the very ones Delete left (a copy of the same source's clips keeps
    their times), the Studio's note says it wrote that path with these very bytes (their SHA-256). The old file left
    as it was is never the new unit's: it stays out of the build."""
    if not e.get("reborn"):
        return False
    if not _as_left(mod, e):
        return True
    sha = wrote.get(e["path"])
    return sha is not None and sha == _sha(mod / e["path"])


def note(mod, paths) -> None:
    """The Studio has written these files of the mod (a unit's card, model, look, a clip copied for it): while a unit
    made again has a leftover file waiting, name each of them that the record names, with the SHA-256 of what was
    written, in <mod>/.taking-out/wrote.json. forget() makes the old file's line "reborn"; this note is how a new write
    with the very size and time Delete left is told from the old file. Nothing is written when no leftover waits.
    OSError when the note can't be written."""
    mod = Path(mod)
    if not record_path(mod).is_file():
        return
    rec = read(mod)
    reborn = {e["path"] for e in rec["files"] if e.get("reborn")}
    if not reborn:
        return
    got = _wrote(mod)
    for path in paths:
        rel = _rel(mod, path)
        if rel in reborn:
            sha = _sha(path)
            if sha is not None:
                got[rel] = sha
    f = mod / FOLDER / NOTE
    part = f.with_name(f.name + ".partial")
    try:
        part.write_text(json.dumps({"files": got}, indent=1) + "\n", encoding="utf-8")
        os.replace(part, f)
    except OSError:
        part.unlink(missing_ok=True)
        raise


def skip_of(mod):
    """For the build's and Export's readers of the mod at `mod`: a test of a file's path, True for one to leave out
    (waiting_files names it); None when nothing waits."""
    waiting = waiting_files(mod)
    if not waiting:
        return None
    return lambda path: _key(path) in waiting


def _drop_empty(folder: Path) -> None:
    """`folder` and the folders in it removed, deepest first, as far as they're empty and Windows lets."""
    for root, _dirs, names in os.walk(folder, topdown=False):
        if not names:
            try:
                os.rmdir(root)
            except OSError:
                pass


def clear(mod) -> list[str]:
    """Take out what the record names, as far as Windows lets now (the Studio does when the mod is opened and before
    Test in game and Export build it): each file still as Delete left it is moved into a fresh holding folder in
    .taking-out and removed with it; one still held stays named; one the program that held it wrote since stays, never
    taken out, named (so out of the build while its unit is gone); one gone leaves the record. A folder goes once
    nothing is left in it: it stays named while all it holds still waits (or a program has it open), and its line goes
    when something else is in it now. A holding folder named goes once it can be emptied. Returns the files and folders
    taken out, as paths in the mod. Never raises: a record that can't be written stays as it was, and what it names
    stays out of the build until the next time."""
    mod = Path(mod)
    if not record_path(mod).is_file():
        return []
    rec = read(mod)
    gone, files, folders, holds = [], [], [], list(rec["holds"])
    trash = None
    wrote = _wrote(mod)
    for e in rec["files"]:
        if not _there(mod, e):
            continue                                  # (gone: its line goes)
        if _new_units(mod, e, wrote):
            continue                                  # (a unit made again wrote it: its own, never taken out)
        if not _as_left(mod, e):
            files.append(e)                           # (written since by the program that held it: kept, never taken
            continue                                  #  out, and out of the build while its unit is gone)
        try:
            if trash is None:
                trash = Path(tempfile.mkdtemp(prefix="", dir=mod / FOLDER))
            os.rename(mod / e["path"], trash / str(len(gone)))
            gone.append(e["path"])
        except OSError:
            files.append(e)                           # (still held: next time)
    waiting = {_key(mod / e["path"]) for e in files}
    for e in rec["folders"]:
        path = mod / e["path"]
        try:
            if not path.is_dir():
                continue
            _drop_empty(path)
            if not path.exists():
                gone.append(e["path"])
                continue
            inside = [os.path.join(r, n) for r, _d, names in os.walk(path) for n in names]
        except OSError:
            folders.append(e)
            continue
        if all(_key(f) in waiting for f in inside):
            folders.append(e)                         # (all it holds waits, or a program has it open)
    if trash is not None:
        holds.append(trash.name)
    left = []
    for name in holds:
        h = mod / FOLDER / name
        shutil.rmtree(h, ignore_errors=True)
        try:
            if h.exists():
                left.append(name)
        except OSError:
            left.append(name)
    try:
        _write(mod, {"files": files, "folders": folders, "holds": left})
    except OSError:
        pass
    return gone


def forget(mod, unit: str) -> None:
    """A unit called `unit` is made (again) in the mod (ModEdits.add_unit, before anything of it is written): what a
    Delete of an earlier one of that name left waiting stops waiting. What of it can be taken out now goes first
    (clear); a file a program still holds, or wrote since, is from then on the new unit's, read by the build like any of
    its files, and what the new unit writes is never mistaken for the old one's leftover (a copy of the same source's
    clips has the very bytes and times Delete left: anim.copy_unit). OSError when the record can't be written."""
    mod = Path(mod)
    if not unit or not record_path(mod).is_file():
        return
    clear(mod)
    rec = read(mod)
    # a file of the old unit still exactly as Delete left it (held by a program) stays named, out of the build: the new
    # unit never wears it, unless its own write is in the Studio's note (note); one written since is the new unit's
    files = [dict(e, reborn=True) if e["unit"] == unit and _as_left(mod, e) else e
             for e in rec["files"] if e["unit"] != unit or _as_left(mod, e)]
    fresh = {e["path"] for e in rec["files"] if e["unit"] == unit and not e.get("reborn")}
    got = _wrote(mod)
    if fresh & set(got):   # (a note of an earlier unit's saves at these paths is nothing to this one)
        part = (mod / FOLDER / NOTE).with_name(NOTE + ".partial")
        try:
            part.write_text(json.dumps({"files": {k: v for k, v in got.items() if k not in fresh}}) + "\n",
                            encoding="utf-8")
            os.replace(part, mod / FOLDER / NOTE)
        except OSError:
            part.unlink(missing_ok=True)
            raise
    left = {"files": files,
            "folders": [e for e in rec["folders"] if e["unit"] != unit], "holds": rec["holds"]}
    if left != rec:
        _write(mod, left)
