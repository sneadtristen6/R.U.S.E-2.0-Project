# Install and play

> **For:** players · **You need:** R.U.S.E. on Steam, installed · **Takes:** 5 minutes

**The short version:** download **RUSE-Launcher-Setup** from the releases page, run it, open **RUSE Launcher**, click
**Supported mods**, tick a mod and press **Install**, put it in a mod set, then **Play**. Each step below says exactly
where to click.

You only need **RUSE Launcher** to play mods. **RUSE Studio** is for making them (see the end of this page).

## Step 1: Download the Launcher

1. Open the [launcher releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher) page.
2. The newest one is at the top, marked **Latest** (for example *RUSE Launcher 0.4.8.7*).
3. Scroll down to **Assets** under it and click **RUSE-Launcher-Setup-0.4.8.7.exe** (the version number changes; take
   the `.exe` that starts with `RUSE-Launcher-Setup`). Your browser downloads it.

The other files there (`RUSE-Launcher-notes.json`, *Source code*) aren't needed.

## Step 2: Install it

1. Open the file you downloaded (usually in your **Downloads** folder).
2. **"Windows protected your PC"?** Click **More info**, then **Run anyway**. The app is new to Windows' reputation
   check; its code is public on this GitHub.
3. Click through the installer. Leave **Keep a clean copy of my game's files** ticked: the apps never change your
   game's folder, but other mod managers and hand edits can, and every modded game is built from those files. The
   copy is made the first time the app starts (a few minutes, about as much disk space as the game).
4. Start **RUSE Launcher** (Start menu, or the desktop shortcut). It finds R.U.S.E. by itself through Steam.
   If it says it can't: **Settings > Game folder > Choose folder…** and pick the folder that holds `RUSE.exe`
   (usually `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

## Step 3: Get mods

**From our list (easiest):** click **Supported mods**, tick the mods you want and press **Install**. Each file is
downloaded and checked against the list before it goes into your library.

**From a file someone shared:** click **Add a mod file…** and pick the file, or drag it onto the window. The Launcher
takes:
- `.rusemod`: made with RUSE Studio;
- `.rmod`: made for LittleGroove's RUSE Mod Manager;
- `.zip`: a zipped mod folder.

It checks the file first: a file that isn't a mod, or that holds a program, is refused with the reason.

**An old mod that comes as the game's own files** (`.dat` packs you were told to copy into the game folder): click
**Convert an old mod…**, pick its folder, give it a name and click **Convert and add to the library**. Your game folder
isn't touched.

## Step 4: Pick what to play

1. A **mod set** is the mods you play together, in order. Click **New mod set…**, add the mods and put them in order
   (when two mods change the same thing, the lower one wins).
2. If two mods can't be played together, the Launcher says which and why, before you play.

## Step 5: Play

Pick your mod set and press **Play**. The first time, the Launcher builds a modded copy of the game (a minute or so);
after that only what changed. Then R.U.S.E. starts, with your mods.

> [!NOTE]
> Starting R.U.S.E. from **Steam** starts the game **without** mods, as always. To play with mods, start it from the
> Launcher's **Play**. Your Steam install is never changed.

## Updates

The Launcher checks for a new version each time it starts: click **Update** when it offers one. If the update fails
with "certificate verify failed", download the newest `RUSE-Launcher-Setup` from Step 1 in your browser and run it: it
installs over the old one and keeps your mods.

## Problems?

| What you see | What to do |
|---|---|
| "Windows protected your PC" | **More info**, then **Run anyway** (Step 2). |
| The Launcher can't find R.U.S.E. | **Settings > Game folder > Choose folder…**, the folder with `RUSE.exe`. |
| "certificate verify failed: unable to get local issuer certificate" | Get Launcher 0.4.8.4 or newer (Step 1); see [[When something goes wrong|When-Something-Goes-Wrong]]. |
| The game starts without my mods | Start it with the Launcher's **Play**, not from Steam. |
| Friends can't join my game | Everyone needs the same mods in the same order: [[Play with friends|Play-With-Friends]]. |
| Anything else | [[When something goes wrong|When-Something-Goes-Wrong]], or ask in [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) or on the [Discord](https://discord.gg/DbufY4Jfg). |

## Linux and Steam Deck (through Proton)

When an app's own window can't show its pages (under Proton it stays blue, because Microsoft's WebView2 doesn't start
there), the app opens in your web browser instead, and a small box says so: keep the box open while you play, and
close it to close the app. Not tried on Linux yet: please tell us how it goes in
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## Making mods: RUSE Studio

1. Open the [studio releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio) page. The Studio
   is a preview, so its releases are marked **Pre-release**: take the newest.
2. Under **Assets**, click **RUSE-Studio-Setup-0.9.8.7.exe** (the newest version), run it as in Step 2.
3. Start **RUSE Studio**, then follow [[Your first mod|Your-First-Mod]] (10 minutes).

**Next:** [[Play with friends|Play-With-Friends]]
