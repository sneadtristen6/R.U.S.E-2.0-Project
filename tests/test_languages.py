"""The apps' eleven languages (the owner, 2026-10-30: Persian in the Studio and the Launcher; "a wiki and readmes and
the updates in every language we support"): the game's ten and Persian, which the game hasn't got.

The words files' own tests check each word is in every language (schema.APP_LANGS); these check what Persian brings
(the first start's guess, right-to-left text, the game's own languages left at ten) and that every language has its
README, wiki and update notes, with every wiki link leading to a page that exists."""
from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path
from urllib.parse import unquote

from rusemod import community, loc, mission, schema, uilang

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "docs" / "wiki"
NOTES = ROOT / ".github" / "release-notes"
OTHERS = [lang for lang in schema.APP_LANGS if lang != "us"]


def notes_json():
    spec = importlib.util.spec_from_file_location("notes_json", ROOT / "installers" / "notes_json.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pages() -> dict[str, Path]:
    """Every wiki page by its name on GitHub (the file's name: GitHub's wiki names pages by it, in any folder)."""
    out = {}
    for p in WIKI.rglob("*.md"):
        if p.stem != "_Sidebar":
            assert p.stem not in out, f"two wiki pages called {p.stem}: {out[p.stem]} and {p}"
            out[p.stem] = p
    return out


class Languages(unittest.TestCase):
    def test_the_apps_have_the_game_s_ten_and_persian(self):
        self.assertEqual(schema.APP_LANGS, schema.LANGS + ("fa",))
        listed = {lang["code"]: lang for lang in schema.languages()}
        self.assertEqual(list(listed), ["base", *schema.APP_LANGS])
        self.assertEqual(listed["fa"]["name"], "فارسی")
        self.assertTrue(listed["fa"]["rtl"])
        self.assertFalse(any(lang.get("rtl") for code, lang in listed.items() if code != "fa"))
        # the game's own languages (its text folders, a mission's texts) stay the game's ten
        self.assertEqual(loc.LANGS, schema.LANGS)
        self.assertEqual(mission.LANGS, schema.LANGS)

    def test_a_persian_pc_gets_persian_even_when_the_game_is_in_english(self):
        self.assertEqual(uilang.suggest("english", "fa-IR"), ("fa", "pc"))  # the game in Steam can't be in Persian
        self.assertEqual(uilang.suggest(None, "fa_IR"), ("fa", "pc"))
        self.assertEqual(uilang.suggest("english", "fr-FR"), ("us", "steam"))  # a language the game has: Steam's
        self.assertEqual(uilang.language_code("fa-IR"), "fa")

    def test_persian_text_reads_right_to_left_in_both_apps(self):
        studio, launcher = ROOT / "src/ruse_studio", ROOT / "src/ruse_launcher"
        self.assertEqual((studio / "ui/rtl.js").read_bytes(), (launcher / "ui/rtl.js").read_bytes())
        for app in (studio, launcher):
            with self.subTest(app=app.name):
                page = (app / "ui/index.html").read_text(encoding="utf-8")
                self.assertLess(page.index('<script src="rtl.js"></script>'), page.index('<script src="app.js"></script>'))
                self.assertIn("window.rtlText(", (app / "ui/app.js").read_text(encoding="utf-8"))
                self.assertIn('"rtl.js"', (app / "app.py").read_text(encoding="utf-8"))  # the built app's self-test
                css = (app / "ui/style.css").read_text(encoding="utf-8")
                self.assertIn('html[data-lang="fa"]', css)  # a font with Persian letters

    def test_the_update_notes_in_every_language(self):
        self.assertEqual(sorted(notes_json().LANGS), sorted(OTHERS))
        version = re.compile(r"^\*\*(\d+\.\d+\.\d+(?:\.\d+)?):\*\*", re.M)
        for app in ("launcher", "studio"):
            english = version.findall((NOTES / f"{app}.md").read_text(encoding="utf-8-sig"))
            for lang in OTHERS:
                with self.subTest(app=app, lang=lang):
                    mine = version.findall((NOTES / f"{app}.{lang}.md").read_text(encoding="utf-8-sig"))
                    self.assertEqual(mine, english)  # every version, in the same order

    def test_a_readme_and_a_wiki_in_every_language(self):
        english = sorted(p.stem for p in WIKI.glob("*.md") if p.stem != "_Sidebar")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        side = (WIKI / "_Sidebar.md").read_text(encoding="utf-8")
        for lang in OTHERS:
            with self.subTest(lang=lang):
                own = (ROOT / f"README.{lang}.md").read_text(encoding="utf-8")
                self.assertIn(f"(README.{lang}.md)", readme)  # the English page's language line leads to it
                self.assertIn("[English](README.md)", own)
                self.assertEqual(len(list((WIKI / lang).glob("*.md"))), len(english))
                home = community.WIKI_HOMES[lang]
                self.assertTrue((WIKI / lang / f"{home}.md").is_file(), home)  # where the apps' wiki button leads
                self.assertIn(f"|{home}]]", side)  # the sidebar's language line

    def test_every_wiki_link_leads_to_a_page(self):
        names = pages()
        wiki = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/wiki"
        for p in [*WIKI.rglob("*.md"), *ROOT.glob("README*.md")]:
            text = p.read_text(encoding="utf-8")
            for link in re.findall(r"\[\[([^\]]+)\]\]", text):
                page = link.rpartition("|")[2].split("#", 1)[0].strip().replace(" ", "-")
                with self.subTest(file=p.name, link=link):
                    self.assertIn(page, names)
            for page in re.findall(re.escape(wiki) + r"/([^\s)#\"'>]+)", text):
                with self.subTest(file=p.name, page=page):
                    self.assertIn(unquote(page), names)


if __name__ == "__main__":
    unittest.main()
