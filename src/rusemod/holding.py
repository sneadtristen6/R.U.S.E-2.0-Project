"""What a unit's Delete couldn't take out of the mod yet: a file of the unit another program has open, which Windows
won't let anything move or remove until that program lets go of it. The owner, 2026-11-13, asked why deleting a unit
should ever stop: "if someone clicks it should through". So the Studio's Delete (ruse_studio.edits.TakeOut) takes the
unit out all the same and names each such file here, in the mod's holding record <mod>/.taking-out/waiting.json; the
build (build.load_mod's readers) and Export (package.files_of) leave every file named here out, so neither stops on
it, and the Studio takes them out by itself (clear) when the mod is opened and before Test in game and Export build it.

Each file is named with its size and time as Delete left it: one written in its place since (the unit made again under
the same name, once the program let go) is never left out or taken out, and its line goes. A folder Delete couldn't
move is named too, to go once nothing is left in it, and so is a finished take-out's own holding folder it couldn't
empty ("holds"). The record and the holding folders are the Studio's own: .taking-out is a dot folder, which a build
never reads and a package never takes."""
from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

FOLDER = ".taking-out"      # <mod>/.taking-out/: the holding folders of the Studio's take-outs, and this record
RECORD = "waiting.json"


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
            out["files"].append({"unit": str(e.get("unit") or ""), "path": e["path"], "size": e["size"],
                                 "time": e["time"]})
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
        try:
            f.parent.rmdir()   # (when empty)
        except OSError:
            pass
        return
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


def waiting_files(mod) -> set[str]:
    """The files the record names that are still as Delete left it (each os.path.normcase'd, absolute)."""
    mod = Path(mod)
    if not record_path(mod).is_file():
        return set()
    return {_key(mod / e["path"]) for e in read(mod)["files"] if _as_left(mod, e)}


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
    .taking-out and removed with it; one still held stays named; one changed or gone leaves the record untouched (never
    a file written there since). A folder goes once nothing is left in it: it stays named while all it holds still
    waits (or a program has it open), and its line goes when something else is in it now. A holding folder named goes
    once it can be emptied. Returns the files and folders taken out, as paths in the mod. Never raises: a record that
    can't be written stays as it was, and what it names stays out of the build until the next time."""
    mod = Path(mod)
    if not record_path(mod).is_file():
        return []
    rec = read(mod)
    gone, files, folders, holds = [], [], [], list(rec["holds"])
    trash = None
    for e in rec["files"]:
        if not _as_left(mod, e):
            continue                                  # (gone, or another file in its place: not what Delete left)
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
