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


def alpha_lost(report) -> dict:
    """Of an import's report (a model's record's "report"), what it says couldn't be kept of the model's own shine and
    side colour, for the page (app.js alphaLostLines): "blender_alpha_lost" and "alpha_sizes", those it has."""
    if not isinstance(report, dict):
        return {}
    return {k: json.loads(json.dumps(report[k])) for k in LOST if report.get(k)}


def blender_notes(report: dict) -> list:
    """The import's notes (in the record, in English) on what came back from Blender with the plain 144: each material
    that came back without an alpha picture of its own, in the order Blender sent them ("blender_alpha"), and each that
    went out with one and didn't come back under its name ("blender_alpha_lost")."""
    from rusemod.modelin import PLAIN_ALPHA
    lost = report.get("blender_alpha_lost") or {}
    flat_names = {str(m) for k in ("none", "gone") for m in lost.get(k) or []}
    flat = [m for m in (report.get("blender_alpha") or {}) if str(m) in flat_names]
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
    if not isinstance(before, dict) or not isinstance(report, dict) or not any(before.get(k) for k in SAID):
        return
    for k in SAID:
        if before.get(k):
            report[k] = json.loads(json.dumps(before[k]))
    report.setdefault("notes", []).extend(blender_notes(report))


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
        try:
            data = json.loads(record.read_text(encoding="utf-8")) if record is not None and record.is_file() else None
        except (OSError, ValueError):
            data = None
        if isinstance(data, dict):   # (as Import model wrote it, with this said too)
            data["report"] = report
            record.write_text(json.dumps(data, indent=1), encoding="utf-8")
            if not kind and "own_model" in res:   # (look()'s, read before this was said)
                res["own_model"] = json.loads(json.dumps(report))
            # (look()'s row of his kind in the answer, the riflemen's the first: read before this was said too)
            rows = [r for r in res.get("kinds") or [] if isinstance(r, dict)]
            for row in [r for r in rows if r.get("kind") == kind] if kind else rows[:1]:
                for k in LOST:
                    row.pop(k, None)
                row.update(alpha_lost(report))

    def model_blender(self, address: str, lang: str = "us", kind: str | None = None) -> dict:
        """Open the unit's model in Blender to be changed (see the module's note); `kind`: one of a squad's other
        soldiers, opened alone (his last sending, or the game model his figure draws). The game model goes out with
        the alpha picture of each material beside it, listed in the work folder's alpha.json (Bring back the model
        puts them back). Returns look() with "work" (the work folder), "file" (what Blender opened) and "kind" (None
        for the riflemen)."""
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
                summary = gltf.export(lib, [model], work, rest_bones=True)[0]
            finally:
                lib.close()
            start = Path(summary["file"])
            # which alpha picture goes out with each material (Blender keeps none of them): Bring back puts them back
            _write(work / ALPHA, {"format": 1, "start": start.name, "alpha": self._alphas_out(start, summary)})
        w = words(lang)
        (work / "words.json").write_text(json.dumps(
            {"send": w["blender_model_send"], "sent": w["blender_model_sent"],
             "hint": [w["blender_model_hint1"], w["blender_model_hint2"]]}, ensure_ascii=False), encoding="utf-8")
        self._blenders[str(work)] = open_model_to_change(blender, start, send, work / "words.json")
        return {**self.look(address), "work": str(work), "file": str(start), "kind": kind}

    def model_blender_back(self, address: str, size: float = 1.0, kind: str | None = None) -> dict:
        """Take what Blender sent in as the unit's own model (Import model's way), or, with `kind`, as that soldier's
        own model alone (the squad's others keep theirs): an open Blender is asked to send first; a closed one's last
        sending is used. Each material's alpha picture that went out goes back in by its name (rusemod.gltf.
        with_alpha), into <work>/kept/<its name>.glb, the file Import model takes in; its report says what each got
        (_alpha_said). Returns model_import()'s answer with "work" and "kind"."""
        from rusemod import gltf
        from rusemod.blender import ask_to_send
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
        return {**got, "work": str(work), "kind": kind}
