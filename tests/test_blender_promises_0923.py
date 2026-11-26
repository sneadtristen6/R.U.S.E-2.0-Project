"""The 0.9.8.22 announcement's promises for squads, Blender and animations that were built for 0.9.8.23 (the owner,
2026-11-26: "The 60 promises should be built into this release"; his picks 21 to 52 of REVIEW-0920.md, "everything that
you agreed to, 21 through 52"): each promise's words in the eleven languages, and where the page shows them.

One class per promise (ITEM: its number in D:/RUSE-2.0/scratch/release-next/audit-2026-11-26/results/
plan_squads-blender.json's order; the sentence names the promise). These read the page's code and the words (there is
no browser here, as tests/test_lookmoves.py and tests/test_squadpage.py do it); what a page then looks like in the
game's window is not checked here.

FOR: the squads, Blender and animations promises of release 0.9.8.23 (24, 29, 52a-52y, 51f, 51j, 21, 22).
USED-BY: gentle.py, -m unittest."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import re
import tomllib
import unittest
from pathlib import Path
from urllib.parse import quote

from rusemod.community import REPO_URL, WIKI_TOPICS, wiki_url

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "src" / "ruse_studio" / "ui"
LANGS = ["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa"]
WORDS = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
ERRORS = tomllib.loads((ROOT / "src" / "ruse_studio" / "errors.toml").read_text(encoding="utf-8"))
BLANK = re.compile(r"\{\w+\}")


def js(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def function_text(source: str, name: str) -> str:
    """`function name(` to the next line that is a closing brace at column 0."""
    start = source.index(f"function {name}(")
    return source[start: source.index("\n}\n", start)]


class InElevenLanguages(unittest.TestCase):
    def words_in_eleven_languages(self, keys, english_left_in=False):
        """Each key has every language, the same blanks as the English, nothing empty (and, for a new sentence, no
        language left as the English)."""
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, WORDS)
                self.assertEqual(set(WORDS[key]), set(LANGS))
                for lang in LANGS:
                    self.assertTrue(WORDS[key][lang].strip(), lang)
                    self.assertEqual(sorted(BLANK.findall(WORDS[key][lang])), sorted(BLANK.findall(WORDS[key]["us"])), lang)
                    if english_left_in and lang != "us":
                        self.assertNotEqual(WORDS[key][lang], WORDS[key]["us"], lang)

    def names_in_every_language(self, line_key, button_keys):
        """A line names each of those buttons by the page's own word, in every language."""
        for lang in LANGS:
            for button in button_keys:
                with self.subTest(line=line_key, button=button, lang=lang):
                    self.assertIn(WORDS[button][lang], WORDS[line_key][lang])


class Item3FirstHintOnATank(InElevenLanguages):
    """Pick 24: Blender's first hint says "Change the model" for a unit that isn't a squad (the behaviour is in
    test_modelblender); here: it is another sentence in every language and says the model, not the soldier."""
    ITEM = "3"

    def test_the_model_wording(self):
        self.words_in_eleven_languages(["blender_model_hint1_model"], english_left_in=True)
        self.assertTrue(WORDS["blender_model_hint1_model"]["us"].startswith("Change the model, or bring in your own model"))
        self.assertNotIn("soldier", WORDS["blender_model_hint1_model"]["us"])
        self.assertIn("soldier", WORDS["blender_model_hint1"]["us"])


class Item9UniformWordsInEveryLanguage(InElevenLanguages):
    """51j: Custom uniform and Back to the default uniform answer in the Studio's language (the behaviour is
    test_scenarios_squads_soldiers' SQ-11)."""
    ITEM = "9"

    def test_the_four_sentences_name_no_button_the_page_hasnt(self):
        keys = ["uniform_custom_done", "copy_own_done", "uniform_default_done", "copy_default_done"]
        self.words_in_eleven_languages(keys, english_left_in=True)
        for key in ("uniform_custom_done", "copy_own_done"):
            self.assertNotIn("Repaint in Blender", WORDS[key]["us"])
            self.names_in_every_language(key, ["look_open"])

    def test_the_calls_take_the_language(self):
        import inspect
        from ruse_studio.api import StudioApi
        for call in ("model_copy", "model_copy_remove"):
            self.assertIn("lang", inspect.signature(getattr(StudioApi, call)).parameters, call)


class WikiPages(InElevenLanguages):
    def topic_opens_each_language_s_page(self, topic, us, fr):
        self.assertEqual(sorted(WIKI_TOPICS[topic]), sorted(LANGS))
        self.assertEqual(wiki_url("us", topic), f"{REPO_URL}/wiki/{quote(us)}")
        self.assertEqual(wiki_url("fr", topic), f"{REPO_URL}/wiki/{quote(fr)}")
        for lang, page in WIKI_TOPICS[topic].items():
            folder = ROOT / "docs" / "wiki" / ("" if lang == "us" else lang)
            self.assertTrue((folder / f"{page}.md").is_file(), (topic, lang))
        self.words_in_eleven_languages([f"tip_help_trouble_{topic}"])


AUTOMATIC = {"us": "Automatic", "fr": "Automatique", "ger": "Automatisch", "ita": "Automatica", "spa": "Automática",
             "pol": "Automatycznie", "ru": "Автоматически", "cz": "Automaticky", "jpn": "自動", "sc": "自动",
             "fa": "خودکار"}
OLD_END = {"us": "Not tried in the game yet.", "fr": "Pas encore essayé dans le jeu.",
           "ger": "Noch nicht im Spiel ausprobiert.", "ita": "Non ancora provato nel gioco.",
           "spa": "Aún no probado en el juego.", "pol": "Jeszcze niesprawdzone w grze.",
           "ru": "В игре ещё не проверено.", "cz": "Ve hře zatím nevyzkoušeno.",
           "jpn": "ゲーム内ではまだ試していません。", "sc": "尚未在游戏中试过。", "fa": "هنوز در بازی امتحان نشده است."}


        #                                         code says the same words, for every refusal)


if __name__ == "__main__":
    unittest.main()
