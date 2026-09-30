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
from rusemod.scenery import (SCALE16, T_COMPACT, T_FULL, NewObject, Scenery, SceneryEditError, SceneryError,
                             add_objects, descriptors, group_of, layout, objects_toml, parse_objects, placement, view)


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
        self.assertEqual(hall[1:3], [1000, 2000])
        self.assertEqual(scenery.MEMBER, "output\\save.boobspc")


def spots(data):
    """Every object as (name index, x, y), for comparing whole maps."""
    return Counter((sym, round(m[3], 2), round(m[7], 2)) for sym, m in Scenery(data).walk())


class Adding(unittest.TestCase):
    def test_new_objects_land_where_asked_and_nothing_else_moves(self):
        data = village()
        new, notes = add_objects(data, [NewObject("TypeWarrior/MairieNormande", 7000.0, 8000.0, 90.0, 1.5),
                                        NewObject("TypeWarrior/Chene_02", -500.0, 300.0, 0.0, 4.0)])
        self.assertEqual(spots(new) - spots(data), Counter({(0, 7000.0, 8000.0): 1, (1, -500.0, 300.0): 1}))
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
        objs = [NewObject("TypeWarrior/Chene_02", 1.5, 2.0, 45.0, 2.0), NewObject("TypeWarrior/MairieNormande", 3.0, 4.0)]
        text = objects_toml(objs, "Made in the Studio.")
        self.assertTrue(text.startswith("# Made in the Studio.\n"))
        self.assertEqual(parse_objects(tomllib.loads(text)["object"]), objs)


class Building(unittest.TestCase):
    """A mod's maps/<map>/scenery.toml, built into the map's pack (MOD_FORMAT §8)."""

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
            self.assertEqual(api.scenery("Test"), {"objects": [], "saved": None, "mod": None})
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


if __name__ == "__main__":
    unittest.main()
