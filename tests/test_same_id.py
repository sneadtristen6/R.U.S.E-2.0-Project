"""A unit mod and map changes made under one name (a tester's Test in game, 2026-10-30: the Studio's "bridge-test"
unit mod and map changes both had the id bridge-test, and the build stopped on "IndexError: list index out of range"
in the load order). The build reads the second under an id of its own (rusemod.play.read_mods), the load order says
plainly when two of one id still meet (rusemod.resolve), and the Studio no longer gives a new one a name the other
kind has (StudioApi.new_mod)."""
import tempfile
import unittest
from pathlib import Path

from rusemod.play import build_ids, keep_order, read_mods
from rusemod.resolve import ModInfo, ResolveError, load_order
from ruse_studio.api import StudioApi


def folder(root: Path, kind: str, mod_id: str) -> Path:
    f = root / kind / mod_id
    (f / ("maps" if kind == "maps" else "src")).mkdir(parents=True)
    (f / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nversion = "0.1.0"\n', encoding="utf-8")
    return f


class SameId(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_ids(self):
        self.assertEqual(build_ids(["a", "b"]), ["a", "b"])
        self.assertEqual(build_ids(["a", "a"]), ["a", "a-2"])
        self.assertEqual(build_ids(["a", "a", "a-2"]), ["a", "a-3", "a-2"])  # never one another folder has
        self.assertEqual(build_ids(["a", "a", "a"]), ["a", "a-2", "a-3"])

    def test_the_load_order_says_it_plainly(self):
        with self.assertRaisesRegex(ResolveError, "bridge-test is in the set more than once"):
            load_order([ModInfo("bridge-test"), ModInfo("bridge-test")])

    def test_a_unit_mod_and_map_changes_of_one_name_build_together(self):
        unit = folder(self.root, "mods", "bridge-test")
        maps = folder(self.root, "maps", "bridge-test")
        said = []
        mods = read_mods([unit, maps], said.append)
        self.assertEqual([m.id for m, _ops in mods], ["bridge-test", "bridge-test-2"])
        self.assertEqual(len(said), 1)
        self.assertIn("builds as bridge-test-2", said[0])
        keep_order(mods)
        self.assertEqual([m.id for m in load_order([m for m, _ops in mods])], ["bridge-test", "bridge-test-2"])
        self.assertIn('id = "bridge-test"', (maps / "mod.toml").read_text(encoding="utf-8"))  # its files as they were

    def test_a_new_one_never_takes_the_other_kinds_name(self):
        api = StudioApi(home=self.root / "home", game_dir=self.root / "game")
        api.new_mod("Bridge test")
        api.new_mod("Bridge test", "map")
        self.assertTrue((self.root / "home" / "mods" / "bridge-test" / "mod.toml").is_file())
        self.assertTrue((self.root / "home" / "maps" / "bridge-test-2" / "mod.toml").is_file())
        self.assertFalse((self.root / "home" / "maps" / "bridge-test").exists())


if __name__ == "__main__":
    unittest.main()
