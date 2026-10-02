"""A map's scenery (rusemod.scenery) on small made-up files: the file, its blocks and items, the walk, what the
Studio shows, and the scenery types from made-up descriptor NDFs (no game files needed)."""
import hashlib
import math
import struct
import tempfile
import tomllib
import unittest
from collections import Counter
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import scenery
from rusemod.build import build_and_write, load_mod
from rusemod.edat import Edat
from rusemod.scenery import (BURY, SCALE16, SHRINK, T_COMPACT, T_FULL, NewObject, Scenery, SceneryEditError,
                             SceneryError, add_objects, bury_objects, descriptors, group_of, layout, objects_toml,
                             parse_objects, placement, view)


def compact(sym, x, y, turn=0.0, size=1.0):
    c, s = math.cos(turn) * size, math.sin(turn) * size
    q = [round(v / SCALE16) for v in (c, -s, s, c)]
    return struct.pack("<I4h4f", 0x80000000 | sym << 4, *q, x, y, 0.0, size)


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
    """(block, item offset) of every road piece the game's close-up road pass reaches, walked the way the game walks
    a scenery file: a block is entered only when its root has the road mark (bit 25), a block seen from far starts
    at its root's right side, and inside it a node is entered only with the mark."""
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
    # the three grids (far, middle, close: cells 81,920, 20,480 and 5,120 across, records of 4, 5 and 3 bytes) over
    # 40,960 x 40,960, every cell empty
    fields = [tab_off, len(blocks) + 1, data_off, len(data), flags_off, len(flags), names_off, len(name_blob),
              opt_off, 0, names2_off, 4, layers_off, 0, 1, 1, 2, 2, 8, 8, grid_off, 4, grid_off + 4, 20,
              grid_off + 24, 192]
    body = (b"0.6\0" + struct.pack("<26I", *fields) + struct.pack(f"<{len(blocks) + 1}I", *offsets, len(data)) + data
            + name_blob + flags + struct.pack("<I", 0) + bytes(4 + 20 + 192))
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
        self.assertIn("with block 1", notes[0])
        hall = next(m for sym, m in s.walk() if sym == 0 and round(m[3]) == 5300)
        _x, _y, turn, size = placement(hall)
        self.assertAlmostEqual(math.degrees(turn), 45.0, places=3)
        self.assertAlmostEqual(size, 2.0, places=3)

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


class RoadStickers(unittest.TestCase):
    """A new road's stickers (the game's Route pieces: what draws a road up close), cut like the shipped ones and
    added with the objects in the map's own style."""

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
        self.assertLessEqual(new_pieces, road_pass(after))  # drawn up close: the road mark from the map's top down

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
        _new, notes = add_objects(data, [NewObject("TypeWarrior/Chene_02", 30000.0, 30000.0)])  # out in the open
        self.assertIn("lie in no box of the map's draw tree", notes[-1])
        self.assertIn("(30000, 30000)", notes[-1])

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
        # every oak everywhere: both woods keep only their road piece; the patch nothing places goes, so does the wood
        new, notes, by = scenery.erase_objects(raw, [scenery.EraseArea(5000.0, 500.0, 9000.0)], E_KINDS, {2})
        t = self.check(raw, new)
        self.assertEqual(by, {"vegetation": 12})
        self.assertEqual(len(t.blocks), 3)
        self.assertEqual(t.placings()[0], [1, 1, 1])
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
            # the hall only when the area names buildings, with a word that units still can't walk there
            (mod / "maps" / "Test" / "scenery.toml").write_text(
                '[[erase]]\nx = 1000\ny = 2000\nradius = 10\nwhat = ["building"]\n', encoding="utf-8")
            result = build_and_write(game, [load_mod(mod)], out=root / "out2", say=lines.append)
            self.assertEqual(result.errors, [])
            self.assertIn("stays closed to units", " ".join(f.message for f in result.findings))
            arc = Edat((root / "out2" / "DataMapTest_v09.dat").read_bytes())
            new = bytes(arc.read(arc.find(scenery.MEMBER)))
            self.assertEqual(spots(village()) - spots(new), Counter({(0, 1000.0, 2000.0): 1}))

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
        self.assertIn("open: [moves, 0, 3]", maps)       # open to every unit
        self.assertIn("uncover: [cover, 0, 1]", maps)    # cover taken away
        reapply = maps[maps.index("function reapply()"):]
        reapply = reapply[:reapply.index("\n}\n")]
        self.assertLess(reapply.index("applyStroke(ed, s)"), reapply.index("eraseDab(a)"))
        woods = scenery.EraseArea(1.0, 2.0, 3.0)
        opens, uncover = cleared_woods({"M": ([woods, scenery.EraseArea(4.0, 5.0, 6.0, ("prop",))], ["m"])})
        self.assertEqual(opens, {"M": ([Block(1.0, 2.0, 3.0, "all", True)], ["m"])})
        self.assertEqual(uncover, {"M": ([Paint(1.0, 2.0, 3.0, "cover", True)], ["m"])})


if __name__ == "__main__":
    unittest.main()
