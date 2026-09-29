# Argonne Forrest Mod

Forests now behave like towns: every ground unit (infantry, recon, tanks, towed guns) is blocked from entering forest terrain via InitialFlagSet, AND every forest cell on all 31 real maps carries the same 'blocked/clear-path' terrain bit water and cliffs already use -- CONFIRMED in-game to block both movement AND line-of-sight/gunfire through the forest. Combines Impassable_Forests_V1 + Forest_Terrain_Block_V1 into one mod.

Rebuilt from the RUSE-Mod-Manager mod `Argonne_Forrest_Mod_V1.rmod` (version 1.1.0, made on game build 24087620) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 158 objects changed, 158 values set.

## Assumptions to check in-game

- the original rewrote each unit's whole InitialFlagSet list; here the bits 11, 21, 55 are added to the list the game has

## Not rebuilt

- terrain layers for 31 map(s) (`sdb_patches`): that part of the format waits for the terrain work (PLAN.md §7 MT)
