"""Opened ground grown on a grid (rusemod.nav._grow, behind Graph.open_ground): the same circles, in the same order,
and the same count of circles left out as walking every spot in every pass, the way it was first written (`passes`
below: a list of all the spots, which a whole map drained across can't hold in memory)."""
import math
import random
import unittest

from rusemod import nav
from test_nav import made, row

STEP = nav.STEP


def passes(sources, now, least, where, joins, rest):
    """nav._fill as it was when Graph.open_ground went through it (its `joins` way, kept as it was written, less the
    blocks' zones a refill keeps clear of: an open has none): the spots as a sorted list, walked whole in every
    pass."""
    live = [c for c in now if c[2] > 0]
    near = nav._Buckets(live)
    placed = nav._Buckets([])  # the new circles so far

    def covered(x, y, extra=None):
        key = (int(x // near.size), int(y // near.size))
        return any((x - live[i][0]) ** 2 + (y - live[i][1]) ** 2 < live[i][2] ** 2 for i in near.cells.get(key, ())) \
            or extra is not None and any((x - extra.circles[i][0]) ** 2 + (y - extra.circles[i][1]) ** 2
                                         < extra.circles[i][2] ** 2 for i in extra.cells.get(key, ()))

    step = 2 * STEP
    spots, seen = [], set()
    holders = nav._Buckets(list(sources))
    for sx, sy, sr in sources:
        for i in range(int((sx - sr) // step), int((sx + sr) // step) + 1):
            for j in range(int((sy - sr) // step), int((sy + sr) // step) + 1):
                if (i, j) in seen:
                    continue
                seen.add((i, j))
                x, y = i * step, j * step
                deep, source = max(((sources[k][2] - ((x - sources[k][0]) ** 2 + (y - sources[k][1]) ** 2) ** 0.5, k)
                                    for k in holders.near(x, y, 0.0)), default=(-1.0, 0))
                if deep < least or (where is not None and not where(x, y)):
                    continue
                room = min([deep])
                room = (room // STEP) * STEP
                if room >= least and not covered(x, y):
                    spots.append((room, x, y, source))
    spots.sort(key=lambda s: (-s[0], s[1], s[2]))
    out = []
    left = spots
    while left:
        later, took = [], len(out)
        for spot in left:
            r, x, y, source = spot
            if covered(x, y, placed):
                continue
            c = (float(x), float(y), float(r))
            if joins(c) or any(nav._meeting(c, placed.circles[i]) is not None for i in placed.near(*c)):
                out.append(c + (source,))
                placed.add(c)
            else:
                later.append(spot)
        left = later
        if len(out) == took:
            break
    unreached = nav._Buckets(list(placed.circles))
    for r, x, y, _source in left:
        if not covered(x, y, unreached):
            rest.append((float(x), float(y), float(r)))
            unreached.add((float(x), float(y), float(r)))
    return out


def both(zones, old, least, box, where=None, shut=None, most=10 ** 9):
    """(_grow's answer, the passes' answer) for one graph's circles `old`: each (circles, left out). `shut(point)`
    stands for an owner's local map with no ground at a meeting point (no link there)."""
    def meets(c, d):
        point = nav._meeting(c, old[d]) if old[d][2] > 0 else None
        return None if point is None or (shut is not None and shut(point)) else point
    ground = nav._Buckets(list(old))

    def joins(c):
        return any(meets(c, d) is not None for d in ground.near(*c))

    def allowed(x, y):
        return box[0] <= x <= box[2] and box[1] <= y <= box[3] and (where is None or where(x, y))
    rest: list = []
    walked = [c[:3] for c in passes(list(zones), old, least, allowed, joins, rest)]
    new, left, full = nav._grow(list(zones), old, least, box, where, meets, most)
    return (new, left, full), (walked, len(rest))


def scene(rng, on_grid: bool, reach: float = 9000.0, side: float = 60000.0):
    """A made-up graph's circles and some zones over and beside them: on the game's grids, or anywhere."""
    def spot(unit):
        return float(unit * rng.randint(0, int(side // unit))) if on_grid else rng.uniform(0.0, side)

    def size(low, high):
        return float(STEP * rng.randint(int(low // STEP), int(high // STEP))) if on_grid else rng.uniform(low, high)
    old = [(spot(STEP), spot(STEP), size(1280.0, 9600.0)) for _ in range(rng.randint(1, 10))]
    old += [(spot(STEP), spot(STEP), 0.0) for _ in range(rng.randint(0, 2))]  # emptied circles
    rng.shuffle(old)
    zones = [(spot(4800.0 if rng.random() < 0.5 else STEP), spot(4800.0 if rng.random() < 0.5 else STEP),
              size(400.0, reach)) for _ in range(rng.randint(1, 14))]
    for _ in range(rng.randint(0, 8)):  # and some across an old circle's rim, where ground is reached
        x, y, r = rng.choice(old)
        turn, out = rng.uniform(0.0, 2 * math.pi), r + rng.uniform(-1500.0, 3000.0)
        x, y = x + out * math.cos(turn), y + out * math.sin(turn)
        zones.append((float(STEP * round(x / STEP)), float(STEP * round(y / STEP)), size(1500.0, reach)) if on_grid
                     else (x, y, size(1500.0, reach)))
    rng.shuffle(zones)
    return old, zones


class SameAsThePasses(unittest.TestCase):
    def same(self, zones, old, least, box, **more):
        (new, left, full), (walked, rest) = both(zones, old, least, box, **more)
        self.assertFalse(full)
        self.assertEqual(new, walked)
        self.assertEqual([tuple(map(type, c)) for c in new], [(float, float, float)] * len(new))
        self.assertEqual(left, rest)
        return new, left

    def test_on_the_games_grids(self):
        rng = random.Random(1)
        taken = left_out = 0
        for _ in range(60):
            old, zones = scene(rng, on_grid=True)
            new, left = self.same(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0))
            taken, left_out = taken + len(new), left_out + left
        self.assertGreater(taken, 300)  # (both happen: circles reached, and circles left out)
        self.assertGreater(left_out, 100)

    def test_anywhere(self):
        # middles and radii off every grid: the spots' room, what an old circle covers and what meets it all come
        # from the same sums as before, so the answer is the same to the last bit
        rng = random.Random(2)
        taken = 0
        for _ in range(60):
            old, zones = scene(rng, on_grid=False)
            taken += len(self.same(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0))[0])
        self.assertGreater(taken, 300)

    def test_big_zones(self):
        # more room than NEAR and RING: the big spots look round themselves in the first pass, and a new circle's
        # neighbours are found square by square
        rng = random.Random(3)
        most = 0
        for k in range(24):
            old, zones = scene(rng, on_grid=k % 2 == 0, reach=30000.0)
            new, _left = self.same(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0))
            most = max([most] + [r for _x, _y, r in new])
        self.assertGreater(most, nav.RING * STEP)

    def test_a_zone_wider_than_the_map(self):
        # room past 255 STEPs (a spot's room is kept in a byte up to there, in wider numbers past it); the map's edge
        # keeps the spots few
        old = [(30000.0, 30000.0, 6400.0), (41000.5, 30000.0, 3000.0), (9000.0, 9000.0, 2500.0)]
        for zones in ([(100000.0, 40000.0, 200000.0)], [(-70000.3, 31000.7, 180000.0), (90000.0, 20000.0, 70000.0)]):
            new, _left = self.same(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0))
            self.assertGreater(max(r for _x, _y, r in new), 255 * STEP)

    def test_every_spots_room(self):
        # how deep in the zone it lies deepest in, in whole STEPs, by the plain sum: whatever the zones' sizes (the
        # numbers a spot's room is kept in grow with them) and wherever their middles sit
        box = (0.0, 0.0, 30000.0, 20000.0)
        for zones, code in (([(4800.0, 9600.0, 3840.0), (9600.0, 9600.0, 3840.0), (14400.0, 14400.0, 1920.0),
                              (20000.5, 3000.25, 5000.0), (29000.0, 19000.0, 2560.0), (-1000.0, 0.0, 3840.0)], None),
                            ([(15000.0, 10000.0, 90000.0), (4800.0, 9600.0, 3840.0)], "H"),
                            ([(15000.5, 10000.0, 30000000.0), (4800.0, 9600.0, 3840.0)], "I"),
                            ([(15000.0, 10000.0, 3.0e12)], "Q")):
            spots = nav._Spots(zones, nav.MIN_RADIUS, box)
            self.assertEqual((spots.wide, spots.i0, spots.j0, spots.ni, spots.nj), (code, 0, 0, 47, 32))
            for place, room in enumerate(spots.room):
                x, y = spots.at(place)
                deep = max(r - ((x - zx) ** 2 + (y - zy) ** 2) ** 0.5 for zx, zy, r in zones)
                self.assertEqual(room, int(deep // STEP) if deep >= nav.MIN_RADIUS else 0, (zones, x, y))
            self.assertGreaterEqual(spots.top, max(spots.room))
        self.assertEqual(nav._Spots([(5000.0, 5000.0, 1000.0)], nav.MIN_RADIUS, box).ni, 0)  # too small for a spot
        self.assertEqual(nav._Spots([(-9000.0, 5000.0, 3000.0)], nav.MIN_RADIUS, box).ni, 0)  # off the map

    def test_small_rooms_in_a_local_map(self):
        # a town's local map: down to STEP, middles inside the owner only
        rng = random.Random(4)
        taken = 0
        for k in range(40):
            old, zones = scene(rng, on_grid=k % 2 == 0, reach=6000.0, side=24000.0)
            old = [(x, y, r / 4 if k % 2 else float(STEP * max(1, int(r // STEP) // 4))) for x, y, r in old]
            ox, oy, orad = 12000.0, 12000.0, rng.choice((6400.0, 9600.0, 10000.5))

            def inside(x, y, ox=ox, oy=oy, orad=orad):
                return math.hypot(x - ox, y - oy) < orad
            taken += len(self.same(zones, old, STEP, (ox - orad, oy - orad, ox + orad, oy + orad), where=inside)[0])
        self.assertGreater(taken, 300)

    def test_no_link_where_an_owners_local_map_has_no_ground(self):
        rng = random.Random(5)
        for k in range(40):
            old, zones = scene(rng, on_grid=k % 2 == 0)
            self.same(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0),
                      shut=lambda point: int(point[0] // 2000) % 2 == 0)

    def test_the_edge_of_the_map(self):
        rng = random.Random(6)
        for k in range(30):
            old, zones = scene(rng, on_grid=k % 2 == 0)
            self.same(zones, old, nav.MIN_RADIUS, (20000.0, 15000.0, 41000.0, 44444.0))

    def test_a_dried_bed_across_a_sea(self):
        # the build's zones over a dried bed (build._bed_circles): a lattice 4,800 apart of radius 3,840. Beside the
        # land it is reached, circle after circle; an island of it out at sea is left out
        from rusemod.build import BED_RADII
        land = [(0.0, 24000.0, 12800.0), (3200.0, 9600.0, 6400.0)]
        sea = [(float(x), float(y), BED_RADII[0]) for x in range(14400, 62400, 4800) for y in range(0, 48000, 4800)]
        far = [(float(x), float(y), BED_RADII[(x + y) // 4800 % 4]) for x in range(96000, 110400, 4800)
               for y in range(0, 14400, 4800)]
        new, left = self.same(sea + far, land, nav.MIN_RADIUS, (0.0, 0.0, 120000.0, 60000.0))
        self.assertGreater(len(new), 100)
        self.assertTrue(all(x < 70000 for x, _y, _r in new))
        self.assertGreater(left, 5)

    def test_many_passes(self):
        # ground reached only at the far end of the spots' order (the old circle is past the highest x): a pass takes
        # the one big circle next to what the pass before took, and the next goes on from it
        old = [(60160.0, 32000.0, 3200.0)]
        zones = [(float(x), 32000.0, 2560.0) for x in range(6400, 60000, 3840)]
        new, left = self.same(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 70000.0, 70000.0))
        self.assertGreater(len(new), 20)
        self.assertEqual(left, 0)
        big = [x for x, _y, r in new if r == 2560.0]
        self.assertGreater(len(big), 4)
        self.assertEqual(big, sorted(big, reverse=True))  # (from the old circle outward)


class StoppedWhenTooMany(unittest.TestCase):
    def test_the_first_circles_and_no_more(self):
        rng = random.Random(7)
        stopped = 0
        for k in range(30):
            old, zones = scene(rng, on_grid=k % 2 == 0)
            (whole, _left, _full), _walked = both(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0))
            most = rng.randint(1, 12)
            (some, left, full), _walked = both(zones, old, nav.MIN_RADIUS, (0.0, 0.0, 60000.0, 60000.0), most=most)
            if len(whole) >= most:
                self.assertEqual((some, left, full), (whole[:most], 0, True))
                stopped += 1
            else:
                self.assertEqual((some, full), (whole, False))
        self.assertGreater(stopped, 10)

    def test_a_graph_too_big_to_write_is_refused_as_before(self):
        # (_finish refuses more than 65,535 link numbers in the lists: every link is listed twice)
        self.assertEqual(row().open_ground([(12500.0, 2000.0, 2560.0)])["added"], 1)  # a circle and its link
        g = row()
        g.links = g.links * 16383 + g.links[:1]  # 32,767 links: no room for one more
        g.lists = [0] * (2 * len(g.links))
        g.circles = [c[:3] + (0, 0) for c in g.circles[:-1]] + [(0.0, 0.0, 0.0, len(g.lists), 1)]
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())  # (it can be written as it is)
        with self.assertRaises(nav.NavError) as caught:
            g.open_ground([(12500.0, 2000.0, 2560.0)])
        self.assertEqual(str(caught.exception), "the graph would be too big for its 16-bit numbers")
        # the count the growing stops at is the count _finish refuses at: a new circle comes with a link of its own
        self.assertEqual(min(32768 - len(g.links), 65535 - (len(g.circles) - 1)), 1)
        with self.assertRaises(nav.NavError) as caught:
            g._finish([c[:3] for c in g.circles[:-1]] + [(12160.0, 1920.0, 1280.0)], list(enumerate(g.links)),
                      [(None, (2, 3, 11000.0, 2000.0))], 3)
        self.assertEqual(str(caught.exception), "the graph would be too big for its 16-bit numbers")


class Covered(unittest.TestCase):
    def test_the_spots_inside_a_new_circle_go_and_no_others(self):
        # row by row from a square root, then by the test itself: the same spots as the test on every one (small
        # circles' rows are kept for the next; a big one's are worked out on the grid's rows only)
        for zone, box, wide, size, tries in (
                ((30000.0, 20000.0, 81000.0), (0.0, 0.0, 60000.0, 40000.0), None, (94, 63),  # a byte for a spot's room
                 ((1, (5, 5)), (2, (0, 0)), (7, (3, 60)), (12, (50, 30)), (13, (93, 62)), (64, (20, 40)), (65, (30, 30)),
                  (100, (90, 5)))),
                ((150000.0, 100000.0, 1000000.0), (0.0, 0.0, 300000.0, 200000.0), "H", (469, 313),  # a wider number
                 ((12, (100, 100)), (65, (468, 312)), (301, (200, 150)), (2000, (10, 10))))):
            for lv, (ci, cj) in tries:
                spots = nav._Spots([zone], nav.MIN_RADIUS, box)
                self.assertEqual((spots.wide, spots.ni, spots.nj, spots.room.count(0)), (wide, *size, 0))
                place = ci * spots.nj + cj
                spots.cover(place, lv)
                inside = [(640.0 * (at // spots.nj) - 640.0 * ci) ** 2 + (640.0 * (at % spots.nj) - 640.0 * cj) ** 2
                          < (lv * STEP) ** 2 for at in range(len(spots.room))]
                self.assertEqual([room == 0 for room in spots.room], inside, (lv, ci, cj))
                spots.cover(place, lv)  # (again: a small circle's rows are kept)
                self.assertEqual([room == 0 for room in spots.room], inside, (lv, ci, cj))


class Links(unittest.TestCase):
    def test_two_circles_meet_whichever_is_named_first(self):
        # the growing stops where the links would no longer fit, counting a link for every new circle: the one to
        # the circle it was reached from, which Graph._open_here finds again from the other end
        rng = random.Random(10)
        for k in range(20000):
            p, q = ((640.0 * rng.randint(0, 6000), 640.0 * rng.randint(0, 4000), 320.0 * rng.randint(1, 40))
                    if k % 2 else (rng.uniform(0, 4e6), rng.uniform(0, 4e6), rng.uniform(300, 13000))
                    for _ in range(2))
            q = q if k % 4 else (p[0] + 640.0 * rng.randint(-12, 12), p[1] + 640.0 * rng.randint(-12, 12), q[2])
            self.assertEqual(nav._meeting(p, q) is None, nav._meeting(q, p) is None)


class Lists(unittest.TestCase):
    def test_the_nearest_circle_of_them_all(self):
        # (a new circle with no old one near it goes in the index under the nearest: nav._index_more)
        rng = random.Random(9)
        for k in range(30):
            circles = [(float(320 * rng.randint(0, 300)), float(320 * rng.randint(0, 300)),
                        float(320 * rng.randint(1, 40))) if k % 2 else
                       (rng.uniform(0, 90000), rng.uniform(0, 90000), rng.uniform(300, 12000))
                       for _ in range(rng.choice((1, 7, 9, 60, 300)))]
            circles += circles[:3]  # (equals: the first of them)
            tree = nav._Nearest(circles)
            for _ in range(40):
                x, y = (float(640 * rng.randint(-400, 600)), float(640 * rng.randint(-400, 600))) if k % 2 else \
                    (rng.uniform(-200000, 300000), rng.uniform(-200000, 300000))
                plain = min(range(len(circles)), key=lambda i: ((circles[i][0] - x) ** 2 + (circles[i][1] - y) ** 2)
                            ** 0.5 - circles[i][2])
                self.assertEqual(tree.find(x, y), plain)

    def test_the_index_with_new_circles_far_from_the_old(self):
        # as going through every old circle for each new one gave it (how nav._index_more was first written)
        def plain(points, old, new):
            live = [i for i, c in enumerate(old) if c[2] > 0]
            where = nav._Buckets([old[i] for i in live])
            into, boxes = {}, {}
            for j, (x, y, r) in new:
                ids = list(where.near(x, y, r + 20480.0)) or range(len(live))
                bank = live[min(ids, key=lambda k: ((old[live[k]][0] - x) ** 2 + (old[live[k]][1] - y) ** 2) ** 0.5
                                - old[live[k]][2])]
                into.setdefault(bank, []).append(j)
                bx0, by0, bx1, by1 = boxes.get(bank, (x, y, x, y))
                boxes[bank] = (min(bx0, x - r), min(by0, y - r), max(bx1, x + r), max(by1, y + r))
            return nav._index_add(points, into, boxes)
        rng = random.Random(12)
        old = [(float(320 * rng.randint(0, 200)), float(320 * rng.randint(0, 200)), float(320 * rng.randint(0, 20)))
               for _ in range(40)]
        points = nav._tree_write(nav._tree_build(old))
        new = [(40 + j, (float(640 * rng.randint(-300, 600)), float(640 * rng.randint(-300, 600)), 1280.0))
               for j in range(200)]
        self.assertGreater(sum(1 for _j, (x, y, r) in new if not list(nav._Buckets(old).near(x, y, r + 20480.0))), 50)
        self.assertEqual(nav._index_more(points, old, new), plain(points, old, new))

    def test_zones_with_no_new_circle_in_them(self):
        rng = random.Random(8)
        for k in range(40):
            zones = [(rng.uniform(0, 90000), rng.uniform(0, 90000), rng.choice((0.0, -5.0, 900.0, 7000.0, 300000.0)))
                     for _ in range(rng.randint(0, 30))]
            circles = [(rng.uniform(0, 90000), rng.uniform(0, 90000), 1280.0) for _ in range(rng.randint(0, 40) * (k % 3))]
            plain = [i for i, (zx, zy, zr) in enumerate(zones)
                     if not any(math.hypot(x - zx, y - zy) < zr for x, y, _r in circles)]
            self.assertEqual(nav._without(zones, circles), plain)

    def test_the_zones_that_reach_an_owner_in_their_order(self):
        # (Graph.open_ground looks the zones up by place for each town: the same ones, in the order given)
        local = made([(5000.0, 5000.0, 1280.0)], [])
        g = made([(5000.0, 5000.0, 6400.0), (16000.0, 5000.0, 6400.0)], [(0, 1)], [local])
        zones = [(float(x), float(y), 2000.0) for x in range(0, 30000, 1500) for y in range(0, 12000, 1500)]
        seen = []
        inner = nav.Graph._open_here

        def spy(self, zs, *args, **kwargs):
            seen.append(list(zs))
            return inner(self, zs, *args, **kwargs)
        nav.Graph._open_here = spy
        try:
            g.open_ground(zones)
        finally:
            nav.Graph._open_here = inner
        self.assertEqual(seen[0], zones)
        self.assertEqual(seen[1], [z for z in zones if math.hypot(z[0] - 5000.0, z[1] - 5000.0) < z[2] + 6400.0])


if __name__ == "__main__":
    unittest.main()
