"""The made-up game the maps scenario tests (tests/test_scenarios_maps*.py) run on, and their helpers; no test of its
own. It is test_studio's WithMod (a Studio on its made-up game, a fresh home per test, a game that only pretends to
start) with test_newmap's made-up map added to that game: Blitz (pack SuperCrossRoads4) with its map-list entry, its
BATTLES entry, its scenario, grid, constants and map pack, and its name in the menus, here in all ten of the game's
languages; on its ground test_scenery's village (a town hall and oaks, so it has types to place), and a cover grid
(test_cover's) and a level-build state (test_statedb's way) the build can read. OperationGame offers Blitz as an
Operation with a mission of its own to copy. The game's program file is the one WithMod writes; nothing here names it.

What this made-up game can't show (the real install's dry builds do): a map made bigger (it has no far-view files to
grow), the RUSE Guard scripts (no Battles launcher script; switched off where IA_Common.dat is in it), the units' class
names and the nations' packs a mission's units need.

Each scenario drives the Studio through the calls its page makes (ruse_studio.api.StudioApi), then checks what the
player is told, the map's files, and whether the map still builds (Test in game on this made-up game: the build
runs, the game only pretends to start).

FOR: the overnight scenario tests of making map mods in the Studio (owner, 2026-11-13: "Usual and unusual situations
[a] player can find themselves in when making new mods in our apps"). USED-BY: tests/test_scenarios_maps*.py."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
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


MISSION_FOLDER = "scripting_challenge"   # the copied Operation's script folder, as Anzio's is called
MISSION_MEMBER = "genpython\\1000\\test\\map\\supercrossroads4\\scripting_challenge\\effetmap.xyz"
NAMED = "datadir:\\test\\map\\supercrossroads4\\scripting_challenge\\effetmap.py"


def copied_mission() -> bytes:
    """The made-up Operation's own mission script (.xyz, as the game keeps it in IA_Common.dat), written with the
    Studio's own script writer (rusemod.missionscript): two sides, side 0 played by a person (the US), side 1 by the
    computer (Germany), and a wait as its whole mission."""
    import hashlib
    from rusemod.missionscript import Attr, Ref, assemble, call, source
    from rusemod.pyscript import Xyz, write_xyz
    e = "_enum_for_game_play"
    imports = [e, "leveldesign.camps", "leveldesign.descriptor", "leveldesign.launcheffetmap"]
    defs = [("P", call("leveldesign.camps.VariableCamp", Alliance=1, NiveauIA=Attr(f"{e}.NiveauIA.Player"),
                       Nationalite=Attr(f"{e}.Nationalite.EU"), CampNumber=-1)),
            ("C", call("leveldesign.camps.VariableCamp", Alliance=2, NiveauIA=Attr(f"{e}.NiveauIA.Scripted"),
                       Nationalite=Attr(f"{e}.Nationalite.Allemagne"), CampNumber=-1)),
            ("W", call("leveldesign.descriptor.DescriptorWaitDuree", Duree=2.5)),
            ("ER", call("leveldesign.launcheffetmap.DescriptorLaunchEffetMap", CampList=[Ref("P"), Ref("C")],
                        CampaignInfo=None, EffetMap=Ref("W"), GameRules=None, MapChapterPos=None, PostInit=[],
                        TagList=[], UnitToSpawnList=[], GameMode=Attr(f"{e}.TGameTimerMode.Clock")))]
    text = source(imports, defs, "ER")
    return write_xyz(Xyz(hashlib.md5(text.encode("latin-1")).digest(), assemble(imports, defs, "ER", NAMED)))


def operation_globals() -> bytes:
    """test_newmap.menu_globals' Operation menu (Blitz's entry and another in a TChallengePack's ChallengeList), with
    what the game's own has round it: the pack's PackGUID and the TChallengePackManager listing the pack (a mission
    of the mod's own goes in a pack of its own there: rusemod.missionbuild.own_packs)."""
    from fixtures import make_ndf, val
    from test_newmap import GUID_BLITZ, GUID_OTHER, i32, key, ref, s
    return make_ndf(
        objects=[(0, [(0, key("M_D_01")), (1, val(0x1A, GUID_BLITZ)), (2, s(0)), (3, i32(1))]),
                 (0, [(0, key("M_D_08")), (1, val(0x1A, GUID_OTHER)), (2, s(1)), (3, i32(1))]),
                 (1, [(4, val(0x11, struct.pack("<I", 2) + ref(0, 0) + ref(1, 0))), (5, val(0x1A, bytes(range(48, 64))))]),
                 (2, [(6, val(0x11, struct.pack("<I", 1) + ref(2, 1)))])],
        classes=["TChallengeMapInfo", "TChallengePack", "TChallengePackManager"],
        props=[("Description", 0), ("GUID", 0), ("TrackingId", 0), ("CategoryId", 0), ("ChallengeList", 1),
               ("PackGUID", 1), ("ChallengePackList", 2)],
        strings=["CH26", "X99"], topo=[2, 3], compress=True)


class OperationGame(MapGame):
    """MapGame with Blitz offered as an Operation instead of a BATTLES map (operation_globals), its mission there to
    copy: the scenario cluster names the mission's folder and text file, IA_Common.dat holds its script
    (copied_mission), ZZ_Win.dat its text files in English and French. The Scenario side's Mission trays work on a
    copy of it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_newmap import SCENARIO_CLUSTER
        from rusemod.ndf import Ndf
        from rusemod.players import GLOBALS
        rev = cls.game / "Data" / "PC" / "190852"
        glad = members(rev / "ZZ_GladPatchableWin.dat")
        glad[GLOBALS] = operation_globals()
        cluster = Ndf(glad[SCENARIO_CLUSTER])
        cluster.add_string("DataDir:\\Test\\map\\SuperCrossRoads4\\" + MISSION_FOLDER)
        cluster.add_string("SuperCrossRoads4\\" + MISSION_FOLDER + "\\Localization.csv")
        glad[SCENARIO_CLUSTER] = cluster.to_member(compress=True)
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(flat_pack(glad))
        (rev / "IA_Common.dat").write_bytes(flat_pack({MISSION_MEMBER: copied_mission()}))
        texts = {f"genlocalisation\\ww2\\localisation\\translations\\{lang}\\map\\supercrossroads4\\{MISSION_FOLDER}"
                 f"\\localization.dic": make_dic([(name_to_key("SIDE_NAME"), f"Side ({lang})")]) for lang in ("us", "fr")}
        (rev / "ZZ_Win.dat").write_bytes(flat_pack({**members(rev / "ZZ_Win.dat"), **texts}))
        cls.game_files = {p.relative_to(cls.game).as_posix(): p.read_bytes() for p in cls.game.rglob("*") if p.is_file()}
        cls.index = build_index(cls.game, Path(cls.tmp.name, "op-index.sqlite"), say=lambda line: None)

    def setUp(self):
        super().setUp()
        # RUSE Guard's scripts switched off, as test_fairplay's Off does: with IA_Common.dat in it, the build would add
        # them after the game's own Battles launcher, which this made-up game hasn't got
        from rusemod import fairplay
        off = mock.patch.object(fairplay, "ON", False)
        off.start()
        self.addCleanup(off.stop)


if __name__ == "__main__":
    unittest.main()
