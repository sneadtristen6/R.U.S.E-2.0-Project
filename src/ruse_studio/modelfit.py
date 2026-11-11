"""A new unit's model on bones of its own split into its two halves, and what of its animations and bones won't fit
(StudioApi's ModelFitCalls; item 5, part 3; the owner's 7, 2026-11-10: "Yes, seven should warn them. If it's gonna
break, and then tell them how to fix it. And what's the issue is. Should be intuitive.").

model_fit (the unit page's "Its two halves" and "Will it work in the game?" boxes, app.js fitBox): for a unit whose
own model is on bones of its own (its record's "skeleton": "own"), the bone it splits at (the one chosen, else the one
suggested), which bones are in its upper half and which in its lower, every bone as a tree; and for any unit with a
model rigged to bones (its own, or the game soldier's), the problems rusemod.bonefit finds: each animation it will play
whose bones don't fit the model, each bone the unit's shots and parts need that the model hasn't got, more than 64
bones. model_split keeps the chosen bone in the model's record (files/models/<unit>.json "split"), which the build
splits the model at (rusemod.bonefit.split_for). A model on the game soldier's bones keeps the game's own halves: no
choice. What the page checks is the game's own data for the unit the new one copies and the mod's own animations; the
build checks the same again on the mod's data as built (rusemod.build.unit_fit_checks)."""
from __future__ import annotations

import re
from pathlib import Path

# the figures of a unit, by the end of their path from it, as the page names them (words.toml fit_fig_<kind>)
FIGURE_KINDS = (("DescriptorFigurine", "far"), ("GfxDescriptorIconeCadavre", "fallen"), ("GfxDescriptorCadavre", "wreck"),
                ("GfxDescriptorFusilier", "rifle"), ("GfxDescriptorBazooka", "heavy"), ("GfxDescriptor", "unit"))
OWN = "own:"   # what a listing plays, when it's the mod's own animation file: own:<the file>


def figure_kind(path: str) -> str:
    """How the page names a figure ("rifle", "heavy", "far", "fallen", "wreck", "unit" or "other")."""
    last = path.rsplit(".", 1)[-1]
    if re.search(r"\[\d+\]", last) or "SousElements" in path:
        return "other"      # (a person or a part held on a bone)
    return next((kind for end, kind in FIGURE_KINDS if last == end), "other")


def bone_tree(names: list, parents: list, top: set) -> list:
    """Every bone as the page draws its tree: [{"name", "depth", "top": in the upper half}], each bone after its parent,
    its children in bone order."""
    kids: dict = {}
    for b, p in enumerate(parents):
        kids.setdefault(p, []).append(b)
    out, todo = [], [(b, 0) for b in reversed(kids.get(-1, []))]
    seen = set()
    while todo:
        b, depth = todo.pop()
        if b in seen:
            continue
        seen.add(b)
        out.append({"name": names[b], "depth": depth, "top": names[b] in top})
        todo += [(k, depth + 1) for k in reversed(kids.get(b, []))]
    out += [{"name": names[b], "depth": 0, "top": names[b] in top} for b in range(len(names)) if b not in seen]
    return out


class ModelFitCalls:
    def _fitcheck_model(self, address: str) -> tuple:
        """(the unit's own model file, its record, its report) or (None, {}, {}) for a unit with none."""
        from rusemod import bonefit
        from rusemod.unitmodel import glb_report
        glb = self._own_model_file(address)
        if glb is None or not glb.is_file():
            return None, {}, {}
        record = bonefit.model_record(glb)
        report = record.get("report") if isinstance(record.get("report"), dict) else glb_report(glb)
        return glb, record, report

    @staticmethod
    def _fitcheck_skeleton(record: dict, report: dict) -> str | None:
        """The shared record's "skeleton" ("own": bones of its own; "soldier": the game's bones of the unit it copies),
        worked out from the fitting's report for a record written before it said; None for a model fitted on a hull."""
        from rusemod.modelin import OWN_SKELETON
        if record.get("skeleton") in ("own", "soldier"):
            return record["skeleton"]
        if report.get(OWN_SKELETON):
            return "own"
        return "soldier" if report.get("rigged") else None

    def model_fit(self, address: str) -> dict:
        """What the unit page shows of a new unit's own model rigged to bones (the module's note): {"skeleton": "own",
        "soldier" or None (nothing to show), "bones": how many, "halves": {"split", "suggested", "chosen": whether the
        modder chose it, "top": [bones], "bottom": [bones], "tree": bone_tree} (own bones only), "problems": [
        rusemod.bonefit's, each with "figure_kind", and "clip_names" for animations]}."""
        from rusemod import bonefit
        glb, record, report = self._fitcheck_model(address)
        skeleton = self._fitcheck_skeleton(record, report) if glb is not None else None
        out = {"skeleton": skeleton, "bones": 0, "halves": None, "problems": []}
        if skeleton is None:
            return out
        problems = []
        if skeleton == "own":
            blob = bonefit.glb_record(glb)
            if blob is None:
                return dict(out, skeleton=None)
            names, parents = bonefit.skeleton_of(blob)
            split, notes = bonefit.chosen_split(names, parents, record.get(bonefit.SPLIT))
            halves = bonefit.halves_of(names, parents, split)
            out["halves"] = dict(halves, suggested=bonefit.suggest_split(names, parents),
                                 chosen=bonefit.SPLIT in record and not any(n["kind"] == "split_gone" for n in notes),
                                 tree=bone_tree(names, parents, set(halves["top"])))
            problems += bonefit.model_problems(names, parents, record.get(bonefit.SPLIT))
        else:
            names = self._fitcheck_game_bones(report.get("like"))
            if names is None:
                return out
            problems += bonefit.model_problems(names)
        out["bones"] = len(names)
        problems += self._fitcheck_figures(address, report, names, own_bones=skeleton == "own")
        for p in problems:
            if p.get("figure") is not None:
                p["figure_kind"] = figure_kind(p["figure"])
            if p.get("clips"):
                p["clip_names"] = [self._fitcheck_clip_name(c) for c in p["clips"]]
        out["problems"] = problems
        return out

    def model_split(self, address: str, bone: str | None = None) -> dict:
        """Keep `bone` as the bone the unit's own model splits at (its upper half: that bone and every bone under it);
        None or "": back to the suggested one. Returns model_fit()."""
        from rusemod import bonefit
        from .api import StudioError
        glb, record, report = self._fitcheck_model(address)
        if glb is None or self._fitcheck_skeleton(record, report) != "own":
            # not a game rule: only a model on bones of its own splits where the modder says (one on the game soldier's
            # bones keeps the game's two halves)
            raise StudioError("Only a model with bones of its own can be split where you choose: import one first.")
        blob = bonefit.glb_record(glb)
        if blob is None:
            raise StudioError("The model's bones can't be read: import the model again.")
        names, _parents = bonefit.skeleton_of(blob)
        if bone and bone.lower() not in names:
            raise StudioError(f"The model has no bone called {bone}.")
        with self._saving:
            bonefit.save_split(glb, bone or None)
        return self.model_fit(address)

    def _fitcheck_game_bones(self, model: str | None) -> list | None:
        """The bones of the game's model `model` (the one a model rigged to the game's bones was fitted to), None when
        not known."""
        if not model or self._game() is None:
            return None
        from rusemod import models
        try:
            lib = models.Library(self._game())
        except (OSError, ValueError):
            return None
        try:
            got = lib.bone_names(model)
        finally:
            lib.close()
        return [n.lower() for n in got] if got else None

    def _fitcheck_figures(self, address: str, report: dict, names: list, own_bones: bool) -> list:
        """bonefit.check_figure on every figure of the unit that draws its own model (the game's data for the unit it
        copies: the figures naming the model it was fitted to, or one with the same bones), each listing taken as what
        it will play: the unit's own animation for that action (files/anim/units.toml), else the game's clip."""
        from rusemod import anim, bonefit
        from rusemod.animlist import member_of
        try:
            edits = self._edits()
        except Exception:      # (a mod file that can't be read: nothing to check against)
            return []
        real, unit = self._resolve(edits, address)
        if unit is None:
            return []
        ix = self._open()
        try:
            figures = bonefit.index_figures(ix.db, real.split(":", 1)[0])
        finally:
            ix.close()
        mine = bonefit.own_figures(figures, [report.get("like"), *(report.get("also") or [])])
        try:
            own = anim.mod_unit_clips(self._mod_dir()).get(unit.target.rsplit("/", 1)[-1], {})
        except anim.AnimError:
            own = {}
        actions, clips = own.get("actions") or {}, own.get("clips") or {}
        # (on the game's own bones its parts and the game's clips fit: only its own clips can't, and only they're read)
        bones_of = self._fitcheck_bones if own_bones else lambda k: self._fitcheck_bones(k) if k.startswith(OWN) else None
        out = []
        for fig in mine:
            plays = []
            for action, file, mask in fig.listings:
                f = actions.get((action, fig.path)) or actions.get((action, None))
                edit = clips.get(member_of(file)) if file else None
                if f is None and edit and edit.get("file"):
                    f = edit["file"]
                plays.append((action, f"{OWN}{f}" if f is not None else file, mask))
            out += bonefit.check_figure(names, bonefit.Figure(fig.path, fig.model, plays, fig.needs if own_bones else []),
                                        bones_of, lambda k: k.startswith(OWN), masks=False)
        return out

    def _fitcheck_bones(self, key: str) -> list | None:
        """The bones of what a listing plays (_fitcheck_figures' key): the mod's own file, or the game's clip (RUSE Decoy's
        list of the game's clips, read once per game build)."""
        from rusemod import bonefit
        from rusemod.animlist import member_of
        if key.startswith(OWN):
            try:
                return bonefit.clip_bones(Path(key[len(OWN):]).read_bytes())
            except OSError:
                return None
        try:
            row = self._decoy_clip_row(member_of(key))
        except Exception:      # (the game's clips can't be read here: not known)
            return None
        return row["skeleton"].split("|") if row and row.get("skeleton") else None

    @staticmethod
    def _fitcheck_clip_name(key: str) -> str:
        from rusemod.animlist import member_of, words
        if key.startswith(OWN):
            return Path(key[len(OWN):]).stem
        return words(member_of(key))
