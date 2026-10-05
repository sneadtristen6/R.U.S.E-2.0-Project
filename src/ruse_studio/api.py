"""What the Studio's screens can ask for. Plain JSON-friendly data in and out; every answer about the game comes from
the game index, opened read-only for each question (the window calls from several threads).

Editing: the modder works in one mod at a time (made here, in the platform folder's `mods/`, or any mod folder they
open). Every change is saved at once in that mod's `src/studio.rndf` (edits.py). New units are copies of a unit the
game has, kept in the same file with their names in `text/studio.baseunite.csv`; the game index doesn't know them,
so their pages are the copied unit's pages, with the copy's own changes on top. Test in game builds the mod into its
own modded copy and starts the game, with the platform's engine (rusemod.play), so the Studio doesn't need the
launcher. Settings has the clean game backup, as the launcher does (rusemod.backup.BackupCalls): the only way the
Studio writes into the game's own folder, and only when the modder asks for a restore.
"""
from __future__ import annotations

import base64
import hashlib
import functools
import html
import json
import math
import re
import shutil
import sqlite3
import struct
import zlib
import threading
import tomllib
import unicodedata
from dataclasses import asdict, replace
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from rusemod import doctor, identity, missions, mod_index, package, scenario, scenery, schema, startlog
from rusemod.backup import BackupCalls
from rusemod.brush import BrushError, parse_strokes, strokes_toml
from rusemod.community import APP_NAMES, CommunityCalls, private_paths_out
from rusemod.update import UpdateCalls
from rusemod.build import MAP_FILES, BuildError, build_and_write, build_cache, load_mod
from rusemod.lock import fingerprint_text
from rusemod.home import PrefsCalls, default_home, game_dir as find_game_dir
from rusemod.index import FORMAT as INDEX_FORMAT, LIST_VALUES, WHOLE_LISTS, Index, build_index, default_path
from rusemod.patch import INT_RANGES
from rusemod.play import SHARED, Starter, instances_dir
from rusemod.rndf import RndfError
from rusemod.steam import build_of, data_revisions, find_game
from rusemod.uilang import LanguageCalls
from rusemod.build import find_pack
from rusemod.edat import Edat
from rusemod.modcheck import check_mod_folder
from rusemod.roadnet import RoadNetError
from rusemod.terrain import LODS, ground_png, map_list, pack_file, terrain
from rusemod.webui import Job, job_view, pick_file, pick_folder, pick_save

from .edits import EditsFileError, Link, ModEdits, NewUnit, plain_name
from . import __version__

KINDS = {"ground": ("TUniteAuSolDescriptor",), "infantry": ("TInfanterieDescriptor",),
         "air": ("TAvionDescriptor",), "buildings": ("TBatimentDescriptor",)}
KIND_OF = {cls: kind for kind, classes in KINDS.items() for cls in classes}
AMMO = "TAmmunition"  # a weapon's shots (damage, range, rate of fire): listed as the "ammo" kind, and copied for a
WEAPON = "TMountedWeaponDescriptor"  # weapon of its own; a weapon on a unit fires one ammo (its Ammunition)
SHOT_TAG = "weapon_effet_tag"  # a weapon's EffectTag names the part of the unit's model it fires from (_shots)
RANGE = "PorteeMaximale"  # a weapon's range: a value of the ammo it fires (set_range)
RANGE_COPY = "Ammo_Range_"  # the start of the name of an ammo copy set_range makes for one weapon
FLAG_LISTS = set(WHOLE_LISTS)  # lists edited as a set of flags, any length (a unit's InitialFlagSet)
NOT_EDITABLE = {"DescriptorId", "TrackingId", "AmmunitionId", "Nationalite"}  # ids stay unique (rusemod.identity);
# moving a unit to another nation needs more than one number (its menus, and the new nation's add-on for China), so it
# comes later
ALL_CLASSES = tuple(KIND_OF)
# What a unit or building is for (the unit list's and the Spawn tool's second sort, after the kind). Buildings by their
# code name, first match wins (a decoy HQ is a decoy): Leurre is French for decoy. Units by the factory that builds them
# (its menu number); 3 is the construction menu, where the forts' guns sit.
BUILDING_GROUPS = (("fake", ("Leurre", "Fake")), ("hq", ("Headquarter",)),
                   ("money", ("BatimentAdministratif", "Depot")),
                   ("fort", ("Defense", "Def_", "ArtillerieField", "PosteAlerte")))
FACTORY_GROUPS = {8: "barracks", 10: "armor", 11: "antitank", 13: "artillery", 12: "prototype", 9: "airfield",
                  3: "turret"}
GROUPS = ("hq", "money", "factory", "fort", "fake", *FACTORY_GROUPS.values(), "other")  # the order lists show them in
# Ammunition by what it is: its kind's English name in the game's texts (TypeName), the same in every language.
AMMO_GROUPS = {"ap": ("AP shell",), "he": ("HE shell", "Assault gun", "Mortar", "Navy gun", "Nuclear gun"),
               "aa": ("AA gun",), "mg": ("Machine-gun", "Machine-guns", "MG turrets", "Fixed MG"),
               "infantry_weapons": ("Infantry weapon", "Handguns", "Grenades", "Flamethrower", "Satchel charge"),
               "antitank_weapons": ("Bazooka", "PIAT", "Panzerfaust", "Panzerschreck", "Panzerknacker"),
               "bombs": ("Carpet bombing", "Diving bomb", "HE bomb"), "rockets": ("Rocket", "Rockets", "V2")}
AMMO_GROUP_OF = {text: g for g, texts in AMMO_GROUPS.items() for text in texts}
AMMO_GROUP_ORDER = (*AMMO_GROUPS, "other")


# Each building's map icon, by the game's own descriptor name (Descriptor_Building_VehiculeFactory is the Armor Base,
# Usine_Canon the Artillery & AA Base, UsineAutomoteur the Anti-Tank Base...); the first match wins, so the bunkers'
# longer names come first. The owner, 2026-10-03: an HQ clearly an HQ, a depot a truck, an armor base and an airfield
# different, and "the bunkers need to have a difference between the bunkers".
BUILDING_ICONS = (
    ("hq2", ("TruckFactory",)), ("hq", ("Headquarter",)), ("depot", ("BatimentDepot",)), ("admin", ("BatimentAdministratif",)),
    ("airfield", ("Aeroport",)), ("barracks", ("Caserne",)), ("armor_base", ("VehiculeFactory",)),
    ("at_base", ("UsineAutomoteur",)), ("art_base", ("Usine_Canon",)), ("proto_base", ("ExperimentalFactory",)),
    ("atomic", ("Usine_Atomique",)),
    ("bunker_at", ("MGATNest", "DefenseAT")), ("bunker_mg", ("MGNest", "Bunker_enterre")),
    ("bunker_aa", ("DefenseDCA", "Position_DCA")), ("bunker_art", ("Artillerie", "Position_105mm")),
    ("bunker_fort", ("Maginot", "Siegfried", "DefenseLegere")), ("bunker_op", ("PosteAlerte",)),
)
UNIT_ICONS = {"armor": "tank", "antitank": "at_gun", "artillery": "howitzer", "airfield": "plane", "barracks": "truck",
              "prototype": "tank", "turret": "bunker_mg"}  # a ground unit by what builds it (infantry: a soldier)


def icon_of(kind: str, address: str, group: str) -> tuple[str, bool]:
    """(the map icon for a unit or building, whether it's a decoy): see BUILDING_ICONS and UNIT_ICONS."""
    name = _tail(address)
    if kind == "buildings":
        decoy = "Leurre" in name or name.endswith("Fake")
        return next((icon for icon, parts in BUILDING_ICONS if any(p in name for p in parts)), "building"), decoy
    if kind == "infantry":
        return "soldier", False
    if kind == "air":
        return "plane", False
    if group == "artillery" and any(p in name for p in ("DCA", "Flak", "Bofors", "Quad")):
        return "aa_gun", False
    return UNIT_ICONS.get(group, "unit"), False


# The unit list's subsections under Ground, Infantry and Air (owner, 2026-10-03: "heavy tank light tank medium tank
# heavy bomber medium bomber light bomber ... when it's a recon unit recon"): the game's own type of each unit, its
# TypeUnitHintToken's text. The list's type pick sends one as TYPE_PICK + its name.
UNIT_KINDS = ("ground", "infantry", "air")
TYPE_PICK = "type:"
# The order the types are offered in: each family together, light before medium before heavy, fighters before
# bombers (the game's type keys; a key not here comes after them, by name)
TYPE_ORDER = (
    "RECO_u", "RECO_ar", "TANK_l", "TANK_ladv", "TANK_m", "TANK_madv", "TANK_h", "TANK_hadv", "TANK_jadv", "FLAME",
    "TD", "TD_us", "TD_adv", "TD_adv_us", "AT", "AT_adv", "AAAT", "AA", "AA_m", "AA_ar", "ART_l", "ART_m", "ART_h",
    "ART_ar", "ART_har", "ASSAULT", "ASSAULT_h", "ROCKETV", "ROCKETLV", "ROCKETT", "NUKE_art", "NUKE_mis",
    "INF_l", "INF_r", "INF_h", "INF_e", "INF_sharp", "INF_sap",
    "AIR_f", "AIR_fadv", "AIR_j", "AIR_fb", "AIR_fbadv", "AIR_bl", "AIR_bm", "AIR_bh", "AIR_bj", "AIR_arec", "AIR_rec",
    "AIR_tr")
ARMOUR_TYPES = ("D_", "TB_")  # type keys whose text is how much a fort takes ("Fragile Position"), not what it is


def _type_order(kinds: dict) -> list[str]:
    """The type names there are ({name: its game type key, or None for a group's name}), in TYPE_ORDER."""
    rank = {key: n for n, key in enumerate(TYPE_ORDER)}
    return sorted(kinds, key=lambda t: (rank.get(kinds[t], len(TYPE_ORDER) + (kinds[t] is None)), t))


def group_of(kind: str, address: str, factory: int | None) -> str:
    """What a unit or building is for: one of GROUPS (a mod's new unit goes by the one it was copied from)."""
    if kind == "buildings":
        name = _tail(address)
        return next((g for g, parts in BUILDING_GROUPS if any(p in name for p in parts)), "factory")
    return FACTORY_GROUPS.get(factory, "other")
NATIONS = 7
DEPOT_SLAB = "DalleBatimentDepot"  # a map's supply depot spot, as the Spawn tool offers it (rusemod.scenario.DEPOT)
_PREFIX = re.compile(r"^(Descriptor_[A-Za-z]+_)")  # Descriptor_Unit_M4_Sherman -> a copy is Descriptor_Unit_<Name>
PACKAGE_FILES = ("RUSE mods (*.rusemod)",)  # the "save as" dialog's filter for Export mod…


def _tail(address: str) -> str:
    return address.rsplit("/", 1)[-1]


def _shifted_cam(cam: dict, dx: float, dy: float) -> dict:
    """A start's warm-up camera path moved by (dx, dy) on the map, its look directions as they were."""
    return {**cam, "path": [[x + dx, y + dy, z] for x, y, z in cam["path"]]}


def _turned_cam(cam: dict, x: float, y: float, angle: float) -> dict:
    """A start's warm-up camera path turned `angle` radians about (x, y), as the build turns it (CamPaths.turn)."""
    if not angle:
        return cam
    ca, sa = math.cos(angle), math.sin(angle)
    path = [[x + (px - x) * ca - (py - y) * sa, y + (px - x) * sa + (py - y) * ca, pz] for px, py, pz in cam["path"]]
    look = cam.get("look")
    if look:
        look = [look[0] * ca - look[1] * sa, look[0] * sa + look[1] * ca, look[2]]
    return {**cam, "path": path, "look": look}


def _shot_name(effect: str | None) -> str:
    """$/GFX/Everything/FX_Tir_ObusAP_Moyen -> ObusAP Moyen."""
    name = _tail(effect or "")
    return name[len("FX_Tir_"):].replace("_", " ") if name.startswith("FX_Tir_") else name.replace("_", " ")


def _short(num: float):
    """A number from the index as the modder should see it: 12, not 12.0; 0.1, not the float32's 0.100000001."""
    if isinstance(num, int) or num.is_integer():
        return int(num)
    try:
        if struct.unpack("<f", struct.pack("<f", num))[0] == num:
            for digits in range(6, 10):
                text = float(f"{num:.{digits}g}")
                if struct.unpack("<f", struct.pack("<f", text))[0] == num:
                    return text
    except OverflowError:
        pass
    return num


def _props(o: dict) -> dict[str, dict]:
    """One object's values from the index, per property: list or not, and its numbers (None for texts)."""
    props: dict[str, dict] = {}
    for path, num, text in o["values"]:
        prop = path.split("[", 1)[0]
        p = props.setdefault(prop, {"list": "[" in path, "numbers": [], "texts": [], "in_order": True})
        if p["list"] and path != f"{prop}[{len(p['numbers'])}]":
            p["in_order"] = False  # a list that also holds something else (a reference): not editable as numbers
        p["numbers"].append(None if num is None else _short(num))
        p["texts"].append(text)
    return props


def _can_edit(prop: str, p: dict) -> bool:
    return prop not in NOT_EDITABLE and p["in_order"] and all(n is not None for n in p["numbers"]) \
        and not (p["list"] and len(p["numbers"]) >= WHOLE_LISTS.get(prop, LIST_VALUES))  # the index keeps 16 items of
    # most lists: there may be more


def ammo_name(texts: dict, name_key, type_key) -> str | None:
    """What the game calls an ammunition: its kind, then its calibre ("AP shell · Medium cal."), from its two texts."""
    kind, calibre = texts.get(type_key), texts.get(name_key)
    return " · ".join(dict.fromkeys(t for t in (kind, calibre) if t)) or None


def _whole(value, kind: str, prop: str):
    """Round like the build does for whole-number properties (half away from zero), and check it fits."""
    r = int(Decimal(str(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    lo, hi = (0, 1) if kind == "bool" else INT_RANGES[kind]
    if not lo <= r <= hi:
        raise StudioError(f"{prop}: {r} doesn't fit (it must be {lo} to {hi})")
    return r


def safe_name(name: str) -> str:
    """The part of a new unit's address made from its name: ASCII letters, digits and _ only (accents dropped, other
    letters left out), which the game's data, its Python unit list and .rndf files all accept."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", plain).strip("_")


class StudioError(Exception):
    pass


# the ways a mod's map files can be wrong, as their readers say it
_FILE_MISTAKES = (tomllib.TOMLDecodeError, UnicodeDecodeError, BrushError, scenario.ScenarioError,
                  scenery.SceneryEditError, RoadNetError)


def _erase_dict(a) -> dict:
    """An erase area (rusemod.scenery.EraseArea) as the Maps view takes it."""
    out = {"x": a.x, "y": a.y, "radius": a.radius, "what": list(a.what), "types": list(a.types)}
    if a.shape != "round":  # the brush types: a square (its direction) or a line (its end)
        out.update(shape=a.shape, dx=a.dx, dy=a.dy, x2=a.x2, y2=a.y2)
    return out


def _save_checked(path: Path, text: str, read) -> None:
    """Save `text` into `path` only when `read(its TOML)` takes it: the Studio never writes a file that it, or the
    build, can't read back (Studio 0.7.0 once saved water strokes without their level)."""
    try:
        read(tomllib.loads(text))
    except _FILE_MISTAKES as exc:
        raise StudioError(f"The Studio would have saved {path.name}, which it can't read back ({exc}), so nothing "
                          f"was saved. Please report this.") from None
    ModEdits._write(path, text)


def _scenario_tables(data: dict, where: str) -> tuple[list, list, list, list]:
    """A scenario.toml's (moves, new starting points, spawns, removes), as the build reads them."""
    return (scenario.parse_moves(data.get("move", []), where), scenario.parse_starts(data.get("start", []), where),
            scenario.parse_spawns(data.get("spawn", []), where), scenario.parse_removes(data.get("remove", []), where))


def _scenario_sectors(data: dict, where: str):
    """A scenario.toml's [sectors] setting (rusemod.sectors.Sectors), or None."""
    from rusemod.sectors import parse_sectors
    found = parse_sectors(data.get("sectors"), where)
    return found[0] if found else None


def _scenario_checked(where: str):
    """The check a rewritten scenario.toml must pass (_save_checked): every table read back as the build reads it."""
    return lambda data: (_scenario_tables(data, where), _scenario_sectors(data, where))


def _scenario_toml(moves: list, starts: list, spawns: list, removes: list, header: str, sectors=None) -> str:
    """A scenario.toml holding all four kinds of edit and the sectors' setting (none is ever left out on a rewrite)."""
    return scenario.scenario_toml(moves, starts, spawns, removes, header, sectors)


_KEEP = object()  # (a rewrite keeps what the file has)


def _copied(view: dict, copy) -> dict:
    """A shipped map's scenarios as a new map of it has them (`copy`: (name, newmap.NewMap); None: the map itself):
    only the one its entry loads (the entry map.toml names: a BATTLES map, an Operation or a campaign chapter; else
    the BATTLES ones), listed under the new map's name, as the build makes it. The cached view stays the game's."""
    if copy is None:
        return view
    _name, spec = copy

    def copied(s):
        if spec.entry is not None:
            return [e for e in s["entries"] if e["name"] == spec.entry]
        return [e for e in s["entries"] if e["kind"] == "skirmish"]
    out = []
    for s in view["scenarios"]:
        found = copied(s)
        if not found:
            continue
        seats = re.match(r"^\(\d+\)", found[0]["name"])  # "(2) Blitz" -> "(2) Blitz at Dusk"
        out.append({**s, "kind": found[0]["kind"],
                    "entries": [{"name": f"{seats.group(0)} {spec.names['us']}" if seats else spec.names["us"],
                                 "kind": found[0]["kind"],
                                 "titles": {lang: spec.names.get(lang, spec.names["us"])
                                            for lang in (found[0]["titles"] or {"us": ""})}}]})
    return {**view, "scenarios": out}


def _pack_name(name: str, taken: set) -> str:
    """A new map's own name (its folder and files: a letter, then up to 39 letters, digits and _; rusemod.newmap
    check_name) from what the menus call it: "Blitz at dusk" -> BlitzAtDusk, accents dropped; NewMap when nothing is
    left (a name in Russian or Japanese). `taken` (lower case): names in use; a number is added until it's free."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[A-Za-z0-9]+", plain)
    base = "".join(w[:1].upper() + w[1:] for w in words)
    if not base or not base[0].isalpha():
        base = "NewMap" + base
    base = base[:36]
    out, n = base, 2
    while out.lower() in taken:
        out, n = f"{base}{n}", n + 1
    return out


def _aside(path: Path) -> Path:
    """Rename a mod file that can't be read to <name>.broken.toml (-2, -3... when taken): out of the build's way,
    never lost. Returns the new path."""
    kept, k = path.with_name(f"{path.stem}.broken.toml"), 2
    while kept.exists():
        kept, k = path.with_name(f"{path.stem}.broken-{k}.toml"), k + 1
    path.rename(kept)
    return kept


@functools.cache
def _words() -> dict:
    return tomllib.loads(Path(__file__).with_name("words.toml").read_text(encoding="utf-8"))


def words(lang: str = schema.BASE) -> dict:
    """The Studio's own words in `lang` (English for `base` and anything missing)."""
    return {key: texts.get(lang) or texts["us"] for key, texts in _words().items()}


class StudioApi(UpdateCalls, PrefsCalls, LanguageCalls, CommunityCalls, BackupCalls, startlog.StartCalls):
    UPDATE_APP, UPDATE_VERSION = "studio", __version__  # rusemod.update: the app looks for its newer releases
    PREFS_APP = "studio"  # rusemod.home: the language and keys, kept in settings.json

    def __init__(self, index_path=None, game_dir=None, find=find_game, home=None, starter=None, instances=None,
                 pick_save=None, backups=None):
        self._index_path = Path(index_path) if index_path else None
        self._game_dir = Path(game_dir) if game_dir else None
        self._find = find
        self._home = Path(home) if home else default_home()
        self._starter = starter or Starter()
        self._instances = Path(instances) if instances else None
        self._backups = Path(backups) if backups else None  # the clean game backup (rusemod.backup): RUSE-Backup
        # on the game's drive
        self._jobs: dict[str, Job] = {}
        self._units: list | None = None  # every unit and building, read once per index
        self._ammo: list | None = None   # every ammunition, the same
        self._window = None  # set by the window (a folder dialog for "Open a mod folder", "save as" for Export)
        self._pick_save = pick_save  # tests: a stand-in for the "save as" dialog (filename -> path or None)
        self._saving = threading.RLock()  # the window calls from several threads: one change to the file at a time,
        # and no reading it mid-change (Windows can't replace a file that's open)
        self._grounds: dict[tuple, dict] = {}  # the last maps shown in 3D, so switching back is instant
        self._grounds_lock = threading.Lock()
        self._ground_jobs: dict[str, str] = {}  # picture being made -> its job, so asking twice doesn't make it twice
        self._sceneries: dict[tuple, dict] = {}  # the last maps' scenery (map_scenery)
        self._scenario_owners: dict[tuple, list[dict]] = {}  # mission CampList owners, for the spawn picker
        self._descriptors: tuple = (None, {})    # (unit pack, its scenery types), read once per game build
        self._models_done: dict[str, dict] = {}  # map -> the index of its 3D models (map_models), once made
        self._check_jobs: dict[str, str] = {}  # map -> its "Check this map" job, so asking twice runs it once
        self._blenders: dict[str, object] = {}  # a unit's work folder -> the Blender opened on it (Bring back asks
        # it to save)
        self._previews_lock = threading.Lock()  # one unit model made for the preview at a time
        # the Erase tool's count (scenery_erased): one at a time, and a newer ask stops the one running, so painting
        # many circles never piles up counts (the owner's whole-map erase on M04_Cotentin, 2026-10-04: one count took
        # 161 s and 0.7 GB, and a count per stroke ran the Studio out of memory)
        self._erased_lock = threading.Lock()
        self._erased_ask = threading.Lock()
        self._erased_gen = 0

    # --- where things are ---
    def _game(self) -> Path | None:
        if self._game_dir:
            return self._game_dir
        return find_game_dir(self._home, self._find)[0]  # the same answer as the launcher's

    def _path(self) -> Path | None:
        if self._index_path:
            return self._index_path
        game = self._game()
        return default_path(game) if game else None

    def _open(self) -> Index:
        path = self._path()
        if path is None:
            # not a game rule: the game or one of its files isn't found
            raise FileNotFoundError("We couldn't find R.U.S.E., so there's no game index to open.")
        return Index(path)

    # --- the screen's words ---
    def languages(self) -> list[dict]:
        return schema.languages()

    # A scenario's kind is named by the game's own main-menu button (its text files, in the player's language), so
    # the Studio says exactly what to click: BATTLES (what other games call skirmish), OPERATION, CAMPAIGN.
    GAME_MENU = {"scen_kind_skirmish": "BTN_SKIRMI", "scen_kind_operation": "BTN_CHALLE",
                 "scen_kind_campaign": "BTN_CAMPAI"}

    def strings(self, lang: str = schema.BASE) -> dict:
        out = words(lang)
        try:
            ix = self._open()
            try:
                got = ix.names(list(self.GAME_MENU.values()), lang if lang in schema.LANGS else "us")
            finally:
                ix.close()
        except (OSError, sqlite3.Error, KeyError, ValueError):
            return out  # no index yet: the Studio's own words
        for word, key in self.GAME_MENU.items():
            text = (got.get(key) or "").strip()
            if text:
                out[word] = text[:1] + text[1:].lower() if text.isupper() else text  # BATTLES -> Battles
        return out

    def nations(self, lang: str = schema.BASE) -> list[str]:
        return [schema.nation(n, lang) for n in range(NATIONS)]

    def status(self) -> dict:
        path = self._path()
        if path is None or not path.is_file():
            return {"ready": False, "can_build": self._game() is not None}
        ix = Index(path)
        try:
            meta = ix.meta()
        finally:
            ix.close()
        if meta.get("format") != INDEX_FORMAT:  # made by an older Studio: build it again (the same button)
            return {"ready": False, "can_build": self._game() is not None, "old": True}
        return {"ready": True, "build": meta.get("build"), "built": meta.get("built"), "path": str(path)}

    # --- units ---
    def _all_units(self, ix: Index) -> list[dict]:
        if self._units is None:
            self._units = ix.units(ALL_CLASSES)
        return self._units

    def _new_units(self) -> dict[str, NewUnit]:
        """The current mod's new units (none when there's no mod, or its files can't be read: browsing goes on)."""
        try:
            edits = self._edits()
        except EditsFileError:
            return {}
        return edits.new_units if edits else {}

    def units(self, lang: str = schema.BASE, kind: str = "all", nation: int = -1, search: str = "",
              group: str = "all") -> dict:
        """The units and buildings to list, with names in `lang` (the code names by default), each with its `group`
        (what it's for, group_of); `group` lists only those. `groups`: the groups there are of `kind` and `nation`. The current mod's new units come first, under the nation
        and factory they were given, marked `new`. `kind` "ammo" lists the ammunition instead (see `ammo`)."""
        if kind == "ammo":
            return self.ammo(lang, search, group)
        ix = self._open()
        try:
            rows = self._all_units(ix)
            names = ix.names([u["key"] for u in rows], lang) if lang != schema.BASE else {}
            # the game's own words on each unit's card, English beside the code names: its type ("Light Tank", "Heavy
            # Bomber"), its name and its line ("May field armored units and armored recon."; the owner, 2026-10-03:
            # "descriptor building vehicular factory lorette ... what the fuck is that")
            told = lang if lang in schema.LANGS else "us"
            type_names = {k: html.unescape(t).strip() for k, t in ix.names([u["type_key"] for u in rows], told).items()}
            game_names = names if lang != schema.BASE else ix.names([u["key"] for u in rows], told)
            descs = ix.names([u.get("desc_key") for u in rows], told)
        finally:
            ix.close()
        by_address = {u["address"]: u for u in rows}
        new = []
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        for unit in edits.new_units.values() if edits else []:
            if unit.source not in by_address:  # a copied ammunition, listed under "ammo"
                continue
            src = by_address.get(unit.source, {"class": "TUniteAuSolDescriptor", "nation": 0, "factory": None})
            own = edits.of(unit.target)
            new.append({"address": unit.target, "class": src["class"], "key": None,
                        "nation": int(own.get("Nationalite", src["nation"])),
                        "factory": own.get("Factory", src["factory"]), "slot": None, "new": True,
                        "source": unit.source, "name": unit.name, "type_key": src.get("type_key"),
                        "desc_key": src.get("desc_key")})
        query, own_words = search.strip().lower(), words(lang)
        out, present, kinds = [], set(), {}
        for u in new + rows:
            k = KIND_OF.get(u["class"], "ground")
            if kind != "all" and k != kind or nation >= 0 and u["nation"] != nation:
                continue
            g = group_of(k, u.get("source") or u["address"], u["factory"])
            utype = None
            if k != "buildings":  # a building's type text is how much it takes, not what it is
                key = u.get("type_key") or ""
                utype = type_names.get(key) if not key.startswith(ARMOUR_TYPES) else None
                if utype:
                    kinds.setdefault(utype, key)
                else:  # a fort's gun, a ship, a transport: no type of its own in the game, so what it's for
                    utype = own_words.get("group_" + g) or None
                    if utype:
                        kinds.setdefault(utype, None)
            present.add(g)
            if group.startswith(TYPE_PICK) and utype != group[len(TYPE_PICK):] or \
                    not group.startswith(TYPE_PICK) and group != "all" and g != group:
                continue
            # what a player would call it: its own name, the game's, else (no name in the game) what it's for
            game_name = (u.get("name") or (game_names.get(u["key"]) or "").strip()
                         or own_words.get("no_game_name", "{group}").replace("{group}", own_words.get("group_" + g, g)))
            name = (u.get("name") or names.get(u["key"]) or (game_name if lang != schema.BASE else "")
                    or _tail(u["address"]))
            desc = (descs.get(u.get("desc_key")) or "").strip()
            if query and not any(query in s.lower() for s in (name, u["address"], utype or "", game_name)):
                continue
            out.append({"address": u["address"], "name": name, "base_name": _tail(u["address"]), "kind": k,
                        "nation": u["nation"], "nation_name": schema.nation(u["nation"], lang),
                        "factory": u["factory"], "slot": u["slot"], "new": u.get("new", False),
                        "source": u.get("source"), "group": g, "type": utype, "game_name": game_name, "desc": desc,
                        "decoy": g == "fake"})
        return {"units": out, "total": len(rows) + len(new), "groups": [g for g in GROUPS if g in present],
                "types": _type_order(kinds) if kind in UNIT_KINDS else []}

    # --- ammunition: what a weapon fires (damage, range, rate of fire); several units' weapons share one ---
    def _all_ammo(self, ix: Index) -> list[dict]:
        if self._ammo is None:
            self._ammo = ix.ammunition()
        return self._ammo

    def _ammo_names(self, ix: Index, rows, lang: str) -> dict:
        """Address -> what to call an ammunition: its kind and calibre in `lang` ("AP shell · Medium cal."), else
        its code name."""
        keys = [k for a in rows for k in (a["name_key"], a["type_key"]) if k]
        texts = ix.names(keys, lang) if lang != schema.BASE else {}
        return {a["address"]: ammo_name(texts, a["name_key"], a["type_key"]) or _tail(a["address"]) for a in rows}

    def ammo(self, lang: str = schema.BASE, search: str = "", group: str = "all") -> dict:
        """The ammunition to list, like `units`: the current mod's copies first (marked `new`), then the game's by
        `group` (AMMO_GROUPS: what it is) and kind, each with the units whose weapons fire it (`users`, names in
        `lang`). `group` lists only those; `groups`: the groups there are."""
        ix = self._open()
        try:
            rows = self._all_ammo(ix)
            names = self._ammo_names(ix, rows, lang)
            english = ix.names([a["type_key"] for a in rows if a["type_key"]], "us")
            users = {u for a in rows for u in a["users"]}
            user_names = self._names(ix, sorted(users), lang)
            nation_of = {u["address"]: u["nation"] for u in self._all_units(ix)}
        finally:
            ix.close()
        by_address = {a["address"]: a for a in rows}
        new = []
        for unit in self._new_units().values():
            src = by_address.get(unit.source)
            if src is None:
                continue
            new.append({"address": unit.target, "id": None, "users": [], "new": True, "source": unit.source,
                        "name": unit.name, "source_name": names[unit.source]})
        group_of = {a["address"]: AMMO_GROUP_OF.get(english.get(a["type_key"], ""), "other") for a in rows}
        order = {g: n for n, g in enumerate(AMMO_GROUP_ORDER)}
        # by group, then the game's kind (MG turrets apart from machine-guns), then the game's own order
        rows = sorted(rows, key=lambda a: (order[group_of[a["address"]]], english.get(a["type_key"], "")))
        words = search.strip().lower()
        out, present = [], set()
        for a in new + rows:
            g = group_of[a.get("source") or a["address"]]
            present.add(g)
            if group != "all" and g != group:
                continue
            name = a.get("name") or names[a["address"]]
            used = [user_names[u] for u in a["users"]]
            if words and words not in name.lower() and words not in a["address"].lower() \
                    and not any(words in u.lower() for u in used):
                continue
            nations = self._nations_of(a["users"] or by_address.get(a.get("source"), {}).get("users", []), nation_of, lang)
            out.append({"address": a["address"], "name": name, "base_name": _tail(a["address"]), "kind": "ammo",
                        "id": a["id"], "users": used, "nations": nations, "nation": -1, "nation_name": "",
                        "factory": None, "slot": None, "new": a.get("new", False), "source": a.get("source"),
                        "source_name": a.get("source_name"), "group": g})
        return {"units": out, "total": len(rows) + len(new), "groups": [g for g in AMMO_GROUP_ORDER if g in present]}

    @staticmethod
    def _nations_of(users, nation_of: dict, lang: str) -> list[str]:
        """The countries whose units fire an ammunition (a copy: its source's), in the game's nation order."""
        found = sorted({nation_of[u] for u in users if u in nation_of})
        return [schema.nation(n, lang) for n in found]

    def flags(self, lang: str = schema.BASE) -> dict:
        """Every unit flag, by number: each one the game's units carry in their flag lists (InitialFlagSet) and each
        one rusemod/labels.toml [flags] explains (0-104; the ones no unit carries are state the game sets while it
        runs, which do nothing in a unit's flags), with what it does, how many units have it and a few of them by
        name."""
        ix = self._open()
        try:
            rows = {r["flag"]: r for r in ix.flag_sets()}
            names = self._names(ix, sorted({e for r in rows.values() for e in r["examples"]}), lang)
        finally:
            ix.close()
        none = {"count": 0, "examples": []}
        return {"flags": [{"flag": n, "count": rows.get(n, none)["count"],
                           "examples": [names[e] for e in rows.get(n, none)["examples"]], "meaning": schema.flag(n, lang)}
                          for n in sorted(set(rows) | set(schema.flag_numbers()))]}

    def weapons(self, address: str, lang: str = schema.BASE) -> dict:
        """A unit's mounted weapons and what each fires: [{address, name, ammo: {address, name}, edited, range,
        game_range, firing, own_copy}], plus every ammunition it could fire instead (`choices`, the game's and the
        mod's copies). `range` is the ammo's range now (None when it has none), `game_range` that ammo's in the game
        (a copy's: its source's),
        `firing` the units that fire the same ammo with the mod's picks (this one too: address and name), `own_copy`
        whether it fires a copy made in this mod that no other unit fires."""
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, new = self._resolve(edits, address)
        base = address.partition(":")[0]
        ix = self._open()
        try:
            plan = ix.clone_plan(real)
            # in their place on the unit (turret 1's weapons first), so "Weapon 1" is the main gun
            parts = sorted((a for a in plan["copied"] + plan["shared"] if ix.show(a)["class"] == WEAPON),
                           key=lambda a: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", a)])
            weapons = []
            unit_shots = self._shots(ix, real.partition(":")[0])
            for part in parts:
                o = ix.show(part)
                tag = next((t for p, _n, t in o["values"] if p == "EffectTag"), None)
                fires = next((what for p, k, what in ix.uses(part) if p == "Ammunition" and k == "object"), None)
                where = (base + part[len(new.source):]) if new else part
                chosen = edits.get(where, "Ammunition") if edits else None
                current = str(chosen) if chosen else fires
                weapons.append({"real": part, "address": where, "name": tag or f"{_tail(part)}", "fires": fires,
                                "shot": self._shot_now(ix, edits, unit_shots.get(tag, []), real, base),
                                "range": self._range(ix, edits, current) if current else None,
                                "game_range": self._range(ix, edits, current, game=True) if current else None,
                                "firing": self._firing(ix, edits, current) if current else []})
            rows = self._all_ammo(ix)
            names = self._ammo_names(ix, rows, lang)
            nation_of = {u["address"]: u["nation"] for u in self._all_units(ix)}
            firing_names = self._names(ix, sorted({u for w in weapons for u in w["firing"]}), lang,
                                       edits.new_units if edits else None)
        finally:
            ix.close()
        users = {a["address"]: a["users"] for a in rows}
        copies = {t: u for t, u in (edits.new_units.items() if edits else []) if u.source in names}
        for t, u in copies.items():
            names[t] = u.name
            users[t] = users.get(u.source, [])
        choices = [{"address": a, "name": n, "new": a in copies,
                    "nations": self._nations_of(users.get(a, []), nation_of, lang)}
                   for a, n in sorted(names.items(), key=lambda kv: kv[1].lower())]
        out = []
        for w in weapons:
            chosen = edits.get(w["address"], "Ammunition") if edits else None
            current = str(chosen) if chosen else w["fires"]
            out.append({"address": w["address"], "name": w["name"],
                        "ammo": {"address": current, "name": names.get(current) or (_tail(current) if current else "")},
                        "game_ammo": w["fires"], "edited": bool(chosen), "shot": w["shot"],
                        "range": w["range"], "game_range": w["game_range"],
                        "firing": [{"address": u, "name": firing_names[u]} for u in w["firing"]],
                        "own_copy": bool(edits and current in edits.new_units and w["firing"] == [base])})
        return {"weapons": out, "choices": choices}

    def _range(self, ix: Index, edits: ModEdits | None, ammo: str, game: bool = False) -> float | None:
        """An ammunition's range (RANGE) with the mod's change, if any (`game`: as the game has it; a copy made in
        the mod: its source's); None when it has none."""
        mine = edits.get(ammo, RANGE) if edits and not game else None
        if mine is not None:
            return mine
        real, _new = self._resolve(edits, ammo)
        try:
            return next((n for p, n, _t in ix.show(real)["values"] if p == RANGE and n is not None), None)
        except KeyError:  # an ammunition this game build hasn't got
            return None

    def _fires(self, ix: Index, edits: ModEdits | None, unit: str) -> set[str]:
        """The ammunition a unit's weapons fire now, with the mod's picks (set_ammo)."""
        real, new = self._resolve(edits, unit)
        try:
            plan = ix.clone_plan(real)
        except KeyError:
            return set()
        out = set()
        for part in plan["copied"] + plan["shared"]:
            if ix.show(part)["class"] != WEAPON:
                continue
            chosen = edits.get((unit + part[len(new.source):]) if new else part, "Ammunition") if edits else None
            game = next((what for p, k, what in ix.uses(part) if p == "Ammunition" and k == "object"), None)
            if chosen or game:
                out.add(str(chosen) if chosen else game)
        return out

    def _firing(self, ix: Index, edits: ModEdits | None, ammo: str) -> list[str]:
        """The named units whose weapons fire `ammo` now: the game's, less the weapons the mod points at another,
        plus the ones it points at this one and the mod's copies of units that fire it."""
        real, _new = self._resolve(edits, ammo)
        maybe = set(next((a["users"] for a in self._all_ammo(ix) if a["address"] == real), []))
        if edits:
            maybe |= {t for t, u in edits.new_units.items() if u.source in maybe}
            maybe |= {t for (t, path, _how), e in edits.edits.items()
                      if path.rpartition(".")[2] == "Ammunition" and isinstance(e.value, Link)}
        return sorted(u for u in maybe if ammo in self._fires(ix, edits, u))

    def set_range(self, unit: str, weapon: str, value, mode: str = "own") -> dict:
        """A weapon's range, from its unit's page: the range of the ammunition it fires. "shared" changes that ammo,
        for every unit that fires it. "own" changes this unit only: an ammo no other unit fires (the game's, or a
        copy made in this mod) is changed where it is; otherwise the weapon gets a copy of it (new_ammo's recipe,
        named RANGE_COPY + the unit and the weapon's number) and fires that (set_ammo). A copy made here that's back
        at its source's range, with nothing else changed on it, goes again and the weapon fires its source."""
        if mode not in ("own", "shared"):
            raise StudioError(f"For whom: own or shared, not {mode!r}")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise StudioError("Range: one number.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        listed = self.weapons(unit)["weapons"]
        n, w = next(((i, x) for i, x in enumerate(listed) if x["address"] == weapon), (None, None))
        if w is None:
            raise StudioError(f"{weapon} isn't a weapon of {unit}")
        ammo = w["ammo"]["address"]
        if w["range"] is None:
            raise StudioError(f"{ammo} has no range to change")
        alone = [u["address"] for u in w["firing"]] in ([], [unit.partition(":")[0]])
        if mode == "shared" or alone:
            saved = self.edit(ammo, RANGE, value)
            fired = ammo
            copy = edits.new_units.get(ammo)
            if copy and _tail(ammo).startswith(RANGE_COPY) and copy.source == w["game_ammo"] and alone:
                if not ModEdits(edits.folder).of(ammo):  # nothing changed on it now: the game's own ammo again
                    self.set_ammo(unit, weapon, copy.source)
                    with self._saving:
                        ModEdits(edits.folder).remove_unit(ammo)
                    fired = copy.source
            return {"saved": saved["saved"], "ammo": fired, "range": saved["value"], "copied": False}
        source = edits.new_units[ammo].source if ammo in edits.new_units else ammo
        carry = edits.of(ammo)  # what the mod changed on the ammo it fired goes with it: only the range differs
        unit_name = re.sub(r"^Descriptor_[A-Za-z]+_", "", _tail(unit.partition(":")[0]))
        stem = safe_name(f"{unit_name} {n + 1}")
        ix = self._open()
        try:
            namespace = source.rsplit("/", 1)[0]
            target, k = f"{namespace}/{RANGE_COPY}{stem}", 2
            while target in edits.new_units or self._exists(ix, target):
                target, k = f"{namespace}/{RANGE_COPY}{stem}_{k}", k + 1
        finally:
            ix.close()
        with self._saving:
            ModEdits(edits.folder).add_unit(target, source, plain_name(target), carry, named=False)
        self.set_ammo(unit, weapon, target)
        saved = self.edit(target, RANGE, value)
        return {"saved": saved["saved"], "ammo": target, "range": saved["value"], "copied": True}

    def set_ammo(self, unit: str, weapon: str, ammo: str) -> dict:
        """Make a unit's weapon fire another ammunition (one of `weapons(unit)["choices"]`), saved in the current mod
        as a link at the weapon's address; choosing the game's own ammo again removes the change."""
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        if weapon.partition(":")[0] != unit.partition(":")[0]:
            raise StudioError(f"{weapon} isn't a weapon of {unit}")
        real_weapon, _new = self._resolve(edits, weapon)
        real_ammo, ammo_copy = self._resolve(edits, ammo)
        ix = self._open()
        try:
            try:
                o = ix.show(real_weapon)
            except KeyError:
                # not a game rule: the game or one of its files isn't found
                raise StudioError(f"There's no weapon at {weapon} in this game build.") from None
            if o["class"] != WEAPON:
                raise StudioError(f"{weapon} isn't a weapon (it's a {o['class']})")
            if o["shared"] and not o["export"]:
                raise StudioError(f"{weapon} is shared by several units; change it on each unit's own copy")
            try:
                if ix.show(real_ammo)["class"] != AMMO:
                    raise StudioError(f"{ammo} isn't an ammunition")
            except KeyError:
                raise StudioError(f"There's no ammunition at {ammo}.") from None
            game_ammo = next((what for p, k, what in ix.uses(real_weapon) if p == "Ammunition" and k == "object"), None)
            tag = next((t for p, _n, t in o["values"] if p == "EffectTag"), None)
            real_unit = real_weapon.partition(":")[0]
            mine = self._shots(ix, real_unit).get(tag, []) if tag else []
            theirs = self._shot_of(ix, real_ammo) if mine and ammo != game_ammo else []
        finally:
            ix.close()
        base = weapon.partition(":")[0]
        with self._saving:
            edits = ModEdits(edits.folder)
            if ammo == game_ammo:
                edits.reset(weapon, "Ammunition")
            else:
                edits.set(weapon, "Ammunition", Link(ammo))
            # the muzzle flash and sound follow the ammo: the Sherman's gun on a rifleman fires like a Sherman
            for s in mine:
                where, prop = base + s["part"][len(real_unit):], f"BinderEffets[{s['entry']}].v"
                other = next((x for x in theirs if x["key"] == s["key"]), theirs[0] if theirs else None)
                if other is None or other["call"] == s["call"]:
                    edits.reset(where, prop, s["share"])
                else:
                    edits.set(where, prop, Link(other["call"]), s["share"])
        return {"saved": str(edits.file), "ammo": ammo, "edited": ammo != game_ammo,
                "shot": _shot_name(theirs[0]["effect"]) if theirs else ""}

    def new_ammo(self, source: str, name: str) -> dict:
        """A copy of an ammunition in the current mod, for a weapon of its own (Groove's recipe: copy the ammo,
        change the copy, point one weapon at it). In game it keeps its source's name; `name` is what the Studio
        calls it. The copy gets a fresh AmmunitionId when built (rusemod.identity)."""
        name = (name or "").strip()
        if not name:
            raise StudioError("Give the copy a name.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: a copy is saved in a mod.")
        if source in edits.new_units:
            raise StudioError(f"{name}: copy the ammunition {_tail(source)} was made from instead")
        ix = self._open()
        try:
            try:
                o = ix.show(source)
            except KeyError:
                # not a game rule: the game or one of its files isn't found
                raise StudioError(f"{source} isn't in this game build") from None
            if not o["export"] or o["class"] != AMMO:
                raise StudioError(f"{source} isn't an ammunition, so it can't be copied here")
            namespace = source.rsplit("/", 1)[0]
            stem = safe_name(name)
            target = f"{namespace}/Ammo_{stem}" if stem else None
            n = 1
            while target is None or target in edits.new_units or self._exists(ix, target):
                target, n = f"{namespace}/Ammo_New_{n}", n + 1
        finally:
            ix.close()
        with self._saving:
            edits = ModEdits(edits.folder)
            if target in edits.new_units:
                raise StudioError(f"There's already a copy at {target}. Pick another name.")
            edits.add_unit(target, source, name, {}, named=False)
        return {"address": target, "name": name, "saved": str(edits.file)}

    @staticmethod
    def _exists(ix: Index, address: str) -> bool:
        try:
            ix.show(address)
            return True
        except KeyError:
            return False

    def menus(self, lang: str = schema.BASE) -> dict:
        """The build menus a new unit can go in: for every nation, its factories, each shown by the units it holds
        (the game has no names for factories), in menu order."""
        ix = self._open()
        try:
            rows = self._all_units(ix)
            names = self._names(ix, [u["address"] for u in rows if u["factory"] is not None], lang)
        finally:
            ix.close()
        by_menu: dict[tuple, list] = {}
        for u in rows:
            if u["factory"] is not None:
                by_menu.setdefault((u["nation"], u["factory"]), []).append(u)
        nations = []
        for n in range(NATIONS):
            factories = []
            for (nation, factory), units in sorted(by_menu.items()):
                if nation != n:
                    continue
                units = sorted(units, key=lambda u: (u["slot"] is None, u["slot"] or 0, u["address"]))
                factories.append({"factory": factory, "units": [names[u["address"]] for u in units[:3]],
                                  "count": len(units)})
            nations.append({"nation": n, "name": schema.nation(n, lang), "factories": factories})
        return {"nations": nations}

    def _names(self, ix: Index, addresses, lang: str, new_units: dict | None = None) -> dict:
        """Address -> what to call it on screen: a unit's in-game name in `lang`, a new unit's own name, else the
        end of its address."""
        keys = {u["address"]: u["key"] for u in self._all_units(ix)}
        texts = ix.names([keys.get(a) for a in addresses], lang) if lang != schema.BASE else {}
        new_units = new_units or {}
        return {a: new_units[a].name if a in new_units else texts.get(keys.get(a)) or _tail(a) for a in addresses}

    @staticmethod
    def _resolve(edits: ModEdits | None, address: str) -> tuple[str, NewUnit | None]:
        """Where the index knows an address: a new unit (or one of its own parts) is looked up in the unit it copies.
        Returns (the address in the index, the new unit or None)."""
        unit = edits.new_unit_of(address) if edits else None
        if unit is None:
            return address, None
        _base, _, inside = address.partition(":")
        return unit.source + (f":{inside}" if inside else ""), unit

    @staticmethod
    def _shots(ix: Index, unit: str) -> dict[str, list[dict]]:
        """A unit's shots, the muzzle flash and sound its model plays when a weapon fires, by the weapon's EffectTag:
        {tag: [{part, entry, key, call, effect, share}]}. The model (GfxDescriptor) has a part per tag
        (SousElements[i].k = weapon_effet_tag1); in it, a map binds an event (tir; tir_move: firing on the move) to a
        call of an effect, $/GFX/Everything/FX_Tir_*, which also plays the sound."""
        gfx = next((w for p, k, w in ix.uses(unit) if p == "GfxDescriptor" and k == "object"), None)
        if gfx is None or not gfx.startswith(unit + ":"):  # a model the unit doesn't own: not changed from here
            return {}
        kids = {p: w for p, k, w in ix.uses(gfx) if k == "object"}
        out = {}
        for path, _n, tag in ix.show(gfx)["values"]:
            m = re.fullmatch(r"SousElements\[(\d+)\]\.k", path)
            if not (m and tag and tag.startswith(SHOT_TAG)):
                continue
            todo, found = [kids.get(f"SousElements[{m.group(1)}].v")], []
            while todo:
                part = todo.pop(0)
                if part is None:
                    continue
                o = ix.show(part)
                keys = {p: text for p, _n2, text in o["values"] if p.endswith(".k")}
                for p, k, w in ix.uses(part):
                    b = re.fullmatch(r"BinderEffets\[(\d+)\]\.v", p)
                    if b and k == "object":
                        found.append({"part": part, "entry": int(b.group(1)), "key": keys.get(f"BinderEffets[{b.group(1)}].k"),
                                      "call": w, "effect": next((e for q, _k, e in ix.uses(w) if q == "Action"), None),
                                      "share": "own" if o["shared"] else None})
                    elif k == "object" and re.fullmatch(r"SousElements\[\d+\]\.v", p):
                        todo.append(w)
            out[tag] = found
        return out

    def _shot_of(self, ix: Index, ammo: str) -> list[dict]:
        """The shot of a weapon that fires `ammo` in the game (the first one that has one): what a unit's weapon
        plays when it's made to fire that ammo."""
        for user, path in ix.used_by(ammo):
            if path != "Ammunition" or ix.show(user)["class"] != WEAPON:
                continue
            tag = next((t for p, _n, t in ix.show(user)["values"] if p == "EffectTag"), None)
            found = self._shots(ix, user.partition(":")[0]).get(tag) if tag else None
            if found:
                return found
        return []

    @staticmethod
    def _shot_now(ix: Index, edits: ModEdits | None, shots: list[dict], real: str, base: str) -> str:
        """The name of the shot a weapon plays now (its main event, tir), with the mod's change if it has one."""
        s = next((x for x in shots if x["key"] == "tir"), shots[0] if shots else None)
        if s is None:
            return ""
        unit = real.partition(":")[0]
        link = edits.get(base + s["part"][len(unit):], f"BinderEffets[{s['entry']}].v", s["share"]) if edits else None
        effect = s["effect"]
        if link:
            try:
                effect = next((e for q, _k, e in ix.uses(str(link)) if q == "Action"), effect)
            except KeyError:
                pass
        return _shot_name(effect)

    def unit(self, address: str, lang: str = schema.BASE, via: str = "") -> dict:
        """One unit (or any object): its values in groups, its parts and what uses it, with the current mod's edits.
        `via` is the named unit the modder came from: a part several units share can then be changed for that unit
        only (it gets its own copy) as well as for all of them. A new unit's page is its source's, at the new
        address, with the copy's own values as edits."""
        try:
            mod = self._edits()
            broken = ""
        except EditsFileError as exc:  # browsing still works; editing waits until the file is fixed
            mod, broken = None, str(exc)
        new_units = mod.new_units if mod else {}
        real, new = self._resolve(mod, address)
        via_real, _via_new = self._resolve(mod, via) if via else ("", None)
        ix = self._open()
        try:
            try:
                o = ix.show(real)
            except KeyError:
                # not a game rule: the game or one of its files isn't found
                raise StudioError(f"There's nothing at {address} in this game build.") from None
            share = None
            if o["shared"] and not o["export"]:
                owners = o["owners"] + [t for t, u in new_units.items() if u.source in o["owners"]]  # copies use it too
                names = self._names(ix, owners + ([via] if via else []), lang, new_units)
                path = ix.path_to(via_real, o["address"]) if via_real in o["owners"] else None
                share = {"owners": [{"address": a, "name": names[a]} for a in owners],
                         "via": {"address": via, "name": names[via], "path": path} if path else None}
            types = ix.prop_types(o["class"])
            plan = ix.clone_plan(real)
            base = address.partition(":")[0]
            rewrite = (lambda a: base + a[len(new.source):]) if new else (lambda a: a)  # its own parts, at its address
            parts = [{"address": rewrite(a), "class": ix.show(a)["class"], "shared": False} for a in plan["copied"]] + \
                    [{"address": a, "class": ix.show(a)["class"], "shared": True} for a in plan["shared"]]
            uses = []
            for a in plan["references"]:  # named objects it uses (weapons, ammo…): editable on their own page
                try:
                    uses.append({"address": ix.show(a)["address"], "class": ix.show(a)["class"]})
                except KeyError:  # an import the index couldn't find
                    pass
            all_users = [] if new else ix.used_by(real)  # nothing in the game points at a new unit
            used_by = [{"address": a, "path": p} for a, p in all_users[:30]]
            key = next((t for p, _n, t in o["values"] if p == "NameInMenuToken"), None)
            shown = ix.names([key], lang).get(key) if key and lang != schema.BASE else None
            # the game's own words for it, English beside the code names: its name and its card's line
            told = lang if lang in schema.LANGS else "us"
            said = {p: t for p, _n, t in o["values"]
                    if p in ("DescriptionUnitHintToken", "LongDescriptionUnitHintToken")}
            dkey = said.get("DescriptionUnitHintToken") or said.get("LongDescriptionUnitHintToken")
            about = ix.names([k for k in (key, dkey) if k], told)
            game_name, desc = (about.get(key) or "").strip(), (about.get(dkey) or "").strip()
            source_name = self._names(ix, [new.source], lang)[new.source] if new else None
        finally:
            ix.close()
        editable, why = self._editable(o)
        if broken:
            editable, why = False, broken
        top = new is not None and ":" not in address  # the new unit itself, not a part of it
        if top:
            shown = new.name
        keyed = address if new else o["address"]  # a copy's edits by its own address, anything else by the index's
        edits = mod.of(keyed, "shared" if share else None) if mod else {}
        own = mod.of(f"{via}:{share['via']['path']}", "own") if mod and share and share["via"] else {}
        users = len({a.split(":")[0] for a, _p in all_users})
        rows: dict[str, dict] = {}
        for prop, p in _props(o).items():
            values = []
            for num, text in zip(p["numbers"], p["texts"]):
                if prop == "Nationalite" and num is not None:
                    n = edits.get(prop, num) if top else num
                    values.append(f"{n} ({schema.nation(n, lang)})")
                elif prop == "NameInMenuToken" and top:
                    values.append(shown)
                elif prop == identity.DEBUG_NAME and top and text:  # the build gives the copy its own (MOD_FORMAT §10.5)
                    values.append(identity.debug_name(new.source, text, address))
                elif prop == "NameInMenuToken" and shown:
                    values.append(f"{text} ({shown})")
                else:
                    values.append(text if num is None else str(num))
            rows[prop] = {"prop": prop, "label": schema.label(prop, lang), "group": schema.group(prop),
                          "values": values, "numbers": p["numbers"], "list": p["list"],
                          "type": types.get(prop + "[]" if p["list"] else prop, ""),
                          "editable": editable and _can_edit(prop, p),
                          "locked": prop in NOT_EDITABLE, "edited": edits.get(prop), "edited_own": own.get(prop)}
        if "Nationalite" not in rows and o["class"] in KIND_OF:  # 0 isn't written
            n = edits.get("Nationalite", 0) if top else 0
            rows["Nationalite"] = {"prop": "Nationalite", "label": schema.label("Nationalite", lang),
                                   "group": "identity", "values": [f"{n} ({schema.nation(n, lang)})"], "numbers": [0],
                                   "list": False, "type": "int32", "editable": False, "locked": True, "edited": None,
                                   "edited_own": None}
        groups = []
        for g in schema.GROUP_ORDER:
            members = [r for r in rows.values() if r["group"] == g]
            if members:
                groups.append({"key": g, "name": schema.group_name(g, lang), "rows": members})
        return {"address": address, "class": o["class"], "name": shown or _tail(address),
                "game_name": (new.name if top else game_name), "desc": desc,
                "stable": o["stable"], "shared": o["shared"], "owners": o["owners"], "groups": groups,
                "parts": parts, "uses": uses, "used_by": used_by, "editable": editable, "why_not": why,
                "named": bool(o["export"]), "share": share,
                "users": users if o["export"] and o["class"] not in KIND_OF and users > 1 else 0,
                "can_copy": bool(o["export"]) and o["class"] in KIND_OF and editable and new is None,
                "can_copy_ammo": bool(o["export"]) and o["class"] == AMMO and editable and new is None,
                "has_weapons": o["class"] in KIND_OF,  # the page then asks for weapons(address)
                "new": {"source": new.source, "source_name": source_name} if top else None}

    def _editable(self, o: dict) -> tuple[bool, str]:
        """Whether this object's values can be edited from the Studio, and if not, why (a key of the tool's words)."""
        if not o["stable"]:
            return False, "not_stable"
        return True, ""

    def _where(self, ix: Index, o: dict, mode: str, via: str, address: str, edits: ModEdits) -> tuple[str, str | None]:
        """Where a change to object `o` (shown at `address`) is written, and how (MOD_FORMAT §10.5). A part several
        units share is changed for all of them ("shared", at its own address) or for one of them only ("own":
        through that unit, which gets its own copy of the part); anything else just at its address."""
        if not (o["shared"] and not o["export"]):
            return address, None
        if mode == "shared":
            return o["address"], "shared"
        if mode != "own":
            raise StudioError(f"{o['address']} is shared by several units: change it for one of them, or for all")
        via_real, _new = self._resolve(edits, via) if via else ("", None)
        path = ix.path_to(via_real, o["address"]) if via_real in o["owners"] else None
        if path is None:
            raise StudioError(f"{via or 'no unit'} doesn't use {o['address']}, so it can't get its own copy")
        return f"{via}:{path}", "own"

    # --- maps (read from the game itself, not the index: the ground isn't in the index) ---
    def maps(self) -> dict:
        """The Maps view's list: the game's maps that ship a terrain pack, one per pack, in the game's order, with
        the names the game lists them by (rusemod.terrain)."""
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        shipped = [m for m in map_list(game) if m["found"]]
        copies = self._new_maps()
        if not copies:
            return {"maps": shipped}
        out = []
        for m in shipped:
            out.append(m)
            for name, spec in copies.values():  # each new map right after the map it copies
                if spec.copy_of.lower() == m["pack"].lower():
                    out.append({"pack": name, "names": [spec.names["us"]], "paths": [name],
                                "titles": {lang: [spec.names.get(lang, spec.names["us"])] for lang in m["titles"]},
                                "kinds": [self._copy_kind(spec)], "file": pack_file(name), "found": True,
                                "copy_of": m["pack"], "copy_of_names": m["names"]})
        return {"maps": out}

    # --- new maps (MOD_FORMAT §8 "A new map"): a copy of a shipped map with a name of its own, made by the build from
    # the map project's maps/<name>/map.toml (copy_of). The map view shows a copy as the map it copies with the copy's
    # own edits on top: its game data is read from the shipped map, its edits go to maps/<name>/. Proven in the game
    # (TESTS.md T15b, T16: 101 new maps listed at once, each playing its own ground).
    def _new_maps(self) -> dict:
        """The current map project's new maps: {name, lower case: (name, newmap.NewMap)}."""
        from rusemod import newmap
        folder = self._map_dir()
        out: dict = {}
        if folder is None or not (folder / "maps").is_dir():
            return out
        for f in sorted((folder / "maps").iterdir()):
            path = f / "map.toml"
            if not path.is_file():
                continue
            try:
                specs = newmap.parse(tomllib.loads(path.read_text(encoding="utf-8")), f"maps/{f.name}/map.toml",
                                     f.name)
            except (OSError, ValueError):  # (a broken file is the mod check's to say)
                continue
            if specs:
                out[f.name.lower()] = (f.name, specs[0])
        return out

    def _game_pack(self, pack: str) -> str:
        """The game's map whose files a map of the view is read from: a new map's shipped map, else the map itself."""
        copy = self._new_maps().get(str(pack).lower())
        return copy[1].copy_of if copy else pack

    def duplicate_options(self, pack: str) -> dict:
        """What Duplicate map needs to know about `pack` before asking for a name: {"source": the shipped map it
        copies, "entries": what a copy can start from (_menu_entries: its BATTLES maps, Operations and campaign
        chapters), "name": a suggested name, "folder": the map project the copy goes into (None: one is made), "why":
        why it can't be copied, or None}."""
        source = self._game_pack(pack)
        entries = self._menu_entries(source)
        m = next((x for x in self.maps()["maps"] if x["pack"] == pack), {})
        called = ((m.get("titles") or {}).get("us") or m.get("names") or [pack])[0]  # what players call it
        folder = self._map_dir()
        return {"source": source, "entries": entries, "name": f"{called} 2",
                "folder": str(folder) if folder else None,
                # not a game rule: our map copier starts from one of the menus' entries (its scenario and menu entry)
                "why": None if entries else "No menu offers this map (BATTLES, OPERATIONS or the CAMPAIGN), so it has "
                                            "no entry to copy."}

    def _menu_entries(self, source: str) -> list[dict]:
        """The game's menu entries of map `source` a copy can start from (rusemod.newmap.menu_entries), in the map
        list's order: [{"name": its map-list name, "kind": battles, operation or campaign, "titles": what the menus
        call it, {lang: text}}]. Kept per game file."""
        from rusemod import newmap
        from rusemod import players as pl
        from rusemod.ndf import Ndf
        from rusemod.terrain import menu_keys, menu_texts
        game = self._game()
        glad_path = find_pack(game, "ZZ_GladPatchableWin.dat") if game is not None else None
        if glad_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("ZZ_GladPatchableWin.dat isn't in the game folder.")
        key = ("menu-entries", str(glad_path), glad_path.stat().st_mtime, source.lower())
        with self._grounds_lock:
            cached = self._sceneries.get(key)
        if cached is not None:
            return cached
        with Edat.open(str(glad_path)) as glad:
            def read(member):
                e = glad.entry(member)
                return bytes(glad.read(e)) if e is not None else None
            g, m = Ndf(read(pl.GLOBALS)), Ndf(read(pl.MAPINFO))
        found = newmap.menu_entries(m, g, source)
        menus, keys = menu_keys(g), {}
        for mi, _gi, name, _kind in found:
            guid = next((bytes(v.payload) for pi, v in m.objects[mi].props if m.prop_name(pi) == "GUID"), b"")
            ranked = sorted(menus.get(guid, []))
            keys[name] = ranked[0][1] if ranked else None
        texts = menu_texts(game, {k for k in keys.values() if k is not None})
        out = [{"name": name, "kind": kind,
                "titles": {lang: t[keys[name]] for lang, t in texts.items() if keys[name] in t}}
               for _mi, _gi, name, kind in found]
        with self._grounds_lock:
            self._sceneries[key] = out
        return out

    def _copy_kind(self, spec) -> str:
        """The map list's kind of a new map (the Maps view's filter: skirmish, operation or campaign), by the entry it
        copies: a BATTLES map unless map.toml names an Operation's or a campaign chapter's."""
        if spec.entry is None:
            return "skirmish"
        try:
            kind = next((e["kind"] for e in self._menu_entries(spec.copy_of) if e["name"] == spec.entry), "battles")
        except (StudioError, OSError, ValueError):
            kind = "battles"
        return {"battles": "skirmish"}.get(kind, kind)

    def duplicate_map(self, pack: str, name: str, entry: str | None = None, preset: str | None = None) -> dict:
        """Make a new map: a copy of `pack` called `name` in the menus, in the current map project (one is made when
        none is picked). The map project's changes to `pack` so far are copied with it, so the copy starts as the
        map view shows it; with `preset` (rusemod.presets: "blank_terrain", "blank_ocean", a Battles map only) it
        starts blank instead, its files the preset's, made from the shipped map's own. Returns {"pack": the new map's
        own name (its folder and files), "maps": maps()}."""
        from rusemod import newmap, presets, roadnet
        if preset is not None and preset not in presets.KINDS:
            raise StudioError(f"There's no {preset!r} to start from.")
        name = " ".join(str(name or "").split())
        if not name:
            raise StudioError("Give the new map a name.")
        if len(name) > newmap.NAME_LONGEST:
            raise StudioError(f"The name is {len(name)} characters; the menus take {newmap.NAME_LONGEST}.")
        opts = self.duplicate_options(pack)
        if opts["why"]:
            raise StudioError(opts["why"])
        old_copy = self._new_maps().get(pack.lower())
        if entry is None and old_copy is not None:
            entry = old_copy[1].entry  # a copy of a copy copies the same entry
        battles = [e["name"] for e in opts["entries"] if e["kind"] == "battles"]
        if entry is not None and entry not in [e["name"] for e in opts["entries"]]:
            raise StudioError(f"{opts['source']} has no entry {entry!r}.")
        if entry is None and len(battles) != 1:
            raise StudioError("Pick what to copy: one of this map's BATTLES maps, Operations or campaign chapters.")
        if entry is not None and battles == [entry]:
            entry = None  # the map's one BATTLES map: map.toml needn't say it
        files: dict = {}
        if preset is not None:
            if entry is not None and entry not in battles:
                # not a game rule: a blank copy takes the scenario's own items out, which a mission's script needs
                raise StudioError("Blank Terrain and Blank Ocean start from a Battles map.")
            game = self._game()
            if game is None:
                # not a game rule: the game or one of its files isn't found
                raise StudioError("The game folder isn't found, so the map's own files can't be read.")
            try:
                scen = presets.copy_scenario(game, opts["source"], entry)
                files = presets.preset_files(preset, presets.read_facts(game, opts["source"], scen))
            except (presets.PresetError, OSError, ValueError, KeyError, struct.error) as exc:
                raise StudioError(f"{opts['source']} can't start blank: {exc}") from None
        if self._map_dir() is None:
            self.new_mod(name, "map")
        folder = self._map_dir()
        taken = {m["pack"].lower() for m in self.maps()["maps"]}
        taken |= {f.name.lower() for f in (folder / "maps").iterdir()} if (folder / "maps").is_dir() else set()
        new = _pack_name(name, taken)
        players = self._read_players(pack)  # the map's player count in this project comes along too
        if entry is None and players is not None:
            entry = players.entry
        spec = newmap.NewMap(opts["source"], {"us": name}, entry)
        target, src_dir = folder / "maps" / new, folder / "maps" / pack
        header = (f"A new map: a copy of {opts['source']} called {name!r} in the menus (MOD_FORMAT §8).\n"
                  "Made in the RUSE Studio's Duplicate map, which rewrites this file.")
        checks = {"terrain.toml": lambda data: parse_strokes(data.get("stroke", []), "terrain.toml"),
                  "scenario.toml": _scenario_checked("scenario.toml"),
                  "roads.toml": lambda data: (roadnet.parse_roads(data.get("road", []), "roads.toml"),
                                              roadnet.parse_take_out(data.get("take_out"), "roads.toml")),
                  "scenery.toml": lambda data: (scenery.parse_objects(data.get("object", []), "scenery.toml")
                                                + scenery.parse_erase(data.get("erase", []), "scenery.toml"))}
        with self._saving:
            target.mkdir(parents=True)
            for fname, text in files.items():  # a blank start: the preset's files, each checked as the build reads it
                _save_checked(target / fname, text, checks[fname])
            for f in sorted(src_dir.iterdir()) if src_dir.is_dir() and not files else []:  # the changes made so far
                if f.is_file() and f.name in MAP_FILES and f.name != "map.toml":
                    (target / f.name).write_bytes(f.read_bytes())
            _save_checked(target / "map.toml", newmap.map_toml(spec, players.count if players else None, header),
                          lambda data: newmap.parse(data, "map.toml", new))
        return {"pack": new, "maps": self.maps()["maps"]}

    def delete_map(self, pack: str) -> dict:
        """Delete a new map (one made with Duplicate map) from the current map project: its folder maps/<name>/, with
        every change made to it, goes to the Recycle Bin (it can be put back from there). The game's own maps can't be
        deleted. Returns {"deleted": its name, "copy_of": the map it copied (the view opens that), "maps": maps()}."""
        from rusemod.recycle import to_recycle_bin
        copy = self._new_maps().get(str(pack or "").lower())
        if copy is None:
            # not a game rule: the Studio deletes only what it made; the game's own maps are never touched
            raise StudioError(f"{pack} isn't a new map made in these map changes, so it can't be deleted here: the "
                              "game's own maps stay.")
        name, spec = copy
        with self._saving:
            try:
                to_recycle_bin(self._map_dir() / "maps" / name)
            except OSError as exc:
                raise StudioError(str(exc)) from None
        return {"deleted": name, "copy_of": spec.copy_of, "maps": self.maps()["maps"]}

    # A map's data the window asks for (its scenery, roads, bridges, cover...), kept in memory: about six kinds a map,
    # so 24 is the last few maps. It was 3 in all, so one map's own kinds pushed each other out as it opened, and
    # every visit read everything again (issue #15: "a map is slow to open").
    MAP_DATA_KEPT = 24
    MAP_DATA_FORMAT = 1  # the kept files' format: a new one means they're all made again

    def _kept_on_disk(self, what: str, pack: str, sources: list, make):
        """`make()`'s answer (JSON-ready) for one map, kept in the cache folder between runs: named by the map, the
        game files it's read from (each one's size and time: a game update or a changed pack makes a new one) and this
        Studio's version (the names and rules it's made with). Reading the game files again took seconds a map on
        M03_Italie (its road pieces 2.8, its scenery 2, its bridges 1.3). Never fails for the cache's sake."""
        from . import __version__
        stamp = "-".join(f"{p.stat().st_size}-{int(p.stat().st_mtime)}" for p in sources)
        kept = self.cache_dir / "maps" / f"{what}-{pack}-{stamp}-v{__version__}-{self.MAP_DATA_FORMAT}.json"
        try:
            return json.loads(kept.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        out = make()
        try:
            kept.parent.mkdir(parents=True, exist_ok=True)
            part = kept.with_suffix(".part")
            part.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
            part.replace(kept)  # whole or not at all
        except OSError:
            pass
        return out

    def map_view(self, pack: str, lod: str = "lowdef") -> dict:
        """One map's ground for the 3D view: its mesh as packed buffers the window unpacks, and its overview picture.
        `lod`: "lowdef" (light, opens fast) or "highdef" (the close-up mesh the game draws near the camera)."""
        if lod not in LODS:
            raise StudioError(f"No detail level called {lod!r}")
        pack = self._game_pack(pack)  # a new map shows the ground it copies
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        key = (str(game), pack, lod)
        with self._grounds_lock:
            if key in self._grounds:
                self._grounds[key] = self._grounds.pop(key)  # most recent last
                return self._grounds[key]
        map_path = find_pack(game, pack_file(pack))
        view = (self._kept_on_disk(f"ground-{lod}", pack, [map_path], lambda: terrain(game, pack, lod))
                if map_path is not None else terrain(game, pack, lod))
        with self._grounds_lock:
            self._grounds[key] = view
            while len(self._grounds) > 4:
                self._grounds.pop(next(iter(self._grounds)))
        return view

    def map_scenery(self, pack: str) -> dict:
        """What stands on a map, for the 3D view (rusemod.scenery.view): every building, and a sample of props and
        trees, each with its type (name, group, the game editor's category, its model). About a second per map."""
        pack = self._game_pack(pack)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        map_path, unit_path = find_pack(game, pack_file(pack)), find_pack(game, "ZZ_GladPatchableWin.dat")
        if map_path is None or unit_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{pack_file(pack) if map_path is None else 'ZZ_GladPatchableWin.dat'} isn't in the game "
                              f"folder.")
        key = (str(map_path), map_path.stat().st_mtime)
        with self._grounds_lock:
            if key in self._sceneries:
                return self._sceneries[key]
        def make():
            with Edat.open(str(unit_path)) as unit_arc, Edat.open(str(map_path)) as map_arc:
                try:
                    return scenery.view(map_arc, unit_arc, self._scenery_types(unit_path, unit_arc))
                except (KeyError, scenery.SceneryError) as exc:
                    raise StudioError(f"{map_path.name}: its scenery can't be read ({exc}).") from None
        out = self._kept_on_disk("scenery", pack, [map_path, unit_path], make)
        with self._grounds_lock:
            self._sceneries[key] = out
            while len(self._sceneries) > self.MAP_DATA_KEPT:
                self._sceneries.pop(next(iter(self._sceneries)))
        return out

    def _scenery_types(self, unit_path: Path, unit_arc) -> dict:
        """The game's scenery types (rusemod.scenery.descriptors), read once per ZZ_GladPatchableWin.dat."""
        dkey = (str(unit_path), unit_path.stat().st_mtime)
        if self._descriptors[0] != dkey:
            self._descriptors = (dkey, scenery.descriptors(unit_arc))
        return self._descriptors[1]

    def map_roads(self, pack: str) -> dict:
        """A map's roads for the 3D view (rusemod.scenery Scenery.roads): {"pieces": [x0, y0, x1, y1, x2, y2, x3, y3,
        ...]}, each road piece a cubic Bézier's four points, in map units."""
        pack = self._game_pack(pack)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        map_path = find_pack(game, pack_file(pack))
        if map_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{pack_file(pack)} isn't in the game folder.")
        key = ("roads", str(map_path), map_path.stat().st_mtime)
        with self._grounds_lock:
            if key in self._sceneries:
                return self._sceneries[key]
        def make():
            with Edat.open(str(map_path)) as map_arc:
                try:
                    sc = scenery.Scenery(bytes(map_arc.read(map_arc.find(scenery.MEMBER))))
                except (KeyError, scenery.SceneryError, struct.error) as exc:
                    raise StudioError(f"{map_path.name}: its scenery can't be read ({exc}).") from None
            return {"pieces": [round(v) for piece in sc.roads() for v in piece]}
        out = self._kept_on_disk("roads", pack, [map_path], make)
        with self._grounds_lock:
            self._sceneries[key] = out
            while len(self._sceneries) > self.MAP_DATA_KEPT:
                self._sceneries.pop(next(iter(self._sceneries)))
        return out

    def map_cover(self, pack: str) -> dict:
        """Where units hide on a map, as the game has it (rusemod.cover: the cover grid in DataMap_Win.dat), for the
        map view to draw under the mod's cover brushes: {"size": n, "box": [x0, y0, width, height] in map units,
        "bits": base64 of n*n bits (cell i at byte i // 8, bit i % 8; row by row from y0), 1 = cover}. n is at most
        1024 (bigger grids are sampled); kept per map."""
        from rusemod import cover
        pack = self._game_pack(pack)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        path = find_pack(game, cover.PACK)
        if path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{cover.PACK} isn't in the game folder.")
        key = ("cover", str(path), path.stat().st_mtime, pack.lower())
        with self._grounds_lock:
            cached = self._sceneries.get(key)
        if cached is not None:
            return cached
        def make():
            with Edat.open(str(path)) as arc:
                try:
                    win = bytes(arc.read(arc.find(cover.member(pack))))
                except KeyError:
                    raise StudioError(f"{pack} has no cover grid in {cover.PACK}, so its cover can't be shown or "
                                      f"painted.") from None
            try:
                got = cover.cover_bits(win)
            except (cover.CoverError, ValueError, struct.error) as exc:
                raise StudioError(f"{pack}: its cover grid can't be read ({exc}).") from None
            return {"size": got["size"], "box": list(got["box"]), "bits": base64.b64encode(got["bits"]).decode("ascii")}
        out = self._kept_on_disk("cover", pack.lower(), [path], make)
        with self._grounds_lock:
            self._sceneries[key] = out
        return out

    def map_movement(self, pack: str) -> dict:
        """Where units can go on a map, as the game has it (rusemod.nav: the navigation graphs in DataMap_Win.dat),
        for the map view to draw under the mod's block brushes: {"size": n, "box": [x0, y0, width, height] in map
        units, "infantry": base64 of n*n bits, "vehicles": the same} (cell i at byte i // 8, bit i % 8; row by row
        from y0; 1 = a circle of that graph holds the cell's middle). n is 512; kept per map."""
        from rusemod import cover, nav
        from ruse_mod_engine import sdb
        pack = self._game_pack(pack)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        path = find_pack(game, cover.PACK)
        if path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{cover.PACK} isn't in the game folder.")
        key = ("movement", str(path), path.stat().st_mtime, pack.lower())
        with self._grounds_lock:
            cached = self._sceneries.get(key)
        if cached is not None:
            return cached
        with Edat.open(str(path)) as arc:
            try:
                win = bytes(arc.read(arc.find(cover.member(pack))))
            except KeyError:
                raise StudioError(f"{pack} has no movement data in {cover.PACK}.") from None
        try:
            bufs = sdb.split_mapinfo(win)[1]
            graphs = {name: nav.Graph.read(bufs[k]) for name, k in (("infantry", 1), ("vehicles", 2))}
        except (nav.NavError, ValueError, struct.error, TypeError) as exc:
            raise StudioError(f"{pack}: its movement data can't be read ({exc}).") from None
        n = 512
        x0, y0, size = graphs["infantry"].box[0], graphs["infantry"].box[1], graphs["infantry"].box[2]
        out = {"size": n, "box": [float(x0), float(y0), float(size), float(size)]}
        cell = size / n
        for name, g in graphs.items():
            bits = bytearray((n * n + 7) // 8)
            for cx, cy, r, _l, _c in g.circles[:-1]:
                if r <= 0:
                    continue
                i0, i1 = max(0, int((cx - r - x0) / cell)), min(n - 1, int((cx + r - x0) / cell))
                j0, j1 = max(0, int((cy - r - y0) / cell)), min(n - 1, int((cy + r - y0) / cell))
                rr = r * r
                for j in range(j0, j1 + 1):
                    dy = y0 + (j + 0.5) * cell - cy
                    dy2 = dy * dy
                    if dy2 > rr:
                        continue
                    half = (rr - dy2) ** 0.5
                    a, b = max(i0, int((cx - half - x0) / cell)), min(i1, int((cx + half - x0) / cell))
                    for i in range(a, b + 1):
                        k = j * n + i
                        bits[k >> 3] |= 1 << (k & 7)
            out[name] = base64.b64encode(bytes(bits)).decode("ascii")
        with self._grounds_lock:
            self._sceneries[key] = out
        return out

    def map_scenarios(self, pack: str, edited: bool = True) -> dict:
        """A map's scenarios (rusemod.scenario), for the map view: {"scenarios": [{"file", "kind", "entries",
        "zones", "items"}]}, by kind (skirmish, operation, campaign, demo, test, unused: what the game's map list and
        menus do with it), then by name. `entries`: the map list's entries that load it, each with its name and what
        the menus call it in each language ({lang: text}). Zones are drawn as their triangles; items are starting
        points, spawns, circle and rectangle zones, labels and waypoints, each with its number (`item`). `edited`:
        as the current mod leaves them (items it moves are at their new place and marked `moved`; the units and
        buildings it spawns come last, marked `mine` with their number among the mod's spawns)."""
        from rusemod.terrain import menu_texts
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        path = find_pack(game, scenario.PACK)
        glad_path = find_pack(game, "ZZ_GladPatchableWin.dat")
        if path is None or glad_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{scenario.PACK if path is None else 'ZZ_GladPatchableWin.dat'} isn't in the game folder.")
        mine, pack = pack, self._game_pack(pack)  # a new map: the game's scenarios of the map it copies, its own edits
        copy = self._new_maps().get(mine.lower()) if mine != pack else None
        key = ("scenarios", str(path), path.stat().st_mtime, pack.lower())
        with self._grounds_lock:
            cached = self._sceneries.get(key)
        if cached is not None:
            result = self._with_units(self._with_scenario_edits(mine, _copied(cached, copy))) if edited \
                else _copied(cached, copy)
            return self._with_scenario_owners(game, pack, result)
        with Edat.open(str(path)) as arc:
            found = scenario.of_map(arc, pack)
            paths = {}  # each scenario's warm-up camera paths: a starting point's opening camera (scenario.campaths)
            for f in found:
                try:
                    paths[f] = scenario.campaths(bytes(arc.read(arc.find(scenario.campath_member(pack, f)))))
                except (KeyError, ValueError, struct.error):
                    paths[f] = {}
        with Edat.open(str(glad_path)) as glad:
            kinds = scenario.kinds_of(glad, pack)
        texts = menu_texts(game, {e["key"] for es in kinds.values() for e in es if e["key"] is not None})
        out_list = []
        for f, s in found.items():
            entries = [{"name": e["name"], "kind": e["kind"],
                        "titles": {lang: t[e["key"]] for lang, t in texts.items() if e["key"] in t}}
                       for e in kinds.get(f.lower(), [])]
            kind = entries[0]["kind"] if entries else "unused"
            view = scenario.view(s)
            for k, it in enumerate(view["items"]):
                it["item"] = k
                cam = paths.get(f, {}).get(it.get("warmup") or "")
                if it["kind"] == "StartingPoint" and cam and cam.get("path"):
                    it["cam"] = {"path": cam["path"], "look": (cam.get("looks") or [None])[-1]}  # rests at the last key
            out_list.append({"file": f, "kind": kind, "entries": entries, **view})
        out_list.sort(key=lambda s: (scenario.KINDS.index(s["kind"]), (s["entries"][0]["name"] if s["entries"] else s["file"]).lower()))
        out = self._with_units({"scenarios": out_list})
        with self._grounds_lock:
            self._sceneries[key] = out
        result = self._with_units(self._with_scenario_edits(mine, _copied(out, copy))) if edited else _copied(out, copy)
        return self._with_scenario_owners(game, pack, result)

    def _with_scenario_owners(self, game: Path, pack: str, view: dict) -> dict:
        """Each scenario's `owners`: who Add unit can give a spawn to (_scenario_owners), read once per scenario."""
        todo = [s for s in view.get("scenarios", [])
                if (str(game), pack.lower(), s.get("file", "").lower()) not in self._scenario_owners]
        if todo:
            ia_path = find_pack(game, "IA_Common.dat")
            try:
                ia = Edat.open(str(ia_path)) if ia_path is not None else None
            except OSError:
                ia = None
            try:
                for s in todo:
                    key = (str(game), pack.lower(), s.get("file", "").lower())
                    self._scenario_owners[key] = self._scenario_owners_of(ia, pack, s.get("file", ""))
            finally:
                if ia is not None:
                    ia.close()
        for s in view.get("scenarios", []):
            s["owners"] = self._scenario_owners[(str(game), pack.lower(), s.get("file", "").lower())]
        return view

    @staticmethod
    def _scenario_owners_of(ia, pack: str, file: str) -> list[dict]:
        """Who a spawn can be given to in a scenario (Add unit's "Who gets it?"): Neutral, then the camps its mission
        script lists (rusemod.missions: each camp's number as a spawn saves it, whether a human player plays it, its
        country and its team), by number; the game's rule is that a later camp with the same number takes it. A
        scenario with no script to read (a BATTLES map's: those spawn only neutral items) gets plain camps 0 to 8,
        none called a player."""
        neutral = {"camp": scenario.NEUTRAL, "kind": "neutral"}
        try:
            found = missions.scenario_camps(ia, pack, file) if ia is not None else []
        except (KeyError, ValueError, struct.error, zlib.error):  # (ScriptError is a ValueError)
            found = []
        if not found:
            return [neutral, *({"camp": n, "kind": "camp"} for n in range(9))]
        by_key = {}
        for c in found:
            by_key[c.key] = {"camp": c.key, "kind": "player" if c.player else "ai",
                             "nation": missions.NATIONS.get(c.nation), "team": c.alliance}
        return [neutral, *(by_key[k] for k in sorted(by_key))]

    def _with_units(self, view: dict) -> dict:
        """Each spawn told what it is, for the map view's icons and labels: "unit_kind" (ground, infantry, air,
        buildings), "group" (what it's for: group_of), "nation" (Nationalite) and "unit" (its address), from its
        Python class name (`what`: the units' ClassNameForDebug). A class the game data hasn't got (a new unit of a
        mod) stays without them; a supply depot's slab (DalleBatimentDepot) is told it's a depot."""
        if getattr(self, "_by_class", None) is None:
            by_class = {}
            try:
                ix = self._open()
            except (StudioError, OSError):
                return view
            try:
                marks = ",".join("?" * len(ALL_CLASSES))
                rows = ix.db.execute(f"""SELECT o.address, o.class, v.text FROM value v JOIN object o ON o.id = v.object
                                         WHERE v.path = 'ClassNameForDebug' AND o.class IN ({marks}) AND o.shadow = 0
                                         AND o.export IS NOT NULL""", list(ALL_CLASSES)).fetchall()
                units = {u["address"]: u for u in self._all_units(ix)}
            finally:
                ix.close()
            for address, cls, name in rows:
                if name:
                    u = units.get(address, {})
                    kind = KIND_OF.get(cls, "")
                    group = group_of(kind, address, u.get("factory")) if kind else ""
                    icon, decoy = icon_of(kind, address, group) if kind else ("unit", False)
                    by_class.setdefault(name, {"unit": address, "unit_kind": kind, "nation": u.get("nation", 0),
                                               # what it's for (HQ, depot, factory, armor, airfield...) and its icon
                                               "group": group, "icon": icon, "decoy": decoy})
            self._by_class = by_class
        for s in view.get("scenarios", []):
            for it in s.get("items", []):
                if it.get("kind") == "Spawn" and it.get("what") in self._by_class:
                    it.update(self._by_class[it["what"]])
                elif it.get("kind") == "Spawn" and it.get("what") == "DalleBatimentDepot":
                    it.update(unit_kind="buildings", group="depot", icon="depot")  # the map's supply depot slabs
        return view

    def _with_scenario_edits(self, pack: str, base: dict) -> dict:
        """The map's scenarios as the current mod leaves them (a copy; the cached ones stay the game's). Items it takes
        out are marked `gone` (the map view shows them faded, to put back)."""
        moves, starts, spawns, removes = self._read_scenario_tables(pack)
        whole = self._read_scenario_sectors(pack)
        whole = whole is not None and whole.whole_map
        if not moves and not spawns and not starts and not removes and not whole:
            return base
        out = []
        for s in base["scenarios"]:
            s = {**s, "items": [dict(it) for it in s["items"]]}
            if whole and s.get("zones"):  # sectors over the whole map: drawn as the build will make them
                zones, why = self._whole_map_zones(pack, s["file"])
                if zones is not None:
                    s["zones"], s["sectors_whole"] = zones, True
                else:
                    s["sectors_note"] = why
            for r in removes:
                if r.file.lower() == s["file"].lower() and r.item < len(s["items"]):
                    s["items"][r.item]["gone"] = True
            for m in moves:
                if m.file.lower() == s["file"].lower() and m.item < len(s["items"]):
                    it = s["items"][m.item]
                    if it.get("cam"):  # the build carries a start's warm-up camera path by the same offset
                        it["cam"] = _turned_cam(_shifted_cam(it["cam"], m.x - it["x"], m.y - it["y"]), m.x, m.y,
                                                m.camera or 0.0)
                    it.update(x=m.x, y=m.y, moved=(m.x, m.y) != (it["x"], it["y"]) or it.get("moved", False),
                              camera=m.camera or 0.0)
            places: dict = {}
            shipped = [it for it in s["items"] if it["kind"] == "StartingPoint"]
            for it in shipped:
                if it.get("alliance") is not None:
                    places.setdefault(it["alliance"], set()).add(it.get("place") or 1)
            for n, st in enumerate(starts):
                if st.file.lower() == s["file"].lower():
                    place = st.place or max(places.get(st.team, {0}), default=0) + 1
                    places.setdefault(st.team, set()).add(place)
                    new = {"kind": "StartingPoint", "x": st.x, "y": st.y, "turn": st.rotation or 0.0, "name": "",
                           "alliance": st.team, "place": place, "mine": True, "start": n, "item": len(s["items"])}
                    # its camera as the build makes it: a copy of the warm-up path of the start it copies (a
                    # teammate's, the highest place; else the nearest start's), moved by the same offset
                    mine = [it for it in shipped if it.get("alliance") == st.team]
                    model = (max(mine, key=lambda it: it.get("place") or 1) if mine else
                             min(shipped, key=lambda it: (it["x"] - st.x) ** 2 + (it["y"] - st.y) ** 2) if shipped
                             else None)
                    if model is not None and model.get("cam"):
                        new["cam"] = _turned_cam(_shifted_cam(model["cam"], st.x - model["x"], st.y - model["y"]),
                                                 st.x, st.y, st.camera or 0.0)
                    new["camera"] = st.camera or 0.0
                    s["items"].append(new)
            for n, sp in enumerate(spawns):
                if sp.file.lower() == s["file"].lower():
                    s["items"].append({"kind": "Spawn", "x": sp.x, "y": sp.y, "turn": sp.rotation, "name": "",
                                       "camp": sp.camp, "what": sp.what, "mine": True, "spawn": n,
                                       "item": len(s["items"])})
            out.append(s)
        return {"scenarios": out, "sectors_whole": whole}

    @property
    def cache_dir(self) -> Path:
        """Made files the window loads by address (served as `cache/...` by the window's own server)."""
        return self._home / "cache"

    def map_ground(self, pack: str) -> dict:
        """The map's real ground textures as one picture, made once per map pack (about half a minute) and kept in
        the cache: {"url": "cache/ground/..."} when it's there, else {"job": id}; ask again when the job is done."""
        pack = self._game_pack(pack)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        path = find_pack(game, pack_file(pack))
        if path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{pack_file(pack)} isn't in the game folder.")
        st = path.stat()
        name = f"{pack}-{st.st_size}-{int(st.st_mtime)}.png"  # a new game build makes a new picture
        out = self.cache_dir / "ground" / name
        if out.is_file():
            return {"url": f"cache/ground/{name}"}
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id
        return job.start(lambda say: ground_png(game, pack, out, progress=lambda d, n: say(f"{d}/{n}")),
                         "The ground textures are ready.")

    def map_models(self, pack: str) -> dict:
        """The real 3D models of the map's scenery (rusemod.models, from DomesticNukes and his Claude's .spk notes),
        made once per map and game build (about ten seconds) and kept in the cache: {"base": "cache/models/.../",
        "index": {...}} when they're there, else {"job": id}; ask again when the job is done. The index's type
        numbers are map_scenery's."""
        from rusemod import models
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        types = self.map_scenery(pack)["types"]
        zz = find_pack(game, "ZZ_Win.dat")
        st = zz.stat()
        folder = f"{st.st_size}-{int(st.st_mtime)}"  # a new game build makes new models
        out = self.cache_dir / "models" / folder
        name = f"models:{folder}:{pack}"
        done = self._models_done.get(name)
        if done is not None:
            return {"base": f"cache/models/{folder}/", "index": done}
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id

        def work(say):
            self._models_done[name] = models.map_models(game, types, out, say=say)

        return job.start(work, "The 3D models are ready.")

    # --- a map's scenarios, edited: maps/<pack>/scenario.toml in the current mod (MOD_FORMAT §8, rusemod.scenario):
    # starting points and other items moved, units and buildings spawned ---
    SCENARIO_HEADER = ("The starting points and other items this mod moves on this map's scenarios, and the units and "
                       "buildings it spawns (docs/MOD_FORMAT.md §8).\nMade in the RUSE Studio, which rewrites this file.")

    def _scenario_file(self, pack: str) -> Path:
        folder = self._map_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: scenario changes are saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "scenario.toml"

    def _read_scenario_edits(self, pack: str) -> tuple[list, list]:
        """(moves, spawns) the current mod makes on this map's scenarios; none without a mod."""
        moves, _starts, spawns = self._read_scenario_all(pack)
        return moves, spawns

    def _read_scenario_all(self, pack: str) -> tuple[list, list, list]:
        """(moves, new starting points, spawns) the current mod makes on this map's scenarios; none without a mod."""
        return self._read_scenario_tables(pack)[:3]

    def _read_scenario_removes(self, pack: str) -> list:
        """The map's own design items the current mod takes out (scenario.Remove); none without a mod."""
        return self._read_scenario_tables(pack)[3]

    def _read_scenario_tables(self, pack: str) -> tuple[list, list, list, list]:
        """(moves, new starting points, spawns, removes) of the current mod's scenario.toml for this map."""
        data, path = self._scenario_data(pack)
        if data is None:
            return [], [], [], []
        try:
            return _scenario_tables(data, str(path))
        except scenario.ScenarioError as exc:
            raise StudioError(f"{path} has a mistake ({exc}). The mod check at the top can set it aside, or fix it "
                              f"by hand.") from None

    def _read_scenario_sectors(self, pack: str):
        """The current mod's [sectors] setting for this map (rusemod.sectors.Sectors), or None."""
        from rusemod.sectors import SectorError
        data, path = self._scenario_data(pack)
        if data is None:
            return None
        try:
            return _scenario_sectors(data, str(path))
        except SectorError as exc:
            raise StudioError(f"{path} has a mistake ({exc}). The mod check at the top can set it aside, or fix it "
                              f"by hand.") from None

    def _scenario_data(self, pack: str) -> tuple[dict | None, Path | None]:
        """The current mod's scenario.toml for this map, read (None without a mod or the file)."""
        if self._map_dir() is None:
            return None, None
        path = self._scenario_file(pack)
        if not path.is_file():
            return None, path
        try:
            return tomllib.loads(path.read_text(encoding="utf-8")), path
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise StudioError(f"{path} has a mistake ({exc}). The mod check at the top can set it aside, or fix it "
                              f"by hand.") from None

    def _write_scenario_edits(self, pack: str, moves: list, spawns: list, starts: list | None = None,
                              removes: list | None = None, sectors=_KEEP) -> Path:
        """Write the mod's scenario edits; `starts` / `removes` None keep the file's own new starting points / the
        map's items it takes out, and its sectors' setting is kept unless `sectors` is given."""
        path = self._scenario_file(pack)
        if starts is None or removes is None:
            _m, own_starts, _s, own_removes = self._read_scenario_tables(pack)
            starts = own_starts if starts is None else starts
            removes = own_removes if removes is None else removes
        if sectors is _KEEP:
            sectors = self._read_scenario_sectors(pack)
        if moves or spawns or starts or removes or (sectors is not None and sectors.whole_map):
            _save_checked(path, _scenario_toml(moves, starts, spawns, removes, self.SCENARIO_HEADER, sectors),
                          _scenario_checked(str(path)))
        elif path.is_file():
            path.unlink()
        return path

    def _base_scenario(self, pack: str, file: str) -> dict:
        found = next((s for s in self.map_scenarios(pack, edited=False)["scenarios"] if s["file"].lower() == file.lower()), None)
        if found is None:
            raise StudioError(f"{pack} has no scenario {file}")
        return found

    def scenario_move(self, pack: str, file: str, item: int, x: float, y: float) -> dict:
        """Put design item `item` of scenario `file` at x, y in the current mod (a second move of it replaces the
        first). Returns the map's scenarios as the mod leaves them."""
        base = self._base_scenario(pack, file)
        if not 0 <= int(item) < len(base["items"]):
            raise StudioError(f"{file} has no item {item}")
        kind = base["items"][int(item)]["kind"]
        if kind not in scenario.KINDS_MOVABLE:
            raise StudioError(f"a {kind or 'plain item'} can't be moved")
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            old = next((m for m in moves if m.file.lower() == file.lower() and m.item == int(item)), None)
            moves = [m for m in moves if m is not old]
            moves.append(scenario.Move(file, int(item), kind, float(x), float(y),
                                       camera=old.camera if old is not None else None))
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_turn_camera(self, pack: str, file: str, item: int, turn: float) -> dict:
        """Turn the warm-up camera of starting point `item` of scenario `file` `turn` radians about it (from where the
        game has it; 0 puts it back), LittleGroove's camera ring. Kept with the start's move in the mod (a start
        not moved gets a move to where it stands)."""
        base = self._base_scenario(pack, file)
        if not 0 <= int(item) < len(base["items"]) or base["items"][int(item)]["kind"] != "StartingPoint":
            raise StudioError(f"{file} has no starting point {item}")
        if not math.isfinite(float(turn)):
            raise StudioError("the camera's turn must be a number")
        it = base["items"][int(item)]
        turn = math.remainder(float(turn), math.tau) or None
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            old = next((m for m in moves if m.file.lower() == file.lower() and m.item == int(item)), None)
            moves = [m for m in moves if m is not old]
            if old is None:
                old = scenario.Move(file, int(item), "StartingPoint", float(it["x"]), float(it["y"]))
            if turn is not None or (old.x, old.y) != (it["x"], it["y"]):
                moves.append(replace(old, camera=turn))
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_turn_start_camera(self, pack: str, number: int, turn: float) -> dict:
        """Turn the warm-up camera of the current mod's new starting point number `number` `turn` radians about it."""
        if not math.isfinite(float(turn)):
            raise StudioError("the camera's turn must be a number")
        with self._saving:
            moves, starts, spawns = self._read_scenario_all(pack)
            if not 0 <= int(number) < len(starts):
                raise StudioError("that starting point isn't in the mod any more")
            starts[int(number)] = replace(starts[int(number)], camera=math.remainder(float(turn), math.tau) or None)
            self._write_scenario_edits(pack, moves, spawns, starts)
        return self.map_scenarios(pack)

    def scenario_put_back(self, pack: str, file: str, item: int) -> dict:
        """Undo the current mod's move of item `item`, or its taking it out (it's back where the game has it)."""
        with self._saving:
            moves, starts, spawns, removes = self._read_scenario_tables(pack)
            moves = [m for m in moves if not (m.file.lower() == file.lower() and m.item == int(item))]
            removes = [r for r in removes if not (r.file.lower() == file.lower() and r.item == int(item))]
            self._write_scenario_edits(pack, moves, spawns, starts, removes)
        return self.map_scenarios(pack)

    def scenario_remove(self, pack: str, file: str, items) -> dict:
        """Take the map's own design items `items` (a number, or a list of them) of scenario `file` out in the current
        mod: the game leaves them out (scenario.Remove; LittleGroove's way, seen in the game 2026-10-05). A starting point
        can only be moved. A move of an item taken out goes with it. Returns the map's scenarios as the mod leaves
        them."""
        base = self._base_scenario(pack, file)
        numbers = sorted({int(i) for i in (items if isinstance(items, (list, tuple)) else [items])})
        for i in numbers:
            if not 0 <= i < len(base["items"]):
                raise StudioError(f"{file} has no item {i}")
            kind = base["items"][i]["kind"]
            if kind == "StartingPoint":
                # rule: seats-per-team
                raise StudioError("A starting point can't be taken out: every player needs one. Move it instead.")
            if kind not in scenario.KINDS_REMOVABLE:
                raise StudioError(f"a {kind or 'plain item'} can't be taken out")
        with self._saving:
            moves, starts, spawns, removes = self._read_scenario_tables(pack)
            taken = {(r.file.lower(), r.item) for r in removes}
            removes += [scenario.Remove(file, i, base["items"][i]["kind"]) for i in numbers
                        if (file.lower(), i) not in taken]
            moves = [m for m in moves if not (m.file.lower() == file.lower() and m.item in numbers)]
            self._write_scenario_edits(pack, moves, spawns, starts, removes)
        return self.map_scenarios(pack)

    def scenario_sectors(self, pack: str, whole_map: bool) -> dict:
        """Sectors over the whole map on (every scenario of the map: each place its sectors leave out goes to the
        sector nearest it, rusemod.sectors) or off, in the current mod. Returns the map's scenarios, drawn with the
        sectors as the build will make them."""
        from rusemod.sectors import Sectors
        if self._map_dir() is None:
            raise StudioError("Pick or make a mod first: scenario changes are saved in it.")
        with self._saving:
            moves, starts, spawns, removes = self._read_scenario_tables(pack)
            self._write_scenario_edits(pack, moves, spawns, starts, removes, Sectors(bool(whole_map)))
        return self.map_scenarios(pack)

    PREVIEW_CELLS = 1024  # the map view's sectors over the whole map: a coarser grid than the build's (quicker)

    def _whole_map_zones(self, pack: str, file: str):
        """Scenario `file`'s sectors over the whole map as the map view draws zones (the build's way on a coarser
        grid), or (None, why) when they can't be made. Worked out once per scenario."""
        from rusemod import sectors
        from rusemod.cover import member as movement_member
        game = self._game()
        shipped = self._game_pack(pack)
        path = find_pack(game, scenario.PACK) if game is not None else None
        if path is None:
            return None, "the game's scenarios aren't found"
        key = ("whole-map-sectors", str(path), path.stat().st_mtime, shipped.lower(), file.lower())
        with self._grounds_lock:
            hit = self._sceneries.get(key)
        if hit is not None:
            return hit
        folder = scenario.folder_of(shipped)
        stem = file[:-len(".scenario")] if file.lower().endswith(".scenario") else file
        try:
            with Edat.open(str(path)) as arc:
                s = scenario.Scenario.read(bytes(arc.read(arc.find(folder + file))))
                kdt = arc.entry(f"{folder}zonebluff\\{stem}.kdt")
                if kdt is None:
                    out = (None, "it has no zone map: its sectors stay as they are")
                else:
                    width, height = sectors.map_size(bytes(arc.read(arc.find(movement_member(shipped)))))
                    res = sectors.over_whole_map(s, bytes(arc.read(kdt)), width, height, None, self.PREVIEW_CELLS)
                    s.zones = res.zones
                    out = (scenario.view(s)["zones"], "")
        except (KeyError, ValueError, struct.error) as exc:   # (SectorError and ScenarioError are ValueErrors)
            out = (None, str(exc))
        with self._grounds_lock:
            self._sceneries[key] = out
        return out

    def scenario_spawn(self, pack: str, file: str, unit: str, x: float, y: float, camp: int | None = scenario.NEUTRAL,
                       rotation: float = 0.0) -> dict:
        """Spawn a unit or building (`unit`: its address, as the unit list gives it) when scenario `file` starts, at
        x, y, for side `camp` (-1: neutral, the only side a skirmish game spawns). Returns the map's scenarios as
        the mod leaves them."""
        return self.scenario_spawn_many(pack, file, unit, [[x, y]], camp, rotation)

    SPAWN_MOST = 50  # units one click may add (a formation)

    def scenario_spawn_many(self, pack: str, file: str, unit: str, points: list, camp: int | None = scenario.NEUTRAL,
                            rotation: float = 0.0) -> dict:
        """Spawn `unit` at each [x, y] of `points` (a formation, up to SPAWN_MOST) when scenario `file` starts, for
        side `camp` (-1: neutral; a skirmish scenario takes only that), all turned `rotation` radians; saved in one
        go. Returns the map's scenarios."""
        try:
            where = [(float(x), float(y)) for x, y in points]
        except (TypeError, ValueError):
            raise StudioError("the places to spawn at must be pairs of numbers") from None
        if not 1 <= len(where) <= self.SPAWN_MOST or not all(map(math.isfinite, (v for p in where for v in p))):
            raise StudioError(f"a spawn takes 1 to {self.SPAWN_MOST} places, each two finite numbers")
        camp = scenario.NEUTRAL if camp is None else int(camp)
        if self._base_scenario(pack, file)["kind"] == "skirmish" and camp != scenario.NEUTRAL:
            # rule: skirmish-neutral-spawns
            raise StudioError(f"{file} is a skirmish map's scenario: a skirmish game spawns only neutral items, so a "
                              f"unit for side {camp} would never appear. Pick Neutral, or an Operation's scenario.")
        if unit == DEPOT_SLAB:  # a map's supply depot spot: not a unit of the list, written as the shipped ones are
            name = DEPOT_SLAB
        else:
            ix = self._open()
            try:
                try:
                    o = ix.show(unit)
                except KeyError:
                    raise StudioError(f"There's no unit at {unit}.") from None
                name = next((t for p, _n, t in o["values"] if p == "ClassNameForDebug" and t), None)
            finally:
                ix.close()
        if not name:
            # not a game rule: a spawn needs a class name to be written
            raise StudioError(f"{_tail(unit)} has no class name for the game's scripts, so it can't be spawned")
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            spawns += [scenario.Spawn(file, name, x, y, camp, float(rotation)) for x, y in where]
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_move_spawn(self, pack: str, number: int, x: float, y: float) -> dict:
        """Put the current mod's spawn number `number` at x, y."""
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            if not 0 <= int(number) < len(spawns):
                raise StudioError("that spawn isn't in the mod any more")
            spawns[int(number)] = replace(spawns[int(number)], x=float(x), y=float(y))
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_remove_spawn(self, pack: str, number: int) -> dict:
        """Take back the current mod's spawn number `number` (its place among the mod's spawns on this map)."""
        with self._saving:
            moves, spawns = self._read_scenario_edits(pack)
            if not 0 <= int(number) < len(spawns):
                raise StudioError("that spawn isn't in the mod any more")
            del spawns[int(number)]
            self._write_scenario_edits(pack, moves, spawns)
        return self.map_scenarios(pack)

    def scenario_add_start(self, pack: str, file: str, team: int, x: float, y: float) -> dict:
        """A new starting point in scenario `file` for `team` (1-8), at the team's next place, at x, y: more players
        on a map need one each (PLAN A10). Returns the map's scenarios as the mod leaves them."""
        if isinstance(team, bool) or not 1 <= int(team) <= 8 or not all(map(math.isfinite, (float(x), float(y)))):
            raise StudioError("a starting point needs a team from 1 to 8 and a place on the map")
        self._base_scenario(pack, file)
        with self._saving:
            moves, starts, spawns = self._read_scenario_all(pack)
            starts.append(scenario.Start(file, int(team), float(x), float(y)))
            self._write_scenario_edits(pack, moves, spawns, starts)
        return self.map_scenarios(pack)

    def scenario_move_start(self, pack: str, number: int, x: float, y: float) -> dict:
        """Put the current mod's new starting point number `number` at x, y."""
        with self._saving:
            moves, starts, spawns = self._read_scenario_all(pack)
            if not 0 <= int(number) < len(starts):
                raise StudioError("that starting point isn't in the mod any more")
            starts[int(number)] = replace(starts[int(number)], x=float(x), y=float(y))
            self._write_scenario_edits(pack, moves, spawns, starts)
        return self.map_scenarios(pack)

    def scenario_remove_start(self, pack: str, number: int) -> dict:
        """Take back the current mod's new starting point number `number`."""
        with self._saving:
            moves, starts, spawns = self._read_scenario_all(pack)
            if not 0 <= int(number) < len(starts):
                raise StudioError("that starting point isn't in the mod any more")
            del starts[int(number)]
            self._write_scenario_edits(pack, moves, spawns, starts)
        return self.map_scenarios(pack)

    # --- how many players a map takes: maps/<pack>/map.toml in the current mod (MOD_FORMAT §8, rusemod.players) ---
    MAP_HEADER = ("How many players this map takes in this mod (docs/MOD_FORMAT.md §8).\nMade in the RUSE Studio, "
                  "which rewrites this file.")

    def _map_file(self, pack: str) -> Path:
        return self._scenario_file(pack).with_name("map.toml")

    def map_players(self, pack: str) -> dict:
        """The map's online entries and how many players each takes: {"entries": [{"name", "players", "layouts",
        "file"}], "mod": the mod's count or None, "entry": the entry it sets, "missing": the starting points the
        mod's count still needs ([team, place] pairs), "most": 8}. No entries: the map isn't played online."""
        from rusemod import newmap
        from rusemod import players as pl
        from rusemod.ndf import Ndf
        game = self._game()
        glad_path = find_pack(game, "ZZ_GladPatchableWin.dat") if game is not None else None
        if glad_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("ZZ_GladPatchableWin.dat isn't in the game folder.")
        with Edat.open(str(glad_path)) as glad:
            def read(member):
                e = glad.entry(member)
                return bytes(glad.read(e)) if e is not None else None
            g, m = Ndf(read(pl.GLOBALS)), Ndf(read(pl.MAPINFO))
            found = []
            copy = self._new_maps().get(pack.lower())  # a new map has the one BATTLES entry it copies
            for mi, gi, name in pl.entries(m, g, copy[1].copy_of if copy else pack):
                if copy and not (newmap._listed(g, gi) and copy[1].entry in (None, name)):
                    continue
                p = {g.prop_name(pi): v for pi, v in g.objects[gi].props}
                layouts = [t for key, t in pl.LAYOUTS if key in p and p[key].scalar()]
                found.append({"name": name, "players": p["NbPlayers"].scalar() if "NbPlayers" in p else None,
                              "layouts": layouts, "file": pl.scenario_of(m, mi, read)})
        setting = self._read_players(pack)
        out = {"entries": found, "mod": setting.count if setting else None, "entry": setting.entry if setting else None,
               "missing": [], "most": pl.PLAYERS_MOST}
        target = next((e for e in found if setting and (setting.entry is None or e["name"] == setting.entry)), None)
        if setting and target and target["file"]:
            sizes: dict = {}  # starting points per team: the game seats a team on them whatever their places
            s = next((x for x in self.map_scenarios(pack)["scenarios"] if x["file"].lower() == target["file"]), None)
            for it in (s["items"] if s else []):
                if it["kind"] == "StartingPoint" and it.get("alliance") is not None:
                    sizes[int(it["alliance"])] = sizes.get(int(it["alliance"]), 0) + 1
            out["missing"] = [list(pair) for pair in pl.seats(sizes, target["layouts"], setting.count)]
        return out

    def _read_players(self, pack: str):
        from rusemod import players as pl
        if self._map_dir() is None:
            return None
        path = self._map_file(pack)
        if not path.is_file():
            return None
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            if "copy_of" in data and "players" not in data:
                return None  # a new map's file: its entry is the one it copies, not a player count's
            got = pl.parse_map(data, str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, pl.PlayersError) as exc:
            raise StudioError(f"{path} has a mistake ({exc}). The mod check at the top can set it aside, or fix it "
                              f"by hand.") from None
        return got[0] if got else None

    def set_players(self, pack: str, count: int | None, entry: str | None = None) -> dict:
        """Set how many players the map takes in the current mod (None: as the game has it). Returns map_players."""
        from rusemod import players as pl
        path = self._map_file(pack)
        copy = self._new_maps().get(pack.lower())
        if copy is not None:  # a new map's file says what it copies too: it's rewritten, never removed
            from rusemod import newmap
            spec = replace(copy[1], entry=entry or copy[1].entry)
            if count is not None:
                pl.parse_map({"players": int(count)}, "the count")  # (refuses a count the lobby can't seat)
            text = newmap.map_toml(spec, None if count is None else int(count),
                                   f"A new map: a copy of {spec.copy_of} called {spec.names['us']!r} in the menus "
                                   "(MOD_FORMAT §8).\nMade in the RUSE Studio, which rewrites this file.")
            with self._saving:
                _save_checked(path, text, lambda data: newmap.parse(data, str(path), copy[0]))
            return self.map_players(pack)
        with self._saving:
            if count is None:
                if path.is_file():
                    path.unlink()
            else:
                setting = pl.parse_map({"players": int(count), **({"entry": entry} if entry else {})}, "the count")[0]
                _save_checked(path, pl.map_toml(setting, self.MAP_HEADER),
                              lambda data: pl.parse_map(data, str(path)))
        return self.map_players(pack)

    # --- placing objects on a map: maps/<pack>/scenery.toml in the current mod (MOD_FORMAT §8, rusemod.scenery) ---
    SCENERY_HEADER = ("The objects this mod adds to this map, in order, and the circles where it takes the map's own "
                      "away ([[erase]]; docs/MOD_FORMAT.md §8).\nMade in the RUSE Studio, which rewrites this file.")

    def _scenery_file(self, pack: str) -> Path:
        folder = self._map_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: what you place is saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "scenery.toml"

    @staticmethod
    def _read_objects(path: Path, table: str = "object") -> list:
        """The file's objects, or with `table` "erase" its erase areas (kept as they are when the Studio rewrites it)."""
        if not path.is_file():
            return []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            parse = scenery.parse_erase if table == "erase" else scenery.parse_objects
            return parse(data.get(table, []), str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, scenery.SceneryEditError) as exc:
            raise StudioError(f"{path} can't be read ({exc}). The mod check at the top can set it aside, or fix it by "
                              f"hand: the Studio won't write over it.") from None

    def _write_objects(self, path: Path, objects: list, erase: list | None = None) -> None:
        """The file with `objects` and `erase` (default: its erase areas as they are); gone when both are empty."""
        if erase is None:
            erase = self._read_objects(path, "erase")
        if objects or erase:
            _save_checked(path, scenery.objects_toml(objects, self.SCENERY_HEADER, erase),
                          lambda data: (scenery.parse_objects(data.get("object", []), str(path))
                                        + scenery.parse_erase(data.get("erase", []), str(path))))
            return
        if path.is_file():
            path.unlink()
        for folder in (path.parent, path.parent.parent):
            try:
                folder.rmdir()
            except OSError:
                break

    def scenery(self, pack: str) -> dict:
        """The objects the current mod places on a map and its circles to erase: {"objects": [{type, x, y, turn,
        size}], "erase": [{x, y, radius, what, types}], "saved": the file or None, "mod": the mod or None}."""
        folder = self._map_dir()
        if folder is None:
            return {"objects": [], "erase": [], "saved": None, "mod": None}
        path = self._scenery_file(pack)
        with self._saving:
            objects = self._read_objects(path)
            erase = self._read_objects(path, "erase")
        return {"objects": [asdict(o) for o in objects], "erase": [_erase_dict(a) for a in erase],
                "saved": str(path) if objects or erase else None, "mod": str(folder)}

    def scenery_erase(self, pack: str, areas: list) -> dict:
        """The Erase tool's circles (dicts: x, y, radius, and what: the groups it takes, default trees and props),
        saved after the ones already there as the scenery file's [[erase]] tables, its objects kept: the map's own
        scenery in them is taken off when the mod is built. Returns {"count": circles on the map now, "saved": the
        file}."""
        path = self._scenery_file(pack)
        if not isinstance(areas, list) or not areas or not all(isinstance(a, dict) for a in areas):
            raise StudioError("the circles to erase must be a list of tables (x, y, radius)")
        try:
            new = scenery.parse_erase(areas, "the circles to erase")
        except scenery.SceneryEditError as exc:
            raise StudioError(str(exc)) from None
        with self._saving:
            every = self._read_objects(path, "erase") + new
            self._write_objects(path, self._read_objects(path), every)
        return {"count": len(every), "saved": str(path)}

    def scenery_erase_undo(self, pack: str, count: int = 1) -> dict:
        """Take the last `count` circles to erase off the map (the file's objects stay). Returns {"count": left,
        "removed": how many went, "saved": the file or None}."""
        path = self._scenery_file(pack)
        with self._saving:
            every = self._read_objects(path, "erase")
            n = max(0, min(int(count), len(every)))
            left = every[:len(every) - n]
            if n:
                self._write_objects(path, self._read_objects(path), left)
        return {"count": len(left), "removed": n, "saved": str(path) if path.is_file() else None}

    def scenery_erased(self, pack: str) -> dict:
        """What the current mod's circles to erase take off a map when the mod is built, worked out the way the build
        erases (rusemod.scenery.erase_count): {"count": circles, "takes": {group: objects}, "error": why the build
        would refuse them (the map's scenery would grow too big), or ""}. Seconds even on the biggest map erased
        whole. One count runs at a time; a newer ask stops an older one, which then answers {"superseded": true}."""
        none = {"count": 0, "takes": {}, "error": ""}
        if self._map_dir() is None:
            return none
        with self._erased_ask:
            self._erased_gen += 1
            mine = self._erased_gen
        with self._erased_lock:
            if mine != self._erased_gen:
                return {**none, "superseded": True}
            try:
                return self._count_erased(pack, lambda: mine != self._erased_gen)
            except scenery.EraseCancelled:
                return {**none, "superseded": True}

    def _count_erased(self, pack: str, cancel) -> dict:
        none = {"count": 0, "takes": {}, "error": ""}
        path = self._scenery_file(pack)
        with self._saving:
            areas = self._read_objects(path, "erase")
        if not areas:
            return none
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        src = pack_file(self._game_pack(pack))  # a new map's scenery is the map it copies
        map_path, unit_path = find_pack(game, src), find_pack(game, "ZZ_GladPatchableWin.dat")
        if map_path is None or unit_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{src if map_path is None else 'ZZ_GladPatchableWin.dat'} isn't in the game folder.")
        with Edat.open(str(unit_path)) as unit_arc, Edat.open(str(map_path)) as map_arc:
            descs = self._scenery_types(unit_path, unit_arc)
            try:
                raw = bytes(map_arc.read(map_arc.find(scenery.MEMBER)))
            except KeyError:
                raise StudioError(f"{map_path.name} has no scenery file.") from None
        out = {"count": len(areas), "takes": {}, "error": ""}
        try:
            out["takes"] = scenery.erase_count(raw, areas, descs, cancel)
        except (scenery.SceneryError, struct.error) as exc:
            raise StudioError(f"{map_path.name}: its scenery can't be read ({exc}).") from None
        except scenery.SceneryEditError as exc:
            out["error"] = str(exc)
        return out

    def scenery_add(self, pack: str, objects: list) -> dict:
        """Place objects (dicts with the scenery file's keys) after the ones already there, in the current mod. Only
        types the map already uses. Returns {"count": objects placed on the map now, "saved": the file}."""
        path = self._scenery_file(pack)
        try:
            new = scenery.parse_objects(list(objects or []), "the new objects")
        except scenery.SceneryEditError as exc:
            raise StudioError(str(exc)) from None
        known = {row[0] for row in self.map_scenery(pack)["palette"]}
        for o in new:
            if o.type not in known:
                raise StudioError(f"{o.type} isn't one of this map's own types, so the map can't take it.")
        with self._saving:
            every = self._read_objects(path) + new
            self._write_objects(path, every)
        return {"count": len(every), "saved": str(path)}

    def scenery_undo(self, pack: str, count: int = 1, objects: list | None = None) -> dict:
        """Take the last `count` placed objects off the map; or, given `objects` (dicts with the scenery file's keys),
        those objects, wherever they are in the file (for each, the last one like it): the trees of a Forest stroke,
        with other objects placed after them. Returns {"count": left, "removed": how many went, "saved": the file or
        None}."""
        path = self._scenery_file(pack)
        if objects is not None:
            try:
                gone = scenery.parse_objects(list(objects), "the objects to take off")
            except scenery.SceneryEditError as exc:
                raise StudioError(str(exc)) from None
        with self._saving:
            every = self._read_objects(path)
            if objects is None:
                n = max(0, min(int(count), len(every)))
                left = every[:len(every) - n]
            else:
                left = list(every)
                for o in reversed(gone):
                    at = next((i for i in range(len(left) - 1, -1, -1) if left[i] == o), None)
                    if at is not None:
                        del left[at]
                n = len(every) - len(left)
            self._write_objects(path, left)
        return {"count": len(left), "removed": n, "saved": str(path) if path.is_file() else None}

    # --- shaping a map's ground: maps/<pack>/terrain.toml in the current mod (MOD_FORMAT §8, rusemod.brush) ---
    # --- new roads: maps/<pack>/roads.toml in the current mod (MOD_FORMAT §8, rusemod.roadnet) ---
    ROADS_HEADER = ("The roads this mod adds to this map, as lines (docs/MOD_FORMAT.md §8).\nMade in the RUSE Studio, "
                    "which rewrites this file.")
    ROAD_POINTS_MOST = 5000   # points in one road's line

    def _roads_file(self, pack: str) -> Path:
        folder = self._map_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: new roads are saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "roads.toml"

    @staticmethod
    def _read_roads(path: Path) -> list:
        from rusemod import roadnet
        if not path.is_file():
            return []
        try:
            return roadnet.parse_roads(tomllib.loads(path.read_text(encoding="utf-8")).get("road", []), str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, roadnet.RoadNetError) as exc:
            raise StudioError(f"{path} can't be read ({exc}). The mod check at the top can set it aside, or fix it by "
                              f"hand: the Studio won't write over it.") from None

    @staticmethod
    def _read_take_out(path: Path):
        """The map's own roads and bridges the file takes out (rusemod.roadnet.TakeOut; nothing without the file)."""
        from rusemod import roadnet
        if not path.is_file():
            return roadnet.TakeOut()
        try:
            return roadnet.take_out_of(roadnet.parse_take_out(tomllib.loads(path.read_text(encoding="utf-8"))
                                                              .get("take_out"), str(path)))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, roadnet.RoadNetError) as exc:
            raise StudioError(f"{path} can't be read ({exc}). The mod check at the top can set it aside, or fix it by "
                              f"hand: the Studio won't write over it.") from None

    def _write_roads(self, path: Path, roads: list, take_out=None) -> None:
        """Write the mod's new roads; `take_out` None keeps what the file takes out of the map's own."""
        from rusemod import roadnet
        if take_out is None:
            take_out = self._read_take_out(path)
        if roads or take_out.names():
            _save_checked(path, roadnet.roads_toml(roads, self.ROADS_HEADER, take_out),
                          lambda data: (roadnet.parse_roads(data.get("road", []), str(path)),
                                        roadnet.parse_take_out(data.get("take_out"), str(path))))
            return
        if path.is_file():
            path.unlink()
        for folder in (path.parent, path.parent.parent):  # maps/<pack>, then maps, when they're empty
            try:
                folder.rmdir()
            except OSError:
                break

    def roads(self, pack: str) -> dict:
        """The roads the current mod adds to a map, for the Maps view: {"roads": [{"points": [[x, y], ...], "join":
        map units, "keep_trees": whether the trees on its path stay, "crossings": [[x0, y0, x1, y1], ...] where it
        crosses water (a bridge goes there when the map has a bridge kind)}], "bridge": the map's bridge kind or None, "saved": the file or None, "mod": the mod or None
        when none is picked}."""
        folder = self._map_dir()
        if folder is None:
            return {"roads": [], "bridge": None, "saved": None, "mod": None, "take_out": []}
        path = self._roads_file(pack)
        with self._saving:
            roads = self._read_roads(path)
            taken = self._read_take_out(path)
        water, kind = self._water(pack) if roads else (None, None)
        from rusemod.bridges import crossings
        return {"roads": [{"points": [list(p) for p in r.points], "join": r.join, "keep_trees": r.keep_trees,
                           "crossings": [list(map(round, c)) for c in crossings(water, r.points)] if water and r.bridges else []}
                          for r in roads],
                "bridge": kind, "saved": str(path) if roads or taken.names() else None, "mod": str(folder),
                "take_out": taken.names()}

    def road_take_out(self, pack: str, roads: bool, bridges: bool) -> dict:
        """Take the map's own roads (its road network, the roads drawn from high up and on the map table, its road
        stickers) and its own bridges (their models, their floors sunk under the ground) out in the current mod, or
        keep them: roads.toml take_out (rusemod.roadnet.TakeOut). The mod's own new roads stay. Returns roads(pack)."""
        from rusemod import roadnet
        if self._map_dir() is None:
            raise StudioError("Pick or make a mod first: the change is saved in it.")
        path = self._roads_file(pack)
        with self._saving:
            self._write_roads(path, self._read_roads(path), roadnet.TakeOut(bool(roads), bool(bridges)))
        return self.roads(pack)

    def map_road_graph(self, pack: str) -> dict:
        """The roads a depot or a starting point sticks to (the map view's Stick to roads): {"nodes": [[x, y], ...],
        "edges": [[a, b], ...]}: the map's road network (mapinfo.win's first buffer, the one supply routes use), and the
        current mod's new roads as more edges. The offsets a depot and an HQ keep from these lines are LittleGroove's,
        measured on every shipped scenario (RUSE-Mod-Manager map_editor.py _ROAD_SNAP_OFFSET: depot 11,696 over 1,554
        placements, HQ 13,580 over 353)."""
        from ruse_mod_engine import sdb
        from rusemod.cover import member
        from rusemod.roadnet import RoadNet
        game = self._game()
        path = find_pack(game, scenario.PACK) if game is not None else None
        if path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{scenario.PACK} isn't in the game folder.")
        src = self._game_pack(pack)  # a new map's road network is the map it copies
        key = ("roadgraph", str(path), path.stat().st_mtime, src.lower())
        with self._grounds_lock:
            cached = self._sceneries.get(key)
        if cached is None:
            with Edat.open(str(path)) as arc:
                try:
                    raw = bytes(arc.read(arc.find(member(src))))
                except KeyError:
                    raise StudioError(f"{src} has no movement and road file (mapinfo.win)") from None
            try:
                net = RoadNet.read(sdb.split_mapinfo(raw)[1][0])
            except (ValueError, IndexError, struct.error) as exc:
                raise StudioError(f"{src}: its road network can't be read ({exc})") from None
            cached = {"nodes": [[round(p[0], 1), round(p[1], 1)] for p in net.points],
                      "edges": [[a, b] for a, b, _cost in net.links]}
            with self._grounds_lock:
                self._sceneries[key] = cached
        nodes, edges = list(cached["nodes"]), list(cached["edges"])
        try:
            mine = self._read_roads(self._roads_file(pack)) if self._map_dir() is not None else []
        except StudioError:
            mine = []
        for r in mine:
            first = len(nodes)
            nodes += [[round(x, 1), round(y, 1)] for x, y in r.points]
            edges += [[first + k, first + k + 1] for k in range(len(r.points) - 1)]
        return {"nodes": nodes, "edges": edges, "offset": {"depot": 11696.0, "hq": 13580.0}}

    def _water(self, pack: str) -> tuple:
        """(where a map has water, as rusemod.bridges.Water; its bridge kind or None), kept per map."""
        from rusemod.bridges import Water, bridge_type
        from rusemod.tms import Tms
        pack = self._game_pack(pack)
        game = self._game()
        map_path = find_pack(game, pack_file(pack)) if game is not None else None
        if map_path is None:
            return None, None
        key = ("water", str(map_path), map_path.stat().st_mtime)
        with self._grounds_lock:
            if key in self._sceneries:
                return self._sceneries[key]
        unit_path = find_pack(game, "ZZ_GladPatchableWin.dat")
        with Edat.open(str(map_path)) as map_arc:
            try:
                water = Water(Tms(bytes(map_arc.read(map_arc.find("output\\highdef.tms")))))
                sc = scenery.Scenery(bytes(map_arc.read(map_arc.find(scenery.MEMBER))))
            except (KeyError, ValueError, struct.error) as exc:
                raise StudioError(f"{map_path.name}: its ground can't be read ({exc}).") from None
        kind = None
        if unit_path is not None:
            with Edat.open(str(unit_path)) as unit_arc:
                dkey = (str(unit_path), unit_path.stat().st_mtime)
                if self._descriptors[0] != dkey:
                    self._descriptors = (dkey, scenery.descriptors(unit_arc))
            kind = bridge_type(sc.names, sc.types(), self._descriptors[1])
        out = (water, kind)
        with self._grounds_lock:
            self._sceneries[key] = out
            while len(self._sceneries) > self.MAP_DATA_KEPT:
                self._sceneries.pop(next(iter(self._sceneries)))
        return out

    # --- "Check this map" (rusemod.mapcheck) ---
    def map_check(self, pack: str) -> dict:
        """What would go wrong on the map `pack` with the current mod, found before the game starts: the mod built as
        Test in game builds it (its changes to this map only) into a folder removed afterwards, and the built map
        checked (rusemod.mapcheck.check_map), in the background. Returns {'job': id}, the one already running for this
        map if there is one; follow it with job(id). Its result, once done: {"pack", "findings"} (mapcheck's findings,
        their "say" a word in words.toml filled with their "data"; one "ok" finding when nothing was found)."""
        from rusemod import mapcheck
        folder = self._map_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: the check builds it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there's no map to check.")
        if self._restoring():  # the build would take half-restored files (rusemod.backup)
            # not a game rule: something else is busy (the game, the other app, a restore)
            raise StudioError("The game's files are being restored: wait for it to finish.")
        with self._grounds_lock:
            running = self._check_jobs.get(pack)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            job.result = None
            self._jobs[job.id] = job
            self._check_jobs[pack] = job.id

        def work(say):
            job.result = {"pack": pack, "findings": mapcheck.check_map(game, folder, pack, say)}
        return job.start(self._reading_game(game, work), "The map is checked.",
                         plain=(BuildError, RndfError, OSError))

    # --- the Bridges dock: the map's own bridge kinds, and bridges placed by hand (rusemod.bridges) ---
    def map_bridges(self, pack: str) -> dict:
        """The map's own bridge kinds, for the Bridges dock: {"kinds": [rusemod.bridges.kinds' dicts], "kind": the
        kind new roads' bridges are, or None when the map has none}. Kept per map (each kind's model is measured)."""
        from rusemod.bridges import kinds, model_length
        pack = self._game_pack(pack)
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no maps to show.")
        map_path, unit_path = find_pack(game, pack_file(pack)), find_pack(game, "ZZ_GladPatchableWin.dat")
        if map_path is None or unit_path is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{pack_file(pack) if map_path is None else 'ZZ_GladPatchableWin.dat'} isn't in the game "
                              f"folder.")
        key = ("bridges", str(map_path), map_path.stat().st_mtime)
        with self._grounds_lock:
            if key in self._sceneries:
                return self._sceneries[key]
        def make():
            with Edat.open(str(unit_path)) as unit_arc:
                dkey = (str(unit_path), unit_path.stat().st_mtime)
                if self._descriptors[0] != dkey:
                    self._descriptors = (dkey, scenery.descriptors(unit_arc))
            descs = self._descriptors[1]
            with Edat.open(str(map_path)) as map_arc:
                try:
                    sc = scenery.Scenery(bytes(map_arc.read(map_arc.find(scenery.MEMBER))))
                except (KeyError, scenery.SceneryError, struct.error) as exc:
                    raise StudioError(f"{map_path.name}: its scenery can't be read ({exc}).") from None
            lengths: dict = {}

            def length_of(kind):
                if kind not in lengths:
                    lengths[kind] = model_length(game, descs, kind)
                return lengths[kind]
            found = kinds(sc, descs, length_of)
            return {"kinds": found, "kind": next((k["type"] for k in found if k["roads"]), None)}
        # (the bridge models' lengths come from ZZ_Win.dat)
        zz = find_pack(game, "ZZ_Win.dat")
        out = self._kept_on_disk("bridges", pack, [map_path, unit_path] + ([zz] if zz else []), make)
        with self._grounds_lock:
            self._sceneries[key] = out
            while len(self._sceneries) > self.MAP_DATA_KEPT:
                self._sceneries.pop(next(iter(self._sceneries)))
        return out

    def bridge_add(self, pack: str, kind: str, x: float, y: float, turn: float, length: float) -> dict:
        """Place a bridge of the map's own `kind` by hand, centred on (x, y), its deck `length` map units long along
        `turn` (degrees from east toward south), sunk as the map sinks its own; saved in the mod's scenery.toml. Only a
        kind the map places (its floor is copied from one). Returns {"count": objects placed on the map now, "saved":
        the file, "object": the bridge as saved}."""
        from rusemod.bridges import BridgeError, by_hand
        path = self._scenery_file(pack)
        found = next((k for k in self.map_bridges(pack)["kinds"] if k["type"] == kind), None)
        if found is None:
            raise StudioError(f"{kind} isn't one of this map's own bridge kinds, so the map can't take it.")
        if not found["placed"]:
            raise StudioError(f"This map places no {found['name']} of its own, so there's no floor to copy for one: "
                              f"units would walk on the riverbed under it. Pick a kind the map places.")
        try:
            x, y, turn, length = (float(v) for v in (x, y, turn, length))
            if not all(math.isfinite(v) for v in (x, y, turn, length)):
                raise ValueError
            o = by_hand(kind, x, y, turn, length, found["length"], found["turn"], found["lift"])
        except BridgeError as exc:  # (a ValueError too)
            raise StudioError(str(exc)) from None
        except (TypeError, ValueError):
            raise StudioError("A bridge's place, turn and length are numbers") from None
        o = replace(o, x=round(o.x), y=round(o.y))
        with self._saving:
            every = self._read_objects(path) + [o]
            self._write_objects(path, every)
        return {"count": len(every), "saved": str(path), "object": asdict(o)}

    def road_add(self, pack: str, points: list, join: float = 3000.0, keep_trees: bool = False) -> dict:
        """Add a road (its line: [[x, y], ...] in map units, in order) to the map in the current mod. Its ends join a
        road within `join` map units (the window snaps them onto one); with `keep_trees` the trees and bushes on its
        path stay (the Roads tray's box). Returns {"count": roads on the map now, "saved": the file}."""
        from rusemod import roadnet
        path = self._roads_file(pack)
        if not isinstance(points, list) or len(points) > self.ROAD_POINTS_MOST:
            raise StudioError(f"A road's line holds 2 to {self.ROAD_POINTS_MOST} points")
        try:
            new = roadnet.parse_roads([{"points": [list(p) for p in points], "join": join,
                                        "keep_trees": keep_trees is True}], "the new road")
        except (roadnet.RoadNetError, TypeError) as exc:
            raise StudioError(str(exc)) from None
        with self._saving:
            every = self._read_roads(path) + new
            self._write_roads(path, every)
        return {"count": len(every), "saved": str(path)}

    def road_undo(self, pack: str, count: int = 1) -> dict:
        """Take the last `count` new roads off the map (the file goes when none is left). Returns {"count": roads
        left, "removed": how many went, "saved": the file or None}."""
        path = self._roads_file(pack)
        with self._saving:
            every = self._read_roads(path)
            n = max(0, min(int(count), len(every)))
            left = every[:len(every) - n]
            if n:
                self._write_roads(path, left)
        return {"count": len(left), "removed": n, "saved": str(path) if left else None}

    TERRAIN_HEADER = ("The ground this mod reshapes on this map: brush strokes, applied in order (docs/MOD_FORMAT.md "
                      "§8).\nMade in the RUSE Studio, which rewrites this file.")

    def _terrain_file(self, pack: str) -> Path:
        folder = self._map_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first: the shaped ground is saved in it.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(pack or "")):
            raise StudioError(f"{pack!r} isn't a map's pack name")
        return folder / "maps" / pack / "terrain.toml"

    @staticmethod
    def _read_strokes(path: Path) -> list:
        if not path.is_file():
            return []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            return parse_strokes(data.get("stroke", []), str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, BrushError) as exc:
            raise StudioError(f"{path} can't be read ({exc}). The mod check at the top can set it aside, or fix it by "
                              f"hand: the Studio won't write over it.") from None

    def _write_strokes(self, path: Path, strokes: list) -> None:
        if strokes:
            _save_checked(path, strokes_toml(strokes, self.TERRAIN_HEADER),
                          lambda data: parse_strokes(data.get("stroke", []), str(path)))
            return
        if path.is_file():
            path.unlink()
        for folder in (path.parent, path.parent.parent):  # maps/<pack>, then maps, when they're empty
            try:
                folder.rmdir()
            except OSError:
                break

    def terrain(self, pack: str) -> dict:
        """The strokes the current mod makes on a map's ground, for the Maps view to draw on the game's own:
        {"strokes": [{brush, x, y, radius, height, level, weight}], "saved": the file or None, "mod": the mod or
        None when none is picked}."""
        folder = self._map_dir()
        if folder is None:
            return {"strokes": [], "saved": None, "mod": None}
        path = self._terrain_file(pack)
        with self._saving:
            strokes = self._read_strokes(path)
        return {"strokes": [asdict(s) for s in strokes], "saved": str(path) if strokes else None, "mod": str(folder)}

    def terrain_add(self, pack: str, strokes: list) -> dict:
        """Add strokes (dicts with the terrain file's keys) after the ones already on the map, in the current mod.
        Returns {"count": strokes on the map now, "saved": the file}."""
        path = self._terrain_file(pack)
        try:
            new = parse_strokes(list(strokes or []), "the new strokes")
        except BrushError as exc:
            raise StudioError(str(exc)) from None
        with self._saving:
            every = self._read_strokes(path) + new
            self._write_strokes(path, every)
        return {"count": len(every), "saved": str(path)}

    def terrain_undo(self, pack: str, count: int = 1) -> dict:
        """Take the last `count` strokes off the map (the file goes when none is left). Returns {"count": strokes
        left, "removed": how many went, "saved": the file or None}."""
        path = self._terrain_file(pack)
        with self._saving:
            every = self._read_strokes(path)
            n = max(0, min(int(count), len(every)))
            left = every[:len(every) - n]
            if n:
                self._write_strokes(path, left)
        return {"count": len(left), "removed": n, "saved": str(path) if left else None}

    # --- the mod check (like a mod manager's): every file read as the build reads it, before it's too late ---
    def check_mod(self) -> dict:
        """Every file of the current mod read as the build reads it, each mistake in plain words: {"mod": its folder
        or None, "problems": [{"file": its path in the mod (None: the mod as a whole), "problem": what's wrong,
        "set_aside": whether Set aside can take the file out}]}. The window runs it when a mod is picked and
        before Test in game."""
        folder = self._mod_dir()
        if folder is None:
            return {"mod": None, "problems": []}
        return {"mod": str(folder), "problems": check_mod_folder(folder, self._game())}

    def rename_map_folder(self, name: str, to: str) -> dict:
        """Rename the current mod's maps/<name> to maps/<to> (the fix the mod check offers). Refused when maps/<to>
        already exists (the two would need merging by hand). Returns check_mod()."""
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first.")
        pattern = r"[A-Za-z0-9_]+"
        if not (re.fullmatch(pattern, str(name or "")) and re.fullmatch(pattern, str(to or ""))):
            raise StudioError("A map folder's name is letters, digits and _ only")
        source, target = folder / "maps" / name, folder / "maps" / to
        if not source.is_dir():
            raise StudioError(f"maps/{name} isn't in this mod")
        with self._saving:
            if target.exists() and target.resolve() != source.resolve():
                raise StudioError(f"maps/{to} already exists: move the files from maps/{name} into it by hand")
            source.rename(target)
        return self.check_mod()

    def set_aside(self, file: str) -> dict:
        """Take a broken map file (`file`: its path in the mod, as check_mod gives it) out of the current mod: it's
        renamed <name>.broken.toml beside it, never deleted, and the build skips it. Returns check_mod() and "kept":
        the renamed file."""
        folder = self._mod_dir()
        if folder is None:
            raise StudioError("Pick or make a mod first.")
        path = folder / str(file or "")
        if path.name not in MAP_FILES or path.parent.parent != folder / "maps" or not path.is_file():
            raise StudioError(f"{file} isn't one of this mod's map files")
        with self._saving:
            kept = _aside(path)
        return self.check_mod() | {"kept": str(kept)}

    # --- the mod being edited ---
    def _settings(self) -> dict:
        try:
            return json.loads((self._home / "studio.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self, settings: dict) -> None:
        self._home.mkdir(parents=True, exist_ok=True)
        (self._home / "studio.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

    def _mod_dir(self, kind: str = "mod") -> Path | None:
        """The folder being edited: the mod (`kind` "mod", the Units tab's) or the map (`kind` "map", the Maps
        tab's). Mods and maps are kept apart (the owner, 2026-10-02); a Studio from before kept both in the mod, so
        until a map is picked, the Maps tab goes on with the mod's maps."""
        settings = self._settings()
        path = settings.get(kind) or (settings.get("mod") if kind == "map" else None)
        return Path(path) if path and Path(path, "mod.toml").is_file() else None

    def _map_dir(self) -> Path | None:
        return self._mod_dir("map")

    def _edits(self) -> ModEdits | None:
        folder = self._mod_dir()
        if folder is None:
            return None
        with self._saving:
            return ModEdits(folder)

    KINDS = {"mod": ("mods", "recent"), "map": ("maps", "recent_maps")}  # kind: (its folder in the platform's, its list)

    def _kind(self, kind: str) -> str:
        if kind not in self.KINDS:
            raise StudioError(f"{kind!r} is neither a mod nor a map")
        return kind

    def mods(self, kind: str = "mod") -> dict:
        """The mods (`kind` "mod") or maps ("map") the Studio knows: the ones made here, and folders opened before,
        plus the one being edited. A map is a mod folder too (MOD_FORMAT §8: its maps/ files); the maps list also
        shows the mods made before mods and maps were apart that hold maps."""
        kind = self._kind(kind)
        folder_name, recent_key = self.KINDS[kind]
        found = {}
        for root in [self._home / folder_name] + ([self._home / "mods"] if kind == "map" else []):
            for f in sorted(root.iterdir()) if root.is_dir() else []:
                if (f / "mod.toml").is_file() and (kind == "mod" or root.name == "maps" or (f / "maps").is_dir()):
                    found.setdefault(str(f), f.name)
        for path in self._settings().get(recent_key, []):
            if Path(path, "mod.toml").is_file():
                found.setdefault(path, Path(path).name)
        current = self._mod_dir(kind)
        if current is not None:
            found.setdefault(str(current), current.name)
        return {"mods": [{"path": p, "name": n} for p, n in found.items()], "kind": kind,
                "current": str(current) if current else None}

    def new_mod(self, name: str, kind: str = "mod") -> dict:
        """Make a new, empty mod (or map: `kind` "map") in the platform folder and start editing it."""
        kind = self._kind(kind)
        name = name.strip()
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or ("my-map" if kind == "map" else "my-mod")
        base = self._home / self.KINDS[kind][0]
        folder, n = base / slug, 2
        while folder.exists():
            folder, n = base / f"{slug}-{n}", n + 1
        (folder / ("maps" if kind == "map" else "src")).mkdir(parents=True)
        made = "A map made in the RUSE Studio." if kind == "map" else "Made in the RUSE Studio."
        (folder / "mod.toml").write_text(
            f'[mod]\nid          = "{folder.name}"\nname        = {json.dumps(name or folder.name)}\n'
            f'version     = "0.1.0"\ndescription = "{made}"\n', encoding="utf-8")
        return self.choose_mod(str(folder), kind)

    def choose_mod(self, path: str, kind: str = "mod") -> dict:
        kind = self._kind(kind)
        if not Path(path, "mod.toml").is_file():
            raise StudioError(f"{path} isn't a mod folder (it has no mod.toml)")
        settings = self._settings()
        settings[kind] = str(path)
        recent_key = self.KINDS[kind][1]
        recent = [p for p in settings.get(recent_key, []) if p != str(path)]
        settings[recent_key] = [str(path)] + recent[:9]
        self._save_settings(settings)
        return self.mods(kind)

    def open_mod_folder(self, kind: str = "mod") -> dict:
        if self._window is None:
            return self.mods(kind)
        chosen = pick_folder(self._window)
        return self.choose_mod(chosen, kind) if chosen else self.mods(kind)

    # --- the Settings tab ---
    def game_folder(self) -> dict:
        """The R.U.S.E. folder in use and how it was found: {"path" or None, "picked": chosen by hand (shared with the
        launcher, settings.json), "version": this Studio's version}."""
        from rusemod.home import settings as shared_settings
        game = self._game()
        picked = shared_settings(self._home).get("game_dir")
        return {"path": str(game) if game else None, "picked": bool(picked and game and Path(picked) == game),
                "version": __version__}

    def choose_game_folder(self) -> dict:
        """Ask for the R.U.S.E. folder (when Steam can't tell, or to use another copy); it must hold RUSE.exe. Kept
        in settings.json, which the launcher reads too. Returns game_folder() and, when refused, a "message"."""
        from rusemod.home import save_settings, settings as shared_settings
        if self._window is None:
            return self.game_folder()
        chosen = pick_folder(self._window)
        if not chosen:
            return self.game_folder()
        if not Path(chosen, "RUSE.exe").is_file():
            return {**self.game_folder(), "message": f"{chosen} doesn't have RUSE.exe in it. Pick the R.U.S.E folder itself."}
        values = shared_settings(self._home)
        values["game_dir"] = str(chosen)
        save_settings(self._home, values)
        self._game_dir = None
        return self.game_folder()

    def edited(self) -> list[str]:
        """The named objects the current mod changes: a part changed for all its users marks every one of them. New
        units aren't in it: the list marks them as new instead."""
        try:
            edits = self._edits()
        except EditsFileError:
            return []
        if not edits:
            return []
        names = edits.edited() - set(edits.new_units)
        if edits.shared():
            ix = self._open()
            try:
                for address in edits.shared():
                    try:
                        names |= set(ix.show(address)["owners"])
                    except KeyError:  # not in this game build's index
                        pass
            finally:
                ix.close()
        return sorted(names)

    def edit(self, address: str, prop: str, value, mode: str = "", via: str = "") -> dict:
        """Change one value (a number, or a list of numbers) of an object in the current mod. Saved at once; setting
        the value it had before again removes the change. For a part several units share, `mode` says for whom:
        "own" (only `via`, the unit the modder came from) or "shared" (all of them)."""
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        real, _new = self._resolve(edits, address)
        ix = self._open()
        try:
            o = ix.show(real)
            types = ix.prop_types(o["class"])
            ok, why = self._editable(o)
            if not ok:
                raise StudioError(f"{address} can't be edited here ({why})")
            where, how = self._where(ix, o, mode, via, address, edits)
        finally:
            ix.close()
        p = _props(o).get(prop)
        if p is None or not _can_edit(prop, p):
            raise StudioError(f"{prop} of {address} can't be edited here")
        values = value if isinstance(value, list) else [value]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            raise StudioError(f"{prop}: numbers only")
        if p["list"] != isinstance(value, list):
            raise StudioError(f"{prop}: expected a list of numbers" if p["list"] else f"{prop}: one number")
        if prop in FLAG_LISTS:  # a set of flags: any number of them, each once
            values = list(dict.fromkeys(values))
        elif len(values) != len(p["numbers"]):
            raise StudioError(f"{prop}: expected {len(p['numbers'])} numbers" if p["list"] else f"{prop}: one number")
        kind = types.get(prop + "[]" if p["list"] else prop, "")
        if kind in INT_RANGES:
            values = [_whole(v, kind, prop) for v in values]
        with self._saving:
            edits = ModEdits(edits.folder)  # read again: another change may have been saved meanwhile
            before = edits.get(o["address"], prop, "shared") if how == "own" else None  # what "all of them" got
            before = before if before is not None else (p["numbers"] if p["list"] else p["numbers"][0])
            if (values if p["list"] else values[0]) == before:
                edits.reset(where, prop, how)
            else:
                edits.set(where, prop, values if p["list"] else values[0], how)
        return {"saved": str(edits.file), "value": values if p["list"] else values[0]}

    def reset(self, address: str, prop: str, mode: str = "", via: str = "") -> dict:
        edits = self._edits()
        if edits is None:
            return {"saved": None}
        real, _new = self._resolve(edits, address)
        ix = self._open()
        try:
            where, how = self._where(ix, ix.show(real), mode, via, address, edits)
        finally:
            ix.close()
        with self._saving:
            edits = ModEdits(edits.folder)
            edits.reset(where, prop, how)
        return {"saved": str(edits.file)}

    # --- a unit's look: its models out to Blender, its paint back into the mod (rusemod.unitlook, rusemod.blender) ---
    @staticmethod
    def _unit_models(ix: Index, address: str) -> list[str]:
        """The model files (.ase2ndfbin, as mesh packs name them) of a unit's graphics: the object its GfxDescriptor
        names and that object's own parts (not the shared interface pieces they refer to)."""
        gfx = next((w for p, k, w in ix.uses(address) if p == "GfxDescriptor" and k == "object"), None)
        files, seen, todo = set(), set(), [gfx] if gfx else []
        while todo and len(seen) < 2000:
            a = todo.pop()
            if a in seen:
                continue
            seen.add(a)
            for _p, kind, what in ix.uses(a):
                if kind == "file" and str(what).lower().endswith(".ase2ndfbin"):
                    files.add(str(what).lower().replace("/", "\\"))
                elif kind == "object" and what and what not in seen and what.startswith(gfx):
                    todo.append(what)
        return sorted(files)

    @staticmethod
    def _unit_card_file(ix: Index, address: str) -> str | None:
        """The unit's card, its picture in the build menu, as its TextureForInterface names it (None: it has none)."""
        tex = next((w for p, k, w in ix.uses(address) if p == "TextureForInterface" and k == "object"), None)
        if tex is None:
            return None
        return next((str(w) for p, k, w in ix.uses(tex) if p == "FileName" and k == "file"), None)

    def _look_card(self, address: str) -> str | None:
        """The unit's card as a texture path in ZZ_Win.dat (rusemod.unitlook.card_member), or None."""
        from rusemod.unitlook import card_member
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, _unit = self._resolve(edits, address)
        ix = self._open()
        try:
            name = self._unit_card_file(ix, real)
        finally:
            ix.close()
        return card_member(name) if name else None

    def _own_card_file(self, address: str) -> Path | None:
        """A new unit's own card in the current mod (files/cards/<its name>.png, rusemod.unitlook), whether made yet
        or not; None for the game's own units (their card is changed in place, files/replace)."""
        from rusemod.unitlook import CARDS
        try:
            edits = self._edits()
        except EditsFileError:
            return None
        unit = edits.new_unit_of(address) if edits else None
        mod = self._mod_dir()
        return mod / CARDS / f"{_tail(unit.target)}.png" if unit is not None and mod is not None else None

    def _own_model_file(self, address: str) -> Path | None:
        """A new unit's own model in the current mod (files/models/<its name>.glb, rusemod.unitmodel), whether made yet
        or not; None for the game's own units."""
        from rusemod.unitmodel import MODELS
        try:
            edits = self._edits()
        except EditsFileError:
            return None
        unit = edits.new_unit_of(address) if edits else None
        mod = self._mod_dir()
        return mod / MODELS / f"{_tail(unit.target)}.glb" if unit is not None and mod is not None else None

    def model_import(self, address: str, file: str | None = None, size: float = 1.0) -> dict:
        """Give a new unit a model of its own: `file` (a .3ds with its pictures beside it, or a .glb; asked for when
        not given) fitted to the model of the unit it copies (its length times `size`, its turret on the copy's
        turret point) and saved as the mod's files/models/<the unit's name>.glb, which the build writes into the game
        beside the copied model. Returns {"model": what was made (parts, counts, pictures, "missing"), **look()}."""
        from rusemod.modelin import ModelError
        from rusemod.unitmodel import import_model
        target = self._own_model_file(address)
        if target is None:
            # not a game rule: the Studio gives models only to the units a mod makes (a game unit's stays the game's)
            raise StudioError("Only a new unit made in this mod can get a model of its own: copy the unit first.")
        if file is None:
            if self._window is None:
                return {"model": None, **self.look(address)}
            file = pick_file(self._window, ("3D model (*.3ds;*.glb)",))
            if not file:
                return {"model": None, **self.look(address)}
        try:
            size = float(size)
        except (TypeError, ValueError):
            raise StudioError("The size is a number: 1 is as long as the unit it copies.") from None
        if not 0.2 <= size <= 5:
            raise StudioError("Give a size from 0.2 to 5 (1 is as long as the unit it copies).")
        found = [m for m in self._look_models(address)[0] if "_dest" not in m.lower()]
        if not found:
            raise StudioError("The unit this one copies has no 3D model to fit a new one to.")
        try:
            report = import_model(self._game(), found[0], Path(file), target, size=size)
        except (ModelError, OSError, ValueError) as exc:
            raise StudioError(f"{Path(file).name}: {exc}") from None
        report["file"] = Path(file).name
        record = target.with_suffix(".json")
        record.write_text(json.dumps({"from": str(file), "size": size, "report": report}, indent=1), encoding="utf-8")
        return {"model": report, **self.look(address)}

    def model_import_remove(self, address: str) -> dict:
        """Take a new unit's own model out of the mod: it shows the model of the unit it copies again."""
        target = self._own_model_file(address)
        if target is not None:
            with self._saving:
                target.unlink(missing_ok=True)
                target.with_suffix(".json").unlink(missing_ok=True)
        return self.look(address)

    def _card_view(self, address: str) -> dict | None:
        """The card as the unit page shows it: {"texture", "width", "height", "url": the picture now (the mod's or the
        game's, a copy in the cache), "own": whether the mod has its own}; None when the unit has no card. A new unit's
        own card is files/cards/<its name>.png; until it has one, it shows its source's."""
        from rusemod.dxt import png_bytes
        from rusemod.unitlook import is_picture, mod_textures, picture_rgba
        member = self._look_card(address)
        game = self._game()
        if member is None or game is None:
            return None
        zz = find_pack(game, "ZZ_Win.dat")
        st = zz.stat()
        arc = Edat.open(str(zz))
        try:
            entry = arc.entry(member)
            original = bytes(arc.read(entry)) if entry is not None else None
        finally:
            arc.close()
        if original is None or not is_picture(original):
            return None
        w, h, rgba = picture_rgba(original)
        mod = self._mod_dir()
        mine = self._own_card_file(address)  # a new unit's own card (made or not); None for a game unit
        mine_made = mine is not None and mine.is_file()
        replaced = (mod_textures(mod).get(member) or (None, None))[0] if mod is not None else None
        own = mine if mine_made else replaced  # a new unit without its own shows its source's, as the mod has it
        if own is not None:
            fst = own.stat()
            name = hashlib.sha1(f"{own}|{fst.st_size}|{fst.st_mtime_ns}".encode()).hexdigest()[:16] + ".png"
            copy = self.cache_dir / "units" / "paint" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(own, copy)
        else:
            name = hashlib.sha1(f"{member}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()[:16] + ".png"
            copy = self.cache_dir / "units" / "cards" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                part = copy.with_name(copy.name + ".part")
                part.write_bytes(png_bytes(rgba, w, h, channels=4))
                part.replace(copy)
        return {"texture": member, "width": w, "height": h, "own": mine_made if mine is not None else own is not None,
                "url": f"cache/units/{'paint' if own is not None else 'cards'}/{name}"}

    def look_card(self, address: str, picture: str) -> dict:
        """Use `picture` (a PNG, as a data: address or base64, the card's own size: the page takes it from its 3D
        view) as the unit's card in the current mod (files/replace/<card>.png). Returns {"card": _card_view, "message"}."""
        from rusemod.png import read_png
        from rusemod.unitlook import REPLACE
        mod = self._mod_dir()
        if mod is None:
            raise StudioError("Pick or make a mod first: the card goes into it.")
        card = self._card_view(address)
        if card is None:
            raise StudioError("This unit has no card picture the Studio can change.")
        try:
            data = base64.b64decode(picture.split(",", 1)[-1], validate=True)
            w, h, _px = read_png(data)
        except (ValueError, TypeError):
            raise StudioError("The card picture couldn't be read (not a PNG).") from None
        if (w, h) != (card["width"], card["height"]):
            raise StudioError(f"The card picture is {w} x {h}; this unit's card is {card['width']} x {card['height']}.")
        # a new unit gets a card of its own (files/cards); a game unit's is changed in place (files/replace)
        to = self._own_card_file(address) or mod / REPLACE / (card["texture"].replace("\\", "/") + ".png")
        to.parent.mkdir(parents=True, exist_ok=True)
        part = to.with_name(to.name + ".part")
        part.write_bytes(data)
        part.replace(to)
        return {"card": self._card_view(address),
                "message": f"The card is in {mod.name} now. Click Test in game to see it in the build menu."}

    def look_card_reset(self, address: str) -> dict:
        """Remove the current mod's card for this unit: the game's own comes back. Returns {"card", "message"}."""
        from rusemod.unitlook import REPLACE
        mod = self._mod_dir()
        card = self._card_view(address)
        if mod is not None and card is not None:
            (self._own_card_file(address) or mod / REPLACE / (card["texture"].replace("\\", "/") + ".png")).unlink(
                missing_ok=True)
        return {"card": self._card_view(address), "message": "The game's own card is back."}

    def _look_folder(self, address: str) -> Path:
        mod = self._mod_dir()
        return self.cache_dir / "looks" / (mod.name if mod else "_") / re.sub(r"[^A-Za-z0-9_-]", "_", _tail(address))

    def _blender(self) -> Path | None:
        from rusemod.blender import find_blender
        from rusemod.home import settings as shared_settings
        return find_blender(shared_settings(self._home).get("blender"))

    def _look_models(self, address: str) -> tuple[list[str], list[str]]:
        """(the unit's models, the textures they're drawn with: paths in ZZ_Win.dat)."""
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        real, _unit = self._resolve(edits, address)
        ix = self._open()
        try:
            names = self._unit_models(ix, real)
        finally:
            ix.close()
        if not names:  # ammo, weapons and the like: nothing to open
            return [], []
        from rusemod import models
        lib = models.Library(self._game())
        try:
            found = [n for n in (lib.find(m, lighter=False) for m in names) if n]
            textures = sorted({models.texture_member(t) for n in found for _p, t in lib.parts(n) if t})
        finally:
            lib.close()
        return found, textures

    def look(self, address: str) -> dict:
        """The Look box of a unit: {"models": its models, "textures": the pictures they're drawn with, "painted":
        those the current mod repaints, "blender": Blender's path ("" when not found), "download": where to get it,
        "opened": whether the unit has been opened in Blender (its work folder is there)}."""
        from rusemod.blender import DOWNLOAD
        from rusemod.unitlook import LOOK_FILE, mod_textures
        if self._game() is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no models to open.")
        found, textures = self._look_models(address)
        mod = self._mod_dir()
        painted = sorted(set(textures) & set(mod_textures(mod))) if mod else []
        blender = self._blender()
        own = self._own_model_file(address)
        own_model = None
        if own is not None and own.is_file():
            try:
                own_model = json.loads(own.with_suffix(".json").read_text(encoding="utf-8")).get("report") or {}
            except (OSError, ValueError):
                own_model = {}
        return {"models": found, "textures": textures, "painted": painted, "blender": str(blender or ""),
                "download": DOWNLOAD, "opened": (self._look_folder(address) / LOOK_FILE).is_file(),
                "new_unit": own is not None, "own_model": own_model}

    def look_open(self, address: str) -> dict:
        """Write the unit's models with their pictures into its work folder and open them in Blender, ready to paint
        (each texture linked to its picture: Image > Save writes it). Returns look() and a "message"."""
        from rusemod import models, unitlook
        from rusemod.blender import open_models
        blender = self._blender()
        if blender is None:
            raise StudioError("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use "
                              "Choose Blender… to show the Studio where blender.exe is.")
        found, _textures = self._look_models(address)
        if not found:
            raise StudioError("This unit has no 3D model the Studio can open.")
        folder = self._look_folder(address)
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)  # a fresh copy of the game's pictures each time
        lib = models.Library(self._game())
        try:
            record = unitlook.prepare(lib, found, folder)
        finally:
            lib.close()
        mod = self._mod_dir()
        if mod is not None:  # paint the mod already has goes on the pictures, so work goes on from it
            have = unitlook.mod_textures(mod)
            for name, info in record["pictures"].items():
                pics = have.get(info["texture"])
                src = pics[1 if info["kind"] == "alpha" else 0] if pics else None
                if src is not None:
                    shutil.copyfile(src, folder / name)
        self._blenders[str(folder)] = open_models(blender, record["models"])
        return {**self.look(address), "message": f"Opening {len(found)} model(s) in Blender. Paint on the model "
                "there, then come back and click Bring back: it saves your paint and puts it in your mod."}

    def look_bring_back(self, address: str) -> dict:
        """Copy every picture painted in Blender (since Open in Blender) into the current mod (files/replace), so
        Test in game shows it. The Blender painting it is asked to save first (rusemod.blender.ask_to_save): a
        Blender this Studio opened and still running is waited for (20 s at most), one it doesn't know of (the
        Studio was restarted) 2 s, a closed one not at all. Returns look(), "brought" [{texture, kind}] and a
        "message"."""
        from rusemod import unitlook
        from rusemod.blender import ask_to_save
        mod = self._mod_dir()
        if mod is None:
            raise StudioError("Pick or make a mod first: the paint goes into it.")
        folder = self._look_folder(address)
        if not (folder / unitlook.LOOK_FILE).is_file():
            raise StudioError("Open this unit in Blender first and paint it, then Bring back.")
        proc = self._blenders.get(str(folder))
        running = proc is not None and proc.poll() is None
        quiet = False
        if running or proc is None:
            quiet = ask_to_save(folder, timeout=20.0 if running else 2.0) is None and running
        record = json.loads((folder / unitlook.LOOK_FILE).read_text(encoding="utf-8"))
        brought = unitlook.bring_back(folder, mod)
        for b in brought:  # what's in the mod now is the new starting point: bringing back twice adds nothing
            pic = folder / b["picture"]
            record["pictures"][b["picture"]]["hash"] = unitlook._pixels_hash(pic, b["kind"] == "alpha")
        if brought:
            (folder / unitlook.LOOK_FILE).write_text(json.dumps(record, indent=1), encoding="utf-8")
        message = (f"Brought back {len(brought)} painted picture(s) into {mod.name}. Click Test in game to see them."
                   if brought else "Nothing new was painted yet. Paint on the model in Blender, then click Bring "
                                   "back.")
        if quiet:
            message += (" Blender didn't answer in time: in Blender, click Save paint (Ctrl+S), then Bring back "
                        "again.")
        return {**self.look(address), "brought": [{"texture": b["texture"], "kind": b["kind"]} for b in brought],
                "message": message}

    PREVIEW_SIDE = 1024  # the preview's pictures: a mip level at most this wide (unit pictures are 1024 or 2048)
    PREVIEW_VERSION = 1  # bumped when what rusemod.gltf writes changes (1: propeller discs apart, 2026-10-04)

    def unit_preview(self, address: str) -> dict:
        """A unit's 3D model for the preview on its page: {"models": [{"url": "cache/units/...glb", "name"}],
        "paint": {texture: url of the mod's painted picture of it}, "card": its build-menu card (_card_view) or None}.
        The .glb files (rusemod.gltf) are made once per game build and kept in the cache: a few seconds the first
        time, then at once."""
        from rusemod import gltf, models
        from rusemod.unitlook import mod_textures
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no models to show.")
        found, textures = self._look_models(address)
        own = self._own_model_file(address)
        if own is not None and own.is_file():  # its own model (files/models): shown as the mod has it
            st = own.stat()
            name = hashlib.sha1(f"{own}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16] + ".glb"
            copy = self.cache_dir / "units" / "own" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(own, copy)
            return {"models": [{"url": f"cache/units/own/{name}", "name": own.stem}], "paint": {},
                    "card": self._card_view(address)}
        st = find_pack(game, "ZZ_Win.dat").stat()
        build = f"{st.st_size}-{int(st.st_mtime)}-v{self.PREVIEW_VERSION}"  # a new game build makes them again
        out = self.cache_dir / "units" / build
        shown = []
        with self._previews_lock:
            lib = None
            try:
                for name in found:
                    stem = re.sub(r"[^A-Za-z0-9_-]", "_", name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", ""))
                    file = out / f"{stem}-{hashlib.sha1(name.encode()).hexdigest()[:8]}.glb"
                    if not file.is_file():
                        if lib is None:
                            lib = models.Library(game)
                        glb, _pictures, _summary = gltf.model_glb(lib, name, side=self.PREVIEW_SIDE)
                        out.mkdir(parents=True, exist_ok=True)
                        part = file.with_name(file.name + ".part")
                        part.write_bytes(glb)
                        part.replace(file)
                    shown.append({"url": f"cache/units/{build}/{file.name}", "name": stem})
            finally:
                if lib is not None:
                    lib.close()
        paint = {}
        mod = self._mod_dir()
        have = mod_textures(mod) if mod is not None else {}
        for tex in textures:
            colour = (have.get(tex) or (None, None))[0]
            if colour is None:
                continue
            st = colour.stat()  # a copy in the cache (the window shows files from there), named for this version
            name = hashlib.sha1(f"{colour}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16] + ".png"
            copy = self.cache_dir / "units" / "paint" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(colour, copy)
            paint[tex] = f"cache/units/paint/{name}"
        return {"models": shown, "paint": paint, "card": self._card_view(address) if shown else None}

    def choose_blender(self) -> dict:
        """Ask where blender.exe is; kept in settings.json. Returns look()-style {"blender": path or ""}."""
        from rusemod.home import save_settings, settings as shared_settings
        if self._window is None:
            return {"blender": str(self._blender() or "")}
        chosen = pick_file(self._window, ("Blender (blender.exe)",))
        if chosen and Path(chosen).name.lower() == "blender.exe" and Path(chosen).is_file():
            values = shared_settings(self._home)
            values["blender"] = str(chosen)
            save_settings(self._home, values)
        elif chosen:
            return {"blender": str(self._blender() or ""), "message": "That isn't blender.exe. Pick blender.exe in "
                                                                       "Blender's folder."}
        return {"blender": str(self._blender() or "")}

    def get_blender(self) -> dict:
        """Open Blender's download page (it's free) in the web browser."""
        from rusemod.blender import DOWNLOAD
        self._starter.open_url(DOWNLOAD)
        return {"url": DOWNLOAD}

    # --- new units ---
    def new_unit(self, source: str, name: str, price, nation: int = -1, factory: int = -1) -> dict:
        """A new unit in the current mod: a copy of `source` called `name` (in every language), costing `price` at
        every battle date, in the source's build menu or in another nation's (`nation` and `factory`, both given).
        Returns its address, so the page can open it."""
        name = (name or "").strip()
        if not name:
            raise StudioError("Give the new unit a name.")
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            raise StudioError("Price: one number, used for every battle date.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: a new unit is saved in a mod.")
        if source in edits.new_units:
            raise StudioError(f"{name}: copy the unit {_tail(source)} was made from instead (a copy of a copy would "
                              f"lose its changes)")
        ix = self._open()
        try:
            try:
                o = ix.show(source)
            except KeyError:
                # not a game rule: the game or one of its files isn't found
                raise StudioError(f"{source} isn't in this game build") from None
            if not o["export"] or o["class"] not in KIND_OF:
                raise StudioError(f"{source} isn't a unit or building, so it can't be copied here")
            types = ix.prop_types(o["class"])
            menus = {(u["nation"], u["factory"]) for u in self._all_units(ix) if u["factory"] is not None}
            namespace, tail = source.rsplit("/", 1)
            m = _PREFIX.match(tail)
            prefix = m.group(1) if m else "Descriptor_Unit_"

            def taken(t: str) -> bool:
                if t in edits.new_units:
                    return True
                try:
                    ix.show(t)
                    return True
                except KeyError:
                    return False

            stem = safe_name(name)
            if stem:
                target = f"{namespace}/{prefix}{stem}"
                if taken(target):
                    raise StudioError(f"There's already a unit called {prefix}{stem} (from {name!r}). Pick another "
                                      f"name.")
            else:  # a name without letters or digits A-Z (Japanese, say): the address gets a number instead
                n = 1
                while taken(f"{namespace}/{prefix}New_{n}"):
                    n += 1
                target = f"{namespace}/{prefix}New_{n}"
        finally:
            ix.close()
        values: dict = {}
        prices = _props(o).get("ProductionPrice")
        if prices and _can_edit("ProductionPrice", prices):
            kind = types.get("ProductionPrice[]" if prices["list"] else "ProductionPrice", "")
            p = _whole(price, kind, "ProductionPrice") if kind in INT_RANGES else price
            values["ProductionPrice"] = [p] * len(prices["numbers"]) if prices["list"] else p
        if nation >= 0 or factory >= 0:
            if (nation, factory) not in menus:
                # not a game rule: the build menus the game has
                raise StudioError(f"No build menu for nation {nation} and factory {factory}: pick one of the menus "
                                  f"the game has")
            own_nation = next((int(n) for path, n, _t in o["values"] if path == "Nationalite" and n is not None), 0)
            own_factory = next((int(n) for path, n, _t in o["values"] if path == "Factory" and n is not None), None)
            if (nation, factory) != (own_nation, own_factory):
                values["Nationalite"], values["Factory"] = nation, factory
        with self._saving:
            edits = ModEdits(edits.folder)  # read again: another change may have been saved meanwhile
            if target in edits.new_units:
                raise StudioError(f"There's already a unit at {target}. Pick another name.")
            edits.add_unit(target, source, name, values)
        return {"address": target, "name": name, "saved": str(edits.file)}

    def delete_unit(self, address: str) -> dict:
        """Remove a new unit from the current mod: its copy, every change made to it and its parts, and its name."""
        edits = self._edits()
        if edits is None or address not in edits.new_units:
            raise StudioError(f"{address} isn't a unit made in this mod, so it can't be deleted here")
        with self._saving:
            edits = ModEdits(edits.folder)
            source = edits.new_units[address].source if address in edits.new_units else None
            edits.remove_unit(address)
        return {"deleted": address, "source": source, "saved": str(edits.file)}

    def test_in_game(self) -> dict:
        """Build the current mod into the PC's one modded copy (`RUSE-Instances\\Modded game`, the Launcher's too:
        rusemod.play.shared_copy) and start the game from it, in the background. Returns {'job': id}; follow it with
        job(id)."""
        # the mod and the map being edited, together (one folder when they're the same, as before mods and maps were
        # apart): the units of the one on the ground of the other
        folders = list(dict.fromkeys(f for f in (self._mod_dir(), self._map_dir()) if f is not None))
        if not folders:
            raise StudioError("Pick or make a mod or a map first.")
        folder = folders[-1]
        if self._building():  # one build at a time: two raced for the same copy
            raise StudioError("A test is already being built: wait for it to finish.")
        if self._restoring():  # a copy built now would take half-restored files (rusemod.backup)
            # not a game rule: something else is busy (the game, the other app, a restore)
            raise StudioError("The game's files are being restored: wait for it to finish.")

        game = self._game()
        copies = self._copies(game)
        instance = copies / SHARED if copies is not None else None
        look = self._where_to_look(folder) if game is not None else []
        name = " + ".join(f.name for f in folders)
        said = words(self.prefs().get("lang") or schema.BASE)  # the build's lines for the player, in their language

        def work(say):
            if game is None:
                # not a game rule: the game or one of its files isn't found
                raise BuildError("We couldn't find R.U.S.E.")
            self._starter.modded(game, folders, instance, name, say, words=said)
            say(f"Built in {instance}. To see your changes in the game:")
            for line in look or ["Your unit changes show in every game mode."]:
                say(f"  {line}")

        job = Job()
        self._jobs[job.id] = job
        self._test_job = job.id
        self._test_folders = folders  # where a failed test's mistakes are looked for (test_problems)
        where = "; ".join(look) if look else "your unit changes show in every game mode"
        return job.start(self._reading_game(game, work),  # a restore, in either app, waits for the build
                         f"R.U.S.E. is starting from {instance}. To see your changes: {where}.",
                         plain=(BuildError, RndfError, OSError))

    # --- a failed test's mistakes, each with its fix (owner, 2026-10-02: an old mistake in a mod blocked every test,
    # buried in the log, and the Studio offered no way out) ---
    _SPAWN_MISTAKE = re.compile(r"(?P<pack>[A-Za-z0-9_]+): scenario\.toml: the spawn of (?P<what>\S+) at "
                                r"\((?P<x>-?\d+), (?P<y>-?\d+)\) in (?P<file>\S+?\.scenario) is for camp")
    _ROAD_MISTAKE = re.compile(r"(?P<pack>[A-Za-z0-9_]+): (?P<roads>road \d+ \(.*?\)(?:, road \d+ \(.*?\))*) would "
                               r"be cut off")

    def test_problems(self) -> dict:
        """The last Test in game's mistakes, when its build stopped on them: {"problems": [{"text": the build's words,
        "mod": the mod folder it's in or "", "fixes": [{"kind": "spawn_neutral" | "spawn_remove" | "road_remove",
        "path": the file, "pack", and what finds the item again}]}]}. A mistake the Studio can't fix here has no
        fixes (its words say what to change)."""
        job = self._jobs.get(getattr(self, "_test_job", None))
        if job is None or not job.errors:
            return {"problems": []}
        folders = [Path(f) for f in getattr(self, "_test_folders", [])]
        by_id = {}
        for f in folders:
            try:
                by_id[load_mod(f).id] = f
            except Exception:  # noqa: BLE001 - a folder that can't be read just gets no fix
                continue
        order = [by_id[i] for i in job.order if i in by_id] or folders
        return {"problems": [self._problem(text, folders, order) for text in job.errors]}

    def _problem(self, text: str, folders: list, order: list) -> dict:
        fixes, mod = [], ""
        m = self._SPAWN_MISTAKE.search(text)
        if m:
            for folder in folders:
                path = folder / "maps" / m["pack"] / "scenario.toml"
                for s in self._spawns_in(path):
                    if s.what == m["what"] and s.file.lower() == m["file"].lower() and \
                            f"{s.x:.0f}" == m["x"] and f"{s.y:.0f}" == m["y"]:
                        who = {"path": str(path), "pack": m["pack"], "what": s.what, "file": s.file,
                               "x": s.x, "y": s.y}
                        fixes = [who | {"kind": "spawn_neutral"}, who | {"kind": "spawn_remove"}]
                        # the build stops at the first one: every team spawn of this setup at once, or one test per
                        # spawn (the owner's old mod had 57 on D-Day)
                        team = sum(1 for t in self._spawns_in(path) if t.file.lower() == s.file.lower()
                                   and t.camp not in (None, scenario.NEUTRAL))
                        if team > 1:
                            every = {"path": str(path), "pack": m["pack"], "file": s.file, "count": team}
                            fixes += [every | {"kind": "spawns_neutral_all"}, every | {"kind": "spawns_remove_all"}]
                        mod = folder.name
                        break
                if fixes:
                    break
        m = self._ROAD_MISTAKE.search(text)
        if m:
            wanted = [int(n) for n in re.findall(r"road (\d+) \(", m["roads"])]
            seen = 0  # the build numbers the map's new roads across the mods, in load order
            for folder in order:
                path = folder / "maps" / m["pack"] / "roads.toml"
                try:
                    roads = self._read_roads(path)
                except StudioError:
                    continue
                for k, r in enumerate(roads):
                    if seen + k + 1 in wanted:
                        fixes.append({"kind": "road_remove", "path": str(path), "pack": m["pack"], "road": seen + k + 1,
                                      "points": [list(p) for p in r.points]})
                        mod = mod or folder.name
                seen += len(roads)
        return {"text": text, "mod": mod, "fixes": fixes}

    @staticmethod
    def _spawns_in(path: Path) -> list:
        if not path.is_file():
            return []
        try:
            return scenario.parse_spawns(tomllib.loads(path.read_text(encoding="utf-8")).get("spawn", []), str(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, scenario.ScenarioError):
            return []

    def test_fix(self, fix: dict) -> dict:
        """Apply one of test_problems' fixes to the file it names (only a file of the last test's mods): a spawn made
        neutral or taken out, a road taken out. The item is found again by what it is, not by its number, so two fixes
        in one file never hit the wrong one. Returns {"done": what was changed}."""
        path = Path(str(fix.get("path", "")))
        mine = [Path(f).resolve() for f in getattr(self, "_test_folders", [])]
        if not any(path.resolve().is_relative_to(f / "maps") for f in mine):
            raise StudioError("That file isn't part of the last test's mods.")
        kind = fix.get("kind")
        with self._saving:
            if kind in ("spawn_neutral", "spawn_remove", "spawns_neutral_all", "spawns_remove_all"):
                data = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
                moves, starts, spawns, removes = _scenario_tables(data, str(path))
                sectors = _scenario_sectors(data, str(path))
                if kind.endswith("_all"):  # every team spawn of that setup
                    hit = [i for i, s in enumerate(spawns) if s.file.lower() == str(fix.get("file", "")).lower()
                           and s.camp not in (None, scenario.NEUTRAL)]
                else:
                    hit = [i for i, s in enumerate(spawns) if s.what == fix.get("what") and s.file == fix.get("file")
                           and s.x == fix.get("x") and s.y == fix.get("y")][:1]
                if not hit:
                    raise StudioError("That spawn isn't in the mod any more.")
                if kind in ("spawn_neutral", "spawns_neutral_all"):
                    for k in hit:
                        spawns[k] = replace(spawns[k], camp=scenario.NEUTRAL)
                else:
                    spawns = [s for i, s in enumerate(spawns) if i not in hit]
                if moves or starts or spawns or removes or (sectors is not None and sectors.whole_map):
                    _save_checked(path, _scenario_toml(moves, starts, spawns, removes, self.SCENARIO_HEADER, sectors),
                                  _scenario_checked(str(path)))
                else:
                    path.unlink()
                done = (f"{len(hit)} team spawn(s) in {fix.get('file')}" if kind.endswith("_all") else fix.get("what")) \
                    + (": made neutral" if "neutral" in kind else ": taken out")
            elif kind == "road_remove":
                roads = self._read_roads(path)
                want = [list(p) for p in fix.get("points", [])]
                k = next((i for i, r in enumerate(roads) if [list(p) for p in r.points] == want), None)
                if k is None:
                    raise StudioError("That road isn't in the mod any more.")
                del roads[k]
                self._write_roads(path, roads)
                done = f"road {fix.get('road')}: taken out"
            else:
                raise StudioError(f"unknown fix {kind!r}")
        return {"done": done}

    def _where_to_look(self, folder: Path) -> list[str]:
        """What to open in the game to see each map the mod changes: the scenario setups it spawns units in or moves
        things on, else the map's skirmish (ground, scenery, cover, movement and roads show in every setup)."""
        out = []
        maps = folder / "maps"
        for d in sorted((p for p in maps.iterdir() if p.is_dir()), key=lambda p: p.name.lower()) if maps.is_dir() else []:
            files = {f.name for f in d.glob("*.toml")} & set(MAP_FILES)
            if not files:
                continue
            try:
                scenarios = self.map_scenarios(d.name, edited=False)["scenarios"]
            except (StudioError, OSError, ValueError, KeyError):
                continue
            wanted = set()
            if "scenario.toml" in files:
                try:
                    moves, spawns = self._read_scenario_edits(d.name)
                    wanted = {m.file.lower() for m in moves} | {s.file.lower() for s in spawns}
                except StudioError:
                    pass
            chosen = [s for s in scenarios if s["file"].lower() in wanted] if wanted else \
                [s for s in scenarios if s.get("kind") == "skirmish"][:1] or scenarios[:1]
            for s in chosen:
                for e in s.get("entries", [])[:2]:
                    title = (e.get("titles") or {}).get("us") or e.get("name") or d.name
                    mode = {"skirmish": "BATTLES", "operation": "OPERATION",  # the game's main-menu buttons
                            "campaign": "CAMPAIGN"}.get(e.get("kind"), e.get("kind") or "a game")
                    out.append(f"{mode} > {title} ({e.get('name', s['file'])})")
        return out

    def _copies(self, game: Path | None) -> Path | None:
        """Where Test in game puts its modded copies; None without the game (no place for them yet)."""
        return (self._instances or instances_dir(game)) if game is not None else None

    def _building(self) -> bool:
        """Whether a Test in game is still being built."""
        busy = self._jobs.get(getattr(self, "_test_job", None))
        return busy is not None and busy.state == "running"

    # --- the troubleshooter (rusemod.doctor): what can stop Test in game, checked in one go ---
    FIXES = ("close_game", "clear_leftovers")  # the findings' fixes run here; "choose_game" is the window's own

    def troubleshoot(self) -> dict:
        """Every finding (rusemod.doctor.checks, with the Studio's own Steam check), and the same as plain text for a
        bug report, the player's own folders left out (rusemod.community), with the Studio's last start-up times
        (rusemod.startlog): {"findings": [...], "report": text}."""
        game = self._game()
        findings = doctor.checks(game, self._copies(game), steam_running=self._starter.steam_running)
        report = doctor.report(findings, APP_NAMES[self.UPDATE_APP], self.UPDATE_VERSION,
                               startlog.recent(self.UPDATE_APP, self._home))
        return {"findings": findings, "report": private_paths_out(report)}

    def troubleshoot_fix(self, action: str) -> dict:
        """Run one finding's fix: "close_game" or "clear_leftovers" (rusemod.doctor.fix). Returns {"done": how many,
        "left": what couldn't be done}."""
        if action not in self.FIXES:
            raise StudioError(f"There's no fix called {action!r}.")
        game = self._game()
        copies = self._copies(game)
        if copies is None:
            # not a game rule: the game or one of its files isn't found
            raise StudioError("We couldn't find R.U.S.E., so there are no modded copies yet.")
        if action == "clear_leftovers" and self._building():  # the copy being built looks like a leftover
            raise StudioError("A test is being built: wait for it to finish.")
        return doctor.fix(action, game, copies)

    # --- the clean game backup (rusemod.backup.BackupCalls: backup_status, backup_make, backup_check, backup_restore,
    # steam_verify), in Settings; its hooks ---
    def _backup_game(self) -> Path | None:
        game = self._game()
        return game if game is not None and game.is_dir() else None

    def _backup_open_url(self, url: str) -> None:
        self._starter.open_url(url)

    def _building_copy(self) -> str:
        """A Test in game building its copy reads the game's files: a restore waits for it."""
        return "A test is being built: wait for it to finish, then try again." if self._building() else ""

    # --- a mod as one file (MOD_FORMAT §2, rusemod.package) ---
    def mod_info(self, kind: str = "mod") -> dict:
        """The current mod's (or map's: `kind` "map") manifest, for the export form: id, name, version, authors,
        description, the game build it was last exported on and its fingerprint."""
        folder = self._mod_dir(self._kind(kind))
        if folder is None:
            raise StudioError("Pick or make a map first." if kind == "map" else "Pick or make a mod first.")
        try:
            return package.info_of(folder)
        except package.PackageError as exc:
            raise StudioError(str(exc)) from None

    def export_mod(self, version: str, author: str = "", description: str = "", kind: str = "mod",
                   choose: bool = False) -> dict:
        """Turn the current mod (or map: `kind` "map") into one file, `<id>-<version>.rusemod`, and put it straight
        where it's used (the owner, 2026-10-02): the file in the platform's `exports` folder, and the mod in the
        Launcher's library, ready for a mod set. `choose`: the window's "save as" dialog picks the file's place
        instead. The version, author and description go into the mod's mod.toml first, so the next export starts
        from them (blank author or description: the old ones stay). The mod is built on the game to record the game
        build and its fingerprint (MOD_FORMAT §12) in the package; without the game it's packed without them, and
        the report says so. Returns {'job': id}, or {'job': None} when the modder cancels the dialog."""
        kind = self._kind(kind)
        folder = self._mod_dir(kind)
        if folder is None:
            raise StudioError("Pick or make a map first." if kind == "map" else "Pick or make a mod first.")
        version = (version or "").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise StudioError("The version should be three numbers, like 1.0.0.")
        suggested = package.file_name(self.mod_info(kind) | {"version": version})
        if self._pick_save is not None:
            target = self._pick_save(suggested)
        elif choose:
            target = pick_save(self._window, suggested, PACKAGE_FILES) if self._window is not None else None
        else:
            (self._home / "exports").mkdir(parents=True, exist_ok=True)
            target = self._home / "exports" / suggested
        if not target:
            return {"job": None}
        target = Path(target)
        if target.suffix.lower() != package.EXTENSION:
            target = target.with_name(target.name + package.EXTENSION)
        manifest = {"version": version}
        if (author or "").strip():
            manifest["authors"] = [author.strip()]
        if (description or "").strip():
            manifest["description"] = description.strip()

        def work(say):
            with self._saving:
                package.update_manifest(folder, mod=manifest)
            game = self._game()
            build_id = revision = fingerprint = answers = None
            if game is None:
                say("R.U.S.E. wasn't found, so the file carries no game build or fingerprint.")
            else:
                say("Building the mod on the game, to record the game build and the fingerprint…")
                result = build_and_write(game, [load_mod(folder)], say=lambda line: say("  " + line),
                                         cache=build_cache())
                if result.errors:
                    raise BuildError("Fix the mod first: the build above has errors, so nothing was exported.")
                build_id = build_of(game)
                revisions = data_revisions(game)
                revision = revisions[0] if len(revisions) == 1 else None
                fingerprint = fingerprint_text(result.fingerprint) if result.fingerprint else None
                answers = result.solved  # (what the long map steps worked out: players' builds take it from the file)
            with self._saving:
                path = package.pack(folder, target, build_id=build_id, data_revision=revision, fingerprint=fingerprint,
                                    solved=answers)
            if answers:
                say(f"The file carries the worked-out answers for {len(answers)} map(s), locked: a player's build takes "
                    f"them instead of working them out again.")
            say(f"Saved as {path}")
            job.result = self._share_view(path)
            say(f"Size: {job.result['size']} bytes")
            say(f"SHA-256: {job.result['sha256']}")
            from rusemod.library import Library, LibraryError
            try:
                info, replaced = Library(self._home / "library").add(path)
                say(f"In the Launcher's mod library as {info['name']} {info.get('version', '')}"
                    f"{' (the older version replaced)' if replaced else ''}: tick it in a mod set and press Play.")
                job.result["library"] = info.get("id")
            except LibraryError as exc:
                say(f"Not added to the Launcher's library: {exc}")

        job = Job()
        job.result = None  # the exported file's size, SHA-256 and list entry, for "Share your mod"
        self._jobs[job.id] = job
        return job.start(work, f"Saved as {target}", plain=(BuildError, RndfError, OSError, package.PackageError))

    # --- Share your mod: how an exported mod gets onto the supported-mods list (MOD_FORMAT §15) ---
    @staticmethod
    def _share_view(path) -> dict:
        """An exported file as the list needs it: where it is, its size and SHA-256, and its `[[mod]]` entry for
        the list's index.toml, ready to paste."""
        path = Path(path)
        data = path.read_bytes()
        size, sha256 = len(data), hashlib.sha256(data).hexdigest()
        return {"path": str(path), "file": path.name, "size": size, "size_text": mod_index.size_text(size),
                "sha256": sha256, "entry": mod_index.entry_text(package.check(path), size, sha256)}

    def share_info(self) -> dict:
        """What "Share your mod" shows besides an export's own file: the list's repository and its page."""
        return {"repo": mod_index.REPO, "page": mod_index.PAGE}

    # --- building the index from the Studio ---
    def build_index(self) -> dict:
        job = Job()
        self._jobs[job.id] = job
        game = self._game()
        if game is None:
            job.state, job.message = "failed", "We couldn't find R.U.S.E."
            return {"job": job.id}

        def work(say):
            build_index(game, self._path(), say=say)
            # what was read from the index before: the Maps tab can read an old one while this one builds
            self._units = self._ammo = self._by_class = None

        return job.start(work, "The game index is ready.")

    def job(self, job_id: str, since: int = 0) -> dict:
        return self._with_result(job_view(self._jobs, job_id, since))  # a backup job's result too
