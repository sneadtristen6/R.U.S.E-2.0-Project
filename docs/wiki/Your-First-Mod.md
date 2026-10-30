# Your first mod

> **For:** new modders · **You need:** R.U.S.E. on Steam · **Takes:** 10 minutes

A full walkthrough: install the Studio, make a mod that makes the M4 Sherman cost $1, and see it in the game.

## 1. Install RUSE Studio

1. Download the installer from the [Studio releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio)
   and run it ("Windows protected your PC": **More info**, **Run anyway**).
2. The first start reads the game's files into an index: a minute or two, once per game update.

## 2. Make a mod

The Studio opens on **What would you like to do?**: **Carry on with a mod**, **Start a new mod**, or **Skip** (tick
**Always skip this screen** to go straight to the tabs from then on; Settings brings it back).

1. Click **Start a new mod**. Its steps show in a bar on top, with **Back** and **Next**:
   - **Name:** type a name, for example `cheap-sherman` (the name players see in the Launcher).
   - **Nations:** for each nation, **Keep its units** (its build menus as in the game) or **Start it empty**.
     **Change** gives a nation a new name and flag ([[Make a nation into another|Make-a-Nation]]).
   - **Research:** **Keep the game's research**, **No research** (every unit can be built from the start), or
     **Custom**.
   - **Buildings:** each nation's buildings and what they build ([[Buildings and build menus|Buildings-and-Build-Menus]]).
   - **What else:** tick what you want to change next (units' values, AI and player settings, music and sounds, any
     other value); each opens as its own tab. For this walkthrough, tick **Units' values**.
2. Keep the game's units and research, and press **Next** until the Units tab opens.

Already in the Studio? The header's **Mod** menu has **New mod...** too: type a name and click **Create**.

From now on, everything you change is saved in this mod, never in the game.

## 3. Change the Sherman

1. Open the **Units** tab and type `sherman` in the search box.
2. Click **M4 Sherman**.
3. Find its price and type `1`. It's saved at once, and the old value shows next to it. **Undo** puts it back.

## 4. Test it

1. Click **Test in game** (header). The Studio checks the mod, builds the modded copy (one for the whole PC, `RUSE-Instances\Modded game` on the game's drive, or the folder you chose in Settings) and starts R.U.S.E.
2. In the game's main menu, click **BATTLES** (a free game against the computer), pick any map, play the USA and
   open the tank factory: the Sherman costs $1.

> [!TIP]
> If a red bar appears under the header instead, the mod check found a mistake in a file of your mod. See
> [[When something goes wrong|When-Something-Goes-Wrong]].

## Where to go next

- More on units: [[Edit units|Edit-Units]]
- Maps: [[Shape the ground|Shape-the-Ground]]
- Share it: [[Export and share|Export-and-Share]]
