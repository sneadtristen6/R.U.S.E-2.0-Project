**RUSE Studio, a preview for modders.** Browse the game's units in any of its ten languages, change them in a mod of
your own, and test it in the game. Your Steam install is never changed.

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

![RUSE Studio's Maps: Centre of Gravity in 3D](https://raw.githubusercontent.com/sneadtristen6/Ruse-Mod-Platform/main/docs/images/studio-maps.jpg)

![RUSE Studio in its preview mode, with sample units](https://raw.githubusercontent.com/sneadtristen6/Ruse-Mod-Platform/main/docs/images/studio-unit.jpg)
