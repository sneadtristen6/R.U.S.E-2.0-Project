"""The build's errors, warnings and lines in the player's language (rusemod.buildtext; the owner, 2026-10-16:
"Translate the 79 build errors and warnings and the build's progress lines"): every such text in the code has its
words in all ten languages with the same blanks, a line or a marked finding comes out in the player's language with
its values, and both apps hand their jobs' lines to the page that way."""
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import buildtext, wordedtext
from rusemod.webui import Job


class EveryTextHasItsWords(unittest.TestCase):
    def test_every_build_text_in_the_code_is_in_ten_languages(self):
        templates = buildtext.templates()
        self.assertGreater(len(templates), 130)
        self.assertEqual(wordedtext.missing(buildtext.FILE, templates), [],
                         "build texts with no words in buildtext.toml: list them and add their words")

    def test_no_entry_is_left_over(self):
        entries = tomllib.loads(buildtext.FILE.read_text(encoding="utf-8"))
        keys = {wordedtext.key_of(t) for t in buildtext.templates()}
        self.assertEqual(sorted(set(entries) - keys), [])


class Worded(unittest.TestCase):
    def test_lines_in_another_language(self):
        self.assertEqual(buildtext.worded("scenery: SuperCrossRoads4, from my-mod", "ger"),
                         "Szenerie: SuperCrossRoads4, aus my-mod")
        self.assertEqual(buildtext.worded("load order: base -> my-mod", "fr"), "ordre de chargement : base -> my-mod")
        self.assertEqual(buildtext.worded("Starting R.U.S.E. from the modded copy…", "sc"), "正在从模组副本启动 R.U.S.E.…")

    def test_a_finding_as_the_lines_mark_it(self):
        """"warning: <finding>" and the report's "  error    <finding>": the level in the player's words, the finding
        in theirs too (not "warning: {0}" with the finding left English)."""
        finding = ("my-mod: Blitz: the open at (100, 200) opened nothing: units could already go there, or it is too "
                   "small (an open needs a radius of 5 m or more) or out of reach of the ground they use")
        said = buildtext.worded(f"warning: {finding}", "spa")
        self.assertTrue(said.startswith("aviso: my-mod: Blitz: la apertura en (100, 200) no abrió nada"), said)
        said = buildtext.worded(f"  error    {finding}", "pol")
        self.assertTrue(said.startswith("  błąd    my-mod: Blitz: otwarcie w (100, 200) nic nie otworzyło"), said)

    def test_english_and_lines_from_deeper_down_stay(self):
        self.assertEqual(buildtext.worded("scenery: Blitz, from a", "us"), "scenery: Blitz, from a")
        self.assertEqual(buildtext.worded("  2 object(s) erased in 2 area(s): 2 vegetation", "fr"),
                         "  2 object(s) erased in 2 area(s): 2 vegetation")  # a step's own note: English for now

    def test_a_job_view(self):
        job = Job()
        job.say("load order: a -> b")
        job.say("menus: Blitz")
        job.state, job.message, job.errors = "failed", "Nothing was written.", ["my-mod: map.toml: x"]
        view = buildtext.worded_view(job.view(), "ita")
        self.assertEqual(view["lines"], ["ordine di caricamento: a -> b", "menu: Blitz"])
        self.assertEqual(view["message"], "Non è stato scritto nulla.")
        self.assertEqual(view["errors"], ["my-mod: map.toml: x"])  # (its own words from deeper down)
        self.assertEqual(buildtext.worded_view(job.view(), "us"), job.view())


class TheAppsSayItSo(unittest.TestCase):
    def test_the_studio_s_job_and_problems(self):
        from ruse_studio.api import StudioApi
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(game_dir=Path(tmp) / "nowhere", home=Path(tmp, "home"), index_path=Path(tmp, "x.sqlite"))
            api.set_pref("lang", "cz")
            job = Job()
            job.say("Building the modded copy of R.U.S.E. for my-mod in D:/copies…")
            api._jobs[job.id] = job
            self.assertEqual(api.job(job.id)["lines"], ["Sestavuji upravenou kopii R.U.S.E. pro my-mod v D:/copies…"])
            job.state, job.errors = "failed", ["my-mod: Blitz: the new roads can't be drawn (no ground)"]
            api._test_job, api._test_folders = job.id, []
            problems = api.test_problems()["problems"]
            self.assertEqual(problems[0]["text"], "my-mod: Blitz: nové silnice nelze nakreslit (no ground)")

    def test_the_launcher_s_job(self):
        from ruse_launcher.api import LauncherApi
        with tempfile.TemporaryDirectory() as tmp:
            api = LauncherApi(home=Path(tmp, "home"), game_dir=Path(tmp) / "nowhere")
            api.set_pref("lang", "ru")
            job = Job()
            job.say("Starting Steam…")
            api._jobs[job.id] = job
            self.assertEqual(api.job(job.id)["lines"], ["Запуск Steam…"])


if __name__ == "__main__":
    unittest.main()
