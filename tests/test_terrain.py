"""The Studio's map view: the game's map list, a map's ground as packed buffers, the stitched ground picture, and the
Studio's calls for them, on a tiny made-up game folder (no game files)."""
import base64
import struct
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import zlib
from array import array
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from test_tmst import make_set
from test_tms import make_tms
from rusemod import dxt
from rusemod.dic import name_to_key
from rusemod.ndf import Ndf
from rusemod.terrain import ground_picture, map_list, maps_from_ndf, menu_keys, mesh_buffers, pack_file, terrain
from rusemod.tms import Tms
from rusemod.tmst import Tmst, dxt1_solid, rgb565, zipo_tile
from rusemod.webui import serve
from ruse_studio.api import StudioApi

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 24


def s(i):
    return val(0x07, struct.pack("<I", i))


def p(i):
    return val(0x1C, struct.pack("<I", i))


def g(i):
    return val(0x1A, bytes([i]) * 16)


def text_key(key):
    return val(0x1D, struct.pack("<Q", key))


# the menus' names for the made-up maps: a multiplayer map, a chapter and a challenge on "Test", one on "Missing"
MP, CHAPTER, CHALLENGE, GONE = (name_to_key(n) for n in ("M_D_01", "S_D_01", "C_D_01", "M_D_02"))


def map_list_ndf() -> bytes:
    """Four map entries (three on the pack "Test", one of them spelt "TEST"), one for a pack that isn't shipped, and
    an unrelated object."""
    strings = ["(6) Test map", "Test", "Test_chapter1", "Missing", "(2) Gone", "TEST", "(2) Test duel"]
    classes = ["TMapLoadInfo", "TSomethingElse"]
    props = [("Name", 0), ("Path", 0), ("RootDatapackName", 0), ("Other", 1), ("GUID", 0)]
    objects = [
        (0, [(0, s(0)), (1, p(1)), (2, s(1)), (4, g(1))]),
        (1, [(3, s(0))]),
        (0, [(0, s(2)), (1, p(2)), (2, s(1)), (4, g(2))]),
        (0, [(0, s(4)), (1, p(3)), (2, s(3)), (4, g(3))]),
        (0, [(0, s(6)), (1, p(1)), (2, s(5)), (4, g(4))]),
    ]
    return make_ndf(objects, classes, props, strings=strings)


def menus_ndf() -> bytes:
    """The menus' entries: a chapter (listed first), the multiplayer maps, a challenge, and an unrelated object."""
    classes = ["TChapterMapInfo", "TMultiMapInfo", "TChallengeMapInfo", "TOther"]
    props = [("GUID", 0), ("Description", 0), ("GUID", 1), ("Description", 1), ("GUID", 2), ("Description", 2),
             ("GUID", 3)]
    objects = [
        (0, [(0, g(2)), (1, text_key(CHAPTER))]),
        (1, [(2, g(1)), (3, text_key(MP))]),
        (2, [(4, g(4)), (5, text_key(CHALLENGE))]),
        (1, [(2, g(3)), (3, text_key(GONE))]),
        (3, [(6, g(1))]),
    ]
    return make_ndf(objects, classes, props)


def menu_texts_edat() -> bytes:
    us = make_dic([(MP, "Test Valley"), (CHAPTER, "1. FIRST  STEPS\n"), (CHALLENGE, "Duel at Dawn"), (GONE, "Gone")])
    fr = make_dic([(MP, "Vallée d'essai"), (CHAPTER, "1. PREMIERS PAS")])  # a text missing in one language
    return make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", "us\\", [("file", "flash_txt.dic", us)]), ("dir", "fr\\", [("file", "flash_txt.dic", fr)])])])


COLOURS = [rgb565(40 * i % 256, 255 - 20 * i, 90 + 10 * i) for i in range(11)]


def tile_set():
    """A 2 x 1 cell tile store whose every tile is a plain (ZIPO) 8 x 8 tile of its own colour."""
    return make_set([zipo_tile(dxt1_solid(c) * 4, 8, 8) for c in COLOURS])


def make_game(root: Path) -> Path:
    game = root / "R.U.S.E"
    core = game / "Data" / "PC" / "190852"
    core.mkdir(parents=True)
    (core / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\", [
        ("file", "mapinfo.cpp.gladndfbin", map_list_ndf()),
        ("dir", "misc\\", [("file", "globals.cpp.gladndfbin", menus_ndf())])])]))
    (core / "ZZ_Win.dat").write_bytes(menu_texts_edat())
    maps = game / "Maps" / "PC"
    maps.mkdir(parents=True)
    index, chunk = tile_set()
    (maps / pack_file("Test")).write_bytes(make_edat([("dir", "output\\", [
        ("file", "highdef.tms", make_tms(water_cell=(1, 0))),
        ("file", "highdef.tmst_chunk_pc", chunk),
        ("file", "highdef.tmst_pc", index),
        ("file", "lowdef.tms", make_tms(1, 1, 5)),
        ("file", "terrain.png", PNG),
    ])]))
    return game


def unpack(b64: str, code: str) -> list:
    a = array(code)
    a.frombytes(zlib.decompress(base64.b64decode(b64)))
    return a.tolist()


class MapList(unittest.TestCase):
    def test_entries_grouped_by_pack_in_the_game_order(self):
        maps = maps_from_ndf(Ndf(map_list_ndf()))
        self.assertEqual(maps, [
            {"pack": "Test", "names": ["(6) Test map", "Test_chapter1", "(2) Test duel"],
             "paths": ["Test", "Test_chapter1"], "keys": []},
            {"pack": "Missing", "names": ["(2) Gone"], "paths": ["Missing"], "keys": []},
        ])
        self.assertEqual(pack_file("Test"), "DataMapTest_v09.dat")

    def test_the_menus_names_best_first(self):
        menus = menu_keys(Ndf(menus_ndf()))
        self.assertEqual(menus[bytes([2]) * 16], [(1, CHAPTER)])
        maps = maps_from_ndf(Ndf(map_list_ndf()), menus)
        # the multiplayer map's name first, though the chapter comes first in the file; then the challenge
        self.assertEqual([m["keys"] for m in maps], [[MP, CHAPTER, CHALLENGE], [GONE]])


class Ground(unittest.TestCase):
    def test_mesh_buffers_hold_every_cell(self):
        raw = make_tms(water_cell=(1, 0))
        tms = Tms(raw)
        view = mesh_buffers(tms)
        pos = unpack(view["positions"], "H")
        tri = unpack(view["triangles"], "I")
        wat = unpack(view["water"], "I")
        heights = unpack(view["water_heights"], "H")
        normals = unpack(view["normals"], "B")
        cells = tms.cells
        self.assertEqual(view["vertices"], sum(c.vcount for c in cells))
        self.assertEqual(len(pos), 3 * view["vertices"])
        self.assertEqual(view["triangle_count"], sum(len(c.triangles(0)) for c in cells) // 3)
        self.assertEqual(pos[:3], list(cells[0].positions()[0][:3]))
        self.assertEqual(normals[:3], [128, 128, 255])
        second = cells[0].vcount  # cell 1's vertex numbers come after cell 0's
        self.assertEqual(tri[len(cells[0].triangles(0))], second + cells[1].triangles(0)[0])
        self.assertEqual(len(wat), len(cells[1].triangles(1)))
        self.assertTrue(all(second <= v < second + cells[1].vcount for v in wat))
        self.assertEqual(heights[second], 500)
        self.assertEqual(view["bounds"], list(tms.bounds))


class OnAGameFolder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = make_game(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_map_list_says_which_packs_are_there(self):
        maps = map_list(self.game)
        self.assertEqual([(m["pack"], m["found"], m["file"]) for m in maps],
                         [("Test", True, "DataMapTest_v09.dat"), ("Missing", False, "DataMapMissing_v09.dat")])

    def test_map_list_has_what_the_menus_call_each_map_in_each_language(self):
        maps = map_list(self.game)
        self.assertEqual(maps[0]["titles"], {"us": ["Test Valley", "1. FIRST STEPS", "Duel at Dawn"],
                                             "fr": ["Vallée d'essai", "1. PREMIERS PAS"]})
        self.assertEqual(maps[1]["titles"], {"us": ["Gone"], "fr": []})
        self.assertNotIn("keys", maps[0])

    def test_terrain_view(self):
        view = terrain(self.game, "Test", "lowdef")
        self.assertEqual((view["pack"], view["lod"], view["vertices"]), ("Test", "lowdef", 25))
        self.assertTrue(view["picture"].startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(view["picture"].split(",", 1)[1]), PNG)
        with self.assertRaises(ValueError):
            terrain(self.game, "Test", "ultra")
        with self.assertRaises(FileNotFoundError):
            terrain(self.game, "Missing")

    def test_ground_picture_puts_each_tile_in_its_place(self):
        seen = []
        width, height, rgb = ground_picture(self.game, "Test", progress=lambda d, n: seen.append((d, n)))
        self.assertEqual((width, height), (16, 8))  # the level with one tile per cell: 2 x 1 tiles of 8 x 8
        self.assertEqual(seen, [(1, 2), (2, 2)])
        index, chunk = tile_set()
        store = Tmst(index, chunk)
        for x in (0, 1):
            tile = store.tile(store.depth - 1, x, 0)
            colour = COLOURS[tile.index]
            expected = bytes(dxt.decode(dxt1_solid(colour), 4, 4)[:3])
            for px, py in ((x * 8, 0), (x * 8 + 7, 7)):
                at = (py * width + px) * 3
                self.assertEqual(rgb[at:at + 3], expected, (x, px, py))
        w0, h0, _ = ground_picture(self.game, "Test", level=0)
        self.assertEqual((w0, h0), (32, 16))

    def test_the_studio_shows_maps_and_makes_the_ground_picture_once(self):
        api = StudioApi(game_dir=self.game, home=self.root / "home", index_path=self.root / "none.sqlite")
        self.assertEqual([m["pack"] for m in api.maps()["maps"]], ["Test"])  # packs that aren't there aren't listed
        first = api.map_view("Test")
        self.assertIs(api.map_view("Test"), first)  # kept: switching back is instant
        self.assertEqual(api.map_view("Test", "highdef")["lod"], "highdef")
        started = api.map_ground("Test")
        self.assertIn("job", started)
        for _ in range(200):
            view = api.job(started["job"])
            if view["state"] != "running":
                break
            time.sleep(0.02)
        self.assertEqual(view["state"], "done", view)
        self.assertEqual(view["lines"], ["1/2", "2/2"])
        ready = api.map_ground("Test")
        self.assertTrue(ready["url"].startswith("cache/ground/Test-"))
        picture = api.cache_dir / ready["url"][len("cache/"):]
        self.assertEqual(picture.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


class ServingMadeFiles(unittest.TestCase):
    def test_extra_folder_is_served_and_nothing_outside_it(self):
        with tempfile.TemporaryDirectory() as d:
            ui, cache = Path(d, "ui"), Path(d, "cache")
            ui.mkdir()
            (cache / "ground").mkdir(parents=True)
            (ui / "index.html").write_text("page")
            (cache / "ground" / "a.png").write_bytes(b"picture")
            Path(d, "secret.txt").write_text("secret")
            server, base = serve(ui, {"cache": cache})
            try:
                def get(path):
                    with urllib.request.urlopen(base + path, timeout=10) as r:
                        return r.read()
                self.assertEqual(get("/index.html"), b"page")
                self.assertEqual(get("/cache/ground/a.png"), b"picture")
                for bad in ("/cache/../secret.txt", "/cache/%2e%2e/secret.txt", "/cache/ground/../../secret.txt"):
                    with self.assertRaises(urllib.error.HTTPError, msg=bad) as caught:
                        get(bad)
                    self.assertEqual(caught.exception.code, 404, bad)
                    caught.exception.close()
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
