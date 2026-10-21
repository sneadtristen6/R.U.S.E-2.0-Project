"""The board (StudioApi's BoardCalls; the owner, 2026-10-18: "a new screen for buildings where you're able to edit the
order and how many units are for what building", and research as a list: "you'll select it and then select the spot
where it goes and then boom"): one nation's buildings, each a row of the units its build menu offers, in the game's
order. A unit is put in a row (one of the nation's own, a copy of another nation's, an era unit), moved along it or to
another row, taken out, and researched from the unit it sits under.

What it follows, as the game does it:
- A building's tab shows its units and its research buttons on one line, in the order of each one's place number
  (PositionInMenu); the number only orders them, so the board keeps each row's numbers rising and changes as few as
  it can.
- A research marked as an upgrade (IsUpgrade) is drawn beside the unit it's researched from, in the same tab, which
  the game needs to find there: so research under a unit of the same building is an upgrade, as all 50 of the game's
  are, and research from a unit of another building is research without the upgrade flag (not tried in the game yet:
  the board says so on the unit).
- Every game unit's battle dates run "from a year on" (ShowInMenu: 1945, 1942, 1939, Total War, Nuclear); a unit the
  board adds is shown at every one (the owner, 2026-10-18: "they need to be added into any given date ... included in
  all of them"); a researched unit is shown only where the unit it's researched from is (the build refuses one shown
  where its parent is hidden: rule unit-research-shown-parent).
- Research stays inside one nation (rule unit-research-parent: the match never finishes loading otherwise).

Add a building (the owner, 2026-10-18: "Adding a new building and giving units to it"): a copy of one of the game's
buildings that make units, for this nation, either making the same units as the building it copies (its kind: it
joins that row and that tab) or units of its own: a kind no game building has (rusemod.ownbuildings: 6, 4, 7, at most
three a nation, "buildings 3 limit"), a row and a tab of its own, filled like any other row. Every nation that has one of
a kind makes its own units of that kind in it."""
from __future__ import annotations

import threading

from rusemod import nations, ownbuildings

ROWS = (8, 13, 10, 11, 9, 12)  # the buildings that make units, in the order of the game's build tabs: Barracks,
# Artillery & AA Base, Armor Base, Anti-Tank Base, Airfield, Prototype Base
ROW_BASE = {8: 100, 13: 200, 10: 300, 11: 400, 9: 500, 12: 600}  # the game's place numbers start at these (measured)
OWN_BASE = 700   # a building with units of its own: its units' place numbers start here (buildings1: 701, 702)
ALL_ROWS = ROWS + ownbuildings.KINDS   # the board's rows in order: the game's, then the buildings with units of their own
KIND, MENU = "TypeBatiment", "Menu"   # a building's kind (the units it makes: their Factory) and its build menu (tab)
AIRFIELD = 9
MOST_TRIED = 10  # the most places one of the game's buildings uses (F-73): more is allowed, said as not tried yet
SHOW, SLOT, FACTORY, NATION = "ShowInMenu", "PositionInMenu", "Factory", "Nationalite"
DATES = 5        # ShowInMenu's battle dates: 1945, 1942, 1939, Total War, Nuclear
YEARS = ((2, 1939), (1, 1942), (0, 1945))  # (its place in ShowInMenu, the year): the earliest first
PICTURES_MOST = 400  # build-menu pictures one board_cards call gives
_PICTURES = threading.Lock()  # board_cards: one at a time (the cache's picture files)


def dates_of(shows) -> dict:
    """A unit's battle dates as the board says them: {"from": the first year a battle shows it (1939, 1942, 1945; None:
    no dated battle), "nuclear": whether Nuclear battles show it}. No list: every battle."""
    if not shows:
        return {"from": 1939, "nuclear": True}
    on = [bool(x) for x in list(shows) + [0] * DATES][:DATES]
    return {"from": next((year for i, year in YEARS if on[i]), None), "nuclear": on[4]}


def row_base(factory: int) -> int:
    """The place number a row's units start after."""
    return ROW_BASE.get(factory, OWN_BASE)


def _on(shows, date: int) -> bool:
    """Whether a unit is shown at battle date `date` (no list: at every one)."""
    return True if shows is None else bool(date < len(shows) and shows[date])


class BoardCalls:
    """Mixed into StudioApi: uses its _open, _edits, _saving, _all_units, _names, _resolve, _upgrade_links,
    _card_view, new_unit, delete_unit, era_unit_add, _era_library and _era_record."""

    # --- what the board reads ---
    def _board_need_mod(self):
        from .api import StudioError
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: the board's changes are saved in it.")
        return edits

    @staticmethod
    def _board_row(factory) -> int:
        from .api import StudioError
        if isinstance(factory, bool) or factory not in ALL_ROWS:
            # not a game rule: the buildings the board shows (the ones that make units)
            raise StudioError(f"{factory}: not one of the buildings that make units")
        return factory

    def _building_kind(self, ix, address: str) -> tuple:
        """A game building's (kind, build menu, prices, battle dates) as the game has them, kept for the session."""
        from .api import _props
        cache = self.__dict__.setdefault("_board_kinds", {})
        key = (str(getattr(ix, "path", "")), address)
        if key not in cache:
            props = _props(ix.show(address))
            first = lambda p: ((props.get(p) or {}).get("numbers") or [None])[0]  # noqa: E731
            cache[key] = (None if first(KIND) is None else int(first(KIND)),
                          None if first(MENU) is None else int(first(MENU)),
                          (props.get("ProductionPrice") or {}).get("numbers") or [0],
                          (props.get(SHOW) or {}).get("numbers"))
        return cache[key]

    def _board_building_list(self, ix, edits, nation: int | None, lang: str = "base") -> list[dict]:
        """The buildings that make units (the game's and the mod's new ones, as the mod has them; nation `nation`'s
        only when it's given): [{address, name, new, source (a new one's game building), nation, kind, menu}], the
        game's first."""
        from .api import KIND_OF, _tail
        games = [u for u in self._all_units(ix) if KIND_OF.get(u["class"]) == "buildings"]
        by_address = {u["address"]: u for u in games}

        def mine(address, prop, fallback):
            v = edits.get(address, prop) if edits is not None else None
            return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else fallback
        out = []
        for u in games:
            kind, menu, _p, _s = self._building_kind(ix, u["address"])
            out.append({"address": u["address"], "name": None, "key": u.get("key"), "new": False, "source": None,
                        "nation": mine(u["address"], NATION, u["nation"]), "kind": mine(u["address"], KIND, kind),
                        "menu": mine(u["address"], MENU, menu)})
        for address, unit in sorted((edits.new_units if edits is not None else {}).items()):
            src = by_address.get(unit.source)
            if src is None:
                continue
            kind, menu, _p, _s = self._building_kind(ix, unit.source)
            out.append({"address": address, "name": unit.name, "key": None, "new": True, "source": unit.source,
                        "nation": mine(address, NATION, src["nation"]), "kind": mine(address, KIND, kind),
                        "menu": mine(address, MENU, menu)})
        out = [b for b in out if b["kind"] in ALL_ROWS and (nation is None or b["nation"] == nation)]
        keys = sorted({b["key"] for b in out if b["key"]})
        names = ix.names(keys, "us" if lang == "base" else lang) if keys else {}
        for b in out:
            if b["name"] is None:
                b["name"] = (names.get(b["key"]) or "").strip() or _tail(b["address"])
        return out

    def _own_menus(self, ix, edits) -> set:
        """{(nation, kind)}: the build menus the mod's buildings with units of their own make (StudioApi.new_unit).
        Only the mod's new buildings are such (no game building has those kinds)."""
        from .api import KIND_OF
        if edits is None or not edits.new_units:
            return set()
        games = {u["address"]: u for u in self._all_units(ix) if KIND_OF.get(u["class"]) == "buildings"}
        out = set()
        for address, unit in edits.new_units.items():
            src = games.get(unit.source)
            kind = edits.get(address, KIND)
            if src is None or not isinstance(kind, int) or kind not in ownbuildings.KINDS:
                continue
            nation = edits.get(address, NATION)
            out.add((nation if isinstance(nation, int) else src["nation"], kind))
        return out

    def _board_info(self, ix, edits, nation: int | None = None) -> dict:
        """The units (the game's and the mod's new ones; not buildings) as the current mod has them, those of `nation`
        only when it's given: {address: {real, new, kind, nation, factory, slot, game_slot, shows, game_shows, parent,
        flag, has_flag, has_link, research}}. `has_link` / `has_flag`: whether the game's object (a new unit's source)
        has a research link / an upgrade flag of its own, so taking it out needs a `delete`."""
        from .api import KIND_OF, RESEARCH, UPGRADE, UPGRADE_FLAG, _props
        from .edits import REMOVED
        rows = {u["address"]: u for u in self._all_units(ix)}
        links = self._upgrade_links(ix, edits)
        game_links = ix.links(UPGRADE)
        new_units = edits.new_units if edits is not None else {}
        out = {}
        for address in list(rows) + [a for a in new_units if a not in rows]:
            real, unit = self._resolve(edits, address)
            u = rows.get(real)
            if u is None or KIND_OF.get(u["class"]) in (None, "buildings"):
                continue
            mine = (lambda prop: edits.get(address, prop)) if edits is not None else (lambda prop: None)
            own_nation = mine(NATION)
            n = int(own_nation) if isinstance(own_nation, (int, float)) else u["nation"]
            if nation is not None and n != nation:
                continue
            props = _props(ix.show(real))
            factory, slot, shows, flag = mine(FACTORY), mine(SLOT), mine(SHOW), mine(UPGRADE_FLAG)
            game_shows = (props.get(SHOW) or {}).get("numbers")
            game_flag = (props.get(UPGRADE_FLAG) or {}).get("numbers")
            research = {}
            for p in RESEARCH:
                own = mine(p)
                research[p] = None if own is REMOVED else own if own is not None else (
                    (props.get(p) or {}).get("numbers", [None])[0])
            out[address] = {
                "real": real, "new": unit is not None, "kind": KIND_OF[u["class"]], "nation": n,
                "factory": int(factory) if isinstance(factory, (int, float)) else u["factory"],
                "slot": int(slot) if isinstance(slot, (int, float)) else u["slot"],
                "game_slot": u["slot"] if unit is None else None,
                "shows": list(shows) if isinstance(shows, list) else game_shows, "game_shows": game_shows,
                "parent": links.get(address),
                "flag": (flag is not REMOVED and bool(flag)) if flag is not None else bool(game_flag and game_flag[0]),
                "has_flag": game_flag is not None, "has_link": real in game_links, "research": research}
        return out

    @staticmethod
    def _board_shown(i: dict) -> bool:
        """Whether a unit is in its build menu at some battle date as the mod has it."""
        return True if i["shows"] is None else any(i["shows"])

    def _board_tree(self, info: dict, nation: int, factory: int) -> list[tuple[str, int]]:
        """A row's units in the board's order, [(address, depth)]: the units shown there, by place number (then name),
        each followed by the ones researched from it in the same row, pushed in (depth 1, 2...)."""
        here = {a: i for a, i in info.items()
                if i["nation"] == nation and i["factory"] == factory and self._board_shown(i)}
        order = sorted(here, key=lambda a: (here[a]["slot"] is None, here[a]["slot"] or 0, a))
        kids: dict[str, list[str]] = {}
        top = []
        for a in order:
            p = here[a]["parent"]
            (kids.setdefault(p, []) if p in here and p != a else top).append(a)
        out, seen = [], set()

        def walk(a, depth):
            if a in seen:  # a loop the mod made by hand: shown once
                return
            seen.add(a)
            out.append((a, depth))
            for k in kids.get(a, []):
                walk(k, depth + 1)
        for a in top + order:  # (one inside a loop, with nothing above it shown: at the end)
            walk(a, 0)
        return out

    @staticmethod
    def _board_slots(seq: list[str], info: dict, base: int) -> list[tuple[str, str, object]]:
        """The place numbers that keep `seq` in order with as few changes as there can be: each unit keeps its number
        while it's above the one before it, else takes the one after. Returns the changes [(address, prop, value)],
        value None where a game unit's own number comes back."""
        changes, last = [], base
        for a in seq:
            i = info[a]
            slot = i["slot"] if i["slot"] is not None and i["slot"] > last else last + 1
            last = slot
            if slot == i["slot"]:  # where it was
                continue
            changes.append((a, SLOT, None if (not i["new"] and slot == i["game_slot"]) else slot))
            i["slot"] = slot
        return changes

    @staticmethod
    def _board_apply(edits, changes) -> None:
        """Save the changes [(address, prop, value)] at once (value None: the game's own value back)."""
        from .edits import Edit
        if not changes:
            return
        for address, prop, value in changes:
            k = edits.key(address, prop)
            if value is None:
                edits.edits.pop(k, None)
            else:
                edits.edits[k] = Edit(k[0], k[1], value, None)
        edits.save()

    def _board_read(self, nation: int | None = None):
        """(the mod's changes read again, the units as they have them): inside `self._saving`."""
        from .edits import ModEdits
        edits = ModEdits(self._board_need_mod().folder)
        ix = self._open()
        try:
            return edits, self._board_info(ix, edits, nation)
        finally:
            ix.close()

    def board(self, nation: int, lang: str = "base") -> dict:
        """Nation `nation`'s board: {"nation", "can": whether a mod is picked, "rows": [{"factory", "units": [{address,
        name, new, kind, depth (pushed in under the unit before it: researched from it), parent, parent_name,
        parent_factory (the parent's building when it's another), upgrade, dates (dates_of), research {UpgradePrice,
        UpgradeTime} (researched units), untried_mix (a plane outside the Airfield or a vehicle in it: not tried in the
        game)}], "most": the most units it shows at one battle date, "untried": more than MOST_TRIED, "buildings":
        [{address, name, new}] the nation's buildings of that kind (a copy that makes the same units is one more),
        "own": a building with units of its own}] (the game's rows, then its buildings with units of their own),
        "own_left": how many more buildings with units of their own it can have, "taken_out": the nation's own units in
        no build menu (hidden by the mod, or never shown in the game), [{address, name, factory, new}]}."""
        from .api import EditsFileError
        n = nations.check(nation)
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        ix = self._open()
        try:
            info = self._board_info(ix, edits, n)
            parents = {i["parent"] for i in info.values() if i["parent"]}
            names = self._names(ix, set(info) | parents, lang, edits.new_units if edits else {})
            blist = self._board_building_list(ix, edits, n, lang)
        finally:
            ix.close()
        own_kinds = [k for k in ownbuildings.KINDS if any(b["kind"] == k for b in blist)]
        rows = []
        for f in list(ROWS) + own_kinds:
            mine = [b for b in blist if b["kind"] == f]
            tree = self._board_tree(info, n, f)
            boxes = []
            for a, depth in tree:
                i = info[a]
                p = i["parent"]
                pf = info[p]["factory"] if p in info else None
                boxes.append({"address": a, "name": names.get(a, a), "new": i["new"], "kind": i["kind"],
                              "depth": depth, "parent": p, "parent_name": names.get(p) if p else None,
                              "parent_factory": pf if p and pf != f else None, "upgrade": i["flag"],
                              "dates": dates_of(i["shows"]), "research": i["research"] if p else None,
                              "untried_mix": i["kind"] != "infantry" and (i["kind"] == "air") != (f == AIRFIELD)})
            most = max((sum(_on(info[a]["shows"], d) for a, _d in tree) for d in range(DATES)), default=0)
            rows.append({"factory": f, "building": mine[0]["name"] if mine else None, "units": boxes, "most": most,
                         "untried": most > MOST_TRIED, "own": f in ownbuildings.KINDS,
                         "buildings": [{"address": b["address"], "name": b["name"], "new": b["new"]} for b in mine]})
        out_of = sorted(({"address": a, "name": names.get(a, a), "factory": i["factory"], "new": i["new"]}
                         for a, i in info.items() if not self._board_shown(i) and i["factory"] in ALL_ROWS),
                        key=lambda u: (ALL_ROWS.index(u["factory"]), u["name"].casefold()))
        return {"nation": n, "can": edits is not None, "rows": rows, "taken_out": out_of,
                "own_left": ownbuildings.MOST - len(own_kinds)}

    def board_picker(self, nation: int, lang: str = "base") -> dict:
        """What the board's empty box offers: {"nations": [{nation, name, units: [{address, name, kind, factory, new,
        here: on this nation's board, taken_out: this nation's but in no build menu}]}] (every nation's units in a
        building that makes units, this nation first, the others' in a build menu), "eras": [{era, units: [{key, name,
        nation, kind, factory, added}]}] (the era units downloaded)}."""
        from rusemod import schema
        from .api import EditsFileError
        from .era_units import ERAS, kind_of
        n = nations.check(nation)
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        ix = self._open()
        try:
            info = {a: i for a, i in self._board_info(ix, edits).items() if i["factory"] in ALL_ROWS}
            names = self._names(ix, list(info), lang, edits.new_units if edits else {})
        finally:
            ix.close()
        groups = []
        for m in [n] + [x for x in range(len(nations.NATIONS)) if x != n]:
            units = [{"address": a, "name": names.get(a, a), "kind": i["kind"], "factory": i["factory"],
                      "new": i["new"], "here": m == n and self._board_shown(i),
                      "taken_out": m == n and not self._board_shown(i)}
                     for a, i in info.items() if i["nation"] == m and (m == n or self._board_shown(i))]
            units.sort(key=lambda u: (ALL_ROWS.index(u["factory"]), u["name"].casefold()))
            if units:
                groups.append({"nation": m, "name": schema.nation(m, lang), "units": units})
        _folder, lib = self._era_library()
        record = self._era_record() if self._mod_dir() is not None else {}
        eras = []
        for era in ERAS:
            units = [{"key": u["key"], "name": u["name"], "nation": u["nation"], "kind": kind_of(u),
                      "factory": u.get("factory") if u.get("factory") in ROWS else None, "added": u["key"] in record}
                     for u in lib["units"] if u["era"] == era]
            if units:
                eras.append({"era": era, "units": sorted(units, key=lambda u: (u["nation"], u["name"].casefold()))})
        return {"nations": groups, "eras": eras}

    def board_where(self, address: str, lang: str = "base") -> dict:
        """Where a unit is on its nation's board, for its page in the Units tab: {"nation", "factory" (None: not in
        a building that makes units), "building": the game's name for it, "place": its place in that building's row
        (1 = first; None: in no build menu), "count": how many are in the row}."""
        from .api import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        ix = self._open()
        try:
            info = self._board_info(ix, edits)
            i = info.get(address)
            if i is None:
                return {"nation": None, "factory": None, "building": None, "place": None, "count": 0}
            blist = self._board_building_list(ix, edits, i["nation"], lang)
        finally:
            ix.close()
        building = next((b["name"] for b in blist if b["kind"] == i["factory"]), None)
        if i["factory"] not in ROWS and building is None:  # (a kind of its own with no building: on no row)
            return {"nation": i["nation"], "factory": None, "building": None, "place": None, "count": 0}
        order = [a for a, _d in self._board_tree(info, i["nation"], i["factory"])]
        return {"nation": i["nation"], "factory": i["factory"], "building": building,
                "place": order.index(address) + 1 if address in order else None, "count": len(order)}

    # --- buildings ---
    def board_building_sources(self, nation: int, lang: str = "base") -> dict:
        """What Add a building offers: {"buildings": [{address, name, nation, nation_name, kind}] the game's buildings
        that make units, nation `nation`'s first, "own_left": how many more buildings with units of their own it can
        have, "patch_kinds": the kinds of those that need the game patch (rusemod.ownbuildings)}."""
        from rusemod import schema
        from .api import EditsFileError
        n = nations.check(nation)
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        ix = self._open()
        try:
            blist = self._board_building_list(ix, edits, None, lang)
        finally:
            ix.close()
        used = {b["kind"] for b in blist if b["nation"] == n and b["kind"] in ownbuildings.KINDS}
        games = [b for b in blist if not b["new"] and b["kind"] in ROWS]
        games.sort(key=lambda b: (b["nation"] != n, b["nation"], ROWS.index(b["kind"]), b["name"].casefold()))
        return {"buildings": [{"address": b["address"], "name": b["name"], "nation": b["nation"],
                               "nation_name": schema.nation(b["nation"], lang), "kind": b["kind"]} for b in games],
                "own_left": ownbuildings.MOST - len(used),
                "next_kind": next((k for k in ownbuildings.KINDS if k not in used), None),
                "patch_kinds": sorted(ownbuildings.PATCHED)}

    def board_add_building(self, nation: int, source: str, name: str, own: bool = False, lang: str = "base") -> dict:
        """A new building for nation `nation`: a copy of the game's building `source` called `name`, shown at every
        battle date, either making the same units as `source`'s kind (`own` False: it joins that row and tab) or units
        of its own (`own`: the first kind of rusemod.ownbuildings the nation hasn't used, its own build menu, a row and
        a tab of its own). Returns board() with "made": its address and "kind"."""
        from .api import StudioError
        from .edits import ModEdits
        n = nations.check(nation)
        edits = self._board_need_mod()
        name = (name or "").strip()
        if not name:
            raise StudioError("Give the new building a name.")
        ix = self._open()
        try:
            blist = self._board_building_list(ix, edits, None, lang)
            src = next((b for b in blist if b["address"] == source and not b["new"] and b["kind"] in ROWS), None)
            if src is None:
                # not a game rule: the buildings Add a building offers to copy
                raise StudioError(f"{source}: pick one of the game's buildings that make units to copy")
            _kind, _menu, prices, shows = self._building_kind(ix, source)
        finally:
            ix.close()
        kind = None
        if own:
            used = {b["kind"] for b in blist if b["nation"] == n and b["kind"] in ownbuildings.KINDS}
            free = [k for k in ownbuildings.KINDS if k not in used]
            if not free:
                # rule: own-units-three
                raise StudioError(f"This nation already has {ownbuildings.MOST} buildings with units of their own, the "
                                  f"most there can be. Copy a building that makes the same units as one of them "
                                  f"instead.")
            kind = free[0]
        made = self.new_unit(source, name, prices[0] or 0, unique=True)["address"]
        changes = []
        if src["nation"] != n:
            changes.append((made, NATION, n))
        if kind is not None:
            changes += [(made, KIND, kind), (made, MENU, ownbuildings.MENU_OF[kind])]
        if shows and not all(shows):
            changes.append((made, SHOW, [1] * len(shows)))
        with self._saving:
            self._board_apply(ModEdits(edits.folder), changes)
        return {**self.board(n, lang), "made": made, "kind": kind}

    def board_remove_building(self, nation: int, address: str, lang: str = "base") -> dict:
        """Take one of the mod's new buildings of nation `nation` out of the mod. Refused while it's the nation's only
        building of a kind of its own and units are still in its row (they'd be in no building). Returns board()."""
        from .api import StudioError
        n = nations.check(nation)
        edits = self._board_need_mod()
        ix = self._open()
        try:
            blist = self._board_building_list(ix, edits, n, lang)
            info = self._board_info(ix, edits, n)
        finally:
            ix.close()
        b = next((x for x in blist if x["address"] == address and x["new"]), None)
        if b is None:
            raise StudioError(f"{address} isn't one of this nation's new buildings")
        others = [x for x in blist if x["kind"] == b["kind"] and x["address"] != address]
        if b["kind"] in ownbuildings.KINDS and not others and self._board_tree(info, n, b["kind"]):
            # not a game rule: the board keeps every unit in a building
            raise StudioError(f"Move or take out the units in {b['name']} first: with no building of their own they "
                              f"couldn't be built anywhere.")
        res = self.delete_unit(address)
        if res.get("deleted") is None:
            raise StudioError(f"{b['name']} couldn't be taken out of the mod")
        return {**self.board(n, lang), "deleted": address}

    def board_cards(self, addresses) -> dict:
        """The build-menu pictures of the units `addresses` (the board asks once its boxes are drawn): {address: a
        cache address of the picture, or None}. One call at a time: two boards drawn at once would write the same
        picture into the cache together."""
        out = {}
        with _PICTURES:
            for a in list(addresses or [])[:PICTURES_MOST]:
                try:
                    card = self._card_view(str(a))
                except (OSError, ValueError, KeyError):
                    card = None
                out[a] = card["url"] if card else None
        return out

    # --- what the board changes ---
    def _board_top(self, info: dict, nation: int, factory: int, without=()) -> list[str]:
        return [a for a, depth in self._board_tree(info, nation, factory) if depth == 0 and a not in without]

    def _board_seq(self, info: dict, nation: int, factory: int, top: list[str], last_child: tuple | None = None):
        """The row's whole order for the top-level order `top`: each unit, then the ones researched from it in the row
        (`last_child` (parent, child): that child after its parent's others)."""
        tree = self._board_tree(info, nation, factory)
        kids: dict[str, list[str]] = {}
        stack: list[str] = []
        for a, d in tree:
            del stack[d:]
            if d:
                kids.setdefault(stack[-1], []).append(a)
            stack.append(a)
        if last_child:
            p, c = last_child
            for v in kids.values():
                if c in v:
                    v.remove(c)
            kids.setdefault(p, []).append(c)
        seq, seen = [], set()

        def walk(a):
            if a in seen:
                return
            seen.add(a)
            seq.append(a)
            for k in kids.get(a, []):
                walk(k)
        for a in top + [a for a, d in tree if d == 0]:  # (anything left out of `top`: where it was)
            walk(a)
        return seq

    def _board_place(self, info, nation, factory, address, index) -> list:
        """Changes that put `address` (already in row `factory`) at top-level place `index` (None: the end)."""
        top = self._board_top(info, nation, factory, without=(address,))
        top.insert(len(top) if index is None else max(0, min(int(index), len(top))), address)
        return self._board_slots(self._board_seq(info, nation, factory, top), info, row_base(factory))

    @staticmethod
    def _board_flag(address: str, i: dict, same_row: bool) -> list:
        """The upgrade flag as the board keeps it: on beside a unit of the same building, off from another."""
        from .api import UPGRADE_FLAG
        from .edits import REMOVED
        i["flag"] = same_row
        if same_row:
            return [(address, UPGRADE_FLAG, None if i["has_flag"] else 1)]
        return [(address, UPGRADE_FLAG, REMOVED if i["has_flag"] else None)]

    @staticmethod
    def _board_unlink(address: str, i: dict) -> list:
        """Changes that make a unit buildable from the start: its research link and upgrade flag out."""
        from .api import UPGRADE, UPGRADE_FLAG
        from .edits import REMOVED
        i["parent"], i["flag"] = None, False
        return [(address, UPGRADE, REMOVED if i["has_link"] else None),
                (address, UPGRADE_FLAG, REMOVED if i["has_flag"] else None)]

    @staticmethod
    def _board_dates(address: str, i: dict, parent: dict) -> list:
        """A researched unit shown only at the battle dates its parent is (rule unit-research-shown-parent)."""
        mine = list(i["shows"] or [1] * DATES)
        both = [1 if (m and _on(parent["shows"], k)) else 0 for k, m in enumerate(mine)]
        if both == [1 if m else 0 for m in mine]:
            return []
        i["shows"] = both
        return [(address, SHOW, both)]

    def board_order(self, nation: int, factory: int, order, lang: str = "base") -> dict:
        """Put row `factory`'s units in the order `order` (its top-level units' addresses, as the page has them after a
        drag); the ones researched from each follow it. Returns board()."""
        from .api import StudioError
        n, f = nations.check(nation), self._board_row(factory)
        with self._saving:
            edits, info = self._board_read(n)
            top = self._board_top(info, n, f)
            order = [a for a in (order or []) if a in top]
            if len(order) != len(set(order)):
                raise StudioError("Each unit can be in the order once.")
            self._board_apply(edits, self._board_slots(self._board_seq(info, n, f, order), info, row_base(f)))
        return self.board(n, lang)

    def board_put(self, nation: int, factory: int, unit: str = "", era: str = "", index=None,
                  lang: str = "base") -> dict:
        """Put a unit in row `factory` of nation `nation`'s board at top-level place `index` (None: the end): `unit`
        one of the nation's own (taken out: put back at its own battle dates, or at every one when the game shows it
        at none; in another row: moved there with the units researched from it), another nation's game unit (a copy
        named as it is, the Units tab's New unit, shown at every battle date), another nation's new unit of this mod
        (moved to this nation, its research links to that nation taken out); or `era` an era unit's key (added as Add
        to my mod does, not researched, shown at every battle date). Returns board() with "made": its address and
        "note": {"copied", "moved_nation", "unlinked": the names of units no longer researched from it}."""
        from .api import StudioError, _props, _tail
        n, f = nations.check(nation), self._board_row(factory)
        edits = self._board_need_mod()
        if bool(unit) == bool(era):
            raise StudioError("Pick one unit to put here.")
        if f in ownbuildings.KINDS:
            ix = self._open()
            try:
                has = (n, f) in self._own_menus(ix, edits)
            finally:
                ix.close()
            if not has:
                # not a game rule: the board puts units only in a building the nation has
                raise StudioError("This nation has no building of that kind: add one with Add a building first.")
        note: dict = {}
        if era:
            address = self.era_unit_add(str(era), n, f, research_from=None)["address"]
            note["era"] = True
        else:
            ix = self._open()
            try:
                info = self._board_info(ix, edits)
                if unit not in info:
                    raise StudioError(f"{unit} isn't a unit the board can put in a building")
                english = self._names(ix, [unit], "us", edits.new_units).get(unit) or _tail(unit)
                price = (_props(ix.show(info[unit]["real"])).get("ProductionPrice") or {}).get("numbers") or [0]
            finally:
                ix.close()
            if info[unit]["nation"] == n or info[unit]["new"]:
                address = unit
                note["moved_nation"] = info[unit]["nation"] != n
            else:
                address = self.new_unit(unit, english, price[0] or 0, n, f, unique=True)["address"]
                note["copied"] = True
        unlinked = []
        with self._saving:
            edits, info = self._board_read()
            i = info[address]
            changes = []
            if i["factory"] != f or note.get("moved_nation"):
                # moved: the units researched from it in its row come along (the game draws them beside it)
                moving = [address] + [a for a, _d in self._board_desc(info, address)]
                old = (i["nation"], i["factory"])
                for a in moving:
                    game_f = None if info[a]["new"] else self._game_factory(a)
                    changes.append((a, FACTORY, None if game_f == f else f))
                    info[a]["factory"] = f
                    if info[a]["nation"] != n:
                        changes.append((a, NATION, n))
                        info[a]["nation"] = n
                for child, ci in info.items():
                    if ci["parent"] not in moving or child in moving:
                        continue
                    if (ci["nation"], ci["factory"]) == old and note.get("moved_nation"):
                        changes += self._board_unlink(child, ci)  # research stays in one nation
                        unlinked.append(child)
                    else:  # its parent's building changed: upgrade or plain research again
                        changes += self._board_flag(child, ci, ci["factory"] == f)
                p = i["parent"]
                if p in info and info[p]["nation"] != n:
                    changes += self._board_unlink(address, i)
                elif p in info:
                    changes += self._board_flag(address, i, info[p]["factory"] == f)
            if not self._board_shown(i) or note.get("copied") or note.get("era"):
                game_on = not i["new"] and bool(i["game_shows"]) and any(i["game_shows"])
                full = [1] * len(i["game_shows"] or [1] * DATES)
                changes.append((address, SHOW, None if game_on else full))
                i["shows"] = i["game_shows"] if game_on else full
            if i["parent"] in info:  # never shown where the unit it's researched from isn't (the build refuses it)
                changes += self._board_dates(address, i, info[i["parent"]])
            self._board_apply(edits, changes)
            self._board_apply(edits, self._board_place(info, n, f, address, index))
            if unlinked:
                ix = self._open()
                try:
                    note["unlinked"] = list(self._names(ix, unlinked, lang, edits.new_units).values())
                finally:
                    ix.close()
        return {**self.board(n, lang), "made": address, "note": note}

    def _game_factory(self, address: str):
        ix = self._open()
        try:
            return next((u["factory"] for u in self._all_units(ix) if u["address"] == address), None)
        finally:
            ix.close()

    @staticmethod
    def _board_desc(info: dict, address: str) -> list[tuple[str, int]]:
        """The units researched from `address` in its row, directly or not, [(address, depth)]."""
        row = (info[address]["nation"], info[address]["factory"])
        out, seen, todo = [], {address}, [(address, 0)]
        while todo:
            a, d = todo.pop(0)
            for c, ci in info.items():
                if ci["parent"] == a and (ci["nation"], ci["factory"]) == row and c not in seen:
                    seen.add(c)
                    out.append((c, d + 1))
                    todo.append((c, d + 1))
        return out

    def board_move(self, nation: int, address: str, factory: int, index=None, lang: str = "base") -> dict:
        """Move one of nation `nation`'s units (and the units researched from it in its row) to row `factory`, or along
        its row, to top-level place `index`. Returns board()."""
        from .api import StudioError
        n = nations.check(nation)
        with self._saving:
            _edits, info = self._board_read(n)
        if address not in info:
            raise StudioError(f"{address} isn't one of this nation's units")
        return self.board_put(n, factory, unit=address, index=index, lang=lang)

    def board_research(self, nation: int, address: str, parent: str | None = None, lang: str = "base") -> dict:
        """Research nation `nation`'s unit `address` from `parent` (a unit of the same nation shown in a build menu,
        not one researched from it), or make it buildable from the start (None). Under a unit of its own building it's
        an upgrade, drawn after that unit's others; from another building, research without the upgrade flag (not
        tried in the game yet). It's then shown only at the battle dates its parent is. Returns board() with "note":
        {"dates": whether its battle dates were narrowed}."""
        from .api import RESEARCH, StudioError, UPGRADE
        from .edits import Link
        n = nations.check(nation)
        note = {}
        with self._saving:
            edits, info = self._board_read(n)
            i = info.get(address)
            if i is None:
                raise StudioError(f"{address} isn't one of this nation's units")
            if parent is None:
                if i["parent"] is not None:
                    self._board_apply(edits, self._board_unlink(address, i))
                return {**self.board(n, lang), "note": note}
            p = info.get(parent)
            if p is None:
                # rule unit-research-parent: researched from another nation's unit, a match never finishes loading
                raise StudioError("A unit can only be researched from one of its own nation's units.")
            if not self._board_shown(p):
                # rule unit-research-shown-parent: the game stops when that build menu opens
                raise StudioError("That unit isn't in any build menu: put it back on the board first.")
            up, seen = parent, set()
            while up is not None and up not in seen:  # never from one researched from it
                if up == address:
                    raise StudioError("A unit can't be researched from one that's researched from it.")
                seen.add(up)
                up = info[up]["parent"] if up in info else None
            changes = [(address, UPGRADE, Link(parent))]
            same = p["factory"] == i["factory"]
            changes += self._board_flag(address, i, same)
            for prop, value in RESEARCH.items():
                if i["research"].get(prop) is None:
                    changes.append((address, prop, value))
                    i["research"][prop] = value
            i["parent"] = parent
            dates = self._board_dates(address, i, p)
            note["dates"] = bool(dates)
            self._board_apply(edits, changes + dates)
            if same:
                top = self._board_top(info, n, i["factory"])
                seq = self._board_seq(info, n, i["factory"], top, last_child=(parent, address))
                self._board_apply(edits, self._board_slots(seq, info, row_base(i["factory"])))
        return {**self.board(n, lang), "note": note}

    def board_take_out(self, nation: int, address: str, researched=None, lang: str = "base") -> dict:
        """Take a unit off nation `nation`'s board: a new unit of the mod goes from the mod (delete_unit, which may ask
        first: "ask", the units researched from it); a game unit leaves every battle date's build menu (hidden, never
        deleted), and the units researched from it are researched from the unit it was researched from, else
        buildable from the start ("relinked": their names). Returns board()."""
        from .api import StudioError, UPGRADE
        from .edits import Link
        n = nations.check(nation)
        with self._saving:
            edits, info = self._board_read(n)
        i = info.get(address)
        if i is None:
            raise StudioError(f"{address} isn't one of this nation's units")
        if i["new"]:
            res = self.delete_unit(address, researched)
            if res.get("deleted") is None:
                return {**self.board(n, lang), "ask": [c["name"] for c in res.get("ask", [])]}
            return {**self.board(n, lang), "deleted": address}
        relinked = []
        with self._saving:
            edits, info = self._board_read(n)
            i = info[address]
            changes = [(address, SHOW, [0] * len(i["game_shows"] or [0] * DATES))]
            i["shows"] = [0] * DATES
            up = i["parent"] if i["parent"] in info and self._board_shown(info[i["parent"]]) else None
            for child, ci in info.items():
                if ci["parent"] != address or not self._board_shown(ci):
                    continue
                if up is not None:
                    changes.append((child, UPGRADE, Link(up)))
                    changes += self._board_flag(child, ci, info[up]["factory"] == ci["factory"])
                    ci["parent"] = up
                    changes += self._board_dates(child, ci, info[up])
                else:
                    changes += self._board_unlink(child, ci)
                relinked.append(child)
            self._board_apply(edits, changes)
            ix = self._open()
            try:
                names = self._names(ix, relinked, lang, edits.new_units) if relinked else {}
            finally:
                ix.close()
        return {**self.board(n, lang), "relinked": [names.get(a, a) for a in relinked]}

    def research_reset_all(self) -> dict:
        """A new mod's "Keep the game's research" (and "Custom", which starts from it) after "No research" was chosen:
        the game's own units researched as in the game again (the mod's research changes on them taken out), except
        where the unit they're researched from is in no build menu now (a nation started empty: the game stops on a
        shown unit researched from a hidden one, so those stay buildable from the start). The mod's new units keep
        theirs. Returns {"reset": how many units}."""
        from .api import UPGRADE, UPGRADE_FLAG
        with self._saving:
            edits, info = self._board_read()
            ix = self._open()
            try:
                game_links = ix.links(UPGRADE)
            finally:
                ix.close()
            back = set()
            for a, i in info.items():
                p = game_links.get(a)
                if i["new"] or p is None or (p in info and not self._board_shown(info[p])):
                    continue
                if any(edits.key(a, prop) in edits.edits for prop in (UPGRADE, UPGRADE_FLAG)):
                    back.add(a)
            self._board_apply(edits, [(a, prop, None) for a in sorted(back) for prop in (UPGRADE, UPGRADE_FLAG)])
        return {"reset": len(back)}

    def research_clear_all(self) -> dict:
        """The new mod's "No research": every unit of every nation buildable from the start (its research link and
        upgrade flag taken out; its research price and time stay, unused). Returns {"cleared": how many}."""
        with self._saving:
            edits, info = self._board_read()
            changes = []
            for a, i in info.items():
                if i["parent"] is not None:
                    changes += self._board_unlink(a, i)
            self._board_apply(edits, changes)
        return {"cleared": len(changes) // 2}
