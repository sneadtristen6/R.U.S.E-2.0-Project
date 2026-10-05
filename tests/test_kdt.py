"""Gameplay ground (.kdt): chunk codecs, container round trip and part replacement on a tiny made-up two-subtree
file (no game files). The file is laid out by hand, independently of the writer."""
import math
import struct
import unittest
import zlib

from fixtures import make_ndf, val
from rusemod.kdt import (
    FILL, OFFSETS, Clip, Kdt, Leaf, Split, compress, decode_indices, decode_main_node, decode_normal, decode_normals,
    decode_positions, decode_tree, decode_trilists, encode_indices, encode_main_node, encode_normal, encode_normals,
    encode_positions, encode_tree, encode_trilists, inflate, leaves, main_regions, read_chunk,
)
from rusemod.tms import encode_parents

BOUNDS = ((0.0, 0.0, 9.0), (491520.0, 491520.0, 117000.0))
# subtree 0: four vertices, one stored relative to an earlier vertex; subtree 1: two vertices
POSITIONS = [[(10, 20, 30), (40, 20, 35), (12, 25, 33), (39, 21, 36)], [(100, 200, 300), (0, 32767, 5)]]
PARENTS = [[0, 0, 0, 1], [0, 0]]
# normals with |b| <= 0.25, so they survive the 12-bit field (the wrap has its own test)
NORMALS = [[(0.0, 0.0, 1.0), (0.1, -0.2, 0.9), (-0.9, 0.1, 0.2), (0.15, 0.7, 0.1)],
           [(0.0, 0.0, -1.0), (0.3, 0.05, 0.9)]]


def game_chunk(data: bytes) -> bytes:
    """A framed chunk with zlib bytes unlike compress()'s (level 1, a different dictionary) but the same content."""
    co = zlib.compressobj(1)
    stream = co.compress(data) + co.flush(zlib.Z_SYNC_FLUSH)
    return struct.pack("<II", len(stream) + 4, len(data)) + stream


def hand_positions(positions, parents, fill=0xDD) -> bytes:
    """The inflated positions chunk laid out by hand (residuals, parent codes, then junk fill)."""
    n = len(positions)
    res = []
    for i, q in enumerate(positions):
        p = positions[parents[i]] if i else (0, 0, 0)
        res += [(q[k] - p[k]) & 0x7FFF for k in range(3)]
    body = struct.pack(f"<II{3 * n}H", n, 0x7FFF, *res) + encode_parents(parents)
    return body + bytes([fill]) * (8 + 12 * n - len(body))


def hand_normal(n) -> int:
    """The packed normal laid out by hand: dominant axis tag, a in the top 16 bits, b in 12 bits (wrapping)."""
    k = max(range(3), key=lambda i: abs(n[i]))
    a, b = n[(k + 1) % 3] / abs(n[k]), n[(k + 2) % 3] / abs(n[k])
    return (round(a * 32768) + 32768) << 16 | (round(b * 8192) % 4096) << 4 | 2 * k + (n[k] > 0)


def hand_storage(positions=POSITIONS, parents=PARENTS, normals=NORMALS, opaque=None):
    """Storage and its region offsets, laid out by hand in the documented order."""
    n_sub = len(positions)
    opaque = opaque or {"indices": [b"\x01\x02\x03" * 5, b"\x07"], "trilists": [b"T0" * 9, b"T1T1T1"],
                        "trees": [b"S0" * 20, b"S1" * 3], "main": b"MAIN" * 5 + b"xyz"}
    out, off = bytearray(), {}
    vstarts = []
    for s in range(n_sub):
        vstarts.append(len(out))
        out += game_chunk(hand_positions(positions[s], parents[s]))
        out += game_chunk(struct.pack(f"<{len(normals[s])}I", *(hand_normal(v) for v in normals[s])))
    off["OffsetOfVertexBufferIndexes"] = len(out)
    out += struct.pack(f"<{n_sub}I", *vstarts)
    off["OffsetOfIndexBuffer"] = base = len(out)
    starts = []
    for s in range(n_sub):
        starts.append(len(out) - base)
        count = opaque["counts"][s] if "counts" in opaque else 3 * (s + 5)
        out += struct.pack("<I", count) + game_chunk(opaque["indices"][s])
    off["OffsetOfIndexBufferIndexes"] = len(out)
    out += struct.pack(f"<{n_sub}I", *starts)
    off["OffsetOfTriangleIndexLists"] = base = len(out)
    starts = []
    for s in range(n_sub):
        starts.append(len(out) - base)
        out += game_chunk(opaque["trilists"][s])
    off["OffsetOfTriangleIndexBufferIndexes"] = len(out)
    out += struct.pack(f"<{n_sub}I", *starts)
    while len(out) % 8:
        out.append(0)
    off["OffsetOfMainNode"] = len(out)
    out += opaque["main"]
    trees = [game_chunk(t) for t in opaque["trees"]]
    off["OffsetOfCompressedSubtreeIndexBuffer"] = len(out)
    pos = 0
    for t in trees:
        out += struct.pack("<I", pos)
        pos += len(t)
    off["OffsetOfCompressedSubtrees"] = len(out)
    for t in trees:
        out += t
    return bytes(out), off


def tag(kind: int, axis: int, rest: int, value: float) -> bytes:
    return struct.pack("<If", (kind << 28) | (rest << 2) | axis, value)


# Real parts for the two subtrees, laid out by hand from the documented encodings:
#   subtree 0: triangles (0 1 2) (1 3 2): history codes 0 1 2 1 3 2; a split on x at 25 with two leaves that list
#   both triangles; subtree 1: the degenerate triangle (0 1 0); a keep-below clip on z at 400 over one leaf.
#   MainNode: the six bounding clips, a split on x, and a leaf for each subtree. TriangleCount: 3 distinct.
VALID_PARTS = {
    "counts": [6, 3],
    "indices": [bytes((0x10, 0x12, 0x23)), bytes((0x10, 0x01))],
    "trees": [bytes((0x40, 25, 0x81, 0x81)), bytes((0x11, 0x90, 0x80))],
    "trilists": [bytes((0x40, 0x41, 0x40, 0x41)), bytes((0x40,))],
    "main": (tag(0, 0, 0, 491520.0) + tag(2, 0, 0, 0.0) + tag(0, 1, 0, 491520.0) + tag(2, 1, 0, 0.0)
             + tag(0, 2, 0, 117000.0) + tag(2, 2, 0, 9.0) + tag(4, 0, 4, 245760.0) + tag(5, 0, 0, 0.0)
             + tag(5, 0, 1, 0.0)),
}


def make_valid_kdt() -> bytes:
    storage, off = hand_storage(opaque=VALID_PARTS)
    return make_kdt(storage, off, triangle_count=3)


def make_kdt(storage=None, offsets=None, subtree_count=2, triangle_count=17, cls="TStreamedMeshKdTree",
             bounds_min=BOUNDS[0]) -> bytes:
    """The NDF wrapper around a hand-made Storage, with the shipped property order. A None `bounds_min` leaves the
    property out, as the shipped files do for a zero minimum."""
    if storage is None:
        storage, offsets = hand_storage()
    values = {"RTVersion": val(0x07, struct.pack("<I", 0)),
              "BoundingBoxMax": val(0x0B, struct.pack("<3f", *BOUNDS[1])),
              "TriangleCount": val(0x03, struct.pack("<I", triangle_count)),
              "IsStreamPacked": val(0x00, b"\x01"), "IsCompressed": val(0x00, b"\x01"),
              "SubtreeCount": val(0x03, struct.pack("<I", subtree_count)),
              "Storage": val(0x14, struct.pack("<I", len(storage)) + storage)}
    for name in OFFSETS:
        values[name] = val(0x03, struct.pack("<I", offsets[name]))
    order = ["RTVersion", "BoundingBoxMin", "BoundingBoxMax", "TriangleCount", "OffsetOfMainNode",
             "OffsetOfTriangleIndexLists", "OffsetOfIndexBuffer", "OffsetOfCompressedSubtrees",
             "OffsetOfCompressedSubtreeIndexBuffer", "OffsetOfVertexBufferIndexes", "OffsetOfIndexBufferIndexes",
             "OffsetOfTriangleIndexBufferIndexes", "IsStreamPacked", "IsCompressed", "SubtreeCount", "Storage"]
    if bounds_min is not None:
        values["BoundingBoxMin"] = val(0x0B, struct.pack("<3f", *bounds_min))
    else:
        order.remove("BoundingBoxMin")
    return make_ndf(objects=[(0, [(i, values[name]) for i, name in enumerate(order)])], classes=[cls],
                    props=[(name, 0) for name in order], strings=["1.1.4"], topo=[0])


def close(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def unit(n):
    length = math.sqrt(sum(x * x for x in n))
    return tuple(x / length for x in n)


class Chunks(unittest.TestCase):
    def test_compress_frames_a_sync_flushed_stream_that_inflates_back(self):
        data = bytes(range(256)) * 3
        c = compress(data)
        ln, size = struct.unpack_from("<II", c, 0)
        self.assertEqual((ln, size, len(c)), (len(c) - 4, len(data), 4 + ln))
        self.assertEqual(c[-4:], b"\x00\x00\xff\xff")          # sync flush marker, no final block
        self.assertEqual(inflate(c), data)
        self.assertEqual(read_chunk(c + b"tail", 0), (c, len(c)))

    def test_inflate_checks_the_announced_size(self):
        c = bytearray(compress(b"abc"))
        struct.pack_into("<I", c, 4, 7)
        with self.assertRaises(ValueError):
            inflate(bytes(c))

    def test_read_chunk_refuses_a_truncated_chunk(self):
        with self.assertRaises(ValueError):
            read_chunk(compress(b"abc")[:-1], 0)


class Positions(unittest.TestCase):
    def test_hand_made_chunk_decodes(self):
        pos, par = decode_positions(hand_positions(POSITIONS[0], PARENTS[0]))
        self.assertEqual((pos, par), (POSITIONS[0], PARENTS[0]))

    def test_encode_matches_the_hand_layout_and_fills_with_aa(self):
        enc = encode_positions(POSITIONS[0], PARENTS[0])
        self.assertEqual(enc, hand_positions(POSITIONS[0], PARENTS[0], fill=FILL))
        self.assertEqual(len(enc), 8 + 12 * 4)
        self.assertEqual(decode_positions(enc), (POSITIONS[0], PARENTS[0]))

    def test_wrap_around_the_quantized_range(self):
        pos = [(0, 32767, 5), (32767, 0, 32767), (3, 3, 3)]
        self.assertEqual(decode_positions(encode_positions(pos))[0], pos)

    def test_default_parents_are_the_previous_vertex(self):
        pos, par = decode_positions(encode_positions(POSITIONS[0]))
        self.assertEqual((pos, par), (POSITIONS[0], [0, 0, 1, 2]))

    def test_refuses_bad_input(self):
        with self.assertRaises(ValueError):
            encode_positions([(0, 0, 32768)])
        with self.assertRaises(ValueError):
            encode_positions(POSITIONS[0], [0, 0, 2, 1])      # vertex 2 cannot point at itself
        with self.assertRaises(ValueError):
            decode_positions(struct.pack("<II", 1, 0xFFFF) + bytes(12))


class Normals(unittest.TestCase):
    def test_word_layout(self):
        self.assertEqual(encode_normal((0.0, 0.0, 1.0)), 0x80000005)         # +z, a = b = 0
        self.assertEqual(encode_normal((0.0, 0.0, -1.0)), 0x80000004)
        self.assertEqual(encode_normal((1.0, 0.0, 0.0)), 0x80000001)
        self.assertEqual(encode_normal((0.0, -1.0, 0.0)), 0x80000002)
        w = encode_normal((0.5, -0.25, 1.0))                                  # +z: a = 0.5, b = -0.25
        self.assertEqual(w >> 16, 32768 + 16384)
        self.assertEqual((w >> 4) & 0xFFF, (-2048) & 0xFFF)
        self.assertEqual(w & 15, 5)
        self.assertEqual(encode_normal((0.2, 0.7, 0.1)), hand_normal((0.2, 0.7, 0.1)))   # +y: a = z/y, b = x/y

    def test_decode_gives_the_unit_normal_back(self):
        for n in [(0.1, -0.2, 0.9), (-0.9, 0.1, 0.2), (0.15, 0.7, 0.1), (0.0, 0.0, -1.0), (0.7, 0.1, -0.7)]:
            self.assertTrue(close(decode_normal(encode_normal(n)), unit(n), 1e-4), n)

    def test_b_wraps_when_it_exceeds_a_quarter(self):
        n = (0.1, 0.4, 1.0)                                    # +z, b = 0.4: round(0.4 * 8192) = 3277 > 2047
        w = encode_normal(n)
        self.assertEqual((w >> 4) & 0xFFF, 3277 & 0xFFF)      # stored as the 12-bit wrap, not clamped
        wrapped = decode_normal(w)                             # reads back as b = (3277 - 4096) / 8192
        self.assertTrue(close(wrapped, unit((0.1, (3277 - 4096) / 8192, 1.0)), 1e-4))
        self.assertEqual(encode_normal(wrapped), w)            # and re-encodes to the same word
        m = (-0.3, 1.0, 0.0)                                   # +y, b = x/y = -0.3 wraps the other way
        self.assertEqual((encode_normal(m) >> 4) & 0xFFF, (-2458) & 0xFFF)

    def test_every_word_survives_decode_then_encode(self):
        # 0x8635 is the shipped tie (a = -1: x and z equal, tagged z); 0xFF5 is the same tie at the other end of b
        for w in [0x8635, 0x1234_5675, 0xFFFF_FFF0, 0x0000_0FF5, 0x7FFF_8003, 0x8000_0001, 0x8000_0004]:
            self.assertEqual(encode_normal(decode_normal(w)), w, hex(w))

    def test_tie_picks_the_later_axis(self):
        self.assertEqual(encode_normal((-0.7, -0.1, 0.7)) & 15, 5)
        self.assertEqual(encode_normal((0.5, 0.5, 0.1)) & 15, 3)

    def test_a_at_one_is_clamped_to_the_field(self):
        self.assertEqual(encode_normal((0.7, 0.1, 0.7)) >> 16, 0xFFFF)

    def test_chunk_and_bad_input(self):
        data = encode_normals(NORMALS[0])
        self.assertEqual(len(data), 16)
        self.assertEqual(data, struct.pack("<4I", *(hand_normal(n) for n in NORMALS[0])))
        for got, want in zip(decode_normals(data), NORMALS[0]):
            self.assertTrue(close(got, unit(want), 1e-4))
        with self.assertRaises(ValueError):
            encode_normal((0.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            decode_normal(0x8000_0006)
        with self.assertRaises(ValueError):
            decode_normals(b"\0\0\0")


class Container(unittest.TestCase):
    def setUp(self):
        self.raw = make_kdt()
        self.k = Kdt(self.raw)

    def test_parts(self):
        k = self.k
        self.assertEqual((len(k.subtrees), k.triangle_count, k.bounds_min, k.bounds_max), (2, 17, *BOUNDS))
        self.assertEqual([t.count for t in k.subtrees], [4, 2])
        self.assertEqual([t.index_count for t in k.subtrees], [15, 18])
        self.assertEqual(inflate(k.subtrees[1].indices), b"\x07")
        self.assertEqual(inflate(k.subtrees[0].trilist), b"T0" * 9)
        self.assertEqual(inflate(k.subtrees[1].tree), b"S1" * 3)
        self.assertEqual(k.main_node, b"MAIN" * 5 + b"xyz")

    def test_decoded_vertices(self):
        for s in range(2):
            self.assertEqual(self.k.positions(s), POSITIONS[s])
            self.assertEqual(self.k.parents(s), PARENTS[s])
            for got, want in zip(self.k.normals(s), NORMALS[s]):
                self.assertTrue(close(got, unit(want), 1e-4))

    def test_unchanged_file_rebuilds_byte_identical(self):
        self.assertEqual(self.k.to_bytes(), self.raw)

    def test_rebuild_recomputes_tables_offsets_and_padding_from_the_parts(self):
        storage, off = hand_storage()
        wrong = {name: 0 for name in off}
        k = Kdt(make_kdt(storage, off))
        for name in OFFSETS:                                   # scramble the properties, the writer restores them
            k._values[name].set_scalar(wrong[name])
        k._values["SubtreeCount"].set_scalar(9)
        self.assertEqual(k.to_bytes(), self.raw)

    def test_storage_offsets_match_the_hand_layout(self):
        storage, off = hand_storage()
        blob, got = self.k.storage()
        self.assertEqual((blob, got), (storage, off))

    def test_refuses_a_file_whose_tables_disagree(self):
        storage, off = hand_storage()
        bad = bytearray(storage)
        struct.pack_into("<I", bad, off["OffsetOfVertexBufferIndexes"] + 4, 1)
        with self.assertRaises(ValueError):
            Kdt(make_kdt(bytes(bad), off))
        moved = dict(off, OffsetOfMainNode=off["OffsetOfMainNode"] + 8)
        with self.assertRaises(ValueError):
            Kdt(make_kdt(storage, moved))
        with self.assertRaises(ValueError):
            Kdt(make_kdt(storage, off, subtree_count=1))
        with self.assertRaises(ValueError):
            Kdt(make_kdt(cls="TOtherThing"))

    def test_a_left_out_minimum_reads_as_zero_and_stays_left_out(self):
        raw = make_kdt(bounds_min=None)
        k = Kdt(raw)
        self.assertEqual(k.bounds_min, (0.0, 0.0, 0.0))
        self.assertEqual(k.to_bytes(), raw)
        self.assertEqual(k.to_world(2, 32767), 117000.0)
        k.bounds_min = (0.0, 0.0, 5.0)
        with self.assertRaises(ValueError):
            k.to_bytes()

    def test_world_coordinates(self):
        k = self.k
        self.assertAlmostEqual(k.to_world(0, 32767), 491520.0)
        self.assertAlmostEqual(k.to_world(2, 0), 9.0)
        self.assertEqual(k.to_quant(1, 491520.0), 32767)
        self.assertEqual(k.to_quant(2, k.to_world(2, 1234)), 1234)


class Editing(unittest.TestCase):
    def setUp(self):
        self.raw = make_kdt()
        self.k = Kdt(self.raw)

    def test_replacing_positions_keeps_everything_else_and_reads_back(self):
        k = self.k
        new = [(11, 21, 31), (41, 21, 36), (13, 26, 34), (40, 22, 37)]
        k.set_positions(0, new)
        out = k.to_bytes()
        self.assertNotEqual(out, self.raw)
        r = Kdt(out)
        self.assertEqual(r.positions(0), new)
        self.assertEqual(r.parents(0), PARENTS[0])                        # the subtree's own parents were kept
        self.assertEqual(r.positions(1), POSITIONS[1])
        self.assertEqual(r.subtrees[0].normals, k.subtrees[0].normals)   # untouched chunks keep their bytes
        self.assertEqual(r.subtrees[1], k.subtrees[1])
        self.assertEqual(r.main_node, k.main_node)
        self.assertEqual([t.index_count for t in r.subtrees], [15, 18])
        self.assertEqual(r.to_bytes(), out)
        got, want = r.storage()[1], {name: r._values[name].scalar() for name in OFFSETS}
        self.assertEqual(got, want)
        self.assertEqual(want["OffsetOfMainNode"] % 8, 0)

    def test_replacing_normals(self):
        k = self.k
        new = [(0.3, 0.1, 1.0), (0.0, 0.0, 1.0)]
        k.set_normals(1, new)
        r = Kdt(k.to_bytes())
        for got, want in zip(r.normals(1), new):
            self.assertTrue(close(got, unit(want), 1e-4))
        self.assertEqual(r.positions(1), POSITIONS[1])
        self.assertEqual(r.subtrees[0], k.subtrees[0])

    def test_own_parents_can_be_given(self):
        k = self.k
        k.set_positions(0, POSITIONS[0], [0, 0, 1, 2])
        r = Kdt(k.to_bytes())
        self.assertEqual((r.positions(0), r.parents(0)), (POSITIONS[0], [0, 0, 1, 2]))

    def test_size_and_count_changes_are_rebuilt(self):
        k = self.k
        k.set_positions(1, [(1, 2, 3), (4, 5, 6)])
        k.subtrees[0].trilist = compress(b"a much longer triangle list " * 40)
        k.main_node = b"M" * 13
        k.triangle_count = 99
        r = Kdt(k.to_bytes())
        self.assertEqual((r.triangle_count, r.main_node, r.positions(1)), (99, b"M" * 13, [(1, 2, 3), (4, 5, 6)]))
        self.assertEqual(inflate(r.subtrees[0].trilist), b"a much longer triangle list " * 40)
        self.assertEqual(r.subtrees[1].tree, k.subtrees[1].tree)

    def test_vertex_count_must_match(self):
        with self.assertRaises(ValueError):
            self.k.set_positions(0, POSITIONS[1])
        with self.assertRaises(ValueError):
            self.k.set_normals(1, NORMALS[0])


class Indices(unittest.TestCase):
    """The index buffer: 4-bit codes over a move-to-front history of the last 8 values (seeded 0..7)."""

    def test_history_codes(self):
        self.assertEqual(decode_indices(bytes((0x10, 0x12, 0x23)), 6), [0, 1, 2, 1, 3, 2])
        self.assertEqual(encode_indices([0, 1, 2, 1, 3, 2]), bytes((0x10, 0x12, 0x23)))

    def test_small_step(self):
        self.assertEqual(decode_indices(bytes((0xA7,)), 2), [7, 9])     # 7 from the history, then 7 + 2
        self.assertEqual(encode_indices([7, 9]), bytes((0xA7,)))

    def test_one_byte_escape_at_an_odd_nibble_reads_high_nibble_first(self):
        self.assertEqual(decode_indices(bytes((0x5F, 0x04)), 1), [20])  # 15, then the byte 0x54 = 20 + 0x40
        self.assertEqual(encode_indices([20]), bytes((0x5F, 0x04)))

    def test_two_byte_escape_at_an_even_nibble(self):
        self.assertEqual(decode_indices(bytes((0xF0, 0xC0, 0x64)), 2), [0, 100])
        self.assertEqual(encode_indices([0, 100]), bytes((0xF0, 0xC0, 0x64)))

    def test_round_trip_and_checks(self):
        import random
        rnd = random.Random(7)
        values = [rnd.choice((rnd.randrange(3000), rnd.randrange(40))) for _ in range(900)]
        self.assertEqual(decode_indices(encode_indices(values), len(values)), values)
        with self.assertRaises(ValueError):
            decode_indices(bytes((0x10, 0x12, 0x23, 0x00)), 6)            # bytes left over
        with self.assertRaises(ValueError):
            encode_indices([0, 20000])                                    # a step the escape can't hold


class Trees(unittest.TestCase):
    """The subtree k-d tree: pre-order node codes, values relative to the nearest ancestor on the same axis."""

    def test_hand_made_tree(self):
        root = decode_tree(bytes((0x40, 25, 0x81, 0x81)))
        self.assertEqual(root, Split(0, 25, Leaf(2), Leaf(2)))
        self.assertEqual([(lo, hi) for _, lo, hi in leaves(root)], [((25, None, None), (None, None, None)),
                                                                      ((None, None, None), (25, None, None))])
        clip = decode_tree(bytes((0x11, 0x90, 0x80)))                   # 9-bit narrow value: 0x190 = 400
        self.assertEqual(clip, Clip(2, 400, False, Leaf(1)))
        self.assertEqual(leaves(clip)[0][1:], ((None, None, None), (None, None, 400)))

    def test_values_are_relative_to_the_nearest_ancestor_on_the_same_axis(self):
        root = Split(0, 1000, Clip(2, 500, True, Split(0, 1200, Leaf(1), Leaf(3, 2))),
                     Clip(0, 800, False, Leaf(32)))
        raw = encode_tree(root)
        # x 1000 (wide, since 0x3E8 > 0x1FF); z 500 keeping above (narrow: 0x1F4 fits 9 bits); x +200 from the
        # split above (narrow); a leaf; a leaf of variant 2; x -200 from 1000 (narrow, negative); a leaf of 32 (the
        # count escape)
        self.assertEqual(raw, bytes((0x44, 0x03, 0xE8, 0x31, 0xF4, 0x40, 0xC8, 0x80, 0xC2, 0x02, 0xC8, 0x9F, 31)))
        self.assertEqual(decode_tree(raw), root)

    def test_round_trip_of_random_trees(self):
        import random
        rnd = random.Random(3)

        def make(depth):
            if depth == 0 or rnd.random() < 0.3:
                return Leaf(rnd.choice((1, 5, 31, 32, 200, 256)), rnd.randrange(4))
            axis, value = rnd.randrange(3), rnd.randrange(32768)
            if rnd.random() < 0.5:
                return Split(axis, value, make(depth - 1), make(depth - 1))
            return Clip(axis, value, rnd.random() < 0.5, make(depth - 1))

        for _ in range(50):
            root = make(7)
            self.assertEqual(decode_tree(encode_tree(root)), root)
        with self.assertRaises(ValueError):
            encode_tree(Leaf(257))
        with self.assertRaises(ValueError):
            decode_tree(bytes((0x81, 0x81)))                              # a byte after the root's last node


class TriangleLists(unittest.TestCase):
    def test_short_and_long_forms(self):
        lists = [[0, 1, 70, 69], [5000], []]
        raw = encode_trilists(lists)
        self.assertEqual(raw, bytes((0x40, 0x41, 0x80, 0, 0, 70, 0x3F, 0x80, 0, 0x13, 0x88)))
        self.assertEqual(decode_trilists(raw, [4, 1, 0]), lists)
        with self.assertRaises(ValueError):
            decode_trilists(raw + bytes((0x40,)), [4, 1, 0])


class MainNode(unittest.TestCase):
    def test_walk_gives_each_subtree_its_region(self):
        entries = decode_main_node(VALID_PARTS["main"])
        self.assertEqual(encode_main_node(entries), VALID_PARTS["main"])
        self.assertEqual(entries[6], (4, 0, 4, 245760.0))
        regions = main_regions(entries)
        self.assertEqual(sorted(regions), [0, 1])
        self.assertEqual(regions[0], ((245760.0, 0.0, 9.0), (491520.0, 491520.0, 117000.0), [0, 1, 2, 3, 4, 5]))
        self.assertEqual(regions[1][:2], ((0.0, 0.0, 9.0), (245760.0, 491520.0, 117000.0)))

    def test_a_subtree_reached_twice_is_an_error(self):
        entries = decode_main_node(tag(4, 0, 4, 1.0) + tag(5, 0, 0, 0.0) + tag(5, 0, 0, 0.0))
        with self.assertRaises(ValueError):
            main_regions(entries)


class Parts(unittest.TestCase):
    """The file's own accessors for the index buffers, trees, lists and the MainNode, on a valid made-up file."""

    def test_read_edit_and_rebuild(self):
        raw = make_valid_kdt()
        k = Kdt(raw)
        self.assertEqual((k.indices(0), k.indices(1)), ([0, 1, 2, 1, 3, 2], [0, 1, 0]))
        self.assertEqual(k.tree(1), Clip(2, 400, False, Leaf(1)))
        self.assertEqual(k.trilists(0), [[0, 1], [0, 1]])
        self.assertEqual(len(k.main_entries()), 9)
        k.set_indices(0, [0, 1, 2, 1, 3, 2, 2, 3, 0])
        k.set_tree(0, Split(0, 25, Leaf(3), Clip(2, 40, False, Leaf(3))), [[0, 1, 2], [0, 1, 2]])
        r = Kdt(k.to_bytes())
        self.assertEqual((r.subtrees[0].index_count, r.indices(0)), (9, [0, 1, 2, 1, 3, 2, 2, 3, 0]))
        self.assertEqual(r.trilists(0), [[0, 1, 2], [0, 1, 2]])
        self.assertEqual(r.subtrees[1], k.subtrees[1])
        with self.assertRaises(ValueError):
            k.set_indices(1, [0, 1, 2])                                  # subtree 1 has 2 vertices
        with self.assertRaises(ValueError):
            k.set_tree(1, Leaf(2), [[0]])                                 # the list must be as long as the leaf
        self.assertEqual(Kdt(raw).to_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
