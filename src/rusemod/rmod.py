""".rmod mods (the format of LittleGroove's RUSE Mod Manager, used by most community mods) in our builds, applied by
his engine (`ruse_mod_engine`).

His applier rewrites game packs on disk. Here it works on `Layered` packs instead: a game pack read-only, with the
changes made so far on top. The applier's writes are only recorded, and the build writes the changed packs into the
modded copy like every other change, so the Steam install is never touched and no multi-GB pack is copied first. A
mod made for another game build is moved to this one with his version maps.

A .rmod may replace the game's own scripts (.xyz, and the .ipk archives that hold them; the owner's call, 2026-09-29,
an exception to PLAN.md decision 23 for .rmod mods), and the build says so; anything else that could run on the PC
(programs, PC scripts) is refused.
"""
from __future__ import annotations

import logging
import re
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from .build import NOT_IN_MODS, BuildError
from .edat import Edat
from .patch import Finding

EXTENSION = ".rmod"
_LOCK = threading.Lock()  # the applier opens packs through a module function, swapped in while it runs
logging.getLogger("ruse_mod_engine").addHandler(logging.NullHandler())
logging.getLogger("ruse_mod_engine").propagate = False  # its messages come back as findings


class Layered(Edat):
    """A game pack with changes on top: reads see the changes; the pack's file is only read. It serves our build
    (as an Edat, whose `write_to` includes the changes) and LittleGroove's applier (as his EdataFile: get, list,
    replace, add, batch_update), which records its edits here instead of rewriting the pack."""

    def __init__(self, base: Edat, path):
        self.__dict__.update(base.__dict__)  # same file, entries and offsets; `base` owns the open file
        self.path = str(path)
        self.changed: dict[str, bytes] = {}  # member path, as in the pack -> new bytes
        self.added: dict[str, bytes] = {}    # path of a new member -> its bytes
        self._header = SimpleNamespace(version=self.version)

    @property
    def is_changed(self) -> bool:
        return bool(self.changed or self.added)

    def close(self) -> None:
        pass  # the base pack closes the file

    # --- as an Edat ---
    def read(self, entry):
        blob = self.changed.get(entry.path)
        return blob if blob is not None else Edat.read(self, entry)

    def iter_chunks(self, replace=None, add=None):
        merged = dict(self.changed)
        for key, blob in (replace or {}).items():
            merged[(self.entry(key) or self.find(key)).path] = blob
        return Edat.iter_chunks(self, merged, {**self.added, **(add or {})})

    # --- as LittleGroove's EdataFile ---
    @property
    def _entries(self):
        return [SimpleNamespace(path=p) for p in self.list()]

    def list(self) -> list[str]:
        return [e.path for e in self.entries] + list(self.added)

    def _added_path(self, path: str) -> str | None:
        key = path.replace("/", "\\").lower()
        return next((p for p in self.added if p.lower() == key), None)

    def get(self, path: str) -> bytes | None:
        e = self.entry(path)
        if e is not None:
            return bytes(self.read(e))
        p = self._added_path(path)
        return self.added[p] if p is not None else None

    def replace(self, path: str, data: bytes) -> None:
        e = self.entry(path)
        if e is not None:
            self.changed[e.path] = bytes(data)
            return
        p = self._added_path(path)
        if p is None:
            raise KeyError(f"File {path!r} not found in {self.path}")
        self.added[p] = bytes(data)

    def add(self, path: str, data: bytes) -> None:
        if self.get(path) is not None:
            raise KeyError(f"File {path!r} already exists in {self.path}. Use replace() instead.")
        self.added[path.replace("/", "\\")] = bytes(data)

    def batch_update(self, to_replace: dict, to_add: dict) -> None:
        for path, data in to_replace.items():
            self.replace(path, data)
        for path, data in to_add.items():
            self.add(path, data)


GAME_SCRIPTS = {".xyz", ".ipk"}  # the game's compiled Python and its archives: allowed in .rmod mods


def _kinds(path: str) -> set[str]:
    """The extensions along a path inside a pack that name something runnable (NOT_IN_MODS)."""
    return {Path(part).suffix.lower() for part in path.replace("\\", "/").split("/") if part} & NOT_IN_MODS


def scripts_of(mod) -> list[str]:
    """The game scripts a .rmod replaces or adds (inside an .ipk, or as .xyz files)."""
    return sorted({"/".join(p for p in (fp.container, fp.path) if p) for g in mod.file_patches for fp in g.files
                   if _kinds(fp.container or "") | _kinds(fp.path)})


def check(path):
    """Read a .rmod the way a build will (his engine's reader), and refuse one that brings programs or PC scripts;
    the game's own scripts are allowed. Returns his RuseMod."""
    from ruse_mod_engine import mod_format
    path = Path(path)
    try:
        mod = mod_format.load(str(path))
    except (OSError, ValueError, KeyError, TypeError) as exc:  # bad JSON, or a mistake his reader names
        raise BuildError(f"{path.name} can't be read as a .rmod mod ({exc}).") from None
    bad = sorted({"/".join(p for p in (fp.container, fp.path) if p) for g in mod.file_patches for fp in g.files
                  if (_kinds(fp.container or "") | _kinds(fp.path)) - GAME_SCRIPTS})
    if bad:
        more = ", …" if len(bad) > 3 else ""
        raise BuildError(f"{path.name} brings files that would run on the PC ({', '.join(bad[:3])}{more}); mods can't "
                         f"bring programs (PLAN.md decision 23).")
    return mod


def mod_id(mod, path) -> str:
    """Our id for a .rmod: its own id (or file name) in lowercase letters, digits and '-'."""
    raw = str(getattr(mod, "id", "") or Path(path).stem)
    return re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-") or "rmod"


def version_of(mod) -> str:
    v = str(getattr(mod, "version", "") or "").strip()
    return v if re.fullmatch(r"\d+(\.\d+){0,2}", v) else "0.0.0"


def make_folder(rmod_path, into) -> None:
    """A mod folder for the library from one .rmod file: mod.toml (from the .rmod's own name, version, author,
    description and game build) plus the file itself, which the build applies."""
    from .package import _toml
    rmod_path, into = Path(rmod_path), Path(into)
    mod = check(rmod_path)
    lines = ["[mod]", f"id = {_toml(mod_id(mod, rmod_path))}", f"name = {_toml(mod.name or rmod_path.stem)}",
             f"version = {_toml(version_of(mod))}"]
    if mod.author:
        lines.append(f"authors = {_toml([mod.author])}")
    if mod.description:
        lines.append(f"description = {_toml(mod.description)}")
    if mod.game_version:
        lines += ["", "[game]", f"builds = {_toml([str(mod.game_version)])}"]
    lines += ["", "[rmod]", f"file = {_toml(rmod_path.name)}"]
    into.mkdir(parents=True, exist_ok=True)
    (into / "mod.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copyfile(rmod_path, into / rmod_path.name)


def data_layout(game) -> str:
    """LittleGroove's name for the game's data layout: "public" (every pack in Data/PC/190852, the Steam release
    and the compat-2 to compat-5 branches) or "compat" (the original layout)."""
    return "public" if (Path(game) / "Data" / "PC" / "190852").is_dir() else "compat"


@dataclass
class RmodRun:
    packs: dict = field(default_factory=dict)     # pack file (resolved Path) -> Layered
    findings: list = field(default_factory=list)  # Finding
    opened: list = field(default_factory=list)    # the packs' files, closed by close()

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]

    def layered(self, path) -> Layered | None:
        return self.packs.get(Path(path).resolve())

    def changed_packs(self) -> dict:
        return {p: a for p, a in self.packs.items() if a.is_changed}

    def close(self) -> None:
        for base in self.opened:
            base.close()
        self.opened.clear()


def apply(game, rmod_paths, build_id: str | None = None, say=print) -> RmodRun:
    """Apply .rmod files, in order, to the packs of the game at `game` (read-only): each mod sees the ones before it,
    and a later mod wins where two change the same thing. Nothing is written; see RmodRun.packs. Call close() when
    the packs have been written."""
    from ruse_mod_engine import applier, edata
    game = Path(game).resolve()
    run = RmodRun()
    original = edata.open_dat

    def open_pack(path):
        p = Path(path).resolve()
        if game not in p.parents:
            return original(path)  # his own temporary copies of nested archives
        if p not in run.packs:
            base = Edat.open(str(p))
            run.opened.append(base)
            run.packs[p] = Layered(base, p)
        return run.packs[p]

    layout = data_layout(game)
    state: dict = {}  # which mod changed what, so a later mod overwriting an earlier one is reported
    with _LOCK:
        edata.open_dat = open_pack
        try:
            for path in map(Path, rmod_paths):
                try:
                    scripts = scripts_of(check(path))
                    res = applier.apply_mod(str(path), str(game), game_version=layout, deploy_state=state,
                                            target_build=build_id or None)
                except BuildError as exc:
                    run.findings.append(Finding("error", str(exc)))
                    continue
                except Exception as exc:  # his engine stopped on this mod: say which, and why
                    run.findings.append(Finding("error", f"{path.name}: the .rmod engine stopped: {exc!r}"))
                    continue
                name = path.name
                if scripts:
                    run.findings.append(Finding("warning", f"{name} changes {len(scripts)} of the game's scripts "
                                                           f"({', '.join(s.rsplit('/', 1)[-1] for s in scripts[:3])}"
                                                           f"{', …' if len(scripts) > 3 else ''}): scripts run "
                                                           f"inside the game, so use it only if you trust its "
                                                           f"author"))
                run.findings += [Finding("error", f"{name}: {e}") for e in res.errors]
                run.findings += [Finding("warning", f"{name}: {w}") for w in res.warnings]
                if res.requires_repair:
                    run.findings.append(Finding("warning", f"{name}: {len(res.requires_repair)} change(s) don't fit "
                                                           f"this game build and were left out (the first: "
                                                           f"{str(res.requires_repair[0]).strip()})"))
                if res.conflicts:
                    earlier = sorted({c.overwrote_mod for c in res.conflicts})
                    run.findings.append(Finding("note", f"{name}: {len(res.conflicts)} change(s) overwrite "
                                                        f"{', '.join(repr(m) for m in earlier)} (the first: "
                                                        f"{res.conflicts[0]})"))
                rep = res.map_report or {}
                if rep.get("map"):
                    run.findings.append(Finding("note", f"{name}: made for build {rep.get('from')}, moved to "
                                                        f"{rep.get('to')} ({rep.get('remapped', 0)} change(s) "
                                                        f"re-addressed)"))
                if rep.get("stale"):
                    run.findings.append(Finding("warning", f"{name}: {len(rep['stale'])} change(s) were made for "
                                                           f"values the game changed after build {rep.get('from')}; "
                                                           f"they're applied anyway"))
                say(f"rmod: {res.summary()}")
        finally:
            edata.open_dat = original
    return run
