"""The build menus by their buildings (the owner, 2026-11-11, on the New unit form's Factory list showing "P40 Warhawk,
M3 Stuart, M4 Sherman": "each factory should be called what its building's called ... Factory is a building"). A
building's kind (TypeBatiment) is the Factory number of the units it makes, so each menu is named by the nation's
buildings of that kind, the game's own names: the Headquarters for 3 (the menu of the buildings), the Prototype Base
and the Atomic Center for 12 (one menu: the Atomic Center stands in Nuclear battles, the Prototype Base in 1945 and
Total War ones, read in the game's data 2026-11-11)."""
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

E = "$/GFX/Everything/"
UNITS = [  # (the game's order)
    {"address": E + "Descriptor_Building_Headquarter", "class": "TBatimentDescriptor", "nation": 0, "factory": None, "slot": None, "key": "HQ"},
    {"address": E + "Descriptor_Building_Caserne", "class": "TBatimentDescriptor", "nation": 0, "factory": 3, "slot": 1, "key": "BARRACKS"},
    {"address": E + "Descriptor_Building_ExperimentalFactory", "class": "TBatimentDescriptor", "nation": 0, "factory": 3, "slot": 2, "key": "PROTO"},
    {"address": E + "Descriptor_Building_Usine_Atomique_US", "class": "TBatimentDescriptor", "nation": 0, "factory": 3, "slot": 3, "key": "ATOMIC"},
    {"address": E + "Descriptor_Building_CaserneLeurre", "class": "TBatimentDescriptor", "nation": 0, "factory": 3, "slot": 4, "key": "DECOY"},
    {"address": E + "Descriptor_Building_HeadquarterITA", "class": "TBatimentDescriptor", "nation": 4, "factory": None, "slot": None, "key": "HQ"},
    {"address": E + "Descriptor_Building_Headquarter_M03_Italie", "class": "TBatimentDescriptor", "nation": 4, "factory": None, "slot": None, "key": "HQ"},
    {"address": E + "Descriptor_Unit_M4_Sherman", "class": "TUniteAuSolDescriptor", "nation": 0, "factory": 8, "slot": 2, "key": "M4"},
    {"address": E + "Descriptor_Unit_Jeep", "class": "TUniteAuSolDescriptor", "nation": 0, "factory": 8, "slot": 1, "key": "JEEP"},
    {"address": E + "Descriptor_Unit_Long_Tom_Nuke", "class": "TUniteAuSolDescriptor", "nation": 0, "factory": 12, "slot": 1, "key": "NUKE"},
    {"address": E + "Descriptor_Unit_Odd", "class": "TUniteAuSolDescriptor", "nation": 0, "factory": 7, "slot": 1, "key": "ODD"},
    {"address": E + "Descriptor_Unit_Italy_Tank", "class": "TUniteAuSolDescriptor", "nation": 4, "factory": 10, "slot": 1, "key": "M13"},
    {"address": E + "Descriptor_Building_Pillbox", "class": "TBatimentDescriptor", "nation": 4, "factory": 3, "slot": 1, "key": None}]
KINDS = {"Descriptor_Building_Headquarter": 3, "Descriptor_Building_Caserne": 8, "Descriptor_Building_ExperimentalFactory": 12,
         "Descriptor_Building_Usine_Atomique_US": 12, "Descriptor_Building_CaserneLeurre": 15,
         "Descriptor_Building_HeadquarterITA": 3, "Descriptor_Building_Headquarter_M03_Italie": 3,
         "Descriptor_Building_Pillbox": 14}
TEXTS = {"us": {"HQ": "HEADQUARTERS", "BARRACKS": "BARRACKS ", "PROTO": "PROTOTYPE BASE", "ATOMIC": "ATOMIC CENTER",
                "DECOY": "DECOY BARRACKS", "M4": "M4 SHERMAN", "JEEP": "WILLYS", "NUKE": "NUCLEAR LONG TOM",
                "ODD": "ODD", "M13": "M13/40"},
         "fr": {"HQ": "QUARTIER GÉNÉRAL", "BARRACKS": "CASERNE", "PROTO": "BASE DE PROTOTYPES", "ATOMIC": "CENTRE ATOMIQUE"}}


class GameIndex:
    """The game index as menus reads it: each building's kind (TypeBatiment) and its texts in two languages."""

    def __init__(self):
        self.asked = []

    def show(self, address):
        kind = KINDS.get(address.rsplit("/", 1)[-1])
        if kind is None:   # a unit: shown at every battle date (ShowInMenu), as the hide reads it
            return {"values": [(f"ShowInMenu[{i}]", 1, None) for i in range(5)]}
        return {"values": [("TypeBatiment", kind, None), ("Menu", 1, None)]}

    def names(self, keys, lang):
        self.asked.append(lang)
        return {k: v for k, v in TEXTS.get(lang, {}).items() if k in set(keys)}

    def close(self):
        pass


class Menus(unittest.TestCase):
    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        self.ix = GameIndex()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._open = lambda: self.ix
        self.api._all_units = lambda ix: UNITS
        self.api._names = lambda ix, addresses, lang, new_units=None: {a: a.rsplit("_", 1)[-1] for a in addresses}

    def tearDown(self):
        self.dir.cleanup()

    def factories(self, lang, nation=0):
        return {f["factory"]: f for f in self.api.menus(lang)["nations"][nation]["factories"]}

    def test_each_menu_is_named_by_its_building(self):
        usa = self.factories("us")
        self.assertEqual({f: m["buildings"] for f, m in usa.items()},
                         {3: ["HEADQUARTERS"],                       # the buildings' own menu: the HQ's kind
                          8: ["BARRACKS"],                           # (the game's trailing space taken off)
                          12: ["PROTOTYPE BASE", "ATOMIC CENTER"],   # two buildings, one menu: both, in the game's order
                          7: []})                                    # no building of that kind: nothing made up
        self.assertEqual((usa[8]["units"], usa[8]["count"]), (["Jeep", "Sherman"], 2))  # (its units still come along)
        self.assertNotIn("DECOY BARRACKS", [n for m in usa.values() for n in m["buildings"]])  # a decoy is a kind of its own

    def test_one_name_once_and_a_building_with_no_name(self):
        italy = self.factories("us", 4)
        self.assertEqual(italy[3]["buildings"], ["HEADQUARTERS"])   # two HQs (one a campaign's), one name
        self.assertEqual(italy[10]["buildings"], [])

    def test_in_the_language_shown_else_english(self):
        self.assertEqual(self.factories("fr")[12]["buildings"], ["BASE DE PROTOTYPES", "CENTRE ATOMIQUE"])
        for lang in ("fa", "base"):   # no game texts in Persian; base: the game's English, never a code name
            self.ix.asked.clear()
            self.assertEqual(self.factories(lang)[3]["buildings"], ["HEADQUARTERS"], lang)
            self.assertEqual(self.ix.asked, ["us"], lang)

    def test_the_board_and_the_built_in_line_use_the_same_names(self):
        """The Nations board's rows and a unit page's "Built in the ...: place n of m" (_board_building_list): the
        game's English names where it has no texts (Persian showed code names, Descriptor_Building_VehiculeFactory,
        found 2026-11-11 by scratch/animmodels/step2/board_where_lang.py)."""
        def names(lang):
            return [b["name"] for b in self.api._board_building_list(self.ix, None, 0, lang)]
        self.assertEqual(names("fa"), ["BARRACKS", "PROTOTYPE BASE", "ATOMIC CENTER"])   # (the HQ, decoy: no row)
        self.assertEqual(names("base"), names("fa"))
        self.assertEqual(names("fr"), ["CASERNE", "BASE DE PROTOTYPES", "CENTRE ATOMIQUE"])

    def test_a_building_without_a_name_in_the_game_goes_by_its_address(self):
        from ruse_studio.api import StudioApi
        self.assertEqual(StudioApi._factory_buildings(self.api, self.ix, "us")[(4, 14)], ["Descriptor_Building_Pillbox"])


class ThePage(unittest.TestCase):
    """The page's lists that name a build menu: the New unit form's and an era unit's Factory list (factoryLabel), the
    Nations tab's fill list (buildingLabel) and its building left with nothing to build."""

    def setUp(self):
        self.ui = ROOT / "src" / "ruse_studio" / "ui"

    def test_the_lists_use_the_buildings(self):
        app = (self.ui / "app.js").read_text(encoding="utf-8")
        self.assertIn('if (f.buildings && f.buildings.length) return f.buildings.join(" / ");', app)
        nations = (self.ui / "nations.js").read_text(encoding="utf-8")
        self.assertIn("if (m.buildings && m.buildings.length) return factoryLabel(m);", nations)
        self.assertIn("(data.empty_buildings || {})[f]", nations)
        self.assertIn("factoryLabel(f)", (self.ui / "eraunits.js").read_text(encoding="utf-8"))

    def test_the_label_no_longer_says_the_units_show_it(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))["factory"]
        self.assertEqual(len(words), 11)
        for lang, text in words.items():
            self.assertNotIn("(", text, lang)
            self.assertNotIn("（", text, lang)   # (the full-width bracket of Japanese and Chinese)
        self.assertEqual(words["us"], "Factory")


class NationTab(unittest.TestCase):
    def test_a_building_left_with_nothing_to_build_is_named(self):
        from ruse_studio.api import StudioApi
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod = root / "mod"
            (mod / "src").mkdir(parents=True)
            api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
            ix = GameIndex()
            api._mod_dir = lambda *a: mod
            api._open = lambda: ix
            api._all_units = lambda ix_: UNITS
            api._names = lambda ix_, addresses, lang, new_units=None: {a: a.rsplit("_", 1)[-1] for a in addresses}
            api._era_library = lambda: (root, {"units": []})
            api._era_record = lambda: {}
            api._upgrade_links = lambda ix_, edits: {}
            self.assertEqual(api.nation_units(0, "us")["empty_buildings"], {})
            view = api.nation_units_hide(0, True, "us")
            self.assertEqual(view["empty"], [7, 8, 12])
            self.assertEqual(view["empty_buildings"], {"7": [], "8": ["BARRACKS"], "12": ["PROTOTYPE BASE", "ATOMIC CENTER"]})


if __name__ == "__main__":
    unittest.main()
