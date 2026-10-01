"""Bridges where a new road crosses water (rusemod.bridges), and the movement graphs opened along them (rusemod.nav
Graph.open), on made-up maps: a tiny mesh with one strip of water, a three-circle graph."""
import dataclasses
import struct
import unittest
from types import SimpleNamespace

from test_nav import row
from test_scenery import block, compact, make_scenery, moved
from test_tms import make_tms
from rusemod import nav
from rusemod.bridges import (CLOSE, DECK, STRETCH, BridgeError, Water, _closing, apply_spans, bridge_objects,
                              bridge_type, crossings, cut, deck, placed_spans, plan)
from rusemod.roadnet import RoadNet, build_tree
from rusemod.scenery import SCALE16, NewObject, Scenery
from rusemod.tms import Tms

# the fixture's water: cell (0, 0)'s first row of quads, y from 0 to 125 across x 0..1000 (map units)
MESH = make_tms(water_cell=(0, 0))


def desc(category, model="m.ase"):
    return SimpleNamespace(category=category, model=model, models=())


def banks():
    """Two banks and a river between: W (r 6400) at x 5000 and E (r 6400) at x 22000, both on y 2000, with nothing
    between x 11,400 and 15,600. One piece, as a map's land is: linked the long way round. The index: x splits them."""
    return nav.Graph(
        box=(0, 0, 32000.0),
        circles=[(5000.0, 2000.0, 6400.0, 0, 0), (22000.0, 2000.0, 6400.0, 1, 0), (0.0, 0.0, 0.0, 2, 0)],
        links=[(0, 1, 13500.0, 20000.0)],
        lists=[0, 0],
        crossings=b"",
        points=nav._tree_write(["branch", 1, struct.pack("<2f", 11400.0, 15600.0), ["leaf", [0]], ["leaf", [1]]]),
        head_rest=bytes(nav.HEADER - 20))


def chain(circles):
    """A graph of `circles` (x, y, r), each linked to the next, its index one leaf."""
    links = [(i, i + 1) + nav._meeting(circles[i], circles[i + 1]) for i in range(len(circles) - 1)]
    mine = [[] for _ in circles]
    for k, (a, b, _x, _y) in enumerate(links):
        mine[a].append(k)
        mine[b].append(k)
    recs, lists = [], []
    for c, (x, y, r) in enumerate(circles):
        recs.append((x, y, r, len(lists), 0))
        lists += mine[c]
    recs.append((0.0, 0.0, 0.0, len(lists), 0))
    return nav.Graph(box=(0, 0, 32000.0), circles=recs, links=links, lists=lists, crossings=b"",
                     points=nav._tree_write(["leaf", list(range(len(circles)))]), head_rest=bytes(nav.HEADER - 20))


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

    def test_what_counts_as_a_bridge(self):
        from rusemod.scenery import is_bridge
        self.assertTrue(is_bridge("COC/Normandie/Ponts", "TypeWarrior/Pont_Metallique_02"))
        self.assertTrue(is_bridge("COC/Tunisie/DecorsKasserine/Ponts", "TypeWarrior/COC_PontDesert_A"))
        # Holland files its bridges with its town's buildings (on 4 maps, with floors): by their name
        self.assertTrue(is_bridge("Hollande/Batiments_ville", "TypeWarrior/Pont_Hollande_02_Bois_TangeantFloor"))
        self.assertFalse(is_bridge("Hollande/Batiments_ville", "TypeWarrior/MaisonHollande_01"))
        self.assertFalse(is_bridge("COC/Normandie/Ponts", "TypeWarrior/Bridge_Dest"))  # wrecks: no deck, no floor
        self.assertFalse(is_bridge("Allemagne/Ponts", "TypeWarrior/Pont_Allemagne_03_Detruit"))
        self.assertFalse(is_bridge("Props", "TypeWarrior/ponton_01"))  # jetties
        self.assertFalse(is_bridge("LB/SnapBox", "Snap Box Pont"))
        dutch = ["TypeWarrior/Pont_Hollande_01_Arnhem", "TypeWarrior/Pont_Hollande_03_Petit_TangeantFloor"]
        self.assertEqual(bridge_type(dutch, {0: 1, 1: 4}, {n: desc("Hollande/Batiments_ville") for n in dutch}),
                         dutch[1])

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

        def mapinfo(g):
            return {member("Blitz"): navmod.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
                net.to_bytes(), g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})}.get
        read = mapinfo(banks())
        new, notes = apply_spans(read, "Blitz", [(11600.0, 2000.0, 16000.0, 2000.0)])
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        self.assertEqual(bufs[0], net.to_bytes())  # no old bridge: the road network is left alone
        graph = navmod.Graph.read(bufs[2])
        # the deck is a chain of circles narrower than the bridge floor, in the main graph: 4,400 of deck every 640,
        # and the two banks. No owner circle over the crossing, so no ground beside the deck to step onto
        self.assertEqual((len(graph.circles) - 1, len(graph.subs)), (8 + 2, 0))
        self.assertEqual(sorted({c[2] for c in graph.circles[:-1]}), [640.0, 6400.0])
        self.assertEqual(graph.parts(), [10])
        self.assertTrue(graph.walkable(13800.0, 2000.0))
        for across in (2700.0, 3300.0):  # 700 and 1,300 off the deck's line: the river, as before the mod
            self.assertFalse(graph.walkable(13800.0, across))
        self.assertEqual(notes[0], "infantry: 1 bridge(s) opened, units kept to the deck (8 circle(s) 5 m wide along "
                                   "it, narrower than the floor they stand on)")
        # a deck whose far end reaches no ground units use would be cut off (the game crashes on an order onto it)
        new, notes = apply_spans(read, "Blitz", [(26000.0, 2000.0, 60000.0, 2000.0)])  # E's land, then nothing
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        self.assertEqual(bufs[2], banks().to_bytes())
        self.assertIn("vehicles can't use the bridge at (43000, 2000): past its east end, no ground they already use "
                      "lies within 62 m along the road", notes[-1])
        read = mapinfo(row())
        with self.assertRaisesRegex(BridgeError, "would cut ground off from the rest of the map"):
            apply_spans(read, "Blitz", [], [(10000.0, 2000.0, 1000.0)])  # B shrinks off A: never an island
        new, notes = apply_spans(read, "Blitz", [], [(10800.0, 2000.0, 400.0)])  # where an old one stood
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        for k in (1, 2):
            self.assertEqual([c[2] > 0 for c in navmod.Graph.read(bufs[k]).circles[:-1]], [True, True, False])
        roads = RoadNet.read(bufs[0])
        self.assertEqual((roads.points, roads.links), ([(0.0, 2000.0), (6000.0, 2000.0)], [(0, 1, 600)]))
        self.assertIn("road network: 1 link(s) taken off the old bridges", notes)


class LocalMovement(unittest.TestCase):
    def test_a_bridges_own_local_movement_isnt_split(self):
        # most shipped bridges have a local graph lining the deck: closing the old deck's middle would leave its two
        # banks' pieces apart, ground units can't get between (a crash, as with the main graph)
        from rusemod.cover import member
        g = banks()
        g.subs = [chain([(8000.0 + 2000.0 * k, 20000.0, 1280.0) for k in range(5)])]
        net = RoadNet([(0.0, 2000.0), (6000.0, 2000.0)], [(0, 1, 600)])
        net.tree = build_tree(net.points, net.links)
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})
        read = {member("Blitz"): win}.get
        with self.assertRaisesRegex(BridgeError, "local movement"):
            apply_spans(read, "Blitz", [(11600.0, 2000.0, 16000.0, 2000.0)], [(12000.0, 20000.0, 1600.0)])
        new, _notes = apply_spans(read, "Blitz", [(11600.0, 2000.0, 16000.0, 2000.0)])  # nothing closed: fine
        self.assertIn(member("Blitz"), new)

    def test_a_replaced_bridges_owner_takes_the_new_deck(self):
        # a road over a bridge of the map's: its deck over the water is closed (the old bridge sunk), but its owner
        # circle stays and its local movement takes the new deck: units cross the old way, kept to the new deck
        from test_nav import bridged, river
        from rusemod.cover import member
        net = RoadNet([(0.0, 2000.0), (6000.0, 2000.0)], [(0, 1, 600)])
        net.tree = build_tree(net.points, net.links)
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), bridged().to_bytes(), bridged().to_bytes(), b"cover")) + b"tail", {})
        read = {member("Blitz"): win}.get
        new, notes = apply_spans(read, "Blitz", [(10200.0, 2600.0, 17000.0, 2600.0)], [(13000.0, 2000.0, 1600.0)],
                                 water=river)
        g = nav.Graph.read(sdb_buffers(new[member("Blitz")])[2])
        self.assertEqual(g.circles, bridged().circles)  # the owner stays (its middle is in the closed ground)
        self.assertEqual((g.parts(), g.subs[0].parts()), ([3], [14]))  # its local map: the banks and the new deck
        self.assertTrue(all(g.walkable(float(x), 2600.0) for x in range(11500, 15600, 100)))
        self.assertFalse(any(g.walkable(float(x), y) for x in range(11500, 15600, 100) for y in (1300.0, 1800.0, 3400.0)))
        self.assertIn("vehicles: 1 bridge(s) opened, units kept to the deck: 1 in the local movement already there "
                      "(an old bridge's or a town's)", notes)

    def test_a_new_deck_opens_no_ground_beside_itself(self):
        # the whole of what keeps units on a new bridge: every place the build opens is over the deck they stand on
        # (the owner's in-game tests, 2026-09-30 and 2026-10-01: wider circles put units in the river beside it)
        from rusemod.cover import member
        g = banks()
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            b"roads", g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})
        span = (11600.0, 2000.0, 16000.0, 2000.0)
        new, _notes = apply_spans({member("Blitz"): win}.get, "Blitz", [span])
        after, before = nav.Graph.read(sdb_buffers(new[member("Blitz")])[2]), banks()
        for x in range(11600, 16100, 100):
            self.assertTrue(after.walkable(float(x), 2000.0), x)  # along the deck, end to end
            for across in (2000.0 + 663.0 + 100, 2000.0 - 663.0 - 100, 4000.0, 300.0):
                opened = after.walkable(float(x), across) and not before.walkable(float(x), across)
                self.assertFalse(opened, (x, across))  # past the floor's width: nothing the map didn't already have


def sdb_buffers(win):
    from ruse_mod_engine import sdb
    return sdb.split_mapinfo(win)[1]


class Opening(unittest.TestCase):
    """A deck opened to units (Graph.open): an owner circle over it at circle number NX (0 here: these graphs have no
    local maps), its local map the deck's circles and copies of the banks it overlaps, approaches in the main graph."""

    def test_a_deck_joined_to_both_banks(self):
        g = banks()
        counts = g.open([(11600.0, 2000.0, 16000.0, 2000.0)], radius=1280.0)  # from W's edge to E's
        self.assertEqual((counts["added"], counts["approach"], counts["closed"], counts["owners"]),
                         (1, 0, [], [(0, 0, 2880.0, 10)]))
        self.assertEqual(g.circles[0][:3], (13760.0, 1920.0, 2880.0))  # the owner, the deck's middle on the grid
        self.assertEqual([c[:3] for c in g.circles[1:-1]], [c[:3] for c in banks().circles[:-1]])  # W, E: 1 and 2
        local = g.subs[0]
        self.assertEqual([round(c[0]) for c in local.circles[2:-1]], [11600, 12229, 12857, 13486, 14114, 14743,
                                                                       15371, 16000])
        self.assertEqual(local.circles[:2], [(5000.0, 2000.0, 6400.0, 0, 0), (22000.0, 2000.0, 6400.0, 1, 0)])
        self.assertEqual(g.links[1], (1, 2, 13500.0, 20000.0))  # the old one, its circles numbered again
        pairs = {(a, b) for a, b, _x, _y in g.links}
        self.assertEqual(pairs, {(0, 1), (0, 2), (1, 2)})  # the owner to each bank
        self.assertEqual((g.parts(), local.parts()), ([3], [10]))  # one piece each: the deck joins both banks
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        self.assertTrue(all(g.walkable(x, 2000.0) for x in range(11000, 16700, 100)))  # all the way over
        self.assertFalse(any(g.walkable(x, y) for x in range(11500, 15600, 100) for y in (1300.0, 2700.0)))
        self.assertEqual(sorted(i for leaf in (nav._tree_read(g.points)[3], nav._tree_read(g.points)[4])
                                for i in leaf[1]), list(range(3)))

    def test_the_index_must_widen_to_find_a_deck(self):
        g = banks()
        g.open([(11600.0, 2000.0, 16000.0, 2000.0)], radius=1280.0)
        self.assertEqual(g.find(13800.0, 2000.0), 0)  # the deck's middle: in the owner
        listed = nav._index_add(nav._index_renumber(banks().points, lambda i: i + 1), {2: [0]})
        stale = dataclasses.replace(g, points=listed)
        self.assertIsNone(stale.find(13800.0, 2000.0))  # listed, but the walk never goes between the old edges
        self.assertEqual(stale.find(5000.0, 2000.0), 1)

    def test_approaches_along_the_road(self):
        g = banks()
        counts = g.open([(12400.0, 2000.0, 14600.0, 2000.0)], radius=800.0, roads=[[(0.0, 2000.0), (30000.0, 2000.0)]])
        self.assertEqual((counts["approach"], counts["longest"], counts["closed"]), (2, 600.0, []))
        self.assertEqual(sorted(round(c[0]) for c in g.circles[3:-1]), [11800, 15200])  # in the main graph
        # the owner: the least that holds the deck and overlaps both approaches by STEP (1,280 meets the east one by
        # 318), their middles outside it
        self.assertEqual(g.circles[0][2], 1600.0)
        self.assertEqual(g.parts(), [len(g.circles) - 1])
        self.assertTrue(all(g.walkable(x, 2000.0) for x in range(11000, 16700, 100)))

    def test_a_deck_that_cant_reach_ground_stays_closed(self):
        g = banks()
        counts = g.open([(26000.0, 2000.0, 60000.0, 2000.0), (80000.0, 2000.0, 90000.0, 2000.0)], radius=1280.0)
        self.assertEqual(counts, {"added": 0, "linked": 0, "approach": 0, "longest": 0.0, "owners": [], "inside": [],
                                  "left_out": 0, "under": 0, "closed": [(0, [1]), (1, [0, 1])], "crowded": [],
                                  "stopped": {}})
        self.assertEqual(g.to_bytes(), banks().to_bytes())  # nothing written: an island would crash the game

    def test_each_end_joins_on_its_own_side(self):
        g = banks()  # the deck's far end reaches E; its near end stops short of W: that end gets its own approach
        counts = g.open([(13000.0, 2000.0, 16800.0, 2000.0)], radius=1280.0)
        self.assertEqual((counts["approach"], counts["closed"]), (1, []))
        self.assertIn((1, 3), {(a, b) for a, b, _x, _y in g.links})  # the approach circle, to W
        self.assertIn((0, 3), {(a, b) for a, b, _x, _y in g.links})  # and to the owner

    def test_a_hairpin_road_leads_off_the_deck_not_back_over_it(self):
        g = nav.Graph(box=(0, 0, 32000.0), circles=[(-6000.0, 200.0, 6400.0, 0, 0), (5500.0, 7000.0, 3200.0, 1, 0),
                                                    (0.0, 0.0, 0.0, 2, 0)],
                      links=[(0, 1, -2000.0, 4000.0)], lists=[0, 0], crossings=b"",
                      points=nav._tree_write(["leaf", [0, 1]]), head_rest=bytes(nav.HEADER - 20))
        road = [(-3000.0, 0.0), (10300.0, 0.0), (7300.0, 4000.0)]  # under the deck, then back north-west past its end
        counts = g.open([(0.0, 200.0, 10000.0, 200.0)], radius=1280.0, roads=[road])
        self.assertEqual((counts["closed"], counts["crowded"]), ([], []))
        # the road comes back into the owner: those approach circles are in its local map only
        approach = [c for c in g.subs[0].circles[:-1] if c[2] == 1280.0]
        self.assertTrue(approach)
        self.assertFalse([c for c in approach if c[0] < 9000 and abs(c[1] - 200) < 1000])  # not back over the deck
        self.assertIn((0, 2), {(a, b) for a, b, _x, _y in g.links})  # E reached, through the owner
        self.assertEqual(g.subs[0].parts(), [len(g.subs[0].circles) - 1])

    def test_an_approach_keeps_out_of_blocked_ground(self):
        g = banks()
        counts = g.open([(13300.0, 2000.0, 15000.0, 2000.0)], radius=1280.0, roads=[[(0.0, 2000.0), (30000.0, 2000.0)]],
                        avoid=lambda x, y, r: ((x - 10900) ** 2 + (y - 2000) ** 2) ** 0.5 < 2000 + r)
        self.assertEqual((counts["added"], counts["closed"]), (0, [(0, [0])]))  # its west approach would cross the block
        x, y, walked, why = counts["stopped"][(0, 0)]  # and the build can say where the road meets it
        self.assertTrue(x < 13300 and walked > 0 and why.startswith("ground closed to units"))

    def test_an_approach_squeezes_past_a_building_with_smaller_circles(self):
        g = banks()  # a building's hole beside the road, 1,200 off its line: a full circle would reach it (480 clear)
        counts = g.open([(13300.0, 2000.0, 15000.0, 2000.0)], radius=1280.0, roads=[[(0.0, 2000.0), (30000.0, 2000.0)]],
                        avoid=lambda x, y, r: ((x - 11500) ** 2 + (y - 3200) ** 2) ** 0.5 < 480 + r)
        self.assertEqual((counts["closed"], counts["crowded"]), ([], []))
        self.assertIn(640.0, {c[2] for c in g.circles[:-1]})  # smaller circles went in where the full one wouldn't fit
        self.assertEqual(g.parts(), [len(g.circles) - 1])
        self.assertFalse(g.walkable(11500.0, 3200.0))  # the building's middle stays off limits

    def test_the_longest_approach_is_of_a_bridge_opened(self):
        g = banks()
        counts = g.open([(13500.0, 2000.0, 13500.0, 60000.0), (12400.0, 2000.0, 14600.0, 2000.0)], radius=800.0,
                        roads=[[(13500.0, 2000.0), (13500.0, -3000.0), (8000.0, -3000.0)], [(0.0, 2000.0), (30000.0, 2000.0)]])
        self.assertEqual((counts["approach"], counts["longest"], counts["closed"]), (2, 600.0, [(0, [1])]))

    def test_the_way_out_follows_the_road(self):
        line = [(-5000.0, 0.0), (0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0)]
        got = list(nav._walk_out((0.0, 0.0), (1.0, 0.0), [line], 500.0, 3000.0))
        self.assertEqual([(w, round(x), round(y)) for w, (x, y) in got],
                         [(500.0, 500, 0), (1000.0, 1000, 0), (1500.0, 1000, 500), (2000.0, 1000, 1000),
                          (2500.0, 1000, 1500), (3000.0, 1000, 2000)])  # round the bend, then straight on
        back = list(nav._walk_out((0.0, 0.0), (-1.0, 0.0), [line], 500.0, 1000.0))
        self.assertEqual([(round(x), round(y)) for _w, (x, y) in back], [(-500, 0), (-1000, 0)])
        far = list(nav._walk_out((0.0, 0.0), (0.0, 1.0), [[(0.0, 9000.0), (5000.0, 9000.0)]], 500.0, 1000.0))
        self.assertEqual([(round(x), round(y)) for _w, (x, y) in far], [(0, 500), (0, 1000)])  # no road near: straight

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
