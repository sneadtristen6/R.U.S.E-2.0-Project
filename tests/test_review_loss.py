"""Review of feat/anim-decoy-blender at 07a688b5, the "silent loss" lens (rule R1: nothing the modder made dropped, and no
failure swallowed, without a word to the modder): the Horse Squad added from the Units tab (ruse_studio.horse_squad)
where it meets the Studio's existing calls (delete_unit, era_unit_remove, model_resize, model_place, models_resize_all,
RUSE Decoy's Change its animations in Blender, Change it in Blender, Export mod), judged on the mod's files on disk.

Each test here FAILS on 07a688b5 by design, for the fault it names, until that fault is fixed:
- the unit page's Delete on a Horse Squad leaves files/models/<unit>@bazooka.glb and .json, which stop the next Test in
  game ("no mod in the set makes a new unit ...", the build's own words);
- an add that fails once the heavy-weapon soldier's model is written (the add's own bones check, or the record not
  written) leaves that file too, though the job says it wasn't added;
- the add's take-back takes out a copy of the US rifle squad the modder made while the add ran;
- a take-back that itself fails is swallowed: the job says the Horse Squad wasn't added while all of it is in the mod;
- two Studio windows: the other window switching the mod during the add leaves a half-made Horse Squad;
- Resize, Move and the resize of every ground unit put back the animation a modder changed in RUSE Decoy;
- the platform folder's horse_squad/ files, made again differently, change an older mod's Horse Squad on its next
  Resize, without a word;
- Change it in Blender on the Horse Squad opens the game's rifleman, not its own model, and Bring back the model drops
  its 25 animations without a word;
- a material back from Blender with the plain 144 (renamed or new there) is named in the import's report only, which
  no page shows;
- with no era downloaded on this PC, adding the Horse Squad drops the era units' credit lines, and taking it out
  deletes the credits file;
- Export mod leaves the credits file (sneadtristen6's line and the era makers') out of the package, and packs the
  Horse Squad's model records naming the platform folder's files by full path (the player's Windows user name);
- a failed read of the game's unit data is said as "your game hasn't the animations".

On the Studio tests' made-up game (WithMod) where the models aren't needed; on the game where they are (RUSE_GAME, the
Studio's index RUSE_STUDIO_INDEX and the passed copy's two files RUSE_HORSE_SQUAD_GLBS, as tests/test_horse_squad.py;
skipped without them). Temporary folders go where RUSE_TEST_TMP says (else the system's)."""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)
from test_animglb import Blenderish
from test_horse_squad import GAME, HEAVY, INDEX, RIFLE, finished, stand_in, tree
from test_studio import WithMod
from rusemod import anim, baf, gltf, horsesquad, models, package
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits

KEY, SQUAD = horse_squad.KEY, horse_squad.SQUAD
LIBERTY = "WWI|USA|Mark VIII Liberty"
TMP = os.environ.get("RUSE_TEST_TMP") or None
# the riflemen's file of before the horse's fall (2026-11-10): what the platform folder holds when made differently
PREFALL = Path(os.environ.get("RUSE_HORSE_PREFALL_RIFLE") or "D:/RUSE-2.0/scratch/animmodels/horse-squad-rifle.glb")
ON_THE_GAME = GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file()
WHY_SKIPPED = ("RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of the copy "
               "that passed in the game aren't there")


def era_library(folder: Path) -> Path:
    """An era units library with one WWI unit (no model) copying the M4 Sherman, as test_horse_squad's."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": [
        {"key": LIBERTY, "era": "WWI", "nation": "USA", "name": "Mark VIII Liberty",
         "in_place_of": "", "card": "Heavy Tank", "building": "Armor base",
         "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman", "copies_name": "", "game_nation": 0,
         "factory": 10, "aircraft": False, "model": None, "fits": True, "picture": None,
         "credit": {"title": "Liberty model", "author": "maker", "licence": "CC-BY 4.0",
                    "url": "https://example.org/Liberty", "extra": ""}}]}), encoding="utf-8")
    return folder


class Closed:
    """A stand-in for the Blender the Studio started, closed again."""

    def poll(self):
        return 0


@unittest.skipUnless(ON_THE_GAME, WHY_SKIPPED)
class OnTheGame(unittest.TestCase):
    """The Horse Squad added through the Studio's own Add (its builder standing in with the passed copy's two files:
    the real builder makes the same bytes) into a mod with the modder's own work in it: a copy of the US rifle squad
    and an era unit with its credit line."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="review-loss-", dir=TMP))
        self.addCleanup(shutil.rmtree, self.home, True)
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(era_library(self.home / "eralib"))})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.api = self.studio()
        self.mod = Path(self.api.new_mod("Mine")["current"])
        self.rifles = self.api.new_unit(SQUAD, "My Rifles", 5, group="new")["address"]
        self.liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]

    def studio(self):
        return StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")

    def add(self, api=None, heavy=HEAVY, during=None) -> dict:
        api = api or self.api
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, heavy, during=during)}):
            return finished(api, api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])

    def kind_files(self, tail: str = "Descriptor_Unit_Horse_Squad") -> list:
        models = self.mod / "files" / "models"
        return sorted(p.name for p in models.glob(f"{tail}@*")) if models.is_dir() else []

    # --- taking it away again ---
    def test_delete_on_its_unit_page_leaves_no_file_that_stops_the_build(self):
        """The unit page's Delete (delete_unit) on a Horse Squad: its heavy-weapon soldier's model stays in
        files/models, and the next Test in game stops on it (seen through the real build, a dry run: "mine:
        files/models/Descriptor_Unit_Horse_Squad@bazooka.glb: no mod in the set makes a new unit
        Descriptor_Unit_Horse_Squad")."""
        view = self.add()
        self.assertEqual(view["state"], "done")
        self.assertEqual(self.kind_files(), ["Descriptor_Unit_Horse_Squad@bazooka.glb",
                                             "Descriptor_Unit_Horse_Squad@bazooka.json"])
        address = view["result"]["address"]
        try:
            self.api.delete_unit(address)
        except StudioError:                          # (refused in words: the Horse Squad stays whole)
            self.assertIn(address, ModEdits(self.mod).new_units)
            return
        self.assertEqual(self.kind_files(), [])

    # --- an add that fails half way ---
    def test_an_add_whose_bones_check_fails_leaves_nothing(self):
        """The builder's heavy-weapon soldier on the game soldier's bones (the case the add's own check is for): the
        job says it wasn't added, and his model and its record stay in files/models (they stop the build as above)."""
        lib = models.Library(GAME)
        try:
            made = gltf.export(lib, [lib.find(horsesquad.BAZOOKA, lighter=False) or horsesquad.BAZOOKA],
                               self.home / "soldier", rest_bones=True)
        finally:
            lib.close()
        before = tree(self.mod)
        view = self.add(heavy=Path(made[0]["file"]))
        self.assertEqual((view["state"], view["message"]), (
            "failed", "The Generic Horse's two models didn't come in on the same bones, so it wasn't added. Please "
                      "report this."))
        self.assertEqual(self.kind_files(), [])
        self.assertEqual(tree(self.mod), before)

    def test_an_add_that_fails_once_the_bazooka_mans_model_is_written_leaves_nothing(self):
        """His model written, then his record not (a full disk, a file held by another program): the job fails, and
        files/models/<unit>@bazooka.glb stays (it stops the build as above)."""
        real = StudioApi._kind_skeleton

        def then_fails(target, report):
            real(target, report)
            raise OSError(28, "No space left on device")

        before = tree(self.mod)
        with mock.patch.object(StudioApi, "_kind_skeleton", staticmethod(then_fails)):
            view = self.add()
        self.assertEqual(view["state"], "failed")
        self.assertEqual(self.kind_files(), [])
        self.assertEqual(tree(self.mod), before)

    def test_the_take_back_leaves_a_copy_the_modder_made_meanwhile(self):
        """While the add runs, the modder copies the US rifle squad (the page's own call, from another thread); the add
        then fails: its take-back deletes the modder's copy as well, as 'not in the mod before and made from the US
        rifle squad'."""
        real = StudioApi.model_import
        ready, done, made = threading.Event(), threading.Event(), {}

        def importing(api, address, file=None, *a, **kw):
            got = real(api, address, file, *a, **kw)
            if not kw.get("kind"):            # the riflemen's model in: the modder's click lands now
                ready.set()
                done.wait(120)
                raise StudioError("The Generic Horse's two models didn't come in on the same bones, so it wasn't "
                                  "added. Please report this.")
            return got

        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}), \
                mock.patch.object(StudioApi, "model_import", importing):
            job = self.api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"]
            try:
                self.assertTrue(ready.wait(600))
                try:
                    made["copy"] = self.api.new_unit(SQUAD, "Second Rifles", 5, group="new")["address"]
                except StudioError:               # (refused in words while the add runs: nothing of his to lose)
                    made["copy"] = None
            finally:
                done.set()
            view = finished(self.api, job)
        self.assertEqual(view["state"], "failed")
        units = ModEdits(self.mod).new_units
        self.assertIn(self.rifles, units)               # (in the mod before the add: kept)
        if made["copy"] is not None:
            self.assertIn(made["copy"], units)          # the modder's own copy, made while the add ran

    def test_a_take_back_that_fails_is_not_said_as_not_added(self):
        """The add's check fails and its take-back can't take the models out (a file another program holds): the take-
        back's failure is swallowed, the job says the Horse Squad 'wasn't added', and the whole of it is in the mod
        (its unit, both models, 25 clips, its era_units.json line and credit line; the Units tab shows it added)."""
        def check(api, address):
            raise StudioError("The Generic Horse's two models didn't come in on the same bones, so it wasn't added. "
                              "Please report this.")

        def remove(api, address, kind=None):
            raise PermissionError(13, "Permission denied")

        with mock.patch.object(StudioApi, "_horse_check", check), \
                mock.patch.object(StudioApi, "model_import_remove", remove):
            view = self.add()
        left = "$/GFX/Everything/Descriptor_Unit_Horse_Squad" in ModEdits(self.mod).new_units
        self.assertEqual(view["state"], "failed")
        self.assertFalse(left and "wasn't added" in view["message"], (left, view["message"]))

    def test_another_window_switching_the_mod_leaves_nothing_half_made(self):
        """A second Studio window on the same platform folder (nothing stops the app being opened twice) switches the
        mod being edited while the first window's add imports the models: the guard is the first window's only, so the
        switch goes through, the add fails ("Only a new unit made in this mod can get a model of its own"), and its
        take-back looks in the other mod: the first mod keeps a half-made Horse Squad (its unit and riflemen's model,
        no heavy-weapon soldier's, its era_units.json and credit lines)."""
        other_window = self.studio()
        second = Path(self.api.new_mod("Second")["current"])
        self.api.choose_mod(str(self.mod))
        before = tree(self.mod)
        real = StudioApi.model_import
        switched = []

        def importing(api, address, file=None, *a, **kw):
            got = real(api, address, file, *a, **kw)
            if not kw.get("kind") and api is self.api and not switched:
                try:
                    other_window.choose_mod(str(second))
                    switched.append("switched")
                except StudioError:               # (refused in words: the mod stays the one the add writes in)
                    switched.append("refused")
            return got

        with mock.patch.object(StudioApi, "model_import", importing):
            view = self.add()
        self.assertEqual(len(switched), 1)
        tail = "Descriptor_Unit_Horse_Squad"
        if view["state"] == "done":                     # all of it, in the mod it was added to
            self.assertEqual(self.kind_files(tail), [f"{tail}@bazooka.glb", f"{tail}@bazooka.json"])
            self.assertTrue((self.mod / "files" / "models" / f"{tail}.glb").is_file())
        else:
            self.assertEqual(tree(self.mod), before)

    # --- its model fitted again ---
    def decoy_change(self, address: str, animation: str = "hr_b_stand", bone: str = "horse spine") -> bytes:
        """One bone of one of its model's own animations turned through RUSE Decoy's Change its animations in Blender
        (decoy_blender, decoy_blender_back; Blender's part: tests/test_animglb.py's stand-in). Returns the clip file's
        bytes after."""
        started = []
        self.api._blender = lambda: Path("C:/b/blender.exe")
        with mock.patch("rusemod.blender.open_model_to_change",
                        lambda b, model, send, words: started.append((model, send)) or Closed()):
            self.api.decoy_blender(address, "us")
        start, send = started[-1]
        Path(send).write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=(animation, bone, baf.axis_angle("x", 20.0))))
        got = self.api.decoy_blender_back(address, "us")
        self.assertEqual(got["changed"], [animation])
        return self.clip(address, animation)

    def clip(self, address: str, animation: str) -> bytes:
        unit = address.rsplit("/", 1)[-1]
        return (self.mod / anim.OWN / unit / anim.own_animations(self.mod, unit)["animations"][animation]).read_bytes()

    def test_resize_move_and_every_ground_unit_keep_a_change_made_in_ruse_decoy(self):
        """Its model is fitted again from the platform folder's file (its record's "from") and its animations taken in
        again from it: an animation changed in RUSE Decoy goes back to the file's, the answers saying nothing
        ("resized Horse Squad 1", "1 model(s) done.")."""
        address = self.add()["result"]["address"]
        for how, call in (("Resize", lambda: self.api.model_resize(address, 1.0)),
                          ("Move", lambda: self.api.model_place(address, [0, 0, 0])),
                          ("every ground unit", lambda: finished(self.api,
                                                                 self.api.models_resize_all("ground", "game")["job"]))):
            with self.subTest(how=how):
                changed = self.decoy_change(address)
                try:
                    call()
                except StudioError:                  # (refused in words: nothing changed)
                    pass
                self.assertEqual(self.clip(address, "hr_b_stand"), changed)

    def test_its_files_made_again_differently_dont_change_an_older_mods_horse_squad_without_a_word(self):
        """The platform folder's horse_squad/ files are every mod's: made again differently (another builder, another
        game; here the riflemen's file of before the horse's fall), the next Resize in a mod made before takes them in,
        its 25 animations 24, the fall gone, nothing said."""
        if not PREFALL.is_file():
            self.skipTest(f"{PREFALL} isn't there")
        address = self.add()["result"]["address"]
        unit = address.rsplit("/", 1)[-1]
        before = sorted(anim.own_animations(self.mod, unit)["animations"])
        shutil.copyfile(PREFALL, self.home / horse_squad.FOLDER / RIFLE.name)
        try:
            answer = self.api.model_resize(address, 1.0)
        except StudioError:
            return                                   # refused in words: nothing changed
        after = sorted(anim.own_animations(self.mod, unit)["animations"])
        said = " ".join((answer.get("model") or {}).get("notes") or [])
        self.assertTrue(after == before or said, (len(before), len(after), sorted(set(before) - set(after))))

    def test_its_records_in_an_exported_mod_name_no_folder_of_the_players(self):
        """Export mod packs files/models/*.json as they are: the Horse Squad's records name the file each model was
        made from by its full path, in the platform folder (%LOCALAPPDATA%\\RUSE Mod Platform\\horse_squad\\... on a
        player's PC: his Windows user name in it), so it goes out with every shared mod that has the Horse Squad."""
        self.assertEqual(self.add()["state"], "done")
        # (read in the EXPORTED file since 2026-11-13: the owner's choice for FL-110, "Keep file name only", is made
        # when the mod is packed; the mod's own records on his PC keep the full path, which Resize and Move need. The
        # test read the mod folder's files before, as the export then packed them unchanged.)
        import zipfile
        out = package.pack(self.mod, self.home / "exported-for-this-test")
        with zipfile.ZipFile(out) as z:
            packed = {n: z.read(n).decode("utf-8", errors="replace") for n in z.namelist() if n.endswith(".json")}
        self.assertIn("files/models/Descriptor_Unit_Horse_Squad.json", packed)
        naming = [name for name, text in packed.items()
                  if str(self.home).lower() in text.replace("\\\\", "\\").lower()]
        self.assertEqual(naming, [])

    def test_change_it_in_blender_opens_its_own_model(self):
        """Change it in Blender (model_blender: the Model row's, on a squad's page when its squad card can't be read)
        opens the game's US rifleman (35 bones, no horse, no animation) for the Horse Squad; brought back as it was
        opened, the Horse Squad's riflemen are on the game soldier's bones and its 25 animations are gone, no note."""
        from rusemod.modelin import glb_document
        address = self.add()["result"]["address"]
        started = []
        self.api._blender = lambda: Path("C:/b/blender.exe")
        with mock.patch("rusemod.blender.open_model_to_change",
                        lambda b, model, send, words: started.append((model, send)) or Closed()):
            try:
                self.api.model_blender(address, "us")
            except StudioError:                      # (refused in words: nothing opened, nothing to bring back)
                return
        doc, _bin = glb_document(Path(started[0][0]).read_bytes())
        self.assertTrue(any(str(n.get("name", "")).startswith("horse ") for n in doc.get("nodes", [])),
                        f"what went out to Blender: {Path(started[0][0]).name}, no horse in it")


class OnTheMadeUpGame(WithMod):
    """Its credit line beside the era units' (its models' import stood in for, as test_horse_squad's own test does: the
    made-up game has no models to fit to)."""

    def setUp(self):
        super().setUp()
        self.lib = era_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        self.patch_lib = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(self.lib)})
        self.patch_lib.start()
        self.addCleanup(self.patch_lib.stop)
        self.files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = self.files / "rifle.glb", self.files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def add(self) -> dict:
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            return finished(self.api, self.api.horse_squad_add(0, 10, "Cavalry", 7, group="new")["job"])

    def test_the_era_units_credit_lines_stay_when_the_era_isnt_on_this_pc(self):
        """A mod with an era unit and its credit line (CC BY asks for it), edited on a PC without that era downloaded
        (another PC, or its download gone): adding the Horse Squad writes the credits file with its line alone, and
        taking it out deletes the file, the era unit still in the mod."""
        folder = Path(self.api.new_mod("Credits")["current"])
        liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        credits = folder / era_units.CREDITS
        line = '- Mark VIII Liberty (WWI, USA): "Liberty model" by maker, CC-BY 4.0, https://example.org/Liberty.'
        self.assertIn(line, credits.read_text(encoding="utf-8"))
        # no era downloaded on this PC now
        with mock.patch.dict(os.environ), mock.patch("ruse_studio.era_units.library_dir", lambda home=None: None):
            os.environ.pop(era_units.LIBRARY_ENV, None)
            self.assertEqual(self.add()["state"], "done")
            self.assertIn(liberty, ModEdits(folder).new_units)
            self.assertIn(line, credits.read_text(encoding="utf-8"))
            self.api.era_unit_remove(KEY)
            self.assertTrue(credits.is_file())
            self.assertIn(line, credits.read_text(encoding="utf-8"))

    def test_export_carries_its_credit(self):
        """Export mod packs the files package.files_of lists: the credits file the Horse Squad's line (and every era
        unit maker's) is written to isn't one of them, so a shared mod goes out without them."""
        folder = Path(self.api.new_mod("Shared")["current"])
        self.assertEqual(self.add()["state"], "done")
        self.assertIn("sneadtristen6", (folder / era_units.CREDITS).read_text(encoding="utf-8"))
        packed = [p.relative_to(folder).as_posix() for p in package.files_of(folder)]
        self.assertIn(era_units.CREDITS, packed)


class ThePage(unittest.TestCase):
    UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"

    def test_a_material_back_from_blender_with_the_plain_144_is_named_to_the_modder(self):
        """Bring back the model names each material that came back with the plain 144 (renamed or new in Blender, its
        alpha picture gone) in its report's "blender_alpha" and notes (ruse_studio.modelblender._alpha_said): no page
        reads either (the Bring back buttons say "model_blender_done" or "model_kind_done" and redraw), and the squad
        card's Bring my changes back drops rusemod.gltf.with_alpha's word on each material ([0]), so the modder is told
        of none of them."""
        import re
        pages = {p.name: p.read_text(encoding="utf-8") for p in self.UI.glob("*.js") if p.name != "fake-api.js"}
        reading = [name for name, text in pages.items() if re.search(r"blender_alpha|\w\.notes\b", text)]
        self.assertTrue(reading, "no page reads an import's notes or blender_alpha")


@unittest.skipUnless(GAME is not None and GAME.is_dir(), "RUSE_GAME names no game folder")
class TheBuildersReading(unittest.TestCase):
    def test_a_read_that_fails_isnt_said_as_animations_missing(self):
        """The squad's listings read from the game's unit data (when the Studio's index hasn't them): a read that
        fails (here an input/output error) is swallowed and said as "Your game's US rifle squad hasn't the animations
        the Horse Squad's riders play."."""
        with mock.patch("rusemod.build.load_pack", side_effect=OSError(5, "Input/output error")):
            try:
                horsesquad._listings_in_game(GAME)
            except horsesquad.HorseSquadError as exc:
                self.assertNotIn("hasn't the animations", str(exc))
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
