"""The public-repo guard (tools/check_public.py): private material, game files and program addresses are refused.

Checked our_tools.json: none of its tools runs this check; these tests read no program, only made-up lines that name
the words the check refuses, and the crash table's own numbers, by name, to look for them in the other files."""
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

    def test_the_crash_table_may_say_where_in_the_program_and_nothing_more(self):
        """Item 25 (the owner, 2026-11-13, his words whole in check_public's PROGRAM_TABLE note: "... if their unit
        was crashing the game, they should be told that." ... "You can put it in the app. ..."): the table of the game
        crashes we know is in the public apps in one file, which may say
        where they are, "in the game's program", and nothing more than any other file: a code address, a word on how
        anything was studied (in any language) or on what the program does is refused there as in bugwatch.py. Made-up
        lines only."""
        import check_public
        table_file = check_public.PROGRAM_TABLE
        self.assertIsInstance(table_file, str)                      # one file, not a list
        table = (Path(__file__).resolve().parents[1] / table_file).read_bytes()
        self.assertEqual(check({table_file: table}), [])
        for elsewhere in ("src/rusemod/bugwatch.py", "src/rusemod/crashplaces2.py", "docs/crashes.md"):
            self.assertEqual(len(check({elsewhere: table})), 1, elsewhere)   # the very same text: refused there
        where = b"# the place in the game's program where it stops\n"
        self.assertEqual(check({table_file: where}), [])            # the one thing it may say
        self.assertEqual(len(check({"src/rusemod/bugwatch.py": where})), 1)
        refused = [b"# FUN_1400abc00 makes the parts\n", b"PLACE = 0x1400abd00\n",
                   b"# found by decompiling the program in Ghidra, with a debugger and a minidump\n",
                   b"# we reverse-engineered the game for this table\n",
                   b"# the RTTI and vtables, read with a hex editor\n",
                   "# trouvé en décompilant le jeu\n".encode("utf-8"), "# 逆コンパイルで見つけた\n".encode("utf-8"),
                   b"# the program reads it here\n", b"# the game's program holds it\n",
                   b"# a part kept in the program\n", b"# a count of the whole game\n"]
        for line in refused:
            self.assertEqual(len(check({table_file: line})), 1, line)                    # refused in the table
            self.assertEqual(len(check({"src/rusemod/bugwatch.py": line})), 1, line)     # as anywhere else
        self.assertEqual(len(check({"private/" + table_file: table})), 1)

    def test_the_crash_tables_details_stand_in_no_other_file(self):
        """Item 25: the details of the game's program the crash table holds (its places, the functions its chains are
        checked against and the unit descriptions' tables, as numbers, and the program's own parts it names) are in
        no file of the apps but the table, the tests and this check's own included (they are looked for by name from
        the table, never written out)."""
        import re
        from rusemod import crashplaces
        root = Path(__file__).resolve().parents[1]
        table = (root / "src" / "rusemod" / "crashplaces.py").read_text(encoding="utf-8")
        numbers = set(crashplaces.PLACES) | set(crashplaces.UNIT_CLASSES) | set(crashplaces.PART_BY_NAME) | \
            set(crashplaces.CREATING) | {n for span in crashplaces.TWO_AXIS for n in span}
        parts = set(re.findall(r"\b(T[A-Z][A-Za-z0-9]+)(?:'s)?\W{0,3}(?:its )?(?:virtual function|constructor)", table))
        self.assertGreaterEqual(len(parts), 5)                      # (the table names them so)
        said = re.compile("|".join([rf"\b(?:0x|FUN_14|sub_14|0x14)0*{n:x}\b" for n in sorted(numbers)]
                                   + [rf"\b{p}\b" for p in sorted(parts)]), re.I)
        found = []
        for path in root.rglob("*"):
            rel = path.relative_to(root).as_posix()
            if not path.is_file() or rel == "src/rusemod/crashplaces.py" or \
                    {".git", "__pycache__", "node_modules"} & set(path.relative_to(root).parts):
                continue
            data = path.read_bytes()
            if b"\0" in data[:8192] or len(data) > 4_000_000:
                continue
            text = data.decode("utf-8", "replace")
            found += [f"{rel}:{text.count(chr(10), 0, m.start()) + 1}: {m.group(0)}" for m in said.finditer(text)]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
