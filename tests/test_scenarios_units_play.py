"""Scenarios: Test in game (the Studio's own) after making new units, as a player of each of the apps' languages
sees it (the owner, 2026-11-13 overnight: "Usual and unusual situations. Player can find themselves in when making new
mods in our apps"): the job built into the PC's modded copy of the made-up game (nothing starts: the game is a
stand-in), and its last words, which the page's card shows (ui/app.js runTest: card.done(ok, j.message)); and a mod
that doesn't build (a value file broken by hand). The made-up game comes from test_scenarios_units_base.

Each test marked expectedFailure shows a finding (its number in the comment above it; the agent's report lists them);
it passes once the finding is mended."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import time
import unittest

from test_scenarios_units_base import LANGS, M1, P1, S1, Player


def wait(api, job: str, seconds: float = 120) -> dict:
    end = time.time() + seconds
    while api.job(job)["state"] == "running" and time.time() < end:
        time.sleep(0.05)
    return api.job(job)


class TestInGame(Player):
    def run_test(self, lang: str) -> dict:
        """Test in game pressed with the Studio in `lang`, followed as the page follows it."""
        self.api.set_pref("lang", None if lang == "us" else lang)
        try:
            return wait(self.api, self.page.test_in_game()["job"])
        finally:
            self.api.set_pref("lang", None)

    def units(self):
        self.call("new_unit", M1, "Test Tank", 40, -1, -1, False, None)
        self.call("new_unit", S1, "Test Squad", 20, -1, -1, False, None)
        self.call("new_unit", P1, "Test Plane", 60, -1, -1, False, None)

    def test_built_and_started_in_every_language(self):
        self.mod("Play test")
        self.units()
        for lang in LANGS:
            with self.subTest(lang=lang):
                j = self.run_test(lang)
                self.assertEqual(j["state"], "done", j)
        self.assertEqual(len(self.started), len(LANGS))

    def test_a_mod_that_doesnt_build_starts_nothing(self):
        folder = self.mod("Broken play")
        self.units()
        (folder / "src" / "extra.rndf").write_text("patch $/GFX/Everything/Nope ( X = 1 )\n", encoding="utf-8")
        j = self.run_test("fr")
        self.assertEqual(j["state"], "failed", j)
        self.assertTrue(j["errors"], j)
        self.assertEqual(self.started, [])

    # U-16: Test in game's last words, on the card the page shows, are English in every language: "R.U.S.E. is starting
    # from <the copy>. To see your changes: your unit changes show in every game mode." (job.start's done message, which
    # rusemod.buildtext doesn't collect: it reads say, warn and Finding only), and for a mod that doesn't build "These
    # mods have errors (listed above). Nothing was changed." (rusemod.play's BuildError, the same)
    @unittest.expectedFailure
    def test_its_last_words_in_every_language(self):
        folder = self.mod("Play words")
        self.units()
        started = {lang: self.run_test(lang)["message"] for lang in LANGS}
        (folder / "src" / "extra.rndf").write_text("patch $/GFX/Everything/Nope ( X = 1 )\n", encoding="utf-8")
        stopped = {lang: self.run_test(lang)["message"] for lang in LANGS}
        self.assertEqual(self.english_left(started), [], started["fr"])
        self.assertEqual(self.english_left(stopped), [], stopped["fr"])


if __name__ == "__main__":
    unittest.main()
