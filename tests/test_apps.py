"""The platform is two separate apps on one engine (PLAN.md decision 22): RUSE Launcher for players, RUSE Studio for
modders. Neither app needs the other, the engine needs neither, and both agree on where the game is."""
import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ruse_launcher.api import LauncherApi
from ruse_studio.api import StudioApi
from rusemod.home import game_dir

SRC = Path(__file__).parents[1] / "src"


def imports(package: str) -> dict[str, set]:
    """File -> the top-level packages it imports (relative imports stay inside the package)."""
    out = {}
    for f in (SRC / package).rglob("*.py"):
        found = set()
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
        out[f.relative_to(SRC).as_posix()] = found
    return out


class TwoApps(unittest.TestCase):
    def test_neither_app_needs_the_other(self):
        for package, forbidden in (("ruse_launcher", {"ruse_studio"}), ("ruse_studio", {"ruse_launcher"}),
                                   ("rusemod", {"ruse_launcher", "ruse_studio"})):
            files = imports(package)
            self.assertTrue(files, package)
            for f, found in files.items():
                self.assertEqual(found & forbidden, set(), f"{f} imports another app")

    def test_each_app_has_its_own_window_and_start_command(self):
        for package, title in (("ruse_launcher", "RUSE Launcher"), ("ruse_studio", "RUSE Studio")):
            self.assertTrue((SRC / package / "__main__.py").is_file(), package)
            page = (SRC / package / "ui" / "index.html").read_text(encoding="utf-8")
            self.assertIn(f"<title>{title}</title>", page)
            self.assertIn(f'"{title}"', (SRC / package / "app.py").read_text(encoding="utf-8"))
        project = (SRC.parent / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('ruse-launcher = "ruse_launcher.app:main"', project)
        self.assertIn('ruse-studio = "ruse_studio.app:main"', project)

    def test_both_apps_find_the_game_in_the_same_place(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RUSE_GAME", None)
            home, game = Path(d, "home"), Path(d, "Games", "R.U.S.E")
            game.mkdir(parents=True)
            (game / "RUSE.exe").write_bytes(b"MZ")
            self.assertEqual(game_dir(home, find=lambda: None), (None, {}))
            steam = {"game_dir": str(Path(d, "steam", "R.U.S.E")), "build_id": "24687178"}
            self.assertEqual(game_dir(home, find=lambda: steam), (Path(steam["game_dir"]), steam))
            os.environ["RUSE_GAME"] = str(Path(d, "from-env"))
            self.assertEqual(game_dir(home, find=lambda: steam)[0], Path(d, "from-env"))
            del os.environ["RUSE_GAME"]
            # picked by hand in the launcher (Steam couldn't tell): the Studio uses it too
            launcher = LauncherApi(home=home, find=lambda: None, pick_folder=lambda: str(game))
            self.assertTrue(launcher.choose_game_folder()["found"])
            self.assertEqual(StudioApi(home=home, find=lambda: None)._game(), game)
            self.assertEqual(game_dir(home, find=lambda: steam)[0], game)  # a folder picked by hand comes first

    def test_the_studio_without_its_game_index_still_has_maps_and_settings(self):
        """"No game index yet" and the index's build (a minute or more, the first start after an update of the game
        or of the index's format) cover only the tabs that need the index, Units and (since 2026-10-06) Economy and AI,
        (2026-10-07) Music: Maps and Settings, where the installer's clean backup shows how far it is, can be used
        meanwhile (seen in the page with index.html?fake=noindex, 2026-10-04; there's no JavaScript test runner here,
        so this checks the two lines)."""
        ui = SRC / "ruse_studio" / "ui"
        self.assertIn(".no-index.off-tab { display: none; }", (ui / "style.css").read_text(encoding="utf-8"))
        script = (ui / "app.js").read_text(encoding="utf-8")
        show_view = script[script.index("function showView(view) {"):script.index("\n}\n", script.index("function showView"))]
        self.assertIn('$("no-index").classList.toggle("off-tab", !["units", "economy", "ai", "music"].includes(view));',
                      show_view)


if __name__ == "__main__":
    unittest.main()
