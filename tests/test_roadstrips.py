"""The roads the game draws up close (rusemod.roadstrips): the road model of a map pack's static meshes, on a made-up
pack laid out as the shipped ones are (two models, a bridge and the road; the road's parts by case; `~` filler after
the materials), and the build's step that draws a new road both ways (build.draw_new_roads, the T12 guard)."""
import hashlib
import math
import struct
import unittest

from test_tms import make_tms
from rusemod import roadstrips
from rusemod.roadstrips import (CASE, MEMBER, SEGMENT, STRIDE, VERTEX, StaticMeshes, StripError, add_roads,
                                case_numbers, draw_roads, grid, strips)
from rusemod.spk import Spk

BRIDGE_FORMAT = "$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__TexCoord0_2wn__TexPackedAtlas0_4ubn"
ROAD_FORMAT = "$/M3D/System/VERTEXTYPE/" + VERTEX
COLOUR = (220, 220, 220, 100)
WIDTH = 400.0
BOUNDS = (0.0, 0.0, 4 * CASE, 2 * CASE)  # 4 x 2 cases


def road_vertex(x, y, z, u):
    return struct.pack("<3f4B4Bf4B2f2f", x, y, z, 255, 128, 128, 128, 128, 0, 128, 128, 1.0, *COLOUR, 0.0, 0.0, u, WIDTH)


def old_strip(x0, y0, x1, y1, z=500.0):
    """A shipped-like strip: two points, three vertices each."""
    return [road_vertex(x, y, z, u) for x, y in ((x0, y0), (x1, y1)) for u in (-0.5, 0.0, 0.5)]


def names(models) -> bytes:
    """The name table: u32 10, 6 bytes, then each model at the top: (0, next), its box, flags, mesh, 0xCDCD, name."""
    out = b""
    for k, (name, box, mesh) in enumerate(models):
        node = struct.pack("<6fIHH", *box, 0, mesh, 0xCDCD) + name.encode() + b"\0"
        size = 8 + len(node)
        out += struct.pack("<II", 0, size if k < len(models) - 1 else 0) + node
    return struct.pack("<I", 10) + bytes(6) + out


def static_pack(road_cases=((1, (2000.0, 2000.0, 9000.0, 2000.0)), (3, (90000.0, 90000.0, 99000.0, 90000.0))),
                road_format=ROAD_FORMAT) -> bytes:
    """A map's static meshes: model `bridges` (one draw, one part) and `road` (one draw, a strip in each of
    `road_cases`: (case, (x0, y0, x1, y1)))."""
    bridge_v = b"".join(struct.pack("<3f4B2H4B", x, 100.0, 50.0, 128, 128, 255, 0, 0, 0, 0, 0, 255, 255)
                        for x in (10.0, 20.0, 30.0))
    bridge_i = struct.pack("<6H", 0, 1, 2, 2, 1, 0)
    road_v, road_i, parts = [], [], [struct.pack("<6fHHIIIII", 10.0, 100.0, 50.0, 30.0, 100.0, 50.0, 7, 0xDDDD,
                                                 0, 3, 0, 6, 0xDDDDCD00)]
    for case, (x0, y0, x1, y1) in road_cases:
        v0, i0 = len(road_v), len(road_i)
        road_v += old_strip(x0, y0, x1, y1)
        road_i += [v0 + j for j in SEGMENT]
        parts.append(struct.pack("<6fHHIIIII", x0, y0, 500.0, x1, y1, 510.0, case, 0xDDDD, v0, 6, i0, 12, 0xDDDDCD00))
    road_vb, road_ib = b"".join(road_v), struct.pack(f"<{len(road_i)}H", *road_i)
    regions = [
        names([("bridges", (10.0, 100.0, 50.0, 30.0, 100.0, 50.0), 0), ("road", (0.0, 0.0, 0.0, 99000.0, 90000.0, 510.0), 1)]),
        struct.pack("<I", 256) + BRIDGE_FORMAT.encode().ljust(256, b"\0") + road_format.encode().ljust(256, b"\0"),
        b"MATERIALS!",  # ending 3 short of a multiple of 4: `~` filler before the parts, as the shipped files have
        b"".join(parts),
        struct.pack("<4H", 0, 1, 1, len(road_cases)),
        struct.pack("<4H", 0, 1, 1, 1),
        struct.pack("<6H", 0, 0, 0, 0, 0, 0xCDCD) + struct.pack("<6H", 1, 1, 1, 1, 1, 0xCDCD),
        struct.pack("<IIIHH", 0, len(bridge_i), 6, 1, 0) + struct.pack("<IIIHH", len(bridge_i), len(road_ib), len(road_i), 1, 0),
        struct.pack("<IIIHH", 0, len(bridge_v), 3, 0, 0) + struct.pack("<IIIHH", len(bridge_v), len(road_vb), len(road_v), 1, 0),
        bridge_i + road_ib,
        bridge_v + road_vb]
    counts = [2, 2, 2, len(parts), 2, 2, 2, 2]
    body, starts = bytearray(0xC4), []
    for k, blob in enumerate(regions):
        if k == 3:
            body += b"~" * (-len(body) % 4)
        starts.append(len(body))
        body += blob
    body[:12] = b"MESHPCPC" + struct.pack("<I", 4)
    struct.pack_into("<I", body, 0x0C, len(body))
    struct.pack_into("<4I", body, 0x20, 0, starts[9], starts[9], len(body) - starts[9])
    struct.pack_into("<I", body, 0x30, 2)
    for i in range(8):
        struct.pack_into("<III", body, 0x34 + 12 * i, starts[i], len(regions[i]), counts[i])
    struct.pack_into("<II", body, 0x94, starts[9], len(regions[9]))
    struct.pack_into("<III", body, 0x9C, starts[8], len(regions[8]), 2)
    struct.pack_into("<II", body, 0xA8, starts[10], len(regions[10]))
    struct.pack_into("<5I", body, 0xB0, starts[7], 0, 0, starts[7], 0)
    body[0x10:0x20] = hashlib.md5(bytes(body[:0x10]) + bytes(body[0x20:0x30])).digest()
    return bytes(body)


def slope(x, y):
    return 1000.0 + x / 100.0


def road_vertices(raw: bytes) -> list[tuple]:
    pack = StaticMeshes(raw)
    vb, _idx = pack.buffers(pack.road_draw())
    return [struct.unpack_from("<3f4B4Bf4B2f2f", vb, k) for k in range(0, len(vb), STRIDE)]


def unbyte(b):
    return b / 255 * 2 - 1


class Cases(unittest.TestCase):
    def test_numbered_along_the_curve_as_the_shipped_maps(self):
        """Numbers read off the shipped files' road parts: D-Day (48 x 32 cases) and Battle of the Bulge (16 x 16)."""
        dday, bulge = case_numbers(48, 32), case_numbers(16, 16)
        self.assertEqual((dday[(22, 13)], dday[(32, 12)], dday[(33, 15)]), (461, 1370, 1364))
        self.assertEqual([bulge[c] for c in ((2, 2), (2, 3), (3, 3), (3, 1))], [8, 9, 10, 12])
        self.assertEqual(sorted(dday.values()), list(range(48 * 32)))  # every case once, none off the map

    def test_the_grid_counts_a_last_case_the_ground_ends_short_of(self):
        self.assertEqual(grid((0.0, 0.0, 3932160.0, 2621440.0)), (48, 32))
        self.assertEqual(grid((0.0, 0.0, 1964160.0, 1964160.0)), (24, 24))  # Beta: 1,920 short of 24 cases


class Reading(unittest.TestCase):
    def test_rebuilt_with_nothing_added_is_the_same_file(self):
        raw = static_pack()
        pack = StaticMeshes(raw)
        self.assertIs(pack.with_strips({}), raw)
        self.assertEqual(pack.with_strips({1: []}), raw)  # rebuilt through and through: byte for byte
        self.assertEqual(Spk(raw).items["road"].mesh, 1)

    def test_a_layout_it_doesnt_know_is_refused(self):
        raw = bytearray(static_pack())
        struct.pack_into("<I", raw, 0x34 + 12 * 4, struct.unpack_from("<I", raw, 0x34 + 12 * 4)[0] + 4)
        with self.assertRaisesRegex(StripError, "groups aren't where"):
            StaticMeshes(bytes(raw))
        with self.assertRaisesRegex(StripError, "stored in a way"):
            StaticMeshes(static_pack(road_format=BRIDGE_FORMAT)).road_draw()
        with self.assertRaisesRegex(StripError, "version-4 mesh pack"):
            StaticMeshes(b"MESHPCPC" + bytes(8))


class Adding(unittest.TestCase):
    def setUp(self):
        self.raw = static_pack()
        # east along y = 1,000 out of case (0, 0), north at x = 100,000 into case (1, 1): a right-angle bend
        self.line = [(1000.0, 1000.0), (100000.0, 1000.0), (100000.0, 100000.0)]
        self.new, self.notes = add_roads(self.raw, [self.line], slope, BOUNDS)

    def test_the_file_reads_back_whole(self):
        pack = StaticMeshes(self.new)
        self.assertEqual(struct.unpack_from("<I", self.new, 0x0C)[0], len(self.new))
        self.assertEqual(self.new[0x10:0x20], hashlib.md5(self.new[:0x10] + self.new[0x20:0x30]).digest())
        self.assertEqual(pack.gaps[3], b"~~~")
        d = pack.road_draw()
        g0, gn = pack.groups[pack.draws[d][4]]
        self.assertEqual(pack.groups[0], [0, 1])  # the bridge's part first, as it was
        self.assertEqual(pack.parts[0], StaticMeshes(self.raw).parts[0])
        vb, idx = pack.buffers(d)
        nv = ni = 0
        for part in pack.parts[g0:g0 + gn]:  # one part per case, in order, tiling the buffers
            fv, cv, fi, ci = part[8:12]
            self.assertEqual((fv, fi), (nv, ni))
            self.assertTrue(all(fv <= k < fv + cv for k in idx[fi:fi + ci]))
            nv, ni = nv + cv, ni + ci
        self.assertEqual((nv * STRIDE, ni), (len(vb), len(idx)))
        number = case_numbers(4, 2)
        self.assertEqual([p[6] for p in pack.parts[g0:g0 + gn]],
                         sorted({1, 3} | {number[(0, 0)], number[(1, 0)], number[(1, 1)]}))
        model = Spk(self.new).items["road"]
        self.assertEqual(model.box[3:5], (100000.0, 100000.0))  # grown to hold the new road
        self.assertIn("close-up strips: ", self.notes[0])

    def test_the_old_strips_keep_their_vertices(self):
        old = road_vertices(self.raw)
        new = road_vertices(self.new)
        for strip in (old[:6], old[6:]):
            k = new.index(strip[0])
            self.assertEqual(new[k:k + 6], strip)

    def test_each_piece_a_strip_on_the_ground_in_the_maps_look(self):
        from rusemod.scenery import road_pieces
        new = [v for v in road_vertices(self.new) if v[2] != 500.0]  # (the old strips lie at 500)
        pieces = road_pieces(self.line)
        self.assertEqual(len(new), 6 * len(pieces))
        ends = {(round(v[0]), round(v[1])) for v in new}
        for p in pieces:
            self.assertIn((round(p.x0), round(p.y0)), ends)
            self.assertIn((round(p.x1), round(p.y1)), ends)
        for v in new:
            self.assertAlmostEqual(v[2], slope(v[0], v[1]), places=0)  # on the ground
            self.assertEqual(v[12:16], COLOUR)
            self.assertEqual(v[19], WIDTH)
            self.assertIn(v[18], (-0.5, 0.0, 0.5))
            self.assertEqual((v[6], v[10], v[9]), (128, 128, 128))  # the side lies flat
        for k in range(0, len(new), 3):
            self.assertEqual([v[18] for v in new[k:k + 3]], [-0.5, 0.0, 0.5])

    def test_directions_sides_and_the_bend(self):
        new = [v for v in road_vertices(self.new) if v[2] != 500.0]
        first = next(v for v in new if (round(v[0]), round(v[1])) == (1000, 1000))
        bend = [v for v in new if (round(v[0]), round(v[1])) == (100000, 1000)]
        self.assertGreater(unbyte(first[3]), 0.99)  # east
        self.assertAlmostEqual(unbyte(first[8]), -1.0, places=1)  # its side: (t.y, -t.x)
        self.assertEqual(first[11], 1.0)  # the road's start: no bend
        self.assertTrue(bend)
        for v in bend:  # halfway between east and north, widened by 1 / cos(45°)
            self.assertAlmostEqual(unbyte(v[3]), unbyte(v[4]), places=1)
            self.assertAlmostEqual(v[11], math.sqrt(2), places=2)

    def test_pieces_off_the_ground_left_out(self):
        new, notes = add_roads(self.raw, [self.line], lambda x, y: None if x > 50000 else 1000.0, BOUNDS)
        self.assertIn("off the ground left out", notes[-1])
        self.assertTrue(all(v[0] <= 50000 for v in road_vertices(new) if v[2] == 1000.0))
        same, notes = add_roads(self.raw, [self.line], lambda x, y: None, BOUNDS)
        self.assertEqual(same, self.raw)

    def test_too_many_vertices_refused(self):
        try:
            roadstrips.MOST = 20
            with self.assertRaisesRegex(StripError, "past the 20 its indices reach"):
                add_roads(self.raw, [self.line], slope, BOUNDS)
        finally:
            roadstrips.MOST = 65536

    def test_the_points_of_a_run(self):
        runs, lost = strips([[(0.0, 0.0), (8000.0, 0.0)]], lambda x, y: 0.0)
        self.assertEqual(lost, 0)
        self.assertEqual([p[0] for p in runs[0]], [(0.0, 0.0, 0.0), (4000.0, 0.0, 0.0), (8000.0, 0.0, 0.0)])
        self.assertTrue(all(p[3] == 1.0 for p in runs[0]))  # straight on: no widening


class NewRoadsAreDrawnBothWays(unittest.TestCase):
    """The T12 guard: a new road vanished up close in every test batch (only painted into the ground's tiles, which
    the game's ground covers with detail textures near the camera wherever the map's close-up map doesn't mark a
    road). The build's road step must paint it, mark it in the close-up map the way the map's own roads are, and add
    every piece to the map's road model."""

    def test_a_new_road_is_drawn_up_close_not_only_painted(self):
        from test_groundpaint import div_map, store
        from test_scenery import village
        from rusemod.build import draw_new_roads
        from rusemod.groundpaint import DETAIL
        from rusemod.scenery import MEMBER as SCENERY, road_pieces
        s = store()  # tiles over 2 x 1 cells of 1,000
        files = {"output\\highdef.tms": make_tms(2, 1), "output\\highdef.tmst_pc": s.index,
                 "output\\highdef.tmst_chunk_pc": s.chunk, MEMBER: static_pack(),
                 DETAIL: div_map(road_row=set(range(32))), SCENERY: village()}  # (a map with a road to take after)
        line = [(100.0, 500.0), (1900.0, 500.0)]
        members, notes = draw_new_roads(files.get, lambda m: "map\\" + m, [line])
        self.assertIn("map\\" + MEMBER, members)  # the road model
        self.assertIn("map\\" + DETAIL, members)  # up close: the close-up map marks it
        self.assertIn("map\\output\\highdef.tmst_chunk_pc", members)  # from afar
        self.assertTrue(any(n.startswith("close-up map: ") for n in notes))
        drawn = {(round(v[0]), round(v[1])) for v in road_vertices(members["map\\" + MEMBER])}
        for p in road_pieces(line):
            self.assertIn((round(p.x0), round(p.y0)), drawn)
            self.assertIn((round(p.x1), round(p.y1)), drawn)
        self.assertTrue(any(n.startswith("close-up strips: ") for n in notes))

    def test_a_map_without_a_road_model_says_so(self):
        members, notes = draw_roads({}.get, str, [[(0.0, 0.0), (1.0, 1.0)]])
        self.assertEqual(members, {})
        self.assertIn("no road model", notes[0])
        self.assertEqual(draw_roads({}.get, str, []), ({}, []))


if __name__ == "__main__":
    unittest.main()
