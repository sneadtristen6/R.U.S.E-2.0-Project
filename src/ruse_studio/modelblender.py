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

What a Bring back sets what came back against is what went out when Blender was opened (animations.json), so nothing of
the modder's is lost on the way (the review of 2026-11-13, after 278fe767): Blender opened again on a sending that was
never brought back opens it with its own animations, as Blender sent them (opened with the mod's, a change made there
and never brought back was dropped without a word), and what went out stays what it is set against; one brought back is
opened with the mod's animations, as they are now, and taken out of the work folder (it is in the mod), so no Bring back
sets it against animations it wasn't made from. Which openings are on what went out, which sending was brought back
last and what each Bring back since took in from Blender are kept in back.json (BACK; each clip changed there in
took/, TOOK), and each opening's session goes to Blender with its words, which Send writes beside the file
(rusemod.blender_model's ABOUT): a sending of a Blender opened on other animations than those it would be set against
is refused, said. An animation that comes back from Blender as it went out, or as the last Bring back took it in, while
the Studio changed it since Blender last gave the mod a clip of it (RUSE Decoy; studio_changed) keeps the Studio's
change, said in the answer's "differs" (RUSE Decoy's own Blender keeps it too: decoyblender's "differs"); one Blender
changed is Blender's and the Studio's change named, as when both change it before one Bring back; one that comes back as
it went out after a Bring back took a change of it in, Blender's undo of that change, is put back as it went out, as
before. Its bones
unticked, the bones the mod's model has are put back (the one Blender button's "what was unticked stays as it was"),
never those of the file the first opening wrote, which a bone moved and brought back since isn't in.

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

import hashlib
import json
import re
import struct
import uuid
from pathlib import Path

from .animmodel_calls import NOT_KEPT, read_record, write_record


def _read_json(path: Path) -> dict:
    """A small JSON file of the work folder as a dict ({} when it isn't there or isn't one)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _sha_of(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


WORK = "blender"
SEND_WAIT = 60.0   # seconds Bring back the model waits for an open Blender to send
ALPHA = "alpha.json"   # in the work folder: the alpha picture that went out with each material, by the material's name
KEPT = "kept"          # <work>/kept/<its name>.glb: what Bring back the model took in, each alpha picture back in it
BACK = "back.json"     # in the work folder: the openings on what went out, the sending brought back last, what it took
TOOK = "took"          # <work>/took/<its SHA-256>.baf: each clip a Bring back took in from Blender, changed there
ABOUT = ".json"        # beside the sending, its name and this: what Send says of it (rusemod.blender_model's ABOUT)
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


def back_state(work: Path) -> dict:
    """The work folder's back.json as this Studio reads it (a field of another shape is one that isn't there):
    {"sessions": [the session of each opening of Blender on what went out last (animations.json): the one that wrote
    it, then each that opened again a sending never brought back], "sent": the SHA-256 of the last sending brought back
    (None: none), "took": {an animation that went out: the SHA-256 of the clip a Bring back since took in from Blender
    for it}}."""
    data = _read_json(Path(work) / BACK)
    sessions = data.get("sessions") if isinstance(data.get("sessions"), list) else []

    took = data.get("took") if isinstance(data.get("took"), dict) else {}
    return {"format": 1, "sessions": [s for s in sessions if isinstance(s, str) and s],
            "sent": data.get("sent") if isinstance(data.get("sent"), str) else None,
            "took": {k: v for k, v in took.items() if isinstance(k, str) and isinstance(v, str)}}


def studio_changed(mine: dict, went: dict, took: dict) -> set:
    """Of the animations that went out to Blender (`went`: {name: the clip as the mod had it}), those the Studio changed
    since Blender last gave the mod a clip of them (`mine`: the mod's clips now): the mod's clip is neither the one the
    last Bring back took in from Blender (`took`: back_state's SHA-256s) nor, before any, the one that went out. Blender
    has such an animation as it gave it, so its change of one of them is set against a change of the Studio's."""
    return {n for n, c in went.items() if n in mine and _sha_of(mine[n]) != (took.get(n) or _sha_of(c))}


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
            raise StudioError("This unit has no soldiers of another kind: open its model in Blender instead.")
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
        {}}]). One whose clip file can't be read (gone, or not a clip) goes out as the model's own file carries it
        (AnimModelCalls._file_clips), as every one did before, and the fit says what it can't read; the others as the
        mod has them (one such file made every one go so, all of them rewritten after: the review of 2026-11-13). []
        for a model that isn't on bones of its own, a unit with none in the mod, or one such file whose animation the
        model's file hasn't got (its file's own go, as before)."""
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
        if not files:
            return []
        carried = None
        rows = []
        for name in files:          # (the mod's order: units.toml lists them so)
            clip, given = mine.get(name), None
            if clip is not None:
                try:
                    given = animblender.on_game_frames(clip)
                except (ValueError, IndexError, struct.error):   # (a clip file of the mod's that isn't one)
                    given = None
            if given is None:       # (its file gone or not a clip: the model's own file's, as before)
                if carried is None:
                    carried = self._file_clips(own)
                clip = carried.get(name)
                if clip is None:    # (the model's file hasn't got it either: its file's own go, as before)
                    return []
                try:
                    given = animblender.on_game_frames(clip)
                except (ValueError, IndexError, struct.error):
                    return []
            rows.append({"name": name, "clip": clip, "blender_clip": given, "member": None, "own": files.get(name),
                         "actions": {}})
        return rows

    @staticmethod
    def _again(send: Path, work: Path, own: Path, given: dict | None) -> Path:
        """What a Blender opened again starts from: its last sending (`send`) with its bones in the record's order and,
        while they are the mod's within float noise (rusemod.rig.bones_of), the mod's own bones exactly
        (rusemod.gltf.bones_like from the unit's model file `own`): Blender's floats moved them a little each trip, and
        two trips moved the Generic Horse's upper arms past that noise (real Blender 4.5.14, 2026-11-13), so the clips
        of the second came back on a skeleton worked out anew, all 25 files rewritten. `given` (a sending brought back,
        everything of it in the mod: _going_out's, as Blender is given them): the animations the mod plays now in place
        of the ones it sent; None (a sending never brought back): its animations as Blender sent them, so a change made
        there and never brought back is still there (opened with the mod's, it was dropped without a word: the review
        of 2026-11-13). As <work>/<the model's name>_again.glb, the sending itself left as Blender wrote it; the sending
        as it is when its bones can't be set against the mod's model's (a bone renamed, added or taken away in Blender:
        what comes back is then taken in as Blender sends it)."""
        import struct as _struct
        from rusemod import animmodel, gltf, rig
        from rusemod.modelin import ModelError, own_animations_glb
        from .api import file_error
        from .squadblender import _put
        try:
            model = own.read_bytes()
            # (its bones in the record's order first, as Bring back the model reads them: Blender writes them in an
            # order of its own, and the record is matched in its own; ba070f5f's walk found it so, the snap never made)
            raw = gltf.joints_like(send.read_bytes(), model)
            if rig.bones_of(raw, animmodel.record_of(own)):
                raw, _word = gltf.bones_like(raw, model)    # (Blender's float noise only: the mod's own bones)
            data = own_animations_glb(raw, given, blender=True) if given else raw
        except (ModelError, animmodel.AnimModelError, ValueError, KeyError, IndexError, TypeError, _struct.error):
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
        opens: what it sent last (a model on bones of its own: with the animations the mod plays now when that sending
        was brought back, with its own as Blender sent them when it wasn't: _again), else the unit's own model when it
        has one (the owner, 2026-11-13, to "The Generic Horse: should 'Change it in Blender' open its own model?":
        "yes"; _own_start, the squad page's way), else the game model, which goes out with the alpha picture of each
        material beside it. Either way the alpha pictures are listed in the work folder's alpha.json (Bring back the
        model puts them back), and what Bring back sets what comes back against in back.json (_opened). Returns look()
        with "work" (the work folder), "file" (what Blender opened) and "kind" (None for the riflemen)."""
        from rusemod import gltf, models
        from rusemod.blender import open_model_to_change
        from .api import StudioError, words
        from .squadblender import _write
        kind = self._blender_kind(address, kind)
        work, send = self._model_work(address, kind)
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org, then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        own = self._kind_file(address, kind) if kind else self._own_model_file(address)
        # a model on bones of its own goes out with the animations the mod plays (item 45: an animation back from
        # Blender as it went out is the mod's own again, byte for byte; _going_out), each kept beside the work file
        # (ruse_studio.animblender.write_sent) for Bring back the model to set what comes back against; the unit's
        # animations are its model's, so a squad's other kind (the heavy-weapon soldier's own model) keeps its file's
        going = self._going_out(own) if not kind and own is not None and own.is_file() else []
        given = {r["name"]: r["blender_clip"] for r in going}
        state = back_state(work)
        session = uuid.uuid4().hex   # (this opening: Send writes it beside what it sends, rusemod.blender_model's ABOUT)
        renew = True    # (what goes out now is what Bring back sets what comes back against: write_sent)
        if send.is_file():
            start = send  # what was sent last time: the work goes on from it
            if going:
                from .api import file_error
                try:
                    brought = state["sent"] is not None and state["sent"] == _sha_of(send.read_bytes())
                except OSError as exc:      # (said in words, never in Python's own)
                    raise file_error(exc, send) from exc
                # brought back, all of it is in the mod: it goes out with the animations the mod plays now (RUSE Decoy
                # may have changed one since). Never brought back: with its own, as Blender sent them, and what went
                # out stays what it is set against, so its Bring back does what bringing that sending back would have
                # (with the mod's, a change made there and never brought back was dropped: the review of 2026-11-13)
                start = self._again(send, work, own, given if brought else None)
                renew = brought and start != send
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
        self._opened(work, send, going if renew else None, state, session)
        w = words(lang)
        (work / "words.json").write_text(json.dumps(
            {"send": w["blender_model_send"], "sent": w["blender_model_sent"],
             "hint": [w["blender_model_hint1"], w["blender_model_hint2"]], "session": session},
            ensure_ascii=False), encoding="utf-8")
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        return {**self.look(address), "work": str(work), "file": str(start), "kind": kind}

    def _opened(self, work: Path, send: Path, going: list | None, state: dict, session: str) -> None:
        """What an opening keeps for Bring back the model: `going` (_going_out's rows; [] none) what went out, written
        beside the work file (_went_out) and set against from now on, with this opening (`session`) the only one on it;
        a sending that was there, brought back already (it's in the mod), is taken out with what Send said of it, so no
        Bring back reads it again and sets it against animations it wasn't made from (RUSE Decoy's own Blender takes
        such a sending out too). None (a sending never brought back, opened again as Blender sent it): what went out
        stays as it is, and this opening is one more on it. back.json (BACK, back_state) says which."""
        from .api import file_error
        from .squadblender import _write
        if going is None:
            state = {**state, "sessions": state["sessions"] + [session]}
        else:
            if going and send.is_file():
                try:
                    send.unlink()
                    send.with_name(send.name + ABOUT).unlink(missing_ok=True)
                except OSError as exc:      # (said in words, never in Python's own)
                    raise file_error(exc, send) from exc
            self._went_out(work, going)
            state = {"format": 1, "sessions": [session], "sent": None, "took": {}}
            import shutil
            shutil.rmtree(work / TOOK, ignore_errors=True)   # (what Bring backs took in on what went out before)
        try:
            _write(work / BACK, state)
        except OSError as exc:              # (said in words, never in Python's own)
            raise file_error(exc, work / BACK) from exc

    def model_blender_back(self, address: str, size: float = 1.0, kind: str | None = None, keep_bones: bool = False,
                           keep_paint: bool = False) -> dict:
        """Take what Blender sent in as the unit's own model (Import model's way), or, with `kind`, as that soldier's
        own model alone (the squad's others keep theirs): an open Blender is asked to send first; a closed one's last
        sending is used. Each material's alpha picture that went out goes back in by its name (rusemod.gltf.
        with_alpha), into <work>/kept/<its name>.glb, the file Import model takes in; its report says what each got
        (_alpha_said). `keep_bones`, `keep_paint` (the one Blender button with Bones or Paint unticked): the bones the
        mod's model has, or the paint it has now (_paint_now), put back (rusemod.gltf.bones_like, paint_like). A
        sending of a Blender opened on other animations than those it would be set against (its session, which Send
        writes beside it, isn't one of back.json's) is refused, nothing taken in. Returns model_import()'s answer with
        "work", "kind", "kept" ({"bones": bones_like's word or None, "paint": the materials put back or None}) and
        "differs" (the animations that came back from Blender as they went out while the Studio changed them since: the
        Studio's change stays, _settled)."""
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
                              "the top, then bring your changes back here.")
        raw = send.read_bytes()
        sha = _sha_of(raw)
        state = back_state(work)
        about = _read_json(send.with_name(send.name + ABOUT))
        if about.get("glb") == sha and isinstance(about.get("session"), str) and about["session"] \
                and state["sessions"] and about["session"] not in state["sessions"]:
            # (a Blender opened before the last opening on other animations, still open or the Studio started again
            # meanwhile, sent it: set against what went out last, a change the Studio made since it opened would be
            # taken for Blender's and put back without a word: the review of 2026-11-13)
            # not a game rule: which Blender sent the file
            raise StudioError("What came back was sent by a Blender opened before the one opened last, so it can't be "
                              "taken in: close that Blender, then in the one opened last click Send to the R.U.S.E. "
                              "Studio and bring your changes back.")
        # (its bones back in the order they went out in: Blender writes them in its own, and a model on bones of its
        # own is read on that order, its animations and the squad's other soldiers' models made on it: rusemod.gltf.
        # joints_like; the Generic Horse's bazooka man was otherwise no longer on the riflemen's bones)
        start = work / str(_read_json(work / ALPHA).get("start") or "")
        own = self._kind_file(address, kind) if kind else self._own_model_file(address)
        kept_words = {"bones": None, "paint": None}
        if start.name and start.is_file() and start != send:
            raw = gltf.joints_like(raw, start.read_bytes())
            if keep_bones:
                # (the one Blender button's unticked Bones: the bones the mod's model has now put back, "what was
                # unticked stays as it was"; the first opening's file, read for them before, has none of a bone moved
                # and brought back since, so it was moved back and every animation made on it again: the review of
                # 2026-11-13, its second suspicion)
                bones = own if own is not None and own.is_file() else start
                raw, kept_words["bones"] = gltf.bones_like(raw, bones.read_bytes())
            if keep_paint:
                # (its unticked Paint: the paint the mod's model has now put back, _paint_now; the first opening's
                # file, read for it before, put a repaint brought back since back to the first picture while the page
                # said "Its paint was kept as it was": found by the anims fixer, 2026-11-14)
                paint = self._paint_now(work, send, own, start)
                raw, kept_words["paint"] = gltf.paint_like(raw, paint.read_bytes())
        # (a model on bones of its own: the skeleton record and each animation that went out back in the file, which
        # Blender keeps no extras of, so the import keeps every animation that came back as it went out byte for byte,
        # and of a changed one every bone that wasn't: rusemod.rig.with_record, with_went_out, kept_clip; item 45)
        sent = animblender.read_sent(work)
        studio: dict = {}
        mine: dict = {}     # (the unit's own animations as the mod has them before this Bring back)
        if sent is not None and not kind and own is not None and self._mod_dir() is not None:
            mine = self._own_now(self._mod_dir(), own.stem)[0]
        if sent is not None:
            went_out = {a["name"]: a["clip"] for a in sent["animations"]}
            given = {a["name"]: a["blender_clip"] for a in sent["animations"]}
            try:
                raw = rig.with_record(raw, sent["record"])
                settled: dict = {}
                if not kind:
                    settled, studio = self._settled(raw, went_out, given, state["took"], work, mine)
                # (the mod's clip of one settled so goes into the file as the clip kept when it comes back as it came
                # back now, set against what it came back as: the import, and every Resize or Move after, keep it so)
                raw = rig.with_went_out(raw, {n: settled[n][0] if n in settled else c for n, c in went_out.items()},
                                        {n: settled[n][1] if n in settled else g for n, g in given.items()})
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
        after = self._own_now(self._mod_dir(), own.stem)[0] if mine else {}
        # (one the Studio changed since Blender last gave the mod a clip of it, that this Bring back put Blender's in
        # the place of: named, as when both change it before one Bring back. The import names it only when the mod's
        # clip isn't the last fit's: one whose Studio change a Bring back kept before, or set back in the Studio to
        # the clip that went out after a Bring back took Blender's in, was put back without a word)
        if sent is not None and mine:
            went_out = {a["name"]: a["clip"] for a in sent["animations"]}
            changed = studio_changed(mine, went_out, state["took"])
            replaced = [n for n in went_out if n in changed and n not in studio and after.get(n) != mine[n]]
            if replaced and isinstance(got.get("model"), dict):
                lost = got["model"].setdefault(NOT_KEPT, {"animations": [], "picks": []})
                named = list(lost.get("animations") or [])
                lost["animations"] = named + [n for n in replaced if n not in named]
        self._alpha_said(address, kind, got, put, went)
        self._brought(work, state, sha, sent, studio, after)
        return {**got, "work": str(work), "kind": kind, "kept": kept_words, "differs": list(studio)}

    @staticmethod
    def _paint_now(work: Path, send: Path, own: Path | None, start: Path) -> Path:
        """The file whose base colour pictures are the paint the unit's model (`own`, or a kind's) has now, under the
        names Blender knows its materials by, for Bring back the model with Paint unticked: what the last Bring back
        took in (<work>/kept/<its name>.glb) while the model is the one made from it (its record's "from" names that
        file; Resize and Move fit again from it, its paint as it was), as Change the squad in Blender starts a soldier
        from his ("kept": ruse_studio.squadblender._start_file); else the file the first opening went out with
        (`start`: alpha.json's), which is the model's paint while nothing was brought back since. The model's own file
        isn't read for it: Import model names each of its materials after its picture (rusemod.modelin.write_glb), and
        paint_like puts pictures back by Blender's material names."""
        kept = work / KEPT / send.name
        record = read_record(own.with_suffix(".json")) if own is not None else None
        made_from = record.get("from") if isinstance(record, dict) else None
        try:
            if kept.is_file() and isinstance(made_from, str) and made_from \
                    and Path(made_from).resolve() == kept.resolve():
                return kept
        except (OSError, ValueError):   # (a "from" that isn't a path here: not the kept file)
            pass
        return start

    @staticmethod
    def _settled(raw: bytes, went: dict, given: dict, took: dict, work: Path, mine: dict) -> tuple[dict, dict]:
        """Of the animations that went out to Blender (`went`: {name: the clip as the mod had it}; `given`: what Blender
        was given of each) and that the mod plays another clip for now than the one that went out, or the Studio
        changed since Blender last gave the mod one (`mine`, AnimModelCalls._own_now's: one on the same bones;
        studio_changed), those Blender brought nothing new of, measured as the import measures (`raw`: what Blender
        sent, its skeleton record back in it; rusemod.rig.kept_clip on its poses), the mod's clip kept for: ({name:
        (the mod's clip, the clip it came back as)}, {name: the mod's clip} of those the Studio changed): first, one the
        Studio changed that came back as it went out (as Blender was given it), or as the last Bring back took it in
        (that clip kept in <work>/took/): Blender didn't change it, so the Studio's change stays (a change made in RUSE
        Decoy while Blender was open was undone by a Bring back that left that animation as it was: the review of
        2026-11-13; RUSE Decoy's own Blender keeps the Studio's then, its "differs"); then one a Bring back since took
        in from Blender, as the mod still has it, that came back as it took it in (Blender opened again on a sending
        never brought back sends a change brought back before again, its numbers through Blender once more: that clip,
        byte for byte). One Blender changed (again) is Blender's, a Studio change of it named (NOT_KEPT), as before;
        one a Bring back took a change of in that came back as it went out is Blender's undo of that change, put back
        as it went out, as before."""
        import dataclasses
        from rusemod import baf, rig, unitmodel
        from rusemod.modelin import glb_document
        studio, again, last = {}, {}, {}
        changed = studio_changed(mine, went, took)
        for name, clip in went.items():
            now = mine.get(name)
            if now is None or (now == clip and name not in changed):
                continue
            try:
                c = baf.parse(now)
                baf.check(c)
                if c.skeleton != baf.parse(clip).skeleton:   # (on other bones: the model's are those that went out)
                    continue
            except (ValueError, IndexError, struct.error):   # (a clip file that isn't one: the fit says so)
                continue
            if name not in changed:     # (the mod's is what the last Bring back took in from Blender)
                again[name] = now
                continue
            studio[name] = now
            kept_file = Path(work) / TOOK / f"{took.get(name)}.baf"
            if took.get(name) and kept_file.is_file():      # (what the last Bring back took in of it from Blender)
                try:
                    last[name] = kept_file.read_bytes()
                except OSError:
                    pass
        if not studio and not again:
            return {}, {}
        try:
            doc, binary = glb_document(raw)
            r = rig.rig_of(doc, binary, "back.glb")
            record, _notes = unitmodel.own_skeleton(r)
            r = dataclasses.replace(r, animations=[a for a in r.animations if a.name in studio or a.name in again])
            made, _notes = unitmodel.own_clips(r, record)
            poses = {a.name: r.poses(a)[1] for a in r.animations if a.name in made}
            settled = {}
            for n in made:
                # (what it may have come back as: what Blender was given of it, or what the last Bring back took in)
                against = [given.get(n) or went[n], *([last[n]] if n in last else [])] if n in studio else [again[n]]
                came = next((a for a in against if rig.kept_clip(made[n], a, poses=poses.get(n)) == (a, [])), None)
                if came is not None:
                    settled[n] = (studio.get(n) or again[n], came)
        except (ValueError, KeyError, IndexError, TypeError, struct.error):   # (read so by the import, which says it)
            return {}, {}
        return settled, {n: now for n, now in studio.items() if n in settled}

    @staticmethod
    def _brought(work: Path, state: dict, sha: str, sent: dict | None, studio: dict, after: dict) -> None:
        """After a Bring back took a sending in (its SHA-256 `sha`): back.json says it was brought back (a Blender opened
        again on it opens it with the mod's animations: model_blender) and what it took in from Blender of each
        animation that went out (`sent`, read_sent's), as the mod has it now (`after`), each one changed there kept in
        <work>/took/ (TOOK): a sending that comes back as it went out after that is Blender's undo of it, and the
        Studio's change of one that comes back as it took it in stays (_settled). One the Studio's change was kept for
        (`studio`) took nothing in: Blender has it as it gave it before, so a change of it there is set against the
        Studio's (studio_changed). A back.json or clip that can't be written loses nothing of the mod: the next opening
        opens the sending as Blender sent it, set against what went out, which is what this Bring back did."""
        from .squadblender import _put, _write
        took = dict(state["took"]) if sent is not None else {}
        if sent is not None:
            for a in sent["animations"]:
                name = a["name"]
                if name in studio or name not in after:
                    continue
                took[name] = _sha_of(after[name])
                kept = work / TOOK / f"{took[name]}.baf"
                if after[name] != a["clip"] and not kept.is_file():
                    try:
                        _put(kept, after[name])
                    except OSError:
                        pass
        try:
            _write(work / BACK, {"format": 1, "sessions": state["sessions"], "sent": sha, "took": took})
        except OSError:
            pass
