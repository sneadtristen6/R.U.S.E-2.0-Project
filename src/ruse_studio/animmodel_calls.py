"""A model on bones of its own and its animations in the Studio (StudioApi's AnimModelCalls; the owner's list, item 5,
part 1: a horse that runs and stops, a rifleman on it who shoots, any creature, brought in by the modder; the
engine's side is rusemod.animmodel).

Import model, and Bring back the model after Blender (ruse_studio.modelblender), take a .glb whose points lean on bones
the unit's own model hasn't got as a model on bones of its own (_own_bones_fit): its skeleton and every animation come
in with it (rusemod.unitmodel.import_model's own_bones), each animation is kept as a clip of the unit's own and each
action of the unit plays the animation named for it (rusemod.animmodel.keep_animations), and the model's record
(files/models/<the unit's name>.json) says what came in (_record_more). A file on the game soldier's own bones goes
on as before (item 4's way). Taking the model out takes its animations out too (_animations_out). The unit's page
shows what came in: model_animations."""
from __future__ import annotations

import json
from pathlib import Path


class AnimModelCalls:
    def _own_bones_fit(self, address: str, file: Path, found: list, target: Path, size: float,
                       clips: dict) -> dict | None:
        """Import model's way for a model on bones of its own: when none of the unit's models (`found`) took the file
        (the loop in StudioApi._fit_model) and its points lean on bones none of them has (rusemod.animmodel.
        own_bones_on), the file comes in on its own skeleton in the place of the first of them the game draws with
        bones (a squad: every soldier of it), its animations as game clips into `clips`. None when the file isn't
        such a model (the loop's own words then say why it wasn't taken)."""
        from rusemod import animmodel
        from rusemod.modelin import ModelError
        from rusemod.unitmodel import import_model
        from .api import StudioError
        if Path(file).suffix.lower() not in (".glb", ".gltf"):
            return None
        try:
            on = animmodel.own_bones_on(self._game(), Path(file), found)
        except (ModelError, OSError, ValueError):   # (a file the importer can't read: the loop said why)
            return None
        if on is None:
            return None
        try:
            return import_model(self._game(), on, Path(file), target, size=size, others=found, own_bones=True,
                                clips=clips)
        except (ModelError, OSError, ValueError) as exc:
            raise StudioError(f"{Path(file).name}: {exc}") from None

    def _record_more(self, address: str, report: dict, file: Path, clips: dict, before: dict) -> dict:
        """What the model's record says of its bones and animations (rusemod.animmodel's record), the unit's own clips
        and rows written for a model on bones of its own; `before`: the record as it was (a model brought in before
        this one), whose animations go when the new model has none of its own. Its notes go into `report`."""
        from rusemod import animmodel, baf
        from rusemod.anim import AnimError
        from rusemod.modelin import OWN_SKELETON
        from .api import StudioError
        from rusemod import anim
        target = self._own_model_file(address)
        unit, mod = target.stem, self._mod_dir()
        was_own = before.get("skeleton") == "own"
        previous = before.get("animations") if was_own else None
        if not report.get(OWN_SKELETON):
            if previous:   # (the clips were made on the old model's bones: they go with it)
                with self._saving:
                    try:
                        anim.drop_animations(mod, unit)
                    except (AnimError, OSError) as exc:
                        raise StudioError(f"The animations of the model it had can't be taken out: {exc}") from None
            return {"skeleton": "soldier", "animations": []} if report.get("rigged") else {}
        try:
            record = animmodel.record_of(target)
            from rusemod.rig import read_rig
            rig = read_rig(file)
            said, halves = animmodel.file_says(animmodel.file_document(file), [a.name for a in rig.animations])
        except (animmodel.AnimModelError, ValueError, OSError) as exc:
            raise StudioError(f"{Path(file).name}: {exc}") from None
        if list(clips) != animmodel.clip_names(rig):   # (one reading of the file, two answers: never expected)
            raise StudioError(f"{Path(file).name}: its animations came out two different ways when read: please report "
                              f"this.")
        # (item 5's merge: the model's animations go into Part 2's table, units.toml's [unit.<unit>.animation],
        # where the action table on the page picks what each action plays and the build plays the nearest for the
        # rest, rusemod.animactions: one rule for the page and the build. What the file itself says an animation
        # plays, its extras, becomes that action's pick.)
        with self._saving:
            try:
                files = anim.set_animations(mod, unit, clips)
                for name, listed in zip(list(clips), said):
                    for listing in listed or []:   # (a listing's name, t_course: the table's action is course)
                        action = listing[2:] if listing[:2] in ("t_", "b_") else listing
                        try:
                            anim.set_pick(mod, unit, action, name)
                        except AnimError:   # (an action name the table doesn't know: the file's word is noted)
                            report.setdefault("notes", []).append(
                                f"{name}: the file says it plays {listing}, which isn't one of the unit's actions")
            except (AnimError, OSError) as exc:
                raise StudioError(f"{Path(file).name}: its animations can't be kept: {exc}") from None
        animations = []
        for name, data in clips.items():
            c = baf.parse(data)
            animations.append({"name": name, "frames": c.frames, "seconds": round(c.duration, 4), "file": files[name]})
        names = baf.skeleton(record)["names"]
        out = {"skeleton": "own", "bones": names, "animations": animations}
        split = before.get("split") if was_own and isinstance(before.get("split"), str) else None
        if split is None or split.lower() not in names:   # (a choice made before, kept while the bone is there)
            split = animmodel.split_of(record, halves) if halves else None
        if split:
            out["split"] = split.lower()
        return out

    def _model_actions(self, address: str, report: dict) -> list:
        """Every action the figures that wear the model list (the game's unit the new one copies, read in the game's
        index: rusemod.animmodel.unit_figures), each once, in the game's order."""
        from rusemod import animmodel
        from rusemod.unitmodel import model_key
        from .edits import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, _unit = self._resolve(edits, address)
        wears = {model_key(m) for m in [report.get("like"), *(report.get("also") or [])] if m}
        ix = self._open()
        try:
            figures = animmodel.unit_figures(ix.db, real.split(":", 1)[0])
        finally:
            ix.close()
        out: list = []
        for _figure, model, actions in figures:
            if model_key(model) in wears:
                out += [a for a in actions if a not in out]
        return out

    def _animations_out(self, address: str, record: Path) -> list:
        """Take out the animations a model on bones of its own brought in (its record's), with the model: the actions
        that played one go back to what they played before (rusemod.animmodel.drop_animations)."""
        from rusemod import animmodel
        from rusemod.anim import AnimError
        from .api import StudioError
        try:
            data = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {}
        except (OSError, ValueError):
            data = {}
        if data.get("skeleton") != "own" or not data.get("animations"):
            return []
        try:
            from rusemod import anim
            anim.drop_animations(self._mod_dir(), record.stem)   # (Part 2's table: the merge's one store)
            return [a.get("name") for a in data["animations"] if isinstance(a, dict)]
        except (AnimError, OSError) as exc:
            raise StudioError(f"The animations of the model it had can't be taken out: {exc}") from None

    def model_animations(self, address: str) -> dict:
        """The unit page's Its animations, for a new unit whose own model is on bones of its own: {"own": whether it
        is, "bones": how many, "animations": [{"name", "seconds", "frames", "actions": [the actions it plays]}],
        "actions": how many actions the figures wearing it list, "empty": [those no animation plays], "split": the
        bone its two halves meet at, or None}. {"own": False} for any other unit."""
        target = self._own_model_file(address)
        if target is None or not target.is_file():
            return {"own": False}
        try:
            data = json.loads(target.with_suffix(".json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"own": False}
        if not isinstance(data, dict) or data.get("skeleton") != "own":
            return {"own": False}
        # (item 5's merge: which animation each action plays is Part 2's table and rule, read live, so this box and
        # the action table never disagree; "empty": the actions nothing is named or picked for, playing the nearest)
        try:
            table = self.unit_actions(address)
        except Exception:   # (the table can't be read: the box still says what came in)
            table = {"own": False}
        plays: dict = {}
        empty = []
        for row in table.get("rows") or [] if table.get("own") else []:
            for name in set((row.get("plays") or {}).values()):
                plays.setdefault(name, []).append(row.get("action"))
            if row.get("how") == "nearest":
                empty.append(row.get("action"))
        rows = []
        for a in data.get("animations") or []:
            rows.append({"name": a.get("name"), "seconds": a.get("seconds"), "frames": a.get("frames"),
                         "actions": plays.get(a.get("name"), [])})
        return {"own": True, "bones": len(data.get("bones") or []), "animations": rows,
                "actions": len(table.get("rows") or []) if table.get("own") else 0, "empty": empty,
                "split": data.get("split")}
