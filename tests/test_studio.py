"""The Studio app's back end (ruse_studio.api) and the display names (rusemod.schema), on a made-up game."""
import hashlib
import os
import re
import struct
import tempfile
import threading
import time
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat, Ndf, schema
from rusemod.brush import parse_strokes
from rusemod.build import build_pack, load_mod
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod import mod_index, package
from rusemod.community import private_paths_out
from rusemod.play import Starter
from ruse_studio import __version__
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


def u32(v):
    return val(0x03, struct.pack("<I", v))


def s(i):
    return val(0x07, struct.pack("<I", i))


AMMO75, AMMO88, APSHELL, MEDIUM, LARGE = (name_to_key(n) for n in ("AMMO75", "AMMO88", "APSHELL", "MEDIUM", "LARGE"))

# classes: 0 TUniteAuSolDescriptor, 1 TInfanterieDescriptor, 2 TBatimentDescriptor, 3 TWeapon, 4 TAmmunition,
# 5 TMountedWeaponDescriptor. The Panzer also has a mounted weapon firing a named ammunition, like the real game's
# units, and a flag list; the M4 keeps the simpler shape the earlier tests were written for.
UNITS = make_ndf(
    objects=[(0, [(0, lst(i32(30), i32(35))), (1, i32(12)), (2, key(SHERMAN)), (3, i32(10)), (4, ref(4, 3))]),  # 0 M4
             (0, [(0, lst(i32(45), i32(45))), (5, i32(1)), (2, key(PANZER)), (3, i32(10)), (4, ref(5, 3)),
                  (13, ref(9, 5)), (14, lst(u32(4), u32(10)))]),                                          # 1 Panzer
             (1, [(6, i32(4))]),                                                                          # 2 infantry
             (2, [(7, lst(i32(20)))]),                                                                    # 3 depot
             (3, [(8, ref(6, 4)), (10, i32(2500)), (11, f32(0.1)), (12, flag(1))]),                       # 4 M4 gun
             (3, [(8, ref(6, 4))]),                                                                       # 5 Panzer gun
             (4, [(9, i32(40))]),                                                                         # 6 shared ammo
             (4, [(15, u32(1001)), (9, i32(55)), (16, key(MEDIUM)), (17, key(APSHELL))]),                # 7 Ammo 75
             (4, [(15, u32(1002)), (9, i32(90)), (16, key(LARGE)), (17, key(APSHELL))]),                 # 8 Ammo 88
             (5, [(18, s(0)), (19, ref(7, 4))])],                                                        # 9 Panzer's mount
    classes=["TUniteAuSolDescriptor", "TInfanterieDescriptor", "TBatimentDescriptor", "TWeapon", "TAmmunition",
             "TMountedWeaponDescriptor"],
    props=[("ProductionPrice", 0), ("SeuilMort", 0), ("NameInMenuToken", 0), ("Factory", 0), ("Weapon", 0),
           ("Nationalite", 0), ("SeuilMort", 1), ("ProductionPrice", 2), ("Ammo", 3), ("Puissance", 4),
           ("PorteeMaximale", 3), ("TempsEntreDeuxTirs", 3), ("TirEnMouvement", 3), ("MountedWeapon", 0),
           ("InitialFlagSet", 0), ("AmmunitionId", 4), ("Name", 4), ("TypeName", 4), ("EffectTag", 5),
           ("Ammunition", 5)],
    strings=["weapon_effet_tag1"],
    exports={0: "GFX/Everything/Descriptor_Unit_M4_Sherman", 1: "GFX/Everything/Descriptor_Unit_Panzer_IV_G",
             2: "GFX/Everything/Descriptor_Unit_Soldat_US_Leger", 3: "GFX/Everything/Descriptor_Building_Depot",
             7: "GFX/Everything/Ammo_Canon_75", 8: "GFX/Everything/Ammo_Canon_88"},
    topo=[0, 1, 2, 3, 7, 8])


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "everything.cpp.gladndfbin", UNITS)]))
    texts = {"us": [(SHERMAN, "M4 Sherman"), (PANZER, "Panzer IV"), (APSHELL, "AP shell"), (MEDIUM, "Medium cal."),
                    (LARGE, "Large cal.")],
             "fr": [(SHERMAN, "M4 Sherman (fr)"), (PANZER, "Panzer IV (fr)"), (APSHELL, "Obus AP"),
                    (MEDIUM, "Moyen cal."), (LARGE, "Gros cal.")]}
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

    def test_units_by_type(self):
        everything = self.api.units()
        self.assertEqual(everything["groups"], ["money", "armor", "other"])  # in GROUPS order: buildings' jobs first
        self.assertEqual({u["base_name"]: u["group"] for u in everything["units"]},
                         {"Descriptor_Building_Depot": "money", "Descriptor_Unit_M4_Sherman": "armor",
                          "Descriptor_Unit_Panzer_IV_G": "armor", "Descriptor_Unit_Soldat_US_Leger": "other"})
        armor = self.api.units(group="armor")
        self.assertEqual([u["base_name"] for u in armor["units"]], ["Descriptor_Unit_M4_Sherman", "Descriptor_Unit_Panzer_IV_G"])
        self.assertEqual(armor["groups"], everything["groups"])  # the choices stay: they're of the kind and nation
        self.assertEqual(self.api.units(kind="buildings")["groups"], ["money"])

    def test_what_a_unit_is_for(self):
        from ruse_studio.api import group_of
        building = "$/GFX/Everything/Descriptor_Building_"
        self.assertEqual([group_of("buildings", building + n, 3) for n in (
            "CaserneLeurreFR", "HeadquarterGRFake", "Headquarter", "BatimentAdministratifUK", "DalleBatimentDepot",
            "DefenseMaginotFR", "Def_Bunker_enterre_JAP", "ArtillerieFieldLourd", "PosteAlerteAvanceUK",
            "VehiculeFactory", "Usine_Atomique_US")],
            ["fake", "fake", "hq", "money", "money", "fort", "fort", "fort", "fort", "factory", "factory"])
        self.assertEqual([group_of(k, "$/GFX/Everything/Descriptor_Unit_X", f) for k, f in (
            ("infantry", 8), ("ground", 10), ("ground", 11), ("ground", 13), ("ground", 12), ("air", 9),
            ("infantry", 9), ("ground", 3), ("ground", None))],
            ["barracks", "armor", "antitank", "artillery", "prototype", "airfield", "airfield", "turret", "other"])

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


class WithMod(unittest.TestCase):
    """A Studio on the made-up game with a fresh platform folder per test, and a game to start (nothing starts)."""

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


class Editing(WithMod):
    """Changing a unit's numbers in place: saved in the mod's src/studio.rndf, read back, built into the game data."""

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
        copy = self.home / "copies" / "studio-tank-test"
        self.assertEqual((j["state"], j["message"]), ("done", f"R.U.S.E. is starting from {copy}. To see your changes: "
                                                               f"your unit changes show in every game mode."), j)
        self.assertIn("  Your unit changes show in every game mode.", j["lines"])
        self.assertEqual(self.started, [copy / "RUSE.exe"])
        pack = Edat((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        self.assertEqual(Ndf(pack.read(pack.find("everything.cpp.gladndfbin"))).objects[0].get(1).scalar(), 15)
        self.assertEqual(self.api.job("nope")["state"], "failed")
        from rusemod.webui import Job
        busy = Job()  # a build still going: a second press (a double click) waits for it
        self.api._jobs[busy.id] = busy
        self.api._test_job = busy.id
        with self.assertRaisesRegex(StudioError, "already being built"):
            self.api.test_in_game()
        busy.state = "done"
        again = self.api.test_in_game()["job"]
        end = time.time() + 20
        while self.api.job(again)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        self.assertEqual(self.api.job(again)["state"], "done")

    def test_export_mod_makes_one_file_with_the_build_and_fingerprint(self):
        with self.assertRaises(StudioError):
            self.api.export_mod("1.0.0")  # no mod yet
        self.api.new_mod("Tank Test")
        self.api.edit(M4, "SeuilMort", 15)
        with self.assertRaisesRegex(StudioError, "like 1.0.0"):
            self.api.export_mod("one")
        self.api._pick_save = lambda name: None  # the dialog cancelled: nothing happens
        self.assertEqual(self.api.export_mod("1.2.0", "Tristen", "Tanks are tougher."), {"job": None})
        # a game the way Steam lays it out, so the build id is known
        steam = self.home / "steamapps"
        game = steam / "common" / "R.U.S.E"
        write_game(game)
        (game / "RUSE.exe").write_bytes(b"MZ")
        (steam / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        dest, picked = self.home / "Documents", []
        dest.mkdir()
        api = StudioApi(index_path=self.index, game_dir=game, home=self.home, instances=self.home / "copies",
                        pick_save=lambda name: (picked.append(name), str(dest / name))[1])

        def export(*args):
            job = api.export_mod(*args)["job"]
            end = time.time() + 20
            while api.job(job)["state"] == "running" and time.time() < end:
                time.sleep(0.02)
            return api.job(job)

        j = export("1.2.0", "Tristen", "Tanks are tougher.")
        self.assertEqual((j["state"], j["message"]), ("done", f"Saved as {dest / 'tank-test-1.2.0.rusemod'}"), j)
        self.assertEqual(picked, ["tank-test-1.2.0.rusemod"])
        info = package.check(dest / "tank-test-1.2.0.rusemod")
        self.assertEqual((info["id"], info["version"], info["authors"], info["description"], info["builds"], info["data_revision"]),
                         ("tank-test", "1.2.0", ["Tristen"], "Tanks are tougher.", ["24687178"], "190852"))
        self.assertRegex(info["fingerprint"], r"^[0-9A-Z]{4}-[0-9A-Z]{4}$")
        self.assertIn("src/studio.rndf", info["files"])
        # "Share your mod": the file's size and SHA-256 for the supported-mods list, and its index.toml entry
        data = (dest / "tank-test-1.2.0.rusemod").read_bytes()
        shared = j["result"]
        self.assertEqual((shared["file"], shared["size"], shared["sha256"]),
                         ("tank-test-1.2.0.rusemod", len(data), hashlib.sha256(data).hexdigest()))
        self.assertIn(f"Size: {len(data)} bytes", j["lines"])
        self.assertIn(f"SHA-256: {shared['sha256']}", j["lines"])
        listed, problems = mod_index.parse("format = 1\n" + shared["entry"].replace('download = ""', 'download = "https://x/t"'))
        self.assertEqual(problems, [])
        self.assertEqual((listed[0]["id"], listed[0]["version"], listed[0]["size"], listed[0]["sha256"], listed[0]["author"],
                          listed[0]["game_build"], listed[0]["fingerprint"]),
                         ("tank-test", "1.2.0", len(data), shared["sha256"], "Tristen", "24687178", info["fingerprint"]))
        self.assertEqual(api.share_info(), {"repo": "sneadtristen6/Ruse-Mods", "page": "https://github.com/sneadtristen6/Ruse-Mods"})
        again = api.mod_info()  # the folder's manifest keeps them for next time
        self.assertEqual((again["version"], again["author"], again["fingerprint"]), ("1.2.0", "Tristen", info["fingerprint"]))
        j = export("1.2.1")  # blank author and description: the old ones stay
        self.assertEqual(j["state"], "done", j)
        self.assertEqual((api.mod_info()["author"], api.mod_info()["description"]), ("Tristen", "Tanks are tougher."))
        (Path(api.mods()["current"]) / "src" / "extra.rndf").write_text("patch $/Nope ( X = 1 )", encoding="utf-8")
        j = export("1.2.2")  # a mod with a mistake isn't exported
        self.assertEqual(j["state"], "failed", j)
        self.assertIn("Fix the mod first", j["message"])
        self.assertFalse((dest / "tank-test-1.2.2.rusemod").exists())
        (Path(api.mods()["current"]) / "src" / "extra.rndf").unlink()
        without = StudioApi(index_path=self.index, game_dir=None, find=lambda: None, home=self.home,
                            pick_save=lambda name: str(dest / name))
        job = without.export_mod("1.3.0")["job"]
        end = time.time() + 20
        while without.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        j = without.job(job)
        self.assertEqual(j["state"], "done", j)
        self.assertIn("R.U.S.E. wasn't found, so the file carries no game build or fingerprint.", j["lines"])
        self.assertEqual(package.check(dest / "tank-test-1.3.0.rusemod")["builds"], ["24687178"])  # kept from before

    def test_numbers_as_modders_see_them(self):
        self.assertEqual([number(x) for x in (0.1, 1e-7, 12.0, True, -2.5, 3)], ["0.1", "0.0000001", "12", "1", "-2.5", "3"])
        self.assertEqual([_short(x) for x in (12.0, 0.10000000149011612, 0.1, 1e300)], [12, 0.1, 0.1, 1e300])
        self.assertEqual(ModEdits(self.home).edits, {})  # a folder without the file: no changes


SUPER = "$/GFX/Everything/Descriptor_Unit_Super_Sherman"


def find_export(ndf, path):
    return next(i for i, name in ndf.exports.items() if name == path)


class NewUnits(WithMod):
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


AMMO_75, AMMO_88 = "$/GFX/Everything/Ammo_Canon_75", "$/GFX/Everything/Ammo_Canon_88"
PANZER_MOUNT = PANZER_IV + ":MountedWeapon"


class AmmoAndFlags(WithMod):
    """The ammunition list, a weapon firing another ammo, a copied ammo of a unit's own, and a unit's flag list."""

    def build(self, folder):
        rev = self.game / "Data" / "PC" / "190852"
        arc = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        return Ndf(new.read(new.find("everything.cpp.gladndfbin")))

    def test_ammunition_listed_with_its_users_and_names(self):
        listed = self.api.units("us", kind="ammo")
        self.assertEqual(listed["total"], 2)
        self.assertEqual([(a["address"], a["name"], a["id"], a["users"], a["kind"]) for a in listed["units"]],
                         [(AMMO_75, "AP shell · Medium cal.", 1001, ["Panzer IV"], "ammo"),
                          (AMMO_88, "AP shell · Large cal.", 1002, [], "ammo")])
        self.assertEqual([a["nations"] for a in listed["units"]], [["Germany"], []])  # the Panzer's country; unused: none
        self.assertEqual([a["name"] for a in self.api.ammo("fr")["units"]], ["Obus AP · Moyen cal.", "Obus AP · Gros cal."])
        self.assertEqual(self.api.ammo("fr")["units"][0]["nations"], ["Allemagne"])
        self.assertEqual([a["name"] for a in self.api.ammo()["units"]], ["Ammo_Canon_75", "Ammo_Canon_88"])  # code names
        self.assertEqual([a["address"] for a in self.api.ammo("us", search="panzer")["units"]], [AMMO_75])  # by user too
        self.assertEqual((listed["groups"], [a["group"] for a in listed["units"]]), (["ap"], ["ap", "ap"]))  # AP shells
        self.assertEqual(len(self.api.units("us", kind="ammo", group="ap")["units"]), 2)
        self.assertEqual(self.api.units("us", kind="ammo", group="bombs")["units"], [])
        page = self.api.unit(AMMO_75)
        self.assertEqual((page["can_copy"], page["can_copy_ammo"], page["has_weapons"]), (False, True, False))
        self.assertTrue(self.api.unit(PANZER_IV)["has_weapons"])

    def test_a_weapon_fires_another_ammo(self):
        folder = Path(self.api.new_mod("Guns")["current"])
        w = self.api.weapons(PANZER_IV, "us")
        self.assertEqual(w["weapons"], [{"address": PANZER_MOUNT, "name": "weapon_effet_tag1",
                                         "ammo": {"address": AMMO_75, "name": "AP shell · Medium cal."},
                                         "game_ammo": AMMO_75, "edited": False, "shot": ""}])
        self.assertEqual([(c["address"], c["nations"]) for c in w["choices"]],
                         [(AMMO_88, []), (AMMO_75, ["Germany"])])  # by name: Large before Medium; whose it is
        self.assertEqual(self.api.weapons(M4)["weapons"], [])  # the M4's gun is the older, simpler shape
        saved = self.api.set_ammo(PANZER_IV, PANZER_MOUNT, AMMO_88)
        self.assertEqual((saved["ammo"], saved["edited"]), (AMMO_88, True))
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("\npatch $/GFX/Everything/Descriptor_Unit_Panzer_IV_G:MountedWeapon\n(\n"
                      "    Ammunition = $/GFX/Everything/Ammo_Canon_88\n)\n", rndf)
        w = self.api.weapons(PANZER_IV, "us")["weapons"][0]
        self.assertEqual((w["ammo"]["address"], w["ammo"]["name"], w["edited"]), (AMMO_88, "AP shell · Large cal.", True))
        self.assertEqual(self.api.edited(), [PANZER_IV])
        ndf = self.build(folder)
        mount = ndf.objects[9]
        self.assertEqual(struct.unpack("<III", mount.get(19).payload)[1], 8)  # the mount now points at Ammo 88
        for unit, weapon, ammo in [(M4, PANZER_MOUNT, AMMO_88), (PANZER_IV, PANZER_IV + ":Weapon", AMMO_88),
                                   (PANZER_IV, PANZER_MOUNT, M4), (PANZER_IV, PANZER_MOUNT, "$/GFX/Nope")]:
            with self.subTest(weapon=weapon, ammo=ammo), self.assertRaises(StudioError):
                self.api.set_ammo(unit, weapon, ammo)
        self.api.set_ammo(PANZER_IV, PANZER_MOUNT, AMMO_75)  # the game's own again: no change left
        self.assertNotIn("MountedWeapon", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        self.assertFalse(self.api.weapons(PANZER_IV)["weapons"][0]["edited"])

    def test_a_copied_ammo_for_a_weapon_of_its_own(self):
        with self.assertRaises(StudioError):
            self.api.new_ammo(AMMO_75, "Hot 75")  # no mod yet
        folder = Path(self.api.new_mod("Copies")["current"])
        made = self.api.new_ammo(AMMO_75, "Hot 75")
        self.assertEqual(made["address"], "$/GFX/Everything/Ammo_Hot_75")
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("\nexport Ammo_Hot_75 is clone $/GFX/Everything/Ammo_Canon_75\n(\n)\n", rndf)
        self.assertFalse((folder / "text" / "studio.baseunite.csv").exists())  # it keeps its source's name in game
        listed = self.api.ammo("us")["units"]
        self.assertEqual((listed[0]["address"], listed[0]["name"], listed[0]["new"], listed[0]["source_name"],
                          listed[0]["nations"]), (made["address"], "Hot 75", True, "AP shell · Medium cal.", ["Germany"]))
        self.assertEqual([u["address"] for u in self.api.units()["units"] if u["new"]], [])  # not among the units
        page = self.api.unit(made["address"], "us")
        rows = {r["prop"]: r for g in page["groups"] for r in g["rows"]}
        self.assertEqual((page["name"], page["new"]["source"], page["can_copy_ammo"]), ("Hot 75", AMMO_75, False))
        self.assertEqual(self.api.edit(made["address"], "Puissance", 80)["value"], 80)
        self.assertEqual(self.rows(made["address"])["Puissance"]["edited"], 80)
        self.assertFalse(rows["AmmunitionId"]["editable"])  # ids stay unique: the build hands one out
        choices = self.api.weapons(PANZER_IV, "us")["choices"]
        self.assertEqual([(c["address"], c["new"]) for c in choices if c["new"]], [(made["address"], True)])
        self.api.set_ammo(PANZER_IV, PANZER_MOUNT, made["address"])
        ndf = self.build(folder)
        copy = find_export(ndf, "$/GFX/Everything/Ammo_Hot_75")
        obj = ndf.objects[copy]
        self.assertEqual((obj.get(15).scalar(), obj.get(9).scalar()), (1003, 80))  # a fresh id, its own damage
        self.assertEqual(struct.unpack("<III", ndf.objects[9].get(19).payload)[1], copy)
        with self.assertRaises(StudioError):
            self.api.new_ammo(made["address"], "Hotter")  # a copy of a copy
        with self.assertRaises(StudioError):
            self.api.new_ammo(PANZER_IV, "Tank")  # not an ammunition
        gone = self.api.delete_unit(made["address"])
        self.assertEqual(gone["source"], AMMO_75)
        self.assertEqual(self.api.ammo()["total"], 2)

    def test_flags_are_a_list_of_any_length(self):
        flags = self.api.flags("us")["flags"]
        self.assertEqual([f["flag"] for f in flags], list(range(105)))  # every flag, the ones no unit carries too
        self.assertEqual([(f["flag"], f["count"], f["examples"]) for f in flags if f["count"] or f["examples"]],
                         [(4, 1, ["Panzer IV"]), (10, 1, ["Panzer IV"])])
        # each flag says what it does, from what we and DomesticNukes have tried in the game (rusemod.schema.flag)
        self.assertEqual([f["meaning"] for f in flags], [schema.flag(n) for n in range(105)])
        self.assertIn("Building", flags[4]["meaning"])
        self.assertIn("in a unit's flags it does nothing", flags[91]["meaning"])  # state the game sets while it runs
        self.assertIn("sans effet", self.api.flags("fr")["flags"][91]["meaning"])  # in the language picked
        self.assertTrue(schema.flag(72).startswith("Sees through obstacles"))
        folder = Path(self.api.new_mod("Flags")["current"])
        row = self.rows(PANZER_IV)["InitialFlagSet"]
        self.assertEqual((row["numbers"], row["list"], row["type"], row["editable"], row["label"]),
                         ([4, 10], True, "uint32", True, "InitialFlagSet"))
        self.assertEqual(self.api.edit(PANZER_IV, "InitialFlagSet", [4, 10, 72, 72])["value"], [4, 10, 72])  # once each
        self.assertEqual(self.api.edit(PANZER_IV, "InitialFlagSet", [10])["value"], [10])  # shorter is fine
        self.assertIn("    InitialFlagSet = [10]\n", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        for value in ([4, -1], [4, 2 ** 32], 4, [4, "x"]):
            with self.subTest(value=value), self.assertRaises(StudioError):
                self.api.edit(PANZER_IV, "InitialFlagSet", value)
        self.assertEqual(self.build(folder).objects[1].get(14).int_list(), [10])
        self.api.edit(PANZER_IV, "InitialFlagSet", [4, 10])  # the game's own: no change left
        self.assertEqual(self.rows(PANZER_IV)["InitialFlagSet"]["edited"], None)

    def test_an_index_from_an_older_studio_is_built_again(self):
        import sqlite3
        old = Path(self.home, "old.sqlite")
        old.write_bytes(self.index.read_bytes())
        db = sqlite3.connect(str(old))
        db.execute("UPDATE meta SET value = '2' WHERE key = 'format'")
        db.commit()
        db.close()
        api = StudioApi(index_path=old, game_dir=self.game, home=self.home)
        self.assertEqual(api.status(), {"ready": False, "can_build": True, "old": True})


class Terrain(WithMod):
    """The Maps view's brushes: strokes saved in the mod's maps/<map pack>/terrain.toml (the build's own format),
    read back for the view to draw, and taken off again with Undo."""

    HILL = {"brush": "hill", "x": 500.0, "y": 600.0, "radius": 120.0, "height": 30.0}

    def test_no_mod_yet(self):
        self.assertEqual(self.api.terrain("TwoIslands"), {"strokes": [], "saved": None, "mod": None})
        with self.assertRaisesRegex(StudioError, "Pick or make a mod"):
            self.api.terrain_add("TwoIslands", [self.HILL])
        with self.assertRaisesRegex(StudioError, "Pick or make a mod"):
            self.api.terrain_undo("TwoIslands")

    def test_strokes_saved_read_back_and_undone(self):
        folder = Path(self.api.new_mod("Hills")["current"])
        file = folder / "maps" / "TwoIslands" / "terrain.toml"
        self.assertEqual(self.api.terrain_add("TwoIslands", [self.HILL]), {"count": 1, "saved": str(file)})
        plateau = {"brush": "plateau", "x": 100, "y": 100, "radius": 50, "level": 20.0, "weight": 1.0}
        smooth = {"brush": "smooth", "x": 100, "y": 100, "radius": 50, "weight": 0.5}
        self.assertEqual(self.api.terrain_add("TwoIslands", [plateau, smooth])["count"], 3)
        # the file is the mod format's own: the build's reader takes it as it is
        strokes = parse_strokes(tomllib.loads(file.read_text(encoding="utf-8"))["stroke"], "terrain.toml")
        self.assertEqual([s.brush for s in strokes], ["hill", "plateau", "smooth"])
        self.assertEqual((strokes[0].height, strokes[1].level, strokes[2].weight), (30.0, 20.0, 0.5))
        view = self.api.terrain("TwoIslands")
        self.assertEqual((view["mod"], view["saved"]), (str(folder), str(file)))
        self.assertEqual([s["brush"] for s in view["strokes"]], ["hill", "plateau", "smooth"])
        self.assertEqual(view["strokes"][0], {"brush": "hill", "x": 500.0, "y": 600.0, "radius": 120.0, "height": 30.0,
                                              "level": 0.0, "weight": 1.0, "x2": 0.0, "y2": 0.0, "level2": 0.0,
                                              "square": False})
        self.assertEqual(self.api.terrain("SuperCrossroads4")["strokes"], [])  # another map has its own
        # Undo takes the last strokes off; the file goes when none is left, and its empty folders with it
        self.assertEqual(self.api.terrain_undo("TwoIslands", 2), {"count": 1, "removed": 2, "saved": str(file)})
        self.assertEqual(parse_strokes(tomllib.loads(file.read_text(encoding="utf-8"))["stroke"])[0].brush, "hill")
        self.assertEqual(self.api.terrain_undo("TwoIslands", 5), {"count": 0, "removed": 1, "saved": None})
        self.assertFalse(file.exists())
        self.assertFalse((folder / "maps").exists())
        self.assertTrue((folder / "mod.toml").is_file())
        self.assertEqual(self.api.terrain("TwoIslands"), {"strokes": [], "saved": None, "mod": str(folder)})
        self.assertEqual(self.api.terrain_undo("TwoIslands"), {"count": 0, "removed": 0, "saved": None})

    def test_each_mod_has_its_own_strokes(self):
        first = self.api.new_mod("First")["current"]
        self.api.terrain_add("TwoIslands", [self.HILL])
        self.api.new_mod("Second")
        self.assertEqual(self.api.terrain("TwoIslands")["strokes"], [])
        self.api.choose_mod(first)
        self.assertEqual(len(self.api.terrain("TwoIslands")["strokes"]), 1)

    def test_what_is_refused(self):
        self.api.new_mod("x")
        with self.assertRaisesRegex(StudioError, "isn't a map's pack name"):
            self.api.terrain("../etc")
        with self.assertRaisesRegex(StudioError, "isn't a map's pack name"):
            self.api.terrain_add("Two Islands", [self.HILL])
        with self.assertRaisesRegex(StudioError, "stroke 1: brush 'mesa' isn't one of"):
            self.api.terrain_add("TwoIslands", [{"brush": "mesa", "x": 1, "y": 1, "radius": 5}])
        with self.assertRaisesRegex(StudioError, "the hill brush needs height"):
            self.api.terrain_add("TwoIslands", [self.HILL, {"brush": "hill", "x": 1, "y": 1, "radius": 5}])
        self.assertEqual(self.api.terrain("TwoIslands")["strokes"], [])  # nothing half-written

    def test_a_broken_terrain_file_is_never_written_over(self):
        folder = Path(self.api.new_mod("x")["current"])
        file = folder / "maps" / "TwoIslands" / "terrain.toml"
        file.parent.mkdir(parents=True)
        by_hand = '[[stroke]]\nbrush = "hill"\n'  # x, y and radius missing
        file.write_text(by_hand, encoding="utf-8")
        for call in (lambda: self.api.terrain("TwoIslands"), lambda: self.api.terrain_add("TwoIslands", [self.HILL]),
                     lambda: self.api.terrain_undo("TwoIslands")):
            with self.assertRaisesRegex(StudioError, "can't be read .*stroke 1"):
                call()
        self.assertEqual(file.read_text(encoding="utf-8"), by_hand)

    MAPS = [{"pack": "SuperCrossRoads4", "titles": {"us": ["Blitz", "Anzio"], "ru": ["Блиц"]}},
            {"pack": "TwoIslands", "titles": {"us": ["Centre of Gravity"]}},
            {"pack": "M04_cotentin", "titles": {"us": ["D-Day", "10. UTAH BEACH"]}}]

    def test_map_folders_named_after_a_title_are_found_and_renamed(self):
        folder = Path(self.api.new_mod("x")["current"])
        hill = '[[stroke]]\nbrush = "hill"\nx = 1.0\ny = 2.0\nradius = 3.0\nheight = 4.0\n'
        for name in ("Blitz", "twoislands", "Nowhere", "SuperCrossRoads4", "Empty"):
            (folder / "maps" / name).mkdir(parents=True)
            if name != "Empty":
                (folder / "maps" / name / "terrain.toml").write_text(hill, encoding="utf-8")
        (folder / "maps" / "scenery.toml").write_text("", encoding="utf-8")
        with mock.patch("rusemod.modcheck.map_list", return_value=self.MAPS):
            got = {p["file"]: p for p in self.api.check_mod()["problems"]}
            self.assertEqual(sorted(got), ["maps/Blitz", "maps/Nowhere", "maps/scenery.toml", "maps/twoislands"])
            self.assertEqual(got["maps/Blitz"]["rename_to"], "SuperCrossRoads4")
            self.assertIn("Blitz is the title of a map whose pack is SuperCrossRoads4", got["maps/Blitz"]["problem"])
            self.assertEqual(got["maps/twoislands"]["rename_to"], "TwoIslands")
            self.assertIsNone(got["maps/Nowhere"]["rename_to"])
            self.assertIn("loose in maps/", got["maps/scenery.toml"]["problem"])
            with self.assertRaisesRegex(StudioError, "maps/SuperCrossRoads4 already exists"):
                self.api.rename_map_folder("Blitz", "SuperCrossRoads4")
            left = self.api.rename_map_folder("twoislands", "TwoIslands")["problems"]
            self.assertNotIn("maps/twoislands", [p["file"] for p in left])
            self.assertTrue((folder / "maps" / "TwoIslands" / "terrain.toml").is_file())
            for name, to in (("Nope", "X"), ("Blitz", "../x"), ("..", "X")):
                with self.assertRaises(StudioError):
                    self.api.rename_map_folder(name, to)

    def test_a_folder_name_to_its_pack(self):
        from rusemod.terrain import pack_for
        for name, pack in (("Blitz", "SuperCrossRoads4"), ("blitz", "SuperCrossRoads4"), ("Anzio", "SuperCrossRoads4"),
                           ("Блиц", "SuperCrossRoads4"), ("supercrossroads4", "SuperCrossRoads4"),
                           ("Centre_of_Gravity", "TwoIslands"), ("UtahBeach", "M04_cotentin"), ("DDay", "M04_cotentin"),
                           ("Nowhere", None), ("", None), ("___", None)):
            self.assertEqual(pack_for(name, self.MAPS), pack, name)
        from rusemod.build import _meant  # the build's error says the same to a player
        with mock.patch("rusemod.terrain.map_list", return_value=self.MAPS):
            self.assertIn("maps/Blitz should be maps/SuperCrossRoads4", _meant(Path("game"), "Blitz"))
            self.assertEqual((_meant(Path("game"), "SuperCrossRoads4"), _meant(Path("game"), "Nowhere")), ("", ""))
        with mock.patch("rusemod.terrain.map_list", side_effect=FileNotFoundError):
            self.assertEqual(_meant(Path("game"), "Blitz"), "")

    def test_new_roads_added_and_taken_back(self):
        self.assertEqual(self.api.roads("Blitz"), {"roads": [], "bridge": None, "saved": None, "mod": None})
        folder = Path(self.api.new_mod("x")["current"])
        file = folder / "maps" / "Blitz" / "roads.toml"
        self.assertEqual(self.api.road_add("Blitz", [[1, 2], [3000.5, 4]])["count"], 1)
        self.assertEqual(self.api.road_add("Blitz", [[10, 20], [30, 40], [50, 60]], 0)["count"], 2)
        got = self.api.roads("Blitz")
        self.assertEqual([r["points"] for r in got["roads"]], [[[1.0, 2.0], [3000.5, 4.0]], [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]]])
        self.assertEqual([r["join"] for r in got["roads"]], [3000.0, 0.0])
        self.assertEqual(got["saved"], str(file))
        for bad in ([[1, 2]], [[1, 2], ["a", 3]], "nope", [[1, 2]] * 5001):
            with self.assertRaises(StudioError):
                self.api.road_add("Blitz", bad)
        self.assertEqual(self.api.road_undo("Blitz"), {"count": 1, "removed": 1, "saved": str(file)})
        self.assertEqual(self.api.road_undo("Blitz", 5), {"count": 0, "removed": 1, "saved": None})
        self.assertFalse(file.exists())

    def test_a_water_stroke_keeps_its_level(self):  # Studio 0.7.0 and before saved it without, then couldn't read it
        self.api.new_mod("x")
        lake = {"brush": "water", "x": 1.0, "y": 2.0, "radius": 3.0, "level": 450.0}
        self.api.terrain_add("TwoIslands", [lake])
        self.assertEqual(self.api.terrain("TwoIslands")["strokes"][0]["level"], 450.0)

    def test_a_file_it_cant_read_back_is_never_saved(self):
        folder = Path(self.api.new_mod("x")["current"])
        with mock.patch("ruse_studio.api.strokes_toml", return_value='[[stroke]]\nbrush = "water"\nx = 1.0\ny = 2.0\nradius = 3.0\n'):
            with self.assertRaisesRegex(StudioError, "can't read back.*needs level"):
                self.api.terrain_add("TwoIslands", [self.HILL])
        self.assertFalse((folder / "maps" / "TwoIslands" / "terrain.toml").exists())

    def test_the_mod_check_lists_every_broken_file_and_sets_them_aside(self):
        self.assertEqual(self.api.check_mod(), {"mod": None, "problems": []})
        folder = Path(self.api.new_mod("x")["current"])
        self.assertEqual(self.api.check_mod()["problems"], [])
        lake = folder / "maps" / "Blitz" / "terrain.toml"
        lake.parent.mkdir(parents=True)
        lake.write_text('[[stroke]]\nbrush = "water"\nx = 1.0\ny = 2.0\nradius = 3.0\n', encoding="utf-8")
        spawns = folder / "maps" / "TwoIslands" / "scenario.toml"
        spawns.parent.mkdir(parents=True)
        spawns.write_text("[[wrong]]\n", encoding="utf-8")
        (folder / "maps" / "TwoIslands" / "notes.toml").write_text("not = [a map file", encoding="utf-8")
        got = self.api.check_mod()["problems"]
        self.assertEqual([(p["file"], p["set_aside"]) for p in got],  # both named, nothing about the notes
                         [("maps/Blitz/terrain.toml", True), ("maps/TwoIslands/scenario.toml", True)])
        self.assertIn("the water brush needs level", got[0]["problem"])
        self.assertIn("unknown key 'wrong'", got[1]["problem"])
        after = self.api.set_aside("maps/Blitz/terrain.toml")
        self.assertEqual(Path(after["kept"]).name, "terrain.broken.toml")
        self.assertEqual([p["file"] for p in after["problems"]], ["maps/TwoIslands/scenario.toml"])
        self.assertEqual(self.api.set_aside("maps/TwoIslands/scenario.toml")["problems"], [])
        for bad in ("mod.toml", "maps/Blitz/terrain.broken.toml", "../x/maps/Blitz/terrain.toml", "maps/Nope/movement.toml"):
            with self.assertRaisesRegex(StudioError, "isn't one of this mod's map files"):
                self.api.set_aside(bad)


class ScenarioEdits(WithMod):
    """The map view's Move and Add unit tools: a starting point moved, units spawned, saved in the mod's
    maps/<map>/scenario.toml and shown on the map as the mod leaves it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_scenario import scenario
        folder = "test/map/blitz/".replace("/", "\\")
        (cls.game / "Data" / "PC" / "190852" / "DataMap_Win.dat").write_bytes(
            make_edat([("dir", folder, [("file", "leveldesign.scenario", scenario())])]))

    def setUp(self):
        super().setUp()
        menus = mock.patch("rusemod.scenario.kinds_of", return_value={})  # no map list in the made-up game (Kinds)
        menus.start()
        self.addCleanup(menus.stop)
        self.mod = Path(self.api.new_mod("Scenario edits")["current"])
        self.file = self.mod / "maps" / "Blitz" / "scenario.toml"

    def items(self, res):
        return next(s for s in res["scenarios"] if s["file"] == "leveldesign.scenario")["items"]

    def test_move_and_put_back(self):
        start = self.items(self.api.map_scenarios("Blitz"))[0]
        self.assertEqual((start["kind"], start["item"]), ("StartingPoint", 0))
        moved = self.items(self.api.scenario_move("Blitz", "leveldesign.scenario", 0, 111.0, 222.0))[0]
        self.assertEqual((moved["x"], moved["y"], moved["moved"]), (111.0, 222.0, True))
        self.items(self.api.scenario_move("Blitz", "leveldesign.scenario", 0, 333.0, 444.0))  # a second move replaces it
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual([(m["item"], m["x"], m["y"]) for m in data["move"]], [(0, 333.0, 444.0)])
        back = self.items(self.api.scenario_put_back("Blitz", "leveldesign.scenario", 0))[0]
        self.assertEqual((back["x"], back["y"], "moved" in back), (start["x"], start["y"], False))
        self.assertFalse(self.file.exists())  # nothing left to change: the file goes
        with self.assertRaisesRegex(StudioError, "no item 9"):
            self.api.scenario_move("Blitz", "leveldesign.scenario", 9, 0.0, 0.0)
        with self.assertRaisesRegex(StudioError, "no scenario"):
            self.api.scenario_move("Blitz", "other.scenario", 0, 0.0, 0.0)

    def test_spawn_move_and_remove(self):
        before = len(self.items(self.api.map_scenarios("Blitz")))
        with self.assertRaisesRegex(StudioError, "no class name"):  # the made-up game's units have none
            self.api.scenario_spawn("Blitz", "leveldesign.scenario", M4, 5.0, 6.0, 2)
        shown = {"values": [("ClassNameForDebug", 0, "Unit_M4_Sherman")]}
        with mock.patch("rusemod.index.Index.show", return_value=shown):
            items = self.items(self.api.scenario_spawn("Blitz", "leveldesign.scenario", M4, 5.0, 6.0, 2))
        mine = items[-1]
        self.assertEqual(len(items), before + 1)
        self.assertEqual((mine["what"], mine["camp"], mine["x"], mine["y"], mine["mine"], mine["spawn"]),
                         ("Unit_M4_Sherman", 2, 5.0, 6.0, True, 0))
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual([(s["what"], s["camp"]) for s in data["spawn"]], [("Unit_M4_Sherman", 2)])
        mine = self.items(self.api.scenario_move_spawn("Blitz", 0, 7.0, 8.0))[-1]
        self.assertEqual((mine["x"], mine["y"], mine["camp"]), (7.0, 8.0, 2))
        self.assertEqual(len(self.items(self.api.scenario_remove_spawn("Blitz", 0))), before)
        self.assertFalse(self.file.exists())
        with self.assertRaisesRegex(StudioError, "isn't in the mod"):
            self.api.scenario_remove_spawn("Blitz", 0)

    def test_a_formation_in_one_go(self):
        before = len(self.items(self.api.map_scenarios("Blitz")))
        shown = {"values": [("ClassNameForDebug", 0, "Unit_M4_Sherman")]}
        with mock.patch("rusemod.index.Index.show", return_value=shown):
            items = self.items(self.api.scenario_spawn_many("Blitz", "leveldesign.scenario", M4,
                                                            [[1, 2], [3, 4], [5, 6]], None, 1.5))
            mine = items[before:]
            self.assertEqual([(m["x"], m["y"], m["camp"], m["spawn"]) for m in mine],
                             [(1.0, 2.0, -1, 0), (3.0, 4.0, -1, 1), (5.0, 6.0, -1, 2)])  # no side: neutral
            data = tomllib.loads(self.file.read_text(encoding="utf-8"))
            self.assertEqual({s["rotation"] for s in data["spawn"]}, {1.5})
            for bad in ([], [[1, 2]] * 51, [[1, "a"]], [[1, float("nan")]], [[1, 2, 3]]):
                with self.assertRaisesRegex(StudioError, "places|pairs"):
                    self.api.scenario_spawn_many("Blitz", "leveldesign.scenario", M4, bad)
        self.assertEqual(len(self.items(self.api.map_scenarios("Blitz"))), before + 3)

    def test_neutral_by_default_and_only_neutral_on_a_skirmish_map(self):
        """A skirmish game spawns only neutral items (camp -1): the tool's default is neutral, and a skirmish
        scenario refuses a player's side; a depot is spawned under the class path the shipped depots use."""
        from rusemod.scenario import DEPOT, Spawn
        shown = {"values": [("ClassNameForDebug", 0, "Unit_M4_Sherman")]}
        with mock.patch("rusemod.index.Index.show", return_value=shown):
            self.assertEqual(self.items(self.api.scenario_spawn("Blitz", "leveldesign.scenario", M4, 5.0, 6.0))[-1]
                             ["camp"], -1)
            skirmish = {"leveldesign.scenario": [{"name": "(2) Blitz", "kind": "skirmish", "key": None}]}
            self.api._sceneries.clear()
            with mock.patch("rusemod.scenario.kinds_of", return_value=skirmish):
                with self.assertRaisesRegex(StudioError, "skirmish game spawns only neutral items"):
                    self.api.scenario_spawn("Blitz", "leveldesign.scenario", M4, 5.0, 6.0, 1)
                self.api.scenario_spawn("Blitz", "leveldesign.scenario", M4, 7.0, 8.0, -1)
            self.api._sceneries.clear()
        with mock.patch("rusemod.index.Index.show", return_value={"values": [("ClassNameForDebug", 0, "DalleBatimentDepot")]}):
            self.api.scenario_spawn("Blitz", "leveldesign.scenario", M4, 9.0, 9.0)
        data = tomllib.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual([s.get("camp") for s in data["spawn"]], [-1, -1, -1])
        self.assertEqual(Spawn("x.scenario", data["spawn"][-1]["what"], 0.0, 0.0).class_path, DEPOT)


class MapDocks(WithMod):
    """The map editor's Bridges dock (map_bridges, bridge_add) and "Check this map" (map_check), on the made-up game:
    its map's bridge kinds and the check stood in for (the made-up game has no map pack)."""

    KINDS = {"kinds": [
        {"type": "TypeWarrior/Pont_TangeantFloor", "name": "Pont_TangeantFloor", "placed": 3, "length": 26000,
         "turn": 90.0, "least": 23400, "most": 52000, "lift": -650.0, "roads": True},
        {"type": "TypeWarrior/Pont_Old", "name": "Pont_Old", "placed": 0, "length": 26000, "turn": 90.0,
         "least": 23400, "most": 52000, "lift": 0.0, "roads": False}], "kind": "TypeWarrior/Pont_TangeantFloor"}

    def wait(self, job_id):
        for _ in range(200):
            got = self.api.job(job_id)
            if got["state"] != "running":
                return got
            time.sleep(0.02)
        self.fail("the job never ended")

    def test_a_bridge_placed_by_hand(self):
        with mock.patch.object(StudioApi, "map_bridges", return_value=self.KINDS):
            with self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
                self.api.bridge_add("Blitz", "TypeWarrior/Pont_TangeantFloor", 1000, 2000, 0, 30000)
            folder = Path(self.api.new_mod("x")["current"])
            got = self.api.bridge_add("Blitz", "TypeWarrior/Pont_TangeantFloor", 1000.4, 2000, 0, 39000)
            self.assertEqual(got["object"], {"type": "TypeWarrior/Pont_TangeantFloor", "x": 1000, "y": 2000, "turn": 90.0,
                                             "size": 1.0, "solid": False, "stretch": 1.5, "lift": -650.0})
            self.assertEqual((got["count"], got["saved"]), (1, str(folder / "maps" / "Blitz" / "scenery.toml")))
            self.assertEqual(self.api.scenery("Blitz")["objects"], [got["object"]])  # read back as saved
            for args, said in ((("TypeWarrior/Chene_02", 0, 0, 0, 30000), "isn't one of this map's own bridge kinds"),
                               (("TypeWarrior/Pont_Old", 0, 0, 0, 30000), "places no Pont_Old of its own"),
                               (("TypeWarrior/Pont_TangeantFloor", 0, 0, 0, 60000), "stretches from 90 to 200 m"),
                               (("TypeWarrior/Pont_TangeantFloor", "a", 0, 0, 30000), "are numbers"),
                               (("TypeWarrior/Pont_TangeantFloor", 0, float("nan"), 0, 30000), "are numbers")):
                with self.assertRaisesRegex(StudioError, said):
                    self.api.bridge_add("Blitz", *args)
            self.assertEqual(self.api.scenery_undo("Blitz")["count"], 0)  # Undo takes it back like any placed object

    def test_check_this_map(self):
        with self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
            self.api.map_check("SuperCrossRoads4")
        folder = Path(self.api.new_mod("x")["current"])
        with self.assertRaisesRegex(StudioError, "isn't a map's pack name"):
            self.api.map_check("../x")
        found = [{"key": "join", "level": "info", "say": "mc_road_unjoined", "data": {"road": 1, "x": 5, "y": 6},
                  "fix": None}]
        go = threading.Event()

        def check(game, mod, pack, say):
            self.assertEqual((Path(game), Path(mod), pack), (self.game, folder, "SuperCrossRoads4"))
            say("roads: SuperCrossRoads4")
            go.wait(5)
            return found
        with mock.patch("rusemod.mapcheck.check_map", side_effect=check):
            first = self.api.map_check("SuperCrossRoads4")["job"]
            self.assertEqual(self.api.map_check("SuperCrossRoads4")["job"], first)  # asked twice: run once
            go.set()
            done = self.wait(first)
        self.assertEqual(done["state"], "done", done)
        self.assertEqual(done["result"], {"pack": "SuperCrossRoads4", "findings": found})
        self.assertEqual(done["lines"], ["roads: SuperCrossRoads4"])
        with mock.patch("rusemod.mapcheck.check_map", side_effect=OSError("the disk is full")):
            failed = self.wait(self.api.map_check("SuperCrossRoads4")["job"])  # a new one once the last has ended
        self.assertEqual((failed["state"], failed["message"]), ("failed", "the disk is full"))

    def test_the_docks_words_match_the_builds(self):
        from rusemod import mapcheck
        from rusemod.bridges import no_kind_note
        words = _words()
        self.assertEqual({k: words[k]["us"] for k in mapcheck.WORDS}, mapcheck.WORDS)  # the findings' own words
        self.assertEqual(words["bridges_none"]["us"].replace("{n}", "2"), no_kind_note(2))  # the build's own note


class Troubleshooter(WithMod):
    """The troubleshooter's two calls (what it checks is rusemod.doctor's: tests/test_doctor.py)."""

    def test_findings_and_a_report_for_a_bug_report(self):
        res = self.api.troubleshoot()
        got = {f["key"]: f for f in res["findings"]}
        self.assertLessEqual({"game", "steam", "running", "drive", "leftovers", "write"}, set(got))
        self.assertEqual((got["game"]["level"], got["game"]["data"]), ("ok", {"path": str(self.game)}))
        self.assertEqual(got["steam"]["say"], "doc_steam_ok")  # the Studio's own Steam check (the test's here)
        self.assertEqual(got["leftovers"]["level"], "ok")
        self.assertEqual(got["write"]["data"], {"path": str(self.home / "copies")})  # where Test in game builds
        self.assertLessEqual({f["say"] for f in res["findings"]}, set(_words()))
        self.assertTrue(res["report"].startswith(f"RUSE Studio {__version__}, Windows "), res["report"])
        self.assertIn(f"[ok] game: doc_game_ok (path={private_paths_out(str(self.game))})", res["report"])
        (self.home / "copies" / "studio-x.old").mkdir(parents=True)  # a copy an earlier test couldn't remove
        left = {f["key"]: f for f in self.api.troubleshoot()["findings"]}["leftovers"]
        self.assertEqual((left["fix"], left["data"]), ("clear_leftovers", {"names": "studio-x.old"}))
        self.assertEqual(self.api.troubleshoot_fix("clear_leftovers"), {"done": 1, "left": []})
        self.assertFalse((self.home / "copies" / "studio-x.old").exists())

    def test_what_is_refused(self):
        for action in ("format the drive", "choose_game"):  # choosing the game folder is the window's own
            with self.assertRaisesRegex(StudioError, "no fix called"):
                self.api.troubleshoot_fix(action)
        from rusemod.webui import Job
        busy = Job()  # a test being built: its half-built copy looks like a leftover
        self.api._jobs[busy.id] = busy
        self.api._test_job = busy.id
        with self.assertRaisesRegex(StudioError, "being built"):
            self.api.troubleshoot_fix("clear_leftovers")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RUSE_GAME", None)
            no_game = StudioApi(index_path=self.index, find=lambda: None, home=self.home,
                                starter=Starter(steam_running=lambda: True))
            with self.assertRaisesRegex(StudioError, "couldn't find R.U.S.E."):
                no_game.troubleshoot_fix("close_game")
            found = no_game.troubleshoot()["findings"]
        self.assertEqual([f["key"] for f in found], ["game", "steam", "running"])  # no place for copies yet
        self.assertEqual((found[0]["level"], found[0]["fix"]), ("fail", "choose_game"))


class CleanBackup(unittest.TestCase):
    """The clean game backup in the Studio's Settings (what it does is rusemod.backup's: tests/test_backup.py), on a
    made-up game of its own: a restore writes into it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        (self.game / "Data").mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        (self.game / "Data" / "lang.ini").write_text("en-US", encoding="utf-8")
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        self.urls = []
        starter = Starter(open_url=self.urls.append, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(game_dir=self.game, home=root / "home", starter=starter, instances=root / "copies",
                             backups=root / "backups")

    def tearDown(self):
        self.tmp.cleanup()

    def wait(self, job_id):
        end = time.time() + 10
        while time.time() < end:
            j = self.api.job(job_id)
            if j["state"] != "running":
                return j
            time.sleep(0.02)
        raise AssertionError("the job didn't finish")

    def test_make_check_and_restore(self):
        self.assertEqual((self.api.backup_status()["current"], self.api.backup_status()["build"]), (None, "24687178"))
        made = self.wait(self.api.backup_make()["job"])
        self.assertEqual((made["state"], made["result"]["files"]), ("done", 2), made)
        self.assertTrue(self.api.backup_status()["current"]["matches"])
        (self.game / "Data" / "lang.ini").unlink()
        found = self.wait(self.api.backup_check()["job"])["result"]
        self.assertEqual((found["changed"], found["missing"], found["added"]), ([], ["Data/lang.ini"], []))
        with mock.patch("rusemod.winfiles.processes", return_value=[]):
            done = self.wait(self.api.backup_restore()["job"])
        self.assertEqual((done["state"], done["result"]["restored"]), ("done", 1), done)
        self.assertEqual((self.game / "Data" / "lang.ini").read_text(encoding="utf-8"), "en-US")
        self.assertEqual(self.api.steam_verify(), {"opened": "steam://validate/21970"})
        self.assertEqual(self.urls, ["steam://validate/21970"])  # through the Studio's own way of opening links

    def test_the_installers_ask_makes_it_on_the_first_start(self):
        """The installer's task "Keep a clean copy of my game's files" leaves `make-backup` in the platform folder:
        the window makes the backup on its next start (backup_requested), and the mark goes once one is made."""
        from rusemod.backup import REQUESTED
        self.assertEqual(self.api.backup_requested(), {"make": False})  # nothing asked
        mark = Path(self.tmp.name) / "home" / REQUESTED
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.write_text("Asked for in the installer.", encoding="utf-8")
        self.assertEqual(self.api.backup_requested(), {"make": True})
        self.assertTrue(mark.is_file())  # kept until the backup exists
        made = self.wait(self.api.backup_make()["job"])
        self.assertEqual(made["state"], "done", made)
        self.assertFalse(mark.exists())
        self.assertEqual(self.api.backup_requested(), {"make": False})
        mark.write_text("Asked again by the other app's installer.", encoding="utf-8")
        self.assertEqual(self.api.backup_requested(), {"make": False})  # the build has its backup already
        self.assertFalse(mark.exists())

    def test_the_installer_offers_it_with_why(self):
        """Beside the desktop icon, in every installer language, with why under the list; asked only when the player
        saw the question (never on an app's own silent update)."""
        script = (Path(__file__).parents[1] / "installers" / "installer.iss").read_text(encoding="utf-8-sig")
        self.assertIn('Name: "gamebackup"; Description: "{cm:BackupTask}"; GroupDescription: "{cm:BackupGroup}"', script)
        languages = re.findall(r'^Name: "(\w+)"; MessagesFile:', script, re.M)
        self.assertEqual(len(languages), 9)
        for lang in languages:
            for key in ("BackupGroup", "BackupTask", "BackupWhy"):
                self.assertRegex(script, rf"(?m)^{lang}\.{key}=\S")
        self.assertIn("CustomMessage('BackupWhy')", script)
        self.assertIn("(not WizardSilent) and WizardIsTaskSelected('gamebackup')", script)
        from rusemod import home
        from rusemod.backup import REQUESTED
        self.assertIn("ExpandConstant('{localappdata}\\RUSE Mod Platform')", script)  # the apps' own folder
        self.assertIn('/ "RUSE Mod Platform"', Path(home.__file__).read_text(encoding="utf-8"))
        self.assertIn(f"\\{REQUESTED}'", script)

    def test_a_test_and_a_restore_wait_for_each_other(self):
        from rusemod.backup import BackupError
        from rusemod.webui import Job
        self.wait(self.api.backup_make()["job"])
        self.api.new_mod("Waiting")
        testing = Job()  # a Test in game building its copy from the game's files
        self.api._jobs[testing.id] = testing
        self.api._test_job = testing.id
        with self.assertRaisesRegex(BackupError, "A test is being built"):
            self.api.backup_restore()
        testing.state = "done"
        restoring = Job()
        restoring.kind = "restore"
        self.api._jobs[restoring.id] = restoring
        self.api._backup_job = restoring.id
        with self.assertRaisesRegex(StudioError, "being restored"):
            self.api.test_in_game()
        with self.assertRaisesRegex(BackupError, "busy"):
            self.api.backup_check()

    def test_the_launcher_at_work_on_the_game_is_waited_for(self):
        from rusemod import backup
        folder = Path(self.tmp.name) / "backups"
        self.assertEqual(self.wait(self.api.backup_make()["job"])["state"], "done")
        self.api.new_mod("Waiting")
        with backup._busy(folder, "restore"):  # the Launcher restoring the game's files: a Test in game waits
            j = self.wait(self.api.test_in_game()["job"])
        self.assertEqual((j["state"], j["message"]), ("failed", "The game's files are being restored: wait for it to "
                                                                "finish."))
        self.assertFalse((Path(self.tmp.name) / "copies").exists())  # nothing was built
        with backup.reading(folder):  # the Launcher building a Play's copy: a restore waits
            with mock.patch("rusemod.winfiles.processes", return_value=[]):
                j = self.wait(self.api.backup_restore()["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("A modded copy of the game is being built", j["message"])
        self.assertEqual([p.name for p in folder.iterdir()], ["24687178"])  # nothing left behind


class ZonesOnTheGround(unittest.TestCase):
    def test_a_zone_follows_hills_and_pits(self):
        """A scenario's zones are drawn as triangles split to about a ground cell and a half, each corner on the
        ground: drawn from the outline alone, a zone was a flat sheet a hill painted inside it poked through (the
        owner's D-Day hill, 2026-10-01). The split itself was checked in the Studio's page: every edge under the
        step, the area and the outline kept."""
        maps = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "maps.js").read_text(encoding="utf-8")
        draw = maps[maps.index("function drawScenario()"):]
        draw = draw[:draw.index("\n}\n")]
        self.assertIn("const step = 1.5 * Math.max(grid.sx, grid.sy);", draw)
        self.assertIn("drapeZone(z.points, z.triangles, step)", draw)
        self.assertIn("g.setIndex(tris);", draw)
        self.assertNotIn("g.setIndex(z.triangles)", draw)
        drape = maps[maps.index("function drapeZone("):]
        drape = drape[:drape.index("\n}\n")]
        self.assertIn("mid.get(key)", drape)  # an edge's middle made once: no cracks between two triangles


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
        used = set(re.findall(r"\b(?:w|state\.words|mv\.words)\.([a-z_]+)", app))
        used |= {"all", "ground", "infantry", "air", "buildings", "not_stable"}  # looked up by key
        from ruse_studio.api import AMMO_GROUP_ORDER, GROUPS
        used |= {"group_" + g for g in GROUPS + AMMO_GROUP_ORDER}  # each type's name too
        maps = (ui / "maps.js").read_text(encoding="utf-8")  # each brush's name is looked up by key
        used |= {"brush_" + name for name in re.findall(r'^  (\w+): \["\w+", "\w+", -?1, (?:true|false),', maps, re.M)}
        self.assertEqual(len(used & {"brush_hill", "brush_ramp", "brush_cover", "brush_town", "brush_block_vehicles"}), 5)
        self.assertGreater(len(used), 25)
        self.assertEqual(sorted(used - set(_words())), [])

    def test_each_word_has_the_same_blanks_in_every_language(self):  # a {name} lost in a translation stays empty
        for name, entry in _words().items():
            blanks = {lang: set(re.findall(r"\{(\w+)\}", text)) for lang, text in entry.items()}
            self.assertEqual([lang for lang, b in blanks.items() if b != blanks["us"]], [], name)

    def test_every_troubleshooter_word_exists(self):  # the dialog looks them up by the findings' own keys
        from rusemod import doctor
        source = Path(doctor.__file__).read_text(encoding="utf-8")
        says = set(re.findall(r'"(doc_\w+)"', source))
        fixes = set(re.findall(r'_finding\("\w+", "\w+", "doc_\w+", "(\w+)"', source))
        self.assertGreater(len(says), 15)
        self.assertEqual(fixes, {"choose_game", "close_game", "clear_leftovers"})  # a new one: the window shows it
        self.assertLessEqual(set(StudioApi.FIXES), fixes)
        self.assertEqual(sorted((says | {"doc_fix_" + f for f in fixes}) - set(_words())), [])


if __name__ == "__main__":
    unittest.main()


def mapv(*pairs):
    return val(0x12, struct.pack("<I", len(pairs)) + b"".join(k + v for k, v in pairs))


# Two tanks whose models bind their gun's shot (muzzle flash and sound) the game's way: the model has a part per
# weapon EffectTag (SousElements: weapon_effet_tag1), and inside it a map from an event (tir; tir_move, firing on the
# move) to a call of an FX_Tir_* effect. The Panzer fires Ammo_Canon_75 with a medium shot, the Tiger Ammo_Canon_88
# with a heavy one. classes: 0 unit, 1 model, 2 model part, 3 mounted weapon, 4 ammo, 5 call, 6 effect
SHOTS = make_ndf(
    objects=[(0, [(0, ref(2, 3)), (1, ref(4, 1))]),                                          # 0 Panzer
             (0, [(0, ref(3, 3)), (1, ref(7, 1))]),                                          # 1 Tiger
             (3, [(2, s(0)), (3, ref(10, 4))]),                                              # 2 Panzer's gun
             (3, [(2, s(0)), (3, ref(11, 4))]),                                              # 3 Tiger's gun
             (1, [(4, mapv((s(0), ref(5, 2))))]),                                            # 4 Panzer's model
             (2, [(5, mapv((s(1), ref(6, 2))))]),                                            # 5 its turret
             (2, [(6, mapv((s(2), ref(12, 5)), (s(3), ref(13, 5))))]),                       # 6 the turret's shots
             (1, [(4, mapv((s(0), ref(8, 2))))]),                                            # 7 Tiger's model
             (2, [(5, mapv((s(1), ref(9, 2))))]),                                            # 8 its turret
             (2, [(6, mapv((s(2), ref(14, 5))))]),                                           # 9 its shot
             (4, [(7, u32(1001))]),                                                          # 10 Ammo 75
             (4, [(7, u32(1002))]),                                                          # 11 Ammo 88
             (5, [(8, ref(15, 6))]), (5, [(8, ref(16, 6))]), (5, [(8, ref(17, 6))]),        # 12-14 calls
             (6, []), (6, []), (6, [])],                                                     # 15-17 effects
    classes=["TUniteAuSolDescriptor", "TGfxDescriptorModele", "TGfxDescriptorModeleSousMobile",
             "TMountedWeaponDescriptor", "TAmmunition", "TActionCall", "TActionDescriptor"],
    props=[("MountedWeapon", 0), ("GfxDescriptor", 0), ("EffectTag", 3), ("Ammunition", 3), ("SousElements", 1),
           ("SousElements", 2), ("BinderEffets", 2), ("AmmunitionId", 4), ("Action", 5)],
    strings=["weapon_effet_tag1", "1", "tir", "tir_move"],
    exports={0: "GFX/Everything/Descriptor_Unit_Panzer_IV_G", 1: "GFX/Everything/Descriptor_Unit_Tiger",
             10: "GFX/Everything/Ammo_Canon_75", 11: "GFX/Everything/Ammo_Canon_88",
             15: "GFX/Everything/FX_Tir_ObusAP_Moyen", 16: "GFX/Everything/FX_Tir_ObusAP_Move_Moyen",
             17: "GFX/Everything/FX_Tir_ObusAP_Lourd"},
    topo=[0, 1, 10, 11, 15, 16, 17])
TIGER = "$/GFX/Everything/Descriptor_Unit_Tiger"


class Shots(unittest.TestCase):
    """A weapon's shot follows its ammo: a gun made to fire another unit's ammo takes that unit's muzzle flash and
    sound (api.set_ammo), in the unit's own model, so no other unit changes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Path(self.tmp.name, "game")
        rev = self.game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "everything.cpp.gladndfbin", SHOTS)]))
        (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
            ("dir", "us\\", [("file", "baseunite.dic", make_dic([(PANZER, "Panzer IV")]))])])]))
        index = build_index(self.game, Path(self.tmp.name, "index.sqlite"), say=lambda line: None)
        self.api = StudioApi(index_path=index, game_dir=self.game, home=Path(self.tmp.name, "home"))

    def tearDown(self):
        self.tmp.cleanup()

    def shots(self, folder):
        """{unit: [the effect each of its shot events plays]} in the mod as built."""
        rev = self.game / "Data" / "PC" / "190852"
        arc = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        nd = Ndf(new.read(new.find("everything.cpp.gladndfbin")))
        from rusemod.ndf import local_ref, sub_values
        names = [p for p, _ in nd.props]
        objs = [{names[pi]: v for pi, v in o.props} for o in nd.objects]
        exp = {p: i for i, p in nd.exports.items()}
        out = {}
        for unit in (PANZER_IV, TIGER):
            model = local_ref(objs[exp[unit]]["GfxDescriptor"])
            turret = local_ref(sub_values(objs[model]["SousElements"])[1])
            part = local_ref(sub_values(objs[turret]["SousElements"])[1])
            calls = sub_values(objs[part]["BinderEffets"])[1::2]
            out[unit] = [nd.exports[local_ref(objs[local_ref(c)]["Action"])].rsplit("/", 1)[-1] for c in calls]
        return out

    def test_the_shot_follows_the_ammo(self):
        folder = Path(self.api.new_mod("Guns")["current"])
        mount = PANZER_IV + ":MountedWeapon"
        self.assertEqual(self.api.weapons(PANZER_IV)["weapons"][0]["shot"], "ObusAP Moyen")
        saved = self.api.set_ammo(PANZER_IV, mount, AMMO_88)
        self.assertEqual(saved["shot"], "ObusAP Lourd")
        self.assertEqual(self.api.weapons(PANZER_IV)["weapons"][0]["shot"], "ObusAP Lourd")
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("\npatch $/GFX/Everything/Descriptor_Unit_Panzer_IV_G:GfxDescriptor.SousElements[0].v"
                      ".SousElements[0].v.BinderEffets[0]\n(\n    v = $/GFX/Everything/Descriptor_Unit_Tiger:"
                      "GfxDescriptor.SousElements[0].v.SousElements[0].v.BinderEffets[0].v\n)\n", rndf)
        # firing on the move too: the Tiger has no shot of its own for it, so its one shot
        self.assertEqual(self.shots(folder), {PANZER_IV: ["FX_Tir_ObusAP_Lourd", "FX_Tir_ObusAP_Lourd"],
                                              TIGER: ["FX_Tir_ObusAP_Lourd"]})
        self.api.set_ammo(PANZER_IV, mount, AMMO_75)  # the game's own ammo again: its own shot again
        self.assertNotIn("BinderEffets", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        self.assertEqual(self.api.weapons(PANZER_IV)["weapons"][0]["shot"], "ObusAP Moyen")
