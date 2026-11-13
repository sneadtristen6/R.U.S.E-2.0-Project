---
title: "Studio 0.9.8.20 and Launcher 0.4.8.20: guards where some mod sets stopped the game; an upgrade made in another building keeps its unit; a squad's own soldier, changed in Blender; Bug Watch says why; RUSE Guard lets players with the same build play together (not fully supported yet); imported models sit where the unit stands; a squad soldier by soldier, animations for one unit and the Horse Squad"
category: Announcements
order: 25
---
**RUSE Studio 0.9.8.20** and **RUSE Launcher 0.4.8.20** are out:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases). Both apps offer the update when they open.

![R.U.S.E. 2.0](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/ruse-2-0-brand.png)

**New in 0.9.8.20: guards where some mod sets stopped the game, and an upgrade made in another building keeps
its unit.** Players' crash reports, sent by Bug Watch, showed the game stopping as soon as the Armor Base was placed
with the R.U.S.E. Field Manual and the Balance Overhaul Mod together.

- **Guards where mods stopped the game:** every modded game now has a guard on three places where the game's own
  scripts stopped it: research cards in a building's list for a unit that is in another building, a mission starting
  the computer player of a side a person plays, and a mission changing units after one of them was killed. A guard
  does nothing unless the game would have stopped. Tested in the game with the Armor Base; the two mission guards were
  tested outside the game.
- **An upgrade made in another building keeps its unit:** with the same two mods, researching the T-34 in the Armor
  Base took the T-26 out of the Barracks, because the game takes a unit away as soon as any upgrade of it is
  researched, wherever that upgrade is made. The build now makes such an upgrade a research of its own and says so in
  a warning. Tested in the game with the USSR and Italy. It changes some sets with the Balance Overhaul Mod, and sets
  with the Field Manual before the Balanced Realism Mod; the warning names each unit.
- **Join codes:** a set the build changes this way gets a new join code, so every player in a match with it needs
  this version. Every other set keeps its join code. After the update, the next **Play** or **Test in game** builds
  your game again by itself.
- **The Launcher's mod set editor says why:** when it can't make or save a set (no mod ticked, or a mod that is no
  longer in your library), it now says so inside the editor, under its buttons. Before, the message went to the set's
  page, hidden behind the editor, so nothing seemed to happen. **Create** and **Save** wait until a mod is ticked.
- **Missions of your own (Studio):** a new map's mission that makes units of a nation its copied mission doesn't load
  now gets that nation's packs, so those units have their models (the game stopped when such a unit was made). The
  mission check also refuses an event that hands a side a person plays to the computer. Not yet tried in the game.
- **A squad's own soldier (Studio):** a modder asked on Discord how to change infantry models. A squad's page now gets
  **Its own model** with **Change it in Blender**: the squad's soldier opens in Blender on his own bones, and Blender
  gets a **Send to the R.U.S.E. Studio** button. **Bring back the model** takes him in on the game soldier's bones,
  with no **Custom uniform** needed. **Import model…** also works now on a unit with a **Custom uniform**: it takes the
  copy out, and **Use the copied unit's model** gives it back in one click. Points Blender leaves with no bone follow
  the root bone, and the page says how many. The wiki's Import a Model page has the steps. Tested in the game with two
  US squads made this way (one with a bigger head, one with a new mesh weighted in Blender); the rest was checked
  outside the game.
- **Bug Watch says why, if you ticked it:** which check refused a build or found a mistake (a fixed name from our
  code), how far a **Play** or **Test in game** got, which mods from our list were on and how many of your own
  (counted by kind, never named), Plays refused before they started, and updates offered, installed or failed. Never
  the words shown, a path, or anything your own mods hold. All of it is in the agreement you accepted (version 3), so
  it isn't shown to you again.

**Also new in 0.9.8.20, in the Studio: a squad soldier by soldier, animations for one unit, models with animations of
their own and the Horse Squad.**

- **A squad, soldier by soldier:** a squad's page now starts with its squad card and a line for each soldier, in place
  of its **Its own model** box. **Change the squad in Blender** opens all its soldiers side by side, each with his own
  copy of his pictures; after **Send to the R.U.S.E. Studio** in Blender, **Bring my changes back** gives each soldier
  only what was done to him. On his line a soldier has **Import a model…** and, once he has a model of his own, **Back
  to the game's look**. Seen from far away, the squad's little figures wear the look most of its soldiers wear. Tested
  in the game with a squad whose bazooka man alone was painted red.
- **More or fewer soldiers:** **Add a soldier** brings in a copy of one in the squad, a soldier from another squad, or
  a model file; **Remove** takes one out; **+1 soldier** and **−1 soldier** add or take away a rifleman at once,
  without Blender. A squad has 2 to 8 soldiers, and a soldier can have a look of his own that no other soldier wears.
  The game gets these through a small game patch, downloaded once and applied only to your modded copy, never to the
  game in your Steam folder; every other squad stays as the game has it. Tested in the game with squads of 3 and 7
  made with these buttons, and with one rifleman alone painted red; a soldier from another squad or a model file, and
  squads of 2 or 8, not yet.
- **Animations for one unit:** a unit's page now has **Look and moves**: its model, its soldiers, its sounds and
  animations and what it rides in, row by row. **Change in RUSE Decoy** on the **Sounds and animation** row opens
  RUSE Decoy on that unit, and a change to one of its animations can be for **Only this unit**, which then plays its
  own copy, or for every unit that plays it. **Back to what every unit plays** takes the unit's own copy out. **Motion
  capture** goes on one unit the same way. Tested in the game with a squad dancing on the spot while every other squad
  stood as before; a speed, a stand-in or a bone changed for one unit, not yet.
- **Animations changed in Blender:** for a new unit made in your mod, **Change its animations in Blender** in RUSE
  Decoy opens Blender with the unit and every animation it plays, each named for what it does in it. Change one, click
  **Send to the R.U.S.E. Studio**, then **Bring my changes back**: the changed ones become that unit's own, and every
  other unit keeps the game's. A sending you never brought back is set aside, and **Bring back the set-aside sending**
  takes it in. Tested in the game with a squad standing and running with an arm raised, and a Horse Squad whose horses
  hold their heads up.
- **Models with bones and animations of their own:** **Import model…** now also takes a .glb on bones of its own with
  its animations: a horse and rider, or any creature. **Its animations** shows which animation the unit plays for each
  thing it does; pick another, or leave it on **Nearest**. **On long moves** a squad can go as itself, playing one of
  them, instead of in its truck. **Its two halves** picks the bone where the model splits into the upper and lower
  halves the game animates at once (a rider aims while his horse runs), and **Will it work in the game?** says what in
  the model could stop the game or look wrong. In a squad, the riflemen and the heavy-weapon soldier each take a model
  of their own on their own line. Tested in the game with a Horse Squad made this way: riflemen and a bazooka man on
  horses, firing, riding as themselves on long moves, each horse falling with its rider; another animation picked by
  hand or another split, not yet.
- **The Horse Squad:** riflemen and a heavy-weapon soldier, each on a horse of his own, now listed in the **Units** tab
  with the units from other eras (**WWII+**, USA), off until you add it. **Add to my mod** makes its horses and riders
  on your PC from your own copy of the game (nothing is downloaded), adds it as a new unit of your mod and puts
  sneadtristen6 in your mod's credits; **Take it out of my mod** takes it all out again. It is made the same way as the
  Horse Squad tested above; added from the **Units** tab, not yet tried in the game.
- **Its own shine after Blender:** a model sent to Blender with **Change it in Blender** and brought back with **Bring
  back the model** keeps its own shine and side-colour layer; before, it came back with the plain one a model from a
  file gets. When one can't be kept, the page says which. Not yet tried in the game.
- **Where your model is kept:** the **Model** row (on a squad's page, **More options**) says where your mod keeps the
  unit's own model on your PC, with **Show in folder**.
- **The Nations tab:** **Start a new mod** now asks only for a name and opens the Studio on the new mod; the guided
  steps are off for now. What only they had is on the **Nations** tab: **Keep its units** or **Start it empty** for
  each nation, and **No research** or **Keep the game's research** for the whole mod.
- **A unit with no card picture (Studio and Launcher):** a unit shown in a build menu with no card picture is now
  refused when the game is built, with what to change. In a test the game stopped as it started with such a unit (a
  copy of the HQ truck shown in a build menu).
- **Export leaves your PC's folders out:** an exported mod no longer carries the folders of your PC that the Studio
  wrote into its model records (often with your Windows user name in them): only the file's own name goes. What you
  wrote yourself (README, descriptions, credits) goes out as you wrote it, and Export tells you if it names your home
  folder. The credits of units from other eras, the Horse Squad's too, now go with the mod.
- **Smaller things:** each factory is called by its building's name; in Persian, the game's names show in English,
  never as code names.
- **Players, update your Launcher:** a mod whose squads have soldiers of their own, or whose units have animations of
  their own, needs Launcher 0.4.8.20 or newer: an older one can't give them. This Launcher gets the small game patch
  such squads need by itself, downloaded once and applied only to your modded copy. Not yet tried in the game from the
  Launcher.

**In 0.9.8.19, right before it: RUSE Guard lets players with the same build play together, cheat mods or not. Not fully
supported yet.** A player told us that he and a friend, both with the same mod pack, were thrown out of every
multiplayer match, because one mod in it (Infinite Supply Depot) is tagged as a cheat. RUSE Guard treated every game
built with a cheat mod or a test tool as offline only: it left each multiplayer and co-op match a few seconds in, and
never looked at who else was playing.

- **What we changed:** one second into a multiplayer or co-op match, such a game now tells the other players' games
  which build it is: a short code made from the game version and the mods, nothing about you. About seven seconds in
  it decides. If every player has the same build (the same game version, the same mods in the same order, the same
  mod versions), it says so on screen and the match goes on. If anyone has another build or no mods, it leaves the
  match as before.
- **A join code for these sets:** in the Launcher, a mod set with a cheat mod now gets a join code like any other.
  The same code means the same build, so compare codes before you play.
- **Every player needs this version:** the game of each player in the match must be built by Launcher 0.4.8.19 or
  Studio 0.9.8.19, or newer. After the update, the next **Play** or **Test in game** builds it again by itself.
- **Not fully supported yet, and it may still be buggy:** we tested it in the game with one player hosting a
  multiplayer match alone against the computer, and outside the game with 20 simulated matches of up to four players.
  Nobody has played it with two people in a real match yet. Use it in multiplayer at your own discretion, try it, and
  tell us what happened on Discord or GitHub: which RUSE Guard message you saw, and whether the match went on.
- **Unchanged:** a game built without cheat mods, skirmish against the computer and the campaign.

**In 0.9.8.18: a fix behind the scenes.** The check of a modded copy (which game files changed
after it was built) now lists what it finds in the same order on Windows and Linux. What it finds doesn't change.

**New in 0.9.8.17: imported models sit where the unit stands.** A modder told us his models were drawn
ahead of their selection rings. The Studio's **Import model…** now puts a new model on the middle of the unit it copies
and gives it a skeleton of its own, so its turret turns where the turret is on your model. Every new import is fitted
this way. A model imported before keeps its old place until you import it again or move it, and the era units keep
theirs. Tested in the game with the game's own Sherman, opened in Blender and brought back, on other units; not yet
with a model from elsewhere, another turret tank, or a turret that turns all the way round.

- **Move it:** if a model still doesn't sit right, open **Move it** under its size on the unit's page (folded away
  until you need it). **Forward**, **Right** and **Up** move it from where it's fitted, in the game's units; a minus
  goes the other way, and 0, 0, 0 puts it back. Its turret and propellers go with it, so they still turn in the right
  place. In the 3D view a blue ring shows where the unit stands, its mark at the front. Tested in the game with tanks
  moved forward, back, right and up.
- **Planes keep their own propellers:** a plane opened in Blender from the Studio and brought back keeps its
  propellers where your model has them, as many as it has: blades on the ground, spinning discs in the air. Tested in
  the game with a three-engined bomber's model on a one-engined fighter, and the other way round. A plane model from
  anywhere else keeps its propellers as drawn, standing still, for now.
- **Any unit can take a model:** soldiers, a gun's crew and planes the Studio couldn't fit a model to before (the
  P-47, for one) take one of their own, rigged to the unit's own bones, such as one of the game's models opened in
  Blender from the Studio and changed there. Tested in the game with a rifle squad, a gun's crew and the P-47.
- **Players, update your Launcher:** a mod with a model imported by Studio 0.9.8.17 or newer needs Launcher 0.4.8.17
  or newer. An older Launcher gives the model the copied unit's skeleton, so its turret turns around the wrong point.
  Mods made before play as they did.

**Also new in 0.9.8.17: a weapon class of an ammo's own.** On an ammo's page, the **Weapon class** box sets how much
of its damage the ammo does to each kind of target, and **New weapon class…** opens one number for each: buildings and
fortifications, aircraft, paratroopers coming down, infantry, light vehicles, armour 1 to 5, and construction trucks.
1 is full damage, 2 double, 0.5 half, and 0 means it can't attack that target at all. Saving gives the ammo its own
copy of the game's damage table, so no other ammo's damage moves (every unit that fires that ammo gets it: copy the
ammo first for one unit only). **Back to the game's class** takes it out again. Tested in the game: rifle squads
whose round got numbers against tanks shot at tanks with their rifles and damaged them.

**Fixed in 0.9.8.16: Troubleshoot's "Clear them" deleted copies you made yourself.** A copy of the game you built by
hand in the copies folder, a test copy or a reference copy, counted as a leftover, and "Clear them" removed it for
good, not to the Recycle Bin. Every copy built anywhere but the app's own modded copy now carries a small keep note,
and a copy with one is never a leftover: Troubleshoot clears only the apps' own leftovers (half-built copies, the ones
older versions made per mod set). It is one code for both apps, so the Studio's Troubleshoot has the fix too. A copy
built before 0.9.8.16 has no note yet: rebuild it once with 0.9.8.16 or newer, or leave "Clear them" alone until you
do.

**New in 0.9.8.15: Vanilla gets the gold R.U.S.E. 2.0 title too.** Play on Vanilla in the Launcher used to start the
plain game through Steam, so only modded games had the gold title. Now it builds the modded copy with no mods and the
gold title, and starts the game from it, the way a mod set does: the first time it builds, then it starts at once
unless you played a mod set in between. RUSE Guard runs in its multiplayer matches, as in every set's. Untick the gold
title in Settings (the Launcher's or the Studio's: it's one setting) and Vanilla starts through Steam as before. Your
Steam install is never changed.

**Fixed in 0.9.8.14:** a few mods bring a match script of their own whose header asks for more room than the script
needs (1 VS 7 AI, 1 VS 15 AI, Operation Overlord and Sand Box among them). The game runs those scripts fine, but Play
and Test in game refused them with "RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...", so no
modded game with one of those mods could be built. The apps now read them the way the game does.

**Also new, in 0.9.8.13:** if you ticked Bug Watch and the game crashes, its report now also says what the game was
trying to read or write, and up to 16 places in the game that led to the crash. Both are read from the game's own
crash report on your PC, which still never leaves it. The agreement lists these two things now (version 3; nothing
else in it changed), so both apps show it to you once more.

**Fixed in 0.9.8.12:** 0.9.8.10 / 0.4.8.10 and 0.9.8.11 / 0.4.8.11 couldn't build a modded game: Play and Test in game
stopped with "No such file or directory: ...fairplay_watch.bin", because their installers left out three of RUSE
Guard's files. Update, and both work.

0.9.8.10 made big mods work, and brought fair play and trust:

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
  with a cheat or a test tool plays multiplayer and co-op only with players who have the same build, and leaves any
  other match by itself (new in 0.9.8.19, above; before it, such a copy left every match). During a real match
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
