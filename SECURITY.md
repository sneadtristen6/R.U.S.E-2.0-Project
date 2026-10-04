# Security

RUSE 2.0 is the RUSE Studio and the RUSE Launcher, made by volunteers for R.U.S.E. (2010). This page says how to report
a security problem, what the apps do to keep you safe today, and the fair play rules we're building (RUSE Guard),
which aren't switched on yet.

## Supported versions

Only the newest release of each app gets security fixes. Each app offers its updates when it starts, so staying up to
date is one click. Both apps are in alpha.

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
- this repository and its release workflow: a leaked key or token, or a way to change a release.

For example: a mod file that runs code on your PC outside the game when the Launcher or the Studio opens it; an update
or a mod that installs although it doesn't match what was published; one of the apps sending your data anywhere.

**Not ours to fix:** R.U.S.E. itself, its multiplayer service and Steam; please report those to their makers.
Someone cheating in a match isn't a security problem in our apps: tell us on the
[Discord](https://discord.gg/DbufY4Jfg). RUSE Guard, below, is how we mean to handle cheating.

## How the apps keep you safe today

- **Your game is never changed.** Mods are built into a separate modded copy of the game; your Steam install is only
  read.
- **Data, not programs.** The apps change the game's data files. They never change the game's program files and never
  inject anything into the running game.
- **Updates are checked.** An update comes only from this repository's GitHub Releases, over HTTPS. Before it runs, its
  SHA-256 must match what GitHub reports for the file and what our release notes publish (at least one of the two must
  be there, and they must agree). A file that doesn't match is deleted. The apps install for your Windows user and
  need no admin rights.
- **Mods from the list are checked.** A mod downloaded from the Supported mods list is installed only if its size and
  SHA-256 match the list's entry. Anything else is deleted and refused, so a changed or cut-off file never installs.
- **What the apps connect to:** GitHub (updates, the mods list and mod downloads), and, for the Studio's 3D view, the
  three.js library from jsDelivr (`cdn.jsdelivr.net`). They never ask for your Steam password or sign in to Steam.
  **Report a problem** only opens a filled-in page in your browser, with your Windows user name taken out of any
  paths; nothing is sent until you post it yourself.
- **This repository** has GitHub's secret scanning and push protection switched on, and a check on every push and pull
  request keeps game files and private material out of it.
- **Mods that change the game's scripts:** scripts run inside the game and can do anything it can. Install those only
  from authors you trust. (RUSE Guard will mark them and ask you first.)

## Fair play: RUSE Guard (planned, not switched on)

R.U.S.E. multiplayer has no anti-cheat of its own. RUSE Guard is DomesticNukes' design, and his name for it: a way to
keep cheats out of matches against other players without ever catching honest ones. **None of it is switched on in
any release yet.** It turns on only after it has been tested in the game. These are the rules it's built to, and
they're our policy from today:

1. **Multiplayer only.** It never runs in single-player: skirmish against the AI, Operations and the campaign stay
   yours, cheats and all.
2. **No automatic bans.** A flag is evidence for a person to review, with the match's replay, never a punishment by
   itself. A player can appeal, and a dismissed flag carries no penalty.
3. **Cheats and test tools stay offline.** A mod set with a cheat or a test tool builds an offline copy of the game:
   it plays against the AI as before and leaves multiplayer and co-op matches.
4. **You choose before scripts run.** Mods that change the game's scripts are marked, and Play waits until you tick
   "I trust this author" for each one.
5. **Same code, same game.** Each modded copy gets a join code to compare with the people you play with before a
   match, so a difference is found before it can look like cheating.
6. **Only what a match needs, and only with your agreement.** Nothing is collected until you've agreed to RUSE Guard's
   terms. After a multiplayer match, its evidence is: the match's replay, a record of the match's state every 10
   seconds of game time and the script hotkeys used, and which mods and versions the copy has, with its files'
   fingerprints. A check for known memory-editing tools running beside the game happens only during a live
   multiplayer match, and only if you allow it; saying no still lets you play. Nothing is collected from single-player.
7. **Signed keys.** Developers who need test tools in a match use a signed dev key, and approved mods can carry a
   signed manifest. The keys that sign them never go in any repository.

Before anything is collected, RUSE Guard's terms of service will say exactly what is kept, for how long, who sees it
and how to appeal.
