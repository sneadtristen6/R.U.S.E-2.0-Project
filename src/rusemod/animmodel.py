"""A model on bones of its own and its animations, from Import model to the game (the owner's list, item 5, part 1:
the Horse Squad that played on 2026-11-09 was made by hand; this is the way in through the Studio).

What the import keeps (ruse_studio.animmodel_calls, with rusemod.unitmodel.import_model's `own_bones`): the model's
file (files/models/<the unit's name>.glb) holds its skeleton and every animation; each animation is also a clip of the
unit's own (files/anim/own/<the unit's name>/<animation>.baf, rusemod.anim), and each action of the unit the file names
gets its row in files/anim/units.toml (actions_named). The model's record (files/models/<the unit's name>.json) says
what came in: "skeleton" ("own"; "soldier" for a model on the game's own bones), "bones" (their names, in the
skeleton's order), "animations" ([{"name", "frames", "seconds", "file"}]), "actions" ({each action the figures that
wear the model list: the animation that plays it, or None when no animation is named for it}) and, when the file says
where its two halves meet, "split" (split_of).

The name rule (actions_named), the first that fits for each action:
  1. the file says so: an animation whose extras list the action ("rusemod_actions", as the Studio's own files have);
  2. the animation is named as the action ("t_marche", for that half alone), or as the action without its half
     ("marche", "stand_vise": both halves), or by a plain word for it (PLAIN: stand or idle, walk, run, death or die,
     fire or shoot, reload, hit, crouch, aim, look, flee, grenade), with or without a half ("b_walk"). A name is read
     in small letters, without what Blender puts before a "|" ("Armature|Walk") and without a start every animation
     of the file shares ("horse_walk", "horse_run": "walk", "run"); a name with a half fits before one without.
An action no animation is named for stays empty (None): which animation plays it is the action table's (item 5,
part 2).

The halves: a soldier plays two clips at once, its top half's and its bottom half's, each listing through a mask that
weighs the bones (its action's t_ or b_). A model on bones of its own is split at one bone (halves_for): the one its
record names ("split": item 5, part 3's page), else its first bone, so the top's clips move the whole model and the
bottom's nothing. The build (rusemod.build.unit_own_halves, point_masks) writes the two masks, copies of the game's own
top and bottom masks naming the model's bones (rusemod.unitmodel.halves), and points every listing of every figure that
wears the model at them; a mask that names no bone (the parachute's) is left as it is: it weighs every bone alike. The
game looks each name a mask weighs up among the model's bones, and a name it can't find stops it with its "Quit game ?"
box, so the game's own masks, naming the soldier's bones, can't stay on such a model; a mask with no names gives every
bone its default weight. Played in the game: the 2026-11-09 Horse Squad's two halves (split at the rider's root, every
bone in one of them). Not tried in the game yet: a split at another bone, and a half with no bone."""
from __future__ import annotations

import re
from pathlib import Path

from . import baf

ACTIONS_EXTRA = "rusemod_actions"   # an animation's extras: the actions it plays (the Studio's own files)
HALVES_EXTRA = "rusemod_halves"     # the asset's extras: {"top": [bones], "bottom": [bones]}
HALF_KEYS = ("t_", "b_")            # an action's half, as the game's soldiers name their actions
# a plain word for one of the game's actions (each the game's action without its half): what a modder calls it
PLAIN = {"stand": "stand", "idle": "stand", "walk": "marche", "run": "course", "death": "mort", "die": "mort",
         "dead": "mort", "fire": "tir", "shoot": "tir", "reload": "recharge", "hit": "hit", "crouch": "accroupi",
         "aim": "stand_vise", "look": "look_around", "flee": "deroute", "grenade": "tir_secondaire"}


class AnimModelError(ValueError):
    pass


# --- the name rule ---
def plain_name(name: str) -> str:
    """An animation's name as the rule reads it: small letters, what Blender puts before a "|" left off, every run of
    other signs one "_"."""
    name = str(name).rsplit("|", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _shared_start(names: list) -> int:
    """How many words ("_"-parted) every one of `names` starts with alike (two names at least), leaving each a word of
    its own and never ending on a half's letter (t, b)."""
    if len(names) < 2:
        return 0
    words = [n.split("_") for n in names]
    k = 0
    while all(len(w) > k + 1 for w in words) and len({w[k] for w in words}) == 1:
        k += 1
    while k and words[0][k - 1] in ("t", "b"):
        k -= 1
    return k


def read_names(names: list) -> list:
    """Each animation name as (half or None, the game's action without its half) the rule reads it as."""
    plain = [plain_name(n) for n in names]
    cut = _shared_start([p for p in plain if p])
    out = []
    for p in plain:
        p = "_".join(p.split("_")[cut:]) if cut else p
        half = next((h for h in HALF_KEYS if p.startswith(h) and len(p) > len(h)), None)
        rest = p[len(half):] if half else p
        out.append((half, PLAIN.get(rest, rest)))
    return out


def action_parts(action: str) -> tuple:
    """(its half or None, the action without it): "t_marche" -> ("t_", "marche")."""
    a = action.lower()
    half = next((h for h in HALF_KEYS if a.startswith(h)), None)
    return half, a[len(half):] if half else a


def clip_names(rig) -> list:
    """Each of a rig's animations (rusemod.rig.Rig) by the name its clip has (rusemod.unitmodel.own_clips: a name the
    file gives twice numbered, "Walk 2"), in the rig's order."""
    out: list = []
    for a in rig.animations:
        name, k = a.name, 2
        while name in out:
            name, k = f"{a.name} {k}", k + 1
        out.append(name)
    return out


def actions_named(actions: list, names: list, said: list | None = None) -> dict:
    """{each of `actions` (the game's names, as the unit's figures list them): the name of the animation of `names`
    that plays it, or None} by the name rule (above). `said`: for each of `names`, the actions the file says it plays
    (its extras), or None."""
    said = list(said or []) + [None] * (len(names) - len(said or []))
    read = read_names(names)
    out: dict = {}
    for action in actions:
        half, core = action_parts(action)
        got = next((n for n, s in zip(names, said) if s and action in s), None)
        if got is None:     # (a name with this half, then one with none: the first in the file's order)
            got = next((n for n, (h, c) in zip(names, read) if h is not None and h == half and c == core), None)
        if got is None:
            got = next((n for n, (h, c) in zip(names, read) if h is None and c == core), None)
        out[action] = got
    return out


# --- the unit's own clips and rows (files/anim/own/<unit>/, files/anim/units.toml: rusemod.anim) ---
def file_names(names: list, reserved=()) -> dict:
    """{each animation's name: the name of its clip file in the unit's folder} (rusemod.anim's rule for a clip
    file's name: letters, digits, _ and -; two that come out alike, not counting capitals, or one alike a file of
    `reserved`, numbered)."""
    from . import anim
    out, taken = {}, {str(r).lower() for r in reserved}
    for name in names:
        try:
            f = anim._file_name(name)
        except anim.AnimError:
            f = "animation.baf"   # (a name with no letter or digit in it)
        stem, k = f[:-len(".baf")], 2
        while f.lower() in taken:
            f, k = f"{stem}_{k}.baf", k + 1
        taken.add(f.lower())
        out[name] = f
    return out


def keep_animations(mod, unit: str, clips: dict, actions: list, said: list | None = None,
                    before: list | None = None) -> dict:
    """Keep a model's animations (`clips`: {name: a game clip's bytes}, rusemod.unitmodel.own_clips) as the unit
    `unit`'s own clips in the mod at `mod`: each a file of the unit's own (files/anim/own/<unit>/, file_names), and
    rows in files/anim/units.toml, the ones rusemod.anim.add_unit_clip writes ([unit.<unit>.action] <action> = <file>),
    all written at once, the clips checked first:
      - a row naming the file of one of the model's animations before this import (`before`, the record's
        "animations": [{"name", "file"}]) stays when an animation of that name came in again (the choice made for it is
        kept: a model changed in Blender and brought back), its file the new one's; else it goes;
      - each of `actions` (the actions the figures wearing the model list) with no row gets the animation named for
        it (actions_named, `said`: what the file says each animation plays), if one is;
      - a row naming another file (one of the unit's own clips made elsewhere: RUSE Decoy) stays as it is.
    A file of `before` that came in again under no name goes. Returns {"animations": [{"name", "frames", "seconds",
    "file"}], "actions": {each of `actions`: the animation its row names, the file's name for a clip of another kind,
    or None for none}, "dropped": [(action, the animation it played)] rows that went}."""
    from . import anim
    mod = Path(mod)
    if not anim._NAME.match(unit):
        raise AnimModelError(f"{unit!r} isn't a unit's name (letters, digits and _)")
    parsed = {}
    for name, data in clips.items():
        try:
            c = baf.parse(data)
            baf.check(c, max(baf.MOST_BONES, c.bones))
        except baf.ClipError as exc:
            raise AnimModelError(f"the animation {name}: {exc}") from None
        parsed[name] = c
    old = {a["file"]: a["name"] for a in before or [] if isinstance(a, dict) and a.get("file") and a.get("name")}
    table = anim.read_units(mod)
    u = {k: v for k, v in (table.get(unit) or {}).items()}
    files = file_names(list(clips), {f for f in anim._named_files(u) if f not in old})   # (never another's file)
    of_file = {f: name for name, f in files.items()}
    dropped = []

    def again(file, action):
        """A row's file as it is to be now: the new file of the animation it played, None when that one is gone."""
        if file not in old:
            return file
        new = files.get(old[file])
        if new is None:
            dropped.append((action, old[file]))
        return new
    acts = {a: f2 for a, f in (u.get("action") or {}).items() if (f2 := again(f, a))}
    figs = {}
    for fig, fv in (u.get("figure") or {}).items():
        kept = {a: f2 for a, f in ((fv or {}).get("action") or {}).items() if (f2 := again(f, a))}
        if kept:
            figs[fig] = {"action": kept}
    for action, name in actions_named([a for a in actions if a not in acts], list(clips), said).items():
        if name is not None:
            acts[action] = files[name]
    u["action"], u["figure"] = acts, figs
    u = {k: v for k, v in u.items() if v}
    if u:
        table[unit] = u
    else:
        table.pop(unit, None)
    folder = mod / anim.OWN / unit
    folder.mkdir(parents=True, exist_ok=True)
    for name, f in files.items():
        tmp = (folder / f).with_suffix(".part")
        tmp.write_bytes(clips[name])
        tmp.replace(folder / f)
    anim.write_units(mod, table)   # (checked as the build reads it before it takes the old one's place)
    taken = {f.lower() for f in files.values()}
    for f in old:
        if f.lower() not in taken:
            (folder / f).unlink(missing_ok=True)
    out = {"animations": [{"name": name, "frames": parsed[name].frames, "seconds": round(parsed[name].duration, 4),
                           "file": files[name]} for name in clips],
           "actions": {a: (of_file.get(acts[a], acts[a]) if a in acts else None) for a in actions},
           "dropped": dropped}
    return out


def drop_animations(mod, unit: str, before: list | None) -> list:
    """Take a model's animations out of the unit `unit`'s own clips (the model taken out, or one on other bones in
    its place): every row naming the file of one of `before` (the record's "animations") and those files. Returns the
    actions that played one."""
    from . import anim
    mod = Path(mod)
    old = {a["file"] for a in before or [] if isinstance(a, dict) and a.get("file")}
    if not old or not anim._NAME.match(unit):
        return []
    table = anim.read_units(mod)
    u = {k: v for k, v in (table.get(unit) or {}).items()}
    gone = [a for a, f in (u.get("action") or {}).items() if f in old]
    u["action"] = {a: f for a, f in (u.get("action") or {}).items() if f not in old}
    figs = {}
    for fig, fv in (u.get("figure") or {}).items():
        acts = {a: f for a, f in ((fv or {}).get("action") or {}).items() if f not in old}
        gone += [a for a, f in ((fv or {}).get("action") or {}).items() if f in old]
        if acts:
            figs[fig] = {"action": acts}
    u["figure"] = figs
    u = {k: v for k, v in u.items() if v}
    if u:
        table[unit] = u
    else:
        table.pop(unit, None)
    anim.write_units(mod, table)
    named = anim._named_files(u) if u else set()
    for f in old:
        if f not in named:
            (mod / anim.OWN / unit / f).unlink(missing_ok=True)
    return sorted(set(gone))


# --- what a model's file says of itself ---
def file_document(path) -> dict:
    """A .glb's or .gltf's JSON part (its pictures and buffers not read)."""
    import json
    import struct
    path = Path(path)
    try:
        if path.suffix.lower() == ".gltf":
            return json.loads(path.read_text(encoding="utf-8"))
        with open(path, "rb") as f:
            head = f.read(20)
            if len(head) < 20 or head[:4] != b"glTF":
                raise AnimModelError(f"{path.name}: not a .glb file")
            length, kind = struct.unpack_from("<I4s", head, 12)
            if kind != b"JSON":
                raise AnimModelError(f"{path.name}: a .glb without its JSON part first")
            return json.loads(f.read(length))
    except (OSError, ValueError, struct.error) as exc:
        raise AnimModelError(f"{path.name}: {exc}") from None


def file_says(doc: dict, names: list) -> tuple[list, dict | None]:
    """What a model's file says of its animations and halves: (for each of `names`, its animations as rusemod.rig
    read them in the file's order, the actions its extras list or None; its halves {"top": [bones], "bottom":
    [bones]} from its extras, or None)."""
    anims = doc.get("animations") or []
    said, k = [], 0
    for name in names:   # (the rig keeps the file's order, leaving out an animation that moves no bone)
        found = None
        while k < len(anims):
            a = anims[k]
            k += 1
            if (a.get("name") or f"animation {k}") == name:
                listed = (a.get("extras") or {}).get(ACTIONS_EXTRA)
                found = [str(x) for x in listed] if isinstance(listed, list) else None
                break
        said.append(found)
    halves = ((doc.get("asset") or {}).get("extras") or {}).get(HALVES_EXTRA)
    ok = isinstance(halves, dict) and all(isinstance(halves.get(h), list) for h in ("top", "bottom"))
    return said, ({h: [str(b).lower() for b in halves[h]] for h in ("top", "bottom")} if ok else None)


def own_bones_on(game, path, models: list) -> str | None:
    """The model of a unit's `models` (in the order Import model tries them) that a model file on bones of its own takes
    the place of: the first the game draws with bones, when the bones the file's points lean on aren't all the bones
    of any of them (a file whose points lean only on one model's bones is rigged to it: rusemod.unitmodel's rigged
    way). None for a file whose points lean on no bone, or on one of the models' own."""
    from .build import find_pack
    from .edat import Edat
    from .modelin import read_model
    from .unitmodel import UnitModelError, find_source, pack_names
    used = {n.lower() for m in read_model(Path(path), skin=True).meshes for v in m.skin for n, _w in v}
    if not used:
        return None
    found = find_pack(Path(game), "ZZ_Win.dat")
    if found is None:
        return None
    zz = Edat.open(str(found))
    try:
        names = pack_names(zz)
        first = None
        for model in models:
            try:
                bones = {n.lower() for n in find_source(zz, model, names, rigged=True).skeleton.names}
            except UnitModelError:   # (drawn with no bones: nothing for a model's own bones to take the place of)
                continue
            if used <= bones:
                return None
            first = first or model
        return first
    finally:
        zz.close()


def record_of(path) -> bytes:
    """The skeleton record of a model on bones of its own, from the mod's file of it (files/models/<unit>.glb) as the
    build writes it (rusemod.unitmodel.read_mod_glb's): the record the file carries while its bones still match it,
    else worked out from them. Its animations aren't read."""
    from .modelin import ModelError, glb_document
    from .rig import rig_of
    from .unitmodel import own_skeleton
    path = Path(path)
    try:
        doc, binary = glb_document(path.read_bytes())
        doc = {k: v for k, v in doc.items() if k != "animations"}
        return own_skeleton(rig_of(doc, binary, path.name))[0]
    except (OSError, ValueError, ModelError, KeyError, IndexError) as exc:
        raise AnimModelError(f"{path.name}: its own skeleton can't be read: {exc}") from None


# --- the halves ---
def default_split(record: bytes) -> str:
    """The bone a model on bones of its own is split at when nothing says where: its first (every bone in the top)."""
    return baf.skeleton(record)["names"][0]


def split_of(record: bytes, halves: dict) -> str | None:
    """The bone the two halves a file names ({"top": [bones], "bottom": [bones]}) meet at: the top half's one bone
    whose parent isn't in it, when the top half is that bone and every bone under it and the bottom half the rest;
    None when they don't split the skeleton so."""
    sk = baf.skeleton(record)
    names = [n.lower() for n in sk["names"]]
    top = {n.lower() for n in halves.get("top") or []}
    if not top or not top <= set(names) or set(names) - top != {n.lower() for n in halves.get("bottom") or []}:
        return None
    roots = [b for b, n in enumerate(names) if n in top and (sk["parents"][b] < 0 or names[sk["parents"][b]] not in top)]
    if len(roots) != 1:
        return None
    from .unitmodel import halves as split_halves
    got = split_halves(record, names[roots[0]])
    return names[roots[0]] if set(got["top"]["Weights"]) == top else None


def halves_for(record: bytes, split: str | None) -> tuple[dict, list]:
    """The model's two halves (rusemod.unitmodel.halves) split at `split` (the record's), else at default_split; and
    what is to be said (a split at a bone it hasn't got, a half with no bone)."""
    from .unitmodel import UnitModelError, halves
    notes = []
    names = baf.skeleton(record)["names"]
    if split and split.lower() not in [n.lower() for n in names]:
        notes.append(f"its halves were to meet at {split}, a bone it hasn't got: every bone is in the top half")
        split = None
    try:
        got = halves(record, split or default_split(record))
    except UnitModelError as exc:   # (not reached: the bone is checked above)
        raise AnimModelError(str(exc)) from None
    if not split:
        notes.append("no bone is chosen where its two halves meet: every bone is in the top half, so its top "
                     "animations move the whole model (not tried in the game yet)")
    return got, notes + got["notes"]


# --- the build: the listings of the figures that wear the model, through its own two halves ---
def _figures(objects, v, path: str, depth: int = 0, seen=frozenset()):
    """(path, object) of each object holding clip listings (ResourceAnimation) under the value `v` of a unit, its
    unnamed parts followed, never another named object (as rusemod.anim.own_listings walks a unit)."""
    from .patch import Inline, ListV, MapV, PairV, Ref
    if depth > 24:
        return
    if isinstance(v, Ref):
        if v.target in objects and not v.target.startswith("$/") and v.target not in seen:
            yield from _obj_figures(objects, objects[v.target], path, depth + 1, seen | {v.target})
    elif isinstance(v, Inline):
        yield from _obj_figures(objects, v.obj, path, depth + 1, seen)
    elif isinstance(v, ListV):
        for i, x in enumerate(v.items):
            yield from _figures(objects, x, f"{path}[{i}]", depth + 1, seen)
    elif isinstance(v, MapV):
        for i, (_k, x) in enumerate(v.pairs):
            yield from _figures(objects, x, f"{path}[{i}].v", depth + 1, seen)
    elif isinstance(v, PairV):
        yield from _figures(objects, v.a, path, depth + 1, seen)
        yield from _figures(objects, v.b, path, depth + 1, seen)


def _obj_figures(objects, obj, path: str, depth: int, seen):
    from .patch import MapV
    if isinstance(obj.props.get("ResourceAnimation"), MapV):
        yield path, obj
    for p, w in obj.props.items():
        if p != "ResourceAnimation":
            yield from _figures(objects, w, f"{path}.{p}" if path else p, depth, seen)


def _part(objects, v):
    from .patch import Inline, Ref
    if isinstance(v, Inline):
        return v.obj
    return objects.get(v.target) if isinstance(v, Ref) and v.target else None


def wears(objects, figure, model: str) -> bool:
    """Whether a figure (an object with clip listings) draws the model `model` (its MeshDescriptor's file, any case)."""
    from .patch import Text
    from .unitmodel import model_key
    mesh = _part(objects, figure.props.get("MeshDescriptor"))
    f = mesh.props.get("FileName") if mesh is not None else None
    return isinstance(f, Text) and model_key(f.value) == model_key(model)


def _names_bones(objects, mask_value) -> bool:
    """Whether a listing's Mask value is a mask that weighs bones by name (a mask with none weighs them alike)."""
    from .patch import MapV
    mask = _part(objects, mask_value)
    w = mask.props.get("Weights") if mask is not None else None
    return isinstance(w, MapV) and bool(w.pairs)


def _half_of(key) -> str:
    """"bottom" for a listing of a b_ action, else "top"."""
    from .patch import Text
    return "bottom" if isinstance(key, Text) and key.value.lower().startswith("b_") else "top"


def figures_of(game, name: str) -> list:
    """[(path, object)] of every figure of the unit `name` (each part of its GfxDescriptor* with clip listings)."""
    unit = game.objects[name]
    return [f for p in unit.props if p.startswith("GfxDescriptor") for f in _figures(game.objects, unit.props[p], p)]


def game_masks(game, name: str, model: str) -> dict:
    """{"top": , "bottom": } the masks (top-level objects' names) a t_ and a b_ listing of the unit `name`'s figures
    that wear `model` name now, among those that weigh bones by name (None where none does): what mask_object copies."""
    from .patch import Ref
    objects = game.objects
    found = {"top": None, "bottom": None}
    for _path, fig in figures_of(game, name):
        if not wears(objects, fig, model):
            continue
        for k, x in fig.props["ResourceAnimation"].pairs:
            a = _part(objects, x)
            m = a.props.get("Mask") if a is not None else None
            if isinstance(m, Ref) and _names_bones(objects, m):
                found[_half_of(k)] = found[_half_of(k)] or m.target
    return found


def mask_object(game, like: str | None, half: dict, cls: str = "THierarchicalASEModelSkeletonMask"):
    """A mask object for one of a model's halves (rusemod.unitmodel.halves' "top" or "bottom": MaskUnionCode,
    AnimationSlot, Weights {bone: weight}): a copy of the game's mask `like` (a top-level object's name), its numbers
    and names in the kinds the game's has them and its Weights the half's; without one, made as the game's top and
    bottom masks are (MaskUnionCode, AnimationSlot, Weights as a map of names to weights)."""
    from decimal import Decimal

    from .patch import MapV, Num, Obj, Text, _fresh
    base = game.objects.get(like) if like else None
    obj = _fresh(base) if base is not None and base.cls == cls else Obj(cls, {})
    kinds = {p: v.kind for p, v in obj.props.items() if isinstance(v, Num)}
    old = obj.props.get("Weights")
    key_kind, weight_kind = "string", "float32"
    if isinstance(old, MapV) and old.pairs:
        k0, v0 = old.pairs[0]
        key_kind = k0.kind if isinstance(k0, Text) else key_kind
        weight_kind = v0.kind if isinstance(v0, Num) else weight_kind
    obj.props["MaskUnionCode"] = Num(kinds.get("MaskUnionCode", "uint32"), Decimal(int(half["MaskUnionCode"])))
    if "AnimationSlot" in half:
        obj.props["AnimationSlot"] = Num(kinds.get("AnimationSlot", "int32"), Decimal(int(half["AnimationSlot"])))
    else:
        obj.props.pop("AnimationSlot", None)
    obj.props.pop("DefaultWeight", None)
    obj.props["Weights"] = MapV([(Text(key_kind, bone), Num(weight_kind, Decimal(repr(float(w)))))
                                 for bone, w in half["Weights"].items()])
    return obj


def point_masks(game, name: str, model: str, masks: dict) -> dict:
    """Point every clip listing of the unit `name` (a top-level object of the build's rusemod.patch.Game) on a figure
    that wears `model` at `masks`["top"] (a listing of a t_ action, or of one with no half) or `masks`["bottom"] (b_),
    each a top-level object's name, when the listing's mask weighs bones by name (one that names none, or no mask,
    stays). A part the unit shares with other units is copied into it first (as rusemod.anim.own_listings does), so
    they keep the game's. Returns {"figures": [paths of the figures that wear it], "pointed": how many listings now
    name one of the two, "others": [(figure path, action, FileName)] of the listings on the unit's figures that don't
    wear it}."""
    from .patch import Inline, ListV, MapV, PairV, Ref, Text, _fresh
    objects = game.objects

    def changes(fig) -> bool:
        if not wears(objects, fig, model):
            return False
        for k, x in fig.props["ResourceAnimation"].pairs:
            a = _part(objects, x)
            m = a.props.get("Mask") if a is not None else None
            if _names_bones(objects, m) and not (isinstance(m, Ref) and m.target == masks[_half_of(k)]):
                return True
        return False

    pointed = 0

    def point(v, path, put, depth=0, seen=frozenset()) -> None:
        nonlocal pointed
        if not any(changes(fig) for _p, fig in _figures(objects, v, path, depth, seen)):
            return
        if isinstance(v, Ref):
            seen = seen | {v.target}
            v = Inline(_fresh(objects[v.target]))   # the unit's own copy of a part others link to as well
            put(v)
        if isinstance(v, Inline):
            obj = v.obj
            ra = obj.props.get("ResourceAnimation")
            if isinstance(ra, MapV) and changes(obj):
                for i, (k, x) in enumerate(ra.pairs):
                    a = _part(objects, x)
                    m = a.props.get("Mask") if a is not None else None
                    if not _names_bones(objects, m) or (isinstance(m, Ref) and m.target == masks[_half_of(k)]):
                        continue
                    own = Inline(_fresh(a)) if isinstance(x, Ref) else x   # (its own copy of the listing)
                    own.obj.props["Mask"] = Ref(masks[_half_of(k)])
                    ra.pairs[i] = (k, own)
                    pointed += 1
            for p, w in list(obj.props.items()):
                if p != "ResourceAnimation":
                    point(w, f"{path}.{p}" if path else p, lambda x, p=p, o=obj: o.props.__setitem__(p, x),
                          depth + 1, seen)
        elif isinstance(v, ListV):
            for i, x in enumerate(v.items):
                point(x, f"{path}[{i}]", lambda y, i=i: v.items.__setitem__(i, y), depth + 1, seen)
        elif isinstance(v, MapV):
            for i, (k, x) in enumerate(v.pairs):
                point(x, f"{path}[{i}].v", lambda y, i=i, k=k: v.pairs.__setitem__(i, (k, y)), depth + 1, seen)
        elif isinstance(v, PairV):
            point(v.a, path, lambda y: setattr(v, "a", y), depth + 1, seen)
            point(v.b, path, lambda y: setattr(v, "b", y), depth + 1, seen)

    if any(changes(fig) for _p, fig in figures_of(game, name)):
        unit = game.own(name)   # (one of the game's: copied before it changes)
        for p in [p for p in unit.props if p.startswith("GfxDescriptor")]:
            point(unit.props[p], p, lambda x, p=p: unit.props.__setitem__(p, x))
    figures, others = [], []
    for path, fig in figures_of(game, name):
        if wears(objects, fig, model):
            figures.append(path)
            continue
        for k, x in fig.props["ResourceAnimation"].pairs:
            a = _part(objects, x)
            f = a.props.get("FileName") if a is not None else None
            if isinstance(f, Text):
                others.append((path, k.value if isinstance(k, Text) else "", f.value))
    return {"figures": figures, "pointed": pointed, "others": others}


# --- the unit's actions, from the game's index ---
def unit_figures(db, unit: str) -> list:
    """[(figure path, the model file it wears (lower case), [its actions in the game's order])] of the game's unit
    `unit` (its address), from the game index `db`: each part reached from the unit's GfxDescriptor* links that lists
    clips (ResourceAnimation), its unnamed parts followed and never a named object (another unit, a shared drawer), as
    the build walks a unit (rusemod.anim.own_listings). A part the unit shares with another is found by its link,
    whichever unit's address the index files it under."""
    row = db.execute("SELECT id FROM object WHERE address = ? AND shadow = 0", (unit,)).fetchone()
    if row is None:
        return []
    todo = [(dst, path) for path, dst in db.execute("SELECT path, dst FROM ref WHERE src = ?", (row[0],))
            if path and path.startswith("GfxDescriptor")]
    out, seen = [], set()
    while todo:
        oid, path = todo.pop(0)
        if oid is None or oid in seen or len(seen) > 20000:
            continue
        seen.add(oid)
        named = db.execute("SELECT export FROM object WHERE id = ?", (oid,)).fetchone()
        if named is None or named[0]:
            continue
        refs = db.execute("SELECT path, dst FROM ref WHERE src = ?", (oid,)).fetchall()
        listed = [(p, d) for p, d in refs if p and p.startswith("ResourceAnimation[") and p.endswith("].v")]
        if listed:
            mesh = next((d for p, d in refs if p == "MeshDescriptor"), None)
            got = db.execute("SELECT text FROM value WHERE object = ? AND path = 'FileName'", (mesh,)).fetchone() \
                if mesh is not None else db.execute("SELECT text FROM value WHERE object = ? AND path = "
                                                    "'MeshDescriptor.FileName'", (oid,)).fetchone()
            actions = []
            for p, _d in sorted(listed, key=lambda r: int(re.search(r"\[(\d+)\]", r[0]).group(1))):
                k = db.execute("SELECT text FROM value WHERE object = ? AND path = ?", (oid, p[:-2] + ".k")).fetchone()
                if k and k[0] and k[0] not in actions:
                    actions.append(k[0])
            out.append((path, (got[0] if got and got[0] else "").replace("/", "\\").lower(), actions))
        todo += [(d, f"{path}.{p}") for p, d in refs if p and not p.startswith("ResourceAnimation[")]
    return out
