"""Unit flags (InitialFlagSet) that crash the game, so a build stops them.

62 (truck) and 63 (construction truck) on anything that isn't a truck crash R.U.S.E. at match start: DomesticNukes and
his Claude put 62 on a Stuart in the game (2026), and ProLution found the same for 63. The game's trucks are its 18
TTruckDescriptor units, and every one of them carries 62; no other unit of the game carries 62 or 63. A truck is a
TTruckDescriptor whatever its other flags: 44 (logistique), which every truck carries too, does nothing on a tank, so it
doesn't make one a truck, and taking it off a truck doesn't make that truck anything else.

The patch engine asks at the end of every run (patch.Engine._truck_flags), for each unit a mod made or whose flags a
mod changed, and only about the flags a mod gave it: the game's own units and flags aren't checked. What every flag
does is in labels.toml [flags].
"""
from __future__ import annotations

from .patch import ListV, Num

PROP = "InitialFlagSet"
TRUCK_CLASS = "TTruckDescriptor"
TRUCK_ONLY = {62: "truck", 63: "construction truck"}


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
