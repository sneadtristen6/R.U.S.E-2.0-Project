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

One Generic Horse (the owner, 2026-11-13: "There is one fucking generic horse unit that we're going to have in the
game. That unit already is capable of being completely changed, their uniform, their animations, everything. So it
does not need to be per country." and "I don't want more than one country to have a horse."): its riders are always
made from the US rifle squad (SQUAD), as on the copy that passed in the game; once added it's a new unit like any
other: its nation and build menu picked in the add form and changed on the Nations tab's board (its page shows where it
is and opens that board), every value on its page, its look in Blender.

Its files are kept and known by their bytes (the owner's 12, to "Another player can't resize or move a Generic Horse
from a shared mod ... Accept that?": "the whole point of having the horse in the game is so it can be made into other
units and have a"; his 46: an older mod's horse never changes). Each model's record keeps the SHA-256 of the file it was
made from (its report's SHA: rusemod.unitmodel.import_model's). The Studio never writes a horse file over one, nor over
one another Studio puts there at the same moment: made again differently, the new file goes beside the old one under a
name of its own (_horse_place), so the file an older mod's Generic Horse was made from stays as it was.

Resize and Move go by the FILE a model was made from, never by the unit (_fit_from; the review of f1fa002c, finding 1:
by the unit, the Generic Horse given the modder's own model was refused once he changed his file, with words that threw
his work away): a model made from one of the Generic Horse's files (in this PC's horse_squad/; on another PC, whose
records name only the file's own name, rusemod.package, one with the bytes its builder makes: MADE_BYTES), whatever the
unit (the Generic Horse, or one the modder made from its files), is fitted again only from a file with the bytes it
was made from: its own while it has them, else the one in this PC's horse_squad/ that has them, else refused in words
and nothing changes (_horse_gone), the words saying first the way out that loses nothing: its files made on this PC
again by adding the Generic Horse to another mod. A record from before the SHA-256 was made from the bytes every Studio
before made under that name (MADE_BYTES). A model made from any other file (the modder's own) is fitted from it as it
is now, as before."""
from __future__ import annotations

import importlib
import itertools
import os
import re
import shutil
import threading
import uuid
from pathlib import Path

KEY = "horse-squad"     # its key among the era units (the mod's era_units.json): never one of a library's (era|nation|name)
NAME = "Generic Horse"    # its name in English: the new unit's when the form gives none, and the credits'
AUTHOR = "sneadtristen6"   # the name on his mods
SQUAD = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"   # the US rifle squad it's made from, as horse-studio2 was
BUILDER = "rusemod.horsesquad"   # its two model files from the player's own game (horse_squad_glbs, HorseSquadError)
FOLDER = "horse_squad"  # in the platform folder: every horse file the builder made, which the mod's records name
SHA = "file_sha256"     # a model's record's report: its file's SHA-256 (rusemod.unitmodel.SOURCE_SHA)
# The bytes the Generic Horse's builder makes under each name it gives (rusemod.horsesquad.FILES), and the release
# candidate's under its other countries' names (a8b65194, taken out again by b00a04f8): the same at every commit of the
# builder since it came in (8af3e622), the US ones the passed copy's byte for byte (run on the game 2026-11-13, each
# commit's own builder: scratch/release-0920/agents/genhorse/builders_all.out and builders_countries.out). No builder
# ever made a file under another name. A model's record from before f1fa002c keeps no SHA-256: naming one of the
# Generic Horse's files under one of these names, it was made from these bytes (_made_bytes); under another name (by
# hand, a test's stand-in builder), it is fitted only while its file has bytes a builder makes (_fit_from). A record
# naming only a file's own name (a mod from another PC) whose SHA-256 is one of these was made from one of its files
# (_horse_file). A builder that makes other bytes adds its own here (tests/test_horse_squad.py ties the US ones to the
# passed copy's).
MADE_BYTES = {
    "horse-squad-rifle.glb": "f56a2e237a962d2ada79a218541368d75ec91a1c2d1c8a466eaca70cbb553419",
    "horse-squad-bazooka.glb": "502da7f365c9d660cfc7b32f9e534c4f0ae0bfef0ab2ff6d2c038b25c7f917d8",
    "horse-squad-ger-rifle.glb": "1ae41d4b41fd0343dd1b653270c7db66339d604184dfb27338d16258d6fafcc3",
    "horse-squad-ger-bazooka.glb": "4583729be95c7f205426596c83c7ba649d5748a2a4a84e43d7cd91d8d91880b8",
    "horse-squad-uk-rifle.glb": "f6868ab83351f2c14af9bcbc1470aea29fb8972304dbad4913fc8941c484ca74",
    "horse-squad-uk-bazooka.glb": "6f56466cb776250d025920205d89814e1bdcfbf814d81359ef5d05b0d8f62382",
    "horse-squad-fr-rifle.glb": "912eb487170b11f9cff6f4df3860aff106dd044aa0f3e9d33e2582022229d73f",
    "horse-squad-fr-bazooka.glb": "ff4f804a7d7e3033f299fd641e4f556e2635154fa85d0f40b1f5b0e2ceb582ad",
}
_HEX64 = re.compile(r"[0-9a-f]{64}")
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


def file_sha256(path) -> str:
    """The SHA-256 of the file at `path`, in hex (rusemod.unitmodel.file_sha256's, here so the Add's job and the size
    box load nothing more)."""
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def made_sha(record) -> str | None:
    """The SHA-256 a model's record keeps of the file it was made from (its report's SHA, 64 hex letters), None when it
    keeps none (a record from before it, or one edited by hand)."""
    report = record.get("report") if isinstance(record, dict) else None
    sha = report.get(SHA) if isinstance(report, dict) else None
    return sha.lower() if isinstance(sha, str) and _HEX64.fullmatch(sha.lower()) else None


def _same_place(a, b) -> bool:
    """Whether two paths name the same place on this PC (any slashes, any case on Windows, through a link too)."""
    try:
        if os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b))):
            return True
        return os.path.normcase(os.path.realpath(str(a))) == os.path.normcase(os.path.realpath(str(b)))
    except (OSError, ValueError):
        return False


def _put_new(made: Path, there: Path) -> bool:
    """`made` moved to `there` only when nothing is there, the check and the move one step, so a file another Studio
    puts there at the same moment is never written over (the review of f1fa002c: a look, then a replace, could write
    over one put there between the two); False when something is there, `made` left where it is."""
    import sys
    if sys.platform == "win32":
        try:
            os.rename(made, there)      # (Windows' rename never writes over a file that's there)
        except FileExistsError:
            return False
        return True
    try:
        os.link(made, there)            # (elsewhere a second name for it, which can't be made over one that's there)
    except FileExistsError:
        return False
    except OSError:                     # (a drive that takes no second names: looked at, then moved, as before)
        if os.path.lexists(there):
            return False
        os.replace(made, there)
        return True
    os.unlink(made)
    return True


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
            name = self._names(ix, [SQUAD], lang if lang in schema.LANGS else "us").get(SQUAD) or SQUAD.rsplit("/", 1)[-1]
            card = self._horse_card(ix, lang) or entry["card"]
        finally:
            ix.close()
        start = [{"address": SQUAD, "name": name, "nation": entry["game_nation"], "suggested": True,
                  "same_type": True}]
        options = self._era_options(None, {}, entry, SQUAD, entry["game_nation"], entry["factory"], lang)
        return dict(entry, card=card, added=record.get(KEY), picture=None, start=start, has_model=False,
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
        self.__dict__["_too_deep"] = None    # (this Add's own refusal of a folder too deep, if any: home_move_offer)
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
            raise StudioError("We couldn't find R.U.S.E.: the Generic Horse is made from your own copy of the game.")
        builder = self._horse_builder()
        self._horse_room(builder, mod, name)
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
                files = self._horse_build(builder, game)
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
                        plan = self._era_plan(KEY, None, {}, entry, nation, factory, SQUAD, None, research_from,
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
                        self._horse_undo(made["address"] if made else None, before)
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

    def _horse_room(self, builder, mod: Path, name) -> None:
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
            need = int(longest(work)) if callable(longest) else len(str(work))
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
        m = _PREFIX.match(SQUAD.rsplit("/", 1)[-1])
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

    def _horse_build(self, builder, game: Path) -> dict:
        """The Horse Squad's two model files made from the player's own game (`game`) by `builder`: into a folder of
        their own first, then into the platform folder's horse_squad/ under the names the builder gave them, never over
        a file there with other bytes (_horse_place: every mod's model records name these files, for Resize and Move,
        and an older mod's horse never changes). Returns {"rifle", "bazooka": its path there, the file its unit's
        model is made from}. The builder's own refusal is said in its words (HorseSquadError, in the modder's
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
                got = builder.horse_squad_glbs(Path(game), work, index=self._path(), say=lambda _line: None)
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
            return {role: self._horse_place(path, root) for role, path in files.items()}
        finally:
            shutil.rmtree(work, ignore_errors=True)

    @staticmethod
    def _horse_place(made: Path, root: Path) -> Path:
        """A file the builder made (`made`, in the Add's own folder) put in the platform folder's horse_squad/ (`root`):
        under the builder's name, or when a file there has other bytes (made by another builder, from another game),
        beside it under that name with the start of its SHA-256 (<name>-<16 letters>.glb, then numbered), never over
        it: the mods made before name that file, and an older mod's horse never changes (the owner's 46). A file there
        with the same bytes is kept as it is, the new one not written; one that can't be read is left too. Put there in
        one step with the look whether a name is free (_put_new): a file another Studio's Add puts under that name at
        the same moment is never written over either. Returns where it is."""
        sha = file_sha256(made)
        stem, suffix = made.stem, made.suffix
        names = itertools.chain((made.name, f"{stem}-{sha[:16]}{suffix}"),
                                (f"{stem}-{sha[:16]}-{n}{suffix}" for n in itertools.count(2)))
        for name in names:
            there = root / name
            if _put_new(made, there):
                return there
            try:
                if there.is_file() and file_sha256(there) == sha:
                    return there        # (the same bytes: kept as they are)
            except OSError:
                continue                # (one that can't be read now: never written over, the next name tried)

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

    def _horse_undo(self, address: str | None, before: set) -> None:
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
            mine = {address} if address else {a for a, u in units.items() if a not in before and u.source == SQUAD}
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

    # --- Resize and Move: the file its model was made from (the owner's 12 and 46), by the FILE, never by the unit ---
    def _fit_from(self, record) -> Path | None:
        """The file Resize and Move fit a new unit's model (whose record is `record`) again from, on this PC
        (api._made_from); None when there's none. It goes by the file the record names, never by which unit it is (the
        review of f1fa002c, finding 1: by the unit, the Generic Horse given the modder's own model was refused once he
        changed his file, and finding 3: by the unit, an era_units.json that couldn't be read turned the check off).

        A file of the modder's own (anything but the Generic Horse's files: _horse_file), on this PC: that file as it is
        now, as before, for every unit, the Generic Horse too. One of the Generic Horse's files (his 46: an older mod's
        horse never changes): only a file with the bytes the model was made from (_made_bytes): its own while it has
        them, else the one in this PC's horse_squad/ that has them, under any name (_horse_with); one there that can't
        be read now: that file, whose reading says why when it's fitted. A file not on this PC (a mod made on another
        PC names only the file's own name, rusemod.package; or gone): the one in this PC's horse_squad/ with the bytes
        the record keeps (the owner's 12: a Generic Horse from another PC is fitted again here when this PC's own horse
        files are the same), whatever file it was. A record from before the SHA-256 naming one of the Generic Horse's
        files under a name no builder gives (by hand, or a test's stand-in builder): its file only while it has bytes
        a builder makes (MADE_BYTES), never other bytes."""
        file = record.get("from") if isinstance(record, dict) else None
        if not isinstance(file, str) or not file:
            return None
        path = Path(file)
        there = path if path.is_absolute() and path.is_file() else None
        if there is not None and not self._horse_file(record):
            return there
        sha = self._made_bytes(record)
        if sha is None:
            if there is None:
                return None
            try:
                return there if file_sha256(there) in MADE_BYTES.values() else None
            except OSError:
                return there
        if there is not None:
            try:
                if file_sha256(there) == sha:
                    return there
            except OSError:
                return there
        return self._horse_with(sha)

    def _horse_file(self, record) -> bool:
        """Whether the file a model's record (`record`) names is one of the Generic Horse's: by its full path, in this
        PC's horse_squad/ (the platform folder's); by its own name alone (a mod made on another PC: rusemod.package),
        when the bytes the record keeps are ones its builder makes (MADE_BYTES). Whatever the unit (the Generic Horse,
        or one the modder made from its files); never by era_units.json. (A file of the modder's own elsewhere, even
        one he copied from there, is his: fitted as it is.)"""
        file = record.get("from") if isinstance(record, dict) else None
        if not isinstance(file, str) or not file:
            return False
        if Path(file).is_absolute():
            return self._in_horse_folder(file)
        return made_sha(record) in MADE_BYTES.values()

    def _in_horse_folder(self, file) -> bool:
        """Whether `file` is in this PC's horse_squad/ (the platform folder's), where it has it or not."""
        return _same_place(Path(str(file)).parent, self._home / FOLDER)

    def _made_bytes(self, record) -> str | None:
        """The SHA-256 of the bytes the model whose record is `record` was made from: the one the record keeps
        (made_sha); else, for one of the Generic Horse's files under a name its builder gives, the bytes every Studio
        before f1fa002c made under that name (MADE_BYTES: the review of f1fa002c, finding 2, a record from before the
        SHA-256 fitted from other bytes without a word); None when not known."""
        sha = made_sha(record)
        if sha is not None or not self._horse_file(record):
            return sha
        file = record.get("from")
        return MADE_BYTES.get(Path(file).name.lower()) if isinstance(file, str) and file else None

    def _horse_with(self, sha: str) -> Path | None:
        """The file in this PC's horse_squad/ (the platform folder's) whose SHA-256 is `sha`; None when none is."""
        try:
            files = sorted(p for p in (self._home / FOLDER).iterdir() if p.suffix.lower() == ".glb" and p.is_file())
        except OSError:
            return None
        for p in files:
            try:
                if file_sha256(p) == sha:
                    return p
            except OSError:
                continue
        return None

    def _horse_is(self, address) -> bool:
        """Whether `address` is this mod's Generic Horse (its era_units.json names it); False when that can't be
        read. Only which way out the words of _horse_gone say goes by it, never whether a model is fitted."""
        from .api import EditsFileError
        if not address:
            return False
        try:
            return self._era_record().get(KEY) == address
        except (OSError, ValueError, EditsFileError):
            return False

    def _horse_named(self, record, address) -> bool:
        """Whether a refusal of Resize or Move says the Generic Horse's words (_horse_gone): its record names one of
        the Generic Horse's files (_horse_file); or, a record from before the SHA-256 naming only a file's own name (a
        mod exported before it), when the unit is this mod's Generic Horse, as before."""
        if self._horse_file(record):
            return True
        file = record.get("from") if isinstance(record, dict) else None
        return isinstance(file, str) and bool(file) and not Path(file).is_absolute() and made_sha(record) is None \
            and self._horse_is(address)

    def _horse_gone(self, address: str, record, moving: bool) -> None:
        """Before Resize or Move (`moving`) is refused because no file with the bytes a model was made from is on this
        PC (_fit_from: None; api.model_resize, model_place, _kinds_ready: their words say "import it again"): when the
        file the model's `record` names is one of the Generic Horse's (_horse_named), a StudioError saying that it
        isn't on this PC as it was then (gone, or there with other bytes: its model is never fitted from them, it
        stays as it is) and the way out that loses nothing first (the review of f1fa002c, finding 5): the Generic
        Horse added to another mod makes its files on this PC again, and with the same bytes as before (the builder
        makes the same ones from the same game), Resize and Move then work; else, this mod's Generic Horse taken out
        of the mod and added again (what was changed on it lost), another unit's model imported again. Nothing for any
        other file (the modder's own: "import it again")."""
        from .api import StudioError
        if not self._horse_named(record, address):
            return
        file = record.get("from")
        # not a game rule: a model made from the Generic Horse's files is fitted again only from the bytes it was
        # made from (the owner's 46)
        if self._horse_is(address):
            if moving:
                raise StudioError(f"The file the Generic Horse's model was made from isn't there any more, or isn't as "
                                  f"it was then ({file}), so it can't be moved and it stays as it is. Nothing is lost "
                                  f"if its files are made on this PC again: add the Generic Horse to another mod (a "
                                  f"new one will do) with Add to my mod in the Units tab (WWII+), then move it here "
                                  f"again: that works when they come out the same as the ones it was made from. If "
                                  f"not, on its page in the Units tab (WWII+) click Take it out of my mod, then Add to "
                                  f"my mod: what you changed on it is lost.")
            raise StudioError(f"The file the Generic Horse's model was made from isn't there any more, or isn't as it "
                              f"was then ({file}), so its size can't be changed and it stays as it is. Nothing is lost "
                              f"if its files are made on this PC again: add the Generic Horse to another mod (a new "
                              f"one will do) with Add to my mod in the Units tab (WWII+), then change its size here "
                              f"again: that works when they come out the same as the ones it was made from. If not, on "
                              f"its page in the Units tab (WWII+) click Take it out of my mod, then Add to my mod: "
                              f"what you changed on it is lost.")
        if moving:
            raise StudioError(f"A model of this unit was made from one of the Generic Horse's files, which isn't there "
                              f"any more, or isn't as it was then ({file}), so it can't be moved and it stays as it "
                              f"is. Nothing is lost if the Generic Horse's files are made on this PC again: add the "
                              f"Generic Horse to a mod (a new one will do) with Add to my mod in the Units tab "
                              f"(WWII+), then move it here again: that works when they come out the same as the ones "
                              f"it was made from. If not, import that model again.")
        raise StudioError(f"A model of this unit was made from one of the Generic Horse's files, which isn't there any "
                          f"more, or isn't as it was then ({file}), so its size can't be changed and it stays as it "
                          f"is. Nothing is lost if the Generic Horse's files are made on this PC again: add the "
                          f"Generic Horse to a mod (a new one will do) with Add to my mod in the Units tab (WWII+), "
                          f"then change its size here again: that works when they come out the same as the ones it was "
                          f"made from. If not, import that model again.")

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
