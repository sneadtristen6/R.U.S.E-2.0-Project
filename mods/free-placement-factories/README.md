# Free Placement Factories

Adds BuildPolicy=2 (the exact value every real bunker/defense structure uses for free placement, confirmed exclusive to that category across all 135 buildings) to all 49 real production buildings, so they can be placed anywhere on the map instead of requiring truck delivery to a road-adjacent depot slab -- CONFIRMED WORKING in-game. TypeBatiment is deliberately left untouched so they keep functioning as real factories, not defense structures. V2 also clears the per-map terrain SDB's FOREST_BIT and BLOCKED_BIT across all 31 real maps, testing whether building placement (unlike unit movement, already known to ignore this data for water/mountains) reads the same terrain data -- an open question, not a confirmed fix.

Rebuilt from the RUSE-Mod-Manager mod `Free_Placement_Factories_V1.rmod` (version 2.0.0, made on game build 24670294) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 49 objects changed, 49 values set.

## Not rebuilt

- terrain layers for 31 map(s) (`sdb_patches`): that part of the format waits for the terrain work (PLAN.md §7 MT)
