"""A file the Studio couldn't read or write, said in words in the Studio's language, never in Python's own (the words
group, round 2: the recheck of round 1 found the Studio's own model import saying "[Errno 28] No space left on device"
on the Horse Squad's Add and on its animations, Resize every ground unit's skip line saying "[Errno 13] Permission
denied" with the Studio in French, and the Add naming its own temporary file in place of the file another program held:
tests/test_recheck_words.py).

- api.file_error's words (a full disk, a file another program holds or Windows didn't allow, one not there, else its
  error number), each in the ten other languages, and the file it names: the one the error names; of two, the one in
  the place a new file was being put, never the Studio's own new one; of two with one not there, the first; none named,
  the one being written for a full disk (always a write), else the one being read (a part of a file another program
  has locked fails part way, naming none), else the one being written. A file's number is never said as its name.
- api.oserror_of: a reader's own error with Python's words of an OSError inside (rusemod.rig.read_rig's "x.glb: [Errno
  13] Permission denied", raised while handling it) is found; one raised after an OSError in words of its own isn't.
- The Horse Squad's Add: a file error the Studio's import said in words (raised from its OSError) said in the Add's own
  words, that it wasn't added, naming the file being read when the error names none; any other refusal of the import
  passed on as it came.
- Resize every ground unit: a unit skipped for a file that couldn't be read or written says why in words in the
  Studio's language, naming that unit's model when the error names no file.
- On the game (RUSE_GAME, the Studio's index and the passed copy's two files, as tests/test_horse_squad.py; skipped
  without them): the import's reader failing on the Horse Squad's file (read_rig wraps the OSError in its own error),
  the import's look at its bones failing on it (once swallowed, then said as another reason), and a Resize whose
  model record can't be written (a full disk), each in words. Nothing of the game's is written."""
import errno
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy  # noqa: F401  (loaded once, before any test patches sys.modules: numpy can't load twice in a process)

from test_horse_squad import GAME, HEAVY, INDEX, RIFLE, finished, stand_in, tree
from test_horse_words import WithLibrary
from ruse_studio import era_units, errortext, horse_squad
from ruse_studio.api import StudioApi, StudioError, disk_full, file_error, file_named, oserror_of
from rusemod.anim import AnimError
from rusemod.modelin import ModelError

KEY, SQUAD = horse_squad.KEY, horse_squad.SQUAD
OTHERS = tuple(lang for lang in errortext.LANGS if lang != "us")
PYTHONS = ("Errno", "WinError", "Permission denied", "No space left", "Access is denied")   # Python's own words
ON_THE_GAME = GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file()
WHY_SKIPPED = ("RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of the copy "
               "that passed in the game aren't there")
KEPT, NEW = "C:\\Mods\\Mine\\files\\models\\Unit.glb", "C:\\Mods\\Mine\\files\\models\\Unit.part"
WRITING, READING = Path("C:/Mods/Mine/files/models/Unit.glb"), Path("D:/Downloads/horse.glb")
TRY_AGAIN = {
    "full": "The disk holding {0} is full. Make room on it, then try again.",
    "held": "{0} couldn't be read or written, because another program has it open or Windows didn't allow it. Close "
            "that program, then try again.",
    "gone": "{0} isn't there.",
    "plain": "{0} couldn't be read or written. Please report this.",
    "code": "{0} couldn't be read or written (error {1}). Please report this.",
}
ADD = {
    "full": "The Horse Squad couldn't be added: the disk holding {0} is full. Make room on it, then add it again.",
    "held": "The Horse Squad couldn't be added: {0} couldn't be read or written, because another program has it open "
            "or Windows didn't allow it. Close that program, then add it again.",
}


def entries() -> dict:
    import tomllib
    return tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))


def wrapped(exc: OSError, wrapper=ModelError, text="x.glb: {0}"):
    """`wrapper` raised as rusemod's readers raise it while handling `exc` (rusemod.rig.read_rig: `raise
    ModelError(f"{path.name}: {exc}") from None`), caught and returned."""
    try:
        try:
            raise exc
        except OSError as caught:
            raise wrapper(text.format(caught)) from None
    except wrapper as out:
        return out


class FileWords(unittest.TestCase):
    def test_the_file_named(self):
        """Of two (a file put in another's place), the one in that place; of two with one not there, the first; none
        named, the fallback; a file's number never."""
        put = PermissionError(errno.EACCES, "Access is denied", NEW, None, KEPT)
        self.assertEqual(file_named(put), KEPT)
        self.assertEqual(file_named(FileNotFoundError(errno.ENOENT, "Not found", NEW, None, KEPT)), NEW)
        self.assertEqual(file_named(PermissionError(errno.EACCES, "Permission denied", KEPT)), KEPT)
        self.assertEqual(file_named(PermissionError(errno.EACCES, "Permission denied"), WRITING), WRITING)
        self.assertEqual(file_named(OSError(errno.EBADF, "Bad file descriptor", 3), WRITING), WRITING)
        self.assertIsNone(file_named(OSError("a pack that ends early")))

    def test_the_words_and_the_file_they_name(self):
        cases = [
            # a full disk: always a write, the file being written when the error names none
            (OSError(errno.ENOSPC, "No space left on device"), TRY_AGAIN["full"].format(WRITING)),
            # another program holding it, or Windows not allowing it: named, else the file being read
            (PermissionError(errno.EACCES, "Access is denied", NEW, None, KEPT), TRY_AGAIN["held"].format(KEPT)),
            (PermissionError(errno.EACCES, "Permission denied"), TRY_AGAIN["held"].format(READING)),
            (FileNotFoundError(errno.ENOENT, "No such file or directory", str(READING)),
             TRY_AGAIN["gone"].format(READING)),
            (OSError(errno.EIO, "Input/output error"), TRY_AGAIN["code"].format(READING, errno.EIO)),
            (OSError("a pack that ends early"), TRY_AGAIN["plain"].format(READING)),
        ]
        if sys.platform == "win32":   # (Windows' own error numbers: ERROR_DISK_FULL, ERROR_HANDLE_DISK_FULL, another)
            cases += [
                (OSError(None, "There is not enough space on the disk", KEPT, 112), TRY_AGAIN["full"].format(KEPT)),
                (OSError(None, "The disk is full", None, 39), TRY_AGAIN["full"].format(WRITING)),   # (Python: EINVAL)
                (OSError(None, "The request could not be performed", KEPT, 1117),
                 TRY_AGAIN["code"].format(KEPT, 1117)),
            ]
        e = entries()
        for exc, expected in cases:
            with self.subTest(exc=repr(exc)):
                said = file_error(exc, WRITING, READING)
                self.assertIsInstance(said, StudioError)
                self.assertEqual(str(said), expected)
                for lang in OTHERS:
                    worded = errortext.worded(str(said), lang)
                    self.assertNotEqual(worded, expected, lang)
                    self.assertNotIn("couldn't", worded, lang)
                    for words in PYTHONS:
                        self.assertNotIn(words, worded, lang)
                    self.assertTrue(str(WRITING) in worded or str(READING) in worded or KEPT in worded, lang)
        # nothing being read: the file being written
        self.assertEqual(str(file_error(PermissionError(errno.EACCES, "Permission denied"), WRITING)),
                         TRY_AGAIN["held"].format(WRITING))
        # its five texts, each its own entry
        for template in TRY_AGAIN.values():
            self.assertIn(errortext.key_of(template), e)
        self.assertTrue(disk_full(OSError(errno.ENOSPC, "x")))
        self.assertFalse(disk_full(OSError(errno.EIO, "x")))

    def test_a_reader_s_error_with_python_s_words_inside_is_found(self):
        held = PermissionError(errno.EACCES, "Permission denied")
        self.assertIs(oserror_of(wrapped(held)), held)                                 # (rusemod.rig.read_rig's way)
        gone = FileNotFoundError(errno.ENOENT, "No such file or directory", "units.toml")
        self.assertIs(oserror_of(wrapped(gone, AnimError, "files/anim/units.toml: {0}")), gone)
        try:                                                                           # (raised from it)
            raise ModelError(f"x.glb: {held}") from held
        except ModelError as exc:
            self.assertIs(oserror_of(exc), held)
        self.assertIs(oserror_of(held), held)
        # its own words after one: not Python's, kept as they are
        self.assertIsNone(oserror_of(wrapped(held, ModelError, "the model has no points")))
        self.assertIsNone(oserror_of(ModelError("x.glb: not a .glb file")))


class TheAddSaysTheImportsFileErrorInItsWords(WithLibrary):
    """The Studio's import says a file it couldn't read or write in words (api.file_error, raised from the OSError);
    the Horse Squad's Add says it in its own, that it wasn't added (the page shows the job's message alone)."""

    def add_with_import(self, raising) -> tuple[dict, Path, dict]:
        folder = Path(self.api.new_mod(f"Import {id(raising)}")["current"])
        before = tree(folder)
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import", side_effect=raising):
            view = finished(self.api, self.api.horse_squad_add(0, 10, "Horse Squad", 5, group="new")["job"])
        self.assertEqual((view["state"], view["lines"]), ("failed", ["build", "unit", "riflemen"]))
        after = tree(folder)
        self.assertEqual(json.loads(after.pop(era_units.INDEX)), {})          # (its record emptied, as test_horse_squad)
        after.pop("src/studio.rndf", None)
        self.assertEqual(after, {k: v for k, v in before.items() if k != "src/studio.rndf"})
        return view, folder, before

    def test_a_full_disk_while_the_import_writes_is_said_as_the_add_s(self):
        def full(address, file, *args, **kw):
            exc = OSError(errno.ENOSPC, "No space left on device")
            raise file_error(exc, self.api._own_model_file(address), Path(file)) from exc
        view, folder, _before = self.add_with_import(full)
        self.assertEqual(view["message"], ADD["full"].format(folder))
        self.assertEqual(self.job_said_in(view["id"], "fr"),
                         entries()[errortext.key_of(ADD["full"])]["fr"].format(folder))

    def test_a_file_the_import_couldn_t_read_is_the_soldier_s_file(self):
        """An error naming no file while the riflemen's file is read (a part another program has locked): the Add
        names that file, the platform folder's copy the Studio made (never the mod, nor the model being written)."""
        def held(address, file, *args, **kw):
            exc = PermissionError(errno.EACCES, "Permission denied")
            raise file_error(exc, self.api._own_model_file(address), Path(file)) from exc
        view, _folder, _before = self.add_with_import(held)
        read = self.home / horse_squad.FOLDER / self.rifle.name
        self.assertEqual(view["message"], ADD["held"].format(read))
        for lang in OTHERS:
            said = self.job_said_in(view["id"], lang)
            self.assertIn(str(read), said, lang)
            self.assertNotIn("couldn't", said, lang)

    def test_the_import_s_other_refusals_are_passed_on_as_they_came(self):
        """The control: a refusal of the import that isn't a file it couldn't read or write (its own words of the
        model) is the job's message as it was."""
        def refused(address, file, *args, **kw):
            raise StudioError(f"{Path(file).name}: not a .glb file")
        view, _folder, _before = self.add_with_import(refused)
        self.assertEqual(view["message"], f"{self.rifle.name}: not a .glb file")

    def test_the_file_held_while_the_add_puts_its_new_one_in_its_place_is_named(self):
        """Of the two files a replace names, the one in its place (another program holds it), never the Add's own new
        one; of two with one not there, the one to be put there."""
        new = self.home / horse_squad.FOLDER / ".making-1234abcd" / "rifle.glb"
        kept = self.home / horse_squad.FOLDER / "rifle.glb"
        said = self.api._horse_file_error(PermissionError(errno.EACCES, "Access is denied", str(new), None, str(kept)),
                                          self.home / horse_squad.FOLDER)
        self.assertEqual(str(said), ADD["held"].format(kept))
        said = self.api._horse_file_error(FileNotFoundError(errno.ENOENT, "Not found", str(new), None, str(kept)),
                                          self.home / horse_squad.FOLDER)
        self.assertEqual(str(said), f"The Horse Squad couldn't be added: {new} isn't there.")


class EveryGroundUnitSaysAFileErrorInWords(WithLibrary):
    def test_a_unit_skipped_for_a_file_says_why_in_words_in_the_studio_s_language(self):
        """A file error that reaches the job as Python's (one no step said in words): the skip line says it in words,
        naming the unit's model when the error names no file; the line's first word as the page reads it."""
        self.api.new_mod("Skipped")
        address = self.api.new_unit(SQUAD, "My Rifles", 5, group="new")["address"]
        model = self.api._own_model_file(address)
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_bytes(b"glb")
        model.with_suffix(".json").write_text(json.dumps({"from": str(model), "size": 1.0}), encoding="utf-8")
        expected = TRY_AGAIN["full"].format(model)
        for lang in ("us", "fr", "jpn", "fa"):
            with self.subTest(lang=lang):
                self.api.set_pref("lang", lang)
                try:
                    with mock.patch.object(StudioApi, "model_resize",
                                           side_effect=OSError(errno.ENOSPC, "No space left on device")):
                        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"])
                finally:
                    self.api.set_pref("lang", "us")
                self.assertEqual(view["state"], "done")
                self.assertEqual(len(view["lines"]), 1)
                first, name, why = view["lines"][0].split("\t")
                self.assertEqual((first, name), ("skipped", "My Rifles"))
                self.assertEqual(why, expected if lang == "us" else errortext.worded(expected, lang))
                self.assertIn(str(model), why)
                for words in PYTHONS:
                    self.assertNotIn(words, why)
                if lang != "us":
                    self.assertNotEqual(why, expected)


@unittest.skipUnless(ON_THE_GAME, WHY_SKIPPED)
class OnTheGame(unittest.TestCase):
    """The Horse Squad's Add into a new mod with its builder standing in with the passed copy's two files, the Studio's
    own import running; one of its readers failing on the riflemen's file as a reader does when another program has
    locked part of it."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="file-words-", dir=os.environ.get("RUSE_TEST_TMP") or None))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.mod = Path(self.api.new_mod("File words")["current"])

    def add(self, *patches) -> dict:
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
            for p in patches:
                p.start()
            try:
                return finished(self.api, self.api.horse_squad_add(0, 8, "Horse Squad", 5, None, None, None,
                                                                   "new")["job"])
            finally:
                for p in reversed(patches):
                    p.stop()

    def assert_the_riflemen_s_file_named_in_words(self, view: dict) -> None:
        self.assertEqual((view["state"], view["lines"]), ("failed", ["build", "unit", "riflemen"]))
        read = self.home / horse_squad.FOLDER / RIFLE.name
        self.assertEqual(view["message"], ADD["held"].format(read))
        for lang in ("fr", "jpn", "fa"):
            self.api.set_pref("lang", lang)
            try:
                said = self.api.job(view["id"])["message"]
            finally:
                self.api.set_pref("lang", "us")
            self.assertIn(str(read), said, lang)
            self.assertNotEqual(said, view["message"], lang)
            for words in PYTHONS:
                self.assertNotIn(words, said, lang)

    def test_the_import_s_reader_failing_on_its_file_is_said_in_words(self):
        """rusemod.rig.read_rig wraps a file it can't read in its own error with Python's words inside ("x.glb:
        [Errno 13] Permission denied"): said in words, naming the riflemen's file."""
        def read_rig(path):
            try:
                raise PermissionError(errno.EACCES, "Permission denied")   # (a locked part, as a read gives it)
            except OSError as exc:
                raise ModelError(f"{Path(path).name}: {exc}") from None
        self.assert_the_riflemen_s_file_named_in_words(self.add(mock.patch("rusemod.rig.read_rig", read_rig)))

    def test_the_import_s_look_at_its_bones_failing_is_said_in_words(self):
        """rusemod.animmodel.own_bones_on reading the file again: its OSError was taken as "not a model on bones of its
        own" and the job said the loop's reason ("its bones aren't ..."), English in every language."""
        def own_bones_on(game, path, models):
            raise PermissionError(errno.EACCES, "Permission denied")
        self.assert_the_riflemen_s_file_named_in_words(
            self.add(mock.patch("rusemod.animmodel.own_bones_on", own_bones_on)))

    def test_a_resize_whose_model_record_can_t_be_written_is_said_in_words(self):
        view = self.add()
        self.assertEqual(view["state"], "done")
        address = view["result"]["address"] if view.get("result") else self.api._era_record()[KEY]
        record = self.api._own_model_file(address).with_suffix(".json")
        real = pathlib.Path.write_text

        def write_text(path, *args, **kw):
            if Path(path) == record:
                raise OSError(errno.ENOSPC, "No space left on device")     # (a write on a full disk names no file)
            return real(path, *args, **kw)
        with mock.patch.object(pathlib.Path, "write_text", write_text), self.assertRaises(StudioError) as said:
            self.api.model_resize(address, 1.2)
        self.assertEqual(str(said.exception), TRY_AGAIN["full"].format(record))
        self.api.set_pref("lang", "fr")
        try:
            worded = str(self.api.page_error(said.exception))
        finally:
            self.api.set_pref("lang", "us")
        self.assertEqual(worded, entries()[errortext.key_of(TRY_AGAIN["full"])]["fr"].format(record))


if __name__ == "__main__":
    unittest.main()
