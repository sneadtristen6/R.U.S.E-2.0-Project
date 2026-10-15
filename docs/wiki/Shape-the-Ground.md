# Shape the ground

> **For:** modders · **You need:** RUSE Studio 0.7.2 and a mod · **Proven in the game:** units drive on edited
> ground and take orders there

## Open the map

1. **Maps** tab, pick the map on the left (the **«** button folds the list away for more room).
2. Look around: drag to turn, right-drag to move, the wheel to zoom (keys: [[Map view keys|Map-View-Keys]]).
3. In the bar along the bottom, click **Ground & water**. Its tools open above the bar, the **Ground** tab first.

## The tools

| Tool | Use it for | How |
|---|---|---|
| **Hill** | a round hill | one click |
| **Raise** / **Lower** | building up or cutting down, bit by bit | drag |
| **Crater** | a crater with a rim | one click |
| **Plateau** | a hill with a flat top | one click |
| **Flatten** | pulling bumps toward one height | drag |
| **Level** | painting ground flat at the height where you start | drag |
| **Smooth** | softening sharp edges | drag |
| **Ramp** | an even slope, say up to a plateau | click where it starts, then where it ends |

**Size** and **Strength** are the sliders on the right (keys **[ ]** and **- =**).

## Water

Click the **Water** tab (in **Ground & water**):

- **Water** floods the ground below a level: the height where you start dragging, plus Strength. Drag it along a
  valley for a river, or into a dip for a lake.
- **Drain** puts the water back to the map's base level: rivers and lakes there dry up.

## Paint the ground with a texture (Studio 0.9.8.5)

**Still buggy, use at your own discretion.** In the bar along the bottom, click **Map Paint**, then **Texture**. Pick
where the texture comes from, click one, and drag on the ground:

- **Game textures:** the ground textures of the game's own maps (grass, fields, sand, snow, rock, roads...), by
  group, with a search. They're read from your game; nothing of them goes in your mod.
- **From a map:** pick a map, click a spot on it: a 320 m square of its ground becomes your texture.
- **Your pictures:** **Add a picture…** keeps a picture of your own in your mod (`files/ground`).
- **Online (free):** Poly Haven and ambientCG textures (CC0) and US aerial photos (public domain). A click downloads
  that one picture into your mod, with its credit. Not tried yet.
- **This map:** copies this map's own ground from a spot you pick.

**Size** lays it bigger or smaller (a quarter to 16 times). With a game texture, **Game detail up close** also lays
the game's own decals of it over what you paint. Not yet seen in the game.

## Undo and start over

**Undo** (or **Ctrl+Z**) takes back the last stroke; **Start over** takes back every stroke on this map.

## See it in the game

**Test in game**, then in the game's main menu click **BATTLES** and pick that map. The message at the bottom of
the Studio says which.

> [!TIP]
> Steep cliffs look jagged: the game's ground is a mesh of triangles, and a sharp edge falls between them. Wide,
> soft shapes look best.

**Next:** [[Cover and movement|Cover-and-Movement]]
