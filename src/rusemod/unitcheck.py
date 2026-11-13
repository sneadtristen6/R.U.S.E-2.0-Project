"""What a unit needs to be for the game to take it, beyond what the data's types say: the build's checks on the units
(and their weapons) a mod made or changed. Each rule is one the game's own 468 unit descriptors all keep.

  DescriptorId      the game keeps one unit per id, across every kind of unit: a unit whose id is 0, or another
                    unit's, is left out of its nation's list, and orders for it build the other one (or nothing).
  Nationalite       0 to 6 (0 US, 1 Germany, 2 UK, 3 France, 4 Italy, 5 USSR, 6 Japan; not written = 0): the game
                    has room for exactly seven nations' unit lists, and another number corrupts it as it loads.
  ProductionPrice,  5 items, one per battle date: at a date with no item the game makes the unit free, or hides it
  ShowInMenu        (and a ShowInMenu of 1 or 2 items is read past its end).
  TextureForInterface  the unit's card picture: as it starts, the game lists each nation's units that are shown at
                    one of the first four battle dates (in_start_list) and reads each one's card picture without
                    asking whether it has one: a unit it lists with no card picture stops the game there. All 203
                    units of the game's own that it lists have one; the HQ truck, the gun truck and 63 more have
                    none and are never listed, so a copy of one of them shown at a battle date is the case.
  InitialFlagSet    rusemod.unitflags: flags that belong to one kind of unit.
  salvos            a weapon's mounted weapons with a SalveNumber other than -1 need 0 to 4, and the weapon's
                    Salves[SalveNumber] above 0; otherwise the game stops at load with a "Quit game ?" box.
  models            a nation's unit models are loaded only in a match where a player has that nation (its skirmish
                    mesh pack, MeshSkirmish_<nation>.spk, beside the common one), or one the cluster maps' loaders
                    force (load_everywhere): a unit whose model is only in another nation's pack would have no model,
                    or crash the game, in every other match, so the build has that nation's packs load in every
                    skirmish, and in every campaign chapter and Operation (load_in_missions).

patch.Engine asks for all but the last at the end of every run and reports what the mods made wrong (what the game's
data already had is left alone); build.build_pack asks for the models, which need ZZ_Win.dat.
"""
from __future__ import annotations

from decimal import Decimal

from .patch import Inline, ListV, Num, Ref, Text, _parts, _walk_value
from . import unitflags

# every kind of unit the game registers by DescriptorId (the classes whose objects carry one)
UNIT_CLASSES = frozenset({"TUniteDescriptor", "TUniteAuSolDescriptor", "TInfanterieDescriptor", "TAvionDescriptor",
                          "TTruckDescriptor", "TBatimentDescriptor", "TUniteDescriptorBarycentre"})
NATIONS = ("US", "Germany", "UK", "France", "Italy", "USSR", "Japan")  # Nationalite 0..6
PACK_TAGS = ("us", "ger", "uk", "fr", "ita", "urss", "japan")        # MeshSkirmish_<tag>.spk, by Nationalite
DATES = 5  # battle dates: items in ProductionPrice and ShowInMenu
ID = "DescriptorId"
NATION = "Nationalite"
WEAPON_CLASS = "TWeaponDescriptor"
MODEL = ".ase2ndfbin"
PACK_DIR = "gen_5\\pack\\gfxdescriptor\\"  # the skirmish mesh packs, in ZZ_Win.dat


def is_unit(obj) -> bool:
    return obj.cls in UNIT_CLASSES


def _int(v):
    return int(v.value) if isinstance(v, Num) else None


def nation_of(obj) -> int:
    n = _int(obj.props.get(NATION))
    return 0 if n is None else n


def problems(obj) -> list[tuple[str, str, str]]:
    """What's wrong with one unit (a patch.Obj of a UNIT_CLASSES class), id clashes aside: [(level, property, why)]."""
    out = []
    n = _int(obj.props.get(NATION))
    if n is not None and not 0 <= n < len(NATIONS):
        names = ", ".join(f"{i} {name}" for i, name in enumerate(NATIONS))
        # rule: unit-nation-range
        out.append(("error", NATION, f"{NATION} {n} isn't a nation: it must be 0 to 6 ({names}); the game has room "
                                     f"for exactly seven nations' units, and another number corrupts it as it loads"))
    if _int(obj.props.get(ID)) == 0:
        # rule: unit-id-zero
        out.append(("error", ID, f"{ID} 0 isn't an id: the game skips the unit in its unit lists, and ordering it "
                                 f"causes an error in the match; give it a number no other unit has"))
    for prop, what in (("ProductionPrice", "the game makes the unit free at the battle dates it has no price for"),
                       ("ShowInMenu", "the game hides the unit at the battle dates it has no item for, and reads a "
                                      "list of 1 or 2 items past its end")):
        v = obj.props.get(prop)
        if v is None:
            continue
        if not isinstance(v, ListV):
            # rule: unit-five-dates
            out.append(("error", prop, f"{prop} isn't a list; it needs {DATES} items, one per battle date"))
        elif len(v.items) != DATES:
            # rule: unit-five-dates
            out.append(("error", prop, f"{prop} has {len(v.items)} item(s); it needs {DATES}, one per battle date "
                                       f"({what})"))
    if not has_card(obj) and in_start_list(obj):
        # rule: unit-card-shown
        out.append(("error", CARD, f"it has no card picture ({CARD}) and is shown in a build menu ({SHOWN}): the game "
                                   f"lists such a unit as it starts, and stops there; hide it at every battle date "
                                   f"({SHOWN} all 0), or make it as a copy of a unit that has a card picture"))
    return out + unitflags.problems(obj)


CARD = "TextureForInterface"      # the unit's card, its picture in the build menu
LISTED_DATES = 4                  # the battle dates the start-up list asks about: the first four of ShowInMenu
UNLISTED_FLAGS = (30, 49)         # a unit with one of these is never in the start-up list
DECOY_FLAGS = (4, 6)              # nor is one with the first and without the second (the game's decoy buildings)


def has_card(obj) -> bool:
    """Whether a unit has a card picture: its TextureForInterface names an object (nil is none)."""
    v = obj.props.get(CARD)
    return isinstance(v, Inline) or (isinstance(v, Ref) and v.target is not None)


def in_start_list(obj) -> bool:
    """Whether the game lists this unit as it starts (each nation's units, for the in-game encyclopedia): shown at
    one of the first four battle dates (the fifth alone doesn't list it; a list longer than five is asked from its
    sixth item on), and not kept out by its flags (UNLISTED_FLAGS, DECOY_FLAGS). The four decoy anti-tank bases of
    the game, shown at four dates with no card picture, are kept out that way."""
    shown = _shown(obj)
    if not shown:
        return False
    if not any(shown[:LISTED_DATES]) and not (len(shown) > DATES and any(shown[DATES:])):
        return False
    flags = unitflags.numbers(obj.props.get(unitflags.PROP)) if obj.props.get(unitflags.PROP) is not None else set()
    if DECOY_FLAGS[0] in flags and DECOY_FLAGS[1] not in flags:
        return False
    return not any(f in flags for f in UNLISTED_FLAGS)


def ids(game) -> dict[str, int | None]:
    """{name: DescriptorId (None when it has none)} of every unit of the game."""
    return {name: _int(o.props.get(ID)) for name, o in game.objects.items() if is_unit(o)}


def id_clashes(game, names) -> dict[str, str]:
    """For the units `names`: {name: why} when another unit of the game, of any kind, has the same DescriptorId."""
    by_id: dict = {}
    for name, v in ids(game).items():
        if v is not None:
            by_id.setdefault(v, []).append(name)
    out = {}
    for name in names:
        obj = game.objects.get(name)
        v = _int(obj.props.get(ID)) if obj is not None and is_unit(obj) else None
        others = [n for n in by_id.get(v, []) if n != name] if v else []
        if others:
            out[name] = (f"{ID} {v} is also {others[0]}'s: the game keeps one unit per id, so it skips this one, and "
                         f"orders for it build {others[0]}; give it a number no other unit has (a copy gets one by "
                         f"itself when it doesn't set {ID})")
    return out


UPGRADE = "UpgradeRequire"


def research_parent_problems(game, names) -> dict[str, str]:
    """For the units `names`: {name: why} when the unit it's researched from (UpgradeRequire) isn't in the game or is
    another nation's. Researched from another nation's unit, the match's loading screen never ends, with no crash and
    no message (2026-10-09: a T-80 copied from the Soviet IS-2, researched from the KV-1, put in the USA's army; rule
    unit-research-parent). One researched from a unit the game doesn't have is refused with it (not tried in the
    game)."""
    out = {}
    for name in names:
        obj = game.objects.get(name)
        if obj is None or not is_unit(obj):
            continue
        v = obj.props.get(UPGRADE)
        if not isinstance(v, Ref):
            continue
        n = nation_of(obj)
        army = NATIONS[n] if 0 <= n < len(NATIONS) else f"nation {n}"
        parent = game.objects.get(v.target)
        fix = (f"Research it from one of {army}'s own units, or make it a unit of its own (delete {UPGRADE} and "
               f"IsUpgrade: the Studio's Upgrade box does both)")
        hang = "the loading screen never ends (no crash, no message; seen in the game)"
        if parent is None:
            out[name] = f"it's researched from {v.target} ({UPGRADE}), which isn't in the game. {fix}"
        elif nation_of(parent) != n:
            pn = nation_of(parent)
            other = NATIONS[pn] if 0 <= pn < len(NATIONS) else f"nation {pn}"
            out[name] = (f"it's researched from {v.target} ({UPGRADE}), which is {other}'s unit, but this unit is in "
                         f"{army}'s army: {hang}. {fix}")
    return out


SHOWN = "ShowInMenu"


def _shown(obj) -> list | None:
    """A unit's ShowInMenu, one number per battle date (None when it has no list)."""
    v = obj.props.get(SHOWN) if obj is not None else None
    return [_int(x) for x in v.items] if isinstance(v, ListV) else None


def research_hidden_parent_problems(game, names) -> dict[str, str]:
    """For the units `names`: {name: why} when the unit is shown in its build menu at a battle date where the unit
    it's researched from (UpgradeRequire) is hidden (its ShowInMenu 0 there). The game's build menu puts a researched
    unit's button after its parent's and stops when the parent has none (seen in the game
    2026-10-10, Italy's units hidden and China's researched from them). The owner, 2026-10-10: "There shouldn't
    be a unit hidden behind a research one shown in the menu ... The one available to be built should be first before
    the research one" (rule unit-research-shown-parent)."""
    out = {}
    for name in names:
        obj = game.objects.get(name)
        if obj is None or not is_unit(obj):
            continue
        v = obj.props.get(UPGRADE)
        if not isinstance(v, Ref):
            continue
        mine, theirs = _shown(obj), _shown(game.objects.get(v.target))
        if not mine or theirs is None:
            continue
        dates = [i + 1 for i, s in enumerate(mine) if s and i < len(theirs) and theirs[i] == 0]
        if dates:
            when = "every battle date" if len(dates) == DATES else f"battle date {', '.join(map(str, dates))}"
            out[name] = (f"it's shown in its build menu at {when}, but {v.target}, the "
                         f"unit it's researched from ({UPGRADE}), is hidden there ({SHOWN} 0): the game stops when that "
                         f"build menu opens (seen in the game). Show {v.target} at those dates too, or make this one a "
                         f"unit of its own (delete {UPGRADE} and IsUpgrade: the Studio's Upgrade box does both)")
    return out


FACTORY = "Factory"       # the kind of building a unit is made in (and whose build list its card stands in)
IS_UPGRADE = "IsUpgrade"


def far_upgrades(game) -> list[tuple[str, str]]:
    """[(the upgrade, the unit it's researched from)] for every UPGRADE of `game` (IsUpgrade 1) researched from
    (UpgradeRequire) a unit made in ANOTHER building (their Factory numbers differ). The game takes a unit out of its
    build list the moment ANY upgrade of it is researched, wherever that upgrade is made: seen in the game
    2026-11-10, a light tank made in the Barracks left its list when its upgrade made in the Armor Base was
    researched, its own upgrade in the Barracks not researched yet (rule unit-far-upgrade). The game as sold has no
    such pair (50 upgrades, each made where its unit is); two mods make one together, when one moves a unit and
    another makes it an upgrade's unit, and so can one mod alone.
    A research linked to another building's unit WITHOUT the upgrade flag is not one: that is how the Studio's board
    writes research across buildings, and in the game the unit it's researched from stayed buildable after the
    research (2026-10-18, a Tiger in the Anti-Tank Base researched from the Armor Base's Sherman)."""
    out = []
    for name, obj in game.objects.items():
        v = obj.props.get(UPGRADE) if is_unit(obj) else None
        if not isinstance(v, Ref) or not _int(obj.props.get(IS_UPGRADE)):
            continue
        parent = game.objects.get(v.target)
        if parent is None or not is_unit(parent):
            continue
        mine, theirs = _int(obj.props.get(FACTORY)), _int(parent.props.get(FACTORY))
        if mine is not None and theirs is not None and mine != theirs:
            out.append((name, v.target))
    return out


def cut_far_upgrades(game) -> list[tuple[str, str]]:
    """Make each of far_upgrades(game) a research of its own: its UpgradeRequire and IsUpgrade taken out, as the
    Studio's Upgrade box does when unticked, so researching it no longer touches the other building's unit. The
    owner, 2026-11-10: "it shouldn't be taken away before the new one's researched". `game` is changed in place
    (its own copies of those units: Game.own); the pairs cut are returned, for the build to say."""
    cut = far_upgrades(game)
    for name, _parent in cut:
        props = game.own(name).props
        props.pop(UPGRADE, None)
        props.pop(IS_UPGRADE, None)
    return cut


def _resolve(game, v):
    """The object a list item is: an owned part, or the named object a reference points at (with its name)."""
    if isinstance(v, Inline):
        return v.obj, None
    if isinstance(v, Ref) and v.target in game.objects:
        return game.objects[v.target], v.target
    return None, None


def salvo_problems(game) -> list[tuple[str, str, frozenset, str]]:
    """Every weapon of the game whose salvos the game refuses: [(top-level object, path to the weapon in it, the named
    objects its turrets and mounted weapons are, why)]."""
    out = []
    for top in sorted(game.objects):
        for path, weapon in _parts(game.objects[top]):
            if weapon.cls != WEAPON_CLASS:
                continue
            salves = weapon.props.get("Salves")
            salves = [_int(x) for x in salves.items] if isinstance(salves, ListV) else []
            turrets = weapon.props.get("TurretDescriptorList")
            for t, item in enumerate(turrets.items if isinstance(turrets, ListV) else []):
                turret, tname = _resolve(game, item)
                if turret is None:
                    continue
                mounted = turret.props.get("MountedWeaponDescriptorList")
                for m, mitem in enumerate(mounted.items if isinstance(mounted, ListV) else []):
                    mw, mname = _resolve(game, mitem)
                    sn = _int(mw.props.get("SalveNumber")) if mw is not None else None
                    if sn is None or sn == -1:
                        continue
                    where = f"TurretDescriptorList[{t}].MountedWeaponDescriptorList[{m}]"
                    reached = frozenset(n for n in (tname, mname) if n)
                    if not 0 <= sn < DATES:
                        why = f"{where} has SalveNumber {sn}, which isn't -1 or 0 to 4"
                    elif sn >= len(salves) or salves[sn] is None or salves[sn] <= 0:
                        have = f"Salves[{sn}] is {salves[sn]}" if sn < len(salves) and salves[sn] is not None \
                            else ("the weapon has no Salves" if not salves else f"Salves has no item {sn}")
                        why = f"{where} has SalveNumber {sn}, but {have}: salvo {sn} isn't defined"
                    else:
                        continue
                    out.append((top, path, reached, f"{why}; the game stops at load with a \"Quit game ?\" box. Give "
                                                    f"the weapon a Salves list with salvo {sn} above 0, or set "
                                                    f"SalveNumber to -1"))
    return out


# --- models ---
def model_files(obj, game) -> set[str]:
    """The model files (.ase2ndfbin) a unit's own Gfx parts name, lower case with backslashes, as mesh packs list
    them. Its parts are what it holds and the unnamed objects they refer to (a model's mesh is one), not named
    objects other units use too."""
    out, seen = set(), set()
    todo = [v for prop, v in obj.props.items() if prop.startswith("Gfx")]
    while todo:
        for x in _walk_value(todo.pop()):
            if isinstance(x, Text) and x.value.lower().endswith(MODEL):
                out.add(x.value.lower().replace("/", "\\"))
            elif isinstance(x, Ref) and x.target and not x.target.startswith("$") and x.target not in seen \
                    and x.target in game.objects:
                seen.add(x.target)
                todo += list(game.objects[x.target].props.values())
    return out


def pack_models(names: dict) -> dict[str, frozenset]:
    """{nation tag or "common": the models a skirmish match loads with it} from the skirmish mesh packs' model names
    (`names`: {pack file name without .spk, lower case: set of model names})."""
    common = names.get("meshskirmish_common", set())
    out = {"common": frozenset(common)}
    for tag in PACK_TAGS:
        have = set(names.get(f"meshskirmish_{tag}", set()))
        if tag == "us":
            have |= names.get("meshskirmishwitboat_us", set())
        out[tag] = frozenset(have)
    return out


def allowed_models(game) -> set[tuple[str, int]]:
    """(model, Nationalite) of every unit of the game: what the game's own units already have works as it does for
    them (Canon_atomique_FR, French, uses the US Long Tom's model)."""
    return {(m, nation_of(o)) for o in game.objects.values() if is_unit(o) for m in model_files(o, game)}


def missing_models(obj, game, packs: dict, allowed=frozenset()) -> dict[str, list[str]]:
    """The models of a unit that aren't loaded for its nation: {model: [the nations whose packs have it]}. Models in
    no skirmish pack, and (model, nation) pairs in `allowed` (the game's own units already have them), don't count."""
    n = nation_of(obj)
    if not 0 <= n < len(PACK_TAGS):
        return {}
    have = packs[PACK_TAGS[n]] | packs["common"]
    out = {}
    for model in sorted(model_files(obj, game)):
        if model in have or (model, n) in allowed:
            continue
        where = [NATIONS[i] for i, tag in enumerate(PACK_TAGS) if model in packs[tag]]
        if where:
            out[model] = where
    return out


# --- having another nation's models load in every match ---
# Each cluster map (genglad\patchable\scenario\<map>\<scenario>\clustermap, 85 in the game) has three loaders of
# per-nation skirmish packs: proxies, meshes and animations. In a skirmish a loader loads SkirmishPacks[i] when a player
# has nation i, or when bit i of its ForceLoadBitFieldIfSkirmish is set (no shipped loader sets it); in other games it
# loads its NotSkirmishPacks, every nation's. Bit i is Nationalite i: SkirmishPacks lists US, GER, UK, FR, ITA, URSS,
# JAP. (ForceLoadBitFieldNationalite, set to 2 on four objects of one scenario, is another class's: the sub-clusters a
# map starts, not packs.)
LOADER = "TClusterLoadSelectifResource"
FORCE = "ForceLoadBitFieldIfSkirmish"


def loaders(game) -> list[tuple[str, str, object]]:
    """Every loader of per-nation skirmish packs in the cluster maps: [(top-level object, path to it, the loader)]."""
    out = []
    for top in sorted(game.objects):
        for path, part in _parts(game.objects[top]):
            if part.cls == LOADER and isinstance(part.props.get("SkirmishPacks"), ListV):
                out.append((top, path, part))
    return out


def load_everywhere(game, nations) -> dict[int, tuple[int, int]]:
    """Have the skirmish packs of `nations` (Nationalite numbers) load in every skirmish, beside the match's own: their
    bits set in every loader that has a pack for them. {nation: (loaders that now load it, cluster maps they're in)};
    a nation no loader has a pack for gets (0, 0)."""
    out = {}
    for n in sorted(set(nations)):
        count, maps = 0, set()
        for top, path, part in loaders(game):
            if n >= len(part.props["SkirmishPacks"].items):
                continue
            old = part.props.get(FORCE)
            bits = int(old.value) if isinstance(old, Num) else 0
            if not bits >> n & 1:  # (changed in the game's own copy of the object: patch.Game.own)
                game.own_part(top, path).props[FORCE] = Num("uint32", Decimal(bits | 1 << n))
            count += 1
            origin = game.objects[top].origin
            maps.add(origin[0] if origin else top)
        out[n] = (count, len(maps))
    return out


# Outside a skirmish (a campaign chapter, an Operation) a loader loads its NotSkirmishPacks and nothing else: the force
# bit above does nothing there. 30 of the 85 cluster maps list only the nations their mission plays, one pack each
# (Holland's chapters: the common pack, US, Germany and UK), so another nation's unit, spawned there or bought, has no
# model (a player's build spawning French units, Holland, 2026-10-03: the game crashed loading the mission). The other
# 55 list one pack of several nations' units (PackMesh_All): it serves the nations its UsefulnessMask names, the six
# of the game as first sold and NOT Japan (the pack's mask ends ...3F, Japan's own packs' ...40; a model goes to a
# pack only when their masks share a nation bit). So a Japanese unit in one of those 55 had no model either (read in
# the data and the program, 2026-11-10; a mission of ours spawning Japanese units built with no word about it).
NOT_SKIRMISH = "NotSkirmishPacks"
MASK = "UsefulnessMask"


def _mask(game, target: str) -> int | None:
    """A pack's mask (its nation bits are the low ones, Nationalite 0 to 6), or None when the data doesn't say."""
    obj = game.objects.get(target)
    return _int(obj.props.get(MASK)) if obj is not None else None


# A cluster map's picker of per-nation skeleton loaders says which nations' it runs in a game that is not a skirmish:
# the nations of these three fields' bits (most Operations: all six of the game as first sold; a campaign chapter:
# the two to five it plays; Japan in almost none).
MISSION_BITS = ("BitFieldNationaliteIfNotSkirmish", "BitFieldPlayerIfNotSkirmish", "ForceLoadBitFieldNationalite")


def mission_nation_bits(game, map_name: str) -> list[int]:
    """For each cluster map of the shipped map `map_name` (one per scenario of it): the nations, as bits by
    Nationalite, whose units it loads in a game that is not a skirmish. [] when the data has none for that map."""
    key = f"/scenario/{map_name.lower()}/"
    out = []
    for top in sorted(game.objects):
        origin = game.objects[top].origin
        where = str(origin[0] if origin else top).replace("\\", "/").lower()
        if key not in where or "clustermap" not in where:
            continue
        bits = None
        for _path, part in _parts(game.objects[top]):
            found = [_int(part.props.get(k)) for k in MISSION_BITS if k in part.props]
            for v in found:
                bits = (bits or 0) | (v or 0)
        if bits is not None:
            out.append(bits)
    return out


def load_in_missions(game, nations) -> dict[int, tuple[int, int]]:
    """Have the per-nation packs of `nations` (Nationalite numbers) load in every campaign chapter and Operation too:
    each loader whose NotSkirmishPacks names nations' packs one by one gets SkirmishPacks[n] added when it lacks it,
    and so does a loader with one pack for several nations when that pack's mask leaves the nation out (Japan).
    A WithBoat pack counts as its nation's (Italy and D-Day list the US's with boats, which holds all of the plain
    one's models and five ships). {nation: (loaders it was added to, cluster maps they're in)}."""
    out = {}
    for n in sorted(set(nations)):
        count, maps = 0, set()
        for top, path, part in loaders(game):
            packs = part.props["SkirmishPacks"].items
            listed = part.props.get(NOT_SKIRMISH)
            if n >= len(packs) or not isinstance(packs[n], Ref) or not packs[n].target or not isinstance(listed, ListV):
                continue
            per_nation = {x.target for x in packs if isinstance(x, Ref) and x.target}
            have = {x.target.replace("WithBoat", "") for x in listed.items if isinstance(x, Ref) and x.target}
            if packs[n].target in have:
                continue  # the nation's there already
            # the packs listed that aren't one nation's own: the common pack, the one pack of several nations
            masks = [m for m in (_mask(game, t) for t in have - per_nation) if m is not None]
            if any(m >> n & 1 for m in masks):
                continue  # a pack of several nations' units serves this nation
            if not masks and not have & per_nation:
                continue  # no mask to go by and no nation named one by one: taken as one pack for every nation
            game.own_part(top, path).props[NOT_SKIRMISH].items.append(Ref(packs[n].target))  # (patch.Game.own)
            count += 1
            origin = game.objects[top].origin
            maps.add(origin[0] if origin else top)
        out[n] = (count, len(maps))
    return out


# The force bit above loads a nation's meshes, proxies and animations, but not its skeletons or card pictures: those
# load through one loader per nation in $/IA/Cluster, run for each nation in the match (skeletons through
# TClusterInitialisationExecuteSelectifSubClusters, which has no force bit in a skirmish). A model whose skeleton
# isn't loaded crashes the game when its unit is built (batch 1, 2026-10-01); a card picture that isn't, shows as a
# plain coloured box, on the card and on the unit's marker. So the nation's skeleton packs and card picture packs are
# added to every other nation's loaders too. Tested in the game (2026-10-02, batch 9e): a German Tiger and Ju 87 for
# the US, with no German player, are built, fight, show their pictures and can be selected. Their UsefulnessMask must
# NOT be widened: tagging the packs for every nation (batch 9c) left no unit selectable.
LOADER_TAGS = ("US", "GER", "UK", "FR", "ITA", "URSS", "JAP")  # the $/IA/Cluster loaders' names, by Nationalite
SKELETONS = "$/IA/Cluster/ClusterLoadPackSkeleton_{}"
CARDS = ("$/IA/Cluster/ClusterLoadTexturePack_Menu{}_Synchrone", "$/IA/Cluster/ClusterLoadTexturePack_Menu{}_Asynchrone")


def _packs(game, name, change: bool = False):
    """The Packs list of the loader `name`, or None. `change`: in the game's own copy of the loader, to add to it
    (patch.Game.own)."""
    obj = game.objects.get(name)
    if obj is not None and change:
        obj = game.own(name)
    v = obj.props.get("Packs") if obj is not None else None
    return v if isinstance(v, ListV) else None


def load_with_every_nation(game, nations) -> dict[int, tuple[int, int]]:
    """Have the skeleton and card picture packs of `nations` (Nationalite numbers) load in every nation's matches: each
    added to the other nations' loaders. {nation: (skeleton packs added, card picture packs added)}; (0, 0) when
    the nation has no loaders, or every loader has them already."""
    import copy
    own_skel, own_cards = {}, {}  # each nation's own packs, before any are added
    for tag in LOADER_TAGS:
        skel = _packs(game, SKELETONS.format(tag))
        own_skel[tag] = [x for x in skel.items if isinstance(x, Inline) and x.obj.copied_from is None] \
            if skel is not None else []
        own_cards[tag] = list(dict.fromkeys(x.target for c in CARDS for x in (_packs(game, c.format(tag)) or
                                                                               ListV([])).items if isinstance(x, Ref)))
    out = {}
    for n in sorted(set(nations)):
        if not 0 <= n < len(LOADER_TAGS):
            out[n] = (0, 0)
            continue
        own = LOADER_TAGS[n]
        skel_items, cards = own_skel[own], own_cards[own]
        added_skel = added_cards = 0
        for tag in LOADER_TAGS:
            if tag == own:
                continue
            into = _packs(game, SKELETONS.format(tag))
            if into is not None:
                have = {x.obj.copied_from for x in into.items if isinstance(x, Inline) and x.obj.copied_from}
                for x in skel_items:
                    if x.obj.origin is not None and x.obj.origin in have:
                        continue
                    c = copy.deepcopy(x.obj)
                    c.copied_from, c.origin = x.obj.origin, None
                    _packs(game, SKELETONS.format(tag), change=True).items.append(Inline(c))
                    added_skel += 1
            for loader_name in CARDS:
                into = _packs(game, loader_name.format(tag))
                if into is None:
                    continue
                have = {x.target for x in into.items if isinstance(x, Ref)}
                for target in cards:
                    if target not in have:
                        _packs(game, loader_name.format(tag), change=True).items.append(Ref(target))
                        have.add(target)
                        added_cards += 1
        out[n] = (added_skel, added_cards)
    return out
