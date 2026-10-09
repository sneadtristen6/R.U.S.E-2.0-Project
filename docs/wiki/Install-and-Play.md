# Install and play

> **For:** players · **You need:** R.U.S.E. on Steam, installed · **Takes:** 5 minutes

## 1. Install the launcher

1. Download the installer (`.exe`) from the
   [launcher releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. Run it. If Windows says "Windows protected your PC", click **More info**, then **Run anyway** (the app is new to
   Windows' reputation check; its code is public on GitHub). Beside **Create a desktop shortcut**, leave **Keep a
   clean copy of my game's files** ticked: the apps never change the game's folder, but other mod managers and hand
   edits can, and every modded game is built from those files. The copy is made the first time the app starts (a
   few minutes, about as much disk space as the game, in `RUSE-Backup` on the game's drive); then **Settings > Clean
   game backup** can check the game's files and put back any that changed.
3. Start **RUSE Launcher**. It finds the game by itself. If it can't: **Settings > Game folder > Choose folder...** and
   pick the folder that holds `RUSE.exe`.

## 2. Add a mod

1. Click **Add a mod file...** and pick the file, or drag the file onto the window.
2. The launcher takes `.rusemod` (made with RUSE Studio), `.rmod` (made for RUSE-Mod-Manager) and `.zip` (a zipped
   mod folder).
3. It checks the file first. A file that isn't a mod, or that holds a program, is refused with the reason.
4. An old mod that comes as the game's own files (`.dat` packs you were meant to copy into the game folder): click
   **Convert an old mod...**, pick its folder, give it a name and click **Convert and add to the library**. The
   launcher compares each pack with your game's clean files (your clean backup, when you've made one in Settings) and
   keeps only what the mod changes. Your game folder isn't touched. It uses LittleGroove's converter.

## 3. Make a mod set

1. A **mod set** is a list of mods in load order. When two mods change the same thing, the lower one wins.
2. Click **New mod set...**, add the mods you want and put them in order.
3. If two mods can't be played together, the launcher says which and why. When two mods change the same game file,
   it says so before **Play**, and **Use the one from…** picks which mod's file the game gets.

## 4. Play

Press **Play**. The first time, the launcher builds the modded copy of the game (a minute or so); after that, only
what changed. Then R.U.S.E. starts.

> [!NOTE]
> Starting R.U.S.E. from Steam starts the game **without** mods, as always. Your Steam install is never changed.

## Updates

The launcher checks for a new version each time it starts. Click **Update** when it offers one.

## Linux and Steam Deck (through Proton)

From Launcher 0.4.8.2 and Studio 0.9.8.2, when an app's own window can't show its pages (under Proton it stays blue,
because Microsoft's WebView2 doesn't start there), the app opens in your web browser instead, and a small box says
so: keep the box open while you play, and close it to close the app. Not tried on Linux yet: please tell us how it
goes in [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Next:** [[Play with friends|Play-With-Friends]]
