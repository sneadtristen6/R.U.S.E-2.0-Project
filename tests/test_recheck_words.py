"""Recheck of the words group's fix on fix/horse-add (round 1, after 70de183f): the Horse Squad's Add said in words in
the Studio's language when a file can't be written, by routes the fix's own tests didn't take (review-loss F14: "an
OSError shows Python's own words ("[Errno 28] ...")"; the fix's report: said in words "for every step of the add job").

Each test here FAILS on 70de183f by design, for the case it names, until that case is said in words:
- the disk full while the riflemen's model is written into the mod (the Studio's own import writing it, not
  model_import replaced as a whole): the job says Python's "[Errno 28] No space left on device", the same in every
  language;
- the disk full while its animations are written into the mod: Python's "[Errno 28] No space left on device" inside
  the translated words "...: its animations can't be kept: {1}";
- the platform folder's file of an Add before, held open by another app while the new one replaces it: the job
  names the Add's own temporary file (removed right after), not the file held open;
- "every ground unit" resized while the Horse Squad's platform-folder file is locked by another app (review-loss F14:
  "The "every ground unit" skip line carries the English reason"): the line's reason is Python's "[Errno 13]
  Permission denied" in English with the Studio in French (Resize's own refusal the same: seen, not asserted).

The first two and the last on the game (RUSE_GAME, the Studio's index RUSE_STUDIO_INDEX and the passed copy's two files
RUSE_HORSE_SQUAD_GLBS, as tests/test_horse_squad.py; skipped without them), the disk full made at the write itself
(what a write raises then), the lock a real one (Windows' byte-range lock); the third on the Studio tests' made-up
game, on Windows (where a file held open can't be replaced). Nothing of the game's is written."""
import errno
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)

from test_horse_squad import GAME, HEAVY, INDEX, RIFLE, finished, stand_in
from test_horse_words import WithLibrary
from ruse_studio import horse_squad
from ruse_studio.api import StudioApi

ON_THE_GAME = GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file()
WHY_SKIPPED = ("RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of the copy "
               "that passed in the game aren't there")
REAL_WRITE = pathlib.Path.write_bytes
PYTHONS = ("Errno", "No space left on device")      # Python's own words for a full disk


def full_disk_at(which):
    """Path.write_bytes as on a full disk for the files `which` picks (what a write raises then); the rest written."""
    def write_bytes(self, data):
        if which(self):
            raise OSError(errno.ENOSPC, "No space left on device")
        return REAL_WRITE(self, data)
    return write_bytes


@unittest.skipUnless(ON_THE_GAME, WHY_SKIPPED)
class TheAddsOwnWritesOnAFullDisk(unittest.TestCase):
    """The Horse Squad's Add (its builder standing in with the passed copy's two files) into a new mod, the disk full
    when one of the mod's files is written by the Studio's own import."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="recheck-words-", dir=os.environ.get("RUSE_TEST_TMP") or None))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.api.new_mod("Full disk")

    def add_on_a_full_disk(self, which) -> dict:
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}), \
                mock.patch.object(pathlib.Path, "write_bytes", full_disk_at(which)):
            view = finished(self.api, self.api.horse_squad_add(0, 8, "Horse Squad", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "failed")
        return view

    def said_in(self, view: dict, lang: str) -> str:
        self.api.set_pref("lang", lang)
        try:
            return self.api.job(view["id"])["message"]
        finally:
            self.api.set_pref("lang", "us")

    def assert_in_words(self, view: dict) -> None:
        """In words in English (never Python's), and said again in the modder's language with none of Python's English
        left inside."""
        for words in PYTHONS:
            self.assertNotIn(words, view["message"])
        for lang in ("fr", "jpn", "fa"):
            said = self.said_in(view, lang)
            with self.subTest(lang=lang):
                self.assertNotEqual(said, view["message"])
                for words in PYTHONS:
                    self.assertNotIn(words, said)

    def test_its_riflemen_s_model_written_on_a_full_disk_is_said_in_words(self):
        """Seen on 70de183f: "horse-squad-rifle-death.glb: [Errno 28] No space left on device" in English, French and
        Japanese alike (api._fit_model / animmodel_calls._own_bones_fit turn the OSError into a StudioError with
        Python's words before the job's own OSError words can say it)."""
        view = self.add_on_a_full_disk(lambda p: p.name == "Descriptor_Unit_Horse_Squad.glb")
        self.assertEqual(view["lines"], ["build", "unit", "riflemen"])
        self.assert_in_words(view)

    def test_its_animations_written_on_a_full_disk_are_said_in_words(self):
        """Seen on 70de183f: "horse-squad-rifle-death.glb : ses animations ne peuvent pas être gardées : [Errno 28] No
        space left on device" in French (animmodel_calls._record_more's "{0}: its animations can't be kept: {1}")."""
        view = self.add_on_a_full_disk(lambda p: p.suffix == ".part" and "own" in p.parts)
        self.assert_in_words(view)


@unittest.skipUnless(sys.platform == "win32", "a file held open by another program stops its replace on Windows only")
class TheFileAnotherProgramHolds(WithLibrary):
    def test_the_platform_folder_s_file_another_program_holds_is_the_one_named(self):
        """Seen on 70de183f: "The Horse Squad couldn't be added: <platform folder>\\horse_squad\\.making-<8 letters>\\
        rifle.glb couldn't be read or written, because another program has it open..." (the Add's own temporary file,
        removed right after; Python's error names it first and the held file second, horse_squad._horse_file_error
        says the first)."""
        root = self.home / horse_squad.FOLDER
        root.mkdir(parents=True, exist_ok=True)
        held = root / self.rifle.name
        held.write_bytes(b"made by an Add before")
        self.api.new_mod("Held")
        with open(held, "rb"):       # (another program holding it, as Python's own open holds a file on Windows)
            with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}):
                view = finished(self.api, self.api.horse_squad_add(0, 10, "Horse Squad", 5, group="new")["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn(str(held), view["message"])
        self.assertNotIn(".making-", view["message"])


@unittest.skipUnless(ON_THE_GAME and sys.platform == "win32", WHY_SKIPPED + " (or this isn't Windows: its file lock)")
class TheEveryGroundUnitLine(unittest.TestCase):
    def test_a_horse_squad_whose_file_another_app_has_locked_is_skipped_with_why_in_the_studio_s_language(self):
        """Seen on 70de183f, the Studio in French: the line "skipped<TAB>Horse Squad<TAB>horse-squad-rifle-death.glb:
        [Errno 13] Permission denied" (the import's "{file}: {exc}", which no template says again; Resize's own
        refusal is the same English, seen, not asserted here)."""
        import msvcrt
        home = Path(tempfile.mkdtemp(prefix="recheck-words-", dir=os.environ.get("RUSE_TEST_TMP") or None))
        self.addCleanup(shutil.rmtree, home, True)
        api = StudioApi(index_path=INDEX, game_dir=GAME, home=home, instances=home / "copies")
        api.new_mod("Locked")
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            view = finished(api, api.horse_squad_add(0, 8, "Horse Squad", 5, None, None, None, "new")["job"])
        self.assertEqual(view["state"], "done")
        file = home / horse_squad.FOLDER / RIFLE.name
        size = file.stat().st_size
        api.set_pref("lang", "fr")
        self.addCleanup(api.set_pref, "lang", "us")
        with open(file, "rb") as held:
            msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, size)     # (another app's lock on the whole file)
            try:
                job = finished(api, api.models_resize_all("ground", "game")["job"])
            finally:
                held.seek(0)
                msvcrt.locking(held.fileno(), msvcrt.LK_UNLCK, size)
        lines = [line.split("\t") for line in job["lines"]]
        self.assertEqual([(ln[0], ln[1]) for ln in lines], [("skipped", "Horse Squad")])
        for words in ("Errno", "Permission denied"):
            self.assertNotIn(words, lines[0][2])


if __name__ == "__main__":
    unittest.main()
