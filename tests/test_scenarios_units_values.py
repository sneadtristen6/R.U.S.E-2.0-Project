"""Scenarios: a player changing a unit's values in the Units tab (the owner, 2026-11-13 overnight: "Usual and unusual
situations. Player can find themselves in when making new mods in our apps"), on test_studio's made-up game (the M4
with a gun firing an ammo shared with the Panzer, the Panzer's mount and flag list). Every kind of value the tab shows:
a whole number, a decimal one, a box ticked or not, a list (one box for all or each), the flags, a link (the ammo a
weapon fires, a copied ammo of its own), at and past their limits; Back to the game's value; the changes file broken
by hand. Each change is made as the page makes it (ui/app.js row(): edit(address, prop, a number or a list, mode, via)
with only finite numbers; reset(address, prop, mode, via)). After each: the page's words in every language, the mod's
src/studio.rndf, and the mod built on the made-up game.

Each test marked expectedFailure shows a finding (its number in the comment above it; the agent's report lists them);
it passes once the finding is mended."""
import struct
import unittest

from test_scenarios_units_base import LANGS, Player, Refused
from test_studio import AMMO, AMMO_75, AMMO_88, M4, M4_GUN, PANZER_IV, PANZER_MOUNT

INT_MOST, INT_LEAST = 2 ** 31 - 1, -2 ** 31


class Values(Player):
    GAME = "studio"

    def rndf(self, folder):
        return (folder / "src" / "studio.rndf").read_text(encoding="utf-8")

    def built(self, folder):
        errors, ndf, _texts = self.build(folder)
        self.assertEqual(errors, [])
        return ndf

    def test_a_whole_number_at_its_limits_and_past_them(self):
        folder = self.mod("Numbers")
        for value, saved in ((15, 15), (15.6, 16), (15.4, 15), (INT_MOST, INT_MOST), (INT_LEAST, INT_LEAST), (0, 0),
                             (-5, -5)):
            with self.subTest(value=value):
                self.assertEqual(self.call("edit", M4, "SeuilMort", value, "", "")["value"], saved)
                self.assertEqual(self.built(folder).objects[0].get(1).scalar(), saved)
        for value in (INT_MOST + 1, INT_LEAST - 1, 1e20):
            with self.subTest(past=value):
                said = self.refusal("edit", M4, "SeuilMort", value, "", "")
                self.assertEqual(self.english_left(said), [])
        self.assertEqual(self.built(folder).objects[0].get(1).scalar(), -5)    # the last change kept, nothing more

    def test_a_decimal_number_at_its_limits(self):
        folder = self.mod("Decimals")
        for value in (0.25, 0.0000001, 3.4e38, -1.5, 0):
            with self.subTest(value=value):
                self.assertEqual(self.call("edit", M4_GUN, "TempsEntreDeuxTirs", value, "", "")["value"], value)
                got = self.built(folder).objects[4].get(11).scalar()
                self.assertAlmostEqual(got, value, delta=abs(value) * 1e-6 + 1e-12)

    # U-9: a decimal value past what the game's 4-byte number holds (the box takes 1e39 or 1e300) is saved, and the
    # mod then no longer builds
    @unittest.expectedFailure
    def test_a_decimal_number_too_big_for_the_game_is_refused_or_builds(self):
        folder = self.mod("Too big a decimal")
        for value in (1e39, 1e300):
            with self.subTest(value=value):
                try:
                    self.call("edit", M4_GUN, "TempsEntreDeuxTirs", value, "", "")
                except Refused as r:   # refused in words: fine, and the mod still builds
                    self.assert_plain(r.text)
                errors, _ndf, _ = self.build(folder)
                self.assertEqual(errors, [], self.rndf(folder)[-300:])

    def test_a_box_ticked_or_not(self):
        folder = self.mod("Ticks")
        self.assertEqual(self.call("edit", M4_GUN, "TirEnMouvement", 0, "", "")["value"], 0)
        self.assertEqual(self.built(folder).objects[4].get(12).payload, b"\x00")
        self.assertEqual(self.call("edit", M4_GUN, "TirEnMouvement", 1, "", "")["value"], 1)   # the game's: no change
        self.assertNotIn("TirEnMouvement", self.rndf(folder))
        for value in (2, -1):   # (a ticked box sends 1 or 0 only)
            with self.subTest(value=value):
                self.assertEqual(self.english_left(self.refusal("edit", M4_GUN, "TirEnMouvement", value, "", "")), [])

    def test_a_list_one_box_for_all_or_each(self):
        folder = self.mod("Lists")
        self.assertEqual(self.call("edit", M4, "ProductionPrice", [40, 40], "", "")["value"], [40, 40])
        self.assertEqual(self.call("edit", M4, "ProductionPrice", [0, 99999], "", "")["value"], [0, 99999])
        self.assertEqual(self.built(folder).objects[0].get(0).int_list(), [0, 99999])
        # (never from the page, which always sends the list its row has; refused, in English only: these refusals are
        # made as `a if b else c`, which the Studio's catalogue of refusals doesn't collect)
        for value in ([1, 2, 3], [1], 5):
            with self.subTest(value=value):
                self.refusal("edit", M4, "ProductionPrice", value, "", "")
        self.assertEqual(self.built(folder).objects[0].get(0).int_list(), [0, 99999])

    def test_the_flags(self):
        folder = self.mod("Flags")
        self.assertEqual(self.call("edit", PANZER_IV, "InitialFlagSet", [4, 10, 104], "", "")["value"], [4, 10, 104])
        self.assertEqual(self.built(folder).objects[1].get(14).int_list(), [4, 10, 104])
        self.assertEqual(self.call("edit", PANZER_IV, "InitialFlagSet", [], "", "")["value"], [])     # none at all
        self.assertEqual(self.built(folder).objects[1].get(14).int_list(), [])
        checked = self.call("flag_check", PANZER_IV, [4, 10, 105], "fr")
        self.assertIn("problems", checked)

    def test_back_to_the_games_value_for_each_kind(self):
        folder = self.mod("Back")
        changes = [(M4, "SeuilMort", 20), (M4, "ProductionPrice", [1, 2]), (M4_GUN, "TempsEntreDeuxTirs", 0.5),
                   (M4_GUN, "TirEnMouvement", 0), (PANZER_IV, "InitialFlagSet", [10])]
        for address, prop, value in changes:
            self.call("edit", address, prop, value, "", "")
        self.call("set_ammo", PANZER_IV, PANZER_MOUNT, AMMO_88)
        for address, prop, _value in changes:
            self.call("reset", address, prop, "", "")
        self.call("set_ammo", PANZER_IV, PANZER_MOUNT, AMMO_75)                 # its own ammo again
        self.assertEqual(self.call("edited"), [])
        self.assertNotIn("patch", self.rndf(folder))
        self.assertEqual(self.build(folder)[0], [])

    def test_a_shared_ammo_for_one_unit_then_all_then_back(self):
        folder = self.mod("Shared")
        self.call("edit", AMMO, "Puissance", 60, "own", PANZER_IV)
        self.call("edit", AMMO, "Puissance", 50, "shared", "")
        self.call("reset", AMMO, "Puissance", "own", PANZER_IV)
        ndf = self.built(folder)
        ammo_of = lambda gun: struct.unpack("<III", ndf.objects[gun].get(8).payload)[1]  # noqa: E731
        self.assertEqual((ammo_of(4), ammo_of(5)), (6, 6))                     # one ammo for both again
        self.assertEqual(ndf.objects[6].get(9).scalar(), 50)
        said = self.refusal("edit", AMMO, "Puissance", 70, "", "")             # for whom? (the page always says)
        self.assertEqual(self.english_left(said), [])

    def test_a_weapon_fires_a_copied_ammo(self):
        """A copied ammo of the Panzer's mount's own (New copy… on the ammo's page, then the weapon's ammo picked)."""
        folder = self.mod("Ammo copy")
        copy = self.call("new_ammo", AMMO_75, "Hot 75")["address"]
        self.call("set_ammo", PANZER_IV, PANZER_MOUNT, copy)
        self.call("edit", copy, "Puissance", 80, "", "")
        self.assertEqual(self.build(folder)[0], [])
        self.assertEqual(self.call("weapons", PANZER_IV, "us")["weapons"][0]["ammo"]["address"], copy)

    # U-10: deleting a copied ammo that a weapon fires (Delete copy on its page) leaves the weapon firing it
    # (Ammunition = the copy's address in src/studio.rndf; the weapon's box still names it), with no word: the mod no
    # longer builds ("...Descriptor_Unit_Panzer_IV_G still refers to $/GFX/Everything/Ammo_Hot_75")
    @unittest.expectedFailure
    def test_after_the_ammo_copy_is_deleted_the_mod_builds(self):
        folder = self.mod("Ammo copy gone")
        copy = self.call("new_ammo", AMMO_75, "Hot 75")["address"]
        self.call("set_ammo", PANZER_IV, PANZER_MOUNT, copy)
        gone = self.call("delete_unit", copy, None)
        self.assertNotEqual(self.call("weapons", PANZER_IV, "us")["weapons"][0]["ammo"]["address"], copy, gone)
        self.assertEqual(self.build(folder)[0], [], self.rndf(folder))

    def test_what_the_mod_check_says_after_the_ammo_copy_is_deleted(self):
        """U-10 as it is now (passes on the code as it is; goes once U-10 is mended): the check bar, which the page
        shows when a mod is picked and before Test in game, names nothing; the build does."""
        folder = self.mod("Ammo copy check")
        copy = self.call("new_ammo", AMMO_75, "Hot 75")["address"]
        self.call("set_ammo", PANZER_IV, PANZER_MOUNT, copy)
        self.call("delete_unit", copy, None)
        print("\nU-10 check_mod:", self.call("check_mod")["problems"])
        self.assertEqual(self.build(folder)[0],
                         ["$/GFX/Everything/Descriptor_Unit_Panzer_IV_G still refers to $/GFX/Everything/Ammo_Hot_75"])

    def test_no_mod_picked(self):
        for call, args in (("edit", (M4, "SeuilMort", 15, "", "")), ("new_unit", (M4, "X", 40, -1, -1, False, None)),
                           ("set_ammo", (PANZER_IV, PANZER_MOUNT, AMMO_88)), ("new_ammo", (AMMO_75, "Hot"))):
            with self.subTest(call=call):
                said = self.refusal(call, *args)
                self.assertTrue(said["us"].startswith("Pick or make a mod first"), said["us"])
                self.assertEqual(self.english_left(said), [])
        self.assertEqual(self.call("reset", M4, "SeuilMort", "", ""), {"saved": None})

    def test_the_changes_file_broken_by_hand(self):
        """src/studio.rndf changed by hand into something the Studio can't read: browsing goes on, nothing is
        written over it, the mod check names it in the player's language."""
        folder = self.mod("Broken changes")
        self.call("edit", M4, "SeuilMort", 15, "", "")
        broken = "patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( SeuilMort = \n"
        (folder / "src" / "studio.rndf").write_text(broken, encoding="utf-8")
        page = self.call("unit", M4, "fr")
        self.assertFalse(page["editable"])
        with self.assertRaises(Refused):
            self.call("edit", M4, "SeuilMort", 16, "", "", lang="fr")
        self.assertEqual(self.rndf(folder), broken)
        problems = self.call("check_mod", lang="fr")["problems"]
        self.assertTrue(problems)

    # U-11: with src/studio.rndf broken by hand, the unit page's notice and every change's refusal are English in every
    # language ("...studio.rndf has a mistake (...). Fix it, or delete it to start over.": an EditsFileError, which the
    # page's errors in the player's language never see)
    @unittest.expectedFailure
    def test_the_changes_file_broken_by_hand_is_said_in_the_players_language(self):
        folder = self.mod("Broken words")
        (folder / "src" / "studio.rndf").write_text("patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( SeuilMort = \n",
                                                    encoding="utf-8")
        said = self.refusal("edit", M4, "SeuilMort", 16, "", "")
        self.assertEqual(self.english_left(said), [], said["fr"])
        notices = {lang: self.call("unit", M4, lang)["why_not"] for lang in LANGS}
        self.assertEqual(self.english_left(notices), [], notices["fr"])


if __name__ == "__main__":
    unittest.main()
