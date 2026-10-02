**RUSE Studio, a preview for modders.** Browse the game's units in any of its ten languages, change them in a mod of
your own, and test it in the game. Your Steam install is never changed.

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
  drawn with **the game's real 3D models and textures**, thanks to the .spk notes from DomesticNukes and his Claude.
- **Terrain brushes:** raise, lower, smooth and ramp the ground, saved in the mod. **Start over** clears a map.
- **Place tool:** one click places a building, prop or tree. Paint an area, or click twice for a line (a hedge, a
  street). Undo takes back a whole area or line. Scenery is only for looks for now: units drive through it.
- **Keys:** WASD / arrows move the view, Q/E turn it, R/F zoom. Hover any button for a tooltip.
- **Export .rusemod:** one file the launcher installs.
- **It updates itself:** from this version on, a bar says when a newer Studio is out; **Update** installs it.

It's new and has barely been tested outside the developer's PC, so please report anything odd on GitHub Issues.

![RUSE Studio's Maps: Centre of Gravity in 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio in its preview mode, with sample units](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
