"""A build list's groups in the Studio (ruse_studio/groups.py; the owner, 2026-10-31: "We just need to limit how many
can be in a certain group. Because it's buggy."; a 7th unit in a full group: "Refuse it"; the groups are the game's
lines, each unit going into the line of its kind), on a made-up game whose units have the game's card types: the
board's groups, the group of a unit's kind (two lines of its kind, none, a new group joined by the next), every way a
unit comes into a group refusing a 7th while a move inside a group and taking out stay allowed, a group already over
the most, and the mod's menu_groups.toml kept in step."""
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from test_board import flag, i32, lst, ref
from test_dic import make_dic
from rusemod import menugroups
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.play import Starter
from ruse_studio import era_units
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits


def key(name):
    return val(0x1D, struct.pack("<Q", name_to_key(name)))


UNIT = ("Nationalite", "Factory", "PositionInMenu", "ShowInMenu", "UpgradeRequire", "IsUpgrade", "UpgradePrice",
        "UpgradeTime", "ProductionPrice", "NameInMenuToken", "TypeUnitHintToken")
AIR = ("Factory", "PositionInMenu", "ShowInMenu", "ProductionPrice", "NameInMenuToken", "TypeUnitHintToken")
BUILDING = ("Nationalite", "TypeBatiment", "Menu", "ShowInMenu", "ProductionPrice", "NameInMenuToken")
PROPS = [(n, 0) for n in UNIT] + [(n, 1) for n in AIR] + [(n, 2) for n in BUILDING]
P = [{n: i for i, (n, c) in enumerate(PROPS) if c == k} for k in range(3)]
E = "$/GFX/Everything/Descriptor_Unit_"
M1, M2, L1, H1, R1, T1, G1, P1 = (E + n for n in ("M1", "M2", "L1", "H1", "R1", "T1", "G1", "P1"))
ARMOR_BASE = "$/GFX/Everything/Descriptor_Building_ArmorBase"
ALL = (1, 1, 1, 1, 1)
TEXTS = {"TANK_m": "Medium Tank", "TANK_h": "Heavy Tank", "RECO_ar": "Armored Recon", "TD": "Tank Destroyer",
         "AIR_f": "Fighter", "N_M1": "M One", "N_M2": "M Two", "N_L1": "L One", "N_H1": "H One", "N_R1": "R One",
         "N_T1": "T One", "N_G1": "G One", "N_P1": "P One", "N_ARMOR": "Armor Base"}


def units() -> bytes:
    """The USA's Armor Base (10): M1 and M2 (an upgrade of M1) medium tanks, L1 a medium tank of a line of its own, H1 a
    heavy tank, R1 armored recon; its Anti-Tank Base (11): T1, a tank destroyer; its Airfield (9): P1, a fighter.
    Germany's Armor Base: G1, a medium tank. The USA's Armor Base building, called Armor Base."""
    def unit(name, factory, slot, card, nation=None, more=()):
        p = P[0]
        values = [(p["Factory"], i32(factory)), (p["PositionInMenu"], i32(slot)), (p["ShowInMenu"], lst(*ALL)),
                  (p["ProductionPrice"], i32(30)), (p["NameInMenuToken"], key("N_" + name)),
                  (p["TypeUnitHintToken"], key(card))]
        if nation is not None:
            values.insert(0, (p["Nationalite"], i32(nation)))
        return (0, values + list(more))
    p = P[0]
    objects = [
        unit("M1", 10, 301, "TANK_m"),                                                                  # 0
        unit("M2", 10, 302, "TANK_m", more=[(p["UpgradeRequire"], ref(0, 0)), (p["IsUpgrade"], flag(1)),
                                            (p["UpgradePrice"], i32(25)), (p["UpgradeTime"], i32(75))]),  # 1
        unit("L1", 10, 303, "TANK_m"),                                                                  # 2
        unit("H1", 10, 304, "TANK_h"),                                                                  # 3
        unit("R1", 10, 305, "RECO_ar"),                                                                 # 4
        unit("T1", 11, 401, "TD"),                                                                      # 5
        unit("G1", 10, 301, "TANK_m", nation=1),                                                        # 6
        (1, [(P[1]["Factory"], i32(9)), (P[1]["PositionInMenu"], i32(501)), (P[1]["ShowInMenu"], lst(*ALL)),
             (P[1]["ProductionPrice"], i32(50)), (P[1]["NameInMenuToken"], key("N_P1")),
             (P[1]["TypeUnitHintToken"], key("AIR_f"))]),                                                # 7 P1
        (2, [(P[2]["Nationalite"], i32(0)), (P[2]["TypeBatiment"], i32(10)), (P[2]["Menu"], i32(1)),
             (P[2]["ShowInMenu"], lst(*ALL)), (P[2]["ProductionPrice"], i32(40)),
             (P[2]["NameInMenuToken"], key("N_ARMOR"))]),                                                 # 8 the base
    ]
    exports = {k: "GFX/Everything/Descriptor_Unit_" + n for k, n in enumerate(("M1", "M2", "L1", "H1", "R1", "T1",
                                                                                "G1", "P1"))}
    exports[8] = ARMOR_BASE[2:]
    return make_ndf(objects=objects, classes=["TUniteAuSolDescriptor", "TAvionDescriptor", "TBatimentDescriptor"],
                    props=PROPS, exports=exports, topo=list(range(9)))


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", units())])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", "us\\", [("file", "baseunite.dic", make_dic([(name_to_key(k), t) for k, t in TEXTS.items()]))])])]))


def entry(name, card, copies=H1, era="WWI", factory=10, air=False):
    """An era library unit (as the library lists it), started from H1 (a heavy tank: never its group's)."""
    return {"key": f"{era}|USA|{name}", "era": era, "nation": "USA", "name": name, "in_place_of": "", "card": card,
            "building": "Armor base", "copies": copies, "copies_name": "", "game_nation": 0, "factory": factory,
            "aircraft": air, "model": None, "fits": True, "picture": None,
            "credit": {"title": f"{name} model", "author": "maker", "licence": "CC0", "url": "https://example.org/x",
                       "extra": ""}}


LIBRARY = ([entry(f"E{k}", "Medium Tank") for k in range(1, 10)]
           + [entry(f"A{k}", "Assault Gun") for k in range(1, 4)]
           + [entry("Patton", "Medium Tank", copies=M1, era="Cold War")])


class Groups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)
        cls.lib = Path(cls.tmp.name, "library")
        cls.lib.mkdir()
        (cls.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": LIBRARY}),
                                                encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                             instances=self.home / "copies")
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(self.lib)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def mod(self):
        self.api.new_mod("Groups")
        self.folder = self.home / "mods" / "groups"
        return self.folder

    def groups(self, factory=10, nation=0):
        row = next(r for r in self.api.board(nation)["rows"] if r["factory"] == factory)
        return {g["root"]: g for g in row["groups"]}

    def file(self):
        return menugroups.read(self.folder)

    def add(self, name, **kw):
        return self.api.era_unit_add(f"WWI|USA|{name}", 0, 10, **kw)["address"]

    def fill(self):
        """M1's line full: M1, M2 and four era units put in it, bought from the start."""
        self.mod()
        return [self.add(f"E{k}", research_from=None, group=M1) for k in range(1, 5)]

    def refused(self, call, *args, **kw):
        with self.assertRaisesRegex(StudioError, r"There's no room in M One's group in Armor Base: it would have "
                                                 r"\d+ units, and a group holds at most 6\. Take a unit out of that "
                                                 r"group, or put this one in a building with units of its own"):
            call(*args, **kw)

    # --- what the board shows ---
    def test_the_board_shows_each_rows_groups(self):
        board = self.api.board(0)
        row = next(r for r in board["rows"] if r["factory"] == 10)
        self.assertEqual([g["root"] for g in row["groups"]], [M1, L1, H1, R1])   # in the menu's order
        m = row["groups"][0]
        self.assertEqual(m, {"root": M1, "name": "M One", "kinds": ["Medium Tank"], "units": [M1, M2], "count": 2,
                             "most": 6, "full": False, "over": False, "new": False})
        self.assertEqual({u["address"]: u["group"] for u in row["units"]},
                         {M1: M1, M2: M1, L1: L1, H1: H1, R1: R1})
        self.assertEqual([g["root"] for g in next(r for r in board["rows"] if r["factory"] == 9)["groups"]], [P1])

    # --- the group of a unit's kind ---
    def test_two_lines_of_its_kind_the_one_with_fewer_units_then_the_first(self):
        self.mod()
        start = self.api.era_unit_start("WWI|USA|E1", H1, 0, 10)["group"]
        self.assertEqual({k: start[k] for k in ("root", "name", "count", "most", "full", "new")},
                         {"root": L1, "name": "L One", "count": 1, "most": 6, "full": False, "new": False})
        self.assertEqual([(c["root"], c["count"]) for c in start["choices"]], [(M1, 2), (L1, 1), (H1, 1), (R1, 1)])
        e1 = self.add("E1", research_from=None)
        self.assertEqual(self.file(), {e1: L1})                                 # bought from the start: written
        self.assertEqual(self.groups()[L1]["units"], [L1, e1])
        e2 = self.add("E2", research_from=None)                                  # two and two: the first in the menu
        self.assertEqual(self.file()[e2], M1)
        self.assertEqual(self.groups()[M1]["units"], [M1, M2, e2])

    def test_no_line_of_its_kind_a_group_of_its_own_the_next_joins_it(self):
        self.mod()
        start = self.api.era_unit_start("WWI|USA|A1", H1, 0, 10)["group"]
        self.assertEqual((start["root"], start["name"], start["count"], start["new"]), (None, "A1", 0, True))
        a1 = self.add("A1")
        a2 = self.add("A2", research_from=None)                                  # bought from the start: written
        self.assertEqual(self.file(), {a1: a1, a2: a1})
        g = self.groups()[a1]
        self.assertEqual((g["units"], g["kinds"], g["new"]), ([a1, a2], ["Assault Gun"], True))
        self.assertEqual(self.api.era_unit_start("WWI|USA|A3", H1, 0, 10)["group"]["root"], a1)
        made = self.api.era_unit_add("WWI|USA|A3", 0, 10)    # its start (H1) not in the group: from its first unit
        self.assertEqual((made["research_from"], made["group"]), (a1, a1))
        self.assertNotIn(made["address"], self.file())
        self.assertEqual(self.groups()[a1]["count"], 3)

    def test_research_only_from_its_group(self):
        """The add form's research choices are its group's units: the Patton (a Cold War medium tank started from M1)
        in L1's line is researched from L1 (the dearest there), not M1; picked into M1's line, from M1 (its start); a
        WWI unit whose start unit isn't in its group, from the group's first unit (test below)."""
        self.mod()
        research = self.api.era_unit_start("Cold War|USA|Patton", M1, 0, 10)["research"]
        self.assertEqual(([c["address"] for c in research["choices"]], research["suggested"], research["why"]),
                         ([L1], L1, "dearest"))
        picked = self.api.era_unit_start("Cold War|USA|Patton", M1, 0, 10, "base", M1)["research"]
        self.assertEqual(([c["address"] for c in picked["choices"]], picked["suggested"], picked["why"]),
                         ([M1, M2], M1, "start"))
        own = self.api.era_unit_start("Cold War|USA|Patton", M1, 0, 10, "base", "new")
        self.assertEqual((own["research"]["choices"], own["research"]["suggested"], own["group"]["root"]),
                         ([], None, None))
        made = self.api.era_unit_add("Cold War|USA|Patton", 0, 10)
        self.assertEqual((made["research_from"], made["group"]), (L1, L1))
        self.assertEqual(self.file(), {})                                        # an upgrade: its research says it
        with self.assertRaisesRegex(StudioError, "that unit is in another group"):
            self.api.era_unit_add("WWI|USA|E1", 0, 10, research_from=M1, group=L1)

    # --- a 7th refused, every way in ---
    def test_era_units_and_copies_refused_in_a_full_group(self):
        self.fill()
        self.assertTrue(self.groups()[M1]["full"])
        before = (ModEdits(self.folder).new_units.keys(), self.file())
        self.refused(self.add, "E5", research_from=None, group=M1)
        self.refused(self.api.board_put, 0, 10, era="WWI|USA|E5", group=M1)
        self.refused(self.api.board_put, 0, 10, unit=G1, group=M1)               # a copy of Germany's
        self.refused(self.api.new_unit, H1, "Copy", 30, group=M1)               # the Units tab's New unit
        self.refused(self.api.new_unit, M2, "Upgrade copy", 30)                  # stays M1's upgrade
        self.assertEqual((ModEdits(self.folder).new_units.keys(), self.file()), before)   # nothing made
        self.assertEqual(json.loads((self.folder / "era_units.json").read_text(encoding="utf-8")).keys(),
                         {f"WWI|USA|E{k}" for k in range(1, 5)})
        # by its kind it goes in L1's line, which has room; or a group of its own
        e5 = self.add("E5", research_from=None)
        self.assertEqual(self.file()[e5], L1)
        e6 = self.api.board_put(0, 10, era="WWI|USA|E6", group="new")["made"]
        self.assertEqual(self.file()[e6], e6)
        copy = self.api.new_unit(H1, "Copy", 30, group="new")["address"]
        self.assertEqual(self.file()[copy], copy)

    def test_moves_and_research_refused_in_a_full_group(self):
        self.fill()
        self.refused(self.api.board_move, 0, H1, 10, None, M1)                  # along its row, into M1's line
        self.refused(self.api.board_move, 0, T1, 10, 0, M1)                     # from the Anti-Tank Base
        self.refused(self.api.board_research, 0, H1, M1)                         # an upgrade of M1: in its line
        self.refused(self.api.set_upgrade, H1, M1)                               # the Upgrade box
        self.refused(self.api.set_upgrade, L1, M1)
        self.assertEqual(self.groups()[M1]["count"], 6)
        self.assertNotIn(H1, self.groups()[M1]["units"])
        self.assertIsNone(ModEdits(self.folder).get(H1, "UpgradeRequire"))       # nothing saved
        # inside the group, or into another with room: never refused
        e1 = self.groups()[M1]["units"][2]
        res = self.api.board_move(0, e1, 10, 0, M1)
        self.assertEqual(next(r for r in res["rows"] if r["factory"] == 10)["units"][0]["address"], e1)
        self.api.board_move(0, M2, 10, 0)                                        # M2 along the row: still M1's
        self.assertEqual(self.groups()[M1]["count"], 6)
        self.api.board_research(0, H1, L1)
        self.assertEqual(self.groups()[L1]["units"], [L1, H1])

    def test_no_research_and_back(self):
        """A new mod's "No research" leaves the game's units each a line of their own (as the game has them) and the
        mod's new ones in their groups; "Keep the game's research" puts the game's lines back, refused when one would
        then hold more than 6."""
        self.mod()
        patton = self.api.era_unit_add("Cold War|USA|Patton", 0, 10)["address"]   # researched from L1
        self.api.research_clear_all()
        self.assertEqual(self.file(), {patton: L1})                              # stays in L1's group
        self.assertEqual(self.groups()[M2]["units"], [M2])                       # the game's: a line of its own
        for k in range(1, 6):
            self.add(f"E{k}", research_from=None, group=M1)                      # M1 and five: full
        with self.assertRaisesRegex(StudioError, "There's no room in M One's group in Armor Base: it would have 7"):
            self.api.research_reset_all()                                        # M2 back in M1's line: 7
        self.assertEqual(self.groups()[M2]["units"], [M2])                       # nothing changed

    def test_the_refusal_in_the_players_language(self):
        from ruse_studio import errortext
        self.fill()
        with self.assertRaises(StudioError) as caught:
            self.add("E5", research_from=None, group=M1)
        self.assertEqual(errortext.worded(str(caught.exception), "fr"),
                         "Plus de place dans le groupe de M One dans Armor Base : il aurait 7 unités, et un groupe "
                         "en contient au plus 6. Retirez une unité de ce groupe, ou mettez celle-ci dans un bâtiment "
                         "qui a ses propres unités (Ajouter un bâtiment…).")

    def test_an_upgrade_stays_in_its_parents_group(self):
        self.mod()
        with self.assertRaisesRegex(StudioError, "M Two is an upgrade of M One in that building"):
            self.api.board_move(0, M2, 10, None, L1)
        self.api.board_move(0, M2, 10, None, M1)                                  # its own group: fine

    def test_taken_out_allowed_put_back_refused_when_full(self):
        self.fill()
        res = self.api.board_take_out(0, M2)                                     # taking out: always
        self.assertEqual(self.groups()[M1]["count"], 5)
        self.add("E5", research_from=None, group=M1)                            # full again
        self.refused(self.api.board_put, 0, 10, unit=M2)                         # put back
        self.refused(self.api.edit, M2, "ShowInMenu", [1, 1, 1, 1, 1])           # by hand, the Units tab
        self.refused(self.api.reset, M2, "ShowInMenu")                           # its Ctrl+Z
        self.refused(self.api.value_reset, M2, "ShowInMenu")                     # the All values tab
        self.assertEqual(ModEdits(self.folder).get(M2, "ShowInMenu"), [0, 0, 0, 0, 0])
        self.assertIn(M2, [u["address"] for u in res["taken_out"]])
        self.api.edit(R1, "ShowInMenu", [0, 0, 1, 1, 1])                        # any other dates: no group changes

    def test_a_building_with_the_most_groups_takes_no_new_one(self):
        """His pick (2026-11-01): at most 10 groups a building, so its list fits on the screen; tried at 5 here (the
        Armor Base has 4: M1's, L1's, H1's, R1's)."""
        self.mod()
        with mock.patch.object(menugroups, "MOST_GROUPS", 5):
            a1 = self.add("A1")                                                  # no line of its kind: the 5th
            start = self.api.era_unit_start("WWI|USA|E1", H1, 0, 10, group="new")["group"]
            self.assertEqual((start["root"], start["full"], start["groups"], start["most_groups"]), (None, True, 5, 5))
            self.assertEqual(self.api.board(0)["rows"][2]["most_groups"], 5)
            with self.assertRaisesRegex(StudioError, r"There's no room for another group in Armor Base: it would have "
                                                     r"6 groups, and a building holds at most 5 so its list fits"):
                self.add("E1", research_from=None, group="new")
            with self.assertRaisesRegex(StudioError, "no room for another group"):
                self.api.board_put(0, 10, era="WWI|USA|E2", group="new")
            self.add("A2", research_from=None)                                   # its kind's group: fine
            self.assertEqual(self.groups()[a1]["count"], 2)
            self.assertEqual(len(self.groups()), 5)

    def test_a_nations_own_units_shown_again_refused_when_their_group_is_full(self):
        copies = self.fill()                                                    # M1, M2 and 4: full
        self.api.nation_units_hide(0, True, factory=10)                         # the USA's own there: out
        self.add("E5", research_from=None, group=copies[0])                     # the four's group, 6 again
        self.add("E6", research_from=None, group=copies[0])
        self.refused(self.api.nation_units_hide, 0, False, factory=10)          # M1 and M2 back: 8
        self.assertEqual(ModEdits(self.folder).get(M1, "ShowInMenu"), [0, 0, 0, 0, 0])   # nothing saved

    def test_a_group_already_over_lets_units_out_and_takes_none_in(self):
        """A mod made before the limit, eight in M1's line: nothing more goes in, units go out, move inside it."""
        self.mod()
        copies = [self.api.new_unit(H1, f"X{k}", 30, group="new")["address"] for k in range(6)]
        menugroups.write(self.folder, {a: M1 for a in copies})                  # by hand: eight in M1's line
        g = self.groups()[M1]
        self.assertEqual((g["count"], g["full"], g["over"]), (8, True, True))
        self.refused(self.add, "E1", research_from=None, group=M1)
        self.api.board_move(0, copies[1], 10, 0, M1)                             # inside it: fine
        self.api.board_take_out(0, copies[0])                                    # out: fine
        self.assertEqual(self.groups()[M1]["count"], 7)
        self.assertNotIn(copies[0], self.file())
        self.api.board_move(0, copies[2], 11)                                    # out to another building: fine
        self.assertEqual(self.groups()[M1]["count"], 6)
        self.assertEqual(self.file()[copies[2]], copies[2])                      # no tank destroyer: its own group
        self.refused(self.api.board_move, 0, copies[2], 10, None, M1)            # and back in: no room

    # --- the mod's menu_groups.toml kept in step ---
    def test_the_file_follows_deletes_and_research(self):
        self.mod()
        a1, a2, a3 = (self.add(n, research_from=None) for n in ("A1", "A2", "A3"))
        self.assertEqual(self.file(), {a1: a1, a2: a1, a3: a1})
        self.api.era_unit_remove("WWI|USA|A1")                                   # its first unit deleted
        self.assertEqual(self.file(), {a2: a2, a3: a2})
        self.assertEqual(self.groups()[a2]["units"], [a2, a3])
        patton = self.api.era_unit_add("Cold War|USA|Patton", 0, 10)["address"]  # researched from L1: no line
        self.assertNotIn(patton, self.file())
        self.api.set_upgrade(patton, None)                                       # buildable from the start: stays
        self.assertEqual(self.file()[patton], L1)
        self.assertEqual(sorted(self.groups()[L1]["units"]), sorted([L1, patton]))
        self.api.board_research(0, patton, M1)                                   # an upgrade of M1: no line
        self.assertNotIn(patton, self.file())
        self.assertIn(patton, self.groups()[M1]["units"])

    def test_a_game_unit_moved_and_moved_back(self):
        self.mod()
        self.api.board_move(0, H1, 11)                                           # no heavy tank there: on its own
        self.assertEqual(self.file(), {H1: H1})
        self.api.board_move(0, H1, 10)                                           # home: as the game has it
        self.assertEqual(self.file(), {})
        self.api.board_move(0, L1, 11, None, T1)                                 # a group picked
        self.assertEqual(self.file(), {L1: T1})
        self.assertEqual(self.groups(11)[T1]["units"], [T1, L1])

    def test_older_callers_lang_in_groups_place(self):
        """board_put and board_move took `lang` where `group` stands now: a language code there is still `lang`."""
        self.mod()
        res = self.api.board_put(0, 10, "", "WWI|USA|A1", None, "fr")
        self.assertIn(res["made"], self.file())
        self.api.board_move(0, res["made"], 11, None, "us")
        self.assertEqual(self.file()[res["made"]], res["made"])


if __name__ == "__main__":
    unittest.main()
