"""The tests lens of the review of feat/anim-decoy-blender at 07a688b5 (reviewer 3 of 4: "would the tests fail if the
code were wrong in a plausible way?"). Each plausible mistake was made on purpose in the code, one at a time, and the
test files that cover it were run; the mistakes no test caught get a test here. Every test below passes on 07a688b5
and fails on the mistake its docstring names (the review's mistake ids: H for the Units tab's Add, S for the shine
door, B for the builder).

On the Studio tests' made-up game, always: the Horse Squad put in the build menu the add form picks; the final check
on its two models' bones refusing models on other bones and taking the unit out; the mod held while its unit is made
and freed after, by the Add itself; one file handed over for both soldiers, or a file that isn't a .glb, refused;
Change it in Blender's alpha.json written anew at a fresh export, a picture it names outside its folder never read,
an old folder's picture taken only when one alone matches, a soldier joined from the squad page keeping his alpha; the
era units' add after the split: a library model whose file is missing never imported, a group of its own answered;
the builder's game index reaching its listings, the game's unit data read only when the index hasn't them, a shadow
copy in the index never read, its scratch folder made in the folder it was given and gone after a refusal, a horse
point on a bone it leaves out refused.

With RUSE_GAME naming the game folder, and the Studio's game index (RUSE_GAME_INDEX, else RUSE_STUDIO_INDEX): the
price and build menu asked kept on the game's own US rifle squad; a bazooka man on bones other than the rifleman's
refused. With the two files the game test passed with too (RUSE_HORSE_FIXES3, else RUSE_HORSE_SQUAD_GLBS): the real
builder through the Units tab's Add gives the mod the files the copy's own calls give with those two files, and the
builder's two files are those bytes (before this review the two had never run together: the Add's tests use a
stand-in builder)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_era_units as eu         # (its EraResearch by the module's name, as test_modelblender's ItsOwnShine below)
import test_horsesquad as th        # (its made-up skeletons and clips)
import test_modelblender as mb      # (its ItsOwnShine by the module's name: imported bare, its tests would run here too)
from test_horse_squad import finished, stand_in, tree
from test_squadblender import SQUAD as THE_SQUAD, STEM as THE_STEM, Squad, glb_from   # (Squad has no tests)
from test_studio import WithMod, write_game
from rusemod import baf, horsesquad as hs, modelin
from rusemod.dxt import png_bytes
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi
from ruse_studio.edits import ModEdits

GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
_INDEX = os.environ.get("RUSE_GAME_INDEX") or os.environ.get("RUSE_STUDIO_INDEX")
INDEX = Path(_INDEX) if _INDEX else None
_PASSED = os.environ.get("RUSE_HORSE_FIXES3") or os.environ.get("RUSE_HORSE_SQUAD_GLBS")
PASSED = Path(_PASSED) if _PASSED else None
KEY, SQUAD = horse_squad.KEY, horse_squad.SQUAD


def era_library(test) -> None:
    """An era units library with nothing of WWII+ in it, for the test's lifetime (as test_horse_squad's)."""
    lib = Path(tempfile.mkdtemp(dir=test.tmp.name))
    (lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": []}), encoding="utf-8")
    patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
    patcher.start()
    test.addCleanup(patcher.stop)


def checked_on(rows: list):
    """The Add's own final check (StudioApi._horse_check, as the code has it), run on these soldiers' rows in place of
    what the made-up game's models would give (it has no models to fit to)."""
    real = StudioApi._horse_check

    def check(api, address):
        with mock.patch.object(api, "_kind_rows", return_value=rows):
            return real(api, address)
    return mock.patch.object(StudioApi, "_horse_check", check)


def own_rows(same_bones, main_skeleton="own") -> list:
    return [{"kind": "fusilier", "own": True, "skeleton": main_skeleton, "same_bones": None},
            {"kind": "bazooka", "own": True, "skeleton": "own", "same_bones": same_bones}]


class TheAddOnTheMadeUpGame(WithMod):
    def setUp(self):
        super().setUp()
        era_library(self)
        self.files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = self.files / "rifle.glb", self.files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def builder(self, rifle=None, heavy=None, **kw):
        return mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(rifle or self.rifle, heavy or self.heavy,
                                                                           **kw)})

    def no_import(self):
        return mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None)

    def test_put_in_the_build_menu_the_form_picks(self):
        """H05 (the USA's menu whatever nation is picked) and H07 (the nation and menu asked ignored): the add form
        lets the modder pick any nation's build menu, as an era unit's does; every other test adds it to the USA's."""
        folder = Path(self.api.new_mod("Germany")["current"])
        with self.builder(), self.no_import(), checked_on(own_rows(True)):
            view = finished(self.api, self.api.horse_squad_add(1, 10, "Kavallerie", group="new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        made = view["result"]["address"]
        row = next(u for u in self.api.units()["units"] if u["address"] == made)
        self.assertEqual((row["nation"], row["factory"], row["new"], row["source"]), (1, 10, True, SQUAD))
        self.assertEqual(json.loads((folder / era_units.INDEX).read_text(encoding="utf-8")), {KEY: made})

    def test_models_not_on_the_same_bones_are_refused_and_taken_out(self):
        """H17 (the final check not asking for the same bones) and H18 (the final check skipped): its own check refuses
        a heavy-weapon soldier whose model isn't on the riflemen's bones, and riflemen not on bones of their own, and
        what the job made goes again; the same rows with the same bones pass (the control)."""
        cases = ((own_rows(False), "heavy-weapon soldier on other bones"),
                 (own_rows(None), "heavy-weapon soldier's bones not known"),
                 (own_rows(True, main_skeleton="soldier"), "riflemen on the game soldier's bones"))
        for k, (rows, what) in enumerate(cases):
            with self.subTest(what):
                folder = Path(self.api.new_mod(f"Bones {k}")["current"])
                before = tree(folder)
                with self.builder(), self.no_import(), checked_on(rows):
                    view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
                self.assertEqual((view["state"], view["message"]), (
                    "failed", "The Generic Horse's two models didn't come in on the same bones, so it wasn't added. "
                              "Please report this."))
                self.assertEqual(view["lines"], ["build", "unit", "riflemen", "bazooka"])
                self.assertEqual(ModEdits(folder).new_units, {})
                after = tree(folder)
                self.assertEqual(json.loads(after.pop(era_units.INDEX)), {})
                after.pop("src/studio.rndf", None)
                self.assertEqual(after, {name: data for name, data in before.items() if name != "src/studio.rndf"})
        folder = Path(self.api.new_mod("Same bones")["current"])
        with self.builder(), self.no_import(), checked_on(own_rows(True)):
            view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertIn(view["result"]["address"], ModEdits(folder).new_units)

    def test_its_mod_is_held_while_its_unit_is_made_and_freed_after(self):
        """H33 (the mod never held while its unit is made), H34 (never freed after) and G01 (making a new mod not
        refused before its folder is made: choose_mod's own hold refuses it after, a stray mod left): test_horse_squad
        sets the hold by hand and checks only the refusal; here the Add's own: switching to another mod, or making a
        new one, while the riflemen's model is imported is refused and makes nothing, and once the Horse Squad is in,
        switching works again."""
        first = Path(self.api.new_mod("Held")["current"])
        other = Path(self.api.new_mod("Other")["current"])
        self.api.choose_mod(str(first))
        mods = sorted(p.name for p in first.parent.iterdir())
        said = []

        def importing(api, address, file, **kw):
            if said:
                return
            for call in (lambda: api.choose_mod(str(other)), lambda: api.new_mod("Third")):
                try:
                    call()
                    said.append("done")
                except Exception as exc:   # (any refusal: its words are checked below)
                    said.append(str(exc))
        with self.builder(), mock.patch.object(StudioApi, "model_import", importing), checked_on(own_rows(True)):
            view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
        self.assertEqual(said, ["The Generic Horse is being added to this mod: wait for it to finish."] * 2)
        self.assertEqual(sorted(p.name for p in first.parent.iterdir()), mods)      # no mod made meanwhile
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertIn(view["result"]["address"], ModEdits(first).new_units)
        self.assertEqual(self.api.choose_mod(str(other))["current"], str(other))

    def test_files_that_aren_t_two_glb_files_are_refused(self):
        """H25 (two files of one name from the builder accepted) and H35 (a file that isn't a .glb accepted): a
        builder that hands over one file for both soldiers, or a file of another kind, didn't make the Horse Squad;
        refused in words, the mod as it was."""
        other = self.files / "heavy.gltf"
        other.write_bytes(b"gltf heavy")
        for k, (rifle, heavy) in enumerate(((self.rifle, self.rifle), (self.rifle, other))):
            with self.subTest(files=(rifle.name, heavy.name)):
                folder = Path(self.api.new_mod(f"Files {k}")["current"])
                before = tree(folder)
                with self.builder(rifle=rifle, heavy=heavy), self.no_import(), checked_on(own_rows(True)):
                    view = finished(self.api, self.api.horse_squad_add(0, 10, group="new")["job"])
                self.assertEqual((view["state"], view["message"]), (
                    "failed", "The Generic Horse can't be made from your game: its two model files didn't come out. "
                              "Please report this."))
                self.assertEqual(tree(folder), before)


class EraUnitsThroughTheSplit(WithMod):
    """era_unit_add as _era_plan and _era_make (the split the Horse Squad shares)."""

    def test_a_library_model_whose_file_is_missing_is_never_imported(self):
        """E08 (the model tried when the library's file isn't there): the library names a model its folder hasn't got
        (an era not fully there): added with the start unit's look ("no_model"), Import model never asked."""
        lib = Path(tempfile.mkdtemp(dir=self.tmp.name))
        unit = {"key": "WWI|USA|Liberty", "era": "WWI", "nation": "USA", "name": "Liberty", "in_place_of": "",
                "card": "Heavy Tank", "building": "Armor base", "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman",
                "copies_name": "", "game_nation": 0, "factory": 10, "aircraft": False, "model": "WWI/USA/Liberty.glb",
                "fits": True, "picture": None, "credit": {"title": "Liberty model", "author": "maker",
                                                          "licence": "CC-BY 4.0", "url": "https://example.org/Liberty"}}
        (lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": [unit]}), encoding="utf-8")
        with mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)}):
            self.api.new_mod("Missing model")
            with mock.patch.object(StudioApi, "model_import", side_effect=AssertionError("Import model asked")):
                made = self.api.era_unit_add("WWI|USA|Liberty", 0, 10)
        self.assertEqual((made["model"], made["model_note"], made["size"]), (None, "no_model", None))


class EraUnitsAnswerTheirGroup(unittest.TestCase):
    """era_unit_add's answer after the split, on test_era_units' made-up game with upgrades and groups (EraResearch's
    own set-up, borrowed: imported bare, its tests would run here too)."""
    setUpClass = classmethod(eu.EraResearch.setUpClass.__func__)
    tearDownClass = classmethod(eu.EraResearch.tearDownClass.__func__)
    setUp, library = eu.EraResearch.setUp, eu.EraResearch.library

    def test_a_group_of_its_own_is_answered_with_its_own_address(self):
        """E10 (a group of its own answered as none): the answer's "group" is its group's first unit, its own address
        for a group of its own (era_unit_add's docstring); test_era_units checks the groups file, not the answer."""
        self.api.new_mod("Own group")
        made = self.api.era_unit_add("Modern|Russia|T-90", 0, 10, research_from=None, group="new")
        self.assertEqual(made["group"], made["address"])
        picked = self.api.era_unit_add("Cold War|USSR|T-80", 0, 10, research_from=None, group=eu.UC)
        self.assertEqual(picked["group"], eu.UC)


@unittest.skipUnless(GAME is not None and GAME.is_dir() and INDEX is not None and INDEX.is_file(),
                     "RUSE_GAME names no game folder, or no game index is named (RUSE_GAME_INDEX, RUSE_STUDIO_INDEX)")
class TheAddOnTheGame(unittest.TestCase):
    def test_its_price_and_build_menu_as_asked(self):
        """H08 (the price asked dropped), H05 and H07 on the game's own US rifle squad: the made-up game's squad has no
        price, and the game test adds it at the squad's own price ($5) in its own menu (USA, barracks), so neither
        test sees the form's price or menu dropped. Here: $7 in Germany's barracks (menu 8)."""
        home = Path(tempfile.mkdtemp(prefix="review-tests-"))
        self.addCleanup(shutil.rmtree, home, True)
        api = StudioApi(index_path=INDEX, game_dir=GAME, home=home)
        self.assertEqual(api.era_start_price(SQUAD)["price"], 5.0)        # (the squad's own price: not the one asked)
        folder = Path(api.new_mod("Asked")["current"])
        files = home / "given"
        files.mkdir()
        (files / "rifle.glb").write_bytes(b"glb rifle")
        (files / "heavy.glb").write_bytes(b"glb heavy")
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(files / "rifle.glb", files / "heavy.glb")}), \
                mock.patch.object(StudioApi, "model_import", lambda a, address, file, **kw: None), \
                checked_on(own_rows(True)):
            view = finished(api, api.horse_squad_add(1, 8, "Kavallerie", 7, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        own = ModEdits(folder).of(view["result"]["address"])
        price = own.get("ProductionPrice")
        self.assertEqual(set(price) if isinstance(price, list) else {price}, {7})
        self.assertEqual((own.get("Nationalite"), own.get("Factory")), (1, 8))


class TheShineDoorMore(unittest.TestCase):
    """More of ItsOwnShine (test_modelblender: its made-up tank, its stand-in for Blender, the Studio's real export and
    Import model's real reading of pictures), for what alpha.json is for."""
    setUp, tearDown = mb.ItsOwnShine.setUp, mb.ItsOwnShine.tearDown
    patched, trip = mb.ItsOwnShine.patched, mb.ItsOwnShine.trip
    MODEL = "Descriptor_Unit_My_Tank.glb"

    def another_export(self, value: int = 9) -> None:
        """What an earlier Change it in Blender of another model leaves in the same work folder (a unit deleted and made
        again under the same name: its Blender folder stays, see below): that model's export and an alpha picture for
        each of the same materials, all `value`."""
        shutil.copyfile(self.work / "test_tank.glb", self.work / "other_tank.glb")
        for material, (w, h) in (("test_tank_hull", (8, 4)), ("test_tank_turret", (4, 4))):
            (self.work / f"other_tank_{material}_alpha.png").write_bytes(png_bytes(bytes([value] * 3) * (w * h), w, h))

    def test_an_old_folder_takes_a_picture_only_when_one_alone_matches(self):
        """S15 (an old folder's picture taken when several match): without alpha.json, two exports' pictures for the
        same material: neither is taken (the plain 144), as the code says, never the wrong one."""
        def old_folder_with_two():
            (self.work / "alpha.json").unlink()
            self.another_export()
        self.trip(before_back=old_folder_with_two)
        plain = bytes([modelin.PLAIN_ALPHA])
        self.assertEqual(mb.alphas_in(self.models / self.MODEL), {"test_tank_hull": plain * 32,
                                                                  "test_tank_turret": plain * 16})

    def test_a_fresh_export_lists_its_own_pictures_anew(self):
        """S06 (a stale alpha.json kept at a fresh export): a work folder keeps what an earlier unsent Change it in
        Blender left (deleting a unit leaves its Blender folder: ruse_studio.edits.remove_unit), so a unit made again
        under the same name from another start unit exports another model into it; its own pictures go back, not the
        plain 144 a list of the other model's would give."""
        other = "ww2\\res3d\\units\\us\\char\\other_tank\\other_tanklod0.ase2ndfbin"
        hull, turret = "ww2\\res3d\\units\\us\\char\\other_tank\\other_hull.tgv", \
            "ww2\\res3d\\units\\us\\char\\other_tank\\other_turret.tgv"
        pictures = {hull: mb.game_picture(13, 8, 4), turret: mb.game_picture(17, 4, 4)}

        class TwoTanks(mb.PaintedLibrary):
            def parts(self, name):
                got = super().parts(name)
                return [(got[0][0], hull), (got[1][0], turret)] if name == other else got

            def picture(self, texture, most=512):
                return pictures.get(texture) or super().picture(texture, most)
        with mock.patch("rusemod.models.Library", TwoTanks), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: self.opened.append(Path(model)) or None), \
                mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)), \
                mock.patch("rusemod.unitmodel.import_model", mb.fitted):
            self.api.model_blender(mb.TANK)                          # opened, never sent
            self.api._look_models = lambda address: ([other], [])   # the unit made again from another tank
            self.api.model_blender(mb.TANK)
            self.assertEqual(self.opened[-1].name, "other_tank.glb")
            mb.blender_sends(self.opened[-1], self.send)
            self.api.model_blender_back(mb.TANK)
        self.assertEqual(mb.alphas_in(self.models / self.MODEL), {"other_hull": pictures[hull][2][3::4],
                                                                  "other_turret": pictures[turret][2][3::4]})

    def test_a_picture_named_outside_the_work_folder_is_never_read(self):
        """S14 (a listed alpha picture outside the work folder used): alpha.json naming a file in another folder is
        never read (the code keeps to the work folder's own files); that material has the plain 144."""
        def elsewhere():
            listed = json.loads((self.work / "alpha.json").read_text(encoding="utf-8"))
            listed["alpha"]["test_tank_hull"] = "../outside_alpha.png"
            (self.work / "alpha.json").write_text(json.dumps(listed), encoding="utf-8")
            (self.work.parent / "outside_alpha.png").write_bytes(png_bytes(bytes([9] * 3) * 32, 8, 4))
        self.trip(before_back=elsewhere)
        got = mb.alphas_in(self.models / self.MODEL)
        self.assertEqual(got["test_tank_hull"], bytes([modelin.PLAIN_ALPHA]) * 32)
        self.assertEqual(got["test_tank_turret"], mb.GAME_ALPHA["test_tank_turret"])


class TheSquadDoorJoin(Squad):
    """The squad page's Add a soldier, brought back (squadblender._join), with test_squadblender's stand-ins."""

    def test_a_soldier_joined_from_blender_keeps_his_alpha(self):
        """S17 (a soldier joined from Blender brought back without his alpha): the shine door moved the squad page's
        alpha helper into rusemod.gltf.with_alpha, and the join is one of its three callers; test_squadcount's join
        tests check his place and number, not his picture's alpha. The file Import model takes in has the alpha
        picture that went out with his material, by its name."""
        with self.patched():
            self.api.soldier_add(THE_SQUAD, "copy", "2")
        new = json.loads((self.work / "squad.json").read_text(encoding="utf-8"))["soldiers"][0]
        self.assertEqual(list(new["alpha"]), ["New soldier 1"])
        self.blender_opened()
        calls = self.taking_in()
        self.blender_sends({"new": glb_from(b"PNG-new", "New soldier 1")})
        with self.patched():
            self.assertEqual(self.api.squad_blender_back(THE_SQUAD)["joined"], "5")
        self.assertEqual(calls, [(THE_SQUAD, f"{THE_STEM}@5.glb", 1.0, "5")])
        doc, binary = modelin.glb_document((self.work / "kept" / f"{THE_STEM}@5.glb").read_bytes())
        alpha = doc["textures"][doc["materials"][0]["extras"]["rusemod_alpha_texture"]]["source"]
        self.assertEqual(modelin.glb_image(doc, binary, alpha), Path(new["alpha"]["New soldier 1"]).read_bytes())


def listings_index(path: Path, shadow_first: bool = False, parts=hs.LISTED) -> None:
    """A game index holding the US rifle squad's figures' listings, as test_horsesquad's (by place: t_stand, b_stand,
    t_tir); `shadow_first`: each figure's shadow copy written before it, listing other clips (a copy the game's later
    pack replaced: never the squad's listings)."""
    db = sqlite3.connect(path)
    db.executescript("CREATE TABLE object (id INTEGER, address TEXT, shadow INTEGER);"
                     "CREATE TABLE ref (src INTEGER, path TEXT, dst INTEGER);"
                     "CREATE TABLE value (object INTEGER, path TEXT, text TEXT);")
    n = 1000
    for k, part in enumerate(parts):
        copies = [(k + 50, 1, (("t_old", "Fusilier_OldLOD0"),)), (k + 1, 0, (("t_tir", "Fusilier_TirLOD0"),
                                                                                ("t_stand", "Fusilier_standlod0"),
                                                                                ("b_stand", "Fusilier_standlod0")))]
        for obj, shadow, rows in (copies if shadow_first else copies[::-1]):
            if not shadow_first and shadow:
                continue
            db.execute("INSERT INTO object VALUES (?, ?, ?)", (obj, hs.UNIT + ":" + part, shadow))
            for place, (key, file) in zip((10, 2, 3), rows):
                n += 1
                db.execute("INSERT INTO ref VALUES (?, ?, ?)", (obj, f"ResourceAnimation[{place}].v", n))
                db.execute("INSERT INTO value VALUES (?, ?, ?)", (obj, f"ResourceAnimation[{place}].k", key))
                db.execute("INSERT INTO value VALUES (?, 'FileName', ?)",
                           (n, f"WW2\\Res3D\\Units\\Common\\{file}.Ase2NdfBin"))
    db.commit()
    db.close()


LISTED_ROWS = [("t_stand", "fusilier_standlod0"), ("b_stand", "fusilier_standlod0"), ("t_tir", "fusilier_tirlod0")]


class TheBuilderAndItsIndex(unittest.TestCase):
    """rusemod.horsesquad's index argument and scratch folder, on a made-up game folder (the Studio tests' own packs:
    no horse, no rifleman in them)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "game"
        write_game(self.game)

    def test_the_index_given_is_the_one_its_listings_come_from(self):
        """B01 and B02 (the index argument ignored): the files are the same bytes either way on this game (the two
        routes agree), so no test of the files can see it; the index is what saves reading the game's unit data. (The
        listings asked for are the US rifle squad's, no other squad being given: since a8b65194 the third argument.)"""
        seen = []

        class Stop(Exception):
            pass

        def listings(game, index, unit):
            seen.append((Path(game), index, unit))
            raise Stop
        index = self.root / "index.sqlite"
        listings_index(index)
        with mock.patch.object(hs, "_listings", listings), self.assertRaises(Stop):
            hs.horse_squad_glbs(self.game, self.root / "out", index=index, say=lambda line: None)
        self.assertEqual(seen, [(self.game, index, hs.UNIT)])

    def test_an_index_that_has_them_spares_the_game_s_unit_data(self):
        index = self.root / "index.sqlite"
        listings_index(index)
        with mock.patch.object(hs, "_listings_in_game", side_effect=AssertionError("the game's unit data read")):
            self.assertEqual(hs._listings(self.game, index), {p: LISTED_ROWS for p in hs.LISTED})

    def test_an_index_without_them_falls_back_to_the_game_s_unit_data(self):
        """B03 (an index without the listings not falling back): an index that hasn't one of the three figures, or
        no index, reads the game's unit data, as the docstring says."""
        index = self.root / "index.sqlite"
        listings_index(index, parts=hs.LISTED[:2])
        from_game = {p: [("t_stand", "fusilier_standlod0")] for p in hs.LISTED}
        with mock.patch.object(hs, "_listings_in_game", return_value=from_game) as read:
            self.assertEqual(hs._listings(self.game, index), from_game)
            self.assertEqual(hs._listings(self.game, None), from_game)
            self.assertEqual(hs._listings(self.game, self.root / "no-index.sqlite"), from_game)
        self.assertEqual(read.call_count, 3)

    def test_a_shadow_copy_listed_first_is_never_read(self):
        """B13 (the index's shadow copies read too): the game index holds a shadow copy of each figure (the plain
        copy's index: one per figure, written after it, so the order hides the mistake); written first here, with
        other listings, it must still not be read."""
        index = self.root / "index.sqlite"
        listings_index(index, shadow_first=True)
        self.assertEqual(hs._listings_in_index(index), {p: LISTED_ROWS for p in hs.LISTED})

    def test_its_scratch_folder_is_made_in_the_folder_given_and_goes(self):
        """B05 (the scratch folder made in the system's temporary folder) and B06 (left behind): made_from's
        docstring: a scratch folder in the folder given, removed after; here after a refusal (no horse in this
        game)."""
        made = []
        real = hs.tempfile.mkdtemp

        def mkdtemp(*args, **kw):
            made.append(Path(real(*args, **kw)))
            return str(made[-1])
        out = self.root / "out"
        with mock.patch.object(hs, "_listings", lambda game, index, unit: {p: LISTED_ROWS for p in hs.LISTED}), \
                mock.patch.object(hs.tempfile, "mkdtemp", mkdtemp), \
                self.assertRaisesRegex(hs.HorseSquadError, "Your game hasn't the model the Generic Horse is made from"):
            hs.made_from(self.game, out, say=lambda line: None)
        self.assertEqual([p.parent for p in made], [out])
        self.assertEqual(list(out.iterdir()), [])

    def test_a_horse_point_on_a_bone_it_leaves_out_is_refused(self):
        """B29 (not refused): a point of the horse leaning on a bone the combined skeleton leaves out would lean on a
        bone that isn't there; refused in words. The control: a point on a bone kept is renamed as the skeleton
        names it."""
        def part(bone):
            return modelin.Part("bip01", 0, [(0.0, 0.0, 0.0)] * 3, [(0.0, 0.0, 1.0)] * 3, [(0.0, 0.0)] * 3, [(0, 1, 2)],
                                skin=[[(bone, 255)]] * 3, tracks=None, draw=0, static=False)
        self.assertEqual(hs._horse_parts([part("bip01 pelvis")])[0].skin, [[("horse pelvis", 255)]] * 3)
        with self.assertRaisesRegex(hs.HorseSquadError, "leans on a bone the Generic Horse leaves out"):
            hs._horse_parts([part("bip01 footsteps")])


class TheSeatInTheClips(unittest.TestCase):
    def test_the_rider_s_root_is_set_against_the_horse_s_first_standing_frame(self):
        """B10 (set against the stand clip halfway): on the game's horse the two give the same bytes (its stand clip
        keeps its back still), and no test read _seat_in_clips on made-up data. A made-up stand clip whose mid-back
        bone moves (test_horsesquad's): at its first frame every bone is at rest, so the seat is a plain move, SEAT
        less the bone's rest place, worked out here by hand."""
        h = baf.skeleton(th.record(th.HORSE))
        raw = {hs.HORSE_CLIPS["stand"]: baf.build(th.clip(th.HORSE, 25, 0.8, "bip01 spine1"))}
        spine1 = (5 + 10 + 12, 0, 100 + 2 + 3)       # (the mid-back bone at rest, as test_horsesquad works it out)
        want = [[1.0, 0.0, 0.0, hs.SEAT[0] - spine1[0]], [0.0, 1.0, 0.0, hs.SEAT[1] - spine1[1]],
                [0.0, 0.0, 1.0, hs.SEAT[2] - spine1[2]], [0.0, 0.0, 0.0, 1.0]]
        got = hs._seat_in_clips(h, raw)
        self.assertLess(max(abs(got[i][j] - want[i][j]) for i in range(4) for j in range(4)), 1e-9, got)


class TheRidersParts(unittest.TestCase):
    def test_a_point_leaning_on_the_legs_more_than_half_is_left_out(self):
        """B27 (up to 60% kept): on the game's rifleman no point leans on his legs between half and 60%, so the files
        are the same bytes, and no test read _rider_parts on made-up data. Here a point at 128 of 255 on a thigh goes
        with its triangle, one at 127 stays (its thigh's share given to the rest), and what stays is moved up by SEAT."""
        part = modelin.Part("bip01", 0, [(0.0, 0.0, 100.0), (5.0, 0.0, 100.0), (0.0, 5.0, 60.0), (5.0, 5.0, 60.0)],
                            [(0.0, 0.0, 1.0)] * 4, [(0.0, 0.0)] * 4, [(0, 1, 2), (0, 1, 3)],
                            skin=[[("bip01 pelvis", 255)], [("bip01 pelvis", 255)],
                                  [("bip01 pelvis", 127), ("bip01 l thigh", 128)],
                                  [("bip01 pelvis", 128), ("bip01 l thigh", 127)]], tracks=None, draw=0, static=False)
        (got,) = hs._rider_parts([part])
        sx, sy, sz = hs.SEAT
        self.assertEqual(got.triangles, [(0, 1, 2)])
        self.assertEqual(got.positions, [(0.0 + sx, 0.0 + sy, 100.0 + sz), (5.0 + sx, 0.0 + sy, 100.0 + sz),
                                         (5.0 + sx, 5.0 + sy, 60.0 + sz)])
        self.assertEqual(got.skin, [[("bip01 pelvis", 255)]] * 3)


@unittest.skipUnless(GAME is not None and GAME.is_dir(), "RUSE_GAME names no game folder")
class TheBuilderOnTheGame(unittest.TestCase):
    def test_a_bazooka_man_on_other_bones_is_refused(self):
        """B28 (not refused): a game whose bazooka man isn't on the rifleman's bones (one bone named otherwise here)
        would give his model a skeleton it wasn't made for; refused in words, nothing made."""
        real, calls = hs._record_of, []

        def record_of(name, meshes, skels):
            blob = real(name, meshes, skels)
            calls.append(name)
            if len(calls) != 3:          # (made_from reads the horse's, the rifleman's, then the bazooka man's)
                return blob
            sk = baf.skeleton(blob)
            names = list(sk["names"])
            names[-1] += " other"
            return baf.skeleton_bytes(names, sk["parents"], sk["bind"], sk["local"], sk["world"], sk["index"])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(hs, "_record_of", record_of), \
                self.assertRaisesRegex(hs.HorseSquadError, "bazooka man isn't on the rifleman's bones"):
            hs.horse_squad_glbs(GAME, Path(tmp) / "out", index=INDEX, say=lambda line: None)
        self.assertEqual(len(calls), 3)


@unittest.skipUnless(GAME is not None and GAME.is_dir() and INDEX is not None and INDEX.is_file() and PASSED is not None
                     and (PASSED / "horse-squad-rifle-death.glb").is_file()
                     and (PASSED / "horse-squad-bazooka-death.glb").is_file(),
                     "RUSE_GAME, the game index or the two files the game test passed with aren't named")
class TheRealBuilderThroughTheAdd(unittest.TestCase):
    def test_the_add_with_the_real_builder_gives_the_copy_s_files(self):
        """The Units tab's Add with the real builder (no stand-in): done; the builder's two files kept in the platform
        folder are the bytes the game test passed with; the mod is the one the copy's own calls make with those two
        files (make_horse_studio2_test.py's: a new unit from the US rifle squad, Import model of each), but for each
        model record's source file ("from" and the report's "file"), its era_units.json and its credit line. Then
        taken out again."""
        rifle, heavy = PASSED / "horse-squad-rifle-death.glb", PASSED / "horse-squad-bazooka-death.glb"
        home = Path(tempfile.mkdtemp(prefix="review-tests-"))
        self.addCleanup(shutil.rmtree, home, True)
        api = StudioApi(index_path=INDEX, game_dir=GAME, home=home)
        one = Path(api.new_mod("By hand")["current"])
        unit = api.new_unit(SQUAD, "Generic Horse", 5, group="new")["address"]
        api.model_import(unit, str(rifle))
        api.model_import(unit, str(heavy), kind="bazooka")
        two = Path(api.new_mod("Added")["current"])
        fresh = tree(two)
        self.assertIs(sys.modules.get(horse_squad.BUILDER), hs)      # (the real builder, no stand-in, is what it gets)
        view = finished(api, api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual((view["state"], view["message"]), ("done", "Generic Horse is in your mod."))
        self.assertEqual(view["result"], {"address": unit, "name": "Generic Horse"})
        kept = home / horse_squad.FOLDER
        self.assertEqual(sorted(os.listdir(kept)), sorted(hs.FILES.values()))      # nothing of the build left
        self.assertEqual((kept / hs.FILES["rifle"]).read_bytes(), rifle.read_bytes())
        self.assertEqual((kept / hs.FILES["bazooka"]).read_bytes(), heavy.read_bytes())
        by_hand, added = tree(one), tree(two)
        self.assertEqual(json.loads(added.pop(era_units.INDEX)), {KEY: unit})
        self.assertEqual(added.pop(era_units.CREDITS).decode("utf-8").replace("\r\n", "\n"),
                         "# Made for RUSE 2.0\n\n- Generic Horse (WWII, USA): by sneadtristen6.\n")
        by_hand.pop("mod.toml"), added.pop("mod.toml")
        self.assertEqual(sorted(added), sorted(by_hand))
        differ = {}
        for name in sorted(by_hand):
            if added[name] == by_hand[name]:
                continue
            if name.endswith(".json"):   # a model's record names the file it was made from, in two places
                a, b = json.loads(by_hand[name]), json.loads(added[name])
                came = b.pop("from", None)
                a.pop("from", None)
                for record in (a, b):
                    (record.get("report") or {}).pop("file", None)
                if a == b and Path(came).parent == kept and Path(came).name in hs.FILES.values():
                    continue
            differ[name] = (len(by_hand[name]), len(added[name]))
        self.assertEqual(differ, {})
        out = api.era_unit_remove(KEY)
        self.assertEqual(out["removed"], unit)
        left = tree(two)
        self.assertEqual(json.loads(left.pop(era_units.INDEX)), {})
        self.assertEqual([ln for ln in left.pop("src/studio.rndf").decode("utf-8").splitlines()
                          if ln.strip() and not ln.startswith("//")], [])
        self.assertEqual(left, fresh)


if __name__ == "__main__":
    unittest.main()
