"""Scenarios: a squad soldier by soldier, as a player meets it in the RUSE Studio's squad page (squad.js on
ruse_studio.squadblender): a new squad as the game has it, +1 and -1 (at 5, up to 8, down to 2, and past each), a look
of his own and Back to the game's look on a soldier's line, a Custom uniform before and after a soldier's own look.
Each ends with what the page says in every language, the mod's files, its build on the made-up game and the Studio's
check of it. The base, its made-up game and its stand-ins: tests/test_scenarios_squads_base.py.

FOR: the squads scenarios (release 0.9.8.20, overnight 2026-11-13/14). USED-BY: the scenarios' run and report."""
import unittest

from test_scenarios_squads_base import (GAME_SQUAD, LANGS, SQUAD, STEM, SquadScenario)


def plus_said(w: dict, r: dict) -> str:
    """What the page says after +1 (squad.js countBy)."""
    return w["squad_added"].replace("{n}", str(r["count"]))


def minus_said(w: dict, r: dict) -> str:
    """What the page says after -1 (squad.js countBy): how many now, a look of his own kept aside, a uniform back."""
    parts = [w["squad_removed"].replace("{number}", str(r["removed"])).replace("{n}", str(r["count"])),
             w["squad_minus_kept"] if r.get("look_kept") else "", w["squad_reset_uniform"] if r.get("copy_back") else ""]
    return " ".join(p for p in parts if p)


class ANewSquad(SquadScenario):
    def test_as_the_game_has_it(self):
        """Usual: New unit copying the game's squad. Its page: 5 soldiers, 4 riflemen and the bazooka man, every
        button there and no limit said; every language its own words. The mod: the copy alone, no soldier's file. It
        builds on the game, and the Studio's check finds nothing."""
        infos = self.every_language_info()
        us = infos["us"]
        self.assertEqual((us["count"], us["own"], [r["id"] for r in us["soldiers"]]), (5, True, list("12345")))
        self.assertEqual([r["label"] for r in us["soldiers"]], ["Rifleman"] * 4 + ["Bazooka man"])
        self.assertEqual({k: us["can"][k] for k in ("add", "remove", "import", "blender")},
                         {"add": True, "remove": True, "import": True, "blender": True})
        self.assertEqual((us["limits"], us["why_not"]), ({"add": None, "remove": None}, None))
        self.assert_worded({lang: i["line"] for lang, i in infos.items()})
        self.assert_worded({lang: i["soldiers"][4]["label"] for lang, i in infos.items()})
        self.assertEqual(self.soldier_files(), [])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertIn(SQUAD, loaded.base.objects)
        self.assertNotIn("R2Behaviour", loaded.base.objects[SQUAD].props)
        self.assertEqual(result.game_patch, [])
        self.assertEqual(self.problems(), [])

    def test_a_game_squad_s_page(self):
        """Usual: the game's own squad opened: shown as it is, nothing of it changeable, and why in every language."""
        infos = self.every_language_info(GAME_SQUAD)
        us = infos["us"]
        self.assertEqual((us["own"], us["count"]), (False, 5))
        self.assertFalse(any(us["can"].values()), us["can"])
        self.assert_worded({lang: i["why_not"] for lang, i in infos.items()})
        for name, args in (("soldier_plus", (GAME_SQUAD,)), ("soldier_minus", (GAME_SQUAD,)),
                           ("soldier_remove", (GAME_SQUAD, "2")), ("soldier_add", (GAME_SQUAD, "copy", "1"))):
            with self.subTest(call=name):
                self.assert_worded(self.refused(name, *args),
                                   "This is one of the game's own squads: copy it first, then change the copy.")
        self.assertFalse((self.mod / "files").exists())


class PlusAndMinus(SquadScenario):
    def test_plus_one_at_5_joins_before_the_bazooka_man(self):
        """Usual: +1 on a squad of 5: soldier 5 joins as a rifleman, the bazooka man is soldier 6, the squad 6 (its
        own number, in the mod). The page says it in every language; it builds with its own number (the own-squads
        patch named), and the Studio's check finds nothing."""
        r = self.page.soldier_plus(SQUAD)
        self.assertEqual((r["joined"], r["count"]), ("5", 6))
        self.assertEqual([s["label"] for s in r["soldiers"]], ["Rifleman"] * 5 + ["Bazooka man"])
        self.assert_worded({lang: plus_said(self.words(lang), r) for lang in LANGS},
                           "One soldier more: the squad has 6 now.")
        self.assertEqual(self.soldier_files(), [f"{STEM}.squad.toml"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        own = loaded.base.objects[SQUAD].props["R2Behaviour"].obj.props["NbSoldatInGroupeCombat"]
        self.assertEqual(int(own.value), 6)
        self.assertEqual(result.game_patch, ["own-squads"])
        self.assertEqual(self.problems(), [])

    def test_up_to_8_and_one_more_refused(self):
        """Usual then unusual: +1 three times (6, 7, 8), then +1 at 8: refused in every language, the button off and
        its reason on the card, nothing changed."""
        for n in (6, 7, 8):
            self.assertEqual(self.page.soldier_plus(SQUAD)["count"], n)
        before = self.files()
        self.assert_worded(self.refused("soldier_plus", SQUAD), "A squad has at most 8 soldiers for now.")
        self.assert_worded(self.refused("soldier_add", SQUAD, "copy", "1"), "A squad has at most 8 soldiers for now.")
        infos = self.every_language_info()
        self.assertEqual((infos["us"]["can"]["add"], infos["us"]["can"]["remove"]), (False, True))
        self.assert_worded({lang: i["limits"]["add"] for lang, i in infos.items()},
                           "A squad has at most 8 soldiers for now.")
        self.assertEqual(self.files(), before)
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        own = loaded.base.objects[SQUAD].props["R2Behaviour"].obj.props["NbSoldatInGroupeCombat"]
        self.assertEqual(int(own.value), 8)

    def test_down_to_2_and_one_fewer_refused(self):
        """Usual then unusual: -1 three times (4, 3, 2: each time the last rifleman, the bazooka man last); then -1
        at 2 and Remove of either: refused in every language, nothing changed. It builds with its own 2."""
        for n, out in ((4, "4"), (3, "3"), (2, "2")):
            r = self.page.soldier_minus(SQUAD)
            self.assertEqual((r["count"], r["removed"]), (n, out))
            self.assertEqual(r["soldiers"][-1]["label"], "Bazooka man")
        self.assert_worded({lang: minus_said(self.words(lang), r) for lang in LANGS},
                           "Soldier 2 is out of the squad: it has 2 soldiers now.")
        before = self.files()
        said = "A squad keeps at least 2 soldiers: the game's own rule."
        self.assert_worded(self.refused("soldier_minus", SQUAD), said)
        for soldier in ("1", "2"):
            self.assert_worded(self.refused("soldier_remove", SQUAD, soldier), said)
        infos = self.every_language_info()
        self.assertEqual((infos["us"]["can"]["add"], infos["us"]["can"]["remove"]), (True, False))
        self.assert_worded({lang: i["limits"]["remove"] for lang, i in infos.items()}, said)
        self.assertEqual(self.files(), before)
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        own = loaded.base.objects[SQUAD].props["R2Behaviour"].obj.props["NbSoldatInGroupeCombat"]
        self.assertEqual(int(own.value), 2)

    def test_plus_then_minus_leaves_the_squad_as_it_was(self):
        """Usual: +1 then -1: the mod's files byte for byte as before (the number back to the game's: no file); only
        the squad's Blender folder (never packed, never built) keeps a state file the two wrote."""
        before = self.files()
        self.page.soldier_plus(SQUAD)
        r = self.page.soldier_minus(SQUAD)
        self.assertEqual((r["removed"], r["count"], r["look_kept"]), ("5", 5, False))
        after = self.files()
        self.assertEqual(sorted(k for k in after if k not in before), [f"blender/{STEM}/squad/state.json"])
        self.assertEqual({k: v for k, v in after.items() if not k.startswith("blender/")}, before)
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertNotIn("R2Behaviour", loaded.base.objects[SQUAD].props)


class ALookOfHisOwn(SquadScenario):
    def test_import_a_model_on_his_line_then_back_to_the_game_s_look(self):
        """Usual: Import a model… on soldier 2's line: his own look, the others' as they were; the page says it in
        every language; it builds with his own look (R2SoldierLooks) and the check finds nothing. Back to the game's
        look on his line: his files leave the mod, the page says so, and it builds as the game's squad again."""
        marine = self.model_file("marine.glb", b"glTF marine")
        r = self.page.soldier_import(SQUAD, "2", str(marine))
        self.assertEqual(r["model"]["file"], "marine.glb")
        label = self.info()["soldiers"][1]["label"]
        self.assert_worded({lang: self.words(lang)["squad_import_done"].replace("{who}", label)
                            .replace("{file}", "marine.glb") for lang in LANGS})
        self.assertEqual(self.soldier_files(), [f"{STEM}@2.glb", f"{STEM}@2.json"])
        self.assertEqual([s["wears"] for s in self.info()["soldiers"]], ["game", "own", "game", "game", "game"])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertIn("R2SoldierLooks", loaded.base.objects[SQUAD].props)
        self.assertEqual(self.problems(), [])
        r = self.page.soldier_reset(SQUAD, "2")
        self.assertEqual((r["model_out"], r["game_look"]), (True, False))
        self.assert_worded({lang: self.words(lang)["squad_reset_done"].replace("{who}", label) for lang in LANGS})
        self.assertEqual(self.soldier_files(), [])
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertNotIn("R2SoldierLooks", loaded.base.objects[SQUAD].props)

    def test_the_bazooka_man_s_own_look(self):
        """Usual: the bazooka man (soldier 5) his own look: fitted to the bazooka man's figure, built as his."""
        r = self.page.soldier_import(SQUAD, "5", str(self.model_file("bazooka.glb", b"glTF bazooka")))
        self.assertEqual(r["model"]["file"], "bazooka.glb")
        self.assertEqual(self.fits[-1][1], "ww2\\res3d\\units\\us\\infanterie\\us_soldier_bazooka_modellod0.ase2ndfbin")
        result, loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(sorted(result.own_models), [f"{STEM}@5"])


class ACustomUniform(SquadScenario):
    def test_a_uniform_then_a_soldier_s_own_look_then_back(self):
        """Usual: Custom uniform on the squad, then Import a model… on soldier 2's line: the uniform comes off (a
        squad can't have both: the page says so), kept in his model's record; Back to the game's look on his line:
        the uniform back. Each step builds, and the check finds nothing."""
        r = self.page.model_copy(SQUAD)
        self.assertTrue((self.models / f"{STEM}.copy.toml").is_file(), r)
        result, _loaded = self.built()
        self.assertEqual(self.errors(result), [])
        r = self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        self.assertTrue(r["copy_out"])
        self.assert_worded({lang: self.words(lang)["squad_copy_out"] for lang in LANGS})
        self.assertFalse((self.models / f"{STEM}.copy.toml").exists())
        result, _loaded = self.built()
        self.assertEqual(self.errors(result), [])
        r = self.page.soldier_reset(SQUAD, "2")
        self.assertTrue(r["copy_back"])
        self.assert_worded({lang: self.words(lang)["squad_reset_uniform"] for lang in LANGS})
        self.assertTrue((self.models / f"{STEM}.copy.toml").is_file())
        result, _loaded = self.built()
        self.assertEqual(self.errors(result), [])
        self.assertEqual(self.problems(), [])

    @unittest.expectedFailure    # finding SQ-11: Custom uniform and Back to the default uniform said in English only
    def test_the_uniform_s_words_in_every_language(self):
        """The Uniform row's two buttons (app.js uniformBox) say the call's own "message" (say(r.message)): model_copy's
        and model_copy_remove's are English sentences in the code (api.model_copy), with no entry in the words, so the
        page says them in English in every language."""
        said, back = {}, {}
        for lang in LANGS:
            self.api.set_pref("lang", lang)
            said[lang] = self.page.model_copy(SQUAD)["message"]
            back[lang] = self.page.model_copy_remove(SQUAD)["message"]
        self.api.set_pref("lang", "us")
        print("\nSQ-11:", said["us"], "|", said["fr"])
        self.assert_worded(said)
        self.assert_worded(back)

    @unittest.expectedFailure    # finding SQ-1: a soldier's own look, then Custom uniform: the mod no longer builds
    def test_a_soldier_s_own_look_then_a_uniform(self):
        """Unusual: Import a model… on soldier 2's line first, then Custom uniform on the squad: the Studio takes it
        (it looks only for the squad's own model, files/models/<unit>.glb, never a soldier's), and the mod then has a
        uniform and a soldier's model together, which its build refuses (rusemod.build.unit_own_copies: one model per
        unit), its words naming files/models/<unit>.glb, a file the mod hasn't got. Either the uniform is refused in
        words, as it is over the squad's own model, or the mod builds."""
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        # (the page's Custom uniform button is off only while look() has the squad's own model: app.js uniformBox)
        button_on = not self.page.look(SQUAD).get("own_model")
        said = self.refused("model_copy", SQUAD)
        made = (self.models / f"{STEM}.copy.toml").is_file()
        result, _loaded = self.built()
        print("\nSQ-1 model_copy after a soldier's look: button on", button_on, "|",
              "refused: " + str(said["us"]) if said["us"] else "taken", "| build:", self.errors(result), "| check:",
              self.problems())
        self.assertTrue(said["us"] is not None or not self.errors(result), (made, self.errors(result)))


if __name__ == "__main__":
    unittest.main()
