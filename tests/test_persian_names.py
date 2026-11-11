"""Persian, the apps' language the game has no texts in (the owner, 2026-10-30), reads the game's English names
everywhere (the owner, 2026-11-11: "Yes, fix it", on the Nations board's units in code names; a check of 32 Studio
calls on the game found 3,196 code names or "no name in the game" lines in Persian, 0 after). The Studio side is
tested on its little game in test_studio (test_persian_shows_the_games_english_names); here the rule and the page."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rusemod import schema  # noqa: E402


class GameLang(unittest.TestCase):
    def test_each_app_language_reads_a_language_the_game_has(self):
        self.assertEqual(schema.game_lang("fa"), "us")
        for lang in schema.LANGS:
            self.assertEqual(schema.game_lang(lang), lang)
        self.assertTrue(all(schema.game_lang(lang) in schema.LANGS for lang in schema.APP_LANGS))
        self.assertEqual(schema.game_lang(schema.BASE), schema.BASE)   # Code names: no texts, as before


class ThePage(unittest.TestCase):
    def test_a_maps_title_falls_back_to_english(self):
        maps = (ROOT / "src" / "ruse_studio" / "ui" / "maps.js").read_text(encoding="utf-8")
        self.assertIn("e.titles && (e.titles[mv.lang] || e.titles.us)) || e.name;", maps)


if __name__ == "__main__":
    unittest.main()
