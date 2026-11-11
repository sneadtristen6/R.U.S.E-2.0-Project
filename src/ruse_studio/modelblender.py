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
pictures that other units wear."""
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
        """Open the unit's model in Blender to be changed (see the module's note). Returns look() with "work" (the
        work folder) and "file" (what Blender opened)."""
        from rusemod import gltf, models
        from rusemod.blender import open_model_to_change
        from .api import StudioError, words
        work, send = self._model_work(address)
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
        return {**self.look(address), "work": str(work), "file": str(start)}

    def model_blender_back(self, address: str, size: float = 1.0) -> dict:
        """Take what Blender sent in as the unit's own model (Import model's way): an open Blender is asked to send
        first; a closed one's last sending is used. Returns model_import()'s answer with "work"."""
        from rusemod.blender import ask_to_send
        from .api import StudioError
        work, send = self._model_work(address)
        proc = self._blenders.get(str(work))
        if proc is not None and proc.poll() is None:  # its Blender is open: it sends what it has now
            ask_to_send(send, SEND_WAIT)
        if not send.is_file():
            # not a game rule: there is nothing to take in until Blender has sent the model
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring back the model here.")
        return {**self.model_import(address, str(send), size), "work": str(work)}
