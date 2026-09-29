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
from dataclasses import asdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from rusemod import identity, schema
from rusemod.brush import BrushError, parse_strokes, strokes_toml
from rusemod.build import BuildError
from rusemod.home import default_home, game_dir as find_game_dir
from rusemod.index import LIST_VALUES, Index, build_index, default_path
from rusemod.patch import INT_RANGES
from rusemod.play import Starter, instances_dir
from rusemod.rndf import RndfError
from rusemod.steam import find_game
from rusemod.build import find_pack
from rusemod.terrain import LODS, ground_png, map_list, pack_file, terrain
from rusemod.webui import Job, job_view, pick_folder

from .edits import EditsFileError, ModEdits, NewUnit

KINDS = {"ground": ("TUniteAuSolDescriptor",), "infantry": ("TInfanterieDescriptor",),
         "air": ("TAvionDescriptor",), "buildings": ("TBatimentDescriptor",)}
KIND_OF = {cls: kind for kind, classes in KINDS.items() for cls in classes}
NOT_EDITABLE = {"DescriptorId", "TrackingId", "Nationalite"}  # ids stay unique (rusemod.identity); moving a unit to
# another nation needs more than one number (its menus, and the new nation's add-on for China), so it comes later
ALL_CLASSES = tuple(KIND_OF)
NATIONS = 7
_PREFIX = re.compile(r"^(Descriptor_[A-Za-z]+_)")  # Descriptor_Unit_M4_Sherman -> a copy is Descriptor_Unit_<Name>


def _tail(address: str) -> str:
    return address.rsplit("/", 1)[-1]


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
        and not (p["list"] and len(p["numbers"]) >= LIST_VALUES)  # the index keeps 16 items: there may be more


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


class StudioApi:
    def __init__(self, index_path=None, game_dir=None, find=find_game, home=None, starter=None, instances=None):
        self._index_path = Path(index_path) if index_path else None
        self._game_dir = Path(game_dir) if game_dir else None
        self._find = find
        self._home = Path(home) if home else default_home()
        self._starter = starter or Starter()
        self._instances = Path(instances) if instances else None
        self._jobs: dict[str, Job] = {}
        self._units: list | None = None  # every unit and building, read once per index
        self._window = None  # set by the window (a folder dialog for "Open a mod folder")
        self._saving = threading.RLock()  # the window calls from several threads: one change to the file at a time,
        # and no reading it mid-change (Windows can't replace a file that's open)
        self._grounds: dict[tuple, dict] = {}  # the last maps shown in 3D, so switching back is instant
        self._grounds_lock = threading.Lock()
        self._ground_jobs: dict[str, str] = {}  # picture being made -> its job, so asking twice doesn't make it twice

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

    def units(self, lang: str = schema.BASE, kind: str = "all", nation: int = -1, search: str = "") -> dict:
        """The units and buildings to list, with names in `lang` (the game's names by default). The current mod's
        new units come first, under the nation and factory they were given, marked `new`."""
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
            src = by_address.get(unit.source, {"class": "TUniteAuSolDescriptor", "nation": 0, "factory": None})
            own = edits.of(unit.target)
            new.append({"address": unit.target, "class": src["class"], "key": None,
                        "nation": int(own.get("Nationalite", src["nation"])),
                        "factory": own.get("Factory", src["factory"]), "slot": None, "new": True,
                        "source": unit.source, "name": unit.name})
        words = search.strip().lower()
        out = []
        for u in new + rows:
            k = KIND_OF.get(u["class"], "ground")
            if kind != "all" and k != kind or nation >= 0 and u["nation"] != nation:
                continue
            name = u.get("name") or names.get(u["key"]) or _tail(u["address"])
            if words and words not in name.lower() and words not in u["address"].lower():
                continue
            out.append({"address": u["address"], "name": name, "base_name": _tail(u["address"]), "kind": k,
                        "nation": u["nation"], "nation_name": schema.nation(u["nation"], lang),
                        "factory": u["factory"], "slot": u["slot"], "new": u.get("new", False),
                        "source": u.get("source")})
        return {"units": out, "total": len(rows) + len(new)}

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
        if p["list"] != isinstance(value, list) or len(values) != len(p["numbers"]):
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
