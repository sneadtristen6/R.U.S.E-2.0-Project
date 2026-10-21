"""The computer players for the Studio, in our own code (LittleGroove's AI editor in RUSE-Mod-Manager had them first):
their profiles, the units they're keener to build, and the ruse cards (every player's).

A computer player in a battle has three profiles: Default, its difficulty and its personality (the two the game's
lobby picks). For each value the game takes the personality's when it isn't Default's, else the difficulty's when it
isn't Default's, else Default's; a value a profile doesn't list counts as 0, and a 0 that isn't Default's wins like any
other (the game's own code does this when the battle starts; battle_values gives the outcome). Like LittleGroove's
editor, the Studio changes the values each profile lists, and Add a value gives a profile one only Default lists.

The "units they're keener to build" entries (BONUS) apply in a battle whose game mode, the computer player's
difficulty and its personality are each in the entry's lists (an empty list matches any); the entry's BonusValue is
then added to the preference of each unit in UnitIDs (empty: every unit), on top of the profile's own preferences
(BonusUnitesAvions...). A computer player rates each unit by how far it sits below its most preferred one, so only the
differences between units count.

LittleGroove's editor also shows the computer players' scripts; that part isn't here.
"""
from __future__ import annotations

import re

LISTS, PROFILE, CARD, BONUS = "TIAProfilList", "TIAProfil", "TBluffCardDescriptor", "TAISpecificBonus"
KINDS = ("default", "difficulty", "personality")  # the profile list's three lists, in its order

PROFILE_GROUPS = (
    ("attack", ("AttaqueTempsActivation", "OffensiveNbMissionMax", "MissionFacteurLancementAttaque",
                "MissionFacteurEnoughToDestroy")),
    ("defense", ("DefenseDistanceMenace", "DefenseDistanceUrgent", "DefenseMaxUnitOnPosition", "DefenseNbMissionMax")),
    ("harass", ("HarcelementActif", "UpgradeActifPourHarcelement")),
    ("money", ("CashReserveTempsActivation", "PercentMoneyToReserveForBatimentAdmin", "PercentMoneyToUseForIdle",
               "DeviseBonusIA", "IncomeBonusIA", "NbBatimentAdministratifEnPlusAvantDesactivation")),
    ("depots", ("DepotNbEnPlusAvantDesactivation", "ValueDepotMinForTruckFactory", "MinutesLeftMinForTruckFactory",
                "NbDepotMinForTruckFactory", "NbUnitsDangerousDepot", "SeuilDistanceGroupeDepot",
                "SeuilDistanceTruckFactory")),
    ("production", ("NbMaxProductionForEnnemyUnit", "NbProdIdleInfanterie", "NbProdIdleTank", "NbProdIdleAntitank",
                    "NbProdIdleArti", "NbProdIdleDCA", "NbProdIdleChasseur", "NbProdIdleBomber",
                    "NbProdIdleChasseurBomber", "ProdIdleCanLaunchResearch")),
    ("weights", ("BonusUnitesAvions", "BonusUnitesArtillerie", "BonusUnitesExperimentales", "BonusUnitesRecherche",
                 "BonusBatimentOTF")),
    ("ruses", ("PourcentChanceUtiliserCarteManipAuDebut", "NbCarteDansLaReservePourLaDifficulte",
               "NbCarteDansLaReservePourLeProfil", "TempsActivationBatimentCamoufle")),
    ("retaliation", ("RepresailleFacteurUniteCombattante", "RepresailleFacteurUniteNonCombattante",
                     "TimeOutRepresailles")),
    ("intel", ("ProbaRepereFake", "TempsMemorisationUnitInvisible")),
)
PROFILE_PROPS = tuple(p for _group, props in PROFILE_GROUPS for p in props)
CARD_PROPS = ("LifeDuration", "ShowInMenu", "PositionInMenu")
BONUS_PROPS = ("BonusValue", "ConsiderStackAsOneEnnemy", "UnitIDs", "WarModes", "AIDifficulties", "AIProfiles")
NUCLEAR_MODE = 4  # the game mode the game's texts call "Nuclear mode" (DLC_GML_02)
# the game modes by number (WarModes), as the game's lobby names them: its own table, in this order
WAR_MODES = ("Btn1945", "Btn1942", "Btn1939", "DLC_GML_01", "DLC_GML_02")
CHOICE_PROPS = ("UnitIDs", "WarModes", "AIDifficulties", "AIProfiles")  # a bonus's lists: picked by name

# the game's own words for the AI's lobby, by text key
WORDS = {"ai": "NAME_AI", "difficulty": "BtnAIDiff", "profile": "BtnAIType", "nuclear": "DLC_GML_02"}
HINT = "AI_HPROF{}"  # personality n's line in the lobby ("This AI will use rush tactics to defeat you")


def _step(path: str) -> int | None:
    m = re.fullmatch(r"\w+\[(\d+)\]", path)
    return int(m.group(1)) if m else None


def configurations(ix) -> list[dict]:
    """[{kind, index, key, address}] of every entry in the game's profile list the game index has: Default, then the
    difficulties, then the personalities, each with its number in the lobby, its name's text key and its profile's
    address (None for one with no profile of its own: the lobby's "Random" personality)."""
    out = []
    for root in ix.of_class(LISTS):
        lists = sorted((_step(p), what) for p, kind, what in ix.uses(root["address"])
                       if kind == "object" and _step(p) is not None)
        for k, address in lists:
            if k >= len(KINDS):
                continue
            items = sorted((_step(p), what) for p, kind, what in ix.uses(address)
                           if kind == "object" and _step(p) is not None)
            for i, config in items:
                uses = ix.uses(config)
                out.append({"kind": KINDS[k], "index": i,
                            "key": next((w for p, kind, w in uses if p == "Name" and kind == "text"), None),
                            "address": next((w for p, kind, w in uses if p == "OverridenParams" and kind == "object"),
                                            None)})
    return out


def profiles(ix) -> list[dict]:
    """The configurations (above) that have a profile of their own: the ones the Studio shows."""
    return [c for c in configurations(ix) if c["address"]]


def battle_values(default: dict, difficulties: list[tuple], personalities: list[tuple]) -> dict:
    """What each value comes to in a battle, by the game's rule (above): {prop: {"difficulties": [(name, value)], the
    value with a personality that leaves it to the others, for each difficulty; "personalities": [(name, value)],
    the personalities whose own value wins on every difficulty (theirs isn't Default's)}}. `default`: {prop: value};
    `difficulties`, `personalities`: [(name, {prop: value})], a value not listed counting as 0."""
    return {prop: {"difficulties": [(name, values.get(prop, 0)) for name, values in difficulties],
                   "personalities": [(name, values.get(prop, 0)) for name, values in personalities
                                     if values.get(prop, 0) != d]}
            for prop, d in default.items()}


def card_key(o: dict) -> tuple:
    """A ruse card's place in the game's menu (PositionInMenu), then its place in the game's list."""
    slot = next((n for path, n, _t in o["values"] if path == "PositionInMenu"), None)
    return (slot if slot is not None else float("inf"), o["index"])
