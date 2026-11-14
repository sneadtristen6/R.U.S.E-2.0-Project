"""A unit's animations through RUSE Decoy's Change its animations in Blender and Bring my changes back
(ruse_studio.animblender, ruse_studio.decoyblender; item 5 of the owner's list, part 4: "fully editable in the studio";
his 11-10 answer: "The only way you should change animation is in Ruse Decoy"), on the made-up model,
skeleton and clips of test_gltf_bones and test_animglb, Blender's part played by test_animglb's stand-in: the names
the animations get, the clips a unit plays as the mod makes them, what goes out and is kept, and what comes back (a
changed animation the unit's own clip for the actions that played it, the rest left alone)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
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


class Closed:
    """A stand-in for the Blender process the Studio started, closed again."""

    def poll(self):
        return 0


class Running:
    """... and one still open."""

    def poll(self):
        return None


class Studio(unittest.TestCase):
    """RUSE Decoy's Change its animations in Blender for one unit (ruse_studio.decoyblender; the owner, 2026-11-10:
    "The only way you should change animation is in Ruse Decoy"), Blender's stand-in sending, and what comes back."""

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
        self.api._mod_dir = lambda kind="mod": self.mod
        self.api._look_models = lambda address: ([NAME], [])
        self.api._own_model_file = lambda address: self.mod / "files" / "models" / "Descriptor_Unit_My_Riflemen.glb"
        self.api._blender = lambda: Path("C:/b/blender.exe")
        self.api._unit_figures = lambda address: FIGURES
        self.work = self.mod / "blender" / "Descriptor_Unit_My_Riflemen" / "animations"
        self.send = self.work / "send.glb"
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
                           lambda b, model, send, words: started.append((model, send)) or Closed()):
            res = self.api.decoy_blender(SQUAD, "us")
        self.assertEqual(started[0][1], self.send)          # (Blender sends where the Studio looks)
        return res, started[0][0]

    def test_opened_with_every_animation_it_plays(self):
        res, start = self.open()
        self.assertEqual((res["opened"], res["can"], res["set_aside"]), (2, True, None))
        self.assertIn("2 animations", res["message"])
        doc, _bin = modelin.glb_document(Path(start).read_bytes())
        self.assertEqual([a["name"] for a in doc["animations"]], ["Stand (made_stand)", "Run (made_run)"])
        self.assertEqual(doc["animations"][0]["extras"]["rusemod_actions"], ["b_stand", "t_stand"])
        self.assertEqual(len(doc["skins"][0]["joints"]), baf.skeleton(RECORD)["bones"])
        sent = animblender.read_sent(self.work)
        self.assertEqual((sent["model"], sent["record"], len(sent["animations"])), (NAME, RECORD, 2))
        words = json.loads((self.work / "words.json").read_text(encoding="utf-8"))
        self.assertEqual((len(words["hint"]), words["sent"]),
                         (2, "Sent. Now click Bring my changes back in RUSE Decoy."))
        # the model's own Blender work folder is left alone: the animations have a folder of their own
        self.assertFalse((self.work.parent / "Descriptor_Unit_My_Riflemen.glb").exists())

    def test_a_changed_animation_comes_back_this_unit_s_own(self):
        """Blender's stand-in sends the file back with the spine turned in the run: the run comes back as the unit's
        own clip for each action of each figure that played it (its other tracks the game's own, byte for byte); the
        stand comes back as it went out and is left alone."""
        _res, start = self.open()
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("Run (made_run)", "bip01 spine", baf.axis_angle("x", 20.0))))
        self.assertTrue(self.api.decoy_blender_state(SQUAD)["waiting"])
        got = self.api.decoy_blender_back(SQUAD, "us")
        self.assertEqual((got["changed"], got["same"], got["new"], got["gone"], got["written"]),
                         (["Run (made_run)"], 1, [], [], 1))
        self.assertEqual(got["message"], "Changed in Blender, this unit's own now: Run (made_run). Every other unit keeps "
                                         "the game's.")
        self.assertFalse(got["waiting"])                     # (brought back: the button goes)
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
        # opened again: the run goes out as the unit's own now
        _res, start = self.open()
        doc, _bin = modelin.glb_document(Path(start).read_bytes())
        self.assertEqual([a["name"] for a in doc["animations"]], ["Stand (made_stand)", "Run (blender_made_run)"])

    def test_made_in_blender_or_not_sent_back(self):
        _res, start = self.open()
        sent = Blenderish(Path(start).read_bytes()).send()
        doc, binary = modelin.glb_document(sent)
        doc["animations"][0]["name"] = "Wave"       # the stand renamed: one made in Blender, and the stand gone
        from test_animglb import gltf_bytes
        self.send.write_bytes(gltf_bytes(doc, binary))
        got = self.api.decoy_blender_back(SQUAD, "us")
        self.assertEqual((got["changed"], got["same"], got["new"], got["gone"], got["written"]),
                         ([], 1, ["Wave"], ["Stand (made_stand)"], 0))
        self.assertIn("Made in Blender, played by no action yet: Wave.", got["message"])
        self.assertIn("so they play as before: Stand (made_stand).", got["message"])
        self.assertFalse((self.mod / anim.UNITS).exists())      # nothing written: no action plays Wave yet

    def test_a_model_on_bones_of_its_own_goes_out_with_its_own_animations(self):
        """The unit's own model on bones of its own (its file carries its record): it goes out with its clips under
        their own names (the modder's, which its record knows), and a changed one comes back as the unit's own."""
        from test_animglb import own_model_file
        own = self.mod / "files" / "models" / "Descriptor_Unit_My_Riflemen.glb"
        own.parent.mkdir(parents=True)
        own.write_bytes(own_model_file())
        res, start = self.open()
        self.assertEqual((Path(start).name, res["opened"]), ("animations.glb", 2))
        sent = animblender.read_sent(self.work)
        self.assertEqual((sent["model"], sent["record"]), ("own", RECORD))
        self.assertEqual([a["name"] for a in sent["animations"]], ["made_stand", "made_run"])
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("made_run", "bip01 spine", baf.axis_angle("x", 20.0))))
        got = self.api.decoy_blender_back(SQUAD, "us")
        self.assertEqual((got["changed"], got["same"], got["written"]), (["made_run"], 1, 1))
        self.assertTrue((self.mod / anim.OWN / "Descriptor_Unit_My_Riflemen" / "blender_made_run.baf").is_file())

    def own_bones_unit(self, model: bytes | None = None, animations: bool = True):
        """The unit's own model on bones of its own that no game figure is on (the Horse Squad's kind: no game clip
        fits it), its animations stand and run in the mod as Import model keeps them, its record listing them, and
        the action "stand" picked to play the run. Returns (its name in units.toml, the animations' files)."""
        from test_animglb import own_model_file
        unit = "Descriptor_Unit_My_Riflemen"
        own = self.mod / "files" / "models" / f"{unit}.glb"
        own.parent.mkdir(parents=True, exist_ok=True)
        own.write_bytes(model or own_model_file())
        self.api._unit_figures = lambda address: []
        files = {}
        if animations:
            files = anim.set_animations(self.mod, unit, {"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[RUN]})
            anim.set_pick(self.mod, unit, "stand", "run")
        own.with_suffix(".json").write_text(json.dumps({"skeleton": "own", "animations": [
            {"name": n, "frames": baf.parse(CLIP_BYTES[m]).frames, "seconds": 1.0, "file": f}
            for (n, f), m in zip(files.items(), (STAND, RUN))]}, indent=1), encoding="utf-8")
        return unit, files

    def test_a_model_on_bones_of_its_own_gets_a_changed_animation_back_in_its_place(self):
        """Its model's own animations go out under their own names (no game clip is on its bones); the run changed
        comes back in the run's place by name: its file changed in the spine alone, the stand byte for byte as it
        was, the pick that plays it kept, no action row of its own written, the record's list the same names. Found
        2026-11-12 checking the join: sent with no action, such a change was said to be the unit's own and written
        nowhere."""
        unit, files = self.own_bones_unit()
        res, start = self.open()
        self.assertEqual((Path(start).name, res["opened"]), ("animations.glb", 2))
        sent = animblender.read_sent(self.work)
        self.assertEqual([(a["name"], a.get("model_animation"), a["actions"]) for a in sent["animations"]],
                         [("stand", "stand", {}), ("run", "run", {})])
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("run", "bip01 spine", baf.axis_angle("x", 20.0))))
        got = self.api.decoy_blender_back(SQUAD, "us")
        self.assertEqual((got["changed"], got["same"], got["new"], got["gone"], got["written"]),
                         (["run"], 1, [], [], 1))
        u = tomllib.loads((self.mod / anim.UNITS).read_text(encoding="utf-8"))["unit"][unit]
        self.assertEqual((u["animation"], u["plays"]), (files, {"stand": "run"}))
        self.assertNotIn("figure", u)
        own = self.mod / anim.OWN / unit
        self.assertEqual((own / files["stand"]).read_bytes(), CLIP_BYTES[STAND])
        mine, theirs = baf.parse((own / files["run"]).read_bytes()), baf.parse(CLIP_BYTES[RUN])
        sk = baf.skeleton(RECORD)
        spine = sk["names"].index("bip01 spine")
        for t, b in enumerate(sk["index"]):
            (self.assertNotEqual if b == spine else self.assertEqual)(mine.tracks[t], theirs.tracks[t])
        record = json.loads((self.mod / "files" / "models" / f"{unit}.json").read_text(encoding="utf-8"))
        self.assertEqual([(a["name"], a["file"], a["frames"]) for a in record["animations"]],
                         [("stand", files["stand"], baf.parse(CLIP_BYTES[STAND]).frames),
                          ("run", files["run"], mine.frames)])
        # opened again: the run goes out as it is now
        _res, start = self.open()
        self.assertEqual(animblender.read_sent(self.work)["animations"][1]["clip"], (own / files["run"]).read_bytes())

    def test_its_model_s_animations_changed_meanwhile_take_nothing_in(self):
        """The model's run imported again while Blender was open: what comes back was made from the old run, so
        nothing is taken in and that is said, the mod as the new import left it."""
        from ruse_studio.api import StudioError
        unit, files = self.own_bones_unit()
        _res, start = self.open()
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("run", "bip01 spine", baf.axis_angle("x", 20.0))))
        anim.set_animations(self.mod, unit, {"stand": CLIP_BYTES[STAND], "run": CLIP_BYTES[STAND]})
        before = (self.mod / anim.UNITS).read_bytes(), (self.mod / anim.OWN / unit / files["run"]).read_bytes()
        with self.assertRaisesRegex(StudioError, "^This unit's model or its animations changed after they went out"):
            self.api.decoy_blender_back(SQUAD, "us")
        self.assertEqual(before, ((self.mod / anim.UNITS).read_bytes(),
                                  (self.mod / anim.OWN / unit / files["run"]).read_bytes()))

    def test_animations_its_file_carries_go_out_before_the_mod_has_any(self):
        """A model on bones of its own whose mod has none of its animations yet: the ones its file carries go out,
        and a changed one comes back with the rest as the unit's model animations, as Import model takes them in."""
        unit, _files = self.own_bones_unit()
        _res, start = self.open()
        carrying = Path(start).read_bytes()        # (a model on bones of its own carrying stand and run)
        self.tearDown()
        self.setUp()
        unit, files = self.own_bones_unit(model=carrying, animations=False)
        self.assertEqual(files, {})
        res, start = self.open()
        sent = animblender.read_sent(self.work)
        self.assertEqual([(a["name"], a.get("model_animation"), a["own"]) for a in sent["animations"]],
                         [("stand", "stand", None), ("run", "run", None)])
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("run", "bip01 spine", baf.axis_angle("x", 20.0))))
        got = self.api.decoy_blender_back(SQUAD, "us")
        self.assertEqual((got["changed"], got["written"]), (["run"], 1))
        now = anim.own_animations(self.mod, unit)["animations"]
        self.assertEqual(list(now), ["stand", "run"])
        own = self.mod / anim.OWN / unit
        self.assertEqual((own / now["stand"]).read_bytes(), sent["animations"][0]["clip"])
        self.assertNotEqual((own / now["run"]).read_bytes(), sent["animations"][1]["clip"])

    def test_the_refusals_in_words(self):
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "^Nothing has come back from Blender yet"):
            self.api.decoy_blender_back(SQUAD, "us")
        self.api._blenders[str(self.work)] = Running()
        with self.assertRaisesRegex(StudioError, "open in Blender already"):
            self.open()
        self.api._blenders.clear()
        self.api._unit_figures = lambda address: []      # (a unit playing no animation on its model's bones)
        with self.assertRaisesRegex(StudioError, "^This unit plays no animation the Studio can open in Blender.$"):
            self.open()
        self.api._blender = lambda: None
        with self.assertRaisesRegex(StudioError, "^Blender isn't found on this PC"):
            self.open()

    def test_a_game_unit_is_told_why_not(self):
        from ruse_studio.api import StudioError
        self.api._own_model_file = lambda address: None
        st = self.api.decoy_blender_state(UNIT)
        why = "Only a new unit made in this mod gets animations of its own: make a new unit from this one first."
        self.assertEqual((st["can"], st["why_not"], st["work"]), (False, why, None))
        with self.assertRaisesRegex(StudioError, f"^{why}$"):
            self.api.decoy_blender(UNIT, "us")

    def test_a_sending_never_brought_back_is_kept_aside(self):
        _res, start = self.open()
        sending = Blenderish(Path(start).read_bytes()).send(
            change=("Run (made_run)", "bip01 spine", baf.axis_angle("x", 20.0)))
        self.send.write_bytes(sending)
        res, _start = self.open()
        aside = Path(res["set_aside"])
        self.assertEqual(((aside / "send.glb").read_bytes(), self.send.exists()), (sending, False))
        self.assertIn(str(aside), res["message"])
        self.assertFalse((self.mod / anim.UNITS).exists())   # (nothing taken in by opening again)


if __name__ == "__main__":
    unittest.main()
