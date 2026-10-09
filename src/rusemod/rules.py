"""Every rule the code applies about what R.U.S.E. itself does, and what it rests on (the owner's hard rule,
2026-10-02: never assume, never generalize). This file only FLAGS them: it changes nothing the apps do.

Each rule's `basis` is how we know it, strongest first:
  game            seen in a match (a test in docs/TESTS.md, a crash, the owner's report)
  studied         found by studying how the game works (the details are in the project's private notes)
  community       another modder's report, not checked by us
  generalization  "every shipped file does X, so the game needs X": a pattern, NOT proof
  unrecorded      nobody wrote down where it came from: an assumption
Only "game" counts as tested. The others are the list to check (GitHub issue 15). A "studied" rule's evidence says what
the study showed and what it left open; "partly" means part of the rule rests on it and the rest is still unknown.

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
    "circle-links": Rule(
        "A movement circle may have at most 128 links: a route through one with more crashes the game.",
        "game", "owner 2026-10-05: a unit built on the drained sea of his D-Day mod (Studio 0.9.7) crashed the game, "
                "its route through a circle with 196 links (the most on any shipped map is 37). The 128 is from "
                "studying how the game works; a circle with 129 to 195 links wasn't seen in a match"),
    "spawn-models": Rule(
        "A spawned unit whose nation's models the match doesn't load crashes the game at the start.",
        "game", "TESTS.md, owner 2026-10-01: 57 Japanese units spawned, no Japanese player: crash"),
    "nation-models": Rule(
        "A unit in another nation's army needs that nation's models loaded in every match.",
        "game", "T13 (crash when built, 2026-10-01); working in batches 9e and 10 (2026-10-02)"),
    "truck-flags": Rule(
        "Flags 62 (truck) and 63 (construction truck) on a unit that isn't a truck crash the game at match start.",
        "game", "62: rule test C (2026-10-02): flag 62 on the US Stuart stopped the game as the match started; the "
                "game's script puts every unit with flag 62 in the truck list as it builds the tech tree, and that "
                "step failed (DomesticNukes saw the same). 63: ProLution's report, not tested by us"),
    "ruses-per-sector": Rule(
        "More than two ruse cards on one sector crashes the game: a sector has room for two.",
        "game", "T37 (owner, 2026-10-06): with the most ruse cards per sector (MaxNbCardsPerZoneByAlliance) at 4, the "
                "game let him put a third on a sector and crashed; other modders' mods for more ruses per sector "
                "crashed too (the owner). Two was seen working; one and none weren't tried"),
    "skirmish-neutral-spawns": Rule(
        "A BATTLES (skirmish) scenario places only neutral spawns; a team's would not appear.",
        "studied", "the game's BATTLES script starts every map with no team list, so only neutral spawns are placed "
                   "(2026-10-02); every shipped BATTLES spawn is neutral too"),
    "road-network-one-piece": Rule(
        "A new road must join the map's road network; supply routes between two pieces fail.",
        "generalization", "every shipped map's road network is one piece; how trucks route between two pieces "
                          "wasn't found in the study (2026-10-02): an in-game test, after roads"),
    "weapon-salvo": Rule(
        "A weapon's salvo number must be one the weapon defines, or the game stops with a 'Quit game?' box.",
        "studied", "the game checks each mounted weapon's salvo number as units load and shows that box when the "
                   "salvo isn't defined (2026-10-01 audit, checked again 2026-10-02)"),
    "unit-nation-range": Rule(
        "Nationalite is 0 to 6; another number corrupts the units as the game loads them.",
        "studied", "the game keeps exactly 7 per-nation unit lists and uses Nationalite to pick one without a range "
                   "check (2026-10-01 audit, checked again 2026-10-02); what breaks after that isn't known"),
    "unit-id-zero": Rule(
        "A unit with DescriptorId 0 (or none) is left out of its nation's list.",
        "studied", "partly: the game skips id 0 when it lists units by id and by nation (the nation list feeds the "
                   "in-game encyclopedia), and an order for such a unit reaches the game's scripts with no unit, an "
                   "error (2026-10-02); what the player sees then isn't known"),
    "unit-id-clash": Rule(
        "Two units with one DescriptorId: orders for one build the other.",
        "studied", "the game keeps the first unit with an id and skips the next without a word; production orders "
                   "name the unit by id (2026-10-01 audit, checked again 2026-10-02)"),
    "unit-research-parent": Rule(
        "A unit researched from (UpgradeRequire) a unit that's missing or another nation's: the match never loads.",
        "game", "2026-10-09 era test 4: the loading screen ran on for minutes with no crash while the game built the "
                "nations' research trees; 5 new units there were researched from other nations' units (the details "
                "are in the project's private notes). Test 5, the same units with those links deleted, loaded at once "
                "(owner: 'load it in instantly'); test 6, era units researched from their own army's units and "
                "chained (T-80 -> T-90M), loaded and researched as set"),
    "unit-five-dates": Rule(
        "ProductionPrice and ShowInMenu have 5 items, one per battle date; fewer makes the unit free or hidden.",
        "studied", "partly: the game's scripts make a missing price 0 and a missing menu item hidden, with the length "
                   "checked (2026-10-02); a read past the list's end reported by the 2026-10-01 audit isn't checked "
                   "again; every shipped unit has 5 items in both"),
    "flag-59": Rule(
        "Flag 59 (paratroop drop) crashes the game on a unit that isn't an aircraft, or on one with nothing to drop.",
        "studied", "the game's interface reads a flag-59 unit as an aircraft and reads what it drops without checking "
                   "either (2026-10-02); which click reaches it isn't known; the 10 shipped units with flag 59 are "
                   "aircraft with a UniteTransportee"),
    "start-ground": Rule(
        "A starting point must stand where a ground unit can (not water, a cliff or a block for every unit), or the "
        "game builds that player's HQ wherever it finds room. A wood is fine.",
        "game", "woods: the owner (2026-10-02): an HQ in a wood works, and supply trucks drive through woods (only "
                "tanks and other vehicles with flags 11/21/55 are kept out). Water and cliffs: the game's script builds "
                "the first HQ where the placer says without asking whether it found room (studied); how far away it "
                "lands isn't seen"),
    "seats-per-team": Rule(
        "Each player needs a starting point of their team, or that player starts with no HQ and no units.",
        "game", "rule test A (2026-10-02, Twilight of the Gods with team 2 one point short): the team's first slot got "
                "the base and the second started with nothing; no crash, no message, not defeated at once. The "
                "game's scripts do the same (no point left: no first HQ, units or camera)"),
    "players-most": Rule(
        "A map takes at most 8 players: the lobby shows at most 8 seats.",
        "game", "rule test B (2026-10-02, Strategists set to 10): the lobby says 'Number of players 10' but shows 8 "
                "seats, and the match loads with 8, no crash. More than 8 would need a new lobby screen; no limit "
                "was found in the game's scripts"),
    "spawn-class": Rule(
        "A spawn's class must be one the game's own spawns use, or loading the map fails.",
        "studied", "partly: a class name the game's unit list doesn't have raises an error while the map loads "
                   "(2026-10-02); our second check (other class paths must be ones shipped spawns use) is stricter than "
                   "the game, which takes any path that exists"),
    "delete-unit-class": Rule(
        "Deleting a unit the game's Python unit list names makes the game fail to load units.",
        "studied", "every class in the game's unit list looks its unit up by name as the list loads, and a missing "
                   "one raises an error, so the whole list fails (2026-10-02)"),
    "newmap-names": Rule(
        "A new map's name must not be one the game has, nor start with flat_ (the test maps).",
        "generalization", "the shipped map names; flat_ maps are the game's test maps"),
    "scenery-md5": Rule(
        "The game refuses a scenery file whose MD5 is wrong.",
        "studied", "the game checks a map's scenery file against the 16 bytes at its start and stops with a "
                   "'Quit game?' box when they differ (2026-10-02); LittleGroove's rule, and the shipped files match it"),
    "scenery-grid": Rule(
        "The game draws nothing placed outside a map's scenery grid.",
        "studied", "up close, the game draws only the grid's cells that hold objects, and none outside it (2026-10-01 "
                   "audit, checked again 2026-10-02); the far tiers rest on the audit alone"),
    "video-vp9-vorbis": Rule(
        "The game plays WebM videos with a VP9 picture and Vorbis sound, and no other kind.",
        "studied", "the game's video player takes WebM only and names only VP9 pictures and Vorbis sound (2026-10-08); "
                   "all 96 shipped videos are such (the campaign's long films with up to 8 sound tracks); another "
                   "kind not tried in the game"),
    "shader-model-3": Rule(
        "The game's shaders are compiled for shader model 3 (vs_3_0 and ps_3_0).",
        "generalization", "all 1,806 shaders in the shipped shader file are vs_3_0 or ps_3_0 (2026-10-08); whether the "
                          "game takes another kind isn't known"),
}


def untested() -> list[tuple[str, Rule]]:
    """The rules never seen in the game, weakest basis first: the list to check."""
    order = {b: i for i, b in enumerate(reversed(BASES))}
    return sorted(((k, r) for k, r in RULES.items() if not r.tested), key=lambda kr: order[kr[1].basis])
