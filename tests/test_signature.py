"""R.U.S.E. 2.0's title in the copies the apps build (rusemod.signature, rusemod.menulogo; the owner, 2026-10-22: "It's
one of our signatures", and "a toggle somewhere in the settings to go back to generic ruse"): on unless Settings says
the game's own title; made from the player's own game files and put in under every mod's (a mod changing one of the
same files has its own used); the platform's own video change isn't held back the way a mod's is; a copy built with
the other choice is built again; the menu logo's gold leaves the menu's code alone.

Checked our_tools.json: none of its program-reading tools apply; this test never reads the program (its fake game
folder has a two-byte stand-in for the game's program, as tests/test_gamefiles.py's does)."""
import io
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

    def test_the_hover_frame_turns_gold_in_place(self):
        # a shape with a black-to-white gradient (the hover frame), inside a sprite placed by the name the menus give
        # it; another white shape not placed so stays white
        bounds = menulogo.rect_bits(0, 4000, 0, 4000).bytes()
        frame_fill = b"\x01\x10\x00\x02" + b"\x00\x00\x00\x00" + b"\xff\xff\xff\xff"  # count, linear, matrix, 2 stops
        white_fill = b"\x01\x00\xff\xff\xff"
        records = b"\x00\x10\x00"  # no lines; 1 fill bit, 0 line bits; the end record
        frame = struct.pack("<H", 5) + bounds + frame_fill + records
        white = struct.pack("<H", 8) + bounds + white_fill + records
        inner = menulogo.tag_header(26, len(place(5))) + place(5) + menulogo.tag_header(1, 0) + menulogo.tag_header(0, 0)
        named = b"\x22" + struct.pack("<HH", 1, 6) + menulogo.SELECTION.encode() + b"\x00"
        outer = menulogo.tag_header(26, len(named)) + named + menulogo.tag_header(1, 0) + menulogo.tag_header(0, 0)
        base = movie((2, frame), (2, white), (39, struct.pack("<HH", 6, 1) + inner), (39, struct.pack("<HH", 7, 1) + outer),
                     (1, b""))
        gold, n = menulogo.gold_selection(base)
        self.assertEqual(n, 1)
        self.assertEqual(len(gold), len(base))
        code, body = menulogo.find_shape(gold, 5)
        self.assertEqual([tuple(body[a:a + 3]) for a in menulogo._gradient_stops(body, code)],
                         [(0, 0, 0), (255, 204, 102)])
        self.assertEqual(menulogo.find_shape(gold, 8)[1], white)  # not a hover frame: untouched
        self.assertEqual(sum(a != b for a, b in zip(gold, base)), 2)  # the white stop's green and blue, nothing else
        plain = movie((2, white), (1, b""))
        self.assertEqual(menulogo.gold_selection(plain), (plain, 0))

    def test_grey_lines_turn_gold_but_not_the_troop_buttons_or_other_colours(self):
        bounds = menulogo.rect_bits(0, 4000, 0, 4000).bytes()
        no_fills, records = b"\x00", b"\x01\x00"   # no fills; 0 fill bits, 1 line bit; the end record

        def lined(sid, *colours):  # a DefineShape with these line colours (1 px)
            lines = bytes([len(colours)]) + b"".join(struct.pack("<H", 20) + bytes(c) for c in colours)
            return struct.pack("<H", sid) + bounds + no_fills + lines + records

        menu_box, troop_box = lined(5, (153, 153, 153), (200, 0, 0)), lined(8, (153, 153, 153))
        troop = b"\x22" + struct.pack("<HH", 1, 8) + b"ie_Tank\x00"
        holder = menulogo.tag_header(26, len(troop)) + troop + menulogo.tag_header(1, 0) + menulogo.tag_header(0, 0)
        base = movie((2, menu_box), (2, troop_box), (39, struct.pack("<HH", 9, 1) + holder), (1, b""))
        gold, n = menulogo.gold_outlines(base)
        self.assertEqual(n, 1)
        self.assertEqual(len(gold), len(base))
        code, body = menulogo.find_shape(gold, 5)
        self.assertEqual([tuple(body[a:a + 3]) for a in menulogo._line_colours(body, code)],
                         [(153, 122, 61), (200, 0, 0)])  # the grey gold (its shade kept), the red as it was
        self.assertEqual(menulogo.find_shape(gold, 8)[1], troop_box)  # a troop button's frame: untouched

    def test_a_panels_frame_line_turns_gold_but_not_a_small_pictures(self):
        if not have("numpy"):
            self.skipTest("the pictures are read with numpy")

        def picture(w, h):  # dark grey with a 1 px 238 grey line along its top (stored blue, green, red, alpha)
            px = bytearray(bytes([40, 40, 40, 255]) * (w * h))
            px[:w * 4] = bytes([238, 238, 238, 255]) * w
            return make_tgv(w, h, "A8R8G8B8_LIN", [zipo_pack(bytes(px))])
        panel = signature.gold_frames(picture(320, 20))
        top = pixels(panel)[:320 * 4]
        self.assertEqual(bytes(top[:4]), bytes([95, 190, 238, 255]))  # 238 times GOLD (stored blue, green, red)
        self.assertEqual(bytes(pixels(panel)[320 * 4:320 * 4 + 4]), bytes([40, 40, 40, 255]))  # inside: as it was
        self.assertEqual(signature.gold_frames(picture(120, 20)), b"")  # a button-sized picture: left alone

    def test_the_small_logo_is_made_for_its_wider_picture_and_keeps_each_screens_alignment(self):
        image = struct.pack("<HHHH", 386, 0, 258, 53) + b"\x00" + bytes([8]) + b"logo.tga"  # Scaleform's outside picture
        w = menulogo.BitWriter()
        w.ub(1, 4), w.ub(0, 4)                        # 1 fill bit, 0 line bits
        w.ub(0, 1), w.ub(0b00101, 5), w.ub(1, 5), w.sb(0, 1), w.sb(0, 1), w.ub(1, 1)   # move to 0, 0; fill 1 right
        for dx, dy in ((5160, 0), (0, 1060), (-5160, 0), (0, -1060)):
            menulogo._edge(w, dx, dy)
        w.ub(0, 6)
        fill = b"\x01\x41" + struct.pack("<H", 386) + b"\x00"   # one bitmap fill, an empty matrix; no lines next
        shape = struct.pack("<H", 387) + menulogo.rect_bits(0, 5160, 0, 1060).bytes() + fill + b"\x00" + w.bytes()

        def holder(spid, char, x_px):  # a sprite placing `char` at x
            p = menulogo.moved_place(place(char), round(x_px * 20))
            return 39, struct.pack("<HH", spid, 1) + menulogo.tag_header(26, len(p)) + p + menulogo.tag_header(1, 0) \
                + menulogo.tag_header(0, 0)
        base = movie((1001, image), (2, shape), holder(388, 387, 0), holder(10, 388, 511), holder(11, 388, 16.5),
                     (1, b""))
        for scale, centred_x in ((1.0, 511 - 74), (258 / 406, 511)):
            made, report = menulogo.small_logo(base, 406, scale)
            self.assertEqual((report["centred"], report["left"]), ([10], [11]))
            tags = {(c, struct.unpack_from("<H", b, 0)[0]): b for c, b, _l in
                    menulogo.read_tags(made, menulogo.tags_start(made), len(made)) if c in (1001, 2, 39)}
            self.assertEqual(struct.unpack_from("<HH", tags[1001, 386], 4), (406, 53))     # the picture's size
            self.assertEqual(menulogo.read_shape(tags[2, 387], 2)["bounds"], [0, 8120, 0, 1060])   # widened
            inner = lambda spid: menulogo.read_tags(tags[39, spid], 4, len(tags[39, spid]))[0][1]  # noqa: E731
            self.assertAlmostEqual(menulogo._place_x(inner(388))[0], scale, places=4)       # drawn at the scale
            self.assertAlmostEqual(menulogo._place_x(inner(10))[1], centred_x, places=1)    # centred screen: centred
            self.assertAlmostEqual(menulogo._place_x(inner(11))[1], 16.5, places=1)         # the other: left edge kept
        with self.assertRaisesRegex(menulogo.LogoError, "small logo"):
            menulogo.small_logo(movie((26, place(12)), (1, b"")), 406)

    def test_the_loading_popup_gets_our_picture_and_hides_its_globe_and_text(self):
        def holder(spid, *places):
            inner = b"".join(menulogo.tag_header(26, len(p)) + p for p in places)
            return 39, struct.pack("<HH", spid, 1) + inner + menulogo.tag_header(1, 0) + menulogo.tag_header(0, 0)
        backdrop = b"\x26" + struct.pack("<HH", 1, menulogo.BACKDROP) + b"\x00" + b"ie_FondNoir\x00"
        globe = b"\x06" + struct.pack("<HH", 5, menulogo.GLOBE) + b"\x00"
        text = b"\x06" + struct.pack("<HH", 3, menulogo.LOADING_TEXT) + b"\x00"
        base = movie(holder(menulogo.WAIT, backdrop, text, globe), holder(77, backdrop), (1, b""))
        made, report = menulogo.our_loading_popup(base)
        self.assertEqual(report, {"hidden": 2, "backdrop": 1})
        tags = menulogo.read_tags(made, menulogo.tags_start(made), len(made))
        self.assertEqual([(c, struct.unpack_from("<H", b, 0)[0]) for c, b, _l in tags[:4]],
                         [(1001, menulogo.BACKDROP_IMAGE), (2, menulogo.BACKDROP_IMAGE + 1),
                          (39, menulogo.BACKDROP_IMAGE + 2), (39, menulogo.WAIT)])     # defined before it's used
        self.assertIn(menulogo.backdrop_file().encode(), tags[0][1])
        placed = [b for c, b, _l in menulogo.read_tags(tags[3][1], 4, len(tags[3][1])) if c == 26]
        self.assertEqual(menulogo._placed(26, placed[0]), (menulogo.BACKDROP_IMAGE + 2, "ie_FondNoir"))  # same name
        for p in placed[1:]:   # the text and the globe: see-through
            self.assertTrue(p[0] & 0x08)
            self.assertTrue(p.endswith(menulogo.cxform((1, 1, 1), 0.0)))
        self.assertEqual(tags[4][1], holder(77, backdrop)[1])   # another popup with the same dark backdrop: as it was
        code, body = menulogo.find_shape(made, menulogo.BACKDROP_IMAGE + 1)
        self.assertEqual(menulogo.read_shape(body, code)["bounds"], [0, 1280 * 20, 0, 720 * 20])
        with self.assertRaisesRegex(menulogo.LogoError, "loading popup"):
            menulogo.our_loading_popup(movie((26, place(12)), (1, b"")))

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


@unittest.skipUnless(have("av") and have("numpy"), "the intro is made with PyAV")
class TheIntroSound(unittest.TestCase):
    def test_the_engine_start_ships_as_the_game_plays_it(self):
        import av
        import numpy as np
        from importlib import resources
        raw = (resources.files("rusemod") / "sounds" / signature.INTRO_SOUND).read_bytes()
        with av.open(io.BytesIO(raw)) as f:
            a = f.streams.audio[0]
            self.assertEqual((a.codec_context.name, a.rate, a.channels), ("vorbis", 48000, 2))  # as the game's own
            pcm = np.concatenate([fr.to_ndarray() for fr in f.decode(a)], axis=1)
        self.assertAlmostEqual(pcm.shape[1] / 48000, 7.5, places=2)  # the intro's length
        self.assertLess(np.abs(pcm).max(), 0.95)                       # its peaks held under full scale
        self.assertAlmostEqual(20 * np.log10(np.sqrt((pcm ** 2).mean())), -20.0, delta=1.0)  # the game's level


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
            self.assertEqual(report["selection frames"], 2)  # the tiles' frame and the buttons' and lists' frame
            for sid in (403, 43):
                code, body = menulogo.find_shape(new, sid)
                stops = [tuple(body[a:a + 3]) for a in menulogo._gradient_stops(body, code)]
                self.assertIn((255, 204, 102), stops)  # white is gold
                self.assertNotIn((255, 255, 255), stops)
            self.assertEqual(report["outline shapes"], 61)
            for sid, want in ((412, (153, 122, 61)), (1100, (255, 204, 102)), (342, (153, 153, 153))):
                code, body = menulogo.find_shape(new, sid)  # a label box, a highlighted button, a troop button
                self.assertEqual(tuple(body[menulogo._line_colours(body, code)[0]:][:3]), want)
            self.assertEqual(gamefiles.check_kind("interface_outgame.gfx", new, menu), "Flash menu")
            area = menulogo.letters(new)
            self.assertAlmostEqual(area.bounds[2] - area.bounds[0], report["right"], delta=6)
            raw = signature._read(opened, lambda name: zz_path, signature.ZZ, signature.LOADING + "ruse.tgv")
            picture = signature.title_picture(raw, new)
            self.assertEqual(gamefiles.check_kind("ruse.tgv", picture, raw), "texture")
            alpha = pixels(picture)[3::4]
            self.assertGreater(sum(1 for a in alpha if a > 128), len(alpha) // 10)  # letters drawn
            # the sub-menus' small logo: R.U.S.E. 2.0, its R.U.S.E. pixels the game's, as wide on screen as before
            small = signature._in_pack(signature._read(opened, lambda name: zz_path, signature.ZZ, signature.OUTGAME),
                                       signature.SMALL)
            made = signature._new_menu(menu, small)
            wide = signature.small_logo_picture(small, made)
            self.assertEqual(gamefiles.check_kind("i182.tgv", wide, small), "texture")
            self.assertEqual((Tgv(wide).width, Tgv(wide).height), (406, 53))
            old, new = pixels(small), pixels(wide)
            self.assertEqual(b"".join(new[y * 406 * 4:(y * 406 + 258) * 4] for y in range(53)), old)
            self.assertTrue(signature._small_made(made))
            self.assertEqual(gamefiles.check_kind("interface_outgame.gfx", made, menu), "Flash menu")
            # the loading popup before the main menu: our picture behind it, its globe and text hidden
            self.assertIsNone(signature._in_pack(signature._read(opened, lambda name: zz_path, signature.ZZ,
                                                                 signature.OUTGAME), signature.BACKDROP))  # (new)
            self.assertTrue(signature.BACKDROP.endswith(menulogo.backdrop_file().lower()[:-4] + ".tgv"))
            popup, report = menulogo.our_loading_popup(menulogo.two_point_oh(menu)[0])
            self.assertEqual(report, {"hidden": 2, "backdrop": 1})
            self.assertEqual(gamefiles.check_kind("interface_outgame.gfx", popup, menu), "Flash menu")
            self.assertEqual(signature._new_menu(menu, small, True), menulogo.our_loading_popup(made)[0])


    def test_the_loading_screens_text_turns_gold_and_the_fingerprint_doesnt_change(self):
        from rusemod import lock
        from rusemod.build import find_pack
        from rusemod.ndf import Ndf
        where = find_pack(GAME, signature.GLAD)
        with Edat.open(str(where)) as arc:
            raw = signature._read(lambda path: arc, lambda name: where, signature.GLAD, signature.LOADING_SCREEN)
        if signature._sha(raw) != signature.FITTED[signature.LOADING_SCREEN]:
            self.skipTest("another version of the game's loading screen")
        gold = signature.gold_loading_screen(raw)
        self.assertEqual(gamefiles.check_kind("x.gladndfbin", gold, raw), "game data")
        before, after = Ndf(raw), Ndf(gold)
        changed = []
        for i, (a, b) in enumerate(zip(before.objects, after.objects)):
            for (pa, va), (pb, vb) in zip(a.props, b.props):
                if va.payload != vb.payload:
                    changed.append((i, before.prop_name(pa), tuple(va.payload), tuple(vb.payload)))
        self.assertEqual(sorted(changed), [   # the tip's style (white) and the "LOADING" one (grey 200), nothing else;
            (564, "ColorBottom", (255, 255, 255, 255), (102, 204, 255, 255)),   # stored blue, green, red, alpha
            (564, "ColorUp", (255, 255, 255, 255), (102, 204, 255, 255)),
            (568, "ColorBottom", (200, 200, 200, 255), (80, 160, 200, 255)),
            (568, "ColorUp", (200, 200, 200, 255), (80, 160, 200, 255))])
        path = f"{signature.GLAD}/{signature.LOADING_SCREEN}"
        self.assertTrue(lock.is_gameplay(path))                                  # (a game data file counts)
        self.assertEqual(lock.canonical(path, gold), lock.canonical(path, raw))  # but not its text colours
        self.assertNotEqual(lock.canonical("other.gladndfbin", gold), lock.canonical("other.gladndfbin", raw))
        self.assertTrue(lock.looks_only_change(path, gold, lambda: raw))         # left off the fingerprint's list
        self.assertFalse(lock.looks_only_change("other.gladndfbin", gold, lambda: raw))
        other = Ndf(gold)
        size = next(v for pi, v in other.objects[564].props if other.prop_name(pi) == "FontSize")
        size.payload = b"\x00\x00\x40\x42"                                       # the tip's size: not looks only
        self.assertFalse(lock.looks_only_change(path, other.to_member(), lambda: raw))


if __name__ == "__main__":
    unittest.main()
