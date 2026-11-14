"""Export scenarios with the game found: the way most players export, the mod built on the game first (the owner,
overnight 2026-11-14: "Usual and unusual situations. Player can find themselves in when making new mods in our apps").

On test_studio's made-up game (its WithMod: a game folder and its index, a fresh platform folder per test, nothing
starts for real; never the PC's own game). Export builds the mod on it to record the game's data and the mod's
fingerprint, as on a player's PC. A finding (FE-n, the scenario report's FINDINGS) is kept as
@unittest.expectedFailure, its docstring naming it."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import os
import sys
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_studio import M4, WithMod
from rusemod import package
from rusemod.library import Library


class Built(WithMod):
    def setUp(self):
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("RUSE_GAME", None)                # (the made-up game only, never the PC's own)
        super().setUp()

    def export(self, version: str, author: str = "") -> dict:
        job = self.api.export_mod(version, author, "")["job"]
        end = time.monotonic() + 120
        while self.api.job(job)["state"] == "running" and time.monotonic() < end:
            time.sleep(0.02)
        return self.api.job(job)

    def test_a_mod_built_on_the_game_goes_out_with_its_fingerprint(self):
        self.api.new_mod("Tank Test")
        self.api.edit(M4, "SeuilMort", 15)
        view = self.export("1.0.0", "Jane Doe")
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertIn("Building the mod on the game, to record the game build and the fingerprint…", view["lines"])
        info = package.check(view["result"]["path"])
        self.assertRegex(info["fingerprint"], r"^[0-9A-Z]{4}-[0-9A-Z]{4}$")
        self.assertIn("tank-test", {m["id"] for m in Library(self.home / "library").mods()})

    def test_a_mod_with_a_mistake_goes_nowhere(self):
        """A file of his with a mistake: Export says the build's words and nothing goes out, nothing is left half
        made, the Launcher's library as it was."""
        folder = Path(self.api.new_mod("Broken")["current"])
        (folder / "src" / "broken.rndf").write_text("patch $/GFX/Everything/Nope ( X = \n", encoding="utf-8")
        view = self.export("1.0.0")
        self.assertEqual(view["state"], "failed")
        self.assertFalse((self.home / "exports").is_dir() and any((self.home / "exports").iterdir()))
        self.assertEqual(Library(self.home / "library").mods(), [])
        self.assertNotIn("Traceback", view["message"])

    def test_a_file_name_in_another_script_inside_the_mod(self):
        """A file of his named in Russian, Japanese or Persian in his mod's files: it goes out and comes back in
        another player's library under the same name."""
        folder = Path(self.api.new_mod("Names")["current"])
        names = ["files/notes/заметки.txt", "files/notes/メモ.txt", "files/notes/یادداشت.txt"]
        for rel in names:
            (folder / rel).parent.mkdir(parents=True, exist_ok=True)
            (folder / rel).write_text(rel, encoding="utf-8")
        view = self.export("1.0.0")
        self.assertEqual(view["state"], "done", view.get("message"))
        with zipfile.ZipFile(view["result"]["path"]) as z:
            self.assertTrue(set(names) <= set(z.namelist()), z.namelist())
        other = Library(Path(self.tmp.name) / "friend-library")
        info, _replaced = other.add(view["result"]["path"])
        for rel in names:
            self.assertEqual((Path(info["path"]) / rel).read_text(encoding="utf-8"), rel)

    @unittest.skipUnless(sys.platform == "win32", "Windows' file locks")
    def test_FE13_a_file_another_program_holds_while_it_is_built(self):
        """FE-13 with the game found: the build reads the mod first, and a file another program holds stopped it with
        "[Errno 13] Permission denied" on the release (adc8ecea). PROPOSED FIX (89885b28): the Studio's words, naming
        the file."""
        import msvcrt
        folder = Path(self.api.new_mod("Held")["current"])
        self.api.edit(M4, "SeuilMort", 15)
        held = folder / "text" / "units.csv"
        held.parent.mkdir(parents=True, exist_ok=True)
        held.write_text("key,us\nk1,Text\n", encoding="utf-8")
        with open(held, "r+b") as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 8)
            try:
                view = self.export("1.0.0")
            finally:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 8)
        self.assertEqual((view["state"], view["message"]),
                         ("failed", f"{held} couldn't be read or written, because another program has it open or "
                                    f"Windows didn't allow it. Close that program, then try again."))


if __name__ == "__main__":
    unittest.main()
