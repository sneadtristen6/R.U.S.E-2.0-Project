"""A new unit's model changed in Blender and brought back (StudioApi's ModelBlenderCalls; the owner's order of
2026-11-10, item 4: a player couldn't give a squad a model of his own; scratch/animmodels/item4/FINDINGS.md).

Change it in Blender (model_blender) writes the unit's model with its bones at their real places (rusemod.gltf's
rest_bones) into the unit's work folder, <mod>/blender/<the unit's name>/, and opens it in Blender
(rusemod.blender_model): the modder changes it there, or brings in a model of his own and puts it on the bones with
Blender's own tools, then clicks Send to the R.U.S.E. Studio. Bring back the model (model_blender_back) asks that Blender
to send it (rusemod.blender.ask_to_send) and takes it in with Import model, as the unit's own model.
The work folder sits beside the mod's src/ and files/: Export doesn't pack it (rusemod.package), the build doesn't read
it, and the modder finds his Blender files there. What was sent last is where the next Change it in Blender starts;
before anything was sent, a unit with a model of its own starts from that model (the owner, 2026-11-13, "yes" to the
Generic Horse's Change it in Blender opening its own model: its horse, its rider, its bones and its animations), as the
squad page's Change the squad in Blender starts a soldier from his; a unit without one, from the game's model.
Unlike Open in Blender in the Look box, this needs no Custom uniform: it changes the unit's own model, never the game's
pictures that other units wear.
Each of a squad's soldiers has his own (the owner, 2026-11-11, on the step-4 test copy: the big-head squad's bazooka
man "did not get scaled", then "edit any individual in like a normal rifleman squad ... inside Blender. Or add a new
model or attach it with bones"): the Model row's buttons are the riflemen's, and a squad whose heavy-weapon soldier
draws another model gives him his own pair under Its soldiers (`kind`: StudioApi._soldier_kinds). His work folder is
<mod>/blender/<the unit's name>@<kind>/, beside his model file files/models/<the unit's name>@<kind>.glb, and what he
sends back is his model alone (Import model's `kind`). A squad has as many looks as the game's unit data gives it: one
model every one of its riflemen wears, and one for its heavy-weapon soldier.

A tank, a plane or a soldier changed in Blender keeps its own shine and side colour (the owner, 2026-11-12, "Keep its
own": its own shine and side-colour layer goes back in, the way the squad page already does it). In the game's
pictures the alpha is the shine where high and the side colour (the team tint) where low; Blender shows it nowhere.
The game's model goes out with each picture's alpha as a picture of its own beside it (rusemod.gltf.export), and
Blender's export keeps no picture a material doesn't show and no extras, so what it sends has none: Import model
gave such a model the plain 144 an outside model gets (measured with Blender 4.5 on 2026-11-11: the bazooka man's
picture came back "plain 144"). So Change it in Blender notes which alpha picture went out with each material
(alpha.json in the work folder, by the material's name), and Bring back the model puts each back in what Blender sent,
by that name (rusemod.gltf.with_alpha, the squad page's), as <work>/kept/<its name>.glb: the file Import model takes
in, and Resize and Move fit again from. A material that comes back under a name none went out with (renamed or new in
Blender) has the plain 144, and the import's report says so ("blender_alpha", and its notes). A model imported from a
file keeps the plain 144 as before (the owner, the same day: "Keep it flat").

A model on bones of its own (the Generic Horse's horse and rider) goes out with the animations the mod plays for the
unit (files/anim/units.toml, files/anim/own/<unit>/: RUSE Decoy changes them there, never in the model's file), and
each animation that comes back as it went out is the mod's own clip again, byte for byte, a changed one differing only
in the bones changed (the owner, 2026-11-13, item 45: "Yes, an animation that comes back from Bundler should come back
the exact same"; before, a trip with nothing changed rewrote all 25 of the Generic Horse's animation files, a key at
every frame). Change it in Blender writes them into the file Blender opens keyed where Blender needs a key to show
every frame as the game plays it (rusemod.modelin.own_animations_into), and keeps each clip that went out beside the
work file (ruse_studio.animblender.write_sent); Bring back the model puts the skeleton record and those clips back in
what Blender sent (rusemod.rig.with_record, with_went_out: Blender keeps no extras), in the order they went out, so the
mod's list of them stays; the import keeps them (ruse_studio.animmodel_calls._went_out_kept, rusemod.rig.kept_clip),
and so does every Resize and Move after, which fit the model again from that file.

What a Bring back couldn't keep is shown to the modder on the page, in his language (a review of 2026-11-12 found it
said only in the import's report and the model's record, which no page read): the report's "blender_alpha_lost" lists
by name each material that came back with the plain 144 because no alpha picture went out under its name ("none",
rusemod.gltf.ALPHA_NONE: renamed or new in Blender here; new there on the squad page, whose Blender carries a renamed
material's picture with it), because its alpha picture is gone from the Blender folder ("gone"), and each that went out
with one and didn't come back under that name ("not_back"); Import model's own "alpha_sizes" (rusemod.modelin) each
picture whose alpha picture isn't its size (a picture swapped in Blender for one of another size), so has the plain 144
too. Both doors write them (the squad page's Bring my changes back too: ruse_studio.squadblender), the model's record
keeps them, through a Resize or a Move as well (keep_said: the same file fitted again has the same loss), look()'s
own_model and kinds rows and squad_info's soldiers carry them (alpha_lost), and the page says them (app.js
alphaLostLines): in the Bring back's pop-up, and beside the model for as long as it has them."""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from .animmodel_calls import read_record, write_record


def _read_json(path: Path) -> dict:
    """A small JSON file of the work folder as a dict ({} when it isn't there or isn't one)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


WORK = "blender"
SEND_WAIT = 60.0   # seconds Bring back the model waits for an open Blender to send
ALPHA = "alpha.json"   # in the work folder: the alpha picture that went out with each material, by the material's name
KEPT = "kept"          # <work>/kept/<its name>.glb: what Bring back the model took in, each alpha picture back in it
# a squad's second figure carries the heavy weapon: the rifleman is the one to change, and what comes back is the
# riflemen's model (Import model's first kind; the heavy-weapon soldier keeps the copied unit's until he gets his own,
# the owner, 2026-11-11: "when you copy a fucking unit, it should copy the unit")
HEAVY = re.compile(r"bazooka|panzerschreck|piat|flame|lanceflamme|mortier|mortar", re.I)
LOST = ("blender_alpha_lost", "alpha_sizes")   # what an import's report says it couldn't keep (alpha_lost)
SAID = ("blender_alpha", "blender_alpha_lost")  # what _alpha_said adds to a report (keep_said carries them)


LOST_KINDS = ("none", "gone", "not_back")   # "blender_alpha_lost"'s lists
# what a Studio from before "blender_alpha_lost" (07a688b5, the shine door) wrote in "blender_alpha" and in its notes,
# word for word: read back so its record still says it on the page and through a Resize (the one check, finding 7)
OLDER_SAID = {"none": "no alpha picture went out to Blender with a material of this name",
              "gone": "the alpha picture that went out with it isn't in its Blender folder any more"}
OLDER_NOT_BACK = "Went out to Blender with an alpha picture and didn't come back under that name: "


def _said(report) -> dict:
    """A report's "blender_alpha" ({material: its word}) as this Studio reads it: {} for one of another shape, a
    material that isn't named by a word left out (a record edited by hand: a field of the wrong shape is one that isn't
    there, never Python's own error: the one check, finding 2)."""
    said = report.get("blender_alpha") if isinstance(report, dict) else None
    if not isinstance(said, dict):
        return {}
    return {m: w for m, w in said.items() if isinstance(m, str) and isinstance(w, str)}


def lost_of(report) -> dict:
    """A report's "blender_alpha_lost" ({"none", "gone", "not_back"}: lists of materials' names) as this Studio reads
    it: a list that isn't one of names left out, one of another shape as if it weren't there. A record from a Studio
    before "blender_alpha_lost" (it has "blender_alpha" and no "blender_alpha_lost") says the same in "blender_alpha"'s
    words and in its notes: read from them (OLDER_SAID; "not_back" from its note, its names as the note lists them,
    split at ", ")."""
    if not isinstance(report, dict):
        return {}
    lost = report.get("blender_alpha_lost")
    if isinstance(lost, dict):
        out = {k: [m for m in lost.get(k) if isinstance(m, str)] for k in LOST_KINDS if isinstance(lost.get(k), list)}
        return {k: v for k, v in out.items() if v}
    if "blender_alpha_lost" in report:   # (one of another shape: not there)
        return {}
    out = {k: [m for m, w in _said(report).items() if phrase in w] for k, phrase in OLDER_SAID.items()}
    notes = report.get("notes") if isinstance(report.get("notes"), list) else []
    for note in notes:
        if _said(report) and isinstance(note, str) and note.startswith(OLDER_NOT_BACK):
            out["not_back"] = [m for m in note[len(OLDER_NOT_BACK):].rstrip(".").split(", ") if m]
    return {k: v for k, v in out.items() if v}


def alpha_lost(report) -> dict:
    """Of an import's report (a model's record's "report"), what it says couldn't be kept of the model's own shine and
    side colour, for the page (app.js alphaLostLines): "blender_alpha_lost" (lost_of: an older Studio's record's too)
    and "alpha_sizes", those it has."""
    if not isinstance(report, dict):
        return {}
    out = {"blender_alpha_lost": lost_of(report)}
    sizes = report.get("alpha_sizes")
    if isinstance(sizes, list):
        out["alpha_sizes"] = json.loads(json.dumps([s for s in sizes if isinstance(s, dict)]))
    return {k: v for k, v in out.items() if v}


def blender_notes(report: dict) -> list:
    """The import's notes (in the record, in English) on what came back from Blender with the plain 144: each material
    that came back without an alpha picture of its own, in the order Blender sent them ("blender_alpha"), and each that
    went out with one and didn't come back under its name ("blender_alpha_lost")."""
    from rusemod.modelin import PLAIN_ALPHA
    lost = lost_of(report)
    flat_names = {str(m) for k in ("none", "gone") for m in lost.get(k) or []}
    flat = [m for m in _said(report) if str(m) in flat_names]
    notes = []
    if flat:
        notes.append(f"Back from Blender without an alpha picture of their own, so with the plain {PLAIN_ALPHA} (no "
                     f"shine or side colour of their own): {', '.join(str(m) for m in flat)}.")
    if lost.get("not_back"):
        notes.append(f"Went out to Blender with an alpha picture and didn't come back under that name: "
                     f"{', '.join(str(m) for m in lost['not_back'])}.")
    return notes


def keep_said(before, report: dict) -> None:
    """A Resize or a Move fits the model again from the file it was made from (StudioApi._fit_model): what its Bring
    back said it couldn't keep (_alpha_said, in the record's report `before`) is still so, as that file is the same, so
    the new `report` says it too (in the record and to the page), as the Custom uniform a model took the place of stays
    kept through them. Nothing for a model that didn't come back from Blender."""
    if not isinstance(before, dict) or not isinstance(report, dict):
        return
    # (read as this Studio reads them: a field of the wrong shape is one that isn't there, never Python's own error, the
    # one check's finding 2; an older Studio's record, "blender_alpha" alone, says it through lost_of and is written
    # from now on with "blender_alpha_lost" too, its finding 7)
    said, lost = _said(before), lost_of(before)
    if not said and not lost:
        return
    if said:
        report["blender_alpha"] = dict(said)
    if lost:
        report["blender_alpha_lost"] = lost
    notes = report.get("notes") if isinstance(report.get("notes"), list) else []
    report["notes"] = notes + [n for n in blender_notes(report) if n not in notes]


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

    @staticmethod
    def _alphas_out(start: Path, summary: dict) -> dict:
        """{each material's name in the game model's file `start`: the alpha picture rusemod.gltf.export wrote beside it
        for that material's texture (its file name: `summary`'s picture_of)}; none for a file it can't read."""
        from rusemod.modelin import glb_document
        alpha_of = {member: name for name, (member, what) in (summary.get("picture_of") or {}).items()
                    if what == "alpha"}
        try:
            doc, _bin = glb_document(Path(start).read_bytes())
        except (OSError, ValueError, struct.error):
            return {}
        out = {}
        for mat in doc.get("materials", []):
            member = (mat.get("extras") or {}).get("rusemod_texture")
            if isinstance(mat.get("name"), str) and member in alpha_of:
                out.setdefault(mat["name"], alpha_of[member])
        return out

    @staticmethod
    def _alphas_back(work: Path, send: Path, raw: bytes) -> dict:
        """{a material's name: the alpha picture that went out to Blender with it (its path in the work folder)}, as
        alpha.json lists them; for a work folder from before alpha.json, each material of the sending `raw` whose alpha
        picture rusemod.gltf.export wrote beside the game model's file (<that file's name>_<the material's
        name>_alpha.png), when one only is there."""
        from rusemod.modelin import glb_document
        from .squadblender import _read
        listed = _read(work / ALPHA).get("alpha")
        if isinstance(listed, dict):
            return {m: work / f for m, f in listed.items()
                    if isinstance(m, str) and isinstance(f, str) and f and Path(f).name == f}
        try:
            doc, _bin = glb_document(raw)
        except (ValueError, struct.error):
            return {}
        stems = [p.stem for p in work.glob("*.glb") if p.name != send.name]
        out = {}
        for mat in doc.get("materials", []):
            name = mat.get("name")
            if not isinstance(name, str) or not name or "/" in name or "\\" in name:   # (a file of this folder only)
                continue
            found = [work / f"{s}_{name}_alpha.png" for s in stems if (work / f"{s}_{name}_alpha.png").is_file()]
            if len(found) == 1:
                out[name] = found[0]
        return out

    def _alpha_said(self, address: str, kind: str | None, res: dict, got: dict, went: dict,
                    lost: list | None = None) -> None:
        """Import model's report of what Bring back the model took in (res["model"]), and the model's record beside it,
        told what each material Blender sent got for alpha ("blender_alpha": `got`, rusemod.gltf.with_alpha's word on
        each), and in its notes which have the plain 144 and why, and which went out (`went`) and didn't come back
        under their names (`lost`: those that didn't come back, when the door knows better than by name: the squad
        page's, whose Blender carries a renamed material's alpha with it): no material's shine and side colour lost
        without a word. The same for the page, by name, in "blender_alpha_lost" ({"none", "gone", "not_back"}: see the
        module's note), and in the answer's look() parts drawn from the record (own_model, a kind's row)."""
        from rusemod.gltf import ALPHA_BACK, ALPHA_GONE, ALPHA_NONE
        from rusemod.modelin import PLAIN_ALPHA
        report = res.get("model")
        if not isinstance(report, dict) or not (got or went):
            return
        plain = f"plain {PLAIN_ALPHA}"
        said = {ALPHA_BACK: "its own, put back",
                ALPHA_NONE: f"{plain}: no alpha picture went out to Blender with a material of this name (renamed or "
                            f"new there)",
                ALPHA_GONE: f"{plain}: the alpha picture that went out with it isn't in its Blender folder any more"}
        report["blender_alpha"] = {m: said[g] for m, g in got.items()}
        lost = [m for m in went if m not in got] if lost is None else list(lost)
        page = {"none": [m for m, g in got.items() if g == ALPHA_NONE],
                "gone": [m for m, g in got.items() if g == ALPHA_GONE], "not_back": lost}
        page = {k: v for k, v in page.items() if v}
        if page:
            report["blender_alpha_lost"] = page
        else:
            report.pop("blender_alpha_lost", None)
        report.setdefault("notes", []).extend(blender_notes(report))
        target = self._kind_file(address, kind) if kind else self._own_model_file(address)
        record = target.with_suffix(".json") if target is not None else None
        data = read_record(record) if record is not None else None
        if data:   # (as Import model wrote it, with this said too)
            from .api import file_error
            data["report"] = report
            try:
                write_record(record, data)   # (whole or not at all)
            except OSError as exc:   # (said in words, never in Python's own)
                raise file_error(exc, record) from exc
            if not kind and "own_model" in res:   # (look()'s, read before this was said)
                res["own_model"] = json.loads(json.dumps(report))
            # (look()'s row of his kind in the answer, the riflemen's the first: read before this was said too)
            rows = [r for r in res.get("kinds") or [] if isinstance(r, dict)]
            for row in [r for r in rows if r.get("kind") == kind] if kind else rows[:1]:
                for k in LOST:
                    row.pop(k, None)
                row.update(alpha_lost(report))

    def _own_start(self, own: Path, work: Path, animations: dict | None = None) -> tuple[Path, dict, bool]:
        """The unit's own model (`own`: files/models/<unit>.glb, or a kind's), as Change it in Blender starts from it,
        the way Change the squad in Blender starts a soldier from his (ruse_studio.squadblender._start_file, "model"):
        a model on bones of its own (the Generic Horse's horse and rider) as it is, its animations those the mod plays
        (`animations`, {name: what Blender is given of the clip}: _going_out) in place of the ones its file carries
        (rusemod.modelin.own_animations_into; RUSE Decoy changes them in the mod, never in that file), one on the game
        soldier's bones with them put at their rest poses (rusemod.gltf.rest_bones_glb). Each material's alpha
        picture (Import model keeps it in the file, its "rusemod_alpha_texture") is written beside it and listed by
        the material's name for Bring back the model (alpha.json; Blender keeps no picture a material doesn't show),
        each material named once. Returns (the file, {material: its alpha picture's file name in `work`}, whether
        `animations` went in: not when its file isn't on their bones, so its own went as before)."""
        import struct as _struct
        from rusemod import gltf, models
        from rusemod.modelin import ModelError, own_animations_into
        from .api import StudioError, file_error
        from .squadblender import _put
        try:
            raw = own.read_bytes()
        except OSError as exc:      # (said in words, never in Python's own)
            raise file_error(exc, own) from exc
        record = read_record(own.with_suffix(".json"))
        record = record if isinstance(record, dict) else {}
        try:
            doc, views = gltf.glb_views(raw)
        except (ValueError, _struct.error) as exc:   # (his model file unreadable: said, never another model opened)
            raise StudioError(f"{own.name}: {exc}") from None
        if record.get("skeleton") != "own":   # (a model on bones of its own carries its whole skeleton at rest)
            report = record.get("report") if isinstance(record.get("report"), dict) else {}
            like = report.get("like") or ((doc.get("asset") or {}).get("extras") or {}).get("rusemod_like")
            if isinstance(like, str) and like:
                lib = models.Library(self._game())
                try:
                    skeleton = lib.skeleton(like) if hasattr(lib, "skeleton") else None
                finally:
                    lib.close()
                placed = gltf.rest_bones_glb(raw, skeleton) if skeleton is not None else None
                if placed:
                    doc, views = gltf.glb_views(placed)
        alphas, names = {}, set()
        for k, mat in enumerate(doc.get("materials", [])):
            name = mat.get("name") if isinstance(mat.get("name"), str) and mat.get("name") else f"{own.stem} {k + 1}"
            while name in names:            # (named once: Bring back puts each alpha back by the material's name)
                name = f"{name} {k + 1}"
            names.add(name)
            mat["name"] = name
            extras = mat.get("extras") if isinstance(mat.get("extras"), dict) else {}
            index = extras.pop("rusemod_alpha_texture", None)
            try:
                data = views[doc["images"][doc["textures"][index]["source"]]["bufferView"]] \
                    if isinstance(index, int) else None
            except (IndexError, KeyError, TypeError):
                data = None                 # (an alpha the file names but hasn't: the plain 144, as an import says)
            if data is not None:
                file = f"{own.stem}_{k + 1}_alpha.png"
                try:
                    _put(work / file, data)
                except OSError as exc:      # (said in words, never in Python's own)
                    raise file_error(exc, work / file) from exc
                alphas[name] = file
            if extras:
                mat["extras"] = extras
            else:
                mat.pop("extras", None)
        put = False
        if animations and record.get("skeleton") == "own":
            try:
                own_animations_into(doc, views, animations, blender=True)
                put = True
            except (ModelError, ValueError, KeyError, IndexError, TypeError, _struct.error):
                put = False     # (its file isn't on the bones of the mod's animations: its own go, as before)
        start = work / f"{own.stem}_own.glb"
        try:
            _put(start, gltf.pack_glb(doc, views))
        except OSError as exc:              # (said in words, never in Python's own)
            raise file_error(exc, start) from exc
        return start, alphas, put

    def _going_out(self, own: Path) -> list:
        """The animations a model on bones of its own goes out to Blender with: those the mod plays for the unit
        (files/anim/units.toml [unit.<name>.animation], its clip files: AnimModelCalls._own_now), in the mod's order,
        as rows for ruse_studio.animblender.write_sent ([{"name", "clip", "blender_clip": what Blender is given of it,
        on the game's 30 frames a second (animblender.on_game_frames), "member": None, "own": its file, "actions":
        {}}]). [] for a model that isn't on bones of its own, or a unit with none in the mod (its file's own go)."""
        from rusemod import anim
        from . import animblender
        record = read_record(own.with_suffix(".json"))
        mod = self._mod_dir()
        if not isinstance(record, dict) or record.get("skeleton") != "own" or mod is None:
            return []
        mine, _picks = self._own_now(mod, own.stem)
        try:
            files = anim.own_animations(mod, own.stem)["animations"]
        except anim.AnimError:
            files = {}
        if not mine or set(mine) != set(files):   # (one its list names that can't be read: its file's own go, as
            return []                              # before, and the fit says what it can't read)
        rows = []
        for name, clip in mine.items():
            try:
                given = animblender.on_game_frames(clip)
            except (ValueError, IndexError, struct.error):   # (a clip file of the mod's that isn't one: its file's
                return []                                     # own go, as before, and the fit says what it can't read)
            rows.append({"name": name, "clip": clip, "blender_clip": given, "member": None, "own": files.get(name),
                         "actions": {}})
        return rows

    @staticmethod
    def _again(send: Path, work: Path, own: Path, given: dict) -> Path:
        """What a Blender opened again starts from: its last sending (`send`) with the animations the mod plays now
        (`given`: _going_out's, as Blender is given them) in place of the ones it sent, and, while its bones are the
        mod's within float noise (rusemod.rig.bones_of), the mod's own bones exactly (rusemod.gltf.bones_like from the
        unit's model file `own`): Blender's floats moved them a little each trip, and two trips moved the Generic
        Horse's upper arms past that noise (real Blender 4.5.14, 2026-11-13), so the clips of the second came back on a
        skeleton worked out anew, all 25 files rewritten. As <work>/<the model's name>_again.glb, the sending itself
        left as Blender wrote it; the sending as it is when the animations aren't on its bones (a bone renamed, added
        or taken away in Blender: what comes back is then taken in as Blender sends it)."""
        import struct as _struct
        from rusemod import baf, gltf, rig
        from rusemod.modelin import ModelError, own_animations_glb
        from .api import file_error
        from .squadblender import _put
        try:
            raw = send.read_bytes()
            if given and rig.bones_of(raw, baf.parse(next(iter(given.values()))).skeleton):
                raw, _word = gltf.bones_like(raw, own.read_bytes())    # (Blender's float noise only: the mod's own)
            data = own_animations_glb(raw, given, blender=True)
        except (ModelError, ValueError, KeyError, IndexError, TypeError, _struct.error):
            return send
        except OSError as exc:              # (said in words, never in Python's own)
            raise file_error(exc, send) from exc
        again = work / f"{own.stem}_again.glb"
        try:
            _put(again, data)
        except OSError as exc:              # (said in words, never in Python's own)
            raise file_error(exc, again) from exc
        return again

    @staticmethod
    def _went_out(work: Path, going: list) -> None:
        """Keep beside the work file the animations that went out to Blender (`going`, _going_out's rows: each clip as
        the mod had it, and what Blender was given of it: ruse_studio.animblender.write_sent's animations.json and
        clips/), on the skeleton record they're on, for Bring back the model; none (a model with no animations of
        its own, or its file's own gone out): any kept from an opening before are taken away (forget_sent)."""
        from rusemod import baf
        from . import animblender
        from .api import file_error
        try:
            if going:
                animblender.write_sent(work, "own", baf.parse(going[0]["clip"]).skeleton, going)
            else:
                animblender.forget_sent(work)
        except OSError as exc:              # (said in words, never in Python's own)
            raise file_error(exc, work / animblender.SENT) from exc

    def model_blender(self, address: str, lang: str = "us", kind: str | None = None) -> dict:
        """Open the unit's model in Blender to be changed (see the module's note); `kind`: one of a squad's other
        soldiers, opened alone (his last sending, his own model, or the game model his figure draws). What Blender
        opens: what it sent last, else the unit's own model when it has one (the owner, 2026-11-13, to "The Generic
        Horse: should 'Change it in Blender' open its own model?": "yes"; _own_start, the squad page's way), else the
        game model, which goes out with the alpha picture of each material beside it. Either way the alpha pictures
        are listed in the work folder's alpha.json (Bring back the model puts them back). Returns look() with "work"
        (the work folder), "file" (what Blender opened) and "kind" (None for the riflemen)."""
        from rusemod import gltf, models
        from rusemod.blender import open_model_to_change
        from .api import StudioError, words
        from .squadblender import _write
        kind = self._blender_kind(address, kind)
        work, send = self._model_work(address, kind)
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        own = self._kind_file(address, kind) if kind else self._own_model_file(address)
        # a model on bones of its own goes out with the animations the mod plays (item 45: an animation back from
        # Blender as it went out is the mod's own again, byte for byte; _going_out), each kept beside the work file
        # (ruse_studio.animblender.write_sent) for Bring back the model to set what comes back against; the unit's
        # animations are its model's, so a squad's other kind (the heavy-weapon soldier's own model) keeps its file's
        going = self._going_out(own) if not kind and own is not None and own.is_file() else []
        given = {r["name"]: r["blender_clip"] for r in going}
        if send.is_file():
            start = send  # what was sent last time: the work goes on from it
            if going:     # (with the animations the mod plays now: RUSE Decoy may have changed one since)
                start = self._again(send, work, own, given)
        elif own is not None and own.is_file():
            # the unit's own model (a model of its own, Import model's or the Generic Horse's horse and rider with its
            # bones and animations): brought back as the game's soldier, it lost them all without a word (the review
            # of 2026-11-12, test_review_loss's test_change_it_in_blender_opens_its_own_model)
            work.mkdir(parents=True, exist_ok=True)
            start, alphas, put = self._own_start(own, work, given)
            going = going if put else []
            _write(work / ALPHA, {"format": 1, "start": start.name, "alpha": alphas})
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
                summary = gltf.export(lib, [model], work, rest_bones=True)[0]
            finally:
                lib.close()
            start = Path(summary["file"])
            # which alpha picture goes out with each material (Blender keeps none of them): Bring back puts them back
            _write(work / ALPHA, {"format": 1, "start": start.name, "alpha": self._alphas_out(start, summary)})
        self._went_out(work, going)
        w = words(lang)
        (work / "words.json").write_text(json.dumps(
            {"send": w["blender_model_send"], "sent": w["blender_model_sent"],
             "hint": [w["blender_model_hint1"], w["blender_model_hint2"]]}, ensure_ascii=False), encoding="utf-8")
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        return {**self.look(address), "work": str(work), "file": str(start), "kind": kind}

    def model_blender_back(self, address: str, size: float = 1.0, kind: str | None = None, keep_bones: bool = False,
                           keep_paint: bool = False) -> dict:
        """Take what Blender sent in as the unit's own model (Import model's way), or, with `kind`, as that soldier's
        own model alone (the squad's others keep theirs): an open Blender is asked to send first; a closed one's last
        sending is used. Each material's alpha picture that went out goes back in by its name (rusemod.gltf.
        with_alpha), into <work>/kept/<its name>.glb, the file Import model takes in; its report says what each got
        (_alpha_said). `keep_bones`, `keep_paint` (the one Blender button with Bones or Paint unticked): the bones or
        pictures that went out put back (rusemod.gltf.bones_like, paint_like). Returns model_import()'s answer with
        "work", "kind" and "kept" ({"bones": bones_like's word or None, "paint": the materials put back or None})."""
        from rusemod import gltf, rig
        from rusemod.blender import ask_to_send
        from . import animblender
        from .api import StudioError
        from .squadblender import _put
        kind = self._blender_kind(address, kind)
        work, send = self._model_work(address, kind)
        proc = self._blenders.get(str(work))
        if proc is not None and proc.poll() is None:  # its Blender is open: it sends what it has now
            ask_to_send(send, SEND_WAIT)
        if not send.is_file():  # not a game rule: the Studio's own hand-over from Blender, nothing sent yet
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring back the model here.")
        raw = send.read_bytes()
        # (its bones back in the order they went out in: Blender writes them in its own, and a model on bones of its
        # own is read on that order, its animations and the squad's other soldiers' models made on it: rusemod.gltf.
        # joints_like; the Generic Horse's bazooka man was otherwise no longer on the riflemen's bones)
        start = work / str(_read_json(work / ALPHA).get("start") or "")
        kept_words = {"bones": None, "paint": None}
        if start.name and start.is_file() and start != send:
            raw = gltf.joints_like(raw, start.read_bytes())
            if keep_bones:   # (the one Blender button's unticked Bones: the bones that went out put back)
                raw, kept_words["bones"] = gltf.bones_like(raw, start.read_bytes())
            if keep_paint:   # (its unticked Paint: the pictures that went out put back)
                raw, kept_words["paint"] = gltf.paint_like(raw, start.read_bytes())
        # (a model on bones of its own: the skeleton record and each animation that went out back in the file, which
        # Blender keeps no extras of, so the import keeps every animation that came back as it went out byte for byte,
        # and of a changed one every bone that wasn't: rusemod.rig.with_record, with_went_out, kept_clip; item 45)
        sent = animblender.read_sent(work)
        if sent is not None:
            try:
                raw = rig.with_record(raw, sent["record"])
                raw = rig.with_went_out(raw, {a["name"]: a["clip"] for a in sent["animations"]},
                                        {a["name"]: a["blender_clip"] for a in sent["animations"]})
            except (ValueError, struct.error):   # (a file that isn't a .glb: Import model says what it is, in words)
                pass
        went = self._alphas_back(work, send, raw)
        data, put = gltf.with_alpha(raw, {m: str(p) for m, p in went.items()})
        kept = work / KEPT / send.name
        before = kept.read_bytes() if kept.is_file() else None
        _put(kept, data)
        try:
            got = self.model_import(address, str(kept), size, kind=kind) if kind else \
                self.model_import(address, str(kept), size)
        except BaseException:
            # (an import that fails leaves the file the model was made from as it was: Resize and Move fit from it)
            if before is None:
                kept.unlink(missing_ok=True)
            else:
                _put(kept, before)
            raise
        self._alpha_said(address, kind, got, put, went)
        return {**got, "work": str(work), "kind": kind, "kept": kept_words}
