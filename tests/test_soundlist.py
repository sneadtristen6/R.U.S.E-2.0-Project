"""rusemod.soundlist: every game sound by kind, its group and a dialogue line's words."""
import sqlite3
import unittest

from rusemod import soundlist

B = "\\"


def p(*parts):
    return B.join(parts)


class Kinds(unittest.TestCase):
    def test_each_folder_its_kind(self):
        s = p("gen_sound", "ww2", "sons")
        for member, kind in (
                (p(s, "sfx_ruse", "sfx_tir", "sfx_bomb.ess"), "weapons"),
                (p(s, "sfx_ruse", "sfx_traine", "traine_roquette_01.ess"), "weapons"),
                (p(s, "sfx_ruse", "sfx_tir_long_range", "sfx_lr_canonbig_01.ess"), "weapons_far"),
                (p(s, "sfx_ruse", "sfx_impact", "sfx_dest_leger.ess"), "impacts"),
                (p(s, "sfx_ruse", "avionecrasement.ess"), "impacts"),
                (p(s, "sfx", "impact", "ge_charleger_rebond_01.ess"), "impacts"),
                (p(s, "sfx_impact", "ge_charmoyen_rebond_01.ess"), "impacts"),
                (p(s, "sfx_moteur", "ge_jeep_run.ess"), "engines"),
                (p(s, "sfx_env", "cow_01.ess"), "surroundings"),
                (p(s, "sfx_env", "multipiste_ambiance_swamp.ess"), "backgrounds"),
                (p(s, "hud", "click2.ess"), "interface"),
                (p(s, "sfx_option", "audiomenu_voice_01.ess"), "interface"),
                (p(s, "hud", "placement_ruse_silenceradio.ess"), "ruses"),
                (p(s, "generated", "acknows", "eu_lighttank_move_1.ess"), "unit_voices"),
                (p(s, "generated", "acknows", "fr", "hq_building_captured_all_1.ess"), "hq_voices"),
                (p(s, "acknows", "2d", "radio", "x.ess"), "radio"),
                (p(s, "atp_music", "battle1.ess"), "music"),
                (p(s, "jingles", "jingle-new.ess"), "music"),
                (p("gen_sound", "test", "map", "m04_cotentin", "scripting", "dialog", "dev", "us", "09vaid_9.ess"),
                 "dialogue"),
                (p(s, "generated", "dialogues", "ne_pas_enlever.ess"), "other")):
            with self.subTest(member=member):
                self.assertEqual(soundlist.kind_of(member), kind)

    def test_language_mission_and_words(self):
        line = p("gen_sound", "test", "map", "m04_cotentin", "scripting", "dialog", "dev", "it", "09vaid_9.ess")
        self.assertEqual(soundlist.language_of(line), "ita")   # the folder says it, the texts say ita
        self.assertEqual(soundlist.mission_of(line), "m04_cotentin")
        self.assertIsNone(soundlist.language_of(p("gen_sound", "ww2", "sons", "hud", "click2.ess")))
        self.assertEqual(soundlist.words("x\\SFX_Tir_ObusAP_Leger_01.ess"), "Tir obusap leger 01")
        self.assertEqual(soundlist.words("x\\Ruse-Inter-Clic de bouton-2.ess"), "Clic de bouton 2")


class Catalogue(unittest.TestCase):
    def db(self):
        """A game index in miniature (rusemod.index's tables that the list reads)."""
        db = sqlite3.connect(":memory:")
        db.executescript("""
            CREATE TABLE object(id INTEGER PRIMARY KEY, class TEXT, shadow INTEGER);
            CREATE TABLE value(object INTEGER, path TEXT, num REAL, text TEXT);
            CREATE TABLE ref(src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
            CREATE TABLE text(file INTEGER, lang TEXT, dictionary TEXT, key TEXT, name TEXT, text TEXT);
            INSERT INTO object VALUES (1,'TSoundSettings',0),(2,'TSoundDescriptor',0),(3,'TSoundStream',0),
                                      (4,'TCutsceneDescriptor',0),(5,'TSoundStream',0),(6,'TSoundSettings',0),
                                      (7,'TSoundDescriptor',0);
            INSERT INTO value VALUES (1,'Identifier',NULL,'SFX_Tir_Canon_01'),(1,'VolumeRef',0.7,NULL),
                                     (2,'Settings_Identifier',NULL,'SFX_Tir_Canon_01'),
                                     (3,'FileName',NULL,'WW2\\Sons\\SFX_RUSE\\SFX_Tir\\SFX_Tir_ObusAP_Leger_01.wav'),
                                     (4,'Key',NULL,'09vAID_9'),(4,'Settings_Identifier',NULL,'GENERATED_DIALOG_GFX'),
                                     (5,'FileName',NULL,'DataDir:\\Test\\map\\M04_cotentin\\scripting\\Dialog\\Dev\\09vAID_9.ol'),
                                     (6,'Identifier',NULL,'SFX_Tir_Canon_01_LR'),
                                     (7,'Settings_Identifier',NULL,'SFX_Tir_Canon_01_LR');
            INSERT INTO ref VALUES (2,'TheSoundStream','object',3,NULL),(4,'TheSoundStream','object',5,NULL),
                                   (7,'TheSoundStream','object',3,NULL);
            INSERT INTO text VALUES (1,'us','dialog','k','09vAID_9','General, the first wave is on the beach.'),
                                    (1,'fr','dialog','k','09vAID_9','Général, la première vague est sur la plage.');
        """)
        return db

    def test_every_sound_with_its_group_and_words(self):
        db = self.db()
        shot = p("gen_sound", "ww2", "sons", "sfx_ruse", "sfx_tir", "sfx_tir_obusap_leger_01.ess")
        line = p("gen_sound", "test", "map", "m04_cotentin", "scripting", "dialog", "dev", "fr", "09vaid_9.ess")
        h = {"frames": 22050, "rate": 22050, "channels": 1, "flag": 0}
        rows = soundlist.catalogue(db, {line: h, shot: h})
        self.assertEqual([r["kind"] for r in rows], ["weapons", "dialogue"])   # in the kinds' order
        self.assertEqual((rows[0]["group"], round(rows[0]["group_volume"], 2), rows[0]["also"]),
                         ("SFX_Tir_Canon_01", 0.7, ["SFX_Tir_Canon_01_LR"]))      # used near and far: both groups
        self.assertEqual((rows[1]["key"], rows[1]["lang"], rows[1]["group"], rows[1]["seconds"]),
                         ("09vAID_9", "fr", "GENERATED_DIALOG_GFX", 1.0))
        self.assertEqual(soundlist.subtitles(db, ["09vAID_9"], "fr"),
                         {"09vAID_9": "Général, la première vague est sur la plage."})


if __name__ == "__main__":
    unittest.main()
