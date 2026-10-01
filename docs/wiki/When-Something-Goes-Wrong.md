# When something goes wrong

Find what you see, and follow the fix.

## A red bar under the Studio's header

That's the **mod check**. The Studio reads every file of your mod the way the game build will, when you pick the mod
and again before **Test in game**, and names each file that has a mistake.

- **Set aside** (next to a broken map file) renames it `<name>.broken.toml` beside the original: nothing is lost, the
  mod works without it, and that map starts clean.
- A problem in `mod.toml` or the unit edits has no Set aside: open the file and fix the line the bar names, or ask in
  [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Known case: RUSE Studio 0.7.0 and earlier saved **Water** strokes without their water level ("the water brush
> needs level"). 0.7.1 fixes it; **Set aside** clears an old file.

## "Windows protected your PC"

The apps are new to Windows' reputation check. Click **More info**, then **Run anyway**.

## "[WinError 5] Access is denied" when testing or playing

Windows refused to remove a copy of the game the app made (in `RUSE-Instances`). Also: "An old modded copy at
`...\RUSE-Instances\<name>.old` can't be removed", on every second **Test in game** or **Play**.

- **Update first** (the apps offer it when they open): from RUSE Studio 0.7.6 and Launcher 0.2.11, a copy Windows
  won't delete never stops a test: it's moved into `RUSE-Instances\.trash` and removed there once nothing holds it.
- **R.U.S.E. still running from an earlier test?** The app says so, with the program's name: close the game (check
  the Details tab of Task Manager for `RUSE.exe`), then try again.
- **With an older version:** delete the folder the message names (`...\RUSE-Instances\<name>.partial` or `.old`;
  Windows asks about read-only files: say yes; only the copy goes, never the game), then try again. If Windows
  refuses, restart Windows first.
- Still there? [[Report it|Report-a-Bug]] with the whole message.

## The app can't find R.U.S.E.

**Settings > Game folder > Choose folder...** and pick the folder that holds `RUSE.exe` (on Steam:
`steamapps\common\R.U.S.E`).

## The game starts, but without my changes

1. Was it started from **Play** (launcher) or **Test in game** (Studio)? From Steam, the game starts unmodded.
2. Map changes show only on that map: in the main menu click **BATTLES** and pick it (the Studio's message after
   Test in game says which button and map).
3. Is the mod in the set, and is a mod lower in the order changing the same thing?

## The game crashes

Write down what you did just before (which map, which order, what was on screen), take a screenshot, and
[[report it|Report-a-Bug]]. Crash reports on edited maps are how the map tools got solid.

## Something else

[[Ask a question|Ask-a-Question]].
