"""What the Studio's screens can ask for. Plain JSON-friendly data in and out, like the launcher's API; every answer
comes from the game index, opened read-only for each question (the window calls from several threads)."""
from __future__ import annotations

import os
import threading
from pathlib import Path

from .. import schema
from ..index import Index, build_index, default_path
from ..steam import find_game
from ..webui import Job

KINDS = {"ground": ("TUniteAuSolDescriptor",), "infantry": ("TInfanterieDescriptor",),
         "air": ("TAvionDescriptor",), "buildings": ("TBatimentDescriptor",)}
KIND_OF = {cls: kind for kind, classes in KINDS.items() for cls in classes}
ALL_CLASSES = tuple(KIND_OF)


def _tail(address: str) -> str:
    return address.rsplit("/", 1)[-1]


class StudioApi:
    def __init__(self, index_path=None, game_dir=None, find=find_game):
        self._index_path = Path(index_path) if index_path else None
        self._game_dir = Path(game_dir) if game_dir else None
        self._find = find
        self._jobs: dict[str, Job] = {}
        self._units: list | None = None  # every unit and building, read once per index

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
        """One unit (or any object): its values in groups, its parts and what uses it."""
        ix = self._open()
        try:
            o = ix.show(address)
            plan = ix.clone_plan(address)
            parts = [{"address": a, "class": ix.show(a)["class"], "shared": False} for a in plan["copied"]] + \
                    [{"address": a, "class": ix.show(a)["class"], "shared": True} for a in plan["shared"]]
            used_by = [{"address": a, "path": p} for a, p in ix.used_by(address)[:30]]
            key = next((t for p, _n, t in o["values"] if p == "NameInMenuToken"), None)
            shown = ix.names([key], lang).get(key) if key and lang != schema.BASE else None
        finally:
            ix.close()
        rows: dict[str, dict] = {}
        for path, num, text in o["values"]:
            prop = path.split("[", 1)[0]
            row = rows.setdefault(prop, {"prop": prop, "label": schema.label(prop, lang), "group": schema.group(prop),
                                         "values": []})
            value = (str(int(num)) if num == int(num) else f"{num:g}") if num is not None else text
            if prop == "Nationalite" and num is not None:
                value = f"{int(num)} ({schema.nation(num, lang)})"
            elif prop == "NameInMenuToken" and shown:
                value = f"{text} ({shown})"
            row["values"].append(value)
        if "Nationalite" not in rows and o["class"] in KIND_OF:  # 0 isn't written
            rows["Nationalite"] = {"prop": "Nationalite", "label": schema.label("Nationalite", lang),
                                   "group": "identity", "values": [f"0 ({schema.nation(0, lang)})"]}
        groups = []
        for g in schema.GROUP_ORDER:
            members = [r for r in rows.values() if r["group"] == g]
            if members:
                groups.append({"key": g, "name": schema.group_name(g, lang), "rows": members})
        return {"address": o["address"], "class": o["class"], "name": shown or _tail(o["address"]),
                "stable": o["stable"], "shared": o["shared"], "owners": o["owners"], "groups": groups,
                "parts": parts, "used_by": used_by}

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
        return job.view(since) if job else {"id": job_id, "state": "failed", "message": "unknown job", "lines": [],
                                            "count": 0}
