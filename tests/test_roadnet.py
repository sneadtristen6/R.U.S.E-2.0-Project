"""The road network (rusemod.roadnet): mapinfo.win's buffer 0 read, written back the game's way, and a road added."""
import math
import struct
import unittest

from rusemod.roadnet import LEAF_MOST, POINT_STEP, RoadNet, RoadNetError, _resample, build_tree


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

    def test_costs_are_a_tenth_of_the_distance(self):
        net = ring()
        a, b, cost = net.links[0]
        self.assertEqual(cost, round(math.dist(net.points[a], net.points[b]) / 10))

    def test_the_index_the_game_way(self):
        net = ring(200, 400000.0)
        self.assertEqual(set(leaves(net.tree)), set(range(200)))
        self.assertTrue(depth_ok(net.tree, net.points, net.links))

        def leaf_sizes(node):
            return [len(node[1])] if node[0] == "leaf" else leaf_sizes(node[2]) + leaf_sizes(node[3])
        self.assertLessEqual(max(leaf_sizes(net.tree)), LEAF_MOST + 2)  # a split's crossing links can add a couple
        self.assertGreater(len(leaf_sizes(net.tree)), 200 // LEAF_MOST)

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

    def test_the_file(self):
        from rusemod.roadnet import Road, parse_roads, roads_toml
        import tomllib
        roads = [Road([(1.0, 2.0), (3.5, 4.0)], 5000.0)]
        self.assertEqual(parse_roads(tomllib.loads(roads_toml(roads, "made by hand"))["road"]), roads)
        for bad, why in (([{"points": [[1, 2]]}], "at least two"), ([{"points": [[1, 2], [3]]}], r"\[x, y\]"),
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
