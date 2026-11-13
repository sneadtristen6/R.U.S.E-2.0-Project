"""A model on bones of its own and its animations in the Studio (StudioApi's AnimModelCalls; the owner's list, item 5,
part 1: a horse that runs and stops, a rifleman on it who shoots, any creature, brought in by the modder; the
engine's side is rusemod.animmodel).

Import model, and Bring back the model after Blender (ruse_studio.modelblender), take a .glb whose points lean on bones
the unit's own model hasn't got as a model on bones of its own (_own_bones_fit): its skeleton and every animation come
in with it (rusemod.unitmodel.import_model's own_bones), each animation is kept as a clip of the unit's own and each
action of the unit plays the animation named for it (rusemod.animmodel.keep_animations), and the model's record
(files/models/<the unit's name>.json) says what came in (_record_more). A file on the game soldier's own bones goes
on as before (item 4's way). Taking the model out takes its animations out too (_animations_out). The unit's page
shows what came in: model_animations.

Fitted again from the same file (Resize, Move, every plane or ground unit at once: _record_more's `refit`), the model
keeps what the modder made of it since: an animation changed in RUSE Decoy (its Change its animations in Blender writes
the change in this same store, by name: ruse_studio.decoyblender) and the animation picked for an action on the page.
Before 2026-11-12 the fit took every animation in again from the file and set the file's own word on an action again,
so the change went back without a word (the silent-loss review's F2). What the last fit took in is kept in the
model's record (FROM_FILE: each animation's fingerprint, the file's own word on each action), so a change of the
modder's is told from the file's own. Whatever of his can't be kept (the file's bones aren't the ones he changed them
on any more; a new model brought in, Import model again, which brings its own animations as before) is named in the
fit's report (NOT_KEPT), and the page says it in words."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FROM_FILE = "from_file"   # the model's record: what its last fit took in from its file ({"animations", "plays"})
NOT_KEPT = "not_kept"     # a fit's report: what of the modder's own it couldn't keep ({"animations", "picks"})


def _sha(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


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

    def _record_more(self, address: str, report: dict, file: Path, clips: dict, before: dict, refit: bool = False,
                     bones_before: bytes | None = None) -> dict:
        """What the model's record says of its bones and animations (rusemod.animmodel's record), the unit's own clips
        and rows written for a model on bones of its own; `before`: the record as it was (a model brought in before
        this one), whose animations go when the new model has none of its own. Its notes go into `report`.

        `refit` (Resize, Move: the model fitted again from the file it was made from; `bones_before`: the skeleton
        record it was on, _bones_now): each of its animations the modder changed since the last fit stays as the mod
        has it while its bones are the same, one the file hasn't got any more too, and each action's pick made on the
        page stays (the file's own word on an action is set again only where the pick is still the one that word
        set). Every other animation and word is the file's again, as before. A new model (Import model, Bring back the
        model) brings its own animations and words, in place of the modder's changes, as before. Either way, what of
        his couldn't be kept goes into the report's NOT_KEPT (the page says it), and the record's FROM_FILE says what
        this fit took in (see the module's note)."""
        from rusemod import animmodel, baf
        from rusemod.anim import AnimError
        from rusemod.modelin import OWN_SKELETON
        from .api import StudioError
        from rusemod import anim
        target = self._own_model_file(address)
        unit, mod = target.stem, self._mod_dir()
        was_own = before.get("skeleton") == "own"
        previous = before.get("animations") if was_own else None
        last = before.get(FROM_FILE) if was_own and isinstance(before.get(FROM_FILE), dict) else {}
        last_clips = last.get("animations") if isinstance(last.get("animations"), dict) else {}
        last_plays = last.get("plays") if isinstance(last.get("plays"), dict) else None
        if not report.get(OWN_SKELETON):
            if previous:   # (the clips were made on the old model's bones: they go with it)
                with self._saving:
                    mine, _picks = self._own_now(mod, unit)
                    try:
                        anim.drop_animations(mod, unit)
                    except (AnimError, OSError) as exc:
                        raise StudioError(f"The animations of the model it had can't be taken out: {exc}") from None
                # (the modder's changes of them go too: named, never dropped quietly; their picks go with the whole
                # action table, which a model on the game soldier's bones hasn't got)
                gone = self._changed_since(mine, last_clips, {}, False)
                if gone:
                    report[NOT_KEPT] = {"animations": gone, "picks": []}
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
        names = baf.skeleton(record)["names"]
        # (a fit again from the same file: on the bones the modder's changes were made on, they still fit)
        same_bones = bones_before == record if bones_before is not None else \
            was_own and [str(b) for b in before.get("bones") or []] == list(names)
        # (item 5's merge: the model's animations go into Part 2's table, units.toml's [unit.<unit>.animation],
        # where the action table on the page picks what each action plays and the build plays the nearest for the
        # rest, rusemod.animactions: one rule for the page and the build. What the file itself says an animation
        # plays, its extras, becomes that action's pick.)
        with self._saving:
            mine, picks = self._own_now(mod, unit)
            changed = self._changed_since(mine, last_clips, clips, refit)
            keep = {}
            for name in changed if refit and same_bones else []:
                try:
                    baf.check(baf.parse(mine[name]))
                except baf.ClipError:   # (a clip file that isn't one any more: the file's takes its place, said)
                    continue
                keep[name] = mine[name]
            kept = {name: keep.get(name, data) for name, data in clips.items()}
            kept.update({name: data for name, data in keep.items() if name not in kept})
            words: dict = {}   # (the file's own word on each action: the animation it says plays it)
            try:
                files = anim.set_animations(mod, unit, kept)
                for name, listed in zip(list(clips), said):
                    for listing in listed or []:
                        if listing[:2] in ("t_", "b_"):
                            # (a half's listing, t_course: a pick is the whole action's, both halves, so it isn't
                            # made from it; Part 2's rule plays each half by the half mark in the animation's own
                            # name, hr_t_.../hr_b_..., as the 11-09 copy did. Made into a pick, a bottom half played
                            # a top animation: 115 of the Horse Squad's 248 listings, the merge's dry run 11-11)
                            continue
                        action = listing
                        if not anim._ACTION.match(action):   # (an action name the table doesn't know: noted)
                            report.setdefault("notes", []).append(
                                f"{name}: the file says it plays {listing}, which isn't one of the unit's actions")
                            continue
                        words[action] = name
                        if refit and (last_plays is None or picks.get(action) != last_plays.get(action)):
                            continue   # (fitted again: the pick made on the page stays, a record's from before too)
                        try:
                            anim.set_pick(mod, unit, action, name)
                        except AnimError:   # (as the name check above: the file's word is noted)
                            report.setdefault("notes", []).append(
                                f"{name}: the file says it plays {listing}, which isn't one of the unit's actions")
                after = anim.own_animations(mod, unit)["plays"]
            except (AnimError, OSError) as exc:
                raise StudioError(f"{Path(file).name}: its animations can't be kept: {exc}") from None
        # what of the modder's own this fit couldn't keep: his animations' changes, and the picks made on the page
        # (with a record from before FROM_FILE, every pick the action table showed)
        lost = [name for name in changed if kept.get(name) != mine[name]]
        chosen = set(picks) if last_plays is None else \
            {a for a in set(picks) | set(last_plays) if picks.get(a) != last_plays.get(a)}
        moved = sorted(a for a in chosen if after.get(a) != picks.get(a))
        if lost or moved:
            report[NOT_KEPT] = {"animations": lost, "picks": moved}
        animations = []
        for name, data in kept.items():
            c = baf.parse(data)
            animations.append({"name": name, "frames": c.frames, "seconds": round(c.duration, 4), "file": files[name]})
        out = {"skeleton": "own", "bones": names, "animations": animations,
               # (what this fit took in from the file: a fingerprint of each animation, one the modder's kept that the
               # file hasn't got any more keeping its own, and the file's word on each action)
               FROM_FILE: {"animations": {**{name: _sha(data) for name, data in clips.items()},
                                          **{name: last_clips[name] for name in keep
                                             if name not in clips and isinstance(last_clips.get(name), str)}},
                           "plays": words}}
        split = before.get("split") if was_own and isinstance(before.get("split"), str) else None
        if split is None or split.lower() not in names:   # (a choice made before, kept while the bone is there)
            split = animmodel.split_of(record, halves) if halves else None
        if split:
            out["split"] = split.lower()
        return out

    @staticmethod
    def _own_now(mod: Path, unit: str) -> tuple[dict, dict]:
        """The unit's model's own animations as the mod has them now ({name: the clip's bytes}; one whose file isn't
        there is left out) and the animation each action is picked to play ({action: name})."""
        from rusemod import anim
        try:
            own = anim.own_animations(mod, unit)
        except anim.AnimError:   # (a units.toml that can't be read: the fit's own writing of it says why)
            return {}, {}
        mine = {}
        for name, rel in own["animations"].items():
            try:
                mine[name] = anim._own_file(Path(mod) / anim.OWN / unit, rel, f"{unit}'s {name}").read_bytes()
            except (anim.AnimError, OSError):
                continue
        return mine, dict(own["plays"])

    @staticmethod
    def _changed_since(mine: dict, taken: dict, clips: dict, refit: bool) -> list:
        """Of the model's animations as the mod has them (`mine`), those changed since the last fit took them in from
        its file (`taken`: their fingerprints, the record's FROM_FILE). An animation with none (a record from before
        them) counts as changed on a fit again from the same file (`refit`) when it isn't what the file gives
        (`clips`); on a new model, nothing tells, so it doesn't."""
        out = []
        for name, data in mine.items():
            known = taken.get(name)
            if isinstance(known, str):
                if _sha(data) != known:
                    out.append(name)
            elif refit and name in clips and data != clips[name]:
                out.append(name)
        return out

    @staticmethod
    def _bones_now(target: Path) -> bytes | None:
        """The skeleton record the unit's own model is on now, when its record says it's on bones of its own (read
        before a fit again writes the model anew: _record_more keeps the modder's changes on the same bones); None
        otherwise, or when it can't be read (the record's bone names tell then)."""
        from rusemod import animmodel
        try:
            record = json.loads(Path(target).with_suffix(".json").read_text(encoding="utf-8"))
            if not isinstance(record, dict) or record.get("skeleton") != "own" or not Path(target).is_file():
                return None
            return animmodel.record_of(target)
        except (OSError, ValueError):   # (animmodel.AnimModelError is a ValueError)
            return None

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
