# Engine notes: ideas from Eugen's own files

Learned by reading the install **read-only**. No Eugen files are stored in this repo; this is our own summary,
kept as design input. Re-derive from the game with the spike tools when needed.

## The game has a Python scripting layer (this is the "useful code")

The `.xyz` files are compiled Python 2.5. Package `eugen` (plus `eugensolo`, `eugentest`, `eugenpatchable`)
is the game's scripting layer — 180 modules. Sub-packages by size:

| Package | Modules | What it is |
|---|---|---|
| `front/`, `headup/` | 30 + 22 | in-game HUD and interface behaviour |
| `defines/` | 20 | constants/enums by domain: `camps`, `colors`, `feedback_text`, and `front/{economie, combat, visibilite, strategic_ia, batiments, avion, bluff, acknows, message, icone}` — the designers' tunables in script form |
| `leveldesign/`, `leveldesignsolo/` | 20 + 20 | campaign and mission scripting: objectives, triggers, scripted events |
| `base/` | 10 | scripting foundation: `camp`, `world_helper`, `geo_database`, `mouvement`, `balise` (waypoints), `eug_timer`, `pickling`, `actions/` |
| `game/`, `interface/`, `tools/`, `debug/` | 9 / 5 / 17 / 6 | rules glue, helpers, debug |
| `effetmap*.py` | per map | per-map effect scripts (also one per map in IA_Common). Variants like `effetmap6ia.py`, `effetmapmultiplayer.py` set AI count / mode — this is what the community "1v15 AI" mod edits |

**Scripting vocabulary (most-referenced identifiers):** `Database` / `GetObject`, `descriptor` / `Descriptor`,
`world` / `current_world` / `world_helper`, `Camp` / `get_camp` / `camp_du_joueur`, `Group`,
`Action` / `ActionInstantaneous` / `execute` / `virtual_run`, `interface_in_game_manager` / `hud`,
`geo_database`, `mouvement`, `balise`, `vector` / `position`, `kill`, `terminate_ifn`, `_enum_for_game_play`, `_ndf`.

## What this means for the tool

1. **Missions and game modes are Python + scenario data.** A custom mode (e.g. Island Defense) is new/edited
   `leveldesign` and `effetmap` scripts plus scenario placements — not just stat changes. The tool needs a
   Python-2.5 compile path and script-pack registration (roadmap M9). Confirms scripts are a first-class mod target.
2. **The engine addresses data by name:** scripts do `Database.GetObject("<descriptor>")`. That is exactly the
   name-based addressing in [MOD_FORMAT.md](MOD_FORMAT.md) §4 — strong validation that patching by export path
   (not by index/offset) matches how the game itself refers to objects.
3. **`defines/*` is a map of the intended tunables** (economy, combat, visibility, strategic AI, buildings…).
   Use it to seed the schema DB's property categories and to know which knobs are "designer-safe".
4. **Domain objects the map/mission editor must model:** `Camp` (side/player), `Group`, `Action`, `balise`
   (waypoints), `geo_database` (zones/geometry), `position`/`vector`.
5. **Behaviour in `everything.cpp` is code-as-data:** classes like `TActionDescriptor*`, `TFunctionCall`,
   `TIntrinsicCall_1/2/3Param`, `TSelect`, `TConstant*` form an action graph. Editing behaviours = editing that
   graph, which our object model already round-trips losslessly (C1). So "new behaviour" is often data, not exe code.

## Tie-in to the roadmap

- Reinforces sequencing: build the tool (I/O, object model, builder, then editors) before any content.
- Adds concrete substance to **M6** (maps/scenarios: Camp/Group/balise/geo_database) and **M9** (scripting/modes).
- The `defines/` tables are the reference for the schema DB (L2) and the unit/economy editor categories.
