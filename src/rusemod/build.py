"""Build mods into game files: from mod folders to rebuilt packs (docs/MOD_FORMAT.md §2, §3, §6, §10).

  mod folders (mod.toml + src/**/*.rndf + text/*.csv)  ->  load order  ->  the pack's data files into the engine's
  model  ->  run the mods  ->  texts: game keys handed out, loc('...') values filled in  ->  write changed files back
  ->  rebuilt unit-data pack + fingerprint, and the rebuilt text pack (ZZ_Win.dat) when mods add or change texts

Value changes, new objects (clones, new units) and deletes all go through rusemod.model; texts through rusemod.loc.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import loc
from .edat import Edat
from .lock import fingerprint
from .model import ModelError, game_path, load, save
from .patch import Engine, Finding, Text, _walk_obj
from .resolve import ModInfo, load_order
from .rndf import parse

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# The game ships "_debuginfo" copies of a few data files that repeat every name of the main file. The game runs with
# them untouched (C2) or rewritten (C4); builds leave them exactly as shipped (PLAN.md §7, C4).
SHADOW = re.compile(r"_debuginfo\.cpp\.[a-z]*ndfbin$")


class BuildError(Exception):
    pass


def load_mod(path) -> tuple[ModInfo, list]:
    """A mod folder (mod.toml + src/**/*.rndf, files in path order, + text/*.csv), or a single .rndf file as a quick
    mod. Text rows end up in `ModInfo.texts`."""
    path = Path(path)
    if path.is_file() and path.suffix.lower() == ".rndf":
        mod_id = re.sub(r"[^a-z0-9-]+", "-", path.stem.lower()).strip("-") or "mod"
        info = ModInfo(mod_id)
        ops = parse(path.read_text(encoding="utf-8"), file=path.name, mod=mod_id)
    else:
        manifest_file = path / "mod.toml"
        if not manifest_file.is_file():
            raise BuildError(f"{path} has no mod.toml (and isn't a .rndf file)")
        try:
            manifest = tomllib.loads(manifest_file.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise BuildError(f"{manifest_file}: {exc}") from None
        m = manifest.get("mod", {})
        mod_id = m.get("id", "")
        if not _ID.match(mod_id):
            raise BuildError(f"{manifest_file}: [mod] id must be lowercase letters, digits and '-' (got {mod_id!r})")
        load_rules = manifest.get("load", {})
        info = ModInfo(mod_id, str(m.get("version", "0.0.0")), dict(manifest.get("dependencies", {})),
                       dict(manifest.get("optional", {})), list(load_rules.get("after", [])),
                       list(load_rules.get("before", [])), dict(manifest.get("conflicts", {})),
                       text_prefix=str(m.get("text_prefix", "")))
        src = path / "src"
        files = sorted(src.rglob("*.rndf"), key=lambda p: p.relative_to(src).as_posix().lower()) if src.is_dir() else []
        ops = []
        for f in files:
            ops += parse(f.read_text(encoding="utf-8"), file=f.relative_to(path).as_posix(), mod=mod_id)
        text_dir = path / "text"
        for f in sorted(text_dir.glob("*.csv"), key=lambda p: p.name.lower()) if text_dir.is_dir() else []:
            try:
                info.texts += loc.read_csv(f.read_text(encoding="utf-8"), f.stem.lower(), mod_id,
                                           f.relative_to(path).as_posix())
            except loc.TextError as exc:
                raise BuildError(str(exc)) from None
    info.when_mods = {mid for op in ops for mid, _rng, _neg in op.when}
    return info, ops


@dataclass
class BuildResult:
    order: list = field(default_factory=list)       # mod ids in load order
    findings: list = field(default_factory=list)    # Finding: errors, warnings, notes
    changed: dict = field(default_factory=dict)     # member path in the pack -> new bytes
    text_changed: dict = field(default_factory=dict)  # member path in the text pack (ZZ_Win.dat) -> new bytes
    fingerprint: bytes | None = None

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]


@dataclass
class PackModel:
    base: object          # the engine's model (patch.Game) of the pack's data files
    loaded: dict          # game path -> model.NdfFile, for writing back
    members: dict         # game path -> member path in the pack
    shadows: list         # debug-info copies, left as shipped


def load_pack(arc: Edat) -> PackModel:
    """The data files of `arc` as the engine's model, the way builds see them (debug-info copies left out)."""
    members, files, shadows = {}, {}, []
    for e in arc.entries:
        start = arc.data_offset + e.offset
        head = arc.raw[start:start + 12]
        if head[:4] == b"EUG0" and head[8:12] == b"CNDF":
            if SHADOW.search(game_path(e.path)):
                shadows.append(e.path)
                continue
            files[game_path(e.path)] = bytes(arc.read(e))
            members[game_path(e.path)] = e.path
    base, loaded = load(files)
    return PackModel(base, loaded, members, shadows)


def needs_text_pack(mods: list) -> bool:
    """Whether building `mods` [(ModInfo, ops)] needs the text pack (ZZ_Win.dat): some mod adds or changes texts."""
    return any(m.texts for m, _ in mods)


def fill_loc(game, keys: dict) -> list[str]:
    """Turn every loc('...') value into the game key its text got. Returns the loc keys no mod defines."""
    missing = []
    for obj in game.objects.values():
        for v in _walk_obj(obj):
            if isinstance(v, Text) and v.kind == "loc":
                if v.value in keys:
                    v.kind, v.value = "key", keys[v.value]
                elif v.value not in missing:
                    missing.append(v.value)
    return missing


def _reader(arc: Edat):
    entries = {e.path.lower(): e for e in arc.entries}

    def read(path: str):
        e = entries.get(path.lower())
        return bytes(arc.read(e)) if e is not None else None
    return read, entries


def build_pack(arc: Edat, mods: list, build_id: str = "0", text_arc: Edat | None = None) -> BuildResult:
    """Run `mods` [(ModInfo, ops)] on the data files of `arc`, and their texts on the .dic files of `text_arc`
    (ZZ_Win.dat; needed when a mod has text/*.csv). Nothing is written; see BuildResult.changed / text_changed."""
    order = load_order([m for m, _ in mods])
    by_id = {m.id: (m, ops) for m, ops in mods}
    result = BuildResult(order=[m.id for m in order])
    pack = load_pack(arc)
    base, loaded, members, shadows = pack.base, pack.loaded, pack.members, pack.shadows
    run = Engine(base).run([by_id[m.id] for m in order])
    result.findings = [Finding("note", n) for n in base.notes] + list(run.findings)
    if shadows:
        result.findings.insert(0, Finding("note", f"left {len(shadows)} debug-info copies as shipped "
                                                  f"({', '.join(p.rsplit(chr(92), 1)[-1] for p in shadows)})"))
    if run.errors:
        return result
    text_mods = [(m.id, m.text_prefix, m.texts) for m in order if m.texts]
    text_plan, read, entries = None, None, {}
    if text_mods:
        if text_arc is None:
            result.findings.append(Finding("error", "these mods add texts, which go into ZZ_Win.dat; it wasn't given"))
            return result
        read, entries = _reader(text_arc)
        try:
            text_plan = loc.plan(text_mods, loc.game_keys_of(read, sorted({r.dictionary for _, _, rows in text_mods
                                                                             for r in rows})))
        except loc.TextError as exc:
            result.findings.append(Finding("error", str(exc)))
            return result
        result.findings += [Finding("warning", message) for message, _row in text_plan.warnings]
    for key in fill_loc(run.game, text_plan.keys if text_plan else {}):
        result.findings.append(Finding("error", f"loc('{key}') has no text: no mod in the set defines {key!r} in "
                                                f"its text/*.csv"))
    if result.errors:
        return result
    notes: list = []
    try:
        changed = save(base, run.game, loaded, run.created, notes)
    except ModelError as exc:
        result.findings.append(Finding("error", str(exc)))
        return result
    result.findings += [Finding("note", n) for n in notes]
    result.changed = {members[p]: data for p, data in changed.items()}
    result.fingerprint = fingerprint(build_id, changed)
    if text_plan:
        try:
            text_changed, text_notes = loc.apply(text_plan, read)
        except loc.TextError as exc:
            result.findings.append(Finding("error", str(exc)))
            return result
        result.findings += [Finding("note", n) for n in text_notes]
        result.text_changed = {entries[p.lower()].path: data for p, data in text_changed.items()}
    return result
