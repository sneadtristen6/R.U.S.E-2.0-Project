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


if __name__ == "__main__":
    unittest.main()
