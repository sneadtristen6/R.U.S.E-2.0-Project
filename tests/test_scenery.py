"""A map's scenery (rusemod.scenery) on small made-up files: the file, its blocks and items, the walk, what the
Studio shows, and the scenery types from made-up descriptor NDFs (no game files needed)."""
import dataclasses
import hashlib
import math
import random
import struct
import tempfile
import tomllib
import unittest
from collections import Counter
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import brush, scenery
from rusemod.build import build_and_write, load_mod
from rusemod.edat import Edat
from rusemod.scenery import (BURY, SCALE16, SHRINK, T_COMPACT, T_FULL, NewObject, Scenery, SceneryEditError,
                             SceneryError, add_objects, bury_objects, descriptors, group_of, layout, objects_toml,
                             parse_objects, placement, view)


def compact(sym, x, y, turn=0.0, size=1.0, z=0.0):
    c, s = math.cos(turn) * size, math.sin(turn) * size
    q = [round(v / SCALE16) for v in (c, -s, s, c)]
    return struct.pack("<I4h4f", 0x80000000 | sym << 4, *q, x, y, z, size)


def moved(word, x, y):
    return struct.pack("<I3f", word | 2, x, y, 0.0)


def road(start=(0.0, 0.0), handle=(0.0, 0.0), end=(0.0, 0.0), back=(0.0, 0.0)):
    """A road piece: its start, the start's handle (an offset), its end, the end's handle (an offset from the end),
    each x, y, z; then 3 and two codes, as on every piece of the game's maps."""
    f = [*start, 0.0, *handle, 0.0, *end, 0.0, *back, 0.0]
    return struct.pack("<I12f3I", 0x01000141, *f, 3, 129958752, 1567752)


def block(items, far=False, mask=0x1F, box=(0.0, 0.0, 1.0, 1.0)):
    """A block with a one-leaf tree; far: its entries list the first item again in front (the far-view rule); mask:
    its root's (0x3F: with the road mark); box: its own."""
    entries, off = [], 0
    for it in items:
        entries.append(off)
        off += len(it)
    if far:
        entries = [0] + entries
    head = struct.pack("<II4f", 0x80000000 | len(entries), 1, *box) + bytes(8)
    tree = struct.pack(f"<{len(entries)}I", *entries) + struct.pack("<II", 0xC0000000 | mask << 20, 0x00FF0000)
    return head + tree + b"".join(items)


def road_pass(s):
    """(block, item offset) of every road piece the game's road pass would reach, walked as the game walks a
    scenery file: a block is entered only when its root has the road mark (bit 25), a block seen from far
    starts at its root's right side, and inside it a node is entered only with the mark. A model of the walk, not of
    the screen: a piece it reaches isn't proven drawn (TESTS.md T12)."""
    reached, todo = set(), [0]
    while todo:
        b = s.blocks[todo.pop()]
        nodes = [struct.unpack_from("<IHBB", b.nodes, 8 * k) for k in range(len(b.nodes) // 8)]
        w0, split = nodes[0][:2]
        if not w0 & scenery.ROAD_BIT:
            continue
        k, lo = ((w0 & 0xFFFFF) >> 2, split) if w0 & 0x00800000 else (0, 0)
        hi, out = len(b.entries), []
        if k and nodes[k][0] >= 0xC0000000:
            out = list(range(lo, hi))
        else:
            stack = [(k, lo, hi)]
            while stack:
                k2, a, z = stack.pop()
                w, sp = nodes[k2][:2]
                if not w & scenery.ROAD_BIT:
                    continue
                if w & 0x40000000:
                    out += range(a, sp)
                else:
                    stack.append((k2 + 1, a, sp))
                if w & 0x80000000:
                    out += range(sp, z)
                else:
                    stack.append((k2 + ((w & 0xFFFFF) >> 2), sp, z))
        by_at = {it.at: it for it in b.items}
        for e in out:
            it = by_at[b.entries[e]]
            if it.kind == "road":
                reached.add((b.index, it.at))
            elif it.kind == "child":
                todo.append(s._by_offset[it.child_offset])
    return reached


def two_woods():
    """The top block places a town hall and a wood (with a road piece of the map's own) twice, south and north, and
    lists both references for far view. Its tree: the root splits the far list off; the full list's node splits
    along y, the hall and the south wood's reference in its lower part (y up to 4,392), the north one's in its upper
    part (from 5,647). No node on the top block's paths has the road mark yet."""
    wood = block([compact(1, 0.0, 0.0), road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))], mask=0x3F)
    items = [compact(0, 1000.0, 2000.0), moved(0, 0, 0), moved(0, 0, 0)]
    offsets = [0, len(items[0]), len(items[0]) + len(items[1])]
    nodes = (struct.pack("<IHBB", 0x1F << 20 | 2 << 2, 2, 0xFF, 0)            # the root: far list | full list
             + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, 2, 0xFF, 0)     # the far list's leaf
             + struct.pack("<IHBB", 0xC0000000 | 0x17 << 20 | 1, 4, 0x70, 0x90))  # the full list, split along y
    entries = [offsets[1], offsets[2]] + offsets
    head = struct.pack("<II4f", 0x80000000 | len(entries), 3, 0.0, 0.0, 10000.0, 10000.0) + bytes(8)
    root_len = len(head) + 4 * len(entries) + len(nodes) + sum(map(len, items))
    items = [compact(0, 1000.0, 2000.0), moved(root_len, 2000.0, 1000.0), moved(root_len, 2000.0, 8000.0)]
    root = head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items)
    return make_scenery([root, wood], NAMES)


def italy_top():
    """A top block like M03_Italie's (and Alpha's, Dolly's, Korsun's, M02_Tunisie's, M08_Allemagne's, Mireille's,
    Robert's): the root splits the far list off, both lists are leaves over the whole map, and the full list's node
    splits at 0, so its left side runs backwards (from 2 to 0). It places the wood twice, both references listed for
    far view, so the wood isn't a block placed once and a road piece out in the open goes among the top block's items."""
    wood = block([compact(1, 0.0, 0.0), road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))], mask=0x3F)
    box = (0.0, 0.0, 40960.0, 40960.0)
    nodes = (struct.pack("<IHBB", 0x3F << 20 | 2 << 2, 2, 0xFF, 0)            # the root: far list | full list
             + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, 2, 0xFF, 0)     # the far list's leaf
             + struct.pack("<IHBB", 0xC0000000 | 0x37 << 20, 0, 0xFF, 0))    # the full list's, split at 0
    first = len(moved(0, 0, 0))
    entries = [0, first, 0, first]
    head = struct.pack("<II4f", 0x80000000 | len(entries), 3, *box) + bytes(8)
    root_len = len(head) + 4 * len(entries) + len(nodes) + 2 * first
    items = [moved(root_len, 5000.0, 5000.0), moved(root_len, 30000.0, 30000.0)]
    root = head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items)
    return make_scenery([root, wood], NAMES)


def open_fields():
    """A top block over 40,960 x 40,960 placing a town hall and a wood twice, both references listed for far view. Its
    full list's node splits along x: the hall and the west wood's reference in its left side (x up to 5,140), the
    east wood's in its right side (from 35,980); the middle of the map is open ground, in no box (a painted field
    away from D-Day's villages)."""
    wood = block([compact(1, 0.0, 0.0)], box=(-100.0, -100.0, 100.0, 100.0))
    items = [compact(0, 1000.0, 2000.0), moved(0, 0, 0), moved(0, 0, 0)]
    offsets = [0, len(items[0]), len(items[0]) + len(items[1])]
    nodes = (struct.pack("<IHBB", 0x1F << 20 | 2 << 2, 2, 0xFF, 0)            # the root: far list | full list
             + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, 2, 0xFF, 0)     # the far list's leaf
             + struct.pack("<IHBB", 0xC0000000 | 0x17 << 20, 4, 0x20, 0xE0))  # the full list, split along x
    entries = [offsets[1], offsets[2]] + offsets
    head = struct.pack("<II4f", 0x80000000 | len(entries), 3, 0.0, 0.0, 40960.0, 40960.0) + bytes(8)
    root_len = len(head) + 4 * len(entries) + len(nodes) + sum(map(len, items))
    items = [compact(0, 1000.0, 2000.0), moved(root_len, 2000.0, 1000.0), moved(root_len, 38000.0, 8000.0)]
    root = head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items)
    return make_scenery([root, wood], NAMES)


def make_scenery(blocks, names, wide: int = 1):
    """`wide`: the grids span `wide` x 40,960 across (x) and 40,960 down."""
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
    # the three grids (far, middle, close: cells 81,920, 20,480 and 5,120 across, records of 4, 5 and 3 bytes) over
    # 40,960 x 40,960 (times `wide` across), every cell empty
    far, mid, close = 4 * wide, 5 * 2 * wide * 2, 3 * 8 * wide * 8
    fields = [tab_off, len(blocks) + 1, data_off, len(data), flags_off, len(flags), names_off, len(name_blob),
              opt_off, 0, names2_off, 4, layers_off, 0, wide, 1, 2 * wide, 2, 8 * wide, 8, grid_off, far,
              grid_off + far, mid, grid_off + far + mid, close]
    body = (b"0.6\0" + struct.pack("<26I", *fields) + struct.pack(f"<{len(blocks) + 1}I", *offsets, len(data)) + data
            + name_blob + flags + struct.pack("<I", 0) + bytes(far + mid + close))
    return hashlib.md5(body).digest() + body


NAMES = ["TypeWarrior/MairieNormande", "TypeWarrior/Chene_02"]


def village():
    """Block 1: two oaks and a road piece; block 0 places a town hall and block 1 twice."""
    wood = block([struct.pack("<I", 0x80000000 | 1 << 4 | 1), moved(0x80000000 | 1 << 4, 100.0, 0.0),
                  road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))])
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

    def test_roads_are_placed_with_their_blocks(self):
        got = sorted(tuple(round(v) for v in piece) for piece in Scenery(village()).roads())
        self.assertEqual(got, [(5010, 20, 5015, 20, 5035, 20, 5040, 20), (5010, 9020, 5015, 9020, 5035, 9020, 5040, 9020)])

    def test_far_view_items_are_listed_twice_but_counted_once(self):
        s = Scenery(make_scenery([block([compact(1, 1, 2), compact(1, 3, 4)], far=True)], NAMES))
        self.assertEqual(len(s.blocks[0].items), 2)
        self.assertEqual(s.types(), {1: 2})

    def test_a_reference_holds_its_block_s_place_in_24_bits(self):
        word = 0x9C000002   # flags and a transform kind round the place
        self.assertEqual(scenery.link_offset(scenery.link_word(word, 0x123450)), 0x123450)
        self.assertEqual(scenery.link_word(word, 0x123450) & ~0x00FFFFFC, word & ~0x00FFFFFC)
        with self.assertRaises(SceneryEditError):   # past what 24 bits hold
            scenery.link_word(word, 0x1000000)

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
    return Edat(unit_pack_raw())


def unit_pack_raw():
    """A descriptor NDF: a multi-state town hall whose normal look is a multi-mode with a close model; an oak drawn
    as a composite of two models, its leaves and its trunk, as the game's trees are."""
    classes = ["TSceneryDescriptorMultiState", "TSceneryDescriptorMultiMode", "TSceneryDescriptorMultiModeEntry",
               "TSceneryDescriptorModel3DFromFile", "TSceneryDescriptorComposite"]
    props = [("RegistrationName", 0), ("Classement", 0), ("SDFalse", 0), ("ModeEntry", 1), ("ModeMask", 2),
             ("SceneryDescriptor", 2), ("ModelASE", 3), ("DescriptorComposition", 4)]
    strings = NAMES + ["COC/Normandie/Batiments_Villes_Villages", "Vegetation/Arbres",
                       "DataDir:\\WW2\\Res3D\\Decors\\France\\MairieNormandelod0.ASE2NdfBin",
                       "DataDir:\\WW2\\Res3D\\Decors\\Vegetation_EU\\Chene_02_Feuilleslod0.ASE2NdfBin",
                       "DataDir:\\WW2\\Res3D\\Decors\\Vegetation_EU\\Chene_02_Tronclod0.ASE2NdfBin"]
    objects = [
        (0, [(0, text(0)), (1, text(2)), (2, ref(1))]),
        (1, [(3, val(0x11, struct.pack("<I", 1) + ref(2)))]),
        (2, [(4, val(0x03, struct.pack("<I", 2))), (5, ref(3))]),
        (3, [(6, text(4, 0x1C))]),
        (0, [(0, text(1)), (1, text(3)), (2, ref(5))]),
        (4, [(7, val(0x11, struct.pack("<I", 2) + ref(6) + ref(7)))]),
        (3, [(6, text(5, 0x1C))]),
        (3, [(6, text(6, 0x1C))]),
    ]
    ndf = make_ndf(objects, classes, props, strings=strings)
    return make_edat([("dir", "genglad\\patchable\\scenery\\", [("file", "france.cpp.gladndfbin", ndf)])])


class Descriptors(unittest.TestCase):
    def test_names_categories_and_models(self):
        d = descriptors(unit_pack())
        hall = d["TypeWarrior/MairieNormande"]
        self.assertEqual((hall.group, hall.category), ("building", "COC/Normandie/Batiments_Villes_Villages"))
        self.assertEqual(hall.model, "ww2\\res3d\\decors\\france\\mairienormandelod0.ase2ndfbin")
        oak = d["TypeWarrior/Chene_02"]
        self.assertEqual((oak.group, oak.models), ("vegetation", ("ww2\\res3d\\decors\\vegetation_eu\\chene_02_feuilleslod0.ase2ndfbin",
                                                                  "ww2\\res3d\\decors\\vegetation_eu\\chene_02_tronclod0.ase2ndfbin")))
        self.assertEqual(oak.model, oak.models[0])
        self.assertEqual(hall.models, (hall.model,))

    def test_the_studio_view(self):
        maps = Edat(make_edat([("dir", "output\\", [("file", "save.boobspc", village())])]))
        v = view(maps, unit_pack(), budget={"building": None, "vegetation": None})
        self.assertEqual(v["groups"], {"building": {"shown": 1, "total": 1}, "vegetation": {"shown": 4, "total": 4}})
        hall = v["items"]["building"]
        self.assertEqual(v["types"][hall[0]][:2], ["MairieNormande", "building"])
        self.assertIs(v["types"][hall[0]][5], False)  # not a bridge: the Erase brush tints it with the buildings
        self.assertEqual(hall[1:3], [1000, 2000])
        self.assertEqual(scenery.MEMBER, "output\\save.boobspc")
        # every type there is to place has its number in types (its model is made for the place list's picture),
        # the ones no shown item uses too
        self.assertEqual([(r[0], v["types"][r[7]][0]) for r in v["palette"]],
                         [("TypeWarrior/MairieNormande", "MairieNormande"), ("TypeWarrior/Chene_02", "Chene_02")])
        bare = view(maps, unit_pack(), budget={"building": 0, "vegetation": 0})
        self.assertEqual(bare["items"], {"building": [], "vegetation": []})
        self.assertEqual(sorted(t[0] for t in bare["types"]), ["Chene_02", "MairieNormande"])
        self.assertEqual([bare["types"][r[7]][0] for r in bare["palette"]], ["MairieNormande", "Chene_02"])


def spots(data):
    """Every object as (name index, x, y), for comparing whole maps."""
    return Counter((sym, round(m[3], 2), round(m[7], 2)) for sym, m in Scenery(data).walk())


class Adding(unittest.TestCase):
    def test_new_objects_land_where_asked_and_nothing_else_moves(self):
        data = village()
        new, notes = add_objects(data, [NewObject("TypeWarrior/MairieNormande", 7000.0, 8000.0, 90.0, 1.5),
                                        NewObject("TypeWarrior/Chene_02", 500.0, 300.0, 0.0, 4.0)])
        self.assertEqual(spots(new) - spots(data), Counter({(0, 7000.0, 8000.0): 1, (1, 500.0, 300.0): 1}))
        self.assertEqual(spots(data) - spots(new), Counter())
        s = Scenery(new)
        last = s.blocks[-1]
        self.assertEqual(len(s.blocks), 3)
        self.assertEqual([it.tform for it in last.items][1:], [T_COMPACT, T_FULL])  # size 4 needs the full form
        hall = next(m for sym, m in s.walk() if sym == 0 and round(m[3]) == 7000)
        _x, _y, turn, size = placement(hall)
        self.assertAlmostEqual(math.degrees(turn), 90.0, places=2)
        self.assertAlmostEqual(size, 1.5, places=3)
        refs = [(b.index, s._by_offset[it.child_offset]) for b in s.blocks for it in b.items if it.kind == "child"]
        self.assertTrue(all(child > parent for parent, child in refs))  # every reference still points forward
        self.assertIn(last.index, [c for _p, c in refs])
        self.assertEqual(add_objects(data, [])[0], data)
        self.assertIn("2 object(s) added", notes[0])

    def test_new_objects_wrap_a_block_the_top_block_draws_from_far(self):
        """The top block lists its second reference to the wood for far view: new objects near it go in a new block
        right after the top block, which that reference now points to, holding the wood (placed where it was) and
        them. Every later reference moves by the new block's size; nothing else moves."""
        wood = block([struct.pack("<I", 0x80000000 | 1 << 4 | 1), moved(0x80000000 | 1 << 4, 100.0, 0.0), road()])
        items = [compact(0, 1000.0, 2000.0), moved(0, 0, 0), moved(0, 0, 0)]
        root_len = len(block(items)) + 4  # one far entry more
        items = [compact(0, 1000.0, 2000.0), moved(root_len, 5000.0, 0.0), moved(root_len, 5000.0, 9000.0)]
        offsets = [0, len(items[0]), len(items[0]) + len(items[1])]
        head = struct.pack("<II4f", 0x80000000 | 4, 1, 0.0, 0.0, 1.0, 1.0) + bytes(8)
        tree = struct.pack("<4I", offsets[2], *offsets) + struct.pack("<II", 0xC0000000 | 0x1F << 20, 0x00FF0000 | 1)
        root = head + tree + b"".join(items)
        self.assertEqual(len(root), root_len)
        data = make_scenery([root, wood], NAMES)
        new, notes = add_objects(data, [NewObject("TypeWarrior/MairieNormande", 5300.0, 9200.0, 45.0, 2.0)])
        self.assertEqual(spots(new) - spots(data), Counter({(0, 5300.0, 9200.0): 1}))
        self.assertEqual(spots(data) - spots(new), Counter())
        s = Scenery(new)
        self.assertEqual(len(s.blocks), 3)
        refs = [(b.index, s._by_offset[it.child_offset]) for b in s.blocks for it in b.items if it.kind == "child"]
        self.assertEqual(refs, [(0, 1), (0, 2), (1, 2)])  # the far one (listed first) goes through the new block
        self.assertIn("with block 1", " ".join(notes))  # (after the tree's widening: its box is 1 across)
        hall = next(m for sym, m in s.walk() if sym == 0 and round(m[3]) == 5300)
        _x, _y, turn, size = placement(hall)
        self.assertAlmostEqual(math.degrees(turn), 45.0, places=3)
        self.assertAlmostEqual(size, 2.0, places=3)

    def test_new_objects_keep_the_levels_asked(self):
        """An object with levels (a [[copy]]'s: its shipped copy's LOD mask) is drawn at exactly those levels: off
        the far-view list when the mask has no far bit, under full-list nodes of its own mask; one without keeps
        every level. A copy's transform takes the source square onto the target, turned about its middle."""
        wood = block([struct.pack("<I", 0x80000000 | 1 << 4 | 1), moved(0x80000000 | 1 << 4, 100.0, 0.0), road()])
        items = [compact(0, 1000.0, 2000.0), moved(0, 0, 0), moved(0, 0, 0)]
        root_len = len(block(items)) + 4
        items = [compact(0, 1000.0, 2000.0), moved(root_len, 5000.0, 0.0), moved(root_len, 5000.0, 9000.0)]
        offsets = [0, len(items[0]), len(items[0]) + len(items[1])]
        head = struct.pack("<II4f", 0x80000000 | 4, 1, 0.0, 0.0, 1.0, 1.0) + bytes(8)
        tree = struct.pack("<4I", offsets[2], *offsets) + struct.pack("<II", 0xC0000000 | 0x1F << 20, 0x00FF0000 | 1)
        data = make_scenery([head + tree + b"".join(items), wood], NAMES)
        new, _ = add_objects(data, [NewObject("TypeWarrior/Chene_02", 5200.0, 9100.0, levels=0x05),
                                    NewObject("TypeWarrior/Chene_02", 5250.0, 9150.0, levels=0x10),
                                    NewObject("TypeWarrior/MairieNormande", 5300.0, 9200.0)])
        s = Scenery(new)
        got = {round(m[3]): mask for sym, m, mask in scenery.walk_levels(s, (5100.0, 9000.0, 5400.0, 9300.0), {0, 1})}
        self.assertEqual(got[5200], 0x05)
        self.assertEqual(got[5250], 0x10)
        self.assertEqual(got[5300] & 0x08, 0x08)   # drawn from far as before
        area = scenery.CopyArea(1000.0, 2000.0, 50.0, sx=300.0, sy=-400.0, turn=90.0)
        m = area.to_target()
        self.assertAlmostEqual(m[3] + m[0] * 1300.0 + m[1] * 1600.0, 1000.0, places=6)   # the source's middle lands
        self.assertAlmostEqual(m[7] + m[4] * 1300.0 + m[5] * 1600.0, 2000.0, places=6)   # on the target's
        self.assertAlmostEqual(m[4], 1.0, places=6)                                        # turned a quarter

    def test_new_objects_hang_on_a_block_listed_at_their_levels(self):
        """Two far-listed references whose full-list leaf boxes both hold the spot: A listed without the close level
        (0x16), B with every level (0x17). A copied plant (levels 0x15) goes on B, though A is nearer, so it keeps its
        close level; with only A's kind it hangs there, drawn at fewer levels, and add_objects says so (2026-10-11:
        a meadow's plants lost their close level that way)."""
        def top(mask_b):
            wood = block([compact(1, 0.0, 0.0)], box=(-100.0, -100.0, 100.0, 100.0))
            first = len(moved(0, 0, 0))
            entries = [0, first, 0, first]
            nodes = (struct.pack("<IHBB", 0x1F << 20 | 2 << 2, 2, 0xFF, 0)          # the root: far list | full list
                     + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, 2, 0xFF, 0)   # the far list's leaf
                     + struct.pack("<IHBB", 0x17 << 20 | 2 << 2, 3, 0xFF, 0)       # the full list: A left, B right,
                     + struct.pack("<IHBB", 0xC0000000 | 0x16 << 20, 2, 0xFF, 0)   # both sides the whole box; A's leaf
                     + struct.pack("<IHBB", 0xC0000000 | mask_b << 20, 3, 0xFF, 0))  # B's leaf
            head = struct.pack("<II4f", 0x80000000 | len(entries), 5, 0.0, 0.0, 40960.0, 40960.0) + bytes(8)
            root_len = len(head) + 4 * len(entries) + len(nodes) + 2 * first
            items = [moved(root_len, 5000.0, 5000.0), moved(root_len, 30000.0, 30000.0)]
            return make_scenery([head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items), wood],
                                NAMES)

        def levels_at(data):
            return {round(m[3]): mask for _s, m, mask in
                    scenery.walk_levels(Scenery(data), (5900.0, 5900.0, 6100.0, 6100.0), {1})}
        plant = NewObject("TypeWarrior/Chene_02", 6000.0, 6000.0, levels=0x15)   # nearer A
        new, notes = add_objects(top(0x17), [plant])
        self.assertEqual(levels_at(new), {6000: 0x15})
        self.assertNotIn("fewer detail levels", " ".join(notes))
        new, notes = add_objects(top(0x16), [plant])
        self.assertEqual(levels_at(new), {6000: 0x14})
        self.assertIn("1 new object(s) hang on a block the map lists at fewer detail levels", " ".join(notes))

    def test_a_spot_under_middle_only_blocks_widens_one_listed_at_every_level(self):
        """A blank map's erased ground: the only reference whose full-list box holds the spot (A, the west half) is
        listed middle-only (0x10, as D-Day lists its big ground-sticker blocks); B (the east half) is listed at every
        level but far (0x17). A copied crop (levels 0x05) hung on A was drawn at 0x05 & 0x10 = nothing (the blank
        farm's 30,183 crops, stones and low plants, 2026-10-15); it now goes on B, whose box is widened over it, and
        keeps its levels."""
        wood = block([compact(1, 0.0, 0.0)], box=(-100.0, -100.0, 100.0, 100.0))
        first = len(moved(0, 0, 0))
        entries = [0, first, 0, first]
        nodes = (struct.pack("<IHBB", 0x1F << 20 | 2 << 2, 2, 0xFF, 0)            # the root: far list | full list
                 + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, 2, 0xFF, 0)     # the far list's leaf
                 + struct.pack("<IHBB", 0x17 << 20 | 2 << 2, 3, 0x80, 0x80)      # the full list split along x:
                 + struct.pack("<IHBB", 0xC0000000 | 0x10 << 20, 2, 0xFF, 0)     # A's leaf (west), middle only
                 + struct.pack("<IHBB", 0xC0000000 | 0x17 << 20, 3, 0xFF, 0))    # B's leaf (east)
        head = struct.pack("<II4f", 0x80000000 | len(entries), 5, 0.0, 0.0, 40960.0, 40960.0) + bytes(8)
        root_len = len(head) + 4 * len(entries) + len(nodes) + 2 * first
        items = [moved(root_len, 5000.0, 5000.0), moved(root_len, 30000.0, 30000.0)]
        data = make_scenery([head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items), wood],
                            NAMES)
        crop = NewObject("TypeWarrior/Chene_02", 6000.0, 6000.0, levels=0x05)
        _groups, _lost, short = scenery._carriers(Scenery(data), [crop])
        self.assertEqual(len(short), 1)   # only A holds it
        new, notes = add_objects(data, [crop])
        got = {round(m[3]): mask for _s, m, mask in
               scenery.walk_levels(Scenery(new), (5900.0, 5900.0, 6100.0, 6100.0), {1})}
        self.assertEqual(got, {6000: 0x05})
        self.assertNotIn("fewer detail levels", " ".join(notes))
        self.assertIn("draw tree widened", " ".join(notes))
        b = scenery._leaf_boxes(Scenery(new).blocks[0])[3]   # B's entry in the full list
        self.assertTrue(b[0] <= 5120.0 and b[2] >= 10240.0, b)   # over the crop's close cell

    def test_a_tree_asking_for_far_view_gets_a_carrier_listed_for_it_there(self):
        """A map two far cells wide (163,840): the far list's box covers only the west far cell; A (west) and B
        (east, placed at 100,000) are both far-listed, their full-list leaves splitting the map in two. A copied tree
        (levels 0x0D: drawn from far too) in the east far cell: B's full-list box holds it at its levels, but B's
        far-list box misses its far cell, so it would never be drawn from far (the blank farm's field 7: its trees
        gone from ~700 m, 2026-10-15). It goes on B, B's far-list box widened over it as well."""
        wood = block([compact(1, 0.0, 0.0)], box=(-100.0, -100.0, 100.0, 100.0))
        first = len(moved(0, 0, 0))
        entries = [0, first, 0, first]
        nodes = (struct.pack("<IHBB", 0x1F << 20 | 2 << 2, 2, 0x40, 0)            # far list (west quarter) | full
                 + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, 2, 0xFF, 0)     # the far list's leaf
                 + struct.pack("<IHBB", 0x17 << 20 | 2 << 2, 3, 0x80, 0x80)      # the full list split along x:
                 + struct.pack("<IHBB", 0xC0000000 | 0x17 << 20, 2, 0xFF, 0)     # A's leaf (west)
                 + struct.pack("<IHBB", 0xC0000000 | 0x17 << 20, 3, 0xFF, 0))    # B's leaf (east)
        head = struct.pack("<II4f", 0x80000000 | len(entries), 5, 0.0, 0.0, 163840.0, 40960.0) + bytes(8)
        root_len = len(head) + 4 * len(entries) + len(nodes) + 2 * first
        items = [moved(root_len, 5000.0, 5000.0), moved(root_len, 100000.0, 5000.0)]
        data = make_scenery([head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items), wood],
                            NAMES, wide=4)
        tree = NewObject("TypeWarrior/Chene_02", 120000.0, 6000.0, levels=0x0D)
        _groups, _lost, short = scenery._carriers(Scenery(data), [tree])
        self.assertEqual(len(short), 1)
        new, notes = add_objects(data, [tree])
        self.assertIn("its far view too", " ".join(notes))
        far_box = scenery._leaf_boxes(Scenery(new).blocks[0])[1]   # B's entry in the far list
        self.assertTrue(far_box[0] <= 117760.0 and far_box[2] >= 122880.0, far_box)   # over the tree's close cell
        self.assertEqual(scenery._carriers(Scenery(new), [NewObject("TypeWarrior/Chene_02", 120000.0, 6000.0,
                                                                    levels=0x0D)])[2], [])

    def test_objects_to_widen_for_go_on_carriers_of_their_own(self):
        """More objects in open ground than one widened carrier takes (WIDEN_MOST, here 1): each part on its own
        carrier, the nearest free one, so no new block wraps another (the blank farm's 30,183 plants went in four
        blocks nested one in the next on one carrier, and none was drawn, 2026-10-15)."""
        from unittest import mock
        data = open_fields()
        field = [NewObject("TypeWarrior/Chene_02", 20000.0, 20000.0), NewObject("TypeWarrior/Chene_02", 25000.0, 12000.0)]
        with mock.patch.object(scenery, "WIDEN_MOST", 1):
            new, notes = add_objects(data, field)
        self.assertEqual(sum("draw tree widened" in n for n in notes), 2, notes)
        s = Scenery(new)
        wrappers = [b for b in s.blocks[1:] if any(it.kind == "object" and it.symbol == 1 and
                                                   round(it.matrix()[3]) not in (0,) for it in b.items)
                    and any(it.kind == "child" for it in b.items)]
        self.assertEqual(len(wrappers), 2)
        for b in wrappers:   # each wraps one of the map's own blocks, not another new one
            kid = s.blocks[s._by_offset[next(it for it in b.items if it.kind == "child").child_offset]]
            self.assertEqual(tuple(kid.bbox), (-100.0, -100.0, 100.0, 100.0))

    def test_a_map_whose_top_block_places_only_blocks(self):
        root_len = len(block([moved(0, 0.0, 0.0)]))
        data = make_scenery([block([moved(root_len, 5000.0, 1000.0)]), block([compact(1, 10.0, 20.0)])], NAMES)
        new, _ = add_objects(data, [NewObject("TypeWarrior/MairieNormande", 100.0, 200.0, 30.0)])
        self.assertEqual(spots(new), Counter({(1, 5010.0, 1020.0): 1, (0, 100.0, 200.0): 1}))

    def test_refusals(self):
        with self.assertRaisesRegex(SceneryEditError, "isn't used on this map"):
            add_objects(village(), [NewObject("TypeWarrior/Nope", 0.0, 0.0)])
        with self.assertRaisesRegex(SceneryEditError, "size"):
            add_objects(village(), [NewObject("TypeWarrior/Chene_02", 0.0, 0.0, 0.0, 99.0)])
        with self.assertRaisesRegex(SceneryEditError, "unknown key 'colour'"):
            parse_objects([{"type": "TypeWarrior/Chene_02", "x": 1, "y": 2, "colour": 3}])
        with self.assertRaisesRegex(SceneryEditError, "has no x"):
            parse_objects([{"type": "TypeWarrior/Chene_02", "y": 2}])

    def test_the_mod_file(self):
        objs = [NewObject("TypeWarrior/Chene_02", 1.5, 2.0, 45.0, 2.0), NewObject("TypeWarrior/MairieNormande", 3.0, 4.0),
                NewObject("TypeWarrior/Pont", 5.0, 6.0, 90.0, 1.0, False, 1.5, -200.0)]  # a bridge: stretched, sunk
        text = objects_toml(objs, "Made in the Studio.")
        self.assertTrue(text.startswith("# Made in the Studio.\n"))
        self.assertEqual(parse_objects(tomllib.loads(text)["object"]), objs)
        self.assertEqual(text.count("stretch"), 1)  # only written when it's not the plain 1.0 / 0.0
        self.assertEqual(text.count("lift"), 1)
        for bad in ({"stretch": 0.1}, {"stretch": 9}, {"lift": 1e6}, {"lift": "deep"}):
            with self.assertRaises(SceneryEditError):
                parse_objects([{"type": "TypeWarrior/Pont", "x": 1, "y": 2, **bad}])

    def test_a_placed_objects_matrix(self):
        m = NewObject("x", 10.0, 20.0, 90.0, 2.0, True, 1.5, -7.0).matrix()
        self.assertEqual([round(v, 6) for v in m], [0.0, -3.0, 0.0, 10.0, 2.0, 0.0, 0.0, 20.0, 0.0, 0.0, 2.0, -7.0])
        x, y, turn, size = placement(m)
        self.assertEqual((x, y, round(math.degrees(turn)), size), (10.0, 20.0, 90, 2.0))


LOW_NAMES = ["TypeWarrior/HerbeHaute_01", "TypeWarrior/Caillou_01", "TypeWarrior/Herbe_verte"]
LOW_DESCS = {"TypeWarrior/HerbeHaute_01": scenery.Descriptor("TypeWarrior/HerbeHaute_01", "TSceneryDescriptor",
                                                              "Vegetation/Herbes", "vegetation", None, "x"),
             "TypeWarrior/Caillou_01": scenery.Descriptor("TypeWarrior/Caillou_01", "TSceneryDescriptor",
                                                          "Props/Ferme", "prop", None, "x"),
             "TypeWarrior/Herbe_verte": scenery.Descriptor("TypeWarrior/Herbe_verte", "TSceneryDescriptorSticker",
                                                           "Stickers", "decal", None, "x")}


class Presets(unittest.TestCase):
    """[[preset]]: a ground kind of the library tiled over an area (scenery.expand_preset), and the fill rule a copy
    follows in add mode (copy_objects: nothing laid on top of what the map already has there)."""

    def library(self) -> dict:
        folder = Path(tempfile.mkdtemp(prefix="presets-"))
        (folder / "p.toml").write_text(
            '[[preset]]\nname = "Wheat field"\ndescription = "Ripe wheat."\nmap = "M04_Cotentin"\naligned = true\n'
            'sources = [[100000.0, 200000.0], [300000.0, 400000.0], [500000.0, 600000.0]]\n', encoding="utf-8")
        return scenery.preset_library(folder / "p.toml")

    def test_the_rows_and_the_library(self):
        lib = self.library()
        self.assertEqual(lib["Wheat field"]["sources"], [(100000.0, 200000.0), (300000.0, 400000.0),
                                                         (500000.0, 600000.0)])
        self.assertEqual(lib["Wheat field"]["map"], "M04_Cotentin")
        self.assertTrue(lib["Wheat field"]["aligned"])
        rows = scenery.parse_presets([{"name": "Wheat field", "x": 1.0, "y": 2.0, "radius": 13000.0,
                                       "mode": "replace", "seed": 2}])
        self.assertEqual(rows, [scenery.PresetArea("Wheat field", 1.0, 2.0, 13000.0, "replace", "square", 1.0, 0.0, 2)])
        for bad, why in (({"x": 1, "y": 2, "radius": 10}, "no name"),
                         ({"name": "W", "x": 1, "y": 2, "radius": 10, "mode": "paint"}, "add or replace"),
                         ({"name": "W", "x": 1, "y": 2, "radius": 10, "size": 3}, "unknown key"),
                         ({"name": "W", "x": 1, "radius": 10}, "has no y"),
                         ({"name": "W", "x": 1, "y": 2, "radius": 10, "shape": "line"}, "round or square")):
            with self.assertRaisesRegex(SceneryEditError, why):
                scenery.parse_presets([bad])
        with self.assertRaisesRegex(SceneryEditError, "no ground preset is called 'Dunes'"):
            scenery.expand_preset(scenery.PresetArea("Dunes", 0.0, 0.0, 6500.0), lib)
        self.assertIn("Wheat field", scenery.preset_library())   # the library the build ships

    def test_an_area_is_tiled_from_the_kind_s_squares(self):
        lib = self.library()
        tile = scenery.TILE
        area = scenery.PresetArea("Wheat field", 10000.0, 20000.0, tile, "add", seed=1)   # 100 m: 2 x 2 tiles
        copies, erases, stamps, objects = scenery.expand_preset(area, lib)
        self.assertEqual(objects, [])   # a tile kind lays no hedgerow
        self.assertEqual(sorted((c.x, c.y) for c in copies),
                         sorted((10000.0 + i * tile / 2, 20000.0 + j * tile / 2) for i in (-1, 1) for j in (-1, 1)))
        self.assertEqual(erases, [])
        self.assertEqual([c.radius for c in copies], [tile / 2] * 4)
        self.assertTrue(all(c.fill and c.source == "M04_Cotentin" and c.layers == scenery.COPY_LAYERS for c in copies))
        self.assertEqual(copies[0].within, ("square", 10000.0, 20000.0, tile, 1.0, 0.0))
        # the sources go round from the seed: 1, 2, 0, 1
        self.assertEqual([(c.x + c.sx, c.y + c.sy) for c in copies],
                         [(300000.0, 400000.0), (500000.0, 600000.0), (100000.0, 200000.0), (300000.0, 400000.0)])
        # a stamp reaches past its tile by the hard edge's fade, so the tiles' joins hold no ground from underneath
        self.assertEqual([(s.brush, s.shape, s.edge, s.clear, s.radius) for s in stamps],
                         [("stamp", "square", "hard", False, tile / 2 / brush.HARD_EDGE)] * 4)
        self.assertEqual(brush.edge_weight("hard", "square", (tile / 2 / stamps[0].radius) ** 2), 1.0)
        self.assertEqual([(s.x + s.sx, s.y + s.sy) for s in stamps], [(c.x + c.sx, c.y + c.sy) for c in copies])
        one = scenery.PresetArea("Wheat field", 10000.0, 20000.0, tile / 2, "replace")   # one tile: on the middle
        copies, erases, stamps, _o = scenery.expand_preset(one, lib)
        self.assertEqual([(c.x, c.y, c.fill) for c in copies], [(10000.0, 20000.0, False)])
        self.assertEqual(len(stamps), 1)
        self.assertEqual(erases, [scenery.EraseArea(10000.0, 20000.0, tile / 2, ("decal",), (scenery.LOW_COVER,),
                                                    shape="square", dx=1.0, dy=0.0)])
        rnd = scenery.PresetArea("Wheat field", 0.0, 0.0, tile * 1.6, "add", "round")   # a circle: tiles inside it
        copies, _e, _s, _o = scenery.expand_preset(rnd, lib)
        self.assertEqual(len(copies), 12)   # middles 0.5 and 1.5 tiles out: 4 inner, 8 at 1.58 out, the 4 corners
        self.assertTrue(all(math.hypot(c.x, c.y) < tile * 1.6 for c in copies))   # (2.12 out) outside

    def test_what_stood_on_a_building_left_behind_is_left_out(self):
        """A building's footprint in the source (round 1000, 1000, 100 x 60 half sizes) the copy doesn't take: a tuft
        4 m up on its wall (a wall plant, as D-Day's veget_EU_035 by its houses) is left out, a tuft on the ground
        beside it and one raised far from any building are copied (the blank farm's field 3: flowers 3-5 m up,
        floating, 2026-10-16)."""
        up = 4.0 * 260.0
        items = [compact(0, 1050.0, 1000.0, z=up),                 # on the wall
                 compact(0, 1000.0, 1300.0),                        # on the ground, 1 m off its wall
                 compact(0, 2000.0, 1000.0, z=up)]                  # raised, 9 m from the house
        data = make_scenery([block(items, box=(0.0, 0.0, 10000.0, 10000.0))], LOW_NAMES)
        house = (1000.0, 1000.0, 100.0, 60.0, 1.0, 0.0, scenery.BUILDING_REACH)
        area = scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0, src_avoid=(house,))
        laid, notes = scenery.copy_objects(data, [area], LOW_DESCS)
        self.assertEqual(sorted((o.x, o.y) for o in laid), [(5000.0, 5300.0), (6000.0, 5000.0)])
        self.assertIn("1 that stood on a building left behind left out", notes[0])
        laid, _n = scenery.copy_objects(data, [scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0)],
                                        LOW_DESCS)
        self.assertEqual(len(laid), 3)   # without the source's buildings, as before

    def test_the_fill_rule_lays_nothing_on_what_the_map_has(self):
        """The source square (round 1000, 1000) holds two tall-grass tufts, a stone and a grass sticker; the target
        (round 5000, 5000) already has a tuft right where the first would land and the same sticker 1 m from where the
        copied one would: in add mode those two are left off, the rest laid; in replace mode everything is laid."""
        items = [compact(0, 1000.0, 1000.0), compact(0, 1400.0, 1000.0), compact(1, 1050.0, 1050.0),
                 compact(2, 1100.0, 1100.0),                                   # the source's
                 compact(0, 5000.0, 5000.0), compact(2, 5100.0, 5360.0)]       # what the target already has (the
        data = make_scenery([block(items, box=(0.0, 0.0, 10000.0, 10000.0))], LOW_NAMES)   # sticker 1 m off)
        area = scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0, fill=True)
        laid, notes = scenery.copy_objects(data, [area], LOW_DESCS)
        self.assertEqual(sorted((o.type.split("/")[-1], o.x, o.y) for o in laid),
                         [("Caillou_01", 5050.0, 5050.0), ("HerbeHaute_01", 5400.0, 5000.0)])
        self.assertIn("2 left off where the map already has one (fill rule)", notes[0])
        laid, notes = scenery.copy_objects(data, [scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0)],
                                           LOW_DESCS)
        self.assertEqual(len(laid), 4)
        self.assertNotIn("fill rule", notes[0])
        # clipped to a bigger footprint: only what lies within 100 units of the target's middle
        clipped = scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0,
                                   within=("round", 5000.0, 5000.0, 100.0, 1.0, 0.0))
        laid, _n = scenery.copy_objects(data, [clipped], LOW_DESCS)
        self.assertEqual(sorted((o.x, o.y) for o in laid), [(5000.0, 5000.0), (5050.0, 5050.0)])
        # another map as the source: its scenery handed in by pack name
        other = scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0, source="Elsewhere")
        with self.assertRaisesRegex(SceneryEditError, "Elsewhere"):
            scenery.copy_objects(data, [other], LOW_DESCS)
        laid, _n = scenery.copy_objects(data, [other], LOW_DESCS, {"Elsewhere": data})
        self.assertEqual(len(laid), 4)

    def test_the_fill_rule_holds_between_overlapping_copies(self):
        """A brush is many dabs that overlap: the second dab lays nothing within the gap of what the first laid, in
        any mode; but the tiles of one preset (one group) meet edge to edge and never thin each other."""
        items = [compact(0, 1000.0, 1000.0), compact(0, 1400.0, 1000.0), compact(1, 1050.0, 1050.0),
                 compact(2, 1100.0, 1100.0)]
        data = make_scenery([block(items, box=(0.0, 0.0, 10000.0, 10000.0))], LOW_NAMES)
        first = scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0)
        second = scenery.CopyArea(5000.0, 5000.0, 1300.0, sx=-4000.0, sy=-4000.0)   # the same dab again
        laid, notes = scenery.copy_objects(data, [first, second], LOW_DESCS)
        self.assertEqual(len(laid), 4)
        self.assertIn("4 left off where an earlier copy laid one (fill rule)", notes[1])
        # 1.15 m over: its far tuft lands 1.15 m past the first's (1 m gap: laid), its near tuft 0.4 m short of the
        # first's far one (left off), the stone 1.15 m off (1.5 m gap: left off), the sticker too (3 m)
        shifted = scenery.CopyArea(5300.0, 5000.0, 1300.0, sx=-4300.0, sy=-4000.0)
        laid, notes = scenery.copy_objects(data, [first, shifted], LOW_DESCS)
        self.assertEqual(sorted(o.type.split("/")[-1] for o in laid),
                         ["Caillou_01"] + ["HerbeHaute_01"] * 3 + ["Herbe_verte"])
        self.assertIn("3 left off where an earlier copy laid one", notes[1])
        tiles = [dataclasses.replace(first, group=7), dataclasses.replace(second, group=7)]
        laid, notes = scenery.copy_objects(data, tiles, LOW_DESCS)
        self.assertEqual(len(laid), 8)
        self.assertNotIn("fill rule", notes[1])


class Borders(unittest.TestCase):
    """A preset's border ([[preset]] border = "edge" or "hedge"): the game's own strips copied along the area's
    outline (scenery.expand_border), in a band 2 m across centred on it, with the map's stickers and low cover there
    taken off first and the area's own tiles stopping short of it, so the strips never sit in the crops."""

    def library(self, text: str | None = None) -> tuple[dict, dict]:
        """A library of one preset and the border "hedge": a strip 2000 long along x round 1000, 1000 and one 3000
        long along y round 9000, 1000 (given the wrong length on purpose: a direction is any length)."""
        folder = Path(tempfile.mkdtemp(prefix="borders-"))
        (folder / "b.toml").write_text(
            '[[preset]]\nname = "Wheat field"\nmap = "M04_Cotentin"\nsources = [[100000.0, 200000.0]]\n\n'
            + (text if text is not None else
               '[[border]]\nname = "hedge"\ndescription = "Hedge foot."\nmap = "M04_Cotentin"\n'
               'sources = [[1000.0, 1000.0, 1.0, 0.0, 2000.0], [9000.0, 1000.0, 0.0, 2.0, 3000.0]]\n'),
            encoding="utf-8")
        return scenery.preset_library(folder / "b.toml"), scenery.border_library(folder / "b.toml")

    @staticmethod
    def inside(c, x: float, y: float) -> bool:
        return c.footprint().t2(x, y) < 1.0 and c.clip().t2(x, y) < 1.0

    def test_the_rows_and_the_library(self):
        _lib, borders = self.library()
        self.assertEqual(borders, {"hedge": {"description": "Hedge foot.", "map": "M04_Cotentin", "sources": [
            (1000.0, 1000.0, 1.0, 0.0, 2000.0), (9000.0, 1000.0, 0.0, 2.0, 3000.0)]}})
        rows = scenery.parse_presets([{"name": "Wheat field", "x": 1.0, "y": 2.0, "radius": 13000.0, "border": "hedge"},
                                      {"name": "Wheat field", "x": 1.0, "y": 2.0, "radius": 13000.0}])
        self.assertEqual([r.border for r in rows], ["hedge", "none"])
        for bad in ("wall", 1, ""):
            with self.assertRaisesRegex(SceneryEditError, "border must be none, edge or hedge"):
                scenery.parse_presets([{"name": "W", "x": 1, "y": 2, "radius": 10, "border": bad}])
        for text, why in (('[[border]]\nname = "hedge"\nsources = [[1.0, 2.0, 1.0, 0.0, 5.0]]\n', "a name, a map"),
                          ('[[border]]\nname = "hedge"\nmap = "M"\nsources = [[1.0, 2.0, 3.0]]\n', "x, y, dx, dy"),
                          ('[[border]]\nname = "hedge"\nmap = "M"\nsources = [[1.0, 2.0, 0.0, 0.0, 5.0]]\n',
                           "direction"),
                          ('[[border]]\nname = "hedge"\nmap = "M"\nsources = [[1.0, 2.0, 1.0, 0.0, 0.0]]\n',
                           "length above 0")):
            with self.assertRaisesRegex(SceneryEditError, why):
                self.library(text)
        lib, borders = self.library()
        with self.assertRaisesRegex(SceneryEditError, "no border is called 'edge'"):
            scenery.expand_preset(scenery.PresetArea("Wheat field", 0.0, 0.0, 6500.0, border="edge"), lib,
                                  borders=borders)
        shipped = scenery.border_library()   # the library the build ships: every border a row may name
        self.assertEqual(sorted(shipped), sorted(b for b in scenery.BORDERS if b != "none"))
        for name, kind in shipped.items():
            self.assertEqual(kind["map"], "M04_Cotentin")
            self.assertEqual(len(kind["sources"]), 8, name)
            self.assertTrue(all(len(s) == 5 and s[4] > 0 for s in kind["sources"]))

    def test_a_square_s_sides_in_pieces_along_the_band(self):
        _lib, borders = self.library()
        area = scenery.PresetArea("Wheat field", 50000.0, 60000.0, 6500.0, "add", dx=3.0, dy=4.0, border="hedge")
        copies, erases = scenery.expand_border(area, borders, group=5)
        corners = area.footprint().corners()
        self.assertEqual([(e.x, e.y, e.x2, e.y2) for e in erases],
                         [(*corners[k], *corners[(k + 1) % 4]) for k in range(4)])
        self.assertTrue(all(e.shape == "line" and e.radius == scenery.BORDER_WIDTH / 2 and e.what == ("decal",)
                            and e.types == (scenery.LOW_COVER,) for e in erases))
        # each side 13000 long, in 7 pieces (the shortest strip is 2000), each from the next strip in turn
        self.assertEqual(len(copies), 28)
        self.assertTrue(all(c.layers == scenery.BORDER_LAYERS and not c.fill and c.group == 5
                            and c.source == "M04_Cotentin" and c.radius == 13000.0 / 7 / 2 for c in copies))
        strips = borders["hedge"]["sources"]
        for k, c in enumerate(copies):
            px, py, pdx, pdy, _n = strips[k % 2]
            m = c.to_target()
            mid = ((c.x + c.within[1]) / 2, (c.y + c.within[2]) / 2)   # the piece's middle, on the outline
            self.assertAlmostEqual(m[0] * px + m[1] * py + m[3], mid[0], places=6)
            self.assertAlmostEqual(m[4] * px + m[5] * py + m[7], mid[1], places=6)
            side = k // 7
            (x0, y0), (x1, y1) = corners[side], corners[(side + 1) % 4]
            along = math.atan2((m[4] * pdx + m[5] * pdy), (m[0] * pdx + m[1] * pdy))
            self.assertAlmostEqual(along, math.atan2(y1 - y0, x1 - x0), places=9)
        # a point of the band lies in one piece exactly; 1 m and a bit off the outline, in none
        for side in range(4):
            (x0, y0), (x1, y1) = corners[side], corners[(side + 1) % 4]
            run = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / run, (y1 - y0) / run
            for t in [0.05 + 0.9 * i / 40 for i in range(41)]:
                for off, want in ((0.0, 1), (250.0, 1), (-250.0, 1), (275.0, 0), (-275.0, 0)):
                    x, y = x0 + ux * t * run - uy * off, y0 + uy * t * run + ux * off
                    self.assertEqual(sum(self.inside(c, x, y) for c in copies), want, (side, t, off))

    def test_a_round_area_s_outline_in_short_chords(self):
        _lib, borders = self.library()
        area = scenery.PresetArea("Wheat field", 1000.0, 2000.0, 13000.0, "add", "round", border="hedge")
        runs = scenery.border_outline(area)
        self.assertEqual(len(runs), 32)   # chords of at most 2,600 (10 m) stray 65 (25 cm) inside a 50 m circle
        for (x0, y0), (x1, y1) in runs:
            self.assertAlmostEqual(math.hypot(x0 - 1000.0, y0 - 2000.0), 13000.0, places=6)
            self.assertLessEqual(13000.0 - math.hypot((x0 + x1) / 2 - 1000.0, (y0 + y1) / 2 - 2000.0),
                                 scenery.BORDER_SAG)
        self.assertEqual(runs[-1][1], runs[0][0])   # closed
        copies, erases = scenery.expand_border(area, borders)
        self.assertEqual((len(copies), len(erases)), (64, 32))   # each chord 2,552 long: two pieces of the 2,000 strip
        small = scenery.PresetArea("Wheat field", 0.0, 0.0, 520.0, "add", "round", border="hedge")
        self.assertEqual(len(scenery.border_outline(small)), 8)
        self.assertEqual(scenery.expand_border(dataclasses.replace(area, border="none"), borders), ([], []))

    def test_the_strips_plants_and_stones_land_in_the_band(self):
        """The strip: 10 tufts along y = 1000 every 200 from x = 100, a stone 100 off its middle line, a sticker on
        it (stickers stay: a border copies plants and stones) and a tuft 500 off it (the field beside: outside the
        band). A 5200 square turned 3, 4 has sides of 3 pieces 1733 long, each the middle of the strip: 8 tufts and
        the stone."""
        items = [compact(0, 100.0 + 200.0 * i, 1000.0) for i in range(10)]
        items += [compact(1, 1000.0, 1100.0), compact(2, 1000.0, 1000.0), compact(0, 1000.0, 1500.0)]
        data = make_scenery([block(items, box=(0.0, 0.0, 2000.0, 2000.0))], LOW_NAMES)
        borders = {"hedge": {"description": "", "map": "M04_Cotentin", "sources": [(1000.0, 1000.0, 1.0, 0.0, 2000.0)]}}
        area = scenery.PresetArea("Wheat field", 20000.0, 20000.0, 2600.0, "add", dx=3.0, dy=4.0, border="hedge")
        strips, _band = scenery.expand_border(area, borders, group=2)
        laid, _notes = scenery.copy_objects(data, strips, LOW_DESCS, {"M04_Cotentin": data})
        self.assertEqual(Counter(o.type.split("/")[-1] for o in laid), {"HerbeHaute_01": 96, "Caillou_01": 12})
        self.assertTrue(all(o.levels == 0x1F for o in laid))   # the levels the strip is drawn at on its map
        for o in laid:   # within 1 m of the outline: the square's own measure, |along| or |across| at its largest
            u = abs((o.x - 20000.0) * 0.6 + (o.y - 20000.0) * 0.8)
            v = abs((o.y - 20000.0) * 0.6 - (o.x - 20000.0) * 0.8)
            self.assertLessEqual(abs(max(u, v) - 2600.0), scenery.BORDER_WIDTH / 2 + 1e-6)
        self.assertEqual(sorted(round(abs(max(abs((o.x - 20000.0) * 0.6 + (o.y - 20000.0) * 0.8),
                                              abs((o.y - 20000.0) * 0.6 - (o.x - 20000.0) * 0.8)) - 2600.0))
                                for o in laid if o.type.endswith("Caillou_01")), [100] * 12)

    def test_a_preset_with_a_border(self):
        """The tiles as without a border but clipped 1 m inside the outline, then the border's strips (the preset's
        group, so the tiles beside them don't thin them) and its band erase; border none changes nothing and needs
        no border library."""
        lib, borders = self.library()
        area = scenery.PresetArea("Wheat field", 0.0, 0.0, 13000.0, "replace", border="hedge")
        plain = dataclasses.replace(area, border="none")
        copies, erases, stamps, objects = scenery.expand_preset(area, lib, group=3, borders=borders)
        copies0, erases0, stamps0, objects0 = scenery.expand_preset(plain, lib, group=3, borders={})
        self.assertEqual((objects, objects0), ([], []))   # tile kinds: no hedgerow, border or not
        strips, band = scenery.expand_border(area, borders, 3)
        inner = ("square", 0.0, 0.0, 13000.0 - scenery.BORDER_WIDTH / 2, 1.0, 0.0)
        self.assertEqual(copies, [dataclasses.replace(c, within=inner) for c in copies0] + strips)
        self.assertEqual(erases, erases0 + band)
        self.assertEqual(len(erases0), 1)   # replace mode: the area's own erase first
        self.assertEqual(stamps, stamps0)
        rnd = scenery.PresetArea("Wheat field", 0.0, 0.0, 13000.0, "add", "round", border="hedge")
        copies, _e, _s, _o = scenery.expand_preset(rnd, lib, borders=borders)
        self.assertEqual(copies[0].within, ("round", 0.0, 0.0, 13000.0 - scenery.BORDER_WIDTH / 2, 1.0, 0.0))


class Fields(unittest.TestCase):
    """[[field]]: a field kind laid as Eugen's editor laid a field, ONE real field's rows over the whole area in one
    direction (scenery.expand_field), and the hedge its border carries: the map's trees and field fence along the
    outline, outside it (scenery.expand_hedgerow, [[hedgerow]])."""

    TABLES = ('[[preset]]\nname = "Meadow"\nmap = "M04_Cotentin"\nsources = [[100000.0, 200000.0]]\n\n'
              '[[field]]\nname = "Wheat field"\ndescription = "One field."\nmap = "M04_Cotentin"\n'
              'sources = [[1000000.0, 900000.0, 30.0, 8000.0, 6000.0, 1400.0, 1500.0], '
              '[2000000.0, 800000.0, 120.0, 9000.0, 3000.0, 1000.0, 1000.0]]\n\n'
              '[[border]]\nname = "hedge"\nmap = "M04_Cotentin"\nsources = [[1000.0, 1000.0, 1.0, 0.0, 2000.0]]\n\n'
              '[[hedgerow]]\nmap = "M04_Cotentin"\ntrees_per_100m = 6.0\n'
              'trees = [["TypeWarrior/Pommier", 0.6, 30], ["TypeWarrior/Hetre_01", 0.4, 15]]\n'
              'fence = ["TypeWarrior/BarriereChamps_02", 31, 780.0]\n')

    def tables(self, text: str | None = None) -> Path:
        folder = Path(tempfile.mkdtemp(prefix="fields-"))
        (folder / "f.toml").write_text(self.TABLES if text is None else text, encoding="utf-8")
        return folder / "f.toml"

    def test_the_tables(self):
        path = self.tables()
        lib = scenery.preset_library(path)
        self.assertEqual((lib["Meadow"]["type"], lib["Wheat field"]["type"]), ("tile", "field"))
        self.assertEqual(lib["Wheat field"]["sources"][0],
                         scenery.FieldSource(1000000.0, 900000.0, 30.0, 8000.0, 6000.0, 1400.0, 1500.0))
        self.assertTrue(lib["Wheat field"]["aligned"])
        rows = scenery.hedgerow_library(path)
        self.assertEqual(rows["M04_Cotentin"], {
            "trees_per_100m": 6.0, "trees": [("TypeWarrior/Pommier", 0.6, 30), ("TypeWarrior/Hetre_01", 0.4, 15)],
            "fence": ("TypeWarrior/BarriereChamps_02", 31, 780.0)})
        for bad, why in (("[1.0, 2.0, 3.0, 8000.0, 6000.0, 1400.0]", "a field source is"),
                         ("[1.0, 2.0, 3.0, 1000.0, 6000.0, 1400.0, 1500.0]", "whole pitches"),
                         ("[1.0, 2.0, 3.0, 8000.0, 6000.0, 0.0, 1500.0]", "whole pitches")):
            with self.assertRaisesRegex(SceneryEditError, why):
                scenery.preset_library(self.tables(f'[[field]]\nname = "W"\nmap = "M"\nsources = [{bad}]\n'))
        with self.assertRaisesRegex(SceneryEditError, "a hedgerow needs a map"):
            scenery.hedgerow_library(self.tables("[[hedgerow]]\ntrees_per_100m = 3.0\n"))
        shipped = scenery.preset_library()   # the library the build ships: its fields are field kinds
        self.assertTrue(all(k["type"] in ("tile", "field") for k in shipped.values()))

    def test_one_field_s_rows_over_the_whole_area(self):
        """Every tile copies the SAME window (the source the seed picks), turned from the source's rows to the area's
        direction; tiles are rectangles of whole pitches, 5 x 1,400 along the rows by 4 x 1,500 across, laid edge to
        edge (no part of the area in two), clipped to the area; nothing of the area is left out; two stamps a tile
        (each a tile wide), from the same window."""
        from rusemod import brush
        lib = scenery.preset_library(self.tables())
        area = scenery.PresetArea("Wheat field", 50000.0, 60000.0, 20000.0, "add", dx=0.6, dy=0.8, seed=2)
        copies, stamps = scenery.expand_field(area, lib["Wheat field"], group=5)
        src = lib["Wheat field"]["sources"][0]   # seed 2 of two sources: the first
        self.assertTrue(copies)
        self.assertEqual({(round(c.x + c.sx, 6), round(c.y + c.sy, 6)) for c in copies}, {(src.x, src.y)})
        self.assertEqual({c.turn for c in copies}, {math.degrees(math.atan2(0.8, 0.6)) - 30.0})
        self.assertEqual({(c.radius, c.along) for c in copies}, {(3000.0, 3500.0)})
        self.assertTrue(all(c.fill and c.group == 5 and c.source == "M04_Cotentin" and c.shape == "square"
                            and (c.dx, c.dy) == (0.6, 0.8) and c.within == ("square", 50000.0, 60000.0, 20000.0, 0.6, 0.8)
                            for c in copies))
        # tile middles on a grid: 7,000 apart along the rows (0.6, 0.8), 6,000 across (-0.8, 0.6)
        along = sorted({round((c.x - 50000.0) * 0.6 + (c.y - 60000.0) * 0.8, 3) for c in copies})
        across = sorted({round(-(c.x - 50000.0) * 0.8 + (c.y - 60000.0) * 0.6, 3) for c in copies})
        self.assertEqual({round(b - a, 3) for a, b in zip(along, along[1:])}, {7000.0})
        self.assertEqual({round(b - a, 3) for a, b in zip(across, across[1:])}, {6000.0})
        foot = area.footprint()
        for k in range(-19, 19, 2):   # every point of the area lies in exactly one tile (off the tiles' joins)
            for m in range(-19, 19, 2):
                a, b = k * 1000.0 + 137.0, m * 1000.0 + 211.0
                x, y = 50000.0 + a * 0.6 - b * 0.8, 60000.0 + a * 0.8 + b * 0.6
                self.assertLess(foot.t2(x, y), 1.0)
                self.assertEqual(sum(c.footprint().t2(x, y) < 1.0 for c in copies), 1, (k, m))
        tile = copies[0].footprint()   # a tile's own shape: 3,500 out along the rows, 3,000 across
        self.assertLess(tile.t2(tile.x + 3499.0 * 0.6, tile.y + 3499.0 * 0.8), 1.0)
        self.assertGreater(tile.t2(tile.x - 2999.0 * 0.8 * 1.01, tile.y + 2999.0 * 0.6 * 1.01), 1.0)
        self.assertEqual(len(stamps), 2 * len(copies))
        self.assertEqual([(s.x, s.y, s.sx, s.sy) for s in stamps[:2]],
                         [(copies[0].x + a * 0.6, copies[0].y + a * 0.8, copies[0].sx, copies[0].sy)
                          for a in (-1750.0, 1750.0)])
        self.assertEqual({(s.brush, s.shape, s.edge, s.radius) for s in stamps},
                         {("stamp", "square", "hard", 3000.0 / brush.HARD_EDGE)})
        other = scenery.expand_field(dataclasses.replace(area, seed=1), lib["Wheat field"])[0]
        self.assertEqual({(round(c.x + c.sx), round(c.y + c.sy)) for c in other}, {(2000000, 800000)})

    def test_a_hedge_carries_the_map_s_trees_and_fence_outside_the_field(self):
        """Along each side: trees at the map's 6 per 100 m (a 100 m side: 6), 1.5 m (+-0.5) outside, by the species'
        shares, each at its own levels; fence pieces end to end 0.6 m outside, along the side; none solid. The same
        seed gives the same hedge; no border, or no hedgerow for the map, none. expand_preset lays them with a field
        kind's hedge border."""
        path = self.tables()
        row = scenery.hedgerow_library(path)["M04_Cotentin"]
        for shape, dx, dy in (("square", 1.0, 0.0), ("square", 0.6, -0.8), ("round", 1.0, 0.0)):
            area = scenery.PresetArea("Wheat field", 40000.0, 30000.0, 13000.0, "add", shape, dx=dx, dy=dy,
                                      border="hedge", seed=4)
            got = scenery.expand_hedgerow(area, row, seed=9)
            self.assertEqual(got, scenery.expand_hedgerow(area, row, seed=9), shape)
            trees = [o for o in got if not o.type.endswith("BarriereChamps_02")]
            fence = [o for o in got if o.type.endswith("BarriereChamps_02")]
            self.assertTrue(all(not o.solid for o in got))
            self.assertEqual({(o.type, o.levels) for o in trees} <= {("TypeWarrior/Pommier", 30),
                                                                      ("TypeWarrior/Hetre_01", 15)}, True)
            self.assertEqual({o.levels for o in fence}, {31})
            self.assertTrue(all(area.footprint().t2(o.x, o.y) > 1.0 for o in got), shape)  # all outside the field
            runs = scenery.border_outline(area)
            self.assertEqual(len(trees), sum(round(math.dist(a, b) / 260.0 * 6.0 / 100.0) for a, b in runs), shape)
            self.assertEqual(len(fence), sum(max(1, math.ceil(math.dist(a, b) / 780.0)) for a, b in runs), shape)
            if shape != "square":
                continue
            self.assertEqual((len(trees), len(fence)), (24, 4 * 34), shape)  # 6 trees, 34 pieces a 100 m side
            for (x0, y0), (x1, y1) in runs:
                run = math.hypot(x1 - x0, y1 - y0)
                ux, uy = (x1 - x0) / run, (y1 - y0) / run

                def out(o):   # how far outside this side (its outward normal -uy, ux), and how far along it
                    return -(o.x - x0) * uy + (o.y - y0) * ux, (o.x - x0) * ux + (o.y - y0) * uy
                mine = [o for o in trees if 0.0 <= out(o)[1] <= run and 0.0 < out(o)[0] < 600.0]
                self.assertEqual(len(mine), 6, shape)
                self.assertTrue(all(260.0 <= out(o)[0] <= 520.0 for o in mine), shape)
                posts = [o for o in fence if abs(out(o)[0] - scenery.FENCE_OUT) < 1e-6 and 0.0 <= out(o)[1] <= run]
                self.assertEqual(len(posts), 34, shape)
                self.assertTrue(all(abs(math.cos(math.radians(o.turn)) - ux) < 1e-9 for o in posts), shape)
        self.assertEqual(scenery.expand_hedgerow(dataclasses.replace(area, border="none"), row), [])
        edge = scenery.expand_hedgerow(dataclasses.replace(area, border="edge"), row, seed=9)  # a field's edge: the
        self.assertEqual(edge, [o for o in got if o.type.endswith("BarriereChamps_02")])         # fence alone
        self.assertTrue(edge)
        self.assertEqual(scenery.expand_hedgerow(area, None), [])
        lib, borders = scenery.preset_library(path), scenery.border_library(path)
        square = scenery.PresetArea("Wheat field", 40000.0, 30000.0, 13000.0, "add", border="hedge", seed=4)
        _c, _e, _s, objects = scenery.expand_preset(square, lib, group=2, borders=borders,
                                                    hedgerows=scenery.hedgerow_library(path))
        self.assertEqual(objects, scenery.expand_hedgerow(square, row, square.seed + 2))
        meadow = dataclasses.replace(square, name="Meadow")   # a tile kind's hedge: the strips alone
        self.assertEqual(scenery.expand_preset(meadow, lib, borders=borders,
                                               hedgerows=scenery.hedgerow_library(path))[3], [])


FB_NAMES = ["TypeWarrior/Labourage_terrefonce", "TypeWarrior/Paille", "TypeWarrior/Champs_Bles",
            "TypeWarrior/HerbeHaute_01", "TypeWarrior/BarriereChamps_03", "TypeWarrior/Labourage_triangle",
            "TypeWarrior/Paille_triangle", "TypeWarrior/Foin_3", "TypeWarrior/Tracteur", "TypeWarrior/Cabane_Pierre",
            "TypeWarrior/Caillou_10", "TypeWarrior/Pommier"]
FB_DESCS = {
    "TypeWarrior/Labourage_terrefonce": scenery.Descriptor("TypeWarrior/Labourage_terrefonce", "TSceneryDescriptorSticker",
                                                           "Stickers", "decal", None, "x"),
    "TypeWarrior/Paille": scenery.Descriptor("TypeWarrior/Paille", "TSceneryDescriptorSticker", "Stickers", "decal",
                                             None, "x"),
    "TypeWarrior/Champs_Bles": scenery.Descriptor("TypeWarrior/Champs_Bles", "TSceneryDescriptor", "Vegetation/Herbes",
                                                  "vegetation", None, "x"),
    "TypeWarrior/HerbeHaute_01": scenery.Descriptor("TypeWarrior/HerbeHaute_01", "TSceneryDescriptor",
                                                    "Vegetation/Herbes", "vegetation", None, "x"),
    "TypeWarrior/BarriereChamps_03": scenery.Descriptor("TypeWarrior/BarriereChamps_03", "TSceneryDescriptor",
                                                        "Props/Ferme", "prop", None, "x"),
    "TypeWarrior/Cabane_Pierre": scenery.Descriptor("TypeWarrior/Cabane_Pierre", "TSceneryDescriptorMultiState",
                                                    "COC/Normandie/Batiments", "building", "hut.ase2ndfbin", "x"),
    "TypeWarrior/Caillou_10": scenery.Descriptor("TypeWarrior/Caillou_10", "TSceneryDescriptor", "Props/Ferme", "prop",
                                                 None, "x"),
    "TypeWarrior/Pommier": scenery.Descriptor("TypeWarrior/Pommier", "TSceneryDescriptor", "Vegetation/Arbres",
                                              "vegetation", None, "x")}


class FieldBrush(unittest.TestCase):
    """[[fieldbrush]]: the WHOLE fields a dab touches turned into a look (scenery.expand_field_brush), the way Eugen's
    field is made: its prefab's row stickers (swapped to the look's kind where they lie), its crops (copied anew from a
    real field of the look, turned to its rows, landing only on the field) and the ground picture under the whole
    field (tinted to the look's colour, a square on each row sticker: the field's own shape). A field is its row
    stickers joined square to square (FIELD_ALONG, FIELD_ACROSS); the plot across a hedge, and everything that isn't
    the field's, stay."""

    LOOK = {"description": "", "map": "", "field_kinds": ("Labourage", "Paille"), "crops": ("Champs_",),
            "stickers": [("Paille", 1.0)], "sources": [(80000.0, 80000.0, 120.0, 30000.0, 30000.0, 0.0, "", "")],
            "colour": "#7b6927"}
    A, B, ANGLE = (20000.0, 20000.0), None, 30.0

    @staticmethod
    def grid(sym, cx, cy, deg, step_u, step_v, half_u, half_v=None):
        """Objects of `sym` on a grid round (cx, cy) along `deg` (u) and across it (v), facing `deg`."""
        a = math.radians(deg)
        ux, uy = math.cos(a), math.sin(a)
        half_v = half_u if half_v is None else half_v
        out = []
        for i in range(-int(half_u // step_u), int(half_u // step_u) + 1):
            for j in range(-int(half_v // step_v), int(half_v // step_v) + 1):
                u, v = i * step_u, j * step_v
                out.append(compact(sym, cx + u * ux - v * uy, cy + u * uy + v * ux, a))
        return out

    @staticmethod
    def across(cx, cy, deg, v):
        a = math.radians(deg)
        return cx - v * math.sin(a), cy + v * math.cos(a)

    HAY_AT = (24000.0, 20000.0)
    HUT_AT = (16000.0, 19000.0)

    def map_data(self, second=False, neighbour=False, past=False, farm=False, dressing=False, fragment=False,
                 harvested=False):
        """Field A: ploughed row stickers facing 30 deg round (20000, 20000), 2,500 apart along the rows and 3,500
        across (rows -7,000..7,000), with its own wheat crops, a fence and a hedge tuft; plot B: the same facing, its
        nearest row 4,600 across from A's last (past FIELD_ACROSS: the far side of a hedge); `second`, a field facing
        80 deg round (36000, 20000); `neighbour`, a plot of two row stickers facing 75 deg, one's middle inside A's
        edge squares and the other's 3,000 along its rows outside them; `past`, a one-sticker field facing 60 deg
        1,500 past that neighbour; `farm`, on A a hay piece at
        HAY_AT, a tractor 8,500 across from its middle (550 inside its edge: 2.1 m) and one at its middle, and a stone
        hut at HUT_AT; `dressing`, stones on A (one inside, one 1 m from its edge), an apple tree inside A, and stones
        on the source field's middle; `fragment`, one straw row sticker facing 120 deg whose middle lies inside A;
        `harvested`, three of the map's own crops laid harvested (sunk 150) 1,500 past HAY_AT along A's rows; a wheat
        field facing 120 deg round (80000, 80000) to copy crops from."""
        items = self.grid(0, 20000.0, 20000.0, 30.0, 2500.0, 3500.0, 10000.0, 7000.0)
        items += self.grid(2, 20000.0, 20000.0, 30.0, 1000.0, 1000.0, 9000.0, 6000.0)
        items += [compact(4, 21000.0, 21000.0), compact(3, 19500.0, 20500.0)]
        if farm:
            items += [compact(7, *self.HAY_AT), compact(8, *self.across(20000.0, 20000.0, 30.0, 8500.0)),
                      compact(8, 20000.0, 20000.0), compact(9, *self.HUT_AT, math.radians(30.0))]
        if dressing:
            items += [compact(10, 21500.0, 19500.0), compact(10, *self.across(20000.0, 20000.0, 30.0, 8800.0)),
                      compact(11, 18500.0, 21000.0)]
            items += self.grid(10, 80000.0, 80000.0, 120.0, 3000.0, 3000.0, 9000.0)
        if fragment:
            items.append(compact(1, 23000.0, 18000.0, math.radians(120.0)))
        if harvested:
            a = math.radians(30.0)
            for k in (1500.0, 1800.0, 2100.0):
                items.append(compact(2, self.HAY_AT[0] + k * math.cos(a), self.HAY_AT[1] + k * math.sin(a), z=-150.0))
        bx, by = self.across(20000.0, 20000.0, 30.0, 7000.0 + 4600.0 + 3500.0)
        items += self.grid(0, bx, by, 30.0, 2500.0, 3500.0, 6000.0, 3500.0)
        if second:
            items += self.grid(0, 36000.0, 20000.0, 80.0, 2500.0, 3500.0, 6000.0)
        if neighbour:   # (a plot of two: one middle in A's squares, one past them; a plot wholly inside A is A's)
            nx, ny = self.across(20000.0, 20000.0, 30.0, -7000.0 - 1500.0)
            items.append(compact(0, nx, ny, math.radians(75.0)))
            n75 = math.radians(75.0)
            items.append(compact(0, nx - 3000.0 * math.cos(n75), ny - 3000.0 * math.sin(n75), n75))
        if past:
            items.append(compact(0, *self.across(20000.0, 20000.0, 30.0, -10000.0), math.radians(60.0)))
        items += self.grid(1, 80000.0, 80000.0, 120.0, 2500.0, 3500.0, 15000.0)
        items += self.grid(2, 80000.0, 80000.0, 120.0, 1000.0, 1000.0, 15000.0)
        items += [compact(3, 80500.0, 80500.0)]
        return make_scenery([block(items, box=(0.0, 0.0, 100000.0, 100000.0))], FB_NAMES)

    @staticmethod
    def stickers(sc, sym=0):
        return [(m[3], m[7], math.degrees(math.atan2(m[4], m[0])) % 180.0)
                for _s, m, _k in scenery.walk_levels(sc, (0, 0, 1e6, 1e6), {sym})]

    @staticmethod
    def on(o, squares, deg=30.0):
        """Whether `o` lies inside one of field A's sticker squares (FIELD_HALF round each middle, along `deg`)."""
        a = math.radians(deg)
        h = scenery.FIELD_HALF + 1.0
        return any(abs((o.x - x) * math.cos(a) + (o.y - y) * math.sin(a)) <= h
                   and abs(-(o.x - x) * math.sin(a) + (o.y - y) * math.cos(a)) <= h for x, y in squares)

    def field_a(self, sc):
        """Field A's own row stickers: within its rows' extent round its middle, facing 30."""
        a = math.radians(30.0)
        out = []
        for x, y, f in self.stickers(sc):
            u = (x - 20000.0) * math.cos(a) + (y - 20000.0) * math.sin(a)
            v = -(x - 20000.0) * math.sin(a) + (y - 20000.0) * math.cos(a)
            if abs(u) <= 10001.0 and abs(v) <= 7001.0 and abs(f - 30.0) < 1.0:
                out.append((round(x, 3), round(y, 3)))
        return sorted(out)

    def test_the_rows_and_the_library(self):
        rows = scenery.parse_field_brushes([{"look": "Wheat", "x": 1, "y": 2, "radius": 3000, "shape": "square",
                                             "dx": 0.6, "dy": 0.8, "seed": 4}])
        self.assertEqual(rows, [scenery.FieldBrush("Wheat", 1.0, 2.0, 3000.0, "square", 0.6, 0.8, 4)])
        for bad, why in (({"x": 1, "y": 2, "radius": 3}, "has no look"),
                         ({"look": "W", "x": 1, "y": 2, "radius": 3, "size": 3}, "unknown key"),
                         ({"look": "W", "x": 1, "radius": 3}, "has no y"),
                         ({"look": "W", "x": 1, "y": 2, "radius": 3, "shape": "line"}, "round or square"),
                         ({"look": "W", "x": 1, "y": 2, "radius": 0}, "radius must be above 0")):
            with self.assertRaisesRegex(SceneryEditError, why):
                scenery.parse_field_brushes([bad])
        looks = scenery.look_library()   # the library the build ships: D-Day's looks
        self.assertTrue({"Wheat", "Ploughed"} <= set(looks))
        self.assertTrue(all(len(s) == 8 for k in looks.values() for s in k["sources"]))
        self.assertTrue(all(k["colour"].startswith("#") for k in looks.values()))
        # every source a real field with its own ground colour and row sticker kind
        self.assertTrue(all(s[6].startswith("#") and s[7] for k in looks.values() for s in k["sources"]))
        self.assertTrue(all(s[7] == "Paille" for s in looks["Wheat"]["sources"]))
        self.assertTrue(all(s[7] in ("Labourage_terrefonce", "Labourage_terreclaire", "Labourage")
                            for s in looks["Ploughed"]["sources"]))
        with tempfile.TemporaryDirectory() as d:   # an older library's six numbers still read, as no colour
            p = Path(d) / "lib.toml"
            p.write_text('[[look]]\nname = "W"\nmap = "M"\nstickers = [["Paille", 1.0]]\n'
                         'sources = [[1, 2, 3, 4, 5, 6]]\n', encoding="utf-8")
            self.assertEqual(scenery.look_library(p)["W"]["sources"], [(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, "", "")])
            p.write_text('[[look]]\nname = "W"\nmap = "M"\nstickers = [["Paille", 1.0]]\n'
                         'sources = [[1, 2, 3, 4, 5, "#123456", "Paille"]]\n', encoding="utf-8")
            with self.assertRaisesRegex(SceneryEditError, "a source is"):
                scenery.look_library(p)

    def test_a_field_copied_whole_somewhere_else(self):
        """[[fieldcopy]] (the ploppable field, for a blank map): the field under (sx, sy) laid whole at (x, y), turned
        45 deg round its middle: its 45 row stickers facing 75, its crops, fence and hedge tuft, everything inside its
        squares and the border round them, nothing of plot B across the hedge; the spot erased first, square by
        square; the picture stamped per grown square from where it lies in the source, turned the same."""
        data = self.map_data()
        sc = scenery.Scenery(data)
        rows = scenery.parse_field_copies([{"x": 60000, "y": 30000, "sx": 20500, "sy": 20300, "turn": 45}])
        self.assertEqual(rows, [scenery.FieldCopy(60000.0, 30000.0, 20500.0, 20300.0, 45.0, 1560.0)])
        for bad, why in (({"x": 1, "y": 2, "sx": 3}, "has no sy"), ({"x": 1, "y": 2, "sx": 3, "sy": 4, "size": 1},
                                                                     "unknown key"),
                         ({"x": 1, "y": 2, "sx": 3, "sy": 4, "border": -1}, "border")):
            with self.assertRaisesRegex(SceneryEditError, why):
                scenery.parse_field_copies([bad])
        erases, copies, stamps, notes = scenery.expand_field_copy(rows[0], sc)
        self.assertEqual((len(erases), len(stamps), len(copies)), (45, 45, 1))
        self.assertIn("field of 45 row sticker(s)", notes[0])
        laid, _n = scenery.copy_objects(data, copies, FB_DESCS)
        a = self.field_a(sc)
        mx = (min(x for x, _y in a) + max(x for x, _y in a)) / 2
        my = (min(y for _x, y in a) + max(y for _x, y in a)) / 2
        c, s = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
        want = sorted((round(60000 + (x - mx) * c - (y - my) * s, 1), round(30000 + (x - mx) * s + (y - my) * c, 1))
                      for x, y in a)
        rows_laid = [o for o in laid if o.type == "TypeWarrior/Labourage_terrefonce"]
        self.assertEqual(sorted((round(o.x, 1), round(o.y, 1)) for o in rows_laid), want)   # A whole, nothing of B
        self.assertTrue(all(abs(o.turn % 180 - 75.0) < 0.1 for o in rows_laid))
        self.assertEqual({o.type for o in laid}, {"TypeWarrior/Labourage_terrefonce", "TypeWarrior/Champs_Bles",
                                                  "TypeWarrior/HerbeHaute_01", "TypeWarrior/BarriereChamps_03"})
        self.assertTrue(all(e.what == scenery.ERASE_DEFAULT and e.shape == "square" for e in erases))
        for st in stamps:   # each reads the source under it: its middle back through the turn
            qx, qy = st.source_of(st.x, st.y)
            ox, oy = st.x - 60000, st.y - 30000
            self.assertAlmostEqual(qx, mx + ox * c + oy * s, places=3)
            self.assertAlmostEqual(qy, my - ox * s + oy * c, places=3)
            self.assertEqual((st.brush, st.edge, st.turn), ("stamp", "hard", 45.0))
        none = scenery.expand_field_copy(scenery.FieldCopy(1, 2, 50000.0, 5000.0), sc)
        self.assertEqual(none[:3], ([], [], []))
        self.assertIn("no field", none[3][0])

    def test_what_stands_on_a_field_stays_as_eugen_lays_it(self):
        """D-Day, measured 2026-10-15: hay and farm machines left on a changed field keep a harvested patch:
        the new crops within HAY_PATCH of them laid as Eugen lays them harvested (wheat squashed to a quarter, sunk
        0.13 m); no new crop lands in a building's box or within its type's gap of it; on a look whose fields carry
        no hay (ploughed) the hay goes, and the tractors past NO_HAY_MACHINE_DEPTH in (the one 2.1 m in stays)."""
        data = self.map_data(farm=True)
        sc = scenery.Scenery(data)
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        hut = {"TypeWarrior/Cabane_Pierre": (-1000.0, -800.0, 1000.0, 800.0, 300.0)}
        erases, _objects, copies, _stamps, notes = scenery.expand_field_brush(dab, self.LOOK, sc, buildings=hut)
        self.assertFalse(any(e.types == ("TypeWarrior/Foin_3",) for e in erases))   # the hay stays
        self.assertIn("3 hay piece(s) and farm machine(s) left standing", notes[0])
        self.assertIn("its crops kept off 1 building(s)", notes[0])
        laid, cnotes = scenery.copy_objects(data, copies, FB_DESCS)
        crops = [o for o in laid if o.type == "TypeWarrior/Champs_Bles"]
        self.assertTrue(crops)
        edge = self.across(20000.0, 20000.0, 30.0, 8500.0)
        stands = (self.HAY_AT, edge, (20000.0, 20000.0))
        low, lift = scenery.HARVESTED["Champs_Bles"]
        for o in crops:
            near = min(math.dist((o.x, o.y), p) for p in stands) < scenery.HAY_PATCH
            self.assertEqual((o.height, o.lift) == (low, lift), near)   # harvested round them, standing elsewhere
        self.assertTrue(any((o.height, o.lift) == (low, lift) for o in crops))
        a = math.radians(30.0)
        for o in crops:   # none in the hut's box grown by its gap (its box turned with it)
            du = abs((o.x - self.HUT_AT[0]) * math.cos(a) + (o.y - self.HUT_AT[1]) * math.sin(a)) - 1000.0
            dv = abs(-(o.x - self.HUT_AT[0]) * math.sin(a) + (o.y - self.HUT_AT[1]) * math.cos(a)) - 800.0
            self.assertGreaterEqual(math.hypot(max(du, 0.0), max(dv, 0.0)), 300.0 - 1e-6)
            self.assertFalse(du < 0 and dv < 0)
        self.assertTrue(any("laid harvested round hay" in n for n in cnotes))
        self.assertTrue(any("kept off a building" in n for n in cnotes))
        # a look whose fields carry no hay: the hay goes, and the tractor in the middle; the one at the edge stays
        bare = dict(self.LOOK, hay=False)
        erases, _o, copies, _s, notes = scenery.expand_field_brush(dab, bare, sc)
        gone = [(e.types, round(e.x), round(e.y)) for e in erases if e.types in (("TypeWarrior/Foin_3",),
                                                                                 ("TypeWarrior/Tracteur",))]
        self.assertEqual(sorted(gone), [(("TypeWarrior/Foin_3",), 24000, 20000),
                                        (("TypeWarrior/Tracteur",), 20000, 20000)])
        self.assertIn("2 hay piece(s) and farm machine(s) taken off (Wheat fields carry none)", notes[0])
        self.assertIn("1 hay piece(s) and farm machine(s) left standing", notes[0])
        self.assertTrue(all(len(c.harvest) <= 1 for c in copies))
        self.assertEqual({(round(h[0]), round(h[1])) for c in copies for h in c.harvest}, {tuple(map(round, edge))})
        # the map without farm things or buildings: the same as before (no patches, nothing kept off)
        plain = scenery.expand_field_brush(dab, self.LOOK, scenery.Scenery(self.map_data()))
        self.assertTrue(all(not c.harvest and not c.avoid for c in plain[2]))

    def test_a_plot_lying_wholly_inside_changes_with_the_field(self):
        """A plot whose every sticker's middle lies inside the fields a dab changes (a straw sticker at another facing:
        Q's straw bands, 2026-10-15) is one of its fields; without it, A alone."""
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        alone = scenery.brush_fields(dab, self.LOOK, scenery.Scenery(self.map_data()))
        self.assertEqual([len(f) for f in alone], [45])
        sc = scenery.Scenery(self.map_data(fragment=True))
        fields = scenery.brush_fields(dab, self.LOOK, sc)
        self.assertEqual(sorted(len(f) for f in fields), [1, 45])
        frag = next(f for f in fields if len(f) == 1)
        self.assertAlmostEqual(math.degrees(math.atan2(frag[0][1][4], frag[0][1][0])) % 180.0, 120.0, places=1)
        _e, objects, _c, _s, notes = scenery.expand_field_brush(dab, self.LOOK, sc)
        laid = [o for o in objects if abs(o.x - 23000.0) < 1 and abs(o.y - 18000.0) < 1]
        self.assertEqual([o.type for o in laid], ["TypeWarrior/Paille"])   # laid again as the look's kind
        self.assertTrue(any("a whole field of 1 row sticker(s)" in n for n in notes))

    def test_the_field_s_dressing_is_the_source_s_from_its_edge_in(self):
        """With the game's descriptors, the field's dressing from FIELD_EDGE in (stones, low plants, ground stickers,
        trees; not its rows, crops or hay) is taken off by one erase whose mask is the field's interior, and the
        source's is laid there through the crops' cells; along the edge the map's stays. Without them, as before."""
        data = self.map_data(dressing=True)
        sc = scenery.Scenery(data)
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        erases, _o, copies, _s, notes = scenery.expand_field_brush(dab, self.LOOK, sc, descs=FB_DESCS)
        dress = [e for e in erases if e.mask is not None]
        self.assertEqual(len(dress), 1)
        e = dress[0]
        self.assertTrue({"TypeWarrior/Caillou_10", "TypeWarrior/Pommier", "TypeWarrior/HerbeHaute_01"} <= set(e.types))
        self.assertFalse({"TypeWarrior/Champs_Bles", "TypeWarrior/Paille", "TypeWarrior/Labourage_terrefonce",
                          "TypeWarrior/Foin_3", "TypeWarrior/Tracteur"} & set(e.types))
        self.assertEqual(e.what, ())
        inside, near_edge = (21500.0, 19500.0), self.across(20000.0, 20000.0, 30.0, 8800.0)
        self.assertTrue(e.mask(*inside) and e.mask(18500.0, 21000.0))
        self.assertFalse(e.mask(*near_edge))   # 0.95 m from A's edge: the edge band stays
        self.assertFalse(e.mask(*self.across(20000.0, 20000.0, 30.0, 12000.0)))   # past A
        self.assertIn("its dressing from 2 m in", notes[0])
        kinds = {i: FB_DESCS[n].group for i, n in enumerate(sc.names) if n in FB_DESCS}
        after = scenery.Scenery(scenery.erase_objects(data, [e], kinds)[0])   # the erase, through its mask
        left = {(after.names[s].rsplit("/", 1)[-1], round(m[3]), round(m[7]))
                for s, m, _k in scenery.walk_levels(after, (0.0, 0.0, 1e6, 1e6), {10, 11})}
        self.assertFalse({("Caillou_10", 21500, 19500), ("Pommier", 18500, 21000)} & left)
        self.assertIn(("Caillou_10", round(near_edge[0]), round(near_edge[1])), left)
        self.assertEqual(sum(1 for nm, x, _y in left if nm == "Caillou_10" and x > 60000), 49)   # the source's stay
        laid, _n = scenery.copy_objects(data, copies, FB_DESCS)
        stones = [o for o in laid if o.type == "TypeWarrior/Caillou_10"]
        self.assertTrue(stones)
        self.assertTrue(all(e.mask(o.x, o.y) for o in stones))   # the source's, in A's interior only
        self.assertFalse(any(o.type in ("TypeWarrior/Pommier", "TypeWarrior/Paille", "TypeWarrior/Labourage_terrefonce")
                             for o in laid))
        plain = scenery.expand_field_brush(dab, self.LOOK, sc)
        self.assertFalse(any(x.mask is not None for x in plain[0]) or any(c.inside is not None for c in plain[2]))

    def test_eugens_own_harvested_ground_round_hay_keeps_its_shape(self):
        """The map's own crops laid harvested within HAY_REACH of hay that stays mark the harvested ground: a new crop
        within HARVESTED_SPOT of one is laid as it is (its height and sink); one past HAY_REACH marks nothing."""
        data = self.map_data(farm=True, harvested=True)
        sc = scenery.Scenery(data)
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        _e, _o, copies, _s, _n = scenery.expand_field_brush(dab, self.LOOK, sc)
        spots = {(round(h[0]), round(h[1]), h[3], h[4], h[5]) for c in copies for h in c.harvest if len(h) == 6}
        a = math.radians(30.0)
        want = {(round(self.HAY_AT[0] + k * math.cos(a)), round(self.HAY_AT[1] + k * math.sin(a)), 1.0, -150.0,
                 "Champs_Bles") for k in (1500.0, 1800.0)}
        self.assertEqual(spots, want)   # (the one 2,100 past the hay: past HAY_REACH)
        laid, _n = scenery.copy_objects(data, copies, FB_DESCS)
        spot_xy = [(s[0], s[1]) for s in want]
        stands = (self.HAY_AT, self.across(20000.0, 20000.0, 30.0, 8500.0), (20000.0, 20000.0))
        for o in (o for o in laid if o.type == "TypeWarrior/Champs_Bles"):
            if min(math.dist((o.x, o.y), p) for p in spot_xy) < scenery.HARVESTED_SPOT - 1:
                self.assertEqual((o.height, o.lift), (1.0, -150.0))
            elif min(math.dist((o.x, o.y), p) for p in stands) < scenery.HAY_PATCH - 1:
                self.assertEqual((o.height, o.lift), scenery.HARVESTED["Champs_Bles"])

    def test_the_building_table_and_gaps(self):
        """building_table: each building type's model box (a composite's together) and its gap in map units, from
        building_gaps (the library's own: D-Day's, Cabane_Pierre 1.85 m); CopyArea.avoids: inside a building's box or
        within its gap of it."""
        default, gaps = scenery.building_gaps()
        self.assertGreater(default, 0.0)
        self.assertEqual(gaps["Cabane_Pierre"], 1.85)
        boxes = {"hut.ase2ndfbin": (-1000.0, -800.0, 0.0, 1000.0, 800.0, 500.0)}
        table = scenery.building_table(FB_NAMES, FB_DESCS, boxes.get, (2.0, {"Cabane_Pierre": 1.5}))
        self.assertEqual(table, {"TypeWarrior/Cabane_Pierre": (-1000.0, -800.0, 1000.0, 800.0, 1.5 * 260.0)})
        self.assertEqual(scenery.building_table(FB_NAMES, FB_DESCS, lambda m: None, (2.0, {})), {})
        area = scenery.CopyArea(0.0, 0.0, 10.0, 0.0, 0.0, avoid=((100.0, 0.0, 50.0, 20.0, 1.0, 0.0, 30.0),
                                                                     (0.0, 500.0, 40.0)))
        self.assertTrue(area.avoids(100.0, 0.0) and area.avoids(170.0, 0.0) and area.avoids(100.0, 45.0))
        self.assertFalse(area.avoids(185.0, 0.0) or area.avoids(100.0, 55.0) or area.avoids(175.0, 45.0))
        self.assertTrue(area.avoids(0.0, 530.0) and not area.avoids(0.0, 545.0))

    def test_a_field_s_painted_outline(self):
        """scenery.field_outline: the cells reachable from the field's squares through its own colour, inside its squares
        grown by OUTLINE_REACH; a dark line past its last squares stops the paint (the same yellow beyond the line is
        the next plot's); a line through it stays, its sides painted (both hold the field's rows: a track, or the
        boundary of two plots joined); a dark patch it closes round is a hole, so still the field."""
        squares = [(float(x), 0.0, 2048.0, 0.0) for x in range(0, 20001, 2500)]   # a row of 9, 0 to 20,000 along x
        yellow, dark = (166, 133, 41), (60, 70, 20)
        clip = scenery.field_outline(squares, lambda x, y: yellow)
        x0, y0, cell, w, h, bits = clip

        def at(x, y):
            i, j = int((x - x0) // cell), int((y - y0) // cell)
            return 0 <= i < w and 0 <= j < h and bits[j * w + i] == 1
        reach = scenery.OUTLINE_REACH
        self.assertTrue(at(10000.0, 0.0) and at(-2048.0 - reach + cell, 0.0) and at(10000.0, 2048.0 + reach - cell))
        self.assertFalse(at(-2048.0 - reach - 2 * cell, 0.0) or at(10000.0, 2048.0 + reach + 2 * cell))
        through = scenery.field_outline(squares, lambda x, y: dark if 15000.0 <= x <= 15600.0 else yellow)
        x0, y0, cell, w, h, bits = through
        self.assertTrue(at(14000.0, 0.0) and not at(15300.0, 0.0) and at(18000.0, 0.0))       # the line stays
        past = scenery.field_outline(squares, lambda x, y: dark if 22200.0 <= x <= 22400.0 else yellow)
        x0, y0, cell, w, h, bits = past
        self.assertTrue(at(22100.0, 0.0) and not at(22300.0, 0.0) and not at(22600.0, 0.0))   # stops at the line
        patch = scenery.field_outline(squares, lambda x, y: dark if math.hypot(x - 8000.0, y) < 900.0 else yellow)
        x0, y0, cell, w, h, bits = patch
        self.assertTrue(at(8000.0, 0.0) and at(8500.0, 300.0))                                  # a hole: filled
        self.assertEqual(scenery.field_outline(squares, lambda x, y: None), ())

    def test_with_the_picture_one_clipped_stamp_a_field(self):
        """Given the map's picture, each field's paint is ONE stamp over it, clipped to its painted outline, through the
        field's same map (the same spot read as by the stamps per sticker); without it, a stamp per row sticker."""
        sc = scenery.Scenery(self.map_data())
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        plain = scenery.expand_field_brush(dab, self.LOOK, sc)[3]
        self.assertEqual(len(plain), 45)
        clipped = scenery.expand_field_brush(dab, self.LOOK, sc, picture=lambda x, y: (166, 133, 41))[3]
        self.assertEqual(len(clipped), 1)
        st = clipped[0]
        self.assertTrue(st.clip and st.brush == "stamp" and st.edge == "hard")
        for p in plain[:5]:   # the same picture map as the per-sticker stamps
            qa, qb = st.source_of(p.x, p.y), p.source_of(p.x, p.y)
            self.assertLess(math.dist(qa, qb), 1e-3)
        f = st.footprint()
        x0, y0, cell, w, h, _bits = st.clip
        for x, y in ((x0, y0), (x0 + w * cell, y0 + h * cell)):   # full strength over the whole mask
            self.assertLessEqual(f.t2(x, y), 0.85 ** 2)

    def test_a_fragment_is_painted_as_the_biggest_field(self):
        """A dab over A's edge, the one-sticker field C (facing 60) and the two-sticker neighbour (75): C and the
        neighbour, fragments under SMALL_FIELD stickers, take A's source and its picture through A's own map (the
        same spot read for a point between one of theirs and one of A's), not a real field at their own angle."""
        sc = scenery.Scenery(self.map_data(neighbour=True, past=True))
        looks = {"Wheat": dict(self.LOOK, sources=[(80000.0, 80000.0, 120.0, 30000.0, 30000.0, 0.0, "", ""),
                                                   (90000.0, 20000.0, 60.0, 30000.0, 30000.0, 0.0, "", "")])}
        x, y = self.across(20000.0, 20000.0, 30.0, -8500.0)
        dab = scenery.FieldBrush("Wheat", x, y, 2000.0)
        fields = scenery.brush_fields(dab, looks["Wheat"], sc)
        self.assertEqual(sorted(len(f) for f in fields), [1, 2, 45])
        _e, _o, _c, stamps, notes = scenery.expand_field_brush(dab, looks["Wheat"], sc, fields=fields)
        self.assertEqual({(s.fx, s.fy) for s in stamps}, {(90000.0, 20000.0)})   # A's (rows nearest: 60), folded
        self.assertEqual(len({round(s.turn, 6) for s in stamps}), 1)                # A's turn
        a_stamp = next(s for s in stamps if math.dist((s.x, s.y), (20000.0, 20000.0)) < 9000.0)
        for s in stamps:
            h = ((s.x + a_stamp.x) / 2, (s.y + a_stamp.y) / 2)
            self.assertLess(math.dist(s.source_of(*h), a_stamp.source_of(*h)), 1e-6)
        self.assertEqual(sum("like the field at (90000, 20000)" in n for n in notes), 3)

    def test_a_field_takes_its_source_fields_colour_and_rows(self):
        """Each field is ONE real field of the look near and far: the source whose crops run nearest its rows gives
        the row sticker kind (its corner pieces that kind's corner pieces) and the picture (stamped from it, so its
        colour), not the look's median colour and share (which laid all four looks olive-brown, the owner's
        2026-10-15 shots)."""
        sc = scenery.Scenery(self.map_data())
        dab = scenery.FieldBrush("Ploughed", 20000.0, 20000.0, 1000.0)
        look = dict(self.LOOK, colour="#7b6927", sources=[
            (80000.0, 80000.0, 120.0, 30000.0, 30000.0, 0.0, "#724f25", "Labourage_terrefonce")])
        _e, objects, _c, stamps, notes = scenery.expand_field_brush(dab, look, sc)
        self.assertEqual({o.type for o in objects}, {"TypeWarrior/Labourage_terrefonce"})
        self.assertEqual({s.brush for s in stamps}, {"stamp"})
        self.assertIn("Labourage_terrefonce rows, its ground picture (#724f25)", notes[0])
        # a source without its own: the look's main kind
        bare = dict(look, sources=[(80000.0, 80000.0, 120.0, 30000.0, 30000.0, 0.0, "", "")])
        _e, objects, _c, stamps, notes = scenery.expand_field_brush(dab, bare, sc)
        self.assertEqual({o.type for o in objects}, {"TypeWarrior/Paille"})
        self.assertIn("its ground picture (#7b6927)", notes[0])
        # a row kind the map doesn't have: the look's main kind
        other = dict(look, sources=[(80000.0, 80000.0, 120.0, 30000.0, 30000.0, 0.0, "#724f25", "Nowhere")])
        self.assertEqual({o.type for o in scenery.expand_field_brush(dab, other, sc)[1]}, {"TypeWarrior/Paille"})

    def test_a_dab_changes_the_whole_field_it_touches(self):
        """A dab 1,000 round in A's middle: every row sticker of A (63) laid again where it was, facing the same way,
        now straw; one square erase and one picture stamp on each, the sticker's own size; A's crops copied anew,
        landing only on A; plot B across the hedge, the fence and the hedge tuft untouched."""
        data = self.map_data()
        sc = scenery.Scenery(data)
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0, seed=1)
        erases, objects, copies, stamps, notes = scenery.expand_field_brush(dab, self.LOOK, sc)
        a = self.field_a(sc)
        self.assertEqual(len(a), 9 * 5)
        self.assertEqual(sorted((round(o.x, 3), round(o.y, 3)) for o in objects), a)   # A whole, nothing of B
        self.assertTrue(all(o.type == "TypeWarrior/Paille" and abs(o.turn - 30.0) < 0.1 and not o.solid
                            for o in objects))
        self.assertEqual(sorted((round(e.x, 3), round(e.y, 3)) for e in erases), a)
        self.assertTrue(all((e.shape, e.what) == ("square", ()) and abs(e.radius - scenery.FIELD_HALF) < 1.0
                            for e in erases))
        self.assertTrue(all(abs(math.degrees(math.atan2(e.dy, e.dx)) - 30.0) < 0.1 for e in erases))
        self.assertTrue(all({"TypeWarrior/Labourage_terrefonce", "TypeWarrior/Champs_Bles"} <= set(e.types)
                            and not {"TypeWarrior/HerbeHaute_01", "TypeWarrior/BarriereChamps_03"} & set(e.types) for e in erases))
        self.assertEqual(len(stamps), len(a))
        # the source field's picture stamped on each square, turned from its rows (120) onto A's (30): a quarter turn;
        # each stamp covers its own sticker's square and reaches FIELD_STAMP past it only toward A's own stickers:
        # A's outline is its stickers' (the plot beyond keeps its ground)
        self.assertTrue(all((s.brush, s.shape, s.edge, s.clear) == ("stamp", "square", "hard", False)
                            and abs(abs(s.turn) - 90.0) < 0.01 for s in stamps))
        t, h, k = math.radians(30.0), scenery.FIELD_HALF, scenery.FIELD_STAMP
        sides = []
        for x, y in a:
            s = min(stamps, key=lambda s: math.dist((s.x, s.y), (x, y)))
            du = (s.x - x) * math.cos(t) + (s.y - y) * math.sin(t)
            dv = -(s.x - x) * math.sin(t) + (s.y - y) * math.cos(t)
            lo_u, hi_u, lo_v, hi_v = du - s.length, du + s.length, dv - s.radius, dv + s.radius
            self.assertTrue(all(abs(e) >= h - 1.0 and abs(e) <= h * k + 1.0 for e in (lo_u, hi_u, lo_v, hi_v)))
            u = (x - 20000.0) * math.cos(t) + (y - 20000.0) * math.sin(t)
            v = -(x - 20000.0) * math.sin(t) + (y - 20000.0) * math.cos(t)
            if u > 9000.0:    # A's last sticker along: its far side at its own edge, its near side reaching on
                self.assertAlmostEqual(hi_u, h, delta=1.0)
                self.assertAlmostEqual(-lo_u, h * k, delta=1.0)
            if v < -6000.0:   # A's last row across, by the plot over the hedge: its outer side at its own edge
                self.assertAlmostEqual(-lo_v, h, delta=1.0)
            sides.append((hi_u, lo_u))
        self.assertTrue(any(abs(hi - h * k) < 1.0 and abs(-lo - h * k) < 1.0 for hi, lo in sides))   # inside: both
        srcs = [s.source_of(s.x, s.y) for s in stamps]
        self.assertTrue(all(abs(x - 80000.0) <= 15000.0 and abs(y - 80000.0) <= 15000.0 for x, y in srcs))
        # one map for the whole field: any two stamps read the same spot for the point half way between them (no
        # seam), folded into the source's middle square
        for p in range(len(stamps)):
            for q in range(p + 1, len(stamps)):
                h = ((stamps[p].x + stamps[q].x) / 2, (stamps[p].y + stamps[q].y) / 2)
                self.assertLess(math.dist(stamps[p].source_of(*h), stamps[q].source_of(*h)), 1e-6)
        self.assertTrue(all(s.fold == 15000.0 and (s.fx, s.fy) == (80000.0, 80000.0) for s in stamps))
        laid, _n = scenery.copy_objects(data, copies, FB_DESCS)
        self.assertTrue(laid)
        self.assertEqual({o.type for o in laid}, {"TypeWarrior/Champs_Bles"})
        pts = [(x, y) for x, y in a]
        self.assertTrue(all(self.on(o, pts)
                            for o in laid))
        self.assertTrue(all(abs(abs(c.turn) - 90.0) < 0.01 for c in copies))   # 120 to 30: a quarter turn
        self.assertIn("a whole field of 45 row sticker(s)", notes[0])
        self.assertEqual(len(scenery.expand_field_brush(dab, dict(self.LOOK, colour=""), sc)[3]), len(a))  # (its own)
        b = scenery.expand_field_brush(scenery.FieldBrush("Wheat", *self.across(20000.0, 20000.0, 30.0, 15100.0), 500.0),
                                       self.LOOK, sc)[1]
        self.assertEqual(len(b), 5 * 3)   # a dab on B: B alone (5 along, 3 rows)

    def test_another_plot_s_row_sticker_with_its_middle_in_the_field_goes_with_it(self):
        """The neighbour plot's sticker whose middle lies in A's squares is laid again where it was, facing as it was,
        as A's new kind (Q's straw bands, 2026-10-15); its other sticker, middle outside A, isn't touched."""
        sc = scenery.Scenery(self.map_data(neighbour=True))
        nx, ny = self.across(20000.0, 20000.0, 30.0, -8500.0)
        n75 = math.radians(75.0)
        ox, oy = nx - 3000.0 * math.cos(n75), ny - 3000.0 * math.sin(n75)
        objects = scenery.expand_field_brush(scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0), self.LOOK, sc)[1]
        back = [o for o in objects if abs(o.x - nx) < 0.5 and abs(o.y - ny) < 0.5]
        self.assertEqual([(o.type, round(o.turn) % 180) for o in back], [("TypeWarrior/Paille", 75)])
        self.assertFalse([o for o in objects if abs(o.x - ox) < 0.5 and abs(o.y - oy) < 0.5])

    def test_a_neighbour_two_dabs_erases_take_is_laid_again_once(self):
        """The neighbour sticker between A and a one-sticker field C facing 60 deg (1,500 past it, not joined to A or
        to it: other facings): dabs on A and on C each take it in their erases; with the map's `relaid` shared it is
        laid back once (D-Day's dabs 3 and 4 laid one Paille twice)."""
        sc = scenery.Scenery(self.map_data(neighbour=True, past=True))
        nx, ny = self.across(20000.0, 20000.0, 30.0, -8500.0)
        cx, cy = self.across(20000.0, 20000.0, 30.0, -10000.0)
        looks = {"Wheat": self.LOOK, "Ploughed": dict(self.LOOK, stickers=[("Labourage_terrefonce", 1.0)])}
        dabs = [scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0), scenery.FieldBrush("Ploughed", cx, cy, 500.0)]
        own, changed = scenery.own_fields(dabs, looks, sc)
        self.assertEqual([len(f) for fs in own for f in fs], [45, 1])

        def back(relaid):
            out = 0
            for k, dab in enumerate(dabs):
                erases, objects, _c, _s, _n = scenery.expand_field_brush(dab, looks[dab.look], sc, fields=own[k],
                                                                         changed=changed, relaid=relaid)
                self.assertTrue(any(e.footprint().t2(nx, ny) < 1.0 for e in erases))   # each dab's erase takes it
                out += sum(1 for o in objects if abs(o.x - nx) < 0.5 and abs(o.y - ny) < 0.5)
            return out
        self.assertEqual(back(None), 2)    # each dab alone lays it back
        self.assertEqual(back(set()), 1)   # the map's dabs together: once

    def test_two_dabs_on_one_field_the_later_paints_it(self):
        """Two dabs on A (Wheat, then Ploughed): A is the later dab's alone, each of its stickers laid once; the first
        dab does nothing; a sticker one dab changes is never laid back as a neighbour by another."""
        sc = scenery.Scenery(self.map_data(neighbour=True))
        looks = {"Wheat": self.LOOK, "Ploughed": dict(self.LOOK, stickers=[("Labourage_terrefonce", 1.0)])}
        dabs = [scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0),
                scenery.FieldBrush("Ploughed", 22165.0, 21250.0, 1000.0)]   # on A's sticker 2,500 along
        own, changed = scenery.own_fields(dabs, looks, sc)
        self.assertEqual([len(o) for o in own], [0, 1])
        self.assertEqual(len(changed), 9 * 5)
        first = scenery.expand_field_brush(dabs[0], looks["Wheat"], sc, fields=own[0], changed=changed)
        self.assertEqual(first[:4], ([], [], [], []))
        self.assertIn("painted by a later dab", first[4][0])
        _e, objects, _c, _s, _n = scenery.expand_field_brush(dabs[1], looks["Ploughed"], sc, fields=own[1],
                                                             changed=changed)
        spots = [(round(o.x, 1), round(o.y, 1)) for o in objects]
        self.assertEqual(len(spots), len(set(spots)))                  # nothing laid twice
        self.assertEqual(sum(1 for o in objects if o.type == "TypeWarrior/Labourage_terrefonce"
                             and abs(o.turn - 30.0) < 0.1), 9 * 5)   # A, now the later dab's look

    def test_the_crops_turn_by_their_own_run(self):
        """A source whose crops run 10 degrees off its stickers: the copy turns 10 degrees more, so they run with the
        rows painted over (the least turn, a half turn either way: rows have no front)."""
        sc = scenery.Scenery(self.map_data())
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        plain = scenery.expand_field_brush(dab, self.LOOK, sc)[2][0].turn
        off = dict(self.LOOK, sources=[(80000.0, 80000.0, 120.0, 30000.0, 30000.0, 10.0, "", "")])
        turned = scenery.expand_field_brush(dab, off, sc)[2][0].turn
        self.assertAlmostEqual((turned - plain + 90.0) % 180.0 - 90.0, -10.0, places=3)
        self.assertTrue(-90.0 <= turned <= 90.0)

    def test_one_kind_for_the_field_and_a_corner_piece_stays_a_corner_piece(self):
        """Every row sticker becomes the look's MAIN kind (a field is one kind, not a checker of the look's mix); a
        corner sticker (_triangle) becomes that kind's corner piece where the map has one, else stays as it was, and
        gets no tint square (it covers part of its square only)."""
        items = self.grid(0, 20000.0, 20000.0, 30.0, 2500.0, 3500.0, 6000.0) + [compact(5, 21234.0, 19876.0, 0.5)]
        sc = scenery.Scenery(make_scenery([block(items, box=(0.0, 0.0, 100000.0, 100000.0))], FB_NAMES))
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        mix = dict(self.LOOK, stickers=[("Labourage_terrefonce", 0.2), ("Paille", 0.7), ("Paille_triangle", 0.1)])
        _e, objects, _c, stamps, _n = scenery.expand_field_brush(dab, mix, sc)
        corner = [o for o in objects if (round(o.x), round(o.y)) == (21234, 19876)]
        self.assertEqual([o.type for o in corner], ["TypeWarrior/Paille_triangle"])
        self.assertTrue(all(o.type == "TypeWarrior/Paille" for o in objects if o not in corner))
        self.assertEqual(len(stamps), len(objects) - 1)
        dark = dict(self.LOOK, stickers=[("Labourage_terrefonce", 1.0)])   # the map has no Labourage_terrefonce_triangle
        objects = scenery.expand_field_brush(dab, dark, sc)[1]
        self.assertEqual([o.type for o in objects if (round(o.x), round(o.y)) == (21234, 19876)],
                         ["TypeWarrior/Labourage_triangle"])
        self.assertEqual({o.type for o in objects if (round(o.x), round(o.y)) != (21234, 19876)},
                         {"TypeWarrior/Labourage_terrefonce"})

    def test_two_fields_under_one_brush_and_none(self):
        data = self.map_data(second=True)
        sc = scenery.Scenery(data)
        dab = scenery.FieldBrush("Wheat", 28000.0, 20000.0, 9000.0, "square")
        _e, objects, copies, _s, notes = scenery.expand_field_brush(dab, self.LOOK, sc)
        self.assertEqual({abs(round(c.turn)) for c in copies}, {40, 90})   # each field turned to its own rows
        self.assertEqual(len(notes), 2)
        nothing = scenery.expand_field_brush(scenery.FieldBrush("Wheat", 50000.0, 50000.0, 3000.0), self.LOOK, sc)
        self.assertEqual(nothing[:4], ([], [], [], []))
        self.assertIn("no field under it", nothing[4][0])

    def test_a_field_bigger_than_the_source_is_laid_in_pieces(self):
        """A source 10,000 inside: field A (about 24,000 x 18,000 with its squares) in pieces 10,000 across, each crop
        still landing on A."""
        data = self.map_data()
        sc = scenery.Scenery(data)
        small = dict(self.LOOK, sources=[(80000.0, 80000.0, 120.0, 10000.0, 10000.0, 0.0, "", "")])
        _e, _o, copies, _s, _n = scenery.expand_field_brush(scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0),
                                                            small, sc)
        self.assertGreater(len(copies), 4)
        self.assertTrue(all(c.radius <= 5000.0 and c.along <= 5000.0 for c in copies))   # inside the source
        a = math.radians(30.0)
        for k in range(-12, 13):   # no point of the field in two pieces (they laid the crops twice over, 2026-10-15)
            for j in range(-10, 11):
                u, v = k * 997.0 + 13.0, j * 991.0 + 7.0
                x, y = 20000.0 + u * math.cos(a) - v * math.sin(a), 20000.0 + u * math.sin(a) + v * math.cos(a)
                self.assertLessEqual(sum(c.footprint().t2(x, y) < 1.0 for c in copies), 1, (k, j))
        laid, _n = scenery.copy_objects(data, copies, FB_DESCS)
        self.assertTrue(laid)
        a = self.field_a(sc)
        self.assertTrue(all(self.on(o, a) for o in laid))


class RoadStickers(unittest.TestCase):
    """A new road's stickers (the game's Route pieces), cut like the shipped ones and added with the objects in the
    map's own style. What the game draws from them isn't known (TESTS.md T12)."""

    def test_a_line_cut_into_pieces(self):
        pieces = scenery.road_pieces([(0.0, 0.0), (10000.0, 0.0), (10000.0, 7000.0)])
        self.assertEqual([(q.x0, q.y0, q.x1, q.y1) for q in pieces],
                         [(0.0, 0.0, 5000.0, 0.0), (5000.0, 0.0, 10000.0, 0.0), (10000.0, 0.0, 10000.0, 3500.0),
                          (10000.0, 3500.0, 10000.0, 7000.0)])
        self.assertEqual((pieces[0].hx0, pieces[0].hy0, pieces[0].hx1, pieces[0].hy1), (500.0, 0.0, -500.0, 0.0))
        close = scenery.road_pieces([(0.0, 0.0), (500.0, 0.0), (1000.0, 0.0), (6000.0, 0.0)])
        self.assertEqual([(q.x0, q.x1) for q in close], [(0.0, 6000.0)])  # a line's close points joined up

    def test_added_in_the_maps_own_style(self):
        raw = village()
        s = Scenery(raw)
        before = sorted(tuple(round(v) for v in p) for p in s.roads())
        pieces = scenery.road_pieces([(1000.0, 2500.0), (9000.0, 2500.0)])
        new, notes = add_objects(raw, [NewObject("TypeWarrior/Chene_02", 1200.0, 2600.0)] + pieces)
        after = Scenery(new)
        got = sorted(tuple(round(v) for v in p) for p in after.roads())
        mine = [p for p in got if p not in before]
        self.assertEqual(mine, [(1000, 2500, 1400, 2500, 4600, 2500, 5000, 2500),
                                (5000, 2500, 5400, 2500, 8600, 2500, 9000, 2500)])  # where they were drawn
        road_items = [it for b in after.blocks for it in b.items if it.kind == "road"]
        self.assertEqual({it.symbol for it in road_items}, {20})  # the map's own Route name
        self.assertEqual({struct.unpack_from("<3I", it.data, 48) for it in road_items} - {(3, 129958752, 1567752)},
                         {(2, 129958752, 1567752)})  # its trailing words, with its block's own count of pieces
        self.assertIn("1 object(s) added", notes[0])
        self.assertIn("2 road sticker piece(s) added", notes[1])  # road pieces go in a block of their own
        new_pieces = {(b.index, it.at) for b in after.blocks for it in b.items if it.kind == "road"
                      and (round(struct.unpack_from("<f", it.data)[0]), round(struct.unpack_from("<f", it.data, 4)[0]))
                      in {(1000, 2500), (5000, 2500)}}
        self.assertEqual(len(new_pieces), 2)
        self.assertLessEqual(new_pieces, road_pass(after))  # the road pass would reach them (the walk, not the screen)

    def test_the_close_up_road_asphalt_and_edges_along_the_line(self):
        """What draws a road up close (proven on D-Day, 2026-10-02): an asphalt sticker every gap along the line,
        turned along it, an edge sticker either side (the left one turned round), never solid."""
        objs = scenery.road_decals([(0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0)], "A", "E", gap=1500.0)
        asphalt = [(o.x, o.y, o.turn) for o in objs if o.type == "A"]
        self.assertEqual(asphalt, [(1500.0, 0.0, 0.0), (3000.0, 0.0, 0.0), (4000.0, 500.0, 90.0),
                                   (4000.0, 2000.0, 90.0)])  # the walk goes round the corner
        first = objs[:3]
        self.assertEqual([(o.type, round(o.x), round(o.y), round(o.turn)) for o in first],
                         [("A", 1500, 0, 0), ("E", 1500, 1380, 0), ("E", 1500, -1380, 180)])
        self.assertTrue(all(o.size == 2.0 and not o.solid for o in objs))
        self.assertEqual(len(scenery.road_decals([(0.0, 0.0), (4000.0, 0.0)], "A", None, gap=1500.0)), 2)  # no edges
        self.assertEqual(scenery.road_decals([(0.0, 0.0), (1000.0, 0.0)], "A", "E"), [])  # shorter than a gap

    def test_a_new_roads_path_cleared_without_touching_the_ground(self):
        """The plants and props on a new road's path go (probe 5's lane 4); its cover and movement stay."""
        from rusemod.build import cleared_woods
        areas = scenery.road_clearing([(0.0, 0.0), (6000.0, 0.0)])
        self.assertEqual([a.x for a in areas], [750.0 * k for k in range(1, 9)])
        self.assertTrue(all(a.radius == 1500.0 and a.what == ("vegetation", "prop") and a.keep_ground for a in areas))
        self.assertEqual(cleared_woods({"Test": (areas, ["mod"])}), ({}, {}))  # no wood cleared, no cover taken
        mine = [scenery.EraseArea(0.0, 0.0, 500.0)]
        self.assertIn("Test", cleared_woods({"Test": (mine, ["mod"])})[0])  # a mod's own erase area still clears

    def test_a_new_block_lists_road_pieces_for_close_view_only(self):
        piece = scenery.road_pieces([(0.0, 0.0), (4000.0, 0.0)])[0]
        style = (20, (129958752, 1567752))
        items = [moved(0, 0.0, 0.0), scenery._road_item(piece, scenery.IDENTITY, style, 1)[0], compact(0, 1.0, 2.0)]
        raw = scenery._new_block(items, (0.0, 0.0, 1.0, 1.0))
        s = Scenery(make_scenery([raw], NAMES))
        b = s.blocks[0]
        root, far_leaf, full = [struct.unpack_from("<IH", b.nodes, 8 * k) for k in range(3)]
        self.assertEqual(root[1], 2)  # the far list: the reference and the object, not the road piece
        kinds = {it.at: it.kind for it in b.items}
        self.assertEqual([kinds[a] for a in b.entries[:2]], ["child", "object"])
        self.assertEqual([kinds[a] for a in b.entries[2:]], ["child", "road", "object"])
        self.assertTrue(root[0] & scenery.ROAD_BIT and full[0] & scenery.ROAD_BIT)
        self.assertFalse(far_leaf[0] & scenery.ROAD_BIT)
        self.assertEqual(b.mask, scenery.ALL_TIERS)  # the LOD mask itself is unchanged

    def test_filed_with_the_maps_own_in_the_leaf_that_holds_them(self):
        """Two roads, one by each wood: the woods are placed twice, so the pieces are filed among the top block's own
        items (as D-Day files 25 of its own out in the open), each in the leaf of its tree whose box holds it. No block
        is added and every item the map had keeps its leaf; the nodes down to the new pieces get the road mark (not
        the far list's leaf); every piece carries its block's count; the road pass reaches each new piece and still
        the wood's own."""
        data = two_woods()
        s0 = Scenery(data)
        top0 = s0.blocks[0]
        own = {(1, it.at) for it in s0.blocks[1].items if it.kind == "road"}
        self.assertEqual(road_pass(s0), set())  # nothing yet: the top block's root has no road mark
        south = scenery.road_pieces([(1000.0, 1500.0), (9000.0, 1500.0)])
        north = scenery.road_pieces([(1000.0, 9000.0), (9000.0, 9000.0)])
        new, notes = add_objects(data, south + north)
        s = Scenery(new)
        self.assertEqual(spots(new), spots(data))  # no object moved
        self.assertEqual(len(s.blocks), 2)
        top = s.blocks[0]
        before = Counter((top0.entries[e], box) for e, box in scenery._leaf_boxes(top0).items())
        boxes = scenery._leaf_boxes(top)
        after = Counter((top.entries[e], box) for e, box in boxes.items())
        self.assertEqual(after - before, Counter({(it.at, boxes[top.entries.index(it.at)]): 1
                                                  for it in top.items if it.kind == "road"}))  # the old ones kept
        mine = [it for it in top.items if it.kind == "road"]
        self.assertEqual(len(mine), 4)
        split = struct.unpack_from("<H", top.nodes, 4)[0]
        for it in mine:
            f = struct.unpack_from("<12f", it.data)
            listed = [e for e, a in enumerate(top.entries) if a == it.at]
            self.assertEqual(len(listed), 1)  # once, for close view: not in the far list
            self.assertGreaterEqual(listed[0], split)
            x0, y0, x1, y1 = boxes[listed[0]]
            self.assertTrue(x0 <= (f[0] + f[6]) / 2 <= x1 and y0 <= (f[1] + f[7]) / 2 <= y1)
            self.assertEqual(struct.unpack_from("<I", it.data, 48)[0], 4)  # the block's count
        self.assertEqual(sorted(round(struct.unpack_from("<f", it.data, 4)[0]) for it in mine), [1500, 1500, 9000, 9000])
        nodes = [struct.unpack_from("<IH", top.nodes, 8 * k) for k in range(3)]
        self.assertEqual([bool(w & scenery.ROAD_BIT) for w, _s in nodes], [True, False, True])
        self.assertEqual([sp for _w, sp in nodes], [2, 2, 6])  # the full list's split: the south pieces before it
        self.assertEqual(road_pass(s), {(0, it.at) for it in mine} | own)
        self.assertEqual(notes, ["4 road sticker piece(s) filed with the map's own, in the leaf of a block's tree that "
                                 "holds each: the top block (4)"])

    def test_a_block_placed_once_files_the_pieces_its_leaf_holds(self):
        """A wood placed once, its box smaller than the top block's leaf: the piece goes among the wood's items, the
        wood's own piece takes the new count, and the top block's way down to the wood gets the road mark."""
        wood = block([compact(1, 0.0, 0.0), road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))],
                     box=(-5000.0, -5000.0, 5000.0, 5000.0))
        top_box = (0.0, 0.0, 40960.0, 40960.0)
        root_len = len(block([moved(0, 0, 0)], box=top_box))
        data = make_scenery([block([moved(root_len, 20000.0, 20000.0)], box=top_box), wood], NAMES)
        new, notes = add_objects(data, scenery.road_pieces([(19000.0, 21000.0), (23000.0, 21000.0)]))
        s = Scenery(new)
        self.assertEqual(len(s.blocks[0].items), 1)  # nothing filed in the top block
        pieces = [it for it in s.blocks[1].items if it.kind == "road"]
        self.assertEqual(len(pieces), 2)
        self.assertEqual({struct.unpack_from("<I", it.data, 48)[0] for it in pieces}, {2})
        self.assertEqual(tuple(round(v) for v in struct.unpack_from("<2f", pieces[1].data)), (-1000, 1000))
        self.assertEqual(road_pass(s), {(1, it.at) for it in pieces})
        self.assertIn("block 1 (1)", notes[0])

    def test_a_turned_blocks_leaf_holds_only_its_own_box(self):
        """A wood placed once, turned 45 degrees: a piece inside its box's bounds on the map but outside the turned
        box itself isn't filed in it (it goes in the top block's leaf, which does hold it)."""
        wood = block([compact(1, 0.0, 0.0), road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))],
                     box=(-5000.0, -5000.0, 5000.0, 5000.0))
        top_box = (0.0, 0.0, 40960.0, 40960.0)
        c = round(math.cos(math.pi / 4) / SCALE16)
        ref = struct.pack("<I4h4f", 0, c, -c, c, c, 20000.0, 20000.0, 0.0, 1.0)  # a child, its offset set below
        root_len = len(block([ref], box=top_box))
        ref = struct.pack("<I", root_len) + ref[4:]
        data = make_scenery([block([ref], box=top_box), wood], NAMES)
        _new, notes = add_objects(data, scenery.road_pieces([(25000.0, 26000.0), (27000.0, 26000.0)]))
        self.assertIn("the top block (1)", notes[0])

    def test_a_backwards_side_never_takes_a_piece(self):
        """M03_Italie's top block (italy_top): a road out in the open goes at the end of the full list, never on the
        full list's node's left side, which runs backwards. An entry added at that side's end went in front of the
        far-view list (a tester's build, 2026-10-03): the game would draw road pieces from far instead of the map's
        blocks, and the new objects, with no far-listed block left to wrap, were hung on a grass decal (drawn up close
        only). Now the far list keeps both references, and an object added with the road wraps one of them."""
        data = italy_top()
        top0 = Scenery(data).blocks[0]
        self.assertEqual([(lf.node, lf.side) for lf in scenery._leaves(scenery._tree(top0), 4, top0.bbox)], [(2, "R")])
        pieces = scenery.road_pieces([(15000.0, 20000.0), (19000.0, 20000.0)])
        new, notes = add_objects(data, [NewObject("TypeWarrior/Chene_02", 16000.0, 21000.0)] + pieces)
        s = Scenery(new)
        top = s.blocks[0]
        kinds = {it.at: it.kind for it in top.items}
        self.assertEqual([kinds[a] for a in top.entries[:2]], ["child", "child"])  # the far list as it was
        self.assertEqual(struct.unpack_from("<H", top.nodes, 4)[0], 2)
        self.assertEqual(len(scenery._far_children(s)), 2)
        self.assertEqual([kinds[a] for a in top.entries[4:]], ["road"] * len(pieces))  # the full list's end
        self.assertIn("the top block (1)", notes[0])
        self.assertIn("1 object(s) added in a new block with block 1 (drawn from far", notes[1])
        self.assertNotIn("hung on", " ".join(notes))

    def test_between_carriers_that_hold_as_many_the_nearest(self):
        """In a top block like M03_Italie's every far-listed reference's boxes are the whole map, so each holds a new
        object as well as the other: it goes on the one whose block is nearest it (the first one, 13.8 km off a test
        road, used to take everything)."""
        new, _notes = add_objects(italy_top(), [NewObject("TypeWarrior/Chene_02", 29000.0, 29000.0)])
        s = Scenery(new)
        refs = {round(it.matrix()[3]): s._by_offset[it.child_offset] for it in s.blocks[0].items if it.kind == "child"}
        self.assertEqual(refs, {5000: 2, 30000: 1})  # the north wood's reference now goes through the new block

    def test_a_far_view_list_that_would_change_stops_the_build(self):
        """Whatever leaf is asked for, a block's far-view list never changes: an entry that would land in it stops
        the build with a message (the backwards side, forced back in here, is the case that did it)."""
        from unittest import mock
        top0 = Scenery(italy_top()).blocks[0]
        piece = scenery._road_item(scenery.road_pieces([(15000.0, 20000.0), (19000.0, 20000.0)])[0],
                                   scenery.IDENTITY, (20, (129958752, 1567752)), 1)[0]
        backwards = scenery._Leaf(2, "L", 2, 0, top0.bbox, [(0, "R"), (2, "L")])
        with mock.patch.object(scenery, "_leaves", return_value=[backwards]):
            with self.assertRaisesRegex(SceneryError, "far-view list"):
                scenery._grown(top0, [((2, "L"), piece)])

    def test_a_split_moves_when_its_left_side_or_all_of_it_comes_after(self):
        """The root splits 4 entries into two nodes of two leaves each: an entry added to the first node's right leaf
        moves the root's split (its left side holds it) and the second node's (it comes after); one added to the
        second node's left leaf moves that node's split only."""
        nodes = [[0x1F << 20 | 2 << 2, 2, 0x80, 0x80], [0xC0000000, 1, 0x80, 0x80], [0xC0000000, 3, 0x80, 0x80]]
        first = [list(n) for n in nodes]
        scenery._one_more(first, [(0, "L"), (1, "R")])
        self.assertEqual([n[1] for n in first], [3, 1, 4])
        second = [list(n) for n in nodes]
        scenery._one_more(second, [(0, "R"), (2, "L")])
        self.assertEqual([n[1] for n in second], [2, 1, 4])

    def test_a_new_object_is_drawn_at_every_distance(self):
        """The game walks a cell of the scenery's grids only when its record says it holds something, finds a
        block's items through the top block's leaf boxes, and turns an object by its word's variation bits and drops
        it at low detail by its tier bits. A new object: its cells marked at all three levels, its carrier the
        reference whose far and full boxes hold it, and no tier or variation copied from the map's own items."""
        data = two_woods()
        new, notes = add_objects(data, [NewObject("TypeWarrior/Chene_02", 3000.0, 9000.0)])  # by the north wood
        s = Scenery(new)
        top = s.blocks[0]
        north = next(it for it in top.items if it.kind == "child" and round(it.matrix()[7]) == 8000)
        wrapper = s.blocks[s._by_offset[north.child_offset]]
        self.assertIn(1, [it.symbol for it in wrapper.items if it.kind == "object"])  # on the north reference
        for level, (size, rec) in enumerate(zip(scenery.GRID_CELL, scenery.GRID_RECORD)):
            w, h = s.grid_dims[2 * level], s.grid_dims[2 * level + 1]
            at = s.grids[level][0] + (int(3000 // size) * h + int(9000 // size)) * rec
            self.assertTrue(scenery._cell_walked(new[at:at + rec], level), level)
            self.assertFalse(scenery._cell_walked(data[at:at + rec], level), level)  # empty before
        self.assertIn("cell(s) of the scenery's grids marked", notes[-1])
        oak = next(it for it in wrapper.items if it.kind == "object")
        self.assertEqual((oak.word >> 26) & 0xF, 0)  # tier 0, no variation, whatever the map's own oaks carry
        with self.assertRaisesRegex(SceneryEditError, "outside the map's scenery grid"):
            add_objects(data, [NewObject("TypeWarrior/Chene_02", 50000.0, 9000.0)])
        _new, notes = add_objects(data, [NewObject("TypeWarrior/Chene_02", 3000.0, 5000.0)])  # between the boxes:
        self.assertNotIn("no box", " ".join(notes))  # its cell meets the south one, so the game walks it there
        before = scenery._leaf_boxes(Scenery(data).blocks[0])
        new, notes = add_objects(data, [NewObject("TypeWarrior/Chene_02", 30000.0, 30000.0)])  # out in the open,
        self.assertNotIn("no box", " ".join(notes))  # past the top block's own box (10,000 across): it grows too
        self.assertIn("draw tree widened", " ".join(notes))
        top = Scenery(new).blocks[0]
        self.assertTrue(top.bbox[2] >= 30720.0 and top.bbox[3] >= 30720.0, top.bbox)  # the object's whole cell
        after = scenery._leaf_boxes(top)
        for e, b in before.items():
            a = after[e]
            self.assertTrue(a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3], (e, b, a))
        self.assertTrue(any(a[0] <= 30000.0 <= a[2] and a[1] <= 30000.0 <= a[3] for e, a in after.items() if e >= 2))

    def test_open_ground_widens_one_box_and_keeps_every_other(self):
        """Objects in no box of the top block's tree (a painted field away from the map's own scenery): the leaf box
        of the reference whose block lies nearest them (the east wood: ~17 km from their middle, the west ~25 km;
        before 2026-10-15 the bigger box, the west's, and a farm hung 5.6 km off was never drawn) is widened
        over their cells, every entry's leaf box still holds what it held, and they go in a block wrapping that
        reference, so the game's walk reaches them."""
        data = open_fields()
        top0 = Scenery(data).blocks[0]
        before = scenery._leaf_boxes(top0)
        self.assertEqual(len(scenery._carriers(Scenery(data), [NewObject("TypeWarrior/Chene_02", 20000.0, 20000.0)])[1]),
                         1)  # out in the open: in no box
        field = [NewObject("TypeWarrior/Chene_02", 20000.0, 20000.0), NewObject("TypeWarrior/Chene_02", 25000.0, 12000.0)]
        new, notes = add_objects(data, field)
        self.assertNotIn("no box", " ".join(notes))
        self.assertIn("draw tree widened", " ".join(notes))
        s = Scenery(new)
        top = s.blocks[0]
        after = scenery._leaf_boxes(top)
        for e, b in before.items():
            a = after[e]
            self.assertTrue(a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3], (e, b, a))
        east = next(it for it in top.items if it.kind == "child" and round(it.matrix()[3]) == 38000)
        e = top.entries.index(east.at, 2)  # its entry in the full list
        cell = scenery.GRID_CELL[2]
        for o in field:
            x0, y0 = math.floor(o.x / cell) * cell, math.floor(o.y / cell) * cell
            b = after[e]
            self.assertTrue(b[0] <= x0 and b[1] <= y0 and b[2] >= x0 + cell and b[3] >= y0 + cell, b)
        wrapper = s.blocks[s._by_offset[east.child_offset]]
        self.assertEqual(sum(1 for it in wrapper.items if it.kind == "object"), 2)

    def test_a_new_block_finds_each_item_through_its_tree(self):
        """A new block's lists are search trees like the shipped blocks': leaves of 1 to 4 entries, each item in the
        leaf box of its entry in both lists (the far list without road pieces), the far list's nodes marked far only."""
        rnd = random.Random(7)
        places = [(rnd.uniform(0.0, 9000.0), rnd.uniform(0.0, 5000.0)) for _ in range(300)]
        items = [compact(1, x, y) for x, y in places]
        boxes = [(x - 50.0, y - 50.0, x + 50.0, y + 50.0) for x, y in places]
        raw = scenery._new_block(items, (-50.0, -50.0, 9050.0, 5050.0), boxes)
        b = Scenery(make_scenery([raw], NAMES)).blocks[0]
        nodes = scenery._tree(b)
        split0 = nodes[0][1]
        self.assertEqual((split0, len(b.entries)), (300, 600))
        leaves = scenery._leaf_boxes(b)
        self.assertEqual(set(leaves), set(range(600)))
        by_at = {it.at: it for it in b.items}
        for e, at in enumerate(b.entries):
            m = by_at[at].matrix()
            x0, y0, x1, y1 = leaves[e]
            self.assertTrue(x0 <= m[3] <= x1 and y0 <= m[7] <= y1, (e, m[3], m[7], leaves[e]))
        self.assertEqual(sorted(b.entries[:300]), sorted(b.entries[300:]))
        right = (nodes[0][0] & 0xFFFFF) >> 2
        self.assertTrue(all((w >> 20) & 0x3F == 0x08 for w, *_ in nodes[1:right]))
        self.assertTrue(all((w >> 20) & 0x3F == 0x17 for w, *_ in nodes[right:]))  # no road piece, no block placed
        sizes, todo = [], [(0, 0, 600)]
        while todo:
            k, lo, hi = todo.pop()
            w, sp = nodes[k][:2]
            for leaf, a, z, nxt in ((w & 0x40000000, lo, sp, k + 1), (w & 0x80000000, sp, hi, k + ((w & 0xFFFFF) >> 2))):
                if leaf:
                    sizes.append(z - a)
                else:
                    todo.append((nxt, a, z))
        self.assertTrue(sizes and all(1 <= n <= scenery.LEAF_MOST for n in sizes), Counter(sizes))

    def test_more_objects_than_a_block_holds_go_in_blocks_wrapping_each_other(self):
        from unittest import mock
        data = open_fields()
        near = [NewObject("TypeWarrior/Chene_02", 1500.0 + 20.0 * k, 1500.0 + 15.0 * (k % 7)) for k in range(120)]
        with mock.patch.object(scenery, "BLOCK_MOST", 50):
            new, notes = add_objects(data, near)
        self.assertEqual(sum("added in a new block" in n for n in notes), 4)  # halved till each fits: 4 of 30
        s = Scenery(new)
        placed = [(round(m[3]) + 2000, round(m[7]) + 1000)  # in the west wood reference's frame (2000, 1000)
                  for bl in s.blocks[1:] if tuple(bl.bbox) != (-100.0, -100.0, 100.0, 100.0)
                  for it in bl.items if it.kind == "object" for m in [it.matrix()]]
        self.assertEqual(sorted(placed), sorted((round(o.x), round(o.y)) for o in near))  # each once

    def test_the_maps_own_tier_and_turn_bits_are_not_copied(self):
        wood = block([struct.pack("<I4h4f", 0x80000000 | 0x34000000 | 1 << 4, *[round(1 / SCALE16), 0, 0,
                                                                                  round(1 / SCALE16)], 0.0, 0.0, 0.0, 1.0)])
        root_len = len(block([moved(0, 0, 0)], far=True))
        data = make_scenery([block([moved(root_len, 1000.0, 1000.0)], far=True), wood], NAMES)
        self.assertEqual((Scenery(data).blocks[1].items[0].word >> 26) & 0xF, 0xD)  # tier 1, variation 3
        new, _notes = add_objects(data, [NewObject("TypeWarrior/Chene_02", 1200.0, 1100.0)])
        mine = [it for b in Scenery(new).blocks for it in b.items
                if it.kind == "object" and it.symbol == 1 and it.tform != scenery.T_IDENTITY]
        self.assertTrue(any(((it.word >> 26) & 0xF) == 0 for it in mine), [hex(it.word) for it in mine])

    def test_a_map_without_stickers_gets_none(self):
        raw = make_scenery([block([compact(0, 100.0, 100.0)])], NAMES)
        new, notes = add_objects(raw, scenery.road_pieces([(0.0, 0.0), (8000.0, 0.0)]))
        self.assertEqual((new, notes), (raw, ["this map has no road stickers to copy: its new roads show from afar only"]))


class TakingOutRoads(unittest.TestCase):
    """roads.toml take_out = ["roads"]: the map's own road pieces out of its scenery, everything else where it was."""

    def test_every_road_piece_goes_and_the_objects_stay(self):
        raw = two_woods()
        before = Scenery(raw)
        self.assertEqual(len(before.roads()), 2)   # the wood's piece, placed twice
        new, notes = scenery.take_out_road_pieces(raw)
        after = Scenery(new)                       # (its sum written again: it reads)
        self.assertEqual(after.roads(), [])
        self.assertEqual(notes, ["1 road piece(s) taken out (the roads drawn from far)"])
        self.assertEqual(sorted((sym, round(m[3]), round(m[7])) for sym, m in after.walk()),
                         sorted((sym, round(m[3]), round(m[7])) for sym, m in before.walk()))  # same places
        self.assertEqual(len(after.blocks), len(before.blocks))
        self.assertLess(len(new), len(raw))
        self.assertEqual(scenery.take_out_road_pieces(new), (new, []))   # none left: the same bytes

    def test_the_road_stickers_are_the_road_decals(self):
        def d(name, category, group="decal"):
            return scenery.Descriptor("TypeWarrior/" + name, "TSceneryDescriptorSticker", category, group, None, "")
        descs = {x.name: x for x in (d("Route_Bitume", "STICKERS/Allemagne"), d("Chemin_Terre_culture", "STICKERS"),
                                     d("Bitume_Base", "STICKERS/Tunisie/Roads"), d("TirBunker_Chemin_traces", "STICKERS"),
                                     d("Cratere", "STICKERS"), d("German_Canon_Fact_Cheminee", "Props", "prop"))}
        self.assertEqual(scenery.road_stickers(list(descs) + ["TypeWarrior/Unknown_Route"], descs),
                         ["TypeWarrior/Route_Bitume", "TypeWarrior/Chemin_Terre_culture", "TypeWarrior/Bitume_Base"])


class Sinking(unittest.TestCase):
    """An object the map ships, sunk out of sight where it's stored (a bridge a new road replaces)."""

    def test_objects_placed_once(self):
        s = Scenery(village())
        got = [(bi, it.at, round(m[3]), round(m[7])) for bi, it, m in s.objects_once()]
        self.assertEqual(got, [(0, 0, 1000, 2000)])  # the hall; the oaks' block is placed twice

    def test_sunk_in_place(self):
        raw = village()
        s = Scenery(raw)
        hall = next(it for it in s.blocks[0].items if it.kind == "object")
        new, notes = bury_objects(raw, [(0, hall.at)])
        self.assertEqual(len(new), len(raw))
        self.assertEqual(notes, ["1 object(s) sunk out of sight"])
        again = Scenery(new)  # the sum was written again
        m = next(m for sym, m in again.walk() if sym == 0)
        x, y, turn, size = placement(m)
        self.assertEqual((x, y), (1000.0, 2000.0))
        self.assertAlmostEqual(turn, math.pi / 2, places=2)
        self.assertAlmostEqual(size, SHRINK, places=3)
        self.assertEqual(m[11], -BURY)
        self.assertEqual(again.raw[16:][:len(raw) - 16].count(b"\0"), new[16:].count(b"\0"))  # nothing else moved
        oaks = [it for it in s.blocks[1].items if it.kind == "object"]
        moved_oak = next(it for it in oaks if it.tform == 2)
        new2, _ = bury_objects(raw, [(1, moved_oak.at)])
        got = sorted(round(m[11]) for sym, m in Scenery(new2).walk() if sym == 1)
        self.assertEqual(got, [-BURY, -BURY, 0, 0])  # a moved object: sunk wherever its block is placed
        self.assertEqual(bury_objects(raw, []), (raw, []))

    def test_refusals(self):
        raw = village()
        s = Scenery(raw)
        bare = next(it for it in s.blocks[1].items if it.tform == 1)
        with self.assertRaisesRegex(SceneryEditError, "without a transform"):
            bury_objects(raw, [(1, bare.at)])
        with self.assertRaisesRegex(SceneryEditError, "no block 9"):
            bury_objects(raw, [(9, 0)])
        with self.assertRaisesRegex(SceneryEditError, "no object at 999"):
            bury_objects(raw, [(0, 999)])


OAK = 0x80000000 | 1 << 4
E_NAMES = ["TypeWarrior/MairieNormande", "TypeWarrior/Chene_02", "TypeWarrior/Pont_Normandie"]
E_KINDS = {0: "building", 1: "vegetation", 2: "building"}


def tree_top(items, far):
    """A top block over `items` with a three-node tree: the root splits the far list (the items at `far`, listed
    first) from the full list, whose node splits its first two items from the rest."""
    offsets, pos = [], 0
    for it in items:
        offsets.append(pos)
        pos += len(it)
    entries = [offsets[i] for i in far] + offsets
    f = len(far)
    nodes = (struct.pack("<IHBB", 0x1F << 20 | 2 << 2, f, 0xFF, 0)
             + struct.pack("<IHBB", 0xC0000000 | 0x08 << 20, f, 0xFF, 0)
             + struct.pack("<IHBB", 0xC0000000 | 0x17 << 20 | 1, f + 2, 0x80, 0x80))
    head = struct.pack("<II4f", 0x80000000 | len(entries), 3, 0.0, 0.0, 20000.0, 20000.0) + bytes(8)
    return head + struct.pack(f"<{len(entries)}I", *entries) + nodes + b"".join(items)


def forest(patch_road=False):
    """Block 2, a patch: three oaks in a row, 100 apart (and a road piece with `patch_road`). Block 1, a wood: a road
    piece and the patch twice, at (0, 0) and (0, 1000). Block 0: a town hall at (5000, 5000), a bridge at (6000,
    6000) and the wood twice, at (0, 0) and (10000, 0), both listed for far view. So each oak is on the map 4 times."""
    patch = block([moved(OAK, 0, 0), moved(OAK, 100, 0), moved(OAK, 200, 0)]
                  + ([road((0.0, 50.0), (5.0, 0.0), (50.0, 50.0), (-5.0, 0.0))] if patch_road else []))
    piece = road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))

    def wood(at):
        return block([piece, moved(at, 0, 0), moved(at, 0, 1000)])

    def top(at):
        return tree_top([compact(0, 5000.0, 5000.0), moved(0x80000000 | 2 << 4, 6000, 6000), moved(at, 0, 0),
                         moved(at, 10000, 0)], [2, 3])
    n0 = len(top(0))
    n1 = len(wood(0))
    return make_scenery([top(n0), wood(n0 + n1), patch], E_NAMES)


def leaves(s, bi=0):
    """Each item of block `bi` (its kind, name and transform: a reference's offset may move) -> the boxes of the
    tree's leaves that list it."""
    b = s.blocks[bi]
    boxes = scenery._leaf_boxes(b)
    by_at = {it.at: (it.kind, it.symbol if it.kind == "object" else None, it.data) for it in b.items}
    out = {}
    for e, at in enumerate(b.entries):
        out.setdefault(by_at[at], []).append(boxes[e])
    return {k: sorted(v) for k, v in out.items()}


class Erasing(unittest.TestCase):
    """A mod's erase areas: the map's own scenery taken out where they lie, shared blocks copied for that spot."""

    def check(self, raw, new):
        """What every erase keeps: the file reads back, each reference points forward to a block's start, every block
        is placed (one top), the roads, the grids and the names stay."""
        s, t = Scenery(raw), Scenery(new)
        for b in t.blocks:
            for it in b.items:
                if it.kind == "child":
                    self.assertGreater(t._by_offset[it.child_offset], b.index)
        self.assertEqual(t.roots(), [0])
        self.assertEqual(sorted(t.roads()), sorted(s.roads()))
        self.assertEqual(new[t.grids[0][0]:], raw[s.grids[0][0]:])
        self.assertEqual(t.names, s.names)
        return t

    def test_many_areas_take_the_same_with_the_grid(self):
        """A new road's clearing makes thousands of circles: past 64 they're looked up on a grid, which must take
        exactly what testing every circle takes."""
        raw = village()
        areas = [scenery.EraseArea(5050.0, 0.0, 100.0)] + [scenery.EraseArea(200000.0 + k * 3000.0, 0.0, 1500.0)
                                                           for k in range(70)] + [scenery.EraseArea(5000.0, 9000.0, 10.0)]
        kinds = {i: "vegetation" for i, n in enumerate(Scenery(raw).names) if "Chene" in n}
        fast = scenery.erase_objects(raw, areas, kinds)[0]  # 72 areas: the grid
        slow = scenery.erase_objects(raw, areas[:64], kinds)[0]  # at most 64 at a time: every circle tested
        slow = scenery.erase_objects(slow, areas[64:], kinds)[0]
        self.assertEqual(spots(fast), spots(slow))
        self.assertEqual(spots(raw) - spots(fast), Counter({(1, 5000.0, 0.0): 1, (1, 5100.0, 0.0): 1,
                                                            (1, 5000.0, 9000.0): 1}))
        g = scenery._AreaGrid([(a, set()) for a in areas])
        near = [p[0] for p in g.query(5000.0, 0.0, 5000.0, 0.0)]  # candidates: the circles of that cell only
        self.assertEqual(near, [areas[0], areas[-1]])
        self.assertEqual(g.query(-1e9, -1e9, 1e9, 1e9), g.pairs)  # a huge box: the whole list

    def test_an_area_over_many_cells_is_found_as_a_small_one_is(self):
        """Map Paint's clearing by size reaches a kilometre past its strokes (136 of those filled 2.3 million cells
        on M04_Cotentin): an area over more than _AreaGrid.BIG cells is kept by the span of cells it covers, and a
        query finds it exactly when its cells meet the query's, in the areas' order, like the ones kept cell by cell."""
        rng = random.Random(4)
        pairs = [(scenery.EraseArea(rng.uniform(-2e6, 2e6), rng.uniform(-2e6, 2e6),
                                    rng.choice((2e4, 3e5, 2e6)) * rng.random() + 1.0,
                                    shape=rng.choice(("round", "square", "line")), x2=rng.uniform(-2e6, 2e6),
                                    y2=rng.uniform(-2e6, 2e6)), set()) for _ in range(120)]
        g = scenery._AreaGrid(pairs)
        self.assertTrue(g.big)                                # some are kept by their span,
        self.assertLess(len(g.big), len(pairs))               # some cell by cell
        c = g.cell

        def cells(x0, y0, x1, y1):
            return int(x0 // c), int(y0 // c), int(x1 // c), int(y1 // c)
        for _ in range(400):
            x, y = rng.uniform(-2.5e6, 2.5e6), rng.uniform(-2.5e6, 2.5e6)
            w, h = rng.choice((0.0, 1e3, 5e4)), rng.choice((0.0, 1e3, 5e4))
            qx0, qy0, qx1, qy1 = cells(x, y, x + w, y + h)
            want = []
            for p in pairs:
                ax0, ay0, ax1, ay1 = cells(*p[0].box())
                if ax0 <= qx1 and qx0 <= ax1 and ay0 <= qy1 and qy0 <= ay1:
                    want.append(p)
            self.assertEqual([id(p) for p in g.query(x, y, x + w, y + h)], [id(p) for p in want])

    def test_an_area_a_placement_lies_well_inside_takes_what_testing_each_object_takes(self):
        """Most of a big map erased (the owner's M04_Cotentin, 2026-10-04): an area a placement lies inside with room
        to spare (scenery._room) takes the objects of its names under it at once. The same file, notes and counts as
        with every object tested (no room: no area is ever sure, and with a second area of other names over the wood
        the erase tests each oak), for each shape and by size, beside a wood only one oak of which goes."""
        from unittest import mock
        raw = forest()
        reach = {"TypeWarrior/Chene_02": 50.0}
        hall = scenery.EraseArea(100.0, 500.0, 2500.0, what=(), types=("TypeWarrior/MairieNormande",))  # over the
        part = scenery.EraseArea(10100.0, 0.0, 50.0)   # first wood too, taking no oak; one oak of the second wood
        over = {  # each holds the first wood whole (its oaks at x 0, 100, 200 and y 0, 1000), far inside it
            "round": scenery.EraseArea(100.0, 500.0, 3000.0),
            "square": scenery.EraseArea(100.0, 500.0, 3000.0, shape="square", dx=1.0, dy=0.3),
            "line": scenery.EraseArea(-2000.0, 500.0, 3000.0, shape="line", x2=2000.0, y2=500.0),
            "by size": scenery.EraseArea(100.0, 500.0, 3000.0, by_size=True),
        }
        real_sure, real_takes = scenery._sure_test, scenery._takes_test
        gone = Counter({(1, float(x), float(y)): 1 for x in (0, 100, 200) for y in (0, 1000)})
        gone[(1, 10100.0, 0.0)] = 1
        for name, area in over.items():
            sure, tested = [], []

            def counted_sure(a, by_size, reach, sure=sure):
                inside = real_sure(a, by_size, reach)
                if inside is None:
                    return None

                def asked(*box):
                    sure.append(inside(*box))
                    return sure[-1]
                return asked

            def counted_takes(a, by_size, tested=tested):
                by_reach, test = real_takes(a, by_size)

                def asked(*args):
                    tested.append(a)
                    return test(*args)
                return by_reach, asked
            areas = [area, hall, part]
            with mock.patch.object(scenery, "_sure_test", counted_sure), \
                    mock.patch.object(scenery, "_takes_test", counted_takes):
                fast = scenery.erase_objects(raw, areas, E_KINDS, {2}, sizes=reach)
            self.assertIn(True, sure, name)             # the area was sure for the first wood,
            self.assertNotIn(area, tested, name)        # so none of its oaks was asked about
            with mock.patch.object(scenery, "_room", lambda *a: None), \
                    mock.patch.object(scenery, "_takes_test", counted_takes):
                del tested[:]
                slow = scenery.erase_objects(raw, areas, E_KINDS, {2}, sizes=reach)
            self.assertGreaterEqual(tested.count(area), 6, name)  # each of the wood's six oaks tested
            self.assertEqual(fast, slow, name)
            self.assertEqual(spots(raw) - spots(fast[0]), gone, name)
            self.check(raw, fast[0])

    def test_the_areas_questions_made_once_answer_as_the_areas_do(self):
        """An erase over most of a big map asks its areas about millions of objects, so each area's questions are made
        once as small functions (scenery._takes_test, _meets_test, _t2_test). They answer exactly as EraseArea.contains
        and .meets and Footprint.t2 do (the same True or False, the same float, the same refusal) for seeded random
        areas of every shape: points on and about their edges, corners and ends, zero sizes, huge and tiny numbers,
        infinities and NaN."""
        rng = random.Random(20261004)
        odd = [0.0, -0.0, 1e-300, -1e-300, 1e300, -1e300, float("inf"), float("-inf"), float("nan"), 1e-160, 5e-324]

        def num(scale=1e6):
            r = rng.random()
            if r < 0.03:
                return rng.choice(odd)
            if r < 0.1:
                return float(rng.randint(-5, 5)) * scale / 4
            return rng.uniform(-scale, scale)

        def outcome(f, *args):
            try:
                got = f(*args)
            except Exception as exc:  # noqa: BLE001 - a refusal must be the same refusal
                return "raised", type(exc).__name__, str(exc)
            return "ok", type(got).__name__, struct.pack("<d", got) if isinstance(got, float) else got

        def area():
            shape = rng.choice(("round", "square", "line", "blob"))
            r = rng.random()
            radius = rng.choice(odd) if r < 0.03 else (0.0 if r < 0.05 else abs(num()) + (0.0 if r < 0.1 else 1.0))
            kw = {}
            if shape == "square":
                kw = {"dx": num(1.0) if rng.random() < 0.9 else 0.0, "dy": num(1.0) if rng.random() < 0.9 else 0.0}
            if shape == "line":
                kw = {"x2": num(), "y2": num()} if rng.random() < 0.9 else {"x2": 0.0, "y2": 0.0}
            return scenery.EraseArea(num(), num(), radius, shape=shape, by_size=True, **kw)

        def near_points(a, f):  # on and about the area's edge, corners, ends and middle
            pts = [(a.x, a.y), (a.x + a.radius, a.y), (a.x, a.y - a.radius), (a.x2, a.y2)]
            if f.shape == "square":
                pts += f.corners()
            bx0, bx1, by0, by1 = f.box()
            pts += [(bx0, by0), (bx1, by1), (bx0, by1), (bx1, by0)]
            out = []
            for x, y in pts:
                out.append((x, y))
                out.append((math.nextafter(x, math.inf), math.nextafter(y, -math.inf)))
                out.append((x + rng.uniform(-1, 1) * a.radius * 0.01, y + rng.uniform(-1, 1) * a.radius * 0.01))
            return out + [(num(), num()) for _ in range(6)]
        asked = 0
        for _ in range(250):
            a = area()
            f = a.footprint()
            meets, t2 = scenery._meets_test(a), scenery._t2_test(f)
            plain, sized = scenery._takes_test(a, False)[1], scenery._takes_test(a, True)[1]

            def old_sized(x, y, rs, a=a, f=f):  # erase_plan's own sum for an area by size, as it was
                r = a.radius + rs
                return f.t2(x, y) * a.radius * a.radius <= r * r
            pts = near_points(a, f)
            for x, y in pts:
                rs = rng.choice((0.0, abs(num(1e5)), rng.choice(odd)))
                self.assertEqual(outcome(plain, x, y), outcome(a.contains, x, y), (a, x, y))
                self.assertEqual(outcome(t2, x, y), outcome(f.t2, x, y), (a, x, y))
                self.assertEqual(outcome(sized, x, y, rs), outcome(old_sized, x, y, rs), (a, x, y, rs))
                for p, q in pts[:6]:
                    for box in ((min(x, p), min(y, q), max(x, p), max(y, q)), (x, y, p, q), (x, y, x, y)):
                        self.assertEqual(outcome(meets, *box), outcome(a.meets, *box), (a, box))
                        asked += 1
        self.assertGreater(asked, 50000)

    def test_a_turned_square_and_a_line_erase_what_they_hold(self):
        """The brush types (2026-10-03): an erase area can be a square turned any way or a line; it takes what stands
        inside it, as a circle does, and is read and written back."""
        raw = village()
        kinds = {i: "vegetation" for i, n in enumerate(Scenery(raw).names) if "Chene" in n}
        two = Counter({(1, 5000.0, 0.0): 1, (1, 5100.0, 0.0): 1})
        for area in (scenery.EraseArea(5050.0, 0.0, 60.0, shape="square", dx=1.0, dy=1.0),
                     scenery.EraseArea(4950.0, 0.0, 10.0, shape="line", x2=5150.0, y2=0.0)):
            new = scenery.erase_objects(raw, [area], kinds)[0]
            self.assertEqual(spots(raw) - spots(new), two, area.shape)
        beside = scenery.EraseArea(4950.0, 500.0, 10.0, shape="line", x2=5150.0, y2=500.0)
        self.assertEqual(scenery.erase_objects(raw, [beside], kinds)[0], raw)
        import tomllib
        areas = [scenery.EraseArea(1.0, 2.0, 3.0, shape="square", dx=0.6, dy=0.8),
                 scenery.EraseArea(1.0, 2.0, 3.0, ("prop",), shape="line", x2=4.0, y2=5.0)]
        back = scenery.parse_erase(tomllib.loads(scenery.objects_toml([], erase=areas))["erase"])
        self.assertEqual(back, areas)
        with self.assertRaisesRegex(scenery.SceneryEditError, "a line needs x2 and y2"):
            scenery.parse_erase([{"x": 1, "y": 2, "radius": 3, "shape": "line"}])

    def test_by_size_an_area_takes_what_reaches_into_it(self):
        """Map Paint's clearing (TESTS.md T26): a sticker or a plant centred outside a painted patch still covers its
        edge, so an area by size takes whatever reaches in: its type's reach times the size it is placed at."""
        raw = village()
        kinds = {i: "vegetation" for i, n in enumerate(Scenery(raw).names) if "Chene" in n}
        reach = {"TypeWarrior/Chene_02": 50.0}
        for area in (scenery.EraseArea(5200.0, 0.0, 60.0, by_size=True),  # the oak at 5100 is 100 off: 60 + 50 reach it
                     scenery.EraseArea(5200.0, 0.0, 60.0, shape="square", by_size=True),
                     scenery.EraseArea(5200.0, -100.0, 60.0, shape="line", x2=5200.0, y2=100.0, by_size=True)):
            new = scenery.erase_objects(raw, [area], kinds, sizes=reach)[0]
            self.assertEqual(spots(raw) - spots(new), Counter({(1, 5100.0, 0.0): 1}), area.shape)  # not the one at 5000
        plain = scenery.EraseArea(5200.0, 0.0, 60.0)
        self.assertEqual(scenery.erase_objects(raw, [plain], kinds, sizes=reach)[0], raw)          # by its middle only
        by_size = scenery.EraseArea(5200.0, 0.0, 60.0, by_size=True)
        self.assertEqual(scenery.erase_objects(raw, [by_size], kinds)[0], raw)                     # no sizes known

    def test_a_mask_takes_what_reaches_into_it_however_its_shape_runs(self):
        """The filled riverbeds of a reshaped map (rusemod.mend.Filled.touches): the area's square only narrows the
        search; the mask, asked with each object's place and reach, says what goes."""
        raw = village()
        kinds = {i: "vegetation" for i, n in enumerate(Scenery(raw).names) if "Chene" in n}
        reach = {"TypeWarrior/Chene_02": 50.0}
        asked = []

        def mask(x, y, r):  # a strip at x 5140..5160: the oak at 5100 reaches it (50), the one at 5000 doesn't
            asked.append((x, y, r))
            return x + r >= 5140.0 and x - r <= 5160.0
        area = scenery.EraseArea(5100.0, 0.0, 400.0, shape="square", by_size=True, mask=mask)
        new = scenery.erase_objects(raw, [area], kinds, sizes=reach)[0]
        self.assertEqual(spots(raw) - spots(new), Counter({(1, 5100.0, 0.0): 1}))
        self.assertIn((5100.0, 0.0, 50.0), asked)  # each with its own reach

    def test_a_shared_patch_is_copied_for_the_erased_spot(self):
        raw = forest()
        new, notes, by = scenery.erase_objects(raw, [scenery.EraseArea(10100.0, 0.0, 50.0)], E_KINDS, {2})
        t = self.check(raw, new)
        self.assertEqual(spots(raw) - spots(new), Counter({(1, 10100.0, 0.0): 1}))  # that oak only
        self.assertEqual(spots(new) - spots(raw), Counter())
        self.assertEqual(by, {"vegetation": 1})
        self.assertEqual(len(t.blocks), 5)  # the wood and its patch copied once each, before the blocks they copy
        self.assertEqual(t.placings()[0], [1, 1, 1, 1, 3])
        self.assertEqual(notes[0], "1 object(s) erased in 1 area(s): 1 vegetation")
        self.assertIn("2 shared block(s) copied for the erased spots", notes[1])
        self.assertEqual(leaves(t), leaves(Scenery(raw)))  # the top block's tree finds what it found
        self.assertEqual(t.blocks[0].nodes, Scenery(raw).blocks[0].nodes)

    def test_buildings_and_bridges_stay_unless_named(self):
        raw = forest()
        around = (5500.0, 5500.0, 1000.0)
        new, notes, by = scenery.erase_objects(raw, [scenery.EraseArea(*around)], E_KINDS, {2})
        self.assertEqual((new, by), (raw, {}))
        self.assertIn("cover nothing they may remove", notes[0])
        new, _notes, by = scenery.erase_objects(raw, [scenery.EraseArea(*around, what=("building",))], E_KINDS, {2})
        self.assertEqual(spots(raw) - spots(new), Counter({(0, 5000.0, 5000.0): 1}))  # the hall, not the bridge
        self.assertEqual(by, {"building": 1})
        new, _notes, by = scenery.erase_objects(
            raw, [scenery.EraseArea(*around, what=(), types=("TypeWarrior/Pont_Normandie",))], E_KINDS, {2})
        self.assertEqual(spots(raw) - spots(new), Counter({(2, 6000.0, 6000.0): 1}))
        self.assertEqual(by, {"bridge": 1})
        _new, notes, _by = scenery.erase_objects(raw, [scenery.EraseArea(*around, types=("TypeWarrior/Nope",))],
                                                 E_KINDS, {2})
        self.assertIn("TypeWarrior/Nope: not on this map, so the erase areas take none of it", notes)

    def test_several_areas_in_one_go(self):
        raw = forest()
        areas = [scenery.EraseArea(0.0, 0.0, 10.0), scenery.EraseArea(10200.0, 1000.0, 10.0),
                 scenery.EraseArea(5000.0, 5000.0, 10.0, ("building",))]
        new, notes, by = scenery.erase_objects(raw, areas, E_KINDS, {2})
        self.check(raw, new)
        self.assertEqual(spots(raw) - spots(new), Counter({(1, 0.0, 0.0): 1, (1, 10200.0, 1000.0): 1,
                                                           (0, 5000.0, 5000.0): 1}))
        self.assertEqual(by, {"vegetation": 2, "building": 1})
        self.assertEqual(notes[0], "3 object(s) erased in 3 area(s): 2 vegetation, 1 building")

    def test_entries_out_of_the_top_blocks_tree(self):
        raw = forest()
        s = Scenery(raw)
        new, _notes, _by = scenery.erase_objects(raw, [scenery.EraseArea(5000.0, 5000.0, 10.0, ("building",))],
                                                 E_KINDS, {2})
        t = self.check(raw, new)
        self.assertEqual(len(t.blocks[0].entries), len(s.blocks[0].entries) - 1)
        self.assertEqual([n[1] for n in scenery._tree(t.blocks[0])], [2, 2, 3])  # the full list's split moved back
        before, after = leaves(s), leaves(t)
        self.assertEqual(len(after), len(before) - 1)
        for item, boxes in after.items():
            self.assertEqual(boxes, before[item])
        self.assertEqual(len(t.blocks), 3)  # a block placed once changes where it is
        self.assertEqual(len(t.blocks[0].raw) % 16, 0)  # padded as the shipped blocks are

    def test_a_placement_left_empty_loses_its_reference(self):
        raw = forest()
        new, notes, by = scenery.erase_objects(raw, [scenery.EraseArea(10100.0, 1000.0, 150.0)], E_KINDS, {2})
        t = self.check(raw, new)
        self.assertEqual(by, {"vegetation": 3})
        self.assertEqual(len(t.blocks), 4)  # the wood copied, without its reference to that patch
        copy = t.blocks[1]
        self.assertEqual(sum(1 for it in copy.items if it.kind == "child"), 1)
        self.assertEqual(spots(raw) - spots(new), Counter({(1, x, 1000.0): 1 for x in (10000.0, 10100.0, 10200.0)}))
        # every oak everywhere: both woods keep only their road piece; the patch nothing places goes, so does the wood.
        # The two woods lose the same objects, so they share one copy, placed twice (as the shipped maps share blocks)
        new, notes, by = scenery.erase_objects(raw, [scenery.EraseArea(5000.0, 500.0, 9000.0)], E_KINDS, {2})
        t = self.check(raw, new)
        self.assertEqual(by, {"vegetation": 12})
        self.assertEqual(len(t.blocks), 2)
        self.assertEqual(t.placings()[0], [1, 2])
        self.assertIn("1 shared block(s) copied", notes[1])
        self.assertIn("2 no longer placed anywhere left out", notes[1])
        self.assertEqual(Counter(sym for sym, _m in t.walk()), Counter({0: 1, 2: 1}))

    def test_road_pieces_stay(self):
        raw = forest(patch_road=True)
        new, _notes, by = scenery.erase_objects(raw, [scenery.EraseArea(5000.0, 500.0, 9000.0)], E_KINDS, {2})
        t = self.check(raw, new)
        self.assertEqual(by, {"vegetation": 12})
        self.assertEqual(len(t.roads()), 6)

    def test_too_big_a_copy_is_refused(self):
        raw = forest()
        old = scenery.DATA_LIMIT
        scenery.DATA_LIMIT = len(Scenery(raw).blocks[0].raw) + 10
        try:
            with self.assertRaisesRegex(SceneryEditError, "copies too many of the map's shared blocks"):
                scenery.erase_objects(raw, [scenery.EraseArea(10100.0, 0.0, 50.0)], E_KINDS, {2})
        finally:
            scenery.DATA_LIMIT = old

    def test_what_the_studio_says_circles_take(self):
        """erase_count, for the Studio's Erase tool: what the circles take, counted as the build erases (groups from
        the scenery types, a bridge only by name), and an erase the build would refuse refused the same way."""
        raw = forest()
        descs = {n: scenery.Descriptor(n, "TSceneryDescriptorMultiState", "", g, None, "")
                 for n, g in zip(E_NAMES, ("building", "vegetation", "building"))}
        self.assertTrue(descs["TypeWarrior/Pont_Normandie"].bridge)
        around = (5500.0, 5500.0, 1000.0)  # the hall and the bridge
        areas = [scenery.EraseArea(0.0, 0.0, 150.0), scenery.EraseArea(*around, ("building",))]
        self.assertEqual(scenery.erase_count(raw, areas, descs), {"vegetation": 2, "building": 1})
        named = scenery.EraseArea(*around, (), ("TypeWarrior/Pont_Normandie",))
        self.assertEqual(scenery.erase_count(raw, [named], descs), {"bridge": 1})
        self.assertEqual(scenery.erase_count(raw, [scenery.EraseArea(*around)], descs), {})
        self.assertEqual(scenery.erase_count(raw, [], descs), {})
        old = scenery.DATA_LIMIT
        scenery.DATA_LIMIT = 10
        try:
            with self.assertRaisesRegex(SceneryEditError, "copies too many of the map's shared blocks"):
                scenery.erase_count(raw, areas, descs)
        finally:
            scenery.DATA_LIMIT = old

    def test_the_mod_file(self):
        areas = scenery.parse_erase([{"x": 1, "y": 2, "radius": 300},
                                     {"x": 3, "y": 4, "radius": 5, "what": ["building"],
                                      "types": ["TypeWarrior/Pont_Normandie"]}])
        self.assertEqual(areas, [scenery.EraseArea(1.0, 2.0, 300.0),
                                 scenery.EraseArea(3.0, 4.0, 5.0, ("building",), ("TypeWarrior/Pont_Normandie",))])
        text = objects_toml([NewObject("TypeWarrior/Chene_02", 50.0, 60.0)], "header", areas)
        data = tomllib.loads(text)
        self.assertEqual(scenery.parse_erase(data["erase"]), areas)
        self.assertEqual(parse_objects(data["object"]), [NewObject("TypeWarrior/Chene_02", 50.0, 60.0)])
        for row, msg in [({"x": 1, "y": 2}, "has no radius"), ({"x": 1, "y": 2, "radius": 0}, "above 0"),
                         ({"x": 1, "y": 2, "radius": 1e9}, "at most"), ({"x": "a", "y": 2, "radius": 1}, "numbers"),
                         ({"x": 1, "y": 2, "radius": 1, "what": ["other"]}, "isn't something it can erase"),
                         ({"x": 1, "y": 2, "radius": 1, "what": "prop"}, "must be a list"),
                         ({"x": 1, "y": 2, "radius": 1, "what": [], "types": []}, "names nothing"),
                         ({"x": 1, "y": 2, "radius": 1, "types": [3]}, "type names"),
                         ({"x": 1, "y": 2, "radius": 1, "size": 1}, "unknown key")]:
            with self.assertRaisesRegex(SceneryEditError, msg):
                scenery.parse_erase([row])


class Building(unittest.TestCase):
    """A mod's maps/<map>/scenery.toml, built into the map's pack (MOD_FORMAT §8)."""

    def test_erase_areas_go_into_the_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "R.U.S.E"
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(unit_pack_raw())
            shipped = make_edat([("dir", "output\\", [("file", "save.boobspc", village())])])
            (game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(shipped)
            mod = root / "mod"
            (mod / "maps" / "Test").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "clearing"\nversion = "1.0.0"\n', encoding="utf-8")
            # the village: the hall at (1000, 2000); oaks at (5000, 0), (5100, 0), (5000, 9000), (5100, 9000)
            (mod / "maps" / "Test" / "scenery.toml").write_text(
                '[[erase]]\nx = 5050\ny = 0\nradius = 100\n\n[[erase]]\nx = 1000\ny = 2000\nradius = 10\n',
                encoding="utf-8")
            info, _ops = load_mod(mod)
            self.assertEqual(info.scenery, {})
            self.assertEqual(info.erase, {"Test": [scenery.EraseArea(5050.0, 0.0, 100.0),
                                                   scenery.EraseArea(1000.0, 2000.0, 10.0)]})
            lines = []
            result = build_and_write(game, [(info, _ops)], out=root / "out", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            self.assertEqual([f for f in result.findings if f.level == "warning"], [])
            self.assertIn("  2 object(s) erased in 2 area(s): 2 vegetation", lines)
            arc = Edat((root / "out" / "DataMapTest_v09.dat").read_bytes())
            new = bytes(arc.read(arc.find(scenery.MEMBER)))
            self.assertEqual(spots(village()) - spots(new), Counter({(1, 5000.0, 0.0): 1, (1, 5100.0, 0.0): 1}))
            self.assertEqual((game / "Maps" / "PC" / "DataMapTest_v09.dat").read_bytes(), shipped)
            # the hall only when the area names buildings; the area's ground is then opened (T25), no warning
            (mod / "maps" / "Test" / "scenery.toml").write_text(
                '[[erase]]\nx = 1000\ny = 2000\nradius = 10\nwhat = ["building"]\n', encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(mod)], out=root / "out2", say=lines.append)
            self.assertEqual(result.errors, [])
            self.assertNotIn("stays closed", " ".join(f.message for f in result.findings))
            self.assertTrue(any("buildings erased: the ground of the erase area(s) that take buildings is opened" in ln
                                for ln in lines), lines)
            arc = Edat((root / "out2" / "DataMapTest_v09.dat").read_bytes())
            new = bytes(arc.read(arc.find(scenery.MEMBER)))
            self.assertEqual(spots(village()) - spots(new), Counter({(0, 1000.0, 2000.0): 1}))
            # by name only (types, no "building" in what): erased, with the warning that its ground stays closed
            (mod / "maps" / "Test" / "scenery.toml").write_text(
                '[[erase]]\nx = 1000\ny = 2000\nradius = 10\nwhat = ["prop"]\ntypes = ["TypeWarrior/MairieNormande"]\n',
                encoding="utf-8")
            result = build_and_write(game, [load_mod(mod)], out=root / "out3", say=lines.append)
            self.assertEqual(result.errors, [])
            self.assertIn("leave their ground closed to units", " ".join(f.message for f in result.findings))

    def test_objects_go_into_the_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "R.U.S.E"
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "x.bin", b"x")]))
            shipped = make_edat([("dir", "output\\", [("file", "save.boobspc", village())])])
            (game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(shipped)
            mod = root / "mod"
            (mod / "maps" / "Test").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "trees"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / "maps" / "Test" / "scenery.toml").write_text(
                objects_toml([NewObject("TypeWarrior/Chene_02", 50.0, 60.0)]), encoding="utf-8")
            info, _ops = load_mod(mod)
            self.assertEqual(info.scenery, {"Test": [NewObject("TypeWarrior/Chene_02", 50.0, 60.0)]})
            lines = []
            result = build_and_write(game, [(info, _ops)], out=root / "out", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            arc = Edat((root / "out" / "DataMapTest_v09.dat").read_bytes())
            new = bytes(arc.read(arc.find(scenery.MEMBER)))
            self.assertEqual(spots(new) - spots(village()), Counter({(1, 50.0, 60.0): 1}))
            self.assertEqual((game / "Maps" / "PC" / "DataMapTest_v09.dat").read_bytes(), shipped)
            (mod / "maps" / "Test" / "scenery.toml").write_text('[[object]]\ntype = "TypeWarrior/Nope"\nx = 1\ny = 2\n',
                                                               encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(mod)], out=root / "out2", say=lines.append)
            self.assertIn("isn't used on this map", result.errors[0].message)
            self.assertIn("Nothing was written.", lines)


class Studio(unittest.TestCase):
    """The Studio's calls: what stands on a map, and placing objects into the current mod's scenery file."""

    def test_placing(self):
        from ruse_studio.api import StudioApi, StudioError
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "R.U.S.E"
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(unit_pack_raw())
            (game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(
                make_edat([("dir", "output\\", [("file", "save.boobspc", village())])]))
            api = StudioApi(game_dir=game, home=Path(tmp, "home"), index_path=Path(tmp, "none.sqlite"))
            v = api.map_scenery("Test")
            self.assertEqual([(r[0], r[2], r[4]) for r in v["palette"]],
                             [("TypeWarrior/MairieNormande", "building", 1), ("TypeWarrior/Chene_02", "vegetation", 4)])
            self.assertEqual(api.scenery("Test"), {"objects": [], "erase": [], "saved": None, "mod": None})
            with self.assertRaises(StudioError):
                api.scenery_add("Test", [{"type": "TypeWarrior/Chene_02", "x": 50, "y": 60}])  # no mod yet
            folder = Path(api.new_mod("Village")["current"])
            api.scenery_add("Test", [{"type": "TypeWarrior/Chene_02", "x": 50, "y": 60}])
            res = api.scenery_add("Test", [{"type": "TypeWarrior/MairieNormande", "x": 70, "y": 80, "turn": 45,
                                            "size": 2}])
            self.assertEqual(res["count"], 2)
            with self.assertRaisesRegex(StudioError, "isn't one of this map's own types"):
                api.scenery_add("Test", [{"type": "TypeWarrior/Nope", "x": 1, "y": 2}])
            info, _ops = load_mod(folder)
            self.assertEqual(info.scenery["Test"], [NewObject("TypeWarrior/Chene_02", 50.0, 60.0),
                                                    NewObject("TypeWarrior/MairieNormande", 70.0, 80.0, 45.0, 2.0)])
            self.assertEqual(api.scenery_undo("Test", 1)["count"], 1)
            self.assertEqual(api.scenery_undo("Test", 5), {"count": 0, "removed": 1, "saved": None})
            self.assertFalse((folder / "maps").exists())
            # erase areas written by hand stay when the Studio rewrites the file
            path = folder / "maps" / "Test" / "scenery.toml"
            path.parent.mkdir(parents=True)
            path.write_text('[[erase]]\nx = 5050\ny = 0\nradius = 100\n', encoding="utf-8")
            api.scenery_add("Test", [{"type": "TypeWarrior/Chene_02", "x": 50, "y": 60}])
            self.assertEqual(api.scenery_undo("Test", 1), {"count": 0, "removed": 1, "saved": str(path)})
            info, _ops = load_mod(folder)
            self.assertEqual(info.erase, {"Test": [scenery.EraseArea(5050.0, 0.0, 100.0)]})
            # a Forest stroke's trees, with an object placed after them: Undo takes those trees, by the objects
            tree = {"type": "TypeWarrior/Chene_02", "x": 1, "y": 2, "turn": 30, "size": 0.9}
            api.scenery_add("Test", [tree, dict(tree, x=5)])
            api.scenery_add("Test", [{"type": "TypeWarrior/MairieNormande", "x": 70, "y": 80}])
            api.scenery_add("Test", [tree])  # the same tree again, later: the last one like it goes
            res = api.scenery_undo("Test", 2, [tree, dict(tree, x=5)])
            self.assertEqual((res["count"], res["removed"]), (2, 2))
            info, _ops = load_mod(folder)
            self.assertEqual(info.scenery["Test"], [NewObject("TypeWarrior/Chene_02", 1.0, 2.0, 30.0, 0.9),
                                                    NewObject("TypeWarrior/MairieNormande", 70.0, 80.0)])
            self.assertEqual(api.scenery_undo("Test", 1, [dict(tree, x=99)])["removed"], 0)  # not there: nothing

    def test_the_erase_tool(self):
        """The map view's Erase brush: its circles saved as the scenery file's [[erase]] tables (the file's objects
        kept, and the objects' own edits keeping the circles), what they take counted the way the build erases,
        taken back by Undo, and built: the map's trees under them go."""
        from ruse_studio.api import StudioApi, StudioError
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "R.U.S.E"
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(unit_pack_raw())
            (game / "Maps" / "PC" / "DataMapTest_v09.dat").write_bytes(
                make_edat([("dir", "output\\", [("file", "save.boobspc", village())])]))
            api = StudioApi(game_dir=game, home=Path(tmp, "home"), index_path=Path(tmp, "none.sqlite"))
            nothing = {"count": 0, "takes": {}, "error": ""}
            self.assertEqual(api.scenery_erased("Test"), nothing)  # no mod: nothing to count
            with self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
                api.scenery_erase("Test", [{"x": 5000, "y": 0, "radius": 50}])
            folder = Path(api.new_mod("Clearing")["current"])
            path = folder / "maps" / "Test" / "scenery.toml"
            self.assertEqual(api.scenery_erased("Test"), nothing)
            api.scenery_add("Test", [{"type": "TypeWarrior/Chene_02", "x": 50, "y": 60}])
            # a drag's circles taking trees and props (the default: left unsaid in the file), then one taking buildings
            # too; the village: its hall at (1000, 2000), oaks at (5000, 0), (5100, 0), (5000, 9000), (5100, 9000)
            res = api.scenery_erase("Test", [{"x": 5000, "y": 0, "radius": 50, "what": ["vegetation", "prop"]},
                                             {"x": 5100, "y": 0, "radius": 50}])
            self.assertEqual(res, {"count": 2, "saved": str(path)})
            api.scenery_erase("Test", [{"x": 1000, "y": 2000, "radius": 10, "what": ["vegetation", "prop", "building"]}])
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual((lines.count("[[erase]]"), lines.count("[[object]]")), (3, 1))
            self.assertEqual([ln for ln in lines if ln.startswith("what")], ['what = ["vegetation", "prop", "building"]'])
            self.assertIn("[[erase]]", lines[0])  # the header says what they are
            got = api.scenery("Test")
            self.assertEqual([o["type"] for o in got["objects"]], ["TypeWarrior/Chene_02"])
            self.assertEqual(got["erase"][0], {"x": 5000.0, "y": 0.0, "radius": 50.0, "what": ["vegetation", "prop"],
                                               "types": []})
            self.assertEqual(api.scenery_erased("Test"), {"count": 3, "takes": {"vegetation": 2, "building": 1},
                                                          "error": ""})
            # placing and taking back objects keeps the circles; wrong circles are refused, nothing saved
            api.scenery_undo("Test", 1)
            api.scenery_add("Test", [{"type": "TypeWarrior/Chene_02", "x": 50, "y": 60}])
            for bad, why in (([{"x": 1, "y": 2, "radius": 3, "what": ["water"]}], "isn't something it can erase"),
                             ([{"x": 1, "y": 2}], "has no radius"), ([{"x": 1, "y": 2, "radius": 0}], "above 0"),
                             ([], "a list of tables"), ("x", "a list of tables"), ([3], "a list of tables")):
                with self.assertRaisesRegex(StudioError, why):
                    api.scenery_erase("Test", bad)
            self.assertEqual(len(api.scenery("Test")["erase"]), 3)
            # Undo: the last circles, the file's objects kept
            self.assertEqual(api.scenery_erase_undo("Test", 1), {"count": 2, "removed": 1, "saved": str(path)})
            info, _ops = load_mod(folder)
            self.assertEqual(info.erase["Test"], [scenery.EraseArea(5000.0, 0.0, 50.0),
                                                  scenery.EraseArea(5100.0, 0.0, 50.0)])
            self.assertEqual(info.scenery["Test"], [NewObject("TypeWarrior/Chene_02", 50.0, 60.0)])
            self.assertEqual(api.scenery_erased("Test")["takes"], {"vegetation": 2})
            # an erase the build would refuse is said, not raised
            old = scenery.DATA_LIMIT
            scenery.DATA_LIMIT = 10
            try:
                res = api.scenery_erased("Test")
            finally:
                scenery.DATA_LIMIT = old
            self.assertIn("copies too many of the map's shared blocks", res["error"])
            # built (the placed oak taken back first): the oaks under the circles go
            api.scenery_undo("Test", 1)
            lines = []
            result = build_and_write(game, [load_mod(folder)], out=Path(tmp) / "out", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            arc = Edat((Path(tmp) / "out" / "DataMapTest_v09.dat").read_bytes())
            new = bytes(arc.read(arc.find(scenery.MEMBER)))
            self.assertEqual(spots(village()) - spots(new), Counter({(1, 5000.0, 0.0): 1, (1, 5100.0, 0.0): 1}))
            # a map that isn't in the game: its circles are saved, but can't be counted
            api.scenery_erase("Nowhere", [{"x": 1, "y": 2, "radius": 3}])
            with self.assertRaisesRegex(StudioError, "DataMapNowhere_v09.dat isn't in the game folder"):
                api.scenery_erased("Nowhere")
            # Undo past the circles: with neither objects nor circles the file goes
            self.assertEqual(api.scenery_erase_undo("Test", 9), {"count": 0, "removed": 2, "saved": None})
            self.assertFalse((folder / "maps" / "Test").exists())
            self.assertEqual(api.scenery_erase_undo("Test"), {"count": 0, "removed": 0, "saved": None})
            self.assertEqual(api.scenery_erased("Test"), nothing)

    def test_the_map_view_erases_as_the_build_does(self):
        """The map view draws the Erase brush's circles by the build's own rules (maps.js): the default and the
        largest circle are rusemod.scenery's, a drag lists what it takes in the file's order (so the default stays
        unsaid), and a circle taking trees opens its ground to every unit and takes its cover, after the strokes, as
        rusemod.build.cleared_woods does."""
        import json
        from rusemod.build import cleared_woods
        from rusemod.cover import Paint
        from rusemod.nav import Block
        maps = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "maps.js").read_text(encoding="utf-8")
        self.assertIn(f"const ERASE_DEFAULT = {json.dumps(list(scenery.ERASE_DEFAULT))};", maps)
        self.assertIn(f"const ERASE_MAX = {scenery.ERASE_MAX:.0f};", maps)
        picked = ["vegetation", "prop", "building"]
        self.assertIn(f"const what = {json.dumps(picked)}.filter(", maps)
        self.assertEqual(picked[:2], list(scenery.ERASE_DEFAULT))
        self.assertLessEqual(set(picked), set(scenery.ERASE_GROUPS))
        self.assertIn('return (a.what || ERASE_DEFAULT).includes("vegetation");', maps)
        self.assertIn('clearsWood(a) ? ["erase", "open", "uncover"] : ["erase"]', maps)
        # open to every unit; cover taken away (the map's own, the Town tool's, painted). Bit 4 of moves and bit 8 of
        # cover only mark what a brush changed (drawn striped): what a cell means for units is the other bits (MEANS)
        self.assertIn("open: [moves, 4, 3]", maps)
        self.assertIn("uncover: [cover, 8, 7]", maps)
        self.assertIn("[[cover, (v) => (v & 7 ? 1 : 0)], [moves, (v) => v & 3]]", maps)
        reapply = maps[maps.index("function reapply()"):]
        reapply = reapply[:reapply.index("\n}\n")]
        self.assertLess(reapply.index("applyStroke(ed, s)"), reapply.index("eraseDab(a)"))
        woods = scenery.EraseArea(1.0, 2.0, 3.0)
        opens, uncover = cleared_woods({"M": ([woods, scenery.EraseArea(4.0, 5.0, 6.0, ("prop",))], ["m"])})
        self.assertEqual(opens, {"M": ([Block(1.0, 2.0, 3.0, "all", True)], ["m"])})
        # the blocked layer goes too (d81bc8b, T41: direct fire stops at it); the view draws no blocked layer
        self.assertEqual(uncover, {"M": ([Paint(1.0, 2.0, 3.0, "cover", True), Paint(1.0, 2.0, 3.0, "blocked", True)],
                                         ["m"])})


if __name__ == "__main__":
    unittest.main()
