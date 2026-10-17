"""The game's own 3D rocks over painted rock (rusemod.rocks): laid only where a palette rock shows on top, from
the map's own rock types by its own mix, square to the ground's slope (a tilted full transform) and sunk into it, the
same every build; the tilted transform (scenery.NewObject.up); the stroke's `rocks` switch."""
import math
import unittest
from unittest import mock

from test_tms import make_tms
from rusemod import rocks
from rusemod.brush import BrushError, Stroke, parse_strokes, strokes_toml
from rusemod.scenery import T_COMPACT, T_FULL, NewObject, encode_transform
from rusemod.tms import Q_MAX, Tms

M = 260.0
ROCK = "swatch:dday:rock"
USED = {"TypeWarrior/RocherNormandie_03": 300, "TypeWarrior/RocherNormandie_04": 100, "TypeWarrior/Pierres": 50,
        "TypeWarrior/ChampsPierres_02": 80, "TypeWarrior/MairieNormande": 4}
BOXES = {"TypeWarrior/RocherNormandie_03": (-0.69 * M, -0.6 * M, 0.0, 0.69 * M, 0.6 * M, 0.69 * M)}


def box_of(t):
    return BOXES.get(t, (-M, -M, 0.0, M, M, 0.5 * M))


class Plane:
    """A made-up ground: z = gx * x + gy * y (Tms.height_box's grid of square middles)."""

    def __init__(self, gx=0.0, gy=0.0):
        self.gx, self.gy = gx, gy

    def height_box(self, x0, y0, x1, y1, step):
        cols, rows = max(1, math.ceil((x1 - x0) / step)), max(1, math.ceil((y1 - y0) / step))
        return [[self.gx * (x0 + (c + 0.5) * step) + self.gy * (y0 + (r + 0.5) * step) for c in range(cols)]
                for r in range(rows)]


def rock_stroke(x=0.0, y=0.0, radius=30.0 * M, **kw):
    return Stroke("texture", x, y, radius, shape="square", edge="hard", texture=ROCK, **kw)


class Transform(unittest.TestCase):
    def test_upright_is_unchanged(self):
        o = NewObject("T", 10.0, 20.0, 30.0, 1.5, lift=-4.0)
        t = math.radians(30.0)
        c, s = math.cos(t) * 1.5, math.sin(t) * 1.5
        self.assertEqual(o.matrix(), (c, -s, 0.0, 10.0, s, c, 0.0, 20.0, 0.0, 0.0, 1.5, -4.0))
        for a, b in zip(NewObject("T", 10.0, 20.0, 30.0, 1.5, lift=-4.0, up=(0.0, 0.0, 1.0)).matrix(), o.matrix()):
            self.assertAlmostEqual(a, b)
        self.assertEqual(encode_transform(o.matrix())[0], T_COMPACT)

    def test_tilted_its_up_axis_is_up_and_it_stays_square(self):
        n = (0.5, -0.3, math.sqrt(1 - 0.34))
        m = NewObject("T", 0.0, 0.0, 70.0, 2.0, up=n, lift=-9.0).matrix()
        cols = [(m[0], m[4], m[8]), (m[1], m[5], m[9]), (m[2], m[6], m[10])]
        for k in range(3):
            self.assertAlmostEqual(math.sqrt(sum(v * v for v in cols[k])), 2.0)   # each axis sized
        for a, b in ((0, 1), (0, 2), (1, 2)):
            self.assertAlmostEqual(sum(cols[a][i] * cols[b][i] for i in range(3)), 0.0)   # square to each other
        for i in range(3):
            self.assertAlmostEqual(cols[2][i] / 2.0, n[i])
        x, y, z = cols   # right-handed as the upright one: x across y is up
        self.assertGreater((x[1] * y[2] - x[2] * y[1]) * z[0] + (x[2] * y[0] - x[0] * y[2]) * z[1]
                           + (x[0] * y[1] - x[1] * y[0]) * z[2], 0.0)
        self.assertEqual(m[11], -9.0)
        self.assertEqual(encode_transform(m)[0], T_FULL)


class Layer(unittest.TestCase):
    def lay(self, strokes, mesh=None, used=None, **kw):
        return rocks.rock_layer(strokes, mesh or Plane(), USED if used is None else used, box_of, seed="t", **kw)

    def test_only_the_maps_own_rocks_in_its_mix(self):
        out, said = self.lay([rock_stroke()])
        self.assertTrue(out)
        self.assertLessEqual(set(said["types"]), {t for t in USED if "Mairie" not in t})
        self.assertEqual(set(said["kinds"]), {"patch", "stones", "boulder"})   # no big boulder, no pebble on it
        b3, b4 = said["types"]["TypeWarrior/RocherNormandie_03"], said["types"]["TypeWarrior/RocherNormandie_04"]
        self.assertGreater(b3, b4)   # 3 to 1 on the map
        self.assertTrue(all(not o.solid and o.levels == 5 and o.lift <= 0.0 for o in out))

    def test_a_blank_map_its_listed_rocks_alike(self):
        # its scenery erased, its name table kept: the rocks it lists are loaded on it, laid in equal shares
        listed = {t: 0 for t in USED}
        out, said = self.lay([rock_stroke()], used=listed)
        self.assertTrue(out)
        b3, b4 = said["types"]["TypeWarrior/RocherNormandie_03"], said["types"]["TypeWarrior/RocherNormandie_04"]
        self.assertLess(abs(b3 - b4), 0.5 * (b3 + b4))
        self.assertEqual(rocks.map_mix({"TypeWarrior/Pierres": 0, "TypeWarrior/ChampsPierres_02": 7})["patch"],
                         [("TypeWarrior/ChampsPierres_02", 7)])

    def test_as_dense_as_asked_on_steep_ground(self):
        steep = Plane(gx=math.tan(math.radians(45.0)))
        out, said = self.lay([rock_stroke()], mesh=steep)
        area = (60.0 * 60.0) / 100.0   # the stroke's square, in 100 m^2
        for k in rocks.KINDS:
            if k.name in ("patch", "stones", "boulder"):
                self.assertAlmostEqual(said["kinds"][k.name] / area, k.per100, delta=k.per100 * 0.35)

    def test_fewer_on_flat_ground(self):
        flat, _ = self.lay([rock_stroke()])
        steep, _ = self.lay([rock_stroke()], mesh=Plane(gx=1.0))
        self.assertLess(len(flat), len(steep) * 0.7)
        self.assertGreater(len(flat), len(steep) * 0.35)

    def test_square_to_the_slope_and_sunk(self):
        g = math.tan(math.radians(40.0))
        out, _ = self.lay([rock_stroke()], mesh=Plane(gy=g))
        n = (0.0, -g / math.sqrt(1 + g * g), 1.0 / math.sqrt(1 + g * g))
        lean_most = max(k.lean for k in rocks.KINDS)
        for o in out:
            off = math.degrees(math.acos(max(-1.0, min(1.0, sum(o.up[i] * n[i] for i in range(3))))))
            self.assertLessEqual(off, lean_most + 0.5)
        boulders = [o for o in out if o.type.endswith("RocherNormandie_03")]
        self.assertTrue(boulders)
        for o in boulders:   # sunk 15-40% of its height
            self.assertTrue(0.15 * 0.69 * M * o.size - 0.1 <= -o.lift <= 0.4 * 0.69 * M * o.size + 0.1)

    def test_inside_the_rock_only_and_under_what_is_painted_over_it(self):
        grass = Stroke("texture", 15.0 * M, 0.0, 10.0 * M, shape="square", edge="hard", texture="swatch:dday:grass")
        out, _ = self.lay([rock_stroke(), grass])
        self.assertTrue(out)
        for o in out:
            self.assertLessEqual(max(abs(o.x), abs(o.y)), 30.0 * M)
            self.assertFalse(abs(o.x - 15.0 * M) < 9.0 * M and abs(o.y) < 9.0 * M)   # the grass on top: none
        under, _ = self.lay([grass, rock_stroke()])
        self.assertTrue(any(abs(o.x - 15.0 * M) < 9.0 * M and abs(o.y) < 9.0 * M for o in under))

    def test_the_same_every_build(self):
        self.assertEqual(self.lay([rock_stroke()])[0], self.lay([rock_stroke()])[0])

    def test_switched_off_or_no_rock_or_no_rocks_on_the_map(self):
        self.assertEqual(self.lay([rock_stroke(rocks=False)])[0], [])
        self.assertEqual(self.lay([Stroke("texture", 0.0, 0.0, 30.0 * M, texture="swatch:dday:grass")])[0], [])
        self.assertEqual(self.lay([Stroke("texture", 0.0, 0.0, 30.0 * M, texture="game:x\\roche.tgv")])[0], [])
        self.assertEqual(self.lay([rock_stroke()], used={"TypeWarrior/MairieNormande": 4})[0], [])

    def test_thinned_to_fit_and_kept_on_the_grid(self):
        out, _ = self.lay([rock_stroke()])
        few, said = self.lay([rock_stroke()], most=len(out) // 3)
        self.assertEqual(len(few), len(out) // 3)
        self.assertTrue(said["thinned"])
        inside, _ = self.lay([rock_stroke()], inside=(1e9, 1e9))
        self.assertTrue(all(o.x >= 0.0 and o.y >= 0.0 for o in inside))
        self.assertLess(len(inside), len(out) * 0.4)

    def test_on_a_real_mesh_its_slope(self):
        # test_tms's made-up mesh (2 x 2 cells of 1,000 units), a ramp rising 1 in 1 along x; the grid made fine to fit
        span = 2000.0
        mesh = make_tms(zf=lambda qx, qy: int(round((qx / Q_MAX * span + 100.0) * 10.0)))
        # a stone every 60 units or so (1,900 per 100 m^2), none leaning off the ground
        with mock.patch.multiple(rocks, CELL=25.0, TILE=16), \
                mock.patch.object(rocks, "KINDS", (rocks.RockKind("stones", ("Pierres",), 1900.0, (1.0, 1.0),
                                                                  (0.0, 0.0), 0.0, 5),)):
            out, _ = rocks.rock_layer([Stroke("texture", 1000.0, 1000.0, 600.0, shape="square", edge="hard",
                                              texture=ROCK)], Tms(mesh), {"TypeWarrior/Pierres": 1}, box_of,
                                      seed="t")
        self.assertTrue(out)
        for o in out:   # leaning back from the rise: up is (-1, 0, 1) / sqrt 2
            self.assertAlmostEqual(o.up[0], -math.sqrt(0.5), delta=0.05)
            self.assertAlmostEqual(o.up[1], 0.0, delta=0.05)


class Switch(unittest.TestCase):
    def test_rocks_is_written_only_when_off_and_read_back(self):
        for brush in ("texture", "repaint"):
            extra = {"texture": ROCK} if brush == "texture" else {}
            on = Stroke(brush, 1.0, 2.0, 3.0, **extra)
            off = Stroke(brush, 1.0, 2.0, 3.0, rocks=False, **extra)
            self.assertNotIn("rocks", strokes_toml([on]))
            self.assertIn("rocks = false", strokes_toml([off]))
            import tomllib
            self.assertFalse(parse_strokes(tomllib.loads(strokes_toml([off]))["stroke"], "t")[0].rocks)

    def test_rocks_is_for_texture_and_repaint(self):
        with self.assertRaises(BrushError):
            parse_strokes([{"brush": "paint", "x": 0, "y": 0, "radius": 1, "colour": "#ffffff",
                                       "rocks": False}], "t")
        with self.assertRaises(BrushError):
            parse_strokes([{"brush": "repaint", "x": 0, "y": 0, "radius": 1, "rocks": "no"}], "t")

    def test_repaint_hands_its_switch_to_its_rock(self):
        from test_repaint import block, ground, laid
        on, _ = laid(ground(block))
        off, _ = laid(ground(block), strokes=(Stroke("repaint", 1000.0, 1000.0, 1000.0, shape="square",
                                                     rocks=False),))
        self.assertTrue(on and all(s.rocks for s in on))
        self.assertTrue(off and not any(s.rocks for s in off))
        self.assertTrue(any(rocks.is_rock(s) for s in on))


if __name__ == "__main__":
    unittest.main()
