"""3D models: the mesh-pack reader (rusemod.spk), the LZ additions it needs (stored blocks, packed literals),
transparent DXT pictures, and the model cache the Studio draws from (rusemod.models), on made-up packs."""
import base64
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import dxt
from rusemod.models import map_models, medium_name, texture_member
from rusemod.spk import Spk, SpkError, layout
from rusemod.tms import lz_decode, lz_encode
from rusemod.tmst import make_tgv, zipo_pack

STORED = "$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__TexCoord0_2wn__TexPackedAtlas0_4ubn"
PACKED = "$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__TexCoord0_2f"
TEXTURE = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Decors\\Test\\TSCTest_diffuseTexture01.png"


def s(i):
    return val(0x07, struct.pack("<I", i))


def material_ndf() -> bytes:
    """One TMeshMaterial: diffuseTexture -> (the atlas path, 0), and its name."""
    textures = val(0x12, struct.pack("<I", 1) + s(0) + val(0x22, val(0x1C, struct.pack("<I", 1)) + val(0x03, bytes(4))))
    return make_ndf([(0, [(0, textures), (1, s(2))])], ["TMeshMaterial"], [("Textures", 0), ("MaterialName", 0)],
                    strings=["diffuseTexture", TEXTURE, "wall"])


def name_trie(entries) -> bytes:
    """A pack's name table: u32 10, 6 bytes, then one directory holding the models (name, box, mesh)."""
    files = b""
    for k, (name, box, mesh) in enumerate(entries):
        body = struct.pack("<6fIHH", *box, 0, mesh, 0xCDCD) + name.encode() + b"\0"
        node = struct.pack("<II", 0, 0) + body
        node += bytes(len(node) % 2)
        if k < len(entries) - 1:
            node = struct.pack("<II", 0, len(node)) + node[8:]
        files += node
    folder = b"ww2\\test\\\0"
    head = 8 + len(folder)
    head += head % 2
    root = struct.pack("<II", head, 0) + folder + bytes(head - 8 - len(folder))
    return struct.pack("<I", 10) + bytes(6) + root + files


def subp(kind: int, storage: int, mode: int, offset: int, payload: bytes) -> bytes:
    """One SUBP stream: header (12 bytes after the magic), u32 size, the payload, padded to 4."""
    head = b"SUBP" + struct.pack("<HBBBHHH", 12, kind, storage, mode, 0, offset, 0) + bytes(1)
    return head + struct.pack("<I", len(payload)) + payload + bytes(-len(payload) % 4)


def packed_vertices(positions, uvs) -> bytes:
    """A compressed vertex buffer: no predictor block (every parent the previous vertex), positions quantized to
    Q = 1023 over their box (LZ), normals raw (zlib), UVs as float2 quantized to Q = 255 (stored as is)."""
    n = len(positions)
    Q = 1023
    lo = [min(p[k] for p in positions) for k in range(3)]
    hi = [max(p[k] for p in positions) for k in range(3)]
    q = [[round((p[k] - lo[k]) / (hi[k] - lo[k]) * Q) if hi[k] > lo[k] else 0 for k in range(3)] for p in positions]
    deltas = [q[0]] + [[(q[i][k] - q[i - 1][k]) & Q for k in range(3)] for i in range(1, n)]
    pos = struct.pack("<H3f3fH", Q, *lo, *hi, 0) + struct.pack(f"<{3 * n}H", *[c for d in deltas for c in d])
    Quv = 255
    uq = [[round(u[k] * Quv) for k in range(2)] for u in uvs]
    ud = [uq[0]] + [[(uq[i][k] - uq[i - 1][k]) & Quv for k in range(2)] for i in range(1, n)]
    uv = struct.pack("<H2f2fH", Quv, 0.0, 0.0, 1.0, 1.0, 0) + struct.pack(f"<{2 * n}H", *[c for d in ud for c in d])
    nrm = bytes([128, 128, 255, 0] * n)
    head = b"VBUF" + struct.pack("<HBHHB", 8, 0xA1, 24, 3, 0)
    return head + subp(2, 3, 2, 0, lz_encode(pos)) + subp(4, 1, 0, 12, zlib.compress(nrm)) + subp(1, 0, 2, 16, uv)


def make_pack() -> bytes:
    """Two models: `walllod0` stored as is (2 triangles, UVs moved into an atlas corner), `wall_lodmediumlod0`
    compressed (the same quad: packed positions and UVs, an index buffer of zlib'd differences)."""
    quad = [(0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (100.0, 0.0, 50.0), (0.0, 0.0, 50.0)]
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    # `_2wn` as the game stores it: signed 16-bit fractions, u 0..1, v -1..0 (v - 1)
    stored = b"".join(struct.pack("<3f4B2H4B", *p, 128, 128, 255, 0, round(u[0] * 32767) & 0xFFFF,
                                  round((u[1] - 1) * 32767) & 0xFFFF, 0, 0, 128, 128) for p, u in zip(quad, uvs))
    packed = packed_vertices(quad, uvs)
    tri = [0, 1, 2, 0, 2, 3]
    ib_plain = struct.pack("<6H", *tri)
    diffs = [tri[0]] + [(tri[i] - tri[i - 1]) & 0xFFFF for i in range(1, len(tri))]
    raw = struct.pack("<6H", *diffs)
    ib_packed = struct.pack("<I", len(raw)) + zlib.compress(raw)[2:-4]  # raw deflate as the game's sync flush
    ib_packed = struct.pack("<I", len(raw)) + zlib.compressobj(wbits=15).compress(raw) + zlib.compressobj().flush()
    co = zlib.compressobj()
    ib_packed = struct.pack("<I", len(raw)) + co.compress(raw) + co.flush(zlib.Z_SYNC_FLUSH)
    names = name_trie([("walllod0.ase2ndfbin", (0, 0, 0, 100, 0, 50), 0),
                       ("wall_lodmediumlod0.ase2ndfbin", (0, 0, 0, 100, 0, 50), 1)])
    formats = struct.pack("<I", 256) + STORED.encode().ljust(256, b"\0") + PACKED.encode().ljust(256, b"\0")
    mats = material_ndf()
    meshes = struct.pack("<HHHH", 0, 1, 1, 1)
    draws = struct.pack("<6H", 0, 0, 0, 0, 0xFFFF, 0xCDCD) + struct.pack("<6H", 0, 0, 1, 1, 0xFFFF, 0xCDCD)
    ib_data = ib_plain + bytes(-len(ib_plain) % 4)
    ib_table = struct.pack("<IIIHH", 0, len(ib_plain), 6, 1, 0) + struct.pack("<IIIHH", len(ib_data), len(ib_packed), 6, 1, 0xC000)
    ib_data += ib_packed
    vb_data = stored + packed
    vb_table = struct.pack("<IIIHH", 0, len(stored), 4, 0, 0) + struct.pack("<IIIHH", len(stored), len(packed), 4, 1, 0xC000)
    body = bytearray()
    at = 0xC4
    offsets = {}
    for key, blob in (("names", names), ("formats", formats), ("materials", mats), ("meshes", meshes),
                      ("draws", draws), ("ib_table", ib_table), ("vb_table", vb_table), ("ib", ib_data), ("vb", vb_data)):
        offsets[key] = at + len(body)
        body += blob + bytes(-len(blob) % 4)
    head = bytearray(0xC4)
    head[0:8] = b"MESHPCPC"
    sections = [("names", len(names), 2), ("formats", len(formats), 2), ("materials", len(mats), 1), (None, 0, 0),
                (None, 0, 0), ("meshes", len(meshes), 2), ("draws", len(draws), 2), ("ib_table", len(ib_table), 2)]
    for i, (key, size, count) in enumerate(sections):
        struct.pack_into("<III", head, 0x34 + 12 * i, offsets[key] if key else offsets["meshes"], size, count)
    struct.pack_into("<II", head, 0x94, offsets["ib"], len(ib_data))
    struct.pack_into("<III", head, 0x9C, offsets["vb_table"], len(vb_table), 2)
    struct.pack_into("<II", head, 0xA8, offsets["vb"], len(vb_data))
    raw_pack = bytes(head) + bytes(body)
    struct.pack_into("<II", head, 8, 4, len(raw_pack))
    return bytes(head) + bytes(body)


class Lz(unittest.TestCase):
    def test_stored_blocks_and_packed_literals(self):
        stored = struct.pack("<BBBBIIIHH", 1, 0x14, 0x88, 0, 5, 0, 0, 0, 0)[:8] + b"hello"
        self.assertEqual(lz_decode(stored), b"hello")
        # 5-bit literals, least significant bit first: 3, 17, 31 then an end bit
        vals, width = [3, 17, 31], 5
        bits = sum(v << (i * width) for i, v in enumerate(vals))
        lits = bits.to_bytes(2, "little")
        body = struct.pack("<BBBBIIIHH", 1, 0x14, width, 0, 3, 3, 0, (0x14 + 4) >> 2, 0) + struct.pack("<I", 1 << 3) + lits
        self.assertEqual(lz_decode(body + bytes(8)), bytes(vals))
        self.assertEqual(lz_decode(lz_encode(b"abcabcabcabc")), b"abcabcabcabc")  # the terrain's streams still read


class Pack(unittest.TestCase):
    def setUp(self):
        self.spk = Spk(make_pack())

    def test_names_formats_and_materials(self):
        self.assertEqual(sorted(self.spk.items), ["ww2\\test\\wall_lodmediumlod0.ase2ndfbin", "ww2\\test\\walllod0.ase2ndfbin"])
        self.assertEqual(self.spk.items["ww2\\test\\walllod0.ase2ndfbin"].box, (0, 0, 0, 100, 0, 50))
        self.assertEqual([c for c, _o, _s in layout(STORED)],
                         ["Position_3f", "NormalIn01_4ubn", "TexCoord0_2wn", "TexPackedAtlas0_4ubn"])
        self.assertEqual(self.spk.materials(), [{"name": "wall", "type": "", "textures": {"diffuseTexture": TEXTURE},
                                                 "skinning": [], "tags": []}])

    def test_signed_uv_words(self):
        from rusemod.spk import wn_uv
        # plain buffers: whole signed 16-bit words; u 0..1, v -1..0 moved up by 1
        self.assertEqual(wn_uv(0, 0x8001), (0.0, 0.0))
        self.assertEqual(wn_uv(32767, 0), (1.0, 1.0))
        u, v = wn_uv(16384, 0xC000)  # u 0.5, v -0.5 -> 0.5
        self.assertAlmostEqual(u, 0.5, 3)
        self.assertAlmostEqual(v, 0.5, 3)
        # compressed buffers: 11-bit values (mask 2047), the words' top bits
        u, v = wn_uv(512, 1536, bits=11)
        self.assertAlmostEqual(u, 0.5, 3)
        self.assertAlmostEqual(v, 0.5, 3)

    def test_a_stored_model_with_its_atlas_corner(self):
        (part,) = self.spk.model("ww2\\test\\walllod0.ase2ndfbin")
        self.assertEqual(part.indices, [0, 1, 2, 0, 2, 3])
        self.assertEqual(part.positions[3:6], [100.0, 0.0, 0.0])
        self.assertAlmostEqual(part.normals[2], 1.0)
        # atlas bytes (0, 0, 128, 128): the whole UV range lands in the atlas's top-left half
        self.assertEqual([round(x, 3) for x in part.uvs[4:6]], [0.502, 0.502])

    def test_a_compressed_model_decodes_to_the_same_quad(self):
        (part,) = self.spk.model("WW2\\Test\\wall_lodmediumlod0.ase2ndfbin")
        self.assertEqual(part.indices, [0, 1, 2, 0, 2, 3])
        want = [0, 0, 0, 100, 0, 0, 100, 0, 50, 0, 0, 50]
        self.assertEqual([round(x, 1) for x in part.positions], want)
        self.assertEqual([round(x, 2) for x in part.uvs], [0, 0, 1, 0, 1, 1, 0, 1])

    def test_not_a_pack(self):
        with self.assertRaises(SpkError):
            Spk(b"MESHPCPC" + struct.pack("<I", 3) + bytes(200))


class Pictures(unittest.TestCase):
    def test_transparent_dxt1_and_dxt5(self):
        red, black = dxt.pack565(255, 0, 0), 0
        block = struct.pack("<HHI", black, red, 0xFFFFFFFF)  # c0 <= c1: index 3 is transparent
        self.assertEqual(bytes(dxt.decode_rgba(block, 4, 4)[:4]), b"\0\0\0\0")
        alpha = bytes([200, 100]) + (1 << 0).to_bytes(6, "little")  # pixel 0 index 1 (100), the others index 0 (200)
        five = alpha + struct.pack("<HHI", red, black, 0)
        rgba = dxt.decode_rgba(five, 4, 4, "DXT5")
        self.assertEqual((rgba[0], rgba[3], rgba[7]), (255, 100, 200))
        png = dxt.png_bytes(bytes(rgba), 4, 4, channels=4)
        self.assertEqual(png[25], 6)  # colour type 6: RGBA

    def test_names(self):
        self.assertEqual(texture_member(TEXTURE), "gen\\ww2\\res3d\\decors\\test\\tsctest_diffusetexture01.tgv")
        self.assertEqual(medium_name("ww2\\a\\houselod0.ase2ndfbin"), "ww2\\a\\house_lodmediumlod0.ase2ndfbin")


class Cache(unittest.TestCase):
    def test_a_maps_models_and_atlas_written_once(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        game = Path(tmp.name, "game")
        rev = game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        green = dxt.pack565(0, 200, 0)
        blocks = struct.pack("<HHI", green, green, 0) * 4  # an 8 x 8 atlas, one colour
        tgv = make_tgv(8, 8, "DXT1", [zipo_pack(blocks)])
        (rev / "ZZ_Win.dat").write_bytes(make_edat([
            ("dir", "gen_5\\pack\\", [("file", "test.spk", make_pack())]),
            ("dir", "gen\\ww2\\res3d\\decors\\test\\", [("file", "tsctest_diffusetexture01.tgv", tgv)])]))
        types = [["Wall", "building", "Test/Walls", "ww2\\test\\walllod0.ase2ndfbin", ["ww2\\test\\walllod0.ase2ndfbin"]],
                 ["Nothing", "prop", "Test", "", []]]
        out = Path(tmp.name, "cache")
        index = map_models(game, types, out)
        (part,) = index["models"]["0"]  # its lighter version is the one drawn
        self.assertEqual((part["vertices"], part["triangles"], part["texture"]), (4, 2, TEXTURE))
        self.assertNotIn("1", index["models"])
        blob = (out / index["bin"]).read_bytes()
        self.assertEqual(struct.unpack_from("<3f", blob, part["positions"] + 12), (100.0, 0.0, 0.0))
        png = (out / index["textures"][TEXTURE]).read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(map_models(game, types, out), index)  # the second time it's read back


if __name__ == "__main__":
    unittest.main()
