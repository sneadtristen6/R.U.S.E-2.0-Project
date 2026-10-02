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

    def test_words_about_the_program_s_insides_are_refused(self):
        found = check({"docs/a.md": b"the limit is program-side", "docs/b.md": b"the nation list is in the program",
                       "src/x.toml": b"# RUSE.exe's own table", "docs/c.md": b"RUSE.exe reads the file first",
                       "docs/d.md": b"a 10-player copy tells whether the program caps it",
                       "docs/fine.md": b"Start RUSE.exe inside the copy; the program's name is shown",
                       "LICENSE": b"the source code in the Program"})
        self.assertEqual(sorted(f.split(":")[0] for f in found), ["docs/a.md", "docs/b.md", "docs/c.md", "docs/d.md",
                                                                 "src/x.toml"])

    def test_words_about_how_anything_was_studied_are_refused(self):
        bad = {"docs/a.md": b"we decompiled the scripts", "docs/b.md": b"the format was reverse-engineered",
               "docs/c.md": b"opened in Ghidra", "src/d.py": b"# uncompyle6 gives the source", "docs/e.md": b"vfunc3 does it",
               "docs/f.md": b"Reverse engineering the map", "docs/h.md": b"the module's bytecode",
               "docs/i.md": b"read from the crash dumps", "docs/j.md": b"watched it in Cheat Engine"}
        fine = {"docs/g.md": b"the game's scripts, read; the file's layout, decoded",
                "src/ruse_mod_engine/script_logic.py": b"decompile -> edit -> recompile (LittleGroove's words)"}
        found = check({**bad, **fine})
        self.assertEqual(sorted(f.split(":")[0] for f in found), sorted(bad))


if __name__ == "__main__":
    unittest.main()
