"""The mend of the one check's findings 1, 6 and 8 (Take a unit out, all or nothing; 2026-11-13).

- 1: Take it out of my mod (era_units.era_unit_remove) or the unit page's Delete (api.delete_unit -> edits.remove_unit)
  while another program holds a file of the unit (units.toml, a clip, a model, era_units.json, the credits): the mod
  stays as it was, byte for byte, the modder is told which file and what to do, and trying again once the file is free
  takes the unit out whole. A mod an older Studio left half deleted (rows in units.toml, a clips' folder, a model's
  copy for a unit it hasn't): the build says what to do, Test in game's log offers to take the leftovers out
  (era_units._leftovers_problem / leftovers_fix), Delete and Take it out tried again take them; never a unit the mod or
  the game has.
- 6: era_units.json or the credits file held at the end of the take-out: nothing goes (all or nothing, as 1).
- 8: a mod whose era unit was deleted before this mend (its record line and CC-BY credit line left): the next save of
  the era files and Export (era_units._era_tidy) take those lines out, every line of a unit the mod has and every era
  credit line this PC's library can't name kept; a mod with nothing stale is left byte for byte.

Most of it on the Studio tests' made-up game (WithMod) or a bare mod folder; HeldOnTheGame on the game with the Horse
Squad, as tests/test_check_words.py's ItsAnimationsFileHeld (skipped without it). Holds are Windows' (open handles)."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules)

from test_export_out import LIBERTY, LIBERTY_LINE, era_library
from test_horse_squad import GAME, HEAVY, INDEX, RIFLE, finished, stand_in
from test_studio import WithMod
from rusemod import anim, buildtext
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits

TAKING_OUT = ".taking-out"   # (edits.TAKING_OUT: written here, so this file runs on the code before the mend too)


def unit_files(mod: Path, tail: str) -> list:
    """Every file of the unit `tail` in the mod, listed here on its own (not the code's list): its card, models,
    records, squad file, copy, kinds' and soldiers' files, building look, clips' folder."""
    models = mod / "files" / "models"
    out = [mod / "files" / "cards" / f"{tail}.png", mod / "files" / "buildings" / tail, mod / anim.OWN / tail]
    out += [models / f"{tail}{s}" for s in (".glb", ".json", ".squad.toml", ".copy.toml")]
    out += list(models.glob(f"{tail}@*")) if models.is_dir() else []
    return sorted(str(p.relative_to(mod)) for p in out if p.exists())


try:
    import msvcrt
except ImportError:
    msvcrt = None

WINDOWS = os.name == "nt"
UNIT = "$/GFX/Everything/Descriptor_Unit_Lancer"
OTHER = "$/GFX/Everything/Descriptor_Unit_Keeper"
SOURCE = "$/GFX/Everything/Descriptor_Unit_M4_Sherman"
OTHER_TANK = "WWI|USA|Whippet Copy"
OTHER_LINE = '- Whippet Copy (WWI, USA): "Whippet model" by maker, CC-BY 4.0, https://example.org/Whippet.'
HAND_LINE = "- Old Tank (WWI, GBR): by someone, CC-BY 4.0, https://example.org/old."


def tree(folder: Path) -> dict:
    """Every file under `folder`: {its path in it: its bytes}."""
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in Path(folder).rglob("*") if p.is_file()}


def rows_for(mod: Path, tails) -> None:
    """units.toml with a row and a clip file of its own for each unit in `tails`."""
    lines = []
    for t in tails:
        lines += [f"[unit.{t}.action]", 't_stand = "stand.baf"', ""]
        own = mod / anim.OWN / t
        own.mkdir(parents=True, exist_ok=True)
        (own / "stand.baf").write_bytes(b"clip of " + t.encode())
    (mod / anim.UNITS).parent.mkdir(parents=True, exist_ok=True)
    (mod / anim.UNITS).write_text("\n".join(lines), encoding="utf-8")


def every_file(mod: Path, tail: str) -> None:
    """The unit `tail`'s own files, every kind Delete takes."""
    models = mod / "files" / "models"
    models.mkdir(parents=True, exist_ok=True)
    (mod / "files" / "cards").mkdir(parents=True, exist_ok=True)
    (mod / "files" / "cards" / f"{tail}.png").write_bytes(b"card")
    for name in (f"{tail}.glb", f"{tail}.json", f"{tail}.squad.toml", f"{tail}@bazooka.glb", f"{tail}@bazooka.json",
                 f"{tail}@2.json", f"{tail}.copy.toml"):
        (models / name).write_bytes(b"of " + name.encode())
    look = mod / "files" / "buildings" / tail          # (a new building's own look)
    look.mkdir(parents=True, exist_ok=True)
    (look / "building.toml").write_bytes(b"# look of " + tail.encode())


def two_tank_library(folder: Path) -> Path:
    """era_library's with a second WWI unit."""
    era_library(folder)
    f = folder / "era_units.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    second = dict(doc["units"][0], key=OTHER_TANK, name="Whippet Copy",
                  credit={"title": "Whippet model", "author": "maker", "licence": "CC-BY 4.0",
                          "url": "https://example.org/Whippet", "extra": ""})
    doc["units"].append(second)
    f.write_text(json.dumps(doc), encoding="utf-8")
    return folder


class RemoveUnit(unittest.TestCase):
    """edits.ModEdits.remove_unit on a bare mod folder: every file of the unit, all or nothing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("RUSE_TEST_TMP") or None)
        self.addCleanup(self.tmp.cleanup)
        self.mod = Path(self.tmp.name) / "mod"
        self.mod.mkdir()
        edits = ModEdits(self.mod)
        edits.add_unit(UNIT, SOURCE, "Lancer", {"ProductionPrice": 100})
        edits.add_unit(OTHER, SOURCE, "Keeper", {})
        self.tail, self.other = UNIT.rsplit("/", 1)[-1], OTHER.rsplit("/", 1)[-1]
        every_file(self.mod, self.tail)
        every_file(self.mod, self.other)
        rows_for(self.mod, [self.tail, self.other])
        self.before = tree(self.mod)

    def gone_whole(self):
        self.assertNotIn(UNIT, ModEdits(self.mod).new_units)
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertNotIn(self.tail, anim.read_units(self.mod))
        self.assertFalse((self.mod / TAKING_OUT).exists())
        # the other unit's all kept, byte for byte
        self.assertIn(OTHER, ModEdits(self.mod).new_units)
        self.assertIn(self.other, anim.read_units(self.mod))
        now = tree(self.mod)
        for name, data in self.before.items():
            if self.other in name and self.tail not in name:
                self.assertEqual(now.get(name), data, name)

    def test_every_file_goes_with_the_unit_and_the_other_unit_s_stay(self):
        ModEdits(self.mod).remove_unit(UNIT)
        self.gone_whole()

    def test_its_own_copy_of_the_model_goes_too(self):
        """A squad's Custom uniform (<unit>.copy.toml): left behind, it stopped every build ("no mod in the set makes a
        unit ..."); before this mend Delete left it."""
        copy = self.mod / "files" / "models" / f"{self.tail}.copy.toml"
        self.assertTrue(copy.is_file())
        ModEdits(self.mod).remove_unit(UNIT)
        self.assertFalse(copy.exists())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_held_model_file_leaves_the_mod_as_it_was_and_trying_again_works(self):
        held = open(self.mod / "files" / "models" / f"{self.tail}@bazooka.glb", "rb")
        try:
            with self.assertRaises(OSError):
                ModEdits(self.mod).remove_unit(UNIT)
        finally:
            held.close()
        self.assertEqual(tree(self.mod), self.before)
        self.assertFalse((self.mod / TAKING_OUT).exists())
        ModEdits(self.mod).remove_unit(UNIT)
        self.gone_whole()

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_held_clip_leaves_the_mod_as_it_was(self):
        held = open(self.mod / anim.OWN / self.tail / "stand.baf", "rb")
        try:
            with self.assertRaises(OSError):
                ModEdits(self.mod).remove_unit(UNIT)
        finally:
            held.close()
        self.assertEqual(tree(self.mod), self.before)

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_held_units_toml_leaves_the_mod_as_it_was_with_no_half_file_beside_it(self):
        held = open(self.mod / anim.UNITS, "rb")
        try:
            with self.assertRaises(OSError):
                ModEdits(self.mod).remove_unit(UNIT)
        finally:
            held.close()
        self.assertEqual(tree(self.mod), self.before)   # (no units.part left either)
        ModEdits(self.mod).remove_unit(UNIT)
        self.gone_whole()

    def test_a_units_toml_with_a_mistake_leaves_the_mod_as_it_was(self):
        (self.mod / anim.UNITS).write_text("[unit.\n", encoding="utf-8")
        before = tree(self.mod)
        with self.assertRaises(anim.AnimError):
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertEqual(tree(self.mod), before)

    def test_a_save_that_fails_puts_every_file_back(self):
        edits = ModEdits(self.mod)
        with mock.patch.object(ModEdits, "_write", side_effect=OSError(28, "No space left on device")):
            with self.assertRaises(OSError):
                edits.remove_unit(UNIT)
        self.assertEqual(tree(self.mod), self.before)
        self.assertIn(UNIT, edits.new_units)                 # (and in memory)
        self.assertIn((UNIT, "ProductionPrice", ""), edits.edits)

    def test_an_ammunition_copy_goes_without_reading_units_toml(self):
        """A copy named False (an ammunition) never has animations: a units.toml that can't be read doesn't stop it."""
        edits = ModEdits(self.mod)
        ammo = "$/GFX/Everything/Ammo_Range_Lancer_1"
        edits.add_unit(ammo, "$/GFX/Everything/Ammo_X", "range", {}, named=False)
        (self.mod / anim.UNITS).write_text("[unit.\n", encoding="utf-8")
        ModEdits(self.mod).remove_unit(ammo)
        self.assertNotIn(ammo, ModEdits(self.mod).new_units)

    def test_leftovers_of_a_unit_the_mod_hasnt(self):
        edits = ModEdits(self.mod)
        edits.new_units.pop(UNIT)          # (as a Delete that stopped half way left it: the unit gone, its files not)
        edits.save()
        before = tree(self.mod)
        gone = ModEdits(self.mod).remove_leftovers(self.tail)
        self.assertIn(f"{anim.UNITS} [unit.{self.tail}]", gone)
        self.assertIn(f"files/models/{self.tail}.copy.toml", gone)
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertNotIn(self.tail, anim.read_units(self.mod))
        self.assertEqual(tree(self.mod)["src/studio.rndf"], before["src/studio.rndf"])
        with self.assertRaises(ValueError):    # never a unit the mod has
            ModEdits(self.mod).remove_leftovers(self.other)
        self.assertIn(self.other, anim.read_units(self.mod))

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_leftovers_with_a_file_held_are_all_put_back_and_trying_again_takes_them(self):
        """The lead's check of 2026-11-13 (a planted mistake no test caught: remove_leftovers no longer putting back
        what it had moved): the take-out of what a deleted unit left, stopped by a file another program holds, leaves
        every leftover where it was (the files it had already set aside too, no .taking-out left), and trying again
        once the file is free takes them all."""
        edits = ModEdits(self.mod)
        edits.new_units.pop(UNIT)
        edits.save()
        before = tree(self.mod)
        self.assertGreater(len(unit_files(self.mod, self.tail)), 2)
        # (a clip in the unit's own animations folder: the folder is the last thing set aside, so the card, the
        # models and the records have been moved by then and must come back)
        held = open(self.mod / anim.OWN / self.tail / "stand.baf", "rb")
        try:
            with self.assertRaises(OSError):
                ModEdits(self.mod).remove_leftovers(self.tail)
        finally:
            held.close()
        self.assertEqual(tree(self.mod), before)
        self.assertFalse((self.mod / TAKING_OUT).exists())
        self.assertIn(self.tail, anim.read_units(self.mod))
        gone = ModEdits(self.mod).remove_leftovers(self.tail)
        self.assertIn(f"{anim.UNITS} [unit.{self.tail}]", gone)
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertNotIn(self.tail, anim.read_units(self.mod))


class AnimRemoveUnit(unittest.TestCase):
    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_its_folder_comes_back_when_units_toml_can_t_be_written(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("RUSE_TEST_TMP") or None) as tmp:
            mod = Path(tmp)
            rows_for(mod, ["Descriptor_Unit_A"])
            before = tree(mod)
            held = open(mod / anim.UNITS, "rb")
            try:
                with self.assertRaises(OSError):
                    anim.remove_unit(mod, "Descriptor_Unit_A")
            finally:
                held.close()
            self.assertEqual(tree(mod), before)
            anim.remove_unit(mod, "Descriptor_Unit_A")
            self.assertEqual(tree(mod), {})


class OnTheStudio(WithMod):
    """The Studio's Delete and Take it out on the made-up game, with an era library of two WWI units."""

    def setUp(self):
        super().setUp()
        lib = two_tank_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        env = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        env.start()
        self.addCleanup(env.stop)
        self.mod = Path(self.api.new_mod("Mend")["current"])
        self.liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        self.whippet = self.api.era_unit_add(OTHER_TANK, 0, 10)["address"]
        self.tail = self.liberty.rsplit("/", 1)[-1]
        rows_for(self.mod, [self.tail, self.whippet.rsplit("/", 1)[-1]])

    def record(self) -> dict:
        f = self.mod / era_units.INDEX
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}

    def credits(self) -> str:
        f = self.mod / era_units.CREDITS
        return f.read_text(encoding="utf-8") if f.is_file() else ""

    def liberty_gone_whole(self):
        self.assertNotIn(self.liberty, ModEdits(self.mod).new_units)
        self.assertEqual(self.record(), {OTHER_TANK: self.whippet})
        self.assertNotIn("Liberty", self.credits())
        self.assertIn(OTHER_LINE, self.credits())
        self.assertNotIn(self.tail, anim.read_units(self.mod))
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertFalse((self.mod / TAKING_OUT).exists())

    def held(self, name: str, click) -> Exception:
        """`click` while another program has the mod's file `name` open: what it raised; the mod checked unchanged."""
        before = tree(self.mod)
        f = open(self.mod / name, "rb")
        try:
            with self.assertRaises(StudioError) as said:
                click()
        finally:
            f.close()
        self.assertEqual(tree(self.mod), before)
        return said.exception

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_delete_with_era_units_json_held_leaves_all_of_it_and_says_so(self):
        """Finding 6: the record line and the credit line go with the unit, or nothing goes."""
        said = self.held(era_units.INDEX, lambda: self.api.delete_unit(self.liberty, "anyway"))
        self.assertIn(era_units.INDEX, str(said))
        self.assertIn("Close that program, then try again.", str(said))
        self.assertEqual(self.api.delete_unit(self.liberty, "anyway")["deleted"], self.liberty)
        self.liberty_gone_whole()

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_take_it_out_with_era_units_json_held_is_said_in_every_language(self):
        """As test_file_words' test_taking_it_out_with_its_era_record_held_is_said_in_words, with a real hold (that
        test stands one in by making Path.write_text fail, which the mend's whole-file writes no longer use)."""
        said = self.held(era_units.INDEX, lambda: self.api.era_unit_remove(LIBERTY, "anyway"))
        from ruse_studio import errortext
        template = ("{0} couldn't be read or written, because another program has it open or Windows didn't allow it. "
                    "Close that program, then try again.")
        path = str(self.mod / era_units.INDEX)
        self.assertEqual(str(said), template.format(path))
        import tomllib
        entries = tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))[errortext.key_of(template)]
        for lang in ("fr", "jpn", "fa"):
            self.api.set_pref("lang", lang)
            try:
                self.assertEqual(str(self.api.page_error(said)), entries[lang].format(path), lang)
            finally:
                self.api.set_pref("lang", "us")
        self.assertEqual(self.api.era_unit_remove(LIBERTY, "anyway")["removed"], self.liberty)
        self.liberty_gone_whole()

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_take_it_out_with_the_credits_held_leaves_all_of_it_and_trying_again_works(self):
        said = self.held(era_units.CREDITS, lambda: self.api.era_unit_remove(LIBERTY, "anyway"))
        self.assertIn(era_units.CREDITS, str(said))
        self.assertEqual(self.api.era_unit_remove(LIBERTY, "anyway")["removed"], self.liberty)
        self.liberty_gone_whole()

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_take_it_out_with_a_clip_held_says_which_file_in_french_too(self):
        name = f"{anim.OWN}/{self.tail}/stand.baf"
        said = self.held(name, lambda: self.api.era_unit_remove(LIBERTY, "anyway"))
        self.assertIn(self.tail, str(said))
        self.api.set_pref("lang", "fr")
        self.assertIn("Fermez ce programme", str(self.api.page_error(said)))
        self.api.set_pref("lang", "us")
        self.assertEqual(self.api.era_unit_remove(LIBERTY, "anyway")["removed"], self.liberty)
        self.liberty_gone_whole()

    def test_a_units_toml_with_a_mistake_is_said_and_nothing_goes(self):
        (self.mod / anim.UNITS).write_text("[unit.\n", encoding="utf-8")
        before = tree(self.mod)
        with self.assertRaisesRegex(StudioError, r"^Nothing was deleted: .*units\.toml has a mistake"):
            self.api.delete_unit(self.liberty, "anyway")
        self.assertEqual(tree(self.mod), before)

    def test_delete_and_take_it_out_still_take_it_whole(self):
        self.assertEqual(self.api.delete_unit(self.liberty, "anyway")["deleted"], self.liberty)
        self.liberty_gone_whole()
        self.assertEqual(self.api.era_unit_remove(OTHER_TANK, "anyway")["removed"], self.whippet)
        self.assertEqual(self.record(), {})
        self.assertEqual(self.credits(), "")
        self.assertFalse((self.mod / anim.UNITS).exists())

    # --- a mod an older Studio left half deleted ---
    def half_deleted(self) -> dict:
        """The Liberty taken out as 0.9.8.19's Delete or a take-out that stopped half way left it: the unit gone from
        src/studio.rndf, its rows, clips, card, record line and credit line left."""
        every_file(self.mod, self.tail)
        edits = ModEdits(self.mod)
        edits.new_units.pop(self.liberty)
        edits.save()
        return tree(self.mod)

    def test_delete_tried_again_takes_what_it_left(self):
        self.half_deleted()
        got = self.api.delete_unit(self.liberty)
        self.assertIsNone(got["deleted"])
        self.assertIn(f"{anim.UNITS} [unit.{self.tail}]", got["leftovers"])
        self.assertNotIn(self.tail, anim.read_units(self.mod))
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertIn(self.whippet.rsplit("/", 1)[-1], anim.read_units(self.mod))

    def test_take_it_out_tried_again_takes_what_it_left_and_its_lines(self):
        self.half_deleted()
        self.assertEqual(self.api.era_unit_remove(LIBERTY)["removed"], self.liberty)
        self.liberty_gone_whole()

    def test_never_a_game_unit_s_own_animations(self):
        """The mod's rows for one of the game's own units are its changes to it: Delete never takes them."""
        sherman = SOURCE.rsplit("/", 1)[-1]
        rows_for(self.mod, [self.tail, sherman])
        ix = self.api._open()
        try:
            ix._object(SOURCE)
        finally:
            ix.close()
        with self.assertRaisesRegex(StudioError, "isn't a unit made in this mod"):
            self.api.delete_unit(SOURCE)
        self.assertIn(sherman, anim.read_units(self.mod))
        self.assertTrue((self.mod / anim.OWN / sherman / "stand.baf").is_file())

    def test_a_unit_with_nothing_left_is_refused_as_before(self):
        with self.assertRaisesRegex(StudioError, "isn't a unit made in this mod"):
            self.api.delete_unit("$/GFX/Everything/Descriptor_Unit_Nobody")

    def build_line(self, copy: bool) -> str:
        """The build's own sentence (rusemod.build's template, as buildtext lists it) for the Liberty's leftovers."""
        start = "{0}: no mod in the set makes a unit {1}, and the game has none of that name. If {2} was deleted"
        mine = [t for t in buildtext.templates() if t.startswith(start)]
        self.assertEqual(len(mine), 2, mine)
        t = next(t for t in mine if ("this file was left behind" in t) == copy)
        where = f"{self.mod.name}: files/models/{self.tail}.copy.toml" if copy else f"{self.mod.name}: {anim.UNITS}"
        return t.format(where, self.tail, self.tail, self.tail, anim.UNITS, anim.OWN, self.tail)

    def test_test_in_game_s_log_offers_to_take_them_out(self):
        self.half_deleted()
        for copy in (False, True):
            fixes = self.api._leftovers_problem(self.build_line(copy), [self.mod])
            self.assertEqual(fixes, [{"kind": "unit_leftovers", "path": str(self.mod), "unit": self.tail}])
        self.assertEqual(self.api._leftovers_problem("my-mod: map.toml: x", [self.mod]), [])
        with self.assertRaisesRegex(StudioError, "isn't part of the last test's mods"):
            self.api.leftovers_fix(fixes[0])
        self.api._test_folders = [str(self.mod)]
        done = self.api.leftovers_fix(fixes[0])["done"]
        self.assertIn(self.tail, done)
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertEqual(self.api._leftovers_problem(self.build_line(False), [self.mod]), [])   # (nothing left)
        with self.assertRaisesRegex(StudioError, "Nothing that"):
            self.api.leftovers_fix(fixes[0])

    def test_no_fix_offered_for_a_unit_the_mod_has(self):
        whippet = self.whippet.rsplit("/", 1)[-1]
        line = self.build_line(False).replace(self.tail, whippet)
        self.assertEqual(self.api._leftovers_problem(line, [self.mod]), [])

    # --- finding 8 ---
    def old_delete(self, address: str) -> None:
        """0.9.8.19's Delete: the unit and its files gone, its record line and credit line left."""
        edits = ModEdits(self.mod)
        edits.new_units.pop(address)
        edits.save()
        anim.remove_unit(self.mod, address.rsplit("/", 1)[-1])

    def test_the_next_save_drops_the_lines_of_a_unit_deleted_before(self):
        self.old_delete(self.liberty)
        self.assertIn(LIBERTY, self.record())
        self.assertIn(LIBERTY_LINE, self.credits())
        _f, lib = self.api._era_library()
        with self.api._saving:
            self.api._era_save(self.api._era_record(), lib)
        self.assertEqual(self.record(), {OTHER_TANK: self.whippet})
        self.assertNotIn(LIBERTY_LINE, self.credits())
        self.assertIn(OTHER_LINE, self.credits())

    def test_export_drops_them_keeps_the_others_and_says_so(self):
        self.old_delete(self.liberty)
        self.api._game = lambda: None
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "x")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        from test_export_out import members
        got = members(Path(view["result"]["path"]))
        self.assertEqual(json.loads(got[era_units.INDEX]), {OTHER_TANK: self.whippet})
        credits = got[era_units.CREDITS].decode("utf-8")
        self.assertNotIn(LIBERTY_LINE, credits)
        self.assertIn(OTHER_LINE, credits)
        self.assertTrue(any("Mark VIII Liberty" in line and "no longer in the mod" in line for line in view["lines"]),
                        view["lines"])

    def test_a_line_the_library_can_t_name_stays(self):
        """An era unit of another era (not downloaded here) the mod has: its credit line stays, as before; the
        deleted Liberty's goes (the library names it)."""
        self.old_delete(self.liberty)
        record = self.record()
        record["WWI|GBR|Old Tank"] = self.whippet          # (a unit the mod has, its era unknown on this PC)
        (self.mod / era_units.INDEX).write_text(json.dumps(record), encoding="utf-8")
        f = self.mod / era_units.CREDITS
        f.write_text(f.read_text(encoding="utf-8").replace(OTHER_LINE, OTHER_LINE + "\n" + HAND_LINE),
                     encoding="utf-8")
        self.assertEqual(self.api._era_tidy(self.mod), ["Mark VIII Liberty"])
        self.assertIn(HAND_LINE, self.credits())
        self.assertIn(OTHER_LINE, self.credits())
        self.assertNotIn(LIBERTY_LINE, self.credits())

    def test_a_mod_with_nothing_stale_is_left_byte_for_byte(self):
        before = tree(self.mod)
        self.assertEqual(self.api._era_tidy(self.mod), [])
        self.assertEqual(tree(self.mod), before)

    # (the fix wired into Test in game's mistakes at the join: api._problem, api.test_fix, app.js; fixer A's two tests)
    def test_problems_offer_it_and_the_fix_takes_it(self):
        from rusemod.webui import Job
        from ruse_studio.edits import unit_files
        self.half_deleted()
        job = Job()
        job.state, job.errors = "failed", [self.build_line(False), "my-mod: map.toml: x"]
        self.api._jobs[job.id] = job
        self.api._test_job, self.api._test_folders = job.id, [str(self.mod)]
        problems = self.api.test_problems()["problems"]
        self.assertEqual(problems[0]["fixes"], [{"kind": "unit_leftovers", "path": str(self.mod), "unit": self.tail}])
        self.assertEqual(problems[0]["mod"], self.mod.name)
        self.assertEqual(problems[1]["fixes"], [])
        self.api.set_pref("lang", "fr")
        self.assertIn("Retirer ce qu'elle a laissé", self.api.test_problems()["problems"][0]["text"])
        self.api.set_pref("lang", "us")
        done = self.api.test_fix(problems[0]["fixes"][0])["done"]
        self.assertIn(self.tail, done)
        self.assertEqual(unit_files(self.mod, self.tail), [])

    def test_the_page_labels_the_button(self):
        import ruse_studio
        js = (Path(ruse_studio.__file__).parent / "ui" / "app.js").read_text(encoding="utf-8")
        self.assertIn("unit_leftovers: [w.test_fix_unit_leftovers, w.tip_test_fix_unit_leftovers]", js)


ON_THE_GAME =msvcrt is not None and GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() \
    and HEAVY.is_file()


@unittest.skipUnless(ON_THE_GAME, "needs Windows, RUSE_GAME, the Studio's game index and the passed copy's two files")
class HeldOnTheGame(unittest.TestCase):
    """The checker's case (test_check_words.ItsAnimationsFileHeld) with the Horse Squad: the mod as it was, the words,
    and trying again once the file is free."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="mt-", dir=os.environ.get("RUSE_TEST_TMP") or None))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.mod = Path(self.api.new_mod("Held")["current"])
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            view = finished(self.api, self.api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.address = view["result"]["address"]
        self.tail = self.address.rsplit("/", 1)[-1]

    def held(self, how: str, click) -> StudioError:
        table = self.mod / anim.UNITS
        before = tree(self.mod)
        f = open(table, "rb")
        size = table.stat().st_size
        if how == "lock":
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, size)
        try:
            with self.assertRaises(StudioError) as said:
                click()
        finally:
            if how == "lock":
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, size)
            f.close()
        self.assertEqual(tree(self.mod), before)
        self.assertIn("units.toml couldn't be read or written, because another program has it open", str(said.exception))
        return said.exception

    def gone_whole(self):
        self.assertNotIn(self.address, ModEdits(self.mod).new_units)
        self.assertNotIn(self.tail, anim.read_units(self.mod))
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertNotIn(horse_squad.KEY, json.loads((self.mod / era_units.INDEX).read_text(encoding="utf-8")))
        credits = self.mod / era_units.CREDITS
        self.assertFalse(credits.is_file() and "sneadtristen6" in credits.read_text(encoding="utf-8"))
        self.assertFalse((self.mod / TAKING_OUT).exists())

    def test_take_it_out_open_then_again(self):
        self.held("open", lambda: self.api.era_unit_remove(horse_squad.KEY, "anyway"))
        self.assertEqual(self.api.era_unit_remove(horse_squad.KEY, "anyway")["removed"], self.address)
        self.gone_whole()

    def test_delete_locked_then_again(self):
        self.held("lock", lambda: self.api.delete_unit(self.address, "anyway"))
        self.assertEqual(self.api.delete_unit(self.address, "anyway")["deleted"], self.address)
        self.gone_whole()


if __name__ == "__main__":
    unittest.main()
