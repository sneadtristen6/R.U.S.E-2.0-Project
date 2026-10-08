"""Era units in the Units tab (StudioApi's EraUnitCalls): RUSE 2.0's base models for four eras (WWI, WWII+, Cold War,
Modern), each another maker's free model (CC0 or CC BY), credited, already fitted and given its nation's markings
(owner 2026-10-08: "add what we have to the studio ... these were all of the what CCO, CC BY ones that we could
include in our game. There's plenty more out there").

They're listed in the Units tab beside the game's own units (owner 2026-10-08: "Why is it not with the rest of the
units? ... the existing ones are in the ... vanilla section. And then there's a World War One, World War Two plus, Cold
War, Modern"): the era filter picks Vanilla (the game's units) or an era. Every era unit is OFF until a modder adds it
(owner 2026-10-08: "I don't want all of these just to automatically be units"). Adding one makes it a new unit of the
current mod: it starts from the values of a game unit the modder picks (owner 2026-10-08: "what if they don't want to
make it the same as a Sherman?": the library only suggests one), with the name, price and build menu given, gets its
model (Import model's step) and its credit in the mod's credits file; then it's a new unit like any other, every value
changed on its page. Taking it out deletes that unit again.

The library: a folder holding era_units.json, the fitted models and their pictures (RUSE_ERA_UNITS, else an era_units
folder beside the Studio's program, else beside its source). The mod keeps which era units it has in era_units.json and
the credits in CREDITS-era-units.md, both in the mod's folder."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

LIBRARY_ENV = "RUSE_ERA_UNITS"
INDEX = "era_units.json"          # in the library: the units; in a mod: {era unit key: its new unit's address}
CREDITS = "CREDITS-era-units.md"  # in a mod: the makers of the era units it has, as their licences ask
ERAS = ("WWI", "WWII", "Cold War", "Modern")
# the Units tab's nation chips: the game's seven nations by number, China (no game nation of its own) as 7
NATION_CODE = {"USA": 0, "Germany": 1, "UK": 2, "France": 3, "Italy": 4, "USSR": 5, "Russia": 5, "Japan": 6, "China": 7}
CLASS_OF = {"ground": "TUniteAuSolDescriptor", "air": "TAvionDescriptor"}


def library_dir() -> Path | None:
    """Where the era units library is: RUSE_ERA_UNITS, else era_units beside the program, else beside the source."""
    places = [os.environ.get(LIBRARY_ENV)] if os.environ.get(LIBRARY_ENV) else []
    places += [Path(sys.executable).resolve().parent / "era_units", Path(sys.argv[0]).resolve().parent / "era_units",
               Path(__file__).resolve().parents[2] / "era_units"]
    for p in places:
        if p and (Path(p) / INDEX).is_file():
            return Path(p)
    return None


def credits_text(units: list[dict]) -> str:
    """The mod's credits file for the era units it has (CC BY asks for the maker, the work, its licence and a note of
    changes)."""
    lines = ["# Era unit models", "",
             "These units use free 3D models by their makers, under the licence named. Changes: fitted to the game "
             "(turned, scaled) and the unit's nation's markings added (older markings covered).", ""]
    for u in sorted(units, key=lambda x: (x["era"], x["nation"], x["name"])):
        c = u["credit"]
        extra = f" {c['extra']}." if c.get("extra") else ""
        lines.append(f"- {u['name']} ({u['era']}, {u['nation']}): \"{c['title']}\" by {c['author']}, {c['licence']}, "
                     f"{c['url']}.{extra}")
    return "\n".join(lines) + "\n"


def kind_of(u: dict) -> str:
    return "air" if u.get("aircraft") else "ground"


class EraUnitCalls:
    """Mixed into StudioApi: uses its _open, _mod_dir, _edits, _saving, _all_units, _names, cache_dir, new_unit,
    model_import, model_import_remove and delete_unit."""

    def _era_library(self) -> tuple[Path | None, dict]:
        folder = library_dir()
        if folder is None:
            return None, {"units": [], "note": ""}
        return folder, json.loads((folder / INDEX).read_text(encoding="utf-8"))

    def _era_record(self) -> dict:
        """{era unit key: its unit's address} for the current mod, keeping only units the mod still has."""
        mod = self._mod_dir()
        if mod is None or not (mod / INDEX).is_file():
            return {}
        try:
            record = json.loads((mod / INDEX).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        edits = self._edits()
        have = set(edits.new_units) if edits is not None else set()
        return {k: a for k, a in record.items() if a in have}

    def _era_save(self, record: dict, lib: dict) -> None:
        mod = self._mod_dir()
        (mod / INDEX).write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
        mine = [u for u in lib["units"] if u["key"] in record]
        credits = mod / CREDITS
        if mine:
            credits.write_text(credits_text(mine), encoding="utf-8")
        else:
            credits.unlink(missing_ok=True)

    def era_units_list(self, era: str, kind: str = "all", nation: int = -1, search: str = "",
                       group: str = "all") -> dict:
        """One era's units for the Units list: {"library": found or not, "units": [{key, name, nation, code (the
        nation chip), card, kind, added}], "types": the card types there, sorted}, filtered as the Units list is:
        by kind (ground or air), nation chip, words in the name and card type ("type:<card>")."""
        folder, lib = self._era_library()
        record = self._era_record() if self._mod_dir() is not None else {}
        words = (search or "").casefold().split()
        rows = [u for u in lib["units"] if u["era"] == era]
        rows = [u for u in rows if kind in ("all", kind_of(u)) and nation in (-1, NATION_CODE.get(u["nation"], -1))]
        types = sorted({u["card"] for u in rows})
        if group.startswith("type:"):
            rows = [u for u in rows if u["card"] == group[5:]]
        rows = [u for u in rows if all(w in u["name"].casefold() for w in words)]
        return {"library": folder is not None, "types": types,
                "units": [{"key": u["key"], "name": u["name"], "nation": u["nation"],
                           "code": NATION_CODE.get(u["nation"], -1), "card": u["card"], "kind": kind_of(u),
                           "added": record.get(u["key"])} for u in rows]}

    def _era_price(self, source: str) -> float:
        from .api import _props
        ix = self._open()
        try:
            prices = _props(ix.show(source)).get("ProductionPrice")
        finally:
            ix.close()
        nums = [n for n in (prices or {}).get("numbers", []) if n is not None]
        return float(nums[0]) if nums else 0.0

    def era_start_price(self, source: str) -> dict:
        """A game unit's price (its first battle date's), for the era unit's price box when the start unit changes."""
        return {"price": self._era_price(source)}

    def era_unit_page(self, key: str, lang: str = "base") -> dict:
        """One era unit for its page: its library entry, "added" (its unit's address in this mod, or None), "has_model",
        "picture" (a cache URL of its model's picture, or None), "price" (the suggested start unit's), and "start":
        the game units it can start from (its kind's units with a build menu: the suggested one first, then its card
        type's, then the rest by name), each {address, name, nation, suggested, same_type}."""
        from .api import StudioError
        folder, lib = self._era_library()
        entry = next((u for u in lib["units"] if u["key"] == key), None)
        if folder is None or entry is None:
            raise StudioError(f"{key}: not in the era units library")
        record = self._era_record() if self._mod_dir() is not None else {}
        picture = None
        if entry.get("picture") and (folder / entry["picture"]).is_file():
            copy = self.cache_dir / "eras" / Path(entry["picture"]).name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(folder / entry["picture"], copy)
            picture = f"cache/eras/{copy.name}"
        ix = self._open()
        try:
            cls = CLASS_OF[kind_of(entry)]
            units = [u for u in self._all_units(ix) if u["class"] == cls and u["factory"] is not None]
            names = self._names(ix, [u["address"] for u in units], lang)
            types = ix.names([u["type_key"] for u in units if u["type_key"]], "us")
        finally:
            ix.close()
        start = []
        for u in units:
            same = types.get(u["type_key"]) == entry["card"]
            start.append({"address": u["address"], "name": names.get(u["address"], u["address"].rsplit("/", 1)[-1]),
                          "nation": u["nation"], "suggested": u["address"] == entry.get("copies"), "same_type": same})
        start.sort(key=lambda s: (not s["suggested"], not s["same_type"], s["name"].casefold()))
        price = self._era_price(entry["copies"]) if entry.get("copies") else 0.0
        return dict(entry, added=record.get(key), price=price, picture=picture, start=start,
                    has_model=bool(entry.get("model") and (folder / entry["model"]).is_file()))

    def era_unit_add(self, key: str, nation: int, factory: int, source: str | None = None, name: str | None = None,
                     price=None) -> dict:
        """Add an era unit to the current mod: a new unit starting from `source`'s values (default: the library's
        suggestion), called `name` (default: the era unit's), costing `price` (default: the source's), in nation
        `nation`'s build menu `factory`, with its model and its credit. Returns {"address", "name", "model": the
        model's report or None, "model_note": "" or why it shows the start unit's model}."""
        from .api import StudioError
        folder, lib = self._era_library()
        entry = next((u for u in lib["units"] if u["key"] == key), None)
        if folder is None or entry is None:
            raise StudioError(f"{key}: not in the era units library")
        if self._mod_dir() is None or self._edits() is None:
            raise StudioError("Pick or make a mod first: an era unit is added to a mod.")
        source = source or entry.get("copies")
        if not source:
            raise StudioError(f"{entry['name']}: pick a unit to start from")
        record = self._era_record()
        if key in record:
            raise StudioError(f"{entry['name']} is already in this mod")
        cost = self._era_price(source) if price is None or price == "" else price
        wanted = (name or "").strip() or entry["name"]
        try:
            made = self.new_unit(source, wanted, cost, int(nation), int(factory))
        except StudioError as exc:
            if name or "already a unit" not in str(exc):
                raise
            wanted = f"{entry['name']} ({entry['era']})"   # the same name in two eras (a Leopard 1 in both, say)
            made = self.new_unit(source, wanted, cost, int(nation), int(factory))
        record[key] = made["address"]
        with self._saving:
            self._era_save(record, lib)
        model, note = None, ""
        if entry.get("model") and (folder / entry["model"]).is_file():
            try:
                model = self.model_import(made["address"], str(folder / entry["model"]), 1.0,
                                          bool(entry.get("aircraft")))["model"]
            except StudioError as exc:
                note = "no_fit" if not entry.get("fits") else str(exc)
        else:
            note = "no_model"
        return {"address": made["address"], "name": made["name"], "model": model, "model_note": note}

    def era_unit_remove(self, key: str) -> dict:
        """Take an era unit out of the mod: its unit, every change made to it, its model and its credit."""
        from .api import StudioError
        _folder, lib = self._era_library()
        record = self._era_record()
        address = record.pop(key, None)
        if address is None:
            raise StudioError(f"{key}: not in this mod")
        try:
            self.model_import_remove(address)
        except StudioError:
            pass
        self.delete_unit(address)
        with self._saving:
            self._era_save(record, lib)
        return {"removed": address}
