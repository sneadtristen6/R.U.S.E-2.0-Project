# Indirect Fire For Everyone

Adds InitialFlagSet bit 1 (working hypothesis: 'indirect fire', based on its vanilla footprint matching exactly the 54 artillery/gun pieces) to every unit and building in the game (410 newly patched, 54 already had it) -- infantry, aircraft, ground vehicles, trucks, buildings, everything.

Rebuilt from the RUSE-Mod-Manager mod `Indirect_Fire_For_Everyone_V1.rmod` (version 1.0.0, made on game build 24087620) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 410 objects changed, 410 values set.

## Assumptions to check in-game

- the original rewrote each unit's whole InitialFlagSet list; here the bits 1 are added to the list the game has

Everything in the original is here.
