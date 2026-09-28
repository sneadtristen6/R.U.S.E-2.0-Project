"""The Studio's edits, kept as an ordinary mod file: `src/studio.rndf` in the mod's folder (MOD_FORMAT §5).

The file is the only record: the Studio reads it back to show what's been changed, and rewrites it after every
change, one `patch` block per object in address order. It only holds plain values (`Prop = 12` or
`Prop = [30, 30, 30, 30, 30]`); hand-written changes belong in other `.rndf` files of the same mod, which the Studio
never touches.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from ..patch import ListV, Num
from ..rndf import RndfError, parse

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


class ModEdits:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.file = self.folder / FILE
        self.edits: dict[tuple[str, str], Edit] = {}
        if self.file.is_file():
            try:
                ops = parse(self.file.read_text(encoding="utf-8"), file=FILE.as_posix(), mod=self.folder.name)
            except (RndfError, UnicodeDecodeError) as exc:
                raise EditsFileError(f"{self.file} has a mistake ({exc}). Fix it, or delete it to start over.") from exc
            for op in ops:
                value = _plain(op.value)
                if op.kind == "set" and value is not None and op.target:
                    self.edits[(op.target, op.path)] = Edit(op.target, op.path, value, op.share)

    @staticmethod
    def key(address: str, prop: str) -> tuple[str, str]:
        target, inside = split(address)
        return target, f"{inside}.{prop}" if inside else prop

    def get(self, address: str, prop: str):
        e = self.edits.get(self.key(address, prop))
        return e.value if e else None

    def set(self, address: str, prop: str, value, share: str | None = None) -> None:
        target, path = self.key(address, prop)
        self.edits[(target, path)] = Edit(target, path, value, share)
        self.save()

    def reset(self, address: str, prop: str) -> None:
        self.edits.pop(self.key(address, prop), None)
        self.save()

    def of(self, address: str) -> dict:
        """prop -> value for the edits made to this object (not its parts)."""
        target, inside = split(address)
        out = {}
        for (t, path), e in self.edits.items():
            head, _, prop = path.rpartition(".")
            if t == target and head == inside:
                out[prop] = e.value
        return out

    def edited(self) -> set[str]:
        """The named objects that have edits (on themselves or their parts)."""
        return {t for t, _p in self.edits}

    def save(self) -> None:
        blocks: dict[tuple, list] = {}
        for (target, path), e in self.edits.items():
            head, _, prop = path.rpartition(".")
            blocks.setdefault((target, head, e.share or ""), []).append((prop, e.value))
        out = [HEADER]
        for (target, head, share) in sorted(blocks):
            where = f"{target}:{head}" if head else target
            out.append(f"\npatch {share + ' ' if share else ''}{where}\n(\n")
            for prop, value in sorted(blocks[(target, head, share)], key=lambda pv: _natural(pv[0])):
                out.append(f"    {prop} = {literal(value)}\n")
            out.append(")\n")
        self.file.parent.mkdir(parents=True, exist_ok=True)
        part = self.file.with_name(self.file.name + ".partial")
        part.write_text("".join(out), encoding="utf-8")
        os.replace(part, self.file)  # never half a file, even if the Studio stops mid-write


def _natural(s: str):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]
