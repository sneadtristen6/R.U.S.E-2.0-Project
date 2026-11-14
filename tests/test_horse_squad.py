"""The Horse Squad in the Units tab (ruse_studio.horse_squad; the owner, 2026-11-12, asked whether the Studio should
build it on each player's PC from their own game as a unit anyone can add like the era units, credited to
sneadtristen6: "Yes, like era units"; his order of 2026-11-10: "the cavalry unit we made should become a new unit just in
the studio that's accredited to me").

On the Studio tests' made-up game: listed in WWII+ whether that era is downloaded or not, found by its name in any of the
Studio's languages, off until added (the era units' rule); its page credits its maker and starts from the US rifle squad
only; refused in words, nothing made, without a mod, when this Studio hasn't the builder (rusemod.horsesquad, another
part's: a stand-in builder here, THE CONTRACT's horse_squad_glbs), when the builder can't make it from the game, when
the builder's files aren't where it was asked to put them, and when the mod being edited changed during the build; a
failure once its unit is made takes the unit out again; its credit line beside the era units' (credits_text); the mod
it's being made in can't be switched away from or deleted meanwhile.

With RUSE_GAME naming the game (and the Studio's game index, RUSE_STUDIO_INDEX, and the two horse-and-rider files of the
copy that passed in the game, RUSE_HORSE_SQUAD_GLBS: their defaults are this PC's), adding it gives the mod the same
files, byte for byte, as the horse-studio2 copy's own calls give with the same two files
(scratch/animmodels/horse-studio/make_horse_studio2_test.py: new_unit from the US rifle squad, Import model of the
riflemen's file, Import model of the heavy-weapon soldier's for his kind), the model records' "from" (the file each was
made from: the platform folder's copy here) aside, and its era_units.json and credit line besides; taking it out
removes the unit, both its models and their animations, and its credit line."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock

from test_studio import WithMod
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits

KEY, SQUAD = horse_squad.KEY, horse_squad.SQUAD
GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
INDEX = Path(os.environ.get("RUSE_STUDIO_INDEX") or "D:/RUSE-2.0/scratch/modelgaps/game-index.sqlite")
GLBS = Path(os.environ.get("RUSE_HORSE_SQUAD_GLBS") or "D:/RUSE-2.0/scratch/animmodels/fixes3")
RIFLE, HEAVY = GLBS / "horse-squad-rifle-death.glb", GLBS / "horse-squad-bazooka-death.glb"


def stand_in(rifle: Path, heavy: Path, refuse: str | None = None, asked=None, during=None, where=None):
    """A stand-in for rusemod.horsesquad (THE CONTRACT): horse_squad_glbs(game, out, *, index=None, say=print) copies
    `rifle` and `heavy` into `out` and returns {"rifle", "bazooka"} paths; `refuse`: raises HorseSquadError(refuse)
    instead; `asked`: a list each call's arguments go into; `during`: run while it builds; `where`: the folder its files
    go in instead of `out` (a builder that didn't do as asked)."""
    module = types.ModuleType("rusemod.horsesquad")

    class HorseSquadError(Exception):
        pass

    def horse_squad_glbs(game, out, *, index=None, say=print):
        if asked is not None:
            asked.append({"game": Path(game), "out": Path(out), "index": index})
        if during is not None:
            during()
        if refuse:
            raise HorseSquadError(refuse)
        into = Path(where or out)
        into.mkdir(parents=True, exist_ok=True)
        got = {}
        for role, src in (("rifle", rifle), ("bazooka", heavy)):
            got[role] = into / Path(src).name
            shutil.copyfile(src, got[role])
        say("made")
        return got

    module.HorseSquadError = HorseSquadError
    module.horse_squad_glbs = horse_squad_glbs
    return module


def finished(api, job: str, most: float = 1800) -> dict:
    """The job's view once it has ended, every line with it."""
    end = time.monotonic() + most
    while time.monotonic() < end:
        view = api.job(job)
        if view["state"] != "running":
            return view
        time.sleep(0.1)
    raise AssertionError(f"job {job} still running after {most} s")


def tree(folder: Path) -> dict:
    """{path inside `folder`: its bytes} of every file in it."""
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}


class OnTheMadeUpGame(WithMod):
    def setUp(self):
        super().setUp()
        lib = Path(tempfile.mkdtemp(dir=self.tmp.name))     # an era units library with nothing of WWII+ in it
        (lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": [
            {"key": "WWI|USA|Mark VIII Liberty", "era": "WWI", "nation": "USA", "name": "Mark VIII Liberty",
             "in_place_of": "", "card": "Heavy Tank", "building": "Armor base",
             "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman", "copies_name": "", "game_nation": 0,
             "factory": 10, "aircraft": False, "model": None, "fits": True, "picture": None,
             "credit": {"title": "Liberty model", "author": "maker", "licence": "CC-BY 4.0",
                        "url": "https://example.org/Liberty", "extra": ""}}]}), encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.files = Path(tempfile.mkdtemp(dir=self.tmp.name))   # two small files the stand-in builder hands over
        self.rifle, self.heavy = self.files / "rifle.glb", self.files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def builder(self, **kw):
        return mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy, **kw)})

    def test_listed_in_wwii_downloaded_or_not_and_off_until_added(self):
        got = self.api.era_units_list("WWII")
        self.assertEqual((got["installed"], got["library"]), (False, True))      # WWII+ isn't downloaded here
        self.assertEqual([(u["key"], u["name"], u["built"], u["by"], u["added"], u["code"], u["kind"])
                          for u in got["units"]], [(KEY, "Generic Horse", True, "sneadtristen6", None, 0, "ground")])
        self.assertEqual(self.api.era_units_list("WWI")["units"][0]["built"], False)   # an era unit's row as before
        self.assertNotIn(KEY, [u["key"] for u in self.api.era_units_list("WWI")["units"]])
        for kind, nation, search, listed in (("air", -1, "", []), ("all", 1, "", []), ("ground", 0, "", [KEY]),
                                             ("all", -1, "horse", [KEY]), ("all", -1, "cheval", [KEY]),
                                             ("all", -1, "騎馬", [KEY]), ("all", -1, "tank", [])):
            with self.subTest(kind=kind, nation=nation, search=search):
                self.assertEqual([u["key"] for u in self.api.era_units_list("WWII", kind, nation, search)["units"]],
                                 listed)
        # nothing of it in a mod until a modder adds it
        folder = Path(self.api.new_mod("Plain")["current"])
        self.assertIsNone(self.api.era_units_list("WWII")["units"][0]["added"])
        self.assertFalse((folder / era_units.INDEX).exists())
        self.assertFalse((folder / era_units.CREDITS).exists())

    def test_its_page_credits_its_maker_and_starts_from_the_rifle_squad_only(self):
        page = self.api.era_unit_page(KEY, "us")
        self.assertEqual((page["name"], page["built"], page["credit"], page["added"], page["has_model"],
                          page["building"]), ("Generic Horse", True, {"author": "sneadtristen6"}, None, False, None))
        self.assertEqual([s["address"] for s in page["start"]], [SQUAD])
        self.assertEqual((page["era"], page["nation"], page["copies"]), ("WWII", "USA", SQUAD))
        # another start unit asked for is never taken: its models are made for that unit's soldiers
        start = self.api.era_unit_start(KEY, "$/GFX/Everything/Descriptor_Unit_M4_Sherman", 0, 10)
        self.assertEqual(start["price"], self.api.era_start_price(SQUAD)["price"])
        with self.assertRaises(StudioError):
            self.api.era_unit_add(KEY, 0, 10)          # never added the era units' way, without its models

    def test_refused_without_a_mod_and_without_the_builder(self):
        with self.builder(), self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
            self.api.horse_squad_add(0, 10, group="new")
        folder = Path(self.api.new_mod("No builder")["current"])
        before = tree(folder)
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: None}), self.assertRaises(StudioError) as said:
            self.api.horse_squad_add(0, 10, group="new")
        self.assertEqual(str(said.exception), "This Studio can't make the Generic Horse yet: the part that makes it "
                                              "from your game isn't in it.")
        self.assertEqual(tree(folder), before)
        self.assertFalse((self.home / horse_squad.FOLDER).exists())

    def test_refused_in_words_when_the_builder_cant_make_it(self):
        folder = Path(self.api.new_mod("Refused")["current"])
        before, asked = tree(folder), []
        with self.builder(refuse="Your game has no horse the Studio can read.", asked=asked):
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Generic Horse", 5, group="new")["job"])
        self.assertEqual((view["state"], view["message"], view["lines"]),
                         ("failed", "The Generic Horse can't be made from your game: Your game has no horse the Studio "
                                    "can read.", ["build"]))
        self.assertEqual(tree(folder), before)                                  # nothing made
        self.assertEqual(os.listdir(self.home / horse_squad.FOLDER), [])        # nothing left of the build
        self.assertEqual((asked[0]["game"], asked[0]["index"]), (self.game, self.index))
        # in the Studio's language, the builder's own words kept as they came
        self.api.set_pref("lang", "fr")
        self.assertEqual(self.api.job(view["id"])["message"], "L'Escouade à cheval générique ne peut pas être fabriquée à partir "
                                                              "de votre jeu : Your game has no horse the Studio can read.")

    def test_files_not_made_where_the_builder_was_asked_are_refused(self):
        folder = Path(self.api.new_mod("Elsewhere")["current"])
        before = tree(folder)
        away = Path(tempfile.mkdtemp(dir=self.tmp.name))
        with self.builder(where=away):
            view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
        self.assertEqual((view["state"], view["message"]), (
            "failed", "The Generic Horse can't be made from your game: its two model files didn't come out. Please "
                      "report this."))
        self.assertEqual(sorted(os.listdir(away)), ["heavy.glb", "rifle.glb"])  # never moved from where they are
        self.assertEqual(tree(folder), before)

    def test_a_failure_once_its_unit_is_made_takes_it_out_again(self):
        """The made-up game has no models to fit to, so its riflemen's import fails after the unit is made: the unit,
        its record and its credit line go again, the mod as it was."""
        folder = Path(self.api.new_mod("Half")["current"])
        before = tree(folder)
        with self.builder():
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Generic Horse", 5, group="new")["job"])
        self.assertEqual(view["state"], "failed")
        self.assertEqual(view["lines"], ["build", "unit", "riflemen"])
        self.assertEqual(view["message"], "The unit this one copies has no 3D model to fit a new one to.")
        self.assertNotIn("Generic Horse", [u["name"] for u in self.api.units()["units"] if u.get("new")])
        self.assertEqual(ModEdits(folder).new_units, {})
        # what's left: its record emptied, and the Studio's own changes file with no change in it (as Delete leaves it)
        after = tree(folder)
        self.assertEqual(json.loads(after.pop(era_units.INDEX)), {})
        self.assertEqual([ln for ln in after.pop("src/studio.rndf").decode("utf-8").splitlines()
                          if ln.strip() and not ln.startswith("//")], [])
        self.assertEqual(after, before)
        # the builder's two files are kept where the mod's model records would name them
        self.assertEqual(sorted(os.listdir(self.home / horse_squad.FOLDER)), ["heavy.glb", "rifle.glb"])

    def test_added_and_taken_out_with_its_credit_line(self):
        """Its models' import stood in for (the made-up game has none to fit to; the game's own run is
        OnTheGame's): the unit, its era_units.json and its credit line in, then out again."""
        folder = Path(self.api.new_mod("In and out")["current"])
        imports = []
        with self.builder(), mock.patch.object(StudioApi, "model_import",
                                               lambda api, address, file, **kw: imports.append((file, kw))), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Cavalry", 7, group="new")["job"])
        self.assertEqual((view["state"], view["lines"]), ("done", ["build", "unit", "riflemen", "bazooka"]))
        made = view["result"]
        self.assertEqual(made["name"], "Cavalry")
        self.assertEqual(imports, [(str(self.home / horse_squad.FOLDER / "rifle.glb"), {}),
                                   (str(self.home / horse_squad.FOLDER / "heavy.glb"), {"kind": "bazooka"})])
        units = {u["address"]: u for u in self.api.units()["units"]}
        self.assertEqual((units[made["address"]]["new"], units[made["address"]]["source"]), (True, SQUAD))
        self.assertEqual(json.loads((folder / era_units.INDEX).read_text(encoding="utf-8")), {KEY: made["address"]})
        self.assertEqual((folder / era_units.CREDITS).read_text(encoding="utf-8"),
                         "# Made for RUSE 2.0\n\n- Generic Horse (WWII, USA): by sneadtristen6.\n")
        self.assertEqual(self.api.era_units_list("WWII")["units"][0]["added"], made["address"])
        self.assertEqual(self.api.era_unit_page(KEY)["added"], made["address"])
        with self.builder(), self.assertRaisesRegex(StudioError, "already in this mod"):
            self.api.horse_squad_add(0, 10, group="new")
        # beside an era unit: both credited, each in its own part of the file
        liberty = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)
        credits = (folder / era_units.CREDITS).read_text(encoding="utf-8")
        self.assertTrue(credits.startswith("# Era unit models\n"), credits)
        self.assertTrue(credits.endswith('- Mark VIII Liberty (WWI, USA): "Liberty model" by maker, CC-BY 4.0, '
                                         'https://example.org/Liberty.\n\n# Made for RUSE 2.0\n\n'
                                         '- Generic Horse (WWII, USA): by sneadtristen6.\n'), credits)
        out = self.api.era_unit_remove(KEY)
        self.assertEqual(out["removed"], made["address"])
        self.assertNotIn(made["address"], {u["address"] for u in self.api.units()["units"]})
        self.assertNotIn("Generic Horse", (folder / era_units.CREDITS).read_text(encoding="utf-8"))
        self.assertEqual(json.loads((folder / era_units.INDEX).read_text(encoding="utf-8")),
                         {"WWI|USA|Mark VIII Liberty": liberty["address"]})
        self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
        self.assertFalse((folder / era_units.CREDITS).exists())

    def test_a_horse_squad_the_mod_has_already_is_never_taken_out(self):
        """Another one put in the mod while this one's files were made (another window, say): this one is refused when
        its unit would be made, and the one there stays, its unit, record and credit line."""
        folder = Path(self.api.new_mod("Kept")["current"])
        other = {}

        def meanwhile():
            entry = self.api._era_built_entry(KEY)
            plan = self.api._era_plan(KEY, None, {}, entry, 0, 10, SQUAD, None, None, None, None, "new")
            other.update(self.api._era_make(KEY, self.api._era_library()[1], entry, plan, 0, 10, "Kept", 5))

        with self.builder(during=meanwhile):
            view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
        self.assertEqual((view["state"], view["message"]), ("failed", "Generic Horse is already in this mod"))
        self.assertEqual(json.loads((folder / era_units.INDEX).read_text(encoding="utf-8")), {KEY: other["address"]})
        self.assertIn(other["address"], ModEdits(folder).new_units)
        self.assertIn("sneadtristen6", (folder / era_units.CREDITS).read_text(encoding="utf-8"))

    def test_a_name_taken_is_refused_before_the_build(self):
        self.api.new_mod("Taken")
        self.api.new_unit("$/GFX/Everything/Descriptor_Unit_M4_Sherman", "Generic Horse", 5, group="new")
        asked = []
        with self.builder(asked=asked), self.assertRaisesRegex(StudioError, "There's already a unit called "
                                                                            "Descriptor_Unit_Generic_Horse"):
            self.api.horse_squad_add(0, 10, "Generic Horse", group="new")
        self.assertEqual(asked, [])

    def test_the_mod_changed_during_the_build(self):
        first = Path(self.api.new_mod("First")["current"])
        second = Path(self.api.new_mod("Second")["current"])
        self.api.choose_mod(str(first))
        before = (tree(first), tree(second))
        with self.builder(during=lambda: self.api.choose_mod(str(second))):
            view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
        self.assertEqual((view["state"], view["message"]), (
            "failed", "The mod being edited changed while the Generic Horse was being made, so it wasn't added: add it "
                      "again."))
        self.assertEqual((tree(first), tree(second)), before)

    def test_its_mod_stays_the_one_edited_while_its_unit_is_made(self):
        first = Path(self.api.new_mod("Busy")["current"])
        other = Path(self.api.new_mod("Other")["current"])
        self.api.choose_mod(str(first))
        self.api.__dict__["_horse_mod"] = first        # (as horse_squad_add sets it while the unit is made)
        try:
            for call in (lambda: self.api.choose_mod(str(other)), lambda: self.api.new_mod("Third"),
                         lambda: self.api.delete_mod(str(first)), lambda: self.api.forget_mod(str(first))):
                with self.assertRaisesRegex(StudioError, "The Generic Horse is being added to this mod"):
                    call()
            self.api.choose_mod(str(first))           # the same mod again: nothing changes
            self.api.forget_mod(str(other))            # another mod: as always
        finally:
            self.api.__dict__["_horse_mod"] = None
        self.api.choose_mod(str(other))

    def test_a_second_ask_follows_the_first(self):
        self.api.new_mod("Twice")
        go = threading.Event()
        with self.builder(during=lambda: go.wait(60)):
            first = self.api.horse_squad_add(0, 10, group="new")["job"]
            try:
                self.assertEqual(self.api.horse_squad_add(0, 10, group="new")["job"], first)
                self.assertEqual(self.api.era_unit_page(KEY)["building"], first)
                with self.assertRaisesRegex(StudioError, "The Generic Horse is being added to this mod"):
                    self.api.era_unit_remove(KEY)          # (taken out only once that's done)
            finally:
                go.set()
            finished(self.api, first)
        self.assertIsNone(self.api.era_unit_page(KEY)["building"])


class ThePageAndItsHelp(unittest.TestCase):
    """The page's own words (eraunits.js, words.toml eras_horse_*, tip_eras_horse_*) and the help page's Horse Squad
    section in each of the eleven languages, naming what the page shows in bold as the page says it there."""
    UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
    PAGES = {"us": "Units-From-Other-Eras", "fr": "fr/Unités-des-autres-époques",
             "ger": "ger/Einheiten-aus-anderen-Epochen", "ita": "ita/Unità-di-altre-epoche",
             "spa": "spa/Unidades-de-otras-épocas", "pol": "pol/Jednostki-z-innych-epok", "ru": "ru/Юниты-других-эпох",
             "cz": "cz/Jednotky-z-jiných-období", "jpn": "jpn/他の時代のユニット", "sc": "sc/其他时代的单位",
             "fa": "fa/یگان‌های-دوره‌های-دیگر"}
    NAMED = ("eras_era_ww2", "eras_horse_name", "eras_start_from", "build_menu", "eras_group", "eras_research_from",
             "eras_add", "eras_open_page", "eras_take_out", "model_import")

    def test_its_words_are_used_and_word_for_word_on_the_stand_in_page(self):
        import re
        from ruse_studio.api import _words
        js, fake = (self.UI / "eraunits.js").read_text(encoding="utf-8"), (self.UI / "fake-api.js").read_text(encoding="utf-8")
        own = sorted(k for k in _words() if re.fullmatch(r"(tip_)?eras_horse_\w+", k))
        self.assertEqual(len(own), 11)
        steps = re.search(r"const HORSE_STEPS = \{(.*?)\};", js, re.S).group(1)
        self.assertEqual(sorted(re.findall(r'(\w+): "', steps)), sorted(horse_squad.STEPS))   # every step of the job
        for key in own:
            with self.subTest(key=key):
                self.assertIn(key, js)                                          # none left behind
                self.assertIn(f'"{key}": {json.dumps(_words()[key]["us"], ensure_ascii=False)}', fake)
        self.assertIn("horse_squad_add: async", fake)
        self.assertIn("api().horse_squad_add(", js)

    def test_the_help_names_the_page_s_words_in_every_language(self):
        import re
        import tomllib
        wiki = self.UI.parents[2] / "docs" / "wiki"
        words = tomllib.loads((self.UI.parent / "words.toml").read_text(encoding="utf-8"))
        for lang, page in self.PAGES.items():
            text = (wiki / f"{page}.md").read_text(encoding="utf-8")
            # its own section: from the heading naming it, to the next
            heads = [m.start() for m in re.finditer(r"^## .*$", text, re.M) if words["eras_horse_name"][lang] in m.group(0)]
            self.assertEqual(len(heads), 1, lang)
            end = text.find("\n## ", heads[0] + 3)
            part = text[heads[0]:end if end > 0 else len(text)]
            for key in self.NAMED:
                with self.subTest(lang=lang, key=key):
                    self.assertIn(f"**{words[key][lang]}**", part)
            self.assertIn("sneadtristen6", part)
            self.assertIn("`CREDITS-era-units.md`", part)


class Credits(unittest.TestCase):
    ERA = {"key": "WWI|USA|A", "era": "WWI", "nation": "USA", "name": "A",
           "credit": {"title": "A model", "author": "maker", "licence": "CC0", "url": "https://example.org/a"}}

    def test_era_units_alone_as_before(self):
        self.assertEqual(era_units.credits_text([self.ERA]),
                         "# Era unit models\n\nThese units use free 3D models by their makers, under the licence named. "
                         "Changes: fitted to the game (turned, scaled) and the unit's nation's markings added (older "
                         "markings covered).\n\n- A (WWI, USA): \"A model\" by maker, CC0, https://example.org/a.\n")

    def test_the_horse_squad_by_its_maker(self):
        self.assertEqual(era_units.credits_text([horse_squad.ENTRY]),
                         "# Made for RUSE 2.0\n\n- Generic Horse (WWII, USA): by sneadtristen6.\n")
        both = era_units.credits_text([horse_squad.ENTRY, self.ERA])
        self.assertTrue(both.endswith("https://example.org/a.\n\n# Made for RUSE 2.0\n\n- Generic Horse (WWII, USA): "
                                      "by sneadtristen6.\n"), both)


@unittest.skipUnless(GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file(),
                     "RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of "
                     "the copy that passed in the game aren't there")
class OnTheGame(unittest.TestCase):
    """The game's own US rifle squad and the two files of the horse-studio2 copy that passed in the game."""

    def test_the_mod_files_of_the_copy_that_passed_and_out_again(self):
        home = Path(tempfile.mkdtemp(prefix="horse-squad-test-"))
        self.addCleanup(shutil.rmtree, home, True)
        api = StudioApi(index_path=INDEX, game_dir=GAME, home=home)
        # the copy's own calls (make_horse_studio2_test.py), in a mod of their own
        one = Path(api.new_mod("By hand")["current"])
        unit = api.new_unit(SQUAD, "Generic Horse", 5, group="new")["address"]
        api.model_import(unit, str(RIFLE))
        api.model_import(unit, str(HEAVY), kind="bazooka")
        # the Units tab's Add to my mod, in another, its builder standing in with the same two files
        two = Path(api.new_mod("Added")["current"])
        fresh = tree(two)
        asked = []
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY, asked=asked)}):
            view = finished(api, api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual((view["state"], view["message"]), ("done", "Generic Horse is in your mod."))
        self.assertEqual(view["lines"], ["build", "unit", "riflemen", "bazooka"])
        self.assertEqual(view["result"], {"address": unit, "name": "Generic Horse"})
        self.assertEqual((asked[0]["game"], asked[0]["index"]), (GAME, INDEX))
        kept = home / horse_squad.FOLDER
        self.assertEqual(sorted(os.listdir(kept)), sorted([RIFLE.name, HEAVY.name]))     # no folder of the build left
        self.assertEqual(((kept / RIFLE.name).read_bytes(), (kept / HEAVY.name).read_bytes()),
                         (RIFLE.read_bytes(), HEAVY.read_bytes()))
        by_hand, added = tree(one), tree(two)
        # its own files besides: the record of the era units it has and its credit line
        self.assertEqual(json.loads(added.pop(era_units.INDEX)), {KEY: unit})
        self.assertEqual(added.pop(era_units.CREDITS).decode("utf-8").replace("\r\n", "\n"),   # (as read_text reads it)
                         "# Made for RUSE 2.0\n\n- Generic Horse (WWII, USA): by sneadtristen6.\n")
        by_hand.pop("mod.toml"), added.pop("mod.toml")       # (each mod's own name, from new_mod)
        self.assertEqual(sorted(added), sorted(by_hand))
        tail = unit.rsplit("/", 1)[-1]
        self.assertIn(f"files/models/{tail}.glb", added)
        self.assertIn(f"files/models/{tail}@bazooka.glb", added)
        differ = {}
        for name in sorted(by_hand):
            if added[name] == by_hand[name]:
                continue
            if name.endswith(".json"):   # a model's record: the file it was made from is named in it
                a, b = json.loads(by_hand[name]), json.loads(added[name])
                froms = (a.pop("from", None), b.pop("from", None))
                if a == b and Path(froms[0]).name == Path(froms[1]).name and Path(froms[1]).parent == kept:
                    continue
            differ[name] = (len(by_hand[name]), len(added[name]))
        self.assertEqual(differ, {})
        rows = {r["kind"]: r for r in api.look(unit)["kinds"]}
        self.assertEqual((rows["fusilier"]["skeleton"], rows["bazooka"]["own"], rows["bazooka"]["same_bones"]),
                         ("own", True, True))
        # taken out again: the unit, both its models and their animations, its credit line
        out = api.era_unit_remove(KEY)
        self.assertEqual(out["removed"], unit)
        self.assertNotIn(unit, {u["address"] for u in api.units()["units"] if u.get("new")})
        left = tree(two)
        self.assertEqual(json.loads(left.pop(era_units.INDEX)), {})
        self.assertNotIn(era_units.CREDITS, left)
        self.assertEqual([n for n in left if tail in n], [])
        self.assertEqual(ModEdits(two).new_units, {})
        # what's left: the Studio's own changes file with no change in it (as Delete leaves it), the mod as it was
        self.assertEqual([ln for ln in left.pop("src/studio.rndf").decode("utf-8").splitlines()
                          if ln.strip() and not ln.startswith("//")], [])
        self.assertEqual(left, fresh)


GERMAN = "$/GFX/Everything/Descriptor_Unit_Soldat_Allemand_Leger"


@unittest.skipUnless(GAME is not None and GAME.is_dir() and INDEX.is_file(),
                     "RUSE_GAME names no game folder, or the Studio's game index isn't there")
class ItsCountry(unittest.TestCase):
    """The country it is from (the owner, 2026-11-13: "generic horse should be fully editable so people can change
    what countmry its from"): Add to my mod with another country's rifle squad picked in Start from, through the REAL
    builder (rusemod.horsesquad), on the game and the Studio's index (both only read)."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="horse-country-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home)

    def test_its_page_offers_each_country_s_rifle_squad_the_us_one_first(self):
        page = self.api.era_unit_page(KEY, "us")
        self.assertEqual([s["address"] for s in page["start"]], list(horse_squad.SQUADS))
        self.assertEqual([s["country"] for s in page["start"]], ["USA", "Germany", "UK", "France"])
        self.assertEqual([s["suggested"] for s in page["start"]], [True, False, False, False])
        price = self.api.era_unit_start(KEY, GERMAN, 1, 8, "us")["price"]
        self.assertEqual(price, self.api._era_price(GERMAN))        # (its values: the German rifle squad's)

    def test_a_german_horse_has_german_riders_its_own_files_and_its_country_in_its_credit(self):
        mod = Path(self.api.new_mod("Kavallerie")["current"])
        view = finished(self.api, self.api.horse_squad_add(1, 8, "Reiter", 5, None, None, None, "new",
                                                           source=GERMAN)["job"])
        self.assertEqual((view["state"], view["message"]), ("done", "Generic Horse is in your mod."))
        unit = view["result"]["address"]
        self.assertEqual(ModEdits(mod).new_units[unit].source, GERMAN)
        kept = self.home / horse_squad.FOLDER
        self.assertEqual(sorted(os.listdir(kept)), ["horse-squad-ger-bazooka.glb", "horse-squad-ger-rifle.glb"])
        tail = unit.rsplit("/", 1)[-1]
        for stem, made in ((tail, "horse-squad-ger-rifle.glb"), (f"{tail}@bazooka", "horse-squad-ger-bazooka.glb")):
            record = json.loads((mod / "files" / "models" / f"{stem}.json").read_text(encoding="utf-8"))
            self.assertEqual((record["from"], record["skeleton"]), (str(kept / made), "own"))
        rows = {r["kind"]: r for r in self.api.look(unit)["kinds"]}
        self.assertEqual((rows["fusilier"]["skeleton"], rows["bazooka"]["own"], rows["bazooka"]["same_bones"]),
                         ("own", True, True))
        self.assertIn("- Generic Horse (WWII, Germany): by sneadtristen6.",
                      (mod / era_units.CREDITS).read_text(encoding="utf-8"))
        out = self.api.era_unit_remove(KEY)                         # (taken out as any Generic Horse is)
        self.assertEqual(out["removed"], unit)
        self.assertNotIn(era_units.CREDITS, os.listdir(mod))

    def test_a_squad_it_isnt_made_from_is_refused_before_anything(self):
        mod = Path(self.api.new_mod("Cavalleria")["current"])
        before = tree(mod)
        with self.assertRaisesRegex(StudioError, "The Generic Horse's riders are made from one of these rifle squads"):
            self.api.horse_squad_add(4, 8, "Cavalli", 5, None, None, None, "new",
                                     source="$/GFX/Everything/Descriptor_Unit_Soldat_ITA_Leger")
        self.assertEqual(tree(mod), before)
        self.assertFalse((self.home / horse_squad.FOLDER).exists())


if __name__ == "__main__":
    unittest.main()
