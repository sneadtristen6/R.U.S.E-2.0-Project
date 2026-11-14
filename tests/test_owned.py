"""Owned copies only (rusemod.owned): the signatures, the codes, the folder check, unlocking, and the gate both apps
start a modded game through.

Checked our_tools.json: its tools study the game's code; these tests only hash made-up files and read a signature.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import shutil
import tempfile
import unittest
from pathlib import Path

from rusemod import owned
from rusemod.play import BuildError, Starter

ROOT = Path(__file__).resolve().parents[1]
# a real Steam install of the game, where this PC has one (read only): Steam's own file, signed by Valve
REAL = next((p for p in (Path("D:/Steam/steamapps/common/R.U.S.E"),
                         Path("C:/Program Files (x86)/Steam/steamapps/common/R.U.S.E"))
             if (p / owned.STEAM_FILE).is_file()), None)
SECRET = bytes(range(32))  # a made-up key for the tests: the project's own never leaves its PC
PUBLIC = owned.public_key(SECRET)


def fake_game(root: Path, installdir: str = "R.U.S.E", record: bool = True) -> Path:
    """A Steam library holding a made-up game folder: RUSE.exe and, when `record`, Steam's manifest naming it."""
    game = root / "steamapps" / "common" / installdir
    game.mkdir(parents=True)
    (game / "RUSE.exe").write_bytes(b"MZ not really the game")
    if record:
        (root / "steamapps" / "appmanifest_21970.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"21970"\n\t"installdir"\t\t"%s"\n}\n' % installdir, encoding="utf-8")
    return game


class Signatures(unittest.TestCase):
    def test_rfc_8032_vectors(self):
        for secret, public, message, signature in [
            ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
             "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
             "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5"
             "f0595bbe24655141438e7a100b"),
            ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
             "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
             "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2e"
             "aeb4302aeeb00d291612bb0c00")]:
            s, m = bytes.fromhex(secret), bytes.fromhex(message)
            self.assertEqual(owned.public_key(s).hex(), public)
            self.assertEqual(owned.sign(s, m).hex(), signature)
            self.assertTrue(owned.verify(bytes.fromhex(public), m, bytes.fromhex(signature)))
            self.assertFalse(owned.verify(bytes.fromhex(public), m + b"!", bytes.fromhex(signature)))

    def test_the_apps_carry_a_real_key(self):
        self.assertEqual(len(owned.UNLOCK_PUBLIC_KEY), 32)
        self.assertNotEqual(owned.UNLOCK_PUBLIC_KEY, bytes(32))
        self.assertIsNotNone(owned._unpack(owned.UNLOCK_PUBLIC_KEY))  # a point on the curve


class Codes(unittest.TestCase):
    def test_base32_both_ways(self):
        for size in (1, 10, 32, 64):
            data = bytes((i * 37 + 11) % 256 for i in range(size))
            text = owned.b32(data)
            self.assertEqual(owned.unb32(text, size), data)
            self.assertEqual(owned.unb32(owned.grouped(text, 5).lower(), size), data)  # dashes and case don't count
        self.assertIsNone(owned.unb32("U" * 16, 10))  # not one of Crockford's letters
        self.assertIsNone(owned.unb32("A" * 15, 10))  # cut short

    def test_an_unlock_code_fits_its_folder_code_only(self):
        code = owned.b32(bytes(range(10)))
        unlock = owned.unlock_code(SECRET, owned.grouped(code))
        self.assertTrue(owned.unlock_fits(unlock, code, PUBLIC))
        self.assertTrue(owned.unlock_fits(unlock.replace("-", " ").lower(), owned.grouped(code), PUBLIC))
        self.assertFalse(owned.unlock_fits(unlock, owned.b32(bytes(range(1, 11))), PUBLIC))  # another PC's code
        self.assertFalse(owned.unlock_fits(unlock, code))  # made with another key than the apps'
        self.assertFalse(owned.unlock_fits(unlock[:-3], code, PUBLIC))  # cut short
        self.assertFalse(owned.unlock_fits("", code, PUBLIC))

    def test_the_folder_code_is_this_pc_and_this_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = fake_game(Path(tmp))
            first = owned.folder_code(game, "pc-1")
            self.assertEqual(len(first), 16)
            self.assertEqual(owned.folder_code(game, "pc-1"), first)
            self.assertNotEqual(owned.folder_code(game, "pc-2"), first)
            (game / "RUSE.exe").write_bytes(b"MZ another build")
            self.assertNotEqual(owned.folder_code(game, "pc-1"), first)
        self.assertTrue(owned.machine_id())


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_steams_record_of_the_install(self):
        self.assertTrue(owned.steam_record(fake_game(self.tmp / "a")))
        self.assertTrue(owned.steam_record(fake_game(self.tmp / "b", installdir="r.u.s.e")))
        self.assertFalse(owned.steam_record(fake_game(self.tmp / "c", record=False)))
        moved = self.tmp / "d" / "R.U.S.E"  # the game copied somewhere Steam doesn't know
        moved.mkdir(parents=True)
        self.assertFalse(owned.steam_record(moved))
        other = fake_game(self.tmp / "e")
        (self.tmp / "e" / "steamapps" / "appmanifest_21970.acf").write_text(
            '"AppState" { "installdir" "Another Game" }', encoding="utf-8")
        self.assertFalse(owned.steam_record(other))

    def test_a_fake_steams_files_are_named(self):
        game = fake_game(self.tmp)
        self.assertEqual(owned.fake_steam_files(game), [])
        (game / "STEAM_SETTINGS").mkdir()
        (game / "steam_emu.ini").write_text("", encoding="utf-8")
        (game / "steam_appid.txt").write_text("21970", encoding="utf-8")  # Steam's own, and our copies': fine
        self.assertEqual(owned.fake_steam_files(game), ["STEAM_SETTINGS", "steam_emu.ini"])

    def test_an_unsigned_or_odd_file_has_no_signer(self):
        game = fake_game(self.tmp)
        self.assertIsNone(owned.signed_by(game / owned.STEAM_FILE))  # missing
        (game / owned.STEAM_FILE).write_bytes(b"MZ" + bytes(200))
        self.assertIsNone(owned.signed_by(game / owned.STEAM_FILE))
        (game / owned.STEAM_FILE).write_bytes(b"not a program at all")
        self.assertIsNone(owned.signed_by(game / owned.STEAM_FILE))

    def test_a_copy_that_fails_has_a_code_and_unlocks(self):
        game = fake_game(self.tmp)
        (game / "steam_emu.ini").write_text("", encoding="utf-8")
        view = owned.check(game, machine="pc-1", public=PUBLIC)
        self.assertFalse(view["ok"])
        self.assertEqual(view["reasons"], ["steam_file", "fake_steam"])
        self.assertEqual(view["fake"], ["steam_emu.ini"])
        self.assertEqual(view["code"], owned.grouped(owned.folder_code(game, "pc-1")))
        unlock = owned.unlock_code(SECRET, view["code"])
        view = owned.check(game, [unlock], machine="pc-1", public=PUBLIC)
        self.assertTrue(view["ok"] and view["unlocked"])
        self.assertFalse(owned.check(game, [unlock], machine="pc-2", public=PUBLIC)["ok"])  # another PC

    @unittest.skipUnless(REAL, "no Steam install of R.U.S.E. on this PC")
    def test_steams_own_file_is_valves_and_a_changed_one_is_not(self):
        self.assertIn("valve corp.", owned.signed_by(REAL / owned.STEAM_FILE))
        self.assertTrue(owned.check(REAL)["ok"])
        changed = self.tmp / owned.STEAM_FILE
        data = bytearray((REAL / owned.STEAM_FILE).read_bytes())
        data[0x1000] ^= 0xFF  # one byte of its code
        changed.write_bytes(bytes(data))
        self.assertIsNone(owned.signed_by(changed))


class Apps(unittest.TestCase):
    def test_the_starter_refuses_before_building_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            starter = Starter()
            starter.owned = lambda game: "not confirmed"
            with self.assertRaises(BuildError) as caught:
                starter.modded(Path(tmp), [], Path(tmp) / "copies" / "Modded game", "test", lambda line: None)
            self.assertEqual(str(caught.exception), "not confirmed")
            self.assertFalse((Path(tmp) / "copies").exists())  # nothing made

    def test_the_launcher_checks_once_its_window_turns_it_on(self):
        from ruse_launcher.api import LauncherApi
        with tempfile.TemporaryDirectory() as tmp:
            game = fake_game(Path(tmp) / "lib")
            api = LauncherApi(game_dir=game, home=Path(tmp) / "home")
            self.assertTrue(api.owned_check()["ok"])  # off: tests of made-up games build copies as before
            api.use_owned_check()
            view = api.owned_check()
            self.assertFalse(view["ok"])
            self.assertEqual(view["words"]["title"], owned.words("us")["title"])
            self.assertEqual(api._starter.owned(game), owned.words("us")["refused"])
            self.assertTrue(api.owned_unlock("0" * 103)["bad_code"])
            opened = []
            api._update_open_url = opened.append
            api.owned_open("ticket")
            self.assertIn("template=unlock.yml", opened[-1])
            self.assertIn(view["code"], opened[-1])

    def test_both_apps_turn_it_on_and_ship_the_box(self):
        for app in ("ruse_launcher", "ruse_studio"):
            source = (ROOT / "src" / app / "app.py").read_text(encoding="utf-8")
            self.assertIn("api.use_owned_check()", source, app)
            self.assertIn('"owned.js"', source, app)
            self.assertIn('<script src="owned.js"></script>',
                          (ROOT / "src" / app / "ui" / "index.html").read_text(encoding="utf-8"), app)
        self.assertEqual((ROOT / "src/ruse_launcher/ui/owned.js").read_bytes(),
                         (ROOT / "src/ruse_studio/ui/owned.js").read_bytes())  # one box, the same in both
        self.assertTrue((ROOT / ".github/ISSUE_TEMPLATE/unlock.yml").is_file())

    def test_the_box_speaks_the_ten_languages(self):
        import tomllib
        table = tomllib.loads(owned._WORDS.read_text(encoding="utf-8"))
        langs = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa"}
        for key, values in table.items():
            self.assertEqual(set(values), langs, key)
            for lang, text in values.items():
                self.assertEqual("{names}" in text, "{names}" in values["us"], (key, lang))
        self.assertNotEqual(owned.words("fr")["title"], owned.words("us")["title"])


if __name__ == "__main__":
    unittest.main()
