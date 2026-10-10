"""The Nations tab (rusemod.nations, ruse_studio.nations; the owner, 2026-10-08: "build the replace-a-nation feature for
this patch"): a nation's lobby and army texts, its flag picture found from the game's flag list, the flag badge (a plain
A8R8G8B8 picture) written as a mod's picture with the badge's own shape kept, and the Studio's calls, on made-up data
(no game files)."""
import base64
import sqlite3
import struct
import tempfile
import time
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


class ShownIndex:
    """The game index as nation_units reads it: each unit's ShowInMenu, one per battle date, all shown."""

    def show(self, address):
        return {"values": [(f"ShowInMenu[{i}]", 1, None) for i in range(5)]}

    def links(self, prop):
        # a US tank researched from Italy's: another nation's chain, never one the Italian hide touches
        return {"$/GFX/Everything/Descriptor_Unit_US_Tank2": "$/GFX/Everything/Descriptor_Unit_US_Tank"}

    def close(self):
        pass


class NationUnits(unittest.TestCase):
    """A nation's units all at once (the owner, 2026-10-10: Italy's units out, China's in): its own units hidden from
    its build menus in one go and shown again, and its menus filled from an era's units of another nation."""

    UNITS = [{"address": "$/GFX/Everything/Descriptor_Unit_Italy_Tank", "class": "TUniteAuSolDescriptor", "nation": 4, "factory": 10},
             {"address": "$/GFX/Everything/Descriptor_Avion_Italy_Plane", "class": "TAvionDescriptor", "nation": 4, "factory": 9},
             {"address": "$/GFX/Everything/Descriptor_Building_Italy_HQ", "class": "TBatimentDescriptor", "nation": 4, "factory": 3},
             {"address": "$/GFX/Everything/Descriptor_Unit_Italy_Off", "class": "TUniteAuSolDescriptor", "nation": 4, "factory": None},
             {"address": "$/GFX/Everything/Descriptor_Unit_US_Tank", "class": "TUniteAuSolDescriptor", "nation": 0, "factory": 10}]
    ERA = [{"key": "Modern|China|ZTZ-99", "era": "Modern", "nation": "China", "name": "ZTZ-99", "card": "Main Battle Tank", "factory": 10},
           {"key": "Modern|China|J-10", "era": "Modern", "nation": "China", "name": "J-10", "card": "Fighter", "factory": 9},
           {"key": "Modern|China|Odd", "era": "Modern", "nation": "China", "name": "Odd", "card": "Tank", "factory": 12},
           {"key": "Modern|USA|M1", "era": "Modern", "nation": "USA", "name": "M1", "card": "Main Battle Tank", "factory": 10}]

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        self.mod = root / "mod"
        (self.mod / "src").mkdir(parents=True)
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda *a: self.mod
        self.api._open = ShownIndex
        self.api._all_units = lambda ix: self.UNITS
        self.api._names = lambda ix, addresses, lang, new_units=None: {a: a.rsplit("_", 1)[-1] for a in addresses}
        self.api._era_library = lambda: (root, {"units": self.ERA})
        self.api._era_record = lambda: {}
        self.api.menus = lambda lang="base": {"nations": [{"nation": n, "factories": [
            {"factory": 9, "units": ["Plane"], "count": 1}, {"factory": 10, "units": ["Tank"], "count": 1}]
            if n == 4 else []} for n in range(7)]}

    def tearDown(self):
        self.dir.cleanup()

    def test_hidden_and_shown_again(self):
        view = self.api.nation_units(4)
        self.assertEqual([(u["name"], u["hidden"]) for u in view["units"]], [("Plane", False), ("Tank", False)])
        self.assertEqual((view["hidden"], view["can"], view["eras"]), (0, True, [{"era": "Modern", "nations": ["China", "USA"]}]))
        view = self.api.nation_units_hide(4, True)  # its HQ and the unit in no menu stay; the US tank too
        self.assertEqual([u["hidden"] for u in view["units"]], [True, True])
        text = (self.mod / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("ShowInMenu = [0, 0, 0, 0, 0]", text)
        self.assertNotIn("Italy_HQ", text)
        self.assertNotIn("US_Tank", text)
        self.assertNotIn("unlinked", view)  # nothing was researched from them
        view = self.api.nation_units_hide(4, False)
        self.assertEqual(view["hidden"], 0)
        self.assertNotIn("ShowInMenu", (self.mod / "src" / "studio.rndf").read_text(encoding="utf-8"))

    def test_a_unit_researched_from_a_hidden_one_is_unlinked(self):
        """The 2026-10-10 crash: Chinese units researched from Italy's, Italy's then hidden; the game's menu stops on a
        shown upgrade whose parent has no button. Hide all makes such a unit buyable from the start, and says so."""
        china = "$/GFX/Everything/Descriptor_Unit_China_Type99"
        self.api._upgrade_links = lambda ix, edits: {china: "$/GFX/Everything/Descriptor_Unit_Italy_Tank",
                                                     "$/GFX/Everything/Descriptor_Unit_US_Tank2": "$/GFX/Everything/Descriptor_Unit_US_Tank"}
        calls = []
        self.api.set_upgrade = lambda address, parent, lang="base": calls.append((address, parent))
        view = self.api.nation_units_hide(4, True)
        self.assertEqual(calls, [(china, None)])
        self.assertEqual(view["unlinked"], ["Type99"])
        calls.clear()
        self.api.nation_units_hide(4, False)  # showing them again unlinks nothing
        self.assertEqual(calls, [])

    def test_filled_from_an_era(self):
        listed = self.api.nation_fill_list(4, "Modern", "China")
        self.assertEqual([(u["name"], u["factory"]) for u in listed["units"]],
                         [("J-10", 9), ("ZTZ-99", 10), ("Odd", None)])  # Italy has no building 12: picked by hand
        added = []

        def era_unit_add(key, nation, factory, *rest, **more):
            if key.endswith("J-10"):
                raise nations.NationError("J-10: no model")
            added.append((key, nation, factory))
            return {"name": key.rsplit("|", 1)[-1], "address": "x"}
        self.api.era_unit_add = era_unit_add
        job = self.api.nation_fill(4, [{"key": "Modern|China|ZTZ-99", "factory": 10},
                                       {"key": "Modern|China|J-10", "factory": 9}])["job"]
        for _ in range(200):
            got = self.api.job(job)
            if got["state"] != "running":
                break
            time.sleep(0.01)
        self.assertEqual(got["state"], "done")
        self.assertEqual(got["lines"], ["added\tZTZ-99", "skipped\tJ-10\tJ-10: no model"])
        self.assertEqual(added, [("Modern|China|ZTZ-99", 4, 10)])
        for picks, why in (([], "Pick 1"), ([{"key": "nope", "factory": 10}], "not in the era units library"),
                           ([{"key": "Modern|China|Odd", "factory": 12}], "pick one of this nation's buildings")):
            with self.subTest(picks=picks), self.assertRaisesRegex(nations.NationError, why):
                self.api.nation_fill(4, picks)
        self.api._mod_dir = lambda *a: None
        with self.assertRaises(nations.NationError):
            self.api.nation_units_hide(4)


if __name__ == "__main__":
    unittest.main()
