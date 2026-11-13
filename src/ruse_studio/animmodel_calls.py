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
modder's is told from the file's own. Whatever of his can't be kept (the model's bones aren't the ones he changed it
on any more; a new model brought in, Import model again, which brings its own animations as before) is named in the
fit's report (NOT_KEPT), and the page says it in words.

A record written before FROM_FILE (by this branch's Studio before 2026-11-12: no release has models on bones of their
own) has no fingerprints. What its last fit took in is then read again (_last_fit): what the file it was made from
gives now, the way a fit takes it in, and the animations the model's own file in the mod carries (a fit writes them
into it; RUSE Decoy never changes that file), so Import model again and Bring back the model name a change made in
RUSE Decoy over such a record too (the resize recheck, round 1). A clip file or model file of the mod that can't be
read is never a reason to stop a fit: the file's animation takes its place and is named, as before the fingerprints
(the same recheck: a damaged clip file stopped Resize, Move and every unit at once)."""
from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path

FROM_FILE = "from_file"   # the model's record: what its last fit took in from its file ({"animations", "plays"})
NOT_KEPT = "not_kept"     # a fit's report: what of the modder's own it couldn't keep ({"animations", "picks"})
UNREAD = (ValueError, IndexError, struct.error)   # a clip's bytes rusemod.baf can't read (its ClipError a ValueError)


def write_record(path: Path, data: dict) -> None:
    """A model's record (files/models/<unit>.json) written whole or not at all: beside itself first, then put in its
    place, so a write that stops part way (the disk full, the Studio closed) leaves the record as it was, never one cut
    short that no fit can read (the resize recheck, round 2: written in place, it was). The same text as before."""
    path = Path(path)
    part = path.with_name(path.name + ".part")
    try:
        part.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(part, path)
    except BaseException:
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _sha(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


def _close(x: float, y: float) -> bool:
    return abs(x - y) <= 1e-5 * max(1.0, abs(x), abs(y))


def _near(a: bytes, b: bytes) -> bool:
    """Whether clip `a` plays as clip `b` does within what a clip's numbers keep through the model's own file (a fit
    writes its clips into it as animations, rusemod.modelin.write_glb, and rusemod.unitmodel.own_clips reads them
    back): the same frames, length, skeleton, keys and key times, every move and size within a float's last places and
    every turn within two steps of its packing. Measured on the Horse Squad, 2026-11-12: 24 of its 25 came back byte
    for byte, hr_b_mort_balle with moves off by 7.7e-6 at most. RUSE Decoy takes a bone in as changed only past
    rusemod.rig.TOL_BACK_* (a move of 0.05 as it shows in the model, a turn of about 0.03 degrees), far coarser. Two
    clips that can't both be read aren't near."""
    from rusemod import baf
    try:
        ca, cb = baf.parse(a), baf.parse(b)
    except UNREAD:
        return False
    if (ca.frames, ca.bones, ca.skeleton) != (cb.frames, cb.bones, cb.skeleton) or not _close(ca.duration, cb.duration):
        return False
    for ta, tb in zip(ca.tracks, cb.tracks):
        for ka, kb in ((ta.T, tb.T), (ta.S, tb.S)):
            if len(ka) != len(kb) or any(p[0] != q[0] or not all(_close(x, y) for x, y in zip(p[1:], q[1:]))
                                         for p, q in zip(ka, kb)):
                return False
        if len(ta.R) != len(tb.R) or any(
                p[0] != q[0] or max(abs(x - y) for x, y in zip(baf.unpack_quat(p[1:]), baf.unpack_quat(q[1:])))
                > 2 * baf.SCALE for p, q in zip(ta.R, tb.R)):
            return False
    return True


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
                     carried: dict | None = None, lost: bool = False) -> dict:
        """What the model's record says of its bones and animations (rusemod.animmodel's record), the unit's own clips
        and rows written for a model on bones of its own; `before`: the record as it was (a model brought in before
        this one), whose animations go when the new model has none of its own. Its notes go into `report`.

        `refit` (Resize, Move: the model fitted again from the file it was made from): each of its animations the
        modder changed since the last fit stays as the mod has it while it's on the model's bones (the skeleton its
        clip was made on, which every clip carries, is the model's now), one the file hasn't got any more too, and each
        action's pick made on the page stays (the file's own word on an action is set again only where the pick is
        still the one that word set). Every other animation and word is the file's again, as before. A new model
        (Import model, Bring back the model) brings its own animations and words, in place of the modder's changes, as
        before. Either way, what of his couldn't be kept goes into the report's NOT_KEPT (the page says it), and the
        record's FROM_FILE says what this fit took in (see the module's note). `carried`: what the unit's own model
        file carried before this fit wrote it anew (_carried_before), for an animation the record has no fingerprint
        of (_last_fit).

        `lost` (StudioApi._fit_model): the unit's model file is there but no record says what it is (one that can't be
        read, cut short, gone, or holding a split alone). `carried` is then every animation that file gives (_file_clips),
        and it alone tells the modder's changes from what the last fit took in: a model on bones of its own before
        this one when it gives any, its changed animations named when the new model takes their place; when it gives
        none, every animation the new model's take the place of is named (nothing tells them apart: said, never put back
        without a word, the resize recheck, round 2)."""
        from rusemod import animmodel, baf
        from rusemod.anim import AnimError
        from rusemod.modelin import OWN_SKELETON
        from .api import StudioError
        from rusemod import anim
        target = self._own_model_file(address)
        unit, mod = target.stem, self._mod_dir()
        was_own = before.get("skeleton") == "own"
        previous = before.get("animations") if was_own else (list(carried) if lost and carried else None)
        last = before.get(FROM_FILE) if was_own and isinstance(before.get(FROM_FILE), dict) else {}
        last_clips = last.get("animations") if isinstance(last.get("animations"), dict) else {}
        last_plays = last.get("plays") if isinstance(last.get("plays"), dict) else None

        # (what the last fit took in, read again only for an animation with no fingerprint: a record from before them.
        # With no model on bones of its own before this one, the animations the unit has came along with a copy of a
        # unit, ruse_studio.actions, not from a fit of a model of its own: nothing to tell them by, as before)
        last_fit = (lambda: self._last_fit(before, file, clips, carried)) if was_own or lost else None
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
                gone = self._changed_since(mine, last_clips, last_fit)
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
        # (item 5's merge: the model's animations go into Part 2's table, units.toml's [unit.<unit>.animation],
        # where the action table on the page picks what each action plays and the build plays the nearest for the
        # rest, rusemod.animactions: one rule for the page and the build. What the file itself says an animation
        # plays, its extras, becomes that action's pick.)
        with self._saving:
            mine, picks = self._own_now(mod, unit)
            changed = self._changed_since(mine, last_clips, last_fit)
            keep = {}
            for name in changed if refit else []:
                try:
                    c = baf.parse(mine[name])
                    baf.check(c)
                except UNREAD:   # (a clip file that isn't one any more: the file's takes its place, said)
                    continue
                if c.skeleton != record:   # (made on other bones than the model's now, the same bone names with
                    continue               # another rest too: the file's takes its place, said)
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
    def _changed_since(mine: dict, taken: dict, last_fit) -> list:
        """Of the model's animations as the mod has them (`mine`), in its order, those the modder changed since the
        last fit took them in from its file: one with a fingerprint (`taken`, the record's FROM_FILE) when it isn't
        that any more; one with none (a record from before them, an animation added by hand) when it is none of what
        `last_fit()` reads that fit took in (_last_fit: exactly, or near where `near`). Nothing read tells it: his,
        named rather than dropped without a word. `last_fit` None (no model on bones of its own before this one): only
        the fingerprints tell."""
        out, told = [], None
        for name, data in mine.items():
            known = taken.get(name)
            if isinstance(known, str):
                if _sha(data) != known:
                    out.append(name)
                continue
            if last_fit is None:
                continue
            if told is None:
                told = last_fit()
            if not any(name in seen and (_near(data, seen[name]) if near else data == seen[name])
                       for seen, near in told):
                out.append(name)
        return out

    def _last_fit(self, before: dict, file: Path, clips: dict, carried: dict | None) -> list:
        """What the model's last fit took in, read again for an animation its record has no fingerprint of:
        [({name: the clip's bytes}, whether only near: _near)], from the file it was made from (the record's "from":
        `clips`, what this fit takes in, when that's the file fitted now, else what it gives now, the way a fit takes
        it in) and from what the model's own file carried before this fit (`carried`, _carried_before: a fit writes
        its clips into it, near as they were). [] when neither can be read."""
        out = []
        old = before.get("from")
        if isinstance(old, str) and old:
            if self._same_file(old, file):
                out.append((clips, False))
            else:
                got = self._file_clips(Path(old))
                if got:
                    out.append((got, False))
        if carried:
            out.append((carried, True))
        return out

    def _carried_before(self, target: Path, before: dict) -> dict | None:
        """The animations the unit's own model file carries now (a fit writes its clips into it: rusemod.modelin.
        write_glb; RUSE Decoy never changes that file), read before a fit writes it anew, when one of the unit's
        animations has no fingerprint in the model's record `before` (a record from before them: _last_fit); None when
        none needs it, {} when the file can't be read."""
        from rusemod import anim
        if not isinstance(before, dict) or before.get("skeleton") != "own" or not Path(target).is_file():
            return None
        try:
            names = list(anim.own_animations(self._mod_dir(), Path(target).stem)["animations"])
        except Exception:  # noqa: BLE001 - a units.toml that can't be read, however: the fit's own reading and
            return None    # writing of it say why (_own_now, rusemod.anim.set_animations), as before the fingerprints
        last = before.get(FROM_FILE)
        taken = last.get("animations") if isinstance(last, dict) else None
        if not names or (isinstance(taken, dict) and all(isinstance(taken.get(n), str) for n in names)):
            return None
        return self._file_clips(Path(target))

    @staticmethod
    def _file_clips(path: Path) -> dict:
        """The animations a model file on bones of its own gives, the way a fit takes them in (rusemod.unitmodel.
        _import_own_bones: its rig, its record, own_clips), {name: the clip's bytes}; {} when it can't be read."""
        from rusemod import rig, unitmodel
        try:
            r = rig.read_rig(Path(path))
            record, _notes = unitmodel.own_skeleton(r)
            made, _notes = unitmodel.own_clips(r, record)
        except Exception:  # noqa: BLE001 - a file that can't be read, however, tells nothing: _changed_since then
            return {}      # names the animation it would have told of (never dropped without a word)
        return made

    @staticmethod
    def _same_file(a, b) -> bool:
        try:
            return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))
        except (TypeError, ValueError, OSError):
            return False

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
