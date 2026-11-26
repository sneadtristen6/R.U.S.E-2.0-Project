# Security

RUSE 2.0 is the RUSE Studio and the RUSE Launcher, made by volunteers for R.U.S.E. (2010). This page says how to report
a security problem, what the apps do to keep you safe, and how RUSE Guard, our anti-cheat, works: it's on in every
modded copy since Launcher 0.4.8.10 and Studio 0.9.8.10.

## Supported versions

Only the newest release of each app gets security fixes. Each app offers its updates when it starts, once its terms are
accepted, so staying up to date is one click, and an update that matters to everyone can be marked required: the apps
then install it by themselves, but only an update that carries our signature. Both apps are in alpha.

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
- a way past RUSE Guard's lock on cheat and test copies, or past the check that the game is a copy you own;
- this repository and its release workflow: a leaked key or token, or a way to change a release.

For example: a mod file that runs code on your PC outside the game when the Launcher or the Studio opens it; an update
or a mod that installs although it doesn't match what was published; a modded copy with a cheat in it that gets into a
multiplayer match; one of the apps sending your data anywhere the terms and privacy notice doesn't say; an update that
installs without our signature.

**Not ours to fix:** R.U.S.E. itself, its multiplayer service and Steam; please report those to their makers.
Someone cheating in a match isn't a security problem in our apps: tell us on the
[Discord](https://discord.gg/h54t5baNsC), and RUSE Guard's review team looks at it.

## How the apps keep you safe

- **Our apps never change your installed game.** Mods are built into a separate modded copy of the game. The one
  exception: if you ask the Launcher or the Studio to restore your game from its clean backup, it puts the game's own
  files back, and moves aside the files that were added and the versions it replaces.
- **What the apps change, and where.** In some instances, game data may be changed, but that is with your copy of the
  game: the separate modded copy. The apps change that copy's data files; mods that change the game's scripts change
  that copy's scripts; and the apps add RUSE Guard's scripts, and a few small guards of their own, to the game's scripts
  in every modded copy. The apps never put anything into the running game. Where a mod set needs more than the data
  allows (more buildings, squads with soldiers of their own, mod sets past 4 GB), a small game patch from our
  [game-patches release](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/game-patches) is applied to
  the modded copy's program file only: the apps refuse a patch file that isn't exactly the one they know (its SHA-256),
  and check the patched program file against the one the patch promises.
- **Updates are signed.** An update comes only from this repository's GitHub Releases, over HTTPS. GitHub builds each
  release as a draft; before it is published, the maintainer checks on his own PC that GitHub's release workflow built
  its files from the tagged commit (GitHub's build attestation), then signs them with the project's release key. That
  key is never uploaded and is protected by a passphrase; its public halves are in `src/rusemod/release_keys.toml`. The
  apps install an update (by the Update button or by themselves) only when its signature fits the app and the version
  and the downloaded file is exactly the signed one; whether an update is required, and what it changes, are read only
  from what was signed. Otherwise nothing installs, the app says so, and points to our Discord. A file that doesn't
  match is deleted. This doesn't cover apps older than the first version with this check, a first download from your
  browser, or something slipped into the release build's own inputs on GitHub before it was signed. The apps install for
  your Windows user and need no admin rights. If an update's download fails three times, the app stops trying by itself
  and points to that release's page on GitHub; a required update still keeps Play waiting.
- **Mods from the list are checked.** A mod downloaded from the Supported mods list is installed only if its size and
  SHA-256 match the list's entry. Anything else is deleted and refused, so a changed or cut-off file never installs.
- **What the apps connect to:** GitHub (updates and their notes, the mod list and the mod downloads, the game patches,
  the era units' models and some motion files), any other site the mod list names for a mod, Poly Haven, ambientCG and
  the USGS for Map Paint, Zenodo for motions, and our own servers: RUSE Guard's (a short record, under your username,
  when a listed cheat tool ran during a multiplayer or co-op match, and a cheat copy's stop note), Bug Watch's (only
  while Bug Watch is on; it also hands the apps our list of known game crashes) and the Steam sign-in server (only when
  you sign in). Section 12 of the terms and privacy notice lists them all. They never ask for your Steam password: Sign
  in through Steam happens on Steam's own page in your browser. **Report a problem** opens a filled-in page in your
  browser, with your Windows user name taken out of any paths; your browser sends those details to GitHub in the page's
  address when the page opens, and nothing is posted until you post it yourself. The Studio's 3D views draw with
  three.js, which ships inside the Studio: nothing is fetched for them.
- **This repository** has GitHub's secret scanning and push protection switched on, and a check on every push and pull
  request keeps game files and private material out of it.
- **Mods that change the game's scripts:** scripts run inside the game and can do anything it can. They're marked, and
  Play waits until you tick "I trust this author" for each one. Install them only from authors you trust.

## Fair play: RUSE Guard (on since Launcher 0.4.8.10 and Studio 0.9.8.10)

R.U.S.E. doesn't have an effective anti-cheat, which is why RUSE Guard is needed; RUSE Guard is ours, and it works only
in copies our apps build. RUSE Guard was DomesticNukes' idea, and the name is his; sneadtristen6 and Claude built it. It
keeps cheats out of matches with players who don't have the same build, without catching honest ones. Accepting it is
part of the terms and privacy notice the apps show at their first start (version 5, 26 November 2026), and these are its
rules:

1. **Where it acts.** Its lock and its program check act only in multiplayer and co-op matches. Its watcher, in every
   modded copy, also watches skirmish matches against the computer: it shows a notice on screen when a side's money
   jumps by 400 or more at once, or a unit is made by a spawn order, and it changes and sends nothing. The Studio never
   sends anything for RUSE Guard. Its list of known cheat tools comes inside the app, where you can read it. The
   Launcher's Vanilla builds a copy with no mods and RUSE Guard in it, like every copy.
2. **Cheats and test tools play only with the same build.** A modded copy built with a cheat or a test tool plays
   multiplayer and co-op only with players whose build is the same, and tells every player's game a short code for its
   build. In any other match it gives up a few seconds in. If that was a multiplayer match that isn't ranked, it then
   stops the game on purpose at the end-of-match screen: the game crashes, and the game's own crash reporter can send
   its report, with RUSE Guard's line saying a cheat copy was stopped, to the game's maker. The Launcher that started
   the game sends us only that line, as a short note under your username. In co-op and ranked matches it only gives up
   the match. Honest copies are never stopped.
3. **You choose before scripts run.** Mods that change the game's scripts are marked, and Play waits until you tick
   "I trust this author" for each one.
4. **Same code, same game.** Each modded copy whose mods change how the game plays gets a join code that stands for its
   game version, its mods with their versions, and what they change in how the game plays. You compare codes with the
   people you play with; we don't receive them today.
5. **The program check.** During a multiplayer or co-op match started from the Launcher, RUSE Guard looks every 30
   seconds at the names of your running programs against its list of known cheat tools, and reports only a name on that
   list, with when the match started and ended. To know a match is on, the Launcher reads the game's error output while
   the game runs and keeps only RUSE Guard's own lines; every other line, Steam's included, is dropped as it is read,
   never kept or sent.
6. **Only what a match needs (match records: not active yet).** When the game can record a match (it can't yet), a match
   record would carry your username and RUSE Guard key, your side, your copy's codes, checks of the game files your copy
   changed and regular checks that everyone's game stays the same, your mods with their checks, which script commands
   your mods tie to keys, any listed cheat tools found running, the match's times, and the newest replay you saved (it
   holds every player's orders and can carry players' in-game names). Today no match record is made, so for an ordinary
   match nothing is sent. RUSE Guard never collects your screen or your keystrokes, and never looks inside other
   programs while they run.
7. **No automatic bans.** If something looks wrong, sneadtristen6 looks at the evidence, and at the replay when there is
   one, and decides; Anthropic's Claude helps him read the records. Appeals, within 30 days of a decision: a private
   message to sneadtristen6 on Discord, or a ticket on our GitHub (tickets are public, so please keep evidence out of
   them); he decides appeals himself too. Confirmed cheating puts your username on our list of flagged players; the apps
   don't act on it yet. RUSE Guard never touches your Steam account; how Steam treats a modded copy online is Valve's
   call, so playing online with one is at your own risk.
8. **How long:** see section 11 of the terms and privacy notice ([PRIVACY.md](PRIVACY.md)).
9. **Signed dev keys (not in use yet).** The apps are built to let a developer's test copy into a match with a signed
   dev key, the one way past the lock. The apps don't carry the key that checks them yet. The keys that would sign them
   never go in any repository.

## Bug Watch and Sign in through Steam

- **Bug Watch** is off unless you tick it, and saving your username never turns it on. When it's on, the apps send crash
  details right away and counts of what you use and what goes wrong once a day, with your username and install ID, never
  your files. Settings shows today's counts word for word, and the names of the reports waiting to go. Each report is
  deleted 7 to 8 days after it reaches our server, unless we mark a very severe crash's report to keep until we've fixed
  that crash. Untick it any time: nothing more is sent, and its counts and waiting reports on your PC are deleted. To
  have reports deleted sooner, email us your report code (Settings shows it only while Bug Watch is on) or your
  username.
- **Sign in through Steam** happens on Steam's own page; we never see your password. Our server keeps a one-way code
  made from your Steam ID, never the ID itself or your IP address. Your PC keeps a pass. It's valid for 30 days and
  stays on your PC until you sign out. Nothing needs it yet.

The terms and privacy notice the apps show at their first start, also at [PRIVACY.md](PRIVACY.md), has the full text of
each; this page says the same in short.
