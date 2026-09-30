"""Painted cover and blocked ground (rusemod.cover): a made-up mapinfo.win, painted and read back, and a mod's
maps/<map>/cover.toml built into the modded copy's DataMap_Win.dat."""
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat
from test_build import PACK, write_mod
from rusemod import cover
from rusemod.build import build_and_write, load_mod, BuildError
from rusemod.edat import Edat
from ruse_mod_engine import sdb

WIDTH = 8000.0  # a map 8 cells wide: 1000 map units a cell
OPEN, WOOD, WALL = 0x01, 0x09, 0x05  # a leaf's first byte keeps bit 0 (the leaf mark)


def leaf(a, b, c, d):
    return a | b << 8 | c << 16 | d << 24 | 1


def mapinfo() -> bytes:
    """A mapinfo.win whose grid is 8×8 cells. The root's quarter at x 4-7, y 0-3 is one leaf (a byte for each 2×2
    cells); its other quarters are nodes of four leaves (a byte a cell). Cells (0-1, 0-1) are a wood, (6-7, 6-7) are
    blocked, the rest is open."""
    root_at = 0x20
    kid = [root_at + 16 * k for k in (1, 2, 3)]
    plain = [leaf(OPEN, OPEN, OPEN, OPEN)] * 4
    nodes = [[kid[0], leaf(OPEN, OPEN, OPEN, OPEN), kid[1], kid[2]],
             [leaf(WOOD, WOOD, WOOD, WOOD)] + plain[1:], plain, plain[:3] + [leaf(WALL, WALL, WALL, WALL)]]
    prefix = struct.pack("<4ffIII", 0.0, 0.0, WIDTH, WIDTH, 960.0, 0, 0, root_at)  # 28 bytes, then the root
    buf3 = sdb.serialize({"ver": 2, "prefix": prefix, "node_start": root_at, "nodes": nodes, "tail": b""})
    head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, WIDTH, WIDTH)
    body = b"".join(struct.pack("<I", len(b)) + b for b in (b"graph", b"grid1", b"grid2", buf3)) + b"tail"
    return sdb.replace_buffer4(head + body, buf3)  # the checksum made


def info_and_ops(folder):
    return load_mod(folder)


def cells(win):
    g = cover.grid(win)
    return g["size"], g["cells"]


class Painting(unittest.TestCase):
    def test_the_made_up_grid(self):
        size, c = cells(mapinfo())
        self.assertEqual(size, 8)
        self.assertEqual([c[j * 8 + i] & 0x0C for j in range(2) for i in range(2)], [8, 8, 8, 8])  # the wood
        self.assertEqual(c[7 * 8 + 7] & 0x0C, 4)  # the blocked corner
        self.assertEqual(sum(1 for b in c if b & 0x0C), 8)

    def test_nothing_painted_is_the_same_file(self):
        win = mapinfo()
        self.assertEqual(cover.paint(win, []), win)

    def test_a_circle_paints_the_cells_whose_centres_are_in_it(self):
        win = mapinfo()
        out = cover.paint(win, [cover.Paint(4500.0, 4500.0, 1200.0)])  # cell centres at 4500 ± 1000 around (4, 4)
        self.assertEqual(hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + out[24:]).digest(), out[8:24])
        head, bufs, trail = sdb.split_mapinfo(out)
        self.assertEqual((bufs[:3], trail), ([b"graph", b"grid1", b"grid2"], b"tail"))  # the rest kept as it was
        tree = sdb.parse(bufs[3])  # the SDB's own checksum and tree are right
        self.assertEqual(sdb.serialize(tree), bufs[3])
        size, c = cells(out)
        painted = sorted((i, j) for j in range(size) for i in range(size) if c[j * 8 + i] & 0x08 and (i > 1 or j > 1))
        self.assertEqual(painted, [(3, 4), (4, 3), (4, 4), (4, 5), (5, 4)])  # a plus: the corners are 1414 away
        self.assertEqual(c[7 * 8 + 7] & 0x0C, 4)  # other cells and layers untouched

    def test_erasing_and_the_blocked_layer(self):
        out = cover.paint(mapinfo(), [cover.Paint(1000.0, 1000.0, 1500.0, erase=True),   # the wood cleared
                                      cover.Paint(7000.0, 7000.0, 800.0, "blocked", erase=True),
                                      cover.Paint(500.0, 7500.0, 400.0, "blocked")])
        size, c = cells(out)
        self.assertEqual(sum(1 for b in c if b & 0x08), 0)
        self.assertEqual([i for i in range(64) if c[i] & 0x04], [7 * 8])  # the corner moved to the other side
        c = cells(cover.paint(mapinfo(), [cover.Paint(7500.0, 7500.0, 400.0, "blocked", erase=True)]))[1]
        self.assertEqual([i for i in range(64) if c[i] & 0x04], [54, 55, 62])  # one cell of the four
        self.assertEqual(cover.paint(mapinfo(), [cover.Paint(90000.0, 90000.0, 500.0)]), mapinfo())  # off the map

    def test_whole_leaves_stay_leaves(self):
        win = mapinfo()
        out = cover.paint(win, [cover.Paint(5000.0, 1000.0, 750.0)])  # exactly the 2×2 cells of one of the big
        self.assertEqual(len(sdb.parse(sdb.split_mapinfo(out)[1][3])["nodes"]), 4)  # leaf's bytes: no node added
        self.assertEqual([i for i in range(64) if cells(out)[1][i] & 0x08 and i % 8 > 1], [4, 5, 12, 13])
        out = cover.paint(win, [cover.Paint(4500.0, 500.0, 400.0)])  # one cell of it: that leaf becomes a node
        self.assertEqual(len(sdb.parse(sdb.split_mapinfo(out)[1][3])["nodes"]), 5)
        out = cover.paint(win, [cover.Paint(1500.0, 3500.0, 400.0)])  # a byte a cell already: no node added
        self.assertEqual(len(sdb.parse(sdb.split_mapinfo(out)[1][3])["nodes"]), 4)
        size, c = cells(out)
        self.assertEqual([i for i in range(64) if c[i] & 0x08 and i >= 16], [3 * 8 + 1])


class File(unittest.TestCase):
    def test_read_and_written(self):
        paints = [cover.Paint(1.0, 2.0, 3.0), cover.Paint(4.0, 5.0, 6.0, "blocked", True)]
        import tomllib
        text = cover.paints_toml(paints, "two circles")
        self.assertTrue(text.startswith("# two circles"))
        self.assertEqual(cover.parse_paints(tomllib.loads(text)["paint"]), paints)
        for bad, why in (({"x": 1, "y": 2}, "radius is missing"), ({"x": 1, "y": 2, "radius": 0}, "more than 0"),
                         ({"x": 1, "y": 2, "radius": 3, "layer": "town"}, "layer must be"),
                         ({"x": 1, "y": 2, "radius": 3, "colour": 1}, "unknown key"),
                         ({"x": "1", "y": 2, "radius": 3}, "must be a number")):
            with self.assertRaisesRegex(cover.CoverError, why):
                cover.parse_paints([bad])
        self.assertEqual(cover.member("SuperCrossRoads4"), "datasmap/supercrossroads4/mapinfo.win".replace("/", "\\"))


class Built(unittest.TestCase):
    """maps/<map>/cover.toml in a mod, built into the modded copy's DataMap_Win.dat (MOD_FORMAT §8)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        rev = self.game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        self.data = make_edat([("dir", "datasmap/blitz/".replace("/", "\\"), [("file", "mapinfo.win", mapinfo())])])
        (rev / "DataMap_Win.dat").write_bytes(self.data)
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, mod_id, text, map_name="Blitz"):
        folder = write_mod(self.root / "mods", mod_id, {})
        (folder / "maps" / map_name).mkdir(parents=True)
        (folder / "maps" / map_name / "cover.toml").write_text(text, encoding="utf-8")
        return folder

    def test_painted_cover_goes_into_the_modded_copy(self):
        folder = self.mod("wood", '[[paint]]\nx = 4500.0\ny = 4500.0\nradius = 1200.0\n')
        self.assertEqual(len(load_mod(folder)[0].cover["Blitz"]), 1)
        lines = []
        result = build_and_write(self.game, [load_mod(folder)], instance=self.root / "copy", say=lines.append)
        self.assertEqual(result.errors, [], lines)
        self.assertIn("cover: Blitz, from wood", lines)
        arc = Edat((self.root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
        size, c = cells(bytes(arc.read(arc.find(cover.member("Blitz")))))
        self.assertTrue(c[4 * 8 + 4] & 0x08)
        self.assertEqual((self.game / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes(), self.data)  # untouched

    def test_the_studio_brushes_in_terrain_toml(self):
        """The Studio's cover and uncover brushes are saved with the other strokes; the build paints them on the
        cover grid (after cover.toml's circles) and leaves the ground files alone."""
        from rusemod.brush import parse_strokes, strokes_toml
        folder = self.mod("brushed", '[[paint]]\nx = 1000.0\ny = 1000.0\nradius = 1500.0\nerase = true\n')
        strokes = parse_strokes([{"brush": "cover", "x": 4500.0, "y": 4500.0, "radius": 1200.0},
                                 {"brush": "uncover", "x": 4500.0, "y": 4500.0, "radius": 400.0}])
        self.assertEqual([s.height_at(4500.0, 4500.0, 7.0) for s in strokes], [7.0, 7.0])  # the ground stays
        (folder / "maps" / "Blitz" / "terrain.toml").write_text(strokes_toml(strokes), encoding="utf-8")
        info, _ops = load_mod(folder)
        self.assertEqual(info.terrain, {})  # nothing for the ground files
        self.assertEqual([(p.radius, p.erase) for p in info.cover["Blitz"]], [(1500.0, True), (1200.0, False), (400.0, True)])
        lines = []
        result = build_and_write(self.game, [info_and_ops(folder)], instance=self.root / "copy3", say=lines.append)
        self.assertEqual(result.errors, [], lines)
        arc = Edat((self.root / "copy3" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
        size, c = cells(bytes(arc.read(arc.find(cover.member("Blitz")))))
        self.assertEqual(sorted(i for i in range(64) if c[i] & 0x08), [3 * 8 + 4, 4 * 8 + 3, 4 * 8 + 5, 5 * 8 + 4])
        # the wood cleared by cover.toml, the plus painted by the brush, its middle taken away again

    def test_the_map_view_gets_the_grid(self):
        import base64
        from ruse_studio.api import StudioApi, StudioError
        api = StudioApi(index_path=self.root / "none.sqlite", game_dir=self.game, home=self.root / "home")
        got = api.map_cover("Blitz")
        self.assertEqual((got["size"], got["box"]), (8, [0.0, 0.0, WIDTH, WIDTH]))
        bits = base64.b64decode(got["bits"])
        self.assertEqual([i for i in range(64) if bits[i >> 3] >> (i & 7) & 1], [0, 1, 8, 9])  # the wood only
        with self.assertRaisesRegex(StudioError, "no cover grid"):
            api.map_cover("Nowhere")

    def test_mistakes(self):
        with self.assertRaisesRegex(BuildError, "unknown key 'circle'"):
            load_mod(self.mod("bad", '[[circle]]\nx = 1\n'))
        folder = self.mod("nomap", '[[paint]]\nx = 1.0\ny = 1.0\nradius = 1.0\n', "Nowhere")
        result = build_and_write(self.game, [load_mod(folder)], instance=self.root / "copy2", say=lambda line: None)
        self.assertIn("Nowhere has no", " ".join(f.message for f in result.errors))


if __name__ == "__main__":
    unittest.main()
