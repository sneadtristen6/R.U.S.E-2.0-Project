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


class DownloadedMap(MapGame):
    """A map mod made by another player (another Studio, its own home), exported, added to this player's Launcher, and
    opened in this player's Studio with Edit an installed mod: a copy under a name of its own, its map changed and
    built."""

    def test_a_downloaded_map_mod_edited(self):
        from rusemod.play import Starter
        from ruse_studio.api import StudioApi
        other = self.home.parent / (self.home.name + "-author")
        author = StudioApi(index_path=self.index, game_dir=self.game, home=other, instances=other / "copies",
                           starter=Starter(open_url=lambda url: None, start_game=lambda exe: None,
                                           steam_running=lambda: True, wait=lambda s: None))
        author.new_mod("Dusk Maps", "map")
        author.duplicate_map(BLITZ, "Blitz at Dusk")
        author.scenery_add("BlitzAtDusk", [{"type": OAK, "x": 1200, "y": 1200}])
        job = author.export_mod("1.0.0", "Author", kind="map")["job"]
        import time
        end = time.time() + 120
        while author.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        self.assertEqual(author.job(job)["state"], "done", author.job(job))
        file = next((other / "exports").glob("*.rusemod"))
        launcher = LauncherApi(game_dir=self.game, home=self.home, instances=self.home / "copies",
                               open_url=lambda url: None, start_game=self.started.append, steam_running=lambda: True,
                               wait=lambda s: None, find=lambda: None)
        launcher.add_mod(str(file))
        installed = self.api.installed_mods()["mods"]
        self.assertEqual([(m["name"], m["maps"], m["units"], m["yours"]) for m in installed],
                         [("Dusk Maps", True, False, "")])
        opened = self.api.edit_installed(installed[0]["id"], "My Dusk")
        self.assertEqual((opened["copied"], opened["maps"], opened["units"]), (True, True, False))
        self.assertEqual(opened["message"], "Your copy My Dusk is open: everything in Dusk Maps is in it, and your "
                                            "changes go into it.")
        self.assertIsNone(opened["mod"]["current"])   # a map mod: the Units tab's mod stays as it was
        self.assertIn("BlitzAtDusk", self.listed())
        self.api.scenery_add("BlitzAtDusk", [{"type": OAK, "x": 1800, "y": 1800}])
        self.assertEqual(len(self.api.scenery("BlitzAtDusk")["objects"]), 2)
        self.assertBuilds()

    # FINDING F1, on Edit an installed mod: the copy's folder is made from the name typed for it, so a copy called
    # "Nul" stops with "<home>\maps\nul couldn't be read or written (error 183). Please report this."
    @unittest.expectedFailure
    def test_f1_a_downloaded_map_mod_copied_under_the_name_nul(self):
        from test_build import write_mod
        mod = write_mod(self.home / "elsewhere", "their-maps", {})
        (mod / "maps" / "BlitzAtDusk").mkdir(parents=True)
        (mod / "maps" / "BlitzAtDusk" / "map.toml").write_text('copy_of = "SuperCrossRoads4"\nname = "Blitz at Dusk"\n',
                                                              encoding="utf-8")
        from rusemod.library import Library
        Library(self.home / "library").add(mod)
        self.assertEqual(page_said(self.api, "edit_installed", "their-maps", "Nul"), "")
        self.assertIn("BlitzAtDusk", self.listed())
        self.assertBuilds()


class HandEdits(MapGame):
    """Map changes a player (or another tool) changed by hand between two Studio sessions, and a very long name."""

    def test_a_maps_file_broken_by_hand(self):
        """map.toml with a quote left open: the map leaves the Maps list, the mod check at the top names the file (and
        can set it aside), and Test in game stops on it, naming it."""
        pack = self.api.duplicate_map(BLITZ, "Blitz at Dusk")["pack"]
        (self.map_folder(pack) / "map.toml").write_text('copy_of = "SuperCrossRoads4"\nname = "Blitz at Dusk\n',
                                                        encoding="utf-8")   # a quote left open
        self.api = self.studio()
        self.assertEqual(self.listed(), [BLITZ])
        problems = {p["file"]: p for p in self.api.check_mod()["problems"]}
        self.assertTrue(problems["maps/BlitzAtDusk/map.toml"]["set_aside"])
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn("maps/BlitzAtDusk/map.toml: Illegal character", got["message"])

    def test_the_map_changes_own_file_broken_by_hand(self):
        """mod.toml with a quote left open."""
        self.api.duplicate_map(BLITZ, "Blitz at Dusk")
        (self.map_dir() / "mod.toml").write_text('[mod]\nid = "blitz-at-dusk\n', encoding="utf-8")
        self.api = self.studio()
        for call, args in (("mods", ("map",)), ("maps", ()), ("check_mod", ())):
            self.assertEqual(page_said(self.api, call, *args), "", call)
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn("mod.toml: Illegal character '\\n' (at line 2, column 20)", got["message"])   # the file, its line

    def test_the_longest_names_the_page_takes(self):
        """The page's name boxes take 60 characters (new map changes, Duplicate map): both at their longest, and a
        ground picture of a long name, the deepest files a map project holds (Windows' 260-character paths: this PC
        has long paths off, as Windows does by default)."""
        self.api.new_mod("A" * 60, "map")
        pack = self.api.duplicate_map(BLITZ, "B" * 60)["pack"]
        import base64
        from rusemod.dxt import png_bytes
        png = png_bytes(bytes((120, 90, 40, 255)) * 16, 4, 4, channels=4)
        self.api.add_ground_picture("C" * 60, "data:image/png;base64," + base64.b64encode(png).decode())
        self.api.scenery_add(pack, [{"type": OAK, "x": 1500, "y": 1500}])
        deepest = max(len(str(p)) for p in self.map_dir().rglob("*"))
        self.assertLess(deepest, 260)   # (201 here, in a temporary folder; Documents\RUSE 2.0\Maps is a little longer)
        self.assertBuilds()


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

    # (Test in game on map changes holding nothing, made or emptied, isn't a scenario this made-up game can show: it
    # has no IA_Common.dat, so its build changes nothing and makes no copy ("The modded copy at <folder> has no <the
    # game's program file>."); on a real install RUSE Guard's watcher (rusemod.fairplay, ON and IN_BUILDS) always
    # goes into IA_Common.dat, so the copy is always made. Taken out of the findings, 2026-11-14.)

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
