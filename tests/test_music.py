"""The Studio's Music tab (ruse_studio.music, MusicCalls): the game's songs by where they play, a song for the page
to play, and the mod's own songs saved from the page's editor."""
import base64
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from rusemod import sound
from ruse_studio.music import MusicCalls, MusicError

M = "$/Misc/Musics/"
D = "gen_sound\\ww2\\sons\\atp_music\\"
SONGS = [  # (address, member)
    (M + "RUSE_outgame", D + "menu.ess"), (M + "RUSE_theme", D + "theme.ess"), (M + "RUSE_battle1", D + "b1.ess"),
    (M + "RUSE_BigVictory", D + "bigv.ess"), (M + "RUSE_Draw", D + "draw.ess"), (M + "RUSE_tunisie", D + "tun.ess"),
    (M + "RUSE_match_intro", D + "intro.ess"), (M + "RUSE_lose", D + "lose.ess")]
MAP1 = "genpython\\1000\\test\\map\\m02_tunisie\\scripting_chapter1\\effetmap.xyz"
MAP3 = "genpython\\1000\\test\\map\\m02_tunisie\\scripting_chapter3\\effetmap.xyz"
EUGEN = "genpython\\eugen.ipk!genpython\\1000\\codeia\\python\\eugen\\headup\\end_game_screens.xyz"
GOALS = "genpython\\eugensolo.ipk!genpython\\1000\\codeia\\python\\eugensolo\\leveldesignsolo\\objectif.xyz"
OTHER = "genpython\\eugen.ipk!genpython\\1000\\codeia\\python\\eugen\\leveldesign\\descriptorspecial.xyz"


def song(seconds: float = 0.5, channels: int = 2, rate: int = 8000) -> bytes:
    return sound.encode([((i * 37) % 2000) - 1000 for i in range(int(seconds * rate) * channels)], channels, rate)


class Calls(MusicCalls):
    """MusicCalls on a made-up game: ZZ_Win.dat with the songs, a mod folder, a cache folder."""

    def __init__(self, d: str, mod: bool = True):
        from fixtures import make_edat
        self.root = Path(d)
        self.game = self.root / "R.U.S.E"
        data = self.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        self.raw = {m: song() for _a, m in SONGS}
        self.raw[D + "intro.ess"] = song(1.0, 1, 11025)
        files = [("file", m[len(D):], b) for m, b in self.raw.items()]
        (data / "ZZ_Win.dat").write_bytes(make_edat([("dir", D, files)]))
        self.mod = self.root / "mod" if mod else None
        if self.mod:
            self.mod.mkdir()
        self.cache_dir = self.root / "cache"
        self._saving = threading.RLock()

    def _game(self):
        return self.game

    def _open(self):
        return mock.Mock(close=lambda: None)

    def _mod_dir(self, kind="mod"):
        return self.mod


def patched():
    songs = [{"address": a, "name": sound.song_name(a), "file": "x", "member": m} for a, m in SONGS]
    slots = {"menu": [M + "RUSE_outgame", M + "RUSE_theme"], "playlists": [[], [M + "RUSE_battle1"], []]}
    named = {(M + "RUSE_battle1").lower(): [MAP1], (M + "RUSE_tunisie").lower(): [MAP1, MAP3],
             (M + "RUSE_bigvictory").lower(): [EUGEN], (M + "RUSE_draw").lower(): [EUGEN, GOALS],
             (M + "RUSE_match_intro").lower(): [OTHER]}
    return [mock.patch.object(sound, "songs", return_value=songs), mock.patch.object(sound, "slots", return_value=slots),
            mock.patch.object(sound, "game_scripts", return_value={}),
            mock.patch.object(sound, "script_songs", return_value=named),
            mock.patch("ruse_studio.music.map_list", return_value=[
                {"pack": "M02_Tunisie", "titles": {"us": ["2. TAKING COMMAND!", "3. X", "4. Y", "5. Z"]}}])]


class Music(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        for p in patched():
            p.start()
            self.addCleanup(p.stop)
        self.calls = Calls(self.d.name)

    def test_songs_by_where_they_play(self):
        got = self.calls.music("us")
        self.assertTrue(got["mod"])
        groups = {g["id"]: [s["name"] for s in g["songs"]] for g in got["groups"]}
        self.assertEqual(groups, {"menu": ["Outgame"], "credits": ["Theme"], "playlist1": ["Battle 1"],
                                  "end": ["Big victory", "Draw"], "missions": ["Tunisie"], "other": ["Match intro"],
                                  "unused": ["Lose"]})
        rows = {s["name"]: s for g in got["groups"] for s in g["songs"]}
        self.assertEqual(rows["Draw"]["also"], ["goals"])
        self.assertEqual(rows["Battle 1"]["also"], ["missions"])
        self.assertEqual(rows["Tunisie"]["maps"], [{"map": "2. TAKING COMMAND! / 3. X / 4. Y …",
                                                    "parts": ["chapter1", "chapter3"]}])
        self.assertEqual((rows["Match intro"]["channels"], rows["Match intro"]["rate"], rows["Match intro"]["seconds"]),
                         (1, 11025, 1.0))
        self.assertFalse(rows["Outgame"]["mine"])
        self.assertEqual(list(self.calls.music("base")["groups"][-1]["songs"][0]), list(rows["Lose"]))  # code names too

    def test_the_game_song_for_the_page(self):
        got = self.calls.music_sound(D + "MENU.ess")  # any letter case
        self.assertEqual(got["kind"], "ess")
        self.assertTrue(got["url"].startswith("cache/sound/game/"))
        self.assertEqual((self.calls.root / got["url"]).read_bytes(), self.calls.raw[D + "menu.ess"])
        with self.assertRaises(MusicError):
            self.calls.music_sound("gen_sound\\..\\..\\secret.ess")
        with self.assertRaises(MusicError):
            self.calls.music_sound(D + "menu.ess", "mod")  # no song of the mod's yet

    def test_saved_in_parts_then_back_to_the_game(self):
        wav = sound.write_wav([((i * 91) % 3000) - 1500 for i in range(2 * 48000)], 2, 48000)
        parts = [wav[i:i + 40000] for i in range(0, len(wav), 40000)]
        for i, part in enumerate(parts):
            res = self.calls.music_save(D + "menu.ess", base64.b64encode(part).decode(), i, len(parts))
        target = self.calls.mod / "files" / "replace" / "gen_sound" / "ww2" / "sons" / "atp_music" / "menu.ess.wav"
        self.assertEqual(res, {"saved": str(target), "seconds": 1.0})
        self.assertEqual(target.read_bytes(), wav)
        self.assertEqual(sound.mod_sounds(self.calls.mod), {D + "menu.ess": target})  # what the build reads
        rows = {s["name"]: s for g in self.calls.music("us")["groups"] for s in g["songs"]}
        self.assertTrue(rows["Outgame"]["mine"])
        mine = self.calls.music_sound(D + "menu.ess", "mod")
        self.assertEqual(((self.calls.root / mine["url"]).read_bytes(), mine["kind"]), (wav, "wav"))
        self.assertEqual(self.calls.music_reset(D + "menu.ess"), {"saved": str(target)})
        self.assertFalse(target.exists())
        self.assertEqual(self.calls.music_reset(D + "menu.ess"), {"saved": None})

    def test_refused(self):
        good = base64.b64encode(sound.write_wav([0, 0] * 100, 2, 8000)).decode()
        with self.assertRaises(MusicError):
            self.calls.music_save(D + "nope.ess", good, 0, 1)  # not one of the game's songs
        with self.assertRaises(MusicError):
            self.calls.music_save(D + "menu.ess", "not base64!", 0, 1)
        with self.assertRaises(MusicError):
            self.calls.music_save(D + "menu.ess", good, 2, 1)  # out of order
        with self.assertRaises(MusicError):
            self.calls.music_save(D + "menu.ess", base64.b64encode(b"RIFF....").decode(), 0, 1)
        with self.assertRaises(MusicError):
            self.calls.music_save(D + "menu.ess", base64.b64encode(sound.write_wav([0] * 30, 3, 8000)).decode(), 0, 1)
        self.assertEqual(list((self.calls.mod).rglob("*.wav")), [])
        with tempfile.TemporaryDirectory() as d2:
            with self.assertRaises(MusicError):  # no mod picked: nowhere to save it
                Calls(d2, mod=False).music_save(D + "menu.ess", good, 0, 1)

    def test_the_page_can_call_them(self):
        from rusemod.webui import page_api
        from ruse_studio.api import StudioApi
        names = set(dir(type(page_api(StudioApi(home=self.d.name)))))
        self.assertLessEqual({"music", "music_sound", "music_save", "music_reset"}, names)


if __name__ == "__main__":
    unittest.main()
