---
title: "Studio 0.9.8.15 and Launcher 0.4.8.15: Vanilla gets the gold R.U.S.E. 2.0 title; mods with their own match scripts build again; clearer game crash reports; mods past 4 GB, build lists in groups, RUSE Guard"
category: Announcements
order: 20
skip: never posted; 0.9.8.16, out three days after it, has its own announcement, which covers it
---
**RUSE Studio 0.9.8.15** and **RUSE Launcher 0.4.8.15** are out:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases). Both apps offer the update when they open.

![R.U.S.E. 2.0](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/ruse-2-0-brand.png)

**New in this update: Vanilla gets the gold R.U.S.E. 2.0 title too.** Play on Vanilla in the Launcher used to start
the plain game through Steam, so only modded games had the gold title. Now it builds the modded copy with no mods and
the gold title, and starts the game from it, the way a mod set does: the first time it builds, then it starts at once
unless you played a mod set in between. RUSE Guard runs in its multiplayer matches, as in every set's. Untick the gold
title in Settings (the Launcher's or the Studio's: it's one setting) and Vanilla starts through Steam as before. Your
Steam install is never changed.

**Fixed in 0.9.8.14, right before it:** a few mods bring a match script of their own whose header asks for more room
than the script needs (1 VS 7 AI, 1 VS 15 AI, Operation Overlord and Sand Box among them). The game runs those scripts
fine, but Play and Test in game refused them with "RUSE Guard's scripts can't be added: .xyz says ... bytes but holds
...", so no modded game with one of those mods could be built. The apps now read them the way the game does.

**Also new, in 0.9.8.13 before that:** if you ticked Bug Watch and the game crashes, its report now also says what the game was
trying to read or write, and up to 16 places in the game that led to the crash. Both are read from the game's own
crash report on your PC, which still never leaves it. A player's crash this week told us only where the game stopped;
now we can trace crashes like it, and fix them. The agreement lists these two things now (version 3; nothing else in
it changed), so both apps show it to you once more.

**Fixed in 0.9.8.12, earlier:** 0.9.8.10 / 0.4.8.10 and 0.9.8.11 / 0.4.8.11 couldn't build a modded game:
Play and Test in game stopped with "No such file or directory: ...fairplay_watch.bin", because their installers left
out three of RUSE Guard's files. Update, and both work.

This update makes big mods work, and brings fair play and trust:

- **Mods past 4 GB** (reported by a player): a modded game whose packs passed 4 GB stopped building. Packs now carry
  their full length, and one past 4 GB uses a small game patch, downloaded once and applied only to your modded copy,
  never to the game in your Steam folder. Tested in the game with all 366 era units.
- **Build lists in groups:** with many units, a building's build list ran off the screen. Each list now shows one row
  per group (the game's own lines), at most 6 units a group and 10 groups a building, so every unit can be reached.
- **Faster builds:** a mod with 366 era units took about 18 minutes to build on an 8-core PC; now about 5 the first
  time and about 3 after.
- **From testers' reports:** imported turret parts and towed guns; one Bridges tab, where the map's own bridges go out
  with their crossings; a unit mod and map changes of one name build together.
- **Your files in Documents\RUSE 2.0:** the Studio keeps your mods, maps, exports and backups where File Explorer
  shows them, and Delete a mod sends one to the Recycle Bin.
- **0.9.8.11, right after 0.9.8.10:** Sign in through Steam finishes in the apps (after Steam's page, the window
  waited and never checked); and on Linux a build's helper programs start fresh, the way they always have on Windows.

The first time an app opens it shows a short agreement and asks you for a username (a # and four numbers are added so
it's unique, like Nick#4821; one name works for both apps). Then:

- **RUSE Guard, our anti-cheat** (from DomesticNukes' design): it works only in real multiplayer and co-op matches,
  never in single-player, skirmish against the computer, the campaign, or while you make mods. A modded copy built
  with a cheat or a test tool is for offline play only and leaves multiplayer matches by itself. During a real match
  it checks the names of your running programs against a list of known cheat tools (names only; nothing else is
  read), and what it collects is filed under your username, never your Steam account. The Launcher gives your modded
  game a **join code**: the same code means the same game, so a match can't drift apart.
- **Bug Watch (optional):** tick it and the apps count what you use and when something goes wrong (their crashes and
  the game's, with which mods were on) and send it once a day to our developers with your username. No real names,
  no Steam account, no files. Off unless you tick it; untick it any time and what was kept is deleted.
- **Sign in through Steam:** a sign-in on Steam's own page in your browser confirms you own R.U.S.E.; we never see
  your password, and your Steam ID is never stored, only a pass kept on your PC for 30 days. In the Launcher's
  Settings. Nothing needs it yet.
- **Owned copies only:** the apps start a modded game only from a copy of R.U.S.E. you own. If yours can't be
  confirmed (a boxed copy from before R.U.S.E. was on Steam, say), a box gives you a code for a ticket on Discord or
  GitHub, and we send you an unlock code.
- **Every language:** the apps, their README and the wiki now speak Persian too, eleven languages in all. An update
  can now be marked required, for the rare fix that matters to everyone; the apps install it by themselves.

The full notes are with each release. R.U.S.E. belongs to Eugen Systems and Ubisoft; R.U.S.E. 2.0 is a free
community project, not made, approved or supported by them, and it needs your own copy of the game.
