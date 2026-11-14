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
  squadblender: the ones ticked side by side), their paint (no Bones: they come back onto the game soldier's bones
  whatever Blender did to them);
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

    def _squad_door(self, address: str) -> tuple:
        """The squad's own Blender (its soldiers side by side, as the one button, Add a soldier and the Studio before
        the one button open it): (whether it has something to bring back, Blender still open on it or a sending of its
        last opening not brought back; that opening's session)."""
        from .squadblender import _sha
        work = self._squad_work(address)
        if work is None:
            return False, None
        state = _read(work / "state.json")
        sent = work / "sent" / "sent.json"
        proc = self._blenders.get(str(work))
        running = proc is not None and proc.poll() is None
        waiting = sent.is_file() and _sha(sent) != state.get("brought") and \
            _read(sent).get("session") == state.get("session")
        return bool(running or waiting), state.get("session")

    def _door_open(self, address: str, state: dict) -> bool:
        """Whether the Blender the one button last opened for this unit (one.json's `state`: its door and kind) is still
        open: then Bring my changes back can take what it sends again."""
        door = state.get("door")
        try:
            if door == "model":
                work = self._model_work(address, self._blender_kind(address, state.get("kind") or None))[0]
            elif door == "paint":
                work = self._look_folder(address)
            elif door == "squad":
                work = self._squad_work(address)
            else:
                return False
        except Exception:  # noqa: BLE001 - a unit gone or changed since: its Blender isn't this unit's any more
            return False
        proc = self._blenders.get(str(work)) if work is not None else None
        return proc is not None and proc.poll() is None

    def _model_door(self, address: str, kind: str | None) -> bool:
        """Whether the model's own Blender (Change it in Blender's, for `kind` or the riflemen) has something to bring
        back: a sending, or Blender still open on it (its Bring back then asks it to send)."""
        work, send = self._model_work(address, self._blender_kind(address, kind))
        proc = self._blenders.get(str(work))
        return send.is_file() or (proc is not None and proc.poll() is None)

    def _own_bones(self, address: str) -> bool:
        """Whether the unit's own model (its riflemen's, for a squad) is on bones of its own (the Generic Horse)."""
        from rusemod import bonefit
        own = self._own_model_file(address)
        return own is not None and own.is_file() and bonefit.skeleton_key(own) is not None

    def blender_parts(self, address: str, lang: str = "us") -> dict:
        """What the one Blender button can take of this unit: {"route": "model", "squad", "kinds" or "paint" (a game
        unit that isn't a squad: its paint alone), "parts": [{"id", "label"}] (the ticks, all on to start), "soldiers":
        [{"id", "label"}] (a squad's: each its own tick), "kinds": [{"id": the kind or "" for the riflemen, "label"}] (a
        squad on bones of its own: one at a time), "open": whether its last Blender hasn't been brought back or is still
        open, "door": that Blender's ("model", "squad", "paint") while open, "can": whether this unit can go to Blender,
        "why_not": the sentence when it can't}."""
        from .api import words
        w = words(lang)
        squad = self._soldiers(address)
        own = self._own_model_file(address)
        state = _read(self._one_file(address)) if self._one_file(address) is not None else {}
        # (open: brought back not yet, or its Blender still open after a bring-back, so it can bring back again)
        out = {"route": "model", "parts": [], "soldiers": [], "kinds": [], "can": own is not None,
               "open": bool(state) and (not state.get("back") or self._door_open(address, state)),
               "why_not": None if own is not None else w["one_why_game"]}
        out["door"] = state.get("door") if out["open"] else None   # (which Blender is open: model, squad or paint)
        if own is None:
            if self._mod_dir() is None:
                out["why_not"] = w["no_mod"]
            elif not squad and self._look_models(address)[0]:
                # a game unit that isn't a squad: its paint alone, as the Look box's Repaint in Blender painted it (seen
                # in the game; its pictures go into the mod); a game squad's uniform is every squad's: copy it first
                out.update({"route": "paint", "parts": [{"id": "paint", "label": w["one_part_paint"]}], "can": True,
                            "why_not": None})
            return out
        parts = [{"id": "model", "label": w["one_part_model"]}]
        # Its bones only for a model on bones of its own: a squad's soldiers on the game soldier's bones come back onto
        # those bones whatever Blender did to them (walked with real Blender 2026-11-13, onewalk.py: a bone moved 5 cm,
        # Its bones ticked and unticked, the mod's model the same byte for byte), so a tick there would change nothing
        if self._own_bones(address):
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
            out["soldiers"] = [{"id": str(s["id"]), "label": w["blender_squad_numbered"].format(
                label=s.get("label") or "", n=s.get("number", s["id"])) if s.get("label") else str(s["id"])}
                for s in info.get("soldiers") or []]   # ("Rifleman 3", as Blender names him)
        return out

    def blender_open(self, address: str, ticks: dict, lang: str = "us") -> dict:
        """Open in Blender what `ticks` say ({"model": bool, "bones": bool, "paint": bool, "soldiers": [ids],
        "kind": the kind for a squad on bones of its own, "" its riflemen}; see the module's note), and remember it for
        blender_back. Returns the opened door's answer with "door"."""
        from .api import StudioError
        ticks = dict(ticks or {})
        parts = self.blender_parts(address, lang)
        if not parts["can"]:
            if self._mod_dir() is None:
                raise StudioError("Pick or make a mod first.")
            # not a game rule: only a new unit of this mod gets a model of its own (the model door's own refusal)
            raise StudioError("Only a new unit made in this mod can get a model of its own: copy the unit first.")
        has = {p["id"] for p in parts["parts"]}   # (a game unit has its paint alone: no model to tick)
        model, paint = bool(ticks.get("model", True)) and "model" in has, bool(ticks.get("paint", True))
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
        bones = any(p["id"] == "bones" for p in parts["parts"])   # (a part this unit has: see blender_parts)
        state = {"format": 1, "door": door, "kind": kind, "keep_bones": bones and not ticks.get("bones", True),
                 "keep_paint": not paint, "back": False,
                 # (the squad Blender's own session: Add a soldier opens that Blender too, without these ticks)
                 "session": self._squad_door(address)[1] if door == "squad" else None}
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
        door = state.get("door") if state.get("door") in ("model", "squad", "paint") else None
        keep_bones, keep_paint = bool(state.get("keep_bones")), bool(state.get("keep_paint"))
        if self._soldiers(address):
            # the squad's own Blender opened by something other than the one button (Add a soldier, or the Studio
            # before the one button, its Blender open or its sending waiting across the update): that Blender comes
            # back, and nothing in it was unticked; one.json stays the one button's
            pending, session = self._squad_door(address)
            if pending and (door != "squad" or state.get("session") != session):
                back = self.squad_blender_back(address, lang)
                return {**back, "door": "squad"}
        if door is None:
            # not a game rule: the Studio's own hand-over from Blender, nothing opened from this page yet
            raise StudioError("Open this unit in Blender first, change it there, then Bring my changes back.")
        if door == "paint":
            got = self.look_bring_back(address)
        elif door == "squad":
            got = self.squad_blender_back(address, lang, keep_bones=keep_bones, keep_paint=keep_paint)
        else:
            kind = state.get("kind") or None
            if not self._model_door(address, kind):
                # not a game rule: the Studio's own hand-over from Blender, nothing sent yet (said with this button's
                # name; the model's own refusal says "bring your changes back", as it's said beside either button)
                raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. "
                                  "Studio at the top, then Bring my changes back here.")
            own = self._kind_file(address, kind) if kind else self._own_model_file(address)
            record = _read(own.with_suffix(".json")) if own is not None else {}
            size = record.get("size") if isinstance(record.get("size"), (int, float)) else 1.0
            got = self.model_blender_back(address, size, kind, keep_bones=keep_bones, keep_paint=keep_paint)
        state["back"] = True
        one.write_text(json.dumps(state, indent=1), encoding="utf-8")
        return {**got, "door": door}
