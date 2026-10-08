"""The Music tab's calls (StudioApi's MusicCalls; rusemod.sound): the game's songs by where they play, each song's
sound for the page to play, and the current mod's own songs, saved from the page's editor as
files/replace/<the song's path in ZZ_Win.dat>.wav. The page makes the WAV (the window reads MP3, OGG, FLAC and WAV
itself, and cuts, fades and sets the volume): nothing to install. Tried in the game (2026-10-07): songs replaced
this way in the main menu and battle lists 1 and 2 play, a unit's replaced voice line too, and new songs added to
lists 1 and 2 (rusemod.sound). A map's background sound (its three layers, or another of the game's) is saved in the
map project, maps/<map>/background_<n>.wav and sound.toml: not tried in the game yet."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
import struct
import threading
import tomllib
import zlib
from pathlib import Path

from rusemod import sound
from rusemod.build import find_pack
from rusemod.edat import Edat
from rusemod.terrain import map_list

# where a song plays, in the order the tab shows them (a song shows under the first that fits, the rest as "also")
GROUPS = ("menu", "credits", "playlist0", "playlist1", "playlist2", "end", "goals", "missions", "other", "unused")
NEW = "new:"  # a mod's new song, "new:list2/My_song" (files/music/list2/My_song.wav, rusemod.sound.mod_new_songs)
VOICES_AT = "$/GFX/Everything/AcknowManager:AcknowUnitContainer.Content["  # the units' voice lines
UNITS_AT = "$/GFX/Everything/Descriptor_Unit_"
VOICE_CLASSES = ("TUniteAuSolDescriptor", "TInfanterieDescriptor", "TAvionDescriptor")  # what has AcknowUnitType
LAYER = "layer:"  # a map's background layer, "layer:<map>/<n>" (the map project's maps/<map>/background_<n>.wav)
UNITS_PACK = "ZZ_GladPatchableWin.dat"  # where each map's settings are (rusemod.sound.map_config_member)


class MusicError(Exception):
    pass


def _part(path: str) -> str:
    """A map script's folder without its "scripting" ("chapter1", "challenge"; "" for a map with one)."""
    parts = path.replace("/", "\\").split("\\")
    folder = parts[-2] if len(parts) >= 2 else ""
    return re.sub(r"^scripting_?", "", folder, flags=re.I)


def _map_of(path: str) -> str | None:
    """The map folder a map script is in (genpython\\<build>\\test\\map\\<map>\\scripting...\\effetmap.xyz)."""
    low = path.lower().replace("/", "\\")
    if "!" in low or "\\map\\" not in low:
        return None
    return path.replace("/", "\\").split("\\")[low.split("\\").index("map") + 1]


class MusicCalls:
    _music_lock = threading.Lock()

    # --- the game's songs, worked out once per game build ---
    def _music_game(self) -> tuple[Path, Path, str]:
        game = self._game()
        zz = find_pack(game, "ZZ_Win.dat") if game is not None else None
        if zz is None:
            # not a game rule: the game or one of its files isn't found
            raise MusicError("We couldn't find R.U.S.E., so there's no music to show.")
        st = zz.stat()
        return game, zz, f"{st.st_size}-{int(st.st_mtime)}"  # a new game build: its songs read again

    def _music_songs(self) -> dict:
        """{song member: song} for the game's songs (rusemod.sound.songs) with where each plays and its length."""
        game, zz, key = self._music_game()
        with self._music_lock:
            kept = getattr(self, "_music_kept", None)
            if kept is not None and kept[0] == key:
                return kept[1]
            ix = self._open()
            try:
                songs = sound.songs(ix)
                where = sound.slots(ix)
            finally:
                ix.close()
            named = sound.script_songs(sound.game_scripts(game))
            menu_keys = {a.lower(): k for a, k in sound.MENU_KEYS.items()}
            out = {}
            with Edat.open(str(zz)) as arc:
                for s in songs:
                    e = arc.entry(s["member"])
                    if e is None:  # not a game rule: the data names a song this game build hasn't got
                        continue
                    h = sound.header(bytes(arc.raw[arc.data_offset + e.offset:arc.data_offset + e.offset + 20]))
                    low = s["address"].lower()
                    groups, maps, game_scripts = [], [], []
                    for a in where["menu"]:
                        if a.lower() == low:
                            groups.append("credits" if menu_keys.get(low) == "credits" else "menu")
                    for i, lst in enumerate(where["playlists"][:3]):
                        if low in (a.lower() for a in lst):
                            groups.append(f"playlist{i}")
                    for path in named.get(low, []):
                        m = _map_of(path)
                        if m is not None:
                            maps.append((m, _part(path)))
                        else:
                            game_scripts.append(path.rsplit("\\", 1)[-1].lower())
                    if any(f.startswith("end_game_screens") for f in game_scripts):
                        groups.append("end")
                    if any(f.startswith("objectif") for f in game_scripts):
                        groups.append("goals")
                    if maps:
                        groups.append("missions")
                    if game_scripts and not {"end", "goals"} & set(groups):
                        groups.append("other")
                    out[s["member"]] = {**s, "groups": groups or ["unused"], "maps": sorted(set(maps)),
                                        "channels": h["channels"], "rate": h["rate"], "frames": h["frames"]}
            self._music_kept = (key, out)
            return out

    def _voice_table(self) -> dict:
        """The units' voice lines, once per game build: {"lines": [{member, nation, kind, moment, version}] in the
        data's order, "units": {(nation, kind): [unit address, ...]}}. A unit speaks the lines of its nation
        (Nationalite) and kind (AcknowUnitType = a line's TypeSpecific); a line's moment is the word in its file's
        name (EU_MediumTank_Move_1: Move), as the game names them."""
        _game, _zz, key = self._music_game()
        with self._music_lock:
            kept = getattr(self, "_voices_kept", None)
            if kept is not None and kept[0] == key:
                return kept[1]
            ix = self._open()
            try:
                found: dict = {}
                for o in ix.of_class("TAcknowUnitDescriptor"):
                    if o["address"].startswith(VOICES_AT):
                        v = {p: n for p, n, _t in o["values"]}
                        found[o["address"]] = {"nation": int(v.get("Nationalite") or 0),
                                               "kind": int(v.get("TypeSpecific") or 0),
                                               "version": int(v.get("Version") or 0)}
                lines = []
                for o in ix.of_class("TSoundStream"):
                    owner = o["address"].rsplit(".FXName.", 1)[0]
                    file = next((t for p, _n, t in o["values"] if p == "FileName" and t), None)
                    if owner in found and file:
                        stem = file.replace("/", "\\").rsplit("\\", 1)[-1].rsplit(".", 1)[0]
                        bits = stem.rsplit("_", 2)
                        lines.append({**found[owner], "member": sound.member_of(file),
                                      "moment": bits[1] if len(bits) == 3 else stem})
                units: dict = {}
                for cls in VOICE_CLASSES:
                    for o in ix.of_class(cls):
                        a = o["address"]
                        if a.startswith(UNITS_AT) and ":" not in a:
                            v = {p: n for p, n, _t in o["values"]}
                            shown = any(n for p, n in v.items() if p.startswith("ShowInMenu") and n)  # a menu shows it
                            units.setdefault((int(v.get("Nationalite") or 0), int(v.get("AcknowUnitType") or 0)),
                                             []).append((a, shown))
            finally:
                ix.close()
            table = {"lines": lines, "units": units}
            self._voices_kept = (key, table)
            return table

    def _new_song(self, member: str) -> dict:
        """A mod's new song, "new:<list>/<name>" (files/music/<list>/<name>.wav; the name made safe), as a song."""
        list_name, _, name = member[len(NEW):].partition("/")
        name = sound.safe_name(name)
        if list_name not in sound.LISTS:
            # not a game rule: the page named a list there isn't (the game has three)
            raise MusicError(f"{list_name} isn't one of the battle lists")
        if not name:
            raise MusicError("Give the song a name (letters and digits).")
        member = f"{NEW}{list_name}/{name}"
        file = self._music_file(member)
        frames = rate = 0
        if file is not None and file.is_file():
            try:
                pcm, channels, rate = sound.read_wav(file.read_bytes())
                frames = len(pcm) // channels
            except sound.SoundError:
                pass
        # made like the game's songs: two channels at 48,000 a second
        return {"member": member, "name": name.replace("_", " "), "list": list_name, "channels": 2, "rate": 48000,
                "frames": frames, "seconds": round(frames / rate, 1) if rate else 0, "new": True}

    def _new_songs(self) -> dict:
        """The current mod's new songs by list: {"list1": [song, ...], ...}."""
        mod = self._mod_dir()
        out: dict = {x: [] for x in sound.LISTS}
        if mod is None:
            return out
        for list_name in sound.LISTS:
            folder = mod / sound.NEW_MUSIC / list_name
            for f in sorted(folder.glob("*.wav")) if folder.is_dir() else []:
                if sound.safe_name(f.stem) == f.stem:
                    out[list_name].append(self._new_song(f"{NEW}{list_name}/{f.stem}"))
        return out

    def _music_song(self, member: str) -> dict:
        """One of the game's songs or voice lines, or a layer of a map's background, with its format: what the page
        may play, replace or put back."""
        if str(member).startswith(NEW):
            return self._new_song(str(member))
        if str(member).startswith(LAYER):
            return self._layer(str(member))
        member = str(member).lower()
        song = self._music_songs().get(member)
        if song is not None:
            return song
        line = next((x for x in self._voice_table()["lines"] if x["member"] == member), None)
        if line is None:
            # not a game rule: the page asked for a song the game hasn't got
            raise MusicError(f"{member} isn't one of the game's songs")
        _game, zz, _key = self._music_game()
        with Edat.open(str(zz)) as arc:
            e = arc.entry(member)
            if e is None:  # not a game rule: the data names a sound this game build hasn't got
                raise MusicError(f"{member} isn't in this game build")
            h = sound.header(bytes(arc.raw[arc.data_offset + e.offset:arc.data_offset + e.offset + 20]))
        return {**line, "name": f"{line['moment']} {line['version']}", "channels": h["channels"], "rate": h["rate"],
                "frames": h["frames"]}

    def _music_file(self, member: str) -> Path | None:
        """The current mod's own song for `member` (files/replace/<member>.wav; a new song's files/music/<list>/
        <name>.wav; a map's background layer the map project's maps/<map>/background_<n>.wav), whether made yet or
        not."""
        if member.startswith(LAYER):
            folder = self._map_dir()
            pack, n = self._map_layer(member)
            return folder / "maps" / self._map_folder(pack) / f"background_{n}.wav" if folder is not None else None
        mod = self._mod_dir()
        if mod is None:
            return None
        if member.startswith(NEW):
            list_name, _, name = member[len(NEW):].partition("/")
            return mod / sound.NEW_MUSIC / list_name / (name + ".wav")
        return mod / sound.REPLACE / (member.replace("\\", "/") + ".wav")

    # --- what the page calls ---
    def music(self, lang: str = "base") -> dict:
        """The Music tab: the game's songs by where they play (GROUPS order), each with its name, length, format, the
        maps whose missions play it ({map: its names in the game's menus in `lang`, parts: the script folders,
        "chapter1"}), and whether the current mod has its own; the mod's new songs ("new": True, member
        "new:<list>/<name>") at the end of their battle list."""
        game, _zz, _key = self._music_game()
        songs = self._music_songs()
        try:
            titles = {m["pack"].lower(): m["titles"] for m in map_list(game)} if lang != "base" else {}
        except (OSError, ValueError, KeyError):  # no map list (a made-up game): each map by its folder's name
            titles = {}
        groups = {g: [] for g in GROUPS}
        for member, s in songs.items():
            mine = self._music_file(member)
            by_map: dict = {}
            for m, part in s["maps"]:
                by_map.setdefault(m, []).append(part)
            maps = []
            for m, parts in by_map.items():
                # the names the menus give the map (a campaign map has one per chapter: which chapter a script is
                # for isn't read yet, so up to three of them, as the AI tab shows them) and the script folders
                t = titles.get(m.lower(), {})
                names = t.get(lang) or t.get("us") or [m]
                maps.append({"map": " / ".join(names[:3]) + (" …" if len(names) > 3 else ""), "parts": parts})
            groups[s["groups"][0]].append({
                "member": member, "name": s["name"], "seconds": round(s["frames"] / s["rate"], 1),
                "channels": s["channels"], "rate": s["rate"], "also": s["groups"][1:], "maps": maps,
                "mine": mine is not None and mine.is_file()})
        new = self._new_songs()
        for i, list_name in enumerate(sound.LISTS):  # the mod's new songs, at the end of their list
            for s in new[list_name]:
                groups[f"playlist{i}"].append({**s, "also": [], "maps": [], "mine": True})
        return {"groups": [{"id": g, "songs": groups[g]} for g in GROUPS if groups[g]],
                "mod": self._mod_dir() is not None}

    def music_sound(self, member: str, which: str = "game") -> dict:
        """A song's sound for the page to play, at an address of the window's own: "game" (the game's song, in the
        game's own kind of file: the page reads it) or "mod" (the current mod's WAV)."""
        song = self._music_song(member)
        if which == "mod":
            mine = self._music_file(song["member"])
            if mine is None or not mine.is_file():
                raise MusicError("This mod has no song of its own here.")
            raw = mine.read_bytes()
            name = hashlib.sha256(raw).hexdigest()[:24] + ".wav"
            out = self.cache_dir / "sound" / "mod" / name
            if not out.is_file():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(raw)
            return {"url": f"cache/sound/mod/{name}", "kind": "wav"}
        _game, zz, key = self._music_game()
        source = song.get("source", song["member"])  # a layer's: the whole background (`pair`: its two channels)
        name = hashlib.sha1(source.encode()).hexdigest()[:24] + ".ess"
        out = self.cache_dir / "sound" / "game" / key / name
        if not out.is_file():
            with Edat.open(str(zz)) as arc:
                raw = bytes(arc.read(arc.entry(source)))
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".part")
            tmp.write_bytes(raw)
            tmp.replace(out)
        return {"url": f"cache/sound/game/{key}/{name}", "kind": "ess", "channels": song["channels"],
                "rate": song["rate"], "frames": song["frames"], "pair": song.get("pair")}

    def music_save(self, member: str, part: str, index: int, count: int) -> dict:
        """The page's finished song (a 16-bit WAV, in `count` base64 parts sent in order): saved in the current mod
        once the last part is in, as files/replace/<the song's path>.wav."""
        song = self._music_song(member)
        target = self._music_file(song["member"])
        if target is None:
            raise MusicError("Pick or make a map project first: a map's sounds are saved in it." if song.get("pair")
                             else "Pick or make a mod first: songs are saved in a mod.")
        if not (isinstance(index, int) and isinstance(count, int) and 0 <= index < count):
            raise MusicError("the song's parts came out of order: try Use this again")
        try:
            data = base64.b64decode(part, validate=True)
        except (binascii.Error, ValueError, TypeError):
            raise MusicError("the song's parts came damaged: try Use this again") from None
        up = self.cache_dir / "sound" / "upload" / (hashlib.sha1(song["member"].encode()).hexdigest()[:24] + ".wav")
        up.parent.mkdir(parents=True, exist_ok=True)
        with up.open("wb" if index == 0 else "ab") as f:
            f.write(data)
        if index < count - 1:
            return {"part": index}
        raw = up.read_bytes()
        try:
            pcm, channels, rate = sound.read_wav(raw)
        except sound.SoundError as exc:
            raise MusicError(f"the song can't be read back ({exc}): try Use this again") from None
        if channels not in sound.FRAMES_PER_BLOCK or not 1 <= rate <= 0xFFFF or len(pcm) < channels:
            # not a game rule: what rusemod.sound writes (the game's own channel counts, a rate its file can hold)
            raise MusicError(f"a song of {channels} channel(s) at {rate} a second can't be made")
        if song.get("pair") and (channels, rate) != (2, 48000):
            # not a game rule: rusemod.sound puts a layer in beside the map's own, which are stereo at 48,000 a second
            raise MusicError(f"a background's layer is stereo at 48,000 a second, not {channels} channel(s) at {rate}")
        with self._saving:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".part")
            tmp.write_bytes(raw)
            tmp.replace(target)
        up.unlink(missing_ok=True)
        return {"saved": str(target), "seconds": round(len(pcm) / channels / rate, 1)}

    def unit_voices(self, address: str, lang: str = "base") -> dict:
        """A unit's voice lines for its page: by moment (the game's own word for it: Move, Attack, Spawn...), each
        line with its length, format and whether the current mod has its own; `shared`: the other units that speak the
        same lines and that a build menu shows (in `lang`), `hidden`: how many others share them that no build menu
        shows (a cutscene's copy, placeholders: missions may still use them), `copy`: True for a modder's copied unit
        (it speaks its source's lines). Empty `moments` for what has no voice (buildings)."""
        try:
            edits = self._edits()
        except Exception:  # a mod file that can't be read: the game's own unit is still shown
            edits = None
        real, new = self._resolve(edits, address)
        real = real.split(":", 1)[0]
        ix = self._open()
        try:
            try:
                u = ix.show(real)
            except KeyError:
                return {"moments": [], "shared": [], "copy": new is not None}
            if u["class"] not in VOICE_CLASSES:
                return {"moments": [], "shared": [], "copy": new is not None}
            v = {p: n for p, n, _t in u["values"]}
            key = (int(v.get("Nationalite") or 0), int(v.get("AcknowUnitType") or 0))
            table = self._voice_table()
            others = [a for a, shown in table["units"].get(key, []) if a != real and shown]
            hidden = sum(1 for a, shown in table["units"].get(key, []) if a != real and not shown)
            names = self._names(ix, others, lang) if others else {}
        finally:
            ix.close()
        _game, zz, _key = self._music_game()
        moments: dict = {}
        with Edat.open(str(zz)) as arc:
            for line in table["lines"]:
                if (line["nation"], line["kind"]) != key:
                    continue
                e = arc.entry(line["member"])
                if e is None:  # not a game rule: the data names a sound this game build hasn't got
                    continue
                h = sound.header(bytes(arc.raw[arc.data_offset + e.offset:arc.data_offset + e.offset + 20]))
                mine = self._music_file(line["member"])
                moments.setdefault(line["moment"], []).append({
                    "member": line["member"], "name": f"{line['moment']} {line['version']}", "version": line["version"],
                    "seconds": round(h["frames"] / h["rate"], 1), "channels": h["channels"], "rate": h["rate"],
                    "mine": mine is not None and mine.is_file(), "also": [], "maps": []})
        return {"moments": [{"id": m, "lines": lines} for m, lines in moments.items()],
                "shared": sorted({names.get(a, a.rsplit("/", 1)[-1]) for a in others}), "hidden": hidden,
                "copy": new is not None}

    def music_reset(self, member: str) -> dict:
        """Take the current mod's own song out: the game's plays again."""
        song = self._music_song(member)
        target = self._music_file(song["member"])
        if target is None or not target.is_file():
            return {"saved": None}
        with self._saving:
            target.unlink()
        return {"saved": str(target)}

    # --- a map's background sound (rusemod.sound; not tried in the game yet): one sound of three stereo layers that
    # the map's settings name; the map project's maps/<map>/background_<n>.wav replace layers, and its sound.toml
    # (background =) starts the map from another of the game's backgrounds ---
    def _backgrounds(self) -> dict:
        """{a map's settings folder, lower case: the background its settings name}, read once per game build."""
        game, _zz, key = self._music_game()
        units = find_pack(game, UNITS_PACK)
        if units is None:
            # not a game rule: the game or one of its files isn't found
            raise MusicError(f"{UNITS_PACK} isn't in this game, so the maps' background sounds can't be read")
        st = units.stat()
        key = f"{key}/{st.st_size}-{int(st.st_mtime)}"
        with self._music_lock:
            kept = getattr(self, "_backgrounds_kept", None)
            if kept is not None and kept[0] == key:
                return kept[1]
            out = {}
            with Edat.open(str(units)) as arc:
                for e in arc.entries:
                    parts = e.path.lower().split("\\")
                    if parts[:3] != ["genglad", "patchable", "map"] or parts[4:] != ["mapconstante.cpp.gladndfbin"]:
                        continue
                    try:
                        name = sound.background_of(bytes(arc.read(e)))
                    except (ValueError, KeyError, IndexError, struct.error, zlib.error):  # a settings file not read
                        name = None
                    if name:
                        out[parts[3]] = name
            self._backgrounds_kept = (key, out)
            return out

    def _map_layer(self, member: str) -> tuple[str, int]:
        """(the map, the layer's number) of "layer:<map>/<n>"."""
        q = re.fullmatch(r"layer:([A-Za-z0-9_]+)/([0-9])", str(member))
        if not q or int(q.group(2)) not in sound.LAYERS:
            # not a game rule: the page named a layer there isn't (the game's backgrounds hold three)
            raise MusicError(f"{member} isn't one of a map's background layers")
        return q.group(1), int(q.group(2))

    def _map_folder(self, pack: str) -> str:
        """The map's folder in the map project: a new map's own (as map.toml's folder spells it), else the pack."""
        copy = self._new_maps().get(str(pack).lower())
        return copy[0] if copy else str(pack)

    def _map_use(self, pack: str) -> str | None:
        """The other background the map project's maps/<map>/sound.toml starts the map from, or None."""
        folder = self._map_dir()
        path = folder / "maps" / self._map_folder(pack) / "sound.toml" if folder is not None else None
        if path is None or not path.is_file():
            return None
        try:
            use = tomllib.loads(path.read_text(encoding="utf-8")).get("background")
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):  # (a broken file is the mod check's to say)
            return None
        return use if isinstance(use, str) and use else None

    def _map_background(self, pack: str) -> tuple[str, str]:
        """(the background the game gives the map (a new map: the map it copies), the one its layers start from)."""
        own = self._backgrounds().get(self._game_pack(pack).lower())
        if own is None:
            # not a game rule: the map's settings name no background sound this game has
            raise MusicError(f"{pack} has no background sound in this game")
        return own, self._map_use(pack) or own

    def _layer(self, member: str) -> dict:
        """A layer of a map's background as a song: two of the background's six channels (`pair`), made like the
        game's (stereo at 48,000 a second); `source`: the background it's heard in now."""
        pack, n = self._map_layer(member)
        _own, use = self._map_background(pack)
        source = sound.ambience_member(use)
        _game, zz, _key = self._music_game()
        with Edat.open(str(zz)) as arc:
            e = arc.entry(source)
            if e is None:  # not a game rule: the data names a sound this game build hasn't got
                raise MusicError(f"{use} isn't in this game build")
            h = sound.header(bytes(arc.raw[arc.data_offset + e.offset:arc.data_offset + e.offset + 20]))
        return {"member": f"{LAYER}{pack}/{n}", "name": str(n), "map": pack, "pair": n, "source": source,
                "channels": 2, "rate": 48000, "frames": h["frames"], "seconds": round(h["frames"] / h["rate"], 1)}

    def map_sound(self, pack: str, lang: str = "base") -> dict:
        """A map's background sound, as its window shows it: {"own": the background the game gives it, "use": the one
        it starts from now (sound.toml's, else its own), "choices": the game's backgrounds, the map's own first, each
        {"file", "name", "maps": the maps that play it by their names in the menus (in `lang`), "seconds", "own"},
        "layers": [{"member", "n", "mine", "seconds", "channels", "rate"}: each made like the game's, stereo at 48,000
        a second], "seconds": how long its background is, "mod": whether a map
        project is open}. A new map's: those of the map it copies, with its own changes."""
        own, use = self._map_background(pack)
        game, zz, _key = self._music_game()
        try:
            titles = {m["pack"].lower(): m["titles"] for m in map_list(game)}
        except (OSError, ValueError, KeyError):  # no map list (a made-up game): the backgrounds by their names
            titles = {}
        found: dict = {}
        for folder, file in sorted(self._backgrounds().items()):
            key = sound.ambience_member(file)
            c = found.setdefault(key, {"file": file, "maps": []})
            if ":" in c["file"] and ":" not in file:  # the name most maps give it (some write DataDir:\ in front)
                c["file"] = file
            t = titles.get(folder)  # (the game's test maps and bases: no menu lists them)
            names = (t.get(lang) or t.get("us") or []) if t else []
            if names and names[0] not in c["maps"]:
                c["maps"].append(names[0])
        choices = []
        with Edat.open(str(zz)) as arc:
            for key, c in found.items():
                e = arc.entry(key)
                if e is None:  # not a game rule: the data names a sound this game build hasn't got
                    continue
                h = sound.header(bytes(arc.raw[arc.data_offset + e.offset:arc.data_offset + e.offset + 20]))
                stem = re.sub(r"^multipiste_ambiance_", "", key.rsplit("\\", 1)[-1].rsplit(".", 1)[0], flags=re.I)
                choices.append({**c, "name": stem.replace("_", " ").title(), "seconds": round(h["frames"] / h["rate"], 1),
                                "own": key == sound.ambience_member(own), "use": key == sound.ambience_member(use)})
        choices.sort(key=lambda c: (not c["own"], (c["maps"] or [c["name"]])[0].lower()))
        at = next((c for c in choices if c["use"]), None)
        layers = []
        for n in sound.LAYERS:
            member = f"{LAYER}{pack}/{n}"
            file = self._music_file(member)
            seconds = None
            if file is not None and file.is_file():
                try:
                    pcm, channels, rate = sound.read_wav(file.read_bytes())
                    seconds = round(len(pcm) / channels / rate, 1)
                except sound.SoundError:
                    seconds = 0
            layers.append({"member": member, "n": n, "mine": seconds is not None, "channels": 2, "rate": 48000,
                           "seconds": seconds if seconds is not None else (at["seconds"] if at else 0)})
        return {"map": pack, "own": own, "use": use, "choices": choices, "layers": layers,
                "seconds": at["seconds"] if at else 0, "mod": self._map_dir() is not None}

    def map_sound_use(self, pack: str, file: str | None, lang: str = "base") -> dict:
        """Start the map's background from another of the game's (`file`, a name map_sound's choices give), or from
        its own again (None, or its own): the map project's maps/<map>/sound.toml. Returns map_sound()."""
        folder = self._map_dir()
        if folder is None:
            raise MusicError("Pick or make a map project first: a map's sounds are saved in it.")
        own, _use = self._map_background(pack)
        if file:
            known = {sound.ambience_member(f): f for f in self._backgrounds().values()}
            if sound.ambience_member(file) not in known:
                # not a game rule: the page named a background none of the game's maps plays
                raise MusicError(f"{file} isn't one of the game's background sounds")
            file = known[sound.ambience_member(file)]
        path = folder / "maps" / self._map_folder(pack) / "sound.toml"
        with self._saving:
            if not file or sound.ambience_member(file) == sound.ambience_member(own):
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# This map's background sound starts from another of the game's (the Studio's "
                                "Background sound).\n" f"background = '{file}'\n", encoding="utf-8")
        return self.map_sound(pack, lang)
