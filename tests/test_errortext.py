"""The Studio's errors in the player's language (ruse_studio.errortext; the owner, 2026-10-16: "Yes, fix the errors"):
every StudioError the Studio's code raises has its words in errors.toml in all ten languages with the same blanks, and
an error going to the page comes out in the Studio's language with its values filled in."""
import re
import tempfile
import tomllib
import unittest
from pathlib import Path

from ruse_studio import errortext
from ruse_studio.api import StudioApi, StudioError

SRC = Path(__file__).parents[1] / "src" / "ruse_studio"
BLANK = re.compile(r"(?<!\{)\{(\d+)\}(?!\})")


class EveryErrorHasItsWords(unittest.TestCase):
    def test_every_error_in_the_code_is_in_ten_languages(self):
        entries = tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))
        templates = errortext.templates_in(sorted(SRC.glob("*.py")))
        self.assertGreater(len(templates), 250)
        missing = [t for t in templates if errortext.key_of(t) not in entries]
        self.assertEqual(missing, [], "errors with no entry in errors.toml: run the list and add their words")
        for t in templates:
            words = entries[errortext.key_of(t)]
            self.assertEqual(words["us"], t)
            for lang in errortext.LANGS:
                self.assertIn(lang, words, (t, lang))
                self.assertEqual(sorted(BLANK.findall(words[lang])), sorted(BLANK.findall(t)), (t, lang))
                words[lang].format(*["x"] * (len(BLANK.findall(t)) + 1))  # (a stray brace would fail here)

    def test_no_entry_is_left_over(self):
        """An entry no error in the code makes any more is words nobody sees: the list is redone when one goes."""
        entries = tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))
        keys = {errortext.key_of(t) for t in errortext.templates_in(sorted(SRC.glob("*.py")))}
        self.assertEqual(sorted(set(entries) - keys), [])


class Worded(unittest.TestCase):
    def test_an_error_in_another_language(self):
        self.assertEqual(errortext.worded("Pick or make a mod first: changes are saved in a mod.", "fr"),
                         "Choisissez ou créez d'abord un mod : les changements y sont enregistrés.")
        self.assertEqual(errortext.worded("DataMapBlitz_v09.dat isn't in the game folder.", "ger"),
                         "DataMapBlitz_v09.dat ist nicht im Spielordner.")
        self.assertEqual(errortext.worded("That box is too big to pick from: at most 1,000 m corner to corner. Drag a "
                                          "smaller one, or use the Erase brush for a whole area.", "sc"),
                         "方框太大，无法选择：对角最多 1,000 米。请拖出更小的方框，或对整片区域使用擦除画笔。")
        # the values keep their place when the words turn round them
        self.assertEqual(errortext.worded("Tiger of Germany can't be edited here", "jpn"),
                         "Germany の Tiger はここでは編集できません")

    def test_a_text_with_a_value_holding_the_same_words(self):
        """The more particular template wins: "{0} isn't in the game folder ({1})." over "{0} isn't in the game
        folder."."""
        self.assertEqual(errortext.worded("ZZ_Win.dat isn't in the game folder (D:/Games/RUSE).", "spa"),
                         "ZZ_Win.dat no está en la carpeta del juego (D:/Games/RUSE).")

    def test_english_and_unknown_texts_stay(self):
        text = "Pick or make a mod first: changes are saved in a mod."
        self.assertEqual(errortext.worded(text, "us"), text)
        self.assertEqual(errortext.worded(text, "base"), text)
        self.assertEqual(errortext.worded("Something nobody wrote", "fr"), "Something nobody wrote")

    def test_the_page_gets_it_in_the_studio_s_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(game_dir=Path(tmp) / "nowhere", home=Path(tmp, "home"), index_path=Path(tmp, "x.sqlite"))
            api.set_pref("lang", "ita")
            said = api.page_error(StudioError("Pick or make a mod first."))
            self.assertIsInstance(said, StudioError)
            self.assertEqual(str(said), "Scegli o crea prima una mod.")
            self.assertIsNone(api.page_error(ValueError("not ours")))           # only the Studio's own errors
            self.assertIsNone(api.page_error(StudioError("Nobody's template")))  # nothing to say differently

    def test_a_page_call_s_error_comes_out_worded(self):
        from rusemod.webui import page_api

        class Api:
            def page_error(self, exc):
                return RuntimeError("worded: " + str(exc))

            def fails(self):
                raise ValueError("as raised")

        with self.assertRaisesRegex(RuntimeError, "worded: as raised"):
            page_api(Api()).fails()


if __name__ == "__main__":
    unittest.main()
