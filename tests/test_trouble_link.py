"""The "Having trouble? Read the guide" link beside the Studio's hard boxes (ui/app.js troubleLink and helpLine, ui/squad.js,
ui/decoy.js; rusemod.community.WIKI_TOPICS and open_help's `topic`). The owner, 2026-11-13: "maybe have like a link
somewhere in the thing where it's like having trouble wiki. I don't know where you put that. I don't want it to look
stupid."

Checks of the code and the wiki (no browser here): every topic's page is in the wiki in each of the eleven languages,
the link opens the page in the player's language (English for English and any language without one), a topic that
isn't one is refused, every topic the page code asks for is one, and the link's words and tooltips are in the eleven
languages and on the stand-in page."""
import re
import tomllib
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import quote

from rusemod.community import REPO_URL, WIKI_TOPICS, CommunityCalls, wiki_url

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "docs" / "wiki"
UI = ROOT / "src" / "ruse_studio" / "ui"
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")


class App(CommunityCalls):
    UPDATE_APP, UPDATE_VERSION = "studio", "0.9.8.20"

    def __init__(self, lang=None):
        self._update_open_url = mock.Mock()
        self._lang = lang

    def prefs(self):
        return {"lang": self._lang} if self._lang else {}


class ThePages(unittest.TestCase):
    def test_every_topic_has_its_page_in_every_language(self):
        self.assertEqual(sorted(WIKI_TOPICS), ["animations", "blender", "bones"])
        for topic, pages in WIKI_TOPICS.items():
            self.assertEqual(sorted(pages), sorted(LANGS), topic)
            for lang, page in pages.items():
                with self.subTest(topic=topic, lang=lang):
                    folder = WIKI if lang == "us" else WIKI / lang
                    self.assertTrue((folder / f"{page}.md").is_file(), f"{folder / page}.md")

    def test_the_link_opens_the_page_in_the_player_s_language(self):
        for lang, want in (("fr", "Modèles-et-os"), ("jpn", "モデルとボーン"), ("us", "Models-and-Bones"),
                           ("base", "Models-and-Bones"), (None, "Models-and-Bones")):
            with self.subTest(lang=lang):
                app = App(lang)
                url = f"{REPO_URL}/wiki/{quote(want)}"
                self.assertEqual(app.open_help("wiki", "bones"), {"opened": url})
                app._update_open_url.assert_called_once_with(url)
        self.assertEqual(wiki_url("fa", "blender"), f"{REPO_URL}/wiki/{quote('باز-کردن-در-Blender')}")
        self.assertEqual(wiki_url("ger"), f"{REPO_URL}/wiki/{quote('Feldhandbuch')}")   # (no topic: the home, as before)

    def test_a_topic_that_isn_t_one_is_refused(self):
        app = App("fr")
        with self.assertRaisesRegex(ValueError, "no wiki page called 'nope'"):
            app.open_help("wiki", "nope")
        with self.assertRaisesRegex(ValueError, "no wiki page called 'bones'"):
            app.open_help("discussions", "bones")   # (a topic is the wiki's only)
        app._update_open_url.assert_not_called()


class ThePageCode(unittest.TestCase):
    def setUp(self):
        self.js = {name: (UI / name).read_text(encoding="utf-8") for name in ("app.js", "squad.js", "decoy.js")}

    def topics(self) -> set:
        found = set()
        for text in self.js.values():
            found |= set(re.findall(r'troubleLink\("(\w+)"\)', text))
            found |= set(re.findall(r'helpLine\([^;]*?, "(\w+)"(?:, "[\w -]+")?\)', text))
            found |= set(re.findall(r'open_help\("wiki", "(\w+)"\)', text))
        return found

    def test_every_topic_the_page_asks_for_is_one(self):
        self.assertEqual(self.topics(), set(WIKI_TOPICS))

    def test_beside_each_hard_box(self):
        app, squad, decoy = self.js["app.js"], self.js["squad.js"], self.js["decoy.js"]
        self.assertIn('helpLine(how, "blender")', app)                    # the Model row's Blender box
        self.assertIn('helpLine(w.fit_checked, "bones")', app)            # Will it work in the game?
        self.assertIn('helpLine(w.fit_halves_example, "bones")', app)     # Its two halves
        self.assertIn('helpLine(w.actions_how, "animations")', app)       # Its animations
        self.assertIn('"blender", "squad-how")', squad)                   # the squad card's big button
        self.assertIn('helpLine(w.decoy_blender_how, "animations")', decoy)   # RUSE Decoy's Blender box
        self.assertIn('$("da-help").addEventListener("click"', decoy)     # RUSE Decoy's animation window
        page = (UI / "index.html").read_text(encoding="utf-8")
        self.assertIn('<button id="da-help" type="button" class="link small trouble-link">', page)

    def test_a_link_with_a_tooltip_never_a_new_button(self):
        link = re.search(r"function troubleLink\(topic\) \{(.*?)\n\}", self.js["app.js"], re.S).group(1)
        self.assertIn('className: "link small trouble-link"', link)   # (the page's quiet link look, not a button's)
        self.assertIn("title: w[`tip_help_trouble_${topic}`]", link)
        self.assertIn('$("da-help").title = w.tip_help_trouble_animations', self.js["decoy.js"])

    def test_its_words_in_eleven_languages_and_on_the_stand_in_page(self):
        words = tomllib.loads((UI.parent / "words.toml").read_text(encoding="utf-8"))
        fake = (UI / "fake-api.js").read_text(encoding="utf-8")
        for key in ["help_trouble", *(f"tip_help_trouble_{t}" for t in WIKI_TOPICS)]:
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), set(LANGS))
                for lang in LANGS:
                    self.assertTrue(words[key][lang].strip(), lang)
                    self.assertNotIn("{", words[key][lang], lang)   # (no blanks in these)
                self.assertGreaterEqual(fake.count(f'"{key}":'), 3)   # (us, fr and sc on the stand-in page)


if __name__ == "__main__":
    unittest.main()
