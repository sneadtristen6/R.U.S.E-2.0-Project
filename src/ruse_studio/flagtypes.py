"""Flag types of the modder's own (StudioApi's FlagTypeCalls), from a player's ask (advolt284 on Discord, 2026-10-22:
a unit flag made from scratch, "a flag that say that unit can drive into water") and the owner's way of doing it: "you
want to make a new flag type. Select from the existing flags and how they work ... You're just checking boxes."

A flag number the game doesn't know does nothing: the game only acts on the flags it reads (rusemod/flaginfo.toml
explains all 105). So a flag type is a name of the modder's own standing for some of the game's flags turned on and
some turned off, given to a unit in one go. Giving it is an ordinary change of the unit's flags (InitialFlagSet) in the
mod: the build and the game see nothing new, and the Studio's flag checks (flag_check) judge the result as they judge
any other change.

The mod keeps its types in flag-types.toml, each with what giving it changed on every unit that has it (the flags it
added, the ones it took away), so taking it off puts back exactly what was there, and changing or deleting a type
changes every unit that has it. A unit's types are given in the file's order: taking one off unwinds them all (the last
given first) and gives the others again, so two types that touch the same flag always end the same way.
"""
from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

FILE = "flag-types.toml"
FLAGS = "InitialFlagSet"
NAME_MOST, ABOUT_MOST, TYPES_MOST = 40, 400, 200
HEADER = ("# Flag types made in the RUSE Studio (a unit's flags: Flag types). Each is a name for some of the game's own\n"
          "# flags turned on and off; a unit given one has those flags in its own flag list (src/studio.rndf), and\n"
          "# `unit` says what giving it changed there, so taking it off puts that back. The build doesn't read this\n"
          "# file. The Studio rewrites it after every change.\n")


class FlagTypeError(Exception):
    """flag-types.toml can't be read (changed by hand): nothing is written over it until it's fixed."""


@dataclass
class FlagType:
    name: str
    about: str = ""
    on: list[int] = field(default_factory=list)
    off: list[int] = field(default_factory=list)
    # unit address -> (the flags giving it added, the flags it took away), in the order the units got it
    units: dict[str, tuple[list[int], list[int]]] = field(default_factory=dict)


def _flags(value, where: str) -> list[int]:
    if not isinstance(value, list) or not all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in value):
        raise FlagTypeError(f"{where}: a list of flag numbers")
    return list(dict.fromkeys(value))


def read_types(folder: Path) -> list[FlagType]:
    """The mod's flag types, in their file's order ([] when it has none). FlagTypeError for a file with a mistake."""
    path = Path(folder) / FILE
    if not path.is_file():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise FlagTypeError(f"{path} has a mistake ({exc}). Fix it, or delete it to start over.") from None
    out, names = [], set()
    for n, t in enumerate(data.get("type", [])):
        where = f"{path.name}: type {n + 1}"
        if not isinstance(t, dict) or not isinstance(t.get("name"), str) or not t["name"].strip():
            raise FlagTypeError(f"{path} has a mistake ({where} needs a name). Fix it, or delete it to start over.")
        try:
            units = {}
            for u in t.get("unit", []):
                if not isinstance(u, dict) or not isinstance(u.get("address"), str):
                    raise FlagTypeError(f"{where}: a unit needs its address")
                units[u["address"]] = (_flags(u.get("added", []), where), _flags(u.get("removed", []), where))
            ft = FlagType(t["name"].strip(), str(t.get("about", "")), _flags(t.get("on", []), where),
                          _flags(t.get("off", []), where), units)
        except FlagTypeError as exc:
            raise FlagTypeError(f"{path} has a mistake ({exc}). Fix it, or delete it to start over.") from None
        if ft.name.lower() in names:
            raise FlagTypeError(f"{path} has a mistake (two types are called {ft.name}). Fix it, or delete it to "
                                f"start over.")
        names.add(ft.name.lower())
        out.append(ft)
    return out


def types_toml(types: list[FlagType]) -> str:
    """flag-types.toml for `types` (read_types reads it back the same)."""
    q = lambda s: json.dumps(s, ensure_ascii=False)  # noqa: E731 (a TOML basic string)
    nums = lambda xs: "[" + ", ".join(str(n) for n in xs) + "]"  # noqa: E731
    out = [HEADER]
    for t in types:
        out.append(f"\n[[type]]\nname = {q(t.name)}\nabout = {q(t.about)}\non = {nums(t.on)}\noff = {nums(t.off)}\n")
        for address, (added, removed) in t.units.items():
            out.append(f"\n[[type.unit]]\naddress = {q(address)}\nadded = {nums(added)}\nremoved = {nums(removed)}\n")
    return "".join(out)


def give(flags: list[int], t: FlagType) -> tuple[list[int], list[int], list[int]]:
    """A unit's flags with type `t` given: (the flags, the ones it added, the ones it took away)."""
    added = [n for n in t.on if n not in flags]
    removed = [n for n in t.off if n in flags]
    return [n for n in flags if n not in t.off] + added, added, removed


def take(flags: list[int], added: list[int], removed: list[int]) -> list[int]:
    """A unit's flags with a type it was given taken off again: what it added out, what it took away back."""
    return [n for n in flags if n not in added] + [n for n in removed if n not in flags]


class FlagTypeCalls:
    """Mixed into StudioApi: uses its _open, _edits, _resolve, _saving, _editable and flag_check."""

    def _types_folder(self):
        from .api import StudioError
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: flag types are saved in a mod.")
        return edits

    def _read_types(self, folder) -> list[FlagType]:
        from .api import StudioError
        try:
            return read_types(folder)
        except FlagTypeError as exc:
            raise StudioError(str(exc)) from None

    def flag_types(self, address: str = "") -> dict:
        """The current mod's flag types: {"types": [{name, about, on, off, units (how many have it), here (whether
        the unit at `address` has it)}], "can": a mod is picked to keep them in}."""
        from .edits import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:  # (a mod file with a mistake: the mod check says so; nothing to list here)
            edits = None
        if edits is None:
            return {"types": [], "can": False}
        types = self._read_types(edits.folder)
        here = self._resolve_unit_key(edits, address) if address else None
        return {"types": [{"name": t.name, "about": t.about, "on": t.on, "off": t.off, "units": len(t.units),
                           "here": here is not None and here in t.units} for t in types], "can": True}

    def _resolve_unit_key(self, edits, address: str) -> str | None:
        """The address a unit's flag change is kept under (a new unit's own, else the index's), or None when it
        isn't a unit with a flag list (every one of the game's units has one)."""
        from .api import KIND_OF, _props
        real, new = self._resolve(edits, address)
        if ":" in address:
            return None
        ix = self._open()
        try:
            try:
                o = ix.show(real)
            except KeyError:
                return None
        finally:
            ix.close()
        if o["class"] not in KIND_OF or FLAGS not in _props(o):
            return None
        return address if new else o["address"]

    def flag_type_save(self, name: str, about: str, on: list, off: list, old_name: str = "") -> dict:
        """Make a flag type in the current mod, or change one (`old_name`: the one it was): `name` (one line, at most
        NAME_MOST letters, no other type's), `about` (what it's for: the tooltip), the game's flags it turns `on` and
        `off` (each a flag the flag guide has, never both). Every unit that has a changed type gets it again as it is
        now. Returns flag_types()."""
        from rusemod import flaginfo
        from .api import StudioError
        edits = self._types_folder()
        name, about = str(name or "").strip(), str(about or "").strip()
        if not name or any(c in name for c in "\r\n\t"):
            raise StudioError("Give the flag type a name (one line).")
        if len(name) > NAME_MOST:
            raise StudioError(f"A flag type's name can be at most {NAME_MOST} letters long.")
        if len(about) > ABOUT_MOST:
            raise StudioError(f"What it's for can be at most {ABOUT_MOST} letters long.")
        known = set(flaginfo.guide())
        try:
            on, off = [list(dict.fromkeys(int(n) for n in xs)) for xs in (on or [], off or [])]
        except (TypeError, ValueError):
            raise StudioError("A flag type's flags are the game's flag numbers.") from None
        bad = [n for n in on + off if n not in known]
        if bad:
            # not a game rule: only the flags the game reads do anything, and the flag guide has every one of them
            raise StudioError(f"Flag {bad[0]} isn't one of the game's flags, so it would do nothing.")
        if not on and not off:
            raise StudioError("Tick at least one flag to turn on or off.")
        both = sorted(set(on) & set(off))
        if both:
            raise StudioError(f"Flag {both[0]} can't be turned on and off by the same type.")
        with self._saving:
            types = self._read_types(edits.folder)
            old = next((t for t in types if old_name and t.name.lower() == str(old_name).strip().lower()), None)
            if old_name and old is None:
                raise StudioError(f"There's no flag type called {old_name} in this mod any more.")
            if any(t is not old and t.name.lower() == name.lower() for t in types):
                raise StudioError(f"There's already a flag type called {name}. Pick another name.")
            if old is None and len(types) >= TYPES_MOST:
                raise StudioError(f"A mod can have at most {TYPES_MOST} flag types.")
            if old is None:
                types.append(FlagType(name, about, on, off))
                self._write_types(edits.folder, types)
            else:
                # each unit that has it: its types taken off by what they changed there, then given again as they
                # are now
                old.name, old.about, old.on, old.off = name, about, on, off
                for address in list(old.units):
                    self._regive(edits, types, address, lambda ts: ts)
                self._write_types(edits.folder, types)
        return self.flag_types()

    def flag_type_delete(self, name: str) -> dict:
        """Delete a flag type from the current mod: every unit that has it gets back what it changed there. Returns
        flag_types()."""
        from .api import StudioError
        edits = self._types_folder()
        with self._saving:
            types = self._read_types(edits.folder)
            gone = next((t for t in types if t.name.lower() == str(name).strip().lower()), None)
            if gone is None:
                raise StudioError(f"There's no flag type called {name} in this mod any more.")
            for address in list(gone.units):
                self._regive(edits, types, address, lambda ts: ts - {id(gone)})
            types.remove(gone)
            self._write_types(edits.folder, types)
        return self.flag_types()

    def flag_type_give(self, address: str, name: str, give_it: bool = True, lang: str = "base") -> dict:
        """Give the unit at `address` the current mod's flag type `name` (`give_it` False: take it off). Returns
        {"saved", "flags": the unit's flags now, "check": flag_check of them, "types": flag_types(address)}."""
        from .api import StudioError
        edits = self._types_folder()
        key = self._resolve_unit_key(edits, address)
        if key is None:
            raise StudioError(f"{address} isn't a unit, so it has no flags to give a type")
        with self._saving:
            types = self._read_types(edits.folder)
            t = next((x for x in types if x.name.lower() == str(name).strip().lower()), None)
            if t is None:
                raise StudioError(f"There's no flag type called {name} in this mod any more.")
            flags = self._regive(edits, types, key, (lambda ts: ts | {id(t)}) if give_it else (lambda ts: ts - {id(t)}))
        return {"saved": str(edits.file), "flags": flags, "check": self.flag_check(address, flags, lang),
                "types": self.flag_types(address)}

    def _regive(self, edits, types: list[FlagType], key: str, change) -> list[int]:
        """Give the unit kept under `key` the types `change(the ids of the types it has)` says, and save its flags and
        flag-types.toml: its types are all taken off (the last given first), then the ones it keeps given again in the
        file's order. Call it holding _saving. Returns its flags."""
        from .edits import ModEdits
        game = self._game_flags(edits, key)
        edits = ModEdits(edits.folder)
        mine = edits.get(key, FLAGS)
        flags = [int(n) for n in mine] if isinstance(mine, list) else list(game)
        had = [t for t in types if key in t.units]
        for t in reversed(had):
            flags = take(flags, *t.units.pop(key))
        keep = change({id(t) for t in had})
        for t in types:
            if id(t) in keep:
                flags, added, removed = give(flags, t)
                t.units[key] = (added, removed)
        if sorted(flags) == sorted(game):  # (the game's own flags, maybe in another order: no change left)
            flags = list(game)
            edits.reset(key, FLAGS)
        else:
            edits.set(key, FLAGS, flags)
        self._write_types(edits.folder, types)
        return flags

    def _game_flags(self, edits, key: str) -> list[int]:
        """The flags the game gives the unit kept under `key` (a new unit: the unit it copies)."""
        real, _new = self._resolve(edits, key)
        ix = self._open()
        try:
            o = ix.show(real)
        finally:
            ix.close()
        return [int(n) for p, n, _t in o["values"] if p.startswith(FLAGS + "[") and n is not None]

    @staticmethod
    def _write_types(folder, types: list[FlagType]) -> None:
        from .edits import ModEdits
        path = Path(folder) / FILE
        if not types:
            path.unlink(missing_ok=True)
            return
        text = types_toml(types)
        try:  # only a file the Studio reads back is ever saved
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            from .api import StudioError
            raise StudioError(f"The Studio would have saved {FILE}, which it can't read back ({exc}), so nothing was "
                              f"saved. Please report this.") from None
        ModEdits._write(path, text)
