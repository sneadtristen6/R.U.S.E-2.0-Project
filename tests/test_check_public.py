"""The public-repo guard (tools/check_public.py): private material, game files and program addresses are refused."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_public import problems  # noqa: E402


def check(files: dict) -> list:
    return problems(list(files), read=lambda p: files[p])


class Guard(unittest.TestCase):
    def test_private_material_is_refused(self):
        found = check({"private/notes.md": b"x", "mods/cheat/mod.toml": b"x", "docs/private/x.md": b"x",
                       "docs/RUSE_Research_Handover_2026.md": b"x", "docs/PLAN.md": b"fine"})
        self.assertEqual(len(found), 4)
        self.assertTrue(all("docs/PLAN.md" not in f for f in found))

    def test_game_files_are_refused_outside_the_tests(self):
        found = check({"stuff/ZZ_Win.dat": b"edat", "a/save.boobspc": b"x", "b/Cheat.rmod": b"{}",
                       "tests/made_up.dat": b"edat", "src/rusemod/scenery.py": b"code"})
        self.assertEqual(sorted(f.split(":")[0] for f in found), ["a/save.boobspc", "b/Cheat.rmod", "stuff/ZZ_Win.dat"])

    def test_program_addresses_are_refused(self):
        found = check({"docs/notes.md": b"the loader FUN_140a5d3f0 reads it", "docs/b.md": b"at 0x140a58ff0",
                       "docs/c.md": b"offset 0x40D and FUN_x are fine"})
        self.assertEqual(sorted(f.split(":")[0] for f in found), ["docs/b.md", "docs/notes.md"])


if __name__ == "__main__":
    unittest.main()
