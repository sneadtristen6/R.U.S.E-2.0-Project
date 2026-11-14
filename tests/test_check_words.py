"""The one check of the words group on the joined code (join/final1): two mistakes no test caught (the lead's planted
mistakes M2 and M5, join-trial-probes/mutants_fixes.py), and the routes the check found.

- M2: the unit page's Delete (delete_unit) on an era unit or the Horse Squad leaves its line in the mod's
  era_units.json and its credit line (era_units._era_forget not called): each must go with the unit, and the other
  units' stay.
- M5: the Horse Squad's add fails and its take-back can't take the unit out again (a file another program holds): the
  job must say that part of it is still in the mod, never only that it wasn't added.
- FINDING, failing on join/final1 by design until fixed (ItsAnimationsFileHeld): Take it out of my mod, or the unit
  page's Delete, on the Horse Squad while another program holds the mod's files/anim/units.toml deletes the unit and
  leaves its rows there and its clips' folder; the next build stops ("<mod>: files/anim/units.toml: no mod in the set
  makes a unit Descriptor_Unit_Horse_Squad, and the game has none of that name", seen in a dry build), and neither
  click can take them out any more ("Horse Squad isn't in this mod"). With the file locked (it can't be read), Take it
  out even says nothing (edits.remove_unit swallows the read's error).

EraLines on the Studio tests' made-up game (WithMod), the models' import standing in (nothing of the game's needed);
ItsAnimationsFileHeld on the game (RUSE_GAME, the Studio's index and the passed copy's two files, as
tests/test_horse_squad.py; skipped without them), Windows only (msvcrt)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)

from test_export_out import LIBERTY, era_library
from test_horse_squad import GAME, HEAVY, INDEX, RIFLE, finished, stand_in
from test_studio import WithMod
from rusemod import anim
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits

try:
    import msvcrt   # (a part of a file locked as another program locks it: Windows)
except ImportError:
    msvcrt = None

KEY = horse_squad.KEY
ON_THE_GAME = msvcrt is not None and GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file()
WHY_SKIPPED = ("RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of the copy "
               "that passed in the game aren't there, or this isn't Windows")
STILL_IN = ("The Generic Horse couldn't be added, and taking it back out failed too, so part of it is still in your mod: "
            "take it out of your mod on its page in the Units tab, or delete it on its unit page.")


class EraLines(WithMod):
    """A mod with the Liberty (an era unit) and the Horse Squad, its models' import standing in."""

    def setUp(self):
        super().setUp()
        lib = era_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        env = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        env.start()
        self.addCleanup(env.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")
        self.mod = Path(self.api.new_mod("Lines")["current"])

    def add_horse(self, **patches) -> dict:
        check = patches.pop("check", lambda api, address: None)
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", check):
            others = [mock.patch.object(StudioApi, name, value) for name, value in patches.items()]
            for p in others:
                p.start()
            try:
                return finished(self.api, self.api.horse_squad_add(0, 10, "Cavalry", 7, group="new")["job"])
            finally:
                for p in reversed(others):
                    p.stop()

    def record(self) -> dict:
        f = self.mod / era_units.INDEX
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}

    def credits(self) -> str:
        f = self.mod / era_units.CREDITS
        return f.read_text(encoding="utf-8") if f.is_file() else ""

    # --- M2 ---
    def test_delete_on_its_unit_page_takes_its_era_line_and_credit_and_keeps_the_others(self):
        liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        view = self.add_horse()
        self.assertEqual(view["state"], "done", view.get("message"))
        horse = view["result"]["address"]
        self.assertEqual(self.record(), {LIBERTY: liberty, KEY: horse})
        self.assertIn("sneadtristen6", self.credits())
        self.assertIn("Liberty", self.credits())
        self.assertEqual(self.api.delete_unit(horse, "anyway")["deleted"], horse)
        self.assertEqual(self.record(), {LIBERTY: liberty})          # its line gone, the Liberty's kept
        self.assertNotIn("sneadtristen6", self.credits())             # its credit gone
        self.assertIn("Liberty", self.credits())                      # the Liberty's kept
        self.assertEqual(self.api.delete_unit(liberty, "anyway")["deleted"], liberty)
        self.assertEqual(self.record(), {})
        self.assertNotIn("Liberty", self.credits())

    # --- M5 ---
    def test_a_take_back_that_leaves_the_unit_says_part_of_it_is_still_in_the_mod(self):
        """The add's check fails; its take-back can't delete the unit (its unit file held by another program): the
        unit stays, and the job says so, with what to do."""
        def check(api, address):
            raise StudioError("The Generic Horse's two models didn't come in on the same bones, so it wasn't added. "
                              "Please report this.")

        def delete(api, address, researched=None):
            raise PermissionError(13, "Permission denied", str(self.mod / "src" / "units.rndf"))

        view = self.add_horse(check=check, delete_unit=delete)
        self.assertEqual(view["state"], "failed")
        self.assertIn("$/GFX/Everything/Descriptor_Unit_Cavalry", ModEdits(self.mod).new_units)
        self.assertEqual(view["message"], STILL_IN)


@unittest.skipUnless(ON_THE_GAME, WHY_SKIPPED)
class ItsAnimationsFileHeld(unittest.TestCase):
    """The Horse Squad added (its builder standing in with the passed copy's two files, the Studio's own import
    running), then taken away while another program holds the mod's files/anim/units.toml: "open", a handle open on it
    (it reads, but no new file can take its place); "lock", a part of it locked too (it can't be read either). The lock
    goes after the click. A unit gone from the mod with its rows left in units.toml stops every build after ("<mod>:
    files/anim/units.toml: no mod in the set makes a unit Descriptor_Unit_Horse_Squad, and the game has none of that
    name"), and the Studio can't take them out any more (the unit isn't in the mod for Take it out or Delete): so the
    unit stays (said in words, try again), or goes with its rows and its clips' folder."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="cw-", dir=os.environ.get("RUSE_TEST_TMP") or None))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.mod = Path(self.api.new_mod("Held")["current"])
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            view = finished(self.api, self.api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.address = view["result"]["address"]
        self.tail = self.address.rsplit("/", 1)[-1]
        self.table = self.mod / anim.UNITS
        self.assertIn(self.tail, anim.read_units(self.mod))

    def taken_away(self, how: str, click) -> tuple:
        """`click` run while another program holds units.toml (`how`); returns (what it raised or None, the unit still
        in the mod, its rows left in units.toml, its clips' folder left)."""
        held = open(self.table, "rb")
        size = self.table.stat().st_size
        if how == "lock":
            msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, size)
        raised = None
        try:
            try:
                click()
            except (StudioError, OSError) as exc:
                raised = exc
        finally:
            if how == "lock":
                held.seek(0)
                msvcrt.locking(held.fileno(), msvcrt.LK_UNLCK, size)
            held.close()
        return (raised, self.address in ModEdits(self.mod).new_units, self.tail in anim.read_units(self.mod),
                (self.mod / anim.OWN / self.tail).is_dir())

    def check(self, how: str, click) -> None:
        raised, unit, rows, folder = self.taken_away(how, click)
        if unit:
            self.assertIsNotNone(raised, "the unit stayed and nothing was said")
        else:
            self.assertEqual((rows, folder), (False, False),
                             f"the unit is gone, its animations left (they stop the build); said: {raised!r}")

    def test_take_it_out_with_the_file_open_in_another_program(self):
        self.check("open", lambda: self.api.era_unit_remove(KEY, "anyway"))

    def test_take_it_out_with_the_file_locked_by_another_program(self):
        self.check("lock", lambda: self.api.era_unit_remove(KEY, "anyway"))

    def test_delete_on_its_unit_page_with_the_file_open_in_another_program(self):
        self.check("open", lambda: self.api.delete_unit(self.address, "anyway"))

    def test_delete_on_its_unit_page_with_the_file_locked_by_another_program(self):
        self.check("lock", lambda: self.api.delete_unit(self.address, "anyway"))


if __name__ == "__main__":
    unittest.main()
