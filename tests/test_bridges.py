"""Bridges where a new road crosses water (rusemod.bridges), and the movement graphs opened along them (rusemod.nav
Graph.open), on made-up maps: a tiny mesh with one strip of water, a three-circle graph."""
import struct
import unittest
from types import SimpleNamespace

from test_nav import row
from test_scenery import block, compact, make_scenery, moved
from test_tms import make_tms
from rusemod import nav
from rusemod.bridges import (CLOSE, DECK, STRETCH, Water, _closing, apply_spans, bridge_objects, bridge_type,
                              crossings, cut, deck, placed_spans, plan)
from rusemod.roadnet import RoadNet, build_tree
from rusemod.scenery import SCALE16, NewObject, Scenery
from rusemod.tms import Tms

# the fixture's water: cell (0, 0)'s first row of quads, y from 0 to 125 across x 0..1000 (map units)
MESH = make_tms(water_cell=(0, 0))


def desc(category, model="m.ase"):
    return SimpleNamespace(category=category, model=model, models=())


def sunk(sym, x, y, z):
    """An object stored the compact way, unturned, at height z (the shipped bridges sit a little under the ground)."""
    one = round(1 / SCALE16)
    return struct.pack("<I4h4f", 0x80000000 | sym << 4, one, 0, 0, one, x, y, z, 1.0)


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

    def test_one_bridge_stretched_bank_to_bank(self):
        # every shipped bridge is one piece resting on both banks: the game sets it on the ground under its ends, so
        # a piece with an end over the water tips into the river (seen in the game, 2026-09-30)
        got = bridge_objects("TypeWarrior/Pont", (0.0, 0.0, 10000.0, 0.0), 6000.0, 90.0, -200.0)
        self.assertEqual(got, [NewObject("TypeWarrior/Pont", 5000.0, 0.0, 90.0, 1.0, False, 1.6667, -200.0)])
        self.assertEqual(bridge_objects("x", (0.0, 0.0, 20000.0, 0.0), 6000.0, 90.0), [])  # wider than it stretches
        short = bridge_objects("x", (0.0, 0.0, 3000.0, 0.0), 6000.0, 90.0)
        self.assertEqual(short[0].stretch, STRETCH[0])  # a creek: never squeezed below the game's own
        long_on_x = bridge_objects("x", (0.0, 0.0, 0.0, 2000.0), 1500.0, 0.0)  # a model long on its x is sized
        self.assertEqual([(o.x, o.y, o.turn, o.size, o.stretch) for o in long_on_x], [(0.0, 1000.0, 90.0, 1.3333, 1.0)])
        self.assertEqual(bridge_objects("x", (0.0, 0.0, 0.0, 0.0), 3000.0), [])

    def test_a_placed_bridges_deck(self):
        o = NewObject("B", 5000.0, 0.0, 90.0, 1.0, False, 1.5)
        self.assertEqual([round(v) for v in deck(o, 6000.0, 90.0)], [500, 0, 9500, 0])
        self.assertEqual([round(v) for v in deck(NewObject("B", 0.0, 0.0, 0.0, 2.0), 1000.0, 0.0)], [-1000, 0, 1000, 0])
        descs = {"B": desc("COC/Normandie/Ponts"), "H": desc("Normandie/Maisons")}
        spans = placed_spans([o, NewObject("H", 1.0, 2.0)], descs, lambda k: (6000.0, 90.0))
        self.assertEqual([[round(v) for v in d] for d in spans], [[500, 0, 9500, 0]])  # a house opens nothing

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
        descs = {bridge: desc("Italie/Ponts")}
        sc = Scenery(make_scenery([block([sunk(0, 100.0, 900.0, -200.0), sunk(0, 900.0, 900.0, -260.0),
                                          sunk(0, 900.0, 950.0, -210.0)])], [bridge]))  # the map's own, on dry land
        line = [(500.0, 400.0), (500.0, 20.0)]
        got = plan(MESH, [line], sc, descs, length_of=lambda k: (100.0, 90.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual(len(got.objects), 1)
        o = got.objects[0]
        self.assertEqual((o.type, o.x, o.turn, o.size, o.solid, o.lift), (bridge, 500.0, 0.0, 1.0, False, -210.0))
        self.assertTrue(1.4 < o.stretch < 1.7, o.stretch)  # about 155 units of crossing, the model 100 long
        self.assertEqual([[round(v) for v in d] for d in got.spans], [[round(v) for v in deck(o, 100.0, 90.0)]])
        self.assertIn("1 water crossing(s): 1 x Pont_TangeantFloor placed, stretched to reach both banks", got.notes[0])
        self.assertEqual((got.hide, got.closed), ([], []))  # no old bridge on the way
        wide = plan(MESH, [line], sc, descs, length_of=lambda k: (60.0, 90.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual((wide.objects, wide.spans), ([], []))  # would need 2.6 times its length
        self.assertIn("too wide for Pont_TangeantFloor", wide.notes[0])
        none = plan(MESH, [line], sc, {}, length_of=lambda k: (100.0, 90.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual((none.objects, none.spans), ([], []))  # no bridge kind: nothing placed, the water stays closed
        self.assertIn("no bridge kind of its own", none.notes[0])
        dry = plan(MESH, [[(1500.0, 400.0), (1500.0, 20.0)]], sc, descs, length_of=lambda k: (100.0, 90.0),
                   sample=10.0, bank=50.0, least=50.0)
        self.assertEqual((dry.objects, dry.spans, dry.notes), ([], [], []))
        by_hand = plan(MESH, [line], sc, descs, length_of=lambda k: (100.0, 90.0), sample=10.0, bank=50.0, least=50.0,
                       existing=[(500.0, 0.0, 500.0, 200.0)])
        self.assertEqual(by_hand.objects, [])
        self.assertIn("already bridged by hand", by_hand.notes[0])

    def test_a_road_over_an_old_bridge_replaces_it(self):
        # owner, 2026-09-30: "if a road goes over an existing bridge it should delete the old and replace it with a
        # new one"
        bridge = "TypeWarrior/Pont_TangeantFloor"
        descs = {bridge: desc("Italie/Ponts")}
        raw = make_scenery([block([sunk(0, 100.0, 900.0, -200.0), sunk(0, 500.0, 60.0, -200.0)])], [bridge])
        sc = Scenery(raw)
        across = [(500.0, 400.0), (500.0, -300.0)]  # right over the river, bank to bank
        got = plan(MESH, [across], sc, descs, length_of=lambda k: (150.0, 90.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual(len(got.objects), 1)
        old = next(it for it in sc.blocks[0].items if it.matrix()[3] == 500.0)
        self.assertEqual(got.hide, [(0, old.at)])  # the one under the road, not the one on dry land
        self.assertEqual(got.closed, [])  # it ran where the new one runs: nothing left over water to close
        aslant = plan(MESH, [[(300.0, 400.0), (700.0, -300.0)]], sc, descs, length_of=lambda k: (150.0, 90.0),
                      sample=10.0, bank=50.0, least=50.0)
        self.assertEqual(aslant.hide, [(0, old.at)])
        self.assertEqual(aslant.closed, [])  # still within a deck's width of the new one (the fixture is small)
        line = [(500.0, 400.0), (500.0, 20.0)]
        self.assertIn("1 old bridge(s) replaced", got.notes[-1])
        # an old bridge in a block the map places twice can't be sunk without sinking both: it stays and serves
        inner = block([sunk(0, 0.0, 0.0, -200.0)])
        root_len = len(block([sunk(0, 100.0, 900.0, -200.0), moved(0, 0.0, 0.0), moved(0, 0.0, 0.0)]))
        root = block([sunk(0, 100.0, 900.0, -200.0), moved(root_len, 500.0, 60.0), moved(root_len, 5000.0, 5000.0)])
        twice = Scenery(make_scenery([root, inner], [bridge]))
        kept = plan(MESH, [line], twice, descs, length_of=lambda k: (100.0, 90.0), sample=10.0, bank=50.0, least=50.0)
        self.assertEqual((kept.objects, kept.spans, kept.hide), ([], [], []))
        self.assertEqual([[round(v) for v in d] for d in kept.kept], [[500, 10, 500, 110]])  # the painter skips it
        self.assertIn("can't be taken away, so it stays and serves the road", kept.notes[-1])

    def test_where_an_old_bridge_stood_over_water_is_closed(self):
        water = Water(Tms(MESH))
        self.assertEqual(_closing(water, (100.0, 60.0, 400.0, 60.0), []),
                         [(100.0, 60.0, CLOSE), (400.0, 60.0, CLOSE)])  # both ends over the water
        self.assertEqual(_closing(water, (100.0, 60.0, 400.0, 60.0), [(250.0, 0.0, 250.0, 125.0)]), [])  # the new deck
        self.assertEqual(_closing(water, (100.0, 400.0, 400.0, 400.0), []), [])  # over dry land

    def test_opened_and_closed_in_the_maps_movement_and_roads(self):
        from rusemod.cover import member
        from rusemod import nav as navmod
        from ruse_mod_engine import sdb
        net = RoadNet([(0.0, 2000.0), (6000.0, 2000.0), (12000.0, 2000.0)], [])
        net.links = [(0, 1, 600), (1, 2, 600)]
        net.tree = build_tree(net.points, net.links)
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
        g = row()
        win = navmod.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})
        read = {member("Blitz"): win}.get
        new, notes = apply_spans(read, "Blitz", [(11600.0, 2000.0, 16000.0, 2000.0)])
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        self.assertEqual(bufs[0], net.to_bytes())  # no old bridge: the road network is left alone
        self.assertEqual(len(navmod.Graph.read(bufs[2]).circles) - 1, 3 + 3)  # 4,400 of deck, a circle every 2,560
        new, notes = apply_spans(read, "Blitz", [], [(10000.0, 2000.0, 1000.0)])  # where an old one stood
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        for k in (1, 2):
            self.assertEqual([c[2] > 0 for c in navmod.Graph.read(bufs[k]).circles[:-1]], [True, True, False])
        roads = RoadNet.read(bufs[0])
        self.assertEqual((roads.points, roads.links), ([(0.0, 2000.0), (6000.0, 2000.0)], [(0, 1, 600)]))
        self.assertIn("road network: 1 link(s) taken off the old bridges", notes)


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
