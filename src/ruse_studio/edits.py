"""The Studio's edits, kept as ordinary mod files in the mod's folder (MOD_FORMAT §5, §6): `src/studio.rndf` for the
changes and the new units, and `text/studio.baseunite.csv` for the new units' names.

The files are the only record: the Studio reads them back to show what's been changed, and rewrites them after every
change: the new units first (one `clone` block each, holding that unit's own values), then one `patch` block per
object in address order. They only hold plain values (`Prop = 12` or `Prop = [30, 30, 30, 30, 30]`), links to named
objects (`Ammunition = $/GFX/Everything/Ammo_X`: which ammo a weapon fires) and the new units' names; hand-written
changes belong in other `.rndf` and `.csv` files of the same mod, which the Studio never touches. A copy that keeps
its source's name in game (an ammunition) has no names row.
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from rusemod import loc
from rusemod.patch import ListV, Num, Ref, Text
from rusemod.rndf import RndfError, parse

FILE = Path("src") / "studio.rndf"
NAMES_FILE = Path("text") / "studio.baseunite.csv"  # into baseunite.dic, the game's unit names (MOD_FORMAT §6)
HEADER = ("// Made by the RUSE Studio, which rewrites this file after every change.\n"
          "// Hand-written changes belong in other .rndf files in src/.\n")
NAME_PROP = "NameInMenuToken"


class Link(str):
    """A value that points at a named object, by its address ($/GFX/Everything/Ammo_X)."""


@dataclass
class Edit:
    target: str             # the named object: $/GFX/Everything/Descriptor_Unit_X
    path: str               # inside it: "SeuilMort", or "Weapons[class=TWeapon].Puissance" for a part
    value: object           # a number, a list of numbers, or a Link
    share: str | None = None


@dataclass
class NewUnit:
    target: str             # $/GFX/Everything/Descriptor_Unit_X: the copy's own address
    source: str             # the unit it copies
    name: str               # the name shown in game (the same in every language, for now)
    named: bool = True      # False: it keeps its source's name in game (a copied ammunition), so no names row

    @property
    def text_key(self) -> str:
        """Its name's row in text/studio.baseunite.csv, which the clone refers to with loc('…')."""
        return f"studio.{self.target.rsplit('/', 1)[-1]}.name"


def split(address: str) -> tuple[str, str]:
    """An index address -> (named object, path inside it)."""
    target, _, inside = address.partition(":")
    return target, inside


def _plain(value):
    if isinstance(value, Ref):
        return Link(value.target) if value.target else None
    if isinstance(value, Num):
        return int(value.value) if value.value == value.value.to_integral() else float(value.value)
    if isinstance(value, ListV) and value.items and all(isinstance(x, Num) for x in value.items):
        return [_plain(x) for x in value.items]
    return None


def number(x) -> str:
    """A number as .rndf text, never in exponent form."""
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, int) or float(x).is_integer():
        return str(int(x))
    return format(Decimal(repr(float(x))).normalize(), "f")


def literal(value) -> str:
    if isinstance(value, Link):
        return str(value)
    return "[" + ", ".join(number(v) for v in value) + "]" if isinstance(value, list) else number(value)


_KEY_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"


def game_key(target: str) -> str:
    """The game key (FORMATS.md §4) of a new unit's name: 10 characters made from the unit's address, so it's the same
    on every PC and two Studio units never get the same one. The game's own keys are readable names (LD_UNI_135), so
    ours start with S and can't be mistaken for one."""
    n = int.from_bytes(hashlib.sha256(target.encode("utf-8")).digest()[:8], "big")
    out = []
    for _ in range(9):
        n, r = divmod(n, len(_KEY_CHARS))
        out.append(_KEY_CHARS[r])
    return "S" + "".join(out)


def plain_name(target: str) -> str:
    """A name to show for a copy whose names file is gone (or that has no names row, like a copied ammunition):
    Descriptor_Unit_Super_Sherman -> Super Sherman, Ammo_Hot_75 -> Hot 75."""
    return re.sub(r"^(Descriptor_[A-Za-z]+_|Ammo_)", "", target.rsplit("/", 1)[-1]).replace("_", " ")


class EditsFileError(Exception):
    """src/studio.rndf (or the names file) can't be read (changed by hand). Nothing is written over it until it's
    fixed or deleted."""


SHARE_ORDER = {"shared": 0, "": 1, "own": 2}  # a change for every user of a part goes in before a unit takes its own
# copy of that part, so the copy has it too (MOD_FORMAT §10.5)


class ModEdits:
    """The Studio's changes in one mod. A change is keyed by the named object, the path to the value inside it, and
    how a part that several units use is changed: "shared" (for all of them), "own" (this unit gets its own copy), or
    "" (not a shared part). New units are copies of a unit the game has; their own values are changes like any other,
    written inside the copy's block."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.file = self.folder / FILE
        self.names_file = self.folder / NAMES_FILE
        self.edits: dict[tuple[str, str, str], Edit] = {}
        self.new_units: dict[str, NewUnit] = {}
        names = self._read_names()
        if self.file.is_file():
            try:
                ops = parse(self.file.read_text(encoding="utf-8"), file=FILE.as_posix(), mod=self.folder.name)
            except (RndfError, UnicodeDecodeError) as exc:
                raise EditsFileError(f"{self.file} has a mistake ({exc}). Fix it, or delete it to start over.") from exc
            for op in ops:
                if op.kind == "clone" and op.target and op.source:
                    self._read_clone(op, names)
                    continue
                value = _plain(op.value)
                if op.kind == "set" and value is not None and op.target:
                    self.edits[(op.target, op.path, op.share or "")] = Edit(op.target, op.path, value, op.share)

    def _read_names(self) -> dict[str, str]:
        """text key -> the English name, from the names file (the other languages get it too, MOD_FORMAT §6)."""
        if not self.names_file.is_file():
            return {}
        try:
            rows = loc.read_csv(self.names_file.read_text(encoding="utf-8"), "baseunite", self.folder.name,
                                NAMES_FILE.as_posix())
        except (loc.TextError, UnicodeDecodeError) as exc:
            raise EditsFileError(f"{self.names_file} has a mistake ({exc}). Fix it, or delete it to start over.") from exc
        return {r.key: r.texts["us"] for r in rows}

    def _read_clone(self, op, names: dict[str, str]) -> None:
        unit = NewUnit(op.target, op.source, plain_name(op.target), named=False)
        for b in op.body:
            if b.kind != "set":
                continue
            if b.path == NAME_PROP and isinstance(b.value, Text) and b.value.kind == "loc":
                unit.name, unit.named = names.get(b.value.value, unit.name), True
                continue
            value = _plain(b.value)
            if value is not None:
                self.edits[(op.target, b.path, "")] = Edit(op.target, b.path, value)
        self.new_units[op.target] = unit

    @staticmethod
    def key(address: str, prop: str, share: str | None = None) -> tuple[str, str, str]:
        target, inside = split(address)
        return target, f"{inside}.{prop}" if inside else prop, share or ""

    def get(self, address: str, prop: str, share: str | None = None):
        e = self.edits.get(self.key(address, prop, share))
        return e.value if e else None

    def set(self, address: str, prop: str, value, share: str | None = None) -> None:
        target, path, how = self.key(address, prop, share)
        self.edits[(target, path, how)] = Edit(target, path, value, how or None)
        self.save()

    def reset(self, address: str, prop: str, share: str | None = None) -> None:
        self.edits.pop(self.key(address, prop, share), None)
        self.save()

    def of(self, address: str, share: str | None = None) -> dict:
        """prop -> value for the edits made to this object (not its parts), made this way (`share`)."""
        target, inside = split(address)
        out = {}
        for (t, path, how), e in self.edits.items():
            head, _, prop = path.rpartition(".")
            if t == target and head == inside and how == (share or ""):
                out[prop] = e.value
        return out

    def edited(self) -> set[str]:
        """The named objects that have edits (on themselves or their parts)."""
        return {t for t, _p, _s in self.edits}

    def shared(self) -> set[str]:
        """The addresses of parts changed for every unit that uses them."""
        return {f"{t}:{p.rpartition('.')[0]}" for t, p, how in self.edits if how == "shared"}

    # --- new units ---
    def add_unit(self, target: str, source: str, name: str, values: dict, named: bool = True) -> NewUnit:
        """A new unit: a copy of `source` at `target`, called `name` in game, with `values` (prop -> value) of its
        own from the start (its price, and its nation and factory when it goes in another build menu). `named`
        False: a copy that keeps its source's name in game (an ammunition); `name` is only what the Studio calls it."""
        unit = NewUnit(target, source, name, named)
        self.new_units[target] = unit
        for prop, value in values.items():
            self.edits[(target, prop, "")] = Edit(target, prop, value)
        self.save()
        return unit

    def remove_unit(self, target: str) -> None:
        """Delete a new unit: its copy, every change made to it and its parts, and its name."""
        self.new_units.pop(target, None)
        for key in [k for k in self.edits if k[0] == target]:
            del self.edits[key]
        self.save()

    def new_unit_of(self, address: str) -> NewUnit | None:
        """The new unit an address belongs to (the unit itself, or a part inside it), or None."""
        return self.new_units.get(split(address)[0])

    # --- writing ---
    def save(self) -> None:
        out = [HEADER]
        for target in sorted(self.new_units):  # copies first: a new unit starts as a copy of the game's own unit
            unit = self.new_units[target]
            out.append(f"\nexport {target.rsplit('/', 1)[-1]} is clone {unit.source}\n(\n")
            if unit.named:
                out.append(f"    {NAME_PROP} = loc('{unit.text_key}')\n")
            own = [(path, e.value) for (t, path, how), e in self.edits.items()
                   if t == target and how == "" and "." not in path]
            for prop, value in sorted(own, key=lambda pv: _natural(pv[0])):
                out.append(f"    {prop} = {literal(value)}\n")
            out.append(")\n")
        blocks: dict[tuple, list] = {}
        for (target, path, how), e in self.edits.items():
            head, _, prop = path.rpartition(".")
            if target in self.new_units and how == "" and not head:
                continue  # written inside the copy's block above
            blocks.setdefault((SHARE_ORDER[how], target, head, how), []).append((prop, e.value))
        for block in sorted(blocks):
            _order, target, head, how = block
            where = f"{target}:{head}" if head else target
            out.append(f"\npatch {how + ' ' if how else ''}{where}\n(\n")
            for prop, value in sorted(blocks[block], key=lambda pv: _natural(pv[0])):
                out.append(f"    {prop} = {literal(value)}\n")
            out.append(")\n")
        self._write(self.file, "".join(out))
        named = [self.new_units[t] for t in sorted(self.new_units) if self.new_units[t].named]
        if named:
            names = io.StringIO()
            writer = csv.writer(names, lineterminator="\n")
            writer.writerow(["key", "game_key", "us"])
            for unit in named:
                writer.writerow([unit.text_key, game_key(unit.target), unit.name])
            self._write(self.names_file, names.getvalue())
        elif self.names_file.is_file():
            self.names_file.unlink()

    @staticmethod
    def _write(file: Path, text: str) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        part = file.with_name(file.name + ".partial")
        part.write_text(text, encoding="utf-8")
        for attempt in range(20):  # never half a file, even if the Studio stops mid-write
            try:
                os.replace(part, file)
                return
            except PermissionError:  # Windows: something (an antivirus, an editor) has the file open for a moment
                if attempt == 19:
                    raise
                time.sleep(0.05)


def _natural(s: str):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]
