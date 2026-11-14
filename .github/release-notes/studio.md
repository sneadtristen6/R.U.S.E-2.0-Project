**RUSE Studio, a preview for modders.** Browse the game's units in any of its ten languages, change them in a mod of
your own, and test it in the game. Your Steam install is never changed.

**0.9.8.20:** Guards where some mod sets stopped the game; an upgrade made in another building keeps its unit; the mod set editor says why, and Play waits for the mods' check; the build warns about missions a set leaves without their places, and .rmod mods' units get their models; Bug Watch says why a build or a Play failed, and the agreement's version 4; a game crash we know names its unit (Launcher); a squad's own soldier, changed in Blender (Studio); a squad soldier by soldier, one Open in Blender, animations for one unit or for the units you pick, models with animations of their own and the Generic Horse (Studio); Delete always goes through (Studio).

- **Guards where mods stopped the game:** with the R.U.S.E. Field Manual and the Balance Overhaul Mod together, the game stopped as soon as the Armor Base was placed (players' crash reports). Every modded game now has a guard on three places where the game's own scripts stopped it: research cards in a building's list for a unit that is in another building, a mission starting the computer player of a side a person plays, and a mission changing units after one of them was killed. A guard does nothing unless the game would have stopped. Tested in the game with the Armor Base; the two mission guards were tested outside the game.
- **An upgrade made in another building keeps its unit:** with the same two mods, researching the T-34 in the Armor Base took the T-26 out of the Barracks, because the game takes a unit away as soon as any upgrade of it is researched, wherever that upgrade is made. The build now makes such an upgrade a research of its own and says so in a warning. Tested in the game with the USSR and Italy. It changes some sets with the Balance Overhaul Mod, and sets with the Field Manual before the Balanced Realism Mod; the warning names each unit.
- **Join codes:** a set the build changes this way gets a new join code, so every player in a match with it needs this version. A set with a mod that gives a gun crew a model of its own gets a new join code too: the crew's little far-away figure now wears that model. A set with the Balanced Realism Mod, the Navy Mod, Sand Box or either Static Commandable Battleship - All Operations mod gets a new join code too: for some of their units, another nation's unit packs now load in every skirmish (below). Every other set keeps its join code. After the update, the next **Play** or **Test in game** builds your game again by itself.
- **Missions a set leaves without their places (Studio and Launcher):** when a set's mods leave a campaign chapter, an Operation or the tutorial without a place its mission watches from its start, the build warns, naming the mod and how many campaign chapters or Operations it does this to, or the tutorial: the game stops about a second after such a mission starts. Every mod is checked, whatever its version, your own too: the build reads the missions from your own game when it builds. The set still builds and plays as before, and the build's count of warnings includes these. Checked with builds of the community mods; not yet tried in the game.
- **.rmod mods' units get their models (Studio and Launcher):** a unit an .rmod mod (RUSE Mod Manager's format) makes, or moves to another nation, now gets the same model check as a Studio mod's unit, in any set and with the mod alone: when its model is only in another nation's unit packs, the build makes those packs load in every skirmish, so it has its model in matches where no player has that nation, and a note names the unit as its card does; where that can't be done, the build refuses the set and says why. Not yet tried in the game.
- **The Launcher's mod set editor says why:** when it can't make or save a set (no mod ticked, or a mod that is no longer in your library), it now says so inside the editor, under its buttons. Before, the message went to the set's page, hidden behind the editor, so nothing seemed to happen. **Create** and **Save** wait until a mod is ticked. Tried in a preview of the screen, not yet in the installed Launcher.
- **Play waits for the mods' check (Launcher):** **Play** stays off until the Launcher has checked whether the set's mods go together, and its tooltip says why. Before, a quick **Play** could send a set whose mods can't go together to the build, which refused it there. Checked by tests; not yet tried in the installed Launcher.
- **Missions of your own (Studio):** a new map's mission that makes units of a nation its copied mission doesn't load now gets that nation's packs, so those units have their models (the game stopped when such a unit was made). The mission check also refuses an event that hands a side a person plays to the computer. Checked by reading a real build back; not yet tried in the game.
- **Models from Blender, and a Custom uniform (Studio):** points Blender leaves with no bone follow the root bone, and the page says how many. **Import model…** also works now on a unit with a **Custom uniform**: it takes the copy out, and **Use the copied unit's model** gives it back in one click. Tested in the game with a squad's soldier weighted in Blender; the Custom uniform part was checked outside the game.
- **A squad, soldier by soldier (Studio):** a squad's page now starts with its squad card and a line for each soldier, in place of its **Its own model** box. **Open in Blender** on its card opens its soldiers side by side, each with his own copy of his pictures; after **Send to the R.U.S.E. Studio** in Blender, **Bring my changes back** gives each soldier only what was done to him. On his line a soldier has **Import a model…** and, once he has a model of his own, **Back to the game's look**. Seen from far away, the squad's little figures wear the look most of its soldiers wear. Tested in the game with a squad whose bazooka man alone was painted red.
- **One Open in Blender (Studio):** a unit's page has one **Open in Blender**: on a squad's card, and for any other unit in its **Model** row, under **More**, in the **Change it in Blender** box. **What goes to Blender ▾** beside it ticks what goes: a squad's soldiers (for a squad on bones of its own, such as the Generic Horse, which model), **Its bones** for a model on bones of its own, and **Its paint**; untick one and **Bring my changes back** leaves it as it was. While Blender has the unit, the button reads **Bring my changes back**. One of the game's own units that isn't a squad sends its paint alone, as **Repaint in Blender** did: copy it first to change its model. A model on bones of its own goes to Blender with its animations: one you don't change there comes back exactly as it went out, and of one you change, only the bones you changed are new; a change made in RUSE Decoy while Blender has the model stays when that animation comes back unchanged, and the page says so. Tested: a new M4 Sherman's whole model changed in Blender, then in the game; in the Studio, a copied G.I. squad's soldiers, the Generic Horse with **Its bones** unticked, and the game's own M4 Sherman's paint. The animations coming back unchanged were checked with Blender on our PC, not yet in the game.
- **More or fewer soldiers (Studio):** **Add a soldier** brings in a copy of one in the squad, a soldier from another squad, or a model file; **Remove** takes one out; **+1 soldier** and **−1 soldier** add or take away a rifleman at once, without Blender. A squad has 2 to 8 soldiers, and a soldier can have a look of his own that no other soldier wears. The game gets these through a small game patch, downloaded once and applied only to your modded copy, never to the game in your Steam folder; every other squad stays as the game has it. Tested in the game with squads of 3 and 7 made with these buttons, and with one rifleman alone painted red; a soldier from another squad or a model file, and squads of 2 or 8, not yet.
- **Animations for one unit (Studio):** a unit's page now has **Look and moves**: its model, its soldiers, its sounds and animations and what it rides in, row by row. **Change in RUSE Decoy** on the **Sounds and animation** row opens RUSE Decoy on that unit, and a change to one of its animations can be for **Only this unit**, which then plays its own copy, or for every unit that plays it. **Back to what every unit plays** takes the unit's own copy out. **Motion capture** goes on one unit the same way. Tested in the game with a squad dancing on the spot while every other squad stood as before; a speed, a stand-in or a bone changed for one unit, not yet.
- **Copies of an animation for the units you pick (Studio):** in RUSE Decoy, **Copy this animation…** makes a copy of an animation in your mod, listed under **Your copies**. Change the copy, then tick under **Who plays it** the units that play it in place of the animation, or under a unit only some of its soldiers or parts; every other unit plays the animation as before. **Back to the game's animation** takes your changes to the copy out again, and **Delete the copy** takes it out of your mod. Tested in the game with two copies of the soldiers' standing animations with a dance in them, ticked for a new squad and for the G.I. squad's bazooka man alone.
- **Animations changed in Blender (Studio):** for a new unit made in your mod, **Change its animations in Blender** in RUSE Decoy opens Blender with the unit and every animation it plays, each named for what it does in it. Change one, click **Send to the R.U.S.E. Studio**, then **Bring my changes back**: the changed ones become that unit's own, and every other unit keeps the game's. A sending you never brought back is set aside, and **Bring back the set-aside sending** takes it in. Tested in the game with a squad standing and running with an arm raised, and a Generic Horse whose horses hold their heads up.
- **Models with bones and animations of their own (Studio):** **Import model…** now also takes a .glb on bones of its own with its animations: a horse and rider, or any creature. **Its animations** shows which animation the unit plays for each thing it does; pick another, or leave it on **Nearest**. **On long moves** a squad can go as itself, playing one of them, instead of in its truck. **Its two halves** picks the bone where the model splits into the upper and lower halves the game animates at once (a rider aims while his horse runs), and **Will it work in the game?** says what in the model could stop the game or look wrong. In a squad, the riflemen and the heavy-weapon soldier each take a model of their own on their own line. Tested in the game with a Generic Horse made this way: riflemen and a bazooka man on horses, firing, riding as themselves on long moves, each horse falling with its rider; another animation picked by hand or another split, not yet.
- **The Generic Horse (Studio):** riflemen and a heavy-weapon soldier, each on a horse of his own, now listed in the **Units** tab with the units from other eras (**WWII+**, USA), off until you add it. **Add to my mod** makes its horses and riders on your PC from your own copy of the game (nothing is downloaded), adds it as a new unit of your mod and puts sneadtristen6 in your mod's credits; **Take it out of my mod** takes it all out again. There is one Generic Horse for every nation: its riders are always made from the G.I. squad, and in your mod it's a unit like any other, in the build menu you pick when you add it (the **Nations** tab moves it to another nation). Tested in the game added from the **Units** tab. Not yet tried in the game: in a mod someone shares with you, its Generic Horse can now be resized and moved on your PC once your Studio has made the same horse files (adding it to any mod of yours makes them); and when the Studio makes those files again and they come out different, they go beside the old ones, so a mod's Generic Horse never changes when you resize or move it (if its own files are gone or changed, **Resize** and **Move it** say so and leave it as it is).
- **A folder too deep for Windows (Studio):** when the Generic Horse's **Add to my mod** is refused because the Studio's folders are too deep for Windows, its page now offers a short folder, such as C:\RUSE2: **Copy everything to C:\RUSE2 and start again** copies the Studio's settings, the Launcher's library and mod sets, and your mods, maps, exported files and backups there, checks every file, makes both apps use that folder from then on and starts the Studio again from it; **Choose another folder…** picks another one instead. Nothing is deleted: your old folders stay where they are. Checked by tests; not yet tried in a real Studio.
- **Its own shine after Blender (Studio):** a model sent to Blender with **Open in Blender** and brought back with **Bring my changes back** keeps its own shine and side-colour layer; before, it came back with the plain one a model from a file gets. When one can't be kept, the page says which. Not yet tried in the game.
- **Where your model is kept (Studio):** the **Model** row (on a squad's page, **More options**) says where your mod keeps the unit's own model on your PC, with **Show in folder**.
- **The Nations tab (Studio):** **Start a new mod** now asks only for a name and opens the Studio on the new mod; the guided steps are off for now. What only they had is on the **Nations** tab: **Keep its units** or **Start it empty** for each nation, and **No research** or **Keep the game's research** for the whole mod.
- **Delete goes through (Studio):** **Delete this unit**, **Take it out of my mod** and the **Nations** tab's take-outs no longer stop when another program has one of the unit's files open: the unit goes all the same, and a file still held stays in the mod's folder for now. **Test in game** and **Export mod…** leave it out, and the Studio removes it by itself later, once that program lets go of it. A list file of the mod that another program holds for more than 3 seconds still stops Delete, with everything put back and the file named. Checked by tests; not yet tried in the game.
- **A unit with no card picture (Studio and Launcher):** a unit shown in a build menu with no card picture is now refused when the game is built, with what to change. In a test the game stopped as it started with such a unit (a copy of the HQ truck shown in a build menu).
- **Export leaves your PC's folders out (Studio):** an exported mod no longer carries the folders of your PC that the Studio wrote into its model records (often with your Windows user name in them): only the file's own name goes. In your own README files, each folder path is cut to its own name, and a path that ends at a user's own folder, and so names that user, is taken out whole; Export lists each cut, and the README in your mod stays as you wrote it. A README Export can't read goes out as you wrote it, and Export names it. Your other texts (descriptions, credits) go out as you wrote them, and Export tells you if one names your home folder. The credits of units from other eras, the Generic Horse's too, now go with the mod.
- **Smaller things (Studio):** each factory is called by its building's name; in Persian, the game's names show in English, never as code names; the check before **Test in game** also reads the map you're editing when it is a folder of its own, and offers its fixes there too.
- **Players, update your Launcher:** a mod whose squads have soldiers of their own, or whose units have animations of their own, needs Launcher 0.4.8.20 or newer: an older one can't give them.
- **Bug Watch says why, if you ticked it:** which check refused a build or found a mistake (a fixed name from our code), how far a **Play** or **Test in game** got, which mods from our list were on and how many of your own, Plays refused before they started, and updates offered, installed or failed. Never the words shown, a path, or the names, words or files of your own mods. A game's crash report after a script error also says how often the guards above kept that game going (not yet tried in the game).
- **A game crash we know names its unit (Launcher, if you ticked Bug Watch):** when the game crashes in one of the ways we know, the Launcher says so after **Play**, in your language: the unit the game was making, by the name on its card (and whether a mod added it), and why, in plain words. It reads this on your PC, from the game's own crash report and your modded copy; the name and the reason are never sent. The unit is told once you've accepted the agreement's version 4 (below). The Studio's **Test in game** doesn't say it. Checked on earlier crash reports; not yet tried in the game.
- **The agreement, version 4:** it now lists more of what Bug Watch sends, if you ticked it: how many mods of your own you had and what kinds of things they hold, such as units, maps, missions or scripts (counted by kind, never named, and never their words, paths or files); at a game crash, the map it was on (one of the game's own maps by its name, a map a mod made only as "a mod's map") and the unit the game was making (one of the game's own units by its number, a unit a mod added only as "a mod's unit"), each only when the game's crash report shows it; and which version of the agreement you accepted. It also says now that the names and words of your own mods are never sent. Nothing else in it changed. Because it changed, both apps show it to you once more when they open; your username stays, and the Bug Watch box stays as you had it.
- **Unchanged:** RUSE Guard, a game without mods, the campaign and skirmish.

**0.9.8.19:** RUSE Guard: a game built with a cheat mod now plays multiplayer and co-op with players who have the same build. Not fully supported yet and it may still be buggy: use it in multiplayer at your own discretion.

- **Reported by a player:** two friends with the same mod pack were thrown out of every multiplayer match, because one mod in it (Infinite Supply Depot) is tagged as a cheat. RUSE Guard treated every game built with a cheat mod or a test tool as offline only: it left each multiplayer and co-op match a few seconds in, and never looked at who else was playing.
- **What we changed:** one second into a multiplayer or co-op match, such a game now tells the other players' games which build it is: a short code made from the game version and the mods, nothing about you. About seven seconds in it decides. If every player has the same build (the same game version, the same mods in the same order, the same mod versions), it says so on screen and the match goes on. If anyone has another build or no mods, it leaves the match as before.
- **A join code for these sets:** in the Launcher, a mod set with a cheat mod now gets a join code like any other. The same code means the same build, so compare codes before you play.
- **Every player needs this version:** the game of each player in the match must be built by Launcher 0.4.8.19 or Studio 0.9.8.19, or newer. After the update, the next **Play** or **Test in game** builds it again by itself.
- **Not fully supported yet:** we tested it in the game with one player hosting a multiplayer match alone against the computer, and outside the game with 20 simulated matches of up to four players. Nobody has played it with two people in a real match yet, so it may still be buggy: use it in multiplayer at your own discretion. Try it and tell us what happened on Discord or GitHub: which RUSE Guard message you saw, and whether the match went on.
- **Unchanged:** a game built without cheat mods, skirmish against the computer and the campaign.

**0.9.8.18:** A fix behind the scenes: the check of a modded copy lists what it finds in the same order on every system.

- **Behind the scenes:** the check of a modded copy (which game files changed after it was built) now lists what it finds in the same order on Windows and Linux. What it finds doesn't change.

**0.9.8.17:** Imported models sit where the unit stands, their turrets and propellers in their own places; an ammo can have a weapon class of its own.
<!-- required update -->

- **A required update:** older versions can't be used any more. When the app opens it installs this one by itself, and **Test in game** waits until it's in.
- **Imported models sit where the unit stands** (a modder's report: models were drawn ahead of their selection rings): **Import model…** now puts a new model on the middle of the unit it copies and gives it a skeleton of its own, so its turret turns where the turret is on your model. Every new import is fitted this way. A model imported before keeps its old place until you import it again or move it (below), and the era units keep theirs. Tested in the game with the game's own Sherman, opened in Blender and brought back, on other units; not yet with a model from elsewhere, another turret tank, or a turret that turns all the way round.
- **Move it:** if a model still doesn't sit right, open **Move it** under its size on the unit's page (folded away until you need it; it stays open on a model you have moved). **Forward**, **Right** and **Up** move it from where it's fitted, in the game's units (the page says how long the copied unit is in them); a minus goes the other way, and 0, 0, 0 puts it back. Its turret and propellers go with it, so they still turn in the right place, and a new size keeps the move. In the 3D view a blue ring shows where the unit stands, its mark at the front. A model rigged to the unit's own bones stays where its bones are: move that one in Blender. From the command line: `ruse import-model ... --move F R U`. Tested in the game with tanks moved forward, back, right and up.
- **Planes keep their own propellers:** a plane opened in Blender from the Studio and brought back with **Import model…** keeps its propellers where your model has them, as many as it has, whatever the plane it copies had: blades on the ground, spinning discs in the air. In the 3D view a plane's discs now show see-through, the way the game draws a spinning propeller. Tested in the game: a three-engined bomber's model on a copy of a one-engined fighter, and the other way round. A plane model from anywhere else keeps its propellers as drawn, standing still: the importer can't tell yet which of its parts are propellers.
- **Any unit can take a model:** soldiers, a gun's crew and the planes the Studio couldn't fit a model to before (the P-47, for one) take a model of their own too, one rigged to the unit's own bones (one of the game's models opened in Blender from the Studio and changed there, say). It keeps those bones and is used as it is, and a squad's other men with the same bones wear it too. Tested in the game: a rifle squad, a gun's crew and the P-47; not yet a model from elsewhere.
- **Play them with this update's Launcher:** a mod with a model imported by this version needs this update's Launcher or newer, for you and your players: an older Launcher gives the model the copied unit's skeleton, so its turret turns around the wrong point. Mods with models imported before play as they did.
- **New weapon class** (on the ammo page): the **Weapon class** box sets how much of its damage an ammo does to each kind of target. **New weapon class…** opens one number for each: buildings and fortifications, aircraft, paratroopers coming down, infantry, light vehicles, armour 1 to 5, and construction trucks. 1 is full damage, 2 double, 0.5 half, and 0 means it can't attack that target at all. **Save class** gives the ammo its own copy of the game's damage table, so no other ammo's damage moves; like any change to an ammo, it counts for every unit that fires it (copy the ammo first for one unit only). **Back to the game's class** takes the copy out, and deleting a copied ammo takes its class with it. Tested in the game: rifle squads whose round got numbers against tanks shot at tanks with their rifles and damaged them. Seen in a preview; not clicked in the app window yet.

**0.9.8.16:** Troubleshoot keeps the game copies you made yourself.

- **Fixed: Troubleshoot's "Clear them" deleted copies you made yourself:** the same fix as the Launcher's (one code for both apps). A copy of the game you built by hand in the copies folder, a test copy or a reference copy, counted as a leftover and was removed for good. Every such copy now carries a small keep note, and a copy with one is never a leftover: only the apps' own leftovers (half-built copies, the ones older versions made per mod set) are cleared. A copy built before this version has no note yet: rebuild it once with this version, or leave "Clear them" alone until you do.

**0.9.8.15:** Vanilla gets the gold R.U.S.E. 2.0 title too.

- **No change in the Studio itself:** this update is the Launcher's (Vanilla gets the gold R.U.S.E. 2.0 title). The gold title tick box in the Studio's Settings is the same setting as the Launcher's, so unticking it here also starts Vanilla through Steam.

**0.9.8.14:** Mods with a match script of their own build again.

- **Fixed: Test in game stopped for some mods** with "RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...": a few mods bring a match script of their own whose header asks for more room than the script needs (1 VS 7 AI, 1 VS 15 AI, Operation Overlord and Sand Box among them). The game runs those scripts fine, but the Studio refused them, so nothing with one of those mods could be built. It now reads them the way the game does.

**0.9.8.13:** Game crash reports say what led to the crash.

- **Bug Watch's game crash reports say more:** if you ticked Bug Watch and the game crashes, the report now also says what the game was trying to read or write, and up to 16 places in the game that led to the crash, read from the game's own crash report on your PC, which still never leaves it. A report that only said where the game stopped couldn't show why; now we can trace crashes like the one a player sent us this week, and fix them.
- **The agreement, version 3:** it now lists these two new things among what a game crash report carries, and nothing else in it changed. Because it changed, both apps show it to you once more when they open.

**0.9.8.12:** Test in game builds modded games again.

- **Fixed: Test in game stopped for every mod** with "No such file or directory: ...fairplay_watch.bin": the installers of 0.9.8.10 and 0.9.8.11 left out three of RUSE Guard's files, so no modded game could be built. They're back in, and an app missing any of its files can no longer be released.

**0.9.8.11:** Sign in through Steam finishes in the apps; on Linux, a build's helper programs start the way they do on Windows.

- **Fixed: Sign in through Steam.** After you signed in on Steam's page, the Launcher and the Studio kept waiting and never asked our server whether you were done: the window stopped its own checks before the first one. It checks every few seconds now and signs you in as soon as Steam says so. Tried in the preview: the check runs and the window shows you signed in.
- **Helper programs start fresh on every system:** the programs a build shares its work out to (imported models, mending the map, movement, water, the map view's terrain) now start fresh on Linux too, the way they always have on Windows. On Linux they started as copies of the running app, which could now and then hang a build, and made one of our checks fail there. Nothing changes on Windows or under Proton on the Steam Deck.

**0.9.8.10:** mods past 4 GB, build lists in groups, faster builds of big mods, your files in Documents\RUSE 2.0, Persian and every page in 11 languages, fixes from testers' reports; and RUSE Guard, our anti-cheat for real multiplayer matches; Bug Watch, crash and usage reports you can opt into; Sign in through Steam; and a first-start agreement.

- **Fixed, reported by a player: mods past 4 GB.** A modded game whose packs passed 4 GB stopped building ("'I' format requires 0 <= number <= 4294967295"). Packs now carry their full length, and one past 4 GB is written in a wider layout that a small game patch lets the game read: downloaded once and applied only to your modded copy, never to the game in your Steam folder. Past 32 GB, or for one file past 4 GB, the build says so plainly. Tested in the game: copies past 4 GB, and with 200, 283 and all 366 era units.
- **Many models of your own:** the game finds a pack's texture stand-ins through an index, and a build that added stand-ins for imported models wrote it wrong: with many era units the game hung or crashed while loading. It's now written the way the game reads it, for every mod that adds them. Tested in the game with all 366 era units.
- **Build lists in groups:** with many units, a building's build list ran off the screen and the units below couldn't be reached. Each list now shows one row per group, the game's own lines (a new unit joins the group of its kind): at most 6 units a group and 10 groups a building, so the whole list stays on the screen. The Studio says why when a group is full and shows the groups on the board and in the era form; a mod made before that's over the limits still builds, with a warning. Tested in the game with 297 era units in groups.
- **Faster builds:** the models you import are kept between builds, and new ones are made side by side on your PC's cores. A mod with 366 era units took about 18 minutes to build on an 8-core PC; now about 5 the first time and about 3 after, with the same game files, byte for byte.
- **Imported models (testers' reports):** a turret part on a bone the copied look doesn't list (an M109 copied from the M7 Priest) stopped the import; now it goes on the copy's own list. A turret part on a model with no turret (the P-40, the M274 Mule) rides on the hull, a towed gun seen from far away shows its own model, and a thin strip texture gets its stand-in. The towed guns tested in the game; the turret parts not looked at closely yet.
- **Bridges (a tester's report):** one Bridges tab: a new bridge, your bridges (each with Go to and Delete), and the map's own bridges with their crossings, taken out or put back with one button. A new bridge counts when taking the old ones out cuts the map in two, and shaping the land keeps the ends of the map's own bridges at their height. Erase is easier to find (Paint & Erase, or the X key). A unit mod and map changes made under one name build together, and the map view shows the game's models again. Not tried in the game yet.
- **Your files in Documents\RUSE 2.0:** your mods, maps, exports and backups go in Documents\RUSE 2.0, where File Explorer shows them; what the Studio kept in its old folder moves there once, and it says so. Delete a mod sends it to the Recycle Bin, Show this mod's folder opens it, and Settings shows where everything is. Seen in a preview; not tried in the app windows yet.
- **Persian and 11 languages:** Persian is the apps' 11th language, written right to left; the README, the wiki, these notes and the setup screens are in all 11.
- **Required updates:** an update we mark required installs by itself, with a box nobody can close (apps from this version on can read the mark). The What's new box keeps its height while you scroll it.
- **Owned copies only:** before Play or Test in game builds a modded copy, the apps check that the game folder is a copy you own, from what Steam left there, on Windows, under Proton on the Steam Deck and on Linux. If yours can't be confirmed (a boxed copy from before R.U.S.E. was on Steam), a box lets you open a ticket, and we send you an unlock code for that PC.
- **Discord:** the apps and pages use a new invite that doesn't expire.
- **A first-start agreement:** the first time the Studio or the Launcher opens, it says what RUSE Guard does and asks you to accept it (it's required to play online with the apps), whether to turn Bug Watch on (optional), and a username our developers see with your reports: a # and four numbers are added so it's unique, like Nick#4821. One name works for both apps. The agreement shows again when it changes. Seen in both apps. In all 11 languages.
- **RUSE Guard:** our anti-cheat, from DomesticNukes' design. It works only in multiplayer and co-op matches, never in single-player, skirmish against the computer, the campaign, or while you make mods. A modded copy built with a cheat or a test tool is for offline play only: it leaves multiplayer and co-op matches by itself. During a real match it checks the names of your running programs against a list of known cheat tools (names only; nothing else is read), and what it collects from a match is filed under your username, never your Steam account. Test in game builds its copies with it. Tested in multiplayer matches with a real opponent; the evidence reaches our server.
- **Bug Watch (optional):** when you tick it, the Studio and the Launcher count what you use and when something goes wrong, the apps' crashes and the game's, with which mods were on, and send it once a day to our developers with your username. No real names, no Steam account, no files. Off unless you tick it; untick it any time and what was kept is deleted. Seen in both apps.
- **Sign in through Steam:** a sign-in on Steam's own page in your browser confirms you own R.U.S.E., for online play, RUSE Guard and content downloads. We never see your password, and your Steam ID is never stored: only a pass kept on your PC for 30 days. The Studio asks once; the Launcher's Settings opens it any time. Nothing needs it yet. Not tried in the apps yet.

**0.9.8.9:** downloads on more PCs, and a safer picture reader.

- **Fixed, reported by a player:** on a PC whose Windows hasn't got the certificate GitHub's downloads are checked against and can't fetch it, downloads failed ("unable to get issuer certificate"). The Studio's downloads (its updates, the game patches, the era units' models and Map Paint's online textures) now also try with the list of certificates Firefox uses, which it carries.
- **Safer pictures:** the library the Studio reads pictures with (Pillow) is now version 13.0.0, with its fixes for specially made picture files that could crash the app, use up its memory, or worse.
- **Tighter code:** the 12 warnings GitHub's code check gave on this project are answered. When the Studio shows its pages in your web browser, they open only its own files, checked in a way that check recognises; downloads ask for TLS 1.2 or newer, as they already did; and reading a failed test's road mistakes stays quick on any message. Nothing else changes in how the Studio works.

**0.9.8.8:** a start screen and a buildings board, buildings of your own, RUSE Decoy for sounds and animations, every game rule in one tab, and R.U.S.E. 2.0 in gold.

- **A start screen:** carry on with your mod, start a new one, or skip it (or always skip it). A new mod's steps: its name, whether each nation keeps its units or starts empty, research (the game's, none, or your own), the buildings board, then what the mod will change. Seen in the game.
- **The buildings board:** each nation's buildings as rows of the units their build menus offer, in the game's order. Put a unit in (the nation's own, a copy of another nation's, an era unit), drag it along a row or to another building, take it out, or research it from the unit it goes under. Each unit's page says where it's built. Seen in the game.
- **Add a building:** a copy of one of the game's buildings that makes the same units, or a building with units of its own and its own tab on the build bar, up to three a nation. The second and third need a small game patch for more buildings: the Studio downloads it once and applies it only to your modded copy, never to the game in your Steam folder. Seen in the game.
- **A building's own look:** on a new building's page, import a 3D model in place of one piece of the look it copies (the main building of a factory or HQ, or the piece you pick), and give it its own picture in the build menu. Seen in the game.
- **Import model on the Maps tab:** a 3D model (.glb, .gltf or .3ds) becomes one of your map's own rocks, props, plants or trees, placed like the game's own, with a size and its maker's credit (models by others: CC0 or CC-BY only). Units knock it over like the game's own; ticked **Solid**, they go round it. Seen in the game.
- **RUSE Decoy, the sound and animation designer,** in place of the Music tab. Every sound in the game by kind (weapons near and far, hits, engines, surroundings, the interface, ruse cards, unit voices, radio, mission lines with what each line says, music): play it, give it its own volume (0 to 200%), or replace it. Animations: put another clip in a clip's place, make one slower or faster, make a bone bigger or turn it, or put motion capture on the soldiers, from a library of 3,205 free moves (the CMU motion capture database and 100STYLE, credited), each downloaded when you pick it. A unit's page opens RUSE Decoy on that unit's own sounds and animations. Seen in the game. Its error messages are in English only for now.
- **AI and player settings:** the Economy and AI tabs are one tab. Player settings: money and income, supply depots, production and ruse cards, as before. Computer players: every one of their 47 values on the default set, each difficulty and each personality (a value the game leaves out of a set shows the 0 the game counts). **Game rules:** 172 more of the game's values in 16 groups (battle and surrender, population, movement and roads, firing and targets, damage, woods and cover, aircraft, ruse cards at work, placing buildings, online ranked play, outlines and effects on screen, the colours of players and sectors with a colour picker, and others), each named and explained. Not tried in the game yet.
- **All values and files:** the All values and Files tabs are one tab, with a switch on top; it opens on the part you used last.
- **Fixed:** All values showed a colour's numbers in the wrong order (the game keeps blue first), so player colour 1, blue, looked orange, and typing in red changed blue. Colours show and take red first now; a mod file keeps the game's order, as before.
- **Fixed: dark and light blotches on maps the Studio made** (blank, bigger, relief and sector maps): the ground's tilt was written wrong, so grass and fields were lit unevenly. A map is lit right once it's built with this version (its ground is made again the first time). Seen in the game.
- **Take out the old crossings (from DomesticNukes):** in the Maps tab's roads, with **Take out the map's bridges** on, **Close the old bridges' crossings** also closes the ground where each old bridge stood over water and cuts the road links through it, so nothing crosses there any more; the rest of the road network stays. Not tried in the game yet.
- **R.U.S.E. 2.0 in gold:** the modded game Test in game builds opens on a battle scene with an engine starting, and its main menu, every menu's small title, the menus' outlines and the loading screens say R.U.S.E. 2.0 in gold. It's made on your PC from your own game's files the first time (a few minutes once, then kept). Settings has a tick box to keep the game's own title. Seen in the game.
- **The game's lettering:** the Studio is written in the game's own menu font, taken from your game each time it starts (the font isn't carried with the Studio).
- **Fixed, reported by a modder:** a model imported on a new unit made from the Panther landed far away from the unit. On new units made from 85 other units it sat off the unit's turret, some by a lot (the 155 mm GPF, the SU-85, the Carro Veloce, the StuG III, the M7 Priest), most by a little. The Studio misread where those units' turrets turn, because their skeletons scale the turret bone; it reads them right now. A model imported before this fix keeps its old place: use Import model again on that unit. Not tried in the game yet.
- **Fixed, reported by a player:** a model whose pictures are JPG or WebP (most downloaded .glb files) was refused; it imports now. A model the importer still can't read (compressed meshes, KTX2 pictures) says so and how to fix it in Blender. Not tried in the game yet.
- **Fixed, reported by a player:** one of the game's own tanks, opened in Blender and imported back, kept its turret still. Open in Blender now names each part's bone as the game does, and Import model turns a part on the turret's bone with the turret. A model exported before this keeps its old names: open it in Blender again. Not tried in the game yet.
- **Name your ammo:** a copied ammo is called by the name you give it in game too, and every ammo's page has **Its name in game**: type a new name or kind for it, in every language at once, then change one language on its own. Not tried in the game yet.
- **Flag types of your own:** under a unit's flags, **Make or change flag types…** makes a named type: tick the game's flags it turns on and off. Give it to any unit from its flags; take it off and the unit's flags go back as they were. Change a type and every unit that has it changes too. The game only acts on its own flags, so a type combines what they already do. Not tried in the game yet.
- **Shot speed explained right:** the number guide said an ammo's shot speed, drag, "without physics" switch and the time before it flies were looks only. They decide when the hit lands: a slower shot hits later, and a moving target is aimed ahead by the flight time (from the game's workings; not tried in a test yet).
- **Every error in ten languages:** the 35 Studio errors that came with Import model and the buildings board.
- **Credits:** the README says what LittleGroove's engine still does in ours, what is ours, and that our texture reader uses ProLution's codec too.
- **Still buggy, use at your own discretion:** Map Paint's textures, and both blank maps (Blank Terrain and Blank Ocean).

**0.9.8.7:** Redo and select what's placed, Grid / Box / Path placing, bigger blank maps, and every value explained.

- **Fixed, reported by a modder:** on a new unit made from one of 17 of the game's units, the box for changing its model never appeared, because the Studio didn't find the copied unit's 3D model. The 17: the King Tiger, the atomic guns, the Long Tom nuke, the V2 launcher, the TransportHQ, the Wurfrahmen half-track, the atomic OI, Type 1 and Type 4, and three campaign versions. The Studio finds those models now, and if it ever can't find a model, the box says so instead of disappearing. The report was about the Panther, which worked on our PC, so that case isn't confirmed fixed yet.
- **The AI tab explained:** each computer-player value says what it does, in plain units (metres, $, minutes) where it has them, and which value wins in a battle for each difficulty and profile. Game modes, difficulties, profiles and units are picked by name instead of by number.
- **Every value explained, everywhere:** All values says what each value does under its name (what a unit links to and the texts it shows too, not only numbers), in plain units, with the price's five boxes named by game mode; a value with no name of its own gets a plain one instead of its code name. On the Units tab every row says what it is, the ones that can't be changed too. The Maps tab's ground brushes say their size in metres and their strength as what it does on that map (a height in metres for Hill, Raise, Lower, Crater, Plateau and Water; a share of the way for Flatten, Level, Smooth and Ramp). The Music tab says when each battle list plays: calm while players build up, fighting once shots land (both heard in the game), and ruse music when a ruse card is played (from the game's workings; not heard in a test yet).
- **The Economy tab, Normal and Nuclear apart:** the game keeps its economy twice, once for its usual modes and once for the Nuclear mode. Where the two differ (money per truckload, ruse cards at the start, when new ruse cards come), each mode now has its own boxes, so the Nuclear mode can be changed alone; elsewhere one change still sets both. Each value also says what it does, under its name. A Nuclear-only change hasn't been tried in the game yet.
- **Redo and select:** Redo in every map tool (Ctrl+Y or Ctrl+Shift+Z, and a Redo button); in the Buildings and Props & trees trays, select what's placed (click, Shift+click or a box), drag to move it, turn it, resize it or delete it, the map's own objects too.
- **Grid, Box and Path:** place rows of objects in a grid or a box, buildings facing the roads, and hedges, tree lines and tree belts along a path, with cover.
- **Bigger blank maps:** a new blank map's Map size window adds or takes strips of ground on any side, and Make sectors fills it with sectors.
- **Menus and feel:** number rows instead of sliders, a search with #tags and your recent searches, pop-up cards, and keys you can rebind (Swap, Take it, Cancel).
- **Safer:** closing the Studio with unsaved work asks first; a map with new cut-off ground is refused before Test in game; a mod made with an older Studio is updated with a backup first (Update this mod); kept build results stay good after a Studio update.
- **Every message in ten languages:** the Studio's errors and the build's lines.
- **New unit** leaves out the two units with no model to start from (the SOLO 57 mm gun and the SOLO paratroopers).
- Not tried in the game yet: what's placed with Grid, Box and Path, moved objects, and a bigger map made in the Studio.
- **Still buggy, use at your own discretion:** Map Paint's textures, and both blank maps (Blank Terrain and Blank Ocean).

**0.9.8.6:** every unit flag and number explained, the map tools show what they did, and blank maps drawn right.

- **Unit flags explained:** each flag on a unit's page shows its name, and hovering it says what it does, how to use it and how sure we are. **Flag guide: every flag explained** lists all 105, with a search. The Studio checks a unit's flags: a known crash (a truck's flags on something that isn't a truck, an armed plane given the recon flag without the fighter flag) shows its fix, and the Studio won't start the game until it's fixed; flags expected to break a unit get a warning.
- **Every number explained:** hover the name of any number of a unit or building to see what it means; beside it, its value in plain units (metres, km/h, seconds, degrees, $, %), a slider to make it smaller or larger than the game's value (its base stat, -90% to +300%), and where it sits among the game's units of its kind. Speeds are in the game's own km/h.
- **How weapons and ammo work**, step by step, in the Weapons box.
- **The map tools show what they did:** Cover, Uncover, Town, Forest, Block and Open mark the ground each stroke went over and say how many m² changed for units, or that nothing changed. Town works in real metres and rings the buildings a click will cover first.
- **Placing:** placed buildings, trees and props show their real models (with a dot at each one's foot); the picked one shows see-through under the pointer before you click; the place list is a grid of pictures. Trees are no longer black, and sector numbers hide when the camera is close.
- **Blank maps** (seen in the game on a Blank Terrain map): shadows over flat ground; what you place where the copied map had sea is drawn; the camera's floor follows the new ground.
- **Still buggy, use at your own discretion:** Map Paint's textures, and both blank maps (Blank Terrain and Blank Ocean).

**0.9.8.5:** planes in any role, weapons that hit planes, and a library for Map Paint's Texture brush.

- **A plane's role** (a player's report: a fighter-bomber given a bomber's carpet bombs flew to its target and dropped nothing): a new Role box on a plane's page makes it a Fighter, Fighter-bomber, Bomber or Scout. Its behaviour, how the computer players use it and its build menu words change with it. A bomber's bombs go in a bomb bay (copied from a game bomber's), the only way a bomber's run drops them. Seen in the game: a fighter-bomber made a bomber drops its bombs; a scout that keeps its guns (a Stuka, an ME109) still attacks and has the scouts' sight.
- **Recon vehicles:** a ground vehicle's Role box makes it Recon: the recon cars' sight (much further than a tank's), how the computer players use them, their build menu words, and it can go into woods (seen in the game with a Panzer IV).
- **What a weapon hits:** each weapon's Hits picks the ground, planes, or both (a second weapon beside it, the way the game's AA guns carry one for each). Seen in the game: tank rounds firing at planes. Known: a plane's gun set to hit the ground alone does no damage yet.
- **Map Paint's Texture brush gets a library:** the game's own ground textures (grass, fields, sand, snow, rock, roads..., by theatre, with a search), a square of any map's ground, pictures of your own, and free pictures online (Poly Haven and ambientCG, CC0; US aerial photos, public domain), one picture downloaded per click and kept in your mod with its credit. A Size slider, the textures used lately, and **Game detail up close**, which lays the game's own decals of a game texture over the ground you paint. Not yet seen in the game; the online downloads not tried yet.
- **Objects placed in open ground**, away from the map's towns, farms and woods, are now within reach of the game's drawing, and big groups of new objects are laid out the way the game's own are (not yet seen in the game).
- **Faster repainting:** the painted ground is kept from build to build, whichever copy or mod painted it: a map painted again the same way takes it back in seconds, not minutes.
- **Still buggy, use at your own discretion:** Map Paint's textures, and both blank maps (Blank Terrain and Blank Ocean).

**0.9.8.4:** missions of your own, blank maps you build up, and much more to customise.

- **Still buggy, use at your own discretion:** Map Paint's textures, and both blank maps (Blank Terrain and Blank Ocean).
- **Missions of your own:** a new Operation or campaign chapter gets its own mission on the map screen's Scenario side: sides, goals, events (When → Do: bring in units, move, attack, hold a zone, artillery, bombing, paratroopers, messages, money, victory, defeat) and camera moves. Seen in the game: its camera move, goals (a zone, a group destroyed, a time), repeating events, money, a side handed to the computer. Not tried yet: paratroopers, a camera move set off by an event.
- **Map | Scenario** on the map screen: the other side's things show faded and can't be grabbed by accident.
- **Blank maps:** nothing of the copied map shows any more, and you place each player's HQ (the build waits until every one is placed). Blank Terrain works for Operations and campaign chapters too.
- **Sectors you make:** paint them, drag their corners, draw a new one as a box, leave ground in no sector, delete one (seen in the game).
- **Supply depots:** the Economy tab gives every depot on every map, or on one map, more trucks (times, or a number each); no more 1,000-truck top.
- **Nations tab:** hide all of a nation's units at once, show them again, or fill its menus with an era's units.
- **Edit an installed mod:** open any mod the Launcher has; someone else's becomes a copy of your own under its own name. RUSE Mod Manager mods (.rmod) are converted so their values can be changed.
- **The mod check in plain words**, with a fix button for each problem.
- **A unit's own look:** its own copy of its model to repaint; squads wear the default uniform or a custom one; pick the truck a squad or gun rides in. Infantry show in 3D and open in Blender.
- **Armour** is picked as one of the game's levels, so the card shows what the unit fights with; **imported planes** keep their spinning propellers and come back facing forward (both seen in the game).
- **Model sizes on a slider** (Tiny, Game size, Real life, Huge: 0.05 to 20), resized any time, every plane at once.
- **More to change:** an AI difficulty's or profile's own value for one only Default lists; numbers past the map tools' sliders; louder and longer music edits.
- **Fixed:** a unit shown in a menu but researched from a hidden one stopped the game: the check names it and the build refuses it. Tanks fire across erased towns again, and units no longer fall into the holes where bridges were taken out (seen in the game).
- **Downloads work on every PC:** when Windows hasn't fetched the certificate GitHub is checked against, the Studio asks Windows for it, as a browser does, and tries again (not tried yet on a PC that had the problem).

**0.9.8.3:** modded copies go where you say.

- **Where modded copies go**, in Settings: choose the folder the modded copy of the game is built in, or go back to
  the recommended place, `RUSE-Instances` on the game's drive (there the copy shares the game's files and is ready in
  seconds; on another drive it is a full copy of the game, slower and bigger). The game's clean backup goes beside it.
  The next Test in game builds in the new place; the old folder can be deleted by hand. The Launcher uses the same
  folder.

**0.9.8.2:** the units from other eras arrive: their models, at their real size, behind research.

- **Units from other eras:** the WWI, WWII+, Cold War and Modern eras in the Units tab have their units now: 366,
  each another maker's free model (CC0 or CC BY), credited. Each era downloads in the Studio when you pick it, from
  our GitHub (each file checked: WWI 232 MB, WWII+ 198 MB, Cold War 996 MB, Modern 709 MB), and updates itself as
  more are finished.
  - **At their real size:** each unit's real width (a plane's: its wingspan) at the game's own scale; change it from
    0.2 to 5 times.
  - **Researched like the game's units:** from any unit of its nation's building, the mod's own era units too, so a
    chain works (a T-80, then a T-90M), with its research price and time. WWI and WWII+ units can be bought straight
    away; Cold War and Modern ones start as researched from a suitable unit.
  - **Their own cards** in the build menu and when selected.
  - Seen in the game: they load at once, the research tabs and a chain, a Land Rover with its own model, the sizes.
    Not tried yet: towed guns (no game gun to fit them to yet).
- **Import model…:** a model with a crew figure first gets its own model (jeeps copying the Kübelwagen showed the
  Kübelwagen's); models painted the specular-glossiness way keep their paint; colours given as numbers aren't black
  any more; big models import faster.
- **A unit researched from another army's unit** left the game on an endless loading screen: **New unit…** drops that
  link now, and the build refuses a unit researched from a missing unit or another nation's, saying why and how to
  fix it.
- **Taking out a unit others are researched from:** choose in **Settings > Research** to be warned first (the
  default), refuse, or re-link them to its own parent; a unit left pointing at a gone one shows it on its page and in
  the check. Research times can be typed in seconds or minutes (that the game counts them in seconds isn't tried in
  the game yet).
- **Linux and Steam Deck (through Proton):** the Studio opens in your web browser when its own window can't. Not
  tried on Linux yet: tell us how it goes.

**0.9.8.1:** LittleGroove's tools come to the Studio, with music and sounds, and a nation made into another.

- **LittleGroove's tools, brought over** from his RUSE-Mod-Manager:
  - **Economy tab:** starting money and income, supply depots, and the ruse cards each side starts with. Seen in the
    game: the starting money and the starting cards.
  - **AI tab:** how the computer players play, the units they prefer and the ruse cards; and the game's map and mission
    scripts, shown as Python, read only. Seen in the game.
  - **Upgrade box** on a unit's page: the unit it's an upgrade of, its own upgrades, its research price and time.
  - **All values tab:** any of the game's objects and values, changed in a mod: add or take out a value, make or
    delete an object, give a text value words of its own.
  - **Files tab:** any file of the game's packs, seen and saved out. Change one with a file of yours or add one: your
    mod keeps only the changes, each checked as its kind.
  - **Missions:** change a mission's scripts; see whether it's in the menus, whether every file it needs loads, and its
    texts; move it up or down in its menu.
  - **Maps:** town and hill names, named points and zones, a map item's name and facing. **Notes** on a unit, a value
    or a computer player.
- **Music tab:** every song by where it plays, each replaced in a small editor in the Studio (cut, fade, volume); new
  songs added to the battle lists; a unit's voice lines on its page; a map's background sound. Seen in the game: the
  songs, the new songs and the voice lines.
- **Make a nation into another.** The new **Nations** tab gives one of the game's seven nations a new name (in the
  lobby, and for its army) and a new flag from any picture: China in Italy's place, say. Its units and what they say
  are changed as before, on the Units tab and each unit's page. Seen in the game: the new name in the lobby, the new
  flag in a match.
- **Units from other eras:** the Units tab gets the eras WWI, WWII+, Cold War and Modern beside the game's own units.
  They have no units yet: those come in a later update.
- **New map: start from scratch…** is on the Maps tab before any map is open.
- **Blank Terrain's ground is drawn as its own.** A new map started blank gets its ground made from your terrain
  strokes, not the game map's ground pushed about: round shores up close and from high up, no dents in hilltops, and
  buildings and tanks sitting right on it. Seen in the game on test maps.
- **Blank Ocean stays, with a warning** on its button: separate islands aren't ready for full-scale battles
  (below).

Not tried in the game yet: the Upgrade box, All values, Files, the missions' tools, the map additions and
background sounds.

**Why there are no navy maps yet.** We tried maps of islands for full-scale battles with ships, and the game itself
stands in the way:

- A land unit sent to an island it can't reach crashes the game.
- Joining the islands with a strip of land stops the crash, but then the computer just sends its infantry across it.
- With no road between the islands, no building can be placed anywhere.
- With the game's own weapons, ships and land units can barely hurt each other.

Map data alone can't fix the crash, so navy maps wait.

**0.9.8:** a new map can start blank, as flat land or open sea, and every map can have its own pictures in the
game's menus.

- **Start a map blank.** **Duplicate map** has a new choice, **Start from**: **Blank Terrain** (flat land with
  nothing on it but the starting points) or **Blank Ocean** (the sea over the whole map). Seen in the game.
- **Menu pictures for any map.** Pick a PNG for the map's picture and its 3D map in the menus, or go back to the
  game's own; the white start dots are drawn where the map's players start. **Make in Blender…** opens the map's own
  3D model to make them, and **Bring back** puts them in your mod. Seen in the game.

| Before | Now |
|---|---|
| A new map started as a full copy of a game map. | **Duplicate map** can start it blank: Blank Terrain or Blank Ocean. |
| A new map showed the menu pictures of the map it copied. | **Menu pictures…** gives it its own: a PNG of yours or a picture made in Blender, with the start dots where its players start. |
| The map's own depots, units, buildings and names stayed. | **Take out** one, or every depot or name at once (seen in the game). |
| The map's own roads and bridges stayed. | The Roads dock takes them out (the road lines gone: seen in the game). |
| Sectors left the sea and the map's edges out. | **Sectors over the whole map**: all of it can be taken (seen in the game). |
| A map's water came from its rivers and its sea only. | **Water over the whole map**: a thin layer, like a navy map's painted sea (seen in the game; units under it not tried yet). |
| The map editor picked spawns one at a time, by code names. | Drag a box to select them as the game does; above the tray, the map's own icons show what's selected and how many. |
| The map editor's panels had one size. | Each floating panel resizes, from 40% to 125%. |
| What's new was in English only. | It's in the Studio's own language. |
| Sending a mod to the mod list meant writing its entry by hand. | **Publish to the mod list** opens the list's form, filled in, with a .zip copy ready to drag in; every export says it was made with RUSE Studio. |
| Import model dropped a model's own shading and see-through parts. | It keeps them, and says what it kept (not seen in the game yet). |
| A unit built on a drained sea could crash the game; old river water stood as walls along a map's edge; erased lighthouses still shone over the sea. | Fixed, each seen in the game. |

Known: **navy maps aren't finished.** Blank Ocean builds and plays, but units under its water haven't been tried yet.

**0.9.7:** very large map mods now build in minutes. Before, they took a very long time to build, and that's why
this update was needed. And **Export mod…** carries what the build worked out, so a player's first build of one
is shorter.

- **The most extreme map mod we have** (BATTLES > D-Day with its sea drained: 154 flatten strokes, 135 paint strokes,
  33,385 buildings erased) took about four hours to build. Now it builds in **under 10 minutes**, with nothing kept
  from an earlier build, and the game files come out the same. It took us roughly 15 hours; where it was stuck and
  why: [How we got here](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here). We're still working on
  making it faster.

| Before | Now |
|---|---|
| A map reshaped across kilometres could take hours to build, run the PC out of memory, or be refused as too big for the map's movement. | Its ground is reshaped in seconds, its riverbeds mended and its ground painted on all of the PC's cores, and its movement worked out on two more while the ground is painted. Each step gives the same files as before. |
| A drained sea stayed closed to units. | A wide dried bed gets movement zones as big as it has room for. **Not yet tried in the game:** units on the opened sea. |
| A rebuild after a small change worked a big map out again. | What was made is kept: unchanged paint takes half a second, unchanged movement comes from the build cache, and a new stroke repaints only the tiles it reaches. |
| A player's first build of a big map mod worked everything out again. | **Export mod…** puts what the build worked out for the map's movement into the mod (`maps/<map>/solved.bin`). It's locked with the game's own file for that map and holds no game files. A player's build takes it, checks every answer, and gives the same files. Ground painting and riverbeds are still made on each PC. |
| Import model showed only on a new unit's page: hard to find. | The Units tab starts with two buttons: **Change a unit** and **New unit (import a model)**. Pick the unit to start from, name it, Create: its page opens at Import model. A game unit's page has **New unit from this one…**. |
| The ship flag (76) said a unit with it moves on water. | It says the unit doesn't move at all, like a building (not tested in the game yet). |

Known: **navy maps aren't worked out yet.** A drained or painted sea builds and loads, but the water still shows.

**0.9.6:** a new unit can have a 3D model of its own, from any 3D tool, and **Test in game** starts at once when
nothing changed. And a first:

- **The first model from another 3D program in R.U.S.E.:** an M1 Abrams, made a new US unit beside the Sherman. It's
  bought at the Armor Base with its own card, built, and turns its turret like the game's tanks. Seen in the game.

| Before | Now |
|---|---|
| A new unit had the model of the unit it copies. | **Import model…** on a new unit's page: pick a **.3ds** (its pictures beside it, or in the folder above) or a **.glb** (from Blender and most 3D tools). The Studio fits it to the unit it copies: its length (times **Size**: 1 is as long, an Abrams over a Sherman is 1.36), its turret on that unit's turret so the game turns it the same way, its pictures as textures of its own. The page shows it in 3D; **Use the copied unit's model** takes it out again. It goes into your mod as `files/models/<the unit's name>.glb`, which opens in Blender. **Seen in the game.** Early: tracks and wheels don't turn yet, the gun's flash shows where the copied unit's muzzle is, and the wreck is the copied unit's. |
| A new unit with its own card crashed the game when it was built (0.9.5). | Its card is where the game reads it on the map too. **Seen in the game.** |
| A map made with **Duplicate map** couldn't be deleted in the Studio. | **Delete map**, under Duplicate map on a new map: it asks once, then its folder goes to the Recycle Bin, where you can get it back. The game's own maps can't be deleted. |
| The Studio said Blender wasn't installed if it was unzipped rather than installed. | It finds Blender wherever you unzipped it (a drive's top folder or one below, Downloads, Desktop, Documents). |
| Repaints came out with some colours a little off (a red and blue patch could turn purple). | Each 4 x 4 patch keeps its own colours. Repainted units and painted ground come out with slightly different picture data than in 0.9.5 (the same look), so such a mod's fingerprint and join code change: players should all update before playing together. |
| **Test in game** rebuilt the whole modded copy every time, even with nothing changed. | Nothing changed since the last build: the game starts at once, no build (a test mod: 21-29 s to under 0.1 s). A build reuses the last copy's unchanged files instead of copying them again. |
| Every build read the game's unit data afresh. | It's kept between builds: a big test mod took 213 s every time; now the first build takes about as long, and the next ones 68 s. The game no longer copies all its data before a build. |
| Erasing most of a big map ran the Studio out of memory, and a whole-map erase was refused as too big. | Erase counts in seconds, one at a time; **Erase the whole map** in the Erase tray (Undo takes it back). Erased scenery is written compactly. New: not yet seen in the game at scale. |
| Ground flattened under a road left the far-view road at the old height. | The road model follows the new ground. New: not yet seen in the game. |
| A flattened riverbed kept its rock and gorge pictures up close. | It's filled from both banks and its low cover taken off. New: not yet seen done by the build in the game. |
| While the game index built (about a minute), the Studio could only wait. | Maps and Settings stay usable; the line at the bottom says when it's ready. |
| A slow start left no clue. | Each start's steps are timed; **Copy report** in Troubleshoot lists the last five. |
| The window's page could reach more of the app than its own calls. | It gets only the app's own calls. |

Also `ruse import-model <file> --like <model> --unit <name>` does the same from the command line.

**0.9.5:** units get a look of their own. See any unit in 3D, repaint it in Blender, give it your own card in the
build menu. And our firsts, all seen in the game:

- **The first unit repainted by a mod:** a red Sherman, up close and from far.
- **The first unit painted in Blender** and brought back into the game.
- **The first build-menu card made in the Studio,** shown in the game's own Armor Base menu.
- **The first new unit with a model of its own,** beside the game's: the Tall Sherman, next to the Sherman (made in
  testing; making your own models in the Studio comes next).
- **The first mission of our own** played to a victory: a new Operation with its own goals, units and an artillery
  strike (made in testing).

| Before | Now |
|---|---|
| A unit's page showed its values only. | **3D model** on the unit's page: turn it, zoom in, see your mod's paint on it. |
| A unit's look was the game's. | **Repaint in Blender:** **Open in Blender** opens the unit's models with their pictures; paint on the model, then **Bring back** saves your paint and puts it in your mod. **Seen in the game**, up close and from far. Blender is free: if the Studio doesn't find it, **Get Blender (free)** and **Choose Blender…** are right there. |
| A unit's picture in the build menu was the game's. | **Use this view as the card:** turn and zoom the 3D model until it looks right in the dashed frame; that view becomes the unit's card in the build menu. **Seen in the game.** |
| A new unit showed the same card as the unit it copies, so the two looked alike in the menu. | A new unit's card is its own (`files/cards/<the unit's name>.png`): making its card never changes the original's. Not yet seen in the game. |
| A unit model pack that grew was dropped by the game, every model in it missing: a crash at the first factory. | Model packs are written the way the game checks them, whatever their size. **Seen in the game:** a second Sherman with a model of its own. |
| A nation's units given to another army had no model in campaign chapters and Operations: a mod spawning French units on Holland crashed while loading. | Their models load there too. **Seen in the game** (French units on Colditz). |
| **Duplicate map** made BATTLES maps only. | It also makes a new **Operation** or **Campaign chapter** from any map's entry. **Seen in the game:** a new Operation. Early: a new campaign chapter wasn't tried yet. |
| Flattening the mountains at a map's edge left a cliff there. | The map's edge follows the ground. **Seen in the game** (Blitz Twin, flat to the edge). |
| Units went round the places where erased town buildings had stood. | The ground opens to every unit where buildings go, as with trees. **Seen in the game.** |
| No way to paint the map's ground. | **Map Paint:** paint the ground's picture with a colour (the wheel, the map's own colours, or the eyedropper) or with the map's own ground copied from another spot. **Clear the ground under it** (on by default) takes the grass, crops and stones off under the paint so it shows at every height. Early: seen in the game from high up. |

**0.9.4:** new maps, early. **Duplicate map** makes a new map from any BATTLES map, and maps open in a second.

| Before | Now |
|---|---|
| Map changes could only change the game's own maps. | **Duplicate map** (Maps tab, under the open map's name) makes a **new map**: a full copy with a name of its own, listed in BATTLES next to the original, that you then change like any map. The window says what it does and how it works. **Seen in the game:** a new map plays its own ground, and 101 new maps at once were all listed and played. Early: copies of maps other than Blitz build but weren't tried in the game yet, and flattening the mountains at a map's edge leaves a cliff there. Please report what you find. |
| A map took seconds to open every time (M03_Italie: 7.6 s). | Its data is kept between visits and runs: 1.7 s the second time. |
| "Mod" and "Map" were two menus alike. | **Unit mod** (with a tank) and **Map changes** (with a map). |
| Sides and zones were easy to mix up. | **Who gets it?** says a side is who controls the units (one country can have several), and a zone's hover says it's an area of the map, not a side. |
| Updates came only as whole versions. | Small fixes can come between versions (0.9.4.1), offered like any update. |

**0.9.3:** everything you place shows from far, new roads through woods look like the map's own, trees you can keep
on a road, props and trees by their names in your language, and builds about three times faster.

| Before | Now |
|---|---|
| Props, trees and buildings to place were listed by French code names: Caillou_10, ChampsPierres_02, Osier... | By names in the Studio's language, all ten, with what kind of thing each one is: "Stony field 2", "Champ de pierres 2", "Steiniges Feld 2". They change with the language button. The code name and its folder are in the tooltip. |
| Rocks and most other props you placed vanished as soon as the camera left close range, and came and went as you turned it. | Everything a mod places is drawn out to the far distance, the map's own objects unchanged. **Seen in the game:** placed rocks show at every height. |
| From high up a new road through a wood was a bright strip, and after a first fix it was gone from medium-long range. | Painted through woods the way the map's own roads are, at every height. **Seen in the game.** |
| A new road always took the trees off its path, about 6 m either side. | **Keep the trees on new roads** in the Roads tray: the trees and bushes stay over the road, and in a wood the road shows fainter and greyer. **Seen in the game.** |
| **Test in game** took about 5 minutes to build a mod with new roads on M03_Italie. | About 1½ minutes: what a map's roads look like is measured once and kept, and copies skip a slow check they don't need. |

**0.9.2:** fixes from a tester's campaign map: bridges for new roads on every map, road ends that snap to bridges
(or not at all), the names a player knows, units for the player, scenery that shows from far, and the scenario's
zones as borders on the ground.

| Before | Now |
|---|---|
| A road over water stopped the build on 20 of the 29 maps with bridges (Italy, Germany, Holland...): its bridge "would have no floor". | It gets its bridge and floor on every map with bridges. Not yet seen in the game on those maps. |
| Every point of a road snapped to the nearest road, onto a road even when you'd placed a bridge there. | Only a road's two ends snap, to a placed bridge's end first. **Snap ends to roads and bridges** in the Roads tray turns it off. |
| Buildings and units by their code names, like "Descriptor_Building_VehiculeFactoryLeurre". | By the names the game gives them (DECOY ARMOR BASE), with the game's own line on what each one does. |
| No way to give units to the player in a campaign chapter: the player's side (0) was refused. | **Who gets it?** lists the scenario's own sides from its mission: "Player · USA (side 0)", "Computer · Germany (side 1)"... |
| On M03_Italie and other maps, a new road out in the open hid the map's scenery from far, and props you placed showed only up close. | The map's far view stays as it was, and placed props show from far like the map's own. Not yet seen in the game. |
| The scenario's zones were coloured sheets floating over the map, covering its ground and the icons. | Each zone is a clear line along its border on the ground with a see-through tint inside, like Stellaris' borders. **Zones' fill** sets the inside (0 %: the borders alone). |

**0.9.1:** drag anything on the map, clearer icons you can size and hide, your language from the first start, and
every unit's type as the game names it.

| Before | Now |
|---|---|
| Starting points, supply depots and spawned units moved only with the Move tool, one click then another. | Grab any of them on the map and drag it, with no tool picked, the way the opening cameras already turned. Depots and HQs still stick to roads while you drag. |
| Map icons were stick figures and boxes, and every bunker looked the same. | An icon for each kind: a soldier, a tank, a truck for supply depots, a plane, guns, a clearly marked HQ, the armor base and the airfield told apart, and every bunker its own (anti-tank, machine gun, anti-aircraft, artillery, fort, lookout post). |
| Icons were bulky from high up, and the only way to hide them was to hide the whole scenario. | Icons shrink as the camera pulls out, a slider sets their size, and the Scenario tray shows or hides each kind (starts, cameras, depots, buildings, units, zones, towns). Kept for next time. |
| The Studio started on the code names, and the language sat in Settings, so players didn't know it speaks their language. | The first start asks: "Choose your language", each language in its own words, the one your game is set to in Steam marked. Then a language button at the top, always in sight. |
| Units were only "Ground" or "Air". | Under Ground, Infantry and Air, the game's own types: Light, Medium and Heavy Tank, Tank Destroyer, Armored Recon, Fighter, Fighter-bomber, Light, Medium and Heavy Bomber, Air Recon... on each unit's line too, in your language. Search finds them ("bomber", "recon"). |
| Windows' list of installed apps showed the first version ever installed. | It shows the version you have. |

**0.9.0:** roads look right. A road you draw now looks like the map's own roads, from high up and right down
at the ground. It took a lot of time and a lot of tests to get there, longer than the bridges
did. Tested in the game on D-Day.

![A new road up close on D-Day: asphalt with a dashed centre line and gravel shoulders fading into the grass](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Before | Now |
|---|---|
| A new road vanished as the camera came down to it: only its paint showed, from high up. | Up close it's drawn with the map's own asphalt stickers, laid along it the way the map lays them, with an edge sticker either side: asphalt, a dashed centre line, gravel shoulders. |
| The paint was one flat colour, paler and wider than the map's roads. | The paint is measured on the map's own roads: their colour, their shoulders, and how they fade into the ground. Each map gets its own. |
| Grass, bushes and the farm's trees grew through a new road. | The map's plants and props on the road's path are taken off (about 6 m either side). Woods keep their cover and movement, and buildings stay. |
| Only D-Day's road stickers were known. | The desert maps' own stickers are used there, laid the same way (not yet seen in the game). |
| A big erase (thousands of circles) took many minutes to build. | Much faster: only the circles near each part of the map are looked at. |

![Three new roads off D-Day's main road](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-6-done-overview.jpg)

**0.8.3:** the map editor's scenario tools from LittleGroove's RUSE-Mod-Manager: supply depots and HQs stick to
roads, an icon for every building and unit, and each player's opening camera shown, carried and turned. Not yet tried
in the game.

| Before | Now |
|---|---|
| A supply depot spot couldn't be placed. | **Supply depot spot** is first under Add unit → Buildings → Money. |
| A starting point went exactly where you clicked, on the road or far from it alike. | **Stick to roads** (on by default) puts it beside the nearest road, as far from it as the game's own maps do (LittleGroove measured it). Untick it to place in the middle of a field. |
| Spawns were a few icons, with letters for the country. | An icon for what each one is (HQ, supply depot, factory, fort, decoy, soldier, tank, anti-tank, artillery, prototype, plane, turret) and the country's roundel. |
| You couldn't see where a player's match opens. | Each starting point shows its opening camera: the flight in (dotted), where it stops, what it looks at, and the part of the map the screen shows. |
| A moved starting point's opening camera stayed at the old place. | The camera moves with it; a new starting point gets a camera of its own. |
| The opening camera couldn't be changed. | With **Move**, drag a start's camera round its HQ to open the match from another side; **Camera back** undoes it. |
| A starting point in a wood was refused. | Allowed: an HQ works there, and supply trucks drive through woods. Only water, cliffs and blocked ground are refused. |

**0.8.2:** a test stopped by a mistake in your mod tells you which and fixes it, mods and maps apart, clearer map
colours and spawns, and one game copy for the whole PC.

| Before | Now |
|---|---|
| A test stopped by a mistake in your mod buried the reason in the log and pointed to Troubleshoot, which can't fix a mod. | Each mistake is listed over the log with a button that fixes it: a team spawn on a BATTLES map made neutral or taken out (every one at once too), a road that joins nothing taken out. Troubleshoot shows only for other failures. |
| The message at the bottom couldn't be closed. | Every message has a × to close it. |
| The test log couldn't be copied. | **Copy report** copies the log and the message, for a bug report or Discord. |
| Mods and maps shared one menu. | Mods and maps each have their own menu, and Export puts the file straight into the Launcher's library. |
| Every spawn on the map looked the same. | Each spawn is a building, tank, soldier or plane icon in its side's colour, with its country. |
| The map's colours weren't explained. | A colour legend for cover, where units go and Erase; the Town tool's cover has its own colour; a see-through slider for each layer. |
| Hills and trees poked through a scenario's zones. | Zones float over the ground, and a **Zones' height** slider sets how high. |
| Every test kept its own copy of the game. | One modded copy for the whole PC, shared with the Launcher. |
| The version wasn't shown, and What's new was a list. | The version is beside the name, and What's new opens a before/after table like this one. |
| Few tooltips. | Tooltips on the main controls, written for players new to modding. |
| New roads on Twilight of the Gods, Alpha, Ostfriesland and Robert missed the map's road model. | They get it too. |
| The build said new roads were "drawn up close". | It says they show from afar; up close they don't show yet (still a known issue). |

**0.8.1:** units from any nation, a new look, a shorter toolbar, and the Erase tool.
- **Units from another nation work.** A new unit can go in any nation's build menu, whatever army its model comes
  from: a German Tiger or Ju 87 for the US, a Japanese Zero or Chi-Ha too. It's built, fights, shows its picture on
  its card and its marker, and can be selected on the ground and in the air, even in a match where nobody plays the
  nation it came from (tested in the game, 2026-10-02). The build has that nation's models load in every match; a
  match takes a little more memory and loading time.
- **A new look:** R.U.S.E.'s blues instead of black and gold, and a new logo: the war-room table.
- **The map editor's toolbar is shorter.** Tools that go together share one tile, with a tab for each: Ground &
  water, Cover & movement, Roads & bridges, Buildings, Props & trees, then Erase, Scenario and Check. A tile opens at
  the tab you used last.
- **Erase tool:** drag over the map's own trees and props (buildings too, if you pick them) and they're gone when the
  mod is built. The red circles are saved in the mod, what they cover is tinted red, and the tray counts what they'll
  take. Where trees go, the ground opens to every unit and loses its forest cover. Erasing a map's own buildings,
  roads, shrubs and rocks properly comes next.
- **The installer offers a clean game backup** beside the desktop shortcut, and says why: with it, the troubleshooter
  can put back anything another mod manager changed.

**0.8.0:** the map editor grows up: new brushes and docks, bridges units really cross, woods you can clear, and a
build that checks the game's rules so what you make works the first time. Plus a troubleshooter and a clean game
backup.
- **New in the map editor:**
  - **Open brushes** (Movement): the reverse of Block. Give units ground the map keeps them off (all units, infantry
    or vehicles). Opening water is allowed and warned: units stand on the riverbed there.
  - **Forest brush** (Cover): trees and cover in one stroke; Undo takes both away.
  - **Bridges dock:** the map's own bridge kinds, and a bridge placed by hand at the length and turn you choose; new
    roads' water crossings drawn in gold.
  - **Check this map:** lists what would go wrong before you test (ground cut off, roads or bridges units can't use,
    road ends not joined, buildings on roads), and clicking one shows where.
  - Drained or raised-dry riverbeds are opened to units by the build.
- **Clear the map's own trees and props:** `[[erase]]` circles in a mod's `scenery.toml` (written by hand for now;
  an Erase tool in the Studio is on the way). Tanks drive into a cleared wood, and infantry there are no longer
  hidden.
- **Placed objects stand on the ground at any size.** A building scaled up 10× floated in the air; it now sits on
  the ground like the map's own.
- **Fixed: cover on the maps that aren't square** (D-Day, Frontline, Djebel, Medjez, Handshake over the Elbe, and the
  Tunisia, Holland and Ardennes campaign maps). Cover painted or cleared there (the Cover, Uncover, Town and Forest
  brushes, `cover.toml`) landed up to a kilometre from where it was drawn, and the map view showed it in that wrong
  place too. Both are right now: if you painted cover on one of these maps, look at it again in the map view. Square
  maps (Blitz and most others) were always right.
- **Bridges work in the game.** A road you draw over water gets the map's own kind of bridge (the Dutch maps' too),
  and tanks, infantry and supply trucks cross it on the deck, infantry at the deck's height. Bridge ends join the
  roads units already use and keep clear of the map's buildings; a bridge that can't be joined stays closed, and the
  build's note says what the road met and where.
- **The build checks the game's rules.** Every file a mod changes was checked against what the game does with it, and
  a mod that would break in the game is refused with a note saying why, before anything is written:
  - roads: units now follow new roads, not only supply trucks, and a new road that joins no other road is refused
    (the road network must stay in one piece);
  - placed buildings and blocks: units can't drive through them any more; new buildings, bridges and trees show at
    every distance;
  - terrain: new water is closed to units, the AI's map follows your woods, blocks, bridges and water, and a stroke
    that can't change the ground (or reaches a bridge's floor) says so;
  - units: a wrong salvo, ID, nation or menu list is refused, unit flags are checked, and every flag is explained in
    the flag picker (flags 62 and 63, which crash the game on a unit that isn't a truck, are an error); a unit put
    in another nation's factory is refused for now (it crashed the game when built; making it work is next);
  - scenario: spawns are neutral by default, a spawn of a unit whose models the match may not load is refused (it
    crashed the game at the start), a start where vehicles can't go is refused, a moved start takes its camera
    along, and seats are counted per team.
- **The build's report** shows every warning (some were lost), and a rebuild takes the old test copy away first, so
  an old copy can't be started by mistake.
- **Square cover:** `square = true` on a `cover.toml` paint, or on a Cover or Uncover stroke in `terrain.toml`,
  paints a square along the map's axes (written by hand for now; the map view draws it as a square).
- **Troubleshoot** (beside *Test in game*, and in Settings > Help): checks in one go what can stop a test (the game
  found, Steam, a game left running from a modded copy, the drive and its free space, leftover copies, read-only
  files, whether the app can write where copies go), with a button for each fix it can make, and a report to paste in
  a bug report, your Windows user name left out.
- **Clean game backup** (Settings): keep a clean copy of your game's files, check them against it, and put back
  anything another mod manager or a hand edit changed. Files that aren't the game's are moved aside, never deleted.
  Or let Steam repair the game (*Verify with Steam*). This is the only place the Studio ever writes into your game
  folder, and only when you ask.
- **Share your mod:** made a mod? After the export, the Studio shows its size and SHA-256 and how to add it to the
  mod list on GitHub and become a contributor.
- **Known issue: new roads aren't drawn up close yet.** They're painted on the ground and show from afar, and units
  use them, but with the camera near the ground a new road disappears. Being worked on.

**0.7.6:** a second Test in game works, and bridges units can always reach.
- **Fixed:** every second *Test in game* could fail with "An old modded copy ... can't be removed ... (Access is
  denied)". A copy Windows won't delete (a file an older version linked to a replaced game file, a program still
  holding it) no longer stops a test: it's moved aside into `RUSE-Instances\.trash` and removed once nothing holds
  it. If R.U.S.E. is still running from the test copy, you're told, with the program's name. Pressing *Test in game*
  twice starts one test, not two.
- **Fixed:** a road's new bridge could crash the game when units were ordered onto it: its deck reached no ground
  units use. Each end of a bridge now joins the ground along the road (up to 62 m of approach); a bridge that can't
  be joined stays closed to units, with a note, and the build never writes ground units can't reach.

**0.7.4:** Test in game works when your game's files are marked read-only.
- **Fixed:** *Test in game* failed every time with "[WinError 5] Access is denied" when R.U.S.E.'s files are marked
  read-only (a disc install, a restored backup): the test copy kept the mark, so a copy left half-built could never
  be removed. The test copy never keeps the mark now, and a leftover from an older version is removed by itself
  (your game's files end exactly as they were). If the game is still running from the test copy, you're told to
  close it instead of getting a Windows error.
- **A road shows its length** while you draw it, beside the pointer (Cities: Skylines style); the Roads tools show
  the total of your new roads.
- **New roads are painted on the ground** in the map's own road colour (proven in the game), and **a road over water
  gets a bridge**: the map's own kind, one piece stretched bank to bank as the game's own bridges are, so units can
  cross. A road over one of the map's own bridges gets the new bridge in its place. (Bridges are new: not checked in
  the game yet.)

**0.7.3:** arrange the map view your way. The map panel (top left) and the tools (bottom) move anywhere by their
grip (⠿) and fold with the arrow next to it: the map panel down to its title, the tools down to their bar.
Double-click a grip to put that panel back. Your layout is kept.

**0.7.2:** roads, and clearer tests.
- **Draw roads**, Cities: Skylines style (the Roads kind in the bar): **Straight**, **Curve** and **Freeform**. An
  end near a road snaps onto it and joins it. New roads draw as blue ribbons and **supply routes use them** (proven
  in the game). They aren't painted on the ground yet.
- The **Roads** box shows the map's own roads in gold.
- The game's own words: a scenario is named after the main-menu button that plays it (**Battles**, Operation,
  Campaign, read from your game's text in your language), and a gold line under the scenario menu says where it
  plays, e.g. *In the game: Battles › D-Day (6 players)*.
- **Test in game** says where it built and exactly what to open to see your changes (e.g. *BATTLES > D-Day*).
- The middle mouse button turns the view in look-around mode too (it zoomed there before).

**0.7.1:** several units at once, a mod check, and help at hand.
- **Add unit** places 1, 2, 4, 6, 8 or 10 at once, in a **line, column, wedge, box or circle** facing up the
  screen, with a spacing slider and rings showing where each will stand.
- The **mod check**: every file of your mod is read the way the game build reads it, when you pick the mod and
  before **Test in game**. A red bar names each problem; a broken map file can be **set aside** (renamed, never
  lost), and a map folder named after the map's title (maps/Blitz) can be **renamed** to its pack name
  (maps/SuperCrossRoads4) in one click.
- Fixed: **Water** strokes were saved without their level, so the game build refused the mod. Every file the
  Studio writes is now read back before it's saved.
- The map list **folds away** («) for more room.
- **Settings > Help & community**: the wiki (the new field manual), Discussions, and **Report a problem**, which
  opens a bug report with your version filled in. An error at the bottom has its own **Report** link. Nothing is
  sent by the app: you read the report and post it.

**0.7.0:** a new look and movement tools. The map tools moved to a bar along the bottom, as in Cities: Skylines, in
R.U.S.E.'s own HUD style: pick a kind (Ground, Water, Cover, Movement, Buildings, Objects, Trees, Scenario) and its
tools open above it; click it again or press Esc to just look around. The scenario's pickers are tiles now, not
drop-downs. **Movement:** the **Where units go** box shows it on the map (red: no unit; yellow: infantry only), and
three new brushes close ground: **Block** (every unit), **Block infantry** and **Block vehicles**. Buildings you place
stop units (the **Solid** box, on by default). Proven in the game: units plan around a blocked pit and go between
placed towers.

**0.6.9:** buildings, props and trees you place now show in the game at every zoom (proven on Blitz, at up to 8×
their size): each group goes in a new block wrapped around the nearest village or farm the map draws from far.
Checked on all 32 maps: nothing else moves. Units still walk through placed buildings; making them solid is next.

**0.6.8:** make towns and woods units can hide in. The map view shows where units hide (the **Cover** box, in
green), and three new brushes paint it: **Cover**, **Uncover**, and **Town** (click a town: cover goes around every
building of it, placed ones too). Proven in the game: infantry on painted cover are hidden.

**0.6.7:** placed objects go up to 10× their size (the Place tool's Size slider; [ and ] step by 0.1 up to 3×, then
by 0.5).

**0.6.6:** the ammunition is sorted by type too: AP shells, HE shells, anti-aircraft, machine guns, infantry
weapons, infantry anti-tank, bombs and rockets (the Type list above the ammunition). Mods can also paint cover (where
units hide, like in a wood) and blocked ground on a map (`maps/<map>/cover.toml`); the Studio tool for it comes next.

**0.6.5:** scenarios can be edited on the map. **Move** a starting point or a spawn (click it, then where it goes;
Put back undoes it). **Add unit** spawns a unit or building when the scenario starts: pick its kind (buildings, ground,
infantry, air), then its type (for buildings: HQ, money, factories, forts and defenses, fake decoys; for units: the
factory that builds them), then the unit (by nation) and its side. Saved in the mod's `maps/<map>/scenario.toml`.
The unit list has the same Type filter.

**0.6.4:** the map list has a type filter: all maps, or only the skirmish maps, Operations, campaign, demo or
test maps (from the game's own menus; a map can be several). It's remembered.

**0.6.3:** a **Settings** tab (next to Units and Maps): the language, the map view's keys, the game folder and
updates in one place, ready for more.

**0.6.2:** finding updates is sturdier: when GitHub turns the one check at start away (it allows 60 an hour
per internet address, shared by everything on it), the Studio reads GitHub's release list instead. Mods can also
spawn units and buildings in a scenario (`[[spawn]]` in `maps/<map>/scenario.toml`).

**0.6.1:**

- **Your language and keys are kept** through restarts, updates and reinstalls (they were lost at every start).
- **Scenarios grouped as the game uses them:** Skirmish, Operations, Campaign, Demo, Test, and the ones no menu
  loads, each named as the game's menus name it ("10. UTAH BEACH", "Anzio").
- **Mods can move starting points and spawns** (`maps/<map>/scenario.toml`); checked in the game: the HQ starts
  where the mod puts it.

**New in 0.6:**

- **Terrain that works in the game:** ground you raise, lower or flatten now takes move orders, the camera stays above
  it, and trees and buildings stand on it. The recipe of DomesticNukes and his Claude: the gameplay ground moves first,
  the drawn ground follows it, and the game's hidden height limits are widened. Checked on all 32 maps.
- **Scenarios on the map:** a "Scenario" row picks one of the map's scenarios (skirmish, challenges, campaign
  chapters) and shows its zones, starting points (pillars in each alliance's colour), spawns (white diamonds) and
  town names. Point at one to see what it is. The first step toward making maps.

**0.5.2:**

- **Water and Drain brushes** (Water on key 0): flood the ground below a level into a lake, or dry a lake
  or river up. By DomesticNukes and his Claude, checked in the game on Blitz.
- **Your own keys:** "Change keys…" under the map view's help line: click an action, press a key. Defaults puts them
  back.

**0.5.1:**

- **A gun keeps its own flash and sound:** when a weapon fires another unit's ammo, it now also takes that unit's
  muzzle flash and firing sound (the Sherman's gun on a rifleman fires like a Sherman). The weapon shows which one it
  plays.
- **Level brush** (key 7): paints the ground flat at the height where you start dragging.
- **WASD moves with the camera**: W is always forward on screen, however the view is turned.
- The game index is built again once, the first time 0.5.1 opens (about half a minute).

**New in 0.5:**

- **New units:** copy a unit from its page, name it, price it and put it in a build menu.
- **Ammo and flags:** an Ammo kind with every ammunition. A weapon can fire another weapon's ammo (the nation it
  comes from is shown) or its own copy of it. Flag lists (what a unit is and does) can be edited, like in RUSE Mod
  Manager's units editor.
- **Maps:** each map shows its in-game name, in your language, next to its code name. Buildings, props and trees are
  drawn with **the game's real 3D models and textures**, thanks to DomesticNukes and his Claude.
- **Terrain brushes:** raise, lower, smooth and ramp the ground, saved in the mod. **Start over** clears a map.
- **Place tool:** one click places a building, prop or tree. Paint an area, or click twice for a line (a hedge, a
  street). Undo takes back a whole area or line. Scenery is only for looks for now: units drive through it.
- **Keys:** WASD / arrows move the view, Q/E turn it, R/F zoom. Hover any button for a tooltip.
- **Export .rusemod:** one file the launcher installs.
- **It updates itself:** from this version on, a bar says when a newer Studio is out; **Update** installs it.

It's new and has barely been tested outside the developer's PC, so please report anything odd on GitHub Issues.

![RUSE Studio's Maps: Centre of Gravity in 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio in its preview mode, with sample units](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
