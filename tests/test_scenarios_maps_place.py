"""Scenarios: what a player places on a map in the Studio's Maps tab (buildings, trees, roads, bridges, cover and
movement, ground paint), the usual way and the unusual ones (at the map's edges and past them, on water, stacked, at
the size limits, many at once), on the made-up game of test_scenarios_maps_base. Each checks what the page is told,
the map's files, and whether the map still builds (Test in game).

The made-up map: ground 3000 x 3000 map units (its scenery grid reaches 81,920), a town hall at (1000, 2000), oaks
at (5000, 0), (5100, 0), (5000, 9000), (5100, 9000), one road along y 2000 from x 0 to 12,000.

FOR: the overnight scenario tests of map mods (owner, 2026-11-13). USED-BY: the release check of 0.9.8.20."""
import tomllib
import unittest
from collections import Counter

from test_scenarios_maps_base import BLITZ, HALL, OAK, MapGame, page_said
from test_scenery import spots, village
from rusemod import scenery
from rusemod.edat import Edat

SCEN = "leveldesign_normal.scenario"
H, O = HALL, OAK
HS = HALL + "_R2Seen"   # a building the mod places: the build's copy of its type drawn at every distance (visibility)


def by_name(raw: bytes) -> Counter:
    names = scenery.Scenery(raw).names
    return Counter({(names[sym], x, y): n for (sym, x, y), n in spots(raw).items()})


class Placing(MapGame):
    def setUp(self):
        super().setUp()
        self.pack = self.api.duplicate_map(BLITZ, "Placed")["pack"]

    def built_spots(self, pack=None) -> Counter:
        """(type name, x, y) of every object on the built map (test_scenery.spots, by the type's name: the build gives
        what it places a name entry of its own)."""
        arc = Edat(self.copy().joinpath("Maps", "PC", f"DataMap{pack or self.pack}_v09.dat").read_bytes())
        return by_name(bytes(arc.read(arc.find(scenery.MEMBER))))

    def added(self, pack=None) -> Counter:
        return self.built_spots(pack) - by_name(village())

    def test_a_building_and_trees_placed_undone_and_placed_again(self):
        self.api.scenery_add(self.pack, [{"type": HALL, "x": 1500, "y": 1500, "turn": 90, "size": 1.0}])
        self.api.scenery_add(self.pack, [{"type": OAK, "x": 500 + 50 * i, "y": 2500} for i in range(5)])
        self.assertEqual(self.api.scenery_undo(self.pack, 1)["count"], 5)  # Undo takes the last object
        self.api.scenery_add(self.pack, [{"type": OAK, "x": 2800, "y": 200}])
        self.assertBuilds()
        self.assertEqual(self.added(), Counter({(HS, 1500.0, 1500.0): 1, (O, 2800.0, 200.0): 1,
                                                **{(O, 500.0 + 50 * i, 2500.0): 1 for i in range(4)}}))
        self.game_untouched()

    def test_at_the_maps_corners(self):
        corners = [(0, 0), (2999, 0), (0, 2999), (2999, 2999)]
        self.api.scenery_add(self.pack, [{"type": OAK, "x": x, "y": y} for x, y in corners])
        self.assertBuilds()
        self.assertEqual(self.added(), Counter({(O, float(x), float(y)): 1 for x, y in corners}))

    def test_past_the_maps_edge_the_build_says_where(self):
        """The page keeps what it places on the ground (its clicks hit the ground; scatter, grid and box stop at the
        map's bounds), so this comes from elsewhere (a file edited by hand): the build names the place and stops."""
        self.api.scenery_add(self.pack, [{"type": OAK, "x": -100, "y": 500}])
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn("(-100, 500) is outside the map's scenery grid", " ".join(got.get("errors", [])))

    def test_stacked_on_one_spot(self):
        """A player clicking the same spot again and again: every object kept, all on that spot, and it builds."""
        for _ in range(60):
            self.api.scenery_add(self.pack, [{"type": OAK, "x": 1500, "y": 1500}])
        self.api.scenery_add(self.pack, [{"type": HALL, "x": 1500, "y": 1500}] * 20)
        self.assertEqual(len(self.api.scenery(self.pack)["objects"]), 80)
        self.assertBuilds()
        self.assertEqual(self.added(), Counter({(O, 1500.0, 1500.0): 60, (HS, 1500.0, 1500.0): 20}))

    def test_the_sizes_and_turns_the_page_offers(self):
        rows = [{"type": OAK, "x": 100 + 100 * i, "y": 100, "size": size, "turn": turn}
                for i, (size, turn) in enumerate(((0.05, 0), (50, 0), (1, 720), (1, -90), (10, 359.9)))]
        self.api.scenery_add(self.pack, rows)
        for bad in ({"size": 0.04}, {"size": 50.5}, {"x": float("nan")}):
            self.assertIn("out of range", page_said(self.api, "scenery_add", self.pack, [{**rows[0], **bad}]))
        self.assertEqual(len(self.api.scenery(self.pack)["objects"]), 5)  # a refusal adds nothing
        self.assertBuilds()

    def test_many_objects_in_many_strokes(self):
        """A big wood painted stroke after stroke (the page places at most 800 a stroke)."""
        for stroke in range(12):
            self.api.scenery_add(self.pack, [{"type": OAK, "x": 10 + (i % 40) * 70, "y": 10 + stroke * 240 + (i // 40) * 12,
                                              "turn": i % 360} for i in range(800)])
        self.assertEqual(len(self.api.scenery(self.pack)["objects"]), 9600)
        self.assertBuilds()
        self.assertEqual(sum(self.added().values()), 9600)

    def test_the_maps_own_objects_moved_and_taken_away(self):
        self.api.scenery_own(self.pack, [
            {"type": HALL, "x": 1000, "y": 2000, "to_x": 2900, "to_y": 2900, "turn": 45},
            {"type": OAK, "x": 5000, "y": 0, "gone": True}])
        self.assertBuilds()
        got = self.built_spots()
        self.assertEqual(got[(HS, 2900.0, 2900.0)], 1)
        self.assertEqual((got[(H, 1000.0, 2000.0)], got[(O, 5000.0, 0.0)]), (0, 0))

    WHOLE = {"x": 1500, "y": 1500, "radius": 2500, "shape": "square", "dx": 1, "dy": 0}  # as its button makes it

    def test_erase_the_whole_maps_trees_then_place_again(self):
        """Erase the whole map as its button does it (one square over the map, half its side and 1000 more), trees and
        props ticked; then a tree and a building placed. (The village's oaks stand past the ground's 3000, at x 5000
        and more: the square reaches 4000 from the middle, so they stay.)"""
        self.api.scenery_erase(self.pack, [{**self.WHOLE, "what": ["vegetation", "prop"]}])
        self.api.scenery_add(self.pack, [{"type": OAK, "x": 1200, "y": 1200}, {"type": HALL, "x": 1800, "y": 600}])
        self.assertBuilds()
        self.assertEqual(self.added(), Counter({(O, 1200.0, 1200.0): 1, (HS, 1800.0, 600.0): 1}))

    def test_erase_the_whole_map_buildings_too_then_place(self):
        """Every kind ticked: on this made-up map the town hall was the one object new ones hang on, so the build
        says it can't place them (in words, nothing written). Whether a real map keeps one: the real install's check."""
        self.api.scenery_erase(self.pack, [{**self.WHOLE, "what": ["vegetation", "prop", "building"]}])
        self.api.scenery_add(self.pack, [{"type": OAK, "x": 1200, "y": 1200}])
        self.assertEqual(self.api.scenery_erased(self.pack)["takes"], {"building": 1})
        got = self.build()
        if got["state"] != "done":   # (on this map: "the map has no object to hang new ones on"; real maps keep one)
            self.assertTrue(got["errors"], got)
            self.assertNotIn("Something went wrong", got["message"])


class WaterOnBlankTerrain(MapGame):
    """A river or a lake painted on a Blank Terrain map, as a player starting from scratch does."""

    # FINDING F11: Blank Terrain's start erases every building of the copied map, and the build opens the ground under
    # the erased buildings to every unit ("of the map's buildings erased: the ground ... is opened"; on the made-up map
    # 9 circles, on a real one thousands). Water the player paints there afterwards lies in those opens: the build
    # warns once an open, "the open at (312, 1500) takes in water ...: units there stand on the ground under it, on
    # the riverbed or the lake's floor. Leave the open off the water unless that is what you want", about opens the
    # player never made (110 warnings on a real Blank Terrain of Blitz with one river), and by its own words units
    # walk on the riverbed there.
    @unittest.expectedFailure
    def test_f11_a_river_on_blank_terrain_isnt_opened_to_units(self):
        pack = self.api.duplicate_map(BLITZ, "Blank River", preset="blank_terrain")["pack"]
        self.api.scenario_move(pack, SCEN, 0, 1200.0, 1200.0)
        self.api.scenario_add_start(pack, SCEN, 1, 2400.0, 2400.0)
        level = self.toml(pack, "terrain.toml")["stroke"][0]["level"]
        self.api.terrain_add(pack, [{"brush": "lower", "x": 0, "y": 1500, "x2": 3000, "y2": 1500, "shape": "line",
                                     "radius": 300, "height": 400},
                                    {"brush": "water", "x": 0, "y": 1500, "x2": 3000, "y2": 1500, "shape": "line",
                                     "radius": 250, "level": level - 100}])
        got = self.assertBuilds()
        self.assertEqual([ln for ln in got["lines"] if "takes in water" in ln], [])



class OnBlankMaps(MapGame):
    """A blank map's whole scenery erased: what a player places there afterwards."""

    def blank(self, preset):
        pack = self.api.duplicate_map(BLITZ, preset.replace("_", " "), preset=preset)["pack"]
        self.api.scenario_move(pack, SCEN, 0, 1200.0, 1200.0)
        self.api.scenario_add_start(pack, SCEN, 1, 2400.0, 2400.0)
        return pack

    def test_a_building_and_trees_on_blank_maps(self):
        """On this made-up map the blank start's erase takes the one object new ones hang on (the town hall), so the
        build says it can't place them, in words. Whether a real map's blank start keeps one: the real install's
        check (dry builds)."""
        for preset in ("blank_ocean", "blank_terrain"):
            with self.subTest(preset=preset):
                pack = self.blank(preset)
                self.api.scenery_add(pack, [{"type": HALL, "x": 1500, "y": 1500}, {"type": OAK, "x": 1600, "y": 1500}])
                got = self.build()
                if got["state"] != "done":   # (on this map: "the map has no object to hang new ones on")
                    self.assertTrue(got["errors"], got)
                    self.assertNotIn("Something went wrong", got["message"])
                self.api.delete_map(pack)


class Roads(MapGame):
    def setUp(self):
        super().setUp()
        self.pack = self.api.duplicate_map(BLITZ, "Roads")["pack"]

    def test_a_road_joined_to_the_maps_own(self):
        self.api.road_add(self.pack, [[500, 2000], [500, 2900], [2500, 2900]])
        got = self.assertBuilds()
        self.assertTrue(any(ln.startswith("roads: Roads") for ln in got["lines"]), got["lines"])

    def test_odd_roads(self):
        """A road of two clicks on one spot, one ending past the map's edge, one of the 5000 points a line holds; one
        more refused in words. (The made-up map is 11 m across: every end is within a road's join of its road.)"""
        for points in ([[100, 100], [100, 100]], [[500, 2000], [-5000, 2000]],
                       [[500, 2000]] + [[500 + i * 0.5, 2100] for i in range(4999)]):
            self.assertEqual(page_said(self.api, "road_add", self.pack, points), "", len(points))
        self.assertIn("2 to 5000 points", page_said(self.api, "road_add", self.pack, [[500, 2000]] * 5001))
        self.assertEqual(len(self.api.roads(self.pack)["roads"]), 3)
        got = self.assertBuilds()
        self.assertIn("  road 3: 2 point(s), 2 link(s), joined at 2 end(s)", got["lines"])

    def test_the_maps_roads_taken_out_and_a_new_one(self):
        self.api.road_take_out(self.pack, True, True)
        self.api.road_add(self.pack, [[100, 100], [2900, 400]])
        self.assertBuilds()

    def test_a_road_over_the_sea_on_a_map_with_no_bridge_kind(self):
        pack = self.api.duplicate_map(BLITZ, "Sea Road", preset="blank_ocean")["pack"]
        self.api.scenario_move(pack, SCEN, 0, 1200.0, 1200.0)
        self.api.scenario_add_start(pack, SCEN, 1, 2400.0, 2400.0)
        self.api.road_add(pack, [[100, 100], [2900, 2900]])
        got = self.assertBuilds()
        self.assertIn("  1 water crossing(s), but this map has no bridge kind of its own: no bridge can go there, and "
                      "units can't cross", got["lines"])

    def test_a_bridge_on_a_map_without_bridges(self):
        self.assertEqual(self.api.map_bridges(self.pack)["kinds"], [])
        self.assertIn("isn't one of this map's own bridge kinds",
                      page_said(self.api, "bridge_add", self.pack, "TypeWarrior/Pont_TangeantFloor", 1000, 1000, 0, 30000))


class CheckThisMap(MapGame):
    """The Maps tab's Check this map (StudioApi.map_check, a job) on a copy with things placed, as a player presses it
    before Test in game."""

    def test_check_this_map(self):
        pack = self.api.duplicate_map(BLITZ, "Checked")["pack"]
        self.api.scenery_add(pack, [{"type": HALL, "x": 1500, "y": 1500}, {"type": OAK, "x": 1700, "y": 1500}])
        self.api.road_add(pack, [[500, 2000], [500, 2900]])
        got = self.wait(self.api.map_check(pack)["job"])
        self.assertEqual(got["state"], "done", got)
        self.assertEqual(got["result"]["pack"], pack)
        said = {f["say"] for f in got["result"]["findings"]}
        self.assertIn("mc_road_unjoined", said)   # the road's end at (500, 2900) joins nothing
        from ruse_studio.api import _words
        self.assertTrue(all(_words()[k].get("fr") for k in said))   # each finding has its words, French too


class Ground(MapGame):
    def setUp(self):
        super().setUp()
        self.pack = self.api.duplicate_map(BLITZ, "Ground")["pack"]

    def grid(self):
        from rusemod import cover
        from rusemod.cover import member
        data = self.copy_pack("Data", "PC", "190852", "DataMap_Win.dat")
        return cover.grid(bytes(data.read(data.entry(member(self.pack)))))

    def test_cover_and_movement_brushes(self):
        self.api.terrain_add(self.pack, [{"brush": "cover", "x": 8000, "y": 8000, "radius": 1500},
                                         {"brush": "uncover", "x": 1000, "y": 1000, "radius": 900},
                                         {"brush": "block_vehicles", "x": 6000, "y": 2000, "radius": 1600},
                                         {"brush": "open", "x": 15000, "y": 15000, "radius": 900}])
        got = self.assertBuilds()
        self.assertIn("cover: Ground, from ground", got["lines"])
        self.assertIn("movement: Ground, from ground", got["lines"])
        g = self.grid()
        cell = 16000 / g["size"]
        self.assertTrue(g["cells"][int(8000 // cell) * g["size"] + int(8000 // cell)] & 0x08)  # the cover painted

    # FINDING F4: a block for every unit (or water) painted over the map's own starting point, which the player hasn't
    # moved, builds with no word; the same block over a start the player moved is refused: "... is where no ground
    # unit can stand ...: the game would build that player's HQ wherever it finds room, possibly far away"
    # (rusemod.scenario.start_ground_problems looks only at new and moved starts).
    @unittest.expectedFailure
    def test_f4_a_block_over_the_maps_own_hq_is_said(self):
        self.api.terrain_add(self.pack, [{"brush": "block", "x": 1000, "y": 2000, "radius": 3000}])
        got = self.build()
        self.assertIn("is where no ground unit can stand", " ".join(got.get("errors", []) + got["lines"]))

    def test_the_hq_moved_onto_a_block(self):
        """The control for F4: the same block, the starting point moved into it: the build says where and stops."""
        self.api.terrain_add(self.pack, [{"brush": "block", "x": 1000, "y": 2000, "radius": 3000}])
        self.api.scenario_move(self.pack, SCEN, 0, 1100.0, 2100.0)
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn("the starting point moved (item 0) at (1100, 2100) in leveldesign_normal.scenario is where no "
                      "ground unit can stand", " ".join(got["errors"]))

    def own_picture(self):
        """A picture of the player's own added for Map Paint as the page adds one (a PNG as a data address)."""
        import base64
        from rusemod.dxt import png_bytes
        png = png_bytes(bytes((120, 90, 40, 255)) * 64 * 64, 64, 64, channels=4)
        got = self.api.add_ground_picture("my mud", "data:image/png;base64," + base64.b64encode(png).decode(), 20.0)
        return got["ref"]

    def test_paint_with_a_picture_of_ones_own(self):
        ref = self.own_picture()
        self.assertEqual(ref, "file:my mud.png")
        self.api.terrain_add(self.pack, [{"brush": "texture", "x": 1500, "y": 1500, "radius": 900, "texture": ref,
                                          "size": 5200}])
        got = self.assertBuilds()
        self.assertIn("paint: Ground, from ground: 1 stroke(s) on the ground's picture", got["lines"])

    def test_the_picture_taken_out_after_its_strokes(self):
        """The player deletes the picture's file (File Explorer) after painting with it: the mod check at the top and
        Test in game both name it."""
        ref = self.own_picture()
        self.api.terrain_add(self.pack, [{"brush": "texture", "x": 1500, "y": 1500, "radius": 900, "texture": ref,
                                          "size": 5200}])
        (self.map_dir() / "files" / "ground" / "my mud.png").unlink()
        said = "maps/Ground/terrain.toml paints with the picture my mud.png, which isn't in the mod's files/ground folder"
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn(said, got["message"])
        self.assertIn(said, " ".join(p["problem"] for p in self.api.check_mod()["problems"]))

    def test_paint_and_stamp(self):
        self.api.terrain_add(self.pack, [{"brush": "paint", "x": 1500, "y": 1500, "radius": 800, "colour": "#a0522d"},
                                         {"brush": "stamp", "x": 1500, "y": 1500, "radius": 400, "sx": 300, "sy": 0}])
        got = self.assertBuilds()
        self.assertIn("paint: Ground, from ground: 2 stroke(s) on the ground's picture", got["lines"])
        self.assertIn('colour must be like "#a07850"',
                      page_said(self.api, "terrain_add", self.pack, [{"brush": "paint", "x": 1, "y": 1, "radius": 5,
                                                                      "colour": "red"}]))
        self.assertEqual(len(self.api.terrain(self.pack)["strokes"]), 2)  # a refusal adds nothing


if __name__ == "__main__":
    unittest.main()
