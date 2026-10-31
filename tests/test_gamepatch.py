"""Game patches (rusemod.gamepatch): only the exact file the apps know is used, only on the game build it's made for,
only with every expected byte in place, and the result is the one promised."""
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import gamepatch


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


EXE = bytes(range(256)) * 4
PATCHED = bytearray(EXE)
PATCHED[10:12] = b"\xaa\xbb"
PATCHED[600:601] = b"\x01"
PATCHED = bytes(PATCHED)
EDITS = [(10, EXE[10:12], b"\xaa\xbb"), (600, EXE[600:601], b"\x01")]
FILE = gamepatch.write("more-buildings", sha(EXE), sha(PATCHED), EDITS)


class GamePatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        p = mock.patch.dict(gamepatch.PATCHES, {"more-buildings": ("more-buildings-test.json", sha(FILE))})
        p.start()
        self.addCleanup(p.stop)
        self.release = self.tmp / "release"
        self.release.mkdir()
        (self.release / "more-buildings-test.json").write_bytes(FILE)
        e = mock.patch.dict("os.environ", {gamepatch.URL_ENV: str(self.release) + "/"})
        e.start()
        self.addCleanup(e.stop)

    def test_applies_exactly(self):
        patch = gamepatch.parse("more-buildings", FILE)
        self.assertEqual(gamepatch.apply(patch, EXE), PATCHED)

    def test_another_build_refused(self):
        patch = gamepatch.parse("more-buildings", FILE)
        with self.assertRaisesRegex(gamepatch.GamePatchError, "another version"):
            gamepatch.apply(patch, EXE[:-1] + b"\x00")

    def test_a_changed_file_refused(self):
        with self.assertRaisesRegex(gamepatch.GamePatchError, "checksum"):
            gamepatch.parse("more-buildings", FILE.replace(b'"format": 1', b'"format": 1 '))
        with self.assertRaisesRegex(gamepatch.GamePatchError, "not a game patch"):
            gamepatch.parse("other", FILE)

    def test_a_wrong_promise_refused(self):
        bad = gamepatch.write("more-buildings", sha(EXE), "1" * 64, EDITS)
        with mock.patch.dict(gamepatch.PATCHES, {"more-buildings": ("x.json", sha(bad))}):
            patch = gamepatch.parse("more-buildings", bad)
        with self.assertRaisesRegex(gamepatch.GamePatchError, "promises"):
            gamepatch.apply(patch, EXE)

    def test_fetched_once_into_the_cache(self):
        cache = self.tmp / "cache"
        lines = []
        gamepatch.fetch("more-buildings", cache, say=lines.append)
        kept = cache / gamepatch.FOLDER / "more-buildings-test.json"
        self.assertEqual(kept.read_bytes(), FILE)
        self.assertEqual(len(lines), 1)
        (self.release / "more-buildings-test.json").unlink()  # not asked for again
        self.assertEqual(gamepatch.fetch("more-buildings", cache, say=lines.append).sha256, sha(FILE))
        self.assertEqual(len(lines), 1)

    def test_a_spoilt_cache_is_fetched_again(self):
        cache = self.tmp / "cache"
        kept = cache / gamepatch.FOLDER / "more-buildings-test.json"
        kept.parent.mkdir(parents=True)
        kept.write_bytes(b"cut off")
        gamepatch.fetch("more-buildings", cache)
        self.assertEqual(kept.read_bytes(), FILE)

    def test_missing_file_said_plainly(self):
        (self.release / "more-buildings-test.json").unlink()
        with self.assertRaisesRegex(gamepatch.GamePatchError, "couldn't be downloaded"):
            gamepatch.fetch("more-buildings", self.tmp / "cache")


# a second patch, as big-packs is: changes in place elsewhere, and bytes added at the file's end
GROWN = bytearray(EXE)
GROWN[100:102] = b"\x11\x22"
GROWN += b"NEW SECTION"
GROWN = bytes(GROWN)
BIG_EDITS = [(100, EXE[100:102], b"\x11\x22"), (len(EXE), b"", b"NEW SECTION")]
BIG = gamepatch.write("big-packs", sha(EXE), sha(GROWN), BIG_EDITS)


class SeveralPatchesTest(unittest.TestCase):
    """A modded copy can need more than one patch (the owner, 2026-10-30: the mods' own buildings and a pack past
    4 GiB): each is tried alone, they mustn't touch the same bytes, then they go in together."""

    def setUp(self):
        p = mock.patch.dict(gamepatch.PATCHES, {"more-buildings": ("more-buildings-test.json", sha(FILE)),
                                                "big-packs": ("big-packs-test.json", sha(BIG))})
        p.start()
        self.addCleanup(p.stop)
        self.more, self.big = gamepatch.parse("more-buildings", FILE), gamepatch.parse("big-packs", BIG)

    def test_bytes_added_at_the_end(self):
        self.assertEqual(gamepatch.apply(self.big, EXE), GROWN)
        self.assertEqual(gamepatch.apply_all([self.big], EXE), GROWN)

    def test_two_patches_together(self):
        both = gamepatch.apply_all([self.more, self.big], EXE)
        want = bytearray(PATCHED)
        want[100:102] = b"\x11\x22"
        self.assertEqual(both, bytes(want) + b"NEW SECTION")
        self.assertEqual(gamepatch.apply_all([self.big, self.more], EXE), both)  # in either order

    def test_two_patches_on_the_same_bytes_refused(self):
        clash = bytearray(EXE)
        clash[11:12] = b"\x99"
        clash_file = gamepatch.write("big-packs", sha(EXE), sha(bytes(clash)), [(11, EXE[11:12], b"\x99")])
        with mock.patch.dict(gamepatch.PATCHES, {"big-packs": ("big-packs-test.json", sha(clash_file))}):
            other = gamepatch.parse("big-packs", clash_file)
        with self.assertRaisesRegex(gamepatch.GamePatchError, "same part"):
            gamepatch.apply_all([self.more, other], EXE)

    def test_added_bytes_must_start_at_the_end(self):
        wrong = gamepatch.write("big-packs", sha(EXE), sha(GROWN), [(len(EXE) - 1, b"", b"NEW SECTION")])
        with mock.patch.dict(gamepatch.PATCHES, {"big-packs": ("big-packs-test.json", sha(wrong))}):
            patch = gamepatch.parse("big-packs", wrong)
        with self.assertRaisesRegex(gamepatch.GamePatchError, "length"):
            gamepatch.apply(patch, EXE)

    def test_a_download_error_says_what_the_patch_is_for(self):
        with mock.patch.dict("os.environ", {gamepatch.URL_ENV: str(Path(tempfile.mkdtemp())) + "/"}):
            with self.assertRaisesRegex(gamepatch.GamePatchError, "bigger than 4 GB"):
                gamepatch.fetch("big-packs", None)



class KnownPatchesTest(unittest.TestCase):
    def test_each_known_patch_names_a_file_and_its_checksum(self):
        for name, (file, file_sha) in gamepatch.PATCHES.items():
            self.assertTrue(file.startswith(name + "-") and file.endswith(".json"), file)
            self.assertTrue(gamepatch._is_sha(file_sha) and file_sha != "0" * 64, name)


if __name__ == "__main__":
    unittest.main()
