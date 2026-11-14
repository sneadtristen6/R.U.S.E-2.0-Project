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
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import struct
import unittest

import test_ai
from test_scenarios_units_base import GAMES, LANGS, Player, Refused
from test_studio import AMMO, AMMO_75, AMMO_88, M4, M4_GUN, PANZER_IV, PANZER_MOUNT

INT_MOST, INT_LEAST = 2 ** 31 - 1, -2 ** 31
GAMES["ai"] = test_ai.write_game     # test_ai's made-up game: the AI and player settings tab's values


class Values(Player):
    GAME = "studio"

    def rndf(self, folder):
        f = folder / "src" / "studio.rndf"
        return f.read_text(encoding="utf-8") if f.is_file() else ""   # (none yet: nothing saved)

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

    # U-9 (mended by the PROPOSED FIX commit after these tests: before it, a decimal value past what the game's 4-byte
    # number holds, 1e39 or 1e300 typed in the box, was saved, and the mod's build then stopped with Python's words,
    # "OverflowError: float too large to pack with f format")
    def test_a_decimal_number_too_big_for_the_game_is_refused_or_builds(self):
        folder = self.mod("Too big a decimal")
        for value in (1e39, 1e300):
            with self.subTest(value=value):
                try:
                    self.call("edit", M4_GUN, "TempsEntreDeuxTirs", value, "", "")
                except Refused as r:   # refused in words: fine, and the mod still builds
                    self.assertNotIn("Overflow", r.text)
                    said = self.refusal("edit", M4_GUN, "TempsEntreDeuxTirs", value, "", "")
                    self.assertEqual(self.english_left(said), [], said["fr"])
                errors, _ndf, _ = self.build(folder)
                self.assertEqual(errors, [], self.rndf(folder)[-300:])

    def test_a_decimal_number_too_big_from_the_all_values_tab(self):
        """The All values tab (value_edit: what's typed, checked by rusemod.values.typed) on the same value."""
        folder = self.mod("Too big from All values")
        for value in ("1e39", 1e39):
            with self.subTest(value=value):
                try:
                    self.call("value_edit", M4_GUN, "TempsEntreDeuxTirs", value, "us")
                    outcome = "saved"
                except Refused as r:
                    outcome = "refused: " + r.text
                try:
                    errors = self.build(folder)[0]
                except OverflowError as exc:
                    errors = [f"the build stopped: OverflowError {exc}"]
                print(f"\nAll values tab, TempsEntreDeuxTirs = {value!r}: {outcome} | build: {errors}")

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

    def test_an_ammos_words_in_every_script(self):
        """The text values a unit's page changes: an ammo's name and kind in game (its page's words boxes:
        ammo_text_set), in every script, an emoji, then the game's words again; a line break refused."""
        folder = self.mod("Ammo words")
        copy = self.call("new_ammo", AMMO_75, "Hot 75")["address"]
        self.call("set_ammo", PANZER_IV, PANZER_MOUNT, copy)
        for words in ("Бронебойный 🙂", "徹甲弾", "穿甲弹", "گلوله ضد زره", "Obus perforant à l'été", "𠮷"):
            with self.subTest(words=words):
                page = self.call("ammo_text_set", copy, "Name", words, "us")
                self.assertEqual(page["name"], words)
                self.assertEqual(self.build(folder)[0], [])
        said = self.refusal("ammo_text_set", AMMO_88, "TypeName", "two\nlines", "us")
        self.assertEqual(self.english_left(said), [])
        self.call("ammo_text_set", copy, "Name", "", "us")                 # its source's name again
        self.assertEqual(self.build(folder)[0], [])

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


class TheStudiosOwnFilesBrokenByHand(Player):
    """The Studio's other files of a mod changed by hand into something it can't read: the animations' list
    (files/anim/units.toml) and the build lists' groups (menu_groups.toml). New unit… is refused; the mod check (the
    page's bar, shown when the mod is picked and before Test in game) names the file."""
    GAME = "studio"

    def broken(self, rel: str) -> tuple[dict, list]:
        folder = self.mod("Broken " + rel.rsplit("/", 1)[-1])
        self.call("new_unit", M4, "Before", 40, -1, -1, False, "new")
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[[[ not toml\n", encoding="utf-8")
        said = self.refusal("new_unit", M4, "After", 40, -1, -1, False, "new")
        problems = self.call("check_mod", lang="fr")["problems"]
        print(f"\n{rel} broken: new_unit says (fr) {said['fr']!r} | check bar: "
              f"{[(p.get('problem'), p.get('plain'), p.get('set_aside')) for p in problems]}")
        return said, problems

    def test_the_animations_list_broken_by_hand(self):
        said, problems = self.broken("files/anim/units.toml")
        self.assertTrue(problems, "the check bar names nothing")

    def test_the_groups_file_broken_by_hand(self):
        said, problems = self.broken("menu_groups.toml")
        self.assertTrue(problems, "the check bar names nothing")

    # U-17: those two files broken by hand are said in Python's TOML reader's words, English in every language: the
    # check bar's line ("...menu_groups.toml: Invalid initial character for a key part (at line 1, column 3)": its
    # plain kind "other", so the page shows it as it is, with no Set aside button) and New unit…'s refusal (menu_groups:
    # the whole of it; units.toml: inside the French frame)
    @unittest.expectedFailure
    def test_the_studios_own_files_broken_by_hand_are_said_in_plain_words(self):
        for rel in ("files/anim/units.toml", "menu_groups.toml"):
            with self.subTest(rel=rel):
                said, problems = self.broken(rel)
                for text in [said["fr"]] + [p.get("problem", "") for p in problems if p.get("plain", {}).get("kind")
                                            == "other"]:
                    self.assertNotIn("Invalid initial character", text)


class ReadOnlyFiles(Player):
    """The mod's changes file marked read-only (a mod unzipped by a tool that keeps that mark, or a synced folder): a
    change, a new unit, a Delete refused in words the player can act on, in every language; nothing lost; once the
    mark is off, they work."""
    GAME = "studio"

    def test_the_changes_file_marked_read_only(self):
        import os
        import stat
        folder = self.mod("Read only")
        made = self.call("new_unit", M4, "Kept", 40, -1, -1, False, "new")["address"]
        rndf = folder / "src" / "studio.rndf"
        before = rndf.read_bytes()
        os.chmod(rndf, stat.S_IREAD)
        self.addCleanup(os.chmod, rndf, stat.S_IREAD | stat.S_IWRITE)
        for call, args in (("edit", (M4, "SeuilMort", 15, "", "")), ("new_unit", (M4, "More", 40, -1, -1, False, "new")),
                           ("delete_unit", (made, None))):
            with self.subTest(call=call):
                said = {}
                for lang in ("us", "fr", "jpn"):   # (each refusal waits for the file a few seconds first)
                    with self.assertRaises(Refused) as cm:
                        self.call(call, *args, lang=lang)
                    said[lang] = cm.exception.text
                self.assertEqual(self.english_left(said), [], said["fr"])
                for text in said.values():
                    self.assertNotIn("Errno", text)
                self.assertEqual(rndf.read_bytes(), before)
        os.chmod(rndf, stat.S_IREAD | stat.S_IWRITE)
        self.call("edit", M4, "SeuilMort", 15, "", "")
        self.call("delete_unit", made, None)
        self.assertEqual(self.build(folder)[0], [])


class DecimalsOfTheAITab(Player):
    """U-9's kind of value in the AI and player settings tab (ai_edit takes a decimal as it comes, as the Units tab's
    edit did), on test_ai's made-up game: a profile's AttaqueTempsActivation, a 4-byte decimal number."""
    GAME = "ai"

    # U-9 too (mended by the same PROPOSED FIX commit: before it, past what the game's 4-byte number holds was saved,
    # and the build stopped with Python's OverflowError)
    def test_an_ai_value_too_big_for_the_game_is_refused_or_builds(self):
        folder = self.mod("AI too big")
        try:
            self.call("ai_edit", test_ai.REGULAR, "AttaqueTempsActivation", 1e39)
        except Refused as r:
            self.assertNotIn("Overflow", r.text)
        try:
            errors = self.build(folder)[0]
        except OverflowError as exc:
            errors = [f"the build stopped: OverflowError {exc}"]
        self.assertEqual(errors, [])

    def test_an_ai_value_at_the_most_the_game_holds(self):
        folder = self.mod("AI at the most")
        self.call("ai_edit", test_ai.REGULAR, "AttaqueTempsActivation", 3.0e38)
        self.assertEqual(self.build(folder)[0], [])


if __name__ == "__main__":
    unittest.main()
