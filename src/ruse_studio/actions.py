"""Which animation each action plays, on a new unit's page (StudioApi's ActionCalls; item 5 of the owner's list,
part 2, 2026-11-10): a unit with a model of its own and its model's animations (Import model; rusemod.anim
.set_animations) shows every action the game plays for it, each with the animation it plays, picked from the model's
animations or left on Nearest, and the page says which one the nearest is (rusemod.animactions: one rule for the page
and the build, so what the page says is what the game plays). Stand, walk and run are the least a model needs: the
page names any of them that has nothing of its own. The ride on long moves: as itself, playing one of its animations
on a loop, or in its truck.

Copies (the owner, 2026-11-10: "They should have the same animation. The only way you should change animation is in
Ruse Decoy, you go and change the animation for your new unit."): a unit copied from one with animations of its own
takes them along (_animations_along, called by StudioApi._unit_new; rusemod.anim.copy_unit). The page only picks
which of a model's animations an action plays; changing an animation itself is RUSE Decoy's."""
from __future__ import annotations

from pathlib import Path


class ActionCalls:
    def _actions_unit(self, address: str):
        """(the mod's folder, the unit's name in units.toml, its NewUnit) for a new unit of the current mod, else
        None."""
        from .api import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:
            return None
        unit = edits.new_unit_of(address) if edits else None
        mod = self._mod_dir()
        if unit is None or mod is None or ":" in address:
            return None
        return mod, unit.target.rsplit("/", 1)[-1], unit

    def _action_listings(self, source: str, models: set | None) -> list:
        """[(figure path, action, the game's clip it plays)] of the figures of the game's unit `source` that draw one
        of `models` (rusemod.unitmodel.model_key's names; None: every figure), from the game index, walked as the
        build walks a unit's graphics (rusemod.anim.unit_figures: its GfxDescriptor* parts and the parts under them,
        never another named object)."""
        from rusemod.unitmodel import model_key
        ix = self._open()
        try:
            db = ix.db
            row = db.execute("SELECT id FROM object WHERE address = ? ORDER BY shadow LIMIT 1", (source,)).fetchone()
            if row is None:
                return []
            out, seen = [], set()

            def text(oid, path):
                got = db.execute("SELECT text FROM value WHERE object = ? AND path = ?", (oid, path)).fetchone()
                return got[0] if got and got[0] else None

            def walk(oid, path, depth):
                if depth > 24 or oid in seen:
                    return
                seen.add(oid)
                refs = db.execute("SELECT path, dst FROM ref WHERE src = ? ORDER BY rowid", (oid,)).fetchall()
                clips = [(p, d) for p, d in refs if p.startswith("ResourceAnimation[") and p.endswith("].v")]
                if clips:
                    mesh = next((d for p, d in refs if p == "MeshDescriptor"), None)
                    model = text(mesh, "FileName") if mesh is not None else None
                    if models is None or (model and model_key(model) in models):
                        for p, d in sorted(clips, key=lambda pd: int(pd[0].split("[", 1)[1].split("]", 1)[0])):
                            key = text(oid, p[:-2] + ".k")
                            if key:
                                out.append((path, key, text(d, "FileName")))
                for p, d in refs:
                    if p.startswith("ResourceAnimation") or p == "MeshDescriptor":
                        continue
                    a = db.execute("SELECT address FROM object WHERE id = ?", (d,)).fetchone()
                    if a and a[0] and ":" in a[0]:   # (a part, never a named object of the game's)
                        walk(d, f"{path}.{p}" if path else p, depth + 1)

            for p, d in db.execute("SELECT path, dst FROM ref WHERE src = ? ORDER BY rowid", (row[0],)).fetchall():
                if p.startswith("GfxDescriptor"):
                    walk(d, p, 1)
            return out
        finally:
            ix.close()

    def unit_actions(self, address: str, lang: str = "us") -> dict:
        """The action table of a new unit with a model of its own and its model's animations: {"own": whether it has
        them (no table for any other unit), "editable", "animations": [{"name", "seconds", "frames"}] in the model's
        order, "rows": [{"action", "section", "picked", "plays": {"top"/"bottom"/"all": animation}, "how": "picked",
        "named" or "nearest", "nearest": what it plays when its pick goes, "keys"}] (rusemod.animactions.table),
        "needed": stand, walk and run, "missing": those of them that have nothing of their own, "ride": {"can": it
        rides a truck on long moves, "truck": that truck's name, "itself": it rides as itself, "picked", "plays",
        "how"}}."""
        from rusemod import anim, animactions, baf
        from rusemod.modelin import OWN_SKELETON
        from rusemod.unitmodel import model_key
        found = self._actions_unit(address)
        if found is None:
            return {"own": False}
        mod, tail, unit = found
        try:
            own = anim.own_animations(mod, tail)
        except anim.AnimError:
            own = {"animations": {}, "plays": {}, "ride": None}
        record = self._own_model_record(address)
        if not own["animations"] or record is None:
            return {"own": False}
        names = list(own["animations"])
        picks = {a: n for a, n in own["plays"].items() if n in own["animations"]}
        info = []
        for n in names:
            seconds = frames = None
            try:
                c = baf.parse((mod / anim.OWN / tail / own["animations"][n]).read_bytes())
                seconds, frames = round(c.duration, 3), c.frames
            except (OSError, baf.ClipError):
                pass
            info.append({"name": n, "seconds": seconds, "frames": frames})
        report = record.get("report") or {}
        models = {model_key(m) for m in [report.get("like"), *(report.get("also") or [])] if m} or None
        listings = self._action_listings(unit.source, models)
        rows = animactions.table(listings, names, picks)
        for r in rows:   # (what a picked action would play were its pick taken out)
            if r["picked"]:
                left = {a: n for a, n in picks.items() if a != r["action"]}
                mine = [x for x in listings if animactions.parse_key(x[1])[1] == r["action"]]
                r["nearest"] = animactions.table(mine, names, left)[0]["plays"] if mine else {}
            else:
                r["nearest"] = r["plays"]
        try:
            rides = self.rides_in(address, lang)
        except Exception:  # (no index or no game: no ride shown)
            rides = {}
        truck = next((c["name"] for c in rides.get("choices", []) if c["address"] == rides.get("now")), None)
        plays, how = animactions.ride(names, picks)
        nearest, _ = animactions.ride(names, {a: n for a, n in picks.items() if a != animactions.RIDE})
        return {"own": True, "editable": True, "animations": info, "rows": rows, "needed": list(animactions.NEEDED),
                "missing": animactions.missing(rows),
                "ride": {"can": bool(rides), "truck": truck, "itself": own["ride"] != "truck",
                         "picked": picks.get(animactions.RIDE), "plays": plays, "how": how, "nearest": nearest},
                "skeleton": (report.get(OWN_SKELETON) or {}).get("bones")}

    def unit_action_set(self, address: str, action: str, animation: str | None, lang: str = "us") -> dict:
        """The unit's action `action` (a row of unit_actions) plays its model's animation `animation`; None or ""
        takes the pick out (it plays the nearest again). Saved in the mod's files/anim/units.toml. Returns
        unit_actions()."""
        from rusemod import anim
        from .api import StudioError
        found = self._actions_unit(address)
        if found is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        mod, tail, _unit = found
        now = self.unit_actions(address, lang)
        if not now.get("own"):
            # not a game rule: the page's table is for a unit with its model's own animations
            raise StudioError("This unit has no animations of its own: import a model that has some first.")
        if action not in {r["action"] for r in now["rows"]} | {"ride"}:
            raise StudioError(f"{action} isn't one of this unit's actions.")
        if animation and animation not in {a["name"] for a in now["animations"]}:
            raise StudioError(f"{animation} isn't one of its model's animations.")
        with self._saving:
            try:
                anim.set_pick(mod, tail, action, animation or None)
            except anim.AnimError as exc:
                raise StudioError(str(exc)) from None
        return self.unit_actions(address, lang)

    def unit_ride_set(self, address: str, ride: str | None, lang: str = "us") -> dict:
        """How the unit goes on long moves: "truck" in its truck; "" (or None) as itself playing the nearest
        animation; an animation's name as itself playing that one. Returns unit_actions()."""
        from rusemod import anim, animactions
        from .api import StudioError
        found = self._actions_unit(address)
        if found is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        mod, tail, _unit = found
        now = self.unit_actions(address, lang)
        if not now.get("own"):
            raise StudioError("This unit has no animations of its own: import a model that has some first.")
        if ride and ride != "truck" and ride not in {a["name"] for a in now["animations"]}:
            raise StudioError(f"{ride} isn't one of its model's animations.")
        with self._saving:
            try:
                anim.set_ride(mod, tail, "truck" if ride == "truck" else None)
                if ride != "truck":
                    anim.set_pick(mod, tail, animactions.RIDE, ride or None)
            except anim.AnimError as exc:
                raise StudioError(str(exc)) from None
        return self.unit_actions(address, lang)

    def _animations_ready(self, mod: Path) -> None:
        """Before a unit is copied: the mod's units.toml must be readable, so the copy can take its source's
        animations along (a StudioError naming the file's mistake, nothing made)."""
        from rusemod import anim
        from .api import StudioError
        try:
            anim.read_units(mod)
        except anim.AnimError as exc:
            raise StudioError(f"{exc}. Fix that file (or delete it) first: a copy takes the animations of the unit "
                              f"it copies from it.") from None

    def _animations_along(self, mod: Path, source: str, target: str) -> bool:
        """The new unit `target` (just made, a copy of `source`) takes `source`'s own animations along (the owner,
        2026-11-10, above): its rows in files/anim/units.toml and its folder of clips (rusemod.anim.copy_unit).
        Whether it had any."""
        from rusemod import anim
        from .api import StudioError
        try:
            return anim.copy_unit(mod, source.rsplit("/", 1)[-1], target.rsplit("/", 1)[-1])
        except anim.AnimError as exc:
            raise StudioError(f"The copy was made, but it couldn't take the animations of the unit it copies: "
                              f"{exc}") from None
