# Draw roads

> **For:** modders · **You need:** RUSE Studio 0.7.4 and a mod · **Proven in the game:** supply routes follow a new
> road, and it's painted on the ground

## See the map's roads

Tick **Roads** at the top of the map: the map's own roads show in gold, on the ground as you shape it.

## Draw a new road

1. In the bar along the bottom, click **Roads & bridges** (its **Roads** tab opens). The map's roads show in
   gold, your new ones in blue.
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
- **It's painted on the ground** in the map's own road colour, so players see it (proven in the game). It looks like
  the map's own roads from high up and right down at the ground.
- **Infantry follow it** to get somewhere faster (proven in the game, Studio 0.8.0).
- **Over water it gets a bridge**: the map's own kind (24 of the 32 maps have one), one piece stretched from bank to
  bank the way the game's own bridges are, and units can drive across. A road over one of the map's own bridges gets
  the new bridge in its place. On a map with no bridge kind, the build says so and the water stays closed. (Proven
  in the game: tanks, infantry and supply trucks cross on the deck.)
- The plants and props on its path are taken off; **Keep the trees on new roads** keeps the trees and bushes (a
  road under the trees).

**See it:** **Test in game**, then in the game's main menu **BATTLES** and the map. Place a supply depot near your
road and watch its route.

**Next:** [[Place buildings and trees|Place-Buildings-and-Trees]]
