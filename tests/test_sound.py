"""rusemod.sound: the game's sounds played and made, the songs and where they play, a mod's sounds in the build."""
import contextlib
import io
import math
import os
import random
import struct
import tempfile
import unittest
import zlib
from array import array
from pathlib import Path
from unittest import mock

from rusemod import sound


def tone(frames: int, channels: int, rate: int = 22050, seed: int = 1) -> list:
    """A chord with a little noise, a different one in each channel: something like music to write and read back."""
    rnd = random.Random(seed)
    out = []
    for i in range(frames):
        for c in range(channels):
            t = i / rate
            v = 9000 * math.sin(2 * math.pi * (220 + 110 * c) * t) + 4000 * math.sin(2 * math.pi * 1375 * t)
            out.append(max(-32768, min(32767, int(v + rnd.randint(-300, 300)))))
    return out


def snr(a, b) -> float:
    sig = sum(x * x for x in a)
    err = sum((x - y) ** 2 for x, y in zip(a, b))
    return float("inf") if err == 0 else 10 * math.log10(sig / err)


class Codec(unittest.TestCase):
    def check(self, channels: int, frames: int, rate: int = 22050):
        pcm = tone(frames, channels, rate)
        played = []
        made = sound.encode(pcm, channels, rate, recon=played)
        stats = sound.Stats()
        back, h = sound.decode(made, stats)
        self.assertEqual(list(back), played)  # the reader plays exactly what the writer meant
        self.assertEqual((h["channels"], h["rate"], h["frames"], h["flag"]), (channels, rate, frames, 1))
        self.assertEqual((h["loop_start"], h["loop_end"]), (0, frames))
        self.assertEqual(stats.breaks, 0)  # each part starts where the one before ended
        self.assertEqual(stats.overruns, 0)
        self.assertLess(max(stats.spare_bits), 8)
        self.assertGreater(snr(pcm, back), 30)
        return made

    def test_mono_stereo_six_and_a_part_part(self):
        self.check(1, 2 * 1024 + 300)
        self.check(2, 3 * 512 + 1, 48000)
        self.check(6, 170 + 7, 48000)

    def test_loud_edges_and_silence(self):
        pcm = [0] * 2000 + [32767 if (i // 40) % 2 else -32768 for i in range(3000)] + [0] * 500
        played = []
        made = sound.encode(pcm, 1, 22050, recon=played)
        self.assertEqual(list(sound.decode(made)[0]), played)
        self.assertGreater(snr(pcm, played), 30)

    def test_refused(self):
        with self.assertRaises(sound.SoundError):
            sound.encode([], 1, 22050)
        with self.assertRaises(sound.SoundError):
            sound.encode([0, 0, 0], 3, 22050)
        with self.assertRaises(sound.SoundError):
            sound.decode(b"RIFF" + bytes(40))

    def test_description(self):
        made = sound.encode(tone(1500, 2, 48000), 2, 48000)
        d = sound.description(made)
        self.assertEqual(len(d), 28)
        self.assertEqual(struct.unpack("<HBBBBHIIIII", d), (0x0106, 1, 2, 0, 4, 48000, 1500, 4, len(made), 0, 1500))
        other = bytearray(made)
        other[4] = 0  # the kind with a loudness track: not made yet
        with self.assertRaises(sound.SoundError):
            sound.description(bytes(other))


class Wav(unittest.TestCase):
    def test_round_trip(self):
        pcm = tone(100, 2)
        raw = sound.write_wav(pcm, 2, 22050)
        got, ch, rate = sound.read_wav(raw)
        self.assertEqual((list(got), ch, rate), (pcm, 2, 22050))

    def test_only_16_bit(self):
        import wave
        out = io.BytesIO()
        with wave.open(out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(1)
            w.setframerate(8000)
            w.writeframes(bytes(10))
        with self.assertRaises(sound.SoundError):
            sound.read_wav(out.getvalue())
        with self.assertRaises(sound.SoundError):
            sound.read_wav(b"not a wav")


class Songs(unittest.TestCase):
    def test_names_and_members(self):
        self.assertEqual(sound.member_of("WW2\\Sons\\ATP_Music\\Battle-1_Ref_1.ogg"),
                         "gen_sound\\ww2\\sons\\atp_music\\battle-1_ref_1.ess")
        self.assertEqual(sound.song_name("$/Misc/Musics/RUSE_battle1_ref"), "Battle 1 ref")
        self.assertEqual(sound.song_name("$/Misc/Musics/RUSE_BigVictory"), "Big victory")
        self.assertEqual(sound.song_name("$/Misc/Musics/RUSE_Intro_Challenges"), "Intro challenges")

    def test_songs_and_slots_from_the_index(self):
        class Ix:
            def of_class(self, cls):
                return [{"address": "$/Misc/Musics/RUSE_outgame", "values": [("FileName", None, "WW2\\Sons\\M.ogg")]},
                        {"address": "$/GFX/Everything/fire", "values": [("FileName", None, "WW2\\Sons\\f.wav")]}]

            def uses(self, address):
                return {sound.MENU_MUSIC: [("MusicDescriptors[0].v", "import", "$/Misc/Musics/RUSE_outgame")],
                        sound.PLAYLISTS: [("PlayLists[0]", "object", sound.PLAYLISTS + ":PlayLists[0]")],
                        sound.PLAYLISTS + ":PlayLists[0]": [("Musics[0]", "import", "$/Misc/Musics/RUSE_a"),
                                                            ("Musics[1]", "import", "$/Misc/Musics/RUSE_b")]}[address]

        ix = Ix()
        self.assertEqual(sound.songs(ix), [{"address": "$/Misc/Musics/RUSE_outgame", "name": "Outgame",
                                            "file": "WW2\\Sons\\M.ogg", "member": "gen_sound\\ww2\\sons\\m.ess"}])
        self.assertEqual(sound.slots(ix), {"menu": ["$/Misc/Musics/RUSE_outgame"],
                                           "playlists": [["$/Misc/Musics/RUSE_a", "$/Misc/Musics/RUSE_b"]]})

    def test_songs_named_by_scripts(self):
        def compiled(*names):
            body = b"".join(b"s" + struct.pack("<I", len(n)) + n for n in names)
            return b"XYZ0" + bytes(24) + zlib.compress(body)

        found = sound.script_songs({"a": compiled(b"$/MISC/Musics/RUSE_Draw", b"PlayMusic"),
                                    "b": compiled(b"$/Misc/Musics/RUSE_draw", b"$/Misc/Musics/RUSE_x")})
        self.assertEqual(found, {"$/misc/musics/ruse_draw": ["a", "b"], "$/misc/musics/ruse_x": ["b"]})


class InTheBuild(unittest.TestCase):
    def test_mod_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "files" / "replace" / "gen_sound" / "ww2"
            root.mkdir(parents=True)
            (root / "a.ess.wav").write_bytes(b"")
            (root / "notes.wav").write_bytes(b"")
            self.assertEqual(list(sound.mod_sounds(Path(d))), ["gen_sound\\ww2\\a.ess"])

    def game(self, d: str):
        """A made-up game whose ZZ_Win.dat holds one song and its description in two sound banks, and a third bank
        without it."""
        from fixtures import make_edat
        from test_build import PACK
        song = sound.encode(tone(800, 2, 48000), 2, 48000)
        desc = sound.description(song)
        bank = make_edat([("dir", "gen_sound\\ww2\\sons\\atp_music\\", [("file", "song.sformat", desc),
                                                                        ("file", "other.sformat", b"x" * 28)])])
        other = make_edat([("dir", "gen_sound\\ww2\\sons\\", [("file", "fire.sformat", b"y" * 28)])])
        zz = make_edat([("dir", "gen_sound\\", [
            ("dir", "pack\\", [("file", "gfxdescriptor.mpk", bank), ("file", "ps3buttonpack.mpk", bank),
                               ("file", "map\\alphaambient.mpk", other)]),
            ("dir", "ww2\\sons\\atp_music\\", [("file", "song.ess", song)])])])
        game = Path(d, "R.U.S.E")
        data = game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        (data / "ZZ_Win.dat").write_bytes(zz)
        return game, zz

    def test_ruse_build_puts_the_song_in(self):
        from rusemod.cli import main
        from rusemod.edat import Edat
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, zz = self.game(d)
            mod = Path(d, "music")
            wav = mod / "files" / "replace" / "gen_sound" / "ww2" / "sons" / "atp_music" / "song.ess.wav"
            wav.parent.mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "music"\nversion = "1.0.0"\n', encoding="utf-8")
            mine = tone(1300, 2, 44100, seed=7)
            wav.write_bytes(sound.write_wav(mine, 2, 44100))
            for run in range(2):  # the second build takes the song from the build cache
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = main(["--game", str(game), "build", str(mod), "--instance", str(Path(d, "copy"))])
                self.assertEqual(code, 0, out.getvalue())
                self.assertIn("sounds: 1", out.getvalue())
                copy = Edat(Path(d, "copy", "Data", "PC", "190852", "ZZ_Win.dat").read_bytes())
                new = bytes(copy.read(copy.find("song.ess")))
                back, h = sound.decode(new)
                self.assertEqual((h["channels"], h["rate"], h["frames"]), (2, 44100, 1300))
                self.assertGreater(snr(mine, back), 30)
                for name in ("gfxdescriptor.mpk", "ps3buttonpack.mpk"):  # its description in both banks that had one
                    bank = Edat(bytes(copy.read(copy.find(name))))
                    self.assertEqual(bytes(bank.read(bank.find("song.sformat"))), sound.description(new))
                    self.assertEqual(bytes(bank.read(bank.find("other.sformat"))), b"x" * 28)
                self.assertEqual(bytes(copy.read(copy.find("alphaambient.mpk"))),
                                 bytes(Edat(zz).read(Edat(zz).find("alphaambient.mpk"))))  # a bank without it: as it was
            self.assertEqual(len(list(Path(d, "home").rglob("*.ess"))), 1)  # made once, kept
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_Win.dat").read_bytes(), zz)  # the install untouched

    def test_ruse_build_adds_a_new_song_to_a_battle_list(self):
        """files/music/list2/<name>.wav: a new song file and its description in both music banks (the other banks
        as they were), a new TSoundStream naming it and battle list 2 holding it (not tried in the game yet)."""
        from fixtures import make_edat, make_ndf, val
        from rusemod.cli import main
        from rusemod.edat import Edat
        from rusemod.ndf import Ndf, local_ref, sub_values

        def ref(i, cls):
            return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

        def lst(*items):
            return val(0x11, struct.pack("<I", len(items)) + b"".join(items))

        battle = val(0x09, struct.pack("<II", 0xAAAAAAAA, 0))
        ndf = make_ndf(objects=[(0, [(0, lst(ref(1, 1), ref(2, 1), ref(3, 1)))]), (1, [(1, lst(battle))]),
                                (1, [(1, lst(battle))]), (1, [(1, lst(battle))]), (2, [(2, val(0x1C, struct.pack("<I", 0)))])],
                       classes=["TMusicInGameDescriptor", "TMusicInGamePlayListDescriptor", "TSoundStream"],
                       props=[("PlayLists", 0), ("Musics", 1), ("FileName", 2)], strings=["WW2\\Sons\\fire.wav"],
                       exports={0: "GFX/Everything/musicInGame"}, imports=["RUSE_battle1"], compress=True)
        units = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, zz = self.game(d)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(units)
            mod = Path(d, "music")
            wav = mod / "files" / "music" / "list2" / "My Song.wav"
            wav.parent.mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "music"\nversion = "1.0.0"\n', encoding="utf-8")
            mine = tone(900, 2, 48000, seed=3)
            wav.write_bytes(sound.write_wav(mine, 2, 48000))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["--game", str(game), "build", str(mod), "--instance", str(Path(d, "copy"))])
            self.assertEqual(code, 0, out.getvalue())
            self.assertIn("new song: Music_music_My_Song in battle list 2", out.getvalue())
            data = Path(d, "copy", "Data", "PC", "190852")
            copy = Edat((data / "ZZ_Win.dat").read_bytes())
            new = bytes(copy.read(copy.entry("gen_sound\\ww2\\sons\\atp_music\\music_my_song.ess")))
            back, h = sound.decode(new)
            self.assertEqual((h["channels"], h["rate"], h["frames"]), (2, 48000, 900))
            self.assertGreater(snr(mine, back), 30)
            for name in ("gfxdescriptor.mpk", "ps3buttonpack.mpk"):  # both banks that hold the game's songs
                bank = Edat(bytes(copy.read(copy.find(name))))
                self.assertEqual(bytes(bank.read(bank.entry("gen_sound\\ww2\\sons\\atp_music\\music_my_song.sformat"))),
                                 sound.description(new))
                was = Edat(bytes(Edat(zz).read(Edat(zz).find(name))))
                game_song = "gen_sound\\ww2\\sons\\atp_music\\song.sformat"
                self.assertEqual(bytes(bank.read(bank.entry(game_song))), bytes(was.read(was.entry(game_song))))
            self.assertEqual(bytes(copy.read(copy.find("alphaambient.mpk"))),
                             bytes(Edat(zz).read(Edat(zz).find("alphaambient.mpk"))))  # no songs there: as it was
            pack = Edat((data / "ZZ_GladPatchableWin.dat").read_bytes())
            nd = Ndf(bytes(pack.read(pack.find("everything.cpp.gladndfbin"))))
            new_obj = len(nd.objects) - 1
            self.assertEqual(nd.classes[nd.objects[new_obj].cls], "TSoundStream")
            file = nd.objects[new_obj].get(nd.prop_index("FileName"))
            self.assertEqual(file.tc, 0x1C)  # a path, as the game's own sound streams name their files
            self.assertEqual(nd.strings[struct.unpack("<I", file.payload)[0]],
                             "WW2\\Sons\\ATP_Music\\music_My_Song.ogg")
            lists = [local_ref(v) for v in sub_values(nd.objects[0].get(nd.prop_index("PlayLists")))]
            musics = [sub_values(nd.objects[i].get(nd.prop_index("Musics"))) for i in lists]
            self.assertEqual([len(m) for m in musics], [1, 2, 1])  # list 2 gets the new song after the game's
            self.assertEqual(local_ref(musics[1][1]), new_obj)
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_Win.dat").read_bytes(), zz)  # the install untouched

    def test_new_songs_from_the_mod_folder(self):
        with tempfile.TemporaryDirectory() as d:
            for rel in ("list1/Calm one.wav", "list3/Ruse!.wav", "list4/nope.wav", "list2/!!!.wav"):
                Path(d, "files", "music", rel).parent.mkdir(parents=True, exist_ok=True)
                Path(d, "files", "music", rel).write_bytes(b"")
            got = sound.mod_new_songs(Path(d), "my-mod")
            self.assertEqual(sorted((s["object"], s["index"], s["file"]) for _w, s in got.values()), [
                ("Music_my_mod_Calm_one", 0, "WW2\\Sons\\ATP_Music\\my-mod_Calm_one.ogg"),
                ("Music_my_mod_Ruse", 2, "WW2\\Sons\\ATP_Music\\my-mod_Ruse.ogg")])  # list4 and a nameless one: not
            self.assertIn("gen_sound\\ww2\\sons\\atp_music\\my-mod_calm_one.ess", got)

    def test_a_sound_the_game_has_not(self):
        from rusemod.cli import main
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, _zz = self.game(d)
            mod = Path(d, "music")
            wav = mod / "files" / "replace" / "gen_sound" / "ww2" / "nope.ess.wav"
            wav.parent.mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "music"\nversion = "1.0.0"\n', encoding="utf-8")
            wav.write_bytes(sound.write_wav(tone(10, 1), 1, 22050))
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                code = main(["--game", str(game), "build", str(mod), "--instance", str(Path(d, "copy"))])
            self.assertNotEqual(code, 0)
            self.assertIn("the game has no sound gen_sound\\ww2\\nope.ess", out.getvalue())


if __name__ == "__main__":
    unittest.main()
