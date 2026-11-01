"""A build list's lines as rows (the owner, 2026-10-31, with all 366 era units in: "the armored infantry cars are in one
line, the unarmored are in one line, the infantry is in one line, and that way on the screen you're only going down
the column. Of different types of stuff, and then you're going across the rows as in like what kind of unit vehicle it
is"; his picks: lines as rows, and a line too long for one row carries on in a second row; fault FL-51).

The game keeps an upgrade's research card beside the unit it upgrades, but a researched upgrade stands as a row of its
own: a mod's era units, each an upgrade of one game unit (eight of the Kubelwagen) or bought from the start, filled the
column past the screen. With lines as rows, a line's buttons stand in that line's rows: its own unit first, its other
units, then its research cards, ACROSS to a row, a longer line carrying on in the rows right below (bigpacks10, his test:
a research card whose unit wasn't in the list stood alone, and while an upgrade is researched the game hides the unit
it upgrades, so its cards stood alone till the research ended: a card goes by its line, not by its unit). A button's
line is the first unit of its upgrades (each research's parent, up the chain); a unit bought from the start joins the
group the mods' menu_groups.toml put it in (rusemod.menugroups: the Studio's pick, the game's own units too), else, a
new unit, the line of the unit it was copied from, which the build writes into the template (`_r2_lines`). A research
card may start a row: its action, like a unit's, has the get_policy the game's research start reads.

The build counts the groups as the Studio does (built_groups, over_limits): a group holding more than menugroups.MOST,
or a building's list more than menugroups.MOST_GROUPS groups, is built with a warning (the owner's picks, 2026-10-31
and 11-01), never refused.

The template runs after the game's own headup/menu module (pyscript.append_module), compiled with the game's Python
2.5.1 (menulines_compiled): after the game numbers a tab's rows (Menu.update_sub_buttons), it links each row's buttons
the way the game links a unit and its research card (add_attached_button, both ways) and numbers the rows again. While the game decides whether a unit's own button stays (Menu.add_bouton_construction_unit:
it goes while the first button beside it has a command, meant for its upgrade being researched), the unit shows only
its own research cards, so another unit being built beside it never takes it away. Any error leaves the tab as the game
made it: an error out of the game's scripts stops the game.
"""
from __future__ import annotations

import base64
import hashlib

from . import menugroups, ownbuildings, pyscript

ACROSS = 6   # a row's cards, units and research cards alike: his pick after bigpacks12 ("a limit of 6 total in a row")
# The units a build list's groups hold, as the Studio has them (ruse_studio.api KINDS: ground, infantry, air). In the
# game's data (its index, 2026-11-01) these are the only classes with a Factory of a building that makes units, beside
# the build bar's tabs (TMainMenuInfos); the buildings' own Factory is 3, the construction menu.
UNITS = ("TUniteAuSolDescriptor", "TInfanterieDescriptor", "TAvionDescriptor")
# The buildings that make units, the board's rows (ruse_studio.board ALL_ROWS): Barracks, Artillery & AA Base, Armor
# Base, Anti-Tank Base, Airfield, Prototype Base, then the buildings with units of their own (rusemod.ownbuildings)
BUILDINGS = (8, 13, 10, 11, 9, 12) + ownbuildings.KINDS

SOURCES = {
    "menu": '''\
# a build list's lines as rows (the RUSE Studio's build): a line's units (its own unit first), then its research cards,
# _r2_across to a row, a line's rows together, the lines in the order of their menu positions. Any error leaves the tab
# as the game made it.
_r2_across = 6
_r2_lines = ()
_r2_line_of = {}
for _r2_pair in _r2_lines:
    _r2_line_of[_r2_pair[0]] = _r2_pair[1]


def _r2_name(descriptor):
    return getattr(getattr(descriptor, 'base_class', None), '__name__', None)


def _r2_first(techno):
    steps = 0
    while techno is not None and techno.IsUpgrade() and steps < 64:
        parent = techno.GetParente()
        if parent is None:
            break
        techno = parent
        steps = steps + 1
    return techno


def _r2_line(techno, descriptor):
    root = _r2_first(techno)
    name = None
    if root is not None:
        name = _r2_name(root.GetDescriptor())
    if name is None:
        name = _r2_name(descriptor)
    if name is None:
        return None
    return _r2_line_of.get(name, name)


def _r2_line_of_button(bouton):
    if bouton.is_unit_button():
        return _r2_line(bouton.techno, bouton.descriptor)
    if bouton.is_techno_button() and bouton.techno is not None:
        return _r2_line(bouton.techno, bouton.techno.GetDescriptor())
    return None


def _r2_rows(self):
    # [(line, [a row's buttons])] in the game's order of the lines: a line's units (its own unit first), then its
    # research cards, _r2_across to a row
    units = {}
    cards = {}
    order = []
    for bouton in self._current_submenu_buttons:
        if not (bouton.is_unit_button() or bouton.is_techno_button()):
            continue
        line = _r2_line_of_button(bouton)
        if line is None:
            continue
        if line not in units:
            units[line] = []
            cards[line] = []
            order.append(line)
        if bouton.is_unit_button():
            units[line].append(bouton)
        else:
            cards[line].append(bouton)
    key = {}            # a line's place down the column: its menu position, the same whether its own unit shows or not
    for line in order:
        places = []
        for bouton in units[line] + cards[line]:
            if bouton.is_unit_button():
                descriptor = bouton.descriptor
            else:
                descriptor = bouton.techno.GetDescriptor()
            places.append(getattr(descriptor, 'PositionInMenu', 0))
            root = _r2_first(bouton.techno)
            if root is not None:
                places.append(getattr(root.GetDescriptor(), 'PositionInMenu', 0))
        least = places[0]
        for place in places:
            if place < least:
                least = place
        key[line] = (least, line)
    order.sort(key=lambda line: key[line])
    rows = []
    for line in order:
        first = [unit for unit in units[line] if _r2_name(unit.descriptor) == line]
        members = first + [unit for unit in units[line] if unit not in first] + cards[line]
        k = 0
        while k < len(members):
            rows.append((line, members[k:k + _r2_across]))
            k = k + _r2_across
    return rows


def _r2_link(self, rows):
    want = {}
    for line, row in rows:
        head = row[0]
        want[head] = row[1:]
        for member in row[1:]:
            want[member] = [head]
    for bouton, others in want.items():
        for linked in bouton.get_attached_buttons()[:]:
            if linked not in others:
                if linked.get_submenu_descriptor() is None:
                    bouton.get_attached_buttons().remove(linked)
                else:
                    bouton.remove_attached_button(linked)
        for other in others:
            if not bouton.has_attached_button(other):
                bouton.add_attached_button(other)


def _r2_number(self, rows):
    # every line's rows numbered together, in their order, where the game's order first reaches a line, each row's
    # buttons in its order; any other button as the game does, with what the game linked beside it
    row_of = {}
    rows_of_line = {}
    for line, row in rows:
        if line not in rows_of_line:
            rows_of_line[line] = []
        rows_of_line[line].append(row)
        for member in row:
            row_of[member] = line
    placed = {}
    index = 0
    merged = 0
    lines_placed = False
    for bouton in self._current_submenu_buttons:
        if bouton in placed:
            continue
        if bouton in row_of:
            if lines_placed:
                continue
            lines_placed = True
            todo = [row for line, row in rows]
        else:
            row = [bouton]
            for other in bouton.get_attached_buttons():
                if other not in placed and other is not bouton and other not in row_of:
                    row.append(other)
            todo = [row]
        for row in todo:
            group = 0
            for member in row:
                member.set_index(index)
                if len(row) > 1 or getattr(member, '_index_in_group', 0):
                    member.set_index_in_group(group)
                if group > 0:
                    merged = merged + 1
                placed[member] = 1
                group = group + 1
            index = index + 1
    self._current_nb_merged_buttons = merged


def _r2_parent_button(self, card):
    techno = card.techno
    if techno is None or not techno.IsUpgrade():
        return None
    parent = techno.GetParente()
    if parent is None:
        return None
    return self._dico_boutons.get(getattr(parent.GetDescriptor(), 'base_class', None))


_r2_game_update_sub_buttons = Menu.update_sub_buttons
_r2_game_add_unit = Menu.add_bouton_construction_unit


def _r2_update_sub_buttons(self, *args, **kwargs):
    result = _r2_game_update_sub_buttons(self, *args, **kwargs)
    try:
        rows = _r2_rows(self)
    except:
        return result
    try:
        _r2_link(self, rows)
        _r2_number(self, rows)
    except:
        pass
    return result


def _r2_add_unit(self, descriptor, *args, **kwargs):
    bouton = None
    kept = None
    try:
        bouton = self._dico_boutons.get(descriptor.base_class)
        if bouton is not None:
            kept = bouton._attached_buttons
            own = []
            for linked in kept:
                if linked.is_techno_button() and _r2_parent_button(self, linked) is bouton:
                    own.append(linked)
            bouton._attached_buttons = own
    except:
        if bouton is not None and kept is not None:
            bouton._attached_buttons = kept
        kept = None
    try:
        return _r2_game_add_unit(self, descriptor, *args, **kwargs)
    finally:
        if kept is not None:
            try:
                if self._dico_boutons.get(descriptor.base_class) is bouton:
                    for linked in bouton._attached_buttons:
                        if linked not in kept:
                            kept.append(linked)
                    bouton._attached_buttons = kept
                else:
                    for linked in kept:
                        if bouton in linked._attached_buttons:
                            linked._attached_buttons.remove(bouton)
            except:
                pass


Menu.update_sub_buttons = _r2_update_sub_buttons
Menu.add_bouton_construction_unit = _r2_add_unit
''',
}
# where each template goes: (the script pack in ZZ_Win.dat, the game's module in it)
SCRIPTS = {
    "menu": ("genpython\\eugen.ipk", "genpython\\1000\\codeia\\python\\eugen\\headup\\menu.xyz"),
}


class MenuLinesError(ValueError):
    pass


def source_sha(name: str) -> str:
    return hashlib.sha256(SOURCES[name].encode("utf-8")).hexdigest()


def template(name: str) -> pyscript.Code:
    """A template, compiled: refused when the compiled one isn't of the source above (menulines_compiled)."""
    from .menulines_compiled import COMPILED
    entry = COMPILED.get(name)
    if entry is None or entry["source_sha256"] != source_sha(name):
        raise MenuLinesError(f"the compiled {name} template isn't the one of its source: compile it again")
    code = pyscript.load(base64.b64decode(entry["marshal"]))
    if not isinstance(code, pyscript.Code):
        raise MenuLinesError(f"the compiled {name} template isn't a module")
    return code


def missing(zz_win) -> str:
    """What of the game's menu script ZZ_Win.dat lacks ("" when it's all there)."""
    from .edat import Edat
    for pack_path, member_path in SCRIPTS.values():
        entry = zz_win.entry(pack_path)
        if entry is None:
            return f"ZZ_Win.dat has no {pack_path}"
        if Edat(bytes(zz_win.read(entry))).entry(member_path) is None:
            return f"{pack_path} has no {member_path}"
    return ""


def script_changes(zz_win, lines, packs: dict | None = None) -> dict:
    """{script pack's path in ZZ_Win.dat: (the pack, as an Edat; {module path: the new .xyz})}: the game's menu module
    with the template run after it, `lines` ((a new unit's class, the class of the unit whose line it joins), ...)
    filled in. `packs`: script packs other steps already changed, {path: (pack, {module path: .xyz})}; a module there
    is changed from that version."""
    from .edat import Edat
    value = tuple((a.encode("latin-1"), b.encode("latin-1")) for a, b in lines)
    out: dict = {}
    for name, (pack_path, member_path) in SCRIPTS.items():
        entry = zz_win.entry(pack_path)
        if entry is None:
            raise MenuLinesError(f"ZZ_Win.dat has no {pack_path}")
        pack, changed = (packs or {}).get(entry.path) or out.get(entry.path) or (Edat(bytes(zz_win.read(entry))), {})
        member = pack.entry(member_path)
        if member is None:
            raise MenuLinesError(f"{pack_path} has no {member_path}")
        raw = changed.get(member.path) or bytes(pack.read(member))
        xyz = pyscript.read_xyz(raw)
        joined = pyscript.append_module(xyz.payload, pyscript.with_value(template(name), b"_r2_lines", value))
        out[entry.path] = (pack, {**changed, member.path: pyscript.write_xyz(pyscript.Xyz(xyz.source_md5, joined))})
    return out


def class_name(objects, by_path, path) -> str | None:
    """A unit's class in the game's Python unit list: its ClassNameForDebug, else the list's own (`by_path`: unit path
    -> its class name there, the game's units), else None."""
    from .patch import Text
    obj = objects.get(path)
    debug = obj.props.get("ClassNameForDebug") if obj is not None else None
    return debug.value if isinstance(debug, Text) else by_path.get(path)


def unit_of(obj, op=None) -> dict:
    """A built object as rusemod.menugroups takes a unit (ruse_studio.groups builds the same from the board): {"parent":
    the unit it's researched from (UpgradeRequire) or None, "flag": whether it's an upgrade (IsUpgrade), "source": a new
    unit's clone source (`op`, the op that made it), "nation" (Nationalite, 0 when it has none), "factory" (its building,
    one of BUILDINGS, else None), "shown" (at some battle date: no ShowInMenu, or a non-zero one), "slot" (its place
    number, PositionInMenu, or None)}."""
    from .patch import ListV, Num, Ref
    p = obj.props
    flag, need, shows = p.get("IsUpgrade"), p.get("UpgradeRequire"), p.get("ShowInMenu")
    nation, factory, slot = (int(v.value) if isinstance(v, Num) else None
                             for v in (p.get("Nationalite"), p.get("Factory"), p.get("PositionInMenu")))
    return {"parent": need.target if isinstance(need, Ref) else None,
            "flag": isinstance(flag, Num) and bool(flag.value),
            "source": op.source if op is not None and getattr(op, "kind", None) == "clone" else None,
            "nation": nation or 0, "factory": factory if factory in BUILDINGS else None,
            "shown": not isinstance(shows, ListV) or any(isinstance(x, Num) and x.value for x in shows.items),
            "slot": slot}


def _upgrade(u: dict) -> bool:
    """Whether a unit stands where its research puts it (rusemod.menugroups.roots climbs from it)."""
    return bool(u["flag"]) and u["parent"] is not None


def lines_of(objects, by_path, created, groups: dict | None = None) -> list[tuple[str, str]]:
    """((a unit's class, the class of its group's first unit), ...) for the template's `_r2_lines`: each unit that
    starts its research chain (no upgrade) and each new unit (created), whose group's first unit is another unit:
    rusemod.menugroups.roots, up the research chain while an upgrade, else where the mods' menu groups put it (`groups`:
    {address: its group's first unit's address}, the game's units too), else a new unit the way of the unit it was
    copied from; fully resolved, as the template maps a line's first unit once. A game upgrade gets none (the game's
    script climbs to its chain's first unit, which carries it); a new upgrade gets its chain's, as before the groups. A
    unit in a group of its own gets none. `objects`: the built game's objects; `by_path`: unit path -> its class name in
    the game's unit list (the game's units); `created`: new object path -> the op that made it (a clone op: its
    source)."""
    groups = groups or {}
    units: dict = {}   # what roots can climb through from the units asked about: every step it may take
    todo = [p for p in list(created) + list(groups) if p in objects]
    while todo:
        path = todo.pop()
        if path in units:
            continue
        u = units[path] = unit_of(objects[path], created.get(path))
        todo += [s for s in (u["parent"], groups.get(path), u["source"]) if s in objects and s not in units]
    root = menugroups.roots(units, groups)
    out = []
    for path, u in units.items():
        if path not in created and (path not in groups or _upgrade(u)):
            continue
        name, to = class_name(objects, by_path, path), class_name(objects, by_path, root[path])
        if name and to and root[path] != path and to != name:
            out.append((name, to))
    return sorted(set(out))


def built_groups(objects, created, groups: dict | None = None) -> tuple[dict, dict]:
    """The build lists' groups of the built game as the Studio counts them (ruse_studio.groups GroupState): every unit
    (UNITS), the game's and the mods', in a building that makes units and shown at some battle date, in the group
    rusemod.menugroups.roots gives it (`groups`: the mods' menu groups), per nation and building, each upgrade one place.
    Returns ({(nation, building, the group's first unit): [its units]} (menugroups.members), {address: its unit
    (unit_of)} of every unit)."""
    units = {p: unit_of(o, created.get(p)) for p, o in objects.items() if o.cls in UNITS}
    return menugroups.members(units, menugroups.roots(units, groups or {})), units


def first_shown(units: dict, key: tuple, members: list) -> str:
    """The unit a group stands under in the Studio (ruse_studio.groups GroupState "root"): its first unit when it's in
    that building's row, else the group's first unit in the board's order (ruse_studio.board _board_tree: the row's
    units by place number, then address, each followed by the ones researched from it in that row)."""
    nation, factory, first = key
    if first in members:
        return first
    here = {a: u for a, u in units.items() if u["nation"] == nation and u["factory"] == factory and u["shown"]}
    order = sorted(here, key=lambda a: (here[a]["slot"] is None, here[a]["slot"] or 0, a))
    kids: dict = {}
    top = []
    for a in order:
        p = here[a]["parent"]
        (kids.setdefault(p, []) if p in here and p != a else top).append(a)
    mine, seen = set(members), set()
    for start in top + order:
        stack = [start]
        while stack:
            a = stack.pop()
            if a in seen:
                continue
            seen.add(a)
            if a in mine:
                return a
            stack += reversed(kids.get(a, []))
    return sorted(members)[0]


def over_limits(objects, created, groups: dict | None = None) -> tuple[list, list]:
    """What of the built game's build lists (built_groups) is past the owner's limits: ([((nation, building, the
    group's first unit), how many, the unit it stands under in the Studio (first_shown))] for each group holding more
    than menugroups.MOST, [((nation, building), how many groups)] for each building whose list has more than
    menugroups.MOST_GROUPS), each the fullest first."""
    found, units = built_groups(objects, created, groups)
    return ([(key, count, first_shown(units, key, found[key])) for key, count in menugroups.over(found)],
            menugroups.crowded(found))
