"""The navigation graphs in mapinfo.win (rusemod.nav): a made-up graph with one local graph, read and written back."""
import struct
import unittest

from rusemod import nav


def graph(subs=()):
    """Two circles side by side and the link where they meet; one crossing and a few index bytes."""
    g = nav.Graph(
        box=(0, 0, 8000.0),
        circles=[(2000.0, 2000.0, 1280.0, 0, 0), (4000.0, 2000.0, 1280.0, 1, 1), (0.0, 0.0, 0.0, 2, 1)],
        links=[(0, 1, 3000.0, 2000.0)],
        lists=[0, 0],
        crossings=struct.pack("<5f2HI", 1.0, 2.0, 3.0, 4.0, 2.0, 0, 0, 0),
        points=struct.pack("<2H", 2, 0) + struct.pack("<H", 1) + b"\0\0",
        subs=list(subs),
        head_rest=bytes(nav.HEADER - 20))
    return g


class Graphs(unittest.TestCase):
    def test_written_and_read_back(self):
        g = graph(subs=[graph()])
        data = g.to_bytes()
        self.assertEqual(struct.unpack_from("<4H", data, 12), (2, 1, 1, 1))  # circles, links, crossings, local graphs
        back = nav.Graph.read(data)
        self.assertEqual(back.to_bytes(), data)
        self.assertEqual((back.circles, back.links, back.lists), (g.circles, g.links, g.lists))
        self.assertEqual(len(back.subs), 1)
        self.assertEqual(back.subs[0].to_bytes(), graph().to_bytes())
        self.assertEqual(back.links_of(1), [0])
        self.assertEqual(back.at(2500.0, 2000.0), [0])
        self.assertEqual(back.at(3000.0, 2000.0), [0, 1])  # where they meet

    def test_mistakes(self):
        data = graph().to_bytes()
        with self.assertRaisesRegex(nav.NavError, "too short"):
            nav.Graph.read(data[:40])
        bad = bytearray(data)
        struct.pack_into("<H", bad, 12, 5)  # says five circles
        with self.assertRaisesRegex(nav.NavError, "don't match"):
            nav.Graph.read(bytes(bad))


def row():
    """Three circles in a row, A (r 3200) at x 2000, B (r 3200) at x 7000, C (r 1600) at x 10000, linked A-B and
    B-C; one crossing through B from link 0 to link 1."""
    return nav.Graph(
        box=(0, 0, 16000.0),
        circles=[(2000.0, 2000.0, 3200.0, 0, 0), (7000.0, 2000.0, 3200.0, 1, 0), (10000.0, 2000.0, 1600.0, 3, 1),
                 (0.0, 0.0, 0.0, 4, 1)],
        links=[(0, 1, 4500.0, 2000.0), (1, 2, 9000.0, 2000.0)],
        lists=[0, 0, 1, 1],
        crossings=struct.pack("<5f2HI", 4500.0, 2000.0, 9000.0, 2000.0, 4500.0, 0, 1, 7),
        points=struct.pack("<H3H", 6, 0, 1, 2),
        head_rest=bytes(nav.HEADER - 20))


class Blocking(unittest.TestCase):
    def test_a_circle_emptied_and_one_shrunk(self):
        g = row()
        counts = g.block([(10800.0, 2000.0, 400.0)])  # C's middle is 800 away: C keeps 400 clear, too small
        self.assertEqual(counts, {"emptied": 1, "shrunk": 0, "links": 1, "crossings": 1})
        self.assertEqual([c[2] for c in g.circles[:-1]], [3200.0, 3200.0, 0.0])
        self.assertEqual(g.links, [(0, 1, 4500.0, 2000.0)])
        self.assertEqual([g.links_of(i) for i in range(3)], [[0], [0], []])
        self.assertEqual(g.crossings, b"")
        self.assertEqual(nav.Graph.read(g.to_bytes()).to_bytes(), g.to_bytes())
        g = row()
        counts = g.block([(1000.0, 5500.0, 500.0)])  # A's middle is 3640 away: A shrinks to keep clear
        self.assertEqual((counts["shrunk"], counts["emptied"], counts["links"]), (1, 0, 0))
        self.assertEqual(g.circles[0][2], 2880.0)  # 3140 clear, in steps of 320
        self.assertEqual(len(g.crossings), 28)  # the crossing's links both stay
        g = row()
        g.block([(4500.0, 2000.0, 200.0)])  # right on A-B's meeting point: both shrink, the link goes
        self.assertEqual(g.links, [(1, 2, 9000.0, 2000.0)])
        self.assertEqual(struct.unpack_from("<2H", g.crossings, 20) if g.crossings else None, None)
        self.assertEqual(g.points, row().points)  # the index isn't touched

    def test_the_file(self):
        import tomllib
        blocks = [nav.Block(1.0, 2.0, 3.0), nav.Block(4.0, 5.0, 6.0, "vehicles")]
        text = nav.blocks_toml(blocks, "two")
        self.assertEqual(nav.parse_blocks(tomllib.loads(text)["block"]), blocks)
        for bad, why in (({"x": 1, "y": 2}, "radius is missing"), ({"x": 1, "y": 2, "radius": -1}, "more than 0"),
                         ({"x": 1, "y": 2, "radius": 3, "units": "boats"}, "units must be"),
                         ({"x": 1, "y": 2, "radius": 3, "who": 1}, "unknown key")):
            with self.assertRaisesRegex(nav.NavError, why):
                nav.parse_blocks([bad])


class Built(unittest.TestCase):
    """maps/<map>/movement.toml in a mod, built into the modded copy's DataMap_Win.dat."""

    def test_blocked_ground_in_the_modded_copy(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from fixtures import make_edat
        from test_build import PACK, write_mod
        from rusemod.build import build_and_write, load_mod
        from rusemod.cover import member
        from rusemod.edat import Edat
        from ruse_mod_engine import sdb
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "steamapps" / "common" / "R.U.S.E"
            rev = game / "Data" / "PC" / "190852"
            rev.mkdir(parents=True)
            (game / "RUSE.exe").write_bytes(b"MZ")
            (rev / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
            win = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
                b"roads", row().to_bytes(), row().to_bytes(), b"cover")) + b"tail", {})
            (rev / "DataMap_Win.dat").write_bytes(
                make_edat([("dir", "datasmap/blitz/".replace("/", "\\"), [("file", "mapinfo.win", win)])]))
            (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            folder = write_mod(root / "mods", "walls", {})
            (folder / "maps" / "Blitz").mkdir(parents=True)
            (folder / "maps" / "Blitz" / "movement.toml").write_text(
                '[[block]]\nx = 10800.0\ny = 2000.0\nradius = 400.0\nunits = "vehicles"\n', encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            self.assertIn("movement: Blitz, from walls", lines)
            arc = Edat((root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
            out = bytes(arc.read(arc.find(member("Blitz"))))
            self.assertEqual(hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + out[24:]).digest(), out[8:24])
            bufs = sdb.split_mapinfo(out)[1]
            self.assertEqual(bufs[1], row().to_bytes())  # infantry untouched
            self.assertEqual(nav.Graph.read(bufs[2]).circles[2][2], 0.0)  # vehicles: C emptied
            self.assertEqual((bufs[0], bufs[3]), (b"roads", b"cover"))


if __name__ == "__main__":
    unittest.main()
