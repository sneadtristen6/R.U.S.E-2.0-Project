**RUSE Launcher 0.4, for players.** It finds R.U.S.E. through Steam, and **Play** builds a modded copy of the game
with your mods and starts it. Your Steam install is never changed.

**0.4.8.17:** Imported models sit where the unit stands, their turrets and propellers in their own places; an ammo can have a weapon class of its own.
<!-- required update -->

- **A required update:** older versions can't be used any more. When the app opens it installs this one by itself, and **Play** waits until it's in.
- **Mods with imported models of the new kind:** the Studio now fits a unit's imported model where the unit stands, with a skeleton of its own, so its turret turns where the turret is on the model, and a plane's propellers spin where the model has them, as many as it has; soldiers, a gun's crew and more planes can take models of their own too. Play such mods with this Launcher or newer: an older one gives the model the copied unit's skeleton, so its turret turns around the wrong point. Mods made before play as they did. Tested in the game on test copies built the way the Launcher builds; not played through the Launcher itself yet.
- **An ammo's own weapon class:** a mod can now give an ammo its own damage against each kind of target (made on the Studio's ammo page). Nothing changed in the Launcher for it: such a mod builds like any other.

**0.4.8.16:** Troubleshoot keeps the game copies you made yourself.

- **Fixed: Troubleshoot's "Clear them" deleted copies you made yourself.** A copy of the game you built by hand in the copies folder, a test copy or a reference copy, counted as a leftover, and "Clear them" removed it for good, not to the Recycle Bin. Every copy built anywhere but the app's own modded copy now carries a small keep note, and a copy with one is never a leftover: Troubleshoot clears only the apps' own leftovers (half-built copies, the ones older versions made per mod set). Found on our own PC on November 1, when it took every test copy there. A copy built before this version has no note yet: rebuild it once with this version, or leave "Clear them" alone until you do.

**0.4.8.15:** Vanilla gets the gold R.U.S.E. 2.0 title too.

- **Vanilla gets the gold R.U.S.E. 2.0 title too:** Play on Vanilla now builds the modded copy with no mods and the gold title, and starts the game from it, the way a mod set does: the first time it builds, then it starts at once unless you played a mod set in between. RUSE Guard runs in its multiplayer matches, as in every set's. Untick the gold title in Settings and Vanilla starts through Steam as before. Your Steam install is never changed.

**0.4.8.14:** Mods with a match script of their own build again.

- **Fixed: Play stopped on some mod sets** with "RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...": a few mods bring a match script of their own whose header asks for more room than the script needs (1 VS 7 AI, 1 VS 15 AI, Operation Overlord and Sand Box among them). The game runs those scripts fine, but the Launcher refused them, so no set with one of those mods could be built. It now reads them the way the game does.

**0.4.8.13:** Game crash reports say what led to the crash.

- **Bug Watch's game crash reports say more:** if you ticked Bug Watch and the game crashes, the report now also says what the game was trying to read or write, and up to 16 places in the game that led to the crash, read from the game's own crash report on your PC, which still never leaves it. A report that only said where the game stopped couldn't show why; now we can trace crashes like the one a player sent us this week, and fix them.
- **The agreement, version 3:** it now lists these two new things among what a game crash report carries, and nothing else in it changed. Because it changed, both apps show it to you once more when they open.

**0.4.8.12:** Play builds modded games again.

- **Fixed: Play stopped on every mod set** with "No such file or directory: ...fairplay_watch.bin": the installers of 0.4.8.10 and 0.4.8.11 left out three of RUSE Guard's files, so no modded game could be built. They're back in, and an app missing any of its files can no longer be released.

**0.4.8.11:** Sign in through Steam finishes in the apps; on Linux, a build's helper programs start the way they do on Windows.

- **Fixed: Sign in through Steam.** After you signed in on Steam's page, the Launcher and the Studio kept waiting and never asked our server whether you were done: the window stopped its own checks before the first one. It checks every few seconds now and signs you in as soon as Steam says so. Tried in the preview: the check runs and the window shows you signed in.
- **Helper programs start fresh on every system:** the programs a build shares its work out to (imported models, mending the map, movement, water) now start fresh on Linux too, the way they always have on Windows. On Linux they started as copies of the running app, which could now and then hang a build, and made one of our checks fail there. Nothing changes on Windows or under Proton on the Steam Deck.

**0.4.8.10:** mods past 4 GB, build lists in groups, faster builds of big mods, Persian and every page in 11 languages, fixes from testers' reports; and RUSE Guard, our anti-cheat for real multiplayer matches, with a join code; Bug Watch, crash and usage reports you can opt into; Sign in through Steam; and a first-start agreement.

- **Fixed, reported by a player: mods past 4 GB.** A mod set whose modded game passed 4 GB stopped building at Play ("'I' format requires 0 <= number <= 4294967295"). Packs now carry their full length, and one past 4 GB is written in a wider layout that a small game patch lets the game read: downloaded once and applied only to your modded copy, never to the game in your Steam folder. Past 32 GB, or for one file past 4 GB, the build says so plainly. Tested in the game: copies past 4 GB, and with 200, 283 and all 366 era units.
- **Many models of your own:** the game finds a pack's texture stand-ins through an index, and a build that added stand-ins for imported models wrote it wrong: with many era units the game hung or crashed while loading. It's now written the way the game reads it, for every mod that adds them. Tested in the game with all 366 era units.
- **Build lists in groups:** a mod with many units gets each building's build list in groups, the game's own lines: at most 6 units a group and 10 groups a building, so the whole list stays on the screen and every unit can be built. A mod made before that's over the limits still builds, with a warning. Tested in the game with 297 era units in groups.
- **Faster builds:** the models in your mods are kept between builds, and new ones are made side by side on your PC's cores. A mod with 366 era units took about 18 minutes to build on an 8-core PC; now about 5 the first time and about 3 after, with the same game files, byte for byte.
- **Testers' reports:** a unit mod and map changes made under one name build together (they stopped Play); a map whose own bridges are taken out builds with the new bridges; imported turret parts and towed guns build as Studio 0.9.8.10 makes them. The bridges and turret parts not tried in the game yet.
- **Your files:** Remove sends a library mod to the Recycle Bin, Show in folder opens a mod where it is, and Settings shows where your files are kept. Seen in a preview; not tried in the app window yet.
- **Persian and 11 languages:** Persian is the apps' 11th language, written right to left; the README, the wiki, these notes and the setup screens are in all 11.
- **Required updates:** an update we mark required installs by itself, with a box nobody can close (apps from this version on can read the mark).
- **Owned copies only:** before Play builds a modded copy, the apps check that the game folder is a copy you own, from what Steam left there, on Windows, under Proton on the Steam Deck and on Linux. If yours can't be confirmed (a boxed copy from before R.U.S.E. was on Steam), a box lets you open a ticket, and we send you an unlock code for that PC.
- **Discord:** the apps and pages use a new invite that doesn't expire.

- **A first-start agreement:** the first time the Launcher or the Studio opens, it says what RUSE Guard does and asks you to accept it (it's required to play online with the apps), whether to turn Bug Watch on (optional), and a username our developers see with your reports: a # and four numbers are added so it's unique, like Nick#4821. One name works for both apps. The agreement shows again when it changes. Seen in both apps. In all 11 languages.
- **RUSE Guard:** our anti-cheat, from DomesticNukes' design. It works only in multiplayer and co-op matches, never in single-player, skirmish against the computer or the campaign. Your modded game gets a **join code** to send to the people you play with: the same code means the same game, the same version, mods and mod versions, so a match can't drift apart. A mod that changes the game's scripts shows a **Runs scripts** badge, and Play waits until you tick that you trust its author; a cheat or a test tool shows **Cheat** and makes the copy offline-only: it leaves multiplayer and co-op matches by itself. During a real match RUSE Guard checks the names of your running programs against a list of known cheat tools (names only; nothing else is read), and what it collects is filed under your username, never your Steam account. Tested in multiplayer matches with a real opponent; the evidence reaches our server.
- **Bug Watch (optional):** when you tick it, the Launcher and the Studio count what you use and when something goes wrong, the apps' crashes and the game's, with which mods were on, and send it once a day to our developers with your username. No real names, no Steam account, no files. Off unless you tick it; untick it any time and what was kept is deleted. Seen in both apps.
- **Sign in through Steam:** a sign-in on Steam's own page in your browser confirms you own R.U.S.E., for online play, RUSE Guard and content downloads. We never see your password, and your Steam ID is never stored: only a pass kept on your PC for 30 days. It's in Settings, **Steam sign-in**; the Launcher asks once. Nothing needs it yet. Not tried in the app yet.

**0.4.8.9:** mods install on more PCs, and a safer picture reader.

- **Fixed, reported by a player:** on some PCs no mod would install: "this PC doesn't trust the site's security certificate (unable to get issuer certificate)". Windows on those PCs hasn't got the certificate GitHub's downloads are checked against and can't fetch it. The Launcher now also tries with the list of certificates Firefox uses, which it carries. Until then, a mod downloaded in your browser from the mod list installs with **Add a mod file…**.
- **Safer pictures:** the library the Launcher reads pictures with (Pillow) is now version 13.0.0, with its fixes for specially made picture files that could crash the app, use up its memory, or worse.
- **Tighter code:** the 12 warnings GitHub's code check gave on this project are answered. When the Launcher shows its pages in your web browser, they open only its own files, checked in a way that check recognises, and downloads ask for TLS 1.2 or newer, as they already did. Nothing changes in how the Launcher works.

**0.4.8.8:** it plays mods made with Studio 0.9.8.8, and your modded game says R.U.S.E. 2.0 in gold.

- **Mods made with Studio 0.9.8.8 play:** buildings of their own (the second and third a nation need a small game patch, downloaded once and applied only to your modded copy, never to the game in your Steam folder), new buildings' own looks and props, sounds and animations changed with RUSE Decoy, the computer players' values and the game rules, and old bridge crossings closed.
- **R.U.S.E. 2.0 in gold:** your modded game opens on a battle scene with an engine starting, and its main menu, every menu's small title, the menus' outlines and the loading screens say R.U.S.E. 2.0 in gold. It's made on your PC from your own game's files the first time (a few minutes once, then kept). Settings has a tick box to keep the game's own title.
- **Fixed: dark and light blotches on maps made with the Studio** (blank, bigger, relief and sector maps): such a map is lit right once it's built with this version (its ground is made again the first time).
- **Fixed, reported by a player:** on the Supported mods page, "New mod set…" did nothing. It opens the new set now. Not tried in the app itself yet.
- **The game's lettering:** the Launcher is written in the game's own menu font, taken from your game each time it starts.
- **Still buggy, play at your own discretion:** maps made with Map Paint's textures, and blank maps (Blank Terrain, Blank Ocean).

**0.4.8.7:** it plays mods made with Studio 0.9.8.7.

- **Mods made with Studio 0.9.8.7 play:** objects moved or placed in grids, boxes and along paths, bigger blank maps with their sectors, and Nuclear-only economy changes.
- **The build's lines in your language**, in all ten.
- **Kept build results stay good after an update.**
- **Still buggy, play at your own discretion:** maps made with Map Paint's textures, and blank maps (Blank Terrain, Blank Ocean).

**0.4.8.6:** it plays mods made with Studio 0.9.8.6.

- **Mods made with Studio 0.9.8.6 play:** blank maps with shadows over flat ground, what's placed where the copied map had sea drawn, and the camera's floor on the new ground.
- **A known crash refused:** a mod whose armed plane carries the recon flag without the fighter flag crashed the game when the plane was sent to attack; the Launcher now refuses to build it and says why.
- **Still buggy, play at your own discretion:** maps made with Map Paint's textures, and blank maps (Blank Terrain, Blank Ocean).

**0.4.8.5:** it plays mods made with Studio 0.9.8.5.

- **Mods made with Studio 0.9.8.5 play:** planes in a new role (a bomber with its bomb bay, a scout that keeps its guns), recon vehicles, weapons that hit planes, and ground painted from the Texture brush's library with the game's detail over it. An older Launcher can't build some of them.
- **Faster:** a map painted again the same way takes its painted ground back from the last build in seconds.
- **Still buggy, play at your own discretion:** maps made with Map Paint's textures, and blank maps (Blank Terrain, Blank Ocean).

**0.4.8.4:** mods download on every PC, and it plays mods made with Studio 0.9.8.4.

- **Mods download on every PC:** on some PCs no mod would download ("certificate verify failed: unable to get local issuer certificate"). Now the Launcher asks Windows for the certificate, as a browser does, and tries again; its own updates too. Not tried yet on a PC that had the problem.
- **Mods made with Studio 0.9.8.4 play:** missions of their own, blank maps with their HQs and sectors, depots with more trucks (an older Launcher refuses depots over 1,000 trucks), units with their own looks and uniforms, edits of other people's mods under their own names.
- **Still buggy, play at your own discretion:** maps made with Map Paint's textures, and blank maps (Blank Terrain, Blank Ocean).

**0.4.8.3:** modded copies go where you say.

- **Where modded copies go**, in Settings: choose the folder the modded copy of the game is built in, or go back to
  the recommended place, `RUSE-Instances` on the game's drive (there the copy shares the game's files and is ready in
  seconds; on another drive it is a full copy of the game, slower and bigger). The game's clean backup goes beside it.
  The next Play builds in the new place; the old folder can be deleted by hand. The Studio uses the same folder.

**0.4.8.2:** it opens in your web browser where its own window can't, and plays mods made with Studio 0.9.8.2.

- **Linux and Steam Deck (through Proton):** the Launcher opens in your web browser when its own window can't. Not
  tried on Linux yet: tell us how it goes.
- Mods made with Studio 0.9.8.2 play: units from other eras with their own models, sizes, research and cards.

**0.4.8.1:** it converts old mods, and plays mods made with Studio 0.9.8.1.

- **Convert an old mod…**, LittleGroove's Convert brought over: an older mod that comes as the game's own packs, made to
  be copied into the game folder, becomes a mod your library plays beside others. Not tried with a real old mod yet.
- **Two mods changing the same game file:** the Launcher says so before Play, and **Use the one from…** picks which.
- Mods made with Studio 0.9.8.1 play: songs and voices, a nation made into another.

**0.4.8:** it plays mods made with Studio 0.9.8, new maps that start blank among them, and shows what's new in your
own language.

| Before | Now |
|---|---|
| A new map showed the menu pictures of the map it copied. | Its own pictures, as its maker made them, with the start dots where its players start. |
| A unit built on a drained sea could crash the game. | Fixed (seen in the game). |
| Old river water stood as walls along a map's edge, and erased lighthouses still shone over the sea. | Fixed (seen in the game). |
| A mod that erases a whole map could run the PC out of memory while it was built. | It builds. |
| What's new was in English only. | It's in the Launcher's own language. |

Known: **navy maps aren't finished.** Blank Ocean builds and plays, but units under its water haven't been tried yet.

**0.4.7:** very large map mods now build in minutes (before, they took a very long time), and it plays mods made
with Studio 0.9.7.

| Before | Now |
|---|---|
| **Play** could take hours to build a big map mod. | The most extreme one we have (BATTLES > D-Day with its sea drained) took about four hours; now under 10 minutes, with the same result. |
| A big map mod's first build worked everything out on your PC. | A mod exported with Studio 0.9.7 carries what its build worked out for the map's movement: your first build of it is shorter. Every answer is checked, and the game files come out the same. |

Known: **navy maps aren't worked out yet.** A drained or painted sea builds and loads, but the water still shows.

**0.4.6:** **Play** starts at once when nothing changed, and plays mods made with Studio 0.9.6: new units with a 3D
model of their own.

| Before | Now |
|---|---|
| **Play** rebuilt the whole modded copy every time, even with nothing changed (a player: "waiting 30 minutes every time"). | Nothing changed: the game starts at once. A change rebuilds, but the last copy's unchanged files are reused, so a copy on another drive than the game no longer copies every pack again. Play says how much it copied. |
| Every build read the game's unit data afresh. | Kept between builds: a big test mod took 213 s every time; now the next builds after the first take 68 s. |
| A mod's new unit had the model of the unit it copies. | Its own model from the mod (`files/models`) is in the game. **Seen in the game:** an M1 Abrams beside the Sherman. |
| A mod's new unit with its own card crashed the game when it was built. | Fixed. **Seen in the game.** |
| Repainted units' colours came out a little off in places. | Closer to the mod's picture. A mod with repainted units or painted ground gets a new fingerprint and join code: everyone playing together should update. |
| A slow start left no clue. | **Copy report** lists the last five starts' steps. |
| — | Plays mods with Studio 0.9.6's whole-map erase, roads on reshaped ground and riverbed fill (new, not yet seen in the game at scale). |

**0.4.5:** plays mods made with Studio 0.9.5: repainted units, their own cards, and units with models of their own.

| Before | Now |
|---|---|
| A mod couldn't change how a unit looks. | Repainted units and cards from a mod show in the game. **Seen in the game:** a red Sherman, a card made in the Studio. |
| A mod whose unit model packs grew was dropped by the game: a crash at the first factory. | Built the way the game checks them. **Seen in the game:** a second Sherman with a model of its own. |
| A mod spawning another nation's units in a campaign chapter or Operation crashed while loading (French units on Holland). | Their models load there too. **Seen in the game.** |
| Flattening the mountains at a map's edge left a cliff there. | The edge follows the ground. **Seen in the game.** |

**0.4.4:** plays mods with new maps, made with Studio 0.9.4's Duplicate map.

| Before | Now |
|---|---|
| New maps from a mod hadn't been tried in the game. | **Seen in the game:** a mod's new map is listed in BATTLES and plays its own ground, 101 at once. Early: report what you find. |
| Updates came only as whole versions. | Small fixes can come between versions (0.4.4.1), offered like any update. |

**0.4.3:** plays mods made with Studio 0.9.3, and builds them about three times faster.

| Before | Now |
|---|---|
| Rocks and most other props a mod placed vanished as soon as the camera left close range. | Drawn out to the far distance; the map's own objects unchanged. **Seen in the game.** |
| A mod's new road through a wood was a bright strip from high up, or gone from medium-long range. | Painted through woods the way the map's own roads are. **Seen in the game.** |
| A mod's roads always took the trees off their path. | A road can keep them (`keep_trees`): it runs under the trees, fainter and greyer in a wood. |
| **Play** took about 5 minutes to build a mod with new roads on M03_Italie. | About 1½ minutes after the first time on a map. |

**0.4.2:** plays mods made with Studio 0.9.2.

| Before | Now |
|---|---|
| A mod with a road over water on Italy, Germany, Holland and other maps was refused: its bridge "would have no floor". | Built: the bridge gets the map's own floor. Not yet seen in the game on those maps. |
| A mod giving units to the player in a campaign chapter (side 0) was refused, and units for the computer's sides were warned "may never appear". | Built; only a side the chapter's mission doesn't have is warned. |
| On M03_Italie and other maps, a mod's new road out in the open hid the map's scenery from far, and its props showed only up close. | The map's far view stays as it was, and the mod's props show from far. Not yet seen in the game. |

**0.4.1:** your language from the first start, and a mod set editor that finds mods by name.

| Before | Now |
|---|---|
| Making a mod set listed your whole library with Create at the bottom, and no way to find a mod by its name. | Create is at the top, with the mods already in the set right under it; below, "Add mods from your library" with a search that narrows the list as you type. |
| The language sat in Settings, so players didn't know the Launcher speaks their language. | The first start asks: "Choose your language", each language in its own words, the one your game is set to in Steam marked (players updating see it once). Then a language button at the top, always in sight. |
| Windows' list of installed apps showed the first version ever installed. | It shows the version you have. |

**0.4.0:** plays mods with new roads the way Studio 0.9 builds them: they look like the map's own roads, from high
up and right down at the ground (tested in the game on D-Day).

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
