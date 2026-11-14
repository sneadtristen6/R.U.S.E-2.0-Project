"""The made-up game the maps scenario tests (tests/test_scenarios_maps*.py) run on, and their helpers; no test of its
own. It is test_studio's WithMod (a Studio on its made-up game, a fresh home per test, a game that only pretends to
start) with test_newmap's made-up map added to that game: Blitz (pack SuperCrossRoads4) with its map-list entry, its
BATTLES entry, its scenario, grid, constants and map pack, and its name in the menus, here in all ten of the game's
languages. The game's program file is the one WithMod writes; nothing here names it.

Each scenario drives the Studio through the calls its page makes (ruse_studio.api.StudioApi), then checks what the
player is told, the map's files, and whether the map still builds (Test in game on this made-up game: the build
runs, the game only pretends to start).

FOR: the overnight scenario tests of making map mods in the Studio (owner, 2026-11-13: "Usual and unusual situations
[a] player can find themselves in when making new mods in our apps"). USED-BY: tests/test_scenarios_maps*.py."""
import os
import struct
import time
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat
from test_dic import make_dic
from test_newmap import PACK_ID, data_files, flat_pack, glad_files, map_pack
from test_scenery import unit_pack_raw, village
from test_studio import WithMod
from rusemod import loc, schema
from rusemod.dic import Dic, name_to_key
from rusemod.edat import Edat
from rusemod.index import build_index

BLITZ = "SuperCrossRoads4"          # the made-up map's pack name; the menus call it Blitz
BATTLES_ENTRY = "(2) Blitz"         # its one BATTLES entry
LANGS = loc.LANGS                   # the game's ten languages
APP_LANGS = schema.APP_LANGS        # the apps' languages (the game's ten and Persian)


def page_said(api, call: str, *args, **kwargs) -> str:
    """What the page is told when it calls `call`: the error's words as the window hands them to the page (through
    rusemod.webui.page_api, the object the window gives the page), or "" when the call goes through."""
    from rusemod.webui import page_api
    try:
        getattr(page_api(api), call)(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001  (whatever the page would get)
        return str(exc)
    return ""


def members(path: Path) -> dict:
    """Every member of a pack: {its path: bytes}."""
    arc = Edat(path.read_bytes())
    return {e.path: bytes(arc.read(e)) for e in arc.entries}


def menu_texts() -> dict:
    """The menus' texts (flash_txt) in all ten languages: test_newmap's two map names (M_D_01 Blitz, M_D_08 Other)."""
    return {loc.member("flash_txt", lang): make_dic([(name_to_key("M_D_01"), "Blitz"), (name_to_key("M_D_08"), "Other")])
            for lang in LANGS}


def level_state(bounds) -> bytes:
    """A level-build state database (output.sdb) laid like test_statedb's (4 x 4 cells, every one land) over the
    map's ground `bounds` (x0, y0, x1, y1): the made-up pack's own isn't one the build can read, and a blank start
    drains the map, which redraws it."""
    from test_statedb import LAND, leaf
    from ruse_mod_engine import sdb
    x0, y0, x1, y1 = bounds
    root_at = 0x20
    prefix = struct.pack("<4ffIII", x0, y0, x1, y1, max(x1 - x0, y1 - y0) / 4, 0, 0, root_at)
    return sdb.serialize({"ver": 2, "prefix": prefix, "node_start": root_at,
                          "nodes": [[leaf(LAND, LAND, LAND, LAND)] * 4], "tail": b""})


def village_map_pack() -> bytes:
    """test_newmap's made-up map pack with test_scenery's village on it (a town hall at (1000, 2000), four oaks), so
    the map has types to place: TypeWarrior/MairieNormande (a building) and TypeWarrior/Chene_02 (a tree); and a
    level-build state the build can read (level_state)."""
    from rusemod.tms import Tms
    arc = Edat(map_pack())
    files = {e.path: bytes(arc.read(e)) for e in arc.entries}
    files["output\\save.boobspc"] = village()
    b = Tms(files["output\\highdef.tms"]).bounds
    files["output\\output.sdb"] = level_state((b[0], b[1], b[3], b[4]))
    raw = bytearray(make_edat([("dir", "output\\", [("file", m.split("\\")[-1], d) for m, d in files.items()])]))
    raw[8:24] = PACK_ID
    return bytes(raw)


HALL, OAK = "TypeWarrior/MairieNormande", "TypeWarrior/Chene_02"   # the village's two types


def map_data_files() -> dict:
    """test_newmap's DataMap_Win.dat members (the scenario and the grid), the grid's cover layer test_cover's own
    (an 8 x 8 cell grid over the grid's 16000 x 16000: a wood in a corner, a blocked corner, the rest open) instead of
    the placeholder test_scenario's grid carries, so the steps that paint cover can read it."""
    import test_cover
    from test_newmap import GRID
    from ruse_mod_engine import sdb
    files = data_files()
    cover_layer = sdb.split_mapinfo(test_cover.mapinfo((0.0, 0.0, 16000.0, 16000.0)))[1][3]
    files[GRID] = sdb.replace_buffer4(files[GRID], cover_layer)
    return files


class MapGame(WithMod):
    """WithMod's Studio on its made-up game, with test_newmap's made-up map in that game (see the module's words)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        rev = cls.game / "Data" / "PC" / "190852"
        scenery_types = {e.path: bytes(Edat(unit_pack_raw()).read(e)) for e in Edat(unit_pack_raw()).entries}
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(flat_pack({**members(rev / "ZZ_GladPatchableWin.dat"),
                                                                 **glad_files(), **scenery_types}))
        (rev / "ZZ_Win.dat").write_bytes(flat_pack({**members(rev / "ZZ_Win.dat"), **menu_texts()}))
        (rev / "DataMap_Win.dat").write_bytes(flat_pack(map_data_files()))
        (cls.game / "Maps" / "PC").mkdir(parents=True, exist_ok=True)
        (cls.game / "Maps" / "PC" / "DataMapSuperCrossroads4_v09.dat").write_bytes(village_map_pack())
        cls.game_files = {p.relative_to(cls.game).as_posix(): p.read_bytes() for p in cls.game.rglob("*") if p.is_file()}
        cls.index = build_index(cls.game, Path(cls.tmp.name, "maps-index.sqlite"), say=lambda line: None)

    def setUp(self):
        env = mock.patch.dict(os.environ, {}, clear=False)  # the real game never stands in for the made-up one
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("RUSE_GAME", None)
        super().setUp()
        # the build's cache in this test's own home (as test_sound's builds have it): no test reads another's
        os.environ["RUSE_PLATFORM_HOME"] = str(self.home)

    # --- what the page does after a call ---
    def wait(self, job_id: str, timeout: float = 120.0) -> dict:
        end = time.time() + timeout
        while time.time() < end:
            got = self.api.job(job_id)
            if got["state"] != "running":
                return got
            time.sleep(0.02)
        self.fail(f"job {job_id} never ended: {self.api.job(job_id)}")

    def build(self) -> dict:
        """Test in game, as the page's button does it: the job's end ({"state", "message", "lines", "errors"...})."""
        return self.wait(self.api.test_in_game()["job"])

    def assertBuilds(self, msg: str = "") -> dict:
        got = self.build()
        self.assertEqual(got["state"], "done", f"{msg}\n" + "\n".join(got.get("lines", [])) + f"\n{got}")
        return got

    def copy(self) -> Path:
        """The one modded copy Test in game builds."""
        return self.home / "copies" / "Modded game"

    def copy_pack(self, *parts) -> Edat:
        return Edat(self.copy().joinpath(*parts).read_bytes())

    def copy_texts(self, lang: str = "us") -> Dic:
        zz = self.copy_pack("Data", "PC", "190852", "ZZ_Win.dat")
        return Dic(bytes(zz.read(zz.entry(loc.member("flash_txt", lang)))))

    def game_untouched(self):
        """The game folder as it was made: no file changed, none added, none taken away."""
        now = {p.relative_to(self.game).as_posix(): p.read_bytes() for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(sorted(now), sorted(self.game_files))
        self.assertEqual([k for k in now if now[k] != self.game_files[k]], [])

    # --- the map project and its maps ---
    def map_dir(self) -> Path:
        return self.api._map_dir()

    def map_folder(self, pack: str) -> Path:
        return self.map_dir() / "maps" / pack

    def toml(self, pack: str, name: str = "map.toml") -> dict:
        return tomllib.loads((self.map_folder(pack) / name).read_text(encoding="utf-8"))

    def listed(self) -> list:
        return [m["pack"] for m in self.api.maps()["maps"]]

    def in_lang(self, lang: str):
        """The Studio's language set as the page's language menu sets it."""
        self.api.set_pref("lang", lang)


if __name__ == "__main__":
    unittest.main()
