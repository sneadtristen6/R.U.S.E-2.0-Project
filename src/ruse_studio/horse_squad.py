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
in words, nothing made. Anything that fails once the unit is made takes it out again, so nothing is left half made.

Its country (the owner, 2026-11-13: "generic horse should be fully editable so people can change what countmry its
from add saddle etc"): the add form's Start from offers each country's rifle squad the builder makes riders from
(SQUADS: the US one, as before, then Germany's, the UK's, France's); the unit starts from that squad's values, its
riders are that squad's rifleman and heavy-weapon soldier, its two files that country's in the platform folder's
horse_squad/ (made once per PC, as before: his "once per pc"), and its credit line names that country (built_entry).
Its look is changed like any unit's own model: Change it in Blender opens its own horse and riders (modelblender)."""
from __future__ import annotations

import importlib
import os
import shutil
import threading
import uuid
from pathlib import Path

KEY = "horse-squad"     # its key among the era units (the mod's era_units.json): never one of a library's (era|nation|name)
NAME = "Generic Horse"    # its name in English: the new unit's when the form gives none, and the credits'
AUTHOR = "sneadtristen6"   # the name on his mods
SQUAD = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"   # the US rifle squad it's made from, as horse-studio2 was
# the country it is from (the owner, 2026-11-13: "generic horse should be fully editable so people can change what
# countmry its from add saddle etc"): the rifle squad picked in its add form's Start from, whose soldiers its riders
# are made from and whose values it starts with (the US one unless another is picked, as before), each by the country
# its credit line names. The builder's own list (rusemod.horsesquad.SQUADS, each squad read from the game first:
# rifleman and heavy-weapon soldier two models on the US rifleman's bones, every clip the riders play there); Italy's
# and the USSR's rifle squads have one look for both soldiers, so they aren't here (a question for the owner)
SQUADS = {SQUAD: "USA", "$/GFX/Everything/Descriptor_Unit_Soldat_Allemand_Leger": "Germany",
          "$/GFX/Everything/Descriptor_Unit_Soldat_UK_Leger": "UK",
          "$/GFX/Everything/Descriptor_Unit_Soldat_FR_Leger": "France"}
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
# Windows' longest path (260 with the character that ends it; a folder: 248) while its long paths aren't on for this
# program: a platform folder of 140 characters stopped the Add (2026-11-12, the real builder: 139 added, 140 not, the
# words "...isn't there"), so the Add works out the longest path it is going to write and says so first (_horse_room)
PATH_MOST = 259
WORK = ".m"             # the Add's own folder in horse_squad/ while the builder works: this and 8 letters (short, so a
#                         deep platform folder has the most room; the files it ends with keep the builder's names)
CLIP_LONGEST = 24       # the longest name of the Horse Squad's animations (hr_t_mort_balle_violente,
#                         hr_t_bazooka_transition1: the passed copy's files), written as <name>.part, then <name>.baf
OWN_CLIPS = ("files", "anim", "own")   # where Import model puts a unit's own animations: <mod>/files/anim/own/<unit>/


def built_entry(mod: Path, key: str, address: str) -> dict:
    """The unit made for RUSE 2.0 called `key` (BUILT) as the mod at `mod` has it at `address`: its entry, its country
    the one of the rifle squad it was made from (SQUADS: its credit line names it, "Generic Horse (WWII, Germany)");
    the entry's own (USA) when the mod's unit can't be read or wasn't made from one of them."""
    from .edits import EditsFileError, ModEdits
    entry = BUILT[key]
    if key != KEY:
        return entry
    try:
        unit = ModEdits(mod).new_units.get(address)
    except (OSError, ValueError, EditsFileError):   # (the mod's units can't be read: its entry's own, as before)
        return entry
    country = SQUADS.get(getattr(unit, "source", None)) if unit is not None else None
    return dict(entry, nation=country) if country else entry


def long_paths_on() -> bool:
    """Whether this program may write a path longer than PATH_MOST: not Windows, or Windows with its long paths
    turned on and this program taking them (ntdll's RtlAreLongPathsEnabled says both); False when it can't tell."""
    import sys
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        enabled = ctypes.WinDLL("ntdll").RtlAreLongPathsEnabled
        enabled.restype = ctypes.c_ubyte        # (a BOOLEAN: one byte)
        return bool(enabled())
    except (OSError, AttributeError):
        return False


class HorseSquadCalls:
    """Mixed into StudioApi: uses EraUnitCalls' (_era_plan, _era_make, _era_options, _era_record, era_unit_remove),
    its _open, _all_units, _names, _game, _path, _home, _jobs, _mod_dir, _new_units, model_import,
    model_import_remove, delete_unit and _kind_rows."""

    # --- what the Units tab lists ---
    def _horse_entry(self, lang: str = "us") -> dict | None:
        """The Horse Squad as the Units tab lists it: ENTRY, with what the game's index says of the US rifle squad
        it's made from: its build menu ("game_nation", "factory": the add form's first pick) and its type ("card": the
        game's word for its kind of unit, on the US rifle squad's card); "names": its name in each of the Studio's
        languages (words.toml eras_horse_name, for the search box). The type in English by default: the kind its group
        goes by (era_units._era_group, as an era unit's library card); in `lang` for the page and the list (_horse_card).
        None when the game has no US rifle squad: it can't be made then."""
        from .api import _words
        ix = self._open()
        try:
            row = next((u for u in self._all_units(ix) if u["address"] == SQUAD), None)
            if row is None:
                return None
            card = self._horse_card(ix, lang)
        finally:
            ix.close()
        names = sorted({t for t in _words().get("eras_horse_name", {}).values() if isinstance(t, str) and t.strip()})
        return dict(ENTRY, game_nation=row["nation"], factory=row["factory"], card=card, names=names)

    def _horse_card(self, ix, lang: str) -> str:
        """The US rifle squad's type (the game's word on its card: the Horse Squad's type) in the Studio's language
        `lang`, as the Units list says a game unit's type (api.units: its HTML entities undone too): a language the game
        has its own, else (Persian, the code names' "base") the game's English; "" when the index has none."""
        import html
        from rusemod import schema
        row = next((u for u in self._all_units(ix) if u["address"] == SQUAD), None)
        key = row.get("type_key") if row is not None else None
        told = lang if lang in schema.LANGS else "us"
        return html.unescape((ix.names([key], told).get(key) or "") if key else "").strip()

    def _era_built(self, lang: str = "us") -> list[dict]:
        """The units made for RUSE 2.0 the game can make (era_units_list's "built" rows), their type in `lang`: none
        while the game's index can't be read."""
        import sqlite3
        try:
            entry = self._horse_entry(lang)
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
        """era_unit_page for the Horse Squad: its entry, its type ("card") in the Studio's language `lang`, "added" (its
        unit's address in this mod, or None), "start": the US rifle squad alone (by its game name: its models are made
        for that unit's soldiers), "has_model" False (no library model: its models are made when it's added),
        "building": the job adding it while one runs (the page follows it), and era_unit_start's "price", "size",
        "size_info", "research" and "group" for its own build menu (its group by its type in English, `entry`'s)."""
        from rusemod import schema
        record = self._era_record() if self._mod_dir() is not None else {}
        ix = self._open()
        try:
            rows = {u["address"]: u for u in self._all_units(ix) if u["address"] in SQUADS}
            names = self._names(ix, list(rows), lang if lang in schema.LANGS else "us")
            card = self._horse_card(ix, lang) or entry["card"]
        finally:
            ix.close()
        # (each country's rifle squad the game has, by its game name: the US one first, suggested, as before)
        start = [{"address": a, "name": names.get(a) or a.rsplit("/", 1)[-1],
                  "nation": rows[a]["nation"] if a != SQUAD else entry["game_nation"], "suggested": a == SQUAD,
                  "same_type": True, "country": SQUADS[a]} for a in SQUADS if a in rows]
        options = self._era_options(None, {}, entry, SQUAD, entry["game_nation"], entry["factory"], lang)
        return dict(entry, card=card, added=record.get(KEY), picture=None, start=start, has_model=False,
                    building=self._horse_running(), **options)

    def _horse_running(self) -> str | None:
        """The job adding the Horse Squad while it runs, else None."""
        job = self.__dict__.get("_horse_job")
        return job if job and job in self._jobs and self._jobs[job].state == "running" else None

    # --- adding it ---
    def horse_squad_add(self, nation: int, factory: int, name: str | None = None, price=None, research_from=None,
                        research_price=None, research_time=None, group=None, source: str | None = None) -> dict:
        """Add the Horse Squad to the current mod, as era_unit_add adds an era unit (its name, `price`, nation
        `nation`'s build menu `factory`, the unit it's `research_from` with `research_price` and `research_time`, its
        `group`: the add form's, era_units._era_plan; it starts from `source`, one of SQUADS: the rifle squad whose
        soldiers its riders are made from, the US one when none is given), its models made first from the player's
        own game: a job the page follows (Job lines STEPS, in turn: "build" its two files with the builder, "unit" the
        unit made, "riflemen" and "bazooka" each one's model imported). Done, its "result" is {"address", "name"};
        failed, its message says why in words and nothing is left made. What's asked is checked before anything starts
        (refused at once, as era_unit_add refuses it); a second ask while one runs follows it. Returns {"job": id}."""
        from rusemod.webui import Job
        from .api import StudioError
        source = source or SQUAD
        if source not in SQUADS:
            # not a game rule: the rifle squads its riders are made from (each read from the game first: SQUADS)
            raise StudioError(f"The Generic Horse's riders are made from one of these rifle squads: "
                              f"{', '.join(a.rsplit('/', 1)[-1] for a in SQUADS)}. {source} isn't one of them.")
        entry = self._era_built_entry(KEY)
        mod = self._mod_dir()
        # everything asked for, checked before the long part (era_unit_add's checks: the mod, already in it, the
        # research, the group's room, the research price and time; and the name's address free)
        self._era_plan(KEY, None, {}, entry, nation, factory, source, None, research_from, research_price,
                       research_time, group)
        self._horse_name_free(name, source)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E.: the Generic Horse is made from your own copy of the game.")
        builder = self._horse_builder()
        self._horse_room(builder, mod, name, source)
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
            # the folder being written (the platform folder's, then the mod) and the file being read (each soldier's
            # file while its model is imported): said when a file can't be read or written and the error names none
            where, reading = self._home / FOLDER, None
            try:
                say(STEPS[0])
                files = self._horse_build(builder, game, source)
                where = mod
                self.__dict__["_horse_mod"] = mod      # from here its mod stays the one edited (_horse_guard)
                try:
                    # the mod it was asked for, still the one being edited: nothing is made in another
                    if self._mod_dir() != mod:
                        raise StudioError("The mod being edited changed while the Generic Horse was being made, so it "
                                          "wasn't added: add it again.")
                    # from here every step writes into this mod, even when another Studio window on the same platform
                    # folder picks another mod meanwhile (its _horse_guard is its own: api._mod_dir keeps this one)
                    self.__dict__["_horse_pin"] = mod
                    say(STEPS[1])
                    made, before = None, set(self._new_units())
                    try:
                        plan = self._era_plan(KEY, None, {}, entry, nation, factory, source, None, research_from,
                                              research_price, research_time, group)
                        made = self._era_make(KEY, self._era_library()[1], entry, plan, nation, factory, name, price)
                        say(STEPS[2])
                        reading = files["rifle"]
                        self.model_import(made["address"], str(files["rifle"]))
                        say(STEPS[3])
                        reading = files["bazooka"]
                        self.model_import(made["address"], str(files["bazooka"]), kind=HEAVY)
                        reading = None
                        self._horse_check(made["address"])
                    except BaseException:
                        self._horse_undo(made["address"] if made else None, before, source)
                        raise
                finally:
                    self.__dict__["_horse_mod"] = None
                    self.__dict__["_horse_pin"] = None
            except OSError as exc:
                # (in words, never Python's own: the job's message goes to the page in the modder's language)
                self._horse_too_long(exc)
                raise self._horse_file_error(exc, where, reading) from exc
            except StudioError as exc:
                # a file the Studio's own import couldn't read or write (api.file_error, raised from its OSError): said
                # as one of the add's own steps' is, that the Horse Squad wasn't added (the import's words don't say)
                if not isinstance(exc.__cause__, OSError):
                    raise
                self._horse_too_long(exc.__cause__)
                raise self._horse_file_error(exc.__cause__, where, reading) from exc.__cause__
            job.result = {"address": made["address"], "name": made["name"]}

        return job.start(work, f"{NAME} is in your mod.", plain=(StudioError, OSError))

    def _horse_name_free(self, name, source: str = SQUAD) -> None:
        """A name given whose address is taken (a unit of the game's, or one the mod made), refused before the long
        part, in _unit_new's words (it names a copy of the US rifle squad so); no name given: _era_make's own way."""
        from .api import _PREFIX, StudioError, safe_name
        wanted = (name or "").strip()
        stem = safe_name(wanted) if wanted else ""
        if not stem:
            return    # (none given, or no letters A-Z: _unit_new finds it a free address)
        namespace, tail = source.rsplit("/", 1)
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

    def _horse_room(self, builder, mod: Path, name, source: str = SQUAD) -> None:
        """Before the long part: the longest path the Add is going to write, in the platform folder (the builder's
        scratch files under horse_squad/: its longest_written, when it says) and in the mod (each animation of the unit
        as Import model writes it, under the name the unit is going to get: `name`, else its own and the one it takes
        when that's taken); a StudioError saying which folder is too deep and by how much, and what to change, when
        Windows won't take it (PATH_MOST; nothing when this program may write longer paths: long_paths_on)."""
        from .api import _PREFIX, StudioError, safe_name
        self.__dict__["_too_deep"] = None
        if long_paths_on():
            return
        root = self._home / FOLDER
        work = root / (WORK + "x" * 8)
        longest = getattr(builder, "longest_written", None)
        try:
            asked = (work,) if source == SQUAD else (work, source)    # (another country's riders: their own files)
            need = int(longest(*asked)) if callable(longest) else len(str(work))
        except (TypeError, ValueError):
            need = len(str(work))
        if need > PATH_MOST:
            # (the page offers the quick fix beside these words: ruse_studio.homemove, home_move_offer's "needed")
            self.__dict__["_too_deep"] = {"what": "platform", "folder": str(self._home), "over": need - PATH_MOST}
            # not a game rule: Windows' longest path, which the files the Horse Squad is made into must fit
            raise StudioError(f"The Generic Horse can't be added: the folder the Studio keeps its own files in "
                              f"({self._home}) is too deep for it. Adding it would write a file whose path is "
                              f"{need - PATH_MOST} character(s) longer than Windows takes ({PATH_MOST} at most). Move "
                              f"it to a folder with a shorter path, and set the Windows environment variable "
                              f"RUSE_PLATFORM_HOME to that folder, then add it again.")
        m = _PREFIX.match(source.rsplit("/", 1)[-1])
        prefix = m.group(1) if m else "Descriptor_Unit_"
        wanted = (name or "").strip()
        stems = [safe_name(wanted)] if wanted and safe_name(wanted) else \
            [safe_name(NAME), safe_name(f"{NAME} ({ENTRY['era']})")]   # (era_units._era_make's two)
        tail = max((prefix + s for s in stems), key=len)
        need = len(str(Path(mod, *OWN_CLIPS, tail, "x" * CLIP_LONGEST + ".part"))) if mod is not None else 0
        if need > PATH_MOST:
            self.__dict__["_too_deep"] = {"what": "mod", "folder": str(mod), "over": need - PATH_MOST}
            # not a game rule: Windows' longest path, which the Horse Squad's animations in the mod must fit
            raise StudioError(f"The Generic Horse can't be added: your mod's folder ({mod}) is too deep for it. Adding "
                              f"it would write a file whose path is {need - PATH_MOST} character(s) longer than "
                              f"Windows takes ({PATH_MOST} at most). Give it a shorter name in the form, or put the mod "
                              f"in a folder with a shorter path, then add it again.")

    def _horse_builder(self):
        """The builder (BUILDER), or a StudioError when this Studio hasn't got it, or has it but a part it needs
        (numpy, say) can't be loaded: said as that, never as the builder not being in it."""
        from .api import StudioError
        try:
            return importlib.import_module(BUILDER)
        except ImportError as exc:
            if exc.name != BUILDER:
                raise self._horse_part_missing(exc) from exc
            # not a game rule: the part of the Studio that makes it
            raise StudioError("This Studio can't make the Generic Horse yet: the part that makes it from your game "
                              "isn't in it.") from None

    @staticmethod
    def _horse_part_missing(exc: ImportError):
        """The StudioError for a part the builder needs that couldn't be loaded (`exc`), named when Python names it."""
        from .api import StudioError
        if exc.name:
            return StudioError(f"This Studio can't make the Generic Horse: a part it needs ({exc.name}) couldn't be "
                               f"loaded. Please report this.")
        return StudioError("This Studio can't make the Generic Horse: a part it needs couldn't be loaded. Please report "
                           "this.")

    def _horse_too_long(self, exc: OSError) -> None:
        """A path longer than Windows takes that stopped the Add (_horse_file_error says it): kept for the page, which
        offers the quick fix beside those words (ruse_studio.homemove)."""
        long = [str(f) for f in (exc.filename, exc.filename2) if f is not None and len(str(f)) > PATH_MOST]
        if long and not long_paths_on():
            self.__dict__["_too_deep"] = {"what": "path", "folder": long[0], "over": len(long[0]) - PATH_MOST}

    @staticmethod
    def _horse_file_error(exc: OSError, folder, reading=None):
        """The StudioError for a file that couldn't be read or written while the Horse Squad was being made or added
        (`exc`), in words and never in Python's own (English, inside the modder's language): the disk full, a file
        another program holds or Windows didn't allow, a file not there, else its error number. A full disk is the one
        holding `folder`, the folder being written then; any other names the file `exc` names (api.file_named: of two,
        the one in the place a new file was being put, never the add's own new one), else the file being read then,
        `reading`, else `folder` (api.file_error's rule)."""
        from .api import StudioError, disk_full, file_named
        if disk_full(exc):
            return StudioError(f"The Generic Horse couldn't be added: the disk holding {folder} is full. Make room on "
                               f"it, then add it again.")
        path = file_named(exc, reading if reading is not None else folder)
        long = [str(f) for f in (exc.filename, exc.filename2) if f is not None and len(str(f)) > PATH_MOST]
        if long and not long_paths_on():
            # not a game rule: Windows' longest path (one _horse_room's sum didn't see coming: said as what it is,
            # never as a file that "isn't there")
            return StudioError(f"The Generic Horse couldn't be added: {long[0]} is {len(long[0]) - PATH_MOST} "
                               f"character(s) longer than Windows takes in a path ({PATH_MOST} at most). Put the "
                               f"folder it is in somewhere with a shorter path, then add it again.")
        code = getattr(exc, "winerror", None) or exc.errno
        if isinstance(exc, PermissionError):   # (a file another program has open comes as this on Windows)
            return StudioError(f"The Generic Horse couldn't be added: {path} couldn't be read or written, because "
                               f"another program has it open or Windows didn't allow it. Close that program, then add "
                               f"it again.")
        if isinstance(exc, FileNotFoundError):
            return StudioError(f"The Generic Horse couldn't be added: {path} isn't there.")
        if code is None:
            return StudioError(f"The Generic Horse couldn't be added: {path} couldn't be read or written. Please report "
                               f"this.")
        return StudioError(f"The Generic Horse couldn't be added: {path} couldn't be read or written (error {code}). "
                           f"Please report this.")

    def _horse_build(self, builder, game: Path, source: str = SQUAD) -> dict:
        """The Horse Squad's two model files made from the player's own game (`game`) by `builder`: into a folder of
        their own first, then into the platform folder's horse_squad/ under the names the builder gave them (the files
        made before are replaced: the mod's model records name them, for Resize and Move). Returns {"rifle",
        "bazooka": its path there}. The builder's own refusal is said in its words (HorseSquadError, in the modder's
        language with the frame: errortext.WITHIN); a part it needs that can't be loaded, memory run out, or anything
        else it stopped on, said in words too (an OSError: by the job, horse_squad_add); files it didn't make where it
        was asked to, refused."""
        from .api import StudioError
        refusal = getattr(builder, "HorseSquadError", None)
        refusals = (refusal,) if isinstance(refusal, type) and issubclass(refusal, Exception) else ()
        root = self._home / FOLDER
        work = root / f"{WORK}{uuid.uuid4().hex[:8]}"
        work.mkdir(parents=True)
        try:
            try:
                got = builder.horse_squad_glbs(Path(game), work, index=self._path(), say=lambda _line: None,
                                               **({} if source == SQUAD else {"squad": source}))
            except refusals as exc:
                # not a game rule: the builder's own refusal, in its plain words, of what the game gave it
                raise StudioError(f"The Generic Horse can't be made from your game: {exc}") from None
            except OSError:
                raise
            except ImportError as exc:   # (a part it loads as it goes)
                raise self._horse_part_missing(exc) from exc
            except MemoryError:
                # not a game rule: this PC's memory
                raise StudioError("The Generic Horse can't be made from your game: this PC ran out of memory while "
                                  "making it. Close other programs, then add it again.") from None
            except Exception as exc:
                # (the builder stopped on something it doesn't check for: a mistake of its own, or game data unlike any
                # it was tried on; Bug Watch counts where, from the error it was raised from)
                # not a game rule: what the builder didn't expect
                raise StudioError("The Generic Horse can't be made from your game: making it stopped on something the "
                                  "Studio didn't expect. Please report this.") from exc
            files = {}
            for role in ROLES:
                path = Path(got[role]) if isinstance(got, dict) and got.get(role) else None
                if path is None or not path.is_file() or path.suffix.lower() != ".glb" \
                        or path.resolve().parent != work.resolve():
                    files = None
                    break
                files[role] = path
            if not files or len({p.name.lower() for p in files.values()}) != len(ROLES):
                # not a game rule: what the builder hands over (two .glb files of its own, where it was asked)
                raise StudioError("The Generic Horse can't be made from your game: its two model files didn't come out. "
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
            raise StudioError("The Generic Horse's two models didn't come in on the same bones, so it wasn't added. "
                              "Please report this.")

    def _horse_undo(self, address: str | None, before: set, source: str = SQUAD) -> None:
        """A Horse Squad this job couldn't finish, taken out again, and only what this job made: its unit (`address`,
        the one _era_make made; only when that never came back, a copy of the US rifle squad that wasn't among the mod's
        new units `before` _era_make began), with its models, its animations and its credit line (era_unit_remove, when
        the mod's era_units.json names it), never a Horse Squad the mod had already, nor a copy the modder made while
        the add ran. Each step is tried even when one before it failed (Delete takes every file of the unit:
        edits.remove_unit); a StudioError when the unit is still in the mod after all (the job then says that, not
        that it wasn't added)."""
        from .api import StudioError
        self.__dict__["_horse_undoing"] = True   # (era_unit_remove refuses the page while the add runs, not this)
        mine = set()
        try:
            units = self._new_units()
            mine = {address} if address else {a for a, u in units.items() if a not in before and u.source == source}
            recorded = self._era_record().get(KEY)
            if recorded in mine:
                try:
                    self.era_unit_remove(KEY, "anyway")
                except (StudioError, OSError):
                    pass   # (the steps below take what it couldn't)
            for left in sorted(mine):
                if left not in self._new_units():
                    continue
                try:
                    self.model_import_remove(left)
                except (StudioError, OSError):
                    pass   # (Delete below takes the unit's model files all the same)
                try:
                    self.delete_unit(left, "anyway")
                except (StudioError, OSError):
                    pass   # (said below: the unit is still in the mod)
        except (StudioError, OSError):
            pass
        finally:
            self.__dict__["_horse_undoing"] = False
        try:
            still = [a for a in mine if a in self._new_units()]
        except (StudioError, OSError):
            still = sorted(mine)
        if still:
            # not a game rule: what this job made couldn't all be taken out of the mod again
            raise StudioError("The Generic Horse couldn't be added, and taking it back out failed too, so part of it "
                              "is still in your mod: take it out of your mod on its page in the Units tab, or delete "
                              "it on its unit page.")

    def _horse_gone(self, address: str, file, moving: bool) -> None:
        """Before Resize or Move (`moving`) is refused because the file a model was made from isn't there any more
        (api.model_resize, model_place, _kinds_ready: their words say "import it again"): when `address` is this mod's
        Horse Squad, whose two files the Studio made in the platform folder (the modder never had them to import), a
        StudioError saying its way out instead: taken out of the mod and added again, its files are made again, and
        what was changed on it goes with it. Nothing for any other unit (a Horse Squad made by hand too: its files
        are the modder's own)."""
        from .api import EditsFileError, StudioError
        try:
            mine = self._era_record().get(KEY) == address
        except (OSError, ValueError, EditsFileError):
            return
        if not mine:
            return
        if moving:
            raise StudioError(f"The file the Generic Horse's model was made from isn't there any more ({file}), so it "
                              f"can't be moved. To have it made again, on its page in the Units tab (WWII+) click Take "
                              f"it out of my mod, then Add to my mod: what you changed on it is lost.")
        raise StudioError(f"The file the Generic Horse's model was made from isn't there any more ({file}), so its size "
                          f"can't be changed. To have it made again, on its page in the Units tab (WWII+) click Take it "
                          f"out of my mod, then Add to my mod: what you changed on it is lost.")

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
            raise StudioError("The Generic Horse is being added to this mod: wait for it to finish.")
