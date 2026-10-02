"""Every rule the code applies about what R.U.S.E. itself does, and what it rests on (the owner's hard rule,
2026-10-02: never assume, never generalize). This file only FLAGS them: it changes nothing the apps do.

Each rule's `basis` is how we know it, strongest first:
  game            seen in a match (a test in docs/TESTS.md, a crash, the owner's report)
  studied         found by studying how the game works (the details are in the project's private notes)
  community       another modder's report, not checked by us
  generalization  "every shipped file does X, so the game needs X": a pattern, NOT proof
  unrecorded      nobody wrote down where it came from: an assumption
Only "game" counts as tested. The others are the list to check (docs/UNTESTED.md, and the GitHub issue made from it).

tests/test_rules.py is the guard: every refusal in the code whose words are about the game names its rule here
(`# rule: <id>` on its line or the one before) or says why it isn't one (`# not a game rule: <why>`); every rule has
a basis and its evidence; every rule here is used. A refusal can't come in without being flagged.
"""
from __future__ import annotations

from dataclasses import dataclass

BASES = ("game", "studied", "community", "generalization", "unrecorded")


@dataclass(frozen=True)
class Rule:
    what: str        # the rule, in a sentence
    basis: str       # one of BASES
    evidence: str    # where: the test, the notes, the report, or the pattern and how many files show it

    @property
    def tested(self) -> bool:
        return self.basis == "game"


RULES: dict[str, Rule] = {
    "ground-reach": Rule(
        "Movement graphs must be one piece: a move order to ground units can't reach crashes the game.",
        "game", "TESTS.md bridges, owner 2026-09-30 18:43: crashed on a move order (the empty-route crash)"),
    "spawn-models": Rule(
        "A spawned unit whose nation's models the match doesn't load crashes the game at the start.",
        "game", "TESTS.md, owner 2026-10-01: 57 Japanese units spawned, no Japanese player: crash"),
    "nation-models": Rule(
        "A unit in another nation's army needs that nation's models loaded in every match.",
        "game", "T13 (crash when built, 2026-10-01); working in batches 9e and 10 (2026-10-02)"),
    "truck-flags": Rule(
        "Flags 62 (truck) and 63 (construction truck) on a unit that isn't a truck crash the game at match start.",
        "community", "DomesticNukes: flag 62 on a Stuart crashed the game (his test); ProLution: the same for 63"),
    "skirmish-neutral-spawns": Rule(
        "A BATTLES (skirmish) scenario places only neutral spawns; a team's would not appear.",
        "generalization", "every spawn in the shipped BATTLES scenarios is neutral (camp -1)"),
    "road-network-one-piece": Rule(
        "A new road must join the map's road network; supply routes between two pieces fail.",
        "generalization", "every shipped map's road network is one piece"),
    "weapon-salvo": Rule(
        "A weapon's salvo number must be one the weapon defines, or the game stops with a 'Quit game?' box.",
        "unrecorded", "added in the 2026-10-01 build audit; no test or study written down"),
    "unit-nation-range": Rule(
        "Nationalite is 0 to 6; another number corrupts the units as the game loads them.",
        "unrecorded", "added in the 2026-10-01 build audit; no test or study written down"),
    "unit-id-zero": Rule(
        "A unit with DescriptorId 0 (or none) is left out of its nation's list.",
        "unrecorded", "added in the 2026-10-01 build audit; no test or study written down"),
    "unit-id-clash": Rule(
        "Two units with one DescriptorId: orders for one build the other.",
        "unrecorded", "added in the 2026-10-01 build audit; no test or study written down"),
    "unit-five-dates": Rule(
        "ProductionPrice and ShowInMenu have 5 items, one per battle date; fewer makes the unit free or hidden.",
        "generalization", "every shipped unit has 5 items in both lists"),
    "flag-59": Rule(
        "Flag 59 (paratroop drop) crashes the game on a unit that isn't an aircraft, or on one with nothing to drop.",
        "generalization", "the 10 shipped units with flag 59 are aircraft with a UniteTransportee"),
    "start-ground": Rule(
        "A starting point must stand where vehicles can go.",
        "generalization", "every shipped starting point stands on ground vehicles use"),
    "seats-per-team": Rule(
        "Each player needs a starting point of their team, or the game can't seat them.",
        "unrecorded", "added with the player counts (2026-10-01); no test or study written down"),
    "players-most": Rule(
        "A map takes at most 8 players.",
        "generalization", "the lobby screen we read (outgame .gfx) has layouts for at most 8 seats"),
    "spawn-class": Rule(
        "A spawn's class must be one the game's own spawns use, or loading the map fails.",
        "unrecorded", "added in the 2026-10-01 build audit; no test or study written down"),
    "delete-unit-class": Rule(
        "Deleting a unit the game's Python unit list names makes the game fail to load units.",
        "unrecorded", "added with the unit list (decision 23); no test written down"),
    "newmap-names": Rule(
        "A new map's name must not be one the game has, nor start with flat_ (the test maps).",
        "generalization", "the shipped map names; flat_ maps are the game's test maps"),
    "scenery-md5": Rule(
        "The game refuses a scenery file whose MD5 is wrong.",
        "community", "LittleGroove's rule for .scenario files; checked by us only that the shipped files match it"),
    "scenery-grid": Rule(
        "The game draws nothing placed outside a map's scenery grid.",
        "unrecorded", "no test or study written down"),
}


def untested() -> list[tuple[str, Rule]]:
    """The rules never seen in the game, weakest basis first: the list to check."""
    order = {b: i for i, b in enumerate(reversed(BASES))}
    return sorted(((k, r) for k, r in RULES.items() if not r.tested), key=lambda kr: order[kr[1].basis])
