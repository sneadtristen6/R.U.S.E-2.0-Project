"""A Test in game the build stopped: its mistakes, each with its fix (owner, 2026-10-02: an old team spawn on D-Day and a
road that joined nothing blocked every test, buried in the log, with no way out but the troubleshooter)."""
import tempfile
import time
import tomllib
import unittest
from pathlib import Path

from ruse_studio.api import StudioApi, StudioError
from rusemod.build import BuildError
from rusemod.webui import Job

SPAWN = ("test, test2: M04_cotentin: scenario.toml: the spawn of Unit_Konoe_Shidan at (2029166, 1329890) in "
         "leveldesign_3v3_v01.scenario is for camp 1, but leveldesign_3v3_v01.scenario is a skirmish map's scenario, "
         "and a skirmish game spawns only neutral items: the game would leave it out without a word. Set camp = -1 "
         "(or leave camp out), or spawn it in an Operation's scenario")
ROAD = ("test, test2: M04_cotentin: road 3 (its ends joined no road within 12 m) would be cut off from the rest of the "
        "map's roads; every road network the game ships is one piece, and supply routes between two pieces fail. "
        "Draw each end onto a road, or give the road a larger join")


def mod(root: Path, name: str, scenario: str = "", roads: str = "") -> Path:
    folder = root / name
    (folder / "maps" / "M04_cotentin").mkdir(parents=True)
    (folder / "mod.toml").write_text(f'[mod]\nid = "{name}"\nname = "{name}"\nversion = "0.1.0"\n', encoding="utf-8")
    if scenario:
        (folder / "maps" / "M04_cotentin" / "scenario.toml").write_text(scenario, encoding="utf-8")
    if roads:
        (folder / "maps" / "M04_cotentin" / "roads.toml").write_text(roads, encoding="utf-8")
    return folder


def road(x: float) -> str:
    return f"[[road]]\npoints = [[{x}, 100.0], [{x + 5000}, 100.0]]\njoin = 3000.0\n\n"


class TheJob(unittest.TestCase):
    def test_a_failed_build_s_errors_and_order_reach_the_window(self):
        exc = BuildError("These mods have errors (listed above). Nothing was changed.")
        exc.errors, exc.order = [SPAWN], ["test", "test2"]
        job = Job()

        def work(say):
            raise exc
        job.start(work, "done", plain=(BuildError,))
        end = time.time() + 5
        while job.state == "running" and time.time() < end:
            time.sleep(0.01)
        view = job.view()
        self.assertEqual((view["state"], view["errors"]), ("failed", [SPAWN]))
        self.assertEqual(job.order, ["test", "test2"])

    def test_a_job_without_errors_looks_as_before(self):
        self.assertNotIn("errors", Job().view())


class Problems(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.api = StudioApi(home=root / "home", find=lambda: None, index_path=root / "none.sqlite")
        spawns = ('[[spawn]]\nfile = "leveldesign_3v3_v01.scenario"\nwhat = "Unit_M4_Sherman"\nx = 10.0\ny = 20.0\n\n'
                  '[[spawn]]\nfile = "leveldesign_3v3_v01.scenario"\nwhat = "Unit_Konoe_Shidan"\nx = 2029166.4\n'
                  'y = 1329889.7\ncamp = 1\n')
        self.test = mod(root, "test", roads=road(0) + road(100000))           # roads 1 and 2
        self.test2 = mod(root, "test2", scenario=spawns, roads=road(200000))  # road 3, and the spawn
        self.outside = mod(root, "other", roads=road(0))
        job = Job()
        job.state, job.errors, job.order = "failed", [SPAWN, ROAD, "test: something else"], ["test", "test2"]
        self.api._jobs[job.id] = job
        self.api._test_job = job.id
        self.api._test_folders = [self.test, self.test2]

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_mistake_finds_its_item(self):
        spawn, road3, other = self.api.test_problems()["problems"]
        self.assertEqual(spawn["mod"], "test2")
        self.assertEqual([f["kind"] for f in spawn["fixes"]], ["spawn_neutral", "spawn_remove"])
        self.assertEqual(spawn["fixes"][0]["what"], "Unit_Konoe_Shidan")
        self.assertEqual((road3["mod"], [f["road"] for f in road3["fixes"]]), ("test2", [3]))  # numbered across mods
        self.assertEqual(road3["fixes"][0]["points"], [[200000.0, 100.0], [205000.0, 100.0]])
        self.assertEqual((other["fixes"], other["mod"]), ([], ""))  # words only: no one-click fix

    def test_making_the_spawn_neutral_keeps_the_rest(self):
        fix = self.api.test_problems()["problems"][0]["fixes"][0]
        self.assertIn("made neutral", self.api.test_fix(fix)["done"])
        data = tomllib.loads((self.test2 / "maps" / "M04_cotentin" / "scenario.toml").read_text(encoding="utf-8"))
        self.assertEqual([(s["what"], s.get("camp", -1)) for s in data["spawn"]],
                         [("Unit_M4_Sherman", -1), ("Unit_Konoe_Shidan", -1)])

    def test_removing_the_spawn_or_the_road_takes_only_that(self):
        spawn, road3, _ = self.api.test_problems()["problems"]
        self.api.test_fix(spawn["fixes"][1])
        data = tomllib.loads((self.test2 / "maps" / "M04_cotentin" / "scenario.toml").read_text(encoding="utf-8"))
        self.assertEqual([s["what"] for s in data["spawn"]], ["Unit_M4_Sherman"])
        self.api.test_fix(road3["fixes"][0])
        self.assertFalse((self.test2 / "maps" / "M04_cotentin" / "roads.toml").exists())  # its only road
        left = tomllib.loads((self.test / "maps" / "M04_cotentin" / "roads.toml").read_text(encoding="utf-8"))
        self.assertEqual(len(left["road"]), 2)  # the other mod's roads stay
        with self.assertRaisesRegex(StudioError, "isn't in the mod any more"):
            self.api.test_fix(road3["fixes"][0])  # done once: never a second road by mistake

    def test_every_team_spawn_of_the_setup_at_once(self):
        """The build stops at the first team spawn: the owner's old mod had 57 on D-Day, one test each without this."""
        path = self.test2 / "maps" / "M04_cotentin" / "scenario.toml"
        more = ''.join(f'\n[[spawn]]\nfile = "leveldesign_3v3_v01.scenario"\nwhat = "Unit_M4_Sherman"\nx = {k}.0\ny = 5.0\n'
                       f'camp = 2\n' for k in range(3))
        more += '\n[[spawn]]\nfile = "leveldesign_normal.scenario"\nwhat = "Unit_M4_Sherman"\nx = 1.0\ny = 1.0\ncamp = 1\n'
        path.write_text(path.read_text(encoding="utf-8") + more, encoding="utf-8")
        fixes = self.api.test_problems()["problems"][0]["fixes"]
        everyone = next(f for f in fixes if f["kind"] == "spawns_neutral_all")
        self.assertEqual(everyone["count"], 4)  # this setup's: the Konoe Shidan and 3 Shermans, not the other setup's
        self.assertIn("4 team spawn(s)", self.api.test_fix(everyone)["done"])
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertEqual([(s["file"], s.get("camp", -1)) for s in data["spawn"]],
                         [("leveldesign_3v3_v01.scenario", -1)] * 5 + [("leveldesign_normal.scenario", 1)])
        gone = {**everyone, "kind": "spawns_remove_all", "file": "leveldesign_normal.scenario"}
        self.api.test_fix(gone)
        self.assertEqual(len(tomllib.loads(path.read_text(encoding="utf-8"))["spawn"]), 5)

    def test_only_the_last_test_s_files(self):
        fix = {"kind": "road_remove", "path": str(self.outside / "maps" / "M04_cotentin" / "roads.toml"),
               "points": [[0.0, 100.0], [5000.0, 100.0]]}
        with self.assertRaisesRegex(StudioError, "isn't part of the last test"):
            self.api.test_fix(fix)
        self.assertTrue((self.outside / "maps" / "M04_cotentin" / "roads.toml").exists())

    def test_no_failed_test_no_problems(self):
        self.api._test_job = None
        self.assertEqual(self.api.test_problems(), {"problems": []})


if __name__ == "__main__":
    unittest.main()
