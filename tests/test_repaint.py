"""Repaint what moved, by rules (rusemod.repaint, Map Paint plan step 8): the ground a mod's brushes moved, inside a
repaint stroke, painted by its new shape with the theme's palette (rock where steep, mud under a new lake, sand on its
shore, grass elsewhere); on test_tms's made-up meshes (2 x 2 cells of 1,000 map units), the grid's squares made
small to fit."""
import tomllib
import unittest
from unittest import mock

from test_tms import make_tms
from rusemod import repaint
from rusemod.brush import BrushError, Stroke, parse_strokes, strokes_toml
from rusemod.tms import Q_MAX

SPAN = 2000.0   # the made-up map, each way (2 cells of 1,000)


def ground(zf):
    """A made-up mesh whose height at world (x, y) is zf(x, y) (world units over its z bounds, -100 at the bottom,
    0.1 a quantum)."""
    return make_tms(zf=lambda qx, qy: int(round((zf(qx / Q_MAX * SPAN, qy / Q_MAX * SPAN) + 100.0) * 10.0)))


FLAT = ground(lambda x, y: 0.0)


def block(x, y):   # a flat-topped block 600 high, steep all round (the mesh's points: 125 apart)
    return 600.0 if 600.0 <= x <= 1400.0 and 600.0 <= y <= 1400.0 else 0.0   # (its sides: 500-625, 1375-1500)


def pit(x, y):     # a pit 60 deep, its sides a gentle slope out to 300 from its middle
    d = max(abs(x - 1000.0), abs(y - 1000.0))
    return -60.0 if d <= 250.0 else max(-60.0, -60.0 + (d - 250.0) * 0.3) if d < 450.0 else 0.0


SMALL = dict(CELL=50.0, MOVED=10.0, SHORE=15.0)
EVERYWHERE = Stroke("repaint", 1000.0, 1000.0, 1000.0, shape="square")
BEACH = Stroke("repaint", 1000.0, 1000.0, 1000.0, shape="square", beach=True)   # sand round new lakes too


def laid(new, waters=(), strokes=(EVERYWHERE,), old=FLAT):
    with mock.patch.multiple(repaint, **SMALL):
        return repaint.expand(list(strokes), old, new, list(waters))


def material_at(strokes, x, y):
    """The swatch of the last stroke whose footprint holds (x, y), as the paint lays it (later on top)."""
    hit = [s for s in strokes if s.footprint().t2(x, y) < 1.0]
    return hit[-1].texture.split(":")[-1] if hit else None


class Rules(unittest.TestCase):
    def test_the_rules(self):
        self.assertEqual(repaint.material(45.0, 100.0, [], []), "rock")      # steep: rock, even by water
        self.assertEqual(repaint.material(45.0, 100.0, [200.0], [200.0]), "rock")
        self.assertEqual(repaint.material(5.0, 100.0, [200.0], [200.0]), "mud")    # under a lake
        self.assertEqual(repaint.material(5.0, 300.0, [], [200.0]), "sand")         # just over it
        self.assertEqual(repaint.material(5.0, 200.0 + repaint.SHORE, [], [200.0]), "grass")
        self.assertEqual(repaint.material(5.0, 100.0, [], []), "grass")
        self.assertEqual((repaint.STEEP, repaint.SHORE, repaint.MOVED), (40.0, 3.0 * 260.0, 2.0 * 260.0))

    def test_nothing_moved_nothing_laid(self):
        out, said = laid(FLAT)
        self.assertEqual(out, [])
        self.assertIn("no ground moved enough", said)

    def test_a_raised_block_rock_round_its_sides_grass_on_top(self):
        out, said = laid(ground(block))
        self.assertTrue(out)
        self.assertEqual({s.brush for s in out}, {"texture"})
        self.assertTrue(all(s.mask == "ragged" and s.edge == "hard" and s.shape == "line" for s in out))
        self.assertEqual(material_at(out, 1000.0, 1000.0), "grass")   # its flat top
        self.assertEqual(material_at(out, 560.0, 1000.0), "rock")     # its steep sides
        self.assertEqual(material_at(out, 1440.0, 1000.0), "rock")
        self.assertIsNone(material_at(out, 200.0, 200.0))             # the ground that didn't move: as it was
        self.assertIn("squares of rock", said)
        self.assertIn("squares of grass", said)
        rows = {round(s.y, 6) for s in out}   # one stroke a run along x: rock, grass, rock at most a row
        self.assertLessEqual(len(out), 3 * len(rows))

    def test_a_new_lake_mud_under_it_sand_round_it_when_asked(self):
        lake = Stroke("water", 1000.0, 1000.0, 400.0, level=-30.0)
        out, _said = laid(ground(pit), [lake], strokes=(BEACH,))
        self.assertEqual(material_at(out, 1000.0, 1000.0), "mud")      # its bed: under the surface
        self.assertEqual(material_at(out, 1000.0, 1370.0), "sand")     # over it by less than SHORE
        plain = laid(ground(pit), [lake])[0]   # beach off (the default, as D-Day's rivers and marshes): no sand
        self.assertEqual(material_at(plain, 1000.0, 1000.0), "mud")
        self.assertEqual(material_at(plain, 1000.0, 1370.0), "grass")
        self.assertFalse(any(s.texture.endswith(":sand") for s in plain))
        without = laid(ground(pit))[0]
        self.assertEqual(material_at(without, 1000.0, 1000.0), "grass")  # no lake: only lowered ground

    def test_a_new_lakes_shore_though_it_didnt_move(self):
        """A lake's shore hardly moves: its sand (with beach) and a bed under the water that wasn't dug are laid all
        the same; unmoved ground nowhere near a new lake stays as it was."""
        out, _said = laid(FLAT, [Stroke("water", 1000.0, 1000.0, 300.0, level=-10.0)], strokes=(BEACH,))
        self.assertEqual(material_at(out, 1000.0, 1000.0), "sand")    # dry (over the level), within SHORE of it
        self.assertEqual(material_at(out, 1000.0, 1350.0), "sand")    # its footprint grown by SHORE_REACH
        self.assertIsNone(material_at(out, 200.0, 200.0))
        self.assertEqual(laid(FLAT, [Stroke("water", 1000.0, 1000.0, 300.0, level=-10.0)])[0], [])   # no beach
        high = laid(FLAT, [Stroke("water", 1000.0, 1000.0, 300.0, level=-40.0)], strokes=(BEACH,))[0]
        self.assertEqual(high, [])   # 40 under the ground: no shore
        for stroke in (EVERYWHERE, BEACH):   # over the ground: a bed, beach or not
            wet = laid(FLAT, [Stroke("water", 1000.0, 1000.0, 300.0, level=20.0)], strokes=(stroke,))[0]
            self.assertEqual(material_at(wet, 1000.0, 1000.0), "mud")
            self.assertEqual(material_at(wet, 1000.0, 1360.0), "sand" if stroke.beach else None)

    def test_only_inside_the_stroke_and_by_the_height_it_says(self):
        part = Stroke("repaint", 700.0, 1000.0, 120.0, shape="square")
        out, _said = laid(ground(block), strokes=(part,))
        self.assertTrue(out)
        self.assertTrue(all(abs(s.x - 700.0) <= 400.0 for s in out))
        self.assertEqual(laid(ground(block), strokes=(Stroke("repaint", 1000.0, 1000.0, 1000.0, shape="square",
                                                             height=700.0),))[0], [])   # moved less than it asks

    def test_a_map_that_starts_flat(self):
        """A blank map (its first height stroke levels the whole map, as Blank Terrain starts and the Studio's blank
        maps draw their ground as our own): what moved is measured from that flat start, not from the copied map's
        own hills, which the level moved everywhere."""
        hills = ground(lambda x, y: 200.0 if (int(x // 250) + int(y // 250)) % 2 else -50.0)
        start = Stroke("level", 1000.0, 1000.0, 1500.0, level=0.0, weight=1.0, shape="square", edge="hard")
        self.assertEqual(repaint.start_level([start, Stroke("hill", 1.0, 1.0, 50.0, height=10.0)], hills), 0.0)
        self.assertIsNone(repaint.start_level([Stroke("hill", 1.0, 1.0, 50.0, height=10.0), start], hills))
        self.assertIsNone(repaint.start_level([Stroke("level", 1000.0, 1000.0, 300.0, level=0.0, weight=1.0)],
                                              hills))   # a level over part of the map: not a flat start
        self.assertIsNone(repaint.start_level([], hills))
        with mock.patch.multiple(repaint, **SMALL):
            everything, _said = repaint.expand([EVERYWHERE], hills, ground(block), [])
            out, said = repaint.expand([EVERYWHERE], hills, ground(block), [], start=0.0)
        self.assertEqual(material_at(everything, 200.0, 200.0), "grass")   # from the hills: the whole square
        self.assertIsNone(material_at(out, 200.0, 200.0))                  # from the flat start: only the block
        self.assertEqual(material_at(out, 1000.0, 1000.0), "grass")
        self.assertEqual(material_at(out, 560.0, 1000.0), "rock")
        self.assertEqual((out, said), laid(ground(block)))   # the same as from flat old ground

    def test_over_a_blank_maps_coat(self):
        """Blank Terrain's one-colour coat over the whole map comes first in its paint: what repaint lays goes over
        it (under it, it was never seen), and under the rest."""
        coat = Stroke("paint", 1000.0, 1000.0, 1500.0, colour="#5f6f3a", weight=1.0, shape="square", edge="hard")
        dab = Stroke("paint", 500.0, 500.0, 100.0, colour="#000000")
        self.assertEqual(repaint.coats([coat, dab], FLAT), 1)
        self.assertEqual(repaint.coats([coat, coat, dab], FLAT), 2)
        self.assertEqual(repaint.coats([dab, coat], FLAT), 0)
        self.assertEqual(repaint.coats([Stroke("paint", 1000.0, 1000.0, 300.0, colour="#5f6f3a", weight=1.0,
                                               shape="square", edge="hard")], FLAT), 0)   # part of the map
        self.assertEqual(repaint.coats([Stroke("paint", 1000.0, 1000.0, 1500.0, colour="#5f6f3a", weight=1.0,
                                               shape="square")], FLAT), 0)   # a soft edge: not a full coat
        self.assertEqual(repaint.coats([], FLAT), 0)

    def test_heights_over_a_box(self):
        """Tms.height_box: the ground on fine squares over part of the map, the same sums as height_grid's over all
        of it (where the squares fall on the same places)."""
        from rusemod.tms import Tms
        t = Tms(ground(block))
        x0, y0, _z0, x1, y1, _z1 = t.bounds
        step = (x1 - x0) / 40
        whole = t.height_grid(40)
        part = t.height_box(x0 + 10 * step, y0 + 5 * step, x0 + 30 * step, y0 + 25 * step, step)
        self.assertEqual((len(part), len(part[0])), (20, 20))
        for j in range(20):
            for i in range(20):
                self.assertAlmostEqual(part[j][i], whole[j + 5][i + 10], places=6)
        self.assertTrue(all(z is None for z in t.height_box(x1 + 100.0, y1 + 100.0, x1 + 200.0, y1 + 200.0, step)[0]))

    def test_in_the_file(self):
        item = {"brush": "repaint", "x": 1.0, "y": 2.0, "radius": 3.0, "shape": "square", "theme": "dday",
                "height": 520.0, "beach": True}
        made = parse_strokes([item])
        self.assertEqual((made[0].theme, made[0].height, made[0].beach), ("dday", 520.0, True))
        self.assertIn("beach = true", strokes_toml(made))
        self.assertNotIn("beach", strokes_toml(parse_strokes([{**item, "beach": False}])))
        for bad in ({**item, "beach": "yes"}, {"brush": "paint", "x": 1.0, "y": 1.0, "radius": 1.0,
                                               "colour": "#000000", "beach": True}):
            with self.assertRaises(BrushError):
                parse_strokes([bad])
        self.assertEqual(parse_strokes(tomllib.loads(strokes_toml(made))["stroke"]), made)
        self.assertEqual(parse_strokes([{"brush": "repaint", "x": 1.0, "y": 2.0, "radius": 3.0}])[0].theme, "")
        for bad, says in (({**item, "theme": "moon"}, "theme must be one of"), ({**item, "height": -1.0}, "below 0"),
                          ({"brush": "paint", "x": 1.0, "y": 1.0, "radius": 1.0, "colour": "#000000",
                            "theme": "dday"}, "for the repaint brush")):
            with self.assertRaises(BrushError) as caught:
                parse_strokes([bad])
            self.assertIn(says, str(caught.exception))
        self.assertEqual(Stroke("repaint", 1.0, 2.0, 3.0).height_at(1.0, 2.0, 55.0), 55.0)   # the ground stays

    def test_the_build_keeps_it_apart_from_the_ground_brushes(self):
        """A mod's terrain.toml with a hill and a repaint: the hill reshapes the ground, the repaint goes to the
        build's paint step (info.repaint), saved and read back by the Studio."""
        import tempfile
        from pathlib import Path
        from rusemod.build import load_mod
        from ruse_studio.api import StudioApi
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(home=Path(tmp, "home"), game_dir=Path(tmp, "game"))
            api.new_mod("Hills", "map")
            got = api.terrain_add("SuperCrossRoads4", [
                {"brush": "hill", "x": 1.0, "y": 2.0, "radius": 300.0, "height": 2600.0},
                {"brush": "repaint", "x": 1.0, "y": 2.0, "radius": 900.0, "shape": "square", "theme": "dday"}])
            folder = Path(got["saved"]).parents[2]
            info, _ops = load_mod(folder)
            self.assertEqual([s.brush for s in info.terrain["SuperCrossRoads4"]], ["hill"])
            self.assertEqual([(s.brush, s.theme) for s in info.repaint["SuperCrossRoads4"]], [("repaint", "dday")])

    def test_the_studio_shows_what_the_build_lays(self):
        """StudioApi.repaint_preview: the map's ground with the mod's ground brushes applied as the build applies them
        (terrain_edit.edit_map), then the rules, worked out in a job once and kept; nothing without a repaint."""
        import tempfile
        import time
        from pathlib import Path
        import rusemod.terrain_edit as te
        import ruse_studio.groundtex_calls as calls
        from ruse_studio.api import StudioApi

        class Pack:
            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

            def find(self, member):
                return member

            def read(self, member):
                return FLAT

        edits = []

        def edit_map(read, strokes, name):
            edits.append([s.brush for s in strokes])
            return {"output\\highdef.tms": ground(block)}, []
        with tempfile.TemporaryDirectory() as tmp:
            api = StudioApi(home=Path(tmp, "home"), game_dir=Path(tmp, "game"))
            api.new_mod("Hills", "map")
            api.terrain_add("SuperCrossRoads4", [{"brush": "hill", "x": 1000.0, "y": 1000.0, "radius": 500.0,
                                                  "height": 600.0}])
            self.assertEqual(api.repaint_preview("SuperCrossRoads4"), {"strokes": [], "said": ""})
            api.terrain_add("SuperCrossRoads4", [{"brush": "repaint", "x": 1000.0, "y": 1000.0, "radius": 1000.0,
                                                  "shape": "square"},
                                                 {"brush": "paint", "x": 5.0, "y": 5.0, "radius": 5.0,
                                                  "colour": "#000000"}])
            pack = Path(tmp, "SuperCrossRoads4.dat")
            pack.write_bytes(b"made-up")
            with mock.patch.object(calls, "find_pack", lambda game, name: pack), \
                    mock.patch.object(api, "_game", lambda: Path(tmp)), \
                    mock.patch.object(calls.Edat, "open", lambda path: Pack()), \
                    mock.patch.object(te, "edit_map", edit_map), mock.patch.multiple(repaint, **SMALL):
                job = api.repaint_preview("SuperCrossRoads4")["job"]
                end = time.time() + 30
                while api.job(job)["state"] == "running" and time.time() < end:
                    time.sleep(0.05)
                self.assertEqual(api.job(job)["state"], "done", api.job(job))
                got = api.repaint_preview("SuperCrossRoads4")
                self.assertEqual(edits, [["hill"]])   # the ground brushes only, once: then kept
                self.assertTrue(got["strokes"])
                self.assertEqual({s["brush"] for s in got["strokes"]}, {"texture"})
                self.assertIn("rock", got["said"])
                again = parse_strokes(got["strokes"])   # the terrain file's own keys: the page lays them as strokes
                self.assertEqual(material_at(again, 1000.0, 1000.0), "grass")


if __name__ == "__main__":
    unittest.main()
