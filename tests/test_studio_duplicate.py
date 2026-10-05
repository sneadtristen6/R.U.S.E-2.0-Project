"""The Maps view's Duplicate map (StudioApi.duplicate_map; MOD_FORMAT §8 "A new map"): a new map, a copy of the map
open, written as maps/<name>/map.toml in the map project. The view shows the copy as the map it copies with the copy's
own edits; its player count and the changes made to the map so far come along. Proven in the game: 101 new maps
listed at once, each playing its own ground (TESTS.md T15b, T16)."""
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import newmap
from ruse_studio.api import StudioApi, StudioError, _copied, _pack_name

ANZIO = "Challenge - 1v1 39 Blitz_2 (Anzio)"
ENTRIES = [{"name": "(2) Blitz", "kind": "battles", "titles": {"us": "Blitz"}},
           {"name": ANZIO, "kind": "operation", "titles": {"us": "Anzio"}}]
OPTIONS = {"source": "SuperCrossRoads4", "entries": ENTRIES, "name": "Blitz 2", "folder": None, "why": None}
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

    def test_an_operations_scenario(self):
        spec = newmap.NewMap("SuperCrossRoads4", {"us": "Anzio Twin"}, "Challenge - 1v1 39 Blitz_2 (Anzio)")
        got = _copied(self.VIEW, ("AnzioTwin", spec))["scenarios"]
        self.assertEqual([(s["file"], s["kind"]) for s in got], [("scenario_challenge_2.scenario", "operation")])
        self.assertEqual(got[0]["entries"][0]["name"], "Anzio Twin")


class WithAMapProject(unittest.TestCase):
    """A Studio whose game has Blitz, its menus' entries made up (OPTIONS)."""

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


class Duplicate(WithAMapProject):
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
        with self.assertRaisesRegex(StudioError, "has no entry"):
            self.api.duplicate_map("SuperCrossRoads4", "Blitz 2", entry="(4) Nope")

    def test_several_entries_need_one_picked(self):
        two = [{"name": n, "kind": "battles", "titles": {}} for n in ("(6) Centre de gravite", "(4) Centre de gravite (2v2)")]
        with mock.patch.object(StudioApi, "duplicate_options", return_value=dict(OPTIONS, entries=two)):
            with self.assertRaisesRegex(StudioError, "Pick what to copy"):
                self.api.duplicate_map("TwoIslands", "Gravity")
            pack = self.api.duplicate_map("TwoIslands", "Gravity", entry="(4) Centre de gravite (2v2)")["pack"]
        data = tomllib.loads((self.api._map_dir() / "maps" / pack / "map.toml").read_text(encoding="utf-8"))
        self.assertEqual(data["entry"], "(4) Centre de gravite (2v2)")

    def test_an_operation(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Anzio Twin", entry=ANZIO)["pack"]
        data = tomllib.loads((self.api._map_dir() / "maps" / pack / "map.toml").read_text(encoding="utf-8"))
        self.assertEqual((data["copy_of"], data["entry"], data["name"]), ("SuperCrossRoads4", ANZIO, "Anzio Twin"))
        with mock.patch.object(StudioApi, "_menu_entries", return_value=ENTRIES):
            listed = {m["pack"]: m["kinds"] for m in self.api.maps()["maps"]}
        self.assertEqual(listed["AnzioTwin"], ["operation"])  # the Maps list's Operations filter shows it

    def test_the_one_battles_map_needs_no_entry(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk", entry="(2) Blitz")["pack"]
        data = tomllib.loads((self.api._map_dir() / "maps" / pack / "map.toml").read_text(encoding="utf-8"))
        self.assertNotIn("entry", data)

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


class DeleteMap(Duplicate):
    """Delete map (StudioApi.delete_map): a new map's folder goes to the Recycle Bin (here: a stand-in that removes it
    and says what it was given), never one of the game's maps."""

    def setUp(self):
        super().setUp()
        self.binned = []

        def to_bin(path):
            self.binned.append(Path(path))
            shutil.rmtree(path)
        patch = mock.patch("rusemod.recycle.to_recycle_bin", side_effect=to_bin)
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_new_map_goes_to_the_bin(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        folder = self.api._map_dir() / "maps" / pack
        (folder / "scenery.toml").write_text("# placed\n", encoding="utf-8")
        res = self.api.delete_map(pack.lower())  # (the list's name, any case)
        self.assertEqual((res["deleted"], res["copy_of"]), (pack, "SuperCrossRoads4"))
        self.assertEqual(self.binned, [folder])
        self.assertFalse(folder.exists())
        self.assertEqual([m["pack"] for m in res["maps"]], ["SuperCrossRoads4"])

    def test_the_others_stay(self):
        keep = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        gone = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Night")["pack"]
        shipped = self.api._map_dir() / "maps" / "SuperCrossRoads4"
        shipped.mkdir()
        (shipped / "terrain.toml").write_text("# a change to the game's map\n", encoding="utf-8")
        res = self.api.delete_map(gone)
        self.assertEqual([m["pack"] for m in res["maps"]], ["SuperCrossRoads4", keep])
        self.assertTrue((self.api._map_dir() / "maps" / keep / "map.toml").is_file())
        self.assertTrue((shipped / "terrain.toml").is_file())

    def test_the_games_own_maps_cant_be(self):
        self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")
        for pack in ("SuperCrossRoads4", "Nope", "", None):
            with self.assertRaisesRegex(StudioError, "game's own maps stay"):
                self.api.delete_map(pack)
        self.assertEqual(self.binned, [])

    def test_when_windows_refuses(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        with mock.patch("rusemod.recycle.to_recycle_bin", side_effect=OSError("close anything that has it open")):
            with self.assertRaisesRegex(StudioError, "close anything"):
                self.api.delete_map(pack)
        self.assertTrue((self.api._map_dir() / "maps" / pack / "map.toml").is_file())


class BlankStart(WithAMapProject):
    """Duplicate map's Start from: Blank Terrain or Blank Ocean (rusemod.presets), the owner's presets (2026-10-05:
    "a preset, like want to start a Navy map", "Blank Terrain, Blank Ocean"): the new map's files are the preset's,
    made from the shipped map's own, instead of the changes made to the map so far."""

    def facts(self):
        from rusemod import presets
        return presets.Facts((0.0, 0.0, 400000.0, 200000.0), 12623.0, 19233.0, "leveldesign_normal.scenario",
                             [(0, "LabelVille"), (1, "StartingPoint"), (2, "Spawn")], ["Odd_Type"])

    def test_the_presets_files_instead_of_the_changes_so_far(self):
        from rusemod import presets
        self.api.new_mod("My maps", "map")
        maps = self.api._map_dir() / "maps" / "SuperCrossRoads4"
        maps.mkdir(parents=True)
        (maps / "terrain.toml").write_text('[[stroke]]\nbrush = "hill"\nx = 1.0\ny = 2.0\nradius = 3.0\nheight = 4.0\n',
                                           encoding="utf-8")
        for kind in presets.KINDS:
            with mock.patch.object(presets, "copy_scenario", return_value=self.facts().scenario) as scen, \
                    mock.patch.object(presets, "read_facts", return_value=self.facts()) as read:
                pack = self.api.duplicate_map("SuperCrossRoads4", f"Blitz {presets.NAMES[kind]}", preset=kind)["pack"]
            self.assertEqual((scen.call_args.args[1:], read.call_args.args[1:]),
                             (("SuperCrossRoads4", None), ("SuperCrossRoads4", "leveldesign_normal.scenario")))
            folder = self.api._map_dir() / "maps" / pack
            for name, text in presets.preset_files(kind, self.facts()).items():
                self.assertEqual(tomllib.loads((folder / name).read_text(encoding="utf-8")), tomllib.loads(text))
            self.assertEqual(tomllib.loads((folder / "map.toml").read_text(encoding="utf-8"))["copy_of"],
                             "SuperCrossRoads4")
            self.assertEqual(sorted(f.name for f in folder.iterdir()),
                             sorted(list(presets.preset_files(kind, self.facts())) + ["map.toml"]))  # no hill

    def test_only_from_a_battles_map(self):
        with self.assertRaisesRegex(StudioError, "Battles map"):
            self.api.duplicate_map("SuperCrossRoads4", "Anzio Blank", entry=ANZIO, preset="blank_terrain")
        with self.assertRaisesRegex(StudioError, "no 'blank_moon'"):
            self.api.duplicate_map("SuperCrossRoads4", "Moon", preset="blank_moon")


class RecycleBin(unittest.TestCase):
    def test_nothing_there(self):
        from rusemod.recycle import to_recycle_bin
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                to_recycle_bin(Path(tmp, "gone"))


if __name__ == "__main__":
    unittest.main()
