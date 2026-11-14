"""Scenarios: RUSE Decoy on a new squad (the owner, overnight 2026-11-13: "Usual and unusual situations"): Copy this
animation… named in other scripts, Who plays it, a copy's speed, Only this unit on a unit ticked for a copy, Back to the
game's animation, Delete the copy, the unit deleted, the refusals; and Change its animations in Blender for a unit that
plays a copy, opened twice, closed without Send, sent twice.

Two made-up games: test_animactions' squad game (a squad playing stand, run and walk clips; the real Studio through
page_api, the real build), and test_animblender's model, skeleton and clips for Change its animations in Blender (its
stand-ins: the model library, the unit's figures, Blender's sending: test_animglb's Blenderish).

A finding is kept as an expected failure naming it (M-n: D:/RUSE-2.0/scratch/release-0920/scenarios/models/NOTES.md
and the scenarios report); the rest pass on release/0.9.8.20-anim 0d5564eb.

FOR: the models and Blender scenarios (release 0.9.8.20, overnight 2026-11-14).
USED-BY: the scenarios' runs (gentle.py, -m unittest)."""
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf, build
from rusemod.edat import Edat
from rusemod.webui import page_api
import test_animblender   # (the module, not its test class: its tests run in test_animblender once)
from ruse_studio import animblender
from test_animactions import clips_pack, unit_data
from test_animblender import CLIP_BYTES, RUN, Running
from test_animglb import Blenderish
from test_scenarios_models_base import LANGS, PYTHON_WORDS

E = "$/GFX/Everything/"
GAME_SQUAD = E + "Descriptor_Unit_Squad"
OTHER = E + "Descriptor_Unit_Other"
COURSE = "genanim_15\\ww2\\res3d\\units\\common\\fusilier_courselod0.baf"   # (the made-up game's run)


class MadeUpSquadGame(unittest.TestCase):
    """test_animactions' made-up game, its index built once for the class; a fresh platform folder per test, a mod
    and a new squad copying the game's (New mod, New unit), the Studio called as the page calls it."""

    @classmethod
    def setUpClass(cls):
        from rusemod.index import build_index
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        data = cls.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(unit_data())
        (data / "ZZ_Win.dat").write_bytes(clips_pack())
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home)
        self.page = page_api(self.api)
        self.addCleanup(self.api.set_pref, "lang", "us")
        self.mod = Path(self.page.new_mod("Dances")["current"])
        self.squad = self.page.new_unit(GAME_SQUAD, "My Squad", 5, group="new")["address"]
        self.tail = self.squad.rsplit("/", 1)[-1]

    def built(self):
        result = build.build_pack(Edat(unit_data()), [build.load_mod(self.mod)], "0", Edat(clips_pack()))
        return result, {Path(m).name: s.get("unit") for m, s in result.own_clips.items()}

    def said(self, name: str, *args, **kw) -> dict:
        from ruse_studio.api import StudioError
        out = {}
        for lang in LANGS:
            self.api.set_pref("lang", lang)
            try:
                getattr(self.page, name)(*args, **kw)
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


class Copies(MadeUpSquadGame):
    def test_copies_named_in_other_scripts_each_its_own(self):
        """Two copies of the run named in Russian with an emoji and in Chinese: each its own copy (ids copy, copy_2),
        its name kept as typed; the Russian one ticked for the new squad at 150%: the build makes its clip for the
        squad alone, and the other copy, ticked for nobody, is said and not made."""
        one = self.page.decoy_copy_make(COURSE, "Бег 🏃")
        two = self.page.decoy_copy_make(COURSE, "跑")
        self.assertEqual([(one["copy"], one["name"]), (two["copy"], two["name"])], [("copy", "Бег 🏃"), ("copy_2", "跑")])
        who = self.page.decoy_copy_players("copy")
        self.assertEqual(who["units"][0]["address"], self.squad)              # (yours first)
        self.page.decoy_copy_tick("copy", self.squad, [])
        self.page.decoy_anim_set(COURSE, speed=150, copy="copy")
        result, clips = self.built()
        self.assertEqual([f.message for f in result.errors], [])
        self.assertEqual(list(clips), ["own_copy_copy_fusilier_courselod0.baf"])
        self.assertTrue(any("the copy 跑 (copy_2) is ticked for no unit" in f.message for f in result.findings))

    def test_only_this_unit_on_a_unit_ticked_for_a_copy_then_back_to_the_game_s(self):
        """Only this unit (200%) on the squad ticked for a copy (150%): the squad plays its own, the build says the
        copy isn't played by it; Back to the game's animation on the squad: it plays the copy again."""
        self.page.decoy_copy_make(COURSE, "Fast")
        self.page.decoy_copy_tick("fast", self.squad, [])
        self.page.decoy_anim_set(COURSE, speed=150, copy="fast")
        self.page.decoy_anim_set(COURSE, speed=200, unit=self.squad)
        result, clips = self.built()
        self.assertEqual(list(clips), [f"own_my_squad_fusilier_courselod0.baf"])
        self.assertTrue(any(f"{self.tail} has its own copy of" in f.message for f in result.findings))
        self.assertIsNone(self.page.decoy_anim_reset(COURSE, unit=self.squad)["own"])
        result, clips = self.built()
        self.assertEqual(list(clips), ["own_copy_fast_fusilier_courselod0.baf"])

    def test_delete_the_copy_or_the_unit(self):
        """Delete the copy: the unit ticked for it plays the game's run again, the copy's file gone; a copy ticked for
        a unit that is then deleted: the copy stays, ticked for nobody, and the mod builds."""
        self.page.decoy_copy_make(COURSE, "Fast")
        self.page.decoy_copy_tick("fast", self.squad, [])
        self.assertEqual(self.page.decoy_copy_delete("fast")["units"], 1)
        self.assertEqual(self.built()[1], {})
        self.page.decoy_copy_make(COURSE, "Slow")
        self.page.decoy_copy_tick("slow", self.squad, [])
        self.page.delete_unit(self.squad)
        self.assertEqual(anim.mod_copies(self.mod)["slow"]["units"], {})
        result, clips = self.built()
        self.assertEqual(([f.message for f in result.errors], clips), ([], {}))

    def test_the_refusals_in_every_language(self):
        self.page.decoy_copy_make(COURSE, "Fast")
        self.assert_worded(self.said("decoy_copy_make", COURSE, "   "), "A copy's name is 1 to 80 letters.")
        self.assert_worded(self.said("decoy_copy_make", COURSE, "の" * 81), "A copy's name is 1 to 80 letters.")
        self.assert_worded(self.said("decoy_copy_delete", "gone"),
                           "This mod has no copy gone any more: it may have been deleted.")
        self.assertEqual(self.page.decoy_copy_make(COURSE, "の" * 80)["name"], "の" * 80)   # (80 letters, 240 bytes)


class CopyThenBlender(unittest.TestCase):
    """Change its animations in Blender (test_animblender's Studio stand-ins) for a unit ticked to play RUSE Decoy's
    copy of the run at 150%."""
    setUp, tearDown, open = test_animblender.Studio.setUp, test_animblender.Studio.tearDown, test_animblender.Studio.open
    UNIT = "Descriptor_Unit_My_Riflemen"

    def ticked(self, speed=150.0):
        anim.write_copies(self.mod, {"fast_run": {"name": "Fast run", "clip": anim.clip_key(RUN), "speed": speed,
                                                  "units": {self.UNIT: []}}})

    def run_out(self) -> float:
        sent = animblender.read_sent(self.work)
        return next(baf.parse(a["clip"]).duration for a in sent["animations"] if a["name"] == "Run (made_run)")

    @unittest.expectedFailure
    def test_m6_the_run_goes_out_as_the_unit_plays_it(self):
        """M-6: the unit plays the copy "Fast run" (the run at 150%: 0.2667 s), and Change its animations in Blender
        sends the run as the game's (0.4 s): what Blender shows isn't what the unit plays. A change to it brought back
        is the unit's own run made from the game's, which it plays from then on in place of the copy (the build's
        rule: a unit's own rows win), the copy still listing it as ticked, and the page says only "Changed in Blender,
        this unit's own now: Run (made_run)". What should happen: the run goes out as the copy plays it (what then
        happens to a change of it is the owner's to say)."""
        self.ticked()
        self.open()
        self.assertAlmostEqual(self.run_out(), baf.parse(CLIP_BYTES[RUN]).duration / 1.5, places=3)

    def test_what_a_change_to_it_does_now(self):
        """The rest of M-6, pinned as it is on 0d5564eb: the change comes back as the unit's own run, at the game's
        length, and the copy still lists the unit."""
        self.ticked()
        _res, start = self.open()
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("Run (made_run)", "bip01 spine", baf.axis_angle("x", 20.0))))
        got = self.api.decoy_blender_back(E + self.UNIT, "us")
        self.assertEqual(got["changed"], ["Run (made_run)"])
        own = self.mod / anim.OWN / self.UNIT / "blender_made_run.baf"
        self.assertAlmostEqual(baf.parse(own.read_bytes()).duration, baf.parse(CLIP_BYTES[RUN]).duration, places=3)
        self.assertEqual(anim.mod_copies(self.mod)["fast_run"]["units"], {self.UNIT: ()})

    def test_control_a_unit_ticked_for_no_copy_gets_the_game_s_run(self):
        self.open()
        self.assertAlmostEqual(self.run_out(), baf.parse(CLIP_BYTES[RUN]).duration, places=3)

    def test_opened_twice_closed_without_send_sent_twice(self):
        """Opened while its Blender is open: refused in words in every language; closed without Send: Bring my
        changes back refused in words; sent twice: the last sending comes back."""
        from ruse_studio.api import StudioError
        from ruse_studio import errortext
        _res, start = self.open()
        self.api._blenders[str(self.work)] = Running()
        with mock.patch("rusemod.models.Library", lambda game: self.lib), self.assertRaises(StudioError) as cm:
            self.api.decoy_blender(E + self.UNIT, "us")
        said = str(cm.exception)
        self.assertEqual(said, "This unit's animations are open in Blender already: change them there, then bring "
                               "your changes back.")
        for lang in LANGS[1:]:
            with self.subTest(lang=lang):
                self.assertNotEqual(errortext.worded(said, lang), said)
        self.api._blenders.clear()
        with self.assertRaises(StudioError) as cm:
            self.api.decoy_blender_back(E + self.UNIT, "us")
        for lang in LANGS[1:]:
            with self.subTest(lang=lang, what="nothing sent"):
                self.assertNotEqual(errortext.worded(str(cm.exception), lang), str(cm.exception))
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("Run (made_run)", "bip01 spine", baf.axis_angle("x", 10.0))))
        self.send.write_bytes(Blenderish(Path(start).read_bytes()).send(
            change=("Stand (made_stand)", "bip01 spine", baf.axis_angle("x", 25.0))))   # (changed again, Send again)
        got = self.api.decoy_blender_back(E + self.UNIT, "us")
        self.assertEqual(got["changed"], ["Stand (made_stand)"])
        units = tomllib.loads((self.mod / anim.UNITS).read_text(encoding="utf-8"))["unit"][self.UNIT]
        self.assertNotIn("b_course", str(units))


if __name__ == "__main__":
    unittest.main()
