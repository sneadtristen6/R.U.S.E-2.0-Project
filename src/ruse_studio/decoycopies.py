"""RUSE Decoy's copies of an animation (StudioApi's DecoyCopyCalls, through DecoyCalls): Copy this animation… makes a
copy of one of the game's clips in the current mod (rusemod.anim's files/anim/copies.toml, its clip file in
files/anim/copies/), changed in RUSE Decoy's editor like any clip (its speed, a stand-in, its bones, a motion capture)
and played only by the units, or the soldiers and parts of a unit, ticked under Who plays it; every other unit plays
the clip as before.

The owner, 2026-11-13: "I'm realizing it doesn't seem like there's a way to copy an animation so that way you can
change an animation and implement it into like certain models and soldiers. That should probably be added to RUSE
Decoy." The way he said "sounds good go" to, that day: Copy this animation…, like Copy this ammo, the copy starting as
what is shown (from a unit's page, as that unit plays it, a change made for it in Blender too); Your copies under
Animations; Who plays it, a tick for each unit that plays the animation (the mod's own units first) and, under a unit,
for each of its soldiers or parts that plays it (its riflemen, its heavy-weapon soldier, its figure seen from far away,
a gun's crewmen); only those (a copy moves the clip's bones; an animation on other bones can stop the game); soldiers
by kind, never one by his number; what a unit has of its own for the same animation (Only this unit, its own animation
from Blender) still plays for it, said on its tick. A figure plays one copy of a clip: ticking it for one takes it out
of the mod's other copies of that clip, said. The build (rusemod.build.unit_own_clips) does what the ticks say, and says
what each finds. Not tried in the game yet."""
from __future__ import annotations

from pathlib import Path

LISTINGS_KEPT = 256   # units whose listings are kept in memory (each read from the game index once)


class DecoyCopyCalls:
    # --- the mod's copies, read and written ---
    def _decoy_copies_now(self) -> tuple[Path, dict, dict]:
        """(the current mod's folder, its copies.toml as written {id: table}, as the build reads it {id: copy}); a
        StudioError without a mod, or when the file can't be read."""
        from rusemod import anim
        from .api import StudioError
        mod = self._mod_dir()
        if mod is None:
            raise StudioError("Pick or make a mod first: animations are changed in a mod.")
        try:
            return mod, anim.read_copies(mod), anim.mod_copies(mod)
        except anim.AnimError as exc:
            raise StudioError(f"{exc}. Fix that file (or delete it) first: your copies of animations are kept "
                              f"there.") from None

    @staticmethod
    def _decoy_copy_entry(table: dict, cid) -> dict:
        from .api import StudioError
        e = table.get(cid) if isinstance(cid, str) else None
        if not isinstance(e, dict):
            raise StudioError(f"This mod has no copy {cid} any more: it may have been deleted.")
        return e

    def _decoy_copy_write(self, mod: Path, table: dict) -> None:
        from rusemod import anim
        from .api import StudioError, file_error, oserror_of
        try:
            anim.write_copies(mod, table)
        except anim.AnimError as exc:
            raise StudioError(f"{exc}. Fix that file (or delete it) first: your copies of animations are kept "
                              f"there.") from None
        except OSError as exc:
            raise file_error(oserror_of(exc) or exc, mod / anim.COPIES) from None

    @staticmethod
    def _decoy_copy_name(name, table: dict, cid: str | None = None) -> str:
        """`name` as a copy's name: 1 to 80 letters, no other copy of the mod called so (any case)."""
        from rusemod import anim
        from .api import StudioError
        name = name.strip() if isinstance(name, str) else ""
        if not name or len(name) > anim.COPY_NAME_MOST or any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise StudioError(f"A copy's name is 1 to {anim.COPY_NAME_MOST} letters.")
        if any(k != cid and str(e.get("name", "")).strip().lower() == name.lower() for k, e in table.items()):
            raise StudioError(f"This mod has a copy called {name} already: give this one another name.")
        return name

    def _decoy_copy_out(self, cid: str, c: dict) -> dict:
        """A copy (`c`, anim.mod_copies') as the page shows it: a clip row's fields (decoy_anim_list's) with the copy's
        name and changes, its id ("copy"), the name of the game's animation it is a copy of ("clip_name"), how many
        units are ticked for it ("units") and the ticks ({a unit's name: [figure paths], [] for every one})."""
        r = self._decoy_clip_row(c["clip"])
        out = self._decoy_edit_out(c["edit"])
        return {"copy": cid, "member": r["member"] if r else c["clip"], "kind": r["kind"] if r else "other",
                "name": c["name"], "clip_name": r["name"] if r else c["clip"].rsplit("\\", 1)[-1],
                "seconds": r["seconds"] if r else 0.0, "frames": r["frames"] if r else 0,
                "bones": r["bones"] if r else 0, "names": r["names"] if r else [], "units": len(c["units"]),
                "clip_units": len(r["units"]) if r else 0, "missing": r is None, **out,
                "changed": bool(out["speed"] != 100.0 or out["from"] or out["mine"] or out["tweaks"]),
                "ticked": {u: list(f) for u, f in sorted(c["units"].items())}}

    def _decoy_copy_get(self, cid: str) -> dict:
        _mod, _table, copies = self._decoy_copies_now()
        if cid not in copies:
            self._decoy_copy_entry({}, cid)
        return self._decoy_copy_out(cid, copies[cid])

    @staticmethod
    def _decoy_toml_of(e: dict) -> dict:
        """A clip's changes as rusemod.anim reads them (speed, from, bones) in the form copies.toml writes them; its
        file is copied apart."""
        from rusemod import anim
        entry: dict = {}
        if e.get("speed", 100.0) != 100.0:
            entry["speed"] = float(e["speed"])
        if e.get("from"):
            entry["from"] = anim.clip_key(e["from"])
        bones = {b: {k: x for k, x in (("size", v["size"]), ("turn", list(v["turn"]) if v["turn"] else None))
                     if x is not None and not (k == "size" and x == 1.0)} for b, v in (e.get("bones") or {}).items()}
        bones = {b: v for b, v in bones.items() if v}
        if bones:
            entry["bone"] = bones
        return entry

    # --- which of a unit's figures play a clip (the build's walk, from the game index) ---
    def _decoy_listings(self, address: str) -> list:
        """rusemod.animmodel.unit_listings of the unit at `address` (a new unit's: the unit it copies), kept per game
        index; [] when the index can't say."""
        from rusemod import animmodel
        try:
            edits = self._edits()
        except Exception:  # noqa: BLE001 (a mod file that can't be read: the game's own unit is still read)
            edits = None
        try:
            real = self._resolve(edits, address)[0].split(":", 1)[0]
            key = (str(self._path()), real)
        except Exception:  # noqa: BLE001 (no game: nothing to read)
            return []
        kept = getattr(self, "_decoy_listings_kept", None)
        if kept is None:
            kept = self._decoy_listings_kept = {}
        if key not in kept:
            try:
                ix = self._open()
            except Exception:  # noqa: BLE001 (no game index yet: nothing known)
                return []
            try:
                rows = animmodel.unit_listings(ix.db, real)
            finally:
                ix.close()
            if len(kept) >= LISTINGS_KEPT:
                kept.clear()
            kept[key] = rows
        return kept[key]

    def _decoy_figures_playing(self, address: str, member: str) -> list:
        """[(figure path, [the actions it plays `member` for])] of the unit at `address`, in the game's order."""
        out = []
        for path, _model, rows in self._decoy_listings(address):
            acts = [a for a, clip in rows if clip == member]
            if acts:
                out.append((path, acts))
        return out

    # --- where a new copy starts ---
    def _decoy_copy_start(self, mod: Path, r: dict, unit: str | None, copy: str | None, copies: dict) -> tuple:
        """(a new copy's changes in copies.toml's form, the clip file it starts from or None, where it starts:
        "copy", "own", "blender", "copy_ticked", "all" or "game"): as copy `copy` is now; else from a unit's page as
        that unit plays the clip now (its own copy of it, Only this unit; else its own animation for the actions that
        play it, from Blender, the one most of them play; else a copy it is ticked in); else as every unit plays it in
        the mod (clips.toml, files/replace); else the game's own."""
        from rusemod import anim
        from .api import StudioError
        member = r["member"]
        if copy:
            c = copies.get(copy)
            if c is None:
                self._decoy_copy_entry({}, copy)
            if c["clip"] != member:
                raise StudioError(f"The copy {c['name']} is a copy of another animation.")
            return self._decoy_toml_of(c["edit"]), c["edit"].get("file"), "copy"
        if unit:
            name = self._decoy_unit_name(unit)
            try:
                own = anim.mod_unit_clips(mod).get(name) or {}
            except anim.AnimError as exc:
                raise StudioError(f"{exc}. Fix that file (or delete it) first: what this unit plays is kept "
                                  f"there.") from None
            e = (own.get("clips") or {}).get(member)
            if e is not None:
                return self._decoy_toml_of(e), e.get("file"), "own"
            actions = own.get("actions") or {}
            counts: dict = {}
            for fig, acts in self._decoy_figures_playing(unit, member):
                for a in acts:
                    f = actions.get((a, fig)) or actions.get((a, None))
                    if f is not None:
                        counts[f] = counts.get(f, 0) + 1
            if counts:
                return {}, sorted(counts, key=lambda f: (-counts[f], str(f)))[0], "blender"
            for c in copies.values():
                if c["clip"] == member and name in c["units"]:
                    return self._decoy_toml_of(c["edit"]), c["edit"].get("file"), "copy_ticked"
        e = self._decoy_clip_edits().get(member)
        if e:
            return self._decoy_toml_of(e), e.get("file"), "all"
        return {}, None, "game"

    # --- what the page calls ---
    def decoy_copies(self) -> dict:
        """The current mod's copies of animations, by name: {"copies": [each as decoy_copy_* give it], "mod": whether a
        mod is open}."""
        if self._mod_dir() is None:
            return {"copies": [], "mod": False}
        _mod, _table, copies = self._decoy_copies_now()
        rows = [self._decoy_copy_out(cid, c) for cid, c in copies.items()]
        return {"copies": sorted(rows, key=lambda x: (x["name"].lower(), x["copy"])), "mod": True}

    def decoy_copy_make(self, member: str, name: str, unit: str | None = None, copy: str | None = None) -> dict:
        """Copy this animation…: a copy of the game's clip `member` called `name` in the current mod, starting as
        copy `copy` is now, or (from a unit's page, `unit` its address) as that unit plays it now, or as every unit
        plays it in the mod (_decoy_copy_start); ticked for no unit yet. Its clip file, when it starts from one, is
        copied into files/anim/copies/<its id>.baf (a motion capture's credit beside it too). Returns the copy, with
        "started": where it started."""
        from rusemod import anim
        from .decoy import DecoyError
        r = self._decoy_clip_row(member)
        if r is None:  # not a game rule: no such animation in the game's packs
            raise DecoyError(f"{member} isn't one of the game's animations")
        mod, table, copies = self._decoy_copies_now()
        name = self._decoy_copy_name(name, table)
        cid = anim.copy_id(name, set(table))
        entry, source, started = self._decoy_copy_start(mod, r, unit, copy, copies)
        entry = {"name": name, "clip": anim.clip_key(r["member"]), **entry}
        made: list = []
        with self._saving:
            try:
                if source is not None:
                    rel = f"{cid}.baf"
                    own = mod / anim.COPY_DIR / rel
                    own.parent.mkdir(parents=True, exist_ok=True)
                    data = Path(source).read_bytes()
                    made.append(own)
                    own.write_bytes(data)
                    side = Path(source).with_suffix(".toml")
                    if side.is_file():   # (a motion capture's credit goes with it)
                        made.append(own.with_suffix(".toml"))
                        own.with_suffix(".toml").write_text(side.read_text(encoding="utf-8"), encoding="utf-8")
                    entry["file"] = rel
                table[cid] = entry
                self._decoy_copy_write(mod, table)
            except BaseException:
                for f in made:   # (nothing of it left behind)
                    f.unlink(missing_ok=True)
                raise
        return {**self._decoy_copy_get(cid), "started": started}

    def decoy_copy_rename(self, copy: str, name: str) -> dict:
        """The copy `copy` called `name` from now on (its id, file and ticks stay)."""
        mod, table, _copies = self._decoy_copies_now()
        e = self._decoy_copy_entry(table, copy)
        name = self._decoy_copy_name(name, table, copy)
        with self._saving:
            table[copy] = {**e, "name": name}
            self._decoy_copy_write(mod, table)
        return self._decoy_copy_get(copy)

    def decoy_copy_delete(self, copy: str) -> dict:
        """The copy `copy` out of the mod, its clip file and credit too: the units ticked for it play the animation
        as before. Returns {"copy", "name", "units": how many units were ticked for it}."""
        from rusemod import anim
        mod, table, _copies = self._decoy_copies_now()
        e = self._decoy_copy_entry(table, copy)
        with self._saving:
            table.pop(copy)
            self._decoy_copy_write(mod, table)
            rel = e.get("file")
            if isinstance(rel, str) and anim._COPY_FILE.match(rel) and \
                    not any(o.get("file") == rel for o in table.values()):
                own = mod / anim.COPY_DIR / rel
                for f in (own, own.with_suffix(".toml")):
                    f.unlink(missing_ok=True)
                folder = mod / anim.COPY_DIR
                if folder.is_dir() and not any(folder.iterdir()):   # (no empty folder left)
                    folder.rmdir()
        return {"copy": copy, "name": e.get("name", copy), "units": len(e.get("units") or {})}

    def decoy_copy_players(self, copy: str, lang: str = "base") -> dict:
        """Who plays it: every unit that plays the clip the copy `copy` is a copy of, the mod's own first then the
        game's, each with its figures that play it (the build's walk: rusemod.animmodel.unit_listings) and what each
        plays now. {"copy": the copy, "units": [{"address", "name", "new", "nation", "ticked": "all", "some" or None,
        "own_copy": the unit has its own copy of the clip (Only this unit, which it plays instead), "own_model": it has
        its model's own animations (the figures wearing its model play those), "figures": [{"path", "kind"
        (ruse_studio.modelfit.figure_kind), "number" (1, 2... among figures of its kind; 0 when it's the only one),
        "actions": how many of its actions play the clip, "own_rows": how many of those play the unit's own animation
        (Blender's), "ticked", "other": the name of another copy of the clip it plays, or None}]}], "unreached": the
        names of the units that play the clip only through a part a copy can't reach (one shared with other units)}."""
        from rusemod import anim
        from .modelfit import figure_kind
        mod, _table, copies = self._decoy_copies_now()
        if copy not in copies:
            self._decoy_copy_entry({}, copy)
        c = copies[copy]
        member = c["clip"]
        r = self._decoy_clip_row(member)
        game = set(r["units"]) if r else set()
        try:
            own_all = anim.mod_unit_clips(mod)
        except anim.AnimError:   # (its units.toml can't be read: the ticks are still shown, without what it says)
            own_all = {}
        try:
            edits = self._edits()
        except Exception:  # noqa: BLE001 (a mod file that can't be read: the game's units are still listed)
            edits = None
        listed = [u for u in self.units(lang)["units"] if u.get("kind") != "buildings"]
        mine = [u for u in listed if u.get("new") and self._resolve(edits, u["address"])[0] in game]
        theirs = [u for u in listed if not u.get("new") and u["address"] in game]
        others = {k: o for k, o in copies.items() if k != copy and o["clip"] == member}
        rows, unreached = [], []
        for u in mine + theirs:
            try:
                name = self._decoy_unit_name(u["address"])
            except Exception:  # noqa: BLE001 (not a unit a copy can be ticked for)
                continue
            figs = self._decoy_figures_playing(u["address"], member)
            if not figs:
                unreached.append(u["name"])
                continue
            own = own_all.get(name) or {}
            actions = own.get("actions") or {}
            ticked = c["units"].get(name)
            kinds = [figure_kind(p) for p, _a in figs]
            seen: dict = {}
            fig_rows = []
            for (path, acts), kind in zip(figs, kinds):
                seen[kind] = seen.get(kind, 0) + 1
                on = ticked is not None and (not ticked or path in ticked)
                other = None if on else next((o["name"] for o in others.values() if name in o["units"]
                                              and (not o["units"][name] or path in o["units"][name])), None)
                fig_rows.append({"path": path, "kind": kind, "number": seen[kind] if kinds.count(kind) > 1 else 0,
                                 "actions": len(acts), "ticked": on, "other": other,
                                 "own_rows": sum(1 for a in acts if (a, path) in actions or (a, None) in actions)})
            n = sum(1 for f in fig_rows if f["ticked"])
            rows.append({"address": u["address"], "name": u["name"], "new": bool(u.get("new")),
                         "nation": u.get("nation_name") or "", "figures": fig_rows,
                         "ticked": "all" if n == len(fig_rows) else "some" if n else None,
                         "own_copy": member in (own.get("clips") or {}), "own_model": bool(own.get("animations"))})
        return {"copy": self._decoy_copy_out(copy, c), "units": rows, "unreached": sorted(set(unreached))}

    def decoy_copy_tick(self, copy: str, address: str, figures=None) -> dict:
        """The unit at `address` ticked for the copy `copy`: `figures` None unticks it, [] ticks every figure of it that
        plays the clip, a list ticks those (their paths, as decoy_copy_players gives them; all of them is []). A figure
        ticked here comes out of the mod's other copies of the same clip (a figure plays one copy of a clip). Returns
        {"copy": the copy, "moved": [the names of the other copies a figure came out of]}."""
        from rusemod import anim
        from .api import StudioError
        mod, table, copies = self._decoy_copies_now()
        e = self._decoy_copy_entry(table, copy)
        name = self._decoy_unit_name(address)
        member = copies[copy]["clip"]
        playing = [p for p, _a in self._decoy_figures_playing(address, member)]
        want = None
        if figures is not None:
            if not isinstance(figures, list) or any(not isinstance(f, str) for f in figures):
                # not a game rule: what the page sends
                raise StudioError("Tick a unit, or some of its soldiers and parts, for a copy.")
            if not playing:
                raise StudioError("This unit doesn't play this animation, so it can't play a copy of it.")
            bad = [f for f in figures if f not in playing]
            if bad:
                raise StudioError(f"This unit has no soldier or part {bad[0]} that plays this animation.")
            want = [] if not figures or set(figures) >= set(playing) else [p for p in playing if p in set(figures)]
        moved = []
        with self._saving:
            units = dict(e.get("units") or {})
            if want is None:
                units.pop(name, None)
            else:
                units[name] = want
            table[copy] = {**e, "units": units}
            if want is not None:
                taking = set(want or playing)
                for k, o in list(table.items()):
                    if k == copy or anim._member(str(o.get("clip", ""))) != member:
                        continue
                    ou = dict(o.get("units") or {})
                    if name not in ou:
                        continue
                    theirs = set(ou[name] or playing)
                    if not theirs & taking:
                        continue
                    left = [p for p in playing if p in theirs - taking]
                    if left:
                        ou[name] = left
                    else:
                        ou.pop(name)
                    table[k] = {**o, "units": ou}
                    moved.append(str(o.get("name", k)))
            self._decoy_copy_write(mod, table)
        return {"copy": self._decoy_copy_get(copy), "moved": moved}

    # --- the editor's changes to a copy (DecoyCalls.decoy_anim_set / _reset / _preview, decoy_mocap_use with `copy`) ---
    def _decoy_copy_save(self, r: dict, copy: str, change) -> dict:
        """Change the copy `copy` of clip `r` in copies.toml: `change(its table)` gives its new table."""
        from .api import StudioError
        mod, table, copies = self._decoy_copies_now()
        e = self._decoy_copy_entry(table, copy)
        if copies[copy]["clip"] != r["member"]:
            raise StudioError(f"The copy {e.get('name', copy)} is a copy of another animation.")
        with self._saving:
            table[copy] = change(dict(e))
            self._decoy_copy_write(mod, table)
        return self._decoy_copy_get(copy)

    def _decoy_copy_reset(self, r: dict, copy: str) -> dict:
        """The copy's changes out (its speed, stand-in, bones and clip file, and the file's credit): the units ticked
        for it play the game's clip until it is changed again; its name and ticks stay."""
        from rusemod import anim
        mod, table, _copies = self._decoy_copies_now()
        rel = self._decoy_copy_entry(table, copy).get("file")
        got = self._decoy_copy_save(r, copy, lambda e: {k: v for k, v in e.items()
                                                        if k not in ("speed", "from", "bone", "file")})
        if isinstance(rel, str) and anim._COPY_FILE.match(rel):
            with self._saving:
                if not any(o.get("file") == rel for o in anim.read_copies(mod).values()):
                    own = mod / anim.COPY_DIR / rel
                    for f in (own, own.with_suffix(".toml")):
                        f.unlink(missing_ok=True)
        return got

    def _decoy_copy_edit(self, copy: str) -> dict:
        """The copy's changes as rusemod.anim.made takes them."""
        _mod, _table, copies = self._decoy_copies_now()
        if copy not in copies:
            self._decoy_copy_entry({}, copy)
        return copies[copy]["edit"]

    def _decoy_copy_file(self, copy: str) -> Path:
        """Where the copy's own clip file goes (files/anim/copies/<its id>.baf), the copy checked to be the mod's."""
        from rusemod import anim
        mod, table, _copies = self._decoy_copies_now()
        self._decoy_copy_entry(table, copy)
        return mod / anim.COPY_DIR / f"{copy}.baf"

    def _decoy_unit_copies(self, address: str) -> dict:
        """{a clip's path: [each copy of it in the current mod ticked for the unit at `address`, as the page shows a
        copy, with "figures": the figures it's ticked for ([] every one)]}; {} without a mod or a unit's name."""
        try:
            name = self._decoy_unit_name(address)
            _mod, _table, copies = self._decoy_copies_now()
        except Exception:  # noqa: BLE001 (no mod, not a unit, or a copies.toml that can't be read: none shown)
            return {}
        out: dict = {}
        for cid, c in copies.items():
            if name in c["units"]:
                out.setdefault(c["clip"], []).append({**self._decoy_copy_out(cid, c), "figures": list(c["units"][name])})
        return out
