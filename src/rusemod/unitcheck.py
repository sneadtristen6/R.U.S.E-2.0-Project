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
                    mesh pack, MeshSkirmish_<nation>.spk, beside the common one): a unit whose model is only in
                    another nation's pack has no model, or crashes the game, in every other match.

patch.Engine asks for the first five at the end of every run and reports what the mods made wrong (what the game's
data already had is left alone); build.build_pack asks for the models, which need ZZ_Win.dat.
"""
from __future__ import annotations

from .patch import Inline, ListV, Num, Ref, Text, _parts, _parts_in
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
        out.append(("error", NATION, f"{NATION} {n} isn't a nation: it must be 0 to 6 ({names}); the game has room "
                                     f"for exactly seven nations' units, and another number corrupts it as it loads"))
    if _int(obj.props.get(ID)) == 0:
        out.append(("error", ID, f"{ID} 0 isn't an id: the game leaves the unit out of its nation's list and can't "
                                 f"build it; give it a number no other unit has"))
    for prop, what in (("ProductionPrice", "the game makes the unit free at the battle dates it has no price for"),
                       ("ShowInMenu", "the game hides the unit at the battle dates it has no item for, and reads a "
                                      "list of 1 or 2 items past its end")):
        v = obj.props.get(prop)
        if v is None:
            continue
        if not isinstance(v, ListV):
            out.append(("error", prop, f"{prop} isn't a list; it needs {DATES} items, one per battle date"))
        elif len(v.items) != DATES:
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
            out[name] = (f"{ID} {v} is also {others[0]}'s: the game keeps one unit per id, so this one is left out of "
                         f"its nation's list and orders for it build {others[0]}; give it a number no other unit has "
                         f"(a copy gets one by itself when it doesn't set {ID})")
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
def model_files(obj) -> set[str]:
    """The model files (.ase2ndfbin) a unit's own Gfx parts name, lower case with backslashes, as mesh packs list
    them."""
    out = set()
    for prop, v in obj.props.items():
        if not prop.startswith("Gfx"):
            continue
        for _path, part in _parts_in(v, prop):
            for x in part.props.values():
                if isinstance(x, Text) and x.value.lower().endswith(MODEL):
                    out.add(x.value.lower().replace("/", "\\"))
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


def missing_models(obj, packs: dict, allowed=frozenset()) -> dict[str, list[str]]:
    """The models of a unit that aren't loaded for its nation: {model: [the nations whose packs have it]}. Models in
    no skirmish pack, and (model, nation) pairs in `allowed` (the game's own units already have them), don't count."""
    n = nation_of(obj)
    if not 0 <= n < len(PACK_TAGS):
        return {}
    have = packs[PACK_TAGS[n]] | packs["common"]
    out = {}
    for model in sorted(model_files(obj)):
        if model in have or (model, n) in allowed:
            continue
        where = [NATIONS[i] for i, tag in enumerate(PACK_TAGS) if model in packs[tag]]
        if where:
            out[model] = where
    return out
