# Security

RUSE 2.0 is the RUSE Studio and the RUSE Launcher, made by volunteers for R.U.S.E. (2010). This page says how to report
a security problem, what the apps do to keep you safe, and how RUSE Guard, our anti-cheat, works: it's on in every
modded copy since Launcher 0.4.8.10 and Studio 0.9.8.10.

## Supported versions

Only the newest release of each app gets security fixes. Each app offers its updates when it starts, so staying up to
date is one click, and an update that matters to everyone can be marked required: the apps then install it by
themselves. Both apps are in alpha.

## Report a security problem

**Report it privately:** [Report a vulnerability](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/security/advisories/new)
(this repository's **Security** tab). Only the project's maintainers see it. Please don't post it in issues,
Discussions or on Discord until it's fixed.

Say what you found, which app and version, and the steps that show it. A small example mod or file helps a lot.

We're a small volunteer team. We'll answer as soon as we can, tell you what we'll do about it, and credit you in the
release notes when the fix ships, unless you'd rather not be named.

**What counts:**

- the Launcher, the Studio and the `rusemod` tools;
- the installers and the apps' updater;
- the Supported mods list ([Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)) and how the Launcher downloads
  and installs mods;
- our online services: the RUSE Guard server, the Bug Watch server and the Steam sign-in server;
- a way past RUSE Guard's offline lock or the check that the game is a copy you own;
- this repository and its release workflow: a leaked key or token, or a way to change a release.

For example: a mod file that runs code on your PC outside the game when the Launcher or the Studio opens it; an update
or a mod that installs although it doesn't match what was published; a modded copy with a cheat in it that gets into
a multiplayer match; one of the apps sending your data anywhere the agreement doesn't say.

**Not ours to fix:** R.U.S.E. itself, its multiplayer service and Steam; please report those to their makers.
Someone cheating in a match isn't a security problem in our apps: tell us on the
[Discord](https://discord.gg/h54t5baNsC), and RUSE Guard's review team looks at it.

## How the apps keep you safe

- **Your game is never changed.** Mods are built into a separate modded copy of the game; your Steam install is only
  read.
- **Data, not programs.** The apps change the game's data files in the modded copy, and never inject anything into the
  running game. Where a mod needs more than the data allows (more buildings, mod sets past 4 GB), a small game patch
  from our [game-patches release](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/game-patches) is
  applied to the modded copy's program only: the apps refuse a patch file that isn't exactly the one they know
  (its SHA-256), and check the patched program against the one the patch promises.
- **Updates are checked.** An update comes only from this repository's GitHub Releases, over HTTPS. Before it runs, its
  SHA-256 must match what GitHub reports for the file and what our release notes publish (at least one of the two must
  be there, and they must agree). A file that doesn't match is deleted. The apps install for your Windows user and
  need no admin rights.
- **Mods from the list are checked.** A mod downloaded from the Supported mods list is installed only if its size and
  SHA-256 match the list's entry. Anything else is deleted and refused, so a changed or cut-off file never installs.
- **What the apps connect to:** GitHub (updates, the mods list, mod downloads, the game patches and the era units'
  models), the three.js library from jsDelivr (`cdn.jsdelivr.net`) for the Studio's 3D view, and our own servers:
  RUSE Guard's (match records and a cheat copy's stop line, under your username), Bug Watch's (only if you tick it)
  and the Steam sign-in server (only when you sign in). They never ask for your Steam password: Sign in through Steam
  happens on Steam's own page in your browser. **Report a problem** only opens a filled-in page in your browser, with
  your Windows user name taken out of any paths; nothing is sent until you post it yourself.
- **This repository** has GitHub's secret scanning and push protection switched on, and a check on every push and pull
  request keeps game files and private material out of it.
- **Mods that change the game's scripts:** scripts run inside the game and can do anything it can. They're marked, and
  Play waits until you tick "I trust this author" for each one. Install them only from authors you trust.

## Fair play: RUSE Guard (on since Launcher 0.4.8.10 and Studio 0.9.8.10)

R.U.S.E. multiplayer has no anti-cheat of its own. RUSE Guard was DomesticNukes' idea, and the name is his;
sneadtristen6 and Claude built it. It keeps cheats out of matches against other players without catching honest ones.
Accepting it is part of the agreement the apps show at their first start (version 4, 13 November 2026), and these are
its rules:

1. **Multiplayer only.** It acts only in multiplayer and co-op matches: never in single-player, skirmish against the
   computer, the campaign or replays, and the Studio never runs it while you make mods.
2. **Cheats and test tools stay offline.** A modded copy built with a cheat or a test tool is for offline play only.
   Taken into a multiplayer or co-op match, it surrenders a few seconds in, then stops the game at the end-of-match
   screen. The Launcher sends us only RUSE Guard's line saying a cheat copy was stopped, with any Steam ID, long number
   or path removed, under your username. Honest copies are never stopped.
3. **You choose before scripts run.** Mods that change the game's scripts are marked, and Play waits until you tick
   "I trust this author" for each one.
4. **Same code, same game.** Each modded copy gets a join code that stands for its game version, its mods and their
   versions. You compare codes with the people you play with; the code is never sent to us.
5. **The program check.** While a multiplayer or co-op match is live, RUSE Guard checks the names of your running
   programs against a list of known cheat tools, and reports only a name on that list. It reads nothing else.
6. **Only what a match needs.** When the game provides it, RUSE Guard may collect a check of the game files that
   change how it plays, regular checks that everyone's game stays the same, a replay you saved, the match's details and
   the list of mods. Today the game provides no match record, so for an ordinary match nothing is sent. It never
   collects your files, your screen, your keystrokes or anything outside a multiplayer or co-op match, and never reads
   your computer's memory.
7. **No automatic bans.** If something looks wrong, our review team (DomesticNukes and sneadtristen6) looks at the
   evidence, and at the replay when there is one, and decides. You can appeal to sneadtristen6 on our Discord or
   GitHub. Confirmed cheating can remove your access to multiplayer through R.U.S.E. 2.0; it never affects your Steam
   account or the game itself.
8. **Kept 48 hours.** A match record is deleted 48 hours after the last player's record of that match reached our
   review server, unless a review of it is open. Confirmed evidence is kept while the player can appeal; after that,
   only the decision itself.
9. **Signed dev keys.** Developers who need test tools in a match use a signed dev key, the one way past the offline
   lock. The keys that sign them never go in any repository.

## Bug Watch and Sign in through Steam

- **Bug Watch** is off unless you tick it. When it's on, the apps send counts of what you use and what goes wrong,
  once a day, with your username: never your real name, your Steam account, your files or paths, or the names and
  words of your own mods. Settings shows, word for word, what would be sent. Counts and crash reports are deleted
  after 7 days; untick it any time and what was kept is deleted.
- **Sign in through Steam** happens on Steam's own page; we never see your password. Our server keeps a one-way code
  made from your Steam account, never your Steam ID or IP address, and your PC keeps a pass for 30 days. Nothing needs
  it yet.

The agreement the apps show at their first start has the full text of each; this page says the same in short.
