"""RUSE Decoy's calls (ruse_studio.decoy, DecoyCalls): every game sound by kind, a mission's lines with their words, a
sound's volume saved in the mod, a whole kind's at once, a unit's own sounds, and any sound replaced through the
Music tab's calls."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import sqlite3
import tempfile
import threading
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import sound
from ruse_studio.decoy import DecoyCalls, DecoyError
from ruse_studio.music import MusicCalls

B = "\\"
SHOT = B.join(["gen_sound", "ww2", "sons", "sfx_ruse", "sfx_tir", "sfx_tir_obusap_leger_01.ess"])
RUN = B.join(["gen_sound", "ww2", "sons", "sfx_moteur", "ge_charmoyen_run.ess"])
IDLE = B.join(["gen_sound", "ww2", "sons", "sfx_moteur", "ge_charmoyen_idleandstop.ess"])
VOICE = B.join(["gen_sound", "ww2", "sons", "generated", "acknows", "eu_mediumtank_move_1.ess"])
LINE = {lang: B.join(["gen_sound", "test", "map", "m04_cotentin", "scripting", "dialog", "dev", lang, "09vaid_9.ess"])
        for lang in ("us", "fr")}
UNIT = "$/GFX/Everything/Descriptor_Unit_Sherman"


def snd(frames=2000, flag=1):
    return sound.encode([((i * 37) % 2000) - 1000 for i in range(frames)], 1, 22050, flag)


def index_db():
    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE object(id INTEGER PRIMARY KEY, class TEXT, shadow INTEGER, address TEXT, export TEXT);
        CREATE TABLE value(object INTEGER, path TEXT, num REAL, text TEXT);
        CREATE TABLE ref(src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
        CREATE TABLE text(file INTEGER, lang TEXT, dictionary TEXT, key TEXT, name TEXT, text TEXT);
        INSERT INTO object VALUES (1,'TSoundSettings',0,'a1',NULL),(2,'TSoundDescriptor',0,'a2',NULL),
                                  (3,'TSoundStream',0,'a3',NULL),(4,'TCutsceneDescriptor',0,'a4',NULL),
                                  (5,'TSoundStream',0,'a5',NULL),
                                  (10,'TUniteAuSolDescriptor',0,'$/GFX/Everything/Descriptor_Unit_Sherman',NULL),
                                  (11,'TSoundMotorDescriptor',0,'m',NULL),(12,'TSoundDescriptor',0,'r',NULL),
                                  (13,'TSoundStream',0,'rs',NULL),(14,'TSoundDescriptor',0,'i',NULL),
                                  (15,'TSoundStream',0,'is',NULL);
        INSERT INTO value VALUES (1,'Identifier',NULL,'SFX_Tir_Canon_01'),(1,'VolumeRef',0.7,NULL),
            (2,'Settings_Identifier',NULL,'SFX_Tir_Canon_01'),
            (3,'FileName',NULL,'WW2\\Sons\\SFX_RUSE\\SFX_Tir\\SFX_Tir_ObusAP_Leger_01.wav'),
            (4,'Key',NULL,'09vAID_9'),
            (5,'FileName',NULL,'DataDir:\\Test\\map\\M04_cotentin\\scripting\\Dialog\\Dev\\09vAID_9.ol'),
            (13,'FileName',NULL,'WW2\\Sons\\SFX_Moteur\\GE_CharMoyen_Run.wav'),
            (15,'FileName',NULL,'WW2\\Sons\\SFX_Moteur\\GE_CharMoyen_IdleAndStop.wav');
        INSERT INTO ref VALUES (2,'TheSoundStream','object',3,NULL),(4,'TheSoundStream','object',5,NULL),
            (10,'SoundMotorDescriptor','object',11,NULL),(11,'Run_Snd','object',12,NULL),
            (11,'IdleAndStop_Snd','object',14,NULL),(12,'TheSoundStream','object',13,NULL),
            (14,'TheSoundStream','object',15,NULL);
        INSERT INTO text VALUES (1,'us','dialog','k','09vAID_9','General, the first wave is on the beach.'),
                                (1,'fr','dialog','k','09vAID_9','Général, la première vague est sur la plage.');
    """)
    return db


class Calls(MusicCalls, DecoyCalls):
    """RUSE Decoy on a made-up game: ZZ_Win.dat with a gun shot, a tank's engine, a voice line and a mission line in
    two languages; a game index in miniature; a mod folder; a cache folder."""

    def __init__(self, d: str, mod: bool = True):
        from fixtures import make_edat
        self.root = Path(d)
        self.game = self.root / "R.U.S.E"
        data = self.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        self.raw = {SHOT: snd(flag=0), RUN: snd(3000, 0), IDLE: snd(1500, 0), VOICE: snd(), LINE["us"]: snd(),
                    LINE["fr"]: snd(2500)}
        files = []
        for m, b in self.raw.items():
            folder, name = m.rsplit(B, 1)
            files.append(("dir", folder + B, [("file", name, b)]))
        (data / "ZZ_Win.dat").write_bytes(make_edat(files))
        self.mod = self.root / "mod" if mod else None
        if self.mod:
            self.mod.mkdir()
        self.cache_dir = self.root / "cache"
        self._saving = threading.RLock()
        self.db = index_db()

    def _game(self):
        return self.game

    def _open(self):
        db = self.db

        def obj(address):
            r = db.execute("SELECT id FROM object WHERE address = ?", (address,)).fetchone()
            if r is None:
                raise KeyError(address)
            return r[0]
        return mock.Mock(db=db, close=lambda: None, of_class=lambda cls: [], _object=obj)

    def _mod_dir(self, kind="mod"):
        return self.mod

    def _edits(self):
        return None

    def _resolve(self, edits, address):
        return address, None

    def unit_voices(self, address, lang="base"):
        return {"moments": [{"id": "Move", "lines": [{"member": VOICE}]}]}


class Decoy(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        from test_music import patched   # the Music tab's songs in this made-up game: none of these sounds
        for p in patched() + [mock.patch("ruse_studio.decoy.map_list",
                                         return_value=[{"pack": "M04_Cotentin", "titles": {"us": ["9. OVERLORD"]}}])]:
            p.start()
            self.addCleanup(p.stop)
        self.calls = Calls(self.d.name)

    def volumes(self):
        f = self.calls.mod / sound.VOLUMES
        return tomllib.loads(f.read_text(encoding="utf-8"))["volume"] if f.is_file() else {}

    def test_kinds_missions_and_languages(self):
        got = self.calls.decoy("us")
        self.assertEqual({k["id"]: k["count"] for k in got["kinds"]},
                         {"weapons": 1, "engines": 2, "unit_voices": 1, "dialogue": 2})
        self.assertEqual(got["missions"], [{"id": "m04_cotentin", "name": "9. OVERLORD", "count": 2}])
        self.assertEqual(got["langs"], ["fr", "us"])
        self.assertTrue(got["mod"])

    def test_a_missions_lines_with_their_words(self):
        got = self.calls.decoy_list("dialogue", in_lang="fr", lang="us")
        self.assertEqual(got["total"], 1)
        self.assertEqual(got["rows"][0]["said"], "General, the first wave is on the beach.")  # in the Studio's language
        self.assertEqual(self.calls.decoy_list("dialogue", lang="fr")["rows"][0]["said"],
                         "Général, la première vague est sur la plage.")
        self.assertEqual(self.calls.decoy_list("dialogue", words="wave beach")["total"], 2)  # searched by what's said
        self.assertEqual(self.calls.decoy_list("dialogue", words="tank")["total"], 0)
        shot = self.calls.decoy_list("weapons")["rows"][0]
        self.assertEqual((shot["group_volume"], shot["grouped"], shot["volume"]), (70, True, 100))
        with self.assertRaises(DecoyError):
            self.calls.decoy_list("nope")

    def test_a_volume_saved_in_the_mod(self):
        self.calls.decoy_volume(SHOT, 150)
        self.assertEqual(self.volumes(), {sound.volume_key(SHOT): 150})
        self.assertEqual(sound.mod_volumes(self.calls.mod), {SHOT: 150})       # the build reads what the page wrote
        self.assertEqual(self.calls.decoy_list("weapons")["rows"][0]["volume"], 150)
        self.calls.decoy_volume(RUN, 0)
        self.assertEqual(len(self.volumes()), 2)
        self.calls.decoy_volume(SHOT, 100)                                       # 100: back to the game's, taken out
        self.assertEqual(self.volumes(), {sound.volume_key(RUN): 0})
        self.calls.decoy_volume(RUN, 100)
        self.assertFalse((self.calls.mod / sound.VOLUMES).exists())               # nothing left: no file
        for bad in (201, -5, True, "x"):
            with self.subTest(bad=bad), self.assertRaises(DecoyError):
                self.calls.decoy_volume(SHOT, bad)
        with self.assertRaises(DecoyError):
            self.calls.decoy_volume("gen_sound\\nope.ess", 50)
        self.assertEqual(self.calls.decoy("us")["kinds"][0]["changed"], 0)

    def test_a_whole_kind_at_once(self):
        got = self.calls.decoy_volume_all("dialogue", 80, in_lang="us")
        self.assertEqual(got["count"], 1)
        self.assertEqual(self.volumes(), {sound.volume_key(LINE["us"]): 80})
        self.calls.decoy_volume_all("engines", 120)
        self.assertEqual(len(self.volumes()), 3)
        self.assertEqual({k["id"]: k["changed"] for k in self.calls.decoy("us")["kinds"]}["engines"], 2)

    def test_a_units_own_sounds(self):
        self.assertEqual(self.calls.decoy_unit(UNIT), {"count": 3, "voices": 1, "engine": 2, "clips": 0, "own_clips": 0})
        rows = self.calls.decoy_unit_list(UNIT)["rows"]
        self.assertEqual([(r["member"], r["role"]) for r in rows],
                         [(RUN, "engine_run"), (IDLE, "engine_idle"), (VOICE, "voice")])
        self.calls.decoy_unit_volume(UNIT, 60)
        self.assertEqual(sorted(self.volumes()), sorted(sound.volume_key(m) for m in (RUN, IDLE, VOICE)))
        self.assertEqual(self.calls.decoy_unit("$/GFX/Everything/Descriptor_Unit_None")["count"], 1)  # voices only

    def test_without_a_mod(self):
        calls = Calls(str(Path(self.d.name) / "other"), mod=False)
        self.assertFalse(calls.decoy("us")["mod"])
        with self.assertRaises(DecoyError):
            calls.decoy_volume(SHOT, 50)

    def test_the_unit_s_words_in_every_language(self):
        # every word RUSE Decoy's page names (w.<key>), in each of the Studio's languages, with the same blanks
        import re
        from rusemod import schema
        from ruse_studio.api import _words
        js = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "decoy.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\bw\.([a-z_0-9]+)", js)) | set(re.findall(r'"((?:tip_)?decoy_[a-z_0-9]*[a-z0-9])"', js))
        words = _words()
        self.assertGreater(len(used), 60)
        self.assertEqual(sorted(k for k in used if k not in words), [])
        self.assertEqual(sorted((k, lang) for k in used for lang in schema.APP_LANGS if not words[k].get(lang)), [])
        for key in ("decoy_anim_for_unit", "decoy_anim_for_all", "decoy_anim_reset_own"):   # each control's tooltip
            self.assertIn("tip_" + key, used)

    def test_any_sound_played_and_replaced(self):
        got = self.calls.music_sound(SHOT)                       # the page reads the game's own sound
        self.assertEqual(got["kind"], "ess")
        self.assertEqual(self.calls._music_song(SHOT)["frames"], 2000)
        target = self.calls._music_file(SHOT)
        self.assertEqual(target, self.calls.mod / "files" / "replace" / (SHOT.replace(B, "/") + ".wav"))
        import base64
        wav = sound.write_wav([0, 100, -100] * 400, 1, 22050)
        self.assertEqual(self.calls.music_save(SHOT, base64.b64encode(wav).decode(), 0, 1)["saved"], str(target))
        self.assertEqual(sound.mod_sounds(self.calls.mod), {SHOT: target})   # the build puts it in (a flag-0 sound)
        self.assertTrue(self.calls.decoy_list("weapons")["rows"][0]["mine"])


class UnitCalls(DecoyCalls):
    """RUSE Decoy opened from a unit's page, on a made-up game: Descriptor_Unit_Squad's rifleman plays the run as
    t_course (an index in miniature); the run and the flee are clips of the same bones (test_mocap's small soldier)."""
    from test_mocap import RUN as _RUN
    FLEE = _RUN.replace("courselod0", "deroutelod0")

    def __init__(self, d):
        from test_mocap import SOLDIER, template
        from rusemod import baf
        self.mod = Path(d)
        self._saving = threading.RLock()
        self.clips = {self._RUN: baf.build(template()), self.FLEE: baf.build(template(loops=False))}
        self.skeleton = "|".join(n for n, _p, _w in SOLDIER)
        self.shown = []
        db = sqlite3.connect(":memory:")
        db.executescript(f"""
            CREATE TABLE object(id INTEGER PRIMARY KEY, class TEXT, shadow INTEGER, address TEXT, export TEXT);
            CREATE TABLE value(object INTEGER, path TEXT, num REAL, text TEXT);
            CREATE TABLE ref(src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
            INSERT INTO object VALUES (1, 'TInfanterieDescriptor', 0, '{SQUAD}', NULL),
                (2, 'TGfxDescriptorBiped', 0, '{SQUAD}:GfxDescriptorFusilier', NULL),
                (3, 'TGfxDescriptorAnimation', 0, '{SQUAD}:GfxDescriptorFusilier.ResourceAnimation[0].v', NULL);
            INSERT INTO ref VALUES (1, 'GfxDescriptorFusilier', 'object', 2, NULL),
                (2, 'ResourceAnimation[0].v', 'object', 3, NULL);
            INSERT INTO value VALUES (2, 'ResourceAnimation[0].k', NULL, 't_course'),
                (3, 'FileName', NULL, 'WW2\\Res3D\\Units\\Common\\Fusilier_courselod0.Ase2NdfBin');
        """)
        self.db = db

    def _mod_dir(self, kind="mod"):
        return self.mod

    def _open(self):
        return mock.Mock(db=self.db, close=lambda: None)

    def _edits(self):
        return None

    def _resolve(self, edits, address):
        return address, None

    def _decoy_clip_row(self, member):
        m = str(member).lower().replace("/", B)
        return {"member": m, "kind": "infantry", "name": m.rsplit(B, 1)[-1], "seconds": 1.0, "frames": 31,
                "bones": len(self.skeleton.split("|")), "names": ["t_course"], "units": ["a", "b", "c"],
                "skeleton": self.skeleton} if m in self.clips else None

    def _decoy_game_clips(self):
        return lambda m: self.clips.get(str(m).lower())

    def _decoy_preview_model(self, r):
        return "soldier"

    def _decoy_glb(self, model, raw):
        from rusemod import baf
        self.shown.append(raw)
        return {"url": "cache/x.glb", "model": model, "seconds": baf.parse(raw).duration}


SQUAD = "$/GFX/Everything/Descriptor_Unit_Squad"


class OnlyThisUnit(unittest.TestCase):
    """RUSE Decoy opened from a unit's page: a change for "Only this unit" goes to the unit's own copy of the clip
    (files/anim/units.toml, rusemod.anim), "Every unit that plays it" to the clip itself (files/anim/clips.toml)."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.calls = UnitCalls(self.d.name)
        self.mod = Path(self.d.name)

    def own(self):
        from rusemod import anim
        return anim.mod_unit_clips(self.mod).get("Descriptor_Unit_Squad", {}).get("clips", {})

    def test_only_this_unit_then_every_unit(self):
        from rusemod import anim
        run = UnitCalls._RUN
        got = self.calls.decoy_anim_set(run, speed=150, unit=SQUAD)
        self.assertEqual((got["speed"], got["own"]["speed"]), (100.0, 150.0))     # the clip's own: as the game's
        self.assertFalse((self.mod / anim.CLIPS).exists())
        self.assertEqual(self.own()[run]["speed"], 150.0)                          # the build reads what it wrote
        row = self.calls.decoy_unit_anims(SQUAD)["rows"][0]
        self.assertEqual((row["member"], row["role"], row["own"]["speed"], row["speed"]), (run, "t_course", 150.0, 100.0))
        self.calls.decoy_anim_set(run, speed=300)                                  # every unit: clips.toml
        self.assertEqual(anim.mod_clips(self.mod)[run]["speed"], 300.0)
        self.assertEqual(self.own()[run]["speed"], 150.0)                          # its own copy stays its own
        self.calls.decoy_anim_preview(run, unit=SQUAD)                            # as this unit plays it: 150%
        self.calls.decoy_anim_preview(run)                                         # as every unit plays it: 300%
        from rusemod import baf
        game = baf.parse(self.calls.clips[run]).duration
        self.assertEqual([round(baf.parse(r).duration, 4) for r in self.calls.shown],
                         [round(game / 1.5, 4), round(game / 3, 4)])

    def test_the_unit_page_counts_what_is_this_unit_s_only(self):
        """The unit page's Look and moves, its Animations row (the owner, 2026-11-11: "Yes, start working on this"):
        decoy_unit's own_clips counts the clips changed for this unit only, never a change every unit has."""
        from unittest import mock
        run = UnitCalls._RUN
        # (this made-up game has no sounds for the squad: decoy_unit's sound half answers none)
        with mock.patch.object(self.calls, "_decoy_unit_sounds", return_value=("", [])):
            self.assertEqual(self.calls.decoy_unit(SQUAD)["own_clips"], 0)
            self.calls.decoy_anim_set(run, speed=300)                              # every unit: not this unit's own
            self.assertEqual(self.calls.decoy_unit(SQUAD)["own_clips"], 0)
            self.calls.decoy_anim_set(run, speed=150, unit=SQUAD)                  # only this unit
            got = self.calls.decoy_unit(SQUAD)
        self.assertEqual((got["own_clips"], got["clips"]), (1, self.calls.decoy_unit_anims(SQUAD)["total"]))

    def test_the_copy_starts_as_what_the_unit_played(self):
        # like Copy this ammo: the change every unit has is the copy's start, then each goes its own way
        run = UnitCalls._RUN
        self.calls.decoy_anim_set(run, speed=200, use=UnitCalls.FLEE)
        got = self.calls.decoy_anim_set(run, bone="bip01 head", size=2.0, unit=SQUAD)
        self.assertEqual((got["own"]["speed"], got["own"]["from"], got["own"]["tweaks"]),
                         (200.0, UnitCalls.FLEE, {"bip01 head": {"size": 2.0, "turn": None}}))
        self.assertEqual(got["tweaks"], {})                                        # every unit's: no bone
        with self.assertRaises(DecoyError):                                        # a part, not a unit
            self.calls.decoy_anim_set(run, speed=50, unit=SQUAD + ":GfxDescriptorFusilier")
        with self.assertRaises(DecoyError):
            self.calls.decoy_anim_set(run, speed=5000, unit=SQUAD)

    def test_motion_capture_for_one_unit_and_back(self):
        from rusemod import anim
        from test_mocap import bvh_text
        run = UnitCalls._RUN
        self.calls.decoy_anim_set(run, speed=50)                                   # every unit: half speed
        mid = self.calls.decoy_mocap_open("walk.bvh", bvh_text([{}] * 241))["id"]
        used = self.calls.decoy_mocap_use(run, mid, 0.5, 1.0, True, None, "Me, CC0", SQUAD)
        self.assertTrue(used["own"]["mine"])
        self.assertEqual(used["own"]["speed"], 50.0)                               # (its changes still on top)
        own = self.mod / anim.OWN / "Descriptor_Unit_Squad" / anim.clip_key(run)
        self.assertTrue(own.is_file() and own.with_suffix(".toml").is_file())
        self.assertEqual(self.own()[run]["file"], own)                             # the build takes it
        self.assertFalse((self.mod / anim.REPLACE).exists())                       # every unit's: untouched
        back = self.calls.decoy_anim_reset(run, SQUAD)
        self.assertIsNone(back["own"])
        self.assertEqual(self.own(), {})
        self.assertFalse((self.mod / anim.OWN / "Descriptor_Unit_Squad").exists())  # its file, credit and folders
        self.assertFalse((self.mod / anim.UNITS).exists())
        self.assertEqual(anim.mod_clips(self.mod)[run]["speed"], 50.0)             # every unit's change kept
        self.calls.decoy_anim_reset(run)
        self.assertFalse((self.mod / anim.CLIPS).exists())

    def test_a_unit_deleted_takes_its_animations(self):
        from rusemod import anim
        from ruse_studio.edits import ModEdits
        self.calls.decoy_anim_set(UnitCalls._RUN, speed=150, unit=SQUAD)
        (self.mod / "src").mkdir()
        edits = ModEdits(self.mod)
        edits.remove_unit(SQUAD)
        self.assertFalse((self.mod / anim.UNITS).exists())


if __name__ == "__main__":
    unittest.main()
