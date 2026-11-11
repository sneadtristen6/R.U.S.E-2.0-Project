"""A unit's animations through Change it in Blender and Bring back the model (ruse_studio.animblender,
ruse_studio.modelblender; item 5 of the owner's list, part 4: "fully editable in the studio"), on the made-up model,
skeleton and clips of test_gltf_bones and test_animglb, Blender's part played by test_animglb's stand-in: the names
the animations get, the clips a unit plays as the mod makes them, what goes out and is kept, and what comes back (a
changed animation the unit's own clip for the actions that played it, the rest left alone)."""
import json
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, modelin
from ruse_studio import animblender
from test_animglb import CLIPS, Blenderish, make_clip
from test_gltf_bones import NAME, RECORD, FakeLibrary

B = "\\"
SQUAD = "$/GFX/Everything/Descriptor_Unit_My_Riflemen"
UNIT = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"
COMMON = B.join(["genanim_15", "ww2", "res3d", "units", "common"]) + B
RUN, STAND, OTHER = COMMON + "made_runlod0.baf", COMMON + "made_standlod0.baf", COMMON + "other_standlod0.baf"
CLIP_BYTES = {RUN: baf.build(CLIPS[0][1]), STAND: baf.build(CLIPS[1][1])}
OTHER_RECORD = baf.skeleton_bytes(["root"], [-1], [(1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0)] * 1,
                                  [(1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0)], [(1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0)])
CLIP_BYTES[OTHER] = baf.build(baf.Clip(1.0, 31, [baf.Track([(0, 0.0, 0.0, 0.0)], [(0, 1.0, 1.0, 1.0)],
                                                           [(0,) + baf.pack_quat(0.0, 0.0, 0.0, 1.0)])], OTHER_RECORD))
OTHER_MODEL = "ww2\\test\\horselod0.ase2ndfbin"
FIGURES = [{"figure": UNIT + ":GfxDescriptorBazooka", "model": NAME, "clips": [("t_stand", STAND), ("t_tir", RUN)]},
           {"figure": UNIT + ":GfxDescriptorFusilier", "model": NAME,
            "clips": [("t_stand", STAND), ("b_stand", STAND), ("b_course", RUN)]},
           {"figure": UNIT + ":GfxDescriptorHorse", "model": OTHER_MODEL, "clips": [("idle1", OTHER)]},
           {"figure": UNIT + ":GfxDescriptorIcone", "model": None, "clips": []}]
US = {"anim_word_run": "run", "anim_word_stand": "stand", "anim_word_aiming": "aiming", "anim_word_right": "right",
      "anim_word_death": "death", "anim_word_bullet": "bullet", "anim_word_back": "from behind",
      "anim_word_top": "top half", "anim_word_fire": "fire", "anim_word_lookaround": "look around"}


def read(member):
    return CLIP_BYTES.get(member.lower())


def skeleton_of(model):
    return RECORD if model == NAME else OTHER_RECORD if model == OTHER_MODEL else None


class Names(unittest.TestCase):
    def test_what_the_unit_does_then_the_clip(self):
        self.assertEqual(animblender.label("fusilier_course_droite_vise", US),
                         "Run, right, aiming (fusilier_course_droite_vise)")
        self.assertEqual(animblender.label("fusilier_mort_balle_dos", US),
                         "Death, bullet, from behind (fusilier_mort_balle_dos)")
        self.assertEqual(animblender.label("hr_t_tir", US), "Top half, fire (hr_t_tir)")
        self.assertEqual(animblender.label("fusilier_course2", US), "Run 2 (fusilier_course2)")
        self.assertEqual(animblender.label("fusilier_look_around", US), "Look around (fusilier_look_around)")
        self.assertEqual(animblender.label("xyz_abc", US), "xyz_abc")
        self.assertEqual(animblender.stem_of(RUN), "made_run")

    def test_never_past_what_blender_keeps_of_a_name(self):
        """An action's name holds 63 bytes in Blender: a longer one is cut, and its animation wouldn't be found when it
        comes back. Words that don't fit go first (Japanese takes three bytes a letter)."""
        long = {k: v * 6 for k, v in US.items()}
        for words in (US, long, {k: "走る" * 9 for k in US}):
            for stem in ("fusilier_bazooka_course_arriere_vise", "fusilier_mort_explosion_dos", "a" * 70):
                self.assertLessEqual(len(animblender.label(stem, words).encode("utf-8")), animblender.NAME_BYTES)
        self.assertTrue(animblender.label("fusilier_course_vise", long).endswith("(fusilier_course_vise)"))


class Plays(unittest.TestCase):
    """unit_plays: the clips a unit plays on a model of these bones, as the mod makes them."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.mod = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def plays(self, mod=None):
        names = baf.skeleton(RECORD)["names"]
        return animblender.unit_plays(FIGURES, names, read, mod, "Descriptor_Unit_My_Riflemen", skeleton_of, US)

    def test_the_game_s_clips_once_each_with_every_action_that_plays_them(self):
        rows = self.plays()
        self.assertEqual([r["name"] for r in rows], ["Stand (made_stand)", "Run (made_run)"])
        self.assertEqual(rows[0]["actions"], {"GfxDescriptorBazooka": ["t_stand"],
                                              "GfxDescriptorFusilier": ["t_stand", "b_stand"]})
        self.assertEqual(rows[1]["actions"], {"GfxDescriptorBazooka": ["t_tir"], "GfxDescriptorFusilier": ["b_course"]})
        self.assertEqual([r["clip"] for r in rows], [CLIP_BYTES[STAND], CLIP_BYTES[RUN]])
        self.assertEqual((rows[0]["member"], rows[0]["own"]), (STAND, None))
        # (the horse's clip is of other bones, the far figure plays none: neither goes out)

    def test_as_the_mod_makes_them(self):
        """Every unit's change (clips.toml: the run at half speed) and the unit's own clip for one action of one
        figure (units.toml, RUSE Decoy's Only this unit) go out as they play."""
        (self.mod / "files" / "anim").mkdir(parents=True)
        (self.mod / "files" / "anim" / "clips.toml").write_text(
            '[clip."genanim_15/ww2/res3d/units/common/made_runlod0.baf"]\nspeed = 50\n', encoding="utf-8")
        own = baf.build(make_clip(12.0))
        anim.add_unit_clip(self.mod, "Descriptor_Unit_My_Riflemen", "t_tir", own, name="my_fire",
                           figure="GfxDescriptorBazooka")
        rows = {r["name"]: r for r in self.plays(self.mod)}
        self.assertEqual(sorted(rows), ["Fire (my_fire)", "Run (made_run)", "Stand (made_stand)"])
        self.assertEqual(baf.parse(rows["Run (made_run)"]["clip"]).duration, baf.parse(CLIP_BYTES[RUN]).duration * 2)
        self.assertEqual(rows["Run (made_run)"]["actions"], {"GfxDescriptorFusilier": ["b_course"]})
        mine = rows["Fire (my_fire)"]
        self.assertEqual((mine["clip"], mine["own"], mine["member"]), (own, "my_fire.baf", None))
        self.assertEqual(mine["actions"], {"GfxDescriptorBazooka": ["t_tir"]})

    def test_what_went_out_is_kept(self):
        rows = self.plays()
        animblender.write_sent(self.mod, NAME, RECORD, rows)
        sent = animblender.read_sent(self.mod)
        self.assertEqual((sent["model"], sent["record"]), (NAME, RECORD))
        self.assertEqual([(a["name"], a["clip"], a["actions"]) for a in sent["animations"]],
                         [(r["name"], r["clip"], r["actions"]) for r in rows])
        animblender.forget_sent(self.mod)
        self.assertIsNone(animblender.read_sent(self.mod))


class FakeArc:
    entries = []

    @staticmethod
    def entry(member):
        return member if member.lower() in CLIP_BYTES else None

    @staticmethod
    def read(entry):
        return CLIP_BYTES[entry.lower()]


class Studio(unittest.TestCase):
    """Change it in Blender with the unit's animations, Blender's stand-in sending, and what comes back."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda: self.mod
        self.api._look_models = lambda address: ([NAME], [])
        self.api._own_model_file = lambda address: self.mod / "files" / "models" / "Descriptor_Unit_My_Riflemen.glb"
        self.api._blender = lambda: Path("C:/b/blender.exe")
        self.api.look = lambda address: {"models": [], "new_unit": True, "soldiers": True}
        self.api._unit_figures = lambda address: FIGURES
        self.work = self.mod / "blender" / "Descriptor_Unit_My_Riflemen"
        self.send = self.work / "Descriptor_Unit_My_Riflemen.glb"
        lib = FakeLibrary()
        lib.arc = FakeArc()
        lib.close = lambda: None
        self.lib = lib

    def tearDown(self):
        self.dir.cleanup()

    def open(self):
        started = []
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append(model) or "proc"):
            res = self.api.model_blender(SQUAD, "us")
        return res, started[0]

    def test_opened_with_every_animation_it_plays(self):
        res, start = self.open()
        self.assertEqual(res["animations"], 2)
        doc, _bin = modelin.glb_document(Path(start).read_bytes())
        self.assertEqual([a["name"] for a in doc["animations"]], ["Stand (made_stand)", "Run (made_run)"])
        self.assertEqual(doc["animations"][0]["extras"]["rusemod_actions"], ["b_stand", "t_stand"])
        self.assertEqual(len(doc["skins"][0]["joints"]), baf.skeleton(RECORD)["bones"])
        sent = animblender.read_sent(self.work)
        self.assertEqual((sent["model"], sent["record"], len(sent["animations"])), (NAME, RECORD, 2))
        words = json.loads((self.work / "words.json").read_text(encoding="utf-8"))
        self.assertEqual(len(words["hint_animations"]), 2)

    def test_a_changed_animation_comes_back_this_squad_s_own(self):
        """Blender's stand-in sends the file back with the spine turned in the run: the run comes back as the squad's
        own clip for each action of each figure that played it (its other tracks the game's own, byte for byte); the
        stand comes back as it went out and is left alone; Import model reads the file in the game's frames."""
        _res, start = self.open()
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("Run (made_run)", "bip01 spine", baf.axis_angle("x", 20.0))))
        source = self.api._game_frames_file(SQUAD, self.send)
        self.assertEqual(source, self.work / "Descriptor_Unit_My_Riflemen.game.glb")
        doc, _bin = modelin.glb_document(source.read_bytes())
        self.assertEqual([doc["nodes"][j]["name"] for j in doc["skins"][0]["joints"]], baf.skeleton(RECORD)["names"])
        got = self.api._animations_back(SQUAD, {"rigged": True})
        self.assertEqual((got["changed"], got["same"], got["new"], got["gone"], got["written"], got["own_bones"]),
                         (["Run (made_run)"], 1, [], [], 1, False))
        units = tomllib.loads((self.mod / anim.UNITS).read_text(encoding="utf-8"))["unit"]["Descriptor_Unit_My_Riflemen"]
        self.assertEqual(units["figure"], {"GfxDescriptorBazooka": {"action": {"t_tir": "blender_made_run.baf"}},
                                           "GfxDescriptorFusilier": {"action": {"b_course": "blender_made_run.baf"}}})
        mine = baf.parse((self.mod / anim.OWN / "Descriptor_Unit_My_Riflemen" / "blender_made_run.baf").read_bytes())
        theirs = CLIPS[0][1]
        spine = baf.skeleton(RECORD)["names"].index("bip01 spine")
        for u, b in enumerate(baf.skeleton(RECORD)["index"]):
            if b != spine:
                self.assertEqual(mine.tracks[u], theirs.tracks[u])
        self.assertNotEqual(mine.tracks[baf.skeleton(RECORD)["index"].index(spine)], theirs.tracks[spine])

    def test_made_in_blender_or_not_sent_back(self):
        _res, start = self.open()
        sent = Blenderish(Path(start).read_bytes()).send()
        doc, binary = modelin.glb_document(sent)
        doc["animations"][0]["name"] = "Wave"       # the stand renamed: one made in Blender, and the stand gone
        from test_animglb import gltf_bytes
        self.send.write_bytes(gltf_bytes(doc, binary))
        self.api._game_frames_file(SQUAD, self.send)
        got = self.api._animations_back(SQUAD, {"rigged": True})
        self.assertEqual((got["changed"], got["same"], got["new"], got["gone"], got["written"]),
                         ([], 1, ["Wave"], ["Stand (made_stand)"], 0))
        self.assertFalse((self.mod / anim.UNITS).exists())      # nothing written: no action plays Wave yet

    def test_a_model_on_bones_of_its_own_takes_them_in_with_it(self):
        _res, start = self.open()
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("Run (made_run)", "bip01 spine", baf.axis_angle("x", 20.0))))
        self.api._game_frames_file(SQUAD, self.send)
        got = self.api._animations_back(SQUAD, {"rigged": True, modelin.OWN_SKELETON: {"bones": 10}})
        self.assertEqual((got["changed"], got["same"], got["written"], got["own_bones"]), (["Run (made_run)"], 1, 0, True))
        self.assertFalse((self.mod / anim.UNITS).exists())

    def test_a_file_not_laid_out_for_blender_is_read_as_it_is(self):
        self.work.mkdir(parents=True)
        plain = self.work / "plain.glb"
        from test_animglb import own_model_file
        plain.write_bytes(own_model_file())
        self.assertEqual(self.api._game_frames_file(SQUAD, plain), plain)
        self.assertIsNone(self.api._animations_back(SQUAD, {"rigged": True}))
        other = self.work / "model.3ds"
        other.write_bytes(b"3ds")
        self.assertEqual(self.api._game_frames_file(SQUAD, other), other)

    def test_a_model_on_bones_of_its_own_opens_with_its_own_animations(self):
        """The unit's own model on bones of its own (its file carries its record): it goes out with its own clips under
        their own names (the modder's, which its record knows), and comes back in the game's frames, record and all."""
        from test_animglb import own_model_file
        own = self.mod / "files" / "models" / "Descriptor_Unit_My_Riflemen.glb"
        own.parent.mkdir(parents=True)
        own.write_bytes(own_model_file())
        res, start = self.open()
        self.assertEqual(Path(start).name, "Descriptor_Unit_My_Riflemen_model.glb")
        self.assertEqual(res["animations"], 2)
        sent = animblender.read_sent(self.work)
        self.assertEqual((sent["model"], sent["record"]), ("own", RECORD))
        self.assertEqual([a["name"] for a in sent["animations"]], ["made_stand", "made_run"])
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("made_run", "bip01 spine", baf.axis_angle("x", 20.0))))
        source = self.api._game_frames_file(SQUAD, self.send)
        self.assertEqual(self.api._turned_back["info"]["kept"], True)
        back = modelin.glb_document(source.read_bytes())[0]
        import base64
        from rusemod.rig import SKELETON_EXTRA
        self.assertEqual(base64.b64decode(back["skins"][0]["extras"][SKELETON_EXTRA]), RECORD)
        got = self.api._animations_back(SQUAD, {"rigged": True, modelin.OWN_SKELETON: {"bones": 10}})
        self.assertEqual((got["changed"], got["same"], got["own_bones"]), (["made_run"], 1, True))

    def test_a_model_on_bones_of_its_own_before_any_action_plays_its_clips(self):
        from test_animglb import own_model_file
        own = self.mod / "files" / "models" / "Descriptor_Unit_My_Riflemen.glb"
        own.parent.mkdir(parents=True)
        own.write_bytes(own_model_file())
        self.api._unit_figures = lambda address: []
        res, start = self.open()
        self.assertEqual(res["animations"], 0)            # (its file carries none: it goes out on its bones alone)
        self.assertEqual(animblender.read_sent(self.work)["animations"], [])

    def test_work_goes_on_from_what_was_sent_last(self):
        _res, start = self.open()
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send())
        with mock.patch("rusemod.models.Library", side_effect=AssertionError("the game's model isn't written again")), \
                mock.patch("rusemod.blender.open_model_to_change", lambda b, model, send, words: "proc"):
            res = self.api.model_blender(SQUAD, "us")
        self.assertEqual((res["file"], res["animations"]), (str(self.send), 2))
        self.assertIsNotNone(animblender.read_sent(self.work))     # (what went out the first time stays the reference)


if __name__ == "__main__":
    unittest.main()
