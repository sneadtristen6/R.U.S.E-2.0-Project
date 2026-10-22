"""The game's lettering on the apps' pages (rusemod.gamefont): copied from the player's game into the app's cache at
each start, named first by both apps' style sheets, never carried by the apps themselves; on a made-up game."""
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat
from rusemod import gamefont

ROOT = Path(__file__).resolve().parents[1]


def write_game(root: Path, fonts: dict[str, bytes]) -> Path:
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / gamefont.PACK).write_bytes(make_edat([("dir", "ww2\\res2d\\fonts\\", [
        ("file", name, data) for name, data in fonts.items()])]))
    return root


class Copy(unittest.TestCase):
    def test_copied_once_from_the_game(self):
        with tempfile.TemporaryDirectory() as d:
            game = write_game(Path(d, "game"), {"ubigame text l reg v11.ttf": b"REG", "ubigame text l bold v07.ttf": b"BOLD!"})
            cache = Path(d, "cache")
            self.assertEqual(gamefont.copy_fonts(game, cache), ["ruse-regular.ttf", "ruse-bold.ttf"])  # the two it has
            folder = cache / gamefont.FOLDER
            self.assertEqual((folder / "ruse-regular.ttf").read_bytes(), b"REG")
            self.assertEqual((folder / "ruse-bold.ttf").read_bytes(), b"BOLD!")
            stamp = (folder / "ruse-regular.ttf").stat().st_mtime_ns
            self.assertEqual(gamefont.copy_fonts(game, cache), ["ruse-regular.ttf", "ruse-bold.ttf"])
            self.assertEqual((folder / "ruse-regular.ttf").stat().st_mtime_ns, stamp)  # the same copy kept
            self.assertFalse(list(folder.glob("*.part")))

    def test_no_game_no_fonts(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(gamefont.copy_fonts(None, Path(d, "cache")), [])
            self.assertEqual(gamefont.copy_fonts(Path(d, "nowhere"), Path(d, "cache")), [])
            self.assertFalse(Path(d, "cache").exists())


class Pages(unittest.TestCase):
    def test_both_apps_name_the_game_s_font_first(self):
        for app in ("ruse_studio", "ruse_launcher"):
            with self.subTest(app=app):
                css = (ROOT / "src" / app / "ui" / "style.css").read_text(encoding="utf-8")
                for name in gamefont.FONTS:
                    self.assertIn(f'url("cache/{gamefont.FOLDER}/{name}")', css)
                self.assertRegex(css, r'font: 1\dpx/1\.45 "RUSE", "Segoe UI"')
                js = (ROOT / "src" / app / "ui" / "app.js").read_text(encoding="utf-8")
                self.assertIn("document.documentElement.dataset.lang = lang;", js)
                py = (ROOT / "src" / app / "app.py").read_text(encoding="utf-8")
                self.assertIn("copy_fonts(", py)
                self.assertIn('extra={"cache": api.cache_dir}', py)

    def test_the_apps_carry_no_game_font(self):
        for app in ("ruse_studio", "ruse_launcher"):
            with self.subTest(app=app):
                found = [p.name for p in (ROOT / "src" / app).rglob("*") if p.suffix.lower() in (".ttf", ".ttc", ".otf")]
                self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
