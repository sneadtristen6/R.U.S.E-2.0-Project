"""rusemod.sound's per-sound volume (files/sound/volume.toml): read, made again louder or quieter, and put in by the
build with its description updated in every bank."""
import contextlib
import io
import os
import struct
import tempfile
import unittest
from array import array
from pathlib import Path
from unittest import mock

from rusemod import sound
from test_sound import snr, tone


def track_description(made: bytes, count: int) -> bytes:
    """A flag-0 description as the game's have one: 36 bytes of fields then 5 loudness bytes per 2048 samples."""
    h = sound.header(made)
    head = struct.pack("<HBBBBHIIIIIIHBB", 0x0106, 0, h["channels"], 0, 2 * h["channels"], h["rate"], h["frames"], 44,
                       len(made), h["loop_start"], h["loop_end"], count, 2048, 10, 5)
    return head + bytes((10 * i + k * 20) % 200 + 10 for i in range(count) for k in range(5))


class Reading(unittest.TestCase):
    def write(self, d: str, text: str) -> Path:
        f = Path(d) / sound.VOLUMES
        f.parent.mkdir(parents=True)
        f.write_text(text, encoding="utf-8")
        return Path(d)

    def test_volumes_from_the_mod_folder(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sound.mod_volumes(Path(d)), {})  # no file: nothing
            mod = self.write(d, '[volume]\n"gen_sound/ww2/sons/a.ess" = 150\n"GEN_SOUND/WW2/B.ess" = 100\n'
                                '"gen_sound/c.ess" = 0\n')
            # forward slashes or back, any case; 100 is the game's own and left out
            self.assertEqual(sound.mod_volumes(mod), {"gen_sound\\ww2\\sons\\a.ess": 150, "gen_sound\\c.ess": 0})

    def test_refused(self):
        for text, says in (('[volume]\n"a.ess" = 201\n', "from 0 to 200"), ('[volume]\n"a.ess" = -1\n', "from 0 to 200"),
                           ('[volume]\n"a.ess" = true\n', "from 0 to 200"), ('[volume]\n"a.wav" = 50\n', "ending .ess"),
                           ('[volume\n', sound.VOLUMES), ('volume = 3\n', "a table")):
            with tempfile.TemporaryDirectory() as d, self.subTest(text=text):
                with self.assertRaises(sound.SoundError) as got:
                    sound.mod_volumes(self.write(d, text))
                self.assertIn(says, str(got.exception))


class Louder(unittest.TestCase):
    def test_quieter_is_scaled(self):
        pcm = array("h", [0, 1000, -1000, 32767, -32768, 7])
        self.assertEqual(list(sound.louder(pcm, 50)), [0, 500, -500, 16384, -16384, 4])
        self.assertEqual(list(sound.louder(pcm, 0)), [0] * 6)

    def test_louder_is_limited_smoothly(self):
        pcm = array("h", [1000, -1000, 20000, -20000, 32767, -32768])
        out = sound.louder(pcm, 200)
        self.assertEqual(list(out[:2]), [2000, -2000])               # quiet parts: just doubled
        for v in out[2:]:                                             # loud parts: rounded off, never the rail
            self.assertLess(abs(v), sound._LIMIT_TOP + 1)
            self.assertGreater(abs(v), sound._LIMIT_FROM)
        self.assertLess(abs(out[2]), abs(out[4]))                    # and still in order (louder stays louder)


class Again(unittest.TestCase):
    def test_kind_length_and_loop_kept(self):
        for flag, channels in ((1, 1), (1, 2), (0, 1)):
            with self.subTest(flag=flag, channels=channels):
                made = bytearray(sound.encode(tone(3000, channels), channels, 22050, flag))
                made[12:20] = struct.pack(">II", 500, 2500)          # a loop of its own, as 37 game sounds have
                made = bytes(made)
                for pct in (0, 50, 150, 200):
                    new = sound.with_volume(made, pct)
                    h0, h = sound.header(made), sound.header(new)
                    self.assertEqual({k: h[k] for k in h if k != "codec"}, {k: h0[k] for k in h0 if k != "codec"})
                    self.assertEqual(sound.header(new)["loop_start"], 500)

    def test_level_follows_the_percent(self):
        made = sound.encode(tone(4000, 1), 1, 22050)
        base, _ = sound.decode(made)
        half, _ = sound.decode(sound.with_volume(made, 50))
        self.assertGreater(snr([v * 0.5 for v in base], half), 25)    # half as loud, the same sound
        loud, _ = sound.decode(sound.with_volume(made, 150))
        self.assertGreater(sum(abs(v) for v in loud), 1.4 * sum(abs(v) for v in base))
        self.assertEqual(sum(1 for v in loud if abs(v) >= 32767), 0)  # nothing on the rail

    def test_kept_in_the_cache(self):
        made = sound.encode(tone(800, 1), 1, 22050)
        with tempfile.TemporaryDirectory() as d:
            one = sound.with_volume(made, 120, Path(d))
            self.assertEqual(len(list(Path(d).rglob("*.ess"))), 1)
            with mock.patch.object(sound, "encode", side_effect=AssertionError("made twice")):
                self.assertEqual(sound.with_volume(made, 120, Path(d)), one)

    def test_description(self):
        made = sound.encode(tone(5000, 1), 1, 22050, 0)
        desc = track_description(made, 3)
        new = sound.with_volume(made, 150)
        out = sound.volume_description(desc, new, 150)
        self.assertEqual(len(out), len(desc))
        self.assertEqual(struct.unpack_from("<I", out, 16)[0], len(new))   # the file's new size
        self.assertEqual(out[:16] + out[20:36], desc[:16] + desc[20:36])    # every other field as it was
        self.assertEqual(list(out[36:]), [min(255, round(b * 1.5)) for b in desc[36:]])  # the track scaled
        flat = sound.description(sound.encode(tone(500, 1), 1, 22050))     # flag 1: no track, just the size
        self.assertEqual(sound.volume_description(flat, b"x" * 77, 40)[20:], flat[20:])


class Track(unittest.TestCase):
    def test_windows_rising_and_louder_is_higher(self):
        pcm = tone(5000, 1)
        for rate, step in ((11025, 1024), (22050, 2048), (44100, 4096), (48000, 4096)):
            self.assertEqual(sound.track_step(rate), step)
        t = sound.loudness_track(pcm, 1, 22050)
        self.assertEqual(len(t), 5 * 3)                                   # ceil(5000 / 2048) windows of five
        for w in range(3):
            five = t[5 * w:5 * w + 5]
            self.assertEqual(list(five), sorted(five))                    # rising, as the game's are
            self.assertGreater(five[4], 0)
        louder = sound.loudness_track(array("h", [2 * v for v in pcm]), 1, 22050)
        self.assertGreater(sum(louder), 1.8 * sum(t))                     # it follows the level, in a straight line
        self.assertEqual(sound.loudness_track(array("h", bytes(2 * 3000)), 1, 22050), bytes(10))  # silence: zeros

    def test_description_like_the_games(self):
        game = sound.encode(tone(4096, 1, seed=3), 1, 22050, 0)
        desc = track_description(game, 2)
        mine = sound.encode(tone(9000, 2, 44100, seed=5), 2, 44100, 0)   # longer, stereo, another rate
        out = sound.description_like(desc, mine)
        h = sound.header(mine)
        count, step, b10, b5 = struct.unpack_from("<IHBB", out, 28)
        self.assertEqual((out[2], out[3], out[5], struct.unpack_from("<H", out, 6)[0]), (0, 2, 4, 44100))
        self.assertEqual(struct.unpack_from("<IIIII", out, 8),
                         (h["frames"], 44, len(mine), h["loop_start"], h["loop_end"]))
        self.assertEqual((count, step, b10, b5), (3, 4096, 10, 5))       # ceil(9000 / 4096)
        self.assertEqual(len(out), 36 + 5 * 3)


class InTheBuild(unittest.TestCase):
    def game(self, d: str):
        """A made-up game: a flag-0 gun shot (a track in its description) and a flag-1 voice, described in two banks."""
        from fixtures import make_edat
        from test_build import PACK
        shot = sound.encode(tone(4096, 1, seed=3), 1, 22050, 0)
        voice = sound.encode(tone(1500, 1, seed=4), 1, 22050)
        bank = make_edat([("dir", "gen_sound\\ww2\\sons\\", [
            ("file", "sfx_ruse\\shot.sformat", track_description(shot, 2)),
            ("file", "generated\\voice.sformat", sound.description(voice))])])
        zz = make_edat([("dir", "gen_sound\\", [
            ("dir", "pack\\", [("file", "gfxdescriptor.mpk", bank), ("file", "map\\m04_cotentindialogues.mpk", bank)]),
            ("dir", "ww2\\sons\\", [("file", "sfx_ruse\\shot.ess", shot), ("file", "generated\\voice.ess", voice)])])])
        game = Path(d, "R.U.S.E")
        data = game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        (data / "ZZ_Win.dat").write_bytes(zz)
        return game, zz, shot, voice

    def build(self, d, game, mod):
        from rusemod.cli import main
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(["--game", str(game), "build", str(mod), "--instance", str(Path(d, "copy"))])
        return code, out.getvalue()

    def test_ruse_build_plays_sounds_at_their_volume(self):
        from rusemod.edat import Edat
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, zz, shot, voice = self.game(d)
            mod = Path(d, "loud")
            (mod / "files" / "sound").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "loud"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / sound.VOLUMES).write_text('[volume]\n"gen_sound/ww2/sons/sfx_ruse/shot.ess" = 150\n'
                                             '"gen_sound/ww2/sons/generated/voice.ess" = 50\n', encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertIn("sound volumes: 2", said)
            copy = Edat(Path(d, "copy", "Data", "PC", "190852", "ZZ_Win.dat").read_bytes())
            new_shot = bytes(copy.read(copy.find("shot.ess")))
            new_voice = bytes(copy.read(copy.find("voice.ess")))
            self.assertEqual(new_shot, sound.with_volume(shot, 150))
            self.assertEqual(new_voice, sound.with_volume(voice, 50))
            for name in ("gfxdescriptor.mpk", "m04_cotentindialogues.mpk"):   # both banks, each description updated
                bank = Edat(bytes(copy.read(copy.find(name))))
                self.assertEqual(bytes(bank.read(bank.find("shot.sformat"))),
                                 sound.volume_description(track_description(shot, 2), new_shot, 150))
                self.assertEqual(bytes(bank.read(bank.find("voice.sformat"))),
                                 sound.volume_description(sound.description(voice), new_voice, 50))
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_Win.dat").read_bytes(), zz)  # install untouched

    def test_a_replaced_sound_gets_its_volume_too(self):
        from rusemod.edat import Edat
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, _zz, _shot, _voice = self.game(d)
            mod = Path(d, "loud")
            wav = mod / "files" / "replace" / "gen_sound" / "ww2" / "sons" / "generated" / "voice.ess.wav"
            wav.parent.mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "loud"\nversion = "1.0.0"\n', encoding="utf-8")
            wav.write_bytes(sound.write_wav(tone(1700, 1, seed=9), 1, 22050))
            (mod / sound.VOLUMES).parent.mkdir(parents=True)
            (mod / sound.VOLUMES).write_text('[volume]\n"gen_sound/ww2/sons/generated/voice.ess" = 50\n', encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            copy = Edat(Path(d, "copy", "Data", "PC", "190852", "ZZ_Win.dat").read_bytes())
            new = bytes(copy.read(copy.find("voice.ess")))
            mine = sound.encode(tone(1700, 1, seed=9), 1, 22050)
            self.assertEqual(new, sound.with_volume(mine, 50))     # the mod's own sound, at half
            self.assertEqual(sound.header(new)["frames"], 1700)

    def test_a_gun_shot_replaced_and_made_louder(self):
        from rusemod.edat import Edat
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, _zz, shot, _voice = self.game(d)
            mod = Path(d, "guns")
            wav = mod / "files" / "replace" / "gen_sound" / "ww2" / "sons" / "sfx_ruse" / "shot.ess.wav"
            wav.parent.mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "guns"\nversion = "1.0.0"\n', encoding="utf-8")
            wav.write_bytes(sound.write_wav(tone(6000, 1, seed=8), 1, 22050))
            (mod / sound.VOLUMES).parent.mkdir(parents=True)
            (mod / sound.VOLUMES).write_text('[volume]\n"gen_sound/ww2/sons/sfx_ruse/shot.ess" = 120\n', encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            copy = Edat(Path(d, "copy", "Data", "PC", "190852", "ZZ_Win.dat").read_bytes())
            new = bytes(copy.read(copy.find("shot.ess")))
            mine = sound.encode(tone(6000, 1, seed=8), 1, 22050, 0)          # the game's kind: flag 0
            self.assertEqual(new, sound.with_volume(mine, 120))
            for name in ("gfxdescriptor.mpk", "m04_cotentindialogues.mpk"):
                bank = Edat(bytes(copy.read(copy.find(name))))
                got = bytes(bank.read(bank.find("shot.sformat")))
                made = sound.description_like(track_description(shot, 2), mine)
                self.assertEqual(got, sound.volume_description(made, new, 120))
                self.assertEqual(struct.unpack_from("<I", got, 28)[0], 3)     # ceil(6000 / 2048) windows

    def test_a_sound_the_game_has_not(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, *_ = self.game(d)
            mod = Path(d, "loud")
            (mod / "files" / "sound").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "loud"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / sound.VOLUMES).write_text('[volume]\n"gen_sound/nope.ess" = 50\n', encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertNotEqual(code, 0)
            self.assertIn("the game has no sound gen_sound/nope.ess", said)


if __name__ == "__main__":
    unittest.main()
