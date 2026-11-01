"""The build lists' groups as the Studio keeps them (StudioApi's GroupCalls; the owner, 2026-10-31, after bigpacks13:
"We just need to limit how many can be in a certain group. Because it's buggy."; a 7th unit added to a full group:
"Refuse it"; his picks the same night: the groups are the game's lines, each unit going into the line of its kind,
counted over every battle date together, and a mod already over it when it's built is built with a warning).

A group is one row of a building's build list (rusemod.menugroups: a line as the game makes it, a unit and its
upgrades, each upgrade one place, the game's own units counted with the mod's), per nation and building, of the units
shown there at some battle date. Its first unit is where rusemod.menugroups.roots leads (up the research chain while an
upgrade, else where the mod's menu_groups.toml puts it, else the way of the unit it was copied from); when that unit
isn't in the row (a copy of another nation's unit in a mod made before the file, or a first unit taken out of the
build menus), the group's first unit in the board's order stands for it.

A unit's kind is the game's card type, in English ("Medium Tank", "Armored Recon", "Fighter"...): a game unit's from
its type text, an era unit's the era library's "card" (what it really is: 33 of the 366 differ from their start
unit's), a copy's (New unit..., the board's copy of another nation's unit) its start unit's. A unit the Studio puts in a
building goes into the group of its kind there: the game's line in that building holding a unit of that card type (its
game units'; with two such lines, the one with fewer units, then the one earlier in the menu); else a group the mod
made whose first unit is of that kind; else a group of its own, which the later units of that kind there then join.

The limit (rusemod.menugroups.MOST, his 6) is checked on every change that can put a unit into a group or move one
between groups: the change is worked out on the mod's changes in memory first (Draft) and refused, nothing saved, when
a group would then hold more than 6 and more than it held before. A move inside one group, or a change that leaves a
group no bigger, never is; a group already over 6 (a mod made before the limit) takes nothing more but lets units out.

The mod's menu_groups.toml is kept in step (_groups_settle): a unit the Studio puts in a group bought from the start (an
era unit, a copy, a unit moved to another building, a unit put in a group picked) is written with its group's first
unit (its own address: a group of its own); an upgrade has no line (its research says where it stands); a new unit made
buildable from the start (its research taken out by the Upgrade box, the board, a unit taken out, "No research")
stays in the group it stood in, under that group's first unit still there, so it never falls back into the group of
the unit it was copied from; a deleted unit's line goes, and the units whose group's first unit is deleted move to the
first remaining unit of that group in the board's order, which becomes the group's new first unit."""
from __future__ import annotations

import json
from collections import Counter

from rusemod import menugroups, nations, schema
from rusemod.menugroups import MOST

from .board import ALL_ROWS
from .edits import Edit, ModEdits

NEW = "new"   # board_put, board_move, era_unit_add, new_unit's `group`: a group of its own
PROPS = ("Factory", "Nationalite", "ShowInMenu", "IsUpgrade", "UpgradeRequire")  # the values that put a unit in a group


def is_lang(text) -> bool:
    """Whether a value is one of the page's language codes (an older caller's `lang` where `group` stands now)."""
    return isinstance(text, str) and (text == schema.BASE or text in schema.APP_LANGS)


def _shown(i: dict) -> bool:
    return True if i["shows"] is None else any(i["shows"])


def _upgrade(i: dict) -> bool:
    """Whether a unit stands where its research puts it (an upgrade: rusemod.menugroups.roots climbs from it)."""
    return bool(i["flag"]) and i["parent"] is not None


class Draft(ModEdits):
    """A mod's changes as they'd be after a change: in memory only, never saved, nothing on disk deleted."""

    def __init__(self, edits: ModEdits):  # (not ModEdits.__init__: nothing is read)
        self.folder, self.file, self.names_file = edits.folder, edits.file, edits.names_file
        self.edits = dict(edits.edits)
        self.new_units = dict(edits.new_units)
        self.new_objects = dict(edits.new_objects)
        self.deleted = set(edits.deleted)

    def save(self) -> None:
        pass

    def remove_unit(self, target: str) -> None:
        self.new_units.pop(target, None)
        for key in [k for k in self.edits if k[0] == target]:
            del self.edits[key]

    def apply(self, changes) -> "Draft":
        """[(address, prop, value)] as BoardCalls._board_apply saves them (value None: the game's own value back)."""
        for address, prop, value in changes:
            k = self.key(address, prop)
            if value is None:
                self.edits.pop(k, None)
            else:
                self.edits[k] = Edit(k[0], k[1], value, None)
        return self


class GroupState:
    """The groups as a mod has them at one moment: `rows` {(nation, building): [group]} in the board's order, each group
    {"id": (nation, building, the unit roots() leads to), "root": its first unit in the row, "units": its units in the
    board's order, "nation", "factory"}; `of` {address: its group}; `info` the board's units (BoardCalls._board_info),
    `file` the mod's menu groups, `kinds` {address: its card type or None}."""

    def __init__(self, info: dict, file: dict, kinds: dict, sources: dict, tree):
        self.info, self.file, self.kinds, self.sources = info, file, kinds, sources
        units = {a: {"parent": i["parent"], "flag": i["flag"], "source": sources.get(a), "nation": i["nation"],
                     "factory": i["factory"] if i["factory"] in ALL_ROWS else None, "shown": _shown(i)}
                 for a, i in info.items()}
        self.roots = menugroups.roots(units, file)
        found = menugroups.members(units, self.roots)
        orders = {}
        for n, f in {(n, f) for n, f, _r in found}:
            orders[(n, f)] = {a: k for k, (a, _d) in enumerate(tree(info, n, f))}
        self.rows: dict[tuple, list[dict]] = {}
        self.of: dict[str, dict] = {}
        self.by_id: dict[tuple, dict] = {}
        for (n, f, key), members in found.items():
            order = orders[(n, f)]
            members = sorted(members, key=lambda a: (order.get(a, len(order)), a))
            g = {"id": (n, f, key), "root": key if key in members else members[0], "units": members, "nation": n,
                 "factory": f, "at": order.get(members[0], len(order))}
            self.rows.setdefault((n, f), []).append(g)
            self.by_id[g["id"]] = g
            for a in members:
                self.of[a] = g
        for row in self.rows.values():
            row.sort(key=lambda g: (g["at"], g["root"]))

    def find(self, nation: int, factory: int, token: str) -> dict | None:
        """The group of row (nation, factory) that `token` names: its first unit's address (or any of its units')."""
        g = self.of.get(token)
        return g if g is not None and (g["nation"], g["factory"]) == (nation, factory) else None

    def matches(self, kind, nation: int, factory: int) -> list[dict]:
        """The groups of row (nation, factory) a unit of card type `kind` goes into: the game's lines holding one of the
        game's units of that kind, else the groups the mod made whose first unit is of that kind; none for a unit
        without a card type (a group of its own)."""
        if kind is None:
            return []
        row = self.rows.get((nation, factory), [])
        games = [g for g in row if not self.info[g["root"]]["new"]
                 and any(self.kinds.get(a) == kind for a in g["units"] if not self.info[a]["new"])]
        return games or [g for g in row if self.info[g["root"]]["new"] and self.kinds.get(g["root"]) == kind]

    def kind_group(self, kind, nation: int, factory: int) -> dict | None:
        """The group a unit of card type `kind` goes into in row (nation, factory) (matches: the one with fewer units,
        then the one earlier in the menu); None: a group of its own."""
        found = self.matches(kind, nation, factory)
        return min(found, key=lambda g: (len(g["units"]), g["at"])) if found else None

    def first_left(self, g: dict, info: dict, unit: str, leaving=()) -> str:
        """The first unit of group `g` still in its row after a change (`info`: the units as they'd be), in the board's
        order, the units `leaving` it (put in another group) passed over; `unit` itself when it comes first or none
        is."""
        for a in g["units"]:
            if a == unit:
                return unit
            i = info.get(a)
            if i is None or a in leaving or not _shown(i) or (i["nation"], i["factory"]) != (g["nation"], g["factory"]):
                continue
            return a
        return unit


class GroupCalls:
    """Mixed into StudioApi: uses BoardCalls' _board_info, _board_tree and _board_building_list, and its _open,
    _edits, _all_units, _names and _era_library."""

    # --- reading ---
    @staticmethod
    def _groups_file(edits) -> dict:
        """The mod's menu groups (rusemod.menugroups.read); none without a mod."""
        from .api import StudioError
        if edits is None:
            return {}
        try:
            return menugroups.read(edits.folder)
        except menugroups.MenuGroupsError as exc:
            raise StudioError(str(exc)) from None

    def _groups_era_cards(self, edits) -> dict:
        """{a new unit's address: its era library entry's card} for the era units of the mod (its era_units.json)."""
        from .era_units import INDEX
        if edits is None:
            return {}
        try:
            record = json.loads((edits.folder / INDEX).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(record, dict) or not record:
            return {}
        _folder, lib = self._era_library()
        cards = {u.get("key"): str(u.get("card") or "").strip() for u in lib.get("units", [])}
        return {a: cards[k] for k, a in record.items() if a in edits.new_units and cards.get(k)}

    def _groups_kinds(self, ix, edits, info: dict) -> dict:
        """{address: its kind (the game's card type in English; None: it has none)} for the units `info`: a game
        unit's and a copy's from the type text of the unit it is (a copy's: its start unit's), an era unit's from the
        era library."""
        rows = {u["address"]: u for u in self._all_units(ix)}
        keys = {a: rows[i["real"]].get("type_key") for a, i in info.items() if i["real"] in rows}
        texts = ix.names([k for k in keys.values() if k], "us")
        out = {a: ((texts.get(k) or "").strip() or None) for a, k in keys.items()}
        out.update({a: c for a, c in self._groups_era_cards(edits).items() if a in info})
        return out

    def _groups_state(self, ix, edits, info: dict | None = None, file: dict | None = None,
                      kinds: dict | None = None) -> GroupState:
        """The mod's groups now (`info`, `file`, `kinds` when already read)."""
        info = self._board_info(ix, edits) if info is None else info
        file = self._groups_file(edits) if file is None else file
        kinds = self._groups_kinds(ix, edits, info) if kinds is None else kinds
        sources = {a: u.source for a, u in (edits.new_units.items() if edits is not None else ())}
        return GroupState(info, file, kinds, sources, self._board_tree)

    def _groups_view(self, ix, edits, state: GroupState, nation: int, factory: int, lang: str) -> list[dict]:
        """Row (nation, factory)'s groups as the board and the add form show them: [{root, name (its first unit's game
        name in `lang`, English in the code names' mode), kinds (the card types in it), units (in the board's order),
        count, most, full (no room for one more), over (more than the most: a mod made before the limit), new (its first
        unit is a new unit of the mod)}]."""
        row = state.rows.get((nation, factory), [])
        names = self._names(ix, [g["root"] for g in row], lang if lang in schema.LANGS else "us",
                            edits.new_units if edits is not None else {})
        out = []
        for g in row:
            kinds = list(dict.fromkeys(state.kinds.get(a) for a in g["units"] if state.kinds.get(a)))
            n = len(g["units"])
            out.append({"root": g["root"], "name": names.get(g["root"], g["root"]), "kinds": kinds,
                        "units": list(g["units"]), "count": n, "most": MOST, "full": n >= MOST, "over": n > MOST,
                        "new": bool(state.info[g["root"]]["new"])})
        return out

    def _groups_target(self, state: GroupState, nation: int, factory: int, group, kind):
        """The group a unit goes into in row (nation, factory): `group` the address of one of its groups' first unit
        (or of one of its units), NEW for a group of its own, None the group of `kind` (GroupState.kind_group).
        Returns the group, or None for a group of its own."""
        from .api import StudioError
        if group is None:
            return state.kind_group(kind, nation, factory)
        if group == NEW:
            return None
        g = state.find(nation, factory, str(group))
        if g is None:
            # not a game rule: the groups the board shows in that building
            raise StudioError(f"{group} isn't in one of the groups of that building: pick one of its groups, or a "
                              f"group of its own.")
        return g

    # --- a change, worked out before it's saved ---
    @staticmethod
    def _groups_touched(edits, draft) -> set:
        """The objects a draft changes (their own values or their parts'), new units made or taken out included."""
        old, new = edits.edits if edits is not None else {}, draft.edits
        out = {k[0] for k in old.keys() ^ new.keys()}
        out |= {k[0] for k in old.keys() & new.keys() if old[k].value != new[k].value}
        out |= (set(edits.new_units) if edits is not None else set()) ^ set(draft.new_units)
        return out

    def _groups_info(self, ix, edits, before: GroupState, draft) -> dict:
        """The board's units as they'd be after a draft: the ones it changes read again, the others as before."""
        touched = self._groups_touched(edits, draft)
        info = {a: i for a, i in before.info.items() if a not in touched}
        info.update(self._board_info(ix, draft, only=touched))
        return info

    def _groups_after(self, ix, edits, before: GroupState, draft, info: dict | None = None,
                      placed: dict | None = None, kinds: dict | None = None) -> GroupState:
        """The groups after a draft (`info`: its units, when already read; `placed`: {unit: the group's first unit it's
        put under, its own address for a group of its own}; `kinds`: the kinds of units it makes), the mod's menu groups
        kept in step (_groups_settle)."""
        info = self._groups_info(ix, edits, before, draft) if info is None else info
        known = dict(before.kinds)
        fresh = [a for a in info if a not in known]
        if fresh:
            known.update(self._groups_kinds(ix, draft, {a: info[a] for a in fresh}))
        known.update(kinds or {})
        file = self._groups_settle(before, info, placed or {})
        sources = {a: u.source for a, u in draft.new_units.items()}
        return GroupState(info, file, known, sources, self._board_tree)

    @staticmethod
    def _groups_settle(before: GroupState, info: dict, placed: dict) -> dict:
        """The mod's menu groups after a change, `info` its units as they'd be and `placed` the units put in a group
        ({unit: the first unit of its group, its own address for a group of its own, None where the game has it}): the
        lines of units no longer there go; each unit placed is written under its group's first unit (None: its line
        out); a new unit made buildable from the start stays in the group it stood in (under that group's first unit
        still in the row: the first remaining one, in the board's order); a unit whose group's first unit is deleted
        moves to the first remaining unit of that group (that unit, a group of its own when it's the first); an upgrade
        has none (its research says where it stands), nor has a game unit standing on its own (it does anyway)."""
        file = {a: t for a, t in before.file.items() if a in info and a not in placed}
        file.update({a: t for a, t in placed.items() if a in info and t is not None})
        leaving = set(placed)
        for a, i in info.items():
            b, g = before.info.get(a), before.of.get(a)
            if a in placed or not i["new"] or _upgrade(i) or b is None or g is None or not _upgrade(b):
                continue
            if _shown(i) and (i["nation"], i["factory"]) == (g["nation"], g["factory"]):
                file[a] = g["root"] if g["root"] in info and g["root"] not in leaving and _shown(info[g["root"]]) \
                    and (info[g["root"]]["nation"], info[g["root"]]["factory"]) == (g["nation"], g["factory"]) \
                    else before.first_left(g, info, a, leaving)
        for a, t in list(file.items()):
            if t != a and t not in info:          # its group's first unit is deleted
                g = before.of.get(a)
                file[a] = before.first_left(g, info, a, leaving) if g is not None else a
        for a, t in list(file.items()):
            if _upgrade(info[a]) or (t == a and not info[a]["new"] and a not in placed):
                del file[a]
        return file

    def _groups_check(self, ix, edits, before: GroupState, after: GroupState, lang: str) -> None:
        """StudioError when a change leaves a group holding more than MOST and more than it held before (the group
        before holding the most of its units; with two, the one holding its first unit, then the smaller), or a
        building with more groups than menugroups.MOST_GROUPS and more than it had before."""
        for (n, f), row in after.rows.items():
            had = len(before.rows.get((n, f), []))
            if len(row) > menugroups.MOST_GROUPS and len(row) > had:
                self._groups_refuse_rows(ix, edits, n, f, len(row), lang)
        for row in after.rows.values():
            for g in row:
                count = len(g["units"])
                if count <= MOST:
                    continue
                tally = Counter(before.of[a]["id"] for a in g["units"] if a in before.of)
                was = 0
                if tally:
                    most = max(tally.values())
                    cores = [k for k, c in tally.items() if c == most]
                    held = [k for k in cores if before.of.get(g["root"], {}).get("id") == k]
                    was = len(before.by_id[held[0]]["units"]) if held else min(
                        len(before.by_id[k]["units"]) for k in cores)
                if count > was:
                    self._groups_refuse(ix, edits, g, count, lang)

    def _groups_refuse(self, ix, edits, g: dict, count: int, lang: str):
        from .api import StudioError
        told = lang if lang in schema.LANGS else "us"
        first = self._names(ix, [g["root"]], told, edits.new_units if edits is not None else {}).get(g["root"])
        building = next((b["name"] for b in self._board_building_list(ix, edits, g["nation"], told)
                         if b["kind"] == g["factory"]), None) or str(g["factory"])
        # not a game rule: the owner's limit (2026-10-31: "We just need to limit how many can be in a certain group.
        # Because it's buggy."; a 7th unit in a full group: "Refuse it"). Whether the game's menu limits it isn't known.
        raise StudioError(f"There's no room in {first}'s group in {building}: it would have {count} units, and a "
                          f"group holds at most {MOST}. Take a unit out of that group, or put this one in a building "
                          f"with units of its own (Add a building…).")

    def _groups_refuse_rows(self, ix, edits, nation: int, factory: int, count: int, lang: str):
        from .api import StudioError
        told = lang if lang in schema.LANGS else "us"
        building = next((b["name"] for b in self._board_building_list(ix, edits, nation, told)
                         if b["kind"] == factory), None) or str(factory)
        # not a game rule: the owner's pick (2026-11-01, "10 groups"): the game places every row, none cut or scrolled
        # (finding F-168), and 10 is what his screen shows while a row is drawn bigger under the mouse (F-169)
        raise StudioError(f"There's no room for another group in {building}: it would have {count} groups, and a "
                          f"building holds at most {menugroups.MOST_GROUPS} so its list fits on the screen. Put this "
                          f"unit in one of its groups, or in a building with units of its own (Add a building…).")

    def _groups_full(self, ix, edits, g: dict | None, lang: str, coming: int = 1, row=None) -> None:
        """StudioError when `coming` units more don't fit in group `g`, or (`g` None: a group of their own) when the
        building `row` ((state, nation, building)) already has menugroups.MOST_GROUPS groups."""
        if g is not None and len(g["units"]) + coming > MOST:
            self._groups_refuse(ix, edits, g, len(g["units"]) + coming, lang)
        if g is None and row is not None:
            state, n, f = row
            have = len(state.rows.get((n, f), []))
            if have + 1 > menugroups.MOST_GROUPS:
                self._groups_refuse_rows(ix, edits, n, f, have + 1, lang)

    def _groups_conflict(self, ix, edits, unit: str, info: dict, lang: str):
        """StudioError: an upgrade put in a group other than its research parent's."""
        from .api import StudioError
        told = lang if lang in schema.LANGS else "us"
        parent = info[unit]["parent"]
        names = self._names(ix, [unit, parent], told, edits.new_units if edits is not None else {})
        # the game's way: an upgrade stands in the line of the unit it's researched from (its script climbs
        # IsUpgrade), so it can't be put in another group while it's one
        raise StudioError(f"{names.get(unit)} is an upgrade of {names.get(parent)} in that building, so it stands in "
                          f"{names.get(parent)}'s group. Make it buildable from the start first to put it in another "
                          f"group.")

    @staticmethod
    def _groups_save(edits, before_file: dict, file: dict) -> None:
        """menu_groups.toml as `file`, when it changed (inside `self._saving`)."""
        if edits is not None and file != before_file:
            menugroups.write(edits.folder, file)

    def _groups_guard(self, edits, changes, lang: str = "us") -> tuple[dict, dict]:
        """Work out changes [(address, prop, value)] (as BoardCalls._board_apply takes them) against the limit before
        they're saved: StudioError naming the group when one would be over it (_groups_check). Returns (the mod's menu
        groups now, as they're to be after the change), for _groups_save. Inside `self._saving`."""
        ix = self._open()
        try:
            before = self._groups_state(ix, edits)
            draft = Draft(edits).apply(changes)
            after = self._groups_after(ix, edits, before, draft)
            self._groups_check(ix, draft, before, after, lang)
        finally:
            ix.close()
        return before.file, after.file

    def _groups_gone(self, edits, address: str) -> tuple[dict, dict]:
        """The mod's menu groups (now, after the new unit `address` is deleted): its line out, the units under it
        moved to the first remaining unit of its group (_groups_settle). Inside `self._saving`."""
        file = self._groups_file(edits)
        ix = self._open()
        try:
            before = self._groups_state(ix, edits, file=file)
            if address not in before.info and address not in file and address not in file.values():
                return file, file
            draft = Draft(edits)
            draft.remove_unit(address)
            after = self._groups_after(ix, edits, before, draft)
        finally:
            ix.close()
        return file, after.file

    def _groups_place(self, edits, address: str, root: str | None) -> None:
        """Write a unit just put in group `root` (its first unit's address; None: a group of its own) into the mod's
        menu groups, when it's bought from the start (an upgrade stands where its research puts it). Inside
        `self._saving`."""
        file = self._groups_file(edits)
        ix = self._open()
        try:
            i = self._board_info(ix, edits, only={address}).get(address)
        finally:
            ix.close()
        want = dict(file)
        want.pop(address, None)
        if i is not None and not _upgrade(i):
            want[address] = root or address
        self._groups_save(edits, file, want)

    # --- what the pages ask ---
    def _groups_offer(self, ix, edits, state: GroupState, kind, nation, factory, group, name: str,
                      lang: str) -> tuple[dict | None, dict | None]:
        """(the group a unit of card type `kind` would go into in a build menu, for a page: {"root" (None: a group of
        its own), "name" (its first unit's game name; this unit's `name` for a group of its own), "count", "most",
        "full", "new" (its first unit is a new unit of the mod; True for a group of its own), "choices": [{root, name,
        count, full}] every group of that building}, that group (None: a group of its own)). (None, None) for a build
        menu that isn't one of the board's buildings. `group` as _groups_target takes it."""
        try:
            n, f = nations.check(nation), int(factory)
        except (nations.NationError, TypeError, ValueError):
            return None, None
        if f not in ALL_ROWS:
            return None, None
        g = self._groups_target(state, n, f, group, kind)
        view = self._groups_view(ix, edits, state, n, f, lang)
        mine = next((v for v in view if g is not None and v["root"] == g["root"]), None)
        # a group of its own is full when the building already has the most groups (menugroups.MOST_GROUPS)
        full = bool(mine["full"]) if mine else len(view) >= menugroups.MOST_GROUPS
        return {"root": mine["root"] if mine else None, "name": mine["name"] if mine else name,
                "count": mine["count"] if mine else 0, "most": MOST, "full": full,
                "new": mine["new"] if mine else True, "groups": len(view), "most_groups": menugroups.MOST_GROUPS,
                "choices": [{"root": v["root"], "name": v["name"], "count": v["count"], "full": v["full"]}
                            for v in view]}, g
