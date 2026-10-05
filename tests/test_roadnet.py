"""The road network (rusemod.roadnet): mapinfo.win's buffer 0 read, written back the game's way, and a road added."""
import math
import struct
import unittest

from rusemod.roadnet import (LEAF_MOST, MAX_DEPTH, POINT_STEP, RoadNet, RoadNetError, _resample, _tree_write,
                             build_tree, cost_word)


def leaves(node):
    return node[1] if node[0] == "leaf" else leaves(node[2]) + leaves(node[3])


def depth_ok(node, points, links, depth=0):
    """Every branch splits x at even depths and y at odd ones: its left links reach down to the split, its right
    links up to it."""
    if node[0] == "leaf":
        return True
    _, split, left, right = node
    axis = depth % 2
    ok = all(min(points[links[i][0]][axis], points[links[i][1]][axis]) <= split for i in leaves(left))
    ok = ok and all(max(points[links[i][0]][axis], points[links[i][1]][axis]) >= split for i in leaves(right))
    return ok and depth_ok(left, points, links, depth + 1) and depth_ok(right, points, links, depth + 1)


def ring(n=24, r=100000.0):
    """A ring road of n points around (500000, 500000)."""
    pts = [(500000 + r * math.cos(2 * math.pi * i / n), 500000 + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    net = RoadNet(pts, [])
    net.links = [(i, (i + 1) % n, net._cost(i, (i + 1) % n)) for i in range(n)]
    net.tree = build_tree(net.points, net.links)
    return net


class Layout(unittest.TestCase):
    def test_written_and_read_back(self):
        net = ring()
        data = net.to_bytes()
        n, m, o1, o2, o3, o4 = struct.unpack_from("<HH4I", data, 0)
        self.assertEqual((n, m, o1, o2, o3), (24, 24, 20, 20 + 12 * 24, 20 + 12 * 24 + 6 * 24))
        self.assertEqual(o4, o3 + 4 * 24)  # each link in two points' lists
        w, x, y = struct.unpack_from("<Iff", data, 20 + 12)  # point 1: links 0 and 1, from list position 2
        self.assertEqual((w >> 8, w & 0xFF), (2, 2))
        again = RoadNet.read(data)
        self.assertEqual(again.to_bytes(), data)
        self.assertEqual(len(again.points), 24)
        self.assertEqual(again.links, net.links)

    def test_a_links_word_is_what_the_game_keeps_once_loaded(self):
        """The game works bits 1-15 out again from the points (the distance / 20, at most 0x7FFF) and keeps bit 0, a
        flag set on most shipped links where vehicles can go: a new link has it where the vehicles' graph has ground
        at the link's middle."""
        net = ring()
        a, b, word = net.links[0]
        self.assertEqual(word, min(int(math.dist(net.points[a], net.points[b]) / 20), 0x7FFF) << 1 | 1)
        self.assertEqual((cost_word(4599.0, True), cost_word(4600.0, False), cost_word(1e9, True)),
                         (229 << 1 | 1, 230 << 1, 0xFFFF))
        net = ring()
        first = len(net.links)
        net.add_road([(380000.0, 500000.0), (420000.0, 500000.0)], join=0.0, open_at=lambda x, y: x < 400000.0)
        for a, b, word in net.links[first:]:
            (ax, ay), (bx, by) = net.points[a], net.points[b]
            self.assertEqual(word & 1, int((ax + bx) / 2 < 400000.0))
            self.assertEqual(word >> 1, min(int(math.hypot(bx - ax, by - ay) / 20), 0x7FFF))
        self.assertEqual({w & 1 for _a, _b, w in net.links[first:]}, {0, 1})

    def test_the_index_the_game_way(self):
        net = ring(200, 400000.0)
        self.assertEqual(set(leaves(net.tree)), set(range(200)))
        self.assertTrue(depth_ok(net.tree, net.points, net.links))

        def leaf_sizes(node):
            return [len(node[1])] if node[0] == "leaf" else leaf_sizes(node[2]) + leaf_sizes(node[3])
        self.assertLessEqual(max(leaf_sizes(net.tree)), LEAF_MOST + 2)  # a split's crossing links can add a couple
        self.assertGreater(len(leaf_sizes(net.tree)), 200 // LEAF_MOST)

    def test_the_index_is_never_deeper_than_the_games_stack(self):
        """The game walks the index with a fixed stack of 32 entries: long links that cross every split (they go into
        both halves, so splitting never shrinks them) once built an index 41 levels deep."""
        def depth(node):
            return 0 if node[0] == "leaf" else 1 + max(depth(node[2]), depth(node[3]))
        for build in (lambda k: ((100000.0 + 200 * k, 100000.0), (1200000.0 + 200 * k, 1200000.0)),  # long diagonals
                      lambda k: ((1000.0 * k, 0.0), (1000.0 * k + 900000.0, 900000.0 - 3000.0 * k)),   # a fan of them
                      lambda k: ((0.0, 1000.0 * k), (500000.0, 1000.0 * k + 1.0))):                  # near parallels
            net = RoadNet()
            for k in range(60):
                net.points += list(build(k))
                net.links.append((len(net.points) - 2, len(net.points) - 1, 0))
            net.tree = build_tree(net.points, net.links)
            self.assertLessEqual(depth(net.tree), MAX_DEPTH)
            self.assertEqual(set(leaves(net.tree)), set(range(60)))
            self.assertTrue(depth_ok(net.tree, net.points, net.links))
            self.assertEqual(RoadNet.read(net.to_bytes()).to_bytes(), net.to_bytes())
        deep = ["leaf", [0]]
        for _ in range(MAX_DEPTH + 1):
            deep = ["branch", 1.0, deep, ["leaf", [0]]]
        with self.assertRaisesRegex(RoadNetError, "more than 24 levels deep"):
            _tree_write(deep)

    def test_mistakes(self):
        with self.assertRaisesRegex(RoadNetError, "shorter than its header"):
            RoadNet.read(b"\0" * 8)
        data = bytearray(ring().to_bytes())
        struct.pack_into("<I", data, 20, 12345)  # point 0's list start no longer matches its links
        with self.assertRaisesRegex(RoadNetError, "point lists don't match"):
            RoadNet.read(bytes(data))


class AddingARoad(unittest.TestCase):
    def test_a_road_joins_the_ring_at_both_ends(self):
        net = ring()
        before = (len(net.points), len(net.links))
        east, west = net.points[0], net.points[12]
        got = net.add_road([(east[0] + 5000, east[1]), (500000, 500000), (west[0] - 5000, west[1])], join=20000.0)
        self.assertEqual(got["joined"], 2)
        self.assertEqual(len(net.links) - before[1], got["links"])
        self.assertEqual(got["links"], got["points"] + 1)  # a chain, plus a link at each end
        new = set(range(before[1], len(net.links)))
        self.assertIn(0, {a for a, b, _ in (net.links[i] for i in new)} | {b for a, b, _ in (net.links[i] for i in new)})
        self.assertEqual(set(leaves(net.tree)), set(range(len(net.links))))
        self.assertTrue(depth_ok(net.tree, net.points, net.links))
        again = RoadNet.read(net.to_bytes())  # still the game's layout
        self.assertEqual(len(again.links), len(net.links))
        degrees = [len(mine) for mine in again._lists()]
        self.assertEqual((degrees[0], degrees[12]), (3, 3))  # two new junctions

    def test_a_road_far_from_any_other_is_a_dead_end_both_ways(self):
        net = ring()
        got = net.add_road([(0.0, 0.0), (50000.0, 0.0)], join=20000.0)
        self.assertEqual(got["joined"], 0)
        self.assertEqual(got["links"], got["points"] - 1)
        with self.assertRaisesRegex(RoadNetError, "at least two points"):
            net.add_road([(1.0, 1.0)])

    def test_points_about_a_step_apart(self):
        pts = _resample([(0.0, 0.0), (10000.0, 0.0), (10000.0, 10000.0)], POINT_STEP)
        gaps = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        self.assertEqual((pts[0], pts[-1]), ((0.0, 0.0), (10000.0, 10000.0)))
        self.assertTrue(all(g <= POINT_STEP * 1.26 for g in gaps), gaps)
        self.assertGreaterEqual(len(pts), 20000 / POINT_STEP)


class Cutting(unittest.TestCase):
    def test_links_through_a_zone_go_with_their_orphan_point(self):
        net = ring()
        east = net.points[0]
        gone = net.cut([(east[0], east[1], 1000.0)])  # a small circle on the ring's east point
        self.assertEqual(gone, 2)  # the two links that met there
        self.assertEqual((len(net.points), len(net.links)), (23, 22))  # the point only they used is gone too
        self.assertNotIn(east, net.points)
        self.assertEqual(set(leaves(net.tree)), set(range(22)))
        self.assertTrue(depth_ok(net.tree, net.points, net.links))
        again = RoadNet.read(net.to_bytes())
        self.assertEqual((again.links, again.to_bytes()), (net.links, net.to_bytes()))
        degrees = [len(mine) for mine in again._lists()]
        self.assertEqual(sorted(degrees)[:2], [1, 1])  # the ring is now an arc with two ends
        self.assertEqual(net.cut([(0.0, 0.0, 10.0)]), 0)  # nothing there: untouched
        net = ring()
        (ax, ay), (bx, by) = net.points[0], net.points[1]
        before = list(net.links)
        number = {}
        gone = net.cut([((ax + bx) / 2, (ay + by) / 2, 500.0)], number)
        self.assertEqual((gone, len(net.points)), (1, 24))  # a link's middle: both its points still serve others
        went = [i for i, new in number.items() if new is None]
        self.assertEqual(len(went), 1)  # the movement graphs' crossings follow these numbers (nav.renumber_roads)
        self.assertEqual(sorted(n for n in number.values() if n is not None), list(range(len(net.links))))
        self.assertEqual(len(number), len(before))
        self.assertTrue(all(net.links[new][:2] == before[old][:2] for old, new in number.items() if new is not None))


class ModRoads(unittest.TestCase):
    """maps/<map>/roads.toml in a mod: read, written, and built into the modded copy's road network."""

    def test_a_road_that_joins_nothing_is_refused(self):
        """Every shipped road network is one piece, and the game's road search runs over it alone: a road whose ends
        join no road would leave supply routes to it failing, so the build refuses it, naming it."""
        from rusemod import nav
        from rusemod.cover import member
        from rusemod.roadnet import Road, apply_roads
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
        net = ring()
        self.assertEqual([len(p) for p in net.parts()], [24])
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), b"infantry", b"vehicles", b"cover")) + b"tail", {})
        read = {member("Blitz"): win}.get
        east, west = net.points[0], net.points[12]
        across = Road([(east[0] + 3000, east[1]), (west[0] - 3000, west[1])])
        far = Road([(0.0, 0.0), (50000.0, 0.0)])
        new, _notes = apply_roads(read, "Blitz", [across])  # joined at both ends: fine
        self.assertIn(member("Blitz"), new)
        with self.assertRaisesRegex(RoadNetError, r"road 2 \(its ends joined no road within 77 m\) would be cut off"):
            apply_roads(read, "Blitz", [across, far])
        new, _notes = apply_roads(read, "Blitz", [far, Road([(50000.0, 0.0), (east[0] + 3000, east[1])])])
        self.assertIn(member("Blitz"), new)  # a later road joins it to the rest: one piece again

    def test_units_follow_the_new_road(self):
        """A new road gets crossings in both movement graphs, through every circle it enters and leaves by two gates,
        so units plan along it; never through a block their graph's units are kept out of."""
        from test_nav import crossings, made
        from rusemod import nav
        from rusemod.cover import member
        from rusemod.roadnet import Road, apply_roads
        from ruse_mod_engine import sdb
        row = [(400000.0 + 50000.0 * i, 500000.0, 25600.0) for i in range(5)]  # overlapping by 1,200 along the road
        g = made(row, [(i, i + 1) for i in range(4)])
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 1000000.0, 1000000.0)
        net = ring()
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})
        read = {member("Blitz"): win}.get
        east, west = net.points[0], net.points[12]
        across = Road([(east[0] - 3000, east[1] + 100), (west[0] + 3000, west[1] + 100)])
        new, notes = apply_roads(read, "Blitz", [across])
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        self.assertEqual(bufs[3], b"cover")
        for k in (1, 2):
            cross = crossings(nav.Graph.read(bufs[k]))
            self.assertEqual(sorted(cross), [1, 2, 3])  # the three middle circles; the ends have one gate each
            self.assertTrue(all(r[7] >= 24 and r[8] >= 24 for rs in cross.values() for r in rs))  # on the new links
        self.assertIn("vehicles: 3 crossing(s) in 3 circle(s), so units follow the new roads", notes)
        block = nav.Block(500000.0, 500000.0, 2000.0, "vehicles")  # on the road in the middle circle
        new, notes = apply_roads(read, "Blitz", [across], [block])
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        self.assertEqual(sorted(crossings(nav.Graph.read(bufs[1]))), [1, 2, 3])  # infantry: not kept out
        self.assertEqual(sorted(crossings(nav.Graph.read(bufs[2]))), [1, 3])
        short = Road([(east[0] - 3000, east[1] + 100), (east[0] - 9000, east[1] + 100)])  # in the east circle only
        _new, notes = apply_roads(read, "Blitz", [across, short])
        self.assertIn("infantry: road 2 has no crossing (it runs through no circle of the movement from one gate to "
                      "another on open ground): units go across country there, not along it", notes)

    def test_the_maps_own_roads_taken_out(self):
        """take_out = ["roads"]: the map's road network left with no point and no link, and every crossing of both
        movement graphs gone with it (a crossing names road links); the rest of the file as it was. A road the mod
        adds then goes into the empty network, one piece."""
        from test_nav import crossings, made
        from rusemod import nav
        from rusemod.cover import member
        from rusemod.roadnet import Road, RoadNet, apply_roads, take_out_roads
        from ruse_mod_engine import sdb
        row = [(400000.0 + 50000.0 * i, 500000.0, 25600.0) for i in range(5)]
        g = made(row, [(i, i + 1) for i in range(4)])
        head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 1000000.0, 1000000.0)
        net = ring()
        win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
            net.to_bytes(), g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})
        east, west = net.points[0], net.points[12]
        across = Road([(east[0] - 3000, east[1] + 100), (west[0] + 3000, west[1] + 100)])
        roads = apply_roads({member("Blitz"): win}.get, "Blitz", [across])[0][member("Blitz")]
        self.assertTrue(crossings(nav.Graph.read(sdb.split_mapinfo(roads)[1][1])))
        out, notes = take_out_roads(roads)
        bufs = sdb.split_mapinfo(out)[1]
        empty = RoadNet.read(bufs[0])
        self.assertEqual((empty.points, empty.links), ([], []))
        for k in (1, 2):
            after = nav.Graph.read(bufs[k])
            self.assertEqual(crossings(after), {})
            self.assertEqual(after.circles[:-1], [c[:4] + (0,) for c in nav.Graph.read(
                sdb.split_mapinfo(roads)[1][k]).circles[:-1]])  # the circles stay, none with a crossing
        self.assertEqual((bufs[3], sdb.split_mapinfo(out)[2]), (b"cover", sdb.split_mapinfo(roads)[2]))
        self.assertIn("crossing(s) of them", notes[0])
        self.assertEqual(take_out_roads(out), (out, []))          # nothing left to take out: the same bytes
        new, _notes = apply_roads({member("Blitz"): out}.get, "Blitz", [Road([(0.0, 0.0), (90000.0, 0.0)])])
        self.assertEqual(len(RoadNet.read(sdb.split_mapinfo(new[member("Blitz")])[1][0]).parts()), 1)

    def test_take_out_in_the_file(self):
        import tomllib
        from rusemod.roadnet import Road, TakeOut, parse_take_out, roads_toml, take_out_of
        text = roads_toml([Road([(1.0, 2.0), (3.0, 4.0)])], "made by hand", TakeOut(True, True))
        data = tomllib.loads(text)
        self.assertEqual((parse_take_out(data["take_out"]), len(data["road"])), ([TakeOut(True, True)], 1))
        self.assertEqual(parse_take_out(["bridges"]), [TakeOut(False, True)])
        self.assertEqual(parse_take_out(None), [])
        for bad in ("roads", ["road"], [1]):
            with self.assertRaises(RoadNetError):
                parse_take_out(bad)
        self.assertEqual(take_out_of([TakeOut(True, False), "a road", TakeOut(False, True)]), TakeOut(True, True))
        self.assertNotIn("take_out", roads_toml([], "", TakeOut()))

    def test_the_file(self):
        from rusemod.roadnet import Road, parse_roads, roads_toml
        import tomllib
        roads = [Road([(1.0, 2.0), (3.5, 4.0)], 5000.0), Road([(5.0, 6.0), (7.0, 8.0)], keep_trees=True)]
        text = roads_toml(roads, "made by hand")
        self.assertEqual(parse_roads(tomllib.loads(text)["road"]), roads)
        self.assertEqual(text.count("keep_trees = true"), 1)  # written only when it's on
        for bad, why in (([{"points": [[1, 2]]}], "at least two"), ([{"points": [[1, 2], [3]]}], r"\[x, y\]"),
                         ([{"points": [[1, 2], [3, 4]], "keep_trees": "yes"}], "keep_trees must be true or false"),
                         ([{"points": [[1, 2], [3, True]]}], r"\[x, y\]"), ([{"points": [[1, 2], [3, 4]], "join": -1}], "join"),
                         ([{"points": [[1, 2], [3, 4]], "width": 3}], "unknown key 'width'"), (["x"], "isn't a table")):
            with self.assertRaisesRegex(RoadNetError, why):
                parse_roads(bad)

    def test_built_into_the_modded_copy(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from fixtures import make_edat
        from test_build import PACK, write_mod
        from rusemod import nav
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
            net = ring()
            win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
                net.to_bytes(), b"infantry", b"vehicles", b"cover")) + b"tail", {})
            (rev / "DataMap_Win.dat").write_bytes(
                make_edat([("dir", "datasmap/blitz/".replace("/", "\\"), [("file", "mapinfo.win", win)])]))
            (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            folder = write_mod(root / "mods", "bypass", {})
            (folder / "maps" / "Blitz").mkdir(parents=True)
            east, west = net.points[0], net.points[12]
            (folder / "maps" / "Blitz" / "roads.toml").write_text(
                f"[[road]]\npoints = [[{east[0] + 3000}, {east[1]}], [{west[0] - 3000}, {west[1]}]]\n", encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            self.assertIn("roads: Blitz, from bypass", lines)
            arc = Edat((root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
            out = bytes(arc.read(arc.find(member("Blitz"))))
            self.assertEqual(hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + out[24:]).digest(), out[8:24])
            bufs = sdb.split_mapinfo(out)[1]
            built = RoadNet.read(bufs[0])
            self.assertGreater(len(built.points), 24 + 50)  # the road across the ring, a point every ~9 m
            self.assertEqual([len(mine) for mine in built._lists()][0], 3)  # joined to the ring's east point
            self.assertEqual((bufs[1], bufs[2], bufs[3]), (b"infantry", b"vehicles", b"cover"))


if __name__ == "__main__":
    unittest.main()
