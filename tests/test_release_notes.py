"""Every language's release notes in one file beside the installer (installers/notes_json.py): the apps show what's
new in their own language (the owner, 2026-10-05: "Translated every language ... inclusive for every language we cover
in the mod")."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "installers"))
import notes_json  # noqa: E402

from rusemod import update  # noqa: E402

ENGLISH = "**RUSE Studio.** Intro.\n\n**0.9.7:** fast.\n| Before | Now |\n|---|---|\n| Slow. | Fast. |\n\n**0.9.6:** older.\n"
FRENCH = "**RUSE Studio.** Intro.\n\n**0.9.7:** rapide.\n| Avant | Maintenant |\n|---|---|\n| Lent. | Rapide. |\n"


class Book(unittest.TestCase):
    def notes(self, files):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        for name, text in files.items():
            (Path(d.name) / name).write_text(text, encoding="utf-8")
        return Path(d.name)

    def test_english_and_each_language(self):
        book = notes_json.book("studio", self.notes({"studio.md": ENGLISH, "studio.fr.md": FRENCH,
                                                     "launcher.ger.md": "**0.4.7:** x\n"}))
        self.assertEqual(sorted(book), ["fr", "us"])  # the Launcher's German isn't the Studio's
        rows = update.changes_since(book["fr"], "0.9.6", "0.9.7")
        self.assertEqual([(r["before"], r["now"]) for r in rows], [("Lent.", "Rapide.")])
        links = notes_json.links("studio", "studio-v0.9.8", book)
        self.assertEqual(links, "[Français](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/studio-v0.9.8/"
                                ".github/release-notes/studio.fr.md)")

    def test_what_the_apps_would_misread_is_refused(self):
        for name, text, why in (("studio.fr.md", FRENCH.replace("**0.9.7:**", "**0.9.7 :**"), "space before its colon"),
                                ("studio.fr.md", "Pas de version.\n", "no version's notes"),
                                ("studio.fr.md", FRENCH.replace("0.9.7", "0.9.9"), "0.9.9 isn't in the English"),
                                ("studio.xx.md", FRENCH, "isn't one of the apps' languages")):
            with self.subTest(why=why), self.assertRaisesRegex(notes_json.NotesError, why):
                notes_json.book("studio", self.notes({"studio.md": ENGLISH, name: text}))

    def test_the_file_written(self):
        root = self.notes({"studio.md": ENGLISH, "studio.fr.md": FRENCH})
        with tempfile.TemporaryDirectory() as out:
            old = notes_json.NOTES
            notes_json.NOTES = root
            try:
                self.assertEqual(notes_json.main(["studio", out]), 0)
            finally:
                notes_json.NOTES = old
            data = json.loads((Path(out) / "RUSE-Studio-notes.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(data), ["fr", "us"])
            self.assertEqual(update.NOTES_ASSET.format(app="Studio"), "RUSE-Studio-notes.json")

    def test_the_repo_s_own_notes_can_be_read_by_the_apps(self):
        for app in notes_json.APPS:
            with self.subTest(app=app):
                book = notes_json.book(app)  # refuses a translation the apps would misread
                self.assertIn("us", book)
                newest = notes_json.versions(book["us"])[0]
                for code, text in book.items():
                    if code != "us" and newest in notes_json.versions(text):
                        self.assertTrue(update.changes_since(text, "0.0.0", newest), f"{app}.{code}.md")

    def test_the_release_publishes_the_file(self):
        flow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("python installers/notes_json.py", flow)
        self.assertIn("$setup.FullName $book.FullName", flow)
        self.assertIn("Read these notes in:", flow)


if __name__ == "__main__":
    unittest.main()
