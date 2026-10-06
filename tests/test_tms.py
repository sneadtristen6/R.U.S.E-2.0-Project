"""Terrain mesh (.tms): stream codecs, container round trip and height edits on small made-up meshes."""
import random
import struct
import unittest
import zlib

from rusemod.tms import (
    HEADER_SIZE, MAGIC, NORMAL, POSITION, Q_MAX, SKIRT_BOTTOM, VERTEX_TYPE, Cell, Patch, Tms, VertexBuffer,
    decode_indices, decode_parents, encode_indices, encode_parents, lz_decode, lz_encode, plateau,
)

LZ = struct.Struct("<BBBBIIIHH")


def hand_stream(bits, lits, toks, count, unit=1):
    """An LZ stream laid out by hand from the documented format (independent of lz_encode)."""
    bits = bits + [1]  # end bit
    words = b"".join(struct.pack("<I", sum(b << i for i, b in enumerate(bits[w:w + 32]))) for w in range(0, len(bits), 32))
    lbase = 0x14 + len(words)
    tbase = (lbase + len(lits) + 3) & ~3
    head = LZ.pack(1, 0x14, 16 if unit == 2 else 8, 0, count, len(lits) // unit, bits.count(1) - 1, lbase >> 2, tbase >> 2)
    body = head + words + lits + bytes(tbase - lbase - len(lits)) + toks
    return body + bytes(((len(body) + 3) & ~3) + 4 - len(body))


class LzStreams(unittest.TestCase):
    def test_hand_made_byte_stream_with_every_token_form(self):
        toks = bytes([
            (2 - 1) | 4 | (2 - 1) << 3,                      # 1 byte: len 2, dist 2        -> "ab"
        ]) + struct.pack("<H", (3 - 1) | (5 - 1) << 3) \
            + struct.pack("<H", 3 | (6 - 4) << 3 | (4 - 1) << 7) \
            + bytes((lambda v: (v & 0xFF, v >> 8 & 0xFF, v >> 16))(7 | (20 - 4) << 3 | (1 - 1) << 11))
        # "abcd" literal, then: len2 dist2 "cd", len3 dist5 "dcd", len6 dist4 "dcdd" .., len20 dist1 run
        s = hand_stream([0, 0, 0, 0, 1, 1, 1, 1], b"abcd", toks, 4 + 2 + 3 + 6 + 20)
        out = bytearray(b"abcd")
        for ln, dist in ((2, 2), (3, 5), (6, 4), (20, 1)):
            for _ in range(ln):
                out.append(out[-dist])
        self.assertEqual(lz_decode(s), bytes(out))

    def test_hand_made_u16_stream_counts_units(self):
        lits = struct.pack("<3H", 1000, 2000, 3000)
        toks = bytes([(3 - 1) | 4 | (3 - 1) << 3])           # len 3 units, dist 3 units
        s = hand_stream([0, 0, 0, 1], lits, toks, 6, unit=2)
        self.assertEqual(lz_decode(s), lits * 2)

    def test_round_trip_and_layout(self):
        rnd = random.Random(7)
        samples = [
            b"",
            bytes(rnd.randrange(256) for _ in range(3000)),
            b"terrain " * 900 + bytes(range(256)) * 40,       # long runs (> 259) and far matches (> 8192)
            bytes(rnd.choice(b"\x00\x01\x80") for _ in range(20000)),
        ]
        for data in samples:
            for unit in (1, 2):
                if len(data) % unit:
                    data = data[:-1]
                s = lz_encode(data, unit)
                self.assertEqual(lz_decode(s), data)
                ver, hlen, method, sb, count, nlit, ntok, lbase, tbase = LZ.unpack_from(s)
                self.assertEqual((ver, hlen, method, count), (1, 0x14, 16 if unit == 2 else 8, len(data) // unit))
                nwords = (nlit + ntok + 1 + 31) // 32
                self.assertEqual(lbase << 2, 0x14 + 4 * nwords)
                self.assertEqual(tbase << 2, ((lbase << 2) + nlit * unit + 3) & ~3)
                last = struct.unpack_from("<I", s, 0x14 + 4 * (nwords - 1))[0]
                self.assertEqual(last.bit_length(), (nlit + ntok) % 32 + 1)   # single end bit after the last op
                self.assertIn(len(s) % 4, (0,))
                self.assertEqual(s[-4:], bytes(4))

    def test_compresses_repetitive_data(self):
        data = struct.pack("<400H", *([7, 7, 9, 1] * 100))
        self.assertLess(len(lz_encode(data, 2)), len(data) // 4)


class Predictor(unittest.TestCase):
    def test_round_trip_with_near_and_far_parents(self):
        par = [0, 0, 1, 2, 0, 4, 1, 6, 3]
        raw = encode_parents(par)
        self.assertEqual(raw[:2], b"\x00\x00")      # vertices 2, 3: previous vertex
        self.assertEqual(raw[2:4], b"\x80\x04")     # vertex 4: four back
        self.assertEqual(decode_parents(raw, len(par)), par)

    def test_rejects_a_parent_that_is_not_earlier(self):
        with self.assertRaises(ValueError):
            encode_parents([0, 0, 2])

    def test_length_mismatch_is_an_error(self):
        with self.assertRaises(ValueError):
            decode_parents(b"\x00\x00", 3)


class Indices(unittest.TestCase):
    def test_running_differences_and_sync_flush(self):
        idx = [0, 1, 5, 5, 1, 0, 65535, 3, 2]
        raw = encode_indices(idx)
        self.assertEqual(struct.unpack_from("<I", raw)[0], 2 * len(idx))
        self.assertEqual(raw[-4:], b"\x00\x00\xff\xff")
        diffs = struct.unpack("<9H", zlib.decompressobj().decompress(raw[4:]))
        self.assertEqual(diffs[:3], (0, 1, 4))
        self.assertEqual(decode_indices(raw), idx)


def grid_cell(x0, x1, y0, y1, n, zf, water=None):
    """A cell meshed as an n x n vertex grid (quantized coords), with list 1 = the first row of quads if water."""
    pos, par = [], []
    for j in range(n):
        for i in range(n):
            x = x0 + (x1 - x0) * i // (n - 1)
            y = y0 + (y1 - y0) * j // (n - 1)
            pos.append((x, y, zf(x, y), 100 if water is None else water))
            k = len(pos) - 1
            par.append(0 if k < 2 else (k - n if i == 0 and j else k - 1))
    nor = [(128, 128, 255, 128)] * len(pos)
    tri = []
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            tri += [a, a + 1, a + n, a + 1, a + n + 1, a + n]
    lists = [tri] + ([tri[:6 * (n - 1)]] if water is not None else [])
    flags = 1 | (2 if water is not None else 0)
    vb = VertexBuffer.build(pos, nor, par).to_bytes()
    half = len(pos) // 2  # two patches: first half and second half of the vertices
    zq = lambda run, f: f(p[2] for p in run)
    patches = [Patch(0, half, 0, len(tri) // 2, 0, 0, 0.0, 0.0), Patch(half, len(pos) - half, len(tri) // 2, len(tri) - len(tri) // 2, 0, 0, 0.0, 0.0)]
    cell = Cell(flags, len(pos), vb, [encode_indices(t) for t in lists], [len(t) for t in lists], b"")
    cell.set_patches(patches)
    return cell, zq


SKIRT_TYPE = b"$/M3D/System/VERTEXTYPE/TVertex__PositionIn4w_4w"


def skirt_q(t: Tms, z: int) -> int:
    """A ground height (quantized) on the curtain's scale, SKIRT_BOTTOM (q 0) to the file's highest height."""
    return min(max(round((t.to_world(2, z) - SKIRT_BOTTOM) * Q_MAX / (t.bounds[5] - SKIRT_BOTTOM)), 1), Q_MAX)


def skirt_meshes(t: Tms) -> list:
    """The skirt read back: per submesh present, (indices, [(x, y, z, w)], [6 bounds], [(vstart, vcount, istart,
    icount)]), from the layout in docs/FORMATS.md (independent of rusemod.tms)."""
    out, pos = [], 0
    for m in range(2):
        ib, vb, bb, pb = struct.unpack_from("<4I", t.skirt, 4 + 16 * m)
        idx = list(struct.unpack_from(f"<{ib // 2}H", t.skirt_data, pos))
        verts = [struct.unpack_from("<4H", t.skirt_data, pos + ib + 8 * j) for j in range(vb // 8)]
        bounds = [struct.unpack_from("<6f", t.skirt_data, pos + ib + vb + 24 * k) for k in range(bb // 24)]
        parts = [struct.unpack_from("<4I", t.skirt_data, pos + ib + vb + bb + 16 * k) for k in range(pb // 16)]
        pos += ib + vb + bb + pb
        if vb:
            out.append((idx, verts, bounds, parts))
    return out


def make_skirt(t: Tms) -> tuple[bytes, bytes]:
    """A skirt for a made-up mesh laid out like the shipped ones: the curtain, a top at the ground's height and a foot
    at q 0 under every edge point, and the water's side, from the ground up to the water, under the edge points whose
    water is above the ground; each in 4 parts, the edges y = 0, x = 0, x = max and y = max in turn (a corner point is
    in two of them). Returns (descriptor, data)."""
    heights = {}
    for c in t.cells:
        for x, y, z, w in c.positions():
            if x in (0, Q_MAX) or y in (0, Q_MAX):
                heights[(x, y)] = (z, w)
    sides = [sorted(xy for xy in heights if xy[1] == 0), sorted((xy for xy in heights if xy[0] == 0), key=lambda p: p[1]),
             sorted((xy for xy in heights if xy[0] == Q_MAX), key=lambda p: p[1]), sorted(xy for xy in heights if xy[1] == Q_MAX)]
    scale = (t.bounds[5] - SKIRT_BOTTOM) / Q_MAX
    desc, data, flags = bytearray(), bytearray(), 0
    for m in range(2):
        idx, verts, bounds, parts = [], [], [], []
        for side in sides:
            cols = side if m == 0 else [xy for xy in side if heights[xy][1] > heights[xy][0]]
            vstart, istart = len(verts), len(idx)
            for n, (x, y) in enumerate(cols):
                z, w = heights[(x, y)]
                verts += [(x, y, skirt_q(t, z), 0), (x, y, 0, 0)] if m == 0 else [(x, y, w, 0), (x, y, z, 0)]
                if n:
                    a = len(verts) - 4
                    idx += [a, a + 1, a + 2, a + 1, a + 3, a + 2]
            run = verts[vstart:]
            if run:
                zs = [SKIRT_BOTTOM + v[2] * scale if m == 0 else t.to_world(2, v[2]) for v in run]
                bounds.append((t.to_world(0, min(v[0] for v in run)), t.to_world(1, min(v[1] for v in run)), min(zs),
                               t.to_world(0, max(v[0] for v in run)), t.to_world(1, max(v[1] for v in run)), max(zs)))
            else:
                bounds.append((0.0,) * 6)
            parts.append((vstart, len(run), istart, len(idx) - istart))
        if not verts:
            desc += bytes(16)
            continue
        flags |= 1 << m
        blob = (struct.pack(f"<{len(idx)}H", *idx) + b"".join(struct.pack("<4H", *v) for v in verts)
                + b"".join(struct.pack("<6f", *b) for b in bounds) + b"".join(struct.pack("<4I", *p) for p in parts))
        desc += struct.pack("<4I", 2 * len(idx), 8 * len(verts), 24 * len(bounds), 16 * len(parts))
        data += blob
    return struct.pack("<I", flags) + bytes(desc) + SKIRT_TYPE.ljust(512, b"\0"), bytes(data)


def make_tms(gw=2, gh=2, n=9, zf=lambda x, y: 1000, water_cell=None, water=500, skirt=False):
    """A made-up mesh: gw x gh cells of n x n points over 1,000 x 1,000 each, heights from zf (quantized), the cell
    water_cell with water at `water` (others at 100), and, with skirt, a skirt like the shipped close-up meshes'
    (else an all-zero descriptor, like the far meshes')."""
    t = Tms.__new__(Tms)
    head = bytearray(HEADER_SIZE)
    head[:4] = MAGIC
    struct.pack_into("<I4s", head, 4, 3, b"PC\0\0")
    head[0x3C:0x3C + len(VERTEX_TYPE)] = VERTEX_TYPE.encode()
    t.head = bytes(head)
    t.grid_w, t.grid_h, t.patch_div = gw, gh, 8
    t.cell_w = t.cell_h = 1000.0
    t.bounds = [0.0, 0.0, -100.0, 1000.0 * gw, 1000.0 * gh, 3176.7]   # z step = 0.1 per quantum
    t.skirt, t.skirt_data = bytes(548), b""
    t.cells = []
    for cy in range(gh):
        for cx in range(gw):
            cell, _ = grid_cell(Q_MAX * cx // gw, Q_MAX * (cx + 1) // gw, Q_MAX * cy // gh, Q_MAX * (cy + 1) // gh,
                                n, zf, water if (cx, cy) == water_cell else None)
            t.cells.append(cell)
    if skirt:
        t.skirt, t.skirt_data = make_skirt(t)
    return t.to_bytes()


class Container(unittest.TestCase):
    def setUp(self):
        self.raw = make_tms(zf=lambda x, y: 1000 + x // 64, water_cell=(1, 0))
        self.tms = Tms(self.raw)

    def test_header_fields(self):
        raw = self.raw
        self.assertEqual(raw[:4], MAGIC)
        self.assertEqual(raw[-4:], MAGIC)
        self.assertEqual(struct.unpack_from("<I", raw, 0x0C)[0], len(raw))
        self.assertEqual(struct.unpack_from("<3I", raw, 0x10), (2, 2, 8))
        self.assertEqual(struct.unpack_from("<2I", raw, 0x24), (HEADER_SIZE, 4 * 48))
        self.assertEqual(self.tms.vertex_type, VERTEX_TYPE)

    def test_rewrite_is_byte_identical(self):
        self.assertEqual(self.tms.to_bytes(), self.raw)

    def test_cells_decode(self):
        c = self.tms.cells[1]
        self.assertEqual(c.flags, 3)
        self.assertEqual(len(c.positions()), 81)
        self.assertEqual(c.positions()[0][3], 500)
        self.assertEqual(c.triangles(1), c.triangles(0)[:48])
        self.assertEqual(self.tms.cells[0].triangles(1), [])
        self.assertEqual(c.normals()[5], (128, 128, 255, 128))

    def test_world_coordinates(self):
        t = self.tms
        self.assertEqual(t.to_world(2, 0), -100.0)
        self.assertAlmostEqual(t.to_world(2, Q_MAX), 3176.7, 3)
        self.assertAlmostEqual(t.to_world(0, Q_MAX), 2000.0, 6)
        self.assertEqual(t.to_quant(2, t.to_world(2, 1234)), 1234)
        self.assertEqual(t.to_quant(2, 1e9), Q_MAX)
        self.assertEqual(t.to_quant(2, -1e9), 0)

    def test_height_grid_interpolates_the_mesh(self):
        grid = self.tms.height_grid(32)
        self.assertEqual((len(grid), len(grid[0])), (32, 32))
        self.assertTrue(all(v is not None for row in grid for v in row))
        # z = 1000 + x/64 quanta -> rises left to right, constant down a column
        self.assertLess(grid[5][2], grid[5][29])
        self.assertAlmostEqual(grid[3][10], grid[28][10], 1)

    def test_bad_input_is_rejected(self):
        with self.assertRaises(ValueError):
            Tms(b"XXXX" + self.raw[4:])
        with self.assertRaises(ValueError):
            Tms(self.raw[:-4] + b"\0\0\0\0")
        bad = bytearray(self.raw)
        struct.pack_into("<I", bad, 0x0C, len(bad) + 1)
        with self.assertRaises(ValueError):
            Tms(bytes(bad))


class HeightEdit(unittest.TestCase):
    def setUp(self):
        self.raw = make_tms(gw=3, gh=3, n=11, water_cell=(1, 1))
        self.tms = Tms(self.raw)

    def test_plateau_changes_only_the_centre_and_re_reads_exactly(self):
        t = self.tms
        fn = plateau(1500.0, 1500.0, 200.0, 400.0, 2000.0)
        n = t.edit_heights(fn)
        self.assertGreater(n, 0)
        out = t.to_bytes()
        back = Tms(out)
        orig = Tms(self.raw)
        for k, (a, b) in enumerate(zip(orig.cells, back.cells)):
            for p, q in zip(a.positions(), b.positions()):
                self.assertEqual((p[0], p[1], p[3]), (q[0], q[1], q[3]))
                want = fn(t.to_world(0, p[0]), t.to_world(1, p[1]), t.to_world(2, p[2]))
                self.assertEqual(q[2], p[2] if want is None else t.to_quant(2, want))
            if k != 4:
                self.assertEqual(a.vb, b.vb)          # untouched cells keep their bytes
                self.assertEqual(a.patches, b.patches)
        centre = back.cells[4]
        top = t.to_quant(2, 2000.0)
        self.assertIn(top, [p[2] for p in centre.positions()])
        # the patch bounds now reach the top; the cell has water so its low bound is recomputed too
        self.assertAlmostEqual(max(p.zhi for p in centre.patch_list()), 2000.0, 1)
        self.assertAlmostEqual(min(p.zlo for p in centre.patch_list()), back.to_world(2, 1000), 1)

    def test_normals_tilt_on_the_slope_and_stay_flat_elsewhere(self):
        t = self.tms
        t.edit_heights(plateau(1500.0, 1500.0, 150.0, 450.0, 2000.0))
        back = Tms(t.to_bytes())
        c = back.cells[4]
        for p, nrm in zip(c.positions(), c.normals()):
            x, y = back.to_world(0, p[0]), back.to_world(1, p[1])
            if abs(y - 1500) < 1 and 1750 < x < 1900:        # on the east slope: normal leans east (+x)
                self.assertGreater(nrm[0], 140)
            if abs(x - 1500) < 1 and 1100 < y < 1250:        # on the south slope: normal leans towards -y
                self.assertLess(nrm[1], 116)
            self.assertEqual(nrm[3], 128)
        self.assertEqual(back.cells[0].normals()[3], (128, 128, 255, 128))

    def test_border_vertices_move_too(self):
        t = self.tms
        t.edit_heights(lambda x, y, z: z + 50.0)
        back = Tms(t.to_bytes())
        self.assertTrue(all(p[2] == 1500 for c in back.cells for p in c.positions()))
        self.assertEqual((back.skirt, back.skirt_data), (bytes(548), b""))   # no skirt to follow (a far mesh)

    def test_heights_are_clamped_to_the_file_range(self):
        t = self.tms
        t.edit_heights(lambda x, y, z: 1e9)
        self.assertEqual(max(p[2] for c in Tms(t.to_bytes()).cells for p in c.positions()), Q_MAX)


class EdgeAndSkirt(unittest.TestCase):
    """Edge points move like any other and the skirt hanging from them follows: keeping them still left a wall of old
    mountain one point thick round the owner's flattened Blitz Twin (2026-10-03). The mesh is flat at 1,000 (quantized)
    and the top middle cell, on the edge y = 0, is under water at 1,200."""

    def setUp(self):
        self.raw = make_tms(gw=3, gh=3, n=11, water_cell=(1, 0), water=1200, skirt=True)
        self.tms = Tms(self.raw)

    def test_the_fixture_has_a_curtain_and_a_water_side(self):
        curtain, side = skirt_meshes(self.tms)
        self.assertEqual(struct.unpack_from("<I", self.tms.skirt)[0], 3)
        self.assertEqual({v[2] for v in curtain[1]}, {0, skirt_q(self.tms, 1000)})
        self.assertEqual({v[2] for v in side[1]}, {1000, 1200})
        self.assertEqual({v[1] for v in side[1]}, {0})
        self.assertEqual(self.tms.to_bytes(), self.raw)   # unedited: byte for byte

    def test_the_curtain_follows_the_moved_edge(self):
        t = self.tms
        t.edit_heights(lambda x, y, z: z + 50.0)          # +500 steps, everywhere
        back = Tms(t.to_bytes())
        self.assertTrue(all(p[2] == 1500 for c in back.cells for p in c.positions()))
        before, (idx, verts, bounds, parts) = skirt_meshes(Tms(self.raw))[0], skirt_meshes(back)[0]
        top = skirt_q(back, 1500)
        self.assertEqual([v[2] for v in verts], [top if v[2] else 0 for v in before[1]])   # the feet stay at q 0
        self.assertEqual((idx, parts, [v[:2] for v in verts]), (before[0], before[3], [v[:2] for v in before[1]]))
        scale = (back.bounds[5] - SKIRT_BOTTOM) / Q_MAX
        for b, old in zip(bounds, before[2]):
            self.assertEqual(b[:2] + b[3:5], old[:2] + old[3:5])        # x, y bounds unchanged
            self.assertEqual(b[2], SKIRT_BOTTOM)
            self.assertAlmostEqual(b[5], SKIRT_BOTTOM + top * scale, 1)
        self.assertEqual(back.skirt, Tms(self.raw).skirt)

    def test_the_water_side_folds_flat_under_ground_raised_above_the_water(self):
        t = self.tms
        t.edit_heights(lambda x, y, z: z + 50.0)          # ground 1,500 over water at 1,200
        _idx, verts, bounds, parts = skirt_meshes(Tms(t.to_bytes()))[1]
        self.assertEqual({v[2] for v in verts}, {1500})
        for b, p in zip(bounds, parts):
            if p[1]:
                self.assertEqual(b[2], b[5])

    def test_the_water_side_reaches_down_to_lowered_ground(self):
        t = self.tms
        t.edit_heights(lambda x, y, z: z - 30.0)          # ground 700 under water at 1,200
        back = Tms(t.to_bytes())
        _idx, verts, bounds, parts = skirt_meshes(back)[1]
        self.assertEqual(sorted({v[2] for v in verts}), [700, 1200])
        self.assertEqual(sum(v[2] == 700 for v in verts), len(verts) // 2)
        part = next(k for k, p in enumerate(parts) if p[1])
        self.assertAlmostEqual(bounds[part][2], back.to_world(2, 700), 2)
        self.assertAlmostEqual(bounds[part][5], back.to_world(2, 1200), 2)

    def test_a_water_side_point_between_edge_points_follows_the_edge_there(self):
        """The shipped water sides have points between the edge's own (133 on the 32 maps, where the water's surface
        meets the bank): they take the edge's height from the points either side (on Blitz two were left at the old
        river's 28,095 under a ground flattened to 31,000)."""
        t = self.tms
        ib, vb = struct.unpack_from("<2I", t.skirt, 4)
        ib2 = struct.unpack_from("<I", t.skirt, 20)[0]
        first = ib + vb + 0x60 + 0x40 + ib2                 # the water side's first vertex: a top, at the water
        data = bytearray(t.skirt_data)
        x, y, z, w = struct.unpack_from("<4H", data, first)
        self.assertEqual((y, z), (0, 1200))
        struct.pack_into("<H", data, first, x + 1)          # now between two edge points, alone under its x, y
        t.skirt_data = bytes(data)
        t.edit_heights(lambda x, y, z: z + 50.0)            # ground 1,500 over the water at 1,200
        back = Tms(t.to_bytes())
        self.assertEqual(struct.unpack_from("<4H", back.skirt_data, first), (x + 1, 0, 1500, 0))

    def test_one_moved_edge_point_moves_only_its_own_column(self):
        t = self.tms
        cell = t.cells[0].positions()
        i = next(n for n, p in enumerate(cell) if p[1] == 0 and 0 < p[0] < Q_MAX // 3)   # on the edge y = 0
        x, y = cell[i][:2]
        t.set_heights(0, {i: 2000})
        verts, before = skirt_meshes(Tms(t.to_bytes()))[0][1], skirt_meshes(Tms(self.raw))[0][1]
        for v, old in zip(verts, before):
            want = skirt_q(t, 2000) if (v[0], v[1]) == (x, y) and old[2] else old[2]
            self.assertEqual(v[2], want)

    def test_an_edit_off_the_edge_keeps_the_skirt_bytes(self):
        t = self.tms
        t.edit_heights(plateau(1500.0, 1500.0, 200.0, 400.0, 2000.0))
        back = Tms(t.to_bytes())
        self.assertEqual((back.skirt, back.skirt_data), (Tms(self.raw).skirt, Tms(self.raw).skirt_data))
        self.assertNotEqual(back.cells[4].vb, Tms(self.raw).cells[4].vb)

    def test_a_new_water_level_at_the_edge_moves_the_water_sides_top(self):
        """The edge's points kept an old river's water under a new sea, and the water's side stood up to it: walls of
        water round Blank Ocean (seen in the game, 2026-10-05). Lower or higher, the side's top follows the water."""
        for level in (1100, 1500):
            with self.subTest(level=level):
                t = Tms(self.raw)
                t.set_water(1, {i: level for i in range(len(t.cells[1].positions()))})
                back = Tms(t.to_bytes())
                _idx, verts, bounds, parts = skirt_meshes(back)[1]
                self.assertEqual(sorted({v[2] for v in verts}), [1000, level])
                self.assertEqual(sum(v[2] == 1000 for v in verts), len(verts) // 2)   # the feet stay on the ground
                part = next(k for k, p in enumerate(parts) if p[1])
                self.assertAlmostEqual(bounds[part][2], back.to_world(2, 1000), 2)
                self.assertAlmostEqual(bounds[part][5], back.to_world(2, level), 2)
                self.assertEqual(skirt_meshes(back)[0], skirt_meshes(Tms(self.raw))[0])   # the curtain stays

    def test_drained_water_at_the_edge_folds_the_water_side_flat(self):
        t = self.tms
        t.set_water(1, {i: 100 for i in range(len(t.cells[1].positions()))})   # under the ground, as beside it
        _idx, verts, bounds, parts = skirt_meshes(Tms(t.to_bytes()))[1]
        self.assertEqual({v[2] for v in verts}, {1000})
        for b, p in zip(bounds, parts):
            if p[1]:
                self.assertEqual(b[2], b[5])

    def test_new_ground_and_new_water_at_the_edge_together(self):
        t = self.tms
        t.edit_heights(lambda x, y, z: z - 30.0)            # ground 700
        t.set_water(1, {i: 900 for i in range(len(t.cells[1].positions()))})
        _idx, verts, _bounds, _parts = skirt_meshes(Tms(t.to_bytes()))[1]
        self.assertEqual(sorted({v[2] for v in verts}), [700, 900])
        self.assertEqual(sum(v[2] == 700 for v in verts), len(verts) // 2)

    def test_a_water_edit_off_the_edge_keeps_the_skirt_bytes(self):
        t = self.tms
        t.set_water(4, {i: 1300 for i in range(len(t.cells[4].positions()))})   # the middle cell: no edge point
        back = Tms(t.to_bytes())
        self.assertEqual((back.skirt, back.skirt_data), (Tms(self.raw).skirt, Tms(self.raw).skirt_data))
        self.assertEqual(back.cells[4].flags & 2, 2)

    def test_a_map_without_water_at_its_edge_has_only_the_curtain(self):
        t = Tms(make_tms(gw=2, gh=2, n=5, skirt=True))
        self.assertEqual(struct.unpack_from("<I", t.skirt)[0], 1)
        self.assertEqual(struct.unpack_from("<4I", t.skirt, 20), (0, 0, 0, 0))
        t.edit_heights(lambda x, y, z: z + 10.0)
        back = Tms(t.to_bytes())
        self.assertEqual(len(skirt_meshes(back)), 1)
        self.assertEqual({v[2] for v in skirt_meshes(back)[0][1]}, {0, skirt_q(back, 1100)})


class VertexBuffers(unittest.TestCase):
    def test_build_matches_the_shipped_layout(self):
        pos = [(i, 2 * i, 3 * i, 7) for i in range(50)]
        nor = [(128, 128, 255, 128)] * 50
        par = [0, 0] + list(range(1, 49))
        raw = VertexBuffer.build(pos, nor, par).to_bytes()
        self.assertEqual(raw[:12], bytes.fromhex("564255460800a10c00020002"))
        vb = VertexBuffer.parse(raw, 50)
        self.assertEqual(vb.decode(POSITION), pos)
        self.assertEqual(vb.decode(NORMAL), nor)
        self.assertEqual(vb.parents(), par)
        self.assertEqual(vb.element(POSITION).head.hex(), "535542500c0008030208000000000000")
        self.assertEqual(vb.element(NORMAL).head.hex(), "535542500c0004030204000800000000")

    def test_values_out_of_range_are_refused(self):
        with self.assertRaises(ValueError):
            VertexBuffer.build([(0, 0, 70000, 0)], [(0, 0, 0, 0)], [0])


if __name__ == "__main__":
    unittest.main()
