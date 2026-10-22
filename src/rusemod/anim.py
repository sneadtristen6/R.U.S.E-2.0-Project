"""A mod's own animations, put in by the build (RUSE Decoy saves them; rusemod.baf reads and writes the clips).

`files/anim/clips.toml` changes the game's clips, each named by its path in the game's packs:

    [clip."genanim_15/ww2/res3d/units/common/fusilier_courselod0.baf"]
    speed = 150                                   # percent of the game's (1 to 1000)
    from = "genanim_15/ww2/res3d/units/common/fusilier_deroutelod0.baf"   # another clip of the same bones in its place
    [clip."genanim_15/ww2/res3d/units/common/fusilier_courselod0.baf".bone."bip01 head"]
    size = 2.5                                    # the bone this many times its size, all along the clip
    turn = ["z", 30]                              # and turned this many degrees about its own x, y or z

and `files/replace/<clip path>` (a .baf made elsewhere: Blender, a motion capture) takes a clip's place whole; the
toml's changes then apply on top of it. The build makes each clip once and writes it into every pack of the game that
holds it (one clip can be in up to seven of the genanim_15 packs, and loose in ZZ_Win.dat).
"""
from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

from . import baf

CLIPS = "files/anim/clips.toml"
REPLACE = "files/replace"
PACKS = "genanim_15\\pack\\"
B = "\\"


class AnimError(ValueError):
    pass


def clip_key(member: str) -> str:
    """How clips.toml names a clip: its path in the packs, forward slashes, lower case."""
    return member.replace(B, "/").lower()


def _member(key: str) -> str:
    return key.strip().replace("/", B).lower()


def mod_clips(folder: Path) -> dict:
    """{clip path (backslashes, lower case): {"speed", "from", "bones": {name: {"size", "turn"}}, "file"}} from a
    mod's files/anim/clips.toml and files/replace/**/*.baf."""
    root = Path(folder)
    out: dict = {}
    f = root / CLIPS
    if f.is_file():
        try:
            table = tomllib.loads(f.read_text(encoding="utf-8")).get("clip", {})
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise AnimError(f"{CLIPS}: {exc}") from None
        if not isinstance(table, dict):
            raise AnimError(f"{CLIPS}: [clip.\"<path>\"] tables, one a clip")
        for key, v in table.items():
            m = _member(key)
            if not m.endswith(".baf") or not isinstance(v, dict):  # not a game rule: a clip is named by its pack path
                raise AnimError(f"{CLIPS}: {key}: name a clip by its path in the game's packs, ending .baf")
            entry = {"speed": 100.0, "from": None, "bones": {}, "file": None}
            if "speed" in v:
                s = v["speed"]
                if isinstance(s, bool) or not isinstance(s, (int, float)) or not 1 <= s <= 1000:
                    raise AnimError(f"{CLIPS}: {key}: speed is a percent from 1 to 1000")
                entry["speed"] = float(s)
            if v.get("from"):
                if not isinstance(v["from"], str):
                    raise AnimError(f"{CLIPS}: {key}: from names another clip by its path")
                entry["from"] = _member(v["from"])
            for bone, bv in (v.get("bone") or {}).items():
                if not isinstance(bv, dict):
                    raise AnimError(f"{CLIPS}: {key}: bone {bone}: size and turn")
                size = bv.get("size", 1.0)
                if isinstance(size, bool) or not isinstance(size, (int, float)) or not 0.01 <= size <= 20:
                    raise AnimError(f"{CLIPS}: {key}: bone {bone}: size from 0.01 to 20")
                turn = bv.get("turn")
                if turn is not None and not (isinstance(turn, list) and len(turn) == 2 and turn[0] in ("x", "y", "z")
                                             and isinstance(turn[1], (int, float)) and not isinstance(turn[1], bool)
                                             and -360 <= turn[1] <= 360):
                    raise AnimError(f"{CLIPS}: {key}: bone {bone}: turn is [\"x\" or \"y\" or \"z\", degrees]")
                entry["bones"][bone] = {"size": float(size), "turn": (turn[0], float(turn[1])) if turn else None}
            out[m] = entry
    rep = root / REPLACE
    if rep.is_dir():
        for p in sorted(rep.rglob("*.baf")):
            m = p.relative_to(rep).as_posix().lower().replace("/", B)
            out.setdefault(m, {"speed": 100.0, "from": None, "bones": {}, "file": None})["file"] = p
    return out


def made(base: bytes, edit: dict, source=None) -> bytes:
    """A clip made from the game's `base` (or the mod's own file, or `source(path)`'s clip for "from") with `edit`."""
    raw = base
    if edit.get("file"):
        raw = Path(edit["file"]).read_bytes()
    elif edit.get("from"):
        got = source(edit["from"]) if source else None
        if got is None:  # not a game rule: no such clip in the game's packs
            raise AnimError(f"the game has no clip {clip_key(edit['from'])}")
        other, mine = baf.parse(got), baf.parse(base)
        if not baf.same_skeleton(mine, other):
            raise AnimError(f"{clip_key(edit['from'])} moves other bones: only a clip of the same bones can stand in")
        raw = got
    try:
        c = baf.parse(raw)
        for bone, b in edit.get("bones", {}).items():
            c = baf.with_bone(c, bone, b.get("size", 1.0), b.get("turn"))
        if edit.get("speed", 100.0) != 100.0:
            c = baf.with_speed(c, edit["speed"])
        return baf.build(c)
    except baf.ClipError as exc:
        raise AnimError(str(exc)) from None


def changes(zz, clips: dict, cache: Path | None = None, say=print, before: dict | None = None) -> dict:
    """{member path in ZZ_Win.dat: new bytes} for a mod's `clips` (mod_clips): each clip made once, and written into
    every genanim_15 pack that holds it (and in its place when it's loose in ZZ_Win.dat). `before`: members other
    build steps already changed ({path: bytes})."""
    from .edat import Edat
    earlier = {k.lower().replace("/", B): v for k, v in (before or {}).items()}
    packs = []
    for e in zz.entries:
        p = e.path.lower()
        if p.startswith(PACKS) and p.endswith(".apk"):
            packs.append((e, Edat(earlier.get(p) or bytes(zz.read(e)))))

    def game_clip(member: str):
        e = zz.entry(member)
        if e is not None:
            return bytes(zz.read(e))
        for _e, pk in packs:
            x = pk.entry(member)
            if x is not None:
                return bytes(pk.read(x))
        return None

    new: dict = {}
    for member, edit in sorted(clips.items()):
        base = game_clip(member)
        if base is None:
            # not a game rule: the mod names a clip this game build doesn't have (a typo, another game build)
            raise AnimError(f"{CLIPS}: the game has no clip {clip_key(member)}")
        key = hashlib.sha256(base + repr(sorted((k, str(v)) for k, v in edit.items())).encode()
                             + (Path(edit["file"]).read_bytes() if edit.get("file") else b"")).hexdigest()
        file = Path(cache) / "anim" / f"{key}.baf" if cache is not None else None
        if file is not None and file.is_file():
            new[member] = file.read_bytes()
        else:
            new[member] = made(base, edit, game_clip)
            if file is not None:
                file.parent.mkdir(parents=True, exist_ok=True)
                part = file.with_suffix(".part")
                part.write_bytes(new[member])
                part.replace(file)
        bits = [f"{e['speed']:g}%" if e.get("speed", 100) != 100 else "" for e in (edit,)]
        if edit.get("from"):
            bits.append(f"as {clip_key(edit['from']).rsplit('/', 1)[-1]}")
        if edit.get("file"):
            bits.append(f"from {Path(edit['file']).name}")
        bits += [f"{b}" for b in edit.get("bones", {})]
        say(f"animation: {clip_key(member)} {' '.join(x for x in bits if x)}".rstrip())
    out: dict = {}
    for member, data in new.items():
        e = zz.entry(member)
        if e is not None:
            out[e.path] = data
    for e, pk in packs:
        replace = {}
        for member, data in new.items():
            x = pk.entry(member)
            if x is not None:
                replace[x.path] = data
        if replace:
            out[e.path] = pk.to_bytes(replace)
    return out
