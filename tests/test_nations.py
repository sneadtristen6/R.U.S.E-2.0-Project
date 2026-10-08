"""The Nations tab (rusemod.nations, ruse_studio.nations; the owner, 2026-10-08: "build the replace-a-nation feature for
this patch"): a nation's lobby and army texts, its flag picture found from the game's flag list, the flag badge (a plain
A8R8G8B8 picture) written as a mod's picture with the badge's own shape kept, and the Studio's calls, on made-up data
(no game files)."""
import base64
import sqlite3
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from rusemod import nations, unitlook
from rusemod.tmst import Tgv, make_tgv, zipo_pack, zipo_unpack

FLAGS = "gen/ww2/res2d/interface/flags/".replace("/", "\\")
ITA = FLAGS + "flag_ita.tgv"


def png(rows):
    """A small RGBA PNG from rows of (r, g, b, a)."""
    h, w = len(rows), len(rows[0])
    raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in rows)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def badge(size=4):
    """A made-up flag badge as the game stores them: one A8R8G8B8 level, ZIPO, blue green red alpha; a round shape in
    its alpha (the corners clear), green all over."""
    px = bytearray()
    for y in range(size):
        for x in range(size):
            corner = (x in (0, size - 1)) and (y in (0, size - 1))
            px += bytes((40, 160, 30, 0 if corner else 255))  # blue 40, green 160, red 30
    return make_tgv(size, size, "A8R8G8B8_LIN", [zipo_pack(bytes(px))], flag=1)


class FakeIndex:
    """The game index's object, ref and value tables, holding one flag list (MultiplayerDataBag.NationalityIcons)."""

    def __init__(self, files):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""CREATE TABLE object (id INTEGER, address TEXT, class TEXT);
                                 CREATE TABLE ref (src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
                                 CREATE TABLE value (object INTEGER, path TEXT, num REAL, text TEXT);""")
        holder, prop = nations.FLAG_LIST
        self.db.execute("INSERT INTO object VALUES (1, ?, 'TLoadingScreenMultiplayerDataBag')", (holder,))
        for n, name in enumerate(files):
            self.db.execute("INSERT INTO object VALUES (?, ?, 'TUIResourceTexture')", (10 + n, f"{holder}:{prop}[{n}]"))
            self.db.execute("INSERT INTO ref VALUES (1, ?, 'object', ?, NULL)", (f"{prop}[{n}]", 10 + n))
            self.db.execute("INSERT INTO value VALUES (?, 'FileName', NULL, ?)", (10 + n, name))

    def close(self):
        pass


GAME_FLAGS = ["DataDir:/WW2/Res2D/Interface/Flags/Flag_{}.png".format(c).replace("/", "\\")
              for c in ("US", "GER", "UK", "FR", "ITA", "USSR", "JAP")]


class Keys(unittest.TestCase):
    def test_lobby_and_army_texts(self):
        self.assertEqual([nations.lobby_key(n) for n in range(7)],
                         ["NATION_0", "NATION_1", "NATION_2", "NATION_3", "NATION_4", "NATION_5", "NATION_7"])
        self.assertEqual(nations.army_key(4), "NAT_NAME_4")
        self.assertIsNone(nations.army_key(6))  # Japan has no army name in the game's texts

    def test_only_the_seven(self):
        for bad in (-1, 7, "x", None):
            with self.subTest(bad=bad), self.assertRaises(nations.NationError):
                nations.check(bad)

    def test_flag_found_from_the_flag_list(self):
        ix = FakeIndex(GAME_FLAGS)
        self.assertEqual(nations.flag_file(ix, 4), GAME_FLAGS[4])
        self.assertEqual(nations.flag_member(ix, 4), ITA)
        self.assertIsNone(nations.flag_member(FakeIndex([]), 4))


class PlainPicture(unittest.TestCase):
    """A flag badge (A8R8G8B8, one level, ZIPO) read and written by rusemod.unitlook."""

    def test_read_as_rgba(self):
        w, h, px = unitlook.picture_rgba(badge())
        self.assertEqual((w, h), (4, 4))
        self.assertEqual(px[4:8], bytes((30, 160, 40, 255)))  # red green blue alpha
        self.assertEqual(px[3], 0)  # a corner: clear

    def test_colour_replaced_shape_kept(self):
        old = badge()
        self.assertTrue(unitlook.is_picture(old) and unitlook.is_plain(old))
        red = bytes((220, 20, 10, 255)) * 16
        new, report = unitlook.make_picture(old, red, 4, 4)
        self.assertEqual((report["blocks"], report["encoded"], report["unit"]), (16, 16, "pixels"))
        g = Tgv(new)
        self.assertEqual((g.width, g.height, g.format, len(g.mips), g.codec, g.flag), (4, 4, "A8R8G8B8_LIN", 1, "ZIPO", 1))
        px = zipo_unpack(g.payload(0))
        self.assertEqual(px[4:8], bytes((10, 20, 220, 255)))  # blue green red, the game's alpha
        self.assertEqual(px[3], 0)  # the corner stays clear: the badge's round shape is the game's
        same, report = unitlook.make_picture(new, red, 4, 4)
        self.assertIs(same, new)
        self.assertEqual(report["encoded"], 0)
        with self.assertRaises(unitlook.LookError):
            unitlook.make_picture(old, bytes(8 * 8 * 4), 8, 8)

    def test_alpha_picture_gives_the_shape(self):
        grey = bytes((128, 128, 128, 255)) * 16
        new, _report = unitlook.make_picture(badge(), bytes((220, 20, 10, 255)) * 16, 4, 4, alpha=grey)
        self.assertEqual(set(zipo_unpack(Tgv(new).payload(0))[3::4]), {128})

    def test_mod_picture_into_the_game_and_its_copy_in_a_pack(self):
        """files/replace/<the flag's path>.png: the loose flag in ZZ_Win.dat and its copy inside a pack of the pack
        (gen\\pack\\vfxbank_gfxeverything.ppk, as the game has Italy's) both changed."""
        from fixtures import make_edat
        from rusemod.edat import Edat
        old = badge()
        zz = Edat(make_edat([("dir", FLAGS, [("file", "flag_ita.tgv", old)]),
                             ("dir", "gen/pack/".replace("/", "\\"), [("file", "vfxbank_gfxeverything.ppk",
                                                                       make_edat([("dir", FLAGS, [("file", "flag_ita.tgv", old)])]))])]))
        with tempfile.TemporaryDirectory() as d:
            pic = Path(d, "flag_ita.tgv.png")
            pic.write_bytes(png([[(220, 20, 10, 255)] * 4] * 4))
            said = []
            out = unitlook.changes(zz, {ITA: (pic, None)}, say=said.append)
        self.assertEqual(sorted(p.rsplit("\\", 1)[-1] for p in out), ["flag_ita.tgv", "vfxbank_gfxeverything.ppk"])
        loose = out[next(p for p in out if p.endswith("flag_ita.tgv"))]
        inner = Edat(out[next(p for p in out if p.endswith(".ppk"))])
        self.assertEqual(bytes(inner.read(inner.entry(ITA))), loose)
        self.assertEqual(zipo_unpack(Tgv(loose).payload(0))[4:8], bytes((10, 20, 220, 255)))
        self.assertTrue(any("16 of 16 pixels" in s for s in said), said)


class StudioNations(unittest.TestCase):
    """StudioApi's Nations calls, with the game index and its texts stood in for."""

    def setUp(self):
        from fixtures import make_edat
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(make_edat([("dir", FLAGS, [("file", "flag_ita.tgv", badge())])]))
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda *a: self.mod
        self.api._open = lambda: FakeIndex(GAME_FLAGS)
        self.api._all_units = lambda ix: [{"nation": 4}] * 3 + [{"nation": 0}]
        game = {"NATION_4": "Italy", "NAT_NAME_4": "Italian Co-Belligerent Army", "NATION_7": "Japan"}
        self.mine = {}
        self.api.value_words = lambda key, kind="mod": {"key": key, "table": "flash_txt", "words": [
            {"lang": "us", "game": game.get(key), "mine": self.mine.get(key)}]}
        self.set_calls = []

        def value_words_set(key, texts, kind="mod"):
            self.set_calls.append((key, texts))
            changed = texts.get("us") != game.get(key)
            if changed:
                self.mine[key] = texts["us"]
            else:
                self.mine.pop(key, None)
            return self.api.value_words(key)
        self.api.value_words_set = value_words_set

    def tearDown(self):
        self.dir.cleanup()

    def italy(self, view):
        return view["nations"][4]

    def test_the_view(self):
        view = self.api.nations_view()
        self.assertTrue(view["mod"])
        self.assertEqual([x["code"] for x in view["nations"]], list(nations.NATIONS))
        it = self.italy(view)
        self.assertEqual((it["name_key"], it["army_key"], it["units"]), ("NATION_4", "NAT_NAME_4", 3))
        self.assertEqual(it["name"][0]["game"], "Italy")
        self.assertEqual((it["flag"]["texture"], it["flag"]["width"], it["flag"]["own"]), (ITA, 4, False))
        self.assertTrue((self.api.cache_dir / it["flag"]["url"][len("cache/"):]).is_file())  # the game's, as a PNG
        self.assertIsNone(view["nations"][6]["army"])  # Japan
        self.assertIsNone(view["nations"][0]["flag"])  # (this made-up game has only Italy's flag picture)

    def test_name_flag_and_back(self):
        view = self.api.nation_words_set(4, "name", {"us": "China"})
        self.assertEqual(self.set_calls[-1], ("NATION_4", {"us": "China"}))
        self.assertEqual(self.italy(view)["name"][0]["mine"], "China")
        flag = png([[(220, 20, 10, 255)] * 4] * 4)
        view = self.api.nation_flag_set(4, "data:image/png;base64," + base64.b64encode(flag).decode())
        saved = self.mod / "files" / "replace" / "gen" / "ww2" / "res2d" / "interface" / "flags" / "flag_ita.tgv.png"
        self.assertEqual(saved.read_bytes(), flag)
        self.assertTrue(self.italy(view)["flag"]["own"])
        with self.assertRaises(nations.NationError):  # not the flag's size
            self.api.nation_flag_set(4, base64.b64encode(png([[(1, 2, 3, 255)] * 8] * 8)).decode())
        with self.assertRaises(nations.NationError):
            self.api.nation_flag_set(4, "not a picture")
        view = self.api.nation_reset(4)
        self.assertFalse(saved.exists())
        self.assertFalse(self.italy(view)["flag"]["own"])
        self.assertNotIn("NATION_4", self.mine)  # the game's words again: the row taken out

    def test_refused(self):
        with self.assertRaises(nations.NationError):  # Japan has no army name
            self.api.nation_words_set(6, "army", {"us": "x"})
        with self.assertRaises(nations.NationError):
            self.api.nation_words_set(9, "name", {"us": "x"})
        self.api._mod_dir = lambda *a: None
        with self.assertRaises(nations.NationError):
            self.api.nation_words_set(4, "name", {"us": "China"})
        with self.assertRaises(nations.NationError):
            self.api.nation_flag_set(4, base64.b64encode(png([[(1, 2, 3, 255)] * 4] * 4)).decode())


if __name__ == "__main__":
    unittest.main()
