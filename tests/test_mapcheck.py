"""The map check (rusemod.mapcheck): each check on made-up graphs, roads and scenery, and the whole check on the real
game's Blitz when it's installed."""
import re
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from test_scenery import block, compact, make_scenery, moved
from rusemod import mapcheck, nav
from rusemod.mapcheck import (WORDS, _samples, check_built, closed_bridges, closed_roads, crossable, cut_off,
                              map_objects, on_roads, unjoined)
from rusemod.roadnet import RoadNet
from rusemod.scenery import Scenery

DECK = (9000.0, 2000.0, 18000.0, 2000.0)  # over the river of river(), bank to bank


def graph(circles, pairs=None, index=None):
    """A graph of `circles` (x, y, r), linked in `pairs` (each to the next when not given) where they meet, its index
    one leaf of the circles in `index` (all of them when not given)."""
    pairs = [(i, i + 1) for i in range(len(circles) - 1)] if pairs is None else pairs
    links = [(a, b) + nav._meeting(circles[a], circles[b]) for a, b in sorted(pairs, key=lambda p: p[1])]
    mine = [[] for _ in circles]
    for k, (a, b, _x, _y) in enumerate(links):
        mine[a].append(k)
        mine[b].append(k)
    recs, lists = [], []
    for c, (x, y, r) in enumerate(circles):
        recs.append((x, y, r, len(lists), 0))
        lists += mine[c]
    recs.append((0.0, 0.0, 0.0, len(lists), 0))
    leaf = list(range(len(circles))) if index is None else index
    return nav.Graph(box=(0, 0, 65536.0), circles=recs, links=links, lists=lists, crossings=b"",
                     points=nav._tree_write(["leaf", leaf]), head_rest=bytes(nav.HEADER - 20))


LAND = [(5000.0, 2000.0, 6400.0), (5000.0, 14000.0, 6400.0), (13500.0, 18000.0, 6400.0), (22000.0, 14000.0, 6400.0),
        (22000.0, 2000.0, 6400.0)]


def river(extra=(), pairs=None, index=None):
    """Two banks along y 2000, W (x up to 11,400) and E (x from 15,600), with the river between: no circle over it.
    One piece, as a map's land is: joined the long way round, north of the river (three circles that don't reach
    y 2000)."""
    circles = LAND + list(extra)
    return graph(circles, [(i, i + 1) for i in range(4)] if pairs is None else pairs, index)


def said(f) -> str:
    """A finding in words, as the UI says it (the units by their own word)."""
    data = dict(f["data"])
    if "units" in data:
        data["units"] = WORDS["mc_units_" + data["units"]]
    return WORDS[f["say"]].format(**data)


class Pieces(unittest.TestCase):
    def test_one_piece_says_nothing(self):
        self.assertEqual(cut_off(river(), "infantry"), [])

    def test_each_piece_past_the_first(self):
        found = cut_off(river([(40000.0, 41000.0, 3200.0)]), "vehicles")
        self.assertEqual(len(found), 1)
        f = found[0]
        self.assertEqual((f["key"], f["level"], f["say"]), ("pieces", "fail", "mc_cut_off"))
        self.assertEqual(f["data"], {"units": "vehicles", "sub": 0, "circles": 1, "metres": 25, "x": 40000,
                                     "y": 41000})
        self.assertIsNone(f["fix"])
        self.assertIn("cut off for vehicles", said(f))

    def test_emptied_circles_are_no_piece(self):
        self.assertEqual(cut_off(river([(40000.0, 41000.0, 0.0)]), "infantry"), [])

    def test_a_local_graph_in_two_pieces(self):
        g = river()
        g.subs = [graph([(1000.0, 1000.0, 1280.0), (9000.0, 1000.0, 1280.0)], pairs=[])]
        found = cut_off(g, "infantry")
        self.assertEqual([(f["data"]["sub"], f["data"]["circles"]) for f in found], [(1, 1)])


class Roads(unittest.TestCase):
    def test_samples_every_step_and_the_end(self):
        self.assertEqual([d for d, _x, _y in _samples([(0.0, 0.0), (1200.0, 0.0)], 500.0)], [0, 500, 1000, 1200])
        self.assertEqual([d for d, _x, _y in _samples([(0.0, 0.0), (600.0, 0.0), (1000.0, 0.0)], 500.0)],
                         [0, 500, 1000])

    def test_a_stretch_over_the_river(self):
        found = closed_roads(river(), [[(0.0, 2000.0), (27000.0, 2000.0)]], "infantry")
        self.assertEqual(len(found), 1)
        f = found[0]
        self.assertEqual((f["key"], f["level"], f["say"]), ("road", "warn", "mc_road_closed"))
        # 11,500 to 15,500 unfound, a sample standing for 500: 4,500 map units, 17 m, its middle at 13,500
        self.assertEqual(f["data"], {"units": "infantry", "road": 1, "metres": 17, "x": 13500, "y": 2000})
        self.assertEqual(said(f), "Road 1: 17 m around (13500, 2000) is ground infantry can't use.")

    def test_a_bridge_deck_is_left_to_the_bridge_check(self):
        self.assertEqual(closed_roads(river(), [[(0.0, 2000.0), (27000.0, 2000.0)]], "infantry", [DECK]), [])

    def test_each_road_and_each_stretch(self):
        lines = [[(0.0, 2000.0), (5000.0, 2000.0)],  # all on W
                 [(0.0, 2000.0), (13000.0, 2000.0)],  # into the river: 11,500 to its end
                 [(5000.0, 2000.0), (5000.0, -30000.0), (22000.0, -30000.0), (22000.0, 2000.0)]]  # off the land
        found = closed_roads(river(), lines, "vehicles")
        self.assertEqual([(f["data"]["road"], f["data"]["x"], f["data"]["y"]) for f in found],
                         [(2, 12250, 2000), (3, 13500, -30000)])
        self.assertEqual(found[0]["data"]["metres"], 8)  # 11,500 to 13,000 and a sample's 500

    def test_ground_the_index_can_t_find_is_closed(self):
        g = river(index=[0, 1, 2, 3])  # E is there, but no order can be given onto it
        found = closed_roads(g, [[(16000.0, 2000.0), (20000.0, 2000.0)]], "infantry")
        self.assertEqual([(f["data"]["metres"], f["data"]["x"]) for f in found], [(15, 18000)])


class Bridges(unittest.TestCase):
    def test_no_bridge_no_way_across(self):
        g = river()
        self.assertFalse(crossable(g, DECK))
        found = closed_bridges(g, [DECK + (2,)], "vehicles")
        self.assertEqual(len(found), 1)
        f = found[0]
        self.assertEqual((f["key"], f["level"], f["say"]), ("bridge", "fail", "mc_bridge_closed"))
        self.assertEqual(f["data"], {"units": "vehicles", "road": 2, "metres": 35, "x": 13500, "y": 2000})
        self.assertIn("closed to vehicles", said(f))

    def test_an_opened_deck_is_crossed(self):
        g = river()
        g.open([DECK], 1280.0)
        self.assertTrue(crossable(g, DECK))
        self.assertEqual(closed_bridges(g, [DECK + (0,)], "infantry"), [])

    def test_a_deck_cut_off_from_the_banks(self):
        deck = [(9000.0 + 2560.0 * k, 2000.0, 2560.0) for k in range(4)]
        pairs = [(i, i + 1) for i in range(4)] + [(5 + k, 6 + k) for k in range(3)]  # linked to each other only
        g = river(deck, pairs)
        self.assertEqual(g.parts(), [5, 4])
        self.assertFalse(crossable(g, DECK))

    def test_a_deck_the_index_can_t_find(self):
        g = river()
        g.open([DECK], 1280.0)
        g.points = nav._tree_write(["leaf", [0, 1, 2, 3, 4]])  # the deck's circles left out of the index
        self.assertFalse(crossable(g, DECK))


class Joins(unittest.TestCase):
    def setUp(self):
        self.net = RoadNet([(0.0, 0.0), (10000.0, 0.0)], [(0, 1, 1000)])
        self.lines = [[(10000.0, 5000.0), (10000.0, 50000.0)],    # its start joins the network, its end nothing
                      [(100000.0, 100000.0), (120000.0, 100000.0)],  # far from everything
                      [(10000.0, 60000.0), (30000.0, 60000.0)]]   # its start joins road 1's end
        for line in self.lines:
            self.net.add_road(line)

    def test_the_ends_not_joined(self):
        found = unjoined(self.net, self.lines)
        self.assertEqual([(f["data"]["road"], f["data"]["x"], f["data"]["y"]) for f in found],
                         [(2, 100000, 100000), (2, 120000, 100000), (3, 30000, 60000)])
        f = found[0]
        self.assertEqual((f["key"], f["level"], f["say"]), ("join", "info", "mc_road_unjoined"))
        self.assertIn("Supply trucks", said(f))

    def test_a_network_not_built_from_these_roads(self):
        self.assertEqual(unjoined(RoadNet([(0.0, 0.0), (10000.0, 0.0)], [(0, 1, 1000)]), self.lines), [])
        self.assertEqual(unjoined(self.net, self.lines[:2]), [])


class Objects(unittest.TestCase):
    LINE = [[(0.0, 9000.0), (10000.0, 9000.0)]]

    def test_buildings_first_then_the_nearest(self):
        objects = [("TypeWarrior/Barriere", 3000.0, 9100.0, "prop"), ("TypeWarrior/MairieNormande", 4000.0, 9300.0,
                   "building"), ("TypeWarrior/Ferme", 6000.0, 9700.0, "building")]  # 700 away: off the road
        found = on_roads(objects, self.LINE)
        self.assertEqual([(f["data"]["name"], f["data"]["x"], f["data"]["road"]) for f in found],
                         [("MairieNormande", 4000, 1), ("Barriere", 3000, 1)])
        f = found[0]
        self.assertEqual((f["key"], f["level"], f["say"]), ("object", "info", "mc_object_on_road"))
        self.assertEqual(said(f), "MairieNormande stands on road 1 at (4000, 9300).")

    def test_at_most_so_many_and_a_count(self):
        objects = [("TypeWarrior/Barriere", 1000.0 * k, 9000.0, "prop") for k in range(5)]
        found = on_roads(objects, self.LINE, most=2)
        self.assertEqual([f["say"] for f in found], ["mc_object_on_road"] * 2 + ["mc_objects_more"])
        self.assertEqual(found[-1]["data"], {"n": 3})
        self.assertEqual(said(found[-1]), "3 more objects stand on the new roads.")

    def test_the_map_s_buildings_and_props_near_a_road(self):
        names = ["TypeWarrior/MairieNormande", "TypeWarrior/Chene_02", "TypeWarrior/Barriere",
                 "TypeWarrior/Pont_Metallique_02"]
        descs = {names[0]: SimpleNamespace(group="building", bridge=False),
                 names[1]: SimpleNamespace(group="vegetation", bridge=False),
                 names[2]: SimpleNamespace(group="prop", bridge=False),
                 names[3]: SimpleNamespace(group="building", bridge=True)}
        # block 1: a town hall, an oak and a fence; block 0: a bridge, a town hall, and block 1 twice
        farm = block([struct.pack("<I", 0x80000000 | 0 << 4 | 1), moved(0x80000000 | 1 << 4, 50.0, 0.0),
                      moved(0x80000000 | 2 << 4, 100.0, 0.0)])
        root_len = len(block([compact(3, 0.0, 0.0), compact(0, 0.0, 0.0), moved(0, 0, 0), moved(0, 0, 0)]))
        root = block([compact(3, 2000.0, 9000.0), compact(0, 1000.0, 2000.0), moved(root_len, 5000.0, 0.0),
                      moved(root_len, 5000.0, 9000.0)])
        sc = Scenery(make_scenery([root, farm], names))
        got = sorted((name, round(x), round(y), group) for name, x, y, group in map_objects(sc, descs, self.LINE))
        # the copy of block 1 at y 0 is nowhere near the road: not walked; the root's own town hall is listed, and
        # on_roads leaves it out
        self.assertEqual(got, [(names[2], 5100, 9000, "prop"), (names[0], 1000, 2000, "building"),
                               (names[0], 5000, 9000, "building")])
        self.assertEqual([f["data"]["x"] for f in on_roads(map_objects(sc, descs, self.LINE), self.LINE)],
                         [5000, 5100])

    def test_no_road_no_walk(self):
        self.assertEqual(list(map_objects(SimpleNamespace(names=[]), {}, [])), [])


class Built(unittest.TestCase):
    def test_every_check_on_a_mapinfo(self):
        lines =[[(0.0, 2000.0), (27000.0, 2000.0)], [(40000.0, 40000.0), (45000.0, 40000.0)]]
        net = RoadNet([(0.0, 0.0), (5000.0, 0.0)], [(0, 1, 500)])
        for line in lines:
            net.add_road(line)
        infantry, vehicles = river(), river()
        infantry.open([DECK], 1280.0)  # the build opened the bridge to infantry only
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), infantry.to_bytes(), vehicles.to_bytes(), b"cover")) + b"tail", {})
        found = check_built(win, lines, [DECK + (1,)], [("TypeWarrior/MairieNormande", 20000.0, 2300.0, "building")])
        self.assertEqual([(f["key"], f["data"].get("units"), f["data"].get("road")) for f in found],
                         [("road", "infantry", 2),  # road 2 is off the land, for both
                          ("bridge", "vehicles", 1), ("road", "vehicles", 2),
                          ("join", None, 1),  # road 1's start joins the network, its end doesn't
                          ("join", None, 2), ("join", None, 2),
                          ("object", None, 1)])
        for f in found:
            said(f)
        self.assertEqual(check_built(win, []), [])
        broken = check_built(b"not a mapinfo.win", [])  # a finding, not a crash
        self.assertEqual([(f["key"], f["level"], f["say"]) for f in broken], [("build", "fail", "mc_build_failed")])


class Words(unittest.TestCase):
    def test_every_word_the_check_says(self):
        source = Path(mapcheck.__file__).read_text(encoding="utf-8")
        used = set(re.findall(r'"(mc_[a-z_]+)"', source.split("WORDS = {", 1)[1].split("\n}\n", 1)[1]))
        self.assertTrue(used)
        self.assertLessEqual(used, set(WORDS))
        self.assertLessEqual({"mc_units_infantry", "mc_units_vehicles"}, set(WORDS))


class RealGame(unittest.TestCase):
    """The whole check, the build included, on the game's Blitz with a one-road mod (only when the game is here)."""

    def test_blitz_with_a_new_road(self):
        from rusemod.steam import find_game
        found = find_game()
        if found is None:
            self.skipTest("R.U.S.E. isn't installed here")
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "one-road"
            (mod / "maps" / "SuperCrossRoads4").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "one-road"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "maps" / "SuperCrossRoads4" / "roads.toml").write_text(
                "[[road]]\npoints = [[450000, 650000], [500000, 655000], [550000, 660000]]\n", encoding="utf-8")
            lines = []
            got = mapcheck.check_map(Path(found["game_dir"]), mod, "SuperCrossRoads4", say=lines.append)
        self.assertTrue(got)
        self.assertNotIn("mc_build_failed", [f["say"] for f in got], lines[-5:])
        for f in got:
            self.assertEqual(set(f), {"key", "level", "say", "data", "fix"})
            said(f)
        self.assertTrue(any(line.startswith("roads: SuperCrossRoads4") for line in lines))


if __name__ == "__main__":
    unittest.main()
