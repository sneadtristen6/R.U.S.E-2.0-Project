"""Bridge floors (rusemod.floors): a new bridge gets the floor of a shipped bridge of its kind, on its own banks, in
the objects-only tree, rebuilt as one subtree whose leaves list every triangle reaching into them. On a made-up file
(test_kdt's), with a made-up shipped floor like Pont_Metallique_02's: four sections along the deck."""
import math
import unittest

from test_kdt import make_valid_kdt
from rusemod import floors, nav
from rusemod.floors import WIDEN, Deck, NoFloor, build_tree, carry, floors_for, found_at, rebuild, triangles
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

    def test_the_file_keeps_the_games_own_rules(self):
        # what every shipped floor file does (all 29 maps): each triangle faces up by the order of its points, each
        # point's normal is the one word UP (the game turns a man to the normal of what he stands on: with normals
        # worked out from the triangles, and aprons whose points ran the other way round, men lay sideways on the
        # decks and fell through one side's floor; the owner's test, 2026-10-01), and no triangle is a sliver
        import struct
        from rusemod.kdt import inflate
        deck = Deck.of(200000.0, 150000.0, 212000.0, 150000.0)
        flipped = [(a, c, b) for a, b, c in strip(deck, 500.0, 900.0)]           # the points the other way round
        sliver = [((205000.0, 151000.0, 700.0), (205000.5, 151000.0, 700.0), (205000.0, 151000.5, 700.0))]
        k = Kdt(rebuild(Kdt(make_valid_kdt()), strip(SHIPPED, FLAT, FLAT) + flipped + sliver))
        self.assertEqual(k.triangle_count, 16)                                    # the sliver is no triangle: left out
        pos, idx = k.positions(0), k.indices(0)
        for i in range(0, len(idx), 3):
            a, b, c = (pos[v] for v in idx[i:i + 3])
            self.assertGreater((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]), 0, i // 3)
        words = struct.unpack(f"<{len(pos)}I", inflate(k.subtrees[0].normals))
        self.assertEqual(set(words), {floors.UP})
        self.assertEqual(floors.UP, 0x7FFDFFF5)
        with self.assertRaises(floors.FloorError):
            rebuild(Kdt(make_valid_kdt()), sliver)

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
    def test_a_new_bridge_with_no_floor_to_copy_is_refused(self):
        """Movement opens along every new deck, so a deck with no floor would put units on the riverbed: refused,
        naming which of the new bridges it is."""
        elsewhere = Deck.of(0.0, 400000.0, 5000.0, 400000.0)  # a shipped bridge of the kind, but with no floor
        new = Deck.of(300000.0, 0.0, 310000.0, 0.0)
        fine = Deck.of(200000.0, 150000.0, 212000.0, 150000.0)  # its kind's shipped bridge has a floor to copy
        with self.assertRaises(NoFloor) as got:
            floors_for(Kdt(base_file()), lambda x, y: FLAT, [(fine, [SHIPPED]), (new, [elsewhere])], [])
        self.assertEqual(got.exception.missing, [1])
        self.assertIn("no floor to copy", str(got.exception))
        with self.assertRaises(NoFloor) as got:  # off the ground mesh: no banks to sit on
            floors_for(Kdt(base_file()), lambda x, y: None, [(new, [SHIPPED])], [])
        self.assertEqual(got.exception.missing, [0])


def metal(deck: Deck, z: float) -> list:
    """A floor like the shipped metal bridges': a band 650 either side of the deck's line, and beside it two flat
    aprons as long as the band, from 620 out to 17,000, 30 above it (24 triangles: 8 each)."""
    out = []
    ts = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for s0, s1, lift in ((-650.0, 650.0, 0.0), (620.0, 17000.0, 30.0), (-17000.0, -620.0, 30.0)):
        for a, b in zip(ts, ts[1:]):
            p = [(*deck.world(a, s0), z + lift), (*deck.world(a, s1), z + lift), (*deck.world(b, s0), z + lift),
                 (*deck.world(b, s1), z + lift)]
            out += [(p[0], p[1], p[2]), (p[1], p[3], p[2])]
    return out


def top(tris, x: float, y: float):
    """The highest floor over (x, y): what a unit there stands on (None: no floor, so the ground under it)."""
    best = None
    for a, b, c in tris:
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if den == 0:
            continue
        l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den
        l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
        l3 = 1.0 - l1 - l2
        if min(l1, l2, l3) >= -1e-9:
            z = l1 * a[2] + l2 * b[2] + l3 * c[2]
            best = z if best is None else max(best, z)
    return best


class Aprons(unittest.TestCase):
    """A squad's five men stand on an arc 2,828 wide, each on the floor under his own feet: beside a deck whose
    movement is 640 wide two of them are 2,054 from its line. With the band alone they stood on the riverbed (the
    owner's test, 2026-10-01: "they are in water not like vanilla ruse ... vanilla ruse they float")."""
    NEW = Deck.of(200000.0, 150000.0, 212000.0, 150000.0)   # 12,000 long, along x; its banks 1,500 in from each end
    BANK = 2000.0

    @staticmethod
    def river(x, y):
        return 201500.0 < x < 210500.0

    def ground(self, x, y):
        return 0.0 if self.river(x, y) else self.BANK   # the riverbed 2,000 below the banks

    def band(self):
        return carry(strip(SHIPPED, FLAT, FLAT), SHIPPED, (FLAT, FLAT), self.NEW, (self.BANK, self.BANK))

    def fair(self, tris, water, ground=None):
        """Every point of the floor `tris` is over water, or on dry ground no more than RISE below it (the top of a
        steep bank at the water's edge: here the banks stand 50 below the floor)."""
        ground = ground or self.ground
        return all(water(x, y) or z - ground(x, y) <= floors.RISE for t in tris for x, y, z in t)

    def test_beside_the_band_over_the_water_at_its_height(self):
        band = self.band()
        beside = floors.apron(band, self.NEW, (self.BANK, self.BANK), self.river, self.ground)
        self.assertEqual(len(beside), 16)  # one piece per section of the band either side, where there's water
        pts = [p for t in beside for p in t]
        self.assertTrue(self.fair(beside, self.river))
        along = [x for x, _y, _z in pts]                                   # to the water's edge under the steep banks
        self.assertTrue(201500.0 - floors.CELL < min(along) <= 201500.0 and 210500.0 <= max(along) < 210500.0
                        + floors.CELL, (min(along), max(along)))           # and no farther over them than a cell
        self.assertTrue(all(abs(z - (self.BANK + 50.0)) < 1e-6 for _x, _y, z in pts))  # in the band's plane
        across = [abs(self.NEW.local(x, y)[1]) for x, y, _z in pts]
        self.assertAlmostEqual(max(across), floors.APRON)
        self.assertAlmostEqual(min(across), 1200.0 * WIDEN - floors.LAP)  # lapping over the band's edge
        both = band + beside
        for x in (201510.0, 203000.0, 206000.0, 209000.0, 210490.0):       # (203000, 206000...: where pieces meet)
            for s in (0.0, 640.0, 640.0 + 1414.0, 640.0 + 2480.0, -640.0 - 1414.0, -3190.0):
                self.assertAlmostEqual(top(both, x, 150000.0 + s), self.BANK + 50.0, msg=(x, s))
        self.assertIsNone(top(both, 206000.0, 150000.0 + 3300.0))          # past the apron: the river
        self.assertIsNone(top(both, 201000.0, 150000.0 + 2054.0))          # beside the deck on the bank: the ground
        self.assertIsNone(top(band, 206000.0, 150000.0 + 2054.0))          # (the band alone: the riverbed)

    def test_a_bank_that_cuts_in_and_ground_near_its_height(self):
        def water(x, y):  # the far bank comes in to 2,500 from the line along the deck's first third
            return self.river(x, y) and (x >= 204000.0 or y < 152500.0)
        beside = floors.apron(self.band(), self.NEW, (self.BANK, self.BANK), water, self.ground)
        pts = [p for t in beside for p in t]
        self.assertTrue(all(water(x, y) or not self.river(x, y) for x, y, _z in pts))  # (the bank that cuts in is
        near = [self.NEW.local(x, y)[1] for x, y, _z in pts if x < 204000.0 - 1.0]
        self.assertLessEqual(max(near), 2500.0)
        self.assertAlmostEqual(min(near), -floors.APRON)                   # the other side still reaches all the way
        self.assertAlmostEqual(max(self.NEW.local(x, y)[1] for x, y, _z in pts if x > 204200.0), floors.APRON)

        # a bank at an angle to the deck: dry ground beside the deck, water farther out (the owner's D-Day decks:
        # stopping at the first dry cell left men 1,400 to 2,000 out over deep water with no floor)
        def spit(x, y):
            return self.river(x, y) and not (x < 204000.0 and 151500.0 < y < 152100.0)
        beside = floors.apron(self.band(), self.NEW, (self.BANK, self.BANK), spit, self.ground)
        self.assertTrue(all(spit(x, y) or not self.river(x, y) for t in beside for x, y, _z in t))  # (a low spit)
        self.assertIsNone(top(beside, 203000.0, 151800.0))                 # the spit: the ground
        self.assertAlmostEqual(top(beside, 203000.0, 152600.0), self.BANK + 50.0)  # the water past it: floor
        self.assertAlmostEqual(top(beside, 205000.0, 151800.0), self.BANK + 50.0)

        # two stretches that only partly meet where two pieces join (at a line of the band): no crack between them
        def steps(x, y):
            return self.river(x, y) and (y < 152500.0 if x < 203000.0 else y > 152100.0 or y < 150000.0)
        beside = floors.apron(self.band(), self.NEW, (self.BANK, self.BANK), steps, self.ground)
        self.assertTrue(all(steps(x, y) or not self.river(x, y) for t in beside for x, y, _z in t))
        for x in (202960.0, 203000.0, 203040.0):
            self.assertAlmostEqual(top(beside, x, 152300.0), self.BANK + 50.0, msg=x)

        def shoal(x, y):  # water everywhere, but a shoal 100 below the deck on one side: no floor over it
            return self.BANK if y > 151000.0 else self.ground(x, y)
        beside = floors.apron(self.band(), self.NEW, (self.BANK, self.BANK), self.river, shoal)
        self.assertTrue(all(self.NEW.local(x, y)[1] < 0 for t in beside for x, y, _z in t))
        self.assertEqual(floors.apron(self.band(), self.NEW, (self.BANK, self.BANK), lambda x, y: False, self.ground),
                         [])                                               # no water: the band alone

    def test_a_build_gives_new_bridges_one_and_takes_a_sunk_bridges(self):
        k = Kdt(rebuild(Kdt(make_valid_kdt()), metal(SHIPPED, self.BANK)))
        data, notes = floors_for(k, self.ground, [(self.NEW, [SHIPPED])], [], self.river)
        tris = triangles(Kdt(data))
        mine = [t for t in tris if all(abs(self.NEW.local(p[0], p[1])[0]) <= 1.2 for p in t)]
        self.assertEqual(len(tris) - len(mine), 24)                        # the shipped bridge keeps all of its own
        self.assertEqual(len([t for t in mine if floors.on_deck(t, self.NEW)
                              and max(abs(self.NEW.local(p[0], p[1])[1]) for p in t) < 1100]), 8)  # its band: not
        reach = max(abs(self.NEW.local(p[0], p[1])[1]) for t in mine for p in t)   # the shipped aprons, 17,000 wide
        self.assertAlmostEqual(reach, floors.APRON, delta=70)              # (the file's grid)
        for s in (0.0, 2054.0, -2054.0, 3000.0):
            self.assertAlmostEqual(top(tris, 206000.0, 150000.0 + s), self.BANK, delta=5, msg=s)
        self.assertEqual(notes, ["floors: 1 bridge(s) given one"])
        _data, notes = floors_for(k, self.ground, [(self.NEW, [SHIPPED])], [], lambda x, y: False)
        self.assertIn("little or no water beside the deck", notes[1])
        # a sunk bridge's aprons go with its band (they'd hold units up over the river where no bridge is)
        other = Deck.of(0.0, 300000.0, 9000.0, 300000.0)
        two = Kdt(rebuild(Kdt(make_valid_kdt()), metal(SHIPPED, FLAT) + metal(other, FLAT)))
        data, notes = floors_for(two, self.ground, [], [SHIPPED])
        self.assertEqual(notes, ["floors: 0 bridge(s) given one, 24 triangle(s) of sunk bridges taken out"])
        left = triangles(Kdt(data))
        self.assertEqual(len(left), 24)
        self.assertTrue(all(abs(other.local(p[0], p[1])[0]) <= 1.2 for t in left for p in t))


if __name__ == "__main__":
    unittest.main()
