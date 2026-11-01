"""A build list's groups (rusemod.menugroups): a unit's group up its research chain while an upgrade, else where the
mod put it, else the way of the unit it was copied from; counted per nation and building over the units shown; the
mod's file read back as written."""
import tempfile
import unittest
from pathlib import Path

from rusemod import menugroups as mg

KUB, N1, N2, N3, TIGER = "$/U/Kub", "$/U/N1", "$/U/N2", "$/U/N3", "$/U/Tiger"


def unit(parent=None, flag=False, source=None, nation=1, factory=8, shown=True):
    return {"parent": parent, "flag": flag, "source": source, "nation": nation, "factory": factory, "shown": shown}


class RootsTest(unittest.TestCase):
    def test_up_the_research_chain_while_an_upgrade(self):
        units = {KUB: unit(), N1: unit(KUB, True), N2: unit(N1, True)}
        self.assertEqual(mg.roots(units), {KUB: KUB, N1: KUB, N2: KUB})

    def test_research_without_the_upgrade_flag_is_a_group_of_its_own(self):
        units = {KUB: unit(), N1: unit(KUB, False)}
        self.assertEqual(mg.roots(units)[N1], N1)

    def test_the_mods_group_before_the_unit_it_was_copied_from(self):
        units = {KUB: unit(), TIGER: unit(factory=10), N1: unit(source=TIGER), N2: unit(source=TIGER)}
        r = mg.roots(units, {N1: KUB, N2: N2})
        self.assertEqual((r[N1], r[N2]), (KUB, N2))

    def test_without_a_group_the_unit_it_was_copied_from(self):
        units = {KUB: unit(), N1: unit(source=KUB), N2: unit(N1, True)}
        self.assertEqual(mg.roots(units), {KUB: KUB, N1: KUB, N2: KUB})

    def test_a_loop_or_a_unit_not_there_stops(self):
        units = {N1: unit(N2, True), N2: unit(N1, True), N3: unit("$/U/Gone", True)}
        r = mg.roots(units)
        self.assertIn(r[N1], (N1, N2))
        self.assertEqual(r[N3], N3)


class MembersTest(unittest.TestCase):
    def test_counted_per_nation_and_building_over_the_shown(self):
        units = {KUB: unit(), N1: unit(KUB, True), N2: unit(KUB, True, shown=False), N3: unit(KUB, True, nation=2),
                 TIGER: unit(factory=None)}
        g = mg.members(units, mg.roots(units))
        self.assertEqual(sorted(g[(1, 8, KUB)]), [KUB, N1])
        self.assertEqual(g[(2, 8, KUB)], [N3])
        self.assertNotIn(TIGER, [a for v in g.values() for a in v])

    def test_over_the_most(self):
        units = {KUB: unit(), **{f"$/U/E{k}": unit(KUB, True) for k in range(mg.MOST)}}
        self.assertEqual(mg.over(mg.members(units, mg.roots(units))), [((1, 8, KUB), mg.MOST + 1)])
        units.pop("$/U/E0")
        self.assertEqual(mg.over(mg.members(units, mg.roots(units))), [])


class CrowdedTest(unittest.TestCase):
    def test_a_building_with_more_groups_than_the_most(self):
        units = {f"$/U/G{k}": unit() for k in range(mg.MOST_GROUPS + 1)}
        units["$/U/Other"] = unit(factory=10)
        self.assertEqual(mg.crowded(mg.members(units, mg.roots(units))), [((1, 8), mg.MOST_GROUPS + 1)])
        units.pop("$/U/G0")
        self.assertEqual(mg.crowded(mg.members(units, mg.roots(units))), [])


class FileTest(unittest.TestCase):
    def test_read_back_as_written(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(mg.read(d), {})
            groups = {"$/GFX/Everything/Descriptor_Unit_A": "$/GFX/Everything/Descriptor_Unit_B", N1: N1}
            mg.write(d, groups)
            self.assertEqual(mg.read(d), groups)
            mg.write(d, {})
            self.assertFalse((Path(d) / mg.FILE).exists())

    def test_a_bad_file_is_said(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / mg.FILE).write_text("[groups]\na = 1\n", encoding="utf-8")
            with self.assertRaises(mg.MenuGroupsError):
                mg.read(d)


if __name__ == "__main__":
    unittest.main()
