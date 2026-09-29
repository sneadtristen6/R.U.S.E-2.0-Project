"""The Studio app's back end (ruse_studio.api) and the display names (rusemod.schema), on a made-up game."""
import os
import re
import struct
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat, Ndf, schema
from rusemod.build import build_pack, load_mod
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError, _short, _words
from ruse_studio.edits import EditsFileError, ModEdits, number

SHERMAN, PANZER = name_to_key("SHERMAN"), name_to_key("PANZER")


def i32(v):
    return val(0x02, struct.pack("<i", v))


def key(k):
    return val(0x1D, struct.pack("<Q", k))


def ref(i, cls=0):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def flag(v):
    return val(0x00, struct.pack("<B", v))


# classes: 0 TUniteAuSolDescriptor, 1 TInfanterieDescriptor, 2 TBatimentDescriptor, 3 TWeapon, 4 TAmmunition
UNITS = make_ndf(
    objects=[(0, [(0, lst(i32(30), i32(35))), (1, i32(12)), (2, key(SHERMAN)), (3, i32(10)), (4, ref(4, 3))]),  # 0 M4
             (0, [(0, lst(i32(45), i32(45))), (5, i32(1)), (2, key(PANZER)), (3, i32(10)), (4, ref(5, 3))]),  # 1 Panzer
             (1, [(6, i32(4))]),                                                                          # 2 infantry
             (2, [(7, lst(i32(20)))]),                                                                    # 3 depot
             (3, [(8, ref(6, 4)), (10, i32(2500)), (11, f32(0.1)), (12, flag(1))]),                       # 4 M4 gun
             (3, [(8, ref(6, 4))]),                                                                       # 5 Panzer gun
             (4, [(9, i32(40))])],                                                                        # 6 shared ammo
    classes=["TUniteAuSolDescriptor", "TInfanterieDescriptor", "TBatimentDescriptor", "TWeapon", "TAmmunition"],
    props=[("ProductionPrice", 0), ("SeuilMort", 0), ("NameInMenuToken", 0), ("Factory", 0), ("Weapon", 0),
           ("Nationalite", 0), ("SeuilMort", 1), ("ProductionPrice", 2), ("Ammo", 3), ("Puissance", 4),
           ("PorteeMaximale", 3), ("TempsEntreDeuxTirs", 3), ("TirEnMouvement", 3)],
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
        cls.api = StudioApi(index_path=cls.index, game_dir=cls.game, home=Path(cls.tmp.name, "home"))

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
            nothing = StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None,
                                home=Path(self.tmp.name, "empty-home"))  # no game folder picked by hand either
            self.assertEqual(nothing.status(), {"ready": False, "can_build": False})  # no game: nothing to build from


M4 = "$/GFX/Everything/Descriptor_Unit_M4_Sherman"
PANZER_IV, DEPOT = "$/GFX/Everything/Descriptor_Unit_Panzer_IV_G", "$/GFX/Everything/Descriptor_Building_Depot"
M4_GUN, AMMO = M4 + ":Weapon", M4 + ":Weapon.Ammo"  # the ammo is shared with the Panzer's gun


class Editing(unittest.TestCase):
    """Changing a unit's numbers in place: saved in the mod's src/studio.rndf, read back, built into the game data."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        (cls.game / "RUSE.exe").write_bytes(b"MZ")
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.started = []
        self.api = self.studio()

    def studio(self):
        starter = Starter(open_url=lambda url: None, start_game=self.started.append, steam_running=lambda: True,
                          wait=lambda s: None)
        return StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                         instances=self.home / "copies")

    def rows(self, address):
        return {r["prop"]: r for g in self.api.unit(address)["groups"] for r in g["rows"]}

    def test_changes_are_saved_in_the_mod_and_read_back(self):
        self.assertEqual(self.api.mods(), {"mods": [], "current": None})
        with self.assertRaises(StudioError):
            self.api.edit(M4, "SeuilMort", 15)  # no mod to save it in yet
        mods = self.api.new_mod("Tank Test")
        folder = self.home / "mods" / "tank-test"
        self.assertEqual(mods, {"mods": [{"path": str(folder), "name": "tank-test"}], "current": str(folder)})
        self.assertIn('name        = "Tank Test"', (folder / "mod.toml").read_text(encoding="utf-8"))

        self.assertEqual(self.api.edit(M4, "SeuilMort", 15)["value"], 15)
        self.assertEqual(self.api.edit(M4, "ProductionPrice", [25.4, 30.5])["value"], [25, 31])  # whole numbers
        self.assertEqual(self.api.edit(M4_GUN, "TempsEntreDeuxTirs", 0.25)["value"], 0.25)
        saved = self.api.edit(M4_GUN, "TirEnMouvement", 0)
        self.assertEqual(saved["saved"], str(folder / "src" / "studio.rndf"))
        self.assertEqual((folder / "src" / "studio.rndf").read_text(encoding="utf-8"), (
            "// Made by the RUSE Studio, which rewrites this file after every change.\n"
            "// Hand-written changes belong in other .rndf files in src/.\n"
            "\npatch $/GFX/Everything/Descriptor_Unit_M4_Sherman\n(\n"
            "    ProductionPrice = [25, 31]\n    SeuilMort = 15\n)\n"
            "\npatch $/GFX/Everything/Descriptor_Unit_M4_Sherman:Weapon\n(\n"
            "    TempsEntreDeuxTirs = 0.25\n    TirEnMouvement = 0\n)\n"))

        rows = self.rows(M4)
        self.assertEqual((rows["SeuilMort"]["values"], rows["SeuilMort"]["edited"]), (["12"], 15))
        self.assertEqual(rows["ProductionPrice"]["edited"], [25, 31])
        self.assertEqual((rows["ProductionPrice"]["list"], rows["ProductionPrice"]["type"]), (True, "int32"))
        self.assertTrue(rows["SeuilMort"]["editable"])
        self.assertFalse(rows["NameInMenuToken"]["editable"])  # a text key
        self.assertEqual((rows["Nationalite"]["editable"], rows["Nationalite"]["locked"]), (False, True))
        gun = self.rows(M4_GUN)
        self.assertEqual((gun["TempsEntreDeuxTirs"]["numbers"], gun["TempsEntreDeuxTirs"]["values"]), ([0.1], ["0.1"]))
        self.assertEqual([gun[p]["type"] for p in ("PorteeMaximale", "TempsEntreDeuxTirs", "TirEnMouvement")],
                         ["int32", "float32", "bool"])
        self.assertEqual(self.api.edited(), [M4])

        again = self.studio()  # the Studio opened again: same mod, same changes, from the file
        self.assertEqual(again.mods()["current"], str(folder))
        self.assertEqual({r["prop"]: r["edited"] for g in again.unit(M4)["groups"] for r in g["rows"]
                          if r["edited"] is not None}, {"SeuilMort": 15, "ProductionPrice": [25, 31]})

        self.api.edit(M4, "SeuilMort", 12)  # the game's own value again: no change left to save
        self.api.reset(M4, "ProductionPrice")
        self.assertEqual((self.rows(M4)["SeuilMort"]["edited"], self.rows(M4)["ProductionPrice"]["edited"]), (None, None))
        self.assertNotIn("Descriptor_Unit_M4_Sherman\n", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        self.assertEqual(self.api.edited(), [M4])  # its gun still has changes

    def test_what_cant_be_edited(self):
        self.api.new_mod("x")
        for address, prop, value in [(M4, "NameInMenuToken", 3),                       # a text key
                                     ("$/GFX/Everything/Descriptor_Unit_Panzer_IV_G", "Nationalite", 0),  # locked
                                     (AMMO, "Puissance", 50),                           # shared with the Panzer
                                     (M4, "ProductionPrice", 5), (M4, "ProductionPrice", [1, 2, 3]),  # a list of 2
                                     (M4, "SeuilMort", "12"), (M4, "SeuilMort", True), (M4, "SeuilMort", 2 ** 31),
                                     (M4_GUN, "TirEnMouvement", 2), (M4, "Nope", 1)]:
            with self.subTest(prop=prop, value=value), self.assertRaises(StudioError):
                self.api.edit(address, prop, value)
        ammo = self.api.unit(AMMO)  # shared: editable, once it's said for whom (the next test)
        self.assertEqual((ammo["editable"], ammo["share"]["via"]), (True, None))
        self.assertEqual(self.api.edited(), [])
        with self.assertRaises(StudioError):
            self.api.choose_mod(self.tmp.name)  # no mod.toml
        self.assertEqual(Path(self.api.new_mod("x")["current"]).name, "x-2")

    def test_a_shared_part_for_one_unit_or_for_all(self):
        folder = Path(self.api.new_mod("Guns")["current"])
        page = self.api.unit(AMMO, via=PANZER_IV)  # opened from the Panzer's page
        self.assertEqual([o["address"] for o in page["share"]["owners"]], [M4, PANZER_IV])
        self.assertEqual(page["share"]["via"], {"address": PANZER_IV, "name": "Descriptor_Unit_Panzer_IV_G",
                                                "path": "Weapon.Ammo"})
        for mode, via in (("", PANZER_IV), ("own", ""), ("own", DEPOT)):
            with self.subTest(mode=mode, via=via), self.assertRaises(StudioError):
                self.api.edit(AMMO, "Puissance", 50, mode, via)  # for whom? / no unit / a unit that doesn't use it

        self.api.edit(AMMO, "Puissance", 50, "shared")  # all of them
        self.api.edit(AMMO, "Puissance", 60, "own", PANZER_IV)  # the Panzer only: it gets its own copy
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        shared = text.index("patch shared $/GFX/Everything/Descriptor_Unit_M4_Sherman:Weapon.Ammo\n(\n    Puissance = 50")
        own = text.index("patch own $/GFX/Everything/Descriptor_Unit_Panzer_IV_G:Weapon.Ammo\n(\n    Puissance = 60")
        self.assertLess(shared, own)  # the copy is taken after the change for everyone, so it has it too
        rows = {r["prop"]: r for g in self.api.unit(AMMO, via=PANZER_IV)["groups"] for r in g["rows"]}
        self.assertEqual((rows["Puissance"]["edited"], rows["Puissance"]["edited_own"]), (50, 60))
        self.assertEqual(self.api.edited(), [M4, PANZER_IV])  # a change for all of them marks every user

        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        ndf = Ndf(new.read(new.find("everything.cpp.gladndfbin")))
        ammo_of = lambda gun: struct.unpack("<III", ndf.objects[gun].get(8).payload)[1]  # noqa: E731
        self.assertEqual(ammo_of(4), 6)  # the M4's gun still uses the shared ammo...
        self.assertEqual(ndf.objects[6].get(9).scalar(), 50)  # ...changed for everyone
        self.assertNotEqual(ammo_of(5), 6)  # the Panzer's gun has its own copy now
        self.assertEqual(ndf.objects[ammo_of(5)].get(9).scalar(), 60)

        self.api.edit(AMMO, "Puissance", 50, "own", PANZER_IV)  # the same as everyone again: no own copy needed
        self.assertNotIn("patch own", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        self.api.reset(AMMO, "Puissance", "shared")
        self.assertEqual(self.api.edited(), [])

    def test_a_studio_edit_changes_the_game_data(self):
        folder = Path(self.api.new_mod("Tank Test")["current"])
        self.api.edit(M4, "SeuilMort", 15)
        self.api.edit(M4, "ProductionPrice", [25, 31])
        self.api.edit(M4_GUN, "PorteeMaximale", 3000)
        self.api.edit(M4_GUN, "TempsEntreDeuxTirs", 0.25)
        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        ndf = Ndf(new.read(new.find("everything.cpp.gladndfbin")))
        m4, gun = ndf.objects[0], ndf.objects[4]
        self.assertEqual((m4.get(1).scalar(), m4.get(0).int_list()), (15, [25, 31]))
        self.assertEqual(gun.get(10).scalar(), 3000)
        self.assertAlmostEqual(gun.get(11).scalar(), 0.25)
        self.assertEqual(ndf.objects[1].get(0).int_list(), [45, 45])  # the Panzer is untouched

    def test_changes_at_the_same_time_are_all_kept(self):  # the window calls from several threads
        self.api.new_mod("x")
        changes = [(M4, "SeuilMort", 20), (M4, "ProductionPrice", [1, 2]), (M4_GUN, "PorteeMaximale", 3000),
                   (M4_GUN, "TempsEntreDeuxTirs", 0.5), (M4_GUN, "TirEnMouvement", 0)]
        threads = [threading.Thread(target=self.api.edit, args=c) for c in changes]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        edits = ModEdits(Path(self.api.mods()["current"])).edits
        self.assertEqual({path: e.value for (_target, path, _how), e in edits.items()},
                         {"SeuilMort": 20, "ProductionPrice": [1, 2], "Weapon.PorteeMaximale": 3000,
                          "Weapon.TempsEntreDeuxTirs": 0.5, "Weapon.TirEnMouvement": 0})

    def test_a_broken_edits_file_is_never_written_over(self):
        folder = Path(self.api.new_mod("x")["current"])
        broken = "patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( SeuilMort = \n"  # changed by hand, badly
        (folder / "src" / "studio.rndf").write_text(broken, encoding="utf-8")
        u = self.api.unit(M4)  # browsing still works
        self.assertFalse(u["editable"])
        self.assertIn("studio.rndf has a mistake", u["why_not"])
        self.assertEqual(self.api.edited(), [])
        with self.assertRaises(EditsFileError):
            self.api.edit(M4, "SeuilMort", 15)
        self.assertEqual((folder / "src" / "studio.rndf").read_text(encoding="utf-8"), broken)

    def test_test_in_game_builds_the_mod_and_starts_it(self):  # the Studio's own, without the launcher
        with self.assertRaises(StudioError):
            self.api.test_in_game()  # no mod yet
        self.api.new_mod("Tank Test")
        self.api.edit(M4, "SeuilMort", 15)
        job = self.api.test_in_game()["job"]
        end = time.time() + 20
        while self.api.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        j = self.api.job(job)
        self.assertEqual((j["state"], j["message"]), ("done", "R.U.S.E. is starting."), j)
        copy = self.home / "copies" / "studio-tank-test"
        self.assertEqual(self.started, [copy / "RUSE.exe"])
        pack = Edat((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        self.assertEqual(Ndf(pack.read(pack.find("everything.cpp.gladndfbin"))).objects[0].get(1).scalar(), 15)
        self.assertEqual(self.api.job("nope")["state"], "failed")

    def test_numbers_as_modders_see_them(self):
        self.assertEqual([number(x) for x in (0.1, 1e-7, 12.0, True, -2.5, 3)], ["0.1", "0.0000001", "12", "1", "-2.5", "3"])
        self.assertEqual([_short(x) for x in (12.0, 0.10000000149011612, 0.1, 1e300)], [12, 0.1, 0.1, 1e300])
        self.assertEqual(ModEdits(self.home).edits, {})  # a folder without the file: no changes


SUPER = "$/GFX/Everything/Descriptor_Unit_Super_Sherman"


def find_export(ndf, path):
    return next(i for i, name in ndf.exports.items() if name == path)


class NewUnits(Editing):
    """New units from a unit's page: a copy of a unit the game has, with its own name, price and build menu, kept in
    the mod's src/studio.rndf and text/studio.baseunite.csv, listed, edited like any other unit, built, deleted."""

    def build(self, folder):
        rev = self.game / "Data" / "PC" / "190852"
        arc, texts = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes()), Edat((rev / "ZZ_Win.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)], text_arc=texts)
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        return Ndf(new.read(new.find("everything.cpp.gladndfbin"))), Edat(texts.to_bytes(result.text_changed))

    def test_a_new_unit_is_written_read_back_listed_and_built(self):
        with self.assertRaises(StudioError):
            self.api.new_unit(M4, "Super Sherman", 50)  # no mod yet
        folder = Path(self.api.new_mod("Copies")["current"])
        made = self.api.new_unit(M4, "Super Sherman", 50.4)
        self.assertEqual((made["address"], made["name"]), (SUPER, "Super Sherman"))
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("\nexport Descriptor_Unit_Super_Sherman is clone $/GFX/Everything/Descriptor_Unit_M4_Sherman\n(\n"
                      "    NameInMenuToken = loc('studio.Descriptor_Unit_Super_Sherman.name')\n"
                      "    ProductionPrice = [50, 50]\n)\n", rndf)  # the price for every battle date, whole
        names = (folder / "text" / "studio.baseunite.csv").read_text(encoding="utf-8")
        self.assertRegex(names, r"^key,game_key,us\nstudio\.Descriptor_Unit_Super_Sherman\.name,S[0-9A-Za-z_]{9},"
                                r"Super Sherman\n$")

        listed = self.api.units("fr")["units"]
        self.assertEqual(listed[0]["address"], SUPER)  # new units first
        self.assertEqual((listed[0]["name"], listed[0]["nation"], listed[0]["kind"], listed[0]["new"], listed[0]["source"]),
                         ("Super Sherman", 0, "ground", True, M4))
        self.assertFalse(listed[1]["new"])
        self.assertEqual(self.api.units()["total"], 5)
        self.assertEqual([u["address"] for u in self.api.units(nation=0, search="super")["units"]], [SUPER])
        self.assertEqual(self.api.edited(), [])  # new, not edited

        page = self.api.unit(SUPER, "fr")
        rows = {r["prop"]: r for g in page["groups"] for r in g["rows"]}
        self.assertEqual((page["name"], page["new"]), ("Super Sherman", {"source": M4, "source_name": "M4 Sherman (fr)"}))
        self.assertEqual((page["can_copy"], page["used_by"], page["named"]), (False, [], True))
        self.assertTrue(self.api.unit(M4)["can_copy"])
        self.assertEqual((rows["ProductionPrice"]["values"], rows["ProductionPrice"]["edited"]), (["30", "35"], [50, 50]))
        self.assertEqual(rows["NameInMenuToken"]["values"], ["Super Sherman"])
        self.assertEqual([(p["address"], p["shared"]) for p in page["parts"]],
                         [(SUPER + ":Weapon", False), (AMMO, True)])  # its own gun, the ammo everyone shares

        # edited like any other unit: its own values go inside its block, its parts get patch blocks
        self.assertEqual(self.api.edit(SUPER, "SeuilMort", 20)["value"], 20)
        self.api.edit(SUPER + ":Weapon", "PorteeMaximale", 3000)
        self.api.edit(AMMO, "Puissance", 70, "own", SUPER)  # the copy gets its own ammo
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("    ProductionPrice = [50, 50]\n    SeuilMort = 20\n)\n", rndf)
        self.assertIn("\npatch $/GFX/Everything/Descriptor_Unit_Super_Sherman:Weapon\n(\n    PorteeMaximale = 3000\n)\n", rndf)
        self.assertIn("\npatch own $/GFX/Everything/Descriptor_Unit_Super_Sherman:Weapon.Ammo\n(\n    Puissance = 70\n)\n", rndf)
        self.assertLess(rndf.index("export"), rndf.index("patch"))  # copies first
        ammo = self.api.unit(AMMO, via=SUPER)
        self.assertEqual([o["address"] for o in ammo["share"]["owners"]], [M4, PANZER_IV, SUPER])
        self.assertEqual(ammo["share"]["via"], {"address": SUPER, "name": "Super Sherman", "path": "Weapon.Ammo"})
        self.assertEqual({r["prop"]: r["edited_own"] for g in ammo["groups"] for r in g["rows"]}, {"Puissance": 70})
        self.assertEqual(self.rows(SUPER)["SeuilMort"]["edited"], 20)
        self.assertEqual(self.api.edited(), [])
        self.api.edit(SUPER, "SeuilMort", 12)  # the copied value again: no change left
        self.assertNotIn("SeuilMort", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))

        again = self.studio()  # opened again: the same new unit, from the files
        self.assertEqual([(u.source, u.name) for u in again._new_units().values()], [(M4, "Super Sherman")])
        self.assertEqual({r["prop"]: r["edited"] for g in again.unit(SUPER)["groups"] for r in g["rows"]
                          if r["edited"] is not None}, {"ProductionPrice": [50, 50]})

        ndf, texts = self.build(folder)
        i = find_export(ndf, SUPER)
        copy = ndf.objects[i]
        self.assertEqual((copy.get(0).int_list(), copy.get(1).scalar()), ([50, 50], 12))
        gun = struct.unpack("<III", copy.get(4).payload)[1]
        self.assertNotEqual(gun, 4)  # its own gun...
        self.assertEqual(ndf.objects[gun].get(10).scalar(), 3000)
        own_ammo = struct.unpack("<III", ndf.objects[gun].get(8).payload)[1]
        self.assertNotEqual(own_ammo, 6)  # ...and its own ammo
        self.assertEqual((ndf.objects[own_ammo].get(9).scalar(), ndf.objects[6].get(9).scalar()), (70, 40))
        self.assertEqual(ndf.objects[0].get(0).int_list(), [30, 35])  # the M4 is untouched
        key = struct.unpack("<Q", copy.get(2).payload)[0]
        self.assertNotEqual(key, SHERMAN)
        from rusemod.dic import Dic
        from rusemod import loc
        for lang in ("us", "fr"):  # one name, in every language the game has
            dic = Dic(texts.read(texts.find(loc.member("baseunite", lang))))
            self.assertEqual(dic.text(key), "Super Sherman")

    def test_a_new_unit_in_another_build_menu(self):
        folder = Path(self.api.new_mod("Lend-Lease")["current"])
        menus = self.api.menus("us")["nations"]
        self.assertEqual([(m["nation"], m["name"]) for m in menus][:2], [(0, "USA"), (1, "Germany")])
        self.assertEqual(menus[0]["factories"], [{"factory": 10, "units": ["M4 Sherman"], "count": 1}])
        self.assertEqual(menus[1]["factories"], [{"factory": 10, "units": ["Panzer IV"], "count": 1}])
        self.assertEqual(menus[5]["factories"], [])
        with self.assertRaises(StudioError):
            self.api.new_unit(M4, "Soviet Sherman", 40, 5, 10)  # the USSR has no factory 10 in this little game
        made = self.api.new_unit(M4, "German Sherman", 40, 1, 10)
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("    Factory = 10\n    Nationalite = 1\n    ProductionPrice = [40, 40]\n)\n", rndf)
        listed = self.api.units(nation=1)["units"]
        self.assertEqual([(u["address"], u["nation"]) for u in listed], [(made["address"], 1), (PANZER_IV, 1)])
        rows = self.rows(made["address"])
        self.assertEqual((rows["Nationalite"]["values"], rows["Nationalite"]["locked"]), (["1 (Allemagne)"], True))
        self.assertEqual(rows["Factory"]["edited"], 10)
        same = self.api.new_unit(M4, "Same menu", 40, 0, 10)  # the source's own menu: nothing to write
        self.assertNotIn("Descriptor_Unit_Same_menu\n(\n    NameInMenuToken = loc('studio.Descriptor_Unit_Same_menu.name')"
                         "\n    Nationalite", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        ndf, _texts = self.build(folder)
        copy = ndf.objects[find_export(ndf, made["address"])]
        self.assertEqual((copy.get(5).scalar(), copy.get(3).scalar(), copy.get(0).int_list()), (1, 10, [40, 40]))
        self.assertEqual(ndf.objects[find_export(ndf, same["address"])].get(5), None)
        self.assertEqual(same["address"], "$/GFX/Everything/Descriptor_Unit_Same_menu")

    def test_names_safe_for_the_game_and_no_clashes(self):
        self.api.new_mod("Names")
        for name, price in [("M4 Sherman", 10), ("", 10), ("  ", 10), ("Fine", "10"), ("Fine", True)]:
            with self.subTest(name=name, price=price), self.assertRaises(StudioError):
                self.api.new_unit(M4, name, price)  # the game's own unit / no name / not a number
        self.assertEqual(self.api.new_unit(M4, "Tigre à 2 tourelles!", 10)["address"],
                         "$/GFX/Everything/Descriptor_Unit_Tigre_a_2_tourelles")
        with self.assertRaises(StudioError):
            self.api.new_unit(M4, "Tigre a 2 tourelles", 10)  # the same address again
        self.assertEqual(self.api.new_unit(M4, "虎", 10)["address"], "$/GFX/Everything/Descriptor_Unit_New_1")
        self.assertEqual(self.api.new_unit(M4, "戦車", 10)["address"], "$/GFX/Everything/Descriptor_Unit_New_2")
        self.assertEqual(self.api.new_unit(DEPOT, "Big Depot", 10)["address"],
                         "$/GFX/Everything/Descriptor_Building_Big_Depot")
        with self.assertRaises(StudioError):
            self.api.new_unit(AMMO, "Ammo copy", 10)  # not a unit
        with self.assertRaises(StudioError):
            self.api.new_unit("$/GFX/Everything/Descriptor_Unit_New_1", "Copy of a copy", 10)
        self.assertEqual([u["name"] for u in self.api.units()["units"] if u["new"]],
                         ["Big Depot", "虎", "戦車", "Tigre à 2 tourelles!"])  # by address
        self.assertEqual(self.api.units(kind="buildings")["units"][0]["name"], "Big Depot")

    def test_deleting_a_new_unit_removes_everything_about_it(self):
        folder = Path(self.api.new_mod("Copies")["current"])
        self.api.new_unit(M4, "Super Sherman", 50)
        self.api.new_unit(M4, "Other", 50)
        self.api.edit(SUPER, "SeuilMort", 20)
        self.api.edit(SUPER + ":Weapon", "PorteeMaximale", 3000)
        self.api.edit(AMMO, "Puissance", 70, "own", SUPER)
        self.api.edit(M4, "SeuilMort", 15)
        with self.assertRaises(StudioError):
            self.api.delete_unit(M4)  # the game's own unit
        self.assertEqual(self.api.delete_unit(SUPER)["source"], M4)
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertNotIn("Super_Sherman", rndf)
        self.assertIn("Descriptor_Unit_Other is clone", rndf)
        self.assertIn("patch $/GFX/Everything/Descriptor_Unit_M4_Sherman\n(\n    SeuilMort = 15\n)", rndf)
        self.assertNotIn("Super", (folder / "text" / "studio.baseunite.csv").read_text(encoding="utf-8"))
        self.api.delete_unit("$/GFX/Everything/Descriptor_Unit_Other")
        self.assertFalse((folder / "text" / "studio.baseunite.csv").exists())  # no names left to keep
        self.assertEqual([u["address"] for u in self.api.units()["units"] if u["new"]], [])
        self.assertEqual(self.api.edited(), [M4])
        with self.assertRaises(StudioError):
            self.api.unit(SUPER)  # gone: nothing at that address any more
        self.assertEqual(ModEdits(folder).new_units, {})

    def test_a_broken_names_file_is_never_written_over(self):
        folder = Path(self.api.new_mod("Copies")["current"])
        self.api.new_unit(M4, "Super Sherman", 50)
        (folder / "text" / "studio.baseunite.csv").write_text("key,us\n,no key\n", encoding="utf-8")
        self.assertFalse(self.api.unit(M4)["editable"])
        self.assertFalse(any(u["new"] for u in self.api.units()["units"]))  # it can't be shown; browsing goes on
        with self.assertRaises(EditsFileError):
            self.api.new_unit(M4, "Another", 50)
        (folder / "text" / "studio.baseunite.csv").unlink()  # gone by hand: the unit keeps a plain name
        self.assertEqual(self.api.units()["units"][0]["name"], "Super Sherman")


class Labels(unittest.TestCase):
    """Every display name has all ten languages, so no modder gets a half-translated tool."""

    def test_complete(self):
        data = schema._data()
        for section, entries in (("props", data["props"]), ("groups", data["groups"]), ("Studio words", _words())):
            for name, entry in entries.items():
                missing = [lang for lang in schema.LANGS if not entry.get(lang)]
                self.assertEqual(missing, [], f"{section}: {name}")
        for name, entry in data["props"].items():
            self.assertIn(entry["group"], schema.GROUP_ORDER, name)
        for lang, names in data["nations"].items():
            self.assertEqual(len(names), 7, lang)
        self.assertEqual(schema.label("ProductionPrice[2]", "fr"), "Prix [2]")
        self.assertEqual(schema.label("NotTranslated", "fr"), "NotTranslated")
        self.assertEqual(schema.label("SeuilMort"), "SeuilMort")  # the game's names by default

    def test_every_word_the_studio_screen_uses_exists(self):
        ui = Path(__file__).parents[1] / "src" / "ruse_studio" / "ui"
        app = "\n".join((ui / f).read_text(encoding="utf-8") for f in ("app.js", "maps.js"))
        used = set(re.findall(r"\b(?:w|state\.words)\.([a-z_]+)", app))
        used |= {"all", "ground", "infantry", "air", "buildings", "not_stable"}  # looked up by key
        self.assertGreater(len(used), 25)
        self.assertEqual(sorted(used - set(_words())), [])


if __name__ == "__main__":
    unittest.main()
