"""A mission's three steps from LittleGroove's mission editor (his menu_entry_tab, load_files_tab and text_tab, the
owner's ask of 2026-10-07: "every feature he has"), on his engine's own code (ruse_mod_engine.scenario_registry,
scenario_chain, edits), so they say what his say:

- **In the menus** (his Menu Entry): whether the game lists the mission at all, which menu, where in it, and the
  values of its menu entry. Changing them goes through the All values tab (the entry is an object of the unit data
  reached from a named object), which saves them in the mod. Moving it up or down within its group (his Move up and
  Move down) is a mod's menus.toml (rusemod.menuorder): menu() shows a mod's order, move() works out the next one.
- **Files check** (his Load & Files): the chain that takes that menu entry to a playable mission, link by link, each
  fine, missing or not matching, with why (`why`: a code the Studio's words say in every language). Read only.
- **Texts** (his Text): every text the mission owns, its menu entry's and its mission script's, each a game text key
  the words panel changes in every language at once.

Everything here reads; nothing writes (the Studio saves). The packs come from the game folder, or from a built copy over it (`over`:
the folder the map check builds into), so a mod's own missions are checked as the game would get them.
"""
from __future__ import annotations

import re
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from .edat import Edat

# his names for the packs (ruse_mod_engine.mod_project.DAT_FILES)
DAT_FILES = {"gameplay": "ZZ_GladPatchableWin.dat", "scripts": "IA_Common.dat", "loc": "ZZ_Win.dat",
             "gameplay_np": "ZZ_GladNotPatchableWin.dat", "maps": "DataMap_Win.dat", "common": "Data_Common.dat"}
KINDS = ("operation", "campaign", "mp")  # his kinds of menu entry (mp: the BATTLES menu's maps)
# the values of a menu entry worth showing, by kind (his scenario_registry._DETAIL_PROPS, the rest in All values)
SHOWN = {"mp": ("NbPlayers", "GameType", "MapSize", "GameModeMulti"),
         "campaign": ("ChapterId", "CategoryId", "NbSecondaryObjectives", "PopCapPlayer", "PopCapIA"),
         "operation": ("CategoryId", "NbPlayers", "PopCapPlayer", "PopCapIA", "PrivilegeId")}
TEXT_PROPS = ("Description", "LongDescription", "LongDescription1", "LongDescription2", "LongDescription3",
              "LongDescription4")


class PackStore:
    """The game's packs (or a built copy's, over them) as the store his engine reads: entry_paths, get_raw, get_ndf
    and read_many by his names for the packs, and `view(name)` for his registry's list()/get() readers."""

    def __init__(self, game: Path, over: Path | None = None):
        self.game, self.over = Path(game), Path(over) if over else None
        self._stack = ExitStack()
        self._arcs: dict = {}
        self._ndfs: dict = {}
        self.bound = None  # his registry's bindings, read once (bindings())

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def close(self) -> None:
        self._stack.close()
        self._arcs.clear()
        self._ndfs.clear()

    def _arc(self, dat_key: str) -> Edat | None:
        if dat_key not in self._arcs:
            from .build import find_pack
            name = DAT_FILES.get(dat_key)
            path = None
            if name and self.over is not None:
                path = next((p for p in self.over.rglob("*") if p.name.lower() == name.lower()), None)
            if path is None and name:
                path = find_pack(self.game, name)
            self._arcs[dat_key] = self._stack.enter_context(Edat.open(str(path))) if path else None
        return self._arcs[dat_key]

    def entry_paths(self, dat_key: str, suffix: str = "") -> list[str]:
        arc = self._arc(dat_key)
        s = suffix.lower()
        return [e.path for e in arc.entries if not s or e.path.lower().endswith(s)] if arc is not None else []

    def get_raw(self, dat_key: str, path: str) -> bytes | None:
        arc = self._arc(dat_key)
        e = arc.entry(path) if arc is not None else None
        return bytes(arc.read(e)) if e is not None else None

    def read_many(self, dat_key: str, paths) -> dict:
        out = {}
        for p in paths:
            raw = self.get_raw(dat_key, p)
            if raw is not None:
                out[p] = raw
        return out

    def get_ndf(self, dat_key: str, path: str):
        key = (dat_key, path.replace("/", "\\").lower())
        if key not in self._ndfs:
            from ruse_mod_engine import ndfbin
            raw = self.get_raw(dat_key, path)
            self._ndfs[key] = ndfbin.read(raw) if raw else None
        return self._ndfs[key]

    def view(self, dat_key: str):
        store = self

        class _View:  # his edata reader's two calls
            def list(self):
                return store.entry_paths(dat_key)

            def get(self, path):
                raw = store.get_raw(dat_key, path)
                if raw is None:
                    raise KeyError(path)
                return raw
        return _View()


@dataclass
class Mission:
    """One scenario file of a map, as his registry binds it: its kind ("operation", "campaign", "mp" or
    "unbound"), its menu entry (`info_idx`: the object's place in the menus' data file) and its pack."""
    map_dir: str
    file: str            # its .scenario file's stem (leveldesign...)
    kind: str
    info_idx: int | None
    pack_idx: int | None
    tracking: str | None


def bindings(store: PackStore) -> dict:
    """{map folder: its scenarios' bindings} (his scenario_registry.build_bindings), read once per store."""
    if store.bound is None:
        from ruse_mod_engine import scenario_registry as SR
        m_ndf, g_ndf = SR.open_registry(store.view("gameplay"))
        store.bound = SR.build_bindings(m_ndf, g_ndf, store.view("maps"), gd=store.view("gameplay"),
                                        ia=store.view("scripts"))
    return store.bound


def missions(store: PackStore, map_dir: str) -> list[Mission]:
    """The map's scenario files and the menu entries that list them (his scenario_registry.build_bindings), the map
    found by its folder's name in any case (the Studio's pack name)."""
    bound = next((v for k, v in bindings(store).items() if k.lower() == map_dir.lower()), [])
    return [Mission(b.map_dir, b.scenario_name or "", b.kind, b.info_idx, b.pack_idx, b.tracking_id)
            for b in bound if b.has_file]


def find(store: PackStore, map_dir: str, file: str) -> Mission | None:
    stem = re.sub(r"\.scenario$", "", file, flags=re.I).lower()
    return next((m for m in missions(store, map_dir) if m.file.lower() == stem), None)


# --- Files check: the chain, link by link ---
def _why(n) -> str:
    """The node's state as a code the Studio words (mission_why_<code>): its kind and how it stands."""
    from ruse_mod_engine import scenario_chain as chain
    if n.optional:
        return "optional"
    state = {chain.OK: "ok", chain.MISSING: "missing", chain.MISMATCH: "mismatch"}.get(n.status, "unknown")
    if n.kind == "mapload" and n.status == chain.MISSING and "GUID" in (n.reason or ""):
        return "mapload_no_id"
    if n.kind == "dico" and n.status == chain.MISSING:
        return "dico_missing"
    return f"{n.kind.replace('-', '_')}_{state}"


# Links a battle map does without: of the game's 30 battle maps, 29 have no mission script and none has its own mission
# texts, and they play (swept 2026-10-08, every shipped scenario: Operations and campaign chapters have no broken link)
BATTLES_WITHOUT = ("script", "dico")


def chain(store: PackStore, map_dir: str, file: str, kind: str = "") -> dict:
    """The chain for one scenario (his scenario_chain.walk): {"links": [{kind, why, state, depth, detail}], "broken":
    how many links are missing or don't match}. Absences the game's own missions have too don't count: his optional
    ones, and for a battle map (`kind` "mp") a mission script and texts of its own (BATTLES_WITHOUT)."""
    from ruse_mod_engine import scenario_chain as chain_mod
    stem = re.sub(r"\.scenario$", "", file, flags=re.I)
    root = chain_mod.walk(store, map_dir, stem)
    if kind == "mp":
        for n in root.walk():
            if n.kind in BATTLES_WITHOUT and n.status != chain_mod.OK:
                n.optional = True
    links = []

    def add(n, depth):
        if depth:  # (the root is the scenario itself)
            state = "optional" if n.optional else {chain_mod.OK: "ok", chain_mod.MISSING: "missing",
                                                   chain_mod.MISMATCH: "mismatch"}.get(n.status, "unknown")
            links.append({"kind": n.kind, "why": _why(n), "state": state, "depth": depth - 1,
                          "detail": n.detail or ""})
        for c in n.children:
            add(c, depth + 1)
    add(root, 0)
    return {"links": links, "broken": len(root.problems())}


# --- In the menus ---
MENU_OF = {"operation": "operation", "campaign": "campaign", "mp": "battles"}  # his kinds -> menus.toml's menus


def menu(store: PackStore, mission: Mission, orders=()) -> dict | None:
    """Where the game's menus list a mission: {"kind", "listed" (in a menu at all), "order": [{"info", "tracking",
    "title_key", "this", "mission" (as menus.toml names it, None when no scenario file), "pack" (the menu pack whose
    list it's in), "group" (its CategoryId), "players"}] (that menu, in the order the player sees it), "values":
    {name: value} (SHOWN), "info" (the entry's place in the menus' data file, for the All values tab)}; None when no
    menu entry lists it. `orders`: a mod's menuorder.Order list, put in as the build would."""
    if mission.kind not in KINDS or mission.info_idx is None:
        return None
    from ruse_mod_engine import scenario_chain as chain_mod
    from ruse_mod_engine import scenario_registry as SR
    from . import menuorder
    g = store.get_ndf("gameplay", chain_mod.GLOBALS_PATH)
    names = {b.info_idx: menuorder.mission(b.map_dir, b.scenario_name + ".scenario")
             for bs in bindings(store).values() for b in bs
             if b.kind == mission.kind and b.has_file and b.info_idx is not None}
    full = SR.full_menu_order(g, mission.kind)
    packs, ids = dict(full), [i for i, _p in full]
    menu_name = MENU_OF[mission.kind]
    by_key = {menuorder.key(menu_name, n): i for i, n in names.items()}
    for o in orders:
        if o.menu == menu_name:
            ids = menuorder.arrange(ids, [by_key[k] for k in (menuorder.key(o.menu, x) for x in o.missions)
                                          if k in by_key])
    order = []
    for info_idx in ids:
        inst = g.instances[info_idx]
        players = SR._get_prop(g, inst, "NbPlayers")
        order.append({"info": info_idx, "tracking": SR._str_prop(g, inst, "TrackingId"),
                      "title_key": _key(g, inst, "Description"), "this": info_idx == mission.info_idx,
                      "mission": names.get(info_idx), "pack": packs[info_idx],
                      "group": SR._group_key(g, info_idx, SR.group_prop_for(mission.kind)),
                      "players": SR.ndf_val(g, players) if players is not None else None})
    inst = g.instances[mission.info_idx]
    values = {}
    for name in SHOWN[mission.kind]:
        v = SR._get_prop(g, inst, name)
        if v is not None:
            values[name] = SR.ndf_val(g, v)
    return {"kind": mission.kind, "listed": mission.pack_idx is not None and any(o["this"] for o in order),
            "order": order, "values": values, "info": mission.info_idx,
            "texts": {p: _key(g, inst, p) for p in TEXT_PROPS if _key(g, inst, p)}}


def run(order: list[dict]) -> tuple[int, int]:
    """[start, end) of the mission's group in `order` (menu()'s): the entries side by side with it in its pack's list
    with its group, the ones it can move among (his scenario_registry.move_within_group)."""
    at = next(i for i, o in enumerate(order) if o["this"])

    def same(o):
        return o["pack"] == order[at]["pack"] and o["group"] == order[at]["group"]
    s, e = at, at + 1
    while s > 0 and same(order[s - 1]):
        s -= 1
    while e < len(order) and same(order[e]):
        e += 1
    return s, e


def move(order: list[dict], delta: int) -> list[str]:
    """The missions of its group (run()) in their order once it has moved `delta` places (-1 up, 1 down), as
    menus.toml names them. ValueError "top" or "bottom" at its group's edge, "unnamed" when one of the group has no
    scenario file (a mod can't name it)."""
    at = next(i for i, o in enumerate(order) if o["this"])
    s, e = run(order)
    to = at + delta
    if to < s:
        raise ValueError("top")
    if to >= e:
        raise ValueError("bottom")
    names = [o["mission"] for o in order[s:e]]
    if None in names:
        raise ValueError("unnamed")
    names[at - s], names[to - s] = names[to - s], names[at - s]
    return names


def _key(g, inst, prop: str) -> str | None:
    """A text value's game text key, as the Studio's index spells it (0x and the 16 hex digits, high first)."""
    from ruse_mod_engine import scenario_registry as SR
    from ruse_mod_engine.ndfbin import T
    v = SR._get_prop(g, inst, prop)
    if v is None or v.type_id != T.LocHash:
        return None
    return "0x" + bytes(v.raw)[::-1].hex().upper()


# --- Texts ---
def texts(store: PackStore, mission: Mission, script_text: str = "") -> list[dict]:
    """Every text the mission owns (his edits.scenario_text_inventory): its menu entry's texts first, then its
    mission script's, in the order they come: [{"key", "where": "menu"|"script", "prop" (a menu text's value name),
    "line" (a script text's line)}]. `script_text`: the mission script as text (rusemod.mapscripts.text)."""
    from ruse_mod_engine import edits
    from ruse_mod_engine import scenario_chain as chain_mod
    reg_ndf = reg_inst = None
    if mission.info_idx is not None:
        reg_ndf = store.get_ndf("gameplay", chain_mod.GLOBALS_PATH)
        reg_inst = reg_ndf.instances[mission.info_idx]
    idx = edits.loc_index(store)
    out = []
    for e in edits.scenario_text_inventory(idx, reg_ndf=reg_ndf, reg_inst=reg_inst, script_source=script_text):
        key = "0x" + bytes(e.key)[::-1].hex().upper()
        for u in e.where:
            if u.source == "menu entry":
                out.append({"key": key, "where": "menu", "prop": u.detail, "line": None})
            else:
                line = re.match(r"line (\d+)", u.where or "")
                out.append({"key": key, "where": "script", "prop": None,
                            "line": int(line.group(1)) if line else None})
        if not e.where:
            out.append({"key": key, "where": "script", "prop": None, "line": None})
    return out


def script_of(store: PackStore, map_dir: str, file: str) -> bytes | None:
    """The mission script the chain finds for the scenario (the one the game runs), or None."""
    from ruse_mod_engine import scenario_chain as chain_mod
    stem = re.sub(r"\.scenario$", "", file, flags=re.I)
    root = chain_mod.walk(store, map_dir, stem)
    hit = next((n for n in root.walk() if n.kind == "script" and n.status == chain_mod.OK), None)
    return store.get_raw("scripts", hit.ref) if hit is not None else None
