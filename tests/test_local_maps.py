"""Graph.add_local_maps: a town's own local map, laid out as the shipped ones are (findings ledger F-95)."""
import math
import unittest

from rusemod import bigmap
from rusemod import nav

M = 260.0


def blank(side_m: float = 2000.0) -> nav.Graph:
    data, _n, _l = bigmap.lattice((side_m * M, side_m * M))
    return nav.Graph.read(data)


def town(cx: float, cy: float):
    """A small town (map units): two rows of houses along a street, a yard closed to vehicles."""
    houses, street = [], []
    for k in range(-6, 7):
        x = cx + k * 12 * M
        houses += [(x, cy + 14 * M, 5 * M), (x, cy - 14 * M, 5 * M)]
        street.append((x, cy, 6.5 * M))
    return houses, street


class LocalMaps(unittest.TestCase):
    def test_a_town_gets_its_own_local_map(self):
        g = blank()
        cx, cy = 1000 * M, 1000 * M
        houses, street = town(cx, cy)
        circles_before = len(g.circles) - 1
        got = g.add_local_maps([(cx, cy, 150 * M, houses, street)])
        self.assertEqual(len(g.subs), 1)
        owner = g.circles[0]
        self.assertAlmostEqual(owner[0], cx, delta=nav.STEP)
        self.assertGreaterEqual(owner[2], 150 * M)
        k, r, n_local, n_links = got["owners"][0]
        self.assertEqual(k, 0)
        self.assertGreater(n_links, 2)
        self.assertGreater(n_local, 5)
        # no other main circle's middle in the owner, the local map one piece, the main graph one piece
        for i, c in enumerate(g.circles[1:-1], start=1):
            self.assertFalse(c[2] > 0 and math.hypot(c[0] - owner[0], c[1] - owner[1]) < owner[2], i)
        self.assertEqual(len(g.subs[0].parts()), 1)
        self.assertEqual(len(g.parts()), 1)
        # inside: a house is closed, the street open; outside the owner the main graph decides as before
        hx, hy, _hr = houses[0]
        self.assertFalse(g.walkable(hx, hy))
        self.assertTrue(g.walkable(cx, cy))
        self.assertTrue(g.walkable(cx + 400 * M, cy + 400 * M))
        # every owner link meets the local map's ground
        for a, b, px, py in g.links:
            if a == 0:
                self.assertIsNotNone(g.subs[0].find(px, py))
        # written and read back the same
        back = nav.Graph.read(g.to_bytes())
        self.assertEqual(back.to_bytes(), g.to_bytes())
        self.assertEqual(len(back.subs), 1)
        self.assertGreaterEqual(len(g.circles) - 1, circles_before - got["emptied"])

    def test_two_towns_largest_first(self):
        g = blank(3000.0)
        a, b = (800 * M, 800 * M), (2200 * M, 2100 * M)
        got = g.add_local_maps([(a[0], a[1], 120 * M, *town(*a)), (b[0], b[1], 200 * M, *town(*b))])
        self.assertEqual(len(g.subs), 2)
        self.assertGreaterEqual(g.circles[0][2], g.circles[1][2])        # owners largest first
        self.assertAlmostEqual(g.circles[0][0], b[0], delta=nav.STEP)
        self.assertEqual([o[0] for o in got["owners"]], [0, 1])
        self.assertFalse(g.walkable(*town(*a)[0][0][:2]))
        self.assertFalse(g.walkable(*town(*b)[0][0][:2]))
        self.assertEqual(len(g.parts()), 1)

    def test_a_river_through_the_town_with_its_bridge(self):
        """A river across the town's disc: with its bridge laid in the local map the town is one piece, both banks
        and the deck walkable; without it, the far bank is cut off (the local map kept in one piece)."""
        cx, cy = 1000 * M, 1000 * M
        river = [(cx + k * 6 * M, cy - 40 * M, 9 * M) for k in range(-30, 31)]   # 18 m wide, the town's width over
        deck = (cx, cy - 40 * M - 20 * M, cx, cy - 40 * M + 20 * M)               # 40 m, bank to bank
        near_bank, far_bank = (cx + 60 * M, cy), (cx + 60 * M, cy - 90 * M)
        g = blank()
        g.add_local_maps([(cx, cy, 150 * M, river, [], [deck])])
        self.assertEqual(len(g.subs[0].parts()), 1)
        self.assertTrue(g.walkable(*near_bank))
        self.assertTrue(g.walkable(*far_bank))
        self.assertTrue(g.walkable(cx, cy - 40 * M))                       # on the deck over the water
        self.assertFalse(g.walkable(cx + 30 * M, cy - 40 * M))             # the water beside it
        bare = blank()
        bare.add_local_maps([(cx, cy, 150 * M, river, [])])
        self.assertEqual(sum(bare.walkable(*p) for p in (near_bank, far_bank)), 1)   # one bank only, no bridge

    def test_a_way_in_along_a_narrow_road(self):
        """A town whose own ground reaches its rim only along one road (woods closed round it): the road still gets a
        way in from the main circle it runs into, where it crosses the overlap and not only at the overlap's middle
        (nav._meeting_on), so the road out of town and the town are one piece."""
        cx, cy = 1000 * M, 1000 * M
        wood = [(cx + dx * M, cy + dy * M, 40 * M) for dx in range(-180, 181, 30) for dy in range(-180, 181, 30)
                if 90 <= math.hypot(dx, dy) < 200]   # the town a clearing in the wood
        ang = math.radians(33)   # off any lattice line
        road = [(cx + math.cos(ang) * k * 5 * M, cy + math.sin(ang) * k * 5 * M, 6.5 * M) for k in range(0, 40)]
        g = blank()
        got = g.add_local_maps([(cx, cy, 150 * M, wood, road)])
        _k, _r, _n, n_links = got["owners"][0]
        self.assertGreaterEqual(n_links, 1)
        for a, _b, px, py in g.links:
            if a == 0:
                self.assertIsNotNone(g.subs[0].find(px, py))
        self.assertTrue(g.walkable(cx + math.cos(ang) * 100 * M, cy + math.sin(ang) * 100 * M))   # the road in town
        self.assertFalse(g.walkable(cx - 120 * M, cy))                                                 # the wood
        self.assertEqual(len(g.parts()), 1)
        # every main circle whose overlap with the owner holds the town's ground somewhere (looked for across it,
        # STEP apart, inside both by half a STEP) is linked to it, not only those holding it at the overlap's middle
        ox, oy, orad = g.circles[0][:3]
        linked = {b for a, b, _x, _y in g.links if a == 0} | {a for a, b, _x, _y in g.links if b == 0}
        missed = []
        for d, (qx, qy, qr, _l, _c) in enumerate(g.circles[:-1]):
            dist = math.hypot(qx - ox, qy - oy)
            if d == 0 or qr <= 0 or orad + qr - dist < nav.STEP:
                continue
            ux, uy = (qx - ox) / dist, (qy - oy) / dist
            tm = (dist - qr + orad) / 2
            pts = [(ox + ux * (tm + dt) - uy * k * nav.STEP, oy + uy * (tm + dt) + ux * k * nav.STEP)
                   for k in range(-60, 61) for dt in (0.0, -nav.STEP / 2, nav.STEP / 2)]
            pts = [(x, y) for x, y in pts if math.hypot(x - ox, y - oy) <= orad - nav.STEP / 2
                   and math.hypot(x - qx, y - qy) <= qr - nav.STEP / 2]
            if any(g.subs[0].find(x, y) is not None for x, y in pts) and d not in linked:
                missed.append(d)
        self.assertEqual(missed, [])

    def test_a_way_in_off_the_overlaps_middle(self):
        """nav._meeting_on: where the town's ground crosses the owner's overlap with a main circle away from the
        overlap's middle (a road leaving the rim aslant), the way in is that point, inside both circles; where the
        overlap holds no ground, none."""
        box = blank().box
        p = (1000 * M, 1000 * M, 150 * M)                        # the owner
        q = (1000 * M + 150 * M + 40 * M - 2 * nav.STEP, 1000 * M, 40 * M)   # a main circle 2 STEP into its rim
        road = nav._local_graph(box, [(1145 * M, 1008 * M, 5 * M)])          # the town's ground: 8 m off the line
        mid = nav._meeting(p, q)
        self.assertIsNone(road.find(*mid))
        got = nav._meeting_on(road, p, q)
        self.assertIsNotNone(got)
        self.assertIsNotNone(road.find(*got))
        for cx, cy, cr in (p, q):
            self.assertLessEqual(math.hypot(got[0] - cx, got[1] - cy), cr - nav.STEP / 2 + 1e-6)
        far = nav._local_graph(box, [(1100 * M, 1100 * M, 5 * M)])           # ground nowhere near the overlap
        self.assertIsNone(nav._meeting_on(far, p, q))

    def test_refused_off_the_map_or_overlapping(self):
        g = blank()
        with self.assertRaises(nav.NavError):
            g.add_local_maps([(50 * M, 1000 * M, 150 * M, [], [])])
        with self.assertRaises(nav.NavError):
            g.add_local_maps([(900 * M, 1000 * M, 150 * M, [], []), (1100 * M, 1000 * M, 150 * M, [], [])])

    def test_a_town_works_with_crossings_and_the_link_cap(self):
        from rusemod.roadnet import RoadNet
        g = blank()
        cx, cy = 1000 * M, 1000 * M
        g.add_local_maps([(cx, cy, 150 * M, *town(cx, cy))])
        self.assertLessEqual(nav.most_links(g.to_bytes()), nav.MAX_LINKS)
        self.assertGreaterEqual(g.cap_links(), 0)


if __name__ == "__main__":
    unittest.main()
