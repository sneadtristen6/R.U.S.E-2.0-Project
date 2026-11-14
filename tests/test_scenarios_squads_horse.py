"""Scenarios: the Generic Horse as a player meets it in the RUSE Studio, on the game (the Studio's game index and the
game folder read, never written): added to a mod from the Units tab (WWII+), taken out, added again; in two mods, one
taken out; in a mod shared to another PC (Export, the Launcher's library, Edit an installed mod), Resize and Move
there, with and without the Generic Horse's files on that PC; taken out while one of its files is open in another
program; and opened in Blender before it was taken out and added again. Each ends with what the page says in every
language, the mod's files, the Studio's check, and, where the case turns on what the build takes, the mod built on the
game into a folder of this run (rusemod.build.build_and_write, as Test in game builds, the game's files read only).

Its builder stands in (as test_horse_squad's ItsFilesOnTheGame) with the two horse-and-rider files of the copy that
passed in the game (RUSE_HORSE_SQUAD_GLBS, by default scratch/animmodels/fixes3), whose bytes are the ones this
Studio's builder makes (horse_squad.MADE_BYTES): the rest is the Studio's own, the models' import and fitting with it.
Blender stands in too: what it writes when it sends is written here.

FOR: the squads scenarios (release 0.9.8.20, overnight 2026-11-13/14). USED-BY: the scenarios' run and report."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_horse_squad import GAME, GLBS, HEAVY, INDEX, RIFLE, finished, stand_in, tree
from test_scenarios_squads_base import LANGS, PYTHON_WORDS
from test_squadblender import Closed
from ruse_studio import era_units, horse_squad

KEY = horse_squad.KEY
TMP_ROOT = Path(os.environ.get("RUSE_TEST_TMP") or "D:/RUSE-2.0/scratch/release-0920/scenarios/squads/tmp")
PATCHES_HERE = "D:/RUSE-2.0/scratch/animmodels/squadpatch/release/"   # (the game patches' release files, kept here)


def fill(word: str, **values) -> str:
    for k, v in values.items():
        word = word.replace("{" + k + "}", str(v))
    return word


@unittest.skipUnless(GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file(),
                     "RUSE_GAME names no game folder, or the Studio's game index or the passed copy's two horse files "
                     "aren't there")
class HorseScenario(unittest.TestCase):
    def setUp(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="horse-scen-", dir=TMP_ROOT))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        env = mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(self.tmp / "platform")})   # (the build's cache)
        env.start()
        self.addCleanup(env.stop)
        self.started = []    # each Blender the Studio would have started: (what it opened, where it sends)
        blender = mock.patch("rusemod.blender.open_model_to_change",
                             lambda b, model, send, words: self.started.append((Path(model), Path(send))) or Closed())
        blender.start()
        self.addCleanup(blender.stop)

    def studio(self, name: str):
        """A Studio on its own platform folder (a PC of its own), as the page calls it."""
        from ruse_studio.api import StudioApi
        from rusemod.webui import page_api
        api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.tmp / name)
        api._blender = lambda: self.tmp / "blender" / "blender.exe"
        self.addCleanup(api.set_pref, "lang", "us")
        return api, page_api(api)

    def added(self, api, page, mod_name: str | None) -> tuple[Path, str]:
        """Add to my mod on the Generic Horse's page (a new mod first when `mod_name` is given): the job followed to its
        end, as the page follows it. (the mod, its unit's address)"""
        if mod_name:
            page.new_mod(mod_name)
        folder = Path(api._mod_dir())
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            view = finished(api, page.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        return folder, view["result"]["address"]

    def refused(self, api, page, name: str, *args) -> dict:
        from ruse_studio.api import StudioError
        out = {}
        for lang in LANGS:
            api.set_pref("lang", lang)
            try:
                getattr(page, name)(*args)
                out[lang] = None
            except StudioError as exc:
                out[lang] = str(exc)
        api.set_pref("lang", "us")
        return out

    def assert_worded(self, said: dict, english: str | None = None) -> None:
        if english is not None:
            self.assertEqual(said["us"], english)
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertTrue(said[lang], lang)
                if lang != "us":
                    self.assertNotEqual(said[lang], said["us"], f"{lang}: English left in")
                for bad in PYTHON_WORDS:
                    self.assertNotIn(bad, said[lang], lang)
                self.assertNotRegex(said[lang], r"\{[a-z_0-9]*\}", lang)

    def words(self, lang: str) -> dict:
        from ruse_studio.api import words
        return words(lang)

    def problems(self, page) -> list:
        return [p.get("problem") for p in page.check_mod()["problems"]]

    @staticmethod
    def animations(folder: Path, address: str) -> dict:
        from rusemod import anim
        unit = address.rsplit("/", 1)[-1]
        own = anim.own_animations(folder, unit)["animations"]
        return {name: (Path(folder) / anim.OWN / unit / rel).read_bytes() for name, rel in own.items()}

    def built_on_the_game(self, *mods: Path):
        """The mods built on the game into a folder of this run (Test in game's build, its output never the game's
        folder): the build's result. The own-squads game patch a squad of its own number needs is read from
        RUSE_GAME_PATCHES_URL, by default the release's patch files kept on this PC (PATCHES_HERE), checked by their
        SHA-256 as the build checks a download."""
        from rusemod.build import DEFAULT_PACK, build_and_write, find_pack, load_mod
        out = Path(tempfile.mkdtemp(prefix="built-", dir=self.tmp))
        patches = os.environ.get("RUSE_GAME_PATCHES_URL") or (PATCHES_HERE if Path(PATCHES_HERE).is_dir() else "")
        with mock.patch.dict(os.environ, {"RUSE_GAME_PATCHES_URL": patches} if patches else {}):
            return build_and_write(GAME, [load_mod(m) for m in mods], pack=str(find_pack(GAME, DEFAULT_PACK)),
                                   out=out / "out", cache=out / "cache", say=lambda _s: None)


class AddedTakenOutAddedAgain(HorseScenario):
    def test_added_taken_out_and_added_again(self):
        """Usual: the Generic Horse is listed in WWII+, not in the mod; Add to my mod: the page says it's in, in every
        language, and its row says so; its page's squad part reads in every language; the check finds nothing. Take it
        out of my mod: the page says so in every language, none of its files left; Add to my mod again: the mod's files
        the same as the first time, byte for byte."""
        api, page = self.studio("pc")
        page.new_mod("Cavalry")
        row = next(u for u in page.era_units_list("WWII")["units"] if u["key"] == KEY)
        self.assertEqual((row["name"], row["added"]), ("Generic Horse", None))
        empty = tree(Path(api._mod_dir()))
        mod, horse = self.added(api, page, None)
        self.assert_worded({lang: fill(self.words(lang)["eras_added"], name="Generic Horse") for lang in LANGS})
        self.assertEqual(next(u for u in page.era_units_list("WWII")["units"] if u["key"] == KEY)["added"], horse)
        info = {lang: page.squad_info(horse, lang) for lang in LANGS}
        self.assertEqual((info["us"]["count"], info["us"]["own"]), (5, True))
        self.assert_worded({lang: i["line"] for lang, i in info.items()})
        self.assertEqual(self.problems(page), [])
        first = tree(mod)
        tail = horse.rsplit("/", 1)[-1]
        self.assertIn(f"files/models/{tail}.glb", first)
        self.assertIn(f"files/models/{tail}@bazooka.glb", first)
        res = page.era_unit_remove(KEY)
        self.assertEqual((res["removed"], res["waiting"]), (horse, []))
        self.assert_worded({lang: fill(self.words(lang)["eras_removed"], name="Generic Horse") for lang in LANGS})
        left = tree(mod)
        self.assertEqual([n for n in left if tail in n and not n.startswith("blender/")], [])
        self.assertNotIn(era_units.CREDITS, left)
        self.assertEqual(json.loads(left.pop(era_units.INDEX)), {})
        self.assertEqual(self.problems(page), [])
        _mod, again = self.added(api, page, None)
        self.assertEqual(again, horse)
        second = tree(mod)
        differ = sorted(n for n in set(first) | set(second) if first.get(n) != second.get(n))
        self.assertEqual(differ, [])
        self.assertEqual(sorted(set(empty) - set(first)), sorted(set(empty) - set(second)))


class InTwoMods(HorseScenario):
    def test_in_two_mods_one_taken_out(self):
        """Usual: the Generic Horse added to two mods (its files made once on this PC, every mod's), then taken out of
        the first: the second's files as they were, and its Resize works (the page says the new size in every
        language), its animations as they were."""
        api, page = self.studio("pc")
        first, horse = self.added(api, page, "Cavalry A")
        second, horse_b = self.added(api, page, "Cavalry B")
        self.assertEqual(sorted(os.listdir(api._home / horse_squad.FOLDER)), sorted([RIFLE.name, HEAVY.name]))
        kept = tree(second)
        page.choose_mod(str(first))
        page.era_unit_remove(KEY)
        self.assertEqual(tree(second), kept)
        page.choose_mod(str(second))
        self.assertTrue(page.model_sizes(horse_b, "us")["resizable"])
        before = self.animations(second, horse_b)
        page.model_resize(horse_b, 1.2)
        self.assert_worded({lang: fill(self.words(lang)["model_resized"], size="1.2") for lang in LANGS})
        self.assertEqual(self.animations(second, horse_b), before)
        self.assertEqual(self.problems(page), [])


class SharedToAnotherPC(HorseScenario):
    def test_resize_and_move_there_without_then_with_its_files(self):
        """Usual: a mod with the Generic Horse exported and opened on another PC (the Launcher's library, Edit an
        installed mod). Its player never added the Generic Horse, so its files aren't on that PC: Resize and Move are
        off (model_sizes) and refused in words in every language, the no-loss way first, nothing changed. He adds the
        Generic Horse to a mod of his own: then both work there, its animations as they were, and the check finds
        nothing."""
        from rusemod import package
        from rusemod.library import Library
        api1, page1 = self.studio("first")
        mod, horse = self.added(api1, page1, "Cavalry")
        before = self.animations(mod, horse)
        export = package.pack(mod, self.tmp / "exported")
        api2, page2 = self.studio("second")
        info, _replaced = Library(api2._home / "library").add(export)
        copy = Path(page2.edit_installed(info["id"], "Cavalry (my copy)")["path"])
        page2.choose_mod(str(copy))
        unchanged = tree(copy)
        self.assertFalse(page2.model_sizes(horse, "us")["resizable"])
        for name, args in (("model_resize", (horse, 1.2)), ("model_place", (horse, [10, 0, 0]))):
            with self.subTest(call=name):
                said = self.refused(api2, page2, name, *args)
                print(f"\nH-shared {name}:", said["us"][:200], "|", said["fr"][:120])
                self.assertTrue(said["us"].startswith("The file the Generic Horse's model was made from isn't there"),
                                said["us"])
                self.assert_worded(said)
        self.assertEqual(tree(copy), unchanged)
        self.added(api2, page2, "My own")
        page2.choose_mod(str(copy))
        self.assertTrue(page2.model_sizes(horse, "us")["resizable"])
        page2.model_resize(horse, 1.2)
        page2.model_place(horse, [10, 0, 0])
        self.assertEqual(self.animations(copy, horse), before)
        self.assertEqual(self.problems(page2), [])


class TakenOutWhileItsFileIsOpen(HorseScenario):
    def test_taken_out_while_its_model_is_open_in_another_program(self):
        """Unusual: its riders' model file open in another program, then Take it out of my mod: it goes all the same,
        the page says which file waits (every language); the mod builds on the game without it (the file left out)
        and the check finds nothing; once the program lets go, opening the mod again takes the file out."""
        api, page = self.studio("pc")
        mod, horse = self.added(api, page, "Cavalry")
        tail = horse.rsplit("/", 1)[-1]
        held = open(mod / "files" / "models" / f"{tail}.glb", "rb")
        try:
            with mock.patch("ruse_studio.edits.HOLD_WAIT", 0.3):
                res = page.era_unit_remove(KEY)
            self.assertEqual((res["removed"], res["waiting"]), (horse, [f"files/models/{tail}.glb"]))
            self.assert_worded({lang: fill(self.words(lang)["unit_deleted_waiting_one"], file=res["waiting"][0])
                                for lang in LANGS})
            self.assertEqual(self.problems(page), [])
            result = self.built_on_the_game(mod)
            self.assertEqual([f.message for f in result.errors], [])
            self.assertNotIn(tail, json.dumps(sorted(getattr(result, "own_models", {}) or {})))
        finally:
            held.close()
        page.choose_mod(str(mod))
        self.assertEqual([n for n in tree(mod) if tail in n and not n.startswith("blender/")], [])


class InASet(HorseScenario):
    def test_a_squad_mod_and_a_horse_mod_together(self):
        """Usual: a mod with a squad of its own number and a soldier's look (+1, Import a model... on soldier 2's line
        from the game's soldier as the Studio exports him) and a mod with the Generic Horse, built together on the
        game: no error, the own-squads patch named, the squad's look and the horse's models among its own models."""
        api, page = self.studio("pc")
        horse_mod, horse = self.added(api, page, "Cavalry")
        squad_mod = Path(page.new_mod("Riflemen")["current"])
        squad = page.new_unit(horse_squad.SQUAD, "Scen Riflemen", 50)["address"]
        page.soldier_plus(squad)
        from rusemod import gltf, models
        lib = models.Library(GAME)
        try:
            soldier = next(m for m in api._look_models(squad)[0] if "bazooka" not in m.lower() and "_dest" not in m)
            glb, _pictures, _summary = gltf.model_glb(lib, soldier, rest_bones=True)
        finally:
            lib.close()
        his = self.tmp / "his models" / "soldier.glb"
        his.parent.mkdir(parents=True)
        his.write_bytes(glb)
        page.soldier_import(squad, "2", str(his))
        result = self.built_on_the_game(squad_mod, horse_mod)
        self.assertEqual([f.message for f in result.errors], [])
        self.assertEqual(result.game_patch, ["own-squads"])
        tail, stem = horse.rsplit("/", 1)[-1], squad.rsplit("/", 1)[-1]
        self.assertEqual(sorted(str(k) for k in result.own_models), sorted([tail, f"{tail}@bazooka", f"{stem}@2"]))

    @unittest.expectedFailure    # finding SQ-12: two mods each with the Generic Horse can't be played together
    def test_two_mods_each_with_the_generic_horse_together(self):
        """Unusual: two mods each with the Generic Horse (the one Generic Horse: the same unit name in each, its files
        the same bytes), built together, as a Launcher set of a player's own cavalry mod and a shared one would be:
        the build stops, the second mod "creates ... Descriptor_Unit_Generic_Horse, but" the first "already has an
        object with that name", and nothing is written."""
        api, page = self.studio("pc")
        first, _horse = self.added(api, page, "Cavalry A")
        second, _same = self.added(api, page, "Cavalry B")
        result = self.built_on_the_game(first, second)
        print("\nSQ-12:", [f.message for f in result.errors])
        self.assertEqual([f.message for f in result.errors], [])


class BlenderThenAddedAgain(HorseScenario):
    @unittest.expectedFailure    # finding SQ-10: the Generic Horse added again opens the old one's Blender sending
    def test_open_in_blender_after_taken_out_and_added_again(self):
        """Unusual: the Generic Horse opened in Blender (the one Blender button: its riflemen with their horse), sent
        changed, closed, not brought back; Take it out of my mod; Add to my mod again. Its Blender folder (blender/
        <unit>/: the sending and the one button's record) isn't among the files the take-out takes, so the new one's
        page has Bring my changes back on its big button, and Open in Blender opens the old one's sending (what was
        sent last: modelblender.model_blender; since the anims piece, aa2c0a65, a file made from that sending,
        <its name>_again.glb: modelblender._again), not its own model as the first time."""
        api, page = self.studio("pc")
        mod, horse = self.added(api, page, "Cavalry")
        page.blender_open(horse, {"model": True, "bones": True, "paint": True, "kind": ""}, "us")
        start, send = self.started[-1]
        send.write_bytes(start.read_bytes())    # (what Blender sent and was never brought back: the old one's)
        page.era_unit_remove(KEY)
        self.added(api, page, None)
        parts = page.blender_parts(horse, "us")
        page.blender_open(horse, {"model": True, "bones": True, "paint": True, "kind": ""}, "us")
        opened = self.started[-1][0]
        print("\nSQ-10 added again: big button open", parts["open"], "| Blender opened", opened.name,
              "| the first time", start.name)
        self.assertFalse(parts["open"])
        self.assertEqual(opened.name, start.name)      # (as the first time: its own model, never the old sending)


if __name__ == "__main__":
    unittest.main()
