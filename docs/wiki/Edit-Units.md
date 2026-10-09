# Edit units

> **For:** modders · **You need:** RUSE Studio and a mod · **Takes:** as long as you like

## Find a unit

The **Units** tab lists every unit and building. Narrow it down with:

- the **search** box (code names or the names players see, in any of the game's ten languages: the language button at the top);
- the **kind** and **nation** chips;
- the **type** menu: what it's for, like HQ, money, factories, forts and decoys for buildings, or the factory that
  builds a unit.

## Change a value

1. Click the unit. Its values are listed by section (price, armour, speed, weapons...).
2. Type a new value. It's saved in your mod at once; the game's value shows next to it.
3. **Undo** next to a value puts the game's value back.

Flags (what a unit can do or be) show as chips: the cross takes one off, the menu adds one.

## Make a new unit

A new unit starts as a copy of a game unit, with its own name, so you can change it without touching the original.
The Units tab has two buttons at the top: **Change a unit** (the list, then the unit's values and Blender) and
**New unit (import a model)**. With **New unit**, pick the unit to start from, give it a name, and click **Create**;
then change it like any other. Or pick the unit and choose **New unit…** on its page.

## Change how a unit looks

The unit's page shows its **3D model**: drag to turn it, scroll to zoom.

- **Repaint in Blender:** click **Open in Blender** (Blender is free; if the Studio doesn't find it, the page offers
  **Get Blender (free)** and **Choose Blender…** to show it where `blender.exe` is). The unit opens with its pictures,
  ready to paint on the model. Paint, then click **Bring back**: your
  paint goes into your mod. Seen in the game, up close and from far.
- **Its card in the build menu:** turn and zoom the 3D model until it looks right inside the dashed frame, then
  **Use this view as the card**. **Game's card** takes it back. Seen in the game. On a new unit, the card is its own:
  the unit it copies keeps its picture.
- **A model of its own (new units):** **Import model…** brings in a 3D model from Blender or any 3D tool. See
  [[Import a model|Import-a-Model]]. A game unit keeps its model: its page has **New unit from this one…** to make
  the new unit the model goes on.

## Research: what it's an upgrade of

A unit's page has an **Upgrade and research** box: the unit it's an upgrade of (**Upgrade of**), its own upgrades, and
its research price and time. Pick another unit of the same build menu, or **None: a unit of its own** to make it
buyable from the start. Research times can be typed in seconds or minutes (the picker beside them).

When you take out a unit that others are researched from, **Settings > Research** decides what happens: **Warn me
first** (the default), **Refuse**, or **Re-link them** to its own parent. A unit left researched from one that's gone
says so here and in the check bar, and the build stops on it until you pick another.

## Units from other eras

366 units from WWI to today, each another maker's free 3D model, can be added to your mod as new units, at their real
size and behind research: see [[Units from other eras|Units-From-Other-Eras]].

## Give a weapon other ammo

A weapon can fire another unit's ammunition; its muzzle flash and sound come with it. Ammunition is sorted by type
(AP, HE, anti-aircraft, machine guns, bombs, rockets...).

## Test it

**Test in game** builds the mod and starts R.U.S.E. Look for the unit where it's built (its factory) in a battle (main menu: **BATTLES**, then a map).

**Next:** [[Export and share|Export-and-Share]]
