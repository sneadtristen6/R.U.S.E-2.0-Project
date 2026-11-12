"""The Horse Squad in the Units tab (StudioApi's HorseSquadCalls): riflemen and a heavy-weapon soldier on horses of their
own, a unit anyone can add to a mod like the era units, credited to its maker.

The owner, 2026-11-10: "the cavalry unit we made should become a new unit just in the studio that's accredited to me";
2026-11-12, asked whether the Studio should build it on each player's PC from their own game, as a unit anyone can add
like the era units, credited to sneadtristen6: "Yes, like era units" (the option: "Off until a modder adds it; built from
their own game when added; your name, sneadtristen6, in that mod's credits"). His rule for era units (2026-10-08,
era_units.py): every one is OFF until a modder adds it.

Its models are made from the game's own horse and rifleman, which can't go in a download: nothing of it is downloaded.
It's listed with the era units, in WWII+, whether that era is downloaded or not (era_units_list's "built" rows). When a
modder adds it (horse_squad_add, a job the page follows), the Studio first makes its two model files from the player's
own game with the builder (rusemod.horsesquad.horse_squad_glbs: the riflemen's horse and rider, and the heavy-weapon
soldier's), into the platform folder's horse_squad/ (the mod's model records name them: Resize and Move fit them again
from there); then it makes the unit the way the copy that passed in the game did (horse-studio2, 2026-11-11, his words
"test works  bazooka there": scratch/animmodels/horse-studio/make_horse_studio2_test.py): a new unit from the US rifle
squad, Import model of the riflemen's file, Import model of the heavy-weapon soldier's for his kind ("bazooka"), both on
the same bones of their own. Its name, price, build menu, group and research are the era units' add form's
(era_units._era_plan and _era_make, shared); its credit line goes in the mod's CREDITS-era-units.md beside the era
units' (era_units.credits_text), and Take it out of my mod takes the unit, both models, their animations and the line
out again (era_unit_remove). The game can't give what the builder needs, or the builder isn't in this Studio: refused
in words, nothing made. Anything that fails once the unit is made takes it out again, so nothing is left half made."""
from __future__ import annotations

import importlib
import os
import shutil
import threading
import uuid
from pathlib import Path

KEY = "horse-squad"     # its key among the era units (the mod's era_units.json): never one of a library's (era|nation|name)
NAME = "Horse Squad"    # its name in English: the new unit's when the form gives none, and the credits'
AUTHOR = "sneadtristen6"   # the name on his mods
SQUAD = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"   # the US rifle squad it's made from, as horse-studio2 was
BUILDER = "rusemod.horsesquad"   # its two model files from the player's own game (horse_squad_glbs, HorseSquadError)
FOLDER = "horse_squad"  # in the platform folder: the two files the builder made last, which the mod's records name
ROLES = ("rifle", "bazooka")    # the builder's answer: the riflemen's file, the heavy-weapon soldier's
HEAVY = "bazooka"       # Import model's kind for the heavy-weapon soldier (StudioApi._soldier_kinds)
STEPS = ("build", "unit", "riflemen", "bazooka")   # the job's lines, in order: what the page says it's doing
# what the Units tab lists (era_units: the library entry's fields); the game's index adds its build menu and its type
ENTRY = {"key": KEY, "era": "WWII", "nation": "USA", "name": NAME, "in_place_of": "", "copies": SQUAD,
         "aircraft": False, "model": None, "fits": True, "picture": None, "card_picture": None,
         "class": "TInfanterieDescriptor", "built": True, "credit": {"author": AUTHOR}}
BUILT = {KEY: ENTRY}    # the units made for RUSE 2.0, by key (era_units: their credits, never a library's)
_LOCK = threading.Lock()


class HorseSquadCalls:
    """Mixed into StudioApi: uses EraUnitCalls' (_era_plan, _era_make, _era_options, _era_record, era_unit_remove),
    its _open, _all_units, _names, _game, _path, _home, _jobs, _mod_dir, _new_units, model_import,
    model_import_remove, delete_unit and _kind_rows."""

    # --- what the Units tab lists ---
    def _horse_entry(self) -> dict | None:
        """The Horse Squad as the Units tab lists it: ENTRY, with what the game's index says of the US rifle squad
        it's made from: its build menu ("game_nation", "factory": the add form's first pick) and its type in English
        ("card": the kind of unit its group goes by, as an era unit's library card); "names": its name in each of
        the Studio's languages (words.toml eras_horse_name, for the search box). None when the game has no US rifle
        squad: it can't be made then."""
        from .api import _words
        ix = self._open()
        try:
            row = next((u for u in self._all_units(ix) if u["address"] == SQUAD), None)
            if row is None:
                return None
            key = row.get("type_key")
            card = ((ix.names([key], "us").get(key) or "") if key else "").strip()
        finally:
            ix.close()
        names = sorted({t for t in _words().get("eras_horse_name", {}).values() if isinstance(t, str) and t.strip()})
        return dict(ENTRY, game_nation=row["nation"], factory=row["factory"], card=card, names=names)

    def _era_built(self) -> list[dict]:
        """The units made for RUSE 2.0 the game can make (era_units_list's "built" rows): none while the game's index
        can't be read."""
        import sqlite3
        try:
            entry = self._horse_entry()
        except (OSError, KeyError, sqlite3.Error):
            return []
        return [entry] if entry is not None else []

    def _era_built_entry(self, key: str) -> dict | None:
        """The unit made for RUSE 2.0 called `key` (_horse_entry), or None when `key` isn't one (a library's era
        unit); a StudioError when the game can't make it."""
        from .api import StudioError
        if key not in BUILT:
            return None
        entry = self._horse_entry()
        if entry is None:
            # not a game rule: the Horse Squad is made from this unit of the game's
            raise StudioError(f"{SQUAD} isn't in this game build")
        return entry

    def _horse_page(self, entry: dict, lang: str = "base") -> dict:
        """era_unit_page for the Horse Squad: its entry, "added" (its unit's address in this mod, or None), "start":
        the US rifle squad alone (by its game name: its models are made for that unit's soldiers), "has_model" False
        (no library model: its models are made when it's added), "building": the job adding it while one runs (the
        page follows it), and era_unit_start's "price", "size", "size_info", "research" and "group" for its own
        build menu."""
        from rusemod import schema
        record = self._era_record() if self._mod_dir() is not None else {}
        ix = self._open()
        try:
            name = self._names(ix, [SQUAD], lang if lang in schema.LANGS else "us").get(SQUAD) or SQUAD.rsplit("/", 1)[-1]
        finally:
            ix.close()
        start = [{"address": SQUAD, "name": name, "nation": entry["game_nation"], "suggested": True,
                  "same_type": True}]
        options = self._era_options(None, {}, entry, SQUAD, entry["game_nation"], entry["factory"], lang)
        return dict(entry, added=record.get(KEY), picture=None, start=start, has_model=False,
                    building=self._horse_running(), **options)

    def _horse_running(self) -> str | None:
        """The job adding the Horse Squad while it runs, else None."""
        job = self.__dict__.get("_horse_job")
        return job if job and job in self._jobs and self._jobs[job].state == "running" else None

    # --- adding it ---
    def horse_squad_add(self, nation: int, factory: int, name: str | None = None, price=None, research_from=None,
                        research_price=None, research_time=None, group=None) -> dict:
        """Add the Horse Squad to the current mod, as era_unit_add adds an era unit (its name, `price`, nation
        `nation`'s build menu `factory`, the unit it's `research_from` with `research_price` and `research_time`, its
        `group`: the add form's, era_units._era_plan; it always starts from the US rifle squad), its models made first
        from the player's own game: a job the page follows (Job lines STEPS, in turn: "build" its two files with the
        builder, "unit" the unit made, "riflemen" and "bazooka" each one's model imported). Done, its "result" is
        {"address", "name"}; failed, its message says why in words and nothing is left made. What's asked is checked
        before anything starts (refused at once, as era_unit_add refuses it); a second ask while one runs follows it.
        Returns {"job": id}."""
        from rusemod.webui import Job
        from .api import StudioError
        entry = self._era_built_entry(KEY)
        mod = self._mod_dir()
        # everything asked for, checked before the long part (era_unit_add's checks: the mod, already in it, the
        # research, the group's room, the research price and time; and the name's address free)
        self._era_plan(KEY, None, {}, entry, nation, factory, SQUAD, None, research_from, research_price,
                       research_time, group)
        self._horse_name_free(name)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E.: the Horse Squad is made from your own copy of the game.")
        builder = self._horse_builder()
        with _LOCK:
            running = self._horse_running()
            if running:
                return {"job": running}
            job = Job()
            job.result = None
            self._jobs[job.id] = job
            self.__dict__["_horse_job"] = job.id
            self.__dict__["_horse_mod"] = None   # the mod being written while its unit is made (_horse_guard)

        def work(say):
            say(STEPS[0])
            files = self._horse_build(builder, game)
            self.__dict__["_horse_mod"] = mod      # from here its mod stays the one edited (_horse_guard)
            try:
                # the mod it was asked for, still the one being edited: nothing is made in another
                if self._mod_dir() != mod:
                    raise StudioError("The mod being edited changed while the Horse Squad was being made, so it "
                                      "wasn't added: add it again.")
                say(STEPS[1])
                made, before = None, set(self._new_units())
                try:
                    plan = self._era_plan(KEY, None, {}, entry, nation, factory, SQUAD, None, research_from,
                                          research_price, research_time, group)
                    made = self._era_make(KEY, self._era_library()[1], entry, plan, nation, factory, name, price)
                    say(STEPS[2])
                    self.model_import(made["address"], str(files["rifle"]))
                    say(STEPS[3])
                    self.model_import(made["address"], str(files["bazooka"]), kind=HEAVY)
                    self._horse_check(made["address"])
                except BaseException:
                    self._horse_undo(made["address"] if made else None, before)
                    raise
            finally:
                self.__dict__["_horse_mod"] = None
            job.result = {"address": made["address"], "name": made["name"]}

        return job.start(work, f"{NAME} is in your mod.", plain=(StudioError, OSError))

    def _horse_name_free(self, name) -> None:
        """A name given whose address is taken (a unit of the game's, or one the mod made), refused before the long
        part, in _unit_new's words (it names a copy of the US rifle squad so); no name given: _era_make's own way."""
        from .api import _PREFIX, StudioError, safe_name
        wanted = (name or "").strip()
        stem = safe_name(wanted) if wanted else ""
        if not stem:
            return    # (none given, or no letters A-Z: _unit_new finds it a free address)
        namespace, tail = SQUAD.rsplit("/", 1)
        m = _PREFIX.match(tail)
        prefix = m.group(1) if m else "Descriptor_Unit_"
        target = f"{namespace}/{prefix}{stem}"
        edits = self._edits()
        taken = edits is not None and target in edits.new_units
        if not taken:
            ix = self._open()
            try:
                ix.show(target)
                taken = True
            except KeyError:
                pass
            finally:
                ix.close()
        if taken:
            raise StudioError(f"There's already a unit called {prefix}{stem} (from {wanted!r}). Pick another name.")

    def _horse_builder(self):
        """The builder (BUILDER), or a StudioError when this Studio hasn't got it."""
        from .api import StudioError
        try:
            return importlib.import_module(BUILDER)
        except ImportError:
            # not a game rule: the part of the Studio that makes it
            raise StudioError("This Studio can't make the Horse Squad yet: the part that makes it from your game "
                              "isn't in it.") from None

    def _horse_build(self, builder, game: Path) -> dict:
        """The Horse Squad's two model files made from the player's own game (`game`) by `builder`: into a folder of
        their own first, then into the platform folder's horse_squad/ under the names the builder gave them (the files
        made before are replaced: the mod's model records name them, for Resize and Move). Returns {"rifle",
        "bazooka": its path there}. The builder's own refusal is said in its words (HorseSquadError); files it didn't
        make where it was asked to, refused."""
        from .api import StudioError
        refusal = getattr(builder, "HorseSquadError", None)
        refusals = (refusal,) if isinstance(refusal, type) and issubclass(refusal, Exception) else ()
        root = self._home / FOLDER
        work = root / f".making-{uuid.uuid4().hex[:8]}"
        work.mkdir(parents=True)
        try:
            try:
                got = builder.horse_squad_glbs(Path(game), work, index=self._path(), say=lambda _line: None)
            except refusals as exc:
                raise StudioError(f"The Horse Squad can't be made from your game: {exc}") from None
            files = {}
            for role in ROLES:
                path = Path(got[role]) if isinstance(got, dict) and got.get(role) else None
                if path is None or not path.is_file() or path.suffix.lower() != ".glb" \
                        or path.resolve().parent != work.resolve():
                    files = None
                    break
                files[role] = path
            if not files or len({p.name.lower() for p in files.values()}) != len(ROLES):
                raise StudioError("The Horse Squad can't be made from your game: its two model files didn't come out. "
                                  "Please report this.")
            out = {}
            for role, path in files.items():
                out[role] = root / path.name
                os.replace(path, out[role])
            return out
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _horse_check(self, address: str) -> None:
        """Both its soldiers' models in, on the same bones of their own (so the heavy-weapon soldier plays the
        riflemen's animations), as on the copy that passed in the game (make_horse_studio2_test.py stopped on
        anything else); a StudioError when they aren't."""
        from .api import StudioError
        rows = {r["kind"]: r for r in self._kind_rows(address)}
        main = next(iter(rows.values()), {})
        heavy = rows.get(HEAVY, {})
        if not (main.get("own") and main.get("skeleton") == "own" and heavy.get("own")
                and heavy.get("same_bones") is True):
            raise StudioError("The Horse Squad's two models didn't come in on the same bones, so it wasn't added. "
                              "Please report this.")

    def _horse_undo(self, address: str | None, before: set) -> None:
        """A Horse Squad this job couldn't finish, taken out again, and only what this job made: its unit (`address`;
        else a copy of the US rifle squad that wasn't among the mod's new units `before` it began), with its models and
        its credit line (era_unit_remove, when the mod's era_units.json names it), never a Horse Squad the mod had
        already."""
        from .api import StudioError
        self.__dict__["_horse_undoing"] = True   # (era_unit_remove refuses the page while the add runs, not this)
        try:
            units = self._new_units()
            mine = ({address} if address else set()) | {a for a, u in units.items()
                                                         if a not in before and u.source == SQUAD}
            recorded = self._era_record().get(KEY)
            if recorded in mine:
                self.era_unit_remove(KEY, "anyway")
                mine.discard(recorded)
            for left in sorted(mine):
                if left not in self._new_units():
                    continue
                try:
                    self.model_import_remove(left)
                except (StudioError, OSError):
                    pass
                self.delete_unit(left, "anyway")
        except (StudioError, OSError):
            pass   # (the job's own failure is what the page says)
        finally:
            self.__dict__["_horse_undoing"] = False

    def _horse_guard(self, path, switching: bool = False) -> None:
        """While the Horse Squad's unit is being made in a mod (its models imported, after its files are made), that
        mod stays the one edited, as the job writes into the mod being edited: `switching` to another mod (choose_mod),
        or deleting or forgetting that one (`path`), is refused until it's done."""
        from .api import StudioError
        busy = self.__dict__.get("_horse_mod")
        if busy is None:
            return
        same = path is not None and os.path.normcase(os.path.abspath(str(path))) == \
            os.path.normcase(os.path.abspath(str(busy)))
        if same != switching:
            raise StudioError("The Horse Squad is being added to this mod: wait for it to finish.")
