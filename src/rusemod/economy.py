"""The game's economy for the Studio, in our own code (LittleGroove's Economy editor had it first): starting money
and income, the depots' supply trucks, production limits, the ruse cards, and the computer players' production and
decoys. The game has these values twice (its usual game modes, and the Nuclear mode's: not tried in the game yet), so
the Studio changes both copies from one value, each reached by the file it's in, and a change holds in every mode; or
one copy alone, where the two are shown apart (the owner, 2026-10-17: "separate normal and nuclear for sure").

Since 2026-10-22 every other value of these constants is offered too, as the game rules (battle, population, movement,
fighting and the rest; the owner: "all game rules keep it nice and organized though"). Whether the PC game holds
players to the population cap isn't tried yet.

Depots, admin buildings and truck factories themselves (price, build time, strength) are buildings: the Studio's
Units page changes them. The most ruse cards on one sector isn't offered: more than two crashes the game
(rusemod.rules, ruses-per-sector, which the build refuses from any mod), and the owner wants it left as the game has it
for now (2026-10-06).
"""
from __future__ import annotations

CLASS = "TTunableConstante"
COPIES = {"normal": "gdconstanteoriginal", "atomic": "gdconstanteatomic"}  # game mode -> part of its file's name
TARGETS = {mode: f'@{CLASS}[file="{part}"]' for mode, part in COPIES.items()}  # how a mod reaches each copy

_SIZES = (1, 2, 3, 4)  # the ruse cards' values come once per size of alliance (1 to 4 players on a side)
GROUPS = (
    ("money", ("QteDeviseInitiale", "TempsGenAutoDevises", "QuantiteGenAutoDevises", "StockDeviseSupplementaireFacile")),
    ("supply", ("QteDeviseParCamion", "NbCamionParConvoi", "TempsENtreDeuxConvois", "TempsENtreDeuxCamionsEnConvoiMin",
                "TempsENtreDeuxCamionsEnConvoiMax", "RatioForDepotNearlyDepleted")),
    ("production", ("MinProductionTime", "MaximumBatimentProduction", "MaxProductionQueueSize",
                    "MaxBatimentAndTechnoProductionSimultaneous", "VirtualFactoryQueueMaximumSlot",
                    "NbAvionsParAeroport")),
    ("cards", ("NbMaxCardsInPool",
               *(f"NbInitialCardsInPoolForAllianceTaille_{n}" for n in _SIZES),
               *(f"PaliersTempsToChooseNewCardForAllianceTaille_{n}" for n in _SIZES))),
    # the game rules (the owner, 2026-10-22: "all game rules keep it nice and organized though"): every other value of
    # the game's constants, by what it is about
    ("battle", ("TimeLimitTable", "TimeMaxForSurrender", "TimeBetweenBuildingDestructionForSurrender",
                "EliminationWarningsDuration", "DureeDecompteLaunchGameMulti")),
    ("population", ("PopCapPerPlayer", "PopCapPerAlliance", "PopCapTotal")),
    ("movement", ("AccelerationSurRoute", "AccelerationSurRouteCamion", "LargeurRoute", "DecalageRoute",
                  "TailleMinimumDeRoute", "AngleArrierePourMarcheArriere", "DistancePourDeclencherMarcheArriere",
                  "DistancePourDeclencherMarcheArriereEnCombat", "LongueurDeDetectionPourEvitement", "DistanceCoherence",
                  "WorldBorderMarginForMouvement", "WorldBorderMarginForOrder", "MultiplicateurVitesseDeroute",
                  "TempsDeploiement", "MorphTimeToGoToAttackPosition", "MorphTimeToGoToMovePosition")),
    ("firing", ("DistToOpenFire", "DistanceFriendlyFire", "DistanceMaxPourAttackWhileMoving",
                "MultiplicateurDispersionQdTireurEnMouvement", "ToleranceTirTouche",
                "WaitingTimeToFocusTargetWithMainOrientation", "WaitingTimeToFocusTargetWithMainOrientationWhenShootable",
                "PorteeMinArmeEstConsidereCommeArtillerie", "LongueurParcourueBombe", "CombatZoneRadius",
                "RF_TypeRapportDeForceFeedback", "ActivateShootToKillDCA", "SeuilDecrocheDCA",
                "DistanceToAddToEnnemiDectectionForAAWeapon", "DistanceToAddToEnnemiDectectionForOtherWeapon",
                "DistanceInfanterieEnnemiDectection")),
    ("reactions", ("DistanceMaxPourAttaquerCibleComportementAuto", "DistancePourchasse", "DistancePourchasseIncrement",
                   "DistanceZoneAlerte", "DistanceMaxAParcourirPourSupportAttaqueEnnemi",
                   "TempsDepuisDernierDegatPourConsiderAttaqueEnnemi", "DistanceRepliQuandTireurInvisible",
                   "TempsEntreDeuxRepliApresOrdreDeStop", "RetourSurPositionApresAttackAutoActif",
                   "RetourSurPositionDesRecosActif", "TempsMinimumDeMaintienOrdre_OrdreAttack",
                   "TempsMinimumDeMaintienOrdre_UniteMoveAndAttack", "TempsMinimumDeMaintienOrdre_UniteSansArme",
                   "ReglesActives_TirReflexSilenceRadio")),
    ("computer", ("ArmyValueForceLaunchAttack", "MinArmyValueToUseManipulationCard", "MaxWaitingRequest",
                  "NbMaxWaitingRequestBeforeRequestingNewFactory",
                  "MaxTimeWaitingRequest", "CheckAndCancelWaitingRequest", "BP_DepotAddedValue", "BP_HqValue",
                  "RF_TypeRapportDeForceInIaStrat", "RF_NbMetreMaxAParcourir")),
    ("decoys", ("NbMin_UniteLeurre_OffensiveGenerale", "NbMax_UniteLeurre_OffensiveGenerale",
                "NbMin_UniteLeurre_OffensiveAerienne", "NbMax_UniteLeurre_OffensiveAerienne",
                "NbMin_UniteLeurre_OffensiveBlinde", "NbMax_UniteLeurre_OffensiveBlinde",
                "ConstructionDelayForFakeBuildingsMin", "ConstructionDelayForFakeBuildingsMax",
                "Ratio_Infanterie_OffensiveGenerale")),
)
# where each group shows in AI and player settings: what players start with and get, the game rules, and the
# computer players' (a group not named here is a game rule)
SECTIONS = {"money": "players", "supply": "players", "production": "players", "cards": "players",
            "computer": "computers", "decoys": "computers"}
PROPS = tuple(p for _group, props in GROUPS for p in props)
RUSES_PER_SECTOR, RUSES_PER_SECTOR_MOST = "MaxNbCardsPerZoneByAlliance", 2  # each sector has room for two ruses


def copies(objects: list[dict]) -> dict[str, dict]:
    """{game mode: its copy}, from every constants object the game index has (Index.of_class(CLASS)), by file. A mode
    whose copy isn't there (another game build) is left out."""
    out = {}
    for mode, part in COPIES.items():
        found = [o for o in objects if part in o["file"].lower()]
        if len(found) == 1:
            out[mode] = found[0]
    return out
