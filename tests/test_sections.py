"""Sections of a map's scenery copied once and placed many times (rusemod.scenery.add_sections, [[section]] in
scenery.toml): on the small made-up files of test_scenery (no game files needed)."""
import math
import tomllib
import unittest
from unittest import mock

from test_scenery import NAMES, open_fields

from rusemod import scenery
from rusemod.scenery import (NewObject, Scenery, SceneryEditError, SectionArea, add_sections, parse_sections,
                             sections_toml, walk_levels)

OAK = "TypeWarrior/Chene_02"


def oaks_walked(data: bytes) -> list[tuple[float, float, int]]:
    """Every oak the walk reaches: (x, y, its mask), rounded."""
    return sorted((round(m[3]), round(m[7]), mask)
                  for _s, m, mask in walk_levels(Scenery(data), (-1e9, -1e9, 1e9, 1e9), {1}))


def stored_oaks(data: bytes) -> int:
    return sum(1 for b in Scenery(data).blocks for it in b.items if it.kind == "object" and it.symbol == 1)


class Placing(unittest.TestCase):
    def test_a_section_is_written_once_and_placed_where_asked(self):
        """Two plants about the section's middle, placed three times (one turned a quarter, one a half): the walk
        reaches six, at their places turned with the section, at the levels their shipped copies have; the file
        holds the two once (and the map's own oaks as before)."""
        data = open_fields()
        before = oaks_walked(data)
        plants = [NewObject(OAK, 0.0, 0.0, levels=0x05), NewObject(OAK, 100.0, 50.0, levels=0x05)]
        places = ((20000.0, 20000.0, 0.0), (22000.0, 20000.0, 90.0), (20000.0, 23000.0, 180.0))
        new, notes = add_sections(data, [("grass", plants, places)])
        s = Scenery(new)
        self.assertEqual(s.roots(), [0])
        self.assertEqual(stored_oaks(new), stored_oaks(data) + 2)
        got = oaks_walked(new)
        for o in before:
            got.remove(o)   # the map's own, as they were
        want = sorted([(20000, 20000, 5), (20100, 20050, 5), (22000, 20000, 5), (21950, 20100, 5),
                       (20000, 23000, 5), (19900, 22950, 5)])
        self.assertEqual(got, want)
        self.assertIn("placed 3 times", " ".join(notes))

    def test_places_in_parts_each_on_a_carrier_of_its_own(self):
        """More places than one new block lists (SECTION_PART, here 1): one new block per part, each wrapping one of
        the map's own blocks (not another new one), and still every place reached."""
        data = open_fields()
        plants = [NewObject(OAK, 0.0, 0.0, levels=0x05)]
        with mock.patch.object(scenery, "SECTION_PART", 1):
            new, _notes = add_sections(data, [("grass", plants, ((20000.0, 20000.0, 0.0), (25000.0, 12000.0, 0.0)))])
        s = Scenery(new)
        wrappers = [b for b in s.blocks[1:] if sum(it.kind == "child" for it in b.items) == 2]
        self.assertEqual(len(wrappers), 2)
        for b in wrappers:
            kid = s.block_at(b.items[0].child_offset)
            self.assertEqual(tuple(kid.bbox), (-100.0, -100.0, 100.0, 100.0))   # the map's own wood
        self.assertIn((20000, 20000, 5), oaks_walked(new))
        self.assertIn((25000, 12000, 5), oaks_walked(new))

    def test_the_grids_are_marked_under_the_places(self):
        data = open_fields()
        new, notes = add_sections(data, [("grass", [NewObject(OAK, 0.0, 0.0, levels=0x05)],
                                          ((20000.0, 20000.0, 0.0),))])
        s = Scenery(new)
        for level in range(3):
            cell = scenery.GRID_CELL[level]
            cx, cy = math.floor(20000.0 / cell), math.floor(20000.0 / cell)
            at = s.grids[level][0] + (cx * s.grid_dims[2 * level + 1] + cy) * scenery.GRID_RECORD[level]
            self.assertEqual(new[at + 2], 1, level)
        self.assertIn("marked as holding something", " ".join(notes))

    def test_refusals(self):
        data = open_fields()
        with self.assertRaisesRegex(SceneryEditError, "isn't used on this map"):
            add_sections(data, [("x", [NewObject("TypeWarrior/Nope", 0.0, 0.0)], ((100.0, 100.0, 0.0),))])
        with mock.patch.object(scenery, "BLOCK_MOST", 1), self.assertRaisesRegex(SceneryEditError, "smaller square"):
            add_sections(data, [("x", [NewObject(OAK, 0.0, 0.0), NewObject(OAK, 1.0, 0.0)], ((100.0, 100.0, 0.0),))])
        self.assertEqual(add_sections(data, [("x", [], ((100.0, 100.0, 0.0),))])[0], data)   # nothing to place


class Tint(unittest.TestCase):
    """The tint under the sections' stickers (groundpaint.fit_sticker_tint): each sticker drawn the colour of the ground
    painted under it, lit as the scene lights it."""

    def test_a_sticker_draws_the_grounds_colour(self):
        from test_groundpaint import BOUNDS, div_map, mark

        from rusemod.groundpaint import (STICKER_LIGHT, _overlay, _tint_of, fit_sticker_tint, sticker_light)
        raw = div_map()   # 64 x 32 pixels over 2,000 x 1,000: 31.25 a pixel
        ground = (120, 96, 50)   # an olive-brown hill under a green sticker
        green = (0.17, 0.24, 0.05)
        new, notes = fit_sticker_tint(raw, BOUNDS, [(500.0, 500.0, 100.0, 30.0, green)], lambda x, y: ground)
        (r, g, _b), a = mark(new, 500.0, 500.0)
        t = _tint_of(r, g, a)
        drawn = [_overlay(green[c], min(max(t[c], 0.0), 1.0)) * STICKER_LIGHT[c] * 255 for c in range(3)]
        for c in range(3):
            self.assertAlmostEqual(drawn[c], ground[c], delta=6.0)
        self.assertEqual(mark(new, 1500.0, 500.0), mark(raw, 1500.0, 500.0))   # no sticker there: as it was
        self.assertIn("100%", " ".join(notes))
        # facing away from the sun the scene lights it less: its tint is brighter there
        away = fit_sticker_tint(raw, BOUNDS, [(500.0, 500.0, 100.0, 30.0, green)], lambda x, y: ground,
                                lambda x, y: (-0.32, -0.56, 0.77))[0]
        self.assertLess(sticker_light((-0.32, -0.56, 0.77))[0], STICKER_LIGHT[0])
        self.assertGreater(mark(away, 500.0, 500.0)[1], a)

    def test_nothing_to_fit(self):
        from test_groundpaint import BOUNDS, div_map

        from rusemod.groundpaint import fit_sticker_tint
        self.assertEqual(fit_sticker_tint(div_map(), BOUNDS, [], lambda x, y: (1, 2, 3))[0], b"")
        self.assertEqual(fit_sticker_tint(div_map(), BOUNDS, [(500.0, 500.0, 100.0, 0.0, (0.2, 0.2, 0.2))],
                                          lambda x, y: None)[0], b"")


class StickerKinds(unittest.TestCase):
    """Each theatre's decor set defines its own Herbe_verte, traces_terre, ... with its own picture: a map's stickers
    are the definitions of the sets it loads (groundtex.decal_kinds)."""

    def test_the_loaded_sets_definition(self):
        from rusemod.groundtex import DecalType, decal_kinds
        types = {"gen\\a.tgv": [DecalType("TypeWarrior/Herbe_verte", "afrique", 2048.0, "gen\\a.tgv")],
                 "gen\\f.tgv": [DecalType("TypeWarrior/Herbe_verte", "france", 2048.0, "gen\\f.tgv", "gen\\fa.tgv")],
                 "gen\\c.tgv": [DecalType("TypeWarrior/Herbe_verte", "communs", 2048.0, "gen\\c.tgv"),
                                DecalType("TypeWarrior/Commun", "communs", 1024.0, "gen\\c.tgv")]}
        got = decal_kinds(types, {"france", "communs"})
        self.assertEqual(got["TypeWarrior/Herbe_verte"].colour, "gen\\f.tgv")   # the theatre's before the common one
        self.assertEqual(got["TypeWarrior/Herbe_verte"].alpha, "gen\\fa.tgv")
        self.assertEqual(got["TypeWarrior/Commun"].theatre, "communs")
        self.assertEqual(set(decal_kinds(types, {"afrique"})), {"TypeWarrior/Herbe_verte"})
        self.assertEqual(len(decal_kinds(types, set())), 2)   # no sets known: every name

    def test_a_one_channel_shape_reads(self):
        """France's stickers keep their shapes as L8 pictures (8 mips, smallest first): read at the mip asked."""
        from rusemod.groundtex import TextureError, tgv_grey
        from rusemod.tmst import make_tgv, zipo_pack
        mips = [zipo_pack(bytes([10 * (s // 2)] * (s * s))) for s in (1, 2, 4, 8)]   # 1, 2, 4, 8 a side
        raw = make_tgv(8, 8, "L8", mips)
        self.assertEqual(tgv_grey(raw, 4), (4, 4, bytes([20] * 16)))
        self.assertEqual(tgv_grey(raw, 64)[:2], (8, 8))
        with self.assertRaises(TextureError):
            tgv_grey(make_tgv(8, 8, "DXT1", mips))

    def test_a_datadir_picture_is_the_packs_member(self):
        from rusemod.groundtex import _texture_member
        self.assertEqual(_texture_member("DataDir:\\WW2\\Res2D\\Decors\\Italie\\Stickers\\Herbe_verte.tga"),
                         "gen\\ww2\\res2d\\decors\\italie\\stickers\\herbe_verte.tgv")
        self.assertEqual(_texture_member("WW2/Res2D/Decors/France/Alpha/Herbe_A.tga"),
                         "gen\\ww2\\res2d\\decors\\france\\alpha\\herbe_a.tgv")


class TheModFile(unittest.TestCase):
    def test_written_and_read_back(self):
        rows = [SectionArea("rock-1", 1000.0, 2000.0, 7800.0, ((5.0, 6.0, 90.0), (7.5, 8.0, 0.0))),
                SectionArea("town_a", 10.0, 20.0, 26000.0, ((1.0, 2.0, 0.0),), ("stickers", "trees", "props"),
                            "M03_Italie")]
        text = sections_toml(rows, "Made in a test.")
        self.assertEqual(parse_sections(tomllib.loads(text)["section"]), rows)

    def test_a_section_listing_its_objects(self):
        """A section made elsewhere (a mod's generated dressing): its objects listed, levels and heights kept."""
        rows = [SectionArea("grass-1", 0.0, 0.0, 0.0, ((5.0, 6.0, 90.0),),
                            objects=(("TypeWarrior/trace_herbe_vive", 10.5, -20.0, 45.0, 0.73, 0x15, 0.0),
                                     ("TypeWarrior/HerbesMarais_02", 1.0, 2.0, 0.0, 1.03, 0x1F, 0.79)))]
        text = sections_toml(rows)
        got = parse_sections(tomllib.loads(text)["section"])
        self.assertEqual(got, rows)
        objs = got[0].new_objects()
        self.assertEqual((objs[1].levels, objs[1].height, objs[1].solid), (0x1F, 0.79, False))
        for bad, why in (([["T", 1, 2, 3, 99, 5]], "size is 0.05 to 50"), ([["T", 1, 2]], "each object"),
                         ([["T", 1, 2, 3, 1, 64]], "levels 0 to")):
            with self.subTest(bad=bad), self.assertRaisesRegex(SceneryEditError, why):
                parse_sections([{"name": "a", "objects": bad, "places": [[1, 2]]}])
        with self.assertRaisesRegex(SceneryEditError, "not both"):
            parse_sections([{"name": "a", "objects": [["T", 1, 2, 3, 1, 5]], "sx": 1, "places": [[1, 2]]}])

    def test_rows_refused(self):
        good = {"name": "a", "sx": 1, "sy": 2, "side": 100, "places": [[1, 2], [3, 4, 90]]}
        self.assertEqual(parse_sections([good])[0].places, ((1.0, 2.0, 0.0), (3.0, 4.0, 90.0)))
        for bad, why in (({"name": "A b"}, "name"), ({"side": 0}, "side"), ({"places": []}, "places"),
                         ({"places": [[1]]}, "each place"), ({"layers": ["houses"]}, "layers"),
                         ({"colour": 1}, "unknown key"), ({"sx": "far"}, "numbers")):
            with self.subTest(bad=bad), self.assertRaisesRegex(SceneryEditError, why):
                parse_sections([{**good, **bad}])
        row = dict(good)
        del row["side"]
        with self.assertRaisesRegex(SceneryEditError, "has no side"):
            parse_sections([row])

    def test_its_copy_area(self):
        a = SectionArea("a", 1000.0, 2000.0, 7800.0, ((0.0, 0.0, 0.0),)).copy_area(group=3)
        self.assertEqual((a.x, a.y, a.radius, a.sx, a.sy, a.shape, a.group), (0.0, 0.0, 3900.0, 1000.0, 2000.0,
                                                                              "square", 3))


if __name__ == "__main__":
    unittest.main()
