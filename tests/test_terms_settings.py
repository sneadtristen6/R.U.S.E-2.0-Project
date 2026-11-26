"""Settings' "Terms, credits and licences" section and the uninstall question (the owner, 2026-11-25, decision 19:
"Yes, for 19, add a second setting for that.").

- Both apps' page API (rusemod.webui.page_api) answers terms_info on a scratch home: the version accepted (0 before
  Accept, the version after guard_accept_terms) and the text of THIRD_PARTY_NOTICES.md and LICENSE, as they are in the
  repository (the files the installers copy beside the program: installers/build_app.py licence_files). A missing file
  is None, never other text.
- Both apps' pages carry the section (one section, three folds, no new buttons) and its words in all 11 languages,
  with a tooltip for each fold; the words are the same in both apps.
- Both installers (installers/installer.iss, one script): the question at uninstall answers No unless chosen, never
  deletes on a silent uninstall, deletes only the default platform folder, and is worded in all 11 languages.
  (Compiling it with Inno Setup is a separate check; this test reads the script.)

FOR: the Settings section and the uninstall question. USED-BY: the test runs (gentle.py, -m unittest)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import os
import re
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import termscalls
from rusemod.webui import page_api

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
APPS = ("ruse_launcher", "ruse_studio")
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
KEYS = ("set_terms_title", "set_terms_help", "terms_accepted", "terms_accepted_none", "terms_newer", "terms_read_agreement",
        "terms_read_credits", "terms_read_licence", "terms_missing", "tip_terms_agreement", "tip_terms_credits",
        "tip_terms_licence")
TMP = os.environ.get("RUSE_TEST_TMP") or None


class Api(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TMP)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def app(self, name):
        nowhere = self.root / "no game"
        if name == "ruse_launcher":
            from ruse_launcher.api import LauncherApi
            return page_api(LauncherApi(game_dir=nowhere, home=self.root / name, find=lambda: None,
                                        open_url=lambda url: None, start_game=lambda path: None,
                                        steam_running=lambda: True, wait=lambda s: None))
        from ruse_studio.api import StudioApi
        return page_api(StudioApi(index_path=self.root / "none.sqlite", game_dir=nowhere, find=lambda: None,
                                  home=self.root / name))

    def test_both_apps_give_the_version_accepted_and_the_two_files(self):
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")[:termscalls.LIMIT]
        licence = (ROOT / "LICENSE").read_text(encoding="utf-8")[:termscalls.LIMIT]
        for name in APPS:
            with self.subTest(app=name):
                api = self.app(name)
                before = api.terms_info()
                self.assertEqual(before["accepted"], 0)   # nothing accepted yet
                self.assertEqual(before["notices"], notices)
                self.assertEqual(before["licence"], licence)
                api.guard_accept_terms()
                after = api.terms_info()
                self.assertEqual(after["accepted"], after["current"])
                self.assertGreater(after["accepted"], 0)

    def test_an_older_version_accepted_is_said_as_it_is(self):
        from rusemod.home import save_settings
        for n in APPS:
            save_settings(self.root / n, {"guard": {"terms": 3}})
        for name in APPS:
            with self.subTest(app=name):
                info = self.app(name).terms_info()
                self.assertEqual(info["accepted"], 3)
                self.assertGreater(info["current"], 3)

    def test_a_missing_file_is_none_never_other_text(self):
        empty = Path(self.tmp.name, "empty")
        empty.mkdir()
        self.assertIsNone(termscalls.read_shipped("LICENSE", [empty]))
        self.assertIsNotNone(termscalls.read_shipped("LICENSE", [empty, ROOT]))   # the next place is tried

    def test_the_apps_ship_the_files_the_section_reads(self):
        sys_build = ROOT / "installers" / "build_app.py"
        text = sys_build.read_text(encoding="utf-8")
        for name in termscalls.FILES.values():
            with self.subTest(name=name):
                self.assertIn(f'"{name}"', text)
                self.assertTrue((ROOT / name).is_file())


class Pages(unittest.TestCase):
    def test_the_section_and_its_folds_are_in_both_pages(self):
        for app in APPS:
            html = (SRC / app / "ui" / "index.html").read_text(encoding="utf-8")
            section = html[html.index('id="set-terms"'):]
            section = section[:section.index("</section>")]
            with self.subTest(app=app):
                self.assertEqual(section.count("<details>"), 3)
                self.assertNotIn("<button", section)   # his fewer-buttons rule: nothing to press but the folds
                for fold in ("agreement", "notices", "licence"):
                    self.assertIn(f'id="terms-{fold}-sum"', section)
                    self.assertIn(f'id="terms-{fold}-text"', section)
            js = (SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            self.assertIn("terms_info", js)
            self.assertIn("tip_terms_licence", js)
            self.assertIn("terms_info", (SRC / app / "ui" / "fake-api.js").read_text(encoding="utf-8"))

    def test_the_words_are_in_every_language_and_the_same_in_both_apps(self):
        words = {a: tomllib.loads((SRC / a / "words.toml").read_text(encoding="utf-8")) for a in APPS}
        for key in KEYS:
            for app in APPS:
                for lang in LANGS:
                    with self.subTest(key=key, app=app, lang=lang):
                        self.assertTrue(words[app][key][lang].strip())
            self.assertEqual(words["ruse_launcher"][key], words["ruse_studio"][key], key)
        for lang in LANGS:   # the placeholder the page fills is kept in every language
            self.assertIn("{version}", words["ruse_studio"]["terms_accepted"][lang])
            self.assertNotIn("{current}", words["ruse_studio"]["terms_accepted"][lang])


NODE = Path("D:/RUSE-2.0/tools/node-v24.22.2-win-x64/node.exe")
NEWER = "This is a newer version than the one you accepted."


@unittest.skipUnless(NODE.is_file(), "Node is not on this PC")
class Drawn(unittest.TestCase):
    """The section's own drawing code (ui/app.js) run in Node (tests/terms_render_in_node.mjs): what each app writes
    for each answer of terms_info, and in the Launcher before any answer."""

    def draw(self, app, info, lang="us"):
        import json
        import subprocess
        words = tomllib.loads((SRC / app / "words.toml").read_text(encoding="utf-8"))
        flat = {k: v[lang] for k, v in words.items() if isinstance(v, dict) and lang in v}
        tmp = tempfile.TemporaryDirectory(dir=TMP)
        self.addCleanup(tmp.cleanup)
        scenario = Path(tmp.name, "scenario.json")
        scenario.write_text(json.dumps({"words": flat, "info": info}), encoding="utf-8")
        run = subprocess.run([str(NODE), str(ROOT / "tests" / "terms_render_in_node.mjs"), str(SRC / app / "ui" / "app.js"),
                              "launcher" if app == "ruse_launcher" else "studio", str(scenario)],
                             capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout), flat

    def test_an_older_version_accepted_says_this_one_is_newer_in_both_apps_and_every_language(self):
        for app in APPS:
            for lang in LANGS:
                with self.subTest(app=app, lang=lang):
                    out, w = self.draw(app, {"accepted": 3, "current": 4, "notices": "n", "licence": "l"}, lang)
                    self.assertEqual(out["terms-accepted"], w["terms_accepted"].replace("{version}", "3") + " " + w["terms_newer"])
                    self.assertTrue(w["terms_newer"].strip())
            out, w = self.draw(app, {"accepted": 3, "current": 4, "notices": "n", "licence": "l"})
            self.assertIn(NEWER, out["terms-accepted"])

    def test_the_current_version_none_and_a_failure_do_not_say_newer(self):
        for app in APPS:
            for info in ({"accepted": 4, "current": 4}, {"accepted": 0, "current": 4}, {"failed": "no"}):
                with self.subTest(app=app, info=info):
                    out, w = self.draw(app, info)
                    self.assertNotIn(NEWER, out["terms-accepted"])
        out, w = self.draw("ruse_studio", {"accepted": 0, "current": 4})
        self.assertEqual(out["terms-accepted"], w["terms_accepted_none"])

    def test_the_launcher_writes_nothing_about_the_version_or_the_files_before_terms_info_answers(self):
        out, w = self.draw("ruse_launcher", None)
        self.assertEqual(out["terms-accepted"], "")   # not "You haven't accepted the agreement yet"
        self.assertEqual(out["terms-notices-text"], "")   # not "isn't on this PC"
        self.assertEqual(out["terms-licence-text"], "")
        self.assertTrue(out["terms-agreement-text"])   # the agreement's words are the app's own, not an answer

    def test_the_launcher_after_the_answer_says_what_it_is(self):
        out, w = self.draw("ruse_launcher", {"accepted": 0, "current": 4, "notices": None, "licence": "L"})
        self.assertEqual(out["terms-accepted"], w["terms_accepted_none"])
        self.assertEqual(out["terms-notices-text"], w["terms_missing"])   # a missing file is still said, once answered
        self.assertEqual(out["terms-licence-text"], "L")


class Installer(unittest.TestCase):
    ISS = (ROOT / "installers" / "installer.iss").read_text(encoding="utf-8-sig")

    def test_the_question_starts_on_no_and_is_never_asked_silently(self):
        code = self.ISS[self.ISS.index("procedure CurUninstallStepChanged"):]
        self.assertIn("MB_YESNO or MB_DEFBUTTON2", code)         # the second button, No, is the default
        self.assertIn("not UninstallSilent", code)               # a silent uninstall deletes nothing
        self.assertIn("usPostUninstall", code)
        self.assertEqual(self.ISS.count("DelTree"), 1)           # one place deletes folders
        self.assertIn("{localappdata}\\RUSE Mod Platform", code)   # only the default platform folder
        self.assertNotIn("PLATFORM_HOME", code)                   # a folder set by hand is never deleted

    def test_old_player_folders_are_kept(self):
        # before 2026-10-30 the player's mods, maps, exports and backups lived in the platform folder; a Yes must not
        # delete them for a player whose Studio has not moved them to Documents yet
        from rusemod.yourfiles import OLD_NAMES
        func = self.ISS[self.ISS.index("function IsOldPlayerFolder"):self.ISS.index("procedure DeleteSettingsAndData")]
        self.assertEqual(set(re.findall(r"Name, '([^']+)'", func)), set(OLD_NAMES.values()))
        body = self.ISS[self.ISS.index("procedure DeleteSettingsAndData"):self.ISS.index("procedure CurUninstallStepChanged")]
        self.assertRegex(body, r"if not IsOldPlayerFolder\(Found\.Name\) then\s+DelTree")
        self.assertNotIn("DelTree(Folder", self.ISS)             # never the whole folder in one go

    def test_it_is_worded_in_all_eleven_languages(self):
        languages = re.findall(r'^Name: "(\w+)"; MessagesFile', self.ISS, re.M)
        self.assertEqual(len(languages), 11)
        for lang in languages:
            with self.subTest(lang=lang):
                line = re.search(rf"^{lang}\.DeleteDataQuestion=(.+)$", self.ISS, re.M)
                self.assertIsNotNone(line)
                self.assertIn("RUSE 2.0", line.group(1))   # the folder that is never deleted is named


if __name__ == "__main__":
    unittest.main()
