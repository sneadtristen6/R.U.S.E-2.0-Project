"""Scenarios on the game itself (its index and packs read only; skipped without them, as tests/test_review_loss.py's
OnTheGame): a copy of the US rifle squad given a model with bones of its own and its animations (the Generic Horse's
riflemen file of the copy that passed in the game, RUSE_HORSE_SQUAD_GLBS) with Import model…, then Will it work in the
game?, Its two halves (a bone chosen, one it hasn't, back to the suggested one), Its animations, the action table (an
animation picked for an action, one it hasn't, back to Nearest); and a creature whose bones are named in other scripts.
Blender is never started. A finding is kept as an expected failure naming it (M-n: the scenarios' NOTES.md and report).

FOR: the models and Blender scenarios (release 0.9.8.20, overnight 2026-11-14).
USED-BY: the scenarios' runs (gentle.py, -m unittest)."""
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy  # noqa: F401  (loaded once, first: numpy can't load twice in a process)
from test_horse_squad import GAME, INDEX, RIFLE
from test_ownrig import little_glb, turn_about
from test_scenarios_models_base import LANGS, PYTHON_WORDS

SQUAD = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"
ON_THE_GAME = GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file()
WHY = "RUSE_GAME names no game folder, or the Studio's game index or the Generic Horse's riflemen file isn't there"


@unittest.skipUnless(ON_THE_GAME, WHY)
class OnTheGame(unittest.TestCase):
    def setUp(self):
        from ruse_studio.api import StudioApi
        from rusemod.webui import page_api
        self.home = Path(tempfile.mkdtemp(prefix="scen-models-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = StudioApi(index_path=INDEX, game_dir=GAME, home=self.home, instances=self.home / "copies")
        self.page = page_api(self.api)
        self.addCleanup(self.api.set_pref, "lang", "us")
        self.page.new_mod("Own bones")
        self.unit = self.page.new_unit(SQUAD, "My Riders", 5, group="new")["address"]

    def said(self, name: str, *args) -> dict:
        from ruse_studio.api import StudioError
        out = {}
        for lang in LANGS:
            self.api.set_pref("lang", lang)
            try:
                getattr(self.page, name)(*args)
                out[lang] = None
            except StudioError as exc:
                out[lang] = str(exc)
        self.api.set_pref("lang", "us")
        return out

    def assert_worded(self, said: dict, english: str) -> None:
        self.assertEqual(said["us"], english)
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertTrue(said[lang], lang)
                if lang != "us":
                    self.assertNotEqual(said[lang], said["us"], f"{lang}: English left in")
                for bad in PYTHON_WORDS:
                    self.assertNotIn(bad, said[lang], lang)


class OwnBonesOnASquad(OnTheGame):
    def test_its_boxes_and_their_refusals(self):
        got = self.page.model_import(self.unit, str(RIFLE))["model"]
        self.assertEqual((got["rigged"], got["own_skeleton"]["bones"], len(got["own_skeleton"]["animations"])),
                         (True, 62, 25))
        fit = self.page.model_fit(self.unit)                           # Will it work in the game?
        self.assertEqual((fit["skeleton"], fit["bones"], fit["halves"]["split"]), ("own", 62, "bip01"))
        chosen = self.page.model_split(self.unit, "bip01 pelvis")["halves"]          # Its two halves
        self.assertEqual((chosen["split"], chosen["chosen"]), ("bip01 pelvis", True))
        self.assert_worded(self.said("model_split", self.unit, "no such bone"), "The model has no bone called no such bone.")
        back = self.page.model_split(self.unit, "")["halves"]
        self.assertEqual((back["split"], back["chosen"]), ("bip01", False))
        anims = self.page.model_animations(self.unit)                  # Its animations
        self.assertEqual((anims["own"], anims["bones"], len(anims["animations"])), (True, 62, 25))
        table = self.page.unit_actions(self.unit)                      # which one each action plays: Nearest
        stand = next(r for r in table["rows"] if r["action"] == "stand")
        self.assertEqual((stand["how"], stand["plays"]), ("named", {"top": "hr_t_stand", "bottom": "hr_b_stand"}))
        picked = next(r for r in self.page.unit_action_set(self.unit, "stand", "hr_b_walk")["rows"]
                      if r["action"] == "stand")
        self.assertEqual((picked["picked"], picked["how"]), ("hr_b_walk", "picked"))
        self.assert_worded(self.said("unit_action_set", self.unit, "stand", "no such animation"),
                           "no such animation isn't one of its model's animations.")
        nearest = next(r for r in self.page.unit_action_set(self.unit, "stand", None)["rows"] if r["action"] == "stand")
        self.assertEqual((nearest["picked"], nearest["plays"]), (None, stand["plays"]))
        self.assertEqual(self.page.check_mod()["problems"], [])

    def figures_built(self) -> dict:
        """{figure: (the model it draws, how many of its listings play one of the unit's own clips, how many the
        game's)} of the unit in the mod built on the game's unit data (build_pack: nothing written)."""
        from rusemod import build
        from rusemod.edat import Edat
        from rusemod.patch import Inline
        with Edat.open(build.find_pack(GAME, build.DEFAULT_PACK)) as arc, \
                Edat.open(build.find_pack(GAME, "ZZ_Win.dat")) as zz:
            result = build.build_pack(arc, [build.load_mod(Path(self.api._mod_dir()))], "0", zz)
            self.assertEqual([f.message for f in result.errors], [])
            objects = build.load_pack(Edat(arc.to_bytes(result.changed))).base.objects
        me = objects[self.unit]

        def part(v):
            return v.obj if isinstance(v, Inline) else objects[v.target]
        out = {}
        for name in ("GfxDescriptorFusilier", "GfxDescriptorIconeCadavre"):
            fig = part(me.props[name])
            files = [part(v).props["FileName"].value.lower() for _k, v in fig.props["ResourceAnimation"].pairs]
            own = sum("own_my_riders_" in f for f in files)
            out[name] = (part(fig.props["MeshDescriptor"]).props["FileName"].value.lower().rsplit("\\", 1)[-1], own,
                         len(files) - own)
        return out

    def test_the_build_plays_the_model_s_own_animations(self):
        """The built copy: its riflemen and its fallen soldier draw its own model and every listing of theirs plays one
        of its own clips (70 and 2), as Its animations says."""
        self.page.model_import(self.unit, str(RIFLE))
        self.assertEqual(self.figures_built(), {
            "GfxDescriptorFusilier": ("descriptor_unit_my_riderslod0.ase2ndfbin", 70, 0),
            "GfxDescriptorIconeCadavre": ("descriptor_unit_my_riderslod0.ase2ndfbin", 2, 0)})

    def test_m8_will_it_work_in_the_game_says_what_the_build_plays(self):
        """M-8 (PROPOSED FIX in this branch): on 0d5564eb Will it work in the game? said its riflemen (every one of
        their 70 actions) and its fallen soldier play the game's clips of 41 bones on the model's 62, "This can stop
        the game: it did in a test", while the build plays the model's own animations for every one of them (the test
        above): the check read only RUSE Decoy's Only this unit rows (files/anim/units.toml's clips and actions), not
        the model's own animations and the action table that plays them. Now no such problem."""
        self.page.model_import(self.unit, str(RIFLE))
        self.assertEqual([(p["figure_kind"], p["level"]) for p in self.page.model_fit(self.unit)["problems"]], [])


class CreatureNamesOnASquad(OnTheGame):
    CREATURE = little_glb(names=("Таз", "背骨", "سر"), animations=[(
        "Бег", [(2, "rotation", (0.0, 0.5, 1.0), [(0, 0, 0, 1), turn_about("x", 30.0), (0, 0, 0, 1)], "LINEAR")])])

    def his_file(self) -> Path:
        f = self.home / "his models" / "существо.glb"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(self.CREATURE)
        return f

    def test_refused_and_nothing_written(self):
        """Its bones named in Russian, Chinese and Persian on a squad (bones of its own): refused, nothing of it in the
        mod; renamed with plain letters, it comes in."""
        from ruse_studio.api import StudioError
        with self.assertRaises(StudioError):
            self.page.model_import(self.unit, str(self.his_file()))
        self.assertFalse((Path(self.api._mod_dir()) / "files" / "models").exists())
        plain = self.home / "his models" / "creature.glb"
        plain.write_bytes(little_glb(animations=[("Run", [(2, "rotation", (0.0, 0.5, 1.0),
                                                           [(0, 0, 0, 1), turn_about("x", 30.0), (0, 0, 0, 1)],
                                                           "LINEAR")])]))
        self.assertTrue(self.page.model_import(self.unit, str(plain))["model"]["rigged"])

    @unittest.expectedFailure
    def test_m1_its_refusal_in_every_language(self):
        """M-1's kind: "существо.glb: существо.glb: the bone name 'Таз' has letters a skeleton can't hold: rename it
        with plain letters in Blender": the file named twice, Python's quotes, English in every language."""
        said = self.said("model_import", self.unit, str(self.his_file()))
        self.assert_worded(said, "существо.glb: the bone name Таз has letters a skeleton can't hold: rename it with "
                                 "plain letters in Blender")


if __name__ == "__main__":
    unittest.main()
