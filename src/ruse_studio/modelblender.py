"""A new unit's model changed in Blender and brought back (StudioApi's ModelBlenderCalls; the owner's order of
2026-11-10, item 4: a player couldn't give a squad a model of his own; scratch/animmodels/item4/FINDINGS.md).

Change it in Blender (model_blender) writes the unit's model with its bones at their real places (rusemod.gltf's
rest_bones) into the unit's work folder, <mod>/blender/<the unit's name>/, and opens it in Blender
(rusemod.blender_model): the modder changes it there, or brings in a model of his own and puts it on the bones with
Blender's own tools, then clicks Send to the R.U.S.E. Studio. Bring back the model (model_blender_back) asks that Blender
to send it (rusemod.blender.ask_to_send) and takes it in with Import model, as the unit's own model.
The work folder sits beside the mod's src/ and files/: Export doesn't pack it (rusemod.package), the build doesn't read
it, and the modder finds his Blender files there. What was sent last is where the next Change it in Blender starts.
Unlike Open in Blender in the Look box, this needs no Custom uniform: it changes the unit's own model, never the game's
pictures that other units wear.
Each of a squad's soldiers has his own (the owner, 2026-11-11, on the step-4 test copy: the big-head squad's bazooka
man "did not get scaled", then "edit any individual in like a normal rifleman squad ... inside Blender. Or add a new
model or attach it with bones"): the Model row's buttons are the riflemen's, and a squad whose heavy-weapon soldier
draws another model gives him his own pair under Its soldiers (`kind`: StudioApi._soldier_kinds). His work folder is
<mod>/blender/<the unit's name>@<kind>/, beside his model file files/models/<the unit's name>@<kind>.glb, and what he
sends back is his model alone (Import model's `kind`). A squad has as many looks as the game's unit data gives it: one
model every one of its riflemen wears, and one for its heavy-weapon soldier."""
from __future__ import annotations

import json
import re
from pathlib import Path

WORK = "blender"
SEND_WAIT = 60.0   # seconds Bring back the model waits for an open Blender to send
# a squad's second figure carries the heavy weapon: the rifleman is the one to change, and what comes back is the
# riflemen's model (Import model's first kind; the heavy-weapon soldier keeps the copied unit's until he gets his own,
# the owner, 2026-11-11: "when you copy a fucking unit, it should copy the unit")
HEAVY = re.compile(r"bazooka|panzerschreck|piat|flame|lanceflamme|mortier|mortar", re.I)


class ModelBlenderCalls:
    def _blender_kind(self, address: str, kind: str | None) -> str | None:
        """Which of a squad's soldiers Change it in Blender is for: None for its riflemen (no kind given, or the
        first: the Model row's buttons), the kind for another (its heavy-weapon soldier: his own buttons under Its
        soldiers). A kind the squad hasn't got is refused."""
        from .api import StudioError
        if not kind:
            return None
        kinds = self._soldier_kinds(address)
        if not kinds:
            raise StudioError("This unit has no soldiers of another kind: Change it in Blender in the Model row is for "
                              "its model.")
        if kind not in kinds:
            raise StudioError(f"This squad has no soldier called {kind}: pick one of those under Its soldiers.")
        return None if kind == next(iter(kinds)) else kind

    def _model_work(self, address: str, kind: str | None = None) -> tuple[Path, Path]:
        """(the work folder <mod>/blender/<its name>/, or <its name>@<kind>/ for one of a squad's other soldiers
        (`kind`, as _blender_kind gives it), the file Blender sends to); a StudioError for a unit that can't have a
        model of its own."""
        from .api import StudioError
        own = self._kind_file(address, kind) if kind else self._own_model_file(address)
        if own is None:
            raise StudioError("Only a new unit made in this mod can get a model of its own: copy the unit first.")
        work = self._mod_dir() / WORK / own.stem
        return work, work / f"{own.stem}.glb"

    def model_blender(self, address: str, lang: str = "us", kind: str | None = None) -> dict:
        """Open the unit's model in Blender to be changed (see the module's note); `kind`: one of a squad's other
        soldiers, opened alone (his last sending, or the game model his figure draws). Returns look() with "work" (the
        work folder), "file" (what Blender opened) and "kind" (None for the riflemen)."""
        from rusemod import gltf, models
        from rusemod.blender import open_model_to_change
        from .api import StudioError, words
        kind = self._blender_kind(address, kind)
        work, send = self._model_work(address, kind)
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        if send.is_file():
            start = send  # what was sent last time: the work goes on from it
        else:
            found = [m for m in self._look_models(address)[0] if "_dest" not in m.lower()]
            if not found:
                raise StudioError("This unit has no 3D model the Studio can open.")
            if kind:   # (one of the squad's other soldiers: the game model his figure draws, _kind_models)
                found = self._kind_models(address, kind, found)
                if not found:
                    raise StudioError("This soldier has no 3D model the Studio can open.")
                model = found[0]
            else:
                found = self._kind_models(address, None, found) or found   # (a squad's riflemen's, _soldier_kinds)
                model = next((m for m in found if not HEAVY.search(m.rsplit("\\", 1)[-1])), found[0])
            work.mkdir(parents=True, exist_ok=True)
            lib = models.Library(self._game())
            try:
                start = Path(gltf.export(lib, [model], work, rest_bones=True)[0]["file"])
            finally:
                lib.close()
        w = words(lang)
        (work / "words.json").write_text(json.dumps(
            {"send": w["blender_model_send"], "sent": w["blender_model_sent"],
             "hint": [w["blender_model_hint1"], w["blender_model_hint2"]]}, ensure_ascii=False), encoding="utf-8")
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        return {**self.look(address), "work": str(work), "file": str(start), "kind": kind}

    def model_blender_back(self, address: str, size: float = 1.0, kind: str | None = None) -> dict:
        """Take what Blender sent in as the unit's own model (Import model's way), or, with `kind`, as that soldier's
        own model alone (the squad's others keep theirs): an open Blender is asked to send first; a closed one's last
        sending is used. Returns model_import()'s answer with "work" and "kind"."""
        from rusemod.blender import ask_to_send
        from .api import StudioError
        kind = self._blender_kind(address, kind)
        work, send = self._model_work(address, kind)
        proc = self._blenders.get(str(work))
        if proc is not None and proc.poll() is None:  # its Blender is open: it sends what it has now
            ask_to_send(send, SEND_WAIT)
        if not send.is_file():  # not a game rule: the Studio's own hand-over from Blender, nothing sent yet
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring back the model here.")
        got = self.model_import(address, str(send), size, kind=kind) if kind else self.model_import(address, str(send), size)
        return {**got, "work": str(work), "kind": kind}
