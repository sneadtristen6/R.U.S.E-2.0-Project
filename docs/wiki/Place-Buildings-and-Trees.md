# Place buildings and trees

> **For:** modders · **You need:** RUSE Studio 0.7.2 and a mod (Grid, Box, Path, Select and Redo: 0.9.8.7; models of
> your own: 0.9.8.8) · **Proven in the game:** placed buildings show at every zoom, up to 8× their size, and units go
> around them. Not tried in the game yet: what's placed with Grid, Box and Path, and moved objects

## Place

1. In the bar, click **Buildings**, or **Props & trees** and then its **Props** or **Trees** tab.
2. Pick a type from the pictures (type in the search box to narrow them). Each picture is drawn from the game's own
   model of it, and the number in its corner is how many the map already has. The list holds this map's own types:
   the game only takes a type a map already uses.
3. Choose how a click places:
   - **One**: one object where you click;
   - **Area**: drag to scatter objects in a circle (**Spacing** keeps them apart, **Area** sets the circle);
   - **Line**: click the start, then the end, for a row (a hedgerow, a street, a tree line), turned along it;
   - **Grid**: rows of objects: click where the first row starts and where it ends, then move out the rows and click
     (**Between rows** sets the gap);
   - **Box**: drag a box on the ground and let go: it fills with the picked object in rows;
   - **Path**: click along the way, then double-click, press **Enter** or **Finish**: the objects follow a smooth curve
     through your clicks (a hedge, a tree line); with a width, a belt of them. **Esc** drops a grid, line or path half
     made.
4. **Face the roads:** near a road, an object goes beside it and turns to face it, and a row follows it; a grid or a
   box leaves the roads clear. The turn slider still turns it (try 180° if a house shows its back).
5. **Turn** and **Size** (up to 10×) are the sliders on the right. Trees vary a little in size and turn by
   themselves, so a wood doesn't look stamped.

Before you click, the type shows see-through under the pointer, turned and sized as it will stand. Placed objects
show as their own models, each with a small gold dot at its foot that marks it from far away.

## Select, move, turn, delete

**Select** (in the **Buildings** and **Props & trees** trays) picks what stands on the map, what your mod placed or the
map's own: click one, **Shift+click** to add, or drag a box around several. Then drag a picked one to move them, use
**Turn** and **Size**, or **Delete**. **Put back as the map has it** undoes your changes to the map's own; **Esc**
picks none.

## Models of your own

**Import model…** (in **Props & trees**) makes a 3D model (.glb, .gltf or .3ds) one of your map mod's own rocks,
props, bushes or trees. It's placed like the game's own, on every map of the mod, with smaller versions for the
middle and far distances made for it. Give it a **Size**, and **Where it's from**: a model someone else made can go
in a mod under CC0 or CC-BY only, with its author. Ticked **Solid: units go around it**; not ticked, units drive
through it and knock it over, as the game's own small props. **Your model…** changes it later. Seen in the game.

## Solid buildings

**Solid** (on by default) makes units go around a placed building instead of through it. Turn it off for a building
that should only be looked at.

## Hiding in them

Placed buildings don't hide units by themselves: open **Cover**, pick **Town** and click the town you made.

## Undo and Redo

**Undo** (or **Ctrl+Z**) takes back the last object, or the whole area, line, grid, box or path, and the last move,
turn, size or delete. **Redo** (or **Ctrl+Y**, **Ctrl+Shift+Z**) puts it back. Every map tool has both.

## Erase the map's own trees and props

1. In the bar, click **Erase** (Studio 0.8.1).
2. Pick what it takes: **trees**, **props**, **buildings** (any mix). Each circle keeps what was picked when you
   painted it.
3. Drag over the map: red circles mark what goes, and what they cover is tinted red. **Size** sets the circles;
   the tray counts what they'll take when the mod is built.

Where trees go, the ground opens to every unit and loses its forest cover (proven in the game: tanks drive into a
cleared wood, infantry there aren't hidden). Erased buildings open their ground to units
too. **Undo** (**Ctrl+Z**) takes back the last drag, **Start over** removes every circle on the map.

**Next:** [[Edit a scenario|Edit-a-Scenario]]
