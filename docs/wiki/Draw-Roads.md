# Draw roads

> **For:** modders · **You need:** RUSE Studio 0.7.2 and a mod · **Proven in the game:** supply routes follow a new
> road

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

3. A blue ribbon follows the pointer. An end near any road **snaps onto it** (a ring shows where), so the new road
   joins it: supply trucks can drive from one to the other.
4. **Esc** drops a road you're drawing; **Undo** (or **Ctrl+Z**) takes back the last one.

New roads are saved in your mod at once (`maps/<map>/roads.toml`).

## What a new road does in the game

- **Supply routes use it** (proven: a supply depot's route took a new shortcut through open fields).
- It isn't painted on the ground yet: the roads you see in the game are part of the ground's picture. Painting them
  comes with the ground-painting tool.
- Trees along it stay for now; clearing them comes with the tool that removes the map's own trees and buildings.

**See it:** **Test in game**, then in the game's main menu **BATTLES** and the map. Place a supply depot near your
road and watch its route.

**Next:** [[Place buildings and trees|Place-Buildings-and-Trees]]
