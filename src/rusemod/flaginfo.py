"""The flag guide: what every unit flag (InitialFlagSet, 0-104) is, what it does in the game, how to use it, how sure
we are and whether it's dangerous (flaginfo.toml), and what's wrong with one unit's flags (judge), so the Studio can
explain each flag and stop or warn about a set before the game is started (the owner, 2026-10-15: "the studio has to
do all the thinking for the modder ... And it has to tell the modder what the thinking is going to be doing").

The build stops on the same crashes (rusemod.unitflags, patch.Engine._truck_flags): 62 and 63 off a truck, 99 without
100 on a plane with weapons, 59 off a plane or without the unit it drops. The rest are warnings: what studying the game
expects to break a unit, not seen in the game yet."""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

from .unitflags import AIRCRAFT_CLASS, FIGHTER, SCOUT, TRUCK_CLASS, TRUCK_ONLY

GROUPS = ("kind", "combat", "movement", "sight", "player", "preview", "state", "unused")
SURE = ("tried", "units", "expected", "state", "unused")
BUILDING_CLASS = "TBatimentDescriptor"
INFANTRY_CLASSES = ("TInfanterieDescriptor",)


@lru_cache(maxsize=1)
def guide() -> dict[int, dict]:
    """{flag: {group, sure, what, does, use, danger, danger_why}} for 0-104 (danger "" when none)."""
    raw = tomllib.loads(Path(__file__).with_name("flaginfo.toml").read_text(encoding="utf-8"))
    return {int(n): {"group": e["group"], "sure": e["sure"], "what": e["what"], "does": e["does"], "use": e["use"],
                     "danger": e.get("danger", ""), "danger_why": e.get("danger_why", "")} for n, e in raw.items()}


def judge(cls: str, flags, had=frozenset(), armed: bool = False, drops: bool = True) -> list[dict]:
    """What's wrong with a unit of class `cls` carrying `flags`: [{"level": "error" | "warning", "flag", "why"}].
    Errors are what crashes the game (the build stops on them too); warnings what's expected to break the unit.
    `had`: the flags it carried before any mod (the game's unit, or the one a new unit copies): a crash the game's
    own data already has isn't the mod's doing. `armed`: it has a weapon. `drops`: a plane with a UniteTransportee."""
    flags, had = set(flags), set(had)
    plane, truck = cls == AIRCRAFT_CLASS, cls == TRUCK_CLASS
    building, infantry = cls == BUILDING_CLASS, cls in INFANTRY_CLASSES
    out = []

    def say(level, n, why):
        out.append({"level": level, "flag": n, "why": why})
    if not truck:
        for n, what in TRUCK_ONLY.items():
            if n in flags and n not in had:
                say("error", n, f"Flag {n} ({what}) crashes the game at match start on anything that isn't a truck. "
                                f"Take it off.")
    if plane and SCOUT in flags and FIGHTER not in flags and SCOUT not in had and armed:
        say("error", SCOUT, f"Flag {SCOUT} (recon plane) on a plane with weapons, without flag {FIGHTER} (fighter), "
                            f"crashes the game when the plane is sent to attack: it behaves as a scout, and a scout "
                            f"can't attack. Add {FIGHTER} too (an armed scout), or take {SCOUT} off.")
    if 59 in flags and not plane:
        say("error", 59, "Flag 59 (paratroop transport) crashes the game on anything that isn't a plane. Take it off.")
    elif 59 in flags and not drops:
        say("error", 59, "Flag 59 (paratroop transport) on a plane with no UniteTransportee (the unit it drops) "
                         "crashes the game. Set UniteTransportee, or take 59 off.")
    if 2 in flags and not plane:
        say("warning", 2, "Flag 2 (aircraft) on a unit that isn't a plane: the game will try to build it at an "
                          "airfield's control tower, which is expected to stop the game with a script error.")
    if plane and 2 not in flags:
        say("warning", 2, "A plane without flag 2 (aircraft) isn't moved or ordered like one. Every plane of the game "
                          "has it.")
    if not building:
        if 4 in flags:
            say("warning", 4, "Flag 4 (building) on a unit is expected to freeze it: buildings don't move or think.")
        if 49 in flags:
            say("warning", 49, "Flag 49 (paratroopers in the air) on a unit is expected to freeze it on the ground.")
        for n in (6, 76):
            if n in flags and n not in had:
                say("warning", n, f"Flag {n} makes a unit stand where it is, like a building or the game's ships: "
                                  f"expected to stop it moving.")
    if 42 in flags and not infantry and 42 not in had:
        say("warning", 42, "Flag 42 (infantry) on a vehicle is expected to stop the game with a script error when it "
                           "dies (it dies the infantry way).")
    if 43 in had and 43 not in flags:
        say("warning", 43, "Without flag 43 the unit isn't counted by its team: missions and the computer player won't "
                           "see it. Put it back.")
    if 22 in had and 22 not in flags:
        say("warning", 22, "Without flag 22 the player can't give the unit orders.")
    if truck and 62 not in flags:
        say("warning", 62, "A truck without flag 62 isn't handled as a truck, so it may carry no supplies. Every truck "
                           "of the game has it.")
    for n in sorted(f for f in flags if not 0 <= f <= 104):
        say("warning", n, f"Flag {n} is outside 0 to 104: the game ignores it.")
    return out
