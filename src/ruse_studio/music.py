"""The Music tab's calls (StudioApi's MusicCalls; rusemod.sound): the game's songs by where they play, each song's
sound for the page to play, and the current mod's own songs, saved from the page's editor as
files/replace/<the song's path in ZZ_Win.dat>.wav. The page makes the WAV (the window reads MP3, OGG, FLAC and WAV
itself, and cuts, fades and sets the volume): nothing to install. Not tried in the game yet (2026-10-07)."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
import threading
from pathlib import Path

from rusemod import sound
from rusemod.build import find_pack
from rusemod.edat import Edat
from rusemod.terrain import map_list

# where a song plays, in the order the tab shows them (a song shows under the first that fits, the rest as "also")
GROUPS = ("menu", "credits", "playlist0", "playlist1", "playlist2", "end", "goals", "missions", "other", "unused")


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

    def _music_song(self, member: str) -> dict:
        song = self._music_songs().get(str(member).lower())
        if song is None:
            # not a game rule: the page asked for a song the game hasn't got
            raise MusicError(f"{member} isn't one of the game's songs")
        return song

    def _music_file(self, member: str) -> Path | None:
        """The current mod's own song for `member` (files/replace/<member>.wav), whether made yet or not."""
        mod = self._mod_dir()
        return mod / sound.REPLACE / (member.replace("\\", "/") + ".wav") if mod is not None else None

    # --- what the page calls ---
    def music(self, lang: str = "base") -> dict:
        """The Music tab: the game's songs by where they play (GROUPS order), each with its name, length, format, the
        maps whose missions play it ({map: its names in the game's menus in `lang`, parts: the script folders,
        "chapter1"}), and whether the current mod has its own."""
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
        name = hashlib.sha1(song["member"].encode()).hexdigest()[:24] + ".ess"
        out = self.cache_dir / "sound" / "game" / key / name
        if not out.is_file():
            with Edat.open(str(zz)) as arc:
                raw = bytes(arc.read(arc.entry(song["member"])))
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".part")
            tmp.write_bytes(raw)
            tmp.replace(out)
        return {"url": f"cache/sound/game/{key}/{name}", "kind": "ess", "channels": song["channels"],
                "rate": song["rate"], "frames": song["frames"]}

    def music_save(self, member: str, part: str, index: int, count: int) -> dict:
        """The page's finished song (a 16-bit WAV, in `count` base64 parts sent in order): saved in the current mod
        once the last part is in, as files/replace/<the song's path>.wav."""
        song = self._music_song(member)
        target = self._music_file(song["member"])
        if target is None:
            raise MusicError("Pick or make a mod first: songs are saved in a mod.")
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
        with self._saving:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".part")
            tmp.write_bytes(raw)
            tmp.replace(target)
        up.unlink(missing_ok=True)
        return {"saved": str(target), "seconds": round(len(pcm) / channels / rate, 1)}

    def music_reset(self, member: str) -> dict:
        """Take the current mod's own song out: the game's plays again."""
        song = self._music_song(member)
        target = self._music_file(song["member"])
        if target is None or not target.is_file():
            return {"saved": None}
        with self._saving:
            target.unlink()
        return {"saved": str(target)}
