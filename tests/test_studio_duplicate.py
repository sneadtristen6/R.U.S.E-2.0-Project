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
            toml = tomllib.loads((folder / "map.toml").read_text(encoding="utf-8"))
            self.assertEqual((toml["copy_of"], toml["picture"], toml["wide_picture"], toml["start_dots"]),
                             ("SuperCrossRoads4", "menu.png", "menu-wide.png", True))  # its own menu pictures,
            for name, data in presets.preset_pictures(kind).items():                 # the build drawing its starts
                self.assertEqual((folder / name).read_bytes(), data)
            self.assertEqual(sorted(f.name for f in folder.iterdir()),
                             sorted(list(presets.preset_files(kind, self.facts())) + ["map.toml", "menu.png",
                                                                                     "menu-wide.png"]))  # no hill

    def test_only_from_a_battles_map(self):
        with self.assertRaisesRegex(StudioError, "Battles map"):
            self.api.duplicate_map("SuperCrossRoads4", "Anzio Blank", entry=ANZIO, preset="blank_terrain")
        with self.assertRaisesRegex(StudioError, "no 'blank_moon'"):
            self.api.duplicate_map("SuperCrossRoads4", "Moon", preset="blank_moon")


class MenuPictures(WithAMapProject):
    """A map's own pictures in the menus (StudioApi.menu_pictures and the calls of its window; map.toml picture,
    wide_picture, start_dots): a PNG picked for either, the game's own back, the start dots, and the pictures made in
    Blender brought back; a new map's and a shipped map's alike (the owner, 2026-10-05: "the option for a custom PNG
    or model and then also being able to make your own")."""

    def setUp(self):
        super().setUp()
        patch = mock.patch.object(StudioApi, "_menu_starts", return_value=[(0.25, 0.5)])
        patch.start()
        self.addCleanup(patch.stop)
        self.api._window = object()

    def shot(self, w=4, h=4, colour=(200, 40, 40, 255)):
        from rusemod.dxt import png_bytes
        path = Path(self.api._map_dir(), f"shot-{w}x{h}.png")
        path.write_bytes(png_bytes(bytes(colour) * (w * h), w, h, channels=4))
        return path

    def pick(self, pack, key, path):
        with mock.patch("ruse_studio.api.pick_file", return_value=str(path)):
            return self.api.pick_menu_picture(pack, key)

    def toml(self, pack):
        return tomllib.loads((self.api._map_dir() / "maps" / pack / "map.toml").read_text(encoding="utf-8"))

    def test_a_new_maps_pictures_picked_and_given_back(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        folder = self.api._map_dir() / "maps" / pack
        (folder / "map.toml").write_text((folder / "map.toml").read_text(encoding="utf-8") + "players = 4\n",
                                         encoding="utf-8")
        got = self.api.menu_pictures(pack)
        self.assertEqual([(p["key"], p["file"], p["own"]) for p in got["pictures"]],
                         [("picture", None, False), ("wide_picture", None, False)])   # the copied map's own
        self.assertTrue(got["new"])
        big = self.shot()
        got = self.pick(pack, "picture", big)
        self.assertEqual((folder / "menu.png").read_bytes(), big.read_bytes())
        self.assertTrue(got["pictures"][0]["own"])
        self.assertTrue(got["pictures"][0]["url"].startswith("data:image/png;base64,"))
        self.pick(pack, "wide_picture", self.shot(34, 10, (20, 20, 220, 255)))
        data = self.toml(pack)
        self.assertEqual((data["picture"], data["wide_picture"], data["players"], data["copy_of"],
                          data.get("start_dots", False)), ("menu.png", "menu-wide.png", 4, "SuperCrossRoads4", False))
        self.assertTrue(self.api.set_start_dots(pack, True)["start_dots"])
        self.assertTrue(self.toml(pack)["start_dots"])
        with mock.patch("rusemod.recycle.to_recycle_bin") as bin_:
            got = self.api.clear_menu_picture(pack, "wide_picture")
        self.assertEqual(bin_.call_args.args[0], folder / "menu-wide.png")
        data = self.toml(pack)
        self.assertNotIn("wide_picture", data)
        self.assertNotIn("start_dots", data)              # no dots without a 3D map of its own
        self.assertEqual(data["picture"], "menu.png")
        with self.assertRaisesRegex(StudioError, "pick one or make it in Blender first"):
            self.api.set_start_dots(pack, True)

    def test_not_a_picture(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        bad = Path(self.api._map_dir(), "shot.png")
        bad.write_bytes(b"not a picture")
        self.assertIn("not a PNG", self.pick(pack, "picture", bad)["message"])
        self.assertNotIn("picture", self.toml(pack))
        with self.assertRaisesRegex(StudioError, "No menu picture called"):
            self.api.pick_menu_picture(pack, "icon")

    def test_a_shipped_maps_own_pictures_beside_its_player_count(self):
        """A themed mod pictures a map of the game's own: its map.toml names the pictures (no copy_of), and the
        player count set there stays with them."""
        self.api.new_mod("Themed", "map")
        self.pick("SuperCrossRoads4", "picture", self.shot())
        self.assertEqual(self.toml("SuperCrossRoads4"), {"picture": "menu.png"})
        with mock.patch.object(StudioApi, "map_players", return_value={}):  # (the made-up game has no map list)
            self.api.set_players("SuperCrossRoads4", 4)
            self.assertEqual(self.toml("SuperCrossRoads4"), {"players": 4, "picture": "menu.png"})
            self.api.set_players("SuperCrossRoads4", None)
        self.assertEqual(self.toml("SuperCrossRoads4"), {"picture": "menu.png"})
        self.assertFalse(self.api.menu_pictures("SuperCrossRoads4")["new"])
        with mock.patch("rusemod.recycle.to_recycle_bin"):
            self.api.clear_menu_picture("SuperCrossRoads4", "picture")
        self.assertFalse((self.api._map_dir() / "maps" / "SuperCrossRoads4" / "map.toml").exists())

    def test_made_in_blender_and_brought_back(self):
        """Save menu pictures in Blender leaves picture.png, wide.png and saved.json in the map's scene folder;
        Bring back cuts the big one to 640 x 360 with the game's frame, keeps the 3D map as rendered, and turns the
        start dots on (the scene's camera puts the map where the build draws them)."""
        from rusemod.png import read_png
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        self.assertIn("Nothing saved in Blender yet", self.api.menu_pictures_bring_back(pack)["message"])
        work = self.api._menu_work(pack)
        work.mkdir(parents=True)
        shutil.copyfile(self.shot(128, 72), work / "picture.png")
        shutil.copyfile(self.shot(136, 40, (20, 60, 80, 255)), work / "wide.png")
        (work / "saved.json").write_text('{"saved": [], "time": 0}', encoding="utf-8")
        got = self.api.menu_pictures_bring_back(pack)
        self.assertIn("Brought back both pictures", got["message"])
        folder = self.api._map_dir() / "maps" / pack
        w, h, px = read_png((folder / "menu.png").read_bytes())
        self.assertEqual(((w, h), tuple(px[:3])), ((640, 360), (132, 134, 132)))      # framed as the game's own
        self.assertEqual((folder / "menu-wide.png").read_bytes(), (work / "wide.png").read_bytes())
        data = self.toml(pack)
        self.assertEqual((data["picture"], data["wide_picture"], data["start_dots"]), ("menu.png", "menu-wide.png", True))

    def test_a_blank_maps_scene_is_its_sea_or_its_grass(self):
        from rusemod import presets
        facts = presets.Facts((0.0, 0.0, 400000.0, 200000.0), 12623.0, 19233.0, "leveldesign_normal.scenario",
                              [(0, "StartingPoint")], [])
        for kind, want in (("blank_ocean", ("ocean", 12623.0)), ("blank_terrain", ("land", 19233.0))):
            with mock.patch.object(presets, "copy_scenario", return_value=facts.scenario), \
                    mock.patch.object(presets, "read_facts", return_value=facts):
                pack = self.api.duplicate_map("SuperCrossRoads4", presets.NAMES[kind], preset=kind)["pack"]
            self.assertEqual(self.api._menu_scene_kind(pack), want)
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        self.assertEqual(self.api._menu_scene_kind(pack), ("map", None))

    def test_blender_needed(self):
        pack = self.api.duplicate_map("SuperCrossRoads4", "Blitz at Dusk")["pack"]
        with mock.patch.object(StudioApi, "_blender", return_value=None), \
                self.assertRaisesRegex(StudioError, "Blender isn't found"):
            self.api.menu_pictures_blender(pack)


class RecycleBin(unittest.TestCase):
    def test_nothing_there(self):
        from rusemod.recycle import to_recycle_bin
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                to_recycle_bin(Path(tmp, "gone"))


if __name__ == "__main__":
    unittest.main()
