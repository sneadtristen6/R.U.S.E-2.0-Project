"""The board (ruse_studio/board.py, ui/board.js; the owner, 2026-10-18: "a new screen for buildings where you're able to
edit the order and how many units are for what building", research "you'll select it and then select the spot where it
goes"), the start screen and a new mod's steps (ruse_studio/startscreen.py, ui/startflow.js), on a made-up game."""
import re
import struct
import tempfile
import time
import tomllib
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat, Ndf, schema
from rusemod.build import build_pack, load_mod
from rusemod.index import build_index
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.board import ROWS, dates_of
from ruse_studio.edits import REMOVED, ModEdits

UI = Path(__file__).parents[1] / "src" / "ruse_studio" / "ui"


def i32(v):
    return val(0x02, struct.pack("<i", v))


def flag(v):
    return val(0x00, struct.pack("<B", v))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(i32(x) for x in items))


PROPS = [("Nationalite", 0), ("Factory", 0), ("PositionInMenu", 0), ("ShowInMenu", 0), ("UpgradeRequire", 0),
         ("IsUpgrade", 0), ("UpgradePrice", 0), ("UpgradeTime", 0), ("ProductionPrice", 0),
         ("Factory", 1), ("PositionInMenu", 1), ("ShowInMenu", 1), ("ProductionPrice", 1),
         ("Nationalite", 2), ("TypeBatiment", 2), ("Menu", 2), ("ShowInMenu", 2), ("ProductionPrice", 2)]
P = {n: i for i, (n, c) in enumerate(PROPS) if c == 0}
PA = {n: i for i, (n, c) in enumerate(PROPS) if c == 1}
PB = {n: i for i, (n, c) in enumerate(PROPS) if c == 2}
E = "$/GFX/Everything/Descriptor_Unit_"
A, B, C, D, TIGER, OLD, PLANE = (E + n for n in ("A", "B", "C", "D", "Tiger", "Old", "Plane"))
ARMOR_BASE = "$/GFX/Everything/Descriptor_Building_ArmorBase"
ALL = (1, 1, 1, 1, 1)


def units() -> bytes:
    """The USA's Armor Base (10): A, B an upgrade of A (from 1942), C (1945, not in Nuclear), Old (never shown); its
    Anti-Tank Base (11): D; its Airfield (9): Plane. Germany's Armor Base: Tiger. The USA's Armor Base building (kind
    10, menu 1, not shown at 1939)."""
    def unit(factory, slot, shows, nation=None, more=()):
        values = [(P["Factory"], i32(factory)), (P["PositionInMenu"], i32(slot)), (P["ShowInMenu"], lst(*shows)),
                  (P["ProductionPrice"], i32(30))]
        if nation is not None:
            values.insert(0, (P["Nationalite"], i32(nation)))
        return (0, values + list(more))
    objects = [
        unit(10, 301, ALL),                                                                     # 0 A
        unit(10, 302, (1, 1, 0, 1, 1), more=[(P["UpgradeRequire"], ref(0, 0)), (P["IsUpgrade"], flag(1)),
                                             (P["UpgradePrice"], i32(25)), (P["UpgradeTime"], i32(75))]),  # 1 B
        unit(10, 303, (1, 0, 0, 1, 0)),                                                         # 2 C
        unit(11, 401, ALL),                                                                     # 3 D
        unit(10, 301, ALL, nation=1),                                                           # 4 Tiger
        unit(10, 1, (0, 0, 0, 0, 0)),                                                           # 5 Old
        (1, [(PA["Factory"], i32(9)), (PA["PositionInMenu"], i32(501)), (PA["ShowInMenu"], lst(*ALL)),
             (PA["ProductionPrice"], i32(50))]),                                                # 6 Plane
        (2, [(PB["Nationalite"], i32(0)), (PB["TypeBatiment"], i32(10)), (PB["Menu"], i32(1)),
             (PB["ShowInMenu"], lst(1, 1, 0, 1, 1)), (PB["ProductionPrice"], i32(40))]),       # 7 the Armor Base
    ]
    names = ("A", "B", "C", "D", "Tiger", "Old", "Plane")
    exports = {k: "GFX/Everything/Descriptor_Unit_" + n for k, n in enumerate(names)}
    exports[7] = ARMOR_BASE[2:]
    return make_ndf(objects=objects, classes=["TUniteAuSolDescriptor", "TAvionDescriptor", "TBatimentDescriptor"],
                    props=PROPS, exports=exports, topo=list(range(len(names) + 1)))


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", units())])]))
    (root / "RUSE.exe").write_bytes(b"MZ")


class Board(unittest.TestCase):
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

    def mod(self):
        self.api.new_mod("Board")
        return self.home / "mods" / "board"

    def row(self, board, factory):
        return [("  " * u["depth"]) + u["address"].rsplit("_", 1)[-1] for u in
                next(r for r in board["rows"] if r["factory"] == factory)["units"]]

    def built(self, folder):
        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        nd = Ndf(new.read(new.find("everything.cpp.gladndfbin")))
        return [{nd.prop_name(pi): v for pi, v in o.props} for o in nd.objects]

    def test_the_game_s_build_menus_as_rows(self):
        board = self.api.board(0)
        self.assertEqual([r["factory"] for r in board["rows"]], list(ROWS))  # the game's tab order
        self.assertEqual(self.row(board, 10), ["A", "  B", "C"])               # B drawn under A, its parent
        self.assertEqual(self.row(board, 11), ["D"])
        self.assertEqual(self.row(board, 9), ["Plane"])
        self.assertEqual(self.row(board, 8), [])
        units = {u["address"]: u for r in board["rows"] for u in r["units"]}
        self.assertEqual(units[B]["dates"], {"from": 1942, "nuclear": True})
        self.assertEqual(units[C]["dates"], {"from": 1945, "nuclear": False})
        self.assertTrue(units[B]["upgrade"])
        self.assertEqual(units[B]["research"], {"UpgradePrice": 25, "UpgradeTime": 75})
        self.assertEqual([u["address"] for u in board["taken_out"]], [OLD])     # never shown in the game
        self.assertFalse(board["can"])                                           # no mod yet
        self.assertEqual(self.row(self.api.board(1), 10), ["Tiger"])
        with self.assertRaises(StudioError):
            self.api.board_put(0, 10, unit=TIGER)                                # no mod: nothing saved

    def test_dates_said_as_the_game_has_them(self):
        self.assertEqual(dates_of(None), {"from": 1939, "nuclear": True})
        self.assertEqual(dates_of([1, 1, 1, 1, 0]), {"from": 1939, "nuclear": False})
        self.assertEqual(dates_of([0, 0, 0, 0, 1]), {"from": None, "nuclear": True})
        self.assertEqual(dates_of([0, 0, 0, 0, 0]), {"from": None, "nuclear": False})

    def test_another_nation_s_unit_is_copied_in_at_every_date(self):
        folder = self.mod()
        res = self.api.board_put(0, 10, unit=TIGER, index=1)
        made = res["made"]
        self.assertTrue(res["note"]["copied"])
        self.assertEqual(self.row(res, 10), ["A", "  B", "Tiger", "C"])        # where it was dropped
        edits = ModEdits(folder)
        self.assertEqual(edits.new_units[made].source, TIGER)
        self.assertEqual(edits.get(made, "ShowInMenu"), [1, 1, 1, 1, 1])        # in every battle (the owner, 10-18)
        self.assertEqual((edits.get(made, "Nationalite"), edits.get(made, "Factory")), (0, 10))
        again = self.api.board_put(0, 11, unit=TIGER)["made"]                   # the same name twice: a free address
        self.assertNotEqual(again, made)
        self.assertTrue(again.endswith("_2"))
        self.assertEqual(edits.new_units[made].name, ModEdits(folder).new_units[again].name)

    def test_research_under_a_unit_of_its_building_is_an_upgrade(self):
        folder = self.mod()
        res = self.api.board_research(0, C, A)
        self.assertEqual(self.row(res, 10), ["A", "  B", "  C"])                # after A's others
        edits = ModEdits(folder)
        self.assertEqual(str(edits.get(C, "UpgradeRequire")), A)
        self.assertEqual(edits.get(C, "IsUpgrade"), 1)
        self.assertEqual((edits.get(C, "UpgradePrice"), edits.get(C, "UpgradeTime")), (50, 50))
        self.assertFalse(res["note"]["dates"])        # C (1945, not Nuclear) is shown only where A is already
        c = self.built(folder)[2]
        self.assertEqual((c["IsUpgrade"].tc, c["IsUpgrade"].payload), (0x00, b"\x01"))
        self.assertEqual(struct.unpack("<III", c["UpgradeRequire"].payload)[:2], (0xBBBBBBBB, 0))  # A
        self.assertEqual(c["PositionInMenu"].scalar(), 303)                      # already after B: kept
        self.assertIsNone(ModEdits(folder).get(C, "PositionInMenu"))

    def test_research_from_another_building_has_no_upgrade_flag(self):
        folder = self.mod()
        res = self.api.board_research(0, D, B)
        d = next(u for r in res["rows"] for u in r["units"] if u["address"] == D)
        self.assertEqual((d["parent"], d["parent_factory"], d["upgrade"]), (B, 10, False))
        self.assertTrue(res["note"]["dates"])                                    # only where B is: from 1942
        edits = ModEdits(folder)
        self.assertEqual(edits.get(D, "ShowInMenu"), [1, 1, 0, 1, 1])
        self.assertIsNone(edits.get(D, "IsUpgrade"))                             # D never had the flag
        with self.assertRaises(StudioError):
            self.api.board_research(0, B, D)                                     # B -> D -> B: a loop
        with self.assertRaises(StudioError):
            self.api.board_research(0, D, TIGER)                                 # another nation's
        with self.assertRaises(StudioError):
            self.api.board_research(0, D, OLD)                                   # in no build menu
        res = self.api.board_research(0, D, None)                                # buildable from the start
        self.assertIsNone(next(u for r in res["rows"] for u in r["units"] if u["address"] == D)["parent"])
        self.assertIsNone(ModEdits(folder).get(D, "UpgradeRequire"))             # (D had none in the game)

    def test_moving_a_unit_takes_its_upgrades_along(self):
        folder = self.mod()
        res = self.api.board_move(0, A, 11, 0)
        self.assertEqual(self.row(res, 11), ["A", "  B", "D"])
        self.assertEqual(self.row(res, 10), ["C"])
        edits = ModEdits(folder)
        self.assertEqual((edits.get(A, "Factory"), edits.get(B, "Factory")), (11, 11))
        back = self.api.board_move(0, A, 10, 0)                                  # the game's building again
        self.assertEqual(self.row(back, 10)[:2], ["A", "  B"])
        self.assertIsNone(ModEdits(folder).get(A, "Factory"))

    def test_the_order_changes_as_few_numbers_as_it_can(self):
        folder = self.mod()
        res = self.api.board_order(0, 10, [C, A])
        self.assertEqual(self.row(res, 10), ["C", "A", "  B"])
        edits = ModEdits(folder)
        self.assertIsNone(edits.get(C, "PositionInMenu"))                       # kept its 303
        self.assertEqual((edits.get(A, "PositionInMenu"), edits.get(B, "PositionInMenu")), (304, 305))

    def test_a_game_unit_taken_out_is_hidden_and_its_upgrades_relinked(self):
        folder = self.mod()
        res = self.api.board_take_out(0, A)
        self.assertEqual(self.row(res, 10), ["B", "C"])
        self.assertEqual(len(res["relinked"]), 1)
        edits = ModEdits(folder)
        self.assertEqual(edits.get(A, "ShowInMenu"), [0, 0, 0, 0, 0])            # hidden, never deleted
        self.assertIs(edits.get(B, "UpgradeRequire"), REMOVED)                  # buildable from the start
        self.assertIn(A, [u["address"] for u in res["taken_out"]])
        put = self.api.board_put(0, 10, unit=A, index=0)                         # put back: the game's dates
        self.assertIsNone(ModEdits(folder).get(A, "ShowInMenu"))
        self.assertEqual(self.row(put, 10)[0], "A")

    def test_a_new_unit_taken_out_asks_first(self):
        folder = self.mod()
        made = self.api.board_put(0, 10, unit=TIGER)["made"]
        self.api.board_research(0, C, made)
        res = self.api.board_take_out(0, made)
        self.assertEqual(len(res["ask"]), 1)                                     # C is researched from it
        self.assertIn(made, ModEdits(folder).new_units)
        res = self.api.board_take_out(0, made, "relink")
        self.assertEqual(res["deleted"], made)
        self.assertNotIn(made, ModEdits(folder).new_units)

    def test_no_research_and_back(self):
        folder = self.mod()
        self.assertEqual(self.api.research_clear_all()["cleared"], 1)            # B
        self.assertIs(ModEdits(folder).get(B, "UpgradeRequire"), REMOVED)
        self.assertEqual(self.api.research_reset_all()["reset"], 1)
        self.assertIsNone(ModEdits(folder).get(B, "UpgradeRequire"))
        self.api.research_clear_all()
        self.api.board_take_out(0, A)                                             # B's parent out of the menus
        self.assertEqual(self.api.research_reset_all()["reset"], 0)
        # B stays buildable from the start: the game stops on a shown unit researched from a hidden one
        self.assertIs(ModEdits(folder).get(B, "UpgradeRequire"), REMOVED)

    def test_the_picker_lists_every_nation_this_one_first(self):
        self.mod()
        pick = self.api.board_picker(1)
        self.assertEqual([g["nation"] for g in pick["nations"]], [1, 0])
        usa = {u["address"]: u for u in pick["nations"][1]["units"]}
        self.assertNotIn(OLD, usa)                                               # another nation's never-shown: out
        own = {u["address"]: u for u in self.api.board_picker(0)["nations"][0]["units"]}
        self.assertTrue(own[OLD]["taken_out"])
        self.assertTrue(own[A]["here"])

    def test_more_than_ten_is_allowed_and_said(self):
        self.mod()
        for _ in range(9):
            res = self.api.board_put(0, 10, unit=TIGER)
        row = next(r for r in res["rows"] if r["factory"] == 10)
        self.assertEqual((row["most"], row["untried"]), (12, True))

    # --- Add a building (the owner, 2026-10-18: "Adding a new building and giving units to it"; "buildings 3 limit")
    def test_a_copy_that_makes_the_same_units_joins_its_row(self):
        folder = self.mod()
        res = self.api.board_add_building(0, ARMOR_BASE, "Armor Base Mk2")
        row = next(r for r in res["rows"] if r["factory"] == 10)
        self.assertEqual([b["name"] for b in row["buildings"]][1:], ["Armor Base Mk2"])
        self.assertEqual([r["factory"] for r in res["rows"]], list(ROWS))          # no row of its own
        edits = ModEdits(folder)
        self.assertEqual(edits.new_units[res["made"]].source, ARMOR_BASE)
        self.assertIsNone(edits.get(res["made"], "TypeBatiment"))                  # the Armor Base's kind
        self.assertEqual(edits.get(res["made"], "ShowInMenu"), [1, 1, 1, 1, 1])     # at every battle date

    def test_buildings_with_units_of_their_own_three_a_nation(self):
        folder = self.mod()
        made = []
        for k in range(3):
            res = self.api.board_add_building(0, ARMOR_BASE, f"Workshop {k}", own=True)
            made.append(res["made"])
            self.assertEqual(res["own_left"], 2 - k)
        self.assertEqual([r["factory"] for r in res["rows"]], list(ROWS) + [6, 4, 7])
        edits = ModEdits(folder)
        self.assertEqual([(edits.get(a, "TypeBatiment"), edits.get(a, "Menu")) for a in made], [(6, 8), (4, 9), (7, 10)])
        with self.assertRaisesRegex(StudioError, "already has 3"):
            self.api.board_add_building(0, ARMOR_BASE, "Workshop 4", own=True)
        other = self.api.board_add_building(1, ARMOR_BASE, "Werkstatt", own=True)   # another nation: its own three
        self.assertEqual((other["kind"], other["own_left"]), (6, 2))
        self.assertEqual(ModEdits(folder).get(other["made"], "Nationalite"), 1)

    def test_units_put_in_a_building_of_their_own(self):
        folder = self.mod()
        with self.assertRaisesRegex(StudioError, "no building of that kind"):
            self.api.board_put(0, 6, unit=TIGER)
        shop = self.api.board_add_building(0, ARMOR_BASE, "Workshop", own=True)["made"]
        res = self.api.board_put(0, 6, unit=TIGER)
        tiger = res["made"]
        self.assertEqual(self.row(res, 6), ["Tiger"])
        edits = ModEdits(folder)
        self.assertEqual((edits.get(tiger, "Factory"), edits.get(tiger, "PositionInMenu")), (6, 701))
        res = self.api.board_move(0, A, 6)                                          # A and B, researched from it
        self.assertEqual(self.row(res, 6), ["Tiger", "A", "  B"])
        self.assertEqual(self.api.board_where(A)["building"], "Workshop")
        with self.assertRaisesRegex(StudioError, "Move or take out"):
            self.api.board_remove_building(0, shop)
        for a in (tiger, A):
            self.api.board_move(0, a, 10) if a == A else self.api.board_take_out(0, a)
        res = self.api.board_remove_building(0, shop)
        self.assertEqual([r["factory"] for r in res["rows"]], list(ROWS))
        self.assertNotIn(shop, ModEdits(folder).new_units)


class StartScreen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.api = StudioApi(index_path=self.home / "none.sqlite", game_dir=self.home / "game", home=self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_fresh_install_has_nothing_to_carry_on_with(self):
        self.assertEqual(self.api.start_mods()["mods"], [])

    def test_the_last_one_first(self):
        self.api.new_mod("Older")
        time.sleep(0.01)
        self.api.new_mod("Newer")
        mods = self.api.start_mods()["mods"]
        self.assertEqual([m["name"] for m in mods], ["Newer", "Older"])
        self.api.choose_mod(mods[1]["path"])
        self.assertEqual([m["name"] for m in self.api.start_mods()["mods"]], ["Older", "Newer"])

    def test_always_skip_is_kept(self):
        self.assertNotIn("start_skip", self.api.prefs())
        self.api.set_pref("start_skip", True)
        self.assertTrue(StudioApi(index_path=self.home / "none.sqlite", game_dir=self.home / "game",
                                  home=self.home).prefs()["start_skip"])


class Page(unittest.TestCase):
    """The page's side: every control explained, every call the Studio's and answered in the browser preview, every
    word in ten languages."""

    def words(self):
        return tomllib.loads((UI.parent / "words.toml").read_text(encoding="utf-8"))

    def test_every_control_has_a_tooltip_and_every_call_exists(self):
        fake = (UI / "fake-api.js").read_text(encoding="utf-8")
        for name in ("board.js", "startflow.js"):
            js = (UI / name).read_text(encoding="utf-8")
            controls = []
            for m in re.finditer(r'el\("(?:button|input|select)", \{', js):
                depth, at = 0, m.end() - 1
                for at in range(m.end() - 1, len(js)):
                    depth += {"{": 1, "}": -1}.get(js[at], 0)
                    if depth == 0:
                        break
                controls.append(js[m.end():at])
            self.assertGreater(len(controls), 5, name)
            self.assertEqual([c for c in controls if "title" not in c], [], name)
            calls = set(re.findall(r"api\(\)\.(\w+)\(", js))
            self.assertEqual(sorted(c for c in calls if not callable(getattr(StudioApi, c, None))), [], name)
            self.assertEqual(sorted(c for c in calls if f"{c}: async" not in fake), [], name)

    def test_every_word_used_is_there_in_ten_languages(self):
        words = self.words()
        used = set()
        for name in ("board.js", "startflow.js", "nations.js"):
            js = (UI / name).read_text(encoding="utf-8")
            used |= set(re.findall(r"\bw\.([a-z_0-9]+)", js))
            used |= {k for k in re.findall(r'"((?:flow|board|ss|set)_[a-z_0-9]+)"', js) if not k.endswith("_")}
        used |= {f"flow_step_{s}" for s in ("name", "nations", "research", "board", "change", "done")}
        used |= {f"flow_help_{s}" for s in ("nations", "units", "economy", "ai", "decoy", "values")}
        used |= {"set_start_title", "set_start_help"}
        self.assertEqual(sorted(k for k in used if k not in words), [])
        for key in used:
            self.assertEqual([lang for lang in schema.LANGS if not words[key].get(lang)], [], key)

    def test_the_page_has_its_parts(self):
        page = (UI / "index.html").read_text(encoding="utf-8")
        for part in ('id="start-screen"', 'id="flow-bar"', 'id="flow-page"', 'id="set-start"', 'src="board.js"',
                     'src="startflow.js"'):
            self.assertIn(part, page)
        from rusemod.home import PREF_KEYS
        self.assertIn("start_skip", PREF_KEYS)
        app = (UI / "app.js").read_text(encoding="utf-8")
        self.assertIn("window.StartFlow.atStart(status.ready)", app)   # after the language and the game index
        flow = (UI / "startflow.js").read_text(encoding="utf-8")
        self.assertIn("if (mods.length) choices.push(big(\"ss_carry\"", flow)  # never on a fresh install


if __name__ == "__main__":
    unittest.main()
