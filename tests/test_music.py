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
        return mock.Mock(close=lambda: None, of_class=lambda cls: [])  # no voice lines in this made-up game

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

    def test_a_new_song_added_listed_and_taken_out(self):
        wav = sound.write_wav([((i * 13) % 2000) - 1000 for i in range(2 * 24000)], 2, 48000)
        res = self.calls.music_save("new:list2/Iwo Jima march!", base64.b64encode(wav).decode(), 0, 1)
        target = self.calls.mod / "files" / "music" / "list2" / "Iwo_Jima_march.wav"
        self.assertEqual(res, {"saved": str(target), "seconds": 0.5})
        self.assertEqual(target.read_bytes(), wav)
        got = {g["id"]: g["songs"] for g in self.calls.music("us")["groups"]}
        mine = got["playlist1"][-1]  # battle list 2, after the game's songs
        self.assertEqual((mine["member"], mine["name"], mine["new"], mine["mine"], mine["seconds"]),
                         ("new:list2/Iwo_Jima_march", "Iwo Jima march", True, True, 0.5))
        self.assertEqual([s["name"] for s in got["playlist1"][:-1]], ["Battle 1"])
        self.assertEqual(self.calls.music_sound("new:list2/Iwo_Jima_march", "mod")["kind"], "wav")
        self.assertEqual(list(sound.mod_new_songs(self.calls.mod, "mod")), ["gen_sound\\ww2\\sons\\atp_music\\mod_iwo_jima_march.ess"])
        self.calls.music_reset("new:list2/Iwo_Jima_march")
        self.assertFalse(target.exists())
        after = {g["id"]: g["songs"] for g in self.calls.music("us")["groups"]}
        self.assertEqual([s["name"] for s in after["playlist1"]], ["Battle 1"])  # out of the list again
        with self.assertRaises(MusicError):  # the game has three lists
            self.calls.music_save("new:list4/x", base64.b64encode(wav).decode(), 0, 1)
        with self.assertRaises(MusicError):  # a name with nothing left once made safe
            self.calls.music_save("new:list1/!!!", base64.b64encode(wav).decode(), 0, 1)

    def test_the_page_can_call_them(self):
        from rusemod.webui import page_api
        from ruse_studio.api import StudioApi
        names = set(dir(type(page_api(StudioApi(home=self.d.name)))))
        self.assertLessEqual({"music", "music_sound", "music_save", "music_reset"}, names)


V = "gen_sound\\ww2\\sons\\generated\\acknows\\"
AT = "$/GFX/Everything/AcknowManager:AcknowUnitContainer.Content["
U = "$/GFX/Everything/Descriptor_Unit_"
LINES = [  # (nation, kind, file stem); nation 0 and kind 0 are left out of the data, as the game's data does
    (0, 1, "EU_MediumTank_Move_1"), (0, 1, "EU_MediumTank_Move_2"), (0, 1, "EU_MediumTank_Spawn_1"),
    (1, 1, "Allemagne_MediumTank_Move_1"), (0, 0, "EU_LightTank_Move_1")]
UNITS = {U + "M4_Sherman": ("TUniteAuSolDescriptor", 0, 1), U + "M3_Lee": ("TUniteAuSolDescriptor", 0, 1),
         U + "Panzer_IV": ("TUniteAuSolDescriptor", 1, 1), U + "M3A1_Stuart": ("TUniteAuSolDescriptor", 0, 0),
         U + "Caserne_US": ("TBatimentDescriptor", 0, 0), U + "M3_Lee_cinematique": ("TUniteAuSolDescriptor", 0, 1)}
HIDDEN = {U + "M3_Lee_cinematique"}  # in no build menu (all ShowInMenu 0), as the game's cutscene copy


class VoiceIndex:
    """The few things unit_voices asks the game index."""

    def of_class(self, cls):
        if cls == "TAcknowUnitDescriptor":
            return [{"address": f"{AT}{i}]", "values": [(p, n, None) for p, n in (
                ("Nationalite", nation), ("TypeSpecific", kind), ("Version", int(stem[-1]))) if n]}
                for i, (nation, kind, stem) in enumerate(LINES)]
        if cls == "TSoundStream":
            return [{"address": f"{AT}{i}].FXName.TheSoundStream",
                     "values": [("FileName", None, f"WW2\\Sons\\Generated\\Acknows\\{stem}.ogg")]}
                    for i, (_n, _k, stem) in enumerate(LINES)]
        return [{"address": a, "values": [(p, n, None) for p, n in (
            ("Nationalite", nation), ("AcknowUnitType", kind), ("ShowInMenu[0]", 0.0 if a in HIDDEN else 1.0),
            ("ShowInMenu[1]", 0.0)) if n is not None and (n or p.startswith("Show"))]}
            for a, (c, nation, kind) in UNITS.items() if c == cls]

    def show(self, address):
        if address not in UNITS:
            raise KeyError(address)
        c, nation, kind = UNITS[address]
        return {"class": c, "values": [(p, n, None) for p, n in (("Nationalite", nation),
                                                                 ("AcknowUnitType", kind)) if n]}

    def close(self):
        pass


class VoiceCalls(Calls):
    def __init__(self, d):
        from fixtures import make_edat
        super().__init__(d)
        zz = self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        self.raw.update({V + stem.lower() + ".ess": song(0.3, 1, 44100) for _n, _k, stem in LINES})
        songs = [("file", m[len(D):], b) for m, b in self.raw.items() if m.startswith(D)]
        voices = [("file", m[len(V):], b) for m, b in self.raw.items() if m.startswith(V)]
        zz.write_bytes(make_edat([("dir", D, songs), ("dir", V, voices)]))

    def _open(self):
        return VoiceIndex()

    def _edits(self):
        return None

    @staticmethod
    def _resolve(edits, address):
        return address, None

    def _names(self, ix, addresses, lang):
        return {a: a.rsplit("_", 1)[-1].upper() for a in addresses}


class Voices(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        for p in patched():
            p.start()
            self.addCleanup(p.stop)
        self.calls = VoiceCalls(self.d.name)

    def test_a_units_lines_by_moment(self):
        got = self.calls.unit_voices(U + "M4_Sherman", "us")
        self.assertEqual([(m["id"], [x["name"] for x in m["lines"]]) for m in got["moments"]],
                         [("Move", ["Move 1", "Move 2"]), ("Spawn", ["Spawn 1"])])  # the US medium tanks' only
        self.assertEqual((got["shared"], got["hidden"]), (["LEE"], 1))  # the cutscene's copy: counted, not named
        self.assertFalse(got["copy"])
        line = got["moments"][0]["lines"][1]
        self.assertEqual((line["member"], line["channels"], line["rate"], line["seconds"], line["mine"]),
                         (V + "eu_mediumtank_move_2.ess", 1, 44100, 0.3, False))
        self.assertEqual([m["id"] for m in self.calls.unit_voices(U + "Panzer_IV")["moments"]], ["Move"])
        self.assertEqual(self.calls.unit_voices(U + "M3A1_Stuart")["moments"][0]["lines"][0]["member"],
                         V + "eu_lighttank_move_1.ess")  # kind 0, nation 0: both left out of the data
        self.assertEqual(self.calls.unit_voices(U + "Caserne_US")["moments"], [])  # a building: no voice
        self.assertEqual(self.calls.unit_voices(U + "Nope")["moments"], [])

    def test_a_line_saved_and_put_back(self):
        member = V + "eu_mediumtank_move_2.ess"
        self.assertEqual(self.calls.music_sound(member)["kind"], "ess")
        wav = sound.write_wav([((i * 7) % 900) - 450 for i in range(44100)], 1, 44100)
        res = self.calls.music_save(member, base64.b64encode(wav).decode(), 0, 1)
        self.assertEqual(res["seconds"], 1.0)
        self.assertEqual(sound.mod_sounds(self.calls.mod), {member: Path(res["saved"])})
        line = self.calls.unit_voices(U + "M4_Sherman")["moments"][0]["lines"][1]
        self.assertTrue(line["mine"])
        self.calls.music_reset(member)
        self.assertFalse(self.calls.unit_voices(U + "M4_Sherman")["moments"][0]["lines"][1]["mine"])
        with self.assertRaises(MusicError):  # not a song nor a voice line of the game's
            self.calls.music_save(V + "nope.ess", base64.b64encode(wav).decode(), 0, 1)


E = "gen_sound\\ww2\\sons\\sfx_env\\"
TUNISIE, SWAMP = "WW2\\Sons\\SFX_ENV\\MultiPiste_Ambiance_Tunisie.wav", "WW2\\Sons\\SFX_ENV\\MultiPiste_Ambiance_Swamp.wav"


def settings(file_name: str) -> bytes:
    """A map's settings file naming `file_name` as its background, as the game's do (Map_SoundConfig)."""
    import struct
    from fixtures import make_ndf, val
    return make_ndf(objects=[(0, [(0, val(0x09, struct.pack("<III", 0xBBBBBBBB, 1, 1)))]),
                             (1, [(1, val(0x1C, struct.pack("<I", 0)))])],
                    classes=["TSoundMapConfig", "TSoundStream"], props=[("AmbianceDecor_MultiPiste", 0), ("FileName", 1)],
                    strings=[file_name], exports={0: "MapConstante/MapInstance/Map_SoundConfig"}, compress=True)


class MapCalls(Calls):
    """Calls on a made-up game with two backgrounds: Tunisia's (played by the Tunisia campaign map and, named with
    DataDir:\\ in front, a base no menu lists) and the swamp's (Swamps'), and a map project beside the mod."""

    def __init__(self, d, new=None):
        from fixtures import make_edat
        super().__init__(d)
        data = self.game / "Data" / "PC" / "190852"
        self.bg = {"tunisie": song(0.2, 6, 48000), "swamp": song(0.3, 6, 48000)}
        songs = [("file", m[len(D):], b) for m, b in self.raw.items()]
        (data / "ZZ_Win.dat").write_bytes(make_edat([("dir", D, songs), ("dir", E, [
            ("file", f"multipiste_ambiance_{n}.ess", b) for n, b in self.bg.items()])]))
        (data / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\map\\", [
            ("dir", f"{folder}\\", [("file", "mapconstante.cpp.gladndfbin", settings(name))])
            for folder, name in (("m02_tunisie", TUNISIE), ("swamps", SWAMP), ("base", "DataDir:\\" + TUNISIE))])]))
        self.maps = self.root / "maps project"
        self.maps.mkdir()
        self.new = new or {}

    def _map_dir(self):
        return self.maps

    def _new_maps(self):
        return self.new

    def _game_pack(self, pack):
        copy = self.new.get(pack.lower())
        return copy[1].copy_of if copy else pack


class Backgrounds(unittest.TestCase):
    """A map's background sound (not tried in the game yet): its three layers heard, replaced and put back, or the
    map started from another of the game's backgrounds; saved where the build reads them (rusemod.sound.mod_ambience)."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        for p in patched():
            p.start()
            self.addCleanup(p.stop)
        self.calls = MapCalls(self.d.name)

    def test_the_maps_background_and_the_games_others(self):
        got = self.calls.map_sound("M02_Tunisie", "us")
        self.assertEqual((got["own"], got["use"], got["seconds"], got["mod"]), (TUNISIE, TUNISIE, 0.2, True))
        self.assertEqual([(c["file"], c["name"], c["maps"], c["seconds"], c["own"], c["use"]) for c in got["choices"]],
                         [(TUNISIE, "Tunisie", ["2. TAKING COMMAND!"], 0.2, True, True),  # its own first, by its menu name
                          (SWAMP, "Swamp", [], 0.3, False, False)])                       # (no menu lists Swamps here)
        self.assertEqual([(x["member"], x["mine"], x["seconds"]) for x in got["layers"]],
                         [(f"layer:M02_Tunisie/{n}", False, 0.2) for n in (1, 2, 3)])
        self.assertEqual({(x["channels"], x["rate"]) for x in got["layers"]}, {(2, 48000)})  # what the page makes
        heard = self.calls.music_sound("layer:M02_Tunisie/2")
        self.assertEqual((heard["kind"], heard["pair"]), ("ess", 2))  # the whole background: the page plays two of six
        self.assertEqual((self.calls.root / heard["url"]).read_bytes(), self.calls.bg["tunisie"])

    def test_a_layer_saved_then_put_back(self):
        wav = sound.write_wav([((i * 11) % 1600) - 800 for i in range(2 * 24000)], 2, 48000)
        res = self.calls.music_save("layer:M02_Tunisie/2", base64.b64encode(wav).decode(), 0, 1)
        target = self.calls.maps / "maps" / "M02_Tunisie" / "background_2.wav"
        self.assertEqual(res, {"saved": str(target), "seconds": 0.5})
        self.assertEqual(sound.mod_ambience(self.calls.maps, "m"),
                         {"M02_Tunisie": {"layers": {2: target}, "use": None, "mod": "m"}})  # what the build reads
        layers = self.calls.map_sound("M02_Tunisie", "us")["layers"]
        self.assertEqual([(x["mine"], x["seconds"]) for x in layers], [(False, 0.2), (True, 0.5), (False, 0.2)])
        self.assertEqual(self.calls.music_sound("layer:M02_Tunisie/2", "mod")["kind"], "wav")
        self.assertEqual(self.calls.music_reset("layer:M02_Tunisie/2"), {"saved": str(target)})
        self.assertFalse(target.exists())
        mono = base64.b64encode(sound.write_wav([0] * 4800, 1, 48000)).decode()
        for member, part in (("layer:M02_Tunisie/2", mono), ("layer:M02_Tunisie/4", base64.b64encode(wav).decode()),
                             ("layer:../x/1", base64.b64encode(wav).decode()), ("layer:Nowhere/1", mono)):
            with self.subTest(member=member), self.assertRaises(MusicError):
                self.calls.music_save(member, part, 0, 1)
        self.assertEqual(list(self.calls.maps.rglob("*.wav")), [])

    def test_started_from_another_background(self):
        got = self.calls.map_sound_use("M02_Tunisie", SWAMP.lower(), "us")  # any letter case: the game's own spelling
        toml = self.calls.maps / "maps" / "M02_Tunisie" / "sound.toml"
        self.assertEqual(sound.mod_ambience(self.calls.maps, "m")["M02_Tunisie"]["use"], SWAMP)
        self.assertEqual((got["own"], got["use"], got["seconds"]), (TUNISIE, SWAMP, 0.3))
        self.assertEqual([c["use"] for c in got["choices"]], [False, True])
        heard = self.calls.music_sound("layer:M02_Tunisie/1")  # a layer is heard in the background it starts from
        self.assertEqual((self.calls.root / heard["url"]).read_bytes(), self.calls.bg["swamp"])
        self.assertEqual(self.calls.map_sound_use("M02_Tunisie", None, "us")["use"], TUNISIE)
        self.assertFalse(toml.exists())
        self.calls.map_sound_use("M02_Tunisie", SWAMP, "us")
        self.calls.map_sound_use("M02_Tunisie", "DataDir:\\" + TUNISIE, "us")  # its own again, however it's spelt
        self.assertFalse(toml.exists())
        with self.assertRaises(MusicError):
            self.calls.map_sound_use("M02_Tunisie", "WW2\\Sons\\SFX_ENV\\Nope.wav", "us")

    def test_a_new_maps_from_the_map_it_copies(self):
        spec = mock.Mock(copy_of="Swamps")
        calls = MapCalls(Path(self.d.name, "new"), new={"blitzatdusk": ("BlitzAtDusk", spec)})
        got = calls.map_sound("blitzatdusk", "us")  # (as the map view names it)
        self.assertEqual((got["own"], got["seconds"]), (SWAMP, 0.3))
        wav = sound.write_wav([0, 0] * 4800, 2, 48000)
        res = calls.music_save("layer:blitzatdusk/3", base64.b64encode(wav).decode(), 0, 1)
        self.assertEqual(res["saved"], str(calls.maps / "maps" / "BlitzAtDusk" / "background_3.wav"))  # its own folder

    def test_the_page_can_call_them(self):
        from rusemod.webui import page_api
        from ruse_studio.api import StudioApi
        names = set(dir(type(page_api(StudioApi(home=self.d.name)))))
        self.assertLessEqual({"map_sound", "map_sound_use"}, names)


if __name__ == "__main__":
    unittest.main()
