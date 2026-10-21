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



class KnownPatchesTest(unittest.TestCase):
    def test_each_known_patch_names_a_file_and_its_checksum(self):
        for name, (file, file_sha) in gamepatch.PATCHES.items():
            self.assertTrue(file.startswith(name + "-") and file.endswith(".json"), file)
            self.assertTrue(gamepatch._is_sha(file_sha) and file_sha != "0" * 64, name)


if __name__ == "__main__":
    unittest.main()
