# Armed Factories

Gives all 49 real production buildings a self-defense turret via UniteDefense (the same always-on mechanism 2 vanilla decoy buildings already use), armed with actual light-infantry rifle ammo borrowed from Unit_Soldat_US_Leger rather than a proper MG-nest's own ammo -- weaker and shorter-ranged, 'factory workers grabbing rifles' rather than a real emplacement. New private turret unit Unit_Tourelle_Factory_Guard, never shown in the build menu, borrows everything non-weapon (armor, visuals, sound, idle-AI) from Unit_Tourelle_MG_GER via anchor.

Rebuilt from the RUSE-Mod-Manager mod `Armed_Factories_V1.rmod` (version 1.0.0, made on game build 24670294) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 6 new objects, 49 objects changed, 49 values set.

## Assumptions to check in-game

- copies of @[ClassNameForDebug='Unit_Tourelle_MG_GER'] with the original's values on top, instead of units built from scratch (the original borrowed most parts from that unit): Descriptor_Unit_Tourelle_Factory_Guard

## Not rebuilt

- kept from the copied unit: GfxDescriptor (the original set a reference by file position (object #60322, TGfxDescriptorModeleWithAnimation)): Descriptor_Unit_Tourelle_Factory_Guard
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #60323, TGfxDescriptorPileJeton)): Descriptor_Unit_Tourelle_Factory_Guard
