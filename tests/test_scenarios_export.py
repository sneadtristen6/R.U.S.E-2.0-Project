"""Export scenarios: the usual and unusual situations a player can find himself in when he makes a mod in the Studio
and exports it (the owner, overnight 2026-11-14: "really limit test some of the unique situations players can find
themselves in when building new things with ... our apps"; "Not just unusual. Usual and unusual situations. Player can
find themselves in when making new mods in our apps").

Each situation is a test. One that shows something wrong is kept as @unittest.expectedFailure, its docstring naming
the finding (FE-n, D:/RUSE-2.0/scratch/release-0920/scenarios/export/FINDINGS.md): it starts to pass once the finding
is mended, and then its mark comes off. Made-up mods and names only, a Studio on a fresh platform folder of each test's
own, no game (Export packs without a build then, as when R.U.S.E. isn't found), the Recycle Bin stood in for (a folder
of the test's: never the PC's). The Launcher's library side is tests/test_scenarios_export_library.py. Not repeated
here: two mods in one set and the units a player makes (work/0920c-scen-units)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import os
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from rusemod import package
from rusemod.library import Library
from ruse_studio.api import StudioApi, StudioError

# a mod's name, its author, its description and its README in the script of each of the apps' 11 languages
SCRIPTS = {
    "us": ("Tank Test", "Jane Doe", "Tanks are tougher.", "# Tank Test\nTanks are tougher, by a third.\n"),
    "fr": ("Équipe de char", "Jérôme Dupré", "Des chars plus résistants.", "Les chars résistent mieux. Ça marche !\n"),
    "ger": ("Panzer Übung", "Jürgen Weiß", "Panzer halten mehr aus.", "Größere Panzer, schöne Grüße.\n"),
    "ita": ("Carri armati più forti", "Niccolò Rossi", "I carri resistono di più.", "Perché no? È così.\n"),
    "spa": ("Tanques más fuertes", "José Núñez", "Los tanques aguantan más.", "¿Por qué no? ¡Sí, señor!\n"),
    "pol": ("Mocniejsze czołgi", "Łukasz Żółć", "Czołgi są wytrzymalsze.", "Zażółć gęślą jaźń.\n"),
    "ru": ("Крепкие танки", "Иван Петров", "Танки крепче.", "Съешь же ещё этих мягких французских булок.\n"),
    "cz": ("Silnější tanky", "Jiří Dvořák", "Tanky vydrží víc.", "Příliš žluťoučký kůň úpěl ďábelské ódy.\n"),
    "jpn": ("強い戦車", "山田 太郎", "戦車が丈夫になります。", "いろはにほへと ちりぬるを\n"),
    "sc": ("更强的坦克", "张伟", "坦克更耐打。", "我能吞下玻璃而不伤身体。\n"),
    "fa": ("تانک‌های قوی‌تر", "علی رضایی", "تانک‌ها مقاوم‌ترند.", "این یک متن آزمایشی است.\n"),
}
PATCH = "patch $/B ( ProductionPrice *= 0.5 )\n"   # (a change any mod can carry: the build reads it)


def members(path) -> dict:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


class Studio(unittest.TestCase):
    """A Studio on a fresh platform folder of its own, no game, the Recycle Bin a folder of the test's."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="scen-export-")
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.api = self.studio(self.home)
        binned = mock.patch("rusemod.recycle.to_recycle_bin",
                            side_effect=lambda p: Path(p).rename(self.bin / f"{len(list(self.bin.iterdir()))}-"
                                                                             f"{Path(p).name}"))
        binned.start()
        self.addCleanup(binned.stop)

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def studio(home: Path) -> StudioApi:
        api = StudioApi(home=home, instances=home / "copies")
        api._game = lambda: None                       # (no game found: Export packs without a build)
        return api

    def make(self, name: str, api=None) -> Path:
        """A new mod called `name`, with one change in it; its folder."""
        api = api or self.api
        folder = Path(api.new_mod(name)["current"])
        (folder / "src" / "units.rndf").write_text(PATCH, encoding="utf-8")
        return folder

    def export(self, version: str, author: str = "", description: str = "", api=None) -> dict:
        api = api or self.api
        job = api.export_mod(version, author, description)["job"]
        end = time.monotonic() + 60
        while api.job(job)["state"] == "running" and time.monotonic() < end:
            time.sleep(0.02)
        return api.job(job)

    def library(self, home=None) -> dict:
        """{id: (name, version, author, description)} of the Launcher's library on the platform folder `home`."""
        return {m["id"]: (m["name"], m["version"], m["author"], m["description"])
                for m in Library((home or self.home) / "library").mods()}

    @staticmethod
    def said(view, start: str) -> list:
        return [ln for ln in view["lines"] if ln.startswith(start)]


class Usual(Studio):
    """What most players do: make a mod, export it, export a new version, make it again."""

    def test_a_first_mod_goes_out_with_what_he_typed(self):
        folder = self.make("Tank Test")
        (folder / "README.md").write_text("# Tank Test\nTanks are tougher.\n", encoding="utf-8")
        view = self.export("1.0.0", "Jane Doe", "Tanks are tougher.")
        self.assertEqual(view["state"], "done", view.get("message"))
        out = self.home / "exports" / "tank-test-1.0.0.rusemod"
        self.assertEqual(view["result"]["path"], str(out))
        info = package.check(out)
        self.assertEqual((info["id"], info["name"], info["version"], info["authors"], info["description"]),
                         ("tank-test", "Tank Test", "1.0.0", ["Jane Doe"], "Tanks are tougher."))
        self.assertEqual(members(out)["README.md"], (folder / "README.md").read_bytes())
        self.assertEqual(self.library(), {"tank-test": ("Tank Test", "1.0.0", "Jane Doe", "Tanks are tougher.")})
        self.assertEqual(self.said(view, "In the Launcher's mod library"),
                         ["In the Launcher's mod library as Tank Test 1.0.0: tick it in a mod set and press Play."])

    def test_a_new_version_replaces_the_one_in_the_library_and_both_files_stay(self):
        self.make("Tank Test")
        self.assertEqual(self.export("1.0.0", "Jane Doe", "First.")["state"], "done")
        view = self.export("1.1.0", "", "")
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(self.library(), {"tank-test": ("Tank Test", "1.1.0", "Jane Doe", "First.")})  # (blank: kept)
        self.assertEqual(sorted(p.name for p in (self.home / "exports").iterdir()),
                         ["tank-test-1.0.0.rusemod", "tank-test-1.1.0.rusemod"])
        self.assertEqual(self.said(view, "In the Launcher's mod library"),
                         ["In the Launcher's mod library as Tank Test 1.1.0 (the older version replaced): tick it in a "
                          "mod set and press Play."])

    def test_the_same_version_exported_again_writes_its_file_again(self):
        folder = self.make("Tank Test")
        first = self.export("1.0.0", "Jane Doe", "")
        (folder / "src" / "units.rndf").write_text(PATCH.replace("0.5", "0.4"), encoding="utf-8")
        again = self.export("1.0.0", "Jane Doe", "")
        self.assertEqual((first["state"], again["state"]), ("done", "done"))
        out = self.home / "exports" / "tank-test-1.0.0.rusemod"
        self.assertIn(b"0.4", members(out)["src/units.rndf"])          # (the file is the mod as it is now)
        self.assertNotEqual(first["result"]["sha256"], again["result"]["sha256"])

    def test_names_and_words_in_every_language_s_script(self):
        """A name, an author, a description and a README in each of the 11 languages' scripts: each goes out as he
        typed it, and the Launcher's library shows it so."""
        made = {}
        for lang, (name, author, description, readme) in SCRIPTS.items():
            with self.subTest(lang=lang):
                folder = self.make(name)
                (folder / "README.md").write_bytes(readme.encode("utf-8"))
                view = self.export("1.0.0", author, description)
                self.assertEqual(view["state"], "done", view.get("message"))
                info = package.check(view["result"]["path"])
                self.assertEqual((info["name"], info["authors"], info["description"]), (name, [author], description))
                self.assertEqual(members(view["result"]["path"])["README.md"], readme.encode("utf-8"))
                self.assertIn(f"In the Launcher's mod library as {name} 1.0.0", "\n".join(view["lines"]))
                made[info["id"]] = (name, "1.0.0", author, description)
        self.assertEqual(self.library(), made)                          # (11 mods, none replacing another)

    def test_a_big_mod_of_many_files(self):
        folder = self.make("Big One")
        notes = folder / "files" / "notes"
        notes.mkdir(parents=True)
        for k in range(1500):
            (notes / f"note-{k:04}.txt").write_text(f"note {k}\n" * 20, encoding="utf-8")
        start = time.monotonic()
        view = self.export("1.0.0", "Jane Doe", "")
        took = time.monotonic() - start
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(sum(1 for n in members(view["result"]["path"]) if n.startswith("files/notes/")), 1500)
        self.assertIn("big-one", self.library())
        self.assertLess(took, 60, "Export of 1,500 small files took over a minute")

    def test_deleted_and_made_again_under_its_name(self):
        """He deletes a mod he exported (its Launcher copy left), makes a new one of the same name and exports it: the
        new one is in the library, the old one in the Recycle Bin; nothing of the old one goes with the new."""
        old = self.make("Remake")
        (old / "README.md").write_text("The first one.\n", encoding="utf-8")
        self.assertEqual(self.export("2.0.0", "Jane Doe", "The first one.")["state"], "done")
        self.api.delete_mod(str(old))
        new = self.make("Remake")
        self.assertEqual(new, old)                                       # (the same name, so the same folder and id)
        view = self.export("1.0.0", "Jane Doe", "Made again.")
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(self.library(), {"remake": ("Remake", "1.0.0", "Jane Doe", "Made again.")})
        self.assertNotIn("README.md", members(view["result"]["path"]))
        self.assertEqual([p.name.split("-", 1)[1] for p in self.bin.iterdir()], ["remake"])

    def test_deleted_with_its_launcher_copy_and_made_again(self):
        old = self.make("Remake")
        self.assertEqual(self.export("2.0.0", "Jane Doe", "")["state"], "done")
        self.assertTrue(self.api.delete_mod(str(old), launcher=True)["launcher"])
        self.assertEqual(self.library(), {})
        self.make("Remake")
        view = self.export("1.0.0", "Jane Doe", "")
        self.assertEqual(self.said(view, "In the Launcher's mod library"),
                         ["In the Launcher's mod library as Remake 1.0.0: tick it in a mod set and press Play."])

    def test_save_as_a_name_without_its_ending_and_a_map_from_the_maps_tab(self):
        chosen = self.root / "chosen" / "My Mod"                          # (a folder not there yet, no ending typed)
        self.api._pick_save = lambda suggested: str(chosen)
        self.make("Picked")
        view = self.export("1.0.0", "Jane Doe")
        self.assertEqual((view["state"], view["result"]["path"]), ("done", str(chosen) + ".rusemod"))
        self.api._pick_save = None
        Path(self.api.new_mod("Beach Map", kind="map")["current"])
        job = self.api.export_mod("1.0.0", "Jane Doe", "", kind="map")["job"]
        end = time.monotonic() + 60
        while self.api.job(job)["state"] == "running" and time.monotonic() < end:
            time.sleep(0.02)
        self.assertEqual(self.api.job(job)["result"]["path"], str(self.home / "exports" / "beach-map-1.0.0.rusemod"))
        self.assertIn("beach-map", self.library())

    def test_a_version_he_types_with_spaces_or_leading_zeros(self):
        self.make("Versions")
        self.assertEqual(self.export(" 1.2.3 ")["result"]["path"], str(self.home / "exports" / "versions-1.2.3.rusemod"))
        self.assertEqual(self.export("01.02.03")["state"], "done")
        for typed in ("1.0", "1.0.0-beta", "v1.0.0", "1.0.0.0", "", "one"):
            with self.subTest(typed=typed), self.assertRaisesRegex(StudioError, "three numbers, like 1.0.0"):
                self.api.export_mod(typed)


class Unusual(Studio):
    """What fewer players do, and what goes wrong then (each finding in FINDINGS.md)."""

    def test_FE1_a_name_with_an_emoji(self):
        """FE-1: new_mod("🚀 Rockets") stopped with "couldn't update ...mod.toml: Escaped character is not a Unicode
        scalar value" and left a folder whose mod.toml nothing could read (its name written as \\ud83d\\ude80)
        (release adc8ecea). PROPOSED FIX: the name is written as TOML writes it (package._toml)."""
        for name in ("\U0001f680 Rockets", "Tanks \"Heavy\" \\ Light", "\U00020000\U0001f3c6"):
            with self.subTest(name=name):
                folder = Path(self.api.new_mod(name)["current"])
                self.assertEqual(package.info_of(folder)["name"], name)
                view = self.export("1.0.0")
                self.assertEqual(view["state"], "done", view.get("message"))
                self.assertEqual(package.check(view["result"]["path"])["name"], name)

    def test_FE3_accented_letters_stay_in_the_mod_s_id(self):
        """FE-3: the id (and the file's name) was made by dropping every letter that isn't a to z: "Équipe de char" was
        quipe-de-char, "Panzer Übung" panzer-bung, "Tanques ñandú" tanques-and, "Tanky č. 2" tanky-2 (release
        adc8ecea). PROPOSED FIX: the letters without their accents first (NFKD, as safe_name does for a unit)."""
        for name, want in (("Équipe de char", "equipe-de-char"), ("Panzer Übung", "panzer-ubung"),
                           ("Tanques ñandú", "tanques-nandu"), ("Tanky č. 2", "tanky-c-2")):
            with self.subTest(name=name):
                self.assertEqual(Path(self.api.new_mod(name)["current"]).name, want)

    def test_FE4_a_long_name(self):
        """FE-4: a name of 300 letters made a folder name Windows refuses: new_mod raised Windows' own "[WinError 3]
        The system cannot find the path specified" (an OSError, no words of the Studio's; release adc8ecea). PROPOSED
        FIX: the id (the folder's and the file's name) is at most api.ID_MOST letters, cut at a word; the name stays
        whole in mod.toml, and the mod goes out."""
        name = ("Panzer " * 43).strip()
        folder = Path(self.api.new_mod(name)["current"])
        self.assertEqual(folder.name, "panzer-panzer-panzer-panzer-panzer")
        self.assertEqual(package.info_of(folder)["name"], name)
        self.assertEqual(Path(self.api.new_mod("x" * 300)["current"]).name, "x" * 40)
        view = self.export("1.0.0")
        self.assertEqual(view["state"], "done", view.get("message"))

    def test_FE5_a_version_typed_in_other_digits(self):
        """FE-5: a version typed with full-width digits (a Japanese or Chinese keyboard's) or Persian ones is taken as
        it is: the file is versions-１.０.０.rusemod and the library shows １.０.０ (Python's \\d takes every script's
        digits; so on the release, adc8ecea). Wanted: taken as 1.0.0, or refused with the three-numbers words.
        PROPOSED FIX: taken as 1.0.0, full-width dots too (api._ascii_digits)."""
        self.make("Versions")
        for typed in ("\uff11.\uff10.\uff10", "\u06f1.\u06f0.\u06f0", "\uff11\uff0e\uff10\uff0e\uff10"):
            with self.subTest(typed=typed):
                try:
                    view = self.export(typed)
                except StudioError as exc:
                    self.assertIn("three numbers", str(exc))
                    continue
                self.assertEqual(Path(view["result"]["path"]).name, "versions-1.0.0.rusemod")

    def test_FE6_a_character_pasted_into_the_author_or_description(self):
        """FE-6: a control character pasted into the author or the description (a vertical tab, a bell) or a line
        separator (U+2028, from a web page or a word processor) stopped Export with Python's TOML words: "couldn't
        update ...mod.toml: Illegal character '\\n' (at line 6, column 17)" (release adc8ecea). PROPOSED FIX: mod.toml
        holds such a character as \\uXXXX (package._toml), so it stays as he typed it and every export goes on."""
        self.make("Pasted")
        for n, (author, description) in enumerate((("Jane\x0bDoe", ""), ("", "first\u2028second"), ("", "bell\x07"))):
            with self.subTest(author=author, description=description):
                view = self.export(f"1.0.{n}", author, description)
                self.assertEqual(view["state"], "done", view.get("message"))
                info = package.check(view["result"]["path"])
                if author:
                    self.assertEqual(info["authors"], [author])
                if description:
                    self.assertEqual(info["description"], description)
        self.assertEqual(self.export("1.1.0")["state"], "done")          # (and the next export, with them kept)

    @unittest.expectedFailure
    def test_FE7_his_own_files_at_the_top_go_along_or_are_named(self):
        """FE-7: README.txt, CREDITS.md, LICENSE.md and NOTICE.txt at the mod's top, and a docs/ folder, are left out
        of the exported file, and Export says nothing (only mod.toml, README.md, LICENSE, CHANGELOG.md and the other
        TOP_FILES go): a CC-BY credit he wrote into CREDITS.md doesn't reach the players."""
        folder = self.make("Credits")
        mine = ["README.txt", "CREDITS.md", "LICENSE.md", "NOTICE.txt", "docs/guide.md"]
        for rel in mine:
            (folder / rel).parent.mkdir(parents=True, exist_ok=True)
            (folder / rel).write_text(f"{rel}: a model by someone, CC-BY 4.0\n", encoding="utf-8")
        view = self.export("1.0.0")
        out = members(view["result"]["path"])
        told = "\n".join(view["lines"])
        for rel in mine:
            with self.subTest(file=rel):
                self.assertTrue(rel in out or rel in told, f"{rel} neither in the file nor named")

    @unittest.expectedFailure
    def test_FE8_the_library_line_says_what_it_replaced(self):
        """FE-8: Export says "(the older version replaced)" whatever was there: the same version again, a newer one
        (3.0.0, after which he exports 2.0.0), and another mod made again under the same name."""
        self.make("Tank Test")
        self.export("1.0.0")
        lines = [self.said(self.export(v), "In the Launcher's mod library")[0] for v in ("1.0.0", "3.0.0", "2.0.0")]
        self.assertNotIn("(the older version replaced)", lines[0])       # (the same version)
        self.assertNotIn("(the older version replaced)", lines[2])       # (3.0.0 was there: not older)

    @unittest.expectedFailure
    def test_FE12_a_mod_past_the_size_a_launcher_takes(self):
        """FE-12: Export packs a mod past package.SIZE_LIMIT (500 MB unpacked), then its own check of the file stops
        the job: "big-1.0.0.rusemod would unpack to ... MB, far more than a mod of data files; it isn't unpacked",
        words about unpacking after the packing is done, and the file no Launcher takes is left in Exports. (The
        limit made small here, as a real 500 MB mod is too big for a test.)"""
        self.make("Big")
        with mock.patch.object(package, "SIZE_LIMIT", 100):
            view = self.export("1.0.0")
        self.assertEqual(view["state"], "failed")
        self.assertEqual(sorted(p.name for p in (self.home / "exports").iterdir()), [])
        self.assertNotIn("unpack", view["message"])

    @unittest.skipUnless(sys.platform == "win32", "Windows' file locks")
    def test_FE13_a_file_another_program_holds(self):
        """FE-13: a file of the mod another program holds (Excel keeps a .csv it has open locked) stopped Export with
        "[Errno 13] Permission denied": Python's words, no file named (release adc8ecea). Wanted: the Studio's own
        words, naming the file and saying to close the program (api.file_error). PROPOSED FIX: pack names the file
        that can't be read (package.named_file) and Export says it in the Studio's words; nothing half made is left."""
        import msvcrt
        folder = self.make("Held")
        held = folder / "text" / "units.csv"
        held.parent.mkdir(parents=True)
        held.write_text("key,us\nk1,Text\n", encoding="utf-8")
        with open(held, "r+b") as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 8)
            try:
                view = self.export("1.0.0")
            finally:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 8)
        self.assertEqual(view["state"], "failed")
        self.assertEqual(view["message"], f"{held} couldn't be read or written, because another program has it open or "
                                          f"Windows didn't allow it. Close that program, then try again.")
        self.assertEqual(list((self.home / "exports").iterdir()), [])     # (nothing half made left)
        self.assertEqual(self.export("1.0.0")["state"], "done")           # (and once it's let go, it goes out)


    @unittest.skipUnless(sys.platform == "win32", "Windows keeps a folder with an open file in it in its place")
    @unittest.expectedFailure
    def test_FE14_the_library_copy_held_while_export_adds_the_new_version(self):
        """FE-14, the Studio's side: a file of the mod's copy in the Launcher's library open in another program while
        he exports a new version: the file is saved, but the job ends "failed" with Windows' own words, "[WinError 5]
        Access is denied: '...library\\held' -> '...library\\.old-held'", and no line about the library. Wanted: the
        export done, and a line saying the library's copy couldn't be replaced, and what to close."""
        self.make("Held")
        self.assertEqual(self.export("1.0.0")["state"], "done")
        with open(self.home / "library" / "held" / "mod.toml", "rb"):
            view = self.export("1.1.0")
        self.assertTrue((self.home / "exports" / "held-1.1.0.rusemod").is_file())
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertTrue(self.said(view, "Not added to the Launcher's library"), view["lines"])

    def test_FE15_export_clicked_again_while_it_runs(self):
        """FE-15: Export started again while the first still runs (the page lets Export… open again during a long
        build) ran both at once on one file: on the release (adc8ecea) one ended with "[WinError 5] Access is denied:
        ...twice-1.0.0.rusemod.part -> ...twice-1.0.0.rusemod", and the half-written .part was left in Exports.
        Wanted: the second waits for the first, or is refused at once in words; nothing half written left. PROPOSED
        FIX: refused at once with the Studio's busy words, and pack never leaves its .part beside the target."""
        self.make("Twice")
        real = self.api._share_view

        def reading(path):                   # (the first export still reading its file when the second packs: as a
            with open(path, "rb"):           # big mod's SHA-256 takes a moment; made long here, so it always meets)
                time.sleep(3)
            return real(path)
        self.api._share_view = reading
        jobs = []
        for _ in range(2):
            try:
                jobs.append(self.api.export_mod("1.0.0", "Jane Doe", "")["job"])
            except StudioError as exc:                                   # (refused at once in words: fine)
                self.assertNotIn("another program", str(exc))
        end = time.monotonic() + 120
        while any(self.api.job(j)["state"] == "running" for j in jobs) and time.monotonic() < end:
            time.sleep(0.05)
        for j in jobs:
            self.assertNotIn("another program", self.api.job(j).get("message") or "")
        self.assertEqual(sorted(p.name for p in (self.home / "exports").iterdir()), ["twice-1.0.0.rusemod"])


if __name__ == "__main__":
    unittest.main()
