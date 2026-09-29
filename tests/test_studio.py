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
        app = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\b(?:w|state\.words)\.([a-z_]+)", app))
        used |= {"all", "ground", "infantry", "air", "buildings", "not_stable"}  # looked up by key
        self.assertGreater(len(used), 25)
        self.assertEqual(sorted(used - set(_words())), [])


if __name__ == "__main__":
    unittest.main()
