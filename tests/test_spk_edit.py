"""3D model packs, writing (rusemod.spk_edit): the rebuild, the header hash, the name trie, and copying a model with
its materials between packs, on made-up packs shaped like the game's (a material list, shared parameter objects)."""
import struct
import unittest

from fixtures import make_ndf, val
from test_spk import TEXTURE, make_pack
from rusemod.ndf import Ndf
from rusemod.spk import Spk, SpkError
from rusemod.spk_edit import (NO_SKELETON, Buffer, Chunk, Model, Pack, RoadPiece, build_names, cell_ids,
                              header_hash, hilbert, material_list, read_chunks, read_names, road_vertices, write_chunks)

LIST, MAT, FLOAT = 0, 1, 2


def ref(obj, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, obj, cls))


def s(i):
    return val(0x07, struct.pack("<I", i))


def game_materials(name: str, texture: str = TEXTURE) -> bytes:
    """Like a shipped pack's materials: object 0 lists the materials; the material points at a shared float."""
    textures = val(0x12, struct.pack("<I", 1) + s(0) + val(0x22, val(0x1C, struct.pack("<I", 1)) + val(0x03, bytes(4))))
    params = val(0x12, struct.pack("<I", 1) + s(3) + ref(2, FLOAT))
    return make_ndf([(LIST, [(0, val(0x11, struct.pack("<I", 1) + ref(1, MAT)))]),
                     (MAT, [(1, textures), (2, s(2)), (3, params)]),
                     (FLOAT, [(0, val(0x05, struct.pack("<f", 0.5)))])],
                    ["TEugBListPBaseClass", "TMeshMaterial", "TEugBFloat"],
                    [("Value", LIST), ("Textures", MAT), ("MaterialName", MAT), ("ParameterDico", MAT)],
                    strings=["diffuseTexture", texture, name, "opacityPower"], topo=[0])


def game_pack(material: str = "wall", texture: str = TEXTURE, rename: bytes | None = None) -> bytes:
    """test_spk's two-model pack with game-shaped materials, written by the writer (so it follows the game's layout)."""
    p = Pack.from_bytes(make_pack())
    mats = game_materials(material, texture)
    p.materials, p.materials_raw, p.material_count = Ndf(mats), mats, 1
    if rename:
        for m in p.models:
            m.name = m.name.replace(b"wall", rename)
    return p.to_bytes()


class Rebuild(unittest.TestCase):
    def test_a_written_pack_reads_back_and_rewrites_the_same(self):
        raw = game_pack()
        self.assertEqual(Pack.from_bytes(raw).to_bytes(), raw)
        old, new = Spk(make_pack()), Spk(raw)
        for name in old.items:
            for a, b in zip(old.model(name), new.model(name)):
                self.assertEqual((a.positions, a.uvs, a.indices), (b.positions, b.uvs, b.indices))

    def test_header_hash_and_sizes(self):
        raw = game_pack()
        self.assertEqual(raw[0x10:0x20], header_hash(raw))
        size, = struct.unpack_from("<I", raw, 0x0C)
        z, start, start2, data = struct.unpack_from("<4I", raw, 0x20)
        self.assertEqual((size, z, start, start2 + data), (len(raw), 0, start2, len(raw)))
        self.assertEqual(struct.unpack_from("<I", raw, 0x30)[0], 2)

    def test_sections_start_on_4_bytes(self):
        raw = game_pack()
        for i in range(8):
            off, size, _n = struct.unpack_from("<III", raw, 0x34 + 12 * i)
            if size:
                self.assertEqual(off % 4, 0)


class Names(unittest.TestCase):
    ENTRY = struct.pack("<6fIHH", 0, 0, 0, 1, 1, 1, 0, 0, NO_SKELETON)

    def test_trie_round_trip_with_shared_folders(self):
        names = [b"ww2\\a\\b1lod0", b"ww2\\a\\b2lod0", b"ww2\\c\\dlod0", b"zz"]
        items = [(n, self.ENTRY) for n in names]
        raw = build_names(items)
        self.assertEqual(struct.unpack_from("<I", raw, 0)[0], 10)
        self.assertEqual(read_names(raw, 10, len(raw)), items)
        self.assertEqual(len(raw) % 2, 0)

    def test_new_names_go_in_folder_order(self):
        p = Pack.from_bytes(game_pack())
        for n in (b"ww2\\test\\us_10\\a", b"ww2\\test\\us_1\\b", b"ww2\\test\\aa"):
            p.add_model(Model(n, (0,) * 6, 0, 0))
        order = [m.name for m in p.models]
        self.assertLess(order.index(b"ww2\\test\\us_1\\b"), order.index(b"ww2\\test\\us_10\\a"))
        self.assertEqual(Spk(p.to_bytes()).items.keys(), {m.name.decode() for m in p.models})

    def test_a_name_twice_is_refused(self):
        p = Pack.from_bytes(game_pack())
        with self.assertRaises(SpkError):
            p.add_model(Model(p.models[0].name.upper(), (0,) * 6, 0, 0))


class Copy(unittest.TestCase):
    def test_copy_a_model_with_its_material(self):
        src = Pack.from_bytes(game_pack("tiger", "ZZ:\\GenTexGroup\\Tiger01.png", rename=b"tiger"))
        dst = Pack.from_bytes(game_pack())
        name = "ww2\\test\\tiger_lodmediumlod0.ase2ndfbin"
        new = dst.copy_model(src, name)
        self.assertEqual(new.mesh, 2)
        self.assertEqual(dst.draws[-1][0], new.mesh)  # a draw call's first u16 is its own mesh number
        raw = dst.to_bytes()
        out, orig = Spk(raw), Spk(game_pack("tiger", "ZZ:\\GenTexGroup\\Tiger01.png", rename=b"tiger"))
        self.assertEqual(len(out.items), 3)
        for a, b in zip(orig.model(name), out.model(name)):
            self.assertEqual((a.positions, a.normals, a.uvs, a.indices), (b.positions, b.normals, b.uvs, b.indices))
            self.assertEqual(out.materials()[b.material],
                             {"name": "tiger", "type": "", "textures": {"diffuseTexture": "ZZ:\\GenTexGroup\\Tiger01.png"}})
        self.assertEqual(struct.unpack_from("<III", raw, 0x34 + 24)[2], 2)  # the material count
        self.assertEqual(len(out.formats), 2)  # the vertex format was already there: not added twice
        # the copied material's shared float came along, and the list points at the new material
        nd = Ndf(raw[struct.unpack_from("<I", raw, 0x34 + 24)[0]:][:struct.unpack_from("<I", raw, 0x34 + 28)[0]])
        self.assertEqual([nd.classes[nd.objects[i].cls] for i in material_list(nd)], ["TMeshMaterial"] * 2)
        self.assertEqual(sum(1 for o in nd.objects if nd.classes[o.cls] == "TEugBFloat"), 2)
        # the pack's own models are untouched
        own = Spk(game_pack())
        for n in own.items:
            self.assertEqual([p.positions for p in own.model(n)], [p.positions for p in out.model(n)])

    def test_a_model_with_a_skeleton_isnt_copied_yet(self):
        src = Pack.from_bytes(game_pack(rename=b"tank"))
        src.models[0].skeleton = 3
        with self.assertRaises(SpkError):
            Pack.from_bytes(game_pack()).copy_model(src, src.models[0].name)

    def test_set_buffer(self):
        p = Pack.from_bytes(game_pack())
        p.set_buffer("ib", 0, struct.pack("<3H", 0, 1, 2), 3)
        out = Spk(p.to_bytes())
        self.assertEqual(out.indices(0), [0, 1, 2])
        self.assertEqual(p.ibs[0], Buffer(3, 1, 0, struct.pack("<3H", 0, 1, 2)))



class StaticMeshes(unittest.TestCase):
    def test_cell_ids_follow_a_hilbert_curve_over_the_squares_inside_the_map(self):
        ids = cell_ids((0, 0, 16 * 81920.0, 16 * 81920.0))      # a 16 x 16 map: the plain Hilbert index
        self.assertEqual(ids, {(x, y): hilbert(16, x, y) for x in range(16) for y in range(16)})
        ids = cell_ids((0, 0, 24 * 81920.0, 24 * 81920.0))      # 24 x 24 (Alpha): ranks along a 32 x 32 curve
        quads = {"x<16,y<16": [], "x<16,y>=16": [], "x>=16,y>=16": [], "x>=16,y<16": []}
        for (x, y), i in ids.items():
            quads[f"x{'<' if x < 16 else '>='}16,y{'<' if y < 16 else '>='}16"].append(i)
        self.assertEqual([(min(v), max(v)) for v in quads.values()], [(0, 255), (256, 383), (384, 447), (448, 575)])

    def test_chunk_sections_round_trip(self):
        p = Pack.from_bytes(game_pack())
        chunks = [Chunk((0, 0, 0, 1, 1, 11), 3, 0, 4, 0, 6), Chunk((1, 1, 0, 2, 2, 11), 7, 4, 4, 6, 6, 0, (5, b"abc"))]
        write_chunks(p, chunks, [(0, 1), (1, 1)])
        back = Pack.from_bytes(p.to_bytes())
        self.assertEqual(read_chunks(back), (chunks, [(0, 1), (1, 1)]))
        self.assertEqual(len(back.extra1[0]), 96)

    def test_a_road_piece_is_two_cross_sections_of_three(self):
        raw = road_vertices(RoadPiece((0.0, 0.0, 5.0), (100.0, 0.0, 6.0), (1.0, 0.0), (1.0, 0.0)))
        self.assertEqual(len(raw), 6 * 44)
        rows = [struct.unpack_from("<3f4B4Bf4B4f", raw, 44 * k) for k in range(6)]
        self.assertEqual([r[-1] for r in rows], [400.0] * 6)                       # v: the width
        self.assertEqual([r[-2] for r in rows], [-0.5, 0.0, 0.5] * 2)              # u across the road
        self.assertEqual(rows[0][3:5], (255, 128))                                 # the direction, n*127+128
        self.assertEqual(rows[0][7:9], (128, 1))                                   # turned: (t.y, -t.x)
        self.assertEqual(rows[0][12:16], (220, 220, 220, 100))
        self.assertEqual([r[2] for r in rows], [5.0] * 3 + [6.0] * 3)


if __name__ == "__main__":
    unittest.main()
