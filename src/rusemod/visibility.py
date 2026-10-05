"""Placed objects drawn from further away. The game draws a scenery type only at the distances its own data gives it,
and many props (rocks, pebbles, stony fields, most stone walls) are drawn close up only: a mod's object of such a type
vanished as soon as the camera left close range (a tester's rocks, 2026-10-03; the map's own patches do the same).

The owner chose (2026-10-03): only what a mod places changes; the map's own objects stay as they are. So for each type
a mod places that isn't drawn from far, the build makes a copy of the type named <type>_R2Seen, drawn at every
distance, and the mod's objects of that type use the copy (rusemod.scenery.add_names). Seen in the game at middle
distances (2026-10-03: the game loads the copies and draws them); the far distance not yet tried."""
from __future__ import annotations

from .patch import Inline, ListV, Num, Ref, Text

SUFFIX = "_R2Seen"
CLOSE, MIDDLE, FAR = 0x03, 0x14, 0x08  # the passes: close (1|2), middle (4|0x10), far


def entries(obj, objects=None) -> list[tuple] | None:
    """A scenery descriptor's mode entries, in list order: [(ModeMask, the entry object, written inside the type)],
    or None when it has no modes (a single model, a sticker: drawn as the game draws those). An entry can be a
    reference instead (220 entries of the shipped prop sets: unnamed objects shared by up to 8 types), read through
    `objects` (the game's objects by name); one that can't be read is (None, None, False)."""
    mm = obj.props.get("SDFalse")
    mm = mm.obj if isinstance(mm, Inline) else (obj if "ModeEntry" in obj.props else None)
    items = mm.props.get("ModeEntry") if mm is not None else None
    if not isinstance(items, ListV):
        return None
    out = []
    for e in items.items:
        o = e.obj if isinstance(e, Inline) else (objects or {}).get(e.target) if isinstance(e, Ref) else None
        m = o.props.get("ModeMask") if o is not None else None
        out.append((int(m.value), o, isinstance(e, Inline)) if isinstance(m, Num) else (None, None, False))
    return out or None


def modes(obj, objects=None) -> list[int] | None:
    """The ModeMasks of a scenery descriptor's entries (entries), or None when it has no modes or one of its entries
    can't be read (then no copy is made: the type is left as the game draws it)."""
    got = entries(obj, objects)
    if not got or any(m is None for m, _o, _inline in got):
        return None
    return [m for m, _o, _inline in got]


def needs_copy(masks: list[int] | None) -> bool:
    """A type with modes but none for the far pass (whatever it has for the middle ones), and a close or middle one
    to widen: a type drawn by other passes alone (an effect's, 0x1000 and up) gains nothing from a copy."""
    return bool(masks) and not any(m & FAR for m in masks) and bool(widened(masks))


def widened(masks: list[int]) -> dict[int, int]:
    """{entry index: its new ModeMask} for a copy: with no middle entry the close ones serve the middle passes too
    (| 4), and the entries for the farthest passes it has (middle, else close) serve the far pass as well (| 8)."""
    middle = any(m & MIDDLE for m in masks)
    out = {}
    for i, m in enumerate(masks):
        new = m
        if not middle and m & CLOSE:
            new |= 0x4
        if (m & MIDDLE) if middle else (m & CLOSE):
            new |= FAR
        if new != m:
            out[i] = new
    return out


def descriptors_named(game, names: set[str]) -> dict[str, list]:
    """{registration name: [(object name, its game file, the object)]} for the scenery descriptors with those names
    in the game model `game` (rusemod.patch.Game)."""
    out: dict[str, list] = {}
    for name, obj in game.objects.items():
        v = obj.props.get("RegistrationName")
        if isinstance(v, Text) and v.value in names:
            origin = obj.origin or obj.copied_from
            out.setdefault(v.value, []).append((name, origin[0] if origin else name.partition("#")[0], obj))
    return out


def plan(game, placed: set[str]) -> dict[str, str]:
    """{type a mod places: its copy's name} for every placed type with no far mode (`placed`: TypeWarrior/...)."""
    found = descriptors_named(game, placed)
    return {t: t + SUFFIX for t in sorted(placed)
            if t in found and all(needs_copy(modes(o, game.objects)) for _n, _f, o in found[t])}


def rndf(game, copies: dict[str, str]) -> str:
    """The .rndf making each copy, once per game file that defines the type. An entry written inside the type is the
    copy's own (a clone copies it): its ModeMask is widened in place. An entry the type refers to is shared with other
    types, the map's own objects among them, so it's left as it is and the copy gets a copy of it of its own, serving
    only the added distances, at the end of its list."""
    found = descriptors_named(game, set(copies))
    lines = ["// Written by the build (rusemod.visibility): copies of the types mods place that the game doesn't draw",
             "// from far, also drawn from far. The map's own objects keep the shipped types."]
    for k, (t, copy) in enumerate(sorted(copies.items())):
        for j, (_name, file, obj) in enumerate(found[t]):
            local = f"R2Seen_{k}_{j}"
            got = entries(obj, game.objects) or []
            lines += [f'{local} is clone @[RegistrationName="{t}", file="{file}"]', "(",
                      f'    RegistrationName = "{copy}"', ")"]
            path = "SDFalse.ModeEntry" if "SDFalse" in obj.props else "ModeEntry"
            added = []
            for i, m in widened([e[0] for e in got]).items():
                old, entry, inline = got[i]
                if inline:
                    lines += [f"patch ~/{local}:{path}[{i}]", "(", f"    ModeMask = {m}"]
                else:  # shared: a copy of it of the copy's own, for the added distances only
                    own = f"{local}_e{i}"
                    added.append(own)
                    lines += [f"{own} is clone ~/{local}:{path}[{i}]", "(", f"    ModeMask = {m & ~old}"]
                if "GraphicOptionDeactivated" in entry.props:
                    lines.append("    delete GraphicOptionDeactivated")
                lines.append(")")
            if added:
                lines += [f"patch ~/{local}", "(", f"    {path} += [{', '.join('~/' + a for a in added)}]", ")"]
    return "\n".join(lines) + "\n"
