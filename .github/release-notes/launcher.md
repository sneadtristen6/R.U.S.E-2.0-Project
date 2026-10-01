**RUSE Launcher 0.2, for players.** It finds R.U.S.E. through Steam, and **Play** builds a modded copy of the game
with your mods and starts it. Your Steam install is never changed.

**0.2.11:** **Play** works every time: a modded copy Windows won't delete (a file an older version linked, a
program still holding it) is moved aside into `RUSE-Instances\.trash` instead of stopping the game, and a game still
running from the copy is named. Mods with new bridges never make ground units can't reach (it crashed the game).

**0.2.9:** **Play** works when your game's files are marked read-only: it failed with "[WinError 5] Access is
denied" once a modded copy was left half-built. If the game is still running from the modded copy, you're told to
close it instead of getting a Windows error. Mods with new roads build their painted roads and bridges.

**0.2.8:** a mod you add is checked at once, the way the game build will read it: a broken map file, or a map
folder named after the map's title (maps/Blitz instead of maps/SuperCrossRoads4), is named with its fix before
Play would stop on it.

**0.2.7:** **Help** and **Report a problem** in the bottom bar: the wiki (a field manual for playing mods),
and a bug report in your browser with the launcher's version filled in. A problem message has its own **Report**
link. Nothing is sent by the launcher: you read the report and post it. Mods whose map folder is named after the
map's title (maps/Blitz instead of maps/SuperCrossRoads4) now get told the fix.

**0.2.6:** a **Settings** button (top right): the language, the game folder and updates in one place, ready
for more.

**0.2.5:** finding updates is sturdier: when GitHub turns the one check at start away (it allows 60 an hour per
internet address, shared by everything on it), the launcher reads GitHub's release list instead.

**0.2.4:** your language is kept through restarts, updates and reinstalls.

**0.2.3:** the red box folds up like the yellow one (a big set can list dozens of clashes).

**0.2.2: Put in best order.** When mods in a set change the same values, the yellow box has a **Put in best order**
button: mods that change more go first and smaller ones after, so each keeps as much of its changes as it can. It
says which mods it saves, and the mods can still be moved by hand.

**0.2.1: mods that don't go together can't be played, and the launcher says why.** When two mods in a set replace
the same file or script, a red box names the mods and what they both change, and Play stays off until one is taken
out. When a later mod only overwrites values of an earlier one (a ship's speed, say), a yellow box lists
them and the set still plays.

**New in 0.2:**

- **Mod sets made in the window:** new, edit, rename, duplicate, delete, and put the mods in order. No more files to
  edit by hand. A three-step guide on the first screen shows the way.
- **Add a mod file…** (or drop it on the window): a `.rusemod` exported by RUSE Studio, a mod folder in a `.zip`, or
  a **RUSE Mod Manager `.rmod`**, used as it is (applied by LittleGroove's own engine).
- **Share a load order** as text, and **Import a load order…** from a friend: the launcher says which mods you have,
  which are missing and which are another version, then makes the set. It's the same text RUSE Mod Manager copies
  and reads, so load orders go both ways.
- **It updates itself:** from this version on, when a newer launcher is out, a bar says so; **Update** downloads it,
  checks its SHA-256 and installs it, and the launcher starts again by itself.

Your mod sets from 0.1 are kept. Problems and ideas: GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
