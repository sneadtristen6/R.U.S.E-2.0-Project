# Edit a scenario

> **For:** modders · **You need:** RUSE Studio 0.9.8.4 and a mod · **Takes:** a few minutes

A **scenario** is what a map starts with: capture zones, each side's starting point, and units and buildings already
on the field. One map has several: one for each way the game plays it.

## The game's three ways to play a map

These are the buttons on R.U.S.E.'s main menu:

| Button | What it is |
|---|---|
| **BATTLES** | A free game against the computer on one map, with the players you choose (other games call this a skirmish). |
| **OPERATION** | A short mission with set goals, on a ready-made setup. |
| **CAMPAIGN** | The story, chapter by chapter. |

The Studio names every scenario after the button that plays it, and a gold line under the scenario menu says
exactly where: for example **In the game: Battles › D-Day (6 players)**.

## Pick the scenario

At the start of the map screen's bar, pick **Scenario** (beside **Map**). The map's own things (ground, buildings, trees,
roads) show faded and can't be grabbed by accident; switch back to **Map** to change them. Then pick the scenario
from the menu at the top. Starting points show as pillars in each side's colour, spawns as white diamonds, zones
as shaded areas.

## Move a starting point or a spawn

1. On the **Scenario** side, click **Move**.
2. Click the pillar or diamond, then click where it goes.
3. To put it back where the game had it, click it again and choose **Put back**.

## Add units: one or a whole formation

1. On the **Scenario** side, click **Add unit**.
2. Pick the kind (Buildings, Ground, Infantry, Air), then the type, then the unit in the list (grouped by nation).
3. Pick **Who gets it?** For an Operation or a campaign chapter the list is that scenario's own camps, from its mission:
   **Player** (you: camp 0 in the campaign) and the **Computer**'s camps, each with its country, plus **Neutral**. The
   number in brackets is what's saved. A **BATTLES** map takes only neutral units (the game starts it with no team
   list, so a player's units there would never appear).
4. **How many:** 1, 2, 4, 6, 8 or 10.
5. For more than one, pick a **formation**: line, column, wedge, box or circle. It faces up the screen: turn the
   view to aim it. **Spacing** sets the metres between units.
6. Rings on the map show where each unit will stand. Click to place them.

A unit you added can be moved like any spawn, or taken out with **Remove**.

## More players on a map (up to 8)

Each player starts at a **starting point** of their team, one per player: in a 3v3, teams 1 and 2 each have places
1 to 3. A 4v4 needs place 4 in both.

1. Pick the scenario the game plays online (its gold line says **Battles**), then in the bar click **Scenario**.
2. **Players** (on the right) shows the map's count, the game's marked *(game)*. Pick the new count, 8 at most.
   The line under it names each starting point that's still missing, e.g. *team 1, place 4*.
3. Click **Add HQ start**, pick the **team**, then click open ground where that player starts, away from the
   others. It takes the team's next place, and its camera and intro from a teammate.
4. When the line says **Every player has a starting point**, **Test in game** and open **BATTLES**: the map is listed
   with its new count, e.g. *(8) Cotentin (4v4)*.

A starting point you added moves with **Move**, or goes with **Remove**. More than 8: no, the game's lobby has 8
seats (tried 2026-10-02).

> [!NOTE]
> New, not yet checked in the game: tell us in [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)
> how an 8-player game goes.

## A blank map: place each player's HQ

A map started as **Blank Terrain** or **Blank Ocean** (the Maps tab's **Duplicate map**) has nothing of the copied map
on it, its HQs neither. **Each player's HQ** (on the Scenario side) lists every HQ the map needs: click **Place**, then
the ground where it goes. **Test in game** waits until every player has an HQ.

> [!WARNING]
> Both blank maps are still buggy: use them at your own discretion, and tell us what you find.

## Sectors

**Sectors** (on the Scenario side) changes the scenario's sectors, the zones ruse cards are played on. A blank map
starts with none: you make them.
- **Shapes:** drag a corner dot to move a border (the sectors that share it move together). Double-click a border to add
  a dot; right-click a dot to remove it. **New sector:** drag a box on the ground. **No sector:** drag a box where no
  sector should be. **Delete sector** gives all its ground to the sectors round it.
- **Paint:** pick a sector, then drag on the ground to paint it; "No sector" takes ground out of every sector.
- **Start from no sectors** or **Start from the map's sectors**; **Undo** takes back the last change.

Seen in the game: painted sectors on a blank map, a new sector drawn on D-Day and lit up alone by a ruse card, ground
in no sector (a gap on the map table that no ruse card lights). The thin lines the Studio cuts so a sector stays one
piece haven't been tried in the game yet.

## Supply depots on this map

Pick a supply depot to give it more trucks (more trucks, more money in it), or use **Every depot here**: multiply
every depot's trucks (**times their trucks**) or give them all the same number (**trucks each**), then **Apply**.
**Back to the game's** undoes it. To change every map at once, use the Economy tab's **Depots on the maps**
([[Economy, AI and more|Economy-AI-and-More]]). Depots with more than 1,000 trucks need Launcher 0.4.8.4 or newer.

## A mission of its own

A new Operation or campaign chapter can play its own mission, with goals, events and camera moves:
[[Make a mission|Make-a-Mission]].

## See your units in the game

1. Click **Test in game** (at the top of the Studio). The Studio builds your mod into the modded copy of the game
   (`RUSE-Instances\Modded game` on your game's drive, or the folder you chose in Settings: one for the whole PC, the Launcher's too) and starts R.U.S.E. from it. The message at the bottom
   says what to open, for example **BATTLES > D-Day**.
2. In the game's main menu, click that button (**BATTLES** for a battle), then pick the map (**D-Day**).
3. Set up the game as usual and start. Your units appear where you placed them.

> [!NOTE]
> Starting R.U.S.E. from Steam starts the game without your mod. Use **Test in game** (or the launcher's **Play**).

> [!NOTE]
> Which starting point belongs to each lobby player in a battle is still being tested. Tell us what you find in
> [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Next:** [[Export and share|Export-and-Share]]
