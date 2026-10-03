"""Fresh identity for copied units (docs/MOD_FORMAT.md §10.5).

A clone starts as an exact copy of its source, so values the game expects to differ between units are the same. After
the clone's own lines run, the engine gives it fresh ones, except for any the clone sets itself:

  DescriptorId, TrackingId, one more than the highest in the game, if the source's class uses them as ids (no two
  AmmunitionId              objects of the class share a value); otherwise left as copied. AmmunitionId: a copied
                            ammunition (a weapon's own ammo), which mods may find by its id (@TAmmunition[...])
  ClassNameForDebug         the clone's own name, written the way the source's is (Descriptor_Unit_X -> Unit_X);
                            `_2`, `_3`, ... added if that's taken
  PositionInMenu            its slot in the build menu (slot = row * 100 + column). Units share a menu when they have
                            the same Nationalite (not written = 0) and Factory. The copied slot is kept if it's free in
                            that menu, else the clone goes after the last unit of the same row.

The name shown in game (NameInMenuToken) stays the source's until text mods can supply new names.
tools/identity_check.py checks these rules against the real game.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .patch import INT_RANGES, Inline, Num, Text, _walk_value

IDS = ("DescriptorId", "TrackingId", "AmmunitionId")
DEBUG_NAME = "ClassNameForDebug"
SLOT = "PositionInMenu"
RULES = IDS + (DEBUG_NAME, SLOT)


@dataclass
class _Scan:
    top: dict = field(default_factory=dict)          # id property -> highest value anywhere in the game
    by_class: dict = field(default_factory=dict)     # (id property, class) -> {value: [names]}
    debug_names: dict = field(default_factory=dict)  # debug name -> [names]
    menus: dict = field(default_factory=dict)        # (nation, factory) -> {slot: [names]}


def _int(v):
    return v.value if isinstance(v, Num) and v.kind in INT_RANGES else None


def menu_of(obj):
    """(nation, factory) of an object in a build menu, or None."""
    factory = _int(obj.props.get("Factory"))
    if factory is None:
        return None
    nation = _int(obj.props.get("Nationalite"))
    return (nation if nation is not None else Decimal(0), factory)


def _scan(game) -> _Scan:
    s = _Scan()

    def note_ids(obj):
        for prop in IDS:
            v = _int(obj.props.get(prop))
            if v is not None and (prop not in s.top or v > s.top[prop]):
                s.top[prop] = v

    for name, obj in game.objects.items():
        note_ids(obj)
        for v in obj.props.values():  # ids inside owned parts count toward the highest too
            for x in _walk_value(v):
                if isinstance(x, Inline):
                    note_ids(x.obj)
        for prop in IDS:
            v = _int(obj.props.get(prop))
            if v is not None:
                s.by_class.setdefault((prop, obj.cls), {}).setdefault(v, []).append(name)
        d = obj.props.get(DEBUG_NAME)
        if isinstance(d, Text):
            s.debug_names.setdefault(d.value, []).append(name)
        menu, slot = menu_of(obj), _int(obj.props.get(SLOT))
        if menu is not None and slot is not None:
            s.menus.setdefault(menu, {}).setdefault(slot, []).append(name)
    return s


def _is_id(scan: _Scan, prop: str, cls: str, new) -> bool:
    """True unless two of the game's own objects of the class share a value (objects in `new` don't count)."""
    values = scan.by_class.get((prop, cls), {})
    return all(len([n for n in names if n not in new]) <= 1 for names in values.values())


def debug_name(source: str, source_debug: str, name: str) -> str:
    """The clone's debug name, following the source's pattern: Descriptor_Unit_M4_Sherman has Unit_M4_Sherman, so a
    clone named Descriptor_Unit_R2_Test gets Unit_R2_Test. Otherwise the clone's name as it is."""
    src_last, new_last = source.rsplit("/", 1)[-1], name.rsplit("/", 1)[-1]
    if source_debug and src_last.endswith(source_debug):
        prefix = src_last[:len(src_last) - len(source_debug)]
        if new_last.startswith(prefix) and len(new_last) > len(prefix):
            return new_last[len(prefix):]
    return new_last


def refresh(game, name: str, source: str, skip=(), new=()) -> list:
    """Give the clone `name` (copied from `source`) fresh identity values, in place. `skip`: properties the clone
    sets itself; `new`: the objects mods added so far. Returns [(property, old value, new value)] per value changed.
    A clone with none of the properties these rules look at (a scenery type's copy, rusemod.visibility) has nothing to
    change, so the game isn't scanned for it (3 seconds a clone)."""
    obj = game.objects[name]
    if not any(p in obj.props for p in RULES if p not in skip):
        return []
    scan, changed = _scan(game), []
    added = set(new) | {name}
    for prop in IDS:
        old = obj.props.get(prop)
        if prop in skip or _int(old) is None or not _is_id(scan, prop, obj.cls, added):
            continue
        new = Num(old.kind, scan.top[prop] + 1)
        obj.props[prop], changed = new, changed + [(prop, old, new)]
    old = obj.props.get(DEBUG_NAME)
    if DEBUG_NAME not in skip and isinstance(old, Text):
        taken = {d for d, names in scan.debug_names.items() if any(n != name for n in names)}
        base = cand = debug_name(source, old.value, name)
        n = 2
        while cand in taken:
            cand, n = f"{base}_{n}", n + 1
        new = Text(old.kind, cand)
        obj.props[DEBUG_NAME], changed = new, changed + [(DEBUG_NAME, old, new)]
    old, menu = obj.props.get(SLOT), menu_of(obj)
    if SLOT not in skip and _int(old) is not None and menu is not None:
        used = {s for s, names in scan.menus.get(menu, {}).items() if any(n != name for n in names)}
        slot = int(_int(old))
        if slot >= 0 and slot in used:
            row = slot // 100
            cols = [int(s) % 100 for s in used if int(s) // 100 == row]
            free = [c for c in range(max(cols) + 1, 100)] or [c for c in range(100) if c not in cols]
            if free:
                new = Num(old.kind, Decimal(row * 100 + free[0]))
                obj.props[SLOT], changed = new, changed + [(SLOT, old, new)]
    return changed


def clashes(game, names) -> list[tuple[str, str]]:
    """For new objects `names`: identity values some other object also has (same class for ids, any object for debug
    names, same build menu for slots), as [(new object, message)]. Ids a class's own objects share aren't ids, so aren't
    checked; nor is a unit's DescriptorId, which no other unit of any kind may share (rusemod.unitcheck)."""
    from .unitcheck import UNIT_CLASSES  # a unit's DescriptorId: an error there (patch.Engine._unit_rules)
    scan, out, new = _scan(game), [], set(names)
    for name in names:
        obj = game.objects.get(name)
        if obj is None:
            continue
        for prop in IDS:
            v = _int(obj.props.get(prop))
            if v is None or not _is_id(scan, prop, obj.cls, new) or (prop == "DescriptorId" and obj.cls in UNIT_CLASSES):
                continue
            others = [n for n in scan.by_class[(prop, obj.cls)][v] if n != name]
            if others:
                out.append((name, f"{name} has {prop} {v}, the same as {others[0]}"))
        d = obj.props.get(DEBUG_NAME)
        others = [n for n in scan.debug_names.get(d.value, []) if n != name] if isinstance(d, Text) else []
        if others:
            out.append((name, f"{name} has {DEBUG_NAME} {d.value!r}, the same as {others[0]}"))
        menu, slot = menu_of(obj), _int(obj.props.get(SLOT))
        others = [n for n in scan.menus.get(menu, {}).get(slot, []) if n != name] if menu and slot is not None else []
        if others:
            out.append((name, f"{name} has build-menu slot {slot}, the same as {others[0]} (they overlap in the menu)"))
    return out
