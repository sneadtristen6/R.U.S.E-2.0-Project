# Draw roads

> **For:** modders · **You need:** RUSE Studio 0.7.4 and a mod · **Proven in the game:** supply routes follow a new
> road, and it's painted on the ground

## See the map's roads

Tick **Roads** at the top of the map: the map's own roads show in gold, on the ground as you shape it.

## Draw a new road

1. In the bar along the bottom, click **Roads**. The map's roads show in gold, your new ones in blue.
2. Pick a tool:

| Tool | How |
|---|---|
| **Straight** | Click where the road starts, then where it ends. |
| **Curve** | Click the start, then the bend it's pulled toward, then the end. |
| **Freeform** | Click along the way; double-click, press **Enter** or click **Finish** to end it. |

3. A blue ribbon follows the pointer, with the **road's length** beside it (Freeform also shows the part from your
   last click). An end near any road **snaps onto it** (a ring shows where), so the new road joins it: supply trucks
   can drive from one to the other. The Roads tools show how many new roads the map has, and their length in all.
4. **Esc** drops a road you're drawing; **Undo** (or **Ctrl+Z**) takes back the last one.

New roads are saved in your mod at once (`maps/<map>/roads.toml`).

## What a new road does in the game

- **Supply routes use it** (proven: a supply depot's route took a new shortcut through open fields).
- **It's painted on the ground** in the map's own road colour, so players see it (proven in the game). **Not yet up
  close:** with the camera near the ground a new road disappears (a known issue, being worked on).
- **Infantry follow it** to get somewhere faster (proven in the game, Studio 0.8.0).
- **Over water it gets a bridge**: the map's own kind (24 of the 32 maps have one), one piece stretched from bank to
  bank the way the game's own bridges are, and units can drive across. A road over one of the map's own bridges gets
  the new bridge in its place. On a map with no bridge kind, the build says so and the water stays closed. (Bridges
  are new: not checked in the game yet.)
- Trees along it stay for now; clearing them comes with the tool that removes the map's own trees and buildings.

**See it:** **Test in game**, then in the game's main menu **BATTLES** and the map. Place a supply depot near your
road and watch its route.

**Next:** [[Place buildings and trees|Place-Buildings-and-Trees]]
