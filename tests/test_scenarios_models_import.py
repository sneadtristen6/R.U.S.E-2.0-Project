"""Scenarios: Import model… on a new tank with every kind of model file a player brings (the owner, overnight
2026-11-13: "Usual and unusual situations"): a tank from Blender, the same tank in centimetres or a thousandth of its
size, forty materials, a picture of 2048 pixels, a scan of 90,000 points, names in other scripts, a creature with bones
of its own and an animation, and the broken files a player ends up with (empty, a text or a zip renamed, cut in half,
its text part broken, nothing to draw, only lines or points). Each ends with what the page says, the mod's files and
the mod's build on the made-up game (test_scenarios_models_base).

A finding is kept as an expected failure naming it (M-n: D:/RUSE-2.0/scratch/release-0920/scenarios/models/NOTES.md
and the scenarios report); the rest pass on release/0.9.8.20-anim 0d5564eb.

FOR: the models and Blender scenarios (release 0.9.8.20, overnight 2026-11-14).
USED-BY: the scenarios' runs (gentle.py, -m unittest)."""
import unittest

from rusemod import modelin, unitmodel
from test_ownrig import little_glb, turn_about
from test_scenarios_models_base import LANGS, STEM, ModelScenario
from test_scenarios_models_files import broken_files, grid_glb, picture, tank_glb

RUN = [("Run", [(2, "rotation", (0.0, 0.5, 1.0), [(0, 0, 0, 1), turn_about("x", 30.0), (0, 0, 0, 1)], "LINEAR")])]


class Imported(ModelScenario):
    """A file Import model takes: the page's words, the mod's files, the build."""

    def imported(self, name: str, data: bytes) -> dict:
        got = self.page.model_import(self.unit, str(self.his_file(name, data)))
        self.assertTrue(got["model"])
        return got

    def assert_built(self, vertices: int, textures: int) -> dict:
        """The mod builds on the made-up game, its model written into the game's packs with `vertices` points and
        `textures` pictures of its own; returns the written report."""
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), stopped), ([], []))
        self.assertEqual(list(written), [STEM])
        report = written[STEM].report
        self.assertEqual((report["vertices"], len(written[STEM].added)), (vertices, textures))
        return report

    def test_a_tank_from_blender_is_the_unit_s_model_and_builds(self):
        """The usual case: the page says the file is now the unit's model, in every language; the mod has the model
        and its record, which names the file; the build writes it beside the copied Panzer."""
        f = self.his_file("tank.glb", tank_glb())
        got = self.page.model_import(self.unit, str(f))
        self.assertEqual((got["model"]["file"], got["model"]["vertices"], got["copy_out"]), ("tank.glb", 24, False))
        said = {lang: self.words(lang)["model_done"].format(file=got["model"]["file"]) for lang in LANGS}
        self.assert_worded(said, "tank.glb is now this unit's model. Click Test in game to see it.")
        self.assertEqual(self.model_files(), [f"{STEM}.glb", f"{STEM}.json"])
        self.assertEqual(self.record()["from"], str(f))
        self.assertEqual(self.page.look(self.unit)["own_model"]["file"], "tank.glb")
        self.assert_built(24, 1)
        self.assertEqual(self.problems(), [])

    def test_in_centimetres_a_thousandth_or_under_a_scaled_empty_it_comes_in_the_same(self):
        """Wrong scale: the same tank written 100 times bigger (centimetres), 1000 times smaller, or 100 times bigger
        under an empty scaled to a hundredth (Blender's scale not applied): each is fitted to the copied unit's length,
        so the mod's model has the same points every time, and builds."""
        points = {}
        for name, data in (("tank.glb", tank_glb()), ("tank_cm.glb", tank_glb(scale=100.0)),
                           ("tank_tiny.glb", tank_glb(scale=0.001)),
                           ("tank_empty.glb", tank_glb(scale=100.0, root_scale=0.01))):
            with self.subTest(file=name):
                self.imported(name, data)
                prep = unitmodel.read_mod_glb(self.models / f"{STEM}.glb")
                points[name] = sorted(tuple(round(c, 2) for c in p) for part in prep.parts for p in part.positions)
                self.assert_built(24, 1)
        self.assertEqual(len({tuple(p) for p in points.values()}), 1, "the four files gave different models")

    def test_forty_materials_each_with_its_picture(self):
        """Forty materials, a picture each: forty pictures in the mod's model and forty textures written by the
        build, one draw each."""
        parts = [(f"Plate{k}", (-1.5 + k * 0.07, 0.3, -3.25), (-1.45 + k * 0.07, 1.5, 3.25)) for k in range(40)]
        got = self.imported("plates.glb", tank_glb(parts=parts, part_material=list(range(40)),
                                                   materials=[(f"Steel{k}", picture(8, 8, seed=k)) for k in range(40)]))
        self.assertEqual(len(got["model"]["pictures"]), 40)
        report = self.assert_built(320, 40)
        self.assertEqual(report["draws"], 40)

    def test_names_in_other_scripts(self):
        """The file, its folder, its parts, its material and its picture named in Russian, Chinese, Persian and with
        an emoji: imported, the page names the file as it is in every language, the record keeps its path whole, a
        Resize fits it again from that file, and the mod builds."""
        f = self.home / "мои модели 我的模型" / "танк 坦克 تانک 🛡.glb"
        f.parent.mkdir(parents=True)
        f.write_bytes(tank_glb(names={"Hull": "Корпус", "Turret": "炮塔", "Gun": "توپ"},
                               materials=[("Краска 🎨", picture())], image_names=["بدنه"]))
        got = self.page.model_import(self.unit, str(f))
        self.assertEqual(got["model"]["file"], "танк 坦克 تانک 🛡.glb")
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertIn("танк 坦克 تانک 🛡.glb", self.words(lang)["model_done"].format(file=got["model"]["file"]))
        self.assertEqual(self.record()["from"], str(f))
        self.page.model_resize(self.unit, 1.25)
        self.assertEqual((self.record()["from"], self.record()["size"]), (str(f), 1.25))
        self.assert_built(24, 1)

    def test_a_picture_of_2048_pixels_comes_in_smaller(self):
        """A picture of 2048 x 2048: the mod's model keeps it at 1024 x 1024, as every picture the import takes; the
        build writes it."""
        got = self.imported("big_picture.glb", tank_glb(materials=[("Paint", picture(2048, 2048))]))
        self.assertEqual([tuple(p) for p in got["model"]["pictures"]], [("Paint", 1024, 1024)])
        self.assert_built(24, 1)

    def test_a_scan_of_90000_points_in_one_part_builds(self):
        """A scan of 300 x 300 points in one part (more than a 16-bit index reaches): imported whole and written with
        32-bit indices, one draw."""
        got = self.imported("scan.glb", grid_glb(300))
        self.assertEqual((got["model"]["vertices"], got["model"]["triangles"]), (90000, 178802))
        report = self.assert_built(90000, 1)
        self.assertEqual(report["draws"], 1)

    def test_import_again_takes_the_new_file_and_use_the_copied_unit_s_model_takes_it_out(self):
        """Import model again with another file: the mod's model is the new one, its record naming it; Use the copied
        unit's model: the model and its record go, and the mod builds with no model of its own."""
        self.imported("tank.glb", tank_glb())
        first = (self.models / f"{STEM}.glb").read_bytes()
        f = self.his_file("plates.glb", tank_glb(materials=[("Paint", picture(16, 16, seed=9))]))
        self.page.model_import(self.unit, str(f))
        self.assertNotEqual((self.models / f"{STEM}.glb").read_bytes(), first)
        self.assertEqual(self.record()["from"], str(f))
        self.page.model_import_remove(self.unit)
        self.assertEqual(self.model_files(), [])
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), result.own_models, stopped), ([], {}, []))


class BonesAndAnimations(ModelScenario):
    """A creature with bones of its own and an animation (Blender's armature, its Run action) on the new tank."""

    def test_it_comes_in_and_builds(self):
        """It is the unit's model and the mod builds (as a still model on the tank's hull)."""
        got = self.page.model_import(self.unit, str(self.his_file("creature.glb", little_glb(animations=RUN))))
        self.assertEqual(got["model"]["parts"], {"body": "hull"})
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), stopped, list(written)), ([], [], [STEM]))

    @unittest.expectedFailure
    def test_m2_what_it_left_out_is_said(self):
        """M-2: its three bones and its Run animation aren't in the mod (its model is a still model on the hull, its
        record names no bone and no animation), and neither the import's report (its notes are empty) nor the page
        says so: the page says "creature.glb is now this unit's model". What should happen: the import says the
        model's bones and its animation (by name) were left out, a tank's model being drawn on the tank's own bones."""
        got = self.page.model_import(self.unit, str(self.his_file("creature.glb", little_glb(animations=RUN))))
        said = " ".join(got["model"].get("notes") or []) + " " + str(got["model"].get("not_kept") or "")
        self.assertIn("Run", said)

    def test_names_in_other_scripts_on_its_bones_and_animation(self):
        """Its bones and its animation named in Russian, Chinese and Persian: it comes in as above, and builds."""
        anims = [("Бег", RUN[0][1])]
        got = self.page.model_import(self.unit, str(self.his_file("существо.glb", little_glb(
            names=("Таз", "背骨", "سر"), animations=anims))))
        self.assertEqual(got["model"]["file"], "существо.glb")
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), stopped), ([], []))


class Broken(ModelScenario):
    """The broken files a player ends up with: each refused, the mod as it was."""
    REFUSED = dict({k: v for k, v in broken_files(tank_glb()).items() if k != "version 1"},
                   **{"only lines": tank_glb(mode=1), "only points": tank_glb(mode=0)})

    def test_each_is_refused_and_the_mod_stays_as_it_was(self):
        before = self.files()
        for what, data in self.REFUSED.items():
            with self.subTest(what=what):
                f = self.his_file(f"{what.replace(' ', '_')}.glb", data)
                said = self.refusal("model_import", self.unit, str(f))
                self.assertIsNotNone(said)
                self.assertEqual(self.files(), before)
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), result.own_models), ([], {}))

    @unittest.expectedFailure
    def test_m1_each_refusal_is_said_in_every_language_in_plain_words(self):
        """M-1 (SQ-6's kind, on the unit's own Import model, with more of them): every refusal is English in every
        language and names the file twice ("empty.glb: empty.glb: not a .glb file"); a file cut short or with its text
        part broken gets Python's JSON reader's words ("Unterminated string starting at: line 1 column 1900 (char
        1899)", "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"); a model of lines or
        points only is said to have "no meshes in it". What should happen: each said once, in the page's language, in
        words a player knows (the file isn't a 3D model, it's cut short, it has nothing with faces to draw)."""
        for what, data in self.REFUSED.items():
            with self.subTest(what=what):
                f = self.his_file(f"{what.replace(' ', '_')}.glb", data)
                said = self.said("model_import", self.unit, str(f))
                self.assert_worded(said)
                self.assertEqual(said["us"].count(f.name), 1, said["us"])
                for words in ("line 1 column", "char ", "Expecting", "Unterminated", "meshes"):
                    self.assertNotIn(words, said["us"])

    def test_a_glb_marked_version_1_is_read_as_the_version_2_it_is(self):
        """Its header says version 1, its parts are glTF 2's: taken as it is (nothing lost), and builds."""
        data = broken_files(tank_glb())["version 1"]
        got = self.page.model_import(self.unit, str(self.his_file("v1.glb", data)))
        self.assertEqual(got["model"]["vertices"], 24)
        result, written, stopped = self.built()
        self.assertEqual((self.build_errors(result), stopped), ([], []))


class WhatTheImportReads(unittest.TestCase):
    """The import's reading on its own, for the record of what the scenarios above rest on."""

    def test_the_files_made_here_are_what_blender_writes(self):
        doc, _bin = modelin.glb_document(tank_glb())
        self.assertEqual(doc["asset"]["generator"], "Khronos glTF Blender I/O")
        self.assertEqual([n["name"] for n in doc["nodes"]], ["Hull", "Turret", "Gun"])
        self.assertEqual(len(doc["images"]), 1)


if __name__ == "__main__":
    unittest.main()
