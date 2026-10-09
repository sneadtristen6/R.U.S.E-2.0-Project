# Units from other eras

> **For:** modders · **You need:** RUSE Studio 0.9.8.2 or later and a mod · **Takes:** a minute or two per unit

366 units from WWI to today sit beside the game's own in the **Units** tab: WWI, WWII+, Cold War and modern
tanks and planes, all in one game. Each is another maker's free 3D model (CC BY), already fitted to the game and given its
nation's markings, and credited. None of them is in your mod until you add it.

## Get an era's units

1. On the **Units** tab, pick an era above the kinds: **WWI**, **WWII+**, **Cold War** or **Modern** (**Vanilla** is
   the game's own units, the list as always).
2. The first time, the Studio says how many units the era has and how big it is, with **Download the WWI units** (or
   that era's). It downloads them from the project's GitHub, checks every file before it's used, and lists them.

   | Era | Units | Download |
   |---|---|---|
   | WWI | 61 | 232 MB |
   | WWII+ | 32 | 198 MB |
   | Cold War | 149 | 996 MB |
   | Modern | 124 | 709 MB |

3. A downloaded era updates itself when newer units are put up: the Studio says so and fetches them.

The era's units are filtered like the game's: kind (ground or air), nation (China too), type, and the search box.

## Add one to your mod

1. Click a unit. Its page shows its model's picture and its maker: **Model by** the maker, the licence, and a link to
   where they shared it.
2. Fill in the form:
   - **Name of the new unit** (shown in every language).
   - **Start from**: the game unit whose values it starts with (speed, armour, weapons, how it plays). The suggested
     one is first; any unit of its kind can be picked.
   - **Price** (every battle date).
   - **Size**: 1 is as long as the start unit. The suggestion is its real size (its real width, a plane's wingspan,
     at the game's own scale); anything from 0.2 to 5.
   - **Build menu**: the nation and the factory it's bought at.
   - **Researched from**: the unit it's researched from, or **None: buyable from the start**, with its **Research
     price** and **Research time** (type the time in seconds or minutes: the picker beside it).
3. Click **Add to my mod**. It's a new unit of your mod now: **Open its page** to change any of its values, its model
   or its card, like any unit. **Take it out of my mod** deletes it again.

## Research chains

A unit can be researched from any unit of its nation's build menu, your mod's own era units too: add a Cold War tank,
then a modern one researched from it. WWI and WWII+ units can be bought straight away; Cold War and Modern ones start as
researched from a suitable unit (the form says which it suggests, and why).

When you take out a unit that others are researched from, **Settings > Research** decides what happens:

- **Warn me first** (the default): the Studio lists the units researched from it, with **Take it out anyway**.
- **Refuse**: the unit stays, and the message says how to change the others first.
- **Re-link them**: each is researched from the removed unit's own parent instead, at its own price and time (or
  becomes buyable from the start).

A unit left researched from one that's gone says so in its **Upgrade and research** box and in the check bar, and the
build stops on it until you pick another unit, or none.

## Credits

Every era unit's maker is credited: on its page, and in your mod's `CREDITS-era-units.md`, which the Studio writes when
you add one. Keep that file with your mod: the models' licence asks for it. The full list of makers is on the
[era units release](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/era-units).

## What's been seen in the game

Seen: they load at once, with their own cards in the build menus; the research tabs and a chain of upgrades; their
own models; their sizes. Not tried yet: towed
guns (the importer can't fit them yet, so they show the start unit's model), and whether the game counts research time
in seconds.
