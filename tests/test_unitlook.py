"""Painted textures into the game (rusemod.unitlook) and PNG pictures (rusemod.png), on made-up textures (no game
files)."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from rusemod import blender, dxt, tgu1, unitlook
from rusemod.png import PngError, read_png
from rusemod.tmst import Tgv, make_tgv
from rusemod.unitpacks import ProxyPack


def png(rgb_rows, ctype=2, filt=0):
    """A small PNG: rows of pixel tuples (3 or 4 values), every line with the same filter."""
    h, w = len(rgb_rows), len(rgb_rows[0])
    raw = b"".join(bytes([filt]) + bytes(v for px in row for v in px) for row in rgb_rows)
    if filt == 1:  # Sub: store differences from the pixel to the left
        bpp = len(rgb_rows[0][0])
        lines = []
        for row in rgb_rows:
            flat = [v for px in row for v in px]
            lines.append(bytes([1]) + bytes((flat[i] - (flat[i - bpp] if i >= bpp else 0)) & 0xFF for i in range(len(flat))))
        raw = b"".join(lines)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def plain_level(w_blocks, h_blocks, blocks, alpha=True):
    head = tgu1.Header(5, w_blocks, h_blocks, 80, 40, w_blocks * h_blocks, tgu1.FLAG_ALPHA if alpha else 0)
    return head.pack()[:tgu1.PLAIN_HEADER] + blocks


def solid_dxt5(n, rgb=(40, 80, 40), alpha=128):
    c = dxt.pack565(*rgb)
    return (bytes([alpha, alpha]) + bytes(6) + struct.pack("<HHI", c, c, 0)) * n


def texture(size=16):
    """A DXT5 texture of `size` pixels (levels down to 4 x 4), every level one green, alpha 128."""
    levels, s = [], size
    while s >= 4:
        levels.append(plain_level(s // 4, s // 4, solid_dxt5((s // 4) ** 2)))
        s //= 2
    return make_tgv(size, size, "DXT5", list(reversed(levels)))


class Png(unittest.TestCase):
    def test_rgb_rgba_and_filters(self):
        rows = [[(10, 20, 30), (40, 50, 60)], [(70, 80, 90), (100, 110, 120)]]
        for filt in (0, 1):
            w, h, px = read_png(png(rows, filt=filt))
            self.assertEqual((w, h), (2, 2))
            self.assertEqual(px[:8], bytes([10, 20, 30, 255, 40, 50, 60, 255]))
        w, h, px = read_png(png([[(1, 2, 3, 4)]], ctype=6))
        self.assertEqual(px, bytes([1, 2, 3, 4]))

    def test_not_a_png(self):
        with self.assertRaises(PngError):
            read_png(b"GIF89a")


class Texture(unittest.TestCase):
    def test_unpainted_picture_changes_nothing(self):
        original = texture()
        g = Tgv(original)
        full = dxt.decode_rgba(tgu1.decode(g.payload(len(g.mips) - 1)), 16, 16, "DXT5")
        new, report = unitlook.make_texture(original, full, None, 16, 16)
        self.assertIs(new, original)
        self.assertEqual(report["encoded"], 0)

    def test_painted_block_only_and_alpha_kept(self):
        original = texture()
        g = Tgv(original)
        full = bytearray(dxt.decode_rgba(tgu1.decode(g.payload(len(g.mips) - 1)), 16, 16, "DXT5"))
        for y in range(4):  # paint the top-left 4 x 4 block red
            for x in range(4):
                full[4 * (y * 16 + x):4 * (y * 16 + x) + 3] = bytes([255, 0, 0])
        new, report = unitlook.make_texture(original, bytes(full), None, 16, 16)
        n = Tgv(new)
        self.assertEqual((n.flag, n.format, len(n.mips)), (1, "DXT5", 3))
        big = tgu1.decode(n.payload(2))
        old_big = tgu1.decode(g.payload(2))
        self.assertEqual(big[16:], old_big[16:])           # every other block is the game's, byte for byte
        self.assertEqual(big[:8], old_big[:8])             # the painted block keeps its alpha
        self.assertEqual(dxt.block_pixels(big[8:16])[0], (255, 0, 0))
        self.assertEqual(report["encoded"], 3)             # that block in each of the 3 levels
        for m in range(3):  # every level written as the game's own small levels: plain TGU1, DXT5
            self.assertEqual(tgu1.Header.parse(n.payload(m)).flags, tgu1.FLAG_ALPHA)

    def test_wrong_size_refused(self):
        with self.assertRaises(unitlook.LookError):
            unitlook.make_texture(texture(), bytes(8 * 8 * 4), None, 8, 8)

    def test_standin_changed_in_place(self):
        standin = make_tgv(8, 8, "DXT5", [solid_dxt5(4)], flag=0)
        full = bytearray(dxt.decode_rgba(solid_dxt5(16), 16, 16, "DXT5"))
        flags = [True] + [False] * 15
        for y in range(4):
            for x in range(4):
                full[4 * (y * 16 + x):4 * (y * 16 + x) + 3] = bytes([255, 0, 0])
        new = unitlook.make_standin(standin, bytes(full), None, 16, 16, flags, [False] * 16)
        g = Tgv(standin)
        off, size = g.mips[0]
        self.assertEqual(new[:off], standin[:off])          # header and flag 0 kept
        self.assertEqual(Tgv(new).flag, 0)
        self.assertNotEqual(new[off + 8:off + 16], standin[off + 8:off + 16])
        self.assertEqual(new[off + 16:], standin[off + 16:])

    def test_mod_files_and_names(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "files" / "replace" / "gen" / "ww2" / "x"
            root.mkdir(parents=True)
            (root / "a01.tgv.png").write_bytes(b"")
            (root / "a01.tgv.alpha.png").write_bytes(b"")
            (root / "notes.png").write_bytes(b"")
            found = unitlook.mod_textures(Path(d))
            self.assertEqual(list(found), ["gen\\ww2\\x\\a01.tgv"])
            self.assertEqual([p.name for p in found["gen\\ww2\\x\\a01.tgv"]], ["a01.tgv.png", "a01.tgv.alpha.png"])
        self.assertEqual(unitlook.standin_name("gen\\WW2\\x\\a01.tgv"), "gentexproxy\\ww2\\x\\a01.tgv")

    def test_ruse_build_writes_the_texture_and_its_standin(self):
        import contextlib
        import io

        from fixtures import make_edat
        from rusemod.cli import main
        from rusemod.edat import Edat
        from rusemod.unitpacks import Proxy
        from test_build import PACK
        name = b"gentexproxy\\ww2\\x\\a01.tgv"
        standin = make_tgv(8, 8, "DXT5", [solid_dxt5(4)], flag=0)
        ppk = ProxyPack([Proxy(b"k" * 8, standin, bytes(8), name.ljust(256, b"\0"))], [0]).to_bytes()
        zz = make_edat([("dir", "gen\\ww2\\x\\", [("file", "a01.tgv", texture())]),
                        ("dir", "gentexproxy\\pack\\", [("file", "p.ppk", ppk)])])
        with tempfile.TemporaryDirectory() as d:
            game = Path(d, "R.U.S.E")
            data = game / "Data" / "PC" / "190852"
            data.mkdir(parents=True)
            (data / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            (data / "ZZ_Win.dat").write_bytes(zz)
            mod = Path(d, "paint")
            pic = mod / "files" / "replace" / "gen" / "ww2" / "x" / "a01.tgv.png"
            pic.parent.mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "paint"\nversion = "1.0.0"\n', encoding="utf-8")
            rows = [[(255, 0, 0) if x < 4 and y < 4 else (40, 80, 40) for x in range(16)] for y in range(16)]
            pic.write_bytes(png(rows))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["--game", str(game), "build", str(mod), "--instance", str(Path(d, "copy"))])
            self.assertEqual(code, 0, out.getvalue())
            self.assertIn("painted textures: 1", out.getvalue())
            copy = Edat(Path(d, "copy", "Data", "PC", "190852", "ZZ_Win.dat").read_bytes())
            new = Tgv(bytes(copy.read(copy.find("a01.tgv"))))
            self.assertEqual(dxt.block_pixels(tgu1.decode(new.payload(2))[8:16])[0], (255, 0, 0))  # painted red
            proxy = ProxyPack.read(bytes(copy.read(copy.find("p.ppk"))))
            self.assertNotEqual(proxy.proxies[0].data, standin)
            self.assertEqual((data / "ZZ_Win.dat").read_bytes(), zz)  # the install untouched

    def test_shared_standin_left_as_the_game_has_it(self):
        """A stand-in sharing its picture (the Sherman's tracks with the Firefly's) is left alone: the other texture
        keeps its look and the pack keeps its size and bytes (T27, 2026-10-04)."""
        from fixtures import make_edat
        from rusemod.edat import Edat
        from rusemod.unitpacks import Proxy
        standin = make_tgv(8, 8, "DXT5", [solid_dxt5(4)], flag=0)
        mine, other, alone = (b"gentexproxy\\ww2\\x\\a01.tgv", b"gentexproxy\\ww2\\y\\a01.tgv",
                              b"gentexproxy\\ww2\\x\\b01.tgv")
        shared = ProxyPack([Proxy(b"k" * 8, standin, bytes(8), other.ljust(256, b"\0")),
                            Proxy(b"m" * 8, standin, bytes(8), mine.ljust(256, b"\0"))], [0, 0]).to_bytes()
        own = ProxyPack([Proxy(b"n" * 8, standin, bytes(8), mine.ljust(256, b"\0")),
                         Proxy(b"o" * 8, make_tgv(8, 8, "DXT5", [solid_dxt5(4, alpha=7)], flag=0), bytes(8),
                               alone.ljust(256, b"\0"))], [0, 1]).to_bytes()
        zz = Edat(make_edat([("dir", "gen\\ww2\\x\\", [("file", "a01.tgv", texture())]),
                             ("dir", "gentexproxy\\pack\\", [("file", "s.ppk", shared), ("file", "t.ppk", own)])]))
        with tempfile.TemporaryDirectory() as d:
            pic = Path(d, "a01.tgv.png")
            pic.write_bytes(png([[(255, 0, 0)] * 16] * 16))
            said = []
            out = unitlook.changes(zz, {"gen\\ww2\\x\\a01.tgv": (pic, None)}, say=said.append)
        paths = {p.rsplit("\\", 1)[-1] for p in out}
        self.assertEqual(paths, {"a01.tgv", "t.ppk"})  # the pack where it shares its picture isn't changed at all
        t = ProxyPack.read(out[next(p for p in out if p.endswith("t.ppk"))])
        self.assertEqual(len(out[next(p for p in out if p.endswith("t.ppk"))]), len(own))
        self.assertNotEqual(t.proxies[0].data, standin)  # its own stand-in is painted
        self.assertTrue(any("shares its picture" in s for s in said), said)

    def test_card_picture(self):
        """A unit's card (one DXT1_LIN level, ZIPO, as all 450 of the game's): changed blocks encoded again, the rest
        the game's byte for byte, packed again under the same TGV header; unchanged: the original."""
        from rusemod.tmst import zipo_pack, zipo_unpack
        w, h = 12, 8
        grey = dxt.pack565(120, 120, 120)
        card = make_tgv(w, h, "DXT1_LIN", [zipo_pack(struct.pack("<HHI", grey, grey, 0) * 6)])
        self.assertTrue(unitlook.is_picture(card))
        self.assertFalse(unitlook.is_picture(texture()))
        _w, _h, px = unitlook.picture_rgba(card)
        same, report = unitlook.make_picture(card, px, w, h)
        self.assertIs(same, card)
        self.assertEqual(report["encoded"], 0)
        new_px = bytearray(px)
        for y in range(4):  # the middle block of the top row red
            for x in range(4, 8):
                new_px[4 * (y * w + x):4 * (y * w + x) + 3] = bytes([255, 0, 0])
        new, report = unitlook.make_picture(card, bytes(new_px), w, h)
        self.assertEqual(report, {"levels": 1, "blocks": 6, "encoded": 1})
        g, old_blocks = Tgv(new), zipo_unpack(Tgv(card).payload(0))
        self.assertEqual((g.flag, g.format, g.width, g.height, len(g.mips), g.codec), (1, "DXT1_LIN", 12, 8, 1, "ZIPO"))
        blocks = zipo_unpack(g.payload(0))
        self.assertEqual(blocks[:8] + blocks[16:], old_blocks[:8] + old_blocks[16:])
        self.assertEqual(dxt.block_pixels(blocks[8:16])[0], (255, 0, 0))
        with self.assertRaises(unitlook.LookError):
            unitlook.make_picture(card, bytes(8 * 8 * 4), 8, 8)

    def test_card_also_replaced_in_the_menu_packs(self):
        """The build menu shows the copy of a card inside a menu pack (an archive of its own inside ZZ_Win.dat,
        gen\\pack\\menuus.ppk): the build replaces it there too, and leaves the pack's other members as they are."""
        from fixtures import make_edat
        from rusemod.edat import Edat
        from rusemod.tmst import zipo_pack
        grey = dxt.pack565(120, 120, 120)
        card = make_tgv(8, 4, "DXT1_LIN", [zipo_pack(struct.pack("<HHI", grey, grey, 0) * 2)])
        other = make_tgv(4, 4, "DXT1_LIN", [zipo_pack(bytes(8))])
        folder = "gen\\ww2\\res2d\\texanimationuniticone\\eu\\"
        menu = make_edat([("dir", folder, [("file", "test.tgv", card), ("file", "other.tgv", other)])])
        zz = Edat(make_edat([("dir", folder, [("file", "test.tgv", card)]),
                             ("dir", "gen\\pack\\", [("file", "menuus.ppk", menu), ("file", "menuger.ppk",
                                                     make_edat([("dir", folder, [("file", "other.tgv", other)])]))])]))
        with tempfile.TemporaryDirectory() as d:
            pic = Path(d, "test.tgv.png")
            pic.write_bytes(png([[(200, 30, 30)] * 8] * 4))
            said = []
            out = unitlook.changes(zz, {folder + "test.tgv": (pic, None)}, say=said.append)
        names = sorted(p.rsplit("\\", 1)[-1] for p in out)
        self.assertEqual(names, ["menuus.ppk", "test.tgv"])  # the German menu pack has no copy: left alone
        loose = out[next(p for p in out if p.endswith("test.tgv"))]
        inner = Edat(out[next(p for p in out if p.endswith("menuus.ppk"))])
        self.assertEqual(bytes(inner.read(inner.entry(folder + "test.tgv"))), loose)
        self.assertEqual(bytes(inner.read(inner.entry(folder + "other.tgv"))), other)
        self.assertTrue(any("menuus.ppk" in s for s in said), said)

    def test_card_member(self):
        self.assertEqual(unitlook.card_member("datadir:/ww2/res2d/texanimationuniticone/eu/m4_sherman.png"),
                         "gen\\ww2\\res2d\\texanimationuniticone\\eu\\m4_sherman.tgv")

    def test_new_units_own_card_name(self):
        self.assertEqual(unitlook.own_card_name("datadir:/ww2/res2d/texanimationuniticone/eu/m4_sherman.png",
                                                "Descriptor_Unit_R2_M4_Sherman_Tall"),
                         "datadir:/ww2/res2d/texanimationuniticone/eu/descriptor_unit_r2_m4_sherman_tall.png")
        game = "DataDir:\\WW2\\Res2D\\TexAnimationUnitIcone\\EU\\M4_Sherman.png"  # as the game's data writes it
        self.assertEqual(unitlook.own_card_name(game, "Descriptor_Unit_R2_X"),
                         "DataDir:\\WW2\\Res2D\\TexAnimationUnitIcone\\EU\\descriptor_unit_r2_x.png")
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(unitlook.mod_cards(Path(d)), {})
            cards = Path(d, "files", "cards")
            cards.mkdir(parents=True)
            (cards / "Descriptor_Unit_R2_X.png").write_bytes(b"x")
            (cards / "notes.txt").write_bytes(b"x")
            self.assertEqual(list(unitlook.mod_cards(Path(d))), ["Descriptor_Unit_R2_X"])

    def test_new_units_card_added_to_the_menu_packs(self):
        """A new unit's own card (T33: it had its source's, so both looked the same): made from the source's card
        (its format and size) and added beside it in every menu pack that holds the source's; the pack's other
        members, the source's card and the packs without it stay as they were."""
        from fixtures import make_edat
        from rusemod.edat import Edat
        from rusemod.tmst import zipo_pack
        grey = dxt.pack565(120, 120, 120)
        card = make_tgv(8, 4, "DXT1_LIN", [zipo_pack(struct.pack("<HHI", grey, grey, 0) * 2)])
        other = make_tgv(4, 4, "DXT1_LIN", [zipo_pack(bytes(8))])
        folder = "gen\\ww2\\res2d\\texanimationuniticone\\eu\\"
        menu = make_edat([("dir", folder, [("file", "other.tgv", other), ("file", "test.tgv", card)])])
        german = make_edat([("dir", folder, [("file", "other.tgv", other)])])
        zz = Edat(make_edat([("dir", folder, [("file", "test.tgv", card)]),
                             ("dir", "gen\\pack\\", [("file", "menuger.ppk", german), ("file", "menuus.ppk", menu)])]))
        new = folder + "descriptor_unit_r2_x.tgv"
        with tempfile.TemporaryDirectory() as d:
            pic = Path(d, "Descriptor_Unit_R2_X.png")
            pic.write_bytes(png([[(200, 30, 30)] * 8] * 4))
            said, loose = [], {}
            out = unitlook.own_cards(zz, {new: (folder + "test.tgv", pic)}, say=said.append, loose=loose)
            self.assertEqual(sorted(p.rsplit("\\", 1)[-1] for p in out), ["menuus.ppk"])
            inner = Edat(out[next(iter(out))])
            # a file of ZZ_Win.dat's own too, like the game's cards: read there once the unit is on the map (T35 crash)
            self.assertEqual(loose, {new: bytes(inner.read(inner.entry(new)))})
            made = Tgv(bytes(inner.read(inner.entry(new))))
            self.assertEqual((made.format, made.width, made.height, made.codec, made.flag), ("DXT1_LIN", 8, 4, "ZIPO", 1))
            # (200, 30, 30) in 5-6-5 bits: 24, 7, 4 -> (198, 28, 33)
            self.assertEqual(unitlook.picture_rgba(bytes(inner.read(inner.entry(new))))[2][:3], bytes([198, 28, 33]))
            self.assertEqual(bytes(inner.read(inner.entry(folder + "test.tgv"))), card)  # the source's as it was
            self.assertEqual(bytes(inner.read(inner.entry(folder + "other.tgv"))), other)
            with self.assertRaises(unitlook.LookError):  # its source's card isn't in the game
                unitlook.own_cards(zz, {new: (folder + "missing.tgv", pic)}, say=said.append)
            with self.assertRaises(unitlook.LookError):  # the name is taken
                unitlook.own_cards(zz, {folder + "test.tgv": (folder + "test.tgv", pic)}, say=said.append)
            pic.write_bytes(png([[(200, 30, 30)] * 4] * 4))
            with self.assertRaises(unitlook.LookError):  # not the card's size
                unitlook.own_cards(zz, {new: (folder + "test.tgv", pic)}, say=said.append)

    def test_a_clone_gets_its_own_card_file(self):
        """The build: a new unit with files/cards/<its name>.png names a card file of its own (beside its source's);
        a card for a unit no mod makes is an error."""
        from types import SimpleNamespace

        from rusemod.build import BuildResult, unit_cards
        from rusemod.patch import Inline, Obj, Text
        from rusemod.resolve import ModInfo
        source = "datadir:/ww2/res2d/texanimationuniticone/eu/m4_sherman.png"
        unit = Obj("TUniteAuSolDescriptor", {"TextureForInterface": Inline(Obj("TTexture", {
            "FileName": Text("path", source)}))})
        name = "$/GFX/Everything/Descriptor_Unit_R2_X"
        run = SimpleNamespace(created={name: SimpleNamespace(kind="clone")}, game=SimpleNamespace(objects={name: unit}))
        result = BuildResult()
        cards = unit_cards(run, [ModInfo("m", cards={"Descriptor_Unit_R2_X": Path("a.png")})], result)
        new = "datadir:/ww2/res2d/texanimationuniticone/eu/descriptor_unit_r2_x.png"
        self.assertEqual(unit.props["TextureForInterface"].obj.props["FileName"], Text("path", new))
        self.assertEqual(cards, {unitlook.card_member(new): (unitlook.card_member(source), Path("a.png"))})
        self.assertEqual(result.errors, [])
        result = BuildResult()
        self.assertEqual(unit_cards(run, [ModInfo("m", cards={"Descriptor_Unit_R2_Y": Path("b.png")})], result), {})
        self.assertEqual(len(result.errors), 1)

    def test_alpha_block(self):
        block = unitlook.alpha_block([0] * 8 + [255] * 8)
        self.assertEqual(block[:2], bytes([255, 0]))
        _rgb, alphas = dxt.dxt5_block(block + bytes(8))
        self.assertEqual(alphas, [0] * 8 + [255] * 8)


def answer_save(folder, saved, before=None):
    """A stand-in for blender_open.py's watch: wait for the save request, do `before` (the "saving"), answer."""
    import json
    import threading
    import time

    def run():
        end = time.monotonic() + 5
        while not (folder / blender.SAVE_REQUEST).exists() and time.monotonic() < end:
            time.sleep(0.02)
        if before:
            before()
        (folder / blender.SAVE_DONE).write_text(json.dumps(saved), encoding="utf-8")
        (folder / blender.SAVE_REQUEST).unlink(missing_ok=True)
    t = threading.Thread(target=run)
    t.start()
    return t


class Blender(unittest.TestCase):
    """Bring back asks the Blender painting the unit to save (rusemod.blender.ask_to_save, blender_open.py)."""

    def test_answered(self):
        with tempfile.TemporaryDirectory() as d:
            t = answer_save(Path(d), ["x_colour.png"])
            self.assertEqual(blender.ask_to_save(Path(d), timeout=5), ["x_colour.png"])
            t.join()
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), [])  # request and answer both gone

    def test_no_blender_answers(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(blender.ask_to_save(Path(d), timeout=0.3))
            self.assertFalse((Path(d) / blender.SAVE_REQUEST).exists())  # a Blender opened later won't answer it

    def test_a_portable_blender_is_found(self):
        """Blender unzipped from blender.org (no installer: not in Program Files, not on the PATH) is found at the top
        of a drive or one folder down, the newest first (one in D:\\Tools\\blender-4.5-windows-x64 wasn't, before)."""
        from unittest import mock
        with tempfile.TemporaryDirectory() as drive, tempfile.TemporaryDirectory() as home:
            for folder in ("Tools/blender-4.5.14-windows-x64", "blender-4.2.3-windows-x64", "Games/notblender"):
                Path(drive, folder).mkdir(parents=True)
            for folder in ("Tools/blender-4.5.14-windows-x64", "blender-4.2.3-windows-x64"):
                Path(drive, folder, "blender.exe").write_bytes(b"")
            Path(drive, "Games", "notblender", "blender.exe").write_bytes(b"")  # not a blender* folder: no
            Path(home, "Downloads", "blender-3.6.0").mkdir(parents=True)
            Path(home, "Downloads", "blender-3.6.0", "blender.exe").write_bytes(b"")
            with mock.patch.object(blender, "_drives", lambda: [drive]), \
                    mock.patch("pathlib.Path.home", lambda: Path(home)):
                found = blender.portable_blenders()
                self.assertEqual(sorted(p.parent.name for p in found),
                                 ["blender-3.6.0", "blender-4.2.3-windows-x64", "blender-4.5.14-windows-x64"])
                with mock.patch.dict("os.environ", {"ProgramFiles": drive, "ProgramW6432": "", "RUSE_BLENDER": ""}), \
                        mock.patch("shutil.which", lambda name: None), \
                        mock.patch("rusemod.steam.steam_roots", lambda: []):
                    self.assertEqual(blender.find_blender().parent.name, "blender-4.5.14-windows-x64")
                    chosen = Path(drive, "blender-4.2.3-windows-x64", "blender.exe")
                    self.assertEqual(blender.find_blender(str(chosen)), chosen)  # the user's pick first

    def test_the_opener_uses_the_same_file_names(self):
        import re
        source = blender.OPENER.read_text(encoding="utf-8")
        names = re.search(r'^SAVE_REQUEST, SAVE_DONE = "([^"]+)", "([^"]+)"', source, re.M).groups()
        self.assertEqual(names, (blender.SAVE_REQUEST, blender.SAVE_DONE))
        self.assertIn('"S", "PRESS", ctrl=True', source)  # Ctrl+S saves the paint (checked in Blender 4.5)


class StudioLook(unittest.TestCase):
    """The Studio's unit preview and Bring back, with the game's models and Blender stood in for."""

    MODEL, TEX = "ww2\\x\\tanklod0.ase2ndfbin", "gen\\ww2\\x\\a01.tgv"

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._look_models = lambda address: ([self.MODEL], [self.TEX])
        self.api._look_card = lambda address: None  # no card unless a test gives one
        self.api._mod_dir = lambda: self.mod

    def tearDown(self):
        self.dir.cleanup()

    def test_preview_made_once_with_the_mods_paint(self):
        from unittest import mock
        made = []

        class Lib:
            def __init__(self, game):
                made.append(game)

            def close(self):
                pass
        with mock.patch("rusemod.models.Library", Lib), \
                mock.patch("rusemod.gltf.model_glb", lambda lib, name, side: (b"glTF-test", {}, {})):
            first = self.api.unit_preview("$/GFX/Everything/Descriptor_Unit_Test")
            self.assertEqual(first["paint"], {})
            pic = self.mod / "files" / "replace" / "gen" / "ww2" / "x" / "a01.tgv.png"
            pic.parent.mkdir(parents=True)
            pic.write_bytes(png([[(255, 0, 0)]]))
            again = self.api.unit_preview("$/GFX/Everything/Descriptor_Unit_Test")
        self.assertEqual(len(made), 1)  # the model was made once, then taken from the cache
        self.assertEqual(again["models"], first["models"])
        url = first["models"][0]["url"]
        self.assertTrue(url.startswith("cache/units/") and url.endswith(".glb"), url)
        self.assertEqual((self.api.cache_dir / url[len("cache/"):]).read_bytes(), b"glTF-test")
        painted = again["paint"][self.TEX]
        self.assertEqual((self.api.cache_dir / painted[len("cache/"):]).read_bytes(), pic.read_bytes())

    def test_card_saved_in_the_mod_and_reset(self):
        import base64

        from fixtures import make_edat
        from rusemod.tmst import zipo_pack
        from ruse_studio.api import StudioError
        member = "gen\\ww2\\res2d\\texanimationuniticone\\eu\\test.tgv"
        grey = dxt.pack565(120, 120, 120)
        card = make_tgv(8, 4, "DXT1_LIN", [zipo_pack(struct.pack("<HHI", grey, grey, 0) * 2)])
        zz = Path(self.dir.name) / "R.U.S.E" / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        zz.write_bytes(make_edat([("dir", "gen\\ww2\\res2d\\texanimationuniticone\\eu\\", [("file", "test.tgv", card)])]))
        self.api._look_card = lambda address: member
        address = "$/GFX/Everything/Descriptor_Unit_Test"
        view = self.api._card_view(address)
        self.assertEqual((view["texture"], view["width"], view["height"], view["own"]), (member, 8, 4, False))
        self.assertTrue((self.api.cache_dir / view["url"][len("cache/"):]).is_file())  # the game's card, as a PNG
        shot = png([[(200, 30, 30)] * 8] * 4)
        res = self.api.look_card(address, "data:image/png;base64," + base64.b64encode(shot).decode())
        saved = self.mod / "files" / "replace" / "gen" / "ww2" / "res2d" / "texanimationuniticone" / "eu" / "test.tgv.png"
        self.assertEqual(saved.read_bytes(), shot)
        self.assertTrue(res["card"]["own"])
        self.assertEqual((self.api.cache_dir / res["card"]["url"][len("cache/"):]).read_bytes(), shot)
        with self.assertRaises(StudioError):  # not the card's size
            self.api.look_card(address, base64.b64encode(png([[(1, 2, 3)] * 4] * 4)).decode())
        self.assertFalse(self.api.look_card_reset(address)["card"]["own"])
        self.assertFalse(saved.exists())

    def test_new_units_card_is_its_own(self):
        """A new unit's card goes to files/cards/<its name>.png, never over its source's (T33: they looked the same)."""
        import base64

        from fixtures import make_edat
        from rusemod.tmst import zipo_pack
        from ruse_studio.edits import NewUnit
        member = "gen\\ww2\\res2d\\texanimationuniticone\\eu\\test.tgv"
        grey = dxt.pack565(120, 120, 120)
        card = make_tgv(8, 4, "DXT1_LIN", [zipo_pack(struct.pack("<HHI", grey, grey, 0) * 2)])
        zz = Path(self.dir.name) / "R.U.S.E" / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        zz.write_bytes(make_edat([("dir", "gen\\ww2\\res2d\\texanimationuniticone\\eu\\", [("file", "test.tgv", card)])]))
        self.api._look_card = lambda address: member  # (the source's card)
        address = "$/GFX/Everything/Descriptor_Unit_R2_New"
        unit = NewUnit(address, "$/GFX/Everything/Descriptor_Unit_Test", "New")

        class Edits:
            def new_unit_of(self, a):
                return unit if a.split(":")[0] == address else None
        self.api._edits = lambda: Edits()
        self.assertFalse(self.api._card_view(address)["own"])
        shot = png([[(200, 30, 30)] * 8] * 4)
        res = self.api.look_card(address, base64.b64encode(shot).decode())
        own = self.mod / "files" / "cards" / "Descriptor_Unit_R2_New.png"
        self.assertEqual(own.read_bytes(), shot)
        self.assertFalse((self.mod / "files" / "replace").exists())  # the source's card isn't touched
        self.assertTrue(res["card"]["own"])
        self.assertFalse(self.api._card_view("$/GFX/Everything/Descriptor_Unit_Test")["own"])  # nor shown for it
        self.assertFalse(self.api.look_card_reset(address)["card"]["own"])
        self.assertFalse(own.exists())

    def test_new_units_own_model(self):
        """Import model: a .3ds or .glb fitted to the copied unit (rusemod.unitmodel.import_model, its own tests) goes
        to the mod's files/models/<the unit's name>.glb, with a record of what was made; the page shows it."""
        from unittest import mock

        from ruse_studio.api import StudioError
        from ruse_studio.edits import NewUnit
        address = "$/GFX/Everything/Descriptor_Unit_R2_New"
        unit = NewUnit(address, "$/GFX/Everything/Descriptor_Unit_Test", "New")

        class Edits:
            def new_unit_of(self, a):
                return unit if a.split(":")[0] == address else None
        self.api._edits = lambda: Edits()
        calls = []

        def fake_import(game, source, file, out, size=1.0, side=1024, pictures=None, aircraft=False):
            calls.append((source, Path(file).name, size))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"glTF-own")
            return {"vertices": 10, "triangles": 4, "draws": 1, "parts": {"Hull": "hull"}, "missing": []}
        model = Path(self.dir.name) / "tank.3ds"
        model.write_bytes(b"3ds")
        self.assertIsNone(self.api.look(address)["own_model"])
        self.assertTrue(self.api.look(address)["new_unit"])
        with mock.patch("rusemod.unitmodel.import_model", fake_import):
            res = self.api.model_import(address, str(model), "1.36")
            with self.assertRaises(StudioError):
                self.api.model_import("$/GFX/Everything/Descriptor_Unit_Test", str(model))  # a game unit
            with self.assertRaises(StudioError):
                self.api.model_import(address, str(model), 9)  # too big
        own = self.mod / "files" / "models" / "Descriptor_Unit_R2_New.glb"
        self.assertEqual((own.read_bytes(), calls), (b"glTF-own", [(self.MODEL, "tank.3ds", 1.36)]))
        self.assertEqual((res["model"]["vertices"], res["model"]["file"]), (10, "tank.3ds"))
        self.assertEqual(self.api.look(address)["own_model"]["vertices"], 10)
        shown = self.api.unit_preview(address)["models"]
        self.assertEqual(len(shown), 1)
        self.assertEqual((self.api.cache_dir / shown[0]["url"][len("cache/"):]).read_bytes(), b"glTF-own")
        self.assertIsNone(self.api.model_import_remove(address)["own_model"])
        self.assertFalse(own.exists() or own.with_suffix(".json").exists())

    def test_own_model_fitted_past_a_crew_figure(self):
        """A copied unit whose models list a crew figure first (the Kubelwagen's driver: no chassis bone) gets the new
        model fitted to the first model that can take one, the vehicle (2026-10-09: every era jeep copying the
        Kubelwagen failed); when none can, the first one's reason is said."""
        from unittest import mock

        from rusemod.unitmodel import UnitModelError
        from ruse_studio.api import StudioError
        from ruse_studio.edits import NewUnit
        address = "$/GFX/Everything/Descriptor_Unit_R2_Jeep"
        unit = NewUnit(address, "$/GFX/Everything/Descriptor_Unit_Test", "Jeep")

        class Edits:
            def new_unit_of(self, a):
                return unit if a.split(":")[0] == address else None
        self.api._edits = lambda: Edits()
        driver, jeep = "ww2\\res3d\\units\\ger\\infanterie\\driverlod0.ase2ndfbin", self.MODEL
        self.api._look_models = lambda a: ([driver, jeep], [])
        tried = []

        def fake_import(game, source, file, out, size=1.0, side=1024, pictures=None, aircraft=False):
            tried.append(source)
            if source == driver:
                raise UnitModelError(f"{driver}'s skeleton has no chassis bone")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"glTF-jeep")
            return {"vertices": 8, "triangles": 2, "draws": 1, "parts": {"Hull": "hull"}, "missing": []}
        model = Path(self.dir.name) / "jeep.glb"
        model.write_bytes(b"glTF")
        with mock.patch("rusemod.unitmodel.import_model", fake_import):
            res = self.api.model_import(address, str(model))
        self.assertEqual((tried, res["model"]["vertices"]), ([driver, jeep], 8))
        self.api._look_models = lambda a: ([driver], [])
        with mock.patch("rusemod.unitmodel.import_model", fake_import), \
                self.assertRaisesRegex(StudioError, "no chassis bone"):
            self.api.model_import(address, str(model))

    def test_bring_back_asks_the_running_blender_to_save(self):
        import json
        folder = Path(self.dir.name) / "work"
        folder.mkdir()
        self.api._look_folder = lambda address: folder
        pic = folder / "tank_A01_colour.png"
        pic.write_bytes(png([[(40, 80, 40)] * 4] * 4))
        record = {"models": [], "pictures": {pic.name: {"texture": self.TEX, "kind": "colour",
                                                        "hash": unitlook._pixels_hash(pic, False)}}}
        (folder / unitlook.LOOK_FILE).write_text(json.dumps(record), encoding="utf-8")

        class Running:
            def poll(self):
                return None
        self.api._blenders[str(folder)] = Running()
        # the paint is only on the picture once Blender saves it, which it does when asked
        t = answer_save(folder, [pic.name], before=lambda: pic.write_bytes(png([[(255, 0, 0)] * 4] * 4)))
        res = self.api.look_bring_back("$/GFX/Everything/Descriptor_Unit_Test")
        t.join()
        self.assertEqual(res["brought"], [{"texture": self.TEX, "kind": "colour"}])
        self.assertEqual((self.mod / "files" / "replace" / "gen" / "ww2" / "x" / "a01.tgv.png").read_bytes(),
                         pic.read_bytes())
        self.assertEqual(res["painted"], [self.TEX])

        class Closed:
            def poll(self):
                return 0
        self.api._blenders[str(folder)] = Closed()  # closed: not asked (no waiting), what it saved is used
        res = self.api.look_bring_back("$/GFX/Everything/Descriptor_Unit_Test")
        self.assertEqual(res["brought"], [])
        self.assertIn("Nothing new", res["message"])
        self.assertFalse((folder / blender.SAVE_REQUEST).exists())


if __name__ == "__main__":
    unittest.main()
