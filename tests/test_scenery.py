"""A map's scenery (rusemod.scenery) on small made-up files: the file, its blocks and items, the walk, what the
Studio shows, and the scenery types from made-up descriptor NDFs (no game files needed)."""
import hashlib
import math
import struct
import unittest

from fixtures import make_edat, make_ndf, val
from rusemod import scenery
from rusemod.edat import Edat
from rusemod.scenery import SCALE16, Scenery, SceneryError, descriptors, group_of, layout, placement, view


def compact(sym, x, y, turn=0.0, size=1.0):
    c, s = math.cos(turn) * size, math.sin(turn) * size
    q = [round(v / SCALE16) for v in (c, -s, s, c)]
    return struct.pack("<I4h4f", 0x80000000 | sym << 4, *q, x, y, 0.0, size)


def moved(word, x, y):
    return struct.pack("<I3f", word | 2, x, y, 0.0)


def road():
    return struct.pack("<I", 0x01000000) + bytes(60)


def block(items, far=False):
    """A block with a one-leaf tree; far: its entries list the first item again in front (the far-view rule)."""
    entries, off = [], 0
    for it in items:
        entries.append(off)
        off += len(it)
    if far:
        entries = [0] + entries
    head = struct.pack("<II4f", 0x80000000 | len(entries), 1, 0.0, 0.0, 1.0, 1.0) + bytes(8)
    tree = struct.pack(f"<{len(entries)}I", *entries) + struct.pack("<II", 0xC0000000 | 0x1F << 20, 0x00FF0000)
    return head + tree + b"".join(items)


def make_scenery(blocks, names):
    offsets, pos = [], 0
    for b in blocks:
        offsets.append(pos)
        pos += len(b)
    data = b"".join(blocks)
    name_blob = b"".join(struct.pack("<I", len(n)) + n.encode() for n in names + [""])
    flags = bytes([1] * len(names))
    tab_off = 124
    data_off = tab_off + 4 * (len(blocks) + 1)
    names_off = data_off + len(data)
    flags_off = names_off + len(name_blob)
    opt_off = flags_off + len(flags)
    names2_off = opt_off
    layers_off = names2_off + 4
    grid_off = layers_off
    fields = [tab_off, len(blocks) + 1, data_off, len(data), flags_off, len(flags), names_off, len(name_blob),
              opt_off, 0, names2_off, 4, layers_off, 0, 1, 1, 1, 1, 1, 1, grid_off, 4, grid_off + 4, 4,
              grid_off + 8, 4]
    body = (b"0.6\0" + struct.pack("<26I", *fields) + struct.pack(f"<{len(blocks) + 1}I", *offsets, len(data)) + data
            + name_blob + flags + struct.pack("<I", 0) + bytes(12))
    return hashlib.md5(body).digest() + body


NAMES = ["TypeWarrior/MairieNormande", "TypeWarrior/Chene_02"]


def village():
    """Block 1: two oaks and a road piece; block 0 places a town hall and block 1 twice."""
    wood = block([struct.pack("<I", 0x80000000 | 1 << 4 | 1), moved(0x80000000 | 1 << 4, 100.0, 0.0), road()])
    root_len = len(block([compact(0, 1000.0, 2000.0), moved(0, 0, 0), moved(0, 0, 0)]))
    root = block([compact(0, 1000.0, 2000.0, math.pi / 2), moved(root_len, 5000.0, 0.0),
                  moved(root_len, 5000.0, 9000.0)])
    return make_scenery([root, wood], NAMES)


class Reading(unittest.TestCase):
    def test_blocks_items_and_names(self):
        s = Scenery(village())
        self.assertEqual(s.names[:2], NAMES)
        self.assertEqual([b.index for b in s.blocks], [0, 1])
        self.assertEqual([it.kind for it in s.blocks[1].items], ["object", "object", "road"])
        self.assertEqual(s.roots(), [0])
        self.assertEqual(s.counts(), [5, 2])
        self.assertEqual(s.types(), {0: 1, 1: 4})

    def test_walk_places_children_with_their_transforms(self):
        s = Scenery(village())
        got = sorted((sym, round(m[3]), round(m[7])) for sym, m in s.walk())
        self.assertEqual(got, [(0, 1000, 2000), (1, 5000, 0), (1, 5000, 9000), (1, 5100, 0), (1, 5100, 9000)])
        hall = next(m for sym, m in s.walk() if sym == 0)
        x, y, turn, size = placement(hall)
        self.assertAlmostEqual(turn, math.pi / 2, places=3)
        self.assertAlmostEqual(size, 1.0, places=3)

    def test_far_view_items_are_listed_twice_but_counted_once(self):
        s = Scenery(make_scenery([block([compact(1, 1, 2), compact(1, 3, 4)], far=True)], NAMES))
        self.assertEqual(len(s.blocks[0].items), 2)
        self.assertEqual(s.types(), {1: 2})

    def test_a_wrong_sum_or_version_is_refused(self):
        raw = bytearray(village())
        raw[200] ^= 1
        with self.assertRaises(SceneryError):
            Scenery(bytes(raw))
        body = b"0.7\0" + village()[20:]
        with self.assertRaises(SceneryError):
            Scenery(hashlib.md5(body).digest() + body)


class Groups(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(group_of("COC/Normandie/Batiments_Villes_Villages", "TSceneryDescriptorMultiState"), "building")
        self.assertEqual(group_of("Props/Ferme", "TSceneryDescriptorMultiState"), "prop")
        self.assertEqual(group_of("Vegetation/Arbres", "TSceneryDescriptorMultiState"), "vegetation")
        self.assertEqual(group_of("STICKERS/France", "TSceneryDescriptorSticker"), "decal")
        self.assertEqual(group_of("LD/Terrain modifiers", "TSceneryDescriptorMultiState"), "other")
        self.assertEqual(group_of("BaseBuilding/FX", "TSceneryDescriptorMultiState"), "other")

    def test_layout_keeps_every_building_and_samples_the_rest(self):
        s = Scenery(village())
        out = layout(s, {0: "building", 1: "vegetation"}, {"building": None, "vegetation": 2})
        self.assertEqual(len(out["building"]), 1)
        self.assertEqual(len(out["vegetation"]), 2)  # one of the two woods, whole
        out = layout(s, {0: "building", 1: "vegetation"}, {"building": None, "vegetation": None})
        self.assertEqual(len(out["vegetation"]), 4)


def ref(index):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, 0))


def text(index, tc=0x07):
    return val(tc, struct.pack("<I", index))


def unit_pack():
    """A descriptor NDF: a multi-state town hall whose normal look is a multi-mode with a close model; an oak."""
    classes = ["TSceneryDescriptorMultiState", "TSceneryDescriptorMultiMode", "TSceneryDescriptorMultiModeEntry",
               "TSceneryDescriptorModel3DFromFile"]
    props = [("RegistrationName", 0), ("Classement", 0), ("SDFalse", 0), ("ModeEntry", 1), ("ModeMask", 2),
             ("SceneryDescriptor", 2), ("ModelASE", 3)]
    strings = NAMES + ["COC/Normandie/Batiments_Villes_Villages", "Vegetation/Arbres",
                       "DataDir:\\WW2\\Res3D\\Decors\\France\\MairieNormandelod0.ASE2NdfBin"]
    objects = [
        (0, [(0, text(0)), (1, text(2)), (2, ref(1))]),
        (1, [(3, val(0x11, struct.pack("<I", 1) + ref(2)))]),
        (2, [(4, val(0x03, struct.pack("<I", 2))), (5, ref(3))]),
        (3, [(6, text(4, 0x1C))]),
        (0, [(0, text(1)), (1, text(3))]),
    ]
    ndf = make_ndf(objects, classes, props, strings=strings)
    return Edat(make_edat([("dir", "genglad\\patchable\\scenery\\", [("file", "france.cpp.gladndfbin", ndf)])]))


class Descriptors(unittest.TestCase):
    def test_names_categories_and_models(self):
        d = descriptors(unit_pack())
        hall = d["TypeWarrior/MairieNormande"]
        self.assertEqual((hall.group, hall.category), ("building", "COC/Normandie/Batiments_Villes_Villages"))
        self.assertEqual(hall.model, "ww2\\res3d\\decors\\france\\mairienormandelod0.ase2ndfbin")
        self.assertEqual((d["TypeWarrior/Chene_02"].group, d["TypeWarrior/Chene_02"].model), ("vegetation", None))

    def test_the_studio_view(self):
        maps = Edat(make_edat([("dir", "output\\", [("file", "save.boobspc", village())])]))
        v = view(maps, unit_pack(), budget={"building": None, "vegetation": None})
        self.assertEqual(v["groups"], {"building": {"shown": 1, "total": 1}, "vegetation": {"shown": 4, "total": 4}})
        hall = v["items"]["building"]
        self.assertEqual(v["types"][hall[0]][:2], ["MairieNormande", "building"])
        self.assertEqual(hall[1:3], [1000, 2000])
        self.assertEqual(scenery.MEMBER, "output\\save.boobspc")


if __name__ == "__main__":
    unittest.main()
