"""The Studio's edits, kept as an ordinary mod file: `src/studio.rndf` in the mod's folder (MOD_FORMAT §5).

The file is the only record: the Studio reads it back to show what's been changed, and rewrites it after every
change, one `patch` block per object in address order. It only holds plain values (`Prop = 12` or
`Prop = [30, 30, 30, 30, 30]`); hand-written changes belong in other `.rndf` files of the same mod, which the Studio
never touches.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from rusemod.patch import ListV, Num
from rusemod.rndf import RndfError, parse

FILE = Path("src") / "studio.rndf"
HEADER = ("// Made by the RUSE Studio, which rewrites this file after every change.\n"
          "// Hand-written changes belong in other .rndf files in src/.\n")


@dataclass
class Edit:
    target: str             # the named object: $/GFX/Everything/Descriptor_Unit_X
    path: str               # inside it: "SeuilMort", or "Weapons[class=TWeapon].Puissance" for a part
    value: object           # a number, or a list of numbers
    share: str | None = None


def split(address: str) -> tuple[str, str]:
    """An index address -> (named object, path inside it)."""
    target, _, inside = address.partition(":")
    return target, inside


def _plain(value):
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
    return "[" + ", ".join(number(v) for v in value) + "]" if isinstance(value, list) else number(value)


class EditsFileError(Exception):
    """src/studio.rndf can't be read (changed by hand). Nothing is written over it until it's fixed or deleted."""


SHARE_ORDER = {"shared": 0, "": 1, "own": 2}  # a change for every user of a part goes in before a unit takes its own
# copy of that part, so the copy has it too (MOD_FORMAT §10.5)


class ModEdits:
    """The Studio's changes in one mod. A change is keyed by the named object, the path to the value inside it, and
    how a part that several units use is changed: "shared" (for all of them), "own" (this unit gets its own copy), or
    "" (not a shared part)."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.file = self.folder / FILE
        self.edits: dict[tuple[str, str, str], Edit] = {}
        if self.file.is_file():
            try:
                ops = parse(self.file.read_text(encoding="utf-8"), file=FILE.as_posix(), mod=self.folder.name)
            except (RndfError, UnicodeDecodeError) as exc:
                raise EditsFileError(f"{self.file} has a mistake ({exc}). Fix it, or delete it to start over.") from exc
            for op in ops:
                value = _plain(op.value)
                if op.kind == "set" and value is not None and op.target:
                    self.edits[(op.target, op.path, op.share or "")] = Edit(op.target, op.path, value, op.share)

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

    def save(self) -> None:
        blocks: dict[tuple, list] = {}
        for (target, path, how), e in self.edits.items():
            head, _, prop = path.rpartition(".")
            blocks.setdefault((SHARE_ORDER[how], target, head, how), []).append((prop, e.value))
        out = [HEADER]
        for block in sorted(blocks):
            _order, target, head, how = block
            where = f"{target}:{head}" if head else target
            out.append(f"\npatch {how + ' ' if how else ''}{where}\n(\n")
            for prop, value in sorted(blocks[block], key=lambda pv: _natural(pv[0])):
                out.append(f"    {prop} = {literal(value)}\n")
            out.append(")\n")
        self.file.parent.mkdir(parents=True, exist_ok=True)
        part = self.file.with_name(self.file.name + ".partial")
        part.write_text("".join(out), encoding="utf-8")
        for attempt in range(20):  # never half a file, even if the Studio stops mid-write
            try:
                os.replace(part, self.file)
                return
            except PermissionError:  # Windows: something (an antivirus, an editor) has the file open for a moment
                if attempt == 19:
                    raise
                time.sleep(0.05)


def _natural(s: str):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]
