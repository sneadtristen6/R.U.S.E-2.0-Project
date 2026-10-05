""".rmod mods (the format of LittleGroove's RUSE Mod Manager, used by most community mods) in our builds, applied by
his engine (`ruse_mod_engine`).

His applier rewrites game packs on disk. Here it works on `Layered` packs instead: a game pack read-only, with the
changes made so far on top. The applier's writes are only recorded, and the build writes the changed packs into the
modded copy like every other change, so the Steam install is never touched and no multi-GB pack is copied first. A
mod made for another game build is moved to this one with his version maps.

A .rmod may replace the game's own scripts (.xyz, and the .ipk archives that hold them; the owner's call, 2026-09-29,
an exception to PLAN.md decision 23 for .rmod mods), and the build says so; anything else that could run on the PC
(programs, PC scripts) is refused.

Before a set of .rmod mods is built, `clashes` says which of them don't go together (MOD_FORMAT.md §13): two mods
replacing the same file with different bytes is a hard clash that stops the build; a later mod overwriting values an
earlier one set is a soft one, shown before Play. Built on DomesticNukes and his Claude's report of 2026-09-30 (75
mods in one set: the build said 0 errors, the game crashed).
"""
from __future__ import annotations

import hashlib
import logging
import re
import shutil
import threading
import tomllib
from dataclasses import asdict, dataclass, field
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
                         f"bring programs.")
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


# --- do these mods work together? ---
# What DomesticNukes' set showed (2026-09-30): seven mods each brought their own copy of a map's script (effetmap.xyz),
# so only the last one's survived and the others' features vanished; two mods set the battleship's speed to 0 after
# Navy Mod had set it, so "ships don't move" was just the later mod winning. Nothing had said so before Play.

ARCHIVES = (".ipk", ".ppk", ".mpk", ".apk", ".gpk")  # nested archives (his edata.CONTAINER_EXTS): whole or edited inside
FILE_KINDS = {".xyz": "script", ".ipk": "script archive", ".bik": "video", ".wmv": "video", ".avi": "video",
              ".wav": "sound", ".ogg": "sound", ".mp3": "sound", ".mpk": "sound archive", ".dds": "picture",
              ".tgv": "picture", ".png": "picture", ".tga": "picture", ".jpg": "picture", ".scenario": "map file",
              ".win": "map file", ".sdb": "map file", ".tms": "map file", ".tmst": "map file", ".tgu1": "map file",
              ".dic": "text file"}
_IDENTITY = ("ClassNameForDebug", "AmmunitionId", "_ShortDatabaseName")  # his applier's name for a created object


def file_kind(path: str) -> str:
    """What kind of game file this is, for a sentence: "script", "video", "map file"... ("game data" when it's none
    of the known kinds)."""
    return FILE_KINDS.get(Path(path).suffix.lower(), "game data")


@dataclass
class Clash:
    """Mods that don't go together. A hard one stops the build: the set can't be played. A soft one is allowed, and
    shown before Play: the later mod overwrites what the earlier one changed."""
    kind: str        # hard: "file", "archive", "script", "create"; soft: "value", "text"
    hard: bool
    mods: list       # the mods' names, in the set's order; "archive": the mod replacing the archive first
    what: str        # the file, the new object's name, or the first value overwritten (Unit_Battleship.VitesseLineaire)
    message: str     # one sentence for the build report
    count: int = 1   # value/text: how many values (texts) the later mod overwrites
    file_kind: str = ""  # file/script: what kind of file it is ("script", "video", "map file", ...)

    def sides(self) -> tuple[str, str]:
        """The two sides of the sentence a screen shows: (a, b). file/script/create: all but the last mod, and the
        last; archive: the mod replacing the archive, and the mods editing inside it; value/text: the later mod (it
        wins), and the earlier one."""
        if self.kind == "archive":
            return self.mods[0], ", ".join(self.mods[1:])
        if self.kind in ("value", "text"):
            return self.mods[1], self.mods[0]
        return ", ".join(self.mods[:-1]), self.mods[-1]

    def view(self) -> dict:
        """Plain data for a screen: the fields, plus the two sides."""
        a, b = self.sides()
        return asdict(self) | {"a": a, "b": b}


def _and(names) -> str:
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


@dataclass
class _Edits:
    """What one .rmod touches, small enough to keep: file contents as digests, values as keys."""
    name: str
    files: dict = field(default_factory=dict)     # (dat, path lower) -> (digest, path): whole files of a pack
    inside: dict = field(default_factory=dict)    # (dat, archive lower, path lower) -> (digest, path, archive)
    archives: set = field(default_factory=set)    # (dat, archive lower): archives replaced whole
    edited_in: set = field(default_factory=set)   # (dat, archive lower): archives edited inside
    creates: dict = field(default_factory=dict)   # (dat, file, table, name) -> what to call it
    values: dict = field(default_factory=dict)    # (dat, file, table, match, prop) -> the example (Object.Prop)
    texts: dict = field(default_factory=dict)     # (dat, dic lower, key) -> the example (baseunite.dic N_UNI_15)


def _edits(mod) -> _Edits:
    e = _Edits(str(mod.name or mod.id))
    for group in mod.file_patches:
        for fp in group.files:
            path = fp.path.replace("\\", "/")
            if fp.container:
                archive = fp.container.replace("\\", "/")
                e.inside[(group.dat, archive.lower(), path.lower())] = (hashlib.sha1(fp.data).digest(), path, archive)
                e.edited_in.add((group.dat, archive.lower()))
            else:
                e.files[(group.dat, path.lower())] = (hashlib.sha1(fp.data).digest(), path)
                if path.lower().endswith(ARCHIVES):
                    e.archives.add((group.dat, path.lower()))
    for group in list(mod.patches) + list(mod.scenario_patches):
        where = getattr(group, "ndf", None) or getattr(group, "scenario", "")
        for ch in group.changes:
            match = ch.match or {}
            match_key = ";".join(f"{k}={v}" for k, v in sorted(match.items()))
            if ch.action == "create":
                name = next((str(v.value) for p in _IDENTITY if (v := (ch.set_props or {}).get(p)) is not None
                             and getattr(v, "value", None) not in (None, "")), "")
                if name:  # an unnamed new object can't clash by name (his rule: two mods adding their own units is fine)
                    e.creates[(group.dat, where, ch.table, name)] = f"{ch.table} '{name}'"
                continue
            props = list(ch.set_props or ()) if ch.action == "patch" else list(ch.del_props or ())
            first = next(iter(match.values()), None)
            head = str(first) if len(match) == 1 and isinstance(first, (str, int)) else ch.table
            for prop in props:
                e.values[(group.dat, where, ch.table, match_key, prop)] = f"{head}.{prop}"
    for group in mod.loc_patches:
        dic = group.dic.replace("\\", "/")
        for entry in group.entries:
            e.texts[(group.dat, dic.lower(), entry.key)] = f"{dic.rsplit('/', 1)[-1]} {entry.key}"
    for group in mod.sdb_patches:
        win = group.win.replace("\\", "/")
        for layer in group.layers:
            e.values[(group.dat, win.lower(), "sdb", "", str(layer.bit))] = f"{win.rsplit('/', 1)[-1]} layer {layer.bit}"
    return e


_edits_seen: dict[str, tuple[tuple, _Edits]] = {}  # file -> ((size, mtime), its edits): the check runs on every change


def rmod_of(path) -> Path | None:
    """The .rmod behind a path: the file itself, or the one a library folder wraps (mod.toml with [rmod] file=);
    None for anything else (our own mods keep their own rules, MOD_FORMAT.md §10.4)."""
    path = Path(path)
    if path.is_file():
        return path if path.suffix.lower() == EXTENSION else None
    manifest = path / "mod.toml"
    if not manifest.is_file():
        return None
    try:
        name = str(tomllib.loads(manifest.read_text(encoding="utf-8")).get("rmod", {}).get("file", ""))
    except (tomllib.TOMLDecodeError, OSError):
        return None
    return path / name if name and Path(name).name == name and (path / name).is_file() else None


def edits_of(path) -> _Edits | None:
    """What the .rmod at `path` (or wrapped in the folder `path`) touches, read once per file version. None for a
    path that isn't a .rmod, or one that can't be read (the build says so)."""
    from ruse_mod_engine import mod_format
    file = rmod_of(path)
    if file is None:
        return None
    try:
        stat = file.stat()
    except OSError:
        return None
    stamp = (stat.st_size, stat.st_mtime_ns)
    key = str(file.resolve())
    hit = _edits_seen.get(key)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    try:
        edits = _edits(mod_format.load(str(file)))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    _edits_seen[key] = (stamp, edits)
    return edits


def clashes(paths) -> list[Clash]:
    """Which of these .rmod mods (files, or library folders wrapping one; other paths are skipped) don't go
    together. Hard clashes first, then soft ones, in the set's order. Fast: only the .rmod files are read, once."""
    edits = [e for e in (edits_of(p) for p in paths) if e is not None]
    hard: list[Clash] = []
    # the same whole file, or the same file inside an archive, with different bytes (identical bytes are harmless)
    for attr, kind, inside in (("files", "file", False), ("inside", "script", True)):
        by_key: dict = {}
        for e in edits:
            for key, value in getattr(e, attr).items():
                by_key.setdefault(key, []).append((e.name, value))
        for key, items in by_key.items():
            if len({value[0] for _n, value in items}) < 2:
                continue
            names = list(dict.fromkeys(n for n, _v in items))
            path = items[0][1][1]
            where = f"inside {items[0][1][2].rsplit('/', 1)[-1]}" if inside else f"in {key[0].rsplit('/', 1)[-1]}"
            kind_word = file_kind(path)
            hard.append(Clash(kind, True, names, path, f"{_and(names)} each replace the same {kind_word}, "
                                                       f"{path.rsplit('/', 1)[-1]} ({path} {where}), with different "
                                                       f"contents, so only the last one's would count. Only one of "
                                                       f"them can be in a set.", file_kind=kind_word))
    # a whole archive replaced by one mod, edited inside by another (either order): the edits are thrown away
    for e in edits:
        for dat, archive in sorted(e.archives):
            others = [o.name for o in edits if o is not e and (dat, archive) in o.edited_in]
            if others:
                name = archive.rsplit("/", 1)[-1]
                hard.append(Clash("archive", True, [e.name] + others, name,
                                  f"{e.name} replaces the whole archive {name}, and {_and(others)} change(s) files "
                                  f"inside it; one of the two would be thrown away. Only one of them can be in a set."))
    # two new objects with the same name in the same file
    by_key = {}
    for e in edits:
        for key, label in e.creates.items():
            by_key.setdefault(key, []).append((e.name, label))
    for key, items in by_key.items():
        names = list(dict.fromkeys(n for n, _l in items))
        if len(names) > 1:
            hard.append(Clash("create", True, names, key[3], f"{_and(names)} each add a new {items[0][1]} in "
                                                             f"{key[1].rsplit('/', 1)[-1]}; two objects can't share a "
                                                             f"name. Only one of them can be in a set."))
    # soft: a later mod changes values (or texts) an earlier one changed too; the later wins, as the build says
    soft: list[Clash] = []
    for attr, kind, noun in (("values", "value", "value"), ("texts", "text", "text")):
        last: dict = {}    # key -> the latest mod so far that changed it
        pairs: dict = {}   # (earlier, later) -> [count, first example]
        for e in edits:
            for key, example in getattr(e, attr).items():
                prev = last.get(key)
                if prev is not None and prev is not e:
                    pair = pairs.setdefault((prev.name, e.name), [0, example])
                    pair[0] += 1
                last[key] = e
        for (earlier, later), (count, example) in pairs.items():
            soft.append(Clash(kind, False, [earlier, later], example,
                              f"{later} changes {count} {noun}{'s' if count > 1 else ''} {earlier} changed too, "
                              f"e.g. {example}; it comes later, so it wins. Put {earlier} after {later} if you want "
                              f"{earlier}'s {noun}s.", count=count))
    return hard + soft


def refusal(hard: list[Clash]) -> str:
    """The build's message when a set has hard clashes: every one, in plain words."""
    return (f"These mods can't be played together ({len(hard)} clash{'es' if len(hard) > 1 else ''}):\n"
            + "\n".join(f"- {c.message}" for c in hard) + "\nNothing was built.")


def best_order(paths) -> list[int]:
    """The order of these mods (indexes into `paths`, the set's order) in which each .rmod keeps as much as it can of
    what it changes. Where mods change the same values (or texts), the later one wins; so of the mods that share
    values, the one that changes more goes first and the one that changes less, which is there for those very
    values, after it. Each group of mods sharing values is ordered in its own places; the other mods, and mods that
    aren't .rmod files, keep theirs. Order can't mend a hard clash (the same file from two mods): those stay."""
    edits = [edits_of(p) for p in paths]
    owners: dict = {}
    for i, e in enumerate(edits):
        if e is not None:
            for key in [("value",) + k for k in e.values] + [("text",) + k for k in e.texts]:
                owners.setdefault(key, []).append(i)
    group = list(range(len(paths)))  # mods sharing a value, joined (union-find)

    def top(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for ids in owners.values():
        for i in ids[1:]:
            group[top(i)] = top(ids[0])
    groups: dict = {}
    for i, e in enumerate(edits):
        if e is not None:
            groups.setdefault(top(i), []).append(i)
    order = list(range(len(paths)))
    for places in groups.values():
        ranked = sorted(places, key=lambda i: (-(len(edits[i].values) + len(edits[i].texts)), i))
        for place, i in zip(places, ranked):
            order[place] = i
    return order


def overwritten(paths) -> list[int]:
    """How many of each mod's values and texts a later mod in this order overwrites (0 for mods that aren't .rmod)."""
    edits = [edits_of(p) for p in paths]
    last: dict = {}
    for i, e in enumerate(edits):
        if e is not None:
            for key in [("value",) + k for k in e.values] + [("text",) + k for k in e.texts]:
                last[key] = i
    lost = [0] * len(paths)
    for i, e in enumerate(edits):
        if e is not None:
            lost[i] = sum(1 for k in [("value",) + k for k in e.values] + [("text",) + k for k in e.texts]
                          if last[k] != i)
    return lost


def sizes(paths) -> list[int]:
    """How many values and texts each mod changes (0 for mods that aren't .rmod)."""
    return [len(e.values) + len(e.texts) if e is not None else 0 for e in (edits_of(p) for p in paths)]
