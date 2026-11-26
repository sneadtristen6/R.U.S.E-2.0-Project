"""The public-repo guard (tools/check_public.py): private material, game files and program addresses are refused.

Checked our_tools.json: none of its tools runs this check; these tests read no program, only made-up lines that name
the words the check refuses, and the crash table as 0.9.8.22 released it, from this repository's history, never
written out (its numbers are looked for in every public file by the private leak scan instead)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
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
                       "docs/RUSE_Research_Handover_2026.md": b"x", "docs/MOD_FORMAT.md": b"fine"})
        self.assertEqual(len(found), 4)
        self.assertTrue(all("docs/MOD_FORMAT.md" not in f for f in found))

    def test_what_describes_the_games_own_files_is_refused(self):
        """The owner, 2026-10-05: the repo holds the apps and what players and modders need; lists of the game's
        files, notes on their layout, working notes and the tools that go through its data are kept private."""
        bad = {"listings/ZZ_Win.dat.txt": b"names", "ruse_edat.py": b"code", "docs/FORMATS.md": b"x",
               "docs/PLAN.md": b"x", "docs/TESTS.md": b"x", "docs/LOG.md": b"x", "docs/RESEARCH-mod-platforms.md": b"x",
               "docs/ROADS.md": b"x", "tools/verify_all.py": b"code", "tools/nation_scan.py": b"code",
               "tools/a_new_tool.py": b"code", "prototypes/spike/ndf.py": b"code"}
        fine = {"docs/MOD_FORMAT.md": b"x", "docs/BIG_PATCH.md": b"x", "docs/wiki/Home.md": b"x", "README.md": b"x",
                "tools/check_public.py": b"code", "tools/check_commit_msg.py": b"code", "tools/rmod_to_mod.py": b"code",
                "tools/post_discussions.py": b"code", "src/rusemod/tools.py": b"code", "tests/test_tools.py": b"code"}
        found = check({**bad, **fine})
        self.assertEqual(sorted(f.split(":")[0] for f in found), sorted(bad))
        self.assertIn("kept in the private repo", found[0])

    def test_game_files_are_refused_outside_the_tests(self):
        found = check({"stuff/ZZ_Win.dat": b"edat", "a/save.boobspc": b"x", "b/Cheat.rmod": b"{}",
                       "tests/made_up.dat": b"edat", "src/rusemod/scenery.py": b"code"})
        self.assertEqual(sorted(f.split(":")[0] for f in found), ["a/save.boobspc", "b/Cheat.rmod", "stuff/ZZ_Win.dat"])

    def test_program_addresses_are_refused(self):
        found = check({"docs/notes.md": b"the loader FUN_1400abc00 reads it", "docs/b.md": b"at 0x1400abd00",
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

    def test_the_script_libraries_names_stand_only_in_their_spots(self):
        """The owner, 2026-10-06 ("Yes, just those spots"): the Studio carries the two libraries LittleGroove's engine
        shows the game's scripts with; their names may stand where they are pinned, built in and credited, and his
        engine's function name in our one call of it. Anywhere else, or any other such word in those files: refused."""
        fine = {"installers/requirements.txt": b"uncompyle6==3.9.3\nxdis==6.1.8\n",
                ".github/workflows/tests.yml": b'run: python -m pip install "uncompyle6==3.9.3" "xdis==6.1.8"',
                "installers/build_app.py": b'"include": ("uncompyle6", "xdis")',
                "THIRD_PARTY_NOTICES.md": b"| uncompyle6 | 3.9.3 | https://github.com/rocky/python-xdis |",
                "src/rusemod/mapscripts.py": b"lines = xyz_compile.decompile_xyz(xyz).splitlines()"}
        self.assertEqual(check(fine), [])
        bad = {"docs/a.md": b"uncompyle6==3.9.3", "src/rusemod/other.py": b"xyz_compile.decompile_xyz(xyz)",
               "installers/README.md": b"pip install xdis",
               "installers/requirements.txt": b"# for the scripts' bytecode\nxdis==6.1.8\n",
               "src/rusemod/mapscripts.py": b"# uncompyle6 turns them into text"}
        self.assertEqual(sorted(f.split(":")[0] for f in check(bad)), sorted(bad))

    def test_the_same_words_in_the_other_languages_are_refused(self):
        """The apps' notes and pages are translated (the owner, 2026-10-05): a translation says no more than the
        English may."""
        bad = {"a.fr.md": "nous avons décompilé les scripts", "b.fr.md": "le format, par rétro-ingénierie",
               "c.ger.md": "mit einem Hex-Editor geöffnet", "d.ita.md": "con l'ingegneria inversa",
               "e.spa.md": "lo descompilamos", "f.pol.md": "dzięki inżynierii wstecznej", "g.ru.md": "декомпилировали скрипты",
               "h.ru.md": "из дампа памяти", "i.cz.md": "zpětným inženýrstvím", "j.jpn.md": "逆コンパイルした",
               "k.sc.md": "通过反编译", "l.fr.md": "dans le débogueur", "m.sc.md": "用调试器"}
        fine = {"n.fr.md": "les scripts du jeu, lus ; la structure du fichier, décodée",
                "o.ru.md": "скрипты игры прочитаны; формат файла расшифрован", "p.jpn.md": "ゲームのスクリプトを読み、ファイルの形式を解読"}
        found = check({f"docs/{k}": v.encode("utf-8") for k, v in {**bad, **fine}.items()})
        self.assertEqual(sorted(f.split(":")[0] for f in found), sorted(f"docs/{k}" for k in bad))

    def test_text_that_says_we_go_through_the_whole_of_the_games_data_is_refused(self):
        """The owner, 2026-10-04, on a README line: "Like you literally, exactly say everything in the game data."
        Public text says what changing strictly data can do; anything beyond data is outside the project."""
        bad = {"README.md": b"read-only count of everything in the game data built around the 7 nations",
               "docs/a.md": b"Everything we know about the game's files, with evidence.",
               "docs/b.md": b"**Whole-game verification:** all 38 archives round-trip",
               "docs/c.md": b"ruse index build   index the whole game once per game build",
               "tools/d.py": b'"""Verify the reader/writer against the WHOLE game install."""',
               "tools/e.py": b"Lists every class, across every NDF file in every pack",
               "docs/f.md": b"checks that every archive and data file in the game rebuilds",
               "docs/g.md": b"a read-only survey of how the game mounts packs",
               "docs/l.md": b"truly new mechanics need the runtime extender",
               "docs/m.md": b"Program work happens somewhere else",
               "docs/n.md": b"nobody has said the program can't be edited"}
        fine = {"docs/h.md": b"what changing strictly data can do; anything beyond data is outside this project",
                "docs/i.md": b"the data files a mod can change are written back byte-identically",
                "src/j.py": b"# making a backup copies the whole game, which takes longer",
                "docs/k.md": b"every map the game ships, drawn in 3D",
                "src/ruse_mod_engine/edata.py": b"dump of everything in the game data (LittleGroove's words)"}
        found = check({**bad, **fine})
        self.assertEqual(sorted(f.split(":")[0] for f in found), sorted(bad))
        self.assertIn("strictly data", found[0])

    def test_no_file_may_say_where_in_the_program_any_more(self):
        """The list of the game crashes we know is the private repo's (the owner, 2026-11-24: "Okay, fine. We can
        move it to the private repo."): from 0.9.8.20 to 0.9.8.22 one file of the apps (src/rusemod/crashplaces.py)
        could say "in the game's program"; now none can, that old path included, and a code address, a word on how
        anything was studied or on what the program does is refused everywhere alike. Made-up lines only."""
        import check_public
        self.assertFalse(hasattr(check_public, "PROGRAM_TABLE"))   # the one exception is gone
        where = b"# the place in the game's program where it stops\n"
        for path in ("src/rusemod/knowncrashes.py", "src/rusemod/bugwatch.py", "src/rusemod/crashplaces.py",
                     "docs/crashes.md"):
            self.assertEqual(len(check({path: where})), 1, path)
        refused = [b"# FUN_1400abc00 makes the parts\n", b"PLACE = 0x1400abd00\n",
                   b"PLACE = 0x00000001400abd00\n", b"at 0x14_00ab_d00\n", b"at 00000001`400abd00\n",
                   b"# found by decompiling the program in Ghidra, with a debugger and a minidump\n",
                   b"# the RTTI and vtables, read with a hex editor\n",
                   "# trouvé en décompilant le jeu\n".encode("utf-8"), b"# the game's program holds it\n"]
        for line in refused:
            self.assertEqual(len(check({"src/rusemod/knowncrashes.py": line})), 1, line)
        self.assertEqual(check({"src/rusemod/knowncrashes.py": b"# our list of the game crashes we know\n"}), [])

    def test_the_crash_lists_files_are_refused_by_name_in_any_folder(self):
        """The table's old file and the file the apps keep the list in (rusemod.knowncrashes.LIST_FILE, and its
        last result and its file on the way): refused by name anywhere, whatever they hold, so a copy put back by
        mistake is caught even with harmless words. The apps' own code for the list is not (the control)."""
        harmless = b"x = 1\n"
        for path in ("src/rusemod/crashplaces.py", "crashplaces.py", "private-ish/CrashPlaces.py",
                     "docs/known-crashes.json", "tests/data/known-crashes-last.json",
                     "src/rusemod/known-crashes.1234.abcdef.tmp.json"):
            self.assertEqual(len(check({path: harmless})), 1, path)
            self.assertIn("private repo", check({path: harmless})[0])
        for path in ("src/rusemod/knowncrashes.py", "tests/test_knowncrashes.py", "src/rusemod/crashcode.py",
                     "docs/known-crashes.md"):
            self.assertEqual(check({path: harmless}), [], path)

    def test_the_cheat_list_may_name_its_tool_and_nothing_more(self):
        """Question 14 (the owner, 2026-11-25: "Fourteen's fine, go with your pick."; the question whole in
        check_public's CHEAT_LIST note): RUSE Guard's list of known cheat tools comes inside the app in one file,
        which may name the one tool the check refuses by name; that name is refused in every other file, and every
        other word the check refuses is refused in the list as anywhere. The real list passes."""
        import check_public
        listed = "src/rusemod/guard_cheat_tools.toml"
        real = (Path(__file__).resolve().parents[1] / listed).read_bytes()
        self.assertIn(b"Cheat Engine", real)                        # (it does name it)
        self.assertEqual(check({listed: real}), [])                 # (the check of Launcher 0.4.8.22 refused it)
        self.assertEqual(check_public.CHEAT_LIST, listed)           # one file, not a list of files
        for elsewhere in ("src/rusemod/guard.py", "src/rusemod/guard_cheat_tools2.toml", "README.md",
                          "src/ruse_launcher/words.toml", "docs/wiki/Home.md"):
            self.assertEqual(len(check({elsewhere: real})), 1, elsewhere)   # the very same text: refused there
        named = b'name = "cheat engine.exe"\nwhat = "Cheat Engine, a memory editor"\n'
        self.assertEqual(check({listed: named}), [])
        self.assertEqual(len(check({"src/rusemod/guard.py": named})), 1)
        for line in (b"# found with a debugger and a hex editor\n", b"# FUN_1400abc00 holds the names\n",
                     b"# we decompiled the game for it\n", b"# CHEAT ENGINE, written another way\n",
                     b"# the program reads the list\n"):
            self.assertEqual(len(check({listed: line})), 1, line)                     # refused in the list
        self.assertEqual(len(check({"private/" + listed: real})), 1)

    def test_the_released_table_is_refused_at_its_old_path(self):
        """The table as 0.9.8.22 released it (6b265ec1), read from this repository's history when it has that commit
        (a shallow copy hasn't: skipped): refused at its old path, by its name and by its words."""
        import subprocess
        root = Path(__file__).resolve().parents[1]
        ran = subprocess.run(["git", "-C", str(root), "show", "6b265ec1:src/rusemod/crashplaces.py"],
                             capture_output=True)
        if ran.returncode != 0 or not ran.stdout:
            self.skipTest("this copy of the repository hasn't got 0.9.8.22's commit")
        table = ran.stdout
        self.assertEqual(len(check({"src/rusemod/crashplaces.py": table})), 1)
        self.assertEqual(len(check({"src/rusemod/elsewhere.py": table})), 1)   # its words alone refuse it too
        self.assertFalse((root / "src" / "rusemod" / "crashplaces.py").exists())


if __name__ == "__main__":
    unittest.main()
