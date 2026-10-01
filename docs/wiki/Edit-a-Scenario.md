# Edit a scenario

> **For:** modders · **You need:** RUSE Studio 0.7.2 and a mod · **Takes:** a few minutes

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

At the top of the map, tick **Scenario** and pick one from the menu. Starting points show as pillars in each side's
colour, spawns as white diamonds, zones as shaded areas.

## Move a starting point or a spawn

1. In the bar, click **Scenario**, then **Move**.
2. Click the pillar or diamond, then click where it goes.
3. To put it back where the game had it, click it again and choose **Put back**.

## Add units: one or a whole formation

1. In the bar, click **Scenario**, then **Add unit**.
2. Pick the kind (Buildings, Ground, Infantry, Air), then the type, then the unit in the list (grouped by nation).
3. Pick the **side** it belongs to.
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
3. Click **Add starting point**, pick the **team**, then click open ground where that player starts, away from the
   others. It takes the team's next place, and its camera and intro from a teammate.
4. When the line says **Every player has a starting point**, **Test in game** and open **BATTLES**: the map is listed
   with its new count, e.g. *(8) Cotentin (4v4)*.

A starting point you added moves with **Move**, or goes with **Remove**. More than 8: not yet (the game's own
limit is still to test).

> [!NOTE]
> New, not yet checked in the game: tell us in [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)
> how an 8-player game goes.

## See your units in the game

1. Click **Test in game** (at the top of the Studio). The Studio builds your mod into its own copy of the game
   (`RUSE-Instances\studio-<your mod>`, next to your game) and starts R.U.S.E. from it. The message at the bottom
   says what to open, for example **BATTLES > D-Day**.
2. In the game's main menu, click that button (**BATTLES** for a battle), then pick the map (**D-Day**).
3. Set up the game as usual and start. Your units appear where you placed them.

> [!NOTE]
> Starting R.U.S.E. from Steam starts the game without your mod. Use **Test in game** (or the launcher's **Play**).

> [!NOTE]
> Which side number is which player in a battle is still being tested. Try Side 1 first, and tell us what you find in
> [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Next:** [[Export and share|Export-and-Share]]
