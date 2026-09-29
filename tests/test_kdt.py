"""Gameplay ground (.kdt): chunk codecs, container round trip and part replacement on a tiny made-up two-subtree
file (no game files). The file is laid out by hand from docs/FORMATS.md §6, independently of the writer."""
import contextlib
import io
import math
import os
import struct
import sys
import tempfile
import unittest
import zlib

from fixtures import make_edat, make_ndf, val
from rusemod.kdt import (
    FILL, OFFSETS, Kdt, compress, decode_normal, decode_normals, decode_positions, encode_normal, encode_normals,
    encode_positions, inflate, read_chunk,
)
from rusemod.tms import encode_parents

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import verify_kdt  # noqa: E402

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
        out += struct.pack("<I", 3 * (s + 5)) + game_chunk(opaque["indices"][s])
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


class VerifyTool(unittest.TestCase):
    def test_runs_on_a_made_up_game_folder(self):
        good = make_kdt()
        storage, off = hand_storage()
        bad = bytearray(good)
        i = bad.index(storage[:32])                  # break the first chunk's zlib bytes
        bad[i + 12] ^= 0xFF
        with tempfile.TemporaryDirectory() as root:
            maps = os.path.join(root, "Maps", "PC")
            os.makedirs(maps)
            for name, camera in (("Good", good), ("Bad", bytes(bad))):
                pack = make_edat([("dir", "output\\", [("file", "occlusioninfo_terrainonly.kdt", good),
                                                       ("file", "occlusioninfo_camera.kdt", camera)])])
                with open(os.path.join(maps, f"DataMap{name}_v09.dat"), "wb") as f:
                    f.write(pack)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = verify_kdt.main([root, "--only", "Good"])
            self.assertEqual(code, 0)
            self.assertIn("1 packs, 2 files, 0 failures", out.getvalue())
            self.assertIn("subtrees    2  vertices        6  OK", out.getvalue())
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = verify_kdt.main([root])
            self.assertEqual(code, 1)
            self.assertIn("2 packs, 4 files, 1 failures", out.getvalue())
            self.assertIn("Bad                      camera  subtrees    2  vertices", out.getvalue())
            self.assertIn("FAIL: subtree 0:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
