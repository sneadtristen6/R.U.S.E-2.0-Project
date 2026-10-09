"""Upgrades (the unit page's Upgrade box; LittleGroove's upgrade chains): the unit a unit is researched from, its
research price and time, saved in the mod and built, on a made-up game."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat, Ndf
from rusemod.build import build_pack, load_mod
from rusemod.index import build_index
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import REMOVED, ModEdits


def i32(v):
    return val(0x02, struct.pack("<i", v))


def flag(v):
    return val(0x00, struct.pack("<B", v))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


PROPS = [("Nationalite", 0), ("Factory", 0), ("UpgradeRequire", 0), ("IsUpgrade", 0), ("UpgradePrice", 0),
         ("UpgradeTime", 0), ("ProductionPrice", 0)]
P = {n: i for i, (n, _c) in enumerate(PROPS)}
E = "$/GFX/Everything/"
A, B, C, D, F = (E + n for n in ("Unit_A", "Unit_B", "Unit_C", "Unit_D", "Unit_F"))


def units() -> bytes:
    """A (US, menu 10), B an upgrade of A (researched for 25 over 75 s), C a US unit of its own in menu 10, D a German
    one in menu 10, F a US one in menu 11."""
    objects = [
        (0, [(P["Factory"], i32(10)), (P["ProductionPrice"], i32(20))]),                                    # A
        (0, [(P["Factory"], i32(10)), (P["UpgradeRequire"], ref(0, 0)), (P["IsUpgrade"], flag(1)),
             (P["UpgradePrice"], i32(25)), (P["UpgradeTime"], i32(75)), (P["ProductionPrice"], i32(30))]),  # B
        (0, [(P["Factory"], i32(10)), (P["ProductionPrice"], i32(40))]),                                    # C
        (0, [(P["Nationalite"], i32(1)), (P["Factory"], i32(10)), (P["ProductionPrice"], i32(40))]),        # D
        (0, [(P["Factory"], i32(11)), (P["ProductionPrice"], i32(40))]),                                    # F
    ]
    return make_ndf(objects=objects, classes=["TUniteAuSolDescriptor"], props=PROPS,
                    exports={0: "GFX/Everything/Unit_A", 1: "GFX/Everything/Unit_B", 2: "GFX/Everything/Unit_C",
                             3: "GFX/Everything/Unit_D", 4: "GFX/Everything/Unit_F"}, topo=[0, 1, 2, 3, 4])


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", units())])]))
    (root / "RUSE.exe").write_bytes(b"MZ")


class Upgrades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                             instances=self.home / "copies")

    def names(self, xs):
        return [x["address"] for x in xs]

    def built(self, folder):
        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        nd = Ndf(new.read(new.find("everything.cpp.gladndfbin")))
        return [{nd.prop_name(pi): v for pi, v in o.props} for o in nd.objects]

    def test_where_a_unit_stands(self):
        b = self.api.upgrade(B)
        self.assertEqual((b["parent"]["address"], b["game_parent"]["address"], b["children"]), (A, A, []))
        self.assertEqual(self.names(b["choices"]), [A, C])  # the same nation's, in the same build menu
        self.assertEqual({p: (r["game"], r["value"]) for p, r in b["research"].items()},
                         {"UpgradePrice": (25, None), "UpgradeTime": (75, None)})
        a = self.api.upgrade(A)
        self.assertEqual((a["parent"], self.names(a["children"])), (None, [B]))
        self.assertEqual(self.names(a["choices"]), [C])  # never one of its own upgrades
        page = self.api.unit(B, "base")
        self.assertTrue(page["can_upgrade"])
        rows = {r["prop"]: r for g in page["groups"] for r in g["rows"]}
        for prop in ("IsUpgrade", "UpgradePrice", "UpgradeTime"):  # changed in the Upgrade box, not the table
            self.assertFalse(rows[prop]["editable"], prop)
        self.assertTrue(rows["ProductionPrice"]["editable"])

    def test_a_unit_of_its_own_made_an_upgrade_and_built(self):
        with self.assertRaises(StudioError):
            self.api.set_upgrade(C, A)  # no mod yet
        self.api.new_mod("Chains")
        folder = self.home / "mods" / "chains"
        res = self.api.set_upgrade(C, A)
        self.assertEqual((res["parent"]["address"], res["game_parent"]), (A, None))
        self.assertEqual({p: r["value"] for p, r in res["research"].items()}, {"UpgradePrice": 50, "UpgradeTime": 50})
        self.assertEqual(self.names(self.api.upgrade(A)["children"]), [B, C])
        self.assertEqual(self.api.set_research(C, "UpgradePrice", 79.6)["value"], 80)
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"\npatch {C}\n(\n    IsUpgrade = 1\n    UpgradePrice = 80\n    UpgradeRequire = {A}\n"
                      "    UpgradeTime = 50\n)\n", text)
        c = self.built(folder)[2]
        self.assertEqual(c["IsUpgrade"].tc, 0x00)  # a yes/no, as on the game's upgrades (the class's type)
        self.assertEqual(c["IsUpgrade"].payload, b"\x01")
        self.assertEqual(struct.unpack("<III", c["UpgradeRequire"].payload)[:2], (0xBBBBBBBB, 0))  # A
        self.assertEqual((c["UpgradePrice"].tc, c["UpgradePrice"].scalar(), c["UpgradeTime"].scalar()), (0x02, 80, 50))

    def test_an_upgrade_made_a_unit_of_its_own_and_back(self):
        self.api.new_mod("Chains")
        folder = self.home / "mods" / "chains"
        res = self.api.set_upgrade(B, None)
        self.assertEqual((res["parent"], self.names(self.api.upgrade(A)["children"])), (None, []))
        self.assertIs(ModEdits(folder).get(B, "UpgradeRequire"), REMOVED)  # read back from the file
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"\npatch {B}\n(\n    delete IsUpgrade\n    delete UpgradeRequire\n)\n", text)
        b = self.built(folder)[1]
        self.assertNotIn("UpgradeRequire", b)
        self.assertNotIn("IsUpgrade", b)
        self.assertEqual((b["UpgradePrice"].scalar(), b["UpgradeTime"].scalar()), (25, 75))  # its research stays
        rows = {r["prop"]: r for g in self.api.unit(B, "base")["groups"] for r in g["rows"]}
        self.assertEqual(rows["IsUpgrade"]["edited"], 0)
        self.api.set_upgrade(B, A)  # the game's own parent again: no change left
        self.assertNotIn("patch", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))

    def test_a_new_unit_in_another_menu_leaves_its_parent(self):
        """A new unit put in a menu its source's research parent isn't in becomes a unit of its own: the game looks
        for every unit's parent among its nation's units while it loads and never stops when it isn't there
        (2026-10-09: a T-80 from the Soviet IS-2, researched from the KV-1, in the USA's menu hung the loading
        screen). In the source's own menu it keeps the parent."""
        self.api.new_mod("Chains")
        folder = self.home / "mods" / "chains"
        away = self.api.new_unit(B, "B abroad", 30, nation=1, factory=10)
        self.assertEqual(away["research_parent_dropped"], A)
        self.assertIsNone(self.api.upgrade(away["address"])["parent"])
        self.assertIs(ModEdits(folder).get(away["address"], "UpgradeRequire"), REMOVED)
        home = self.api.new_unit(B, "B at home", 30)
        self.assertIsNone(home["research_parent_dropped"])
        self.assertEqual(self.api.upgrade(home["address"])["parent"]["address"], A)
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        block = text[text.index(f"export {away['address'].rsplit('/', 1)[-1]} is clone"):]
        block = block[:block.index("\n)\n")]
        self.assertIn("delete UpgradeRequire", block)
        self.assertIn("delete IsUpgrade", block)
        block = text[text.index(f"export {home['address'].rsplit('/', 1)[-1]} is clone"):]
        self.assertNotIn("UpgradeRequire", block[:block.index("\n)\n")])

    def test_what_is_refused(self):
        self.api.new_mod("Chains")
        for unit, parent, why in ((C, D, "can't be researched from"),   # another nation
                                  (C, F, "can't be researched from"),   # another build menu
                                  (A, B, "can't be researched from"),   # its own upgrade: a loop
                                  (C, C, "can't be researched from")):
            with self.subTest(unit=unit, parent=parent), self.assertRaisesRegex(StudioError, why):
                self.api.set_upgrade(unit, parent)
        for prop, value, why in (("ProductionPrice", 1, "isn't a research price or time"),
                                 ("UpgradePrice", "lots", "numbers only"), ("UpgradePrice", -5, "below 0")):
            with self.subTest(prop=prop, value=value), self.assertRaisesRegex(StudioError, why):
                self.api.set_research(B, prop, value)
        with self.assertRaisesRegex(StudioError, "isn't a unit"):
            self.api.upgrade(E + "Nothing")
        self.assertFalse((self.home / "mods" / "chains" / "src" / "studio.rndf").is_file())


if __name__ == "__main__":
    unittest.main()
