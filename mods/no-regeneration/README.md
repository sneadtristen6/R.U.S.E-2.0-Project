# No Regeneration

Disables out-of-combat health regeneration for every unit and building (RegenerationPinnedHorsCombat 10.0 -> 0.0) -- damage is permanent, units fight at whatever condition they're in until destroyed.

Rebuilt from the RUSE-Mod-Manager mod `No_Regeneration_V1.rmod` (version 1.0.0, made on game build 24087620) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 1 object changed, 1 value set.

## Assumptions to check in-game

- the TTunableConstante the original changed by position is changed in every TTunableConstante object instead (the game has one per constants file)

Everything in the original is here.
