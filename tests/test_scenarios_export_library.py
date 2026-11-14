"""Export scenarios, the Launcher's side: what happens to an exported .rusemod in the Launcher's library, the usual
and the unusual (the owner, overnight 2026-11-14: "Usual and unusual situations. Player can find themselves in when
making new mods in our apps"): added, updated to a new version, the same file added twice, a damaged or a cut file,
one a newer Studio made, two players' mods of one id, and the copy's join code before and after a change.

On test_launcher's made-up game (its Base: a game folder, a platform folder, nothing starts for real), with the Studio
on the same platform folder (they share the library, as on a player's PC) and no game for the Studio (Export packs
without a build). A finding (FE-n, D:/RUSE-2.0/scratch/release-0920/scenarios/export/FINDINGS.md) is kept as
@unittest.expectedFailure, its docstring naming it: it starts to pass once mended."""
import sys
import time
import unittest
import zipfile
from pathlib import Path

from test_launcher import Base as LauncherBase, wait_for
from rusemod import fairplay, package
from ruse_launcher.api import LauncherError
from ruse_studio.api import StudioApi

PATCH = "patch $/B ( ProductionPrice *= 0.5 )\n"   # (a change the made-up game's pack has: test_build's $/B)


class Library(LauncherBase):
    def setUp(self):
        super().setUp()
        self.studio = self.studio_on(self.home)

    @staticmethod
    def studio_on(home: Path) -> StudioApi:
        api = StudioApi(home=home, instances=home / "studio-copies")
        api._game = lambda: None                       # (the Studio finds no game: Export packs without a build)
        return api

    def made(self, name: str, studio=None, patch: str = PATCH) -> Path:
        studio = studio or self.studio
        folder = Path(studio.new_mod(name)["current"])
        (folder / "src" / "units.rndf").write_text(patch, encoding="utf-8")
        return folder

    def exported(self, version: str, author: str = "", studio=None) -> Path:
        studio = studio or self.studio
        job = studio.export_mod(version, author, "")["job"]
        end = time.monotonic() + 60
        while studio.job(job)["state"] == "running" and time.monotonic() < end:
            time.sleep(0.02)
        view = studio.job(job)
        self.assertEqual(view["state"], "done", view.get("message"))
        return Path(view["result"]["path"])

    def shown(self, launcher) -> dict:
        return {m["id"]: (m["name"], m["version"], m["author"]) for m in launcher.library()}


class Usual(Library):
    def test_an_exported_file_added_on_another_pc(self):
        """Exported here, added to a friend's Launcher: there it is, as the modder named it."""
        self.made("Tank Test")
        out = self.exported("1.0.0", "Jane Doe")
        friend = self.api(home=Path(self.tmp.name) / "friend")
        got = friend.add_mod(str(out))
        self.assertEqual((got["mod"]["id"], got["replaced"]), ("tank-test", False))
        self.assertEqual(self.shown(friend), {"tank-test": ("Tank Test", "1.0.0", "Jane Doe")})

    def test_a_new_version_replaces_the_old_and_the_same_file_twice_is_one(self):
        self.made("Tank Test")
        first = self.exported("1.0.0", "Jane Doe")
        friend = self.api(home=Path(self.tmp.name) / "friend")
        friend.add_mod(str(first))
        self.assertTrue(friend.add_mod(str(first))["replaced"])          # (the same file again: still one)
        second = self.exported("1.1.0")
        self.assertTrue(friend.add_mod(str(second))["replaced"])
        self.assertEqual(self.shown(friend), {"tank-test": ("Tank Test", "1.1.0", "Jane Doe")})

    def test_a_mod_a_newer_studio_exported_in_this_format(self):
        """A newer Studio's version in [made_with], the mod format the same: added, no word about it."""
        folder = self.made("Tank Test")
        package.update_manifest(folder, made_with={"tool": "RUSE Studio", "version": "9.9.9"})
        friend = self.api(home=Path(self.tmp.name) / "friend")
        got = friend.add_mod(str(self.exported("1.0.0")))
        self.assertEqual((got["mod"]["id"], got["problems"]), ("tank-test", []))

    def test_its_join_code_before_and_after_a_change(self):
        """The copy's join code with the exported mod: a new version gives another code, and comparing the two says
        which version each has; the mod changed and exported again under the same version gives another code too,
        and comparing says a mod was changed without a new version."""
        folder = self.made("Tank Test")
        launcher = self.api()
        self.exported("1.0.0")
        self.mod_set("mine", ["tank-test"])

        def code():
            view = wait_for(launcher, launcher.play("mine")["job"], timeout=60)
            self.assertEqual(view["state"], "done", view)
            got = launcher.fair_play()
            self.assertTrue(got["code"], got)
            return got["code"]
        first = code()
        (folder / "src" / "units.rndf").write_text(PATCH.replace("0.5", "0.25"), encoding="utf-8")
        self.exported("1.0.0")
        same_version = code()
        self.assertNotEqual(first, same_version)
        self.assertEqual(fairplay.compare(first, same_version)["differences"],
                         ["Same mods and versions, but the games still differ (a mod was changed without a new "
                          "version, or the mods load in another order). Use the same mod files in the same order."])
        self.exported("1.1.0")
        newer = code()
        self.assertEqual(fairplay.compare(first, newer)["differences"], ["tank-test: you have 1.0.0, they have 1.1.0."])


class Unusual(Library):
    @unittest.expectedFailure
    def test_FE2_two_players_mods_named_without_latin_letters(self):
        """FE-2: a mod named in Russian, Japanese, Chinese or Persian (no letter a to z) gets the id my-mod (my-mod-2,
        -3... only in the same Studio). Alice's "Танки" and Bob's "Самолёты" are both my-mod, so Carol adding Bob's
        replaces Alice's ("replaced": True), and her library has one of the two."""
        alice = self.studio_on(Path(self.tmp.name) / "alice")
        bob = self.studio_on(Path(self.tmp.name) / "bob")
        self.made("Танки", alice)
        self.made("Самолёты", bob)
        carol = self.api()
        carol.add_mod(str(self.exported("1.0.0", "Alice", alice)))
        carol.add_mod(str(self.exported("1.0.0", "Bob", bob)))
        self.assertEqual(sorted(name for name, _v, _a in self.shown(carol).values()), ["Самолёты", "Танки"])

    @unittest.expectedFailure
    def test_FE9_a_damaged_file(self):
        """FE-9: a .rusemod with a damaged byte (a download gone wrong) stops the Launcher's Add with zlib's own error,
        "zlib.error: Error -3 while decompressing data: invalid code lengths set" (not a LauncherError: no words of
        ours); a damaged byte in another of its files the same way, with zipfile's "Bad CRC-32 for file
        'src/units.rndf'"."""
        self.made("Tank Test")
        out = self.exported("1.0.0")
        for member in ("mod.toml", "src/units.rndf"):
            with self.subTest(member=member):
                raw = bytearray(out.read_bytes())
                with zipfile.ZipFile(out) as z:
                    info = z.getinfo(member)
                    start = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
                raw[start + 3] ^= 0xFF
                damaged = Path(self.tmp.name) / member.replace("/", "-") / "tank-test-1.0.0.rusemod"
                damaged.parent.mkdir()
                damaged.write_bytes(bytes(raw))
                with self.assertRaises(LauncherError):
                    self.api(home=damaged.parent / "friend").add_mod(str(damaged))

    @unittest.expectedFailure
    def test_FE10_a_cut_file(self):
        """FE-10: a .rusemod cut short (a download stopped half way) is called "... isn't a mod: add a mod file
        (.rusemod, .rmod or .zip)": it is a .rusemod, only an unfinished one."""
        self.made("Tank Test")
        out = self.exported("1.0.0")
        cut = Path(self.tmp.name) / "tank-test-1.0.0.rusemod"
        cut.write_bytes(out.read_bytes()[: out.stat().st_size // 2])
        with self.assertRaises(LauncherError) as caught:
            self.api(home=Path(self.tmp.name) / "friend").add_mod(str(cut))
        self.assertNotIn("isn't a mod", str(caught.exception))

    @unittest.expectedFailure
    def test_FE11_a_mod_a_newer_studio_saved_in_a_newer_format(self):
        """FE-11: a mod in a newer mod format ([made_with] format above rusemod.modformat.FORMAT) is added and played
        with no word: the Studio refuses to open such a mod ("saved by a newer RUSE Studio"), but the Launcher builds
        it with code that doesn't know its format, the very thing modformat warns of."""
        self.made("Tank Test")
        out = self.exported("1.0.0")
        newer = Path(self.tmp.name) / "newer"
        package.unpack(out, newer)
        package.update_manifest(newer, made_with={"format": 9})
        try:
            got = self.api(home=Path(self.tmp.name) / "friend").add_mod(str(newer))
        except LauncherError as exc:
            self.assertIn("newer", str(exc))
            return
        self.assertTrue(any("newer" in str(p) for p in got["problems"]), got["problems"])

    @unittest.skipUnless(sys.platform == "win32", "Windows keeps a folder with an open file in it in its place")
    @unittest.expectedFailure
    def test_FE14_a_new_version_while_a_file_of_the_old_one_is_open(self):
        """FE-14: a new version added while a file of the old one is open in another program (Windows won't move the
        old folder then) stops the Launcher's Add with Windows' own words, "[WinError 5] Access is denied" (not a
        LauncherError)."""
        self.made("Tank Test")
        first = self.exported("1.0.0")
        friend = self.api(home=Path(self.tmp.name) / "friend")
        friend.add_mod(str(first))
        second = self.exported("1.1.0")
        held = Path(self.tmp.name) / "friend" / "library" / "tank-test" / "mod.toml"
        with open(held, "rb"):
            with self.assertRaises(LauncherError) as caught:
                friend.add_mod(str(second))
        self.assertIn("mod.toml", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
