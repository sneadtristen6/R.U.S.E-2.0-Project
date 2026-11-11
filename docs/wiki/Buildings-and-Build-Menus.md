# Buildings and build menus

> **For:** modders · **You need:** RUSE Studio 0.9.8.8 or later and a mod · **Takes:** a few minutes

Each nation's buildings, what their build menus offer and in what order, and buildings of your own. Seen in the game.

## The buildings board

Open the **Nations** tab: under each nation, **Buildings and units** shows its buildings as rows, each a row of the
units its build menu offers, in the game's order. Beside each nation's name, **Keep its units** puts every unit of its own back in its build menus, as in the game, and **Start it empty** takes them all out, so you fill its buildings yourself. **Research**, above the nations: **No research** makes every unit of every nation buildable from the start; **Keep the game's research** gives the game's units their research back. Both ask first.

- **+** adds a unit to a building: one of the nation's own, a copy of another nation's, or an
  [[era unit|Units-From-Other-Eras]]. A copy goes into your mod, named as the game names it.
- **Drag** a unit along its row to change its place in the menu, or onto another building to build it there.
- **×** takes a unit out of the build menu. It's hidden, not deleted: the unit is still in the game's files.
- **Research…** then **Put under this one** on the unit it comes after: it's researched from that one (in any of the
  nation's buildings). **Buildable from the start** needs no research. **Research cost** and **Research time (s)** are
  beside it.

Each row says how many units it has. A building left with nothing to build shows the HQ's building list in the game
when it's picked. More than 10 units in one building, a plane in a ground building, or a vehicle at the Airfield:
not tried in the game yet.

A unit's page on the **Units** tab says where it's built ("Built in the ARMOR BASE: place 2 of 6"), and **Show on the
board** opens its row.

## Groups

In the game, a building's build list shows each group as one row: a unit and its upgrades (the Panzer IV and the
Panther). The board shows each building's groups, each with its count (**4 of 6**), and how many groups the building
has (**7 of 10 groups**).

- A new unit goes into the group of its kind in its building, or a group of its own when the building has none of
  that kind. **+** on a group, or a drop onto it, puts it there; **New group** starts one.
- A group holds at most 6 (its units and research cards), and a building at most 10 groups, so its list fits on the
  screen. One more is refused: take a unit out, or put it in a building of its own (**Add a building…**).
- A unit the game gives no card type (a truck, the V2 launcher): pick its group.

Not tried in the game yet.

## Add a building

**Add a building…** under a nation's board: pick the game's building it copies (**Copy of**), give it a **Name**,
then either:

- **Makes the same units as the building it copies**, or
- **Makes units of its own**: a row and a tab of its own on the game's build bar, filled with **+**. Up to three a
  nation.

The second and third building with units of its own need a small game patch for more buildings. The Studio downloads
it once and puts it only into your modded copy of the game, never into the game in your Steam folder.

## A building's own look

On a new building's page, **Import model** puts a 3D model of your own (.glb, .gltf or .3ds) in place of one piece of
the look it copies: the main building of a factory or HQ, or the piece you pick. Your model is sized to that piece and
stands where it stood; the rest of the look stays. The game's own buildings stay as they are: make a new building from
one first.

**Where your mod keeps it:** `files\buildings\<the building's name>\`. The box shows the whole path on your PC (or where it will be, before the model is in), and **Show in folder** opens that folder.

**Its picture in the build menu:** turn and zoom the model until it looks right inside the dashed frame, then use
that view. See [[Import a model|Import-a-Model]] for models in general.

## What's been seen in the game

Seen: the board's changes (units added, moved, taken out, researched from another), a copied building, a building with
units of its own and its tab on the build bar, a second and third one with the game patch, and a building's own model
and picture.
