"""A build list's lines as rows (the owner, 2026-10-31, with all 366 era units in: "the armored infantry cars are in one
line, the unarmored are in one line, the infantry is in one line, and that way on the screen you're only going down
the column. Of different types of stuff, and then you're going across the rows as in like what kind of unit vehicle it
is"; his picks: lines as rows, and a line too long for one row carries on in a second row; fault FL-51).

The game keeps an upgrade's research card beside the unit it upgrades, but a researched upgrade stands as a row of its
own: a mod's era units, each an upgrade of one game unit (eight of the Kubelwagen) or bought from the start, filled the
column past the screen. With lines as rows, every unit of a line stands in that line's row: the line's first unit, at
most ACROSS - 1 more of its units beside it, then the research cards of the units in that row; a longer line carries on
in a row below, which starts with its next unit. A unit's line is the first unit of its upgrades (each research's
parent, up the chain); a new unit bought from the start joins the line of the unit it was copied from, which the build
writes into the template (`_r2_lines`).

The template runs after the game's own headup/menu module (pyscript.append_module), compiled with the game's Python
2.5.1 (menulines_compiled): after the game numbers a tab's rows (Menu.update_sub_buttons), it links each row's buttons
the way the game links a unit and its research card (add_attached_button, both ways) and numbers the rows again, each
row starting with a unit. While the game decides whether a unit's own button stays (Menu.add_bouton_construction_unit:
it goes while the first button beside it has a command, meant for its upgrade being researched), the unit shows only
its own research cards, so another unit being built beside it never takes it away. Any error leaves the tab as the game
made it: an error out of the game's scripts stops the game.
"""
from __future__ import annotations

import base64
import hashlib

from . import pyscript

ACROSS = 5   # a row's units: his 1920 x 1080 screen showed a row of 4 cards and the upgrade tab (bigpacks5, capture 6996)

SOURCES = {
    "menu": '''\
# a build list's lines as rows (the RUSE Studio's build): every unit of a line in that line's row, at most _r2_across
# of them, then the research cards of that row's units; a longer line carries on in a row below, which starts with a
# unit. Any error leaves the tab as the game made it.
_r2_across = 5
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


def _r2_unit_line(bouton):
    techno = _r2_first(bouton.techno)
    name = None
    if techno is not None:
        name = _r2_name(techno.GetDescriptor())
    if name is None:
        name = _r2_name(bouton.descriptor)
    if name is None:
        return None
    return _r2_line_of.get(name, name)


def _r2_parent_button(self, card):
    techno = card.techno
    if techno is None or not techno.IsUpgrade():
        return None
    parent = techno.GetParente()
    if parent is None:
        return None
    return self._dico_boutons.get(getattr(parent.GetDescriptor(), 'base_class', None))


def _r2_rows(self):
    # [(head, [its row's other buttons])] for the tab's units in the game's order, and {card: head}
    lines = {}
    order = []
    cards = []
    for bouton in self._current_submenu_buttons:
        if bouton.is_unit_button():
            line = _r2_unit_line(bouton)
            if line is not None:
                if line not in lines:
                    lines[line] = []
                    order.append(line)
                lines[line].append(bouton)
        elif bouton.is_techno_button():
            cards.append(bouton)
    rows = []
    head_of = {}
    for line in order:
        units = lines[line]
        first = [unit for unit in units if _r2_name(unit.descriptor) == line]
        units = first + [unit for unit in units if unit not in first]
        k = 0
        while k < len(units):
            chunk = units[k:k + _r2_across]
            rows.append((chunk[0], chunk[1:]))
            for unit in chunk:
                head_of[unit] = chunk[0]
            k = k + _r2_across
    card_head = {}
    for card in cards:
        parent = _r2_parent_button(self, card)
        if parent is not None and parent in head_of:
            card_head[card] = head_of[parent]
    return rows, card_head


def _r2_link(self, rows, card_head):
    want = {}
    for head, units in rows:
        want[head] = units[:]
        for unit in units:
            want[unit] = [head]
    for card, head in card_head.items():
        want[head].append(card)
        want[card] = [head]
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
    return want


def _r2_number(self, rows, want):
    # each row numbered where the game's order first reaches it, a line's rows together and in their order
    placed = {}
    line_of_head = {}
    heads_of_line = {}
    for head, units in rows:
        line = _r2_unit_line(head)
        line_of_head[head] = line
        if line not in heads_of_line:
            heads_of_line[line] = []
        heads_of_line[line].append(head)
    index = 0
    merged = 0
    for bouton in self._current_submenu_buttons:
        if bouton in placed:
            continue
        starts = [bouton]
        if bouton in want and bouton not in line_of_head:
            head = want[bouton][0]
            if head not in line_of_head or head in placed:
                continue
            bouton = head
        if bouton in line_of_head:
            starts = heads_of_line[line_of_head[bouton]]
        for start in starts:
            if start in placed:
                continue
            row = [start]
            for other in start.get_attached_buttons():
                if other not in placed and other is not start:
                    row.append(other)
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


_r2_game_update_sub_buttons = Menu.update_sub_buttons
_r2_game_add_unit = Menu.add_bouton_construction_unit


def _r2_update_sub_buttons(self, *args, **kwargs):
    result = _r2_game_update_sub_buttons(self, *args, **kwargs)
    try:
        rows, card_head = _r2_rows(self)
    except:
        return result
    try:
        want = _r2_link(self, rows, card_head)
        _r2_number(self, rows, want)
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


def lines_of(objects, by_path, created) -> list[tuple[str, str]]:
    """((a new unit's class, the class of the unit whose line it joins), ...): a new unit researched from another
    (IsUpgrade, UpgradeRequire) joins that unit's line, one bought from the start the line of the unit it was copied
    from, each followed to a unit that is neither (a game unit's own upgrades are followed by the game's script).
    `objects`: the built game's objects; `by_path`: unit path -> its class name in the game's unit list (the game's
    units); `created`: new object path -> the op that made it (a clone op: its source)."""
    from .patch import Num, Ref, Text

    def cls(path):
        obj = objects.get(path)
        debug = obj.props.get("ClassNameForDebug") if obj is not None else None
        return debug.value if isinstance(debug, Text) else by_path.get(path)

    def up(path):
        obj = objects.get(path)
        if obj is None:
            return None
        flag, need = obj.props.get("IsUpgrade"), obj.props.get("UpgradeRequire")
        if isinstance(flag, Num) and int(flag.value) and isinstance(need, Ref):
            return need.target
        op = created.get(path)
        return op.source if op is not None and getattr(op, "kind", None) == "clone" else None

    out = []
    for path in created:
        name = cls(path)
        if name is None or path not in objects:
            continue
        root, seen = path, {path}
        while True:
            nxt = up(root)
            if nxt is None or nxt in seen:
                break
            seen.add(nxt)
            root = nxt
        root_name = cls(root)
        if root != path and root_name and root_name != name:
            out.append((name, root_name))
    return sorted(set(out))
