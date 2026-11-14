"""A job's last words in the player's language (rusemod.buildtext ENDS; the units scenarios' U-16, 2026-11-14: Test in
game's "R.U.S.E. is starting from ... To see your changes: ...", Play's "R.U.S.E. is starting." and a Play refused
before it starts were English in every language; the owner, 2026-11-14: "There shouldn't be anywhere where it's like
relying too heavily on them to understand things."): every job's done words, its refusals before it starts, the words
of a job that broke and Play's own refusals are in buildtext.toml (test_buildtext checks them all), and the apps hand
them to the page in the player's language. The controls: English is said as before, word for word."""
import tempfile
import time
import unittest
from pathlib import Path

from rusemod import buildtext
from rusemod.webui import Job, page_api
from ruse_launcher.api import LauncherApi
from test_studio import M4, WithMod


def ended(api, job_id: str, timeout: float = 20) -> dict:
    end = time.time() + timeout
    while api.job(job_id)["state"] == "running" and time.time() < end:
        time.sleep(0.02)
    return api.job(job_id)


class TestInGame(WithMod):
    def run_test(self, lang: str) -> dict:
        self.api.set_pref("lang", lang)
        self.api.new_mod("Tank Test")
        self.api.edit(M4, "SeuilMort", 15)
        return ended(self.api, self.api.test_in_game()["job"])

    def test_its_last_words_in_the_studio_s_language(self):
        j = self.run_test("ger")
        copy = self.home / "copies" / "Modded game"
        self.assertEqual((j["state"], j["message"]),
                         ("done", f"R.U.S.E. startet aus {copy}. So sehen Sie Ihre Änderungen: Ihre "
                                  f"Einheitenänderungen zeigen sich in jedem Spielmodus."), j)
        self.assertIn("  Ihre Einheitenänderungen zeigen sich in jedem Spielmodus.", j["lines"])

    def test_control_in_english_word_for_word_as_before(self):
        j = self.run_test("us")
        copy = self.home / "copies" / "Modded game"
        self.assertEqual((j["state"], j["message"]),
                         ("done", f"R.U.S.E. is starting from {copy}. To see your changes: your unit changes show in "
                                  f"every game mode."), j)
        self.assertIn("  Your unit changes show in every game mode.", j["lines"])

    def test_a_job_that_broke_says_its_frame_in_the_studio_s_language(self):
        self.api.set_pref("lang", "cz")
        job = Job()
        self.api._jobs[job.id] = job

        def work(say):
            raise KeyError("a fault of the Studio")
        job.start(work, "never")
        j = ended(self.api, job.id)
        self.assertEqual((j["state"], j["message"]), ("failed", "Něco se pokazilo: KeyError: 'a fault of the Studio'"))


class Play(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.api = LauncherApi(home=self.tmp / "home", game_dir=self.tmp / "nowhere")
        self.page = page_api(self.api)

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_play_refused_before_it_starts_in_the_launcher_s_language(self):
        self.api.set_pref("lang", "pol")
        j = self.page.job(self.page.play("nope")["job"])
        self.assertEqual((j["state"], j["message"]), ("failed", "Nie ma zestawu modów o nazwie 'nope'."))

    def test_control_in_english_word_for_word_as_before(self):
        self.api.set_pref("lang", "us")
        j = self.page.job(self.page.play("nope")["job"])
        self.assertEqual((j["state"], j["message"]), ("failed", "There's no mod set called 'nope'."))

    def test_play_s_own_refusals_and_last_words(self):
        for english, french in (
                ("R.U.S.E. is starting.", "R.U.S.E. se lance."),
                ("These mods have errors (listed above). Nothing was changed.",
                 "Ces mods contiennent des erreurs (listées plus haut). Rien n'a été changé."),
                ("Steam didn't start. Start Steam, then try again.",
                 "Steam n'a pas démarré. Lancez Steam, puis réessayez.")):
            with self.subTest(english=english):
                self.assertEqual(buildtext.worded(english, "fr"), french)


class BuildLinesFromTheStepsFiles(unittest.TestCase):
    """A build's lines said in the files of the steps it runs (rusemod/sound.py, unitlook.py, gamefiles.py,
    gamepatch.py, signature.py, players.py, scenario.py) and the Generic Horse's steps (horsesquad.py): progress lines
    of the kind already translated (the owner's pick of 2026-10-16), English in every language because buildtext
    didn't read those files. test_buildtext checks every one has its words; these, that they come out said."""

    def test_in_the_player_s_language(self):
        for line, lang, said in (
                ("sound volume: Sound/Fx/Tank.wav at 150%", "ru", "громкость звука: Sound/Fx/Tank.wav на 150%"),
                ("game file: ZZ_Win.dat: mods/paint/new.tgv (added, from paint)", "jpn",
                 "ゲームファイル: ZZ_Win.dat: mods/paint/new.tgv（追加、paint から）"),
                ("Generic Horse: making the animations", "spa", "Caballo genérico: haciendo las animaciones"),
                ("game patch own-squads: downloading own-squads-24670294.json", "ger",
                 "Spiel-Patch own-squads: own-squads-24670294.json wird heruntergeladen")):
            with self.subTest(line=line):
                self.assertEqual(buildtext.worded(line, lang), said)

    def test_control_english_and_a_line_no_entry_makes(self):
        self.assertEqual(buildtext.worded("sound volume: Sound/Fx/Tank.wav at 150%", "us"),
                         "sound volume: Sound/Fx/Tank.wav at 150%")
        self.assertEqual(buildtext.worded("unpack", "fr"), "unpack")   # (a step's name for the page, not words)


if __name__ == "__main__":
    unittest.main()
