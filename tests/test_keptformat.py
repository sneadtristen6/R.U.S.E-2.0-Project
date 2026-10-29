"""The kept results' format numbers (rusemod.keptformat): each kind of kept result made on small made-up inputs (the
other tests' own: test_model, test_terrain_edit, test_groundgen, test_groundpaint, test_nav), and a fingerprint of
what it made compared with the one recorded for its kind's number. A result is kept between builds, and between app
versions, under its kind's number alone, so when code makes something else for the same inputs this test fails: bump
the kind's number in rusemod/keptformat.py and record the new fingerprint in RECORDED below (both printed). A change
that makes the same bytes passes, and keeps every player's kept results good across the update."""
import hashlib
import struct
import unittest

from rusemod import keptformat

# kind -> (its format number, the fingerprint of what it makes from the inputs below)
RECORDED = {
    "model": (1, "4acee01f8354daa04ccd754f2a9609ac"),
    "map": (2, "a20c40310c9b8067f2c877cfe210b3c8"),
    "paint": (1, "03428b5ee3145603020f8b7e5c5d4e39"),
    "movement": (1, "ff56e3139dc5b087adf9f75977c69e0f"),
    "tile": (1, "eb940f3d474c4113c9135f0b16691508"),
}


def fingerprint(*parts) -> str:
    h = hashlib.blake2b(digest_size=16)
    for p in parts:
        b = p if isinstance(p, bytes) else repr(p).encode("utf-8", "surrogatepass")
        h.update(struct.pack("<Q", len(b)) + b)
    return h.hexdigest()


def made_model() -> str:
    from test_model import FILES, model_text
    from rusemod.model import load
    return fingerprint(model_text(*load(FILES)))


def made_map() -> str:
    """The terrain step on a made-up map (a hill), and a new map's ground drawn as our own (a sea and an island)."""
    from test_groundgen import BOUNDS, island, sea, whole
    from test_terrain_edit import make_map, reader
    from test_tms import make_tms
    from rusemod.brush import Stroke
    from rusemod.groundgen import Shape, fine_cells, make_mesh
    from rusemod.terrain_edit import edit_map
    from rusemod.tms import Tms
    changed, notes = edit_map(reader(make_map()), [Stroke("hill", 1500.0, 1500.0, 600.0, height=400.0)], "Test")
    shape = Shape([whole(0.0), sea(20.0), island()], BOUNDS, -50.0)
    t = Tms(make_tms(gw=2, gh=2))
    t.cells, info = make_mesh(t, shape.h, shape.w, 16, fine_cells(t, shape))
    return fingerprint(sorted(changed.items()), notes, t.to_bytes(), info)


PAINT = [{"brush": "paint", "x": 500.0, "y": 500.0, "radius": 450.0, "colour": "#e61e1e", "edge": "hard"},
         {"brush": "paint", "x": 700.0, "y": 420.0, "radius": 300.0, "colour": "#c8aa6e", "weight": 0.7},
         {"brush": "paint", "x": 1300.0, "y": 600.0, "radius": 250.0, "colour": "#0010d2", "shape": "square",
          "dx": 1.0, "dy": 0.6},
         {"brush": "stamp", "x": 300.0, "y": 250.0, "radius": 100.0, "sx": 1000.0, "sy": 0.0},
         {"brush": "paint", "x": 1000.0, "y": 500.0, "radius": 1300.0, "colour": "#5f6f3a", "shape": "square",
          "edge": "hard", "weight": 0.4}]


def made_tiles():
    from test_groundpaint import BOUNDS, store, strokes
    from rusemod.groundpaint import paint_strokes
    s = store()
    return s, paint_strokes(s, BOUNDS, strokes(*PAINT))


def made_tile() -> str:
    _s, tiles = made_tiles()
    return fingerprint(sorted(tiles.items()))


def made_paint() -> str:
    """A map's painted pictures: the painted tiles put back into its tile set (Tmst.rebuild)."""
    s, tiles = made_tiles()
    index, chunk = s.rebuild(tiles)
    return fingerprint(index, chunk)


def made_movement() -> str:
    from test_nav import row
    from rusemod import nav
    from rusemod.cover import member
    head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
    win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
        b"roads", row().to_bytes(), row().to_bytes(), b"cover")) + b"tail", {})
    blocks = [nav.Block(x=10800.0, y=2000.0, radius=400.0, units="vehicles"),
              nav.Block(x=7000.0, y=2000.0, radius=900.0, units="all")]
    new, notes = nav.apply_blocks({member("Blitz"): win}.get, "Blitz", blocks)
    return fingerprint(new[member("Blitz")], notes)


MAKERS = {"model": made_model, "map": made_map, "paint": made_paint, "movement": made_movement, "tile": made_tile}


class FormatNumbers(unittest.TestCase):
    def test_every_kind_is_recorded(self):
        self.assertEqual(sorted(RECORDED), sorted(keptformat.FORMATS))
        self.assertEqual(sorted(MAKERS), sorted(keptformat.FORMATS))

    def test_what_each_kind_makes_is_what_its_number_was_recorded_with(self):
        wrong = []
        for kind, make in MAKERS.items():
            now = (keptformat.FORMATS[kind], make())
            if now != RECORDED[kind]:
                wrong.append(f"{kind}: recorded {RECORDED[kind]}, now {now}")
        self.assertEqual(wrong, [], "a kind of kept result comes out different: bump its number in "
                                    "rusemod/keptformat.py, then record (number, fingerprint) here")

    def test_a_number_names_the_kept_result(self):
        from unittest import mock
        from rusemod import mapkeep
        one = mapkeep.key("Blitz", ["pack"], [], None, "paint")
        self.assertEqual(one, mapkeep.key("Blitz", ["pack"], [], None, "paint"))
        self.assertNotEqual(one, mapkeep.key("Blitz", ["pack"], [], None, "movement"))   # each kind its own name
        with mock.patch.dict(keptformat.FORMATS, {"paint": keptformat.FORMATS["paint"] + 1}):
            self.assertNotEqual(one, mapkeep.key("Blitz", ["pack"], [], None, "paint"))
        with self.assertRaises(KeyError):
            keptformat.stamp("no such kind")


if __name__ == "__main__":
    unittest.main()
