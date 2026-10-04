"""Game models to glTF (.glb), on the made-up mesh pack of test_spk (no game files)."""
import json
import struct
import unittest

from rusemod import gltf
from rusemod.spk import Spk

from test_spk import make_pack

NAME = "ww2\\test\\walllod0.ase2ndfbin"


class FakeLibrary:
    """What gltf.model_glb uses of rusemod.models.Library: the pack a model is in, its parts, its pictures."""

    def __init__(self):
        self.spk = Spk(make_pack())
        self.where = {NAME: self.spk}

    def parts(self, name):
        return [(p, "ZZ:\\GenTexGroup\\Test\\Wall01.png") for p in self.spk.model(name)]

    def picture(self, texture, most=512):
        return 2, 2, bytes([200, 100, 50, 255, 200, 100, 50, 0] * 2)


def read_glb(raw: bytes):
    magic, version, total = struct.unpack_from("<4sII", raw, 0)
    jlen, jtype = struct.unpack_from("<I4s", raw, 12)
    doc = json.loads(raw[20:20 + jlen])
    blen, btype = struct.unpack_from("<I4s", raw, 20 + jlen)
    return magic, version, total, jtype, btype, doc, raw[28 + jlen:28 + jlen + blen]


def accessor(doc, binary, i):
    a = doc["accessors"][i]
    v = doc["bufferViews"][a["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    code = {5126: "f", 5123: "H", 5125: "I"}[a["componentType"]]
    vals = struct.unpack_from(f"<{a['count'] * width}{code}", binary, v["byteOffset"])
    return [vals[k:k + width] for k in range(0, len(vals), width)]


class Glb(unittest.TestCase):
    def setUp(self):
        self.raw, self.pictures, self.summary = gltf.model_glb(FakeLibrary(), NAME)
        self.magic, self.version, self.total, self.jtype, self.btype, self.doc, self.bin = read_glb(self.raw)

    def test_container(self):
        self.assertEqual((self.magic, self.version, self.total), (b"glTF", 2, len(self.raw)))
        self.assertEqual((self.jtype, self.btype), (b"JSON", b"BIN\0"))
        self.assertEqual(self.doc["asset"]["version"], "2.0")
        self.assertEqual(self.summary["vertices"], 4)
        self.assertEqual(self.summary["triangles"], 2)

    def test_axes_scale_and_winding(self):
        prim = self.doc["meshes"][0]["primitives"][0]
        pos = accessor(self.doc, self.bin, prim["attributes"]["POSITION"])
        # the game's (100, 0, 50) -> glTF (x, z, y) x 0.01
        self.assertEqual([round(c, 4) for c in pos[2]], [1.0, 0.5, 0.0])
        tri = [i for (i,) in accessor(self.doc, self.bin, prim["indices"])]
        self.assertEqual(tri, [0, 2, 1, 0, 3, 2])  # (x, z, y) is a mirror: each triangle turned round
        self.assertEqual(self.doc["accessors"][prim["attributes"]["POSITION"]]["max"], [1.0, 0.5, 0.0])

    def test_colour_in_the_glb_alpha_beside_it(self):
        self.assertEqual(len(self.doc["images"]), 1)
        self.assertEqual(sorted(self.pictures), ["wall_Wall01_alpha.png", "wall_Wall01_colour.png"])
        for png in self.pictures.values():
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        prim = self.doc["meshes"][0]["primitives"][0]
        self.assertEqual(prim["extras"]["rusemod_draw"], 0)
        self.assertNotIn("skins", self.doc)  # the test wall has no bones
        # each material says which texture it shows (the Studio's preview puts the mod's paint on it by that)
        self.assertEqual(self.doc["materials"][0]["extras"]["rusemod_texture"], "gen\\test\\wall01.tgv")
        self.assertEqual([n["name"] for n in self.doc["nodes"]], ["wall"])
        self.assertEqual(self.summary["propellers"], 0)


class Propeller(unittest.TestCase):
    def test_propeller_discs_get_a_mesh_of_their_own(self):
        lib = FakeLibrary()
        disc = {"name": "$helice_1$", "type": "helice_1", "textures": {}, "tags": ["Camp", "helice_1", "Standard"]}
        lib.spk.materials = lambda: [disc] * 8  # every draw call of the test wall is a propeller disc here
        raw, _pictures, summary = gltf.model_glb(lib, NAME)
        doc = read_glb(raw)[5]
        self.assertEqual([m["name"] for m in doc["meshes"]], ["wall_propeller"])
        self.assertEqual([n["name"] for n in doc["nodes"]], ["wall_propeller"])
        self.assertEqual(doc["scenes"][0]["nodes"], [0])
        self.assertEqual(summary["propellers"], 1)


if __name__ == "__main__":
    unittest.main()
