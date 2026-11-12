"""A squad's soldiers, each changed on his own, the whole squad in one Blender (StudioApi's SquadBlenderCalls; the
squad work's Phase 1, scratch/animmodels/SQUAD-CONTRACTS-2026-11-11.md section 4, the calls the squad page uses).

The owner, 2026-11-11: "if you're able to have the whole squad inside of Blender, why not just make it to where if you
change one unit's appearance in Blender, that it just comes back like that normally" (#4462883); "you change one
soldier's color, only that soldier should change color" (#4462962); "Yes, it matches" to the list in the contracts'
section 2 (#4463065).

- squad_info: what the squad is made of, read from the game and the mod: how many soldiers (the game's one setting,
  NbSoldatInGroupeCombat of $/GFX/Everything/UniteBehaviourDescriptor, with the mod's change of it), one line per kind
  of soldier (StudioApi._soldier_kinds: the riflemen, then the last man's other look; a squad all of one look is one
  line), what each fires by the game's own rule for its squads (the squad contracts' section 3, read 2026-11-11: the
  last man wears the squad's second figure, a weapon whose ammunition has NeedModelChange is fired by the last man, a
  second such weapon by the one before him; the squad's other weapons by the men holding none of those),
  the weapons named as the Studio's weapon list names them (StudioApi.weapons, api.py: each weapon's ammunition with
  the mod's pick, named by _ammo_names from the game's two texts of it, its kind and calibre, which the game's card
  shows), each soldier's 3D view (as unit_preview makes them) and where the mod keeps his model.
- squad_blender: ONE Blender with every soldier line side by side (rusemod.blender_model's squad mode), each from what
  he looks like in the mod now: the file his model was last brought back from this Blender (kept/), but only while
  his model in the mod is still the one made from it (an Import model from a file since wins); else his own model
  (files/models/<unit>.glb, or <unit>@<kind>.glb), its bones put at their rest poses (rusemod.gltf.rest_bones_glb);
  else the game model his figure draws (rusemod.gltf.model_glb, rest_bones, as Change it in Blender writes it) wearing
  the squad's Custom uniform paint when it has one (R2: a modder's paint is kept). Each soldier's pictures are his own
  (his file's; Blender gives each file its own, and blender_model copies any it would share), so painting one never
  paints another. The work folder: <mod>/blender/<unit>/squad/ (never packed, never read by the build).
- squad_blender_back: the open Blender is asked to send (rusemod.blender.ask_to_send), a closed one's last sending is
  used; Blender writes one file per soldier; a soldier is taken in (Import model with his kind) only when his file
  is not byte for byte the one Blender wrote of him when the squad opened or when he was last taken in. Blender 4.5
  writes an untouched soldier byte for byte the same, measured 2026-11-11 (scratch/animmodels/squadblender/
  measure.json: three writes in one session, and two sessions); anything else that differs (a renamed object too)
  counts as changed, so nothing the modder did is ever left out (taking in an untouched soldier again keeps his look).
  Every other soldier's files in the mod stay byte for byte as they were, with one exception the build forces: a
  squad wearing a Custom uniform (its .copy.toml) can't also have a model of its own (rusemod.build.unit_own_copies),
  so Import model takes the uniform off; the soldiers still wearing it are then taken in too, from Blender as they
  were, paint and all, so their look stays ("uniform_kept"). What each soldier's picture had for alpha (the game's
  side colour where low, shine where high) goes back in with him: Blender's export drops it (it keeps no picture a
  material doesn't show), so the alpha the Studio gave each material comes back by its name (rusemod.modelin reads it
  from the material's rusemod_alpha_texture).
- soldier_import, soldier_reset: Import model and Use the copied unit's model for one soldier (model_import and
  model_import_remove with his kind; the riflemen: none), their answers as they are.
The calls the d43f0c6d page used (model_blender, model_blender_back with a kind) stay as they were.

Each squad its own number of soldiers, each soldier his own look (the squad work's Phases 2-3, rusemod.squads; the
owner, 2026-11-12: "I would only want to change it for this one squad. Not every squad in the game.", and his picks
the same night: at least 2, at most 8 for now, an added soldier a figure only, the squad's health and weapons as set
on its page):
- one line per soldier, soldier 1 first ("1".."n"): what he fires by the game's rule (the last soldiers the weapons
  whose ammunition has NeedModelChange), his look: his own (files/models/<unit>@<i>.glb, Import model's with his number
  as the kind), else the model of the figure the game gives his place as the mod has it (the riflemen's own model, the
  bazooka man's) or the game's; a squad's own number in files/models/<unit>.squad.toml (none: the game's setting).
- soldier_add: Blender opens with just the new soldier, starting as the soldier he copies looks (one of this squad's,
  another squad's, or a model file fitted to the soldier's bones); he joins the squad when he's brought back (Bring my
  changes back), standing before the squad's last soldiers who fire its NeedModelChange weapons (so its bazooka man
  stays last), the soldiers after him one number on. soldier_remove: the soldier goes, his own look kept aside in the
  squad's Blender folder (removed/), the soldiers after him one number down. Never fewer than 2 soldiers, nor than the
  weapons its last soldiers fire one each; never more than 8; each refused in a plain sentence.
- soldier_blender: Blender with one soldier alone; squad_blender with every soldier."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import time
import uuid
from pathlib import Path

SQUAD_DIR = "squad"   # <mod>/blender/<the unit's name>/squad/
SEND_WAIT = 60.0      # seconds Bring my changes back waits for an open Blender to send
BEHAVIOUR = "$/GFX/Everything/UniteBehaviourDescriptor"   # the game's one behaviour setting, every squad's
COUNT = "NbSoldatInGroupeCombat"                          # its soldiers in a squad (5 in the game)
NEED = "NeedModelChange"                                  # an ammunition fired by the squad's last men (TAmmunition)
MAIN = "fusilier"                                         # the riflemen's figure (GfxDescriptorFusilier)
LAST = "bazooka"                                          # the last man's (GfxDescriptorBazooka)
WORD = {"fusilier": "rifleman", "bazooka": "bazookaman"}  # each figure's words (words.toml blender_squad_<word>)
PLURAL = {"rifleman": "riflemen", "bazookaman": "bazookamen", "soldier": "soldiers"}


def _sha(path: Path) -> str | None:
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _read(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(path: Path, data: dict) -> None:
    """A JSON file written beside itself first, then put in place (Blender or a second call never reads half)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(part, path)


def _put(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    os.replace(part, path)


def plural_form(lang: str, n: int) -> str:
    """Which of a word's three number forms (words.toml blender_squad_<word>_one/_few/_many) `n` takes in `lang`:
    Russian, Polish and Czech have a form for 2-4 (and 22-24...) of their own; French counts 0 as one; the others one
    and many; Japanese, Chinese and Persian say all three the same."""
    if lang in ("ru", "pol"):
        if n == 1 or (lang == "ru" and n % 10 == 1 and n % 100 != 11):
            return "one"
        return "few" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "many"
    if lang == "cz":
        return "one" if n == 1 else "few" if 2 <= n <= 4 else "many"
    if lang == "fr":
        return "one" if n in (0, 1) else "many"
    return "one" if n == 1 else "many"


class SquadBlenderCalls:
    # --- what the squad is made of ---
    def _kind_lines(self, address: str) -> list:
        """The squad's kinds of soldier, the riflemen first: [{"id": his figure as _soldier_kinds names it, "kind": what
        Import model takes for that kind (None: the riflemen, the unit's own model), "model": the game model his figure
        draws, "word": his words' name}]. A squad whose soldiers all draw one model is one (its riflemen's figure)."""
        kinds = self._soldier_kinds(address)
        if kinds:
            main = next(iter(kinds))
            return [{"id": k, "kind": None if k == main else k, "model": m, "word": WORD.get(k, "soldier")}
                    for k, m in kinds.items()]
        figs = [(p[len("GfxDescriptor"):].lower(), m) for p, m in self._soldier_figures(address)
                if m and "." not in p and p.startswith("GfxDescriptor")
                and p not in ("GfxDescriptor", "GfxDescriptorCadavre", "GfxDescriptorIconeCadavre")]
        ids = [k for k, _m in figs]
        sid = MAIN if MAIN in ids else (ids[0] if ids else MAIN)
        return [{"id": sid, "kind": None, "model": next((m for k, m in figs if k == sid), None), "word": "soldier"}]

    def _squad_lines(self, address: str) -> list:
        """The squad's soldiers, one line each, soldier 1 first (rusemod.squads): {"id": his number "1".."n", "kind":
        the same (what Import model takes for his own look, files/models/<unit>@<i>.glb), "number", "model": the game
        model of the figure the game gives his place, "word": that figure's words' name, "place": that figure's kind
        line ("fusilier", "bazooka"), "base": the kind whose model file he wears when he has no look of his own (None:
        the riflemen's, the unit's own model)}."""
        from rusemod import squads as sq
        kinds = self._kind_lines(address)
        figs = {p: m for p, m in self._soldier_figures(address) if m}
        has_last = bool(figs.get(sq.LAST))
        n = self._squad_count(address)
        out = []
        for i in range(1, n + 1):
            place = sq.place_figure(i, n, has_last)[len("GfxDescriptor"):].lower()
            line = next((ln for ln in kinds if ln["id"] == place), kinds[0]) if len(kinds) > 1 else kinds[0]
            out.append({"id": str(i), "kind": str(i), "number": i,
                        "model": figs.get(sq.place_figure(i, n, has_last)) or line["model"], "word": line["word"],
                        "place": line["id"], "base": line["kind"]})
        return out

    def _squad_file(self, address: str) -> Path | None:
        """The squad's own number of soldiers, files/models/<its name>.squad.toml (made or not); None for a game unit."""
        from rusemod import squads as sq
        own = self._own_model_file(address)
        return own.with_name(f"{own.stem}{sq.SUFFIX}") if own is not None else None

    def _squad_count(self, address: str | None = None) -> int:
        """How many soldiers a squad has: its own number (files/models/<its name>.squad.toml, a squad of this mod's
        own: rusemod.squads), else the game's one setting for every squad, with the mod's change of it."""
        from rusemod import squads as sq
        from .api import StudioError
        own = self._squad_file(address) if address else None
        if own is not None and own.is_file():
            try:
                return sq.read_count(own)
            except sq.SquadError as exc:   # (the file's own mistake, said as it is)
                raise StudioError(str(exc)) from None
        return self._shared_count()

    def _shared_count(self) -> int:
        """The game's one setting for every squad's soldiers, with the mod's change of it."""
        from .api import StudioError
        from .edits import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        mine = edits.get(BEHAVIOUR, COUNT) if edits else None
        if isinstance(mine, (int, float)) and not isinstance(mine, bool):
            return int(mine)
        ix = self._open()
        try:
            found = next((n for p, n, _t in ix.show(BEHAVIOUR)["values"] if p == COUNT and n is not None), None)
        except KeyError:
            found = None
        finally:
            ix.close()
        if found is None:
            # not a game rule: the game's own data, read through the Studio's index of it
            raise StudioError("The number of soldiers in a squad couldn't be read from the game.")
        return int(found)

    @staticmethod
    def _needs_model_change(ix, edits, ammo: str, resolve) -> bool:
        """Whether an ammunition has NeedModelChange (the mod's change of it, else the game's; a copy made in the mod:
        its source's)."""
        mine = edits.get(ammo, NEED) if edits else None
        if isinstance(mine, (int, float)):
            return bool(mine)
        if isinstance(mine, str):
            return mine.strip().lower() in ("true", "1")
        real, _new = resolve(edits, ammo)
        try:
            return any(p == NEED and n for p, n, _t in ix.show(real)["values"])
        except KeyError:
            return False

    def _squad_weapons(self, address: str, lang: str) -> list:
        """The squad's weapons in its order: [(their name as the weapon list shows it, its kind alone, whether its
        ammunition has NeedModelChange)]."""
        from .api import StudioError
        from .edits import EditsFileError
        try:
            listed = self.weapons(address, lang)["weapons"]
        except (KeyError, StudioError):
            return []
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        ix = self._open()
        try:
            out = []
            for w in listed:
                ammo = w["ammo"]["address"]
                if not ammo:
                    continue
                name = w["ammo"]["name"] or ammo.rsplit("/", 1)[-1]
                out.append((name, name.split(" · ")[0], self._needs_model_change(ix, edits, ammo, self._resolve)))
        finally:
            ix.close()
        return out

    @staticmethod
    def _squad_men(lines: list, count: int, weapons: list) -> list:
        """[(the line he wears, [his weapons])] for each man of the squad, first to last, by the game's rules (the
        squad contracts' section 3): the last man wears the second figure, the squad's NeedModelChange weapons go to
        the last man, then the one before him; a man holding none of those fires the squad's others (which of those
        men fires each of them is not known: taken as every one)."""
        ids = [ln["id"] for ln in lines]
        first = MAIN if MAIN in ids else ids[0]
        last = LAST if LAST in ids else first
        need = [w for w in weapons if w[2]]
        others = [w for w in weapons if not w[2]]
        carry: dict = {i: [] for i in range(count)}
        for j, w in enumerate(need):
            if count - 1 - j >= 0:
                carry[count - 1 - j].append(w)
        return [(last if i == count - 1 else first, carry[i] or list(others)) for i in range(count)]

    @staticmethod
    def _squad_line(men: list, lines: list, lang: str) -> str:
        """The squad in one plain sentence in `lang`: "5 soldiers: 4 riflemen (Infantry weapon, Grenades), 1 bazooka
        man (Bazooka)." The men side by side wearing the same and carrying the same, counted together."""
        from .api import words
        w = words(lang)
        word = {ln["id"]: ln["word"] for ln in lines}
        sep = w["blender_squad_list_sep"]

        def counted(stem: str, n: int) -> str:
            return w[f"blender_squad_{PLURAL[stem]}_{plural_form(lang, n)}"].format(n=n)
        groups: list = []
        for look, carried in men:
            names = list(dict.fromkeys(k for _full, k, _need in carried))
            if groups and groups[-1][0] == look and groups[-1][2] == names:
                groups[-1][1] += 1
            else:
                groups.append([look, 1, names])
        soldiers = counted("soldier", len(men))
        if len(groups) == 1 and word.get(groups[0][0]) == "soldier":
            return (w["blender_squad_line_all"].format(soldiers=soldiers, weapons=sep.join(groups[0][2]))
                    if groups[0][2] else w["blender_squad_line_none"].format(soldiers=soldiers))
        parts = [w["blender_squad_group"].format(who=counted(word.get(look, "soldier"), n), weapons=sep.join(names))
                 if names else counted(word.get(look, "soldier"), n) for look, n, names in groups]
        return w["blender_squad_line"].format(soldiers=soldiers, groups=sep.join(parts))

    def _squad_work(self, address: str) -> Path | None:
        """The squad's Blender work folder, <mod>/blender/<its name>/squad/ (made or not); None for a game unit."""
        from .modelblender import WORK
        own = self._own_model_file(address)
        mod = self._mod_dir()
        return mod / WORK / own.stem / SQUAD_DIR if own is not None and mod is not None else None

    def _squad_open(self, address: str, work: Path | None) -> bool:
        """Whether a Blender the Studio opened on this squad is still open: its whole-squad one, or one of its soldiers'
        alone (Change it in Blender)."""
        folders = [work] if work is not None else []
        try:
            folders += [self._model_work(address, None)[0]]
            folders += [self._model_work(address, k)[0] for k in list(self._soldier_kinds(address))[1:]]
        except Exception:  # noqa: BLE001  (a game unit has none of its own)
            pass
        for folder in folders:
            proc = self._blenders.get(str(folder))
            if proc is not None and proc.poll() is None:
                return True
        return False

    def _soldier_preview(self, address: str, line: dict, own: Path | None, models: list) -> dict | None:
        """A soldier's 3D view for the page, as unit_preview makes one: his own model in the mod (a copy in the cache),
        else the game model his figure draws (made once per game build, in unit_preview's cache, shared with it), with
        the squad's Custom uniform paint when it has some ("paint", as unit_preview's); None when there's none."""
        import re

        from rusemod import gltf, models as gamemodels
        from rusemod.build import find_pack
        if own is not None and own.is_file():
            st = own.stat()
            name = hashlib.sha1(f"{own}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16] + ".glb"
            copy = self.cache_dir / "units" / "own" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(own, copy)
            return {"url": f"cache/units/own/{name}"}
        model = self._figure_model(line, models)
        game = self._game()
        if model is None or game is None:
            return None
        st = find_pack(game, "ZZ_Win.dat").stat()
        build = f"{st.st_size}-{int(st.st_mtime)}-v{self.PREVIEW_VERSION}"   # (unit_preview's names, so one cache)
        stem = re.sub(r"[^A-Za-z0-9_-]", "_", model.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", ""))
        file = self.cache_dir / "units" / build / f"{stem}-{hashlib.sha1(model.encode()).hexdigest()[:8]}.glb"
        if not file.is_file():
            with self._previews_lock:
                if not file.is_file():
                    lib = gamemodels.Library(game)
                    try:
                        glb, _pictures, _summary = gltf.model_glb(lib, model, side=self.PREVIEW_SIDE)
                    finally:
                        lib.close()
                    _put(file, glb)
        out = {"url": f"cache/units/{build}/{file.name}"}
        paint = {}
        for tex, (colour, _alpha) in self._paint_of(address).items():   # (unit_preview's: its copy's, or files/replace)
            if colour is None:
                continue
            cst = colour.stat()
            name = hashlib.sha1(f"{colour}|{cst.st_size}|{cst.st_mtime_ns}".encode()).hexdigest()[:16] + ".png"
            copy = self.cache_dir / "units" / "paint" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(colour, copy)
            paint[tex] = f"cache/units/paint/{name}"
        if paint:
            out["paint"] = paint
        return out

    @staticmethod
    def _figure_model(line: dict, models: list) -> str | None:
        """The game model a soldier line's figure draws, as the game's model library names it (one of `models`,
        StudioApi._look_models'), or None."""
        from rusemod.unitmodel import model_key
        want = model_key(line["model"]) if line.get("model") else None
        found = [m for m in models if "_dest" not in m.lower()]
        return next((m for m in found if want is not None and model_key(m) == want), None)

    def squad_info(self, address: str, lang: str = "us") -> dict | None:
        """What a squad is made of, for the squad page (the contracts' section 4): None for a unit that isn't a squad of
        soldiers; else {"name", "copies": the game unit it copies (its name; None for a game unit), "own": whether it's
        a new unit of this mod (only those get models of their own), "count", "line": one sentence in `lang`,
        "soldiers": one row per line, the riflemen first: {"id", "label", "count", "fires", "preview", "own_model",
        "from": the file his model was made from (its name), "blender_changed": whether his model came back from
        Blender, "kept": where the mod keeps his model, made or not}, "blender": {"open", "work", "made", "found":
        whether the Studio finds Blender, "waiting": whether this squad's Blender sent something not brought back},
        "can": {"blender", "import", "reset", "add", "remove"}, "why_not": a sentence when it can't be changed}. Its
        weapons are named in the game's texts in `lang`; the game has no Persian texts, so in Persian they read in
        English (rusemod.schema.game_lang), the Studio's own words around them in Persian."""
        from .api import words
        from .edits import EditsFileError
        from .modelblender import WORK
        if not self._soldiers(address):
            return None
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, new = self._resolve(edits, address)
        ix = self._open()
        try:
            names = self._names(ix, [address] + ([new.source] if new else []), lang,
                                edits.new_units if edits else None)
        finally:
            ix.close()
        from rusemod import squads as sq
        kinds = self._kind_lines(address)
        lines = self._squad_lines(address)
        count = len(lines)
        weapons = self._squad_weapons(address, lang)
        men = self._squad_men(kinds, count, weapons)   # (each soldier's kind and weapons, by the game's rule)
        need = [full for full, _k, needs in weapons if needs]
        w = words(lang)
        own_unit = self._own_model_file(address) is not None
        try:
            models = self._look_models(address)[0]
        except (KeyError, OSError, ValueError):
            models = []
        blender_root = (self._mod_dir() / WORK).resolve() if self._mod_dir() is not None else None
        rows = []
        for ln, (_look, carried) in zip(lines, men):
            own = self._kind_file(address, ln["kind"]) if own_unit else None
            mine = own is not None and own.is_file()
            # the model file he wears: his own look, else his place's kind's model in the mod (the riflemen's, the
            # bazooka man's), else none (the game's)
            worn = own if mine else (self._kind_file(address, ln["base"]) if own_unit else None)
            has = worn is not None and worn.is_file()
            record = _read(worn.with_suffix(".json")) if has else {}
            src = str(record.get("from") or "") if has else ""
            changed = False
            if src and blender_root is not None:
                try:
                    changed = Path(src).resolve().is_relative_to(blender_root)
                except (OSError, ValueError):
                    changed = False
            rows.append({"id": ln["id"], "number": ln["number"], "label": w[f"blender_squad_{ln['word']}"], "count": 1,
                         "fires": list(dict.fromkeys(full for full, _k, _n in carried)),
                         "preview": self._soldier_preview(address, ln, worn if has else None, models),
                         "own_model": has, "wears": "own" if mine else "kind" if has else "game",
                         "from": Path(src).name if src else None, "blender_changed": changed,
                         "kept": str(own) if own is not None else None})
        work = self._squad_work(address)
        state = _read(work / "state.json") if work is not None else {}
        sent = work / "sent" / "sent.json" if work is not None else None
        waiting = bool(sent is not None and sent.is_file() and _sha(sent) != state.get("brought")
                       and _read(sent).get("session") == state.get("session"))
        can_change = own_unit and self._mod_dir() is not None
        is_open = self._squad_open(address, work)
        fewest = sq.fewest(len(need))
        limits = {"add": None, "remove": None}   # (why Add a soldier or Remove can't be, in a plain sentence)
        if can_change and count >= sq.MOST:
            limits["add"] = w["blender_squad_limit_most"].format(n=sq.MOST)
        if can_change and count <= fewest:
            limits["remove"] = w["blender_squad_limit_need"].format(n=len(need), weapons=w["blender_squad_list_sep"].join(
                dict.fromkeys(need))) if len(need) > sq.FEWEST else w["blender_squad_limit_fewest"].format(n=sq.FEWEST)
        return {"name": names.get(address), "copies": names.get(new.source) if new else None, "own": own_unit,
                "count": count, "fewest": fewest, "most": sq.MOST, "line": self._squad_line(men, kinds, lang),
                "soldiers": rows,
                "blender": {"open": is_open, "work": str(work) if work is not None else None,
                            "made": bool(work is not None and work.is_dir()), "found": self._blender() is not None,
                            "waiting": waiting},
                "can": {"blender": can_change and bool(rows), "import": can_change,
                        "reset": can_change and any(r["own_model"] for r in rows),
                        "add": can_change and count < sq.MOST and not is_open,
                        "remove": can_change and count > fewest and not is_open},
                "limits": limits,
                "why_not": None if can_change else w["blender_squad_why_game"]}

    # --- the whole squad in Blender ---
    def _squad_checked(self, address: str, lang: str) -> dict:
        """squad_info, or the refusal: not a squad, a game unit."""
        from .api import StudioError
        info = self.squad_info(address, lang)
        if info is None:
            raise StudioError("This unit isn't a squad of soldiers.")
        if not info["own"]:
            # not a game rule: the Studio gives models only to the units a mod makes (a game unit's stays the game's)
            raise StudioError("This is one of the game's own squads: copy it first, then change the copy.")
        return info

    def _start_file(self, address: str, line: dict, work: Path, state: dict, models: list, lib, name: str,
                    file: Path | None = None) -> tuple:
        """What one soldier starts from in Blender, as a file of his own in <work>/start/<his id>/: (its path, {each
        material's name in it: its alpha picture's path}, where it came from: "kept" his last bring-back from this
        Blender (only while his model in the mod is the one made from it), "model" his own model (one soldier's line
        without a look of his own: the model file of his place's kind he wears, `line`'s "base"; `file`: that file),
        its bones put at their rest poses, "uniform" the game model wearing the squad's Custom uniform and its paint,
        "repainted" the game model with the mod's repaint of the game's picture (files/replace), "game" the game
        model). Its materials and pictures are named after him ("Bazooka man 1"), each material's alpha written
        beside it."""
        from rusemod import gltf
        from rusemod.modelin import glb_document
        from .api import StudioError
        sid = line["id"]
        folder = work / "start" / sid
        target = file if file is not None else self._kind_file(address, line["kind"])
        if file is None and "base" in line and (target is None or not target.is_file()):
            target = self._kind_file(address, line["base"])   # (what he wears: his place's kind's model in the mod)
        taken = (state.get("taken") or {}).get(sid) or {}
        kept = work / "kept" / f"{target.stem}.glb" if target is not None else None
        colour, alpha = {}, {}
        # his last bring-back, only while his model is the one made from it: his model's record names that file, and
        # neither has changed since (an Import model from another file, even of the same bytes, names that file)
        made_from = str(_read(target.with_suffix(".json")).get("from") or "") if target is not None else ""
        try:
            from_kept = bool(made_from) and kept is not None and Path(made_from).resolve() == kept.resolve()
        except (OSError, ValueError):
            from_kept = False
        source = None
        if target is not None and target.is_file() and from_kept and taken \
                and _sha(target) == taken.get("model") and _sha(kept) == taken.get("kept"):
            source, how = kept, "kept"
            raw = kept.read_bytes()
        elif target is not None and target.is_file():
            source, how = target, "model"
            raw = target.read_bytes()
            record = _read(target.with_suffix(".json"))
            if record.get("skeleton") != "own":   # (a model on bones of its own carries its whole skeleton at rest)
                try:
                    doc, _bin = glb_document(raw)
                except (ValueError, struct.error) as exc:
                    raise StudioError(f"{target.name}: {exc}") from None
                like = ((record.get("report") or {}).get("like")
                        or ((doc.get("asset") or {}).get("extras") or {}).get("rusemod_like"))
                skeleton = lib.skeleton(like) if like else None
                placed = gltf.rest_bones_glb(raw, skeleton) if skeleton is not None else None
                raw = placed or raw
        else:
            model = self._figure_model(line, models)
            if model is None:
                raise StudioError("This soldier has no 3D model the Studio can open.")
            raw, pictures, summary = gltf.model_glb(lib, model, rest_bones=True)
            by = {v: k for k, v in (summary.get("picture_of") or {}).items()}   # (texture, kind) -> picture's name
            # the paint he wears in the game now: the Custom uniform's (its own copy's), else a repaint of the game's
            # picture in the mod's files/replace (what every unit drawn with that picture wears)
            paint = {m: p for m, p in self._paint_of(address).items() if any(m == t for t, _k in by)}
            copy = self._own_copy_file(address)
            how = "uniform" if copy is not None and copy.is_file() else "repainted" if paint else "game"
            for member in {m for m, _k in by}:
                mine = paint.get(member) or (None, None)
                colour[member] = mine[0].read_bytes() if mine[0] is not None else None
                alpha[member] = (mine[1].read_bytes() if mine[1] is not None
                                 else pictures.get(by.get((member, "alpha"), ""), None))
        try:
            doc, views = gltf.glb_views(raw)
        except (ValueError, struct.error) as exc:   # (his model file or last bring-back unreadable: said, not skipped)
            raise StudioError(f"{source.name if source is not None else line['id']}: {exc}") from None
        folder.mkdir(parents=True, exist_ok=True)
        alphas = {}
        for k, mat in enumerate(doc.get("materials", [])):
            label = f"{name} {k + 1}"
            extras = mat.get("extras") or {}
            tex = (mat.get("pbrMetallicRoughness") or {}).get("baseColorTexture")
            image = doc["textures"][tex["index"]]["source"] if tex is not None else None
            member = extras.get("rusemod_texture")
            if image is not None and member in colour and colour[member] is not None:
                views[doc["images"][image]["bufferView"]] = colour[member]   # (the Custom uniform's paint on it)
            data = alpha.get(member)
            if data is None and "rusemod_alpha_texture" in extras:   # (his own model's, or his last bring-back's)
                source = doc["textures"][extras["rusemod_alpha_texture"]]["source"]
                data = views[doc["images"][source]["bufferView"]]
            extras.pop("rusemod_alpha_texture", None)
            if extras:
                mat["extras"] = extras
            else:
                mat.pop("extras", None)
            mat["name"] = label
            if image is not None:
                doc["images"][image]["name"] = label
            if data is not None:
                _put(folder / f"{k + 1}_alpha.png", data)
                alphas[label] = str(folder / f"{k + 1}_alpha.png")
        start = folder / f"{sid}.glb"
        _put(start, gltf.pack_glb(doc, views))
        return start, alphas, how

    def squad_blender(self, address: str, lang: str = "us") -> dict:
        """Change the squad in Blender: ONE Blender with every soldier line of the squad side by side, each his own
        (see the module's note). A second click while it's open opens nothing and says so. A sending of the last
        Blender that was never brought back is kept aside (moved to sent-not-brought-<time>/, "set_aside"), and this
        Blender starts from what the mod has. Returns squad_info with "work", "opened": [ids], "started": {id: where
        he started from}, "set_aside", "message"."""
        return self._into_blender(address, lang)

    def soldier_blender(self, address: str, soldier: str, lang: str = "us") -> dict:
        """Change one soldier in Blender: Blender with him alone, as squad_blender opens each soldier (his own
        pictures, where he starts from), brought back the same way (Bring my changes back: squad_blender_back). Refused
        as squad_blender is, and for a soldier the squad hasn't got. Returns squad_blender's answer."""
        self._soldier_kind(address, soldier)   # (not a squad, or no such soldier: refused)
        return self._into_blender(address, lang, only=[str(soldier)])

    def _blender_ready(self, address: str) -> tuple:
        """(Blender's path, the squad's work folder), or the refusal: Blender not found, the squad open in it already."""
        from .api import StudioError
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        work = self._squad_work(address)
        if self._squad_open(address, work):
            raise StudioError("This squad is open in Blender already: change it there, then bring your changes back.")
        return blender, work

    @staticmethod
    def _set_aside(work: Path, state: dict) -> Path | None:
        """A sending of the squad's last Blender that was never brought back, moved to sent-not-brought-<time>/ (kept,
        nothing lost); the folder, or None when there was none."""
        sent = work / "sent"
        if (sent / "sent.json").is_file() and _sha(sent / "sent.json") != state.get("brought"):
            aside = work / time.strftime("sent-not-brought-%Y%m%d-%H%M%S")
            sent.rename(aside)
            return aside
        return None

    def _into_blender(self, address: str, lang: str, only: list | None = None) -> dict:
        """squad_blender's work: every soldier of the squad (`only`: those of these ids) into one Blender, each named
        after his line and his number ("Rifleman 3"), each from his own start file (_start_file)."""
        from rusemod import models as gamemodels
        from .api import words
        info = self._squad_checked(address, lang)
        blender, work = self._blender_ready(address)
        lines = [ln for ln in self._squad_lines(address) if (only is None or ln["id"] in only)
                 and any(r["id"] == ln["id"] for r in info["soldiers"])]
        work.mkdir(parents=True, exist_ok=True)
        state = _read(work / "state.json")
        set_aside = self._set_aside(work, state)
        w = words(lang)
        models = self._look_models(address)[0]
        lib = gamemodels.Library(self._game())
        soldiers, started = [], {}
        try:
            for ln in lines:
                row = next(r for r in info["soldiers"] if r["id"] == ln["id"])
                name = w["blender_squad_numbered"].format(label=row["label"], n=row["number"])
                start, alphas, how = self._start_file(address, ln, work, state, models, lib, name)
                soldiers.append({"id": ln["id"], "name": name, "file": str(start), "alpha": alphas})
                started[ln["id"]] = how
        finally:
            lib.close()
        self._open_blender(address, blender, work, state, soldiers, w)
        message = w["blender_squad_opened"].format(names=w["blender_squad_list_sep"].join(s["name"] for s in soldiers))
        if set_aside is not None:
            message += " " + w["blender_squad_set_aside"].format(folder=str(set_aside))
        return {**self.squad_info(address, lang), "work": str(work), "opened": [s["id"] for s in soldiers],
                "started": started, "set_aside": str(set_aside) if set_aside is not None else None, "message": message}

    def _open_blender(self, address: str, blender: Path, work: Path, state: dict, soldiers: list, w: dict,
                      adding: dict | None = None) -> None:
        """The squad's manifest for Blender (rusemod.blender_model's squad mode: these soldiers, where Blender writes
        what it opened and what it sends, its words; `adding`: the new soldier soldier_add opened, {"id", "at"}), a
        new session in the squad's state, and Blender started on it."""
        from rusemod.blender import open_squad_to_change
        session = uuid.uuid4().hex
        manifest = {"format": 1, "session": session, "unit": self._own_model_file(address).stem, "soldiers": soldiers,
                    "base": str(work / "base"), "sent": str(work / "sent" / "sent.json"),
                    "words": {"send": w["blender_model_send"], "sent": w["blender_squad_sent"],
                              "hint": [w["blender_squad_hint1"], w["blender_squad_hint2"]],
                              "left_out": w["blender_squad_left_out"]}}
        if adding is not None:
            manifest["adding"] = adding
        _write(work / "squad.json", manifest)
        state.update({"format": 1, "session": session, "base": {}})
        _write(work / "state.json", state)
        self._blenders[str(work)] = open_squad_to_change(blender, work / "squad.json")

    @staticmethod
    def _with_alpha(raw: bytes, alphas: dict) -> bytes:
        """A soldier's file from Blender with each material's alpha picture back in it (`alphas`: {material's name: the
        alpha picture's path}, as blender_model lists them), named in the material's extras as rusemod.modelin reads
        it (rusemod_alpha_texture); a material with none, or whose picture isn't there any more, as Blender wrote it."""
        from rusemod import gltf
        try:
            doc, views = gltf.glb_views(raw)
        except (ValueError, struct.error):   # (not a .glb: Import model says so in its own words)
            return raw
        added = False
        for mat in doc.get("materials", []):
            path = alphas.get(mat.get("name"))
            if not path or not Path(path).is_file():
                continue
            view = gltf.add_view(doc, views, Path(path).read_bytes())
            doc.setdefault("images", []).append({"bufferView": view, "mimeType": "image/png",
                                                 "name": f"{mat.get('name')} alpha"})
            doc.setdefault("textures", []).append({"source": len(doc["images"]) - 1})
            mat.setdefault("extras", {})["rusemod_alpha_texture"] = len(doc["textures"]) - 1
            added = True
        return gltf.pack_glb(doc, views) if added else raw

    def squad_blender_back(self, address: str, lang: str = "us") -> dict:
        """Bring my changes back: the open Blender is asked to send (a closed one's last sending is used), and each
        soldier whose file differs from the one Blender wrote of him when the squad opened (or when he was last taken
        in) is taken in with Import model and his kind, his alpha pictures back in it, from <work>/kept/<his model's
        name>.glb (what Resize and Move fit again from); every other soldier's files stay as they were (but see the
        module's note on a Custom uniform). Returns squad_info with "changed", "unchanged", "uniform_kept", "left_out"
        (objects Blender sent with nobody), "reports" (each taken-in soldier's Import model report), "work" and
        "message"."""
        from rusemod.blender import ask_to_send
        from .api import StudioError, words
        info = self._squad_checked(address, lang)
        work = self._squad_work(address)
        manifest = _read(work / "squad.json")
        sent = Path(manifest["sent"]) if manifest.get("sent") else work / "sent" / "sent.json"
        proc = self._blenders.get(str(work))
        if proc is not None and proc.poll() is None:   # its Blender is open: it sends what it has now
            if ask_to_send(sent, SEND_WAIT) is None:
                # not a game rule: the Studio's own hand-over from Blender
                raise StudioError("Blender didn't answer in time: in Blender, click Send to the R.U.S.E. Studio at the "
                                  "top, then bring your changes back again.")
        listing = _read(sent)
        if not manifest or not listing or listing.get("session") != manifest.get("session"):
            # not a game rule: the Studio's own hand-over from Blender, nothing sent from this Blender yet
            raise StudioError("Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at "
                              "the top, then Bring my changes back here.")
        ids = [s["id"] for s in manifest["soldiers"]]
        label = {s["id"]: s.get("name") or s["id"] for s in manifest["soldiers"]}   # (as Blender named each: "Rifleman 3")
        got = listing.get("soldiers") or {}
        missing = [i for i in ids if not (got.get(i) or {}).get("file") or not Path(got[i]["file"]).is_file()]
        if missing:
            # not a game rule: Blender wrote no file for him (every part of him deleted there)
            raise StudioError(f"Blender sent nothing for {', '.join(label.get(i, i) for i in missing)}: in Blender, "
                              f"undo what was deleted (Ctrl+Z), click Send to the R.U.S.E. Studio, then bring your "
                              f"changes back.")
        if manifest.get("adding"):   # (Add a soldier's Blender: the new soldier joins the squad now)
            return self._join(address, lang, work, manifest, listing, sent)
        state = _read(work / "state.json")
        base = dict(state.get("base") or {}) if state.get("session") == manifest.get("session") else {}
        opened = _read(work / "base" / "base.json")
        if opened.get("session") == manifest.get("session"):
            for i, b in (opened.get("soldiers") or {}).items():
                base.setdefault(i, (b or {}).get("sha256"))
        now = {i: _sha(Path(got[i]["file"])) for i in ids}
        changed = [i for i in ids if now[i] != base.get(i)]
        uniform_kept = []
        copy = self._own_copy_file(address)
        if changed and copy is not None and copy.is_file():
            uniform_kept = [i for i in ids if i not in changed
                            and not next(r["own_model"] for r in info["soldiers"] if r["id"] == i)]
        take = [i for i in ids if i in changed or i in uniform_kept]
        lines = {ln["id"]: ln for ln in self._squad_lines(address)}
        reports = {}
        state.setdefault("taken", {})
        for i in take:
            target = self._kind_file(address, lines[i]["kind"])
            kept = work / "kept" / f"{target.stem}.glb"
            _put(kept, self._with_alpha(Path(got[i]["file"]).read_bytes(), got[i].get("alpha") or {}))
            record = _read(target.with_suffix(".json")) if target.is_file() else {}
            if not record and "base" in lines[i]:   # (his first own look: the size of the model he wore, if any)
                worn = self._kind_file(address, lines[i]["base"])
                record = _read(worn.with_suffix(".json")) if worn is not None and worn.is_file() else {}
            size = record.get("size") if isinstance(record.get("size"), (int, float)) else 1.0
            kind = lines[i]["kind"]
            res = self.model_import(address, str(kept), size, kind=kind) if kind else \
                self.model_import(address, str(kept), size)
            reports[i] = res.get("model")
            state["taken"][i] = {"kept": _sha(kept), "model": _sha(target)}
            base[i] = now[i]
            state.update({"session": manifest.get("session"), "base": base})
            _write(work / "state.json", state)
        state.update({"session": manifest.get("session"), "base": base, "brought": _sha(sent)})
        _write(work / "state.json", state)
        w = words(lang)
        sep = w["blender_squad_list_sep"]
        unchanged = [i for i in ids if i not in changed]
        left = list(listing.get("left_out") or [])
        if not changed:
            message = w["blender_squad_back_none"]
        else:
            message = w["blender_squad_back_changed"].format(names=sep.join(label.get(i, i) for i in changed))
            if unchanged:
                message += " " + w["blender_squad_back_unchanged"].format(
                    names=sep.join(label.get(i, i) for i in unchanged))
            if uniform_kept:
                message += " " + w["blender_squad_uniform_kept"].format(
                    names=sep.join(label.get(i, i) for i in uniform_kept))
        if left:
            message += " " + w["blender_squad_left_out_back"].format(names=", ".join(left))
        return {**self.squad_info(address, lang), "changed": changed, "unchanged": unchanged,
                "uniform_kept": uniform_kept, "left_out": left, "reports": reports, "work": str(work),
                "message": message}

    # --- one soldier at a time ---
    def _soldier_kind(self, address: str, soldier: str) -> str | None:
        """The kind Import model takes for one of the squad's soldier lines (None: the riflemen, the unit's own
        model); refused for a unit that isn't a squad, or a soldier the squad hasn't got."""
        from .api import StudioError
        if not self._soldiers(address):
            raise StudioError("This unit isn't a squad of soldiers.")
        line = next((ln for ln in self._squad_lines(address) if ln["id"] == soldier), None)
        if line is None:
            raise StudioError(f"This squad has no soldier called {soldier}.")
        return line["kind"]

    def soldier_import(self, address: str, soldier: str, file: str | None = None, size: float = 1.0) -> dict:
        """Import a model for one soldier from a file (asked for when not given): model_import with his kind (the
        riflemen: none), its answer as it is."""
        kind = self._soldier_kind(address, soldier)
        return self.model_import(address, file, size, kind=kind) if kind else self.model_import(address, file, size)

    def soldier_reset(self, address: str, soldier: str) -> dict:
        """Back to the game's look for one soldier: model_import_remove with his kind (the riflemen: none, which takes
        the other kinds on bones of their own with them, "kinds_out"), its answer as it is. A soldier with a look of
        his own (one line per soldier: rusemod.squads) loses his own; one wearing his place's kind's model in the mod
        (a squad's riflemen's or bazooka man's, from before each soldier had his own) that one, as before."""
        kind = self._soldier_kind(address, soldier)
        line = next((ln for ln in self._squad_lines(address) if ln["id"] == soldier), None)
        if line is not None and kind is not None:
            own = self._kind_file(address, kind)
            if own is None or not own.is_file():
                kind = line["base"]   # (none: the riflemen's, the unit's own model)
        return self.model_import_remove(address, kind=kind) if kind else self.model_import_remove(address)

    # --- a soldier more or less (the squad work's Phases 2-3: rusemod.squads) ---
    def _page_lang(self) -> str:
        """The Studio's language, for a call the page makes without one."""
        from rusemod import schema
        return self.prefs().get("lang") or schema.BASE

    def _need_names(self, address: str, lang: str) -> list:
        """The squad's weapons its last soldiers fire one each (their ammunition has NeedModelChange), named as the
        weapon list names them."""
        return [full for full, _k, needs in self._squad_weapons(address, lang) if needs]

    def _write_count(self, address: str, n: int) -> None:
        """The squad's own number of soldiers into the mod (none kept when it's the game's setting again)."""
        from rusemod import squads as sq
        own = self._own_model_file(address)
        sq.write_count(self._mod_dir(), own.stem, None if n == self._shared_count() else n)

    def _renumber(self, address: str, work: Path, state: dict, start: int, step: int) -> None:
        """The soldiers from number `start` on take the next number (`step` 1) or the one before (-1): their own looks'
        files and records (files/models/<unit>@<i>.glb, .json), their last bring-backs (<work>/kept/) and the squad's
        Blender state of them; never over a file not yet moved."""
        from rusemod import squads as sq
        main = self._own_model_file(address)
        places = [main.parent, work / "kept"]
        have = sorted({s[1] for folder in places if folder.is_dir() for f in folder.glob(f"{main.stem}@*.glb")
                       if (s := sq.soldier_of(f.stem)) is not None and s[0] == main.stem and s[1] >= start})
        for i in (reversed(have) if step > 0 else have):
            j = i + step
            for folder in places:
                for suffix in (".glb", ".json"):
                    src = folder / f"{main.stem}@{i}{suffix}"
                    if src.is_file():
                        os.replace(src, folder / f"{main.stem}@{j}{suffix}")
            record = main.parent / f"{main.stem}@{j}.json"
            data = _read(record)
            if data.get("for") == str(i):
                data["for"] = str(j)
                _write(record, data)
        taken = state.get("taken") or {}
        state["taken"] = {(str(int(k) + step) if k.isdigit() and int(k) >= start else k): v for k, v in taken.items()}
        state["base"] = {}

    def soldier_add(self, address: str, source: str, of: str | None = None, unit: str | None = None,
                    file: str | None = None) -> dict | None:
        """Add a soldier (the owner, 2026-11-11: "copy an existing unit or import a model, and then that takes you to
        Blender. And when you bring it back, that unit can be then added to that squad"): Blender opens with just the
        new soldier, starting as `source` gives him: "copy" one of this squad's soldiers (`of`, his number) as he looks
        now, "unit" a soldier of another squad (`unit`, `of`: his number there) as he looks there, "file" a model file
        (asked for when not given; None back when the picker is closed) fitted to the soldier's bones. He joins the
        squad when he's brought back (squad_blender_back), before its last soldiers who fire its NeedModelChange
        weapons (rusemod.squads.join_place); the squad's health and weapons stay as they are (the owner's pick 4).
        Refused, in words: not a squad of this mod's own, a squad of 8 already, Blender not found or this squad open in
        it, no such way or soldier. Returns squad_info with "work", "opened": ["new"], "adding": {"at": the number he
        will have, "started": where he starts from (_start_file's)}, "set_aside"."""
        from rusemod import models as gamemodels, squads as sq
        from .api import StudioError, pick_file, words
        lang = self._page_lang()
        info = self._squad_checked(address, lang)
        if source not in ("copy", "unit", "file"):
            # not a game rule: the Studio's three ways to add a soldier
            raise StudioError(f"{source} isn't a way to add a soldier: a copy of one in this squad, a soldier from "
                              f"another unit, or a model file.")
        n = info["count"]
        if n >= sq.MOST:
            # not a game rule: the owner's pick 2 (2026-11-12), "Most soldiers for now: 8"
            raise StudioError(f"A squad has at most {sq.MOST} soldiers for now.")
        line = None
        from_address = address
        if source == "copy":
            line = next((ln for ln in self._squad_lines(address) if ln["id"] == str(of)), None)
            if line is None:
                raise StudioError(f"This squad has no soldier called {of}.")
        elif source == "unit":
            if not unit or unit == address or not self._soldiers(unit):
                raise StudioError("The unit to take a soldier from isn't a squad of soldiers.")
            from_address = unit
            line = next((ln for ln in self._squad_lines(unit) if ln["id"] == str(of)), None)
            if line is None:
                raise StudioError(f"That squad has no soldier called {of}.")
        elif file is None:
            if self._window is None:
                return None
            file = pick_file(self._window, ("3D model (*.3ds;*.glb)",))
            if not file:
                return None
        blender, work = self._blender_ready(address)
        figs = {p: m for p, m in self._soldier_figures(address) if m}
        at = sq.join_place(n, len(self._need_names(address, lang)), bool(figs.get(sq.LAST)))
        work.mkdir(parents=True, exist_ok=True)
        state = _read(work / "state.json")
        set_aside = self._set_aside(work, state)
        w = words(lang)
        name = w["blender_squad_new"]
        lib = gamemodels.Library(self._game())
        try:
            if source == "file":
                # fitted to the soldier's bones as the model of the place he'll stand at (before the last soldiers who
                # fire its NeedModelChange weapons, or at the end of a squad all of one figure: a riflemen's place,
                # soldier 1's), into the squad's Blender folder; the mod's own files are left as they are until he joins
                fitted = work / "new" / f"{Path(file).stem}.glb"
                fitted.parent.mkdir(parents=True, exist_ok=True)
                self._fit_model(address, file, 1.0, False, None, True, True, None, kind="1", out=fitted)
                start, alphas, how = self._start_file(address, {"id": "new"}, work, {}, [], lib, name, file=fitted)
            else:
                models = self._look_models(from_address)[0]
                start, alphas, how = self._start_file(from_address, {**line, "id": "new"}, work, {}, models, lib,
                                                      name)
        finally:
            lib.close()
        self._open_blender(address, blender, work, state, [{"id": "new", "name": name, "file": str(start),
                                                            "alpha": alphas}], w,
                           adding={"id": "new", "at": at, "source": source})
        return {**self.squad_info(address, lang), "work": str(work), "opened": ["new"],
                "adding": {"at": at, "started": how}, "set_aside": str(set_aside) if set_aside is not None else None}

    def _join(self, address: str, lang: str, work: Path, manifest: dict, listing: dict, sent: Path) -> dict:
        """squad_blender_back for Add a soldier's Blender: the new soldier joins the squad at the number soldier_add
        gave him (the ones from there on one number on), the squad one soldier more, his look his own (Import model with
        his number, from what Blender sent: <work>/kept/<unit>@<i>.glb). An Import model that fails leaves the squad as
        it was. Returns squad_blender_back's answer with "joined": his number and "count"."""
        from rusemod import squads as sq
        from .api import StudioError, words
        adding = manifest["adding"]
        new = (listing.get("soldiers") or {}).get(adding["id"]) or {}
        n = self._squad_count(address)
        if n >= sq.MOST:
            raise StudioError(f"A squad has at most {sq.MOST} soldiers for now.")
        at = max(1, min(int(adding.get("at") or n + 1), n + 1))
        state = _read(work / "state.json")
        main = self._own_model_file(address)
        main_record = _read(main.with_suffix(".json")) if main.is_file() else {}
        size = main_record.get("size") if isinstance(main_record.get("size"), (int, float)) else 1.0
        self._renumber(address, work, state, at, +1)
        self._write_count(address, n + 1)
        target = self._kind_file(address, str(at))
        kept = work / "kept" / f"{target.stem}.glb"
        _put(kept, self._with_alpha(Path(new["file"]).read_bytes(), new.get("alpha") or {}))
        try:
            res = self.model_import(address, str(kept), size, kind=str(at))
        except BaseException:
            # (the squad as it was: his sending stays in Blender's folder, to bring back again)
            kept.unlink(missing_ok=True)
            for f in (target, target.with_suffix(".json")):
                f.unlink(missing_ok=True)
            self._write_count(address, n)
            self._renumber(address, work, state, at + 1, -1)
            _write(work / "state.json", state)
            raise
        state.setdefault("taken", {})[str(at)] = {"kept": _sha(kept), "model": _sha(target)}
        state.update({"session": manifest.get("session"), "base": {}, "brought": _sha(sent)})
        _write(work / "state.json", state)
        w = words(lang)
        left = list(listing.get("left_out") or [])
        message = w["blender_squad_joined"].format(n=at, count=n + 1)
        if left:
            message += " " + w["blender_squad_left_out_back"].format(names=", ".join(left))
        return {**self.squad_info(address, lang), "changed": [str(at)], "unchanged": [], "uniform_kept": [],
                "left_out": left, "reports": {str(at): res.get("model")}, "joined": str(at), "work": str(work),
                "message": message}

    def soldier_remove(self, address: str, soldier: str) -> dict:
        """Take a soldier out of the squad (`soldier`: his number): the squad one soldier fewer, the soldiers after him
        one number down, his own look kept aside in the squad's Blender folder (<work>/removed-<time>-soldier<i>/:
        nothing lost, not packed). Refused, in words: fewer than 2 soldiers (the game's own rule, the owner's pick 1),
        fewer than the weapons its last soldiers fire one each, the squad open in Blender, no such soldier. A sending
        from Blender never brought back is kept aside first (its soldiers' numbers are the old ones). Returns
        squad_info with "removed", "set_aside", "kept_aside"."""
        from rusemod import squads as sq
        from .api import StudioError
        lang = self._page_lang()
        info = self._squad_checked(address, lang)
        if not any(r["id"] == str(soldier) for r in info["soldiers"]):
            raise StudioError(f"This squad has no soldier called {soldier}.")
        n = info["count"]
        need = self._need_names(address, lang)
        if n - 1 < sq.FEWEST:
            # the game's own rule (its setting makes any number below 2 a 2) and the owner's pick 1
            raise StudioError(f"A squad keeps at least {sq.FEWEST} soldiers: the game's own rule.")
        if n - 1 < len(need):
            # the game's rule: each of these weapons goes to one soldier, from the last one back
            raise StudioError(f"This squad keeps at least {len(need)} soldiers: its last {len(need)} fire "
                              f"{', '.join(dict.fromkeys(need))}, one each.")
        work = self._squad_work(address)
        if self._squad_open(address, work):
            raise StudioError("This squad is open in Blender already: change it there, then bring your changes back.")
        i = int(soldier)
        work.mkdir(parents=True, exist_ok=True)
        state = _read(work / "state.json")
        set_aside = self._set_aside(work, state)
        main = self._own_model_file(address)
        aside = work / time.strftime(f"removed-%Y%m%d-%H%M%S-soldier{i}")
        for f in (main.with_name(f"{main.stem}@{i}.glb"), main.with_name(f"{main.stem}@{i}.json"),
                  work / "kept" / f"{main.stem}@{i}.glb"):
            if f.is_file():
                aside.mkdir(parents=True, exist_ok=True)
                os.replace(f, aside / f.name)
        (state.get("taken") or {}).pop(str(i), None)
        self._renumber(address, work, state, i + 1, -1)
        self._write_count(address, n - 1)
        _write(work / "state.json", state)
        return {**self.squad_info(address, lang), "removed": str(i),
                "set_aside": str(set_aside) if set_aside is not None else None,
                "kept_aside": str(aside) if aside.is_dir() else None}
