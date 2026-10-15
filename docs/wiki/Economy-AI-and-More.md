# Economy, AI and more: LittleGroove's tools

> **For:** modders · **You need:** RUSE Studio 0.9.8.1 or later and a mod · **Takes:** as long as you like

LittleGroove's RUSE-Mod-Manager had tools the Studio didn't. They're in the Studio now, each in your own mod: a change
is saved there at once, and the game's files are never touched.

## Economy tab

Starting money and income, supply depots (money per truck, trucks per convoy, the time between convoys), production
limits, decoys, and the ruse cards each side starts with. A change counts for every game mode. Supply depots and
administration buildings are buildings: their price, build time and strength are on the **Units** tab.
Seen in the game: the starting money and the ruse cards at the start.

**Depots on the maps** (under Supply depots): give every supply depot more trucks, so more money, on **All maps** or
**One map:** you pick. Multiply each depot's trucks (**times their trucks**) or give them all the same number
(**trucks each**). The line above it says what a depot holds with your values. A depot you gave its own trucks on the
Maps tab keeps them. Play mods with more than 1,000 trucks a depot with Launcher 0.4.8.4 or newer. Seen in the game
(D-Day's depots with 500 trucks; other maps three times theirs).

## AI tab

How the computer players play. A computer player mixes three sets of values: **Default**, its difficulty and its
profile (both picked in the game's lobby); pick one to see and change what it lists: when it starts attacking, how
strong it waits to be, how it defends, the units it prefers, and its ruse cards.
Seen in the game: a ruse card taken out of the menu, one moved in it, a card's length, and when Easy starts attacking.

A difficulty or profile lists only some values; the rest come from **Default**. To give it its own value for one only
Default lists, pick it under **Give <name> its own value** and click **Add**: it starts as Default's (nothing changes yet), then change it on its row.
Not tried in the game yet.

**Map and mission scripts**, below it: the scripts the game runs on its maps (the campaign's chapters, challenges,
Operations), shown as Python to read. **Copy** copies one.

## A unit's Upgrade and research box

On a unit's page: the unit it's an upgrade of (**Upgrade of**), its own upgrades, and its research price and time.
Pick another unit, or **None: a unit of its own**. See [[Edit units|Edit-Units]].

## All values tab

Any object and value of the game's, changed in your mod: add or take out a value, make or delete an object, give a
text value words of its own. Not tried in the game yet.

## Files tab

Any file inside the game's packs: pick a pack, then a file to see it as what it is (a picture, a text table, a mission
script...). **Save a copy…** saves it out; **Change it with a file of mine…** puts yours in your mod; **Add a file of
mine to this pack…** adds a new one. Your mod keeps only what you change, never a copy of the game's file. Not tried in
the game yet.

## Missions and maps

A mission's scripts can be changed, and the Studio checks whether it's in the menus, whether every file it needs loads,
and its texts; it can be moved up or down in its menu. On a map: town and hill names, named points and zones, and a
map item's name and facing. **Notes** can be kept on a unit, a value or a computer player. Not tried in the game yet.

## In the Launcher: Convert an old mod

An older mod that comes as the game's own packs, made to be copied into the game folder, becomes a mod your library
plays beside others: see [[Install and play|Install-and-Play]].
