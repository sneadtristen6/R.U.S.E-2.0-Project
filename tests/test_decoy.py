"""RUSE Decoy's calls (ruse_studio.decoy, DecoyCalls): every game sound by kind, a mission's lines with their words, a
sound's volume saved in the mod, a whole kind's at once, a unit's own sounds, and any sound replaced through the
Music tab's calls."""
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
        self.assertEqual(self.calls.decoy_unit(UNIT), {"count": 3, "voices": 1, "engine": 2, "clips": 0})
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


if __name__ == "__main__":
    unittest.main()
