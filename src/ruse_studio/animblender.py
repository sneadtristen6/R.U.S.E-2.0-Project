"""A unit's animations in the file Change it in Blender opens, and back (item 5 of the owner's list, 2026-11-10: "fully
editable in the studio"; ruse_studio.modelblender's calls use this).

What goes out (unit_plays): every clip the unit's figures play on a model of the opened model's bones, as the current
mod makes it: a unit's own clip for that action (files/anim/units.toml, RUSE Decoy's Only this unit, rusemod.anim),
else the unit's own change to the game's clip, else every unit's change (files/anim/clips.toml), else the game's own;
each once, however many actions play it, named in the modder's language after what the unit does in it, with the
clip's file name after it ("Run, aiming (fusilier_course_vise)"), and the actions that play it on each figure. A model
on bones of its own plays its own clips the same way (the clips whose bones are its bones), or, before any action
plays one, the animations its file carries (rusemod.unitmodel.own_clips).

What came out is kept beside the work file (SENT, and each clip as it went out in the clips folder), so Bring back the
model knows the bones the file was laid out from (its reference record) and which clip each animation was: one that
comes back as it went out is left alone; a changed one is the unit's own from then on (rusemod.rig.clips_back keeps
every track the modder didn't change byte for byte)."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

SENT = "animations.json"     # beside the work file: what went out
CLIPS = "clips"              # beside it: each clip as it went out
NAME_BYTES = 60              # an action's name in Blender holds 63 bytes (UTF-8): one past it is cut off
# the parts of the game's clip names, said in words (words.toml anim_word_<part>); a part not here is left to the
# file name in brackets
WORDS = {"stand": "stand", "idle": "stand", "marche": "walk", "walk": "walk", "course": "run", "run": "run",
         "deroute": "flee", "tir": "fire", "fire": "fire", "accroupi": "crouch", "vise": "aiming", "hit": "hit",
         "mort": "death", "balle": "bullet", "explosion": "blast", "dos": "back", "violente": "violent",
         "arriere": "backwards", "droite": "right", "gauche": "left", "grenade": "grenade", "recharge": "reload",
         "lookaround": "lookaround", "transition": "switch", "bazooka": "bazooka", "pion": "far",
         "ride": "ride", "t": "top", "b": "bottom", "move": "walk", "driver": "driver"}
JOINED = {"look_around": "lookaround"}   # two parts of a name that make one word


def stem_of(clip: str) -> str:
    """A clip's file name without folder, ending and lod0 (genanim_15\\...\\fusilier_standlod0.baf -> fusilier_stand)."""
    stem = str(clip).replace("/", "\\").rsplit("\\", 1)[-1]
    stem = stem[:-4] if stem.lower().endswith(".baf") else stem
    return stem[:-4] if stem.lower().endswith("lod0") else stem


def label(stem: str, w: dict) -> str:
    """An animation's name: what the unit does in it, in words (`w`, the Studio's words in the modder's language),
    then its clip's name in brackets; at most NAME_BYTES bytes (fewer words when it would be longer; the clip's name
    alone, or cut, at worst)."""
    parts = []
    joined = stem.lower()
    for two, one in JOINED.items():
        joined = joined.replace(two, one)
    for p in re.split(r"[_\-\s]+", joined):
        word = WORDS.get(p) or WORDS.get(p.rstrip("0123456789"))
        if word:
            text = w.get(f"anim_word_{word}") or word
            digits = p[len(p.rstrip("0123456789")):]
            parts.append(text + (f" {digits}" if digits and p.rstrip("0123456789") else ""))
        elif p.isdigit() and parts:
            parts[-1] += f" {p}"
    parts = [x for i, x in enumerate(parts) if x not in parts[:i]]
    while parts:
        name = f"{', '.join(parts)} ({stem})"
        name = name[:1].upper() + name[1:]
        if len(name.encode("utf-8")) <= NAME_BYTES:
            return name
        parts.pop()
    out = stem
    while len(out.encode("utf-8")) > NAME_BYTES:
        out = out[:-1]
    return out


def unit_name(own_model: Path) -> str:
    """The name units.toml gives a new unit: its own model file's name (files/models/<the unit's name>.glb)."""
    return Path(own_model).stem


def unit_plays(figures: list, names: list, read, mod: Path | None, unit: str, skeleton_of, w: dict,
               labelled: bool = True) -> list[dict]:
    """The clips a unit plays on a model of the bones `names` (lower case, in order), as the current mod makes them:
    [{"name": the animation's name (label; not `labelled`: its clip's own name, a model on bones of its own's, whose
    animations the modder named and the model's record knows by those names), "clip": its bytes, "member": the game's
    clip it is made from (None: a file of the unit's own), "own": the unit's own file's name (None: none), "actions":
    {figure path: [the names the figure gives it]}}], in the order the figures list them. `figures`:
    rusemod.animlist.unit_figures of the unit (a new unit's: the unit it copies); `read`: rusemod.animlist.clip_reader;
    `mod`: the current mod's folder (None: the game's clips); `unit`: the unit's name in units.toml;
    `skeleton_of(model)`: a figure's model's record, or None."""
    from rusemod import anim, baf
    edits, own_rows = {}, {"clips": {}, "actions": {}}
    if mod is not None:
        edits = anim.mod_clips(mod)
        own_rows = anim.mod_unit_clips(mod).get(unit) or own_rows
    want = [n.lower() for n in names]
    fits: dict = {}
    out: dict = {}
    for f in figures:
        if not f["model"] or not f["clips"]:
            continue
        if f["model"] not in fits:
            rec = skeleton_of(f["model"])
            fits[f["model"]] = rec is not None and [n.lower() for n in baf.skeleton(rec)["names"]] == want
        figure = f["figure"].split(":", 1)[-1]
        for key, member in f["clips"]:
            own = own_rows["actions"].get((key, figure)) or own_rows["actions"].get((key, None))
            if own is not None:
                raw, ident = Path(own).read_bytes(), ("own", Path(own).name)
            else:
                base = read(member)
                if base is None:        # not a game rule: the data names a clip this game build hasn't got
                    continue
                edit = own_rows["clips"].get(member) or edits.get(member)
                raw = anim.made(base, edit, read) if edit else base
                ident = ("unit" if member in own_rows["clips"] else "mod" if edit else "game", member)
            if not fits[f["model"]] and own is None:
                continue
            if [n.lower() for n in baf.skeleton(baf.parse(raw).skeleton)["names"]] != want:
                continue        # (a clip of other bones: not one this model plays)
            row = out.setdefault(ident, {"clip": raw, "member": None if ident[0] == "own" else member,
                                         "own": ident[1] if ident[0] == "own" else None, "actions": {}})
            keys = row["actions"].setdefault(figure, [])
            if key not in keys:
                keys.append(key)
    rows, taken = [], set()
    for (kind, what), row in out.items():
        stem = stem_of(what)
        first = label(stem, w) if labelled else stem
        name, n = first, 2
        while name.lower() in taken:
            name, n = f"{first} {n}", n + 1
        taken.add(name.lower())
        rows.append({"name": name, **row})
    return rows


def as_clips(rows: list) -> list:
    """unit_plays' rows as rusemod.gltf.model_glb's and rusemod.animglb.own_glb's `clips`: [(name, clip, extras)],
    each animation's extras the actions that play it (rusemod_actions, rusemod_figures) and its clip
    (rusemod_clip)."""
    from rusemod import baf
    return [(r["name"], baf.parse(r["clip"]), {"rusemod_clip": r["member"] or r["own"] or "",
                                               "rusemod_actions": sorted({k for ks in r["actions"].values() for k in ks}),
                                               "rusemod_figures": r["actions"]}) for r in rows]


def write_sent(work: Path, model: str, record: bytes, rows: list) -> None:
    """Keep what went out beside the work file: SENT ({"model", "record" (base64), "animations": [{"name", "file",
    "member", "own", "actions", and "model_animation" when it is one of the model's own animations (the unit's
    files/anim/units.toml [unit.<name>.animation]: its name there)}]}) and each clip in CLIPS (k.baf, in order)."""
    work = Path(work)
    folder = work / CLIPS
    if folder.is_dir():
        for f in folder.glob("*.baf"):
            f.unlink()
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for k, r in enumerate(rows):
        (folder / f"{k}.baf").write_bytes(r["clip"])
        out.append({"name": r["name"], "file": f"{CLIPS}/{k}.baf", "member": r["member"], "own": r["own"],
                    "actions": r["actions"],
                    **({"model_animation": r["model_animation"]} if r.get("model_animation") else {})})
    part = work / (SENT + ".part")
    part.write_text(json.dumps({"model": model, "record": base64.b64encode(record).decode("ascii"),
                                "animations": out}, indent=1), encoding="utf-8")
    part.replace(work / SENT)


def read_sent(work: Path) -> dict | None:
    """What went out (write_sent's), with "record" as bytes and each animation's "clip" read back; None when nothing
    did (no animations went out from this work folder) or it can't be read."""
    work = Path(work)
    try:
        sent = json.loads((work / SENT).read_text(encoding="utf-8"))
        sent["record"] = base64.b64decode(sent["record"])
        for a in sent["animations"]:
            a["clip"] = (work / a["file"]).read_bytes()
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return sent


def forget_sent(work: Path) -> None:
    """No animations went out from this work folder (the work file opened has none)."""
    work = Path(work)
    (work / SENT).unlink(missing_ok=True)
    if (work / CLIPS).is_dir():
        for f in (work / CLIPS).glob("*.baf"):
            f.unlink()


def file_animations(path: Path) -> list[str]:
    """The names of a .glb's animations, from its JSON part alone; [] for none or a file that isn't one."""
    import struct
    try:
        with open(path, "rb") as f:
            head = f.read(20)
            if len(head) < 20 or head[:4] != b"glTF":
                return []
            length = struct.unpack_from("<I", head, 12)[0]
            doc = json.loads(f.read(length))
    except (OSError, ValueError, struct.error):
        return []
    return [a.get("name", "") for a in doc.get("animations") or []]
