**RUSE Launcher 0.4, for players.** It finds R.U.S.E. through Steam, and **Play** builds a modded copy of the game
with your mods and starts it. Your Steam install is never changed.

**0.4.1:** your language from the first start, and a mod set editor that finds mods by name.

| Before | Now |
|---|---|
| Making a mod set listed your whole library with Create at the bottom, and no way to find a mod by its name. | Create is at the top, with the mods already in the set right under it; below, "Add mods from your library" with a search that narrows the list as you type. |
| The language sat in Settings, so players didn't know the Launcher speaks their language. | The first start asks: "Choose your language", each language in its own words, the one your game is set to in Steam marked (players updating see it once). Then a language button at the top, always in sight. |
| Windows' list of installed apps showed the first version ever installed. | It shows the version you have. |

**0.4.0:** plays mods with new roads the way Studio 0.9 builds them: they look like the map's own roads, from high
up and right down at the ground (tested in the game on D-Day). [How roads were cracked](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/ROADS.md).

![A new road up close on D-Day](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Before | Now |
|---|---|
| A mod's new roads vanished up close. | They're drawn with the map's own asphalt and edge stickers, painted the way the map's roads are, with the plants on their path taken off. |
| A mod with many erase circles took minutes to build. | Much faster. |

**0.3.3:** plays mods made with Studio 0.8.3.

| Before | Now |
|---|---|
| A mod with a turned opening camera (Studio 0.8.3) was refused. | Built: the camera is turned as the mod says. |
| A moved starting point's opening camera stayed at the old place. | The camera moves with it; a new starting point gets a camera of its own. |
| A mod with a starting point in a wood was refused. | Built: an HQ works there. |

**0.3.2:** one game copy for the whole PC, the version shown, and a clearer library.

| Before | Now |
|---|---|
| Each mod set built its own copy of the game. | One modded copy for the whole PC, shared with the Studio. |
| The version wasn't shown, and What's new was a list. | The version is beside the name, and What's new opens a before/after table like this one. |
| Maps and mods looked the same in the library. | A map has a MAP badge. |
| Few tooltips. | Tooltips on the main controls. |
| Mods with new roads on Twilight of the Gods, Alpha, Ostfriesland and Robert missed the map's road model. | They get it too. |

**0.3.1:** mods with units from another nation (a German Tiger for the US, say) work, even in a match where nobody
plays that nation (tested in the game, 2026-10-02). And a new look: R.U.S.E.'s blues instead of black and gold, and a new logo: a fighter climbing through the
clouds. The sidebar has two tabs, **Mod sets** and **Mod library**, each with the whole height, so your whole library
can be reached (half of it was hidden behind the scrollbar), with a search and a count. The installer offers a
**clean game backup** beside the desktop shortcut, and says why.

**0.3.0:** **Supported mods:** the launcher shows our mod list
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)); tick the ones you want and they're
downloaded and checked. On first run you choose your mods; cheat mods are kept apart and never ticked for you. A
**Troubleshoot** button (bottom bar, and on every problem message) checks in one go what can stop **Play** and fixes
what it can, with a report to paste in a bug report. A **clean game backup** in Settings keeps a clean copy of your
game's files and puts back anything another mod manager changed (or let Steam repair it). Mods made with the new
Studio work as made: tanks and infantry cross new bridges on the deck, infantry follow new roads, cleared woods are open
to units, placed buildings stand on the ground at any size, and cover lands where it was painted on D-Day and the
other maps that aren't square. Known issue: new roads aren't drawn up close yet (they show from afar).

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
