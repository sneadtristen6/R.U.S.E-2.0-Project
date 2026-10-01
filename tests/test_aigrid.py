"""The AI's map grid (rusemod.aigrid): a made-up mapinfo.win whose cover grid and movement a mod changes, the AI grid
following them where they changed and kept as it was everywhere else."""
import struct
import unittest

from rusemod import aigrid, cover, nav
from ruse_mod_engine import sdb

SIDE = 8                    # AI cells a side: a map of 8 × 26,000 map units
R = 32                      # cover cells a side: 6,500 map units each, 4 × 4 to an AI cell
WIDTH = SIDE * aigrid.CELL
OPEN, WOOD, WALL = 0x01, 0x09, 0x05  # a cover cell's byte keeps bit 0 (the leaf mark)


def cover_grid(cells) -> bytes:
    """An SDB holding `cells` (R × R bytes, row by row), every level of the tree down to cells of one byte."""
    nodes = []

    def node(x, y, size) -> int:
        k = len(nodes)
        nodes.append(None)
        h = size // 2
        kids = []
        for qx, qy in ((x, y), (x + h, y), (x, y + h), (x + h, y + h)):
            if h == 2:
                bs = [cells[(qy + b) * R + qx + a] for b, a in ((0, 0), (0, 1), (1, 0), (1, 1))]
                kids.append(bs[0] | bs[1] << 8 | bs[2] << 16 | bs[3] << 24 | 1)
            else:
                kids.append(0x20 + 16 * node(qx, qy, h))
        nodes[k] = kids
        return k
    node(0, 0, R)
    prefix = struct.pack("<4ffIII", 0.0, 0.0, WIDTH, WIDTH, WIDTH / R, 0, 0, 0x20)
    return sdb.serialize({"ver": 2, "prefix": prefix, "node_start": 0x20, "nodes": nodes, "tail": b""})


def ai_tail(cells) -> bytes:
    """The tail: no records, then the AI grid of SIDE × SIDE cells (`cells`: (byte 0, byte 1) each)."""
    grid = struct.pack("<II", SIDE, SIDE) + b"".join(bytes(c) for c in cells)
    return struct.pack("<II", 28, 0) + struct.pack("<I", len(grid)) + grid


def mapinfo(cells, ai, vehicles=b"vehicles") -> bytes:
    head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, WIDTH, WIDTH)
    return nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
        b"roads", b"infantry", vehicles, cover_grid(cells))) + ai_tail(ai), {})


def plain():
    """Open ground; the AI grid's clearance all 127, no forest, no tree lines."""
    return [OPEN] * (R * R), [(0, 127)] * (SIDE * SIDE)


class Refreshed(unittest.TestCase):
    def test_the_rules_on_a_made_up_grid(self):
        cells, ai = plain()
        win = mapinfo(cells, ai)
        f, b, n = aigrid._shares(win, SIDE, SIDE)
        self.assertEqual((f, b, n), ([0.0] * 64, [0.0] * 64, [16] * 64))  # 4 × 4 cover cells to an AI cell
        self.assertEqual(aigrid._clearance([c == 0 for c in range(64)], SIDE, SIDE)[:6], [0, 32, 64, 95, 127, 127])
        self.assertEqual(aigrid._clearance([c == 0 for c in range(64)], SIDE, SIDE)[9], 45)  # 1.41 cells off

    def test_an_unchanged_map_keeps_its_grid_byte_for_byte(self):
        cells, ai = plain()
        ai[10] = (0x80, 0x80 | 33)  # values the rules wouldn't give: kept
        win = mapinfo(cells, ai)
        self.assertEqual(aigrid.refresh(win, win), (win, []))
        roads = nav.replace_buffers(win, {0: b"other roads"})  # a change the grid doesn't follow
        self.assertEqual(aigrid.refresh(win, roads), (roads, []))
        far = cover.paint(win, [cover.Paint(3000.0, 3000.0, 2000.0)])  # one cover cell of 16: no rule's answer moves
        out, notes = aigrid.refresh(win, far)
        self.assertEqual(sdb.split_mapinfo(out)[2], sdb.split_mapinfo(win)[2])

    def test_a_cover_circle_flips_forest_on_the_cells_more_than_a_quarter_painted(self):
        cells, ai = plain()
        win = mapinfo(cells, ai)
        x, y = 3 * aigrid.CELL, 3 * aigrid.CELL  # a corner shared by AI cells (2, 2), (3, 2), (2, 3), (3, 3)
        painted = cover.paint(win, [cover.Paint(x + 3250.0, y + 3250.0, 13000.0, square=True)])
        f, _b, _n = aigrid._shares(painted, SIDE, SIDE)
        more = {c for c in range(64) if f[c] > 0.25}
        self.assertTrue(more and {c for c in range(64) if 0 < f[c] <= 0.25})  # some painted a quarter or less
        out, notes = aigrid.refresh(win, painted)
        tail = aigrid.Tail(sdb.split_mapinfo(out)[2])
        self.assertEqual({c for c in range(64) if tail.forest(c)}, more)
        for c in range(64):  # tree lines: a forest cell with an open neighbour (all of these are at the wood's edge)
            self.assertEqual(bool(tail.cells[2 * c] & 0x80), c in more)
            self.assertEqual(tail.clearance(c), 127)  # nothing blocked changed
        self.assertEqual(notes, [f"AI grid: forest redone on {len(more)} cell(s), tree-line spots on {len(more)}, "
                                 f"clearance on 0"])
        self.assertEqual(sdb.split_mapinfo(out)[1], sdb.split_mapinfo(painted)[1])  # the buffers as the paint left them
        import hashlib
        self.assertEqual(hashlib.md5(b"INFOIA\r\n" + b"Eugen Systems" + out[24:]).digest(), out[8:24])
        # the wood taken away again: forest and tree lines go
        back, _notes = aigrid.refresh(out, cover.paint(out, [cover.Paint(x + 3250.0, y + 3250.0, 13000.0, erase=True,
                                                                          square=True)]))
        tail = aigrid.Tail(sdb.split_mapinfo(back)[2])
        self.assertEqual([c for c in range(64) if tail.forest(c) or tail.cells[2 * c] & 0x80], [])

    def test_clearance_follows_blocked_ground_and_the_vehicles_movement(self):
        cells, ai = plain()
        win = mapinfo(cells, ai)
        wall = cover.paint(win, [cover.Paint(aigrid.CELL * 0.5, aigrid.CELL * 0.5, 13000.0, "blocked", square=True)])
        out, _notes = aigrid.refresh(win, wall)  # AI cell 0 all blocked: clearance grows from it
        tail = aigrid.Tail(sdb.split_mapinfo(out)[2])
        self.assertEqual([tail.clearance(c) for c in range(6)], [0, 32, 64, 95, 127, 127])
        self.assertEqual(tail.clearance(63), 127)
        # the vehicles' movement: a circle over AI cells (5..6, 5..6), 79% of each, emptied by a block
        from test_nav import made
        c = (6 * aigrid.CELL, 6 * aigrid.CELL, aigrid.CELL)
        g, moved = made([c], []), made([c], [])
        moved.block([(c[0], c[1], 1000.0)], refill=False)
        before = mapinfo(cells, ai, g.to_bytes())
        after = nav.replace_buffers(before, {2: moved.to_bytes()})
        out, notes = aigrid.refresh(before, after)
        tail = aigrid.Tail(sdb.split_mapinfo(out)[2])
        self.assertEqual([tail.clearance(j * SIDE + i) for j in (5, 6) for i in (5, 6)], [0] * 4)  # blocked now
        self.assertEqual((tail.clearance(5 * SIDE + 4), tail.clearance(4 * SIDE + 4)), (32, 45))  # 1 and 1.41 off
        self.assertEqual(tail.clearance(0), 127)            # more than 4 cells off: as it was
        self.assertTrue(notes and "clearance on" in notes[0])

    def test_a_tail_that_cant_be_read_is_left(self):
        cells, ai = plain()
        win = mapinfo(cells, ai)
        head, bufs, _tail = sdb.split_mapinfo(win)
        odd = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in bufs) + b"tail", {})
        painted = cover.paint(odd, [cover.Paint(30000.0, 30000.0, 13000.0)])
        out, notes = aigrid.refresh(odd, painted)
        self.assertEqual(out, painted)
        self.assertIn("the AI grid couldn't be read", notes[0])


if __name__ == "__main__":
    unittest.main()
