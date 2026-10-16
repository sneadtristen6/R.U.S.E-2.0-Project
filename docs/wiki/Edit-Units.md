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

## Flags: what a unit is and what it can do

Flags are on/off switches, numbered 0 to 104, that tell the game what a unit is (a plane, a truck, infantry, a
building...) and what it can do (go into woods, see all around, fire only when ordered...). On a unit's page they show
as chips, each with its name: hover one to see exactly what it does, how to use it and how sure we are about it. The
cross takes one off; **Add a flag…** adds one, sorted by what the flags are for.

**Flag guide: every flag explained** (under the flags) opens the whole list, with a search box. For each flag it says:

- **what it is and what it does** in the game;
- **how to use it**;
- **how sure we are:** *tried in the game*, *from the game's units* (what the game's own units that have it have in
  common), *expected, not tried yet*, *the game sets it itself* (it turns these on and off while it runs: in a unit's
  list they do nothing), or *unused*.

**The Studio checks every unit's flags** each time you change them, and again before the game starts:

- **Known crashes stop the build**, so the game is never started with them. The unit's page says why and offers the
  fix (**Take 62 off**, **Add 100**):
  - 62 (truck) or 63 (construction truck) on anything that isn't a truck: the game crashes at match start;
  - 99 (recon plane) on a plane with weapons, without 100 (fighter): the game crashes when the plane is sent to
    attack. Use the **Role** box (Scout keeps its attacks) or add 100;
  - 59 (paratroop transport) on anything but a plane, or on a plane with no unit to drop.
- **What's expected to break a unit is a warning**, not a stop: 2 (aircraft) on a ground unit, 4 (building) or 49 on a
  unit, 6 or 76 on a unit that should move (it stands still), 42 (infantry) on a vehicle, or taking off 43 (its team
  counts it) or 22 (the player can order it).

Useful ones, tried in the game: take **11, 21 and 55** off together to let a vehicle into woods; **1** gives any unit
indirect fire; **71** sees all around; **77** fires only when ordered.

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
- **Its own copy of the model:** a unit drawn with the game's model shares its paint with every unit drawn with it.
  **Give it its own copy of the model** (on its page) makes the same model with textures of its own: then **Open in
  Blender** paints this unit only. Works for new units and the game's own.
- **A squad's uniform:** the game's soldiers of a nation all wear one picture (the US's: its GIs, Rangers and
  paratroopers, and the crews of its guns and vehicles), so the **Default uniform** isn't repainted here. Pick
  **Custom uniform** to give the squad its own, then paint it in Blender. Seen in the game.
- **Rides in:** the truck a squad or a gun turns into on the roads: the game's, another nation's, or a copy of a truck
  you made and repainted. Seen in the game.
- **A model of its own (new units):** **Import model…** brings in a 3D model from Blender or any 3D tool. See
  [[Import a model|Import-a-Model]]. A game unit keeps its model: its page has **New unit from this one…** to make
  the new unit the model goes on.

## Armour

**Armour** on a unit's page picks one of the game's armour levels (tanks have 1 to 5, the number on the shield). The
unit fights with it, and its card and build menu show it. Changing a number inside the armour part itself made a unit
fight with one value while its card showed another, so that part can't be changed directly any more. Seen in the game.

## Research: what it's an upgrade of

A unit's page has an **Upgrade and research** box: the unit it's an upgrade of (**Upgrade of**), its own upgrades, and
its research price and time. Pick another unit of the same build menu, or **None: a unit of its own** to make it
buyable from the start. Research times can be typed in seconds or minutes (the picker beside them).

When you take out a unit that others are researched from, **Settings > Research** decides what happens: **Warn me
first** (the default), **Refuse**, or **Re-link them** to its own parent. A unit left researched from one that's gone
says so here and in the check bar, and the build stops on it until you pick another.

A unit shown in its build menu must be researched from a unit that's shown there too: the one you can build comes
first, the research after it. A unit shown at a battle date where the unit it's researched from is hidden stops the
game when that build menu opens (seen in the game), so the check bar names it and the build stops on it. Show the
other unit again, or pick another unit to research it from, or none. **Nations > Hide all** does this for you: a unit
left researched from a hidden one becomes buyable from the start.

## Units from other eras

366 units from WWI to today, each another maker's free 3D model, can be added to your mod as new units, at their real
size and behind research: see [[Units from other eras|Units-From-Other-Eras]].

## Weapons and ammo

The **Weapons** box on a unit's page lists its weapons (Weapon 1 is the main gun). **How weapons and ammo work**, under
it, has these steps too.

1. **Each weapon fires one ammo.** The list beside it picks which: any of the game's ammo, sorted by type (AP, HE,
   anti-aircraft, machine guns, bombs, rockets...), or a copy you made. Its muzzle flash and sound come with it.
2. **The ammo decides what the weapon does:** its damage, range, rate of fire and what it can hit. **Open the ammo**
   to see and change its numbers.
3. **Changing an ammo changes every unit that fires it** (its page lists them). For one unit only: on the ammo's page
   click **Copy this ammo…**, change the copy, then pick the copy in the weapon's list. A weapon's **range** slider
   asks the same: this unit only, or every unit with that ammo.
4. **Hits** (under a weapon) picks the ground, planes or both. A plane's **Role** box sets how it attacks (below).
5. **Adding or removing a weapon isn't possible yet:** weapons are tied to the model's animations, and we're not that
   far along yet.

## Change a plane's role (Studio 0.9.8.5)

A plane's page has a **Role** box: **Fighter**, **Fighter-bomber**, **Bomber** or **Scout**. How it flies and attacks,
how the computer players use it and its build menu words change with it.

- **Bomber:** a bomber drops its bombs on a straight run, and only from a bomb bay. Pick bombs for one of its weapons
  first (Weapons, below), then make it a Bomber: its bombs go in a bomb bay copied from a game bomber's, and you can
  change them there. This is the fix for a fighter-bomber given carpet bombs that dropped nothing. Seen in the game.
- **Scout:** a plane with guns stays able to attack (the box says **Scout, keeping its attacks**) and gets the scouts'
  sight. Seen in the game with a Stuka and an ME109.
- A paratroop plane keeps its role. **Undo** beside the box gives the game's role back, its bombs where they were.

## Make a vehicle recon (Studio 0.9.8.5)

A ground vehicle's **Role** box: **Recon** gives it the recon cars' sight (much further than a tank's), how the
computer players use them, their build menu words, and it can go into woods. It stays as tough and armed as it is.
Seen in the game with a Panzer IV.

## What a weapon hits (Studio 0.9.8.5)

Under each weapon, **Hits** picks **The ground**, **Planes**, or **The ground and planes**. Planes: the weapon fires a
copy of its ammo that hits planes (and does nothing to the ground). Both: it keeps its ammo and gets a second weapon
beside it for planes, the way the game's AA guns carry one for each. A tank firing at planes is seen in the game; a
plane's gun set to hit the ground alone does no damage yet.

## Test it

**Test in game** builds the mod and starts R.U.S.E. Look for the unit where it's built (its factory) in a battle (main menu: **BATTLES**, then a map).

**Next:** [[Export and share|Export-and-Share]]
