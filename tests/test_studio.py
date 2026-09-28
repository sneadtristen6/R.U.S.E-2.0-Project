"""The Studio's back end (rusemod.studio.api) and the display names (rusemod.schema), on a made-up game."""
import os
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import schema
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.studio.api import StudioApi

SHERMAN, PANZER = name_to_key("SHERMAN"), name_to_key("PANZER")


def i32(v):
    return val(0x02, struct.pack("<i", v))


def key(k):
    return val(0x1D, struct.pack("<Q", k))


def ref(i, cls=0):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


# classes: 0 TUniteAuSolDescriptor, 1 TInfanterieDescriptor, 2 TBatimentDescriptor, 3 TWeapon, 4 TAmmunition
UNITS = make_ndf(
    objects=[(0, [(0, lst(i32(30), i32(35))), (1, i32(12)), (2, key(SHERMAN)), (3, i32(10)), (4, ref(4, 3))]),  # 0 M4
             (0, [(0, lst(i32(45), i32(45))), (5, i32(1)), (2, key(PANZER)), (3, i32(10)), (4, ref(5, 3))]),  # 1 Panzer
             (1, [(6, i32(4))]),                                                                          # 2 infantry
             (2, [(7, lst(i32(20)))]),                                                                    # 3 depot
             (3, [(8, ref(6, 4))]),                                                                       # 4 M4 gun
             (3, [(8, ref(6, 4))]),                                                                       # 5 Panzer gun
             (4, [(9, i32(40))])],                                                                        # 6 shared ammo
    classes=["TUniteAuSolDescriptor", "TInfanterieDescriptor", "TBatimentDescriptor", "TWeapon", "TAmmunition"],
    props=[("ProductionPrice", 0), ("SeuilMort", 0), ("NameInMenuToken", 0), ("Factory", 0), ("Weapon", 0),
           ("Nationalite", 0), ("SeuilMort", 1), ("ProductionPrice", 2), ("Ammo", 3), ("Puissance", 4)],
    exports={0: "GFX/Everything/Descriptor_Unit_M4_Sherman", 1: "GFX/Everything/Descriptor_Unit_Panzer_IV_G",
             2: "GFX/Everything/Descriptor_Unit_Soldat_US_Leger", 3: "GFX/Everything/Descriptor_Building_Depot"},
    topo=[0, 1, 2, 3])


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "everything.cpp.gladndfbin", UNITS)]))
    texts = {"us": [(SHERMAN, "M4 Sherman"), (PANZER, "Panzer IV")],
             "fr": [(SHERMAN, "M4 Sherman (fr)"), (PANZER, "Panzer IV (fr)")]}
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", f"{lang}\\", [("file", "baseunite.dic", make_dic(items))]) for lang, items in texts.items()])]))


class Studio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)
        cls.api = StudioApi(index_path=cls.index, game_dir=cls.game)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_status_languages_and_words(self):
        self.assertTrue(self.api.status()["ready"])
        self.assertEqual([lang["code"] for lang in self.api.languages()], ["base"] + list(schema.LANGS))
        self.assertEqual(self.api.strings("fr")["search"], "Rechercher")
        self.assertEqual(self.api.strings("base")["search"], "Search")  # the tool's words fall back to English
        self.assertEqual(self.api.nations("ru")[5], "СССР")

    def test_units_in_game_names_and_in_a_language(self):
        base = self.api.units()
        self.assertEqual(base["total"], 4)
        self.assertEqual([u["name"] for u in base["units"]],
                         ["Descriptor_Building_Depot", "Descriptor_Unit_M4_Sherman", "Descriptor_Unit_Panzer_IV_G",
                          "Descriptor_Unit_Soldat_US_Leger"])
        fr = {u["base_name"]: (u["name"], u["nation_name"]) for u in self.api.units("fr")["units"]}
        self.assertEqual(fr["Descriptor_Unit_M4_Sherman"], ("M4 Sherman (fr)", "États-Unis"))
        self.assertEqual(fr["Descriptor_Unit_Panzer_IV_G"], ("Panzer IV (fr)", "Allemagne"))
        self.assertEqual([u["kind"] for u in self.api.units(kind="infantry")["units"]], ["infantry"])
        self.assertEqual([u["base_name"] for u in self.api.units(nation=1)["units"]], ["Descriptor_Unit_Panzer_IV_G"])
        self.assertEqual([u["name"] for u in self.api.units("us", search="sherman")["units"]], ["M4 Sherman"])

    def test_one_unit(self):
        u = self.api.unit("$/GFX/Everything/Descriptor_Unit_M4_Sherman", "fr")
        self.assertEqual(u["name"], "M4 Sherman (fr)")
        rows = {r["prop"]: r for g in u["groups"] for r in g["rows"]}
        self.assertEqual(rows["ProductionPrice"]["values"], ["30", "35"])
        self.assertEqual(rows["ProductionPrice"]["label"], "Prix")
        self.assertEqual(rows["Nationalite"]["values"], ["0 (États-Unis)"])  # not written: 0
        self.assertEqual(rows["NameInMenuToken"]["values"], ["SHERMAN (M4 Sherman (fr))"])
        self.assertEqual([g["key"] for g in u["groups"]], ["identity", "cost", "combat", "menu"])  # references show as parts
        self.assertEqual([(p["class"], p["shared"]) for p in u["parts"]], [("TWeapon", False), ("TAmmunition", True)])
        base = self.api.unit("$/GFX/Everything/Descriptor_Unit_M4_Sherman")
        rows = {r["prop"]: r for g in base["groups"] for r in g["rows"]}
        self.assertEqual((base["name"], rows["ProductionPrice"]["label"]), ("Descriptor_Unit_M4_Sherman", "ProductionPrice"))

    def test_no_index_yet_then_built_from_the_studio(self):
        missing = Path(self.tmp.name, "later.sqlite")
        api = StudioApi(index_path=missing, game_dir=self.game)
        self.assertEqual(api.status(), {"ready": False, "can_build": True})
        job = api.build_index()["job"]
        end = time.time() + 20
        while api.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.05)
        self.assertEqual(api.job(job)["state"], "done", api.job(job))
        self.assertTrue(api.status()["ready"])
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RUSE_GAME", None)
            nothing = StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None)
            self.assertEqual(nothing.status(), {"ready": False, "can_build": False})  # no game: nothing to build from


class Labels(unittest.TestCase):
    """Every display name has all ten languages, so no modder gets a half-translated tool."""

    def test_complete(self):
        data = schema._data()
        for section in ("props", "groups", "ui"):
            for name, entry in data[section].items():
                missing = [lang for lang in schema.LANGS if not entry.get(lang)]
                self.assertEqual(missing, [], f"{section}.{name}")
        for name, entry in data["props"].items():
            self.assertIn(entry["group"], schema.GROUP_ORDER, name)
        for lang, names in data["nations"].items():
            self.assertEqual(len(names), 7, lang)
        self.assertEqual(schema.label("ProductionPrice[2]", "fr"), "Prix [2]")
        self.assertEqual(schema.label("NotTranslated", "fr"), "NotTranslated")
        self.assertEqual(schema.label("SeuilMort"), "SeuilMort")  # the game's names by default


if __name__ == "__main__":
    unittest.main()
