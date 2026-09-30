"""Bridges where a new road crosses water (rusemod.bridges), and the movement graphs opened along them (rusemod.nav
Graph.open), on made-up maps: a tiny mesh with one strip of water, a three-circle graph."""
import struct
import unittest
from types import SimpleNamespace

from test_nav import row
from test_scenery import block, compact, make_scenery
from test_tms import make_tms
from rusemod import nav
from rusemod.bridges import DECK, Water, bridge_objects, bridge_type, crossings, cut, plan
from rusemod.scenery import Scenery
from rusemod.tms import Tms

# the fixture's water: cell (0, 0)'s first row of quads, y from 0 to 125 across x 0..1000 (map units)
MESH = make_tms(water_cell=(0, 0))


def desc(category, model="m.ase"):
    return SimpleNamespace(category=category, model=model, models=())


class Crossings(unittest.TestCase):
    def test_water_found_along_a_road(self):
        water = Water(Tms(MESH))
        self.assertTrue(water.at(500.0, 60.0))
        self.assertFalse(water.at(500.0, 400.0))
        self.assertFalse(water.at(1500.0, 60.0))  # the other cell is dry
        got = crossings(water, [(500.0, 400.0), (500.0, 20.0)], sample=10.0, bank=50.0, least=50.0)
        self.assertEqual(len(got), 1)
        x0, y0, x1, y1 = got[0]
        self.assertEqual((round(x0), round(x1), round(y1)), (500, 500, 20))  # to the road's end, not past it
        self.assertTrue(165 <= y0 <= 185, y0)  # the water's edge (125) plus the bank (50), give or take a sample
        self.assertEqual(crossings(water, [(1500.0, 400.0), (1500.0, 20.0)], sample=10.0, bank=50.0, least=50.0), [])
        self.assertEqual(crossings(water, [(500.0, 400.0), (500.0, 20.0)], sample=10.0, bank=50.0, least=500.0), [])

    def test_the_maps_own_bridge_kind(self):
        names = ["TypeWarrior/Chene_02", "TypeWarrior/Pont_Metallique_02", "TypeWarrior/Pont_Metallique_02_TangeantFloor",
                 "TypeWarrior/Pont_Old"]
        descs = {names[0]: desc("Vegetation"), names[1]: desc("COC/Normandie/Ponts"),
                 names[2]: desc("COC/Normandie/Ponts"), names[3]: desc("Italie/Ponts")}
        self.assertEqual(bridge_type(names, {1: 9, 2: 1, 3: 20}, descs), names[2])  # a floor first, however used
        self.assertEqual(bridge_type(names[:2] + names[3:], {1: 1, 2: 20}, descs), names[3])  # else the most used
        self.assertIsNone(bridge_type(names[:1], {0: 5}, descs))

    def test_bridges_end_to_end_along_the_span(self):
        got = bridge_objects("TypeWarrior/Pont", (0.0, 0.0, 10000.0, 0.0), 3000.0)
        self.assertEqual([round(o.x) for o in got], [1250, 3750, 6250, 8750])
        self.assertEqual({(o.y, o.turn, o.size, o.solid) for o in got}, {(0.0, 0.0, 1.0, False)})
        south = bridge_objects("TypeWarrior/Pont", (0.0, 0.0, 0.0, 2000.0), 3000.0, 90.0)
        self.assertEqual([(round(o.x), round(o.y), o.turn) for o in south], [(0, 1000, 180.0)])
        self.assertEqual(bridge_objects("x", (0.0, 0.0, 0.0, 0.0), 3000.0), [])

    def test_the_painter_skips_the_deck(self):
        pieces = cut([[(0.0, 0.0), (20000.0, 0.0)]], [(8000.0, 0.0, 12000.0, 0.0)])
        self.assertEqual(len(pieces), 2)
        self.assertTrue(all(p[0] <= 8000 + 1 for p in pieces[0]) and all(p[0] >= 12000 - 1 for p in pieces[1]), pieces)
        self.assertTrue(pieces[0][-1][0] > 7000 and pieces[1][0][0] < 13000)  # cut at the deck's ends, not before
        far = [[(0.0, 5000.0), (20000.0, 5000.0)]]  # well off the deck: one piece, the same as with no span
        self.assertEqual(cut(far, [(8000.0, 0.0, 12000.0, 0.0)]), cut(far, []))
        self.assertEqual(len(cut(far, [])), 1)

    def test_a_plan_for_a_map(self):
        bridge = "TypeWarrior/Pont_TangeantFloor"
        sc = Scenery(make_scenery([block([compact(0, 100.0, 100.0)])], [bridge]))
        descs = {bridge: desc("Italie/Ponts")}
        line = [(500.0, 400.0), (500.0, 20.0)]
        objects, spans, notes = plan(MESH, [line], sc, descs, length_of=lambda k: (60.0, 0.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual(len(spans), 1)
        self.assertEqual({o.type for o in objects}, {bridge})
        self.assertEqual(len(objects), 3)  # about 155 units of deck, 60 each
        self.assertTrue(all(o.solid is False and o.turn == 270.0 for o in objects))  # north on the map (y down)
        self.assertIn("1 water crossing(s): 3 x Pont_TangeantFloor", notes[0])
        objects, spans, notes = plan(MESH, [line], sc, {}, length_of=lambda k: (60.0, 0.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual((objects, spans), ([], []))  # no bridge kind: nothing placed, and the water stays closed
        self.assertIn("no bridge kind of its own", notes[0])
        self.assertEqual(plan(MESH, [[(1500.0, 400.0), (1500.0, 20.0)]], sc, descs, length_of=lambda k: (60.0, 0.0),
                              sample=10.0, bank=50.0, least=50.0), ([], [], []))


class Opening(unittest.TestCase):
    def test_circles_along_a_deck_linked_to_the_bank(self):
        g = row()
        counts = g.open([(11600.0, 2000.0, 16000.0, 2000.0)], radius=800.0)  # from C's edge eastwards
        self.assertEqual(counts, {"added": 7, "linked": 7})  # one to C, then each to the next
        self.assertEqual(len(g.circles) - 1, 10)
        self.assertEqual([round(c[0]) for c in g.circles[3:10]], [11600, 12333, 13067, 13800, 14533, 15267, 16000])
        self.assertEqual(g.links[:2], [(0, 1, 4500.0, 2000.0), (1, 2, 9000.0, 2000.0)])  # the old ones first
        self.assertEqual(sorted(g.links_of(2)), [1, 2])  # C: its old link, and the bridge's first
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        self.assertEqual(sorted(nav._tree_read(g.points)[1]), list(range(10)))  # the one leaf lists them all
        self.assertEqual(len(g.crossings), 28)  # the crossing through B, renumbered, still there
        self.assertEqual(struct.unpack_from("<2H", g.crossings, 20), (0, 1))

    def test_the_index_widens_on_the_way_to_the_bank(self):
        root = ["branch", 1, struct.pack("<2f", 10200.0, 8400.0), ["leaf", [0, 1]], ["leaf", [2]]]  # x: A B | C
        points = nav._tree_write(root)
        got = nav._tree_read(nav._index_add(points, {2: [3, 4]}, {2: (7000.0, 0.0, 20000.0, 4000.0)}))
        self.assertEqual((got[3][1], got[4][1]), ([0, 1], [2, 3, 4]))
        self.assertEqual(struct.unpack("<2f", got[2]), (10200.0, 7000.0))  # the right half now reaches to 7000
        got = nav._tree_read(nav._index_add(points, {0: [3]}, {0: (0.0, 0.0, 12000.0, 4000.0)}))
        self.assertEqual(struct.unpack("<2f", got[2]), (12000.0, 8400.0))  # the left half now reaches to 12000
        deep = ["branch", 1, struct.pack("<2f", 10200.0, 8400.0), ["leaf", [0, 1]],
                ["branch", 1, struct.pack("<2f", 5200.0, 30000.0), ["leaf", [2]], ["leaf", []]]]  # then y: C | -
        got = nav._tree_read(nav._index_add(nav._tree_write(deep), {2: [3]}, {2: (9000.0, 0.0, 20000.0, 9000.0)}))
        self.assertEqual(struct.unpack("<2f", got[2]), (10200.0, 8400.0))  # x: C's half already reached 8400
        self.assertEqual(struct.unpack("<2f", got[4][2]), (9000.0, 30000.0))  # y: the left half's far edge grew
        untouched = nav._index_add(points, {2: [3]})
        self.assertEqual(struct.unpack("<2f", nav._tree_read(untouched)[2]), (10200.0, 8400.0))


if __name__ == "__main__":
    unittest.main()
