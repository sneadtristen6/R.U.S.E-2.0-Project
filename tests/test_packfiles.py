"""The Files tab (rusemod.packfiles, StudioApi.files_*; LittleGroove's Raw / Asset Editor, Browse / Files): every file of
a made-up game's packs and of a pack inside one, each shown as what it is and saved out; nothing written into the
game."""
import base64
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf
from rusemod import packfiles
from rusemod.png import read_png
from rusemod.tmst import make_tgv, zipo_pack
from ruse_studio.api import StudioApi, StudioError


def dic(rows) -> bytes:
    """A text table of (key name, text) rows, laid out as the game's .dic files are."""
    from rusemod.dic import name_to_key
    head = b"TRA\x01" + struct.pack("<I", len(rows))
    off = 8 + 16 * len(rows)
    table, texts = b"", b""
    for name, text in rows:
        raw = text.encode("utf-16-le")
        table += struct.pack("<QII", name_to_key(name), off + len(texts), len(text))
        texts += raw
    return head + table + texts


# a 2x2 A8R8G8B8 picture (B, G, R, A in memory): red, green, blue, half-clear white
PIXELS = bytes([0, 0, 255, 255, 0, 255, 0, 255, 255, 0, 0, 255, 255, 255, 255, 128])
TEXTURE = make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(PIXELS)])
INNER = make_edat([("file", "gen\\inner\\card.tgv", TEXTURE)])


def write_game(root: Path) -> Path:
    game = root / "game"
    rev = game / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "gen\\", [
        ("file", "flag.tgv", TEXTURE), ("file", "notes.txt", "Bonjour, été\n".encode("utf-8")),
        ("file", "blob.bin", bytes(range(256)) * 40), ("file", "menu.ppk", INNER)]),
        ("file", "genlocalisation\\us\\baseunite.dic", dic([("N_A", "ALPHA"), ("N_B", "BRAVO")]))]))
    nd = make_ndf(objects=[(0, []), (0, []), (1, [])], classes=["TUnit", "TWeapon"], props=[])
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "genglad\\everything.ndfbin", nd)]))
    (game / "Maps" / "PC").mkdir(parents=True)
    (game / "Maps" / "PC" / "DataMapIsland_v09.dat").write_bytes(make_edat([("file", "output\\highdef.tms", b"TMS")]))
    (game / "RUSE.exe").write_bytes(b"MZ")
    return game


class Files(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = write_game(Path(cls.tmp.name))
        cls.before = {p: p.read_bytes() for p in cls.game.rglob("*.dat")}

    @classmethod
    def tearDownClass(cls):
        after = {p: p.read_bytes() for p in cls.game.rglob("*.dat")}
        cls.tmp.cleanup()
        assert after == cls.before, "a game pack was changed"

    def test_the_packs_and_their_files(self):
        self.assertEqual([(p["id"], p["file"], p["map"]) for p in packfiles.packs(self.game)],
                         [("gameplay", "ZZ_GladPatchableWin.dat", False), ("texts", "ZZ_Win.dat", False),
                          ("map:DataMapIsland_v09.dat", "DataMapIsland_v09.dat", True)])
        listed = packfiles.listing(self.game, "texts")
        self.assertEqual(([(f["path"], f["kind"]) for f in listed["files"]], listed["total"], listed["matching"]),
                         ([("gen\\flag.tgv", "texture"), ("gen\\notes.txt", "text"), ("gen\\blob.bin", "binary"),
                           ("gen\\menu.ppk", "pack"), ("genlocalisation\\us\\baseunite.dic", "table")], 5, 5))
        self.assertEqual([f["path"] for f in packfiles.listing(self.game, "texts", (), "GEN/F")["files"]],
                         ["gen\\flag.tgv"])  # any case, / or \
        inner = packfiles.listing(self.game, "texts", ["gen\\menu.ppk"])
        self.assertEqual([f["path"] for f in inner["files"]], ["gen\\inner\\card.tgv"])
        self.assertEqual(packfiles.listing(self.game, "map:DataMapIsland_v09.dat")["total"], 1)
        for pack, nested, why in (("sounds", (), "no pack 'sounds'"), ("map:..\\x.dat", (), "no map pack"),
                                  ("texts", ["gen\\notes.txt"], "isn't a pack"), ("texts", ["gen\\none.ppk"], "no ")):
            with self.subTest(pack=pack, nested=nested), self.assertRaisesRegex(packfiles.PackFileError, why):
                packfiles.listing(self.game, pack, nested)

    def test_each_file_shown_as_what_it_is(self):
        pic = packfiles.preview(self.game, "texts", (), "gen\\flag.tgv")
        self.assertEqual((pic["kind"], pic["width"], pic["height"], pic["full"], pic["format"]),
                         ("picture", 2, 2, [2, 2], "A8R8G8B8_LIN"))
        self.assertEqual(read_png(pic["png"])[2], bytes([255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255,
                                                          255, 255, 255, 128]))  # red, green, blue: the right order
        table = packfiles.preview(self.game, "texts", (), "genlocalisation\\us\\baseunite.dic")
        self.assertEqual((table["kind"], table["rows"], table["count"]), ("table", [["N_A", "ALPHA"], ["N_B", "BRAVO"]], 2))
        self.assertEqual(packfiles.preview(self.game, "texts", (), "gen\\notes.txt")["text"], "Bonjour, été\n")
        blob = packfiles.preview(self.game, "texts", (), "gen\\blob.bin")
        self.assertEqual((blob["kind"], len(blob["lines"]), blob["more"]), ("bytes", 512, 10240 - 8192))
        self.assertTrue(blob["lines"][1].startswith("00000010  10 11 12"))
        self.assertEqual(packfiles.preview(self.game, "texts", (), "gen\\menu.ppk")["files"], 1)
        inner = packfiles.preview(self.game, "texts", ["gen\\menu.ppk"], "gen\\inner\\card.tgv")
        self.assertEqual((inner["kind"], inner["width"]), ("picture", 2))
        nd = packfiles.preview(self.game, "gameplay", (), "genglad\\everything.ndfbin")
        self.assertEqual((nd["kind"], nd["objects"], nd["classes"], nd["top"]), ("ndf", 3, 2, [("TUnit", 2), ("TWeapon", 1)]))
        with self.assertRaisesRegex(packfiles.PackFileError, "no gen"):
            packfiles.preview(self.game, "texts", (), "gen\\none.txt")

    def test_the_studio_s_calls(self):
        home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        out = home / "saved" / "menu-card.tgv"
        api = StudioApi(game_dir=self.game, home=home, instances=home / "copies", pick_save=lambda name: str(out))
        self.assertEqual(len(api.files_packs()["packs"]), 3)
        shown = api.files_preview("texts", ["gen\\menu.ppk"], "gen\\inner\\card.tgv")
        self.assertTrue(shown["picture"].startswith("data:image/png;base64,"))
        self.assertEqual(read_png(base64.b64decode(shown["picture"].split(",", 1)[1]))[:2], (2, 2))
        self.assertNotIn("png", shown)
        self.assertEqual(api.files_export("texts", ["gen\\menu.ppk"], "gen\\inner\\card.tgv"), {"saved": str(out)})
        self.assertEqual(out.read_bytes(), TEXTURE)
        self.assertEqual(StudioApi(game_dir=self.game, home=home, instances=home / "copies",
                                   pick_save=lambda name: None).files_export("texts", [], "gen\\flag.tgv"), {"saved": None})
        with self.assertRaisesRegex(StudioError, "isn't a pack"):
            api.files_list("texts", ["gen\\notes.txt"])

    def test_a_game_file_changed_and_added_in_a_mod(self):
        """His Import / Replace and Add File, the safe way (rusemod.gamefiles): a delta in the mod, never the game's
        file; checked as its kind; an added file only in the mod's own folder in the pack."""
        from rusemod import gamefiles
        home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        api = StudioApi(game_dir=self.game, home=home, instances=home / "copies")
        mine = Path(home, "mine.tgv")
        mine.write_bytes(make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(bytes([0, 255, 0, 255]) * 4)]))
        with self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
            api.files_change("texts", [], "gen\\flag.tgv", str(mine))
        api.new_mod("Painted")
        folder = home / "mods" / "painted"
        shown = api.files_change("texts", ["gen\\menu.ppk"], "gen\\inner\\card.tgv", str(mine))
        self.assertEqual((shown["changed"], shown["showing_mine"], shown["can_change"]), (True, True, True))
        self.assertEqual(read_png(base64.b64decode(shown["picture"].split(",", 1)[1]))[2][:4], bytes([0, 255, 0, 255]))
        delta = folder / "files" / "game" / "ZZ_Win.dat" / "gen" / "menu.ppk" / "gen" / "inner" / "card.tgv.rdelta"
        self.assertTrue(delta.is_file())
        self.assertNotIn(TEXTURE, delta.read_bytes())  # never the game's file
        self.assertEqual(gamefiles.apply_delta(TEXTURE, delta.read_bytes()), mine.read_bytes())
        game_side = api.files_preview("texts", ["gen\\menu.ppk"], "gen\\inner\\card.tgv")
        self.assertEqual((game_side["changed"], game_side["showing_mine"]), (True, False))
        self.assertEqual([f.get("mine") for f in api.files_list("texts", ["gen\\menu.ppk"])["files"]], ["changed"])
        notes = Path(home, "notes.txt")
        notes.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(StudioError, "can't be checked"):
            api.files_change("texts", [], "gen\\notes.txt", str(notes))
        self.assertEqual(api.files_preview("texts", [], "gen\\blob.bin")["can_change"], False)
        api.files_reset("texts", ["gen\\menu.ppk"], "gen\\inner\\card.tgv")
        self.assertFalse(delta.exists())
        listed = api.files_add("texts", "pictures/my_flag.tgv", str(mine))
        self.assertEqual(listed["files"][-1], {"path": "mods\\painted\\pictures\\my_flag.tgv", "kind": "texture",
                                               "size": mine.stat().st_size, "mine": "added"})
        self.assertEqual(api.files_preview("texts", [], "mods\\painted\\pictures\\my_flag.tgv")["added"], True)
        for name, why in (("../x.tgv", "Give the new file a name"), ("x.bik", "can't be checked"),
                          ("x.webm", "a video isn't offered yet")):
            with self.subTest(name=name), self.assertRaisesRegex(StudioError, why):
                api.files_add("texts", name, str(mine))
        self.assertEqual(api.files_change("texts", [], "gen\\flag.tgv"), {"cancelled": True})  # (no file picked)
        self.assertFalse((folder / "files" / "game" / "ZZ_Win.dat" / "gen" / "flag.tgv.rdelta").exists())
        from rusemod.build import load_mod
        self.assertEqual([(g.path, g.added) for g in load_mod(folder)[0].game_files],
                         [("mods/painted/pictures/my_flag.tgv", True)])


if __name__ == "__main__":
    unittest.main()
