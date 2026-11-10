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

One unit's own animations: a clip is shared by every unit that plays it, so `files/anim/units.toml` gives one unit
clips of its own, every other unit keeping the game's (RUSE Decoy's "Only this unit"; add_unit_clip for a clip made
elsewhere, Import model's):

    [unit.Descriptor_Unit_Horse_Squad.clip."genanim_15/ww2/res3d/units/common/fusilier_standlod0.baf"]
    speed = 150                                   # as in clips.toml: speed, from, bone; and
    file = "genanim_15/ww2/res3d/units/common/fusilier_standlod0.baf"   # a whole clip in its place (in its folder)
    [unit.Descriptor_Unit_Horse_Squad.action]     # an action of every figure of the unit that lists it
    b_stand = "horse_stand.baf"                   # plays this clip (files/anim/own/<unit>/horse_stand.baf)
    [unit.Descriptor_Unit_Horse_Squad.figure."GfxDescriptorBazooka".action]   # of that figure only (wins)
    t_tir = "rider_bazooka_fire.baf"

The clip files are in `files/anim/own/<the unit's name>/`. The build makes each one once and adds it to ZZ_Win.dat
as a file of its own under a new name (own_<unit>_<name>lod0.baf, beside the soldiers' clips), and points that unit's
listings at it (own_listings): a part of the unit another unit shares too is copied into it first, so the others
keep the game's.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import tomllib
from pathlib import Path

from . import baf

CLIPS = "files/anim/clips.toml"
REPLACE = "files/replace"
UNITS = "files/anim/units.toml"   # units' own animations
OWN = "files/anim/own"            # their clip files, a folder each: files/anim/own/<the unit's name>/
PACKS = "genanim_15\\pack\\"
B = "\\"
# where a unit's own clips go: loose in ZZ_Win.dat in the folder of the soldiers' clips, as the 2026-11-09 test copy's
# own clips were when they played in the game (a folder of their own isn't tried there), and how the data names one
OWN_DIR = "genanim_15\\ww2\\res3d\\units\\common\\"
OWN_DATA_DIR = "WW2\\Res3D\\Units\\Common\\"
_NAME = re.compile(r"^[A-Za-z0-9_]+$")   # a unit's name, as the game's data and the mods give them


class AnimError(ValueError):
    pass


def clip_key(member: str) -> str:
    """How clips.toml names a clip: its path in the packs, forward slashes, lower case."""
    return member.replace(B, "/").lower()


def _member(key: str) -> str:
    return key.strip().replace("/", B).lower()


def _edit(v: dict, where: str) -> dict:
    """One clip's changes as a toml table gives them ({"speed", "from", "bones", "file": None}); `where` starts each
    mistake's words."""
    entry = {"speed": 100.0, "from": None, "bones": {}, "file": None}
    if "speed" in v:
        s = v["speed"]
        if isinstance(s, bool) or not isinstance(s, (int, float)) or not 1 <= s <= 1000:
            raise AnimError(f"{where}: speed is a percent from 1 to 1000")
        entry["speed"] = float(s)
    if v.get("from"):
        if not isinstance(v["from"], str):
            raise AnimError(f"{where}: from names another clip by its path")
        entry["from"] = _member(v["from"])
    for bone, bv in (v.get("bone") or {}).items():
        if not isinstance(bv, dict):
            raise AnimError(f"{where}: bone {bone}: size and turn")
        size = bv.get("size", 1.0)
        if isinstance(size, bool) or not isinstance(size, (int, float)) or not 0.01 <= size <= 20:
            raise AnimError(f"{where}: bone {bone}: size from 0.01 to 20")
        turn = bv.get("turn")
        if turn is not None and not (isinstance(turn, list) and len(turn) == 2 and turn[0] in ("x", "y", "z")
                                     and isinstance(turn[1], (int, float)) and not isinstance(turn[1], bool)
                                     and -360 <= turn[1] <= 360):
            raise AnimError(f"{where}: bone {bone}: turn is [\"x\" or \"y\" or \"z\", degrees]")
        entry["bones"][bone] = {"size": float(size), "turn": (turn[0], float(turn[1])) if turn else None}
    return entry


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
            out[m] = _edit(v, f"{CLIPS}: {key}")
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


# --- one unit's own animations: files/anim/units.toml and files/anim/own/<unit>/ ---
def _own_file(folder: Path, rel, where: str) -> Path:
    """A clip file named in units.toml, in the unit's own folder `folder`: a path under it with forward slashes,
    ending .baf, that is there."""
    if not isinstance(rel, str) or not rel.lower().endswith(".baf") or "\\" in rel or rel.startswith("/") \
            or ":" in rel or any(part in ("", ".", "..") for part in rel.split("/")):
        # not a game rule: where our format keeps a unit's clips
        raise AnimError(f"{where}: name a .baf file in the unit's own folder ({OWN}/<the unit's name>/)")
    f = Path(folder) / rel
    if not f.is_file():
        raise AnimError(f"{where}: {OWN}/{Path(folder).name}/{rel} isn't there")
    return f


def mod_unit_clips(folder: Path, text: str | None = None) -> dict:
    """A mod's units' own animations, from its files/anim/units.toml (or `text`, a units.toml not written yet):
    {unit name: {"clips": {the game's clip path (backslashes, lower case): its changes as mod_clips gives them, "file"
    a clip of the unit's own in its place}, "actions": {(action, figure path or None for every figure): the clip
    file}}}; {} without the file."""
    root = Path(folder)
    f = root / UNITS
    if text is None and not f.is_file():
        return {}
    try:
        table = tomllib.loads(f.read_text(encoding="utf-8") if text is None else text)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise AnimError(f"{UNITS}: {exc}") from None
    units = table.get("unit", {})
    if set(table) - {"unit"} or not isinstance(units, dict):
        # not a game rule: how our format names a unit
        raise AnimError(f"{UNITS}: [unit.<a unit's name>] tables, one a unit")
    out: dict = {}
    for unit, u in units.items():
        if not _NAME.match(unit) or not isinstance(u, dict) or set(u) - {"clip", "action", "figure"}:
            raise AnimError(f"{UNITS}: [unit.{unit}]: a unit's name (letters, digits and _), then its clip, action "
                            f"and figure tables")
        own = root / OWN / unit
        clips: dict = {}
        for key, v in (u.get("clip") or {}).items():
            m = _member(key)
            if not m.endswith(".baf") or not isinstance(v, dict):
                raise AnimError(f"{UNITS}: {unit}: {key}: name a clip by its path in the game's packs, ending .baf")
            entry = _edit(v, f"{UNITS}: {unit}: {key}")
            if v.get("file"):
                entry["file"] = _own_file(own, v["file"], f"{UNITS}: {unit}: {key}")
            clips[m] = entry
        actions: dict = {}
        figures = u.get("figure") or {}
        if not isinstance(u.get("action") or {}, dict) or not isinstance(figures, dict):
            raise AnimError(f"{UNITS}: {unit}: [unit.{unit}.action] names actions, [unit.{unit}.figure.\"<its path>\""
                            f".action] one figure's")
        rows = [(None, u.get("action") or {})]
        for fig, fv in figures.items():
            if not isinstance(fv, dict) or set(fv) - {"action"} or not isinstance(fv.get("action") or {}, dict):
                raise AnimError(f"{UNITS}: {unit}: figure {fig}: its action table")
            rows.append((fig, fv.get("action") or {}))
        for fig, acts in rows:
            for action, rel in acts.items():
                actions[(action, fig)] = _own_file(own, rel, f"{UNITS}: {unit}: {action}"
                                                             + (f" ({fig})" if fig else ""))
        out[unit] = {"clips": clips, "actions": actions}
    return out


def own_stem(unit: str, name: str) -> str:
    """A unit's own clip's name in the game: own_<the unit's name without Descriptor_Unit_>_<name>lod0, in lower case
    letters, digits and _ ("Descriptor_Unit_Horse_Squad", "fusilier_standlod0" -> own_horse_squad_fusilier_standlod0),
    named the way the clips that played on 2026-11-09 were (hr_b_standlod0)."""
    u = re.sub(r"^descriptor_(unit_)?", "", unit.lower())
    n = re.sub(r"lod0$", "", name.lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1].removesuffix(".baf"))
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]+", "_", f"own_{u}_{n}")).strip("_") + "lod0"


def own_member(stem: str) -> str:
    """A unit's own clip's path in ZZ_Win.dat, from its own_stem."""
    return f"{OWN_DIR}{stem}.baf"


def own_data_name(stem: str) -> str:
    """The FileName a listing gives a unit's own clip (animlist.member_of turns it into own_member's path)."""
    return f"{OWN_DATA_DIR}{stem}.Ase2NdfBin"


def _q(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _bare(s: str) -> str:
    return s if re.fullmatch(r"[A-Za-z0-9_-]+", s) else _q(s)


def units_toml(table: dict) -> str | None:
    """units.toml's text for `table` ({unit: {"clip": {clip key: {"speed", "from", "file", "bone": {name: {"size",
    "turn"}}}}, "action": {action: file}, "figure": {path: {"action": {action: file}}}}}), in name order; None when
    it holds nothing."""
    lines = ["# One unit's own animations: every unit not named here plays the game's (rusemod.anim). RUSE Decoy",
             "# (\"Only this unit\") and Import model write it; the build makes each clip a file of its own, beside the",
             "# game's, and points only that unit's actions at it. Clip files: files/anim/own/<the unit's name>/.", ""]
    some = False
    for unit in sorted(table):
        u = table[unit] or {}
        for key in sorted(u.get("clip") or {}):
            e = u["clip"][key]
            some = True
            head = f"unit.{_bare(unit)}.clip.{_q(key)}"
            lines.append(f"[{head}]")
            if e.get("speed") is not None and float(e["speed"]) != 100.0:
                lines.append(f"speed = {float(e['speed']):g}")
            if e.get("from"):
                lines.append(f"from = {_q(e['from'])}")
            if e.get("file"):
                lines.append(f"file = {_q(e['file'])}")
            for bone, b in sorted((e.get("bone") or {}).items()):
                lines.append(f"[{head}.bone.{_q(bone)}]")
                if b.get("size") is not None:
                    lines.append(f"size = {float(b['size']):g}")
                if b.get("turn"):
                    lines.append(f"turn = [{_q(b['turn'][0])}, {float(b['turn'][1]):g}]")
            lines.append("")
        rows = [(f"unit.{_bare(unit)}.action", u.get("action") or {})]
        rows += [(f"unit.{_bare(unit)}.figure.{_q(fig)}.action", (fv or {}).get("action") or {})
                 for fig, fv in sorted((u.get("figure") or {}).items())]
        for head, acts in rows:
            if acts:
                some = True
                lines.append(f"[{head}]")
                lines += [f"{_bare(a)} = {_q(acts[a])}" for a in sorted(acts)]
                lines.append("")
    return "\n".join(lines) if some else None


def read_units(mod: Path) -> dict:
    """The mod's units.toml as it is written ({unit: its tables}), {} without one."""
    f = Path(mod) / UNITS
    if not f.is_file():
        return {}
    try:
        return dict(tomllib.loads(f.read_text(encoding="utf-8")).get("unit", {}))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise AnimError(f"{UNITS}: {exc}") from None


def write_units(mod: Path, table: dict) -> None:
    """Write `table` as the mod's units.toml (read back as the build reads it before it takes the old one's place);
    no file when it holds nothing."""
    f = Path(mod) / UNITS
    text = units_toml(table)
    if text is None:
        f.unlink(missing_ok=True)
        return
    mod_unit_clips(mod, text)   # (raises on anything the build wouldn't take: the old file stays)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(f)


def _file_name(name: str) -> str:
    """A clip file's name in a unit's folder from a name a tool gives it: letters, digits, _ and -, ending .baf."""
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", str(name).removesuffix(".baf")).strip("_")
    if not stem:
        raise AnimError(f"{name!r} can't be a clip's name: give it letters or digits")
    return stem + ".baf"


def add_unit_clip(mod: Path, unit: str, action: str, clip: bytes, name: str | None = None,
                  figure: str | None = None) -> Path:
    """Give the unit `unit` (its name: Descriptor_Unit_Horse_Squad, a new unit's or the game's) a clip of its own for
    its action `action` (the name its figures list the clip by: "t_stand", "b_course", "idle1"...), in the mod at
    `mod`. `clip` is a game clip's bytes (rusemod.baf; checked here); it is kept as files/anim/own/<unit>/<name>.baf
    (`name` the action's when not given: give several actions the same name and bytes to share one file), and its row
    goes in files/anim/units.toml: [unit.<unit>.action] for every figure of the unit that lists the action, or with
    `figure` (its path from the unit: "GfxDescriptorBazooka", "GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine")
    [unit.<unit>.figure."<figure>".action] for that figure alone, which wins. The build then writes the clip into the
    game under a name of its own and points only that unit's listings of the action at it. The clip must move the
    bones of the model the figure draws; the build can't tell. Returns the clip file."""
    if not isinstance(unit, str) or not _NAME.match(unit):
        raise AnimError(f"{unit!r} isn't a unit's name (letters, digits and _)")
    if not isinstance(action, str) or not action.strip() or any(c in action for c in "\"\\\n"):
        raise AnimError(f"{action!r} isn't an action's name")
    try:
        baf.check(baf.parse(clip))
    except baf.ClipError as exc:
        raise AnimError(f"{unit}: {action}: {exc}") from None
    file_name = _file_name(name or action)
    own = Path(mod) / OWN / unit
    table = read_units(mod)
    u = dict(table.get(unit) or {})
    if figure:
        figs = {k: dict(v) for k, v in (u.get("figure") or {}).items()}
        acts = dict((figs.get(figure) or {}).get("action") or {})
        acts[action] = file_name
        figs[figure] = {"action": acts}
        u["figure"] = figs
    else:
        acts = dict(u.get("action") or {})
        acts[action] = file_name
        u["action"] = acts
    table[unit] = u
    own.mkdir(parents=True, exist_ok=True)
    f = own / file_name
    before = f.read_bytes() if f.is_file() else None
    tmp = f.with_suffix(".part")
    tmp.write_bytes(bytes(clip))
    tmp.replace(f)
    try:
        write_units(mod, table)
    except AnimError:   # (units.toml as it was, and the file too)
        if before is None:
            f.unlink(missing_ok=True)
        else:
            f.write_bytes(before)
        raise
    return f


def _named_files(u: dict) -> set:
    """The clip files a unit's tables name, as written there."""
    named = {e.get("file") for e in (u.get("clip") or {}).values() if isinstance(e, dict) and e.get("file")}
    named |= set((u.get("action") or {}).values())
    for fv in (u.get("figure") or {}).values():
        named |= set(((fv or {}).get("action") or {}).values())
    return named


def remove_unit_clip(mod: Path, unit: str, action: str, figure: str | None = None) -> bool:
    """Take add_unit_clip's row out (the action plays what it did before); its file goes too when no other row of
    the unit names it. Whether there was such a row."""
    table = read_units(mod)
    u = dict(table.get(unit) or {})
    if figure:
        figs = {k: dict(v) for k, v in (u.get("figure") or {}).items()}
        acts = dict((figs.get(figure) or {}).get("action") or {})
        gone = acts.pop(action, None)
        if acts:
            figs[figure] = {"action": acts}
        else:
            figs.pop(figure, None)
        u["figure"] = figs
    else:
        acts = dict(u.get("action") or {})
        gone = acts.pop(action, None)
        u["action"] = acts
    if gone is None:
        return False
    u = {k: v for k, v in u.items() if v}
    if u:
        table[unit] = u
    else:
        table.pop(unit, None)
    write_units(mod, table)
    if gone not in _named_files(u):
        (Path(mod) / OWN / unit / gone).unlink(missing_ok=True)
    return True


def remove_unit(mod: Path, unit: str) -> None:
    """Everything a unit had of its own animations, out of the mod: its tables in units.toml and its folder in
    files/anim/own (a unit taken out of a mod: a row for a unit no mod makes is an error in the build)."""
    table = read_units(mod)
    if table.pop(unit, None) is not None:
        write_units(mod, table)
    folder = Path(mod) / OWN / unit
    if _NAME.match(unit) and folder.is_dir():
        shutil.rmtree(folder)


def own_listings(game, name: str, by_clip: dict, by_action: dict) -> dict:
    """Point the clip listings of the unit `name` (a top-level object of `game`, the build's rusemod.patch.Game) at
    clips of its own: every listing whose clip is one of `by_clip`'s ({the game's clip path: the FileName of the
    unit's own}), and every listing of an action in `by_action` ({(action, figure path or None): FileName}: that
    figure's, or every figure's that lists it), which wins. Only the unit's graphics are walked (its GfxDescriptor*
    parts and the unnamed parts under them: never another unit or a named object of the game's); a part the unit
    shares with other units is copied into it before it changes, so they keep the game's, as build._point_at_copies
    does for models (and as the 2026-11-09 test mods' `patch own` lines did for their listings). Returns
    {"pointed": {FileName: how many listings name it now}, "plays": {clip path: listings that play it},
    "actions": {(figure path, action)}}."""
    from .animlist import member_of
    from .patch import Inline, ListV, MapV, PairV, Ref, Text, _fresh
    objects = game.objects

    def anim_of(v):
        if isinstance(v, Inline):
            return v.obj
        return objects.get(v.target) if isinstance(v, Ref) and v.target else None

    def file_of(v):
        a = anim_of(v)
        f = a.props.get("FileName") if a is not None else None
        return f if isinstance(f, Text) and f.value else None

    def wanted(key, v, figure):
        """The FileName this listing is to name, or None (not one of the unit's own)."""
        f = file_of(v)
        if f is None:
            return None
        k = key.value if isinstance(key, Text) else None
        got = (by_action.get((k, figure)) or by_action.get((k, None))) if k is not None else None
        return got or by_clip.get(member_of(f.value))

    def step(path, prop):
        return f"{path}.{prop}" if path else prop

    def figures(v, path, depth=0, seen=frozenset()):
        """(path, object) of each object holding clip listings under `v` (its unnamed parts followed)."""
        if depth > 24:
            return
        if isinstance(v, Ref):
            if v.target in objects and not v.target.startswith("$/") and v.target not in seen:
                yield from obj_figures(objects[v.target], path, depth + 1, seen | {v.target})
        elif isinstance(v, Inline):
            yield from obj_figures(v.obj, path, depth + 1, seen)
        elif isinstance(v, ListV):
            for i, x in enumerate(v.items):
                yield from figures(x, f"{path}[{i}]", depth + 1, seen)
        elif isinstance(v, MapV):
            for i, (_k, x) in enumerate(v.pairs):
                yield from figures(x, f"{path}[{i}].v", depth + 1, seen)
        elif isinstance(v, PairV):
            yield from figures(v.a, path, depth + 1, seen)
            yield from figures(v.b, path, depth + 1, seen)

    def obj_figures(obj, path, depth, seen):
        if isinstance(obj.props.get("ResourceAnimation"), MapV):
            yield path, obj
        for p, w in obj.props.items():
            if p != "ResourceAnimation":
                yield from figures(w, step(path, p), depth, seen)

    def changes(fig, path) -> bool:
        return any((own := wanted(k, v, path)) and file_of(v).value != own
                   for k, v in fig.props["ResourceAnimation"].pairs)

    pointed: dict = {}

    def point(v, path, put, depth=0, seen=frozenset()) -> int:
        if not any(changes(fig, p) for p, fig in figures(v, path, depth, seen)):
            return 0
        if isinstance(v, Ref):
            seen = seen | {v.target}
            v = Inline(_fresh(objects[v.target]))  # the unit's own copy of a part others link to as well
            put(v)
        if isinstance(v, Inline):
            obj, n = v.obj, 0
            ra = obj.props.get("ResourceAnimation")
            for i, (k, x) in enumerate(ra.pairs if isinstance(ra, MapV) else []):
                own = wanted(k, x, path)
                if own and file_of(x).value != own:
                    a = Inline(_fresh(anim_of(x))) if isinstance(x, Ref) else x   # (its own copy of the listing)
                    a.obj.props["FileName"] = Text(a.obj.props["FileName"].kind, own)
                    ra.pairs[i] = (k, a)
                    pointed[own] = pointed.get(own, 0) + 1
                    n += 1
            for p, w in list(obj.props.items()):
                if p != "ResourceAnimation":
                    n += point(w, step(path, p), lambda x, p=p, o=obj: o.props.__setitem__(p, x), depth + 1, seen)
            return n
        if isinstance(v, ListV):
            return sum(point(x, f"{path}[{i}]", lambda y, i=i: v.items.__setitem__(i, y), depth + 1, seen)
                       for i, x in enumerate(v.items))
        if isinstance(v, MapV):
            return sum(point(x, f"{path}[{i}].v", lambda y, i=i, k=k: v.pairs.__setitem__(i, (k, y)), depth + 1, seen)
                       for i, (k, x) in enumerate(v.pairs))
        if isinstance(v, PairV):
            return point(v.a, path, lambda y: setattr(v, "a", y), depth + 1, seen) + \
                point(v.b, path, lambda y: setattr(v, "b", y), depth + 1, seen)
        return 0

    unit = objects[name]
    tops = [p for p in unit.props if p.startswith("GfxDescriptor")]
    plays: dict = {}
    actions: set = set()
    for p in tops:
        for path, fig in figures(unit.props[p], p):
            for k, v in fig.props["ResourceAnimation"].pairs:
                f = file_of(v)
                if isinstance(k, Text):
                    actions.add((path, k.value))
                if f is not None:
                    m = member_of(f.value)
                    plays[m] = plays.get(m, 0) + 1
    if any(changes(fig, path) for p in tops for path, fig in figures(unit.props[p], p)):
        unit = game.own(name)   # (one of the game's: copied before it changes)
        for p in [p for p in unit.props if p.startswith("GfxDescriptor")]:
            point(unit.props[p], p, lambda x, p=p: unit.props.__setitem__(p, x))
    return {"pointed": pointed, "plays": plays, "actions": actions}


def own_clip_files(zz, wanted: dict, cache: Path | None = None, say=print) -> dict:
    """{its path in ZZ_Win.dat: bytes} for the units' own clips (build.unit_own_clips: {that path: {"unit", "clip":
    the game's clip it's made from or None, "edit": its changes, "file": the unit's own file or None}}): each made
    once (`made`: the game's clip with the unit's changes, or the unit's own file, checked), to be added to ZZ_Win.dat
    as files of their own. The game's clips are read from `zz` as the game has them, never changed here."""
    from .edat import Edat
    packs: list | None = None

    def game_clip(member: str):
        nonlocal packs
        e = zz.entry(member)
        if e is not None:
            return bytes(zz.read(e))
        if packs is None:   # (read only when a clip isn't loose)
            packs = [Edat(bytes(zz.read(x))) for x in zz.entries
                     if x.path.lower().startswith(PACKS) and x.path.lower().endswith(".apk")]
        for pk in packs:
            x = pk.entry(member)
            if x is not None:
                return bytes(pk.read(x))
        return None

    out: dict = {}
    for member, spec in sorted(wanted.items()):
        if zz.entry(member) is not None:  # not a game rule: unit_own_clips hands out names the game hasn't got
            raise AnimError(f"{member} is one of the game's own files already")
        where = f"{UNITS}: {spec['unit']}: " + (clip_key(spec["clip"]) if spec.get("clip") else Path(spec["file"]).name)
        if spec.get("clip"):
            base, edit = game_clip(spec["clip"]), spec.get("edit") or {}
            if base is None:
                # not a game rule: the mod names a clip this game build doesn't have (a typo, another game build)
                raise AnimError(f"{where}: the game has no such clip")
        else:
            base, edit = Path(spec["file"]).read_bytes(), {}
        key = hashlib.sha256(b"own\n" + base + repr(sorted((k, str(v)) for k, v in edit.items())).encode()
                             + (Path(edit["file"]).read_bytes() if edit.get("file") else b"")).hexdigest()
        file = Path(cache) / "anim" / f"{key}.baf" if cache is not None else None
        if file is not None and file.is_file():
            data = file.read_bytes()
        else:
            try:
                data = made(base, edit, game_clip)   # (a file of the unit's own alone: read and written again: checked)
            except AnimError as exc:
                raise AnimError(f"{where}: {exc}") from None
            if file is not None:
                file.parent.mkdir(parents=True, exist_ok=True)
                part = file.with_suffix(".part")
                part.write_bytes(data)
                part.replace(file)
        bits = [f"{edit['speed']:g}%" if edit.get("speed", 100) != 100 else ""]
        if edit.get("from"):
            bits.append(f"as {clip_key(edit['from']).rsplit('/', 1)[-1]}")
        if edit.get("file"):
            bits.append(f"from {Path(edit['file']).name}")
        bits += [f"{b}" for b in edit.get("bones", {})]
        what = clip_key(spec["clip"]) if spec.get("clip") else f"{OWN}/{spec['unit']}/{Path(spec['file']).name}"
        say(f"animation of {spec['unit']} alone: {what} {' '.join(x for x in bits if x)}".rstrip()
            + f" -> {member.rsplit(B, 1)[-1]}")
        out[member] = data
    return out
