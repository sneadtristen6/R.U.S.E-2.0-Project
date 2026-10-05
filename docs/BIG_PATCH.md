# The big patch before 1.0 (DRAFT, not released)

What goes into the one big patch we make before 1.0 (not the 1.0 release itself), collected here as each part is
written: what it does and how. Nothing here is released yet; each part says where it stands.

## RUSE Guard: our tools are never how anyone cheats online

RUSE Guard, and the push to make the platform secure, were DomesticNukes' idea, and the name is his. It has two
halves that fit together: the Launcher and in-game half written here, and his match-review half (the detectors, the
replays, the reviews, dev keys and the terms of service) in his own repository. What each half covers, and what of
his goes into this patch, is at the end of this section.

**Where it stands:** our half is written and tested offline, and kept in our private repository, **switched off**,
until it's tested in the game: the released Launcher and build do none of what follows yet. After that, the
in-game part (the offline lock and the watcher) still waits for tests F1 and F3 before it goes into
builds. His half is built and tested offline (59 tests, verified on real replays) and isn't wired into the Launcher
yet.

**How it works,** as the patch notes would say it:

R.U.S.E. multiplayer has no anti-cheat of its own, so we built RUSE Guard into the Launcher. It keeps the cheats people
use for testing out of matches against other players, lets players who don't cheat show it, and makes you choose
before a mod runs scripts inside your game.

**Cheats and test tools are offline only.** A mod set with a cheat or a test tool in it (the "Cheat" mods in Supported
mods, and any mod whose scripts add money, make units out of nowhere or open the game's developer menu) builds an
offline copy of the game. Skirmish against the AI, operations and the campaign work as before. A multiplayer or co-op
match started in that copy says so on screen and is given up a few seconds in, so the cheat never plays against
anyone. *(Not tested in a real match yet: test F1.)*

**Join codes.** The new **Join code** button (bottom bar) shows your modded game's code, starting `RUSE1:`. Send it to
the people you play with: the same code means the same game (the same game version, the same mods, the same versions).
Paste a friend's code and press **Compare**: "Same game", or exactly what differs (a mod one of you is missing, a
different version, a different game build). Two different games in one match drift apart, and that can look like
cheating when it isn't; now you can check before you play. An offline copy has no code.

**A copy changed by hand loses its code.** The Launcher remembers every file it built into the modded copy. If a file
is swapped or edited afterwards, or a pack the game didn't have is added, the Join code box says what changed and
shows no code until the copy is built again. **Check every file of the copy** compares every byte (a few seconds).

**"Runs scripts" and "I trust this author".** Some mods change the game's scripts, and scripts run inside the game and
can do anything it can. The library now marks those mods **Runs scripts**, and Play waits until you tick **I trust
this author** for each one. The tick is for that version: an update asks again. Cheats show a **Cheat** badge.

**The RUSE Guard watcher, in every modded game.** Skirmish, multiplayer and co-op matches say on screen when something
happens that only a cheat does: a unit made out of nowhere, or a player's money jumping far more at once than a match ever gives.
Orders in a match run on every player's PC, so a cheat sent by one player shows on the others' screens too. It
changes nothing in the match, and there's no switch to turn it off. It rides in the maps' own small script pack
(about 2 MB written per Play), so Play stays as fast as before. *(Not tested in the game yet: test F3, which also
checks that normal play never sets it off.)*

**What this can't do,** said plainly: our half runs on your own PC. It stops our Launcher and Studio from being how
anyone cheats online, and gives honest players a way to show their game is the same as yours. It can't stop someone
who edits their game by hand with other tools; that's what DomesticNukes' half is for (below). Nobody gets banned by
any of this: a flag is evidence for a human review, never a punishment.

### Our half and DomesticNukes' half (his design: RUSE-Guard `docs/DESIGN.md`)

His design names five kinds of cheat: C1 changed game data, C2 script mods (free money, playing the enemy's ruse
cards), C3 memory tools and trainers, C4 seeing what you shouldn't (fog, enemy money), C5 a "mod" that harms other
players' PCs. Detector by detector, against what we wrote:

| His part | What it does | Ours | In this patch |
|---|---|---|---|
| 3.1 Sync Code at the lobby | every player's mod fingerprint compared before the match | **Join codes** do this between players by hand; his compares them automatically at the lobby and on a server | his lobby hook + server compare, built on our join codes |
| 3.2 State divergence | a script hashes the match state; players whose games disagree are found | **not in ours** (the game itself never checks this) | his world-hash script, added to the maps' script folders the way our watcher goes in |
| 3.3 Network-order anomaly | free money and production-rate cheats found in the match replay, after the match | **partly**: the watcher flags free money and spawned units live, on screen; no production rate, no replay | his replay scan for the verdict; our watcher as the live hint |
| 3.4 Script integrity | the game's scripts checked against a known-good list | **partly**: our copy check finds any pack changed since the build, but only shows it on the player's screen | his list, reported with the match |
| 3.5 Process / overlay scan | memory tools and overlays running beside the game | **not in ours** | his, disclosed in the terms of service; a hint for review, never a ban by itself |
| 3.6 Behavioural review | a human watches the replay for impossible play | **not in ours** | his review tooling |
| 3.7 Signed mod manifests | catches a whole lobby running the same changed mod, which matching codes can't | **not in ours**: if everyone's mod is changed the same way, everyone's join code still matches | his mod keys; signing keys held by the owner, the public halves shipped in the Launcher |
| 4 Flag, review, verdict | a flag opens a human review with the replay; the player can appeal; no auto-ban | **not in ours** (ours only tells on screen) | his server core; the upload, storage and the reviewers' screen are still to build |
| 5 Replay reading | every order of a match read from its replay file (all 17 kinds) | **not in ours** | his replay reader, the evidence for every review |
| 6 Dev keys | signed keys let a developer use test tools in multiplayer, for testing | **not in ours**: our offline lock keeps test tools out of every online match, developers' too | his dev keys as the one way past our offline lock |
| 7 Mod vetting | a capability scan before a mod is listed; approved sets' codes allow-listed | **partly**: our scan finds scripts that send cheat orders, the "Runs scripts" badge and trust tick, the cheat tag from the mod list | his capability scan for the Supported mods list, and approved sets' codes |
| 8 Terms of service | what is scanned, what a flag means, appeals | **not in ours** | his draft |

What ours adds to his: the offline lock in the game itself (a cheat set can't play online at all, before any server
sees it), the trust tick before a script mod runs, the Launcher's cheat badges, the copy check, and the live watcher.

**One rule of his to apply before turning ours on:** RUSE Guard runs in multiplayer only; it never runs in
single-player. Our watcher also watches skirmish against the AI (that's how test F3 checks it offline); it switches to
multiplayer only once F3 has passed.

### The whole system, built (2026-10-04; switched off, nothing tested in the game)

The owner's choices: the Launcher side in the platform, the server side added to DomesticNukes' repository as new
files, the server on his PC, the process scan as he designed it.

- **In the platform** (in our private repository until it's tested in the game): his signed tokens
  checked with Ed25519 written in plain Python (checked against the standard's test vectors), so the Launcher needs no
  extra package; a **dev key** is the one way past the offline lock; **signed mod manifests** are checked file by file
  before Play; the **in-game record** (his §3.2 state hash every 10 s of game time and §3.4 script hotkeys, multiplayer
  and co-op only) goes in every map's script folder like the watcher; after a multiplayer match the Launcher collects
  the record, the replay and the rest into one **bundle**, signed with the install's own key, and sends it to the
  server or keeps it until one is set; the **process scan** runs only while a multiplayer match is live and only if the
  player allowed it; the Launcher keeps the player's agreement to the terms, the scan's choice and the server's address.
  The owner's public keys go in with it (none made yet).
- **A map mod's worked-out answers** (`maps/<map>/solved.bin`, MOD_FORMAT §8) are part of this picture: the file is
  one of the mod's files, so a signed mod manifest lists it with its hash and a changed one fails the manifest like
  any other file. It is locked with a key made from the game's own file for the map, a build weighs every answer it
  takes, and answers that pass and still differ give other game files, so another fingerprint and another join code
  than everyone else's.
- **For his repository** (pull request #2 on RUSE-Guard, opened 2026-10-04, new files only, his files unchanged): the **server**
  (takes the Launchers' bundles, groups a match's players, runs his detectors, opens reviews only from detectors set to
  flag), the **reviewers' screen**, a **keys tool** (the real key pairs, dev keys, signed mods), the process scan's
  list, the in-game record's source, and how to run it all on his PC.
- **Checked together, without the game:** a dev key and a signed mod made with his tool pass the Launcher's checks;
  three Launchers' bundles reach the server as one match, and only the player whose game drifted gets a review.
- **Still open:** the keys (made once by whoever holds them); the in-game test (can the game write the record's file;
  do two honest players' records match: test F4); honest multiplayer replays to tune his detectors; HTTPS in front of
  the server; the Launcher's screens for the terms, the scan and the server address (none while it's switched off).

## Music, sounds and campaign scenes

**Where it stands:** research and theory only (2026-10-04); nothing built, nothing tried in the game. The owner's
idea: new music for R.U.S.E. 2.0 and its Iwo Jima Operation for variety, different sounds for
units and buildings, and new campaign scenes. What follows is what the game's data says, and our best theory for each
open question, to be proved by one test copy.

**How it would work,** as the patch notes would say it:

**New music.** Mods can bring their own songs. Give the Studio a WAV file and it becomes a game track with a name of
its own: in battles it joins the calm, battle or ruse music (the game switches between those three as the fight goes);
in an Operation the mission plays it at the moment you choose, such as the landing or the victory. Only music you have
the rights to. *(Theory, not tested.)*

**Unit sounds.** A unit can have its own engine sound (running and idling; planes also diving) instead of the one its
kind shares, so a Tiger can roar like no Sherman. Shots, explosions and voices follow the same pattern: each is a
named sound that a mod can replace or point somewhere new. *(Theory, not tested.)*

**Building sounds.** Buildings react to what happens to them with effects: being built, damaged, destroyed, producing
(the smoke and the turning light) and captured. Building already has a sound, so the others can have sounds too: a
factory that hums while it makes a tank. A building given its own copy of those effects sounds different from the
rest. *(Theory, not tested.)*

**Map sound.** Each map has its own background sound. Iwo Jima can borrow what the game already has: the swamp
ambience and the volcano. *(Not tested.)*

**Campaign scenes.** Three kinds, all made by a mission: a camera flight with black bars, dialogue and music, made in
the game itself (missions of ours already play); a full-screen film; and a small film during the mission, a wide strip
or a tall panel. Films are made in Blender, which writes the game's exact video format. *(Films: theory, not tested.)*

**The theories, and why we think so** (the one test copy checks all of them):

1. **A new track needs a small description beside its sound.** A track without one stays silent rather than
   crashing, so the Studio writes both. Expected: the new track plays in full.
2. **A replaced song may need its description updated too.** The community song that replaced the menu music kept the old
   description and **works in the game** (owner, 2026-10-04). Still open: does it play to its end (4:08) or stop at
   the old track's length (about 2:55)? If it plays to the end, replaced songs need no description update. The
   Studio updates it anyway.
3. **A film from Blender plays.** Blender's video output matches what the game plays. Expected: plays, as long as
   the film keeps the game's own sizes and frame rate (the Studio will check them).
4. **A building's effects can carry a sound.** Construction does it already, through the same effects table that
   holds production, damage and capture. Expected: a sound added to the production effect plays while a factory
   works, and only for buildings given their own copy of the table.
5. **Sound effects carry a loudness track** (five levels for every 2048 samples) that music doesn't have. What the
   game uses it for isn't known; the Studio would measure it from the sound itself. Expected: no audible difference
   if it's only approximate.

**The test copy (when it's built):** a 30-second song added to the battle music and played by a mission; the menu
music replaced by a longer song with its description updated; a 5-second Blender film shown during the mission (strip
shape); a factory with a sound on its production effect. One game start answers all five.
