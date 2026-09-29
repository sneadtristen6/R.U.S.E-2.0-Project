# Passable Forests

Lets every tank, tank destroyer, AA vehicle, and mobile artillery/assault gun enter forest terrain the way recon vehicles already can, by removing the InitialFlagSet flags (11, 21, 55) that block forest entry. Confirmed in-game on the M4 Sherman before rolling out to the full roster.

Rebuilt from the RUSE-Mod-Manager mod `Passable_Forests_V1.rmod` (version 1.0.0, made on game build 24087620) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 140 objects changed, 140 values set.

## Assumptions to check in-game

- the original rewrote each unit's whole InitialFlagSet list; here the bits 11, 21, 55 are removed from the list the game has

Everything in the original is here.
