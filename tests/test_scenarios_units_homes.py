"""Scenarios: a player whose Windows user folder isn't plain English letters (the owner, 2026-11-13 overnight: "Usual
and unusual situations. Player can find themselves in when making new mods in our apps"). Russian, Japanese, Chinese
and Persian players' user folders carry their names (C:\\Users\\Иван, C:\\Users\\山田), and names have spaces,
apostrophes and ampersands. The Studio's and the Launcher's platform folder (their mods, exports, library and copies)
is under it. A mod made there, a unit in it, its build, Export, the Launcher's library and Play (on the made-up game:
nothing starts), and the Studio started again. The made-up game comes from test_scenarios_units_base."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import tempfile
import time
import unittest
from pathlib import Path

from rusemod import package
from rusemod.webui import page_api
from ruse_launcher.api import LauncherApi
from test_scenarios_units_base import M1, S1, Player

HOMES = ("Иван Петров", "山田 太郎", "王小明", "علی رضایی", "Seán O'Brien & Co", "Zoë Ångström")


def wait(api, job: str, seconds: float = 120) -> dict:
    end = time.time() + seconds
    while api.job(job)["state"] == "running" and time.time() < end:
        time.sleep(0.05)
    return api.job(job)


class UserFolders(Player):
    def use_home(self, user: str) -> Path:
        home = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "Users" / user / "AppData" / "Local" / "RUSE Mod Platform"
        home.mkdir(parents=True)
        self.home = home
        self.api = self.studio(home)
        self.page = page_api(self.api)
        return home

    def test_a_mod_made_built_exported_and_played_from_each(self):
        for user in HOMES:
            with self.subTest(user=user):
                home = self.use_home(user)
                folder = self.mod("Home Test")
                made = self.call("new_unit", M1, "Home Tank", 40, -1, -1, False, None)["address"]
                self.call("new_unit", S1, "Home Squad", 20, -1, -1, False, None)
                self.call("edit", made, "SeuilMort", 25, "", "")
                self.assertEqual(self.build(folder)[0], [])
                j = wait(self.api, self.call("export_mod", "1.0.0", user, "")["job"])
                self.assertEqual(j["state"], "done", j)
                info = package.check(j["result"]["path"])
                self.assertEqual(info["authors"], [user])
                launcher = LauncherApi(game_dir=self.game, home=home, instances=home / "copies",
                                       open_url=lambda url: None, start_game=self.started.append,
                                       steam_running=lambda: True, wait=lambda s: None)
                set_id = launcher.new_set("Home set", [j["result"]["library"]])["set"]
                played = wait(launcher, launcher.play(set_id)["job"])
                self.assertEqual(played["state"], "done", played)
                self.restart()
                self.assertEqual(self.call("mods", "mod")["current"], str(folder))
                self.assertIn(made, [u["address"] for u in self.call("units")["units"] if u["new"]])


if __name__ == "__main__":
    unittest.main()
