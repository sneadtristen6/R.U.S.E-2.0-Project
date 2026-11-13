"""The Horse Squad in the Studio's eleven languages, never English inside the modder's language (review of 2026-11-12,
the words group: review-loss F14, review-path F5 and F6; the brief: "English left in a translated message is a fault").

- The builder's refusals (rusemod.horsesquad's HorseSquadError, every one in the code): the Studio passes each on in its
  frame "The Horse Squad can't be made from your game: {0}" (horse_squad._horse_build), and says the frame and the
  refusal in its language, each from its errors.toml entry (errortext.WITHIN; the refusal's entry marked with its
  frame). A text none of those entries makes stays as it came: never taken apart by a short entry for other texts.
- The builder failing otherwise: a file it couldn't read or write in words (never Python's own), anything else it stops
  on in words (never "Something went wrong: <Type>"), a part it needs that can't be loaded said as that (never "isn't in
  it"); a file that can't be written once its unit is made, in words too, naming the mod.
- The Horse Squad by its name in the modder's language in the era units' refusals (already in this mod, researched
  from a unit it can't be, not in this mod), an era unit's own name kept as its library says it.
- Its type (the game's word on the US rifle squad's card) in the Studio's language on the WWII+ list and its page, from
  the Studio's game index (English for Persian and the code names, as the Units list says a game unit's type); its group
  still goes by the English one.
- Resize and Move with its files gone from the platform folder: the way out for a Horse Squad (taken out of the mod and
  added again, by the page's own words), never "import it again", which it can't; "every ground unit" says it skipped
  it and why in the Studio's language (the line's first word, which the page reads, the same in every language).

On the Studio tests' made-up game (WithMod) with a stand-in builder, as tests/test_horse_squad.py; the type on the
Studio's game index (RUSE_GAME_INDEX or RUSE_STUDIO_INDEX, this PC's by default; skipped without it). Nothing of the
game's is written."""
import errno
import json
import os
import re
import sys
import tempfile
import tomllib
import types
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)

from test_horse_squad import finished, stand_in, tree
from test_studio import WithMod
from ruse_studio import era_units, errortext, horse_squad
from ruse_studio.api import StudioApi, StudioError
from rusemod import buildtext, schema, wordedtext

KEY, SQUAD = horse_squad.KEY, horse_squad.SQUAD
SRC = Path(__file__).resolve().parents[1] / "src"
BUILDER_FILE = SRC / "rusemod" / "horsesquad.py"
UI = SRC / "ruse_studio" / "ui"
FRAME = "The Generic Horse can't be made from your game: {0}"
OTHERS = tuple(lang for lang in errortext.LANGS if lang != "us")
INDEX = Path(os.environ.get("RUSE_GAME_INDEX") or os.environ.get("RUSE_STUDIO_INDEX")
             or "D:/RUSE-2.0/scratch/modelgaps/game-index.sqlite")
LIBERTY = "WWI|USA|Mark VIII Liberty"


def entries() -> dict:
    return tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))


def words() -> dict:
    return tomllib.loads((SRC / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))


def builder_templates() -> list:
    """Every refusal of the builder, as its template (each HorseSquadError text in its code)."""
    return wordedtext.templates_in([BUILDER_FILE], {"HorseSquadError": 0}, min_text=0)


def made(template: str, *values) -> str:
    """A text as the code makes it from its template."""
    return template.replace("{{", "\x00").replace("}}", "\x01").format(*values).replace("\x00", "{").replace("\x01", "}")


def raising(exc, refusal=None):
    """A stand-in builder (THE CONTRACT: horse_squad_glbs, HorseSquadError) that stops on `exc`, or on its own
    HorseSquadError with the text `refusal`."""
    module = types.ModuleType(horse_squad.BUILDER)

    class HorseSquadError(ValueError):
        pass

    def horse_squad_glbs(game, out, *, index=None, say=print):
        Path(out, "half.glb").write_bytes(b"half made")      # (what it left: the Studio's own folder, removed)
        raise HorseSquadError(refusal) if refusal is not None else exc

    module.HorseSquadError = HorseSquadError
    module.horse_squad_glbs = horse_squad_glbs
    return module


class WithLibrary(WithMod):
    """The made-up game with an era units library holding one WWI unit (the Mark VIII Liberty), nothing of WWII+."""

    def setUp(self):
        super().setUp()
        lib = Path(tempfile.mkdtemp(dir=self.tmp.name))
        (lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": [
            {"key": LIBERTY, "era": "WWI", "nation": "USA", "name": "Mark VIII Liberty", "in_place_of": "",
             "card": "Heavy Tank", "building": "Armor base", "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman",
             "copies_name": "", "game_nation": 0, "factory": 10, "aircraft": False, "model": None, "fits": True,
             "picture": None, "credit": {"title": "Liberty model", "author": "maker", "licence": "CC-BY 4.0",
                                         "url": "https://example.org/Liberty", "extra": ""}}]}), encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        patcher.start()
        self.addCleanup(patcher.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def said_in(self, text: str, lang: str) -> str:
        """`text` (a StudioError as raised) as the page gets it in `lang`."""
        self.api.set_pref("lang", lang)
        try:
            again = self.api.page_error(StudioError(text))
            return str(again) if again is not None else text
        finally:
            self.api.set_pref("lang", "us")

    def job_said_in(self, job: str, lang: str) -> str:
        self.api.set_pref("lang", lang)
        try:
            return self.api.job(job)["message"]
        finally:
            self.api.set_pref("lang", "us")


class TheBuildersRefusals(unittest.TestCase):
    def test_each_has_its_words_marked_with_the_frame_it_goes_in(self):
        """Every refusal in the builder's code has an entry marked with the Studio's frame, and no other entry is
        marked (test_errortext checks every language and blank of each; the frame is a Studio error of the code)."""
        found, e = builder_templates(), entries()
        self.assertEqual(len(found), 30)   # (28, and 2 of 2026-11-13: a squad it isn't made from, another country's clips)
        self.assertEqual(sorted(w["us"] for w in e.values() if isinstance(w, dict) and "within" in w), sorted(found))
        self.assertEqual({e[errortext.key_of(t)]["within"] for t in found}, {FRAME})
        self.assertEqual(list(errortext.WITHIN), [FRAME])
        self.assertIn(FRAME, errortext.templates_in(sorted((SRC / "ruse_studio").glob("*.py"))))

    def test_each_is_said_wholly_in_the_studio_s_language_in_its_frame(self):
        """In each of the ten other languages: the frame's words with the refusal's own words inside, its values (a
        folder, a bone, a number) as they came; never the builder's English sentence."""
        e = entries()
        frame = e[errortext.key_of(FRAME)]
        values = ("D:\\Games\\not-a-game", "7")
        for t in builder_templates():
            inner = e[errortext.key_of(t)]
            n = len(wordedtext.BLANK.findall(t))
            english = made(t, *values[:n])
            text = made(FRAME, english)
            for lang in OTHERS:
                with self.subTest(refusal=t[:60], lang=lang):
                    said = errortext.worded(text, lang)
                    self.assertEqual(said, frame[lang].format(inner[lang].format(*values[:n])))
                    self.assertNotIn(english, said)
            self.assertEqual(errortext.worded(text, "us"), text)       # (as raised: English, and the code names')
            self.assertEqual(errortext.worded(text, "base"), text)

    def test_a_text_none_of_its_entries_makes_stays_as_it_came(self):
        """A builder from another version, or a stand-in, says words no entry has: the frame in the modder's language
        and those words as they came, never taken apart by a short entry for other texts ("{0} has no {1}" turned
        "Your game has no horse the Studio can read." into "Your game n'a pas de horse the Studio can read.")."""
        frame = entries()[errortext.key_of(FRAME)]
        for inner in ("Your game has no horse the Studio can read.", "D:\\Games: {not a blank}", ""):
            for lang in OTHERS:
                with self.subTest(inner=inner, lang=lang):
                    self.assertEqual(errortext.worded(made(FRAME, inner), lang), frame[lang].format(inner))

    def test_the_build_s_own_lines_are_said_as_before(self):
        """The nesting is the Studio's errors' (errortext.WITHIN) only: a build line holding another text keeps it."""
        self.assertEqual(buildtext.worded("load order: base -> my-mod", "fr"), "ordre de chargement : base -> my-mod")
        self.assertEqual(wordedtext.worded(errortext.FILE, made(FRAME, "Your game has no horse."), "fr"),
                         made(entries()[errortext.key_of(FRAME)]["fr"], "Your game has no horse."))


class TheAddSaysItInWords(WithLibrary):
    def add_failing(self, builder) -> tuple[dict, Path, dict]:
        """The Horse Squad's Add with `builder` standing in for the builder, in a new mod: (the job's view, the mod,
        the mod's files before), the mod checked as it was and the platform folder left with nothing of it."""
        self.made = getattr(self, "made", 0) + 1
        folder = Path(self.api.new_mod(f"Words {self.made}")["current"])
        before = tree(folder)
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: builder}):
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Generic Horse", 5, group="new")["job"])
        self.assertEqual(view["state"], "failed")
        self.assertEqual(tree(folder), before)
        self.assertEqual(os.listdir(self.home / horse_squad.FOLDER), [])
        return view, folder, before

    def test_a_refusal_in_the_builder_s_words_is_said_wholly_in_the_studio_s_language(self):
        e = entries()
        text = "Your game hasn't the model the Generic Horse is made from: ww2\\res3d\\units\\us\\x.ase2ndfbin."
        view, _folder, _before = self.add_failing(raising(None, refusal=text))
        self.assertEqual(view["message"], made(FRAME, text))
        inner = e[errortext.key_of("Your game hasn't the model the Generic Horse is made from: {0}.")]
        for lang in OTHERS:
            with self.subTest(lang=lang):
                self.assertEqual(self.job_said_in(view["id"], lang),
                                 e[errortext.key_of(FRAME)][lang].format(
                                     inner[lang].format("ww2\\res3d\\units\\us\\x.ase2ndfbin")))

    def test_a_file_the_builder_couldnt_read_or_write_is_said_in_words(self):
        root = self.home / horse_squad.FOLDER
        cases = (
            (OSError(errno.ENOSPC, "No space left on device"),
             f"The Generic Horse couldn't be added: the disk holding {root} is full. Make room on it, then add it again."),
            (PermissionError(errno.EACCES, "Permission denied", "C:\\Somewhere\\rifle.glb"),
             "The Generic Horse couldn't be added: C:\\Somewhere\\rifle.glb couldn't be read or written, because another "
             "program has it open or Windows didn't allow it. Close that program, then add it again."),
            (FileNotFoundError(errno.ENOENT, "No such file or directory", "D:\\Games\\RUSE\\ZZ_Win.dat"),
             "The Generic Horse couldn't be added: D:\\Games\\RUSE\\ZZ_Win.dat isn't there."),
            (OSError(errno.EIO, "Input/output error"),
             f"The Generic Horse couldn't be added: {root} couldn't be read or written (error {errno.EIO}). Please "
             f"report this."),
            (OSError("a pack that ends early"),
             f"The Generic Horse couldn't be added: {root} couldn't be read or written. Please report this."),
            (OSError(errno.EBADF, "Bad file descriptor", 3),         # (a file's number, never said as its name)
             f"The Generic Horse couldn't be added: {root} couldn't be read or written (error {errno.EBADF}). Please "
             f"report this."),
        )
        for exc, expected in cases:
            with self.subTest(exc=repr(exc)):
                view, _folder, _before = self.add_failing(raising(exc))
                self.assertEqual(view["message"], expected)
                self.assertEqual(view["lines"], ["build"])
                for lang in OTHERS:
                    said = self.job_said_in(view["id"], lang)
                    self.assertNotEqual(said, expected, lang)
                    self.assertNotIn("couldn't", said, lang)
                    self.assertNotIn(str(exc), said, lang)

    def test_anything_else_the_builder_stops_on_is_said_in_words(self):
        other = ("The Generic Horse can't be made from your game: making it stopped on something the Studio didn't "
                 "expect. Please report this.")
        memory = ("The Generic Horse can't be made from your game: this PC ran out of memory while making it. Close "
                  "other programs, then add it again.")
        e = entries()
        for exc, expected in ((IndexError("list index out of range"), other), (KeyError("bip01 spine1"), other),
                              (ValueError("bad magic"), other), (ZeroDivisionError("float division"), other),
                              (MemoryError(), memory)):
            with self.subTest(exc=repr(exc)):
                view, _folder, _before = self.add_failing(raising(exc))
                self.assertEqual(view["message"], expected)
                for lang in OTHERS:
                    self.assertEqual(self.job_said_in(view["id"], lang), e[errortext.key_of(expected)][lang])

    def test_a_part_the_builder_needs_that_can_t_be_loaded_is_said_as_that(self):
        named = "This Studio can't make the Generic Horse: a part it needs ({0}) couldn't be loaded. Please report this."
        unnamed = "This Studio can't make the Generic Horse: a part it needs couldn't be loaded. Please report this."
        missing = ("This Studio can't make the Generic Horse yet: the part that makes it from your game isn't in it.")
        folder = Path(self.api.new_mod("Parts")["current"])
        before = tree(folder)
        for exc, expected in ((ModuleNotFoundError("No module named 'numpy'", name="numpy"), made(named, "numpy")),
                              (ImportError("cannot load module more than once per process"), unnamed),
                              (ModuleNotFoundError("No module named 'rusemod.horsesquad'", name=horse_squad.BUILDER),
                               missing)):    # (the control: the builder itself not in this Studio)
            def importing(name, exc=exc):
                raise exc
            with self.subTest(exc=repr(exc)), \
                    mock.patch.object(horse_squad, "importlib", types.SimpleNamespace(import_module=importing)), \
                    self.assertRaises(StudioError) as said:
                self.api.horse_squad_add(0, 10, group="new")
            self.assertEqual(str(said.exception), expected)
            self.assertEqual(tree(folder), before)
            for lang in OTHERS:
                worded = self.said_in(expected, lang)
                self.assertNotEqual(worded, expected, lang)
                self.assertNotIn("couldn't", worded, lang)
        # one it loads as it goes, while it makes the files
        view, _folder, _before = self.add_failing(raising(ModuleNotFoundError("No module named 'rusemod.gltf'",
                                                                              name="rusemod.gltf")))
        self.assertEqual(view["message"], made(named, "rusemod.gltf"))

    def test_a_file_that_can_t_be_written_once_its_unit_is_made_is_said_in_words(self):
        """The riflemen's model can't be written (a full disk): the unit made is taken out again, and the job says
        why in words, naming the mod's folder (never "[Errno 28] No space left on device")."""
        folder = Path(self.api.new_mod("Full disk")["current"])
        before = tree(folder)
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import",
                                  side_effect=OSError(errno.ENOSPC, "No space left on device")):
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Generic Horse", 5, group="new")["job"])
        expected = (f"The Generic Horse couldn't be added: the disk holding {folder} is full. Make room on it, then add "
                    f"it again.")
        self.assertEqual((view["state"], view["message"], view["lines"]),
                         ("failed", expected, ["build", "unit", "riflemen"]))
        after = tree(folder)
        self.assertEqual(json.loads(after.pop(era_units.INDEX)), {})          # (its record emptied, as test_horse_squad)
        after.pop("src/studio.rndf", None)
        self.assertEqual(after, {k: v for k, v in before.items() if k != "src/studio.rndf"})
        self.assertEqual(self.job_said_in(view["id"], "fr"),
                         entries()[errortext.key_of("The Generic Horse couldn't be added: the disk holding {0} is full. "
                                                    "Make room on it, then add it again.")]["fr"].format(folder))


class TheHorseSquadByItsName(WithLibrary):
    """Its name in the era units' refusals is the Studio's own word for it in the modder's language (words.toml
    eras_horse_name, as errors.toml's other Horse Squad entries say it), never "Horse Squad" in English inside them; an
    era unit's name is its library's, kept as it is."""

    def horse_squad_in(self) -> str:
        entry = self.api._era_built_entry(KEY)
        plan = self.api._era_plan(KEY, None, {}, entry, 0, 10, SQUAD, None, None, None, None, "new")
        return self.api._era_make(KEY, self.api._era_library()[1], entry, plan, 0, 10, "Kept", 5)["address"]

    def test_already_in_this_mod(self):
        self.api.new_mod("Twice")
        self.horse_squad_in()
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                self.assertRaises(StudioError) as said:
            self.api.horse_squad_add(0, 10, group="new")
        self.assertEqual(str(said.exception), "Generic Horse is already in this mod")    # (the English as it was)
        name = words()["eras_horse_name"]
        for lang in OTHERS:
            with self.subTest(lang=lang):
                worded = self.said_in(str(said.exception), lang)
                self.assertIn(name[lang], worded)
                self.assertNotIn("Generic Horse", worded)
        # an era unit's own name, as its library says it
        self.api.era_unit_add(LIBERTY, 0, 10)
        with self.assertRaises(StudioError) as said:
            self.api.era_unit_add(LIBERTY, 0, 10)
        self.assertEqual(self.said_in(str(said.exception), "fr"), "Mark VIII Liberty est déjà dans ce mod")

    def test_researched_from_a_unit_that_isn_t_in_its_build_menu(self):
        """(Researched from a unit of its menu but of another group: on the game's index, TheTypeInTheStudiosLanguage;
        this little game's infantry has no research.)"""
        self.api.new_mod("Research")
        nowhere = "$/GFX/Everything/Descriptor_Unit_Nowhere"
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                self.assertRaises(StudioError) as said:
            self.api.horse_squad_add(0, 10, research_from=nowhere, group="new")
        expected = f"Generic Horse can't be researched from {nowhere} in that build menu"
        self.assertEqual(str(said.exception), expected)
        for lang in OTHERS:
            worded = self.said_in(expected, lang)
            self.assertNotIn("Generic Horse", worded, lang)
            self.assertIn(nowhere, worded, lang)
            self.assertNotEqual(worded, expected, lang)

    def test_taken_out_when_it_isn_t_in_the_mod(self):
        self.api.new_mod("Not in")
        with self.assertRaises(StudioError) as said:
            self.api.era_unit_remove(KEY)
        self.assertEqual(str(said.exception), "Generic Horse isn't in this mod")      # (not its key, "horse-squad")
        for lang in OTHERS:
            worded = self.said_in(str(said.exception), lang)
            self.assertNotIn("Generic Horse", worded, lang)
            self.assertNotIn(KEY, worded, lang)
        with self.assertRaises(StudioError) as said:                          # an era unit's: as before
            self.api.era_unit_remove(LIBERTY)
        self.assertEqual(str(said.exception), f"{LIBERTY}: not in this mod")


@unittest.skipUnless(INDEX.is_file(), "the Studio's game index isn't on this PC (RUSE_GAME_INDEX)")
class TheTypeInTheStudiosLanguage(unittest.TestCase):
    def test_the_list_and_its_page_say_it_in_the_studio_s_language(self):
        """The game's own word on the US rifle squad's card, as the index has it in each of its ten languages;
        English for Persian (not a game language) and for the code names; found by it in that language; its group the
        same in every language (it goes by the English type, as an era unit's by its library card)."""
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(index_path=INDEX, game_dir=Path(tmp) / "no-game", home=Path(tmp) / "home")
            api.new_mod("Types")
            ix = api._open()
            try:
                key = next(u for u in api._all_units(ix) if u["address"] == SQUAD)["type_key"]
                told = {lang: (ix.names([key], lang).get(key) or "").strip() for lang in schema.LANGS}
            finally:
                ix.close()
            self.assertEqual(len(set(told.values())), len(schema.LANGS))      # (the index has it in each)
            groups = set()
            for lang in ("base", *schema.APP_LANGS):
                with self.subTest(lang=lang):
                    card = told.get(lang, told["us"])
                    listed = api.era_units_list("WWII", lang=lang)
                    self.assertEqual([(u["key"], u["card"]) for u in listed["units"]], [(KEY, card)])
                    self.assertEqual(listed["types"], [card])
                    self.assertEqual([u["key"] for u in api.era_units_list("WWII", group=f"type:{card}",
                                                                          lang=lang)["units"]], [KEY])
                    page = api.era_unit_page(KEY, lang)
                    self.assertEqual(page["card"], card)
                    groups.add(json.dumps({k: page["group"][k] for k in ("root", "pick", "new")}))
            self.assertEqual(len(groups), 1, groups)
            self.assertEqual(api.era_units_list("WWII")["units"][0]["card"], told["us"])   # (asked with no language)

    def test_researched_from_a_unit_of_another_group_names_it_in_the_studio_s_language(self):
        """The add form's research pick is one of its group's units; another unit of the menu, asked for with a group
        of its own, is refused before anything is made, naming the Horse Squad in the modder's language."""
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(index_path=INDEX, game_dir=Path(tmp) / "no-game", home=Path(tmp) / "home")
            folder = Path(api.new_mod("Research")["current"])
            page = api.era_unit_page(KEY, "us")
            menu = [c["address"] for c in api._era_research(api._era_built_entry(KEY), SQUAD, page["game_nation"],
                                                             page["factory"], "us")["choices"]]
            self.assertIn(SQUAD, menu)
            before = tree(folder)
            with self.assertRaises(StudioError) as said:
                api.horse_squad_add(page["game_nation"], page["factory"], research_from=SQUAD, group="new")
            expected = (f"Generic Horse can't be researched from {SQUAD}: that unit is in another group of the building "
                        f"than the one picked.")
            self.assertEqual(str(said.exception), expected)
            self.assertEqual(tree(folder), before)
            for lang in OTHERS:
                api.set_pref("lang", lang)
                worded = str(api.page_error(said.exception))
                self.assertNotIn("Generic Horse", worded, lang)
                self.assertNotIn("that unit is in another group", worded, lang)

    def test_its_type_is_the_one_the_units_list_says_for_the_us_rifle_squad(self):
        """The same words as the Units list shows for the unit it's made from, in the Studio's language (the recheck of
        round 1, probe_card.py: equal in all twelve settings; its HTML entities undone the same way, api.units)."""
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(index_path=INDEX, game_dir=Path(tmp) / "no-game", home=Path(tmp) / "home")
            api.new_mod("Types")
            for lang in ("base", *schema.APP_LANGS):
                with self.subTest(lang=lang):
                    rifle = next(u for u in api.units(lang)["units"] if u.get("address") == SQUAD)
                    self.assertTrue(rifle["type"])
                    self.assertEqual([u["card"] for u in api.era_units_list("WWII", lang=lang)["units"]],
                                     [rifle["type"]])
                    self.assertEqual(api.era_unit_page(KEY, lang)["card"], rifle["type"])

    def test_the_page_asks_for_it_in_the_studio_s_language(self):
        js = (UI / "eraunits.js").read_text(encoding="utf-8")
        calls = re.findall(r"api\(\)\.era_units_list\(([^;]*?)\);", js, re.S)
        self.assertTrue(calls)
        self.assertEqual([c for c in calls if not c.rstrip().endswith("state.lang")], [])
        fake = (UI / "fake-api.js").read_text(encoding="utf-8")
        self.assertIn('era_units_list: async (era, kind = "all", nation = -1, search = "", group = "all", lang', fake)
        self.assertIn("card: fakeHorseCard(lang)", fake)


class ResizeAndMoveWithItsFilesGone(WithLibrary):
    """The Horse Squad's two model files are the Studio's own, made in the platform folder's horse_squad/ (the modder
    never had them): with them gone, Resize and Move say its way out, by the page's words in the modder's language;
    another unit's refusal stays "import it again" (its file is the modder's own)."""

    def setUp(self):
        super().setUp()
        self.mod = Path(self.api.new_mod("Gone")["current"])
        entry = self.api._era_built_entry(KEY)
        plan = self.api._era_plan(KEY, None, {}, entry, 0, 10, SQUAD, None, None, None, None, "new")
        self.horse = self.api._era_make(KEY, self.api._era_library()[1], entry, plan, 0, 10, "Generic Horse", 5)[
            "address"]
        self.other = self.api.new_unit(SQUAD, "My Rifles", 5, group="new")["address"]
        self.gone = str(self.home / horse_squad.FOLDER / "horse-squad-rifle.glb")
        for address in (self.horse, self.other):
            model = self.api._own_model_file(address)
            model.parent.mkdir(parents=True, exist_ok=True)
            model.write_bytes(b"glb")
            model.with_suffix(".json").write_text(json.dumps({"from": self.gone, "size": 1.0}), encoding="utf-8")

    def way_out(self, moving: bool) -> str:
        what = "it can't be moved" if moving else "its size can't be changed"
        return (f"The file the Generic Horse's model was made from isn't there any more ({self.gone}), so {what}. To "
                f"have it made again, on its page in the Units tab (WWII+) click Take it out of my mod, then Add to my "
                f"mod: what you changed on it is lost.")

    def test_resize_and_move_say_how_to_have_it_made_again(self):
        w = words()
        for moving, call in ((False, lambda a: self.api.model_resize(a, 1.2)),
                             (True, lambda a: self.api.model_place(a, [10, 0, 0]))):
            with self.subTest(moving=moving):
                with self.assertRaises(StudioError) as said:
                    call(self.horse)
                self.assertEqual(str(said.exception), self.way_out(moving))
                for lang in OTHERS:          # the page's own words for the tab, the era, and the two buttons
                    worded = self.said_in(str(said.exception), lang)
                    for key in ("units_tab", "eras_era_ww2", "eras_take_out", "eras_add"):
                        self.assertIn(w[key][lang], worded, (lang, key))
                    self.assertNotIn("Generic Horse", worded, lang)
                with self.assertRaises(StudioError) as said:                  # another unit: as before
                    call(self.other)
                self.assertIn("import it again", str(said.exception))
        # its heavy-weapon soldier's file gone, the riflemen's there: the same way out
        there = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "rifle.glb"
        there.write_bytes(b"glb")
        model = self.api._own_model_file(self.horse)
        model.with_suffix(".json").write_text(json.dumps({"from": str(there), "size": 1.0}), encoding="utf-8")
        with mock.patch.object(self.api, "_kind_records", return_value=[("bazooka", {"from": self.gone})]):
            for moving, call in ((False, lambda: self.api.model_resize(self.horse, 1.2)),
                                 (True, lambda: self.api.model_place(self.horse, [10, 0, 0]))):
                with self.subTest(moving=moving, kind="bazooka"), self.assertRaises(StudioError) as said:
                    call()
                self.assertEqual(str(said.exception), self.way_out(moving))

    def test_every_ground_unit_says_it_skipped_it_and_why_in_the_studio_s_language(self):
        """The page reads each line's first word ("resized" or "skipped": app.js resizeAllRow, as nations.js reads
        the Nations tab's): the same in every language (translated, the page counted nothing, 0 done and none
        skipped); the reason in the Studio's language."""
        names = {self.horse: "Generic Horse", self.other: "My Rifles"}
        for lang in ("us", "fr", "jpn", "fa"):
            with self.subTest(lang=lang):
                self.api.set_pref("lang", lang)
                try:
                    view = finished(self.api, self.api.models_resize_all("ground", "game")["job"])
                finally:
                    self.api.set_pref("lang", "us")
                self.assertEqual(view["state"], "done")
                lines = dict((ln.split("\t")[1], ln.split("\t")) for ln in view["lines"])
                self.assertEqual(sorted(lines), sorted(names.values()))
                horse = lines["Generic Horse"]
                self.assertEqual(horse[0], "skipped")
                self.assertEqual(lines["My Rifles"][0], "skipped")
                self.assertEqual(horse[2], self.way_out(False) if lang == "us" else errortext.worded(
                    self.way_out(False), lang))
                if lang != "us":
                    self.assertNotIn("Generic Horse", horse[2])
                    self.assertNotIn("import it again", lines["My Rifles"][2])
        for lang in OTHERS:
            self.assertEqual(buildtext.worded("resized\tTiger\t1.2", lang), "resized\tTiger\t1.2")
            self.assertTrue(buildtext.worded("skipped\tTiger\tno real-life size known", lang).startswith(
                "skipped\tTiger\t"), lang)
            self.assertNotEqual(buildtext.worded("skipped\tTiger\tno real-life size known", lang),
                                "skipped\tTiger\tno real-life size known", lang)


if __name__ == "__main__":
    unittest.main()
