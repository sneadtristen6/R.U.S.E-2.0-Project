"""Buildings with units of their own (the owner, 2026-10-18: "Adding a new building and giving units to it"; three, the
most there's room for: "buildings 3 limit").

What makes one, as tested in the game (buildings1, runs 2 and 3, 2026-10-18: all worked):
- a building whose kind (TypeBatiment) is one no game building has, 6, 4 or 7, and whose build menu (Menu) is that
  kind's own, 8, 9 or 10: the units whose Factory is that kind are made in it, by every nation that has one;
- a tab of its own on the build bar: an entry in the bar's list (InterfaceInGameResourceMainMenuInfos, a copy of the
  Prototypes tab's entry), and in the game's scripts the tab's builder (headup/menu_builder), its place on the bar
  (parametres/ParamsMainMenu) and a production queue for the kind (base/camp); the build writes all of them from the
  fixed templates below, filled in with which of the three the mods have;
- kinds 4 and 7 and menus 9 and 10 only with the game patch "more-buildings" (rusemod.gamepatch), which the build
  applies to the modded copy.
A click on a building opens the first tab of its build menu, so each kind has a menu of its own (run 2: three buildings
in menu 8 all opened the first one's tab).
"""
from __future__ import annotations

import base64
import hashlib

from . import pyscript

# (tab key, building kind, build menu, the kind's name and the menu's name in the game's scripts, place on the bar)
SLOTS = (
    ("R2Own1", 6, 8, "DalleBatimentDepot", "menu_all", 12),
    ("R2Own2", 4, 9, "R2Factory4", "R2Menu9", 13),
    ("R2Own3", 7, 10, "R2Factory7", "R2Menu10", 14),
)
KINDS = tuple(s[1] for s in SLOTS)              # 6, 4, 7: the order a nation's own-units buildings take them in
MENU_OF = {s[1]: s[2] for s in SLOTS}           # kind -> its build menu
KEY_OF = {s[1]: s[0] for s in SLOTS}            # kind -> its tab's key
PATCHED = {4, 7}                                 # the kinds that need the game patch
PATCH = "more-buildings"
MOST = len(SLOTS)
TABS_OBJECT = "$/GFX/Everything/InterfaceInGameResourceMainMenuInfos"
TABS_PROP = "MainMenuInfosDico"
COPIED_TAB = "Experiments"                       # the Prototypes tab: each new tab is a copy of its entry
TAB_PREFIX = "MainMenuInfos_R2_"

# The templates, Python 2.5 as the game runs it, each run after the game's own module (pyscript.append_module). The
# build fills in `_r2_own`: the keys of the tabs the mods have. Compiled with the game's Python (ownbuildings_compiled).
SOURCES = {
    "menu_builder": '''\
# the build bar's tabs of a mod's buildings with units of their own (the RUSE Studio's build): each lists only its
# buildings (its kind, in its build menu), the units of its kind and their research, the way the game's unit tabs do
class R2OwnUnitsMenu(MenuBuilderUnit):
    def do_build(self, menu, hud_instance, is_update):
        techno_manager = hud_instance.camp.technologie_manager
        for batiment_descriptor in techno_manager.GetBatiments():
            if batiment_descriptor.Menu is self.menu_type and batiment_descriptor.TypeBatiment == self.type_batiment:
                menu.add_bouton_construction_building(batiment_descriptor, hud_instance, is_dev=False,
                                                      is_ennemi=False)
        for unit_descriptor in techno_manager.GetAllUnitsByFactoryType(self.type_batiment):
            menu.add_bouton_construction_unit(unit_descriptor, hud_instance, techno_manager)
        for techno in techno_manager.Technos():
            if techno.GetDescriptor().Factory == self.type_batiment:
                menu.add_bouton_techno(techno, hud_instance, techno_manager)


_r2_own = ('R2Own1', 'R2Own2', 'R2Own3')
for _r2_key, _r2_kind, _r2_menu in (('R2Own1', 'DalleBatimentDepot', 'menu_all'),
                                    ('R2Own2', 'R2Factory4', 'R2Menu9'),
                                    ('R2Own3', 'R2Factory7', 'R2Menu10')):
    if _r2_key in _r2_own:
        Hud._original_menu_builders.append(R2OwnUnitsMenu(
            _r2_key, getattr(_enum_for_game_play.BatimentEnum, _r2_kind),
            getattr(_enum_for_game_play.BatimentTypeMenu, _r2_menu)))
''',
    "paramsmainmenu": '''\
# the build bar's places of a mod's buildings with units of their own (the RUSE Studio's build), after the game's own
# tabs, in every game mode, each paired with its tab by name
_r2_own = ('R2Own1', 'R2Own2', 'R2Own3')
if 'R2Own1' in _r2_own:
    Param_MainMenu_R2Own1 = MainMenuDescriptor(name=u'R2Own1', position_in_menu=12, is_dev=False,
                                               is_in_normal_mode=True, is_in_nuclear_mode=True,
                                               factory=_enum_for_game_play.BatimentEnum.DalleBatimentDepot,
                                               type_id=_enum_for_game_play.TypeMenu.CommonUnits)
if 'R2Own2' in _r2_own:
    Param_MainMenu_R2Own2 = MainMenuDescriptor(name=u'R2Own2', position_in_menu=13, is_dev=False,
                                               is_in_normal_mode=True, is_in_nuclear_mode=True,
                                               factory=_enum_for_game_play.BatimentEnum.R2Factory4,
                                               type_id=_enum_for_game_play.TypeMenu.CommonUnits)
if 'R2Own3' in _r2_own:
    Param_MainMenu_R2Own3 = MainMenuDescriptor(name=u'R2Own3', position_in_menu=14, is_dev=False,
                                               is_in_normal_mode=True, is_in_nuclear_mode=True,
                                               factory=_enum_for_game_play.BatimentEnum.R2Factory7,
                                               type_id=_enum_for_game_play.TypeMenu.CommonUnits)
''',
    "camp": '''\
# a production queue for each kind of a mod's buildings with units of their own (the RUSE Studio's build): the game's
# camp.init makes them for its own kinds only
_r2_own = ('R2Own1', 'R2Own2', 'R2Own3')


def _r2_own_virtual_factories(self):
    if self.neutre:
        return
    kinds = _enum_for_game_play.BatimentEnum
    for key, kind in (('R2Own1', 'DalleBatimentDepot'), ('R2Own2', 'R2Factory4'), ('R2Own3', 'R2Factory7')):
        if key in _r2_own:
            factory = _virtual_factory.TVirtualFactory(self, getattr(kinds, kind))
            self._list_factory_ref.append(factory)
            self.AddVirtualFactory(getattr(kinds, kind), factory)


_r2_camp_init = camp.init


def _r2_camp_init_with_own(self, *args, **kwargs):
    # the game calls camp.init(self, nom, neutre), neutre by keyword: everything goes to the game's init as it came
    result = _r2_camp_init(self, *args, **kwargs)
    _r2_own_virtual_factories(self)
    return result


camp.init = _r2_camp_init_with_own
''',
}
# where each template goes: (the script pack in ZZ_Win.dat, the game's module in it)
SCRIPTS = {
    "menu_builder": ("genpython\\eugen.ipk", "genpython\\1000\\codeia\\python\\eugen\\headup\\menu_builder.xyz"),
    "paramsmainmenu": ("genpython\\eugenpatchable.ipk",
                       "genpython\\1000\\codeia\\python\\eugenpatchable\\parametres\\paramsmainmenu.xyz"),
    "camp": ("genpython\\eugen.ipk", "genpython\\1000\\codeia\\python\\eugen\\base\\camp.xyz"),
}


class OwnBuildingsError(ValueError):
    pass


def source_sha(name: str) -> str:
    return hashlib.sha256(SOURCES[name].encode("utf-8")).hexdigest()


def template(name: str) -> pyscript.Code:
    """A template, compiled: refused when the compiled one isn't of the source above (ownbuildings_compiled)."""
    from .ownbuildings_compiled import COMPILED
    entry = COMPILED.get(name)
    if entry is None or entry["source_sha256"] != source_sha(name):
        raise OwnBuildingsError(f"the compiled {name} template isn't the one of its source: compile it again")
    code = pyscript.load(base64.b64decode(entry["marshal"]))
    if not isinstance(code, pyscript.Code):
        raise OwnBuildingsError(f"the compiled {name} template isn't a module")
    return code


def keys_for(kinds) -> tuple:
    """The tab keys of the kinds `kinds` (any of 6, 4, 7), in the slots' order."""
    return tuple(s[0] for s in SLOTS if s[1] in set(kinds))


def script_changes(zz_win, kinds) -> dict:
    """{script pack's path in ZZ_Win.dat: (the pack, as an Edat; {module path: the new .xyz})} for the mods' own-units
    kinds `kinds`: each of the game's three modules with its template run after it."""
    from .edat import Edat
    keys = tuple(k.encode("latin-1") for k in keys_for(kinds))
    if not keys:
        return {}
    packs: dict = {}
    for name, (pack_path, member_path) in SCRIPTS.items():
        entry = zz_win.entry(pack_path)
        if entry is None:
            raise OwnBuildingsError(f"ZZ_Win.dat has no {pack_path}")
        if pack_path not in packs:
            packs[pack_path] = (entry, Edat(bytes(zz_win.read(entry))), {})
        _e, pack, out = packs[pack_path]
        member = pack.entry(member_path)
        if member is None:
            raise OwnBuildingsError(f"{pack_path} has no {member_path}")
        xyz = pyscript.read_xyz(bytes(pack.read(member)))
        code = pyscript.with_value(template(name), b"_r2_own", keys)
        joined = pyscript.append_module(xyz.payload, code)
        out[member.path] = pyscript.write_xyz(pyscript.Xyz(xyz.source_md5, joined))
    return {entry.path: (pack, changed) for entry, pack, changed in packs.values()}


def tabs_rndf(tabs: list[tuple[int, str | None]], game_keys: list[str]) -> str:
    """The build bar's entries for the kinds in `tabs` [(kind, the loc key of its title, or None: the copied tab's)]:
    each a copy of the Prototypes tab's entry with its own place, title and kind, no shortcut key; and the bar's list
    set to the game's entries (`game_keys`, the list's keys in its order) followed by the new ones."""
    copied = game_keys.index(COPIED_TAB)
    out = ["// the build bar's tabs of the buildings with units of their own (rusemod.ownbuildings)\n"]
    keys = []
    for kind, title in tabs:
        key, _k, _m, _kn, _mn, place = next(s for s in SLOTS if s[1] == kind)
        name = TAB_PREFIX + key
        out.append(f"export {name} is clone {TABS_OBJECT}:{TABS_PROP}[{copied}].v\n(\n    PositionInMenu = {place}\n"
                   + (f"    TitleToken = loc('{title}')\n    TitleToken2 = loc('{title}')\n" if title else "")
                   + f"    Factory = {kind}\n)\npatch ~/{name} ( delete IdForShortcut )\n")
        keys.append((key, name))
    entries = [f"        ('{k}', {TABS_OBJECT}:{TABS_PROP}[{i}].v)" for i, k in enumerate(game_keys)]
    entries += [f"        ('{key}', ~/{name})" for key, name in keys]
    out.append(f"patch {TABS_OBJECT}\n(\n    {TABS_PROP} = MAP [\n" + ",\n".join(entries) + "\n    ]\n)\n")
    return "".join(out)
