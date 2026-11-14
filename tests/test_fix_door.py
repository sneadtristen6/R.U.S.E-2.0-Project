"""RUSE Decoy's Change its animations in Blender / Bring my changes back, after reviewer 4's findings were fixed
(tests/test_review_decoy.py holds the reviewer's own): what the reviewer found but left without a test (the words for
an animation made in Blender, a sending set aside by a second opening, the file each round keeps), and the same faults
as a class (a bone deleted in Blender, not only renamed; a frame rate other than the game's with a change in it; the
halves warning where it must not be said). Each check has a legitimate case beside it that must still work.

On the made-up model, skeleton and clips of test_gltf_bones and test_animglb (no game files), Blender's part played by
test_animglb's stand-in (Blenderish) doing what a real Blender does for that edit."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import re
import tomllib
import unittest
from pathlib import Path

from rusemod import anim, baf, gltf, modelin, rig
from test_animblender import CLIP_BYTES, RUN, SQUAD
from test_animglb import CLIPS, ORIGINALS, Blenderish, gltf_bytes
from test_gltf_bones import NAME, RECORD, FakeLibrary
from test_review_decoy import HEAD_TURN, SPINE_TURN, UNIT, Door

SRC = Path(__file__).resolve().parents[1] / "src"


def without_bone(raw: bytes, bone: str) -> bytes:
    """What Blender sends when the modder deleted a bone (Edit mode, X) and the bones under it kept where they were
    in the model at every frame: its node out of the skin, its children hung from its parent, each child's rest and
    keys made from the two (so the deleted bone's own turn is carried by its children)."""
    import struct
    from rusemod.gltf import FLOAT, _Glb
    doc, binary = modelin.glb_document(raw)
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    nodes = doc["nodes"]
    s = next(i for i, n in enumerate(nodes) if n.get("name") == bone)
    p = next(i for i, n in enumerate(nodes) if s in n.get("children", []))
    kids = list(nodes[s].get("children", []))

    def trs(n: dict) -> tuple:
        return (tuple(n.get("translation", (0.0, 0.0, 0.0))), tuple(n.get("rotation", (0.0, 0.0, 0.0, 1.0))),
                tuple(n.get("scale", (1.0, 1.0, 1.0))))

    def joined(a, b) -> tuple:
        move, turn, size, _off = rig.decompose(rig.mul(rig.compose(*a), rig.compose(*b)))
        return list(move), list(turn), list(size)
    for c in kids:
        t, r, z = joined(trs(nodes[s]), trs(nodes[c]))
        nodes[c].update(translation=t, rotation=r, scale=z)
    for a in doc["animations"]:
        got = {}
        for ch in a["channels"]:
            got.setdefault(ch["target"]["node"], {})[ch["target"]["path"]] = ch
        paths = ("translation", "rotation", "scale")
        mine = [modelin.glb_accessor(doc, binary, a["samplers"][got[s][q]["sampler"]]["output"]) for q in paths]
        for c in kids:
            theirs = [modelin.glb_accessor(doc, binary, a["samplers"][got[c][q]["sampler"]]["output"]) for q in paths]
            new = [joined((mine[0][k], mine[1][k], mine[2][k]), (theirs[0][k], theirs[1][k], theirs[2][k]))
                   for k in range(len(mine[0]))]
            for i, q in enumerate(paths):
                out = g.accessor([tuple(v[i]) for v in new], "VEC4" if q == "rotation" else "VEC3", FLOAT, target=None)
                a["samplers"][got[c][q]["sampler"]]["output"] = out
        a["channels"] = [ch for ch in a["channels"] if ch["target"]["node"] != s]
    nodes[p]["children"] = [x for x in nodes[p]["children"] if x != s] + kids
    nodes[s].pop("children", None)
    skin = doc["skins"][0]
    ibm = modelin.glb_accessor(doc, binary, skin["inverseBindMatrices"])
    k = skin["joints"].index(s)
    skin["joints"] = skin["joints"][:k] + skin["joints"][k + 1:]
    flat = [v for m in ibm[:k] + ibm[k + 1:] for v in m]
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(flat)}f", *flat)), "componentType": FLOAT,
                               "count": len(skin["joints"]), "type": "MAT4"})
    skin["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
    return g.to_bytes()


def at_rate(raw: bytes, rate: float) -> bytes:
    """What Blender sends with its scene set to `rate` frames a second: each frame at its time at that rate."""
    from rusemod.gltf import FLOAT, _Glb
    doc, binary = modelin.glb_document(raw)
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    for a in doc["animations"]:
        times = [t * baf.FPS / rate for t in modelin.glb_accessor(doc, binary, a["samplers"][0]["input"])]
        tin = g.accessor(times, "SCALAR", FLOAT, target=None)
        g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
        for s in a["samplers"]:
            s["input"] = tin
    return g.to_bytes()


class Engine(unittest.TestCase):
    """rusemod.rig on the made-up model: a bone the file hasn't got (D-F1's class), the rate a file was sampled at
    (D-F8's)."""

    def setUp(self):
        self.raw, _pics, _s = gltf.model_glb(FakeLibrary(), NAME, clips=CLIPS)

    def back(self, raw: bytes):
        r = rig.rig_of(*modelin.glb_document(raw))
        return r, rig.back_of(r, RECORD)

    def test_a_bone_missing_from_the_file_is_held_and_its_children_stay_where_the_file_has_them(self):
        """The spine deleted in Blender, the bones under it where they were: every clip comes back byte for byte (the
        spine held as it went out, fx_point and the head from it). Before the fix the spine's turn counted twice in its
        children and every clip came back changed."""
        r, back = self.back(without_bone(Blenderish(self.raw).send(), "bip01 spine"))
        self.assertEqual((back.missing, back.new), (["bip01 spine"], []))
        got = rig.clips_back(r, back, RECORD, ORIGINALS)
        self.assertEqual([(g["name"], g["same"], g["changed"]) for g in got], [(n, True, []) for n in ORIGINALS])

    def test_with_a_bone_missing_a_change_elsewhere_is_still_that_change_alone(self):
        """The same, and the head turned in the run: the run comes back changed on the head alone (the spine and
        fx_point byte for byte as they went out), the stand as it went out."""
        sent = Blenderish(self.raw).send(change=("Run (made_run)", "bip01 head", HEAD_TURN))
        r, back = self.back(without_bone(sent, "bip01 spine"))
        got = {g["name"]: g for g in rig.clips_back(r, back, RECORD, ORIGINALS)}
        self.assertEqual(got["Run (made_run)"]["changed"], ["bip01 head"])
        self.assertTrue(got["Stand (made_stand)"]["same"])

    def test_the_rate_a_file_was_sampled_at(self):
        sent = Blenderish(self.raw).send()
        self.assertAlmostEqual(rig.sampled_rate(rig.rig_of(*modelin.glb_document(sent))), 30.0, places=2)
        self.assertAlmostEqual(rig.sampled_rate(rig.rig_of(*modelin.glb_document(at_rate(sent, 24.0)))), 24.0,
                               places=2)
        # the Studio's own file keeps keys only where Blender needs them: not evenly spaced, so not told
        self.assertIsNone(rig.sampled_rate(rig.rig_of(*modelin.glb_document(self.raw))))

    def test_at_another_rate_each_frame_is_one_of_the_game_s(self):
        """Sent at 24 frames a second with the spine turned in the run: the clip made frame for frame is the very clip
        the same change makes at the game's 30 (byte for byte), and the untouched stand is the one that went out."""
        r30, back30 = self.back(Blenderish(self.raw).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        at30 = {g["name"]: g for g in rig.clips_back(r30, back30, RECORD, ORIGINALS)}
        sent24 = at_rate(Blenderish(self.raw).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)), 24.0)
        r24, back24 = self.back(sent24)
        at24 = {g["name"]: g for g in rig.clips_back(r24, back24, RECORD, ORIGINALS, rate=rig.sampled_rate(r24))}
        self.assertEqual(at24["Run (made_run)"]["clip"], at30["Run (made_run)"]["clip"])
        self.assertEqual(at24["Run (made_run)"]["changed"], ["bip01 spine"])
        self.assertEqual(at24["Stand (made_stand)"]["clip"], ORIGINALS["Stand (made_stand)"])


class Words(unittest.TestCase):
    """D-F10: "They stay in your Blender file." wasn't true (nothing saves a .blend). The words are made true in all 11
    languages, and nothing keeps a new animation (keeping one waits on the owner's question 2)."""

    def test_an_animation_made_in_blender_isn_t_said_to_stay_in_a_file(self):
        words = tomllib.loads((SRC / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))["decoy_blender_new"]
        old = {"us": "They stay in your Blender file.", "fr": "Elles restent dans votre fichier Blender.",
               "ger": "Sie bleiben in deiner Blender-Datei.", "ita": "Restano nel tuo file Blender.",
               "spa": "Se quedan en tu archivo de Blender.", "pol": "Zostają w twoim pliku Blendera.",
               "ru": "Они остаются в вашем файле Blender.", "cz": "Zůstávají ve tvém souboru Blenderu.",
               "jpn": "Blenderのファイルに残ります。", "sc": "它们保留在你的 Blender 文件里。",
               "fa": "در فایل Blender شما می‌مانند."}
        for lang, text in old.items():
            self.assertIn("{names}", words[lang], lang)
            self.assertNotIn(text, words[lang], lang)
            self.assertIn("(File > Save)", words[lang].replace("（", "(").replace("）", ")"), lang)  # Blender's menu
        self.assertEqual(words["us"], "Made in Blender, played by no action yet: {names}. The Studio doesn't take "
                                      "them in: to keep them, save them in Blender (File > Save).")
        # what makes them true: nothing the door runs saves a .blend, and Send writes only the .glb and what it says
        source = (SRC / "rusemod" / "blender_model.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"save_as_mainfile|save_mainfile|wm\.save", source))


class DoorFixes(Door):
    """The Studio's own calls (test_review_decoy.Door's set-up: a new unit of a mod on the made-up model)."""

    def own_files(self) -> set:
        folder = self.mod / anim.OWN / UNIT
        return {p.name for p in folder.glob("*.baf")} if folder.is_dir() else set()

    def named(self) -> set:
        return anim.files_named(self.mod, UNIT)

    # --- D-F10: an animation made in Blender ---
    def test_an_animation_made_in_blender_is_said_and_nothing_of_it_kept(self):
        start = self.open()
        doc, binary = modelin.glb_document(Blenderish(start).send())
        doc["animations"].append(dict(doc["animations"][0], name="Wave"))    # (a new action: the stand's keys copied)
        self.send.write_bytes(gltf_bytes(doc, binary))
        got = self.back()
        self.assertEqual((got["new"], got["changed"], got["written"]), (["Wave"], [], 0))
        self.assertIn("Made in Blender, played by no action yet: Wave. The Studio doesn't take them in", got["message"])
        self.assertEqual(self.own_files(), set())
        self.assertFalse((self.mod / anim.UNITS).exists())

    # --- D-F11: a sending set aside by a second opening ---
    def test_a_sending_set_aside_can_still_be_brought_back(self):
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.assertTrue(self.api.decoy_blender_state(SQUAD)["waiting"])
        started = []
        from unittest import mock
        with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append(model) or __import__(
                               "test_animblender").Closed()):
            opened = self.api.decoy_blender(SQUAD, "us")
        aside = Path(opened["set_aside"])
        self.assertTrue(all((aside / f).is_file() for f in ("send.glb", "animations.json", "clips/0.baf", "clips/1.baf")))
        self.assertIn(str(aside), opened["message"])
        self.assertIn("Bring back the set-aside sending takes it in", opened["message"])
        self.assertFalse((self.mod / anim.UNITS).exists())             # (nothing taken in by opening again)
        st = self.api.decoy_blender_state(SQUAD)
        self.assertEqual((st["aside"], st["aside_folder"]), (aside.name, str(aside)))
        # the new Blender sent nothing: Bring my changes back says so, and the sending set aside isn't read by it
        with self.assertRaisesRegex(StudioError, "^Nothing has come back from Blender yet"):
            self.back()
        got = self.api.decoy_blender_back(SQUAD, "us", aside.name)
        self.assertEqual((got["changed"], got["written"]), (["Run (made_run)"], 1))
        units = tomllib.loads((self.mod / anim.UNITS).read_text(encoding="utf-8"))["unit"][UNIT]
        self.assertEqual(units["figure"], {"GfxDescriptorBazooka": {"action": {"t_tir": "blender_made_run.baf"}},
                                           "GfxDescriptorFusilier": {"action": {"b_course": "blender_made_run.baf"}}})
        self.assertFalse(aside.exists())
        self.assertIsNone(got["aside"])
        with self.assertRaisesRegex(StudioError, "^There's no sending set aside called"):
            self.api.decoy_blender_back(SQUAD, "us", aside.name)

    def test_two_sendings_set_aside_are_both_reachable_newest_first(self):
        from unittest import mock
        from test_animblender import Closed

        def reopen() -> tuple:
            started = []
            with mock.patch("rusemod.models.Library", lambda game: self.lib), \
                    mock.patch("rusemod.blender.open_model_to_change",
                               lambda b, model, send, words: started.append(model) or Closed()):
                res = self.api.decoy_blender(SQUAD, "us")
            return res, Path(started[0]).read_bytes()
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        first, start = reopen()
        self.send.write_bytes(Blenderish(start).send(change=("Stand (made_stand)", "bip01 head", HEAD_TURN)))
        second, _start = reopen()
        self.assertEqual(self.api.decoy_blender_state(SQUAD)["aside"], Path(second["set_aside"]).name)
        got = self.api.decoy_blender_back(SQUAD, "us", Path(second["set_aside"]).name)
        self.assertEqual(got["changed"], ["Stand (made_stand)"])
        self.assertEqual(got["aside"], Path(first["set_aside"]).name)
        got = self.api.decoy_blender_back(SQUAD, "us", got["aside"])
        self.assertEqual((got["changed"], got["aside"]), (["Run (made_run)"], None))

    def test_a_name_that_isn_t_a_sending_set_aside_is_refused(self):
        from ruse_studio.api import StudioError
        self.open()
        for name in ("../../mod", "sent-not-brought-x/../..", "clips", ""):
            with self.assertRaisesRegex(StudioError, "^There's no sending set aside called"):
                self.api.decoy_blender_back(SQUAD, "us", name)

    # --- D-F6's class: a sending made for another opening ---
    def about(self, **said) -> None:
        """What Send writes beside the file (rusemod.blender_model.say_about) for the sending in place."""
        import hashlib
        (self.work / "send.glb.json").write_text(json.dumps(
            {"glb": hashlib.sha256(self.send.read_bytes()).hexdigest(), "fps": 30.0, "nla": [], **said}),
            encoding="utf-8")

    def test_a_blender_left_open_from_an_earlier_opening_is_told_apart(self):
        """The Studio restarted while Blender was open, the animations opened again: the old Blender's sending (Send
        writes the opening it was started for beside it) is refused, nothing written; the one opened last is taken."""
        from ruse_studio.api import StudioError
        start = self.open()
        session = json.loads((self.work / "words.json").read_text(encoding="utf-8"))["session"]
        self.assertEqual(session, json.loads((self.work / "state.json").read_text(encoding="utf-8"))["session"])
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.about(session="an earlier one")
        with self.assertRaisesRegex(StudioError, "^What came back was sent by a Blender opened before the last"):
            self.back()
        self.assertFalse((self.mod / anim.UNITS).exists())
        self.about(session=session, nla=["Stand (made_stand)"])       # (the Blender opened last: taken, NLA said)
        got = self.back()
        self.assertEqual((got["changed"], got["nla"]), (["Run (made_run)"], ["Stand (made_stand)"]))
        self.assertIn("Blender's NLA editor plays these with timing of its own", got["message"])

    def test_what_send_said_of_another_sending_is_not_read(self):
        start = self.open()
        self.send.write_bytes(Blenderish(start).send())
        self.about(session="an earlier one", nla=["Run (made_run)"])
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        got = self.back()                        # (its fingerprint is of the sending before: said of none)
        self.assertEqual((got["changed"], got["nla"]), (["Run (made_run)"], []))

    # --- D-F12: one file, the same each round, none left that nothing names ---
    def test_each_round_keeps_the_same_file_and_none_is_left_unnamed(self):
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.assertEqual(self.back()["changed"], ["Run (made_run)"])
        first = (self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes()
        start = self.open()          # (round two: the run goes out as the unit's own now)
        sent = json.loads((self.work / "animations.json").read_text(encoding="utf-8"))
        self.assertIn("Run (blender_made_run)", [a["name"] for a in sent["animations"]])
        self.send.write_bytes(Blenderish(start).send(change=("Run (blender_made_run)", "bip01 head", HEAD_TURN)))
        got = self.back()
        self.assertEqual(got["changed"], ["Run (blender_made_run)"])
        self.assertEqual(self.own_files(), {"blender_made_run.baf"})          # (no blender_blender_made_run.baf)
        self.assertEqual(self.named(), {"blender_made_run.baf"})
        second = (self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes()
        self.assertNotEqual(second, first)
        # undone in the same Blender: the file as it went out this round (round one's), in its place, nothing left over
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual(got["undone"], ["Run (blender_made_run)"])
        self.assertEqual((self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes(), first)
        self.assertEqual((self.own_files(), self.named()), ({"blender_made_run.baf"}, {"blender_made_run.baf"}))

    def test_a_change_undone_in_the_same_blender_leaves_no_file_behind(self):
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.back()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 head", HEAD_TURN)))
        got = self.back()                                   # (a second change in the same Blender: the same file)
        self.assertEqual((got["changed"], self.own_files()), (["Run (made_run)"], {"blender_made_run.baf"}))
        self.send.write_bytes(Blenderish(start).send())
        got = self.back()
        self.assertEqual((got["undone"], got["changed"]), (["Run (made_run)"], []))
        self.assertIn("Your change undone in Blender, so they play as before again: Run (made_run).", got["message"])
        self.assertEqual(self.own_files(), set())
        self.assertFalse((self.mod / anim.UNITS).exists())
        # a fourth sending as the third: nothing new
        got = self.back()
        self.assertEqual((got["written"], got["message"]),
                         (0, "Nothing new has come from Blender since your changes were last brought back."))

    def test_a_change_taken_out_elsewhere_since_is_taken_in_again(self):
        """The run changed and brought back, then its own clip taken out elsewhere (RUSE Decoy's way back to the game's:
        rusemod.anim.remove_unit_clip); Bring my changes back again with the same sending: Blender still shows the
        change, so it is taken in again, never called nothing new."""
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        self.back()
        for fig, key in (("GfxDescriptorBazooka", "t_tir"), ("GfxDescriptorFusilier", "b_course")):
            anim.remove_unit_clip(self.mod, UNIT, key, figure=fig)
        self.assertFalse((self.mod / anim.UNITS).exists())
        got = self.back()
        self.assertEqual((got["changed"], got["written"]), (["Run (made_run)"], 1))
        self.assertEqual((self.own_files(), self.named()), ({"blender_made_run.baf"}, {"blender_made_run.baf"}))

    def test_a_model_animation_put_back_elsewhere_since_is_taken_in_again(self):
        """The same for a model on bones of its own: the run changed and brought back, then the model's animations put
        back as they were (Import model again); the same sending brought back again takes the change in again."""
        files = self.own_bones_unit({"stand": CLIP_BYTES[__import__("test_animblender").STAND], "run": CLIP_BYTES[RUN]})
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("run", "bip01 spine", SPINE_TURN)))
        changed = self.back()
        self.assertEqual(changed["changed"], ["run"])
        mine = (self.mod / anim.OWN / UNIT / files["run"]).read_bytes()
        anim.set_animations(self.mod, UNIT, {"stand": CLIP_BYTES[__import__("test_animblender").STAND],
                                            "run": CLIP_BYTES[RUN]})
        got = self.back()
        self.assertEqual((got["changed"], got["written"]), (["run"], 1))
        self.assertEqual((self.mod / anim.OWN / UNIT / files["run"]).read_bytes(), mine)

    def test_a_file_another_animation_plays_is_never_written_over(self):
        """The game's run on one figure and a file of the unit's own on another, both called blender_made_run once
        written: the run changed takes a file of its own (blender_made_run_2.baf), the other figure's file stays."""
        mine = baf.build(baf.parse(CLIP_BYTES[RUN]))
        anim.add_unit_clip(self.mod, UNIT, "t_tir", mine, name="blender_made_run", figure="GfxDescriptorBazooka")
        before = (self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes()
        start = self.open()
        sent = json.loads((self.work / "animations.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(a["name"] for a in sent["animations"]),
                         ["Run (blender_made_run)", "Run (made_run)", "Stand (made_stand)"])
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        got = self.back()
        self.assertEqual(got["changed"], ["Run (made_run)"])
        self.assertEqual((self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes(), before)
        units = self.rows()
        self.assertEqual(units["figure"]["GfxDescriptorFusilier"]["action"]["b_course"], "blender_made_run_2.baf")
        self.assertEqual(units["figure"]["GfxDescriptorBazooka"]["action"]["t_tir"], "blender_made_run.baf")

    # --- D-F1's class: a bone deleted, not only renamed ---
    def test_a_bone_deleted_in_blender_is_refused_naming_it(self):
        from ruse_studio.api import StudioError
        start = self.open()
        self.send.write_bytes(without_bone(Blenderish(start).send(), "bip01 spine"))
        with self.assertRaisesRegex(StudioError, "^These bones of this unit's skeleton didn't come back from Blender: "
                                                 "bip01 spine\\. "):
            self.back()
        self.assertFalse((self.mod / anim.UNITS).exists())
        self.assertTrue(self.api.decoy_blender_state(SQUAD)["waiting"])     # (refused: still not brought back)

    def test_a_renamed_bone_is_named_both_ways_as_spelled_in_blender(self):
        from ruse_studio.api import StudioError
        from test_review_decoy import renamed
        start = self.open()
        self.send.write_bytes(renamed(Blenderish(start).send(), "bip01 spine", "Spine.R"))
        with self.assertRaisesRegex(StudioError, "didn't come back from Blender: bip01 spine, and these came back that "
                                                 "it hasn't got: Spine\\.R\\. "):
            self.back()
        self.assertFalse((self.mod / anim.UNITS).exists())

    def test_a_bone_added_and_nothing_else_changed_is_said_and_takes_nothing_in(self):
        from test_review_decoy import with_new_bone
        start = self.open()
        self.send.write_bytes(with_new_bone(Blenderish(start).send(), "Run (made_run)", "bip01 head"))
        got = self.back()
        self.assertEqual((got["new_bones"], got["changed"], got["written"]), (["prop"], [], 0))
        self.assertIn("Bones made in Blender, which this unit's skeleton hasn't got, so the game can't play them: prop.",
                      got["message"])

    # --- D-F8's class: another frame rate with a change ---
    def test_a_change_at_24_frames_a_second_is_taken_in_frame_for_frame_and_said(self):
        start = self.open()
        self.send.write_bytes(at_rate(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)),
                                      24.0))
        got = self.back()
        self.assertEqual(got["changed"], ["Run (made_run)"])
        self.assertAlmostEqual(got["fps"], 24.0, places=2)
        self.assertIn("Blender's scene played at 24 frames a second and the game plays at 30", got["message"])
        mine = baf.parse((self.mod / anim.OWN / UNIT / "blender_made_run.baf").read_bytes())
        theirs = baf.parse(CLIP_BYTES[RUN])
        self.assertEqual((mine.frames, mine.duration), (theirs.frames, theirs.duration))

    def test_the_game_s_own_rate_says_nothing_of_frames(self):
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("Run (made_run)", "bip01 spine", SPINE_TURN)))
        got = self.back()
        self.assertIsNone(got["fps"])
        self.assertNotIn("frames a second", got["message"])

    # --- D-F3's warning: only where the half doesn't play the change ---
    def test_a_change_on_the_animation_s_own_half_or_a_picked_one_is_not_warned(self):
        self.own_bones_unit({"t_stand": CLIP_BYTES[__import__("test_animblender").STAND], "b_run": CLIP_BYTES[RUN]},
                            split="bip01 spine")
        start = self.open()
        self.send.write_bytes(Blenderish(start).send(change=("b_run", "bip01 l thigh", HEAD_TURN)))
        got = self.back()                       # (the thigh is the lower half's: b_run plays it)
        self.assertEqual((got["changed"], got["halves"]), (["b_run"], []))
        self.send.write_bytes(Blenderish(start).send(change=("b_run", "bip01 head", HEAD_TURN)))
        got = self.back()                       # (the head is the upper half's: said, as not tried in the game)
        self.assertEqual(got["halves"], ["b_run (bip01 head)"])
        self.assertIn("not tried in the game yet", got["message"])
        anim.set_pick(self.mod, UNIT, "course", "b_run")      # (picked for an action: both halves play it)
        self.send.write_bytes(Blenderish(start).send(change=("b_run", "bip01 head", SPINE_TURN)))
        got = self.back()
        self.assertEqual((got["changed"], got["halves"]), (["b_run"], []))


if __name__ == "__main__":
    unittest.main()
