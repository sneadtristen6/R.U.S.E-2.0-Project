# Cheat Mod 2.0

Every unit AND every building costs $1 to build, every unit's ProductionTime is 0, and the global MinProductionTime floor is lowered to 0.01 seconds so 0-second production actually takes effect instead of being clamped back up to 1 second. Extends the example Cheat Mod (units-only $1 pricing) with building pricing and the confirmed-working instant-production fix.

Rebuilt from the RUSE-Mod-Manager mod `Cheat_Mod_V2.rmod` (version 2.0.0, made on game build 24087620) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 441 objects changed, 746 values set.

## Assumptions to check in-game

- the TTunableConstante the original changed by position is changed in every TTunableConstante object instead (the game has one per constants file)

Everything in the original is here.
