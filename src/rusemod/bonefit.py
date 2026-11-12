"""Whether a model's bones fit what plays on it and what hangs on it, and where a model on bones of its own splits into
the two halves a soldier's animations play on (the owner's 7, 2026-11-10: "Yes, seven should warn them. If it's gonna
break, and then tell them how to fix it. And what's the issue is. Should be intuitive.").

Used by the build (rusemod.build.unit_fit_checks: warnings in its report) and by the Studio's unit page
(ruse_studio.modelfit: the same checks in the page's words, and the split chosen there). Every check is a warning,
never a refusal. What each one rests on:

  an animation's bones  The game plays an animation on a model bone by bone, in the animation's own order, as many bones
                        as the model has, and never looks at their names: each of the game's clips carries the bones of
                        the model it was made for (rusemod.baf). So an animation with fewer bones than its model is read
                        past its end: the game stopped on one in the owner's horse test of 2026-11-09 (the game's horse
                        standing, 36 bones, played on a figure of 41). One with more bones than its model puts its
                        bones past the model's (not tried in the game). One with as many bones but other names, or the
                        same names in another order, moves the wrong bones (not tried in the game).
  a bone a shot needs   A firing animation starts its shot on a bone the unit's data names (Fx_Tir_01 on a rifle,
                        Fx_Tir_02 on a bazooka, Bip01 L Hand for a grenade). On a model without it the unit fires with
                        no shot to be seen: the owner saw it on 2026-11-09.
  a bone a part needs   A figure's parts hang on bones by name: the upper body that turns toward its target (Bip01
                        Spine), a weapon shown and hidden (Arme_1), a turret, a wheel, a person or a muzzle held on a
                        bone. A part whose bone the model hasn't got isn't made, and the game is expected to stop with
                        an error box (not tried in the game for one bone missing alone; a figure none of whose parts
                        was made stopped the game on 2026-11-09).
  the halves            Each half (a mask) weighs bones by name, and a name its model hasn't got is expected to stop
                        the game with an error box (not tried in the game). The game adds the two halves' weights up and
                        never divides: a bone weighed 1 in both is moved twice over, its children more, and the horses
                        of 2026-11-09 came out as big as the map that way.
  more than 64 bones    The game isn't seen to animate a model with more (rusemod.unitmodel.MOST_ANIMATED; not tried in
                        the game).

The split: a model on bones of its own plays one animation on its upper half (aiming, firing) and one on its lower half
(walking, running) at once, as a soldier does, and splits at one bone: that bone and every bone under it are the upper
half (rusemod.unitmodel.halves). The modder picks the bone on the unit's page; it is kept as "split" in the model's
record (files/models/<the unit's name>.json, beside its .glb) and the build takes it (split_for). suggest_split gives
the one shown first: the rider's own first bone on a horse with a rider (where the owner's Horse Squad of 2026-11-09
split), else the first spine bone (a soldier's way), else where the skeleton first branches. A model on the game
soldier's bones keeps the game's own halves."""
from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

from . import baf

MOST_ANIMATED = 64    # rusemod.unitmodel.MOST_ANIMATED: the most bones a model the game animates is seen to have
TOP_MASK, BOTTOM_MASK = 65280, 255   # the two halves' MaskUnionCode (rusemod.unitmodel)
RECORD = ".json"      # files/models/<the unit's name>.json beside its .glb: the model's record (the Studio's)
SPLIT = "split"       # the record's chosen bone
SUM_MOST = 1.01       # a bone's two halves weighing more than this together is moved more than once over

# what the game's data names a bone for, by the class and the property that name it: every one of them sits in a
# figure's parts (SousElements, a wheel list) or in an event of one of its animations (the plain game's data,
# 2026-11-10: 7,248 such names)
NEEDS = {
    "TActionDescriptorLaunchEffetOnSousMobile": (("SousMobile", "shot"),),          # a shot starts there
    "TGfxDescriptorCompensationBoneOperator": (("SousMobileName", "turn"),),        # the upper body turns at it
    "TGfxDescriptorVisibilityBoneOperator": (("SousMobileName", "show"),),          # a weapon shown or hidden
    "TGfxDescriptorModeleSousMobile": (("SousMobileName", "hold"),),                # a part held on it
    "TGfxDescriptorTourelle": (("SousMobileName", "turret"),),                      # a turret turns there
    "TGfxDescriptorBoneOperator": (("SousMobileName", "move"),),                    # a part moved there
    "TGfxDescriptorChassis": (("NameBone", "body"),),                               # the body rests on it
    "TGfxDescriptorRoue": (("NameBone", "wheel"),),                                 # a wheel turns there
    "TGfxDescriptorHook": (("ChassisBoneName", "hook"), ("HookBoneName", "hook")),  # a towed gun's hook
}
SHOT = "shot"
CLIP_ROOT = "genanim_15\\"


class FitError(ValueError):
    pass


# --- a skeleton ---
def skeleton_of(record: bytes) -> tuple[list, list]:
    """(bone names in lower case, parents) of a skeleton record (rusemod.baf.skeleton's layout)."""
    sk = baf.skeleton(record)
    return [n.lower() for n in sk["names"]], list(sk["parents"])


def clip_bones(raw: bytes) -> list | None:
    """An animation clip's bones by number, in lower case (the bones of the model it was made for); None for bytes
    that aren't a clip."""
    try:
        return [n.lower() for n in baf.skeleton(baf.parse(raw).skeleton)["names"]]
    except (baf.ClipError, ValueError, IndexError, UnicodeDecodeError, struct.error):
        return None


def under(parents: list, bone: int) -> set:
    """`bone` and every bone hanging from it."""
    out = {bone}
    grew = True
    while grew:      # (parents come first in every record: once round is enough; the loop guards any other order)
        grew = False
        for b, p in enumerate(parents):
            if p in out and b not in out:
                out.add(b)
                grew = True
    return out


def depths(parents: list) -> list:
    out = []
    for b in range(len(parents)):
        d, p = 0, parents[b]
        while p >= 0 and d <= len(parents):
            d, p = d + 1, parents[p]
        out.append(d)
    return out


# --- the split ---
_FAMILY = re.compile(r"[\s:_.\-|]+")


def _family(name: str) -> str:
    """A bone name's first word: "horse l thigh" -> "horse", "bip01 pelvis" -> "bip01", "fx_tir_01" -> "fx"."""
    return _FAMILY.split(name.strip().lower(), 1)[0]


def suggest_split(names: list, parents: list) -> str:
    """The bone a model on bones of its own is suggested to split at (the module's note): the first bone of a second
    body hanging on the first (its own bones' names start apart from the rest, and it has a head: the rider on the
    owner's Horse Squad of 2026-11-09, his bip01 on the horse's back), else the first bone named spine (a soldier's
    upper half from the spine up), else the child with the most bones under it where the skeleton first branches,
    else the first bone."""
    low = [n.lower() for n in names]
    if not low:
        raise FitError("a skeleton with no bones")
    depth = depths(parents)
    order = sorted(range(len(low)), key=lambda b: (depth[b], b))
    every = set(range(len(low)))
    for b in order:
        if parents[b] < 0:
            continue
        mine = under(parents, b)
        inside = {_family(low[k]) for k in mine}
        outside = {_family(low[k]) for k in every - mine}
        if outside and not inside & outside and any("head" in low[k] for k in mine) \
                and any("head" in low[k] for k in every - mine):
            return low[b]
    for b in order:
        if "spine" in low[b]:
            return low[b]
    for b in order:
        children = [k for k, p in enumerate(parents) if p == b]
        if len(children) >= 2:
            return low[max(children, key=lambda k: (len(under(parents, k)), -k))]
    return low[order[0]]


def halves_of(names: list, parents: list, split: str) -> dict:
    """{"split": the bone, "top": its bones in the upper half, "bottom": the rest, in bone order}; a FitError when the
    skeleton has no such bone."""
    low = [n.lower() for n in names]
    if split.lower() not in low:
        # not a game rule: a half starts at one of the model's own bones
        raise FitError(f"the model has no bone called {split}")
    top = under(parents, low.index(split.lower()))
    return {"split": split.lower(), "top": [low[b] for b in sorted(top)],
            "bottom": [low[b] for b in range(len(low)) if b not in top]}


def chosen_split(names: list, parents: list, saved: str | None) -> tuple[str, list]:
    """(the bone the model splits at, problems): the one saved (`saved`, the record's "split") while the model still has
    it, else suggest_split; a problem when the saved one is gone, and when the split leaves the lower half empty."""
    low = [n.lower() for n in names]
    problems = []
    split = saved.lower() if isinstance(saved, str) and saved.strip() else None
    if split is not None and split not in low:
        problems.append({"kind": "split_gone", "level": "note", "seen": False, "split": saved,
                         "used": suggest_split(low, parents)})
        split = None
    if split is None:
        split = suggest_split(low, parents)
    if len(under(parents, low.index(split))) == len(low):
        problems.append({"kind": "split_all_top", "level": "note", "seen": False, "split": split})
    return split, problems


def model_record(glb: Path) -> dict:
    """The model's record beside its file (files/models/<unit>.json), {} when there is none or it can't be read."""
    try:
        data = json.loads(Path(glb).with_suffix(RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def glb_record(glb: Path) -> bytes | None:
    """The skeleton record of a mod's model on bones of its own (files/models/<unit>.glb, rusemod.modelin.write_glb's
    with its record in its skin), None for a model on another unit's bones or none."""
    from .modelin import OWN_SKELETON, ModelError
    from .rig import read_rig
    from .unitmodel import glb_report
    if not glb_report(glb).get(OWN_SKELETON):
        return None
    try:
        return read_rig(glb).record()
    except (ModelError, OSError, ValueError, baf.ClipError):
        return None


def skeleton_key(glb: Path) -> tuple | None:
    """A mod's model on bones of its own as (its bone names in lower case, their parents), to tell whether two models
    are on the same bones (a squad's riflemen's and its bazooka man's: the unit's own animations and halves are made
    on one skeleton); None for a model on another unit's bones, or a file that can't be read."""
    record = glb_record(Path(glb))
    if record is None:
        return None
    try:
        names, parents = skeleton_of(record)
    except (ValueError, KeyError, IndexError, UnicodeDecodeError, struct.error):
        return None
    return tuple(names), tuple(parents)


def split_for(glb: Path) -> str | None:
    """The bone the build splits a mod's model on bones of its own at (rusemod.unitmodel.halves): the one the modder
    chose on the unit's page while the model still has it, else suggest_split's; None for any other model."""
    record = glb_record(glb)
    if record is None:
        return None
    names, parents = skeleton_of(record)
    return chosen_split(names, parents, model_record(glb).get(SPLIT))[0]


def halves_for(glb: Path) -> dict | None:
    """The two halves (masks) the build writes for a mod's model on bones of its own: rusemod.unitmodel.halves at
    split_for's bone ({"split", "top", "bottom", "notes"}); None for any other model."""
    from .unitmodel import halves
    record = glb_record(glb)
    if record is None:
        return None
    names, parents = skeleton_of(record)
    return halves(record, chosen_split(names, parents, model_record(glb).get(SPLIT))[0])


def save_split(glb: Path, bone: str | None) -> None:
    """Keep `bone` as the split in the model's record (None or "": back to the suggested one). The record is the
    Studio's (files/models/<unit>.json); one that isn't there is made with the split alone."""
    path = Path(glb).with_suffix(RECORD)
    data = model_record(glb)
    if bone:
        data[SPLIT] = bone.lower()
    else:
        data.pop(SPLIT, None)
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(path)


# --- a unit's figures: the model each draws, its animations by action, the bones its parts and shots need ---
@dataclass
class Mask:
    code: int                     # MaskUnionCode: 65280 the upper half, 255 the lower
    default: float = 0.0          # DefaultWeight: every bone not named
    weights: dict | None = None   # {bone name as the data gives it: weight}; None when not known (the game index)


@dataclass
class Figure:
    path: str                     # from the unit: "GfxDescriptorFusilier", "GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"
    model: str                    # its MeshDescriptor's FileName as the data gives it ("" without one)
    listings: list = field(default_factory=list)   # [(action, the clip's FileName, Mask or None)]
    needs: list = field(default_factory=list)      # [(bone as the data gives it, what for: NEEDS)]


def _step(path: str, prop: str) -> str:
    return f"{path}.{prop}" if path else prop


def data_figures(game, name: str) -> list:
    """The figures of the unit `name` (a top-level object of `game`, a rusemod.patch.Game: the build's data), every
    object with a model (MeshDescriptor) under its GfxDescriptor* parts. Only the unit's own parts and the unnamed parts
    under them are walked (a named object of the game's isn't), but a listing, its mask and a model part are read
    wherever they are. A part found under a figure needs that figure's bones; a figure under another (a person on a
    bone) is a figure of its own."""
    from .patch import Inline, ListV, MapV, Num, PairV, Ref, Text
    objects = game.objects

    def target(v, named: bool = False):
        if isinstance(v, Inline):
            return v.obj
        if isinstance(v, Ref) and v.target in objects and (named or not v.target.startswith("$/")):
            return objects[v.target]
        return None

    def number(v, default=0.0) -> float:
        return float(v.value) if isinstance(v, Num) else default

    def mask_of(v) -> Mask | None:
        m = target(v, named=True)
        if m is None:
            return None
        w = m.props.get("Weights")
        weights = {}
        for k, x in (w.pairs if isinstance(w, MapV) else []):
            if isinstance(k, Text):
                weights[k.value] = number(x, 1.0)
        return Mask(int(number(m.props.get("MaskUnionCode"))), number(m.props.get("DefaultWeight")), weights)

    out: list = []

    def visit(obj, path: str, depth: int, seen: frozenset, holder) -> None:
        if depth > 24:
            return
        if "MeshDescriptor" in obj.props:
            mesh = target(obj.props["MeshDescriptor"], named=True)
            f = mesh.props.get("FileName") if mesh is not None else None
            holder = Figure(path, f.value if isinstance(f, Text) else "")
            ra = obj.props.get("ResourceAnimation")
            for k, v in (ra.pairs if isinstance(ra, MapV) else []):
                a = target(v, named=True)
                if a is None or not isinstance(k, Text):
                    continue
                fn = a.props.get("FileName")
                holder.listings.append((k.value, fn.value if isinstance(fn, Text) else "", mask_of(a.props.get("Mask"))))
            out.append(holder)
        if holder is not None:
            for prop, why in NEEDS.get(obj.cls, ()):
                t = obj.props.get(prop)
                if isinstance(t, Text) and t.value:
                    holder.needs.append((t.value, why))
        for p, w in obj.props.items():
            if p in ("MeshDescriptor", "Mask"):
                continue
            named = p == "ResourceAnimation"     # (a listing may be a named object: its events are the figure's)
            walk(w, _step(path, p), depth + 1, seen, holder, named)

    def walk(v, path: str, depth: int, seen: frozenset, holder, named: bool = False) -> None:
        if isinstance(v, (Inline, Ref)):
            obj = target(v, named)
            if obj is not None and id(obj) not in seen:
                visit(obj, path, depth, seen | {id(obj)}, holder)
        elif isinstance(v, ListV):
            for i, x in enumerate(v.items):
                walk(x, f"{path}[{i}]", depth, seen, holder, named)
        elif isinstance(v, MapV):
            for i, (_k, x) in enumerate(v.pairs):
                walk(x, f"{path}[{i}].v", depth, seen, holder, named)
        elif isinstance(v, PairV):
            walk(v.a, path, depth, seen, holder, named)
            walk(v.b, path, depth, seen, holder, named)

    unit = objects[name]
    # (and a squad's soldiers' own figures, R2SoldierLooks: rusemod.squads)
    for p in [p for p in unit.props if p.startswith("GfxDescriptor") or p == "R2SoldierLooks"]:
        walk(unit.props[p], p, 0, frozenset(), None)
    return out


def index_figures(db, address: str) -> list:
    """data_figures from the game index (rusemod.index's sqlite, `db`) for the unit at `address`: the game's own
    data as shipped, so a mod's changes to the unit aren't in it, and a mask's weights aren't kept there (Mask.weights
    None). [] for a unit the index hasn't got."""
    row = db.execute("SELECT id FROM object WHERE (address = ? OR export = ?) ORDER BY shadow LIMIT 1",
                     (address, address)).fetchone()
    if row is None:
        return []
    out: list = []

    def info(oid):
        return db.execute("SELECT class, export FROM object WHERE id = ?", (oid,)).fetchone()

    def text(oid, prop):
        r = db.execute("SELECT text FROM value WHERE object = ? AND path = ?", (oid, prop)).fetchone()
        return r[0] if r and r[0] is not None else None

    def num(oid, prop, default=0.0):
        r = db.execute("SELECT num FROM value WHERE object = ? AND path = ?", (oid, prop)).fetchone()
        return float(r[0]) if r and r[0] is not None else default

    def links(oid):
        return db.execute("SELECT path, dst FROM ref WHERE src = ? AND dst IS NOT NULL ORDER BY rowid", (oid,)).fetchall()

    def visit(oid, path: str, depth: int, seen: frozenset, holder) -> None:
        got = info(oid)
        if depth > 24 or got is None:
            return
        cls = got[0]
        refs = links(oid)
        mesh = next((d for p, d in refs if p == "MeshDescriptor"), None)
        if mesh is not None:
            holder = Figure(path, text(mesh, "FileName") or "")
            for p, d in refs:
                m = re.fullmatch(r"ResourceAnimation\[(\d+)\]\.v", p)
                if m is None:
                    continue
                key = text(oid, f"ResourceAnimation[{m[1]}].k")
                mask = next((x for q, x in links(d) if q == "Mask"), None)
                holder.listings.append((key or "", text(d, "FileName") or "",
                                        Mask(int(num(mask, "MaskUnionCode")), num(mask, "DefaultWeight"))
                                        if mask is not None else None))
            out.append(holder)
        if holder is not None:
            for prop, why in NEEDS.get(cls, ()):
                t = text(oid, prop)
                if t:
                    holder.needs.append((t, why))
        for p, d in refs:
            if p == "MeshDescriptor" or p == "Mask" or d in seen:
                continue
            c = info(d)
            if c is None:
                continue
            listing = p.startswith("ResourceAnimation[")
            if c[1] and not listing:      # a named object of the game's: not the unit's own part
                continue
            visit(d, _step(path, p), depth + 1, seen | {d}, holder)

    unit = row[0]
    for p, d in links(unit):
        if p.startswith("GfxDescriptor") and "." not in p and "[" not in p:
            c = info(d)
            if c is not None and not c[1]:
                visit(d, p, 0, frozenset({unit, d}), None)
    return out


# --- the checks ---
def clip_fit(model: list, clip: list) -> dict | None:
    """How an animation's bones (`clip`: its bone names by number) fit a model's (`model`): None when they're the
    same, else {"how": "fewer" | "more" (than the model has) | "names" (as many, other names) | "order" (the same names
    in another order), "clip_bones", "model_bones", "examples": [[the animation's bone, the model's]] (names: the
    first few that differ)}."""
    a, b = [n.lower() for n in clip], [n.lower() for n in model]
    if a == b:
        return None
    out = {"clip_bones": len(a), "model_bones": len(b), "examples": []}
    if len(a) < len(b):
        return dict(out, how="fewer")
    if len(a) > len(b):
        return dict(out, how="more")
    if sorted(a) == sorted(b):
        return dict(out, how="order")
    return dict(out, how="names", examples=[[x, y] for x, y in zip(a, b) if x != y][:3])


def clip_level(how: str) -> tuple[str, bool]:
    """(what the game does with such an animation: "stops" or "wrong", whether that was seen in the game)."""
    return ("stops", True) if how == "fewer" else ("stops", False) if how == "more" else ("wrong", False)


def check_figure(model: list, fig: Figure, bones_of, own=lambda _clip: False, masks: bool = True) -> list:
    """The problems of one figure drawing a model whose bones are `model` (names by number): the animations it plays
    whose bones don't fit (`bones_of(FileName)`: that clip's bones, None when not known; `own(FileName)`: whether it's
    the mod's own animation, not the game's), those that don't fit the same way said together (a figure still playing
    the game soldier's 32 clips is one problem, not 32), each bone its parts and shots need that the model hasn't got,
    and (with `masks`, the build's data) halves naming bones the model hasn't got or weighing a bone more than once over.
    Problems are dicts: {"kind", "level": "stops" | "wrong" | "unseen" | "untried" | "note", "seen": whether it was
    seen in the game, "figure": its path, ...}; an animation problem's "clips" [FileName] and "actions" [action]."""
    have = {n.lower() for n in model}
    out = []
    by_clip: dict = {}
    for action, file, _mask in fig.listings:
        if file:
            by_clip.setdefault(file, []).append(action)
    together: dict = {}
    for file, actions in by_clip.items():
        bones = bones_of(file)
        if bones is None:
            continue
        fit = clip_fit(model, bones)
        if fit is None:
            continue
        key = (fit["how"], fit["clip_bones"], bool(own(file)))
        if key not in together:
            level, seen = clip_level(fit["how"])
            together[key] = dict(fit, kind="clip", level=level, seen=seen, figure=fig.path, own=key[2], clips=[],
                                 actions=[])
            out.append(together[key])
        together[key]["clips"].append(file)
        together[key]["actions"] = sorted(set(together[key]["actions"]) | set(actions))
    missing: dict = {}
    for bone, why in fig.needs:
        if bone.lower() not in have:
            missing.setdefault((bone.lower(), why), []).append(bone)
    for (low, why), said in sorted(missing.items()):
        out.append({"kind": "bone", "level": "unseen" if why == SHOT else "stops", "seen": why == SHOT,
                    "figure": fig.path, "bone": said[0], "need": why, "count": len(said)})
    if masks:
        gone_all, count, halves = set(), 0, set()
        for _action, _file, mask in fig.listings:
            if mask is None or mask.weights is None:
                continue
            gone = {n for n in mask.weights if n.lower() not in have}
            if gone:
                gone_all |= gone
                count += 1
                halves.add("top" if mask.code == TOP_MASK else "bottom" if mask.code == BOTTOM_MASK else "other")
        if gone_all:
            out.append({"kind": "mask_bones", "level": "stops", "seen": False, "figure": fig.path,
                        "halves": sorted(halves), "names": sorted(gone_all, key=str.lower), "count": count})
        doubled = _doubled(model, fig)
        if doubled:
            out.append({"kind": "mask_sum", "level": "wrong", "seen": True, "figure": fig.path,
                        "bones": doubled[0], "most": doubled[1]})
    return out


def _doubled(model: list, fig: Figure) -> tuple[list, float] | None:
    """([the bones the figure's upper and lower halves weigh more than once over together], the most), or None: each
    upper-half mask its listings name against each lower-half one."""
    def weight(mask: Mask, bone: str) -> float:
        for n, w in mask.weights.items():
            if n.lower() == bone:
                return w
        return mask.default
    tops = {id(m): m for _a, _f, m in fig.listings if m is not None and m.weights is not None and m.code == TOP_MASK}
    bottoms = {id(m): m for _a, _f, m in fig.listings if m is not None and m.weights is not None and m.code == BOTTOM_MASK}
    over, most = set(), 0.0
    for t in tops.values():
        for b in bottoms.values():
            for bone in model:
                s = weight(t, bone.lower()) + weight(b, bone.lower())
                if s > SUM_MOST:
                    over.add(bone.lower())
                    most = max(most, s)
    return (sorted(over), round(most, 3)) if over else None


def model_problems(names: list, parents: list | None = None, saved_split: str | None = None) -> list:
    """The problems of the model itself: more than MOST_ANIMATED bones, and (with `parents`, a model on bones of its
    own) its split (chosen_split's)."""
    out = []
    if len(names) > MOST_ANIMATED:
        out.append({"kind": "too_many", "level": "untried", "seen": False, "bones": len(names), "most": MOST_ANIMATED})
    if parents is not None and names:
        out += chosen_split(names, parents, saved_split)[1]
    return out


class GameBones:
    """The bones of the game's own clips and models, read from ZZ_Win.dat (`zz`, an open rusemod.edat.Edat): a clip
    loose there or in a genanim_15 pack, a model's skeleton from the skeleton packs (gen_5\\pack\\...\\skeleton_*.spk);
    each pack read once, when first needed, each answer kept."""

    def __init__(self, zz):
        self.zz = zz
        self._clip_packs = None
        self._skeletons = None
        self._bones: dict = {}

    def clip(self, member: str) -> bytes | None:
        """A game clip's bytes by its path in the packs (rusemod.animlist.member_of), None when the game hasn't got it."""
        from .edat import Edat
        if self.zz is None:
            return None
        e = self.zz.entry(member)
        if e is not None:
            return bytes(self.zz.read(e))
        if self._clip_packs is None:
            self._clip_packs = [Edat(bytes(self.zz.read(x))) for x in self.zz.entries
                                if x.path.lower().startswith(CLIP_ROOT + "pack\\") and x.path.lower().endswith(".apk")]
        for pk in self._clip_packs:
            x = pk.entry(member)
            if x is not None:
                return bytes(pk.read(x))
        return None

    def clip_bones(self, member: str) -> list | None:
        key = ("clip", member.lower())
        if key not in self._bones:
            raw = self.clip(member)
            self._bones[key] = clip_bones(raw) if raw is not None else None
        return self._bones[key]

    def model_bones(self, model: str) -> list | None:
        """A game model's bones by number (its skeleton record's names, lower case), None when no skeleton pack holds
        it. `model`: a figure's FileName or a model's path in the packs."""
        from .unitpacks import NONE, MeshPack
        if self.zz is None or not model:
            return None
        if self._skeletons is None:
            self._skeletons = {}
            for e in self.zz.entries:
                p = e.path.lower()
                if p.startswith("gen_5\\pack\\") and p.endswith(".spk") and p.rsplit("\\", 1)[-1].startswith("skeleton"):
                    try:
                        pack = MeshPack.read(bytes(self.zz.read(e)))
                    except (ValueError, struct.error):
                        continue
                    for name, item in pack.items.items():
                        if item[2] != NONE:
                            self._skeletons.setdefault(model_key(name), pack.skeletons[item[2]])
        key = ("model", model_key(model))
        if key not in self._bones:
            record = self._skeletons.get(key[1])
            try:
                self._bones[key] = skeleton_of(record)[0] if record is not None else None
            except (ValueError, IndexError, struct.error, UnicodeDecodeError):
                self._bones[key] = None
        return self._bones[key]


def own_figures(figures: list, models) -> list:
    """The figures among `figures` drawing one of `models` (FileNames or model paths, any case and slashes)."""
    want = {model_key(m) for m in models if m}
    return [f for f in figures if f.model and model_key(f.model) in want]


def model_key(name: str) -> str:
    return name.replace("/", "\\").lower().rsplit(".", 1)[0]
