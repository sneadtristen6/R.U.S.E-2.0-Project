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
(rusemod.anim.add_unit_clip: files/anim/units.toml, files/anim/own/<unit>/), kept in one file whose name stays the same
each round (_action_file: the unit's own file it went out as, else blender_<the game's clip>), and a clip file no row
names any more goes (Export packs all of files/): RUSE Decoy shows it under Only this unit, every other unit keeps the
game's. One made in Blender (no clip went out under its name) is played by no action yet and said, and isn't taken in;
one that went out and didn't come back stays as it was and is said. The model in the file is only what the animations
play on: what is done to it isn't taken in (the model's own doors are Import a model and Change the squad in Blender).

A model on bones of its own (a horse, any creature: Import model kept its record in its file) plays its model's own
animations, which Import model put in the unit's files/anim/units.toml [unit.<name>.animation] and its actions play by
name or the nearest (rusemod.animactions); no game clip is on its bones. Those go out under their own names, as the mod
has them (before it has any, the ones its file carries), and a changed one comes back in its place by name
(rusemod.anim.set_animations, Import model's own store), so whatever played it plays it changed and every pick stays.
Found 2026-11-12 checking the join: sent with no action, such a change was said to be the unit's own and written
nowhere. When the model or the animation changed after it went out (a model imported again while Blender was open),
nothing is taken in, and that is said. The build plays such a model's animations by halves (rusemod.animactions: one
named for a half, t_ or b_, on that half's listings only, through the model's own two masks): a change to bones of the
other half is said, as not tried in the game yet (_halves_unplayed; the owner decides whether more is done).

Each Bring my changes back makes the mod play what Blender sent, compared with what the mod has now: a change brought
back earlier since Blender opened and undone there since is undone in the mod too (its rows and file as they were;
state.json "wrote"), and the same sending brought back twice is nothing new. Refused, nothing written: a bone of the
unit's skeleton renamed or deleted in Blender (its animations are on that skeleton: which bone a renamed one was can't
be told, and a deleted one's points don't move in Blender as the game moves them). Said, the rest taken in: a bone made
in Blender (the game can't play it), timing Blender's NLA editor gives an action (Send carries the actions as they are:
rusemod.blender_model's ABOUT), and a scene set to another frame rate than the game's 30 (each frame sent is taken as
one of the game's: rusemod.rig.Rig.frames' rate).

The work folder: <mod>/blender/<unit>/animations/ (never packed): what went out (animblender's animations.json and
clips/), the file Blender opened, the file it sends (send.glb) and what Send says of it (send.glb.json), the words, and
state.json ("session"; "brought": the fingerprint of the last sending brought back; "wrote": what each bring back since
Blender opened made of an animation). Each opening starts from what the mod has now: a sending brought back already is
taken out (it's in the mod; a bring back never reads it again); one never brought back is kept aside whole first
(sent-not-brought-<time>/: the sending with what went out with it), and Bring back the set-aside sending still takes it
in (decoy_blender_back's `aside`)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import time
from pathlib import Path

WORK = "animations"      # <mod>/blender/<unit>/animations/
SEND = "send.glb"        # what Blender sends
ABOUT = SEND + ".json"   # what Send says of it (rusemod.blender_model's ABOUT: its frame rate, the NLA's timing)
STATE = "state.json"
ASIDE = "sent-not-brought-"   # a sending never brought back, kept aside whole: <ASIDE><time>/
SEND_WAIT = 60.0         # seconds Bring my changes back waits for an open Blender to send
RATE_NEAR = 5e-4         # a frame rate this near the game's 30 (a share of it) is the game's: a float's time isn't exact
_SAFE_FILE = re.compile(r"^[A-Za-z0-9_-]+\.baf$")   # a clip file's name as rusemod.anim writes it


def _sha(path: Path) -> str | None:
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _sha_of(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


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


def _fps_text(rate: float) -> str:
    """A frame rate as said: 24, 29.97."""
    return f"{rate:.2f}".rstrip("0").rstrip(".")


def _figure_row(table: dict, figure: str, action: str) -> str | None:
    """The file a unit's table (units.toml's [unit.<name>]) gives one figure's action, or None."""
    return (((table.get("figure") or {}).get(figure) or {}).get("action") or {}).get(action)


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

    @staticmethod
    def _asides(work: Path) -> list:
        """The sendings kept aside whole (_anim_set_aside) that can still be brought back, newest first."""
        from . import animblender
        if not Path(work).is_dir():
            return []
        return sorted((p for p in Path(work).iterdir() if p.is_dir() and p.name.startswith(ASIDE)
                       and (p / SEND).is_file() and (p / animblender.SENT).is_file()),
                      key=lambda p: p.name, reverse=True)

    def decoy_blender_state(self, address: str, lang: str = "us") -> dict:
        """What RUSE Decoy's page for one unit shows of its Blender door: {"can": whether its animations can go out
        (a new unit of this mod), "why_not": a sentence when they can't, "open": its Blender is open now, "waiting": a
        sending not brought back yet, "work": the work folder (None for a game unit), "aside": the newest sending kept
        aside that can still be brought back (its folder's name, for decoy_blender_back's `aside`; None: none),
        "aside_folder": where it is}."""
        from .api import words
        w = words(lang)
        work = self._anim_work(address)
        if work is None:
            return {"can": False, "why_not": w["decoy_blender_why_game"], "open": False, "waiting": False,
                    "work": None, "aside": None, "aside_folder": None}
        send = work / SEND
        state = _read(work / STATE)
        waiting = send.is_file() and _sha(send) != state.get("brought") and state.get("session") is not None
        asides = self._asides(work)
        return {"can": True, "why_not": None, "open": self._anim_open(work), "waiting": bool(waiting),
                "work": str(work), "aside": asides[0].name if asides else None,
                "aside_folder": str(asides[0]) if asides else None}

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
    @staticmethod
    def _anim_set_aside(work: Path) -> Path:
        """Blender's last sending, never brought back, kept aside whole: moved to sent-not-brought-<time>/ with what
        Send said of it, and a copy of what went out with it (animations.json and its clips), its state and its words,
        so Bring back the set-aside sending can still take it in. Returns the folder."""
        from . import animblender
        stamp = time.strftime(f"{ASIDE}%Y%m%d-%H%M%S")
        aside, k = work / stamp, 2
        while aside.exists():
            aside, k = work / f"{stamp}-{k}", k + 1
        aside.mkdir()
        os.replace(work / SEND, aside / SEND)
        if (work / ABOUT).is_file():
            os.replace(work / ABOUT, aside / ABOUT)
        for name in (animblender.SENT, STATE, "words.json"):
            if (work / name).is_file():
                shutil.copy2(work / name, aside / name)
        if (work / animblender.CLIPS).is_dir():
            shutil.copytree(work / animblender.CLIPS, aside / animblender.CLIPS)
        return aside

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
            set_aside = self._anim_set_aside(work)
        else:   # (a sending brought back already is in the mod: a bring back from this opening never reads it again)
            send.unlink(missing_ok=True)
            (work / ABOUT).unlink(missing_ok=True)
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
        session = hashlib.sha256(f"{time.time()}|{work}".encode()).hexdigest()[:16]
        _write(work / "words.json", {"send": w["blender_model_send"], "sent": w["decoy_blender_sent"],
                                     "hint": [w["blender_anim_hint1"], w["blender_anim_hint2"]],
                                     "hint_animations": [], "nla": w["decoy_blender_nla"], "session": session})
        # (a new opening: nothing brought back from it yet, nothing it wrote)
        _write(work / STATE, {"session": session, "file": str(start)})
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        message = w["decoy_blender_opened"].format(n=len(rows))
        if set_aside is not None:
            message += " " + w["decoy_blender_set_aside"].format(folder=str(set_aside))
        return {**self.decoy_blender_state(address, lang), "opened": len(rows), "file": str(start),
                "set_aside": str(set_aside) if set_aside is not None else None, "message": message}

    # --- and back ---
    def _aside_folder(self, work: Path, aside: str) -> Path:
        """The set-aside sending `aside` names (decoy_blender_state's "aside": a folder of the work folder's)."""
        from .api import StudioError
        name = str(aside or "")
        folder = work / name
        if Path(name).name != name or not name.startswith(ASIDE) or folder not in self._asides(work):
            # not a game rule: the Studio's own folder of what Blender sent
            raise StudioError(f"There's no sending set aside called {name} for this unit any more.")
        return folder

    def decoy_blender_back(self, address: str, lang: str = "us", aside: str | None = None) -> dict:
        """Bring my changes back: the open Blender is asked to send (a closed one's last sending is used); each
        animation that came back changed becomes the unit's own clip for every action of every figure that played it,
        or, one of its model's own animations, takes that animation's place by name; one changed and brought back
        before since Blender opened, and undone in Blender since, is put back as it went out (see the module's note).
        `aside`: bring back the sending kept aside under that name instead (decoy_blender_state's "aside"; it goes once
        brought back). Refused, in words, nothing written: nothing sent from this Blender yet, nothing went out from it,
        a file not on the bones its animations went out on, a bone of them renamed or deleted in Blender, the model or
        one of its changed animations not as it went out. Returns decoy_blender_state's answer with "changed",
        "undone" (names), "same" (how many came back as the mod plays them), "new", "gone" (names), "written" (how many
        were kept), "new_bones", "halves" (changes the game may not play, said), "nla", "fps" (None: the game's) and
        "message"."""
        from rusemod import anim, baf, rig
        from rusemod.blender import ask_to_send
        from rusemod.modelin import ModelError, glb_document
        from . import animblender
        from .api import StudioError, words
        w = words(lang)
        work = self._anim_work(address)
        if work is None:
            raise StudioError(w["decoy_blender_why_game"])
        folder = work if aside is None else self._aside_folder(work, aside)
        send = folder / SEND
        if aside is None and self._anim_open(work):   # its Blender is open: it sends what it has now
            if ask_to_send(send, SEND_WAIT) is None:
                raise StudioError("Blender didn't answer in time: in Blender, click Send to the R.U.S.E. Studio at the "
                                  "top, then bring your changes back again.")
        sent = animblender.read_sent(folder)
        state = _read(folder / STATE)
        if not send.is_file() or sent is None:
            # not a game rule: the Studio's own hand-over from Blender, nothing sent from this Blender yet
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring my changes back here.")
        sha = _sha(send)
        empty = {"changed": [], "undone": [], "same": 0, "new": [], "gone": [], "written": 0, "new_bones": [],
                 "halves": [], "nla": [], "fps": None}
        unit = animblender.unit_name(self._own_model_file(address))
        mod = self._mod_dir()
        went = {a["name"]: a for a in sent["animations"]}
        # what bring backs since Blender opened wrote, while the mod still has it (RUSE Decoy or Import model may have
        # changed it since: then this sending is taken in again, as Blender shows it)
        kept = state.get("wrote") if isinstance(state.get("wrote"), dict) else {}
        wrote = {n: p for n, p in kept.items() if n in went and isinstance(p, dict)
                 and self._in_force(mod, unit, went[n], p)}
        if sha == state.get("brought") and len(wrote) == len(kept):
            # (brought back already and the mod as it left it: nothing new came from Blender since)
            return {**self.decoy_blender_state(address, lang), **empty, "message": w["decoy_blender_nothing_new"]}
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
        spelled = {str(n.get("name") or "").lower(): str(n.get("name")) for n in doc.get("nodes") or []}
        new_bones = [spelled.get(n, n) for n in back.new]      # (as the modder spelled them in Blender)
        if back.missing:
            # not a game rule: the animations are on the unit's own skeleton, and which bone a renamed one was can't be
            # told (a deleted one's points don't move in Blender as the game would move them)
            missing = ", ".join(back.missing)
            if back.new:
                raise StudioError(f"These bones of this unit's skeleton didn't come back from Blender: {missing}, and "
                                  f"these came back that it hasn't got: {', '.join(new_bones)}. A bone renamed or "
                                  f"deleted there can't be taken back into its animations, so nothing was taken in: "
                                  f"give the bones their names back in Blender (or undo deleting them), click Send to "
                                  f"the R.U.S.E. Studio, then bring your changes back again.")
            raise StudioError(f"These bones of this unit's skeleton didn't come back from Blender: {missing}. A bone "
                              f"renamed or deleted there can't be taken back into its animations, so nothing was taken "
                              f"in: give the bones their names back in Blender (or undo deleting them), click Send to "
                              f"the R.U.S.E. Studio, then bring your changes back again.")
        about = _read(folder / ABOUT)
        if about.get("glb") != sha:       # (said of another sending, or of none)
            about = {}
        if about.get("session") and state.get("session") and about["session"] != state["session"]:
            # not a game rule: a Blender left open from an earlier opening (the Studio restarted meanwhile) sent it,
            # made from what went out then, not from what went out last
            raise StudioError("What came back was sent by a Blender opened before the last Change its animations in "
                              "Blender, so it can't be taken in: close that Blender, then in the one opened last click "
                              "Send to the R.U.S.E. Studio and bring your changes back.")
        rate = rig.sampled_rate(r)
        if rate is not None and abs(rate - baf.FPS) <= baf.FPS * RATE_NEAR:
            rate = None                   # (the game's own 30 a second)
        came = animblender.file_animations(send)
        out = {**empty, "new": [n for n in came if n not in went], "gone": [n for n in went if n not in came],
               "new_bones": new_bones, "nla": [n for n in about.get("nla") or [] if isinstance(n, str)],
               "fps": rate}
        by_action, by_name, allowed, models, bones = [], {}, {}, [], {}
        last = False        # (one came back as last brought back, not as it went out)
        seen = set()
        for got in rig.clips_back(r, back, sent["record"], {n: a["clip"] for n, a in went.items()}, rate=rate):
            name, a = got["name"], went.get(got["name"])
            if a is None:
                continue
            seen.add(name)
            prev = wrote.get(name)
            if (got["same"] if prev is None else _sha_of(got["clip"]) == prev.get("sha")):
                out["same"] += 1    # (as the mod plays it now)
                last = last or prev is not None
                continue
            undo = got["same"]      # (as it went out again: a change brought back before, undone in Blender since)
            if undo:
                out["undone"].append(name)
            else:
                out["changed"].append(name)
                bones[name] = got["changed"]
            clip = a["clip"] if undo else got["clip"]
            if a.get("model_animation"):
                by_name[a["model_animation"]] = clip
                allowed[a["model_animation"]] = {_sha_of(a["clip"])} | ({prev["sha"]} if prev else set())
                models.append((name, undo, clip))
            else:
                by_action.append((name, a, clip, undo, prev))
        # (one that came back under its name but moved no bone the game has is one that didn't come back)
        out["gone"] += [n for n in went if n in came and n not in seen]
        clips = self._model_animations_back(address, sent, by_name, allowed) if by_name else None
        current = None
        try:
            with self._saving:
                before = anim.files_named(mod, unit)
                taken: set = set()
                for name, a, clip, undo, prev in by_action:
                    current = name
                    if undo:
                        self._undo_action(mod, unit, a, prev)
                        wrote.pop(name, None)
                    else:
                        wrote[name] = self._write_action(mod, unit, a, clip, prev, taken)
                    out["written"] += 1
                current = None
                if clips is not None:
                    files = anim.set_animations(mod, unit, clips)
                    self._record_lengths(address, clips, files)
                    for name, undo, clip in models:
                        if undo:
                            wrote.pop(name, None)
                        else:
                            wrote[name] = {"sha": _sha_of(clip)}
                    out["written"] += len(models)
                anim.drop_unnamed(mod, unit, before)
        except (anim.AnimError, OSError) as exc:
            if aside is None:       # (what was written is kept in the state: an undo in Blender still undoes it)
                _write(folder / STATE, {**state, "wrote": wrote})
            if current is not None:
                raise StudioError(f"{current}: {exc}") from None
            raise StudioError(str(exc)) from None
        if aside is None:
            _write(folder / STATE, {**state, "brought": sha, "wrote": wrote})
        else:                       # (taken in: kept aside no more)
            shutil.rmtree(folder, ignore_errors=True)
        sep = w["blender_squad_list_sep"]
        if sent.get("model") == "own":
            out["halves"] = self._halves_unplayed(address, sent, bones, sep)
        said = []
        if out["changed"]:
            said.append(w["decoy_blender_changed"].format(names=sep.join(out["changed"])))
        if out["undone"]:
            said.append(w["decoy_blender_undone"].format(names=sep.join(out["undone"])))
        if not out["changed"] and not out["undone"] and out["same"]:
            said.append(w["decoy_blender_same_rest"] if out["gone"] or last else w["decoy_blender_same"])
        if out["halves"]:
            said.append(w["decoy_blender_halves"].format(names=sep.join(out["halves"])))
        if out["new"]:
            said.append(w["decoy_blender_new"].format(names=sep.join(out["new"])))
        if out["gone"]:
            said.append(w["decoy_blender_gone"].format(names=sep.join(out["gone"])))
        if out["new_bones"]:
            said.append(w["decoy_blender_new_bones"].format(names=sep.join(out["new_bones"])))
        if out["nla"]:
            said.append(w["decoy_blender_nla"].format(names=sep.join(out["nla"])))
        if rate is not None:
            said.append(w["decoy_blender_fps"].format(fps=_fps_text(rate)))
        return {**self.decoy_blender_state(address, lang), **out, "message": " ".join(said)}

    @staticmethod
    def _in_force(mod: Path, unit: str, a: dict, prev: dict) -> bool:
        """Whether what a bring back since Blender opened wrote of an animation (`prev`, the state's "wrote") is what the
        mod plays now: one of the model's own animations, its file by name with those bytes; an action's own clip,
        every figure's row for its actions naming that file, with those bytes. False once anything else changed it."""
        from rusemod import anim
        try:
            if a.get("model_animation"):
                f = anim.own_animations(mod, unit)["animations"].get(a["model_animation"])
            else:
                table = anim.read_units(mod).get(unit) or {}
                rows = {_figure_row(table, fig, key) for fig, keys in (a.get("actions") or {}).items() for key in keys}
                f = prev.get("file") if rows == {prev.get("file")} else None
        except anim.AnimError:
            return False
        return isinstance(f, str) and _sha(Path(mod) / anim.OWN / unit / f) == prev.get("sha")

    # --- an animation an action plays: the unit's own clip, kept in one file ---
    @staticmethod
    def _action_file(table: dict, a: dict, taken: set) -> str:
        """The file a changed animation an action plays is kept in (unit_plays' row `a`; `table`: the unit's in
        units.toml now; `taken`: the files other animations of this bring back took, lower case): the unit's own file
        it went out as, written again in its place, while every row naming it is one of the animation's own actions;
        else blender_<the clip's name>.baf, with _2, _3... when another row of the unit, or another animation, has
        that name. So the same animation is in the same file each round, and two never share one."""
        from rusemod import anim
        from . import animblender
        mine = {(fig, key) for fig, keys in a["actions"].items() for key in keys}
        keys = {key for _fig, key in mine}

        def others(file: str) -> bool:      # (a row naming it that isn't one of this animation's actions)
            low = file.lower()
            for fig, fv in (table.get("figure") or {}).items():
                for key, f in ((fv or {}).get("action") or {}).items():
                    if str(f).lower() == low and (fig, key) not in mine:
                        return True
            if any(str(f).lower() == low and key not in keys for key, f in (table.get("action") or {}).items()):
                return True
            rest = {str(f).lower() for f in (table.get("animation") or {}).values()}
            rest |= {str((e or {}).get("file") or "").lower() for e in (table.get("clip") or {}).values()}
            return low in rest
        own = a.get("own")
        if own and _SAFE_FILE.match(own) and own.lower() not in taken and not others(own):
            return own
        stem = re.sub(r"^(blender_)+", "", animblender.stem_of(a.get("member") or own or a["name"]))
        base = anim._file_name(f"blender_{stem}")[:-len(".baf")]
        file, k = f"{base}.baf", 2
        while file.lower() in taken or others(file):
            file, k = f"{base}_{k}.baf", k + 1
        return file

    def _write_action(self, mod: Path, unit: str, a: dict, clip: bytes, prev: dict | None, taken: set) -> dict:
        """The changed clip `clip` of an animation actions play (unit_plays' row `a`) as the unit's own for every action
        of every figure that played it (rusemod.anim.add_unit_clip), in _action_file's file. Returns what the state's
        "wrote" keeps of it: {"sha": the clip's, "file", "before": [[figure, action, the file that figure's own row for
        it named before the door first wrote it since Blender opened, or None: none]]} (`prev`: the last of it)."""
        from rusemod import anim
        table = anim.read_units(mod).get(unit) or {}
        file = self._action_file(table, a, taken)
        before = prev["before"] if prev else [[fig, key, _figure_row(table, fig, key)]
                                              for fig, keys in a["actions"].items() for key in keys]
        for fig, keys in a["actions"].items():
            for key in keys:
                anim.add_unit_clip(mod, unit, key, clip, name=file[:-len(".baf")], figure=fig)
        taken.add(file.lower())
        return {"sha": _sha_of(clip), "file": file, "before": before}

    @staticmethod
    def _undo_action(mod: Path, unit: str, a: dict, prev: dict) -> None:
        """An animation's own clip brought back since Blender opened, undone in Blender since: each figure's row for
        each of its actions as it was before (`prev`, _write_action's), and the unit's own file it went out as (one
        written in its place) as it went out. A file no row names any more goes after (drop_unnamed)."""
        from rusemod import anim
        table = anim.read_units(mod)
        u = dict(table.get(unit) or {})
        figs = {k: dict(v or {}) for k, v in (u.get("figure") or {}).items()}
        for fig, key, value in prev.get("before") or []:
            acts = dict((figs.get(fig) or {}).get("action") or {})
            if value is None:
                acts.pop(key, None)
            else:
                acts[key] = value
            if acts:
                figs[fig] = {"action": acts}
            else:
                figs.pop(fig, None)
        u["figure"] = figs
        u = {k: v for k, v in u.items() if v}
        if u:
            table[unit] = u
        else:
            table.pop(unit, None)
        own = a.get("own")
        if own and own == prev.get("file") and _SAFE_FILE.match(own):    # (its own file, written in its place)
            f = Path(mod) / anim.OWN / unit / own
            part = f.with_name(f.name + ".part")
            part.write_bytes(bytes(a["clip"]))
            os.replace(part, f)
        anim.write_units(mod, table)

    # --- a model on bones of its own ---
    def _halves_unplayed(self, address: str, sent: dict, bones: dict, sep: str) -> list:
        """For a model on bones of its own, each animation that came back changed on bones the game may not play from
        it ("<its name> (<those bones>)"): one played on one half of the body only, changed on bones of the other half
        (the build's two masks for the model: rusemod.bonefit.halves_for). A model's own animation plays on one half
        when its name is made for that half (rusemod.animactions.marked: t_ or b_, after what all its names start with)
        and no action picks it (a pick plays on both); one an action's own row plays, when every one of its actions is
        that half's (t_ or b_). Read from the build's rules, not tried in the game (`bones`: {name: the bones whose
        track came back changed})."""
        from rusemod import anim, animactions, bonefit
        from rusemod.unitmodel import UnitModelError
        from . import animblender
        own = self._own_model_file(address)
        try:
            halves = bonefit.halves_for(Path(own)) if own is not None else None
        except (bonefit.FitError, UnitModelError, OSError, ValueError, KeyError, IndexError, struct.error):
            halves = None   # (its halves can't be told: nothing said of them)
        if not halves:
            return []
        weighed = {h: {n.lower() for n in halves[h]["Weights"]} for h in ("top", "bottom")}
        model = [a["model_animation"] for a in sent["animations"] if a.get("model_animation")]
        marks = animactions.marked(model) if model else {}
        try:
            picked = set(anim.own_animations(self._mod_dir(), animblender.unit_name(own))["plays"].values())
        except anim.AnimError:
            picked = set()
        went = {a["name"]: a for a in sent["animations"]}
        out = []
        for name, changed in bones.items():
            a = went.get(name) or {}
            if a.get("model_animation"):
                n = a["model_animation"]
                half = None if n in picked else marks.get(n, (None, None))[1]
            else:
                sides = {animactions.parse_key(k)[0] for ks in (a.get("actions") or {}).values() for k in ks}
                half = next(iter(sides)) if len(sides) == 1 else None
            if half not in weighed:
                continue
            unplayed = [b for b in changed if b.lower() not in weighed[half]]
            if unplayed:
                out.append(f"{name} ({sep.join(unplayed)})")
        return out

    def _model_animations_back(self, address: str, sent: dict, by_name: dict, allowed: dict) -> dict:
        """The model's own animations to keep after a bring back (rusemod.anim.set_animations' `clips`): the mod's as
        they are now, each that came back changed (`by_name`: {its name: the clip}) in its place; when they went out
        from the model's file (the mod had none), every one that went out, as Import model takes them in. Refused,
        nothing written, when the model's bones, or one of those animations, changed after they went out: the mod's
        clip for each of `by_name` must be one of `allowed`'s ({its name: the SHA-256 of what went out, and of what a
        bring back since Blender opened wrote})."""
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
                or (clips and any(_sha_of(clips.get(n) or b"") not in allowed.get(n, set()) for n in by_name)):
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
