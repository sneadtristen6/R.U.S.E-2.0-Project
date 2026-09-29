# Community mods, rebuilt in our format

RUSE-Mod-Manager mods (`.rmod` files) rebuilt as mods of ours by [`tools/rmod_to_mod.py`](../tools/rmod_to_mod.py)
(the format and what carries over: [docs/MOD_FORMAT.md §13](../docs/MOD_FORMAT.md)). Each folder is a normal mod
(`mod.toml`, `src/<id>.rndf`, sometimes `text/*.csv`) with a README that says what the original did, what is in the
rebuilt mod, the assumptions to check in-game, and what could not be rebuilt. The numbers, names and descriptions
are the original authors'; the originals were made on Steam builds 24087620 or 24670294 (`[game] builds`), and
ours build against whatever game is installed, because they find objects by name, not by position.

**None of these has been checked in-game yet.** Each README's "Assumptions" are the first things to look at.

**To play one:** in the launcher (0.2), drop the mod's folder on the window (or "Add a mod file…" and pick its
`mod.toml`), put it in a mod set, Play. From a prompt: `ruse build mods/airfield-capacity --instance D:\RUSE-Instances\test`.

## In the repo (18)

| Mod | What it does | State |
|---|---|---|
| `airfield-capacity` | airfields hold 128 planes instead of 8 | complete (also the Cold War constants) |
| `all-around-awareness` | every ground unit sees all round (flag 71) | complete |
| `argonne-forrest-mod` | ground units can't enter forests (flags 11, 21, 55) | the terrain layers of 31 maps are not carried: forests don't block line of sight yet |
| `armed-factories` | every production building gets a rifle turret | complete; the turret unit is a copy of the German MG nest (assumption) |
| `bigger-bomb-loads` | bombers drop twice the bombs, in a wider spread | complete |
| `cheat-mod-v2` | everything costs 1 and builds at once (useful for testing) | complete |
| `double-speed-range` | double speed, weapon range and vision | complete |
| `faster-multi-takeoff` | 24 planes per airfield, no gap between take-offs and landings | complete |
| `fnat-all-the-time-v1` | units never get pinned (threshold 2,000,000); by DomesticNukes | complete |
| `free-placement-factories` | production buildings can be placed anywhere | the terrain layers are not carried (the original wasn't sure they matter) |
| `half-speed-range` | half speed, weapon range and vision | complete |
| `high-altitude-planes` | planes fly four times higher | complete |
| `indirect-fire-for-everyone` | every unit and building gets flag 1 (indirect fire, the original's reading) | complete |
| `infinite-fanaticism` | each unit's pinned threshold is one above its health | complete |
| `low-altitude-planes` | planes fly at a quarter of the height | complete |
| `navy-mod` | a destroyer, heavy cruiser and battleship for every nation, with names and descriptions | **experimental**: the ships are copies of the game's own three ships with the original's stats; the original's icons, model rewiring and mesh-pack changes were matched by file position and are not carried, so the ships may look or behave differently, or not appear. Kept as the starting point for landing ships (Pacific) |
| `no-bunkers` | no fixed defences can be built | complete |
| `no-regeneration` | no health regeneration out of combat | complete |
| `passable-forests` | vehicles can enter forests (flags 11, 21, 55 removed) | complete |
| `tanks-only` | only tanks can be built | complete |

## Rebuilt, not added (the tool makes them again from the `.rmod` in a second)

What is instructive in them is written down in [docs/FORMATS.md §2](../docs/FORMATS.md) ("Values and tricks from
community mods"). One HP Units, Super Speed Everything, Peashooter Snipers, Super Rate of Fire, Here I'll Hold Your
Hand and No Fog of War are stress tests; Meme Descriptions rewrites 419 unit texts; Super Aggressive AI and New AI
Doctrines change the AI profiles (the two doctrine rewrites need the profiles found on the PC first); Nuclear
Artillery Endgame makes the atomic cannons buildable with new shells; Static Battleship and Operations Solo were the
original author's experiments.

## Not rebuilt

- **Campaign Red Zone Fix:** 19 recompiled mission scripts (`.xyz`). Mods of ours take script sources only
  (MOD_FORMAT §9), never compiled code.
- **Custom Music** (a copyrighted song as an 18 MB `.ess` file) and **Meme Intro** (a replacement splash video):
  whole files only; sound and video aren't part of mods yet.
- **RCRBM 2** by CHANDAWG2007 and **Monte Cassino Demo MP** by SuperCrumpets: other people's mods. RCRBM 2 also
  matches 200 objects by file position on an older build; Monte Cassino ships a scenario file.
- **Tharshey's Extreme Nations v5, Tharshey's Extreme AI, Val's Reworked Nations:** whole replacement copies of
  `ZZ_GladPatchableWin.dat` for the "Compat 2" branch, not mods in any format. Importing them needs a
  "compare two packs" tool and the pristine pack of that branch (the PC has it).
