"""Packs past 4 GiB in a build (rusemod.build._wide_packs; the owner, 2026-10-30: a player's mod set with many era
units' own models stopped at 4 GiB): nothing changes while every pack fits; once one doesn't, every pack of 2 GiB or
more in the copy is written wide and the copy gets the big-packs game patch; past what even a wide pack holds, the
build stops with what to do. Sizes are stand-ins that only say their length (nothing that big is made)."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat
from test_edat import TREE, Says
from rusemod import Edat, build
from rusemod.build import BuildError


class WidePacks(unittest.TestCase):
    def setUp(self):
        self.game = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.game, True)
        data = self.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        self.own = data / "ZZ_Win.dat"  # the game's own big pack, left alone by these mods
        self.own.write_bytes(make_edat(TREE))
        self.lines = []

    def wide(self, rebuilt):
        wide, opened = build._wide_packs(self.game, rebuilt, self.lines.append)
        for _p, arc, _c in opened:
            self.addCleanup(arc.close)
        return wide, opened

    def test_nothing_changes_while_every_pack_fits(self):
        rebuilt = [(self.game / "Data" / "PC" / "190852" / "Data_Common.dat", Edat(make_edat(TREE)),
                    {"top.bin": b"small"})]
        self.assertEqual(self.wide(rebuilt), (set(), []))
        self.assertEqual(self.lines, [])

    def test_past_4_gib_every_big_pack_goes_wide_the_games_own_too(self):
        common = self.game / "Data" / "PC" / "190852" / "Data_Common.dat"
        three = Says(3_000_000_000)  # three of them: the third starts 6 GB in, past where a plain place reaches
        rebuilt = [(common, Edat(make_edat(TREE)), {"top.bin": three, "genglad\\readme.txt": three,
                                                    "genglad\\patchable\\mapinfo.cpp.gladndfbin": three})]
        # (the game's own pack here is tiny: "2 GiB or more" is made small for the test)
        with mock.patch.object(build, "TWO_GIB", 100):
            wide, opened = self.wide(rebuilt)
        self.assertEqual(wide, {common, self.own})
        self.assertEqual([p for p, _a, _c in opened], [self.own])  # rewritten wide as it is
        self.assertIn("big-packs game patch", self.lines[0])
        self.assertIn("ZZ_Win.dat", self.lines[1])

    def test_too_big_even_wide_stops_the_build_with_what_to_do(self):
        rebuilt = [(self.game / "x.dat", Edat(make_edat(TREE)), {"top.bin": Says(5_000_000_000)})]
        with self.assertRaisesRegex(BuildError, "era units"):
            self.wide(rebuilt)


class OtherReaders(unittest.TestCase):
    """LittleGroove's engine (ruse_mod_engine.edata), which the apps' mod tools use, reads a wide pack and an 8-byte
    data length as rusemod.edat does."""

    def test_the_engine_reads_a_wide_pack(self):
        from test_edat import PATHS
        from ruse_mod_engine.edata import EdataFile
        raw = Edat(make_edat(TREE)).to_bytes(wide=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "wide.dat")
            path.write_bytes(raw)
            ed = EdataFile.open(str(path))
            got = {p.replace("/", "\\"): ed.get(p) for p in ed.list()}
        self.assertEqual({k.lower(): bytes(v) for k, v in got.items()}, {k.lower(): v for k, v in PATHS.items()})

    def test_an_animation_pack_written_as_before(self):
        from rusemod import unitpacks
        raw = make_edat(TREE)
        self.assertEqual(unitpacks.archive_with(raw, {})[:0x2D][0x25:], raw[0x25:0x2D])  # 8 bytes, high 4 at 0


if __name__ == "__main__":
    unittest.main()
