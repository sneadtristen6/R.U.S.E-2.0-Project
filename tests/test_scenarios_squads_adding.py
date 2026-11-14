"""Scenarios: soldiers added and taken out one by one, as a player meets it on the RUSE Studio's squad page (squad.js on
ruse_studio.squadblender and the one Blender button, ruse_studio.oneblender): Add a soldier (a copy of one of the squad,
a soldier of another squad, a model file) through Blender and Bring my changes back; the whole squad in Blender with one
soldier changed; Remove with and without a look of his own (his look kept aside, the others renumbered), the bazooka man
too; +1 with soldiers of different looks (the look most wear); the squad open in Blender; a sending from Blender never
brought back. Each ends with what the page says in every language, the mod's files, its build on the made-up game and
the Studio's check of it. The base, its made-up game and its stand-ins: tests/test_scenarios_squads_base.py.

What the page says is put together here as squad.js puts it together (its words from the Studio's words in each
language, filled in as app.js fill does); where the question is whether the page says something at all, the test reads
the page's own code for it (page_part), as no browser runs here.

FOR: the squads scenarios (release 0.9.8.20, overnight 2026-11-13/14). USED-BY: the scenarios' run and report."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import re
import unittest
from pathlib import Path
from unittest import mock

from test_scenarios_squads_base import (CHARGES, GAME_SQUAD, LANGS, RIFLE_MODEL, SQUAD, STEM, TANK, SquadScenario,
                                        model_glb, sha)
from test_squadblender import Closed, Running

PAGE = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui" / "squad.js"


def fill(word: str, **values) -> str:
    """app.js fill: each {key} in `word` replaced by its value."""
    for k, v in values.items():
        word = word.replace("{" + k + "}", str(v))
    return word


def page_part(name: str) -> str:
    """squad.js's code of one of its functions (`const name = ...` to its closing `};` at the same indent)."""
    text = PAGE.read_text(encoding="utf-8")
    m = re.search(rf"^( *)const {name} = .*?^\1}};", text, re.S | re.M)
    if m is None:
        raise AssertionError(f"squad.js has no {name}")
    return m.group(0)


class Adding(SquadScenario):
    def brought_back(self, changed: dict | None = None, lang: str = "us") -> dict:
        """Blender opened (what it writes), the modder changes what `changed` gives ({id: the file's bytes}) or nothing,
        clicks Send to the R.U.S.E. Studio and closes Blender; then Bring my changes back on the page (the one Blender
        button: StudioApi.blender_back, as squad.js bringBack calls it)."""
        self.blender_opened()
        self.blender_sends(changed or {})
        return self.page.blender_back(SQUAD, lang)

    def name_of(self, lang: str, info: dict, sid: str) -> str:
        """squad.js soldierName: "Soldier 3: Rifleman"."""
        s = next(x for x in info["soldiers"] if x["id"] == sid)
        return fill(self.words(lang)["squad_soldier_one"], who=s["label"], n=s["number"])

    def joined_said(self, r: dict) -> dict:
        """What the page says when Add a soldier's Blender comes back (squad.js bringBack: r.joined)."""
        return {lang: fill(self.words(lang)["squad_added"], n=r["count"]) for lang in LANGS}

    def removed_said(self, r: dict, number: str) -> dict:
        """What the page says after Remove on a soldier's line (squad.js removeParts), as it is now."""
        out = {}
        for lang in LANGS:
            w = self.words(lang)
            out[lang] = " ".join(p for p in (fill(w["squad_removed"], number=number, n=r["count"]),
                                             w["squad_reset_uniform"] if r.get("copy_back") else "") if p)
        return out

    def own_count(self, loaded) -> int:
        return int(loaded.base.objects[SQUAD].props["R2Behaviour"].obj.props["NbSoldatInGroupeCombat"].value)


class AddASoldier(Adding):
    def test_a_copy_of_one_of_his_soldiers_changed_in_blender(self):
        """Usual: Add a soldier, a copy of soldier 2 (a rifleman in the game's look): Blender opens with him alone,
        starting from the game's rifleman; the page says what to do there in every language; the mod's files as they
        were, and it builds as before. Changed in Blender and brought back: he joins as soldier 5, before the bazooka man
        (soldier 6 now), a look of his own from what Blender sent; the page says the squad has 6, in every language; it
        builds with 6 soldiers and his look, and the Studio's check finds nothing."""
        before = self.files()
        r = self.page.soldier_add(SQUAD, "copy", "2", None, None)
        self.assertEqual((r["opened"], r["adding"], r["set_aside"]), (["new"], {"at": 5, "started": "game"}, None))
        self.assertEqual(len(self.opened), 1)
        m = self.manifest()
        self.assertEqual(([s["id"] for s in m["soldiers"]], m["adding"]["at"]), (["new"], 5))
        self.assert_worded({lang: self.words(lang)["squad_add_opened"] for lang in LANGS})
        self.assertEqual(self.soldier_files(), [])
        self.assertEqual({k: v for k, v in self.files().items() if not k.startswith("blender/")}, before)
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertNotIn("R2Behaviour", loaded.base.objects[SQUAD].props)
        r = self.brought_back({"new": model_glb(RIFLE_MODEL, b"NEW5")})
        self.assertEqual((r["joined"], r["count"], r["door"]), ("5", 6, "squad"))
        self.assertEqual([s["label"] for s in r["soldiers"]], ["Rifleman"] * 5 + ["Bazooka man"])
        self.assertEqual([s["wears"] for s in r["soldiers"]], ["game"] * 4 + ["own", "game"])
        self.assert_worded(self.joined_said(r), "One soldier more: the squad has 6 now.")
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml", f"{STEM}@5.glb", f"{STEM}@5.json"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 6)
        self.assertIn("R2SoldierLooks", loaded.base.objects[SQUAD].props)
        self.assertEqual(sorted(result.own_models), [f"{STEM}@5"])
        self.assertEqual(result.game_patch, ["own-squads"])
        self.assertEqual(self.problems(), [])
        self.assertFalse(self.info()["blender"]["waiting"])

    def test_soldiers_of_two_other_squads(self):
        """Usual: Add a soldier from another unit, twice: the game's own squad's bazooka man (soldier 5 there), then the
        squad of three charges' soldier 1, each brought back unchanged: soldiers 5 and 6 here, each a look of his own made
        from his figure as Blender sent it, the bazooka man here soldier 7. The page's list of squads to pick from (the
        Units tab's infantry, this squad left out) has both. It builds with 7 and both looks."""
        listed = {u["address"] for u in self.page.units("us", "infantry", -1, "", "all")["units"]} - {SQUAD}
        self.assertTrue({GAME_SQUAD, CHARGES} <= listed, listed)
        self.assertNotIn(TANK, listed)
        r = self.page.soldier_add(SQUAD, "unit", "5", GAME_SQUAD, None)
        self.assertEqual(r["adding"], {"at": 5, "started": "game"})
        r = self.brought_back()
        self.assertEqual((r["joined"], r["count"]), ("5", 6))
        r = self.page.soldier_add(SQUAD, "unit", "1", CHARGES, None)
        self.assertEqual(r["adding"]["at"], 6)
        r = self.brought_back()
        self.assertEqual((r["joined"], r["count"]), ("6", 7))
        self.assertEqual([s["wears"] for s in r["soldiers"]], ["game"] * 4 + ["own", "own", "game"])
        self.assertEqual(r["soldiers"][-1]["label"], "Bazooka man")
        self.assert_worded(self.joined_said(r), "One soldier more: the squad has 7 now.")
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml", f"{STEM}@5.glb", f"{STEM}@5.json",
                                                f"{STEM}@6.glb", f"{STEM}@6.json"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 7)
        self.assertEqual(sorted(result.own_models), [f"{STEM}@5", f"{STEM}@6"])
        self.assertEqual(self.problems(), [])

    def test_a_model_file_of_his_own(self):
        """Usual: Add a soldier from a model file on his PC (the file picker's): fitted to the soldier's bones into the
        squad's Blender folder, the mod's files as they were; Blender opens with him; brought back changed: soldier 5,
        a look of his own from what Blender sent. The picker closed instead: nothing opens and the page says nothing."""
        self.assertIsNone(self.page.soldier_add(SQUAD, "file", None, None, None))   # (no window here: the picker closed)
        self.assertEqual(self.opened, [])
        marine = self.model_file("marine.glb", b"glTF marine")
        r = self.page.soldier_add(SQUAD, "file", None, None, str(marine))
        self.assertEqual(r["adding"], {"at": 5, "started": "model"})
        self.assertEqual(self.fits[0], ("marine.glb", RIFLE_MODEL))
        self.assertEqual(self.soldier_files(), [])
        r = self.brought_back({"new": model_glb(RIFLE_MODEL, b"MAR5")})
        self.assertEqual((r["joined"], r["count"]), ("5", 6))
        self.assertEqual(r["soldiers"][4]["wears"], "own")
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 6)
        self.assertEqual(self.problems(), [])

    def test_a_soldier_of_another_new_squad_as_he_looks_there(self):
        """Usual: a second new squad in the mod, its soldier 2 a look of his own; Add a soldier to the first from it:
        Blender starts from that look (his model file), and brought back unchanged he joins wearing it."""
        other = self.page.new_unit(GAME_SQUAD, "My Other Squad", 50)["address"]
        self.page.soldier_import(other, "2", str(self.model_file("ranger.glb", b"glTF ranger")))
        r = self.page.soldier_add(SQUAD, "unit", "2", other, None)
        self.assertEqual(r["adding"], {"at": 5, "started": "model"})
        r = self.brought_back()
        self.assertEqual((r["joined"], r["count"]), ("5", 6))
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(sorted(result.own_models), ["Descriptor_Unit_My_Other_Squad@2", f"{STEM}@5"])
        self.assertEqual(self.problems(), [])

    def test_ways_a_page_out_of_date_can_ask_for(self):
        """Unusual (a page left open while the squad changed, or a hand-made call): a soldier the squad hasn't got, a
        unit that isn't a squad (the tank), this squad itself as the other unit, a soldier the other squad hasn't got,
        a way that isn't one: each refused in words in every language, nothing opened, nothing changed."""
        before = self.files()
        for args, english in (
                (("copy", "9", None, None), "This squad has no soldier called 9."),
                (("unit", "1", TANK, None), "The unit to take a soldier from isn't a squad of soldiers."),
                (("unit", "1", SQUAD, None), "The unit to take a soldier from isn't a squad of soldiers."),
                (("unit", "9", GAME_SQUAD, None), "That squad has no soldier called 9."),
                (("paste", None, None, None),
                 "paste isn't a way to add a soldier: a copy of one in this squad, a soldier from another unit, or a "
                 "model file.")):
            with self.subTest(args=args):
                self.assert_worded(self.refused("soldier_add", SQUAD, *args), english)
        self.assertEqual(self.opened, [])
        self.assertEqual(self.files(), before)

    def test_add_at_7_then_plus_one_before_bringing_him_back(self):
        """Unusual: 7 soldiers, Add a soldier opens Blender with the new one; Blender sends and is closed; before Bring my
        changes back, +1 makes the squad 8. The Blender sending is kept aside by +1 (its numbers are the old ones), so
        there's nothing to bring back: the page's Bring back button for a closed Blender goes (squad_info's blender.
        waiting false; a Bring back asked for all the same is refused in words). The squad is 8, it builds, and his
        sending is in the folder +1 named (what the page says of it: ASendingNeverBroughtBack)."""
        for _ in range(2):
            self.page.soldier_plus(SQUAD)
        self.page.soldier_add(SQUAD, "copy", "1", None, None)
        self.blender_opened()
        self.blender_sends({"new": model_glb(RIFLE_MODEL, b"NEW8")})
        self.assertTrue(self.info()["blender"]["waiting"])
        r = self.page.soldier_plus(SQUAD)
        self.assertEqual(r["count"], 8)
        self.assertTrue(r["set_aside"] and (Path(r["set_aside"]) / "new.glb").is_file(), r["set_aside"])
        self.assertFalse(self.info()["blender"]["waiting"])
        self.assert_worded(self.refused("blender_back", SQUAD, "us"),
                           "Open this unit in Blender first, change it there, then Bring my changes back.")
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 8)


class TheSquadInBlender(Adding):
    def test_open_change_one_bring_back(self):
        """Usual: Open in Blender on the squad (the one Blender button, every soldier ticked): Blender opens with the 5
        side by side, the page says what to do in every language; soldier 3 changed and sent: Bring my changes back
        takes him in alone (a look of his own), the page names who changed and who didn't, in every language. It
        builds with his look and the check finds nothing; the squad's number stays the game's."""
        parts = self.page.blender_parts(SQUAD, "us")
        self.assertEqual((parts["route"], [s["id"] for s in parts["soldiers"]]), ("squad", list("12345")))
        r = self.page.blender_open(SQUAD, {"model": True, "paint": True, "soldiers": list("12345")}, "us")
        self.assertEqual((r["door"], r["opened"]), ("squad", list("12345")))
        self.assert_worded({lang: self.words(lang)["squad_blender_opened"] for lang in LANGS})
        r = self.brought_back({"3": model_glb(RIFLE_MODEL, b"CHG3")})
        self.assertEqual((r["changed"], r["unchanged"]), (["3"], ["1", "2", "4", "5"]))
        info = {lang: self.info(lang) for lang in LANGS}
        said = {lang: fill(self.words(lang)["squad_back_some"], changed=self.name_of(lang, info[lang], "3"),
                           unchanged=", ".join(self.name_of(lang, info[lang], i) for i in "1245")) for lang in LANGS}
        self.assert_worded(said, "Changed: Soldier 3: Rifleman. As they were: Soldier 1: Rifleman, Soldier 2: "
                                 "Rifleman, Soldier 4: Rifleman, Soldier 5: Bazooka man. Click Test in game to see it.")
        self.assertEqual([s["wears"] for s in r["soldiers"]], ["game", "game", "own", "game", "game"])
        self.assertTrue(r["soldiers"][2]["blender_changed"])
        self.assertEqual(self.soldier_files(), [f"{STEM}@3.glb", f"{STEM}@3.json"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertNotIn("R2Behaviour", loaded.base.objects[SQUAD].props)
        self.assertEqual(sorted(result.own_models), [f"{STEM}@3"])
        self.assertEqual(self.problems(), [])

    def test_while_open_nothing_changes_the_squad_s_number(self):
        """Usual: while the squad is open in Blender, Add a soldier, +1, -1 and Remove are refused in words in every
        language (the soldiers' numbers are Blender's), and the page draws none of them (squad_info's can)."""
        self.page.blender_open(SQUAD, {"model": True, "paint": True, "soldiers": list("12345")}, "us")
        self.api._blenders[str(self.work)] = Running()
        self.addCleanup(self.api._blenders.pop, str(self.work), None)
        before = self.files()
        said = "This squad is open in Blender already: change it there, then bring your changes back."
        for name, args in (("soldier_plus", (SQUAD,)), ("soldier_minus", (SQUAD,)), ("soldier_remove", (SQUAD, "2")),
                           ("soldier_add", (SQUAD, "copy", "1", None, None))):
            with self.subTest(call=name):
                self.assert_worded(self.refused(name, *args), said)
        can = self.info()["can"]
        self.assertEqual((can["add"], can["remove"]), (False, False))
        self.assertEqual(self.files(), before)


class RemoveASoldier(Adding):
    def test_remove_a_soldier_with_a_look_of_his_own(self):
        """Usual: soldiers 2 and 3 each a look of his own (two files), then Remove on soldier 2's line: the squad 4, his
        look kept aside in the squad's Blender folder (nothing lost, never packed), soldier 3's look now soldier 2's
        (his files renumbered), the bazooka man soldier 4. It builds with 4, the look on soldier 2 the one soldier 3
        had, and the check finds nothing."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        self.page.soldier_import(SQUAD, "3", str(self.model_file("ranger.glb", b"glTF ranger")))
        third = (self.models / f"{STEM}@3.glb").read_bytes()
        r = self.page.soldier_remove(SQUAD, "2")
        self.assertEqual((r["removed"], r["count"], r["look_kept"], r["copy_back"]), ("2", 4, True, False))
        aside = Path(r["kept_aside"])
        self.assertEqual(sorted(p.name for p in aside.iterdir()), [f"{STEM}@2.glb", f"{STEM}@2.json"])
        self.assertTrue(aside.is_relative_to(self.work))
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml", f"{STEM}@2.glb", f"{STEM}@2.json"])
        self.assertEqual((self.models / f"{STEM}@2.glb").read_bytes(), third)
        self.assertEqual([s["label"] for s in r["soldiers"]], ["Rifleman"] * 3 + ["Bazooka man"])
        self.assertEqual([s["wears"] for s in r["soldiers"]], ["game", "own", "game", "game"])
        self.assertEqual(r["soldiers"][1]["from"], "ranger.glb")
        self.assert_worded(self.removed_said(r, "2"), "Soldier 2 is out of the squad: it has 4 soldiers now.")
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 4)
        self.assertEqual(sorted(result.own_models), [f"{STEM}@2"])
        self.assertEqual(self.problems(), [])

    def test_the_page_says_where_his_look_went(self):
        """Finding SQ-3, its PROPOSED FIX: Remove on the line of a soldier with a look of his own keeps that look aside
        (StudioApi.soldier_remove's look_kept), as -1 does; the page said so after -1 (squad.js countBy:
        squad_minus_kept, "His own look is kept with your Blender files for this squad: More options says where.") but
        not after Remove (squad.js removeParts read only copy_back). Now both read it."""
        self.assertIn("look_kept", page_part("countBy"))
        self.assertIn("look_kept", page_part("removeParts"))

    @unittest.expectedFailure    # finding SQ-4: two looks kept aside for one soldier number in one second: one lost
    def test_two_removes_of_soldier_2_in_one_second(self):
        """Unusual: soldiers 2 and 3 each a look of his own; Remove on soldier 2's line, then on soldier 2's line again
        (the one who was 3) within the same second of the PC's clock: both looks are to be kept aside, but the folder is
        named by the second and his number (removed-<time>-soldier2), so the second's files take the first's place
        and the first look is in no folder (the same second held still here, as two quick clicks have it)."""
        import time
        from ruse_studio import squadblender
        real, moment = time.strftime, time.localtime()
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        self.page.soldier_import(SQUAD, "3", str(self.model_file("ranger.glb", b"glTF ranger")))
        looks = {(self.models / f"{STEM}@{i}.glb").read_bytes() for i in (2, 3)}
        self.assertEqual(len(looks), 2)
        with mock.patch.object(squadblender.time, "strftime", lambda fmt, t=None: real(fmt, moment)):
            self.assertTrue(self.page.soldier_remove(SQUAD, "2")["look_kept"])
            self.assertTrue(self.page.soldier_remove(SQUAD, "2")["look_kept"])
        kept = {p.read_bytes() for p in self.work.rglob(f"{STEM}@2.glb")}
        print("\nSQ-4 kept aside:", sorted(str(p.relative_to(self.work)) for p in self.work.rglob(f"{STEM}@2.*")))
        self.assertEqual(kept, looks)

    def test_remove_the_bazooka_man(self):
        """Usual: the bazooka man (soldier 5) a look of his own, then Remove on his line: the squad 4, his look kept
        aside, the last rifleman (soldier 4) the squad's bazooka man now (the game gives the bazooka to the last soldier:
        its figure and weapon by place). It builds with 4, no look of the mod's left, and the check finds nothing."""
        self.page.soldier_import(SQUAD, "5", str(self.model_file("bazooka.glb", b"glTF bazooka")))
        r = self.page.soldier_remove(SQUAD, "5")
        self.assertEqual((r["removed"], r["count"], r["look_kept"]), ("5", 4, True))
        self.assertEqual([s["label"] for s in r["soldiers"]], ["Rifleman"] * 3 + ["Bazooka man"])
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 4)
        self.assertEqual(sorted(result.own_models), [])
        self.assertEqual(self.problems(), [])

    def test_remove_the_bazooka_man_when_the_last_rifleman_has_a_look(self):
        """Unusual: soldier 4 (a rifleman) a look of his own, then Remove on the bazooka man's line: soldier 4 is the
        squad's last man now, wearing his own look made for a rifleman's place. It builds, and the check finds
        nothing; what the game draws for him (his look on the bazooka man's place) is for a game test."""
        self.page.soldier_import(SQUAD, "4", str(self.model_file("marine.glb", b"glTF marine")))
        self.assertEqual(self.fits[-1][1], RIFLE_MODEL)
        r = self.page.soldier_remove(SQUAD, "5")
        self.assertEqual([(s["label"], s["wears"]) for s in r["soldiers"]],
                         [("Rifleman", "game")] * 3 + [("Bazooka man", "own")])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(sorted(result.own_models), [f"{STEM}@4"])
        self.assertEqual(self.problems(), [])


class PlusWithLooks(Adding):
    def test_plus_one_wears_the_look_most_riflemen_wear(self):
        """Usual: soldiers 1 and 2 the same look (Import model from two files of the same bytes), soldier 3 another,
        soldier 4 the game's: +1 joins as soldier 5 wearing a copy of soldier 1's look (the most worn, the owner's pick
        5); -1 then takes him out again, his look kept aside, which the page says. Each builds."""
        same = b"glTF same"
        self.page.soldier_import(SQUAD, "1", str(self.model_file("a.glb", same)))
        self.page.soldier_import(SQUAD, "2", str(self.model_file("a copy.glb", same)))
        self.page.soldier_import(SQUAD, "3", str(self.model_file("b.glb", b"glTF other")))
        first = (self.models / f"{STEM}@1.glb").read_bytes()
        self.assertEqual((self.models / f"{STEM}@2.glb").read_bytes(), first)
        r = self.page.soldier_plus(SQUAD)
        self.assertEqual((r["joined"], r["like"], r["count"]), ("5", "1", 6))
        self.assertEqual((self.models / f"{STEM}@5.glb").read_bytes(), first)
        self.assertEqual([s["wears"] for s in r["soldiers"]], ["own", "own", "own", "game", "own", "game"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 6)
        self.assertEqual(self.problems(), [])
        r = self.page.soldier_minus(SQUAD)
        self.assertEqual((r["removed"], r["count"], r["look_kept"]), ("5", 5, True))
        said = {lang: " ".join((fill(self.words(lang)["squad_removed"], number="5", n=5),
                                self.words(lang)["squad_minus_kept"])) for lang in LANGS}
        self.assert_worded(said, "Soldier 5 is out of the squad: it has 5 soldiers now. His own look is kept with your "
                                 "Blender files for this squad: More options says where.")
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])

    def test_plus_one_when_most_wear_the_game_s_look(self):
        """Usual: soldier 3 a look of his own, the other riflemen the game's: +1 joins wearing the game's look (no file
        for him), and the mod builds with 6."""
        self.page.soldier_import(SQUAD, "3", str(self.model_file("b.glb", b"glTF other")))
        r = self.page.soldier_plus(SQUAD)
        self.assertEqual((r["joined"], r["like"]), ("5", "1"))
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml", f"{STEM}@3.glb", f"{STEM}@3.json"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 6)


class ASendingNeverBroughtBack(Adding):
    """Blender sent the squad (or a new soldier) and was closed, and the player does something else on the page before
    Bring my changes back: Open in Blender again, Add a soldier, +1, -1 or Remove. Each keeps the sending aside
    (sent-not-brought-<time>/ in the squad's Blender folder: nothing lost) and answers with where ("set_aside"); the
    Studio's words for it: blender_squad_set_aside, "Blender's last sending was never brought back, so it was kept aside
    in {folder}."."""

    def sent_and_closed(self):
        self.page.blender_open(SQUAD, {"model": True, "paint": True, "soldiers": list("12345")}, "us")
        self.blender_opened()
        self.blender_sends({"3": model_glb(RIFLE_MODEL, b"CHG3")})
        self.assertTrue(self.info()["blender"]["waiting"])

    def test_each_way_keeps_the_sending_aside(self):
        """Usual: the sending kept aside by each of the five, with where, and the Bring back button gone (nothing
        waiting); Open in Blender's own answer says it in words (its "message"). (A second apart each time, as a
        player's Blender sendings are: the folder is named by the second.)"""
        import time
        for name, args in (("blender_open", (SQUAD, {"model": True, "paint": True, "soldiers": list("12345")}, "us")),
                           ("soldier_add", (SQUAD, "copy", "1", None, None)), ("soldier_plus", (SQUAD,)),
                           ("soldier_minus", (SQUAD,)), ("soldier_remove", (SQUAD, "2"))):
            with self.subTest(call=name):
                self.sent_and_closed()
                r = getattr(self.page, name)(*args)
                self.assertTrue(r["set_aside"] and (Path(r["set_aside"]) / "3.glb").is_file(), r)
                self.assertFalse(self.info()["blender"]["waiting"])
                if name == "blender_open":
                    self.assertIn(fill(self.words("us")["blender_squad_set_aside"], folder=r["set_aside"]),
                                  r["message"])
                time.sleep(1.1)

    def test_the_page_says_it(self):
        """Finding SQ-2, its PROPOSED FIX: each of the page's five ways reads the answer's set_aside (or Open in
        Blender's message) and says where the sending went, with the Studio's own words for it in each language
        (blender_squad_set_aside). Before, squad.js openBlender said its own squad_blender_opened, addSoldier
        squad_add_opened, countBy squad_added / squad_removed, removeParts squad_removed, and none read set_aside or the
        message."""
        for part in ("openBlender", "addSoldier", "countBy", "removeParts"):
            with self.subTest(part=part):
                code = page_part(part)
                self.assertTrue("set_aside" in code or ".message" in code, part)
                self.assertIn("blender_squad_set_aside", code)
        self.assert_worded({lang: fill(self.words(lang)["blender_squad_set_aside"], folder="D:\\x") for lang in LANGS})


class ThePageCodeRead(unittest.TestCase):
    def test_each_part_the_findings_read_is_found(self):
        """The control for SQ-2 and SQ-3's tests (an expected failure takes any error as its failure): each squad.js
        part they read is found, and what -1 says of a look kept aside is found in countBy, so a part that does read
        an answer's field is told apart from one that doesn't."""
        for name in ("openBlender", "addSoldier", "countBy", "removeParts"):
            with self.subTest(part=name):
                self.assertIn(f"const {name} = ", page_part(name))
        self.assertIn("look_kept", page_part("countBy"))
        self.assertIn("squad_minus_kept", page_part("countBy"))


if __name__ == "__main__":
    unittest.main()
