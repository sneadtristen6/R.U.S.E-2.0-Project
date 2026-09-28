"""Build mods into game files: from mod folders to a rebuilt pack (docs/MOD_FORMAT.md §2, §3, §10).

  mod folders (mod.toml + src/**/*.rndf)  ->  load order  ->  the pack's data files into the engine's model
  ->  run the mods  ->  write changed files back  ->  rebuilt pack + fingerprint

Value changes work end to end today; adding or removing objects is the bridge's next step (rusemod.model).
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .edat import Edat
from .lock import fingerprint
from .model import ModelError, game_path, load, save
from .patch import Engine, Finding
from .resolve import ModInfo, load_order
from .rndf import parse

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class BuildError(Exception):
    pass


def load_mod(path) -> tuple[ModInfo, list]:
    """A mod folder (mod.toml + src/**/*.rndf, files in path order), or a single .rndf file as a quick mod."""
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
                       list(load_rules.get("before", [])), dict(manifest.get("conflicts", {})))
        src = path / "src"
        files = sorted(src.rglob("*.rndf"), key=lambda p: p.relative_to(src).as_posix().lower()) if src.is_dir() else []
        ops = []
        for f in files:
            ops += parse(f.read_text(encoding="utf-8"), file=f.relative_to(path).as_posix(), mod=mod_id)
    info.when_mods = {mid for op in ops for mid, _rng, _neg in op.when}
    return info, ops


@dataclass
class BuildResult:
    order: list = field(default_factory=list)       # mod ids in load order
    findings: list = field(default_factory=list)    # Finding: errors, warnings, notes
    changed: dict = field(default_factory=dict)     # member path in the pack -> new bytes
    fingerprint: bytes | None = None

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]


def build_pack(arc: Edat, mods: list, build_id: str = "0") -> BuildResult:
    """Run `mods` [(ModInfo, ops)] on the data files of `arc`. Nothing is written; see BuildResult.changed."""
    order = load_order([m for m, _ in mods])
    by_id = {m.id: (m, ops) for m, ops in mods}
    result = BuildResult(order=[m.id for m in order])
    members, files = {}, {}
    for e in arc.entries:
        start = arc.data_offset + e.offset
        head = arc.raw[start:start + 12]
        if head[:4] == b"EUG0" and head[8:12] == b"CNDF":
            files[game_path(e.path)] = bytes(arc.read(e))
            members[game_path(e.path)] = e.path
    base, loaded = load(files)
    run = Engine(base).run([by_id[m.id] for m in order])
    result.findings = [Finding("note", n) for n in base.notes] + list(run.findings)
    if run.errors:
        return result
    try:
        changed = save(base, run.game, loaded)
    except ModelError as exc:
        result.findings.append(Finding("error", str(exc)))
        return result
    result.changed = {members[p]: data for p, data in changed.items()}
    result.fingerprint = fingerprint(build_id, changed)
    return result
