"""A map's data kept between runs (StudioApi._kept_on_disk) and in memory (MAP_DATA_KEPT). Issue #15: "a map is slow to
open": the memory kept 3 entries in all, so one map's own kinds pushed each other out as it opened, and every run read
the game files again (seconds a map on M03_Italie)."""
import os
import tempfile
import unittest
from pathlib import Path

from ruse_studio.api import StudioApi


class KeptMapData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.api = StudioApi(home=Path(self.tmp.name, "home"))
        self.source = Path(self.tmp.name, "DataMapX_v09.dat")
        self.source.write_bytes(b"map")
        self.made = 0

    def make(self):
        self.made += 1
        return {"pieces": [1, 2, 3], "made": self.made}

    def test_made_once_then_read_back(self):
        first = self.api._kept_on_disk("roads", "X", [self.source], self.make)
        again = StudioApi(home=Path(self.tmp.name, "home"))._kept_on_disk("roads", "X", [self.source], self.make)
        self.assertEqual(self.made, 1)
        self.assertEqual(again, first)  # a new run reads it back, the same

    def test_a_changed_game_file_makes_it_again(self):
        self.api._kept_on_disk("roads", "X", [self.source], self.make)
        self.source.write_bytes(b"a new game build")
        st = self.source.stat()
        os.utime(self.source, (st.st_atime, st.st_mtime + 10))
        self.assertEqual(self.api._kept_on_disk("roads", "X", [self.source], self.make)["made"], 2)
        self.assertEqual(self.api._kept_on_disk("scenery", "X", [self.source], self.make)["made"], 3)  # each its own

    def test_memory_holds_a_few_maps_of_every_kind(self):
        self.assertGreaterEqual(StudioApi.MAP_DATA_KEPT, 6 * 3)


if __name__ == "__main__":
    unittest.main()
