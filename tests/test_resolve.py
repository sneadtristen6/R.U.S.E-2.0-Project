"""Mod versions and load order (docs/MOD_FORMAT.md §10.6)."""
import unittest

from rusemod.resolve import ModInfo, ResolveError, load_order, matches, pick_versions


def ids(mods):
    return [m.id for m in mods]


class Versions(unittest.TestCase):
    def test_ranges(self):
        self.assertTrue(matches("0.1.5", ">=0.1, <0.2"))
        self.assertFalse(matches("0.2.0", ">=0.1, <0.2"))
        self.assertTrue(matches("0.3.9", "^0.3"))
        self.assertFalse(matches("0.4.0", "^0.3"))
        self.assertTrue(matches("1.9.0", "^1.2"))
        self.assertFalse(matches("2.0.0", "^1.2"))
        self.assertTrue(matches("1.2.7", "~1.2"))
        self.assertFalse(matches("1.3.0", "~1.2"))
        self.assertTrue(matches("5.0.0", "*"))
        self.assertTrue(matches("1.2.0", "1.2"))
        self.assertFalse(matches("1.2.1", "1.2"))

    def test_newest_version_every_range_accepts(self):
        catalog = {
            "core": [ModInfo("core", "0.3.0"), ModInfo("core", "0.3.4"), ModInfo("core", "0.4.0")],
            "units": [ModInfo("units", "1.0.0", depends={"core": "^0.3"})],
        }
        chosen = pick_versions({"units": "*", "core": "*"}, catalog)
        self.assertEqual(chosen["core"].version, "0.3.4")  # 0.4.0 is newer, but units needs ^0.3

    def test_disagreement_names_both_sides(self):
        catalog = {"core": [ModInfo("core", "0.3.0")], "units": [ModInfo("units", "1.0.0", depends={"core": ">=0.5"})]}
        with self.assertRaisesRegex(ResolveError, r"core.*units 1.0.0 wants >=0.5"):
            pick_versions({"units": "*"}, catalog)

    def test_missing_mod(self):
        with self.assertRaisesRegex(ResolveError, "isn't available"):
            pick_versions({"ghost": "*"}, {})


class Order(unittest.TestCase):
    def test_dependencies_first_then_alphabetical(self):
        mods = [ModInfo("zeta"), ModInfo("alpha", depends={"zeta": "*"}), ModInfo("beta")]
        self.assertEqual(ids(load_order(mods)), ["beta", "zeta", "alpha"])

    def test_optional_dependency_only_when_present(self):
        mods = [ModInfo("a", optional={"z": "*"}), ModInfo("z")]
        self.assertEqual(ids(load_order(mods)), ["z", "a"])
        self.assertEqual(ids(load_order([ModInfo("a", optional={"z": "*"})])), ["a"])

    def test_when_mod_counts_as_optional_dependency(self):
        mods = [ModInfo("compat", when_mods={"better-ai"}), ModInfo("better-ai")]
        self.assertEqual(ids(load_order(mods)), ["better-ai", "compat"])

    def test_after_and_before(self):
        mods = [ModInfo("a", after=["c"]), ModInfo("b", before=["a"]), ModInfo("c")]
        self.assertEqual(ids(load_order(mods)), ["b", "c", "a"])

    def test_same_input_same_order_every_time(self):
        mods = [ModInfo(x) for x in ["m", "b", "x", "a"]]
        self.assertEqual(ids(load_order(mods)), ["a", "b", "m", "x"])
        self.assertEqual(ids(load_order(list(reversed(mods)))), ["a", "b", "m", "x"])

    def test_loop_is_named(self):
        mods = [ModInfo("a", after=["b"]), ModInfo("b", after=["a"])]
        with self.assertRaisesRegex(ResolveError, r"loop: a -> b -> a"):
            load_order(mods)

    def test_missing_or_wrong_dependency(self):
        with self.assertRaisesRegex(ResolveError, "needs core, which isn't in the mod set"):
            load_order([ModInfo("units", depends={"core": "*"})])
        with self.assertRaisesRegex(ResolveError, "needs core >=1.0, but the set has 0.3.0"):
            load_order([ModInfo("units", depends={"core": ">=1.0"}), ModInfo("core", "0.3.0")])

    def test_conflicting_mods_stop_everything(self):
        with self.assertRaisesRegex(ResolveError, "can't be used together with old-units"):
            load_order([ModInfo("ruse2", conflicts={"old-units": "*"}), ModInfo("old-units", "1.0.0")])


if __name__ == "__main__":
    unittest.main()
