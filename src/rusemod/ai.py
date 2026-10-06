"""The computer players, as LittleGroove's AI editor (RUSE-Mod-Manager) offers them, for the Studio: their profiles,
the units they're keener to build, and the ruse cards (every player's).

A computer player in a battle has three profiles: Default, its difficulty and its personality (the two the game's
lobby picks). For each value the game takes the personality's when it isn't Default's, else the difficulty's when it
isn't Default's, else Default's; a value a profile doesn't list counts as 0 (not tried in the game yet). Like
LittleGroove's editor, the Studio changes the values each profile lists: a value it doesn't list would need its type
written out in the mod, which the Studio's mod file doesn't keep.

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


def card_key(o: dict) -> tuple:
    """A ruse card's place in the game's menu (PositionInMenu), then its place in the game's list."""
    slot = next((n for path, n, _t in o["values"] if path == "PositionInMenu"), None)
    return (slot if slot is not None else float("inf"), o["index"])
