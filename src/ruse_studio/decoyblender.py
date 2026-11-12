"""RUSE Decoy's Change its animations in Blender: one unit's animations out to Blender and back, the changed ones that
unit's own (StudioApi's DecoyBlenderCalls).

The owner, 2026-11-10, his answer to question 8: "The only way you should change animation is in Ruse Decoy, you go
and change the animation for your new unit."; his plan of 2026-11-11 ("Yes, join them"), step 2: Edit in Blender inside
Decoy; 2026-11-12: "work until all things not done are done and work in studio". So the door is RUSE Decoy's page for
one unit (a unit's page opens it there), never the model's Change it in Blender, which stays the model's alone.

The engine is item 5 Part 4's (feat/anim5-blender, agent 5-4, checked offline: every clip of the US rifleman and of the
Horse Squad back byte for byte when untouched, one bone changed when one was): ruse_studio.animblender says which clips
the unit plays as the mod makes them and names them in the modder's words; rusemod.gltf.export(clips=) /
rusemod.animglb.own_glb lay the model and those clips out for Blender on the real bones; rusemod.blender_model opens
them at the game's 30 frames a second, each an action in the Action Editor; Send writes every action back;
rusemod.rig.clips_back turns each back into a game clip, every bone the modder didn't change byte for byte the clip that
went out. A changed one becomes the unit's own clip for every action of every figure that played it
(rusemod.anim.add_unit_clip: files/anim/units.toml, files/anim/own/<unit>/): RUSE Decoy shows it under Only this unit,
every other unit keeps the game's. One made in Blender (no clip went out under its name) is played by no action yet and
said; one that went out and didn't come back stays as it was and is said. The model in the file is only what the
animations play on: what is done to it isn't taken in (the model's own doors are Import a model and Change the squad in
Blender).

A model on bones of its own (a horse, any creature: Import model kept its record in its file) plays its model's own
animations, which Import model put in the unit's files/anim/units.toml [unit.<name>.animation] and its actions play by
name or the nearest (rusemod.animactions); no game clip is on its bones. Those go out under their own names, as the mod
has them (before it has any, the ones its file carries), and a changed one comes back in its place by name
(rusemod.anim.set_animations, Import model's own store), so whatever played it plays it changed and every pick stays.
Found 2026-11-12 checking the join: sent with no action, such a change was said to be the unit's own and written
nowhere. When the model or the animation changed after it went out (a model imported again while Blender was open),
nothing is taken in, and that is said.

The work folder: <mod>/blender/<unit>/animations/ (never packed): what went out (animblender's animations.json and
clips/), the file Blender opened, the file it sends (send.glb), the words, and state.json ("brought": the fingerprint of
the last sending brought back). Each opening starts from what the mod has now; a sending never brought back is kept
aside first (sent-not-brought-<time>/, nothing lost)."""
from __future__ import annotations

import hashlib
import json
import os
import struct
import time
from pathlib import Path

WORK = "animations"      # <mod>/blender/<unit>/animations/
SEND = "send.glb"        # what Blender sends
STATE = "state.json"
SEND_WAIT = 60.0         # seconds Bring my changes back waits for an open Blender to send


def _sha(path: Path) -> str | None:
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _read(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(part, path)


class DecoyBlenderCalls:
    # --- where, and whether ---
    def _anim_work(self, address: str) -> Path | None:
        """The unit's animation work folder, <mod>/blender/<its name>/animations/ (made or not); None for a unit that
        isn't a new unit of this mod."""
        from .modelblender import WORK as BLENDER
        own = self._own_model_file(address)
        mod = self._mod_dir()
        return mod / BLENDER / own.stem / WORK if own is not None and mod is not None else None

    def _anim_open(self, work: Path | None) -> bool:
        proc = self._blenders.get(str(work)) if work is not None else None
        return proc is not None and proc.poll() is None

    def decoy_blender_state(self, address: str, lang: str = "us") -> dict:
        """What RUSE Decoy's page for one unit shows of its Blender door: {"can": whether its animations can go out
        (a new unit of this mod), "why_not": a sentence when they can't, "open": its Blender is open now, "waiting": a
        sending not brought back yet, "work": the work folder (None for a game unit)}."""
        from .api import words
        w = words(lang)
        work = self._anim_work(address)
        if work is None:
            return {"can": False, "why_not": w["decoy_blender_why_game"], "open": False, "waiting": False,
                    "work": None}
        send = work / SEND
        state = _read(work / STATE)
        waiting = send.is_file() and _sha(send) != state.get("brought") and state.get("session") is not None
        return {"can": True, "why_not": None, "open": self._anim_open(work), "waiting": bool(waiting),
                "work": str(work)}

    # --- the unit's animations (item 5 Part 4's, kept from feat/anim5-blender's modelblender) ---
    def _own_bones_model(self, address: str) -> tuple[bytes | None, bytes | None]:
        """(the unit's own model file's bytes, its skeleton record) when its model is on bones of its own (its file
        carries its record: rusemod.modelin.write_glb), else (None, None)."""
        import base64
        from rusemod.modelin import glb_document
        from rusemod.rig import SKELETON_EXTRA
        own = self._own_model_file(address)
        if own is None or not own.is_file():
            return None, None
        try:
            raw = own.read_bytes()
            doc, _binary = glb_document(raw)
        except (OSError, ValueError, struct.error):     # (not a .glb the Studio can read: no bones of its own)
            return None, None
        for skin in doc.get("skins") or []:
            given = (skin.get("extras") or {}).get(SKELETON_EXTRA)
            if given:
                return raw, base64.b64decode(given)
        return None, None

    def _unit_figures(self, address: str) -> list:
        """rusemod.animlist.unit_figures of the unit (a new unit's: those of the unit it copies); [] without the
        game's index."""
        from rusemod import animlist
        from .edits import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, _unit = self._resolve(edits, address)
        try:
            ix = self._open()
        except FileNotFoundError:  # (no game index yet: nothing known of it)
            return []
        try:
            return animlist.unit_figures(ix.db, real.split(":", 1)[0])
        finally:
            ix.close()

    def _unit_plays(self, address: str, lib, record: bytes, w: dict, own_raw: bytes | None = None) -> list:
        """ruse_studio.animblender.unit_plays for the unit on a model of `record`'s bones. A model on bones of its own
        (`own_raw`, its file): its model's own animations first, under their own names (the modder's, which its record
        knows them by), each row's "model_animation" its name in units.toml [unit.<name>.animation] (as the mod has
        them: _model_animations), then any clip an action of its own plays on these bones; an action row naming one of
        the model's animation files goes out once, as the model's."""
        from rusemod import anim, animlist, baf
        from . import animblender
        from .api import StudioError
        own = self._own_model_file(address)
        names = baf.skeleton(record)["names"]
        try:
            rows = animblender.unit_plays(self._unit_figures(address), names, animlist.clip_reader(lib.arc),
                                          self._mod_dir(), animblender.unit_name(own), lib.skeleton, w,
                                          labelled=own_raw is None)
        except (anim.AnimError, baf.ClipError) as exc:   # (a clip file of the mod's that isn't one: says which)
            raise StudioError(str(exc)) from None
        if own_raw is None:
            return rows
        model = self._model_animations(address, own_raw, record)
        files = {r["own"] for r in model if r["own"]}
        rows = [r for r in rows if r["own"] is None or r["own"] not in files]
        taken = {r["name"].lower() for r in model}
        for r in rows:      # (an action's own clip named like one of the model's animations)
            name, k = r["name"], 2
            while name.lower() in taken:
                name, k = f"{r['name']} {k}", k + 1
            r["name"] = name
            taken.add(name.lower())
        return model + rows

    def _model_animations(self, address: str, own_raw: bytes, record: bytes) -> list:
        """The model's own animations as unit_plays' rows, each with "model_animation" (its name): as the mod has them
        (files/anim/units.toml [unit.<name>.animation], the files in files/anim/own/<name>/), or, before it has any,
        the ones the model's file carries (rusemod.unitmodel.own_clips, as Import model would take them in)."""
        from rusemod import anim, rig, unitmodel
        from rusemod.modelin import ModelError, glb_document
        from . import animblender
        from .api import StudioError
        mod = self._mod_dir()
        unit = animblender.unit_name(self._own_model_file(address))
        try:
            mine = anim.own_animations(mod, unit)["animations"] if mod is not None else {}
            if mine:
                return [{"name": n, "clip": anim._own_file(Path(mod) / anim.OWN / unit, f, f"{unit}'s {n}").read_bytes(),
                         "member": None, "own": f, "actions": {}, "model_animation": n} for n, f in mine.items()]
        except (anim.AnimError, OSError) as exc:     # (a file units.toml names that isn't there: says which)
            raise StudioError(str(exc)) from None
        try:
            carried, _notes = unitmodel.own_clips(rig.rig_of(*glb_document(own_raw)), record)
        except (ModelError, ValueError):
            return []
        return [{"name": n, "clip": c, "member": None, "own": None, "actions": {}, "model_animation": n}
                for n, c in carried.items()]

    # --- out to Blender ---
    def decoy_blender(self, address: str, lang: str = "us") -> dict:
        """Change its animations in Blender: Blender opens with the unit's model and every animation the unit plays as
        the mod makes them (see the module's note). Refused, in words: a unit that isn't a new unit of this mod, Blender
        not found, its Blender open already, a unit playing no animation on its model's bones. Returns
        decoy_blender_state's answer with "opened": how many animations, "file": what Blender opened, "set_aside": a
        sending never brought back that was kept aside, and "message"."""
        from rusemod import animglb, gltf, models
        from rusemod.blender import open_model_to_change
        from . import animblender
        from .api import StudioError, words
        from .modelblender import HEAVY
        w = words(lang)
        work = self._anim_work(address)
        if work is None:
            raise StudioError(w["decoy_blender_why_game"])
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        if self._anim_open(work):
            raise StudioError("This unit's animations are open in Blender already: change them there, then bring your "
                              "changes back.")
        work.mkdir(parents=True, exist_ok=True)
        state = _read(work / STATE)
        send = work / SEND
        set_aside = None
        if send.is_file() and _sha(send) != state.get("brought"):
            set_aside = work / time.strftime("sent-not-brought-%Y%m%d-%H%M%S")
            set_aside.mkdir()
            os.replace(send, set_aside / SEND)
        own_raw, own_record = self._own_bones_model(address)
        lib = models.Library(self._game())
        try:
            if own_raw is not None:     # a model on bones of its own, with its own animations
                record, model = own_record, "own"
                rows = self._unit_plays(address, lib, own_record, w, own_raw)
                if not rows:
                    raise StudioError("This unit plays no animation the Studio can open in Blender.")
                try:
                    data, _summary = animglb.own_glb(own_raw, animblender.as_clips(rows))
                except animglb.AnimGlbError as exc:
                    raise StudioError(str(exc)) from None
                start = work / "animations.glb"
                start.write_bytes(data)
            else:
                found = [m for m in self._look_models(address)[0] if "_dest" not in m.lower()]
                if not found:
                    raise StudioError("This unit has no 3D model the Studio can open.")
                model = next((m for m in found if not HEAVY.search(m.rsplit("\\", 1)[-1])), found[0])
                record = lib.skeleton(model) if hasattr(lib, "skeleton") else None
                rows = self._unit_plays(address, lib, record, w) if record is not None else []
                if not rows:
                    raise StudioError("This unit plays no animation the Studio can open in Blender.")
                try:
                    start = Path(gltf.export(lib, [model], work, rest_bones=True,
                                             clips={model: animblender.as_clips(rows)})[0]["file"])
                except animglb.AnimGlbError as exc:
                    raise StudioError(str(exc)) from None
        finally:
            lib.close()
        animblender.write_sent(work, model, record, rows)
        _write(work / "words.json", {"send": w["blender_model_send"], "sent": w["decoy_blender_sent"],
                                     "hint": [w["blender_anim_hint1"], w["blender_anim_hint2"]],
                                     "hint_animations": []})
        state.update({"session": hashlib.sha256(f"{time.time()}|{work}".encode()).hexdigest()[:16],
                      "file": str(start)})
        _write(work / STATE, state)
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        message = w["decoy_blender_opened"].format(n=len(rows))
        if set_aside is not None:
            message += " " + w["blender_squad_set_aside"].format(folder=str(set_aside))
        return {**self.decoy_blender_state(address, lang), "opened": len(rows), "file": str(start),
                "set_aside": str(set_aside) if set_aside is not None else None, "message": message}

    # --- and back ---
    def decoy_blender_back(self, address: str, lang: str = "us") -> dict:
        """Bring my changes back: the open Blender is asked to send (a closed one's last sending is used); each
        animation that came back changed becomes the unit's own clip for every action of every figure that played it,
        or, one of its model's own animations, takes that animation's place by name (see the module's note). Refused,
        in words, nothing written: nothing sent from this Blender yet, nothing went out from it, a file not on the
        bones its animations went out on, the model or one of its changed animations not as it went out. Returns
        decoy_blender_state's answer with "changed", "same" (how many came back as they went), "new", "gone" (names),
        "written" (how many changed ones were kept) and "message"."""
        from rusemod import anim, rig
        from rusemod.blender import ask_to_send
        from rusemod.modelin import ModelError, glb_document
        from . import animblender
        from .api import StudioError, words
        w = words(lang)
        work = self._anim_work(address)
        if work is None:
            raise StudioError(w["decoy_blender_why_game"])
        send = work / SEND
        if self._anim_open(work):   # its Blender is open: it sends what it has now
            if ask_to_send(send, SEND_WAIT) is None:
                raise StudioError("Blender didn't answer in time: in Blender, click Send to the R.U.S.E. Studio at the "
                                  "top, then bring your changes back again.")
        sent = animblender.read_sent(work)
        state = _read(work / STATE)
        if not send.is_file() or sent is None:
            # not a game rule: the Studio's own hand-over from Blender, nothing sent from this Blender yet
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring my changes back here.")
        raw = send.read_bytes()
        try:
            doc, binary = glb_document(raw)
            r = rig.rig_of(doc, binary, send.name)
            back = rig.back_of(r, sent["record"])
        except (ModelError, ValueError, KeyError, IndexError, struct.error) as exc:
            raise StudioError(f"{send.name}: {exc}") from None
        if back is None:
            # not a game rule: the bones the animations went out on (the record kept beside them)
            raise StudioError("What came back from Blender isn't on this unit's bones, so its animations can't be "
                              "taken in: send the file RUSE Decoy opened.")
        went = {a["name"]: a for a in sent["animations"]}
        came = animblender.file_animations(send)
        out = {"changed": [], "same": 0, "new": [n for n in came if n not in went],
               "gone": [n for n in went if n not in came], "written": 0}
        unit = animblender.unit_name(self._own_model_file(address))
        mod = self._mod_dir()
        by_action, by_name = [], {}     # (what came back changed: an action's clip; one of the model's animations)
        for got in rig.clips_back(r, back, sent["record"], {n: a["clip"] for n, a in went.items()}):
            a = went.get(got["name"])
            if a is None:
                continue
            if got["same"]:
                out["same"] += 1
                continue
            out["changed"].append(got["name"])
            if a.get("model_animation"):
                by_name[a["model_animation"]] = got["clip"]
            else:
                by_action.append((got["name"], a, got["clip"]))
        clips = self._model_animations_back(address, sent, by_name) if by_name else None
        for shown, a, clip in by_action:
            name = f"blender_{animblender.stem_of(a['member'] or a['own'] or shown)}"
            try:
                with self._saving:
                    for figure, keys in a["actions"].items():
                        for key in keys:
                            anim.add_unit_clip(mod, unit, key, clip, name=name, figure=figure)
                out["written"] += 1
            except anim.AnimError as exc:
                raise StudioError(f"{shown}: {exc}") from None
        if clips is not None:
            try:
                with self._saving:
                    files = anim.set_animations(mod, unit, clips)
                    self._record_lengths(address, clips, files)
            except (anim.AnimError, OSError) as exc:
                raise StudioError(str(exc)) from None
            out["written"] += len(by_name)
        state.update({"brought": _sha(send)})
        _write(work / STATE, state)
        sep = w["blender_squad_list_sep"]
        said = [w["decoy_blender_changed"].format(names=sep.join(out["changed"])) if out["changed"]
                else w["decoy_blender_same"]]
        if out["new"]:
            said.append(w["decoy_blender_new"].format(names=sep.join(out["new"])))
        if out["gone"]:
            said.append(w["decoy_blender_gone"].format(names=sep.join(out["gone"])))
        return {**self.decoy_blender_state(address, lang), **out, "message": " ".join(said)}

    def _model_animations_back(self, address: str, sent: dict, by_name: dict) -> dict:
        """The model's own animations to keep after a bring back (rusemod.anim.set_animations' `clips`): the mod's as
        they are now, each that came back changed (`by_name`: {its name: the clip}) in its place; when they went out
        from the model's file (the mod had none), every one that went out, as Import model takes them in. Refused,
        nothing written, when the model's bones, or one of those animations, changed after they went out."""
        from rusemod import anim
        from . import animblender
        from .api import StudioError
        mod = self._mod_dir()
        unit = animblender.unit_name(self._own_model_file(address))
        model = [a for a in sent["animations"] if a.get("model_animation")]
        went = {a["model_animation"]: a["clip"] for a in model}
        _raw, record = self._own_bones_model(address)
        try:
            now = anim.own_animations(mod, unit)["animations"]
            clips = {n: anim._own_file(Path(mod) / anim.OWN / unit, f, f"{unit}'s {n}").read_bytes()
                     for n, f in now.items()}
        except (anim.AnimError, OSError) as exc:
            raise StudioError(str(exc)) from None
        from_mod = any(a.get("own") for a in model)
        if record != sent["record"] or (from_mod and not clips) \
                or (clips and any(clips.get(n) != went.get(n) for n in by_name)):
            # not a game rule: what came back was made from the model and animations the mod had when they went out
            raise StudioError("This unit's model or its animations changed after they went out to Blender, so what "
                              "came back can't be taken in: open its animations in Blender again.")
        return {**(clips or went), **by_name}

    def _record_lengths(self, address: str, clips: dict, files: dict) -> None:
        """The model's record (files/models/<unit>.json, Import model's) lists its animations with their lengths and
        files: kept in step with the animations kept (`clips`; `files`, rusemod.anim.set_animations' answer), so the
        unit's page says a changed one's own length. A record with no such list is left alone."""
        from rusemod import baf
        own = self._own_model_file(address)
        path = own.with_suffix(".json") if own is not None else None
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path is not None and path.is_file() else None
        except (OSError, ValueError):
            return
        if not isinstance(data, dict) or not isinstance(data.get("animations"), list):
            return
        data["animations"] = [{"name": n, "frames": (c := baf.parse(clip)).frames, "seconds": round(c.duration, 4),
                               "file": files[n]} for n, clip in clips.items()]
        part = path.with_name(path.name + ".part")
        part.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(part, path)
