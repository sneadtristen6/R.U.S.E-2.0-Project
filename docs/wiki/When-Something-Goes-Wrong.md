# When something goes wrong

Find what you see, and follow the fix.

## A red bar under the Studio's header

That's the **mod check**. The Studio reads every file of your mod the way the game build will, when you pick the mod
and again before **Test in game**, and names each file that has a mistake.

- **Set aside** (next to a broken map file) renames it `<name>.broken.toml` beside the original: nothing is lost, the
  mod works without it, and that map starts clean.
- A problem in `mod.toml` or the unit edits has no Set aside: open the file and fix the line the bar names, or ask in
  [Discussions > Help](https://github.com/sneadtristen6/Ruse-Mod-Platform/discussions).

> [!NOTE]
> Known case: RUSE Studio 0.7.0 and earlier saved **Water** strokes without their water level ("the water brush
> needs level"). 0.7.1 fixes it; **Set aside** clears an old file.

## "Windows protected your PC"

The apps are new to Windows' reputation check. Click **More info**, then **Run anyway**.

## "[WinError 5] Access is denied" when testing or playing

Windows refused to remove a copy of the game the app made (in `RUSE-Instances`).

- **R.U.S.E. still running from an earlier test?** Close it, then try again: a running game keeps its copy in use.
- **Your game's files marked read-only** (a disc install, a restored backup)? RUSE Studio 0.7.4 and Launcher 0.2.9
  handle that by themselves: update (the apps offer it when they open). With an older version, delete the folder
  the message names (`...\RUSE-Instances\<name>.partial` or `.old`; Windows asks about read-only files: say yes;
  only the copy goes, never the game), then try again.
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
