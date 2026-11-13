"""The one Blender button of a unit's page: Open in Blender, and Bring my changes back (the owner, 2026-11-13: "Have it
like you can either take the whole unit or ... you can go within that unit and select which ones you want to bring into
Blender ... Rather than having a button to take each thing into Blender, you can just like, I want to leave everything,
I want to bring everything but the bones. So then you just uncheck the bones and then you're good to go"; then "this.
release"). Before it a unit's page had a Blender button per part (Change it in Blender on the model and on each kind of
soldier, Change the squad in Blender, the paint's own Open in Blender), each with its Bring back, and two of them did
the same thing differently: Change the squad in Blender broke a squad on bones of its own (the Generic Horse and every
horse squad of our test mods, walked with real Blender 2026-11-13: the changed rider came in off the riflemen's bones,
"that can stop the game", with every soldier's animations) where Change it in Blender works. His words of 2026-11-13:
"Why is there two different buttons doing the same thing that then break sometimes? ... I thought we talked about
making that page a hell of a lot less buttons." Animations stay RUSE Decoy's (his 2026-11-10: "The only way you should
change animation is in Ruse Decoy"); a model's own animations ride along in its file and come back as they went.

What the ticks open, one Blender at a time (blender_parts says what a unit has; blender_open opens; blender_back takes
in, and remembers nothing else than one.json in the unit's Blender folder):
- a unit that isn't a squad: its model (Change it in Blender's way, modelblender), its bones when it has them, its
  paint; the model unticked and the paint ticked: the paint alone (the Look box's way, the game's pictures);
- a squad of soldiers on the game soldier's bones: its soldiers, each ticked or not (Change the squad in Blender's way,
  squadblender: the ones ticked side by side), their bones, their paint;
- a squad on bones of its own (the Generic Horse): one of its kinds at a time (the riflemen with their horse, or the
  heavy-weapon soldier), as Change it in Blender opens them, never the whole squad side by side (five horses, each with
  every animation: ten minutes to open and the break above);
- Bones or Paint unticked: Bring back puts what went out back (rusemod.gltf.bones_like, paint_like), so it comes back
  as it was."""
from __future__ import annotations

import json
from pathlib import Path

ONE = "one.json"          # which Blender the one button opened for a unit, and with which ticks
PARTS = ("model", "bones", "paint")


def _read(path: Path) -> dict:
    try:
        got = json.loads(Path(path).read_text(encoding="utf-8"))
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


class OneBlenderCalls:
    def _one_file(self, address: str) -> Path | None:
        """<mod>/blender/<the unit's name>/one.json, None with no mod picked."""
        from .modelblender import WORK
        mod = self._mod_dir()
        return None if mod is None else mod / WORK / address.rsplit("/", 1)[-1] / ONE

    def _own_bones(self, address: str) -> bool:
        """Whether the unit's own model (its riflemen's, for a squad) is on bones of its own (the Generic Horse)."""
        from rusemod import bonefit
        own = self._own_model_file(address)
        return own is not None and own.is_file() and bonefit.skeleton_key(own) is not None

    def blender_parts(self, address: str, lang: str = "us") -> dict:
        """What the one Blender button can take of this unit: {"route": "model", "squad" or "kinds", "parts": [{"id",
        "label"}] (the ticks, all on to start), "soldiers": [{"id", "label"}] (a squad's: each its own tick), "kinds":
        [{"id": the kind or "" for the riflemen, "label"}] (a squad on bones of its own: one at a time), "open": whether
        its last Blender hasn't been brought back, "can": whether this unit can go to Blender, "why_not": the sentence
        when it can't}."""
        from .api import words
        w = words(lang)
        squad = self._soldiers(address)
        own = self._own_model_file(address)
        state = _read(self._one_file(address)) if self._one_file(address) is not None else {}
        out = {"route": "model", "parts": [], "soldiers": [], "kinds": [], "open": bool(state) and not state.get("back"),
               "can": own is not None, "why_not": None if own is not None else w["one_why_game"]}
        if own is None:
            return out
        parts = [{"id": "model", "label": w["one_part_model"]}]
        if squad or (own.is_file() and self._own_bones(address)):
            parts.append({"id": "bones", "label": w["one_part_bones"]})
        parts.append({"id": "paint", "label": w["one_part_paint"]})
        out["parts"] = parts
        if squad and self._own_bones(address):
            out["route"] = "kinds"
            out["kinds"] = [{"id": "", "label": w["one_kind_riflemen"]}] + [
                {"id": str(row.get("kind")), "label": row.get("label") or w["one_kind_other"]}
                for row in self._kind_rows(address)[1:] if row.get("kind")]
        elif squad:
            out["route"] = "squad"
            info = self.squad_info(address, lang) or {}
            out["soldiers"] = [{"id": str(s["id"]), "label": s.get("label") or str(s["id"])}
                               for s in info.get("soldiers") or []]
        return out

    def blender_open(self, address: str, ticks: dict, lang: str = "us") -> dict:
        """Open in Blender what `ticks` say ({"model": bool, "bones": bool, "paint": bool, "soldiers": [ids],
        "kind": the kind for a squad on bones of its own, "" its riflemen}; see the module's note), and remember it for
        blender_back. Returns the opened door's answer with "door"."""
        from .api import StudioError
        ticks = dict(ticks or {})
        parts = self.blender_parts(address, lang)
        if not parts["can"]:
            # not a game rule: only a new unit of this mod gets a model of its own (the model door's own refusal)
            raise StudioError("Only a new unit made in this mod can get a model of its own: copy the unit first.")
        model, paint = bool(ticks.get("model", True)), bool(ticks.get("paint", True))
        soldiers = [str(s) for s in (ticks.get("soldiers") or [])]
        if parts["route"] == "squad" and model and not soldiers:
            soldiers = [s["id"] for s in parts["soldiers"]]
        if not model and paint:
            got, door, kind = self.look_open(address), "paint", None
        elif not model:
            # not a game rule: nothing was ticked, so there is nothing for Blender to open
            raise StudioError("Tick what goes to Blender first: the model, its bones or its paint.")
        elif parts["route"] == "squad":
            got, door, kind = self._into_blender(address, lang, only=soldiers), "squad", None
        else:
            kind = str(ticks.get("kind") or "") or None if parts["route"] == "kinds" else None
            got, door = self.model_blender(address, lang, kind), "model"
        state = {"format": 1, "door": door, "kind": kind, "keep_bones": not ticks.get("bones", True),
                 "keep_paint": not paint, "back": False}
        one = self._one_file(address)
        one.parent.mkdir(parents=True, exist_ok=True)
        one.write_text(json.dumps(state, indent=1), encoding="utf-8")
        return {**got, "door": door}

    def blender_back(self, address: str, lang: str = "us") -> dict:
        """Bring my changes back from the Blender the one button opened (blender_open's one.json): the model's, the
        squad's or the paint's own bring-back, with the unticked Bones and Paint put back as they went out. Returns that
        bring-back's answer with "door" and "kept"."""
        from .api import StudioError
        one = self._one_file(address)
        state = _read(one) if one is not None else {}
        door = state.get("door")
        if door not in ("model", "squad", "paint"):
            # not a game rule: the Studio's own hand-over from Blender, nothing opened from this page yet
            raise StudioError("Open this unit in Blender first, change it there, then Bring my changes back.")
        keep_bones, keep_paint = bool(state.get("keep_bones")), bool(state.get("keep_paint"))
        if door == "paint":
            got = self.look_bring_back(address)
        elif door == "squad":
            got = self.squad_blender_back(address, lang, keep_bones=keep_bones, keep_paint=keep_paint)
        else:
            kind = state.get("kind") or None
            own = self._kind_file(address, kind) if kind else self._own_model_file(address)
            record = _read(own.with_suffix(".json")) if own is not None else {}
            size = record.get("size") if isinstance(record.get("size"), (int, float)) else 1.0
            got = self.model_blender_back(address, size, kind, keep_bones=keep_bones, keep_paint=keep_paint)
        state["back"] = True
        one.write_text(json.dumps(state, indent=1), encoding="utf-8")
        return {**got, "door": door}
