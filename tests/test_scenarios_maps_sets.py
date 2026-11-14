"""Scenarios: a player's map mod after it's made: exported and played in a mod set with a units mod (the Launcher's
mod sets), opened again after the Studio starts again, and deleted (Delete map, Delete a mod...), on the made-up game of
test_scenarios_maps_base. Each checks what the page is told, the files, and whether the map still builds.

FOR: the overnight scenario tests of map mods (owner, 2026-11-13). USED-BY: the release check of 0.9.8.20."""
import shutil
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from test_scenarios_maps_base import BLITZ, OAK, MapGame, page_said
from test_studio import M4
from rusemod.dic import name_to_key
from rusemod.edat import Edat
from rusemod.ndf import Ndf
from ruse_launcher.api import LauncherApi


class Sets(MapGame):
    """A units mod and a map mod made in the Studio, exported, and played together in one of the Launcher's mod sets."""

    def launcher(self):
        return LauncherApi(game_dir=self.game, home=self.home, instances=self.home / "launcher-copies",
                           open_url=lambda url: None, start_game=self.started.append, steam_running=lambda: True,
                           wait=lambda s: None, find=lambda: None)

    def export(self, kind):
        got = self.wait(self.api.export_mod("1.0.0", "Tester", f"A {kind} for a set.", kind=kind)["job"])
        self.assertEqual(got["state"], "done", got)
        return got

    def wait_launcher(self, api, job_id):
        import time
        end = time.time() + 120
        while time.time() < end:
            j = api.job(job_id)
            if j["state"] != "running":
                return j
            time.sleep(0.02)
        self.fail("the Launcher's job never ended")

    def test_a_units_mod_and_a_map_mod_in_one_set(self):
        self.api.new_mod("Tanks")
        self.api.edit(M4, "SeuilMort", 15)
        self.export("mod")
        self.api.new_mod("Blitz at Dusk", "map")   # Maps tab, top menu: new map changes
        self.api.duplicate_map(BLITZ, "Blitz at Dusk")
        self.api.scenery_add("BlitzAtDusk", [{"type": OAK, "x": 1500, "y": 1500}])
        self.export("map")
        launcher = self.launcher()
        ids = {m["name"]: m["id"] for m in launcher.library()}
        self.assertEqual(sorted(ids), ["Blitz at Dusk", "Tanks"])
        launcher.new_set("Night battle", [ids["Tanks"], ids["Blitz at Dusk"]])
        set_id = "night-battle"
        self.assertEqual(launcher.set_check(set_id)["hard"], [])
        j = self.wait_launcher(launcher, launcher.play(set_id)["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.home / "launcher-copies" / "Modded game"
        self.assertTrue((copy / "Maps" / "PC" / "DataMapBlitzAtDusk_v09.dat").is_file())
        glad = Edat((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        self.assertEqual(Ndf(glad.read(glad.find("everything.cpp.gladndfbin"))).objects[0].get(1).scalar(), 15)
        self.assertEqual(len(self.started), 1)
        self.game_untouched()

    # FINDING F7: with a units mod picked and no map changes picked yet, Duplicate map (and every Maps tab edit) goes
    # into the units mod's folder (StudioApi._mod_dir's fallback for mods made before mods and maps were apart, taken
    # for any units mod, one with no maps too); Export of the map then exports the units mod under its name and
    # replaces its copy in the Launcher's library ("In the Launcher's mod library as Tanks 1.0.0 (the older version
    # replaced)"). duplicate_map's own words: "in the current map project (one is made when none is picked)".
    @unittest.expectedFailure
    def test_f7_a_map_made_after_a_units_mod_gets_map_changes_of_its_own(self):
        tanks = Path(self.api.new_mod("Tanks")["current"])
        self.api.edit(M4, "SeuilMort", 15)
        self.api.duplicate_map(BLITZ, "Blitz at Dusk")
        self.assertFalse((tanks / "maps").exists())
        self.assertNotEqual(self.map_dir(), tanks)

    def test_a_units_mod_and_map_changes_given_one_name(self):
        """The same name for the units mod and the map changes: the second gets a folder of its own (their ids would
        clash in one set)."""
        mod = Path(self.api.new_mod("Normandy")["current"])
        maps = Path(self.api.new_mod("Normandy", "map")["current"])
        self.assertNotEqual(mod.name, maps.name)
        self.api.duplicate_map(BLITZ, "Normandy Dusk")
        self.assertBuilds()

    def test_two_map_mods_making_a_map_of_one_name(self):
        """Two players' map mods, each a new map called Blitz at Dusk (the same folder name), in one set: the
        Launcher says they clash, and Play stops with words."""
        for project in ("Mine", "Friend"):
            self.api.new_mod(project, "map")
            self.api.duplicate_map(BLITZ, "Blitz at Dusk")
            self.export("map")
        launcher = self.launcher()
        ids = {m["name"]: m["id"] for m in launcher.library()}
        launcher.new_set("Both", [ids["Mine"], ids["Friend"]])
        j = self.wait_launcher(launcher, launcher.play("both")["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("mine and friend both make a new map called BlitzAtDusk", " ".join(j["errors"]))

    # FINDING F8: the Launcher's mod set check (shown while a set is edited and before Play) says nothing of two map
    # mods making a new map of one folder name; Play then stops: "mine and friend both make a new map called
    # BlitzAtDusk ... give one another folder name, or leave one mod out" (a player can't rename a downloaded mod's map).
    @unittest.expectedFailure
    def test_f8_the_set_check_names_two_maps_of_one_name(self):
        for project in ("Mine", "Friend"):
            self.api.new_mod(project, "map")
            self.api.duplicate_map(BLITZ, "Blitz at Dusk")
            self.export("map")
        launcher = self.launcher()
        ids = {m["name"]: m["id"] for m in launcher.library()}
        launcher.new_set("Both", [ids["Mine"], ids["Friend"]])
        self.assertTrue(launcher.set_check("both")["hard"])


class Reopened(MapGame):
    """The Studio closed and started again on the same home: the map changes open as they were left."""

    def test_the_map_opened_again(self):
        pack = self.api.duplicate_map(BLITZ, "Blitz at Dusk")["pack"]
        self.api.scenery_add(pack, [{"type": OAK, "x": 1500, "y": 1500}])
        self.api.terrain_add(pack, [{"brush": "hill", "x": 1500.0, "y": 1500.0, "radius": 600.0, "height": 40.0}])
        self.api.road_add(pack, [[500, 2000], [500, 2900]])
        self.assertBuilds()
        before = {"scenery": self.api.scenery(pack), "terrain": self.api.terrain(pack), "roads": self.api.roads(pack),
                  "maps": self.api.maps(), "current": self.api.mods("map")["current"]}
        self.api = self.studio()   # the Studio started again
        after = {"scenery": self.api.scenery(pack), "terrain": self.api.terrain(pack), "roads": self.api.roads(pack),
                 "maps": self.api.maps(), "current": self.api.mods("map")["current"]}
        self.assertEqual(after, before)
        got = self.assertBuilds()
        from ruse_studio.api import _words
        self.assertEqual(got["lines"][0], _words()["play_unchanged"]["us"])  # nothing changed: started as it is


class Deleting(MapGame):
    """Delete map and Delete a mod... (to the Recycle Bin: here a stand-in that removes the folder, as
    test_studio_duplicate's DeleteMap has it)."""

    def setUp(self):
        super().setUp()
        self.binned = []

        def to_bin(path):
            self.binned.append(Path(path))
            shutil.rmtree(path)
        patch = mock.patch("rusemod.recycle.to_recycle_bin", side_effect=to_bin)
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_map_open_deleted_and_the_rest_still_builds(self):
        keep = self.api.duplicate_map(BLITZ, "Blitz Kept")["pack"]
        gone = self.api.duplicate_map(BLITZ, "Blitz Gone")["pack"]
        third = self.api.duplicate_map(gone, "Copy Of Gone")["pack"]   # a copy of the one about to go
        self.assertBuilds()
        res = self.api.delete_map(gone)
        self.assertEqual((res["deleted"], res["copy_of"]), (gone, BLITZ))
        self.assertEqual(sorted(m["pack"] for m in res["maps"]), sorted([BLITZ, keep, third]))
        self.assertBuilds()   # the copy of it keeps working: it copies the shipped map
        names = {self.copy_texts("us").text(name_to_key(f"M_D_{n}")) for n in (31, 32)}
        self.assertEqual(names, {"Blitz Kept", "Copy Of Gone"})

    def test_the_last_new_map_deleted(self):
        pack = self.api.duplicate_map(BLITZ, "Only One")["pack"]
        self.assertBuilds()
        self.api.delete_map(pack)
        self.assertEqual(self.listed(), [BLITZ])
        self.assertIsNotNone(self.map_dir())   # the map changes stay, empty

    # FINDING F6: Test in game on map changes that hold nothing (made, nothing done yet; or their last map deleted),
    # with Settings' game title the game's own (with R.U.S.E. 2.0's title the copy always changes something; this
    # made-up game has no title to change, so it shows either way): the old copy is set aside, the build says "The
    # mods change nothing in these packs.", no new copy is made, and the page is told "The modded copy at <folder> has
    # no <the game's program file>."
    @unittest.expectedFailure
    def test_f6_new_map_changes_tested_before_anything_is_made(self):
        self.api.set_game_title(False)
        self.api.new_mod("Nothing Yet", "map")
        got = self.build()
        self.assertNotIn("The modded copy at", got["message"])

    @unittest.expectedFailure
    def test_f6_the_last_map_deleted_then_tested(self):
        self.api.set_game_title(False)
        pack = self.api.duplicate_map(BLITZ, "Only One")["pack"]
        self.assertBuilds()
        self.api.delete_map(pack)
        got = self.build()
        self.assertNotIn("The modded copy at", got["message"])

    def test_empty_map_changes_tested_after_the_launcher_played_a_set(self):
        """F6 after the Launcher played a set (the modded copy is the PC's one, the Launcher's too) with a downloaded
        units mod: the Studio, with only new map changes that hold nothing yet, presses Test in game; the Launcher's
        copy is left set aside as "Modded game.old" and nothing starts."""
        from test_build import write_mod
        downloaded = write_mod(self.home / "elsewhere", "tougher",
                               {"t.rndf": "patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( SeuilMort = 15 )"})
        (self.home / "sets").mkdir(parents=True, exist_ok=True)
        (self.home / "sets" / "tougher.toml").write_text(f'name = "Tougher"\nmods = ["{downloaded.as_posix()}"]\n',
                                                         encoding="utf-8")
        launcher = LauncherApi(game_dir=self.game, home=self.home, instances=self.home / "copies",
                               open_url=lambda url: None, start_game=self.started.append, steam_running=lambda: True,
                               wait=lambda s: None, find=lambda: None)
        j = self.wait_any(launcher, launcher.play("tougher")["job"])
        self.assertEqual(j["state"], "done", j)
        self.assertTrue((self.copy() / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").is_file())
        self.api.new_mod("Nothing Yet", "map")
        self.assertIsNone(self.api.mods()["current"])   # no units mod in the Studio
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn("The modded copy at", got["message"])
        self.assertIn("the old copy at", " ".join(got["lines"]))
        self.assertEqual(sorted(p.name for p in (self.home / "copies").iterdir()), ["Modded game.old"])
        self.assertEqual(len(self.started), 1)   # the Launcher's start only

    def wait_any(self, api, job_id):
        import time
        end = time.time() + 120
        while api.job(job_id)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        return api.job(job_id)

    def test_the_map_changes_deleted_with_the_launchers_copy(self):
        self.api.duplicate_map(BLITZ, "Blitz at Dusk")
        project = self.map_dir()
        got = self.wait(self.api.export_mod("1.0.0", kind="map")["job"])
        self.assertEqual(got["state"], "done", got)
        ours = self.api.your_mods()["maps"]
        self.assertEqual([(m["ours"], bool(m["launcher"]), m["editing"]) for m in ours], [(True, True, "map")])
        res = self.api.delete_mod(str(project), launcher=True)
        self.assertTrue(res["launcher"])
        self.assertEqual(res["map"]["current"], None)
        self.assertFalse(project.exists())
        self.assertEqual(self.listed(), [BLITZ])
        self.assertIn("Pick or make a mod or a map first", page_said(self.api, "test_in_game"))


if __name__ == "__main__":
    unittest.main()
