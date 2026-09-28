"""What the Studio's screens can ask for. Plain JSON-friendly data in and out, like the launcher's API; every answer
comes from the game index, opened read-only for each question (the window calls from several threads).

Editing: the modder works in one mod at a time (made here, in the platform folder's `mods/`, or any mod folder they
open). Every change is saved at once in that mod's `src/studio.rndf` (studio/edits.py); Play builds the mod into a
modded copy and starts the game, like the launcher.
"""
from __future__ import annotations

import json
import os
import re
import struct
import threading
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from .. import schema
from ..home import default_home
from ..index import LIST_VALUES, Index, build_index, default_path
from ..launcher.api import LauncherApi
from ..patch import INT_RANGES
from ..steam import find_game
from ..webui import Job
from .edits import EditsFileError, ModEdits

KINDS = {"ground": ("TUniteAuSolDescriptor",), "infantry": ("TInfanterieDescriptor",),
         "air": ("TAvionDescriptor",), "buildings": ("TBatimentDescriptor",)}
KIND_OF = {cls: kind for kind, classes in KINDS.items() for cls in classes}
NOT_EDITABLE = {"DescriptorId", "TrackingId", "Nationalite"}  # ids stay unique (rusemod.identity); moving a unit to
# another nation needs more than one number (its menus, and the new nation's add-on for China), so it comes later
ALL_CLASSES = tuple(KIND_OF)


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


class StudioError(Exception):
    pass


class StudioApi:
    def __init__(self, index_path=None, game_dir=None, find=find_game, home=None, launcher=None):
        self._index_path = Path(index_path) if index_path else None
        self._game_dir = Path(game_dir) if game_dir else None
        self._find = find
        self._home = Path(home) if home else default_home()
        self._launcher = launcher or LauncherApi(game_dir=game_dir, home=self._home, find=find)
        self._jobs: dict[str, Job] = {}
        self._units: list | None = None  # every unit and building, read once per index
        self._window = None  # set by the window (a folder dialog for "Open a mod folder")
        self._saving = threading.Lock()  # the window calls from several threads; one change to the file at a time

    # --- where things are ---
    def _game(self) -> Path | None:
        if self._game_dir:
            return self._game_dir
        if os.environ.get("RUSE_GAME"):
            return Path(os.environ["RUSE_GAME"])
        found = self._find()
        return Path(found["game_dir"]) if found else None

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
        return schema.ui(lang)

    def nations(self, lang: str = schema.BASE) -> list[str]:
        return [schema.nation(n, lang) for n in range(7)]

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

    def units(self, lang: str = schema.BASE, kind: str = "all", nation: int = -1, search: str = "") -> dict:
        """The units and buildings to list, with names in `lang` (the game's names by default)."""
        ix = self._open()
        try:
            rows = self._all_units(ix)
            names = ix.names([u["key"] for u in rows], lang) if lang != schema.BASE else {}
        finally:
            ix.close()
        words = search.strip().lower()
        out = []
        for u in rows:
            k = KIND_OF.get(u["class"], "ground")
            if kind != "all" and k != kind or nation >= 0 and u["nation"] != nation:
                continue
            name = names.get(u["key"]) or _tail(u["address"])
            if words and words not in name.lower() and words not in u["address"].lower():
                continue
            out.append({"address": u["address"], "name": name, "base_name": _tail(u["address"]), "kind": k,
                        "nation": u["nation"], "nation_name": schema.nation(u["nation"], lang),
                        "factory": u["factory"], "slot": u["slot"]})
        return {"units": out, "total": len(rows)}

    def unit(self, address: str, lang: str = schema.BASE) -> dict:
        """One unit (or any object): its values in groups, its parts and what uses it, with the current mod's edits."""
        ix = self._open()
        try:
            o = ix.show(address)
            types = ix.prop_types(o["class"])
            plan = ix.clone_plan(address)
            parts = [{"address": a, "class": ix.show(a)["class"], "shared": False} for a in plan["copied"]] + \
                    [{"address": a, "class": ix.show(a)["class"], "shared": True} for a in plan["shared"]]
            uses = []
            for a in plan["references"]:  # named objects it uses (weapons, ammo…): editable on their own page
                try:
                    uses.append({"address": ix.show(a)["address"], "class": ix.show(a)["class"]})
                except KeyError:  # an import the index couldn't find
                    pass
            all_users = ix.used_by(address)
            used_by = [{"address": a, "path": p} for a, p in all_users[:30]]
            key = next((t for p, _n, t in o["values"] if p == "NameInMenuToken"), None)
            shown = ix.names([key], lang).get(key) if key and lang != schema.BASE else None
        finally:
            ix.close()
        editable, why = self._editable(o)
        try:
            mod = self._edits()
        except EditsFileError as exc:  # browsing still works; editing waits until the file is fixed
            mod, editable, why = None, False, str(exc)
        edits = mod.of(o["address"]) if mod else {}
        users = len({a.split(":")[0] for a, _p in all_users})
        rows: dict[str, dict] = {}
        for prop, p in _props(o).items():
            values = []
            for num, text in zip(p["numbers"], p["texts"]):
                if prop == "Nationalite" and num is not None:
                    values.append(f"{num} ({schema.nation(num, lang)})")
                elif prop == "NameInMenuToken" and shown:
                    values.append(f"{text} ({shown})")
                else:
                    values.append(text if num is None else str(num))
            rows[prop] = {"prop": prop, "label": schema.label(prop, lang), "group": schema.group(prop),
                          "values": values, "numbers": p["numbers"], "list": p["list"],
                          "type": types.get(prop + "[]" if p["list"] else prop, ""),
                          "editable": editable and _can_edit(prop, p),
                          "locked": prop in NOT_EDITABLE, "edited": edits.get(prop)}
        if "Nationalite" not in rows and o["class"] in KIND_OF:  # 0 isn't written
            rows["Nationalite"] = {"prop": "Nationalite", "label": schema.label("Nationalite", lang),
                                   "group": "identity", "values": [f"0 ({schema.nation(0, lang)})"], "numbers": [0],
                                   "list": False, "type": "int32", "editable": False, "locked": True, "edited": None}
        groups = []
        for g in schema.GROUP_ORDER:
            members = [r for r in rows.values() if r["group"] == g]
            if members:
                groups.append({"key": g, "name": schema.group_name(g, lang), "rows": members})
        return {"address": o["address"], "class": o["class"], "name": shown or _tail(o["address"]),
                "stable": o["stable"], "shared": o["shared"], "owners": o["owners"], "groups": groups,
                "parts": parts, "uses": uses, "used_by": used_by, "editable": editable, "why_not": why,
                "users": users if o["export"] and o["class"] not in KIND_OF and users > 1 else 0}

    def _editable(self, o: dict) -> tuple[bool, str]:
        """Whether this object's values can be edited from the Studio, and if not, why (a key of the tool's words)."""
        if not o["stable"]:
            return False, "not_stable"
        if o["shared"] and not o["export"]:
            return False, "shared_part_later"
        return True, ""

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
        return ModEdits(folder) if folder else None

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
        import webview
        chosen = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        return self.choose_mod(chosen[0]) if chosen else self.mods()

    def edited(self) -> list[str]:
        try:
            edits = self._edits()
        except EditsFileError:
            return []
        return sorted(edits.edited()) if edits else []

    def edit(self, address: str, prop: str, value) -> dict:
        """Change one value (a number, or a list of numbers) of an object in the current mod. Saved at once; setting
        the game's own value again removes the change."""
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        ix = self._open()
        try:
            o = ix.show(address)
            types = ix.prop_types(o["class"])
        finally:
            ix.close()
        ok, why = self._editable(o)
        if not ok:
            raise StudioError(f"{address} can't be edited here ({why})")
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
            if values == p["numbers"]:
                edits.reset(o["address"], prop)
            else:
                edits.set(o["address"], prop, values if p["list"] else values[0])
        return {"saved": str(edits.file), "value": values if p["list"] else values[0]}

    def reset(self, address: str, prop: str) -> dict:
        with self._saving:
            edits = self._edits()
            if edits is not None:
                edits.reset(address, prop)
        return {"saved": str(edits.file) if edits else None}

    def play(self) -> dict:
        """Build the current mod into its own modded copy and start the game from it."""
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first.")
        return self._launcher.play_folders(folder.name, [str(folder)], f"studio-{folder.name}")

    # --- building the index from the Studio ---
    def build_index(self) -> dict:
        job = Job()
        self._jobs[job.id] = job
        game = self._game()
        if game is None:
            job.state, job.message = "failed", "We couldn't find R.U.S.E."
            return {"job": job.id}

        def run():
            try:
                build_index(game, self._path(), say=job.say)
                self._units = None
                job.state, job.message = "done", "The game index is ready."
            except Exception as exc:  # shown to the modder as it is
                job.state, job.message = "failed", f"{type(exc).__name__}: {exc}"

        threading.Thread(target=run, daemon=True).start()
        return {"job": job.id}

    def job(self, job_id: str, since: int = 0) -> dict:
        job = self._jobs.get(job_id)
        return job.view(since) if job else self._launcher.job(job_id, since)
