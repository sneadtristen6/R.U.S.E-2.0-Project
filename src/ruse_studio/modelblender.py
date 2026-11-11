"""A new unit's model changed in Blender and brought back (StudioApi's ModelBlenderCalls; the owner's order of
2026-11-10, item 4: a player couldn't give a squad a model of his own; scratch/animmodels/item4/FINDINGS.md), with its
animations (item 5 of his list: "fully editable in the studio"; ruse_studio.animblender).

Change it in Blender (model_blender) writes the unit's model with its bones at their real places (rusemod.gltf's
rest_bones) into the unit's work folder, <mod>/blender/<the unit's name>/, and opens it in Blender
(rusemod.blender_model): the modder changes it there, or brings in a model of his own and puts it on the bones with
Blender's own tools, then clicks Send to the R.U.S.E. Studio. Bring back the model (model_blender_back) asks that Blender
to send it (rusemod.blender.ask_to_send) and takes it in with Import model, as the unit's own model.
The work folder sits beside the mod's src/ and files/: Export doesn't pack it (rusemod.package), the build doesn't read
it, and the modder finds his Blender files there. What was sent last is where the next Change it in Blender starts.
Unlike Open in Blender in the Look box, this needs no Custom uniform: it changes the unit's own model, never the game's
pictures that other units wear.

A unit whose figures play animations gets them in the same file, every bone of its skeleton with them (rusemod.gltf's
`clips`; a model on bones of its own: rusemod.animglb.own_glb, its own clips), and what went out is kept beside it
(ruse_studio.animblender). Coming back, any file laid out that way (Bring back the model, or the modder's own File >
Export picked in Import model) is first put back in the game's frames (rusemod.rig.turn_back: _game_frames_file), so
Import model reads it as any other; then each animation that came back changed becomes the unit's own clip for the
actions that play it (rusemod.anim.add_unit_clip: the unit's actions alone, every other unit plays the game's), one
that came back as it went out is left alone (_animations_back). A model on bones of its own takes its animations in
with the model itself (Import model's own_bones)."""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

WORK = "blender"
SEND_WAIT = 60.0   # seconds Bring back the model waits for an open Blender to send
# a squad's second figure carries the heavy weapon: the rifleman is the one to change (the others with the same bones
# wear the model too: rusemod.unitmodel._own_model_part)
HEAVY = re.compile(r"bazooka|panzerschreck|piat|flame|lanceflamme|mortier|mortar", re.I)
GAME_FRAMES = ".game.glb"   # a file laid out for Blender, put back in the game's frames, beside the work file


class ModelBlenderCalls:
    def _model_work(self, address: str) -> tuple[Path, Path]:
        """(the unit's work folder <mod>/blender/<its name>/, the file Blender sends to); a StudioError for a unit
        that can't have a model of its own."""
        from .api import StudioError
        own = self._own_model_file(address)
        if own is None:
            raise StudioError("Only a new unit made in this mod can get a model of its own: copy the unit first.")
        work = self._mod_dir() / WORK / own.stem
        return work, work / f"{own.stem}.glb"

    def model_blender(self, address: str, lang: str = "us") -> dict:
        """Open the unit's model in Blender to be changed (see the module's note), with every animation the unit
        plays on it. Returns look() with "work" (the work folder), "file" (what Blender opened) and "animations" (how
        many it holds)."""
        from rusemod import animglb, gltf, models
        from rusemod.blender import open_model_to_change
        from . import animblender
        from .api import StudioError, words
        work, send = self._model_work(address)
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        w = words(lang)
        if send.is_file():
            start = send  # what was sent last time: the work goes on from it
        else:
            own_raw, own_record = self._own_bones_model(address)
            found = [m for m in self._look_models(address)[0] if "_dest" not in m.lower()]
            if own_raw is None and not found:
                raise StudioError("This unit has no 3D model the Studio can open.")
            work.mkdir(parents=True, exist_ok=True)
            lib = models.Library(self._game())
            try:
                if own_raw is not None:     # a model on bones of its own, with its own animations
                    rows = self._unit_plays(address, lib, own_record, w, own_raw)
                    data, _summary = animglb.own_glb(own_raw, animblender.as_clips(rows))
                    start = work / f"{send.stem}_model.glb"
                    start.write_bytes(data)
                    animblender.write_sent(work, "own", own_record, rows)
                else:
                    model = next((m for m in found if not HEAVY.search(m.rsplit("\\", 1)[-1])), found[0])
                    record = lib.skeleton(model) if hasattr(lib, "skeleton") else None
                    rows = self._unit_plays(address, lib, record, w) if record is not None else []
                    clips = {model: animblender.as_clips(rows)} if rows else None
                    try:
                        start = Path(gltf.export(lib, [model], work, rest_bones=True, **(
                            {"clips": clips} if clips else {}))[0]["file"])
                    except animglb.AnimGlbError as exc:
                        raise StudioError(str(exc)) from None
                    if rows:
                        animblender.write_sent(work, model, record, rows)
                    else:
                        animblender.forget_sent(work)
            finally:
                lib.close()
        (work / "words.json").write_text(json.dumps(
            {"send": w["blender_model_send"], "sent": w["blender_model_sent"],
             "hint": [w["blender_model_hint1"], w["blender_model_hint2"]],
             "hint_animations": [w["blender_anim_hint1"], w["blender_anim_hint2"]]}, ensure_ascii=False),
            encoding="utf-8")
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        return {**self.look(address), "work": str(work), "file": str(start),
                "animations": len(animblender.file_animations(start))}

    def model_blender_back(self, address: str, size: float = 1.0) -> dict:
        """Take what Blender sent in as the unit's own model (Import model's way), its animations with it: an open
        Blender is asked to send first; a closed one's last sending is used. Returns model_import()'s answer with
        "work"."""
        from rusemod.blender import ask_to_send
        from .api import StudioError
        work, send = self._model_work(address)
        proc = self._blenders.get(str(work))
        if proc is not None and proc.poll() is None:  # its Blender is open: it sends what it has now
            ask_to_send(send, SEND_WAIT)
        if not send.is_file():
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring back the model here.")
        return {**self.model_import(address, str(send), size), "work": str(work)}

    # --- a unit's animations (ruse_studio.animblender) ---
    def _own_bones_model(self, address: str) -> tuple[bytes | None, bytes | None]:
        """(the unit's own model file's bytes, its skeleton record) when its model is on bones of its own (its file
        carries its record: rusemod.modelin.write_glb), else (None, None)."""
        import base64
        import struct
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
        """ruse_studio.animblender.unit_plays for the unit on a model of `record`'s bones; a model on bones of its own
        (`own_raw`, its file) keeps its animations' own names (the modder's, which its record knows them by), and when
        its actions play none of its own clips yet, the animations its file carries go out (rusemod.unitmodel.own_clips),
        no action playing them."""
        from rusemod import anim, animlist, baf, rig, unitmodel
        from rusemod.modelin import ModelError, glb_document
        from . import animblender
        from .api import StudioError
        own = self._own_model_file(address)
        names = baf.skeleton(record)["names"]
        try:
            rows = animblender.unit_plays(self._unit_figures(address), names, animlist.clip_reader(lib.arc),
                                          self._mod_dir(), animblender.unit_name(own), lib.skeleton, w,
                                          labelled=own_raw is None)
        except anim.AnimError as exc:
            raise StudioError(str(exc)) from None
        if rows or own_raw is None:
            return rows
        try:
            carried, _notes = unitmodel.own_clips(rig.rig_of(*glb_document(own_raw)), record)
        except (ModelError, ValueError):
            return []
        return [{"name": n, "clip": c, "member": None, "own": None, "actions": {}} for n, c in carried.items()]

    def _reference_of(self, address: str, work: Path) -> tuple[bytes | None, dict | None]:
        """(the skeleton record a file sent back for the unit was laid out from, what went out with it): the work
        folder's (animblender.read_sent), else the unit's own model's record when it is on bones of its own, else
        None (no animations went out; a model on the game soldier's bones is read as item 4 reads it)."""
        from . import animblender
        sent = animblender.read_sent(work)
        if sent is not None:
            return sent["record"], sent
        _raw, record = self._own_bones_model(address)
        return record, None

    def _game_frames_file(self, address: str, file: Path) -> Path:
        """The file Import model reads for `file`: itself, or, when its bones are laid out for Blender from the unit's
        reference record (_reference_of; Change it in Blender's file and the same sent back or exported by hand), the
        same in the game's frames (rusemod.rig.turn_back, each bone the modder didn't change as the clip that went out
        has it), written beside the work file as <its name>.game.glb. What turn_back found is kept for
        _animations_back."""
        from rusemod import rig
        from rusemod.modelin import ModelError
        from . import animblender
        from .api import StudioError
        self._turned_back = {}
        if self._mod_dir() is None:
            return file
        try:
            work, _send = self._model_work(address)
        except StudioError:     # (not a new unit: Import model says why)
            return file
        if file.suffix.lower() != ".glb" or not file.is_file():
            return file
        record, sent = self._reference_of(address, work)
        if record is None:
            return file
        originals = {a["name"]: a["clip"] for a in (sent or {}).get("animations", [])}
        try:
            data, info = rig.turn_back(file.read_bytes(), record, file.name, originals)
        except (ModelError, ValueError, OSError, KeyError, IndexError, struct.error):
            return file      # (Import model reads it as it is, and says what's wrong with it)
        if data is None:
            return file
        work.mkdir(parents=True, exist_ok=True)
        out = work / (file.stem + GAME_FRAMES)
        out.write_bytes(data)
        self._turned_back = {"file": str(file), "record": record, "sent": sent, "info": info,
                             "names": animblender.file_animations(file)}
        return out

    def _animations_back(self, address: str, report: dict | None) -> dict | None:
        """After Import model took a file _game_frames_file put back in the game's frames (the one it kept): its
        animations against what went out. A model on the game soldier's bones (its report has no own skeleton): each
        that came back changed becomes the unit's own clip for every action of every figure that played it
        (rusemod.anim.add_unit_clip); one made in Blender (no clip went out under its name) is played by no action yet,
        and said; one that went out and didn't come back stays as it was, and is said. A model on bones of its own took
        them in with it. Returns {"changed": names, "same": how many came back as they went, "new": names, "gone":
        names, "written": how many clips were written, "own_bones": whether the model is on bones of its own}, or None
        (no animations went out)."""
        from rusemod import anim, rig
        from rusemod.modelin import OWN_SKELETON, ModelError, glb_document
        from . import animblender
        from .api import StudioError
        turned = getattr(self, "_turned_back", None) or {}
        if not turned or not turned.get("sent") or report is None:
            return None
        file = Path(turned["file"])
        sent = turned["sent"]
        went = {a["name"]: a for a in sent["animations"]}
        came = turned["names"]
        # on bones of its own: the fitting's report says so, or the model's record (COMMON5's "skeleton": "own")
        own_bones = bool(report.get(OWN_SKELETON)) or (self._own_model_record(address) or {}).get("skeleton") == "own"
        out = {"changed": [], "same": 0, "new": [n for n in came if n not in went],
               "gone": [n for n in went if n not in came], "written": 0, "own_bones": own_bones}
        if own_bones:
            for a in turned["info"].get("animations", []):
                if a["changed"]:
                    out["changed"].append(a["name"])
                elif a["changed"] is not None:
                    out["same"] += 1
            return out
        try:
            doc, binary = glb_document(Path(file).read_bytes())
            r = rig.rig_of(doc, binary, Path(file).name)
            back = rig.back_of(r, turned["record"])
        except (ModelError, ValueError, OSError, KeyError, IndexError, struct.error):
            return out
        if back is None:
            return out
        unit = animblender.unit_name(self._own_model_file(address))
        mod = self._mod_dir()
        for got in rig.clips_back(r, back, turned["record"], {n: a["clip"] for n, a in went.items()}):
            a = went.get(got["name"])
            if a is None:
                continue
            if got["same"]:
                out["same"] += 1
                continue
            out["changed"].append(got["name"])
            name = f"blender_{animblender.stem_of(a['member'] or a['own'] or got['name'])}"
            try:
                with self._saving:
                    for figure, keys in a["actions"].items():
                        for key in keys:
                            anim.add_unit_clip(mod, unit, key, got["clip"], name=name, figure=figure)
                out["written"] += 1
            except anim.AnimError as exc:
                raise StudioError(f"{got['name']}: {exc}") from None
        return out
