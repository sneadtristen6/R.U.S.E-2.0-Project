"""The privacy code (the owner, 2026-11-25, question 13: "Settings shows a short code that finds your own RUSE Guard
records, for privacy requests"; 12: "Yes, build it"). It is made from what every RUSE Guard bundle already carries,
the install's public key (client_key), so nothing new is sent:

    privacy_code(client_key_hex) = the first 12 characters of base32 (RFC 4648, upper case, no padding) of
    SHA-256(b"RUSE-GUARD-PRIVACY-1:" + bytes.fromhex(client_key_hex)), shown as XXXX-XXXX-XXXX.

The same two test vectors are in the servers' repo's test. Settings of both apps shows it, read-only, with a tooltip;
an install with no key yet is told how the code is made, and no key is made just to show it."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import ed25519, guard
from ruse_launcher.api import LauncherApi
from ruse_studio.api import StudioApi

ROOT = Path(__file__).resolve().parents[1]
LANGS = ["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa"]
VECTORS = {"0" * 64: "FRRR-IM2K-4RUX", "f" * 64: "HFGC-7FTX-32YL"}   # computed once, written into both repos' tests


class Definition(unittest.TestCase):
    def test_the_two_shared_vectors(self):
        for key, code in VECTORS.items():
            self.assertEqual(guard.privacy_code(key), code)

    def test_the_shape(self):
        code = guard.privacy_code(ed25519.public_key(b"\x07" * 32).hex())
        self.assertRegex(code, r"^[A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4}$")


class OwnCode(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def apps(self):
        return {"launcher": LauncherApi(home=self.tmp / "launcher", game_dir=self.tmp / "nowhere"),
                "studio": StudioApi(game_dir=self.tmp / "nowhere", home=self.tmp / "studio",
                                    index_path=self.tmp / "x.sqlite")}

    def test_no_key_yet_shows_nothing_and_makes_no_key(self):
        for name, api in self.apps().items():
            with self.subTest(app=name):
                self.assertEqual(api.guard_privacy_code(), {"code": ""})
                self.assertFalse(Path(api._home, guard.CLIENT_KEY).exists(), "no key made only to show a code")

    def test_the_code_is_the_one_made_from_the_key_every_bundle_carries(self):
        for name, api in self.apps().items():
            with self.subTest(app=name):
                key = guard.client_key(api._home)   # what the first match's bundle does
                public = ed25519.public_key(key).hex()
                self.assertEqual(api.guard_privacy_code(), {"code": guard.privacy_code(public)})
                self.assertRegex(api.guard_privacy_code()["code"], r"^[A-Z2-7]{4}(-[A-Z2-7]{4}){2}$")

    def test_a_damaged_key_file_shows_nothing_and_is_not_replaced(self):
        for name, api in self.apps().items():
            with self.subTest(app=name):
                p = Path(api._home, guard.CLIENT_KEY)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"short")
                self.assertEqual(api.guard_privacy_code(), {"code": ""})
                self.assertEqual(p.read_bytes(), b"short")


class Settings(unittest.TestCase):
    def test_both_apps_say_it_in_all_11_languages(self):
        for app in ("ruse_launcher", "ruse_studio"):
            words = tomllib.loads((ROOT / "src" / app / "words.toml").read_text(encoding="utf-8"))
            for key in ("set_guardcode_title", "tip_guardcode", "set_guardcode_none"):
                with self.subTest(app=app, key=key):
                    self.assertEqual(sorted(words[key]), sorted(LANGS))
                    self.assertTrue(all(words[key][lang].strip() for lang in LANGS))

    def test_both_settings_pages_show_it_read_only_with_the_tooltip(self):
        for app in ("ruse_launcher", "ruse_studio"):
            with self.subTest(app=app):
                html = (ROOT / "src" / app / "ui" / "index.html").read_text(encoding="utf-8")
                js = (ROOT / "src" / app / "ui" / "app.js").read_text(encoding="utf-8")
                self.assertIn('id="set-guardcode"', html)
                self.assertIn('id="guardcode-value"', html)
                self.assertNotIn("<input id=\"guardcode", html, "read-only: no field to type in")
                self.assertIn("guard_privacy_code()", js)
                self.assertIn("w.tip_guardcode", js)
                self.assertIn("w.set_guardcode_none", js)
                self.assertIn('"guardcode-value"', js)
                fake = (ROOT / "src" / app / "ui" / "fake-api.js").read_text(encoding="utf-8")
                self.assertIn("guard_privacy_code", fake)


if __name__ == "__main__":
    unittest.main()
