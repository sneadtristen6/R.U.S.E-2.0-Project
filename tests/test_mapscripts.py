"""The game's map and mission scripts shown as Python (rusemod.mapscripts, the AI tab's script viewer), on a made-up
game whose scripts are small ones of our own (none of the game's). Skipped where the two libraries LittleGroove's
engine uses for it aren't installed (the Python 3.11 test runs: .github/workflows/tests.yml)."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat
from rusemod import mapscripts
from ruse_studio.api import StudioApi, StudioError

MISSING = mapscripts.missing()


def s(b: bytes) -> bytes:
    return b"s" + struct.pack("<i", len(b)) + b


def name(b: bytes) -> bytes:  # an interned name, as Python 2.5 writes a code object's names
    return b"t" + struct.pack("<i", len(b)) + b


def tup(*items: bytes) -> bytes:
    return b"(" + struct.pack("<i", len(items)) + b"".join(items)


def script(value: int) -> bytes:
    """A module of our own, `GOAL = <value>`, as the game keeps its scripts (Python 2.5, in an .xyz)."""
    from ruse_mod_engine import xyz_compile
    code = b"d\x00\x00Z\x00\x00d\x01\x00S"  # LOAD_CONST 0, STORE_NAME 0, LOAD_CONST 1 (None), RETURN_VALUE
    obj = (b"c" + struct.pack("<iiii", 0, 0, 1, 0x40) + s(code) + tup(b"i" + struct.pack("<i", value), b"N")
           + tup(name(b"GOAL")) + tup() + tup() + tup() + s(b"effetmap.py") + name(b"<module>")
           + struct.pack("<i", 1) + s(b""))
    return xyz_compile.pack(obj)


PATHS = ("genpython\\1000\\test\\map\\supercrossroads4\\scripting_challenge\\effetmap.xyz",
         "genpython\\1000\\test\\map\\m04_cotentin\\scripting_chapter1\\effetmap.xyz",
         "genpython\\1000\\test\\map\\supercrossroads4\\scripting_testia\\maptests\\__init__.xyz")


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    files = [("file", p, script(i + 1)) for i, p in enumerate(PATHS)] + [("file", "readme.txt", b"not a script")]
    (rev / "IA_Common.dat").write_bytes(make_edat(files))
    (root / "RUSE.exe").write_bytes(b"MZ")


@unittest.skipIf(MISSING, f"can't show scripts here: {MISSING}")
class Scripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_a_script_as_python(self):
        self.assertEqual(mapscripts.text(script(7)), "GOAL = 7\n")  # without the library's lines about itself
        self.assertEqual(mapscripts.text(mapscripts.sample()), "")  # the self-test's: an empty module
        self.assertIsNone(mapscripts.missing())

    def test_the_list_by_map(self):
        found = mapscripts.scripts(self.game)
        self.assertEqual([(f["map"], f["part"], f["file"]) for f in found],
                         [("m04_cotentin", "scripting_chapter1", "effetmap.xyz"),
                          ("supercrossroads4", "scripting_challenge", "effetmap.xyz"),
                          ("supercrossroads4", "scripting_testia", "maptests/__init__.xyz")])
        self.assertEqual(mapscripts.text(mapscripts.read(self.game, found[0]["path"])), "GOAL = 2\n")
        with self.assertRaises(KeyError):
            mapscripts.read(self.game, "readme.txt")  # not a script
        self.assertEqual(mapscripts.scripts(Path(self.tmp.name, "nothing")), [])

    def test_the_ai_tab_s_calls(self):
        home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        api = StudioApi(game_dir=self.game, home=home, instances=home / "copies")
        page = api.ai_scripts("us")
        self.assertIsNone(page["missing"])
        # no map list in this made-up game: each map by its folder's name
        self.assertEqual([(x["map"], x["part"], x["file"], x["detail"]) for x in page["scripts"]][:2],
                         [("m04_cotentin", "chapter1", "effetmap.xyz", "m04_cotentin/scripting_chapter1/effetmap.xyz"),
                          ("supercrossroads4", "challenge", "effetmap.xyz",
                           "supercrossroads4/scripting_challenge/effetmap.xyz")])
        shown = api.ai_script(PATHS[0])
        self.assertEqual((shown["text"], shown["lines"]), ("GOAL = 1\n", 1))
        self.assertIs(api.ai_script(PATHS[0])["text"], shown["text"])  # the second time from the session's copy
        with self.assertRaisesRegex(StudioError, "isn't one of IA_Common.dat's scripts"):
            api.ai_script("genpython\\nothing.xyz")


if __name__ == "__main__":
    unittest.main()
