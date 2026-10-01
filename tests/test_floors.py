"""Bridge floors (rusemod.floors): a new bridge gets the floor of a shipped bridge of its kind, on its own banks, in
the objects-only tree, rebuilt as one subtree whose leaves list every triangle reaching into them. On a made-up file
(test_kdt's), with a made-up shipped floor like Pont_Metallique_02's: four sections along the deck."""
import math
import unittest

from test_kdt import make_valid_kdt
from rusemod import floors, nav
from rusemod.floors import WIDEN, Deck, build_tree, carry, floors_for, found_at, rebuild, triangles
from rusemod.kdt import Kdt


def strip(deck: Deck, z0: float, z1: float, lift: float = 50.0) -> list:
    """A floor like the shipped metal bridges': 4 sections along `deck`, 1,200 either side of its line, from z0 at
    the start to z1 at the end, `lift` above that line."""
    out = []
    ts = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for a, b in zip(ts, ts[1:]):
        za, zb = z0 + (z1 - z0) * (a + 1) / 2 + lift, z0 + (z1 - z0) * (b + 1) / 2 + lift
        p = [(*deck.world(a, -1200.0), za), (*deck.world(a, 1200.0), za), (*deck.world(b, -1200.0), zb),
             (*deck.world(b, 1200.0), zb)]
        out += [(p[0], p[1], p[2]), (p[1], p[3], p[2])]
    return out


SHIPPED = Deck.of(100000.0, 100000.0, 110000.0, 100000.0)   # 10,000 long, along x
FLAT = 1000.0


def base_file() -> bytes:
    """A one-subtree objects-only file holding the shipped bridge's floor on flat ground (z 1000)."""
    return rebuild(Kdt(make_valid_kdt()), strip(SHIPPED, FLAT, FLAT))


class Decks(unittest.TestCase):
    def test_along_and_across(self):
        d = Deck.of(0.0, 0.0, 0.0, 2000.0)  # along y
        self.assertEqual(d.local(*d.world(0.5, 300.0)), (0.5, 300.0))
        self.assertEqual(d.ends(), ((0.0, 0.0), (0.0, 2000.0)))
        with self.assertRaises(floors.FloorError):
            Deck.of(1.0, 1.0, 1.0, 1.0)

    def test_a_floor_carried_to_another_deck_and_its_banks(self):
        floor = strip(SHIPPED, FLAT, FLAT)
        new = Deck.of(300000.0, 200000.0, 300000.0, 212000.0)  # along y, 12,000 long, banks at 2000 and 2600
        got = carry(floor, SHIPPED, (FLAT, FLAT), new, (2000.0, 2600.0))
        pts = sorted({p for t in got for p in t}, key=lambda p: (round(new.local(p[0], p[1])[0], 3), p[0]))
        start, end = pts[0], pts[-1]
        self.assertAlmostEqual(new.local(start[0], start[1])[0], -1.0)
        self.assertAlmostEqual(start[2], 2050.0)   # the start bank's ground, and the floor's own 50 above it
        self.assertAlmostEqual(end[2], 2650.0)
        # wider than the one it came from (WIDEN): the movement on a new deck reaches 640 either side of its line,
        # and a unit at that edge with no floor under it drops to the riverbed (the game, 2026-10-01)
        across = [abs(new.local(p[0], p[1])[1]) for p in pts]
        self.assertAlmostEqual(max(across), 1200.0 * WIDEN)
        self.assertGreater(max(across), nav.DECK_RADIUS * 1.25)
        plain = carry(floor, SHIPPED, (FLAT, FLAT), new, (2000.0, 2600.0), widen=1.0)
        self.assertAlmostEqual(max(abs(new.local(p[0], p[1])[1]) for t in plain for p in t), 1200.0)


class Rebuilding(unittest.TestCase):
    def test_every_triangle_is_found_from_its_middle(self):
        k = Kdt(base_file())
        tris = triangles(k)
        self.assertEqual((len(k.subtrees), k.triangle_count, len(tris)), (1, 8, 8))
        for i, t in enumerate(tris):
            cx, cy = sum(p[0] for p in t) / 3, sum(p[1] for p in t) / 3
            self.assertIn(i, found_at(k, cx, cy))
        self.assertEqual(found_at(k, 400000.0, 400000.0), [])  # nothing there
        entries = k.main_entries()
        self.assertEqual([e[0] for e in entries], [0, 2, 0, 2, 0, 2, 5])  # the bounds, then the one subtree

    def test_the_old_points_keep_their_values(self):
        first = Kdt(base_file())
        again = Kdt(rebuild(Kdt(base_file()), triangles(first)))
        self.assertEqual(triangles(again), triangles(first))  # the bounds held them: nothing re-quantized

    def test_bounds_grow_to_hold_new_triangles(self):
        k = Kdt(base_file())
        far = [((600000.0, 600000.0, 200000.0), (601000.0, 600000.0, 200000.0), (600000.0, 601000.0, 200000.0))]
        k2 = Kdt(rebuild(k, triangles(k) + far))
        self.assertGreaterEqual(k2.bounds_max[0], 601000.0)
        self.assertGreaterEqual(k2.bounds_max[2], 200000.0)
        self.assertEqual(len(triangles(k2)), 9)

    def test_many_triangles_split_into_small_leaves(self):
        many = []
        for i in range(40):  # 40 little floors in a row: the tree splits them, every one still found
            d = Deck.of(50000.0 + i * 9000.0, 300000.0, 55000.0 + i * 9000.0, 300000.0)
            many += strip(d, 500.0 + i, 600.0 + i)
        k = Kdt(rebuild(Kdt(make_valid_kdt()), many))
        root = k.tree(0)
        from rusemod.kdt import leaves
        self.assertGreater(len(leaves(root)), 20)
        self.assertLessEqual(max(leaf.count for leaf, _lo, _hi in leaves(root)), floors.LEAF_MOST)
        for i, t in enumerate(triangles(k)):
            self.assertIn(i, found_at(k, sum(p[0] for p in t) / 3, sum(p[1] for p in t) / 3))
        _root, lists = build_tree([((0, 0, 0), (5, 5, 5))])
        self.assertEqual(lists, [[0]])


class ForABuild(unittest.TestCase):
    def test_a_new_bridge_gets_its_kinds_floor(self):
        k = Kdt(base_file())
        new = Deck.of(200000.0, 150000.0, 212000.0, 150000.0)
        data, notes = floors_for(k, lambda x, y: 2000.0 if x > 150000 else FLAT, [(new, [SHIPPED])], [])
        got = Kdt(data)
        tris = triangles(got)
        self.assertEqual(len(tris), 16)
        mine = [t for t in tris if floors.on_deck(t, new)]
        self.assertEqual(len(mine), 8)
        self.assertTrue(all(abs(p[2] - 2050.0) < 5 for t in mine for p in t))  # on its banks, 50 above
        self.assertTrue(found_at(got, 206000.0, 150000.0))
        self.assertEqual(notes, ["floors: 1 bridge(s) given one"])

    def test_a_sunk_bridge_loses_its_floor_and_nothing_to_copy_is_said(self):
        k = Kdt(base_file())
        data, notes = floors_for(k, lambda x, y: FLAT, [], [SHIPPED])
        self.assertEqual((data, notes), (b"", ["the sunk bridge's floor stays: it's the only one on this map"]))
        two = rebuild(Kdt(make_valid_kdt()), strip(SHIPPED, FLAT, FLAT) + strip(Deck.of(0.0, 300000.0, 9000.0,
                                                                                         300000.0), FLAT, FLAT))
        data, notes = floors_for(Kdt(two), lambda x, y: FLAT, [], [SHIPPED])
        self.assertEqual(notes, ["floors: 0 bridge(s) given one, 8 triangle(s) of sunk bridges taken out"])
        self.assertEqual(len(triangles(Kdt(data))), 8)
        elsewhere = Deck.of(0.0, 400000.0, 5000.0, 400000.0)
        data, notes = floors_for(Kdt(base_file()), lambda x, y: FLAT, [(Deck.of(300000.0, 0.0, 310000.0, 0.0),
                                                                         [elsewhere])], [])
        self.assertEqual(data, b"")
        self.assertIn("no floor to copy", notes[0])
        data, notes = floors_for(Kdt(base_file()), lambda x, y: None, [(Deck.of(300000.0, 0.0, 310000.0, 0.0),
                                                                          [SHIPPED])], [])
        self.assertIn("no floor to copy", notes[0])  # off the ground mesh: no banks to sit on


if __name__ == "__main__":
    unittest.main()
