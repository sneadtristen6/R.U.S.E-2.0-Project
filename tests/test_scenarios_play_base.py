"""Scenario tests' base: what a player meets around Test in game (the RUSE Studio) and Play (the RUSE Launcher) on the
same PC (the owner, overnight 2026-11-13/14: "Usual and unusual situations. Player can find themselves in when making
new mods in our apps.").

The made-up game is the Studio tests' own (tests/test_studio.py WithMod: write_game's units, its index built once per
class), and nothing starts: the Studio tests' Starter stands in for opening links, starting the game, Steam and waiting.
The Launcher here is the real LauncherApi on the SAME platform folder, game folder and modded-copy folder as the
Studio, as both apps are on a player's PC (they share settings.json, the library and the one modded copy). Each call
is made as the page makes it: the Studio's through rusemod.webui.page_api (a refusal said in the Studio's language),
the Launcher's on the API itself (its window calls it directly); every language where the page says something.

Bug Watch's crash reports are never read from this PC: LOCALAPPDATA points at a folder of the test, so a game watch
looks only at the made-up reports a test writes there.

FOR: the Test in game and Play scenarios (release 0.9.8.20, overnight 2026-11-14,
D:/RUSE-2.0/scratch/release-0920/scenarios/play). USED-BY: tests/test_scenarios_play_*.py."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from test_studio import M4, WithMod

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
PYTHON_WORDS = ("Traceback", "Errno", "WinError", "KeyError", "TypeError", "ValueError", "NoneType", "object has no")


def fill(word: str, **values) -> str:
    """app.js fill / fillText: each {key} in `word` replaced by its value."""
    for k, v in values.items():
        word = word.replace("{" + k + "}", str(v))
    return word


class PlayScenario(WithMod):
    """A player's PC: the Studio (WithMod's, its Starter standing in) and the Launcher on one platform folder."""

    def setUp(self):
        super().setUp()
        self.local = Path(tempfile.mkdtemp(dir=self.tmp.name))   # (this PC's LOCALAPPDATA, for Bug Watch: the test's)
        env = mock.patch.dict(os.environ, {"LOCALAPPDATA": str(self.local)})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        from rusemod.webui import page_api
        self.page = page_api(self.api)
        self.addCleanup(self.api.set_pref, "lang", "us")
        self.urls = []

    # --- the two apps ---
    def launcher(self, **kw):
        """The Launcher on this PC: the same platform folder, game folder and modded copies as the Studio."""
        from ruse_launcher.api import LauncherApi
        args = dict(game_dir=self.game, home=self.home, instances=self.home / "copies", open_url=self.urls.append,
                    start_game=self.started.append, steam_running=lambda: True, wait=lambda s: None)
        args.update(kw)
        return LauncherApi(**args)

    def copy(self) -> Path:
        """The PC's one modded copy (rusemod.play.SHARED, in the copies folder both apps were given)."""
        from rusemod.play import SHARED
        return self.home / "copies" / SHARED

    def exe_of(self, folder: Path) -> Path:
        """The game's program file in `folder` (the copy, or the game), as the Starter finds it."""
        return next(p for p in Path(folder).iterdir() if p.suffix.lower() == ".exe")

    def wait(self, job: str, api=None, most: float = 30) -> dict:
        """A job's view once it has ended (as the page follows it)."""
        api = api or self.api
        end = time.time() + most
        while time.time() < end:
            view = api.job(job)
            if view["state"] != "running":
                return view
            time.sleep(0.02)
        raise AssertionError(f"job {job} still running after {most} s")

    def in_game(self, lang: str = "us") -> dict:
        """Test in game clicked (the page's call), in `lang`, followed to its end: the job's view as the page gets it."""
        self.api.set_pref("lang", lang)
        try:
            return self.wait(self.page.test_in_game()["job"])
        finally:
            self.api.set_pref("lang", "us")

    def played(self, launcher, set_id: str, lang: str = "us") -> dict:
        launcher.set_pref("lang", lang)
        try:
            return self.wait(launcher.play(set_id)["job"], launcher)
        finally:
            launcher.set_pref("lang", "us")

    def every_language(self, call) -> dict:
        """{lang: call(lang)} for the Studio's 11 languages."""
        return {lang: call(lang) for lang in LANGS}

    def refused(self, name: str, *args) -> dict:
        """The Studio's `name` called as the page calls it, once per language: {lang: the refusal's words} (None: not
        refused)."""
        from ruse_studio.api import StudioError
        out = {}
        for lang in LANGS:
            self.api.set_pref("lang", lang)
            try:
                getattr(self.page, name)(*args)
                out[lang] = None
            except StudioError as exc:
                out[lang] = str(exc)
        self.api.set_pref("lang", "us")
        return out

    def words(self, lang: str) -> dict:
        from ruse_studio.api import words
        return words(lang)

    def launcher_words(self, lang: str) -> dict:
        from ruse_launcher.api import words
        return words(lang)

    def assert_worded(self, said: dict, english: str | None = None) -> None:
        """Every language's words for one thing a page says: English as `english` when given, every other language its
        own words (never the English left in, never Python's words, no blank left unfilled)."""
        if english is not None:
            self.assertEqual(said["us"], english)
        for lang in LANGS:
            with self.subTest(lang=lang):
                text = said[lang]
                self.assertTrue(text, lang)
                if lang != "us":
                    self.assertNotEqual(text, said["us"], f"{lang}: English left in")
                for bad in PYTHON_WORDS:
                    self.assertNotIn(bad, text, lang)
                self.assertNotRegex(text, r"\{[a-z_0-9]*\}", lang)

    # --- the mod ---
    def a_mod(self, name: str = "Tank Test", value: int = 15) -> Path:
        """New mod, and one value changed on the made-up game's M4 (its SeuilMort), as the Units tab does."""
        folder = Path(self.page.new_mod(name)["current"])
        self.page.edit(M4, "SeuilMort", value)
        return folder

    def problems(self) -> list:
        return [p.get("problem") for p in self.page.check_mod()["problems"]]
