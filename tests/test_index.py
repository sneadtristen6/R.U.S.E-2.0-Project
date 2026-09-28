"""The game index (PLAN.md L2) on a made-up game: every pack, file, object, reference and text, and its questions."""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod.cli import main
from rusemod.dic import name_to_key
from rusemod.index import Index, build_index


def i32(v):
    return val(0x02, struct.pack("<i", v))


def ref(i, cls=0):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def imp(k):
    return val(0x09, struct.pack("<II", 0xAAAAAAAA, k))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


# classes: 0 TUnit, 1 TWeaponA, 2 TWeaponB, 3 TAmmo, 4 TLeftover
# props: 0 Price(TUnit), 1 Weapons(TUnit), 2 Ammo(TWeaponA), 3 Ammo(TWeaponB), 4 Power(TAmmo), 5 Icon(TUnit),
#        6 Name(TUnit), 7 Menu(TUnit), 8 Ammo(TUnit)
SHERMAN = name_to_key("SHERMAN")
UNITS = make_ndf(
    objects=[
        (0, [(0, lst(i32(30), i32(35))), (1, lst(ref(1, 1), ref(2, 2))), (5, val(0x1C, struct.pack("<I", 0))),
             (6, val(0x1D, struct.pack("<Q", SHERMAN))), (7, imp(0))]),          # 0 A (named)
        (1, [(2, ref(3, 3))]),                                                      # 1 A's weapon A
        (2, [(3, ref(3, 3))]),                                                      # 2 A's weapon B
        (3, [(4, i32(40))]),                                                        # 3 ammo, shared by A and B
        (0, [(0, lst(i32(10), i32(12))), (8, ref(3, 3))]),                          # 4 B (named)
        (4, [(4, i32(1))]),                                                         # 5 reached by no named object
    ],
    classes=["TUnit", "TWeaponA", "TWeaponB", "TAmmo", "TLeftover"],
    props=[("Price", 0), ("Weapons", 0), ("Ammo", 1), ("Ammo", 2), ("Power", 3), ("Icon", 0), ("Name", 0),
           ("Menu", 0), ("Ammo", 0), ("Power", 4)],
    strings=["GameData:\\Gfx\\Icons\\A.tgv"], exports={0: "A", 4: "B"}, imports=["Menus/Armour"], topo=[0, 4])
MENUS = make_ndf(objects=[(0, [(0, i32(1))])], classes=["TMenu"], props=[("Slots", 0)], exports={0: "Menus/Armour"})


def write(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (root / "Maps" / "PC").mkdir(parents=True)
    nested = make_edat([("file", "eugen.xyz", b"python bytecode")])
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([
        ("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", UNITS),
                                               ("file", "everything_debuginfo.cpp.gladndfbin", UNITS),
                                               ("file", "menus.cpp.gladndfbin", MENUS)])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([
        ("dir", "genpython\\", [("file", "eugen.ipk", nested)]),
        ("dir", "genlocalisation\\ww2\\localisation\\translations\\us\\", [
            ("file", "baseunite.dic", make_dic([(SHERMAN, "M4 Sherman"), (name_to_key("UNUSED"), "Nobody uses me")]))])]))
    (root / "Maps" / "PC" / "DataMapTwoIslands_v09.dat").write_bytes(make_edat([("file", "output\\div_map.tgv_pc", b"map")]))
    (root.parent.parent / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')


class GameIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "steamapps", "common", "R.U.S.E")
        cls.game.mkdir(parents=True)
        write(cls.game)
        cls.path = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)
        cls.ix = Index(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.ix.close()
        cls.tmp.cleanup()

    def test_every_pack_and_file(self):
        counts = self.ix.report()["counts"]
        self.assertEqual((counts["core packs"], counts["map packs"], counts["nested packs"], counts["files"]),
                         ("2", "1", "1", "7"))
        rows = dict(self.ix.db.execute("SELECT location, game_path || ' ' || type || ' ' || IFNULL(map, '') FROM file"))
        self.assertEqual(rows["ZZ_Win.dat!genpython\\eugen.ipk!eugen.xyz"], "eugen.xyz xyz ")
        self.assertEqual(rows["DataMapTwoIslands_v09.dat!output\\div_map.tgv_pc"],
                         "datasmap/output/div_map.tgv_pc tgv_pc TwoIslands")
        self.assertEqual(self.ix.meta()["build"], "24687178")

    def test_stable_addresses(self):
        found = dict(self.ix.find("$/"))
        self.assertEqual(found["$/A:Weapons[class=TWeaponA]"], "TWeaponA")  # a class selector, not a position
        self.assertEqual(found["$/B:Ammo"], "TAmmo")  # shared: through the shortest path
        leftover = self.ix.show("genglad/patchable/gfx/everything.cpp.gladndfbin#5")
        self.assertEqual((leftover["stable"], leftover["class"]), (False, "TLeftover"))
        self.assertEqual(self.ix.report()["counts"]["last-resort addresses"], "2")  # the main file and its copy

    def test_owners_and_what_a_clone_copies(self):
        ammo = self.ix.show("$/B:Ammo")
        self.assertEqual((ammo["shared"], ammo["owners"]), (True, ["$/A", "$/B"]))
        plan = self.ix.clone_plan("$/A")
        self.assertEqual(plan, {"copied": ["$/A:Weapons[class=TWeaponA]", "$/A:Weapons[class=TWeaponB]"],
                                "shared": ["$/B:Ammo"], "references": ["$/Menus/Armour"]})

    def test_where_used_and_what_it_uses(self):
        self.assertEqual(self.ix.used_by("$/B:Ammo"), [("$/A:Weapons[class=TWeaponA]", "Ammo"),
                                                       ("$/A:Weapons[class=TWeaponB]", "Ammo"), ("$/B", "Ammo")])
        self.assertEqual(self.ix.used_by("$/Menus/Armour"), [("$/A", "Menu")])  # through an import, other file
        kinds = [(p, k, t) for p, k, t in self.ix.uses("$/A")]
        self.assertIn(("Icon", "file", "gamedata:/gfx/icons/a.tgv"), kinds)
        self.assertIn(("Name", "text", "SHERMAN"), kinds)
        self.assertEqual(self.ix.where_file("icons"), [("$/A", "Icon", "gamedata:/gfx/icons/a.tgv")])
        counts = self.ix.report()["counts"]
        self.assertEqual((counts["imports"], counts["imports resolved"]), ("2", "2"))

    def test_numbers_and_texts(self):
        self.assertEqual(self.ix.filter("TUnit", "Price[0]", ">", 20), [("$/A", 30.0)])
        self.assertEqual(self.ix.filter("TUnit", "Price[1]", "<=", 12), [("$/B", 12.0)])
        with self.assertRaises(ValueError):
            self.ix.filter("TUnit", "Price[0]", "; DROP", 1)
        self.assertEqual(self.ix.texts("sherman"), [("SHERMAN", "baseunite", "M4 Sherman")])
        self.assertEqual(self.ix.text_used_by("SHERMAN"), [("$/A", "Name")])
        self.assertEqual(self.ix.unused_texts(), [("UNUSED", "baseunite", "Nobody uses me")])
        seen = self.ix.db.execute("SELECT count, min, max FROM prop_seen WHERE class='TAmmo' AND prop='Power'").fetchone()
        self.assertEqual(seen, (2, 40.0, 40.0))

    def test_ruse_index_commands(self):
        env = {"RUSE_PLATFORM_HOME": str(Path(self.tmp.name, "home"))}
        with mock.patch.dict(os.environ, env):
            code, out = run_cli("--game", str(self.game), "index", "build")
            self.assertEqual(code, 0, out)
            self.assertIn("NDF files: 3", out)
            code, out = run_cli("--game", str(self.game), "index", "show", "$/B:Ammo")
            self.assertIn("shared by: $/A, $/B", out)
            self.assertIn("used by: $/B  (Ammo)", out)
            code, out = run_cli("--game", str(self.game), "index", "filter", "TUnit", "Price[0]", ">", "20")
            self.assertIn("$/A  30", out)
            code, out = run_cli("--game", str(self.game), "index", "texts", "sherman")
            self.assertIn("SHERMAN  (baseunite)  M4 Sherman", out)
            code, out = run_cli("--game", str(self.game), "index", "clone", "$/A")
            self.assertIn("shared (stays shared): $/B:Ammo", out)
            code, out = run_cli("--game", str(self.game), "index", "show", "$/Nope")
            self.assertEqual(code, 2)


def run_cli(*argv):
    import contextlib
    import io
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(list(argv))
    return code, out.getvalue()


if __name__ == "__main__":
    unittest.main()
