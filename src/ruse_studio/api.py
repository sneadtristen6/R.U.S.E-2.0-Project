"""What the Studio's screens can ask for. Plain JSON-friendly data in and out; every answer about the game comes from
the game index, opened read-only for each question (the window calls from several threads).

Editing: the modder works in one mod at a time (made here, in the platform folder's `mods/`, or any mod folder they
open). Every change is saved at once in that mod's `src/studio.rndf` (edits.py). New units are copies of a unit the
game has, kept in the same file with their names in `text/studio.baseunite.csv`; the game index doesn't know them,
so their pages are the copied unit's pages, with the copy's own changes on top. Test in game builds the mod into its
own modded copy and starts the game, with the platform's engine (rusemod.play), so the Studio doesn't need the
launcher.
"""
from __future__ import annotations

import functools
import json
import re
import struct
import threading
import tomllib
import unicodedata
from dataclasses import asdict, replace
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from rusemod import identity, package, scenario, scenery, schema
from rusemod.brush import BrushError, parse_strokes, strokes_toml
from rusemod.update import UpdateCalls
from rusemod.build import BuildError, build_and_write, load_mod
from rusemod.lock import fingerprint_text
from rusemod.home import PrefsCalls, default_home, game_dir as find_game_dir
from rusemod.index import FORMAT as INDEX_FORMAT, LIST_VALUES, WHOLE_LISTS, Index, build_index, default_path
from rusemod.patch import INT_RANGES
from rusemod.play import Starter, instances_dir
from rusemod.rndf import RndfError
from rusemod.steam import build_of, data_revisions, find_game
from rusemod.build import find_pack
from rusemod.edat import Edat
from rusemod.terrain import LODS, ground_png, map_list, pack_file, terrain
from rusemod.webui import Job, job_view, pick_folder, pick_save

from .edits import EditsFileError, Link, ModEdits, NewUnit
from . import __version__

KINDS = {"ground": ("TUniteAuSolDescriptor",), "infantry": ("TInfanterieDescriptor",),
         "air": ("TAvionDescriptor",), "buildings": ("TBatimentDescriptor",)}
KIND_OF = {cls: kind for kind, classes in KINDS.items() for cls in classes}
AMMO = "TAmmunition"  # a weapon's shots (damage, range, rate of fire): listed as the "ammo" kind, and copied for a
WEAPON = "TMountedWeaponDescriptor"  # weapon of its own; a weapon on a unit fires one ammo (its Ammunition)
SHOT_TAG = "weapon_effet_tag"  # a weapon's EffectTag names the part of the unit's model it fires from (_shots)
FLAG_LISTS = set(WHOLE_LISTS)  # lists edited as a set of flags, any length (a unit's InitialFlagSet)
NOT_EDITABLE = {"DescriptorId", "TrackingId", "AmmunitionId", "Nationalite"}  # ids stay unique (rusemod.identity);
# moving a unit to another nation needs more than one number (its menus, and the new nation's add-on for China), so it
# comes later
ALL_CLASSES = tuple(KIND_OF)
# What a unit or building is for (the unit list's and the Spawn tool's second sort, after the kind). Buildings by their
# code name, first match wins (a decoy HQ is a decoy): Leurre is French for decoy. Units by the factory that builds them
# (its menu number); 3 is the construction menu, where the forts' guns sit.
BUILDING_GROUPS = (("fake", ("Leurre", "Fake")), ("hq", ("Headquarter",)),
                   ("money", ("BatimentAdministratif", "Depot")),
                   ("fort", ("Defense", "Def_", "ArtillerieField", "PosteAlerte")))
FACTORY_GROUPS = {8: "barracks", 10: "armor", 11: "antitank", 13: "artillery", 12: "prototype", 9: "airfield",
                  3: "turret"}
GROUPS = ("hq", "money", "factory", "fort", "fake", *FACTORY_GROUPS.values(), "other")  # the order lists show them in
# Ammunition by what it is: its kind's English name in the game's texts (TypeName), the same in every language.
AMMO_GROUPS = {"ap": ("AP shell",), "he": ("HE shell", "Assault gun", "Mortar", "Navy gun", "Nuclear gun"),
               "aa": ("AA gun",), "mg": ("Machine-gun", "Machine-guns", "MG turrets", "Fixed MG"),
               "infantry_weapons": ("Infantry weapon", "Handguns", "Grenades", "Flamethrower", "Satchel charge"),
               "antitank_weapons": ("Bazooka", "PIAT", "Panzerfaust", "Panzerschreck", "Panzerknacker"),
               "bombs": ("Carpet bombing", "Diving bomb", "HE bomb"), "rockets": ("Rocket", "Rockets", "V2")}
AMMO_GROUP_OF = {text: g for g, texts in AMMO_GROUPS.items() for text in texts}
AMMO_GROUP_ORDER = (*AMMO_GROUPS, "other")


def group_of(kind: str, address: str, factory: int | None) -> str:
    """What a unit or building is for: one of GROUPS (a mod's new unit goes by the one it was copied from)."""
    if kind == "buildings":
        name = _tail(address)
        return next((g for g, parts in BUILDING_GROUPS if any(p in name for p in parts)), "factory")
    return FACTORY_GROUPS.get(factory, "other")
NATIONS = 7
_PREFIX = re.compile(r"^(Descriptor_[A-Za-z]+_)")  # Descriptor_Unit_M4_Sherman -> a copy is Descriptor_Unit_<Name>
PACKAGE_FILES = ("RUSE mods (*.rusemod)",)  # the "save as" dialog's filter for Export mod…


def _tail(address: str) -> str:
    return address.rsplit("/", 1)[-1]


def _shot_name(effect: str | None) -> str:
    """$/GFX/Everything/FX_Tir_ObusAP_Moyen -> ObusAP Moyen."""
    name = _tail(effect or "")
    return name[len("FX_Tir_"):].replace("_", " ") if name.startswith("FX_Tir_") else name.replace("_", " ")


def _short(num: float):
    """A number from the index as the modder should see it: 12, not 12.0; 0.1, not the float32's 0.100000001."""
    if isinstance(num, int) or num.is_integer():
        return int(num)
    try:
        if struct.unpack("<f", struct.pack("<f", num))[0] == num:
            for digits in range(6, 10):
                text = float(f"{num:.{digits}g}")
                if struct.unpack("<f", struct.pack("<f", text))[0] == num:
                    return text
    except OverflowError:
        pass
    return num


def _props(o: dict) -> dict[str, dict]:
    """One object's values from the index, per property: list or not, and its numbers (None for texts)."""
    props: dict[str, dict] = {}
    for path, num, text in o["values"]:
        prop = path.split("[", 1)[0]
        p = props.setdefault(prop, {"list": "[" in path, "numbers": [], "texts": [], "in_order": True})
        if p["list"] and path != f"{prop}[{len(p['numbers'])}]":
            p["in_order"] = False  # a list that also holds something else (a reference): not editable as numbers
        p["numbers"].append(None if num is None else _short(num))
        p["texts"].append(text)
    return props


def _can_edit(prop: str, p: dict) -> bool:
    return prop not in NOT_EDITABLE and p["in_order"] and all(n is not None for n in p["numbers"]) \
        and not (p["list"] and len(p["numbers"]) >= WHOLE_LISTS.get(prop, LIST_VALUES))  # the index keeps 16 items of
    # most lists: there may be more


def ammo_name(texts: dict, name_key, type_key) -> str | None:
    """What the game calls an ammunition: its kind, then its calibre ("AP shell · Medium cal."), from its two texts."""
    kind, calibre = texts.get(type_key), texts.get(name_key)
    return " · ".join(dict.fromkeys(t for t in (kind, calibre) if t)) or None


def _whole(value, kind: str, prop: str):
    """Round like the build does for whole-number properties (half away from zero), and check it fits."""
    r = int(Decimal(str(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    lo, hi = (0, 1) if kind == "bool" else INT_RANGES[kind]
    if not lo <= r <= hi:
        raise StudioError(f"{prop}: {r} doesn't fit (it must be {lo} to {hi})")
    return r


def safe_name(name: str) -> str:
    """The part of a new unit's address made from its name: ASCII letters, digits and _ only (accents dropped, other
    letters left out), which the game's data, its Python unit list and .rndf files all accept."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", plain).strip("_")


class StudioError(Exception):
    pass


@functools.cache
def _words() -> dict:
    return tomllib.loads(Path(__file__).with_name("words.toml").read_text(encoding="utf-8"))


def words(lang: str = schema.BASE) -> dict:
    """The Studio's own words in `lang` (English for `base` and anything missing)."""
    return {key: texts.get(lang) or texts["us"] for key, texts in _words().items()}


class StudioApi(UpdateCalls, PrefsCalls):
    UPDATE_APP, UPDATE_VERSION = "studio", __version__  # rusemod.update: the app looks for its newer releases
    PREFS_APP = "studio"  # rusemod.home: the language and keys, kept in settings.json

    def __init__(self, index_path=None, game_dir=None, find=find_game, home=None, starter=None, instances=None,
                 pick_save=None):
        self._index_path = Path(index_path) if index_path else None
        self._game_dir = Path(game_dir) if game_dir else None
        self._find = find
        self._home = Path(home) if home else default_home()
        self._starter = starter or Starter()
        self._instances = Path(instances) if instances else None
        self._jobs: dict[str, Job] = {}
        self._units: list | None = None  # every unit and building, read once per index
        self._ammo: list | None = None   # every ammunition, the same
        self._window = None  # set by the window (a folder dialog for "Open a mod folder", "save as" for Export)
        self._pick_save = pick_save  # tests: a stand-in for the "save as" dialog (filename -> path or None)
        self._saving = threading.RLock()  # the window calls from several threads: one change to the file at a time,
        # and no reading it mid-change (Windows can't replace a file that's open)
        self._grounds: dict[tuple, dict] = {}  # the last maps shown in 3D, so switching back is instant
        self._grounds_lock = threading.Lock()
        self._ground_jobs: dict[str, str] = {}  # picture being made -> its job, so asking twice doesn't make it twice
        self._sceneries: dict[tuple, dict] = {}  # the last maps' scenery (map_scenery)
        self._descriptors: tuple = (None, {})    # (unit pack, its scenery types), read once per game build
        self._models_done: dict[str, dict] = {}  # map -> the index of its 3D models (map_models), once made

    # --- where things are ---
    def _game(self) -> Path | None:
        if self._game_dir:
            return self._game_dir
        return find_game_dir(self._home, self._find)[0]  # the same answer as the launcher's

    def _path(self) -> Path | None:
        if self._index_path:
            return self._index_path
        game = self._game()
        return default_path(game) if game else None

    def _open(self) -> Index:
        path = self._path()
        if path is None:
            raise FileNotFoundError("We couldn't find R.U.S.E., so there's no game index to open.")
        return Index(path)

    # --- the screen's words ---
    def languages(self) -> list[dict]:
        return schema.languages()

    def strings(self, lang: str = schema.BASE) -> dict:
        return words(lang)

    def nations(self, lang: str = schema.BASE) -> list[str]:
        return [schema.nation(n, lang) for n in range(NATIONS)]

    def status(self) -> dict:
        path = self._path()
        if path is None or not path.is_file():
            return {"ready": False, "can_build": self._game() is not None}
        ix = Index(path)
        try:
            meta = ix.meta()
        finally:
            ix.close()
        if meta.get("format") != INDEX_FORMAT:  # made by an older Studio: build it again (the same button)
            return {"ready": False, "can_build": self._game() is not None, "old": True}
        return {"ready": True, "build": meta.get("build"), "built": meta.get("built"), "path": str(path)}

    # --- units ---
    def _all_units(self, ix: Index) -> list[dict]:
        if self._units is None:
            self._units = ix.units(ALL_CLASSES)
        return self._units

    def _new_units(self) -> dict[str, NewUnit]:
        """The current mod's new units (none when there's no mod, or its files can't be read: browsing goes on)."""
        try:
            edits = self._edits()
        except EditsFileError:
            return {}
        return edits.new_units if edits else {}

    def units(self, lang: str = schema.BASE, kind: str = "all", nation: int = -1, search: str = "",
              group: str = "all") -> dict:
        """The units and buildings to list, with names in `lang` (the code names by default), each with its `group`
        (what it's for, group_of); `group` lists only those. `groups`: the groups there are of `kind` and `nation`. The current mod's new units come first, under the nation
        and factory they were given, marked `new`. `kind` "ammo" lists the ammunition instead (see `ammo`)."""
        if kind == "ammo":
            return self.ammo(lang, search, group)
        ix = self._open()
        try:
            rows = self._all_units(ix)
            names = ix.names([u["key"] for u in rows], lang) if lang != schema.BASE else {}
        finally:
            ix.close()
        by_address = {u["address"]: u for u in rows}
        new = []
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        for unit in edits.new_units.values() if edits else []:
            if unit.source not in by_address:  # a copied ammunition, listed under "ammo"
                continue
            src = by_address.get(unit.source, {"class": "TUniteAuSolDescriptor", "nation": 0, "factory": None})
            own = edits.of(unit.target)
            new.append({"address": unit.target, "class": src["class"], "key": None,
                        "nation": int(own.get("Nationalite", src["nation"])),
                        "factory": own.get("Factory", src["factory"]), "slot": None, "new": True,
                        "source": unit.source, "name": unit.name})
        words = search.strip().lower()
        out, present = [], set()
        for u in new + rows:
            k = KIND_OF.get(u["class"], "ground")
            if kind != "all" and k != kind or nation >= 0 and u["nation"] != nation:
                continue
            g = group_of(k, u.get("source") or u["address"], u["factory"])
            present.add(g)
            if group != "all" and g != group:
                continue
            name = u.get("name") or names.get(u["key"]) or _tail(u["address"])
            if words and words not in name.lower() and words not in u["address"].lower():
                continue
            out.append({"address": u["address"], "name": name, "base_name": _tail(u["address"]), "kind": k,
                        "nation": u["nation"], "nation_name": schema.nation(u["nation"], lang),
                        "factory": u["factory"], "slot": u["slot"], "new": u.get("new", False),
                        "source": u.get("source"), "group": g})
        return {"units": out, "total": len(rows) + len(new), "groups": [g for g in GROUPS if g in present]}

    # --- ammunition: what a weapon fires (damage, range, rate of fire); several units' weapons share one ---
    def _all_ammo(self, ix: Index) -> list[dict]:
        if self._ammo is None:
            self._ammo = ix.ammunition()
        return self._ammo

    def _ammo_names(self, ix: Index, rows, lang: str) -> dict:
        """Address -> what to call an ammunition: its kind and calibre in `lang` ("AP shell · Medium cal."), else
        its code name."""
        keys = [k for a in rows for k in (a["name_key"], a["type_key"]) if k]
        texts = ix.names(keys, lang) if lang != schema.BASE else {}
        return {a["address"]: ammo_name(texts, a["name_key"], a["type_key"]) or _tail(a["address"]) for a in rows}

    def ammo(self, lang: str = schema.BASE, search: str = "", group: str = "all") -> dict:
        """The ammunition to list, like `units`: the current mod's copies first (marked `new`), then the game's by
        `group` (AMMO_GROUPS: what it is) and kind, each with the units whose weapons fire it (`users`, names in
        `lang`). `group` lists only those; `groups`: the groups there are."""
        ix = self._open()
        try:
            rows = self._all_ammo(ix)
            names = self._ammo_names(ix, rows, lang)
            english = ix.names([a["type_key"] for a in rows if a["type_key"]], "us")
            users = {u for a in rows for u in a["users"]}
            user_names = self._names(ix, sorted(users), lang)
            nation_of = {u["address"]: u["nation"] for u in self._all_units(ix)}
        finally:
            ix.close()
        by_address = {a["address"]: a for a in rows}
        new = []
        for unit in self._new_units().values():
            src = by_address.get(unit.source)
            if src is None:
                continue
            new.append({"address": unit.target, "id": None, "users": [], "new": True, "source": unit.source,
                        "name": unit.name, "source_name": names[unit.source]})
        group_of = {a["address"]: AMMO_GROUP_OF.get(english.get(a["type_key"], ""), "other") for a in rows}
        order = {g: n for n, g in enumerate(AMMO_GROUP_ORDER)}
        # by group, then the game's kind (MG turrets apart from machine-guns), then the game's own order
        rows = sorted(rows, key=lambda a: (order[group_of[a["address"]]], english.get(a["type_key"], "")))
        words = search.strip().lower()
        out, present = [], set()
        for a in new + rows:
            g = group_of[a.get("source") or a["address"]]
            present.add(g)
            if group != "all" and g != group:
                continue
            name = a.get("name") or names[a["address"]]
            used = [user_names[u] for u in a["users"]]
            if words and words not in name.lower() and words not in a["address"].lower() \
                    and not any(words in u.lower() for u in used):
                continue
            nations = self._nations_of(a["users"] or by_address.get(a.get("source"), {}).get("users", []), nation_of, lang)
            out.append({"address": a["address"], "name": name, "base_name": _tail(a["address"]), "kind": "ammo",
                        "id": a["id"], "users": used, "nations": nations, "nation": -1, "nation_name": "",
                        "factory": None, "slot": None, "new": a.get("new", False), "source": a.get("source"),
                        "source_name": a.get("source_name"), "group": g})
        return {"units": out, "total": len(rows) + len(new), "groups": [g for g in AMMO_GROUP_ORDER if g in present]}

    @staticmethod
    def _nations_of(users, nation_of: dict, lang: str) -> list[str]:
        """The countries whose units fire an ammunition (a copy: its source's), in the game's nation order."""
        found = sorted({nation_of[u] for u in users if u in nation_of})
        return [schema.nation(n, lang) for n in found]

    def flags(self, lang: str = schema.BASE) -> dict:
        """Every flag number the game's units carry in their flag lists (InitialFlagSet), with what is known about
        it (rusemod/labels.toml [flags]), how many units have it and a few of them by name."""
        ix = self._open()
        try:
            rows = ix.flag_sets()
            names = self._names(ix, sorted({e for r in rows for e in r["examples"]}), lang)
        finally:
            ix.close()
        return {"flags": [{"flag": r["flag"], "count": r["count"], "examples": [names[e] for e in r["examples"]],
                           "meaning": schema.flag(r["flag"], lang)} for r in rows]}

    def weapons(self, address: str, lang: str = schema.BASE) -> dict:
        """A unit's mounted weapons and what each fires: [{address, name, ammo: {address, name}, edited}], plus
        every ammunition it could fire instead (`choices`, the game's and the mod's copies)."""
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, new = self._resolve(edits, address)
        base = address.partition(":")[0]
        ix = self._open()
        try:
            plan = ix.clone_plan(real)
            # in their place on the unit (turret 1's weapons first), so "Weapon 1" is the main gun
            parts = sorted((a for a in plan["copied"] + plan["shared"] if ix.show(a)["class"] == WEAPON),
                           key=lambda a: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", a)])
            weapons = []
            unit_shots = self._shots(ix, real.partition(":")[0])
            for part in parts:
                o = ix.show(part)
                tag = next((t for p, _n, t in o["values"] if p == "EffectTag"), None)
                fires = next((what for p, k, what in ix.uses(part) if p == "Ammunition" and k == "object"), None)
                weapons.append({"real": part, "address": (base + part[len(new.source):]) if new else part,
                                "name": tag or f"{_tail(part)}", "fires": fires,
                                "shot": self._shot_now(ix, edits, unit_shots.get(tag, []), real, base)})
            rows = self._all_ammo(ix)
            names = self._ammo_names(ix, rows, lang)
            nation_of = {u["address"]: u["nation"] for u in self._all_units(ix)}
        finally:
            ix.close()
        users = {a["address"]: a["users"] for a in rows}
        copies = {t: u for t, u in (edits.new_units.items() if edits else []) if u.source in names}
        for t, u in copies.items():
            names[t] = u.name
            users[t] = users.get(u.source, [])
        choices = [{"address": a, "name": n, "new": a in copies,
                    "nations": self._nations_of(users.get(a, []), nation_of, lang)}
                   for a, n in sorted(names.items(), key=lambda kv: kv[1].lower())]
        out = []
        for w in weapons:
            chosen = edits.get(w["address"], "Ammunition") if edits else None
            current = str(chosen) if chosen else w["fires"]
            out.append({"address": w["address"], "name": w["name"],
                        "ammo": {"address": current, "name": names.get(current) or (_tail(current) if current else "")},
                        "game_ammo": w["fires"], "edited": bool(chosen), "shot": w["shot"]})
        return {"weapons": out, "choices": choices}

    def set_ammo(self, unit: str, weapon: str, ammo: str) -> dict:
        """Make a unit's weapon fire another ammunition (one of `weapons(unit)["choices"]`), saved in the current mod
        as a link at the weapon's address; choosing the game's own ammo again removes the change."""
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        if weapon.partition(":")[0] != unit.partition(":")[0]:
            raise StudioError(f"{weapon} isn't a weapon of {unit}")
        real_weapon, _new = self._resolve(edits, weapon)
        real_ammo, ammo_copy = self._resolve(edits, ammo)
        ix = self._open()
        try:
            try:
                o = ix.show(real_weapon)
            except KeyError:
                raise StudioError(f"There's no weapon at {weapon} in this game build.") from None
            if o["class"] != WEAPON:
                raise StudioError(f"{weapon} isn't a weapon (it's a {o['class']})")
            if o["shared"] and not o["export"]:
                raise StudioError(f"{weapon} is shared by several units; change it on each unit's own copy")
            try:
                if ix.show(real_ammo)["class"] != AMMO:
                    raise StudioError(f"{ammo} isn't an ammunition")
            except KeyError:
                raise StudioError(f"There's no ammunition at {ammo}.") from None
            game_ammo = next((what for p, k, what in ix.uses(real_weapon) if p == "Ammunition" and k == "object"), None)
            tag = next((t for p, _n, t in o["values"] if p == "EffectTag"), None)
            real_unit = real_weapon.partition(":")[0]
            mine = self._shots(ix, real_unit).get(tag, []) if tag else []
            theirs = self._shot_of(ix, real_ammo) if mine and ammo != game_ammo else []
        finally:
            ix.close()
        base = weapon.partition(":")[0]
        with self._saving:
            edits = ModEdits(edits.folder)
            if ammo == game_ammo:
                edits.reset(weapon, "Ammunition")
            else:
                edits.set(weapon, "Ammunition", Link(ammo))
            # the muzzle flash and sound follow the ammo: the Sherman's gun on a rifleman fires like a Sherman
            for s in mine:
                where, prop = base + s["part"][len(real_unit):], f"BinderEffets[{s['entry']}].v"
                other = next((x for x in theirs if x["key"] == s["key"]), theirs[0] if theirs else None)
                if other is None or other["call"] == s["call"]:
                    edits.reset(where, prop, s["share"])
                else:
                    edits.set(where, prop, Link(other["call"]), s["share"])
        return {"saved": str(edits.file), "ammo": ammo, "edited": ammo != game_ammo,
                "shot": _shot_name(theirs[0]["effect"]) if theirs else ""}

    def new_ammo(self, source: str, name: str) -> dict:
        """A copy of an ammunition in the current mod, for a weapon of its own (Groove's recipe: copy the ammo,
        change the copy, point one weapon at it). In game it keeps its source's name; `name` is what the Studio
        calls it. The copy gets a fresh AmmunitionId when built (rusemod.identity)."""
        name = (name or "").strip()
        if not name:
            raise StudioError("Give the copy a name.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: a copy is saved in a mod.")
        if source in edits.new_units:
            raise StudioError(f"{name}: copy the ammunition {_tail(source)} was made from instead")
        ix = self._open()
        try:
            try:
                o = ix.show(source)
            except KeyError:
                raise StudioError(f"{source} isn't in this game build") from None
            if not o["export"] or o["class"] != AMMO:
                raise StudioError(f"{source} isn't an ammunition, so it can't be copied here")
            namespace = source.rsplit("/", 1)[0]
            stem = safe_name(name)
            target = f"{namespace}/Ammo_{stem}" if stem else None
            n = 1
            while target is None or target in edits.new_units or self._exists(ix, target):
                target, n = f"{namespace}/Ammo_New_{n}", n + 1
        finally:
            ix.close()
        with self._saving:
            edits = ModEdits(edits.folder)
            if target in edits.new_units:
                raise StudioError(f"There's already a copy at {target}. Pick another name.")
            edits.add_unit(target, source, name, {}, named=False)
        return {"address": target, "name": name, "saved": str(edits.file)}

    @staticmethod
    def _exists(ix: Index, address: str) -> bool:
        try:
            ix.show(address)
            return True
        except KeyError:
            return False

    def menus(self, lang: str = schema.BASE) -> dict:
        """The build menus a new unit can go in: for every nation, its factories, each shown by the units it holds
        (the game has no names for factories), in menu order."""
        ix = self._open()
        try:
            rows = self._all_units(ix)
            names = self._names(ix, [u["address"] for u in rows if u["factory"] is not None], lang)
        finally:
            ix.close()
        by_menu: dict[tuple, list] = {}
        for u in rows:
            if u["factory"] is not None:
                by_menu.setdefault((u["nation"], u["factory"]), []).append(u)
        nations = []
        for n in range(NATIONS):
            factories = []
            for (nation, factory), units in sorted(by_menu.items()):
                if nation != n:
                    continue
                units = sorted(units, key=lambda u: (u["slot"] is None, u["slot"] or 0, u["address"]))
                factories.append({"factory": factory, "units": [names[u["address"]] for u in units[:3]],
                                  "count": len(units)})
            nations.append({"nation": n, "name": schema.nation(n, lang), "factories": factories})
        return {"nations": nations}

    def _names(self, ix: Index, addresses, lang: str, new_units: dict | None = None) -> dict:
        """Address -> what to call it on screen: a unit's in-game name in `lang`, a new unit's own name, else the
        end of its address."""
        keys = {u["address"]: u["key"] for u in self._all_units(ix)}
        texts = ix.names([keys.get(a) for a in addresses], lang) if lang != schema.BASE else {}
        new_units = new_units or {}
        return {a: new_units[a].name if a in new_units else texts.get(keys.get(a)) or _tail(a) for a in addresses}

    @staticmethod
    def _resolve(edits: ModEdits | None, address: str) -> tuple[str, NewUnit | None]:
        """Where the index knows an address: a new unit (or one of its own parts) is looked up in the unit it copies.
        Returns (the address in the index, the new unit or None)."""
        unit = edits.new_unit_of(address) if edits else None
        if unit is None:
            return address, None
        _base, _, inside = address.partition(":")
        return unit.source + (f":{inside}" if inside else ""), unit

    @staticmethod
    def _shots(ix: Index, unit: str) -> dict[str, list[dict]]:
        """A unit's shots, the muzzle flash and sound its model plays when a weapon fires, by the weapon's EffectTag:
        {tag: [{part, entry, key, call, effect, share}]}. The model (GfxDescriptor) has a part per tag
        (SousElements[i].k = weapon_effet_tag1); in it, a map binds an event (tir; tir_move: firing on the move) to a
        call of an effect, $/GFX/Everything/FX_Tir_*, which also plays the sound."""
        gfx = next((w for p, k, w in ix.uses(unit) if p == "GfxDescriptor" and k == "object"), None)
        if gfx is None or not gfx.startswith(unit + ":"):  # a model the unit doesn't own: not changed from here
            return {}
        kids = {p: w for p, k, w in ix.uses(gfx) if k == "object"}
        out = {}
        for path, _n, tag in ix.show(gfx)["values"]:
            m = re.fullmatch(r"SousElements\[(\d+)\]\.k", path)
            if not (m and tag and tag.startswith(SHOT_TAG)):
                continue
            todo, found = [kids.get(f"SousElements[{m.group(1)}].v")], []
            while todo:
                part = todo.pop(0)
                if part is None:
                    continue
                o = ix.show(part)
                keys = {p: text for p, _n2, text in o["values"] if p.endswith(".k")}
                for p, k, w in ix.uses(part):
                    b = re.fullmatch(r"BinderEffets\[(\d+)\]\.v", p)
                    if b and k == "object":
                        found.append({"part": part, "entry": int(b.group(1)), "key": keys.get(f"BinderEffets[{b.group(1)}].k"),
                                      "call": w, "effect": next((e for q, _k, e in ix.uses(w) if q == "Action"), None),
                                      "share": "own" if o["shared"] else None})
                    elif k == "object" and re.fullmatch(r"SousElements\[\d+\]\.v", p):
                        todo.append(w)
            out[tag] = found
        return out

    def _shot_of(self, ix: Index, ammo: str) -> list[dict]:
        """The shot of a weapon that fires `ammo` in the game (the first one that has one): what a unit's weapon
        plays when it's made to fire that ammo."""
        for user, path in ix.used_by(ammo):
            if path != "Ammunition" or ix.show(user)["class"] != WEAPON:
                continue
            tag = next((t for p, _n, t in ix.show(user)["values"] if p == "EffectTag"), None)
            found = self._shots(ix, user.partition(":")[0]).get(tag) if tag else None
            if found:
                return found
        return []

    @staticmethod
    def _shot_now(ix: Index, edits: ModEdits | None, shots: list[dict], real: str, base: str) -> str:
        """The name of the shot a weapon plays now (its main event, tir), with the mod's change if it has one."""
        s = next((x for x in shots if x["key"] == "tir"), shots[0] if shots else None)
        if s is None:
            return ""
        unit = real.partition(":")[0]
        link = edits.get(base + s["part"][len(unit):], f"BinderEffets[{s['entry']}].v", s["share"]) if edits else None
        effect = s["effect"]
        if link:
            try:
                effect = next((e for q, _k, e in ix.uses(str(link)) if q == "Action"), effect)
            except KeyError:
                pass
        return _shot_name(effect)

    def unit(self, address: str, lang: str = schema.BASE, via: str = "") -> dict:
        """One unit (or any object): its values in groups, its parts and what uses it, with the current mod's edits.
        `via` is the named unit the modder came from: a part several units share can then be changed for that unit
        only (it gets its own copy) as well as for all of them. A new unit's page is its source's, at the new
        address, with the copy's own values as edits."""
        try:
            mod = self._edits()
            broken = ""
        except EditsFileError as exc:  # browsing still works; editing waits until the file is fixed
            mod, broken = None, str(exc)
        new_units = mod.new_units if mod else {}
        real, new = self._resolve(mod, address)
        via_real, _via_new = self._resolve(mod, via) if via else ("", None)
        ix = self._open()
        try:
            try:
                o = ix.show(real)
            except KeyError:
                raise StudioError(f"There's nothing at {address} in this game build.") from None
            share = None
            if o["shared"] and not o["export"]:
                owners = o["owners"] + [t for t, u in new_units.items() if u.source in o["owners"]]  # copies use it too
                names = self._names(ix, owners + ([via] if via else []), lang, new_units)
                path = ix.path_to(via_real, o["address"]) if via_real in o["owners"] else None
                share = {"owners": [{"address": a, "name": names[a]} for a in owners],
                         "via": {"address": via, "name": names[via], "path": path} if path else None}
            types = ix.prop_types(o["class"])
            plan = ix.clone_plan(real)
            base = address.partition(":")[0]
            rewrite = (lambda a: base + a[len(new.source):]) if new else (lambda a: a)  # its own parts, at its address
            parts = [{"address": rewrite(a), "class": ix.show(a)["class"], "shared": False} for a in plan["copied"]] + \
                    [{"address": a, "class": ix.show(a)["class"], "shared": True} for a in plan["shared"]]
            uses = []
            for a in plan["references"]:  # named objects it uses (weapons, ammo…): editable on their own page
                try:
                    uses.append({"address": ix.show(a)["address"], "class": ix.show(a)["class"]})
                except KeyError:  # an import the index couldn't find
                    pass
            all_users = [] if new else ix.used_by(real)  # nothing in the game points at a new unit
            used_by = [{"address": a, "path": p} for a, p in all_users[:30]]
            key = next((t for p, _n, t in o["values"] if p == "NameInMenuToken"), None)
            shown = ix.names([key], lang).get(key) if key and lang != schema.BASE else None
            source_name = self._names(ix, [new.source], lang)[new.source] if new else None
        finally:
            ix.close()
        editable, why = self._editable(o)
        if broken:
            editable, why = False, broken
        top = new is not None and ":" not in address  # the new unit itself, not a part of it
        if top:
            shown = new.name
        keyed = address if new else o["address"]  # a copy's edits by its own address, anything else by the index's
        edits = mod.of(keyed, "shared" if share else None) if mod else {}
        own = mod.of(f"{via}:{share['via']['path']}", "own") if mod and share and share["via"] else {}
        users = len({a.split(":")[0] for a, _p in all_users})
        rows: dict[str, dict] = {}
        for prop, p in _props(o).items():
            values = []
            for num, text in zip(p["numbers"], p["texts"]):
                if prop == "Nationalite" and num is not None:
                    n = edits.get(prop, num) if top else num
                    values.append(f"{n} ({schema.nation(n, lang)})")
                elif prop == "NameInMenuToken" and top:
                    values.append(shown)
                elif prop == identity.DEBUG_NAME and top and text:  # the build gives the copy its own (MOD_FORMAT §10.5)
                    values.append(identity.debug_name(new.source, text, address))
                elif prop == "NameInMenuToken" and shown:
                    values.append(f"{text} ({shown})")
                else:
                    values.append(text if num is None else str(num))
            rows[prop] = {"prop": prop, "label": schema.label(prop, lang), "group": schema.group(prop),
                          "values": values, "numbers": p["numbers"], "list": p["list"],
                          "type": types.get(prop + "[]" if p["list"] else prop, ""),
                          "editable": editable and _can_edit(prop, p),
                          "locked": prop in NOT_EDITABLE, "edited": edits.get(prop), "edited_own": own.get(prop)}
        if "Nationalite" not in rows and o["class"] in KIND_OF:  # 0 isn't written
            n = edits.get("Nationalite", 0) if top else 0
            rows["Nationalite"] = {"prop": "Nationalite", "label": schema.label("Nationalite", lang),
                                   "group": "identity", "values": [f"{n} ({schema.nation(n, lang)})"], "numbers": [0],
                                   "list": False, "type": "int32", "editable": False, "locked": True, "edited": None,
                                   "edited_own": None}
        groups = []
        for g in schema.GROUP_ORDER:
            members = [r for r in rows.values() if r["group"] == g]
            if members:
                groups.append({"key": g, "name": schema.group_name(g, lang), "rows": members})
        return {"address": address, "class": o["class"], "name": shown or _tail(address),
                "stable": o["stable"], "shared": o["shared"], "owners": o["owners"], "groups": groups,
                "parts": parts, "uses": uses, "used_by": used_by, "editable": editable, "why_not": why,
                "named": bool(o["export"]), "share": share,
                "users": users if o["export"] and o["class"] not in KIND_OF and users > 1 else 0,
                "can_copy": bool(o["export"]) and o["class"] in KIND_OF and editable and new is None,
                "can_copy_ammo": bool(o["export"]) and o["class"] == AMMO and editable and new is None,
                "has_weapons": o["class"] in KIND_OF,  # the page then asks for weapons(address)
                "new": {"source": new.source, "source_name": source_name} if top else None}

    def _editable(self, o: dict) -> tuple[bool, str]:
        """Whether this object's values can be edited from the Studio, and if not, why (a key of the tool's words)."""
        if not o["stable"]:
            return False, "not_stable"
        return True, ""

    def _where(self, ix: Index, o: dict, mode: str, via: str, address: str, edits: ModEdits) -> tuple[str, str | None]:
        """Where a change to object `o` (shown at `address`) is written, and how (MOD_FORMAT §10.5). A part several
        units share is changed for all of them ("shared", at its own address) or for one of them only ("own":
        through that unit, which gets its own copy of the part); anything else just at its address."""
        if not (o["shared"] and not o["export"]):
            return address, None
        if mode == "shared":
            return o["address"], "shared"
        if mode != "own":
            raise StudioError(f"{o['address']} is shared by several units: change it for one of them, or for all")
        via_real, _new = self._resolve(edits, via) if via else ("", None)
        path = ix.path_to(via_real, o["address"]) if via_real in o["owners"] else None
        if path is None:
            raise StudioError(f"{via or 'no unit'} doesn't use {o['address']}, so it can't get its own copy")
        return f"{via}:{path}", "own"

    # --- maps (read from the game itself, not the index: the ground isn't in the index) ---
    def maps(self) -> dict:
        """The Maps view's list: the game's maps that ship a terrain pack, one per pack, in the game's order, with
        the names the game lists them by (rusemod.terrain)."""
        game = self._game()
        if game is None:
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        return {"maps": [m for m in map_list(game) if m["found"]]}

    def map_view(self, pack: str, lod: str = "lowdef") -> dict:
        """One map's ground for the 3D view: its mesh as packed buffers the window unpacks, and its overview picture.
        `lod`: "lowdef" (light, opens fast) or "highdef" (the close-up mesh the game draws near the camera)."""
        if lod not in LODS:
            raise StudioError(f"No detail level called {lod!r}")
        game = self._game()
        if game is None:
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        key = (str(game), pack, lod)
        with self._grounds_lock:
            if key in self._grounds:
                self._grounds[key] = self._grounds.pop(key)  # most recent last
                return self._grounds[key]
        view = terrain(game, pack, lod)
        with self._grounds_lock:
            self._grounds[key] = view
            while len(self._grounds) > 4:
                self._grounds.pop(next(iter(self._grounds)))
        return view

    def map_scenery(self, pack: str) -> dict:
        """What stands on a map, for the 3D view (rusemod.scenery.view): every building, and a sample of props and
        trees, each with its type (name, group, the game editor's category, its model). About a second per map."""
        game = self._game()
        if game is None:
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        map_path, unit_path = find_pack(game, pack_file(pack)), find_pack(game, "ZZ_GladPatchableWin.dat")
        if map_path is None or unit_path is None:
            raise StudioError(f"{pack_file(pack) if map_path is None else 'ZZ_GladPatchableWin.dat'} isn't in the game "
                              f"folder.")
        key = (str(map_path), map_path.stat().st_mtime)
        with self._grounds_lock:
            if key in self._sceneries:
                return self._sceneries[key]
        with Edat.open(str(unit_path)) as unit_arc, Edat.open(str(map_path)) as map_arc:
            dkey = (str(unit_path), unit_path.stat().st_mtime)
            if self._descriptors[0] != dkey:
                self._descriptors = (dkey, scenery.descriptors(unit_arc))
            try:
                out = scenery.view(map_arc, unit_arc, self._descriptors[1])
            except (KeyError, scenery.SceneryError) as exc:
                raise StudioError(f"{map_path.name}: its scenery can't be read ({exc}).") from None
        with self._grounds_lock:
            self._sceneries[key] = out
            while len(self._sceneries) > 3:
                self._sceneries.pop(next(iter(self._sceneries)))
        return out

    def map_scenarios(self, pack: str, edited: bool = True) -> dict:
        """A map's scenarios (rusemod.scenario), for the map view: {"scenarios": [{"file", "kind", "entries",
        "zones", "items"}]}, by kind (skirmish, operation, campaign, demo, test, unused: what the game's map list and
        menus do with it), then by name. `entries`: the map list's entries that load it, each with its name and what
        the menus call it in each language ({lang: text}). Zones are drawn as their triangles; items are starting
        points, spawns, circle and rectangle zones, labels and waypoints, each with its number (`item`). `edited`:
        as the current mod leaves them (items it moves are at their new place and marked `moved`; the units and
        buildings it spawns come last, marked `mine` with their number among the mod's spawns)."""
        from rusemod.terrain import menu_texts
        game = self._game()
        if game is None:
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        path = find_pack(game, scenario.PACK)
        glad_path = find_pack(game, "ZZ_GladPatchableWin.dat")
        if path is None or glad_path is None:
            raise StudioError(f"{scenario.PACK if path is None else 'ZZ_GladPatchableWin.dat'} isn't in the game folder.")
        key = ("scenarios", str(path), path.stat().st_mtime, pack.lower())
        with self._grounds_lock:
            cached = self._sceneries.get(key)
        if cached is not None:
            return self._with_scenario_edits(pack, cached) if edited else cached
        with Edat.open(str(path)) as arc:
            found = scenario.of_map(arc, pack)
        with Edat.open(str(glad_path)) as glad:
            kinds = scenario.kinds_of(glad, pack)
        texts = menu_texts(game, {e["key"] for es in kinds.values() for e in es if e["key"] is not None})
        out_list = []
        for f, s in found.items():
            entries = [{"name": e["name"], "kind": e["kind"],
                        "titles": {lang: t[e["key"]] for lang, t in texts.items() if e["key"] in t}}
                       for e in kinds.get(f.lower(), [])]
            kind = entries[0]["kind"] if entries else "unused"
            view = scenario.view(s)
            for k, it in enumerate(view["items"]):
                it["item"] = k
            out_list.append({"file": f, "kind": kind, "entries": entries, **view})
        out_list.sort(key=lambda s: (scenario.KINDS.index(s["kind"]), (s["entries"][0]["name"] if s["entries"] else s["file"]).lower()))
        out = {"scenarios": out_list}
        with self._grounds_lock:
            self._sceneries[key] = out
        return self._with_scenario_edits(pack, out) if edited else out

    def _with_scenario_edits(self, pack: str, base: dict) -> dict:
        """The map's scenarios as the current mod leaves them (a copy; the cached ones stay the game's)."""
        moves, spawns = self._read_scenario_edits(pack)
        if not moves and not spawns:
            return base
        out = []
        for s in base["scenarios"]:
            s = {**s, "items": [dict(it) for it in s["items"]]}
            for m in moves:
                if m.file.lower() == s["file"].lower() and m.item < len(s["items"]):
                    s["items"][m.item].update(x=m.x, y=m.y, moved=True)
            for n, sp in enumerate(spawns):
                if sp.file.lower() == s["file"].lower():
                    s["items"].append({"kind": "Spawn", "x": sp.x, "y": sp.y, "turn": sp.rotation, "name": "",
                                       "camp": sp.camp, "what": sp.what, "mine": True, "spawn": n,
                                       "item": len(s["items"])})
            out.append(s)
        return {"scenarios": out}

    @property
    def cache_dir(self) -> Path:
        """Made files the window loads by address (served as `cache/...` by the window's own server)."""
        return self._home / "cache"

    def map_ground(self, pack: str) -> dict:
        """The map's real ground textures as one picture, made once per map pack (about half a minute) and kept in
        the cache: {"url": "cache/ground/..."} when it's there, else {"job": id}; ask again when the job is done."""
        game = self._game()
        if game is None:
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        path = find_pack(game, pack_file(pack))
        if path is None:
            raise StudioError(f"{pack_file(pack)} isn't in the game folder.")
        st = path.stat()
        name = f"{pack}-{st.st_size}-{int(st.st_mtime)}.png"  # a new game build makes a new picture
        out = self.cache_dir / "ground" / name
        if out.is_file():
            return {"url": f"cache/ground/{name}"}
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id
        return job.start(lambda say: ground_png(game, pack, out, progress=lambda d, n: say(f"{d}/{n}")),
                         "The ground textures are ready.")

    def map_models(self, pack: str) -> dict:
        """The real 3D models of the map's scenery (rusemod.models, from DomesticNukes and his Claude's .spk notes),
        made once per map and game build (about ten seconds) and kept in the cache: {"base": "cache/models/.../",
        "index": {...}} when they're there, else {"job": id}; ask again when the job is done. The index's type
        numbers are map_scenery's."""
        from rusemod import models
        game = self._game()
        if game is None:
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        types = self.map_scenery(pack)["types"]
        zz = find_pack(game, "ZZ_Win.dat")
        st = zz.stat()
        folder = f"{st.st_size}-{int(st.st_mtime)}"  # a new game build makes new models
        out = self.cache_dir / "models" / folder
        name = f"models:{folder}:{pack}"
        done = self._models_done.get(name)
        if done is not None:
            return {"base": f"cache/models/{folder}/", "index": done}
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id

        def work(say):
            self._models_done[name] = models.map_models(game, types, out, say=say)

        return job.start(work, "The 3D models are ready.")

    # --- a map's scenarios, edited: maps/<pack>/scenario.toml in the current mod (MOD_FORMAT §8, rusemod.scenario):
    # starting points and other items moved, units and buildings spawned ---
    SCENARIO_HEADER = ("The starting points and other items this mod moves on this map's scenarios, and the units and "
                       "buildings it spawns (docs/MOD_FORMAT.md §8).\nMade in the RUSE Studio, which rewrites this file.")

    def _scenario_file(self, pack: str) -> Path:
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: scenario changes are saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "scenario.toml"

    def _read_scenario_edits(self, pack: str) -> tuple[list, list]:
        """(moves, spawns) the current mod makes on this map's scenarios; none without a mod."""
        if self._mod_dir() is None:
            return [], []
        path = self._scenario_file(pack)
        if not path.is_file():
            return [], []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            return (scenario.parse_moves(data.get("move", []), str(path)),
                    scenario.parse_spawns(data.get("spawn", []), str(path)))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, scenario.ScenarioError) as exc:
            raise StudioError(f"{path} has a mistake ({exc}). Fix it, or delete it to start over.") from None

    def _write_scenario_edits(self, pack: str, moves: list, spawns: list) -> Path:
        path = self._scenario_file(pack)
        if moves or spawns:
            ModEdits._write(path, scenario.moves_toml(moves, self.SCENARIO_HEADER) + "\n" + scenario.spawns_toml(spawns))
        elif path.is_file():
            path.unlink()
        return path

    def _base_scenario(self, pack: str, file: str) -> dict:
        found = next((s for s in self.map_scenarios(pack, edited=False)["scenarios"] if s["file"].lower() == file.lower()), None)
        if found is None:
            raise StudioError(f"{pack} has no scenario {file}")
        return found

    def scenario_move(self, pack: str, file: str, item: int, x: float, y: float) -> dict:
        """Put design item `item` of scenario `file` at x, y in the current mod (a second move of it replaces the
        first). Returns the map's scenarios as the mod leaves them."""
        base = self._base_scenario(pack, file)
        if not 0 <= int(item) < len(base["items"]):
            raise StudioError(f"{file} has no item {item}")
        kind = base["items"][int(item)]["kind"]
        if kind not in scenario.KINDS_MOVABLE:
            raise StudioError(f"a {kind or 'plain item'} can't be moved")
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            moves = [m for m in moves if not (m.file.lower() == file.lower() and m.item == int(item))]
            moves.append(scenario.Move(file, int(item), kind, float(x), float(y)))
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_put_back(self, pack: str, file: str, item: int) -> dict:
        """Undo the current mod's move of item `item` (it goes back where the game has it)."""
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            moves = [m for m in moves if not (m.file.lower() == file.lower() and m.item == int(item))]
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_spawn(self, pack: str, file: str, unit: str, x: float, y: float, camp: int | None = 1,
                       rotation: float = 0.0) -> dict:
        """Spawn a unit or building (`unit`: its address, as the unit list gives it) when scenario `file` starts, at
        x, y, for side `camp`. Returns the map's scenarios as the mod leaves them."""
        self._base_scenario(pack, file)
        ix = self._open()
        try:
            try:
                o = ix.show(unit)
            except KeyError:
                raise StudioError(f"There's no unit at {unit}.") from None
            name = next((t for p, _n, t in o["values"] if p == "ClassNameForDebug" and t), None)
        finally:
            ix.close()
        if not name:
            raise StudioError(f"{_tail(unit)} has no class name for the game's scripts, so it can't be spawned")
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            spawns.append(scenario.Spawn(file, name, float(x), float(y), None if camp is None else int(camp), float(rotation)))
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_move_spawn(self, pack: str, number: int, x: float, y: float) -> dict:
        """Put the current mod's spawn number `number` at x, y."""
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            if not 0 <= int(number) < len(spawns):
                raise StudioError("that spawn isn't in the mod any more")
            spawns[int(number)] = replace(spawns[int(number)], x=float(x), y=float(y))
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_remove_spawn(self, pack: str, number: int) -> dict:
        """Take back the current mod's spawn number `number` (its place among the mod's spawns on this map)."""
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            if not 0 <= int(number) < len(spawns):
                raise StudioError("that spawn isn't in the mod any more")
            del spawns[int(number)]
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    # --- placing objects on a map: maps/<pack>/scenery.toml in the current mod (MOD_FORMAT §8, rusemod.scenery) ---
    SCENERY_HEADER = ("The objects this mod adds to this map, in order (docs/MOD_FORMAT.md §8).\nMade in the RUSE "
                      "Studio, which rewrites this file.")

    def _scenery_file(self, pack: str) -> Path:
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: what you place is saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "scenery.toml"

    @staticmethod
    def _read_objects(path: Path) -> list:
        if not path.is_file():
            return []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            return scenery.parse_objects(data.get("object", []), str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, scenery.SceneryEditError) as exc:
            raise StudioError(f"{path} can't be read ({exc}). Fix or remove it by hand: the Studio won't write over "
                              f"it.") from None

    def _write_objects(self, path: Path, objects: list) -> None:
        if objects:
            ModEdits._write(path, scenery.objects_toml(objects, self.SCENERY_HEADER))
            return
        if path.is_file():
            path.unlink()
        for folder in (path.parent, path.parent.parent):
            try:
                folder.rmdir()
            except OSError:
                break

    def scenery(self, pack: str) -> dict:
        """The objects the current mod places on a map: {"objects": [{type, x, y, turn, size}], "saved": the file or
        None, "mod": the mod or None}."""
        folder = self._mod_dir()
        if folder is None:
            return {"objects": [], "saved": None, "mod": None}
        path = self._scenery_file(pack)
        with self._saving:
            objects = self._read_objects(path)
        return {"objects": [asdict(o) for o in objects], "saved": str(path) if objects else None, "mod": str(folder)}

    def scenery_add(self, pack: str, objects: list) -> dict:
        """Place objects (dicts with the scenery file's keys) after the ones already there, in the current mod. Only
        types the map already uses. Returns {"count": objects placed on the map now, "saved": the file}."""
        path = self._scenery_file(pack)
        try:
            new = scenery.parse_objects(list(objects or []), "the new objects")
        except scenery.SceneryEditError as exc:
            raise StudioError(str(exc)) from None
        known = {row[0] for row in self.map_scenery(pack)["palette"]}
        for o in new:
            if o.type not in known:
                raise StudioError(f"{o.type} isn't one of this map's own types, so the map can't take it.")
        with self._saving:
            every = self._read_objects(path) + new
            self._write_objects(path, every)
        return {"count": len(every), "saved": str(path)}

    def scenery_undo(self, pack: str, count: int = 1) -> dict:
        """Take the last `count` placed objects off the map. Returns {"count": left, "removed": how many went,
        "saved": the file or None}."""
        path = self._scenery_file(pack)
        with self._saving:
            every = self._read_objects(path)
            n = max(0, min(int(count), len(every)))
            left = every[:len(every) - n]
            self._write_objects(path, left)
        return {"count": len(left), "removed": n, "saved": str(path) if left else None}

    # --- shaping a map's ground: maps/<pack>/terrain.toml in the current mod (MOD_FORMAT §8, rusemod.brush) ---
    TERRAIN_HEADER = ("The ground this mod reshapes on this map: brush strokes, applied in order (docs/MOD_FORMAT.md "
                      "§8).\nMade in the RUSE Studio, which rewrites this file.")

    def _terrain_file(self, pack: str) -> Path:
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: the shaped ground is saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "terrain.toml"

    @staticmethod
    def _read_strokes(path: Path) -> list:
        if not path.is_file():
            return []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            return parse_strokes(data.get("stroke", []), str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, BrushError) as exc:
            raise StudioError(f"{path} can't be read ({exc}). Fix or remove it by hand: the Studio won't write over "
                              f"it.") from None

    def _write_strokes(self, path: Path, strokes: list) -> None:
        if strokes:
            ModEdits._write(path, strokes_toml(strokes, self.TERRAIN_HEADER))
            return
        if path.is_file():
            path.unlink()
        for folder in (path.parent, path.parent.parent):  # maps/<pack>, then maps, when they're empty
            try:
                folder.rmdir()
            except OSError:
                break

    def terrain(self, pack: str) -> dict:
        """The strokes the current mod makes on a map's ground, for the Maps view to draw on the game's own:
        {"strokes": [{brush, x, y, radius, height, level, weight}], "saved": the file or None, "mod": the mod or
        None when none is picked}."""
        folder = self._mod_dir()
        if folder is None:
            return {"strokes": [], "saved": None, "mod": None}
        path = self._terrain_file(pack)
        with self._saving:
            strokes = self._read_strokes(path)
        return {"strokes": [asdict(s) for s in strokes], "saved": str(path) if strokes else None, "mod": str(folder)}

    def terrain_add(self, pack: str, strokes: list) -> dict:
        """Add strokes (dicts with the terrain file's keys) after the ones already on the map, in the current mod.
        Returns {"count": strokes on the map now, "saved": the file}."""
        path = self._terrain_file(pack)
        try:
            new = parse_strokes(list(strokes or []), "the new strokes")
        except BrushError as exc:
            raise StudioError(str(exc)) from None
        with self._saving:
            every = self._read_strokes(path) + new
            self._write_strokes(path, every)
        return {"count": len(every), "saved": str(path)}

    def terrain_undo(self, pack: str, count: int = 1) -> dict:
        """Take the last `count` strokes off the map (the file goes when none is left). Returns {"count": strokes
        left, "removed": how many went, "saved": the file or None}."""
        path = self._terrain_file(pack)
        with self._saving:
            every = self._read_strokes(path)
            n = max(0, min(int(count), len(every)))
            left = every[:len(every) - n]
            if n:
                self._write_strokes(path, left)
        return {"count": len(left), "removed": n, "saved": str(path) if left else None}

    # --- the mod being edited ---
    def _settings(self) -> dict:
        try:
            return json.loads((self._home / "studio.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self, settings: dict) -> None:
        self._home.mkdir(parents=True, exist_ok=True)
        (self._home / "studio.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

    def _mod_dir(self) -> Path | None:
        path = self._settings().get("mod")
        return Path(path) if path and Path(path, "mod.toml").is_file() else None

    def _edits(self) -> ModEdits | None:
        folder = self._mod_dir()
        if folder is None:
            return None
        with self._saving:
            return ModEdits(folder)

    def mods(self) -> dict:
        """The mods the Studio knows: the ones made here, and folders opened before. Plus the one being edited."""
        found = {}
        mods_dir = self._home / "mods"
        for f in sorted(mods_dir.iterdir()) if mods_dir.is_dir() else []:
            if (f / "mod.toml").is_file():
                found[str(f)] = f.name
        for path in self._settings().get("recent", []):
            if Path(path, "mod.toml").is_file():
                found.setdefault(path, Path(path).name)
        current = self._mod_dir()
        return {"mods": [{"path": p, "name": n} for p, n in found.items()],
                "current": str(current) if current else None}

    def new_mod(self, name: str) -> dict:
        """Make a new, empty mod in the platform folder and start editing it."""
        name = name.strip()
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "my-mod"
        folder, n = self._home / "mods" / slug, 2
        while folder.exists():
            folder, n = self._home / "mods" / f"{slug}-{n}", n + 1
        (folder / "src").mkdir(parents=True)
        (folder / "mod.toml").write_text(
            f'[mod]\nid          = "{folder.name}"\nname        = {json.dumps(name or folder.name)}\n'
            f'version     = "0.1.0"\ndescription = "Made in the RUSE Studio."\n', encoding="utf-8")
        return self.choose_mod(str(folder))

    def choose_mod(self, path: str) -> dict:
        if not Path(path, "mod.toml").is_file():
            raise StudioError(f"{path} isn't a mod folder (it has no mod.toml)")
        settings = self._settings()
        settings["mod"] = str(path)
        recent = [p for p in settings.get("recent", []) if p != str(path)]
        settings["recent"] = [str(path)] + recent[:9]
        self._save_settings(settings)
        return self.mods()

    def open_mod_folder(self) -> dict:
        if self._window is None:
            return self.mods()
        chosen = pick_folder(self._window)
        return self.choose_mod(chosen) if chosen else self.mods()

    # --- the Settings tab ---
    def game_folder(self) -> dict:
        """The R.U.S.E. folder in use and how it was found: {"path" or None, "picked": chosen by hand (shared with the
        launcher, settings.json), "version": this Studio's version}."""
        from rusemod.home import settings as shared_settings
        game = self._game()
        picked = shared_settings(self._home).get("game_dir")
        return {"path": str(game) if game else None, "picked": bool(picked and game and Path(picked) == game),
                "version": __version__}

    def choose_game_folder(self) -> dict:
        """Ask for the R.U.S.E. folder (when Steam can't tell, or to use another copy); it must hold RUSE.exe. Kept
        in settings.json, which the launcher reads too. Returns game_folder() and, when refused, a "message"."""
        from rusemod.home import save_settings, settings as shared_settings
        if self._window is None:
            return self.game_folder()
        chosen = pick_folder(self._window)
        if not chosen:
            return self.game_folder()
        if not Path(chosen, "RUSE.exe").is_file():
            return {**self.game_folder(), "message": f"{chosen} doesn't have RUSE.exe in it. Pick the R.U.S.E folder itself."}
        values = shared_settings(self._home)
        values["game_dir"] = str(chosen)
        save_settings(self._home, values)
        self._game_dir = None
        return self.game_folder()

    def edited(self) -> list[str]:
        """The named objects the current mod changes: a part changed for all its users marks every one of them. New
        units aren't in it: the list marks them as new instead."""
        try:
            edits = self._edits()
        except EditsFileError:
            return []
        if not edits:
            return []
        names = edits.edited() - set(edits.new_units)
        if edits.shared():
            ix = self._open()
            try:
                for address in edits.shared():
                    try:
                        names |= set(ix.show(address)["owners"])
                    except KeyError:  # not in this game build's index
                        pass
            finally:
                ix.close()
        return sorted(names)

    def edit(self, address: str, prop: str, value, mode: str = "", via: str = "") -> dict:
        """Change one value (a number, or a list of numbers) of an object in the current mod. Saved at once; setting
        the value it had before again removes the change. For a part several units share, `mode` says for whom:
        "own" (only `via`, the unit the modder came from) or "shared" (all of them)."""
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        real, _new = self._resolve(edits, address)
        ix = self._open()
        try:
            o = ix.show(real)
            types = ix.prop_types(o["class"])
            ok, why = self._editable(o)
            if not ok:
                raise StudioError(f"{address} can't be edited here ({why})")
            where, how = self._where(ix, o, mode, via, address, edits)
        finally:
            ix.close()
        p = _props(o).get(prop)
        if p is None or not _can_edit(prop, p):
            raise StudioError(f"{prop} of {address} can't be edited here")
        values = value if isinstance(value, list) else [value]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            raise StudioError(f"{prop}: numbers only")
        if p["list"] != isinstance(value, list):
            raise StudioError(f"{prop}: expected a list of numbers" if p["list"] else f"{prop}: one number")
        if prop in FLAG_LISTS:  # a set of flags: any number of them, each once
            values = list(dict.fromkeys(values))
        elif len(values) != len(p["numbers"]):
            raise StudioError(f"{prop}: expected {len(p['numbers'])} numbers" if p["list"] else f"{prop}: one number")
        kind = types.get(prop + "[]" if p["list"] else prop, "")
        if kind in INT_RANGES:
            values = [_whole(v, kind, prop) for v in values]
        with self._saving:
            edits = ModEdits(edits.folder)  # read again: another change may have been saved meanwhile
            before = edits.get(o["address"], prop, "shared") if how == "own" else None  # what "all of them" got
            before = before if before is not None else (p["numbers"] if p["list"] else p["numbers"][0])
            if (values if p["list"] else values[0]) == before:
                edits.reset(where, prop, how)
            else:
                edits.set(where, prop, values if p["list"] else values[0], how)
        return {"saved": str(edits.file), "value": values if p["list"] else values[0]}

    def reset(self, address: str, prop: str, mode: str = "", via: str = "") -> dict:
        edits = self._edits()
        if edits is None:
            return {"saved": None}
        real, _new = self._resolve(edits, address)
        ix = self._open()
        try:
            where, how = self._where(ix, ix.show(real), mode, via, address, edits)
        finally:
            ix.close()
        with self._saving:
            edits = ModEdits(edits.folder)
            edits.reset(where, prop, how)
        return {"saved": str(edits.file)}

    # --- new units ---
    def new_unit(self, source: str, name: str, price, nation: int = -1, factory: int = -1) -> dict:
        """A new unit in the current mod: a copy of `source` called `name` (in every language), costing `price` at
        every battle date, in the source's build menu or in another nation's (`nation` and `factory`, both given).
        Returns its address, so the page can open it."""
        name = (name or "").strip()
        if not name:
            raise StudioError("Give the new unit a name.")
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            raise StudioError("Price: one number, used for every battle date.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: a new unit is saved in a mod.")
        if source in edits.new_units:
            raise StudioError(f"{name}: copy the unit {_tail(source)} was made from instead (a copy of a copy would "
                              f"lose its changes)")
        ix = self._open()
        try:
            try:
                o = ix.show(source)
            except KeyError:
                raise StudioError(f"{source} isn't in this game build") from None
            if not o["export"] or o["class"] not in KIND_OF:
                raise StudioError(f"{source} isn't a unit or building, so it can't be copied here")
            types = ix.prop_types(o["class"])
            menus = {(u["nation"], u["factory"]) for u in self._all_units(ix) if u["factory"] is not None}
            namespace, tail = source.rsplit("/", 1)
            m = _PREFIX.match(tail)
            prefix = m.group(1) if m else "Descriptor_Unit_"

            def taken(t: str) -> bool:
                if t in edits.new_units:
                    return True
                try:
                    ix.show(t)
                    return True
                except KeyError:
                    return False

            stem = safe_name(name)
            if stem:
                target = f"{namespace}/{prefix}{stem}"
                if taken(target):
                    raise StudioError(f"There's already a unit called {prefix}{stem} (from {name!r}). Pick another "
                                      f"name.")
            else:  # a name without letters or digits A-Z (Japanese, say): the address gets a number instead
                n = 1
                while taken(f"{namespace}/{prefix}New_{n}"):
                    n += 1
                target = f"{namespace}/{prefix}New_{n}"
        finally:
            ix.close()
        values: dict = {}
        prices = _props(o).get("ProductionPrice")
        if prices and _can_edit("ProductionPrice", prices):
            kind = types.get("ProductionPrice[]" if prices["list"] else "ProductionPrice", "")
            p = _whole(price, kind, "ProductionPrice") if kind in INT_RANGES else price
            values["ProductionPrice"] = [p] * len(prices["numbers"]) if prices["list"] else p
        if nation >= 0 or factory >= 0:
            if (nation, factory) not in menus:
                raise StudioError(f"No build menu for nation {nation} and factory {factory}: pick one of the menus "
                                  f"the game has")
            own_nation = next((int(n) for path, n, _t in o["values"] if path == "Nationalite" and n is not None), 0)
            own_factory = next((int(n) for path, n, _t in o["values"] if path == "Factory" and n is not None), None)
            if (nation, factory) != (own_nation, own_factory):
                values["Nationalite"], values["Factory"] = nation, factory
        with self._saving:
            edits = ModEdits(edits.folder)  # read again: another change may have been saved meanwhile
            if target in edits.new_units:
                raise StudioError(f"There's already a unit at {target}. Pick another name.")
            edits.add_unit(target, source, name, values)
        return {"address": target, "name": name, "saved": str(edits.file)}

    def delete_unit(self, address: str) -> dict:
        """Remove a new unit from the current mod: its copy, every change made to it and its parts, and its name."""
        edits = self._edits()
        if edits is None or address not in edits.new_units:
            raise StudioError(f"{address} isn't a unit made in this mod, so it can't be deleted here")
        with self._saving:
            edits = ModEdits(edits.folder)
            source = edits.new_units[address].source if address in edits.new_units else None
            edits.remove_unit(address)
        return {"deleted": address, "source": source, "saved": str(edits.file)}

    def test_in_game(self) -> dict:
        """Build the current mod into its own modded copy (`RUSE-Instances\\studio-<mod>`) and start the game from it,
        in the background. Returns {'job': id}; follow it with job(id)."""
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first.")

        def work(say):
            game = self._game()
            if game is None:
                raise BuildError("We couldn't find R.U.S.E.")
            instance = (self._instances or instances_dir(game)) / f"studio-{folder.name}"
            self._starter.modded(game, [folder], instance, folder.name, say)

        job = Job()
        self._jobs[job.id] = job
        return job.start(work, "R.U.S.E. is starting.", plain=(BuildError, RndfError, OSError))

    # --- a mod as one file (MOD_FORMAT §2, rusemod.package) ---
    def mod_info(self) -> dict:
        """The current mod's manifest, for the export form: id, name, version, authors, description, the game build
        it was last exported on and its fingerprint."""
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first.")
        try:
            return package.info_of(folder)
        except package.PackageError as exc:
            raise StudioError(str(exc)) from None

    def export_mod(self, version: str, author: str = "", description: str = "") -> dict:
        """Turn the current mod into one file, `<id>-<version>.rusemod`, where the modder chooses (the window's "save
        as" dialog). The version, author and description go into the mod's mod.toml first, so the next export starts
        from them (blank author or description: the old ones stay). The mod is built on the game to record the game
        build and its fingerprint (MOD_FORMAT §12) in the package; without the game it's packed without them, and
        the report says so. Returns {'job': id}, or {'job': None} when the modder cancels the dialog."""
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first.")
        version = (version or "").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise StudioError("The version should be three numbers, like 1.0.0.")
        suggested = package.file_name(self.mod_info() | {"version": version})
        if self._pick_save is not None:
            target = self._pick_save(suggested)
        else:
            target = pick_save(self._window, suggested, PACKAGE_FILES) if self._window is not None else None
        if not target:
            return {"job": None}
        target = Path(target)
        if target.suffix.lower() != package.EXTENSION:
            target = target.with_name(target.name + package.EXTENSION)
        manifest = {"version": version}
        if (author or "").strip():
            manifest["authors"] = [author.strip()]
        if (description or "").strip():
            manifest["description"] = description.strip()

        def work(say):
            with self._saving:
                package.update_manifest(folder, mod=manifest)
            game = self._game()
            build_id = revision = fingerprint = None
            if game is None:
                say("R.U.S.E. wasn't found, so the file carries no game build or fingerprint.")
            else:
                say("Building the mod on the game, to record the game build and the fingerprint…")
                result = build_and_write(game, [load_mod(folder)], say=lambda line: say("  " + line))
                if result.errors:
                    raise BuildError("Fix the mod first: the build above has errors, so nothing was exported.")
                build_id = build_of(game)
                revisions = data_revisions(game)
                revision = revisions[0] if len(revisions) == 1 else None
                fingerprint = fingerprint_text(result.fingerprint) if result.fingerprint else None
            with self._saving:
                path = package.pack(folder, target, build_id=build_id, data_revision=revision, fingerprint=fingerprint)
            say(f"Saved as {path}")

        job = Job()
        self._jobs[job.id] = job
        return job.start(work, f"Saved as {target}", plain=(BuildError, RndfError, OSError, package.PackageError))

    # --- building the index from the Studio ---
    def build_index(self) -> dict:
        job = Job()
        self._jobs[job.id] = job
        game = self._game()
        if game is None:
            job.state, job.message = "failed", "We couldn't find R.U.S.E."
            return {"job": job.id}

        def work(say):
            build_index(game, self._path(), say=say)
            self._units = None

        return job.start(work, "The game index is ready.")

    def job(self, job_id: str, since: int = 0) -> dict:
        return job_view(self._jobs, job_id, since)
