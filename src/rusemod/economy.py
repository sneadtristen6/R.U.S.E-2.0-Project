"""The game's economy, as LittleGroove's Economy editor (RUSE-Mod-Manager) offers it, for the Studio: starting money
and income, the depots' supply trucks, production limits, the ruse cards, and the computer players' production and
decoys. The game has these values twice (its usual game modes, and the Nuclear mode's: not tried in the game yet), so
the Studio changes both copies from one value, each reached by the file it's in, and a change holds in every mode.

Depots, admin buildings and truck factories themselves (price, build time, strength) are buildings: the Studio's
Units page changes them. The population cap isn't offered: it is a console setting, off in the PC game (not tested).
Nor are the most ruse cards on one sector: more than two crashes the game (rusemod.rules, ruses-per-sector, which the
build refuses from any mod), and the owner wants it left as the game has it for now (2026-10-06).
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
    ("computer", ("ArmyValueForceLaunchAttack", "MinArmyValueToUseManipulationCard", "MaxWaitingRequest",
                  "NbMaxWaitingRequestBeforeRequestingNewFactory",
                  "MaxTimeWaitingRequest", "CheckAndCancelWaitingRequest", "BP_DepotAddedValue", "BP_HqValue")),
    ("decoys", ("NbMin_UniteLeurre_OffensiveGenerale", "NbMax_UniteLeurre_OffensiveGenerale",
                "NbMin_UniteLeurre_OffensiveAerienne", "NbMax_UniteLeurre_OffensiveAerienne",
                "NbMin_UniteLeurre_OffensiveBlinde", "NbMax_UniteLeurre_OffensiveBlinde",
                "ConstructionDelayForFakeBuildingsMin", "ConstructionDelayForFakeBuildingsMax")),
)
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
