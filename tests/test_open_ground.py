"""The open brushes (rusemod.nav, Graph.open_ground): ground given back to units where a made-up map's movement has
none, the reverse of a block, in the main graph and in a town's own local map; blocks and opens in order; the warning
for water; the files; the AI grid following."""
import struct
import tomllib
import unittest
from types import SimpleNamespace

from rusemod import nav
from rusemod.brush import BRUSHES, parse_strokes
from test_nav import made, row, town


def circles_of(g):
    return [c[:3] for c in g.circles[:-1]]


def win_of(g, size=16000.0) -> bytes:
    """A mapinfo.win holding `g` as both movement graphs."""
    head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, size, size)
    return nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
        b"roads", g.to_bytes(), g.to_bytes(), b"cover")) + b"tail", {})


class MainGraph(unittest.TestCase):
    def test_ground_past_the_edge_is_opened_and_linked(self):
        g, old = row(), row()  # A, B, C along y 2000; C reaches x 11,600
        self.assertFalse(g.walkable(13500.0, 2000.0))
        c = g.open_ground([(12500.0, 2000.0, 2560.0)])
        self.assertGreater(c["added"], 0)
        self.assertGreater(c["linked"], 0)
        self.assertEqual((c["local"], c["left_out"], c["idle"]), (0, 0, []))
        self.assertTrue(g.walkable(13500.0, 2000.0))
        self.assertTrue(g.walkable(12000.0, 2000.0))
        self.assertEqual(g.parts(), [len(g.circles) - 1])  # one piece
        self.assertEqual(circles_of(g)[:3], circles_of(old))  # the old circles keep their numbers
        self.assertEqual(g.crossings, old.crossings)  # and their crossings
        for x, y, r in circles_of(g)[3:]:  # every new circle inside the stroke, and found by the index
            self.assertLessEqual(((x - 12500.0) ** 2 + (y - 2000.0) ** 2) ** 0.5 + r, 2560.0)
            self.assertGreaterEqual(r, nav.MIN_RADIUS)
            self.assertIsNotNone(g.find(x, y))
        data = g.to_bytes()
        self.assertEqual(nav.Graph.read(data).to_bytes(), data)

    def test_ground_already_open_is_left_as_it_was(self):
        g = row()
        c = g.open_ground([(7000.0, 2000.0, 2000.0)])  # inside B
        self.assertEqual((c["added"], c["idle"]), (0, [0]))
        self.assertEqual(g.to_bytes(), row().to_bytes())

    def test_an_island_no_unit_could_reach_stays_closed(self):
        g = row()
        c = g.open_ground([(13000.0, 13000.0, 2560.0), (12500.0, 2000.0, 400.0)])  # far off; too small
        self.assertEqual((c["added"], c["idle"]), (0, [0, 1]))
        self.assertGreater(c["left_out"], 0)
        self.assertEqual(g.to_bytes(), row().to_bytes())
        self.assertFalse(g.walkable(13000.0, 13000.0))

    def test_never_off_the_map(self):
        g = row()  # the map is 16,000 across
        c = g.open_ground([(17000.0, 2000.0, 3000.0)])
        self.assertTrue(all(0 <= x <= 16000.0 and 0 <= y <= 16000.0 for x, y, _r in circles_of(g)))
        self.assertEqual(c["idle"], [0] if not c["added"] else [])

    def test_in_a_town_the_local_map_gets_the_ground(self):
        g = town()  # the town: owner 0 at (5000, 26000), its local map three circles down x 5000
        self.assertFalse(g.walkable(7000.0, 24000.0))  # in the owner, off its local map
        n, m = len(g.circles), len(g.subs[0].circles)
        c = g.open_ground([(7000.0, 24000.0, 2000.0)])
        self.assertEqual(c["added"], 0)  # no main circle with its middle in the owner
        self.assertEqual(len(g.circles), n)
        self.assertGreater(c["local"], 0)
        self.assertEqual(len(g.subs[0].circles), m + c["local"])
        self.assertTrue(g.walkable(7000.0, 24000.0))
        self.assertEqual(g.subs[0].parts(), [len(g.subs[0].circles) - 1])
        for x, y, r in circles_of(g.subs[0])[m - 1:]:
            self.assertLess(((x - 5000.0) ** 2 + (y - 26000.0) ** 2) ** 0.5, 6400.0)  # middles in the owner
            self.assertGreaterEqual(r, nav.STEP)
        data = g.to_bytes()
        self.assertEqual(nav.Graph.read(data).to_bytes(), data)


class InOrder(unittest.TestCase):
    """apply_blocks: blocks and opens in order, the later one winning where they meet."""

    def graphs(self, blocks):
        from rusemod.cover import member
        from ruse_mod_engine import sdb
        idle = []
        new, notes = nav.apply_blocks({member("Blitz"): win_of(row())}.get, "Blitz", blocks, idle)
        bufs = sdb.split_mapinfo(new[member("Blitz")])[1]
        return nav.Graph.read(bufs[1]), nav.Graph.read(bufs[2]), idle, notes

    def test_an_open_after_a_block_wins(self):
        block = nav.Block(10000.0, 2000.0, 400.0)  # C emptied
        opened = nav.Block(10000.0, 2000.0, 2000.0, open=True)
        inf, veh, idle, notes = self.graphs([block, opened])
        for g in (inf, veh):
            self.assertTrue(g.walkable(10500.0, 2000.0))
            self.assertEqual(len(g.parts()), 1)
        self.assertEqual(idle, [])
        self.assertTrue(any("1 open(s)" in n for n in notes), notes)

    def test_a_block_after_an_open_wins(self):
        opened = nav.Block(10000.0, 2000.0, 2000.0, open=True)  # open already: nothing to do
        block = nav.Block(10000.0, 2000.0, 400.0)
        inf, veh, idle, _notes = self.graphs([opened, block])
        for g in (inf, veh):
            self.assertFalse(g.walkable(10000.0, 2000.0))
        self.assertEqual(idle, [opened])

    def test_only_the_units_named(self):
        opened = nav.Block(12500.0, 2000.0, 2560.0, "infantry", open=True)
        inf, veh, idle, _notes = self.graphs([opened])
        self.assertTrue(inf.walkable(13500.0, 2000.0))
        self.assertFalse(veh.walkable(13500.0, 2000.0))
        self.assertEqual(veh.to_bytes(), row().to_bytes())
        self.assertEqual(idle, [])

    def test_bridges_roads_and_the_cover_check_see_only_the_blocks(self):
        blocks = [nav.Block(1.0, 2.0, 3.0), nav.Block(4.0, 5.0, 6.0, open=True)]
        self.assertEqual(nav.closing(blocks), blocks[:1])


class Water(unittest.TestCase):
    def test_an_open_over_water_is_named_with_its_wet_spot(self):
        def river(x, y):
            return 11400.0 < x < 15600.0

        wet = nav.Block(10000.0, 2000.0, 3000.0, open=True)
        dry = nav.Block(3000.0, 2000.0, 3000.0, open=True)
        block = nav.Block(13000.0, 2000.0, 3000.0)  # a block over water is no news
        got = nav.wet_opens([wet, dry, block], river)
        self.assertEqual(len(got), 1)
        self.assertIs(got[0][0], wet)
        x, y = got[0][1]
        self.assertTrue(river(x, y))
        self.assertLess(((x - 10000.0) ** 2 + (y - 2000.0) ** 2) ** 0.5, 3000.0)


class Files(unittest.TestCase):
    def test_movement_toml_blocks_and_opens(self):
        blocks = [nav.Block(1.0, 2.0, 3.0), nav.Block(4.0, 5.0, 6.0, "vehicles", open=True)]
        data = tomllib.loads(nav.blocks_toml(blocks, "two"))
        self.assertEqual(nav.parse_blocks(data["block"]) + nav.parse_blocks(data["open"], table="open"), blocks)
        with self.assertRaisesRegex(nav.NavError, "open 1: radius is missing"):
            nav.parse_blocks([{"x": 1, "y": 2}], table="open")

    def test_the_brushes(self):
        self.assertEqual([(BRUSHES[b].kind, BRUSHES[b].shape) for b in ("open", "open_infantry", "open_vehicles")],
                         [("open", "all"), ("open", "infantry"), ("open", "vehicles")])
        s = parse_strokes([{"brush": "open_vehicles", "x": 1.0, "y": 2.0, "radius": 3000.0}])[0]
        self.assertEqual(s.height_at(1.0, 2.0, 50.0), 50.0)  # the ground stays

    def test_strokes_go_to_the_movement_in_their_order(self):
        from rusemod.build import _block_brushes
        strokes = parse_strokes([
            {"brush": "block", "x": 0.0, "y": 0.0, "radius": 1000.0},
            {"brush": "raise", "x": 1.0, "y": 0.0, "radius": 1000.0, "height": 10.0},
            {"brush": "open_infantry", "x": 2.0, "y": 0.0, "radius": 1000.0},
            {"brush": "open", "x": 3.0, "y": 0.0, "radius": 1000.0}])
        info = SimpleNamespace(terrain={"Blitz": strokes}, movement={"Blitz": [nav.Block(9.0, 9.0, 9.0)]})
        _block_brushes(info)
        self.assertEqual(info.movement["Blitz"], [
            nav.Block(9.0, 9.0, 9.0), nav.Block(0.0, 0.0, 1000.0), nav.Block(2.0, 0.0, 1000.0, "infantry", True),
            nav.Block(3.0, 0.0, 1000.0, "all", True)])
        self.assertEqual([s.brush for s in info.terrain["Blitz"]], ["raise"])

    def test_a_square_or_a_line_goes_in_as_circles_covering_it(self):
        """The movement graphs are circles: a square or a line block (the brush types, 2026-10-03) goes in as circles
        whose union covers it, in the stroke's place in the order."""
        from rusemod.build import BLOCK_CELL, _block_brushes
        strokes = parse_strokes([
            {"brush": "block", "x": 0.0, "y": 0.0, "radius": 3000.0, "shape": "square", "dx": 1.0, "dy": 1.0},
            {"brush": "open_vehicles", "x": 0.0, "y": 0.0, "radius": 500.0, "shape": "line", "x2": 4000.0, "y2": 0.0}])
        info = SimpleNamespace(terrain={"Blitz": strokes}, movement={})
        _block_brushes(info)
        blocks = info.movement["Blitz"]
        square = [b for b in blocks if not b.open]
        line = [b for b in blocks if b.open]
        self.assertEqual(len(square), len(strokes[0].footprint().circles(BLOCK_CELL)))
        self.assertEqual(blocks, square + line)                  # in their order
        self.assertTrue(all(b.units == "vehicles" for b in line))
        for px, py in ((2000.0, 0.0), (0.0, 2000.0), (0.0, 0.0)):  # inside the turned square: covered
            self.assertTrue(any((px - b.x) ** 2 + (py - b.y) ** 2 <= b.radius ** 2 for b in square))
        self.assertTrue(any((2000.0 - b.x) ** 2 + (400.0 - b.y) ** 2 <= b.radius ** 2 for b in line))


class Built(unittest.TestCase):
    def test_opened_ground_in_the_modded_copy(self):
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
            (rev / "DataMap_Win.dat").write_bytes(
                make_edat([("dir", "datasmap/blitz/".replace("/", "\\"), [("file", "mapinfo.win", win_of(row()))])]))
            (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            folder = write_mod(root / "mods", "paths", {})
            (folder / "maps" / "Blitz").mkdir(parents=True)
            (folder / "maps" / "Blitz" / "movement.toml").write_text(  # ground units use already: a note
                '[[open]]\nx = 7000.0\ny = 2000.0\nradius = 2000.0\n', encoding="utf-8")
            (folder / "maps" / "Blitz" / "terrain.toml").write_text(
                '[[stroke]]\nbrush = "open_vehicles"\nx = 12500.0\ny = 2000.0\nradius = 2560.0\n', encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            self.assertIn("movement: Blitz, from paths", lines)
            notes = [f.message for f in result.findings if f.level == "note" and "opened nothing" in f.message]
            self.assertEqual(len(notes), 1, result.findings)
            self.assertIn("(7000, 2000)", notes[0])
            arc = Edat((root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes())
            bufs = sdb.split_mapinfo(bytes(arc.read(arc.find(member("Blitz")))))[1]
            self.assertEqual(bufs[1], row().to_bytes())  # infantry untouched
            self.assertTrue(nav.Graph.read(bufs[2]).walkable(13500.0, 2000.0))  # vehicles: opened


class AiGrid(unittest.TestCase):
    def test_opened_ground_the_ai_had_as_blocked_is_open_to_it(self):
        from rusemod import aigrid, cover
        from ruse_mod_engine import sdb
        from test_aigrid import SIDE, mapinfo, plain
        cell = aigrid.CELL
        cells, ai = plain()
        g = made([(2 * cell, 0.5 * cell, cell)], [])  # vehicles' ground east of AI cell 0, none on it
        g.box = (0, 0, SIDE * cell)
        start = mapinfo(cells, ai, g.to_bytes())
        walled = cover.paint(start, [cover.Paint(0.5 * cell, 0.5 * cell, 13000.0, "blocked", square=True)])
        was = [i == 0 for i in range(SIDE * SIDE)]  # the map as shipped: AI cell 0 blocked, its grid saying so
        tail = aigrid.Tail(sdb.split_mapinfo(walled)[2])
        for c, v in enumerate(aigrid._clearance(was, SIDE, SIDE)):
            tail.cells[2 * c + 1] = v
        head, bufs, _t = sdb.split_mapinfo(walled)
        before = nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in bufs) + tail.to_bytes(),
                                     {})
        opened = nav.Graph.read(g.to_bytes())
        self.assertGreater(opened.open_ground([(0.5 * cell, 0.5 * cell, 0.75 * cell)])["added"], 0)
        out, notes = aigrid.refresh(before, nav.replace_buffers(before, {2: opened.to_bytes()}))
        after = aigrid.Tail(sdb.split_mapinfo(out)[2])
        self.assertEqual(aigrid.Tail(sdb.split_mapinfo(before)[2]).clearance(0), 0)
        self.assertEqual(after.clearance(0), 127)  # nothing blocked near it any more
        self.assertTrue(notes and "clearance on" in notes[0])


class DriedBeds(unittest.TestCase):
    """A river the terrain edits dried (raised ground) is opened to units: the build's zones over its samples (a D-Day
    test: tanks couldn't cross a dried stretch of river)."""

    def test_zones_big_enough_for_a_circle_and_off_the_water_left(self):
        from rusemod.build import BED_RADII, _bed_circles
        bed = [(x, y) for x in range(0, 20480, 640) for y in range(0, 5120, 640)]  # 80 m long, 20 m wide
        zones = _bed_circles(bed)
        self.assertTrue(zones and all(r >= nav.MIN_RADIUS for _x, _y, r in zones))
        held = [p for p in bed if any((p[0] - x) ** 2 + (p[1] - y) ** 2 <= r * r for x, y, r in zones)]
        self.assertEqual(len(held), len(bed))

        def wet(x, y):  # the river goes on past x = 20480
            return x > 20480
        near_water = _bed_circles(bed, wet)
        self.assertTrue(all(x + r <= 20480 for x, _y, r in near_water))
        self.assertTrue(all(r in BED_RADII for _x, _y, r in near_water))
        self.assertEqual(_bed_circles([(0.0, 0.0)], lambda x, y: True), [])  # all water around: nothing to open

    def test_opened_on_a_graph(self):
        from rusemod.build import _bed_circles
        g = made([(0.0, 0.0, 12800.0)], [])  # a field, the dried bed beside it
        bed = [(x, y) for x in range(12800, 28160, 640) for y in range(-2560, 3200, 640)]
        counts = g.open_ground(_bed_circles(bed))
        self.assertGreater(counts["added"], 0)
        self.assertTrue(g.walkable(20480.0, 0.0))
        self.assertEqual(len(g.parts()), 1)


if __name__ == "__main__":
    unittest.main()
