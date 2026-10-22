"""Every sound the game has, as RUSE Decoy lists them: each of the 17,462 sound files of ZZ_Win.dat by kind (weapons
near and far, impacts, engines, surroundings, map backgrounds, the interface, the ruse cards, unit voices, the HQ's
lines, radio, mission dialogue, music), with a name to show, its length and format, the sound group whose settings it
plays with (and that group's volume in the game), and, for a mission's dialogue line, its words in every language.

Where each kind lives (the game's folders under gen_sound\\ww2\\sons, counted 2026-10-21):
    sfx_ruse\\sfx_tir 35, sfx_ruse\\sfx_traine 2         weapons heard near
    sfx_ruse\\sfx_tir_long_range 34                      weapons heard far away
    sfx_ruse\\sfx_impact 36, sfx\\impact 4, sfx_impact 2, sfx_ruse 2   impacts, hits and destruction
    sfx_moteur 15                                         engines
    sfx_env 41 (+ 13 multipiste_ambiance_*)              surroundings (+ the maps' backgrounds)
    hud 15 + sfx_option 4 (+ hud\\placement_ruse_* 10)   the interface (+ the ruse cards)
    generated\\acknows 3,322                             the units' voice lines (one language)
    generated\\acknows\\<lang> 8 x 244                   the HQ's and intelligence lines (each language)
    acknows 41                                            radio chatter and its jingles
    gen_sound\\test\\map\\<mission>\\...\\<lang> 11,896  the missions' dialogue (each language)
    atp_music 28, jingles 9                               music
How loud the game plays each: its own volume x its group's (TSoundSettings VolumeRef, at most 1.0) x the game's own
volume options; RUSE Decoy's slider changes the sound itself (rusemod.sound.with_volume).
"""
from __future__ import annotations

import html
import re

B = "\\"
SONS = B.join(["gen_sound", "ww2", "sons"]) + B
MISSIONS = B.join(["gen_sound", "test", "map"]) + B
KINDS = ("weapons", "weapons_far", "impacts", "engines", "surroundings", "backgrounds", "interface", "ruses",
         "unit_voices", "hq_voices", "radio", "dialogue", "music", "other")
LANG_FOLDERS = {"fr": "fr", "ger": "ger", "it": "ita", "jpn": "jpn", "pol": "pol", "ru": "ru", "spa": "spa", "us": "us"}
# (the game's sound folders name Italian "it"; its texts, "ita")


def kind_of(member: str) -> str:
    """The kind a sound path (lower case, backslashes) belongs to."""
    p = member.lower()
    if p.startswith(MISSIONS):
        return "dialogue"
    if not p.startswith(SONS):
        return "other"
    rest = p[len(SONS):]
    top, _, tail = rest.partition(B)
    if top == "sfx_ruse":
        sub = tail.split(B)[0] if B in tail else ""
        return {"sfx_tir": "weapons", "sfx_traine": "weapons", "sfx_tir_long_range": "weapons_far"}.get(sub, "impacts")
    if top in ("sfx", "sfx_impact"):
        return "impacts"
    if top == "sfx_moteur":
        return "engines"
    if top == "sfx_env":
        return "backgrounds" if tail.startswith("multipiste_ambiance") else "surroundings"
    if top == "hud":
        return "ruses" if tail.startswith("placement_ruse_") else "interface"
    if top == "sfx_option":
        return "interface"
    if top == "generated":
        if tail.startswith("acknows" + B):
            return "hq_voices" if tail.count(B) >= 2 else "unit_voices"
        return "other"
    if top == "acknows":
        return "radio"
    if top in ("atp_music", "jingles"):
        return "music"
    return "other"


def language_of(member: str) -> str | None:
    """The language folder a per-language sound is in (dialogue, the HQ's lines), as the game's texts name it."""
    parts = member.lower().split(B)
    for part in reversed(parts[:-1]):
        if part in LANG_FOLDERS:
            return LANG_FOLDERS[part]
    return None


def mission_of(member: str) -> str | None:
    """The mission folder a dialogue line is in (m04_cotentin)."""
    p = member.lower()
    return p[len(MISSIONS):].split(B)[0] if p.startswith(MISSIONS) else None


def words(member: str) -> str:
    """A sound's file name in words: "SFX_Tir_ObusAP_Leger_01" -> "Tir obusap leger 01" (the game's own name; the
    index's paths are in lower case, so words run together as the game wrote them)."""
    stem = member.replace("/", B).rsplit(B, 1)[-1].rsplit(".", 1)[0]
    stem = re.sub(r"^(sfx_|ge_|ruse-inter-)", "", stem, flags=re.I)
    return re.sub(r"[_\-]+", " ", stem).strip().capitalize() or stem


def _stem(file_name: str) -> str:
    return file_name.replace("/", B).rsplit(B, 1)[-1].rsplit(".", 1)[0].lower()


def groups(db) -> dict:
    """{sound file's member path: {"group": its sound group, "group_volume": that group's VolumeRef}} from the game
    index (rusemod.index's database): a TSoundDescriptor names its group (Settings_Identifier) and its sound
    (TheSoundStream -> TSoundStream FileName); a group's volume is its TSoundSettings VolumeRef (1.0 if not set). A
    sound used by several descriptors keeps the first group found and lists the others."""
    from .sound import member_of
    vol = {}
    for ident, v in db.execute("""SELECT i.text, v.num FROM object o
                                  JOIN value i ON i.object = o.id AND i.path = 'Identifier'
                                  LEFT JOIN value v ON v.object = o.id AND v.path = 'VolumeRef'
                                  WHERE o.class = 'TSoundSettings' AND o.shadow = 0"""):
        vol[ident] = 1.0 if v is None else float(v)
    out: dict = {}
    for ident, fname in db.execute("""SELECT s.text, f.text FROM object o
                                      LEFT JOIN value s ON s.object = o.id AND s.path = 'Settings_Identifier'
                                      JOIN ref r ON r.src = o.id AND r.path = 'TheSoundStream'
                                      JOIN value f ON f.object = r.dst AND f.path = 'FileName'
                                      WHERE o.class IN ('TSoundDescriptor', 'TCutsceneDescriptor') AND o.shadow = 0"""):
        if not fname:
            continue
        # a file named for every language at once (.ol, .o1, .ol1...: the game adds the language's folder; mission
        # dialogue also starts DataDir:\) is filed under its name alone, "ol:<stem>", for each language's file
        ext = fname.rsplit(".", 1)[-1].lower()
        m = f"ol:{_stem(fname)}" if ext.startswith("o") and ext != "ogg" else member_of(fname)
        got = out.setdefault(m, {"group": ident or "", "group_volume": vol.get(ident, 1.0) if ident else 1.0,
                                 "also": []})
        if ident and ident != got["group"] and ident not in got["also"]:
            got["also"].append(ident)
    return out


def dialogue_keys(db) -> dict:
    """{a dialogue line's file stem, lower case (09vaid_9): its text key name (09vAID_9)} from the missions'
    TCutsceneDescriptor (Key + TheSoundStream's FileName, ...\\Dialog\\Dev\\09vAID_9.ol: one file per language)."""
    out = {}
    for key, fname in db.execute("""SELECT k.text, f.text FROM object o
                                    JOIN value k ON k.object = o.id AND k.path = 'Key'
                                    JOIN ref r ON r.src = o.id AND r.path = 'TheSoundStream'
                                    JOIN value f ON f.object = r.dst AND f.path = 'FileName'
                                    WHERE o.class = 'TCutsceneDescriptor' AND o.shadow = 0"""):
        if key and fname:
            out.setdefault(_stem(fname), key)
    return out


def subtitles(db, keys, lang: str) -> dict:
    """{text key: its words in `lang`} from the game's dialogue texts."""
    keys = [k for k in set(keys) if k]
    out = {}
    for start in range(0, len(keys), 500):
        chunk = keys[start:start + 500]
        marks = ",".join("?" * len(chunk))
        for name, text in db.execute(f"""SELECT name, text FROM text WHERE lang = ? AND dictionary = 'dialog'
                                         AND name IN ({marks})""", [lang] + chunk):
            out[name] = html.unescape(text) if text and "&" in text else text
    return out


def catalogue(db, headers: dict) -> list[dict]:
    """Every sound: [{member, kind, name, seconds, channels, rate, flag, group, group_volume, also, mission, lang,
    key}] for `headers` ({member path: rusemod.sound.header of its file}), sorted by kind (KINDS order) then path."""
    found = groups(db)
    keys = dialogue_keys(db)
    rows = []
    for member, h in headers.items():
        k = kind_of(member)
        g = found.get(member) or found.get(f"ol:{_stem(member)}", {})
        row = {"member": member, "kind": k, "name": words(member),
               "seconds": round(h["frames"] / h["rate"], 2) if h.get("rate") else 0.0, "frames": h.get("frames", 0),
               "channels": h.get("channels"), "rate": h.get("rate"), "flag": h.get("flag"),
               "group": g.get("group", ""), "group_volume": g.get("group_volume", 1.0), "also": g.get("also", []),
               "mission": mission_of(member), "lang": language_of(member), "key": None}
        if k == "dialogue":
            row["key"] = keys.get(_stem(member))
        rows.append(row)
    order = {k: i for i, k in enumerate(KINDS)}
    rows.sort(key=lambda r: (order.get(r["kind"], len(KINDS)), r["member"]))
    return rows
