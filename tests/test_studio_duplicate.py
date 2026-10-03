"""The Maps view's Duplicate map (StudioApi.duplicate_map; MOD_FORMAT §8 "A new map"): a new map, a copy of the map
open, written as maps/<name>/map.toml in the map project. The view shows the copy as the map it copies with the copy's
own edits; its player count and the changes made to the map so far come along. Proven in the game: 101 new maps
listed at once, each playing its own ground (TESTS.md T15b, T16)."""
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import newmap
from ruse_studio.api import StudioApi, StudioError, _copied, _pack_name

OPTIONS = {"source": "SuperCrossRoads4", "entries": ["(2) Blitz"], "name": "Blitz 2", "folder": None, "why": None}
SHIPPED = [{"pack": "SuperCrossRoads4", "names": ["(2) Blitz"], "titles": {"us": ["Blitz"]}, "kinds": ["skirmish"],
            "file": "DataMapSuperCrossRoads4_v09.dat", "found": True}]


class PackName(unittest.TestCase):
    def test_from_the_menu_name(self):
        self.assertEqual(_pack_name("Blitz at dusk", set()), "BlitzAtDusk")
        self.assertEqual(_pack_name("Côte d'Opale", set()), "CoteDOpale")  # accents dropped
        self.assertEqual(_pack_name("Блиц 2", set()), "NewMap2")           # nothing Latin left
        self.assertEqual(_pack_name("1944 front", set()), "NewMap1944Front")  # starts with a letter

    def test_a_number_until_free(self):
        self.assertEqual(_pack_name("Blitz at dusk", {"blitzatdusk", "blitzatdusk2"}), "BlitzAtDusk3")

    def test_always_a_name_the_game_takes(self):
        for name in ("Blitz at dusk", "x" * 60, "Блиц", "a b c 1 2 3", "Ünïcødé"):
            newmap.check_name(_pack_name(name, set()))  # raises when the game's files can't carry it


class CopiedScenarios(unittest.TestCase):
    VIEW = {"scenarios": [
        {"file": "leveldesign_normal.scenario", "items": [],
         "entries": [{"name": "(2) Blitz", "kind": "skirmish", "titles": {"us": "Blitz", "fr": "Blitz"}}]},
        {"file": "scenario_challenge_2.scenario", "items": [],
         "entries": [{"name": "Challenge - 1v1 39 Blitz_2 (Anzio)", "kind": "operation", "titles": {}}]}]}

    def test_only_the_battles_scenario_under_the_new_name(self):
        spec = newmap.NewMap("SuperCrossRoads4", {"us": "Blitz at Dusk", "fr": "Blitz au crépuscule"})
        got = _copied(self.VIEW, ("BlitzAtDusk", spec))["scenarios"]
        self.assertEqual([s["file"] for s in got], ["leveldesign_normal.scenario"])
        self.assertEqual(got[0]["entries"], [{"name": "(2) Blitz at Dusk", "kind": "skirmish",
                                              "titles": {"us": "Blitz at Dusk", "fr": "Blitz au crépuscule"}}])
        self.assertEqual(self.VIEW["scenarios"][0]["entries"][0]["name"], "(2) Blitz")  # the cached view stays

    def test_the_map_itself_unchanged(self):
        self.assertIs(_copied(self.VIEW, None), self.VIEW)


class Duplicate(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.api = StudioApi(home=Path(tmp.name, "home"), game_dir=Path(tmp.name, "game"))
        for name, value in (("duplicate_options", lambda pack: dict(OPTIONS, folder=self._folder())),):
            patch = mock.patch.object(StudioApi, name, side_effect=value, autospec=False)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch("ruse_studio.api.map_list", return_value=[dict(m) for m in SHIPPED])
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.object(StudioApi, "_game", return_value=Path(tmp.name, "game"))
        patch.start()
        self.addCleanup(patch.stop)

    def _folder(self):
        d = self.api._map_dir()
        return str(d) if d else None

    def test_a_new_map_project_when_none_is_picked(self):
        res = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")
        self.assertEqual(res["pack"], "BlitzAtDusk")
        folder = self.api._map_dir()
        self.assertIsNotNone(folder)
        data = tomllib.loads((folder / "maps" / "BlitzAtDusk" / "map.toml").read_text(encoding="utf-8"))
        self.assertEqual((data["copy_of"], data["name"]), ("SuperCrossRoads4", "Blitz at Dusk"))
        self.assertEqual(newmap.parse(data, "map.toml", "BlitzAtDusk")[0].copy_of, "SuperCrossRoads4")
        listed = [m["pack"] for m in res["maps"]]
        self.assertEqual(listed, ["SuperCrossRoads4", "BlitzAtDusk"])  # right after the map it copies
        new = res["maps"][1]
        self.assertEqual((new["copy_of"], new["titles"]["us"], new["kinds"]), ("SuperCrossRoads4", ["Blitz at Dusk"],
                                                                                 ["skirmish"]))

    def test_the_view_reads_the_map_it_copies(self):
        self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")
        self.assertEqual(self.api._game_pack("BlitzAtDusk"), "SuperCrossRoads4")
        self.assertEqual(self.api._game_pack("blitzatdusk"), "SuperCrossRoads4")
        self.assertEqual(self.api._game_pack("SuperCrossRoads4"), "SuperCrossRoads4")

    def test_changes_so_far_and_the_player_count_come_along(self):
        self.api.new_mod("My maps", "map")
        maps = self.api._map_dir() / "maps" / "SuperCrossRoads4"
        maps.mkdir(parents=True)
        terrain = '[[stroke]]\nbrush = "hill"\nx = 1.0\ny = 2.0\nradius = 3.0\nheight = 4.0\n'
        (maps / "terrain.toml").write_text(terrain, encoding="utf-8")
        (maps / "map.toml").write_text("players = 4\n", encoding="utf-8")
        (maps / "notes.txt").write_text("not a map file", encoding="utf-8")
        new = self.api._map_dir() / "maps" / self.api.duplicate_map("SuperCrossRoads4", "Big Blitz")["pack"]
        self.assertEqual((new / "terrain.toml").read_text(encoding="utf-8"), terrain)
        self.assertFalse((new / "notes.txt").exists())
        data = tomllib.loads((new / "map.toml").read_text(encoding="utf-8"))
        self.assertEqual((data["copy_of"], data["players"]), ("SuperCrossRoads4", 4))
        self.assertEqual(maps.joinpath("terrain.toml").read_text(encoding="utf-8"), terrain)  # the original keeps it

    def test_a_copy_of_a_copy_copies_the_shipped_map_with_its_edits(self):
        first = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        (self.api._map_dir() / "maps" / first / "scenery.toml").write_text("# placed\n", encoding="utf-8")
        second = self.api.duplicate_map(first, "Blitz at Night")["pack"]
        folder = self.api._map_dir() / "maps" / second
        self.assertEqual(tomllib.loads((folder / "map.toml").read_text(encoding="utf-8"))["copy_of"],
                         "SuperCrossRoads4")
        self.assertTrue((folder / "scenery.toml").is_file())

    def test_refused(self):
        with self.assertRaisesRegex(StudioError, "name"):
            self.api.duplicate_map("SuperCrossRoads4", "   ")
        with self.assertRaisesRegex(StudioError, "60"):
            self.api.duplicate_map("SuperCrossRoads4", "x" * 61)
        with self.assertRaisesRegex(StudioError, "no BATTLES entry"):
            self.api.duplicate_map("SuperCrossRoads4", "Blitz 2", entry="(4) Nope")

    def test_several_entries_need_one_picked(self):
        OPTIONS_TWO = dict(OPTIONS, entries=["(6) Centre de gravite", "(4) Centre de gravite (2v2)"])
        with mock.patch.object(StudioApi, "duplicate_options", return_value=OPTIONS_TWO):
            with self.assertRaisesRegex(StudioError, "pick the one"):
                self.api.duplicate_map("TwoIslands", "Gravity")
            pack = self.api.duplicate_map("TwoIslands", "Gravity", entry="(4) Centre de gravite (2v2)")["pack"]
        data = tomllib.loads((self.api._map_dir() / "maps" / pack / "map.toml").read_text(encoding="utf-8"))
        self.assertEqual(data["entry"], "(4) Centre de gravite (2v2)")

    def test_a_map_battles_doesnt_list(self):
        with mock.patch.object(StudioApi, "duplicate_options", return_value=dict(OPTIONS, entries=[], why="Only maps")):
            with self.assertRaisesRegex(StudioError, "Only maps"):
                self.api.duplicate_map("M02_Tunisie", "Desert")

    def test_players_on_a_copy_keep_what_it_copies(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        path = self.api._map_dir() / "maps" / pack / "map.toml"
        self.assertIsNone(self.api._read_players(pack))  # a new map's file without a count
        with mock.patch.object(StudioApi, "map_players", return_value={}):
            self.api.set_players(pack, 4)
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual((data["copy_of"], data["name"], data["players"]), ("SuperCrossRoads4", "Blitz at Dusk", 4))
            self.api.set_players(pack, None)  # back to the game's count: the file stays, the copy with it
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((data["copy_of"], "players" in data), ("SuperCrossRoads4", False))


if __name__ == "__main__":
    unittest.main()
