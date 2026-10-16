"""The level-build state database's water bit (rusemod.statedb), on made-up meshes (tests/test_groundgen.py's way) and
a made-up SDB: drained ground made land, new water made water, Eugen's own marks left where the ground didn't change."""
import struct
import unittest

from rusemod import statedb
from rusemod.groundgen import Shape, fine_cells, make_mesh
from rusemod.tms import Tms
from ruse_mod_engine import sdb

from test_groundgen import BOUNDS, island, sea, whole
from test_tms import make_tms

LAND, WATER, WOOD = 0x01, 0x09, 0x11   # as D-Day's file reads: land, water, land with scenery on it


def leaf(a, b, c, d):
    return a | b << 8 | c << 16 | d << 24 | 1


def state(values) -> bytes:
    """An SDB over the made-up map (0, 0, 2000, 2000) at 4 x 4 cells of 500: the root's four quarters, each a leaf of
    2 x 2 cells; `values` is the 16 cells' bytes, row by row (row 0 at y 0)."""
    root_at = 0x20
    quarters = []
    for qy, qx in ((0, 0), (0, 2), (2, 0), (2, 2)):
        quarters.append(leaf(*[values[(qy + dy) * 4 + qx + dx] for dy in (0, 1) for dx in (0, 1)]))
    prefix = struct.pack("<4ffIII", *BOUNDS, 500.0, 0, 0, root_at)
    return sdb.serialize({"ver": 2, "prefix": prefix, "node_start": root_at, "nodes": [quarters], "tail": b""})


def cells(raw: bytes) -> list[int]:
    grid, r = sdb.to_grid(sdb.parse(raw))
    assert r == 4
    return list(grid)


def mesh(strokes) -> Tms:
    t = Tms(make_tms(gw=2, gh=2))
    shape = Shape(strokes, BOUNDS, -50.0)
    t.cells, _info = make_mesh(t, shape.h, shape.w, 16, fine_cells(t, shape))
    return Tms(t.to_bytes())


class Water(unittest.TestCase):
    def test_a_drained_sea_is_made_land(self):
        """The blank farm's case: the copied map's sea (0x09 everywhere), the new ground flat and dry: every cell made
        land (0x01), so the game draws scenery there (F-46)."""
        new, dried, flooded = statedb.with_water(state([WATER] * 16), mesh([whole(10.0)]))
        self.assertEqual((dried, flooded), (16, 0))
        self.assertEqual(cells(new), [LAND] * 16)

    def test_new_water_is_made_water_and_loses_the_scenery_mark(self):
        new, dried, flooded = statedb.with_water(state([WOOD] * 16), mesh([whole(0.0), sea(20.0)]))
        self.assertEqual((dried, flooded), (0, 16))
        self.assertEqual(cells(new), [WATER] * 16)

    def test_only_the_ground_the_new_mesh_changes(self):
        """With the mesh the file was made for: a sea with an island, Eugen's file marking one cell under the sea as
        land (as his shore cells differ from a cell-middle test); the island drained away, only the cells whose water
        changed are touched, his odd cell stays."""
        old = mesh([whole(0.0), sea(20.0), island(x=1500.0, y=1500.0, r=500.0)])
        marks = [WATER] * 16
        marks[0] = LAND                       # his own mark under the sea
        for i in (10, 11, 14, 15):            # the island's cells (middles 354 from its middle), land
            marks[i] = LAND
        new, dried, flooded = statedb.with_water(state(marks), mesh([whole(0.0), sea(20.0)]), old)
        got = cells(new)
        self.assertEqual(got[0], LAND)        # untouched: the ground there didn't change
        self.assertEqual([got[i] for i in (10, 11, 14, 15)], [WATER] * 4)
        self.assertEqual((dried, flooded), (0, 4))

    def test_nothing_to_change_is_the_same_file(self):
        raw = state([LAND] * 16)
        new, dried, flooded = statedb.with_water(raw, mesh([whole(10.0)]))
        self.assertEqual((new, dried, flooded), (raw, 0, 0))


if __name__ == "__main__":
    unittest.main()
