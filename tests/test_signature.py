"""R.U.S.E. 2.0's title in the copies the apps build (rusemod.signature, rusemod.menulogo; the owner, 2026-10-22: "It's
one of our signatures", and "a toggle somewhere in the settings to go back to generic ruse"): on unless Settings says
the game's own title; made from the player's own game files and put in under every mod's (a mod changing one of the
same files has its own used); the platform's own video change isn't held back the way a mod's is; a copy built with
the other choice is built again; the menu logo's gold leaves the menu's code alone.

Checked our_tools.json: none of its program-reading tools apply; this test never reads the program (its fake game
folder has a two-byte stand-in for the game's program, as tests/test_gamefiles.py's does)."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf
from rusemod import filechecks, gamefiles, menulogo, signature
from rusemod.build import build_and_write, load_mod
from rusemod.edat import Edat
from rusemod.play import built_from
from rusemod.tmst import Tgv, make_tgv, zipo_pack, zipo_unpack

PIXELS = bytes([0, 0, 255, 255, 0, 255, 0, 255, 255, 0, 0, 255, 255, 255, 255, 128])  # blue, green, red, white
BACKGROUND = make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(PIXELS)])
# every pixel's brightest channel is 255, which the video's gold curve keeps at 255: gold (stored blue, green, red)
# with each pixel's alpha
GOLD_BACKGROUND = bytes([102, 204, 255, 255]) * 3 + bytes([102, 204, 255, 128])
OTHER = make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(bytes([0, 255, 0, 255]) * 4)])
NDF = make_ndf(objects=[(0, [])], classes=["TUnit"], props=[])
LOADING = "gen/ww2/res2d/interface/loading/background.tgv"


def write_game(root: Path) -> Path:
    """A game with the loading screen's background in both places the real one has it (no menu movie: its logo
    can't be made here)."""
    game = root / "game"
    rev = game / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "genglad\\patchable\\gfx\\x.gladndfbin", NDF)]))
    loading = ("dir", "ww2\\res2d\\interface\\loading\\", [("file", "background.tgv", BACKGROUND)])
    ppk = make_edat([("dir", "gen\\", [loading])])
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "gen\\", [loading, ("file", "pack\\basesystem3d.ppk", ppk)])]))
    (game / "RUSE.exe").write_bytes(b"MZ")
    return game


def pixels(tgv: bytes) -> bytes:
    return zipo_unpack(Tgv(tgv).payload(0))


def movie(*tags: tuple[int, bytes]) -> bytes:
    """An uncompressed Scaleform movie of these tags (a zero-size stage, 30 frames a second, one frame)."""
    body = b"".join(menulogo.tag_header(code, len(b)) + b for code, b in tags) + menulogo.tag_header(0, 0)
    head = b"\x00" + struct.pack("<HH", 30 << 8, 1)
    out = bytearray(b"GFX\x08" + struct.pack("<I", 0) + head + body)
    struct.pack_into("<I", out, 4, len(out))
    return bytes(out)


def place(char: int) -> bytes:
    """A PlaceObject2 of `char` at depth 1, with an empty matrix."""
    return b"\x06" + struct.pack("<HH", 1, char) + b"\x00"


class Settings(unittest.TestCase):
    def test_on_unless_settings_say_the_games_own(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.assertTrue(signature.title_on(home))
            signature.keep_title(home, False)
            self.assertEqual(json.loads((home / "settings.json").read_text(encoding="utf-8"))[signature.SETTING],
                             "game")
            self.assertFalse(signature.title_on(home))
            signature.keep_title(home, True)
            self.assertNotIn(signature.SETTING, json.loads((home / "settings.json").read_text(encoding="utf-8")))
            self.assertTrue(signature.title_on(home))

    def test_a_copy_built_with_the_other_choice_is_built_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = write_game(Path(tmp))
            self.assertNotEqual(built_from(game, [], title=True)["key"], built_from(game, [], title=False)["key"])
            self.assertEqual(built_from(game, [])["key"], built_from(game, [], title=True)["key"])


class MenuGold(unittest.TestCase):
    def test_the_logos_placements_get_the_gold_and_nothing_else_changes(self):
        base = movie((26, place(659)), (26, place(12)), (1, b""))
        gold, n = menulogo.tint(base)
        self.assertEqual(n, 1)
        tags = menulogo.read_tags(gold, menulogo.tags_start(gold), len(gold))
        self.assertEqual(tags[0][1][0] & 0x08, 0x08)  # a colour change on the logo's placement
        self.assertEqual(tags[0][1][5:6], b"\x00")    # after its own matrix
        self.assertEqual(tags[0][1][6:], menulogo.cxform(menulogo.GOLD))
        self.assertEqual(tags[1][1], place(12))
        filechecks.check_flash(gold, base)  # the menu's code is the game's
        plain = movie((26, place(12)), (1, b""))
        self.assertEqual(menulogo.tint(plain), (plain, 0))

    @unittest.skipIf(menulogo.unary_union is None, "the letters need shapely")
    def test_a_movie_without_its_logo_is_refused(self):
        with self.assertRaisesRegex(menulogo.LogoError, "fitted"):
            menulogo.two_point_oh(movie((26, place(12)), (1, b"")))


class OurOwnChange(unittest.TestCase):
    def test_a_video_isnt_offered_to_mods_but_is_ours(self):
        with self.assertRaisesRegex(gamefiles.GameFileError, "video"):
            gamefiles.taken("ww2/videos/loading/loading.webm")
        self.assertEqual(gamefiles.taken("ww2/videos/loading/loading.webm", ours=True), "video")
        with self.assertRaisesRegex(gamefiles.GameFileError, "Music tab"):
            gamefiles.taken("x.ess", ours=True)  # (a sound still goes through the Music tab)


def have(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


@unittest.skipUnless(have("numpy") and have("PIL"), "the gold pictures are made with numpy and Pillow")
class InTheBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = write_game(self.root)
        self.before = {p: p.read_bytes() for p in self.game.rglob("*.dat")}

    def tearDown(self):
        self.assertEqual({p: p.read_bytes() for p in self.game.rglob("*.dat")}, self.before)  # never written
        self.tmp.cleanup()

    def built(self, mods=(), on=True):
        lines, out = [], self.root / "out"
        result = build_and_write(self.game, [load_mod(m) for m in mods], out=out, say=lines.append,
                                 cache=self.root / "cache", signature=on)
        zz = out / "ZZ_Win.dat"
        return result, lines, (Edat(zz.read_bytes()) if zz.is_file() else None)

    @staticmethod
    def backgrounds(arc: Edat) -> tuple[bytes, bytes]:
        path = LOADING.replace("/", "\\")
        loose = bytes(arc.read(arc.entry(path)))
        ppk = Edat(bytes(arc.read(arc.entry("gen\\pack\\basesystem3d.ppk"))))
        return loose, bytes(ppk.read(ppk.entry(path)))

    def test_the_loading_background_turns_gold_in_both_places(self):
        result, lines, arc = self.built()
        self.assertEqual(result.errors, [], lines)
        for got in self.backgrounds(arc):
            self.assertEqual(pixels(got), GOLD_BACKGROUND)
        self.assertIn(f"game file: ZZ_Win.dat: {LOADING} (changed, from {signature.TITLE})", lines)
        self.assertTrue(any(f.name.startswith("background-") for f in (self.root / "cache" / "signature").iterdir()))
        self.assertFalse([line for line in lines if "fitted" in line], lines)  # no menu here: nothing said about it

    def test_the_games_own_title_when_settings_say_so(self):
        result, lines, arc = self.built(on=False)
        self.assertEqual(result.errors, [], lines)
        self.assertIsNone(arc)
        self.assertIn("The mods change nothing in these packs.", lines)

    def test_a_mod_changing_the_same_file_has_its_own_used(self):
        mod = self.root / "paint"
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "paint"\nversion = "0.1.0"\n', encoding="utf-8")
        f = mod / "files" / "game" / "ZZ_Win.dat" / (LOADING + ".rdelta")
        f.parent.mkdir(parents=True)
        f.write_bytes(gamefiles.make_delta(BACKGROUND, OTHER))
        result, lines, arc = self.built([mod])
        self.assertEqual(result.errors, [], lines)
        loose, inside = self.backgrounds(arc)
        self.assertEqual(loose, OTHER)                       # the mod's
        self.assertEqual(pixels(inside), GOLD_BACKGROUND)    # the other copy, which the mod leaves alone: ours
        self.assertIn(f"{signature.TITLE}: paint changes ZZ_Win.dat: {LOADING}, so paint's is used", lines)
        # the title is looks only (pictures, a video, menu packs: rusemod.lock's cosmetic kinds): players with it on
        # and off have the same fingerprint
        off, lines_off, _arc = self.built([mod], on=False)
        self.assertEqual(off.errors, [], lines_off)
        self.assertIsNotNone(result.fingerprint)
        self.assertEqual(result.fingerprint, off.fingerprint)


def real_game():
    try:
        from rusemod.steam import find_game
        found = find_game()
        return Path(found["game_dir"]) if found else None
    except Exception:  # no Steam, no game: the tests below need the real one
        return None


GAME = real_game()


@unittest.skipUnless(GAME is not None and menulogo.unary_union is not None, "needs R.U.S.E. installed, and shapely")
class OnTheRealGame(unittest.TestCase):
    """The menu logo and the loading picture, made from the game's own files, pass the build's checks (the video
    takes minutes to encode: checked by hand, not here)."""

    def test_menu_and_picture(self):
        from rusemod.build import find_pack
        zz_path = find_pack(GAME, "ZZ_Win.dat")
        with Edat.open(str(zz_path)) as zz:
            opened = lambda path: zz  # noqa: E731  (the only pack read here)
            menu = signature._read(opened, lambda name: zz_path, signature.ZZ, signature.MENU)
            if signature._sha(menu) != signature.FITTED[signature.MENU]:
                self.skipTest("another version of the game's menu")
            new, report = menulogo.two_point_oh(menu)
            self.assertEqual(report["tinted"], 2)
            self.assertEqual(gamefiles.check_kind("interface_outgame.gfx", new, menu), "Flash menu")
            area = menulogo.letters(new)
            self.assertAlmostEqual(area.bounds[2] - area.bounds[0], report["right"], delta=6)
            raw = signature._read(opened, lambda name: zz_path, signature.ZZ, signature.LOADING + "ruse.tgv")
            picture = signature.title_picture(raw, new)
            self.assertEqual(gamefiles.check_kind("ruse.tgv", picture, raw), "texture")
            alpha = pixels(picture)[3::4]
            self.assertGreater(sum(1 for a in alpha if a > 128), len(alpha) // 10)  # letters drawn


if __name__ == "__main__":
    unittest.main()
