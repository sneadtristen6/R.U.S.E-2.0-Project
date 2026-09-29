# All-Around Awareness

Adds InitialFlagSet bit 71 ('vision_circulaire' -- 360-degree vision, no facing restriction) to every ground unit (150 newly patched, 54 already had it vanilla -- mostly artillery and turretless casemate vehicles). Real vanilla precedent for this flag (unlike the dead Total Blackout experiment) -- 54/204 ground units plus all aircraft already use it. No more sneaking around a unit's blind side.

Rebuilt from the RUSE-Mod-Manager mod `All_Around_Awareness_V1.rmod` (version 1.0.0, made on game build 24670294) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 150 objects changed, 150 values set.

## Assumptions to check in-game

- the original rewrote each unit's whole InitialFlagSet list; here the bits 71 are added to the list the game has

Everything in the original is here.
