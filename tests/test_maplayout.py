"""rusemod.maplayout: a map's plots, what stands on them, their looks, their neighbours and the farm pieces they sit
in, read from the scenery (made-up maps from test_scenery's helpers)."""
import math
import tempfile
import unittest

from rusemod import maplayout, scenery
import test_scenery as ts
from test_scenery import FB_DESCS, FB_NAMES, block, compact, make_scenery, moved

HAY_NAMES = FB_NAMES + ["TypeWarrior/Foin", "TypeWarrior/Charrette_Foin", "TypeWarrior/MairieNormande"]
HAY_DESCS = dict(FB_DESCS)
for n, g in (("TypeWarrior/Foin", "prop"), ("TypeWarrior/Charrette_Foin", "prop"),
             ("TypeWarrior/MairieNormande", "building")):
    HAY_DESCS[n] = scenery.Descriptor(n, "TSceneryDescriptor", "Props/Ferme", g, None, "x")
FOIN, CART, HALL = len(FB_NAMES), len(FB_NAMES) + 1, len(FB_NAMES) + 2


class Plots(unittest.TestCase):
    def setUp(self):
        self.fb = ts.FieldBrush   # (its grid helpers; the module, not the class, is imported: its tests run there)

    def layout(self, items, picture=None, names=HAY_NAMES):
        data = make_scenery([block(items, box=(0.0, 0.0, 100000.0, 100000.0))], names)
        sc = scenery.Scenery(data)
        return sc, maplayout.read_layout(sc, HAY_DESCS, None, picture, "Test")

    def a_field(self):
        """Field A's rows (45 stickers facing 30 round (20000, 20000)) and plot B across the hedge (15)."""
        items = self.fb.grid(0, 20000.0, 20000.0, 30.0, 2500.0, 3500.0, 10000.0, 7000.0)
        bx, by = self.fb.across(20000.0, 20000.0, 30.0, 15100.0)
        items += self.fb.grid(0, bx, by, 30.0, 2500.0, 3500.0, 6000.0, 3500.0)
        return items

    def test_plots_are_the_brush_s_fields(self):
        """A and B are two plots (B lies across the hedge, past FIELD_ACROSS); each plot is the field the brush
        would change from any of its stickers."""
        sc, lay = self.layout(self.a_field())
        self.assertEqual(sorted(len(p.stickers) for p in lay.plots), [15, 45])
        a = max(lay.plots, key=lambda p: len(p.stickers))
        self.assertAlmostEqual(a.facing, 30.0, places=3)
        self.assertEqual(a.rows, {"Labourage_terrefonce": 45})
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        fields = scenery.brush_fields(dab, self.fb.LOOK, sc)
        self.assertEqual(sorted((round(m[3], 1), round(m[7], 1)) for f in fields for _s, m, _k, _h in f),
                         sorted((round(lay.stickers[k][1][3], 1), round(lay.stickers[k][1][7], 1)) for k in a.stickers))
        self.assertEqual(lay.plots_under(dab.footprint()), [a.id])
        self.assertEqual(lay.plot_at(20000.0, 20000.0)[0], a.id)
        self.assertIsNone(lay.plot_at(90000.0, 10000.0)[0])
        b = min(lay.plots, key=lambda p: len(p.stickers))
        self.assertEqual((a.neighbours, b.neighbours), ([b.id], [a.id]))   # their squares meet across the hedge
        self.assertTrue(5800.0 <= a.area_m2 <= 7200.0, a.area_m2)   # 24,096 x 18,096 units of squares: 6,450 m2

    def test_what_stands_on_a_plot(self):
        """Crops, hay and a cart (with how deep in and how many crops round them), a fence, a hedge tuft, and a
        building near it with its nearest crop and row sticker."""
        items = self.a_field()
        items += self.fb.grid(2, 20000.0, 20000.0, 30.0, 1000.0, 1000.0, 3000.0, 3000.0)   # 49 crops round A's middle
        items += [compact(FOIN, 21500.0, 20500.0), compact(CART, 22000.0, 21000.0), compact(4, 21000.0, 21000.0),
                  compact(3, 19500.0, 20500.0), compact(HALL, 20000.0, 9000.0)]
        _sc, lay = self.layout(items)
        a = max(lay.plots, key=lambda p: len(p.stickers))
        self.assertEqual(a.crops, {"Champs_Bles": 49})
        self.assertEqual(sorted(h[0] for h in a.hay), ["Charrette_Foin", "Foin"])
        self.assertTrue(all(h[3] > 0 and h[4] > 0 for h in a.hay))      # inside, among crops
        self.assertEqual(a.fences, 1)
        self.assertEqual(len(lay.buildings), 1)
        name, x, y, crop_m, row_m = lay.buildings[0]
        self.assertEqual((name, x, y), ("TypeWarrior/MairieNormande", 20000.0, 9000.0))
        self.assertTrue(crop_m is not None and row_m is not None and row_m < crop_m)
        self.assertEqual(a.buildings, [0])
        f = maplayout.facts(lay)
        self.assertEqual(f["hay and machines by look"]["other"]["pieces"], 2)
        self.assertEqual(f["buildings near plots"], 1)

    def test_looks_come_from_the_picture_rows_and_crops(self):
        """Wheat: yellow picture, straw rows, 35+ wheat clumps a 100 m2; ploughed: brown, earth rows, bare; a green
        picture over earth rows reads as other."""
        items = self.fb.grid(1, 20000.0, 20000.0, 30.0, 2500.0, 3500.0, 10000.0, 7000.0)   # Paille rows
        items += self.fb.grid(2, 20000.0, 20000.0, 30.0, 300.0, 300.0, 10000.0, 7000.0)    # wheat, ~49 a 100 m2
        _sc, lay = self.layout(items, picture=lambda x, y: (166, 133, 41))
        self.assertEqual(lay.plots[0].look, "wheat")
        _sc, lay = self.layout(self.a_field(), picture=lambda x, y: (123, 83, 41))
        self.assertEqual({p.look for p in lay.plots}, {"ploughed"})
        _sc, lay = self.layout(self.a_field(), picture=lambda x, y: (60, 90, 20))
        self.assertEqual({p.look for p in lay.plots}, {"other"})
        self.assertEqual(maplayout.look_of(None, {"Paille": 3}, {}, 100.0), "other")

    def test_farm_pieces_and_keeping(self):
        """A 200 m block of rows placed twice, turned: two places of one farm piece, each plot in it knows the piece
        and its spot inside; saved and loaded, the layout is the same."""
        piece = block(self.fb.grid(0, 26000.0, 26000.0, 0.0, 2500.0, 3500.0, 8000.0, 6000.0),
                      box=(0.0, 0.0, 52000.0, 52000.0))
        root_len = len(block([moved(0, 0, 0), moved(0, 0, 0)], box=(0.0, 0.0, 400000.0, 400000.0)))
        root = block([moved(root_len, 10000.0, 10000.0), moved(root_len, 200000.0, 50000.0)],
                     box=(0.0, 0.0, 400000.0, 400000.0))
        sc = scenery.Scenery(make_scenery([root, piece], HAY_NAMES))
        lay = maplayout.read_layout(sc, HAY_DESCS, None, None, "Test")
        self.assertEqual(len(lay.tiles), 1)
        self.assertEqual(lay.tiles[0][1], 2)            # placed twice
        self.assertEqual(len(lay.plots), 2)
        self.assertTrue(all(p.tile and p.tile[0] == lay.tiles[0][0] for p in lay.plots))
        self.assertEqual({(p.tile[2], p.tile[3]) for p in lay.plots}, {(26000, 26000)})   # the same spot in it
        with tempfile.TemporaryDirectory() as d:
            path = d + "/lay.json"
            lay.save(path)
            back = maplayout.Layout.load(path)
        self.assertEqual([(p.id, p.stickers, p.tile) for p in back.plots],
                         [(p.id, p.stickers, p.tile) for p in lay.plots])
        self.assertEqual(back.plot_at(*lay.plots[0].middle)[0], lay.plots[0].id)


class Preview(unittest.TestCase):
    """rusemod.brushpreview: a dab's plots, what stays standing on them or is taken off, the buildings round them
    and the warnings where the result does what the map never does (here without a picture): none when the brush's
    rules hold (the hay's harvested patch, the hall's gap)."""

    def test_a_dab_on_a_with_hay_and_a_hall(self):
        fb = ts.FieldBrush
        items = fb.grid(0, 20000.0, 20000.0, 30.0, 2500.0, 3500.0, 10000.0, 7000.0)
        bx, by = fb.across(20000.0, 20000.0, 30.0, 15100.0)
        items += fb.grid(0, bx, by, 30.0, 2500.0, 3500.0, 6000.0, 3500.0)
        items += fb.grid(1, 80000.0, 80000.0, 120.0, 2500.0, 3500.0, 15000.0)       # the wheat source
        items += fb.grid(2, 80000.0, 80000.0, 120.0, 1000.0, 1000.0, 15000.0)
        items += [compact(FOIN, 21500.0, 20500.0), compact(HALL, 20000.0, 14500.0)]
        data = make_scenery([block(items, box=(0.0, 0.0, 100000.0, 100000.0))], HAY_NAMES)
        sc = scenery.Scenery(data)
        lay = maplayout.read_layout(sc, HAY_DESCS, None, None, "Test")
        from rusemod import brushpreview
        dab = scenery.FieldBrush("Wheat", 20000.0, 20000.0, 1000.0)
        hall = {HAY_NAMES[HALL]: (-800.0, -600.0, 800.0, 600.0, 2.0 * 260.0)}   # (box and gap: building_table's)
        pv = brushpreview.preview(dab, fb.LOOK, sc, data, lay, None, None, None, HAY_DESCS, buildings=hall)
        a_id, b_id = lay.plot_at(20000.0, 20000.0)[0], lay.plot_at(bx, by)[0]
        self.assertEqual([r["id"] for r in pv.plots], [a_id])
        self.assertEqual(pv.plots[0]["rows after"], {"Paille": 45})
        self.assertEqual(pv.neighbours, [b_id])
        self.assertEqual([(s["name"], s["stays"]) for s in pv.stays], [("Foin", True)])
        self.assertEqual([b["name"] for b in pv.buildings], ["MairieNormande"])
        self.assertGreaterEqual(pv.buildings[0]["nearest new standing crop m"], 2.0)
        self.assertTrue(pv.crops_laid > 0)
        self.assertEqual(pv.warnings, [])
        self.assertIsNone(pv.before)
        # a look whose fields carry no hay: the hay is taken off
        bare = brushpreview.preview(dab, dict(fb.LOOK, hay=False), sc, data, lay, None, None, None, HAY_DESCS)
        self.assertEqual([(s["name"], s["stays"]) for s in bare.stays], [("Foin", False)])
        self.assertEqual(bare.buildings, [])


if __name__ == "__main__":
    unittest.main()
