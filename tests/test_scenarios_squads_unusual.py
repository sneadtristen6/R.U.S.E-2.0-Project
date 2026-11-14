"""Scenarios: a squad in the less usual places a player can take it in the RUSE Studio: its number of soldiers written by
hand in its file (9, 1, a word), the squad deleted (with its soldiers' looks and number; with a Blender sending never
brought back; with a soldier's look another program has open) and made again under its name, two new squads in one mod,
a squad whose last three soldiers fire its weapons one each, a file that isn't a model on a soldier's line, and the
squad's own model (the Model row's, every rifleman's) with one soldier back to the game's look and +1. Each ends with
what the page says in every language, the mod's files, its build on the made-up game and the Studio's check of it. The
base, its made-up game and its stand-ins: tests/test_scenarios_squads_base.py.

FOR: the squads scenarios (release 0.9.8.20, overnight 2026-11-13/14). USED-BY: the scenarios' run and report."""
import unittest
from pathlib import Path
from unittest import mock

from rusemod.unitmodel import import_model as REAL_FITTING
from test_scenarios_squads_adding import fill
from test_scenarios_squads_base import (CHARGES, GAME_SQUAD, LANGS, RIFLE_MODEL, SQUAD, STEM, SquadScenario,
                                        model_glb)

OTHER_STEM = "Descriptor_Unit_My_Other_Squad"


def now_said(w: dict, s: dict) -> str:
    """What the page says under a soldier's name of the look he wears (squad.js soldierLine's "now")."""
    if not s["own_model"]:
        return w["squad_now_game"]
    return w["squad_now_blender"] if s["blender_changed"] else fill(w["squad_now_file"], file=s["from"] or "")


class Unusual(SquadScenario):
    def put_count(self, text: str) -> Path:
        """The squad's file written by hand (files/models/<unit>.squad.toml), as a modder could in Notepad."""
        f = self.models / f"{STEM}.squad.toml"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def own_count(self, loaded, stem: str = STEM) -> int:
        return int(loaded.base.objects["$/GFX/Everything/" + stem].props["R2Behaviour"].obj.props[
            "NbSoldatInGroupeCombat"].value)


class TheSquadFileByHand(Unusual):
    def test_9_and_1_by_hand_shown_and_mended_with_minus_and_plus(self):
        """Unusual: 9 by hand: the page shows 9, no +1 and why in every language; the build stops on the file, naming it;
        -1 makes it 8, which builds. Then 1 by hand: the page shows 1, no -1 and why; the build stops, naming the file;
        +1 makes it 2, which builds."""
        self.put_count("count = 9\n")
        infos = self.every_language_info()
        self.assertEqual((infos["us"]["count"], infos["us"]["can"]["add"]), (9, False))
        self.assert_worded({lang: i["limits"]["add"] for lang, i in infos.items()},
                           "A squad has at most 8 soldiers for now.")
        result, _loaded = self.built()
        self.assertEqual(len(self.errors(result)), 1)
        self.assertIn(f"files/models/{STEM}.squad.toml", self.errors(result)[0])
        self.assertEqual(self.page.soldier_minus(SQUAD)["count"], 8)
        result, loaded = self.built()
        self.assertEqual((self.errors(result), self.own_count(loaded)), ([], 8))
        self.put_count("count = 1\n")
        infos = self.every_language_info()
        self.assertEqual((infos["us"]["count"], infos["us"]["can"]["remove"]), (1, False))
        self.assert_worded({lang: i["limits"]["remove"] for lang, i in infos.items()},
                           "A squad keeps at least 2 soldiers: the game's own rule.")
        result, _loaded = self.built()
        self.assertIn(f"files/models/{STEM}.squad.toml", self.errors(result)[0])
        self.assertEqual(self.page.soldier_plus(SQUAD)["count"], 2)
        result, loaded = self.built()
        self.assertEqual((self.errors(result), self.own_count(loaded)), ([], 2))

    @unittest.expectedFailure    # finding SQ-7: the Studio's check misses squad rules the build stops on
    def test_the_check_names_the_file_before_the_build_stops_on_it(self):
        """The Studio's check (check_mod: "Every file of the current mod read as the build reads it"; the window runs it
        when the mod is picked and before Test in game) says nothing of a squad file of 9 or of 1, which the build stops
        on (rusemod.build's squad rules run in build_pack, the check only loads the mod: rusemod.modcheck)."""
        for text in ("count = 9\n", "count = 1\n"):
            with self.subTest(text=text):
                self.put_count(text)
                self.assertTrue(self.errors(self.built()[0]))
                problems = self.problems()
                print(f"\nSQ-7 {text.strip()}: check {problems}")
                self.assertTrue(any(p and f"{STEM}.squad.toml" in p for p in problems), problems)

    def test_a_word_by_hand(self):
        """Unusual: a word for the number by hand: the squad's part of the page can't be read (squad.js infoOf: the
        page says the words instead), +1 and -1 say the same, and the Studio's check names the file (it loads the mod
        as the build does). Deleting the file by hand mends it."""
        f = self.put_count('count = "x"\n')
        said = self.refused("squad_info", SQUAD, "us")
        self.assertIn(f"files/models/{STEM}.squad.toml", said["us"])
        print("\nSQ-9 a word by hand:", {lang: said[lang] for lang in ("us", "fr", "jpn")})
        for name in ("soldier_plus", "soldier_minus"):
            self.assertEqual(self.refused(name, SQUAD)["us"], said["us"])
        self.assertTrue(any(f"{STEM}.squad.toml" in (p or "") for p in self.problems()), self.problems())
        f.unlink()
        self.assertEqual(self.info()["count"], 5)
        self.assertEqual(self.problems(), [])

    @unittest.expectedFailure    # finding SQ-9: those words English in every language, Python's quotes in them
    def test_a_word_by_hand_said_in_every_language(self):
        self.put_count('count = "x"\n')
        said = self.refused("squad_info", SQUAD, "us")
        self.assert_worded(said)
        self.assertNotIn("'x'", said["us"])


class DeleteASquad(Unusual):
    def test_delete_with_looks_and_number_then_make_it_again(self):
        """Usual: soldier 2 a look of his own and +1 (6), then Delete: every file of the squad leaves the mod, the page
        says it went in every language, the mod builds without it; New unit under the same name: the game's squad
        again (5, every soldier the game's look), no file, built as the game's."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        self.page.soldier_plus(SQUAD)
        res = self.page.delete_unit(SQUAD)
        self.assertEqual((res["deleted"], res["waiting"]), (SQUAD, []))
        self.assert_worded({lang: fill(self.words(lang)["unit_deleted"], name="My Squad") for lang in LANGS})
        self.assertEqual(self.soldier_files(), [])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertNotIn(SQUAD, (loaded.base.objects if loaded is not None else {}))
        self.assertEqual(self.page.new_unit(GAME_SQUAD, "My Squad", 50)["address"], SQUAD)
        info = self.info()
        self.assertEqual((info["count"], {s["wears"] for s in info["soldiers"]}), (5, {"game"}))
        self.assertEqual(self.soldier_files(), [])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertNotIn("R2Behaviour", loaded.base.objects[SQUAD].props)
        self.assertEqual(self.problems(), [])

    @unittest.expectedFailure    # finding SQ-5: a squad made again takes in the deleted one's Blender sending
    def test_made_again_starts_with_none_of_the_deleted_one_s_blender_work(self):
        """Unusual: the squad open in Blender, soldier 3 changed and sent, Blender closed, not brought back; Delete; New
        unit under the same name. The squad's Blender folder (blender/<unit>/, its sending and the one Blender button's
        record) isn't the unit's files Delete takes out (ruse_studio.edits.unit_files), so the new squad's page has
        Bring my changes back on its big button and under it, and that brings the deleted squad's soldier 3 into it."""
        self.page.blender_open(SQUAD, {"model": True, "paint": True, "soldiers": list("12345")}, "us")
        self.blender_opened()
        self.blender_sends({"3": model_glb(RIFLE_MODEL, b"OLD3")})
        self.page.delete_unit(SQUAD)
        self.page.new_unit(GAME_SQUAD, "My Squad", 50)
        waiting, opened = self.info()["blender"]["waiting"], self.page.blender_parts(SQUAD, "us")["open"]
        r = self.page.blender_back(SQUAD, "us")
        print("\nSQ-5 made again: waiting", waiting, "| big button open", opened, "| Bring back:", r.get("message"),
              "| files", self.soldier_files())
        self.assertEqual((waiting, opened, self.soldier_files()), (False, False, []))

    def test_delete_while_a_soldier_s_look_is_held_open(self):
        """Unusual: soldier 2's look file open in another program (Windows won't let it be moved), then Delete: the
        squad goes all the same (the owner, 2026-11-13: "if someone clicks it should through"), the page says which
        file waits, in every language; the build leaves that file out, and the check finds nothing; once the program
        lets go, opening the mod again takes the file out."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        held = open(self.models / f"{STEM}@2.glb", "rb")
        try:
            with mock.patch("ruse_studio.edits.HOLD_WAIT", 0.3):
                res = self.page.delete_unit(SQUAD)
            self.assertEqual((res["deleted"], res["waiting"]), (SQUAD, [f"files/models/{STEM}@2.glb"]))
            self.assert_worded({lang: fill(self.words(lang)["unit_deleted_waiting_one"], file=res["waiting"][0])
                                for lang in LANGS})
            result, loaded = self.built()
            self.assertEqual(self.errors(result), [])
            self.assertEqual(result.own_models, {} if isinstance(result.own_models, dict) else [])
            self.assertEqual(self.problems(), [])
        finally:
            held.close()
        self.page.choose_mod(str(self.mod))
        self.assertEqual(self.soldier_files(), [])

    def test_made_again_while_a_deleted_soldier_s_look_is_still_held(self):
        """Unusual: as above, and New unit under the same name while the file is still held. By rusemod.holding.forget
        (a file a program still holds is from then on the new unit's), the new squad's soldier 2 wears it: the page
        shows his look, the build takes it (an owner question: see the report). Held or let go, it stays."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        held = open(self.models / f"{STEM}@2.glb", "rb")
        try:
            with mock.patch("ruse_studio.edits.HOLD_WAIT", 0.3):
                self.page.delete_unit(SQUAD)
            self.page.new_unit(GAME_SQUAD, "My Squad", 50)
            wears = [s["wears"] for s in self.info()["soldiers"]]
        finally:
            held.close()
        self.page.choose_mod(str(self.mod))
        self.assertEqual(wears, ["game", "own", "game", "game", "game"])
        self.assertEqual(self.soldier_files(), [f"{STEM}@2.glb"])
        result, _loaded = self.built()
        self.assertEqual((self.errors(result), sorted(result.own_models)), ([], [f"{STEM}@2"]))

    @unittest.expectedFailure    # finding SQ-8: a look with no record: the page says "Your model, from ."
    def test_a_look_without_its_record_is_said_with_a_name(self):
        """A soldier's look file with no record beside it (left by the Delete above, or copied by hand): squad_info's
        "from" is None, and the page's line under his name fills "Your model, from {file}." with nothing."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        (self.models / f"{STEM}@2.json").unlink()
        info = self.every_language_info()
        said = {lang: now_said(self.words(lang), i["soldiers"][1]) for lang, i in info.items()}
        print("\nSQ-8:", said["us"])
        self.assert_worded(said)
        self.assertNotIn(" .", said["us"])


class TwoSquadsInOneMod(Unusual):
    def test_each_its_own_number_and_looks(self):
        """Usual: two new squads in one mod, the first +1 (6) and soldier 2 a look of his own, the second -1 (4) and
        soldier 1 a look of his own: each page its own, each built with its own number and look, the check finds
        nothing."""
        other = self.page.new_unit(GAME_SQUAD, "My Other Squad", 50)["address"]
        self.page.soldier_plus(SQUAD)
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        self.page.soldier_minus(other)
        self.page.soldier_import(other, "1", str(self.model_file("ranger.glb", b"glTF ranger")))
        self.assertEqual((self.info()["count"], self.info("us", other)["count"]), (6, 4))
        self.assert_worded({lang: self.info(lang, other)["line"] for lang in LANGS})
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual((self.own_count(loaded), self.own_count(loaded, OTHER_STEM)), (6, 4))
        self.assertEqual(sorted(result.own_models), [f"{OTHER_STEM}@1", f"{STEM}@2"])
        self.assertEqual(self.problems(), [])


class AFewestOfThree(Unusual):
    def test_minus_down_to_its_three_and_plus_before_them(self):
        """Usual: a new squad copying the game's squad of three charges (its last three fire one each): -1 takes out
        the soldiers before them (2, then 1), then -1 is refused in every language naming the weapon (in the game's
        texts; the made-up game has none, so its name); +1 joins before the three. It builds with 4."""
        sappers = self.page.new_unit(CHARGES, "My Sappers", 50)["address"]
        self.assertEqual(self.info("us", sappers)["fewest"], 3)
        self.assertEqual([self.page.soldier_minus(sappers)["removed"] for _ in range(2)], ["2", "1"])
        said = "This squad keeps at least 3 soldiers: its last 3 fire Ammo_Bazooka, one each."
        self.assert_worded(self.refused("soldier_minus", sappers), said)
        self.assert_worded({lang: self.info(lang, sappers)["limits"]["remove"] for lang in LANGS}, said)
        r = self.page.soldier_plus(sappers)
        self.assertEqual((r["joined"], r["count"]), ("1", 4))
        self.assertEqual([bool(s["fires"]) for s in r["soldiers"]], [False, True, True, True])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded, "Descriptor_Unit_My_Sappers"), 4)
        self.assertEqual(self.problems(), [])


class ImportOnASoldiersLine(Unusual):
    def test_another_file_on_the_same_line(self):
        """Usual: Import a model... on soldier 2's line, then again from another file: his look is the second file's,
        one look file for him, the page names the file, and it builds."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        first = (self.models / f"{STEM}@2.glb").read_bytes()
        r = self.page.soldier_import(SQUAD, "2", str(self.model_file("ranger.glb", b"glTF ranger")))
        self.assertEqual(r["model"]["file"], "ranger.glb")
        self.assertNotEqual((self.models / f"{STEM}@2.glb").read_bytes(), first)
        self.assertEqual(self.info()["soldiers"][1]["from"], "ranger.glb")
        self.assertEqual(self.soldier_files(), [f"{STEM}@2.glb", f"{STEM}@2.json"])
        result, _loaded = self.built()
        self.assertEqual((self.errors(result), sorted(result.own_models)), ([], [f"{STEM}@2"]))

    @unittest.expectedFailure    # finding SQ-6: a file that isn't a model: English in every language, named twice
    def test_a_file_that_isn_t_a_model(self):
        """Unusual: the file picker's file isn't a model (a broken .glb, a .txt): refused (the Studio's own fitting
        reads it), nothing changed; its words name the file twice and are English in every language."""
        before = self.files()
        with mock.patch("rusemod.unitmodel.import_model", REAL_FITTING):
            for name, data in (("broken.glb", b"this is not a model"), ("notes.txt", b"hello")):
                with self.subTest(file=name):
                    said = self.refused("soldier_import", SQUAD, "2", str(self.model_file(name, data)))
                    print(f"\nSQ-6 {name}:", {lang: said[lang] for lang in ("us", "fr", "jpn")})
                    self.assertEqual(self.files(), before)
                    self.assertEqual(said["us"].count(name), 1, said["us"])
                    self.assert_worded(said)


class TheSquadsOwnModel(Unusual):
    def test_the_riflemen_s_model_one_back_to_the_game_s_look_and_plus_one(self):
        """Usual (a squad made before each soldier had his own look, or with the Model row's Import model): the
        riflemen's model for the squad (every rifleman wears it); Back to the game's look on soldier 2 (him alone: a
        record says so); +1 joins wearing what most riflemen wear (the riflemen's model: no file of his own); then Back
        to the game's look on the others one by one: when the last one wearing it is back, the model leaves the mod,
        and so do the records. Each step builds and the check finds nothing."""
        r = self.page.model_import(SQUAD, str(self.model_file("riflemen.glb", b"glTF riflemen")))
        self.assertEqual(r["model"]["file"], "riflemen.glb")
        self.assertEqual([s["wears"] for s in self.info()["soldiers"]], ["kind"] * 4 + ["game"])
        r = self.page.soldier_reset(SQUAD, "2")
        self.assertEqual(r["game_look"], True)
        self.assertEqual([s["wears"] for s in self.info()["soldiers"]], ["kind", "game", "kind", "kind", "game"])
        r = self.page.soldier_plus(SQUAD)
        self.assertEqual((r["joined"], r["count"]), ("5", 6))
        self.assertEqual([s["wears"] for s in r["soldiers"]], ["kind", "game", "kind", "kind", "kind", "game"])
        self.assertEqual(self.soldier_files(), [f"{STEM}.glb", f"{STEM}.json", f"{STEM}.squad.toml", f"{STEM}@2.json"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.own_count(loaded), 6)
        self.assertEqual(self.problems(), [])
        for soldier in ("1", "3", "4"):
            self.assertTrue(self.page.soldier_reset(SQUAD, soldier)["game_look"], soldier)
        r = self.page.soldier_reset(SQUAD, "5")
        self.assertEqual((r["model_out"], r["game_look"]), (True, False))
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml"])
        self.assertEqual({s["wears"] for s in self.info()["soldiers"]}, {"game"})
        result, loaded = self.built()
        self.assertEqual((self.errors(result), self.own_count(loaded)), ([], 6))
        self.assertEqual(self.problems(), [])


if __name__ == "__main__":
    unittest.main()
