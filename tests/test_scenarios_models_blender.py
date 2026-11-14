"""Scenarios: the one Blender button on a new tank's page, with every tick, and the ways a player leaves Blender (the
owner, overnight 2026-11-13: "Usual and unusual situations"): everything ticked and a repaint; Its paint unticked on a
later trip; Its model unticked and Its paint ticked; nothing ticked; Blender closed without Send; two Blenders; Send
twice; Bring back twice; another file imported after a trip; the model taken out, or the unit deleted, while its
Blender is open. Blender is stood in (test_scenarios_models_base: what it opens is recorded, what its Send writes is
written as Blender 4.5 writes it, test_modelblender's blender_sends). Each ends with what the page says, the mod's
files and its build on the made-up game.

A finding is kept as an expected failure naming it (M-n: D:/RUSE-2.0/scratch/release-0920/scenarios/models/NOTES.md
and the scenarios report); the rest pass on release/0.9.8.20-anim 0d5564eb.

FOR: the models and Blender scenarios (release 0.9.8.20, overnight 2026-11-14).
USED-BY: the scenarios' runs (gentle.py, -m unittest)."""
import hashlib
import json
import unittest
from pathlib import Path
from unittest import mock

from rusemod.dxt import png_bytes
from rusemod.png import read_png
from test_modelblender import blender_sends
from test_scenarios_models_base import LANGS, NAME, PANZER, STEM, ModelScenario
from test_scenarios_models_files import colours_in, picture, repaint, tank_glb

RED, BLUE = (200, 30, 30), (30, 40, 210)
ALL = {"model": True, "paint": True}
PAINT_UNTICKED = {"model": True, "paint": False}
PAINT_ALONE = {"model": False, "paint": True}


class OneButton(ModelScenario):
    """A new tank with its own model (tank.glb, one material "Paint"), its page's one Blender button."""

    def setUp(self):
        super().setUp()
        self.page.model_import(self.unit, str(self.his_file("tank.glb", tank_glb())))
        self.first = colours_in(self.models / f"{STEM}.glb")["Paint"]   # (its paint as imported)
        stack = self.blender_stood_in()
        stack.__enter__()
        self.addCleanup(stack.__exit__, None, None, None)

    def opens(self, ticks=ALL) -> dict:
        return self.page.blender_open(self.unit, ticks)

    def sends(self, colour=None, session: str | None = None) -> None:
        """Blender sends what it opened last (`colour`: the "Paint" material repainted so there); `session`: the
        sending marked as sent by that opening (Send writes it beside the file: rusemod.blender_model's ABOUT)."""
        blender_sends(self.opened[-1], self.send)
        if colour is not None:
            repaint(self.send, {"Paint": colour})
        if session is not None:
            raw = self.send.read_bytes()
            self.send.with_name(self.send.name + ".json").write_text(json.dumps(
                {"glb": hashlib.sha256(raw).hexdigest(), "session": session}), encoding="utf-8")

    def session(self) -> str:
        return json.loads((self.work / "words.json").read_text(encoding="utf-8"))["session"]

    def paint(self) -> tuple:
        return colours_in(self.models / f"{STEM}.glb")["Paint"]

    def assert_builds(self) -> None:
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), stopped, list(written)), ([], [], [STEM]))

    # --- the ticks ---
    def test_what_a_tank_with_its_own_model_can_tick(self):
        parts = self.page.blender_parts(self.unit)
        self.assertEqual((parts["route"], [p["id"] for p in parts["parts"]], parts["can"]), ("model", ["model", "paint"],
                                                                                              True))
        for lang in LANGS:     # (the ticks' words, as the page shows them)
            with self.subTest(lang=lang):
                labels = [p["label"] for p in self.page.blender_parts(self.unit, lang)["parts"]]
                self.assertTrue(all(labels), lang)
                if lang != "us":
                    self.assertNotEqual(labels, [p["label"] for p in parts["parts"]], lang)

    def test_everything_ticked_a_repaint_comes_back_and_builds(self):
        self.assertEqual(self.opens()["door"], "model")
        self.assertEqual(self.opened[-1].name, f"{STEM}_own.glb")       # (its own model, not the game's)
        self.sends(RED)
        got = self.page.blender_back(self.unit)
        self.assertEqual((got["door"], got["kept"], self.paint()), ("model", {"bones": None, "paint": None}, RED))
        self.assertEqual(self.record()["from"], str(self.work / "kept" / self.send.name))
        self.assert_builds()

    def test_paint_unticked_on_the_first_trip_keeps_its_paint(self):
        """Its paint unticked on the first trip, the hull repainted in Blender: its paint stays as imported."""
        self.opens(PAINT_UNTICKED)
        self.sends(RED)
        got = self.page.blender_back(self.unit)
        self.assertEqual((got["kept"]["paint"], self.paint()), (["Paint"], self.first))
        self.assert_builds()

    def test_m3_paint_unticked_on_a_later_trip_keeps_the_repaint_brought_back(self):
        """M-3 (the paint-unticked loss): repainted red and brought back, then a trip with Its paint unticked, repainted
        blue there: the tank went back to the paint it was imported with, (90, 110, 60), and the answer said its paint
        was kept ("kept": {"paint": ["Paint"]}) (work/0920c-scen-models eccd02d9). PROPOSED FIX on
        work/0920c-paint-unticked (4680a5eb): it stays red, the paint it has now."""
        self.opens()
        self.sends(RED)
        self.page.blender_back(self.unit)
        self.opens(PAINT_UNTICKED)
        self.sends(BLUE)
        self.page.blender_back(self.unit)
        self.assertEqual(self.paint(), RED)

    @unittest.expectedFailure
    def test_m4_its_paint_alone_repaints_its_own_model(self):
        """M-4: Its model unticked, Its paint ticked, on a tank with a model of its own: Blender opens the copied
        game Panzer (the Look box's Repaint in Blender: ger_panzeriv.glb with the game's pictures), and Bring my changes
        back puts the painted picture in files/replace, where it repaints the game's Panzer and every unit drawn with
        that picture; the tank's own model is as it was, and the page says "Brought back 1 painted picture(s) into
        models. Click Test in game to see them." What should happen: its own model's paint is what goes to Blender
        and comes back (or the page says this tick paints the copied unit's pictures, every unit drawn with them)."""
        opened = []
        with mock.patch("rusemod.blender.open_models", lambda b, models: opened.append(models) or None):
            got = self.opens(PAINT_ALONE)
            self.assertEqual(got["door"], "paint")
            folder = Path(self.api._look_folder(self.unit))
            record = json.loads((folder / "look.json").read_text(encoding="utf-8"))
            colour = next(folder / k for k, v in record["pictures"].items() if v.get("kind") != "alpha")
            w, h, _rgba = read_png(colour.read_bytes())
            colour.write_bytes(png_bytes(bytes((255, 0, 255)) * (w * h), w, h))      # painted pink there
            self.page.blender_back(self.unit)
        replaced = [k for k in self.files() if k.startswith("files/replace/")]
        self.assertEqual((replaced, self.paint()), ([], (255, 0, 255)),
                         f"opened {[Path(m).name for m in opened[-1]]}")

    @unittest.expectedFailure
    def test_m7_blender_s_words_name_this_page_s_button(self):
        """M-7: Blender opened by the one Blender button on a tank is given the soldier door's words (its words.json):
        "Sent. Now click Bring back the model in the R.U.S.E. Studio." and "Change the soldier, or bring in your own
        model (File > Import) and put it on his bones...", while this page's button is "Bring my changes back" and the
        unit is a tank. What should happen: Blender names the button the page has (and doesn't speak of a soldier)."""
        self.opens()
        words = json.loads((self.work / "words.json").read_text(encoding="utf-8"))
        self.assertIn(self.words("us")["squad_blender_back"], words["sent"])
        self.assertNotIn("soldier", " ".join(words["hint"]))

    def test_nothing_ticked_is_refused_in_every_language(self):
        said = self.said("blender_open", self.unit, {"model": False, "paint": False})
        self.assert_worded(said, "Tick what goes to Blender first: the model, its bones or its paint.")
        self.assertEqual(self.opened, [])

    # --- leaving Blender ---
    def test_closed_without_send_is_refused_in_every_language_and_changes_nothing(self):
        before = self.files()
        self.opens()
        said = self.said("blender_back", self.unit)
        self.assert_worded(said, "Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. "
                                 "Studio at the top, then Bring my changes back here.")
        self.assertEqual({k: v for k, v in self.files().items() if k.startswith("files/")},
                         {k: v for k, v in before.items() if k.startswith("files/")})

    def test_two_blenders_the_first_one_s_sending_is_refused_the_second_s_taken(self):
        """Opened twice (two Blenders on it): what the first sends is refused in words in every language, nothing
        taken; what the second sends comes in."""
        self.opens()
        first = self.session()
        self.opens()
        second = self.session()
        self.assertNotEqual(first, second)
        self.sends(RED, session=first)
        said = self.said("blender_back", self.unit)
        self.assert_worded(said, "What came back was sent by a Blender opened before the one opened last, so it can't "
                                 "be taken in: close that Blender, then in the one opened last click Send to the "
                                 "R.U.S.E. Studio and bring your changes back.")
        self.assertEqual(self.paint(), self.first)
        self.sends(BLUE, session=second)
        self.page.blender_back(self.unit)
        self.assertEqual(self.paint(), BLUE)
        self.assert_builds()

    def test_send_twice_the_last_comes_back(self):
        self.opens()
        self.sends(RED)
        self.sends(BLUE)                         # (changed again there, Send again: the file written over)
        self.page.blender_back(self.unit)
        self.assertEqual(self.paint(), BLUE)

    def test_bring_back_twice_changes_nothing_the_second_time(self):
        self.opens()
        self.sends(RED)
        self.page.blender_back(self.unit)
        once = {k: v for k, v in self.files().items() if k.startswith("files/")}
        self.page.blender_back(self.unit)
        self.assertEqual({k: v for k, v in self.files().items() if k.startswith("files/")}, once)
        self.assertEqual(self.paint(), RED)

    # --- the model changed or gone while Blender has it ---
    @unittest.expectedFailure
    def test_m5_another_file_imported_after_a_trip_is_what_blender_opens(self):
        """M-5 (SQ-10's kind, through Import model): a trip brought back, then Import model of another file (camo.glb,
        its material "Camo"); the one Blender button then opens Blender's last sending, the model from before (its
        material "Paint"), and Bring my changes back puts that model in place of camo.glb, its record no longer naming
        it, without a word. What should happen: Blender opens the model the unit has now (camo.glb's), as it does for a
        unit never opened in Blender."""
        self.opens()
        self.sends(RED)
        self.page.blender_back(self.unit)
        camo = self.his_file("camo.glb", tank_glb(materials=[("Camo", picture(16, 16, seed=40))]))
        self.page.model_import(self.unit, str(camo))
        self.opens()
        doc = json.loads(self.opened[-1].read_bytes()[20:20 + int.from_bytes(self.opened[-1].read_bytes()[12:16],
                                                                               "little")])
        self.assertEqual([m["name"] for m in doc["materials"]], ["Camo"], f"opened {self.opened[-1].name}")

    def test_another_file_imported_after_a_trip_its_record_names_it_until_blender(self):
        """The part of M-5 that holds: Import model after a trip makes camo.glb the model, its record naming it, and
        the mod builds with it."""
        self.opens()
        self.sends(RED)
        self.page.blender_back(self.unit)
        camo = self.his_file("camo.glb", tank_glb(materials=[("Camo", picture(16, 16, seed=40))]))
        self.page.model_import(self.unit, str(camo))
        self.assertEqual((self.record()["from"], list(colours_in(self.models / f"{STEM}.glb"))), (str(camo), ["Camo"]))
        self.assert_builds()

    def test_the_model_taken_out_while_blender_is_open_comes_back_with_bring_back(self):
        """Use the copied unit's model while Blender is open: the model goes; Bring my changes back, clicked after,
        takes what Blender sends in as the unit's model again (what the player asked for last)."""
        self.opens()
        self.page.model_import_remove(self.unit)
        self.assertEqual(self.model_files(), [])
        self.sends(RED)
        self.page.blender_back(self.unit)
        self.assertEqual((self.model_files(), self.paint()), ([f"{STEM}.glb", f"{STEM}.json"], RED))
        self.assert_builds()

    @unittest.expectedFailure
    def test_sq5_on_the_model_door_a_deleted_unit_s_blender_is_not_the_new_one_s(self):
        """SQ-5's kind on a tank (scenarios/squads found it on a squad): the tank deleted while its Blender has a
        sending, then New unit under the same name: the new tank's one Blender button reads Bring my changes back
        (its door open) and brings the deleted tank's model in. Before that, Bring back on the deleted tank is refused
        as "Only a new unit made in this mod can get a model of its own: copy the unit first.", and the deleted tank's
        Blender folder stays in the mod. What should happen: the new tank starts with nothing to bring back."""
        self.opens()
        self.sends(RED)
        self.page.delete_unit(self.unit)
        self.assertEqual(self.refusal("blender_back", self.unit),
                         "Only a new unit made in this mod can get a model of its own: copy the unit first.")
        self.assertEqual(self.page.new_unit(PANZER, NAME, 50, group="new")["address"], self.unit)
        parts = self.page.blender_parts(self.unit)
        self.assertEqual((parts["open"], parts["door"]), (False, None))


if __name__ == "__main__":
    unittest.main()
