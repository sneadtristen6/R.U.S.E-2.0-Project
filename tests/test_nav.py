"""The navigation graphs in mapinfo.win (rusemod.nav): a made-up graph with one local graph, read and written back."""
import struct
import unittest

from rusemod import nav


def graph(subs=()):
    """Two circles side by side and the link where they meet; one crossing and a few index bytes."""
    g = nav.Graph(
        box=(0, 0, 8000.0),
        circles=[(2000.0, 2000.0, 1280.0, 0, 0), (4000.0, 2000.0, 1280.0, 1, 1), (0.0, 0.0, 0.0, 2, 1)],
        links=[(0, 1, 3000.0, 2000.0)],
        lists=[0, 0],
        crossings=struct.pack("<5f2HI", 1.0, 2.0, 3.0, 4.0, 2.0, 0, 0, 0),
        points=struct.pack("<2H", 2, 0) + struct.pack("<H", 1) + b"\0\0",
        subs=list(subs),
        head_rest=bytes(nav.HEADER - 20))
    return g


class Graphs(unittest.TestCase):
    def test_written_and_read_back(self):
        g = graph(subs=[graph()])
        data = g.to_bytes()
        self.assertEqual(struct.unpack_from("<4H", data, 12), (2, 1, 1, 1))  # circles, links, crossings, local graphs
        back = nav.Graph.read(data)
        self.assertEqual(back.to_bytes(), data)
        self.assertEqual((back.circles, back.links, back.lists), (g.circles, g.links, g.lists))
        self.assertEqual(len(back.subs), 1)
        self.assertEqual(back.subs[0].to_bytes(), graph().to_bytes())
        self.assertEqual(back.links_of(1), [0])
        self.assertEqual(back.at(2500.0, 2000.0), [0])
        self.assertEqual(back.at(3000.0, 2000.0), [0, 1])  # where they meet

    def test_crossings_follow_the_road_links_numbered_again(self):
        g = row()
        g.subs = [row()]
        self.assertEqual(struct.unpack_from("<2H", g.crossings, 24), (7, 0))  # the road links it runs on
        self.assertEqual(g.renumber_roads({7: 3, 0: 1, 5: 2}), 0)
        for gg in (g, g.subs[0]):
            self.assertEqual(struct.unpack_from("<2H", gg.crossings, 24), (3, 1))
            self.assertEqual(struct.unpack_from("<4H", gg.crossings, 20)[:2], (0, 1))  # its graph links untouched
        self.assertEqual(g.renumber_roads({9: 4}), 0)  # numbers it doesn't name stay as they are
        self.assertEqual(struct.unpack_from("<2H", g.crossings, 24), (3, 1))
        self.assertEqual(g.renumber_roads({3: 0, 1: None}), 2)  # its road link 1 went: the crossing goes, here and below
        self.assertEqual((g.crossings, [c[4] for c in g.circles]), (b"", [0, 0, 0, 0]))
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())

    def test_parts_and_the_index_walk(self):
        g = row()
        self.assertEqual(g.parts(), [3])
        self.assertEqual((g.find(2000.0, 2000.0), g.find(10500.0, 2000.0), g.find(50000.0, 0.0)), (0, 2, None))
        g.links = g.links[:1]  # B-C unlinked: C is a piece of its own
        self.assertEqual(g.parts(), [2, 1])

    def test_mistakes(self):
        data = graph().to_bytes()
        with self.assertRaisesRegex(nav.NavError, "too short"):
            nav.Graph.read(data[:40])
        bad = bytearray(data)
        struct.pack_into("<H", bad, 12, 5)  # says five circles
        with self.assertRaisesRegex(nav.NavError, "don't match"):
            nav.Graph.read(bytes(bad))


def row():
    """Three circles in a row, A (r 3200) at x 2000, B (r 3200) at x 7000, C (r 1600) at x 10000, linked A-B and
    B-C; one crossing through B from link 0 to link 1."""
    return nav.Graph(
        box=(0, 0, 16000.0),
        circles=[(2000.0, 2000.0, 3200.0, 0, 0), (7000.0, 2000.0, 3200.0, 1, 0), (10000.0, 2000.0, 1600.0, 3, 1),
                 (0.0, 0.0, 0.0, 4, 1)],
        links=[(0, 1, 4500.0, 2000.0), (1, 2, 9000.0, 2000.0)],
        lists=[0, 0, 1, 1],
        crossings=struct.pack("<5f2HI", 4500.0, 2000.0, 9000.0, 2000.0, 4500.0, 0, 1, 7),
        points=struct.pack("<H3H", 6, 0, 1, 2),
        head_rest=bytes(nav.HEADER - 20))


class Blocking(unittest.TestCase):
    def test_ground_a_block_cuts_off_goes_too(self):
        # the owner's D-Day mod (2026-09-30): block brushes cut a town's local map into five pieces, and the build
        # wrote it; ground units can't reach crashes the game when they're ordered onto it
        g = row()
        g.block([(7000.0, 2000.0, 400.0)], refill=False)  # B emptied: A and C are each on their own
        self.assertEqual(g.parts(), [1, 1])
        self.assertEqual(g.drop_cut_off(), 1)
        self.assertEqual((g.parts(), [c[2] > 0 for c in g.circles[:-1]].count(True)), ([1], 1))
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        g = town()
        g.subs[0].block([(5000.0, 22400.0, 300.0)], refill=False)  # the middle one goes: the town's map in two
        self.assertEqual(g.subs[0].parts(), [1, 1])
        self.assertEqual(nav._drop_cut_off(g), 1)
        self.assertEqual((g.subs[0].parts(), g.parts()), ([1], [6]))
        g = town()
        g.subs[0].block([(5000.0, 22400.0, 3000.0)], refill=False)  # no ground left in the town: no route through
        self.assertEqual(nav._drop_cut_off(g), 1)  # the owner goes, and nothing else is cut off
        self.assertEqual((g.circles[0][2], g.parts()), (0.0, [5]))
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())

    def test_a_block_never_shrinks_a_circle_that_owns_a_local_map(self):
        # the owner's D-Day test (2026-10-01): a mod that only placed buildings left an infantry squad standing in the
        # river beside a bridge of the map's own. The blocks had shrunk the owner circles the game decides ground by,
        # so everything their local maps kept closed opened up. apply_blocks keeps owners whole and blocks in the
        # local maps instead
        from rusemod.cover import member
        import struct
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 32000.0, 32000.0)
        g = bridged()  # an owner of 8,000 over a river, its local map lining the deck
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            b"roads", g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})
        block = nav.Block(x=12000.0, y=2000.0, radius=600.0, units="all")  # a building on the bank inside the owner
        new, _notes = nav.apply_blocks({member("Blitz"): win}.get, "Blitz", [block])
        from ruse_mod_engine import sdb
        after = nav.Graph.read(sdb.split_mapinfo(new[member("Blitz")])[1][2])
        self.assertEqual(after.circles[0][2], 8000.0)           # the owner is untouched
        self.assertEqual(len(after.subs), len(g.subs))
        before_local = [c[2] for c in g.subs[0].circles[:-1]]
        after_local = [c[2] for c in after.subs[0].circles[:-1]]
        self.assertNotEqual(after_local[:len(before_local)], before_local)  # the block went into its local map
        self.assertFalse(after.walkable(12000.0, 2000.0))       # the building's own ground is closed
        self.assertTrue(after.walkable(14000.0, 2000.0))        # the deck beyond it still isn't

    def test_an_emptied_circle_leaves_the_index(self):
        """The game finds the circle nearest an order or a route's end through the index, with no test of the radius:
        an emptied circle left in it is landed on, and a route to it (it has no links) fails. Written, the index holds
        the live circles only, by their own numbers."""
        def listed(node):
            return node[1] if node[0] == "leaf" else listed(node[3]) + listed(node[4])
        g = row()
        g.block([(10800.0, 2000.0, 400.0)], refill=False)  # C emptied
        self.assertEqual(sorted(listed(nav._tree_read(g.points))), [0, 1, 2])  # still listed until it's written
        back = nav.Graph.read(g.to_bytes())
        self.assertEqual(sorted(listed(nav._tree_read(back.points))), [0, 1])
        self.assertEqual((back.find(2000.0, 2000.0), back.find(7000.0, 2000.0), back.find(11000.0, 2000.0)),
                         (0, 1, None))  # (11,000: C's ground only)
        self.assertEqual(back.to_bytes(), g.to_bytes())
        untouched = row()
        self.assertEqual(nav.Graph.read(untouched.to_bytes()).points, untouched.points)  # nothing emptied: as it was

    def test_a_crossing_whose_road_runs_through_a_block_goes(self):
        """The game routes a unit through a circle along its crossing's road without asking whether the ground is
        walkable: a block on that road (a building placed on a town's road) has to take the crossing out, or units
        drive through it. The road itself stays (supply trucks use it)."""
        from rusemod.roadnet import RoadNet
        road = RoadNet([(1000.0 * i, 2000.0) for i in range(13)], [(i, i + 1, 100) for i in range(12)])
        g = row()  # its crossing through B runs on road links 7 (x 7,000-8,000) and 0 (x 0-1,000)
        self.assertEqual(g.drop_crossings_through(lambda: road, [(7000.0, 4500.0, 400.0)]), 0)  # in B, off the road
        self.assertEqual(g.drop_crossings_through(lambda: road, [(5000.0, 5000.0, 400.0)]), 0)  # near no circle's road
        self.assertEqual(len(g.crossings), 28)
        self.assertEqual(g.drop_crossings_through(lambda: road, [(5000.0, 2000.0, 400.0)]), 1)  # on the road, in B
        self.assertEqual((g.crossings, [c[4] for c in g.circles]), (b"", [0, 0, 0, 0]))
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        self.assertEqual(len(road.links), 12)

    def test_a_circle_emptied_and_one_shrunk(self):
        g = row()
        counts = g.block([(10800.0, 2000.0, 400.0)])  # C's middle is 800 away: C keeps 400 clear, too small
        self.assertEqual(counts, {"emptied": 1, "shrunk": 0, "links": 1, "crossings": 1, "added": 0, "linked": 0})
        self.assertEqual([c[2] for c in g.circles[:-1]], [3200.0, 3200.0, 0.0])
        self.assertEqual(g.links, [(0, 1, 4500.0, 2000.0)])
        self.assertEqual([g.links_of(i) for i in range(3)], [[0], [0], []])
        self.assertEqual(g.crossings, b"")
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        g = row()
        counts = g.block([(1000.0, 5500.0, 500.0)])  # A's middle is 3640 away: A shrinks to keep clear
        self.assertEqual((counts["shrunk"], counts["emptied"], counts["links"]), (1, 0, 0))
        self.assertEqual(g.circles[0][2], 2880.0)  # 3140 clear, in steps of 320
        self.assertEqual(len(g.crossings), 28)  # the crossing's links both stay
        g = row()
        g.block([(4500.0, 2000.0, 200.0)])  # right on A-B's meeting point: both shrink, the link goes
        self.assertEqual(g.links, [(1, 2, 9000.0, 2000.0)])
        self.assertEqual(struct.unpack_from("<2H", g.crossings, 20) if g.crossings else None, None)
        self.assertEqual(g.points, row().points)  # the index isn't touched
        g = row()
        g.block([(9700.0, 2000.0, 400.0)])  # C goes; B shrinks to 2240, off A-B's meeting point, still overlapping A
        self.assertEqual(g.links, [(0, 1, 4980.0, 2000.0)])  # the gate moves to where they still meet: A and B stay one
        self.assertEqual(g.parts(), [2])

    def test_the_ground_given_up_is_filled_back(self):
        """A big circle with a small block at its edge: it shrinks a lot, and new circles fill what it gave up,
        right up to the block, linked in, and listed in the index as one more tree."""
        g = nav.Graph(box=(0, 0, 80000.0), circles=[(20000.0, 20000.0, 16000.0, 0, 0), (40000.0, 20000.0, 8000.0, 1, 0),
                                                     (0.0, 0.0, 0.0, 2, 0)],
                      links=[(0, 1, 34000.0, 20000.0)], lists=[0, 0], crossings=b"", points=struct.pack("<3H", 4, 0, 1),
                      head_rest=bytes(nav.HEADER - 20))
        zone = (20000.0, 33000.0, 2000.0)  # near the big circle's top edge
        counts = g.block([zone])
        self.assertEqual((counts["shrunk"], counts["emptied"]), (1, 0))
        self.assertEqual(g.circles[0][2], 10880.0)  # 11000 clear, in steps of 320
        self.assertGreater(counts["added"], 3)
        new = g.circles[2:-1]
        for x, y, r, _l, _c in new:
            self.assertGreaterEqual(r, nav.MIN_RADIUS)
            self.assertLessEqual(((x - 20000.0) ** 2 + (y - 20000.0) ** 2) ** 0.5 + r, 16000.0)  # inside the old one
            self.assertGreaterEqual(((x - zone[0]) ** 2 + (y - zone[1]) ** 2) ** 0.5, zone[2] + r)  # clear of the zone
            self.assertEqual((x % nav.STEP, y % nav.STEP, r % nav.STEP), (0.0, 0.0, 0.0))
        for i, (a, b, x, y) in enumerate(g.links):  # every link inside both its circles, and listed for both
            self.assertLess(a, b)
            for c in (a, b):
                cx, cy, cr = g.circles[c][:3]
                self.assertLessEqual((x - cx) ** 2 + (y - cy) ** 2, cr * cr + 1.0)
                self.assertIn(i, g.links_of(c))
        self.assertTrue(all(g.links_of(c) for c in range(len(g.circles) - 1)))  # nothing left unlinked
        self.assertEqual([b for _a, b, _x, _y in g.links], sorted(b for _a, b, _x, _y in g.links))  # as the game's files
        # the index: the leaf that listed the shrunk circle (0) lists the new ones too, padded to 4 bytes
        n = counts["added"]
        self.assertEqual(struct.unpack_from(f"<{3 + n}H", g.points, 0), (2 * (2 + n), 0, 1) + tuple(range(2, 2 + n)))
        self.assertEqual(len(g.points), (2 + 2 * (2 + n) + 3) // 4 * 4)
        self.assertEqual(nav._index_add(struct.pack("<3H", 4, 0, 1), {7: [9]}), struct.pack("<4H", 6, 0, 1, 9))
        # a branch: its right half is found through the jump, the left half padded to 4 bytes
        tree = struct.pack("<HHff", 1, 3, 100.0, 200.0) + struct.pack("<2H", 2, 0) + struct.pack("<2H", 2, 1)
        self.assertEqual(nav._tree_read(tree), ["branch", 1, struct.pack("<ff", 100.0, 200.0), ["leaf", [0]], ["leaf", [1]]])
        self.assertEqual(nav._tree_write(nav._tree_read(tree)), tree)
        grown = nav._index_add(tree, {0: [5, 6]})
        self.assertEqual(nav._tree_read(grown), ["branch", 1, struct.pack("<ff", 100.0, 200.0), ["leaf", [0, 5, 6]], ["leaf", [1]]])
        self.assertEqual(struct.unpack_from("<HH", grown, 0), (1, 5))  # the jump grew from 4 to 8 bytes: word 4 | bit
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        # the old ground outside the zone is covered again, but for thin slivers along the circles' edges
        import random
        rnd, lost = random.Random(1), 0
        for _ in range(400):
            x, y = rnd.uniform(4000, 36000), rnd.uniform(4000, 36000)
            if (x - 20000) ** 2 + (y - 20000) ** 2 > 15000 ** 2 or (x - zone[0]) ** 2 + (y - zone[1]) ** 2 < 3000 ** 2:
                continue
            lost += not g.at(x, y)
        self.assertLess(lost, 12)

    def test_the_file(self):
        import tomllib
        blocks = [nav.Block(1.0, 2.0, 3.0), nav.Block(4.0, 5.0, 6.0, "vehicles")]
        text = nav.blocks_toml(blocks, "two")
        self.assertEqual(nav.parse_blocks(tomllib.loads(text)["block"]), blocks)
        for bad, why in (({"x": 1, "y": 2}, "radius is missing"), ({"x": 1, "y": 2, "radius": -1}, "more than 0"),
                         ({"x": 1, "y": 2, "radius": 3, "units": "boats"}, "units must be"),
                         ({"x": 1, "y": 2, "radius": 3, "who": 1}, "unknown key")):
            with self.assertRaisesRegex(nav.NavError, why):
                nav.parse_blocks([bad])


def made(circles, pairs, subs=(), points=None, crossings=()):
    """A graph of `circles` (x, y, r) linked in `pairs` where they meet (listed by their second circle), with local
    maps `subs` and `crossings` ((circle, gate link, gate link, road link, road link), a record each), its index one
    leaf unless `points` is given."""
    links = [(a, b) + nav._meeting(circles[a], circles[b]) for a, b in sorted(pairs, key=lambda p: (p[1], p[0]))]
    mine = [[] for _ in circles]
    for k, (a, b, _x, _y) in enumerate(links):
        mine[a].append(k)
        mine[b].append(k)
    recs, lists, cross = [], [], []
    for c, (x, y, r) in enumerate(circles):
        recs.append((x, y, r, len(lists), len(cross)))
        lists += mine[c]
        cross += [struct.pack("<5f4H", x, y, x + 1, y + 1, 1.0, g0, g1, r0, r1) for cc, g0, g1, r0, r1 in crossings
                  if cc == c]
    recs.append((0.0, 0.0, 0.0, len(lists), len(cross)))
    return nav.Graph(box=(0, 0, 65536.0), circles=recs, links=links, lists=lists, crossings=b"".join(cross),
                     points=points or nav._tree_write(["leaf", list(range(len(circles)))]), subs=list(subs),
                     head_rest=bytes(nav.HEADER - 20))


LAND = [(5000.0, 2000.0, 6400.0), (5000.0, 14000.0, 6400.0), (13500.0, 18000.0, 6400.0), (22000.0, 14000.0, 6400.0),
        (22000.0, 2000.0, 6400.0)]
DECK = (9000.0, 2000.0, 18000.0, 2000.0)  # over the river of town(), bank to bank


def town():
    """Two banks along y 2000, W (circle 1, x up to 11,400) and E (circle 5, x from 15,600), the river between (no
    circle over it), joined the long way round north of it; a town at the top, circle 0, whose local map (three
    circles) holds the point where it meets the land; a crossing in circles 2 and 3. Its index: x splits the town,
    W and the circle north of W from the rest."""
    local = made([(5000.0, 20800.0, 1280.0), (5000.0, 22400.0, 1280.0), (5000.0, 24000.0, 1280.0)], [(0, 1), (1, 2)])
    tree = ["branch", 1, struct.pack("<2f", 11400.0, 7100.0), ["leaf", [0, 1, 2]], ["leaf", [3, 4, 5]]]
    return made([(5000.0, 26000.0, 6400.0)] + LAND, [(0, 2), (1, 2), (2, 3), (3, 4), (4, 5)], [local],
                nav._tree_write(tree), [(2, 0, 1, 7, 8), (3, 2, 3, 8, 9)])


def river(x, y):
    return 11400.0 < x < 15600.0 and -40000.0 < y < 40000.0


class Owners(unittest.TestCase):
    """A new bridge's own local map (Graph.open): an owner circle over the deck, put in at circle number NX."""

    def test_every_old_number_follows_the_owner_in(self):
        old, g = town(), town()
        counts = g.open([DECK], 1280.0, water=river)
        self.assertEqual(counts["owners"], [(0, 1, 4800.0, 18)])  # circle 1, after the town; 16 deck circles, 2 copies
        self.assertEqual((counts["added"], counts["linked"], counts["closed"], counts["crowded"]), (1, 2, [], []))

        def num(i):
            return i if i < 1 else i + 1
        self.assertEqual(g.circles[1][:3], (13440.0, 1920.0, 4800.0))  # the deck's middle on the grid
        self.assertEqual([c[:3] for c in g.circles[:1] + g.circles[2:-1]], [c[:3] for c in old.circles[:-1]])
        pairs = {(a, b): (x, y) for a, b, x, y in g.links}
        for a, b, x, y in old.links:  # every old link, between the same circles, where it was
            self.assertEqual(pairs[(num(a), num(b))], (x, y))
        self.assertEqual(set(pairs) - {(num(a), num(b)) for a, b, _x, _y in old.links}, {(1, 2), (1, 6)})  # to W, E
        self.assertEqual([b for _a, b, _x, _y in g.links], sorted(b for _a, b, _x, _y in g.links))
        for i in range(len(old.circles) - 1):  # each circle's list: links to the same circles, and the owner's
            before = {num(a + b - i) for a, b, _x, _y in (old.links[k] for k in old.links_of(i))}
            after = {a + b - num(i) for a, b, _x, _y in (g.links[k] for k in g.links_of(num(i)))}
            self.assertLessEqual(before, after)
            self.assertEqual(after - before, {1} if num(i) in (2, 6) else set())
        for i in range(len(old.circles) - 1):  # the crossings: the same records, their gates the same circles' links
            mine = [old.crossings[28 * k:28 * k + 28] for k in range(old.circles[i][4], old.circles[i + 1][4])]
            now = [g.crossings[28 * k:28 * k + 28] for k in range(g.circles[num(i)][4], g.circles[num(i) + 1][4])]
            self.assertEqual([r[:20] + r[24:] for r in mine], [r[:20] + r[24:] for r in now])
            for r, s in zip(mine, now):
                was = [old.links[k][:2] for k in struct.unpack_from("<2H", r, 20)]
                self.assertEqual([g.links[k][:2] for k in struct.unpack_from("<2H", s, 20)],
                                 [(num(a), num(b)) for a, b in was])
        self.assertEqual(len(g.crossings), len(old.crossings))
        for x, y, _r, _l, _c in old.circles[:-1]:  # the index finds every old circle as before, numbered again
            self.assertEqual(g.find(x, y), num(old.find(x, y)))
        leaves, todo = [], [nav._tree_read(g.points)]
        while todo:
            node = todo.pop()
            if node[0] == "leaf":
                leaves += node[1]
            else:
                todo += [node[3], node[4]]
        self.assertEqual(sorted(leaves), list(range(7)))
        self.assertEqual(g.find(13500.0, 2000.0), 1)  # the deck: the owner (its edges widened to reach it)

    def test_the_header_offsets_and_the_new_local_map(self):
        old, g = town(), town()
        g.open([DECK], 1280.0, water=river)
        data = g.to_bytes()
        self.assertEqual(struct.unpack_from("<4H", data, 12), (7, 7, 2, 2))  # circles, links, crossings, local maps
        offsets = struct.unpack_from("<7I", data, nav.HEADER)  # five sections and one per local map
        self.assertEqual(offsets[0], nav.HEADER + 4 * 7)
        self.assertEqual(data[offsets[5]:offsets[6]], old.subs[0].to_bytes())  # the town's, as it was
        local = data[offsets[6]:]
        self.assertEqual(local, g.subs[1].to_bytes())  # the bridge's, after it
        self.assertEqual((struct.unpack_from("<H", local, 18)[0], local[20:nav.HEADER]), (0, bytes(nav.HEADER - 20)))
        self.assertEqual(local[:12], data[:12])  # the main graph's box
        back = nav.Graph.read(data)
        self.assertEqual(back.to_bytes(), data)
        sub = back.subs[1]
        self.assertEqual(sub.parts(), [18])  # one piece
        self.assertEqual(sorted({c[2] for c in sub.circles[:-1]}), [640.0, 6400.0])  # the deck, and copies of W and E
        for a, b, x, y in back.links:  # where the owner meets W and E: on ground of its local map
            if 1 in (a, b):
                self.assertIsNotNone(sub.find(x, y))
        self.assertEqual(sub.crossings, b"")

    def test_the_river_beside_the_deck_stays_closed(self):
        old, g = town(), town()
        g.open([DECK], 1280.0, water=river)
        for x in range(11500, 15600, 100):
            self.assertTrue(g.walkable(float(x), 2000.0))  # all along the deck
            for dy in (700.0, 1000.0, 1280.0, 2000.0, 4000.0):  # beside it: water, as before
                for y in (2000.0 - dy, 2000.0 + dy):
                    self.assertFalse(g.walkable(float(x), y), (x, y))
                    self.assertFalse(old.walkable(float(x), y))
        for x, y in ((3000.0, 2000.0), (9000.0, 6000.0), (20000.0, -2000.0), (5000.0, 21000.0)):  # the land as before
            self.assertTrue(g.walkable(x, y) and old.walkable(x, y))
        self.assertFalse(g.walkable(5000.0, 30000.0) or old.walkable(5000.0, 30000.0))  # the town: off its local map
        plain = town()  # main circles along the deck (before 2026-09-30, evening): the water beside it was ground
        plain.circles = plain.circles[:-1] + [(13500.0, 2000.0, 1280.0, 10, 2), (0.0, 0.0, 0.0, 10, 2)]
        plain.points = nav._tree_write(["leaf", list(range(7))])
        self.assertTrue(plain.walkable(13500.0, 2900.0))

    def test_a_deck_with_no_room_for_an_owner_stays_closed(self):
        g = town()
        islet = (13500.0, 5120.0, 1280.0)  # a circle's middle 3,200 from the deck's: no owner can hold the deck alone
        g.circles = g.circles[:-1] + [islet + (10, 2), (0.0, 0.0, 0.0, 10, 2)]
        before = g.to_bytes()
        counts = g.open([DECK], 1280.0, water=river)
        self.assertEqual((counts["crowded"], counts["owners"], counts["added"]), ([0], [], 0))
        self.assertEqual(g.to_bytes(), before)

    def test_an_old_deck_of_main_circles_goes_under_the_new_one(self):
        # a bridge of the map's with no owner, its deck plain main circles over the river (three on D-Day): they'd be
        # in the new owner, so they go when it opens; without the water they're land, and the new deck has no room
        chained = [(12000.0, 2000.0, 1600.0), (13500.0, 2000.0, 1600.0), (15000.0, 2000.0, 1600.0)]
        pairs = [(0, 2), (1, 2), (2, 3), (3, 4), (4, 5), (1, 6), (6, 7), (7, 8), (5, 8)]
        g = made([(5000.0, 26000.0, 6400.0)] + LAND + chained, pairs, town().subs)
        counts = g.open([DECK], 1280.0, water=river)
        self.assertEqual((counts["under"], counts["owners"], counts["crowded"]), (3, [(0, 1, 4800.0, 18)], []))
        self.assertEqual([c[2] for c in g.circles[7:10]], [0.0, 0.0, 0.0])  # (numbered one up: the owner is 1)
        self.assertFalse([lk for lk in g.links if {lk[0], lk[1]} & {7, 8, 9}])
        self.assertEqual(g.parts(), [7])
        self.assertTrue(g.walkable(13500.0, 2000.0) and not g.walkable(13500.0, 3000.0))
        g = made([(5000.0, 26000.0, 6400.0)] + LAND + chained, pairs, town().subs)
        self.assertEqual(g.open([DECK], 1280.0)["crowded"], [0])

    def test_a_deck_in_an_old_owner_goes_into_its_local_map(self):
        g, old = bridged(), bridged()
        counts = g.open([(10200.0, 2000.0, 17000.0, 2000.0)], 1280.0, water=river)
        self.assertEqual((counts["inside"], counts["owners"], counts["added"]), ([(0, 0)], [], 0))
        self.assertEqual(g.circles, old.circles)  # the main graph as it was: the owner takes the deck
        self.assertEqual(g.links, old.links)
        sub = g.subs[0]
        self.assertEqual(sub.parts(), [14])  # the banks and the new deck's 12 circles: one piece
        self.assertEqual([c[2] for c in sub.circles[1:5]], [0.0] * 4)  # the old deck, over the water, gone
        for a, b, x, y in g.links:
            self.assertIsNotNone(sub.find(x, y))  # where the owner meets W and E: still on its ground
        for x in range(11500, 15600, 100):
            self.assertTrue(g.walkable(float(x), 2000.0))
            self.assertFalse(g.walkable(float(x), 2700.0) or g.walkable(float(x), 1300.0))
            self.assertTrue(old.walkable(float(x), 2700.0))  # (the old deck's circles reached it)
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        g = bridged()  # a deck that leaves the owner: it can't go in, and there's no room for one of its own
        counts = g.open([(10200.0, 2000.0, 24000.0, 2000.0)], 1280.0, water=river)
        self.assertEqual((counts["inside"], counts["crowded"]), ([], [0]))
        self.assertEqual(g.to_bytes(), bridged().to_bytes())

    def test_what_only_the_old_deck_held_goes_with_it(self):
        # some maps have small circles beside a bridge's deck, linked to the deck alone: with the old deck gone they'd
        # be a piece apart (an order there crashes the game), so they go too
        g = bridged()
        side = (11300.0, 3200.0, 640.0)  # on the bank, linked only to the old deck's first circle
        circles = [c[:3] for c in g.subs[0].circles[:-1]] + [side]
        g.subs[0] = made(circles, [(i, i + 1) for i in range(5)] + [(1, 6)])
        counts = g.open([(10200.0, 2000.0, 17000.0, 2000.0)], 1280.0, water=river)
        self.assertEqual(counts["inside"], [(0, 0)])
        self.assertEqual(g.subs[0].circles[6][2], 0.0)
        self.assertEqual(g.subs[0].parts(), [14])

    def test_an_old_bridges_owner_stays_when_its_deck_is_closed(self):
        g = bridged()
        g.block([(13000.0, 2000.0, 1600.0)], refill=False, keep_owners=True)
        self.assertEqual(g.circles[0][2], 8000.0)  # its middle is in the zone, but it owns a local map: it stays
        self.assertEqual(g.subs[0].parts(), [1, 1])  # its local map lost the deck: the banks apart
        g = bridged()
        g.block([(13000.0, 2000.0, 1600.0)], refill=False)
        self.assertEqual(g.circles[0][2], 0.0)


def bridged():
    """Two banks along y 2000, W (circle 1) and E (circle 2), and the river between (x 11,400 to 15,600), crossed by
    a bridge of the map's: its owner (circle 0, radius 8,000) links W and E, and its local map has a bank circle at
    each end, holding the points where it meets them, and an old deck between, four circles of 1,280 over the water."""
    deck = [(9600.0, 2000.0, 1600.0)] + [(11800.0 + 1100.0 * k, 2000.0, 1280.0) for k in range(4)] \
        + [(17600.0, 2000.0, 1600.0)]
    local = made(deck, [(i, i + 1) for i in range(len(deck) - 1)])
    return made([(13800.0, 2000.0, 8000.0), (5000.0, 2000.0, 6400.0), (22000.0, 2000.0, 6400.0)], [(0, 1), (0, 2)],
                [local])


def road(line, step=1000.0):
    """A road network along the polyline `line`: points every `step` (its corners kept), linked in a chain."""
    from rusemod.roadnet import RoadNet
    pts = [line[0]]
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        k = max(1, round(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 / step))
        pts += [(ax + (bx - ax) * i / k, ay + (by - ay) * i / k) for i in range(1, k + 1)]
    return RoadNet(pts, [(i, i + 1, 100) for i in range(len(pts) - 1)])


def crossings(g):
    """{circle: [(x0, y0, x1, y1, length, gate a, gate b, road link 0, road link 1)]} of a graph."""
    out = {}
    for c in range(len(g.circles) - 1):
        for k in range(g.circles[c][4], g.circles[c + 1][4]):
            out.setdefault(c, []).append(struct.unpack_from("<5f4H", g.crossings, 28 * k))
    return out


class Crossings(unittest.TestCase):
    """New roads get crossings (Graph.add_crossings): units plan along a road only through them."""
    ROW = [(7000.0, 2000.0, 3200.0), (2000.0, 2000.0, 3200.0), (12000.0, 2000.0, 3200.0)]  # B, A west, C east

    def test_a_road_through_a_circle_from_gate_to_gate(self):
        g = made(self.ROW, [(0, 1), (0, 2)])  # A-B meet at x 4,500, B-C at x 9,500
        net = road([(250.0, 2000.0), (14250.0, 2000.0)])  # links of 1,000: x 4,500 on link 4, 9,500 on link 9
        got = g.add_crossings(net)
        self.assertEqual((got["added"], got["circles"], got["full"]), (1, 1, 0))
        (x0, y0, x1, y1, length, ga, gb, r0, r1), = crossings(g)[0]  # in B only: A and C have one gate each
        self.assertEqual((ga, gb), (0, 1))  # the lower gate first
        self.assertEqual({g.links[ga][:2], g.links[gb][:2]}, {(0, 1), (0, 2)})
        self.assertAlmostEqual(x0, 4500.0, 2)
        self.assertAlmostEqual(x1, 9500.0, 2)
        self.assertEqual((y0, y1), (2000.0, 2000.0))
        self.assertAlmostEqual(length, 5000.0, 1)  # along the road
        self.assertEqual((r0, r1), (4, 9))
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        self.assertEqual(g.add_crossings(net)["added"], 0)  # never twice

    def test_only_for_the_new_roads(self):
        net = road([(250.0, 2000.0), (14250.0, 2000.0)])
        g = made(self.ROW, [(0, 1), (0, 2)])
        self.assertEqual(g.add_crossings(net, fresh={0, 13})["added"], 0)  # new links in A and C only: none through B
        got = g.add_crossings(net, fresh={6})  # one in B's middle
        self.assertEqual((got["added"], got["named"]), (1, set(range(4, 10))))

    def test_kept_with_the_circles_own(self):
        """The new crossing goes in its circle's range, in order of gates and road links; the rest stay as they were."""
        g = made(self.ROW, [(0, 1), (0, 2)], crossings=[(0, 0, 1, 50, 51), (2, 1, 1, 60, 61)])
        before = crossings(g)
        g.add_crossings(road([(250.0, 2000.0), (14250.0, 2000.0)]))
        after = crossings(g)
        self.assertEqual([r[5:] for r in after[0]], [(0, 1, 4, 9), (0, 1, 50, 51)])
        self.assertEqual(after[2], before[2])
        self.assertEqual([c[4] for c in g.circles], [0, 2, 2, 3])

    def test_never_through_a_block(self):
        """The game moves a unit along a crossing's road without asking whether the ground is walkable: a crossing
        whose road runs through a block (a placed building) would have units drive through it."""
        net = road([(250.0, 2000.0), (14250.0, 2000.0)])
        g = made(self.ROW, [(0, 1), (0, 2)])
        self.assertEqual(g.add_crossings(net, zones=[(7000.0, 2600.0, 400.0)])["added"], 1)  # beside the road
        g = made(self.ROW, [(0, 1), (0, 2)])
        self.assertEqual(g.add_crossings(net, zones=[(7000.0, 2300.0, 400.0)])["added"], 0)  # on it

    def test_a_road_through_three_gates_has_one_for_each_two_in_a_row(self):
        """A road that comes in by W's gate, runs up to N's and back down, and leaves by E's: crossings W-N and N-E,
        none W-E (on the shipped maps no crossing has a third gate's point on its way)."""
        circles = [(10000.0, 2000.0, 6400.0), (2000.0, 2000.0, 3200.0), (18000.0, 2000.0, 3200.0),
                   (10000.0, 9000.0, 3200.0)]  # B, then W, E and N around it
        g = made(circles, [(0, 1), (0, 2), (0, 3)])
        net = road([(0.0, 2000.0), (6000.0, 2000.0), (10000.0, 7400.0), (14000.0, 2000.0), (20000.0, 2000.0)])
        g.add_crossings(net)
        gate = {g.links[k][1]: k for k in g.links_of(0)}  # gate link by B's neighbour
        self.assertEqual(sorted(r[5:7] for r in crossings(g)[0]),
                         sorted([tuple(sorted((gate[1], gate[3]))), tuple(sorted((gate[3], gate[2])))]))

    def test_not_over_ground_a_towns_own_map_keeps_units_off(self):
        """In a circle that owns a local map (a town), units stand only on its local map's circles: a crossing whose
        road runs over a gap in them (a building) isn't made; slips narrower than nav.GAP between them don't count
        (the shipped towns' roads cross many)."""
        net = road([(250.0, 2000.0), (14250.0, 2000.0)])
        local = [(4000.0 + 640.0 * i, 2000.0, 300.0) for i in range(10)]  # 40 apart: slips
        g = made(self.ROW, [(0, 1), (0, 2)], [made(local, [])])
        self.assertEqual(g.add_crossings(net)["added"], 1)
        gap = [c for i, c in enumerate(local) if i not in (4, 5, 6)]  # x 6,220 to 8,180 closed
        g = made(self.ROW, [(0, 1), (0, 2)], [made(gap, [])])
        self.assertEqual(g.add_crossings(net)["added"], 0)


class Index(unittest.TestCase):
    def test_an_index_built_as_the_games_are(self):
        import random
        rnd = random.Random(7)
        circles = [(rnd.uniform(0, 50000), rnd.uniform(0, 50000), rnd.choice((640.0, 1280.0, 3200.0))) for _ in range(57)]
        tree = nav._tree_build(circles)
        seen = []

        def walk(node, depth):  # each edge exactly its half's reach (up to f32), leaves of at most 4
            if node[0] == "leaf":
                self.assertLessEqual(len(node[1]), nav.LEAF)
                seen.extend(node[1])
                return node[1]
            left, right = walk(node[3], depth + 1), walk(node[4], depth + 1)
            self.assertLessEqual(abs(len(left) - len(right)), 1)  # split at the median
            axis = depth % 2
            far, near = struct.unpack("<2f", node[2])
            self.assertGreaterEqual(far, max(circles[i][axis] + circles[i][2] for i in left))
            self.assertLess(far - max(circles[i][axis] + circles[i][2] for i in left), 0.01)
            self.assertLessEqual(near, min(circles[i][axis] - circles[i][2] for i in right))
            self.assertLessEqual(max(circles[i][axis] for i in left), min(circles[i][axis] for i in right))
            return left + right
        walk(tree, 0)
        self.assertEqual(sorted(seen), list(range(57)))
        g = nav._local_graph((0, 0, 65536.0), circles)
        for x, y, r, _l, _c in g.circles[:-1]:  # every circle found through it, right to its rim
            self.assertIsNotNone(g.find(x, y))
            self.assertIsNotNone(g.find(x + r * 0.999, y))
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        self.assertEqual(nav._f32(1578973.3, up=True), 1578973.375)
        self.assertEqual(nav._f32(1578973.3, up=False), 1578973.25)
        self.assertEqual(nav._f32(11400.0, up=True), 11400.0)

    def test_never_deeper_than_the_games_stack(self):
        """The game walks an index with a fixed stack of 32 entries: one deeper than MAX_DEPTH is never written."""
        def depth(node):
            return 0 if node[0] == "leaf" else 1 + max(depth(node[3]), depth(node[4]))
        circles = [(320.0 * i, 320.0 * (i % 7), 640.0) for i in range(60000)]
        self.assertLessEqual(depth(nav._tree_build(circles)), nav.MAX_DEPTH)
        deep = ["leaf", [0]]
        for _ in range(nav.MAX_DEPTH + 1):
            deep = ["branch", 1, struct.pack("<2f", 1.0, 0.0), deep, ["leaf", [1]]]
        with self.assertRaisesRegex(nav.NavError, "more than 24 levels deep"):
            nav._tree_write(deep)

    def test_a_circle_near_water_is_tested_all_over(self):
        self.assertFalse(nav._wet(river, 9000.0, 2000.0, 1280.0))
        self.assertTrue(nav._wet(river, 10500.0, 2000.0, 1280.0))  # its middle is dry, its rim isn't
        self.assertFalse(nav._wet(None, 13000.0, 2000.0, 1280.0))


class NewWater(unittest.TestCase):
    """Ground under water is never walkable on a shipped map, but the water and height brushes change only the ground
    files: the build blocks the new water (nav.water_blocks)."""

    def test_new_water_is_covered_and_the_shore_kept(self):
        def old(x, y):  # a river, and a pond the stroke drains
            return 0.0 <= x <= 10000.0 or math.hypot(x - 60000.0, y - 30000.0) < 3000.0

        def new(x, y):  # the river, and a new lake running into it
            return 0.0 <= x <= 10000.0 or math.hypot(x - 30000.0, y - 30000.0) < 8000.0 or (
                10000.0 <= x <= 30000.0 and abs(y - 30000.0) < 1500.0)
        import math
        zones, drained = nav.water_blocks(old, new, [(30000.0, 30000.0, 21000.0), (60000.0, 30000.0, 5000.0)])
        self.assertTrue(zones)
        for i in range(-60, 61):  # every new water point (inside the strokes) is in a block, the shore just outside
            for j in range(-60, 61):
                x, y = 30000.0 + 300.0 * i, 30000.0 + 300.0 * j
                inside = any(math.hypot(x - zx, y - zy) <= zr for zx, zy, zr in zones)
                deep = math.hypot(x - 30000.0, y - 30000.0) < 7300.0 or (10700.0 <= x <= 29000.0 and abs(y - 30000.0) < 800.0)
                if deep:
                    self.assertTrue(inside, (x, y))
                if not (old(x, y) or new(x, y)) and min(math.hypot(x - 30000.0, y - 30000.0) - 8000.0,
                                                        abs(y - 30000.0) - 1500.0 if 10000.0 <= x <= 30000.0 else 1e9) > 700.0:
                    self.assertFalse(inside, (x, y))  # dry ground more than a step from the water stays open
        self.assertTrue(drained)
        self.assertTrue(all(math.hypot(x - 60000.0, y - 30000.0) < 3000.0 for x, y in drained))
        self.assertLess(len(zones), 200)  # (about two a step of shore: the graphs' blocking stays quick)
        self.assertEqual(nav.water_blocks(old, old, [(30000.0, 30000.0, 21000.0)]), ([], []))
        # blocked in the graphs: no point of the lake is walkable afterwards, ground well off it still is
        circles = [(x, y, 6400.0) for x in range(14000, 50000, 8000) for y in range(14000, 50000, 8000)]
        pairs = [(a, b) for a in range(len(circles)) for b in range(a + 1, len(circles))
                 if nav._meeting(circles[a], circles[b]) is not None]
        g = made([(float(x), float(y), r) for x, y, r in circles], pairs)
        self.assertTrue(g.walkable(30000.0, 30000.0))
        g.block(zones)
        g = nav.Graph.read(g.to_bytes())
        for i in range(-25, 26):
            for j in range(-25, 26):
                x, y = 30000.0 + 300.0 * i, 30000.0 + 300.0 * j
                if math.hypot(x - 30000.0, y - 30000.0) < 7300.0:
                    self.assertFalse(g.walkable(x, y), (x, y))
        self.assertTrue(g.walkable(44000.0, 44000.0))


class Built(unittest.TestCase):
    """maps/<map>/movement.toml in a mod, built into the modded copy's DataMap_Win.dat."""

    def test_blocked_ground_in_the_modded_copy(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from fixtures import make_edat
        from test_build import PACK, write_mod
        from rusemod.build import build_and_write, load_mod
        from rusemod.cover import member
        from rusemod.edat import Edat
        from ruse_mod_engine import sdb
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "steamapps" / "common" / "R.U.S.E"
            rev = game / "Data" / "PC" / "190852"
            rev.mkdir(parents=True)
            (game / "RUSE.exe").write_bytes(b"MZ")
            (rev / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
            win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
                b"roads", row().to_bytes(), row().to_bytes(), b"cover")) + b"tail", {})
            (rev / "DataMap_Win.dat").write_bytes(
                make_edat([("dir", "datasmap/blitz/".replace("/", "\\"), [("file", "mapinfo.win", win)])]))
            (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            folder = write_mod(root / "mods", "walls", {})
            (folder / "maps" / "Blitz").mkdir(parents=True)
            (folder / "maps" / "Blitz" / "movement.toml").write_text(
                '[[block]]\nx = 10800.0\ny = 2000.0\nradius = 400.0\nunits = "vehicles"\n', encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            self.assertIn("movement: Blitz, from walls", lines)
            arc = Edat((root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
            out = bytes(arc.read(arc.find(member("Blitz"))))
            self.assertEqual(hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + out[24:]).digest(), out[8:24])
            bufs = sdb.split_mapinfo(out)[1]
            self.assertEqual(bufs[1], row().to_bytes())  # infantry untouched
            self.assertEqual(nav.Graph.read(bufs[2]).circles[2][2], 0.0)  # vehicles: C emptied
            self.assertEqual((bufs[0], bufs[3]), (b"roads", b"cover"))


if __name__ == "__main__":
    unittest.main()
