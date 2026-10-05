"""Sectors over the whole map (rusemod.sectors) on a made-up map: two square sectors side by side in a bigger map, their
zone map made by the module itself from a one-part template (no game files). Checked: every place of the map ends up
in a sector, the sectors' own ground keeps its number, the open map goes to the nearest one, the zones keep the rules
every shipped zone keeps, and the zone map says the same as the drawn sectors."""
import math
import struct
import unittest

from test_kdt import hand_storage, make_kdt
from rusemod import sectors as S
from rusemod.kdt import Kdt, Leaf, encode_indices, encode_main_node, encode_trilists, encode_tree
from rusemod.scenario import Scenario, Zone

try:
    from rusemod.numpy2 import np
except ImportError:  # the module needs numpy, as the apps have it
    np = None

W, H = 262144.0, 196608.0
RING_A = [(30000.0, 40000.0), (110000.0, 40000.0), (110000.0, 120000.0), (30000.0, 120000.0)]
RING_B = [(110000.0, 40000.0), (190000.0, 40000.0), (190000.0, 120000.0), (110000.0, 120000.0)]


def template() -> bytes:
    """A zone map with one part holding one triangle (the layout rusemod.sectors.zone_map writes over)."""
    opaque = {"counts": [3], "indices": [encode_indices([0, 1, 2])], "trees": [encode_tree(Leaf(1))],
              "trilists": [encode_trilists([[0]])], "main": encode_main_node([(5, 0, 0, 0.0)])}
    storage, off = hand_storage(positions=[[(0, 0, 0), (100, 0, 0), (0, 100, 0)]], parents=[[0, 0, 0]],
                                normals=[[(0.0, 0.0, 1.0)] * 3], opaque=opaque)
    return make_kdt(storage, off, subtree_count=1, triangle_count=1)


def blank(number: int, anchor) -> Zone:
    return Zone(number, f"zone_{number}", anchor, [(0.0, 0.0, 0.0, 22186.9, 0.0)], [], [], (0, 0, 0, 0), (0, 0),
                [1 - number])


def made_up(rings=(RING_A, RING_B), anchors=((70000.0, 80000.0, 0.0), (150000.0, 80000.0, 0.0))):
    """A scenario whose sectors are `rings` (drawn by zone_mesh) and its zone map (zone_map)."""
    zones = [S.zone_mesh(blank(n, a), list(r), lambda x, y: 100.0)[0] for n, (r, a) in enumerate(zip(rings, anchors))]
    kdt = S.zone_map(template(), {n: list(r) for n, r in enumerate(rings)}, W, H)
    return Scenario(9, zones, []), kdt


def level_at(kdt: Kdt, x: float, y: float):
    """The number the zone map gives at (x, y): its highest triangle there, height / LEVEL rounded (None: none)."""
    pos = [(kdt.to_world(0, p[0]), kdt.to_world(1, p[1]), kdt.to_world(2, p[2])) for p in kdt.positions(0)]
    idx = kdt.indices(0)
    best = None
    for t in range(0, len(idx), 3):
        a, b, c = (pos[v] for v in idx[t:t + 3])
        d1 = (x - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (y - b[1])
        d2 = (x - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (y - c[1])
        d3 = (x - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y - a[1])
        if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
            lv = int(math.floor(a[2] / S.LEVEL + 0.5))
            best = lv if best is None else max(best, lv)
    return best


def area2(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class WholeMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s, cls.kdt = made_up()
        cls.res = S.over_whole_map(cls.s, cls.kdt, W, H, lambda x, y: 50.0, most=512)

    def test_every_place_is_in_a_sector_and_the_old_ground_keeps_its_number(self):
        new = Kdt(self.res.kdt)
        self.assertEqual(new.bounds_max, (W, H, S.LEVEL))
        for i in range(0, 41):
            for j in range(0, 31):
                x, y = 1.0 + (W - 2) * i / 40, 1.0 + (H - 2) * j / 30
                got = level_at(new, x, y)
                self.assertIn(got, (0, 1), (x, y))
                if 30000 < x < 110000 and 40000 < y < 120000:
                    self.assertEqual(got, 0, (x, y))
                elif 110000 < x < 190000 and 40000 < y < 120000:
                    self.assertEqual(got, 1, (x, y))
                elif x < 100000:
                    self.assertEqual(got, 0, (x, y))   # nearer the left square
                elif x > 200000:
                    self.assertEqual(got, 1, (x, y))
        self.assertTrue((self.res.labels >= 0).all())

    def test_the_zones_keep_the_shipped_rules(self):
        for z in self.res.zones:
            first, n = z.border_vertices
            ring = [z.vertices[i][:2] for i in range(first, first + n)]
            self.assertGreater(S.area(ring), 0)                                    # counter-clockwise
            self.assertTrue(all(z.vertices[i][4] == 0.0 for i in range(first, first + n)))
            self.assertTrue(all(z.vertices[i][4] == 1.0 for i in range(first + n, first + 2 * n)))
            self.assertEqual(z.border_triangles, (z.border_triangles[0], 2 * n, first, 2 * n))
            self.assertTrue(all(v[3] == 22186.9 for v in z.vertices))             # the 4th value kept
            self.assertTrue(all(v[2] == 50.0 for v in z.vertices))                # the ground's height
            self.assertEqual(len(z.parts), 2)
            ay = z.anchor[1]
            for k, (ft, nt, fv, nv) in enumerate(z.parts):
                self.assertGreater(nt, 0)
                ys = [z.vertices[i][1] for i in range(fv, fv + nv)]
                self.assertTrue(max(ys) <= ay if k == 0 else min(ys) >= ay)
                for t in z.triangles[ft:ft + nt]:
                    self.assertTrue(all(fv <= i < fv + nv for i in t))
                    self.assertGreater(area2(*(z.vertices[i][:2] for i in t)), 0)
            bft, bnt, _bfv, _bnv = z.border_triangles
            self.assertEqual(bft + bnt, len(z.triangles))
            for t in z.triangles[bft:]:
                self.assertGreaterEqual(area2(*(z.vertices[i][:2] for i in t)), 0)
            fill = sum(area2(*(z.vertices[i][:2] for i in t)) for ft, nt, _fv, _nv in z.parts
                       for t in z.triangles[ft:ft + nt]) / 2
            self.assertAlmostEqual(fill, S.area(ring), delta=S.area(ring) * 1e-9)  # the parts cover the outline

    def test_the_two_halves_reach_the_map_edges_and_border_each_other(self):
        a, b = (z for z in self.res.zones)
        self.assertEqual(a.outline, [1])
        self.assertEqual(b.outline, [0])
        total = sum(S.area([z.vertices[i][:2] for i in range(z.border_vertices[0], sum(z.border_vertices))])
                    for z in self.res.zones)
        self.assertAlmostEqual(total, W * H, delta=W * H * 1e-9)

    def test_the_scenario_reads_back(self):
        self.s.zones = self.res.zones
        back = Scenario.read(self.s.to_bytes())
        self.assertEqual([z.number for z in back.zones], [0, 1])
        f32 = [struct.unpack("<5f", struct.pack("<5f", *v)) for v in self.res.zones[0].vertices]   # as stored
        self.assertEqual(back.zones[0].vertices, f32)
        self.assertEqual(back.zones[1].triangles, self.res.zones[1].triangles)

    def test_a_sector_inside_another_is_refused(self):
        inner = [(60000.0, 60000.0), (80000.0, 60000.0), (80000.0, 80000.0), (60000.0, 80000.0)]
        outer = [(20000.0, 20000.0), (150000.0, 20000.0), (150000.0, 150000.0), (20000.0, 150000.0)]
        zones = [S.zone_mesh(blank(0, (30000.0, 30000.0, 0.0)), outer, lambda x, y: 0.0)[0],
                 S.zone_mesh(blank(1, (70000.0, 70000.0, 0.0)), inner, lambda x, y: 0.0)[0]]
        # the zone map gives the inner square its own number over the outer one: the higher triangle wins
        kdt = S.zone_map(template(), {0: outer, 1: inner}, W, H)
        with self.assertRaisesRegex(S.SectorError, "inside it"):
            S.over_whole_map(Scenario(9, zones, []), kdt, W, H, None, most=512)


class Pieces(unittest.TestCase):
    def test_triangulate_covers_a_concave_outline(self):
        ell = [(0, 0), (40, 0), (40, 10), (10, 10), (10, 30), (0, 30)]
        tris = S.triangulate(ell)
        self.assertEqual(len(tris), len(ell) - 2)
        self.assertTrue(all(area2(*(ell[i] for i in t)) > 0 for t in tris))
        self.assertEqual(sum(area2(*(ell[i] for i in t)) for t in tris) / 2, S.area(ell))

    def test_triangulate_leaves_out_a_point_on_a_straight_side(self):
        square = [(0, 0), (5, 0), (10, 0), (10, 10), (0, 10)]
        tris = S.triangulate(square)
        self.assertEqual(sum(area2(*(square[i] for i in t)) for t in tris) / 2, 100)
        self.assertTrue(all(area2(*(square[i] for i in t)) > 0 for t in tris))

    def test_simplify_keeps_the_ends_and_each_points_own_tolerance(self):
        stairs = [(float(i // 2 + i % 2), float(i // 2)) for i in range(21)]   # a staircase, 1 high and wide
        self.assertEqual(S.simplify(stairs, 2.0), [stairs[0], stairs[-1]])
        tight = [0.1] * len(stairs)
        self.assertEqual(len(S.simplify(stairs, tight)), len(stairs))
        loop = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
        self.assertEqual(S.simplify(loop, 0.5), loop)

    def test_is_simple(self):
        self.assertTrue(S.is_simple([(0, 0), (10, 0), (10, 10), (0, 10)]))
        self.assertFalse(S.is_simple([(0, 0), (10, 10), (10, 0), (0, 10)]))      # a bow tie
        self.assertFalse(S.is_simple([(0, 0), (0, 10), (10, 10), (10, 0)]))      # clockwise
        self.assertFalse(S.is_simple([(0, 0), (10, 0), (5, 0), (5, 5)]))         # a side folding back

    def test_inner_ring_keeps_the_band_and_narrows_only_where_it_must(self):
        square = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        inner, widths = S.inner_ring(square, 10.0)
        self.assertEqual(widths, [10.0] * 4)
        for (x, y), (ix, iy) in zip(square, inner):
            self.assertAlmostEqual(abs(ix - x), 10.0)
            self.assertAlmostEqual(abs(iy - y), 10.0)
        thin = [(0.0, 0.0), (100.0, 0.0), (100.0, 6.0), (0.0, 6.0)]              # 6 wide: a band of 10 can't fit
        inner, widths = S.inner_ring(thin, 10.0)
        self.assertTrue(all(w < 3.0 for w in widths))

    def test_map_size_from_the_movement_file(self):
        win = b"INFOIA\r\n" + bytes(32) + struct.pack("<2f", 3932160.0, 2621440.0) + bytes(16)
        self.assertEqual(S.map_size(win), (3932160.0, 2621440.0))
        with self.assertRaises(S.SectorError):
            S.map_size(b"nope" + bytes(60))


class Setting(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(S.parse_sectors(None), [])
        self.assertEqual(S.parse_sectors({"whole_map": True}), [S.Sectors(True)])
        self.assertEqual(S.parse_sectors({}), [S.Sectors(False)])
        for bad in ({"whole_map": "yes"}, {"whole": True}, [1]):
            with self.assertRaises(S.SectorError):
                S.parse_sectors(bad)

    def test_the_last_mod_decides_and_the_table_reads_back(self):
        import tomllib
        self.assertTrue(S.whole_map_of(["a move", S.Sectors(True)]))
        self.assertFalse(S.whole_map_of([S.Sectors(True), S.Sectors(False)]))
        self.assertFalse(S.whole_map_of(["a move"]))
        self.assertEqual(S.sectors_toml(S.Sectors(False)), "")
        self.assertEqual(S.parse_sectors(tomllib.loads(S.sectors_toml(S.Sectors(True)))["sectors"]), [S.Sectors(True)])


@unittest.skipIf(np is None, "numpy (the apps carry it) isn't here")
class Apply(unittest.TestCase):
    def test_every_scenario_with_a_zone_map_and_none_without(self):
        from rusemod.cover import member as movement_member
        from rusemod.scenario import folder_of
        s, kdt = made_up()
        folder = folder_of("TestMap")
        win = b"INFOIA\r\n" + bytes(32) + struct.pack("<2f", W, H) + bytes(16)
        pack = {movement_member("TestMap"): win, folder + "a.scenario": s.to_bytes(),
                folder + "zonebluff\\a.kdt": kdt, folder + "b.scenario": s.to_bytes()}
        out, notes = S.apply_sectors(pack.get, "TestMap", ["a.scenario", "b.scenario"], None, most=512)
        self.assertEqual(sorted(out), sorted([folder + "a.scenario", folder + "zonebluff\\a.kdt"]))
        self.assertTrue(any("b.scenario" in n and "no zone map" in n for n in notes))
        back = Scenario.read(out[folder + "a.scenario"])
        self.assertEqual(len(back.zones), 2)
        self.assertEqual(level_at(Kdt(out[folder + "zonebluff\\a.kdt"]), 5000.0, 5000.0), 0)

    def test_a_scenario_that_cant_be_made_again_stays_as_it_is(self):
        from rusemod.cover import member as movement_member
        from rusemod.scenario import folder_of
        inner = [(60000.0, 60000.0), (80000.0, 60000.0), (80000.0, 80000.0), (60000.0, 80000.0)]
        outer = [(20000.0, 20000.0), (150000.0, 20000.0), (150000.0, 150000.0), (20000.0, 150000.0)]
        s, kdt = made_up((outer, inner), ((30000.0, 30000.0, 0.0), (70000.0, 70000.0, 0.0)))
        folder = folder_of("TestMap")
        win = b"INFOIA\r\n" + bytes(32) + struct.pack("<2f", W, H) + bytes(16)
        pack = {movement_member("TestMap"): win, folder + "a.scenario": s.to_bytes(), folder + "zonebluff\\a.kdt": kdt}
        skipped = []
        out, _notes = S.apply_sectors(pack.get, "TestMap", ["a.scenario"], None, most=512, skipped=skipped)
        self.assertEqual(out, {})
        self.assertEqual(len(skipped), 1)
        self.assertIn("inside it", skipped[0])


if __name__ == "__main__":
    unittest.main()
