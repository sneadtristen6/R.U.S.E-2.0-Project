"""An .rmod mod (LittleGroove's RUSE Mod Manager format, `rusemod.rmod`) made into a mod the Studio can show and
change (the owner, 2026-10-10: "make a converter so it'll work between our mod and what our studio does").

Every value change of the mod that the Studio can show becomes a Studio change (the Studio writes them into
`src/studio.rndf`, `ruse_studio.edits`), so it's in the Units and All values tabs like any change made there.
Everything else stays an .rmod, smaller: new objects, deletions, whole files, texts, map layers and the values the
Studio can't spell yet. The build applies that .rmod first and the mod's other changes on top of it
(`rusemod.build.build_and_write`), so the converted mod plays as the original did.

A value change becomes a Studio change when:
- it's in the unit data (ZZ_GladPatchableWin.dat) and the game index has the NDF file it changes;
- its object is found on this game build the way LittleGroove's applier finds it (his build-to-build index map, then
  `find_instances`: by name, by number, by anchor, or every object of a class), the object existed before the mod
  (not one the mod makes), the mod doesn't delete it, and it has a `$/` name or is part of an object that has one;
- the object already has that value (his applier can add a value an object hasn't got; a Studio change can't);
- the value is a number, a yes/no, a list of them, a text, a file path or a link to a named object (or none);
- no change the .rmod keeps sets the same value of the same object (the order between the two would change).
"""
from __future__ import annotations

import collections
import copy
import re
import sqlite3
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .build import DEFAULT_PACK, find_pack
from .edat import Edat
from .patch import ListV, Num, Ref, Text
from .rndf import literal

NUMBERS = {"Bool": "bool", "Int8": "int8", "Int16": "int16", "UInt16": "uint16", "Int32": "int32",
           "UInt32": "uint32", "Int64": "int64", "Float32": "float32", "Float64": "float64"}
TEXTS = {"StringRef": "string", "PathRef": "path", "WideString": "wstr"}
_LIST = re.compile(r"List<(\w+)>")


@dataclass
class Change:
    """One Studio change: the named object, the path inside it, the value as mod-file text (None: the value is taken
    out, `delete Prop`), and "shared" for a part inside the object (the .rmod changes that part for every unit
    using it, MOD_FORMAT §10.5)."""
    target: str
    path: str
    value: str | None
    share: str = ""


@dataclass
class Converted:
    changes: list = field(default_factory=list)           # Change
    kept: object = None                                    # the RuseMod left as an .rmod, or None when nothing is
    counts: collections.Counter = field(default_factory=collections.Counter)  # "values" + what stays, by kind

    def kept_counts(self) -> dict:
        """{kind: how many stay in the .rmod} (new objects, deletions, values the Studio can't show yet, whole
        files, texts, map layers, map changes)."""
        return {k: v for k, v in self.counts.items() if k != "values" and v}


def _index_addresses(index_path, ndf_path: str) -> dict[int, str]:
    """{instance number: Studio address} of the NDF file at `ndf_path` in the unit data pack, from the game index."""
    db = sqlite3.connect(f"file:{Path(index_path).as_posix()}?mode=ro", uri=True)
    try:
        rows = db.execute("SELECT f.id, p.name FROM file f JOIN pack p ON p.id = f.pack WHERE lower(f.game_path) = ?",
                          (ndf_path.replace("\\", "/").lower(),)).fetchall()
        ids = [fid for fid, name in rows if str(name or "").lower() == DEFAULT_PACK.lower()] or [r[0] for r in rows]
        if not ids:
            return {}
        return dict(db.execute("SELECT idx, address FROM object WHERE file = ? AND address IS NOT NULL AND "
                               "address != ''", (ids[0],)))
    finally:
        db.close()


def _num(kind: str, value) -> Num:
    if kind == "bool":
        return Num(kind, Decimal(1 if value else 0))
    if kind.startswith("float"):
        return Num(kind, Decimal(repr(float(value))))
    return Num(kind, Decimal(int(value)))


class _Group:
    """One patch group of the mod (one NDF file of the unit data) read against this game build."""

    def __init__(self, ndf, addresses: dict[int, str], index_map: dict | None):
        self.ndf = ndf
        self.addresses = addresses
        self.before = len(ndf.instances)  # the objects the game has; the mod's own come after
        self.index_map = index_map or {}
        # his ObjRef numbers move with the build map's offsets: those links aren't followed here
        self.moved_refs = bool(self.index_map.get("_instance_segments") or self.index_map.get("_instance_offset")
                               or self.index_map.get("_class_map"))

    def targets(self, change) -> list:
        """[(instance number, instance)] of the game's own objects the change touches on this build, as his applier
        finds them (his build-to-build index map first: applier._translate_change's last branch)."""
        m = dict(change.match or {})
        if "_index" in m and self.index_map:
            moved = self.index_map.get(str(int(m["_index"])))
            if moved is not None:
                m["_index"] = str(moved)
        return [(i, inst) for i, inst in self.ndf.find_instances(change.table, m or None) if i < self.before]

    def has(self, inst, prop: str) -> bool:
        p = self.ndf.prop_by_name_and_class(prop, inst.class_index)
        return p is not None and inst.get(p.index) is not None

    def link(self, value):
        """A link to a named object (Ref), nil (Ref(None)), or None when it can't be written as one."""
        if value is None:
            return Ref(None)
        if not isinstance(value, dict):
            return None
        idx = None
        if "stable_ref" in value and "key_val" in value:
            hits = self.ndf.find_instances(str(value.get("class_name", "")), {value["stable_ref"]: value["key_val"]})
            idx = hits[0][0] if len(hits) == 1 else None
        elif "anchor" in value:
            idx = self.ndf.resolve_anchor(value["anchor"])
        elif "inst" in value and not self.moved_refs:
            idx = int(value["inst"])
        if idx is None or idx >= self.before:
            return None
        address = self.addresses.get(idx, "")
        return Ref(address) if address.startswith("$/") and ":" not in address else None

    def value(self, vdef) -> str | None:
        """A value as mod-file text, or None when the Studio can't spell it yet."""
        t, v = vdef.type_name, vdef.value
        model = None
        try:
            if t in NUMBERS:
                model = _num(NUMBERS[t], v)
            elif t in TEXTS:
                model = Text(TEXTS[t], str(v))
            elif t == "ObjRef":
                model = self.link(v)
            elif (m := _LIST.fullmatch(t)) and isinstance(v, list):
                inner = m.group(1)
                if inner in NUMBERS:
                    model = ListV([_num(NUMBERS[inner], x) for x in v])
                elif inner in TEXTS:
                    model = ListV([Text(TEXTS[inner], str(x)) for x in v])
                elif inner == "ObjRef":
                    items = [self.link(x) for x in v]
                    model = ListV(items) if all(x is not None for x in items) else None
            return None if model is None else literal(model)
        except (ValueError, TypeError, ArithmeticError):
            return None


def _kind(change) -> str:
    return {"create": "new objects", "delete": "deletions"}.get(change.action, "values the Studio can't show yet")


def _count_rest(out: Converted, mod) -> None:
    out.counts["whole files"] += sum(len(g.files) for g in mod.file_patches)
    out.counts["texts"] += sum(len(g.entries) for g in mod.loc_patches)
    out.counts["map layers"] += sum(len(g.layers) for g in mod.sdb_patches)
    out.counts["map changes"] += sum(len(g.changes) for g in mod.scenario_patches)


def _kept_whole(out: Converted, mod) -> Converted:
    for g in mod.patches:
        for ch in g.changes:
            out.counts[_kind(ch)] += 1
    _count_rest(out, mod)
    out.kept = mod
    return out


def convert(rmod_path, game, index_path) -> Converted:
    """What of the .rmod at `rmod_path` becomes Studio changes on the game at `game` (its game index at
    `index_path`), and what stays an .rmod (the module's docstring). Reads only."""
    from ruse_mod_engine import mod_format, ndfbin
    from ruse_mod_engine.applier import resolve_dat_for_version
    from . import rmod as rmods
    from .steam import build_of

    rmod_path, game = Path(rmod_path), Path(game)
    original = mod_format.load(str(rmod_path))
    out = Converted()
    if rmod_path.name.lower().endswith(".compat.rmod"):  # made for the original game's layout: kept whole
        return _kept_whole(out, original)
    work = mod_format.load(str(rmod_path))
    build = build_of(game)
    if build and work.game_version and str(work.game_version) != str(build):
        from ruse_mod_engine import version_map
        work, _report = version_map.remap_mod(work, str(work.game_version), str(build))
    if len(work.patches) != len(original.patches) or any(len(a.changes) != len(b.changes)
                                                         for a, b in zip(work.patches, original.patches)):
        return _kept_whole(out, original)  # the build map reshaped it: nothing can be matched back
    unit_pack = find_pack(game, DEFAULT_PACK)
    layout = rmods.data_layout(game)
    # per change: (group, change, [(prop, [Change per object] or None when it stays)] or None when it stays whole,
    # the objects it touches)
    plans = []
    relinked: set[str] = set()   # objects whose links (or values taken out) the mod changes, by address
    group_addresses: dict[int, dict] = {}
    for gi, group in enumerate(work.patches):
        dat = game / resolve_dat_for_version(group.dat, layout)
        same_pack = unit_pack is not None and dat.is_file() and dat.resolve() == unit_pack.resolve()
        addresses = group_addresses[gi] = _index_addresses(index_path, group.ndf) if same_pack else {}
        data = None
        if addresses:
            with Edat.open(str(dat)) as arc:
                entry = arc.entry(group.ndf.replace("\\", "/")) or arc.entry(group.ndf.replace("/", "\\"))
                data = bytes(arc.read(entry)) if entry is not None else None
        if data is None:
            plans += [(gi, ci, None, []) for ci in range(len(group.changes))]
            continue
        g = _Group(ndfbin.read(data), addresses, group.index_map.get(layout))
        deleted = {i for ch in group.changes if ch.action == "delete" for i, _inst in g.targets(ch)}
        for ci, ch in enumerate(group.changes):
            if ch.action not in ("patch", "delete_props"):
                plans.append((gi, ci, None, []))
                continue
            hits = g.targets(ch)
            if ch.action == "delete_props" or any("ObjRef" in v.type_name or v.type_name == "$ref"
                                                  for v in (ch.set_props or {}).values()):
                relinked.update(addresses[i] for i, _inst in hits if i in addresses)
            # a Studio change names its object: one with no name of its own (a scenery file's `<file>#<n>`) stays
            if not hits or any(i in deleted or not addresses.get(i, "").startswith("$/") for i, _inst in hits):
                plans.append((gi, ci, None, hits))
                continue
            props = []
            for prop in (list(ch.set_props or {}) if ch.action == "patch" else list(ch.del_props or [])):
                text = g.value(ch.set_props[prop]) if ch.action == "patch" else None
                if (ch.action == "patch" and text is None) or not all(g.has(inst, prop) for _i, inst in hits):
                    props.append((prop, None))
                    continue
                made = []
                for i, _inst in hits:
                    target, _sep, inside = addresses[i].partition(":")
                    made.append((i, Change(target, f"{inside}.{prop}" if inside else prop, text,
                                           "shared" if inside else "")))
                props.append((prop, made))
            plans.append((gi, ci, props, hits))
    # a value of an object that a change the .rmod keeps sets too: both stay in the .rmod, so their order holds
    kept_keys = set()
    for gi, ci, props, hits in plans:
        ch = work.patches[gi].changes[ci]
        names = list(ch.set_props or {}) + list(ch.del_props or [])
        stay = names if props is None else [p for p, made in props if made is None]
        kept_keys.update((gi, i, p) for i, _inst in hits for p in stay)

    def through_relinked(i: int, addresses: dict) -> bool:
        """Whether the way to object i passes an object whose links the mod changes. His applier changes the
        object found on the game's own data; a Studio change walks its path on the changed data, so it would land
        on whatever the new link points at (Zombie Mode re-links units' parts)."""
        target, _sep, inside = addresses.get(i, "").partition(":")
        segs = inside.split(".") if inside else []
        return any(a in relinked for a in [target] + [f"{target}:{'.'.join(segs[:k])}" for k in range(1, len(segs))]
                   ) if segs else False
    final: dict[tuple, Change] = {}
    kept_mod = copy.deepcopy(original)
    for g in kept_mod.patches:
        g.changes = []
    for gi, ci, props, hits in plans:
        orig = original.patches[gi].changes[ci]
        if props is None:
            kept_mod.patches[gi].changes.append(orig)
            out.counts[_kind(orig)] += 1
            continue
        ids = [i for i, _inst in hits]
        stay = [p for p, made in props if made is None or any((gi, i, p) in kept_keys for i in ids)
                or any(through_relinked(i, group_addresses[gi]) for i, _c in made)]
        for p, made in props:
            if p in stay:
                continue
            for _i, c in made:
                final.pop((c.target, c.path, c.share), None)  # a later change of the same value wins (his applier)
                final[(c.target, c.path, c.share)] = c
        if stay:
            part = copy.deepcopy(orig)
            if orig.action == "patch":
                part.set_props = {p: v for p, v in orig.set_props.items() if p in stay}
            else:
                part.del_props = [p for p in orig.del_props if p in stay]
            kept_mod.patches[gi].changes.append(part)
            out.counts["values the Studio can't show yet"] += 1
    kept_mod.patches = [g for g in kept_mod.patches if g.changes or g.import_add or g.import_remove or g.export_add
                        or g.export_remove]
    out.changes = list(final.values())
    out.counts["values"] = len(out.changes)
    _count_rest(out, original)
    empty = not (kept_mod.patches or kept_mod.file_patches or kept_mod.loc_patches or kept_mod.sdb_patches
                 or kept_mod.scenario_patches)
    out.kept = None if empty else kept_mod
    return out


def write_kept(converted: Converted, folder, rmod_name: str) -> None:
    """What a conversion keeps as an .rmod, into the mod folder `folder` (an .rmod mod's: mod.toml + `rmod_name`):
    the smaller .rmod over the old one; when nothing is kept, the .rmod and mod.toml's [rmod] table go."""
    from ruse_mod_engine import mod_format
    from .package import MANIFEST
    folder = Path(folder)
    file = folder / rmod_name
    if converted.kept is None:
        file.unlink(missing_ok=True)
        manifest = folder / MANIFEST
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(re.sub(r"(?ms)^\[rmod\]\n.*?(?=^\[|\Z)", "", text).rstrip("\n") + "\n", encoding="utf-8")
    else:
        mod_format.save(converted.kept, str(file))
