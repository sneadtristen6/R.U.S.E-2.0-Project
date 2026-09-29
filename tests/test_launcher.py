"""The launcher app's back end (ruse_launcher.api) on a made-up game folder; nothing starts for real."""
import os
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from test_build import PACK, price, write_mod
from ruse_launcher import app
from ruse_launcher.api import LauncherApi
from rusemod.play import STEAM_OPEN, STEAM_PLAY
from rusemod.webui import serve


def wait_for(api, job_id, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        j = api.job(job_id)
        if j["state"] != "running":
            return j
        time.sleep(0.02)
    raise AssertionError("the job didn't finish")


class Launcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        (self.game / "Data" / "PC" / "190852").mkdir(parents=True)
        (self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        self.home, self.instances = root / "home", root / "copies"
        self.urls, self.started = [], []
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop("RUSE_GAME", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def api(self, **kw):
        args = dict(game_dir=self.game, home=self.home, instances=self.instances, open_url=self.urls.append,
                    start_game=self.started.append, steam_running=lambda: True, wait=lambda s: None)
        args.update(kw)
        return LauncherApi(**args)

    def mod_set(self, name, mods, body=""):
        (self.home / "sets").mkdir(parents=True, exist_ok=True)
        lines = ", ".join(f'"{Path(m).as_posix()}"' for m in mods)
        (self.home / "sets" / f"{name}.toml").write_text(f'name = "{name.title()}"\nmods = [{lines}]\n{body}',
                                                         encoding="utf-8")

    def test_status(self):
        s = self.api().status()
        self.assertTrue(s["found"])
        self.assertEqual(s["build"], "24687178")
        self.assertIn("(build 24687178)", s["message"])
        s = self.api(game_dir=None, find=lambda: None).status()
        self.assertEqual((s["found"], s["message"]), (False, "We couldn't find R.U.S.E. Is it installed through Steam?"))

    def test_choosing_the_game_folder(self):
        wrong = Path(self.tmp.name)
        api = self.api(game_dir=None, find=lambda: None, pick_folder=lambda: str(wrong))
        self.assertIn("doesn't have RUSE.exe", api.choose_game_folder()["message"])
        api._pick_folder = lambda: str(self.game)
        self.assertTrue(api.choose_game_folder()["found"])
        self.assertTrue(self.api(game_dir=None, find=lambda: None).status()["found"])  # remembered

    def test_mod_sets(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod], 'description = "Every building costs half."\n')
        self.mod_set("empty", [])
        (self.home / "sets" / "Bad Name.toml").write_text("mods = []", encoding="utf-8")
        sets = self.api().mod_sets()
        self.assertEqual([s["id"] for s in sets], ["vanilla", "bad name", "empty", "half"])
        half = sets[-1]
        self.assertEqual((half["name"], half["description"], half["mod_names"]),
                         ("Half", "Every building costs half.", ["econ-half"]))
        self.assertIn("lowercase", sets[1]["error"])
        self.assertEqual(sets[2]["error"], "it lists no mods")

    def test_play_vanilla_goes_through_steam(self):
        api = self.api()
        j = wait_for(api, api.play("vanilla")["job"])
        self.assertEqual((j["state"], self.urls), ("done", [STEAM_PLAY]))

    def test_play_a_mod_set_builds_the_copy_and_starts_it(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod])
        api = self.api()
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / "half"
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
        self.assertEqual(self.started, [copy / "RUSE.exe"])
        self.assertTrue(any("modded copy ready" in line for line in j["lines"]))
        later = api.job(j["id"], since=j["count"])
        self.assertEqual(later["lines"], [])  # `since` skips the lines already shown

    def test_steam_is_started_first_when_it_isnt_running(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod])
        answers = iter([False, False, True])
        api = self.api(steam_running=lambda: next(answers))
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(self.urls, [STEAM_OPEN])
        self.assertIn("Starting Steam…", j["lines"])

    def test_problems_end_the_job_with_a_plain_message(self):
        bad = write_mod(self.tmp.name, "bad", {"x.rndf": "patch $/Nope ( P = 1 )"})
        self.mod_set("bad", [bad])
        self.mod_set("empty", [])
        api = self.api()
        j = wait_for(api, api.play("bad")["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("have errors", j["message"])
        self.assertEqual(self.started, [])
        self.assertIn("has a mistake", api.job(api.play("empty")["job"])["message"])
        self.assertIn("no mod set called", api.job(api.play("nope")["job"])["message"])


class Window(unittest.TestCase):
    def test_the_screens_are_served_on_this_pc_only(self):
        server, base = serve(app.UI)
        try:
            self.assertTrue(base.startswith("http://127.0.0.1:"))
            with urllib.request.urlopen(f"{base}/index.html") as r:
                self.assertIn(b"RUSE", r.read())
        finally:
            server.shutdown()
            server.server_close()

    def test_without_pywebview_it_says_how_to_install_it(self):
        with mock.patch.dict(sys.modules, {"webview": None}):
            with mock.patch("builtins.print") as out:
                self.assertEqual(app.main([]), 2)
        self.assertIn("pip install pywebview", out.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
