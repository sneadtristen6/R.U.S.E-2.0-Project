"""Unit flags (InitialFlagSet) that crash the game, so a build stops them.

62 (truck) and 63 (construction truck) on anything that isn't a truck crash R.U.S.E. at match start: DomesticNukes and
his Claude put 62 on a Stuart in the game (2026), and ProLution found the same for 63. The game's trucks are its 18
TTruckDescriptor units, and every one of them carries 62; no other unit of the game carries 62 or 63. A truck is a
TTruckDescriptor whatever its other flags: 44 (logistique), which every truck carries too, does nothing on a tank, so it
doesn't make one a truck, and taking it off a truck doesn't make that truck anything else.

The patch engine asks at the end of every run (patch.Engine._truck_flags), for each unit a mod made or whose flags a
mod changed, and only about the flags a mod gave it: the game's own units and flags aren't checked. What every flag
does is in labels.toml [flags].

Other flags belong to one kind of unit too (`problems`, asked through rusemod.unitcheck), as the game's own units have
them: flag 2 (avion) is on all 63 aircraft (TAvionDescriptor) and nothing else, and moves and orders a unit as an
aircraft; flag 59 (transport_parachutiste) is on 10 aircraft, each with the unit it drops in UniteTransportee, which
the game reads without asking whether there is one; every truck carries 62, which makes it carry supplies. The game
only reads flags 0 to 104: a higher number does nothing.
"""
from __future__ import annotations

from .patch import ListV, Num, Ref

PROP = "InitialFlagSet"
TRUCK_CLASS = "TTruckDescriptor"
TRUCK_ONLY = {62: "truck", 63: "construction truck"}
AIRCRAFT_CLASS = "TAvionDescriptor"
DROPS = "UniteTransportee"  # the unit an aircraft with flag 59 drops
LAST_FLAG = 104             # the game reads flags 0..104


def numbers(value) -> set[int]:
    """The numbers in a flag list (a ListV), in a list of them, or one number (a Num); nothing for anything else."""
    items = value.items if isinstance(value, ListV) else value if isinstance(value, list) else [value]
    return {int(n.value) for n in items if isinstance(n, Num)}


def is_truck(obj) -> bool:
    """A truck: a TTruckDescriptor, like the game's 18 trucks."""
    return obj.cls == TRUCK_CLASS


def truck_flags(obj) -> set[int]:
    """The truck-only flags (62, 63) a unit (a patch.Obj) carries."""
    return numbers(obj.props.get(PROP)) & set(TRUCK_ONLY)


def crashes(obj, had=frozenset()) -> list[str]:
    """Why this unit (a patch.Obj) would crash the game at match start: a sentence for each truck-only flag it carries
    without being a truck. Nothing for a truck, or for a unit without those flags. `had`: the ones it carried before
    any mod (the game's own data), which don't count."""
    if is_truck(obj):
        return []
    found = truck_flags(obj) - set(had)
    return [f"flag {n} ({what}) on a unit that isn't a truck crashes R.U.S.E. at match start; take it off (only "
            f"trucks, {TRUCK_CLASS} units, can carry it)" for n, what in TRUCK_ONLY.items() if n in found]


def problems(obj) -> list[tuple[str, str, str]]:
    """What else is wrong with a unit's flags (a patch.Obj with InitialFlagSet), beyond the truck-only ones:
    [(level, property, why)]. Errors for what crashes the game, warnings for what only works wrong."""
    if PROP not in obj.props:
        return []
    flags, out = numbers(obj.props.get(PROP)), []
    aircraft = obj.cls == AIRCRAFT_CLASS
    if 59 in flags and not aircraft:
        # rule: flag-59
        out.append(("error", PROP, f"flag 59 (transport_parachutiste) on a unit that isn't an aircraft crashes R.U.S.E. "
                                   f"when the game looks for the paratroopers it drops; take it off (only aircraft, "
                                   f"{AIRCRAFT_CLASS} units with a {DROPS}, can carry it)"))
    elif 59 in flags and not (isinstance(obj.props.get(DROPS), Ref) and obj.props[DROPS].target):
        # rule: flag-59
        out.append(("error", DROPS, f"flag 59 (transport_parachutiste) on an aircraft with no {DROPS} crashes R.U.S.E. "
                                    f"when the game looks for the paratroopers it drops; set {DROPS} to the unit it "
                                    f"drops, or take the flag off"))
    if 2 in flags and not aircraft:
        out.append(("warning", PROP, "flag 2 (avion) on a unit that isn't an aircraft makes the game move and order it "
                                     "like an aircraft; take it off"))
    if aircraft and 2 not in flags:
        out.append(("warning", PROP, "an aircraft without flag 2 (avion) isn't moved or ordered like one; every "
                                     "aircraft of the game carries it: put it back"))
    if is_truck(obj) and 62 not in flags:
        out.append(("warning", PROP, "a truck without flag 62 (truck) isn't handled as a truck, so it may carry no "
                                     "supplies; every truck of the game carries it: put it back"))
    for n in sorted(f for f in flags if not 0 <= f <= LAST_FLAG):
        out.append(("warning", PROP, f"flag {n} is outside 0 to {LAST_FLAG}, so the game ignores it; take it off"))
    return out
