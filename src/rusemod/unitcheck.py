"""What a unit needs to be for the game to take it, beyond what the data's types say: the build's checks on the units
(and their weapons) a mod made or changed. Each rule is one the game's own 468 unit descriptors all keep.

  DescriptorId      the game keeps one unit per id, across every kind of unit: a unit whose id is 0, or another
                    unit's, is left out of its nation's list, and orders for it build the other one (or nothing).
  Nationalite       0 to 6 (0 US, 1 Germany, 2 UK, 3 France, 4 Italy, 5 USSR, 6 Japan; not written = 0): the game
                    has room for exactly seven nations' unit lists, and another number corrupts it as it loads.
  ProductionPrice,  5 items, one per battle date: at a date with no item the game makes the unit free, or hides it
  ShowInMenu        (and a ShowInMenu of 1 or 2 items is read past its end).
  InitialFlagSet    rusemod.unitflags: flags that belong to one kind of unit.
  salvos            a weapon's mounted weapons with a SalveNumber other than -1 need 0 to 4, and the weapon's
                    Salves[SalveNumber] above 0; otherwise the game stops at load with a "Quit game ?" box.
  models            a nation's unit models are loaded only in a match where a player has that nation (its skirmish
                    mesh pack, MeshSkirmish_<nation>.spk, beside the common one), or one the cluster maps' loaders
                    force (load_everywhere): a unit whose model is only in another nation's pack would have no model,
                    or crash the game, in every other match, so the build has that nation's packs load in every
                    skirmish, and in every campaign chapter and Operation (load_in_missions).

patch.Engine asks for the first five at the end of every run and reports what the mods made wrong (what the game's
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
    return out + unitflags.problems(obj)


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
        for top, _path, part in loaders(game):
            if n >= len(part.props["SkirmishPacks"].items):
                continue
            old = part.props.get(FORCE)
            bits = int(old.value) if isinstance(old, Num) else 0
            if not bits >> n & 1:
                part.props[FORCE] = Num("uint32", Decimal(bits | 1 << n))
            count += 1
            origin = game.objects[top].origin
            maps.add(origin[0] if origin else top)
        out[n] = (count, len(maps))
    return out


# Outside a skirmish (a campaign chapter, an Operation) a loader loads its NotSkirmishPacks and nothing else: the force
# bit above does nothing there. 30 of the 85 cluster maps list only the nations their mission plays, one pack each
# (Holland's chapters: the common pack, US, Germany and UK), so another nation's unit, spawned there or bought, has no
# model (a player's build spawning French units, Holland, 2026-10-03: the game crashed loading the mission). The other
# 55 list one pack of every nation's units (PackMesh_All) and need nothing.
NOT_SKIRMISH = "NotSkirmishPacks"


def load_in_missions(game, nations) -> dict[int, tuple[int, int]]:
    """Have the per-nation packs of `nations` (Nationalite numbers) load in every campaign chapter and Operation too:
    each loader whose NotSkirmishPacks names nations' packs one by one gets SkirmishPacks[n] added when it lacks it.
    A WithBoat pack counts as its nation's (Italy and D-Day list the US's with boats, which holds all of the plain
    one's models and five ships). {nation: (loaders it was added to, cluster maps they're in)}."""
    out = {}
    for n in sorted(set(nations)):
        count, maps = 0, set()
        for top, _path, part in loaders(game):
            packs = part.props["SkirmishPacks"].items
            listed = part.props.get(NOT_SKIRMISH)
            if n >= len(packs) or not isinstance(packs[n], Ref) or not packs[n].target or not isinstance(listed, ListV):
                continue
            per_nation = {x.target for x in packs if isinstance(x, Ref) and x.target}
            have = {x.target.replace("WithBoat", "") for x in listed.items if isinstance(x, Ref) and x.target}
            if not have & per_nation or packs[n].target in have:
                continue  # one pack for every nation (or none named one by one), or the nation's there already
            listed.items.append(Ref(packs[n].target))
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


def _packs(game, name):
    obj = game.objects.get(name)
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
                    into.items.append(Inline(c))
                    added_skel += 1
            for loader_name in CARDS:
                into = _packs(game, loader_name.format(tag))
                if into is None:
                    continue
                have = {x.target for x in into.items if isinstance(x, Ref)}
                for target in cards:
                    if target not in have:
                        into.items.append(Ref(target))
                        have.add(target)
                        added_cards += 1
        out[n] = (added_skel, added_cards)
    return out
