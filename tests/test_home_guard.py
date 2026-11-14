"""No test writes into the real Studio home (the owner, 2026-11-13, "Yes, make it"; tests/home_guard.py).

Every test file imports home_guard first, so the default home of the whole run is a scratch folder of its own; the
build cache, a Studio made without a home and a process a test starts all land there. The control: the real home's
game index is only named for reading."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def first_statement(path: Path):
    """The first statement of a test file after its docstring and any `from __future__` import."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        return node
    return None


class EveryTestFile(unittest.TestCase):
    def test_every_test_file_imports_the_guard_first(self):
        files = sorted(HERE.glob("test_*.py"))
        self.assertGreater(len(files), 200)
        missing = []
        for f in files:
            node = first_statement(f)
            if not (isinstance(node, ast.Import) and [a.name for a in node.names] == ["home_guard"]):
                missing.append(f.name)
        self.assertEqual(missing, [], "these test files don't import home_guard first: add "
                                      "'import home_guard  # noqa: F401' as their first import")

    def test_a_file_that_forgets_it_is_named(self):
        """The check itself, on a made-up file: a test file whose first import is another one is caught."""
        with tempfile.TemporaryDirectory(dir=os.environ.get("RUSE_TEST_TMP") or None) as d:
            f = Path(d, "test_forgot.py")
            f.write_text('"""A test."""\nimport unittest\nimport home_guard\n', encoding="utf-8")
            node = first_statement(f)
            self.assertFalse(isinstance(node, ast.Import) and [a.name for a in node.names] == ["home_guard"])


class TheHome(unittest.TestCase):
    def test_the_default_home_is_the_run_s_own_folder(self):
        from rusemod.home import default_home
        self.assertEqual(default_home(), home_guard.HOME)
        self.assertNotEqual(home_guard.HOME.resolve(), home_guard.REAL.resolve())
        self.assertTrue(home_guard.HOME.is_dir())

    def test_the_build_cache_and_a_studio_made_without_a_home_land_in_it(self):
        from rusemod.build import build_cache
        from ruse_studio.api import StudioApi
        self.assertEqual(build_cache(), home_guard.HOME / "cache" / "build")
        api = StudioApi(index_path=home_guard.HOME / "none.sqlite", find=lambda: None)
        self.assertEqual(api._home, home_guard.HOME)

    def test_a_process_a_test_starts_gets_it_too(self):
        out = subprocess.run([sys.executable, "-c", "import os; print(os.environ['RUSE_PLATFORM_HOME'])"],
                             capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(Path(out), home_guard.HOME)

    def test_the_real_home_s_game_index_is_only_named_for_reading(self):
        """The control: the two tests of the real game's missions read the index the real home holds."""
        from rusemod.index import build_key
        with tempfile.TemporaryDirectory(dir=os.environ.get("RUSE_TEST_TMP") or None) as game:
            self.assertEqual(home_guard.game_index(game),
                             home_guard.REAL / "index" / f"{build_key(Path(game))}.sqlite")


if __name__ == "__main__":
    unittest.main()
