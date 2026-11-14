"""Scenarios: a player reshaping a nation's build menus in the RUSE Studio's Nations tab (the owner, 2026-11-13
overnight: "Usual and unusual situations. Player can find themselves in when making new mods in our apps"): Keep its
units / Empty it (ui/nations.js keepOrEmpty: nation_units_hide(nation, empty, lang)), No research / Keep the game's
research (researchBox: research_clear_all, research_reset_all), the board's take-outs and puts (ui/board.js:
board_take_out, board_put), Add a building with names in every script, and these mixed with new units. After each: the
page's answer and words in every language, the mod's files, and the mod built on the made-up game.

Each test marked expectedFailure shows a finding (its number in the comment above it; the agent's report lists them);
it passes once the finding is mended."""
import unittest

from test_scenarios_units_base import (ARMOR_US, G1, G2, GAME_LANGS, H1, L1, M1, M2, P1, P2, S1, T1, A1, Player)
from ruse_studio.edits import REMOVED, ModEdits


class KeepOrEmpty(Player):
    def row(self, nation=0, factory=10):
        return next(r for r in self.call("board", nation, "us")["rows"] if r["factory"] == factory)

    def test_empty_the_usa_then_keep_its_units(self):
        folder = self.mod("Empty USA")
        res = self.call("nation_units_hide", 0, True, "us")
        self.assertEqual(res["hidden"], len(res["units"]))
        self.assertEqual(sorted(res["empty"]), [8, 9, 10, 11, 13])          # every building left with nothing
        self.assertEqual(self.row()["units"], [])
        errors, ndf, _ = self.build(folder)
        self.assertEqual(errors, [])
        self.assertEqual(self.value(ndf, M1, "ShowInMenu").int_list(), [0] * 5)
        back = self.call("nation_units_hide", 0, False, "us")
        self.assertEqual((back["hidden"], back["empty"]), (0, []))
        self.assertEqual(self.build(folder)[0], [])
        self.assertNotIn("ShowInMenu", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))

    def test_new_units_in_an_emptied_nation(self):
        folder = self.mod("Empty and new")
        self.call("nation_units_hide", 0, True, "us")
        made = [self.call("new_unit", M1, f"Fresh {k}", 40, -1, -1, False, None)["address"] for k in range(3)]
        squad = self.call("new_unit", S1, "Fresh Squad", 20, -1, -1, False, None)["address"]
        units = self.call("nation_units", 0, "us")
        self.assertEqual(sorted(units["empty"]), [9, 11, 13])                # the Armor Base and Barracks have units
        self.assertTrue(all(a in [u["address"] for u in self.row()["units"]] for a in made))
        self.assertEqual(self.build(folder)[0], [])
        back = self.call("nation_units_hide", 0, False, "us")               # the game's own come back beside them
        self.assertEqual(back["hidden"], 0)
        self.assertIn(squad, [u["address"] for u in self.row(0, 8)["units"]])
        self.assertEqual(self.build(folder)[0], [])

    def test_a_copy_researched_from_a_unit_hidden_with_its_nation(self):
        """A copy of M2 stays M2's way: an upgrade of M1. Empty the USA: M1 hidden, the copy still shown, so it's made
        buyable from the start (the game stops when a shown unit's research parent is hidden) and the page says
        which."""
        folder = self.mod("Hidden parent")
        copy = self.call("new_unit", M2, "M2 Copy", 40, -1, -1, False, None)["address"]
        res = self.call("nation_units_hide", 0, True, "us")
        self.assertEqual(res.get("unlinked"), ["M2 Copy"])
        self.assertIsNone(self.call("upgrade", copy, "us")["parent"])
        self.assertEqual(self.build(folder)[0], [])
        self.call("nation_units_hide", 0, False, "us")
        self.assertEqual(self.build(folder)[0], [])

    def test_empty_germany_with_a_lend_lease_tank_in_it(self):
        folder = self.mod("Empty Germany")
        lend = self.call("new_unit", M1, "Lend Tank", 40, 1, 10, False, None)["address"]
        res = self.call("nation_units_hide", 1, True, "us")
        self.assertEqual(sorted(res["empty"]), [8])                          # its Armor Base has the copy
        self.assertIn(lend, [u["address"] for u in self.row(1, 10)["units"]])
        self.assertEqual(self.build(folder)[0], [])


class Research(Player):
    def test_no_research_then_the_games_research_back(self):
        folder = self.mod("No research")
        cleared = self.call("research_clear_all")["cleared"]
        self.assertEqual(cleared, 3)                                           # M2, P2 and G2
        for unit in (M2, P2, G2):
            self.assertIs(ModEdits(folder).get(unit, "UpgradeRequire"), REMOVED)
        errors, ndf, _ = self.build(folder)
        self.assertEqual(errors, [])
        self.assertIsNone(self.value(ndf, M2, "UpgradeRequire"))
        self.assertEqual(self.call("research_reset_all")["reset"], 3)
        self.assertNotIn("UpgradeRequire", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        self.assertEqual(self.build(folder)[0], [])

    def test_no_research_with_copies_then_back_when_a_group_would_be_full(self):
        """No research: M2 stands on its own. Four copies of M1 fill M1's line to 5 (M1 and the copies); the game's
        research back would put M2 in it again: 6, which fits; a fifth copy first makes it 7: refused, in words, and
        nothing changes."""
        folder = self.mod("Research back")
        self.call("research_clear_all")
        copies = [self.call("new_unit", M1, f"Medium {k}", 40, -1, -1, False, None)["address"] for k in range(5)]
        groups = next(r for r in self.call("board", 0, "us")["rows"] if r["factory"] == 10)["groups"]
        self.assertEqual(next(g for g in groups if g["root"] == M1)["count"], 6)
        before = self.files(folder)
        said = self.refusal("research_reset_all")
        self.assertEqual(self.english_left(said), [])
        for text in said.values():
            self.assert_plain(text)
        self.assertEqual(self.files(folder), before)
        self.call("delete_unit", copies[0], None)
        self.assertEqual(self.call("research_reset_all")["reset"], 3)
        self.assertEqual(self.build(folder)[0], [])

    def test_a_copy_researched_from_another_copy(self):
        """The board's research pick: a copy researched from another copy, then the first deleted, as Settings >
        Research says (relink: buyable from the start)."""
        folder = self.mod("Copies' research")
        a = self.call("new_unit", H1, "Heavy A", 40, -1, -1, False, None)["address"]
        b = self.call("new_unit", H1, "Heavy B", 40, -1, -1, False, None)["address"]
        self.call("board_research", 0, b, a, "us")
        self.assertEqual(self.call("upgrade", b, "us")["parent"]["address"], a)
        self.assertEqual(self.build(folder)[0], [])
        self.api.set_pref("research_gone", "relink")
        self.call("delete_unit", a, None)
        self.assertIsNone(self.call("upgrade", b, "us")["parent"])
        self.assertEqual(self.build(folder)[0], [])


class TakeOuts(Player):
    def test_a_game_unit_with_an_upgrade_taken_out_and_put_back(self):
        folder = self.mod("Take out")
        res = self.call("board_take_out", 0, M1, None, "us")
        self.assertEqual(res["relinked"], ["M Two"])
        self.assertIs(ModEdits(folder).get(M2, "UpgradeRequire"), REMOVED)
        self.assertEqual(self.build(folder)[0], [])
        self.call("board_put", 0, 10, M1, "", 0, None, "us")
        self.assertIsNone(ModEdits(folder).get(M1, "ShowInMenu"))
        self.assertEqual(self.build(folder)[0], [])

    def test_the_last_unit_of_a_building_taken_out(self):
        folder = self.mod("Empty barracks")
        self.call("board_take_out", 0, S1, None, "us")
        self.assertEqual(self.call("nation_units", 0, "us")["empty"], [8])   # the page warns about this one
        self.assertEqual(self.build(folder)[0], [])

    def test_every_kind_moved_to_another_building(self):
        """A plane in the Armor Base, a squad in the Airfield: the board allows any of the nation's buildings; what
        the game makes of it isn't known (not tried in the game)."""
        folder = self.mod("Moves")
        self.call("board_move", 0, P1, 10, None, "new", "us")
        self.call("board_move", 0, S1, 9, None, "new", "us")
        self.assertEqual(self.build(folder)[0], [])


class AddABuilding(Player):
    def test_buildings_named_in_every_script(self):
        """Three buildings with units of their own (a nation's most), a fourth refused; then, as the made-up game has
        no build bar list for a building of its own to be built with, those taken away again and the names given to
        buildings that join the Armor Base's row, built into every language."""
        folder = self.mod("Buildings")
        names = ["Usine à chars", "戦車工場", "Танковый завод", "کارخانه"]
        own = [self.call("board_add_building", 0, ARMOR_US, name, True, "us")["made"] for name in names[:3]]
        said = self.refusal("board_add_building", 0, ARMOR_US, names[3], True, "us")   # a fourth of its own
        self.assertEqual(self.english_left(said), [])
        for address in own:
            self.call("board_remove_building", 0, address, "us")
        made = [self.call("board_add_building", 0, ARMOR_US, name, False, "us")["made"] for name in names]
        errors, ndf, texts = self.build(folder)
        self.assertEqual(errors, [])
        for name, address in zip(names, made):
            with self.subTest(name=name):
                self.assertEqual(self.built_names(ndf, texts, address), {lang: name for lang in GAME_LANGS})


if __name__ == "__main__":
    unittest.main()
